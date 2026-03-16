"""
Telegram file downloader.
Downloads voice and photo files from the Telegram Bot API using the bot token.

Flow:
  1. GET /bot{TOKEN}/getFile?file_id=...  → resolves file_id to a file_path
  2. GET /file/bot{TOKEN}/{file_path}      → downloads raw bytes
"""
import base64
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"
TIMEOUT = 30.0

_MIME_MAP = {
    "ogg": "audio/ogg",
    "oga": "audio/ogg",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "pdf": "application/pdf",
}


async def download_file_b64(file_id: str) -> tuple[str, str]:
    """
    Download a Telegram file by file_id.
    Returns (base64_string, mime_type).
    Raises on failure — callers must catch.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Step 1: resolve file_id → file_path
        resp = await client.get(
            f"{TELEGRAM_API}/bot{settings.telegram_bot_token}/getFile",
            params={"file_id": file_id},
        )
        resp.raise_for_status()
        result = resp.json()
        if not result.get("ok"):
            raise ValueError(f"Telegram getFile failed: {result.get('description', 'unknown error')}")

        file_path = result["result"]["file_path"]

        # Step 2: download the actual bytes
        dl_resp = await client.get(
            f"{TELEGRAM_API}/file/bot{settings.telegram_bot_token}/{file_path}",
        )
        dl_resp.raise_for_status()

    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    mime_type = _MIME_MAP.get(ext, "application/octet-stream")
    b64 = base64.b64encode(dl_resp.content).decode("utf-8")
    logger.debug("Downloaded file_id=%s path=%s mime=%s size=%d bytes", file_id, file_path, mime_type, len(dl_resp.content))
    return b64, mime_type
