from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderText(BaseModel):
    text: str = Field(min_length=1)


class ExtractedPurchaseOrderItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str | None
    quantity: int | None
    unit_price: float | None


class PurchaseOrderExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    po_number: str | None
    customer: str | None
    items: list[ExtractedPurchaseOrderItem]
    ship_to: str | None
    missing_fields: list[str]


class EmailPurchaseOrderExtraction(BaseModel):
    message_id: str | None = None
    sender: str
    subject: str
    body: str
    attachment_name: str
    purchase_order: PurchaseOrderExtraction
