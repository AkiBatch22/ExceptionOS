import hmac
import os

from fastapi import Request
from fastapi.responses import JSONResponse


PUBLIC_PATHS = {"/health", "/ready"}


async def require_api_key(request: Request, call_next):
    configured_secret = os.getenv("API_SHARED_SECRET")

    if configured_secret and request.url.path not in PUBLIC_PATHS:
        supplied_secret = request.headers.get("X-ExceptionOS-Key")
        if supplied_secret is None or not hmac.compare_digest(
            supplied_secret,
            configured_secret,
        ):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)
