import json
from email.message import EmailMessage
from types import SimpleNamespace
from unittest.mock import patch

import pymupdf
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


class FakeImap:
    email_bytes = b""
    marked_uids = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def login(self, username, password):
        return "OK", [b"logged in"]

    def select(self, mailbox):
        return "OK", [b"1"]

    def uid(self, command, uid, *args):
        if command == "search":
            return "OK", [b"42"]

        if command == "fetch":
            return "OK", [(b"42 (BODY[])", self.email_bytes)]

        if command == "store":
            self.marked_uids.append(uid)
            return "OK", [b"marked"]

        raise AssertionError(f"Unexpected IMAP command: {command}")


def purchase_order_pdf(po_number: str, sku: str, quantity: int):
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        (
            f"PO Number: {po_number}\n"
            "Customer: Acme Inc.\n"
            f"SKU: {sku}\n"
            f"Quantity: {quantity}\n"
            "Unit Price: 18\n"
            "Ship To: Austin office"
        ),
        fontsize=12,
    )
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def purchase_order_email(
    message_id: str,
    po_number: str,
    sku: str,
    quantity: int,
):
    message = EmailMessage()
    message["From"] = "orders@acme.example"
    message["To"] = "sales@example.com"
    message["Subject"] = f"Purchase order {po_number}"
    message["Message-ID"] = message_id
    message.set_content("Please process the attached purchase order.")
    message.add_attachment(
        purchase_order_pdf(po_number, sku, quantity),
        maintype="application",
        subtype="pdf",
        filename=f"{po_number}.pdf",
    )
    return message.as_bytes()


def groq_response(extraction: dict):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(extraction))
            )
        ]
    )


def import_from_fake_inbox(monkeypatch, email_bytes: bytes, extraction: dict):
    FakeImap.email_bytes = email_bytes
    FakeImap.marked_uids = []
    monkeypatch.setenv("IMAP_HOST", "imap.example.com")
    monkeypatch.setenv("IMAP_USERNAME", "orders@example.com")
    monkeypatch.setenv("IMAP_PASSWORD", "test-password")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")

    with (
        patch("backend.app.services.inbox.imaplib.IMAP4_SSL", FakeImap),
        patch("backend.app.services.extraction.Groq") as groq,
    ):
        groq.return_value.chat.completions.create.return_value = groq_response(
            extraction
        )
        return client.post("/purchase-orders/import-email")


def test_email_to_erp_order_workflow(monkeypatch):
    message_id = "<po-e2e-ready@acme.example>"
    purchase_order = {
        "po_number": "PO-E2E-READY",
        "customer": "Acme Inc.",
        "items": [
            {"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18}
        ],
        "ship_to": "Austin office",
        "missing_fields": [],
    }

    import_response = import_from_fake_inbox(
        monkeypatch,
        purchase_order_email(message_id, "PO-E2E-READY", "HD-BLK-M", 50),
        purchase_order,
    )

    assert import_response.status_code == 200
    assert FakeImap.marked_uids == ["42"]
    assert client.get("/email-imports").json()["imports"][0][
        "message_id"
    ] == message_id

    assessment = client.post(
        "/purchase-orders/assess",
        json={key: value for key, value in purchase_order.items() if key != "missing_fields"},
    )
    assert assessment.json() == {"decision": "ready", "issues": []}

    process_response = client.post(
        "/email-imports/process",
        params={"message_id": message_id},
        json={key: value for key, value in purchase_order.items() if key != "missing_fields"},
    )

    assert process_response.status_code == 200
    assert process_response.json()["erp_order_id"] == "ERP-PO-E2E-READY"
    assert client.get("/email-imports").json() == {"imports": []}
    events = client.get("/purchase-orders/PO-E2E-READY/events").json()["events"]
    assert [event["event"] for event in events] == [
        "purchase_order_received",
        "assessment_completed",
        "erp_order_created",
    ]


def test_email_to_human_review_workflow(monkeypatch):
    message_id = "<po-e2e-review@acme.example>"
    purchase_order = {
        "po_number": "PO-E2E-REVIEW",
        "customer": "Acme Inc.",
        "items": [
            {"sku": "HD-BLK-XL", "quantity": 10, "unit_price": 20}
        ],
        "ship_to": "Austin office",
        "missing_fields": [],
    }
    order_payload = {
        key: value
        for key, value in purchase_order.items()
        if key != "missing_fields"
    }

    import_response = import_from_fake_inbox(
        monkeypatch,
        purchase_order_email(
            message_id,
            "PO-E2E-REVIEW",
            "HD-BLK-XL",
            10,
        ),
        purchase_order,
    )
    assert import_response.status_code == 200

    assessment = client.post("/purchase-orders/assess", json=order_payload)
    assert assessment.json()["decision"] == "human_review_required"

    process_response = client.post(
        "/email-imports/process",
        params={"message_id": message_id},
        json=order_payload,
    )

    assert process_response.status_code == 200
    assert process_response.json()["status"] == "human_review_required"
    review_id = process_response.json()["review_id"]
    review = client.get(f"/reviews/{review_id}")
    assert review.status_code == 200
    assert review.json()["status"] == "pending"
    assert client.get("/email-imports").json() == {"imports": []}
    events = client.get("/purchase-orders/PO-E2E-REVIEW/events").json()["events"]
    assert [event["event"] for event in events] == [
        "purchase_order_received",
        "assessment_completed",
        "review_created",
    ]
