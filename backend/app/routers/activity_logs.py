from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import ActivityLogDB, TaskDB
from schemas import ActivityAnalysisOut, ActivityLogCreate, ActivityLogOut
from services.ai_assist import build_pdca_stow_analysis


router = APIRouter()


@router.post("/activity-logs", response_model=ActivityLogOut)
def create_activity_log(log: ActivityLogCreate, db: Session = Depends(get_db)):
    data = log.model_dump()
    if data["occurred_at"] is None:
        data["occurred_at"] = datetime.utcnow()
    data["sop_model"] = data.get("sop_model") or "pdca"
    item = ActivityLogDB(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/activity-logs", response_model=List[ActivityLogOut])
def list_activity_logs(db: Session = Depends(get_db)):
    return db.query(ActivityLogDB).order_by(ActivityLogDB.occurred_at.desc()).all()


@router.get("/activity-logs/analysis", response_model=ActivityAnalysisOut)
def analyze_activity_logs(db: Session = Depends(get_db)):
    activity_items = db.query(ActivityLogDB).order_by(ActivityLogDB.occurred_at.desc()).limit(100).all()
    completed_tasks = (
        db.query(TaskDB)
        .filter(TaskDB.done == True)
        .filter(TaskDB.type != "not_todo")
        .order_by(TaskDB.completed_at.desc().nullslast(), TaskDB.created_at.desc())
        .limit(100)
        .all()
    )
    return build_pdca_stow_analysis(activity_items, completed_tasks)
