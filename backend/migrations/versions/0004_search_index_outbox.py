"""Adds the Elasticsearch outbox and queues every ticket that already has text.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

operation_type = postgresql.ENUM("index", "delete", name="outbox_operation", create_type=False)
status_type = postgresql.ENUM("pending", "done", "failed", name="outbox_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    operation_type.create(bind)
    status_type.create(bind)
    op.create_table(
        "search_index_outbox",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("operation", operation_type, nullable=False),
        sa.Column("status", status_type, nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.String(128), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_search_index_outbox_status_created_at",
        "search_index_outbox",
        ["status", "created_at"],
    )
    op.execute(
        """
        INSERT INTO search_index_outbox (id, ticket_id, operation, status)
        SELECT gen_random_uuid(), id, 'index', 'pending'
        FROM tickets WHERE text_masked IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_table("search_index_outbox")
    bind = op.get_bind()
    status_type.drop(bind)
    operation_type.drop(bind)
