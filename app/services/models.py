"""Shared data models for dependency tree representation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DependencyNode:
    """Represents a single dependency in the resolved tree.

    Attributes:
        name: Normalized package name.
        depth: Distance from the root (0 = direct dependency).
        parent_chain: Ordered list of ancestor names from root to this node.
                      e.g. ['fastapi', 'starlette'] means fastapi → starlette → this.
        is_direct: True if this is a direct (top-level) dependency.
        children: Names of this node's direct sub-dependencies.
    """

    name: str
    depth: int = 0
    parent_chain: list[str] = field(default_factory=list)
    is_direct: bool = True
    children: list[str] = field(default_factory=list)

    @property
    def dependency_path(self) -> str:
        """Human-readable dependency path string.

        Example: 'fastapi → starlette → anyio'
        """
        chain = [*self.parent_chain, self.name]
        return " → ".join(chain)
