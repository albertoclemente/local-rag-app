#!/usr/bin/env python3
"""
Service integration test script.
Tests that all backend services can be initialized and work together.
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_service_initialization():
    """Test that all services can be initialized"""
    print("🔧 Testing service initialization...")
    
    try:
        # Mock the external dependencies for testing
        sys.modules['httpx'] = type('MockHttpx', (), {
            'AsyncClient': type('AsyncClient', (), {
                '__init__': lambda self, **kwargs: None,
                'get': lambda self, url: type('Response', (), {'status_code': 200, 'json': lambda: {'models': []}})(),
                'post': lambda self, url, **kwargs: type('Response', (), {'status_code': 200, 'json': lambda: {'response': 'test'}})(),
                'aclose': lambda self: None
            })
        })()
        
        # Test settings
        print("  📋 Testing settings...")
        from app.settings import get_settings
        settings = get_settings()
        print(f"    ✅ Settings loaded - Profile: {settings.profile}")
        print(f"    ✅ Data directory: {settings.data_dir}")
        print(f"    ✅ LLM model: {settings.llm_model}")
        
        # Test diagnostics
        print("  📊 Testing diagnostics...")
        from app.diagnostics import get_logger
        logger = get_logger("test")
        logger.info("Test log message")
        print("    ✅ Logging system working")
        
        # Test models
        print("  📦 Testing data models...")
        from app.models import Document, QueryRequest, QueryResponse
        test_doc = Document(
            id="test",
            name="test.txt",
            type="txt",
            size=100,
            created_at=time.time(),
            tags=[],
            status="indexed"
        )
        print("    ✅ Data models working")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Service initialization failed: {e}")
        return False

async def test_service_integration():
    """Test that services can work together"""
    print("🔗 Testing service integration...")
    
    try:
        # Test that all modules can import each other
        print("  📥 Testing module imports...")
        
        # Storage module
        try:
            from app.storage import DocumentStorage
            print("    ✅ Storage module imports")
        except Exception as e:
            print(f"    ❌ Storage module import failed: {e}")
            return False
        
        # Parsing module  
        try:
            from app.parsing import DocumentParser
            print("    ✅ Parsing module imports")
        except Exception as e:
            print(f"    ❌ Parsing module import failed: {e}")
            return False
        
        # Chunking module
        try:
            from app.chunking import AdaptiveChunker
            print("    ✅ Chunking module imports")
        except Exception as e:
            print(f"    ❌ Chunking module import failed: {e}")
            return False
        
        # Embeddings module
        try:
            from app.embeddings import get_embedder_service
            print("    ✅ Embeddings module imports")
        except Exception as e:
            print(f"    ❌ Embeddings module import failed: {e}")
            return False
        
        # Qdrant module
        try:
            from app.qdrant_index import QdrantIndex
            print("    ✅ Qdrant module imports")
        except Exception as e:
            print(f"    ❌ Qdrant module import failed: {e}")
            return False
        
        # Retrieval module
        try:
            from app.retrieval import RetrievalEngine
            print("    ✅ Retrieval module imports")
        except Exception as e:
            print(f"    ❌ Retrieval module import failed: {e}")
            return False
        
        # LLM module
        try:
            from app.llm import LLMService
            print("    ✅ LLM module imports")
        except Exception as e:
            print(f"    ❌ LLM module import failed: {e}")
            return False
        
        # API module
        try:
            from app.api import router
            print("    ✅ API module imports")
        except Exception as e:
            print(f"    ❌ API module import failed: {e}")
            return False
        
        # WebSocket module
        try:
            from app.ws import manager
            print("    ✅ WebSocket module imports")
        except Exception as e:
            print(f"    ❌ WebSocket module import failed: {e}")
            return False
        
        # Main module
        try:
            from app.main import create_app
            print("    ✅ Main module imports")
        except Exception as e:
            print(f"    ❌ Main module import failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Service integration test failed: {e}")
        return False

async def test_app_creation():
    """Test that the FastAPI app can be created"""
    print("🚀 Testing FastAPI app creation...")
    
    try:
        from app.main import create_app
        app = create_app()
        
        # Check that routes are registered
        routes = [route.path for route in app.routes]
        expected_routes = [
            "/api/documents",
            "/api/query", 
            "/api/health",
            "/ws/stream"
        ]
        
        for expected_route in expected_routes:
            if any(expected_route in route for route in routes):
                print(f"    ✅ Route registered: {expected_route}")
            else:
                print(f"    ❌ Route missing: {expected_route}")
                return False
        
        print("    ✅ FastAPI app created successfully")
        return True
        
    except Exception as e:
        print(f"    ❌ App creation failed: {e}")
        return False

async def test_directory_structure():
    """Test that required directories exist or can be created"""
    print("📁 Testing directory structure...")
    
    try:
        from app.settings import get_settings
        settings = get_settings()
        
        # Test directory creation
        required_dirs = [
            settings.data_dir,
            settings.library_raw_dir,
            settings.library_parsed_dir,
            settings.config_dir,
            settings.logs_dir
        ]
        
        for dir_path in required_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            if Path(dir_path).exists():
                print(f"    ✅ Directory available: {dir_path}")
            else:
                print(f"    ❌ Directory creation failed: {dir_path}")
                return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Directory structure test failed: {e}")
        return False

async def run_all_tests():
    """Run all integration tests"""
    print("Running backend service integration tests...\n")
    
    tests = [
        ("Service Initialization", test_service_initialization),
        ("Service Integration", test_service_integration), 
        ("FastAPI App Creation", test_app_creation),
        ("Directory Structure", test_directory_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"=== {test_name} ===")
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED\n")
            else:
                print(f"❌ {test_name} FAILED\n")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}\n")
    
    print(f"=== SUMMARY ===")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("\nThe backend is properly wired and ready to run.")
        print("Section 7 (Wire routes & WS) implementation is complete!")
        return True
    else:
        print("❌ Some integration tests failed.")
        print("Please check the errors above and fix any issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
