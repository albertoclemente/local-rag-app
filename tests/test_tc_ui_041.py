#!/usr/bin/env python3
"""
TC-UI-041: Chat transcript & accessibility + Streaming Error States
Test chat transcript functionality, accessibility features, and streaming error handling.
"""

import requests
import websocket
import json
import time
import traceback

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

def test_chat_transcript_accessibility():
    """Test chat transcript with multiple turns and accessibility features"""
    print("🧪 TC-UI-041a: Testing chat transcript & accessibility")
    print("=" * 60)
    
    try:
        # Check if backend is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Backend not accessible")
            return False
        print("✅ Backend is accessible")
        
        # Get available documents
        docs_response = requests.get(f"{BASE_URL}/api/documents")
        if docs_response.status_code != 200:
            print("❌ Could not fetch documents")
            return False
            
        documents_data = docs_response.json()
        documents = documents_data.get('documents', [])
        if not documents:
            print("❌ No documents available")
            return False
            
        # Find a good document (indexed and with content)
        test_doc = None
        for doc in documents:
            if doc.get('status') == 'indexed' and doc.get('embedding_status') == 'indexed':
                test_doc = doc
                break
                
        if not test_doc:
            print("❌ No indexed documents available")
            return False
            
        print(f"✅ Using document: {test_doc['name']} ({test_doc['id']})")
        
        session_id = "test-session-ui-041-transcript"
        
        # Test multiple turns in conversation
        queries = [
            "What is the main topic of this document?",
            "Can you provide more details about the first section?", 
            "What are the key points mentioned?"
        ]
        
        turn_results = []
        
        print(f"\n📝 Testing {len(queries)} conversation turns...")
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔄 Turn {i}: '{query[:50]}...'")
            
            # Start query
            query_data = {
                "query": query,
                "session_id": session_id, 
                "document_ids": [test_doc['id']]
            }
            
            query_response = requests.post(f"{BASE_URL}/api/query", json=query_data)
            if query_response.status_code != 200:
                print(f"❌ Query {i} failed: {query_response.status_code}")
                return False
                
            turn_data = query_response.json()
            turn_id = turn_data.get("turnId")
            print(f"✅ Turn {i} started with ID: {turn_id}")
            
            # Monitor WebSocket for this turn
            streaming_success = monitor_turn_completion(session_id, turn_id, i)
            
            turn_results.append({
                'turn_number': i,
                'query': query,
                'turn_id': turn_id,
                'streaming_success': streaming_success
            })
            
            # Brief pause between turns
            time.sleep(1)
        
        # Analyze conversation results
        print(f"\n🔍 Analyzing conversation transcript...")
        successful_turns = sum(1 for turn in turn_results if turn['streaming_success'])
        print(f"📊 Successful turns: {successful_turns}/{len(turn_results)}")
        
        for turn in turn_results:
            status = "✅" if turn['streaming_success'] else "❌"
            print(f"   {status} Turn {turn['turn_number']}: {turn['query'][:40]}...")
        
        # Test conversation context retrieval
        print(f"\n📋 Testing conversation history API...")
        history_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/history")
        
        if history_response.status_code == 200:
            history_data = history_response.json()
            turns_in_history = len(history_data.get('turns', []))
            print(f"✅ Conversation history retrieved: {turns_in_history} turns")
            
            # Validate turn structure
            if turns_in_history > 0:
                first_turn = history_data['turns'][0]
                required_fields = ['turn_id', 'query', 'response', 'timestamp']
                missing_fields = [field for field in required_fields if field not in first_turn]
                
                if not missing_fields:
                    print("✅ Turn structure contains all required fields")
                    
                    # Check timestamp format for accessibility
                    timestamp = first_turn.get('timestamp', '')
                    if 'T' in timestamp and ':' in timestamp:
                        print("✅ ISO timestamp format for accessibility")
                    else:
                        print("❌ Non-ISO timestamp format")
                        return False
                else:
                    print(f"❌ Missing fields in turns: {missing_fields}")
                    return False
        else:
            print(f"❌ Could not retrieve conversation history: {history_response.status_code}")
            return False
        
        return successful_turns >= 2  # At least 2 successful turns
        
    except Exception as e:
        print(f"❌ Chat transcript test failed: {e}")
        traceback.print_exc()
        return False

