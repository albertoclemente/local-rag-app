"""
Tests for the embeddings module.
"""

import numpy as np
import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.embeddings import (
    EmbeddingConfig,
    EmbeddingCache,
    LocalEmbedder,
    embed_chunks,
    embed_query,
    get_embedding_info
)


class TestEmbeddingConfig:
    """Test embedding configuration."""
    
    def test_get_config_eco(self):
        """Test eco profile configuration."""
        config = EmbeddingConfig.get_config('eco')
        
        assert config['model_name'] == 'all-MiniLM-L6-v2'
        assert config['device'] == 'cpu'
        assert config['batch_size'] == 16
        assert config['max_workers'] == 2
    
    def test_get_config_balanced(self):
        """Test balanced profile configuration."""
        config = EmbeddingConfig.get_config('balanced')
        
        assert config['model_name'] == 'all-mpnet-base-v2'
        assert config['device'] == 'auto'
        assert config['batch_size'] == 32
        assert config['max_workers'] == 4
    
    def test_get_config_performance(self):
        """Test performance profile configuration."""
        config = EmbeddingConfig.get_config('performance')
        
        assert config['model_name'] == 'all-mpnet-base-v2'
        assert config['device'] == 'auto'
        assert config['batch_size'] == 64
        assert config['max_workers'] == 8
    
    def test_get_config_default(self):
        """Test unknown profile defaults to balanced."""
        config = EmbeddingConfig.get_config('unknown')
        
        assert config == EmbeddingConfig.get_config('balanced')


class TestEmbeddingCache:
    """Test embedding cache functionality."""
    
    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        return tmp_path / "embeddings_cache"
    
    @pytest.fixture
    def cache(self, cache_dir):
        """Create embedding cache instance."""
        return EmbeddingCache(cache_dir)
    
    def test_cache_miss(self, cache):
        """Test cache miss."""
        embedding = cache.get("test text", "test-model")
        assert embedding is None
        assert cache.stats['misses'] == 1
        assert cache.stats['hits'] == 0
    
    def test_cache_set_and_get(self, cache):
        """Test setting and getting from cache."""
        text = "test text"
        model = "test-model"
        embedding = np.array([1.0, 2.0, 3.0])
        
        # Set in cache
        cache.set(text, model, embedding)
        
        # Get from cache
        cached_embedding = cache.get(text, model)
        assert cached_embedding is not None
        np.testing.assert_array_equal(cached_embedding, embedding)
        assert cache.stats['hits'] == 1
    
    def test_cache_different_models(self, cache):
        """Test that different models have separate cache entries."""
        text = "same text"
        embedding1 = np.array([1.0, 2.0])
        embedding2 = np.array([3.0, 4.0])
        
        cache.set(text, "model1", embedding1)
        cache.set(text, "model2", embedding2)
        
        cached1 = cache.get(text, "model1")
        cached2 = cache.get(text, "model2")
        
        np.testing.assert_array_equal(cached1, embedding1)
        np.testing.assert_array_equal(cached2, embedding2)
    
    def test_cache_clear(self, cache):
        """Test cache clearing."""
        cache.set("text1", "model", np.array([1.0]))
        cache.set("text2", "model", np.array([2.0]))
        
        cleared_count = cache.clear()
        assert cleared_count == 2
        assert cache.get("text1", "model") is None
        assert cache.stats['hits'] == 0
        assert cache.stats['misses'] == 1


