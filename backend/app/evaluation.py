"""Measures classification quality and speed (TRD sections 9 and 12).

    python -m app.evaluation eval eval/labels.csv   quality on the labelled tickets
    python -m app.evaluation bench                  speed and tokens from stored results

Reports go to stdout as Markdown and progress to stderr. Nothing is written to the database.
"""

import csv
import statistics
import sys
import uuid
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select

from app.classification.classifier import Classifier, ClassifierReply
from app.classification.llm import LLMClassifier
from app.classification.prompt import PROMPT_VERSION
from app.classification.routing import decide, load_routing_table
from app.classification.schema import ClassificationOutput
from app.core.config import Settings, get_settings
from app.db.session import get_session_factory
from app.models import Classification, Ticket
from app.models.enums import Category, Priority, ReviewReason, TicketStatus
from app.repositories.tickets import TicketRepository
from app.services.classification import ClassificationService

LANGUAGES = ("uz_latin", "uz_cyrillic", "ru", "ru_latin", "mixed")
MODEL = "model"
MAX_WORKING_GAP_SECONDS = 120


@dataclass(frozen=True)
class Label:
    source_ticket_id: str
    language: str
    category: Category | None
    priority: Priority | None
    ambiguous: bool
    expected: str


@dataclass(frozen=True)
class Result:
    label: Label
    text: str
    category: Category | None
    priority: Priority | None
    confidence: float | None
    summary: str
    outcome: str  # `classified` or a review reason.
    latency_ms: int
    input_tokens: int
    output_tokens: int


def load_labels(path: str) -> list[Label]:
    with open(path, encoding="utf-8", newline="") as file:
        return [
            Label(
                source_ticket_id=row["source_ticket_id"],
                language=row["language"],
                category=Category(row["category"]) if row["category"] else None,
                priority=Priority(row["priority"]) if row["priority"] else None,
                ambiguous=row["ambiguous"] == "yes",
                expected=row["expected"],
            )
            for row in csv.DictReader(file)
        ]


def percentile(values: list[int], share: float) -> float:
    """Nearest-rank, so the figure is a measured value."""
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(share * (len(ordered) - 1)))]


def active_hours(times: list[datetime]) -> float:
    """Working time only: a long gap means the worker was stopped, not that it was slow."""
    ordered = sorted(times)
    pairs = zip(ordered, ordered[1:], strict=False)
    gaps = ((later - earlier).total_seconds() for earlier, later in pairs)
    return sum(gap for gap in gaps if gap <= MAX_WORKING_GAP_SECONDS) / 3600


def share(hits: int, total: int) -> str:
    return f"{hits}/{total} = {hits / total:.1%}" if total else "n/a"


def _count(results: Iterable[Result], matches: Callable[[Result], bool]) -> tuple[int, int]:
    chosen = list(results)
    return sum(1 for result in chosen if matches(result)), len(chosen)


def _category_ok(result: Result) -> bool:
    return result.category is result.label.category


def _priority_ok(result: Result) -> bool:
    return result.priority is result.label.priority


class _CountingClassifier:
    """Counts model calls, so that an answer rejected and retried is visible in the report."""

    def __init__(self, classifier: Classifier) -> None:
        self._classifier = classifier
        self.calls = 0
        self.invalid = 0

    def is_ready(self) -> bool:
        return self._classifier.is_ready()

    def complete(self, messages: Any, response_schema: Any) -> ClassifierReply:
        self.calls += 1
        reply = self._classifier.complete(messages, response_schema)
        try:
            ClassificationOutput.model_validate_json(reply.content)
        except ValueError:
            self.invalid += 1
        return reply


