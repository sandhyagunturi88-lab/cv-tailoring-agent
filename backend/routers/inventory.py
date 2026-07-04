from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend import config
from backend.schemas import InventoryDict, SchemaErrorsResponse
from core.ingest import load_inventory, save_inventory, schema_errors

router = APIRouter(tags=["inventory"])


@router.get("/inventory")
def get_inventory() -> dict:
    return load_inventory(config.INVENTORY_PATH)


@router.put("/inventory")
def put_inventory(inv: InventoryDict) -> dict:
    data = inv.model_dump()
    errs = schema_errors(data)
    if errs:
        raise HTTPException(status_code=422, detail={"errors": errs})
    save_inventory(config.INVENTORY_PATH, data)
    return data


@router.post("/inventory/validate", response_model=SchemaErrorsResponse)
def validate_inventory(inv: InventoryDict) -> SchemaErrorsResponse:
    return SchemaErrorsResponse(errors=schema_errors(inv.model_dump()))
