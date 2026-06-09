DARK_THEME = """
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", "San Francisco", "Helvetica Neue", sans-serif;
    font-size: 13px;
}
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
QTextEdit {
    border: none;
    background-color: #2d2d2d;
    color: #e0e0e0;
    padding: 8px;
    border-radius: 8px;
}
QPushButton {
    background-color: #2d2d2d;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    color: #e0e0e0;
}
QPushButton:hover {
    background-color: #3d3d3d;
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
QMenu {
    background-color: #252526;
    border: 1px solid #333;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #094771;
}
"""

CHAT_BUBBLE_STYLE = """
QWidget {
    background: transparent;
}
"""

MESSAGE_BUBBLE_SENT = """
QLabel {
    background-color: #094771;
    color: white;
    padding: 8px 14px;
    border-radius: 14px;
    font-size: 13px;
}
"""

MESSAGE_BUBBLE_RECEIVED = """
QLabel {
    background-color: #2d2d2d;
    color: #e0e0e0;
    padding: 8px 14px;
    border-radius: 14px;
    font-size: 13px;
}
"""

BADGE_STYLE = """
QLabel {
    background-color: #ef4444;
    color: white;
    font-size: 11px;
    font-weight: bold;
    border-radius: 10px;
    padding: 2px 6px;
    min-width: 16px;
    min-height: 16px;
}
"""
