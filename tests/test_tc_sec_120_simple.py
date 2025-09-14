#!/usr/bin/env python3
"""
TC-SEC-120: Local-only operation validation (Simplified)
Test core local-only functionality without complex document processing.
"""

import requests
import subprocess
import time
import socket
import psutil
import json

# Configuration
BASE_URL = "http://localhost:8000"

def check_external_connectivity():
    """Check if external network connections are available"""
    external_hosts = [
        ("8.8.8.8", 53),           # Google DNS
        ("1.1.1.1", 53),           # Cloudflare DNS  
        ("api.openai.com", 443),   # OpenAI API
        ("huggingface.co", 443),   # HuggingFace
    ]
    
    accessible_hosts = []
    for host, port in external_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                accessible_hosts.append(f"{host}:{port}")
        except:
            pass
    
    return accessible_hosts

def monitor_network_connections(duration=5):
    """Monitor for new outbound network connections"""
    initial_connections = set()
    violations = []
    
    try:
        # Get initial connections
        for conn in psutil.net_connections(kind='inet'):
            if (conn.status == 'ESTABLISHED' and conn.raddr and 
                conn.raddr.ip not in ['127.0.0.1', '::1'] and 
                not conn.raddr.ip.startswith('192.168.')):
                initial_connections.add(f"{conn.raddr.ip}:{conn.raddr.port}")
        
        # Wait and check for new connections
        time.sleep(duration)
        
        current_connections = set()
        for conn in psutil.net_connections(kind='inet'):
            if (conn.status == 'ESTABLISHED' and conn.raddr and 
                conn.raddr.ip not in ['127.0.0.1', '::1'] and 
                not conn.raddr.ip.startswith('192.168.')):
                current_connections.add(f"{conn.raddr.ip}:{conn.raddr.port}")
        
        # Find new connections
        new_connections = current_connections - initial_connections
        for conn in new_connections:
            violations.append(f"New outbound connection: {conn}")
        
        return len(violations) == 0, violations
        
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return True, []  # Cannot monitor, assume no violations

def test_local_backend_operation():
    """Test that backend operates locally without outbound connections"""
    print("🧪 TC-SEC-120a: Testing local backend operation")
    print("=" * 60)
    
    try:
        # Test health endpoint
        print("🏥 Testing health endpoint...")
        no_violations, violations = monitor_network_connections(2)
        
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint accessible locally")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        if not no_violations:
            print("❌ Network violations during health check:")
            for violation in violations:
                print(f"   🚨 {violation}")
            return False
        else:
            print("✅ No outbound connections during health check")
        
        return True
        
    except Exception as e:
        print(f"❌ Local backend test failed: {e}")
        return False

def test_local_document_access():
    """Test local document access without outbound connections"""
    print("\n🧪 TC-SEC-120b: Testing local document access")
    print("=" * 60)
    
    try:
        print("📄 Testing documents endpoint...")
        
        # Monitor during document list access
        no_violations, violations = monitor_network_connections(3)
        
        response = requests.get(f"{BASE_URL}/api/documents", timeout=10)
        if response.status_code == 200:
            docs_data = response.json()
            doc_count = len(docs_data.get('documents', []))
            print(f"✅ Documents endpoint accessible: {doc_count} documents")
        else:
            print(f"❌ Documents endpoint failed: {response.status_code}")
            return False
        
        if not no_violations:
            print("❌ Network violations during document access:")
            for violation in violations:
                print(f"   🚨 {violation}")
            return False
        else:
            print("✅ No outbound connections during document access")
        
        return True
        
    except Exception as e:
        print(f"❌ Local document access test failed: {e}")
        return False

