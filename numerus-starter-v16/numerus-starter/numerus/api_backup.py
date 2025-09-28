
from __future__ import annotations
from fastapi import FastAPI, HTTPException, APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional
from .rules import SystemRules
from .engine import analyze, AnalysisInput

from fastapi import Depends, Header
import os


import jwt
from typing import Optional
import json
import datetime


import requests, time
_JWKS = None
_JWKS_TS = 0

def _get_jwks():
    global _JWKS, _JWKS_TS
    url = os.getenv("JWKS_URL")
    now = time.time()
    if not url:
        return None
    if _JWKS and now - _JWKS_TS < 3600:
        return _JWKS
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        _JWKS = resp.json()
        _JWKS_TS = now
        return _JWKS
    except Exception:
        return None


def require_jwt():
    def inner(authorization: Optional[str] = Header(default=None, alias="Authorization")):
        if os.getenv("REQUIRE_JWT","0").lower() not in ("1","true","yes"):
            return None
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")
        token = authorization.split(" ",1)[1]
        alg = os.getenv("JWT_ALG","HS256")
        audience = os.getenv("JWT_AUD","")
        jwks = _get_jwks()
        options = {"verify_aud": bool(audience)}
        try:
            if jwks:
                import json
                from jwt import algorithms as _alg
                hdr = jwt.get_unverified_header(token)
                kid = hdr.get('kid')
                key = None
                for k in jwks.get('keys', []):
                    if k.get('kid') == kid:
                        key = _alg.RSAAlgorithm.from_jwk(json.dumps(k))
                        break
                if not key:
                    raise HTTPException(status_code=401, detail="JWKS key not found")
                decoded = jwt.decode(token, key=key, algorithms=[alg,'RS256','RS384','RS512'], audience=audience or None, options=options)
            else:
                secret = os.getenv('JWT_SECRET','')
                decoded = jwt.decode(token, secret, algorithms=[alg], audience=audience or None, options=options)
            scopes = decoded.get("scope","").split() if isinstance(decoded.get("scope"), str) else decoded.get("scopes", [])
            return {"sub": decoded.get("sub"), "scopes": scopes, "claims": decoded}
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid JWT")
    return inner
def require_scope(required: str):
    def inner(jwt_info: dict | None = Depends(require_jwt)):
        if os.getenv("REQUIRE_JWT","0").lower() not in ("1","true","yes"):
            return True
        scopes = (jwt_info or {}).get("scopes", [])
        if required in scopes:
            return True
        raise HTTPException(status_code=403, detail=f"Missing scope: {required}")
    return inner


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    require = os.getenv("REQUIRE_API_KEY", "0").lower() in ("1","true","yes")
    if not require:
        return True
    keys = [k.strip() for k in os.getenv("API_KEYS","").split(",") if k.strip()]
    if not keys:
        # If required but no keys set, deny all
        raise HTTPException(status_code=401, detail="API key required (server not configured)")
    if x_api_key in keys:
        return True
    raise HTTPException(status_code=401, detail="Invalid or missing API key")



import logging, sys
from logging.handlers import TimedRotatingFileHandler
class JsonFormatter(logging.Formatter):
    def format(self, record):
        import json, time
        data = {
            "ts": int(time.time()),
            "level": record.levelname,
            "msg": record.getMessage(),
            "name": record.name
        }
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)
handler = logging.StreamHandler(sys.stdout)
audit_handler = TimedRotatingFileHandler('/app_audit.log', when='midnight', backupCount=7)
audit_handler.setFormatter(JsonFormatter())
logging.getLogger().addHandler(audit_handler)
handler.setFormatter(JsonFormatter())
logging.getLogger().handlers = [handler]
logging.getLogger().setLevel(logging.INFO)


import uuid
from starlette.middleware.base import BaseHTTPMiddleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'none'"
        if request.url.scheme == "https":
            response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
        return response
