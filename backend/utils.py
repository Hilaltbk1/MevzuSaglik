from __future__ import annotations
from dotenv import load_dotenv  # 1. Bunu ekle

# 2. DİĞER HER ŞEYDEN ÖNCE ÇALIŞTIR
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from backend.config.configuration import Settings
from backend.llm_client import llm_client
from backend.routers import search, history, session_router, admin, add_documents, billing, health
import google.generativeai as genai


def create_app() -> FastAPI:
    app = FastAPI(title="MevzuSaglik")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(search.router)
    app.include_router(history.router)
    app.include_router(session_router.router)
    app.include_router(add_documents.router)
    app.include_router(admin.router)
    app.include_router(health.router)
    app.include_router(billing.router)
    return app
