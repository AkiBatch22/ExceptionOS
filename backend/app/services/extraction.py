import os

from dotenv import load_dotenv
from groq import APIConnectionError, Groq

from backend.app.schemas.extraction import PurchaseOrderExtraction

load_dotenv()

MODEL = "openai/gpt-oss-20b"

INSTRUCTIONS = """Extract purchase-order data from the supplied text.
Use only values explicitly present in the text.
Never guess or invent a value.
Use null for a missing scalar value and add its field path to missing_fields.
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
                    "schema": PurchaseOrderExtraction.model_json_schema(),
                },
            },
        )
    except APIConnectionError as error:
        raise RuntimeError("Groq is unavailable") from error

    content = response.choices[0].message.content or "{}"
    return PurchaseOrderExtraction.model_validate_json(content)
