from __future__ import annotations

from pathlib import Path
import subprocess


class GitError(RuntimeError):
    pass


def run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise GitError(detail or f"git {' '.join(args)} failed")
    return proc.stdout


def repo_root(start: Path) -> Path:
    output = run_git(start, "rev-parse", "--show-toplevel").strip()
    return Path(output).resolve()


def changed_files(repo: Path, base: str, head: str) -> tuple[str, ...]:
    output = run_git(repo, "diff", "--name-only", f"{base}...{head}")
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def tracked_files(repo: Path) -> tuple[str, ...]:
    output = run_git(repo, "ls-files")
    return tuple(line.strip() for line in output.splitlines() if line.strip())
