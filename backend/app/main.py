"""FastAPI application entry point for Phase 1."""

import logging
import re
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.backtest import router as backtest_router
from app.api.config import router as config_router
from app.api.market import router as market_router
from app.api.metrics import router as metrics_router
from app.api.signals import router as signals_router
from app.api.terminal import router as terminal_router
from app.config import get_settings
from app.database import initialize_database
from app.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("smart_signals_fx.http")
_requests_by_client: dict[str, deque[float]] = defaultdict(deque)
_rate_window_seconds = 60.0
_rate_limit_per_minute = 120


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    try:
        yield
    finally:
        from app.services.mt5_service import mt5_service
        mt5_service.close()

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
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    supplied_id = request.headers.get("x-request-id", "")
    request_id = supplied_id if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", supplied_id) else str(uuid.uuid4())
    started = time.perf_counter()
    try:
        if request.url.path != "/health":
            client_key = request.client.host if request.client else "unknown"
            current_time = time.monotonic()
            requests = _requests_by_client[client_key]
            while requests and current_time - requests[0] >= _rate_window_seconds:
                requests.popleft()
            if len(requests) >= _rate_limit_per_minute:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": {"code": "rate_limit_exceeded", "message": "Request limit exceeded"}},
                    headers={"Retry-After": str(int(_rate_window_seconds))},
                )
                response.headers["X-Request-ID"] = request_id
                return response
            requests.append(current_time)
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
app.include_router(backtest_router)
app.include_router(config_router)
app.include_router(market_router)
app.include_router(metrics_router)
app.include_router(signals_router)
app.include_router(terminal_router)
