from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def load_dotenv_if_available(start: Path | None = None) -> None:
    current = (start or Path.cwd()).resolve()
    candidates = [current, *current.parents]
    env_path = next((path / ".env" for path in candidates if (path / ".env").exists()), None)
    if env_path is None:
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        _load_simple_dotenv(env_path)
        return

    load_dotenv(env_path, override=False)


def _load_simple_dotenv(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_str(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().strip('"').strip("'")


def env_float(key: str, default: float) -> float:
    value = env_str(key)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except ValueError:
        return default


def env_int(key: str, default: int) -> int:
    value = env_str(key)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_bool(key: str, default: bool) -> bool:
    value = env_str(key)
    if value in (None, ""):
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def build_common_kwargs(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "max_tokens": env_int("MAX_TOKENS", 512),
        "timeout": env_int("MODEL_TIMEOUT", 120),
        "streaming": env_bool("STREAMING", True),
        "top_p": env_float("TOP_P", 0.9),
    }
    if extra:
        kwargs.update(extra)
    return kwargs
