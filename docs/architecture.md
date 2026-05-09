# Architecture

Aide is currently a backend-first FastAPI application with a PostgreSQL-compatible relational database.

The repository is intentionally small. Most implementation details live in `backend/app/main.py` while the prototype is still early.

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

Location: `backend/app/main.py`

Responsibilities:

- Create the FastAPI app
- Configure the SQLAlchemy engine from `DATABASE_URL`
- Provide database sessions through FastAPI dependencies
- Define ORM models
- Define Pydantic schemas
- Expose HTTP routes

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

## Future Architecture

As the project grows, the backend should likely split into:

```text
backend/app/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── routers/
│   ├── daily.py
│   ├── tasks.py
│   ├── thoughts.py
│   └── money.py
└── services/
```

Planned future components:

- Web frontend
- Authentication
- Alembic migrations
- AI summary service
- Embedding generation
- Qdrant vector store
- Retrieval layer for personal memory
