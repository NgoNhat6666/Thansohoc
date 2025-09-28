
from __future__ import annotations
from typing import Dict, List
import os
import json

# ===== CẢNH BÁO =====
# Nội dung dưới đây là diễn giải tham khảo bằng tiếng Việt.
# Thần số học không phải là khoa học. Kết quả chỉ phù hợp cho mục đích tự phản tư/khai vấn.
# ====================

# Từ khoá lõi cho 1–9 và 11/22/33
_BASE = {
    1:  {"ten":"1 – Khởi xướng", "keywords":["dẫn dắt","tự chủ","tiên phong"], "plus":"Chủ động, quyết đoán, độc lập.", "minus":"Dễ độc đoán, cô lập, tự áp lực.", "advice":"Lãnh đạo bằng lắng nghe; trao quyền, không ôm hết."},
    2:  {"ten":"2 – Kết nối",   "keywords":["hợp tác","đồng cảm","ngoại giao"], "plus":"Nhạy cảm, hoà giải, tinh tế.", "minus":"Sợ xung đột, phụ thuộc cảm xúc.", "advice":"Giữ ranh giới cá nhân; nói thẳng nhu cầu."},
    3:  {"ten":"3 – Biểu đạt",  "keywords":["sáng tạo","ngôn ngữ","niềm vui"], "plus":"Dễ biểu đạt, truyền cảm hứng.", "minus":"Phân tán, bốc đồng, nông.", "advice":"Tập trung vào dự án có deadline; luyện kỷ luật."},
    4:  {"ten":"4 – Hệ thống",  "keywords":["kỷ luật","ổn định","kết cấu"], "plus":"Thực tế, bền bỉ, đáng tin.", "minus":"Cứng nhắc, sợ đổi mới.", "advice":"Giữ cấu trúc nhưng chừa không gian thử nghiệm."},
    5:  {"ten":"5 – Tự do",     "keywords":["biến đổi","trải nghiệm","mạo hiểm"], "plus":"Thích nghi, lanh lợi, yêu khám phá.", "minus":"Bồn chồn, quá đà, thiếu cam kết.", "advice":"Tự do có khung: quy tắc 80/20, lịch cố định tối thiểu."},
    6:  {"ten":"6 – Chăm sóc",  "keywords":["trách nhiệm","gia đình","thẩm mỹ"], "plus":"Quan tâm, chữa lành, thẩm mỹ tốt.", "minus":"Quá ôm đồm, cầu toàn, hay phán xét vì tốt.", "advice":"Chăm mình trước khi chăm người (nguyên tắc mặt nạ oxy)."},
    7:  {"ten":"7 – Nội quán",  "keywords":["nghiên cứu","trực giác","chân lý"], "plus":"Sâu sắc, suy tư, ưa tri thức.", "minus":"Khép kín, hoài nghi cực đoan.", "advice":"Đổi cô độc thành cô tịch: giữ nhịp xã hội tối thiểu."},
    8:  {"ten":"8 – Thành tựu", "keywords":["quản trị","vật chất","ảnh hưởng"], "plus":"Tham vọng tích cực, quản trị tốt.", "minus":"Áp lực quyền lực, công cụ hoá quan hệ.", "advice":"Cân bằng quyền lực – trách nhiệm – đạo đức."},
    9:  {"ten":"9 – Phụng sự",  "keywords":["nhân bản","chữa lành","kết thúc"], "plus":"Vị tha, bao dung, nghệ thuật/nhân văn.", "minus":"Hy sinh quá mức, mơ hồ thực tế.", "advice":"Phụng sự có ranh giới; hoàn tất, đừng kéo dài chia tay."},
    11: {"ten":"11 – Trực giác", "keywords":["truyền cảm hứng","tâm linh","tầm nhìn"], "plus":"Nhạy cảm năng lượng, soi đường.", "minus":"Quá tải cảm xúc, mất đất.", "advice":"Neo đất: thói quen cơ thể, ngủ, dinh dưỡng, thiên nhiên."},
    22: {"ten":"22 – Kiến trúc sư", "keywords":["hiện thực hoá","quy mô lớn","hệ thống xã hội"], "plus":"Biến tầm nhìn thành hệ thống bền vững.", "minus":"Quá kiểm soát, kiệt sức.", "advice":"Phân quyền, đo lường, xây đội kế thừa."},
    33: {"ten":"33 – Chữa lành", "keywords":["từ bi","giáo dưỡng","phục vụ"], "plus":"Chữa lành qua dạy–sống–làm gương.", "minus":"Tự hi sinh tới mức kiệt quệ.", "advice":"Phát triển kỹ năng chăm sóc bản thân như kỹ năng nghề."}
}

