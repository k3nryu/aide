from types import SimpleNamespace
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ThoughtDB
from schemas import ThoughtCreate, ThoughtOut, ThoughtTaskSuggestionOut
from services import caldav_aide
from services.ai_assist import suggest_tasks_from_thought


router = APIRouter()


@router.post("/thoughts", response_model=ThoughtOut)
def create_thought(thought: ThoughtCreate, db: Session = Depends(get_db)):
    if caldav_aide.is_enabled():
        return caldav_aide.create_thought(thought.model_dump())
    if db is None:
        raise HTTPException(status_code=503, detail="No storage backend configured")
    item = ThoughtDB(**thought.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/thoughts", response_model=List[ThoughtOut])
def list_thoughts(db: Session = Depends(get_db)):
    if caldav_aide.is_enabled():
        return caldav_aide.list_thoughts()
    if db is None:
        raise HTTPException(status_code=503, detail="No storage backend configured")
    return db.query(ThoughtDB).order_by(ThoughtDB.created_at.desc()).all()


@router.post("/thoughts/{thought_id}/task-suggestions", response_model=ThoughtTaskSuggestionOut)
def suggest_thought_tasks(thought_id: int, db: Session = Depends(get_db)):
    if caldav_aide.is_enabled():
        try:
            thought = SimpleNamespace(**caldav_aide.get_thought(thought_id))
        except caldav_aide.CalDAVJournalNotFound:
            raise HTTPException(status_code=404, detail="Thought not found")
    else:
        if db is None:
            raise HTTPException(status_code=503, detail="No storage backend configured")
        thought = db.query(ThoughtDB).filter(ThoughtDB.id == thought_id).first()
        if not thought:
            raise HTTPException(status_code=404, detail="Thought not found")
    return suggest_tasks_from_thought(thought)
