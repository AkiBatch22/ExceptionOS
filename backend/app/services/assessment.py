from backend.app.schemas.purchase_order import PurchaseOrder
from backend.app.services.customers import check_customer
from backend.app.services.inventory import check_inventory
from backend.app.services.pricing import check_prices
from backend.app.services.reconciliation import check_totals


def assess_purchase_order(purchase_order: PurchaseOrder):
    issues = []

    issues.extend(check_customer(purchase_order.customer)["issues"])
    issues.extend(check_inventory(purchase_order.items)["issues"])
    issues.extend(check_prices(purchase_order.items)["issues"])
    issues.extend(check_totals(purchase_order)["issues"])

    decision = "human_review_required" if issues else "ready"

    return {"decision": decision, "issues": issues}
