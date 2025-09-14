#!/usr/bin/env python3
"""
TC-UI-040: StreamingIndicator during generation (Simplified Version)
Test streaming indicator states during query processing through WebSocket.
"""

import requests
import websocket
import json
import time
import traceback

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

def test_streaming_simple():
    """Simple streaming test with direct WebSocket connection"""
    print("🧪 TC-UI-040 Simple: Testing streaming indicator states")
    print("=" * 60)
    
    # Step 1: Start a query
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
            
        test_doc = documents[0]
        print(f"✅ Using document: {test_doc['name']} ({test_doc['id']})")
        
        # Start query
        query_data = {
            "query": "What is machine learning and how does it work?",
            "session_id": "test-session-ui-040", 
            "document_ids": [test_doc['id']]
        }
        
        print(f"\n📝 Testing query: '{query_data['query']}'")
        print("🚀 Step 1: Starting query via API...")
        
        query_response = requests.post(f"{BASE_URL}/api/query", json=query_data)
        if query_response.status_code != 200:
            print(f"❌ Query failed: {query_response.status_code}")
            return False
            
        turn_data = query_response.json()
        turn_id = turn_data.get("turnId")  # camelCase from API
        print(f"✅ Query started with turn ID: {turn_id}")
        
        # Step 2: Connect to WebSocket and monitor streaming
        print("\n📡 Step 2: Monitoring WebSocket streaming...")
        
        streaming_events = []
        stream_complete = False
        timeout = 60
        start_time = time.time()
        
        try:
            # Use correct WebSocket URL with query parameters
            ws_url = f"{WS_URL}/ws/stream?session_id={query_data['session_id']}&turn_id={turn_id}"
            ws = websocket.create_connection(ws_url, timeout=10)
            print("✅ WebSocket connection established")
            
            while time.time() - start_time < timeout and not stream_complete:
                try:
                    ws.settimeout(1.0)  # 1 second timeout for each message
                    message = ws.recv()
                    event_data = json.loads(message)
                    event_type = event_data.get('event', 'UNKNOWN')  # Use 'event' field
                    
                    streaming_events.append(event_type)
                    
                    if event_type == 'START':
                        print("📨 Received event: START")
                        print("   🟢 RETRIEVING state detected")
                    elif event_type == 'TOKEN':
                        token_text = event_data.get('text', '')[:15] + '...'
                        print(f"📨 Received event: TOKEN")
                        print(f"   🔵 STREAMING state - token: '{token_text}'")
                    elif event_type == 'CITATION':
                        citation_label = event_data.get('label', '?')
                        print(f"📨 Received event: CITATION")
                        print(f"   📚 Citation received: {citation_label}")
                    elif event_type == 'SOURCES':
                        print("📨 Received event: SOURCES")
                    elif event_type == 'END':
                        print("📨 Received event: END")
                        print("   🔴 COMPLETE state - generation finished")
                        stats = event_data.get('stats', {})
                        print(f"   📊 Stats: {stats.get('tokens', 0)} tokens in {stats.get('ms', 0)}ms")
                        stream_complete = True
                        break
                    elif event_type == 'ERROR':
                        print(f"📨 Received event: ERROR")
                        print(f"   ❌ Error: {event_data.get('message', 'Unknown error')}")
                        break
                        
                except websocket.WebSocketTimeoutException:
                    continue  # Keep waiting
                except Exception as e:
                    print(f"❌ WebSocket error: {e}")
                    break
            
            ws.close()
            
        except Exception as e:
            print(f"❌ Failed to establish WebSocket connection: {e}")
            return False
        
        # Step 3: Analyze results
        print(f"\n🔍 Step 3: Analyzing streaming events...")
        print(f"Events received: {streaming_events}")
        
        # Check for required events
        has_start = 'START' in streaming_events
        has_tokens = streaming_events.count('TOKEN') > 0
        has_end = 'END' in streaming_events
        
        print(f"\n📊 Event Analysis:")
        print(f"   START event: {'✅' if has_start else '❌'}")
        print(f"   TOKEN events: {'✅' if has_tokens else '❌'} ({streaming_events.count('TOKEN')} tokens)")
        print(f"   END event: {'✅' if has_end else '❌'}")
        print(f"   Stream completed: {'✅' if stream_complete else '❌'}")
        
        # Overall result
        success = has_start and has_tokens and (has_end or stream_complete)
        
        if success:
            print("\n✅ TC-UI-040 Simple: PASSED")
            print("   ✓ Streaming state transitions working correctly")
            return True
        else:
            print("\n❌ TC-UI-040 Simple: FAILED")
            if not has_start:
                print("   ✗ Missing START event")
            if not has_tokens:
                print("   ✗ No TOKEN events received")
            if not has_end and not stream_complete:
                print("   ✗ Stream did not complete properly")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_streaming_simple()
