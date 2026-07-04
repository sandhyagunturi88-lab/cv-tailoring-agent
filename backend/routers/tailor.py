from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend import config
from backend.schemas import (
    BulletsResponse,
    FitScoreRequest,
    FitScoreResponse,
    KeywordsRequest,
    KeywordsResponse,
    MatchRequest,
    MatchResponse,
    RewriteRequest,
    TailorRunRequest,
    TailorRunResponse,
)
from core.ingest import load_inventory, normalize_jd
from core.llm import LLMError
from core.report import fit_score
from core.tailor import extract_keywords, match, rewrite
from core.validate import validate_bullets

router = APIRouter(tags=["tailor"])


@router.post("/tailor/keywords", response_model=KeywordsResponse)
def tailor_keywords(req: KeywordsRequest) -> KeywordsResponse:
    try:
        keywords = extract_keywords(normalize_jd(req.jd))
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return KeywordsResponse(keywords=keywords)


@router.post("/tailor/match", response_model=MatchResponse)
def tailor_match(req: MatchRequest) -> MatchResponse:
    inventory = load_inventory(config.INVENTORY_PATH)
    keywords = [k.model_dump() for k in req.keywords]
    hits, gaps = match(keywords, inventory)
    return MatchResponse(hits=hits, gaps=gaps)


@router.post("/tailor/run", response_model=TailorRunResponse)
def tailor_run(req: TailorRunRequest) -> TailorRunResponse:
    inventory = load_inventory(config.INVENTORY_PATH)
    try:
        keywords = extract_keywords(normalize_jd(req.jd))
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    hits, gaps = match(keywords, inventory)
    score = fit_score(hits, gaps, keywords)
    return TailorRunResponse(keywords=keywords, hits=hits, gaps=gaps, score=score)


@router.post("/tailor/rewrite", response_model=BulletsResponse)
def tailor_rewrite(req: RewriteRequest) -> BulletsResponse:
    inventory = load_inventory(config.INVENTORY_PATH)
    by_id = {e["id"]: e for e in inventory.get("entries", [])}
    entries = [by_id[i] for i in req.entry_ids if i in by_id]
    keywords = [k.model_dump() for k in req.keywords]
    try:
        raw = rewrite(entries, keywords)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    bullets = validate_bullets(raw, inventory)
    return BulletsResponse(bullets=bullets)


@router.post("/fit-score", response_model=FitScoreResponse)
def compute_fit_score(req: FitScoreRequest) -> FitScoreResponse:
    hits = {k: [kw.model_dump() for kw in v] for k, v in req.hits.items()}
    gaps = [k.model_dump() for k in req.gaps]
    keywords = [k.model_dump() for k in req.keywords]
    return FitScoreResponse(score=fit_score(hits, gaps, keywords))
