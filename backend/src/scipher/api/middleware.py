from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import asyncio
import logging
from typing import Callable

from scipher.core.exceptions import ScipherBaseException
from scipher.models.schemas import ErrorResponse

# Configure logging (only if not already configured)
if not logging.getLogger(__name__).hasHandlers():
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs all incoming requests and their processing time"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = asyncio.get_event_loop().time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = asyncio.get_event_loop().time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code} Time: {process_time:.3f}s"
        )
        
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except ScipherBaseException as e:
            logger.error(f"ScipherException: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    success=False,
                    error=e.__class__.__name__,
                    detail=e.detail
                ).dict()
            )
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    success=False,
                    error="InternalServerError",
                    detail="An unexpected error occurred"
                ).dict()
            )
