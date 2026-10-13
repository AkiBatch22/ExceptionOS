from backend.app.integrations.erp.catalog import PRODUCTS
from backend.app.schemas.purchase_order import PurchaseOrderItem


def check_prices(items: list[PurchaseOrderItem]):
    issues = []

    for item in items:
        product = PRODUCTS.get(item.sku)

        if product is not None and item.unit_price != product["unit_price"]:
            issues.append(
                {
                    "sku": item.sku,
                    "po_price": item.unit_price,
                    "erp_price": product["unit_price"],
                    "reason": "price_mismatch",
                }
            )

    return {"prices_match": not issues, "issues": issues}
