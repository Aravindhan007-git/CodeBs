from fastapi import APIRouter, Depends
from pydantic import BaseModel

from codebs.config import Settings, get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app_version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_version=settings.app_version,
        environment=settings.environment,
    )