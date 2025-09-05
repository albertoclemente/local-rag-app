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

def test_unsupported_file():
    """Test TC-FUNC-002: Upload unsupported file type"""
    base_url = "http://localhost:8000"
    
    print("=== TC-FUNC-002: Upload unsupported file type ===")
    
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
    
    # Test unsupported file upload
    print("\n--- Testing unsupported file upload (.sh) ---")
    try:
        test_file = "/Users/alberto/projects/RAG_APP/test_documents/unsupported_file.sh"
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{base_url}/api/documents", files=files)
            print(f"Upload status: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Expected: 400 Bad Request or 422 Unprocessable Entity
            if response.status_code in [400, 422]:
                print("✅ PASSED: Correctly rejected unsupported file type")
            else:
                print("❌ FAILED: Should have rejected unsupported file type")
                
    except Exception as e:
        print(f"Upload test failed: {e}")
    
    return True

if __name__ == "__main__":
    backend_process = start_backend()
    try:
        time.sleep(5)  # Give server time to start
        test_unsupported_file()
    finally:
        backend_process.terminate()
        backend_process.wait()
        print("\nBackend stopped")
