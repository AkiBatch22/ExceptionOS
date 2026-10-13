from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.schemas.extraction import (
    EmailPurchaseOrderExtraction,
    PurchaseOrderExtraction,
    PurchaseOrderText,
)
from backend.app.schemas.purchase_order import PurchaseOrder
from backend.app.services.assessment import assess_purchase_order
from backend.app.services.audit import get_events
from backend.app.services.customers import check_customer
from backend.app.services.email import parse_purchase_order_email
from backend.app.services.extraction import extract_purchase_order
from backend.app.services.inventory import check_inventory
from backend.app.services.inbox_import import NoImportableEmail, import_next_email
from backend.app.services.pdf import extract_pdf_text
from backend.app.services.pricing import check_prices
from backend.app.services.processing import process_purchase_order

router = APIRouter(prefix="/purchase-orders")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


async def read_upload(file: UploadFile):
    content = await file.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload must be 10 MB or smaller")

    return content


@router.post("/extract", response_model=PurchaseOrderExtraction)
def extract(request: PurchaseOrderText):
    try:
        return extract_purchase_order(request.text)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="AI extraction failed") from error


@router.post("/extract-pdf", response_model=PurchaseOrderExtraction)
async def extract_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Upload a PDF file")

    try:
        text = extract_pdf_text(await read_upload(file))
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        return extract_purchase_order(text)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="AI extraction failed") from error


@router.post("/extract-email", response_model=EmailPurchaseOrderExtraction)
async def extract_email(file: UploadFile = File(...)):
    filename = file.filename or ""

    if file.content_type != "message/rfc822" and not filename.lower().endswith(
        ".eml"
    ):
        raise HTTPException(status_code=415, detail="Upload an EML email file")

    try:
        email = parse_purchase_order_email(await read_upload(file))
        text = extract_pdf_text(email["pdf_bytes"])
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        purchase_order = extract_purchase_order(text)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="AI extraction failed") from error

    return {
        "sender": email["sender"],
        "subject": email["subject"],
        "body": email["body"],
        "attachment_name": email["attachment_name"],
        "purchase_order": purchase_order,
    }


@router.post("/import-email", response_model=EmailPurchaseOrderExtraction)
def import_email():
    try:
        return import_next_email()
    except NoImportableEmail as error:
        raise HTTPException(
            status_code=404,
            detail="No unread email with exactly one PDF attachment was found",
        ) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="AI extraction failed") from error


@router.post("/validate")
def validate_purchase_order(purchase_order: PurchaseOrder):
    return {"valid": True}


@router.post("/check-inventory")
def check_purchase_order_inventory(purchase_order: PurchaseOrder):
    return check_inventory(purchase_order.items)


@router.post("/check-prices")
def check_purchase_order_prices(purchase_order: PurchaseOrder):
    return check_prices(purchase_order.items)


@router.post("/check-customer")
def check_purchase_order_customer(purchase_order: PurchaseOrder):
    return check_customer(purchase_order.customer)


@router.post("/assess")
def assess(purchase_order: PurchaseOrder):
    return assess_purchase_order(purchase_order)


@router.post("/process")
def process(purchase_order: PurchaseOrder):
    return process_purchase_order(purchase_order)


@router.get("/{po_number}/events")
def read_purchase_order_events(po_number: str):
    return {"po_number": po_number, "events": get_events(po_number)}
