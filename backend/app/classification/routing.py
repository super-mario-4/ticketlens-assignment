from dataclasses import dataclass
from pathlib import Path

import yaml

from app.classification.schema import ClassificationOutput
from app.models.enums import Category, ReviewReason, TicketStatus

_MAX_TEAM_LENGTH = 64
_ROUTED_CATEGORIES = frozenset(Category) - {Category.OTHER}


class RoutingConfigError(Exception):
    """The routing file cannot be used. Fails at startup, not on a ticket."""


@dataclass(frozen=True)
class RoutingTable:
    teams: dict[Category, str]

    def team_for(self, category: Category) -> str:
        return self.teams[category]


@dataclass(frozen=True)
class RoutingDecision:
    status: TicketStatus
    review_reason: ReviewReason | None = None
    team: str | None = None


def load_routing_table(path: str | Path) -> RoutingTable:
    try:
        config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RoutingConfigError(f"Cannot read routing file: {type(exc).__name__}") from exc

    teams = config.get("teams") if isinstance(config, dict) else None
    if not isinstance(teams, dict):
        raise RoutingConfigError("Routing file has no `teams` mapping")

    if set(teams) != {category.value for category in _ROUTED_CATEGORIES}:
        raise RoutingConfigError("Routing file must list every category except `other`")
    for team in teams.values():
        if not isinstance(team, str) or not team.strip() or len(team) > _MAX_TEAM_LENGTH:
            raise RoutingConfigError("Routing file has an invalid team name")

    return RoutingTable({Category(category): team for category, team in teams.items()})


def decide(
    output: ClassificationOutput, routing: RoutingTable, confidence_threshold: float
) -> RoutingDecision:
    """The checks run in the order set by ADR-0004. A team is assigned only to a routed ticket."""
    if output.confidence < confidence_threshold:
        return RoutingDecision(TicketStatus.NEEDS_REVIEW, ReviewReason.LOW_CONFIDENCE)
    if output.category is Category.OTHER:
        return RoutingDecision(TicketStatus.NEEDS_REVIEW, ReviewReason.UNCLEAR)
    return RoutingDecision(TicketStatus.CLASSIFIED, team=routing.team_for(output.category))
