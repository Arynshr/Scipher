from pydantic import BaseModel
from datetime import datetime
from zoneinfo import ZoneInfo
from enum import Enum
from uuid import UUID
from typing import List, Optional, Dict, Any

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class JobType(str, Enum):
    EXTRACTION = "extraction"

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    version: str

class DeleteResponse(BaseModel):
    message: str
    id: UUID

class SectionSchema(BaseModel):
    id: Optional[int] = None
    document_id: UUID
    section_type: str
    content: str
    order: int = 0
    
    class Config:
        from_attributes = True

class ProcessingJobSchema(BaseModel):
    id: int
    document_id: UUID
    job_type: JobType
    status: ProcessingStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

class ProcessedContent(BaseModel):
    id: UUID
    filename: str  # Sanitized filename
    original_filename: str  # Original filename
    text: str
    sections: List[SectionSchema]
    metadata: Dict[str, Any]

class StatusResponse(BaseModel):
    id: UUID
    status: ProcessingStatus
    message: str
    error_message: Optional[str] = None

class DocumentResponse(BaseModel):
    id: UUID
    filename: str  # Sanitized filename
    original_filename: str  # Original filename
    upload_date: datetime
    status: ProcessingStatus
    error_message: Optional[str] = None
    file_size: int
    
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int