def _brief(n: int) -> Dict:
    return _BASE.get(n, {"ten": f"{n}", "keywords": [], "plus":"", "minus":"", "advice":""})

def _para(title: str, body: str) -> str:
    return f"**{title}.** {body}"

def describe_life_path(n: int) -> str:
    b = _brief(n)
    return (
        f"{b['ten']} – Đường đời (Life Path). "
        f"Chủ đề học-và-sống trọn đời của bạn xoay quanh: {', '.join(b['keywords'])}. "
        f"{_para('Thế mạnh', b['plus'])} "
        f"{_para('Điểm mù', b['minus'])} "
        f"{_para('Gợi ý thực hành', b['advice'])}"
    )

def describe_expression(n: int) -> str:
    b = _brief(n)
    return (
        f"{b['ten']} – Biểu đạt/Định mệnh (Expression/Destiny). "
        f"Cách bạn vận hành thiên bẩm và tài năng tự nhiên. "
        f"{_para('Phong cách thể hiện', ', '.join(b['keywords']))} "
        f"{_para('Đòn bẩy', b['plus'])} "
        f"{_para('Cần tránh', b['minus'])}"
    )

def describe_soul_urge(n: int) -> str:
    b = _brief(n)
    return (
        f"{b['ten']} – Nội tâm/Khát tâm (Soul Urge/Heart's Desire). "
        f"Động cơ sâu xa khiến bạn thấy có ý nghĩa. "
        f"{_para('Bạn được nạp năng lượng bởi', ', '.join(b['keywords']))} "
        f"{_para('Khi lệch pha', b['minus'])}"
    )

def describe_personality(n: int) -> str:
    b = _brief(n)
    return (
        f"{b['ten']} – Ấn tượng bên ngoài (Personality). "
        f"Cảm giác đầu tiên người khác nhận ở bạn. "
        f"{_para('Dễ thấy', b['plus'])} "
        f"{_para('Dễ hiểu nhầm', b['minus'])}"
    )

def describe_birthday(n: int) -> str:
    b = _brief(n)
    return (
        f"{b['ten']} – Con số Ngày sinh. "
        f"Tài năng trọng điểm kiểu 'món quà bẩm sinh'. "
        f"{_para('Quà tặng', b['plus'])} "
        f"{_para('Lạm dụng quà tặng', b['minus'])}"
    )

def describe_maturity(n: int) -> str:
    b = _brief(n)
    return (
        f"{b['ten']} – Trưởng thành (Maturity). "
        f"Khuynh hướng đích khi 'gộp' bài học đường đời và tài năng. "
        f"{_para('Đích đến', ', '.join(b['keywords']))} "
        f"{_para('Cái bẫy tuổi trung niên', b['minus'])}"
    )

_PERSONAL_YEAR = {
    1:"Khởi đầu, gieo hạt, tự chủ. Tốt cho bắt dự án mới; hạn chế ràng buộc cũ.",
    2:"Ủ mầm, hợp tác, kiên nhẫn. Tập trung quan hệ/đội nhóm; tránh thúc ép.",
    3:"Mở rộng biểu đạt, sáng tạo, truyền thông. Coi chừng phân tán.",
    4:"Xây nền, kỷ luật, sức khoẻ thói quen. Trả nợ kỷ luật, tối ưu hệ thống.",
    5:"Đổi mới, di chuyển, tự do có khung. Quản rủi ro, tránh quá đà.",
    6:"Gia đình, chữa lành, trách nhiệm. Cân bằng chăm người–chăm mình.",
    7:"Nội quán, học thuật, R&D, tinh lọc. Đừng cô lập; giữ thể chất.",
    8:"Thành tựu, kinh doanh, quyền hạn. Rõ mục tiêu–đo lường–đạo đức.",
    9:"Kết thúc, thu hoạch, buông, chữa lành. Dọn chỗ cho chu kỳ mới."
}

def describe_personal_year(n: int) -> str:
    return f"Năm cá nhân {n}. {_PERSONAL_YEAR.get(n, '')}"

