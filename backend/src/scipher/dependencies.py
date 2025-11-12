from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from scipher.models.database import async_session
from scipher.core.document_processor import document_processor, DocumentProcessor
from scipher.core.validator import validator, DocumentValidator
from scipher.utils.file_utils import file_manager, FileManager
from scipher.core.summarizer import document_summarizer, DocumentSummarizer

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as db:
        yield db

def get_document_processor() -> DocumentProcessor:
    return document_processor

def get_validator() -> DocumentValidator:
    return validator

def get_file_manager() -> FileManager:
    return file_manager

def get_summarizer() -> DocumentSummarizer:
    return document_summarizer
