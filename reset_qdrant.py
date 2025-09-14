#!/usr/bin/env python3
"""
Reset Qdrant collection with correct configuration
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append('backend')

from app.qdrant_index import get_qdrant_service

async def reset_qdrant():
    print("🔄 RESETTING QDRANT COLLECTION")
    print("=" * 40)
    
    try:
        # Get Qdrant service
        print("1. Getting Qdrant service...")
        qdrant_service = await get_qdrant_service()
        
        # Delete existing collection
        print("2. Deleting existing collection...")
        try:
            await qdrant_service.client.delete_collection(qdrant_service.COLLECTION_NAME)
            print("   ✅ Collection deleted")
        except Exception as e:
            print(f"   ⚠️ Error deleting collection (might not exist): {e}")
        
        # Reset the service state
        qdrant_service.collection_exists = False
        
        # Recreate collection
        print("3. Recreating collection...")
        await qdrant_service._ensure_collection()
        
        # Check new collection stats
        print("4. Checking new collection...")
        stats = await qdrant_service.get_collection_stats()
        print(f"   New collection stats: {stats}")
        
        print("✅ Qdrant collection reset successfully!")
        
    except Exception as e:
        print(f"❌ Error resetting Qdrant: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reset_qdrant())
