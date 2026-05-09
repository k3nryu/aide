from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import ThoughtDB
from schemas import ThoughtCreate, ThoughtOut


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
