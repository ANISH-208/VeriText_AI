from functools import lru_cache
from app.core.config import ENABLE_SEMANTIC, MODEL_NAME

_model = None
_error: str | None = None


def status() -> dict:
    return {"enabled": ENABLE_SEMANTIC, "loaded": _model is not None, "model": MODEL_NAME, "error": _error}


def encode(texts: list[str]):
    global _model, _error
    if not ENABLE_SEMANTIC:
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(MODEL_NAME, device="cpu")
        except Exception as exc:
            _error = str(exc)
            return None
    try:
        return _model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    except Exception as exc:
        _error = str(exc)
        return None
