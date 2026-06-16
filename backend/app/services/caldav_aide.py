import uuid
import zlib
from datetime import date, datetime, time, timedelta

from services import caldav_tasks
from services.caldav_ical import build_vjournal, compact_summary, description_from_sections
from services.caldav_store import list_calendar_objects, put_calendar_object


JOURNAL_ID_OFFSET = 2_000_000_000
EVENT_ID_OFFSET = 3_000_000_000


class CalDAVJournalNotFound(RuntimeError):
    pass


class CalDAVEventNotFound(RuntimeError):
    pass


def is_enabled():
    return caldav_tasks.is_enabled()


def list_thoughts():
    items = [_thought_from_journal(obj) for obj in _list_journal_type("thought")]
    return sorted(items, key=lambda item: item["created_at"], reverse=True)


def get_thought(thought_id: int):
    for obj in _list_journal_type("thought"):
        item = _thought_from_journal(obj)
        if item["id"] == thought_id:
            return item
    raise CalDAVJournalNotFound("Thought not found")


def create_thought(payload):
    created_at = datetime.utcnow()
    uid = _new_uid("thought")
    item_id = _journal_id(uid)
    metadata = {
        "id": item_id,
        "content": payload["content"],
        "tag": payload.get("tag"),
        "created_at": created_at.isoformat(),
    }
    ics = build_vjournal(
        uid=uid,
        summary=compact_summary("Thought: ", payload["content"]),
        occurred_at=created_at,
        created_at=created_at,
        description=description_from_sections(("Content", payload["content"]), ("Tag", payload.get("tag"))),
        categories=["AIDE", "THOUGHT", _tag(payload.get("tag"))],
        aide_type="thought",
        aide_id=item_id,
        metadata=metadata,
    )
    put_calendar_object("VJOURNAL", uid, ics)
    return {
        "id": item_id,
        "content": payload["content"],
        "tag": payload.get("tag"),
        "created_at": created_at,
    }


def list_activity_logs():
    items = [_activity_from_journal(obj) for obj in _list_journal_type("activity_log")]
    return sorted(items, key=lambda item: item["occurred_at"], reverse=True)


def create_activity_log(payload):
    created_at = datetime.utcnow()
    occurred_at = payload.get("occurred_at") or created_at
    sop_model = payload.get("sop_model") or "pdca"
    uid = _new_uid("activity")
    item_id = _journal_id(uid)
    metadata = {
        "id": item_id,
        "title": payload["title"],
        "category": payload.get("category"),
        "note": payload.get("note"),
        "sop_model": sop_model,
        "plan": payload.get("plan"),
        "result": payload.get("result"),
        "learning": payload.get("learning"),
        "next_action": payload.get("next_action"),
        "energy_level": payload.get("energy_level"),
        "occurred_at": occurred_at.isoformat(),
        "created_at": created_at.isoformat(),
    }
    ics = build_vjournal(
        uid=uid,
        summary=compact_summary("Activity: ", payload["title"]),
        occurred_at=occurred_at,
        created_at=created_at,
        description=description_from_sections(
            ("Title", payload["title"]),
            ("Note", payload.get("note")),
            ("Plan", payload.get("plan")),
            ("Result", payload.get("result")),
            ("Learning", payload.get("learning")),
            ("Next action", payload.get("next_action")),
        ),
        categories=["AIDE", "ACTIVITY", _tag(payload.get("category")), _tag(sop_model)],
        aide_type="activity_log",
        aide_id=item_id,
        metadata=metadata,
    )
    put_calendar_object("VJOURNAL", uid, ics)
    return _activity_from_metadata(metadata)


def list_money_records():
    items = [_money_from_journal(obj) for obj in _list_journal_type("money_record")]
    return sorted(items, key=lambda item: item["record_date"], reverse=True)


