from fastapi import FastAPI,Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from scipher.config import settings
from scipher.models.database import init_db
from scipher.dependencies import get_db
from scipher.api.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from scipher.api.routes import upload, processing, content
from scipher.models.schemas import HealthResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    await init_db()
    await settings.initialize()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Scipher",
    version=settings.APP_VERSION,
    debug=bool(settings.DEBUG),
    lifespan=lifespan
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
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
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint for monitoring"""
    db_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
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
