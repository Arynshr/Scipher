from typing import Any, Dict, List, Optional
from fastapi.responses import JSONResponse
from scipher.models.schemas import ProcessingStatus


class ResponseFormatter:
    """Standardized API response formatting"""
    
    @staticmethod
    def success_response(
        data: Any,
        message: str = "Success",
        status_code: int = 200
    ) -> JSONResponse:
        """
        Format successful response
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            
        Returns:
            Formatted JSON response
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "success": True,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def error_response(
        error: str,
        detail: str,
        status_code: int = 400
    ) -> JSONResponse:
        """
        Format error response
        
        Args:
            error: Error type
            detail: Error details
            status_code: HTTP status code
            
        Returns:
            Formatted JSON error response
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": error,
                "detail": detail
            }
        )
    
    @staticmethod
    def pagination_response(
        items: List[Any],
        total: int,
        skip: int,
        limit: int
    ) -> Dict[str, Any]:
        """
        Format paginated response
        
        Args:
            items: List of items
            total: Total count
            skip: Offset
            limit: Page size
            
        Returns:
            Pagination metadata with items
        """
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total
        }
    
    @staticmethod
    def status_message_mapper(status: str) -> str:
        """
        Map processing status to human-readable message
        
        Args:
            status: Processing status
            
        Returns:
            Human-readable status message
        """
        messages = {
            ProcessingStatus.UPLOADED: "Document uploaded successfully, queued for processing",
            ProcessingStatus.PROCESSING: "Document is being processed",
            ProcessingStatus.COMPLETED: "Processing completed successfully",
            ProcessingStatus.FAILED: "Processing failed"
        }
        return messages.get(status, "Unknown status")


# Singleton instance
response_formatter = ResponseFormatter()
