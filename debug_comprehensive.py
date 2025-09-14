#!/usr/bin/env python3
"""
Comprehensive debug of the retrieval pipeline
"""

import requests
import json
import time

def debug_retrieval_pipeline():
    """Debug the entire retrieval pipeline step by step"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    print("🔍 COMPREHENSIVE RETRIEVAL DEBUG")
    print("=" * 50)
    
    # Step 1: Check backend health
    print("\n1. 🏥 Backend Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Step 2: Upload a fresh document
    print("\n2. 📤 Upload Fresh Document")
    try:
        with open('test_documents/technical_doc.md', 'rb') as f:
            files = {'file': ('fresh_debug.md', f, 'text/markdown')}
            response = requests.post(f"{BASE_URL}/api/documents", files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            doc_info = data.get('document', {})
            doc_id = doc_info.get('id')
            print(f"✅ Document uploaded: {doc_id}")
            print(f"   Status: {doc_info.get('status')}")
            print(f"   Embedding status: {doc_info.get('embedding_status')}")
            
            # Wait for processing if needed
            if doc_info.get('embedding_status') != 'indexed':
                print("⏳ Waiting for indexing...")
                time.sleep(5)
                
                # Check status again
                doc_response = requests.get(f"{BASE_URL}/api/documents")
                if doc_response.status_code == 200:
                    docs = doc_response.json().get('documents', [])
                    doc = next((d for d in docs if d['id'] == doc_id), None)
                    if doc:
                        print(f"   Updated status: {doc.get('status')} / {doc.get('embedding_status')}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return
    
    # Step 3: Test different queries with different complexities
    print("\n3. 🔍 Test Multiple Queries")
    
    test_queries = [
        "machine learning",  # Simple, should definitely match
        "pipeline",          # Single word from document  
        "implementation",    # Another word from document
        "architecture",      # Another word from document
        "what is machine learning pipeline?",  # Question format
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n3.{i} Testing query: '{query}'")
        
        try:
            # Make a simple search request to see if we can get any results
            search_payload = {"query": query, "limit": 3}
            search_response = requests.post(f"{BASE_URL}/api/search", json=search_payload, timeout=10)
            
            if search_response.status_code == 200:
                results = search_response.json()
                print(f"   📊 Search API returned: {len(results.get('results', []))} results")
                if results.get('results'):
                    for j, result in enumerate(results['results'][:2]):
                        print(f"      {j+1}. Score: {result.get('score', 'N/A'):.3f}")
                        print(f"         Text: {result.get('content', '')[:60]}...")
            elif search_response.status_code == 404:
                print("   ⚠️ Search API endpoint not found - this is expected")
            else:
                print(f"   ❌ Search API error: {search_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Search test error: {e}")
        
        # Test via WebSocket streaming
        try:
            session_id = f"debug-session-{i}"
            query_data = {"query": query, "sessionId": session_id}
            
            query_response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=10)
            if query_response.status_code == 200:
                query_result = query_response.json()
                turn_id = query_result.get('turnId')
                print(f"   ✅ Query started, turn_id: {turn_id}")
                
                # Note: We won't test WebSocket here to keep it simple
                # The issue is likely in the retrieval service itself
                
            else:
                print(f"   ❌ Query start failed: {query_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Query test error: {e}")
        
        # Short break between queries
        time.sleep(1)
    
    # Step 4: Check document content
    print("\n4. 📄 Document Content Analysis")
    try:
        with open('test_documents/technical_doc.md', 'r') as f:
            content = f.read()
            print(f"   Document length: {len(content)} characters")
            print(f"   Contains 'machine learning': {'machine learning' in content.lower()}")
            print(f"   Contains 'pipeline': {'pipeline' in content.lower()}")
            print(f"   Contains 'implementation': {'implementation' in content.lower()}")
            print(f"   First 200 chars: {content[:200]}...")
    except Exception as e:
        print(f"   ❌ Content check error: {e}")
    
    # Step 5: Summary
    print("\n5. 📋 Summary")
    print("   If all steps above worked but retrieval_chunks=0 in WebSocket,")
    print("   the issue is likely in the Qdrant search or retrieval service.")
    print("   Check:")
    print("   - Vector dimensions match between embeddings and Qdrant")
    print("   - Qdrant collection actually contains vectors") 
    print("   - Score thresholds aren't too restrictive")
    print("   - Embedding generation is working correctly")

if __name__ == "__main__":
    debug_retrieval_pipeline()
