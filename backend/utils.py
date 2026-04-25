from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.config.configuration import Settings
from backend.llm_client import llm_client
from backend.routers import search, history, session_router, admin, add_documents, billing, health, auth_router
import google.generativeai as genai

from backend.logger import logger

# Limiter nesnesi oluştur
limiter = Limiter(key_func=get_remote_address)

def create_app() -> FastAPI:
    app = FastAPI(title="MevzuSaglik")

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    ALLOWED_ORIGINS = [
        "https://mevzusaglik.com.tr",
        "https://www.mevzusaglik.com.tr",
        "https://mevzusaglik.pages.dev",  # Cloudflare Pages önizleme adresi
        "https://mevzusaglik.mevzusaglik.workers.dev",  # Backend'in kendi adresi
        "http://localhost:8000",
        "http://localhost:3000",  # Genelde React/Vite kullanırsan lazım olur
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    app.include_router(search.router)
    app.include_router(history.router)
    app.include_router(session_router.router)
    app.include_router(add_documents.router)
    app.include_router(admin.router)
    app.include_router(health.router)
    app.include_router(billing.router)
    app.include_router(auth_router.router)
    return app
