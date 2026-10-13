from fastapi.testclient import TestClient

from backend.app.integrations.erp.orders import get_order
from backend.app.main import app

client = TestClient(app)


def test_created_order_events_can_be_read():
    client.post(
        "/purchase-orders/process",
        json={
            "po_number": "PO-READY",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-M", "quantity": 1, "unit_price": 18},
            ],
            "ship_to": "Austin office",
        },
    )

    response = client.get("/purchase-orders/PO-READY/events")

    assert response.status_code == 200
    assert response.json() == {
        "po_number": "PO-READY",
        "events": [
            {"event": "purchase_order_received", "details": {}},
            {
                "event": "erp_order_created",
                "details": {"erp_order_id": "ERP-PO-READY"},
            },
        ],
    }


def test_approved_review_events_can_be_read():
    process_response = client.post(
        "/purchase-orders/process",
        json={
            "po_number": "PO-REVIEW",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-XL", "quantity": 10, "unit_price": 20},
            ],
            "ship_to": "Austin office",
        },
    )
    review_id = process_response.json()["review_id"]
    client.post(
        f"/reviews/{review_id}/decision",
        json={"decision": "approved"},
    )

    response = client.get("/purchase-orders/PO-REVIEW/events")

    assert response.status_code == 200
    assert response.json()["events"] == [
        {"event": "purchase_order_received", "details": {}},
        {"event": "review_created", "details": {"review_id": review_id}},
        {"event": "review_approved", "details": {"review_id": review_id}},
        {
            "event": "erp_order_created",
            "details": {"erp_order_id": "ERP-PO-REVIEW"},
        },
    ]


def test_rejected_review_records_no_order_event():
    process_response = client.post(
        "/purchase-orders/process",
        json={
            "po_number": "PO-REJECTED",
            "customer": "Unknown Company",
            "items": [
                {"sku": "HD-BLK-M", "quantity": 1, "unit_price": 18},
            ],
            "ship_to": "Austin office",
        },
    )
    review_id = process_response.json()["review_id"]
    client.post(
        f"/reviews/{review_id}/decision",
        json={"decision": "rejected"},
    )

    response = client.get("/purchase-orders/PO-REJECTED/events")

    assert response.json()["events"][-1] == {
        "event": "review_rejected",
        "details": {"review_id": review_id},
    }
    assert get_order("ERP-PO-REJECTED") is None


def test_purchase_order_without_events_returns_empty_history():
    response = client.get("/purchase-orders/PO-MISSING/events")

    assert response.status_code == 200
    assert response.json() == {"po_number": "PO-MISSING", "events": []}
