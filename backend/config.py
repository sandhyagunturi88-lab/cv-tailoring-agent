"""
backend/config.py — environment-driven configuration for the FastAPI backend.

Loaded first (before any `core.*` import) so `.env` is found via an explicit,
CWD-independent path — `core/llm.py`'s own bare `load_dotenv()` becomes a
harmless no-op second call.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=REPO_ROOT / ".env")

INVENTORY_PATH = os.environ.get("INVENTORY_PATH", str(REPO_ROOT / "data" / "inventory.yaml"))
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(REPO_ROOT / "data" / "uploads")))
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "10"))
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:8501").split(",") if o.strip()]
