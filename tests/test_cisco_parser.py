"""
NetSage AI - Cisco CLI Parser Tests
Verifies regex parsing of show commands, interfaces, VLANs, trunks, routes, ACLs, and client ipconfig.
"""

from src.utils.cisco_parser import (
    extract_command_blocks,
    parse_ip_interface_brief,
    parse_vlan_brief,
    parse_interfaces_trunk,
    parse_ip_routes,
    parse_access_lists,
    parse_ipconfig,
)


def test_extract_command_blocks():
    text = """
SW1# show vlan brief
VLAN Name Status Ports
1 default active Fa0/1

SW1# show interfaces trunk
Port Mode Status Native vlan
Gi0/1 on trunking 1
"""
    blocks = extract_command_blocks(text)
    assert len(blocks) >= 2
    assert "show vlan brief" in blocks
    assert "show interfaces trunk" in blocks
    assert "default" in blocks["show vlan brief"]


def test_parse_ip_interface_brief():
    text = """
Interface              IP-Address      OK? Method Status                Protocol
FastEthernet0/1        192.168.1.1     YES manual up                    up
GigabitEthernet0/0     10.0.0.1        YES manual up                    up
GigabitEthernet0/1     unassigned      YES unset  administratively down down
"""
    intfs = parse_ip_interface_brief(text)
    assert len(intfs) == 3
    assert intfs[0]["interface"] == "FastEthernet0/1"
    assert intfs[0]["ip"] == "192.168.1.1"
    assert intfs[0]["status"] == "up"
    assert intfs[2]["status"] == "administratively down"


def test_parse_vlan_brief():
    text = """
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/1, Fa0/3, Fa0/4
10   Finance                          active    Fa0/2
20   Sales                            active    
"""
    vlans = parse_vlan_brief(text)
    assert "1" in vlans
    assert "10" in vlans
    assert "20" in vlans
    assert vlans["10"]["name"] == "Finance"
    assert vlans["10"]["status"] == "active"
    assert "Fa0/2" in vlans["10"]["ports"]


def test_parse_interfaces_trunk():
    text = """
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      1

Port        Vlans allowed on trunk
Gi0/1       10,30
"""
    trunks = parse_interfaces_trunk(text)
    assert len(trunks) == 1
    assert trunks[0]["port"] == "Gi0/1"
    assert trunks[0]["native_vlan"] == "1"
    assert trunks[0]["allowed_vlans"] == "10,30"


def test_parse_ip_routes():
    text = """
Gateway of last resort is not set

C        10.1.1.0/24 is directly connected, GigabitEthernet0/0
S        192.168.30.0/24 [1/0] via 10.0.0.6
O        172.16.0.0/16 [110/2] via 10.0.0.2
"""
    result = parse_ip_routes(text)
    assert result["gateway_of_last_resort"] is None
    assert len(result["routes"]) == 2
    assert result["routes"][0]["prefix"] == "192.168.30.0/24"
    assert result["routes"][0]["next_hop"] == "10.0.0.6"
    assert result["routes"][1]["type"] == "O"


def test_parse_access_lists():
    text = """
Standard IP access list 10
    10 deny 10.0.0.5 (24 matches)
    20 permit any
Extended IP access list 110
    10 permit tcp 192.168.1.0 0.0.0.255 any eq 80
"""
    acls = parse_access_lists(text)
    assert len(acls) == 2
    assert acls[0]["type"] == "standard"
    assert acls[0]["name"] == "10"
    assert len(acls[0]["rules"]) == 2
    assert acls[1]["type"] == "extended"
    assert acls[1]["name"] == "110"


def test_parse_ipconfig():
    text = """
PC-1> ipconfig /all
FastEthernet0 Connection:
   IP Address......................: 192.168.1.150
   Subnet Mask.....................: 255.255.255.0
   Default Gateway.................: 192.168.1.1
   DNS Servers.....................: 10.0.0.35
"""
    parsed = parse_ipconfig(text)
    assert parsed["ip"] == "192.168.1.150"
    assert parsed["subnet_mask"] == "255.255.255.0"
    assert parsed["gateway"] == "192.168.1.1"
    assert parsed["dns"] == "10.0.0.35"
