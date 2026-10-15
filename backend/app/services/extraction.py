import os

from dotenv import load_dotenv
from groq import APIConnectionError, Groq

from backend.app.schemas.extraction import (
    LLMPurchaseOrderExtraction,
    PurchaseOrderExtraction,
)

load_dotenv()

MODEL = "openai/gpt-oss-20b"
REQUIRED_ITEM_FIELDS = ("sku", "quantity", "unit_price")

INSTRUCTIONS = """Extract purchase-order data from the supplied text.
Use only values explicitly present in the text.
Never guess or invent a value.
Normalize dates to YYYY-MM-DD and currency to its three-letter ISO code only when
the document makes the currency unambiguous.
Capture product descriptions, printed or embroidered decoration instructions,
line totals, subtotal, discount, tax, freight, and total when present.
Use null for an optional scalar value that is absent.
Add only missing processing fields to missing_fields: po_number, customer,
ship_to, items, and each item's sku, quantity, or unit_price.
Use an empty items list and add 'items' to missing_fields when no line items are present.
For a partially specified line item, use null for its missing values and include paths such as 'items[0].quantity'.
Return only data that matches the provided schema."""


def extract_purchase_order(text: str):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    try:
        timeout = float(os.getenv("GROQ_TIMEOUT_SECONDS", "30"))
    except ValueError as error:
        raise RuntimeError("GROQ_TIMEOUT_SECONDS must be a number") from error

    if timeout <= 0:
        raise RuntimeError("GROQ_TIMEOUT_SECONDS must be greater than zero")

    client = Groq(api_key=api_key, timeout=timeout)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": INSTRUCTIONS},
                {"role": "user", "content": text},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "purchase_order_extraction",
                    "strict": True,
                    "schema": LLMPurchaseOrderExtraction.model_json_schema(),
                },
            },
        )
    except APIConnectionError as error:
        raise RuntimeError("Groq is unavailable") from error

    content = response.choices[0].message.content or "{}"
    extraction = PurchaseOrderExtraction.model_validate_json(content)
    return _normalize_missing_fields(extraction)


def _normalize_missing_fields(extraction: PurchaseOrderExtraction):
    """Derive processing requirements in code instead of trusting prompt wording."""
    missing_fields = []

    for field in ("po_number", "customer", "ship_to"):
        if not getattr(extraction, field):
            missing_fields.append(field)

    if not extraction.items:
        missing_fields.append("items")
    else:
        for index, item in enumerate(extraction.items):
            for field in REQUIRED_ITEM_FIELDS:
                if getattr(item, field) is None:
                    missing_fields.append(f"items[{index}].{field}")

    return extraction.model_copy(update={"missing_fields": missing_fields})
