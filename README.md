# Aide

Aide is a personal executive assistant system for daily planning, task management, thought capture, lightweight finance tracking, and eventually AI-assisted memory.

The project is currently an early backend-first prototype. It exposes a FastAPI API backed by PostgreSQL-compatible SQLAlchemy models and runs locally through Docker Compose.

## Current Capabilities

- Daily briefing endpoint
- Task and not-to-do capture
- Task editing
- Task completion
- Company/personal task classification
- One-time and recurring task metadata
- Recurring task fields for daily, weekly, monthly, yearly, solar, and lunar patterns
- Grouped not-to-dos for legal, morality, company, family, and health boundaries
- Completed task lookup by time range or keyword
- Calendar event capture for today's meetings
- Thought capture with optional tags
- Activity/life log capture for things that happened outside the task list
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

The backend requires a `DATABASE_URL` environment variable.

Docker Compose loads environment variables from `.env`:

```env
DATABASE_URL=postgresql://user:password@host.docker.internal:5432/aide
```

Adjust the value to match the local or hosted PostgreSQL instance.

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
- `POST /tasks` - create a task or not-to-do
- `PATCH /tasks/{task_id}` - update a task
- `POST /tasks/{task_id}/complete` - complete a task
- `GET /calendar/sources` - list planned/available calendar sources
- `GET /calendar/events` - list calendar events for a date
- `POST /calendar/events` - create or import a calendar event
- `GET /thoughts` - list thoughts
- `POST /thoughts` - create a thought
- `GET /activity-logs` - list activity/life logs
- `POST /activity-logs` - create an activity/life log
- `GET /money` - list money records
- `POST /money` - create a money record

## Project Docs

- [Vision](docs/vision.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Product Ideas / 产品想法](docs/product-ideas.md)
- [Agent Instructions](AGENTS.md)
