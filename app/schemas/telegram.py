from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TelegramLinkStatusOut(BaseModel):
    is_linked: bool
    is_active: bool
    linked_at: Optional[datetime] = None
    telegram_username: Optional[str] = None
    has_pending_token: bool = False
    token_expires_at: Optional[datetime] = None


class TelegramLinkGenerateOut(BaseModel):
    deep_link: str
    expires_at: datetime
    bot_username: str


class TelegramLinkActionOut(BaseModel):
    status: str
    message: str
