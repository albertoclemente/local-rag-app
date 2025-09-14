"""
API routes for the RAG WebApp backend.
Provides REST endpoints for document management, query processing, and system administration.
"""

print("DEBUG: Starting to execute api.py")

import logging
print("DEBUG: After logging import")

import time
print("DEBUG: After time import")
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

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
from app.settings import get_settings
from app.diagnostics import get_logger

# Import services
from app.storage import DocumentStorage, get_document_storage_service
from app.parsing import DocumentParser, get_document_parser_service
from app.chunking import AdaptiveChunker, get_chunking_service
from app.embeddings import get_embedder_service, embed_chunks, get_embedding_info
from app.qdrant_index import get_qdrant_service
from app.retrieval import get_retrieval_service
from app.llm import get_llm_service
from app.ws import store_query

logger = get_logger(__name__)
router = APIRouter()

print(f"DEBUG: Router created successfully in api.py: {router}")

# Simple test endpoint
@router.get("/test")
async def test_endpoint():
    return {"message": "API is working"}
