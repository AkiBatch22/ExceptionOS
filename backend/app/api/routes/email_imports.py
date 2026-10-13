from fastapi import APIRouter, HTTPException

from backend.app.schemas.purchase_order import PurchaseOrder
from backend.app.services.email_imports import (
    complete_email_import,
    get_email_import,
    list_email_imports,
)
from backend.app.services.processing import process_purchase_order


router = APIRouter(prefix="/email-imports")


@router.get("")
def read_email_imports():
    return {"imports": list_email_imports()}


@router.get("/detail")
def read_email_import(message_id: str):
    email_import = get_email_import(message_id)

    if email_import is None:
        raise HTTPException(status_code=404, detail="Email import not found")

    return email_import


@router.post("/process")
def process_email_import(message_id: str, purchase_order: PurchaseOrder):
    email_import = get_email_import(message_id)

    if email_import is None:
        raise HTTPException(status_code=404, detail="Email import not found")

    if email_import["status"] != "pending":
        raise HTTPException(status_code=409, detail="Email import already completed")

    result = process_purchase_order(purchase_order)

    if not complete_email_import(message_id):
        raise HTTPException(status_code=409, detail="Email import already completed")

    return result
