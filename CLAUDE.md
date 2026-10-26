# CLAUDE.md: Agentic Data Scientist

## Objective
A collaborative multi-agent data science and BI platform with human-in-the-loop
workflows. Specialised agents (Data Access, Data Quality, EDA, Feature Engineering,
Data Scientist, Critic/Evaluator, Business Analyst) exchange structured messages. A
LangGraph orchestrator routes the work, and people approve the steps that matter.
The project is built in phases, and the current phase is recorded in `README.md`.
Do not start a new phase without the user's approval.

## Environment
- Windows, PowerShell, VS Code, Python 3.11 (pyenv-win), project venv at `.venv`.
- Local PostgreSQL 17 was observed on **port 5433** during the Phase 1 inspection.
  Treat it as configuration, not as verified connectivity. See `docs/postgres-mcp-integration.md`.
- Run the app: `streamlit run src/agentic_data_scientist/app/main.py`
- Run the tests: `python -m pytest`

## Layout (`src/agentic_data_scientist/`)
| Path | Responsibility | Status |
|---|---|---|
| `app/` | Streamlit UI only: layout, widgets, calls into other layers | exists |
| `config/` | Typed settings from env/`.env`; no I/O beyond reading env | exists |
| `system_status.py` | Verifiable status checks (no network/DB calls) | exists |
| `data/` | Ingestion and processing (pandas/DuckDB/PyArrow) | planned |
| `db/` | SQLAlchemy engine, repositories for metadata, messages, approvals | planned |
| `memory/` | Durable project memory (Postgres), separate from conversation context | planned |
| `agents/` | Agent logic; each agent returns structured proposals or findings | planned |
| `graph/` | LangGraph state, routing, checkpoints, approval gates, revision loops | planned |
| `tools/` | Deterministic tools used by agents (stats, transforms, training) | planned |

Create a planned package only when its first real module is written, never
as an empty placeholder. UI code must not contain business, agent or database
logic.

## Coding and testing conventions
- Use type hints, small pure functions and frozen dataclasses (or Pydantic once
  added) for structured data.
- Settings functions accept an `env` mapping so they can be tested without
  touching `os.environ`.
- Every module with logic gets pytest tests in `tests/`. Tests must run with no
  `.env`, no credentials and no network. `tests/conftest.py` isolates `.env` and
  the `ADS_DB_*` variables.
- Test Streamlit pages with `streamlit.testing.v1.AppTest`.
- A change is not done until `python -m pytest` passes and the real output has
  been checked.

## Dependency management
- `pyproject.toml` is the single source of dependencies:
  - Runtime packages go in `[project.dependencies]`.
  - Later-phase packages go in the optional extras (`data`, `db`, `agents`, `ml`).
  - Test tools go in `dev`.
- `requirements.txt` is just `-e .[dev]`.
- Add a package only when the current milestone uses it. Prefer lower bounds that
  match an API we actually rely on. Avoid exact pins unless something forces them.
- Never install into the global Python. Ask before installing anything new.

## Security and credentials
- Secrets live only in `.env` (git-ignored) or in user environment variables.
  `.env.example` holds placeholders only.
- Never print, log or commit passwords, connection strings containing passwords,
  or API keys. `DatabaseSettings.password` is excluded from `repr`.
- Check `git status` and `git diff` for secrets before every commit.
- Never commit or push unless the user asks.

## Database and MCP
- The app connects directly with SQLAlchemy using its own role (`ADS_DB_*`).
- The MCP server is a separate client with a least-privilege read-only role
  (`ads_mcp_readonly`). The app must never route data through MCP.
- DBeaver is an independent admin client. Do not assume DBeaver 25.1.1 has an MCP
  server.
- Do not create databases or roles, change schemas or grant privileges without
  explicit user approval.
- A connection counts as working only after a real test query succeeds.
- Every database path needs query timeouts, row/byte caps, SQL allowlisting for
  agent-generated SQL, and error messages that are safe to show users.

## Human-in-the-loop rules
- Human approval is required before:
  - executing any proposed feature transformation
  - starting any model training
- A changed plan needs fresh approval. A rejected proposal must never proceed
  silently; it is either revised or ended.
- Approvals are real LangGraph interrupt/checkpoint states, persisted so that
  pending approvals survive restarts.
- Never show approval controls in the UI before they actually work.

## Agent communication and memory
- Agents exchange typed messages with a kind (finding, question, proposal,
  challenge, decision), the sender, evidence references and a status.
- Agent output is a **proposal or finding, not a trusted fact**. The Critic and the
  human validate it.
- LangGraph owns routing, shared state, checkpoints and **bounded** revision loops,
  with an explicit maximum number of iterations.
- Durable project memory (Postgres) is kept separate from temporary conversation
  context.
- Calculations, statistics and model training use deterministic Python tools,
  never arithmetic generated by an LLM.
- Never fabricate agent activity, results, charts or statuses. Never claim an
  operation succeeded without verifying it. The UI shows only real, recorded
  events.

## Definition of done (each milestone)
1. The scope is implemented with no fabricated or placeholder features presented
   as working.
2. Tests have been added or updated, and `python -m pytest` passes. Report the
   actual output.
3. `README.md` and this file match the code, and planned items are labelled as
   planned.
4. `git status` and `git diff` have been reviewed for secrets and unintended files.
5. There is a completion report covering what works, what remains, test results
   and the next milestone. The user approves it before the next phase begins.
