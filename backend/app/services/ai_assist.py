import re
from collections import Counter
from datetime import datetime, timedelta


ACTION_KEYWORDS = (
    "想",
    "需要",
    "应该",
    "可以",
    "准备",
    "计划",
    "整理",
    "学习",
    "检查",
    "改善",
    "实现",
    "做",
)

GROWTH_KEYWORDS = ("学习", "健康", "运动", "家人", "老婆", "长期", "财富自由", "复盘", "改善")


def _shorten(text, limit=72):
    cleaned = re.sub(r"\s+", " ", text).strip(" ，。,.")
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def _split_sentences(content):
    parts = re.split(r"[\n。！？!?；;]+", content)
    return [part.strip(" ，,") for part in parts if part.strip()]


def suggest_tasks_from_thought(thought):
    sentences = _split_sentences(thought.content)
    candidates = [sentence for sentence in sentences if any(keyword in sentence for keyword in ACTION_KEYWORDS)]
    if not candidates and sentences:
        candidates = [sentences[0]]

    suggestions = []
    for sentence in candidates[:5]:
        title = _shorten(sentence)
        if not any(keyword in title for keyword in ("做", "整理", "检查", "准备", "学习", "改善")):
            title = _shorten(f"整理想法：{title}")
        importance = "high" if any(keyword in sentence for keyword in GROWTH_KEYWORDS) else "medium"
        suggestions.append(
            {
                "title": title,
                "description": f"由想法拆分：{_shorten(thought.content, 180)}",
                "context": "personal",
                "importance": importance,
                "urgency": "medium",
            }
        )

    return {
        "thought_id": thought.id,
        "source": thought.content,
        "summary": "Aide 根据想法内容生成了可确认的任务草稿。当前为本地规则原型，未来可替换为 AI 模型。",
        "suggestions": suggestions,
    }


def _recent(items, limit=5):
    return list(items[:limit])


def build_pdca_stow_analysis(activity_logs, completed_tasks):
    now = datetime.utcnow()
    recent_cutoff = now - timedelta(days=14)
    recent_activities = [item for item in activity_logs if item.occurred_at >= recent_cutoff]
    recent_completed = [item for item in completed_tasks if (item.completed_at or item.created_at) >= recent_cutoff]
    categories = Counter(item.category or "未分类" for item in recent_activities)
    top_categories = categories.most_common(3)

    completed_titles = [item.title for item in _recent(recent_completed)]
    activity_titles = [item.title for item in _recent(recent_activities)]

    if top_categories:
        category_summary = "、".join(f"{name} {count} 次" for name, count in top_categories)
    else:
        category_summary = "最近还没有足够行为记录"

    pdca = {
        "plan": f"最近 14 天完成了 {len(recent_completed)} 个任务，记录了 {len(recent_activities)} 条行为。",
        "do": "；".join(activity_titles) if activity_titles else "暂无足够行为样本。",
        "check": f"行为高频类别：{category_summary}。",
        "act": "把重复出现的行为趋势转成一个想法或任务；把未完成但反复出现的问题放进下一轮计划。",
    }

    strengths = []
    if recent_completed:
        strengths.append(f"有实际完成记录：{', '.join(completed_titles)}")
    if top_categories:
        strengths.append(f"有持续记录习惯，最高频类别是 {top_categories[0][0]}。")
    if not strengths:
        strengths.append("已经开始记录数据，这是后续复盘的基础。")

    threats = []
    if categories.get("sleep", 0) or categories.get("睡眠", 0):
        threats.append("睡眠相关行为值得持续观察，避免影响第二天执行力。")
    if categories.get("food", 0) or categories.get("饮食", 0):
        threats.append("饮食记录可以继续积累，用来发现能量和健康波动。")
    if not threats:
        threats.append("当前样本还少，过早下结论可能误导判断。")

    opportunities = [
        "把高频行为转成可持续习惯任务。",
        "把完成任务后的行为结果写回想法，用来形成下一轮 PDCA。",
    ]

    weaknesses = []
    if len(recent_activities) < 5:
        weaknesses.append("最近行为样本偏少，趋势判断还不稳定。")
    if not recent_completed:
        weaknesses.append("最近完成任务较少，任务和行为之间的闭环还不明显。")
    if not weaknesses:
        weaknesses.append("可以继续补充行为的分类和备注，让分析更具体。")

    thought_inputs = [
        "哪些行为反复出现，值得变成固定任务？",
        "哪些完成任务带来了明显好处，值得继续强化？",
        "哪些行为可能正在拖累健康、家庭、工作或长期目标？",
    ]

    return {
        "summary": "Aide 根据完成任务和行为记录生成了 PDCA/STOW 草稿。当前为本地规则原型，未来可替换为 AI 模型。",
        "pdca": pdca,
        "stow": {
            "strengths": strengths,
            "threats": threats,
            "opportunities": opportunities,
            "weaknesses": weaknesses,
        },
        "thought_inputs": thought_inputs,
    }
