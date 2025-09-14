#!/usr/bin/env python3
"""
Debug script to check if chunks are being stored in Qdrant
"""

import asyncio
import sys
import os

# Add the backend app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.qdrant_index import get_qdrant_service

async def test_qdrant_storage():
    """Test if chunks are actually stored in Qdrant"""
    
    print("🔍 QDRANT STORAGE DEBUG TEST")
    print("=" * 50)
    
    try:
        # Get Qdrant service
        qdrant = await get_qdrant_service()
        print("✅ Qdrant service initialized")
        
        # Get collection stats
        stats = await qdrant.get_collection_stats()
        print(f"📊 Collection stats: {stats}")
        
        # Try to get all points to see what's stored
        if qdrant.client:
            loop = asyncio.get_event_loop()
            
            # Get all points in the collection
            result = await loop.run_in_executor(
                None,
                lambda: qdrant.client.scroll(
                    collection_name=qdrant.COLLECTION_NAME,
                    limit=100,
                    with_payload=True,
                    with_vectors=False
                )
            )
            
            points, _ = result
            print(f"📊 Total points in collection: {len(points)}")
            
            # Show details of first few points
            for i, point in enumerate(points[:5]):
                doc_id = point.payload.get('doc_id', 'unknown') if point.payload else 'no_payload'
                chunk_id = point.payload.get('chunk_id', 'unknown') if point.payload else 'no_payload'
                text_preview = (point.payload.get('text', '')[:100] + '...') if point.payload and point.payload.get('text') else 'no_text'
                print(f"   Point {i+1}: doc_id={doc_id}, chunk_id={chunk_id}")
                print(f"            Text: {text_preview}")
            
            # Count chunks by document ID
            doc_counts = {}
            for point in points:
                if point.payload and 'doc_id' in point.payload:
                    doc_id = point.payload['doc_id']
                    doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
            
            print(f"\n📊 Chunks per document:")
            for doc_id, count in doc_counts.items():
                print(f"   {doc_id}: {count} chunks")
                
        else:
            print("❌ Qdrant client not available")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qdrant_storage())
