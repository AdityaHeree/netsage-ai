"""
NetSage AI - Live Troubleshooter Page
Interactive 4-step troubleshooting lab: Input Evidence -> Rule Checks -> AI Diagnosis -> Human Review & Fix
"""

import json
import streamlit as st
from src.config import (
    CATEGORIES,
    NETSAGE_MODE,
    is_gemini_configured,
)
from src.db import (
    init_db,
    seed_db,
    get_all_cases,
    get_case_by_id,
    insert_diagnosis,
    insert_review,
    insert_responsible_ai_log,
)
from src.rules.engine import run_deterministic_checks
from src.ai.gemini_client import diagnose_case

st.set_page_config(
    page_title="Live Troubleshooter — NetSage AI",
    page_icon="🔍",
    layout="wide",
)

# Ensure DB is initialized
init_db()
seed_db()

st.title("🔍 Live Troubleshooter & Demo Lab")
st.caption("AI-Assisted Network Diagnostic Assistant with Mandatory Human-in-the-Loop Review")
st.divider()

# Session State Initialization
if "troubleshooter_symptom" not in st.session_state:
    st.session_state["troubleshooter_symptom"] = ""
if "troubleshooter_topology" not in st.session_state:
    st.session_state["troubleshooter_topology"] = ""
if "troubleshooter_commands" not in st.session_state:
    st.session_state["troubleshooter_commands"] = ""
if "troubleshooter_case_id" not in st.session_state:
    st.session_state["troubleshooter_case_id"] = None
if "current_findings" not in st.session_state:
    st.session_state["current_findings"] = None
if "current_diagnosis" not in st.session_state:
    st.session_state["current_diagnosis"] = None
if "current_diagnosis_id" not in st.session_state:
    st.session_state["current_diagnosis_id"] = None
if "review_submitted" not in st.session_state:
    st.session_state["review_submitted"] = False
if "review_decision" not in st.session_state:
    st.session_state["review_decision"] = None
if "verification_simulated" not in st.session_state:
    st.session_state["verification_simulated"] = False

# Check if a case was loaded from the Case Repository page
if "selected_case_id" in st.session_state and st.session_state["selected_case_id"]:
    loaded_case = get_case_by_id(st.session_state["selected_case_id"])
    if loaded_case:
        st.session_state["troubleshooter_case_id"] = loaded_case["id"]
        st.session_state["troubleshooter_symptom"] = loaded_case["symptom"]
        st.session_state["troubleshooter_topology"] = loaded_case["topology_notes"]
        st.session_state["troubleshooter_commands"] = loaded_case["show_commands"]
        st.session_state["current_findings"] = None
        st.session_state["current_diagnosis"] = None
        st.session_state["current_diagnosis_id"] = None
        st.session_state["review_submitted"] = False
        st.session_state["review_decision"] = None
        st.session_state["verification_simulated"] = False
    st.session_state["selected_case_id"] = None

# Case Selector
all_cases = get_all_cases()
case_options = ["-- Custom Case / New Input --"] + [f"{c['id']}: {c['title']} ({c['category']})" for c in all_cases]

# Find current index
current_index = 0
if st.session_state["troubleshooter_case_id"]:
    for idx, opt in enumerate(case_options[1:], 1):
        if opt.startswith(st.session_state["troubleshooter_case_id"]):
            current_index = idx
            break

def on_case_change():
    selected = st.session_state["case_selector"]
    if selected.startswith("--"):
        st.session_state["troubleshooter_case_id"] = None
        st.session_state["troubleshooter_symptom"] = ""
        st.session_state["troubleshooter_topology"] = ""
        st.session_state["troubleshooter_commands"] = ""
    else:
        case_id = selected.split(":")[0].strip()
        case_data = get_case_by_id(case_id)
        if case_data:
            st.session_state["troubleshooter_case_id"] = case_data["id"]
            st.session_state["troubleshooter_symptom"] = case_data["symptom"]
            st.session_state["troubleshooter_topology"] = case_data["topology_notes"]
            st.session_state["troubleshooter_commands"] = case_data["show_commands"]
    st.session_state["current_findings"] = None
    st.session_state["current_diagnosis"] = None
    st.session_state["current_diagnosis_id"] = None
    st.session_state["review_submitted"] = False
    st.session_state["review_decision"] = None
    st.session_state["verification_simulated"] = False

col_select, col_mode = st.columns([3, 1])
with col_select:
    st.selectbox(
        "📁 Load a Lab Scenario or Enter Custom Data:",
        options=case_options,
        index=current_index,
        key="case_selector",
        on_change=on_case_change,
    )

