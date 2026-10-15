import re

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from fastapi.encoders import jsonable_encoder

from backend.app.core.database import get_connection
from backend.app.integrations.erp.orders import create_order
from backend.app.schemas.purchase_order import PurchaseOrder
from backend.app.services.audit import record_event
from backend.app.services.assessment import assess_purchase_order
from backend.app.services.correction_memory import (
    is_rememberable,
    party_key,
    remember_correction,
)
from backend.app.services.recommendations import recommend_actions


def create_review(
    purchase_order: PurchaseOrder,
    issues: list,
    source_document_id: str | None = None,
):
    review_id = f"REVIEW-{purchase_order.po_number}"
    recommendations = recommend_actions(issues)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reviews (
                review_id, po_number, status, purchase_order, issues,
                erp_order_id, source_document_id, recommendations
            )
            VALUES (%s, %s, 'pending', %s, %s, NULL, %s, %s)
            ON CONFLICT (review_id) DO UPDATE
            SET status = 'pending',
                purchase_order = EXCLUDED.purchase_order,
                issues = EXCLUDED.issues,
                erp_order_id = NULL,
                source_document_id = EXCLUDED.source_document_id,
                recommendations = EXCLUDED.recommendations
            """,
            (
                review_id,
                purchase_order.po_number,
                Jsonb(purchase_order.model_dump(mode="json")),
                Jsonb(jsonable_encoder(issues)),
                source_document_id,
                Jsonb(recommendations),
            ),
        )

    return review_id


def get_review(review_id: str):
    with get_connection() as connection:
        connection.row_factory = dict_row
        review = connection.execute(
            """
            SELECT review_id, status, purchase_order, issues, erp_order_id,
                source_document_id, recommendations
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
    from backend.app.services.audit import get_events

    review["events"] = get_events(review["purchase_order"].po_number)
    return review


def _field_parts(field_path: str):
    item_match = re.fullmatch(
        r"items\[(\d+)\]\.(sku|description|quantity|unit_price|line_total)",
        field_path,
    )
    if item_match:
        return ("item", int(item_match.group(1)), item_match.group(2))
    if field_path in {
        "customer",
        "ship_to",
        "po_date",
        "requested_delivery_date",
        "currency",
        "subtotal",
        "discount",
        "tax",
        "freight",
        "total",
    }:
        return ("root", field_path)
    raise ValueError("This purchase-order field cannot be corrected here")


def apply_review_correction(
    review: dict,
    field_path: str,
    corrected_value: str,
    remember: bool,
):
    if review["status"] != "pending":
        raise ValueError("Only pending reviews can be corrected")

    purchase_order = review["purchase_order"]
    payload = purchase_order.model_dump(mode="json")
    parts = _field_parts(field_path)
    if parts[0] == "item":
        _, index, field = parts
        if index >= len(payload["items"]):
            raise ValueError("The selected item does not exist")
        original_value = payload["items"][index].get(field)
        payload["items"][index][field] = corrected_value
    else:
        _, field = parts
        original_value = payload.get(field)
        payload[field] = corrected_value

    corrected_order = PurchaseOrder.model_validate(payload)
    assessment = assess_purchase_order(corrected_order)
    recommendations = recommend_actions(assessment["issues"])
    original_customer = purchase_order.customer

    if remember and not is_rememberable(field_path):
        raise ValueError("Only customer, ship-to, and item SKU corrections can be remembered")

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE reviews
            SET purchase_order = %s, issues = %s, recommendations = %s
            WHERE review_id = %s
            """,
            (
                Jsonb(corrected_order.model_dump(mode="json")),
                Jsonb(jsonable_encoder(assessment["issues"])),
                Jsonb(recommendations),
                review["review_id"],
            ),
        )
        connection.execute(
            """
            INSERT INTO review_corrections (
                review_id, party_key, field_path, original_value,
                corrected_value, remembered
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                review["review_id"],
                party_key(original_customer),
                field_path,
                None if original_value is None else str(original_value),
                corrected_value,
                remember,
            ),
        )

    pattern_id = None
    if remember:
        pattern_id = remember_correction(
            original_customer,
            field_path,
            "" if original_value is None else str(original_value),
            corrected_value,
        )

    record_event(
        corrected_order.po_number,
        "correction_applied",
        {
            "review_id": review["review_id"],
            "field_path": field_path,
            "original_value": original_value,
            "corrected_value": corrected_value,
            "remembered": remember,
            "pattern_id": pattern_id,
        },
    )
    if remember:
        record_event(
            corrected_order.po_number,
            "correction_pattern_remembered",
            {"pattern_id": pattern_id, "field_path": field_path},
        )

    return get_review(review["review_id"])


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
