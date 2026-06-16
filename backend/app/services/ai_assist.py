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
FREEDOM_KEYWORDS = ("财富自由", "人生自由", "现金流", "资产", "收入", "自由", "长期")


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


def _non_empty(values):
    return [value.strip() for value in values if value and value.strip()]


def _join(values, fallback):
    items = _non_empty(values)
    if not items:
        return fallback
    return "；".join(items[:5])


def _first(values, fallback):
    items = _non_empty(values)
    return items[0] if items else fallback


def _activity_detail(item):
    parts = [item.title]
    if getattr(item, "result", None):
        parts.append(f"结果：{item.result}")
    if getattr(item, "learning", None):
        parts.append(f"检查：{item.learning}")
    if getattr(item, "next_action", None):
        parts.append(f"下一步：{item.next_action}")
    return " / ".join(_non_empty(parts))


def build_pdca_stow_analysis(activity_logs, completed_tasks):
    now = datetime.utcnow()
    recent_cutoff = now - timedelta(days=14)
    recent_activities = [item for item in activity_logs if item.occurred_at >= recent_cutoff]
    recent_completed = [item for item in completed_tasks if (item.completed_at or item.created_at) >= recent_cutoff]
    categories = Counter(item.category or "未分类" for item in recent_activities)
    top_categories = categories.most_common(3)

    completed_titles = [item.title for item in _recent(recent_completed)]
    activity_details = [_activity_detail(item) for item in _recent(recent_activities)]
    plan_details = [item.plan for item in recent_activities if getattr(item, "plan", None)]
    result_details = [item.result for item in recent_activities if getattr(item, "result", None)]
    learning_details = [item.learning for item in recent_activities if getattr(item, "learning", None)]
    next_actions = _non_empty(item.next_action for item in recent_activities if getattr(item, "next_action", None))[:5]
    structured_count = sum(
        1
        for item in recent_activities
        if any(
            getattr(item, field, None)
            for field in ("plan", "result", "learning", "next_action", "energy_level")
        )
    )
    energy_values = [item.energy_level for item in recent_activities if getattr(item, "energy_level", None)]

    if top_categories:
        category_summary = "、".join(f"{name} {count} 次" for name, count in top_categories)
    else:
        category_summary = "最近还没有足够行为记录"

    energy_summary = ""
    if energy_values:
        average_energy = round(sum(energy_values) / len(energy_values), 1)
        low_energy_count = sum(1 for value in energy_values if value <= 2)
        energy_summary = f"平均能量 {average_energy}/5，低能量记录 {low_energy_count} 次。"

    pdca = {
        "plan": _join(
            plan_details,
            f"最近 14 天完成了 {len(recent_completed)} 个任务，记录了 {len(recent_activities)} 条行为。",
        ),
        "do": _join(activity_details, "暂无足够行为样本。"),
        "check": _join(
            [*result_details, *learning_details, f"行为高频类别：{category_summary}。", energy_summary],
            f"行为高频类别：{category_summary}。",
        ),
        "act": _join(
            next_actions,
            "把重复出现的行为趋势转成一个想法或任务；把未完成但反复出现的问题放进下一轮计划。",
        ),
    }

    strengths = []
    if recent_completed:
        strengths.append(f"有实际完成记录：{', '.join(completed_titles)}")
    if result_details:
        strengths.append("行为记录开始包含结果，后续复盘可以从事实出发。")
    if top_categories:
        strengths.append(f"有持续记录习惯，最高频类别是 {top_categories[0][0]}。")
    if not strengths:
        strengths.append("已经开始记录数据，这是后续复盘的基础。")

    threats = []
    if categories.get("sleep", 0) or categories.get("睡眠", 0):
        threats.append("睡眠相关行为值得持续观察，避免影响第二天执行力。")
    if categories.get("food", 0) or categories.get("饮食", 0):
        threats.append("饮食记录可以继续积累，用来发现能量和健康波动。")
    if energy_values and sum(1 for value in energy_values if value <= 2) >= 2:
        threats.append("低能量记录偏多，计划需要更小步，避免只靠临场兴奋推进。")
    if recent_activities and not next_actions:
        threats.append("最近行为有记录，但缺少下一步，容易停在复盘而不是进入行动。")
    if not threats:
        threats.append("当前样本还少，过早下结论可能误导判断。")

    opportunities = [
        "把高频行为转成可持续习惯任务。",
        "把完成任务后的行为结果写回想法，用来形成下一轮 PDCA。",
        "对下一轮目标使用 SMART 写清楚最小可交付结果。",
        "汇报给自己时用 SCAQ：先说情境，再说冲突、问题和答案。",
    ]

    weaknesses = []
    if len(recent_activities) < 5:
        weaknesses.append("最近行为样本偏少，趋势判断还不稳定。")
    if structured_count < 3:
        weaknesses.append("结构化字段使用还少，建议记录计划、结果、检查和下一步中的至少两项。")
    if not recent_completed:
        weaknesses.append("最近完成任务较少，任务和行为之间的闭环还不明显。")
    if not weaknesses:
        weaknesses.append("可以继续补充行为的分类和备注，让分析更具体。")

    default_next_action = "今天只选一个 15 分钟动作，完成后立刻记录结果。"
    primary_next_action = _first(next_actions, default_next_action)
    primary_category = top_categories[0][0] if top_categories else "成长"
    freedom_related = any(
        any(keyword in text for keyword in FREEDOM_KEYWORDS)
        for text in [*completed_titles, *activity_details, *plan_details, *result_details, *learning_details, primary_next_action]
    )
    relevance = (
        "这个目标直接服务于财富自由/人生自由的长期闭环。"
        if freedom_related
        else "这个目标服务于稳定行动、复盘和长期自由的基础能力。"
    )

    scaq = {
        "situation": f"最近 14 天完成 {len(recent_completed)} 个任务，记录 {len(recent_activities)} 条行为；高频类别：{category_summary}。",
        "complication": _join([*weaknesses, *threats], "样本还少，暂时只能做轻量判断。"),
        "ask": "下一轮最应该解决的问题：怎样把记录里的真实行为转成一个小而确定的行动闭环？",
        "answer": primary_next_action,
    }

    smart_goal = {
        "specific": f"围绕“{primary_category}”完成一个可观察的小动作：{primary_next_action}",
        "measurable": "完成后新增 1 条行为记录，至少写清结果、检查或下一步中的 2 项。",
        "achievable": "动作控制在 15-30 分钟，低能量时只做最小版本。",
        "relevant": relevance,
        "time_bound": "今天结束前完成；明天简报时复盘是否进入下一轮 PDCA。",
    }

    communication_models = {
        "aida": {
            "attention": "先看最近真实行为，而不是重新做大计划。",
            "interest": f"高频类别是 {category_summary}，这里可能藏着最值得优化的模式。",
            "desire": "把一个模式变成可重复的小动作，可以降低拖延和临场决策成本。",
            "action": primary_next_action,
        },
        "five_w_two_h": {
            "what": primary_next_action,
            "why": relevance,
            "when": "今天。",
            "where": "用 Aide 记录任务或行为结果。",
            "who": "用户行动，Aide 负责留痕、复盘和提示。",
            "how": "先做最小版本，再写结果和下一步。",
            "how_much": "15-30 分钟，不追求一次解决完整问题。",
        },
    }

    thought_inputs = [
        "哪些行为反复出现，值得变成固定任务？",
        "哪些完成任务带来了明显好处，值得继续强化？",
        "哪些行为可能正在拖累健康、家庭、工作或长期目标？",
        "如果今天只做一个 15 分钟动作，哪个动作最能推进长期自由？",
    ]

    debate_prompts = [
        "正方：最近记录里哪个行为最能证明你正在变好？反方：这个证据有没有可能只是偶然？",
        "如果一个聪明但懒得配合的人反驳这个计划，他最可能攻击哪一点？",
        "这条下一步是否真的服务长期自由，还是只是让今天看起来忙？",
        "如果明天只允许保留一个行动，哪个动作最值得留下，为什么？",
    ]

    return {
        "summary": "Aide 根据完成任务和结构化行为记录生成了 PDCA/STOW/SCAQ/SMART 草稿。当前为本地规则原型，未来可替换为 AI 模型。",
        "pdca": pdca,
        "stow": {
            "strengths": strengths,
            "threats": threats,
            "opportunities": opportunities,
            "weaknesses": weaknesses,
        },
        "scaq": scaq,
        "smart_goal": smart_goal,
        "communication_models": communication_models,
        "debate_prompts": debate_prompts,
        "next_actions": next_actions
        or [
            default_next_action,
            "把一个反复出现的问题写成 SMART 小目标。",
        ],
        "thought_inputs": thought_inputs,
    }
