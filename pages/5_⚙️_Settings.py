"""
NetSage AI - Settings & System Configuration Page
Manage AI execution modes, test Gemini API connection, and maintain SQLite database state.
"""

import os
import streamlit as st
from pathlib import Path
from src.config import (
    DB_PATH,
    DEFAULT_GEMINI_MODEL,
    GEMINI_API_KEY,
    NETSAGE_MODE,
    is_gemini_configured,
)
from src.db import (
    init_db,
    seed_db,
    reset_db,
    count_cases,
    count_diagnoses,
    count_reviews,
    count_responsible_ai_logs,
)
from src.ai.gemini_client import create_gemini_client

st.set_page_config(
    page_title="Settings — NetSage AI",
    page_icon="⚙️",
    layout="wide",
)

# Ensure DB is initialized
init_db()
seed_db()

st.title("⚙️ System Settings & Environment")
st.caption("Configure runtime AI engine modes, test Gemini API connectivity, and manage database state.")
st.divider()

# Section 1: AI Engine Configuration
st.markdown("### 🧠 AI Engine Mode Configuration")

current_session_mode = st.session_state.get("runtime_ai_mode", NETSAGE_MODE)
selected_mode = st.radio(
    "Select Active Diagnostic Mode:",
    options=["OFFLINE_MOCK", "GEMINI_LIVE"],
    index=0 if current_session_mode == "OFFLINE_MOCK" else 1,
    help="OFFLINE_MOCK operates 100% locally without API keys. GEMINI_LIVE connects to Google Gemini via google-genai SDK."
)
st.session_state["runtime_ai_mode"] = selected_mode

if selected_mode == "OFFLINE_MOCK":
    st.success("🟢 **Offline Mock Mode Active**: The system will use the smart deterministic heuristic mock engine without requiring an internet connection or API keys.")
else:
    st.info("🔵 **Gemini Live Mode Active**: The system will send structured diagnosis prompts to the Gemini API.")

st.divider()

# Section 2: Gemini API Key & Connection Test
st.markdown("### 🔑 Google Gemini API Settings")

has_env_key = is_gemini_configured()
status_label = "✅ Configured in Environment (.env)" if has_env_key else "⚠️ Not Configured in Environment"
st.write(f"**Environment Key Status:** {status_label}")
st.write(f"**Default Model Target:** `{DEFAULT_GEMINI_MODEL}`")

custom_key = st.text_input(
    "Session Gemini API Key (Optional - stored in volatile session memory only):",
    type="password",
    placeholder="Enter API key for this session (e.g. AIzaSy...)",
    help="This key will NOT be written to disk, git, or SQLite database.",
)

if custom_key.strip():
    st.session_state["runtime_gemini_api_key"] = custom_key.strip()
    st.caption("🔒 Session API key registered in memory.")

if st.button("🧪 Test Gemini API Connection"):
    active_key = st.session_state.get("runtime_gemini_api_key") or GEMINI_API_KEY
    if not is_gemini_configured(active_key):
        st.error("❌ No API key available to test. Please add a key in .env or enter a session key above.")
    else:
        with st.spinner("Connecting to Google Gemini API via google-genai SDK..."):
            try:
                client = create_gemini_client(active_key)
                response = client.models.generate_content(
                    model=DEFAULT_GEMINI_MODEL,
                    contents="Ping. Respond with 'PONG' only.",
                )
                st.success(f"✅ **Gemini Connection Successful!** Response from {DEFAULT_GEMINI_MODEL}: `{response.text.strip()}`")
            except Exception as e:
                st.error(f"❌ **Gemini Connection Failed:** {e}")

st.divider()

# Section 3: Database Status & Maintenance
st.markdown("### 🗄️ SQLite Database Status & Maintenance")

col_d1, col_d2 = st.columns(2)

with col_d1:
    st.markdown("#### 📁 File Information")
    st.write(f"**Database Path:** `{DB_PATH}`")
    file_size_kb = DB_PATH.stat().st_size / 1024 if DB_PATH.exists() else 0
    st.write(f"**Database Size:** `{file_size_kb:.1f} KB`")

with col_d2:
    st.markdown("#### 📊 Table Record Counts")
    st.write(f"- **Troubleshooting Cases:** `{count_cases()}`")
    st.write(f"- **AI Diagnoses Stored:** `{count_diagnoses()}`")
    st.write(f"- **Human Reviews Stored:** `{count_reviews()}`")
    st.write(f"- **Responsible AI Logs:** `{count_responsible_ai_logs()}`")

st.markdown("---")
st.markdown("#### ⚠️ Reset & Reseed Database")
st.warning("Resetting the database will drop all user-created diagnoses and reviews, re-initializing the database with the pristine 32 cases and 5 Responsible AI calibration logs.")

confirm_reset = st.checkbox("I understand that resetting the database will erase live review history.")

if st.button("🔄 Reset & Reseed Database to Factory State", type="primary", disabled=not confirm_reset):
    with st.spinner("Resetting SQLite database tables and re-seeding..."):
        res = reset_db()
        st.success(f"✅ Database reset and reseeded successfully! ({res['cases_seeded']} cases, {res['rai_logs_seeded']} RAI records).")
        st.rerun()
