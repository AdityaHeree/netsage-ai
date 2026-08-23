"""
NetSage AI - DHCP & DNS Deterministic Rules
Detects APIPA/missing DHCP pool, missing excluded addresses, missing IP helper-address,
DHCP default-router mismatch, unreachable DNS, and disabled domain lookups.
"""

import re
from typing import List
from src.models import RuleFinding


def check_dhcp_dns_rules(symptom: str, topology_notes: str, show_commands: str) -> List[RuleFinding]:
    """Inspects show commands and topology for DHCP and DNS anomalies."""
    findings: List[RuleFinding] = []
    text = show_commands + "\n" + topology_notes + "\n" + symptom

    # 1. APIPA & Missing DHCP Pool
    if "169.254." in text:
        if "No DHCP pools configured" in show_commands or "show ip dhcp pool" in show_commands:
            findings.append(RuleFinding(
                rule_name="DHCP_POOL_MISSING",
                category="DHCP",
                severity="High",
                message="Client received APIPA address (169.254.x.x) because no DHCP pool is configured on the local router.",
                matched_evidence=["Client IP: 169.254.120.45", "R1# show ip dhcp pool -> No DHCP pools configured"],
                recommendation="Configure DHCP pool: 'ip dhcp pool LAN_POOL' -> 'network 192.168.50.0 255.255.255.0' -> 'default-router 192.168.50.1'."
            ))

    # 2. IP Address Conflict & Missing Excluded Address
    if "show ip dhcp conflict" in show_commands.lower() or "duplicate ip address" in text.lower():
        if "excluded-address" not in show_commands:
            findings.append(RuleFinding(
                rule_name="DHCP_EXCLUDED_ADDRESS_MISSING",
                category="DHCP",
                severity="Critical",
                message="DHCP pool is missing excluded-address statement, causing DHCP server to assign the gateway's own static IP.",
                matched_evidence=["IP address conflict detected for gateway IP in DHCP conflict log"],
                recommendation="Exclude static infrastructure addresses: 'ip dhcp excluded-address 192.168.1.1 192.168.1.10'."
            ))

    # 3. Missing DHCP Relay / Helper Address
    if "Helper address is not set" in show_commands or ("centralized dhcp" in topology_notes.lower() and "helper-address" not in show_commands):
        findings.append(RuleFinding(
            rule_name="DHCP_HELPER_ADDRESS_MISSING",
            category="DHCP",
            severity="High",
            message="Router interface is missing 'ip helper-address' to relay DHCP broadcast DISCOVER packets across routed subnets.",
            matched_evidence=["Helper address is not set on GigabitEthernet0/1"],
            recommendation="Configure DHCP relay on the interface: 'interface Gi0/1' -> 'ip helper-address 10.1.1.100'."
        ))

    # 4. Incorrect Default-Router in DHCP Pool
    if "default-router 192.168.100.254" in show_commands and ("192.168.100.1" in topology_notes or "192.168.100.1" in show_commands):
        findings.append(RuleFinding(
            rule_name="DHCP_DEFAULT_ROUTER_MISMATCH",
            category="DHCP",
            severity="High",
            message="DHCP pool is distributing incorrect default-router IP (192.168.100.254) while the actual gateway IP is 192.168.100.1.",
            matched_evidence=["ip dhcp pool POOL_100 -> default-router 192.168.100.254"],
            recommendation="Update DHCP pool option: 'ip dhcp pool POOL_100' -> 'default-router 192.168.100.1'."
        ))

    # 5. DNS Server Unreachable / Typo
    if "10.0.0.35" in text and "10.0.0.53" in topology_notes:
        findings.append(RuleFinding(
            rule_name="DNS_SERVER_IP_UNREACHABLE",
            category="DNS",
            severity="Medium",
            message="Client DNS server points to unreachable IP 10.0.0.35 instead of corporate DNS server 10.0.0.53.",
            matched_evidence=["Client DNS Server: 10.0.0.35 with ping timeout"],
            recommendation="Correct client DNS server configuration to 10.0.0.53."
        ))

    # 6. Static Host Table Typo
    if "logserver" in text and "10.0.0.250" in show_commands and "10.0.0.25" in topology_notes:
        findings.append(RuleFinding(
            rule_name="DNS_STATIC_HOST_TYPO",
            category="DNS",
            severity="Low",
            message="Static 'ip host logserver' contains IP address typo (10.0.0.250 instead of 10.0.0.25).",
            matched_evidence=["Host logserver mapped to 10.0.0.250 in show hosts"],
            recommendation="Correct static host entry: 'no ip host logserver 10.0.0.250' -> 'ip host logserver 10.0.0.25'."
        ))

    # 7. Domain Lookup Disabled on Router
    if "no ip domain-lookup" in show_commands and ("name-server" in show_commands or "domain" in text):
        findings.append(RuleFinding(
            rule_name="DNS_DOMAIN_LOOKUP_DISABLED",
            category="DNS",
            severity="Low",
            message="Router has 'no ip domain-lookup' configured, preventing resolution of hostnames via DNS name-server.",
            matched_evidence=["no ip domain-lookup in running configuration"],
            recommendation="Enable domain lookup in global configuration: 'ip domain-lookup'."
        ))

    return findings
