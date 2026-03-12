import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.agent_discovery import router as agent_discovery_router
from app.api.health import router as health_router
from app.api.root import router as root_router
from app.api.v1.lead_extract import router as lead_extract_router
from app.api.v1.payment import router as payment_router
from app.api.v1.pricing import router as pricing_router
from app.api.v1.search import router as search_router
from app.api.v1.structured_web import router as structured_web_router
from app.config import get_settings
from app.core.response_builders import build_error
from app.exceptions import AppError, PaymentRequiredError
from app.logging import configure_logging
from app.middleware.access_log import AccessLogMiddleware
from app.middleware.metering import MeteringMiddleware
from app.middleware.payment_stub import PaymentStubMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_size import RequestSizeLimitMiddleware

configure_logging()
logger = logging.getLogger("app")
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
)
app.state.payment_hard_enforcement = settings.enable_payment_enforcement
app.state.payment_shadow_mode = settings.payment_shadow_mode
app.state.payment_verifier = settings.payment_verifier

allowed_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_window=settings.rate_limit_requests, window_seconds=settings.rate_limit_window_seconds)
app.add_middleware(AccessLogMiddleware)
app.add_middleware(MeteringMiddleware)
app.add_middleware(PaymentStubMiddleware)

app.include_router(root_router)
app.include_router(agent_discovery_router)
app.include_router(health_router)
app.include_router(structured_web_router)
app.include_router(lead_extract_router)
app.include_router(search_router)
app.include_router(pricing_router)
app.include_router(payment_router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    request_id = getattr(request.state, "request_id", "unknown")
    meta = None
    payment = None
    details = None
    if isinstance(exc, PaymentRequiredError):
        meta = {"pricing_id": exc.pricing_id, "payment_mode": exc.payment_mode}
        payment = {
            "chain": exc.chain,
            "token": exc.token,
            "receiver_wallet": exc.receiver_wallet,
            "payment_mode": exc.payment_mode,
            "payment_format": exc.payment_format,
        }
        details = {"reason": exc.reason or "payment_required"}
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error(code=exc.code, message=exc.message, request_id=request_id, meta=meta, payment=payment, details=details),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    message = exc.errors()[0].get("msg", "Invalid request payload.") if exc.errors() else "Invalid request payload."
    return JSONResponse(
        status_code=422,
        content=build_error(code="REQUEST_VALIDATION_ERROR", message=message, request_id=request_id),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("unhandled_exception request_id=%s", request_id)
    return JSONResponse(
        status_code=500,
        content=build_error(code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred.", request_id=request_id),
    )
