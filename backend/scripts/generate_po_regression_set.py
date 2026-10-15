import json
from pathlib import Path

import pymupdf


OUTPUT_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "tests" / "regression_cases"
)


CASES = [
    {
        "id": "01_clean_digital",
        "title": "Clean digital purchase order",
        "depicts": "A clear one-page PDF with a complete header, one line item, totals, and delivery details.",
        "expected": {
            "po_number": "PO-REG-001",
            "customer": "Acme Inc.",
            "currency": "USD",
            "items": [{"sku": "HD-BLK-M", "quantity": 20, "unit_price": 18, "line_total": 360}],
            "subtotal": 360,
            "total": 360,
        },
    },
    {
        "id": "02_low_quality_scan",
        "title": "Low-resolution scanned PO",
        "depicts": "A rasterized, low-resolution page that contains no selectable PDF text and must use OCR.",
        "scan": True,
        "expected": {
            "po_number": "PO-REG-002",
            "customer": "Acme Inc.",
            "items": [{"sku": "HD-BLK-M", "quantity": 12, "unit_price": 18}],
        },
    },
    {
        "id": "03_rotated_scan",
        "title": "Rotated scanned PO",
        "depicts": "A scanned purchase order rotated by 90 degrees, testing orientation handling before OCR.",
        "scan": True,
        "rotation": 90,
        "expected": {
            "po_number": "PO-REG-003",
            "customer": "Acme Inc.",
            "items": [{"sku": "HD-BLK-M", "quantity": 8, "unit_price": 18}],
        },
    },
    {
        "id": "04_multi_page_table",
        "title": "Line-item table continued across pages",
        "depicts": "A two-page PO where the item table continues on page two and totals appear only at the end.",
        "pages": 2,
        "expected": {
            "po_number": "PO-REG-004",
            "customer": "Acme Inc.",
            "items": [
                {"sku": "HD-BLK-M", "quantity": 10, "unit_price": 18},
                {"sku": "HD-BLK-XL", "quantity": 5, "unit_price": 20},
            ],
            "subtotal": 280,
            "total": 280,
        },
    },
    {
        "id": "05_repeated_table_headers",
        "title": "Repeated headers on every page",
        "depicts": "A multi-page table whose column headings repeat, testing that headings are not extracted as products.",
        "pages": 2,
        "repeat_headers": True,
        "expected": {
            "po_number": "PO-REG-005",
            "items": [
                {"sku": "HD-BLK-M", "quantity": 6, "unit_price": 18},
                {"sku": "HD-BLK-XL", "quantity": 3, "unit_price": 20},
            ],
        },
    },
    {
        "id": "06_wrapped_item_description",
        "title": "Wrapped and split line-item description",
        "depicts": "A long product description and decoration note wrapped across several lines between the SKU and numeric columns.",
        "expected": {
            "po_number": "PO-REG-006",
            "items": [{
                "sku": "HD-BLK-M",
                "description": "Premium heavyweight black hoodie with recycled lining",
                "quantity": 15,
                "unit_price": 18,
                "decoration_requirements": ["White Acme logo embroidered on left chest"],
            }],
        },
    },
    {
        "id": "07_handwritten_style_note",
        "title": "Handwritten-style rush instruction",
        "depicts": "A normal PO with an angled handwritten-style note requesting expedited delivery.",
        "handwritten_note": True,
        "expected": {
            "po_number": "PO-REG-007",
            "requested_delivery_date": "2026-11-02",
            "items": [{"sku": "HD-BLK-M", "quantity": 10, "unit_price": 18}],
        },
    },
    {
        "id": "08_stamp_over_text",
        "title": "Approval stamp overlapping text",
        "depicts": "A large red approval stamp partially covering the line-item area, testing noisy visual overlays.",
        "stamp": True,
        "expected": {
            "po_number": "PO-REG-008",
            "items": [{"sku": "HD-BLK-M", "quantity": 25, "unit_price": 18}],
        },
    },
    {
        "id": "09_missing_po_number",
        "title": "Missing required PO number",
        "depicts": "An otherwise complete order with no PO number, testing explicit missing-field detection and safe review routing.",
        "omit_po_number": True,
        "expected": {
            "po_number": None,
            "missing_fields": ["po_number"],
            "customer": "Acme Inc.",
        },
    },
    {
        "id": "10_conflicting_totals",
        "title": "Mathematically inconsistent totals",
        "depicts": "Ten units at $18 but a $200 line total and grand total, testing deterministic reconciliation.",
        "expected": {
            "po_number": "PO-REG-010",
            "items": [{"sku": "HD-BLK-M", "quantity": 10, "unit_price": 18, "line_total": 200}],
            "subtotal": 200,
            "total": 200,
        },
        "expected_issues": ["line_total_mismatch", "subtotal_mismatch"],
    },
    {
        "id": "11_multiple_currencies",
        "title": "Conflicting currencies",
        "depicts": "The header says USD while the line item and total use EUR, testing ambiguity rather than silent guessing.",
        "multiple_currencies": True,
        "expected": {
            "po_number": "PO-REG-011",
            "currency": None,
            "items": [{"sku": "HD-BLK-M", "quantity": 10, "unit_price": 18}],
        },
    },
    {
        "id": "12_european_number_format",
        "title": "European decimal and thousands separators",
        "depicts": "Prices use comma decimals and period thousands separators, testing locale-aware normalization.",
        "european": True,
        "expected": {
            "po_number": "PO-REG-012",
            "currency": "EUR",
            "items": [{"sku": "HD-BLK-M", "quantity": 100, "unit_price": 18.5, "line_total": 1850}],
            "total": 1850,
        },
    },
    {
        "id": "13_multiple_ship_to_addresses",
        "title": "Split shipment to two addresses",
        "depicts": "One PO requests separate quantities for Austin and Dallas, exposing the current single-address model limitation.",
        "multiple_addresses": True,
        "expected": {
            "po_number": "PO-REG-013",
            "ship_to": None,
            "missing_fields": ["ship_to"],
            "items": [{"sku": "HD-BLK-M", "quantity": 20, "unit_price": 18}],
        },
    },
    {
        "id": "14_decoration_in_footnote",
        "title": "Decoration requirements hidden in footnotes",
        "depicts": "Logo method, position, colour, and artwork reference appear in small-print footnotes rather than the item row.",
        "decoration_footnote": True,
        "expected": {
            "po_number": "PO-REG-014",
            "items": [{
                "sku": "HD-BLK-M",
                "quantity": 30,
                "unit_price": 18,
                "decoration_requirements": [
                    "Embroider Acme logo on left chest in white thread",
                    "Artwork reference ACME-LOGO-V3",
                ],
            }],
        },
    },
    {
        "id": "15_mixed_document_bundle",
        "title": "PO bundled with artwork and terms",
        "depicts": "A three-page file containing the PO, an artwork page, and legal terms, testing page classification and irrelevant-content resistance.",
        "bundle": True,
        "pages": 3,
        "expected": {
            "po_number": "PO-REG-015",
            "customer": "Acme Inc.",
            "items": [{"sku": "HD-BLK-M", "quantity": 40, "unit_price": 18}],
        },
    },
]


