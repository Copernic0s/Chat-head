from PyQt6.QtWidgets import QWidget, QLabel, QMenu, QGraphicsDropShadowEffect, QGraphicsBlurEffect
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QPropertyAnimation, QTimer, QEasingCurve
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QRadialGradient, QFont, QMouseEvent,
    QPaintEvent, QLinearGradient, QPen, QBrush,
)
from .styles import DANGER, FONT


class BubbleWidget(QWidget):
    left_clicked = pyqtSignal()
    drag_finished = pyqtSignal()
    badge_updated = pyqtSignal(int)

    SIZE = 64

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = QPoint()
        self._dragging = False
        self._unread = 0
        self._pulse = 0.0
        self._pulse_dir = 1

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.SIZE + 8, self.SIZE + 8)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(10, 132, 255, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.badge = QLabel("", self)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet(f"""
            QLabel {{
                background-color: {DANGER};
                color: white;
                font-size: 11px;
                font-weight: 700;
                border-radius: 10px;
                padding: 2px 6px;
                min-width: 16px;
                min-height: 16px;
                font-family: {FONT};
            }}
        """)
        self.badge.adjustSize()
        self.badge.hide()

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.start(50)

        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _update_pulse(self):
        if self._unread > 0:
            self._pulse += 0.04 * self._pulse_dir
            if self._pulse > 1.0:
                self._pulse = 1.0
                self._pulse_dir = -1
            elif self._pulse < 0.0:
                self._pulse = 0.0
                self._pulse_dir = 1
            self.update()

    def set_unread(self, count: int):
        self._unread = count
        if count > 0:
            self.badge.setText(str(count))
            self.badge.adjustSize()
            self.badge.move(
                self.width() - self.badge.width() - 2,
                0,
            )
            self.badge.show()
            self._pulse = 0.0
            self._pulse_dir = 1
        else:
            self.badge.hide()
        self.badge_updated.emit(count)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        r = self.SIZE / 2

        bg = QRadialGradient(cx, cy, r + 4)
        bg.setColorAt(0.0, QColor("#1a8cff"))
        bg.setColorAt(0.6, QColor("#0a6ed1"))
        bg.setColorAt(1.0, QColor("#0055aa"))
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1.5))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        glow = QRadialGradient(cx, cy, r * 1.8)
        alpha = int(40 + 30 * self._pulse)
        glow.setColorAt(0.0, QColor(10, 132, 255, alpha))
        glow.setColorAt(1.0, QColor(10, 132, 255, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r * 1.4, r * 1.4)

        highlight = QRadialGradient(cx - r * 0.3, cy - r * 0.3, r * 0.8)
        highlight.setColorAt(0.0, QColor(255, 255, 255, 50))
        highlight.setColorAt(0.5, QColor(255, 255, 255, 15))
        highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        painter.setFont(QFont("Segoe UI", 22))
        painter.setPen(QColor(255, 255, 255, 230))
        painter.drawText(self.rect().adjusted(0, 0, 0, -2),
                          Qt.AlignmentFlag.AlignCenter, "💬")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (event.globalPosition().toPoint()
                              - self.frameGeometry().topLeft())
            self._dragging = True
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            delta = (event.globalPosition().toPoint()
                     - self._drag_pos - self.pos()).manhattanLength()
            self._dragging = False
            self.drag_finished.emit()
            if delta < 5:
                self.left_clicked.emit()

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: rgba(22, 24, 30, 0.92);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
                padding: 6px;
                font-family: {FONT};
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 6px;
                color: rgba(255,255,255,0.85);
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background: rgba(10, 132, 255, 0.25);
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background: rgba(255,255,255,0.06);
                margin: 4px 8px;
            }}
        """)
        open_action = menu.addAction("Abrir")
        config_action = menu.addAction("Configuración")
        menu.addSeparator()
        quit_action = menu.addAction("Salir")

        action = menu.exec(pos)
        if action == quit_action:
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()
        elif action == open_action:
            self.left_clicked.emit()

    def fade_in(self):
        self.setWindowOpacity(0)
        self.show()
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
