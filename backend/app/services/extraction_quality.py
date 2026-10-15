import re

from backend.app.schemas.extraction import (
    ExtractionQuality,
    PurchaseOrderExtraction,
)


def _normalize(value: str):
    return re.sub(r"\s+", " ", value.casefold()).strip()


def assess_extraction_quality(
    extraction: PurchaseOrderExtraction,
    source_text: str,
):
    score = 1.0
    signals = []

    if extraction.missing_fields:
        penalty = min(0.7, len(extraction.missing_fields) * 0.18)
        score -= penalty
        signals.append(
            f"{len(extraction.missing_fields)} required processing field(s) are missing"
        )
    else:
        signals.append("All required processing fields were extracted")

    if not extraction.items:
        score -= 0.3
        signals.append("No line items were extracted")

    normalized_text = _normalize(source_text)
    confirmed = 0
    checked = 0
    for value in (extraction.po_number, extraction.customer, extraction.ship_to):
        if value:
            checked += 1
            if _normalize(value) in normalized_text:
                confirmed += 1

    if checked:
        if confirmed == checked:
            signals.append("Core values also appear in the saved document text")
        else:
            score -= 0.1 * (checked - confirmed)
            signals.append(
                f"{checked - confirmed} core value(s) could not be confirmed by exact text search"
            )

    score = round(max(0.0, min(1.0, score)), 2)
    level = "high" if score >= 0.85 else "medium" if score >= 0.6 else "low"
    return ExtractionQuality(score=score, level=level, signals=signals)
