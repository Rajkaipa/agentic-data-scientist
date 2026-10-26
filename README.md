# agentic-data-scientist

A collaborative multi-agent data science and AI business intelligence platform with human-in-the-loop workflows.

Specialised agents will import and assess data, explore it, propose features and models, and challenge each other's results. People approve feature transformations and model training before anything runs.

> **Current status: Phase 1 (foundation), in review.** Only the Overview page, configuration loading and verified status checks are implemented. Agents, data import, approval workflows and database integration are **planned, not built**.

## What works today

- A Streamlit app, **Agentic Data Scientist**, with an Overview page that shows:
  - planned capabilities and a roadmap
  - a **system status** section reporting only what the app can verify: Python version, installed dependencies, whether a `.env` file exists, and whether the optional database settings are present and valid
- The app needs no API keys and no database credentials. Database settings are optional and are never connection-tested in Phase 1, so the app never displays "connected".
- A pytest suite covers configuration, status checks, version metadata and a headless render of the app.

## Prerequisites

- Windows with PowerShell
- Python 3.11 or newer (developed on 3.11.3)
- Git
- Optional, for later phases: PostgreSQL 17 and DBeaver. On the development machine, PostgreSQL was observed on **port 5433** during the Phase 1 inspection; check your own server's port.

## Setup (Windows PowerShell)

```powershell
# From the folder you want the project in:
git clone https://github.com/Rajkaipa/agentic-data-scientist.git
cd agentic-data-scientist

# Create the virtual environment (skip if .venv already exists)
python -m venv .venv

# Activate it. If scripts are blocked, allow them for this terminal session only:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

# Install the project (editable) plus test tools
python -m pip install -r requirements.txt

# Optional: local settings (all values are optional in Phase 1)
Copy-Item .env.example .env
```

`requirements.txt` installs the package defined in `pyproject.toml` together with its `dev` extra.

- **Runtime dependencies:** `streamlit` and `python-dotenv`.
- **Test dependency:** `pytest`.
- **Optional groups for later phases:** `data`, `db`, `agents` and `ml`. Install one only when a milestone needs it, for example `pip install -e ".[data]"`.

VS Code is configured in `.vscode/settings.json` to use `.venv\Scripts\python.exe` and to run pytest.

## Run the app

```powershell
streamlit run src/agentic_data_scientist/app/main.py
```

Then open http://localhost:8501.

## Run the tests

```powershell
python -m pytest
```

Check the summary line pytest prints (for example `N passed`). Any failure or error means the setup is not working.

## Project layout

```
CLAUDE.md                      Engineering rules for Claude Code and contributors
pyproject.toml                 Package metadata, dependencies and optional groups
requirements.txt               Phase 1 install (-e .[dev])
.env.example                   Placeholder settings (copy to .env; never commit .env)
.streamlit/config.toml         Streamlit options (usage statistics off)
src/agentic_data_scientist/
  app/main.py                  Streamlit entry point (Overview page)
  config/settings.py           Typed, optional settings from the environment or .env
  system_status.py             Verifiable status checks (no network or database calls)
tests/                         pytest suite
docs/postgres-mcp-integration.md   PostgreSQL / DBeaver / MCP plan
data/                          Local data (git-ignored except .gitkeep)
```

The `data/`, `db/`, `memory/`, `agents/`, `graph/` and `tools/` packages are added in the phase where each first gets real code. `CLAUDE.md` describes what each one is responsible for.

## Configuration

All configuration is optional in Phase 1.

| Variable | Purpose |
|---|---|
| `ADS_DB_HOST`, `ADS_DB_PORT`, `ADS_DB_NAME`, `ADS_DB_USER`, `ADS_DB_PASSWORD` | The app's own PostgreSQL connection, used from Phase 2. `.env.example` suggests port `5433`, the port observed during setup. A configured port is not verified until Phase 2 adds a real connection check. |

When settings are missing, incomplete or invalid (for example a non-numeric port), the status page reports it and the app keeps running.

## PostgreSQL and MCP: current status

| Item | Status |
|---|---|
| PostgreSQL 17.4 service | Observed running and accepting connections on `localhost:5433` (`pg_isready`) at the Phase 1 inspection on 2026-10-26. The app does not re-check this. |
| Database login or test query | **Not done**: no credentials have been used |
| Read-only role for MCP | **Designed, not created** (`ads_owner` / `ads_mcp_readonly` SQL in the docs) |
| PostgreSQL MCP server | **Not installed or configured**. MCP Toolbox for Databases is recommended, with Postgres MCP Pro as the fallback. |
| App connection through SQLAlchemy | Planned for Phase 2 |

DBeaver, the MCP server and the app are planned as independent clients of the same PostgreSQL instance, each with its own role. See [docs/postgres-mcp-integration.md](docs/postgres-mcp-integration.md).

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Project foundation, configuration, status page, tests | In review |
| 2 | Data Hub: file and PostgreSQL ingestion, persistent project metadata | Planned |
| 3 | Data quality assessment and EDA with Plotly | Planned |
| 4 | LangGraph orchestration, structured agent messages, approval checkpoints | Planned |
| 5 | Feature Engineering Agent and Data Scientist Lab | Planned |
| 6 | Critic/Evaluator and AI Business Analyst | Planned |
| 7 | Agent Activity audit view, MLflow tracking, hardening | Planned |

## License

MIT. See [LICENSE](LICENSE).
