"""
NetSage AI - SQLite Database Layer
Handles database initialization, parameterized queries, migrations, seed loading, and CRUD operations.
"""

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.config import (
    DB_PATH,
    SEED_CASES_PATH,
    SEED_RAI_PATH,
)


def get_db_connection(db_path: Optional[Union[Path, str]] = None) -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database with row factory and foreign keys enabled.
    """
    path = str(db_path or DB_PATH)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Union[Path, str]] = None) -> None:
    """
    Initialize SQLite schema with the 4 required tables:
    1. cases
    2. diagnoses
    3. reviews
    4. responsible_ai_logs
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Cases Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                symptom TEXT NOT NULL,
                topology_notes TEXT NOT NULL,
                show_commands TEXT NOT NULL,
                actual_root_cause TEXT,
                osi_layer TEXT,
                concept_tag TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 2. Diagnoses Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnoses (
                id TEXT PRIMARY KEY,
                case_id TEXT,
                symptom TEXT NOT NULL,
                show_commands TEXT NOT NULL,
                rule_findings_json TEXT,
                root_cause TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence_json TEXT NOT NULL,
                osi_layer TEXT NOT NULL,
                next_command TEXT NOT NULL,
                fix_steps_json TEXT NOT NULL,
                raw_ai_response TEXT,
                mode TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE SET NULL
            );
            """
        )

        # 3. Reviews Table (Human-in-the-Loop)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                diagnosis_id TEXT NOT NULL,
                case_id TEXT,
                decision TEXT NOT NULL,
                reviewer_name TEXT NOT NULL,
                human_notes TEXT,
                corrected_root_cause TEXT,
                corrected_fix_steps_json TEXT,
                agreement_score INTEGER DEFAULT 1,
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE SET NULL
            );
            """
        )

        # 4. Responsible AI Logs Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS responsible_ai_logs (
                id TEXT PRIMARY KEY,
                case_title TEXT NOT NULL,
                category TEXT NOT NULL,
                ai_root_cause TEXT NOT NULL,
                ai_confidence REAL NOT NULL,
                human_correction TEXT NOT NULL,
                failure_category TEXT NOT NULL,
                lesson_learned TEXT NOT NULL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        conn.commit()


def seed_db(db_path: Optional[Union[Path, str]] = None) -> Dict[str, int]:
    """
    Seed database from data/seed_cases.json and data/seed_responsible_ai.json.
    Idempotent: Uses INSERT OR IGNORE to prevent duplicate rows across app restarts.
    Returns count of items seeded.
    """
    init_db(db_path)
    seeded_counts = {"cases_seeded": 0, "rai_logs_seeded": 0}

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Seed Cases
        if SEED_CASES_PATH.exists():
            with open(SEED_CASES_PATH, "r", encoding="utf-8") as f:
                cases_data = json.load(f)

            for case in cases_data:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO cases (
                        id, title, category, severity, symptom,
                        topology_notes, show_commands, actual_root_cause,
                        osi_layer, concept_tag
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        case["id"],
                        case["title"],
                        case["category"],
                        case["severity"],
                        case["symptom"],
                        case["topology_notes"],
                        case["show_commands"],
                        case.get("actual_root_cause", ""),
                        case.get("osi_layer", "Layer 3 - Network"),
                        case.get("concept_tag", ""),
                    ),
                )
                if cursor.rowcount > 0:
                    seeded_counts["cases_seeded"] += 1

        # Seed Responsible AI Logs
        if SEED_RAI_PATH.exists():
            with open(SEED_RAI_PATH, "r", encoding="utf-8") as f:
                rai_data = json.load(f)

            for log in rai_data:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO responsible_ai_logs (
                        id, case_title, category, ai_root_cause,
                        ai_confidence, human_correction, failure_category, lesson_learned
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        log["id"],
                        log["case_title"],
                        log["category"],
                        log["ai_root_cause"],
                        float(log["ai_confidence"]),
                        log["human_correction"],
                        log["failure_category"],
                        log["lesson_learned"],
                    ),
                )
                if cursor.rowcount > 0:
                    seeded_counts["rai_logs_seeded"] += 1

        conn.commit()

    return seeded_counts


# ============================================================================
# Cases CRUD
# ============================================================================

def insert_case(case_data: Dict[str, Any], db_path: Optional[Union[Path, str]] = None) -> str:
    """Insert a new case or lab scenario."""
    case_id = case_data.get("id") or f"CASE-{uuid.uuid4().hex[:8].upper()}"
    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO cases (
                id, title, category, severity, symptom,
                topology_notes, show_commands, actual_root_cause,
                osi_layer, concept_tag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                case_data["title"],
                case_data["category"],
                case_data.get("severity", "Medium"),
                case_data["symptom"],
                case_data.get("topology_notes", ""),
                case_data["show_commands"],
                case_data.get("actual_root_cause", ""),
                case_data.get("osi_layer", "Layer 3 - Network"),
                case_data.get("concept_tag", ""),
            ),
        )
        conn.commit()
    return case_id


