import os
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status


_requests: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def get_extraction_limit():
    try:
        limit = int(os.getenv("EXTRACTION_RATE_LIMIT_PER_MINUTE", "0"))
    except ValueError as error:
        raise RuntimeError(
            "EXTRACTION_RATE_LIMIT_PER_MINUTE must be a whole number"
        ) from error

    if limit < 0:
        raise RuntimeError(
            "EXTRACTION_RATE_LIMIT_PER_MINUTE cannot be negative"
        )

    return limit


def enforce_extraction_rate_limit(request: Request):
    limit = get_extraction_limit()
    if limit == 0:
        return

    forwarded = request.headers.get("x-forwarded-for", "")
    client = forwarded.split(",", 1)[0].strip()
    if not client:
        client = request.client.host if request.client else "unknown"

    now = monotonic()
    cutoff = now - 60
    with _lock:
        attempts = _requests[client]
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()

        if len(attempts) >= limit:
            retry_after = max(1, round(60 - (now - attempts[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many extraction requests. Try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )

        attempts.append(now)
