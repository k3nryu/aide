from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from database import Base, engine
from routers import activity_logs, calendar, daily, money, tasks, thoughts


Base.metadata.create_all(bind=engine)


def sync_prototype_schema():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "tasks" not in table_names:
        return
    task_columns = {column["name"] for column in inspector.get_columns("tasks")}
    columns_to_add = {
        "importance": "ALTER TABLE tasks ADD COLUMN importance VARCHAR(50) DEFAULT 'medium'",
        "urgency": "ALTER TABLE tasks ADD COLUMN urgency VARCHAR(50) DEFAULT 'medium'",
        "context": "ALTER TABLE tasks ADD COLUMN context VARCHAR(50) DEFAULT 'personal'",
        "todo_kind": "ALTER TABLE tasks ADD COLUMN todo_kind VARCHAR(50) DEFAULT 'one_time'",
        "recurrence_frequency": "ALTER TABLE tasks ADD COLUMN recurrence_frequency VARCHAR(50)",
        "recurrence_calendar": "ALTER TABLE tasks ADD COLUMN recurrence_calendar VARCHAR(50) DEFAULT 'solar'",
        "recurrence_month": "ALTER TABLE tasks ADD COLUMN recurrence_month INTEGER",
        "recurrence_day": "ALTER TABLE tasks ADD COLUMN recurrence_day INTEGER",
        "recurrence_weekdays": "ALTER TABLE tasks ADD COLUMN recurrence_weekdays VARCHAR(100)",
        "recurrence_rule": "ALTER TABLE tasks ADD COLUMN recurrence_rule TEXT",
        "not_todo_group": "ALTER TABLE tasks ADD COLUMN not_todo_group VARCHAR(50)",
        "recurrence_natural": "ALTER TABLE tasks ADD COLUMN recurrence_natural TEXT",
        "recurrence_cron": "ALTER TABLE tasks ADD COLUMN recurrence_cron VARCHAR(120)",
        "recurrence_prepare_days": "ALTER TABLE tasks ADD COLUMN recurrence_prepare_days INTEGER",
        "advanced_format": "ALTER TABLE tasks ADD COLUMN advanced_format VARCHAR(50) DEFAULT 'markdown'",
        "advanced_body": "ALTER TABLE tasks ADD COLUMN advanced_body TEXT",
        "completed_at": "ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP",
        "available_date": "ALTER TABLE tasks ADD COLUMN available_date DATE",
        "starts_at": "ALTER TABLE tasks ADD COLUMN starts_at TIMESTAMP",
        "ends_at": "ALTER TABLE tasks ADD COLUMN ends_at TIMESTAMP",
        "location": "ALTER TABLE tasks ADD COLUMN location VARCHAR(255)",
        "source": "ALTER TABLE tasks ADD COLUMN source VARCHAR(50) DEFAULT 'manual'",
    }
    with engine.begin() as connection:
        for column_name, statement in columns_to_add.items():
            if column_name not in task_columns:
                connection.execute(text(statement))
    if "calendar_events" in inspector.get_table_names():
        calendar_columns = {column["name"] for column in inspector.get_columns("calendar_events")}
        calendar_columns_to_add = {
            "importance": "ALTER TABLE calendar_events ADD COLUMN importance VARCHAR(50) DEFAULT 'high'",
            "event_kind": "ALTER TABLE calendar_events ADD COLUMN event_kind VARCHAR(50) DEFAULT 'one_time'",
            "recurrence_frequency": "ALTER TABLE calendar_events ADD COLUMN recurrence_frequency VARCHAR(50)",
            "recurrence_calendar": "ALTER TABLE calendar_events ADD COLUMN recurrence_calendar VARCHAR(50) DEFAULT 'solar'",
            "recurrence_month": "ALTER TABLE calendar_events ADD COLUMN recurrence_month INTEGER",
            "recurrence_day": "ALTER TABLE calendar_events ADD COLUMN recurrence_day INTEGER",
            "recurrence_weekdays": "ALTER TABLE calendar_events ADD COLUMN recurrence_weekdays VARCHAR(100)",
            "recurrence_natural": "ALTER TABLE calendar_events ADD COLUMN recurrence_natural TEXT",
            "recurrence_rule": "ALTER TABLE calendar_events ADD COLUMN recurrence_rule TEXT",
            "done": "ALTER TABLE calendar_events ADD COLUMN done BOOLEAN DEFAULT FALSE",
            "completed_at": "ALTER TABLE calendar_events ADD COLUMN completed_at TIMESTAMP",
        }
        with engine.begin() as connection:
            for column_name, statement in calendar_columns_to_add.items():
                if column_name not in calendar_columns:
                    connection.execute(text(statement))
    if "activity_logs" in table_names:
        activity_columns = {column["name"] for column in inspector.get_columns("activity_logs")}
        activity_columns_to_add = {
            "sop_model": "ALTER TABLE activity_logs ADD COLUMN sop_model VARCHAR(50) DEFAULT 'pdca'",
            "plan": "ALTER TABLE activity_logs ADD COLUMN plan TEXT",
            "result": "ALTER TABLE activity_logs ADD COLUMN result TEXT",
            "learning": "ALTER TABLE activity_logs ADD COLUMN learning TEXT",
            "next_action": "ALTER TABLE activity_logs ADD COLUMN next_action TEXT",
            "energy_level": "ALTER TABLE activity_logs ADD COLUMN energy_level INTEGER",
        }
        with engine.begin() as connection:
            for column_name, statement in activity_columns_to_add.items():
                if column_name not in activity_columns:
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
