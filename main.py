"""Entrypoint for Render and ASGI runners executing `uvicorn main:app` from the repository root."""
from app.main import app

__all__ = ["app"]
