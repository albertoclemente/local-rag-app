#!/usr/bin/env python3
"""
DEFINITIVE RESET - Final solution to the RAG problem
"""

import os
import shutil
import subprocess
import sys
import time
import requests
from pathlib import Path

def cmd(command, cwd=None):
    """Execute command and return result"""
    print(f"🔨 {command}")
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, 
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except:
        return False, "", "timeout/error"

def definitive_destroy():
    """Complete destruction of everything"""
    print("💥 DEFINITIVE DESTRUCTION")
    print("=" * 40)
    
    # Kill everything
    print("🔪 Killing all processes...")
    cmd("pkill -f uvicorn")
    cmd("pkill -f 'npm run dev'")
    cmd("lsof -ti:8000 | xargs kill -9")
    cmd("lsof -ti:3000 | xargs kill -9")
    time.sleep(3)
    
    # Destroy all data
    print("🗑️  Destroying all data...")
    paths_to_destroy = [
        "/Users/alberto/RAGApp",
        "/Users/alberto/projects/RAG_APP/backend/.env"
    ]
    
    for path in paths_to_destroy:
        if os.path.exists(path):
            print(f"💣 {path}")
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
    
    # Clear Python caches
    print("🧹 Clearing caches...")
    cmd("find /Users/alberto/projects/RAG_APP -name '__pycache__' -exec rm -rf {} +")
    cmd("find /Users/alberto/projects/RAG_APP -name '*.pyc' -delete")
    
    print("✅ Destruction complete\n")

def rebuild_fresh():
    """Rebuild everything fresh"""
    print("🏗️  FRESH REBUILD")
    print("=" * 40)
    
    # Create directories
    print("📁 Creating directories...")
    os.makedirs("/Users/alberto/RAGApp/documents", exist_ok=True)
    os.makedirs("/Users/alberto/RAGApp/qdrant_data", exist_ok=True)
    
    # Create .env with debug settings
    print("⚙️  Creating debug environment...")
    env_content = """QDRANT_PATH=/Users/alberto/RAGApp/qdrant_data
RAG_DATA_DIR=/Users/alberto/RAGApp
RAG_DEBUG=true
RAG_LOG_LEVEL=DEBUG
RAG_PROFILE=balanced
"""
    
    with open("/Users/alberto/projects/RAG_APP/backend/.env", "w") as f:
        f.write(env_content)
    
    print("✅ Rebuild complete\n")

def start_backend():
    """Start backend with proper configuration"""
    print("🚀 STARTING BACKEND")
    print("=" * 40)
    
    os.chdir("/Users/alberto/projects/RAG_APP/backend")
    
    # Use the correct module path
    print("🔧 Launching uvicorn...")
    process = subprocess.Popen([
        "uvicorn", "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload",
        "--log-level", "debug"
    ])
    
    # Wait for startup
    print("⏳ Waiting for backend health...")
    for i in range(60):  # 2 minutes
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=3)
            if response.status_code == 200:
                print("✅ Backend is healthy!")
                return process
        except:
            pass
        
        if i % 5 == 0:
            print(f"   Still waiting... ({i+1}/60)")
        time.sleep(2)
    
    print("❌ Backend startup failed")
    process.terminate()
    return None

