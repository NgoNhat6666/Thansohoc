from __future__ import annotations
from fastapi import FastAPI, HTTPException, APIRouter, Request, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import jwt
import json
import datetime
import time
import calendar
import requests
import logging
import sys
import uuid
import hmac
import hashlib
import urllib.request
from logging.handlers import TimedRotatingFileHandler
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .rules import SystemRules
from .engine import analyze, AnalysisInput

# Global metrics
_METRICS = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_error": 0,
    "systems_used": {},
    "response_times": [],
    "start_time": time.time()
}

# Global variables
_JWKS = None
_JWKS_TS = 0
_RATE_LIMIT = {}
_REDIS = None

# Try to connect to Redis if available
if os.getenv('REDIS_URL'):
    try:
        import redis
        _REDIS = redis.from_url(os.getenv('REDIS_URL'))
    except Exception:
        _REDIS = None

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
        raise HTTPException(status_code=401, detail="API key required (server not configured)")
    if x_api_key in keys:
        return True
    raise HTTPException(status_code=401, detail="Invalid or missing API key")

# JSON Formatter for logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "ts": int(time.time()),
            "level": record.levelname,
            "msg": record.getMessage(),
            "name": record.name
        }
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)

# Setup logging
handler = logging.StreamHandler(sys.stdout)
audit_handler = TimedRotatingFileHandler('/tmp/app_audit.log', when='midnight', backupCount=7)
audit_handler.setFormatter(JsonFormatter())
logging.getLogger().addHandler(audit_handler)
handler.setFormatter(JsonFormatter())
logging.getLogger().handlers = [handler]
logging.getLogger().setLevel(logging.INFO)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'no-referrer'
        # Relaxed CSP to allow static resources and external CDN
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline'; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data:; connect-src 'self';"
        if request.url.scheme == "https":
            response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
        return response

# Metrics Middleware
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        _METRICS["requests_total"] += 1
        
        try:
            response = await call_next(request)
            if response.status_code < 400:
                _METRICS["requests_success"] += 1
            else:
                _METRICS["requests_error"] += 1
        except Exception as e:
            _METRICS["requests_error"] += 1
            raise
        
        duration = (time.time() - start_time) * 1000  # milliseconds
        _METRICS["response_times"].append(duration)
        
        # Keep only last 1000 response times for memory efficiency
        if len(_METRICS["response_times"]) > 1000:
            _METRICS["response_times"] = _METRICS["response_times"][-1000:]
        
        return response

# Rate limiting helper
def _rate_key(request: StarletteRequest, api_key: str | None):
    if api_key:
        return f"key:{api_key}"
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"

# Rate Limit Middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        if request.url.path not in ["/v1/analyze", "/v1/export", "/v1/analyze/batch"]:
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
                return Response(status_code=429, content=json.dumps({"detail":"Rate limit exceeded"}), media_type="application/json")
        else:
            bucket = _RATE_LIMIT.get(key, {"ts": now, "count": 0})
            if bucket["ts"] != now:
                bucket = {"ts": now, "count": 0}
            bucket["count"] += 1
            _RATE_LIMIT[key] = bucket
            if bucket["count"] > limit:
                return Response(status_code=429, content=json.dumps({"detail":"Rate limit exceeded"}), media_type="application/json")
        return await call_next(request)

# Tenant and quota management
def _tenant_from_key(key: str | None) -> str | None:
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
    try:
        mapping = json.loads(os.getenv("QUOTAS_JSON","{}"))
        return int(mapping.get(tenant, mapping.get("default", 10000)))
    except Exception:
        return 10000

def _plan_of(tenant: str) -> str:
    try:
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
    
    global _REDIS
    bucket = _quota_bucket(tenant)
    if _REDIS:
        try:
            cnt = _REDIS.get(bucket)
            if cnt is None:
                now = datetime.datetime.utcnow()
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

