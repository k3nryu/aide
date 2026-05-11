import re
from calendar import monthrange
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import CalendarEventDB, TaskDB


router = APIRouter()


def _is_recurring_task(task: TaskDB):
    return task.todo_kind == "recurring" or task.recurrence_frequency or task.recurrence_natural


def _weekday_indexes(text: str):
    source = text or ""
    labels = [
        ("日", 0),
        ("天", 0),
        ("一", 1),
        ("二", 2),
        ("三", 3),
        ("四", 4),
        ("五", 5),
        ("六", 6),
    ]
    values = []
    for label, index in labels:
        if f"周{label}" in source or f"星期{label}" in source or f"礼拜{label}" in source:
            values.append(index)
    for value in re.findall(r"\b[0-6]\b", source):
        index = int(value)
        if index not in values:
            values.append(index)
    return values


def _next_monthly_date(today: date, day_value):
    if not day_value:
        return None
    day = int(day_value)
    this_month_day = min(day, monthrange(today.year, today.month)[1])
    this_month = date(today.year, today.month, this_month_day)
    if this_month >= today:
        return this_month
    next_month = today.month + 1
    year = today.year
    if next_month > 12:
        next_month = 1
        year += 1
    next_month_day = min(day, monthrange(year, next_month)[1])
    return date(year, next_month, next_month_day)


def _next_yearly_date(today: date, month_value, day_value):
    if not month_value or not day_value:
        return None
    month = int(month_value)
    day = int(day_value)
    this_year_day = min(day, monthrange(today.year, month)[1])
    this_year = date(today.year, month, this_year_day)
    if this_year >= today:
        return this_year
    next_year_day = min(day, monthrange(today.year + 1, month)[1])
    return date(today.year + 1, month, next_year_day)


def _next_recurring_occurrence(task: TaskDB, today: date):
    if not _is_recurring_task(task):
        return None
    if task.recurrence_frequency == "daily":
        return today
    if task.recurrence_frequency == "weekly":
        weekdays = _weekday_indexes(f"{task.recurrence_weekdays or ''} {task.recurrence_natural or ''}")
        if not weekdays:
            return None
        today_weekday = (today.weekday() + 1) % 7
        next_offset = min((weekday - today_weekday + 7) % 7 for weekday in weekdays)
        return today + timedelta(days=next_offset)
    if task.recurrence_frequency == "monthly":
        return _next_monthly_date(today, task.recurrence_day)
    if task.recurrence_frequency == "yearly":
        return _next_yearly_date(today, task.recurrence_month, task.recurrence_day)
    return None


def _recurrence_notice_days(task: TaskDB):
    if task.recurrence_frequency == "yearly":
        return 14
    if task.recurrence_frequency == "monthly":
        return 3
    if task.recurrence_frequency == "weekly":
        return 1
    return 0


def _is_recurring_in_attention_window(task: TaskDB, today: date):
    if not _is_recurring_task(task):
        return False
    if task.due_date and (task.due_date - today).days <= 3:
        return True
    next_date = _next_recurring_occurrence(task, today)
    if not next_date:
        return False
    days_left = (next_date - today).days
    return 0 <= days_left <= _recurrence_notice_days(task)


def _should_show_today(task: TaskDB, today: date):
    if task.type == "not_todo" or task.done:
        return False
    if _is_recurring_task(task):
        return _is_recurring_in_attention_window(task, today)
    if task.due_date:
        return task.due_date <= today
    return task.created_at and task.created_at.date() == today


@router.get("/daily/briefing")
def daily_briefing(db: Session = Depends(get_db)):
    today = date.today()
    start = datetime.combine(today, time.min)
    end = start + timedelta(days=1)
    tasks = (
        db.query(TaskDB)
        .filter(TaskDB.done == False)
        .filter(TaskDB.type != "not_todo")
        .order_by(TaskDB.created_at.desc())
        .all()
    )
    tasks = [task for task in tasks if _should_show_today(task, today)][:5]
    meetings = (
        db.query(CalendarEventDB)
        .filter((CalendarEventDB.done == False) | (CalendarEventDB.done == None))
        .filter(CalendarEventDB.starts_at >= start)
        .filter(CalendarEventDB.starts_at < end)
        .order_by(CalendarEventDB.starts_at.asc())
        .limit(8)
        .all()
    )
    return {
        "date": str(today),
        "message": "Today's briefing from Aide.",
        "tasks": tasks,
        "meetings": meetings,
    }
