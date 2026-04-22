from __future__ import annotations
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config.configuration import settings
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Doğru başlatma:
genai.configure(api_key=settings.GOOGLE_API_KEY)


llm_client = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL_NAME or "gemini-2.5-flash",
    google_api_key=settings.GOOGLE_API_KEY
)
