from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tomllib


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Stage:
    name: str
    command: tuple[str, ...]
    cwd: str | None = None
    timeout: int = 300
    allow_failure: bool = False


@dataclass(frozen=True)
class DocRule:
    name: str
    patterns: tuple[str, ...]
    required_any: tuple[str, ...]
    required_all: tuple[str, ...]


@dataclass(frozen=True)
class Config:
    version: int
    stages: tuple[Stage, ...]
    doc_rules: tuple[DocRule, ...]
    secret_allowlist: tuple[str, ...]


def _list_of_strings(value: Any, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ConfigError(f"{field} must be an array of non-empty strings")
    return tuple(value)


def load_config(path: Path) -> Config:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}") from exc

    version = raw.get("version", 1)
    if version != 1:
        raise ConfigError(f"unsupported config version: {version!r}")

    stages: list[Stage] = []
    seen_names: set[str] = set()
    for index, item in enumerate(raw.get("stages", [])):
        if not isinstance(item, dict):
            raise ConfigError(f"stages[{index}] must be a table")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f"stages[{index}].name must be a non-empty string")
        if name in seen_names:
            raise ConfigError(f"duplicate stage name: {name}")
        seen_names.add(name)
        command = _list_of_strings(item.get("command"), f"stages[{index}].command")
        if not command:
            raise ConfigError(f"stages[{index}].command cannot be empty")
        timeout = item.get("timeout", 300)
        if not isinstance(timeout, int) or timeout <= 0:
            raise ConfigError(f"stages[{index}].timeout must be a positive integer")
        cwd = item.get("cwd")
        if cwd is not None and (not isinstance(cwd, str) or not cwd):
            raise ConfigError(f"stages[{index}].cwd must be a non-empty string")
        allow_failure = item.get("allow_failure", False)
        if not isinstance(allow_failure, bool):
            raise ConfigError(f"stages[{index}].allow_failure must be boolean")
        stages.append(Stage(name, command, cwd, timeout, allow_failure))

    docs = raw.get("docs", {})
    if not isinstance(docs, dict):
        raise ConfigError("docs must be a table")
    doc_rules: list[DocRule] = []
    for index, item in enumerate(docs.get("rules", [])):
        if not isinstance(item, dict):
            raise ConfigError(f"docs.rules[{index}] must be a table")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f"docs.rules[{index}].name must be a non-empty string")
        patterns = _list_of_strings(item.get("patterns"), f"docs.rules[{index}].patterns")
        required_any = _list_of_strings(item.get("required_any"), f"docs.rules[{index}].required_any")
        required_all = _list_of_strings(item.get("required_all"), f"docs.rules[{index}].required_all")
        if not patterns:
            raise ConfigError(f"docs.rules[{index}].patterns cannot be empty")
        if not required_any and not required_all:
            raise ConfigError(f"docs.rules[{index}] must define required_any or required_all")
        doc_rules.append(DocRule(name, patterns, required_any, required_all))

    security = raw.get("security", {})
    if not isinstance(security, dict):
        raise ConfigError("security must be a table")
    secret_allowlist = _list_of_strings(security.get("tracked_secret_allowlist"), "security.tracked_secret_allowlist")

    return Config(version, tuple(stages), tuple(doc_rules), secret_allowlist)
