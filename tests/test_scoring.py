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
    status, reason, confidence = ScoringEngine.classify(signals)
    assert status == HealthStatus.HEALTHY
    assert confidence == "Low"  # Data is good, no negative signals


def test_classify_stable_but_healthy():
    """V2: A library with no commits but a recent release should be healthy."""
    last_release = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    signals = DependencySignals(
        name="stable-lib",
        repo_url="http://github.com/test/stable",
        last_commit_date=(datetime.now(timezone.utc) - timedelta(days=100)).isoformat(),
        latest_release_date=last_release,
        contributor_count=5,
    )
    status, reason, confidence = ScoringEngine.classify(signals)
    assert status == HealthStatus.HEALTHY


def test_classify_risky_multi_signal():
    """V2: Risky only if commits, releases, and contributors are all bad."""
    stale_date = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
    signals = DependencySignals(
        name="dead-lib",
        repo_url="http://github.com/test/dead",
        last_commit_date=stale_date,
        latest_release_date=stale_date,
        contributor_count=1,
    )
    status, reason, confidence = ScoringEngine.classify(signals)
    assert status == HealthStatus.RISKY
    assert confidence == "High"


def test_classify_warning_solo_developer():
    last_commit = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    signals = DependencySignals(
        name="solo-lib",
        repo_url="http://github.com/test/solo",
        last_commit_date=last_commit,
        contributor_count=1,
    )
    status, reason, confidence = ScoringEngine.classify(signals)
    assert status == HealthStatus.WARNING
    assert "solo developer" in reason
    assert confidence == "Low"
