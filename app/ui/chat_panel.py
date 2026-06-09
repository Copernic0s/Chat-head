from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QScrollArea, QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint, QEvent
from PyQt6.QtGui import QKeyEvent
from datetime import datetime
from ..storage.models import Chat, Message


PANEL_WIDTH = 380
PANEL_HEIGHT = 550


class MessageBubble(QFrame):
    def __init__(self, text: str, is_out: bool, time: datetime, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(0)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(280)

        if is_out:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #094771;
                    color: white;
                    padding: 8px 14px;
                    border-radius: 14px;
                    font-size: 13px;
                }
            """)
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    padding: 8px 14px;
                    border-radius: 14px;
                    font-size: 13px;
                }
            """)
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(bubble)

        time_label = QLabel(time.strftime("%H:%M"))
        time_label.setStyleSheet("color: #888; font-size: 10px; padding: 2px 8px 0 8px;")
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

        self.setFixedSize(PANEL_WIDTH, PANEL_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            ChatPanel {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 12px;
            }
        """)

        self._build_ui()

        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = self._build_header()
        layout.addWidget(header)

        self._stack = QWidget()
        self._stack.setStyleSheet("background-color: transparent;")
        self._stack_layout = QVBoxLayout(self._stack)
        self._stack_layout.setContentsMargins(0, 0, 0, 0)
        self._stack_layout.setSpacing(0)

        self._chat_list = QListWidget()
        self._chat_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #252526;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)
        self._chat_list.itemClicked.connect(self._on_chat_clicked)
        self._stack_layout.addWidget(self._chat_list)

        self._chat_view = QWidget()
        self._chat_view.setStyleSheet("background-color: transparent;")
        chat_view_layout = QVBoxLayout(self._chat_view)
        chat_view_layout.setContentsMargins(0, 0, 0, 0)
        chat_view_layout.setSpacing(0)

        self._messages_container = QWidget()
        self._messages_container.setStyleSheet("background-color: transparent;")
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
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        chat_view_layout.addWidget(self._scroll_area)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(8, 8, 8, 8)

        self._input_field = QTextEdit()
        self._input_field.setPlaceholderText("Escribe un mensaje...")
        self._input_field.setFixedHeight(40)
        self._input_field.setStyleSheet("""
            QTextEdit {
                border: 1px solid #444;
                border-radius: 20px;
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 8px 16px;
                font-size: 13px;
            }
        """)
        self._input_field.installEventFilter(self)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(36, 36)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #094771;
                border: none;
                border-radius: 18px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0a5a8a;
            }
        """)
        send_btn.clicked.connect(self._send_message)

        input_layout.addWidget(self._input_field)
        input_layout.addWidget(send_btn)
        chat_view_layout.addLayout(input_layout)

        self._chat_view.hide()
        self._stack_layout.addWidget(self._chat_view)

        layout.addWidget(self._stack, 1)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet("background-color: #252526; border-radius: 12px 12px 0 0;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 0, 12, 0)

        title = QLabel("Chat Head")
        title.setStyleSheet("color: #e0e0e0; font-size: 14px; font-weight: bold;")
        hl.addWidget(title)
        hl.addStretch()

        self._back_btn = QPushButton("←")
        self._back_btn.setFixedSize(28, 28)
        self._back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #e0e0e0;
                font-size: 16px;
            }
            QPushButton:hover { color: white; }
        """)
        self._back_btn.clicked.connect(self._show_chat_list)
        self._back_btn.hide()
        hl.addWidget(self._back_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
            }
            QPushButton:hover { color: #ef4444; }
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
        w.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)

        avatar = QLabel(chat.title[0].upper() if chat.title else "?")
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet("""
            background-color: #094771;
            color: white;
            font-size: 18px;
            font-weight: bold;
            border-radius: 20px;
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(avatar)

        text_layout = QVBoxLayout()
        name_label = QLabel(chat.title)
        name_label.setStyleSheet("color: #e0e0e0; font-size: 13px; font-weight: bold; background: transparent;")
        text_layout.addWidget(name_label)

        if chat.last_message:
            preview = chat.last_message[:60] + ("..." if len(chat.last_message) > 60 else "")
            preview_label = QLabel(preview)
            preview_label.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
            text_layout.addWidget(preview_label)

        layout.addLayout(text_layout, 1)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if chat.last_message_time:
            time_str = chat.last_message_time.strftime("%H:%M")
            time_label = QLabel(time_str)
            time_label.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
            right_layout.addWidget(time_label)

        if chat.unread_count > 0:
            badge = QLabel(str(chat.unread_count))
            badge.setStyleSheet("""
                background-color: #ef4444;
                color: white;
                font-size: 10px;
                font-weight: bold;
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
            bubble = MessageBubble(msg.text, msg.out, msg.date, self._messages_container)
            self._messages_layout.addWidget(bubble)

        QTimer.singleShot(100, self._scroll_to_bottom)

    def add_message(self, msg: Message):
        bubble = MessageBubble(msg.text, msg.out, msg.date, self._messages_container)
        self._messages_layout.addWidget(bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        scrollbar = self._scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

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
        start_pos = QPoint(target_pos.x() + 400, target_pos.y())
        self.move(start_pos)
        self.show()
        self.raise_()
        self._anim.setStartValue(start_pos)
        self._anim.setEndValue(target_pos)
        self._anim.start()

    def hide_panel(self):
        end_pos = QPoint(self.x() + 400, self.y())
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(end_pos)
        self._anim.finished.connect(self._on_hide_finished)
        self._anim.start()

    def _on_hide_finished(self):
        self.hide()
        self._anim.finished.disconnect(self._on_hide_finished)
