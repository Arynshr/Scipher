from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import asyncio

from sqlalchemy.orm import Session
from docling.document_converter import DocumentConverter

from scipher.models.database import Document, Section, ProcessingJob
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
    
    async def process_document(self, doc_id: str, file_path: str, db: Session):
        """
        Main processing pipeline for documents
        
        Args:
            doc_id: Document ID
            file_path: Path to uploaded file
            db: Database session
        """
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return
        
        job = None
        
        try:
            # Update status
            doc.status = ProcessingStatus.PROCESSING
            db.commit()
            
            # Create processing job
            job = ProcessingJob(
                document_id=doc_id,
                job_type=JobType.EXTRACTION,
                status="running",
                started_at=datetime.now(ZoneInfo("UTC"))
            )
            db.add(job)
            db.commit()
            
            logger.info(f"Starting Docling extraction for document {doc_id}")
            
            # Extract text using Docling
            extracted_data = await self.extract_text(file_path)
            
            if not extracted_data or not extracted_data.get("text"):
                raise ProcessingException("No text extracted from document")
            
            # Save extracted text
            doc.extracted_text = extracted_data["text"]
            doc.metadata_json = json.dumps(extracted_data["metadata"])
            
            # Parse and save sections
            sections = await self.parse_sections(extracted_data)
            for idx, section_data in enumerate(sections):
                section = Section(
                    document_id=doc_id,
                    section_type=section_data["type"],
                    content=section_data["content"],
                    order=idx
                )
                db.add(section)
            
            # Save processed data to file
            await self.save_processed_data(doc_id, extracted_data)
            
            # Update document status
            doc.status = ProcessingStatus.COMPLETED
            job.status = "completed"
            job.completed_at = datetime.now(ZoneInfo("UTC"))
            job.result_data = f"Extracted {len(extracted_data['text'])} characters"
            
            db.commit()
            logger.info(f"Successfully processed document {doc_id}")
            
        except Exception as e:
            logger.error(f"Processing failed for document {doc_id}: {str(e)}")
            doc.status = ProcessingStatus.FAILED
            doc.error_message = str(e)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(ZoneInfo("UTC"))
            db.commit()
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
                "pages": getattr(result.document, 'num_pages', 0),
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
    
    async def parse_sections(self, extracted_data: Dict[str, Any]) -> List[Dict[str, str]]:
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
                    "content": line_stripped[2:]
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
    
    async def save_processed_data(self, doc_id: str, data: Dict[str, Any]):
        """
        Save processed data to JSON file
        
        Args:
            doc_id: Document ID
            data: Processed data dictionary
        """
        output_path = self.processed_dir / f"{doc_id}.json"
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._save_json_sync,
                output_path,
                data
            )
            logger.info(f"Saved processed data to {output_path}")
        except Exception as e:
            raise ProcessingException(f"Failed to save processed data: {str(e)}")
    
    def _save_json_sync(self, output_path: Path, data: Dict[str, Any]):
        """Synchronous JSON save helper"""
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_processed_data(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Load processed data from file
        
        Args:
            doc_id: Document ID
            
        Returns:
            Processed data dictionary or None
        """
        file_path = self.processed_dir / f"{doc_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise ProcessingException(f"Failed to load processed data: {str(e)}")


# Singleton instance
document_processor = DocumentProcessor()
