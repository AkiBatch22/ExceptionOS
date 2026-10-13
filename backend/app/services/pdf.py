import os
import shutil
from io import BytesIO
from pathlib import Path

import pymupdf
from pypdf import PdfReader
from pypdf.errors import PdfReadError


def extract_pdf_text(pdf_bytes: bytes):
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        page_texts = [page.extract_text() or "" for page in reader.pages]
    except (PdfReadError, OSError, ValueError) as error:
        raise ValueError("The uploaded file is not a readable PDF") from error

    if any(not text.strip() for text in page_texts):
        page_texts = _extract_scanned_pages(pdf_bytes, page_texts)

    text = "\n".join(page_texts)

    if not text.strip():
        raise ValueError("OCR could not find text in the PDF")

    return text


def _extract_scanned_pages(pdf_bytes: bytes, page_texts: list[str]):
    tessdata = find_tessdata()

    try:
        document = pymupdf.open(stream=pdf_bytes, filetype="pdf")

        with document:
            for page_number, text in enumerate(page_texts):
                if text.strip():
                    continue

                page = document[page_number]
                text_page = page.get_textpage_ocr(
                    language="eng",
                    dpi=300,
                    full=True,
                    tessdata=str(tessdata),
                )
                page_texts[page_number] = page.get_text(textpage=text_page)
    except Exception as error:
        raise ValueError("OCR could not process the PDF") from error

    return page_texts


def find_tessdata():
    configured_path = os.getenv("TESSDATA_PREFIX")
    executable = shutil.which("tesseract")
    candidates = [
        Path(configured_path) if configured_path else None,
        Path(executable).parent / "tessdata" if executable else None,
        Path(r"C:\Program Files\Tesseract-OCR\tessdata"),
    ]

    for candidate in candidates:
        if candidate and (candidate / "eng.traineddata").is_file():
            return candidate

    raise RuntimeError(
        "Tesseract OCR with English language data is not installed"
    )
