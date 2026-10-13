from psycopg.types.json import Jsonb

from backend.app.core.database import get_connection


def record_event(po_number: str, event: str, details: dict):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_events (po_number, event, details)
            VALUES (%s, %s, %s)
            """,
            (po_number, event, Jsonb(details)),
        )


def get_events(po_number: str):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event, details
            FROM audit_events
            WHERE po_number = %s
            ORDER BY id
            """,
            (po_number,),
        ).fetchall()

    return [{"event": event, "details": details} for event, details in rows]
