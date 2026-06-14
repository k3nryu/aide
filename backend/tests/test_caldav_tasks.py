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


if __name__ == "__main__":
    unittest.main()
