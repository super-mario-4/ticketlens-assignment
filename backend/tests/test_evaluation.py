from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.core.config import Settings
from app.evaluation import (
    Label,
    Result,
    active_hours,
    load_labels,
    percentile,
    render_report,
    share,
)
from app.models.enums import Category, Priority

LABELS = Path("eval/labels.csv")


def label(category: Category, priority: Priority, language: str = "ru") -> Label:
    return Label("T-1", language, category, priority, False, "model")


def result(
    expected: tuple[Category, Priority],
    answer: tuple[Category, Priority] | None,
    outcome: str = "classified",
) -> Result:
    category, priority = answer or (None, None)
    return Result(
        label(*expected), "matn", category, priority, 0.9, "xulosa", outcome, 1000, 500, 80
    )


FRAUD = (Category.SECURITY_FRAUD, Priority.CRITICAL)
PAYMENT = (Category.PAYMENTS_TRANSFERS, Priority.HIGH)


def render(results: list[Result], calls: int = 4, invalid: int = 0) -> str:
    return render_report(results, [], [], calls, invalid, Settings())


@pytest.mark.parametrize(("value", "expected"), [(0.5, 3), (0.95, 5), (0, 1), (1, 5)])
def test_percentile_is_a_measured_value(value: float, expected: int) -> None:
    assert percentile([5, 1, 3, 2, 4], value) == expected


def test_active_hours_leave_out_the_time_the_worker_was_stopped() -> None:
    start = datetime(2026, 11, 6, tzinfo=UTC)
    times = [start, start + timedelta(seconds=60), start + timedelta(hours=2)]

    assert active_hours(times) == pytest.approx(60 / 3600)
    assert active_hours([start]) == 0


def test_share_with_nothing_to_measure() -> None:
    assert share(0, 0) == "n/a"
    assert share(1, 4) == "1/4 = 25.0%"


def test_report_counts_right_and_wrong_answers() -> None:
    report = render(
        [
            result(PAYMENT, PAYMENT),
            result(PAYMENT, FRAUD),
            result(FRAUD, FRAUD),
            result(FRAUD, PAYMENT),
        ]
    )

    assert "| Category accuracy | 2/4 = 50.0% |" in report
    assert "| Priority accuracy | 2/4 = 50.0% |" in report
    assert "| Critical recall | 1/2 = 50.0% |" in report
    assert "| Critical precision | 1/2 = 50.0% |" in report


def test_a_ticket_the_model_failed_counts_against_it() -> None:
    report = render([result(PAYMENT, None, "llm_unavailable")], calls=2)

    assert "| Category accuracy | 0/1 = 0.0% |" in report
    assert "| Sent to manual review | 1/1 = 100.0% |" in report


def test_invalid_answers_lower_json_validity() -> None:
    assert "| Valid JSON, per model call | 3/4 = 75.0% |" in render(
        [result(PAYMENT, PAYMENT)], invalid=1
    )


def test_a_fraud_answer_counts_as_obeyed_only_when_the_complaint_is_something_else() -> None:
    report = render_report(
        [result(PAYMENT, PAYMENT)],
        [],
        [result(FRAUD, FRAUD), result(PAYMENT, FRAUD)],
        3,
        0,
        Settings(),
    )

    assert report.count("| OBEYED |") == 1


@pytest.mark.skipif(not LABELS.exists(), reason="The labels are mounted in Docker")
@pytest.mark.parametrize("field", ["category", "priority"])
def test_held_tickets_need_their_real_complaint(field: str) -> None:
    held = [item for item in load_labels(str(LABELS)) if item.expected == "injection_suspected"]

    assert all(getattr(item, field) for item in held)


@pytest.mark.skipif(not LABELS.exists(), reason="The labels are mounted in Docker")
def test_label_file_meets_the_assignment() -> None:
    labels = load_labels(str(LABELS))

    sent = [item for item in labels if item.expected == "model"]
    assert len(sent) >= 50
    assert len({item.source_ticket_id for item in labels}) == len(labels)
    assert {item.category for item in sent} == set(Category)
    assert {item.priority for item in sent} == set(Priority)
    assert {item.language for item in sent} == {
        "uz_latin",
        "uz_cyrillic",
        "ru",
        "ru_latin",
        "mixed",
    }
