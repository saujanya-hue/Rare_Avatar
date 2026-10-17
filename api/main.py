"""Vercel Serverless Function Entrypoint for FastAPI."""
import os
import sys

# Compute paths
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
app_dir = os.path.join(backend_dir, "app")

for path in (root_dir, backend_dir, app_dir):
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

try:
    from backend.app.main import app
except Exception as e1:
    try:
        from app.main import app
    except Exception as e2:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        app = FastAPI(title="RareAvatar Serverless Diagnostics")
        @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
        async def fallback_diagnostic_handler(full_path: str):
            return JSONResponse(
                status_code=500,
                content={
                    "detail": f"Backend initialization error: {str(e1)} | {str(e2)}",
                    "path_requested": full_path,
                    "sys_path": sys.path[:5]
                }
            )
