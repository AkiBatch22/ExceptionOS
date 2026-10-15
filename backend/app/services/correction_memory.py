import re

from psycopg.rows import dict_row

from backend.app.core.database import get_connection
from backend.app.schemas.extraction import PurchaseOrderExtraction


REMEMBERABLE_FIELDS = {"customer", "ship_to", "items[*].sku"}


def party_key(value: str):
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def canonical_field_path(field_path: str):
    return re.sub(r"items\[\d+\]", "items[*]", field_path)


def is_rememberable(field_path: str):
    return canonical_field_path(field_path) in REMEMBERABLE_FIELDS


def remember_correction(
    party_label: str,
    field_path: str,
    original_value: str,
    corrected_value: str,
):
    canonical_path = canonical_field_path(field_path)
    if canonical_path not in REMEMBERABLE_FIELDS:
        raise ValueError("This field changes per order and cannot be remembered")

    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO correction_patterns (
                party_key, party_label, field_path, original_value,
                corrected_value
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (
                party_key, field_path, original_value, corrected_value
            )
            DO UPDATE SET
                confirmation_count = correction_patterns.confirmation_count + 1,
                last_confirmed_at = NOW(),
                status = CASE
                    WHEN correction_patterns.confirmation_count + 1 >= 3
                    THEN 'trusted_suggestion'
                    ELSE correction_patterns.status
                END
            RETURNING id
            """,
            (
                party_key(party_label),
                party_label,
                canonical_path,
                original_value,
                corrected_value,
            ),
        ).fetchone()
    return row[0]


def record_pattern_feedback(pattern_id: int, feedback: str):
    with get_connection() as connection:
        if feedback == "accepted":
            row = connection.execute(
                """
                UPDATE correction_patterns
                SET confirmation_count = confirmation_count + 1,
                    last_confirmed_at = NOW(),
                    status = CASE
                        WHEN confirmation_count + 1 >= 3
                        THEN 'trusted_suggestion'
                        ELSE status
                    END
                WHERE id = %s AND status != 'disabled'
                RETURNING id
                """,
                (pattern_id,),
            ).fetchone()
        else:
            row = connection.execute(
                """
                UPDATE correction_patterns
                SET rejection_count = rejection_count + 1,
                    status = CASE
                        WHEN rejection_count + 1 >= 2
                        THEN 'disabled'
                        ELSE status
                    END
                WHERE id = %s AND status != 'disabled'
                RETURNING id
                """,
                (pattern_id,),
            ).fetchone()
    return row is not None


def _extracted_values(extraction: PurchaseOrderExtraction):
    values = {
        "customer": extraction.customer,
        "ship_to": extraction.ship_to,
    }
    for index, item in enumerate(extraction.items):
        values[f"items[{index}].sku"] = item.sku
    return values


def find_suggestions(extraction: PurchaseOrderExtraction):
    if not extraction.customer:
        return []

    values = _extracted_values(extraction)
    with get_connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(
            """
            SELECT id AS pattern_id, party_label, field_path,
                original_value, corrected_value, confirmation_count, status
            FROM correction_patterns
            WHERE party_key = %s AND status != 'disabled'
            ORDER BY confirmation_count DESC, id
            """,
            (party_key(extraction.customer),),
        ).fetchall()

    suggestions = []
    for actual_path, value in values.items():
        if value is None:
            continue
        for row in rows:
            if (
                canonical_field_path(actual_path) == row["field_path"]
                and str(value).casefold() == row["original_value"].casefold()
            ):
                suggestions.append(
                    {
                        **row,
                        "field_path": actual_path,
                    }
                )
                break
    return suggestions
