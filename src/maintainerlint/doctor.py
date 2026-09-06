from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import PurePosixPath
import shutil


@dataclass(frozen=True)
class DoctorFinding:
    level: str
    message: str


_HIGH_RISK_PATTERNS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
    "**/credentials.json",
    "**/secrets.json",
    "**/id_rsa",
    "**/id_ed25519",
)

_SAFE_EXAMPLES = (".env.example", ".env.sample", ".env.template")


def suspicious_tracked_files(paths: tuple[str, ...], allowlist: tuple[str, ...]) -> tuple[str, ...]:
    findings: list[str] = []
    for path in paths:
        normalized = PurePosixPath(path).as_posix()
        if normalized in _SAFE_EXAMPLES or any(fnmatch(normalized, pattern) for pattern in allowlist):
            continue
        if any(fnmatch(normalized, pattern) for pattern in _HIGH_RISK_PATTERNS):
            findings.append(normalized)
    return tuple(findings)


def environment_findings() -> tuple[DoctorFinding, ...]:
    findings: list[DoctorFinding] = []
    for executable in ("git",):
        if shutil.which(executable):
            findings.append(DoctorFinding("PASS", f"{executable} is available"))
        else:
            findings.append(DoctorFinding("FAIL", f"{executable} is not available"))
    return tuple(findings)
