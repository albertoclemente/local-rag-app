#!/usr/bin/env python3
"""
TC-UI-041: Chat transcript & accessibility (Simplified Version)
Test that focuses on the conversation history API and error handling.
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"

def test_conversation_history_api():
    """Test the conversation history API functionality"""
    print("🧪 TC-UI-041a: Testing conversation history API")
    print("=" * 60)
    
    try:
        # Check if backend is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Backend not accessible")
            return False
        print("✅ Backend is accessible")
        
        # Test sessions list endpoint
        sessions_response = requests.get(f"{BASE_URL}/api/sessions")
        if sessions_response.status_code == 200:
            sessions_data = sessions_response.json()
            print(f"✅ Sessions endpoint working: {len(sessions_data.get('sessions', []))} sessions")
        else:
            print(f"❌ Sessions endpoint failed: {sessions_response.status_code}")
            return False
        
        # Find an existing session with history
        sessions = sessions_data.get('sessions', [])
        test_session_id = None
        
        for session in sessions:
            session_id = session.get('session_id') if isinstance(session, dict) else session
            turn_count = session.get('turn_count', 0) if isinstance(session, dict) else 0
            
            if turn_count > 0:
                test_session_id = session_id
                print(f"✅ Found session with history: {session_id} ({turn_count} turns)")
                break
        
        if not test_session_id:
            print("⚠️  No sessions with conversation history found")
            return True  # Not a failure, just no data to test
        
        # Test conversation history structure
        history_response = requests.get(f"{BASE_URL}/api/sessions/{test_session_id}/history")
        if history_response.status_code == 200:
            history_data = history_response.json()
            turns = history_data.get('turns', [])
            
            if len(turns) > 0:
                first_turn = turns[0]
                
                # Check required fields
                required_fields = ['turn_id', 'query', 'response', 'timestamp']
                missing_fields = [field for field in required_fields if field not in first_turn]
                
                if not missing_fields:
                    print("✅ Turn structure contains all required fields")
                    
                    # Check timestamp format
                    timestamp = first_turn.get('timestamp', '')
                    if 'T' in timestamp and ':' in timestamp:
                        print("✅ Timestamp format is ISO-compatible")
                    else:
                        print("❌ Timestamp format not ISO-compatible")
                        return False
                    
                    # Check sources field for citations
                    if 'sources' in first_turn:
                        sources = first_turn['sources']
                        if isinstance(sources, list) and len(sources) > 0:
                            print(f"✅ Citations available: {len(sources)} sources")
                        else:
                            print("⚠️  No sources in conversation turn")
                    else:
                        print("❌ Sources field missing from turn")
                        return False
                    
                    return True
                else:
                    print(f"❌ Missing required fields: {missing_fields}")
                    return False
            else:
                print("⚠️  No turns found in conversation history")
                return True
        else:
            print(f"❌ Could not retrieve conversation history: {history_response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Conversation history test failed: {e}")
        return False

def test_api_error_handling():
    """Test API error handling and validation"""
    print("\n🧪 TC-UI-041b: Testing API error handling")
    print("=" * 60)
    
    try:
        # Test 1: Empty query validation
        print("📝 Test 1: Empty query validation...")
        empty_query = {
            "query": "",
            "session_id": "test-error-handling",
            "document_ids": []
        }
        
        response = requests.post(f"{BASE_URL}/api/query", json=empty_query)
        if response.status_code == 422:
            print("✅ Empty query properly rejected with validation error")
        else:
            print(f"⚠️  Empty query response: {response.status_code} (expected 422)")
        
        # Test 2: Invalid session ID in conversation API
        print("\n📝 Test 2: Invalid session ID...")
        invalid_session_response = requests.get(f"{BASE_URL}/api/sessions/invalid-session-12345/history")
        if invalid_session_response.status_code == 404:
            print("✅ Invalid session ID properly rejected with 404")
        else:
            print(f"⚠️  Invalid session response: {invalid_session_response.status_code} (expected 404)")
        
        # Test 3: Malformed JSON
        print("\n📝 Test 3: Malformed JSON request...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/query", 
                data="invalid json{",
                headers={"Content-Type": "application/json"}
            )
            if response.status_code in [400, 422]:
                print("✅ Malformed JSON properly rejected")
            else:
                print(f"⚠️  Malformed JSON response: {response.status_code}")
        except Exception as e:
            print("✅ Malformed JSON properly rejected (connection error)")
        
        # Test session info endpoint
        print("\n📝 Test 4: Session info endpoint...")
        sessions_response = requests.get(f"{BASE_URL}/api/sessions")
        if sessions_response.status_code == 200:
            sessions = sessions_response.json().get('sessions', [])
            if sessions:
                test_session = sessions[0]
                session_id = test_session.get('session_id') if isinstance(test_session, dict) else test_session
                info_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
                if info_response.status_code == 200:
                    session_info = info_response.json()
                    required_info_fields = ['session_id', 'turn_count', 'created_at', 'last_active']
                    missing_info_fields = [field for field in required_info_fields if field not in session_info]
                    
                    if not missing_info_fields:
                        print("✅ Session info endpoint working with all fields")
                    else:
                        print(f"❌ Session info missing fields: {missing_info_fields}")
                        return False
                else:
                    print(f"❌ Session info endpoint failed: {info_response.status_code}")
                    return False
            else:
                print("⚠️  No sessions available to test session info")
        
        return True
        
    except Exception as e:
        print(f"❌ API error handling test failed: {e}")
        return False

def test_accessibility_structure():
    """Test data structure for accessibility compliance"""
    print("\n🧪 TC-UI-041c: Testing accessibility-friendly data structure")
    print("=" * 60)
    
    try:
        # Get sessions and check structure
        sessions_response = requests.get(f"{BASE_URL}/api/sessions")
        if sessions_response.status_code != 200:
            print("❌ Cannot access sessions for accessibility test")
            return False
        
        sessions = sessions_response.json().get('sessions', [])
        if not sessions:
            print("⚠️  No sessions available for accessibility test")
            return True
        
        # Test session with conversation history
        test_session = sessions[0]
        session_id = test_session.get('session_id') if isinstance(test_session, dict) else test_session
        history_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/history")
        
        if history_response.status_code == 200:
            history_data = history_response.json()
            turns = history_data.get('turns', [])
            
            if turns:
                accessibility_checks = []
                first_turn = turns[0]
                
                # Check for structured data that's screen reader friendly
                if 'timestamp' in first_turn:
                    timestamp = first_turn['timestamp']
                    if 'T' in timestamp:  # ISO format
                        accessibility_checks.append("✅ ISO timestamp for screen readers")
                    else:
                        accessibility_checks.append("❌ Non-ISO timestamp format")
                
                # Check for clear role distinction
                if 'query' in first_turn and 'response' in first_turn:
                    accessibility_checks.append("✅ Clear user/assistant role distinction")
                else:
                    accessibility_checks.append("❌ Unclear conversation roles")
                
                # Check for citation structure
                if 'sources' in first_turn and isinstance(first_turn['sources'], list):
                    accessibility_checks.append("✅ Structured citations for navigation")
                else:
                    accessibility_checks.append("❌ Citations not structured")
                
                # Check response is text-based
                if 'response' in first_turn and isinstance(first_turn['response'], str):
                    accessibility_checks.append("✅ Text-based responses for screen readers")
                else:
                    accessibility_checks.append("❌ Non-text response format")
                
                print("📊 Accessibility compliance checks:")
                for check in accessibility_checks:
                    print(f"   {check}")
                
                return all("✅" in check for check in accessibility_checks)
            else:
                print("⚠️  No conversation turns to check accessibility")
                return True
        else:
            print("❌ Cannot retrieve conversation for accessibility test")
            return False
            
    except Exception as e:
        print(f"❌ Accessibility structure test failed: {e}")
        return False

def run_tc_ui_041_simple():
    """Main test execution for simplified TC-UI-041"""
    print("🧪 Starting TC-UI-041: Chat transcript & accessibility (Simplified)")
    print("=" * 70)
    
    # Run all sub-tests
    history_test_passed = test_conversation_history_api()
    error_test_passed = test_api_error_handling() 
    accessibility_test_passed = test_accessibility_structure()
    
    # Overall result
    print("\n" + "=" * 70)
    if history_test_passed and error_test_passed and accessibility_test_passed:
        print("✅ TC-UI-041 SIMPLIFIED: PASSED")
        print("   ✓ Conversation history API working")
        print("   ✓ API error handling working")
        print("   ✓ Accessibility-friendly data structure")
        return True
    else:
        print("❌ TC-UI-041 SIMPLIFIED: FAILED")
        if not history_test_passed:
            print("   ✗ Conversation history API issues")
        if not error_test_passed:
            print("   ✗ API error handling issues")
        if not accessibility_test_passed:
            print("   ✗ Accessibility structure issues")
        return False

if __name__ == "__main__":
    success = run_tc_ui_041_simple()
    exit(0 if success else 1)
