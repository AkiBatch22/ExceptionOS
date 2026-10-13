from psycopg.types.json import Jsonb
from psycopg.rows import dict_row

from backend.app.core.database import get_connection
from backend.app.schemas.extraction import PurchaseOrderExtraction


def email_was_imported(message_id: str):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM email_imports WHERE message_id = %s",
            (message_id,),
        ).fetchone()

    return row is not None


def record_email_import(
    message_id: str,
    imap_uid: str,
    sender: str,
    subject: str,
    attachment_name: str,
    purchase_order: PurchaseOrderExtraction,
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO email_imports (
                message_id,
                imap_uid,
                sender,
                subject,
                attachment_name,
                po_number,
                extraction
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (message_id) DO NOTHING
            """,
            (
                message_id,
                imap_uid,
                sender,
                subject,
                attachment_name,
                purchase_order.po_number,
                Jsonb(purchase_order.model_dump(mode="json")),
            ),
        )


def list_email_imports():
    with get_connection() as connection:
        connection.row_factory = dict_row
        return connection.execute(
            """
            SELECT
                message_id,
                sender,
                subject,
                attachment_name,
                po_number,
                extraction->>'customer' AS customer,
                imported_at
            FROM email_imports
            WHERE extraction IS NOT NULL AND status = 'pending'
            ORDER BY imported_at DESC, message_id
            """
        ).fetchall()


def get_email_import(message_id: str):
    with get_connection() as connection:
        connection.row_factory = dict_row
        return connection.execute(
            """
            SELECT
                message_id,
                sender,
                subject,
                attachment_name,
                extraction,
                status,
                imported_at
            FROM email_imports
            WHERE message_id = %s AND extraction IS NOT NULL
            """,
            (message_id,),
        ).fetchone()


def complete_email_import(message_id: str):
    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE email_imports
            SET status = 'completed', completed_at = NOW()
            WHERE message_id = %s AND status = 'pending'
            RETURNING message_id
            """,
            (message_id,),
        ).fetchone()

    return row is not None
