import pytest

from agentic_data_scientist.config import settings as settings_module


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    """Keep the developer's real .env and ADS_DB_* shell variables out of tests."""
    for var in settings_module.DB_ENV_VARS.values():
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(settings_module, "PROJECT_ROOT", tmp_path)
