"""Streamlit entry point: ``streamlit run src/agentic_data_scientist/app/main.py``."""

from __future__ import annotations

import streamlit as st

from agentic_data_scientist import __version__
from agentic_data_scientist.config import load_dotenv_file, load_settings
from agentic_data_scientist.system_status import (
    MIN_PYTHON,
    database_config_summary,
    dependency_report,
    python_is_supported,
    python_version,
)

APP_TITLE = "Agentic Data Scientist"

PLANNED_VIEWS = (
    "Data Hub",
    "EDA",
    "Feature Engineering",
    "Data Scientist Lab",
    "AI Business Analyst",
    "Agent Activity",
)

CAPABILITIES = (
    ("Data access", "Import CSV, Excel, JSON, Parquet, PostgreSQL and permitted public datasets."),
    ("Quality & EDA", "Assess data quality, propose cleaning steps and explore data with interactive Plotly charts."),
    ("Feature engineering", "A dedicated agent proposes transformations; nothing runs until a human approves it."),
    ("Modelling", "A Data Scientist agent proposes tasks, targets, algorithms and evaluation strategies."),
    ("Critique", "A Critic/Evaluator agent challenges assumptions and checks model results."),
    ("Business answers", "An AI Business Analyst answers questions from validated data and builds reports."),
)

# (phase, title, status). Only Phase 1 has started; everything else is planned.
ROADMAP = (
    ("Phase 1", "Project foundation, configuration, status page and tests", "In review"),
    ("Phase 2", "Data Hub: file and PostgreSQL ingestion, persistent project metadata", "Planned"),
    ("Phase 3", "Data quality assessment and EDA with Plotly", "Planned"),
    ("Phase 4", "LangGraph orchestration, structured agent messages, approval checkpoints", "Planned"),
    ("Phase 5", "Feature Engineering Agent and Data Scientist Lab", "Planned"),
    ("Phase 6", "Critic/Evaluator and AI Business Analyst", "Planned"),
    ("Phase 7", "Agent Activity audit view, MLflow tracking, hardening", "Planned"),
)

STATE_LABELS = {
    "ok": ":green[●] ",
    "warn": ":orange[●] ",
    "info": ":gray[●] ",
    "error": ":red[●] ",
}


def _status_card(title: str, state: str, value: str, detail: str) -> None:
    with st.container(border=True):
        st.caption(title)
        st.markdown(f"{STATE_LABELS[state]}**{value}**")
        st.caption(detail)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"### {APP_TITLE}")
        st.caption(f"Version {__version__}")
        st.markdown("**Current view:** Overview")
        st.markdown("**Planned views**")
        st.markdown("\n".join(f"- {view} *(not yet built)*" for view in PLANNED_VIEWS))


def render_overview() -> None:
    st.title(APP_TITLE)
    st.markdown(
        "A collaborative multi-agent platform for data science and AI business intelligence. "
        "Specialised agents will exchange structured findings and proposals, while **people "
        "approve** feature transformations and model training before anything runs."
    )
    st.info(
        "Phase 1 foundation. Agents, data import and approval workflows are not implemented yet; "
        "this page only reports what the application can verify about itself.",
        icon="ℹ️",
    )

    st.subheader("Planned capabilities")
    cols = st.columns(3)
    for i, (name, text) in enumerate(CAPABILITIES):
        with cols[i % 3], st.container(border=True):
            st.markdown(f"**{name}**")
            st.caption(text)

    render_system_status()
    render_roadmap()


def render_system_status() -> None:
    st.subheader("System status")
    st.caption("Checked when the page loads. No network or database connections are made.")

    env_found = load_dotenv_file()
    settings = load_settings()
    report = dependency_report()

    core = report["core"]
    core_ok = all(pkg.installed for pkg in core)
    db_state, db_message = database_config_summary(settings)
    db_card_state = {"configured": "ok", "incomplete": "warn", "invalid": "error"}.get(db_state, "info")
    db_value = {
        "configured": "Configured (not verified)",
        "incomplete": "Incomplete",
        "invalid": "Invalid",
        "not_configured": "Not configured",
    }[db_state]

    cols = st.columns(4)
    with cols[0]:
        supported = python_is_supported()
        _status_card(
            "Python",
            "ok" if supported else "error",
            python_version(),
            f"Requires {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+",
        )
    with cols[1]:
        _status_card(
            "Core dependencies",
            "ok" if core_ok else "error",
            f"{sum(p.installed for p in core)}/{len(core)} installed",
            ", ".join(p.name for p in core),
        )
    with cols[2]:
        _status_card(
            "Local .env file",
            "ok" if env_found else "info",
            "Found" if env_found else "Not found",
            "Optional. Copy .env.example to .env.",
        )
    with cols[3]:
        _status_card("App database settings", db_card_state, db_value, db_message)

    with st.expander("Dependency groups (from pyproject.toml)"):
        rows = ["| Group | Package | Installed version |", "|---|---|---|"]
        for group, packages in report.items():
            for pkg in packages:
                rows.append(f"| {group} | {pkg.name} | {pkg.version or '—'} |")
        st.markdown("\n".join(rows))
        st.caption("Only the core and dev groups are needed in Phase 1. Other groups are for later phases.")

    st.markdown(
        "**PostgreSQL / MCP:** not integrated yet. During the Phase 1 setup inspection (2026-10-26), "
        "a local PostgreSQL 17 server was observed on port 5433. This page does **not** check it live, "
        "so that observation may be out of date. See `docs/postgres-mcp-integration.md` for the plan."
    )


def render_roadmap() -> None:
    st.subheader("Roadmap")
    rows = ["| Phase | Scope | Status |", "|---|---|---|"]
    rows += [f"| {phase} | {scope} | {status} |" for phase, scope, status in ROADMAP]
    st.markdown("\n".join(rows))


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🧭", layout="wide")
    render_sidebar()
    render_overview()


if __name__ == "__main__":  # `streamlit run` executes this file as __main__
    main()
