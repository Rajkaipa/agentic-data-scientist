"""Verifiable system status checks shown in the UI.

Every check here reports something the process can observe directly
(interpreter version, installed package metadata, presence of settings).
Nothing here opens network or database connections.
"""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from importlib import metadata

from agentic_data_scientist.config import Settings

MIN_PYTHON = (3, 11)

# Distribution names grouped as in pyproject.toml. "core" is required now;
# the other groups are optional extras for later phases.
DEPENDENCY_GROUPS: dict[str, tuple[str, ...]] = {
    "core": ("streamlit", "python-dotenv"),
    "dev": ("pytest",),
    "data": ("pandas", "numpy", "pyarrow", "openpyxl", "duckdb", "plotly"),
    "db": ("sqlalchemy", "psycopg"),
    "agents": ("langgraph", "langchain-core"),
    "ml": ("scikit-learn", "xgboost", "catboost", "mlflow"),
}


@dataclass(frozen=True)
class PackageStatus:
    name: str
    version: str | None

    @property
    def installed(self) -> bool:
        return self.version is not None


def package_status(name: str) -> PackageStatus:
    try:
        return PackageStatus(name, metadata.version(name))
    except metadata.PackageNotFoundError:
        return PackageStatus(name, None)


def dependency_report() -> dict[str, list[PackageStatus]]:
    return {
        group: [package_status(name) for name in names]
        for group, names in DEPENDENCY_GROUPS.items()
    }


def python_version() -> str:
    return platform.python_version()


def python_is_supported(version_info: tuple[int, ...] = tuple(sys.version_info)) -> bool:
    return tuple(version_info[:2]) >= MIN_PYTHON


def database_config_summary(settings: Settings) -> tuple[str, str]:
    """Return a (state, message) pair describing database configuration only.

    State is one of "not_configured", "incomplete", "invalid" or "configured".
    Connectivity is never implied: no connection is attempted in Phase 1.
    """
    db = settings.database
    if db.errors:
        return "invalid", " ".join(db.errors)
    if db.is_configured:
        return (
            "configured",
            f"Settings present for {db.user}@{db.host}:{db.port}/{db.database}. "
            f"Port {db.port} is configured, not verified: no connectivity check runs in Phase 1.",
        )
    if db.is_partially_configured:
        return "incomplete", "Missing: " + ", ".join(db.missing_fields)
    return "not_configured", "Optional. No ADS_DB_* settings found."
