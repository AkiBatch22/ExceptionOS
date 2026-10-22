from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_api_key_is_optional_for_local_development(monkeypatch):
    monkeypatch.delenv("API_SHARED_SECRET", raising=False)

    assert client.get("/reviews").status_code == 200


def test_health_checks_remain_public(monkeypatch):
    monkeypatch.setenv("API_SHARED_SECRET", "test-shared-secret")

    assert client.get("/health").status_code == 200


def test_protected_routes_reject_missing_or_invalid_key(monkeypatch):
    monkeypatch.setenv("API_SHARED_SECRET", "test-shared-secret")

    assert client.get("/reviews").status_code == 401
    assert (
        client.get(
            "/reviews",
            headers={"X-ExceptionOS-Key": "wrong-secret"},
        ).status_code
        == 401
    )


def test_protected_routes_accept_configured_key(monkeypatch):
    monkeypatch.setenv("API_SHARED_SECRET", "test-shared-secret")

    response = client.get(
        "/reviews",
        headers={"X-ExceptionOS-Key": "test-shared-secret"},
    )

    assert response.status_code == 200
