import os
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin
from xml.etree import ElementTree

from services import caldav_tasks


DAV_NS = "DAV:"
CALDAV_NS = "urn:ietf:params:xml:ns:caldav"


class CalDAVCollectionNotFound(RuntimeError):
    pass


@dataclass
class CalDAVCollection:
    href: str
    displayname: Optional[str]
    components: List[str]


def list_calendar_collections():
    settings = caldav_tasks._settings()
    if not settings:
        raise caldav_tasks.CalDAVNotConfigured("CalDAV is not configured")

    home_url = caldav_tasks._calendar_home_url(settings["url"])
    body = """<?xml version="1.0" encoding="utf-8" ?>
<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <D:displayname/>
    <D:resourcetype/>
    <C:supported-calendar-component-set/>
  </D:prop>
</D:propfind>"""
    _, _, payload = caldav_tasks._request(
        "PROPFIND",
        home_url,
        body,
        {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
    )
    root = ElementTree.fromstring(payload)
    collections = []
    for response in root.findall(f"{{{DAV_NS}}}response"):
        href = caldav_tasks._child_text(response, f"{{{DAV_NS}}}href")
        supported = response.find(f".//{{{CALDAV_NS}}}supported-calendar-component-set")
        if not href or supported is None:
            continue
        components = [
            item.attrib.get("name")
            for item in supported.findall(f"{{{CALDAV_NS}}}comp")
            if item.attrib.get("name")
        ]
        if not components:
            continue
        collections.append(
            CalDAVCollection(
                href=href,
                displayname=caldav_tasks._child_text(response, f".//{{{DAV_NS}}}displayname"),
                components=components,
            )
        )
    return collections


def collection_url_for(component_name: str):
    component_name = component_name.upper()
    env_name = {
        "VTODO": "CALDAV_TASK_COLLECTION",
        "VEVENT": "CALDAV_EVENT_COLLECTION",
        "VJOURNAL": "CALDAV_JOURNAL_COLLECTION",
    }.get(component_name)

    settings = caldav_tasks._settings()
    if not settings:
        raise caldav_tasks.CalDAVNotConfigured("CalDAV is not configured")

    if env_name:
        explicit = os.getenv(env_name)
        if explicit:
            return urljoin(settings["url"], explicit.rstrip("/") + "/")

    for collection in list_calendar_collections():
        if component_name in collection.components:
            return urljoin(settings["url"], collection.href)
    raise CalDAVCollectionNotFound(f"No CalDAV collection found for {component_name}")


def list_component_uids(component_name: str):
    component_name = component_name.upper()
    collection_url = collection_url_for(component_name)
    body = f"""<?xml version="1.0" encoding="utf-8" ?>
<C:calendar-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <C:calendar-data/>
  </D:prop>
  <C:filter>
    <C:comp-filter name="VCALENDAR">
      <C:comp-filter name="{component_name}" />
    </C:comp-filter>
  </C:filter>
</C:calendar-query>"""
    _, _, payload = caldav_tasks._request(
        "REPORT",
        collection_url,
        body,
        {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
    )
    root = ElementTree.fromstring(payload)
    uids = []
    for response in root.findall(f"{{{DAV_NS}}}response"):
        raw = caldav_tasks._child_text(response, f".//{{{CALDAV_NS}}}calendar-data")
        if not raw:
            continue
        lines = _unfold_ical_lines(raw)
        for line in lines:
            if line.startswith("UID:"):
                uids.append(line.split(":", 1)[1].strip())
                break
    return uids


def put_calendar_object(component_name: str, uid: str, ics: str):
    collection_url = collection_url_for(component_name)
    href = f"{uid}.ics"
    item_url = urljoin(collection_url, href)
    caldav_tasks._request("PUT", item_url, ics, {"Content-Type": "text/calendar; charset=utf-8"})
    return item_url


def _unfold_ical_lines(ics):
    lines = []
    for raw_line in ics.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw_line.startswith((" ", "\t")) and lines:
            lines[-1] += raw_line[1:]
        elif raw_line:
            lines.append(raw_line)
    return lines
