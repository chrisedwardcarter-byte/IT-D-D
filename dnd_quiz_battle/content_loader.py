"""Utilities for ingesting learning materials from different sources."""
from __future__ import annotations

import importlib.util
from pathlib import Path


class UnsupportedFileTypeError(ValueError):
    """Raised when a provided file cannot be processed."""


def load_content_from_file(path: str | Path) -> str:
    """Load textual content from PowerPoint, PDF, or plain-text files."""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    suffix = file_path.suffix.lower()
    if suffix in {".ppt", ".pptx"}:
        return _load_from_pptx(file_path)
    if suffix == ".pdf":
        return _load_from_pdf(file_path)
    if suffix in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8")

    raise UnsupportedFileTypeError(
        f"Unsupported file type '{file_path.suffix}'. Supported formats are PPT, PPTX, PDF, TXT, and MD."
    )


def _load_from_pptx(path: Path) -> str:
    if importlib.util.find_spec("pptx") is None:
        raise ModuleNotFoundError(
            "python-pptx is required to read PowerPoint files. Install it with `pip install python-pptx`."
        )
    from pptx import Presentation

    presentation = Presentation(path)
    text_chunks = []
    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                text_chunks.append(shape.text)
    return "\n".join(text_chunks)


def _load_from_pdf(path: Path) -> str:
    if importlib.util.find_spec("pdfplumber") is None:
        raise ModuleNotFoundError(
            "pdfplumber is required to read PDF files. Install it with `pip install pdfplumber`."
        )
    import pdfplumber

    text_chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            text_chunks.append(text)
    return "\n".join(text_chunks)


__all__ = ["load_content_from_file", "UnsupportedFileTypeError"]
