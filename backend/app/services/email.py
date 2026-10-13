from email import policy
from email.parser import BytesParser
from hashlib import sha256


def parse_purchase_order_email(email_bytes: bytes):
    message = BytesParser(policy=policy.default).parsebytes(email_bytes)
    message_id = str(message.get("Message-ID", "")).strip()

    if not message_id:
        message_id = f"sha256:{sha256(email_bytes).hexdigest()}"

    body_parts = []
    pdf_attachments = []

    for part in message.walk():
        content_type = part.get_content_type()
        filename = part.get_filename()
        disposition = part.get_content_disposition()

        if content_type == "text/plain" and disposition != "attachment":
            body_parts.append(part.get_content())

        if content_type == "application/pdf" or (
            filename and filename.lower().endswith(".pdf")
        ):
            pdf_attachments.append(
                {
                    "filename": filename or "attachment.pdf",
                    "content": part.get_payload(decode=True) or b"",
                }
            )

    if not pdf_attachments:
        raise ValueError("The email has no PDF attachment")

    if len(pdf_attachments) > 1:
        raise ValueError("The email has multiple PDF attachments")

    attachment = pdf_attachments[0]

    if not attachment["content"]:
        raise ValueError("The PDF attachment is empty")

    return {
        "message_id": message_id,
        "sender": str(message.get("From", "")),
        "subject": str(message.get("Subject", "")),
        "body": "\n".join(body_parts).strip(),
        "attachment_name": attachment["filename"],
        "pdf_bytes": attachment["content"],
    }
