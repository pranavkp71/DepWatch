from datetime import datetime, timedelta

from app.scoring import HealthStatus, ScoringEngine
from app.services.analyzer import DependencySignals


def test_classify_healthy():
    last_commit = (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
    signals = DependencySignals(
        name="test-lib",
        repo_url="http://github.com/test/lib",
        last_commit_date=last_commit,
        contributor_count=5,
        open_issues_count=10,
        recent_issue_activity=5,
    )
    status, reason = ScoringEngine.classify(signals)
    assert status == HealthStatus.HEALTHY


def test_classify_risky_no_commits():
    last_commit = (datetime.utcnow() - timedelta(days=100)).isoformat() + "Z"
    signals = DependencySignals(
        name="stale-lib",
        repo_url="http://github.com/test/stale",
        last_commit_date=last_commit,
        contributor_count=5,
    )
    status, reason = ScoringEngine.classify(signals)
    assert status == HealthStatus.RISKY
    assert "No commits" in reason


def test_classify_warning_low_contributors():
    last_commit = (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
    signals = DependencySignals(
        name="solo-lib",
        repo_url="http://github.com/test/solo",
        last_commit_date=last_commit,
        contributor_count=1,
    )
    status, reason = ScoringEngine.classify(signals)
    assert status == HealthStatus.WARNING
    assert "Low contributor" in reason
