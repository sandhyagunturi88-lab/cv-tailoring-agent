"""
client.py — requests-based wrapper the Streamlit frontend uses to call the
FastAPI backend. app.py never imports core/* directly; everything goes
through here so the two processes stay fully decoupled.

Run the backend with: uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import os

import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
_TIMEOUT = 30


class BackendError(Exception):
    """Raised with the backend's own error message (its `detail` field)."""


def _raise_for_status(resp: requests.Response) -> None:
    if resp.ok:
        return
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:
        detail = resp.text
    if isinstance(detail, dict) and "errors" in detail:
        detail = "\n".join(detail["errors"])
    raise BackendError(str(detail))


def is_backend_up() -> bool:
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return resp.ok
    except requests.RequestException:
        return False


def get_inventory() -> dict:
    resp = requests.get(f"{BACKEND_URL}/inventory", timeout=_TIMEOUT)
    _raise_for_status(resp)
    return resp.json()


def save_inventory(inv: dict) -> dict:
    resp = requests.put(f"{BACKEND_URL}/inventory", json=inv, timeout=_TIMEOUT)
    _raise_for_status(resp)
    return resp.json()


def validate_inventory(inv: dict) -> list[str]:
    resp = requests.post(f"{BACKEND_URL}/inventory/validate", json=inv, timeout=_TIMEOUT)
    _raise_for_status(resp)
    return resp.json()["errors"]


def upload_cv(filename: str, data: bytes) -> dict:
    files = {"file": (filename, data)}
    resp = requests.post(f"{BACKEND_URL}/cv/upload", files=files, timeout=_TIMEOUT)
    _raise_for_status(resp)
    return resp.json()


def run_tailor(jd: str) -> dict:
    resp = requests.post(f"{BACKEND_URL}/tailor/run", json={"jd": jd}, timeout=_TIMEOUT)
    _raise_for_status(resp)
    return resp.json()


def rewrite_bullets(entry_ids: list[str], keywords: list[dict]) -> list[dict]:
    resp = requests.post(
        f"{BACKEND_URL}/tailor/rewrite",
        json={"entry_ids": entry_ids, "keywords": keywords},
        timeout=_TIMEOUT,
    )
    _raise_for_status(resp)
    return resp.json()["bullets"]


def export_docx(bullets: list[str]) -> bytes:
    resp = requests.post(f"{BACKEND_URL}/export/docx", json={"bullets": bullets}, timeout=_TIMEOUT)
    _raise_for_status(resp)
    return resp.content
