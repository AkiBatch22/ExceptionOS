from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_prices_match():
    response = client.post(
        "/purchase-orders/check-prices",
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
    assert response.json() == {"prices_match": True, "issues": []}


def test_price_mismatch():
    response = client.post(
        "/purchase-orders/check-prices",
        json={
            "po_number": "PO-4832",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-M", "quantity": 50, "unit_price": 17},
            ],
            "ship_to": "Austin office",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "prices_match": False,
        "issues": [
            {
                "sku": "HD-BLK-M",
                "po_price": 17,
                "erp_price": 18,
                "reason": "price_mismatch",
            }
        ],
    }


def test_price_check_skips_unknown_sku():
    response = client.post(
        "/purchase-orders/check-prices",
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
    assert response.json() == {"prices_match": True, "issues": []}
