from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import CORS_ORIGINS

app = FastAPI(title="VeriText AI", version="1.0.0", description="Local document similarity indicators for human review.")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])
app.include_router(router)
