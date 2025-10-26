from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
import logging

from scipher.dependencies import get_db
from scipher.models.database import Document, ProcessingJob
from scipher.models.schemas import StatusResponse, ProcessingJobSchema, ProcessingStatus
from scipher.core.exceptions import DocumentNotFoundException

logger = logging.getLogger(__name__)
router = APIRouter(tags=["processing"])


@router.get("/status/{doc_id}", response_model=StatusResponse)
async def get_processing_status(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    Get processing status for a document
    
    - **doc_id**: Document ID
    
    Returns current processing status and any error messages
    """
    
    # Convert string to UUID
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    # Get document
    doc = db.query(Document).filter(Document.id == str(doc_uuid)).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    # Determine status message
    if doc.status == ProcessingStatus.COMPLETED.value:
        message = "Document processing completed successfully"
    elif doc.status == ProcessingStatus.PROCESSING.value:
        message = "Document is currently being processed"
    elif doc.status == ProcessingStatus.FAILED.value:
        message = f"Document processing failed: {doc.error_message or 'Unknown error'}"
    elif doc.status == ProcessingStatus.UPLOADED.value:
        message = "Document uploaded and queued for processing"
    else:
        message = f"Document status: {doc.status}"
    
    return StatusResponse(
        id=doc_uuid,
        status=ProcessingStatus(doc.status),
        message=message,
        error_message=doc.error_message
    )


@router.get("/jobs/{doc_id}", response_model=List[ProcessingJobSchema])
async def get_processing_jobs(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    Get processing jobs for a document
    
    - **doc_id**: Document ID
    
    Returns list of processing jobs with their status
    """
    
    # Convert string to UUID
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    # Get document
    doc = db.query(Document).filter(Document.id == str(doc_uuid)).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    # Get processing jobs
    jobs = db.query(ProcessingJob).filter(ProcessingJob.document_id == str(doc_uuid)).all()
    
    return [
        ProcessingJobSchema(
            id=job.id,
            document_id=job.document_id,
            job_type=job.job_type,
            status=job.status,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )
        for job in jobs
    ]


@router.get("/documents", response_model=List[StatusResponse])
async def list_documents_status(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of documents to return"),
    status: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    db: Session = Depends(get_db)
):
    """
    List documents with their processing status
    
    - **skip**: Number of documents to skip (pagination)
    - **limit**: Maximum number of documents to return (1-100)
    - **status**: Optional filter by processing status
    
    Returns list of documents with their current status
    """
    
    # Build query
    query = db.query(Document)
    
    if status:
        query = query.filter(Document.status == status.value)
    
    # Apply pagination
    documents = query.offset(skip).limit(limit).all()
    
    # Convert to StatusResponse
    results = []
    for doc in documents:
        if doc.status == ProcessingStatus.COMPLETED.value:
            message = "Document processing completed successfully"
        elif doc.status == ProcessingStatus.PROCESSING.value:
            message = "Document is currently being processed"
        elif doc.status == ProcessingStatus.FAILED.value:
            message = f"Document processing failed: {doc.error_message or 'Unknown error'}"
        elif doc.status == ProcessingStatus.UPLOADED.value:
            message = "Document uploaded and queued for processing"
        else:
            message = f"Document status: {doc.status}"
        
        results.append(StatusResponse(
            id=doc.id,
            status=ProcessingStatus(doc.status),
            message=message,
            error_message=doc.error_message
        ))
    
    return results
