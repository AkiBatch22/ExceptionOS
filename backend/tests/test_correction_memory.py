from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.extraction import PurchaseOrderExtraction
from backend.app.services.correction_memory import find_suggestions

client = TestClient(app)


def create_unknown_sku_review(po_number: str):
    response = client.post(
        "/purchase-orders/process",
        json={
            "po_number": po_number,
            "customer": "Acme Inc.",
            "items": [{"sku": "HD-B1K-M", "quantity": 2, "unit_price": 18}],
            "ship_to": "Austin office",
        },
    )
    assert response.status_code == 200
    return response.json()["review_id"]


def test_correction_can_be_applied_once_without_creating_memory():
    review_id = create_unknown_sku_review("PO-CORRECT-ONCE")

    response = client.post(
        f"/reviews/{review_id}/corrections",
        json={
            "field_path": "items[0].sku",
            "corrected_value": "HD-BLK-M",
            "remember": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["purchase_order"]["items"][0]["sku"] == "HD-BLK-M"
    assert body["issues"] == []
    extraction = PurchaseOrderExtraction(
        po_number="PO-NEXT",
        customer="Acme Inc.",
        items=[{"sku": "HD-B1K-M", "quantity": 1, "unit_price": 18}],
        ship_to="Austin office",
        missing_fields=[],
    )
    assert find_suggestions(extraction) == []


def test_remembered_correction_is_visible_but_not_silently_applied():
    review_id = create_unknown_sku_review("PO-CORRECT-REMEMBER")
    response = client.post(
        f"/reviews/{review_id}/corrections",
        json={
            "field_path": "items[0].sku",
            "corrected_value": "HD-BLK-M",
            "remember": True,
        },
    )
    assert response.status_code == 200

    extraction = PurchaseOrderExtraction(
        po_number="PO-NEXT",
        customer="Acme Inc.",
        items=[{"sku": "HD-B1K-M", "quantity": 1, "unit_price": 18}],
        ship_to="Austin office",
        missing_fields=[],
    )
    suggestions = find_suggestions(extraction)

    assert extraction.items[0].sku == "HD-B1K-M"
    assert suggestions[0]["field_path"] == "items[0].sku"
    assert suggestions[0]["original_value"] == "HD-B1K-M"
    assert suggestions[0]["corrected_value"] == "HD-BLK-M"

    feedback = client.post(
        f"/reviews/patterns/{suggestions[0]['pattern_id']}/feedback",
        json={"feedback": "accepted", "po_number": "PO-NEXT"},
    )
    assert feedback.status_code == 200


def test_order_specific_field_cannot_be_remembered():
    review_id = create_unknown_sku_review("PO-UNSAFE-MEMORY")

    response = client.post(
        f"/reviews/{review_id}/corrections",
        json={
            "field_path": "items[0].quantity",
            "corrected_value": "1",
            "remember": True,
        },
    )

    assert response.status_code == 422
    assert "can be remembered" in response.json()["detail"]
