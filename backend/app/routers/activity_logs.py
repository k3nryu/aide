from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import ActivityLogDB
from schemas import ActivityLogCreate, ActivityLogOut


router = APIRouter()


@router.post("/activity-logs", response_model=ActivityLogOut)
def create_activity_log(log: ActivityLogCreate, db: Session = Depends(get_db)):
    data = log.model_dump()
    if data["occurred_at"] is None:
        data["occurred_at"] = datetime.utcnow()
    item = ActivityLogDB(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/activity-logs", response_model=List[ActivityLogOut])
def list_activity_logs(db: Session = Depends(get_db)):
    return db.query(ActivityLogDB).order_by(ActivityLogDB.occurred_at.desc()).all()
