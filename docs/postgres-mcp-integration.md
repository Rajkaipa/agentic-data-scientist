# PostgreSQL, DBeaver and MCP integration plan

Status: **plan only.** No MCP server is installed or configured, no database
connection has been made, and no roles, schemas or privileges have been
created. Every step under "Next steps" needs explicit approval first.

## 1. Verified environment (inspected 2026-10-26)

| Item | Finding | How verified |
|---|---|---|
| PostgreSQL client/server tools | 17.4 in `C:\Program Files\PostgreSQL\17\bin` | `psql --version` |
| Windows service | `postgresql-x64-17`, Running, Automatic start | `Get-Service` |
| Listening port | **5433** (not the default 5432), on `0.0.0.0` and `::` | `Get-NetTCPConnection`, `pg_isready -p 5433` → accepting connections |
| Port 5432 | No response | `pg_isready -p 5432` |
| Data directory | `C:\Program Files\PostgreSQL\17\data` | service command line |
| DBeaver | 25.1.1 (user-reported); no built-in MCP server assumed | — |
| Claude Code | 2.1.310; supports `claude mcp add` / `add-json`, stdio/SSE/HTTP, scopes `local`/`project`/`user` | `claude mcp --help` |
| Node / uv / Docker | Node 24.4.1 (`npx`), uv/uvx, Docker 28.4.0 available | `--version` |

**Not verified:** credentials, existing databases or roles, any SQL query.

**Security observation:** the server listens on all interfaces. If remote
access is not needed, consider reviewing `listen_addresses` and `pg_hba.conf`
so only `localhost` is accepted. This is a system change and needs approval.

## 2. Architecture: three independent clients

```
                 ┌──────────────────────────────┐
                 │ PostgreSQL 17  localhost:5433 │
                 └──────────────────────────────┘
                    ▲            ▲             ▲
   admin role       │            │ ads_mcp_    │ ads_app role
   (human, GUI)     │            │ readonly    │ (Phase 2+)
            ┌───────┴──┐   ┌─────┴───────┐  ┌──┴──────────────────┐
            │ DBeaver  │   │ MCP server  │  │ Streamlit app       │
            │ 25.1.1   │   │ (stdio, for │  │ SQLAlchemy + psycopg│
            │          │   │ Claude Code)│  │ ADS_DB_* settings   │
            └──────────┘   └─────────────┘  └─────────────────────┘
```

- **DBeaver** is used by a person for administration and inspection. It uses its
  own saved connection (host `localhost`, port `5433`), and its password is kept in
  DBeaver's secure storage rather than in project files. You can also add a second
  DBeaver connection as `ads_mcp_readonly` to see exactly what the agent can see.
- **The MCP server** exposes approved, read-only database tools to Claude Code and
  later to compatible agents. It has its own role and its own credentials, and it
  does not depend on DBeaver.
- **The application** connects directly through SQLAlchemy using the `ADS_DB_*`
  variables in `.env`. It never goes through MCP. MCP is a developer and agent
  tool, not the application's data layer.

## 3. MCP server evaluation

