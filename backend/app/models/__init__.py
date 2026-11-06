"""SQLAlchemy models. Import each model here so Alembic can detect it."""

from app.models.classification import Classification
from app.models.correction import Correction
from app.models.import_job import ImportJob
from app.models.search_index_outbox import SearchIndexOutbox
from app.models.ticket import Ticket
from app.models.user import User

__all__ = ["Classification", "Correction", "ImportJob", "SearchIndexOutbox", "Ticket", "User"]
