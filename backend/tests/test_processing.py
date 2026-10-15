from fastapi.testclient import TestClient

from backend.app.integrations.erp.orders import get_order
from backend.app.main import app
from backend.app.services.reviews import get_review

client = TestClient(app)


def test_ready_purchase_order_is_created():
    response = client.post(
        "/purchase-orders/process",
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
    assert response.json() == {
        "status": "created",
        "erp_order_id": "ERP-PO-4832",
        "issues": [],
    }
    assert get_order("ERP-PO-4832") is not None
    assert get_review("REVIEW-PO-4832") is None


def test_purchase_order_with_issues_is_not_created():
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

    assert response.status_code == 200
    assert response.json() == {
        "status": "human_review_required",
        "review_id": "REVIEW-PO-4832",
        "erp_order_id": None,
        "issues": [
            {
                "sku": "HD-BLK-XL",
                "requested": 10,
                "available": 5,
                "reason": "insufficient_stock",
            }
        ],
    }
    assert get_order("ERP-PO-4832") is None
    assert get_review("REVIEW-PO-4832") is not None


def test_decimal_reconciliation_issue_can_create_review():
    response = client.post(
        "/purchase-orders/process",
        json={
            "po_number": "PO-TOTAL-MISMATCH",
            "customer": "Acme Inc.",
            "items": [
                {
                    "sku": "HD-BLK-M",
                    "quantity": 10,
                    "unit_price": 18,
                    "line_total": 200,
                }
            ],
            "ship_to": "Austin office",
            "subtotal": 200,
            "total": 200,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "human_review_required"
    review = client.get(f"/reviews/{response.json()['review_id']}")
    assert review.status_code == 200
    assert {issue["reason"] for issue in review.json()["issues"]} >= {
        "line_total_mismatch",
        "subtotal_mismatch",
    }
