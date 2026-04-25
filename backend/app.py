"""
Minimal app file for ASGI servers.
This file avoids problematic imports that cause issues with Python 3.9.
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import create_app directly
    from backend.utils import create_app
    app = create_app()
    
    # Add basic routes if needed
    from fastapi import FastAPI
    
    # Ensure app is FastAPI instance
    if not isinstance(app, FastAPI):
        print("Warning: create_app() did not return a FastAPI instance")
        app = FastAPI()
    
    print("✓ App created successfully")
    
except Exception as e:
    print(f"✗ Error creating app: {e}")
    # Create a minimal app as fallback
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"message": "App is running but some imports failed", "error": str(e)}
    
    @app.get("/health")
    def health():
        return {"status": "ok"}

# Export app for ASGI
__all__ = ["app"]