
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

    return extract_text_from_txt(file_path)

import markdown
from markdown_pdf import MarkdownPdf, Section


def save_summary(text: str, output_file: str = "summary.md") -> str:
    """Generate a summary and save it as markdown. Returns the summary text."""
    summary = generate_summary(text)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(summary)
    return summary


def md_to_pdf(md_file: str = "summary.md", pdf_file: str = "summary.pdf") -> None:
    """Convert a markdown file to PDF using the installed libraries."""
    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(html))
    pdf.save(pdf_file)
    print(f"Wrote {pdf_file}")
def summary_to_pdf_bytes(summary_md: str) -> bytes:
    """Convert a summary markdown string to PDF bytes (no temp files left behind)."""
    import tempfile
    import os
    from contextlib import suppress
    import markdown
    from markdown_pdf import MarkdownPdf, Section

    # Convert markdown to HTML
    html = markdown.markdown(summary_md, extensions=["tables", "fenced_code"])

    # Use a temp file for the PDF output
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_path = tmp.name

    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(html))
        pdf.save(pdf_path)

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    finally:
        with suppress(OSError):
            os.unlink(pdf_path)

    return pdf_bytes
def _safe_json(raw: str) -> dict:
    """Parse JSON that may be wrapped in markdown fences."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def generate_quiz(text: str, num_questions: int = 5) -> list[dict]:
    system_prompt = (
        "You are a quiz generator. "
        "You ONLY output valid JSON. "
        "No prose, no markdown, no code fences — just a JSON object."
    )

    user_prompt = f"""Generate exactly {num_questions} multiple-choice questions based on the text below.

Respond with a single JSON object matching this exact structure:
{{
  "questions": [
    {{
      "question": "string",
      "options": ["A) string", "B) string", "C) string", "D) string"],
      "answer": "A",
      "explanation": "one short sentence"
    }}
  ]
}}

Rules:
- Exactly {num_questions} questions.
- Exactly 4 options per question, each prefixed with "A) ", "B) ", "C) ", "D) ".
- "answer" is a single letter: A, B, C, or D.
- "explanation" is under 20 words.
- Respond with JSON only.

Text:
{text[:6000]}
"""

    raw = _call_llm(system_prompt, user_prompt, json_mode=True)
    return _safe_json(raw).get("questions", [])