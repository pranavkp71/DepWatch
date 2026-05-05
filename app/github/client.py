import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from fastapi import HTTPException


class GitHubClient:
    """Async client for GitHub REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DepWatch-Scanner",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    async def _get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> Any:
        async with httpx.AsyncClient(base_url=self.BASE_URL, headers=self.headers) as client:
            response = await client.get(endpoint, params=params)
            if response.status_code == 404:
                return None
            if response.status_code == 403:
                # Likely rate limit
                raise HTTPException(
                    status_code=403, detail="GitHub API rate limit exceeded or forbidden."
                )
            response.raise_for_status()
            return response.json()

    async def get_repo_metadata(self, owner: str, repo: str) -> Optional[dict[str, Any]]:
        """Fetch general repository information."""
        return await self._get(f"/repos/{owner}/{repo}")

    async def get_last_commit(self, owner: str, repo: str) -> Optional[dict[str, Any]]:
        """Fetch the most recent commit."""
        commits = await self._get(f"/repos/{owner}/{repo}/commits", params={"per_page": 1})
        return commits[0] if commits else None

    async def get_contributor_count(self, owner: str, repo: str) -> int:
        """Fetch total contributor count (approximated via per_page=1)."""
        # Using a trick: per_page=1 and looking at the 'Link' header would be better,
        # but for MVP we'll just fetch a small list or use the 'size' if available.
        # GitHub stats API is better for this.
        contributors = await self._get(f"/repos/{owner}/{repo}/contributors", params={"per_page": 1})
        # Note: This is simplified. Real logic should check headers for total count.
        # But per-page=1 doesn't give total count easily without Link header parsing.
        # For MVP, we'll fetch up to 100 to see if it's "low".
        contributors = await self._get(f"/repos/{owner}/{repo}/contributors", params={"per_page": 100})
        return len(contributors) if contributors else 0

    async def get_open_issues_count(self, owner: str, repo: str) -> int:
        """Fetch count of open issues."""
        repo_data = await self.get_repo_metadata(owner, repo)
        return repo_data.get("open_issues_count", 0) if repo_data else 0

    async def get_recent_issue_activity(self, owner: str, repo: str, days: int = 30) -> int:
        """Fetch count of issues updated in the last N days."""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        issues = await self._get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": "all", "since": since, "per_page": 100},
        )
        return len(issues) if issues else 0

    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Fetch content of a file from the repository (decoded as UTF-8)."""
        data = await self._get(f"/repos/{owner}/{repo}/contents/{path}")
        if data and "content" in data:
            import base64

            # GitHub encodes content in base64
            content_encoded = data["content"]
            return base64.b64decode(content_encoded).decode("utf-8")
        return None

    async def search_repo(self, query: str) -> Optional[dict[str, Any]]:
        """Search for a repository and return the first result."""
        data = await self._get("/search/repositories", params={"q": query, "per_page": 1})
        if data and "items" in data and data["items"]:
            return data["items"][0]
        return None

    async def get_latest_release(self, owner: str, repo: str) -> Optional[str]:
        """Fetch the date of the latest release. Returns None if no releases exist."""
        data = await self._get(f"/repos/{owner}/{repo}/releases/latest")
        if data and "published_at" in data:
            return data["published_at"]
        return None
