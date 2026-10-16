# VeriText AI backend

FastAPI service for local TXT/PDF/DOCX parsing, OCR of scanned PDF pages, lexical and semantic comparison, page-aware evidence, and PDF report generation.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8137
```

Swagger UI: http://localhost:8137/docs. The frontend defaults to `http://127.0.0.1:8137/api`. Configure the model, reference limits, and OCR language in `.env.example`. The multilingual SentenceTransformer model downloads on first semantic scan (about 470 MB). Set `VERITEXT_ENABLE_SEMANTIC=false` for lexical-only operation or preload the model before going offline. CPU inference is used. Tesseract OCR and the selected language's trained data are required for scanned pages. Unsaved uploads are processed in memory; references saved by the user are kept in the browser's IndexedDB library and are not uploaded until selected for an analysis.
