from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def create_ready_order(po_number: str):
    return client.post(
        "/purchase-orders/process",
        json={
            "po_number": po_number,
            "customer": "Acme Inc.",
            "items": [{"sku": "HD-BLK-M", "quantity": 2, "unit_price": 18}],
            "ship_to": "Austin office",
        },
    )


def test_created_erp_orders_can_be_listed_and_opened():
    create_ready_order("PO-ORDER-LIST")

    list_response = client.get("/erp-orders")
    detail_response = client.get("/erp-orders/ERP-PO-ORDER-LIST")

    assert list_response.status_code == 200
    assert list_response.json()["orders"][0]["erp_order_id"] == "ERP-PO-ORDER-LIST"
    assert list_response.json()["orders"][0]["purchase_order"]["customer"] == "Acme Inc."
    assert detail_response.status_code == 200
    assert detail_response.json()["purchase_order"]["items"][0]["quantity"] == 2
    assert detail_response.json()["events"][-1]["event"] == "erp_order_created"


def test_missing_erp_order_returns_not_found():
    response = client.get("/erp-orders/ERP-MISSING")

    assert response.status_code == 404
    assert response.json() == {"detail": "ERP order not found"}
