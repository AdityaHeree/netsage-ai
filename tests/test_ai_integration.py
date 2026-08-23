"""
NetSage AI - Phase 4 AI Integration & Mock Engine Tests
Verifies prompt construction, schema validation, mock engine across 8 domains, fallback logic, and client mocking.
"""

import json
from unittest.mock import MagicMock, patch
import pytest
from pydantic import ValidationError

from src.models import DiagnosisResponse, RuleFinding
from src.ai.prompts import build_troubleshooting_prompt, SYSTEM_INSTRUCTION, FEW_SHOT_EXAMPLES
from src.ai.mock_ai import generate_mock_diagnosis
from src.ai.gemini_client import (
    create_gemini_client,
    request_gemini_diagnosis,
    diagnose_case,
)


def test_prompt_construction_and_fields():
    """Verify that all 4 required input fields are formatted into the prompt."""
    symptom = "PC-1 cannot ping gateway"
    topology = "PC-1 in VLAN 10 on SW1 Fa0/1"
    show_cmds = "SW1# show vlan brief"
    findings = [
        RuleFinding(
            rule_name="VLAN_ACCESS_MISMATCH",
            category="VLAN",
            severity="High",
            message="Fa0/1 in VLAN 1",
            matched_evidence=["Fa0/1 1 default"],
            recommendation="switchport access vlan 10",
        )
    ]

    prompt = build_troubleshooting_prompt(
        symptom=symptom,
        topology_notes=topology,
        show_commands=show_cmds,
        rule_findings=findings,
    )

    assert "User-Reported Symptom:" in prompt
    assert symptom in prompt
    assert "Topology Notes & Addressing Scheme:" in prompt
    assert topology in prompt
    assert "Cisco Show-Command Output Evidence:" in prompt
    assert show_cmds in prompt
    assert "Deterministic Pre-Check Findings:" in prompt
    assert "VLAN_ACCESS_MISMATCH" in prompt
    assert len(FEW_SHOT_EXAMPLES) >= 2


def test_pydantic_diagnosis_validation_success():
    """Verify valid DiagnosisResponse passes validation."""
    valid_data = {
        "root_cause": "VLAN mismatch on switchport",
        "confidence": 0.95,
        "evidence": ["Fa0/1 in VLAN 1"],
        "osi_layer": "Layer 2 - Data Link",
        "next_command": "show vlan brief",
        "fix_steps": ["switchport access vlan 10"],
        "explanation": "Port in wrong VLAN",
        "risk_assessment": "Low",
    }
    diag = DiagnosisResponse.model_validate(valid_data)
    assert diag.confidence == 0.95
    assert diag.osi_layer == "Layer 2 - Data Link"
    assert len(diag.fix_steps) == 1