def get_all_cases(db_path: Optional[Union[Path, str]] = None) -> List[Dict[str, Any]]:
    """Retrieve all troubleshooting cases ordered by category and ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases ORDER BY category, id ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_case_by_id(case_id: str, db_path: Optional[Union[Path, str]] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a specific case by its unique ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_cases_by_category(category: str, db_path: Optional[Union[Path, str]] = None) -> List[Dict[str, Any]]:
    """Retrieve all cases matching a specific category (e.g. 'VLAN')."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE category = ? ORDER BY id ASC", (category,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def count_cases(db_path: Optional[Union[Path, str]] = None) -> int:
    """Return total number of cases in the database."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cases")
        return cursor.fetchone()[0]


# ============================================================================
# Diagnoses CRUD
# ============================================================================

def insert_diagnosis(diag_data: Dict[str, Any], db_path: Optional[Union[Path, str]] = None) -> str:
    """Insert an AI diagnosis session record."""
    diag_id = diag_data.get("id") or f"DIAG-{uuid.uuid4().hex[:8].upper()}"
    
    rule_findings_str = (
        json.dumps(diag_data.get("rule_findings_json", []))
        if not isinstance(diag_data.get("rule_findings_json"), str)
        else diag_data.get("rule_findings_json")
    )
    evidence_str = (
        json.dumps(diag_data.get("evidence_json", []))
        if not isinstance(diag_data.get("evidence_json"), str)
        else diag_data.get("evidence_json")
    )
    fix_steps_str = (
        json.dumps(diag_data.get("fix_steps_json", []))
        if not isinstance(diag_data.get("fix_steps_json"), str)
        else diag_data.get("fix_steps_json")
    )

    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO diagnoses (
                id, case_id, symptom, show_commands, rule_findings_json,
                root_cause, confidence, evidence_json, osi_layer,
                next_command, fix_steps_json, raw_ai_response, mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                diag_id,
                diag_data.get("case_id"),
                diag_data["symptom"],
                diag_data["show_commands"],
                rule_findings_str,
                diag_data["root_cause"],
                float(diag_data["confidence"]),
                evidence_str,
                diag_data["osi_layer"],
                diag_data["next_command"],
                fix_steps_str,
                diag_data.get("raw_ai_response", ""),
                diag_data.get("mode", "OFFLINE_MOCK"),
            ),
        )
        conn.commit()
    return diag_id


def get_diagnosis_by_id(diag_id: str, db_path: Optional[Union[Path, str]] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a diagnosis record by ID with parsed JSON fields."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM diagnoses WHERE id = ?", (diag_id,))
        row = cursor.fetchone()
        if not row:
            return None
        data = dict(row)
        data["rule_findings"] = json.loads(data["rule_findings_json"]) if data.get("rule_findings_json") else []
        data["evidence"] = json.loads(data["evidence_json"]) if data.get("evidence_json") else []
        data["fix_steps"] = json.loads(data["fix_steps_json"]) if data.get("fix_steps_json") else []
        return data


def get_recent_diagnoses(limit: int = 50, db_path: Optional[Union[Path, str]] = None) -> List[Dict[str, Any]]:
    """Retrieve recent diagnoses ordered by creation date."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM diagnoses ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            data = dict(row)
            data["evidence"] = json.loads(data["evidence_json"]) if data.get("evidence_json") else []
            data["fix_steps"] = json.loads(data["fix_steps_json"]) if data.get("fix_steps_json") else []
            results.append(data)
        return results


# ============================================================================
# Reviews CRUD (Human-in-the-Loop)
# ============================================================================

def insert_review(review_data: Dict[str, Any], db_path: Optional[Union[Path, str]] = None) -> str:
    """Insert a human review decision."""
    review_id = review_data.get("id") or f"REV-{uuid.uuid4().hex[:8].upper()}"
    
    corrected_fix_steps = review_data.get("corrected_fix_steps_json") or review_data.get("corrected_fix_steps")
    if corrected_fix_steps is not None and not isinstance(corrected_fix_steps, str):
        corrected_fix_steps_str = json.dumps(corrected_fix_steps)
    else:
        corrected_fix_steps_str = corrected_fix_steps

    decision = review_data["decision"].upper()
    agreement_score = 1 if decision == "ACCEPTED" else 0

    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO reviews (
                id, diagnosis_id, case_id, decision, reviewer_name,
                human_notes, corrected_root_cause, corrected_fix_steps_json,
                agreement_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                review_data["diagnosis_id"],
                review_data.get("case_id"),
                decision,
                review_data.get("reviewer_name", "Network Engineer"),
                review_data.get("human_notes", ""),
                review_data.get("corrected_root_cause"),
                corrected_fix_steps_str,
                agreement_score,
            ),
        )
        conn.commit()
    return review_id


