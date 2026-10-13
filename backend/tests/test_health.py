from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_checks_database_and_ocr():
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok", "ocr": "ok"},
    }


def test_readiness_failure_returns_service_unavailable():
    with patch(
        "backend.app.main.check_readiness",
        return_value={"database": "unavailable", "ocr": "ok"},
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "unavailable", "ocr": "ok"},
    }
