from collections.abc import Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse


def create_health_router(
    service_name: str,
    readiness_checks: list[Callable[[], bool]] | None = None,
) -> APIRouter:
    """Create health and readiness endpoints for a service.

    /health - always returns 200 if the process is running (liveness)
    /ready - returns 200 only if all readiness checks pass (readiness)

    Readiness checks are callables that return True when the service
    is ready to handle traffic (e.g. model loaded, index available).
    """
    router = APIRouter(tags=["health"])
    checks = readiness_checks or []

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": service_name}

    @router.get("/ready")
    async def ready() -> JSONResponse:
        failed = []
        for check in checks:
            try:
                if not check():
                    failed.append(check.__name__)
            except Exception:
                failed.append(check.__name__)

        if failed:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "failed_checks": failed},
            )
        return JSONResponse(content={"status": "ready", "service": service_name})

    return router
