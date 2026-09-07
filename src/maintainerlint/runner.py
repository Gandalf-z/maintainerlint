from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import time

from .config import Stage
from .redact import redact


@dataclass(frozen=True)
class StageResult:
    name: str
    passed: bool
    allowed_failure: bool
    duration_seconds: float
    log_path: Path
    failure_summary: tuple[str, ...]
    failure_tail: tuple[str, ...]


class StageExecutionError(RuntimeError):
    pass


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        path.chmod(0o700)


def _write_private(path: Path, content: str) -> None:
    _ensure_private_directory(path.parent)
    path.write_text(content, encoding="utf-8")
    if os.name != "nt":
        path.chmod(0o600)


def _failure_lines(output: str) -> tuple[str, ...]:
    found: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith(("FAILED ", "ERROR ", "FAIL ")) or " ASSERTIONERROR" in upper:
            summary = stripped.split(" - ", 1)[0]
            if summary and summary not in found:
                found.append(summary)
    return tuple(found[-30:])


def run_stage(stage: Stage, *, repo: Path, log_root: Path) -> StageResult:
    cwd = (repo / stage.cwd).resolve() if stage.cwd else repo
    try:
        cwd.relative_to(repo)
    except ValueError as exc:
        raise StageExecutionError(f"stage {stage.name!r} cwd escapes repository: {cwd}") from exc

    started = time.monotonic()
    try:
        proc = subprocess.run(
            list(stage.command),
            cwd=cwd,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=stage.timeout,
        )
        raw = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
        passed = proc.returncode == 0
    except subprocess.TimeoutExpired as exc:
        raw = "\n".join(
            str(part or "")
            for part in (exc.stdout, exc.stderr, f"TIMEOUT after {stage.timeout}s")
        )
        passed = False

    duration = time.monotonic() - started
    sanitized = redact(raw, repo=repo)
    wall_ns = time.time_ns()
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(wall_ns // 1_000_000_000))
    stamp = f"{stamp}-{wall_ns % 1_000_000_000:09d}"
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in stage.name)
    log_path = log_root / f"{stamp}-{safe_name}.log"
    _write_private(log_path, sanitized)
    summary = _failure_lines(sanitized)
    tail = tuple(sanitized.splitlines()[-80:]) if not passed else ()
    return StageResult(stage.name, passed, stage.allow_failure, duration, log_path, summary, tail)
