from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import TaskDB


router = APIRouter()


@router.get("/daily/briefing")
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
