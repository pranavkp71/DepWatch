from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, List

from app.services.analyzer import DependencySignals


class HealthStatus(str, Enum):
    HEALTHY = "Healthy"
    WARNING = "Warning"
    RISKY = "Risky"
    UNKNOWN = "Unknown"


@dataclass
class HealthReview:
    status: HealthStatus
    risk_score: int = 0
    confidence: str = "Low"
    signals: List[str] = field(default_factory=list)
    recommendation: str = "No action needed"
    reason: str = ""  # Keep for backward compatibility/summary


class ScoringEngine:
    """Rule-based scoring engine for dependency health."""

    @staticmethod
    def _parse_days_since(date_str: Optional[str], now: datetime) -> Optional[int]:
        if not date_str:
            return None
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (now - dt).days

    @staticmethod
    def classify(signals: DependencySignals) -> HealthReview:
        """Classify dependency health based on gathered signals."""
        if not signals.repo_url:
            return HealthReview(
                status=HealthStatus.UNKNOWN,
                reason="Repository not found",
                confidence="Low",
                recommendation="Verify repository URL"
            )

        now = datetime.now(timezone.utc)
        review = HealthReview(status=HealthStatus.HEALTHY)

        days_since_commit = ScoringEngine._parse_days_since(signals.last_commit_date, now)
        days_since_release = ScoringEngine._parse_days_since(signals.latest_release_date, now)

        # Baseline conditions (V2 logic preserved for now, to be refined in next steps)
        no_commits_90d = days_since_commit is not None and days_since_commit > 90
        no_release_120d = days_since_release is None or days_since_release > 120
        low_contributors = signals.contributor_count < 2
        stagnant_issues = signals.open_issues_count > 50 and signals.recent_issue_activity == 0

        # Initial Status Assignment
        if no_commits_90d and no_release_120d and low_contributors:
            review.status = HealthStatus.RISKY
            review.recommendation = "Consider alternative"
        elif stagnant_issues and low_contributors:
            review.status = HealthStatus.RISKY
            review.recommendation = "Consider alternative"
        elif low_contributors or stagnant_issues or (days_since_commit and days_since_commit > 30):
            review.status = HealthStatus.WARNING
            review.recommendation = "Monitor for activity"
        else:
            review.status = HealthStatus.HEALTHY
            review.recommendation = "No action needed"

        return review
