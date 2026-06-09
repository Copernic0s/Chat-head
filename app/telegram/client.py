import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, Awaitable

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import User, Chat, Channel

from .auth import load_credentials

logger = logging.getLogger(__name__)

SESSION_DIR = Path.home() / ".telegram-chat-head"
SESSION_PATH = str(SESSION_DIR / "session")


class TGClient:
    def __init__(self):
        self._client: Optional[TelegramClient] = None
        self._phone: Optional[str] = None
        self._connected = False
        self._message_handler: Optional[Callable] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def start(self, phone: str, code_callback: Callable[[], Awaitable[str]]):
        creds = load_credentials()
        if not creds:
            raise RuntimeError("No credentials configured")

        self._phone = phone
        self._client = TelegramClient(
            SESSION_PATH,
            creds["api_id"],
            creds["api_hash"],
            system_version="4.16.30-vxCUSTOM",
            device_model="Chat Head Desktop",
            app_version="1.0.0",
        )

        await self._client.connect()

        if not await self._client.is_user_authorized():
            sent = await self._client.send_code_request(phone)
            code = await code_callback()
            try:
                await self._client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = await code_callback()
                await self._client.sign_in(password=password)

        self._connected = True
        logger.info("Connected to Telegram")

        if self._message_handler:
            self._client.add_event_handler(
                self._message_handler,
                events.NewMessage,
            )

        await self._client.run_until_disconnected()

    def set_message_handler(self, handler: Callable):
        self._message_handler = handler
        if self._client and self._connected:
            self._client.add_event_handler(
                handler,
                events.NewMessage,
            )

    async def get_dialogs(self):
        if not self._client or not self._connected:
            return []
        dialogs = await self._client.get_dialogs()
        result = []
        for d in dialogs:
            entity = d.entity
            if isinstance(entity, User):
                title = getattr(entity, "first_name", "") or ""
                last = getattr(entity, "last_name", "") or ""
                if last:
                    title = f"{title} {last}".strip()
                if not title:
                    title = getattr(entity, "phone", "Unknown")
            elif hasattr(entity, "title"):
                title = entity.title or "Unknown"
            else:
                title = "Unknown"

            result.append({
                "id": d.id,
                "title": title,
                "unread": d.unread_count,
                "last_message": d.message.text if d.message else "",
                "last_message_date": d.message.date if d.message else None,
            })
        return result

    async def get_messages(self, chat_id: int, limit: int = 50):
        if not self._client or not self._connected:
            return []
        messages = await self._client.get_messages(chat_id, limit=limit)
        result = []
        for m in messages:
            result.append({
                "id": m.id,
                "chat_id": chat_id,
                "sender_id": m.sender_id or 0,
                "text": m.text or "",
                "date": m.date,
                "out": m.out,
            })
        return result

    async def send_message(self, chat_id: int, text: str):
        if not self._client or not self._connected:
            return
        await self._client.send_message(chat_id, text)

    async def disconnect(self):
        if self._client:
            self._connected = False
            await self._client.disconnect()
            logger.info("Disconnected from Telegram")
