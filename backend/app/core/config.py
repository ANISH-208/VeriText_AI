from dotenv import load_dotenv
load_dotenv()

import os

MODEL_NAME = os.getenv("VERITEXT_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
ENABLE_SEMANTIC = os.getenv("VERITEXT_ENABLE_SEMANTIC", "true").lower() == "true"
MAX_UPLOAD_MB = int(os.getenv("VERITEXT_MAX_UPLOAD_MB", "12"))
MAX_TEXT_CHARS = int(os.getenv("VERITEXT_MAX_TEXT_CHARS", "200000"))
MAX_REFERENCES = int(os.getenv("VERITEXT_MAX_REFERENCES", "50"))
MAX_TOTAL_REFERENCE_CHARS = int(os.getenv("VERITEXT_MAX_TOTAL_REFERENCE_CHARS", "2000000"))
OCR_LANGUAGE = os.getenv("VERITEXT_OCR_LANGUAGE", "eng")
LEXICAL_THRESHOLD = float(os.getenv("VERITEXT_LEXICAL_THRESHOLD", "0.28"))
SEMANTIC_THRESHOLD = float(os.getenv("VERITEXT_SEMANTIC_THRESHOLD", "0.72"))
CORS_ORIGINS = os.getenv("VERITEXT_CORS_ORIGINS", "http://localhost:5173").split(",")
