from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_purchase_order_is_ready():
    response = client.post(
        "/purchase-orders/assess",
        json={
            "po_number": "PO-4832",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18},
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"decision": "ready", "issues": []}


def test_purchase_order_requires_human_review():
    response = client.post(
        "/purchase-orders/assess",
        json={
            "po_number": "PO-4832",
            "customer": "Unknown Company",
            "items": [
                {"sku": "HD-BLK-XL", "quantity": 10, "unit_price": 19},
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "decision": "human_review_required",
        "issues": [
            {
                "customer": "Unknown Company",
                "reason": "unknown_customer",
            },
            {
                "sku": "HD-BLK-XL",
                "requested": 10,
                "available": 5,
                "reason": "insufficient_stock",
            },
            {
                "sku": "HD-BLK-XL",
                "po_price": 19,
                "erp_price": 20,
                "reason": "price_mismatch",
            },
        ],
    }
