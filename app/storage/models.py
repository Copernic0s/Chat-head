from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ChatHeadState:
    x: int = 100
    y: int = 100
    active_chat_id: Optional[int] = None
    panel_open: bool = False


@dataclass
class Chat:
    id: int
    title: str
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0


@dataclass
class Message:
    id: int
    chat_id: int
    sender_id: int
    text: str
    date: datetime
    out: bool = False
