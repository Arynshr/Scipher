from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from contextlib import asynccontextmanager

from scipher.config import settings
from scipher.models.database import init_db, get_async_session
from scipher.api.middleware import (
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    DatabaseSessionMiddleware
)
from scipher.api.routes import upload, processing, content
from scipher.models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    await init_db()
    settings.UPLOAD_DIR.mkdir(exist_ok=True)
    settings.PROCESSED_DATA_DIR.mkdir(exist_ok=True)
    settings.TEMP_DIR.mkdir(exist_ok=True)
    
    yield
    
    # Shutdown (add cleanup if needed)


app = FastAPI(
    title=settings.APP_NAME,
    description="Scipher",
    version=settings.APP_VERSION,
    debug=bool(settings.DEBUG),
    lifespan=lifespan
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(DatabaseSessionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(processing.router, prefix="/api")
app.include_router(content.router, prefix="/api")


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
    """Health check endpoint for monitoring"""
    db_status = "disconnected"
    
    # Now works correctly with @asynccontextmanager
    async with get_async_session() as session:
        try:
            await session.execute(text("SELECT 1"))
            db_status = "connected"
        except OperationalError:
            db_status = "disconnected"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.now(ZoneInfo("UTC")),
        database=db_status,
        version=settings.APP_VERSION
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=str(settings.HOST),
        port=int(settings.PORT),
        reload=bool(settings.DEBUG),
        workers=1 if bool(settings.DEBUG) else 4
    )
