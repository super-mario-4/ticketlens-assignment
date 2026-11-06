from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.health import HealthRepository
from app.services.health import HealthService


def get_health_repository(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthRepository:
    return HealthRepository(
        session=session,
        elasticsearch_url=settings.elasticsearch_url,
        timeout_seconds=settings.health_check_timeout_seconds,
    )


def get_health_service(
    repository: Annotated[HealthRepository, Depends(get_health_repository)],
) -> HealthService:
    return HealthService(repository)
