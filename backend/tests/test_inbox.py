from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.extraction import PurchaseOrderExtraction

client = TestClient(app)


def parsed_email():
    return {
        "message_id": "<po-4832@acme.example>",
        "sender": "orders@acme.example",
        "subject": "Purchase order PO-4832",
        "body": "Please process the attached order.",
        "attachment_name": "order.pdf",
        "pdf_bytes": b"pdf bytes",
    }


def extraction():
    return PurchaseOrderExtraction(
        po_number="PO-4832",
        customer="Acme Inc.",
        items=[{"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18}],
        ship_to="Austin office",
        missing_fields=[],
    )


def test_unread_email_is_imported_and_marked_processed():
    with (
        patch(
            "backend.app.services.inbox_import.fetch_unread_emails",
            return_value=[{"uid": "42", "content": b"email bytes"}],
        ),
        patch(
            "backend.app.services.inbox_import.parse_purchase_order_email",
            return_value=parsed_email(),
        ),
        patch(
            "backend.app.services.inbox_import.extract_pdf_text",
            return_value="PO Number: PO-4832",
        ),
        patch(
            "backend.app.services.inbox_import.extract_purchase_order",
            return_value=extraction(),
        ),
        patch(
            "backend.app.services.inbox_import.mark_email_processed"
        ) as mark_processed,
    ):
        response = client.post("/purchase-orders/import-email")

    assert response.status_code == 200
    assert response.json()["purchase_order"]["po_number"] == "PO-4832"
    mark_processed.assert_called_once_with("42")


def test_email_is_not_marked_when_extraction_fails():
    with (
        patch(
            "backend.app.services.inbox_import.fetch_unread_emails",
            return_value=[{"uid": "42", "content": b"email bytes"}],
        ),
        patch(
            "backend.app.services.inbox_import.parse_purchase_order_email",
            return_value=parsed_email(),
        ),
        patch(
            "backend.app.services.inbox_import.extract_pdf_text",
            side_effect=ValueError("OCR could not find text in the PDF"),
        ),
        patch(
            "backend.app.services.inbox_import.mark_email_processed"
        ) as mark_processed,
    ):
        response = client.post("/purchase-orders/import-email")

    assert response.status_code == 422
    mark_processed.assert_not_called()


def test_inbox_skips_email_without_one_pdf():
    with (
        patch(
            "backend.app.services.inbox_import.fetch_unread_emails",
            return_value=[
                {"uid": "41", "content": b"no pdf"},
                {"uid": "42", "content": b"purchase order"},
            ],
        ),
        patch(
            "backend.app.services.inbox_import.parse_purchase_order_email",
            side_effect=[ValueError("No PDF"), parsed_email()],
        ),
        patch(
            "backend.app.services.inbox_import.extract_pdf_text",
            return_value="PO Number: PO-4832",
        ),
        patch(
            "backend.app.services.inbox_import.extract_purchase_order",
            return_value=extraction(),
        ),
        patch(
            "backend.app.services.inbox_import.mark_email_processed"
        ) as mark_processed,
    ):
        response = client.post("/purchase-orders/import-email")

    assert response.status_code == 200
    mark_processed.assert_called_once_with("42")


def test_empty_inbox_returns_not_found():
    with patch(
        "backend.app.services.inbox_import.fetch_unread_emails",
        return_value=[],
    ):
        response = client.post("/purchase-orders/import-email")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No unread email with exactly one PDF attachment was found"
    }


def test_previously_imported_email_is_skipped():
    new_email = parsed_email() | {"message_id": "<po-NEW@acme.example>"}

    with (
        patch(
            "backend.app.services.inbox_import.fetch_unread_emails",
            return_value=[
                {"uid": "41", "content": b"duplicate"},
                {"uid": "42", "content": b"new"},
            ],
        ),
        patch(
            "backend.app.services.inbox_import.parse_purchase_order_email",
            side_effect=[parsed_email(), new_email],
        ),
        patch(
            "backend.app.services.inbox_import.email_was_imported",
            side_effect=[True, False],
        ),
        patch(
            "backend.app.services.inbox_import.extract_pdf_text",
            return_value="PO Number: PO-4832",
        ) as pdf_extractor,
        patch(
            "backend.app.services.inbox_import.extract_purchase_order",
            return_value=extraction(),
        ),
        patch(
            "backend.app.services.inbox_import.record_email_import"
        ) as record_import,
        patch(
            "backend.app.services.inbox_import.mark_email_processed"
        ) as mark_processed,
    ):
        response = client.post("/purchase-orders/import-email")

    assert response.status_code == 200
    pdf_extractor.assert_called_once_with(b"pdf bytes")
    record_import.assert_called_once()
    assert mark_processed.call_count == 2
    mark_processed.assert_any_call("41")
    mark_processed.assert_any_call("42")
