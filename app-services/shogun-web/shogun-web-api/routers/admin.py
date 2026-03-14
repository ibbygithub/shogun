import os
import time
from fastapi import APIRouter, Request, Depends
import httpx
from auth import get_current_user, require_admin, User
from db import get_conn
from cache import get_cache
from models import AdminHealthResponse, ServiceHealth
from datetime import datetime, timezone

router = APIRouter(prefix="/admin", tags=["admin"])


def _check_http(name: str, url: str) -> ServiceHealth:
    ts = datetime.now(timezone.utc).isoformat()
    try:
        t0 = time.monotonic()
        resp = httpx.get(url, timeout=5.0)
        latency = round((time.monotonic() - t0) * 1000, 1)
        status = "ok" if resp.status_code < 400 else "degraded"
    except Exception:
        latency = None
        status = "unreachable"
    return ServiceHealth(name=name, status=status, latency_ms=latency, last_check=ts)


def _check_valkey() -> ServiceHealth:
    ts = datetime.now(timezone.utc).isoformat()
    try:
        t0 = time.monotonic()
        get_cache().ping()
        latency = round((time.monotonic() - t0) * 1000, 1)
        return ServiceHealth(name="valkey", status="ok", latency_ms=latency, last_check=ts)
    except Exception:
        return ServiceHealth(name="valkey", status="unreachable", latency_ms=None, last_check=ts)


def _check_db() -> ServiceHealth:
    ts = datetime.now(timezone.utc).isoformat()
    try:
        t0 = time.monotonic()
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        latency = round((time.monotonic() - t0) * 1000, 1)
        return ServiceHealth(name="database", status="ok", latency_ms=latency, last_check=ts)
    except Exception:
        return ServiceHealth(name="database", status="unreachable", latency_ms=None, last_check=ts)


@router.get("/health", response_model=AdminHealthResponse)
def admin_health(request: Request, user: User = Depends(get_current_user)):
    require_admin(user)
    llm_url = os.getenv("LLM_GATEWAY_URL", "http://llm.platform.ibbytech.com")
    services = [
        _check_http("shogun-core",       "http://brainnode-01.ibbytech.com:8082/health"),
        _check_http("llm-gateway",       f"{llm_url}/health"),
        _check_http("telegram-gateway",  "http://telegram.platform.ibbytech.com/health"),
        _check_valkey(),
        _check_db(),
    ]
    return AdminHealthResponse(services=services)
