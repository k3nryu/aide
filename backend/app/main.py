from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from database import Base, engine
from routers import activity_logs, calendar, daily, money, tasks, thoughts


Base.metadata.create_all(bind=engine)


def sync_prototype_schema():
    inspector = inspect(engine)
    if "tasks" not in inspector.get_table_names():
        return
    task_columns = {column["name"] for column in inspector.get_columns("tasks")}
    columns_to_add = {
        "importance": "ALTER TABLE tasks ADD COLUMN importance VARCHAR(50) DEFAULT 'medium'",
        "urgency": "ALTER TABLE tasks ADD COLUMN urgency VARCHAR(50) DEFAULT 'medium'",
        "context": "ALTER TABLE tasks ADD COLUMN context VARCHAR(50) DEFAULT 'personal'",
        "recurrence_natural": "ALTER TABLE tasks ADD COLUMN recurrence_natural TEXT",
        "recurrence_cron": "ALTER TABLE tasks ADD COLUMN recurrence_cron VARCHAR(120)",
        "recurrence_prepare_days": "ALTER TABLE tasks ADD COLUMN recurrence_prepare_days INTEGER",
        "advanced_format": "ALTER TABLE tasks ADD COLUMN advanced_format VARCHAR(50) DEFAULT 'markdown'",
        "advanced_body": "ALTER TABLE tasks ADD COLUMN advanced_body TEXT",
        "completed_at": "ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP",
    }
    with engine.begin() as connection:
        for column_name, statement in columns_to_add.items():
            if column_name not in task_columns:
                connection.execute(text(statement))


sync_prototype_schema()

app = FastAPI(title="Aide")


@app.middleware("http")
async def no_cache_app_static(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/app"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(daily.router)
app.include_router(tasks.router)
app.include_router(calendar.router)
app.include_router(thoughts.router)
app.include_router(activity_logs.router)
app.include_router(money.router)
app.mount("/app", StaticFiles(directory="static", html=True), name="app")


@app.get("/")
def root():
    return {"status": "ok", "app": "Aide"}
