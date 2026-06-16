import json
from calendar import monthrange
from datetime import date, datetime, time


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
    recurrence=None,
):
    now = datetime.utcnow()
    if not start_date and recurrence:
        start_date = recurrence_start(metadata or recurrence, default=(created_at or now), as_datetime=False)
    lines = _base_component_lines("VTODO", uid, summary, now, created_at)
    lines.append(f"STATUS:{'COMPLETED' if done else 'NEEDS-ACTION'}")
    _append_common_lines(lines, description, categories, aide_type, aide_id, metadata)
    if start_date:
        lines.append(f"DTSTART;VALUE=DATE:{format_ical_date(start_date)}")
    _append_recurrence_line(lines, recurrence)
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
    recurrence=None,
    all_day=False,
):
    now = datetime.utcnow()
    lines = _base_component_lines("VEVENT", uid, summary, now, created_at)
    if all_day:
        start_date = starts_at.date() if isinstance(starts_at, datetime) else starts_at
        lines.append(f"DTSTART;VALUE=DATE:{format_ical_date(start_date)}")
        if ends_at:
            end_date = ends_at.date() if isinstance(ends_at, datetime) else ends_at
            lines.append(f"DTEND;VALUE=DATE:{format_ical_date(end_date)}")
    else:
        lines.append(f"DTSTART:{format_ical_datetime(starts_at)}")
        if ends_at:
            lines.append(f"DTEND:{format_ical_datetime(ends_at)}")
    _append_recurrence_line(lines, recurrence)
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


def recurrence_payload(metadata):
    if not metadata:
        return None
    rule = _json_dict(metadata.get("recurrence_rule"))
    frequency = rule.get("frequency") or metadata.get("recurrence_frequency")
    if not frequency:
        return None
    payload = {
        "frequency": str(frequency).lower(),
        "interval": rule.get("interval") or 1,
        "start_date": rule.get("start_date") or metadata.get("available_date") or metadata.get("starts_at"),
        "end_date": rule.get("end_date"),
        "month": rule.get("month") or metadata.get("recurrence_month"),
        "day": rule.get("day") or metadata.get("recurrence_day"),
        "weekdays": rule.get("weekdays") or metadata.get("recurrence_weekdays"),
        "nth": rule.get("nth"),
        "nth_weekday": rule.get("nth_weekday"),
    }
    return payload


def recurrence_start(metadata, *, default=None, as_datetime=False):
    recurrence = recurrence_payload(metadata)
    value = recurrence.get("start_date") if recurrence else None
    month = _safe_int((recurrence or {}).get("month"))
    day = _safe_int((recurrence or {}).get("day"))
    parsed = _parse_dt_or_date(value, as_datetime=as_datetime)
    if parsed:
        return parsed
    if month and day:
        today = date.today()
        day_value = min(day, monthrange(today.year, month)[1])
        base_date = date(today.year, month, day_value)
        if as_datetime:
            return datetime.combine(base_date, time.min)
        return base_date
    parsed_default = _parse_dt_or_date(default, as_datetime=as_datetime)
    if parsed_default:
        return parsed_default
    return default


def _append_recurrence_line(lines, recurrence):
    rule = recurrence_rrule(recurrence)
    if rule:
        lines.append(f"RRULE:{rule}")


def recurrence_rrule(recurrence):
    if not recurrence:
        return None
    frequency = str(recurrence.get("frequency") or "").upper()
    if frequency not in {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}:
        return None

    parts = [f"FREQ={frequency}"]
    interval = _safe_int(recurrence.get("interval"))
    if interval and interval > 1:
        parts.append(f"INTERVAL={interval}")

    weekdays = weekday_codes(recurrence.get("weekdays") or recurrence.get("nth_weekday"))
    month = _safe_int(recurrence.get("month"))
    day = _safe_int(recurrence.get("day"))
    nth = _safe_int(recurrence.get("nth"))
    end_date = _parse_dt_or_date(recurrence.get("end_date"))

    if frequency == "WEEKLY" and weekdays:
        parts.append(f"BYDAY={','.join(weekdays)}")
    if frequency == "MONTHLY":
        if day:
            parts.append(f"BYMONTHDAY={day}")
        elif weekdays and nth:
            parts.append(f"BYDAY={','.join(weekdays)}")
            parts.append(f"BYSETPOS={nth}")
    if frequency == "YEARLY":
        if month:
            parts.append(f"BYMONTH={month}")
        if day:
            parts.append(f"BYMONTHDAY={day}")
        elif weekdays and nth:
            parts.append(f"BYDAY={','.join(weekdays)}")
            parts.append(f"BYSETPOS={nth}")

    if end_date:
        if isinstance(end_date, datetime):
            until = end_date
        else:
            until = datetime.combine(end_date, time(23, 59, 59))
        parts.append(f"UNTIL={format_ical_datetime(until)}")
    return ";".join(parts)


def weekday_codes(value):
    if not value:
        return []
    source = value if isinstance(value, list) else str(value)
    mapping = {
        "0": "SU",
        "1": "MO",
        "2": "TU",
        "3": "WE",
        "4": "TH",
        "5": "FR",
        "6": "SA",
        "周日": "SU",
        "星期日": "SU",
        "礼拜日": "SU",
        "周天": "SU",
        "星期天": "SU",
        "礼拜天": "SU",
        "周一": "MO",
        "星期一": "MO",
        "礼拜一": "MO",
        "周二": "TU",
        "星期二": "TU",
        "礼拜二": "TU",
        "周三": "WE",
        "星期三": "WE",
        "礼拜三": "WE",
        "周四": "TH",
        "星期四": "TH",
        "礼拜四": "TH",
        "周五": "FR",
        "星期五": "FR",
        "礼拜五": "FR",
        "周六": "SA",
        "星期六": "SA",
        "礼拜六": "SA",
        "SU": "SU",
        "MO": "MO",
        "TU": "TU",
        "WE": "WE",
        "TH": "TH",
        "FR": "FR",
        "SA": "SA",
    }
    tokens = source if isinstance(source, list) else [token for token in str(source).replace("、", ",").split(",") if token]
    values = []
    for token in tokens:
        key = str(token).strip()
        code = mapping.get(key)
        if code and code not in values:
            values.append(code)
    return values


def _json_dict(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _parse_dt_or_date(value, *, as_datetime=False):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if as_datetime else value.date()
    if isinstance(value, date):
        return datetime.combine(value, time.min) if as_datetime else value
    text = str(value).strip()
    try:
        parsed_dt = datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
        return parsed_dt if as_datetime else parsed_dt.date()
    except ValueError:
        pass
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed if as_datetime else parsed.date()
        except ValueError:
            continue
    return None


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
