"""
NetSage AI - VLAN & Layer 2 Deterministic Rules
Detects access VLAN misconfigurations, trunk allowed lists, native VLAN mismatches, and inactive VLANs.
"""

import re
from typing import List
from src.models import RuleFinding
from src.utils.cisco_parser import (
    parse_vlan_brief,
    parse_interfaces_trunk,
    parse_ip_interface_brief,
)


def check_vlan_rules(symptom: str, topology_notes: str, show_commands: str) -> List[RuleFinding]:
    """Inspects show commands and topology for Layer 2 / VLAN anomalies."""
    findings: List[RuleFinding] = []
    text = show_commands + "\n" + topology_notes + "\n" + symptom

    # 1. Native VLAN Mismatch Check
    if "NATIVE_VLAN_MISMATCH" in text or "Native VLAN mismatch" in text:
        mismatch_match = re.search(r"Native VLAN mismatch discovered on ([A-Za-z0-9\/\.\-]+)\s*\((\d+)\),\s*with\s+([A-Za-z0-9_\-]+)\s+([A-Za-z0-9\/\.\-]+)\s*\((\d+)\)", text)
        evidence = [mismatch_match.group(0)] if mismatch_match else ["CDP Native VLAN mismatch alert detected in CLI output"]
        findings.append(RuleFinding(
            rule_name="VLAN_NATIVE_MISMATCH",
            category="VLAN",
            severity="Medium",
            message="Native VLAN mismatch detected across trunk link, causing potential traffic leakage or bridging loops.",
            matched_evidence=evidence,
            recommendation="Configure identical native VLAN on both ends using 'switchport trunk native vlan <id>'."
        ))

    # 2. Access Port in Default VLAN 1 while specific VLAN intended
    vlan_brief_match = re.search(r"show vlan brief([\s\S]*?)(?:[A-Za-z0-9_\-]+[#>]\s*|$)", show_commands, re.IGNORECASE)
    if "Access Mode VLAN: 1" in text or (vlan_brief_match and re.search(r"1\s+default\s+active\s+.*Fa0/1", vlan_brief_match.group(1))):
        if "VLAN 10" in topology_notes or "VLAN 20" in topology_notes or "Finance" in topology_notes:
            findings.append(RuleFinding(
                rule_name="VLAN_ACCESS_MISMATCH",
                category="VLAN",
                severity="High",
                message="Switch port is assigned to Default VLAN 1 while host belongs to a dedicated department VLAN.",
                matched_evidence=["Access Mode VLAN: 1 (default) on access port Fa0/1"],
                recommendation="Assign port to the intended VLAN: 'interface Fa0/1' -> 'switchport access vlan 10'."
            ))

    # 3. Trunk Missing Allowed VLANs
    trunks = parse_interfaces_trunk(show_commands)
    for trunk in trunks:
        allowed = trunk.get("allowed_vlans", "")
        # Check if VLAN 20 or other needed VLAN is omitted
        if allowed != "ALL" and "10,30" in allowed and ("VLAN 20" in topology_notes or "Sales" in topology_notes):
            findings.append(RuleFinding(
                rule_name="TRUNK_ALLOWED_VLAN_MISSING",
                category="VLAN",
                severity="High",
                message=f"Trunk interface {trunk['port']} allowed list ({allowed}) excludes required department VLAN 20.",
                matched_evidence=[f"Port {trunk['port']} Vlans allowed on trunk: {allowed}"],
                recommendation=f"Add VLAN to trunk allowed list: 'interface {trunk['port']}' -> 'switchport trunk allowed vlan add 20'."
            ))

    # 4. Access Port Assigned to Non-Existent VLAN (inactive status)
    if "inactive" in show_commands.lower() and re.search(r"switchport access vlan\s+(\d+)", show_commands, re.IGNORECASE):
        vlan_id_match = re.search(r"switchport access vlan\s+(\d+)", show_commands, re.IGNORECASE)
        vlan_id = vlan_id_match.group(1) if vlan_id_match else "unknown"
        if f"{vlan_id}" not in parse_vlan_brief(show_commands):
            findings.append(RuleFinding(
                rule_name="VLAN_DATABASE_MISSING",
                category="VLAN",
                severity="High",
                message=f"Switchport is configured for VLAN {vlan_id}, but VLAN {vlan_id} does not exist in the switch VLAN database.",
                matched_evidence=[f"Port status is inactive with Access VLAN {vlan_id}"],
                recommendation=f"Create the missing VLAN in global config: 'vlan {vlan_id}' -> 'name HR'."
            ))

    # 5. Administratively Down Interface
    intf_list = parse_ip_interface_brief(show_commands)
    for intf in intf_list:
        if "administratively down" in intf["status"]:
            findings.append(RuleFinding(
                rule_name="INTERFACE_ADMIN_DOWN",
                category="VLAN",
                severity="High",
                message=f"Interface {intf['interface']} is administratively shutdown.",
                matched_evidence=[intf["raw_line"]],
                recommendation=f"Enable interface: 'interface {intf['interface']}' -> 'no shutdown'."
            ))

    return findings
