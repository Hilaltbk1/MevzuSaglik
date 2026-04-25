"""
ASGI entry point for Uvicorn.
This file provides a simple way to import the FastAPI app.
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app from backend.main_simple (Python 3.9 compatible)
try:
    from backend.main_simple import app
    print("✓ Using main_simple.py (Python 3.9 compatible)")
except ImportError as e:
    print(f"✗ Error importing main_simple: {e}")
    # Fallback to simple app
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="MevzuSaglik Fallback")
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    def root():
        return {"message": "MevzuSaglik API (Fallback)", "status": "ok"}
    
    @app.get("/health")
    def health():
        return {"status": "healthy", "python_version": "3.9.0"}

# Export the app for ASGI servers
__all__ = ["app"]