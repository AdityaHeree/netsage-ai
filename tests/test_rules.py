"""
NetSage AI - Deterministic Rule Engine Tests
Verifies that each of the 6 rule checking modules detects specific network configuration faults.
"""

from src.rules.engine import run_deterministic_checks, format_findings_for_prompt
from src.rules.vlan_rules import check_vlan_rules
from src.rules.gateway_rules import check_gateway_rules
from src.rules.dhcp_dns_rules import check_dhcp_dns_rules
from src.rules.routing_rules import check_routing_rules
from src.rules.acl_rules import check_acl_rules
from src.rules.nat_wireless_rules import check_nat_wireless_rules


def test_vlan_access_and_trunk_rules():
    """Verify detection of VLAN access mismatch and missing trunk allowed VLANs."""
    symptom = "PC-1 cannot ping Finance gateway"
    topology = "PC-1 is in Finance VLAN 10 on SW1 Fa0/1"
    show_cmds = """
SW1# show interfaces FastEthernet0/1 switchport
Access Mode VLAN: 1 (default)
"""
    findings = check_vlan_rules(symptom, topology, show_cmds)
    assert any(f.rule_name == "VLAN_ACCESS_MISMATCH" for f in findings)

    # Test Trunk Allowed Missing
    symptom2 = "Sales hosts across SW1 and SW2 cannot communicate"
    topology2 = "SW1 to SW2 trunk on Gi0/1. Sales is VLAN 20."
    show_cmds2 = """
SW1# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      1
Port        Vlans allowed on trunk
Gi0/1       10,30
"""
    findings2 = check_vlan_rules(symptom2, topology2, show_cmds2)
    assert any(f.rule_name == "TRUNK_ALLOWED_VLAN_MISSING" for f in findings2)


def test_gateway_rules():
    """Verify detection of subnet mask mismatch and missing switch default-gateway."""
    # Subnet mask mismatch
    symptom = "Upper IP hosts cannot reach gateway 192.168.1.1"
    topology = "LAN is intended to be 192.168.1.0/24"
    show_cmds = """
R1# show ip interface GigabitEthernet0/0
GigabitEthernet0/0 is up, line protocol is up
  Internet address is 192.168.1.1/25
PC-1# ipconfig
Subnet Mask: 255.255.255.0
"""
    findings = check_gateway_rules(symptom, topology, show_cmds)
    assert any(f.rule_name == "GW_SUBNET_MASK_MISMATCH" for f in findings)

    # Missing switch default gateway
    symptom2 = "Admin cannot SSH to Switch SW1 from remote subnet"
    topology2 = "SW1 has Management VLAN 1 IP 192.168.1.2/24"
    show_cmds2 = """
SW1# show ip route
Default gateway is not set
SW1# show ip interface brief
Vlan1 192.168.1.2 YES manual up up
"""
    findings2 = check_gateway_rules(symptom2, topology2, show_cmds2)
    assert any(f.rule_name == "SWITCH_MISSING_DEFAULT_GATEWAY" for f in findings2)


def test_dhcp_dns_rules():
    """Verify detection of APIPA missing DHCP pool and excluded address conflict."""
    # APIPA / Missing Pool
    symptom = "Workstation gets 169.254.x.x"
    topology = "Local router should assign DHCP"
    show_cmds = """
PC-1> ipconfig
IP Address: 169.254.120.45
R1# show ip dhcp pool
No DHCP pools configured
"""
    findings = check_dhcp_dns_rules(symptom, topology, show_cmds)
    assert any(f.rule_name == "DHCP_POOL_MISSING" for f in findings)

    # Missing Excluded Address
    symptom2 = "Duplicate IP address detected for 192.168.1.1"
    topology2 = "Gateway is 192.168.1.1"
    show_cmds2 = """
R1# show ip dhcp conflict
IP address 192.168.1.1 Ping Mar 01 2026
R1# show running-config
ip dhcp pool LAN_POOL
 network 192.168.1.0 255.255.255.0
"""
    findings2 = check_dhcp_dns_rules(symptom2, topology2, show_cmds2)
    assert any(f.rule_name == "DHCP_EXCLUDED_ADDRESS_MISSING" for f in findings2)


