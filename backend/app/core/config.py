from dotenv import load_dotenv
load_dotenv()

import os

MODEL_NAME = os.getenv("VERITEXT_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
ENABLE_SEMANTIC = os.getenv("VERITEXT_ENABLE_SEMANTIC", "true").lower() == "true"
MAX_UPLOAD_MB = int(os.getenv("VERITEXT_MAX_UPLOAD_MB", "12"))
MAX_TEXT_CHARS = int(os.getenv("VERITEXT_MAX_TEXT_CHARS", "200000"))
MAX_REFERENCES = int(os.getenv("VERITEXT_MAX_REFERENCES", "8"))
LEXICAL_THRESHOLD = float(os.getenv("VERITEXT_LEXICAL_THRESHOLD", "0.28"))
SEMANTIC_THRESHOLD = float(os.getenv("VERITEXT_SEMANTIC_THRESHOLD", "0.72"))
CORS_ORIGINS = os.getenv("VERITEXT_CORS_ORIGINS", "http://localhost:5173").split(",")
