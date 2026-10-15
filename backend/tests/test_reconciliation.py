from decimal import Decimal

from backend.app.schemas.purchase_order import PurchaseOrder
from backend.app.services.reconciliation import check_totals


def test_consistent_totals_pass_reconciliation():
    purchase_order = PurchaseOrder(
        po_number="PO-TOTALS-OK",
        customer="Acme Inc.",
        items=[
            {
                "sku": "HD-BLK-M",
                "quantity": 10,
                "unit_price": 18,
                "line_total": 180,
            }
        ],
        ship_to="Austin office",
        subtotal=180,
        discount=10,
        tax=5,
        freight=15,
        total=190,
    )

    result = check_totals(purchase_order)

    assert result == {
        "valid": True,
        "calculated_subtotal": Decimal("180"),
        "issues": [],
    }


def test_conflicting_totals_produce_explicit_issues():
    purchase_order = PurchaseOrder(
        po_number="PO-TOTALS-BAD",
        customer="Acme Inc.",
        items=[
            {
                "sku": "HD-BLK-M",
                "quantity": 10,
                "unit_price": 18,
                "line_total": 200,
            }
        ],
        ship_to="Austin office",
        subtotal=200,
        total=200,
    )

    reasons = [
        issue["reason"] for issue in check_totals(purchase_order)["issues"]
    ]

    assert reasons == [
        "line_total_mismatch",
        "subtotal_mismatch",
    ]


def test_total_reconciliation_allows_one_cent_tolerance():
    purchase_order = PurchaseOrder(
        po_number="PO-TOTALS-ROUNDING",
        customer="Acme Inc.",
        items=[
            {"sku": "HD-BLK-M", "quantity": 3, "unit_price": "18.333"}
        ],
        ship_to="Austin office",
        subtotal="55.00",
        total="55.00",
    )

    assert check_totals(purchase_order)["issues"] == []
