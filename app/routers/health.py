"""
Health and readiness endpoints.
Used by load balancers and Kubernetes probes.
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns 200 OK when the application is running.",
)
async def health_check() -> HealthResponse:
    from app.config import get_settings
    settings = get_settings()
    return HealthResponse(status="ok", version=settings.app_version)


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
    description="Returns 200 OK when the application can serve traffic.",
)
async def readiness_check() -> HealthResponse:
    from app.config import get_settings
    settings = get_settings()
    return HealthResponse(status="ready", version=settings.app_version)
