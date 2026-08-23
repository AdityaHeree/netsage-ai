"""
NetSage AI - Configuration & Constants Management
Handles environment variables, paths, and core domain taxonomy.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "netsage.db"
SEED_CASES_PATH = DATA_DIR / "seed_cases.json"
SEED_RAI_PATH = DATA_DIR / "seed_responsible_ai.json"

# Load .env if present
load_dotenv(BASE_DIR / ".env")

# App Mode & Environment
NETSAGE_ENV = os.getenv("NETSAGE_ENV", "development")
NETSAGE_MODE = os.getenv("NETSAGE_MODE", "OFFLINE_MOCK").upper()  # 'OFFLINE_MOCK' or 'GEMINI_LIVE'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Default Gemini Model Name (for google-genai SDK)
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# Domain Categories (8 Required Networking Domains)
CATEGORIES = [
    "VLAN",
    "Gateway",
    "DHCP",
    "DNS",
    "Routing",
    "ACL",
    "NAT",
    "Wireless",
]

# Severity Classifications
SEVERITY_LEVELS = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

# OSI Layer Classifications
OSI_LAYERS = [
    "Layer 1 - Physical",
    "Layer 2 - Data Link",
    "Layer 3 - Network",
    "Layer 4 - Transport",
    "Layer 7 - Application",
]

# Human-in-the-Loop Review Decisions
REVIEW_DECISIONS = [
    "ACCEPTED",
    "EDITED",
    "REJECTED",
]

# Responsible AI Failure Taxonomy
FAILURE_CATEGORIES = [
    "Hallucination",
    "Incomplete Evidence",
    "Wrong OSI Layer",
    "Dangerous Fix Command",
    "Overconfidence",
]


def is_gemini_configured(api_key: str | None = None) -> bool:
    """
    Check if a valid Gemini API key is configured either in environment or passed in.
    """
    key = api_key or GEMINI_API_KEY
    return bool(key and key.strip() and key != "your_gemini_api_key_here")