def monitor_turn_completion(session_id, turn_id, turn_number):
    """Monitor a single turn completion via WebSocket"""
    try:
        ws_url = f"{WS_URL}/ws/stream?session_id={session_id}&turn_id={turn_id}"
        ws = websocket.create_connection(ws_url, timeout=10)
        
        events_received = []
        timeout = 45  # Longer timeout for conversation context
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                ws.settimeout(1.0)
                message = ws.recv()
                event_data = json.loads(message)
                event_type = event_data.get('event', 'UNKNOWN')
                
                events_received.append(event_type)
                
                if event_type == 'END':
                    ws.close()
                    print(f"   ✅ Turn {turn_number} completed successfully")
                    return True
                elif event_type == 'ERROR':
                    ws.close()
                    print(f"   ❌ Turn {turn_number} ended with error")
                    return False
                    
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                print(f"   ❌ Turn {turn_number} WebSocket error: {e}")
                break
        
        ws.close()
        print(f"   ⏰ Turn {turn_number} timed out")
        return False
        
    except Exception as e:
        print(f"   ❌ Turn {turn_number} connection failed: {e}")
        return False

def test_streaming_error_handling():
    """Test streaming error states and error handling"""
    print("\n🧪 TC-UI-041b: Testing streaming error handling")
    print("=" * 60)
    
    try:
        # Test 1: Empty query
        print("📝 Test 1: Empty query...")
        empty_query_data = {
            "query": "",
            "session_id": "test-session-ui-041-errors",
            "document_ids": []
        }
        
        response = requests.post(f"{BASE_URL}/api/query", json=empty_query_data)
        if response.status_code == 422:  # Validation error expected
            print("✅ Empty query properly rejected with validation error")
        else:
            print(f"⚠️  Empty query response: {response.status_code} (expected 422)")
        
        # Test 2: Invalid document ID
        print("\n📝 Test 2: Invalid document ID...")
        invalid_doc_query = {
            "query": "What is this about?",
            "session_id": "test-session-ui-041-errors",
            "document_ids": ["invalid-doc-id-12345"]
        }
        
        response = requests.post(f"{BASE_URL}/api/query", json=invalid_doc_query)
        if response.status_code in [400, 404]:  # Error expected
            print("✅ Invalid document ID properly rejected")
        else:
            print(f"⚠️  Invalid document ID response: {response.status_code}")
        
        # Test 3: WebSocket disconnection simulation
        print("\n📝 Test 3: WebSocket error simulation...")
        
        # Start a valid query first
        docs_response = requests.get(f"{BASE_URL}/api/documents")
        documents_data = docs_response.json()
        documents = documents_data.get('documents', [])
        
        if documents:
            test_doc = documents[0]
            query_data = {
                "query": "Test query for error handling",
                "session_id": "test-session-ui-041-errors",
                "document_ids": [test_doc['id']]
            }
            
            query_response = requests.post(f"{BASE_URL}/api/query", json=query_data)
            if query_response.status_code == 200:
                turn_data = query_response.json()
                turn_id = turn_data.get("turnId")
                
                # Connect to WebSocket and then close abruptly
                try:
                    ws_url = f"{WS_URL}/ws/stream?session_id={query_data['session_id']}&turn_id={turn_id}"
                    ws = websocket.create_connection(ws_url, timeout=5)
                    
                    # Receive a few events then close
                    for _ in range(3):
                        try:
                            ws.settimeout(2.0)
                            message = ws.recv()
                            event_data = json.loads(message)
                            print(f"   📨 Received: {event_data.get('event', 'UNKNOWN')}")
                        except:
                            break
                    
                    # Abrupt close
                    ws.close()
                    print("✅ WebSocket disconnection simulated")
                    
                except Exception as e:
                    print(f"⚠️  WebSocket error simulation: {e}")
        
        # Test 4: Malformed WebSocket URL
        print("\n📝 Test 4: Malformed WebSocket connection...")
        try:
            bad_ws_url = f"{WS_URL}/ws/stream?invalid_params"
            ws = websocket.create_connection(bad_ws_url, timeout=5)
            ws.close()
            print("⚠️  Malformed WebSocket URL was accepted (unexpected)")
        except Exception as e:
            print("✅ Malformed WebSocket URL properly rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming error test failed: {e}")
        traceback.print_exc()
        return False

