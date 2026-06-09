import sys
import asyncio
import logging
import threading
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import QApplication, QInputDialog
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QPoint

from app.ui.bubble import BubbleWidget
from app.ui.chat_panel import ChatPanel
from app.storage.database import save_state, load_state
from app.storage.models import Chat, Message
from app.telegram.client import TGClient
from app.telegram.events import EventHandler
from app.telegram.auth import load_credentials, save_credentials

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


class SignalBridge(QObject):
    message_received = pyqtSignal(dict)
    dialogs_loaded = pyqtSignal(list)
    messages_loaded = pyqtSignal(list)
    login_required = pyqtSignal()
    connected = pyqtSignal()


class ChatHeadApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.state = load_state()
        self.bridge = SignalBridge()
        self.tg_client = TGClient()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._chats: dict[int, Chat] = {}
        self._messages: dict[int, list[Message]] = {}
        self._logged_in = False

        self.bubble = BubbleWidget()
        self.panel = ChatPanel()
        self._setup_signals()

        self.bubble.move(self.state.x, self.state.y)
        self.bubble.fade_in()

    def _setup_signals(self):
        self.bubble.left_clicked.connect(self._toggle_panel)
        self.bubble.drag_finished.connect(self._persist_state)

        self.bridge.message_received.connect(self._on_telegram_message)
        self.bridge.dialogs_loaded.connect(self._on_dialogs_loaded)
        self.bridge.messages_loaded.connect(self._on_messages_loaded)
        self.bridge.login_required.connect(self._show_login_dialog)
        self.bridge.connected.connect(self._on_connected)

        self.panel.closed.connect(self._close_panel)
        self.panel.chat_selected.connect(self._on_chat_selected)
        self.panel.send_message_signal.connect(self._on_send_message)

    def _toggle_panel(self):
        if self.panel.isVisible():
            self._close_panel()
        else:
            self._open_panel()

    def _open_panel(self):
        target = self.bubble.pos()
        panel_x = target.x() - 390
        panel_y = max(50, target.y() - 240)
        self.panel.show_panel(QPoint(panel_x, panel_y))

        chat = self._get_active_chat()
        if chat:
            self._update_badge_decrement()
        self.state.panel_open = True
        self._persist_state()

    def _close_panel(self):
        self.panel.hide_panel()
        self.state.panel_open = False
        self._persist_state()

    def _get_active_chat(self) -> Optional[Chat]:
        return self._chats.get(self.state.active_chat_id)

    def _update_badge_decrement(self):
        chat = self._get_active_chat()
        if chat:
            chat.unread_count = 0
            self.bubble.set_unread(sum(c.unread_count for c in self._chats.values()))
            self.panel.set_chats(list(self._chats.values()))

    def _on_chat_selected(self, chat_id: int):
        self.state.active_chat_id = chat_id
        self._persist_state()
        self._update_badge_decrement()
        self._load_chat_messages(chat_id)

    def _load_chat_messages(self, chat_id: int):
        if chat_id in self._messages:
            self.panel.display_messages(self._messages[chat_id])
        else:
            asyncio.run_coroutine_threadsafe(
                self._do_fetch_messages(chat_id), self._loop
            )

    async def _do_fetch_messages(self, chat_id: int):
        try:
            raw_msgs = await self.tg_client.get_messages(chat_id)
            msgs = [
                Message(
                    id=m["id"],
                    chat_id=m["chat_id"],
                    sender_id=m["sender_id"],
                    text=m["text"],
                    date=m["date"],
                    out=m["out"],
                )
                for m in raw_msgs
            ]
            self._messages[chat_id] = msgs
            self.bridge.messages_loaded.emit(msgs)
        except Exception as e:
            logger.error(f"Failed to fetch messages: {e}")

    async def _do_fetch_dialogs(self):
        try:
            raw_dialogs = await self.tg_client.get_dialogs()
            self.bridge.dialogs_loaded.emit(raw_dialogs)
        except Exception as e:
            logger.error(f"Failed to fetch dialogs: {e}")

    def _on_dialogs_loaded(self, raw_dialogs: list):
        self._chats.clear()
        for d in raw_dialogs:
            chat = Chat(
                id=d["id"],
                title=d["title"],
                last_message=d["last_message"],
                last_message_time=d["last_message_date"],
                unread_count=d["unread"],
            )
            self._chats[chat.id] = chat

        total_unread = sum(c.unread_count for c in self._chats.values())
        self.bubble.set_unread(total_unread)
        self.panel.set_chats(list(self._chats.values()))

    def _on_messages_loaded(self, msgs: list):
        if msgs:
            self.panel.display_messages(msgs)

    def _on_telegram_message(self, data: dict):
        msg = Message(
            id=data["id"],
            chat_id=data["chat_id"],
            sender_id=data["sender_id"],
            text=data["text"],
            date=data["date"],
            out=data["out"],
        )

        if msg.chat_id not in self._messages:
            self._messages[msg.chat_id] = []
        self._messages[msg.chat_id].append(msg)

        if msg.chat_id in self._chats:
            chat = self._chats[msg.chat_id]
            chat.last_message = msg.text
            chat.last_message_time = msg.date
            if self.state.active_chat_id != msg.chat_id or not self.panel.isVisible():
                chat.unread_count += 1
            total = sum(c.unread_count for c in self._chats.values())
            self.bubble.set_unread(total)
            self.panel.set_chats(list(self._chats.values()))

        if self.state.active_chat_id == msg.chat_id and self.panel.isVisible():
            self.panel.add_message(msg)

    async def _run_telegram(self):
        try:
            self._loop = asyncio.get_running_loop()

            creds = load_credentials()
            if not creds:
                self.bridge.login_required.emit()
                return

            phone = creds.get("phone", "")
            handler = EventHandler(lambda d: self.bridge.message_received.emit(d))
            self.tg_client.set_message_handler(handler.handle)

            await self.tg_client.start(
                phone, self._handle_telegram_code,
                on_connected=lambda: self.bridge.connected.emit()
            )

        except Exception as e:
            logger.error(f"Telegram error: {e}")

    async def _handle_telegram_code(self) -> str:
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def show_dialog():
            code, ok = QInputDialog.getText(
                None, "Código de verificación",
                "Ingresa el código enviado a Telegram:"
            )
            if ok and code:
                loop.call_soon_threadsafe(lambda: future.set_result(code))
            else:
                loop.call_soon_threadsafe(lambda: future.set_exception(RuntimeError("Cancelled")))

        QTimer.singleShot(0, show_dialog)
        return await future

    def _show_login_dialog(self):
        api_id, ok = QInputDialog.getText(None, "API ID", "Ingresa tu API ID:")
        if not ok or not api_id:
            return
        api_hash, ok = QInputDialog.getText(None, "API Hash", "Ingresa tu API Hash:")
        if not ok or not api_hash:
            return
        phone, ok = QInputDialog.getText(None, "Teléfono", "Ingresa tu número (ej: +521234567890):")
        if not ok or not phone:
            return

        save_credentials(int(api_id), api_hash, phone)
        self._start_telegram_async()

    def _on_connected(self):
        self._logged_in = True
        logger.info("Telegram connected, loading dialogs...")
        asyncio.run_coroutine_threadsafe(self._do_fetch_dialogs(), self._loop)

    def _on_send_message(self, chat_id: int, text: str):
        asyncio.run_coroutine_threadsafe(
            self._do_send_message(chat_id, text), self._loop
        )

        msg = Message(
            id=0, chat_id=chat_id, sender_id=0,
            text=text, date=datetime.now(), out=True,
        )
        self.panel.add_message(msg)
        if chat_id in self._chats:
            self._chats[chat_id].last_message = text
            self._chats[chat_id].last_message_time = datetime.now()
            self.panel.set_chats(list(self._chats.values()))

    async def _do_send_message(self, chat_id: int, text: str):
        try:
            await self.tg_client.send_message(chat_id, text)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def _start_telegram_async(self):
        asyncio.run_coroutine_threadsafe(self._run_telegram(), self._loop)

    def _persist_state(self):
        self.state.x = self.bubble.x()
        self.state.y = self.bubble.y()
        save_state(self.state)

    def _run_async_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.create_task(self._run_telegram())
        self._loop.run_forever()

    def run(self):
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()

        while self._loop is None:
            pass

        exit_code = self.app.exec()
        self._cleanup()
        sys.exit(exit_code)

    def _cleanup(self):
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.tg_client.disconnect(), self._loop
            )
            self._loop.call_soon_threadsafe(self._loop.stop)


if __name__ == "__main__":
    app = ChatHeadApp()
    app.run()
