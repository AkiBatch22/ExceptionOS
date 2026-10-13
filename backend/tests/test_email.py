from email.message import EmailMessage
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.extraction import PurchaseOrderExtraction
from backend.app.services.email import parse_purchase_order_email

client = TestClient(app)


def email_with_pdfs(count: int):
    message = EmailMessage()
    message["From"] = "orders@acme.example"
    message["To"] = "sales@example.com"
    message["Subject"] = "Purchase order PO-4832"
    message["Message-ID"] = "<po-4832@acme.example>"
    message.set_content("Please process the attached order.")

    for number in range(count):
        message.add_attachment(
            f"pdf {number}".encode(),
            maintype="application",
            subtype="pdf",
            filename=f"order-{number}.pdf",
        )

    return message.as_bytes()


def test_email_metadata_and_pdf_are_parsed():
    email = parse_purchase_order_email(email_with_pdfs(1))

    assert email["sender"] == "orders@acme.example"
    assert email["message_id"] == "<po-4832@acme.example>"
    assert email["subject"] == "Purchase order PO-4832"
    assert email["body"] == "Please process the attached order."
    assert email["attachment_name"] == "order-0.pdf"
    assert email["pdf_bytes"] == b"pdf 0"


def test_email_without_pdf_is_rejected():
    with pytest.raises(ValueError, match="no PDF attachment"):
        parse_purchase_order_email(email_with_pdfs(0))


def test_email_with_multiple_pdfs_is_rejected():
    with pytest.raises(ValueError, match="multiple PDF attachments"):
        parse_purchase_order_email(email_with_pdfs(2))


def test_email_pdf_is_sent_through_existing_extraction_pipeline():
    extraction = PurchaseOrderExtraction(
        po_number="PO-4832",
        customer="Acme Inc.",
        items=[{"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18}],
        ship_to="Austin office",
        missing_fields=[],
    )

    with (
        patch(
            "backend.app.api.routes.purchase_orders.extract_pdf_text",
            return_value="PO Number: PO-4832",
        ) as pdf_extractor,
        patch(
            "backend.app.api.routes.purchase_orders.extract_purchase_order",
            return_value=extraction,
        ) as po_extractor,
    ):
        response = client.post(
            "/purchase-orders/extract-email",
            files={
                "file": (
                    "order.eml",
                    email_with_pdfs(1),
                    "message/rfc822",
                )
            },
        )

    assert response.status_code == 200
    assert response.json()["sender"] == "orders@acme.example"
    assert response.json()["attachment_name"] == "order-0.pdf"
    assert response.json()["purchase_order"]["po_number"] == "PO-4832"
    pdf_extractor.assert_called_once_with(b"pdf 0")
    po_extractor.assert_called_once_with("PO Number: PO-4832")