def create_money_record(payload):
    created_at = datetime.utcnow()
    record_date = payload.get("record_date") or date.today()
    uid = _new_uid("money")
    item_id = _journal_id(uid)
    metadata = {
        "id": item_id,
        "title": payload["title"],
        "amount": payload["amount"],
        "type": payload["type"],
        "category": payload.get("category"),
        "note": payload.get("note"),
        "record_date": record_date.isoformat(),
        "created_at": created_at.isoformat(),
    }
    ics = build_vjournal(
        uid=uid,
        summary=compact_summary(f"{payload['type'].title()}: ", payload["title"]),
        occurred_at=record_date,
        created_at=created_at,
        description=description_from_sections(
            ("Title", payload["title"]),
            ("Type", payload["type"]),
            ("Amount", payload["amount"]),
            ("Category", payload.get("category")),
            ("Note", payload.get("note")),
        ),
        categories=["AIDE", "MONEY", _tag(payload["type"]), _tag(payload.get("category"))],
        aide_type="money_record",
        aide_id=item_id,
        metadata=metadata,
    )
    put_calendar_object("VJOURNAL", uid, ics)
    return _money_from_metadata(metadata)


def list_not_todos():
    items = [_not_todo_from_journal(obj) for obj in _list_journal_type("not_todo")]
    return sorted(items, key=lambda item: item["created_at"], reverse=True)


def list_calendar_events(event_date=None, account_context=None, all_events=False):
    outcomes_by_event_id, outcomes_by_uid = _event_outcomes()
    items = []
    for obj in list_calendar_objects("VEVENT"):
        item = _calendar_event_from_object(obj)
        outcome = outcomes_by_event_id.get(item["id"]) or outcomes_by_uid.get(obj.uid)
        if outcome:
            item["done"] = True
            item["completed_at"] = outcome["completed_at"]
        if account_context and item["account_context"] != account_context:
            continue
        if not all_events:
            target_date = event_date or date.today()
            if item["done"]:
                continue
            if not item["starts_at"] or item["starts_at"].date() != target_date:
                continue
        items.append(item)
    return sorted(items, key=lambda item: item["starts_at"] or datetime.max)


def complete_calendar_event(event_id: int):
    event_obj = _find_event(event_id)
    event = _calendar_event_from_object(event_obj)
    completed_at = datetime.utcnow()
    uid = f"aide-calendar-event-outcome-{event_id}@aide.local"
    metadata = {
        "id": _journal_id(uid),
        "event_id": event_id,
        "source_uid": event_obj.uid,
        "completed_at": completed_at.isoformat(),
    }
    ics = build_vjournal(
        uid=uid,
        summary=compact_summary("Meeting outcome: ", event["title"]),
        occurred_at=completed_at,
        created_at=completed_at,
        description=description_from_sections(
            ("Event", event["title"]),
            ("Status", "completed"),
            ("Location", event.get("location")),
            ("Description", event.get("description")),
        ),
        categories=["AIDE", "OUTCOME", "EVENT", _tag(event.get("account_context"))],
        aide_type="calendar_event_outcome",
        aide_id=metadata["id"],
        metadata=metadata,
        related_to=metadata["source_uid"],
    )
    put_calendar_object("VJOURNAL", uid, ics)
    event["done"] = True
    event["completed_at"] = completed_at
    return event


def upsert_task_outcome(task):
    completed_at = task.get("completed_at") or datetime.utcnow()
    uid = f"aide-task-outcome-{task['id']}@aide.local"
    metadata = {
        "id": _journal_id(uid),
        "task_id": task["id"],
        "source_uid": task.get("advanced_body"),
        "completed_at": completed_at.isoformat() if isinstance(completed_at, datetime) else str(completed_at),
    }
    ics = build_vjournal(
        uid=uid,
        summary=compact_summary("Task outcome: ", task["title"]),
        occurred_at=completed_at,
        created_at=completed_at,
        description=description_from_sections(
            ("Task", task["title"]),
            ("Status", "completed"),
            ("Description", task.get("description")),
        ),
        categories=["AIDE", "OUTCOME", "TASK", _tag(task.get("context"))],
        aide_type="task_outcome",
        aide_id=metadata["id"],
        metadata=metadata,
        related_to=task.get("advanced_body"),
    )
    put_calendar_object("VJOURNAL", uid, ics)


