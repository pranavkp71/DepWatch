from datetime import datetime
from enum import Enum

from app.services.analyzer import DependencySignals


class HealthStatus(str, Enum):
    HEALTHY = "Healthy"
    WARNING = "Warning"
    RISKY = "Risky"
    UNKNOWN = "Unknown"


class ScoringEngine:
    """Rule-based scoring engine for dependency health."""

    @staticmethod
    def classify(signals: DependencySignals) -> tuple[HealthStatus, str]:
        """Classify dependency health based on gathered signals."""
        if not signals.repo_url:
            return HealthStatus.UNKNOWN, "Repository not found"

        # 1. Check for Risky (Red)
        if signals.last_commit_date:
            last_commit_dt = datetime.fromisoformat(signals.last_commit_date.replace("Z", ""))
            days_since_commit = (datetime.utcnow() - last_commit_dt).days
            if days_since_commit > 90:
                return HealthStatus.RISKY, f"No commits in last {days_since_commit} days"

        if signals.open_issues_count > 50 and signals.recent_issue_activity == 0:
            return HealthStatus.RISKY, "Many open issues with no recent activity"

        # 2. Check for Warning (Yellow)
        if signals.contributor_count < 2:
            return HealthStatus.WARNING, "Low contributor count (< 2)"

        if signals.last_commit_date:
            last_commit_dt = datetime.fromisoformat(signals.last_commit_date.replace("Z", ""))
            days_since_commit = (datetime.utcnow() - last_commit_dt).days
            if days_since_commit > 30:
                return HealthStatus.WARNING, f"Slowing commit activity ({days_since_commit} days since last commit)"

        # 3. Healthy (Green)
        return HealthStatus.HEALTHY, "Active commits and responsive maintainers"
