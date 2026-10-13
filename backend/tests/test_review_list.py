from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def create_pending_review(po_number: str):
    response = client.post(
        "/purchase-orders/process",
        json={
            "po_number": po_number,
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-XL", "quantity": 10, "unit_price": 20},
            ],
            "ship_to": "Austin office",
        },
    )
    return response.json()["review_id"]


def test_review_list_defaults_to_pending():
    pending_review_id = create_pending_review("PO-PENDING")
    approved_review_id = create_pending_review("PO-APPROVED")
    client.post(
        f"/reviews/{approved_review_id}/decision",
        json={"decision": "approved"},
    )

    response = client.get("/reviews")

    assert response.status_code == 200
    assert response.json() == {
        "reviews": [
            {
                "review_id": pending_review_id,
                "po_number": "PO-PENDING",
                "customer": "Acme Inc.",
                "status": "pending",
                "issue_count": 1,
            }
        ]
    }


def test_review_list_can_filter_by_status():
    approved_review_id = create_pending_review("PO-APPROVED")
    client.post(
        f"/reviews/{approved_review_id}/decision",
        json={"decision": "approved"},
    )

    response = client.get("/reviews?status=approved")

    assert response.status_code == 200
    assert response.json() == {
        "reviews": [
            {
                "review_id": approved_review_id,
                "po_number": "PO-APPROVED",
                "customer": "Acme Inc.",
                "status": "approved",
                "issue_count": 1,
            }
        ]
    }


def test_review_list_rejects_unknown_status():
    response = client.get("/reviews?status=unknown")

    assert response.status_code == 422
