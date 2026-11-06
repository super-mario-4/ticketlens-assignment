from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.classification.classifier import Classifier
from app.classification.llm import LLMClassifier
from app.classification.routing import RoutingTable, load_routing_table
from app.core.config import Settings, get_settings
from app.core.security import read_token
from app.db.session import get_db
from app.models import User
from app.models.enums import UserRole
from app.repositories.health import HealthRepository
from app.repositories.imports import ImportRepository
from app.repositories.search_outbox import SearchOutboxRepository
from app.repositories.tickets import TicketRepository
from app.repositories.users import UserRepository
from app.search.client import SearchClient
from app.services.auth import AuthService
from app.services.health import HealthService
from app.services.imports import ImportService
from app.services.tickets import TicketService

CSV_MEDIA_TYPES = frozenset(
    {"text/csv", "application/csv", "application/vnd.ms-excel", "application/octet-stream"}
)

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CsvUpload:
    filename: str
    content: bytes


def file_too_large(max_bytes: int) -> dict[str, object]:
    return {"code": "file_too_large", "max_bytes": max_bytes}


@lru_cache
def get_classifier() -> Classifier:
    """One shared client, so that readiness checks reuse a connection."""
    return LLMClassifier(get_settings())


@lru_cache
def get_routing() -> RoutingTable:
    return load_routing_table(get_settings().routing_config_path)


@lru_cache
def get_search_client() -> SearchClient:
    return SearchClient(get_settings())


def get_health_repository(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    classifier: Annotated[Classifier, Depends(get_classifier)],
) -> HealthRepository:
    return HealthRepository(
        session=session,
        elasticsearch_url=settings.elasticsearch_url,
        timeout_seconds=settings.health_check_timeout_seconds,
        classifier=classifier,
    )


def get_health_service(
    repository: Annotated[HealthRepository, Depends(get_health_repository)],
) -> HealthService:
    return HealthService(repository)


def get_import_service(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ImportService:
    return ImportService(
        session=session,
        imports=ImportRepository(session),
        tickets=TicketRepository(session),
        settings=settings,
        outbox=SearchOutboxRepository(session),
    )


def get_ticket_service(
    session: Annotated[Session, Depends(get_db)],
    search: Annotated[SearchClient, Depends(get_search_client)],
    routing: Annotated[RoutingTable, Depends(get_routing)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TicketService:
    return TicketService(session, TicketRepository(session), search, routing, settings)


def get_auth_service(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(session, UserRepository(session), settings)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    user_id = read_token(credentials.credentials, settings) if credentials else None
    user = UserRepository(session).get(user_id) if user_id else None
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            {"code": "not_authenticated"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def _require(role: UserRole, user: User) -> User:
    if user.role is not role:
        raise HTTPException(status.HTTP_403_FORBIDDEN, {"code": "forbidden"})
    return user


def require_operator(user: Annotated[User, Depends(get_current_user)]) -> User:
    return _require(UserRole.OPERATOR, user)


def require_lead(user: Annotated[User, Depends(get_current_user)]) -> User:
    return _require(UserRole.LEAD, user)


async def read_csv_upload(
    file: Annotated[UploadFile, File(description="CSV file: UTF-8, at most 10 MB.")],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CsvUpload:
    """The file stays in memory: `create_app` keeps uploads within the size limit off disk,
    because raw tickets must never be written there (ADR-0003)."""
    media_type = (file.content_type or "").split(";")[0].strip().lower()
    if media_type not in CSV_MEDIA_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, {"code": "unsupported_media_type"}
        )

    content = await file.read()
    if len(content) > settings.max_import_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, file_too_large(settings.max_import_bytes)
        )
    return CsvUpload(filename=file.filename or "", content=content)
