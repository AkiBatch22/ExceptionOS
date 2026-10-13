from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_valid_purchase_order():
    response = client.post(
        "/purchase-orders/validate",
        json={
            "po_number": "PO-4832",
            "customer": "Acme Inc.",
            "items": [
                {
                    "sku": "HD-BLK-M",
                    "quantity": 50,
                    "unit_price": 18,
                }
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"valid": True}


def test_purchase_order_rejects_zero_quantity():
    response = client.post(
        "/purchase-orders/validate",
        json={
            "po_number": "PO-4832",
            "customer": "Acme Inc.",
            "items": [
                {
                    "sku": "HD-BLK-M",
                    "quantity": 0,
                    "unit_price": 18,
                }
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 422