def describe_pinnacles(pinnacles: List[int], ages: List[int]) -> List[Dict]:
    buckets = []
    # 4 đợt: [0..a1], [a1..a2], [a2..a3], [a3..]
    spans = [
        ("Giai đoạn 1", None, ages[0]),
        ("Giai đoạn 2", ages[0], ages[1]),
        ("Giai đoạn 3", ages[1], ages[2]),
        ("Giai đoạn 4", ages[2], ages[3]),
    ]
    for i, p in enumerate(pinnacles):
        b = _brief(p)
        title, start, end = spans[i]
        theme = f"Chủ đề: {', '.join(b['keywords'])}. Thế mạnh: {b['plus']} Cạm bẫy: {b['minus']}"
        buckets.append({
            "index": i+1, "number": p, "title": title, "age_from": start, "age_to": end, "theme": theme
        })
    return buckets

def describe_challenges(challenges: List[int]) -> List[str]:
    res = []
    for idx, c in enumerate(challenges, 1):
        b = _brief(c)
        res.append(f"Thử thách {idx} – số {c}: luyện bài {', '.join(b['keywords'])}. Bẫy: {b['minus']}")
    return res

# Karmic lessons – thiếu sóng năng lượng 1..9 trong tên
_LESSON = {
    1:"Thiếu tự chủ/khởi xướng. Bài học: nói 'tôi muốn', thử lãnh vai nhỏ.",
    2:"Thiếu hợp tác/tinh tế. Bài học: luyện lắng nghe, phản hồi không phòng thủ.",
    3:"Thiếu biểu đạt/sáng tạo. Bài học: viết nhật ký 10 phút/ngày, thực hành trình bày.",
    4:"Thiếu kỷ luật/kết cấu. Bài học: checklist tối thiểu, thói quen 15 phút.",
    5:"Thiếu linh hoạt/trải nghiệm. Bài học: mỗi tuần thử 1 điều mới có rào chắn an toàn.",
    6:"Thiếu chăm sóc/trách nhiệm. Bài học: hoàn thành việc nhỏ đến nơi đến chốn.",
    7:"Thiếu chiều sâu/nội quán. Bài học: lịch đọc nghiên cứu + thời gian im lặng.",
    8:"Thiếu tự thân quyền lực/tài chính. Bài học: ngân sách 50–30–20, đo lường mục tiêu.",
    9:"Thiếu vị tha/kết thúc. Bài học: luyện buông – đóng dự án đúng hạn."
}

def describe_karmic_lessons(less: List[int]) -> List[str]:
    if not less:
        return ["Không có Karmic Lesson thiếu rõ rệt từ tên (1–9 đều hiện diện)."]
    return [f"Thiếu {n}: {_LESSON[n]}" for n in less if n in _LESSON]

# Karmic debts – 13/14/16/19 (mang tính truyền thống)
_DEBT = {
    13:"13 (1–3–4): bài học kỷ luật vượt trì hoãn; lao động thông minh thay vì sức đơn thuần.",
    14:"14 (1–4–5): tự do đi kèm trách nhiệm; làm chủ xung động/đam mê.",
    16:"16 (1–6–7): sụp tự ái để tìm chân ngã; bớt kiểm soát người thân.",
    19:"19 (1–9–1): tự lực thực sự; bỏ kỳ vọng 'được cứu' hoặc ánh hào quang giả."
}

def describe_karmic_debts() -> List[str]:
    return [v for _, v in _DEBT.items()]



def describe_pyramid(pyr: Dict) -> Dict:
    base = pyr.get("base", []); mid = pyr.get("mid", []); apex = pyr.get("apex")
    expl = {
        "base": f"Hàng đáy (Tháng–Ngày–Năm rút gọn): {base}. Tháng = 'bối cảnh', Ngày = 'tính cách nổi', Năm = 'phông nền thế hệ' (tính biểu tượng).",
        "mid": f"Tầng giữa: {mid} (trái = Tháng+Ngày; phải = Ngày+Năm).",
        "apex": f"Đỉnh: {apex}. Điểm cân giữa 'trải nghiệm cá nhân' và 'bối cảnh thế hệ'."
    }
    return {"values": pyr, "explain": expl}

