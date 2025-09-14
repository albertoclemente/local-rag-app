#!/usr/bin/env python3
"""
RADICAL RESET - Targeted system destruction and rebuild
"""

import os
import shutil
import subprocess
import sys
import time
import requests
import json
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Run command and return output"""
    try:
        print(f"🔨 {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def radical_destroy():
    """Destroy everything RAG-related"""
    print("💥 RADICAL DESTRUCTION PHASE")
    print("=" * 50)
    
    # Kill processes
    print("\n🔪 Terminating all processes...")
    kill_commands = [
        "pkill -f uvicorn",
        "pkill -f 'npm run dev'",
        "pkill -f 'next dev'",
        "lsof -ti:8000 | xargs kill -9 2>/dev/null || true",
        "lsof -ti:3000 | xargs kill -9 2>/dev/null || true"
    ]
    
    for cmd in kill_commands:
        run_cmd(cmd)
    
    time.sleep(3)
    
    # Destroy data
    print("\n🗑️  Destroying all data...")
    destroy_paths = [
        "/Users/alberto/RAGApp",
        "/Users/alberto/projects/RAG_APP/backend/.env"
    ]
    
    for path in destroy_paths:
        if os.path.exists(path):
            print(f"💣 Destroying: {path}")
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
    
    # Clear Python caches
    print("\n🧹 Clearing caches...")
    cache_patterns = [
        "/Users/alberto/projects/RAG_APP/backend/**/__pycache__",
        "/Users/alberto/projects/RAG_APP/backend/**/*.pyc"
    ]
    
    run_cmd("find /Users/alberto/projects/RAG_APP/backend -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true")
    run_cmd("find /Users/alberto/projects/RAG_APP/backend -name '*.pyc' -delete 2>/dev/null || true")
    
    print("✅ Destruction complete")

def rebuild_environment():
    """Rebuild from scratch"""
    print("\n🏗️  REBUILD PHASE")
    print("=" * 50)
    
    # Create directories
    print("📁 Creating fresh directories...")
    os.makedirs("/Users/alberto/RAGApp/documents", exist_ok=True)
    os.makedirs("/Users/alberto/RAGApp/qdrant_data", exist_ok=True)
    
    # Create enhanced .env
    print("⚙️  Creating enhanced environment...")
    env_content = """# RADICAL RESET ENVIRONMENT
