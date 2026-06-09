import logging
from typing import Callable, Any

from telethon import events

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, on_message: Callable[[dict], None]):
        self._on_message = on_message

    async def handle(self, event: events.NewMessage.Event):
        try:
            msg = event.message
            chat = await event.get_chat()
            chat_id = chat.id if hasattr(chat, "id") else event.chat_id

            data = {
                "id": msg.id,
                "chat_id": chat_id,
                "sender_id": msg.sender_id or 0,
                "text": msg.text or "",
                "date": msg.date,
                "out": msg.out,
            }
            self._on_message(data)
        except Exception as e:
            logger.error(f"Error handling message event: {e}")
