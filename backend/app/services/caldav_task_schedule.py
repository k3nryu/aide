from datetime import datetime, timedelta

from services.caldav_ical import build_vevent, recurrence_payload, recurrence_start


def sync_task_schedule_event(task):
    from services.caldav_store import put_calendar_object

    if not _is_recurring(task):
        return None

    uid = f"aide-task-schedule-{task['id']}@aide.local"
    metadata = {
        "id": task["id"],
        "task_id": task["id"],
        "source_uid": task.get("advanced_body"),
        "title": task["title"],
        "description": task.get("description"),
        "context": task.get("context"),
        "importance": task.get("importance"),
        "urgency": task.get("urgency"),
        "recurrence_frequency": task.get("recurrence_frequency"),
        "recurrence_calendar": task.get("recurrence_calendar"),
        "recurrence_month": task.get("recurrence_month"),
        "recurrence_day": task.get("recurrence_day"),
        "recurrence_weekdays": task.get("recurrence_weekdays"),
        "recurrence_rule": task.get("recurrence_rule"),
        "recurrence_natural": task.get("recurrence_natural"),
        "starts_at": _iso(task.get("starts_at")),
        "ends_at": _iso(task.get("ends_at")),
        "created_at": _iso(task.get("created_at")),
    }

    all_day = task.get("starts_at") is None
    starts_at = task.get("starts_at") or recurrence_start(metadata, default=task.get("available_date") or task.get("created_at"), as_datetime=True)
    ends_at = task.get("ends_at") or (starts_at + timedelta(hours=1) if starts_at and not all_day else None)
    if starts_at is None:
        starts_at = datetime.utcnow()

    ics = build_vevent(
        uid=uid,
        summary=task["title"],
        starts_at=starts_at,
        ends_at=ends_at,
        created_at=task.get("created_at") or datetime.utcnow(),
        description=task.get("description"),
        categories=["AIDE", "TASK_SCHEDULE", _tag(task.get("context"))],
        aide_type="task_schedule",
        aide_id=task["id"],
        metadata=metadata,
        recurrence=recurrence_payload(metadata),
        all_day=all_day,
    )
    put_calendar_object("VEVENT", uid, ics)
    return uid


def _is_recurring(task):
    return bool(task.get("todo_kind") == "recurring" or task.get("recurrence_frequency") or task.get("recurrence_natural"))


def _iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _tag(value):
    if not value:
        return None
    return str(value).strip().replace(" ", "_").replace("-", "_").upper()
