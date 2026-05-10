from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str = "todo"
    priority: str = "medium"
    importance: str = "medium"
    urgency: str = "medium"
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


class ActivityLogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    note: Optional[str] = None
    occurred_at: Optional[datetime] = None


class ActivityLogOut(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    note: Optional[str] = None
    occurred_at: datetime
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
