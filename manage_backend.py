#!/usr/bin/env python3
"""
Backend management script
Provides clean start/stop/restart functionality for development
"""

import subprocess
import signal
import sys
import time
import os
import requests
from pathlib import Path

BACKEND_DIR = Path(__file__).parent / "backend"
PID_FILE = "/tmp/rag_backend.pid"
LOG_FILE = "/tmp/rag_backend.log"

def is_backend_running():
    """Check if backend is accessible"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_backend():
    """Start the backend server"""
    if is_backend_running():
        print("✅ Backend is already running")
        return True
        
    print("🚀 Starting backend server...")
    
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000"
    ]
    
    with open(LOG_FILE, "w") as log_file:
        process = subprocess.Popen(
            cmd,
            cwd=BACKEND_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
    
    # Save PID
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))
    
    # Wait for startup
    for i in range(30):  # 30 second timeout
        if is_backend_running():
            print("✅ Backend started successfully")
            return True
        time.sleep(1)
    
    print("❌ Backend failed to start")
    return False

def stop_backend():
    """Stop the backend server"""
    print("🛑 Stopping backend server...")
    
    # Try to read PID
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        import os
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            print("✅ Backend stopped")
        except ProcessLookupError:
            print("Backend was not running")
            
        # Clean up PID file
        if Path(PID_FILE).exists():
            Path(PID_FILE).unlink()
            
    except FileNotFoundError:
        print("No PID file found")
    
    # Fallback: kill all uvicorn processes
    subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)

def restart_backend():
    """Restart the backend server"""
    stop_backend()
    time.sleep(2)
    return start_backend()

def status_backend():
    """Show backend status"""
    if is_backend_running():
        print("✅ Backend is running")
        print("🔗 Health endpoint: http://127.0.0.1:8000/health")
        print("📖 API docs: http://127.0.0.1:8000/api/docs")
    else:
        print("❌ Backend is not running")

if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Manage RAG WebApp backend')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        start_backend()
    elif args.action == 'stop':
        stop_backend()
    elif args.action == 'restart':
        restart_backend()
    elif args.action == 'status':
        status_backend()
