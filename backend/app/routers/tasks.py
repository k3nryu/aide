from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from schemas import TaskOut
from services import caldav_aide, caldav_tasks


router = APIRouter()


def _completed_after(range_name: Optional[str]):
    if not range_name:
        return None
    today = datetime.utcnow()
    ranges = {
        "1d": timedelta(days=1),
        "3d": timedelta(days=3),
        "1w": timedelta(days=7),
        "1m": timedelta(days=31),
    }
    if range_name.endswith("y") and range_name[:-1].isdigit():
        return today - timedelta(days=365 * int(range_name[:-1]))
    if range_name not in ranges:
        return None
    return today - ranges[range_name]


@router.get("/tasks", response_model=List[TaskOut])
def list_tasks(
    done: Optional[bool] = None,
    context: Optional[str] = None,
    search: Optional[str] = None,
    completed_range: Optional[str] = None,
):
    if not caldav_tasks.is_enabled():
        raise HTTPException(status_code=503, detail="CalDAV storage is not configured")

    after = _completed_after(completed_range)
    caldav_items = caldav_tasks.list_tasks()
    not_todos = caldav_aide.list_not_todos()
    items = [*caldav_items, *not_todos]
    if done is not None:
        items = [item for item in items if item["done"] is done]
    if context:
        items = [item for item in items if item["context"] == context]
    if search:
        items = [item for item in items if search.lower() in item["title"].lower()]
    if after:
        items = [item for item in items if (item["completed_at"] or item["created_at"]) >= after]
    if done is True:
        return sorted(items, key=lambda item: (item["completed_at"] or item["created_at"]), reverse=True)
    return sorted(items, key=lambda item: item["created_at"], reverse=True)


@router.post("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: int):
    if not caldav_tasks.is_enabled():
        raise HTTPException(status_code=503, detail="CalDAV storage is not configured")

    not_todo_ids = {item["id"] for item in caldav_aide.list_not_todos()}
    if task_id in not_todo_ids:
        raise HTTPException(status_code=400, detail="Not-to-do items cannot be completed")
    try:
        item = caldav_tasks.complete_task(task_id)
        caldav_aide.upsert_task_outcome(item)
        return item
    except caldav_tasks.CalDAVTaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found")
