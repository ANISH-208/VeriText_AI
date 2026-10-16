from io import BytesIO
from pathlib import Path
import pymupdf
from docx import Document
from fastapi import HTTPException, UploadFile
from app.core.config import MAX_UPLOAD_MB, OCR_LANGUAGE
from app.utils.text_utils import normalize_text

ALLOWED = {".txt", ".pdf", ".docx"}


def parse_document(filename: str, data: bytes, ocr_language: str | None = None) -> dict:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED:
        raise ValueError("Unsupported file type. Upload a TXT, PDF, or DOCX file.")
    pages: list[str] = []
    ocr_pages: list[int] = []
    if ext == ".txt":
        text = data.decode("utf-8-sig", errors="replace")
    elif ext == ".pdf":
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            for index, page in enumerate(pdf, start=1):
                page_text = page.get_text("text").strip()
                if len(page_text) < 40:
                    try:
                        page_text = page.get_textpage_ocr(language=ocr_language or OCR_LANGUAGE, dpi=180).extractText().strip()
                        if page_text:
                            ocr_pages.append(index)
                    except Exception as exc:
                        if not page_text:
                            raise ValueError(f"{filename}: OCR could not process page {index}. Install Tesseract OCR and language data for '{ocr_language or OCR_LANGUAGE}', then retry. ({exc})") from exc
                pages.append(page_text)
        text = "\n\n".join(p for p in pages if p)
        if not text.strip():
            raise ValueError(f"{filename}: no selectable text or readable OCR text was found.")
    else:
        doc = Document(BytesIO(data))
        text = "\n\n".join(p.text for p in doc.paragraphs)
    text = normalize_text(text)
    if not text:
        raise ValueError(f"{filename}: the document contains no extractable text.")
    return {"text": text, "pages": pages, "ocr_pages": ocr_pages}


def parse_bytes(filename: str, data: bytes) -> str:
    return parse_document(filename, data)["text"]


async def read_upload(upload: UploadFile, with_metadata: bool = False, ocr_language: str | None = None) -> str | dict:
    name = upload.filename or "document"
    if Path(name).suffix.lower() not in ALLOWED:
        raise HTTPException(415, "Unsupported file type. Upload a TXT, PDF, or DOCX file.")
    data = await upload.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds the {MAX_UPLOAD_MB} MB limit.")
    try:
        parsed = parse_document(name, data, ocr_language)
        return parsed if with_metadata else parsed["text"]
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc
