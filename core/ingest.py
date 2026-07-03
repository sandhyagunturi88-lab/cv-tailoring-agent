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


def normalize_jd(text: str) -> str:
    """Strip HTML and collapse whitespace. The JD is untrusted input — treated
    as data only, capped in length so it can't be used to blow up prompt cost."""
    stripped = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", stripped).strip()[:15000]
