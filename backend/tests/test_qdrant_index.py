"""
Tests for the Qdrant index module.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import numpy as np

from app.qdrant_index import (
    QdrantConfig,
    QdrantIndex,
    get_qdrant_index
)


class TestQdrantConfig:
    """Test Qdrant configuration."""
    
    def test_get_config_eco(self):
        """Test eco profile configuration."""
        config = QdrantConfig.get_config('eco')
        
        assert config['vectors_config']['size'] == 384
        assert config['vectors_config']['distance'] == 'Cosine'
        assert config['optimizers_config']['default_segment_number'] == 2
        assert config['hnsw_config']['ef_construct'] == 100
    
    def test_get_config_balanced(self):
        """Test balanced profile configuration."""
        config = QdrantConfig.get_config('balanced')
        
        assert config['vectors_config']['size'] == 768
        assert config['vectors_config']['distance'] == 'Cosine'
        assert config['optimizers_config']['default_segment_number'] == 4
        assert config['hnsw_config']['ef_construct'] == 200
    
    def test_get_config_performance(self):
        """Test performance profile configuration."""
        config = QdrantConfig.get_config('performance')
        
        assert config['vectors_config']['size'] == 768
        assert config['vectors_config']['distance'] == 'Cosine'
        assert config['optimizers_config']['default_segment_number'] == 8
        assert config['hnsw_config']['ef_construct'] == 400
    
    def test_get_config_default(self):
        """Test unknown profile defaults to balanced."""
        config = QdrantConfig.get_config('unknown')
        assert config == QdrantConfig.get_config('balanced')


class TestQdrantIndex:
    """Test Qdrant index functionality."""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client."""
        mock = Mock()
        mock.get_cluster_info.return_value = Mock(
            peer_id="test-peer",
            raft_info=Mock()
        )
        mock.get_collections.return_value = Mock(collections=[])
        mock.create_collection.return_value = None
        mock.update_collection.return_value = None
        mock.upsert.return_value = Mock(operation_id=123)
        mock.get_operations.return_value = Mock(operations=[])
        return mock
    
    @pytest.fixture
    def qdrant_index(self):
        """Create QdrantIndex instance."""
        with patch('app.qdrant_index.get_settings') as mock_settings:
            mock_settings.return_value.qdrant_url = "http://test:6333"
            return QdrantIndex('balanced')
    
    def test_qdrant_index_initialization(self, qdrant_index):
        """Test QdrantIndex initialization."""
        assert qdrant_index.profile == 'balanced'
        assert qdrant_index.qdrant_url == "http://test:6333"
        assert qdrant_index.client is None
        assert qdrant_index.collection_exists is False
    
    @pytest.mark.asyncio
    async def test_initialize_not_available(self, qdrant_index):
        """Test initialization when qdrant-client not available."""
        with patch('app.qdrant_index.QDRANT_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="qdrant-client not available"):
                await qdrant_index.initialize()
    
    @pytest.mark.asyncio
    @patch('app.qdrant_index.QDRANT_AVAILABLE', True)
    @patch('app.qdrant_index.QdrantClient')
    async def test_initialize_success(self, mock_client_class, qdrant_index, mock_qdrant_client):
        """Test successful initialization."""
        mock_client_class.return_value = mock_qdrant_client
        
        await qdrant_index.initialize()
        
        assert qdrant_index.client is not None
        mock_client_class.assert_called_once_with(url="http://test:6333")
        mock_qdrant_client.get_cluster_info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.qdrant_index.QDRANT_AVAILABLE', True)
    @patch('app.qdrant_index.QdrantClient')
    async def test_initialize_connection_error(self, mock_client_class, qdrant_index):
        """Test initialization with connection error."""
        mock_client = Mock()
        mock_client.get_cluster_info.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client
        
        with pytest.raises(RuntimeError, match="Cannot connect to Qdrant"):
            await qdrant_index.initialize()
    
    @pytest.mark.asyncio
    async def test_index_chunks(self, qdrant_index, mock_qdrant_client):
        """Test indexing chunks."""
        qdrant_index.client = mock_qdrant_client
        qdrant_index.collection_exists = True
        
        chunks = [
            {
                "text": "Test chunk 1",
                "embedding": [1.0, 2.0, 3.0],
                "chunk_id": 1,
                "token_count": 10
            },
            {
                "text": "Test chunk 2", 
                "embedding": [4.0, 5.0, 6.0],
                "chunk_id": 2,
                "token_count": 15
            }
        ]
        
        stats = await qdrant_index.index_chunks(chunks, "doc123")
        
        assert stats['indexed'] == 2
        assert stats['skipped'] == 0
        assert stats['errors'] == 0
        mock_qdrant_client.upsert.assert_called_once()
        
        # Check that points were created correctly
        call_args = mock_qdrant_client.upsert.call_args
        points = call_args[0][1]  # Second argument is points
        assert len(points) == 2
        assert points[0].id == "doc123_1"
        assert points[0].payload['doc_id'] == "doc123"
        assert points[0].payload['text'] == "Test chunk 1"
    
    @pytest.mark.asyncio
    async def test_index_chunks_missing_embedding(self, qdrant_index, mock_qdrant_client):
        """Test indexing chunks with missing embeddings."""
        qdrant_index.client = mock_qdrant_client
        qdrant_index.collection_exists = True
        
        chunks = [
            {"text": "Valid chunk", "embedding": [1.0, 2.0], "chunk_id": 1},
            {"text": "Missing embedding", "chunk_id": 2},  # No embedding
            {"embedding": [3.0, 4.0], "chunk_id": 3}  # No text
        ]
        
        stats = await qdrant_index.index_chunks(chunks, "doc123")
        
        assert stats['indexed'] == 1
        assert stats['skipped'] == 2
        assert stats['errors'] == 0
    
    @pytest.mark.asyncio
    async def test_search_similar(self, qdrant_index, mock_qdrant_client):
        """Test similarity search."""
        qdrant_index.client = mock_qdrant_client
        qdrant_index.collection_exists = True
        
        # Mock search results
        mock_result = [
            Mock(
                id="doc123_1",
                score=0.95,
                payload={
                    'doc_id': 'doc123',
                    'chunk_id': 1,
                    'text': 'Test chunk',
                    'token_count': 10,
                    'chunk_index': 0,
                    'meta_source': 'page1'
                }
            )
        ]
        mock_qdrant_client.search.return_value = mock_result
        
        query_embedding = np.array([1.0, 2.0, 3.0])
        results = await qdrant_index.search_similar(query_embedding, limit=5)
        
        assert len(results) == 1
        assert results[0]['id'] == "doc123_1"
        assert results[0]['score'] == 0.95
        assert results[0]['doc_id'] == 'doc123'
        assert results[0]['text'] == 'Test chunk'
        assert results[0]['metadata']['source'] == 'page1'
        
        # Verify search was called correctly
        mock_qdrant_client.search.assert_called_once()
        call_args = mock_qdrant_client.search.call_args[0]
        assert call_args[0] == qdrant_index.COLLECTION_NAME
        assert call_args[1] == [1.0, 2.0, 3.0]  # Query vector
        assert call_args[3] == 5  # Limit
    
    @pytest.mark.asyncio
    async def test_search_similar_with_filter(self, qdrant_index, mock_qdrant_client):
        """Test similarity search with document filter."""
        qdrant_index.client = mock_qdrant_client
        qdrant_index.collection_exists = True
        mock_qdrant_client.search.return_value = []
        
        query_embedding = np.array([1.0, 2.0])
        await qdrant_index.search_similar(
            query_embedding, 
            limit=10,
            doc_filter=['doc1', 'doc2']
        )
        
        # Check that filter was applied
        call_args = mock_qdrant_client.search.call_args[0]
        query_filter = call_args[2]  # Third argument is filter
        assert query_filter is not None
    
    @pytest.mark.asyncio
    async def test_delete_document_chunks(self, qdrant_index, mock_qdrant_client):
        """Test deleting document chunks."""
        qdrant_index.client = mock_qdrant_client
        qdrant_index.collection_exists = True
        
        result = await qdrant_index.delete_document_chunks("doc123")
        
        assert result == 1  # Success indicator
        mock_qdrant_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_collection_stats(self, qdrant_index, mock_qdrant_client):
        """Test getting collection statistics."""
        qdrant_index.client = mock_qdrant_client
        qdrant_index.collection_exists = True
        
        # Mock collection info
        mock_collection_info = Mock()
        mock_collection_info.points_count = 100
        mock_collection_info.segments_count = 2
        mock_collection_info.status.name = "Green"
        mock_collection_info.config.params.vectors.size = 768
        mock_collection_info.config.params.vectors.distance.name = "Cosine"
        mock_collection_info.config.optimizer_config = None
        
        mock_qdrant_client.get_collection.return_value = mock_collection_info
        
        stats = await qdrant_index.get_collection_stats()
        
        assert stats['collection_name'] == 'rag_chunks'
        assert stats['points_count'] == 100
        assert stats['segments_count'] == 2
        assert stats['vector_size'] == 768
        assert stats['distance'] == 'Cosine'
        assert stats['status'] == 'Green'
        assert stats['profile'] == 'balanced'
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, qdrant_index, mock_qdrant_client):
        """Test successful health check."""
        qdrant_index.client = mock_qdrant_client
        qdrant_index.collection_exists = True
        
        mock_cluster_info = Mock(
            peer_id="test-peer",
            raft_info=Mock()
        )
        mock_qdrant_client.get_cluster_info.return_value = mock_cluster_info
        
        health = await qdrant_index.health_check()
        
        assert health['status'] == 'healthy'
        assert health['peer_id'] == 'test-peer'
        assert health['collection_exists'] is True
        assert health['url'] == "http://test:6333"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, qdrant_index):
        """Test health check failure."""
        # Don't initialize client to simulate connection failure
        health = await qdrant_index.health_check()
        
        assert health['status'] == 'unhealthy'
        assert 'error' in health
        assert health['url'] == "http://test:6333"
    
    @pytest.mark.asyncio
    async def test_cleanup(self, qdrant_index):
        """Test cleanup."""
        mock_client = Mock()
        qdrant_index.client = mock_client
        qdrant_index.collection_exists = True
        
        await qdrant_index.cleanup()
        
        mock_client.close.assert_called_once()
        assert qdrant_index.client is None
        assert qdrant_index.collection_exists is False


