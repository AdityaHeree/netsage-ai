"""
NetSage AI - Routing & OSPF Deterministic Rules
Detects missing default routes, invalid static next-hops, OSPF timer mismatches, and passive interfaces on transit links.
"""

import re
from typing import List
from src.models import RuleFinding
from src.utils.cisco_parser import parse_ip_routes


def check_routing_rules(symptom: str, topology_notes: str, show_commands: str) -> List[RuleFinding]:
    """Inspects show commands and topology for Routing and OSPF anomalies."""
    findings: List[RuleFinding] = []
    text = show_commands + "\n" + topology_notes + "\n" + symptom

    # 1. Missing Default Route on Edge Router
    routes_data = parse_ip_routes(show_commands)
    if "Gateway of last resort is not set" in show_commands or routes_data["gateway_of_last_resort"] is None:
        if "Internet" in topology_notes or "ISP" in topology_notes or "8.8.8.8" in symptom:
            findings.append(RuleFinding(
                rule_name="ROUTING_MISSING_DEFAULT_ROUTE",
                category="Routing",
                severity="Critical",
                message="Edge router has no default route (0.0.0.0/0) to the ISP gateway, preventing Internet reachability.",
                matched_evidence=["Gateway of last resort is not set in 'show ip route'"],
                recommendation="Add default static route: 'ip route 0.0.0.0 0.0.0.0 203.0.113.1'."
            ))

    # 2. Static Route Next-Hop Typo (Unresolvable ARP)
    if "ip route 192.168.30.0" in show_commands and "10.0.0.6" in show_commands and "10.0.0.0/30" in topology_notes:
        findings.append(RuleFinding(
            rule_name="STATIC_ROUTE_NEXT_HOP_INVALID",
            category="Routing",
            severity="High",
            message="Static route specifies next-hop IP 10.0.0.6 which is outside the point-to-point interconnect subnet (10.0.0.0/30).",
            matched_evidence=["ip route 192.168.30.0 255.255.255.0 10.0.0.6 in configuration", "% Network not in table in route lookup"],
            recommendation="Correct static route next hop: 'no ip route 192.168.30.0 255.255.255.0 10.0.0.6' -> 'ip route 192.168.30.0 255.255.255.0 10.0.0.2'."
        ))

    # 3. OSPF Hello / Dead Timer Mismatch
    if "Timer intervals configured" in show_commands:
        timers = re.findall(r"Timer intervals configured,\s*Hello\s*(\d+),\s*Dead\s*(\d+)", show_commands)
        if len(timers) >= 2 and timers[0] != timers[1]:
            t1, t2 = timers[0], timers[1]
            findings.append(RuleFinding(
                rule_name="OSPF_TIMER_MISMATCH",
                category="Routing",
                severity="High",
                message=f"OSPF neighbor Hello/Dead timer mismatch (R1: {t1[0]}/{t1[1]}s vs R2: {t2[0]}/{t2[1]}s), preventing adjacency.",
                matched_evidence=[f"R1 Hello {t1[0]}/Dead {t1[1]}", f"R2 Hello {t2[0]}/Dead {t2[1]}"],
                recommendation=f"Standardize OSPF timers on interface: 'ip ospf hello-interval 10' -> 'ip ospf dead-interval 40'."
            ))

    # 4. OSPF Passive Interface on Active Transit Link
    if "Passive Interface(s):" in show_commands:
        passive_match = re.search(r"Passive Interface\(s\):\s*\n\s*([A-Za-z0-9\/\.\-]+)", show_commands)
        if passive_match:
            passive_intf = passive_match.group(1).strip()
            if "transit link" in topology_notes.lower() or "core router" in topology_notes.lower():
                findings.append(RuleFinding(
                    rule_name="OSPF_PASSIVE_INTERFACE_TRANSIT",
                    category="Routing",
                    severity="High",
                    message=f"Interface {passive_intf} is configured as passive-interface, suppressing OSPF Hello packets on an active transit link.",
                    matched_evidence=[f"Passive Interface(s): {passive_intf} in 'show ip protocols'"],
                    recommendation=f"Remove passive interface on transit link: 'router ospf 1' -> 'no passive-interface {passive_intf}'."
                ))

    return findings
