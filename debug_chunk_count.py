#!/usr/bin/env python3
"""
Debug the chunk counting method specifically
"""

import asyncio
import sys
import os

# Add the backend app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.qdrant_index import get_qdrant_service

async def test_chunk_counting():
    """Test the chunk counting method for specific documents"""
    
    print("🔍 CHUNK COUNTING DEBUG TEST")
    print("=" * 50)
    
    try:
        # Get Qdrant service
        qdrant = await get_qdrant_service()
        print("✅ Qdrant service initialized")
        
        # Test documents we know exist
        test_docs = [
            "278a3ac2-1e36-4efd-a263-e410a41a6722",  # technical_doc.md
            "7aaf1077-d856-491f-8eba-12eea124b890",  # recipe.txt
            "49408d1e-a249-4c28-b4ed-ec9eb6e4d10c",  # test_simple.txt
        ]
        
        for doc_id in test_docs:
            print(f"\n📊 Testing document: {doc_id}")
            
            # Use our chunk counting method
            count = await qdrant.get_document_chunk_count(doc_id)
            print(f"   get_document_chunk_count(): {count}")
            
            # Manual count using scroll
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: qdrant.client.scroll(
                    collection_name=qdrant.COLLECTION_NAME,
                    limit=1000,
                    with_payload=True,
                    with_vectors=False
                )
            )
            
            points, _ = result
            manual_count = 0
            for point in points:
                if (hasattr(point, 'payload') and 
                    point.payload and 
                    point.payload.get('doc_id') == doc_id):
                    manual_count += 1
                    print(f"   Found chunk: {point.payload.get('chunk_id', 'unknown')}")
            
            print(f"   Manual count: {manual_count}")
            
            if count != manual_count:
                print(f"   ⚠️ MISMATCH: API count={count}, actual count={manual_count}")
            else:
                print(f"   ✅ Counts match!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chunk_counting())
