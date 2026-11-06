from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_auth_service
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    credentials: LoginRequest, service: Annotated[AuthService, Depends(get_auth_service)]
) -> TokenResponse:
    token = service.login(credentials.username, credentials.password)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, {"code": "invalid_credentials"})
    return token
