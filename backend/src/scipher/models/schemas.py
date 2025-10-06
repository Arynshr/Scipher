from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ProcessingStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Processing job types"""
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    GLOSSARY = "glossary"
    CLASSIFICATION = "classification"


# Request Schemas
class UploadRequest(BaseModel):
    """Document upload metadata"""
    description: Optional[str] = None
    tags: Optional[List[str]] = None


# Response Schemas
class DocumentResponse(BaseModel):
    """Standard document response"""
    id: str
    filename: str
    original_filename: str
    upload_date: datetime
    status: str
    error_message: Optional[str] = None
    file_size: int
    
    class Config:
        from_attributes = True


class SectionSchema(BaseModel):
    """Document section"""
    id: Optional[int] = None
    section_type: str
    content: str
    order: int = 0
    
    class Config:
        from_attributes = True


class ProcessedContent(BaseModel):
    """Complete processed document content"""
    id: str
    filename: str
    text: str
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class StatusResponse(BaseModel):
    """Processing status response"""
    id: str
    status: str
    message: str
    error_message: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Paginated document list"""
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: str
    status_code: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    version: str


class DeleteResponse(BaseModel):
    """Delete operation response"""
    message: str
    id: str


class ProcessingJobSchema(BaseModel):
    """Processing job details"""
    id: int
    document_id: str
    job_type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True
