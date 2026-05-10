from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .update_formatter import UpdateItem


APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
HISTORY_FILE = DATA_DIR / "update_history.json"


def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_batch(updates: list[UpdateItem], discord_message: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = load_history()
    history.insert(
        0,
        {
            "created_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
            "updates": [asdict(update) for update in updates],
            "discord_message": discord_message,
        },
    )
    HISTORY_FILE.write_text(json.dumps(history[:50], indent=2), encoding="utf-8")