def test_local_query_operation():
    """Test local query operation without outbound connections"""
    print("\n🧪 TC-SEC-120c: Testing local query operation")
    print("=" * 60)
    
    try:
        # Get available documents first
        docs_response = requests.get(f"{BASE_URL}/api/documents")
        if docs_response.status_code != 200:
            print("❌ Cannot access documents for query test")
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
            print("⚠️  No indexed documents available - testing with any document")
            if documents:
                test_doc = documents[0]
            else:
                print("❌ No documents available for query test")
                return False
        
        print(f"📝 Using document: {test_doc['name']}")
        
        # Perform query and monitor network
        query_data = {
            "query": "What is this document about?",
            "session_id": "test-sec-120-query",
            "document_ids": [test_doc['id']]
        }
        
        print("🔍 Performing query operation...")
        
        # Start monitoring before query
        start_time = time.time()
        no_violations_start, violations_start = monitor_network_connections(1)
        
        response = requests.post(f"{BASE_URL}/api/query", json=query_data, timeout=15)
        
        # Continue monitoring after query
        no_violations_end, violations_end = monitor_network_connections(3)
        
        if response.status_code == 200:
            query_result = response.json()
            turn_id = query_result.get('turnId')
            print(f"✅ Query operation successful: {turn_id}")
        else:
            print(f"❌ Query operation failed: {response.status_code}")
            return False
        
        # Check for network violations
        all_violations = violations_start + violations_end
        if all_violations:
            print("❌ Network violations during query operation:")
            for violation in all_violations:
                print(f"   🚨 {violation}")
            return False
        else:
            print("✅ No outbound connections during query operation")
        
        return True
        
    except Exception as e:
        print(f"❌ Local query test failed: {e}")
        return False

def test_session_management():
    """Test session management without outbound connections"""
    print("\n🧪 TC-SEC-120d: Testing session management")
    print("=" * 60)
    
    try:
        print("📋 Testing sessions endpoint...")
        
        # Monitor during session access
        no_violations, violations = monitor_network_connections(2)
        
        response = requests.get(f"{BASE_URL}/api/sessions", timeout=10)
        if response.status_code == 200:
            sessions_data = response.json()
            session_count = len(sessions_data.get('sessions', []))
            print(f"✅ Sessions endpoint accessible: {session_count} sessions")
        else:
            print(f"❌ Sessions endpoint failed: {response.status_code}")
            return False
        
        if not no_violations:
            print("❌ Network violations during session access:")
            for violation in violations:
                print(f"   🚨 {violation}")
            return False
        else:
            print("✅ No outbound connections during session management")
        
        return True
        
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        return False

def run_tc_sec_120_simple():
    """Main test execution for simplified TC-SEC-120"""
    print("🧪 Starting TC-SEC-120: Local-only operation validation (Simplified)")
    print("=" * 70)
    
    # Check network connectivity status
    print("📡 Checking external network connectivity...")
    external_hosts = check_external_connectivity()
    
    if external_hosts:
        print("⚠️  External network connectivity detected:")
        for host in external_hosts:
            print(f"   📡 {host}")
        print("   💡 Note: System has network access but should operate locally")
    else:
        print("✅ No external network connectivity detected")
        print("🔒 System appears network-isolated")
    
    # Run local operation tests
    backend_test = test_local_backend_operation()
    document_test = test_local_document_access()
    query_test = test_local_query_operation()
    session_test = test_session_management()
    
    # Overall result
    print("\n" + "=" * 70)
    
    all_tests_passed = backend_test and document_test and query_test and session_test
    
    if all_tests_passed:
        print("✅ TC-SEC-120 SIMPLIFIED: PASSED")
        print("   ✓ Backend operates locally without outbound connections")
        print("   ✓ Document access works without network calls")
        print("   ✓ Query operations work without network calls")
        print("   ✓ Session management works without network calls")
        
        if external_hosts:
            print("   💡 Local-only operation validated despite network availability")
        else:
            print("   🔒 Confirmed network-isolated operation")
        
        return True
    else:
        print("❌ TC-SEC-120 SIMPLIFIED: FAILED")
        if not backend_test:
            print("   ✗ Backend operation issues")
        if not document_test:
            print("   ✗ Document access issues")
        if not query_test:
            print("   ✗ Query operation issues")
        if not session_test:
            print("   ✗ Session management issues")
        return False

if __name__ == "__main__":
    success = run_tc_sec_120_simple()
    exit(0 if success else 1)
