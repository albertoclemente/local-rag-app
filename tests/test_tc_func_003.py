#!/usr/bin/env python3

import subprocess
import sys
import time
import requests
import json
import os

def start_backend():
    """Start the backend server"""
    print("Starting backend server...")
    backend_dir = "/Users/alberto/projects/RAG_APP/backend"
    
    # Start uvicorn in background
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "app.main:create_app", "--factory",
        "--host", "127.0.0.1", "--port", "8000"
    ], cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    return process

def test_duplicate_upload():
    """Test TC-FUNC-003: Upload duplicate file"""
    base_url = "http://localhost:8000"
    
    print("=== TC-FUNC-003: Upload duplicate file ===")
    
    # Wait for server to start
    print("Waiting for server to start...")
    for i in range(30):
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                print("✅ Server is ready!")
                break
        except:
            time.sleep(1)
    else:
        print("❌ Server failed to start")
        return False
    
    test_file = "/Users/alberto/projects/RAG_APP/test_documents/sample_document.txt"
    
    # First upload
    print("\n--- First upload ---")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response1 = requests.post(f"{base_url}/api/documents", files=files)
            print(f"First upload status: {response1.status_code}")
            
            if response1.status_code == 200:
                doc1_data = response1.json()
                print(f"First upload ID: {doc1_data.get('document', {}).get('id')}")
            else:
                print(f"First upload response: {response1.text}")
                
    except Exception as e:
        print(f"First upload failed: {e}")
        return False
    
    # Second upload (duplicate)
    print("\n--- Second upload (duplicate) ---")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response2 = requests.post(f"{base_url}/api/documents", files=files)
            print(f"Duplicate upload status: {response2.status_code}")
            print(f"Duplicate upload response: {response2.text}")
            
            # Check behavior: could be 409 Conflict, 200 with existing doc, or 400
            if response2.status_code == 409:
                print("✅ PASSED: Correctly detected duplicate with 409 Conflict")
            elif response2.status_code == 200:
                doc2_data = response2.json()
                doc2_id = doc2_data.get('document', {}).get('id')
                print(f"Second upload ID: {doc2_id}")
                if 'already exists' in response2.text.lower() or 'duplicate' in response2.text.lower():
                    print("✅ PASSED: Duplicate detected and handled gracefully")
                else:
                    print("⚠️  NOTED: System allows duplicate uploads (creates new entries)")
            else:
                print(f"⚠️  UNEXPECTED: Status {response2.status_code}")
                
    except Exception as e:
        print(f"Duplicate upload test failed: {e}")
    
    # Check document list
    print("\n--- Checking document list ---")
    try:
        response = requests.get(f"{base_url}/api/documents")
        if response.status_code == 200:
            docs = response.json().get('documents', [])
            sample_docs = [doc for doc in docs if doc['name'] == 'sample_document.txt']
            print(f"Total documents named 'sample_document.txt': {len(sample_docs)}")
            for i, doc in enumerate(sample_docs):
                print(f"  Document {i+1}: ID={doc['id']}, Status={doc['status']}")
        else:
            print(f"Failed to get document list: {response.status_code}")
    except Exception as e:
        print(f"Document list check failed: {e}")
    
    return True

if __name__ == "__main__":
    backend_process = start_backend()
    try:
        time.sleep(5)  # Give server time to start
        test_duplicate_upload()
    finally:
        backend_process.terminate()
        backend_process.wait()
        print("\nBackend stopped")
