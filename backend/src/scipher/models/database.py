from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import settings

# Database setup
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DB_ECHO
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Document(Base):
    """Main document entity"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="uploaded")
    error_message = Column(String, nullable=True)
    file_size = Column(Integer, nullable=False)
    
    # Relationships
    sections = relationship("Section", back_populates="document", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan")
    
    # Processed content storage
    extracted_text = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    

class Section(Base):
    """Document sections (abstract, introduction, etc.)"""
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    section_type = Column(String, nullable=False)  # title, abstract, body, conclusion
    content = Column(Text, nullable=False)
    order = Column(Integer, default=0)
    
    # Relationships
    document = relationship("Document", back_populates="sections")


class ProcessingJob(Base):
    """Track background processing tasks"""
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    job_type = Column(String, nullable=False)  # extraction, summarization, glossary
    status = Column(String, default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    result_data = Column(JSON, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="processing_jobs")


# Create all tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
