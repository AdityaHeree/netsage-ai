"""
NetSage AI - Smart Offline Mock Diagnostic Engine
Generates realistic, validated DiagnosisResponse objects without internet or Gemini API access.
"""

from typing import List, Optional
from src.models import DiagnosisResponse, RuleFinding
from src.rules.engine import run_deterministic_checks


def generate_mock_diagnosis(
    symptom: str,
    topology_notes: str,
    show_commands: str,
    rule_findings: Optional[List[RuleFinding]] = None,
) -> DiagnosisResponse:
    """
    Generates a realistic, domain-specific DiagnosisResponse using pattern matching
    over the symptom, topology, show-command text, and deterministic rule findings.
    """
    findings = rule_findings if rule_findings is not None else run_deterministic_checks(
        symptom=symptom,
        topology_notes=topology_notes,
        show_commands=show_commands,
    )
    rule_names = {f.rule_name for f in findings}
    text = (symptom + "\n" + topology_notes + "\n" + show_commands).lower()

    # -------------------------------------------------------------------------
    # 1. VLAN Scenarios
    # -------------------------------------------------------------------------
    if "VLAN_ACCESS_MISMATCH" in rule_names or ("vlan 1" in text and "vlan 10" in text and "fa0/1" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Switchport FastEthernet0/1 is incorrectly assigned to Default VLAN 1 instead of VLAN 10 (Finance), isolating the host from its gateway.",
            confidence=0.96,
            evidence=[
                "Deterministic rule check triggered: VLAN_ACCESS_MISMATCH",
                "SW1# show interfaces Fa0/1 switchport reports Access Mode VLAN: 1 (default)",
                "Topology notes require Fa0/1 to reside in VLAN 10 (Finance)"
            ],
            osi_layer="Layer 2 - Data Link",
            next_command="show vlan brief",
            fix_steps=[
                "configure terminal",
                "interface FastEthernet0/1",
                "switchport mode access",
                "switchport access vlan 10",
                "end"
            ],
            explanation="When an access port is in the wrong VLAN, its Ethernet frames cannot traverse to the router sub-interface or default gateway residing in another VLAN.",
            risk_assessment="Low"
        )

    if "TRUNK_ALLOWED_VLAN_MISSING" in rule_names or ("allowed on trunk" in text and "10,30" in text and "20" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Trunk interface Gi0/1 has an allowed VLAN list restricting traffic to VLANs 10 and 30, dropping VLAN 20 (Sales) frames between switches.",
            confidence=0.95,
            evidence=[
                "Deterministic rule check triggered: TRUNK_ALLOWED_VLAN_MISSING",
                "SW1# show interfaces trunk indicates Vlans allowed on trunk: 10,30",
                "VLAN 20 is active in management domain but filtered on Gi0/1"
            ],
            osi_layer="Layer 2 - Data Link",
            next_command="show interfaces trunk",
            fix_steps=[
                "configure terminal",
                "interface GigabitEthernet0/1",
                "switchport trunk allowed vlan add 20",
                "end"
            ],
            explanation="802.1Q trunks only forward broadcast and unicast frames for VLANs included in the trunk allowed list. Adding VLAN 20 permits inter-switch Sales traffic.",
            risk_assessment="Low"
        )

    if "VLAN_NATIVE_MISMATCH" in rule_names or "native_vlan_mismatch" in text or "native vlan mismatch" in text:
        return DiagnosisResponse(
            root_cause="[Mock Mode] 802.1Q Native VLAN mismatch across trunk link Fa0/24 (SW1 is set to Native VLAN 10 while SW2 is set to Native VLAN 99).",
            confidence=0.97,
            evidence=[
                "CDP alert: %CDP-4-NATIVE_VLAN_MISMATCH discovered on FastEthernet0/24",
                "SW1 Native VLAN: 10, SW2 Native VLAN: 99 in trunk parameters"
            ],
            osi_layer="Layer 2 - Data Link",
            next_command="show interfaces trunk",
            fix_steps=[
                "configure terminal",
                "interface FastEthernet0/24",
                "switchport trunk native vlan 99",
                "end"
            ],
            explanation="Mismatched native VLANs cause untagged frames from one VLAN to be mistakenly received into a different VLAN on the remote switch, creating security and spanning tree anomalies.",
            risk_assessment="Medium"
        )

    if "VLAN_DATABASE_MISSING" in rule_names or ("inactive" in text and "vlan 50" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Switchport Fa0/5 is assigned to VLAN 50, but VLAN 50 has not been created in the switch VLAN database, forcing the port into an inactive state.",
            confidence=0.95,
            evidence=[
                "SW1# show interfaces FastEthernet0/5 status reports status: inactive",
                "SW1# show vlan brief does not contain an entry for VLAN 50"
            ],
            osi_layer="Layer 2 - Data Link",
            next_command="show vlan brief",
            fix_steps=[
                "configure terminal",
                "vlan 50",
                "name HR",
                "end"
            ],
            explanation="Cisco IOS will not forward traffic on access ports assigned to non-existent VLAN IDs. Creating the VLAN in the database transitions the interface to active forwarding.",
            risk_assessment="Low"
        )

    # -------------------------------------------------------------------------
    # 2. Gateway Scenarios
    # -------------------------------------------------------------------------
    if "GW_SUBNET_MASK_MISMATCH" in rule_names or ("192.168.1.1/25" in text and "255.255.255.0" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Router interface GigabitEthernet0/0 is configured with subnet mask /25 (255.255.255.128) while client workstations use /24 (255.255.255.0), isolating hosts with IPs .128-.254.",
            confidence=0.96,
            evidence=[
                "R1# show ip interface GigabitEthernet0/0 reports Internet address is 192.168.1.1/25",
                "PC-1 ipconfig reports Subnet Mask 255.255.255.0 with IP 192.168.1.150"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip interface GigabitEthernet0/0",
            fix_steps=[
                "configure terminal",
                "interface GigabitEthernet0/0",
                "ip address 192.168.1.1 255.255.255.0",
                "end"
            ],
            explanation="A /25 mask limits the router's local broadcast domain to 192.168.1.0 - 192.168.1.127. Workstations with IP addresses above .127 cannot be reached by the router without a routing entry.",
            risk_assessment="Medium"
        )

    if "SWITCH_MISSING_DEFAULT_GATEWAY" in rule_names or ("default gateway is not set" in text and "vlan1" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Layer 2 Switch SW1 is missing the 'ip default-gateway' command, preventing management response packets from returning to remote subnets.",
            confidence=0.94,
            evidence=[
                "SW1# show ip route displays 'Default gateway is not set'",
                "SW1# show running-config contains no default-gateway configuration"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip route",
            fix_steps=[
                "configure terminal",
                "ip default-gateway 192.168.1.1",
                "end"
            ],
            explanation="Layer 2 switches do not maintain an IP routing table; they require an explicit 'ip default-gateway' to forward management SSH/ICMP replies outside their local subnet.",
            risk_assessment="Low"
        )

    if "HOST_GATEWAY_IP_MISMATCH" in rule_names or ("172.16.10.254" in text and "172.16.10.1" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Host PC-Admin is statically configured with non-existent default gateway 172.16.10.254 instead of the actual router gateway IP 172.16.10.1.",
            confidence=0.98,
            evidence=[
                "PC-Admin ipconfig lists Default Gateway: 172.16.10.254",
                "R1# show ip interface brief shows GigabitEthernet0/0 is 172.16.10.1"
            ],
            osi_layer="Layer 3 - Network",
            next_command="ping 172.16.10.1",
            fix_steps=[
                "# On PC-Admin Network Settings:",
                "Set Default Gateway to 172.16.10.1"
            ],
            explanation="A host cannot forward frames outside its local subnet when its default gateway IP cannot be resolved via ARP.",
            risk_assessment="Low"
        )

    if "HSRP_VIP_MISMATCH" in rule_names or ("show standby" in text and "192.168.1.254" in text and "192.168.1.250" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] HSRP Group 1 Virtual IP mismatch between R1 (192.168.1.254) and R2 (192.168.1.250), causing split-brain active state on both routers.",
            confidence=0.95,
            evidence=[
                "R1# show standby brief shows Grp 1 Virtual IP 192.168.1.254",
                "R2# show standby brief shows Grp 1 Virtual IP 192.168.1.250"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show standby brief",
            fix_steps=[
                "configure terminal",
                "interface GigabitEthernet0/0",
                "standby 1 ip 192.168.1.254",
                "end"
            ],
            explanation="HSRP requires identical standby group numbers and virtual IP configurations across redundant peers to establish proper active/standby failover states.",
            risk_assessment="Medium"
        )

    # -------------------------------------------------------------------------
    # 3. DHCP Scenarios
    # -------------------------------------------------------------------------
    if "DHCP_POOL_MISSING" in rule_names or ("169.254." in text and "no dhcp pools" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] DHCP pool has not been configured on Router R1 for subnet 192.168.50.0/24, causing clients to fall back to APIPA (169.254.x.x).",
            confidence=0.96,
            evidence=[
                "Client received 169.254.120.45 APIPA address",
                "R1# show ip dhcp pool returns 'No DHCP pools configured'"
            ],
            osi_layer="Layer 7 - Application",
            next_command="show ip dhcp pool",
            fix_steps=[
                "configure terminal",
                "ip dhcp pool LAN_POOL",
                "network 192.168.50.0 255.255.255.0",
                "default-router 192.168.50.1",
                "dns-server 8.8.8.8",
                "end"
            ],
            explanation="When a DHCP client broadcasts DISCOVER packets without an active DHCP pool on the local router or relay, the client assigns itself an automatic 169.254.0.0/16 address.",
            risk_assessment="Low"
        )

    if "DHCP_EXCLUDED_ADDRESS_MISSING" in rule_names or ("dhcp conflict" in text and "192.168.1.1" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] DHCP pool is missing the 'ip dhcp excluded-address' statement for the gateway IP 192.168.1.1, causing the router to issue its own IP to a client workstation.",
            confidence=0.97,
            evidence=[
                "R1# show ip dhcp conflict lists conflict on 192.168.1.1 detected by Ping",
                "Running configuration lacks 'ip dhcp excluded-address 192.168.1.1'"
            ],
            osi_layer="Layer 7 - Application",
            next_command="show ip dhcp conflict",
            fix_steps=[
                "configure terminal",
                "ip dhcp excluded-address 192.168.1.1 192.168.1.10",
                "end",
                "clear ip dhcp conflict *"
            ],
            explanation="DHCP servers will lease all addresses in their configured network statement unless static infrastructure addresses (gateways, servers, printers) are explicitly excluded.",
            risk_assessment="Medium"
        )

    if "DHCP_HELPER_ADDRESS_MISSING" in rule_names or ("helper address is not set" in text and "10.1.1.100" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Router interface GigabitEthernet0/1 lacks an 'ip helper-address' configuration to relay broadcast DHCP DISCOVER requests to the central DHCP server at 10.1.1.100.",
            confidence=0.96,
            evidence=[
                "R1# show ip interface GigabitEthernet0/1 indicates 'Helper address is not set'",
                "Central DHCP server is located across routed boundary on 10.1.1.100"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip interface GigabitEthernet0/1",
            fix_steps=[
                "configure terminal",
                "interface GigabitEthernet0/1",
                "ip helper-address 10.1.1.100",
                "end"
            ],
            explanation="Routers drop broadcast packets by default. The 'ip helper-address' command converts UDP broadcast DISCOVER (port 67) into unicast packets directed to the central server.",
            risk_assessment="Low"
        )

    if "DHCP_DEFAULT_ROUTER_MISMATCH" in rule_names or ("default-router 192.168.100.254" in text and "192.168.100.1" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] DHCP pool POOL_100 is configured with 'default-router 192.168.100.254' when the actual router interface IP is 192.168.100.1.",
            confidence=0.97,
            evidence=[
                "R1# show running-config lists default-router 192.168.100.254",
                "Active gateway interface GigabitEthernet0/0 is 192.168.100.1"
            ],
            osi_layer="Layer 7 - Application",
            next_command="show ip dhcp pool POOL_100",
            fix_steps=[
                "configure terminal",
                "ip dhcp pool POOL_100",
                "default-router 192.168.100.1",
                "end"
            ],
            explanation="DHCP Option 3 (Router) distributes the default gateway to clients. Supplying an unassigned IP prevents clients from reaching external subnets.",
            risk_assessment="Low"
        )

    # -------------------------------------------------------------------------
    # 4. DNS Scenarios
    # -------------------------------------------------------------------------
    if "DNS_SERVER_IP_UNREACHABLE" in rule_names or ("10.0.0.35" in text and "10.0.0.53" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Client PC-1 has its DNS server set to unreachable IP 10.0.0.35 instead of the valid corporate DNS server at 10.0.0.53.",
            confidence=0.96,
            evidence=[
                "PC-1 ipconfig /all reports DNS Servers: 10.0.0.35",
                "ping 10.0.0.35 fails with Request timed out",
                "Topology notes confirm DNS server IP is 10.0.0.53"
            ],
            osi_layer="Layer 7 - Application",
            next_command="ping 10.0.0.53",
            fix_steps=[
                "# On Client PC-1 Network Settings:",
                "Update primary DNS server to 10.0.0.53"
            ],
            explanation="Domain name resolution fails because queries sent to 10.0.0.35 time out. Pointing the client to 10.0.0.53 restores FQDN lookup.",
            risk_assessment="Low"
        )

    if "DNS_DOMAIN_LOOKUP_DISABLED" in rule_names or ("no ip domain-lookup" in text and "name-server" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Router has 'no ip domain-lookup' configured, preventing the IOS kernel from sending DNS queries to the configured name-server.",
            confidence=0.94,
            evidence=[
                "R1# show running-config contains 'no ip domain-lookup'",
                "Ping by FQDN fails with '% Unrecognized host or address'"
            ],
            osi_layer="Layer 7 - Application",
            next_command="show hosts",
            fix_steps=[
                "configure terminal",
                "ip domain-lookup",
                "end"
            ],
            explanation="'no ip domain-lookup' disables DNS client functionality in Cisco IOS, causing all hostname lookups to fail unless statically defined in 'ip host'.",
            risk_assessment="Low"
        )

    # -------------------------------------------------------------------------
    # 5. Routing Scenarios
    # -------------------------------------------------------------------------
    if "ROUTING_MISSING_DEFAULT_ROUTE" in rule_names or ("gateway of last resort is not set" in text and ("isp" in text or "8.8.8.8" in text)):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Edge Router R1 lacks a default route ('Gateway of last resort is not set') to the ISP gateway at 203.0.113.1, dropping outbound Internet traffic.",
            confidence=0.98,
            evidence=[
                "Deterministic rule check triggered: ROUTING_MISSING_DEFAULT_ROUTE",
                "R1# show ip route displays 'Gateway of last resort is not set'",
                "ISP link 203.0.113.0/30 is directly connected on Gi0/1"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip route 0.0.0.0",
            fix_steps=[
                "configure terminal",
                "ip route 0.0.0.0 0.0.0.0 203.0.113.1",
                "end"
            ],
            explanation="Routers drop any destination packet not matching a specific route in the routing table. Adding a default static route (0.0.0.0/0) forwards all unknown traffic to the ISP.",
            risk_assessment="Low"
        )

    if "STATIC_ROUTE_NEXT_HOP_INVALID" in rule_names or ("10.0.0.6" in text and "10.0.0.0/30" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Static route for 192.168.30.0/24 specifies next-hop IP 10.0.0.6 which is not on the directly connected /30 link (10.0.0.0/30), resulting in an unresolvable next-hop.",
            confidence=0.96,
            evidence=[
                "R1# show running-config lists 'ip route 192.168.30.0 255.255.255.0 10.0.0.6'",
                "Point-to-point link subnet is 10.0.0.0/30 (valid host IPs are 10.0.0.1 and 10.0.0.2)",
                "R1# show ip route reports '% Network not in table'"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip route 192.168.30.0",
            fix_steps=[
                "configure terminal",
                "no ip route 192.168.30.0 255.255.255.0 10.0.0.6",
                "ip route 192.168.30.0 255.255.255.0 10.0.0.2",
                "end"
            ],
            explanation="Static routes require a next-hop IP that is directly reachable on a connected subnet. 10.0.0.6 is unreachable, causing the route to be excluded from the FIB.",
            risk_assessment="Low"
        )

    if "OSPF_TIMER_MISMATCH" in rule_names or ("timer intervals configured" in text and "hello 10" in text and "hello 5" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] OSPF Hello/Dead timer mismatch on GigabitEthernet0/0 (R1 has 10/40s, R2 has 5/20s), preventing neighbor adjacency formation.",
            confidence=0.97,
            evidence=[
                "R1# show ip ospf interface Gi0/0 reports Hello 10, Dead 40",
                "R2# show ip ospf interface Gi0/0 reports Hello 5, Dead 20",
                "R1# show ip ospf neighbor displays no active neighbors"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip ospf neighbor",
            fix_steps=[
                "configure terminal",
                "interface GigabitEthernet0/0",
                "ip ospf hello-interval 10",
                "ip ospf dead-interval 40",
                "end"
            ],
            explanation="OSPF requires Hello and Dead intervals to match exactly between directly connected neighbors before establishing a 2-WAY or FULL adjacency.",
            risk_assessment="Medium"
        )

    if "OSPF_PASSIVE_INTERFACE_TRANSIT" in rule_names or ("passive-interface" in text and "transit" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Transit interface GigabitEthernet0/1 is configured with 'passive-interface', suppressing OSPF Hello packet transmission to core neighbor R2.",
            confidence=0.96,
            evidence=[
                "R1# show ip protocols lists GigabitEthernet0/1 under Passive Interface(s)",
                "No OSPF neighbor adjacency formed across Gi0/1"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip ospf neighbor",
            fix_steps=[
                "configure terminal",
                "router ospf 1",
                "no passive-interface GigabitEthernet0/1",
                "end"
            ],
            explanation="Passive interfaces advertise their connected subnet into OSPF but suppress sending and receiving Hello packets, preventing adjacencies on interconnecting transit links.",
            risk_assessment="Low"
        )

    # -------------------------------------------------------------------------
    # 6. ACL Scenarios
    # -------------------------------------------------------------------------
    if "ACL_STANDARD_DESTINATION_MISUSE" in rule_names or (("access-list 10" in text or "access list 10" in text) and "10.0.0.5" in text and "out" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Standard ACL 10 was applied outbound with 'deny 10.0.0.5', which checks packet SOURCE IP rather than DESTINATION IP, blocking legitimate return traffic.",
            confidence=0.96,
            evidence=[
                "R1# show access-lists 10 displays Standard IP access list 10: deny 10.0.0.5",
                "Standard ACLs (1-99) only filter by source address and cannot inspect destination IP"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show access-lists",
            fix_steps=[
                "configure terminal",
                "interface GigabitEthernet0/1",
                "no ip access-group 10 out",
                "ip access-list extended ACL_WEB_FILTER",
                "deny ip any host 10.0.0.5",
                "permit ip any any",
                "interface GigabitEthernet0/1",
                "ip access-group ACL_WEB_FILTER out",
                "end"
            ],
            explanation="Standard access lists only examine source IP addresses. When placed outbound towards a server, they inspect whether the packet originated from the server, causing logic errors.",
            risk_assessment="Medium"
        )

    if "ACL_DIRECTION_INVERTED" in rule_names or ("ip access-group 150 out" in text and "ingress" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Inbound security filter ACL 150 is applied in the 'out' direction on WAN ingress interface GigabitEthernet0/0, leaving ingress traffic uninspected.",
            confidence=0.96,
            evidence=[
                "R1# show ip interface GigabitEthernet0/0 reports 'Outbound access list is 150'",
                "Inbound access list is not set on the untrusted WAN interface"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip interface GigabitEthernet0/0",
            fix_steps=[
                "configure terminal",
                "interface GigabitEthernet0/0",
                "no ip access-group 150 out",
                "ip access-group 150 in",
                "end"
            ],
            explanation="Access lists applied in the outbound direction filter packets exiting the interface. Applying ACL 150 'in' ensures untrusted ingress packets are filtered upon entry.",
            risk_assessment="Medium"
        )

    # -------------------------------------------------------------------------
    # 7. NAT Scenarios
    # -------------------------------------------------------------------------
    if "NAT_OVERLOAD_KEYWORD_MISSING" in rule_names or ("ip nat inside source list 1 interface" in text and ("pat" in text or "only one host" in text or "single public" in text or "overload" not in text)):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Dynamic NAT configuration on Router R1 is missing the 'overload' keyword, enabling 1-to-1 dynamic NAT rather than Port Address Translation (PAT).",
            confidence=0.98,
            evidence=[
                "R1# show running-config lists 'ip nat inside source list 1 interface GigabitEthernet0/0' without 'overload'",
                "R1# show ip nat translations contains only 1 entry with no port translations"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip nat translations",
            fix_steps=[
                "configure terminal",
                "no ip nat inside source list 1 interface GigabitEthernet0/0",
                "ip nat inside source list 1 interface GigabitEthernet0/0 overload",
                "end"
            ],
            explanation="Without 'overload', dynamic NAT maps the single public IP to the first requesting host. Subsequent hosts cannot obtain an address translation until the active session expires.",
            risk_assessment="Low"
        )

    if "NAT_INTERFACE_ROLES_INVERTED" in rule_names or ("ip nat inside" in text and "connected to isp" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] NAT interface roles are inverted: WAN/ISP interface Gi0/0 is configured as 'ip nat inside' while LAN interface Gi0/1 is configured as 'ip nat outside'.",
            confidence=0.97,
            evidence=[
                "GigabitEthernet0/0 (ISP WAN): ip nat inside",
                "GigabitEthernet0/1 (LAN): ip nat outside",
                "show ip nat translations is completely empty"
            ],
            osi_layer="Layer 3 - Network",
            next_command="show ip nat translations",
            fix_steps=[
                "configure terminal",
                "interface GigabitEthernet0/0",
                "no ip nat inside",
                "ip nat outside",
                "interface GigabitEthernet0/1",
                "no ip nat outside",
                "ip nat inside",
                "end"
            ],
            explanation="Cisco IOS NAT triggers translation when packets travel from an 'inside' interface to an 'outside' interface. Inverting these roles prevents translations from initiating.",
            risk_assessment="Medium"
        )

    # -------------------------------------------------------------------------
    # 8. Wireless Scenarios
    # -------------------------------------------------------------------------
    if "WIRELESS_SSID_CASE_MISMATCH" in rule_names or ("ssid corpnet" in text and "ssid: corpnet" in text and "corpnet" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] Wireless SSID name case mismatch: AP-1 broadcasts SSID 'CorpNet' (mixed case) while client profile is configured with 'corpnet' (all lowercase).",
            confidence=0.96,
            evidence=[
                "AP1# show running-config lists 'dot11 ssid CorpNet'",
                "Laptop-1 wireless profile specifies 'SSID: corpnet'",
                "802.11 SSID parameters are strictly case-sensitive"
            ],
            osi_layer="Layer 2 - Data Link",
            next_command="show dot11 associations",
            fix_steps=[
                "# On Wireless Client Device:",
                "Edit wireless connection profile SSID to match exact case: CorpNet"
            ],
            explanation="802.11 Beacon frames match client probe requests using byte-exact string comparison. A case mismatch prevents probe response and association.",
            risk_assessment="Low"
        )

    if "WIRELESS_PSK_MISMATCH" in rule_names or ("handshake_fail" in text or "mic failure" in text):
        return DiagnosisResponse(
            root_cause="[Mock Mode] WPA2-PSK passphrase mismatch (case sensitivity in 'SecurePass2026!' vs 'Securepass2026!'), causing 4-Way Handshake Message Integrity Code (MIC) authentication failure.",
            confidence=0.98,
            evidence=[
                "%DOT11-4-HANDSHAKE_FAIL: 4-way handshake failed for client - MIC failure",
                "AP Key: SecurePass2026! vs Client Key: Securepass2026!"
            ],
            osi_layer="Layer 2 - Data Link",
            next_command="show logging | include Handshake",
            fix_steps=[
                "# On Wireless Client Device:",
                "Re-enter WPA2-PSK passphrase exactly: SecurePass2026!"
            ],
            explanation="In WPA2-PSK 4-way handshake, both client and AP derive the Pairwise Master Key (PMK) from the passphrase. A passphrase typo causes MIC validation to fail.",
            risk_assessment="Low"
        )

    # -------------------------------------------------------------------------
    # 9. Generic / Fallback Diagnostic
    # -------------------------------------------------------------------------
    rule_summary = findings[0].message if findings else "Unidentified network anomaly."
    rule_rec = findings[0].recommendation if findings and findings[0].recommendation else "Review interface and routing configuration."

    return DiagnosisResponse(
        root_cause=f"[Mock Mode] Detected potential configuration issue: {rule_summary}",
        confidence=0.75 if findings else 0.50,
        evidence=[f"Observation: {f.message}" for f in findings] or ["Raw CLI evidence supplied for analysis"],
        osi_layer=findings[0].category + " Layer" if findings else "Layer 3 - Network",
        next_command="show running-config",
        fix_steps=[rule_rec],
        explanation="Offline Mock Engine evaluated the supplied symptom and CLI show-command text against known baseline rule heuristics.",
        risk_assessment="Low"
    )
