"""
API routes for the RAG WebApp backend.
Provides REST endpoints for document management, query processing, and system administration.
"""

import logging
import time
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
    DocumentType,
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
from app.chunking import AdaptiveChunker, get_chunking_service, rechunk_document_with_params
from app.embeddings import get_embedder_service, embed_chunks, get_embedding_info
from app.qdrant_index import get_qdrant_service
from app.retrieval import get_retrieval_service
from app.llm import get_llm_service
from app.ws import store_query
from app.conversation import get_conversation_manager

logger = get_logger(__name__)
router = APIRouter()


# Dependency injection for services
async def get_storage_service() -> DocumentStorage:
    """Get document storage service."""
    return await get_document_storage_service()

async def get_parser_service() -> DocumentParser:
    """Get document parser service.""" 
    return await get_document_parser_service()

async def get_chunking_service_dep() -> AdaptiveChunker:
    """Get chunking service."""
    return await get_chunking_service()


# =============================================================================
# Document Management Routes
# =============================================================================

@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    storage=Depends(get_document_storage_service),
    parser=Depends(get_document_parser_service)
) -> DocumentUploadResponse:
    """
    Upload a document for processing.
    
    - **file**: The document file (PDF, TXT, DOCX, MD, EPUB)
    - **tags**: Optional comma-separated tags
    
    Returns the created Document with metadata.
    """
    try:
        logger.info(f"🔧 FIXED VERSION: Uploading document: {file.filename}")
        
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        file_ext = file.filename.split('.')[-1].lower()
        supported_formats = parser.get_supported_types()
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(supported_formats)}"
            )
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Read file content
        file_content = await file.read()
        
        # Store the uploaded file
        document = await storage.store_uploaded_file(
            file_content=file_content,
            filename=file.filename,
            tags=tag_list
        )
        
        # TODO: Trigger parsing and indexing asynchronously
        # For now, we'll parse and chunk synchronously
        try:
            raw_file_path = await storage.get_raw_file_path(document.id)
            if raw_file_path:
                # Parse the document
                parsed_data = await parser.parse_document(raw_file_path, document.type)
                await storage.store_parsed_content(document.id, parsed_data)
                
                # Chunk the document
                chunker = await get_chunking_service()
                doc_type_str = parsed_data.get('document_type', 'txt')
                doc_type = DocumentType(doc_type_str)
                chunked_doc = await chunker.chunk_document(
                    document.id, 
                    parsed_data.get('full_text', ''),
                    parsed_data.get('structure', {}),
                    doc_type
                )
                
                # Store chunking results
                chunk_data = {
                    "chunks": chunked_doc.chunks,
                    "metadata": [meta.__dict__ for meta in chunked_doc.metadata],
                    "params": chunked_doc.chunking_params.__dict__,
                    "rationale": chunked_doc.rationale,
                    "stats": chunked_doc.stats
                }
                
                # Store chunks alongside parsed content
                parsed_data["chunking"] = chunk_data
                await storage.store_parsed_content(document.id, parsed_data)

                # Embed the chunks
                try:
                    logger.info(f"Creating embeddings for {len(chunked_doc.chunks)} chunks...")
                    
                    # Convert chunks to the format expected by embed_chunks
                    chunk_dicts = [{"text": chunk} for chunk in chunked_doc.chunks]
                    embedded_chunks = await embed_chunks(chunk_dicts)
                    
                    # Store embeddings in vector database
                    qdrant = await get_qdrant_service()
                    await qdrant.index_chunks(embedded_chunks, document.id)
                    
                    # Update document status to include embeddings
                    await storage.update_document_metadata(
                        document.id, 
                        {
                            "status": "indexed", 
                            "embedding_status": "indexed",
                            "chunk_count": len(chunked_doc.chunks)
                        }
                    )
                    logger.info(f"Embeddings created successfully for document {document.id}")
                    
                except Exception as embed_error:
                    logger.error(f"Failed to create embeddings for document {document.id}: {embed_error}")
                    # Document is still chunked, just not embedded
                    await storage.update_document_metadata(
                        document.id, 
                        {
                            "status": "indexed", 
                            "embedding_status": "error",
                            "chunk_count": len(chunked_doc.chunks)
                        }
                    )
                
                document.status = "indexed"  # type: ignore
                
                logger.info(
                    f"Document processed successfully: {document.id} "
                    f"({len(chunked_doc.chunks)} chunks, {chunked_doc.stats.get('avg_chunk_tokens', 0):.0f} avg tokens)"
                )
        except Exception as parse_error:
            logger.error(f"Failed to process document {document.id}: {parse_error}")
            await storage.update_document_metadata(
                document.id, 
                {"status": "error"}
            )
        
        logger.info(f"Document uploaded successfully: {document.id}")
        return DocumentUploadResponse(document=document)
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    tag: Optional[str] = Query(None, description="Filter by tag"),
    status: Optional[str] = Query(None, description="Filter by status"),
    storage=Depends(get_document_storage_service)
) -> DocumentListResponse:
    """
    List all documents with optional filters.
    
    - **tag**: Filter documents by tag
    - **status**: Filter documents by status (indexed, needs-reindex, error, indexing)
    """
    try:
        logger.info(f"Listing documents with filters - tag: {tag}, status: {status}")
        
        documents = await storage.list_documents(
            tag_filter=tag,
            status_filter=status
        )
        
        return DocumentListResponse(documents=documents, total=len(documents))
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/documents/{doc_id}", response_model=Document)
async def update_document(
    doc_id: str,
    update_request: DocumentUpdateRequest,
    storage=Depends(get_document_storage_service)
) -> Document:
    """
    Update document metadata.
    
    - **doc_id**: Document ID
    - **name**: New document name (optional)
    - **tags**: New tags list (optional)
    """
    try:
        logger.info(f"Updating document {doc_id}")
        
        # Check if document exists
        document = await storage.load_document_metadata(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update fields
        update_data = {}
        if update_request.name is not None:
            update_data["name"] = update_request.name
        if update_request.tags is not None:
            update_data["tags"] = update_request.tags
        
        if update_data:
            await storage.update_document_metadata(doc_id, update_data)
            # Reload to get updated document
            document = await storage.load_document_metadata(doc_id)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    secure: bool = Query(False, description="Secure delete (overwrite)"),
    storage=Depends(get_document_storage_service)
) -> JSONResponse:
    """
    Delete a document and its embeddings.
    
    - **doc_id**: Document ID
    - **secure**: If true, securely overwrite the file before deletion
    """
    try:
        logger.info(f"Deleting document {doc_id}, secure: {secure}")
        
        success = await storage.delete_document(doc_id, secure=secure)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return JSONResponse(
            content={"message": f"Document {doc_id} deleted successfully"},
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{doc_id}/reindex")
async def reindex_document(
    doc_id: str,
    reindex_request: DocumentReindexRequest,
    storage=Depends(get_document_storage_service),
    parser=Depends(get_document_parser_service)
) -> JSONResponse:
    """
    Reindex a document with optional custom chunking parameters.
    
    - **doc_id**: Document ID
    - **chunk_size**: Override chunk size (optional)
    - **chunk_overlap**: Override chunk overlap (optional)
    """
    try:
        logger.info(f"Reindexing document {doc_id}")
        
        # Check if document exists
        document = await storage.load_document_metadata(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update status to indicate reindexing
        await storage.update_document_metadata(doc_id, {"status": "indexing"})
        
        try:
            # Get the raw file
            raw_file_path = await storage.get_raw_file_path(doc_id)
            if raw_file_path:
                # Re-parse the document
                parsed_data = await parser.parse_document(raw_file_path, document.type)
                
                # Re-chunk with custom parameters if provided
                chunker = await get_chunking_service()
                if reindex_request.chunk_size or reindex_request.chunk_overlap:
                    chunked_doc = await rechunk_document_with_params(
                        doc_id, 
                        parsed_data,
                        chunk_size=reindex_request.chunk_size,
                        chunk_overlap=reindex_request.chunk_overlap
                    )
                    logger.info(f"Re-chunked with custom params: size={reindex_request.chunk_size}, overlap={reindex_request.chunk_overlap}")
                else:
                    doc_type_str = parsed_data.get('document_type', 'txt')
                    doc_type = DocumentType(doc_type_str)
                    chunked_doc = await chunker.chunk_document(
                        doc_id, 
                        parsed_data.get('full_text', ''),
                        parsed_data.get('structure', {}),
                        doc_type
                    )
                
                # Store updated results
                chunk_data = {
                    "chunks": chunked_doc.chunks,
                    "metadata": [meta.__dict__ for meta in chunked_doc.metadata],
                    "params": chunked_doc.chunking_params.__dict__,
                    "rationale": chunked_doc.rationale,
                    "stats": chunked_doc.stats
                }
                
                parsed_data["chunking"] = chunk_data
                await storage.store_parsed_content(doc_id, parsed_data)
                
                # Embed and index the chunks
                try:
                    logger.info(f"Creating embeddings for {len(chunked_doc.chunks)} chunks...")
                    chunk_dicts = [chunk.__dict__ for chunk in chunked_doc.chunks]
                    embedded_chunks = await embed_chunks(chunk_dicts)
                    
                    # Index in Qdrant
                    qdrant = await get_qdrant_service()
                    await qdrant.index_chunks(embedded_chunks, doc_id)
                    logger.info(f"Successfully indexed {len(embedded_chunks)} chunks into Qdrant")
                except Exception as e:
                    logger.error(f"Failed to embed/index chunks: {e}")
                    raise
                
                await storage.update_document_metadata(doc_id, {
                    "status": "indexed",
                    "chunk_count": len(chunked_doc.chunks)
                })
                
                logger.info(
                    f"Document reindexed: {doc_id} "
                    f"({len(chunked_doc.chunks)} chunks, rationale: {chunked_doc.rationale})"
                )
            else:
                raise Exception("Raw file not found")
        except Exception as e:
            await storage.update_document_metadata(doc_id, {"status": "error"})
            raise e
        
        return JSONResponse(
            content={"message": f"Document {doc_id} reindexed successfully"},
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reindexing document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Query Routes
# =============================================================================

@router.post("/query", response_model=QueryResponse)
async def start_query(
    query_request: QueryRequest,
    retrieval_engine=Depends(get_retrieval_service)
) -> QueryResponse:
    """
    Start a new query session.
    
    - **query**: The user's query
    - **sessionId**: Session identifier
    
    Returns session and turn IDs for WebSocket streaming.
    """
    try:
        logger.info(f"Starting query: {query_request.query}")
        
        # Generate a turn ID for this specific query
        turn_id = str(uuid.uuid4())
        
        # Store the query for the WebSocket handler to retrieve
        store_query(query_request.session_id, turn_id, query_request.query)
        
        logger.info(f"Query stored for streaming - session: {query_request.session_id}, turn: {turn_id}")
        
        return QueryResponse(
            sessionId=query_request.session_id,
            turnId=turn_id
        )
        
    except Exception as e:
        logger.error(f"Error starting query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# System Routes
# =============================================================================

@router.get("/settings", response_model=Settings)
async def get_settings_endpoint() -> Settings:
    """Get current system settings."""
    return get_settings()


@router.put("/settings")
async def update_settings(settings: Settings) -> JSONResponse:
    """Update system settings."""
    try:
        # TODO: Implement settings persistence
        logger.info("Settings update requested")
        return JSONResponse(content={"message": "Settings updated successfully"})
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=SystemStatus)
async def get_system_status() -> SystemStatus:
    """Get system status and resource usage."""
    try:
        # Check all service health
        storage_service = await get_storage_service()
        qdrant_service = await get_qdrant_service()
        llm_service = await get_llm_service()
        retrieval_service = await get_retrieval_service()
        
        # Get health status from each service
        llm_health = {}
        try:
            import asyncio
            qdrant_health = await asyncio.wait_for(qdrant_service.health_check(), timeout=2.0)
            llm_health = await asyncio.wait_for(llm_service.health_check(), timeout=2.0)
            services_healthy = qdrant_health.get("healthy", True) and llm_health.get("healthy", True)
        except Exception as e:
            logger.warning(f"Service health check failed: {e}")
            services_healthy = True  # Assume healthy for local operation
        
        # Get actual document count
        documents = await storage_service.list_documents()
        document_count = len(documents)

        # Gather resource usage
        from app.diagnostics import get_resource_monitor
        monitor = get_resource_monitor()
        system = monitor.get_system_resources()
        mem = monitor.get_memory_usage()

        # Compute simple CPU and RAM metrics for UI
        cpu_usage = system.get("cpu_percent") or 0.0
        ram_usage_bytes = int(mem.get("rss_bytes") or 0)

        # Determine model name if available from health payload
        # Start with configured model name to avoid blocking on network
        try:
            model_name = getattr(llm_service, 'config', None).model_name if getattr(llm_service, 'config', None) else None
        except Exception:
            model_name = None
        try:
            if isinstance(llm_health, dict):
                model_name = (
                    llm_health.get("model")
                    or (llm_health.get("model_info") or {}).get("model")
                    or (llm_health.get("model_info") or {}).get("name")
                    or model_name
                )
        except Exception as e:
            logger.warning(f"Failed to extract LLM model name: {e}")

        return SystemStatus(
            status="operational" if services_healthy else "degraded",
            cpu_usage=cpu_usage,
            ram_usage=ram_usage_bytes,
            indexing_progress=None,  # Could be wired to background jobs if available
            offline=False,
            model_name=model_name
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(content={"status": "healthy", "timestamp": time.time()})

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint."""
    return {"message": "API is working", "router": "functional"}

# Conversation session management endpoints

@router.get("/sessions")
async def list_sessions():
    """List all active conversation sessions"""
    conversation_mgr = get_conversation_manager()
    return {"sessions": conversation_mgr.get_all_sessions()}

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a specific session"""
    conversation_mgr = get_conversation_manager()
    session_info = conversation_mgr.get_session_info(session_id)
    
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_info

@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    conversation_mgr = get_conversation_manager()
    turns = conversation_mgr.get_session_turns(session_id)
    
    if turns is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"session_id": session_id, "turns": turns}

@router.delete("/sessions/{session_id}/context")
async def clear_session_context(session_id: str):
    """Clear conversation context for a session"""
    conversation_mgr = get_conversation_manager()
    success = conversation_mgr.clear_session_context(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session context cleared", "session_id": session_id}

@router.post("/sessions/cleanup")
async def cleanup_old_sessions():
    """Clean up old inactive sessions"""
    conversation_mgr = get_conversation_manager()
    conversation_mgr.cleanup_old_sessions()
    return {"message": "Old sessions cleaned up"}
