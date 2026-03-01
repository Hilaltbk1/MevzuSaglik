from google import genai
from config.configuration import Settings
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from routers import search, history, session_router

settings = Settings()

# Doğru başlatma:
genai.configure(api_key=settings.GOOGLE_API_KEY)

# llm_client olarak Gemini modelini tanımla
llm_client = genai.GenerativeModel('gemini-1.5-flash')

def create_app() -> FastAPI:

    app = FastAPI(title="MevzuSaglik")

    def initrouters(app:FastAPI):
        app.include_router(search.router)
        app.include_router(history.router)
        app.include_router(session_router.router)

    def configure_middleswares(app:FastAPI):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    configure_middleswares(app)
    initrouters(app)

    return app
