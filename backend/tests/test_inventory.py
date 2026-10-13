from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_inventory_can_fulfill_order():
    response = client.post(
        "/purchase-orders/check-inventory",
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
    assert response.json() == {"can_fulfill": True, "issues": []}


def test_inventory_reports_insufficient_stock():
    response = client.post(
        "/purchase-orders/check-inventory",
        json={
            "po_number": "PO-4832",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-XL", "quantity": 10, "unit_price": 20},
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "can_fulfill": False,
        "issues": [
            {
                "sku": "HD-BLK-XL",
                "requested": 10,
                "available": 5,
                "reason": "insufficient_stock",
            }
        ],
    }


def test_inventory_reports_unknown_sku():
    response = client.post(
        "/purchase-orders/check-inventory",
        json={
            "po_number": "PO-4832",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "UNKNOWN", "quantity": 1, "unit_price": 10},
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "can_fulfill": False,
        "issues": [
            {
                "sku": "UNKNOWN",
                "requested": 1,
                "available": None,
                "reason": "unknown_sku",
            }
        ],
    }
