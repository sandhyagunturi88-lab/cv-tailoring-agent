from __future__ import annotations

from fastapi import APIRouter

from backend import config
from backend.schemas import BulletsResponse, ValidateRequest
from core.ingest import load_inventory
from core.validate import validate_bullets

router = APIRouter(tags=["validate"])


@router.post("/validate", response_model=BulletsResponse)
def validate(req: ValidateRequest) -> BulletsResponse:
    inventory = load_inventory(config.INVENTORY_PATH)
    bullets = [b.model_dump() for b in req.bullets]
    validated = validate_bullets(bullets, inventory)
    return BulletsResponse(bullets=validated)
