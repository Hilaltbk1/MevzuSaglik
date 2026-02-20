from fastapi import FastAPI
from openai import OpenAI
from starlette.middleware.cors import CORSMiddleware
from config.configuration import Settings
from routers import search, history

settings = Settings()

# Doğru başlatma:
llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def create_app() -> FastAPI:

    app = FastAPI(title="MevzuSaglik")

    def initrouters(app:FastAPI):
        app.include_router(search.router)
        app.include_router(history.router)

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