def enrich_pinnacles_detail(items: List[Dict]) -> List[Dict]:
    # Add short suggestions per pinnacle number from base dictionary
    out = []
    for it in items:
        n = it.get("number")
        b = _brief(n)
        it2 = dict(it)
        it2["theme"] = { "keywords": b["keywords"], "strength": b["plus"], "pitfall": b["minus"], "advice": b["advice"] }
        out.append(it2)
    return out


def describe_lo_shu(grid: Dict[str,int]) -> Dict:
    # Trả về lời bình cho từng số 1..9 và các mặt (thể–tâm–trí)
    explain_each = {}
    notes = []
    planes = {
        "Thể (1–4–7)": sum(grid.get(k,0) for k in ["1","4","7"]),
        "Tâm (2–5–8)": sum(grid.get(k,0) for k in ["2","5","8"]),
        "Trí (3–6–9)": sum(grid.get(k,0) for k in ["3","6","9"]),
    }
    for k in map(str, range(1,10)):
        cnt = grid.get(k, 0)
        if cnt == 0:
            explain_each[k] = f"Thiếu {k}: năng lượng này cần luyện chủ động."
        elif cnt == 1:
            explain_each[k] = f"Có {k} (1 lần): khuynh hướng tự nhiên vừa đủ."
        elif cnt == 2:
            explain_each[k] = f"{k} (2 lần): năng lượng nổi trội – dùng có ý thức."
        else:
            explain_each[k] = f"{k} (>=3): dồi dào – coi chừng lệch; cần kênh xả lành mạnh."
    notes.append("Lo Shu chỉ là lược đồ đếm con số ngày sinh – tính biểu tượng, không khoa học.")
    return {"each": explain_each, "planes": planes, "notes": notes}




def _match_rule(rule: dict, lp: int, ex: int, su: int, pe: int) -> bool:
    def _ok(key, val, cur):
        if key not in rule: 
            return True
        t = rule[key]
        if t is None:
            return True
        if isinstance(t, list):
            return cur in t
        return cur == t
    return _ok("lp", rule.get("lp"), lp) and _ok("ex", rule.get("ex"), ex) and _ok("su", rule.get("su"), su) and _ok("pe", rule.get("pe"), pe)

def _score_rule(rule: dict) -> int:
    # signature rules first (+100), then specificity: LP+EX (4), LP+SU (3), LP+PE (2), single (1)
    s = 0
    if rule.get('signature'): s += 100
    if 'lp' in rule and 'ex' in rule: s = max(s, 4 + s)
    if 'lp' in rule and 'su' in rule: s = max(s, 3 + s)
    if 'lp' in rule and 'pe' in rule: s = max(s, 2 + s)
    if s == 0: s = 1
    return s


