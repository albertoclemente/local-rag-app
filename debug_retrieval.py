#!/usr/bin/env python3
"""
Debug script to test Qdrant retrieval step by step
"""

print("Starting debug script...")

import asyncio
import sys
from pathlib import Path

print(f"Python path: {sys.path}")

# Add backend to path
backend_path = str(Path(__file__).parent / "backend")
print(f"Adding backend path: {backend_path}")
sys.path.insert(0, backend_path)

print("Importing modules...")
from app.qdrant_index import get_qdrant_service
from app.embeddings import embed_query
from app.retrieval import get_retrieval_service
print("Modules imported successfully")

async def debug_retrieval():
    """Debug the retrieval pipeline step by step"""
    
    print("🔍 Debug: Testing Qdrant retrieval pipeline")
    
    try:
        # Test 1: Get Qdrant service
        print("\n1. Getting Qdrant service...")
        qdrant_service = await get_qdrant_service()
        print(f"✅ Qdrant service initialized")
        
        # Test 2: Check if collection exists
        print("\n2. Checking collection...")
        try:
            # Try to get collection info
            collection_info = await qdrant_service.client.get_collection("documents")
            print(f"✅ Collection 'documents' exists")
            print(f"   Points count: {collection_info.points_count}")
            print(f"   Vector size: {collection_info.config.params.vectors.size}")
        except Exception as e:
            print(f"❌ Collection issue: {e}")
            return
        
        # Test 3: Test embedding generation
        print("\n3. Testing embedding generation...")
        query = "What is machine learning?"
        print(f"   Query: {query}")
        
        query_embedding = await embed_query(query)
        print(f"✅ Generated embedding, shape: {query_embedding.shape}")
        
        # Test 4: Test raw Qdrant search
        print("\n4. Testing raw Qdrant search...")
        raw_results = await qdrant_service.search_similar(
            query_embedding, 
            k=5, 
            score_threshold=0.1  # Very low threshold to see any results
        )
        print(f"✅ Raw search returned {len(raw_results)} results")
        
        for i, result in enumerate(raw_results):
            print(f"   {i+1}. ID: {result.id}, Score: {result.score:.3f}")
            print(f"       Text: {result.text[:100]}...")
        
        # Test 5: Test full retrieval service
        print("\n5. Testing full retrieval service...")
        retrieval_service = await get_retrieval_service()
        retrieval_result = await retrieval_service.retrieve_for_query(query)
        
        print(f"✅ Retrieval service returned {len(retrieval_result.chunks)} chunks")
        print(f"   Coverage score: {retrieval_result.coverage_score:.3f}")
        print(f"   Query complexity: {retrieval_result.query_complexity}")
        
        for i, chunk in enumerate(retrieval_result.chunks):
            print(f"   {i+1}. Doc: {chunk.doc_id}, Score: {chunk.score:.3f}")
            print(f"       Text: {chunk.text[:100]}...")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_retrieval())
