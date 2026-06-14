import sys
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from services.ai_assist import build_pdca_stow_analysis


@dataclass
class Activity:
    title: str
    category: Optional[str]
    note: Optional[str]
    occurred_at: datetime
    plan: Optional[str] = None
    result: Optional[str] = None
    learning: Optional[str] = None
    next_action: Optional[str] = None
    energy_level: Optional[int] = None


@dataclass
class Task:
    title: str
    completed_at: Optional[datetime]
    created_at: datetime


class AIAssistTests(unittest.TestCase):
    def test_structured_activity_fields_drive_pdca_analysis(self):
        now = datetime.utcnow()
        activities = [
            Activity(
                title="写财富自由目标",
                category="growth",
                note=None,
                occurred_at=now - timedelta(hours=1),
                plan="写下一个 SMART 小目标",
                result="发布第一版目标草稿",
                learning="目标太大时需要先拆成 15 分钟动作",
                next_action="明天补一条可执行任务",
                energy_level=4,
            )
        ]
        completed = [Task(title="整理现金流", completed_at=now, created_at=now)]

        result = build_pdca_stow_analysis(activities, completed)

        self.assertIn("SMART 小目标", result["pdca"]["plan"])
        self.assertIn("发布第一版目标草稿", result["pdca"]["check"])
        self.assertEqual(result["next_actions"], ["明天补一条可执行任务"])
        self.assertTrue(any("SCAQ" in item for item in result["stow"]["opportunities"]))


if __name__ == "__main__":
    unittest.main()
