from __future__ import annotations
import json
from pathlib import Path
from typing import Any

# Use project root so runtime/ is always in the same place
_project_root = Path(__file__).resolve().parent.parent
RUNTIME_DIR = _project_root / "runtime"
STATE_PATH = RUNTIME_DIR / "state.json"


def load_state() -> dict[str, Any] | None:
    try:
        if not STATE_PATH.exists():
            return None
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_state(payload: dict[str, Any]) -> None:
    try:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass
