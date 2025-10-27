from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey, Text, BigInteger, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid
from typing import Optional, List

from scipher.config import settings
from scipher.models.schemas import ProcessingStatus

class Base(DeclarativeBase):
    pass

async_engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)

async def init_db():
    """Initialize database tables asynchronously"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String, nullable=False)  # Added for sanitized filename
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    upload_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")))
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String, default=ProcessingStatus.UPLOADED.value)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    sections: Mapped[List["Section"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    jobs: Mapped[List["ProcessingJob"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class Section(Base):
    __tablename__ = "sections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=False)
    section_type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    document: Mapped["Document"] = relationship(back_populates="sections")

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=False)
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    document: Mapped["Document"] = relationship(back_populates="jobs")
