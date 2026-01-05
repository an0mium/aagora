"""Tests for the DocumentHandler class."""

import json
import pytest
from unittest.mock import Mock, MagicMock


class TestDocumentHandlerRouting:
    """Test route matching for DocumentHandler."""

    @pytest.fixture
    def doc_handler(self):
        from aragora.server.handlers.documents import DocumentHandler
        ctx = {"document_store": None}
        return DocumentHandler(ctx)

    def test_can_handle_documents_list(self, doc_handler):
        assert doc_handler.can_handle("/api/documents") is True

    def test_can_handle_documents_formats(self, doc_handler):
        assert doc_handler.can_handle("/api/documents/formats") is True

    def test_can_handle_document_by_id(self, doc_handler):
        assert doc_handler.can_handle("/api/documents/abc123") is True

    def test_cannot_handle_nested_path(self, doc_handler):
        assert doc_handler.can_handle("/api/documents/abc/nested") is False

    def test_cannot_handle_unknown_route(self, doc_handler):
        assert doc_handler.can_handle("/api/other") is False


class TestListDocumentsEndpoint:
    """Test /api/documents endpoint."""

    @pytest.fixture
    def mock_store(self):
        store = Mock()
        store.list_all.return_value = [
            {"id": "doc1", "filename": "test.pdf", "word_count": 100},
            {"id": "doc2", "filename": "other.txt", "word_count": 50},
        ]
        return store

    @pytest.fixture
    def doc_handler(self, mock_store):
        from aragora.server.handlers.documents import DocumentHandler
        ctx = {"document_store": mock_store}
        return DocumentHandler(ctx)

    def test_list_documents_returns_documents(self, doc_handler):
        result = doc_handler.handle("/api/documents", {}, None)
        assert result.status_code == 200
        data = json.loads(result.body)
        assert data["count"] == 2
        assert len(data["documents"]) == 2

    def test_list_documents_no_store_returns_empty(self):
        from aragora.server.handlers.documents import DocumentHandler
        ctx = {"document_store": None}
        handler = DocumentHandler(ctx)
        result = handler.handle("/api/documents", {}, None)
        assert result.status_code == 200
        data = json.loads(result.body)
        assert data["count"] == 0
        assert data["documents"] == []
        assert "error" in data


class TestFormatsEndpoint:
    """Test /api/documents/formats endpoint."""

    @pytest.fixture
    def doc_handler(self):
        from aragora.server.handlers.documents import DocumentHandler
        ctx = {"document_store": None}
        return DocumentHandler(ctx)

    def test_formats_returns_supported_types(self, doc_handler):
        result = doc_handler.handle("/api/documents/formats", {}, None)
        assert result.status_code == 200
        data = json.loads(result.body)
        # Should return some format information
        assert isinstance(data, dict)


class TestGetDocumentEndpoint:
    """Test /api/documents/{id} endpoint."""

    @pytest.fixture
    def mock_store(self):
        store = Mock()
        doc = Mock()
        doc.to_dict.return_value = {
            "id": "doc123",
            "filename": "test.pdf",
            "content": "Hello world",
        }
        store.get.return_value = doc
        return store

    @pytest.fixture
    def doc_handler(self, mock_store):
        from aragora.server.handlers.documents import DocumentHandler
        ctx = {"document_store": mock_store}
        return DocumentHandler(ctx)

    def test_get_document_returns_doc(self, doc_handler, mock_store):
        result = doc_handler.handle("/api/documents/doc123", {}, None)
        assert result.status_code == 200
        data = json.loads(result.body)
        assert data["id"] == "doc123"
        assert data["filename"] == "test.pdf"
        mock_store.get.assert_called_once_with("doc123")

    def test_get_document_not_found(self, doc_handler, mock_store):
        mock_store.get.return_value = None
        result = doc_handler.handle("/api/documents/missing", {}, None)
        assert result.status_code == 404
        data = json.loads(result.body)
        assert "error" in data

    def test_get_document_no_store_returns_500(self):
        from aragora.server.handlers.documents import DocumentHandler
        ctx = {"document_store": None}
        handler = DocumentHandler(ctx)
        result = handler.handle("/api/documents/doc123", {}, None)
        assert result.status_code == 500


class TestDocumentIdValidation:
    """Test document ID validation."""

    @pytest.fixture
    def doc_handler(self):
        from aragora.server.handlers.documents import DocumentHandler
        store = Mock()
        store.get.return_value = None  # Document not found
        ctx = {"document_store": store}
        return DocumentHandler(ctx)

    def test_path_traversal_in_id_blocked(self, doc_handler):
        # ID with path traversal pattern embedded
        result = doc_handler.handle("/api/documents/doc..id", {}, None)
        # Should return 400 for invalid ID (contains ..)
        assert result.status_code == 400
        data = json.loads(result.body)
        assert "error" in data

    def test_special_chars_blocked(self, doc_handler):
        result = doc_handler.handle("/api/documents/doc;rm", {}, None)
        assert result.status_code == 400

    def test_valid_id_accepted(self, doc_handler):
        result = doc_handler.handle("/api/documents/valid-doc-123", {}, None)
        # Should proceed to check store (returns 404 since mock returns None)
        assert result.status_code == 404
