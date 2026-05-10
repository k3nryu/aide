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
    context: str = "personal"
    todo_kind: str = "one_time"
    recurrence_frequency: Optional[str] = None
    recurrence_calendar: Optional[str] = "solar"
    recurrence_month: Optional[int] = Field(default=None, ge=1, le=12)
    recurrence_day: Optional[int] = Field(default=None, ge=1, le=31)
    recurrence_weekdays: Optional[str] = None
    not_todo_group: Optional[str] = None
    recurrence_natural: Optional[str] = None
    recurrence_cron: Optional[str] = None
    recurrence_prepare_days: Optional[int] = Field(default=None, ge=0, le=365)
    advanced_format: Optional[str] = "markdown"
    advanced_body: Optional[str] = None
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    importance: Optional[str] = None
    urgency: Optional[str] = None
    context: Optional[str] = None
    todo_kind: Optional[str] = None
    recurrence_frequency: Optional[str] = None
    recurrence_calendar: Optional[str] = None
    recurrence_month: Optional[int] = Field(default=None, ge=1, le=12)
    recurrence_day: Optional[int] = Field(default=None, ge=1, le=31)
    recurrence_weekdays: Optional[str] = None
    not_todo_group: Optional[str] = None
    recurrence_natural: Optional[str] = None
    recurrence_cron: Optional[str] = None
    recurrence_prepare_days: Optional[int] = Field(default=None, ge=0, le=365)
    advanced_format: Optional[str] = None
    advanced_body: Optional[str] = None
    due_date: Optional[date] = None


class TaskOut(TaskCreate):
    id: int
    done: bool
    completed_at: Optional[datetime] = None
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


class CalendarEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    source: str = Field(default="manual", max_length=50)
    account_context: str = Field(default="personal", max_length=50)
    starts_at: datetime
    ends_at: Optional[datetime] = None
    location: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    external_id: Optional[str] = Field(default=None, max_length=255)


class CalendarEventOut(CalendarEventCreate):
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
