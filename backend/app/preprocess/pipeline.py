import logging
from dataclasses import dataclass

from app.models.enums import ReviewReason, TicketStatus
from app.preprocess.clean import clean_text
from app.preprocess.content import has_no_content
from app.preprocess.injection import is_suspicious
from app.preprocess.mask import assert_masked, mask_sensitive_data
from app.preprocess.normalize import normalize_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreparedText:
    text_masked: str | None
    status: TicketStatus
    review_reason: ReviewReason | None = None


def prepare_text(raw_text: str, max_length: int) -> PreparedText:
    """Runs the steps in TRD section 4. Fails closed: on any error no text is kept."""
    try:
        normalized = normalize_text(raw_text)
        masked = mask_sensitive_data(clean_text(normalized))[:max_length]
        assert_masked(masked)

        if has_no_content(masked):
            return PreparedText(masked, TicketStatus.NEEDS_REVIEW, ReviewReason.NO_CONTENT)
        # The text before cleaning is checked, so nothing can hide in a removed quote or subject.
        if is_suspicious(normalized):
            return PreparedText(masked, TicketStatus.NEEDS_REVIEW, ReviewReason.INJECTION_SUSPECTED)
        return PreparedText(masked, TicketStatus.PENDING)
    except Exception as exc:  # Any fault here must stop the raw text.
        logger.warning("Ticket text preparation failed: %s", type(exc).__name__)
        return PreparedText(None, TicketStatus.NEEDS_REVIEW, ReviewReason.MASKING_ERROR)
