import sqlite3
import os
import json
from pathlib import Path
from typing import Optional
from .models import ChatHeadState


DB_DIR = Path.home() / ".telegram-chat-head"
DB_PATH = DB_DIR / "state.db"


def _ensure_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )"""
    )
    conn.commit()
    return conn


def save_state(state: ChatHeadState):
    conn = _ensure_db()
    data = {
        "x": state.x,
        "y": state.y,
        "active_chat_id": state.active_chat_id,
        "panel_open": state.panel_open,
    }
    conn.execute(
        "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
        ("chat_head_state", json.dumps(data)),
    )
    conn.commit()
    conn.close()


def load_state() -> ChatHeadState:
    conn = _ensure_db()
    cursor = conn.execute(
        "SELECT value FROM state WHERE key = ?", ("chat_head_state",)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        data = json.loads(row[0])
        return ChatHeadState(
            x=data.get("x", 100),
            y=data.get("y", 100),
            active_chat_id=data.get("active_chat_id"),
            panel_open=data.get("panel_open", False),
        )
    return ChatHeadState()
