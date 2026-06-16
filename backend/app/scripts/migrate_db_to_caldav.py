import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import SessionLocal
from models import ActivityLogDB, CalendarEventDB, MoneyRecordDB, TaskDB, ThoughtDB
from services.caldav_ical import (
    build_vevent,
    build_vjournal,
    build_vtodo,
    compact_summary,
    description_from_sections,
)
from services.caldav_store import list_component_uids, list_calendar_collections, put_calendar_object


def main():
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup_path = Path(f"/tmp/aide-caldav-backup-{timestamp}.json")

    with SessionLocal() as db:
        tasks = db.query(TaskDB).order_by(TaskDB.id.asc()).all()
        events = db.query(CalendarEventDB).order_by(CalendarEventDB.id.asc()).all()
        thoughts = db.query(ThoughtDB).order_by(ThoughtDB.id.asc()).all()
        activity_logs = db.query(ActivityLogDB).order_by(ActivityLogDB.id.asc()).all()
        money_records = db.query(MoneyRecordDB).order_by(MoneyRecordDB.id.asc()).all()

        backup = {
            "exported_at": timestamp,
            "tasks": [serialize_task(item) for item in tasks],
            "calendar_events": [serialize_event(item) for item in events],
            "thoughts": [serialize_thought(item) for item in thoughts],
            "activity_logs": [serialize_activity(item) for item in activity_logs],
            "money_records": [serialize_money(item) for item in money_records],
        }
        backup_path.write_text(json.dumps(backup, ensure_ascii=False, indent=2, default=str))

    collections = list_calendar_collections()
    existing = {
        "VTODO": set(list_component_uids("VTODO")),
        "VEVENT": set(list_component_uids("VEVENT")),
        "VJOURNAL": set(list_component_uids("VJOURNAL")),
    }
    results = {"VTODO": {"created": 0, "updated": 0}, "VEVENT": {"created": 0, "updated": 0}, "VJOURNAL": {"created": 0, "updated": 0}}

    for item in tasks:
        if item.type == "not_todo":
            uid = uid_for("not-todo", item.id)
            upsert(
                "VJOURNAL",
                uid,
                build_vjournal(
                    uid=uid,
                    summary=compact_summary("Not-to-do: ", item.title),
                    occurred_at=item.created_at,
                    created_at=item.created_at,
                    description=description_from_sections(
                        ("Title", item.title),
                        ("Description", item.description),
                        ("Group", item.not_todo_group),
                        ("Context", item.context),
                    ),
                    categories=["AIDE", "NOT_TODO", normalize_tag(item.context), normalize_tag(item.not_todo_group)],
                    aide_type="not_todo",
                    aide_id=item.id,
                    metadata=serialize_task(item),
                ),
                existing,
                results,
            )
            continue

        todo_uid = uid_for("task", item.id)
        upsert(
            "VTODO",
            todo_uid,
            build_vtodo(
                uid=todo_uid,
                summary=item.title,
                description=description_from_sections(
                    ("Description", item.description),
                    ("Context", item.context),
                    ("Priority", item.priority),
                    ("Importance", item.importance),
                    ("Urgency", item.urgency),
                    ("Recurrence", item.recurrence_natural or item.recurrence_frequency),
                ),
                created_at=item.created_at,
                due_date=item.due_date,
                start_date=item.available_date,
                completed_at=item.completed_at,
                done=bool(item.done),
                categories=["AIDE", "TODO", normalize_tag(item.context), normalize_tag(item.todo_kind)],
                aide_type="todo",
                aide_id=item.id,
                metadata=serialize_task(item),
            ),
            existing,
            results,
        )
        if item.done:
            outcome_uid = uid_for("task-outcome", item.id)
            upsert(
                "VJOURNAL",
                outcome_uid,
                build_vjournal(
                    uid=outcome_uid,
                    summary=compact_summary("Task outcome: ", item.title),
                    occurred_at=item.completed_at or item.created_at,
                    created_at=item.created_at,
                    description=description_from_sections(
                        ("Task", item.title),
                        ("Status", "completed"),
                        ("Description", item.description),
                    ),
                    categories=["AIDE", "OUTCOME", "TASK", normalize_tag(item.context)],
                    aide_type="task_outcome",
                    aide_id=item.id,
                    metadata={"task_id": item.id, "source_uid": todo_uid},
                    related_to=todo_uid,
                ),
                existing,
                results,
            )

    for item in events:
        event_uid = uid_for("event", item.id)
        upsert(
            "VEVENT",
            event_uid,
            build_vevent(
                uid=event_uid,
                summary=item.title,
                starts_at=item.starts_at,
                ends_at=item.ends_at,
                created_at=item.created_at,
                location=item.location,
                description=description_from_sections(
                    ("Description", item.description),
                    ("Source", item.source),
                    ("Context", item.account_context),
                    ("Importance", item.importance),
                    ("Recurrence", item.recurrence_natural or item.recurrence_frequency),
                ),
                categories=["AIDE", "EVENT", normalize_tag(item.account_context), normalize_tag(item.source)],
                aide_type="calendar_event",
                aide_id=item.id,
                metadata=serialize_event(item),
            ),
            existing,
            results,
        )
        if item.done:
            outcome_uid = uid_for("event-outcome", item.id)
            upsert(
                "VJOURNAL",
                outcome_uid,
                build_vjournal(
                    uid=outcome_uid,
                    summary=compact_summary("Meeting outcome: ", item.title),
                    occurred_at=item.completed_at or item.starts_at or item.created_at,
                    created_at=item.created_at,
                    description=description_from_sections(
                        ("Event", item.title),
                        ("Status", "completed"),
                        ("Location", item.location),
                        ("Description", item.description),
                    ),
                    categories=["AIDE", "OUTCOME", "EVENT", normalize_tag(item.account_context)],
                    aide_type="calendar_event_outcome",
                    aide_id=item.id,
                    metadata={"event_id": item.id, "source_uid": event_uid},
                    related_to=event_uid,
                ),
                existing,
                results,
            )

    for item in thoughts:
        uid = uid_for("thought", item.id)
        upsert(
            "VJOURNAL",
            uid,
            build_vjournal(
                uid=uid,
                summary=compact_summary("Thought: ", item.content),
                occurred_at=item.created_at,
                created_at=item.created_at,
                description=description_from_sections(
                    ("Content", item.content),
                    ("Tag", item.tag),
                ),
                categories=["AIDE", "THOUGHT", normalize_tag(item.tag)],
                aide_type="thought",
                aide_id=item.id,
                metadata=serialize_thought(item),
            ),
            existing,
            results,
        )

    for item in activity_logs:
        uid = uid_for("activity", item.id)
        upsert(
            "VJOURNAL",
            uid,
            build_vjournal(
                uid=uid,
                summary=compact_summary("Activity: ", item.title),
                occurred_at=item.occurred_at,
                created_at=item.created_at,
                description=description_from_sections(
                    ("Title", item.title),
                    ("Note", item.note),
                    ("Plan", item.plan),
                    ("Result", item.result),
                    ("Learning", item.learning),
                    ("Next action", item.next_action),
                ),
                categories=["AIDE", "ACTIVITY", normalize_tag(item.category), normalize_tag(item.sop_model)],
                aide_type="activity_log",
                aide_id=item.id,
                metadata=serialize_activity(item),
            ),
            existing,
            results,
        )

    for item in money_records:
        uid = uid_for("money", item.id)
        upsert(
            "VJOURNAL",
            uid,
            build_vjournal(
                uid=uid,
                summary=compact_summary(f"{(item.type or 'money').title()}: ", item.title),
                occurred_at=item.record_date or item.created_at.date(),
                created_at=item.created_at,
                description=description_from_sections(
                    ("Title", item.title),
                    ("Type", item.type),
                    ("Amount", item.amount),
                    ("Category", item.category),
                    ("Note", item.note),
                ),
                categories=["AIDE", "MONEY", normalize_tag(item.type), normalize_tag(item.category)],
                aide_type="money_record",
                aide_id=item.id,
                metadata=serialize_money(item),
            ),
            existing,
            results,
        )

    print("backup", backup_path)
    for collection in collections:
        print(
            "collection",
            collection.displayname or "-",
            collection.href,
            ",".join(collection.components),
        )
    for component_name, counts in results.items():
        print(component_name, "created", counts["created"], "updated", counts["updated"])