with col_mode:
    runtime_mode = st.session_state.get("runtime_ai_mode", NETSAGE_MODE)
    mode_color = "🟢 OFFLINE MOCK" if runtime_mode == "OFFLINE_MOCK" else "🔵 GEMINI LIVE"
    st.info(f"**AI Engine:** {mode_color}")

# Input Section
st.markdown("### 📝 Step 1: Input Case Evidence")
col_sym, col_top = st.columns(2)

with col_sym:
    symptom_input = st.text_area(
        "User-Reported Symptom:",
        value=st.session_state["troubleshooter_symptom"],
        height=110,
        placeholder="e.g. PC-1 in Finance cannot ping Default Gateway 192.168.10.1 on Router R1.",
    )

with col_top:
    topology_input = st.text_area(
        "Topology Notes & IP Scheme:",
        value=st.session_state["troubleshooter_topology"],
        height=110,
        placeholder="e.g. PC-1 connects to Switch SW1 Fa0/1. Expected VLAN 10 (Finance). R1 G0/1 is gateway.",
    )

commands_input = st.text_area(
    "Cisco Show-Command Output Evidence:",
    value=st.session_state["troubleshooter_commands"],
    height=180,
    placeholder="Paste raw Cisco CLI show output here, e.g. show vlan brief, show ip interface brief, show ip route...",
)

# Keep session state updated
st.session_state["troubleshooter_symptom"] = symptom_input
st.session_state["troubleshooter_topology"] = topology_input
st.session_state["troubleshooter_commands"] = commands_input

# Buttons Row
col_btn1, col_btn2, col_btn_clear = st.columns([2, 2, 1])

with col_btn1:
    if st.button("⚙️ 1. Run Deterministic Rule Checks", use_container_width=True, type="secondary"):
        if not commands_input.strip() and not symptom_input.strip():
            st.warning("Please enter symptoms or Cisco show-command output before running rule checks.")
        else:
            findings = run_deterministic_checks(
                symptom=symptom_input,
                topology_notes=topology_input,
                show_commands=commands_input,
            )
            st.session_state["current_findings"] = findings
            st.rerun()

with col_btn2:
    if st.button("🧠 2. Run AI Diagnosis", use_container_width=True, type="primary"):
        if not commands_input.strip() and not symptom_input.strip():
            st.warning("Please enter symptoms or Cisco show-command output before running AI diagnosis.")
        else:
            with st.spinner("Analyzing evidence and generating structured diagnosis..."):
                findings = st.session_state["current_findings"] or run_deterministic_checks(
                    symptom=symptom_input,
                    topology_notes=topology_input,
                    show_commands=commands_input,
                )
                st.session_state["current_findings"] = findings

                target_mode = st.session_state.get("runtime_ai_mode", NETSAGE_MODE)
                target_key = st.session_state.get("runtime_gemini_api_key", None)

                ai_result = diagnose_case(
                    symptom=symptom_input,
                    topology_notes=topology_input,
                    show_commands=commands_input,
                    rule_findings=findings,
                    mode=target_mode,
                    api_key=target_key,
                )

                diag = ai_result["diagnosis"]
                st.session_state["current_diagnosis"] = ai_result

                # Save diagnosis to SQLite
                diag_record = {
                    "case_id": st.session_state["troubleshooter_case_id"],
                    "symptom": symptom_input,
                    "show_commands": commands_input,
                    "rule_findings_json": [f.model_dump() for f in findings],
                    "root_cause": diag.root_cause,
                    "confidence": diag.confidence,
                    "evidence_json": diag.evidence,
                    "osi_layer": diag.osi_layer,
                    "next_command": diag.next_command,
                    "fix_steps_json": diag.fix_steps,
                    "raw_ai_response": ai_result["raw_response"],
                    "mode": ai_result["mode_used"],
                }
                diag_id = insert_diagnosis(diag_record)
                st.session_state["current_diagnosis_id"] = diag_id
                st.session_state["review_submitted"] = False
                st.session_state["review_decision"] = None
                st.session_state["verification_simulated"] = False
                st.rerun()

with col_btn_clear:
    if st.button("🔄 Reset Lab", use_container_width=True):
        st.session_state["current_findings"] = None
        st.session_state["current_diagnosis"] = None
        st.session_state["current_diagnosis_id"] = None
        st.session_state["review_submitted"] = False
        st.session_state["review_decision"] = None
        st.session_state["verification_simulated"] = False
        st.rerun()

st.divider()

