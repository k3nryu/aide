# Agent Instructions

Project-specific guidance for coding agents working on Aide.

## Product Intent

Aide is a personal executive assistant system for daily briefing, tasks, not-to-dos, thought capture, finance tracking, and future AI memory.

The product should feel calm, practical, mobile-first, and ADHD-friendly. Favor fast capture, clear defaults, short lists, and simple summaries.

## Current State

Aide is an early backend-first prototype.

Implemented:

- FastAPI backend
- SQLAlchemy ORM models
- PostgreSQL-compatible database access
- Docker Compose local backend service

Not implemented yet:

- Frontend
- Authentication
- Database migrations
- Tests
- RAG, Qdrant, and AI provider integration

## Architecture Guidelines

- Keep APIs simple, explicit, and resource-oriented.
- Avoid overengineering; use the smallest structure that fits the current feature.
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

## Testing

There is no test suite yet. When adding meaningful behavior, prefer focused tests with the smallest reasonable setup. If tests cannot be added yet, document manual verification.

## Style

- Keep code readable and direct.
- Keep functions small and focused.
- Prefer explicit names over abbreviations.
- Add comments only when they clarify non-obvious behavior.
- Preserve the user's existing work and avoid unrelated refactors.
