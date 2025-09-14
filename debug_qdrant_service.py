#!/usr/bin/env python3
"""Test Qdrant service directly"""

import asyncio
import sys
sys.path.append('/Users/alberto/projects/RAG_APP/backend')

async def test_qdrant_service():
    try:
        from app.qdrant_index import get_qdrant_service
        from app.embeddings import embed_query
        
        # Get the service 
        qdrant_service = await get_qdrant_service()
        print(f"✅ Got Qdrant service: {type(qdrant_service)}")
        
        # Test embedding generation
        query = "What have we learned from building with LLMs?"
        query_embedding = await embed_query(query)
        print(f"✅ Generated embedding with shape: {query_embedding.shape}")
        
        # Try a direct search
        print(f"🔍 Attempting direct vector search...")
        results = await qdrant_service.search_similar(
            query_embedding,
            limit=5,
            score_threshold=0.1  # Very low threshold
        )
        
        print(f"📊 Search results: {len(results) if results else 0} chunks found")
        
        if results:
            for i, result in enumerate(results[:3]):
                print(f"  Result {i+1}: score={result.score:.3f}, doc={result.metadata.get('filename', 'unknown')}")
                print(f"    Text preview: {result.content[:100]}...")
        else:
            print("⚠️  No results found - this is the problem!")
            
            # Check if collection exists
            try:
                import asyncio
                await asyncio.sleep(1)  # Let qdrant service stabilize
                
                # Try to check the collection directly
                print("🔍 Checking collection status...")
                
                # Use the internal client if available
                if hasattr(qdrant_service, 'client'):
                    collections = qdrant_service.client.get_collections()
                    print(f"Collections: {[c.name for c in collections.collections]}")
                    
                    if 'rag_documents' in [c.name for c in collections.collections]:
                        collection_info = qdrant_service.client.get_collection('rag_documents')
                        print(f"Vector count in collection: {collection_info.vectors_count}")
                    else:
                        print("❌ rag_documents collection not found!")
                        
            except Exception as e:
                print(f"Error checking collection: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qdrant_service())