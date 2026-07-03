"""
core/validate.py — the anti-fabrication guard.

Deliberately has zero LLM calls: this is the deterministic backstop that
catches anything rewrite() invents, regardless of how it was generated.
A bullet passes only if every number and every named skill/tool/proper noun
it states is traceable, verbatim, to the cited entry's own claim/evidence text.
"""

from __future__ import annotations

import re

# Sentence-initial capitals that are just grammar, not a claim about a skill/tool/employer.
_ALLOW = {
    "led", "certified", "improved", "managed", "administered", "delivered", "drove",
    "built", "owned", "coordinated", "developed", "designed", "created", "implemented",
    "established", "streamlined", "enhanced", "achieved", "reduced", "increased",
    "directed", "oversaw", "spearheaded", "facilitated", "collaborated", "partnered",
    "supported", "executed", "the", "this", "that", "these", "those", "a", "an",
    "and", "for", "with", "using", "via", "across", "within",
}


def validate_bullets(bullets: list[dict], inventory: dict) -> list[dict]:
    by_id = {e["id"]: e for e in inventory.get("entries", [])}
    out = []
    for b in bullets:
        e = by_id.get(b.get("evidence_id"))
        if e is None:
            out.append({**b, "status": "blocked",
                        "violation": f"unknown evidence_id {b.get('evidence_id')!r}"})
            continue

        hay = (e.get("claim", "") + " " + e.get("evidence", "")).lower()
        text = b.get("text", "")
        bad = None

        # every number/metric in the bullet must be traceable to the evidence
        for n in re.findall(r"\d[\d,.]*%?", text):
            if n.rstrip("%") not in hay:
                bad = n
                break

        # every named skill/tool/proper noun must be traceable too; common
        # sentence-initial words and CV action verbs are exempt
        if bad is None:
            for tok in re.findall(r"\b[A-Z][A-Za-z]{2,}\b", text):
                if tok.lower() not in hay and tok.lower() not in _ALLOW:
                    bad = tok
                    break

        if bad:
            out.append({**b, "status": "blocked",
                        "violation": f'token "{bad}" not found in evidence {e["id"]}'})
        else:
            out.append({**b, "status": "ok", "violation": None})
    return out
