from pathlib import Path
from typing import Set
import re
from fastapi import UploadFile

from config import settings
from core.exceptions import (
    ValidationException,
    FileSizeExceededException,
    UnsupportedFileTypeException,
    DocumentNotReadyException
)
from models.schemas import ProcessingStatus


class DocumentValidator:
    """Handles all validation logic for documents and files"""
    
    def __init__(
        self,
        allowed_extensions: Set[str] = None,
        max_file_size: int = None
    ):
        self.allowed_extensions = allowed_extensions or settings.ALLOWED_EXTENSIONS
        self.max_file_size = max_file_size or settings.MAX_FILE_SIZE
    
    def validate_file_extension(self, filename: str) -> str:
        """
        Validate file extension against allowed types
        
        Args:
            filename: Original filename
            
        Returns:
            File extension (lowercase)
            
        Raises:
            UnsupportedFileTypeException: If file type not allowed
        """
        file_ext = Path(filename).suffix.lower()
        
        if not file_ext:
            raise ValidationException("File has no extension")
        
        if file_ext not in self.allowed_extensions:
            raise UnsupportedFileTypeException(file_ext, self.allowed_extensions)
        
        return file_ext
    
    def validate_file_size(self, file: UploadFile) -> int:
        """
        Validate file size against maximum limit
        
        Args:
            file: Uploaded file object
            
        Returns:
            File size in bytes
            
        Raises:
            FileSizeExceededException: If file too large
            ValidationException: If file is empty
        """
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to start
        
        if file_size == 0:
            raise ValidationException("Empty file uploaded")
        
        if file_size > self.max_file_size:
            raise FileSizeExceededException(file_size, self.max_file_size)
        
        return file_size
    
    def validate_document_status(self, status: str, required_status: str = None):
        """
        Validate document processing status
        
        Args:
            status: Current document status
            required_status: Expected status (optional)
            
        Raises:
            DocumentNotReadyException: If status doesn't match requirement
        """
        if required_status and status != required_status:
            raise DocumentNotReadyException("document", status)
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and other attacks
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = Path(filename).name
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1)
            filename = name[:250] + '.' + ext
        
        return filename
    
    def validate_pagination(self, skip: int, limit: int) -> tuple:
        """
        Validate pagination parameters
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Validated (skip, limit) tuple
            
        Raises:
            ValidationException: If parameters invalid
        """
        if skip < 0:
            raise ValidationException("Skip parameter must be non-negative")
        
        if limit < 1 or limit > 100:
            raise ValidationException("Limit must be between 1 and 100")
        
        return skip, limit


# Singleton instance
validator = DocumentValidator()