def _load_context_rules() -> list:
    import json, os
    path = os.path.join(os.path.dirname(__file__), "context_rules.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _select_context(numerics: Dict, role: str | None = None) -> list:
    rules = _load_context_rules()
    lp = numerics.get('life_path'); ex = numerics.get('expression'); su = numerics.get('soul_urge'); pe = numerics.get('personality')
    role_norm = _norm_role(role)
    def _role_ok(r):
        roles = r.get('roles') or ([r.get('role')] if r.get('role') else [])
        roles = [(_norm_role(x) or '') for x in roles]
        return (not role_norm) or (role_norm in roles)
    cand = [r for r in rules if _match_rule(r, lp, ex, su, pe) and _role_ok(r)]
    # sort: signature + role match highest
    def _score(r):
        base = _score_rule(r)
        if r.get('signature'): base += 100
        if role_norm and ((r.get('roles') and role_norm in [(_norm_role(x) or '') for x in r['roles']]) or (_norm_role(r.get('role')) == role_norm)):
            base += 50
        return base
    cand.sort(key=_score, reverse=True)
    out = []
    for r in cand:
        out.append({"text": r.get('vi'), "habits": r.get('habits', []), "role": r.get('role') or r.get('roles', [])})
    return out


def _norm_role(role: str | None) -> str | None:
    if not role: return None
    r = role.strip().lower().replace(' ', '_')
    aliases = {
        'pm':'product_manager', 'product':'product_manager', 'product owner':'product_manager',
        'swe':'software_engineer','developer':'software_engineer','engineer':'software_engineer',
        'ds':'data_scientist','data':'data_scientist',
        'founder':'founder','ceo':'ceo','coo':'coo',
        'hr':'hr_leader','people':'hr_leader',
        'coach':'coach','consultant':'consultant',
        'teacher':'teacher','giáo_viên':'teacher','giáo vien':'teacher',
        'therapist':'therapist','tâm_lý':'therapist','psychotherapist':'therapist',
        'artist':'artist','writer':'writer','content':'content_creator',
        'policy':'policy_analyst','analyst':'policy_analyst',
        'doctor':'doctor','physician':'doctor','bác_sĩ':'doctor','bac si':'doctor',
        'nurse':'nurse','y_tá':'nurse','y ta':'nurse',
        'lawyer':'lawyer','luật_sư':'lawyer','luat su':'lawyer',
        'investor':'investor','vc':'investor','trader':'trader','financial_analyst':'financial_analyst','accountant':'accountant','financial_planner':'financial_planner',
        'musician':'musician','composer':'composer','filmmaker':'filmmaker','photographer':'photographer',
        'operations':'operations_manager','ops':'operations_manager','supply_chain':'supply_chain_manager','logistics':'supply_chain_manager',
        'devops':'devops_engineer','security':'security_engineer','cybersecurity':'security_engineer',
        'civil_engineer':'civil_engineer','architect':'architect','project_manager':'project_manager','customer_support':'customer_support_lead',
        'marketing':'marketing_lead','sales':'sales_lead',
        'designer':'designer','ux':'ux_researcher','researcher':'researcher'
    }
    return aliases.get(r, r)

def compose(numerics: Dict, full_name: str, date_of_birth: str, locale: str = "vi", system: str = "Pythagorean", role: str | None = None, depth: str = "standard") -> Dict:
    # numerics: output 'numbers' từ engine.analyze
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

    return {
        "header": {
            "system": system,
            "locale": locale,
            "full_name": full_name,
            "date_of_birth": date_of_birth
        },
        "core": {
            "life_path": describe_life_path(lp) if lp else None,
            "expression": describe_expression(ex) if ex else None,
            "soul_urge": describe_soul_urge(su) if su else None,
            "personality": describe_personality(pe) if pe else None,
            "birthday": describe_birthday(bd) if bd else None,
            "maturity": describe_maturity(ma) if ma else None,
        },
        "cycles": {
            "pinnacles": describe_pinnacles(p, ages) if p and ages else [],
            "pinnacles_detailed": enrich_pinnacles_detail(numerics.get("pinnacles_detailed", [])),
            "challenges": describe_challenges(c) if c else [],
            "personal_year": describe_personal_year(py) if py else None
        },
        "lo_shu": describe_lo_shu(grid),
        "pyramid": describe_pyramid(numerics.get("life_pyramid", {})),
        "context": _select_context(numerics, role=role),
        "karmic": {
            "lessons": describe_karmic_lessons(lessons),
            "debts_generic": describe_karmic_debts(),
            "note": "Bật \"trace: true\" để xem 13/14/16/19 xuất hiện ở bước nào (life_path_total, expression_total, pinnacles/challenges...)."
        },
        "disclaimer": "Diễn giải cho mục đích tự phản tư. Không thay thế tư vấn y khoa/tài chính/pháp lý."
    }


def _load_expert_pack() -> dict:
    base = os.path.join(os.path.dirname(__file__), "content")
    for fn in ["expert-pack-vi-pro.json", "expert-pack-vi.json"]:
        p = os.path.join(base, fn)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}

    # Expert Max synthesis
    try:
        if depth in ("expert","expert_max") and pack:
            lp = numerics.get("core",{}).get("life_path")
            ex = numerics.get("core",{}).get("expression")
            su = numerics.get("core",{}).get("soul_urge")
            pe = numerics.get("core",{}).get("personality")
            py = numerics.get("cycles",{}).get("personal_year")
            lp_block = pack.get("life_path",{}).get(str(lp),{})
            overlays = {
                "expression": pack.get("life_path",{}).get(str(ex),{}),
                "soul_urge": pack.get("life_path",{}).get(str(su),{}),
                "personality": pack.get("life_path",{}).get(str(pe),{})
            }
            bridges = pack.get("bridges",{})
            roles = pack.get("roles",{})
            role_key = None
            if role:
                role_key = role.lower().replace(" ","_")
            role_pack = roles.get(role_key, {}) if role_key else {}
            # Build expert sections
            summary = f"Số đường đời {lp} — {lp_block.get('theme','')}. Biểu đạt {ex}; năm cá nhân {py}."
            strengths = list(dict.fromkeys(lp_block.get("strengths",[]) + overlays["expression"].get("strengths",[]) ))
            blind = list(dict.fromkeys(lp_block.get("blindspots",[]) + overlays["expression"].get("blindspots",[]) ))
            habits = list(dict.fromkeys(lp_block.get("habits",[]) + overlays["expression"].get("habits",[]) ))
            if role_pack.get("micro"):
                habits = habits[:3] + role_pack["micro"]
            if_then = [pack.get("if_then",{}).get("overwhelm",""), pack.get("if_then",{}).get("scatter","")]
            if lp and ex:
                key = f"{lp}x{ex}"
                if key in bridges: if_then.append("Bridge: " + bridges[key])
            questions = lp_block.get("expert_questions",[])
            warnings = [pack.get("voice",{}).get("disclaimer","")]
            expert = {
                "summary": summary,
                "strengths": [x for x in strengths if x],
                "blindspots": [x for x in blind if x],
                "habits": [x for x in habits if x][:7],
                "if_then": [x for x in if_then if x],
                "questions": questions,
                "warnings": warnings,
                "role_hint": role_pack.get("lp_ex_hint")
            }
            out["expert"] = expert
    except Exception as e:
        out["expert_error"] = str(e)


