import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from services import caldav_store


class CalDAVStoreTests(unittest.TestCase):
    def test_parse_component_props_and_metadata_for_vjournal(self):
        ics = "\r\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "BEGIN:VJOURNAL",
                "UID:aide-thought-1@aide.local",
                "SUMMARY:Thought: simplify storage",
                "DESCRIPTION:Content:\\nMove records to CalDAV",
                'X-AIDE-METADATA:{"id":42,"content":"Move records to CalDAV","tag":"infra"}',
                "END:VJOURNAL",
                "END:VCALENDAR",
            ]
        )

        props = caldav_store.parse_component_props(ics, "VJOURNAL")
        metadata = caldav_store.parse_metadata(props["X-AIDE-METADATA"])

        self.assertEqual(props["UID"], "aide-thought-1@aide.local")
        self.assertEqual(props["SUMMARY"], "Thought: simplify storage")
        self.assertIn("Move records to CalDAV", props["DESCRIPTION"])
        self.assertEqual(metadata["id"], 42)
        self.assertEqual(metadata["tag"], "infra")


if __name__ == "__main__":
    unittest.main()
