from pathlib import Path

from agentic_data_scientist.config import load_settings
from agentic_data_scientist.config.settings import DB_ENV_VARS, load_database_settings

FULL_ENV = {
    "ADS_DB_HOST": "localhost",
    "ADS_DB_PORT": "5433",
    "ADS_DB_NAME": "ads",
    "ADS_DB_USER": "ads_app",
    "ADS_DB_PASSWORD": "s3cret-value",
}


def test_empty_environment_is_valid_and_unconfigured(tmp_path: Path):
    settings = load_settings(env={}, env_file=tmp_path / ".env")
    assert settings.env_file_found is False
    assert settings.database.is_configured is False
    assert settings.database.is_partially_configured is False
    assert settings.database.errors == ()
    assert settings.database.missing_fields == list(DB_ENV_VARS.values())


def test_complete_environment_is_configured():
    db = load_database_settings(FULL_ENV)
    assert db.is_configured
    assert db.port == 5433
    assert db.missing_fields == []


def test_partial_environment_reports_missing_fields():
    db = load_database_settings({"ADS_DB_HOST": "localhost", "ADS_DB_PORT": "5433"})
    assert db.is_partially_configured
    assert set(db.missing_fields) == {"ADS_DB_NAME", "ADS_DB_USER", "ADS_DB_PASSWORD"}


def test_blank_values_count_as_missing():
    db = load_database_settings({**FULL_ENV, "ADS_DB_USER": "   "})
    assert not db.is_configured
    assert db.missing_fields == ["ADS_DB_USER"]


def test_invalid_port_is_reported_not_raised():
    for bad in ("abc", "0", "70000"):
        db = load_database_settings({**FULL_ENV, "ADS_DB_PORT": bad})
        assert not db.is_configured
        assert db.errors and "ADS_DB_PORT" in db.errors[0]


def test_password_is_not_in_repr():
    db = load_database_settings(FULL_ENV)
    assert "s3cret-value" not in repr(db)
    assert "s3cret-value" not in repr(load_settings(env=FULL_ENV))


def test_env_file_detection(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("ADS_DB_HOST=localhost\n", encoding="utf-8")
    assert load_settings(env={}, env_file=env_file).env_file_found is True


def test_env_example_contains_no_values_for_secrets():
    example = Path(__file__).resolve().parents[1] / ".env.example"
    lines = [
        line for line in example.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    values = dict(line.split("=", 1) for line in lines)
    assert set(DB_ENV_VARS.values()) <= values.keys()
    assert values["ADS_DB_PASSWORD"] == ""
    assert values["ADS_DB_USER"] == ""
