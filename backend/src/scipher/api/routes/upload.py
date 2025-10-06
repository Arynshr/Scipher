from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from scipher.dependencies import get_db, get_validator, get_file_manager, get_document_processor
from scipher.core.validator import DocumentValidator
from scipher.core.document_processor import DocumentProcessor
from scipher.utils.file_utils import FileManager
from scipher.models.database import Document
from scipher.models.schemas import DocumentResponse, ProcessingStatus
from scipher.core.exceptions import DatabaseException

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    validator: DocumentValidator = Depends(get_validator),
    file_manager: FileManager = Depends(get_file_manager),
    processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Upload a research paper for processing
    
    - **file**: PDF file to upload (max 50MB)
    
    Returns document metadata with processing status
    """
    
    # Validate file extension
    file_ext = validator.validate_file_extension(file.filename)
    
    # Validate file size
    file_size = validator.validate_file_size(file)
    
    # Sanitize filename
    safe_original_name = validator.sanitize_filename(file.filename)
    
    # Generate unique filename
    doc_id, safe_filename = file_manager.generate_unique_filename(file.filename)
    
    # Save file
    file_path = file_manager.save_upload_file(file, safe_filename)
    
    # Create database record
    try:
        db_doc = Document(
            id=doc_id,
            filename=safe_filename,
            original_filename=safe_original_name,
            file_path=str(file_path),
            file_size=file_size,
            status=ProcessingStatus.UPLOADED
        )
        
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
    except Exception as e:
        # Cleanup file if database fails
        file_manager.delete_file(file_path)
        raise DatabaseException(f"Failed to create document record: {str(e)}")
    
    # Queue background processing
    background_tasks.add_task(
        processor.process_document,
        doc_id,
        str(file_path),
        db
    )
    
    return db_doc
