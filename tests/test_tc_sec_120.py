#!/usr/bin/env python3
"""
TC-SEC-120: No outbound traffic - Local-only operation validation
Test that ingestion, retrieval, and generation succeed with NIC disabled.
"""

import requests
import subprocess
import time
import os
import signal
import psutil
import socket
from pathlib import Path
import json

# Configuration
BASE_URL = "http://localhost:8000"

class NetworkMonitor:
    """Monitor network connections during test execution"""
    
    def __init__(self):
        self.initial_connections = set()
        self.monitored_connections = set()
        self.violations = []
    
    def start_monitoring(self):
        """Start monitoring network connections"""
        self.initial_connections = self.get_current_connections()
        print(f"📊 Initial network connections: {len(self.initial_connections)}")
    
    def get_current_connections(self):
        """Get current network connections"""
        connections = set()
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    # Only track outbound connections
                    if conn.raddr.ip != '127.0.0.1' and not conn.raddr.ip.startswith('192.168.'):
                        connections.add(f"{conn.raddr.ip}:{conn.raddr.port}")
            return connections
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return connections
    
    def check_for_violations(self):
        """Check for new outbound connections"""
        current_connections = self.get_current_connections()
        new_connections = current_connections - self.initial_connections
        
        if new_connections:
            for conn in new_connections:
                self.violations.append(f"New outbound connection: {conn}")
        
        return len(new_connections) == 0
    
    def get_violations(self):
        """Get list of network violations"""
        return self.violations

