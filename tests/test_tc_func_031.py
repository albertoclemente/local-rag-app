#!/usr/bin/env python3
"""
Test Script for TC-FUNC-031: Citations appear and are clickable
Tests that citations [1], [2], etc. appear in responses and clicking them
shows the source snippet with document name, page/location, and relevance score.
"""

import requests
import time
import json
import sys
import pytest
import websocket
import threading
import uuid
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"
TEST_DOC = "/Users/alberto/projects/RAG_APP/test_documents/technical_doc.md"

def check_backend_health():
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def ensure_document_indexed():
    """Ensure we have at least one indexed document for testing"""
    try:
        # Check if we already have indexed documents
        response = requests.get(f"{BASE_URL}/api/documents", timeout=10)
        if response.status_code == 200:
            result = response.json()
            docs = result.get('documents', [])
            if docs and len(docs) > 0:
                print(f"✅ Found {len(docs)} indexed documents")
                # Find a document that is fully indexed with embeddings
                for doc in docs:
                    if (doc.get('status') == 'indexed' and 
                        doc.get('embedding_status') == 'indexed'):
                        doc_id = doc.get('id')
                        print(f"✅ Using document: {doc.get('name')} ({doc_id})")
                        return True, doc_id
                
                # If no fully indexed document, return first one anyway
                doc_id = docs[0].get('id')
                print(f"⚠️ Using first document (may not be fully indexed): {docs[0].get('name')} ({doc_id})")
                return True, doc_id
                
        # Upload test document if none found
        print("📄 No documents found, uploading test document...")
        if not Path(TEST_DOC).exists():
            print(f"❌ Test document not found: {TEST_DOC}")
            return False, None
            
        with open(TEST_DOC, 'rb') as f:
            files = {'file': (Path(TEST_DOC).name, f, 'text/markdown')}
            response = requests.post(f"{BASE_URL}/api/upload", files=files, timeout=30)
            
        if response.status_code == 201:
            result = response.json()
            doc_id = result.get('id')
            print(f"✅ Document uploaded successfully: {doc_id}")
            
            # Wait for processing
            time.sleep(3)
            return True, doc_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error ensuring document: {e}")
        return False, None

