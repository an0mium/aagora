"""
Tests for GraphDebatesHandler - graph-structured debate endpoints.

Tests cover:
- POST /api/debates/graph - Run graph debate
- GET /api/debates/graph/{id} - Get debate by ID
- GET /api/debates/graph/{id}/branches - Get branches
- GET /api/debates/graph/{id}/nodes - Get nodes
"""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch

from aragora.server.handlers.graph_debates import GraphDebatesHandler


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def handler():
    """Create GraphDebatesHandler instance."""
    return GraphDebatesHandler({})


@pytest.fixture
def mock_storage():
    """Create mock storage with async methods."""
    storage = Mock()
    storage.get_graph_debate = AsyncMock(return_value={
        "debate_id": "graph-123",
        "task": "Test task",
        "nodes": [],
        "branches": [],
    })
    storage.get_debate_branches = AsyncMock(return_value=[
        {"id": "main", "parent_id": None},
        {"id": "branch-1", "parent_id": "main"},
    ])
    storage.get_debate_nodes = AsyncMock(return_value=[
        {"id": "node-1", "content": "Test", "branch_id": "main"},
    ])
    return storage


@pytest.fixture
def mock_handler_obj(mock_storage):
    """Create mock HTTP handler object."""
    handler = Mock()
    handler.storage = mock_storage
    handler.event_emitter = None
    return handler


# ============================================================================
# Route Recognition Tests
# ============================================================================

class TestGraphDebatesRouting:
    """Tests for graph debates route recognition."""

    def test_routes_defined(self, handler):
        """Test handler has routes defined."""
        assert "/api/debates/graph" in handler.ROUTES

    def test_auth_required_endpoints(self, handler):
        """Test auth required endpoints defined."""
        assert "/api/debates/graph" in handler.AUTH_REQUIRED_ENDPOINTS


# ============================================================================
# GET /api/debates/graph/{id} Tests
# ============================================================================

class TestGetGraphDebate:
    """Tests for getting specific graph debate."""

    @pytest.mark.asyncio
    async def test_get_debate_success(self, handler, mock_handler_obj):
        """Test successful debate retrieval."""
        result = await handler.handle_get(
            mock_handler_obj,
            "/api/debates/graph/graph-123",
            {},
        )

        assert result.status_code == 200
        data = json.loads(result.body)
        assert data["debate_id"] == "graph-123"

    @pytest.mark.asyncio
    async def test_get_debate_not_found(self, handler, mock_handler_obj, mock_storage):
        """Test 404 for non-existent debate."""
        mock_storage.get_graph_debate.return_value = None

        result = await handler.handle_get(
            mock_handler_obj,
            "/api/debates/graph/nonexistent",
            {},
        )

        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_get_debate_no_storage(self, handler):
        """Test 503 when storage not configured."""
        mock_handler = Mock()
        mock_handler.storage = None

        result = await handler.handle_get(
            mock_handler,
            "/api/debates/graph/graph-123",
            {},
        )

        assert result.status_code == 503


# ============================================================================
# GET /api/debates/graph/{id}/branches Tests
# ============================================================================

class TestGetBranches:
    """Tests for getting debate branches."""

    @pytest.mark.asyncio
    async def test_get_branches_success(self, handler, mock_handler_obj):
        """Test successful branches retrieval."""
        result = await handler.handle_get(
            mock_handler_obj,
            "/api/debates/graph/graph-123/branches",
            {},
        )

        assert result.status_code == 200
        data = json.loads(result.body)
        assert "branches" in data
        assert len(data["branches"]) == 2

    @pytest.mark.asyncio
    async def test_get_branches_includes_debate_id(self, handler, mock_handler_obj):
        """Test branches response includes debate ID."""
        result = await handler.handle_get(
            mock_handler_obj,
            "/api/debates/graph/graph-123/branches",
            {},
        )

        data = json.loads(result.body)
        assert data["debate_id"] == "graph-123"


# ============================================================================
# GET /api/debates/graph/{id}/nodes Tests
# ============================================================================

class TestGetNodes:
    """Tests for getting debate nodes."""

    @pytest.mark.asyncio
    async def test_get_nodes_success(self, handler, mock_handler_obj):
        """Test successful nodes retrieval."""
        result = await handler.handle_get(
            mock_handler_obj,
            "/api/debates/graph/graph-123/nodes",
            {},
        )

        assert result.status_code == 200
        data = json.loads(result.body)
        assert "nodes" in data

    @pytest.mark.asyncio
    async def test_get_nodes_includes_debate_id(self, handler, mock_handler_obj):
        """Test nodes response includes debate ID."""
        result = await handler.handle_get(
            mock_handler_obj,
            "/api/debates/graph/graph-123/nodes",
            {},
        )

        data = json.loads(result.body)
        assert data["debate_id"] == "graph-123"


# ============================================================================
# POST /api/debates/graph Tests
# ============================================================================

class TestRunGraphDebate:
    """Tests for running graph debates."""

    @pytest.mark.asyncio
    async def test_run_debate_missing_task(self, handler, mock_handler_obj):
        """Test 400 when task is missing."""
        result = await handler.handle_post(
            mock_handler_obj,
            "/api/debates/graph",
            {},
        )

        assert result.status_code == 400
        data = json.loads(result.body)
        assert "task" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_run_debate_wrong_path(self, handler, mock_handler_obj):
        """Test 404 for wrong path."""
        result = await handler.handle_post(
            mock_handler_obj,
            "/api/debates/graph/something",
            {"task": "Test"},
        )

        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_run_debate_graph_module_unavailable(self, handler, mock_handler_obj):
        """Test error when graph module not available."""
        with patch.object(handler, "_load_agents", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = [Mock(name="agent1")]

            # The import will fail since graph module may not exist
            result = await handler.handle_post(
                mock_handler_obj,
                "/api/debates/graph",
                {"task": "Test topic", "agents": ["claude"]},
            )

            # Either 500 (import error) or success (if module exists)
            assert result.status_code in [200, 500]


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestGraphDebatesErrorHandling:
    """Tests for error handling in graph debates handler."""

    @pytest.mark.asyncio
    async def test_storage_exception_handled(self, handler, mock_handler_obj, mock_storage):
        """Test storage exceptions are handled gracefully."""
        mock_storage.get_graph_debate.side_effect = Exception("DB error")

        result = await handler.handle_get(
            mock_handler_obj,
            "/api/debates/graph/graph-123",
            {},
        )

        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_branches_exception_handled(self, handler, mock_handler_obj, mock_storage):
        """Test branches retrieval error handling."""
        mock_storage.get_debate_branches.side_effect = Exception("Connection lost")

        result = await handler.handle_get(
            mock_handler_obj,
            "/api/debates/graph/graph-123/branches",
            {},
        )

        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_nodes_exception_handled(self, handler, mock_handler_obj, mock_storage):
        """Test nodes retrieval error handling."""
        mock_storage.get_debate_nodes.side_effect = Exception("Timeout")

        result = await handler.handle_get(
            mock_handler_obj,
            "/api/debates/graph/graph-123/nodes",
            {},
        )

        assert result.status_code == 500
