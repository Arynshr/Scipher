from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from docling.document_converter import DocumentConverter
from scipher.models.database import Document, Section, ProcessingJob
from scipher.models.schemas import ProcessingStatus, JobType
from scipher.core.exceptions import ProcessingException
from scipher.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Asynchronous document processing pipeline using Docling"""

    def __init__(self):
        self.processed_dir = settings.PROCESSED_DATA_DIR
        self.processed_dir.mkdir(exist_ok=True)
        self.converter = DocumentConverter()

    async def process_document(self, doc_id: str, file_path: str, db: AsyncSession):
        """Process a document asynchronously"""
        # Fetch document
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalars().first()
        if not doc:
            logger.error(f"Document {doc_id} not found")
            return

        job = None
        try:
            # Update status
            doc.status = ProcessingStatus.PROCESSING.value
            await db.commit()

            # Create processing job
            job = ProcessingJob(
                document_id=doc_id,
                job_type=JobType.EXTRACTION.value,
                status="running",
                started_at=datetime.now(ZoneInfo("UTC"))
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)

            logger.info(f"Starting Docling extraction for document {doc_id}")

            # Extract text using Docling
            extracted_data = await self.extract_text(file_path)

            if not extracted_data or not extracted_data.get("text"):
                raise ProcessingException("No text extracted from document")

            # Save extracted text and metadata
            doc.extracted_text = extracted_data["text"]
            doc.metadata_json = json.dumps(extracted_data["metadata"])
            await db.commit()

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
            await db.commit()

            # Save processed data to file
            await self.save_processed_data(doc_id, extracted_data)

            # Update document and job status
            doc.status = ProcessingStatus.COMPLETED.value
            job.status = "completed"
            job.completed_at = datetime.now(ZoneInfo("UTC"))
            job.result_data = f"Extracted {len(extracted_data['text'])} characters"
            await db.commit()
            await db.refresh(doc)
            await db.refresh(job)

            logger.info(f"Successfully processed document {doc_id}")

        except Exception as e:
            logger.error(f"Processing failed for document {doc_id}: {str(e)}")
            doc.status = ProcessingStatus.FAILED.value
            doc.error_message = str(e)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(ZoneInfo("UTC"))
            await db.commit()
            raise ProcessingException(str(e))

    async def extract_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF using Docling asynchronously"""
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise ProcessingException(f"File not found: {file_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ProcessingException(f"Unsupported file type: {pdf_path.suffix}")

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self._convert_pdf_sync, str(pdf_path))
            markdown_text = result.document.export_to_markdown()
            metadata = {
                "pages": getattr(result.document, "num_pages", lambda: None)(),
                "file_size": pdf_path.stat().st_size,
                "extraction_date": datetime.now(ZoneInfo("UTC")).isoformat(),
                "converter": "docling",
                "format": "markdown"
            }
            return {"text": markdown_text, "metadata": metadata, "sections": []}

        except Exception as e:
            logger.error(f"Docling extraction failed: {str(e)}")
            raise ProcessingException(f"Text extraction failed: {str(e)}")

    def _convert_pdf_sync(self, file_path: str):
        """Synchronous helper for PDF conversion in executor"""
        return self.converter.convert(file_path)

    async def parse_sections(self, extracted_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Parse text into sections based on markdown headers"""
        text = extracted_data.get("text", "")
        sections = []
        current_section = {"type": "body", "content": ""}

        for line in text.split("\n"):
            line_stripped = line.strip()
            if line_stripped.startswith("# "):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"type": "title", "content": line_stripped[2:]}
            elif line_stripped.startswith("## "):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"type": "section", "content": line_stripped[3:] + "\n"}
            else:
                current_section["content"] += line + "\n"

        if current_section["content"]:
            sections.append(current_section)

        if not sections:
            sections = [{"type": "body", "content": text}]

        return sections

    async def save_processed_data(self, doc_id: str, data: Dict[str, Any]):
        """Save processed document data asynchronously"""
        output_path = self.processed_dir / f"{doc_id}.json"
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._save_json_sync, output_path, data)
        logger.info(f"Saved processed data to {output_path}")

    def _save_json_sync(self, output_path: Path, data: Dict[str, Any]):
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_processed_data(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Load processed data from file"""
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
