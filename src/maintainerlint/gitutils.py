from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChangeEntry:
    status: str
    paths: tuple[str, ...]


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


def parse_name_status_z(output: str) -> tuple[ChangeEntry, ...]:
    tokens = output.split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()

    entries: list[ChangeEntry] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if not status:
            continue
        path_count = 2 if status[0] in {"R", "C"} else 1
        if index + path_count > len(tokens):
            raise GitError("unexpected git --name-status -z output")
        paths = tuple(tokens[index:index + path_count])
        index += path_count
        entries.append(ChangeEntry(status=status, paths=paths))
    return tuple(entries)


def changed_entries(repo: Path, base: str, head: str) -> tuple[ChangeEntry, ...]:
    output = run_git(repo, "diff", "--name-status", "-z", "-M", f"{base}...{head}")
    return parse_name_status_z(output)


def tracked_files(repo: Path) -> tuple[str, ...]:
    output = run_git(repo, "ls-files")
    return tuple(line.strip() for line in output.splitlines() if line.strip())