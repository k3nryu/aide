from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import CalendarEventDB, TaskDB


router = APIRouter()


@router.get("/daily/briefing")
def daily_briefing(db: Session = Depends(get_db)):
    today = date.today()
    start = datetime.combine(today, time.min)
    end = start + timedelta(days=1)
    tasks = (
        db.query(TaskDB)
        .filter(TaskDB.done == False)
        .filter(TaskDB.type != "not_todo")
        .filter((TaskDB.due_date == today) | (TaskDB.due_date == None))
        .order_by(TaskDB.created_at.desc())
        .limit(5)
        .all()
    )
    not_todos = (
        db.query(TaskDB)
        .filter(TaskDB.type == "not_todo")
        .order_by(TaskDB.created_at.desc())
        .limit(5)
        .all()
    )
    meetings = (
        db.query(CalendarEventDB)
        .filter(CalendarEventDB.starts_at >= start)
        .filter(CalendarEventDB.starts_at < end)
        .order_by(CalendarEventDB.starts_at.asc())
        .limit(8)
        .all()
    )
    return {
        "date": str(today),
        "message": "Today's briefing from Aide.",
        "tasks": tasks,
        "not_todos": not_todos,
        "meetings": meetings,
    }
