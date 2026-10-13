from backend.app.core.database import get_connection
from backend.app.services.pdf import find_tessdata


REQUIRED_TABLES = [
    "erp_orders",
    "reviews",
    "audit_events",
    "email_imports",
]


def check_readiness():
    checks = {"database": "ok", "ocr": "ok"}

    try:
        with get_connection() as connection:
            for table in REQUIRED_TABLES:
                exists = connection.execute(
                    "SELECT to_regclass(%s)",
                    (table,),
                ).fetchone()[0]

                if exists is None:
                    checks["database"] = "unavailable"
                    break
    except Exception:
        checks["database"] = "unavailable"

    try:
        find_tessdata()
    except RuntimeError:
        checks["ocr"] = "unavailable"

    return checks
