from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderText(BaseModel):
    text: str = Field(min_length=1)


class ExtractedPurchaseOrderItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str | None
    description: str | None = None
    quantity: int | None
    unit_price: float | None
    line_total: Decimal | None = None
    decoration_requirements: list[str] | None = None


class PurchaseOrderExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    po_number: str | None
    customer: str | None
    po_date: date | None = None
    requested_delivery_date: date | None = None
    currency: str | None = None
    items: list[ExtractedPurchaseOrderItem]
    ship_to: str | None
    subtotal: Decimal | None = None
    discount: Decimal | None = None
    tax: Decimal | None = None
    freight: Decimal | None = None
    total: Decimal | None = None
    missing_fields: list[str]


class LLMExtractedPurchaseOrderItem(BaseModel):
    """All keys are required so strict JSON-schema providers remain compatible."""

    model_config = ConfigDict(extra="forbid")

    sku: str | None
    description: str | None
    quantity: int | None
    unit_price: float | None
    line_total: float | None
    decoration_requirements: list[str] | None


class LLMPurchaseOrderExtraction(BaseModel):
    """Provider schema; optional business values are represented as required nullable keys."""

    model_config = ConfigDict(extra="forbid")

    po_number: str | None
    customer: str | None
    po_date: date | None
    requested_delivery_date: date | None
    currency: str | None
    items: list[LLMExtractedPurchaseOrderItem]
    ship_to: str | None
    subtotal: float | None
    discount: float | None
    tax: float | None
    freight: float | None
    total: float | None
    missing_fields: list[str]


class ExtractionQuality(BaseModel):
    score: float = Field(ge=0, le=1)
    level: str
    signals: list[str]


class SuggestedCorrection(BaseModel):
    pattern_id: int
    party_label: str
    field_path: str
    original_value: str
    corrected_value: str
    confirmation_count: int
    status: str


class PurchaseOrderExtractionResult(PurchaseOrderExtraction):
    document_id: str | None = None
    extraction_quality: ExtractionQuality | None = None
    suggested_corrections: list[SuggestedCorrection] = Field(default_factory=list)


class EmailPurchaseOrderExtraction(BaseModel):
    message_id: str | None = None
    sender: str
    subject: str
    body: str
    attachment_name: str
    purchase_order: PurchaseOrderExtractionResult
