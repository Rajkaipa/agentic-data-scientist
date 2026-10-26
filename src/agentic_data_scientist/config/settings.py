"""Typed settings for the application.

All settings are optional in Phase 1: the app must start with no `.env` file,
no API keys and no database credentials. Values are read from a mapping
(normally ``os.environ``) so tests can supply their own environment.

The application's own database connection uses the ``ADS_DB_*`` variables.
These are deliberately distinct from any variables used to configure an MCP
server, which connects to PostgreSQL independently with its own role.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_ENV_VARS = {
    "host": "ADS_DB_HOST",
    "port": "ADS_DB_PORT",
    "database": "ADS_DB_NAME",
    "user": "ADS_DB_USER",
    "password": "ADS_DB_PASSWORD",
}


@dataclass(frozen=True)
class DatabaseSettings:
    """Optional PostgreSQL settings for the application's direct connection."""

    host: str | None = None
    port: int | None = None
    database: str | None = None
    user: str | None = None
    # Excluded from repr so the password never appears in logs or tracebacks.
    password: str | None = field(default=None, repr=False)
    errors: tuple[str, ...] = ()

    @property
    def missing_fields(self) -> list[str]:
        return [
            DB_ENV_VARS[name]
            for name in DB_ENV_VARS
            if getattr(self, name) in (None, "")
        ]

    @property
    def is_configured(self) -> bool:
        """True when every field is present and valid. Says nothing about connectivity."""
        return not self.missing_fields and not self.errors

    @property
    def is_partially_configured(self) -> bool:
        return not self.is_configured and len(self.missing_fields) < len(DB_ENV_VARS)


@dataclass(frozen=True)
class Settings:
    env_file: Path
    env_file_found: bool
    database: DatabaseSettings


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _parse_port(raw: str | None) -> tuple[int | None, str | None]:
    if raw is None:
        return None, None
    try:
        port = int(raw)
    except ValueError:
        return None, f"{DB_ENV_VARS['port']} must be an integer."
    if not 1 <= port <= 65535:
        return None, f"{DB_ENV_VARS['port']} must be between 1 and 65535."
    return port, None


def load_database_settings(env: Mapping[str, str]) -> DatabaseSettings:
    port, port_error = _parse_port(_clean(env.get(DB_ENV_VARS["port"])))
    return DatabaseSettings(
        host=_clean(env.get(DB_ENV_VARS["host"])),
        port=port,
        database=_clean(env.get(DB_ENV_VARS["database"])),
        user=_clean(env.get(DB_ENV_VARS["user"])),
        password=env.get(DB_ENV_VARS["password"]) or None,
        errors=(port_error,) if port_error else (),
    )


def load_dotenv_file(env_file: Path | None = None) -> bool:
    """Load a ``.env`` file into ``os.environ`` without overriding existing variables."""
    env_file = env_file or PROJECT_ROOT / ".env"
    if not env_file.is_file():
        return False
    load_dotenv(env_file, override=False)
    return True


def load_settings(
    env: Mapping[str, str] | None = None, env_file: Path | None = None
) -> Settings:
    env_file = env_file or PROJECT_ROOT / ".env"
    return Settings(
        env_file=env_file,
        env_file_found=env_file.is_file(),
        database=load_database_settings(os.environ if env is None else env),
    )
