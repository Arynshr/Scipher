from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging
import json
from uuid import UUID

from scipher.models.database import get_async_session, Document, Section
from scipher.models.schemas import ProcessedContent, DeleteResponse, SectionSchema, ProcessingStatus
from scipher.core.document_processor import document_processor
from scipher.config import settings
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(tags=["content"])


@router.get("/document/{doc_id}", response_model=ProcessedContent)
async def get_document_content(
    doc_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve processed document content
    
    - **doc_id**: Document ID
    
    Returns extracted text, sections, and metadata
    """
    
    # Convert string to UUID
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    # Get document
    result = await db.execute(
        select(Document).where(Document.id == doc_uuid)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    
    if doc.status != ProcessingStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400, 
            detail=f"Document not ready. Current status: {doc.status}"
        )
    
    # Get sections from database
    sections_result = await db.execute(
        select(Section)
        .where(Section.document_id == doc_uuid)
        .order_by(Section.order)
    )
    sections = sections_result.scalars().all()
    
    # Convert to SectionSchema objects
    sections_data = [
        SectionSchema(
            id=section.id,
            document_id=str(section.document_id),
            section_type=section.section_type,
            content=section.content,
            order=section.order
        )
        for section in sections
    ]
    
    # Parse metadata JSON if exists
    metadata_dict = {}
    if doc.metadata_json:
        try:
            metadata_dict = json.loads(doc.metadata_json)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse metadata JSON for document {doc_id}")
    
    # Load processed data if available
    processed_data = document_processor.load_processed_data(doc_id)
    
    return ProcessedContent(
        id=str(doc.id),  # Convert UUID to string
        filename=doc.original_filename,
        text=doc.extracted_text or "No text extracted",
        sections=sections_data,
        metadata={
            "upload_date": doc.upload_date.isoformat(),
            "file_size": doc.file_size,
            **metadata_dict,
            **(processed_data.get("metadata", {}) if processed_data else {})
        }
    )


@router.get("/document/{doc_id}/sections", response_model=List[SectionSchema])
async def get_document_sections(
    doc_id: str,
    section_type: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve document sections
    
    - **doc_id**: Document ID
    - **section_type**: Filter by section type (optional)
    
    Returns list of document sections
    """
    
    # Convert string to UUID
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    # Check if document exists
    result = await db.execute(
        select(Document).where(Document.id == doc_uuid)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    
    # Build query
    query = select(Section).where(Section.document_id == doc_uuid)
    
    # Apply section type filter if provided
    if section_type:
        query = query.where(Section.section_type == section_type)
    
    query = query.order_by(Section.order)
    
    sections_result = await db.execute(query)
    sections = sections_result.scalars().all()
    
    return [
        SectionSchema(
            id=section.id,
            document_id=str(section.document_id),
            section_type=section.section_type,
            content=section.content,
            order=section.order
        )
        for section in sections
    ]


@router.get("/document/{doc_id}/text")
async def get_document_text(
    doc_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve raw extracted text from document
    
    - **doc_id**: Document ID
    
    Returns plain text content
    """
    
    # Convert string to UUID
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    result = await db.execute(
        select(Document).where(Document.id == doc_uuid)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    
    if doc.status != ProcessingStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Document not ready. Current status: {doc.status}"
        )
    
    return {
        "id": str(doc.id),
        "filename": doc.original_filename,
        "text": doc.extracted_text or "No text available",
        "status": doc.status
    }


@router.delete("/document/{doc_id}", response_model=DeleteResponse)
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Delete a document and all associated data
    
    - **doc_id**: Document ID
    
    Deletes document, files, sections, and processing jobs
    """
    
    # Convert string to UUID
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    result = await db.execute(
        select(Document).where(Document.id == doc_uuid)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    
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
        id=doc_id  # Return as string (matches input)
    )
