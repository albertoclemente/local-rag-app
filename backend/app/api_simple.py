#!/usr/bin/env python3
"""
Simple API endpoint for document upload with duplicate detection
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from typing import Optional
import hashlib

from app.models import DocumentUploadResponse
from app.storage import get_document_storage_service
from app.diagnostics import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    storage=Depends(get_document_storage_service)
) -> DocumentUploadResponse:
    """
    Upload a document for processing with duplicate detection.
    """
    try:
        logger.info(f"Uploading document: {file.filename}")
        
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['pdf', 'txt', 'docx', 'md', 'epub']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}"
            )
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Read file content
        file_content = await file.read()
        
        # Calculate file hash to check for duplicates
        sha256_hash = hashlib.sha256()
        sha256_hash.update(file_content)
        file_hash = sha256_hash.hexdigest()
        
        # Check for duplicates before storing
        existing_doc = await storage.find_duplicate_by_hash(file_hash)
        
        if existing_doc:
            logger.info(f"Duplicate file detected: {file.filename} matches existing document {existing_doc.id}")
            return DocumentUploadResponse(
                document=existing_doc,
                message="Document already exists (duplicate detected)",
                is_duplicate=True
            )
        
        # Store the uploaded file (no duplicate found)
        document = await storage.store_uploaded_file(
            file_content=file_content,
            filename=file.filename,
            tags=tag_list
        )
        
        logger.info(f"Document uploaded successfully: {document.id}")
        return DocumentUploadResponse(
            document=document,
            message="Document uploaded successfully",
            is_duplicate=False
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@router.get("/documents")
async def list_documents(storage=Depends(get_document_storage_service)):
    """List all documents."""
    try:
        documents = await storage.list_documents()
        return {"documents": documents, "total": len(documents)}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
