from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from app.core.response_builders import build_error


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        settings = get_settings()
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > settings.request_max_body_bytes:
                    request_id = getattr(request.state, "request_id", "unknown")
                    return JSONResponse(
                        status_code=413,
                        content=build_error(
                            code="REQUEST_TOO_LARGE",
                            message="Request body exceeds configured size limit.",
                            request_id=request_id,
                        ),
                    )
            except ValueError:
                pass
        return await call_next(request)