def _list_journal_type(aide_type):
    return [obj for obj in list_calendar_objects("VJOURNAL") if obj.props.get("X-AIDE-TYPE") == aide_type]


def _find_event(event_id):
    for obj in list_calendar_objects("VEVENT"):
        metadata_id = _metadata_int(obj.metadata, "id", default=_event_id(obj.uid))
        if metadata_id == event_id:
            return obj
    raise CalDAVEventNotFound("Calendar event not found")


def _event_outcomes():
    by_event_id = {}
    by_uid = {}
    for obj in _list_journal_type("calendar_event_outcome"):
        completed_at = _metadata_datetime(obj.metadata, "completed_at") or _prop_datetime(obj.props.get("DTSTART"))
        event_id = _metadata_int(obj.metadata, "event_id")
        source_uid = obj.metadata.get("source_uid") or obj.props.get("RELATED-TO")
        payload = {"completed_at": completed_at}
        if event_id is not None:
            by_event_id[event_id] = payload
        if source_uid:
            by_uid[source_uid] = payload
    return by_event_id, by_uid


def _thought_from_journal(obj):
    metadata = obj.metadata
    return {
        "id": _metadata_int(metadata, "id", default=_journal_id(obj.uid)),
        "content": metadata.get("content") or obj.props.get("DESCRIPTION") or obj.props.get("SUMMARY") or "",
        "tag": metadata.get("tag"),
        "created_at": _metadata_datetime(metadata, "created_at") or _prop_datetime(obj.props.get("CREATED")) or datetime.utcnow(),
    }


def _activity_from_journal(obj):
    return _activity_from_metadata(obj.metadata, fallback_props=obj.props, uid=obj.uid)


def _activity_from_metadata(metadata, fallback_props=None, uid=None):
    fallback_props = fallback_props or {}
    return {
        "id": _metadata_int(metadata, "id", default=_journal_id(uid or "activity")),
        "title": metadata.get("title") or fallback_props.get("SUMMARY") or "",
        "category": metadata.get("category"),
        "note": metadata.get("note"),
        "sop_model": metadata.get("sop_model") or "pdca",
        "plan": metadata.get("plan"),
        "result": metadata.get("result"),
        "learning": metadata.get("learning"),
        "next_action": metadata.get("next_action"),
        "energy_level": metadata.get("energy_level"),
        "occurred_at": _metadata_datetime(metadata, "occurred_at") or _prop_datetime(fallback_props.get("DTSTART")) or datetime.utcnow(),
        "created_at": _metadata_datetime(metadata, "created_at") or _prop_datetime(fallback_props.get("CREATED")) or datetime.utcnow(),
    }


def _money_from_journal(obj):
    return _money_from_metadata(obj.metadata, uid=obj.uid)


def _money_from_metadata(metadata, uid=None):
    return {
        "id": _metadata_int(metadata, "id", default=_journal_id(uid or "money")),
        "title": metadata.get("title") or "",
        "amount": float(metadata.get("amount") or 0),
        "type": metadata.get("type") or "expense",
        "category": metadata.get("category"),
        "note": metadata.get("note"),
        "record_date": _metadata_date(metadata, "record_date") or date.today(),
        "created_at": _metadata_datetime(metadata, "created_at") or datetime.utcnow(),
    }


def _not_todo_from_journal(obj):
    return _not_todo_from_metadata(obj.metadata, uid=obj.uid)