def send_query_and_get_response(query, session_id):
    """Send a query and capture the full response including citations"""
    try:
        # Start query
        query_data = {
            "query": query,
            "session_id": session_id,
            "stream": True
        }
        
        response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=10)
        if response.status_code != 200:
            return False, f"Query start failed: {response.status_code}", None, None
            
        query_response = response.json()
        turn_id = query_response.get('turnId')
        
        # Connect to WebSocket using correct endpoint with query parameters
        ws_url = f"{WS_URL}/ws/stream?session_id={session_id}&turn_id={turn_id}"
        
        messages = []
        citations = []
        sources = []
        response_complete = False
        
        def on_message(ws, message):
            nonlocal response_complete
            try:
                data = json.loads(message)
                event_type = data.get('event', data.get('type'))
                
                if event_type == 'TOKEN':
                    messages.append(data.get('text', ''))
                elif event_type == 'message':
                    messages.append(data.get('content', ''))
                elif event_type == 'CITATION' or event_type == 'citations':
                    citation_data = data.get('citations', [data])
                    citations.extend(citation_data)
                elif event_type == 'sources':
                    sources.extend(data.get('sources', []))
                elif event_type == 'END':
                    # Response complete
                    response_complete = True
                    ws.close()
                elif event_type == 'ERROR':
                    # Error occurred
                    response_complete = True
                    ws.close()
            except Exception as e:
                print(f"Error parsing message: {e}")
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            pass
            
        ws = websocket.WebSocketApp(ws_url,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        
        # Run WebSocket in a thread
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for response to complete (up to 15 seconds)
        wait_time = 0
        while not response_complete and wait_time < 15:
            time.sleep(0.5)
            wait_time += 0.5
        
        if not response_complete:
            ws.close()
        
        full_response = ''.join(messages)
        return True, full_response, citations, sources
        
    except Exception as e:
        return False, f"Error during query: {e}", None, None

def test_citations_in_response():
    """Test that citations appear in query responses"""
    print("\n🧪 TC-FUNC-031: Testing citations appearance and functionality")
    
    # Check backend health
    if not check_backend_health():
        pytest.fail("❌ Backend is not accessible")
    
    # Ensure we have documents to cite
    success, doc_id = ensure_document_indexed()
    if not success:
        pytest.fail("❌ Failed to ensure document is indexed")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Test queries that should generate citations
    test_queries = [
        "What is machine learning?",
        "Explain the key concepts in this document",
        "How does gradient descent work?"
    ]
    
    citation_found = False
    
    for query in test_queries:
        print(f"\n📝 Testing query: '{query}'")
        
        success, response, citations, sources = send_query_and_get_response(query, session_id)
        
        if not success:
            print(f"❌ Query failed: {response}")
            continue
        
        print(f"✅ Got response: {response[:100]}...")
        
        # Debug: print the full response to see what's actually there
        print(f"🔍 Full response: '{response}'")
        print(f"🔍 Response length: {len(response)}")
        
        # Check for citation markers in response
        citation_patterns = ['[1]', '[2]', '[3]', '(1)', '(2)', '(3)']
        found_citations = []
        
        for pattern in citation_patterns:
            if pattern in response:
                found_citations.append(pattern)
                citation_found = True
        
        if found_citations:
            print(f"✅ Found citation markers: {found_citations}")
        
        # Check citations data
        if citations:
            print(f"✅ Received {len(citations)} citations")
            for i, citation in enumerate(citations):
                print(f"   Citation {i+1}: {citation}")
        
        # Check sources data  
        if sources:
            print(f"✅ Received {len(sources)} sources")
            for i, source in enumerate(sources):
                print(f"   Source {i+1}: {source.get('document', 'Unknown')} - Score: {source.get('score', 'N/A')}")
    
    if not citation_found:
        pytest.fail("❌ No citations found in any response")
    
    print("✅ TC-FUNC-031 PASSED: Citations functionality working")

def test_citation_source_details():
    """Test that citation sources contain required information"""
    print("\n🧪 TC-FUNC-031b: Testing citation source details")
    
    # Check backend health
    if not check_backend_health():
        pytest.fail("❌ Backend is not accessible")
    
    # Ensure we have documents
    success, doc_id = ensure_document_indexed()
    if not success:
        pytest.fail("❌ Failed to ensure document is indexed")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Query that should generate citations
    query = "What are the main topics covered in this document?"
    
    success, response, citations, sources = send_query_and_get_response(query, session_id)
    
    if not success:
        pytest.fail(f"❌ Query failed: {response}")
    
    print(f"✅ Got response with {len(sources) if sources else 0} sources")
    
    if not sources:
        pytest.fail("❌ No sources returned with response")
    
    # Validate source structure
    required_fields = ['document', 'content', 'score']
    
    for i, source in enumerate(sources):
        print(f"\n📋 Validating source {i+1}:")
        
        for field in required_fields:
            if field not in source:
                pytest.fail(f"❌ Missing required field '{field}' in source {i+1}")
            
            value = source[field]
            if value is None or (isinstance(value, str) and not value.strip()):
                pytest.fail(f"❌ Empty value for field '{field}' in source {i+1}")
        
        print(f"   ✅ Document: {source['document']}")
        print(f"   ✅ Content: {source['content'][:50]}...")
        print(f"   ✅ Score: {source['score']}")
        
        # Validate score is a number between 0 and 1
        score = source['score']
        if not isinstance(score, (int, float)) or score < 0 or score > 1:
            pytest.fail(f"❌ Invalid score value: {score} (should be 0-1)")
    
    print("✅ TC-FUNC-031b PASSED: Citation source details are complete")

if __name__ == "__main__":
    test_citations_in_response()
    test_citation_source_details()
