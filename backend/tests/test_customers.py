from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_customer_exists():
    response = client.post(
        "/purchase-orders/check-customer",
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
    assert response.json() == {"customer_exists": True, "issues": []}


def test_unknown_customer():
    response = client.post(
        "/purchase-orders/check-customer",
        json={
            "po_number": "PO-4832",
            "customer": "Unknown Company",
            "items": [
                {"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18},
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "customer_exists": False,
        "issues": [
            {
                "customer": "Unknown Company",
                "reason": "unknown_customer",
            }
        ],
    }
