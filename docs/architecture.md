# Architecture

Aide is currently a backend-first FastAPI application with a PostgreSQL-compatible relational database.

The repository is intentionally small. The backend is split by responsibility into app setup, database configuration, ORM models, Pydantic schemas, and routers.

## System Overview

```text
Client / Browser / API caller
        |
        v
FastAPI backend
        |
        v
SQLAlchemy ORM
        |
        v
PostgreSQL database
```

Docker Compose runs the backend locally and injects configuration from `.env`.

## Runtime Components

### Backend

Key files:

- `backend/app/main.py` creates the FastAPI app, creates tables, and includes routers.
- `backend/app/database.py` configures the SQLAlchemy engine, session factory, base model, and database dependency.
- `backend/app/models.py` defines ORM models.
- `backend/app/schemas.py` defines Pydantic request and response schemas.
- `backend/app/routers/` contains route handlers by domain.
- `backend/app/static/` contains a simple browser UI for local testing.

### Database

The backend expects `DATABASE_URL` to point at a PostgreSQL-compatible database.

Tables are created automatically at startup with:

```python
Base.metadata.create_all(bind=engine)
```

This is acceptable for the early prototype. A migration system such as Alembic should be introduced before schema changes become frequent or production data matters.

### Docker Compose

Location: `compose.yml`

The compose service:

- builds `./backend`
- runs Uvicorn with reload enabled
- mounts `./backend/app` into the container
- exposes the backend on port `8000`
- loads environment variables from `.env`

## Data Model

### `tasks`

Stores todos and not-todos.

Important fields:

- `title`
- `description`
- `type`
- `priority`
- `importance`
- `urgency`
- `context`
- `recurrence_natural`
- `recurrence_cron`
- `recurrence_prepare_days`
- `advanced_format`
- `advanced_body`
- `done`
- `due_date`
- `completed_at`
- `created_at`

The `type` field currently distinguishes `todo` from `not_todo`.
The `context` field currently distinguishes `personal` from `company`.
Recurring tasks are stored as metadata first; actual future instance generation is still a later service-layer concern.
The `priority` field uses four values: `ultra`, `high`, `medium`, and `low`.
The `advanced_format` and `advanced_body` fields store Markdown or YAML text for richer recurring-task and not-to-do input.

### `calendar_events`

Stores meetings imported from or aligned with calendars.

Important fields:

- `title`
- `source`
- `account_context`
- `starts_at`
- `ends_at`
- `location`
- `description`
- `external_id`
- `created_at`

The current prototype supports the shared event model and manual/API ingestion. Real Google, Apple, and Outlook account sync still needs provider-specific authentication and sync jobs.

### `thoughts`

Stores captured thoughts and notes.

Important fields:

- `content`
- `tag`
- `created_at`

### `activity_logs`

Stores things the user actually did, including events that were not planned tasks.

Important fields:

- `title`
- `category`
- `note`
- `occurred_at`
- `created_at`

### `money_records`

Stores lightweight finance entries.

Important fields:

- `title`
- `amount`
- `type`
- `category`
- `note`
- `record_date`
- `created_at`

The `type` field currently distinguishes `income` from `expense`.

## API Structure

Current routes:

- `GET /`
- `GET /daily/briefing`
- `GET /tasks`
- `POST /tasks`
- `PATCH /tasks/{task_id}`
- `POST /tasks/{task_id}/complete`
- `GET /calendar/sources`
- `GET /calendar/events`
- `POST /calendar/events`
- `GET /thoughts`
- `POST /thoughts`
- `GET /activity-logs`
- `POST /activity-logs`
- `GET /money`
- `POST /money`

## Backend Layout

```text
backend/app/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── routers/
│   ├── __init__.py
│   ├── calendar.py
│   ├── daily.py
│   ├── money.py
│   ├── tasks.py
│   └── thoughts.py
```

Future business logic that grows beyond simple route handlers should move into `services/`.

## Future Components

Planned future components:

- Web frontend
- Authentication
- Alembic migrations
- AI summary service
- Embedding generation
- Qdrant vector store
- Retrieval layer for personal memory
