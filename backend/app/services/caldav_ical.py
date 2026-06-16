import json
from datetime import date, datetime


PRODID = "-//Aide//CalDAV Migration//EN"


def build_vtodo(
    *,
    uid,
    summary,
    description=None,
    created_at=None,
    due_date=None,
    start_date=None,
    completed_at=None,
    done=False,
    categories=None,
    aide_type="todo",
    aide_id=None,
    metadata=None,
):
    now = datetime.utcnow()
    lines = _base_component_lines("VTODO", uid, summary, now, created_at)
    lines.append(f"STATUS:{'COMPLETED' if done else 'NEEDS-ACTION'}")
    _append_common_lines(lines, description, categories, aide_type, aide_id, metadata)
    if start_date:
        lines.append(f"DTSTART;VALUE=DATE:{format_ical_date(start_date)}")
    if due_date:
        lines.append(f"DUE;VALUE=DATE:{format_ical_date(due_date)}")
    if done:
        lines.append("PERCENT-COMPLETE:100")
        lines.append(f"COMPLETED:{format_ical_datetime(completed_at or now)}")
    return _wrap_calendar("VTODO", lines)


def build_vevent(
    *,
    uid,
    summary,
    starts_at,
    description=None,
    created_at=None,
    ends_at=None,
    location=None,
    categories=None,
    aide_type="calendar_event",
    aide_id=None,
    metadata=None,
):
    now = datetime.utcnow()
    lines = _base_component_lines("VEVENT", uid, summary, now, created_at)
    lines.append(f"DTSTART:{format_ical_datetime(starts_at)}")
    if ends_at:
        lines.append(f"DTEND:{format_ical_datetime(ends_at)}")
    if location:
        lines.append(f"LOCATION:{escape_ical_text(location)}")
    _append_common_lines(lines, description, categories, aide_type, aide_id, metadata)
    return _wrap_calendar("VEVENT", lines)


def build_vjournal(
    *,
    uid,
    summary,
    occurred_at,
    description=None,
    created_at=None,
    categories=None,
    aide_type,
    aide_id=None,
    metadata=None,
    related_to=None,
):
    now = datetime.utcnow()
    lines = _base_component_lines("VJOURNAL", uid, summary, now, created_at)
    lines.append(f"DTSTART:{format_ical_datetime(occurred_at)}")
    if related_to:
        lines.append(f"RELATED-TO:{escape_ical_text(related_to)}")
    _append_common_lines(lines, description, categories, aide_type, aide_id, metadata)
    return _wrap_calendar("VJOURNAL", lines)


def description_from_sections(*sections):
    parts = []
    for title, value in sections:
        if value is None or value == "":
            continue
        parts.append(f"{title}:\n{value}")
    return "\n\n".join(parts) if parts else None


def compact_summary(prefix, text, limit=120):
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return f"{prefix}{cleaned}" if prefix else cleaned
    return f"{prefix}{cleaned[:limit].rstrip()}..."


def format_ical_date(value):
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%Y%m%d")


def format_ical_datetime(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    return value.strftime("%Y%m%dT%H%M%SZ")


def escape_ical_text(value):
    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def fold_ical_line(line):
    if len(line) <= 75:
        return line
    parts = [line[:75]]
    rest = line[75:]
    while rest:
        parts.append(" " + rest[:74])
        rest = rest[74:]
    return "\r\n".join(parts)


def _base_component_lines(component, uid, summary, now, created_at):
    return [
        f"BEGIN:{component}",
        f"UID:{escape_ical_text(uid)}",
        f"SUMMARY:{escape_ical_text(summary or 'Untitled Aide record')}",
        f"DTSTAMP:{format_ical_datetime(now)}",
        f"CREATED:{format_ical_datetime(created_at or now)}",
    ]


def _append_common_lines(lines, description, categories, aide_type, aide_id, metadata):
    if description:
        lines.append(f"DESCRIPTION:{escape_ical_text(description)}")
    if categories:
        values = [escape_ical_text(item) for item in categories if item]
        if values:
            lines.append(f"CATEGORIES:{','.join(values)}")
    if aide_type:
        lines.append(f"X-AIDE-TYPE:{escape_ical_text(aide_type)}")
    if aide_id is not None:
        lines.append(f"X-AIDE-ID:{escape_ical_text(aide_id)}")
    lines.append("X-AIDE-SOURCE:db-migration")
    if metadata:
        lines.append(f"X-AIDE-METADATA:{escape_ical_text(json.dumps(metadata, ensure_ascii=False, default=str))}")


def _wrap_calendar(component, component_lines):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        *component_lines,
        f"END:{component}",
        "END:VCALENDAR",
        "",
    ]
    return "\r\n".join(fold_ical_line(line) for line in lines)
