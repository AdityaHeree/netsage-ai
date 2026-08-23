"""
NetSage AI - Phase 1 Foundation Tests
Verifies that configuration, constants, and Pydantic models import and validate successfully.
"""

import pytest
from src.config import (
    CATEGORIES,
    SEVERITY_LEVELS,
    OSI_LAYERS,
    REVIEW_DECISIONS,
    FAILURE_CATEGORIES,
    is_gemini_configured,
)
from src.models import (
    RuleFinding,
    DiagnosisResponse,
    Case,
    Review,
    ResponsibleAILog,
)


def test_config_constants():
    """Verify that all required taxonomy constants are properly populated."""
    assert len(CATEGORIES) == 8
    assert "VLAN" in CATEGORIES
    assert "Gateway" in CATEGORIES
    assert "DHCP" in CATEGORIES
    assert "DNS" in CATEGORIES
    assert "Routing" in CATEGORIES
    assert "ACL" in CATEGORIES
    assert "NAT" in CATEGORIES
    assert "Wireless" in CATEGORIES

    assert "Critical" in SEVERITY_LEVELS
    assert "Layer 2 - Data Link" in OSI_LAYERS
    assert "ACCEPTED" in REVIEW_DECISIONS
    assert "Hallucination" in FAILURE_CATEGORIES


def test_is_gemini_configured_helper():
    """Verify the API key helper function logic."""
    assert is_gemini_configured("") is False
    assert is_gemini_configured("your_gemini_api_key_here") is False
    assert is_gemini_configured("AIzaSyFakeKeyTest123") is True


def test_rule_finding_model():
    """Verify RuleFinding Pydantic model validation."""
    finding = RuleFinding(
        rule_name="VLAN_ACCESS_MISMATCH",
        category="VLAN",
        severity="High",
        message="Fa0/1 is in VLAN 1 instead of VLAN 10",
        matched_evidence=["FastEthernet0/1 1 default"],
        recommendation="switchport access vlan 10",
    )
    assert finding.rule_name == "VLAN_ACCESS_MISMATCH"
    assert finding.severity == "High"
    assert len(finding.matched_evidence) == 1


def test_diagnosis_response_model():
    """Verify DiagnosisResponse Pydantic model validation and confidence constraints."""
    diag = DiagnosisResponse(
        root_cause="Port Fa0/1 is assigned to Default VLAN 1 instead of VLAN 10.",
        confidence=0.95,
        evidence=["SW1# show vlan brief -> Fa0/1 in default VLAN 1"],
        osi_layer="Layer 2 - Data Link",
        next_command="show vlan brief",
        fix_steps=["interface FastEthernet0/1", "switchport access vlan 10"],
        explanation="Access port misconfiguration prevents host from reaching VLAN 10 default gateway.",
        risk_assessment="Low",
    )
    assert diag.confidence == 0.95
    assert diag.osi_layer == "Layer 2 - Data Link"
    assert len(diag.fix_steps) == 2

    # Verify confidence must be between 0.0 and 1.0
    with pytest.raises(Exception):
        DiagnosisResponse(
            root_cause="Test",
            confidence=1.5,  # Out of range!
            evidence=[],
            osi_layer="Layer 2",
            next_command="show vlan",
            fix_steps=[],
            explanation="Test",
        )


def test_case_model():
    """Verify Case Pydantic model validation."""
    case = Case(
        id="CASE-VLAN-01",
        title="Host Cannot Ping Gateway",
        category="VLAN",
        severity="High",
        symptom="PC-1 cannot ping default gateway 192.168.10.1",
        topology_notes="PC-1 on SW1 Fa0/1, R1 on SW1 G0/1",
        show_commands="SW1# show vlan brief\n...",
        actual_root_cause="Fa0/1 in VLAN 1 instead of VLAN 10",
    )
    assert case.id == "CASE-VLAN-01"
    assert case.category == "VLAN"


def test_review_model():
    """Verify Review Pydantic model validation."""
    review = Review(
        id="REV-001",
        diagnosis_id="DIAG-001",
        decision="ACCEPTED",
        reviewer_name="Aditya",
        human_notes="Accurate diagnosis",
        agreement_score=1,
    )
    assert review.decision == "ACCEPTED"
    assert review.agreement_score == 1


def test_responsible_ai_log_model():
    """Verify ResponsibleAILog Pydantic model validation."""
    log = ResponsibleAILog(
        id="RAI-01",
        case_title="OSI Layer Mismatch in NAT",
        category="NAT",
        ai_root_cause="DNS server failure",
        ai_confidence=0.88,
        human_correction="Missing overload keyword in NAT statement",
        failure_category="Wrong OSI Layer",
        lesson_learned="Ensure NAT pool and overload status are checked before assuming Layer 7 DNS drop.",
    )
    assert log.failure_category == "Wrong OSI Layer"
    assert log.ai_confidence == 0.88
