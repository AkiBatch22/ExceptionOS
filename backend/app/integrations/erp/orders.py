from psycopg.types.json import Jsonb

from backend.app.core.database import get_connection
from backend.app.schemas.purchase_order import PurchaseOrder


def create_order(purchase_order: PurchaseOrder):
    erp_order_id = f"ERP-{purchase_order.po_number}"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO erp_orders (erp_order_id, po_number, purchase_order)
            VALUES (%s, %s, %s)
            ON CONFLICT (erp_order_id) DO UPDATE
            SET purchase_order = EXCLUDED.purchase_order
            """,
            (
                erp_order_id,
                purchase_order.po_number,
                Jsonb(purchase_order.model_dump(mode="json")),
            ),
        )

    return erp_order_id


def get_order(erp_order_id: str):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT purchase_order FROM erp_orders WHERE erp_order_id = %s",
            (erp_order_id,),
        ).fetchone()

    if row is None:
        return None

    return PurchaseOrder.model_validate(row[0])
