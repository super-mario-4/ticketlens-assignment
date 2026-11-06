from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import create_app
from app.models import User
from app.models.enums import UserRole


def acting_operator(session: Annotated[Session, Depends(get_db)]) -> User:
    """For tests about something other than login. `test_auth.py` covers the real path."""
    session.execute(
        insert(User)
        .values(username="system", password_hash="!", role=UserRole.OPERATOR)
        .on_conflict_do_nothing(index_elements=[User.username])
    )
    return session.scalars(select(User).where(User.username == "system")).one()


def authorized_app() -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_current_user] = acting_operator
    return app
