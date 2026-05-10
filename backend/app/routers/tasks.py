from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import TaskDB
from schemas import TaskCreate, TaskOut, TaskUpdate


router = APIRouter()


@router.get("/tasks", response_model=List[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(TaskDB).order_by(TaskDB.created_at.desc()).all()


@router.post("/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    item = TaskDB(**task.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    item = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    item.done = True
    db.commit()
    db.refresh(item)
    return item


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    item = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item
