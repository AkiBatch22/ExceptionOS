import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.core.rate_limit import (
    _requests,
    enforce_extraction_rate_limit,
    get_extraction_limit,
)


def make_request(client: str):
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/purchase-orders/extract",
            "headers": [(b"x-forwarded-for", client.encode())],
            "client": ("127.0.0.1", 1000),
        }
    )


def test_rate_limit_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("EXTRACTION_RATE_LIMIT_PER_MINUTE", raising=False)
    assert get_extraction_limit() == 0


def test_rate_limit_rejects_requests_over_limit(monkeypatch):
    monkeypatch.setenv("EXTRACTION_RATE_LIMIT_PER_MINUTE", "1")
    _requests.clear()
    request = make_request("198.51.100.10")

    enforce_extraction_rate_limit(request)

    with pytest.raises(HTTPException) as error:
        enforce_extraction_rate_limit(request)

    assert error.value.status_code == 429


def test_invalid_rate_limit_is_rejected(monkeypatch):
    monkeypatch.setenv("EXTRACTION_RATE_LIMIT_PER_MINUTE", "many")

    with pytest.raises(RuntimeError, match="must be a whole number"):
        get_extraction_limit()