def test_pydantic_diagnosis_validation_failure():
    """Verify out-of-range confidence or missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
        DiagnosisResponse(
            root_cause="Test",
            confidence=1.5,  # Out of range!
            evidence=["Test"],
            osi_layer="Layer 2",
            next_command="show",
            fix_steps=[],
            explanation="Test",
        )

    with pytest.raises(ValidationError):
        # Missing root_cause
        DiagnosisResponse.model_validate_json('{"confidence": 0.8}')


def test_mock_ai_vlan():
    """Verify Mock AI recognizes VLAN access mismatch scenario."""
    diag = generate_mock_diagnosis(
        symptom="PC-1 cannot ping Finance gateway",
        topology_notes="PC-1 is in VLAN 10 on Fa0/1",
        show_commands="SW1# show interfaces Fa0/1 switchport\nAccess Mode VLAN: 1 (default)",
    )
    assert isinstance(diag, DiagnosisResponse)
    assert "VLAN" in diag.root_cause
    assert diag.osi_layer == "Layer 2 - Data Link"
    assert 0.0 <= diag.confidence <= 1.0
    assert len(diag.fix_steps) > 0


def test_mock_ai_gateway():
    """Verify Mock AI recognizes Gateway subnet mask mismatch scenario."""
    diag = generate_mock_diagnosis(
        symptom="Hosts cannot ping 192.168.1.1",
        topology_notes="LAN is 192.168.1.0/24",
        show_commands="R1# show ip interface Gi0/0\nInternet address is 192.168.1.1/25\nPC-1# ipconfig\nSubnet Mask: 255.255.255.0",
    )
    assert isinstance(diag, DiagnosisResponse)
    assert "subnet mask" in diag.root_cause.lower() or "/25" in diag.root_cause
    assert diag.osi_layer == "Layer 3 - Network"


def test_mock_ai_dhcp():
    """Verify Mock AI recognizes DHCP APIPA missing pool scenario."""
    diag = generate_mock_diagnosis(
        symptom="Workstations get 169.254.x.x APIPA",
        topology_notes="Router R1 is local DHCP",
        show_commands="PC-1> ipconfig\nIP Address: 169.254.120.45\nR1# show ip dhcp pool\nNo DHCP pools configured",
    )
    assert isinstance(diag, DiagnosisResponse)
    assert "DHCP" in diag.root_cause or "APIPA" in diag.root_cause
    assert diag.osi_layer == "Layer 7 - Application"


def test_mock_ai_dns():
    """Verify Mock AI recognizes unreachable DNS server scenario."""
    diag = generate_mock_diagnosis(
        symptom="PC cannot resolve hostnames",
        topology_notes="Corporate DNS server is at 10.0.0.53",
        show_commands="PC-1> ipconfig /all\nDNS Servers: 10.0.0.35\nPC-1> ping 10.0.0.35\nRequest timed out.",
    )
    assert isinstance(diag, DiagnosisResponse)
    assert "DNS" in diag.root_cause or "10.0.0.35" in diag.root_cause
    assert diag.osi_layer == "Layer 7 - Application"


def test_mock_ai_routing():
    """Verify Mock AI recognizes missing default route scenario."""
    diag = generate_mock_diagnosis(
        symptom="Cannot access 8.8.8.8",
        topology_notes="Edge router connected to ISP",
        show_commands="R1# show ip route\nGateway of last resort is not set",
    )
    assert isinstance(diag, DiagnosisResponse)
    assert "default route" in diag.root_cause.lower() or "last resort" in diag.root_cause.lower()
    assert diag.osi_layer == "Layer 3 - Network"


def test_mock_ai_acl():
    """Verify Mock AI recognizes standard ACL destination misuse scenario."""
    diag = generate_mock_diagnosis(
        symptom="Users cannot access web server 10.0.0.5",
        topology_notes="Finance LAN to web server",
        show_commands="R1# show access-lists 10\nStandard IP access list 10\n 10 deny 10.0.0.5\nR1# show running-config\nip access-group 10 out",
    )
    assert isinstance(diag, DiagnosisResponse)
    assert "Standard ACL" in diag.root_cause or "ACL" in diag.root_cause
    assert diag.osi_layer == "Layer 3 - Network"


def test_mock_ai_nat():
    """Verify Mock AI recognizes missing NAT overload scenario."""
    diag = generate_mock_diagnosis(
        symptom="Only one host can access the Internet",
        topology_notes="50 PCs in LAN. Needs PAT.",
        show_commands="R1# show running-config\nip nat inside source list 1 interface GigabitEthernet0/0\n(no overload)",
    )
    assert isinstance(diag, DiagnosisResponse)
    assert "overload" in diag.root_cause.lower() or "PAT" in diag.root_cause
    assert diag.osi_layer == "Layer 3 - Network"


def test_mock_ai_wireless():
    """Verify Mock AI recognizes wireless SSID case mismatch."""
    diag = generate_mock_diagnosis(
        symptom="Laptop cannot connect to wireless",
        topology_notes="AP broadcasts SSID CorpNet",
        show_commands="AP1# show running-config\ndot11 ssid CorpNet\nLaptop-1> show wireless-profile\nSSID: corpnet",
    )
    assert isinstance(diag, DiagnosisResponse)
    assert "SSID" in diag.root_cause
    assert diag.osi_layer == "Layer 2 - Data Link"


def test_diagnose_case_offline_mock_mode():
    """Verify unified diagnose_case in OFFLINE_MOCK mode returns valid response."""
    result = diagnose_case(
        symptom="PC cannot reach server",
        topology_notes="VLAN 10",
        show_commands="SW1# show interfaces Fa0/1 switchport\nAccess Mode VLAN: 1 (default)",
        mode="OFFLINE_MOCK",
    )
    assert result["mode_used"] == "OFFLINE_MOCK"
    assert isinstance(result["diagnosis"], DiagnosisResponse)
    assert result["diagnosis"].confidence > 0.0
    assert len(result["rule_findings"]) > 0


def test_missing_api_key_handling():
    """Verify create_gemini_client raises ValueError when no valid API key is available."""
    with pytest.raises(ValueError, match="No valid Gemini API key"):
        create_gemini_client(api_key="")

    with pytest.raises(ValueError, match="No valid Gemini API key"):
        create_gemini_client(api_key="your_gemini_api_key_here")


def test_gemini_failure_fallback_to_mock():
    """Verify that when Gemini API call fails, diagnose_case falls back to OFFLINE_MOCK."""
    with patch("src.ai.gemini_client.request_gemini_diagnosis", side_effect=Exception("API Connection Refused")):
        result = diagnose_case(
            symptom="OSPF down",
            topology_notes="R1 and R2 in Area 0",
            show_commands="R1# show ip ospf interface Gi0/0\nTimer intervals configured, Hello 10, Dead 40\nR2# show ip ospf interface Gi0/0\nTimer intervals configured, Hello 5, Dead 20",
            mode="GEMINI_LIVE",
            api_key="AIzaFakeTestKey12345",
            allow_fallback=True,
        )
        assert result["mode_used"] == "OFFLINE_MOCK"
        assert "Gemini request failed" in result["error"]
        assert isinstance(result["diagnosis"], DiagnosisResponse)


def test_mocked_gemini_live_success():
    """Verify diagnose_case successfully processes a valid structured response from Gemini API."""
    mock_payload = {
        "root_cause": "OSPF Hello/Dead timer mismatch between R1 and R2.",
        "confidence": 0.99,
        "evidence": ["R1 has Hello 10, Dead 40", "R2 has Hello 5, Dead 20"],
        "osi_layer": "Layer 3 - Network",
        "next_command": "show ip ospf neighbor",
        "fix_steps": ["interface Gi0/0", "ip ospf hello-interval 10", "ip ospf dead-interval 40"],
        "explanation": "OSPF requires matching timers for neighbor state.",
        "risk_assessment": "Low",
    }
    
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_payload)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.ai.gemini_client.create_gemini_client", return_value=mock_client):
        result = diagnose_case(
            symptom="OSPF neighbor down",
            topology_notes="R1 and R2 Area 0",
            show_commands="Timer intervals configured, Hello 10, Dead 40",
            mode="GEMINI_LIVE",
            api_key="AIzaValidMockedTestKey",
        )
        assert result["mode_used"] == "GEMINI_LIVE"
        assert result["diagnosis"].confidence == 0.99
        assert result["diagnosis"].root_cause == "OSPF Hello/Dead timer mismatch between R1 and R2."
        assert result["error"] is None


def test_diagnose_sample_case_end_to_end():
    """Verify complete pipeline: Case input -> Deterministic Rules -> AI Diagnosis (Mock) -> Valid DiagnosisResponse."""
    from src.db import get_case_by_id, init_db, seed_db
    init_db()
    seed_db()

    case = get_case_by_id("CASE-VLAN-01")
    assert case is not None

    result = diagnose_case(
        symptom=case["symptom"],
        topology_notes=case["topology_notes"],
        show_commands=case["show_commands"],
        mode="OFFLINE_MOCK",
    )

    assert result["mode_used"] == "OFFLINE_MOCK"
    assert len(result["rule_findings"]) > 0
    assert result["rule_findings"][0].rule_name == "VLAN_ACCESS_MISMATCH"

    diag = result["diagnosis"]
    assert isinstance(diag, DiagnosisResponse)
    assert 0.0 <= diag.confidence <= 1.0
    assert diag.osi_layer == "Layer 2 - Data Link"
    assert len(diag.evidence) > 0
    assert len(diag.fix_steps) > 0
    assert "show" in diag.next_command.lower() or "ping" in diag.next_command.lower()

