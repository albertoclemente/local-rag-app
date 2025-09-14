#!/usr/bin/env python3
"""
Debug script to test sources and citations
"""

import asyncio
import json
import requests
import websocket
import uuid
import time

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"

def upload_test_document():
    """Upload a known test document"""
    test_file = "/Users/alberto/projects/RAG_APP/test_documents/technical_doc.md"
    
    try:
        with open(test_file, 'rb') as file:
            files = {'file': ('technical_doc.md', file, 'text/markdown')}
            response = requests.post(f"{BASE_URL}/api/documents", files=files, timeout=30)
            
        if response.status_code == 200:
            data = response.json()
            doc_id = data.get('document', {}).get('id')
            print(f"✅ Uploaded document: {doc_id}")
            return doc_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def wait_for_indexing(doc_id, timeout=60):
    """Wait for document to be indexed"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/api/documents", timeout=10)
            if response.status_code == 200:
                documents = response.json().get('documents', [])
                doc = next((d for d in documents if d['id'] == doc_id), None)
                
                if doc and doc.get('status') == 'indexed' and doc.get('embedding_status') == 'indexed':
                    print(f"✅ Document indexed")
                    return True
                        
        except Exception as e:
            print(f"   Error checking status: {e}")
            
        time.sleep(2)
    
    return False

def test_websocket_with_sources():
    """Test WebSocket with a query that should produce sources"""
    session_id = str(uuid.uuid4())
    
    # Start query
    query_data = {
        "query": "What is technical documentation and what are its benefits?",
        "sessionId": session_id
    }
    
    response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Query start failed: {response.status_code}")
        return
        
    query_response = response.json()
    turn_id = query_response.get('turnId')
    
    # Connect to WebSocket
    ws_url = f"{WS_URL}/ws/stream?session_id={session_id}&turn_id={turn_id}"
    print(f"🔗 Connecting to: {ws_url}")
    
    messages = []
    citations = []
    sources = []
    response_complete = False
    
    def on_message(ws, message):
        nonlocal response_complete
        try:
            data = json.loads(message)
            event_type = data.get('event')
            
            print(f"📨 Received: {event_type} - {json.dumps(data)[:100]}...")
            
            if event_type == 'TOKEN':
                messages.append(data.get('text', ''))
            elif event_type == 'CITATION':
                citations.append(data)
            elif event_type == 'SOURCES':
                sources.extend(data.get('sources', []))
            elif event_type == 'END':
                response_complete = True
                ws.close()
                
        except Exception as e:
            print(f"Error parsing message: {e}")
    
    def on_error(ws, error):
        print(f"WebSocket error: {error}")
        
    def on_close(ws, close_status_code, close_msg):
        print(f"🔒 WebSocket closed")
    
    ws = websocket.WebSocketApp(ws_url,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    print("⏳ Starting WebSocket...")
    ws.run_forever()
    
    print(f"\n📊 Results:")
    print(f"   Messages: {len(messages)}")
    print(f"   Citations: {len(citations)}")
    print(f"   Sources: {len(sources)}")
    
    if sources:
        print(f"\n📋 Sources received:")
        for i, source in enumerate(sources):
            print(f"   {i+1}. Document: {source.get('document', 'N/A')}")
            print(f"      Score: {source.get('score', 'N/A')}")
            print(f"      Content: {source.get('content', 'N/A')[:50]}...")
    else:
        print("❌ No sources received")

def main():
    print("🧪 Debug Sources and Citations")
    print("=" * 40)
    
    # Upload and index a document
    doc_id = upload_test_document()
    if not doc_id:
        print("❌ Failed to upload document")
        return
    
    # Wait for indexing
    if not wait_for_indexing(doc_id):
        print("❌ Document indexing failed")
        return
    
    # Test WebSocket with sources
    test_websocket_with_sources()

if __name__ == "__main__":
    main()