def _base_lines(case):
    number = int(case["id"].split("_")[0])
    po_number = f"PO-REG-{number:03d}"
    lines = ["PURCHASE ORDER"]
    if not case.get("omit_po_number"):
        lines.append(f"PO Number: {po_number}")
    lines.extend(
        [
            "Customer: Acme Inc.",
            "PO Date: 2026-10-16",
            "Requested Delivery: 2026-11-15",
            "Currency: USD",
            "Ship To: Austin Office, 500 Market Street, Austin, TX 78702",
            "",
            "SKU | Description | Quantity | Unit Price | Line Total",
        ]
    )
    return lines


def _case_pages(case):
    lines = _base_lines(case)
    case_id = case["id"]

    if case_id == "01_clean_digital":
        lines += ["HD-BLK-M | Black hoodie | 20 | USD 18.00 | USD 360.00", "Subtotal: USD 360.00", "Total: USD 360.00"]
    elif case_id == "02_low_quality_scan":
        lines += ["HD-BLK-M | Black hoodie | 12 | USD 18.00 | USD 216.00", "Total: USD 216.00"]
    elif case_id == "03_rotated_scan":
        lines += ["HD-BLK-M | Black hoodie | 8 | USD 18.00 | USD 144.00", "Total: USD 144.00"]
    elif case_id in {"04_multi_page_table", "05_repeated_table_headers"}:
        first = lines + ["HD-BLK-M | Black hoodie | 10 | USD 18.00 | USD 180.00", "Continued on next page"]
        second = []
        if case.get("repeat_headers"):
            first[-2] = "HD-BLK-M | Black hoodie | 6 | USD 18.00 | USD 108.00"
            second.append("SKU | Description | Quantity | Unit Price | Line Total")
            second.append("HD-BLK-XL | Black XL hoodie | 3 | USD 20.00 | USD 60.00")
        else:
            second.append("HD-BLK-XL | Black XL hoodie | 5 | USD 20.00 | USD 100.00")
            second += ["Subtotal: USD 280.00", "Total: USD 280.00"]
        return [first, second]
    elif case_id == "06_wrapped_item_description":
        lines += [
            "HD-BLK-M | Premium heavyweight black hoodie",
            "with recycled lining | 15 | USD 18.00 | USD 270.00",
            "Decoration: White Acme logo embroidered on left chest",
        ]
    elif case_id == "07_handwritten_style_note":
        lines += ["HD-BLK-M | Black hoodie | 10 | USD 18.00 | USD 180.00"]
    elif case_id == "08_stamp_over_text":
        lines += ["HD-BLK-M | Black hoodie | 25 | USD 18.00 | USD 450.00"]
    elif case_id == "09_missing_po_number":
        lines += ["HD-BLK-M | Black hoodie | 10 | USD 18.00 | USD 180.00"]
    elif case_id == "10_conflicting_totals":
        lines += ["HD-BLK-M | Black hoodie | 10 | USD 18.00 | USD 200.00", "Subtotal: USD 200.00", "Total: USD 200.00"]
    elif case_id == "11_multiple_currencies":
        lines += ["Pricing currency below: EUR", "HD-BLK-M | Black hoodie | 10 | EUR 18.00 | EUR 180.00", "Total: EUR 180.00"]
    elif case_id == "12_european_number_format":
        lines[5] = "Currency: EUR"
        lines += ["HD-BLK-M | Black hoodie | 100 | EUR 18,50 | EUR 1.850,00", "Total: EUR 1.850,00"]
    elif case_id == "13_multiple_ship_to_addresses":
        lines[6] = "Split shipment: 10 units to Austin Office; 10 units to Dallas Office"
        lines += ["HD-BLK-M | Black hoodie | 20 | USD 18.00 | USD 360.00"]
    elif case_id == "14_decoration_in_footnote":
        lines += [
            "HD-BLK-M | Black hoodie* | 30 | USD 18.00 | USD 540.00",
            "",
            "* Decoration footnote: Embroider Acme logo on left chest in white thread.",
            "  Artwork reference ACME-LOGO-V3.",
        ]
    elif case_id == "15_mixed_document_bundle":
        first = lines + ["HD-BLK-M | Black hoodie | 40 | USD 18.00 | USD 720.00", "Total: USD 720.00"]
        return [
            first,
            ["ARTWORK PROOF", "ACME-LOGO-V3", "Visual reference only. Not an additional order."],
            ["STANDARD TERMS AND CONDITIONS", "Payment due within 30 days.", "Returns require authorization."],
        ]
    return [lines]


