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
    llm_client = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME or "gemini-2.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        max_output_tokens=768,  # uzun yanıtları kes — süre tavanı
        max_retries=1,  # kota/hata durumunda 100 sn değil ~3 sn'de hata dön
        timeout=45,  # LLM 45 sn'de cevap vermezse isteği bırak
    )
    logger.info(f"LLM client başarıyla oluşturuldu: {settings.LLM_MODEL_NAME}")
except Exception as e:
    logger.error(f"LLM client oluşturma hatası: {e}")
    raise