def upsert(component_name, uid, ics, existing, results):
    put_calendar_object(component_name, uid, ics)
    if uid in existing[component_name]:
        results[component_name]["updated"] += 1
    else:
        results[component_name]["created"] += 1
        existing[component_name].add(uid)


def uid_for(kind, item_id):
    return f"aide-{kind}-{item_id}@aide.local"


def normalize_tag(value):
    if not value:
        return None
    return str(value).strip().replace(" ", "_").replace("-", "_").upper()


def serialize_task(item):
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "type": item.type,
        "priority": item.priority,
        "importance": item.importance,
        "urgency": item.urgency,
        "context": item.context,
        "todo_kind": item.todo_kind,
        "recurrence_frequency": item.recurrence_frequency,
        "recurrence_calendar": item.recurrence_calendar,
        "recurrence_month": item.recurrence_month,
        "recurrence_day": item.recurrence_day,
        "recurrence_weekdays": item.recurrence_weekdays,
        "recurrence_rule": item.recurrence_rule,
        "not_todo_group": item.not_todo_group,
        "recurrence_natural": item.recurrence_natural,
        "due_date": item.due_date,
        "available_date": item.available_date,
        "location": item.location,
        "source": item.source,
        "done": item.done,
        "completed_at": item.completed_at,
        "created_at": item.created_at,
    }


def serialize_event(item):
    return {
        "id": item.id,
        "title": item.title,
        "source": item.source,
        "account_context": item.account_context,
        "importance": item.importance,
        "event_kind": item.event_kind,
        "recurrence_frequency": item.recurrence_frequency,
        "recurrence_calendar": item.recurrence_calendar,
        "recurrence_month": item.recurrence_month,
        "recurrence_day": item.recurrence_day,
        "recurrence_weekdays": item.recurrence_weekdays,
        "recurrence_natural": item.recurrence_natural,
        "recurrence_rule": item.recurrence_rule,
        "starts_at": item.starts_at,
        "ends_at": item.ends_at,
        "location": item.location,
        "description": item.description,
        "external_id": item.external_id,
        "done": item.done,
        "completed_at": item.completed_at,
        "created_at": item.created_at,
    }


def serialize_thought(item):
    return {
        "id": item.id,
        "content": item.content,
        "tag": item.tag,
        "created_at": item.created_at,
    }


def serialize_activity(item):
    return {
        "id": item.id,
        "title": item.title,
        "category": item.category,
        "note": item.note,
        "sop_model": item.sop_model,
        "plan": item.plan,
        "result": item.result,
        "learning": item.learning,
        "next_action": item.next_action,
        "energy_level": item.energy_level,
        "occurred_at": item.occurred_at,
        "created_at": item.created_at,
    }


def serialize_money(item):
    return {
        "id": item.id,
        "title": item.title,
        "amount": str(item.amount),
        "type": item.type,
        "category": item.category,
        "note": item.note,
        "record_date": item.record_date,
        "created_at": item.created_at,
    }


if __name__ == "__main__":
    main()
