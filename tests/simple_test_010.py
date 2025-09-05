#!/usr/bin/env python3
"""
Simple test for TC-FUNC-010: Adaptive Chunking
"""

import requests
import time
from pathlib import Path

def test_backend():
    """Test if backend is accessible"""
    try:
        print("Testing backend connection...")
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        print(f"Response status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Backend connection failed: {e}")
        return False

def upload_file(file_path):
    """Upload a file and return response"""
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (file_path.name, file, 'text/plain')}
            response = requests.post("http://127.0.0.1:8000/api/documents", files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Uploaded: {file_path.name}")
            print(f"   Document ID: {result.get('document_id', 'N/A')}")
            print(f"   Chunks: {result.get('chunks_created', 'N/A')}")
            return True
        else:
            print(f"❌ Failed: {file_path.name} - {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Error text: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {file_path.name} - {str(e)}")
        return False

def main():
    print("🧪 TC-FUNC-010: Adaptive Chunking Test")
    print("=" * 50)
    
    if not test_backend():
        print("❌ Backend not accessible")
        return
    
    print("✅ Backend accessible")
    
    # Test files
    test_files = [
        "/Users/alberto/projects/RAG_APP/test_documents/technical_doc.md",
        "/Users/alberto/projects/RAG_APP/test_documents/narrative_story.txt", 
        "/Users/alberto/projects/RAG_APP/test_documents/financial_report.txt",
        "/Users/alberto/projects/RAG_APP/test_documents/recipe.txt"
    ]
    
    success_count = 0
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            if upload_file(path):
                success_count += 1
        else:
            print(f"❌ File not found: {file_path}")
    
    print(f"\n📋 Result: {success_count}/{len(test_files)} files uploaded successfully")
    
    if success_count == len(test_files):
        print("🎉 TC-FUNC-010 PASSED")
    else:
        print("❌ TC-FUNC-010 FAILED")

if __name__ == "__main__":
    main()
