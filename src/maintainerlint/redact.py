from __future__ import annotations

from pathlib import Path
import re


_SECRET_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(
        r"(?i)([\"']?(?:api[_ -]?key|authorization|[a-z0-9_.-]*token|[a-z0-9_.-]*secret|password|credential)[\"']?\s*[:=]\s*)"
        r"(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
    ),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b", re.I),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
)


def _path_spellings(path: Path) -> tuple[str, ...]:
    raw = str(path)
    spellings = {raw}
    if "\\" in raw:
        spellings.add(raw.replace("\\", "/"))
    if re.match(r"^[A-Za-z]:/", raw):
        spellings.add(raw.replace("/", "\\"))
    return tuple(sorted((item for item in spellings if item), key=len, reverse=True))


def _redact_path(value: str, path: Path, marker: str) -> str:
    for spelling in _path_spellings(path):
        if re.match(r"^[A-Za-z]:[\\/]", spelling):
            value = re.sub(re.escape(spelling), marker, value, flags=re.IGNORECASE)
        else:
            value = value.replace(spelling, marker)
    return value


def redact(text: object, *, repo: Path | None = None, home: Path | None = None) -> str:
    value = str(text or "")
    if repo is not None:
        value = _redact_path(value, repo, "<REPO>")
    home = home or Path.home()
    value = _redact_path(value, home, "<HOME>")
    for index, pattern in enumerate(_SECRET_PATTERNS):
        if index == 1:
            value = pattern.sub(lambda match: f"{match.group(1)}<REDACTED>", value)
        else:
            value = pattern.sub("<REDACTED>", value)
    return value