| Candidate | Licence / maintenance | Safety controls | Notes |
|---|---|---|---|
| **MCP Toolbox for Databases** ([googleapis/genai-toolbox](https://github.com/googleapis/genai-toolbox)) | Apache-2.0. Actively developed by Google (2,300+ commits; install docs at v1.15.0). | `tools.yaml` lets you expose **only named, parameterised SQL tools** (`$1` placeholders), so no free-form SQL is needed. Prebuilt `--prebuilt=postgres` tool sets also exist. | Ships as a single Go binary (`toolbox.exe`) or via `npx @toolbox-sdk/server`. Supports stdio (`--stdio`) and HTTP. |
| **Postgres MCP Pro** ([crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp)) | MIT. Last PyPI release 0.3.0 on 2025-05-16. | "Restricted" mode runs read-only transactions, parses SQL with pglast, rejects COMMIT/ROLLBACK and applies an execution-time limit. | Requires **Python ≥ 3.12**, so run it in isolation with `uvx` or Docker, not in this project's 3.11 `.venv`. Configured through `DATABASE_URI`. |
| `@modelcontextprotocol/server-postgres` | **Archived 2025-05-29** (read-only repository). | — | Do not use. |

**Recommendation: MCP Toolbox for Databases with a custom `tools.yaml`.**

- **Why:** it is actively maintained and ships as a self-contained binary. Its
  custom tool definitions also let us expose a small allowlist of operations
  (list schemas and tables, describe a table, a bounded sample, and approved
  parameterised queries) instead of arbitrary SQL. Start without a generic
  `execute_sql` tool, and add one later only if we decide it is needed.
- **Fallback:** Postgres MCP Pro in restricted mode, if a free-form read-only SQL
  tool turns out to be required.

**Before installing, re-check the official docs.** The Toolbox's Claude Code-specific
page could not be fetched during this inspection (HTTP 404), and secondary sources
disagreed on flags. Confirm the following against the release you install:

- the exact `--stdio` and `--tools-file` flags
- the variable names for the prebuilt Postgres configuration (reported as
  `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER` and
  `POSTGRES_PASSWORD`)

## 4. Least-privilege read-only role (design; **not executed**)

The database role is the primary security boundary. Restrictions in the MCP
server and in SQL validation are additional layers on top of it.

Run this only after approval, as an administrator, in psql or DBeaver.
`<db>` and `<schema>` are placeholders.

### Who owns what

| Role | Purpose | Login |
|---|---|---|
| `ads_owner` | **Owns and creates** the tables in `<schema>`. Data loading runs as this role, either directly or through `SET ROLE ads_owner` from a member login. | No (`NOLOGIN`) |
| `ads_mcp_readonly` | **Receives** read-only access (`SELECT`) for the MCP server. Owns nothing. | Yes |

```sql
-- Owner of the analytics objects. NOLOGIN: people and loaders act as it via SET ROLE.
CREATE ROLE ads_owner NOLOGIN;
ALTER SCHEMA <schema> OWNER TO ads_owner;   -- or: CREATE SCHEMA <schema> AUTHORIZATION ads_owner;

-- No password in SQL text: set it afterwards with \password (prompted, not logged).
CREATE ROLE ads_mcp_readonly
  LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
  CONNECTION LIMIT 3;

-- Session defaults: guard rails, not the security boundary (a session can SET them).
ALTER ROLE ads_mcp_readonly SET default_transaction_read_only = on;
ALTER ROLE ads_mcp_readonly SET statement_timeout = '15s';
ALTER ROLE ads_mcp_readonly SET lock_timeout = '2s';
ALTER ROLE ads_mcp_readonly SET idle_in_transaction_session_timeout = '30s';

-- The actual boundary: only CONNECT, USAGE and SELECT on approved objects.
GRANT CONNECT ON DATABASE <db> TO ads_mcp_readonly;
GRANT USAGE ON SCHEMA <schema> TO ads_mcp_readonly;

-- Tables that already exist (a one-time grant; it does not cover future tables).
GRANT SELECT ON ALL TABLES IN SCHEMA <schema> TO ads_mcp_readonly;

-- Tables that ads_owner creates FROM NOW ON in <schema>.
-- Must be run by ads_owner, by a member of it, or by a superuser.
ALTER DEFAULT PRIVILEGES FOR ROLE ads_owner IN SCHEMA <schema>
  GRANT SELECT ON TABLES TO ads_mcp_readonly;
```

```
\password ads_mcp_readonly
```

**How default privileges work:** `ALTER DEFAULT PRIVILEGES` applies only to objects
created *after* it runs, and only by the role named in `FOR ROLE`. If you leave
`FOR ROLE` out, that role is whoever runs the statement. Default privileges do
**not** cover tables created by any other role.

So if a table in `<schema>` is created by a different login, `ads_mcp_readonly`
will not be able to read it until one of these happens:
- someone runs an explicit `GRANT SELECT` on that table, or
- the table's ownership is transferred with `ALTER TABLE ... OWNER TO ads_owner`.

The simplest rule is that every object in `<schema>` is created as `ads_owner`.
You can check the current default privileges with `\ddp` in psql.

Do **not** grant `pg_read_all_data`, `pg_read_server_files`, `pg_execute_server_program`
or ownership of any object. The future application role (`ads_app`) is separate
and gets write access only to its own metadata schema.

## 5. Claude Code configuration (planned)

### Scope

- **`local`** (the default) stores the configuration in `~/.claude.json` for this
  project only. It is never committed.
- **`project`** writes `.mcp.json` to the repository root. That file is committed
  and needs per-user approval. It supports `${VAR}` and `${VAR:-default}`
  expansion, so it can be committed without secrets.

**Plan:** commit a `.mcp.json` that contains only `${...}` references, and supply
the real values from the environment at launch (see "Storing the MCP password"
below for the options). Passing `-e POSTGRES_PASSWORD=...` on the command line
would leave the password in PowerShell history and in plain text in
`~/.claude.json`.

Sketch, to be adapted to the verified Toolbox flags. The launcher is left open
on purpose; see the note below.

```json
{
  "mcpServers": {
    "postgres-readonly": {
      "command": "<launcher: npx, or the full path to toolbox.exe>",
      "args": ["<launcher-specific args>",
               "--tools-file", "mcp/tools.yaml", "--stdio"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5433",
        "POSTGRES_DATABASE": "${ADS_MCP_PG_DATABASE}",
        "POSTGRES_USER": "ads_mcp_readonly",
        "POSTGRES_PASSWORD": "${ADS_MCP_PG_PASSWORD}"
      }
    }
  }
}
```

**Windows launcher (verify at setup time):** it is **unverified** whether Claude Code
on native Windows needs `npx` wrapped as `cmd /c npx` for stdio servers.

- **What I checked:** I searched the current Claude Code MCP documentation during
  Phase 1 and found no such statement.
- **What to check at setup:** read the docs for the Claude Code version installed
  at that time (2.1.310 during Phase 1) and the selected MCP server's install
  docs. Then confirm the server actually starts with `claude mcp get
  postgres-readonly` or `/mcp` before relying on it.
- **Possible way round it:** pointing `command` at a downloaded `toolbox.exe`
  would avoid the `npx` launcher altogether. That still has to be verified the
  same way.

### Storing the MCP password

No option below has been applied, and no credentials have been set. Whichever
option you choose, never type the password as a command argument or into a
script. Read it with a masked prompt instead.

| Option | Where the secret lives | Trade-offs |
|---|---|---|
| **A. Process-scoped variable** (recommended for first tests) | Only in the memory of the current PowerShell window and the processes it starts | Nothing persists on disk, and it is gone when the window closes. You have to re-enter it each session. Child processes started from that window, including Claude Code and its MCP servers, inherit it. |
| **B. Windows user environment variable** | Plain text in your user profile's registry (`HKCU\Environment`) | It persists across reboots until you remove it. Every process running as your user can read it and inherits it. It is not encrypted, audited or rotated, and it is **not a secret vault**. Use it only if A becomes impractical. |
| **C. `pgpass.conf`** (`%APPDATA%\postgresql\pgpass.conf`) | A plain-text file with lines of the form `host:port:db:user:password` | Covered in detail below. |
| **D. A secret store** (Windows Credential Manager, or the PowerShell `SecretManagement` module) | Encrypted per user | This is a real vault. It needs a small launcher script that fetches the secret and starts the server, which is extra setup. Consider it once the integration is stable. |

**About option C (`pgpass.conf`):**
- **Plain text:** the file stores the password unencrypted.
- **No permission check on Windows:** on Unix, libpq ignores the file if other
  users can read it. On Windows, the
  [PostgreSQL 17 docs](https://www.postgresql.org/docs/17/libpq-pgpass.html) say
  no permission check is made and the file's directory is assumed to be secure.
  So you have to restrict the file to your own user yourself, with `icacls`.
- **Client support:** only clients that implement pgpass will read it. libpq and
  psycopg do. Whether the selected MCP server does is **unverified**.
- **Git:** the file must never be inside the repository. `.gitignore` excludes
  `pgpass.conf` and `.pgpass` as a safeguard.

Option A without echoing the password (current window only, nothing persisted):

```powershell
$s = Read-Host "MCP DB password" -AsSecureString
$b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
try { $env:ADS_MCP_PG_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
claude   # start Claude Code from this same window
```

For option B, the only difference is the assignment line, which becomes
`[Environment]::SetEnvironmentVariable("ADS_MCP_PG_PASSWORD", <value>, "User")`.
The trade-offs above still apply.

## 6. Query safety controls

| Control | MCP path | Application path (Phase 2+) |
|---|---|---|
| Read-only | Role grants plus `default_transaction_read_only` | Separate `ads_app` role. Agent-generated SQL runs only through a read-only connection. |
| Timeouts | Role `statement_timeout = 15s`, `lock_timeout = 2s` | The same settings per connection, plus a SQLAlchemy `pool_timeout` |
| Result size | `LIMIT` built into each `tools.yaml` query, with a capped limit parameter | `fetchmany` with a hard row cap, and a byte cap before data reaches the UI or an LLM |
| SQL validation | Only named tools; no free-form SQL at first | A parser-based allowlist (a single `SELECT`, no DDL, DML or `COMMIT`) before execution |
| Errors | Server returns database errors | Database errors become user-safe messages. Connection strings and passwords are never logged. |

## 7. Next steps (each needs approval)

1. Choose the database name and schema(s) the agents may read.
2. Decide which role owns or creates the tables (`ads_owner`). Then run the role
   script in section 4, and set the password with `\password`.
3. Confirm the MCP server choice and pin a version after re-reading its docs.
   Verify the Windows launcher at the same time (section 5).
4. Download the server binary or package. This is a user-level download, not a
   global Python change.
5. Add `mcp/tools.yaml` and `.mcp.json` (references only). Choose a password
   storage option from section 5 and supply the value.
6. Verify the setup, and only report success after both checks pass:
   - `SELECT current_user, current_setting('transaction_read_only');` returns
     `ads_mcp_readonly` and `on`.
   - A `CREATE TABLE` attempt fails with a permission error.
