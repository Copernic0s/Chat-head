from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QFont, QMouseEvent, QPaintEvent, QIcon, QPixmap


class BubbleWidget(QWidget):
    left_clicked = pyqtSignal()
    drag_finished = pyqtSignal()
    badge_updated = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = QPoint()
        self._dragging = False
        self._unread = 0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(64, 64)

        self.badge = QLabel("", self)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet("""
            QLabel {
                background-color: #ef4444;
                color: white;
                font-size: 11px;
                font-weight: bold;
                border-radius: 10px;
                padding: 2px 5px;
                min-width: 16px;
                min-height: 16px;
            }
        """)
        self.badge.adjustSize()
        self.badge.hide()

        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(200)

    def set_unread(self, count: int):
        self._unread = count
        if count > 0:
            self.badge.setText(str(count))
            self.badge.adjustSize()
            self.badge.move(
                self.width() - self.badge.width() - 4,
                -2,
            )
            self.badge.show()
        else:
            self.badge.hide()
        self.badge_updated.emit(count)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor("#094771"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 60, 60)

        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.setPen(QColor("white"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "💬")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragging = True
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                delta = (event.globalPosition().toPoint() - self._drag_pos - self.pos()).manhattanLength()
                self._dragging = False
                self.drag_finished.emit()
                if delta < 5:
                    self.left_clicked.emit()

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #252526;
                border: 1px solid #333;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
                color: #e0e0e0;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
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
        elif action == config_action:
            pass

    def fade_in(self):
        self.setWindowOpacity(0)
        self.show()
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def fade_out(self, callback=None):
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        if callback:
            self.fade_anim.finished.connect(callback)
        self.fade_anim.start()
