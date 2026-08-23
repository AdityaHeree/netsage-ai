"""
NetSage AI - Case Repository Page
Filterable catalog of 32 Cisco lab scenarios across 8 networking domains with 1-click troubleshooter loading.
"""

import streamlit as st
import pandas as pd
from src.config import CATEGORIES, SEVERITY_LEVELS
from src.db import init_db, seed_db, get_all_cases

st.set_page_config(
    page_title="Case Repository — NetSage AI",
    page_icon="📚",
    layout="wide",
)

# Ensure DB is initialized
init_db()
seed_db()

st.title("📚 Cisco Lab Case Repository")
st.caption("Comprehensive catalog of 32 realistic Packet Tracer troubleshooting scenarios across 8 networking domains.")
st.divider()

# Filters Row
col_search, col_cat, col_sev = st.columns([2, 1, 1])

with col_search:
    search_query = st.text_input("🔍 Search scenarios (by title, symptom, concept):", placeholder="e.g. VLAN, OSPF, NAT, APIPA, ACL...")

with col_cat:
    category_filter = st.selectbox("Filter Domain:", options=["All Domains"] + CATEGORIES)

with col_sev:
    severity_filter = st.selectbox("Filter Severity:", options=["All Severities"] + SEVERITY_LEVELS)

# Query & Filter Data
all_cases = get_all_cases()

filtered_cases = []
for c in all_cases:
    # Category filter
    if category_filter != "All Domains" and c["category"] != category_filter:
        continue
    # Severity filter
    if severity_filter != "All Severities" and c["severity"] != severity_filter:
        continue
    # Search text
    if search_query.strip():
        q = search_query.lower()
        searchable_text = f"{c['id']} {c['title']} {c['category']} {c['symptom']} {c.get('concept_tag', '')} {c.get('actual_root_cause', '')}".lower()
        if q not in searchable_text:
            continue
    filtered_cases.append(c)

st.markdown(f"**Showing {len(filtered_cases)} of {len(all_cases)} Scenarios**")

if not filtered_cases:
    st.info("No cases match your filter criteria. Try adjusting the search filters.")
else:
    # Summary Table
    df = pd.DataFrame(filtered_cases)[["id", "title", "category", "severity", "osi_layer", "concept_tag"]]
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.TextColumn("Case ID", width="small"),
            "title": st.column_config.TextColumn("Scenario Title", width="large"),
            "category": st.column_config.TextColumn("Domain", width="small"),
            "severity": st.column_config.TextColumn("Severity", width="small"),
            "osi_layer": st.column_config.TextColumn("OSI Layer", width="medium"),
            "concept_tag": st.column_config.TextColumn("Concept Tag", width="medium"),
        },
    )

    st.divider()
    st.markdown("### 🔬 Scenario Inspector & 1-Click Demo Loader")

    for case in filtered_cases:
        severity_badge = {
            "Critical": "🔴 Critical",
            "High": "🟠 High",
            "Medium": "🟡 Medium",
            "Low": "🔵 Low",
        }.get(case["severity"], case["severity"])

        with st.expander(f"**[{case['id']}] {case['title']}** — *{case['category']}* ({severity_badge})"):
            c1, c2 = st.columns([3, 1])

            with c1:
                st.markdown(f"**📌 Concept Tag:** `{case.get('concept_tag', 'General')}` | **OSI Layer:** `{case.get('osi_layer', 'Layer 3')}`")
                st.markdown(f"**❗ Symptom:** {case['symptom']}")
                st.markdown(f"**🗺️ Topology Notes:** {case['topology_notes']}")
                st.markdown(f"**🎯 Ground Truth Root Cause:** `{case.get('actual_root_cause', 'N/A')}`")

                with st.expander("📄 View Raw Cisco CLI Evidence (Show Commands)"):
                    st.code(case["show_commands"], language="text")

            with c2:
                st.markdown("#### 🚀 Demo Action")
                if st.button("Load into Troubleshooter ➡️", key=f"load_{case['id']}", type="primary", use_container_width=True):
                    st.session_state["selected_case_id"] = case["id"]
                    st.switch_page("pages/1_🔍_Live_Troubleshooter.py")
