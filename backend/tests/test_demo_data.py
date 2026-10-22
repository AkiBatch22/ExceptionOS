from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app.core.database import get_connection
from backend.app.main import app
from backend.app.services.demo_data import (
    delete_expired_demo_data,
    get_retention_hours,
)


client = TestClient(app)


def insert_order(erp_order_id: str, po_number: str, created_at: datetime):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO erp_orders (
                erp_order_id, po_number, purchase_order, created_at
            ) VALUES (%s, %s, '{}'::jsonb, %s)
            """,
            (erp_order_id, po_number, created_at),
        )


def test_demo_cleanup_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    insert_order(
        "ERP-OLD",
        "PO-OLD",
        datetime.now(timezone.utc) - timedelta(days=10),
    )

    assert delete_expired_demo_data(retention_hours=1) == 0

    with get_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM erp_orders"
        ).fetchone()[0] == 1


def test_demo_cleanup_deletes_only_expired_records(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    now = datetime.now(timezone.utc)
    insert_order("ERP-OLD", "PO-OLD", now - timedelta(hours=3))
    insert_order("ERP-NEW", "PO-NEW", now)

    assert delete_expired_demo_data(retention_hours=1) == 1

    with get_connection() as connection:
        remaining = connection.execute(
            "SELECT erp_order_id FROM erp_orders"
        ).fetchall()
    assert remaining == [("ERP-NEW",)]


def test_demo_reset_requires_mode_and_secret(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DEMO_RESET_SECRET", "test-reset-secret")
    insert_order("ERP-RESET", "PO-RESET", datetime.now(timezone.utc))

    denied = client.post(
        "/demo/reset",
        headers={"X-Demo-Reset-Secret": "wrong"},
    )
    assert denied.status_code == 404

    response = client.post(
        "/demo/reset",
        headers={"X-Demo-Reset-Secret": "test-reset-secret"},
    )
    assert response.status_code == 204

    with get_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM erp_orders"
        ).fetchone()[0] == 0


def test_invalid_retention_is_rejected(monkeypatch):
    monkeypatch.setenv("DEMO_RETENTION_HOURS", "0")

    try:
        get_retention_hours()
    except RuntimeError as error:
        assert str(error) == "DEMO_RETENTION_HOURS must be at least 1"
    else:
        raise AssertionError("Expected invalid retention to be rejected")
