from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from scipher.dependencies import get_db, get_validator
from scipher.core.validator import DocumentValidator
from scipher.models.database import Document
from scipher.models.schemas import StatusResponse, DocumentResponse, DocumentListResponse
from scipher.core.exceptions import DocumentNotFoundException
from scipher.utils.response_utils import response_formatter

router = APIRouter(prefix="/api", tags=["processing"])


@router.get("/status/{doc_id}", response_model=StatusResponse)
async def get_processing_status(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    Get processing status of a specific document
    
    - **doc_id**: Document ID
    
    Returns current processing status and message
    """
    
    doc = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    # Get human-readable status message
    message = response_formatter.status_message_mapper(doc.status)
    
    return StatusResponse(
        id=doc.id,
        status=doc.status,
        message=message,
        error_message=doc.error_message
    )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return"),
    status: str = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    validator: DocumentValidator = Depends(get_validator)
):
    """
    List all uploaded documents with pagination
    
    - **skip**: Offset for pagination (default: 0)
    - **limit**: Max results per page (default: 10, max: 100)
    - **status**: Filter by processing status (optional)
    
    Returns paginated list of documents
    """
    
    # Validate pagination parameters
    skip, limit = validator.validate_pagination(skip, limit)
    
    # Build query
    query = db.query(Document)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Document.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    documents = query.order_by(Document.upload_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return DocumentListResponse(
        documents=documents,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/documents/stats")
async def get_document_statistics(
    db: Session = Depends(get_db)
):
    """
    Get statistics about documents
    
    Returns counts by status and total size
    """
    from sqlalchemy import func
    from scipher.models.schemas import ProcessingStatus
    
    # Count by status
    status_counts = {}
    for status in ProcessingStatus:
        count = db.query(Document).filter(Document.status == status.value).count()
        status_counts[status.value] = count
    
    # Total documents
    total_documents = db.query(Document).count()
    
    # Total file size
    total_size = db.query(func.sum(Document.file_size)).scalar() or 0
    
    return {
        "total_documents": total_documents,
        "status_counts": status_counts,
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }
