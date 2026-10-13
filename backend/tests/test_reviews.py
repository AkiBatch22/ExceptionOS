from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_pending_review_can_be_read():
    process_response = client.post(
        "/purchase-orders/process",
        json={
            "po_number": "PO-4832",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-XL", "quantity": 10, "unit_price": 20},
            ],
            "ship_to": "Austin office",
        },
    )
    review_id = process_response.json()["review_id"]

    response = client.get(f"/reviews/{review_id}")

    assert response.status_code == 200
    assert response.json()["review_id"] == "REVIEW-PO-4832"
    assert response.json()["status"] == "pending"
    assert response.json()["purchase_order"]["po_number"] == "PO-4832"
    assert response.json()["issues"][0]["reason"] == "insufficient_stock"


def test_missing_review_returns_not_found():
    response = client.get("/reviews/REVIEW-MISSING")

    assert response.status_code == 404
    assert response.json() == {"detail": "Review not found"}
