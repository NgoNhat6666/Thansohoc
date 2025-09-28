from __future__ import annotations
from fastapi import FastAPI, HTTPException, APIRouter, Request, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional
import os
import jwt
import json
import datetime
import time
import calendar
import requests
import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from .rules import SystemRules
from .engine import analyze, AnalysisInput

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

# FastAPI app and router
app = FastAPI(title="Numerus API", version="1.0.0")
router = APIRouter(prefix="/v1")

# CORS middleware
from fastapi.middleware.cors import CORSMiddleware
origins = [o.strip() for o in os.getenv("ALLOW_ORIGINS","*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    import os
    systems = []
    for fn in os.listdir(DATA_DIR):
        if fn.endswith(".json"):
            with open(os.path.join(DATA_DIR, fn), "r", encoding="utf-8") as f:
                data = json.load(f)
                systems.append({"id": fn.replace(".json",""), "name": data.get("name")})
    return {"systems": systems}

# Include router in app
app.include_router(router)