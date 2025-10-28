from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import asyncio
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import fitz  # PyMuPDF

from scipher.models.database import async_session, Document, Section, ProcessingJob
from scipher.models.schemas import ProcessingStatus, JobType
from scipher.core.exceptions import ProcessingException
from scipher.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Handles document parsing with PyMuPDF.
    Fast, reliable extraction for research papers.
    """

    def __init__(self, processing_timeout: int = 300):
        """
        Args:
            processing_timeout: Max allowed time (in seconds) for document processing.
        """
        self.processed_dir = settings.PROCESSED_DATA_DIR
        self.processed_dir.mkdir(exist_ok=True)
        self.processing_timeout = processing_timeout
        logger.info("DocumentProcessor initialized with PyMuPDF backend.")

    async def process_document(self, doc_id: str, file_path: str):
        """
        Main entrypoint for processing a document asynchronously.
        """
        async with async_session() as db:
            job = None
            doc = None

            try:
                # Fetch target document
                stmt = select(Document).filter_by(id=doc_id)
                doc = (await db.scalars(stmt)).first()
                if not doc:
                    logger.warning(f"Document {doc_id} not found in DB.")
                    return

                # Update initial status
                doc.status = ProcessingStatus.PROCESSING.value
                await db.commit()

                # Create a job entry
                job = ProcessingJob(
                    document_id=doc_id,
                    job_type=JobType.EXTRACTION.value,
                    status=ProcessingStatus.RUNNING.value,
                    started_at=datetime.now(ZoneInfo("UTC")),
                )
                db.add(job)
                await db.commit()

                logger.info(f"Started document extraction for {file_path} (ID: {doc_id})")

                # Dynamic timeout based on file size
                file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
                timeout = min(600, max(120, int(file_size_mb * 20)))
                
                # Run extraction with timeout
                extracted_data = await asyncio.wait_for(
                    self.extract_text(file_path),
                    timeout=timeout,
                )

                if not extracted_data or not extracted_data.get("text"):
                    raise ProcessingException("No text extracted from document.")

                # Quality check and warning
                quality_score = self._calculate_quality(extracted_data["text"])
                if quality_score < 0.5:
                    logger.warning(f"Low extraction quality ({quality_score:.2f}) for {doc_id}. Document may be scanned or have complex layout.")

                # Save extracted text and metadata
                doc.extracted_text = extracted_data["text"]
                extracted_data["metadata"]["quality_score"] = quality_score
                doc.metadata_json = json.dumps(extracted_data["metadata"])

                # Parse and persist sections
                sections = self.parse_sections(extracted_data)
                for idx, sdata in enumerate(sections):
                    db.add(
                        Section(
                            document_id=doc_id,
                            section_type=sdata["type"],
                            content=sdata["content"],
                            order=idx,
                        )
                    )

                # Persist processed data file
                await self.save_processed_data(doc_id, extracted_data)

                # Mark success
                doc.status = ProcessingStatus.COMPLETED.value
                job.status = ProcessingStatus.COMPLETED.value
                job.completed_at = datetime.now(ZoneInfo("UTC"))
                job.result_data = f"Extracted {len(extracted_data['text'])} characters (quality: {quality_score:.2f})"

                await db.commit()
                logger.info(f"✅ Document {doc_id} processed successfully.")

            except asyncio.TimeoutError:
                msg = f"Processing timed out after {timeout}s for document {doc_id}"
                logger.error(msg)
                await self._mark_failed(db, doc, job, msg)
                raise ProcessingException(msg)

            except Exception as e:
                msg = f"Processing failed for {doc_id}: {str(e)}"
                logger.error(msg)
                await self._mark_failed(db, doc, job, msg)
                raise ProcessingException(msg)

    async def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text and structure using PyMuPDF.
        Handles native PDF text extraction with layout preservation.
        """
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise ProcessingException(f"File not found: {file_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise ProcessingException(f"Unsupported file type: {pdf_path.suffix}")

        loop = asyncio.get_event_loop()

        logger.info(f"Extracting text with PyMuPDF: {pdf_path.name}")
        result = await loop.run_in_executor(
            None, self._extract_with_pymupdf, str(pdf_path)
        )
        
        logger.info(f"✅ Extracted {len(result['text'])} characters from {pdf_path.name}")
        return result

    def _extract_with_pymupdf(self, file_path: str) -> Dict[str, Any]:
        """
        Fast extraction using PyMuPDF for native PDF text.
        Preserves structure via font size analysis and text blocks.
        """
        doc = fitz.open(file_path)
        markdown_parts = []
        
        metadata = {
            "pages": len(doc),
            "file_size": Path(file_path).stat().st_size,
            "extraction_date": datetime.now(ZoneInfo("UTC")).isoformat(),
            "extractor": "pymupdf",
            "format": "markdown",
            "has_images": False,
            "has_tables": False,
        }

        for page_num, page in enumerate(doc, start=1):
            # Check for images
            if page.get_images():
                metadata["has_images"] = True

            # Extract text blocks with structure
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
            
            for block in blocks:
                if block.get("type") == 0:  # Text block
                    lines = block.get("lines", [])
                    
                    for line in lines:
                        if not line.get("spans"):
                            continue
                            
                        # Get text and font info
                        text = " ".join([span["text"] for span in line["spans"]]).strip()
                        if not text:
                            continue
                        
                        # Analyze font size for header detection
                        font_size = line["spans"][0].get("size", 11)
                        font_flags = line["spans"][0].get("flags", 0)
                        is_bold = font_flags & 2 ** 4  # Bold flag
                        
                        # Header detection
                        if font_size > 16 or (font_size > 14 and is_bold):
                            markdown_parts.append(f"\n# {text}\n")
                        elif font_size > 13 or (font_size > 11 and is_bold):
                            markdown_parts.append(f"\n## {text}\n")
                        elif font_size > 11.5:
                            markdown_parts.append(f"\n### {text}\n")
                        else:
                            markdown_parts.append(text + " ")
                    
                    # Add paragraph break after block
                    markdown_parts.append("\n\n")

            # Page break
            if page_num < len(doc):
                markdown_parts.append("\n---\n\n")

        doc.close()
        
        # Clean up excessive whitespace
        markdown_text = "".join(markdown_parts)
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)  # Max 2 newlines
        markdown_text = re.sub(r' {2,}', ' ', markdown_text)  # Single spaces
        
        return {
            "text": markdown_text.strip(),
            "metadata": metadata,
            "sections": []
        }

    def _calculate_quality(self, text: str) -> float:
        """
        Heuristic quality score based on text characteristics.
        Returns score between 0.0 and 1.0.
        
        High score = clean, well-structured text
        Low score = potentially scanned/OCR issues
        """
        if not text or len(text) < 100:
            return 0.0

        score = 1.0
        
        # Check alpha character ratio (should be high)
        alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / len(text)
        if alpha_ratio < 0.7:
            score -= 0.3

        # Check for excessive special characters
        special_ratio = sum(not c.isalnum() and not c.isspace() and c not in '.,!?;:()-"' for c in text) / len(text)
        if special_ratio > 0.15:
            score -= 0.2

        # Check average word length
        words = [w for w in text.split() if w.isalpha()]
        if words:
            avg_word_len = sum(len(w) for w in words) / len(words)
            if avg_word_len < 3:
                score -= 0.3
            elif avg_word_len > 10:
                score -= 0.1

        # Check for proper sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) > 5:
            avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences)
            if 5 < avg_sentence_len < 50:
                score += 0.1

        # Check for common research paper indicators
        research_terms = ['abstract', 'introduction', 'method', 'result', 'conclusion', 'reference']
        if any(term in text.lower() for term in research_terms):
            score += 0.1

        return max(0.0, min(1.0, score))

    def parse_sections(self, extracted_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Markdown header-based section segmentation.
        Supports #, ##, and ### headers.
        """
        text = extracted_data.get("text", "")
        sections = []
        current = {"type": "body", "content": ""}

        for line in text.split("\n"):
            line_stripped = line.strip()
            
            if line_stripped.startswith("# ") and not line_stripped.startswith("## "):
                if current["content"].strip():
                    sections.append(current)
                current = {"type": "title", "content": line_stripped[2:] + "\n"}
            elif line_stripped.startswith("## ") and not line_stripped.startswith("### "):
                if current["content"].strip():
                    sections.append(current)
                current = {"type": "section", "content": line_stripped[3:] + "\n"}
            elif line_stripped.startswith("### "):
                if current["content"].strip():
                    sections.append(current)
                current = {"type": "subsection", "content": line_stripped[4:] + "\n"}
            else:
                current["content"] += line + "\n"

        if current["content"].strip():
            sections.append(current)

        return sections or [{"type": "body", "content": text}]

    async def save_processed_data(self, doc_id: str, data: Dict[str, Any]):
        """Saves extracted data as JSON."""
        output_path = self.processed_dir / f"{doc_id}.json"
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_json_sync, output_path, data)
        logger.info(f"Saved processed data to {output_path}")

    def _save_json_sync(self, path: Path, data: Dict[str, Any]):
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_processed_data(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Loads JSON results from previous runs."""
        file_path = self.processed_dir / f"{doc_id}.json"
        if not file_path.exists():
            return None
        try:
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise ProcessingException(f"Failed to load processed data: {str(e)}")

    async def _mark_failed(self, db: AsyncSession, doc, job, message: str):
        """Marks a failed document/job with consistent metadata."""
        if doc:
            doc.status = ProcessingStatus.FAILED.value
            doc.error_message = message
        if job:
            job.status = ProcessingStatus.FAILED.value
            job.error_message = message
            job.completed_at = datetime.now(ZoneInfo("UTC"))
        await db.commit()


# Singleton instance
document_processor = DocumentProcessor()
