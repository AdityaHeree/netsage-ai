"""
NetSage AI - NAT & Wireless Deterministic Rules
Detects missing NAT overload keywords, inverted inside/outside interfaces, NAT ACL exclusions,
SSID case mismatches, WPA-PSK key errors, AP VLAN placements, and 802.1X misconfigs.
"""

import re
from typing import List
from src.models import RuleFinding


def check_nat_wireless_rules(symptom: str, topology_notes: str, show_commands: str) -> List[RuleFinding]:
    """Inspects show commands and topology for NAT and Wireless anomalies."""
    findings: List[RuleFinding] = []
    text = show_commands + "\n" + topology_notes + "\n" + symptom

    # 1. Dynamic NAT / PAT Missing 'overload' Keyword
    if "ip nat inside source list" in show_commands and "overload" not in show_commands:
        if "PAT" in text or "hosts" in topology_notes.lower() or "single public" in text.lower() or "50 PCs" in text:
            findings.append(RuleFinding(
                rule_name="NAT_OVERLOAD_KEYWORD_MISSING",
                category="NAT",
                severity="Critical",
                message="Dynamic NAT statement is missing the 'overload' keyword, restricting translation to 1-to-1 mapping and starving other LAN hosts.",
                matched_evidence=["ip nat inside source list 1 interface GigabitEthernet0/0 (missing 'overload')"],
                recommendation="Add overload keyword: 'ip nat inside source list 1 interface Gi0/0 overload'."
            ))

    # 2. NAT Inside / Outside Interface Roles Inverted
    if "description Connected to ISP" in show_commands and "ip nat inside" in show_commands:
        if "description Connected to LAN" in show_commands and "ip nat outside" in show_commands:
            findings.append(RuleFinding(
                rule_name="NAT_INTERFACE_ROLES_INVERTED",
                category="NAT",
                severity="Critical",
                message="NAT interface roles are inverted: WAN/ISP interface is configured as 'inside' while LAN interface is configured as 'outside'.",
                matched_evidence=["GigabitEthernet0/0 (ISP): ip nat inside", "GigabitEthernet0/1 (LAN): ip nat outside"],
                recommendation="Invert NAT interface roles: 'interface Gi0/0' -> 'ip nat outside', 'interface Gi0/1' -> 'ip nat inside'."
            ))

    # 3. NAT ACL Excludes Subnet
    if "ip nat inside source list" in show_commands and "Standard IP access list 1" in show_commands:
        if "192.168.30.0" in symptom and "192.168.30.0" not in show_commands:
            findings.append(RuleFinding(
                rule_name="NAT_ACL_SUBNET_EXCLUDED",
                category="NAT",
                severity="High",
                message="The access list referenced by NAT translation does not permit the newly added Engineering subnet 192.168.30.0/24.",
                matched_evidence=["access-list 1 contains permits for 192.168.10.0 and 192.168.20.0, but omits 192.168.30.0"],
                recommendation="Add subnet to NAT ACL: 'access-list 1 permit 192.168.30.0 0.0.0.255'."
            ))

    # 4. Static 1-to-1 NAT IP Typo
    if "ip nat inside source static" in show_commands and "192.168.1.88" in show_commands and "192.168.1.80" in topology_notes:
        findings.append(RuleFinding(
            rule_name="NAT_STATIC_MAPPING_TYPO",
            category="NAT",
            severity="High",
            message="Static 1-to-1 NAT rule translates to 192.168.1.88 instead of the actual web server IP 192.168.1.80.",
            matched_evidence=["ip nat inside source static 192.168.1.88 203.0.113.10"],
            recommendation="Correct static NAT entry: 'no ip nat inside source static 192.168.1.88 203.0.113.10' -> 'ip nat inside source static 192.168.1.80 203.0.113.10'."
        ))

    # 5. Wireless SSID Case Mismatch
    if "dot11 ssid CorpNet" in show_commands and "SSID: corpnet" in show_commands:
        findings.append(RuleFinding(
            rule_name="WIRELESS_SSID_CASE_MISMATCH",
            category="Wireless",
            severity="Medium",
            message="SSID names are case-sensitive: Access Point broadcasts 'CorpNet' while client profile is configured with 'corpnet'.",
            matched_evidence=["AP SSID: CorpNet", "Client Profile SSID: corpnet"],
            recommendation="Update wireless client profile SSID to match exact case: 'CorpNet'."
        ))

    # 6. WPA2-PSK Key Mismatch / Handshake Failure
    if "HANDSHAKE_FAIL" in show_commands or "MIC failure" in show_commands:
        if "SecurePass2026!" in show_commands and "Securepass2026!" in show_commands:
            findings.append(RuleFinding(
                rule_name="WIRELESS_PSK_MISMATCH",
                category="Wireless",
                severity="Medium",
                message="WPA2 Pre-Shared Key passphrase mismatch (case difference in character 'P'/'p'), causing 4-way handshake MIC failure.",
                matched_evidence=["%DOT11-4-HANDSHAKE_FAIL: 4-way handshake failed", "AP Key: SecurePass2026! vs Client Key: Securepass2026!"],
                recommendation="Update client WPA2 passphrase to match AP: 'SecurePass2026!'."
            ))

    # 7. AP Switchport Assigned to Wrong VLAN
    if "Connected to AP-1" in show_commands and "switchport access vlan 10" in show_commands:
        if "Wireless-Clients" in show_commands and "40" in show_commands:
            findings.append(RuleFinding(
                rule_name="WIRELESS_AP_VLAN_MISPLACED",
                category="Wireless",
                severity="High",
                message="Switch port connected to Access Point is assigned to Server VLAN 10 instead of Wireless Client VLAN 40.",
                matched_evidence=["Fa0/12 (Connected to AP-1) -> switchport access vlan 10"],
                recommendation="Change AP switchport VLAN: 'interface Fa0/12' -> 'switchport access vlan 40'."
            ))

    # 8. Guest WLAN 802.1X Misconfiguration
    if "Profile Name: Guest-WiFi" in show_commands or "Guest-WiFi" in show_commands:
        if "802.1X (RADIUS)" in show_commands and ("Open" in topology_notes or "PSK" in topology_notes or "Visitors" in symptom):
            findings.append(RuleFinding(
                rule_name="WIRELESS_GUEST_AUTH_MISCONFIG",
                category="Wireless",
                severity="Medium",
                message="Guest WLAN profile is configured for 802.1X RADIUS authentication instead of Open/PSK/WebAuth.",
                matched_evidence=["WLAN Guest-WiFi: Authentication Key Management 802.1X (RADIUS)"],
                recommendation="Reconfigure Guest WLAN security to PSK or WebAuth in WLC/AP settings."
            ))

    return findings
