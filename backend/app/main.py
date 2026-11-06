import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from starlette.formparsers import MultiPartParser

from app.api.deps import file_too_large, get_routing
from app.api.middleware import UploadSizeLimitMiddleware
from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import get_engine, get_session_factory
from app.repositories.imports import ImportRepository
from app.repositories.search_outbox import SearchOutboxRepository
from app.repositories.tickets import TicketRepository
from app.repositories.users import UserRepository
from app.services.auth import AuthService
from app.services.imports import ImportService

logger = logging.getLogger(__name__)

# Room for the multipart boundary and part headers around the file itself.
MULTIPART_OVERHEAD_BYTES = 64 * 1024


def _create_configured_users() -> None:
    try:
        with get_session_factory()() as session:
            AuthService(session, UserRepository(session), get_settings()).create_configured_users()
    except SQLAlchemyError as exc:
        logger.warning("Configured users were not created: %s", type(exc).__name__)


def _recover_interrupted_imports() -> None:
    settings = get_settings()
    try:
        with get_session_factory()() as session:
            service = ImportService(
                session,
                ImportRepository(session),
                TicketRepository(session),
                settings,
                SearchOutboxRepository(session),
            )
            recovered = service.recover_interrupted()
    except SQLAlchemyError as exc:
        logger.warning("Interrupted imports were not checked: %s", type(exc).__name__)
        return
    if recovered:
        logger.warning("Marked %d interrupted import jobs as failed", recovered)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_settings()  # Stops startup early if the configuration is invalid.
    get_routing()  # The same for the routing file.
    _create_configured_users()
    _recover_interrupted_imports()
    yield
    get_engine().dispose()


async def _database_unavailable(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": {"code": "database_unavailable"}},
    )


def create_app() -> FastAPI:
    app = FastAPI(title="TicketLens API", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(OperationalError, _database_unavailable)

    # Starlette moves uploads over 1 MB to a temporary file. Raw tickets must never reach disk
    # (ADR-0003), so anything the size limit accepts stays in memory.
    max_bytes = get_settings().max_import_bytes
    max_upload_bytes = max_bytes + MULTIPART_OVERHEAD_BYTES
    MultiPartParser.spool_max_size = max_upload_bytes
    app.add_middleware(
        UploadSizeLimitMiddleware,
        path="/api/imports",
        max_bytes=max_upload_bytes,
        detail=file_too_large(max_bytes),
    )
    app.include_router(api_router)
    return app


app = create_app()
