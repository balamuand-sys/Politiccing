import fitz  # PyMuPDF


def extract_text(file_path: str) -> str:
    doc = fitz.open(file_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages)


def get_preview(text: str, max_chars: int = 3000) -> str:
    return text[:max_chars]
