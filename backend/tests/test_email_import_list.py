from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.extraction import PurchaseOrderExtraction
from backend.app.services.email_imports import record_email_import


client = TestClient(app)


def save_import(message_id: str, po_number: str):
    record_email_import(
        message_id=message_id,
        imap_uid="42",
        sender="orders@acme.example",
        subject=f"Purchase order {po_number}",
        attachment_name="order.pdf",
        purchase_order=PurchaseOrderExtraction(
            po_number=po_number,
            customer="Acme Inc.",
            items=[
                {"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18}
            ],
            ship_to="Austin office",
            missing_fields=[],
        ),
    )


def test_email_imports_can_be_listed():
    save_import("<po-4832@acme.example>", "PO-4832")

    response = client.get("/email-imports")

    assert response.status_code == 200
    assert response.json()["imports"][0]["message_id"] == (
        "<po-4832@acme.example>"
    )
    assert response.json()["imports"][0]["customer"] == "Acme Inc."


def test_email_import_detail_contains_saved_extraction():
    message_id = "<po-4832@acme.example>"
    save_import(message_id, "PO-4832")

    response = client.get(
        "/email-imports/detail",
        params={"message_id": message_id},
    )

    assert response.status_code == 200
    assert response.json()["subject"] == "Purchase order PO-4832"
    assert response.json()["extraction"]["po_number"] == "PO-4832"


def test_missing_email_import_returns_not_found():
    response = client.get(
        "/email-imports/detail",
        params={"message_id": "<missing@example.com>"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Email import not found"}


def test_processed_order_completes_and_hides_import():
    message_id = "<po-4832@acme.example>"
    save_import(message_id, "PO-4832")

    response = client.post(
        "/email-imports/process",
        params={"message_id": message_id},
        json={
            "po_number": "PO-4832",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18}
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert client.get("/email-imports").json() == {"imports": []}


def test_human_review_creation_also_completes_import():
    message_id = "<po-review@acme.example>"
    save_import(message_id, "PO-REVIEW")

    response = client.post(
        "/email-imports/process",
        params={"message_id": message_id},
        json={
            "po_number": "PO-REVIEW",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-XL", "quantity": 10, "unit_price": 20}
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "human_review_required"
    assert client.get("/email-imports").json() == {"imports": []}


def test_completed_import_cannot_be_processed_twice():
    message_id = "<po-4832@acme.example>"
    save_import(message_id, "PO-4832")
    purchase_order = {
        "po_number": "PO-4832",
        "customer": "Acme Inc.",
        "items": [
            {"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18}
        ],
        "ship_to": "Austin office",
    }
    client.post(
        "/email-imports/process",
        params={"message_id": message_id},
        json=purchase_order,
    )

    response = client.post(
        "/email-imports/process",
        params={"message_id": message_id},
        json=purchase_order,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email import already completed"}