class TestLocalEmbedder:
    """Test local embedder functionality."""
    
    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer."""
        mock = Mock()
        mock.encode.return_value = np.array([[1.0, 2.0, 3.0]])
        mock.max_seq_length = 512
        mock.device = "cpu"
        return mock
    
    @pytest.fixture
    def embedder(self, tmp_path):
        """Create embedder instance with temporary storage."""
        with patch('app.embeddings.get_settings') as mock_settings:
            mock_settings.return_value.storage_path = str(tmp_path)
            return LocalEmbedder('eco')
    
    def test_embedder_initialization(self, embedder):
        """Test embedder initialization."""
        assert embedder.profile == 'eco'
        assert embedder.model_name == 'all-MiniLM-L6-v2'
        assert embedder.device == 'cpu'  # eco profile uses cpu
        assert embedder.model is None
    
    def test_determine_device_cpu(self, embedder):
        """Test device determination for CPU."""
        with patch('app.embeddings.TORCH_AVAILABLE', False):
            device = embedder._determine_device()
            assert device == 'cpu'
    
    @patch('app.embeddings.TORCH_AVAILABLE', True)
    @patch('app.embeddings.torch')
    def test_determine_device_cuda(self, mock_torch, embedder):
        """Test device determination with CUDA."""
        embedder.config['device'] = 'auto'
        mock_torch.cuda.is_available.return_value = True
        
        device = embedder._determine_device()
        assert device == 'cuda'
    
    def test_get_embedding_dimension(self, embedder):
        """Test embedding dimension lookup."""
        assert embedder.get_embedding_dimension() == 384  # MiniLM
        
        embedder.model_name = 'all-mpnet-base-v2'
        assert embedder.get_embedding_dimension() == 768  # MPNet
    
    @pytest.mark.asyncio
    async def test_embed_text_not_available(self, embedder):
        """Test embedding when sentence-transformers not available."""
        with patch('app.embeddings.SENTENCE_TRANSFORMERS_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="sentence-transformers not available"):
                await embedder.embed_text("test")
    
    @pytest.mark.asyncio
    @patch('app.embeddings.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    async def test_embed_texts_with_cache(self, embedder, mock_sentence_transformer):
        """Test embedding with caching."""
        # Mock the model loading
        with patch.object(embedder, '_load_model', return_value=mock_sentence_transformer):
            # First embedding - should generate and cache
            result1 = await embedder.embed_texts(["test text"])
            assert len(result1) == 1
            assert isinstance(result1[0], np.ndarray)
            
            # Reset mock to ensure it's not called again
            mock_sentence_transformer.encode.reset_mock()
            
            # Second embedding - should use cache
            result2 = await embedder.embed_texts(["test text"])
            assert len(result2) == 1
            
            # Model should not be called again (cache hit)
            mock_sentence_transformer.encode.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, embedder):
        """Test getting model information."""
        info = await embedder.get_model_info()
        
        assert info['model_name'] == 'all-MiniLM-L6-v2'
        assert info['device'] in ['cpu', 'mps']  # Accept both CPU and Metal Performance Shaders
        assert info['profile'] == 'eco'
        assert info['dimension'] == 384
        assert 'cache_stats' in info
        assert 'available' in info


@pytest.mark.asyncio
async def test_embed_chunks():
    """Test chunk embedding function."""
    chunks = [
        {"text": "First chunk", "chunk_id": 1},
        {"text": "Second chunk", "chunk_id": 2}
    ]
    
    mock_embedder = AsyncMock()
    mock_embedder.embed_texts.return_value = [
        np.array([1.0, 2.0]),
        np.array([3.0, 4.0])
    ]
    
    with patch('app.embeddings.get_embedder', return_value=mock_embedder):
        result = await embed_chunks(chunks)
        
        assert len(result) == 2
        assert result[0]['text'] == "First chunk"
        assert result[0]['chunk_id'] == 1
        assert result[0]['embedding'] == [1.0, 2.0]
        assert result[1]['text'] == "Second chunk"
        assert result[1]['chunk_id'] == 2
        assert result[1]['embedding'] == [3.0, 4.0]


@pytest.mark.asyncio
async def test_embed_query():
    """Test query embedding function."""
    mock_embedder = AsyncMock()
    mock_embedder.embed_text.return_value = np.array([1.0, 2.0, 3.0])
    
    with patch('app.embeddings.get_embedder', return_value=mock_embedder):
        result = await embed_query("test query")
        
        np.testing.assert_array_equal(result, np.array([1.0, 2.0, 3.0]))
        mock_embedder.embed_text.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_get_embedding_info_success():
    """Test getting embedding info successfully."""
    mock_embedder = AsyncMock()
    mock_embedder.get_model_info.return_value = {
        'model_name': 'test-model',
        'available': True
    }
    
    with patch('app.embeddings.get_embedder', return_value=mock_embedder):
        result = await get_embedding_info()
        
        assert result['model_name'] == 'test-model'
        assert result['available'] is True


@pytest.mark.asyncio
async def test_get_embedding_info_error():
    """Test getting embedding info with error."""
    with patch('app.embeddings.get_embedder', side_effect=Exception("Test error")):
        result = await get_embedding_info()
        
        assert result['available'] is False
        assert result['error'] == "Test error"
        assert result['model_name'] == 'unknown'
        assert result['dimension'] == 0


@pytest.mark.asyncio
async def test_embed_chunks_empty():
    """Test embedding empty chunk list."""
    result = await embed_chunks([])
    assert result == []


@pytest.mark.asyncio
async def test_embedder_cleanup():
    """Test embedder cleanup."""
    embedder = LocalEmbedder('eco')
    mock_executor = Mock()
    embedder.executor = mock_executor
    embedder.model = Mock()
    
    await embedder.cleanup()
    
    mock_executor.shutdown.assert_called_once_with(wait=True)
    assert embedder.executor is None
    assert embedder.model is None
