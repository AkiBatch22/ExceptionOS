from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from backend.app.core.database import get_connection
from backend.app.integrations.erp.orders import create_order
from backend.app.schemas.purchase_order import PurchaseOrder
from backend.app.services.audit import record_event


def create_review(purchase_order: PurchaseOrder, issues: list):
    review_id = f"REVIEW-{purchase_order.po_number}"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reviews (
                review_id, po_number, status, purchase_order, issues, erp_order_id
            )
            VALUES (%s, %s, 'pending', %s, %s, NULL)
            ON CONFLICT (review_id) DO UPDATE
            SET status = 'pending',
                purchase_order = EXCLUDED.purchase_order,
                issues = EXCLUDED.issues,
                erp_order_id = NULL
            """,
            (
                review_id,
                purchase_order.po_number,
                Jsonb(purchase_order.model_dump(mode="json")),
                Jsonb(issues),
            ),
        )

    return review_id


def get_review(review_id: str):
    with get_connection() as connection:
        connection.row_factory = dict_row
        review = connection.execute(
            """
            SELECT review_id, status, purchase_order, issues, erp_order_id
            FROM reviews
            WHERE review_id = %s
            """,
            (review_id,),
        ).fetchone()

    if review is None:
        return None

    review["purchase_order"] = PurchaseOrder.model_validate(
        review["purchase_order"]
    )
    return review


def list_reviews(status: str):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                review_id,
                po_number,
                purchase_order->>'customer' AS customer,
                status,
                jsonb_array_length(issues) AS issue_count
            FROM reviews
            WHERE status = %s
            ORDER BY created_at, review_id
            """,
            (status,),
        ).fetchall()

    return [
        {
            "review_id": review_id,
            "po_number": po_number,
            "customer": customer,
            "status": review_status,
            "issue_count": issue_count,
        }
        for review_id, po_number, customer, review_status, issue_count in rows
    ]


def decide_review(review: dict, decision: str):
    purchase_order = review["purchase_order"]
    erp_order_id = None

    record_event(
        purchase_order.po_number,
        f"review_{decision}",
        {"review_id": review["review_id"]},
    )

    if decision == "approved":
        erp_order_id = create_order(purchase_order)
        record_event(
            purchase_order.po_number,
            "erp_order_created",
            {"erp_order_id": erp_order_id},
        )

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE reviews
            SET status = %s, erp_order_id = %s
            WHERE review_id = %s
            """,
            (decision, erp_order_id, review["review_id"]),
        )

    return {
        "review_id": review["review_id"],
        "status": decision,
        "erp_order_id": erp_order_id,
    }
