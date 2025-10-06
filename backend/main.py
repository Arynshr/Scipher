from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from scipher.config import settings
from scipher.models.database import init_db
from scipher.api.middleware import (
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    DatabaseSessionMiddleware
)
from scipher.api.routes import upload, processing, content
from scipher.models.schemas import HealthResponse

# Initialize database
init_db()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Scipher",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(DatabaseSessionMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(content.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"{settings.APP_NAME} - Phase 1",
        "version": settings.APP_VERSION,
        "status": "active",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring
    
    Returns API health status and version
    """
    from scipher.models.database import engine
    
    # Check database connection
    try:
        with engine.connect() as conn:
            db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.utcnow(),
        database=db_status,
        version=settings.APP_VERSION
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
