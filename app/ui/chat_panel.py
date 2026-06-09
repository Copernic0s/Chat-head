from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QScrollArea, QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint, QEvent, QRectF
from PyQt6.QtGui import (
    QKeyEvent, QPainter, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QFont, QPainterPath,
)
from datetime import datetime
from ..storage.models import Chat, Message
from .styles import (
    PANEL_STYLE, HEADER_STYLE, CHAT_ITEM_NAME, CHAT_ITEM_PREVIEW,
    CHAT_ITEM_TIME, CHAT_ITEM_BADGE, AVATAR_STYLE, MESSAGE_SENT,
    MESSAGE_RECEIVED, SEND_BTN_STYLE, CLOSE_BTN, BACK_BTN, FONT,
    GLASS_BORDER, TEXT_SECONDARY, DANGER, TEXT_PRIMARY, ACCENT,
    ACCENT_GLOW,
)


PANEL_WIDTH = 380
PANEL_HEIGHT = 550


class GlassPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 16, 16)

        bg = QLinearGradient(0, 0, 0, rect.height())
        bg.setColorAt(0.0, QColor(22, 24, 30, 200))
        bg.setColorAt(0.5, QColor(18, 20, 26, 215))
        bg.setColorAt(1.0, QColor(14, 16, 22, 230))
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(QColor(255, 255, 255, 18), 1))
        painter.drawPath(path)

        hl = QLinearGradient(0, 0, rect.width(), 0)
        hl.setColorAt(0.0, QColor(255, 255, 255, 0))
        hl.setColorAt(0.5, QColor(255, 255, 255, 6))
        hl.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(hl))
        painter.setPen(Qt.PenStyle.NoPen)
        inner = QRectF(rect).adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(inner, 15, 15)


