# Architecture

Aide is currently a backend-first FastAPI application with CalDAV as the primary runtime data store. The old PostgreSQL-compatible SQLAlchemy model remains for prototype compatibility and one-time migration work, but it is no longer the intended source of truth.

The repository is intentionally small. The backend is split by responsibility into app setup, database configuration, ORM models, Pydantic schemas, and routers.

## System Overview

```text
Client / Browser / API caller
        |
        v
FastAPI backend
        |
        v
CalDAV services
        |
        v
VTODO / VEVENT / VJOURNAL collections
```

Docker Compose runs the backend locally and injects configuration from `.env`.
The backend can also join an external `radicale_default` Docker network so it can talk to a local Radicale container directly at `http://radicale:5232/`, without going through Nginx or Cloudflare.

## Runtime Components

### Backend

Key files:

- `backend/app/main.py` creates the FastAPI app, creates tables, and includes routers.
- `backend/app/database.py` configures the SQLAlchemy engine, session factory, base model, and database dependency.
- `backend/app/models.py` defines ORM models.
- `backend/app/schemas.py` defines Pydantic request and response schemas.
- `backend/app/routers/` contains route handlers by domain.
- `backend/app/static/` contains a simple browser UI for local testing.
- `backend/app/services/caldav_tasks.py` contains the minimal CalDAV VTODO adapter used by the tasks API.
- `backend/app/services/caldav_aide.py` maps Aide journals, outcomes, not-to-dos, and calendar events to CalDAV components.
- `backend/app/services/caldav_store.py` contains the low-level CalDAV component read/write helpers.

### CalDAV Storage

Aide reads tasks from CalDAV `VTODO` components and meetings from `VEVENT` components. Aide-specific records such as thoughts, activity logs, money notes, not-to-dos, task outcomes, and meeting outcomes are stored as `VJOURNAL` components with `X-AIDE-TYPE` and JSON metadata.

Tasks and meetings are intentionally not created or edited inside Aide anymore. They should be maintained in a CalDAV task/calendar client or upstream SaaS, then read by Aide for daily briefing and review.

Set `CALDAV_COLLECTION` when the CalDAV account has more than one collection. Component-specific overrides are also supported with `CALDAV_TASK_COLLECTION`, `CALDAV_EVENT_COLLECTION`, and `CALDAV_JOURNAL_COLLECTION`.

### Legacy Database

`DATABASE_URL` is optional. If present, the SQLAlchemy models can still create the old prototype tables, mainly to support migration and historical compatibility.

Tables are created automatically at startup with:

```python
Base.metadata.create_all(bind=engine)
```

This is acceptable only for the legacy prototype layer. New runtime storage should go through CalDAV unless the product direction changes.

### Docker Compose

Location: `compose.yml`

The compose service:

- builds `./backend`
- runs Uvicorn with reload enabled
- mounts `./backend/app` into the container
- exposes the backend on port `8000`
- loads environment variables from `.env`

## Data Model

### Legacy `tasks`

Historical table for todos and not-todos. It is not the runtime task source anymore.

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
Recurring tasks are stored as metadata first: frequency, solar/lunar calendar, optional month/day/weekday fields, optional natural-language notes, and `recurrence_rule` JSON for richer interval/range/exclusion details. Actual future instance generation is still a later service-layer concern.
The `not_todo_group` field groups not-to-dos into legal, morality, company, family, and health boundaries.
The `priority` field uses four values: `ultra`, `high`, `medium`, and `low`.
The `recurrence_cron`, `recurrence_prepare_days`, `advanced_format`, and `advanced_body` fields are retained for prototype compatibility, but the current product direction favors simple structured recurrence fields and no advanced rule input in the UI.

At runtime, normal To-Dos are read from CalDAV VTODO items. Not-to-dos are read from CalDAV VJOURNAL records so they do not need a local table.

### Legacy `calendar_events`

Historical table for meetings imported from or aligned with calendars. It is not the runtime calendar source anymore.

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

At runtime, meetings are read from CalDAV VEVENT items. Completion/attendance is written as a VJOURNAL outcome rather than creating or editing local meeting records.

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
- `sop_model`
- `plan`
- `result`
- `learning`
- `next_action`
- `energy_level`
- `occurred_at`
- `created_at`

The structured fields are optional. A quick log can still be only a title, while a review-oriented log can capture a lightweight PDCA loop and one energy score for later trend analysis.

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
- `POST /tasks/{task_id}/complete`
- `GET /calendar/sources`
- `GET /calendar/events`
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
Activity analysis already consumes structured activity fields when present, while keeping the older title/category/note path as a fallback for historical records.

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
│   ├── ai_assist.py
│   ├── caldav_aide.py
│   ├── caldav_ical.py
│   ├── caldav_store.py
│   └── caldav_tasks.py
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
