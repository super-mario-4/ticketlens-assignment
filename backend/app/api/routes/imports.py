import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    CsvUpload,
    get_current_user,
    get_import_service,
    read_csv_upload,
    require_operator,
)
from app.models import ImportJob, User
from app.schemas.imports import ImportJobResponse
from app.services.imports import ImportFileError, ImportService

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_import(
    upload: Annotated[CsvUpload, Depends(read_csv_upload)],
    user: Annotated[User, Depends(require_operator)],
    service: Annotated[ImportService, Depends(get_import_service)],
) -> ImportJobResponse:
    """Imports a CSV file sent as `multipart/form-data`. It never reaches disk."""
    try:
        job = service.run(upload.content, upload.filename, user)
    except ImportFileError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, error.detail) from None
    return _response(job)


@router.get("/{job_id}")
def get_import(
    job_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[ImportService, Depends(get_import_service)],
) -> ImportJobResponse:
    job = service.get(job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {"code": "import_not_found"})
    return _response(job)


def _response(job: ImportJob) -> ImportJobResponse:
    return ImportJobResponse.model_validate(job)
