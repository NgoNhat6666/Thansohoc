
# Numerus — Starter (FastAPI + Plugin Rules)

A clean starter for a **thần số học** (numerology) service, designed for GitHub Codespaces and Copilot.
This project focuses on *transparency* and *modularity*: every rule is explicit, testable, and swappable.

## Quick start (Codespaces-friendly)

```bash
# If using Poetry (recommended)
poetry install
poetry run uvicorn numerus.api:app --reload --host 0.0.0.0 --port 8000

# Or with plain pip
pip install -r requirements.txt  # optional if you prefer a requirements file
uvicorn numerus.api:app --reload --host 0.0.0.0 --port 8000
```

Open: http://localhost:8000/docs

## API

**POST** `/analyze`

Example body:
```json
{
  "full_name": "Nguyen Van A",
  "date_of_birth": "2000-07-15",
  "gender": "unspecified",
  "system": "pythagorean",
  "target_year": 2025
}
```

## Features

- Unicode-safe name normalization (removes diacritics by default, configurable per system).
- Multiple systems as **plugins**: `pythagorean`, `chaldean` (extensible to Hebrew Gematria, Abjad, Greek, etc.).
- Core outputs: Life Path, Expression (Destiny), Soul Urge, Personality, Birthday, Maturity, Karmic Debts, Karmic Lessons, Pinnacles & Challenges, Personal Year, and Lo Shu grid.
- Inclusive: `gender` is optional; if provided, it is echoed only (no numerics depend on it unless a system defines it).
- Transparent: each system has a JSON config declaring mapping, reduction, master numbers, vowels policy, etc.

## Ethic & Disclaimer

Numerology is **not** a science. Treat results as entertainment and reflective prompts, not facts.
Handle personal data (name, DOB) with privacy-by-design (no logs by default, no tracking).

## Tests

```bash
poetry run pytest -q
```

## Structure

```
numerus/
  api.py          # FastAPI app
  engine.py       # core calculators
  rules.py        # loader + schema
  systems/
    pythagorean.json
    chaldean.json
tests/
  test_engine.py
.devcontainer/
  devcontainer.json
  Dockerfile
.github/workflows/
  ci.yml
```

Happy building!


---

## Diễn giải (Vietnamese narrative)

Gọi API kèm `detailed: true` để nhận phần diễn giải tiếng Việt (Life Path, Expression, Soul Urge, Personality, Birthday, Maturity, Pinnacles/Challenges, Personal Year, Lo Shu, Karmic Lessons/Debts).

**Ví dụ:**
```json
{
  "full_name": "Nguyen Van A",
  "date_of_birth": "2000-07-15",
  "system": "pythagorean",
  "target_year": 2025,
  "detailed": true
}
```

Phần diễn giải nằm ở `result.report`.


### Trace mở rộng
Thêm `trace: true` trong body để xem:
- Tổng trước khi rút gọn cho từng chỉ số (life_path_total, expression_total, soul_urge_total, personality_total, maturity_total).
- Raw steps Pinnacles/Challenges (p1_raw.., c1_raw..).
- Những nơi xuất hiện **Karmic Debts 13/14/16/19** (`karmic_debt_hits`).

```json
{
  "full_name": "Nguyen Van A",
  "date_of_birth": "2000-07-15",
  "system": "pythagorean",
  "target_year": 2025,
  "detailed": true,
  "trace": true
}
```


### Hệ quy tắc mới (non‑Latin)

Thêm sẵn:
- `greek_isopsephy` — Isopsephy (Hy Lạp), có nguyên âm Α Ε Η Ι Ο Υ Ω.
- `hebrew_gematria` — Gematria (Do Thái), không dùng nguyên âm chữ cái; có dạng cuối (ך ם ן ף ץ) cùng giá trị.
- `arabic_abjad` — Abjad (Ả Rập) theo thứ tự abjadī; có giá trị tới 1000.

> Lưu ý: các hệ non‑Latin đặt `normalization: "none"` và engine đã sửa để chỉ lấy ký tự có trong `char_map`, không ép về A‑Z.


### Nâng cấp v5
- Hệ **Vietnamese Latin**: giữ dấu tiếng Việt, map theo Pythagorean của chữ gốc.
- Reporter tiếng Anh (`en_reporter.py`): có thể mở rộng đa ngôn ngữ.
- `/export` trả HTML nhanh để chia sẻ/in ấn.
- `/examples` trả ví dụ tên hợp lệ cho từng hệ.
- Dockerfile **production** dùng gunicorn+uvicorn.
- Tests smoke cho 4 hệ mới.

