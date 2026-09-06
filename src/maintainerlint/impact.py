from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch

from .config import DocRule


@dataclass(frozen=True)
class RuleResult:
    name: str
    triggered_by: tuple[str, ...]
    satisfied: bool
    missing_any: tuple[str, ...]
    missing_all: tuple[str, ...]


def _matches(path: str, pattern: str) -> bool:
    # fnmatch handles the common repo-path glob forms used in MaintainerLint config.
    return fnmatch(path, pattern)


def evaluate_rules(changed: tuple[str, ...], rules: tuple[DocRule, ...]) -> tuple[RuleResult, ...]:
    changed_set = set(changed)
    results: list[RuleResult] = []
    for rule in rules:
        triggers = tuple(
            path for path in changed if any(_matches(path, pattern) for pattern in rule.patterns)
        )
        if not triggers:
            continue
        any_ok = not rule.required_any or any(path in changed_set for path in rule.required_any)
        missing_any = () if any_ok else rule.required_any
        missing_all = tuple(path for path in rule.required_all if path not in changed_set)
        results.append(
            RuleResult(
                name=rule.name,
                triggered_by=triggers,
                satisfied=any_ok and not missing_all,
                missing_any=missing_any,
                missing_all=missing_all,
            )
        )
    return tuple(results)