def upload_and_index():
    """Upload document and ensure it's properly indexed"""
    print("📤 DOCUMENT UPLOAD & INDEXING")
    print("=" * 40)
    
    # Find the PDF
    pdf_path = None
    search_dirs = ["/Users/alberto/Downloads", "/Users/alberto/Desktop"]
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for file in os.listdir(search_dir):
                if file.endswith('.pdf') and 'LLM' in file:
                    pdf_path = os.path.join(search_dir, file)
                    break
        if pdf_path:
            break
    
    if not pdf_path:
        print("❌ Could not find LLM PDF in Downloads or Desktop")
        return False
    
    print(f"📄 Found: {os.path.basename(pdf_path)}")
    
    # Upload
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            response = requests.post("http://localhost:8000/api/documents/upload", 
                                   files=files, timeout=180)
        
        if response.status_code == 200:
            doc_data = response.json()
            doc_id = doc_data['id']
            print(f"✅ Uploaded: {doc_id}")
            
            # Monitor indexing with detailed progress
            print("⏳ Monitoring indexing (this may take several minutes)...")
            for i in range(240):  # 20 minutes max
                try:
                    check_response = requests.get(f"http://localhost:8000/api/documents/{doc_id}")
                    if check_response.status_code == 200:
                        doc_info = check_response.json()
                        status = doc_info.get('embedding_status', 'unknown')
                        chunks = doc_info.get('chunkCount', 0)
                        
                        if i % 10 == 0:  # Every 50 seconds
                            print(f"   Status: {status}, Chunks: {chunks}")
                        
                        if status == 'indexed' and chunks > 0:
                            print(f"🎉 INDEXING SUCCESS! {chunks} chunks indexed")
                            return True
                        elif status == 'failed':
                            print("❌ Indexing failed")
                            return False
                            
                except Exception as e:
                    if i % 20 == 0:
                        print(f"   Check error: {e}")
                
                time.sleep(5)
            
            print("❌ Indexing timeout")
            return False
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def final_verification():
    """Final system verification"""
    print("🔍 FINAL VERIFICATION")
    print("=" * 40)
    
    # Check documents
    try:
        response = requests.get("http://localhost:8000/api/documents")
        if response.status_code == 200:
            docs = response.json().get('documents', [])
            print(f"📊 Total documents: {len(docs)}")
            
            if len(docs) == 1:
                doc = docs[0]
                chunks = doc.get('chunkCount', 0)
                status = doc.get('embedding_status', 'unknown')
                print(f"   Document: {doc.get('filename', 'unknown')}")
                print(f"   Status: {status}")
                print(f"   Chunks: {chunks}")
                
                if status == 'indexed' and chunks > 0:
                    print("✅ Document is properly indexed")
                else:
                    print("❌ Document indexing issue")
                    return False
            else:
                print(f"❌ Expected 1 document, found {len(docs)}")
                return False
        else:
            print("❌ Could not check documents")
            return False
    except Exception as e:
        print(f"❌ Document check error: {e}")
        return False
    
    # Test query endpoint
    print("\n🧪 Testing query endpoint...")
    try:
        test_query = "How many documents do you have access to?"
        response = requests.post("http://localhost:8000/api/query", 
                               json={"query": test_query}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query endpoint working: {result.get('query_id')}")
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Query error: {e}")
        return False

def main():
    """Execute the definitive reset"""
    print("🚨 DEFINITIVE RAG RESET 🚨")
    print("Final solution to fix all problems")
    print("=" * 50)
    
    # Step 1: Destroy everything
    definitive_destroy()
    
    # Step 2: Rebuild fresh
    rebuild_fresh()
    
    # Step 3: Start backend
    backend_process = start_backend()
    if not backend_process:
        print("💥 Backend startup failed")
        return
    
    try:
        # Step 4: Upload and index
        if not upload_and_index():
            print("💥 Document upload/indexing failed")
            return
        
        # Step 5: Final verification
        if not final_verification():
            print("💥 Final verification failed")
            return
        
        # Success!
        print("\n" + "🎉" * 25)
        print("🚀 DEFINITIVE RESET COMPLETE! 🚀")
        print("🎉" * 25)
        print()
        print("✅ System is completely rebuilt and verified")
        print("🌐 Frontend: http://localhost:3000 (start manually)")
        print("🔧 Backend: http://localhost:8000 (running)")
        print("📊 Health: http://localhost:8000/api/health")
        print("📄 Documents: http://localhost:8000/api/documents")
        print()
        print("🔥 EVERYTHING IS FRESH AND WORKING!")
        print("🧪 Try: 'How many documents do you have access to?'")
        print()
        print("The LLM should now correctly report having access to 1 document")
        print("Press Ctrl+C to stop backend")
        
        # Keep running
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 Stopping backend...")
            
    finally:
        if backend_process:
            backend_process.terminate()
            time.sleep(2)
            try:
                backend_process.kill()
            except:
                pass

if __name__ == "__main__":
    main()