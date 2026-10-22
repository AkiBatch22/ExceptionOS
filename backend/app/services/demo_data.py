import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

from backend.app.core.database import get_connection


logger = logging.getLogger(__name__)


def demo_mode_enabled():
    return os.getenv("DEMO_MODE", "false").casefold() == "true"


def get_retention_hours():
    try:
        hours = int(os.getenv("DEMO_RETENTION_HOURS", "48"))
    except ValueError as error:
        raise RuntimeError("DEMO_RETENTION_HOURS must be a whole number") from error

    if hours < 1:
        raise RuntimeError("DEMO_RETENTION_HOURS must be at least 1")

    return hours


def reset_demo_data():
    if not demo_mode_enabled():
        raise RuntimeError("Demo data reset is disabled")

    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE source_lookups, review_corrections, correction_patterns,
                email_imports, audit_events, reviews, erp_orders, source_documents
            RESTART IDENTITY
            """
        )


def delete_expired_demo_data(retention_hours: int | None = None):
    if not demo_mode_enabled():
        return 0

    hours = retention_hours or get_retention_hours()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    with get_connection() as connection:
        deleted = 0
        statements = [
            (
                """
                DELETE FROM review_corrections
                WHERE review_id IN (
                    SELECT review_id FROM reviews WHERE created_at < %s
                )
                """,
                (cutoff,),
            ),
            ("DELETE FROM reviews WHERE created_at < %s", (cutoff,)),
            ("DELETE FROM audit_events WHERE created_at < %s", (cutoff,)),
            ("DELETE FROM email_imports WHERE imported_at < %s", (cutoff,)),
            (
                """
                DELETE FROM source_lookups
                WHERE document_id IN (
                    SELECT document_id FROM source_documents WHERE created_at < %s
                )
                """,
                (cutoff,),
            ),
            (
                """
                DELETE FROM source_documents AS documents
                WHERE documents.created_at < %s
                  AND NOT EXISTS (
                      SELECT 1 FROM reviews
                      WHERE source_document_id = documents.document_id
                  )
                """,
                (cutoff,),
            ),
            ("DELETE FROM erp_orders WHERE created_at < %s", (cutoff,)),
            (
                "DELETE FROM correction_patterns WHERE last_confirmed_at < %s",
                (cutoff,),
            ),
        ]

        for query, parameters in statements:
            cursor = connection.execute(query, parameters)
            deleted += cursor.rowcount

    return deleted


async def cleanup_demo_data_once():
    try:
        deleted = await asyncio.to_thread(delete_expired_demo_data)
        if deleted:
            logger.info("Deleted %s expired demo records", deleted)
    except Exception:
        logger.exception("Demo data cleanup failed")


async def cleanup_demo_data(interval_seconds: int = 3600):
    while True:
        await cleanup_demo_data_once()
        await asyncio.sleep(interval_seconds)
