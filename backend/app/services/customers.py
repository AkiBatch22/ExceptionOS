from backend.app.integrations.erp.catalog import CUSTOMERS


def check_customer(customer: str):
    if customer in CUSTOMERS:
        return {"customer_exists": True, "issues": []}

    return {
        "customer_exists": False,
        "issues": [
            {
                "customer": customer,
                "reason": "unknown_customer",
            }
        ],
    }