def _not_todo_from_metadata(metadata, uid=None):
    return {
        "id": _metadata_int(metadata, "id", default=_journal_id(uid or "not_todo")),
        "title": metadata.get("title") or "",
        "description": metadata.get("description"),
        "type": "not_todo",
        "priority": metadata.get("priority") or "medium",
        "importance": metadata.get("importance") or "medium",
        "urgency": metadata.get("urgency") or "medium",
        "context": metadata.get("context") or "personal",
        "todo_kind": "one_time",
        "recurrence_frequency": None,
        "recurrence_calendar": "solar",
        "recurrence_month": None,
        "recurrence_day": None,
        "recurrence_weekdays": None,
        "recurrence_rule": None,
        "not_todo_group": metadata.get("not_todo_group"),
        "recurrence_natural": None,
        "recurrence_cron": None,
        "recurrence_prepare_days": None,
        "advanced_format": "caldav_journal",
        "advanced_body": metadata.get("advanced_body") or uid,
        "due_date": None,
        "available_date": None,
        "starts_at": None,
        "ends_at": None,
        "location": None,
        "source": "caldav_journal",
        "done": False,
        "completed_at": None,
        "created_at": _metadata_datetime(metadata, "created_at") or datetime.utcnow(),
    }


def _calendar_event_from_object(obj):
    return _calendar_event_from_metadata(obj.metadata, props=obj.props, uid=obj.uid)


def _calendar_event_from_metadata(metadata, props=None, uid=None):
    props = props or {}
    starts_at = _metadata_datetime(metadata, "starts_at") or _prop_datetime(props.get("DTSTART"))
    ends_at = _metadata_datetime(metadata, "ends_at") or _prop_datetime(props.get("DTEND"))
    return {
        "id": _metadata_int(metadata, "id", default=_event_id(uid or "event")),
        "title": metadata.get("title") or props.get("SUMMARY") or "",
        "source": metadata.get("source") or "manual",
        "account_context": metadata.get("account_context") or "personal",
        "importance": metadata.get("importance") or "high",
        "event_kind": metadata.get("event_kind") or "one_time",
        "recurrence_frequency": metadata.get("recurrence_frequency"),
        "recurrence_calendar": metadata.get("recurrence_calendar") or "solar",
        "recurrence_month": metadata.get("recurrence_month"),
        "recurrence_day": metadata.get("recurrence_day"),
        "recurrence_weekdays": metadata.get("recurrence_weekdays"),
        "recurrence_natural": metadata.get("recurrence_natural"),
        "recurrence_rule": metadata.get("recurrence_rule"),
        "starts_at": starts_at,
        "ends_at": ends_at,
        "location": metadata.get("location") or props.get("LOCATION"),
        "description": metadata.get("description") or props.get("DESCRIPTION"),
        "external_id": metadata.get("external_id"),
        "done": bool(metadata.get("done")),
        "completed_at": _metadata_datetime(metadata, "completed_at"),
        "created_at": _metadata_datetime(metadata, "created_at") or _prop_datetime(props.get("CREATED")) or datetime.utcnow(),
    }


def _new_uid(kind):
    return f"aide-{kind}-{uuid.uuid4()}@aide.local"


def _journal_id(uid):
    return JOURNAL_ID_OFFSET + (zlib.crc32(uid.encode("utf-8")) % 1_000_000_000)


def _event_id(uid):
    return EVENT_ID_OFFSET + (zlib.crc32(uid.encode("utf-8")) % 1_000_000_000)


def _metadata_int(metadata, key, default=None):
    value = metadata.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _metadata_datetime(metadata, key):
    value = metadata.get(key)
    return _parse_datetime(value)


def _metadata_date(metadata, key):
    value = metadata.get(key)
    return _parse_date(value)


def _prop_datetime(value):
    if not value:
        return None
    return caldav_tasks._parse_ical_datetime(value)


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return caldav_tasks._parse_ical_datetime(text)


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    parsed = _parse_datetime(value)
    return parsed.date() if parsed else None


def _tag(value):
    if not value:
        return None
    return str(value).strip().replace(" ", "_").replace("-", "_").upper()
