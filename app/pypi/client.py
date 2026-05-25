"""PyPI JSON API client for resolving transitive dependencies."""

import re
from typing import Optional

import httpx


class PyPIClient:
    """Async client for the PyPI JSON API with in-memory caching."""

    BASE_URL = "https://pypi.org"

    def __init__(self) -> None:
        self._cache: dict[str, list[str]] = {}

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize a package name per PEP 503 (lowercase, hyphens → dashes)."""
        return re.sub(r"[-_.]+", "-", name).lower()

    @staticmethod
    def _parse_dep_name(dep_string: str) -> Optional[str]:
        """Extract the clean package name from a PEP 508 dependency string.

        Examples:
            'requests>=2.0'            → 'requests'
            'urllib3[socks]!=1.25.0'   → 'urllib3'
            'foo ; python_version<"3"' → 'foo'
            'bar (>=1.0)'              → 'bar'
        """
        # Strip environment markers (everything after ';')
        dep_string = dep_string.split(";")[0].strip()
        # Extract the package name (before any extras, version specifiers, or parens)
        match = re.match(r"^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)", dep_string)
        return match.group(1) if match else None

    async def get_dependencies(self, package_name: str) -> list[str]:
        """Fetch the runtime dependencies of a package from PyPI.

        Returns a list of normalized dependency package names.
        Results are cached in-memory for the lifetime of this client.
        """
        normalized = self._normalize_name(package_name)

        if normalized in self._cache:
            return self._cache[normalized]

        deps: list[str] = []
        try:
            async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=15.0) as client:
                response = await client.get(f"/pypi/{normalized}/json")
                if response.status_code != 200:
                    self._cache[normalized] = []
                    return []

                data = response.json()
                requires_dist: list[str] = data.get("info", {}).get("requires_dist") or []

                for dep_str in requires_dist:
                    # Skip dependencies with 'extra ==' markers (optional extras)
                    if "extra ==" in dep_str or "extra==" in dep_str:
                        continue
                    name = self._parse_dep_name(dep_str)
                    if name:
                        deps.append(self._normalize_name(name))

        except (httpx.HTTPError, Exception):
            # Network errors, timeouts, JSON parse errors — fail gracefully
            pass

        self._cache[normalized] = deps
        return deps
