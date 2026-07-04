"""
CV Tailoring Agent v2 — Streamlit front end
============================================
Thin UI only — all logic (inventory storage, CV extraction, keyword
matching, rewriting, the anti-fabrication guard, export) lives in the FastAPI
backend (backend/) and is reached exclusively through client.py over HTTP.
This file has zero `core.*` imports.

RUN IT (two processes):
    Terminal 1: uvicorn backend.main:app --reload --port 8000
    Terminal 2: streamlit run app.py
(or use scripts/run_backend.ps1 and scripts/run_frontend.ps1)

GUARDRAILS BAKED INTO THIS UI (do not remove):
    - Export stays disabled until every changed bullet is accepted/rejected.
    - Blocked bullets are displayed, never hidden.
    - Gap keywords are reported, never auto-filled.
    - Real data lives in data/inventory.yaml (gitignored), owned by the backend.
"""

from __future__ import annotations

import html

import streamlit as st

import client

# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------
st.set_page_config(page_title="CV Tailoring Agent", page_icon="🛡️", layout="wide")
TEAL, RED = "#0E7C7B", "#B4423A"

# ---- Visual polish layer (design tokens). Structural redesign = Phase 2, see UI_REDESIGN_SPEC.md ----
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap');
html { font-size:120%; }
html, body, [data-testid="stAppViewContainer"] { font-family:'Source Sans 3',system-ui,sans-serif; }
[data-testid="stAppViewContainer"] { background:#F7F9FB; color:#1F2933; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { background:#1F2933; }
[data-testid="stSidebar"] * { color:#E6EAEE !important; font-family:'Source Sans 3',system-ui,sans-serif; }
/* Streamlit's icon glyphs (sidebar collapse arrow, uploader icon) are ligature text in a
   dedicated icon font — the blanket font-family rule above broke them into literal words. */
[data-testid="stIconMaterial"], .material-icons, .material-symbols-rounded {
  font-family: 'Material Symbols Rounded', 'Material Icons' !important;
}
h1,h2,h3 { font-family:'Source Sans 3',system-ui,sans-serif; font-weight:700; color:#1F2933 !important; letter-spacing:-.01em; }
p, span, label, div { color:#1F2933; }
[data-testid="stMetric"] { background:#FFFFFF; border:1px solid #E3E8EE; border-radius:10px;
  padding:14px 16px; box-shadow:0 1px 3px rgba(16,42,67,.06); }
[data-testid="stMetricValue"] { color:#0E7C7B !important; font-weight:700; }
[data-testid="stMetricLabel"] { color:#5B6472 !important; }

/* Buttons — explicit palette, both states, so text is never dark-on-dark */
.stButton>button, .stDownloadButton>button {
  background:#0E7C7B !important; color:#FFFFFF !important;
  border:1px solid #0E7C7B !important; border-radius:8px !important; font-weight:600 !important;
}
.stButton>button:hover, .stDownloadButton>button:hover {
  background:#0A5C5B !important; color:#FFFFFF !important; border-color:#0A5C5B !important;
}
.stButton>button:disabled, .stDownloadButton>button:disabled {
  background:#E9EBF0 !important; color:#9AA0AC !important; border-color:#E9EBF0 !important;
}
/* Secondary / plain buttons (e.g. checkbox-adjacent, radio) keep readable text on light bg */
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label { color:#1F2933 !important; }

/* Sidebar logo — plain icon button, overrides the teal button fill above (declared later = wins) */
.st-key-logo_home button {
  background:transparent !important; border:none !important;
  padding:8px 0 4px 0 !important; box-shadow:none !important;
}
.st-key-logo_home button p { font-size:4.5rem !important; line-height:1 !important; color:#E6EAEE !important; }
.st-key-logo_home button:hover p { color:#2DBDBA !important; }
.st-key-logo_home { margin-bottom:-4px; }

/* File uploader (content area) — subtle card dropzone, teal Browse button */
[data-testid="stFileUploaderDropzone"] {
  background:#FFFFFF !important; border:1px dashed #9AD5D4 !important; border-radius:8px !important;
}
[data-testid="stFileUploaderDropzone"] button {
  background:#0E7C7B !important; color:#FFFFFF !important;
  border:1px solid #0E7C7B !important; border-radius:8px !important; font-weight:600 !important;
  width:auto !important; height:auto !important; min-width:fit-content !important;
  white-space:nowrap !important; padding:6px 16px !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
  background:#0A5C5B !important; border-color:#0A5C5B !important;
}

textarea, input[type="text"] { border-radius:8px !important; color:#1F2933 !important; background:#FFFFFF !important; }

.cva-chip{display:inline-block;background:#E3F2F1;color:#0A5C5B;border:1px solid #9AD5D4;
  border-radius:14px;padding:2px 12px;margin:0 6px 6px 0;font-size:.85rem;font-weight:600}
.cva-chip-miss{background:#F9ECEB;color:#B4423A;border-color:#E5B7B2}
.cva-card{background:#fff;border:1px solid #E3E8EE;border-left:4px solid #0E7C7B;border-radius:10px;
  padding:12px 16px;margin-bottom:6px;box-shadow:0 1px 3px rgba(16,42,67,.06);color:#1F2933}
.cva-card-blocked{border-left-color:#B4423A;background:#FBF3F2}
.cva-ev{font-family:Consolas,monospace;font-size:.72rem;color:#0A5C5B;background:#E3F2F1;
  border-radius:4px;padding:1px 8px;letter-spacing:.03em}
.cva-ev-err{color:#B4423A;background:#F9ECEB}
.cva-gapbox{background:#FBF3F2;border:1px solid #E5B7B2;border-radius:10px;padding:12px 16px;margin:8px 0;color:#1F2933}

/* Content-area import callout */
.cva-import-cta{background:#E3F2F1;border:1px solid #9AD5D4;border-radius:8px;
  padding:10px 12px;margin:10px 0;font-size:.85rem;line-height:1.4;color:#0A5C5B}
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)

if not client.is_backend_up():
    st.error(
        "**Backend offline** — start it with `uvicorn backend.main:app --reload` "
        "(or run `scripts/run_backend.ps1`), then reload this page."
    )
    st.stop()

ss = st.session_state
ss.setdefault("inventory", client.get_inventory())
ss.setdefault("run", None)          # {"keywords","hits","gaps","score"}
ss.setdefault("run_id", 0)          # nonce: isolates widget keys per run (stale-state fix)
ss.setdefault("ticked", set())      # entry ids selected for rewrite
ss.setdefault("bullets", [])        # validated bullets
ss.setdefault("decisions", {})      # bullet index -> "accepted"|"rejected"

if "_nav_next" in ss:  # deferred nav: must land before the radio widget below is instantiated
    ss["nav_radio"] = ss.pop("_nav_next")

with st.sidebar:
    if st.button("🛡️", key="logo_home", help="Home", type="tertiary"):
        st.session_state["nav_radio"] = "📇 Inventory"
        st.rerun()
    st.markdown("### CV Tailoring Agent")
    st.caption(f"local · evidence-only · v2 · {len(ss.inventory.get('entries', []))} entries")
    screen = st.radio("Navigate", ["📇 Inventory", "🎯 Tailor", "✅ Review & Export"],
                       key="nav_radio", label_visibility="collapsed")

try:
    errors = client.validate_inventory(ss.inventory)
except client.BackendError as e:
    st.error(f"Couldn't validate inventory: {e}")
    errors = []


def _render_import_preview(cv_text: str, source_label: str, base_id: str, widget_prefix: str) -> None:
    st.markdown(
        f"<div class='cva-import-cta'>📄 Extracted {len(cv_text):,} characters from "
        f"<b>{html.escape(source_label)}</b> — add tags below, then add it as an entry.</div>",
        unsafe_allow_html=True,
    )
    tags_input = st.text_input(
        "Tags (comma-separated, required)", key=f"{widget_prefix}_add_tags",
        placeholder="e.g. scrum-master, agile",
    )
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    if st.button("➕ Add as inventory entry", key=f"{widget_prefix}_add_entry",
                 use_container_width=True, disabled=not tags):
        existing_ids = {e["id"] for e in ss.inventory.get("entries", [])}
        uid, n = base_id, 1
        while uid in existing_ids:
            n += 1
            uid = f"{base_id}-{n}"
        first_line = next((l.strip() for l in cv_text.splitlines() if l.strip()), source_label)
        ss.inventory.setdefault("entries", []).append({
            "id": uid,
            "claim": first_line[:120],
            "evidence": cv_text.strip()[:5000],
            "tags": tags,
        })
        st.success(f"Added '{uid}' — refine claim/tags below, then Save.")
    with st.expander("Preview extracted text"):
        st.text(cv_text[:3000] + ("…" if len(cv_text) > 3000 else ""))


# ---------------------------------------------------------------------------
# S1 — INVENTORY
# ---------------------------------------------------------------------------
if screen == "📇 Inventory":
    st.subheader("Evidence inventory")
    st.caption("Everything a tailored CV is allowed to say lives here. No entry — no claim.")

    entries = ss.inventory.get("entries", [])
    if errors:
        st.error("SCHEMA INVALID — Tailor is disabled:\n\n- " + "\n- ".join(errors))
    elif entries:
        st.success("SCHEMA VALID ✓")

    st.markdown("**Import CV**")
    uploaded = st.file_uploader(
        "Upload .docx / .pdf / .pptx", type=["docx", "pdf", "pptx"], key="cv_upload"
    )
    if uploaded is not None:
        try:
            result = client.upload_cv(uploaded.name, uploaded.getvalue())
        except client.BackendError as e:
            st.error(str(e))
        else:
            cv_text = result["text"]
            if cv_text.strip():
                base_id = f"upload-{uploaded.name.rsplit('.', 1)[0].lower().replace(' ', '-')}"
                _render_import_preview(cv_text, uploaded.name, base_id, "cv")

    st.divider()

    ss.setdefault("show_manual_entry", False)
    if not entries and not ss.show_manual_entry:
        st.info("No entries yet — import a CV above, or add one manually below.")
        if st.button("➕ Add a blank entry"):
            ss.show_manual_entry = True
            st.rerun()
    else:
        scaffold = entries or [{"id": "", "claim": "", "evidence": "", "tags": []}]
        rows = [
            {"id": e["id"], "claim": e["claim"], "evidence": e["evidence"], "tags": ", ".join(e["tags"])}
            for e in scaffold
        ]
        edited = st.data_editor(rows, num_rows="dynamic", use_container_width=True, key="inv_editor")
        if any(r.get("id") for r in edited) and st.button("💾 Save your skills to compare against JD"):
            new_inv = {
                "entries": [
                    {"id": r["id"], "claim": r["claim"], "evidence": r["evidence"],
                     "tags": [t.strip() for t in str(r["tags"]).split(",") if t.strip()]}
                    for r in edited if r.get("id")
                ]
            }
            try:
                saved = client.save_inventory(new_inv)
            except client.BackendError as e:
                st.error(f"Not saved:\n\n{e}")
            else:
                ss.inventory = saved
                ss.show_manual_entry = False
                ss.run, ss.bullets, ss.decisions, ss.ticked = None, [], {}, set()  # invalidate stale run
                st.success("Saved. Previous tailor run cleared.")

# ---------------------------------------------------------------------------
# S2 — TAILOR
# ---------------------------------------------------------------------------
elif screen == "🎯 Tailor":
    st.subheader("Tailor to a job description")
    if errors:
        st.error("Fix the inventory schema first (see Inventory screen).")
        st.stop()
    st.caption("The JD is untrusted input — treated as data, never as instructions.")
    jd = st.text_area("Paste job description", height=170, placeholder="Senior Scrum Master — ServiceNow & Terraform…")

    if st.button("Run tailor →", type="primary", disabled=not jd.strip()):
        try:
            with st.spinner("Extracting keywords…"):
                r = client.run_tailor(jd)
        except client.BackendError as e:
            st.error(f"Couldn't run tailor: {e}")
        else:
            ss.run = r
            ss.run_id += 1
            ss.ticked = set(r["hits"].keys())
            ss.bullets, ss.decisions = [], {}

    if ss.run:
        r = ss.run
        c1, c2, c3 = st.columns(3)
        c1.metric("Fit score (deterministic)", f"{r['score']}/100")
        c2.metric("Matched keywords", sum(len(v) for v in r["hits"].values()))
        c3.metric("Gaps — never filled", len(r["gaps"]))

        seen_terms: set[str] = set()
        chip_html = ""
        for kws_list in r["hits"].values():
            for k in kws_list:
                if k["term"] not in seen_terms:
                    seen_terms.add(k["term"])
                    chip_html += f"<span class='cva-chip'>{html.escape(k['term'])}</span>"
        if chip_html:
            st.markdown(chip_html, unsafe_allow_html=True)

        st.markdown("**Matched evidence** — untick to exclude, tick to force-include (your override):")
        by_id = {e["id"]: e for e in ss.inventory["entries"]}
        for e in ss.inventory["entries"]:
            kws = ", ".join(k["term"] for k in r["hits"].get(e["id"], []))
            label = f"`{e['id']}` — {e['claim'][:90]}" + (f"  ·  _{kws}_" if kws else "  ·  _no keyword match — tick only if truly relevant_")
            on = st.checkbox(label, value=e["id"] in ss.ticked, key=f"tick_{ss.run_id}_{e['id']}")
            if on:
                ss.ticked.add(e["id"])
            else:
                ss.ticked.discard(e["id"])

        if r["gaps"]:
            gap_chips = "".join(
                f"<span class='cva-chip cva-chip-miss'>{html.escape(g['term'])} · {g['priority']}</span>"
                for g in r["gaps"]
            )
            st.markdown(
                f"<div class='cva-gapbox'><b style='color:{RED}'>Gap report — no evidence for:</b><br>{gap_chips}"
                f"<div style='color:{RED};font-size:.85rem;font-style:italic'>The agent will not fabricate these — "
                "add evidence, reframe honestly, or accept the gap.</div></div>",
                unsafe_allow_html=True,
            )

        if st.button("Rewrite selected evidence →", disabled=not ss.ticked):
            try:
                with st.spinner("Rewriting bullets…"):
                    ss.bullets = client.rewrite_bullets(list(ss.ticked), r["keywords"])
            except client.BackendError as e:
                st.error(f"Couldn't rewrite: {e}")
            else:
                ss.decisions = {}
                ss["_nav_next"] = "✅ Review & Export"
                st.rerun()

# ---------------------------------------------------------------------------
# S3 — REVIEW & EXPORT
# ---------------------------------------------------------------------------
else:
    st.subheader("Review every change")
    if not ss.bullets:
        st.info("No run yet — go to Tailor first.")
        st.stop()

    pending = 0
    for i, b in enumerate(ss.bullets):
        left, right = st.columns([1, 1])
        txt, vio, eid = html.escape(b["text"]), html.escape(b.get("violation") or ""), html.escape(b["evidence_id"])
        if b["status"] == "blocked":
            right.markdown(
                f"<div class='cva-card cva-card-blocked'>"
                f"<span class='cva-ev cva-ev-err'>BLOCKED BY VALIDATE.PY</span><br>"
                f"<s style='color:#808495'>{txt}</s><br>"
                f"<span style='color:{RED};font-size:.85rem'>{vio} — original kept, violation logged</span></div>",
                unsafe_allow_html=True,
            )
            left.caption("guard rejection — no action needed")
            continue
        right.markdown(
            f"<div class='cva-card'>"
            f"<span class='cva-ev'>evidence: {eid}</span><br>{txt}</div>",
            unsafe_allow_html=True,
        )
        choice = left.radio("Decision", ["pending", "accept", "reject"], key=f"dec_{ss.run_id}_{i}", horizontal=True)
        ss.decisions[i] = choice
        pending += choice == "pending"

    st.divider()
    accepted = [b["text"] for i, b in enumerate(ss.bullets) if ss.decisions.get(i) == "accept"]
    if pending:
        st.button(f"⬇ Export DOCX — locked ({pending} pending)", disabled=True)
        st.caption("Guardrail #2: nothing exports until every bullet has your explicit decision.")
    else:
        try:
            data = client.export_docx(accepted)
        except client.BackendError as e:
            st.error(f"Couldn't export: {e}")
        else:
            is_docx = data[:2] == b"PK"
            st.download_button(
                "⬇ Export tailored bullets",
                data=data,
                file_name="tailored_cv." + ("docx" if is_docx else "md"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document" if is_docx else "text/markdown",
            )
            st.caption(f"{len(accepted)} accepted bullets.")
