#!/usr/bin/env python3
"""Debug Qdrant collection configuration to understand vector field names."""

import asyncio
from app.qdrant_index import QdrantIndex

async def debug_collection():
    """Debug collection configuration."""
    print("🔍 QDRANT COLLECTION DEBUG")
    print("=" * 50)
    
    try:
        # Initialize Qdrant
        qdrant = QdrantIndex()
        await qdrant.initialize()
        
        # Get detailed collection info
        print("1. Getting collection information...")
        loop = asyncio.get_event_loop()
        collection_info = await loop.run_in_executor(
            None,
            qdrant.client.get_collection,
            qdrant.COLLECTION_NAME
        )
        
        print(f"   Collection: {qdrant.COLLECTION_NAME}")
        print(f"   Status: {collection_info.status}")
        print(f"   Optimizer status: {collection_info.optimizer_status}")
        print(f"   Vectors config: {collection_info.config.params.vectors}")
        print(f"   Collection config: {collection_info.config}")
        
        # Try to get vector names
        if hasattr(collection_info.config.params, 'vectors'):
            vectors_config = collection_info.config.params.vectors
            print(f"   Vectors type: {type(vectors_config)}")
            print(f"   Vectors: {vectors_config}")
            if hasattr(vectors_config, '__dict__'):
                print(f"   Vectors dict: {vectors_config.__dict__}")
            if hasattr(vectors_config, 'size'):
                print(f"   Vector size: {vectors_config.size}")
            if hasattr(vectors_config, 'distance'):
                print(f"   Vector distance: {vectors_config.distance}")
        
        # Get points count
        count_result = await loop.run_in_executor(
            None,
            qdrant.client.count,
            qdrant.COLLECTION_NAME
        )
        print(f"   Points count: {count_result.count}")
        
        # Try to scroll some points to see their structure
        print("\n2. Examining point structure...")
        scroll_result = await loop.run_in_executor(
            None,
            lambda: qdrant.client.scroll(
                collection_name=qdrant.COLLECTION_NAME,
                limit=1
            )
        )
        
        points, _ = scroll_result
        if points:
            point = points[0]
            print(f"   Point ID: {point.id}")
            print(f"   Point vector type: {type(point.vector)}")
            print(f"   Point vector keys: {list(point.vector.keys()) if hasattr(point.vector, 'keys') else 'not dict'}")
            print(f"   Point payload: {point.payload}")
        else:
            print("   No points found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_collection())
