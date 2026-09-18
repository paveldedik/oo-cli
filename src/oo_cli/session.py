"""The session cookies of an authenticating gateway, kept between runs.

Cookies are stored under the endpoint they were issued for and are never inspected;
whatever the gateway set is what gets replayed. The file is the user's to read,
nobody else's.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

def path() -> Path:
    return Path(os.environ.get("OO_HOME") or Path.home() / ".oo") / "session.json"


def load(endpoint: str) -> dict[str, str]:
    entry = _read().get(endpoint)
    if not entry:
        return {}
    return entry.get("cookies", {})


def age(endpoint: str) -> float | None:
    """Seconds since the session was stored, or None when there is none."""
    entry = _read().get(endpoint)
    return None if not entry else time.time() - entry.get("saved_at", 0)


def save(endpoint: str, cookies: dict[str, str]) -> None:
    sessions = _read()
    sessions[endpoint] = {"cookies": cookies, "saved_at": time.time()}
    _write(sessions)


def clear(endpoint: str) -> bool:
    sessions = _read()
    if endpoint not in sessions:
        return False
    del sessions[endpoint]
    _write(sessions)
    return True


def header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in sorted(cookies.items()))


def _read() -> dict[str, dict]:
    try:
        return json.loads(path().read_text())
    except (OSError, ValueError):
        return {}


def _write(sessions: dict[str, dict]) -> None:
    file = path()
    file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    file.touch(mode=0o600, exist_ok=True)
    file.write_text(json.dumps(sessions, indent=2))
    os.chmod(file, 0o600)
