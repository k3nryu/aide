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
- exposes the backend on `127.0.0.1:8000`
- loads environment variables from `.env`

## Data Model

### `tasks`

Stores todos and not-todos.

Important fields:

- `title`
- `description`
- `type`
- `priority`
- `done`
- `due_date`
- `created_at`

The `type` field currently distinguishes `todo` from `not_todo`.

### `thoughts`

Stores captured thoughts and notes.

Important fields:

- `content`
- `tag`
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
- `POST /tasks/{task_id}/complete`
- `GET /thoughts`
- `POST /thoughts`
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
