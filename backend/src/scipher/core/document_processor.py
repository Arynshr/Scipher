from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from docling.document_converter import DocumentConverter

from scipher.models.database import async_session, Document, Section, ProcessingJob
from scipher.models.schemas import ProcessingStatus, JobType
from scipher.core.exceptions import ProcessingException
from scipher.config import settings
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Orchestrates document processing pipeline
    Integrates with Docling for PDF parsing
    """
    
    def __init__(self):
        self.processed_dir = settings.PROCESSED_DATA_DIR
        self.processed_dir.mkdir(exist_ok=True)
        self.converter = DocumentConverter()
    
    async def process_document(self, doc_id: str, file_path: str):
        """
        Main processing pipeline for documents
        
        Args:
            doc_id: Document ID
            file_path: Path to uploaded file
        """
        async with async_session() as db:
            job = None
            
            try:
                # Get document (async query)
                stmt = select(Document).filter_by(id=doc_id)
                doc = (await db.scalars(stmt)).first()
                if not doc:
                    return
                
                # Update status
                doc.status = ProcessingStatus.PROCESSING.value
                await db.commit()
                
                # Create processing job
                job = ProcessingJob(
                    document_id=doc_id,
                    job_type=JobType.EXTRACTION.value,
                    status=ProcessingStatus.RUNNING.value,  # Fixed to use ProcessingStatus
                    started_at=datetime.now(ZoneInfo("UTC"))
                )
                db.add(job)
                await db.commit()
                
                logger.info(f"Starting Docling extraction for document {doc_id}")
                
                # Extract text using Docling
                extracted_data = await self.extract_text(file_path)
                
                if not extracted_data or not extracted_data.get("text"):
                    raise ProcessingException("No text extracted from document")
                
                # Save markdown text to file (not in DB for efficiency)
                markdown_text = extracted_data["text"]
                await self.save_markdown_file(doc_id, markdown_text)
                
                # Store minimal text in DB (nullable, for fallback/search) - first 1000 chars
                doc.extracted_text = markdown_text[:1000] if len(markdown_text) > 1000 else markdown_text
                doc.metadata_json = json.dumps(extracted_data["metadata"])
                
                # Parse and save sections with only metadata (preview, not full content)
                sections = self.parse_sections(extracted_data)
                for idx, section_data in enumerate(sections):
                    # Store only preview (first 200 chars) for filtering, not full content
                    content_preview = section_data["content"][:200] if len(section_data["content"]) > 200 else section_data["content"]
                    section = Section(
                        document_id=doc_id,
                        section_type=section_data["type"],
                        content=content_preview,  # Only preview, full content in MD file
                        order=idx
                    )
                    db.add(section)
                
                # Update document status
                doc.status = ProcessingStatus.COMPLETED.value
                job.status = ProcessingStatus.COMPLETED.value
                job.completed_at = datetime.now(ZoneInfo("UTC"))
                job.result_data = f"Extracted {len(extracted_data['text'])} characters"
                
                await db.commit()
                logger.info(f"Successfully processed document {doc_id}")
                
            except Exception as e:
                logger.error(f"Processing failed for document {doc_id}: {str(e)}")
                if doc:
                    doc.status = ProcessingStatus.FAILED.value
                    doc.error_message = str(e)
                if job:
                    job.status = ProcessingStatus.FAILED.value
                    job.error_message = str(e)
                    job.completed_at = datetime.now(ZoneInfo("UTC"))
                await db.commit()
                raise ProcessingException(str(e))
    
    async def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF using Docling
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        pdf_path = Path(file_path)
        
        if not pdf_path.exists():
            raise ProcessingException(f"File not found: {file_path}")
        
        if pdf_path.suffix.lower() != '.pdf':
            raise ProcessingException(f"Unsupported file type: {pdf_path.suffix}")
        
        try:
            logger.info(f"Converting PDF with Docling: {pdf_path.name}")
            
            # Run conversion in executor (CPU-bound operation)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._convert_pdf_sync,
                str(pdf_path)
            )
            
            # Export to markdown for clean text extraction
            markdown_text = result.document.export_to_markdown()
            
            # Get document metadata
            metadata = {
                "pages": result.document.num_pages(),
                "file_size": pdf_path.stat().st_size,
                "extraction_date": datetime.now(ZoneInfo("UTC")).isoformat(),
                "converter": "docling",
                "format": "markdown"
            }
            
            logger.info(f"Extracted {len(markdown_text)} characters from {pdf_path.name}")
            
            return {
                "text": markdown_text,
                "metadata": metadata,
                "sections": []
            }
            
        except Exception as e:
            logger.error(f"Docling extraction failed: {str(e)}")
            raise ProcessingException(f"Text extraction failed: {str(e)}")
    
    def _convert_pdf_sync(self, file_path: str):
        """Synchronous PDF conversion helper for executor"""
        return self.converter.convert(file_path)
    
    def parse_sections(self, extracted_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Parse document into logical sections
        
        Args:
            extracted_data: Raw extracted data
            
        Returns:
            List of section dictionaries
        """
        text = extracted_data.get("text", "")
        
        # Simple section detection based on markdown headers
        sections = []
        current_section = {"type": "body", "content": ""}
        
        for line in text.split('\n'):
            line_stripped = line.strip()
            
            # Detect headers (markdown format)
            if line_stripped.startswith('# '):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {
                    "type": "title",
                    "content": line_stripped[2:] + "\n"
                }
            elif line_stripped.startswith('## '):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {
                    "type": "section",
                    "content": line_stripped[3:] + "\n"
                }
            else:
                current_section["content"] += line + "\n"
        
        # Add last section
        if current_section["content"]:
            sections.append(current_section)
        
        # If no sections detected, return full text as body
        if not sections:
            sections = [{
                "type": "body",
                "content": text
            }]
        
        return sections
    
    async def save_markdown_file(self, doc_id: str, markdown_text: str):
        """
        Save processed markdown to file
        
        Args:
            doc_id: Document ID
            markdown_text: Markdown content to save
        """
        output_path = self.processed_dir / f"{doc_id}.md"
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._save_markdown_sync,
                output_path,
                markdown_text
            )
            logger.info(f"Saved markdown file to {output_path}")
        except Exception as e:
            raise ProcessingException(f"Failed to save markdown file: {str(e)}")
    
    def _save_markdown_sync(self, output_path: Path, markdown_text: str):
        """Synchronous markdown save helper"""
        with output_path.open("w", encoding="utf-8") as f:
            f.write(markdown_text)
    
    def load_markdown_file(self, doc_id: str) -> Optional[str]:
        """
        Load markdown file
        
        Args:
            doc_id: Document ID
            
        Returns:
            Markdown content or None
        """
        file_path = self.processed_dir / f"{doc_id}.md"
        
        if not file_path.exists():
            return None
        
        try:
            with file_path.open("r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise ProcessingException(f"Failed to load markdown file: {str(e)}")

# Singleton instance
document_processor = DocumentProcessor()
