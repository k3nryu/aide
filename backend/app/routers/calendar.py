from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from schemas import CalendarEventOut
from services import caldav_aide


router = APIRouter()


@router.get("/calendar/sources")
def calendar_sources():
    return {
        "sources": [
            {"name": "Google Calendar", "key": "google", "status": "planned_oauth"},
            {"name": "Apple Calendar", "key": "apple", "status": "planned_ics_or_caldav"},
            {"name": "Outlook Calendar", "key": "outlook", "status": "planned_oauth"},
            {"name": "Manual import", "key": "manual", "status": "removed_use_caldav"},
        ]
    }


@router.get("/calendar/events", response_model=List[CalendarEventOut])
def list_calendar_events(
    event_date: Optional[date] = None,
    account_context: Optional[str] = None,
    all_events: bool = False,
):
    if not caldav_aide.is_enabled():
        raise HTTPException(status_code=503, detail="CalDAV storage is not configured")

    return caldav_aide.list_calendar_events(
        event_date=event_date,
        account_context=account_context,
        all_events=all_events,
    )


@router.post("/calendar/events/{event_id}/complete", response_model=CalendarEventOut)
def complete_calendar_event(event_id: int):
    if not caldav_aide.is_enabled():
        raise HTTPException(status_code=503, detail="CalDAV storage is not configured")

    try:
        return caldav_aide.complete_calendar_event(event_id)
    except caldav_aide.CalDAVEventNotFound:
        raise HTTPException(status_code=404, detail="Calendar event not found")
