"""Allowed values for the data model. TRD section 5: this is the single source for these lists."""

from enum import StrEnum

from sqlalchemy import Enum


class Channel(StrEnum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEB_FORM = "web_form"


class TicketStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    CLASSIFIED = "classified"
    NEEDS_REVIEW = "needs_review"


class ReviewReason(StrEnum):
    NO_CONTENT = "no_content"
    UNCLEAR = "unclear"
    LOW_CONFIDENCE = "low_confidence"
    INJECTION_SUSPECTED = "injection_suspected"
    SCHEMA_ERROR = "schema_error"
    LLM_UNAVAILABLE = "llm_unavailable"
    MASKING_ERROR = "masking_error"


class Category(StrEnum):
    PAYMENTS_TRANSFERS = "payments_transfers"
    TECHNICAL_ISSUES = "technical_issues"
    ACCOUNT_ACCESS = "account_access"
    CARD_ISSUES = "card_issues"
    FEES_CHARGES = "fees_charges"
    CREDIT_INSTALLMENTS = "credit_installments"
    IDENTITY_VERIFICATION = "identity_verification"
    SECURITY_FRAUD = "security_fraud"
    REFUNDS = "refunds"
    SUPPORT_COMPLAINTS = "support_complaints"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"


class Priority(StrEnum):
    """Declared from most to least urgent: PostgreSQL sorts enums in this order."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ImportStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(StrEnum):
    OPERATOR = "operator"
    LEAD = "lead"


def _pg_enum(enum_class: type[StrEnum], name: str) -> Enum:
    """Stores the enum's values, not its Python member names."""
    return Enum(enum_class, name=name, values_callable=lambda members: [m.value for m in members])


CHANNEL_TYPE = _pg_enum(Channel, "ticket_channel")
TICKET_STATUS_TYPE = _pg_enum(TicketStatus, "ticket_status")
REVIEW_REASON_TYPE = _pg_enum(ReviewReason, "review_reason")
CATEGORY_TYPE = _pg_enum(Category, "ticket_category")
PRIORITY_TYPE = _pg_enum(Priority, "ticket_priority")
IMPORT_STATUS_TYPE = _pg_enum(ImportStatus, "import_status")
USER_ROLE_TYPE = _pg_enum(UserRole, "user_role")
