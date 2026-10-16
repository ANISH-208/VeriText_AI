from io import BytesIO
from pathlib import Path
import pymupdf
from docx import Document
from fastapi import HTTPException, UploadFile
from app.core.config import MAX_UPLOAD_MB
from app.utils.text_utils import normalize_text

ALLOWED = {".txt", ".pdf", ".docx"}


def parse_bytes(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED:
        raise ValueError("Unsupported file type. Upload a TXT, PDF, or DOCX file.")
    if ext == ".txt":
        text = data.decode("utf-8-sig", errors="replace")
    elif ext == ".pdf":
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            text = "\n\n".join(page.get_text("text") for page in pdf)
        if not text.strip():
            raise ValueError(f"{filename}: no selectable text was found. Scanned PDFs need OCR, which is not included.")
    else:
        doc = Document(BytesIO(data))
        text = "\n\n".join(p.text for p in doc.paragraphs)
    text = normalize_text(text)
    if not text:
        raise ValueError(f"{filename}: the document contains no extractable text.")
    return text


async def read_upload(upload: UploadFile) -> str:
    name = upload.filename or "document"
    if Path(name).suffix.lower() not in ALLOWED:
        raise HTTPException(415, "Unsupported file type. Upload a TXT, PDF, or DOCX file.")
    data = await upload.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds the {MAX_UPLOAD_MB} MB limit.")
    try:
        return parse_bytes(name, data)
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc
