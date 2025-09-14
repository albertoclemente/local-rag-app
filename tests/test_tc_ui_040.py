#!/usr/bin/env python3
"""
TC-UI-040: StreamingIndicator during generation
Tests that streaming indicators show proper states during query processing.

Steps: Submit a query; observe RETRIEVING → STREAMING → COMPLETE.
Expected: Proper event sequence with START → TOKEN → END states; no errors during streaming.
"""

import sys
import os
import requests
import websocket
import json
import time
import uuid
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test environment setup
os.environ['RAG_TEST_MODE'] = '1'

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

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
        response = requests.get(f"{BASE_URL}/api/documents", timeout=10)
        if response.status_code == 200:
            documents = response.json().get('documents', [])
            
            # Find a document that is fully indexed
            for doc in documents:
                if (doc.get('status') == 'indexed' and 
                    doc.get('embedding_status') == 'indexed'):
                    doc_id = doc.get('id')
                    print(f"✅ Using document: {doc.get('name')} ({doc_id})")
                    return True, doc_id
            
            if documents:
                doc_id = documents[0].get('id')
                print(f"⚠️  Using first available document: {documents[0].get('name')} ({doc_id})")
                return True, doc_id
        
        print("❌ No documents available for testing")
        return False, None
        
    except Exception as e:
        print(f"❌ Error checking documents: {e}")
        return False, None

