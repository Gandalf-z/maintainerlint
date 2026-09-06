from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase

from .gitutils import ChangeEntry


@dataclass(frozen=True)
class ScopeFinding:
    change: ChangeEntry
    escaped_paths: tuple[str, ...]


@dataclass(frozen=True)
class ScopeResult:
    findings: tuple[ScopeFinding, ...]

    @property
    def escaped_paths(self) -> tuple[str, ...]:
        paths: list[str] = []
        for finding in self.findings:
            for path in finding.escaped_paths:
                if path not in paths:
                    paths.append(path)
        return tuple(paths)

    @property
    def satisfied(self) -> bool:
        return not self.escaped_paths


def _normalize(value: str) -> str:
    normalized = value.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = _normalize(path)
    return any(fnmatchcase(normalized, _normalize(pattern)) for pattern in patterns)


def _paths_to_check(change: ChangeEntry) -> tuple[str, ...]:
    kind = change.status[:1]
    if kind == "C":
        return (change.paths[-1],)
    return change.paths


def evaluate_scope(
    changes: tuple[ChangeEntry, ...],
    allow: tuple[str, ...],
    support: tuple[str, ...] = (),
) -> ScopeResult:
    patterns = tuple(allow) + tuple(support)
    findings: list[ScopeFinding] = []
    for change in changes:
        escaped = tuple(
            path for path in _paths_to_check(change)
            if not _matches(path, patterns)
        )
        if escaped:
            findings.append(ScopeFinding(change=change, escaped_paths=escaped))
    return ScopeResult(findings=tuple(findings))