# VeriText AI — AI-Based Plagiarism & Paraphrasing Checker

A locally runnable document review tool for finding exact/near-exact overlap and possible semantic similarity against references you provide. It keeps source comparison separate from exploratory writing-pattern analysis. Results are indicators for human review, never a determination of plagiarism or AI authorship.

## Features

- Compare pasted text or TXT, PDF, and DOCX submissions with up to 50 reference files (subject to a combined text-size limit).
- Word and character n-gram TF-IDF similarity, normalized exact overlap, and local multilingual SentenceTransformer embeddings.
- Token-level evidence highlights, PDF page attribution, reviewer notes and statuses, citation suggestions, and detailed PDF export.
- Opt-in reference library stored in the browser's IndexedDB; saved files never leave this device.
- OCR for image-based PDF pages through the installed local Tesseract OCR engine.
- Standalone mode for text-pattern features; it does not search the web or an external source corpus.
- Temporary in-memory processing for unsaved documents. Saved references remain in local browser storage until removed.
- Responsive React UI, FastAPI Swagger docs, and configurable local thresholds.

## Requirements

Python 3.11+ (Python 3.13 may work depending on available PyTorch wheels), Node.js 20+, npm, and Tesseract OCR. The multilingual model downloads on the first semantic scan (about 470 MB). A network connection is needed unless it is already cached. To run without embeddings, set `VERITEXT_ENABLE_SEMANTIC=false`; exact and lexical checks remain active.

## Run locally

In two terminals:

```bash
cd backend
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8137
```

```bash
cd frontend
npm install
VITE_API_URL=http://127.0.0.1:8137/api npm run dev
```

Open http://localhost:5173. API docs are at http://localhost:8137/docs. Copy `backend/.env.example` to `backend/.env` if you want custom settings; the backend loads that file on startup. Frontend API URL can be set with `VITE_API_URL` (default `http://127.0.0.1:8137/api`).

### Windows notes

Use PowerShell activation command above. If script execution is restricted, use `backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt` and `backend/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8137` from the backend directory. In PowerShell, start the frontend with `$env:VITE_API_URL="http://127.0.0.1:8137/api"; npm run dev`.

### Convenience startup

Run `./dev.sh` on macOS/Linux after setup. It starts backend and frontend in one terminal and stops both on Ctrl+C.

## Configuration

See [backend/.env.example](backend/.env.example): model name, OCR language, semantic enablement, upload size, text and reference limits, lexical and semantic thresholds, and allowed frontend origins. Cross-language semantic matching is enabled by default. OCR language data must be installed in Tesseract. Thresholds change backend behavior without frontend edits. Unsaved files are held in memory during requests, with limits enforced before parsing.

## Architecture

- `backend/app/api`: HTTP routes and request validation.
- `backend/app/services/document_parser.py`: TXT/PDF/DOCX extraction, page metadata, and local OCR fallback.
- `backend/app/services/matching_engine.py`: passage splitting, chunked TF-IDF/embedding comparisons, evidence highlights, page attribution, coverage, and exploratory writing signals.
- `backend/app/models/embedding_model.py`: lazy CPU model loading and health state.
- `backend/app/services/report_generator.py`: downloadable PDF.
- `frontend/src/pages/App.tsx`: responsive analysis and results UI; `src/services/api.ts` handles API calls.

## Metric definitions and limitations

- **Matched text coverage**: word count in distinct submitted passages flagged by configured matching rules divided by submitted word count; each supplied reference passage can contribute to at most one flagged match per scan. It is unavailable without references and is not a plagiarism percentage.
- **Lexical similarity**: a blend of word uni/bi-gram and character 3–5 gram TF-IDF cosine similarity.
- **Semantic similarity**: embedding cosine similarity from the configured local multilingual SentenceTransformer model. Scores can reflect shared concepts, not copying.
- **Writing-pattern index**: a transparent exploratory blend of sentence-length variation and lexical diversity. It is not a classifier, probability, or validated AI authorship signal. Never use it alone to accuse or penalize an author.

No web-wide or publisher corpus is searched. Human review of source context, quotation, attribution, and common terminology is necessary.

## Tests

```bash
cd backend
PYTHONPATH=. .venv/bin/pytest -q
```

Tests use synthetic text and generated TXT/PDF/DOCX content. The semantic-ranking test injects deterministic embeddings so tests do not need a model download; they do not claim a measured real-world detection accuracy.

## Troubleshooting

- **Model download fails / offline**: set `VERITEXT_ENABLE_SEMANTIC=false`, or download/cache the configured Hugging Face model before going offline. Restart the API after changing environment variables.
- **Python dependency install fails**: use Python 3.11 or 3.12 for the broadest ML wheel compatibility; create a fresh virtual environment and retry.
- **Port conflict**: choose another backend port (for example `8138`) and set `VITE_API_URL=http://127.0.0.1:8138/api`; update `VERITEXT_CORS_ORIGINS` only if you also change the frontend port.
- **Scanned PDF OCR fails**: install Tesseract OCR and the selected language's trained data, then restart the backend. OCR can misread text; verify the page image before using a result.
- **Citation helper**: it formats source details you enter; it does not search for or verify publication metadata.
