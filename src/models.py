"""
NetSage AI - Data Models & Schemas
Typed Pydantic schemas for data integrity across UI, AI, and Database layers.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class RuleFinding(BaseModel):
    """Represents an anomaly or observation found by deterministic rule checks."""
    rule_name: str = Field(description="Unique rule identifier (e.g. VLAN_ACCESS_MISMATCH)")
    category: str = Field(description="Networking category (e.g. VLAN, Gateway, DHCP)")
    severity: str = Field(default="Medium", description="Severity: Low, Medium, High, Critical")
    message: str = Field(description="Human-readable explanation of the detected anomaly")
    matched_evidence: List[str] = Field(default_factory=list, description="Specific CLI lines matching the rule")
    recommendation: Optional[str] = Field(default=None, description="Suggested configuration fix or next step")


class DiagnosisResponse(BaseModel):
    """Structured AI output schema enforced for Gemini and Mock AI."""
    root_cause: str = Field(
        description="Clear, precise explanation of why the network issue is occurring"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Diagnostic confidence score between 0.00 and 1.00"
    )
    evidence: List[str] = Field(
        description="Specific CLI show command lines or symptoms supporting this diagnosis"
    )
    osi_layer: str = Field(
        description="OSI Layer affected, e.g. Layer 2 - Data Link, Layer 3 - Network"
    )
    next_command: str = Field(
        description="Recommended diagnostic or verification Cisco command"
    )
    fix_steps: List[str] = Field(
        description="Step-by-step Cisco CLI commands to resolve the issue"
    )
    explanation: str = Field(
        description="Detailed technical reasoning behind the diagnosis"
    )
    risk_assessment: str = Field(
        default="Low",
        description="Risk level of applying the fix (Low, Medium, High)"
    )


class Case(BaseModel):
    """Troubleshooting scenario case model."""
    id: str = Field(description="Unique Case ID (e.g. CASE-VLAN-01)")
    title: str = Field(description="Descriptive title of the lab scenario")
    category: str = Field(description="Networking domain (e.g. VLAN, Routing, ACL)")
    severity: str = Field(default="Medium", description="Severity level: Low, Medium, High, Critical")
    symptom: str = Field(description="User-reported symptom description")
    topology_notes: str = Field(description="Brief topology and IP addressing scheme notes")
    show_commands: str = Field(description="Raw Cisco CLI show commands output")
    actual_root_cause: Optional[str] = Field(default=None, description="Ground truth answer for evaluation")
    osi_layer: Optional[str] = Field(default="Layer 3 - Network", description="Primary OSI layer of the issue")
    concept_tag: Optional[str] = Field(default=None, description="Key networking concept tag")
    created_at: Optional[str] = Field(default=None, description="Timestamp of case creation")


class Review(BaseModel):
    """Human-in-the-Loop review decision."""
    id: str = Field(description="Unique Review ID")
    diagnosis_id: str = Field(description="Associated diagnosis record ID")
    case_id: Optional[str] = Field(default=None, description="Associated case ID if applicable")
    decision: str = Field(description="Review decision: ACCEPTED, EDITED, or REJECTED")
    reviewer_name: str = Field(default="Network Engineer", description="Name/Role of reviewer")
    human_notes: Optional[str] = Field(default="", description="Reviewer feedback/observations")
    corrected_root_cause: Optional[str] = Field(default=None, description="Human corrected root cause if edited/rejected")
    corrected_fix_steps: Optional[List[str]] = Field(default=None, description="Human corrected CLI fix commands")
    agreement_score: int = Field(default=1, description="1 if ACCEPTED, 0 if EDITED or REJECTED")
    reviewed_at: Optional[str] = Field(default=None, description="Timestamp of review submission")


class ResponsibleAILog(BaseModel):
    """Audit log entry capturing AI misdiagnoses and human corrections."""
    id: str = Field(description="Unique Log ID (e.g. RAI-01)")
    case_title: str = Field(description="Title of the scenario")
    category: str = Field(description="Networking category")
    ai_root_cause: str = Field(description="What the AI originally diagnosed")
    ai_confidence: float = Field(description="AI confidence score at time of diagnosis")
    human_correction: str = Field(description="Human network engineer's corrected ground truth")
    failure_category: str = Field(description="Type of failure (e.g. Hallucination, Incomplete Evidence)")
    lesson_learned: str = Field(description="Key takeaway and guardrail recommendation")
    logged_at: Optional[str] = Field(default=None, description="Timestamp of the correction log")
