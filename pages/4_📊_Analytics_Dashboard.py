"""
NetSage AI - Analytics Dashboard Page
Visual performance analytics, AI-Human agreement rates, category distribution, and severity breakdowns from SQLite data.
"""

import streamlit as st
import pandas as pd
import altair as alt
from src.db import init_db, seed_db, get_analytics_summary

st.set_page_config(
    page_title="Analytics Dashboard — NetSage AI",
    page_icon="📊",
    layout="wide",
)

# Ensure DB is initialized
init_db()
seed_db()

st.title("📊 NetSage AI Operational Analytics")
st.caption("Real-time performance indicators, diagnostic distribution, and Human-in-the-Loop agreement metrics.")
st.divider()

# Load summary from SQLite
stats = get_analytics_summary()

# KPI Row
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    st.metric(label="Total Lab Cases", value=stats["total_cases"])
with kpi2:
    st.metric(label="Diagnoses Run", value=stats["total_diagnoses"])
with kpi3:
    st.metric(label="Reviews Completed", value=stats["total_reviews"])
with kpi4:
    st.metric(label="Pending Reviews", value=stats["pending_reviews"])
with kpi5:
    agr_val = f"{stats['agreement_rate']}%" if stats["total_reviews"] > 0 else "N/A"
    st.metric(label="AI Agreement Rate", value=agr_val)
with kpi6:
    conf_val = f"{stats['avg_confidence']}%" if stats["total_diagnoses"] > 0 else "N/A"
    st.metric(label="Avg AI Confidence", value=conf_val)

st.divider()

# Charts Grid (2x2)
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.markdown("### 📂 Cases by Networking Domain")
    if stats["category_counts"]:
        df_cat = pd.DataFrame(stats["category_counts"])
        chart_cat = (
            alt.Chart(df_cat)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#4F46E5")
            .encode(
                x=alt.X("category:N", title="Networking Domain", sort="-y"),
                y=alt.Y("count:Q", title="Number of Cases"),
                tooltip=["category", "count"]
            )
            .properties(height=280)
        )
        st.altair_chart(chart_cat, use_container_width=True)
    else:
        st.info("No case category data available.")

with row1_col2:
    st.markdown("### 🚦 Cases by Severity Level")
    if stats["severity_counts"]:
        df_sev = pd.DataFrame(stats["severity_counts"])
        chart_sev = (
            alt.Chart(df_sev)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#0EA5E9")
            .encode(
                x=alt.X("severity:N", title="Severity Classification", sort=["Critical", "High", "Medium", "Low"]),
                y=alt.Y("count:Q", title="Count"),
                tooltip=["severity", "count"]
            )
            .properties(height=280)
        )
        st.altair_chart(chart_sev, use_container_width=True)
    else:
        st.info("No severity distribution data available.")

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown("### ⚖️ Human Review Decisions Breakdown")
    if stats["decision_counts"]:
        df_dec = pd.DataFrame(stats["decision_counts"])
        chart_dec = (
            alt.Chart(df_dec)
            .mark_arc(innerRadius=50)
            .encode(
                theta=alt.Theta("count:Q"),
                color=alt.Color("decision:N", scale=alt.Scale(
                    domain=["ACCEPTED", "EDITED", "REJECTED"],
                    range=["#10B981", "#F59E0B", "#EF4444"]
                )),
                tooltip=["decision", "count"]
            )
            .properties(height=280)
        )
        st.altair_chart(chart_dec, use_container_width=True)
    else:
        st.info("No human reviews submitted yet. Submit reviews in the Live Troubleshooter to populate this chart.")

with row2_col2:
    st.markdown("### 🌐 Distribution by OSI Layer")
    if stats["osi_counts"]:
        df_osi = pd.DataFrame(stats["osi_counts"])
        chart_osi = (
            alt.Chart(df_osi)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#8B5CF6")
            .encode(
                x=alt.X("osi_layer:N", title="OSI Model Layer", sort="-y"),
                y=alt.Y("count:Q", title="Number of Scenarios"),
                tooltip=["osi_layer", "count"]
            )
            .properties(height=280)
        )
        st.altair_chart(chart_osi, use_container_width=True)
    else:
        st.info("No OSI layer distribution data available.")
