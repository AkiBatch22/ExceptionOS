from backend.app.integrations.erp.catalog import PRODUCTS
from backend.app.schemas.purchase_order import PurchaseOrderItem


def check_inventory(items: list[PurchaseOrderItem]):
    issues = []

    for item in items:
        product = PRODUCTS.get(item.sku)

        if product is None:
            issues.append(
                {
                    "sku": item.sku,
                    "requested": item.quantity,
                    "available": None,
                    "reason": "unknown_sku",
                }
            )
        elif item.quantity > product["stock"]:
            issues.append(
                {
                    "sku": item.sku,
                    "requested": item.quantity,
                    "available": product["stock"],
                    "reason": "insufficient_stock",
                }
            )

    return {"can_fulfill": not issues, "issues": issues}
