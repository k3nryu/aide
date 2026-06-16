# Aide

Aide is a personal executive assistant system for daily PDCA, task management, thought capture, lightweight finance tracking, and eventually AI-assisted memory.

The product goal is not to become a complex calendar app. Aide should help one person act, record what happened, check patterns, get practical suggestions, and keep looping toward personal growth, financial freedom, and life freedom. Scheduling should stay simple and connect to external calendar/CalDAV services where possible.

The project is currently an early backend-first prototype. It exposes a FastAPI API, uses CalDAV as the primary runtime data store, and runs locally through Docker Compose. The old SQLAlchemy/PostgreSQL model remains only for prototype compatibility and migration tooling.

## Current Capabilities

- Daily briefing endpoint
- CalDAV-backed To-Do reading and completion/outcome capture
- CalDAV-backed calendar event reading and attendance outcome capture
- Company/personal task classification
- One-time and recurring task metadata
- Recurring task fields for daily, weekly, monthly, yearly, solar, and lunar patterns
- Grouped not-to-dos read from CalDAV VJOURNAL records
- Thought capture with optional tags
- Thought-to-action suggestion drafts for manual review
- Activity/life log capture for things that happened outside the task list
- Structured activity logs with optional PDCA/SOP fields: plan, result, check/learning, next action, and energy level
- Activity review draft with PDCA, STOW, SCAQ, SMART, AIDA, 5W2H, and debate prompts
- Money record capture for income and expenses
- Financial independence dashboard with FI assets, fixed expense items, passive income, and safe withdrawal rate
- Simple browser UI for quick local testing
- Dockerized backend service

## Planned Capabilities

- Web-first frontend
- Mobile-friendly daily workflow
- AI summaries
- Retrieval-augmented personal memory
- Qdrant-backed vector search
- More structured finance views

## Repository Layout

```text
.
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       └── routers/
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   └── vision.md
├── compose.yml
├── AGENTS.md
└── README.md
```

## Backend

The backend is implemented under `backend/app`.

- `main.py` creates the FastAPI app, creates tables, and includes routers
- `database.py` configures SQLAlchemy and database sessions
- `models.py` defines ORM models
- `schemas.py` defines Pydantic schemas
- `routers/` contains API routes by domain

## Configuration

The backend requires CalDAV variables for the main runtime workflow. `DATABASE_URL` is optional and should only be kept when you need legacy prototype tables or migration tooling.

Docker Compose loads environment variables from `.env`:

```env
CALDAV_URL=http://radicale:5232/
CALDAV_USERNAME=your-user
CALDAV_PASSWORD=your-password
CALDAV_COLLECTION=/your-user/main-calendar/
# Optional legacy database:
# DATABASE_URL=postgresql://user:password@host.docker.internal:5432/aide
```

When CalDAV variables are present, Aide reads To-Dos from VTODO, reads meetings/events from VEVENT, and stores Aide logs such as thoughts, activity logs, money notes, not-to-dos, and outcomes as VJOURNAL records. Tasks and meetings should be created and edited in the CalDAV client or upstream service, not inside Aide.

## Running Locally

Start the backend:

```bash
docker compose -f compose.yml up --build
```

The API is exposed on:

```text
http://127.0.0.1:8000
```

For another device on the same trusted network, use the host machine's IP address:

```text
http://<host-ip>:8000
```

FastAPI interactive docs are available at:

```text
http://127.0.0.1:8000/docs
```

A simple browser UI is available at:

```text
http://127.0.0.1:8000/app/
```

## API Overview

- `GET /` - health/status
- `GET /daily/briefing` - today's briefing
- `GET /tasks` - list tasks, optionally filtered by completion, context, completion range, or search
- `POST /tasks/{task_id}/complete` - complete a CalDAV task and write an outcome journal
- `GET /calendar/sources` - list planned/available calendar sources
- `GET /calendar/events` - list calendar events for a date
- `POST /calendar/events/{event_id}/complete` - write a calendar attendance outcome journal
- `GET /thoughts` - list thoughts
- `POST /thoughts` - create a thought
- `POST /thoughts/{thought_id}/task-suggestions` - draft action suggestions from a thought
- `GET /activity-logs` - list activity/life logs
- `POST /activity-logs` - create an activity/life log
- `GET /activity-logs/analysis` - draft PDCA/STOW analysis from completed tasks and activity logs
- `GET /money` - list money records
- `POST /money` - create a money record

## Project Docs

- [Vision](docs/vision.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Product Ideas / 产品想法](docs/product-ideas.md)
- [Agent Instructions](AGENTS.md)
