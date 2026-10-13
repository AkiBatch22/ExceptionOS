import imaplib
import os

from dotenv import load_dotenv


load_dotenv()


def fetch_unread_emails():
    settings = _get_settings()

    try:
        with imaplib.IMAP4_SSL(
            settings["host"],
            settings["port"],
            timeout=settings["timeout"],
        ) as inbox:
            inbox.login(settings["username"], settings["password"])
            inbox.select(settings["mailbox"])
            status, data = inbox.uid("search", None, "UNSEEN")

            if status != "OK":
                raise RuntimeError("Unable to search the IMAP inbox")

            emails = []

            for uid in data[0].split()[:20]:
                status, message_data = inbox.uid(
                    "fetch", uid, "(BODY.PEEK[])"
                )

                if status != "OK":
                    continue

                content = next(
                    (
                        item[1]
                        for item in message_data
                        if isinstance(item, tuple)
                    ),
                    None,
                )

                if content:
                    emails.append({"uid": uid.decode(), "content": content})

            return emails
    except (imaplib.IMAP4.error, OSError) as error:
        raise RuntimeError("Unable to access the IMAP inbox") from error


def mark_email_processed(uid: str):
    settings = _get_settings()

    try:
        with imaplib.IMAP4_SSL(
            settings["host"],
            settings["port"],
            timeout=settings["timeout"],
        ) as inbox:
            inbox.login(settings["username"], settings["password"])
            inbox.select(settings["mailbox"])
            status, _ = inbox.uid("store", uid, "+FLAGS", "\\Seen")

            if status != "OK":
                raise RuntimeError("Unable to mark the email as processed")
    except (imaplib.IMAP4.error, OSError) as error:
        raise RuntimeError("Unable to access the IMAP inbox") from error


def _get_settings():
    names = ["IMAP_HOST", "IMAP_USERNAME", "IMAP_PASSWORD"]
    missing = [name for name in names if not os.getenv(name)]

    if missing:
        raise RuntimeError(f"{', '.join(missing)} is not configured")

    try:
        port = int(os.getenv("IMAP_PORT", "993"))
        timeout = float(os.getenv("IMAP_TIMEOUT_SECONDS", "30"))
    except ValueError as error:
        raise RuntimeError("IMAP port and timeout must be numbers") from error

    if not 1 <= port <= 65535:
        raise RuntimeError("IMAP_PORT must be between 1 and 65535")

    if timeout <= 0:
        raise RuntimeError("IMAP_TIMEOUT_SECONDS must be greater than zero")

    return {
        "host": os.environ["IMAP_HOST"],
        "port": port,
        "timeout": timeout,
        "username": os.environ["IMAP_USERNAME"],
        "password": os.environ["IMAP_PASSWORD"],
        "mailbox": os.getenv("IMAP_MAILBOX", "INBOX"),
    }
