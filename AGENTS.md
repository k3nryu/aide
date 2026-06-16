# Agent Instructions

Project-specific guidance for coding agents working on Aide.

## Product Intent

Aide is a personal executive assistant system for daily briefing, tasks, not-to-dos, thought capture, structured activity logging, finance tracking, and future AI memory.

The product should feel calm, practical, mobile-first, and ADHD-friendly. Favor fast capture, clear defaults, short lists, and simple summaries.

## Current State

Aide is an early backend-first prototype.

Implemented:

- FastAPI backend
- SQLAlchemy ORM models
- Optional PostgreSQL-compatible legacy database access
- Docker Compose local backend service
- Simple static browser UI
- CalDAV-backed To-Do reading through VTODO
- CalDAV-backed calendar event reading through VEVENT
- Aide-specific records and outcomes through VJOURNAL
- Structured PDCA-friendly activity log fields
- Small standard-library unit tests for AI-assist heuristics

Not implemented yet:

- Full web frontend
- Authentication
- Database migrations
- RAG, Qdrant, and AI provider integration

## Architecture Guidelines

- Keep APIs simple, explicit, and resource-oriented.
- Avoid overengineering; use the smallest structure that fits the current feature.
- Do not reintroduce local task or meeting authoring unless the user explicitly reverses the CalDAV-first direction.
- Keep changes small and aligned with the prototype.
- Validate user input at the Pydantic schema boundary.
- Add external services only when the roadmap or user request calls for them.
- Split `backend/app/main.py` into modules as the backend grows.

## Backend Conventions

Current stack:

- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn
- PostgreSQL via `psycopg2-binary`

Use existing SQLAlchemy and Pydantic patterns unless refactoring is part of the task.

Keep route names resource-oriented:

- `/tasks`
- `/thoughts`
- `/money`
- `/daily/briefing`

When behavior grows beyond simple route handlers, introduce a service layer.

Likely module split:

- `app/database.py`
- `app/models.py`
- `app/schemas.py`
- `app/routers/`
- `app/services/`

## Data Safety

- Do not delete or reset data without explicit user approval.
- Do not commit secrets.
- Treat `.env` as local configuration.
- Avoid unnecessary logs of financial or personal memory content.

## Documentation

Update docs when changing product direction, architecture, or major workflows.

- `README.md` for setup and current capabilities
- `docs/vision.md` for product intent
- `docs/architecture.md` for technical structure
- `docs/roadmap.md` for planned work
- `AGENTS.md` for agent guidance

## GitHub Workflow

When publishing work to GitHub, prefer a clear and conservative flow.

Recommended flow for feature work:

1. Keep changes on a feature branch such as `codex/activity-logs-browser-ui`.
2. Before switching branches, check `git status -sb`.
3. Commit all intended changes on the feature branch.
4. Push the feature branch to GitHub.
5. Switch back to `main`.
6. Merge the feature branch into `main`.
7. Push `main` to GitHub.

Do not switch branches or merge while there are uncommitted changes unless the user explicitly asks for that and the risk is clear.

When explaining git work to the user, use plain language:

- "Feature branch" means a safe place to develop before touching `main`.
- `main` should represent the current usable version.
- Merge only after the feature branch has been checked and committed.
- If a PR cannot be created automatically, provide the GitHub PR URL and explain the blocker.

## Testing

There is no test suite yet. When adding meaningful behavior, prefer focused tests with the smallest reasonable setup. If tests cannot be added yet, document manual verification.

## Style

- Keep code readable and direct.
- Keep functions small and focused.
- Prefer explicit names over abbreviations.
- Add comments only when they clarify non-obvious behavior.
- Preserve the user's existing work and avoid unrelated refactors.
