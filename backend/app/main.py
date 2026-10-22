"""FastAPI application entry point for Phase 1."""

import logging
import re
import time
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.config import get_settings
from app.logging_config import configure_logging
from app.security import require_api_token

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("smart_signals_fx.http")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Read-only market signal service. This API does not place, modify, "
        "or close broker orders."
    ),
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    supplied_id = request.headers.get("x-request-id", "")
    request_id = supplied_id if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", supplied_id) else str(uuid.uuid4())
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error", extra={"request_id": request_id})
        response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "HTTP request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
        # Avoid logging query strings, credentials, or request bodies.
    )
    return response


app.include_router(health_router)


@app.get(
    "/api/v1/terminal",
    tags=["terminal"],
    summary="Read terminal connection status",
    dependencies=[Depends(require_api_token)],
)
async def terminal_status() -> dict[str, str]:
    """Phase 1 placeholder; MT5 connectivity is implemented in Phase 2."""
    return {"status": "not_configured", "message": "MetaTrader 5 connector is not implemented yet"}
