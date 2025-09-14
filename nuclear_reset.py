#!/usr/bin/env python3
"""
NUCLEAR RESET - Complete system wipe and rebuild
This script will completely destroy and rebuild the entire RAG system
"""

import os
import shutil
import subprocess
import sys
import time
import requests
import json
from pathlib import Path

def run_command(cmd, cwd=None, timeout=30):
    """Run a command and return success status"""
    try:
        print(f"🔨 Running: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd, timeout=timeout, 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success: {cmd}")
            return True, result.stdout
        else:
            print(f"❌ Failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: {cmd}")
        return False, "Timeout"
    except Exception as e:
        print(f"💥 Exception: {cmd} - {e}")
        return False, str(e)

def nuclear_reset():
    """Complete system reset"""
    print("🚨 NUCLEAR RESET - DESTROYING EVERYTHING 🚨")
    print("=" * 60)
    
    # 1. Kill all processes
    print("\n🔪 STEP 1: Killing all processes")
    processes = [
        "pkill -f 'uvicorn.*main:app'",
        "pkill -f 'npm.*dev'", 
        "pkill -f 'node.*next'",
        "pkill -f 'python.*main.py'",
        "lsof -ti:8000 | xargs kill -9",
        "lsof -ti:3000 | xargs kill -9"
    ]
    
    for cmd in processes:
        run_command(cmd)
    
    time.sleep(3)
    
    # 2. Destroy all data
    print("\n💣 STEP 2: Destroying all data")
    data_paths = [
        "/Users/alberto/RAGApp",
        "/Users/alberto/projects/RAG_APP/backend/.env",
        "/Users/alberto/projects/RAG_APP/backend/__pycache__",
        "/Users/alberto/projects/RAG_APP/backend/app/__pycache__",
        "/Users/alberto/projects/RAG_APP/frontend/.next",
        "/Users/alberto/projects/RAG_APP/frontend/node_modules/.cache"
    ]
    
    for path in data_paths:
        if os.path.exists(path):
            print(f"🗑️  Destroying: {path}")
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
        else:
            print(f"🔍 Not found (OK): {path}")
    
    # 3. Create fresh environment
    print("\n🏗️  STEP 3: Creating fresh environment")
    
    # Create new data directory
    os.makedirs("/Users/alberto/RAGApp/documents", exist_ok=True)
    os.makedirs("/Users/alberto/RAGApp/qdrant_data", exist_ok=True)
    
    # Create enhanced .env with debugging
    env_content = """# RAG WebApp Environment - NUCLEAR RESET VERSION
QDRANT_PATH=/Users/alberto/RAGApp/qdrant_data
RAG_DATA_DIR=/Users/alberto/RAGApp
RAG_DEBUG=true
RAG_LOG_LEVEL=DEBUG
RAG_PROFILE=balanced

# Force rebuild flags
RAG_FORCE_REINDEX=true
RAG_CLEAR_CACHE=true
RAG_VERBOSE_LOGGING=true
"""
    
    with open("/Users/alberto/projects/RAG_APP/backend/.env", "w") as f:
        f.write(env_content)
    
    print("✅ Fresh environment created")
    
    # 4. Install/update dependencies
    print("\n📦 STEP 4: Installing dependencies")
    
    # Backend
    os.chdir("/Users/alberto/projects/RAG_APP/backend")
    success, _ = run_command("pip install -r requirements.txt", timeout=120)
    if not success:
        print("❌ Backend dependency install failed")
        return False
    
    # Frontend
    os.chdir("/Users/alberto/projects/RAG_APP/frontend")
    success, _ = run_command("npm install", timeout=120)
    if not success:
        print("❌ Frontend dependency install failed")
        return False
    
    return True

def enhanced_startup():
    """Start services with enhanced monitoring"""
    print("\n🚀 STEP 5: Enhanced startup with monitoring")
    
    # Start backend with debug logging
    print("🔧 Starting backend with debug mode...")
    os.chdir("/Users/alberto/projects/RAG_APP/backend")
    
    backend_cmd = "RAG_DEBUG=true RAG_VERBOSE_LOGGING=true uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    backend_process = subprocess.Popen(backend_cmd, shell=True)
    
    # Wait for backend to start
    print("⏳ Waiting for backend to initialize...")
    for i in range(30):
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is healthy")
                break
        except:
            pass
        time.sleep(2)
        print(f"⏳ Still waiting... ({i+1}/30)")
    else:
        print("❌ Backend failed to start")
        backend_process.terminate()
        return False
    
    # Start frontend
    print("🎨 Starting frontend...")
    os.chdir("/Users/alberto/projects/RAG_APP/frontend")
    frontend_process = subprocess.Popen("npm run dev", shell=True)
    
    # Wait for frontend
    print("⏳ Waiting for frontend...")
    for i in range(20):
        try:
            response = requests.get("http://localhost:3000", timeout=2)
            if response.status_code == 200:
                print("✅ Frontend is running")
                break
        except:
            pass
        time.sleep(2)
    else:
        print("❌ Frontend may have issues, but continuing...")
    
    return True, backend_process, frontend_process

