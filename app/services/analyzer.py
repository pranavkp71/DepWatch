from dataclasses import dataclass
from typing import Optional

from app.github import GitHubClient


@dataclass
class DependencySignals:
    name: str
    repo_url: Optional[str] = None
    last_commit_date: Optional[str] = None
    latest_release_date: Optional[str] = None  # V2: release activity signal
    contributor_count: int = 0
    open_issues_count: int = 0
    recent_issue_activity: int = 0  # Issues updated in last 30 days


class DependencyAnalyzer:
    """Service to analyze health signals for a list of dependencies."""

    def __init__(self, client: GitHubClient):
        self.client = client

    async def analyze(self, name: str) -> DependencySignals:
        """Fetch health signals for a single dependency."""
        signals = DependencySignals(name=name)

        # 1. Resolve repo
        repo_data = await self.client.search_repo(name)
        if not repo_data:
            return signals

        owner = repo_data["owner"]["login"]
        repo = repo_data["name"]
        signals.repo_url = repo_data["html_url"]

        # 2. Fetch signals
        last_commit = await self.client.get_last_commit(owner, repo)
        if last_commit:
            signals.last_commit_date = last_commit["commit"]["committer"]["date"]

        signals.latest_release_date = await self.client.get_latest_release(owner, repo)
        signals.contributor_count = await self.client.get_contributor_count(owner, repo)
        signals.open_issues_count = await self.client.get_open_issues_count(owner, repo)
        signals.recent_issue_activity = await self.client.get_recent_issue_activity(owner, repo)

        return signals
