from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend import config
from backend.schemas import CVUploadResponse
from core.extract import extract_cv_text

router = APIRouter(tags=["import"])

ALLOWED_CV_SUFFIXES = {".docx", ".pdf", ".pptx"}


@router.post("/cv/upload", response_model=CVUploadResponse)
async def upload_cv(file: UploadFile = File(...)) -> CVUploadResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_CV_SUFFIXES:
        raise HTTPException(status_code=422, detail=f"Unsupported file type: {suffix or '(none)'}")

    data = await file.read()
    max_bytes = config.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {config.MAX_UPLOAD_MB} MB limit")

    try:
        text = extract_cv_text(file.filename, data)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    (config.UPLOAD_DIR / stored_name).write_bytes(data)

    return CVUploadResponse(
        original_filename=file.filename,
        stored_as=stored_name,
        text=text,
        char_count=len(text),
    )
