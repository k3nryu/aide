import base64
import os
import re
import uuid
import zlib
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree


DAV_NS = "DAV:"
CALDAV_NS = "urn:ietf:params:xml:ns:caldav"
CALDAV_ID_OFFSET = 1_000_000_000


class CalDAVNotConfigured(RuntimeError):
    pass


class CalDAVTaskNotFound(RuntimeError):
    pass


@dataclass
class CalDAVItem:
    href: str
    etag: Optional[str]
    ics: str
    task: Dict


def is_enabled():
    return bool(_settings())


def list_tasks():
    collection_url = _task_collection_url()
    body = """<?xml version="1.0" encoding="utf-8" ?>
<C:calendar-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <D:getetag/>
    <C:calendar-data/>
  </D:prop>
  <C:filter>
    <C:comp-filter name="VCALENDAR">
      <C:comp-filter name="VTODO" />
    </C:comp-filter>
  </C:filter>
</C:calendar-query>"""
    _, _, payload = _request(
        "REPORT",
        collection_url,
        body,
        {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
    )
    return [item.task for item in _items_from_multistatus(payload.decode("utf-8", errors="replace"))]


def create_task(task):
    collection_url = _task_collection_url()
    uid = f"{uuid.uuid4()}@aide"
    now = datetime.utcnow()
    ics = _build_vtodo(
        uid=uid,
        summary=task.title,
        description=task.description,
        due_date=task.due_date,
        start_date=task.available_date,
        created_at=now,
        completed_at=None,
        done=False,
    )
    href = f"{uid}.ics"
    item_url = urljoin(collection_url, href)
    _request("PUT", item_url, ics, {"Content-Type": "text/calendar; charset=utf-8"})
    return _task_from_vtodo(item_url, ics)


def update_task(task_id: int, values: Dict):
    item = _find_item(task_id)
    props = _parse_vtodo(item.ics)
    summary = values.get("title") or props.get("SUMMARY") or item.task["title"]
    description = values.get("description", props.get("DESCRIPTION"))
    due_date = values.get("due_date")
    if due_date is None:
        due_date = _parse_ical_date(props.get("DUE"))
    start_date = values.get("available_date")
    if start_date is None:
        start_date = _parse_ical_date(props.get("DTSTART"))
    completed_at = _parse_ical_datetime(props.get("COMPLETED"))
    done = values.get("done", item.task["done"])
    ics = _build_vtodo(
        uid=props.get("UID") or item.task["advanced_body"],
        summary=summary,
        description=description,
        due_date=due_date,
        start_date=start_date,
        created_at=_parse_ical_datetime(props.get("CREATED")) or item.task["created_at"],
        completed_at=completed_at,
        done=done,
    )
    _request("PUT", urljoin(_base_url(), item.href), ics, {"Content-Type": "text/calendar; charset=utf-8"})
    return _task_from_vtodo(item.href, ics)


def complete_task(task_id: int):
    item = _find_item(task_id)
    props = _parse_vtodo(item.ics)
    now = datetime.utcnow()
    ics = _build_vtodo(
        uid=props.get("UID") or item.task["advanced_body"],
        summary=props.get("SUMMARY") or item.task["title"],
        description=props.get("DESCRIPTION"),
        due_date=_parse_ical_date(props.get("DUE")),
        start_date=_parse_ical_date(props.get("DTSTART")),
        created_at=_parse_ical_datetime(props.get("CREATED")) or item.task["created_at"],
        completed_at=now,
        done=True,
    )
    _request("PUT", urljoin(_base_url(), item.href), ics, {"Content-Type": "text/calendar; charset=utf-8"})
    return _task_from_vtodo(item.href, ics)


def _settings():
    url = os.getenv("CALDAV_URL")
    username = os.getenv("CALDAV_USERNAME")
    password = os.getenv("CALDAV_PASSWORD")
    if not url or not username or not password:
        return None
    return {
        "url": url.rstrip("/") + "/",
        "username": username,
        "password": password,
        "collection": os.getenv("CALDAV_TASK_COLLECTION"),
    }


def _base_url():
    settings = _settings()
    if not settings:
        raise CalDAVNotConfigured("CalDAV is not configured")
    return settings["url"]


def _auth_header():
    settings = _settings()
    token = base64.b64encode(f"{settings['username']}:{settings['password']}".encode()).decode()
    return f"Basic {token}"


def _request(method, url, body=None, headers=None):
    data = body.encode("utf-8") if isinstance(body, str) else body
    request_headers = {
        "Authorization": _auth_header(),
        "User-Agent": "aide-caldav",
    }
    request_headers.update(headers or {})
    request = Request(url, data=data, headers=request_headers, method=method)
    with urlopen(request, timeout=10) as response:
        return response.status, response.headers, response.read()


def _task_collection_url():
    settings = _settings()
    if not settings:
        raise CalDAVNotConfigured("CalDAV is not configured")
    if settings["collection"]:
        return urljoin(settings["url"], settings["collection"].rstrip("/") + "/")

    home_url = _calendar_home_url(settings["url"])
    body = """<?xml version="1.0" encoding="utf-8" ?>
<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <D:displayname/>
    <D:resourcetype/>
    <C:supported-calendar-component-set/>
  </D:prop>
</D:propfind>"""
    _, _, payload = _request(
        "PROPFIND",
        home_url,
        body,
        {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
    )
    root = ElementTree.fromstring(payload)
    for response in root.findall(f"{{{DAV_NS}}}response"):
        href = _child_text(response, f"{{{DAV_NS}}}href")
        calendar_data = response.find(f".//{{{CALDAV_NS}}}supported-calendar-component-set")
        if not href or calendar_data is None:
            continue
        names = {item.attrib.get("name") for item in calendar_data.findall(f"{{{CALDAV_NS}}}comp")}
        if "VTODO" in names:
            return urljoin(settings["url"], href)
    raise CalDAVTaskNotFound("No VTODO collection found")


def _calendar_home_url(base_url):
    body = """<?xml version="1.0" encoding="utf-8" ?>
<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <D:current-user-principal/>
    <C:calendar-home-set/>
  </D:prop>
</D:propfind>"""
    _, _, payload = _request(
        "PROPFIND",
        base_url,
        body,
        {"Depth": "0", "Content-Type": "application/xml; charset=utf-8"},
    )
    root = ElementTree.fromstring(payload)
    home_href = _child_text(root, f".//{{{CALDAV_NS}}}calendar-home-set/{{{DAV_NS}}}href")
    if home_href:
        return urljoin(base_url, home_href)
    principal_href = _child_text(root, f".//{{{DAV_NS}}}current-user-principal/{{{DAV_NS}}}href")
    if not principal_href:
        raise CalDAVTaskNotFound("No calendar home set found")

    _, _, principal_payload = _request(
        "PROPFIND",
        urljoin(base_url, principal_href),
        body,
        {"Depth": "0", "Content-Type": "application/xml; charset=utf-8"},
    )
    principal_root = ElementTree.fromstring(principal_payload)
    principal_home_href = _child_text(
        principal_root, f".//{{{CALDAV_NS}}}calendar-home-set/{{{DAV_NS}}}href"
    )
    return urljoin(base_url, principal_home_href or principal_href)


def _items_from_multistatus(payload):
    root = ElementTree.fromstring(payload)
    items = []
    for response in root.findall(f"{{{DAV_NS}}}response"):
        href = _child_text(response, f"{{{DAV_NS}}}href")
        calendar_data = _child_text(response, f".//{{{CALDAV_NS}}}calendar-data")
        if not href or not calendar_data:
            continue
        etag = _child_text(response, f".//{{{DAV_NS}}}getetag")
        items.append(CalDAVItem(href=href, etag=etag, ics=calendar_data, task=_task_from_vtodo(href, calendar_data)))
    return items


def _find_item(task_id: int):
    collection_url = _task_collection_url()
    body = """<?xml version="1.0" encoding="utf-8" ?>
<C:calendar-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <D:getetag/>
    <C:calendar-data/>
  </D:prop>
  <C:filter>
    <C:comp-filter name="VCALENDAR">
      <C:comp-filter name="VTODO" />
    </C:comp-filter>
  </C:filter>
</C:calendar-query>"""
    _, _, payload = _request(
        "REPORT",
        collection_url,
        body,
        {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
    )
    for item in _items_from_multistatus(payload.decode("utf-8", errors="replace")):
        if item.task["id"] == task_id:
            return item
    raise CalDAVTaskNotFound("CalDAV task not found")


def _task_from_vtodo(href, ics):
    props = _parse_vtodo(ics)
    completed_at = _parse_ical_datetime(props.get("COMPLETED"))
    done = props.get("STATUS") in {"COMPLETED", "CANCELLED"} or bool(completed_at)
    due_date = _parse_ical_date(props.get("DUE"))
    start_date = _parse_ical_date(props.get("DTSTART"))
    created_at = _parse_ical_datetime(props.get("CREATED")) or datetime.utcnow()
    return {
        "id": _task_id(href, props.get("UID")),
        "title": props.get("SUMMARY") or "Untitled CalDAV task",
        "description": props.get("DESCRIPTION"),
        "type": "todo",
        "priority": "high" if due_date and due_date <= date.today() else "medium",
        "importance": "medium",
        "urgency": "high" if due_date and due_date <= date.today() else "medium",
        "context": "personal",
        "todo_kind": "one_time",
        "recurrence_frequency": None,
        "recurrence_calendar": "solar",
        "recurrence_month": None,
        "recurrence_day": None,
        "recurrence_weekdays": None,
        "recurrence_rule": None,
        "not_todo_group": None,
        "recurrence_natural": None,
        "recurrence_cron": None,
        "recurrence_prepare_days": None,
        "advanced_format": "caldav",
        "advanced_body": props.get("UID") or href,
        "due_date": due_date,
        "available_date": start_date,
        "starts_at": None,
        "ends_at": None,
        "location": props.get("LOCATION"),
        "source": "caldav",
        "done": done,
        "completed_at": completed_at,
        "created_at": created_at,
    }


def _task_id(href, uid=None):
    normalized = uid or unquote(urlparse(href).path or href)
    return CALDAV_ID_OFFSET + (zlib.crc32(normalized.encode("utf-8")) % CALDAV_ID_OFFSET)


def _parse_vtodo(ics):
    lines = _unfold_ical_lines(ics)
    in_todo = False
    props = {}
    for line in lines:
        if line == "BEGIN:VTODO":
            in_todo = True
            continue
        if line == "END:VTODO":
            break
        if not in_todo or ":" not in line:
            continue
        name_part, value = line.split(":", 1)
        name = name_part.split(";", 1)[0].upper()
        props[name] = _unescape_ical_text(value)
    return props


def _unfold_ical_lines(ics):
    lines = []
    for raw_line in ics.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw_line.startswith((" ", "\t")) and lines:
            lines[-1] += raw_line[1:]
        elif raw_line:
            lines.append(raw_line)
    return lines


def _build_vtodo(uid, summary, description, due_date, start_date, created_at, completed_at, done):
    now = datetime.utcnow()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Aide//CalDAV Todo//EN",
        "BEGIN:VTODO",
        f"UID:{_escape_ical_text(uid)}",
        f"SUMMARY:{_escape_ical_text(summary)}",
        f"DTSTAMP:{_format_ical_datetime(now)}",
        f"CREATED:{_format_ical_datetime(created_at or now)}",
        f"STATUS:{'COMPLETED' if done else 'NEEDS-ACTION'}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{_escape_ical_text(description)}")
    if start_date:
        lines.append(f"DTSTART;VALUE=DATE:{_format_ical_date(start_date)}")
    if due_date:
        lines.append(f"DUE;VALUE=DATE:{_format_ical_date(due_date)}")
    if done:
        lines.append("PERCENT-COMPLETE:100")
        lines.append(f"COMPLETED:{_format_ical_datetime(completed_at or now)}")
    lines.extend(["END:VTODO", "END:VCALENDAR", ""])
    return "\r\n".join(_fold_ical_line(line) for line in lines)


def _parse_ical_date(value):
    if not value:
        return None
    parsed = _parse_ical_datetime(value)
    return parsed.date() if parsed else None


def _parse_ical_datetime(value):
    if not value:
        return None
    cleaned = value.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed
        except ValueError:
            continue
    return None


def _format_ical_date(value):
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%Y%m%d")


def _format_ical_datetime(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    return value.strftime("%Y%m%dT%H%M%SZ")


def _escape_ical_text(value):
    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _unescape_ical_text(value):
    return re.sub(r"\\([nN,;\\])", lambda match: "\n" if match.group(1).lower() == "n" else match.group(1), value)


def _fold_ical_line(line):
    if len(line) <= 75:
        return line
    parts = [line[:75]]
    rest = line[75:]
    while rest:
        parts.append(" " + rest[:74])
        rest = rest[74:]
    return "\r\n".join(parts)


def _child_text(element, path):
    child = element.find(path)
    return child.text if child is not None else None
