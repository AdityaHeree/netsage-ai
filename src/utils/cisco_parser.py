"""
NetSage AI - Cisco CLI Text Parser
Extracts structured network state from raw Cisco IOS show commands and running configurations.
Note: CLI text is strictly analyzed as data; no commands are executed on the host system.
"""

import re
from typing import Any, Dict, List, Optional


def extract_command_blocks(raw_text: str) -> Dict[str, str]:
    """
    Splits multi-command CLI output into individual command sections.
    Matches lines starting with prompt like 'Router# show ...', 'SW1# show ...', 'PC-1> ...'
    """
    blocks: Dict[str, str] = {}
    if not raw_text or not raw_text.strip():
        return blocks

    pattern = r"(?:^|\n)([A-Za-z0-9_\-\.\(\)]+[#>]\s*show\s+[^\n]+|[A-Za-z0-9_\-\.\(\)]+[#>]\s*ipconfig[^\n]*)"
    splits = re.split(pattern, raw_text, flags=re.IGNORECASE)

    if len(splits) <= 1:
        # No clear show prompt delimiters, store entire text under 'raw'
        blocks["raw"] = raw_text.strip()
        return blocks

    # The split puts matching headers at odd indices and bodies at even indices
    for i in range(1, len(splits), 2):
        header = splits[i].strip()
        body = splits[i + 1].strip() if (i + 1) < len(splits) else ""
        
        # Normalize header command name
        cmd_match = re.search(r"[#>]\s*(.+)$", header)
        cmd_key = cmd_match.group(1).strip().lower() if cmd_match else header.lower()
        blocks[cmd_key] = body

    # Also keep a raw fallback
    blocks["raw"] = raw_text.strip()
    return blocks


def parse_ip_interface_brief(text: str) -> List[Dict[str, str]]:
    """
    Parses 'show ip interface brief' table.
    Returns list of dicts: [{'interface': 'Gi0/0', 'ip': '192.168.1.1', 'status': 'up', 'protocol': 'up'}, ...]
    """
    interfaces = []
    lines = text.strip().splitlines()
    for line in lines:
        match = re.match(
            r"^([A-Za-z0-9\/\.\-]+)\s+([0-9\.]+|unassigned)\s+\w+\s+\w+\s+(up|down|administratively down)\s+(up|down)",
            line.strip(),
            re.IGNORECASE,
        )
        if match:
            interfaces.append({
                "interface": match.group(1),
                "ip": match.group(2),
                "status": match.group(3).lower(),
                "protocol": match.group(4).lower(),
                "raw_line": line.strip(),
            })
    return interfaces


