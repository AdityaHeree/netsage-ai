"""
NetSage AI - Google Gemini AI Client & Unified Diagnostic Service
Integrates google-genai SDK with structured Pydantic response enforcement and offline fallback.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types
from pydantic import ValidationError

from src.config import (
    DEFAULT_GEMINI_MODEL,
    GEMINI_API_KEY,
    NETSAGE_MODE,
    is_gemini_configured,
)
from src.models import DiagnosisResponse, RuleFinding
from src.rules.engine import run_deterministic_checks
from src.ai.prompts import SYSTEM_INSTRUCTION, build_troubleshooting_prompt
from src.ai.mock_ai import generate_mock_diagnosis

logger = logging.getLogger(__name__)


def create_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """
    Instantiates a modern google-genai Client.
    API key is read from configuration or parameter and is never hardcoded.
    """
    key = api_key or GEMINI_API_KEY
    if not key or not key.strip() or key == "your_gemini_api_key_here":
        raise ValueError("No valid Gemini API key configured. Provide an API key or use OFFLINE_MOCK mode.")
    return genai.Client(api_key=key.strip())


def request_gemini_diagnosis(
    symptom: str,
    topology_notes: str,
    show_commands: str,
    rule_findings: Optional[List[RuleFinding]] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[DiagnosisResponse, str]:
    """
    Calls the Gemini API using structured JSON output and validates the response with Pydantic.
    Returns (DiagnosisResponse, raw_json_string).
    """
    client = create_gemini_client(api_key)
    prompt = build_troubleshooting_prompt(
        symptom=symptom,
        topology_notes=topology_notes,
        show_commands=show_commands,
        rule_findings=rule_findings,
    )
    target_model = model_name or DEFAULT_GEMINI_MODEL

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=DiagnosisResponse,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.2,
    )

    response = client.models.generate_content(
        model=target_model,
        contents=prompt,
        config=config,
    )

    raw_text = response.text or "{}"
    try:
        # Validate through Pydantic
        diagnosis = DiagnosisResponse.model_validate_json(raw_text)
        return diagnosis, raw_text
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(f"Gemini output failed validation: {e}. Raw response: {raw_text}")
        raise ValueError(f"Gemini structured output validation error: {e}") from e


def diagnose_case(
    symptom: str,
    topology_notes: str,
    show_commands: str,
    rule_findings: Optional[List[RuleFinding]] = None,
    mode: Optional[str] = None,
    api_key: Optional[str] = None,
    allow_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Unified AI Diagnostic Service Entrypoint.
    
    Workflow:
    1. Executes deterministic rules if not already provided.
    2. Determines execution mode (GEMINI_LIVE vs OFFLINE_MOCK).
    3. Invokes Gemini API or Offline Mock Engine.
    4. Handles errors and provides seamless fallback to OFFLINE_MOCK if Gemini is unreachable.
    5. Returns a structured dictionary containing DiagnosisResponse, mode_used, rule_findings, and raw_response.
    """
    # 1. Deterministic Rule Checking
    findings = rule_findings if rule_findings is not None else run_deterministic_checks(
        symptom=symptom,
        topology_notes=topology_notes,
        show_commands=show_commands,
    )

    # 2. Mode Resolution
    target_mode = (mode or NETSAGE_MODE).upper()
    has_key = is_gemini_configured(api_key)

    if target_mode == "GEMINI_LIVE" and has_key:
        try:
            diagnosis, raw_response = request_gemini_diagnosis(
                symptom=symptom,
                topology_notes=topology_notes,
                show_commands=show_commands,
                rule_findings=findings,
                api_key=api_key,
            )
            return {
                "diagnosis": diagnosis,
                "mode_used": "GEMINI_LIVE",
                "rule_findings": findings,
                "raw_response": raw_response,
                "error": None,
            }
        except Exception as e:
            logger.warning(f"Gemini API request failed: {e}")
            if not allow_fallback:
                raise

            # Graceful fallback to Mock AI
            mock_diagnosis = generate_mock_diagnosis(
                symptom=symptom,
                topology_notes=topology_notes,
                show_commands=show_commands,
                rule_findings=findings,
            )
            return {
                "diagnosis": mock_diagnosis,
                "mode_used": "OFFLINE_MOCK",
                "rule_findings": findings,
                "raw_response": mock_diagnosis.model_dump_json(indent=2),
                "error": f"Gemini request failed ({e}); safely fell back to Offline Mock Engine.",
            }

    # Default to OFFLINE_MOCK
    mock_diagnosis = generate_mock_diagnosis(
        symptom=symptom,
        topology_notes=topology_notes,
        show_commands=show_commands,
        rule_findings=findings,
    )
    return {
        "diagnosis": mock_diagnosis,
        "mode_used": "OFFLINE_MOCK",
        "rule_findings": findings,
        "raw_response": mock_diagnosis.model_dump_json(indent=2),
        "error": None if target_mode == "OFFLINE_MOCK" else "Gemini API key not configured; using Offline Mock Engine.",
    }