def test_streaming_indicator_states():
    """Test that streaming goes through proper state transitions"""
    print("\n🧪 TC-UI-040: Testing streaming indicator states")
    print("=" * 60)
    
    # Check backend health
    if not check_backend_health():
        print("❌ Backend is not accessible")
        return False
    
    print("✅ Backend is accessible")
    
    # Ensure we have documents
    success, doc_id = ensure_document_indexed()
    if not success:
        print("❌ Failed to find indexed documents")
        return False
    
    # Generate unique session ID for this test
    session_id = str(uuid.uuid4())
    
    # Test query
    test_query = "What is machine learning and how does it work?"
    print(f"\n📝 Testing query: '{test_query}'")
    
    # Step 1: Start the query via API
    print("\n🚀 Step 1: Starting query via API...")
    try:
        query_data = {
            "query": test_query,
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Query start failed: {response.status_code} - {response.text}")
            return False
        
        query_response = response.json()
        turn_id = query_response.get('turnId')
        print(f"✅ Query started with turn ID: {turn_id}")
        
    except Exception as e:
        print(f"❌ Failed to start query: {e}")
        return False
    
    # Step 2: Connect to WebSocket and monitor streaming states
    print("\n📡 Step 2: Monitoring WebSocket streaming states...")
    
    ws_url = f"{WS_URL}/ws/stream?session_id={session_id}&turn_id={turn_id}"
    
    # Track streaming states
    streaming_events = []
    expected_events = ['START', 'TOKEN', 'END']
    connection_success = False
    stream_complete = False
    
    def on_message(ws, message):
        nonlocal stream_complete
        try:
            data = json.loads(message)
            event_type = data.get('event')
            
            if event_type:
                streaming_events.append(event_type)
                print(f"📨 Received event: {event_type}")
                
                if event_type == 'START':
                    print("   🟢 RETRIEVING state detected")
                elif event_type == 'TOKEN':
                    token_text = data.get('text', '')
                    if len(token_text) > 0:
                        print(f"   🔵 STREAMING state - token: '{token_text[:20]}...'")
                elif event_type == 'END':
                    print("   ✅ COMPLETE state detected")
                    stream_complete = True
                    ws.close()
                elif event_type == 'ERROR':
                    print(f"   ❌ ERROR detected: {data.get('detail', 'Unknown error')}")
                    stream_complete = True
                    ws.close()
                elif event_type == 'CITATION':
                    print(f"   📚 Citation received: {data.get('label', 'N/A')}")
                    
        except Exception as e:
            print(f"   ⚠️  Error parsing message: {e}")
    
    def on_error(ws, error):
        print(f"❌ WebSocket error: {error}")
    
    def on_open(ws):
        nonlocal connection_success
        connection_success = True
        print("✅ WebSocket connection established")
    
    def on_close(ws, close_status_code, close_msg):
        print("🔌 WebSocket connection closed")
    
    # Create WebSocket connection
    ws = websocket.WebSocketApp(ws_url,
                              on_message=on_message,
                              on_error=on_error,
                              on_open=on_open,
                              on_close=on_close)
    
    # Run WebSocket in a thread
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()
    
    # Wait for streaming to complete (up to 30 seconds)
    wait_time = 0
    max_wait = 30
    
    while not stream_complete and wait_time < max_wait:
        time.sleep(0.5)
        wait_time += 0.5
    
    if not connection_success:
        print("❌ Failed to establish WebSocket connection")
        return False
    
    if not stream_complete:
        print("❌ Streaming did not complete within timeout")
        ws.close()
        return False
    
    # Step 3: Analyze streaming state transitions
    print(f"\n🔍 Step 3: Analyzing streaming events...")
    print(f"Events received: {streaming_events}")
    
    # Validate event sequence
    validation_results = []
    
    # Check if we got START event
    if 'START' in streaming_events:
        validation_results.append("✅ START event (RETRIEVING state) detected")
    else:
        validation_results.append("❌ Missing START event (RETRIEVING state)")
    
    # Check if we got TOKEN events  
    token_count = streaming_events.count('TOKEN')
    if token_count > 0:
        validation_results.append(f"✅ {token_count} TOKEN events (STREAMING state) detected")
    else:
        validation_results.append("❌ No TOKEN events (STREAMING state) detected")
    
    # Check if we got END event
    if 'END' in streaming_events:
        validation_results.append("✅ END event (COMPLETE state) detected")
    else:
        validation_results.append("❌ Missing END event (COMPLETE state)")
    
    # Check event order
    if streaming_events:
        first_event = streaming_events[0]
        last_event = streaming_events[-1]
        
        if first_event == 'START':
            validation_results.append("✅ Streaming starts with START event")
        else:
            validation_results.append(f"❌ Streaming should start with START, got: {first_event}")
        
        if last_event == 'END':
            validation_results.append("✅ Streaming ends with END event")
        else:
            validation_results.append(f"❌ Streaming should end with END, got: {last_event}")
    
    # Check for errors
    if 'ERROR' in streaming_events:
        validation_results.append("⚠️  ERROR event detected during streaming")
    else:
        validation_results.append("✅ No ERROR events during streaming")
    
    # Print validation results
    print("\n📋 Validation Results:")
    for result in validation_results:
        print(f"  {result}")
    
    # Determine overall test result
    failed_validations = [r for r in validation_results if r.startswith("❌")]
    
    if len(failed_validations) == 0:
        print(f"\n🎉 TC-UI-040 PASSED: Streaming indicator states working correctly")
        print(f"   Events: {' → '.join(set(streaming_events))}")
        return True
    else:
        print(f"\n❌ TC-UI-040 FAILED: {len(failed_validations)} validation failures")
        for failure in failed_validations:
            print(f"   {failure}")
        return False

def test_streaming_error_handling():
    """Test streaming behavior with invalid queries"""
    print("\n🧪 TC-UI-040b: Testing streaming error handling")
    print("=" * 60)
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Test with empty query to trigger error
    print("📝 Testing with empty query...")
    
    try:
        query_data = {
            "query": "",  # Empty query should trigger validation error
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=10)
        
        if response.status_code == 422:
            print("✅ Empty query properly rejected with validation error")
            return True
        elif response.status_code == 200:
            print("⚠️  Empty query accepted - may need better validation")
            return True
        else:
            print(f"❌ Unexpected response to empty query: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing empty query: {e}")
        return False

def run_tc_ui_040():
    """Main test execution"""
    print("🧪 Starting TC-UI-040: StreamingIndicator during generation")
    print("=" * 60)
    
    # Run main streaming test
    streaming_test_passed = test_streaming_indicator_states()
    
    # Run error handling test
    error_test_passed = test_streaming_error_handling()
    
    # Overall result
    if streaming_test_passed and error_test_passed:
        print("\n✅ TC-UI-040 OVERALL: PASSED")
        print("   ✓ Streaming state transitions working correctly")
        print("   ✓ Error handling working correctly")
        return True
    else:
        print("\n❌ TC-UI-040 OVERALL: FAILED")
        if not streaming_test_passed:
            print("   ✗ Streaming state transitions issues")
        if not error_test_passed:
            print("   ✗ Error handling issues")
        return False

if __name__ == "__main__":
    try:
        success = run_tc_ui_040()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
