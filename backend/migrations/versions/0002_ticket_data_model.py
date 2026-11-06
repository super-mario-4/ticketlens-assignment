"""Ticket data model: users, import jobs, tickets, classifications and corrections.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Several columns share these types, so they are created once, before the tables.
channel = postgresql.ENUM(
    "telegram", "email", "web_form", name="ticket_channel", create_type=False
)
ticket_status = postgresql.ENUM(
    "pending", "processing", "classified", "needs_review", name="ticket_status", create_type=False
)
review_reason = postgresql.ENUM(
    "no_content",
    "unclear",
    "low_confidence",
    "injection_suspected",
    "schema_error",
    "llm_unavailable",
    "masking_error",
    name="review_reason",
    create_type=False,
)
category = postgresql.ENUM(
    "payments_transfers",
    "technical_issues",
    "account_access",
    "card_issues",
    "fees_charges",
    "credit_installments",
    "identity_verification",
    "security_fraud",
    "refunds",
    "support_complaints",
    "feature_request",
    "other",
    name="ticket_category",
    create_type=False,
)
priority = postgresql.ENUM(
    "Critical", "High", "Medium", "Low", name="ticket_priority", create_type=False
)
import_status = postgresql.ENUM(
    "processing", "completed", "failed", name="import_status", create_type=False
)
user_role = postgresql.ENUM("operator", "lead", name="user_role", create_type=False)

ENUM_TYPES = (
    channel,
    ticket_status,
    review_reason,
    category,
    priority,
    import_status,
    user_role,
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in ENUM_TYPES:
        enum_type.create(bind)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )

    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("status", import_status, nullable=False),
        sa.Column("total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("inserted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skipped", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "errors",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "total >= 0 AND inserted >= 0 AND skipped >= 0",
            name=op.f("ck_import_jobs_counts_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_import_jobs_created_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_jobs")),
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_ticket_id", sa.String(length=64), nullable=False),
        sa.Column("channel", channel, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("text_masked", sa.Text(), nullable=True),
        sa.Column("status", ticket_status, nullable=False),
        sa.Column("review_reason", review_reason, nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("import_job_id", sa.Uuid(), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("classified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("attempts >= 0", name=op.f("ck_tickets_attempts_non_negative")),
        sa.CheckConstraint(
            "status <> 'needs_review' OR review_reason IS NOT NULL",
            name=op.f("ck_tickets_needs_review_has_reason"),
        ),
        sa.CheckConstraint(
            "status <> 'processing' OR processing_started_at IS NOT NULL",
            name=op.f("ck_tickets_processing_has_start_time"),
        ),
        sa.CheckConstraint(
            "text_masked IS NOT NULL OR review_reason IS NOT DISTINCT FROM 'masking_error'",
            name=op.f("ck_tickets_text_required_unless_masking_error"),
        ),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["import_jobs.id"],
            name=op.f("fk_tickets_import_job_id_import_jobs"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tickets")),
        sa.UniqueConstraint("source_ticket_id", name=op.f("uq_tickets_source_ticket_id")),
    )
    op.create_index("ix_tickets_status_created_at", "tickets", ["status", "created_at"])
    op.create_index("ix_tickets_channel_created_at", "tickets", ["channel", "created_at"])
    op.create_index(op.f("ix_tickets_import_job_id"), "tickets", ["import_job_id"])
    op.create_index(op.f("ix_tickets_ingested_at"), "tickets", ["ingested_at"])

    op.create_table(
        "classifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("category", category, nullable=False),
        sa.Column("priority", priority, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("team", sa.String(length=64), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name=op.f("ck_classifications_confidence_range"),
        ),
        sa.CheckConstraint(
            "latency_ms >= 0 AND input_tokens >= 0 AND output_tokens >= 0",
            name=op.f("ck_classifications_usage_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            name=op.f("fk_classifications_ticket_id_tickets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_classifications")),
    )
    op.create_index(
        "ix_classifications_ticket_id_created_at",
        "classifications",
        ["ticket_id", "created_at"],
    )

    op.create_table(
        "corrections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("old_category", category, nullable=True),
        sa.Column("new_category", category, nullable=False),
        sa.Column("old_priority", priority, nullable=True),
        sa.Column("new_priority", priority, nullable=False),
        sa.Column("old_team", sa.String(length=64), nullable=True),
        sa.Column("new_team", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("corrected_by", sa.Uuid(), nullable=False),
        sa.Column(
            "corrected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["corrected_by"],
            ["users.id"],
            name=op.f("fk_corrections_corrected_by_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            name=op.f("fk_corrections_ticket_id_tickets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_corrections")),
    )
    op.create_index(
        "ix_corrections_ticket_id_corrected_at",
        "corrections",
        ["ticket_id", "corrected_at"],
    )


def downgrade() -> None:
    op.drop_table("corrections")
    op.drop_table("classifications")
    op.drop_table("tickets")
    op.drop_table("import_jobs")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_type in ENUM_TYPES:
        enum_type.drop(bind)
