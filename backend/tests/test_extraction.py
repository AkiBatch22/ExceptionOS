from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.extraction import PurchaseOrderExtraction
from backend.app.schemas.extraction import LLMPurchaseOrderExtraction
from backend.app.services.extraction import _normalize_missing_fields

client = TestClient(app)


def test_model_schema_avoids_provider_unsupported_decimal_patterns():
    schema = LLMPurchaseOrderExtraction.model_json_schema()

    assert "pattern" not in str(schema)


def test_missing_fields_are_derived_from_processing_requirements():
    extraction = PurchaseOrderExtraction(
        po_number="PO-1",
        customer="Acme Inc.",
        items=[{"sku": "HD-BLK-M", "quantity": 10, "unit_price": 18}],
        ship_to="Austin office",
        subtotal=180,
        missing_fields=["discount", "tax", "freight"],
    )

    assert _normalize_missing_fields(extraction).missing_fields == []


def test_purchase_order_text_is_extracted():
    extraction = PurchaseOrderExtraction(
        po_number="PO-4832",
        customer="Acme Inc.",
        items=[{"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18}],
        ship_to="Austin office",
        missing_fields=[],
    )

    with patch(
        "backend.app.api.routes.purchase_orders.extract_purchase_order",
        return_value=extraction,
    ):
        response = client.post(
            "/purchase-orders/extract",
            json={"text": "PO Number: PO-4832"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["extraction_quality"]["score"] == 0.8
    assert body["suggested_corrections"] == []
    assert {key: value for key, value in body.items() if key not in {
        "extraction_quality", "suggested_corrections"
    }} == {
        "po_number": "PO-4832",
        "customer": "Acme Inc.",
        "items": [
            {"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18.0},
        ],
        "ship_to": "Austin office",
        "missing_fields": [],
    }


def test_empty_purchase_order_text_is_rejected():
    response = client.post("/purchase-orders/extract", json={"text": ""})

    assert response.status_code == 422


def test_missing_api_key_returns_service_unavailable():
    with patch(
        "backend.app.api.routes.purchase_orders.extract_purchase_order",
        side_effect=RuntimeError("GROQ_API_KEY is not configured"),
    ):
        response = client.post(
            "/purchase-orders/extract",
            json={"text": "PO Number: PO-4832"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "GROQ_API_KEY is not configured"}


def test_purchase_order_pdf_is_extracted():
    extraction = PurchaseOrderExtraction(
        po_number="PO-4832",
        customer="Acme Inc.",
        items=[{"sku": "HD-BLK-M", "quantity": 50, "unit_price": 18}],
        ship_to="Austin office",
        missing_fields=[],
    )

    with (
        patch(
            "backend.app.api.routes.purchase_orders.extract_pdf_text",
            return_value="PO Number: PO-4832",
        ) as pdf_extractor,
        patch(
            "backend.app.api.routes.purchase_orders.extract_purchase_order",
            return_value=extraction,
        ) as po_extractor,
    ):
        response = client.post(
            "/purchase-orders/extract-pdf",
            files={"file": ("order.pdf", b"pdf bytes", "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json()["po_number"] == "PO-4832"
    pdf_extractor.assert_called_once_with(b"pdf bytes")
    po_extractor.assert_called_once_with("PO Number: PO-4832")


def test_non_pdf_upload_is_rejected():
    response = client.post(
        "/purchase-orders/extract-pdf",
        files={"file": ("order.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json() == {"detail": "Upload a PDF file"}


def test_pdf_that_ocr_cannot_read_is_rejected():
    with patch(
        "backend.app.api.routes.purchase_orders.extract_pdf_text",
        side_effect=ValueError("OCR could not find text in the PDF"),
    ):
        response = client.post(
            "/purchase-orders/extract-pdf",
            files={"file": ("scan.pdf", b"pdf bytes", "application/pdf")},
        )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "OCR could not find text in the PDF"
    }


@pytest.mark.parametrize(
    ("endpoint", "filename", "content_type"),
    [
        ("/purchase-orders/extract-pdf", "large.pdf", "application/pdf"),
        ("/purchase-orders/extract-email", "large.eml", "message/rfc822"),
    ],
)
def test_large_upload_is_rejected(endpoint, filename, content_type):
    response = client.post(
        endpoint,
        files={
            "file": (
                filename,
                b"x" * (10 * 1024 * 1024 + 1),
                content_type,
            )
        },
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Upload must be 10 MB or smaller"}
