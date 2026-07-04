"""
core/ingest.py — loading the evidence inventory and normalizing job descriptions.

No LLM calls here on purpose: what evidence exists and what the JD literally
says must stay auditable and reproducible.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


def load_inventory(path: str) -> dict:
    """Load the evidence inventory from YAML. Ships no sample data — a
    missing file just means an empty inventory, filled in via the UI."""
    p = Path(path)
    if not p.exists():
        return {"entries": []}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    data.setdefault("entries", [])
    return data


def save_inventory(path: str, inv: dict) -> None:
    """Write the evidence inventory to YAML, creating the parent dir if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(inv, sort_keys=False), encoding="utf-8")


def normalize_jd(text: str) -> str:
    """Strip HTML and collapse whitespace. The JD is untrusted input — treated
    as data only, capped in length so it can't be used to blow up prompt cost."""
    stripped = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", stripped).strip()[:15000]


def schema_errors(inv: dict) -> list[str]:
    """Validate the inventory shape: every entry needs id/claim/evidence/tags,
    ids must be unique, tags must be a list."""
    errs, ids = [], set()
    for i, e in enumerate(inv.get("entries", [])):
        for f in ("id", "claim", "evidence", "tags"):
            if not e.get(f):
                errs.append(f"entry {i}: missing '{f}'")
        eid = e.get("id")
        if eid:
            if eid in ids:
                errs.append(f"duplicate id '{eid}'")
            ids.add(eid)
        if e.get("tags") and not isinstance(e["tags"], list):
            errs.append(f"entry {i}: tags must be a list")
    return errs
