from time import perf_counter

from backend.app.integrations.erp.orders import create_order
from backend.app.schemas.purchase_order import PurchaseOrder
from backend.app.services.assessment import assess_purchase_order
from backend.app.services.audit import record_event
from backend.app.services.reviews import create_review


def process_purchase_order(
    purchase_order: PurchaseOrder,
    source_document_id: str | None = None,
):
    started_at = perf_counter()
    record_event(purchase_order.po_number, "purchase_order_received", {})
    assessment = assess_purchase_order(purchase_order)
    record_event(
        purchase_order.po_number,
        "assessment_completed",
        {
            "duration_ms": round((perf_counter() - started_at) * 1000),
            "decision": assessment["decision"],
            "issue_count": len(assessment["issues"]),
        },
    )

    if assessment["decision"] != "ready":
        review_id = create_review(
            purchase_order,
            assessment["issues"],
            source_document_id,
        )
        record_event(
            purchase_order.po_number,
            "review_created",
            {"review_id": review_id},
        )

        return {
            "status": "human_review_required",
            "review_id": review_id,
            "erp_order_id": None,
            "issues": assessment["issues"],
        }

    erp_order_id = create_order(purchase_order)
    record_event(
        purchase_order.po_number,
        "erp_order_created",
        {"erp_order_id": erp_order_id},
    )

    return {
        "status": "created",
        "erp_order_id": erp_order_id,
        "issues": [],
    }
