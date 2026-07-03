"""
tests/test_app_mock.py — formal suite for app.py's pipeline logic.

Runs WITHOUT streamlit installed (streamlit is stubbed) so it works in CI and
bare environments. Covers the mock backend, which doubles as the behavioral
spec for core/: when Phase 1 lands, port these cases to tests/test_tailor.py
and tests/test_validate.py against the real modules.

Run:  pytest tests/ -v
"""
import io
import sys
import types
from pathlib import Path

import pytest

# ---- stub streamlit so app.py's module-level code is importable ------------
st_stub = types.ModuleType("streamlit")


class _SS(dict):
    def __getattr__(self, k):
        return self.get(k)

    def __setattr__(self, k, v):
        self[k] = v


st_stub.session_state = _SS()
sys.modules.setdefault("streamlit", st_stub)

# ---- load only the logic section of app.py (everything before the UI) ------
APP = Path(__file__).resolve().parents[1] / "app.py"
_head = APP.read_text(encoding="utf-8").split("# App state")[0]
G: dict = {}
exec(compile(_head, str(APP), "exec"), G)

INV = G["SAMPLE_INVENTORY"]
st_stub.session_state.inventory = INV


# ---------------------------------------------------------------- schema ----
def test_schema_valid_sample():
    assert G["schema_errors"](INV) == []


def test_schema_missing_field_and_duplicate():
    bad = {"entries": [
        {"id": "a-1", "claim": "x", "evidence": "y", "tags": ["t"]},
        {"id": "a-1", "claim": "x", "evidence": "y", "tags": ["t"]},
        {"id": "", "claim": "", "evidence": "y", "tags": ["t"]},
    ]}
    errs = G["schema_errors"](bad)
    assert any("duplicate id 'a-1'" in e for e in errs)
    assert any("missing 'id'" in e for e in errs)
    assert any("missing 'claim'" in e for e in errs)
    # missing ids must not be reported as duplicates of each other
    assert sum("duplicate" in e for e in errs) == 1


def test_schema_tags_must_be_list():
    bad = {"entries": [{"id": "a", "claim": "c", "evidence": "e", "tags": "not-a-list"}]}
    assert any("tags must be a list" in e for e in G["schema_errors"](bad))


# ------------------------------------------------------------- pipeline ----
JD = ("Senior Scrum Master with ServiceNow and Terraform experience, "
      "stakeholder management, Jira dashboards")


def _run():
    jd = G["_mock_normalize_jd"](JD)
    kws = G["_mock_extract_keywords"](jd)
    hits, gaps = G["_mock_match"](kws, INV)
    return kws, hits, gaps


def test_normalize_strips_html_and_whitespace():
    out = G["_mock_normalize_jd"]("<b>Scrum</b>   Master\n\nrole")
    assert out == "Scrum Master role"


def test_gap_is_reported_never_matched():
    _, hits, gaps = _run()
    gap_terms = {g["term"] for g in gaps}
    assert "terraform" in gap_terms
    assert not any("terraform" in " ".join(k["term"] for k in v) for v in hits.values())


def test_match_finds_evidence_for_known_skills():
    _, hits, _ = _run()
    assert "exp-tcs-001" in hits           # scrum master / servicenow
    assert "skill-jira-001" in hits        # jira


def test_fit_score_weighting_must_times_three():
    kws = [{"term": "a", "priority": "must"}, {"term": "b", "priority": "nice"}]
    assert G["_mock_fit_score"]({"e1": [kws[0]]}, [kws[1]], kws) == 75  # 3/(3+1)


def test_fit_score_bounds():
    kws, hits, gaps = _run()
    s = G["_mock_fit_score"](hits, gaps, kws)
    assert 0 <= s <= 100


# ---------------------------------------------------------------- guard ----
def test_fabrication_seed_is_blocked():
    """THE non-negotiable test: an unevidenced skill must never pass."""
    kws, hits, _ = _run()
    entries = [e for e in INV["entries"] if e["id"] in hits]
    bullets = G["_mock_rewrite"](entries, kws)          # seeds a Terraform bullet
    validated = G["_mock_validate"](bullets, INV)
    blocked = [b for b in validated if b["status"] == "blocked"]
    assert any("Terraform" in b["text"] for b in blocked)
    assert all(b["violation"] for b in blocked)


def test_unknown_evidence_id_is_blocked():
    v = G["_mock_validate"]([{"text": "Led things", "evidence_id": "ghost-999"}], INV)
    assert v[0]["status"] == "blocked" and "unknown evidence_id" in v[0]["violation"]


def test_unevidenced_number_is_blocked():
    v = G["_mock_validate"](
        [{"text": "Improved delivery 40% using Jira", "evidence_id": "skill-jira-001"}], INV)
    assert v[0]["status"] == "blocked" and "40" in v[0]["violation"]


def test_clean_bullet_passes():
    v = G["_mock_validate"](
        [{"text": "Administered Jira boards for sprint dashboards", "evidence_id": "skill-jira-001"}], INV)
    assert v[0]["status"] == "ok" and v[0]["violation"] is None


# --------------------------------------------------------------- export ----
def test_export_returns_docx_or_markdown_fallback():
    data = G["_mock_export_docx"](["bullet one", "bullet two"])
    assert isinstance(data, (bytes, bytearray)) and len(data) > 20
    if data[:2] == b"PK":                      # python-docx present
        import zipfile
        assert zipfile.ZipFile(io.BytesIO(data)).namelist()  # valid zip/docx
    else:                                      # markdown fallback
        assert data.decode().startswith("# Tailored CV bullets")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
