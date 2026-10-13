from backend.app.services.email import parse_purchase_order_email
from backend.app.services.email_imports import (
    email_was_imported,
    record_email_import,
)
from backend.app.services.extraction import extract_purchase_order
from backend.app.services.inbox import fetch_unread_emails, mark_email_processed
from backend.app.services.pdf import extract_pdf_text


class NoImportableEmail(Exception):
    pass


def import_next_email():
    selected_email = None
    parsed_email = None

    for unread_email in fetch_unread_emails():
        try:
            candidate = parse_purchase_order_email(unread_email["content"])

            if email_was_imported(candidate["message_id"]):
                try:
                    mark_email_processed(unread_email["uid"])
                except RuntimeError:
                    pass
                continue

            parsed_email = candidate
            selected_email = unread_email
            break
        except ValueError:
            continue

    if selected_email is None or parsed_email is None:
        raise NoImportableEmail

    text = extract_pdf_text(parsed_email["pdf_bytes"])
    purchase_order = extract_purchase_order(text)
    record_email_import(
        message_id=parsed_email["message_id"],
        imap_uid=selected_email["uid"],
        sender=parsed_email["sender"],
        subject=parsed_email["subject"],
        attachment_name=parsed_email["attachment_name"],
        purchase_order=purchase_order,
    )
    mark_email_processed(selected_email["uid"])

    return {
        "message_id": parsed_email["message_id"],
        "sender": parsed_email["sender"],
        "subject": parsed_email["subject"],
        "body": parsed_email["body"],
        "attachment_name": parsed_email["attachment_name"],
        "purchase_order": purchase_order,
    }
