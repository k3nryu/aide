from datetime import date, datetime, time, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import CalendarEventDB
from schemas import CalendarEventCreate, CalendarEventOut


router = APIRouter()


@router.get("/calendar/sources")
def calendar_sources():
    return {
        "sources": [
            {"name": "Google Calendar", "key": "google", "status": "planned_oauth"},
            {"name": "Apple Calendar", "key": "apple", "status": "planned_ics_or_caldav"},
            {"name": "Outlook Calendar", "key": "outlook", "status": "planned_oauth"},
            {"name": "Manual import", "key": "manual", "status": "available"},
        ]
    }


@router.get("/calendar/events", response_model=List[CalendarEventOut])
def list_calendar_events(
    event_date: Optional[date] = None,
    account_context: Optional[str] = None,
    db: Session = Depends(get_db),
):
    target_date = event_date or date.today()
    start = datetime.combine(target_date, time.min)
    end = start + timedelta(days=1)
    query = db.query(CalendarEventDB).filter(CalendarEventDB.starts_at >= start).filter(CalendarEventDB.starts_at < end)
    if account_context:
        query = query.filter(CalendarEventDB.account_context == account_context)
    return query.order_by(CalendarEventDB.starts_at.asc()).all()


@router.post("/calendar/events", response_model=CalendarEventOut)
def create_calendar_event(event: CalendarEventCreate, db: Session = Depends(get_db)):
    item = CalendarEventDB(**event.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
