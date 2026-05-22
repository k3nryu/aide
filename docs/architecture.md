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
- `todo_kind`
- `recurrence_frequency`
- `recurrence_calendar`
- `recurrence_month`
- `recurrence_day`
- `recurrence_weekdays`
- `recurrence_rule`
- `not_todo_group`
- `recurrence_natural`
- `recurrence_cron`
- `recurrence_prepare_days`
- `advanced_format`
- `advanced_body`
- `done`
- `due_date`
- `available_date`
- `starts_at`
- `ends_at`
- `location`
- `source`
- `completed_at`
- `created_at`

The `type` field currently distinguishes `todo` from `not_todo`.
The `context` field currently distinguishes `personal` from `company`.
The `todo_kind` field distinguishes one-time todos from recurring todos.
The `available_date` field represents the earliest date a one-time task can realistically be acted on, while `due_date` represents the latest completion date.
The `starts_at`, `ends_at`, `location`, and `source` fields let meeting-like scheduled work live directly on tasks instead of requiring a separate meeting entry in the task UI.
Recurring tasks are stored as metadata first: frequency, solar/lunar calendar, optional month/day/weekday fields, optional natural-language notes, and `recurrence_rule` JSON for richer interval/range/exclusion details. Actual future instance generation is still a later service-layer concern.
The `not_todo_group` field groups not-to-dos into legal, morality, company, family, and health boundaries.
The `priority` field uses four values: `ultra`, `high`, `medium`, and `low`.
The `recurrence_cron`, `recurrence_prepare_days`, `advanced_format`, and `advanced_body` fields are retained for prototype compatibility, but the current product direction favors simple structured recurrence fields and no advanced rule input in the UI.

### `calendar_events`

Stores meetings imported from or aligned with calendars.

Important fields:

- `title`
- `source`
- `account_context`
- `importance`
- `event_kind`
- `recurrence_frequency`
- `recurrence_calendar`
- `recurrence_month`
- `recurrence_day`
- `recurrence_weekdays`
- `recurrence_natural`
- `recurrence_rule`
- `starts_at`
- `ends_at`
- `location`
- `description`
- `external_id`
- `done`
- `completed_at`
- `created_at`

The current prototype supports the shared event model and manual/API ingestion. Recurring meetings use the legacy recurrence summary fields plus `recurrence_rule` JSON for Outlook-style details such as interval, date range, excluded business-day sets, and time duration. Real Google, Apple, and Outlook account sync still needs provider-specific authentication and sync jobs.
The `done` and `completed_at` fields archive a meeting series or meeting item when the user marks it as finished from the task list; archived meetings are excluded from active calendar/task views.

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
- `PATCH /calendar/events/{event_id}`
- `POST /calendar/events/{event_id}/complete`
- `GET /thoughts`
- `POST /thoughts`
- `POST /thoughts/{thought_id}/task-suggestions`
- `GET /activity-logs`
- `POST /activity-logs`
- `GET /activity-logs/analysis`
- `GET /money`
- `POST /money`

AI-assist routes currently return reviewable drafts. The prototype uses local heuristic logic in `services/ai_assist.py`; future provider-backed AI should replace that service layer without changing the user confirmation flow.

## Backend Layout

```text
backend/app/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── routers/
│   ├── __init__.py
│   ├── activity_logs.py
│   ├── calendar.py
│   ├── daily.py
│   ├── money.py
│   ├── tasks.py
│   └── thoughts.py
├── services/
│   └── ai_assist.py
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
