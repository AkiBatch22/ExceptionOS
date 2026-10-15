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
    body = response.json()
    assert body["po_number"] == "PO-READY"
    assert [event["event"] for event in body["events"]] == [
        "purchase_order_received",
        "assessment_completed",
        "erp_order_created",
    ]
    assert all(event["created_at"] for event in body["events"])
    assert body["events"][1]["details"]["duration_ms"] >= 0
    assert body["events"][2]["details"] == {"erp_order_id": "ERP-PO-READY"}


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
    events = response.json()["events"]
    assert [event["event"] for event in events] == [
        "purchase_order_received",
        "assessment_completed",
        "review_created",
        "review_approved",
        "erp_order_created",
    ]
    assert events[2]["details"] == {"review_id": review_id}
    assert all(event["created_at"] for event in events)


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

    last_event = response.json()["events"][-1]
    assert last_event["event"] == "review_rejected"
    assert last_event["details"] == {"review_id": review_id}
    assert last_event["created_at"]
    assert get_order("ERP-PO-REJECTED") is None


def test_purchase_order_without_events_returns_empty_history():
    response = client.get("/purchase-orders/PO-MISSING/events")

    assert response.status_code == 200
    assert response.json() == {"po_number": "PO-MISSING", "events": []}
