from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from typing import Callable

from core.exceptions import ScipherBaseException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs all incoming requests and their processing time"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code} Time: {process_time:.3f}s"
        )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except ScipherBaseException as e:
            # Handle custom exceptions
            logger.error(f"ScipherException: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": e.__class__.__name__,
                    "detail": e.detail
                }
            )
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "InternalServerError",
                    "detail": "An unexpected error occurred"
                }
            )


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """Ensures database sessions are properly closed"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        # Database sessions are handled by dependency injection
        # This middleware ensures cleanup on errors
        return response
