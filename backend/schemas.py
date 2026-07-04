"""
backend/schemas.py — Pydantic request/response models for the FastAPI backend.

Backend-internal only: the Streamlit frontend never imports these, it only
speaks JSON over HTTP via client.py. Keeping this boundary means the backend's
schemas can change without ever touching the frontend process.
"""

from __future__ import annotations

from pydantic import BaseModel


class Entry(BaseModel):
    id: str
    claim: str
    evidence: str
    tags: list[str]


class Inventory(BaseModel):
    entries: list[Entry] = []


class InventoryDict(BaseModel):
    """Accepts loosely-typed entries so validation errors surface as our own
    schema_errors() messages instead of generic Pydantic 422s."""
    entries: list[dict] = []


class SchemaErrorsResponse(BaseModel):
    errors: list[str]


class TextResponse(BaseModel):
    text: str


class CVUploadResponse(BaseModel):
    original_filename: str
    stored_as: str
    text: str
    char_count: int


class Keyword(BaseModel):
    term: str
    priority: str


class KeywordsRequest(BaseModel):
    jd: str


class KeywordsResponse(BaseModel):
    keywords: list[Keyword]


class MatchRequest(BaseModel):
    keywords: list[Keyword]


class MatchResponse(BaseModel):
    hits: dict[str, list[Keyword]]
    gaps: list[Keyword]


class TailorRunRequest(BaseModel):
    jd: str


class TailorRunResponse(BaseModel):
    keywords: list[Keyword]
    hits: dict[str, list[Keyword]]
    gaps: list[Keyword]
    score: int


class RewriteRequest(BaseModel):
    entry_ids: list[str]
    keywords: list[Keyword]


class Bullet(BaseModel):
    text: str
    evidence_id: str
    status: str | None = None
    violation: str | None = None


class BulletsResponse(BaseModel):
    bullets: list[Bullet]


class ValidateRequest(BaseModel):
    bullets: list[Bullet]


class FitScoreRequest(BaseModel):
    hits: dict[str, list[Keyword]]
    gaps: list[Keyword]
    keywords: list[Keyword]


class FitScoreResponse(BaseModel):
    score: int


class ExportRequest(BaseModel):
    bullets: list[str]
