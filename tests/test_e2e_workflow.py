"""
NetSage AI - Phase 6 End-to-End Workflow Tests across All 8 Networking Domains
Tests the full lifecycle: Case DB -> Rule Engine -> AI Diagnosis (Mock) -> Human Review -> Analytics.
"""

import pytest
from src.config import CATEGORIES
from src.db import (
    init_db,
    seed_db,
    get_cases_by_category,
    insert_diagnosis,
    insert_review,
    get_analytics_summary,
)
from src.rules.engine import run_deterministic_checks
from src.ai.gemini_client import diagnose_case
from src.models import DiagnosisResponse


@pytest.fixture(autouse=True)
def setup_fresh_db():
    """Ensure database schema is ready and seeded."""
    init_db()
    seed_db()


@pytest.mark.parametrize("category", CATEGORIES)
def test_end_to_end_pipeline_per_category(category):
    """
    Verifies that for each of the 8 networking domains:
    1. At least 1 seeded case is fetched.
    2. Deterministic rule engine triggers relevant findings.
    3. AI diagnosis engine produces a valid, typed DiagnosisResponse.
    4. Diagnosis and Review records are persisted to SQLite.
    """
    cases = get_cases_by_category(category)
    assert len(cases) == 4, f"Expected 4 cases for {category}, found {len(cases)}"
    
    sample_case = cases[0]
    
    # 1. Deterministic Rule Checks
    findings = run_deterministic_checks(
        symptom=sample_case["symptom"],
        topology_notes=sample_case["topology_notes"],
        show_commands=sample_case["show_commands"],
    )
    assert len(findings) > 0, f"Expected deterministic rule findings for {sample_case['id']} ({category})"

    # 2. AI Diagnosis (Offline Mock Mode)
    result = diagnose_case(
        symptom=sample_case["symptom"],
        topology_notes=sample_case["topology_notes"],
        show_commands=sample_case["show_commands"],
        rule_findings=findings,
        mode="OFFLINE_MOCK",
    )
    assert result["mode_used"] == "OFFLINE_MOCK"
    diag = result["diagnosis"]
    assert isinstance(diag, DiagnosisResponse)
    assert 0.0 <= diag.confidence <= 1.0
    assert len(diag.evidence) > 0
    assert len(diag.fix_steps) > 0
    assert diag.root_cause

    # 3. Database Persistence (Diagnosis)
    diag_record = {
        "case_id": sample_case["id"],
        "symptom": sample_case["symptom"],
        "show_commands": sample_case["show_commands"],
        "rule_findings_json": [f.model_dump() for f in findings],
        "root_cause": diag.root_cause,
        "confidence": diag.confidence,
        "evidence_json": diag.evidence,
        "osi_layer": diag.osi_layer,
        "next_command": diag.next_command,
        "fix_steps_json": diag.fix_steps,
        "raw_ai_response": result["raw_response"],
        "mode": result["mode_used"],
    }
    diag_id = insert_diagnosis(diag_record)
    assert diag_id.startswith("DIAG-")

    # 4. Human Review Submission
    review_record = {
        "diagnosis_id": diag_id,
        "case_id": sample_case["id"],
        "decision": "ACCEPTED",
        "reviewer_name": "Test Engineer",
        "human_notes": f"Automated test validation for {category}",
        "agreement_score": 1,
    }
    rev_id = insert_review(review_record)
    assert rev_id.startswith("REV-")


def test_analytics_reflects_e2e_reviews():
    """Verify get_analytics_summary aggregates all persisted cases, diagnoses, and reviews."""
    summary = get_analytics_summary()
    assert summary["total_cases"] == 32
    assert summary["total_diagnoses"] >= 8
    assert summary["total_reviews"] >= 8
    assert summary["agreement_rate"] > 0.0