def test_routing_rules():
    """Verify detection of missing default route and OSPF timer mismatch."""
    # Missing Default Route
    symptom = "Cannot ping 8.8.8.8"
    topology = "Edge router connected to ISP"
    show_cmds = """
R1# show ip route
Gateway of last resort is not set
C 10.1.1.0/24 is directly connected
"""
    findings = check_routing_rules(symptom, topology, show_cmds)
    assert any(f.rule_name == "ROUTING_MISSING_DEFAULT_ROUTE" for f in findings)

    # OSPF Timer Mismatch
    symptom2 = "OSPF neighbor state stays DOWN"
    topology2 = "R1 and R2 connected in Area 0"
    show_cmds2 = """
R1# show ip ospf interface Gi0/0
Timer intervals configured, Hello 10, Dead 40
R2# show ip ospf interface Gi0/0
Timer intervals configured, Hello 5, Dead 20
"""
    findings2 = check_routing_rules(symptom2, topology2, show_cmds2)
    assert any(f.rule_name == "OSPF_TIMER_MISMATCH" for f in findings2)


def test_acl_rules():
    """Verify detection of standard ACL misuse and inverted direction."""
    symptom = "Finance users cannot access Web Server 10.0.0.5"
    topology = "Finance LAN 192.168.10.0/24. Web server 10.0.0.5."
    show_cmds = """
R1# show access-lists 10
Standard IP access list 10
    10 deny 10.0.0.5
    20 permit any
R1# show running-config interface GigabitEthernet0/1
ip access-group 10 out
"""
    findings = check_acl_rules(symptom, topology, show_cmds)
    assert any(f.rule_name == "ACL_STANDARD_DESTINATION_MISUSE" for f in findings)

    # Inverted ACL direction
    symptom2 = "Untrusted WAN traffic not filtered"
    topology2 = "WAN ingress filter"
    show_cmds2 = """
R1# show running-config interface GigabitEthernet0/0
description WAN Ingress
ip access-group 150 out
"""
    findings2 = check_acl_rules(symptom2, topology2, show_cmds2)
    assert any(f.rule_name == "ACL_DIRECTION_INVERTED" for f in findings2)


def test_nat_wireless_rules():
    """Verify detection of missing NAT overload keyword and SSID case mismatch."""
    # Missing Overload
    symptom = "Only 1 PC can access internet at a time"
    topology = "Inside LAN has 50 PCs with single public IP. Needs PAT."
    show_cmds = """
R1# show running-config
ip nat inside source list 1 interface GigabitEthernet0/0
"""
    findings = check_nat_wireless_rules(symptom, topology, show_cmds)
    assert any(f.rule_name == "NAT_OVERLOAD_KEYWORD_MISSING" for f in findings)

    # SSID Case Mismatch
    symptom2 = "Laptop cannot associate to Wi-Fi"
    topology2 = "AP broadcasts SSID CorpNet"
    show_cmds2 = """
AP1# show running-config
dot11 ssid CorpNet
Laptop-1> show wireless-profile
SSID: corpnet
"""
    findings2 = check_nat_wireless_rules(symptom2, topology2, show_cmds2)
    assert any(f.rule_name == "WIRELESS_SSID_CASE_MISMATCH" for f in findings2)


def test_master_engine_aggregator_and_prompt_formatter():
    """Verify that run_deterministic_checks aggregates across modules and sorts by severity."""
    symptom = "Network down; Internet unreachable; PC-1 in wrong VLAN"
    topology = "PC-1 in VLAN 10. Edge router to ISP."
    show_cmds = """
SW1# show interfaces FastEthernet0/1 switchport
Access Mode VLAN: 1 (default)
R1# show ip route
Gateway of last resort is not set
"""
    findings = run_deterministic_checks(symptom, topology, show_cmds)
    assert len(findings) >= 2
    
    # Critical should precede High
    assert findings[0].severity in ["Critical", "High"]

    # Verify prompt formatting helper
    formatted_prompt = format_findings_for_prompt(findings)
    assert "Deterministic Rule Engine Findings:" in formatted_prompt
    assert "VLAN_ACCESS_MISMATCH" in formatted_prompt
    assert "ROUTING_MISSING_DEFAULT_ROUTE" in formatted_prompt
