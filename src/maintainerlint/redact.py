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


def redact(text: object, *, repo: Path | None = None, home: Path | None = None) -> str:
    value = str(text or "")
    if repo is not None:
        value = value.replace(str(repo), "<REPO>")
    home = home or Path.home()
    value = value.replace(str(home), "<HOME>")
    for index, pattern in enumerate(_SECRET_PATTERNS):
        if index == 1:
            value = pattern.sub(lambda match: f"{match.group(1)}<REDACTED>", value)
        else:
            value = pattern.sub("<REDACTED>", value)
    return value
