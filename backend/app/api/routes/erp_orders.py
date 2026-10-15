from fastapi import APIRouter, HTTPException

from backend.app.integrations.erp.orders import get_order_record, list_orders


router = APIRouter(prefix="/erp-orders")


@router.get("")
def read_erp_orders():
    return {"orders": list_orders()}


@router.get("/{erp_order_id}")
def read_erp_order(erp_order_id: str):
    order = get_order_record(erp_order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="ERP order not found")
    return order
