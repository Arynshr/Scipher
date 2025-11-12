"""
Reusable document summarizer built on top of Hugging Face BART.

The summarizer is designed to be lazily loaded so that model weights are only
brought into memory when the first summary request arrives.  Text is chunked
based on tokenizer length limits to keep inference stable, and three presets
are exposed to produce summaries at different difficulty levels.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from threading import Lock
from typing import Dict, List, Optional

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SummaryResult:
    """Container for difficulty-based summaries."""

    easy: str
    intermediate: str
    technical: str
    chunk_count: int
    source_characters: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class DocumentSummarizer:
    """Generate summaries for extracted document text."""

    def __init__(
        self,
        model_name: str = "sshleifer/distilbart-cnn-12-6",
        chunk_token_length: int = 800,
        chunk_summary_max_tokens: int = 200,
        difficulty_presets: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> None:
        self.model_name = model_name
        self.chunk_token_length = chunk_token_length
        self.chunk_summary_max_tokens = chunk_summary_max_tokens
        self._difficulty_presets = difficulty_presets or {
            "easy": {"min_length": 35, "max_length": 90, "num_beams": 2},
            "intermediate": {"min_length": 70, "max_length": 160, "num_beams": 2},
            "technical": {"min_length": 120, "max_length": 240, "num_beams": 3},
        }

        self._tokenizer = None
        self._pipeline = None
        self._lock: Lock = Lock()

    @property
    def device(self) -> int:
        return 0 if torch.cuda.is_available() else -1

    def summarize(self, text: str) -> SummaryResult:
        """Summarize text into three difficulty levels."""
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Cannot summarize empty text")

        tokenizer = self._ensure_tokenizer()
        chunks = self._chunk_text(cleaned, tokenizer)
        logger.debug("Summarizer chunked document into %d segments", len(chunks))

        chunk_summaries = [
            self._run_pipeline(
                chunk,
                min_length=max(18, int(self.chunk_summary_max_tokens * 0.25)),
                max_length=self.chunk_summary_max_tokens,
                num_beams=2,
            )
            for chunk in chunks
        ]
        combined = " ".join(chunk_summaries) if len(chunk_summaries) > 1 else chunk_summaries[0]

        difficulty_outputs = {
            name: self._run_pipeline(
                combined,
                min_length=config["min_length"],
                max_length=config["max_length"],
                num_beams=config.get("num_beams", 4),
            )
            for name, config in self._difficulty_presets.items()
        }

        return SummaryResult(
            easy=difficulty_outputs["easy"],
            intermediate=difficulty_outputs["intermediate"],
            technical=difficulty_outputs["technical"],
            chunk_count=len(chunks),
            source_characters=len(cleaned),
        )

    def _ensure_tokenizer(self):
        if self._tokenizer is None:
            with self._lock:
                if self._tokenizer is None:
                    logger.info("Loading tokenizer for %s", self.model_name)
                    self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                    # Set model_max_length if not already set (fixes truncation warning)
                    if not hasattr(self._tokenizer, 'model_max_length') or self._tokenizer.model_max_length is None:
                        self._tokenizer.model_max_length = 1024  # Safe default for DistilBART
        return self._tokenizer

    def _ensure_pipeline(self):
        if self._pipeline is None:
            with self._lock:
                if self._pipeline is None:
                    logger.info("Loading summarization pipeline for %s", self.model_name)
                    model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
                    tokenizer = self._ensure_tokenizer()
                    self._pipeline = pipeline(
                        "summarization",
                        model=model,
                        tokenizer=tokenizer,
                        device=self.device,
                    )
        return self._pipeline

    def _chunk_text(self, text: str, tokenizer) -> List[str]:
        tokens = tokenizer.encode(text, add_special_tokens=False)
        if len(tokens) <= self.chunk_token_length:
            return [text]

        chunks = []
        for start in range(0, len(tokens), self.chunk_token_length):
            end = min(start + self.chunk_token_length, len(tokens))
            token_slice = tokens[start:end]
            chunk_text = tokenizer.decode(token_slice, skip_special_tokens=True, clean_up_tokenization_spaces=True)
            chunks.append(chunk_text.strip())
        return chunks

    def _run_pipeline(self, text: str, *, min_length: int, max_length: int, num_beams: int) -> str:
        summarizer = self._ensure_pipeline()
        max_length = max(min_length + 10, max_length)
        try:
            summary = summarizer(
                text,
                min_length=min_length,
                max_length=max_length,
                num_beams=num_beams,
                do_sample=False,
                truncation=True,
            )
        except RuntimeError as exc:  # typically CUDA OOM or max_length issues
            logger.warning("Summarization failed, retrying with adjusted parameters: %s", exc)
            summary = summarizer(
                text,
                min_length=max(10, int(min_length * 0.6)),
                max_length=max(20, int(max_length * 0.8)),
                num_beams=max(2, int(num_beams / 2)),
                do_sample=False,
                truncation=True,
            )

        return summary[0]["summary_text"].strip()


document_summarizer = DocumentSummarizer()
