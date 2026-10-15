from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.documents import locate_source, store_document


client = TestClient(app)


def test_source_lookup_is_on_demand_and_cached():
    document_id = store_document(
        "order.pdf",
        "application/pdf",
        b"fake pdf content",
        [
            "PO Number: PO-SOURCE-1\nHD-BLK-M | Quantity 10 | Unit Price 18",
            "Ship To: Austin Office",
        ],
    )

    first = locate_source(
        document_id,
        "items[0].quantity",
        "10",
        "HD-BLK-M",
    )
    second = locate_source(
        document_id,
        "items[0].quantity",
        "10",
        "HD-BLK-M",
    )

    assert first["found"] is True
    assert first["page"] == 1
    assert first["cached"] is False
    assert "HD-BLK-M" in first["snippet"]
    assert second["cached"] is True


def test_document_is_attached_to_created_review():
    document_id = store_document(
        "review.pdf",
        "application/pdf",
        b"review pdf content",
        ["HD-BLK-XL | Quantity 10 | Unit Price 20"],
    )

    process_response = client.post(
        "/purchase-orders/process",
        params={"document_id": document_id},
        json={
            "po_number": "PO-SOURCE-REVIEW",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-XL", "quantity": 10, "unit_price": 20}
            ],
            "ship_to": "Austin office",
        },
    )
    review_id = process_response.json()["review_id"]

    review = client.get(f"/reviews/{review_id}").json()

    assert review["source_document_id"] == document_id


def test_unknown_source_document_returns_not_found():
    response = client.get(
        "/documents/DOC-missing/source",
        params={"field_path": "total", "value": "100"},
    )

    assert response.status_code == 404
