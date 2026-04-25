from __future__ import annotations
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config.configuration import settings
import google.generativeai as genai
from dotenv import load_dotenv
from backend.logger import logger

load_dotenv()

logger.info("LLM client başlatılıyor...")

try:
    # Doğru başlatma:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    logger.info("Google Generative AI API'si başarıyla yapılandırıldı")
    
    llm_client = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME or "gemini-2.5-flash",
        google_api_key=settings.GOOGLE_API_KEY
    )
    logger.info(f"LLM client başarıyla oluşturuldu: {settings.LLM_MODEL_NAME}")
    
except Exception as e:
    logger.error(f"LLM client oluşturma hatası: {e}")
    raise