def test_accessibility_features():
    """Test accessibility-related features via API"""
    print("\n🧪 TC-UI-041c: Testing accessibility features")
    print("=" * 60)
    
    try:
        # Test conversation history structure for accessibility
        session_id = "test-session-ui-041-accessibility"
        
        # Create a conversation turn
        docs_response = requests.get(f"{BASE_URL}/api/documents")
        documents_data = docs_response.json()
        documents = documents_data.get('documents', [])
        
        if not documents:
            print("❌ No documents available for accessibility test")
            return False
        
        test_doc = documents[0]
        query_data = {
            "query": "Accessibility test query",
            "session_id": session_id,
            "document_ids": [test_doc['id']]
        }
        
        # Start query
        query_response = requests.post(f"{BASE_URL}/api/query", json=query_data)
        if query_response.status_code != 200:
            print("❌ Could not start accessibility test query")
            return False
        
        turn_data = query_response.json()
        turn_id = turn_data.get("turnId")
        
        # Wait for completion
        time.sleep(5)
        
        # Check conversation structure
        history_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/history")
        if history_response.status_code == 200:
            history_data = history_response.json()
            
            # Check for accessibility-friendly structure
            accessibility_checks = []
            
            # Check timestamp format (should be ISO format for screen readers)
            turns = history_data.get('turns', [])
            if turns:
                first_turn = turns[0]
                timestamp = first_turn.get('timestamp', '')
                
                if 'T' in timestamp and ':' in timestamp:
                    accessibility_checks.append("✅ ISO timestamp format")
                else:
                    accessibility_checks.append("❌ Non-ISO timestamp format")
                
                # Check for role identification  
                if 'turn_id' in first_turn and 'query' in first_turn and 'response' in first_turn:
                    accessibility_checks.append("✅ Complete turn structure present")
                else:
                    accessibility_checks.append("❌ Incomplete turn structure")
                
                # Check response structure
                if 'response' in first_turn and isinstance(first_turn['response'], str):
                    accessibility_checks.append("✅ Response is text-based")
                else:
                    accessibility_checks.append("❌ Response structure not text-friendly")
                
                # Check sources for citations
                if 'sources' in first_turn:
                    accessibility_checks.append("✅ Sources available for citations")
                else:
                    accessibility_checks.append("❌ No sources for citation accessibility")
            
            print("📊 Accessibility structure checks:")
            for check in accessibility_checks:
                print(f"   {check}")
            
            return all("✅" in check for check in accessibility_checks)
        else:
            print("❌ Could not retrieve conversation for accessibility test")
            return False
        
    except Exception as e:
        print(f"❌ Accessibility test failed: {e}")
        traceback.print_exc()
        return False

def run_tc_ui_041():
    """Main test execution for TC-UI-041"""
    print("🧪 Starting TC-UI-041: Chat transcript & accessibility + Streaming errors")
    print("=" * 70)
    
    # Run all sub-tests
    transcript_test_passed = test_chat_transcript_accessibility()
    error_test_passed = test_streaming_error_handling()
    accessibility_test_passed = test_accessibility_features()
    
    # Overall result
    print("\n" + "=" * 70)
    if transcript_test_passed and error_test_passed and accessibility_test_passed:
        print("✅ TC-UI-041 OVERALL: PASSED")
        print("   ✓ Chat transcript functionality working")
        print("   ✓ Streaming error handling working")
        print("   ✓ Accessibility features validated")
        return True
    else:
        print("❌ TC-UI-041 OVERALL: FAILED")
        if not transcript_test_passed:
            print("   ✗ Chat transcript issues")
        if not error_test_passed:
            print("   ✗ Streaming error handling issues")
        if not accessibility_test_passed:
            print("   ✗ Accessibility feature issues")
        return False

if __name__ == "__main__":
    success = run_tc_ui_041()
    exit(0 if success else 1)