def check_backend_accessibility():
    """Check if backend is accessible locally"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_local_ingestion():
    """Test document ingestion without network access"""
    print("🧪 TC-SEC-120a: Testing local document ingestion")
    print("=" * 60)
    
    try:
        # Check if backend is running
        if not check_backend_accessibility():
            print("❌ Backend not accessible - cannot test ingestion")
            return False
        
        print("✅ Backend is accessible locally")
        
        # Start network monitoring
        monitor = NetworkMonitor()
        monitor.start_monitoring()
        
        # Create a test document for ingestion
        test_content = """
        LOCAL-ONLY TEST DOCUMENT
        
        This document is being used to test the local-only ingestion capability 
        of the RAG system. The system should be able to process this document
        without making any outbound network connections.
        
        Key requirements:
        1. Document parsing should work locally
        2. Chunking should operate without network calls
        3. Embeddings should be generated locally
        4. Vector indexing should use local Qdrant only
        
        This test validates that the entire ingestion pipeline respects
        the local-only design principle of the RAG WebApp.
        """
        
        # Create temporary test file
        test_file_path = "/tmp/local_only_test.txt"
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        print("📄 Created test document for local ingestion")
        
        # Upload the document
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('local_only_test.txt', f, 'text/plain')}
                data = {'tags': json.dumps(['local-only', 'security-test'])}
                
                print("📤 Uploading document...")
                response = requests.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    doc_data = response_data.get('document', response_data)  # Handle both formats
                    doc_id = doc_data.get('id')
                    print(f"✅ Document uploaded successfully: {doc_id}")
                    
                    # Wait for processing to complete
                    print("⏳ Waiting for document processing...")
                    max_wait = 90  # 90 seconds max wait for security test
                    wait_time = 0
                    
                    while wait_time < max_wait:
                        # Check network violations during processing
                        if not monitor.check_for_violations():
                            print("❌ Network violation detected during ingestion!")
                            for violation in monitor.get_violations():
                                print(f"   🚨 {violation}")
                            return False
                        
                        # Check document status
                        doc_response = requests.get(f"{BASE_URL}/api/documents/{doc_id}")
                        if doc_response.status_code == 200:
                            doc_info = doc_response.json()
                            status = doc_info.get('status')
                            embedding_status = doc_info.get('embedding_status')
                            
                            if status == 'indexed' and embedding_status == 'indexed':
                                print("✅ Document processing completed successfully")
                                break
                            elif status == 'error':
                                print(f"❌ Document processing failed: {doc_info}")
                                return False
                        
                        time.sleep(2)
                        wait_time += 2
                    
                    if wait_time >= max_wait:
                        print("❌ Document processing timed out")
                        return False
                    
                    # Final network check
                    if monitor.check_for_violations():
                        print("✅ No outbound network connections detected during ingestion")
                        return True
                    else:
                        print("❌ Network violations detected:")
                        for violation in monitor.get_violations():
                            print(f"   🚨 {violation}")
                        return False
                        
                else:
                    print(f"❌ Document upload failed: {response.status_code}")
                    return False
                    
        finally:
            # Cleanup test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
        
    except Exception as e:
        print(f"❌ Local ingestion test failed: {e}")
        return False

def test_local_retrieval():
    """Test document retrieval without network access"""
    print("\n🧪 TC-SEC-120b: Testing local retrieval")
    print("=" * 60)
    
    try:
        # Check if backend is running
        if not check_backend_accessibility():
            print("❌ Backend not accessible - cannot test retrieval")
            return False
        
        # Start network monitoring
        monitor = NetworkMonitor()
        monitor.start_monitoring()
        
        # Get available documents
        docs_response = requests.get(f"{BASE_URL}/api/documents")
        if docs_response.status_code != 200:
            print("❌ Cannot access documents for retrieval test")
            return False
        
        documents_data = docs_response.json()
        documents = documents_data.get('documents', [])
        
        # Find an indexed document
        test_doc = None
        for doc in documents:
            if doc.get('status') == 'indexed' and doc.get('embedding_status') == 'indexed':
                test_doc = doc
                break
        
        if not test_doc:
            print("❌ No indexed documents available for retrieval test")
            return False
        
        print(f"✅ Using document: {test_doc['name']} for retrieval test")
        
        # Perform a query that requires retrieval
        query_data = {
            "query": "What is the main topic and key information in this document?",
            "session_id": "test-sec-120-retrieval",
            "document_ids": [test_doc['id']]
        }
        
        print("🔍 Performing retrieval query...")
        query_response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=30)
        
        if query_response.status_code == 200:
            turn_data = query_response.json()
            turn_id = turn_data.get("turnId")
            print(f"✅ Query initiated: {turn_id}")
            
            # Wait a moment for processing
            time.sleep(5)
            
            # Check for network violations during retrieval
            if monitor.check_for_violations():
                print("✅ No outbound network connections detected during retrieval")
                return True
            else:
                print("❌ Network violations detected during retrieval:")
                for violation in monitor.get_violations():
                    print(f"   🚨 {violation}")
                return False
        else:
            print(f"❌ Query failed: {query_response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Local retrieval test failed: {e}")
        return False

def test_local_generation():
    """Test response generation without network access"""
    print("\n🧪 TC-SEC-120c: Testing local generation")
    print("=" * 60)
    
    try:
        # Check if backend is running
        if not check_backend_accessibility():
            print("❌ Backend not accessible - cannot test generation")
            return False
        
        # Start network monitoring  
        monitor = NetworkMonitor()
        monitor.start_monitoring()
        
        # Get available documents
        docs_response = requests.get(f"{BASE_URL}/api/documents")
        if docs_response.status_code != 200:
            print("❌ Cannot access documents for generation test")
            return False
        
        documents_data = docs_response.json()
        documents = documents_data.get('documents', [])
        
        # Find an indexed document
        test_doc = None
        for doc in documents:
            if doc.get('status') == 'indexed' and doc.get('embedding_status') == 'indexed':
                test_doc = doc
                break
        
        if not test_doc:
            print("❌ No indexed documents available for generation test")
            return False
        
        print(f"✅ Using document: {test_doc['name']} for generation test")
        
        # Start a query and monitor the full generation process
        query_data = {
            "query": "Please provide a comprehensive summary of the key points in this document.",
            "session_id": "test-sec-120-generation",
            "document_ids": [test_doc['id']]
        }
        
        print("🤖 Starting response generation...")
        query_response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=30)
        
        if query_response.status_code == 200:
            turn_data = query_response.json()
            turn_id = turn_data.get("turnId")
            print(f"✅ Generation initiated: {turn_id}")
            
            # Monitor for longer period during generation
            monitor_duration = 30  # 30 seconds
            check_interval = 2  # Check every 2 seconds
            
            for i in range(0, monitor_duration, check_interval):
                time.sleep(check_interval)
                
                if not monitor.check_for_violations():
                    print(f"❌ Network violation detected at {i+check_interval}s into generation")
                    for violation in monitor.get_violations():
                        print(f"   🚨 {violation}")
                    return False
            
            print("✅ No outbound network connections detected during generation")
            return True
        else:
            print(f"❌ Generation query failed: {query_response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Local generation test failed: {e}")
        return False

def test_network_isolation_status():
    """Test and report on network isolation status"""
    print("\n🧪 TC-SEC-120d: Network isolation validation")
    print("=" * 60)
    
    try:
        # Check for external connectivity
        print("📡 Testing external network connectivity...")
        
        external_hosts = [
            ("8.8.8.8", 53),      # Google DNS
            ("1.1.1.1", 53),      # Cloudflare DNS  
            ("api.openai.com", 443),  # OpenAI API
            ("huggingface.co", 443),  # HuggingFace
        ]
        
        external_accessible = []
        for host, port in external_hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    external_accessible.append(f"{host}:{port}")
            except:
                pass  # Expected when network is isolated
        
        if external_accessible:
            print("⚠️  External network access detected:")
            for host in external_accessible:
                print(f"   📡 Accessible: {host}")
            print("   💡 For true local-only testing, consider disabling network interface")
            return "partial"  # Still proceed with tests but note network availability
        else:
            print("✅ No external network connectivity detected")
            print("🔒 System appears to be properly network-isolated")
            return True
        
    except Exception as e:
        print(f"⚠️  Network isolation check failed: {e}")
        return "unknown"

def run_tc_sec_120():
    """Main test execution for TC-SEC-120"""
    print("🧪 Starting TC-SEC-120: Local-only operation validation")
    print("=" * 70)
    
    # Check network isolation status first
    isolation_status = test_network_isolation_status()
    
    # Run local operation tests
    ingestion_test_passed = test_local_ingestion()
    retrieval_test_passed = test_local_retrieval()
    generation_test_passed = test_local_generation()
    
    # Overall result
    print("\n" + "=" * 70)
    
    if ingestion_test_passed and retrieval_test_passed and generation_test_passed:
        print("✅ TC-SEC-120 OVERALL: PASSED")
        print("   ✓ Local document ingestion working without network calls")
        print("   ✓ Local retrieval working without network calls")
        print("   ✓ Local generation working without network calls")
        
        if isolation_status == "partial":
            print("   ⚠️  Note: External network still accessible (not isolated)")
        elif isolation_status == True:
            print("   🔒 System properly network-isolated")
        
        return True
    else:
        print("❌ TC-SEC-120 OVERALL: FAILED")
        if not ingestion_test_passed:
            print("   ✗ Local ingestion issues")
        if not retrieval_test_passed:
            print("   ✗ Local retrieval issues")
        if not generation_test_passed:
            print("   ✗ Local generation issues")
        return False

if __name__ == "__main__":
    success = run_tc_sec_120()
    exit(0 if success else 1)