# Step 2: Deterministic Rule Checks Output
if st.session_state["current_findings"] is not None:
    st.markdown("### ⚙️ Deterministic Rule Engine Findings")
    findings = st.session_state["current_findings"]

    if not findings:
        st.success("✅ No baseline deterministic configuration anomalies detected in the provided evidence.")
    else:
        for idx, f in enumerate(findings, 1):
            severity_colors = {
                "Critical": "🔴",
                "High": "🟠",
                "Medium": "🟡",
                "Low": "🔵",
            }
            icon = severity_colors.get(f.severity, "⚪")
            with st.expander(f"{icon} **[{f.severity}] {f.rule_name}** ({f.category}) — {f.message}", expanded=True):
                st.write(f"**Explanation:** {f.message}")
                if f.matched_evidence:
                    st.write("**Matched Evidence:**")
                    for ev in f.matched_evidence:
                        st.code(ev, language="text")
                if f.recommendation:
                    st.info(f"💡 **Suggested Action:** `{f.recommendation}`")

# Step 3: Structured AI Diagnosis Output
if st.session_state["current_diagnosis"] is not None:
    st.divider()
    st.markdown("### 🧠 AI Structured Diagnosis")
    diag_result = st.session_state["current_diagnosis"]
    diag = diag_result["diagnosis"]
    mode_used = diag_result["mode_used"]

    if diag_result.get("error"):
        st.warning(diag_result["error"])

    # Metrics Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="Diagnostic Confidence", value=f"{diag.confidence * 100:.1f}%")
    with m_col2:
        st.metric(label="Affected OSI Layer", value=diag.osi_layer)
    with m_col3:
        st.metric(label="Risk Assessment", value=diag.risk_assessment)
    with m_col4:
        st.metric(label="Diagnosis Source", value=mode_used)

    # Detailed Root Cause Card
    st.info(f"🎯 **Root Cause:** {diag.root_cause}")

    col_diag_left, col_diag_right = st.columns(2)

    with col_diag_left:
        st.markdown("#### 🔍 Evidence Citations")
        for ev in diag.evidence:
            st.markdown(f"- {ev}")

        st.markdown("#### 📖 Technical Explanation")
        st.write(diag.explanation)

    with col_diag_right:
        st.markdown("#### 🛠️ Recommended Cisco CLI Remediation")
        st.code("\n".join(diag.fix_steps), language="cisco")

        st.markdown("#### 🔎 Recommended Verification Command")
        st.code(diag.next_command, language="cisco")

    # Step 4: Human-in-the-Loop Review
    st.divider()
    st.markdown("### ⚖️ Mandatory Human-in-the-Loop Review")
    st.caption("AI diagnoses are advisory only and must be inspected and approved by a human engineer before taking remediation actions.")

    if st.session_state["review_submitted"]:
        dec = st.session_state["review_decision"]
        if dec == "ACCEPTED":
            st.success(f"✅ **Decision Stored**: AI Diagnosis has been **ACCEPTED** by reviewer and logged in the database.")
        elif dec == "EDITED":
            st.info(f"✏️ **Decision Stored**: AI Diagnosis has been **EDITED** with human corrections and logged.")
        elif dec == "REJECTED":
            st.error(f"❌ **Decision Stored**: AI Diagnosis has been **REJECTED** and captured in the Responsible AI audit log.")
    else:
        tab_accept, tab_edit, tab_reject = st.tabs(["✅ Accept Diagnosis", "✏️ Edit & Correct", "❌ Reject Diagnosis"])

        with tab_accept:
            st.markdown("Confirm that the AI's root cause, evidence citations, and CLI fix commands are accurate.")
            reviewer_name = st.text_input("Reviewer Name/ID:", value="Network Engineer", key="accept_reviewer")
            accept_notes = st.text_input("Reviewer Comments (Optional):", value="Diagnosis and fix steps verified against topology.", key="accept_notes")

            if st.button("Confirm & Accept Diagnosis", type="primary", key="btn_accept"):
                review_record = {
                    "diagnosis_id": st.session_state["current_diagnosis_id"],
                    "case_id": st.session_state["troubleshooter_case_id"],
                    "decision": "ACCEPTED",
                    "reviewer_name": reviewer_name,
                    "human_notes": accept_notes,
                    "agreement_score": 1,
                }
                insert_review(review_record)
                st.session_state["review_submitted"] = True
                st.session_state["review_decision"] = "ACCEPTED"
                st.rerun()

        with tab_edit:
            st.markdown("Modify the root cause or CLI fix steps if the AI was partially inaccurate.")
            edit_reviewer = st.text_input("Reviewer Name/ID:", value="Senior Network Engineer", key="edit_reviewer")
            edited_root_cause = st.text_area("Corrected Root Cause:", value=diag.root_cause, key="edit_rc")
            edited_fix_steps = st.text_area("Corrected Fix Steps (One command per line):", value="\n".join(diag.fix_steps), key="edit_fix")
            edit_notes = st.text_input("Reason for Modification:", value="Adjusted specific interface command.", key="edit_notes")

            if st.button("Save Corrected Diagnosis", key="btn_edit"):
                fix_list = [line.strip() for line in edited_fix_steps.splitlines() if line.strip()]
                review_record = {
                    "diagnosis_id": st.session_state["current_diagnosis_id"],
                    "case_id": st.session_state["troubleshooter_case_id"],
                    "decision": "EDITED",
                    "reviewer_name": edit_reviewer,
                    "human_notes": edit_notes,
                    "corrected_root_cause": edited_root_cause,
                    "corrected_fix_steps": fix_list,
                    "agreement_score": 0,
                }
                insert_review(review_record)
                st.session_state["review_submitted"] = True
                st.session_state["review_decision"] = "EDITED"
                st.rerun()

        with tab_reject:
            st.markdown("Reject the diagnosis if the AI hallucinated, provided dangerous commands, or misidentified the failure.")
            reject_reviewer = st.text_input("Reviewer Name/ID:", value="Network Auditor", key="reject_reviewer")
            failure_type = st.selectbox(
                "Failure Mode Classification:",
                options=["Hallucination", "Dangerous Fix Command", "Incomplete Evidence", "Wrong OSI Layer", "Overconfidence"],
                key="reject_failure_type"
            )
            reject_correction = st.text_area("Human Corrected Ground Truth (Required):", key="reject_correction", placeholder="Explain the true problem and the exact fix.")
            reject_lesson = st.text_input("Lesson Learned / Guardrail Rule:", key="reject_lesson", placeholder="e.g. Ensure OSPF timers are checked before assuming process ID mismatch.")
            reject_notes = st.text_input("Rejection Notes:", key="reject_notes", placeholder="e.g. AI recommended destructive config replacement.")

            if st.button("Submit Rejection & Log to Responsible AI", key="btn_reject"):
                if not reject_correction.strip():
                    st.warning("Please provide the human correction before rejecting.")
                else:
                    review_record = {
                        "diagnosis_id": st.session_state["current_diagnosis_id"],
                        "case_id": st.session_state["troubleshooter_case_id"],
                        "decision": "REJECTED",
                        "reviewer_name": reject_reviewer,
                        "human_notes": reject_notes,
                        "corrected_root_cause": reject_correction,
                        "agreement_score": 0,
                    }
                    insert_review(review_record)

                    # Also log to Responsible AI table
                    rai_record = {
                        "case_title": st.session_state["troubleshooter_case_id"] or "Custom Troubleshooter Session",
                        "category": diag.osi_layer,
                        "ai_root_cause": diag.root_cause,
                        "ai_confidence": diag.confidence,
                        "human_correction": reject_correction,
                        "failure_category": failure_type,
                        "lesson_learned": reject_lesson or "Always verify against Packet Tracer topology.",
                    }
                    insert_responsible_ai_log(rai_record)

                    st.session_state["review_submitted"] = True
                    st.session_state["review_decision"] = "REJECTED"
                    st.rerun()

    # Step 5: Fix & Simulated Verification
    st.divider()
    st.markdown("### 🧪 Step 5: Fix Application & Verification Simulator")
    st.info("⚠️ **Note:** Cisco configuration commands must be applied by you inside **Cisco Packet Tracer**. NetSage AI runs purely locally and does not execute commands on your host machine or network.")

    if st.button("📡 Simulate Packet Tracer Verification Test", key="btn_verify"):
        st.session_state["verification_simulated"] = True

    if st.session_state["verification_simulated"]:
        st.markdown("#### 📟 Simulated Packet Tracer Terminal Output:")
        st.code(
            f"""
PC-1> ping target_host
Pinging destination with 32 bytes of data:
Reply from target_host: bytes=32 time=2ms TTL=128
Reply from target_host: bytes=32 time=1ms TTL=128
Reply from target_host: bytes=32 time=1ms TTL=128
Reply from target_host: bytes=32 time=1ms TTL=128

Ping statistics for destination:
    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 1ms, Maximum = 2ms, Average = 1ms

[Packet Tracer Simulation: Connectivity verified successfully following fix application.]
            """,
            language="text"
        )
        st.success("✅ **Simulated Verification Complete**: Packet delivery confirmed in lab simulation.")
