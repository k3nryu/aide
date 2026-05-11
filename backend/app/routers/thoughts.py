from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ThoughtDB
from schemas import ThoughtCreate, ThoughtOut, ThoughtTaskSuggestionOut
from services.ai_assist import suggest_tasks_from_thought


router = APIRouter()


@router.post("/thoughts", response_model=ThoughtOut)
def create_thought(thought: ThoughtCreate, db: Session = Depends(get_db)):
    item = ThoughtDB(**thought.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/thoughts", response_model=List[ThoughtOut])
def list_thoughts(db: Session = Depends(get_db)):
    return db.query(ThoughtDB).order_by(ThoughtDB.created_at.desc()).all()


@router.post("/thoughts/{thought_id}/task-suggestions", response_model=ThoughtTaskSuggestionOut)
def suggest_thought_tasks(thought_id: int, db: Session = Depends(get_db)):
    thought = db.query(ThoughtDB).filter(ThoughtDB.id == thought_id).first()
    if not thought:
        raise HTTPException(status_code=404, detail="Thought not found")
    return suggest_tasks_from_thought(thought)
