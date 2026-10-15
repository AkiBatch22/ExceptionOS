import json
import os

from fastapi.encoders import jsonable_encoder
from groq import Groq
from pydantic import BaseModel, ConfigDict, Field


BASIC_ISSUES = {
    "unknown_customer",
    "unknown_sku",
    "insufficient_stock",
    "price_mismatch",
    "line_total_mismatch",
    "subtotal_mismatch",
    "total_mismatch",
}

FALLBACK_ACTIONS = {
    "unknown_customer": "Confirm the customer record or map it to an existing ERP customer.",
    "unknown_sku": "Confirm the supplier SKU and map it to an internal SKU.",
    "insufficient_stock": "Check replenishment timing or discuss a partial shipment with the customer.",
    "price_mismatch": "Compare the PO price with the approved customer price before proceeding.",
    "line_total_mismatch": "Verify the quantity, unit price, and stated line total.",
    "subtotal_mismatch": "Recalculate the line totals and confirm the stated subtotal.",
    "total_mismatch": "Verify subtotal, discount, tax, freight, and final total.",
}


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actions: list[str] = Field(max_length=3)


INSTRUCTIONS = """Recommend at most three short, safe operator actions for the
supplied basic purchase-order issues. Do not approve or reject the order. Do not
invent inventory, pricing, customer, policy, tax, legal, fraud, or payment facts.
Return only non-executing recommendations. The supplied issues have already been
restricted to the allowed basic categories."""


def _fallback(issues: list[dict]):
    actions = []
    for issue in issues:
        action = FALLBACK_ACTIONS.get(issue.get("reason"))
        if action and action not in actions:
            actions.append(action)
    return actions[:3]


def recommend_actions(issues: list[dict]):
    basic_issues = [
        issue for issue in issues if issue.get("reason") in BASIC_ISSUES
    ]
    if not basic_issues:
        return []

    fallback = _fallback(basic_issues)
    if os.getenv("ENABLE_LLM_RECOMMENDATIONS", "true").casefold() != "true":
        return fallback

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return fallback

    try:
        client = Groq(api_key=api_key, timeout=15)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": INSTRUCTIONS},
                {
                    "role": "user",
                    "content": json.dumps(jsonable_encoder(basic_issues)),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "basic_issue_recommendations",
                    "strict": True,
                    "schema": RecommendationResponse.model_json_schema(),
                },
            },
        )
        result = RecommendationResponse.model_validate_json(
            response.choices[0].message.content or "{}"
        )
        return result.actions
    except Exception:
        return fallback
