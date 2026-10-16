from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from app.core.config import MAX_REFERENCES, MAX_TEXT_CHARS
from app.models.embedding_model import status
from app.schemas.requests import TextAnalysisRequest
from app.services.document_parser import read_upload
from app.services.matching_engine import analyze
from app.services.report_generator import create_pdf

router = APIRouter(prefix="/api")

@router.get("/health")
def health():
    return {"status": "ok", "semantic_model": status(), "privacy": "Documents are processed in memory and are not retained."}

@router.post("/analyze/text")
def analyze_text(request: TextAnalysisRequest):
    if len(request.references) > MAX_REFERENCES:
        raise HTTPException(422, f"At most {MAX_REFERENCES} references are allowed.")
    for ref in request.references:
        if not isinstance(ref.get("filename"), str) or not isinstance(ref.get("text"), str):
            raise HTTPException(422, "Each reference needs filename and text fields.")
        if len(ref["text"]) > MAX_TEXT_CHARS:
            raise HTTPException(413, "A reference exceeds the configured text length limit.")
    if len(request.text) > MAX_TEXT_CHARS:
        raise HTTPException(413, "Submitted text exceeds the configured limit.")
    try:
        return analyze(request.text, request.references)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/analyze/standalone")
def analyze_standalone(request: TextAnalysisRequest):
    try:
        return analyze(request.text, [], standalone=True)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/analyze/files")
async def analyze_files(submission: UploadFile | None = File(default=None), submitted_text: str = Form(default=""), references: list[UploadFile] = File(default=[])):
    if len(references) > MAX_REFERENCES:
        raise HTTPException(422, f"At most {MAX_REFERENCES} reference files are allowed.")
    if submission is None and not submitted_text.strip():
        raise HTTPException(422, "Provide submitted_text or upload a submission document.")
    if len(submitted_text) > MAX_TEXT_CHARS:
        raise HTTPException(413, "Submitted text exceeds the configured limit.")
    submitted = await read_upload(submission) if submission else submitted_text
    if len(submitted) > MAX_TEXT_CHARS:
        raise HTTPException(413, "Submitted document exceeds the configured text length limit.")
    refs = []
    for ref in references:
        ref_text = await read_upload(ref)
        if len(ref_text) > MAX_TEXT_CHARS:
            raise HTTPException(413, f"Reference {ref.filename or 'document'} exceeds the configured text length limit.")
        refs.append({"filename": ref.filename or "reference", "text": ref_text})
    try:
        return analyze(submitted, refs, standalone=not refs)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/reports/pdf")
def report_pdf(report: dict):
    try:
        content = create_pdf(report)
    except Exception as exc:
        raise HTTPException(422, "Could not generate a report from this analysis.") from exc
    return Response(content, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=veritext-analysis.pdf"})
