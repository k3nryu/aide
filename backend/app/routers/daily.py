import json
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


def _is_recurring_event(event: CalendarEventDB):
    return event.event_kind == "recurring" or event.recurrence_frequency or event.recurrence_natural


def _is_recurring_item(item):
    return (
        getattr(item, "todo_kind", None) == "recurring"
        or getattr(item, "event_kind", None) == "recurring"
        or getattr(item, "recurrence_frequency", None)
        or getattr(item, "recurrence_natural", None)
    )


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


def _recurrence_rule(item):
    if not item.recurrence_rule:
        return {}
    try:
        value = json.loads(item.recurrence_rule)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _rule_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


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


def _next_recurring_occurrence(item, today: date):
    if not _is_recurring_item(item):
        return None
    rule = _recurrence_rule(item)
    start_date = _rule_date(rule.get("start_date"))
    end_date = _rule_date(rule.get("end_date"))
    base_date = max(today, start_date) if start_date else today
    if end_date and base_date > end_date:
        return None
    if item.recurrence_frequency == "daily":
        return base_date
    if item.recurrence_frequency == "weekly":
        weekdays = _weekday_indexes(f"{item.recurrence_weekdays or ''} {item.recurrence_natural or ''}")
        if not weekdays:
            return None
        today_weekday = (base_date.weekday() + 1) % 7
        next_offset = min((weekday - today_weekday + 7) % 7 for weekday in weekdays)
        next_date = base_date + timedelta(days=next_offset)
        return None if end_date and next_date > end_date else next_date
    if item.recurrence_frequency == "monthly":
        next_date = _next_monthly_date(base_date, item.recurrence_day)
        return None if end_date and next_date and next_date > end_date else next_date
    if item.recurrence_frequency == "yearly":
        next_date = _next_yearly_date(base_date, item.recurrence_month, item.recurrence_day)
        return None if end_date and next_date and next_date > end_date else next_date
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
    if task.starts_at and task.starts_at.date() == today:
        return True
    if _is_recurring_task(task):
        return _is_recurring_in_attention_window(task, today)
    if task.available_date:
        return task.available_date <= today
    if task.due_date:
        return task.due_date <= today
    return task.created_at and task.created_at.date() == today


def _event_occurs_today(event: CalendarEventDB, today: date):
    if event.done:
        return False
    if not _is_recurring_event(event):
        return event.starts_at and event.starts_at.date() == today
    next_date = _next_recurring_occurrence(event, today)
    return next_date == today


def _apply_today_event_time(event: CalendarEventDB, today: date):
    if not _is_recurring_event(event) or not event.starts_at:
        return event
    rule = _recurrence_rule(event)
    start_time = event.starts_at.time()
    if rule.get("start_time"):
        try:
            start_time = time.fromisoformat(rule["start_time"])
        except ValueError:
            pass
    duration_minutes = rule.get("duration_minutes")
    if not duration_minutes and event.ends_at:
        duration_minutes = int((event.ends_at - event.starts_at).total_seconds() // 60)
    event.starts_at = datetime.combine(today, start_time)
    if duration_minutes:
        event.ends_at = event.starts_at + timedelta(minutes=int(duration_minutes))
    return event


@router.get("/daily/briefing")
def daily_briefing(db: Session = Depends(get_db)):
    today = date.today()
    tasks = (
        db.query(TaskDB)
        .filter(TaskDB.done == False)
        .filter(TaskDB.type != "not_todo")
        .order_by(TaskDB.created_at.desc())
        .all()
    )
    tasks = [task for task in tasks if _should_show_today(task, today)][:5]
    meeting_items = (
        db.query(CalendarEventDB)
        .filter((CalendarEventDB.done == False) | (CalendarEventDB.done == None))
        .order_by(CalendarEventDB.starts_at.asc())
        .all()
    )
    meetings = [_apply_today_event_time(event, today) for event in meeting_items if _event_occurs_today(event, today)][:8]
    return {
        "date": str(today),
        "message": "Today's briefing from Aide.",
        "tasks": tasks,
        "meetings": meetings,
    }