class MessageBubble(QFrame):
    def __init__(self, text: str, is_out: bool, time: datetime, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(2)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(280)
        bubble.setStyleSheet(MESSAGE_SENT if is_out else MESSAGE_RECEIVED)
        layout.setAlignment(
            Qt.AlignmentFlag.AlignRight if is_out else Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(bubble)

        time_label = QLabel(time.strftime("%H:%M"))
        time_label.setStyleSheet(
            f"color: rgba(255,255,255,0.3); font-size: 10px; padding: 0 8px; background: transparent;"
        )
        time_label.setAlignment(
            Qt.AlignmentFlag.AlignRight if is_out else Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(time_label)

        self.setLayout(layout)


class ChatPanel(QWidget):
    closed = pyqtSignal()
    chat_selected = pyqtSignal(int)
    send_message_signal = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chats: dict[int, Chat] = {}
        self._messages: dict[int, list[Message]] = {}
        self._active_chat_id: int | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(PANEL_WIDTH, PANEL_HEIGHT)

        self._container = GlassPanel(self)
        self._container.setGeometry(0, 0, PANEL_WIDTH, PANEL_HEIGHT)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = self._build_header()
        layout.addWidget(header)

        self._stack = QWidget()
        self._stack.setStyleSheet("background: transparent;")
        self._stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        stack_layout = QVBoxLayout(self._stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.setSpacing(0)

        self._chat_list = QListWidget()
        self._chat_list.setStyleSheet(PANEL_STYLE)
        self._chat_list.itemClicked.connect(self._on_chat_clicked)
        stack_layout.addWidget(self._chat_list)

        self._chat_view = QWidget()
        self._chat_view.setStyleSheet("background: transparent;")
        cv_layout = QVBoxLayout(self._chat_view)
        cv_layout.setContentsMargins(0, 0, 0, 0)
        cv_layout.setSpacing(0)

        self._messages_container = QWidget()
        self._messages_container.setStyleSheet("background: transparent;")
        self._messages_layout = QVBoxLayout(self._messages_container)
        self._messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._messages_layout.setSpacing(4)
        self._messages_layout.setContentsMargins(0, 4, 0, 4)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._messages_container)
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 4px;
                background: transparent;
                margin: 4px 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.15);
                border-radius: 2px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255,255,255,0.25);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        cv_layout.addWidget(self._scroll_area)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(10, 8, 10, 10)

        self._input_field = QTextEdit()
        self._input_field.setPlaceholderText("Mensaje...")
        self._input_field.setFixedHeight(40)
        self._input_field.setStyleSheet("""
            QTextEdit {
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 20px;
                background: rgba(255,255,255,0.06);
                color: rgba(255,255,255,0.92);
                padding: 8px 16px;
                font-size: 13px;
                font-family: "Segoe UI Variable", "Segoe UI", system-ui, sans-serif;
                selection-background-color: #0a84ff;
            }
            QTextEdit:focus {
                border-color: #0a84ff;
            }
        """)
        self._input_field.installEventFilter(self)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(36, 36)
        send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a84ff, stop:1 #0055cc);
                border: none;
                border-radius: 18px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a94ff, stop:1 #0066dd);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0066cc, stop:1 #004488);
            }
        """)
        send_btn.clicked.connect(self._send_message)

        input_layout.addWidget(self._input_field)
        input_layout.addWidget(send_btn)
        cv_layout.addLayout(input_layout)

        self._chat_view.hide()
        stack_layout.addWidget(self._chat_view)

        layout.addWidget(self._stack, 1)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("background: rgba(255,255,255,0.04); border-bottom: 1px solid rgba(255,255,255,0.07);")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 10, 0)

        title = QLabel("Chat Head")
        title.setStyleSheet(f"color: rgba(255,255,255,0.92); font-size: 15px; font-weight: 700; background: transparent; font-family: {FONT};")
        hl.addWidget(title)
        hl.addStretch()

        self._back_btn = QPushButton("←")
        self._back_btn.setFixedSize(30, 30)
        self._back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255,255,255,0.5);
                font-size: 16px;
                border-radius: 15px;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
                color: white;
            }
        """)
        self._back_btn.clicked.connect(self._show_chat_list)
        self._back_btn.hide()
        hl.addWidget(self._back_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255,255,255,0.4);
                font-size: 14px;
                border-radius: 15px;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
                color: #ff453a;
            }
        """)
        close_btn.clicked.connect(self._close_panel)
        hl.addWidget(close_btn)

        return header

    def set_chats(self, chats: list[Chat]):
        self._chats = {c.id: c for c in chats}
        self._chat_list.clear()
        for chat in chats:
            item = QListWidgetItem()
            widget = self._build_chat_item(chat)
            item.setData(Qt.ItemDataRole.UserRole, chat.id)
            item.setSizeHint(widget.sizeHint())
            self._chat_list.addItem(item)
            self._chat_list.setItemWidget(item, widget)

    def _build_chat_item(self, chat: Chat) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)

        avatar = QLabel(chat.title[0].upper() if chat.title else "?")
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0a84ff, stop:1 #0055aa);
            color: white;
            font-size: 18px;
            font-weight: 700;
            border-radius: 22px;
        """)
        layout.addWidget(avatar)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        name_label = QLabel(chat.title)
        name_label.setStyleSheet(f"color: rgba(255,255,255,0.92); font-size: 13px; font-weight: 600; background: transparent;")
        text_layout.addWidget(name_label)

        if chat.last_message:
            preview = chat.last_message[:60] + ("..." if len(chat.last_message) > 60 else "")
            preview_label = QLabel(preview)
            preview_label.setStyleSheet(f"color: rgba(255,255,255,0.45); font-size: 11px; background: transparent;")
            text_layout.addWidget(preview_label)

        layout.addLayout(text_layout, 1)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_layout.setSpacing(4)

        if chat.last_message_time:
            time_label = QLabel(chat.last_message_time.strftime("%H:%M"))
            time_label.setStyleSheet(f"color: rgba(255,255,255,0.25); font-size: 10px; background: transparent;")
            right_layout.addWidget(time_label)

        if chat.unread_count > 0:
            badge = QLabel(str(chat.unread_count))
            badge.setStyleSheet(f"""
                background-color: {DANGER};
                color: white;
                font-size: 10px;
                font-weight: 700;
                border-radius: 8px;
                padding: 1px 5px;
                min-width: 14px;
            """)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            right_layout.addWidget(badge)

        layout.addLayout(right_layout)

        return w

    def _on_chat_clicked(self, item: QListWidgetItem):
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        self._active_chat_id = chat_id
        self.chat_selected.emit(chat_id)
        self._show_chat_view()

    def _show_chat_view(self):
        self._chat_list.hide()
        self._chat_view.show()
        self._back_btn.show()

    def _show_chat_list(self):
        self._chat_view.hide()
        self._chat_list.show()
        self._back_btn.hide()
        self._active_chat_id = None

    def display_messages(self, messages: list[Message]):
        for i in reversed(range(self._messages_layout.count())):
            item = self._messages_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        for msg in messages:
            self._messages_layout.addWidget(
                MessageBubble(msg.text, msg.out, msg.date, self._messages_container)
            )
        QTimer.singleShot(100, self._scroll_to_bottom)

    def add_message(self, msg: Message):
        self._messages_layout.addWidget(
            MessageBubble(msg.text, msg.out, msg.date, self._messages_container)
        )
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self._scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _send_message(self):
        text = self._input_field.toPlainText().strip()
        if not text or self._active_chat_id is None:
            return
        self._input_field.clear()
        self.send_message_signal.emit(self._active_chat_id, text)

    def eventFilter(self, obj, event):
        if obj == self._input_field and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._send_message()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self._close_panel()
        super().keyPressEvent(event)

    def _close_panel(self):
        self.closed.emit()

    def show_panel(self, target_pos: QPoint):
        self.setWindowOpacity(1.0)
        self.move(target_pos)
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_panel(self):
        self.hide()
