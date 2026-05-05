import json
import re

from app.github import GitHubClient


class DependencyScanner:
    """Service to detect and extract dependencies from a GitHub repository."""

    def __init__(self, client: GitHubClient):
        self.client = client

    async def extract_dependencies(self, owner: str, repo: str) -> list[str]:
        """Attempt to extract dependencies from known manifest files."""
        # 1. package.json (JS/TS)
        js_deps = await self._parse_package_json(owner, repo)
        if js_deps:
            return js_deps

        # 2. requirements.txt (Python legacy)
        py_deps = await self._parse_requirements_txt(owner, repo)
        if py_deps:
            return py_deps

        # 3. pyproject.toml (modern Python)
        toml_deps = await self._parse_pyproject_toml(owner, repo)
        if toml_deps:
            return toml_deps

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

        dependencies = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            match = re.match(r"^([a-zA-Z0-9_\-\[\]]+)", line)
            if match:
                dependencies.append(match.group(1))

        return list(set(dependencies))

    async def _parse_pyproject_toml(self, owner: str, repo: str) -> list[str]:
        """Extract dependency names from pyproject.toml [project] dependencies."""
        content = await self.client.get_file_content(owner, repo, "pyproject.toml")
        if not content:
            return []

        dependencies = []

        # Parse [project] dependencies section using regex (no TOML library needed for MVP)
        # Captures content between `dependencies = [` and the closing `]`
        in_deps_block = False
        for line in content.splitlines():
            stripped = line.strip()

            if re.match(r"^dependencies\s*=\s*\[", stripped):
                in_deps_block = True
                # Check if it closes on the same line
                if stripped.endswith("]"):
                    break
                continue

            if in_deps_block:
                if stripped == "]" or stripped.startswith("]"):
                    in_deps_block = False
                    break
                # Extract package name from quoted dep string like "requests>=2.0"
                match = re.search(r'["\']([a-zA-Z0-9_\-\[\]]+)', stripped)
                if match:
                    dependencies.append(match.group(1))

        return list(set(dependencies))
