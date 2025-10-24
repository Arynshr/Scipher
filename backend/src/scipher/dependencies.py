from typing import Generator
from sqlalchemy.orm import Session

from scipher.models.database import SessionLocal
from scipher.core.document_processor import document_processor, DocumentProcessor
from scipher.core.validator import validator, DocumentValidator
from scipher.utils.file_utils import file_manager, FileManager


def get_db() -> Generator[Session, None, None]:

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_document_processor() -> DocumentProcessor:

    return document_processor


def get_validator() -> DocumentValidator:

    return validator


def get_file_manager() -> FileManager:

    return file_manager