def parse_vlan_brief(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Parses 'show vlan brief' table.
    Returns dict: {'1': {'name': 'default', 'status': 'active', 'ports': ['Fa0/1', 'Fa0/2']}, ...}
    """
    vlans: Dict[str, Dict[str, Any]] = {}
    lines = text.strip().splitlines()
    for line in lines:
        match = re.match(r"^(\d+)\s+([A-Za-z0-9_\-]+)\s+(active|act/unsup|suspend)\s*(.*)$", line.strip(), re.IGNORECASE)
        if match:
            vlan_id = match.group(1)
            name = match.group(2)
            status = match.group(3).lower()
            ports_raw = match.group(4)
            ports = [p.strip() for p in ports_raw.split(",") if p.strip()] if ports_raw else []
            vlans[vlan_id] = {
                "name": name,
                "status": status,
                "ports": ports,
            }
    return vlans


def parse_interfaces_trunk(text: str) -> List[Dict[str, Any]]:
    """
    Parses 'show interfaces trunk' output.
    Returns list of trunks: [{'port': 'Gi0/1', 'mode': 'on', 'native_vlan': '1', 'allowed_vlans': '10,30'}, ...]
    """
    trunks = []
    lines = text.strip().splitlines()
    
    # 1. Match Port Mode Status Native vlan
    port_matches = re.findall(r"^([A-Za-z0-9\/\.\-]+)\s+(\w+)\s+[\w\.\-]+\s+(\w+)\s+(\d+)", text, re.MULTILINE)
    
    # 2. Match Vlans allowed on trunk
    allowed_section = re.search(r"Port\s+Vlans allowed on trunk\s*\n((?:[A-Za-z0-9\/\.\-]+\s+[0-9,\-ALL]+\n?)+)", text, re.IGNORECASE)
    allowed_map = {}
    if allowed_section:
        for row in allowed_section.group(1).strip().splitlines():
            parts = row.split()
            if len(parts) >= 2:
                allowed_map[parts[0]] = parts[1]

    for port, mode, status, native_vlan in port_matches:
        trunks.append({
            "port": port,
            "mode": mode.lower(),
            "status": status.lower(),
            "native_vlan": native_vlan,
            "allowed_vlans": allowed_map.get(port, "ALL"),
        })
    return trunks


def parse_ip_routes(text: str) -> Dict[str, Any]:
    """
    Parses 'show ip route' output.
    Returns:
    {
      'gateway_of_last_resort': '203.0.113.1' or None,
      'routes': [{'type': 'S', 'prefix': '192.168.30.0/24', 'next_hop': '10.0.0.6'}, ...]
    }
    """
    result: Dict[str, Any] = {
        "gateway_of_last_resort": None,
        "routes": [],
    }

    # Gateway of last resort check
    gw_match = re.search(r"Gateway of last resort is\s+([0-9\.]+|not set)", text, re.IGNORECASE)
    if gw_match:
        val = gw_match.group(1)
        result["gateway_of_last_resort"] = None if "not set" in val.lower() else val

    # Routes list
    lines = text.strip().splitlines()
    for line in lines:
        line_clean = line.strip()
        # Static route: S 192.168.30.0/24 [1/0] via 10.0.0.6
        static_match = re.match(r"^S\s+([0-9\.\/]+)\s+(?:\[\d+\/\d+\]\s+via\s+([0-9\.]+)|is directly connected)", line_clean)
        if static_match:
            result["routes"].append({
                "type": "S",
                "prefix": static_match.group(1),
                "next_hop": static_match.group(2) if static_match.group(2) else "direct",
                "raw_line": line_clean,
            })
        # OSPF route: O 192.168.10.0/24 [110/2] via 10.0.0.2
        ospf_match = re.match(r"^O\s+([0-9\.\/]+)\s+\[\d+\/\d+\]\s+via\s+([0-9\.]+)", line_clean)
        if ospf_match:
            result["routes"].append({
                "type": "O",
                "prefix": ospf_match.group(1),
                "next_hop": ospf_match.group(2),
                "raw_line": line_clean,
            })

    return result


def parse_access_lists(text: str) -> List[Dict[str, Any]]:
    """
    Parses 'show access-lists' or 'show running-config | section access-list'.
    Returns list of ACL definitions and their ACE lines.
    """
    acls = []
    lines = text.strip().splitlines()
    current_acl = None

    for line in lines:
        line_clean = line.strip()
        acl_header = re.match(r"^(Standard|Extended)\s+IP\s+access\s+list\s+([A-Za-z0-9_\-]+)", line_clean, re.IGNORECASE)
        if acl_header:
            if current_acl:
                acls.append(current_acl)
            current_acl = {
                "type": acl_header.group(1).lower(),
                "name": acl_header.group(2),
                "rules": [],
            }
            continue

        std_match = re.match(r"^access-list\s+(\d+)\s+(permit|deny)\s+(.+)", line_clean, re.IGNORECASE)
        if std_match:
            num = std_match.group(1)
            action = std_match.group(2).lower()
            spec = std_match.group(3)
            acls.append({
                "type": "standard" if int(num) < 100 or (1300 <= int(num) <= 1999) else "extended",
                "name": num,
                "rules": [{"action": action, "spec": spec, "raw": line_clean}],
            })
            continue

        if current_acl:
            rule_match = re.match(r"^(?:\d+\s+)?(permit|deny)\s+(.+)", line_clean, re.IGNORECASE)
            if rule_match:
                current_acl["rules"].append({
                    "action": rule_match.group(1).lower(),
                    "spec": rule_match.group(2),
                    "raw": line_clean,
                })

    if current_acl:
        acls.append(current_acl)

    return acls


def parse_ipconfig(text: str) -> Dict[str, str]:
    """
    Parses PC 'ipconfig' or 'ipconfig /all' output.
    Returns: {'ip': '192.168.1.150', 'subnet_mask': '255.255.255.0', 'gateway': '192.168.1.1', 'dns': '10.0.0.35'}
    """
    data = {}
    ip_match = re.search(r"IP\s+Address[\.\s]+:\s*([0-9\.]+)", text, re.IGNORECASE)
    if ip_match:
        data["ip"] = ip_match.group(1)

    mask_match = re.search(r"Subnet\s+Mask[\.\s]+:\s*([0-9\.]+)", text, re.IGNORECASE)
    if mask_match:
        data["subnet_mask"] = mask_match.group(1)

    gw_match = re.search(r"Default\s+Gateway[\.\s]+:\s*([0-9\.]+)", text, re.IGNORECASE)
    if gw_match:
        data["gateway"] = gw_match.group(1)

    dns_match = re.search(r"DNS\s+Servers[\.\s]+:\s*([0-9\.]+)", text, re.IGNORECASE)
    if dns_match:
        data["dns"] = dns_match.group(1)

    return data
