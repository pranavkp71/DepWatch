from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any

from app.services.analyzer import DependencySignals


class HealthStatus(str, Enum):
    HEALTHY = "Healthy"
    WARNING = "Warning"
    RISKY = "Risky"
    UNKNOWN = "Unknown"


class ScoringEngine:
    """Rule-based scoring engine for dependency health."""

    @staticmethod
    def _parse_days_since(date_str: Optional[str], now: datetime) -> Optional[int]:
        if not date_str:
            return None
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (now - dt).days

    @staticmethod
    def classify(signals: DependencySignals) -> tuple[HealthStatus, str, str]:
        """Classify dependency health based on gathered signals. Returns (status, reason, confidence)."""
        if not signals.repo_url:
            return HealthStatus.UNKNOWN, "Repository not found", "Low"

        now = datetime.now(timezone.utc)

        days_since_commit = ScoringEngine._parse_days_since(signals.last_commit_date, now)
        days_since_release = ScoringEngine._parse_days_since(signals.latest_release_date, now)

        # Build conditions
        no_commits_90d = days_since_commit is not None and days_since_commit > 90
        no_release_120d = days_since_release is None or days_since_release > 120
        low_contributors = signals.contributor_count < 2
        
        slow_commits_30d = days_since_commit is not None and days_since_commit > 30
        no_release_60d = days_since_release is None or days_since_release > 60
        stagnant_issues = signals.open_issues_count > 50 and signals.recent_issue_activity == 0

        # Calculate confidence based on negative signals
        negative_signals = sum([
            no_commits_90d,
            no_release_120d,
            low_contributors,
            stagnant_issues,
            slow_commits_30d
        ])

        if negative_signals >= 3:
            confidence = "High"
        elif negative_signals == 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # 1. 🔴 Risky
        if no_commits_90d and no_release_120d and low_contributors:
            return HealthStatus.RISKY, "No recent commits and no releases in 120+ days with low maintainer activity", confidence
            
        if stagnant_issues and low_contributors:
            return HealthStatus.RISKY, "Many open issues with no recent activity and low maintainer count", confidence

        # 2. 🟡 Warning
        if low_contributors:
            return HealthStatus.WARNING, "Stable but maintained by a solo developer or low contributor count (< 2)", confidence

        if slow_commits_30d and no_release_60d:
            return HealthStatus.WARNING, "Slowing commit activity and no recent releases in 60+ days", confidence
            
        if stagnant_issues:
            return HealthStatus.WARNING, "Many open issues with no recent activity", confidence

        # 3. 🟢 Healthy
        return HealthStatus.HEALTHY, "Active commits or recent releases with reasonable maintainer count", confidence
