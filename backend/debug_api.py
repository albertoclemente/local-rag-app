#!/usr/bin/env python3
"""
Debug script to isolate the app.api import issue
"""

import sys
import traceback

def test_import_sections():
    """Test each section of app.api imports separately"""
    
    print("Testing imports from app.api step by step...")
    
    try:
        print("\n1. Testing basic imports...")
        import logging
        import time
        import uuid
        from pathlib import Path
        from typing import List, Optional
        print("✓ Basic imports successful")
        
        print("\n2. Testing FastAPI imports...")
        from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
        from fastapi.responses import JSONResponse
        print("✓ FastAPI imports successful")
        
        print("\n3. Testing app.models imports...")
        from app.models import (
            Document,
            DocumentListResponse,
            DocumentUpdateRequest,
            DocumentReindexRequest,
            DocumentUploadResponse,
            QueryRequest,
            QueryResponse,
            Settings,
            SystemStatus,
            ErrorResponse
        )
        print("✓ app.models imports successful")
        
        print("\n4. Testing app.settings and diagnostics...")
        from app.settings import get_settings
        from app.diagnostics import get_logger
        print("✓ app.settings and diagnostics imports successful")
        
        print("\n5. Testing service imports...")
        from app.storage import DocumentStorage, get_document_storage_service
        from app.parsing import DocumentParser, get_document_parser_service
        from app.chunking import AdaptiveChunker, get_chunking_service
        from app.embeddings import get_embedder_service, embed_chunks, get_embedding_info
        from app.qdrant_index import get_qdrant_service
        from app.retrieval import get_retrieval_service
        from app.llm import get_llm_service
        from app.ws import store_query
        print("✓ All service imports successful")
        
        print("\n6. Testing logger and router creation...")
        logger = get_logger(__name__)
        router = APIRouter()
        print("✓ Logger and router creation successful")
        print(f"Router object: {router}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed at step: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import_sections()
    if success:
        print("\n✅ All imports successful - the issue is elsewhere")
    else:
        print("\n❌ Found the problematic import")
