from fastapi import HTTPException, status


class ScipherBaseException(HTTPException):
    """Base exception for Scipher application"""
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class DocumentNotFoundException(ScipherBaseException):
    """Raised when document is not found in database"""
    def __init__(self, doc_id: str):
        super().__init__(
            detail=f"Document with ID '{doc_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ProcessingException(ScipherBaseException):
    """Raised when document processing fails"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Processing failed: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ValidationException(ScipherBaseException):
    """Raised for validation errors"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Validation error: {detail}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FileSizeExceededException(ScipherBaseException):
    """Raised when file size exceeds limit"""
    def __init__(self, size: int, max_size: int):
        super().__init__(
            detail=f"File size {size / (1024*1024):.2f}MB exceeds maximum allowed {max_size / (1024*1024):.2f}MB",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )


class UnsupportedFileTypeException(ScipherBaseException):
    """Raised for unsupported file types"""
    def __init__(self, file_type: str, allowed_types: set):
        super().__init__(
            detail=f"File type '{file_type}' not supported. Allowed types: {', '.join(allowed_types)}",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )


class DocumentNotReadyException(ScipherBaseException):
    """Raised when document is accessed before processing completes"""
    def __init__(self, doc_id: str, current_status: str):
        super().__init__(
            detail=f"Document '{doc_id}' is not ready. Current status: {current_status}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FileOperationException(ScipherBaseException):
    """Raised for file operation errors"""
    def __init__(self, operation: str, detail: str):
        super().__init__(
            detail=f"File {operation} failed: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DatabaseException(ScipherBaseException):
    """Raised for database operation errors"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Database error: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
