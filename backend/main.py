"""
backend/main.py — FastAPI app entrypoint.

Run: uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import config  # noqa: F401 — imported first so .env loads before core.*
from backend.routers import export, inventory, tailor, uploads, validate

app = FastAPI(title="CV Tailoring Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory.router)
app.include_router(uploads.router)
app.include_router(tailor.router)
app.include_router(validate.router)
app.include_router(export.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
