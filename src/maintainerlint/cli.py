from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .config import ConfigError, load_config
from .doctor import environment_findings, suspicious_tracked_files
from .gitutils import GitError, changed_entries, changed_files, repo_root, tracked_files
from .impact import evaluate_rules
from .runner import StageExecutionError, run_stage
from .scope import evaluate_scope
from .templates import DEFAULT_CONFIG, PR_TEMPLATE


def _resolve_repo(path: str | None) -> Path:
    start = Path(path or ".").resolve()
    return repo_root(start)


def _config_path(repo: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo / path


def command_init(args: argparse.Namespace) -> int:
    target = Path(args.directory).resolve()
    target.mkdir(parents=True, exist_ok=True)
    config = target / "maintainerlint.toml"
    if config.exists() and not args.force:
        print(f"SKIP {config.name} already exists (use --force to replace)")
    else:
        config.write_text(DEFAULT_CONFIG, encoding="utf-8")
        print(f"CREATE {config}")

    if args.pr_template:
        pr = target / ".github" / "pull_request_template.md"
        pr.parent.mkdir(parents=True, exist_ok=True)
        if pr.exists() and not args.force:
            print(f"SKIP {pr} already exists (use --force to replace)")
        else:
            pr.write_text(PR_TEMPLATE, encoding="utf-8")
            print(f"CREATE {pr}")
    return 0


def command_check(args: argparse.Namespace) -> int:
    repo = _resolve_repo(args.repo)
    config = load_config(_config_path(repo, args.config))
    selected = set(args.stage or ())
    unknown = selected - {stage.name for stage in config.stages}
    if unknown:
        raise ConfigError(f"unknown stage(s): {', '.join(sorted(unknown))}")

    stages = tuple(stage for stage in config.stages if not selected or stage.name in selected)
    if not stages:
        print("SKIP no stages configured")
        return 0

    log_root = repo / ".maintainerlint" / "logs"
    failed = False
    for stage in stages:
        result = run_stage(stage, repo=repo, log_root=log_root)
        label = "PASS" if result.passed else ("WARN" if result.allowed_failure else "FAIL")
        print(f"{label} {result.name} ({result.duration_seconds:.1f}s)")
        if not result.passed:
            if result.failure_summary:
                print("  failing: " + "; ".join(result.failure_summary))
            print(f"  log: {result.log_path.relative_to(repo)}")
            for line in result.failure_tail:
                print(f"  | {line}")
            if not result.allowed_failure:
                failed = True
    return 1 if failed else 0


def command_impact(args: argparse.Namespace) -> int:
    repo = _resolve_repo(args.repo)
    config = load_config(_config_path(repo, args.config))
    changed = tuple(args.changed or ())
    if not changed:
        changed = changed_files(repo, args.base, args.head)

    results = evaluate_rules(changed, config.doc_rules)
    if args.format == "json":
        import json

        print(json.dumps({
            "changed": changed,
            "rules": [
                {
                    "name": result.name,
                    "triggered_by": result.triggered_by,
                    "satisfied": result.satisfied,
                    "missing_any": result.missing_any,
                    "missing_all": result.missing_all,
                }
                for result in results
            ],
        }, indent=2))
    else:
        if not results:
            print("PASS documentation impact: no configured rules triggered")
        for result in results:
            label = "PASS" if result.satisfied else "FAIL"
            print(f"{label} documentation impact: {result.name}")
            print("  triggered by: " + ", ".join(result.triggered_by))
            if result.missing_any:
                print("  require at least one: " + ", ".join(result.missing_any))
            if result.missing_all:
                print("  require all: " + ", ".join(result.missing_all))

    unsatisfied = any(not result.satisfied for result in results)
    return 1 if args.strict and unsatisfied else 0


def command_scope(args: argparse.Namespace) -> int:
    repo = _resolve_repo(args.repo)
    changes = changed_entries(repo, args.base, args.head)
    result = evaluate_scope(
        changes,
        tuple(args.allow),
        tuple(args.allow_support or ()),
    )

    if not changes:
        print("PASS scope: no changed files")
        return 0

    if result.satisfied:
        print(
            f"PASS scope: {len(changes)} change(s) stayed within "
            f"{len(args.allow)} primary and {len(args.allow_support or ())} support pattern(s)"
        )
        return 0

    label = "FAIL" if args.strict else "WARN"
    print(f"{label} scope: {len(result.escaped_paths)} path(s) escaped the declared boundary")
    for finding in result.findings:
        rendered = " -> ".join(finding.change.paths)
        print(f"  {finding.change.status} {rendered}")
        for path in finding.escaped_paths:
            print(f"    escaped: {path}")
    return 1 if args.strict else 0


def command_doctor(args: argparse.Namespace) -> int:
    repo = _resolve_repo(args.repo)
    config = load_config(_config_path(repo, args.config))
    failed = False
    for finding in environment_findings():
        print(f"{finding.level} {finding.message}")
        failed = failed or finding.level == "FAIL"

    risky = suspicious_tracked_files(tracked_files(repo), config.secret_allowlist)
    if risky:
        failed = True
        print("FAIL suspicious secret-like files are tracked:")
        for path in risky:
            print(f"  - {path}")
    else:
        print("PASS no high-confidence secret-like tracked files found")
    print(f"PASS config loaded: {_config_path(repo, args.config).relative_to(repo)}")
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maintainerlint",
        description="Deterministic guardrails for AI-assisted software maintenance.",
    )
    parser.add_argument("--version", action="version", version=f"maintainerlint {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a starter MaintainerLint config")
    init.add_argument("directory", nargs="?", default=".")
    init.add_argument("--force", action="store_true")
    init.add_argument("--pr-template", action="store_true", help="also create a concise PR template")
    init.set_defaults(func=command_init)

    check = sub.add_parser("check", help="run configured low-output verification stages")
    check.add_argument("--repo")
    check.add_argument("--config", default="maintainerlint.toml")
    check.add_argument("--stage", action="append", help="run only this named stage; repeatable")
    check.set_defaults(func=command_check)

    impact = sub.add_parser("impact", help="evaluate documentation-drift rules for changed files")
    impact.add_argument("--repo")
    impact.add_argument("--config", default="maintainerlint.toml")
    impact.add_argument("--base", default="HEAD~1")
    impact.add_argument("--head", default="HEAD")
    impact.add_argument("--changed", action="append", help="explicit changed path; bypasses git diff")
    impact.add_argument("--strict", action="store_true", help="exit non-zero when a rule is unsatisfied")
    impact.add_argument("--format", choices=("text", "json"), default="text")
    impact.set_defaults(func=command_impact)

    scope = sub.add_parser("scope", help="check that a Git diff stayed inside declared path boundaries")
    scope.add_argument("--repo")
    scope.add_argument("--base", default="HEAD~1")
    scope.add_argument("--head", default="HEAD")
    scope.add_argument(
        "--allow",
        action="append",
        required=True,
        help="allowed primary path glob; repeatable",
    )
    scope.add_argument(
        "--allow-support",
        action="append",
        help="allowed support-artifact glob (for example docs/**); repeatable",
    )
    scope.add_argument("--strict", action="store_true", help="exit non-zero when any path escapes")
    scope.set_defaults(func=command_scope)

    doctor = sub.add_parser("doctor", help="check repo/config prerequisites and tracked-secret risks")
    doctor.add_argument("--repo")
    doctor.add_argument("--config", default="maintainerlint.toml")
    doctor.set_defaults(func=command_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ConfigError, GitError, StageExecutionError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())