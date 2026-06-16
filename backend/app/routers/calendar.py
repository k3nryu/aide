from datetime import date, datetime, time, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import CalendarEventDB
from schemas import CalendarEventCreate, CalendarEventOut, CalendarEventUpdate
from services import caldav_aide


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
    all_events: bool = False,
    db: Session = Depends(get_db),
):
    if caldav_aide.is_enabled():
        return caldav_aide.list_calendar_events(
            event_date=event_date,
            account_context=account_context,
            all_events=all_events,
        )
    if db is None:
        raise HTTPException(status_code=503, detail="No storage backend configured")
    query = db.query(CalendarEventDB)
    if not all_events:
        query = query.filter((CalendarEventDB.done == False) | (CalendarEventDB.done == None))
        target_date = event_date or date.today()
        start = datetime.combine(target_date, time.min)
        end = start + timedelta(days=1)
        query = query.filter(CalendarEventDB.starts_at >= start).filter(CalendarEventDB.starts_at < end)
    if account_context:
        query = query.filter(CalendarEventDB.account_context == account_context)
    return query.order_by(CalendarEventDB.starts_at.asc()).all()


@router.post("/calendar/events", response_model=CalendarEventOut)
def create_calendar_event(event: CalendarEventCreate, db: Session = Depends(get_db)):
    if caldav_aide.is_enabled():
        return caldav_aide.create_calendar_event(event.model_dump())
    if db is None:
        raise HTTPException(status_code=503, detail="No storage backend configured")
    item = CalendarEventDB(**event.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/calendar/events/{event_id}/complete", response_model=CalendarEventOut)
def complete_calendar_event(event_id: int, db: Session = Depends(get_db)):
    if caldav_aide.is_enabled():
        try:
            return caldav_aide.complete_calendar_event(event_id)
        except caldav_aide.CalDAVEventNotFound:
            raise HTTPException(status_code=404, detail="Calendar event not found")
    if db is None:
        raise HTTPException(status_code=503, detail="No storage backend configured")
    item = db.query(CalendarEventDB).filter(CalendarEventDB.id == event_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    item.done = True
    item.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item


@router.patch("/calendar/events/{event_id}", response_model=CalendarEventOut)
def update_calendar_event(event_id: int, event: CalendarEventUpdate, db: Session = Depends(get_db)):
    if caldav_aide.is_enabled():
        try:
            return caldav_aide.update_calendar_event(event_id, event.model_dump(exclude_unset=True))
        except caldav_aide.CalDAVEventNotFound:
            raise HTTPException(status_code=404, detail="Calendar event not found")
    if db is None:
        raise HTTPException(status_code=503, detail="No storage backend configured")
    item = db.query(CalendarEventDB).filter(CalendarEventDB.id == event_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    values = event.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item
