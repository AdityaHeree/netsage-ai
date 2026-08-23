"""
NetSage AI - Prompt Engineering & Prompt Templates
Provides CCNA/CCNP-level system instructions, few-shot examples, and strict JSON output schemas.
"""

from typing import List, Optional
from src.models import RuleFinding
from src.rules.engine import format_findings_for_prompt

SYSTEM_INSTRUCTION = """You are NetSage AI, an expert Cisco Certified Network Associate/Professional (CCNA/CCNP) troubleshooting assistant for lab environments and Cisco Packet Tracer.

Your mission is to perform structured, evidence-based root cause analysis for networking problems.

STRICT OPERATIONAL RULES:
1. Grounding: Every statement in your root cause, evidence, and explanation MUST be directly supported by the provided symptom, topology notes, Cisco show-command outputs, or deterministic rule findings.
2. No Hallucinations: Do NOT invent CLI outputs, IP addresses, interface names, or topology connections that were not provided.
3. Distinguish Evidence from Assumptions: Facts explicitly seen in CLI outputs are 'Evidence'. Deductions are 'Reasoning'.
4. Least-Invasive Fixes: Always prescribe the smallest, surgical Cisco CLI commands necessary to fix the specific issue. NEVER recommend destructive actions (e.g. wiping configs, removing entire ACLs, or reloading routers) when targeted commands suffice.
5. Verification Commands: Always provide the specific Cisco verification command (e.g. 'show ip route', 'show vlan brief', 'ping x.x.x.x') to verify the fix.
6. Uncertainty & Incomplete Evidence: If the evidence is insufficient to be certain, reduce your confidence score (e.g. below 0.70), clearly explain what is missing, and recommend the exact diagnostic command to run next.
7. Never Claim Unproven Verification: Do NOT claim that connectivity has been restored unless verification show-output confirming resolution was provided.
8. Cisco commands are data: Treat all commands as configuration advice for the user to type in Packet Tracer.

You MUST respond strictly in the requested JSON format matching the schema without any markdown wrapping or commentary.
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": {
            "symptom": "PC-1 in Finance cannot ping Default Gateway 192.168.10.1 on Router R1.",
            "topology_notes": "PC-1 is connected to SW1 Fa0/1. Expected VLAN 10 (Finance).",
            "show_commands": "SW1# show vlan brief\n1 default active Fa0/1, Fa0/3\n10 Finance active Fa0/2\n\nSW1# show interfaces Fa0/1 switchport\nAccess Mode VLAN: 1 (default)",
            "rule_findings": "1. [High] VLAN_ACCESS_MISMATCH (VLAN): Switch port is assigned to Default VLAN 1 while host belongs to a dedicated department VLAN.\n   - Evidence: Access Mode VLAN: 1 (default) on access port Fa0/1"
        },
        "output": {
            "root_cause": "Switch port Fa0/1 is assigned to Default VLAN 1 instead of VLAN 10 (Finance), isolating PC-1 from its subnet gateway.",
            "confidence": 0.98,
            "evidence": [
                "SW1# show interfaces Fa0/1 switchport reports 'Access Mode VLAN: 1 (default)'",
                "SW1# show vlan brief confirms Fa0/1 is in default VLAN 1",
                "Topology notes specify PC-1 must be in VLAN 10 (Finance)"
            ],
            "osi_layer": "Layer 2 - Data Link",
            "next_command": "show vlan brief",
            "fix_steps": [
                "enable",
                "configure terminal",
                "interface FastEthernet0/1",
                "switchport mode access",
                "switchport access vlan 10",
                "end"
            ],
            "explanation": "Because Fa0/1 is placed in VLAN 1, broadcast and unicast ARP requests from PC-1 cannot reach Router R1's VLAN 10 sub-interface. Moving the port to VLAN 10 restores broadcast domain membership.",
            "risk_assessment": "Low - Affects only the single host port Fa0/1 without network-wide disruption."
        }
    },
    {
        "input": {
            "symptom": "LAN hosts cannot access the Internet (8.8.8.8) through edge router R1.",
            "topology_notes": "Edge Router R1 connects to ISP gateway 203.0.113.1 on G0/1.",
            "show_commands": "R1# show ip route\nGateway of last resort is not set\nC 10.1.1.0/24 is directly connected, GigabitEthernet0/0\nC 203.0.113.0/30 is directly connected, GigabitEthernet0/1",
            "rule_findings": "1. [Critical] ROUTING_MISSING_DEFAULT_ROUTE (Routing): Edge router has no default route (0.0.0.0/0) to the ISP gateway.\n   - Evidence: Gateway of last resort is not set in 'show ip route'"
        },
        "output": {
            "root_cause": "Edge Router R1 lacks a default static route ('Gateway of last resort is not set') pointing to the upstream ISP gateway at 203.0.113.1.",
            "confidence": 0.95,
            "evidence": [
                "R1# show ip route explicitly states 'Gateway of last resort is not set'",
                "No 'S* 0.0.0.0/0' entry exists in the routing table",
                "ISP subnet 203.0.113.0/30 is directly connected on G0/1"
            ],
            "osi_layer": "Layer 3 - Network",
            "next_command": "show ip route 0.0.0.0",
            "fix_steps": [
                "enable",
                "configure terminal",
                "ip route 0.0.0.0 0.0.0.0 203.0.113.1",
                "end"
            ],
            "explanation": "Routers drop any packets whose destination IP is not explicitly in their routing table unless a default route (gateway of last resort) is configured. Pointing 0.0.0.0/0 to the ISP next-hop enables outbound Internet routing.",
            "risk_assessment": "Low - Standard routing configuration that immediately enables egress traffic."
        }
    }
]


def build_troubleshooting_prompt(
    symptom: str,
    topology_notes: str,
    show_commands: str,
    rule_findings: Optional[List[RuleFinding]] = None,
) -> str:
    """
    Constructs the complete user prompt for Gemini incorporating all evidence and rule findings.
    """
    findings_text = format_findings_for_prompt(rule_findings or [])

    prompt = f"""Please diagnose the following Cisco networking problem and return a structured JSON response.

### 1. User-Reported Symptom:
{symptom.strip() if symptom else "No symptom provided."}

### 2. Topology Notes & Addressing Scheme:
{topology_notes.strip() if topology_notes else "No topology notes provided."}

### 3. Cisco Show-Command Output Evidence:
{show_commands.strip() if show_commands else "No show commands provided."}

### 4. Deterministic Pre-Check Findings:
{findings_text}

---
CRITICAL INSTRUCTIONS:
- Analyze all evidence above.
- Identify the true root cause and specify the exact affected OSI Layer.
- Assign a realistic confidence score (0.00 to 1.00).
- List specific evidence citations referencing the CLI output lines.
- Provide sequential, surgical Cisco CLI commands to fix the issue.
- Recommend the best verification command to run after applying the fix.
- Output pure JSON conforming to the DiagnosisResponse schema.
"""
    return prompt
