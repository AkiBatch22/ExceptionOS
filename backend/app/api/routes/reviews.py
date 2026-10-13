from typing import Literal

from fastapi import APIRouter, HTTPException

from backend.app.schemas.review import ReviewDecision
from backend.app.services.reviews import decide_review, get_review, list_reviews

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
