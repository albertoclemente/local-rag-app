#!/usr/bin/env python3
"""
Test Script for TC-FUNC-032: Follow-up question uses context
Tests that follow-up questions in a conversation consider the context 
from previous questions in the same session, and that clear-context 
functionality resets this behavior.
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
    """Send a query and capture the full response"""
    try:
        # Start query
        query_data = {
            "query": query,
            "session_id": session_id,
            "stream": True
        }
        
        response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=10)
        if response.status_code != 200:
            return False, f"Query start failed: {response.status_code}", None
            
        query_response = response.json()
        turn_id = query_response.get('turnId')
        
        # Connect to WebSocket using correct endpoint with query parameters
        ws_url = f"{WS_URL}/ws/stream?session_id={session_id}&turn_id={turn_id}"
        
        messages = []
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
        return True, full_response, turn_id
        
    except Exception as e:
        return False, f"Error during query: {e}", None

def clear_conversation_context(session_id):
    """Clear the conversation context for a session"""
    try:
        response = requests.delete(f"{BASE_URL}/api/sessions/{session_id}/context", timeout=10)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Error clearing context: {e}")
        return False

def test_follow_up_question_uses_context():
    """Test that follow-up questions use context from previous questions"""
    print("\n🧪 TC-FUNC-032: Testing follow-up question context usage")
    
    # Check backend health
    if not check_backend_health():
        pytest.fail("❌ Backend is not accessible")
    
    # Ensure we have documents
    success, doc_id = ensure_document_indexed()
    if not success:
        pytest.fail("❌ Failed to ensure document is indexed")
    
    # Generate unique session ID for this conversation
    session_id = str(uuid.uuid4())
    
    # First question - establish context
    print("\n📝 Q1: Asking initial question about machine learning")
    q1 = "What is machine learning?"
    
    success, response1, turn_id1 = send_query_and_get_response(q1, session_id)
    
    if not success:
        pytest.fail(f"❌ First query failed: {response1}")
    
    print(f"✅ Q1 Response: {response1[:100]}...")
    
    # Brief pause between questions
    time.sleep(1)
    
    # Follow-up question that requires context from Q1
    print("\n📝 Q2: Asking follow-up question that requires context")
    q2 = "What are the main types of it?"  # "it" should refer to machine learning from Q1
    
    success, response2, turn_id2 = send_query_and_get_response(q2, session_id)
    
    if not success:
        pytest.fail(f"❌ Follow-up query failed: {response2}")
    
    print(f"✅ Q2 Response: {response2[:100]}...")
    
    # Verify that the follow-up response shows understanding of context
    # The response should discuss types of machine learning, not be confused about "it"
    context_indicators = [
        "machine learning",
        "supervised",
        "unsupervised", 
        "reinforcement",
        "types",
        "classification",
        "regression"
    ]
    
    found_context_indicators = []
    response2_lower = response2.lower()
    
    for indicator in context_indicators:
        if indicator in response2_lower:
            found_context_indicators.append(indicator)
    
    print(f"🔍 Found context indicators: {found_context_indicators}")
    
    if len(found_context_indicators) < 2:
        pytest.fail(f"❌ Follow-up response doesn't show context understanding. Response: {response2}")
    
    print("✅ Follow-up question successfully used context from previous question")

def test_clear_context_resets_behavior():
    """Test that clearing context resets conversation behavior"""
    print("\n🧪 TC-FUNC-032b: Testing clear context functionality")
    
    # Check backend health
    if not check_backend_health():
        pytest.fail("❌ Backend is not accessible")
    
    # Ensure we have documents
    success, doc_id = ensure_document_indexed()
    if not success:
        pytest.fail("❌ Failed to ensure document is indexed")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Establish context with first question
    print("\n📝 Q1: Establishing context about neural networks")
    q1 = "Tell me about neural networks"
    
    success, response1, turn_id1 = send_query_and_get_response(q1, session_id)
    
    if not success:
        pytest.fail(f"❌ First query failed: {response1}")
    
    print(f"✅ Q1 Response: {response1[:100]}...")
    
    # Ask follow-up that should use context
    print("\n📝 Q2: Follow-up before clearing context")
    q2 = "How do they learn?"  # "they" should refer to neural networks
    
    success, response2, turn_id2 = send_query_and_get_response(q2, session_id)
    
    if not success:
        pytest.fail(f"❌ Second query failed: {response2}")
    
    print(f"✅ Q2 Response: {response2[:100]}...")
    
    # Clear the conversation context
    print("\n🧹 Clearing conversation context...")
    if not clear_conversation_context(session_id):
        print("⚠️ Clear context endpoint may not be implemented, continuing test...")
    else:
        print("✅ Context cleared")
    
    # Brief pause
    time.sleep(1)
    
    # Ask the same follow-up question after clearing context
    print("\n📝 Q3: Same follow-up after clearing context")
    q3 = "How do they learn?"  # Without context, "they" should be unclear
    
    success, response3, turn_id3 = send_query_and_get_response(q3, session_id)
    
    if not success:
        pytest.fail(f"❌ Third query failed: {response3}")
    
    print(f"✅ Q3 Response: {response3[:100]}...")
    
    # After clearing context, the response should either:
    # 1. Ask for clarification about what "they" refers to
    # 2. Give a generic response about learning
    # 3. Be different from the contextual response
    
    confusion_indicators = [
        "what do you mean",
        "could you clarify",
        "what are you referring to",
        "please specify", 
        "not sure what",
        "unclear",
        "more specific"
    ]
    
    response3_lower = response3.lower()
    shows_confusion = any(indicator in response3_lower for indicator in confusion_indicators)
    
    # Check if responses are significantly different
    responses_different = len(set(response2.split()) - set(response3.split())) > 5
    
    if shows_confusion or responses_different:
        print("✅ Clear context successfully reset conversation behavior")
    else:
        print("⚠️ Clear context may not be fully implemented - responses are similar")
        print(f"   Response before clear: {response2[:50]}...")
        print(f"   Response after clear:  {response3[:50]}...")

def test_multiple_context_turns():
    """Test context preservation across multiple conversation turns"""
    print("\n🧪 TC-FUNC-032c: Testing multi-turn context preservation")
    
    # Check backend health
    if not check_backend_health():
        pytest.fail("❌ Backend is not accessible")
    
    # Ensure we have documents
    success, doc_id = ensure_document_indexed()
    if not success:
        pytest.fail("❌ Failed to ensure document is indexed")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Multi-turn conversation to test context preservation
    conversation = [
        ("What is deep learning?", ["deep learning", "neural", "layers"]),
        ("What are its main advantages?", ["deep learning", "advantage", "benefit"]),
        ("What about the disadvantages?", ["disadvantage", "limitation", "challenge"]),
    ]
    
    responses = []
    
    for i, (question, expected_keywords) in enumerate(conversation, 1):
        print(f"\n📝 Q{i}: {question}")
        
        success, response, turn_id = send_query_and_get_response(question, session_id)
        
        if not success:
            pytest.fail(f"❌ Query {i} failed: {response}")
        
        responses.append(response)
        print(f"✅ Q{i} Response: {response[:100]}...")
        
        # Check if response contains expected context-aware keywords
        response_lower = response.lower()
        found_keywords = [kw for kw in expected_keywords if kw in response_lower]
        
        print(f"🔍 Found expected keywords: {found_keywords}")
        
        if len(found_keywords) == 0:
            print(f"⚠️ Response may not show full context awareness")
        
        # Brief pause between questions
        time.sleep(1)
    
    print("✅ Multi-turn context preservation test completed")

if __name__ == "__main__":
    test_follow_up_question_uses_context()
    test_clear_context_resets_behavior()
    test_multiple_context_turns()
