#!/usr/bin/env python3
"""
Debug script to test chunking process directly
"""

import asyncio
import sys
import os

# Add the backend app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.chunking import AdaptiveChunker
from app.models import DocumentType

async def test_chunking():
    """Test the chunking process with sample text"""
    
    # Test text that should definitely be chunked
    test_text = """This is a comprehensive test document designed to force chunking behavior in the RAG system.

SECTION 1: INTRODUCTION
This section contains substantial content that should definitely be split into multiple chunks during processing. The chunking algorithm should recognize this as separate content blocks that need to be processed independently for optimal retrieval performance.

SECTION 2: TECHNICAL DETAILS
Here we provide extensive technical information that spans multiple paragraphs and should result in several distinct chunks. The content is sufficiently large and diverse to trigger the adaptive chunking mechanisms built into the system.

This paragraph continues the technical section with additional details about implementation specifics, configuration parameters, and operational considerations that would typically be separated during the chunking process.

SECTION 3: METHODOLOGY
The methodology section describes the approach taken for testing and validation. It includes step-by-step procedures, validation criteria, and expected outcomes that should be chunked separately for effective information retrieval.

Furthermore, this section contains subsections with detailed explanations of various testing scenarios, edge cases, and performance benchmarks that demonstrate the system's capabilities under different conditions.

SECTION 4: RESULTS AND ANALYSIS
This final section presents comprehensive results from testing activities. The analysis covers performance metrics, accuracy measurements, and comparative evaluations against baseline systems.

The detailed findings include statistical analysis, trend identification, and recommendations for future improvements. This content should be substantial enough to generate multiple chunks during the indexing process.

CONCLUSION
This document contains approximately 300+ words across multiple distinct sections that should trigger the chunking algorithm to create several separate chunks for optimal retrieval and processing efficiency."""

    print("🔍 CHUNKING DEBUG TEST")
    print("=" * 50)
    print(f"Input text length: {len(test_text)} characters")
    print(f"Estimated words: {len(test_text.split())}")
    print()
    
    # Initialize chunker
    chunker = AdaptiveChunker()
    
    # Test sentence splitting first
    print("1. Testing sentence splitting...")
    sentences = chunker._split_into_sentences(test_text)
    print(f"   Found {len(sentences)} sentences")
    for i, sentence in enumerate(sentences[:5]):  # Show first 5
        print(f"   Sentence {i+1}: {sentence[:100]}...")
    print()
    
    # Test token estimation
    print("2. Testing token estimation...")
    total_tokens = chunker._estimate_tokens(test_text)
    print(f"   Total estimated tokens: {total_tokens}")
    print()
    
    # Test chunking parameters
    print("3. Testing chunking parameters...")
    params = await chunker._determine_chunking_params(
        test_text, {}, DocumentType.TXT
    )
    print(f"   Strategy: {params.strategy}")
    print(f"   Min chunk size: {params.min_chunk_size} tokens")
    print(f"   Max chunk size: {params.max_chunk_size} tokens")
    print(f"   Min overlap: {params.min_overlap_percent}%")
    print()
    
    # Test full chunking
    print("4. Testing full chunking process...")
    try:
        result = await chunker.chunk_document(
            "test_doc_001",
            test_text,
            {},
            DocumentType.TXT
        )
        
        print(f"   ✅ Chunking successful!")
        print(f"   Number of chunks: {len(result.chunks)}")
        print(f"   Rationale: {result.rationale}")
        print(f"   Stats: {result.stats}")
        
        for i, chunk in enumerate(result.chunks):
            print(f"\n   Chunk {i+1} ({len(chunk)} chars, ~{chunker._estimate_tokens(chunk)} tokens):")
            print(f"   {chunk[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Chunking failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chunking())
