import os
from datetime import datetime, date
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Date, Numeric
from sqlalchemy.orm import sessionmaker, declarative_base, Session

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI(title="Aide")


class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), default="todo")  # todo / not_todo
    priority = Column(String(50), default="medium")
    done = Column(Boolean, default=False)
    due_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)


class ThoughtDB(Base):
    __tablename__ = "thoughts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    tag = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class MoneyRecordDB(Base):
    __tablename__ = "money_records"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(50), nullable=False)  # income / expense
    category = Column(String(100))
    note = Column(Text)
    record_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str = "todo"
    priority: str = "medium"
    due_date: Optional[date] = None


class TaskOut(TaskCreate):
    id: int
    done: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ThoughtCreate(BaseModel):
    content: str
    tag: Optional[str] = None


class ThoughtOut(ThoughtCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MoneyCreate(BaseModel):
    title: str
    amount: float
    type: str
    category: Optional[str] = None
    note: Optional[str] = None
    record_date: Optional[date] = None


class MoneyOut(MoneyCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"status": "ok", "app": "Aide"}


@app.get("/daily/briefing")
def daily_briefing(db: Session = Depends(get_db)):
    today = date.today()
    tasks = (
        db.query(TaskDB)
        .filter(TaskDB.done == False)
        .filter((TaskDB.due_date == today) | (TaskDB.due_date == None))
        .order_by(TaskDB.created_at.desc())
        .limit(5)
        .all()
    )
    not_todos = (
        db.query(TaskDB)
        .filter(TaskDB.type == "not_todo")
        .filter(TaskDB.done == False)
        .order_by(TaskDB.created_at.desc())
        .limit(5)
        .all()
    )
    return {
        "date": str(today),
        "message": "Today's briefing from Aide.",
        "tasks": tasks,
        "not_todos": not_todos,
    }


@app.get("/tasks", response_model=List[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(TaskDB).order_by(TaskDB.created_at.desc()).all()


@app.post("/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    item = TaskDB(**task.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    item = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    item.done = True
    db.commit()
    db.refresh(item)
    return item


@app.post("/thoughts", response_model=ThoughtOut)
def create_thought(thought: ThoughtCreate, db: Session = Depends(get_db)):
    item = ThoughtDB(**thought.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/thoughts", response_model=List[ThoughtOut])
def list_thoughts(db: Session = Depends(get_db)):
    return db.query(ThoughtDB).order_by(ThoughtDB.created_at.desc()).all()


@app.post("/money", response_model=MoneyOut)
def create_money_record(record: MoneyCreate, db: Session = Depends(get_db)):
    data = record.model_dump()
    if data["record_date"] is None:
        data["record_date"] = date.today()
    item = MoneyRecordDB(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/money", response_model=List[MoneyOut])
def list_money_records(db: Session = Depends(get_db)):
    return db.query(MoneyRecordDB).order_by(MoneyRecordDB.record_date.desc()).all()
