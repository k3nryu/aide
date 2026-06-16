import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from services import caldav_tasks


class CalDAVTasksTests(unittest.TestCase):
    def test_vtodo_maps_to_task_shape(self):
        ics = "\r\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "BEGIN:VTODO",
                "UID:abc@example",
                "SUMMARY:Write plan",
                "DESCRIPTION:Plan next action",
                "CREATED:20260614T010203Z",
                "DTSTART;VALUE=DATE:20260614",
                "DUE;VALUE=DATE:20260615",
                "STATUS:NEEDS-ACTION",
                "END:VTODO",
                "END:VCALENDAR",
            ]
        )

        task = caldav_tasks._task_from_vtodo("/cjl/tasks/abc.ics", ics)

        self.assertEqual(task["title"], "Write plan")
        self.assertEqual(task["description"], "Plan next action")
        self.assertEqual(task["source"], "caldav")
        self.assertFalse(task["done"])
        self.assertEqual(str(task["available_date"]), "2026-06-14")
        self.assertEqual(str(task["due_date"]), "2026-06-15")

    def test_task_id_uses_path_for_absolute_and_relative_hrefs(self):
        self.assertEqual(
            caldav_tasks._task_id("http://radicale:5232/cjl/tasks/abc.ics"),
            caldav_tasks._task_id("/cjl/tasks/abc.ics"),
        )

    def test_task_id_prefers_uid_over_encoded_href(self):
        self.assertEqual(
            caldav_tasks._task_id("/cjl/tasks/abc%40aide.ics", "abc@aide"),
            caldav_tasks._task_id("/different/path.ics", "abc@aide"),
        )

    def test_vtodo_metadata_restores_aide_fields(self):
        ics = "\r\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "BEGIN:VTODO",
                "UID:aide-task-1@aide.local",
                "SUMMARY:Weekly review",
                "CREATED:20260614T010203Z",
                'X-AIDE-METADATA:{"id":123456789,"context":"company","todo_kind":"recurring","importance":"high","urgency":"medium","priority":"ultra","recurrence_frequency":"weekly","recurrence_weekdays":"1,3,5","recurrence_natural":"周一三五回顾","starts_at":"2026-06-14T09:30:00","ends_at":"2026-06-14T10:00:00"}',
                "STATUS:NEEDS-ACTION",
                "END:VTODO",
                "END:VCALENDAR",
            ]
        )

        task = caldav_tasks._task_from_vtodo("/cjl/tasks/aide-task-1.ics", ics)

        self.assertEqual(task["id"], 123456789)
        self.assertEqual(task["context"], "company")
        self.assertEqual(task["todo_kind"], "recurring")
        self.assertEqual(task["importance"], "high")
        self.assertEqual(task["priority"], "ultra")
        self.assertEqual(task["recurrence_frequency"], "weekly")
        self.assertEqual(task["recurrence_weekdays"], "1,3,5")
        self.assertEqual(task["recurrence_natural"], "周一三五回顾")
        self.assertEqual(str(task["starts_at"]), "2026-06-14 09:30:00")
        self.assertEqual(str(task["ends_at"]), "2026-06-14 10:00:00")


if __name__ == "__main__":
    unittest.main()
