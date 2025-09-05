"""
Tests for the retrieval module and dynamic-k algorithms.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import numpy as np

from app.retrieval import (
    QueryComplexity,
    RetrievalParams,
    ChunkResult,
    RetrievalResult,
    QueryAnalyzer,
    CoverageMeter,
    DynamicKController,
    RetrievalEngine,
    get_retrieval_engine
)


class TestQueryAnalyzer:
    """Test query complexity analysis."""
    
    def test_simple_query_analysis(self):
        """Test simple query detection."""
        simple_queries = [
            "What is Python?",
            "Define machine learning",
            "Who is the author?",
            "When was it published?"
        ]
        
        for query in simple_queries:
            complexity = QueryAnalyzer.analyze_complexity(query)
            assert complexity == QueryComplexity.SIMPLE, f"Query '{query}' should be SIMPLE"
    
    def test_complex_query_analysis(self):
        """Test complex query detection."""
        complex_queries = [
            "Compare and contrast the advantages and disadvantages of different machine learning approaches",
            "Analyze the relationship between economic factors and social outcomes in developing countries",
            "Provide a comprehensive overview of the implications of artificial intelligence on employment",
            "How does the implementation of renewable energy systems differ across various geographical regions?"
        ]
        
        for query in complex_queries:
            complexity = QueryAnalyzer.analyze_complexity(query)
            assert complexity == QueryComplexity.COMPLEX, f"Query '{query}' should be COMPLEX"
    
    def test_moderate_query_analysis(self):
        """Test moderate query detection."""
        moderate_queries = [
            "Tell me about machine learning",
            "Describe the benefits of Python for data science",
            "Tell me about neural networks",
            "Discuss the impact of artificial intelligence"
        ]
        
        for query in moderate_queries:
            complexity = QueryAnalyzer.analyze_complexity(query)
            assert complexity == QueryComplexity.MODERATE, f"Query '{query}' should be MODERATE"
    
    def test_edge_cases(self):
        """Test edge cases in query analysis."""
        # Empty query
        assert QueryAnalyzer.analyze_complexity("") == QueryComplexity.SIMPLE
        
        # Very short query
        assert QueryAnalyzer.analyze_complexity("AI") == QueryComplexity.SIMPLE
        
        # Multiple questions
        complexity = QueryAnalyzer.analyze_complexity("What is AI? How does it work? Why is it important?")
        assert complexity == QueryComplexity.COMPLEX


class TestCoverageMeter:
    """Test coverage analysis functionality."""
    
    @pytest.fixture
    def coverage_meter(self):
        """Create coverage meter instance."""
        return CoverageMeter()
    
    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        return [
            ChunkResult(
                id="chunk1", doc_id="doc1", chunk_id="1", 
                text="Machine learning is a subset of artificial intelligence",
                score=0.9, token_count=10, chunk_index=0, metadata={}
            ),
            ChunkResult(
                id="chunk2", doc_id="doc1", chunk_id="2",
                text="Deep learning uses neural networks with multiple layers",
                score=0.85, token_count=9, chunk_index=1, metadata={}
            ),
            ChunkResult(
                id="chunk3", doc_id="doc2", chunk_id="1",
                text="Natural language processing helps computers understand human language",
                score=0.8, token_count=10, chunk_index=0, metadata={}
            )
        ]
    
    def test_calculate_coverage_empty(self, coverage_meter):
        """Test coverage calculation with empty chunks."""
        query_embedding = np.array([1.0, 2.0, 3.0])
        coverage = coverage_meter.calculate_coverage([], query_embedding)
        assert coverage == 0.0
    
    def test_calculate_coverage_single_chunk(self, coverage_meter, sample_chunks):
        """Test coverage calculation with single chunk."""
        query_embedding = np.array([1.0, 2.0, 3.0])
        coverage = coverage_meter.calculate_coverage([sample_chunks[0]], query_embedding)
        assert 0.0 < coverage <= 1.0
    
    def test_calculate_coverage_multiple_chunks(self, coverage_meter, sample_chunks):
        """Test coverage calculation with multiple chunks."""
        query_embedding = np.array([1.0, 2.0, 3.0])
        coverage = coverage_meter.calculate_coverage(sample_chunks, query_embedding)
        assert 0.0 < coverage <= 1.0
        
        # Coverage should increase with more diverse content
        coverage_single = coverage_meter.calculate_coverage([sample_chunks[0]], query_embedding)
        assert coverage >= coverage_single
    
    def test_coverage_plateau_detection(self, coverage_meter):
        """Test coverage plateau detection."""
        # Simulate plateau by adding similar coverage scores
        coverage_meter.coverage_history = [0.5, 0.6, 0.61, 0.61]
        assert coverage_meter.has_coverage_plateaued()
        
        # Test non-plateau
        coverage_meter.coverage_history = [0.3, 0.5, 0.7]
        assert not coverage_meter.has_coverage_plateaued()
    
    def test_similarity_penalty(self, coverage_meter):
        """Test similarity penalty for duplicate content."""
        # Create chunks with overlapping content
        similar_chunks = [
            ChunkResult(
                id="chunk1", doc_id="doc1", chunk_id="1",
                text="machine learning artificial intelligence",
                score=0.9, token_count=4, chunk_index=0, metadata={}
            ),
            ChunkResult(
                id="chunk2", doc_id="doc1", chunk_id="2", 
                text="machine learning deep neural networks",
                score=0.85, token_count=5, chunk_index=1, metadata={}
            )
        ]
        
        penalty = coverage_meter._calculate_similarity_penalty(similar_chunks)
        assert 0.0 < penalty < 1.0  # Should have some penalty for overlapping content


class TestDynamicKController:
    """Test dynamic-k controller functionality."""
    
    @pytest.fixture
    def controller(self):
        """Create DynamicKController instance."""
        params = RetrievalParams(k_min=3, k_max=8, budget_tokens=1000)
        return DynamicKController(params)
    
    @pytest.fixture
    def mock_qdrant_service(self):
        """Mock Qdrant service."""
        mock = AsyncMock()
        mock.search_similar.return_value = [
            {
                'id': 'chunk1', 'doc_id': 'doc1', 'chunk_id': '1',
                'text': 'Machine learning is powerful', 'score': 0.9,
                'token_count': 5, 'chunk_index': 0, 'metadata': {}
            },
            {
                'id': 'chunk2', 'doc_id': 'doc1', 'chunk_id': '2', 
                'text': 'Deep learning uses neural networks', 'score': 0.85,
                'token_count': 6, 'chunk_index': 1, 'metadata': {}
            },
            {
                'id': 'chunk3', 'doc_id': 'doc2', 'chunk_id': '1',
                'text': 'AI transforms many industries', 'score': 0.8,
                'token_count': 5, 'chunk_index': 0, 'metadata': {}
            }
        ]
        return mock
    
    @pytest.mark.asyncio
    async def test_determine_optimal_k_simple_query(self, controller, mock_qdrant_service):
        """Test dynamic-k for simple query."""
        query = "What is machine learning?"
        query_embedding = np.array([1.0, 2.0, 3.0])
        
        result = await controller.determine_optimal_k(
            query, query_embedding, mock_qdrant_service
        )
        
        assert isinstance(result, RetrievalResult)
        assert result.query_complexity == QueryComplexity.SIMPLE
        assert result.k_used >= controller.params.k_min
        assert result.k_used <= controller.params.k_max
        assert len(result.chunks) == result.k_used
        assert result.total_tokens > 0
        assert 0.0 <= result.coverage_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_determine_optimal_k_complex_query(self, controller, mock_qdrant_service):
        """Test dynamic-k for complex query."""
        query = "Compare and contrast the advantages and disadvantages of machine learning versus traditional programming approaches"
        query_embedding = np.array([1.0, 2.0, 3.0])
        
        result = await controller.determine_optimal_k(
            query, query_embedding, mock_qdrant_service
        )
        
        assert result.query_complexity == QueryComplexity.COMPLEX
        # Complex queries should tend to use more chunks
        assert result.k_used >= 3
    
    @pytest.mark.asyncio
    async def test_budget_constraint(self, mock_qdrant_service):
        """Test that retrieval respects token budget."""
        # Set very low budget
        params = RetrievalParams(k_min=2, k_max=10, budget_tokens=10)
        controller = DynamicKController(params)
        
        query = "Test query"
        query_embedding = np.array([1.0, 2.0, 3.0])
        
        result = await controller.determine_optimal_k(
            query, query_embedding, mock_qdrant_service
        )
        
        assert result.total_tokens <= params.budget_tokens
        assert result.stop_reason in ["budget_exceeded", "no_results"]
    
    @pytest.mark.asyncio
    async def test_no_results(self, controller):
        """Test handling when no results are found."""
        mock_service = AsyncMock()
        mock_service.search_similar.return_value = []
        
        query = "Non-existent query"
        query_embedding = np.array([1.0, 2.0, 3.0])
        
        result = await controller.determine_optimal_k(
            query, query_embedding, mock_service
        )
        
        assert result.k_used == 0
        assert len(result.chunks) == 0
        assert result.stop_reason == "no_results"
    
    def test_marginal_gain_calculation(self, controller):
        """Test marginal gain calculation."""
        previous_chunks = [
            ChunkResult("1", "doc1", "1", "text1", 0.9, 10, 0, {}),
            ChunkResult("2", "doc1", "2", "text2", 0.8, 10, 1, {})
        ]
        
        current_chunks = previous_chunks + [
            ChunkResult("3", "doc2", "1", "text3", 0.7, 10, 0, {})
        ]
        
        gain = controller._calculate_marginal_gain(previous_chunks, current_chunks)
        assert 0.0 <= gain <= 1.0
        
        # No gain when no new chunks
        no_gain = controller._calculate_marginal_gain(current_chunks, current_chunks)
        assert no_gain == 0.0
    
    def test_trim_to_budget(self, controller):
        """Test trimming chunks to fit budget."""
        chunks = [
            ChunkResult("1", "doc1", "1", "text1", 0.9, 50, 0, {}),
            ChunkResult("2", "doc1", "2", "text2", 0.8, 40, 1, {}),
            ChunkResult("3", "doc2", "1", "text3", 0.7, 30, 0, {}),
            ChunkResult("4", "doc2", "2", "text4", 0.6, 20, 1, {})
        ]
        
        trimmed = controller._trim_to_budget(chunks, 80)
        
        total_tokens = sum(chunk.token_count for chunk in trimmed)
        assert total_tokens <= 80
        
        # Should prioritize higher scoring chunks
        if len(trimmed) > 1:
            assert trimmed[0].score >= trimmed[-1].score


class TestRetrievalEngine:
    """Test the main retrieval engine."""
    
    @pytest.fixture
    def engine(self):
        """Create retrieval engine instance."""
        return RetrievalEngine('balanced')
    
    def test_engine_initialization(self, engine):
        """Test engine initialization with different profiles."""
        assert engine.profile == 'balanced'
        assert engine.params.k_min == 3
        assert engine.params.k_max == 10
        assert engine.params.budget_tokens == 4000
        
        # Test eco profile
        eco_engine = RetrievalEngine('eco')
        assert eco_engine.params.budget_tokens == 2000
        assert eco_engine.params.k_max == 6
        
        # Test performance profile
        perf_engine = RetrievalEngine('performance')
        assert perf_engine.params.budget_tokens == 8000
        assert perf_engine.params.k_max == 12
        assert perf_engine.params.rerank is True
    
    @pytest.mark.asyncio
    async def test_retrieve_for_query_success(self, engine):
        """Test successful query retrieval."""
        query = "What is machine learning?"
        
        # Mock dependencies
        with patch('app.retrieval.embed_query') as mock_embed:
            with patch('app.retrieval.get_qdrant_service') as mock_qdrant:
                mock_embed.return_value = np.array([1.0, 2.0, 3.0])
                
                mock_service = AsyncMock()
                mock_service.search_similar.return_value = [
                    {
                        'id': 'chunk1', 'doc_id': 'doc1', 'chunk_id': '1',
                        'text': 'Machine learning explanation', 'score': 0.9,
                        'token_count': 5, 'chunk_index': 0, 'metadata': {}
                    }
                ]
                mock_qdrant.return_value = mock_service
                
                result = await engine.retrieve_for_query(query)
                
                assert isinstance(result, RetrievalResult)
                assert result.k_used > 0
                assert len(result.chunks) == result.k_used
                assert result.retrieval_time > 0
    
    @pytest.mark.asyncio
    async def test_retrieve_for_query_with_filter(self, engine):
        """Test query retrieval with document filter."""
        query = "Test query"
        doc_filter = ["doc1", "doc2"]
        
        with patch('app.retrieval.embed_query') as mock_embed:
            with patch('app.retrieval.get_qdrant_service') as mock_qdrant:
                mock_embed.return_value = np.array([1.0, 2.0, 3.0])
                
                mock_service = AsyncMock()
                mock_service.search_similar.return_value = []
                mock_qdrant.return_value = mock_service
                
                result = await engine.retrieve_for_query(query, doc_filter=doc_filter)
                
                # Verify filter was passed to search
                mock_service.search_similar.assert_called()
                call_args = mock_service.search_similar.call_args
                assert call_args[1]['doc_filter'] == doc_filter
    
    @pytest.mark.asyncio
    async def test_retrieve_for_query_custom_params(self, engine):
        """Test query retrieval with custom parameters."""
        query = "Test query"
        custom_params = {"k_max": 15, "budget_tokens": 5000}
        
        with patch('app.retrieval.embed_query') as mock_embed:
            with patch('app.retrieval.get_qdrant_service') as mock_qdrant:
                mock_embed.return_value = np.array([1.0, 2.0, 3.0])
                
                mock_service = AsyncMock()
                mock_service.search_similar.return_value = []
                mock_qdrant.return_value = mock_service
                
                result = await engine.retrieve_for_query(query, custom_params=custom_params)
                
                assert isinstance(result, RetrievalResult)
    
    @pytest.mark.asyncio
    async def test_retrieve_for_query_error_handling(self, engine):
        """Test error handling in retrieval."""
        query = "Test query"
        
        with patch('app.retrieval.embed_query', side_effect=Exception("Embedding error")):
            result = await engine.retrieve_for_query(query)
            
            assert result.k_used == 0
            assert len(result.chunks) == 0
            assert result.stop_reason == "error"
            assert "error" in result.stats


@pytest.mark.asyncio
async def test_get_retrieval_engine():
    """Test getting global retrieval engine instance."""
    with patch('app.retrieval.get_settings') as mock_settings:
        mock_settings.return_value.performance_profile = 'eco'
        
        engine1 = await get_retrieval_engine()
        engine2 = await get_retrieval_engine()
        
        # Should return same instance
        assert engine1 is engine2
        assert engine1.profile == 'eco'


@pytest.mark.asyncio
async def test_get_retrieval_engine_profile_change():
    """Test getting retrieval engine with profile change."""
    with patch('app.retrieval.get_settings') as mock_settings:
        mock_settings.return_value.performance_profile = 'balanced'
        
        # Get first instance
        engine1 = await get_retrieval_engine('eco')
        assert engine1.profile == 'eco'
        
        # Get with different profile - should create new instance
        engine2 = await get_retrieval_engine('performance')
        assert engine2.profile == 'performance'
        assert engine1 is not engine2


class TestRetrievalParams:
    """Test retrieval parameters."""
    
    def test_default_params(self):
        """Test default parameter values."""
        params = RetrievalParams()
        
        assert params.k_min == 3
        assert params.k_max == 10
        assert params.score_threshold == 0.7
        assert params.epsilon_gain == 0.05
        assert params.coverage_threshold == 0.85
        assert params.budget_tokens == 4000
        assert params.rerank is False
        assert params.diversity_penalty == 0.1
    
    def test_custom_params(self):
        """Test custom parameter initialization."""
        params = RetrievalParams(
            k_min=5,
            k_max=15,
            budget_tokens=8000,
            rerank=True
        )
        
        assert params.k_min == 5
        assert params.k_max == 15
        assert params.budget_tokens == 8000
        assert params.rerank is True


class TestChunkResult:
    """Test chunk result data structure."""
    
    def test_chunk_result_creation(self):
        """Test creating chunk result."""
        chunk = ChunkResult(
            id="test_id",
            doc_id="doc123",
            chunk_id="chunk456", 
            text="Test chunk text",
            score=0.85,
            token_count=10,
            chunk_index=0,
            metadata={"source": "page1"}
        )
        
        assert chunk.id == "test_id"
        assert chunk.doc_id == "doc123"
        assert chunk.chunk_id == "chunk456"
        assert chunk.text == "Test chunk text"
        assert chunk.score == 0.85
        assert chunk.token_count == 10
        assert chunk.chunk_index == 0
        assert chunk.metadata == {"source": "page1"}
        assert chunk.rerank_score is None
