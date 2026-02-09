from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryStore:
    last_fingerprint: str | None = None

    commentary: list[str] = field(default_factory=list)
    winprob_history: list[str] = field(default_factory=list)

    winprob_home: float | None = None
    postgame_recap: str | None = None

    last_state: dict[str, Any] | None = None

    poll_count: int = 0
    last_update_iso: str | None = None


STORE = MemoryStore()
