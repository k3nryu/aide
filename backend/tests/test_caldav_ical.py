import sys
import unittest
from datetime import date, datetime
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from services import caldav_ical


class CalDAVICalTests(unittest.TestCase):
    def test_recurrence_rrule_builds_weekly_byday(self):
        recurrence = {
            "frequency": "weekly",
            "interval": 1,
            "start_date": "2026-06-17",
            "weekdays": "周一、周四",
        }

        rule = caldav_ical.recurrence_rrule(recurrence)

        self.assertEqual(rule, "FREQ=WEEKLY;BYDAY=MO,TH")

    def test_build_vevent_includes_yearly_rrule(self):
        ics = caldav_ical.build_vevent(
            uid="aide-event-1@aide.local",
            summary="Annual reminder",
            starts_at=datetime(2026, 4, 8, 0, 0),
            created_at=datetime(2026, 1, 1, 0, 0),
            all_day=True,
            recurrence={"frequency": "yearly", "month": 4, "day": 8},
        )

        self.assertIn("RRULE:FREQ=YEARLY;BYMONTH=4;BYMONTHDAY=8", ics)
        self.assertIn("DTSTART;VALUE=DATE:20260408", ics)

    def test_build_vtodo_derives_dtstart_for_daily_recurrence(self):
        ics = caldav_ical.build_vtodo(
            uid="aide-task-1@aide.local",
            summary="每天拍一个视频",
            created_at=datetime(2026, 6, 17, 9, 0),
            recurrence={"frequency": "daily", "start_date": date(2026, 6, 17)},
            metadata={"created_at": "2026-06-17T09:00:00"},
        )

        self.assertIn("DTSTART;VALUE=DATE:20260617", ics)
        self.assertIn("RRULE:FREQ=DAILY", ics)


if __name__ == "__main__":
    unittest.main()
