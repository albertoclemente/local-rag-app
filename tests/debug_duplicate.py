#!/usr/bin/env python3
"""Debug script to test duplicate detection logic"""

import asyncio
import sys
import os
sys.path.insert(0, '/Users/alberto/projects/RAG_APP/backend')

from app.storage import DocumentStorage
from app.settings import get_settings

async def test_duplicate_logic():
    """Test the duplicate detection logic directly"""
    
    storage = DocumentStorage()
    
    # Test file content
    test_content = b"This is a test document for RAG application.\n\nIt contains sample content for testing duplicate detection.\n\nThe quick brown fox jumps over the lazy dog."
    
    print("=== Testing Duplicate Detection Logic ===")
    
    # Calculate hash
    import hashlib
    sha256_hash = hashlib.sha256()
    sha256_hash.update(test_content)
    file_hash = sha256_hash.hexdigest()
    print(f"File hash: {file_hash}")
    
    # First, check if any existing documents match this hash
    print("\n--- Checking for existing duplicates ---")
    existing = await storage.find_duplicate_by_hash(file_hash)
    if existing:
        print(f"Found existing document: {existing.id} - {existing.name}")
    else:
        print("No existing document found")
    
    # Store the file
    print("\n--- Storing first document ---")
    doc1 = await storage.store_uploaded_file(
        file_content=test_content,
        filename="test_duplicate.txt",
        tags=["test"]
    )
    print(f"Stored document: {doc1.id}")
    
    # Check metadata file was created with hash
    metadata_path = storage._get_document_metadata_path(doc1.id)
    print(f"Metadata path: {metadata_path}")
    
    if metadata_path.exists():
        import json
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print(f"Metadata file hash: {metadata.get('file_hash', 'MISSING')}")
    else:
        print("ERROR: Metadata file not found!")
    
    # Try to find duplicate now
    print("\n--- Checking for duplicate after storage ---")
    duplicate = await storage.find_duplicate_by_hash(file_hash)
    if duplicate:
        print(f"Found duplicate: {duplicate.id} - {duplicate.name}")
    else:
        print("ERROR: Duplicate not found!")
    
    # Try storing again
    print("\n--- Attempting to store duplicate ---")
    doc2 = await storage.store_uploaded_file(
        file_content=test_content,
        filename="test_duplicate_copy.txt",
        tags=["test", "duplicate"]
    )
    print(f"Second storage result: {doc2.id}")
    
    if doc1.id == doc2.id:
        print("✅ SUCCESS: Duplicate detection working - same document returned")
    else:
        print("❌ FAILED: New document created instead of returning existing")

if __name__ == "__main__":
    asyncio.run(test_duplicate_logic())
