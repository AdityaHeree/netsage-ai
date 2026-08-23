"""
NetSage AI — Applied AI + Network Troubleshooting Helper
Main landing page and architecture navigation.
"""

import streamlit as st
from src.config import (
    CATEGORIES,
    NETSAGE_MODE,
    is_gemini_configured,
)
from src.db import (
    init_db,
    seed_db,
    count_cases,
    count_diagnoses,
    count_reviews,
    count_responsible_ai_logs,
)

# Configure Streamlit Page
st.set_page_config(
    page_title="NetSage AI — Network Troubleshooting Assistant",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize & Seed Database
init_db()
seed_db()

total_cases = count_cases()
total_diagnoses = count_diagnoses()
total_reviews = count_reviews()
total_rai_logs = count_responsible_ai_logs()

# Sidebar
with st.sidebar:
    st.title("🌐 NetSage AI")
    st.caption("AI-Assisted Network Troubleshooting Helper")
    st.divider()

    runtime_mode = st.session_state.get("runtime_ai_mode", NETSAGE_MODE)
    mode_status = "🟢 OFFLINE MOCK" if runtime_mode == "OFFLINE_MOCK" else "🔵 GEMINI LIVE"
    st.markdown(f"**Engine Mode:** {mode_status}")

    gemini_status = "Configured ✅" if is_gemini_configured() else "Offline Mode 🟢"
    st.write(f"**Gemini API:** {gemini_status}")

    st.divider()
    st.markdown("### 📋 Implementation Phase")
    st.success("✅ **Phase 5 Complete**: Multipage UI & HITL Workflow Ready")
    st.markdown(
        """
        - [x] **Phase 1:** Project Scaffolding & Schemas
        - [x] **Phase 2:** Database & 32 Seed Cases + 5 RAI Logs
        - [x] **Phase 3:** 6 Deterministic Rule Modules
        - [x] **Phase 4:** Gemini Integration & Mock AI
        - [x] **Phase 5:** Full Multipage Streamlit UI
        - [ ] **Phase 6:** End-to-End Verification
        """
    )

# Main Hero Section
st.title("🌐 NetSage AI")
st.subheader("Applied AI + Network Troubleshooting Helper for Cisco Labs")
st.markdown(
    """
    **NetSage AI** is an intelligent troubleshooting companion designed for Cisco Packet Tracer and networking lab environments.
    It combines **6 deterministic rule-checking modules** with **structured Gemini AI diagnostics** under a mandatory
    **Human-in-the-Loop (HITL)** review process to deliver fast, accurate, and explainable network remediation.
    """
)

st.divider()

# System Metrics
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Target Domains", value=f"{len(CATEGORIES)} Categories", delta="VLAN, DHCP, NAT...")
with col2:
    st.metric(label="Pre-Seeded Cases", value=f"{total_cases} Scenarios", delta="4 per domain")
with col3:
    st.metric(label="Rule Check Modules", value="6 Modules", delta="Pre-AI validation")
with col4:
    st.metric(label="Diagnoses Logged", value=f"{total_diagnoses} Sessions")
with col5:
    st.metric(label="Human Reviews", value=f"{total_reviews} Recorded", delta="Accept / Edit / Reject")

st.divider()

# 5-Step Demo Workflow Visualizer
st.markdown("### 🔄 The NetSage AI Troubleshooting Lifecycle")

step1, step2, step3, step4, step5 = st.columns(5)

with step1:
    st.info("#### 1. Ingestion\nSubmit user symptom, topology scheme, and raw Cisco show-command evidence.")
with step2:
    st.info("#### 2. Rule Checks\nRun 6 deterministic modules to detect definite misconfigurations.")
with step3:
    st.info("#### 3. AI Diagnosis\nGenerate structured root cause, confidence, evidence citations, and fix steps.")
with step4:
    st.info("#### 4. HITL Review\nHuman engineer reviews and **Accepts**, **Edits**, or **Rejects** the diagnosis.")
with step5:
    st.info("#### 5. Verification\nApply surgical CLI fix in Packet Tracer and run simulated ping test.")

st.divider()

# Navigation Quick Links
st.markdown("### 🚀 Quick Navigation")
nav1, nav2, nav3, nav4 = st.columns(4)

with nav1:
    st.markdown("#### 🔍 Live Troubleshooter")
    st.write("Diagnose live cases with rule checks, AI root cause analysis, and human review.")
    if st.button("Open Troubleshooter ➡️", key="home_btn_troubleshoot", use_container_width=True):
        st.switch_page("pages/1_🔍_Live_Troubleshooter.py")

with nav2:
    st.markdown("#### 📚 Case Repository")
    st.write("Search and explore the catalog of 32 Cisco lab scenarios across 8 domains.")
    if st.button("Browse 32 Cases ➡️", key="home_btn_cases", use_container_width=True):
        st.switch_page("pages/2_📚_Case_Repository.py")

with nav3:
    st.markdown("#### ⚖️ Responsible AI Log")
    st.write("Review curated calibration case studies and audit live human corrections.")
    if st.button("View AI Logs ➡️", key="home_btn_rai", use_container_width=True):
        st.switch_page("pages/3_⚖️_Responsible_AI_Log.py")

with nav4:
    st.markdown("#### 📊 Analytics Dashboard")
    st.write("Inspect real-time agreement rates, category breakdowns, and performance KPIs.")
    if st.button("Open Dashboard ➡️", key="home_btn_dash", use_container_width=True):
        st.switch_page("pages/4_📊_Analytics_Dashboard.py")
