import io
from docx import Document
from reportlab.pdfgen import canvas
from app.services.document_parser import parse_bytes
from app.services.matching_engine import analyze
from app.utils.text_utils import normalize_text, split_passages

ORIGINAL = "The quick brown fox jumps over the lazy dog near the river bank. This example sentence contains enough words to be useful for comparing copied material across documents."

import pytest

@pytest.fixture(autouse=True)
def no_model_download(monkeypatch):
    import app.services.matching_engine as engine
    monkeypatch.setattr(engine, "encode", lambda texts: None)


def test_normalize_and_split():
    assert normalize_text(" a  b\r\n\r\n\r\nc ") == "a b\n\nc"
    assert len(split_passages("First sentence. Second sentence!")) == 2


def test_exact_and_near_copy_detected():
    exact = analyze(ORIGINAL, [{"filename": "source.txt", "text": ORIGINAL}])
    assert exact["metrics"]["exact_match_count"] >= 1
    near = analyze("The quick brown fox jumps over a lazy dog beside the river bank. This example sentence contains enough words to be useful for comparing copied material across documents.", [{"filename": "src", "text": ORIGINAL}])
    assert near["matches"]
    assert near["matches"][0]["category"] in {"near_exact", "exact"}


def test_unrelated_and_empty():
    report = analyze("Quantum mechanics describes particles using probability amplitudes and wave functions.", [{"filename": "src", "text": ORIGINAL}])
    assert report["matches"] == []
    assert report["metrics"]["matched_text_coverage"] == 0
    try:
        analyze("", [])
        assert False
    except ValueError:
        pass


def test_multiple_references_and_coverage():
    report = analyze(ORIGINAL, [{"filename": "one", "text": "A distinct sentence with unrelated words."}, {"filename": "two", "text": ORIGINAL}])
    assert len(report["references"]) == 2
    assert report["metrics"]["matched_text_coverage"] > 0
    assert report["matches"][0]["reference_name"] == "two"


def test_parse_txt_docx_pdf_and_invalid():
    assert parse_bytes("a.txt", b"Hello text") == "Hello text"
    doc = Document(); doc.add_paragraph("Word document text")
    buffer = io.BytesIO(); doc.save(buffer)
    assert "Word document" in parse_bytes("a.docx", buffer.getvalue())
    pdf = io.BytesIO(); c = canvas.Canvas(pdf); c.drawString(50, 750, "PDF document text"); c.save()
    assert "PDF document" in parse_bytes("a.pdf", pdf.getvalue())
    try:
        parse_bytes("bad.exe", b"no")
        assert False
    except ValueError:
        pass


def test_standalone_and_report_pdf():
    report = analyze(ORIGINAL, [], standalone=True)
    assert report["standalone"] is True
    assert report["metrics"]["matched_text_coverage"] is None
    from app.services.report_generator import create_pdf
    assert create_pdf(report).startswith(b"%PDF")


def test_semantic_paraphrase_signal(monkeypatch):
    import numpy as np
    import app.services.matching_engine as engine
    def fake_encode(texts):
        vectors=[]
        for text in texts:
            if "submitted" in text:
                vectors.append([1.0, 0.0])
            elif "reference" in text:
                vectors.append([0.95, 0.3122499])
            else:
                vectors.append([0.0, 1.0])
        return np.asarray(vectors)
    monkeypatch.setattr(engine, "encode", fake_encode)
    report=engine.analyze("submitted: Researchers examined how sleep affects memory consolidation.", [{"filename":"paper.txt","text":"reference: The study investigated the influence of rest on the stabilization of recollections."}])
    assert report["matches"] and report["matches"][0]["category"] == "semantic"


def test_api_health_and_validation():
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.post("/api/analyze/text", json={"text":""}).status_code == 422
    invalid=client.post("/api/analyze/files", files={"submission":("x.exe",b"bad","application/octet-stream")})
    assert invalid.status_code == 415


def test_threshold_and_reference_deduplication(monkeypatch):
    import app.services.matching_engine as engine
    near="The quick brown fox quickly jumps above a lazy dog close to the river bank. This example sentence contains sufficient words to be useful for comparing copied material across documents."
    monkeypatch.setattr(engine, "LEXICAL_THRESHOLD", 0.99)
    monkeypatch.setattr(engine, "SEMANTIC_THRESHOLD", 1.0)
    assert engine.analyze(near, [{"filename":"src", "text":ORIGINAL}])["matches"] == []
    monkeypatch.setattr(engine, "LEXICAL_THRESHOLD", 0.28)
    repeated=engine.analyze(ORIGINAL + " " + ORIGINAL, [{"filename":"src", "text":ORIGINAL}])
    assert repeated["metrics"]["exact_match_count"] == 2
    assert repeated["metrics"]["matched_text_coverage"] < 100


def test_api_analysis_schema_and_pdf_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    response=client.post("/api/analyze/text", json={"text":ORIGINAL,"references":[{"filename":"source.txt","text":ORIGINAL}]})
    assert response.status_code == 200
    payload=response.json()
    assert payload["metrics"]["exact_match_count"] >= 1
    assert payload["matches"][0]["reference_name"] == "source.txt"
    pdf=client.post("/api/reports/pdf", json=payload)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