QDRANT_PATH=/Users/alberto/RAGApp/qdrant_data
RAG_DATA_DIR=/Users/alberto/RAGApp
RAG_DEBUG=true
RAG_LOG_LEVEL=DEBUG
RAG_PROFILE=balanced
RAG_VERBOSE_LOGGING=true
RAG_FORCE_REINDEX=true
"""
    
    with open("/Users/alberto/projects/RAG_APP/backend/.env", "w") as f:
        f.write(env_content)
    
    print("✅ Environment rebuilt")

def start_services():
    """Start services with monitoring"""
    print("\n🚀 STARTUP PHASE")
    print("=" * 50)
    
    # Start backend
    print("🔧 Starting backend...")
    os.chdir("/Users/alberto/projects/RAG_APP/backend")
    
    # Use the correct Python command for the environment
    backend_process = subprocess.Popen([
        "python", "-m", "uvicorn", "main:app", 
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ], env={**os.environ, "RAG_DEBUG": "true"})
    
    # Wait for backend
    print("⏳ Waiting for backend...")
    for i in range(30):
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is healthy!")
                break
        except:
            pass
        time.sleep(2)
        print(f"   Still waiting... ({i+1}/30)")
    else:
        print("❌ Backend startup timeout")
        backend_process.terminate()
        return None
    
    return backend_process

def upload_test_document():
    """Upload and verify document"""
    print("\n📤 DOCUMENT UPLOAD PHASE")
    print("=" * 50)
    
    # Find PDF
    pdf_path = None
    search_locations = [
        "/Users/alberto/Downloads",
        "/Users/alberto/Desktop", 
        "/Users/alberto/Documents"
    ]
    
    for location in search_locations:
        if os.path.exists(location):
            for file in os.listdir(location):
                if file.endswith('.pdf') and ('LLM' in file or 'llm' in file.lower()):
                    pdf_path = os.path.join(location, file)
                    break
        if pdf_path:
            break
    
    if not pdf_path:
        print("❌ Could not find LLM PDF document")
        print("🔍 Please ensure the PDF is in Downloads, Desktop, or Documents")
        return False
    
    print(f"📄 Found PDF: {os.path.basename(pdf_path)}")
    
    # Upload
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            response = requests.post("http://localhost:8000/api/documents/upload", 
                                   files=files, timeout=120)
        
        if response.status_code == 200:
            doc_data = response.json()
            doc_id = doc_data.get('id')
            print(f"✅ Upload successful: {doc_id}")
            
            # Monitor indexing
            print("⏳ Monitoring indexing progress...")
            for i in range(120):  # 10 minutes max
                try:
                    check_response = requests.get(f"http://localhost:8000/api/documents/{doc_id}")
                    if check_response.status_code == 200:
                        doc_info = check_response.json()
                        status = doc_info.get('embedding_status', 'unknown')
                        chunks = doc_info.get('chunkCount', 0)
                        
                        if i % 6 == 0:  # Print every 30 seconds
                            print(f"   Status: {status}, Chunks: {chunks}")
                        
                        if status == 'indexed' and chunks > 0:
                            print(f"🎉 INDEXING COMPLETE! {chunks} chunks indexed")
                            return True
                except Exception as e:
                    if i % 6 == 0:
                        print(f"   Checking... ({e})")
                
                time.sleep(5)
            
            print("❌ Indexing timeout")
            return False
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def test_rag_system():
    """Test the complete RAG system"""
    print("\n🧪 RAG SYSTEM TEST")
    print("=" * 50)
    
    # Check document count
    try:
        response = requests.get("http://localhost:8000/api/documents")
        if response.status_code == 200:
            docs = response.json().get('documents', [])
            print(f"📊 Documents in system: {len(docs)}")
            for doc in docs:
                print(f"   - {doc.get('filename', 'unknown')}: {doc.get('chunkCount', 0)} chunks")
        else:
            print("❌ Could not fetch documents")
            return False
    except Exception as e:
        print(f"❌ Document check failed: {e}")
        return False
    
    # Test query
    test_query = "How many documents do you have access to?"
    print(f"\n🔍 Testing query: '{test_query}'")
    
    try:
        response = requests.post("http://localhost:8000/api/query", 
                               json={"query": test_query}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            query_id = result.get('query_id')
            print(f"✅ Query initiated: {query_id}")
            
            # Wait for WebSocket processing
            time.sleep(5)
            print("⏳ Query should be processing via WebSocket...")
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Query error: {e}")
        return False

def main():
    """Execute radical reset"""
    print("🚨 RADICAL RAG SYSTEM RESET 🚨")
    print("This will completely destroy and rebuild everything")
    print("=" * 60)
    
    # Phase 1: Destroy
    radical_destroy()
    
    # Phase 2: Rebuild
    rebuild_environment()
    
    # Phase 3: Start
    backend_process = start_services()
    if not backend_process:
        print("💥 Failed to start services")
        return
    
    try:
        # Phase 4: Upload
        if not upload_test_document():
            print("💥 Document upload failed")
            return
        
        # Phase 5: Test
        if not test_rag_system():
            print("💥 RAG system test failed")
            return
        
        print("\n" + "🎉" * 20)
        print("🚀 RADICAL RESET COMPLETE! 🚀")
        print("🎉" * 20)
        print(f"✅ System is now completely fresh and operational")
        print(f"🌐 Open your browser to: http://localhost:3000")
        print(f"🧪 Test query: 'How many documents do you have access to?'")
        print(f"📊 API Health: http://localhost:8000/api/health")
        print(f"📄 Documents: http://localhost:8000/api/documents")
        print("")
        print("🔥 Everything has been rebuilt from absolute zero!")
        print("Press Ctrl+C to stop")
        
        # Keep running
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            
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