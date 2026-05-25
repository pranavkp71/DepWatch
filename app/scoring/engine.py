from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

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
                recommendation="Verify repository URL",
            )

        now = datetime.now(timezone.utc)
        review = HealthReview(status=HealthStatus.HEALTHY)

        days_since_commit = ScoringEngine._parse_days_since(signals.last_commit_date, now)
        days_since_release = ScoringEngine._parse_days_since(signals.latest_release_date, now)

        # 1. Collect Signals (Step 2 Implementation)
        if days_since_commit is not None:
            review.signals.append(f"Last commit {days_since_commit} days ago")
        else:
            review.signals.append("No commit history found")

        if days_since_release is not None:
            review.signals.append(f"Last release {days_since_release} days ago")
        else:
            review.signals.append("No official releases found")

        review.signals.append(f"Contributor count: {signals.contributor_count}")

        if signals.open_issues_count > 0:
            review.signals.append(f"Open issues: {signals.open_issues_count}")
            if signals.recent_issue_activity == 0:
                review.signals.append("No issue activity in last 30 days")
            else:
                review.signals.append(f"{signals.recent_issue_activity} issues updated recently")

        # 2. Compute Confidence from Signals (Step 3 Implementation)
        # We define "agreeing signals" as significant evidence (positive or negative)
        strong_signals = 0

        # Negative triggers
        no_commits_90d = days_since_commit is not None and days_since_commit > 90
        no_release_120d = days_since_release is None or days_since_release > 120
        low_contributors = signals.contributor_count < 2
        stagnant_issues = signals.open_issues_count > 50 and signals.recent_issue_activity == 0

        # Positive triggers
        recent_commit_30d = days_since_commit is not None and days_since_commit <= 30
        recent_release_60d = days_since_release is not None and days_since_release <= 60
        healthy_contributors = signals.contributor_count >= 5

        # Sum them up
        strong_signals = sum(
            [
                no_commits_90d,
                no_release_120d,
                low_contributors,
                stagnant_issues,
                recent_commit_30d,
                recent_release_60d,
                healthy_contributors,
            ]
        )

        if strong_signals >= 3:
            review.confidence = "High"
        elif strong_signals == 2:
            review.confidence = "Medium"
        else:
            review.confidence = "Low"

        # 3. Compute Risk Score (0-10) (Step 5 Implementation)
        risk_points = 0

        # Penalize stagnation
        if no_commits_90d:
            risk_points += 3

        if days_since_release is not None and days_since_release > 120:
            risk_points += 3
        elif days_since_release is None:
            # Lack of official releases is a minor signal, not a major risk
            risk_points += 1

        if low_contributors:
            risk_points += 2

        if stagnant_issues:
            risk_points += 2

        # Mitigation: Large maintainer base reduces risk
        if signals.contributor_count >= 10:
            risk_points = max(0, risk_points - 2)

        review.risk_score = min(10, risk_points)

        # 4. Final Status and Recommendation Assignment
        if review.risk_score >= 7:
            review.status = HealthStatus.RISKY
            review.recommendation = "Consider replacing this dependency"
        elif review.risk_score >= 4:
            review.status = HealthStatus.WARNING
            review.recommendation = "Monitor this dependency regularly"
        else:
            review.status = HealthStatus.HEALTHY
            review.recommendation = "No action needed"

        return review
