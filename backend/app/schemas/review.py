from typing import Literal

from pydantic import BaseModel, Field


class ReviewDecision(BaseModel):
    decision: Literal["approved", "rejected"]


class ReviewCorrection(BaseModel):
    field_path: str = Field(min_length=1, max_length=100)
    corrected_value: str = Field(min_length=1, max_length=1000)
    remember: bool = False


class PatternFeedback(BaseModel):
    feedback: Literal["accepted", "rejected"]
    po_number: str = Field(min_length=1, max_length=200)
