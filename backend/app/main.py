from fastapi import FastAPI

from database import Base, engine
from routers import daily, money, tasks, thoughts


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aide")
app.include_router(daily.router)
app.include_router(tasks.router)
app.include_router(thoughts.router)
app.include_router(money.router)


@app.get("/")
def root():
    return {"status": "ok", "app": "Aide"}
