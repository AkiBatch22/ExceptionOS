import asyncio
import logging
import os

from backend.app.services.inbox_import import (
    NoImportableEmail,
    import_next_email,
)


logger = logging.getLogger(__name__)


def get_poll_interval():
    try:
        interval = int(os.getenv("INBOX_POLL_INTERVAL_SECONDS", "0"))
    except ValueError as error:
        raise RuntimeError(
            "INBOX_POLL_INTERVAL_SECONDS must be a whole number"
        ) from error

    if interval < 0:
        raise RuntimeError(
            "INBOX_POLL_INTERVAL_SECONDS cannot be negative"
        )

    return interval


async def poll_inbox_once():
    try:
        await asyncio.to_thread(import_next_email)
    except NoImportableEmail:
        pass
    except Exception:
        logger.exception("Automatic inbox import failed")


async def poll_inbox(interval: int):
    while True:
        await poll_inbox_once()
        await asyncio.sleep(interval)
