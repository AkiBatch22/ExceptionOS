import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.app.api.routes.email_imports import router as email_imports_router
from backend.app.api.routes.erp_orders import router as erp_orders_router
from backend.app.api.routes.documents import router as documents_router
from backend.app.api.routes.demo import router as demo_router
from backend.app.api.routes.purchase_orders import router as purchase_orders_router
from backend.app.api.routes.reviews import router as reviews_router
from backend.app.core.readiness import check_readiness
from backend.app.core.api_auth import require_api_key
from backend.app.services.polling import get_poll_interval, poll_inbox
from backend.app.services.demo_data import cleanup_demo_data, demo_mode_enabled


@asynccontextmanager
async def lifespan(app: FastAPI):
    interval = get_poll_interval()
    polling_task = None
    cleanup_task = None

    if interval > 0:
        polling_task = asyncio.create_task(poll_inbox(interval))

    if demo_mode_enabled():
        cleanup_task = asyncio.create_task(cleanup_demo_data())

    yield

    if polling_task:
        polling_task.cancel()
        with suppress(asyncio.CancelledError):
            await polling_task

    if cleanup_task:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(lifespan=lifespan)
app.middleware("http")(require_api_key)

app.include_router(email_imports_router)
app.include_router(erp_orders_router)
app.include_router(documents_router)
app.include_router(demo_router)
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
