from pathlib import Path

from agentic_data_scientist.config import load_settings
from agentic_data_scientist.system_status import (
    database_config_summary,
    dependency_report,
    package_status,
    python_is_supported,
)


def test_core_dependencies_are_installed():
    report = dependency_report()
    assert all(pkg.installed for pkg in report["core"] + report["dev"])


def test_missing_package_reports_not_installed():
    status = package_status("definitely-not-a-real-package-xyz")
    assert status.installed is False
    assert status.version is None


def test_python_version_check():
    assert python_is_supported()
    assert python_is_supported((3, 11, 0))
    assert not python_is_supported((3, 10, 12))


def test_database_summary_states(tmp_path: Path):
    env_file = tmp_path / ".env"

    def state(env):
        return database_config_summary(load_settings(env=env, env_file=env_file))

    assert state({})[0] == "not_configured"
    assert state({"ADS_DB_HOST": "localhost"})[0] == "incomplete"
    assert state({"ADS_DB_PORT": "x"})[0] == "invalid"

    full = {
        "ADS_DB_HOST": "localhost", "ADS_DB_PORT": "5433", "ADS_DB_NAME": "ads",
        "ADS_DB_USER": "u", "ADS_DB_PASSWORD": "pw-should-not-show",
    }
    configured_state, message = state(full)
    assert configured_state == "configured"
    assert "not verified" in message.lower()
    assert "pw-should-not-show" not in message
