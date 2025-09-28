
from __future__ import annotations
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
import datetime, re

from .rules import SystemRules, normalize_name

TRACE_DEBTS = {13,14,16,19}

DIGITS = set("0123456789")

def reduce_number(n: int, rules: SystemRules) -> int:
    # Classic reduction: keep master numbers if configured
    if n < 10:
        return n
    if rules.keep_master and n in rules.master_numbers:
        return n
    s = sum(int(d) for d in str(n))
    if rules.keep_master and s in rules.master_numbers:
        return s
    while s >= 10:
        if rules.keep_master and s in rules.master_numbers:
            break
        s = sum(int(d) for d in str(s))
    return s

def letters_of(name: str, rules: SystemRules) -> Tuple[List[str], List[str]]:
    # Returns (vowels, consonants) after normalization and uppercasing
    normalized = normalize_name(name, rules.normalization).upper()
    # Keep only A-Z and spaces
    filtered = re.sub(r"[^A-Z\s]", "", normalized)
    parts = filtered.split()
    vowels, consonants = [], []
    for ch in filtered:
        if ch == " ":
            continue
        key = ch.upper()
        if key not in rules.char_map:
            continue
        if key == "Y":
            if rules.include_y_as_vowel:
                vowels.append(key)
            else:
                consonants.append(key)
        elif key in rules.vowels:
            vowels.append(key)
        else:
            consonants.append(key)
    return vowels, consonants

def letters_all(name: str, rules: SystemRules) -> List[str]:
    normalized = normalize_name(name, rules.normalization).upper()
    filtered = re.sub(r"[^A-Z\s]", "", normalized)
    return [ch for ch in filtered if ch != " "]

def sum_letters(letters: List[str], rules: SystemRules) -> int:
    total = 0
    for ch in letters:
        total += rules.char_map.get(ch, 0)
    return total

def date_parts(dob: str) -> Tuple[int, int, int]:
    # dob = YYYY-MM-DD
    y, m, d = map(int, dob.split("-"))
    return y, m, d

def life_path(dob: str, rules: SystemRules) -> int:
    y, m, d = date_parts(dob)
    # sum of all digits (with master rule)
    total = sum(int(c) for c in f"{y:04d}{m:02d}{d:02d}")
    return reduce_number(total, rules)

def birthday_number(dob: str, rules: SystemRules) -> int:
    day = int(dob.split("-")[2])
    return reduce_number(day, rules)

def expression_number(full_name: str, rules: SystemRules) -> int:
    letters = letters_all(full_name, rules)
    return reduce_number(sum_letters(letters, rules), rules)

def soul_urge_number(full_name: str, rules: SystemRules) -> int:
    v, _ = letters_of(full_name, rules)
    return reduce_number(sum_letters(v, rules), rules)

def personality_number(full_name: str, rules: SystemRules) -> int:
    _, c = letters_of(full_name, rules)
    return reduce_number(sum_letters(c, rules), rules)

def maturity_number(full_name: str, dob: str, rules: SystemRules) -> int:
    lp = life_path(dob, rules)
    ex = expression_number(full_name, rules)
    return reduce_number(lp + ex, rules)

def karmic_debts(n: int) -> List[int]:
    debts = []
    for kd in (13, 14, 16, 19):
        if n == kd or any(sum(int(d) for d in str(v)) == kd for v in (n,)):
            # We only mark the configuration number itself; detailed placement is in report composition.
            pass
    # Standard presentation is to tag if any calculated raw sums hit these numbers before reduction;
    # We will expose where they occurred in the analysis (implemented below).
    return [13, 14, 16, 19]

def compute_karmic_lessons(full_name: str, rules: SystemRules) -> List[int]:
    # Which digit-values 1..9 are missing in the name mapping distribution
    letters = letters_all(full_name, rules)
    seen = set(rules.char_map.get(ch, 0) for ch in letters if ch in rules.char_map)
    return [d for d in range(1, 10) if d not in seen]

