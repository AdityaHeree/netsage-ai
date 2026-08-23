"""
NetSage AI - Master Deterministic Rule Engine
Aggregates and executes all 6 domain-specific rule modules before calling AI.
"""

from typing import List, Dict, Any
from src.models import RuleFinding
from src.rules.vlan_rules import check_vlan_rules
from src.rules.gateway_rules import check_gateway_rules
from src.rules.dhcp_dns_rules import check_dhcp_dns_rules
from src.rules.routing_rules import check_routing_rules
from src.rules.acl_rules import check_acl_rules
from src.rules.nat_wireless_rules import check_nat_wireless_rules


SEVERITY_ORDER = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


def run_deterministic_checks(
    symptom: str,
    topology_notes: str,
    show_commands: str,
) -> List[RuleFinding]:
    """
    Executes all 6 deterministic rule checking modules against input data.
    Returns a severity-sorted list of detected RuleFinding objects.
    """
    findings: List[RuleFinding] = []

    # 1. VLAN & Layer 2 Rules
    findings.extend(check_vlan_rules(symptom, topology_notes, show_commands))

    # 2. Default Gateway & ARP Rules
    findings.extend(check_gateway_rules(symptom, topology_notes, show_commands))

    # 3. DHCP & DNS Rules
    findings.extend(check_dhcp_dns_rules(symptom, topology_notes, show_commands))

    # 4. Routing & OSPF Rules
    findings.extend(check_routing_rules(symptom, topology_notes, show_commands))

    # 5. ACL & Security Rules
    findings.extend(check_acl_rules(symptom, topology_notes, show_commands))

    # 6. NAT & Wireless Rules
    findings.extend(check_nat_wireless_rules(symptom, topology_notes, show_commands))

    # Deduplicate findings by rule_name
    unique_findings: Dict[str, RuleFinding] = {}
    for f in findings:
        if f.rule_name not in unique_findings:
            unique_findings[f.rule_name] = f

    # Sort findings by severity (Critical down to Low)
    sorted_findings = sorted(
        unique_findings.values(),
        key=lambda x: SEVERITY_ORDER.get(x.severity, 0),
        reverse=True,
    )

    return sorted_findings


def format_findings_for_prompt(findings: List[RuleFinding]) -> str:
    """
    Formats rule findings as a clear text summary to be included in the AI prompt.
    Helps ground the LLM and eliminate hallucinations.
    """
    if not findings:
        return "No deterministic configuration rule violations detected."

    lines = ["Deterministic Rule Engine Findings:"]
    for idx, f in enumerate(findings, 1):
        lines.append(f"{idx}. [{f.severity}] {f.rule_name} ({f.category}): {f.message}")
        if f.matched_evidence:
            for ev in f.matched_evidence:
                lines.append(f"   - Evidence: {ev}")
        if f.recommendation:
            lines.append(f"   - Suggested Action: {f.recommendation}")
    return "\n".join(lines)