def get_all_reviews(db_path: Optional[Union[Path, str]] = None) -> List[Dict[str, Any]]:
    """Retrieve all human reviews with diagnosis references."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.*, d.root_cause as ai_root_cause, d.confidence as ai_confidence, d.osi_layer
            FROM reviews r
            LEFT JOIN diagnoses d ON r.diagnosis_id = d.id
            ORDER BY r.reviewed_at DESC
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_reviews_by_case(case_id: str, db_path: Optional[Union[Path, str]] = None) -> List[Dict[str, Any]]:
    """Retrieve reviews associated with a specific case."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reviews WHERE case_id = ? ORDER BY reviewed_at DESC", (case_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ============================================================================
# Responsible AI Logs CRUD
# ============================================================================

def insert_responsible_ai_log(log_data: Dict[str, Any], db_path: Optional[Union[Path, str]] = None) -> str:
    """Insert a Responsible AI calibration / error log."""
    log_id = log_data.get("id") or f"RAI-{uuid.uuid4().hex[:8].upper()}"
    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO responsible_ai_logs (
                id, case_title, category, ai_root_cause,
                ai_confidence, human_correction, failure_category, lesson_learned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                log_data["case_title"],
                log_data["category"],
                log_data["ai_root_cause"],
                float(log_data["ai_confidence"]),
                log_data["human_correction"],
                log_data["failure_category"],
                log_data["lesson_learned"],
            ),
        )
        conn.commit()
    return log_id


def get_all_responsible_ai_logs(db_path: Optional[Union[Path, str]] = None) -> List[Dict[str, Any]]:
    """Retrieve all Responsible AI case studies and error logs."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM responsible_ai_logs ORDER BY id ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def count_responsible_ai_logs(db_path: Optional[Union[Path, str]] = None) -> int:
    """Return total number of Responsible AI logs."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM responsible_ai_logs")
        return cursor.fetchone()[0]


def count_diagnoses(db_path: Optional[Union[Path, str]] = None) -> int:
    """Return total number of AI diagnoses in the database."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM diagnoses")
        return cursor.fetchone()[0]


def count_reviews(db_path: Optional[Union[Path, str]] = None) -> int:
    """Return total number of human reviews in the database."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reviews")
        return cursor.fetchone()[0]


def reset_db(db_path: Optional[Union[Path, str]] = None) -> Dict[str, int]:
    """
    Destructively drops all tables and re-initializes and re-seeds from JSON seed files.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS reviews;")
        cursor.execute("DROP TABLE IF EXISTS diagnoses;")
        cursor.execute("DROP TABLE IF EXISTS cases;")
        cursor.execute("DROP TABLE IF EXISTS responsible_ai_logs;")
        conn.commit()
    return seed_db(db_path)


def get_analytics_summary(db_path: Optional[Union[Path, str]] = None) -> Dict[str, Any]:
    """
    Computes real-time analytics for the Dashboard.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        total_cases = cursor.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        total_diagnoses = cursor.execute("SELECT COUNT(*) FROM diagnoses").fetchone()[0]
        total_reviews = cursor.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        pending_reviews = max(0, total_diagnoses - total_reviews)

        # AI-Human Agreement Rate
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_reviewed,
                SUM(agreement_score) as agreed_count,
                AVG(agreement_score) * 100 as agreement_rate
            FROM reviews
            """
        )
        agreement_row = cursor.fetchone()
        agreement_rate = round(agreement_row["agreement_rate"], 1) if agreement_row and agreement_row["agreement_rate"] is not None else 0.0

        # Average AI Confidence
        cursor.execute("SELECT AVG(confidence) * 100 as avg_conf FROM diagnoses")
        conf_row = cursor.fetchone()
        avg_confidence = round(conf_row["avg_conf"], 1) if conf_row and conf_row["avg_conf"] is not None else 0.0

        # Category Breakdown
        cursor.execute("SELECT category, COUNT(*) as count FROM cases GROUP BY category ORDER BY count DESC")
        category_counts = [dict(r) for r in cursor.fetchall()]

        # Severity Breakdown
        cursor.execute("SELECT severity, COUNT(*) as count FROM cases GROUP BY severity ORDER BY count DESC")
        severity_counts = [dict(r) for r in cursor.fetchall()]

        # Decisions Breakdown
        cursor.execute("SELECT decision, COUNT(*) as count FROM reviews GROUP BY decision")
        decision_counts = [dict(r) for r in cursor.fetchall()]

        # OSI Layer Breakdown
        cursor.execute("SELECT osi_layer, COUNT(*) as count FROM cases WHERE osi_layer IS NOT NULL GROUP BY osi_layer")
        osi_counts = [dict(r) for r in cursor.fetchall()]

        return {
            "total_cases": total_cases,
            "total_diagnoses": total_diagnoses,
            "total_reviews": total_reviews,
            "pending_reviews": pending_reviews,
            "agreement_rate": agreement_rate,
            "avg_confidence": avg_confidence,
            "category_counts": category_counts,
            "severity_counts": severity_counts,
            "decision_counts": decision_counts,
            "osi_counts": osi_counts,
        }

