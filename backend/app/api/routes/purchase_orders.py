from time import perf_counter

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.schemas.extraction import (
    EmailPurchaseOrderExtraction,
    PurchaseOrderExtraction,
    PurchaseOrderExtractionResult,
    PurchaseOrderText,
)
from backend.app.schemas.purchase_order import PurchaseOrder
from backend.app.services.assessment import assess_purchase_order
from backend.app.services.audit import get_events
from backend.app.services.customers import check_customer
from backend.app.services.correction_memory import find_suggestions
from backend.app.services.documents import store_document
from backend.app.services.email import parse_purchase_order_email
from backend.app.services.extraction import extract_purchase_order
from backend.app.services.extraction_quality import assess_extraction_quality
from backend.app.services.inventory import check_inventory
from backend.app.services.audit import record_event
from backend.app.services.inbox_import import NoImportableEmail, import_next_email
from backend.app.services.pdf import extract_pdf_text, split_pdf_pages
from backend.app.services.pricing import check_prices
from backend.app.services.processing import process_purchase_order

router = APIRouter(prefix="/purchase-orders")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


async def read_upload(file: UploadFile):
    content = await file.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload must be 10 MB or smaller")

    return content


def extraction_result(
    extraction: PurchaseOrderExtraction,
    text: str,
    started_at: float,
    document_id: str | None = None,
):
    duration_ms = round((perf_counter() - started_at) * 1000)
    result = PurchaseOrderExtractionResult(
        **extraction.model_dump(),
        document_id=document_id,
        extraction_quality=assess_extraction_quality(extraction, text),
        suggested_corrections=find_suggestions(extraction),
    )
    if extraction.po_number:
        record_event(
            extraction.po_number,
            "extraction_completed",
            {
                "duration_ms": duration_ms,
                "document_id": document_id,
                "item_count": len(extraction.items),
                "quality_score": result.extraction_quality.score,
            },
        )
    return result


@router.post(
    "/extract",
    response_model=PurchaseOrderExtractionResult,
    response_model_exclude_none=True,
)
def extract(request: PurchaseOrderText):
    started_at = perf_counter()
    try:
        extraction = extract_purchase_order(request.text)
        return extraction_result(
            extraction,
            request.text,
            started_at,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="AI extraction failed") from error


@router.post(
    "/extract-pdf",
    response_model=PurchaseOrderExtractionResult,
    response_model_exclude_none=True,
)
async def extract_pdf(file: UploadFile = File(...)):
    started_at = perf_counter()
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Upload a PDF file")

    content = await read_upload(file)
    try:
        text = extract_pdf_text(content)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        extraction = extract_purchase_order(text)
        document_id = store_document(
            file.filename or "purchase-order.pdf",
            "application/pdf",
            content,
            split_pdf_pages(text),
        )
        return extraction_result(
            extraction,
            text,
            started_at,
            document_id,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="AI extraction failed") from error


@router.post(
    "/extract-email",
    response_model=EmailPurchaseOrderExtraction,
    response_model_exclude_none=True,
)
async def extract_email(file: UploadFile = File(...)):
    started_at = perf_counter()
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
        extraction = extract_purchase_order(text)
        document_id = store_document(
            email["attachment_name"],
            "application/pdf",
            email["pdf_bytes"],
            split_pdf_pages(text),
        )
        purchase_order = extraction_result(
            extraction,
            text,
            started_at,
            document_id,
        )
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
def process(
    purchase_order: PurchaseOrder,
    document_id: str | None = None,
):
    return process_purchase_order(purchase_order, document_id)


@router.get("/{po_number}/events")
def read_purchase_order_events(po_number: str):
    return {"po_number": po_number, "events": get_events(po_number)}
