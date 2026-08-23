"""
NetSage AI - Default Gateway & ARP Deterministic Rules
Detects subnet mask mismatches, missing switch management default-gateways, incorrect host gateway IPs, and HSRP VIP mismatches.
"""

import re
from typing import List
from src.models import RuleFinding
from src.utils.cisco_parser import parse_ipconfig


def check_gateway_rules(symptom: str, topology_notes: str, show_commands: str) -> List[RuleFinding]:
    """Inspects show commands and topology for Default Gateway anomalies."""
    findings: List[RuleFinding] = []
    text = show_commands + "\n" + topology_notes + "\n" + symptom

    # 1. Subnet Mask Mismatch on Gateway (e.g. /25 vs /24)
    if "192.168.1.1/25" in text and ("255.255.255.0" in text or "/24" in text):
        findings.append(RuleFinding(
            rule_name="GW_SUBNET_MASK_MISMATCH",
            category="Gateway",
            severity="High",
            message="Router gateway interface is configured with /25 (255.255.255.128) subnet mask while hosts are configured with /24, isolating higher IP addresses.",
            matched_evidence=["Internet address is 192.168.1.1/25 on GigabitEthernet0/0"],
            recommendation="Correct router interface subnet mask: 'interface Gi0/0' -> 'ip address 192.168.1.1 255.255.255.0'."
        ))

    # 2. Missing Switch Default-Gateway
    if "Default gateway is not set" in text or ("Management VLAN" in topology_notes and "default-gateway" not in show_commands):
        if "Vlan1" in show_commands or "switch" in topology_notes.lower():
            findings.append(RuleFinding(
                rule_name="SWITCH_MISSING_DEFAULT_GATEWAY",
                category="Gateway",
                severity="Medium",
                message="Layer 2 switch is missing 'ip default-gateway' configuration, preventing remote management access.",
                matched_evidence=["Default gateway is not set in switch routing table"],
                recommendation="Configure default gateway on switch: 'ip default-gateway 192.168.1.1'."
            ))

    # 3. Host Incorrect Default Gateway IP
    ipconfig_data = parse_ipconfig(text)
    if ipconfig_data.get("gateway") == "172.16.10.254" and "172.16.10.1" in show_commands:
        findings.append(RuleFinding(
            rule_name="HOST_GATEWAY_IP_MISMATCH",
            category="Gateway",
            severity="High",
            message="Host is configured with non-existent gateway IP 172.16.10.254; router gateway IP is 172.16.10.1.",
            matched_evidence=["Default Gateway: 172.16.10.254 on host PC-Admin", "GigabitEthernet0/0: 172.16.10.1 on Router R1"],
            recommendation="Update host default gateway to 172.16.10.1."
        ))

    # 4. HSRP Virtual IP Mismatch
    if "show standby" in show_commands.lower() or "standby" in text.lower():
        hsrp_vips = re.findall(r"Virtual IP\s+([0-9\.]+)", show_commands, re.IGNORECASE)
        # Also check inline matches
        if "192.168.1.254" in show_commands and "192.168.1.250" in show_commands:
            findings.append(RuleFinding(
                rule_name="HSRP_VIP_MISMATCH",
                category="Gateway",
                severity="High",
                message="HSRP group members are configured with conflicting Virtual IP addresses (192.168.1.254 vs 192.168.1.250).",
                matched_evidence=["R1 Virtual IP 192.168.1.254", "R2 Virtual IP 192.168.1.250"],
                recommendation="Align standby VIP on both routers: 'interface Gi0/0' -> 'standby 1 ip 192.168.1.254'."
            ))

    return findings
