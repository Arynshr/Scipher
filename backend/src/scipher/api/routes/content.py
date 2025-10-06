from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import logging  # For proper logging

from scipher.dependencies import get_db, get_file_manager, get_document_processor
from scipher.utils.file_utils import FileManager
from scipher.core.document_processor import DocumentProcessor
from scipher.models.database import Document, Section
from scipher.models.schemas import ProcessedContent, DeleteResponse, SectionSchema, ProcessingStatus
from scipher.core.exceptions import DocumentNotFoundException, DocumentNotReadyException

router = APIRouter(prefix="/api", tags=["content"])


@router.get("/document/{doc_id}", response_model=ProcessedContent)
async def get_document_content(
    doc_id: str,
    db: Session = Depends(get_db),
    processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Retrieve processed document content
    
    - **doc_id**: Document ID
    
    Returns extracted text, sections, and metadata
    """
    
    doc = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    if doc.status != ProcessingStatus.COMPLETED:
        raise DocumentNotReadyException(doc_id, doc.status)
    
    # Get sections from database
    sections = db.query(Section)\
        .filter(Section.document_id == doc_id)\
        .order_by(Section.order)\
        .all()
    
    sections_data = [
        {
            "type": section.section_type,
            "content": section.content,
            "order": section.order
        }
        for section in sections
    ]
    
    # Load processed data if available
    processed_data = processor.load_processed_data(doc_id)
    
    return ProcessedContent(
        id=doc.id,
        filename=doc.original_filename,
        text=doc.extracted_text or "No text extracted",
        sections=sections_data,
        metadata={
            "upload_date": doc.upload_date.isoformat(),
            "file_size": doc.file_size,
            **(doc.metadata_json or {}),
            **(processed_data.get("metadata", {}) if processed_data else {})
        }
    )


@router.get("/document/{doc_id}/sections", response_model=List[SectionSchema])
async def get_document_sections(
    doc_id: str,
    section_type: str = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve document sections
    
    - **doc_id**: Document ID
    - **section_type**: Filter by section type (optional)
    
    Returns list of document sections
    """
    
    # Check if document exists
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    # Build query
    query = db.query(Section).filter(Section.document_id == doc_id)
    
    # Apply section type filter if provided
    if section_type:
        query = query.filter(Section.section_type == section_type)
    
    sections = query.order_by(Section.order).all()
    
    return sections


@router.get("/document/{doc_id}/text")
async def get_document_text(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve raw extracted text from document
    
    - **doc_id**: Document ID
    
    Returns plain text content
    """
    
    doc = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    if doc.status != ProcessingStatus.COMPLETED:
        raise DocumentNotReadyException(doc_id, doc.status)
    
    return {
        "id": doc.id,
        "filename": doc.original_filename,
        "text": doc.extracted_text or "No text available"
    }

logger = logging.getLogger(__name__)

@router.delete("/document/{doc_id}", response_model=DeleteResponse)
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    file_manager: FileManager = Depends(get_file_manager),
    processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Delete a document and all associated data
    
    - **doc_id**: Document ID
    
    Deletes document, files, sections, and processing jobs
    """
    
    doc = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    # Delete physical file
    try:
        file_manager.delete_file(doc.file_path)
    except Exception as e:
        logger.warning(f"Could not delete file {doc.file_path}: {e}")
    
    # Delete processed data file
    try:
        processed_file = processor.processed_dir / f"{doc_id}.json"
        if processed_file.exists():
            file_manager.delete_file(str(processed_file))  # Ensure str compatibility
    except Exception as e:
        logger.warning(f"Could not delete processed data for {doc_id}: {e}")
    
    # Delete database record (cascade will handle sections and jobs)
    db.delete(doc)
    db.commit()
    
    return DeleteResponse(
        message="Document deleted successfully",
        id=doc_id
    )
