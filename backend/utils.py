from langchain_google_genai import ChatGoogleGenerativeAI
# Harm ayarlarını direkt langchain_google_genai üzerinden alalım, diğeri hata veriyor olabilir
from langchain_google_genai import HarmCategory, HarmBlockThreshold
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from backend.config.configuration import Settings
from backend.routers import search, history, session_router
import google.generativeai as genai
settings = Settings()

# Doğru başlatma:
genai.configure(api_key=settings.GOOGLE_API_KEY)

# llm_client olarak Gemini modelini tanımla
llm_client = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GOOGLE_API_KEY,
    safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

                                   )

def create_app() -> FastAPI:

    app = FastAPI(title="MevzuSaglik")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from backend.routers import search, history, session_router
    app.include_router(search.router)
    app.include_router(history.router)
    app.include_router(session_router.router)



    return app
