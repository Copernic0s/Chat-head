GLASS_BG = "rgba(18, 20, 26, 0.72)"
GLASS_BORDER = "rgba(255, 255, 255, 0.07)"
GLASS_HIGHLIGHT = "rgba(255, 255, 255, 0.03)"
ACCENT = "#0a84ff"
ACCENT_GLOW = "rgba(10, 132, 255, 0.25)"
TEXT_PRIMARY = "rgba(255, 255, 255, 0.92)"
TEXT_SECONDARY = "rgba(255, 255, 255, 0.50)"
DANGER = "#ff453a"
SENT_BG = "rgba(10, 132, 255, 0.80)"
RECEIVED_BG = "rgba(255, 255, 255, 0.08)"
FONT = '"Segoe UI Variable", "Segoe UI", system-ui, -apple-system, sans-serif'

PANEL_STYLE = f"""
    QWidget {{
        font-family: {FONT};
        font-size: 13px;
        color: {TEXT_PRIMARY};
    }}
    QListWidget {{
        border: none;
        background: transparent;
        outline: none;
        padding: 4px 0;
    }}
    QListWidget::item {{
        padding: 14px 16px;
        border: none;
        border-radius: 10px;
        margin: 2px 8px;
    }}
    QListWidget::item:hover {{
        background: {GLASS_HIGHLIGHT};
    }}
    QListWidget::item:selected {{
        background: {ACCENT_GLOW};
    }}
    QTextEdit {{
        border: 1px solid {GLASS_BORDER};
        border-radius: 20px;
        background: rgba(255,255,255,0.06);
        color: {TEXT_PRIMARY};
        padding: 8px 16px;
        font-size: 13px;
        font-family: {FONT};
        selection-background-color: {ACCENT};
    }}
    QTextEdit:focus {{
        border-color: {ACCENT};
    }}
    QScrollBar:vertical {{
        width: 4px;
        background: transparent;
        margin: 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255,255,255,0.15);
        border-radius: 2px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(255,255,255,0.25);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
"""

BUBBLE_GRADIENT_START = "#0a84ff"
BUBBLE_GRADIENT_END = "#0066cc"

BUBBLE_STYLE = f"""
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {BUBBLE_GRADIENT_START},
        stop:1 {BUBBLE_GRADIENT_END});
    border: 1px solid rgba(255,255,255,0.15);
"""

BADGE_STYLE = f"""
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
"""

HEADER_STYLE = f"""
    background: rgba(255,255,255,0.04);
    border-bottom: 1px solid {GLASS_BORDER};
"""

CHAT_ITEM_NAME = f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600; background: transparent;"
CHAT_ITEM_PREVIEW = f"color: {TEXT_SECONDARY}; font-size: 11px; background: transparent;"
CHAT_ITEM_TIME = f"color: rgba(255,255,255,0.3); font-size: 10px; background: transparent;"
CHAT_ITEM_BADGE = f"""
    background-color: {DANGER};
    color: white;
    font-size: 10px;
    font-weight: 700;
    border-radius: 8px;
    padding: 1px 5px;
    min-width: 14px;
"""

AVATAR_STYLE = f"""
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {ACCENT},
        stop:1 #0055aa);
    color: white;
    font-size: 17px;
    font-weight: 700;
    border-radius: 20px;
"""

MESSAGE_SENT = f"""
    QLabel {{
        background-color: {SENT_BG};
        color: white;
        padding: 8px 14px;
        border-radius: 16px 16px 4px 16px;
        font-size: 13px;
    }}
"""

MESSAGE_RECEIVED = f"""
    QLabel {{
        background-color: {RECEIVED_BG};
        color: {TEXT_PRIMARY};
        padding: 8px 14px;
        border-radius: 16px 16px 16px 4px;
        font-size: 13px;
    }}
"""

SEND_BTN_STYLE = f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {ACCENT},
            stop:1 #0055aa);
        border: none;
        border-radius: 18px;
        color: white;
        font-size: 16px;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #0a93ff,
            stop:1 #0066cc);
    }}
    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #0066cc,
            stop:1 #004488);
    }}
"""

CLOSE_BTN = f"""
    QPushButton {{
        background: transparent;
        border: none;
        color: rgba(255,255,255,0.4);
        font-size: 14px;
        border-radius: 14px;
        padding: 4px;
    }}
    QPushButton:hover {{
        background: rgba(255,255,255,0.1);
        color: {DANGER};
    }}
"""

BACK_BTN = f"""
    QPushButton {{
        background: transparent;
        border: none;
        color: {TEXT_SECONDARY};
        font-size: 16px;
        border-radius: 14px;
        padding: 4px;
    }}
    QPushButton:hover {{
        background: rgba(255,255,255,0.1);
        color: white;
    }}
"""