def pinnacles_and_challenges(dob: str, rules: SystemRules):
    y, m, d = date_parts(dob)

    rm = reduce_number(m, rules)
    rd = reduce_number(d, rules)
    ry = reduce_number(y, rules)

    p1 = reduce_number(rm + rd, rules)
    p2 = reduce_number(rd + ry, rules)
    p3 = reduce_number(p1 + p2, rules)
    p4 = reduce_number(rm + ry, rules)

    c1 = abs(rm - rd)
    c2 = abs(rd - ry)
    c3 = abs(c1 - c2)
    c4 = abs(rm - ry)

    # age cycles (standard scheme: first pinnacle to 36 - life_path, then 9-year cycles)
    lp = life_path(dob, rules)
    first_transition_age = 36 - lp
    return {
        "pinnacles": [p1, p2, p3, p4],
        "challenges": [reduce_number(c1, rules), reduce_number(c2, rules),
                       reduce_number(c3, rules), reduce_number(c4, rules)],
        "transition_ages": [first_transition_age, first_transition_age + 9, first_transition_age + 18, first_transition_age + 27]
    }



def life_pyramid(dob: str, rules: SystemRules):
    # Working convention:
    # Base row: reduced Month (M), Day (D), Year (Y)
    # Next row: L = reduce(M + D), R = reduce(D + Y)
    # Apex: A = reduce(L + R)
    # Return structure and a simple age mapping aligned with pinnacles transitions.
    y, m, d = date_parts(dob)
    M = reduce_number(m, rules)
    D = reduce_number(d, rules)
    Y = reduce_number(y, rules)
    L = reduce_number(M + D, rules)
    R = reduce_number(D + Y, rules)
    A = reduce_number(L + R, rules)
    return {
        "base": [M, D, Y],
        "mid": [L, R],
        "apex": A
    }

def detailed_pinnacles(dob: str, rules: SystemRules):
    data = pinnacles_and_challenges(dob, rules)
    p = data["pinnacles"]; c = data["challenges"]; ages = data["transition_ages"]
    out = []
    spans = [
        (None, ages[0]),
        (ages[0], ages[1]),
        (ages[1], ages[2]),
        (ages[2], ages[3])
    ]
    for i, num in enumerate(p):
        out.append({
            "index": i+1,
            "number": num,
            "challenge": c[i] if i < len(c) else None,
            "age_from": spans[i][0],
            "age_to": spans[i][1]
        })
    return out


def personal_year(dob: str, target_year: int, rules: SystemRules) -> int:
    y, m, d = date_parts(dob)
    total = sum(int(c) for c in f"{target_year:04d}{m:02d}{d:02d}")
    return reduce_number(total, rules)

def lo_shu_grid(dob: str) -> Dict[str, int]:
    digits = [c for c in dob if c.isdigit()]
    counts = {str(i): 0 for i in range(1, 10)}
    for d in digits:
        if d != '0' and d in counts:
            counts[d] += 1
    return counts

@dataclass
class AnalysisInput:
    full_name: str
    date_of_birth: str  # ISO YYYY-MM-DD
    gender: str | None = None
    system: str = "pythagorean"
    target_year: int | None = None

