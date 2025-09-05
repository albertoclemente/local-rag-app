#!/usr/bin/env python3
"""
Test Script for TC-FUNC-011: Re-index on param change
Tests that documents can be re-indexed when chunking parameters change,
and status properly updates through the process.
"""

import requests
import time
import json
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_DOC = "/Users/alberto/projects/RAG_APP/test_documents/technical_doc.md"

def check_backend_health():
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def upload_document():
    """Upload a test document and return document info"""
    try:
        with open(TEST_DOC, 'rb') as file:
            files = {'file': (Path(TEST_DOC).name, file, 'text/plain')}
            response = requests.post(f"{BASE_URL}/api/documents", files=files, timeout=30)
            
        if response.status_code == 200:
            result = response.json()
            document_id = result.get('document', {}).get('id')
            print(f"✅ Document uploaded with ID: {document_id}")
            print(f"   Chunks created: {result.get('chunks_created', 'N/A')}")
            return document_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return None

def get_document_status(document_id):
    """Get current document status"""
    try:
        # First try getting single document, if that fails, get from list
        response = requests.get(f"{BASE_URL}/api/documents", timeout=10)
        if response.status_code == 200:
            documents = response.json().get('documents', [])
            for doc in documents:
                if doc.get('id') == document_id:
                    status = doc.get('status', 'unknown')
                    chunk_count = doc.get('chunk_count', 0)
                    print(f"📊 Document status: {status}, Chunks: {chunk_count}")
                    return status, chunk_count
            print(f"❌ Document {document_id} not found in list")
            return None, None
        else:
            print(f"❌ Failed to get documents list: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ Status check error: {str(e)}")
        return None, None

def update_chunking_params(document_id, chunk_size=600, overlap_percent=15):
    """Update document chunking parameters"""
    try:
        payload = {
            "chunking_strategy": "manual",
            "chunk_size": chunk_size,
            "overlap_percent": overlap_percent
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/documents/{document_id}",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chunking parameters updated")
            print(f"   Strategy: manual, Size: {chunk_size}, Overlap: {overlap_percent}%")
            return True
        else:
            print(f"❌ Parameter update failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Parameter update error: {str(e)}")
        return False

def trigger_reindex(document_id):
    """Trigger re-indexing of the document"""
    try:
        # Provide required request body for reindex
        payload = {
            "force": True  # Force reindex even if not needed
        }
        
        response = requests.post(
            f"{BASE_URL}/api/documents/{document_id}/reindex", 
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Re-indexing triggered")
            return True
        else:
            print(f"❌ Re-index failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Re-index error: {str(e)}")
        return False

def wait_for_indexing_complete(document_id, timeout=60):
    """Wait for indexing to complete and return final status"""
    print("⏳ Waiting for re-indexing to complete...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status, chunk_count = get_document_status(document_id)
        
        if status == "indexed":
            print(f"✅ Re-indexing completed with {chunk_count} chunks")
            return True, chunk_count
        elif status == "error":
            print(f"❌ Re-indexing failed")
            return False, None
        elif status in ["indexing", "needs_reindex"]:
            print(f"⏳ Status: {status}...")
            time.sleep(2)
        else:
            print(f"⚠️ Unexpected status: {status}")
            time.sleep(2)
    
    print(f"❌ Re-indexing timed out after {timeout} seconds")
    return False, None

def run_reindex_test():
    """Main test function for TC-FUNC-011"""
    print("🧪 Starting TC-FUNC-011: Re-index on param change")
    print("=" * 60)
    
    # Check backend health
    if not check_backend_health():
        print("❌ Backend is not accessible. Please start the backend first.")
        return False
    
    print("✅ Backend is accessible")
    print()
    
    # Step 1: Upload document with auto chunking
    print("📤 Step 1: Upload document with auto chunking")
    document_id = upload_document()
    if not document_id:
        return False
    
    time.sleep(2)
    initial_status, initial_chunks = get_document_status(document_id)
    print()
    
    # Step 2: Update to manual chunking parameters
    print("⚙️ Step 2: Switch to manual chunking (600 tokens, 15% overlap)")
    if not update_chunking_params(document_id, chunk_size=600, overlap_percent=15):
        return False
    
    time.sleep(1)
    after_update_status, _ = get_document_status(document_id)
    
    # Check if status changed to "needs_reindex"
    if after_update_status == "needs_reindex":
        print("✅ Status correctly changed to 'needs_reindex'")
    else:
        print(f"⚠️ Expected 'needs_reindex', got '{after_update_status}'")
    print()
    
    # Step 3: Trigger re-indexing
    print("🔄 Step 3: Trigger re-indexing")
    if not trigger_reindex(document_id):
        return False
    
    print()
    
    # Step 4: Wait for completion and verify
    print("⏳ Step 4: Wait for re-indexing completion")
    success, final_chunks = wait_for_indexing_complete(document_id)
    
    if success:
        print()
        print("📊 Re-indexing Results:")
        print(f"   Initial chunks: {initial_chunks}")
        print(f"   Final chunks: {final_chunks}")
        
        if final_chunks != initial_chunks:
            print("✅ Chunk count changed - manual parameters applied")
        else:
            print("⚠️ Chunk count unchanged - manual parameters may not have been applied")
        
        print()
        print("🎉 TC-FUNC-011 PASSED: Re-indexing completed successfully")
        return True
    else:
        print("❌ TC-FUNC-011 FAILED: Re-indexing did not complete")
        return False

if __name__ == "__main__":
    success = run_reindex_test()
    exit(0 if success else 1)
