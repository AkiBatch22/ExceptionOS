from decimal import Decimal

from backend.app.schemas.purchase_order import PurchaseOrder


TOLERANCE = Decimal("0.01")


def _different(left: Decimal, right: Decimal):
    return abs(left - right) > TOLERANCE


def check_totals(purchase_order: PurchaseOrder):
    issues = []
    calculated_subtotal = Decimal("0")

    for index, item in enumerate(purchase_order.items):
        expected_line_total = item.quantity * item.unit_price
        calculated_subtotal += expected_line_total

        if item.line_total is not None and _different(
            item.line_total, expected_line_total
        ):
            issues.append(
                {
                    "reason": "line_total_mismatch",
                    "item_index": index,
                    "sku": item.sku,
                    "document_value": item.line_total,
                    "expected_value": expected_line_total,
                }
            )

    if purchase_order.subtotal is not None and _different(
        purchase_order.subtotal, calculated_subtotal
    ):
        issues.append(
            {
                "reason": "subtotal_mismatch",
                "document_value": purchase_order.subtotal,
                "expected_value": calculated_subtotal,
            }
        )

    if purchase_order.total is not None:
        base = purchase_order.subtotal or calculated_subtotal
        expected_total = (
            base
            - (purchase_order.discount or Decimal("0"))
            + (purchase_order.tax or Decimal("0"))
            + (purchase_order.freight or Decimal("0"))
        )
        if _different(purchase_order.total, expected_total):
            issues.append(
                {
                    "reason": "total_mismatch",
                    "document_value": purchase_order.total,
                    "expected_value": expected_total,
                }
            )

    return {
        "valid": not issues,
        "calculated_subtotal": calculated_subtotal,
        "issues": issues,
    }
