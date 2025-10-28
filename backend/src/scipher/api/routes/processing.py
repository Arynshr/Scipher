from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
import logging

from scipher.dependencies import get_db
from scipher.models.database import Document, ProcessingJob
from scipher.models.schemas import StatusResponse, ProcessingJobSchema, ProcessingStatus, DocumentListResponse, DocumentResponse
from scipher.core.exceptions import DocumentNotFoundException

logger = logging.getLogger(__name__)
router = APIRouter(tags=["processing"])

def get_status_message(doc) -> str:
    """Helper function to generate status message based on document status"""
    if doc.status == ProcessingStatus.COMPLETED.value:
        return "Document processing completed successfully"
    elif doc.status == ProcessingStatus.PROCESSING.value:
        return "Document is currently being processed"
    elif doc.status == ProcessingStatus.FAILED.value:
        return f"Document processing failed: {doc.error_message or 'Unknown error'}"
    elif doc.status == ProcessingStatus.UPLOADED.value:
        return "Document uploaded and queued for processing"
    else:
        return f"Document status: {doc.status}"

@router.get("/status/{doc_id}", response_model=StatusResponse)
async def get_processing_status(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get processing status for a document
    
    - **doc_id**: Document ID
    
    Returns current processing status and any error messages
    """
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    stmt = select(Document).filter_by(id=str(doc_uuid))
    doc = (await db.scalars(stmt)).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    return StatusResponse(
        id=doc_uuid,
        status=ProcessingStatus(doc.status),
        message=get_status_message(doc),
        error_message=doc.error_message
    )

@router.get("/jobs/{doc_id}", response_model=List[ProcessingJobSchema])
async def get_processing_jobs(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get processing jobs for a document
    
    - **doc_id**: Document ID
    
    Returns list of processing jobs with their status
    """
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    stmt = select(Document).filter_by(id=str(doc_uuid))
    doc = (await db.scalars(stmt)).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    stmt = select(ProcessingJob).filter_by(document_id=str(doc_uuid))
    jobs = (await db.scalars(stmt)).all()
    
    return [ProcessingJobSchema.from_orm(job) for job in jobs]

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of documents to return"),
    status: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    db: AsyncSession = Depends(get_db)
):
    """
    List documents with their metadata
    
    - **skip**: Number of documents to skip (pagination)
    - **limit**: Maximum number of documents to return (1-100)
    - **status**: Optional filter by processing status
    
    Returns paginated list of documents with metadata
    """
    stmt = select(Document)
    if status:
        stmt = stmt.filter_by(status=status.value)
    
    # Count total for pagination
    count_stmt = select(func.count()).select_from(Document)
    if status:
        count_stmt = count_stmt.filter_by(status=status.value)
    total = (await db.scalar(count_stmt)) or 0
    
    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)
    documents = (await db.scalars(stmt)).all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.from_orm(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit
    )
