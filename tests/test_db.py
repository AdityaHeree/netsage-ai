"""
NetSage AI - Phase 2 Database & Seed Dataset Tests
Verifies SQLite schema creation, CRUD operations, seed data integrity, and idempotency.
"""

import sqlite3
import pytest
from src.config import CATEGORIES
from src.db import (
    init_db,
    seed_db,
    get_db_connection,
    insert_case,
    get_all_cases,
    get_case_by_id,
    get_cases_by_category,
    count_cases,
    insert_diagnosis,
    get_diagnosis_by_id,
    get_recent_diagnoses,
    insert_review,
    get_all_reviews,
    get_reviews_by_case,
    insert_responsible_ai_log,
    get_all_responsible_ai_logs,
    count_responsible_ai_logs,
)


@pytest.fixture
def temp_db(tmp_path):
    """Provides a fresh temporary SQLite database path for isolated testing."""
    db_file = tmp_path / "test_netsage.db"
    init_db(db_file)
    return db_file


def test_db_initialization_and_tables(temp_db):
    """Verify all 4 required tables exist upon database initialization."""
    with get_db_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row["name"] for row in cursor.fetchall()]

    assert "cases" in tables
    assert "diagnoses" in tables
    assert "reviews" in tables
    assert "responsible_ai_logs" in tables


def test_insert_and_get_case(temp_db):
    """Verify inserting and querying custom cases."""
    case_data = {
        "id": "CASE-TEST-01",
        "title": "Test Port Security Error",
        "category": "VLAN",
        "severity": "High",
        "symptom": "Port err-disabled after unauthorized laptop connection",
        "topology_notes": "SW1 Fa0/1 connected to user desk",
        "show_commands": "SW1# show interfaces status err-disabled",
        "actual_root_cause": "Port security violation shutdown port",
        "osi_layer": "Layer 2 - Data Link",
        "concept_tag": "Port Security",
    }
    inserted_id = insert_case(case_data, db_path=temp_db)
    assert inserted_id == "CASE-TEST-01"

    retrieved = get_case_by_id("CASE-TEST-01", db_path=temp_db)
    assert retrieved is not None
    assert retrieved["title"] == "Test Port Security Error"
    assert retrieved["category"] == "VLAN"
    assert retrieved["concept_tag"] == "Port Security"

    vlan_cases = get_cases_by_category("VLAN", db_path=temp_db)
    assert len(vlan_cases) == 1
    assert vlan_cases[0]["id"] == "CASE-TEST-01"


def test_insert_and_get_diagnosis(temp_db):
    """Verify inserting and retrieving AI diagnosis records with parsed JSON structures."""
    diag_data = {
        "id": "DIAG-TEST-01",
        "case_id": None,
        "symptom": "Ping fails to gateway",
        "show_commands": "SW1# show ip int brief",
        "rule_findings_json": [{"rule": "SHUTDOWN_INT", "severity": "High"}],
        "root_cause": "Interface GigabitEthernet0/1 is administratively down.",
        "confidence": 0.96,
        "evidence_json": ["GigabitEthernet0/1 is administratively down, line protocol is down"],
        "osi_layer": "Layer 1 - Physical",
        "next_command": "show ip interface brief",
        "fix_steps_json": ["interface GigabitEthernet0/1", "no shutdown"],
        "mode": "OFFLINE_MOCK",
    }
    inserted_id = insert_diagnosis(diag_data, db_path=temp_db)
    assert inserted_id == "DIAG-TEST-01"

    retrieved = get_diagnosis_by_id("DIAG-TEST-01", db_path=temp_db)
    assert retrieved is not None
    assert retrieved["root_cause"] == "Interface GigabitEthernet0/1 is administratively down."
    assert retrieved["confidence"] == 0.96
    assert isinstance(retrieved["fix_steps"], list)
    assert "no shutdown" in retrieved["fix_steps"]
    assert isinstance(retrieved["rule_findings"], list)

    recents = get_recent_diagnoses(limit=10, db_path=temp_db)
    assert len(recents) == 1


