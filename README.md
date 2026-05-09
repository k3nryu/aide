# Aide

Aide is a personal executive assistant system for daily planning, task management, thought capture, lightweight finance tracking, and eventually AI-assisted memory.

The project is currently an early backend-first prototype. It exposes a FastAPI API backed by PostgreSQL-compatible SQLAlchemy models and runs locally through Docker Compose.

## Current Capabilities

- Daily briefing endpoint
- Task and not-to-do capture
- Task completion
- Thought capture with optional tags
- Money record capture for income and expenses
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
│       └── main.py
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   └── vision.md
├── compose.yml
├── AGENTS.md
└── README.md
```

## Backend

The backend is implemented in `backend/app/main.py`.

It currently contains:

- FastAPI application setup
- SQLAlchemy engine and session management
- ORM models
- Pydantic schemas
- Route handlers
- Automatic table creation at startup

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

FastAPI interactive docs are available at:

```text
http://127.0.0.1:8000/docs
```

## API Overview

- `GET /` - health/status
- `GET /daily/briefing` - today's briefing
- `GET /tasks` - list tasks
- `POST /tasks` - create a task or not-to-do
- `POST /tasks/{task_id}/complete` - complete a task
- `GET /thoughts` - list thoughts
- `POST /thoughts` - create a thought
- `GET /money` - list money records
- `POST /money` - create a money record

## Project Docs

- [Vision](docs/vision.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Agent Instructions](AGENTS.md)
