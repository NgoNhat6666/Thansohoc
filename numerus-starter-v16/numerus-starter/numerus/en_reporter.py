
from __future__ import annotations
from typing import Dict, List

_BASE = {
    1:  {"name":"1 – Initiator", "keywords":["leadership","autonomy","pioneering"], "plus":"Proactive, decisive, independent.", "minus":"Bossy, isolated, self-imposed pressure.", "advice":"Lead by listening; empower others."},
    2:  {"name":"2 – Connector", "keywords":["cooperation","empathy","diplomacy"], "plus":"Sensitive, conciliatory.", "minus":"Conflict-averse, emotionally dependent.", "advice":"State needs clearly; keep boundaries."},
    3:  {"name":"3 – Expression", "keywords":["creativity","language","joy"], "plus":"Inspiring communicator.", "minus":"Scattered, impulsive, shallow.", "advice":"Focus with deadlines; practice discipline."},
    4:  {"name":"4 – Structure", "keywords":["discipline","stability","system"], "plus":"Practical, reliable.", "minus":"Rigid, change-averse.", "advice":"Keep structure but allow experiments."},
    5:  {"name":"5 – Freedom", "keywords":["change","experience","adventure"], "plus":"Adaptive, curious.", "minus":"Restless, excessive, non-committal.", "advice":"Freedom with guardrails (80/20)."},
    6:  {"name":"6 – Care", "keywords":["responsibility","family","aesthetics"], "plus":"Nurturing, healing.", "minus":"Over-caretaking, perfectionist.", "advice":"Self-care before care for others."},
    7:  {"name":"7 – Insight", "keywords":["research","intuition","truth"], "plus":"Deep, reflective.", "minus":"Reclusive, cynical.", "advice":"Maintain minimal social rhythm."},
    8:  {"name":"8 – Power", "keywords":["management","material","influence"], "plus":"Ambitious, managerial.", "minus":"Power stress, instrumentalize people.", "advice":"Balance power with ethics."},
    9:  {"name":"9 – Service", "keywords":["humanity","healing","closure"], "plus":"Compassionate, artistic.", "minus":"Over-sacrifice, impractical.", "advice":"Serve with boundaries; finish well."},
    11: {"name":"11 – Intuition", "keywords":["inspiration","spiritual","vision"], "plus":"High sensitivity and guidance.", "minus":"Emotional overload.", "advice":"Grounding routines: sleep, body, nature."},
    22: {"name":"22 – Master Builder", "keywords":["realization","scale","systems"], "plus":"Make vision tangible at scale.", "minus":"Over-control, burnout.", "advice":"Delegate, measure, build successors."},
    33: {"name":"33 – Compassion", "keywords":["mercy","teaching","service"], "plus":"Heal by teaching/example.", "minus":"Self-erasure.", "advice":"Treat self-care as a professional skill."}
}

def _b(n:int): return _BASE.get(n, {"name": f"{n}","keywords":[],"plus":"","minus":"","advice":""})

def describe_block(title: str, text: str) -> str:
    return f"**{title}.** {text}"

def compose(numerics: Dict, full_name: str, date_of_birth: str, system: str = "Pythagorean", role: str | None = None) -> Dict:
    lp = numerics.get("life_path")
    ex = numerics.get("expression")
    su = numerics.get("soul_urge")
    pe = numerics.get("personality")
    bd = numerics.get("birthday")
    ma = numerics.get("maturity")
    p  = numerics.get("pinnacles", [])
    c  = numerics.get("challenges", [])
    ages = numerics.get("transition_ages", [])
    py = numerics.get("personal_year")
    grid = numerics.get("lo_shu", {})
    lessons = numerics.get("karmic_lessons", [])

    def brief(n): b=_b(n); return {
        "summary": f"{b['name']}",
        "strengths": b["plus"],
        "pitfalls": b["minus"],
        "advice": b["advice"]
    }

    core = {
        "life_path": brief(lp) if lp else None,
        "expression": brief(ex) if ex else None,
        "soul_urge": brief(su) if su else None,
        "personality": brief(pe) if pe else None,
        "birthday": brief(bd) if bd else None,
        "maturity": brief(ma) if ma else None,
    }

    cycles = {
        "personal_year": f"Personal Year {py}" if py else None,
        "pinnacles": [
            {"index":i+1, "number":num, "age_from": ages[i-1] if i>0 else None, "age_to": ages[i] if i<len(ages) else None}
            for i, num in enumerate(p)
        ],
        "challenges": [{"index":i+1, "number":num} for i, num in enumerate(c)]
    }

    return {
        "header": {"system": system, "full_name": full_name, "date_of_birth": date_of_birth, "locale": "en"},
        "core": core,
        "cycles": cycles,
        "lo_shu": grid,
        "karmic": {"lessons": lessons, "note":"Numbers are symbolic. Not science."},
        "disclaimer": "Entertainment & reflection only."
    }
