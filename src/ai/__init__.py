"""
NetSage AI - AI Integration & Prompt Engineering Package
"""

from src.ai.gemini_client import (
    diagnose_case,
    create_gemini_client,
    request_gemini_diagnosis,
)
from src.ai.mock_ai import generate_mock_diagnosis
from src.ai.prompts import (
    SYSTEM_INSTRUCTION,
    FEW_SHOT_EXAMPLES,
    build_troubleshooting_prompt,
)

__all__ = [
    "diagnose_case",
    "create_gemini_client",
    "request_gemini_diagnosis",
    "generate_mock_diagnosis",
    "SYSTEM_INSTRUCTION",
    "FEW_SHOT_EXAMPLES",
    "build_troubleshooting_prompt",
]
