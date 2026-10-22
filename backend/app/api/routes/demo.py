import hmac
import os

from fastapi import APIRouter, Header, HTTPException, status

from backend.app.services.demo_data import demo_mode_enabled, reset_demo_data


router = APIRouter(prefix="/demo")


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset(x_demo_reset_secret: str | None = Header(default=None)):
    configured_secret = os.getenv("DEMO_RESET_SECRET")

    if not demo_mode_enabled() or not configured_secret:
        raise HTTPException(status_code=404, detail="Not found")

    if x_demo_reset_secret is None or not hmac.compare_digest(
        x_demo_reset_secret,
        configured_secret,
    ):
        raise HTTPException(status_code=404, detail="Not found")

    reset_demo_data()
