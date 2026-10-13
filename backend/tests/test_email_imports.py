from backend.app.services.email_imports import (
    email_was_imported,
    record_email_import,
)
from backend.app.schemas.extraction import PurchaseOrderExtraction


def test_email_import_is_persisted_once():
    message_id = "<po-4832@acme.example>"
    purchase_order = PurchaseOrderExtraction(
        po_number="PO-4832",
        customer="Acme Inc.",
        items=[{"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18}],
        ship_to="Austin office",
        missing_fields=[],
    )

    assert email_was_imported(message_id) is False

    record_email_import(
        message_id=message_id,
        imap_uid="42",
        sender="orders@acme.example",
        subject="Purchase order PO-4832",
        attachment_name="order.pdf",
        purchase_order=purchase_order,
    )
    record_email_import(
        message_id=message_id,
        imap_uid="42",
        sender="orders@acme.example",
        subject="Purchase order PO-4832",
        attachment_name="order.pdf",
        purchase_order=purchase_order,
    )

    assert email_was_imported(message_id) is True
