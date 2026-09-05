"""Entrypoint for runners executing `uvicorn main:app` from inside the backend/ directory."""
import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.main import app

__all__ = ["app"]
