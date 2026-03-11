import time
import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Injects a unique request ID into every request.

    If the caller sends X-Request-ID (e.g. the LLM service calling prediction),
    we reuse that ID so logs correlate across services. Otherwise we generate one.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request_id_var.set(req_id)

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=req_id)

        logger = structlog.get_logger()
        start = time.perf_counter()

        await logger.ainfo(
            "request_started",
            method=request.method,
            path=str(request.url.path),
        )

        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        await logger.ainfo(
            "request_completed",
            method=request.method,
            path=str(request.url.path),
            status=response.status_code,
            duration_ms=elapsed_ms,
        )

        response.headers["X-Request-ID"] = req_id
        return response
