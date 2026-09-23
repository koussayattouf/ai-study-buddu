from pypdf import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """Read every page of a PDF and join the text."""
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages)


def extract_text_from_txt(file_path: str) -> str:
    """Read a plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_document(file_path: str) -> str:
    """Pick the right extractor based on file extension."""
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    return extract_text_from_txt(file_path)