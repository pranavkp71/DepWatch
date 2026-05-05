import json
import re
from typing import Optional

from app.github import GitHubClient


class DependencyScanner:
    """Service to detect and extract dependencies from a GitHub repository."""

    def __init__(self, client: GitHubClient):
        self.client = client

    async def extract_dependencies(self, owner: str, repo: str) -> list[str]:
        """Attempt to extract dependencies from package.json or requirements.txt."""
        # Check package.json (JS/TS)
        js_deps = await self._parse_package_json(owner, repo)
        if js_deps:
            return js_deps

        # Check requirements.txt (Python)
        py_deps = await self._parse_requirements_txt(owner, repo)
        if py_deps:
            return py_deps

        return []

    async def _parse_package_json(self, owner: str, repo: str) -> list[str]:
        """Extract dependency names from package.json."""
        content = await self.client.get_file_content(owner, repo, "package.json")
        if not content:
            return []

        try:
            data = json.loads(content)
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            return list(set(list(deps.keys()) + list(dev_deps.keys())))
        except (json.JSONDecodeError, AttributeError):
            return []

    async def _parse_requirements_txt(self, owner: str, repo: str) -> list[str]:
        """Extract dependency names from requirements.txt."""
        content = await self.client.get_file_content(owner, repo, "requirements.txt")
        if not content:
            return []

        # Simple regex to extract package names from requirements.txt
        # Handles lines like: requests==2.31.0, flask>=2.0, etc.
        dependencies = []
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Match package name at start of line
            match = re.match(r"^([a-zA-Z0-9_\-\[\]]+)", line)
            if match:
                dependencies.append(match.group(1))

        return list(set(dependencies))
