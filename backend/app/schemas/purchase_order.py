from decimal import Decimal

from pydantic import BaseModel, Field


class PurchaseOrderItem(BaseModel):
    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class PurchaseOrder(BaseModel):
    po_number: str = Field(min_length=1)
    customer: str = Field(min_length=1)
    items: list[PurchaseOrderItem] = Field(min_length=1)
    ship_to: str = Field(min_length=1)
