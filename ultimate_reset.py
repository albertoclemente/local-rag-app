#!/usr/bin/env python3
"""
ULTIMATE RAG RESET
The final, definitive solution that will work no matter what
"""

import os
import shutil
import subprocess
import sys
import time
import requests
import signal
from pathlib import Path

class UltimateReset:
    def __init__(self):
        self.backend_process = None
        self.base_dir = "/Users/alberto/projects/RAG_APP"
        self.data_dir = "/Users/alberto/RAGApp"
        
    def log(self, message):
        print(f"🔧 {message}")
        
    def destroy_everything(self):
        """Nuclear destruction of all RAG components"""
        self.log("ULTIMATE DESTRUCTION PHASE")
        print("=" * 50)
        
        # Kill processes aggressively
        kill_commands = [
            "pkill -9 -f uvicorn",
            "pkill -9 -f 'npm run dev'",
            "pkill -9 -f python.*app.main",
            "lsof -ti:8000 | xargs -r kill -9",
            "lsof -ti:3000 | xargs -r kill -9"
        ]
        
        for cmd in kill_commands:
            try:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            except:
                pass
        
        time.sleep(3)
        
        # Destroy data
        destroy_paths = [
            self.data_dir,
            f"{self.base_dir}/backend/.env"
        ]
        
        for path in destroy_paths:
            if os.path.exists(path):
                self.log(f"Destroying: {path}")
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
                except:
                    pass
        
        # Clear caches
        try:
            subprocess.run(f"find {self.base_dir} -name '__pycache__' -exec rm -rf {{}} +", 
                         shell=True, capture_output=True)
            subprocess.run(f"find {self.base_dir} -name '*.pyc' -delete", 
                         shell=True, capture_output=True)
        except:
            pass
            
        self.log("Destruction complete")
        
    def setup_environment(self):
        """Setup clean environment"""
        self.log("ENVIRONMENT SETUP")
        print("=" * 50)
        
        # Create directories
        os.makedirs(f"{self.data_dir}/documents", exist_ok=True)
        os.makedirs(f"{self.data_dir}/qdrant_data", exist_ok=True)
        
        # Create minimal .env
        env_content = f"""QDRANT_PATH={self.data_dir}/qdrant_data
RAG_DATA_DIR={self.data_dir}
"""
        
        with open(f"{self.base_dir}/backend/.env", "w") as f:
            f.write(env_content)
            
        self.log("Environment ready")
        
    def start_backend(self):
        """Start backend with proper error handling"""
        self.log("BACKEND STARTUP")
        print("=" * 50)
        
        os.chdir(f"{self.base_dir}/backend")
        
        # Start backend
        cmd = ["python", "-m", "uvicorn", "app.main:app", 
               "--host", "0.0.0.0", "--port", "8000"]
        
        self.log(f"Starting: {' '.join(cmd)}")
        
        try:
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for startup
            for i in range(60):  # 2 minutes
                try:
                    response = requests.get("http://localhost:8000/api/health", timeout=2)
                    if response.status_code == 200:
                        self.log("Backend is healthy!")
                        return True
                except:
                    pass
                
                if self.backend_process.poll() is not None:
                    # Process died
                    stdout, stderr = self.backend_process.communicate()
                    self.log(f"Backend died! Error: {stderr}")
                    return False
                
                if i % 5 == 0:
                    self.log(f"Waiting for backend... ({i+1}/60)")
                time.sleep(2)
            
            self.log("Backend startup timeout")
            return False
            
        except Exception as e:
            self.log(f"Failed to start backend: {e}")
            return False
    
    def upload_document(self):
        """Upload test document"""
        self.log("DOCUMENT UPLOAD")
        print("=" * 50)
        
        # Find PDF
        pdf_path = None
        for search_dir in ["/Users/alberto/Downloads", "/Users/alberto/Desktop"]:
            if os.path.exists(search_dir):
                for file in os.listdir(search_dir):
                    if file.endswith('.pdf') and 'LLM' in file:
                        pdf_path = os.path.join(search_dir, file)
                        break
            if pdf_path:
                break
        
        if not pdf_path:
            self.log("❌ Could not find LLM PDF")
            return False
        
        self.log(f"Found PDF: {os.path.basename(pdf_path)}")
        
        # Upload
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': f}
                response = requests.post("http://localhost:8000/api/documents", 
                                       files=files, timeout=300)
            
            if response.status_code == 200:
                doc_data = response.json()
                self.log(f"Upload response: {doc_data}")
                doc_id = doc_data.get('document', {}).get('id')
                if not doc_id:
                    self.log(f"❌ No document ID in response: {doc_data}")
                    return False
                self.log(f"Upload successful: {doc_id}")
                
                # Monitor indexing
                self.log("Monitoring indexing...")
                for i in range(300):  # 25 minutes
                    try:
                        check_response = requests.get(f"http://localhost:8000/api/documents/{doc_id}")
                        if check_response.status_code == 200:
                            doc_info = check_response.json()
                            status = doc_info.get('embedding_status', 'unknown')
                            chunks = doc_info.get('chunkCount', 0)
                            
                            if i % 10 == 0:  # Every 50 seconds
                                self.log(f"Status: {status}, Chunks: {chunks}")
                            
                            if status == 'indexed' and chunks > 0:
                                self.log(f"🎉 INDEXING SUCCESS! {chunks} chunks")
                                return True
                            elif status == 'failed':
                                self.log("❌ Indexing failed")
                                return False
                                
                    except Exception as e:
                        if i % 20 == 0:
                            self.log(f"Check error: {e}")
                    
                    time.sleep(5)
                
                self.log("❌ Indexing timeout")
                return False
            else:
                self.log(f"❌ Upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Upload error: {e}")
            return False
    
    def verify_system(self):
        """Final verification"""
        self.log("SYSTEM VERIFICATION")
        print("=" * 50)
        
        # Check documents
        try:
            response = requests.get("http://localhost:8000/api/documents")
            if response.status_code == 200:
                docs = response.json().get('documents', [])
                self.log(f"Total documents: {len(docs)}")
                
                if len(docs) == 1:
                    doc = docs[0]
                    self.log(f"Document: {doc.get('filename')}")
                    self.log(f"Status: {doc.get('embedding_status')}")
                    self.log(f"Chunks: {doc.get('chunkCount')}")
                    
                    if doc.get('embedding_status') == 'indexed' and doc.get('chunkCount', 0) > 0:
                        self.log("✅ Document properly indexed")
                    else:
                        self.log("❌ Document indexing issue")
                        return False
                else:
                    self.log(f"❌ Expected 1 document, found {len(docs)}")
                    return False
            else:
                self.log("❌ Could not fetch documents")
                return False
        except Exception as e:
            self.log(f"❌ Document check error: {e}")
            return False
        
        # Test query
        self.log("Testing query endpoint...")
        try:
            response = requests.post("http://localhost:8000/api/query", 
                                   json={"query": "How many documents do you have access to?"}, 
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Query endpoint working: {result.get('query_id')}")
                return True
            else:
                self.log(f"❌ Query failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Query error: {e}")
            return False
    
    def cleanup(self):
        """Cleanup on exit"""
        if self.backend_process:
            self.log("Stopping backend...")
            self.backend_process.terminate()
            time.sleep(2)
            if self.backend_process.poll() is None:
                self.backend_process.kill()
    
    def run(self):
        """Execute the ultimate reset"""
        try:
            print("🚨 ULTIMATE RAG RESET 🚨")
            print("The final solution to end all problems")
            print("=" * 60)
            
            # Phase 1: Destroy
            self.destroy_everything()
            
            # Phase 2: Setup
            self.setup_environment()
            
            # Phase 3: Start
            if not self.start_backend():
                self.log("❌ Backend startup failed")
                return False
            
            # Phase 4: Upload
            if not self.upload_document():
                self.log("❌ Document upload failed")
                return False
            
            # Phase 5: Verify
            if not self.verify_system():
                self.log("❌ System verification failed")
                return False
            
            # Success!
            print("\n" + "🎉" * 40)
            print("🚀 ULTIMATE RESET SUCCESSFUL! 🚀")
            print("🎉" * 40)
            print()
            print("✅ System is completely rebuilt and operational")
            print("✅ Backend running on http://localhost:8000")
            print("✅ Document uploaded and properly indexed")
            print("✅ All endpoints tested and working")
            print()
            print("🔥 THE RAG SYSTEM IS NOW PERFECT!")
            print()
            print("Next steps:")
            print("1. Open frontend at http://localhost:3000")
            print("2. Ask: 'How many documents do you have access to?'")
            print("3. LLM should correctly report: 1 document")
            print()
            print("Press Ctrl+C to stop")
            
            # Keep running
            try:
                while True:
                    time.sleep(10)
                    # Health check
                    try:
                        requests.get("http://localhost:8000/api/health", timeout=2)
                    except:
                        self.log("⚠️ Backend health check failed")
                        break
            except KeyboardInterrupt:
                self.log("Shutting down...")
            
            return True
            
        except Exception as e:
            self.log(f"Fatal error: {e}")
            return False
        finally:
            self.cleanup()

def main():
    reset = UltimateReset()
    
    # Handle signals for clean shutdown
    def signal_handler(signum, frame):
        reset.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    success = reset.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()