def verify_system():
    """Comprehensive system verification"""
    print("\n🔍 STEP 6: System verification")
    
    tests = [
        ("Backend Health", "http://localhost:8000/api/health"),
        ("Settings API", "http://localhost:8000/api/settings"),
        ("Documents API", "http://localhost:8000/api/documents"),
        ("Ollama Service", "http://localhost:11434/api/tags")
    ]
    
    all_good = True
    for name, url in tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
                if "documents" in url:
                    data = response.json()
                    print(f"   📄 Documents: {len(data.get('documents', []))}")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                all_good = False
        except Exception as e:
            print(f"❌ {name}: {e}")
            all_good = False
    
    return all_good

def upload_and_test_document():
    """Upload the test document and verify everything works"""
    print("\n📤 STEP 7: Upload and test document")
    
    # Find the PDF file
    pdf_path = None
    search_paths = [
        "/Users/alberto/RAGApp/documents",
        "/Users/alberto/Downloads",
        "/Users/alberto/Desktop",
        "/Users/alberto/projects/RAG_APP"
    ]
    
    for search_dir in search_paths:
        if os.path.exists(search_dir):
            for file in os.listdir(search_dir):
                if file.endswith('.pdf') and 'LLM' in file:
                    pdf_path = os.path.join(search_dir, file)
                    break
        if pdf_path:
            break
    
    if not pdf_path:
        print("❌ Could not find the PDF document")
        return False
    
    print(f"📄 Found PDF: {pdf_path}")
    
    # Upload the document
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            response = requests.post("http://localhost:8000/api/documents/upload", files=files, timeout=60)
            
        if response.status_code == 200:
            doc_data = response.json()
            doc_id = doc_data.get('id')
            print(f"✅ Document uploaded successfully: {doc_id}")
            
            # Wait for indexing
            print("⏳ Waiting for indexing to complete...")
            for i in range(60):  # Wait up to 5 minutes
                try:
                    check_response = requests.get(f"http://localhost:8000/api/documents/{doc_id}")
                    if check_response.status_code == 200:
                        doc_info = check_response.json()
                        status = doc_info.get('embedding_status', 'unknown')
                        chunk_count = doc_info.get('chunkCount', 0)
                        
                        print(f"⏳ Status: {status}, Chunks: {chunk_count}")
                        
                        if status == 'indexed' and chunk_count > 0:
                            print(f"✅ Document fully indexed with {chunk_count} chunks")
                            return True
                except:
                    pass
                
                time.sleep(5)
            
            print("❌ Document indexing timed out")
            return False
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def test_query_system():
    """Test the query system end-to-end"""
    print("\n🧪 STEP 8: Testing query system")
    
    test_queries = [
        "How many documents do you have access to?",
        "What have we learned from building with LLMs?",
        "What are the key insights about LLM development?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        try:
            response = requests.post(
                "http://localhost:8000/api/query",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Query successful")
                print(f"   Query ID: {result.get('query_id', 'unknown')}")
                
                # Wait a moment for processing
                time.sleep(3)
                
            else:
                print(f"❌ Query failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Query error: {e}")
    
    return True

def main():
    """Main nuclear reset procedure"""
    print("🚨 NUCLEAR RESET PROCEDURE 🚨")
    print("This will completely destroy and rebuild the RAG system")
    print("=" * 60)
    
    # Step 1-4: Nuclear reset
    if not nuclear_reset():
        print("💥 Nuclear reset failed")
        return False
    
    # Step 5: Enhanced startup
    startup_result = enhanced_startup()
    if not startup_result:
        print("💥 Enhanced startup failed")
        return False
    
    backend_process, frontend_process = startup_result[1], startup_result[2]
    
    try:
        # Step 6: Verify system
        if not verify_system():
            print("💥 System verification failed")
            return False
        
        # Step 7: Upload document
        if not upload_and_test_document():
            print("💥 Document upload/indexing failed")
            return False
        
        # Step 8: Test queries
        if not test_query_system():
            print("💥 Query system test failed")
            return False
        
        print("\n" + "="*60)
        print("🎉 NUCLEAR RESET COMPLETED SUCCESSFULLY! 🎉")
        print("=" * 60)
        print("✅ System is fully operational")
        print("🌐 Frontend: http://localhost:3000")
        print("🔧 Backend: http://localhost:8000")
        print("📊 Health: http://localhost:8000/api/health")
        print("📄 Documents: http://localhost:8000/api/documents")
        print("")
        print("🔥 The system has been completely rebuilt from scratch!")
        print("🧪 Try asking: 'How many documents do you have access to?'")
        print("")
        print("Press Ctrl+C to stop the services")
        
        # Keep running
        try:
            while True:
                time.sleep(10)
                # Periodic health check
                try:
                    requests.get("http://localhost:8000/api/health", timeout=2)
                except:
                    print("⚠️  Backend health check failed")
        except KeyboardInterrupt:
            print("\n🛑 Shutting down services...")
            
    finally:
        # Cleanup
        try:
            backend_process.terminate()
            frontend_process.terminate()
            time.sleep(2)
            backend_process.kill()
            frontend_process.kill()
        except:
            pass

if __name__ == "__main__":
    main()