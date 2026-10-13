import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.app.api.routes.email_imports import router as email_imports_router
from backend.app.api.routes.purchase_orders import router as purchase_orders_router
from backend.app.api.routes.reviews import router as reviews_router
from backend.app.core.readiness import check_readiness
from backend.app.services.polling import get_poll_interval, poll_inbox


@asynccontextmanager
async def lifespan(app: FastAPI):
    interval = get_poll_interval()
    polling_task = None

    if interval > 0:
        polling_task = asyncio.create_task(poll_inbox(interval))

    yield

    if polling_task:
        polling_task.cancel()
        with suppress(asyncio.CancelledError):
            await polling_task


app = FastAPI(lifespan=lifespan)

app.include_router(email_imports_router)
app.include_router(purchase_orders_router)
app.include_router(reviews_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    checks = check_readiness()
    is_ready = all(status == "ok" for status in checks.values())
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={
            "status": "ready" if is_ready else "not_ready",
            "checks": checks,
        },
    )
