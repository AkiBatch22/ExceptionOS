from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class PurchaseOrderItem(BaseModel):
    sku: str = Field(min_length=1)
    description: str | None = None
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal | None = Field(default=None, ge=0)
    decoration_requirements: list[str] | None = None


class PurchaseOrder(BaseModel):
    po_number: str = Field(min_length=1)
    customer: str = Field(min_length=1)
    po_date: date | None = None
    requested_delivery_date: date | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    items: list[PurchaseOrderItem] = Field(min_length=1)
    ship_to: str = Field(min_length=1)
    subtotal: Decimal | None = Field(default=None, ge=0)
    discount: Decimal | None = Field(default=None, ge=0)
    tax: Decimal | None = Field(default=None, ge=0)
    freight: Decimal | None = Field(default=None, ge=0)
    total: Decimal | None = Field(default=None, ge=0)
