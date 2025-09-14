#!/usr/bin/env python3
"""Debug script to check Qdrant database contents"""

import os
import sys
sys.path.append('/Users/alberto/projects/RAG_APP/backend')

try:
    from app.settings import get_settings
    
    # Get settings
    settings = get_settings()
    print(f"Qdrant path: {settings.qdrant_path}")
    print(f"Data dir: {settings.data_dir}")
    
    # Try to check the vector database directly
    from qdrant_client import QdrantClient
    import time
    
    # Wait a moment to avoid conflicts
    time.sleep(2)
    
    # Create a separate client instance
    client = QdrantClient(path=settings.qdrant_data_dir)
    
    try:
        collections = client.get_collections()
        print(f"Collections: {[c.name for c in collections.collections]}")
        
        if 'rag_documents' in [c.name for c in collections.collections]:
            collection_info = client.get_collection('rag_documents')
            print(f"Vector count: {collection_info.vectors_count}")
            
            if collection_info.vectors_count > 0:
                # Get a sample of points
                scroll_result = client.scroll('rag_documents', limit=3, with_payload=True)
                points = scroll_result[0]
                print(f"Sample points: {len(points)}")
                for i, point in enumerate(points):
                    print(f"  Point {i+1}: {point.payload.get('filename', 'unknown')}")
            else:
                print("No vectors found in collection!")
        else:
            print("rag_documents collection not found!")
            
    except Exception as e:
        print(f"Error accessing collection: {e}")
        
    finally:
        client.close()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()