def _insert_lines(page, lines, fontsize=11):
    y = 60
    for line in lines:
        page.insert_text((54, y), line, fontsize=fontsize, fontname="helv")
        y += 22


def _make_pdf(case, path):
    document = pymupdf.open()
    for lines in _case_pages(case):
        page = document.new_page(width=612, height=792)
        _insert_lines(page, lines)

        if case.get("handwritten_note"):
            page.insert_text(
                (310, 620),
                "RUSH: deliver by 2026-11-02",
                fontsize=15,
                fontname="heit",
                color=(0.1, 0.2, 0.8),
            )
        if case.get("stamp"):
            rectangle = pymupdf.Rect(210, 235, 430, 315)
            page.draw_rect(rectangle, color=(0.9, 0.1, 0.1), width=4)
            page.insert_text((250, 285), "APPROVED", fontsize=28, color=(0.9, 0.1, 0.1))

    if case.get("scan"):
        scanned = pymupdf.open()
        for source_page in document:
            pixmap = source_page.get_pixmap(matrix=pymupdf.Matrix(0.8, 0.8), colorspace=pymupdf.csGRAY)
            page = scanned.new_page(width=612, height=792)
            page.insert_image(page.rect, stream=pixmap.tobytes("jpeg"))
            if case.get("rotation"):
                page.set_rotation(case["rotation"])
        document.close()
        document = scanned

    document.save(path)
    document.close()


def main():
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    manifest = []
    for case in CASES:
        filename = f"{case['id']}.pdf"
        _make_pdf(case, OUTPUT_DIRECTORY / filename)
        manifest.append(
            {
                key: value
                for key, value in {**case, "file": filename}.items()
                if key not in {"scan", "rotation", "pages", "repeat_headers", "handwritten_note", "stamp", "omit_po_number", "multiple_currencies", "european", "multiple_addresses", "decoration_footnote", "bundle"}
            }
        )

    (OUTPUT_DIRECTORY / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(CASES)} regression PDFs in {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    main()