def test_insert_and_get_review(temp_db):
    """Verify inserting and retrieving human reviews and agreement scoring."""
    # First create diagnosis to reference
    diag_data = {
        "id": "DIAG-REV-01",
        "symptom": "Test symptom",
        "show_commands": "Test commands",
        "root_cause": "Test AI cause",
        "confidence": 0.90,
        "evidence_json": ["Test evidence"],
        "osi_layer": "Layer 3 - Network",
        "next_command": "show ip route",
        "fix_steps_json": ["fix 1"],
        "mode": "GEMINI_LIVE",
    }
    insert_diagnosis(diag_data, db_path=temp_db)

    # Insert ACCEPTED review
    rev_data = {
        "id": "REV-TEST-01",
        "diagnosis_id": "DIAG-REV-01",
        "case_id": None,
        "decision": "ACCEPTED",
        "reviewer_name": "Aditya",
        "human_notes": "Accurate root cause and fix.",
    }
    rev_id = insert_review(rev_data, db_path=temp_db)
    assert rev_id == "REV-TEST-01"

    reviews = get_all_reviews(db_path=temp_db)
    assert len(reviews) == 1
    assert reviews[0]["decision"] == "ACCEPTED"
    assert reviews[0]["agreement_score"] == 1
    assert reviews[0]["ai_root_cause"] == "Test AI cause"


def test_insert_and_get_responsible_ai_log(temp_db):
    """Verify inserting and retrieving custom Responsible AI calibration logs."""
    log_data = {
        "id": "RAI-TEST-01",
        "case_title": "Custom Misdiagnosis Case",
        "category": "DNS",
        "ai_root_cause": "DNS Server crashed",
        "ai_confidence": 0.82,
        "human_correction": "Firewall blocked UDP port 53",
        "failure_category": "Wrong OSI Layer",
        "lesson_learned": "Check firewall rules before assuming server down",
    }
    log_id = insert_responsible_ai_log(log_data, db_path=temp_db)
    assert log_id == "RAI-TEST-01"

    all_logs = get_all_responsible_ai_logs(db_path=temp_db)
    assert len(all_logs) == 1
    assert all_logs[0]["failure_category"] == "Wrong OSI Layer"
    assert count_responsible_ai_logs(db_path=temp_db) == 1


def test_seed_db_loading(temp_db):
    """Verify that seed_db populates exactly 32 cases (4 per category) and 5 RAI logs."""
    counts = seed_db(temp_db)
    assert counts["cases_seeded"] == 32
    assert counts["rai_logs_seeded"] == 5

    # Check total counts in DB
    assert count_cases(temp_db) == 32
    assert count_responsible_ai_logs(temp_db) == 5

    # Verify exactly 4 cases exist in each of the 8 categories
    for cat in CATEGORIES:
        cases_in_cat = get_cases_by_category(cat, db_path=temp_db)
        assert len(cases_in_cat) == 4, f"Category '{cat}' should have exactly 4 cases, found {len(cases_in_cat)}"


def test_seed_idempotency(temp_db):
    """Verify that running seed_db multiple times does not produce duplicate rows."""
    # First seed
    seed_db(temp_db)
    initial_cases = count_cases(temp_db)
    initial_rai = count_responsible_ai_logs(temp_db)

    # Second seed
    second_counts = seed_db(temp_db)
    assert second_counts["cases_seeded"] == 0
    assert second_counts["rai_logs_seeded"] == 0

    assert count_cases(temp_db) == initial_cases == 32
    assert count_responsible_ai_logs(temp_db) == initial_rai == 5


def test_case_fields_integrity(temp_db):
    """Verify all 32 seeded cases have all required non-empty fields and realistic CLI evidence."""
    seed_db(temp_db)
    cases = get_all_cases(temp_db)
    assert len(cases) == 32

    required_fields = [
        "id",
        "title",
        "category",
        "severity",
        "symptom",
        "topology_notes",
        "show_commands",
        "actual_root_cause",
        "osi_layer",
        "concept_tag",
    ]

    for case in cases:
        for field in required_fields:
            value = case.get(field)
            assert value is not None and str(value).strip() != "", f"Case {case.get('id')} missing field: {field}"
        assert case["category"] in CATEGORIES
        assert "#" in case["show_commands"] or ">" in case["show_commands"]


def test_rai_fields_integrity(temp_db):
    """Verify all 5 seeded Responsible AI logs have all required fields and correct IDs (RAI-01 to RAI-05)."""
    seed_db(temp_db)
    rai_logs = get_all_responsible_ai_logs(temp_db)
    assert len(rai_logs) == 5

    expected_ids = ["RAI-01", "RAI-02", "RAI-03", "RAI-04", "RAI-05"]
    actual_ids = [log["id"] for log in rai_logs]
    assert actual_ids == expected_ids

    required_fields = [
        "id",
        "case_title",
        "category",
        "ai_root_cause",
        "ai_confidence",
        "human_correction",
        "failure_category",
        "lesson_learned",
    ]

    for log in rai_logs:
        for field in required_fields:
            value = log.get(field)
            assert value is not None and str(value).strip() != "", f"RAI log {log.get('id')} missing field: {field}"
        assert 0.0 <= float(log["ai_confidence"]) <= 1.0
