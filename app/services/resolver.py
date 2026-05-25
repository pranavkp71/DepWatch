"""Recursive dependency tree resolver using PyPI metadata."""

import asyncio
import collections
from typing import List

from app.pypi.client import PyPIClient
from app.services.models import DependencyNode


class TransitiveDependencyResolver:
    """Resolves a complete dependency tree from a list of direct dependencies."""

    def __init__(self, pypi_client: PyPIClient, max_depth: int = 3):
        self.pypi_client = pypi_client
        self.max_depth = max_depth

    async def resolve(self, direct_deps: List[str]) -> List[DependencyNode]:
        """Resolve all transitive dependencies using BFS traversal.

        Args:
            direct_deps: List of top-level package names.

        Returns:
            A flat list of all unique DependencyNode objects (direct + transitive).
        """
        # Flat list of results
        resolved_nodes: List[DependencyNode] = []

        # Tracking visited packages to prevent cycles and redundant network calls
        # Maps package_name -> depth at which it was first found
        visited = {}

        # BFS queue: (package_name, depth, parent_chain)
        queue = collections.deque()

        # Add direct dependencies to queue
        for dep in direct_deps:
            norm_name = self.pypi_client._normalize_name(dep)
            if norm_name not in visited:
                visited[norm_name] = 0
                queue.append((norm_name, 0, []))

        while queue:
            # Current batch processing for concurrency (optional, but good for speed)
            # Process one "level" at a time or just go one-by-one.
            # To keep it simple for MVP, we'll go one by one but we could batch them.
            name, depth, parent_chain = queue.popleft()

            # Create the node
            node = DependencyNode(
                name=name,
                depth=depth,
                parent_chain=parent_chain,
                is_direct=(depth == 0)
            )

            # If we haven't reached max depth, fetch children
            if depth < self.max_depth:
                children_names = await self.pypi_client.get_dependencies(name)
                node.children = children_names

                # Prepare children for queue
                for child in children_names:
                    if child not in visited:
                        visited[child] = depth + 1
                        queue.append((child, depth + 1, parent_chain + [name]))

            resolved_nodes.append(node)

        return resolved_nodes
