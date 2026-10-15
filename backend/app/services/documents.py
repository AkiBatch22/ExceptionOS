import hashlib
import re

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from backend.app.core.database import get_connection


def store_document(
    filename: str,
    content_type: str,
    content: bytes,
    page_texts: list[str],
):
    document_id = f"DOC-{hashlib.sha256(content).hexdigest()[:24]}"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO source_documents (
                document_id, filename, content_type, content, page_texts
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (document_id) DO UPDATE
            SET filename = EXCLUDED.filename,
                content_type = EXCLUDED.content_type,
                page_texts = EXCLUDED.page_texts
            """,
            (
                document_id,
                filename,
                content_type,
                content,
                Jsonb(page_texts),
            ),
        )

    return document_id


def get_document(document_id: str):
    with get_connection() as connection:
        connection.row_factory = dict_row
        return connection.execute(
            """
            SELECT document_id, filename, content_type, content, page_texts
            FROM source_documents
            WHERE document_id = %s
            """,
            (document_id,),
        ).fetchone()


def _normalized(value: str):
    return re.sub(r"[^a-z0-9.]+", " ", value.casefold()).strip()


def _snippet(text: str, start: int, length: int):
    left = max(0, start - 100)
    right = min(len(text), start + length + 140)
    return " ".join(text[left:right].split())


def _find_in_pages(page_texts: list[str], value: str, context: str):
    normalized_value = _normalized(value)
    context_tokens = {
        token for token in _normalized(context).split() if len(token) > 2
    }

    if not normalized_value:
        return {"found": False, "reason": "No value was supplied"}

    best_match = None
    for page_number, page_text in enumerate(page_texts, start=1):
        normalized_page = _normalized(page_text)
        normalized_index = normalized_page.find(normalized_value)
        if normalized_index < 0:
            continue

        raw_tokens = normalized_value.split()
        first_token = raw_tokens[0] if raw_tokens else value
        raw_match = re.search(re.escape(first_token), page_text, re.IGNORECASE)
        raw_start = raw_match.start() if raw_match else 0
        snippet = _snippet(page_text, raw_start, max(len(value), 1))
        snippet_tokens = set(_normalized(snippet).split())
        score = 1 + len(context_tokens & snippet_tokens)
        candidate = {
            "found": True,
            "page": page_number,
            "snippet": snippet,
            "method": "deterministic_text_search",
            "score": score,
        }
        if best_match is None or score > best_match["score"]:
            best_match = candidate

    if best_match is None:
        return {
            "found": False,
            "reason": "The value was not found in the saved document text",
        }

    best_match.pop("score")
    return best_match


def locate_source(
    document_id: str,
    field_path: str,
    field_value: str,
    context: str = "",
):
    with get_connection() as connection:
        cached = connection.execute(
            """
            SELECT result
            FROM source_lookups
            WHERE document_id = %s
              AND field_path = %s
              AND field_value = %s
              AND context = %s
            """,
            (document_id, field_path, field_value, context),
        ).fetchone()

    if cached is not None:
        return {**cached[0], "cached": True}

    document = get_document(document_id)
    if document is None:
        return None

    result = _find_in_pages(document["page_texts"], field_value, context)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO source_lookups (
                document_id, field_path, field_value, context, result
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (document_id, field_path, field_value, context)
            DO UPDATE SET result = EXCLUDED.result
            """,
            (document_id, field_path, field_value, context, Jsonb(result)),
        )

    return {**result, "cached": False}
