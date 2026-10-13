import asyncio
from unittest.mock import patch

from backend.app.services.polling import get_poll_interval, poll_inbox_once


def test_polling_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("INBOX_POLL_INTERVAL_SECONDS", raising=False)

    assert get_poll_interval() == 0


def test_polling_interval_comes_from_environment(monkeypatch):
    monkeypatch.setenv("INBOX_POLL_INTERVAL_SECONDS", "60")

    assert get_poll_interval() == 60


def test_polling_cycle_imports_one_email():
    with patch(
        "backend.app.services.polling.import_next_email"
    ) as import_email:
        asyncio.run(poll_inbox_once())

    import_email.assert_called_once_with()
