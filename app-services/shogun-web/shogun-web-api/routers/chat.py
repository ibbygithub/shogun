import json
import os
import time
from fastapi import APIRouter, Request, Depends
import httpx
from auth import get_current_user, User
from cache import get_cache
from models import ChatMessage

router = APIRouter(prefix="/chat", tags=["chat"])

LLM_GATEWAY = os.getenv("LLM_GATEWAY_URL", "http://llm.platform.ibbytech.com")
HISTORY_TTL = 86400  # 24 hours

SYSTEM_PROMPT = """You are Shogun, an AI travel concierge for the Ibbotson family's Japan trip
(March 23 – April 9, 2026). You have deep knowledge of every city, restaurant,
temple, and transit option on the itinerary. You can answer questions about
specific POIs, give restaurant recommendations, explain cultural customs, and
help plan each day. In the web interface, you serve as both a trip advisor
and an educational guide — if someone asks about Todaiji Temple, give them
a real educational answer, not just basic tourist tips."""


def _history_key(user_id: int) -> str:
    return f"shogun:web:{user_id}:chat"


def _load_history(user_id: int) -> list[dict]:
    cache = get_cache()
    raw = cache.get(_history_key(user_id))
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _save_history(user_id: int, history: list[dict]) -> None:
    cache = get_cache()
    cache.setex(_history_key(user_id), HISTORY_TTL, json.dumps(history))


@router.post("")
def chat(body: ChatMessage, request: Request, user: User = Depends(get_current_user)):
    history = _load_history(user.id)

    history.append({
        "role": "user",
        "content": body.message,
        "timestamp": time.time(),
    })

    # Build messages for LLM gateway (strip timestamps for API call)
    messages = [
        {"role": h["role"], "content": h["content"]}
        for h in history
    ]

    payload = {
        "system": SYSTEM_PROMPT,
        "messages": messages,
        "max_tokens": 1024,
    }

    resp = httpx.post(f"{LLM_GATEWAY}/chat", json=payload, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    response_text = data.get("output_text") or data.get("response", "")

    history.append({
        "role": "assistant",
        "content": response_text,
        "timestamp": time.time(),
    })
    _save_history(user.id, history)

    return {"response": response_text, "session_id": str(user.id)}


@router.get("/history")
def get_history(request: Request, user: User = Depends(get_current_user)):
    history = _load_history(user.id)
    return [
        {"role": h["role"], "content": h["content"], "timestamp": h.get("timestamp")}
        for h in history
    ]
