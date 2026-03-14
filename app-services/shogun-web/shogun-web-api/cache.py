import os
import redis

_client: redis.Redis | None = None


def get_cache() -> redis.Redis:
    global _client
    if _client is None:
        valkey_url = os.getenv("VALKEY_URL", "redis://localhost:6379")
        _client = redis.from_url(valkey_url, decode_responses=True)
    return _client
