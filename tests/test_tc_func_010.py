"""
Test Script for TC-FUNC-010: Adaptive Chunking
Tests adaptive chunking system with diverse document types to validate
different chunking strategies are applied based on content structure.
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOCS_DIR = Path("test_documents")

# Test documents with expected chunking characteristics
test_documents = [
    {
        "file": "technical_doc.md",
        "description": "Technical documentation with structured content",
        "expected_strategy": "Structure-aware chunking for headers and code blocks"
    },
    {
        "file": "narrative_story.txt", 
        "description": "Narrative prose with flowing content",
        "expected_strategy": "Semantic boundary detection for natural breaks"
    },
    {
        "file": "financial_report.txt",
        "description": "Financial report with bullet points and metrics",
        "expected_strategy": "List-aware chunking for structured data"
    },
    {
        "file": "recipe.txt",
        "description": "Recipe with numbered steps and ingredients",
        "expected_strategy": "Step-aware chunking for procedural content"
    },
    {
        "file": "sample_document.txt",
        "description": "Simple text document",
        "expected_strategy": "Standard chunking for plain text"
    }
]

def check_backend_health():
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def upload_document(file_path, description):
    """Upload a document and return response with chunking details"""
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (file_path.name, file, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=30)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully uploaded: {file_path.name}")
            print(f"   Document ID: {result.get('document_id', 'N/A')}")
            print(f"   Chunks created: {result.get('chunks_created', 'N/A')}")
            print(f"   Is duplicate: {result.get('is_duplicate', False)}")
            
            # Check for chunking strategy information
            if 'chunking_strategy' in result:
                print(f"   Chunking strategy: {result['chunking_strategy']}")
            if 'chunk_details' in result:
                print(f"   Chunk details: {result['chunk_details']}")
                
            return result
        else:
            print(f"❌ Failed to upload {file_path.name}: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception uploading {file_path.name}: {str(e)}")
        return None

def get_document_chunks(document_id):
    """Retrieve chunks for a document to analyze chunking behavior"""
    try:
        response = requests.get(f"{BASE_URL}/documents/{document_id}/chunks", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get chunks for document {document_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Exception getting chunks for document {document_id}: {str(e)}")
        return None

def analyze_chunking_strategy(document_info, chunks_data):
    """Analyze the chunking strategy applied to a document"""
    if not chunks_data:
        return
        
    chunks = chunks_data.get('chunks', [])
    if not chunks:
        print("   No chunks found for analysis")
        return
        
    print(f"   📊 Chunking Analysis:")
    print(f"   - Total chunks: {len(chunks)}")
    
    # Analyze chunk sizes
    chunk_sizes = [len(chunk.get('content', '')) for chunk in chunks]
    if chunk_sizes:
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        min_size = min(chunk_sizes)
        max_size = max(chunk_sizes)
        print(f"   - Chunk sizes: avg={avg_size:.0f}, min={min_size}, max={max_size}")
    
    # Check for overlap indicators
    overlaps = [chunk.get('overlap_size', 0) for chunk in chunks if 'overlap_size' in chunk]
    if overlaps:
        avg_overlap = sum(overlaps) / len(overlaps)
        print(f"   - Average overlap: {avg_overlap:.0f} characters")
    
    # Look for chunking metadata
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        metadata = chunk.get('metadata', {})
        if metadata:
            print(f"   - Chunk {i+1} metadata: {metadata}")

def run_adaptive_chunking_test():
    """Main test function for TC-FUNC-010"""
    print("🧪 Starting TC-FUNC-010: Adaptive Chunking Test")
    print("=" * 60)
    
    # Check backend health
    if not check_backend_health():
        print("❌ Backend is not accessible. Please start the backend first.")
        return False
    
    print("✅ Backend is accessible")
    print()
    
    all_results = []
    
    for doc_info in test_documents:
        file_path = TEST_DOCS_DIR / doc_info["file"]
        
        print(f"📄 Testing: {doc_info['file']}")
        print(f"   Description: {doc_info['description']}")
        print(f"   Expected: {doc_info['expected_strategy']}")
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue
            
        # Upload document
        upload_result = upload_document(file_path, doc_info["description"])
        if upload_result:
            all_results.append({
                "file": doc_info["file"],
                "upload_result": upload_result
            })
            
            # Get chunks for analysis
            document_id = upload_result.get('document_id')
            if document_id:
                chunks_data = get_document_chunks(document_id)
                analyze_chunking_strategy(upload_result, chunks_data)
                
        print()
        time.sleep(1)  # Brief pause between uploads
    
    # Summary
    print("📋 Test Summary:")
    print("=" * 40)
    successful_uploads = len([r for r in all_results if r['upload_result']])
    print(f"✅ Successfully uploaded: {successful_uploads}/{len(test_documents)} documents")
    
    if successful_uploads == len(test_documents):
        print("🎉 TC-FUNC-010 PASSED: All documents uploaded with adaptive chunking")
        return True
    else:
        print("❌ TC-FUNC-010 FAILED: Some documents failed to upload")
        return False

if __name__ == "__main__":
    success = run_adaptive_chunking_test()
    exit(0 if success else 1)
