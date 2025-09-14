#!/usr/bin/env python3
"""
Debug script for TC-FUNC-032: Follow-up question context
This will help us understand what's happening with conversation context
"""

import requests
import websocket
import json
import time
import uuid
import threading
import sys

BASE_URL = "http://localhost:8000"

def debug_conversation_context():
    """Debug the conversation context system"""
    print("🔍 Debugging TC-FUNC-032: Conversation Context")
    print("=" * 60)
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    print(f"📋 Session ID: {session_id}")
    
    # First, let's check if we can get session info
    try:
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}", timeout=5)
        print(f"📊 Initial session info status: {response.status_code}")
    except:
        print("📊 Session endpoint not accessible (expected for new session)")
    
    # Step 1: Send first query
    print("\n📝 Q1: What is machine learning?")
    
    # Connect to WebSocket
    ws_url = f"ws://localhost:8000/ws/stream"
    messages = []
    
    def on_message(ws, message):
        messages.append(json.loads(message))
    
    def on_error(ws, error):
        print(f"WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print("WebSocket connection closed")
    
    # First query
    ws1 = websocket.WebSocketApp(ws_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    def run_ws1():
        ws1.run_forever()
    
    # Start WebSocket in background
    ws1_thread = threading.Thread(target=run_ws1)
    ws1_thread.daemon = True
    ws1_thread.start()
    
    time.sleep(1)  # Let connection establish
    
    # Send first query
    query1_data = {
        "query": "What is machine learning?",
        "session_id": session_id,
        "turn_id": str(uuid.uuid4())
    }
    
    ws1.send(json.dumps(query1_data))
    
    # Wait for response
    time.sleep(10)
    ws1.close()
    
    # Process first response
    response1_text = ""
    for msg in messages:
        if msg.get('event') == 'RESPONSE':
            response1_text += msg.get('text', '')
    
    print(f"✅ Q1 Response: {response1_text[:100]}...")
    print(f"📊 Q1 Events received: {len(messages)}")
    
    # Step 2: Check session info after first query
    print(f"\n🔍 Checking session info after Q1...")
    try:
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}", timeout=5)
        if response.status_code == 200:
            session_data = response.json()
            print(f"✅ Session exists with {session_data.get('turn_count', 0)} turns")
        else:
            print(f"⚠️  Session status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking session: {e}")
    
    # Step 3: Send follow-up query with same session
    print(f"\n📝 Q2: What are the main types of it? (session: {session_id})")
    
    messages2 = []
    
    def on_message2(ws, message):
        messages2.append(json.loads(message))
    
    ws2 = websocket.WebSocketApp(ws_url,
                                on_message=on_message2,
                                on_error=on_error,
                                on_close=on_close)
    
    def run_ws2():
        ws2.run_forever()
    
    ws2_thread = threading.Thread(target=run_ws2)
    ws2_thread.daemon = True
    ws2_thread.start()
    
    time.sleep(1)
    
    # Send follow-up query
    query2_data = {
        "query": "What are the main types of it?",
        "session_id": session_id,  # Same session
        "turn_id": str(uuid.uuid4())
    }
    
    ws2.send(json.dumps(query2_data))
    
    # Wait for response
    time.sleep(10)
    ws2.close()
    
    # Process second response
    response2_text = ""
    for msg in messages2:
        if msg.get('event') == 'RESPONSE':
            response2_text += msg.get('text', '')
    
    print(f"✅ Q2 Response: {response2_text[:200]}...")
    print(f"📊 Q2 Events received: {len(messages2)}")
    
    # Step 4: Analyze if context was used
    print(f"\n🧠 Analysis:")
    print(f"   Q1 mentioned: machine learning")
    print(f"   Q2 asked about: 'types of it'")
    
    response2_lower = response2_text.lower()
    context_indicators = ['machine learning', 'supervised', 'unsupervised', 'reinforcement']
    found_indicators = [ind for ind in context_indicators if ind in response2_lower]
    
    print(f"   Q2 context indicators found: {found_indicators}")
    
    if 'machine learning' in response2_lower or len(found_indicators) >= 2:
        print("✅ SUCCESS: Context appears to be working!")
    else:
        print("❌ ISSUE: Context not properly used")
        print(f"   Full Q2 response: {response2_text}")
    
    # Step 5: Check final session state
    print(f"\n📊 Final session check...")
    try:
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}", timeout=5)
        if response.status_code == 200:
            session_data = response.json()
            print(f"✅ Final session has {session_data.get('turn_count', 0)} turns")
        else:
            print(f"⚠️  Final session status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking final session: {e}")

if __name__ == "__main__":
    debug_conversation_context()
