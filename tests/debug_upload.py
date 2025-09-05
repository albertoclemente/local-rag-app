#!/usr/bin/env python3
"""
Simple test to debug document upload and status issues
"""

import requests
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def debug_upload():
    """Debug document upload process"""
    
    # Test different document
    test_doc = "/Users/alberto/projects/RAG_APP/test_documents/recipe.txt"
    
    print("🔍 Debugging document upload...")
    
    try:
        with open(test_doc, 'rb') as file:
            files = {'file': (Path(test_doc).name, file, 'text/plain')}
            response = requests.post(f"{BASE_URL}/api/documents", files=files, timeout=30)
            
        print(f"Upload response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Upload result: {result}")
            
            # Get document list to see status
            list_response = requests.get(f"{BASE_URL}/api/documents")
            if list_response.status_code == 200:
                docs = list_response.json().get('documents', [])
                print(f"Documents in system: {len(docs)}")
                for doc in docs[-3:]:  # Show last 3 docs
                    print(f"  - {doc.get('filename', 'N/A')}: {doc.get('status', 'N/A')} ({doc.get('chunk_count', 0)} chunks)")
        else:
            print(f"Upload failed: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_upload()
