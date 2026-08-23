"""
NetSage AI - Responsible AI & Human-in-the-Loop Audit Log Page
Demonstrates AI error taxonomy, model drift tracking, and curated human calibration case studies.
"""

import streamlit as st
import pandas as pd
from src.config import FAILURE_CATEGORIES
from src.db import (
    init_db,
    seed_db,
    get_all_responsible_ai_logs,
    get_all_reviews,
)

st.set_page_config(
    page_title="Responsible AI Log — NetSage AI",
    page_icon="⚖️",
    layout="wide",
)

# Ensure DB is initialized
init_db()
seed_db()

st.title("⚖️ Responsible AI & HITL Correction Log")
st.caption("Documenting AI failure modes, model hallucinations, and human engineering corrections for accountable network operations.")
st.divider()

# Load Data from SQLite
rai_logs = get_all_responsible_ai_logs()
all_reviews = get_all_reviews()
human_corrections_live = [r for r in all_reviews if r["decision"] in ["EDITED", "REJECTED"]]

# KPI Metrics Row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Curated Calibration Logs", value=len(rai_logs), delta="RAI-01 to RAI-05")
with col2:
    st.metric(label="Live Human Corrections", value=len(human_corrections_live), delta="From user sessions")
with col3:
    hallucination_count = sum(1 for log in rai_logs if "Hallucination" in log["failure_category"])
    st.metric(label="Hallucination Errors", value=hallucination_count)
with col4:
    dangerous_count = sum(1 for log in rai_logs if "Dangerous" in log["failure_category"])
    st.metric(label="Dangerous Fix Flags", value=dangerous_count)
with col5:
    wrong_osi_count = sum(1 for log in rai_logs if "OSI Layer" in log["failure_category"])
    st.metric(label="OSI Layer Mismatches", value=wrong_osi_count)

st.divider()

# Section 1: Curated Seeded Calibration Case Studies
st.markdown("### 🎓 Curated Calibration Case Studies (Demonstration Dataset)")
st.info("ℹ️ These 5 curated demonstration records illustrate canonical AI failure modes in networking (e.g. hallucinating process ID requirements, proposing destructive reconfiguration, or mistaking Layer 3/4 NAT drops for Layer 7 DNS errors).")

for log in rai_logs:
    failure_badge_color = {
        "Hallucination": "🟣",
        "Dangerous Fix Command": "🔴",
        "Incomplete Evidence": "🟠",
        "Wrong OSI Layer": "🟡",
        "Overconfidence": "🔵",
    }.get(log["failure_category"], "⚪")

    with st.expander(f"{failure_badge_color} **[{log['id']}] {log['case_title']}** — *{log['category']}* ({log['failure_category']})", expanded=True):
        c_ai, c_human = st.columns(2)

        with c_ai:
            st.markdown("#### 🤖 AI Initial (Flawed) Diagnosis")
            st.error(f"**Root Cause:** {log['ai_root_cause']}")
            st.caption(f"Confidence Score at Inference: **{float(log['ai_confidence']) * 100:.1f}%**")

        with c_human:
            st.markdown("#### 👨‍💻 Human Engineer Correction")
            st.success(f"**True Ground Truth:** {log['human_correction']}")

        st.markdown(f"💡 **Key Guardrail & Lesson Learned:** `{log['lesson_learned']}`")

st.divider()

# Section 2: Live Human Corrections Audit
st.markdown("### 📝 Live Session Human Reviews & Audits")
if not all_reviews:
    st.info("No live human reviews submitted yet. Use the Live Troubleshooter to diagnose cases and submit reviews!")
else:
    review_rows = []
    for r in all_reviews:
        review_rows.append({
            "Review ID": r["id"],
            "Decision": "✅ ACCEPTED" if r["decision"] == "ACCEPTED" else ("✏️ EDITED" if r["decision"] == "EDITED" else "❌ REJECTED"),
            "Reviewer": r["reviewer_name"],
            "Case ID": r.get("case_id") or "Custom Session",
            "AI Root Cause": (r.get("ai_root_cause") or "N/A")[:60] + "...",
            "Human Notes": r.get("human_notes") or "",
            "Timestamp": r.get("reviewed_at", ""),
        })

    df_rev = pd.DataFrame(review_rows)
    st.dataframe(df_rev, use_container_width=True, hide_index=True)