> Gợi ý: thêm `?locale=en` hoặc một trường `locale` trong body để chọn reporter tiếng Anh (hiện mặc định dùng VI trong narrative). Bạn có thể hoán đổi khi cần.


### Ngữ cảnh diễn giải (context-aware dictionary)
- File `numerus/context_rules.json` định nghĩa các **tổ hợp** (ví dụ: `{"lp":1,"ex":7}`) kèm đoạn VI/EN.
- Reporter VI tự động thêm vào `report.context` các đoạn phù hợp từ tổ hợp core numbers (LP/EX/SU/PE).
- Bạn có thể mở rộng rules bằng cách thêm item JSON mới (không cần sửa code).

### Bảo vệ API bằng API keys
- Bật biến môi trường `REQUIRE_API_KEY=1` và đặt danh sách `API_KEYS="key1,key2"`.
- Gửi header `X-API-Key: <key>` khi gọi `POST /analyze` và `POST /export`.
- `/health`, `/systems`, `/examples` để **open** cho client kiểm tra kết nối.

Xem `.env.example` để cấu hình nhanh.


### Nâng cấp v7 (pro)
- **Locale** trong body (`locale: "vi"|"en"`) → chọn reporter tương ứng.
- **Context engine** thông minh: rule có thể là số, mảng số, hoặc bỏ qua; ưu tiên LP×EX > LP×SU > LP×PE > đơn lẻ.
- **Rate limit** in-memory (mặc định 60 req/phút mỗi API key hoặc IP) — cấu hình `RATE_LIMIT_PER_MIN`.
- **Audit ẩn danh**: bật `AUDIT=1` + `AUDIT_SECRET=...` → log HMAC(name|dob) vào `/app_audit.log` (không lưu PII thô).
- **CORS** qua `ALLOW_ORIGINS`.
- **Batch** endpoint `/analyze/batch`.
- **Export HTML** có CSS cơ bản và locale narrative.

Env mẫu:
```
REQUIRE_API_KEY=1
API_KEYS=dev_key_123
RATE_LIMIT_PER_MIN=60
AUDIT=1
AUDIT_SECRET=replace_with_long_random
ALLOW_ORIGINS=*
```


## Nâng cấp v8 (Enterprise)
- **JWT** (tùy chọn) bên cạnh API key: bật `REQUIRE_JWT=1, JWT_SECRET=..., JWT_ALG=HS256, JWT_AUD=...`.
- **Rate limit Redis**: đặt `REDIS_URL=redis://...` để chuyển limiter sang Redis (phân tán). Fallback: in-memory.
- **Prometheus /metrics**: theo dõi request count/latency.
- **Structured logs** JSON ra stdout.
- **Webhook**: `WEBHOOK_URL=https://...` để nhận payload sau analyze/export.
- **PDF export** `/export/pdf` với ReportLab (fallback giữ HTML ở `/export`).

### Đỉnh cao cuộc đời & Kim tự tháp
- `numbers.pinnacles_detailed`: mỗi giai đoạn có số đỉnh, **challenge**, tuổi bắt–kết, và **theme** (từ khóa, điểm mạnh, bẫy, gợi ý).
- `numbers.life_pyramid`: kim tự tháp 3 tầng (Month–Day–Year rút gọn → tầng giữa → đỉnh). Reporter VI giải thích ý nghĩa từng tầng.



## v9 — Enterprise best practices
- **Versioned API**: all core endpoints under `/v1`.
- **Tenant & Quota**: API key format `tenant:KEY`. Monthly quota per tenant from `QUOTAS_JSON` (Redis-backed if `REDIS_URL` set).
- **JWT scopes**: require `admin` scope for admin endpoints; extendable to `analyze:read`, `export:write`.
- **Security headers**: HSTS, X-Frame-Options, etc.; **Request ID** in every response.
- **Probes**: `/livez`, `/readyz` (checks Redis).
- **Error metrics**: Prometheus counters for 4xx/5xx by endpoint.
- **Admin**: inspect/reset quota (JWT admin).

Sample env:
```
QUOTAS_JSON={"default":20000,"vip":200000}
REQUIRE_JWT=1
JWT_SECRET=replace_with_long_random
JWT_ALG=HS256
JWT_AUD=numerus
```
