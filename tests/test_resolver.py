import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.resolver import TransitiveDependencyResolver
from app.services.models import DependencyNode

@pytest.mark.asyncio
async def test_recursive_resolution_simple():
    """Test standard BFS traversal (A -> B -> C)."""
    pypi_client = MagicMock()
    # Normalize helper is needed by resolver
    pypi_client._normalize_name = lambda x: x.lower()
    
    # Mock PyPI dependency responses
    async def mock_get_deps(name):
        responses = {
            "a": ["b"],
            "b": ["c"],
            "c": []
        }
        return responses.get(name, [])
        
    pypi_client.get_dependencies = AsyncMock(side_effect=mock_get_deps)
    
    resolver = TransitiveDependencyResolver(pypi_client, max_depth=3)
    nodes = await resolver.resolve(["a"])
    
    assert len(nodes) == 3
    
    # Check A (Direct)
    a_node = next(n for n in nodes if n.name == "a")
    assert a_node.depth == 0
    assert a_node.is_direct is True
    assert a_node.parent_chain == []
    
    # Check B (Transitive depth 1)
    b_node = next(n for n in nodes if n.name == "b")
    assert b_node.depth == 1
    assert b_node.is_direct is False
    assert b_node.parent_chain == ["a"]
    assert b_node.dependency_path == "a → b"
    
    # Check C (Transitive depth 2)
    c_node = next(n for n in nodes if n.name == "c")
    assert c_node.depth == 2
    assert c_node.parent_chain == ["a", "b"]
    assert c_node.dependency_path == "a → b → c"

@pytest.mark.asyncio
async def test_cycle_detection():
    """Test that cycles (A -> B -> A) don't cause infinite loops."""
    pypi_client = MagicMock()
    pypi_client._normalize_name = lambda x: x.lower()
    
    async def mock_get_deps(name):
        responses = {
            "a": ["b"],
            "b": ["a"]
        }
        return responses.get(name, [])
        
    pypi_client.get_dependencies = AsyncMock(side_effect=mock_get_deps)
    
    resolver = TransitiveDependencyResolver(pypi_client, max_depth=5)
    nodes = await resolver.resolve(["a"])
    
    # Should only have A and B
    assert len(nodes) == 2
    assert {n.name for n in nodes} == {"a", "b"}

@pytest.mark.asyncio
async def test_depth_limiting():
    """Test that max_depth is respected (A -> B -> C -> D) with depth=2."""
    pypi_client = MagicMock()
    pypi_client._normalize_name = lambda x: x.lower()
    
    async def mock_get_deps(name):
        responses = {
            "a": ["b"],
            "b": ["c"],
            "c": ["d"],
            "d": []
        }
        return responses.get(name, [])
        
    pypi_client.get_dependencies = AsyncMock(side_effect=mock_get_deps)
    
    # Max depth 2 means we resolve A(0), B(1), C(2) but NOT D(3)
    resolver = TransitiveDependencyResolver(pypi_client, max_depth=2)
    nodes = await resolver.resolve(["a"])
    
    assert len(nodes) == 3
    assert {n.name for n in nodes} == {"a", "b", "c"}
    
    c_node = next(n for n in nodes if n.name == "c")
    # C's children are fetched but not added to the resolved list if they would exceed depth
    # Actually, in my current implementation:
    # if depth < max_depth: fetch children and add to queue
    # depth 0 < 2: fetch A children (B), queue B(1)
    # depth 1 < 2: fetch B children (C), queue C(2)
    # depth 2 is NOT < 2: dont fetch C children.
    # So results should be A, B, C. This matches.
    assert c_node.depth == 2

@pytest.mark.asyncio
async def test_normalization_and_deduplication():
    """Test that different spellings of the same package are deduplicated."""
    pypi_client = MagicMock()
    # Mock real normalization logic
    import re
    def normalize(name):
        return re.sub(r"[-_.]+", "-", name).lower()
    pypi_client._normalize_name = normalize
    
    async def mock_get_deps(name):
        responses = {
            "pkg-a": ["Pkg_B"],
            "pkg-b": ["pkg.c"]
        }
        return [normalize(d) for d in responses.get(name, [])]
        
    pypi_client.get_dependencies = AsyncMock(side_effect=mock_get_deps)
    
    # Resolving "PKG_A" should find pkg-a, pkg-b, pkg-c
    resolver = TransitiveDependencyResolver(pypi_client, max_depth=3)
    nodes = await resolver.resolve(["PKG_A"])
    
    assert len(nodes) == 3
    assert {n.name for n in nodes} == {"pkg-a", "pkg-b", "pkg-c"}
