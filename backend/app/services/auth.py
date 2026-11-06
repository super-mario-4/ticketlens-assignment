from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_token, hash_password, verify_password
from app.models.enums import UserRole
from app.repositories.users import UserRepository
from app.schemas.auth import TokenResponse

# Checked for an unknown name too, so response time does not reveal which names exist.
_NO_USER_HASH = hash_password("no user")


class AuthService:
    def __init__(self, session: Session, users: UserRepository, settings: Settings) -> None:
        self._session = session
        self._users = users
        self._settings = settings

    def login(self, username: str, password: str) -> TokenResponse | None:
        user = self._users.get_by_username(username)
        stored = user.password_hash if user else _NO_USER_HASH
        if not verify_password(password, stored) or user is None:
            return None
        return TokenResponse(
            access_token=create_token(user.id, self._settings),
            username=user.username,
            role=user.role,
        )

    def create_configured_users(self) -> None:
        """Accounts come from the environment (TRD section 6)."""
        settings = self._settings
        accounts = (
            (settings.operator_username, settings.operator_password, UserRole.OPERATOR),
            (settings.lead_username, settings.lead_password, UserRole.LEAD),
        )
        for username, password, role in accounts:
            self._users.add_if_missing(username, hash_password(password.get_secret_value()), role)
        self._session.commit()
