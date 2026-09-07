from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tomllib


class TaskError(ValueError):
    pass


@dataclass(frozen=True)
class TaskContract:
    version: int
    base: str
    head: str
    allow: tuple[str, ...]
    support: tuple[str, ...]
    targeted_stages: tuple[str, ...]


_ALLOWED_FIELDS = {
    "version",
    "base",
    "head",
    "allow",
    "support",
    "targeted_stages",
}


def _non_empty_string(value: Any, field: str, default: str | None = None) -> str:
    if value is None and default is not None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise TaskError(f"{field} must be a non-empty string")
    return value


def _string_array(
    value: Any,
    field: str,
    *,
    required: bool = False,
) -> tuple[str, ...]:
    if value is None:
        if required:
            raise TaskError(f"{field} must be a non-empty array of strings")
        return ()
    if (
        not isinstance(value, list)
        or not all(isinstance(item, str) and item.strip() for item in value)
        or (required and not value)
    ):
        qualifier = "non-empty " if required else ""
        raise TaskError(f"{field} must be a {qualifier}array of non-empty strings")
    return tuple(value)


def load_task(path: Path) -> TaskContract:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TaskError(f"task contract not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise TaskError(f"invalid TOML in task contract {path}: {exc}") from exc

    unknown = sorted(set(raw) - _ALLOWED_FIELDS)
    if unknown:
        raise TaskError(f"unknown task field(s): {', '.join(unknown)}")

    version = raw.get("version")
    if version != 1:
        raise TaskError(f"unsupported task contract version: {version!r}")

    return TaskContract(
        version=1,
        base=_non_empty_string(raw.get("base"), "base", "HEAD~1"),
        head=_non_empty_string(raw.get("head"), "head", "HEAD"),
        allow=_string_array(raw.get("allow"), "allow", required=True),
        support=_string_array(raw.get("support"), "support"),
        targeted_stages=_string_array(raw.get("targeted_stages"), "targeted_stages"),
    )
