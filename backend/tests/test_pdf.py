from io import BytesIO
from unittest.mock import patch

import pytest
from pypdf import PdfWriter

from backend.app.services.pdf import extract_pdf_text


def blank_pdf():
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(output)
    return output.getvalue()


def test_scanned_pdf_uses_ocr_fallback():
    with patch(
        "backend.app.services.pdf._extract_scanned_pages",
        return_value=["PO Number: PO-SCANNED"],
    ) as ocr:
        text = extract_pdf_text(blank_pdf())

    assert text == "PO Number: PO-SCANNED"
    ocr.assert_called_once()


def test_pdf_is_rejected_when_ocr_finds_no_text():
    with patch(
        "backend.app.services.pdf._extract_scanned_pages",
        return_value=[""],
    ):
        with pytest.raises(ValueError, match="OCR could not find text"):
            extract_pdf_text(blank_pdf())


def test_unreadable_pdf_is_rejected_before_ocr():
    with pytest.raises(ValueError, match="not a readable PDF"):
        extract_pdf_text(b"not a pdf")
