from datetime import datetime, timedelta, timezone

from app.scoring import HealthStatus, ScoringEngine
from app.services.analyzer import DependencySignals


def test_classify_healthy():
    last_commit = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    signals = DependencySignals(
        name="test-lib",
        repo_url="http://github.com/test/lib",
        last_commit_date=last_commit,
        contributor_count=5,
        open_issues_count=10,
        recent_issue_activity=5,
    )
    review = ScoringEngine.classify(signals)
    assert review.status == HealthStatus.HEALTHY
    assert review.risk_score <= 1  # 1 point for no official release found
    assert "Last commit 5 days ago" in review.signals


def test_risk_mitigation():
    """V3: Mitigation for large maintainer base."""
    stale_date = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
    signals = DependencySignals(
        name="large-lib",
        repo_url="http://github.com/test/large",
        last_commit_date=stale_date,
        contributor_count=20, # Large maintainer base
    )
    review = ScoringEngine.classify(signals)
    # Stale commits (+3) + No release (+1) = 4. Mitigation (-2) = 2.
    assert review.status == HealthStatus.HEALTHY
    assert review.risk_score == 2
