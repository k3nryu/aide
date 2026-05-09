from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import Base, engine
from routers import activity_logs, daily, money, tasks, thoughts


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aide")
app.include_router(daily.router)
app.include_router(tasks.router)
app.include_router(thoughts.router)
app.include_router(activity_logs.router)
app.include_router(money.router)
app.mount("/app", StaticFiles(directory="static", html=True), name="app")


@app.get("/")
def root():
    return {"status": "ok", "app": "Aide"}
