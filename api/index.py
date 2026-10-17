"""Vercel Serverless Function Entrypoint for FastAPI."""
import os
import sys

# Ensure backend root is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
for path in (root_dir, backend_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

from backend.app.main import app
