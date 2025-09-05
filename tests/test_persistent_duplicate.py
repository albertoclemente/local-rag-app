#!/usr/bin/env python3

import requests
import time

def test_persistent_duplicate_detection():
    """Test duplicate detection with persistent backend"""
    base_url = "http://localhost:8000"
    
    print("=== TC-FUNC-003: Duplicate Detection Test (Persistent) ===")
    print("Note: Ensure backend is already running on localhost:8000")
    
    # Check if server is ready
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Backend not ready")
            return
        print("✅ Backend is ready!")
    except:
        print("❌ Backend not accessible on localhost:8000")
        print("Please start the backend first with: uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000")
        return
    
    test_file = "/Users/alberto/projects/RAG_APP/test_documents/sample_document.txt"
    
    # First upload
    print("\n--- First upload ---")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response1 = requests.post(f"{base_url}/documents", files=files)
            print(f"First upload status: {response1.status_code}")
            
            if response1.status_code == 200:
                doc1_data = response1.json()
                print(f"First upload ID: {doc1_data.get('document', {}).get('id')}")
                print(f"Is duplicate: {doc1_data.get('is_duplicate', False)}")
                print(f"Message: {doc1_data.get('message')}")
            else:
                print(f"First upload response: {response1.text}")
                return
                
    except Exception as e:
        print(f"First upload failed: {e}")
        return
    
    # Second upload (should be detected as duplicate)
    print("\n--- Second upload (should detect duplicate) ---")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response2 = requests.post(f"{base_url}/documents", files=files)
            print(f"Duplicate upload status: {response2.status_code}")
            
            if response2.status_code == 200:
                doc2_data = response2.json()
                doc2_id = doc2_data.get('document', {}).get('id')
                is_duplicate = doc2_data.get('is_duplicate', False)
                message = doc2_data.get('message', '')
                
                print(f"Second upload ID: {doc2_id}")
                print(f"Is duplicate: {is_duplicate}")
                print(f"Message: {message}")
                
                if is_duplicate:
                    print("✅ PASSED: Duplicate correctly detected!")
                    
                    # Verify same document ID
                    first_id = doc1_data.get('document', {}).get('id')
                    if doc2_id == first_id:
                        print("✅ PASSED: Same document ID returned!")
                    else:
                        print(f"⚠️  WARNING: Different IDs - First: {first_id}, Second: {doc2_id}")
                else:
                    print("❌ FAILED: Duplicate not detected")
            else:
                print(f"Duplicate upload failed: {response2.status_code} - {response2.text}")
                
    except Exception as e:
        print(f"Duplicate upload test failed: {e}")

if __name__ == "__main__":
    test_persistent_duplicate_detection()
