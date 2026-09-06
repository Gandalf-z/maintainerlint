from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
import json

from .config import DocRule


IMPACT_SCHEMA = "maintainerlint.impact"
IMPACT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RuleResult:
    name: str
    triggered_by: tuple[str, ...]
    satisfied: bool
    missing_any: tuple[str, ...]
    missing_all: tuple[str, ...]

    @property
    def status(self) -> str:
        return "pass" if self.satisfied else "fail"


@dataclass(frozen=True)
class ImpactReport:
    changed: tuple[str, ...]
    rules: tuple[RuleResult, ...]

    @property
    def satisfied(self) -> bool:
        return all(result.satisfied for result in self.rules)

    @property
    def status(self) -> str:
        return "pass" if self.satisfied else "fail"

    @property
    def failed_rule_count(self) -> int:
        return sum(not result.satisfied for result in self.rules)


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


def build_report(changed: tuple[str, ...], rules: tuple[DocRule, ...]) -> ImpactReport:
    return ImpactReport(changed=changed, rules=evaluate_rules(changed, rules))


def report_to_dict(report: ImpactReport) -> dict[str, object]:
    return {
        "schema": IMPACT_SCHEMA,
        "schema_version": IMPACT_SCHEMA_VERSION,
        "status": report.status,
        "changed": list(report.changed),
        "summary": {
            "triggered_rules": len(report.rules),
            "failed_rules": report.failed_rule_count,
        },
        "rules": [
            {
                "name": result.name,
                "status": result.status,
                "satisfied": result.satisfied,
                "triggered_by": list(result.triggered_by),
                "missing_any": list(result.missing_any),
                "missing_all": list(result.missing_all),
            }
            for result in report.rules
        ],
    }


def render_text(report: ImpactReport) -> str:
    if not report.rules:
        return "PASS documentation impact: no configured rules triggered"

    lines: list[str] = []
    for result in report.rules:
        label = "PASS" if result.satisfied else "FAIL"
        lines.append(f"{label} documentation impact: {result.name}")
        lines.append("  triggered by: " + ", ".join(result.triggered_by))
        if result.missing_any:
            lines.append("  require at least one: " + ", ".join(result.missing_any))
        if result.missing_all:
            lines.append("  require all: " + ", ".join(result.missing_all))
    return "\n".join(lines)


def _markdown_paths(paths: tuple[str, ...]) -> str:
    return ", ".join(f"`{path}`" for path in paths)


def render_markdown(report: ImpactReport) -> str:
    lines = ["### MaintainerLint documentation impact", ""]
    if not report.rules:
        lines.append("**PASS** — no configured documentation-impact rules triggered.")
        return "\n".join(lines)

    triggered = len(report.rules)
    failed = report.failed_rule_count
    noun = "rule" if triggered == 1 else "rules"
    if report.satisfied:
        lines.append(f"**PASS** — {triggered} triggered {noun}; all satisfied.")
    else:
        lines.append(f"**FAIL** — {failed} of {triggered} triggered {noun} unsatisfied.")

    for result in report.rules:
        label = "PASS" if result.satisfied else "FAIL"
        lines.extend(["", f"- **{label}** {result.name}"])
        lines.append(f"  - Triggered by: {_markdown_paths(result.triggered_by)}")
        if result.missing_any:
            lines.append(f"  - Require at least one: {_markdown_paths(result.missing_any)}")
        if result.missing_all:
            lines.append(f"  - Require all: {_markdown_paths(result.missing_all)}")
    return "\n".join(lines)


def render_json(report: ImpactReport) -> str:
    return json.dumps(report_to_dict(report), indent=2)


def render_report(report: ImpactReport, format_name: str) -> str:
    if format_name == "text":
        return render_text(report)
    if format_name == "markdown":
        return render_markdown(report)
    if format_name == "json":
        return render_json(report)
    raise ValueError(f"unsupported impact format: {format_name}")
