# VeriText AI backend

FastAPI service for local document parsing, lexical and optional semantic comparison, writing-pattern signals, and PDF report generation.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8137
```

Swagger UI: http://localhost:8137/docs. The frontend defaults to `http://127.0.0.1:8137/api`. Set environment values from `.env.example` as needed. The SentenceTransformer model downloads on first semantic scan; set `VERITEXT_ENABLE_SEMANTIC=false` to use lexical checks only or preload `VERITEXT_MODEL_NAME` for offline operation. CPU inference is used. No uploaded file is saved to disk.
