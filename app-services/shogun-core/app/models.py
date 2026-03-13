"""
Pydantic models matching the Telegram gateway envelope schema (openapi.yaml v2.0.0).
"""
from typing import Any, Optional
from pydantic import BaseModel


class TelegramUpdate(BaseModel):
    update_id: Optional[int] = None


class TelegramFrom(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    id: Optional[int] = None
    type: Optional[str] = None
    title: Optional[str] = None


class TelegramMessageMeta(BaseModel):
    message_id: Optional[int] = None
    date: Optional[int] = None
    reply_to_message_id: Optional[int] = None
    edit_date: Optional[int] = None


class GatewayCapabilities(BaseModel):
    can_search: bool = False
    can_scrape: bool = False
    can_fetch_files: bool = False


class TelegramEnvelope(BaseModel):
    receipt_id: str
    received_at: str
    kind: str  # text | location | photo | document | voice
    update: TelegramUpdate
    from_: TelegramFrom = TelegramFrom()
    chat: TelegramChat = TelegramChat()
    message: TelegramMessageMeta = TelegramMessageMeta()
    capabilities: GatewayCapabilities = GatewayCapabilities()
    payload: dict[str, Any] = {}

    class Config:
        # Gateway sends "from" — Python reserved word, alias it
        populate_by_name = True

    @classmethod
    def model_validate_json_alias(cls, data: dict) -> "TelegramEnvelope":
        # Rename "from" → "from_" before validation
        if "from" in data:
            data["from_"] = data.pop("from")
        return cls.model_validate(data)
