import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional


def extract_text(file_path: str) -> str:
    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n\n".join(pages)


def get_preview(text: str, max_chars: int = 2000) -> str:
    return text[:max_chars]
