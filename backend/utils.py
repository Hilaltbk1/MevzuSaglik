from __future__ import annotations
from dotenv import load_dotenv  # 1. Bunu ekle

# 2. DİĞER HER ŞEYDEN ÖNCE ÇALIŞTIR
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from backend.config.configuration import Settings
from backend.routers import search, history, session_router,admin
import google.generativeai as genai

from backend.services.Retrievers import retrieval_chain

settings = Settings()

# Doğru başlatma:
genai.configure(api_key=settings.GOOGLE_API_KEY)


llm_client = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GOOGLE_API_KEY
)


def create_app() -> FastAPI:
    # utils.py — create_app içine
    from backend.routers import health

    app = FastAPI(title="MevzuSaglik")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from backend.routers import search, history, session_router,add_documents
    app.include_router(search.router)
    app.include_router(history.router)
    app.include_router(session_router.router)
    app.include_router(add_documents.router)
    app.include_router(admin.router)
    app.include_router(health.router)
    return app
