#!/usr/bin/env python3
"""
Simple WebSocket test to see what messages we receive
"""

import requests
import time
import json
import websocket
import threading
import uuid

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"

def test_websocket_debug():
    """Test WebSocket connection and see all messages"""
    
    # Start a query
    session_id = str(uuid.uuid4())
    query_data = {
        "query": "What is machine learning?",
        "session_id": session_id,
        "stream": True
    }
    
    response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=10)
    print(f"Query response: {response.status_code} - {response.json()}")
    
    if response.status_code != 200:
        print("❌ Query failed")
        return
        
    query_response = response.json()
    turn_id = query_response.get('turnId')
    
    # Connect to WebSocket
    ws_url = f"{WS_URL}/ws/stream?session_id={session_id}&turn_id={turn_id}"
    print(f"Connecting to: {ws_url}")
    
    received_messages = []
    
    def on_message(ws, message):
        print(f"📨 Received: {message}")
        received_messages.append(message)
    
    def on_error(ws, error):
        print(f"❌ WebSocket error: {error}")
        
    def on_open(ws):
        print("✅ WebSocket opened")
        
    def on_close(ws, close_status_code, close_msg):
        print(f"🔒 WebSocket closed: {close_status_code} - {close_msg}")
        
    ws = websocket.WebSocketApp(ws_url,
                              on_message=on_message,
                              on_error=on_error,
                              on_open=on_open,
                              on_close=on_close)
    
    # Run WebSocket in a thread
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()
    
    # Wait for response
    print("⏳ Waiting for WebSocket messages...")
    time.sleep(10)
    ws.close()
    
    print(f"\n📊 Summary: Received {len(received_messages)} messages")
    for i, msg in enumerate(received_messages):
        print(f"  {i+1}: {msg[:100]}...")

if __name__ == "__main__":
    test_websocket_debug()
