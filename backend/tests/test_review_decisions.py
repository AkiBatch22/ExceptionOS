from fastapi.testclient import TestClient

from backend.app.integrations.erp.orders import get_order
from backend.app.main import app

client = TestClient(app)


def create_pending_review():
    response = client.post(
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
    return response.json()["review_id"]


def test_approval_creates_erp_order():
    review_id = create_pending_review()

    response = client.post(
        f"/reviews/{review_id}/decision",
        json={"decision": "approved"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "review_id": "REVIEW-PO-4832",
        "status": "approved",
        "erp_order_id": "ERP-PO-4832",
    }
    assert get_order("ERP-PO-4832") is not None


def test_rejection_does_not_create_erp_order():
    review_id = create_pending_review()

    response = client.post(
        f"/reviews/{review_id}/decision",
        json={"decision": "rejected"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "review_id": "REVIEW-PO-4832",
        "status": "rejected",
        "erp_order_id": None,
    }
    assert get_order("ERP-PO-4832") is None


def test_missing_review_cannot_be_decided():
    response = client.post(
        "/reviews/REVIEW-MISSING/decision",
        json={"decision": "approved"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Review not found"}


def test_review_cannot_be_decided_twice():
    review_id = create_pending_review()
    client.post(
        f"/reviews/{review_id}/decision",
        json={"decision": "rejected"},
    )

    response = client.post(
        f"/reviews/{review_id}/decision",
        json={"decision": "approved"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Review already decided"}
    assert get_order("ERP-PO-4832") is None
