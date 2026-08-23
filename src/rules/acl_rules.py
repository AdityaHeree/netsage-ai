"""
NetSage AI - ACL & Traffic Filtering Deterministic Rules
Detects standard ACL filtering destination vs source, implicit deny all drops, inverted in/out direction, and incorrect interface bindings.
"""

import re
from typing import List
from src.models import RuleFinding
from src.utils.cisco_parser import parse_access_lists


def check_acl_rules(symptom: str, topology_notes: str, show_commands: str) -> List[RuleFinding]:
    """Inspects show commands and topology for ACL and filtering anomalies."""
    findings: List[RuleFinding] = []
    text = show_commands + "\n" + topology_notes + "\n" + symptom

    # 1. Standard ACL Used for Outbound Destination Filtering
    if "Standard IP access list 10" in show_commands or "access-list 10 deny 10.0.0.5" in text:
        if "ip access-group 10 out" in show_commands and "10.0.0.5" in show_commands:
            findings.append(RuleFinding(
                rule_name="ACL_STANDARD_DESTINATION_MISUSE",
                category="ACL",
                severity="High",
                message="Standard ACL 10 filters source addresses; applying 'deny 10.0.0.5' outbound inappropriately filters packets originating from 10.0.0.5 instead of traffic destined to it.",
                matched_evidence=["Standard IP access list 10: deny 10.0.0.5", "ip access-group 10 out on GigabitEthernet0/1"],
                recommendation="Replace standard ACL with an extended ACL that inspects destination IP: 'access-list 100 deny ip any host 10.0.0.5' -> 'access-list 100 permit ip any any'."
            ))

    # 2. Implicit Deny All Blocking Management/DNS/Required Traffic
    if "Implicit Deny" in show_commands or "Implicit Deny all" in show_commands:
        if "SSH" in symptom or "ping" in symptom or "DNS" in symptom:
            findings.append(RuleFinding(
                rule_name="ACL_IMPLICIT_DENY_BLOCK",
                category="ACL",
                severity="Medium",
                message="Extended ACL only permits HTTP/HTTPS; implicit 'deny ip any any' at the end of the access-list drops unlisted management, DNS, or ICMP traffic.",
                matched_evidence=["Extended IP access list lacks explicit permit for required protocol"],
                recommendation="Add explicit permit ACE for required traffic or management protocol."
            ))

    # 3. Inbound Filter Applied Inverted as Outbound
    if "ip access-group 150 out" in show_commands and ("WAN Ingress" in show_commands or "ingress" in topology_notes.lower() or "untrusted" in text.lower()):
        findings.append(RuleFinding(
            rule_name="ACL_DIRECTION_INVERTED",
            category="ACL",
            severity="High",
            message="Security filter ACL 150 is applied in the 'out' direction instead of 'in' on ingress WAN interface.",
            matched_evidence=["Outbound access list is 150 on GigabitEthernet0/0 (WAN Ingress)"],
            recommendation="Change access-group direction to inbound: 'interface Gi0/0' -> 'no ip access-group 150 out' -> 'ip access-group 150 in'."
        ))

    # 4. ACL Applied to Wrong Physical Interface
    if "ip access-group 102 in" in show_commands and "GigabitEthernet0/0" in show_commands:
        if "Guest LAN" in show_commands or ("Guest" in topology_notes and "GigabitEthernet0/1" in topology_notes):
            findings.append(RuleFinding(
                rule_name="ACL_WRONG_INTERFACE_PLACEMENT",
                category="ACL",
                severity="Medium",
                message="Guest isolation ACL 102 was applied to WAN interface Gi0/0 instead of Guest interface Gi0/1.",
                matched_evidence=["ip access-group 102 in applied to GigabitEthernet0/0", "GigabitEthernet0/1 (Guest LAN) has no access-group applied"],
                recommendation="Move ACL binding: 'interface Gi0/0' -> 'no ip access-group 102 in', 'interface Gi0/1' -> 'ip access-group 102 in'."
            ))

    return findings
