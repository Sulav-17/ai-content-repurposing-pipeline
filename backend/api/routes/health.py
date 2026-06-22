from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from backend.services.readiness_service import is_ready, readiness_checks


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-content-repurposing-pipeline",
    }


@router.get("/health/live")
def health_live() -> dict[str, str]:
    return {
        "status": "alive",
        "service": "ai-content-repurposing-pipeline",
    }


@router.get("/health/ready")
def health_ready(request: Request) -> JSONResponse:
    runtime_settings = getattr(request.app.state, "runtime_settings", None)
    checks = readiness_checks(runtime_settings)
    response_status = "ready" if is_ready(checks) else "not_ready"
    status_code = status.HTTP_200_OK if response_status == "ready" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": response_status,
            "checks": checks,
        },
    )