@pytest.mark.asyncio
async def test_get_qdrant_index():
    """Test getting global Qdrant index instance."""
    with patch('app.qdrant_index.get_settings') as mock_settings:
        mock_settings.return_value.performance_profile = 'eco'
        mock_settings.return_value.qdrant_url = "http://localhost:6333"
        
        with patch.object(QdrantIndex, 'initialize', new_callable=AsyncMock):
            index1 = await get_qdrant_index()
            index2 = await get_qdrant_index()
            
            # Should return same instance
            assert index1 is index2
            assert index1.profile == 'eco'


@pytest.mark.asyncio
async def test_get_qdrant_index_profile_change():
    """Test getting Qdrant index with profile change."""
    with patch('app.qdrant_index.get_settings') as mock_settings:
        mock_settings.return_value.performance_profile = 'balanced'
        mock_settings.return_value.qdrant_url = "http://localhost:6333"
        
        with patch.object(QdrantIndex, 'initialize', new_callable=AsyncMock) as mock_init:
            with patch.object(QdrantIndex, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
                # Get first instance
                index1 = await get_qdrant_index('eco')
                assert index1.profile == 'eco'
                
                # Get with different profile - should create new instance
                index2 = await get_qdrant_index('performance')
                assert index2.profile == 'performance'
                assert index1 is not index2
                
                # Old instance should be cleaned up
                mock_cleanup.assert_called_once()
