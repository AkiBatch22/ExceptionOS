import pytest
import httpx
from groq import APITimeoutError
from unittest.mock import patch

from backend.app.services.extraction import extract_purchase_order
from backend.app.services.inbox import _get_settings
from backend.app.services.polling import get_poll_interval


def configure_imap(monkeypatch):
    monkeypatch.setenv("IMAP_HOST", "imap.example.com")
    monkeypatch.setenv("IMAP_USERNAME", "orders@example.com")
    monkeypatch.setenv("IMAP_PASSWORD", "test-password")


def test_invalid_imap_port_is_rejected(monkeypatch):
    configure_imap(monkeypatch)
    monkeypatch.setenv("IMAP_PORT", "70000")

    with pytest.raises(RuntimeError, match="between 1 and 65535"):
        _get_settings()


def test_invalid_imap_timeout_is_rejected(monkeypatch):
    configure_imap(monkeypatch)
    monkeypatch.setenv("IMAP_TIMEOUT_SECONDS", "0")

    with pytest.raises(RuntimeError, match="greater than zero"):
        _get_settings()


def test_invalid_groq_timeout_is_rejected(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_TIMEOUT_SECONDS", "not-a-number")

    with pytest.raises(RuntimeError, match="must be a number"):
        extract_purchase_order("PO Number: PO-1")


def test_negative_poll_interval_is_rejected(monkeypatch):
    monkeypatch.setenv("INBOX_POLL_INTERVAL_SECONDS", "-1")

    with pytest.raises(RuntimeError, match="cannot be negative"):
        get_poll_interval()


def test_groq_timeout_becomes_safe_unavailable_error(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    with patch("backend.app.services.extraction.Groq") as groq:
        groq.return_value.chat.completions.create.side_effect = APITimeoutError(
            httpx.Request("POST", "https://api.groq.com")
        )

        with pytest.raises(RuntimeError, match="Groq is unavailable"):
            extract_purchase_order("PO Number: PO-1")
