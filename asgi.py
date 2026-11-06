"""
ASGI entry point for Uvicorn.
This file provides a simple way to import the FastAPI app.
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app from backend.main
from backend.main import app

# Export the app for ASGI servers
__all__ = ["app"]