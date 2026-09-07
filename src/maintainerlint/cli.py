from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import sys

from . import __version__
from .config import ConfigError, load_config
from .detect import DetectionResult, detect_stages
from .doctor import environment_findings, suspicious_tracked_files
from .gitutils import GitError, changed_entries, changed_files, repo_root, tracked_files
from .impact import build_report, render_report
from .runner import StageExecutionError, run_stage
from .scope import evaluate_scope
from .templates import DEFAULT_CONFIG, PR_TEMPLATE, render_detected_config


def _resolve_repo(path: str | None) -> Path:
    start = Path(path or ".").expanduser().resolve()
    return repo_root(start)


def _config_path(repo: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (repo / path).resolve()


def _external_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _display_path(path: Path, repo: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo.resolve()))
    except ValueError:
        pass
    home = Path.home().resolve()
    try:
        return str(Path("~") / resolved.relative_to(home))
    except ValueError:
        return str(resolved)


def _print_detection(result: DetectionResult) -> None:
    if result.signals:
        for signal in result.signals:
            print(f"DETECT {signal}")
    else:
        print("DETECT no supported repository signals")
    for proposal in result.proposals:
        print(
            f"PROPOSE {proposal.ecosystem}/{proposal.name}: "
            f"{shlex.join(proposal.command)} ({proposal.reason})"
        )


def _proposed_policy(target: Path, *, detect: bool) -> str:
    config_text = DEFAULT_CONFIG
    if detect:
        detection = detect_stages(target)
        _print_detection(detection)
        if detection.usable:
            config_text = render_detected_config(detection.proposals)
            print(f"USE detected {detection.ecosystems[0]} stages")
        else:
            print(f"FALLBACK generic starter: {detection.fallback_reason}")
    return config_text


def _print_policy(config_text: str) -> None:
    print("POLICY BEGIN maintainerlint.toml")
    print(config_text, end="" if config_text.endswith("\n") else "\n")
    print("POLICY END maintainerlint.toml")


def command_init(args: argparse.Namespace) -> int:
    target = Path(args.directory).expanduser().resolve()
    dry_run = bool(getattr(args, "dry_run", False))
    config = target / "maintainerlint.toml"

    if config.exists() and not args.force:
        print(f"SKIP {config.name} already exists (use --force to replace)")
    else:
        config_text = _proposed_policy(target, detect=bool(getattr(args, "detect", False)))
        if dry_run:
            action = "REPLACE" if config.exists() else "CREATE"
            print(f"WOULD {action} {config}")
            _print_policy(config_text)
        else:
            target.mkdir(parents=True, exist_ok=True)
            config.write_text(config_text, encoding="utf-8")
            print(f"CREATE {config}")

    if args.pr_template:
        pr = target / ".github" / "pull_request_template.md"
        if pr.exists() and not args.force:
            print(f"SKIP {pr} already exists (use --force to replace)")
        elif dry_run:
            action = "REPLACE" if pr.exists() else "CREATE"
            print(f"WOULD {action} {pr}")
        else:
            pr.parent.mkdir(parents=True, exist_ok=True)
            pr.write_text(PR_TEMPLATE, encoding="utf-8")
            print(f"CREATE {pr}")

    if dry_run:
        print("ZERO-WRITE dry-run: MaintainerLint created or modified no target files")
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    repo = _resolve_repo(args.repo)
    detection = detect_stages(repo)
    print(f"INSPECT repository: {repo}")
    _print_detection(detection)

    if detection.usable:
        config_text = render_detected_config(detection.proposals)
        print(f"USE detected {detection.ecosystems[0]} stages")
    else:
        config_text = DEFAULT_CONFIG
        print(f"FALLBACK generic starter: {detection.fallback_reason}")

    _print_policy(config_text)

    config = repo / "maintainerlint.toml"
    if config.exists():
        print("ADOPT init --detect would keep existing maintainerlint.toml")
        print("ADOPT review first; --force is required to replace existing policy")
    else:
        print("ADOPT init --detect would create maintainerlint.toml")
    print("ADOPT init --detect --pr-template would additionally create .github/pull_request_template.md")
    print("ZERO-WRITE inspect: MaintainerLint created or modified no target files")
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

    if args.log_dir:
        log_root = _external_path(args.log_dir)
    elif args.state_dir:
        log_root = _external_path(args.state_dir) / "logs"
    else:
        log_root = repo / ".maintainerlint" / "logs"

    failed = False
    for stage in stages:
        result = run_stage(stage, repo=repo, log_root=log_root)
        label = "PASS" if result.passed else ("WARN" if result.allowed_failure else "FAIL")
        print(f"{label} {result.name} ({result.duration_seconds:.1f}s)")
        if not result.passed:
            if result.failure_summary:
                print("  failing: " + "; ".join(result.failure_summary))
            print(f"  log: {_display_path(result.log_path, repo)}")
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

    report = build_report(changed, config.doc_rules)
    print(render_report(report, args.format))
    return 1 if args.strict and not report.satisfied else 0


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
    config_path = _config_path(repo, args.config)
    config = load_config(config_path)
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
    print(f"PASS config loaded: {_display_path(config_path, repo)}")
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maintainerlint",
        description="Deterministic guardrails for AI-assisted software maintenance.",
    )
    parser.add_argument("--version", action="version", version=f"maintainerlint {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create or preview a starter MaintainerLint config")
    init.add_argument("directory", nargs="?", default=".")
    init.add_argument("--force", action="store_true")
    init.add_argument(
        "--detect",
        action="store_true",
        help="propose conservative stages from repository files before creating policy",
    )
    init.add_argument(
        "--dry-run",
        action="store_true",
        help="print the exact proposed policy and planned writes without creating files",
    )
    init.add_argument("--pr-template", action="store_true", help="also create a concise PR template")
    init.set_defaults(func=command_init)

    inspect = sub.add_parser("inspect", help="inspect a repository and preview adoption without writes")
    inspect.add_argument("--repo")
    inspect.set_defaults(func=command_inspect)

    check = sub.add_parser("check", help="run configured low-output verification stages")
    check.add_argument("--repo")
    check.add_argument("--config", default="maintainerlint.toml")
    check.add_argument("--stage", action="append", help="run only this named stage; repeatable")
    check.add_argument(
        "--state-dir",
        help="store MaintainerLint-owned state outside the repository; logs use DIR/logs",
    )
    check.add_argument(
        "--log-dir",
        help="store MaintainerLint-owned logs in DIR; overrides --state-dir for logs",
    )
    check.set_defaults(func=command_check)

    impact = sub.add_parser("impact", help="evaluate documentation-drift rules for changed files")
    impact.add_argument("--repo")
    impact.add_argument("--config", default="maintainerlint.toml")
    impact.add_argument("--base", default="HEAD~1")
    impact.add_argument("--head", default="HEAD")
    impact.add_argument("--changed", action="append", help="explicit changed path; bypasses git diff")
    impact.add_argument("--strict", action="store_true", help="exit non-zero when a rule is unsatisfied")
    impact.add_argument("--format", choices=("text", "markdown", "json"), default="text")
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
