from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging
import json
from uuid import UUID

from scipher.dependencies import get_db, get_document_processor
from scipher.models.database import Document, Section
from scipher.models.schemas import ProcessedContent, DeleteResponse, SectionSchema, ProcessingStatus
from scipher.core.document_processor import DocumentProcessor
from scipher.core.exceptions import DocumentNotFoundException
from scipher.config import settings
from pydantic import BaseModel
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(tags=["content"])

# New Pydantic model for get_document_text response
class TextResponse(BaseModel):
    id: UUID
    filename: str
    text: str
    status: ProcessingStatus

@router.get("/document/{doc_id}", response_model=ProcessedContent)
async def get_document_content(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Retrieve processed document content
    
    - **doc_id**: Document ID
    
    Returns extracted text, sections, and metadata
    """
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    stmt = select(Document).filter_by(id=str(doc_uuid))
    doc = (await db.scalars(stmt)).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    if doc.status != ProcessingStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400, 
            detail=f"Document not ready. Current status: {doc.status}"
        )
    
    sections_stmt = select(Section).filter_by(document_id=str(doc_uuid)).order_by(Section.order)
    sections = (await db.scalars(sections_stmt)).all()
    
    return ProcessedContent(
        id=doc.id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        text=doc.extracted_text or "",
        sections=[SectionSchema.from_orm(section) for section in sections],
        metadata=json.loads(doc.metadata_json) if doc.metadata_json else {},
        file_size=doc.file_size,
        upload_date=doc.upload_date
    )

@router.get("/document/{doc_id}/sections", response_model=List[SectionSchema])
async def get_document_sections(
    doc_id: str,
    section_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve document sections
    
    - **doc_id**: Document ID
    - **section_type**: Filter by section type (optional)
    
    Returns list of document sections
    """
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    # Check if document exists
    stmt = select(Document).filter_by(id=str(doc_uuid))
    doc = (await db.scalars(stmt)).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    # Build query
    query = select(Section).filter_by(document_id=str(doc_uuid))
    if section_type:
        query = query.filter_by(section_type=section_type)
    
    query = query.order_by(Section.order)
    sections = (await db.scalars(query)).all()
    
    return [SectionSchema.from_orm(section) for section in sections]

@router.get("/document/{doc_id}/text", response_model=TextResponse)
async def get_document_text(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve raw extracted text from document
    
    - **doc_id**: Document ID
    
    Returns plain text content
    """
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    stmt = select(Document).filter_by(id=str(doc_uuid))
    doc = (await db.scalars(stmt)).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    if doc.status != ProcessingStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Document not ready. Current status: {doc.status}"
        )
    
    return TextResponse(
        id=doc.id,
        filename=doc.original_filename,
        text=doc.extracted_text or "No text available",
        status=ProcessingStatus(doc.status)
    )

@router.delete("/document/{doc_id}", response_model=DeleteResponse)
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and all associated data
    
    - **doc_id**: Document ID
    
    Deletes document, files, sections, and processing jobs
    """
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    stmt = select(Document).filter_by(id=str(doc_uuid))
    doc = (await db.scalars(stmt)).first()
    
    if not doc:
        raise DocumentNotFoundException(doc_id)
    
    # Delete physical file
    try:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
    except Exception as e:
        logger.warning(f"Could not delete file {doc.file_path}: {e}")
    
    # Delete processed data file
    try:
        processed_file = settings.PROCESSED_DATA_DIR / f"{doc_id}.json"
        if processed_file.exists():
            processed_file.unlink()
            logger.info(f"Deleted processed data: {processed_file}")
    except Exception as e:
        logger.warning(f"Could not delete processed data for {doc_id}: {e}")
    
    # Delete markdown file if exists
    try:
        md_file = settings.PROCESSED_DATA_DIR / f"{doc_id}.md"
        if md_file.exists():
            md_file.unlink()
            logger.info(f"Deleted markdown: {md_file}")
    except Exception as e:
        logger.warning(f"Could not delete markdown for {doc_id}: {e}")
    
    # Delete database record (cascade will handle sections and jobs)
    await db.delete(doc)
    await db.commit()
    
    logger.info(f"Successfully deleted document {doc_id}")
    
    return DeleteResponse(
        message="Document deleted successfully",
        id=doc_uuid  # Use UUID
    )
