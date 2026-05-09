from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str = "todo"
    priority: str = "medium"
    due_date: Optional[date] = None


class TaskOut(TaskCreate):
    id: int
    done: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ThoughtCreate(BaseModel):
    content: str
    tag: Optional[str] = None


class ThoughtOut(ThoughtCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MoneyCreate(BaseModel):
    title: str
    amount: float
    type: str
    category: Optional[str] = None
    note: Optional[str] = None
    record_date: Optional[date] = None


class MoneyOut(MoneyCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
