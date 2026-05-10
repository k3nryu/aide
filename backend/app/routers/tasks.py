from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import TaskDB
from schemas import TaskCreate, TaskOut, TaskUpdate


router = APIRouter()


def _effective_task_values(values):
    recurrence = values.get("recurrence_natural") or values.get("recurrence_cron")
    importance = values.get("importance") or "medium"
    urgency = values.get("urgency") or "medium"
    due_date = values.get("due_date")
    prepare_days = values.get("recurrence_prepare_days")

    if recurrence and importance == "medium":
        importance = "high"

    if due_date and urgency != "high":
        notice_days = prepare_days if prepare_days is not None else 3
        if due_date <= date.today() + timedelta(days=notice_days):
            urgency = "high"

    if importance == "high" and urgency != "high":
        priority = "ultra"
    elif importance == "high" and urgency == "high":
        priority = "high"
    elif urgency == "high":
        priority = "medium"
    elif importance == "low" and urgency == "low":
        priority = "low"
    else:
        priority = "medium"

    effective_values = values.copy()
    effective_values["importance"] = importance
    effective_values["urgency"] = urgency
    effective_values["priority"] = priority
    return effective_values


def _completed_after(range_name: Optional[str]):
    if not range_name:
        return None
    today = datetime.utcnow()
    ranges = {
        "1d": timedelta(days=1),
        "3d": timedelta(days=3),
        "1w": timedelta(days=7),
        "1m": timedelta(days=31),
    }
    if range_name.endswith("y") and range_name[:-1].isdigit():
        return today - timedelta(days=365 * int(range_name[:-1]))
    if range_name not in ranges:
        return None
    return today - ranges[range_name]


@router.get("/tasks", response_model=List[TaskOut])
def list_tasks(
    done: Optional[bool] = None,
    context: Optional[str] = None,
    search: Optional[str] = None,
    completed_range: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(TaskDB)
    if done is not None:
        query = query.filter(TaskDB.done == done)
    if context:
        query = query.filter(TaskDB.context == context)
    if search:
        query = query.filter(TaskDB.title.ilike(f"%{search}%"))
    if done is True:
        query = query.order_by(TaskDB.completed_at.desc().nullslast(), TaskDB.created_at.desc())
    else:
        query = query.order_by(TaskDB.created_at.desc())
    items = query.all()
    after = _completed_after(completed_range)
    if after:
        items = [item for item in items if (item.completed_at or item.created_at) >= after]
    return items


@router.post("/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    item = TaskDB(**_effective_task_values(task.model_dump()))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    item = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    if item.type == "not_todo":
        raise HTTPException(status_code=400, detail="Not-to-do items cannot be completed")
    item.done = True
    item.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    item = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    values = task.model_dump(exclude_unset=True)
    current_values = {
        "title": item.title,
        "description": item.description,
        "type": item.type,
        "priority": item.priority,
        "importance": item.importance,
        "urgency": item.urgency,
        "context": item.context,
        "recurrence_natural": item.recurrence_natural,
        "recurrence_cron": item.recurrence_cron,
        "recurrence_prepare_days": item.recurrence_prepare_days,
        "advanced_format": item.advanced_format,
        "advanced_body": item.advanced_body,
        "due_date": item.due_date,
    }
    effective_values = _effective_task_values({**current_values, **values})
    for key in set(values) | {"priority", "importance", "urgency"}:
        value = effective_values[key]
        setattr(item, key, value)
    if item.type == "not_todo":
        item.done = False
        item.completed_at = None
    db.commit()
    db.refresh(item)
    return item
