from app.repositories.health import HealthRepository
from app.schemas.health import ComponentStatus, ReadinessComponents, ReadinessResponse


def _component_status(is_available: bool) -> ComponentStatus:
    return "ok" if is_available else "unavailable"


class HealthService:
    def __init__(self, repository: HealthRepository) -> None:
        self._repository = repository

    def readiness(self) -> ReadinessResponse:
        """Only PostgreSQL decides readiness; the others are reported (TRD sections 6 and 10)."""
        postgres_available = self._repository.postgres_is_available()
        return ReadinessResponse(
            status="ready" if postgres_available else "not_ready",
            components=ReadinessComponents(
                postgres=_component_status(postgres_available),
                elasticsearch=_component_status(self._repository.elasticsearch_is_available()),
                llm=_component_status(self._repository.llm_is_available()),
            ),
        )