app = FastAPI(title="Numerus API", version="1.0.0")
router = APIRouter(prefix="/v1")

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time, hmac, hashlib, json as _json
import redis

# CORS from env
origins = [o.strip() for o in os.getenv("ALLOW_ORIGINS","*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory rate limit (simple fixed window)
_RATE_LIMIT = {}
_REDIS = None
if os.getenv('REDIS_URL'):
    try:
        _REDIS = redis.from_url(os.getenv('REDIS_URL'))
    except Exception:
        _REDIS = None
def _rate_key(request: Request, api_key: str | None):
    if api_key:
        return f"key:{api_key}"
    # fallback to ip
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path not in ["/analyze", "/export", "/analyze/batch"]:
            return await call_next(request)
        limit = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))
        api_key = request.headers.get("X-API-Key")
        key = _rate_key(request, api_key)
        now = int(time.time() // 60)
        if _REDIS:
            rkey = f"rl:{key}:{now}"
            try:
                cnt = _REDIS.incr(rkey)
                _REDIS.expire(rkey, 90)
            except Exception:
                cnt = None
            if cnt and int(cnt) > limit:
                return Response(status_code=429, content=_json.dumps({"detail":"Rate limit exceeded"}), media_type="application/json")
        else:
            bucket = _RATE_LIMIT.get(key, {"ts": now, "count": 0})
            if bucket["ts"] != now:
                bucket = {"ts": now, "count": 0}
            bucket["count"] += 1
            _RATE_LIMIT[key] = bucket
            if bucket["count"] > limit:
                return Response(status_code=429, content=_json.dumps({"detail":"Rate limit exceeded"}), media_type="application/json")
        return await call_next(request)

app.add_middleware(RateLimitMiddleware)

import calendar

def _tenant_from_key(key: str | None) -> str | None:
    # key format: tenant:keyvalue OR plain key -> tenant "default"
    if not key:
        return None
    if ":" in key:
        t, _ = key.split(":",1)
        return t
    return "default"

def _quota_bucket(tenant: str) -> str:
    now = datetime.datetime.utcnow()
    ym = f"{now.year}{now.month:02d}"
    return f"quota:{tenant}:{ym}"

def _quota_limit_for(tenant: str) -> int:
    # From JSON mapping in env QUOTAS_JSON='{"default": 10000, "vip": 100000}'
    try:
        import json
        mapping = json.loads(os.getenv("QUOTAS_JSON","{}"))
        return int(mapping.get(tenant, mapping.get("default", 10000)))
    except Exception:
        return 10000

def _plan_of(tenant: str) -> str:
    # Map tenant to plan: env PLAN_JSON='{"default":"free","vip":"enterprise"}'
    try:
        import json
        m = json.loads(os.getenv("PLAN_JSON","{}"))
        return m.get(tenant, m.get("default","free"))
    except Exception:
        return "free"

def _quota_check_and_decr(tenant: str) -> bool:
    if not tenant:
        return True
    limit = _quota_limit_for(tenant)
    if limit <= 0:
        return True
    # redis if available
    global _REDIS
    import datetime
    bucket = _quota_bucket(tenant)
    if _REDIS:
        try:
            cnt = _REDIS.get(bucket)
            if cnt is None:
                # set initial count = limit-1
                now = datetime.datetime.utcnow()
                last_day = calendar.monthrange(now.year, now.month)[1]
                # expire at next month 1st day
                # approximate: 35 days ttl
                ttl = 35*24*3600
                _REDIS.set(bucket, limit-1, ex=ttl)
                return True
            else:
                val = int(cnt)
                if val <= 0:
                    return False
                _REDIS.decr(bucket)
                return True
        except Exception:
            pass
    # fallback memory
    global _RATE_LIMIT
    memq = _RATE_LIMIT.get(bucket, limit)
    if memq <= 0:
        return False
    _RATE_LIMIT[bucket] = memq - 1
    return True


# Audit logging (no PII): HMAC of (name|dob) with AUDIT_SECRET

import urllib.request

def _post_webhook(kind: str, payload: dict, trace_id: str | None = None):
    url = os.getenv("WEBHOOK_URL")
    if not url:
        return
    try:
        body = {"kind": kind, "payload": payload}
        if trace_id: body["trace_id"] = trace_id
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def audit_event(kind: str, name: str, dob: str, system: str, ok: bool, extras: dict | None = None):
    if os.getenv("AUDIT","0").lower() not in ("1","true","yes"):
        return
    secret = os.getenv("AUDIT_SECRET","").encode("utf-8")
    msg = f"{name}|{dob}".encode("utf-8")
    user_id = hmac.new(secret, msg, hashlib.sha256).hexdigest() if secret else "anon"
    rec = {"ts": int(time.time()), "kind": kind, "user": user_id, "system": system, "ok": ok}
    if extras:
        rec.update(extras)
    try:
        with open("/app_audit.log","a", encoding="utf-8") as f:
            f.write(_json.dumps(rec, ensure_ascii=False)+"\n")
    except Exception:
        pass


class AnalyzeRequest(BaseModel):
    full_name: str = Field(..., description="Full name to analyze")
    date_of_birth: str = Field(..., description="YYYY-MM-DD")
    gender: Optional[str] = Field(default=None, description="Optional gender (echoed only)")
    system: str = Field(default="pythagorean", description="Numerology system")
    target_year: Optional[int] = Field(default=None, description="For personal year calculations")
    detailed: bool = Field(default=True, description="Include narrative report")
    trace: bool = Field(default=False, description="Return extended computation trace")
    locale: Optional[str] = Field(default="vi", description="Narrative locale: vi|en")
    role: Optional[str] = Field(default=None, description="User role, e.g., product_manager, researcher, teacher")
    depth: Optional[str] = Field(default="standard", description="Narrative depth: basic|standard|expert|expert_max")

@router.post("/analyze")
def post_analyze(req: AnalyzeRequest, request: Request, _: bool = Depends(require_api_key), __: dict | None = Depends(require_jwt)):
    tenant = _tenant_from_key(os.getenv('DUMMY','') or '')
    # prefer header key for tenant
    tenant = _tenant_from_key(req.__dict__.get('_api_key', None)) if hasattr(req, '__dict__') else None
    # quota
    tenant = _tenant_from_key(request.headers.get('X-API-Key'))
    if not _quota_check_and_decr(tenant):
        raise HTTPException(status_code=402, detail="Quota exceeded for tenant")
    try:
        rules = SystemRules.load(req.system)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    tenant = _tenant_from_key(request.headers.get('X-API-Key'))
    if not _quota_check_and_decr(tenant):
        raise HTTPException(status_code=402, detail="Quota exceeded for tenant")
    try:
        result = analyze(
            AnalysisInput(
                full_name=req.full_name,
                date_of_birth=req.date_of_birth,
                gender=req.gender,
                system=req.system,
                target_year=req.target_year,
            ),
            rules=rules,
            trace=req.trace
        )
        # Compose narrative if requested
        if req.detailed:
            try:
                from . import reporter
                result["report"] = reporter.compose(
                    numerics=result.get("numbers", {}),
                    full_name=req.full_name,
                    date_of_birth=req.date_of_birth,
                    locale="vi",
                    system=rules.name
                )
            except Exception:
                # Fail-soft: ignore narrative errors
                result["report_error"] = "reporter_failed"
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")


@router.get("/health")
def get_health():
    return {"status": "ok"}

@router.get("/systems")
def get_systems():
    from .rules import DATA_DIR
    import os, json
    systems = []
    for fn in os.listdir(DATA_DIR):
        if fn.endswith(".json"):
            with open(os.path.join(DATA_DIR, fn), "r", encoding="utf-8") as f:
                data = json.load(f)
                systems.append({"id": fn.replace(".json",""), "name": data.get("name")})
    return {"systems": systems}


from fastapi.responses import HTMLResponse

@app.post("/export", response_class=HTMLResponse)
from fastapi import Request
@router.post("/export")
def post_export(req: AnalyzeRequest, request: Request, _: bool = Depends(require_api_key), __: dict | None = Depends(require_jwt)):
    # Reuse analyze then render minimal HTML
    # quota
    tenant = _tenant_from_key(request.headers.get('X-API-Key'))
    if not _quota_check_and_decr(tenant):
        raise HTTPException(status_code=402, detail="Quota exceeded for tenant")
    try:
        rules = SystemRules.load(req.system)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # quota
    tenant = _tenant_from_key(request.headers.get('X-API-Key'))
    if not _quota_check_and_decr(tenant):
        raise HTTPException(status_code=402, detail="Quota exceeded for tenant")
    try:
        result = analyze(
        AnalysisInput(
            full_name=req.full_name,
            date_of_birth=req.date_of_birth,
            gender=req.gender,
            system=req.system,
            target_year=req.target_year,
        ),
        rules=rules,
        trace=req.trace
    )
    except Exception as e:
        audit_event('export', req.full_name, req.date_of_birth, rules.name, False, {'error': str(e)})
        raise

    # Locale switch for narrative
    narrative = None
    if req.detailed:
        try:
            if getattr(req, "gender", None) == "en" or (hasattr(req, "system") and False):
                pass
        except Exception:
            pass
        try:
            # Choose reporter by query param `?locale=en` (fallback vi)
            # FastAPI doesn't directly parse query in body, so infer via gender misuse isn't right;
            # Instead, allow header-like override via system name convention (not ideal). Keep vi default.
            from . import reporter as vi
            narrative = vi.compose(result.get("numbers", {}), req.full_name, req.date_of_birth, locale="vi", system=rules.name, role=req.role)
        except Exception:
            narrative = None

    # Simple HTML (no CSS heavy)
    nums = result.get("numbers", {})
    def row(k, v):
        return f"<tr><td><b>{k}</b></td><td>{v}</td></tr>"
    core_rows = "".join([
        row("Life Path", nums.get("life_path")),
        row("Birthday", nums.get("birthday")),
        row("Expression", nums.get("expression")),
        row("Soul Urge", nums.get("soul_urge")),
        row("Personality", nums.get("personality")),
        row("Maturity", nums.get("maturity")),
        row("Personal Year", nums.get("personal_year")),
    ])
    html = f"""
    <html><head><meta charset='utf-8'><title>Numerus Report</title><style>body{font-family:system-ui,Arial,sans-serif;max-width:900px;margin:32px auto;line-height:1.5}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:6px 10px}h1{margin-bottom:8px}small{color:#666}</style></head>
    <body>
      <h1>Numerus Report</h1>
      <p><b>Name:</b> {req.full_name} — <b>DOB:</b> {req.date_of_birth} — <b>System:</b> {rules.name}</p>
      <h2>Core Numbers</h2>
      <table border="1" cellpadding="6" cellspacing="0">{core_rows}</table>
      {"<h2>Narrative</h2><pre>"+json.dumps(narrative, ensure_ascii=False, indent=2)+"</pre>" if narrative else ""}
      <hr/>
      <small>Disclaimer: Numerology is not science. For reflection only.</small>
    </body></html>
    """
    audit_event('export', req.full_name, req.date_of_birth, rules.name, True)
    _post_webhook('export', result, trace_id=request.headers.get('X-Request-ID'))
    return HTMLResponse(content=html, status_code=200)


@router.get("/examples")
def get_examples():
    return {
        "pythagorean": ["Nguyen Van A", "Tran Thi B"],
        "chaldean": ["Nguyen Van A", "Tran Thi B"],
        "vietnamese_latin": ["Trần Thị Thu Hà", "Đặng Hoàng Anh"],
        "greek_isopsephy": ["ΙΩΑΝΝΗΣ", "ΣΟΦΙΑ"],
        "hebrew_gematria": ["שלום", "דוד"],
        "arabic_abjad": ["محمد", "علي"]
    }


class AnalyzeBatchRequest(BaseModel):
    items: list[AnalyzeRequest]

@router.post("/analyze/batch")
from fastapi import Request
@router.post("/analyze/batch")
def post_analyze_batch(req: AnalyzeBatchRequest, request: Request, _: bool = Depends(require_api_key), __: dict | None = Depends(require_jwt)):
    # quota (1 per item)
    tenant = _tenant_from_key(request.headers.get('X-API-Key'))
    out = []
    for item in req.items:
        # quota per item
        if not _quota_check_and_decr(tenant):
            out.append({"ok": False, "error": "Quota exceeded"}); continue
        try:
            rules = SystemRules.load(item.system)
            res = analyze(
                AnalysisInput(
                    full_name=item.full_name,
                    date_of_birth=item.date_of_birth,
                    gender=item.gender,
                    system=item.system,
                    target_year=item.target_year,
                ),
                rules=rules,
                trace=item.trace
            )
            # Narrative
            try:
                if (item.locale or "vi").lower().startswith("en"):
                    from . import en_reporter as rep
                    res["report"] = rep.compose(res.get("numbers", {}), item.full_name, item.date_of_birth, system=rules.name, role=item.role)
                else:
                    from . import reporter as rep
                    res["report"] = rep.compose(res.get("numbers", {}), item.full_name, item.date_of_birth, locale="vi", system=rules.name, role=item.role)
            except Exception:
                res["report_error"] = "reporter_failed"
            out.append({"ok": True, "data": res})
            audit_event("analyze", item.full_name, item.date_of_birth, rules.name, True, {"batch": True})
        except Exception as e:
            out.append({"ok": False, "error": str(e)})
            audit_event("analyze", item.full_name, item.date_of_birth, item.system, False, {"batch": True})
    return {"results": out}


from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
REQS = Counter('numerus_requests_total','Total requests',['endpoint'])
ERR4 = Counter('numerus_errors_4xx_total','4xx errors',['endpoint'])
ERR5 = Counter('numerus_errors_5xx_total','5xx errors',['endpoint'])
LAT = Histogram('numerus_latency_seconds','Request latency',['endpoint'])

@app.middleware("http")
async def prom_mw(request, call_next):
    endpoint = request.url.path
    with LAT.labels(endpoint).time():
        resp = await call_next(request)
    try:
        REQS.labels(endpoint).inc()
        if 400 <= resp.status_code < 500:
            ERR4.labels(endpoint).inc()
        if resp.status_code >= 500:
            ERR5.labels(endpoint).inc()
    except Exception:
        pass
    return resp

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


from reportlab.lib.pagesizes import A4
import qrcode
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
from fastapi.responses import StreamingResponse

@app.post("/export/pdf")
def post_export_pdf(req: AnalyzeRequest, _: bool = Depends(require_api_key), __: dict | None = Depends(require_jwt)):
    # compute
    # quota
    tenant = _tenant_from_key(request.headers.get('X-API-Key'))
    if not _quota_check_and_decr(tenant):
        raise HTTPException(status_code=402, detail="Quota exceeded for tenant")
    try:
        rules = SystemRules.load(req.system)
        result = analyze(
            AnalysisInput(
                full_name=req.full_name,
                date_of_birth=req.date_of_birth,
                gender=req.gender,
                system=req.system,
                target_year=req.target_year,
            ),
            rules=rules,
            trace=req.trace
        )
    except Exception as e:
        audit_event('export_pdf', req.full_name, req.date_of_birth, req.system, False, {'error': str(e)})
        raise
    # narrative
    narrative = None
    try:
        if (req.locale or "vi").lower().startswith("en"):
            from . import en_reporter as rep
            narrative = rep.compose(result.get("numbers", {}), req.full_name, req.date_of_birth, system=rules.name, role=req.role, depth=req.depth)
        else:
            from . import reporter as rep
            narrative = rep.compose(result.get("numbers", {}), req.full_name, req.date_of_birth, locale="vi", system=rules.name, role=req.role, depth=req.depth)
    except Exception:
        narrative = None
    # draw
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 40
    def line(txt, size=10):
        nonlocal y
        c.setFont("Helvetica", size)
        c.drawString(36, y, txt[:120])
        y -= size + 4
        if y < 60:
            c.showPage()
            y = h - 40
    line("Numerus Report", 14)
    line(f"Name: {req.full_name} | DOB: {req.date_of_birth} | System: {rules.name} | Role: {getattr(req, "role", None) or "n/a"}", 10)
    nums = result.get("numbers", {})
    for key in ["life_path","birthday","expression","soul_urge","personality","maturity","personal_year"]:
        line(f"{key}: {nums.get(key)}")
    line("— Pinnacles —", 12)
    for it in result.get("numbers",{}).get("pinnacles", []):
        line(f"P{result.get('numbers',{}).get('pinnacles', []).index(it)+1}: {it}")
    line("— Pyramid —", 12)
    pyr = result.get("numbers",{}).get("life_pyramid", {})
    if pyr:
        _draw_pyramid(c, 36, y-120, 60, 30, pyr)
        y -= 160
    # QR code if share_url provided via env SHARE_URL_BASE
    share_base = os.getenv('SHARE_URL_BASE')
    if share_base:
        import tempfile
        url = f"{share_base}?name={req.full_name}&dob={req.date_of_birth}&system={rules.name}"
        img = qrcode.make(url)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        img.save(tmp.name)
        c.drawImage(tmp.name, 460, y, width=100, height=100)
        y -= 110
    if narrative:
        pass
    # years/pinnacle print
    years = result.get('report',{}).get('years_detail') if isinstance(result.get('report'), dict) else None
    if years and years.get('current'):
        line("— Personal Year —", 12)
        cur = years['current']
        line(f"Year {cur.get('year')}: {cur.get('theme')}")
        [line(f"+ {s}") for s in (cur.get('strengths') or [])[:3]]
        [line(f"- {s}") for s in (cur.get('pitfalls') or [])[:2]]
    if years and years.get('next'):
        nxt = years['next']
        line("— Next Year —", 12)
        line(f"Year {nxt.get('year')}: {nxt.get('theme')}")
        if nxt.get('bridge'): line("Bridge: " + nxt['bridge'])
        if nxt.get('caution'): line("Note: " + nxt['caution'])
    pin = result.get('report',{}).get('pinnacle_detail') if isinstance(result.get('report'), dict) else None
    if pin:
        line("— Active Pinnacle —", 12)
        line(f"P{pin.get('index')} {pin.get('number')} ({pin.get('age_from')}→{pin.get('age_to')})")
        line("Theme: " + str(pin.get('theme')))
    
    # expert print
    expert = result.get('report',{}).get('expert') if isinstance(result.get('report'), dict) else None
    if expert:
        pass
        line("— Expert Max —", 12)
        line(expert.get('summary',''))
        line("Điểm mạnh:")
        [line(f"- {s}") for s in expert.get('strengths',[])[:4]]
        line("Điểm mù:")
        [line(f"- {s}") for s in expert.get('blindspots',[])[:4]]
        line("Thói quen:")
        [line(f"- {h}") for h in expert.get('habits',[])[:5]]

        line("— Narrative —", 12)
        for sec, val in narrative.get("core", {}).items():
            if val and isinstance(val, dict):
                line(f"{sec}: {val.get('summary','')}")
        for ctx in narrative.get("context", [])[:6]:
            line(f"* {ctx}")
    c.showPage(); c.save()
    buf.seek(0)
    audit_event('export_pdf', req.full_name, req.date_of_birth, rules.name, True)
    _post_webhook('export_pdf', result, trace_id=request.headers.get('X-Request-ID'))
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=report.pdf"})


@app.get("/livez")
def livez():
    return {"status":"live"}

@app.get("/readyz")
def readyz():
    ok_redis = True
    if os.getenv("REDIS_URL"):
        try:
            _REDIS.ping()
        except Exception:
            ok_redis = False
    return {"status":"ready" if ok_redis else "degraded", "redis": ok_redis}


@router.get("/admin/quota/{tenant}")
def get_quota(tenant: str, _: bool = Depends(require_scope("admin"))):
    # Try Redis first
    if _REDIS:
        val = _REDIS.get(_quota_bucket(tenant))
        left = int(val) if val is not None else None
    else:
        left = _RATE_LIMIT.get(_quota_bucket(tenant))
    return {"tenant": tenant, "left": left, "limit": _quota_limit_for

def _plan_of(tenant: str) -> str:
    # Map tenant to plan: env PLAN_JSON='{"default":"free","vip":"enterprise"}'
    try:
        m = json.loads(os.getenv("PLAN_JSON","{}"))
        return m.get(tenant, m.get("default","free"))
    except Exception:
        return "free"
(tenant)}

@router.post("/admin/quota/{tenant}/reset")
def reset_quota(tenant: str, _: bool = Depends(require_scope("admin"))):
    limit = _quota_limit_for

def _plan_of(tenant: str) -> str:
    # Map tenant to plan: env PLAN_JSON='{"default":"free","vip":"enterprise"}'
    try:
        m = json.loads(os.getenv("PLAN_JSON","{}"))
        return m.get(tenant, m.get("default","free"))
    except Exception:
        return "free"
(tenant)
    if _REDIS:
        _REDIS.set(_quota_bucket(tenant), limit)
    else:
        _RATE_LIMIT[_quota_bucket(tenant)] = limit
    return {"tenant": tenant, "left": limit}

app.include_router(router)


def _draw_pyramid(c, x, y, cell_w, cell_h, pyr):
    base = pyr.get('base', []); mid = pyr.get('mid', []); apex = pyr.get('apex')
    # Apex
    c.setStrokeColor(colors.black); c.rect(x+cell_w, y+2*cell_h, cell_w, cell_h, stroke=1, fill=0)
    c.drawCentredString(x+1.5*cell_w, y+2.5*cell_h, str(apex))
    # Mid
    c.rect(x+0.5*cell_w, y+cell_h, cell_w, cell_h, stroke=1, fill=0)
    c.drawCentredString(x+1*cell_w, y+1.5*cell_h, str(mid[0] if len(mid)>0 else ''))
    c.rect(x+1.5*cell_w, y+cell_h, cell_w, cell_h, stroke=1, fill=0)
    c.drawCentredString(x+2*cell_w, y+1.5*cell_h, str(mid[1] if len(mid)>1 else ''))
    # Base
    for i in range(3):
        c.rect(x+i*cell_w, y, cell_w, cell_h, stroke=1, fill=0)
        if i < len(base): c.drawCentredString(x+(i+0.5)*cell_w, y+0.5*cell_h, str(base[i]))


@router.post("/admin/delete")
def right_to_delete(name: str, dob: str, _: bool = Depends(require_scope("admin"))):
    # We do not store PII; record a tombstone so future HMACs can be ignored if you implement storage.
    audit_event('delete_request', name, dob, 'n/a', True)
    return {"status":"ack"}


@router.get("/roles")
def get_roles():
    return {
        "roles": [
            "product_manager","software_engineer","data_scientist",
            "researcher","ux_researcher","designer","teacher",
            "therapist","coach","consultant","founder","ceo","coo",
            "hr_leader","marketing_lead","sales_lead","artist","writer",
            "content_creator","policy_analyst"
        ,"doctor","nurse","lawyer","investor","trader","financial_analyst","accountant","financial_planner","musician","composer","filmmaker","photographer","operations_manager","supply_chain_manager","devops_engineer","security_engineer","civil_engineer","architect","project_manager","customer_support_lead"]
    }
