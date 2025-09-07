"""
Tests for Vector MCP server.
"""

import pytest
import os
from unittest.mock import Mock, patch
from src.vector_mcp.src.vector_config import VectorIndexingConfig
from src.vector_mcp.src.embedding_service import EmbeddingService
from src.vector_mcp.src.supabase_vector_store import SupabaseVectorStore


class TestVectorIndexingConfig:
    """Test VectorIndexingConfig class."""
    
    def test_from_environment_missing_vars(self):
        """Test configuration loading with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            config = VectorIndexingConfig.from_environment()
            assert config is None
    
    def test_from_environment_valid_config(self):
        """Test configuration loading with valid environment variables."""
        env_vars = {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'a' * 60,  # Valid length key
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = VectorIndexingConfig.from_environment()
            assert config is not None
            assert config.supabase_url == 'https://test.supabase.co'
            assert config.table_name == 'documents'  # Default value
    
    def test_is_valid_url(self):
        """Test URL validation."""
        assert VectorIndexingConfig._is_valid_url('https://test.supabase.co')
        assert not VectorIndexingConfig._is_valid_url('http://test.com')
        assert not VectorIndexingConfig._is_valid_url('invalid-url')
    
    def test_is_valid_api_key(self):
        """Test API key validation."""
        assert VectorIndexingConfig._is_valid_api_key('a' * 60)
        assert not VectorIndexingConfig._is_valid_api_key('short')
        assert not VectorIndexingConfig._is_valid_api_key('')


class TestEmbeddingService:
    """Test EmbeddingService class."""
    
    def test_init_without_api_key(self):
        """Test initialization without OpenAI API key."""
        with patch.dict(os.environ, {}, clear=True):
            service = EmbeddingService()
            assert not service.is_available()
    
    def test_check_service_health(self):
        """Test service health check."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123456789012345678901234567890'}, clear=True):
            service = EmbeddingService()
            # Should pass basic health check even without real API key
            assert service.check_service_health()
    
    def test_chunk_text_empty(self):
        """Test text chunking with empty input."""
        service = EmbeddingService()
        chunks = service.chunk_text("")
        assert chunks == []
    
    def test_chunk_text_short(self):
        """Test text chunking with short input."""
        service = EmbeddingService()
        text = "This is a short text."
        chunks = service.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text


class TestSupabaseVectorStore:
    """Test SupabaseVectorStore class."""
    
    def test_init(self):
        """Test initialization."""
        store = SupabaseVectorStore(
            supabase_url="https://test.supabase.co",
            supabase_key="test_key"
        )
        assert store.supabase_url == "https://test.supabase.co"
        assert store.supabase_key == "test_key"
        assert store.table_name == "documents"
    
    def test_is_retryable_error(self):
        """Test error classification."""
        store = SupabaseVectorStore("url", "key")
        
        # Test retryable errors
        assert store._is_retryable_error(ConnectionError("Connection failed"))
        assert store._is_retryable_error(Exception("timeout"))
        assert store._is_retryable_error(Exception("server error"))
        
        # Test non-retryable errors
        assert not store._is_retryable_error(ValueError("Invalid input"))
        assert not store._is_retryable_error(Exception("authentication failed"))


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    from src.vector_mcp.src.vector_mcp import app
    from starlette.testclient import TestClient
    
    client = TestClient(app)
    response = client.get("/health")
    
    # Should return either healthy or degraded status
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert data["service"] == "vector-mcp"
    assert "version" in data