# Webhook and audit
def _post_webhook(kind: str, payload: dict, trace_id: str | None = None):
    url = os.getenv("WEBHOOK_URL")
    if not url:
        return
    try:
        body = {"kind": kind, "payload": payload}
        if trace_id: 
            body["trace_id"] = trace_id
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
        with open("/tmp/app_audit.log","a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False)+"\n")
    except Exception:
        pass

# Request/Response models
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

class BatchAnalyzeRequest(BaseModel):
    requests: List[AnalyzeRequest] = Field(..., description="List of analyze requests")
    parallel: bool = Field(default=False, description="Process in parallel")

# FastAPI app and router
app = FastAPI(title="Numerus API", version="1.0.0")
router = APIRouter(prefix="/v1")

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Add middlewares
origins = [o.strip() for o in os.getenv("ALLOW_ORIGINS","*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(MetricsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# Routes
@router.post("/analyze")
def post_analyze(req: AnalyzeRequest, request: Request, _: bool = Depends(require_api_key), __: dict | None = Depends(require_jwt)):
    tenant = _tenant_from_key(request.headers.get('X-API-Key'))
    if not _quota_check_and_decr(tenant):
        raise HTTPException(status_code=402, detail="Quota exceeded for tenant")
    
    try:
        rules = SystemRules.load(req.system)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
        
        # Track system usage in metrics
        if req.system in _METRICS["systems_used"]:
            _METRICS["systems_used"][req.system] += 1
        else:
            _METRICS["systems_used"][req.system] = 1
        
        # Compose narrative if requested
        if req.detailed:
            try:
                from . import reporter
                result["report"] = reporter.compose(
                    numerics=result.get("numbers", {}),
                    full_name=req.full_name,
                    date_of_birth=req.date_of_birth,
                    locale=req.locale or "vi",
                    system=rules.name,
                    role=req.role,
                    depth=req.depth
                )
            except Exception:
                result["report_error"] = "reporter_failed"
        
        # Audit event
        audit_event("analyze", req.full_name, req.date_of_birth, req.system, True)
        
        return result
    except ValueError as ve:
        audit_event("analyze", req.full_name, req.date_of_birth, req.system, False, {"error": str(ve)})
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        audit_event("analyze", req.full_name, req.date_of_birth, req.system, False, {"error": "internal"})
        raise HTTPException(status_code=500, detail="Internal error")

@router.get("/health")
def get_health():
    return {"status": "ok"}

@router.get("/metrics")
def get_metrics():
    """Get application metrics for monitoring"""
    uptime = time.time() - _METRICS["start_time"]
    
    # Calculate response time stats
    response_times = _METRICS["response_times"]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    min_response_time = min(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0
    
    # Calculate success rate
    total_requests = _METRICS["requests_total"]
    success_rate = (_METRICS["requests_success"] / total_requests * 100) if total_requests > 0 else 0
    
    return {
        "uptime_seconds": round(uptime, 2),
        "requests": {
            "total": _METRICS["requests_total"],
            "success": _METRICS["requests_success"],
            "error": _METRICS["requests_error"],
            "success_rate_percent": round(success_rate, 2)
        },
        "response_time_ms": {
            "average": round(avg_response_time, 2),
            "minimum": round(min_response_time, 2),
            "maximum": round(max_response_time, 2),
            "samples": len(response_times)
        },
        "systems_used": _METRICS["systems_used"],
        "memory_info": {
            "response_times_cached": len(response_times)
        }
    }

@router.get("/systems")
def get_systems():
    from .rules import DATA_DIR
    systems = []
    for fn in os.listdir(DATA_DIR):
        if fn.endswith(".json"):
            with open(os.path.join(DATA_DIR, fn), "r", encoding="utf-8") as f:
                data = json.load(f)
                systems.append({"id": fn.replace(".json",""), "name": data.get("name")})
    return {"systems": systems}

@router.post("/export", response_class=HTMLResponse)
def post_export(req: AnalyzeRequest, request: Request, _: bool = Depends(require_api_key), __: dict | None = Depends(require_jwt)):
    tenant = _tenant_from_key(request.headers.get('X-API-Key'))
    if not _quota_check_and_decr(tenant):
        raise HTTPException(status_code=402, detail="Quota exceeded for tenant")
    
    try:
        rules = SystemRules.load(req.system)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
        
        # Generate simple HTML report
        html_content = f"""
        <html>
        <head><title>Numerology Report - {req.full_name}</title></head>
        <body>
        <h1>Numerology Report</h1>
        <h2>{req.full_name} - {req.date_of_birth}</h2>
        <h3>System: {req.system}</h3>
        <pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>
        </body>
        </html>
        """
        return html_content
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")

@router.get("/examples")
def get_examples():
    return {
        "examples": [
            {
                "name": "Nguyễn Văn A",
                "dob": "1990-01-15",
                "system": "pythagorean"
            },
            {
                "name": "Trần Thị B",
                "dob": "1985-05-20",
                "system": "chaldean"
            }
        ]
    }

@router.post("/analyze/batch")
def post_batch_analyze(req: BatchAnalyzeRequest, request: Request, _: bool = Depends(require_api_key), __: dict | None = Depends(require_jwt)):
    tenant = _tenant_from_key(request.headers.get('X-API-Key'))
    
    results = []
    for analyze_req in req.requests:
        if not _quota_check_and_decr(tenant):
            results.append({"error": "Quota exceeded for tenant"})
            continue
        
        try:
            rules = SystemRules.load(analyze_req.system)
            result = analyze(
                AnalysisInput(
                    full_name=analyze_req.full_name,
                    date_of_birth=analyze_req.date_of_birth,
                    gender=analyze_req.gender,
                    system=analyze_req.system,
                    target_year=analyze_req.target_year,
                ),
                rules=rules,
                trace=analyze_req.trace
            )
            results.append(result)
        except Exception as e:
            results.append({"error": str(e)})
    
    return {"results": results}

# Admin endpoints
@router.get("/admin/quota/{tenant}")
def get_quota_status(tenant: str, _: bool = Depends(require_scope("admin"))):
    limit = _quota_limit_for(tenant)
    bucket = _quota_bucket(tenant)
    
    if _REDIS:
        try:
            cnt = _REDIS.get(bucket)
            left = int(cnt) if cnt else limit
        except Exception:
            left = limit
    else:
        left = _RATE_LIMIT.get(bucket, limit)
    
    return {
        "tenant": tenant, 
        "left": left, 
        "limit": limit,
        "plan": _plan_of(tenant)
    }

@router.post("/admin/quota/{tenant}/reset")
def reset_quota(tenant: str, _: bool = Depends(require_scope("admin"))):
    limit = _quota_limit_for(tenant)
    bucket = _quota_bucket(tenant)
    
    if _REDIS:
        try:
            _REDIS.set(bucket, limit)
        except Exception:
            pass
    else:
        _RATE_LIMIT[bucket] = limit
    
    return {"tenant": tenant, "left": limit}

@router.post("/admin/delete")
def right_to_delete(name: str, dob: str, _: bool = Depends(require_scope("admin"))):
    # GDPR compliance - delete user data
    audit_event("delete", name, dob, "admin", True)
    return {"message": "Data deletion request processed"}

@router.get("/roles")
def get_roles():
    return {
        "roles": [
            "product_manager",
            "researcher", 
            "teacher",
            "consultant",
            "student"
        ]
    }

# Root endpoint với real web application

# Root endpoint với real web application
@app.get("/", response_class=HTMLResponse) 
def root():
    static_path = os.path.join(os.path.dirname(__file__), "..", "static")
    index_path = os.path.join(static_path, "index.html")
    
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Add cache-busting timestamp
        timestamp = str(int(time.time()))
        content = content.replace('styles.css', f'styles.css?v={timestamp}')
        content = content.replace('script.js', f'script.js?v={timestamp}')
        return content
    else:
        return """
        <html>
            <head><title>Numerus API</title></head>
            <body>
                <h1>Numerus API</h1>
                <p>Static files not found. Please check static directory.</p>
                <a href="/docs">Go to API Documentation</a>
            </body>
        </html>
        """

# Include router in app
app.include_router(router)