def analyze(inp: AnalysisInput, rules: SystemRules, trace: bool = False) -> Dict:
    # Basic validation
    try:
        y, m, d = inp.date_of_birth.split("-")
        _ = datetime.date(int(y), int(m), int(d))
    except Exception as e:
        raise ValueError("date_of_birth must be YYYY-MM-DD and valid")

    report: Dict = {"system": rules.name, "input": {"full_name": inp.full_name, "date_of_birth": inp.date_of_birth, "gender": inp.gender}}

    lp = life_path(inp.date_of_birth, rules)
    bd = birthday_number(inp.date_of_birth, rules)
    ex = expression_number(inp.full_name, rules)
    su = soul_urge_number(inp.full_name, rules)
    pe = personality_number(inp.full_name, rules)
    ma = maturity_number(inp.full_name, inp.date_of_birth, rules)

    pc = pinnacles_and_challenges(inp.date_of_birth, rules)
    py = personal_year(inp.date_of_birth, inp.target_year or datetime.date.today().year, rules)
    grid = lo_shu_grid(inp.date_of_birth)
    lessons = compute_karmic_lessons(inp.full_name, rules)

    report["numbers"] = {
        "life_path": lp,
        "birthday": bd,
        "expression": ex,
        "soul_urge": su,
        "personality": pe,
        "maturity": ma,
        "pinnacles": pc["pinnacles"],
        "challenges": pc["challenges"],
        "transition_ages": pc["transition_ages"],
        "personal_year": py,
        "lo_shu": grid,
        "life_pyramid": life_pyramid(inp.date_of_birth, rules),
        "pinnacles_detailed": detailed_pinnacles(inp.date_of_birth, rules),
        "karmic_lessons": lessons
    }

    # Build detailed trace if requested
    if trace:
        raw = {}
        # DOB components
        y, m, d = date_parts(inp.date_of_birth)
        raw["dob"] = {
            "year": y, "month": m, "day": d,
            "sum_all_digits": sum(int(c) for c in f"{y:04d}{m:02d}{d:02d}")
        }
        # Name sums
        v_letters, c_letters = letters_of(inp.full_name, rules)
        all_letters = letters_all(inp.full_name, rules)
        v_sum = sum_letters(v_letters, rules)
        c_sum = sum_letters(c_letters, rules)
        all_sum = sum_letters(all_letters, rules)
        raw["name"] = {
            "vowels_sum": v_sum,
            "consonants_sum": c_sum,
            "all_sum": all_sum,
            "vowels_letters": v_letters,
            "consonants_letters": c_letters,
            "all_letters": all_letters
        }
        # Key numbers before reduction
        raw["pre_reduction"] = {
            "life_path_total": raw["dob"]["sum_all_digits"],
            "birthday_day": d,
            "expression_total": all_sum,
            "soul_urge_total": v_sum,
            "personality_total": c_sum,
            "maturity_total": raw["dob"]["sum_all_digits"] + all_sum  # lp (pre-red) + expression (pre-red)
        }
        # Pinnacles & challenges raw steps
        rm = reduce_number(m, rules)  # as per engine logic we use reduced m,d,y to build pinnacles
        rd = reduce_number(d, rules)
        ry = reduce_number(y, rules)
        raw["pinnacles_raw"] = {
            "rm": rm, "rd": rd, "ry": ry,
            "p1_raw": rm + rd,
            "p2_raw": rd + ry,
            "p3_raw": reduce_number(rm + rd, rules) + reduce_number(rd + ry, rules),
            "p4_raw": rm + ry,
            "c1_raw": abs(rm - rd),
            "c2_raw": abs(rd - ry),
            "c3_raw": abs(abs(rm - rd) - abs(rd - ry)),
            "c4_raw": abs(rm - ry)
        }
        # Karmic debts detection: where 13/14/16/19 appear before reduction
        debt_hits = []
        for label, val in [
            ("life_path_total", raw["pre_reduction"]["life_path_total"]),
            ("birthday_day", raw["pre_reduction"]["birthday_day"]),
            ("expression_total", raw["pre_reduction"]["expression_total"]),
            ("soul_urge_total", raw["pre_reduction"]["soul_urge_total"]),
            ("personality_total", raw["pre_reduction"]["personality_total"]),
            ("maturity_total", raw["pre_reduction"]["maturity_total"]),
            ("p1_raw", raw["pinnacles_raw"]["p1_raw"]),
            ("p2_raw", raw["pinnacles_raw"]["p2_raw"]),
            ("p3_raw", raw["pinnacles_raw"]["p3_raw"]),
            ("p4_raw", raw["pinnacles_raw"]["p4_raw"]),
            ("c1_raw", raw["pinnacles_raw"]["c1_raw"]),
            ("c2_raw", raw["pinnacles_raw"]["c2_raw"]),
            ("c3_raw", raw["pinnacles_raw"]["c3_raw"]),
            ("c4_raw", raw["pinnacles_raw"]["c4_raw"]),
        ]:
            if val in TRACE_DEBTS:
                debt_hits.append({"where": label, "value": val})
        raw["karmic_debt_hits"] = debt_hits
        report["trace"] = raw
    else:
        report["trace"] = {"enabled": False}

    report["disclaimer"] = (
        "Numerology is not science. Treat this as entertainment and reflective prompts, not factual claims. "
        "We do not use gender in calculations unless a system explicitly defines it."
    )
    return report