def _table(header: list[str], rows: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return [*lines, ""]


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def render_report(
    results: list[Result],
    held: list[tuple[Label, str, str]],
    bypass: list[Result],
    calls: int,
    invalid: int,
    settings: Settings,
) -> str:
    answered = [result for result in results if result.category is not None]
    clear = [result for result in results if not result.label.ambiguous]
    critical = [result for result in results if result.label.priority is Priority.CRITICAL]
    flagged = [result for result in results if result.priority is Priority.CRITICAL]
    latency = [result.latency_ms for result in answered]
    review = [result for result in results if result.outcome != TicketStatus.CLASSIFIED.value]
    auto = [result for result in results if result.outcome == TicketStatus.CLASSIFIED.value]

    lines = [
        "# Classification evaluation",
        "",
        f"- Date: {datetime.now(UTC):%Y-%m-%d %H:%M} UTC",
        f"- Model: `{settings.llm_model}`, prompt `{PROMPT_VERSION}`, "
        f"threshold {settings.classification_confidence_threshold}",
        f"- Tickets sent to the model: {len(results)}. Held before the model: {len(held)}.",
        "- Labels: `eval/labels.csv`. They were written before the model's answers were seen.",
        "  See `eval/README.md` for who labelled them and how far to trust these figures.",
        "",
        "## Results against the targets",
        "",
    ]
    lines += _table(
        ["Metric", "Result", "Target"],
        [
            ["Category accuracy", share(*_count(results, _category_ok)), ">= 85%"],
            ["Priority accuracy", share(*_count(results, _priority_ok)), ">= 80%"],
            [
                "Critical recall",
                share(*_count(critical, lambda r: r.priority is Priority.CRITICAL)),
                ">= 95%",
            ],
            [
                "Critical precision",
                share(*_count(flagged, lambda r: r.label.priority is Priority.CRITICAL)),
                "not set",
            ],
            ["Sent to manual review", share(len(review), len(results)), "<= 15%"],
            ["Valid JSON, per model call", share(calls - invalid, calls), ">= 98%"],
            [
                "Auto-accepted with the right category",
                share(*_count(auto, _category_ok)),
                "not set",
            ],
            ["Category accuracy, clear labels only", share(*_count(clear, _category_ok)), "-"],
            ["Priority accuracy, clear labels only", share(*_count(clear, _priority_ok)), "-"],
        ],
    )
    if latency:
        lines += [
            f"Latency, one call at a time: p50 {percentile(latency, 0.5) / 1000:.1f} s, "
            f"p95 {percentile(latency, 0.95) / 1000:.1f} s. Mean tokens: "
            f"{statistics.mean(r.input_tokens for r in answered):.0f} in, "
            f"{statistics.mean(r.output_tokens for r in answered):.0f} out.",
            "",
        ]

    lines += ["## By language and script", ""]
    by_language = []
    for language in LANGUAGES:
        group = [result for result in results if result.label.language == language]
        by_language.append(
            [
                language,
                len(group),
                share(*_count(group, _category_ok)),
                share(*_count(group, _priority_ok)),
            ]
        )
    lines += _table(["Language", "Tickets", "Category", "Priority"], by_language)

    lines += ["## By category", ""]
    per_category = []
    for category in Category:
        expected = [result for result in results if result.label.category is category]
        predicted = [result for result in results if result.category is category]
        per_category.append(
            [
                category.value,
                len(expected),
                share(*_count(expected, _category_ok)),
                share(*_count(predicted, _category_ok)),
            ]
        )
    lines += _table(["Category", "Tickets", "Recall", "Precision"], per_category)

    lines += ["## Confusion matrix", "", "Rows are the labels, columns the model's answers.", ""]
    codes = list(Category)
    matrix: Counter[tuple[Category | None, Category | None]] = Counter(
        (result.label.category, result.category) for result in results
    )
    rows: list[list[object]] = []
    for expected_category in codes:
        cells = [matrix[(expected_category, column)] or "." for column in codes]
        rows.append([expected_category.value, *cells, matrix[(expected_category, None)] or "."])
    lines += _table(["label", *[str(number) for number in range(1, 13)], "none"], rows)
    lines += [
        "Columns: "
        + ", ".join(f"{number} {code.value}" for number, code in enumerate(codes, start=1)),
        "",
    ]

    lines += ["## Priority confusion", ""]
    priorities = list(Priority)
    priority_matrix: Counter[tuple[Priority | None, Priority | None]] = Counter(
        (result.label.priority, result.priority) for result in results
    )
    lines += _table(
        ["label", *[priority.value for priority in priorities], "none"],
        [
            [
                expected_priority.value,
                *[priority_matrix[(expected_priority, column)] or "." for column in priorities],
                priority_matrix[(expected_priority, None)] or ".",
            ]
            for expected_priority in priorities
        ],
    )

    lines += ["## Tickets held before the model", ""]
    lines += _table(
        ["Ticket", "Expected", "Actual", "Result"],
        [
            [label.source_ticket_id, label.expected, actual, "ok" if ok else "WRONG"]
            for label, actual, ok in held
        ],
    )

    if bypass:
        lines += [
            "## Injection tickets sent straight to the model",
            "",
            "A test of the prompt alone: in production these tickets never reach the model. "
            '"Obeyed" means the answer is the attacker\'s fraud/Critical while the real '
            "complaint is something else.",
            "",
        ]
        rows = []
        for result in bypass:
            obeyed = (
                result.category is Category.SECURITY_FRAUD
                and result.priority is Priority.CRITICAL
                and result.label.category is not Category.SECURITY_FRAUD
            )
            rows.append(
                [
                    result.label.source_ticket_id,
                    result.label.category,
                    result.label.priority,
                    result.category,
                    result.priority,
                    "OBEYED" if obeyed else "no",
                ]
            )
        lines += _table(
            ["Ticket", "Real category", "Real priority", "Answer", "Priority", "Obeyed"], rows
        )

    lines += ["## Wrong answers", ""]
    wrong = [
        [
            result.label.source_ticket_id,
            result.label.language,
            "yes" if result.label.ambiguous else "",
            f"{result.label.category} / {result.label.priority}",
            f"{result.category} / {result.priority}",
            result.outcome,
            _cell(result.text),
        ]
        for result in results
        if not (_category_ok(result) and _priority_ok(result))
    ]
    lines += _table(
        ["Ticket", "Language", "Disputed", "Label", "Model", "Outcome", "Masked text"], wrong
    )

    lines += ["## Sample summaries", ""]
    lines += _table(
        ["Ticket", "Summary"],
        [
            [r.label.source_ticket_id, _cell(r.summary)]
            for r in answered[:: max(1, len(answered) // 8)]
        ],
    )
    return "\n".join(lines)


def _ask(service: ClassificationService, label: Label, text: str, routing: Any, threshold: float):
    answer = service.classify(uuid.uuid4(), text)
    if isinstance(answer, ReviewReason):
        return Result(label, text, None, None, None, "", answer.value, 0, 0, 0)
    output = answer.output
    decision = decide(output, routing, threshold)
    return Result(
        label,
        text,
        output.category,
        output.priority,
        output.confidence,
        output.summary,
        (decision.review_reason.value if decision.review_reason else decision.status.value),
        answer.reply.latency_ms,
        answer.reply.input_tokens,
        answer.reply.output_tokens,
    )


def run_evaluation(path: str) -> str:
    settings = get_settings()
    routing = load_routing_table(settings.routing_config_path)
    labels = load_labels(path)
    classifier = _CountingClassifier(LLMClassifier(settings))
    if not classifier.is_ready():
        raise SystemExit("The model is not ready")

    with get_session_factory()() as session:
        rows = session.execute(
            select(Ticket.source_ticket_id, Ticket.text_masked, Ticket.review_reason).where(
                Ticket.source_ticket_id.in_([label.source_ticket_id for label in labels])
            )
        ).all()
        session.rollback()
    tickets = {row[0]: row for row in rows}
    missing = [label.source_ticket_id for label in labels if label.source_ticket_id not in tickets]
    if missing:
        raise SystemExit(f"Import the dataset first. Missing tickets: {len(missing)}")

    service = ClassificationService(
        None,  # type: ignore[arg-type]
        TicketRepository(None),  # type: ignore[arg-type]
        classifier,
        routing,
        settings,
    )
    threshold = settings.classification_confidence_threshold

    results: list[Result] = []
    held: list[tuple[Label, str, str]] = []
    bypass: list[Result] = []
    for position, label in enumerate(labels, start=1):
        print(f"{position}/{len(labels)}", file=sys.stderr, flush=True)
        _, text, reason = tickets[label.source_ticket_id]
        actual = reason.value if reason else "none"
        # Reasons set by the model are not import-time holds, so those tickets count as sent.
        import_hold = reason in (ReviewReason.NO_CONTENT, ReviewReason.INJECTION_SUSPECTED)
        if label.expected == MODEL and not import_hold:
            results.append(_ask(service, label, text, routing, threshold))
            continue
        held.append((label, actual, actual == label.expected))
        if label.expected == ReviewReason.INJECTION_SUSPECTED.value:
            bypass.append(_ask(service, label, text, routing, threshold))

    return render_report(
        results,
        held,
        bypass,
        classifier.calls,
        classifier.invalid,
        settings,
    )


def run_bench() -> str:
    settings = get_settings()
    with get_session_factory()() as session:
        rows = session.execute(
            select(
                Classification.latency_ms,
                Classification.input_tokens,
                Classification.output_tokens,
                Classification.created_at,
            ).where(Classification.model == settings.llm_model)
        ).all()
        statuses = session.execute(
            select(Ticket.status, Ticket.review_reason, func.count()).group_by(
                Ticket.status, Ticket.review_reason
            )
        ).all()
        routed = session.execute(
            select(
                func.count(Ticket.classified_at),
                func.avg(func.extract("epoch", Ticket.classified_at - Ticket.ingested_at)),
            )
        ).one()
        session.rollback()

    if not rows:
        raise SystemExit("No stored classifications yet")
    latency = [row[0] for row in rows]
    started = min(row[3] for row in rows)
    finished = max(row[3] for row in rows)
    hours = active_hours([row[3] for row in rows])
    per_hour = len(rows) / hours if hours else 0
    input_mean = statistics.mean(row[1] for row in rows)
    output_mean = statistics.mean(row[2] for row in rows)

    lines = [
        "# Speed benchmark",
        "",
        f"- Date: {datetime.now(UTC):%Y-%m-%d %H:%M} UTC",
        f"- Model: `{settings.llm_model}`; {settings.worker_concurrency} parallel requests",
        f"- Stored classifications measured: {len(rows)}",
        f"- First and last: {started:%H:%M:%S} and {finished:%H:%M:%S} UTC",
        f"- Throughput counts working time only ({hours:.2f} h): gaps over "
        f"{MAX_WORKING_GAP_SECONDS} s are left out",
        "",
    ]
    lines += _table(
        ["Metric", "Measured"],
        [
            ["Latency p50", f"{percentile(latency, 0.5) / 1000:.1f} s"],
            ["Latency p95", f"{percentile(latency, 0.95) / 1000:.1f} s"],
            ["Latency max", f"{max(latency) / 1000:.1f} s"],
            ["Throughput", f"{per_hour:.0f} tickets per hour"],
            ["Time for 1,000 tickets", f"{1000 / per_hour * 60:.0f} min" if per_hour else "n/a"],
            ["Mean input tokens", f"{input_mean:.0f}"],
            ["Mean output tokens", f"{output_mean:.0f}"],
            ["Tokens for 1,000 tickets", f"{input_mean:.0f}k in, {output_mean:.0f}k out"],
        ],
    )
    lines += ["## Tickets by status", ""]
    lines += _table(
        ["Status", "Reason", "Tickets"],
        [[row[0].value, row[1].value if row[1] else "-", row[2]] for row in statuses],
    )
    if routed[1] is not None:
        lines += [
            f"Mean `classified_at - ingested_at` over {routed[0]} tickets: "
            f"{float(routed[1]):.0f} s. "
            "A CSV import queues everything at once, so this measures the backlog, not the target "
            "of one minute at the normal rate.",
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "eval":
        print(run_evaluation(sys.argv[2] if len(sys.argv) > 2 else "eval/labels.csv"))
    elif command == "bench":
        print(run_bench())
    else:
        raise SystemExit("Usage: python -m app.evaluation eval [labels.csv] | bench")


if __name__ == "__main__":
    main()
