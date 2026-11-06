import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import User
from app.models.enums import UserRole


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: uuid.UUID) -> User | None:
        return self._session.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self._session.scalars(select(User).where(User.username == username)).one_or_none()

    def add_if_missing(self, username: str, password_hash: str, role: UserRole) -> None:
        """An existing account keeps its password."""
        self._session.execute(
            insert(User)
            .values(username=username, password_hash=password_hash, role=role)
            .on_conflict_do_nothing(index_elements=[User.username])
        )
