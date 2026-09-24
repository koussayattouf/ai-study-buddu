import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = "openai/gpt-oss-20b"

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

def chunk_text(text: str, max_chars: int = 6000) -> list[str]:
    """Split long text into pieces that fit comfortably in one request."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    if len(paragraphs) <= 1:
        return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) < max_chars:
            current += p + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = p + "\n\n"
    if current:
        chunks.append(current.strip())

    final = []
    for c in chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            final.extend(c[i:i + max_chars] for i in range(0, len(c), max_chars))

    return final

def _call_llm(system: str, user: str, json_mode: bool = False) -> str:
    """Send one request to Groq and return the assistant's reply text."""
    kwargs = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def generate_summary(text: str) -> str:
    chunks = chunk_text(text)
    partials = []
    for i, chunk in enumerate(chunks, 1):
        partials.append(
            _call_llm(
                "You are an expert study assistant. Summarize text clearly "
                "with bullet points and key concepts.",
                f"Summarize part {i}/{len(chunks)}:\n\n{chunk}",
            )
        )

    if len(partials) == 1:
        return partials[0]

    return _call_llm(
        "Combine these partial summaries into one coherent, well-structured "
        "summary with a title, overview, and key bullet points.",
        "\n\n".join(partials),
    )