def _load_cycles_pack() -> dict:
    base = os.path.join(os.path.dirname(__file__), "content", "cycles")
    out = {}
    for fn in ["personal_years_vi.json","pinnacles_vi.json"]:
        p = os.path.join(base, fn)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    out[fn] = json.load(f)
            except Exception:
                out[fn] = {}
    return out


    # Year & Pinnacle synthesis (expert-grade)
    try:
        py_map = cycles.get("personal_years_vi.json", {})
        pin_map = cycles.get("pinnacles_vi.json", {})
        cur_py = numerics.get("cycles",{}).get("personal_year")
        nxt_py = (cur_py % 9) + 1 if isinstance(cur_py,int) and cur_py >=1 else None
        year_block = None
        if cur_py and str(cur_py) in py_map:
            y = py_map[str(cur_py)]
            year_block = {
                "year": cur_py,
                "theme": y.get("theme"),
                "strengths": y.get("strengths", []),
                "pitfalls": y.get("pitfalls", []),
                "habits": y.get("habits", []),
                "metrics": y.get("metrics", [])
            }
        next_block = None
        if nxt_py and str(nxt_py) in py_map:
            y2 = py_map[str(nxt_py)]
            next_block = {
                "year": nxt_py,
                "theme": y2.get("theme"),
                "bridge": py_map[str(cur_py)].get("next_year",{}).get("bridge") if year_block else None,
                "caution": py_map[str(cur_py)].get("next_year",{}).get("caution") if year_block else None,
                "habits": y2.get("habits", [])[:3]
            }
        # Active pinnacle from numerics, then enrich
        active_pin = None
        # numerics may have stages with index, number, age_from, age_to
        p_list = numerics.get("pinnacles_detailed") or numerics.get("pinnacles") or []
        # choose one where 'current_age' falls in range if available; else first
        cur_age = numerics.get("profile",{}).get("age")
        chosen = None
        for p in p_list:
            a1 = p.get("age_from"); a2 = p.get("age_to")
            if cur_age and a1 is not None and a2 is not None and a1 <= cur_age <= a2:
                chosen = p; break
        if not chosen and p_list: chosen = p_list[0]
        if chosen:
            num = chosen.get("number")
            more = pin_map.get(str(num), {})
            active_pin = {
                "index": chosen.get("index"),
                "number": num,
                "age_from": chosen.get("age_from"),
                "age_to": chosen.get("age_to"),
                "challenge": chosen.get("challenge"),
                "theme": more.get("theme"),
                "strengths": more.get("strengths", []),
                "pitfalls": more.get("pitfalls", []),
                "practices_3_6m": more.get("practices_3_6m", []),
                "questions": more.get("questions", [])
            }
        out["years_detail"] = {"current": year_block, "next": next_block}
        out["pinnacle_detail"] = active_pin
    except Exception as e:
        out["years_error"] = str(e)
    