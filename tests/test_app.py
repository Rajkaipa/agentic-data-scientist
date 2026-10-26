from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_FILE = Path(__file__).resolve().parents[1] / "src" / "agentic_data_scientist" / "app" / "main.py"


def test_package_imports():
    import agentic_data_scientist
    import agentic_data_scientist.app  # noqa: F401
    import agentic_data_scientist.config  # noqa: F401

    assert agentic_data_scientist.__version__


def test_installed_metadata_version_matches_package():
    from importlib.metadata import version

    import agentic_data_scientist

    assert version("agentic-data-scientist") == agentic_data_scientist.__version__


def test_app_runs_without_credentials():
    at = AppTest.from_file(str(APP_FILE), default_timeout=30).run()
    assert not at.exception
    assert at.title[0].value == "Agentic Data Scientist"
    subheaders = [s.value for s in at.subheader]
    assert {"Planned capabilities", "System status", "Roadmap"} <= set(subheaders)
    page_text = " ".join(m.value for m in at.markdown)
    assert "Not configured" in page_text
    assert "Connected" not in page_text
    # The setup-time port observation must not read as a live check.
    assert "does **not** check it live" in page_text
