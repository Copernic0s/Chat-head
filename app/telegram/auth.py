import os
import json
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".telegram-chat-head"
CONFIG_PATH = CONFIG_DIR / "config.json"


def save_credentials(api_id: int, api_hash: str, phone: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {"api_id": api_id, "api_hash": api_hash, "phone": phone}
    CONFIG_PATH.write_text(json.dumps(data, indent=2))


def load_credentials() -> Optional[dict]:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return None


def delete_credentials():
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
