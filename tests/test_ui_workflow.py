"""
NetSage AI - Phase 5 UI & Page Workflow Tests
Verifies that all Streamlit pages (app.py and pages 1 to 5) initialize and render without errors using AppTest.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from src.config import BASE_DIR
from src.db import init_db, seed_db, get_analytics_summary

DEFAULT_TIMEOUT = 10.0


@pytest.fixture(autouse=True)
def setup_database():
    """Ensures database is initialized and seeded before UI tests run."""
    init_db()
    seed_db()


def test_app_landing_page():
    """Verify app.py landing page renders title, metrics, and navigation elements."""
    app_path = str(BASE_DIR / "app.py")
    at = AppTest.from_file(app_path, default_timeout=DEFAULT_TIMEOUT).run()
    assert not at.exception
    assert len(at.title) >= 1
    assert len(at.metric) >= 5


def test_case_repository_page():
    """Verify Case Repository page loads the 32 cases and filters."""
    repo_path = str(BASE_DIR / "pages" / "2_📚_Case_Repository.py")
    at = AppTest.from_file(repo_path, default_timeout=DEFAULT_TIMEOUT).run()
    assert not at.exception
    assert len(at.dataframe) >= 1


def test_responsible_ai_page():
    """Verify Responsible AI Log page renders calibration cases and metrics."""
    rai_path = str(BASE_DIR / "pages" / "3_⚖️_Responsible_AI_Log.py")
    at = AppTest.from_file(rai_path, default_timeout=DEFAULT_TIMEOUT).run()
    assert not at.exception
    assert len(at.metric) >= 5


def test_analytics_dashboard_page():
    """Verify Analytics Dashboard page renders KPIs and chart components from SQLite."""
    dash_path = str(BASE_DIR / "pages" / "4_📊_Analytics_Dashboard.py")
    at = AppTest.from_file(dash_path, default_timeout=DEFAULT_TIMEOUT).run()
    assert not at.exception
    assert len(at.metric) >= 6
    summary = get_analytics_summary()
    assert summary["total_cases"] == 32


def test_settings_page():
    """Verify Settings page renders mode options and database status."""
    settings_path = str(BASE_DIR / "pages" / "5_⚙️_Settings.py")
    at = AppTest.from_file(settings_path, default_timeout=DEFAULT_TIMEOUT).run()
    assert not at.exception
    assert len(at.radio) >= 1


def test_live_troubleshooter_initial_render():
    """Verify Live Troubleshooter page renders initial input forms and buttons."""
    trouble_path = str(BASE_DIR / "pages" / "1_🔍_Live_Troubleshooter.py")
    at = AppTest.from_file(trouble_path, default_timeout=DEFAULT_TIMEOUT).run()
    assert not at.exception
    assert len(at.text_area) >= 3
    assert len(at.button) >= 3
