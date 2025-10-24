from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, sessionmaker
from sqlalchemy import String, DateTime, ForeignKey, Text, BigInteger, Integer, create_engine
from sqlalchemy.dialects.postgresql import UUID
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid
from typing import Optional, List

from scipher.config import settings

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Async database engine and session factory
async_engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)
async_session = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

# Sync database engine and session factory (for compatibility)
sync_engine = create_engine(settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://"), echo=settings.DB_ECHO)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

@asynccontextmanager
async def get_async_session():
    """Provide an async database session"""
    async with async_session() as session:
        yield session

async def init_db():
    """Initialize database tables asynchronously"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def get_db():
    """Provide a synchronous database session (for compatibility)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Document(Base):
    """Main document entity"""
    __tablename__ = "documents"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True).with_variant(String(36), "sqlite"),
        primary_key=True,
        default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(ZoneInfo("UTC"))
    )
    status: Mapped[str] = mapped_column(String, default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Processed content storage
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    sections: Mapped[List["Section"]] = relationship(
        "Section", 
        back_populates="document", 
        cascade="all, delete-orphan"
    )
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob", 
        back_populates="document", 
        cascade="all, delete-orphan"
    )


class Section(Base):
    """Document sections (abstract, introduction, etc.)"""
    __tablename__ = "sections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True).with_variant(String(36), "sqlite"),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )
    section_type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="sections")


class ProcessingJob(Base):
    """Track background processing tasks"""
    __tablename__ = "processing_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True).with_variant(String(36), "sqlite"),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="processing_jobs")
