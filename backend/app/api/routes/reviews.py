from typing import Literal

from fastapi import APIRouter, HTTPException

from backend.app.schemas.review import (
    PatternFeedback,
    ReviewCorrection,
    ReviewDecision,
)
from backend.app.services.audit import record_event
from backend.app.services.correction_memory import record_pattern_feedback
from backend.app.services.reviews import (
    apply_review_correction,
    decide_review,
    get_review,
    list_reviews,
)

router = APIRouter(prefix="/reviews")


@router.get("")
def read_reviews(
    status: Literal["pending", "approved", "rejected"] = "pending",
):
    return {"reviews": list_reviews(status)}


@router.get("/{review_id}")
def read_review(review_id: str):
    review = get_review(review_id)

    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    return review


@router.post("/{review_id}/decision")
def submit_review_decision(review_id: str, review_decision: ReviewDecision):
    review = get_review(review_id)

    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    if review["status"] != "pending":
        raise HTTPException(status_code=409, detail="Review already decided")

    return decide_review(review, review_decision.decision)


@router.post("/{review_id}/corrections")
def submit_review_correction(
    review_id: str,
    correction: ReviewCorrection,
):
    review = get_review(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    try:
        return apply_review_correction(
            review,
            correction.field_path,
            correction.corrected_value,
            correction.remember,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/patterns/{pattern_id}/feedback")
def submit_pattern_feedback(pattern_id: int, feedback: PatternFeedback):
    if not record_pattern_feedback(pattern_id, feedback.feedback):
        raise HTTPException(status_code=404, detail="Correction pattern not found")

    record_event(
        feedback.po_number,
        f"supplier_suggestion_{feedback.feedback}",
        {"pattern_id": pattern_id},
    )
    return {"pattern_id": pattern_id, "status": feedback.feedback}
