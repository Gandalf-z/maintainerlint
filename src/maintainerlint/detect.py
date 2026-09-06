from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class StageProposal:
    ecosystem: str
    name: str
    command: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class DetectionResult:
    signals: tuple[str, ...]
    proposals: tuple[StageProposal, ...]

    @property
    def ecosystems(self) -> tuple[str, ...]:
        values: list[str] = []
        for signal in self.signals:
            ecosystem = signal.split(":", 1)[0]
            if ecosystem not in values:
                values.append(ecosystem)
        return tuple(values)

    @property
    def usable(self) -> bool:
        return len(self.ecosystems) == 1 and bool(self.proposals)

    @property
    def fallback_reason(self) -> str:
        if not self.signals:
            return "no supported repository signals found"
        if len(self.ecosystems) > 1:
            return "multiple ecosystems detected: " + ", ".join(self.ecosystems)
        if not self.proposals:
            return "supported repository metadata found, but no high-confidence check command was detected"
        return "detection was not usable"


def _detect_python(repo: Path) -> tuple[tuple[str, ...], tuple[StageProposal, ...]]:
    signals: list[str] = []
    proposals: list[StageProposal] = []
    pyproject = repo / "pyproject.toml"
    pytest_ini = repo / "pytest.ini"
    tox_ini = repo / "tox.ini"

    if pyproject.exists():
        signals.append("python: pyproject.toml")
    if pytest_ini.exists():
        signals.append("python: pytest.ini")
    if tox_ini.exists():
        signals.append("python: tox.ini")

    if tox_ini.exists():
        proposals.append(StageProposal("python", "tests", ("python", "-m", "tox"), "tox.ini"))
        return tuple(signals), tuple(proposals)

    if pytest_ini.exists():
        proposals.append(
            StageProposal("python", "tests", ("python", "-m", "pytest", "-q"), "pytest.ini")
        )
        return tuple(signals), tuple(proposals)

    if pyproject.exists():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            return tuple(signals), tuple(proposals)
        tool = data.get("tool", {})
        pytest_tool = tool.get("pytest", {}) if isinstance(tool, dict) else {}
        if isinstance(pytest_tool, dict) and isinstance(pytest_tool.get("ini_options"), dict):
            proposals.append(
                StageProposal(
                    "python",
                    "tests",
                    ("python", "-m", "pytest", "-q"),
                    "pyproject.toml [tool.pytest.ini_options]",
                )
            )
    return tuple(signals), tuple(proposals)


def _detect_node(repo: Path) -> tuple[tuple[str, ...], tuple[StageProposal, ...]]:
    package = repo / "package.json"
    if not package.exists():
        return (), ()

    signals = ("node: package.json",)
    try:
        data = json.loads(package.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return signals, ()
    if not isinstance(data, dict):
        return signals, ()

    manager = "npm"
    package_manager = data.get("packageManager")
    if isinstance(package_manager, str):
        declared = package_manager.split("@", 1)[0].strip().lower()
        if declared in {"npm", "pnpm", "yarn"}:
            manager = declared

    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return signals, ()

    proposals: list[StageProposal] = []
    for script, stage_name in (
        ("test", "tests"),
        ("lint", "lint"),
        ("typecheck", "typecheck"),
        ("build", "build"),
    ):
        value = scripts.get(script)
        if not isinstance(value, str) or not value.strip():
            continue
        if script == "test" and "no test specified" in value.lower():
            continue
        proposals.append(
            StageProposal(
                "node",
                stage_name,
                (manager, "run", script),
                f"package.json scripts.{script}",
            )
        )
    return signals, tuple(proposals)


def _detect_rust(repo: Path) -> tuple[tuple[str, ...], tuple[StageProposal, ...]]:
    if not (repo / "Cargo.toml").exists():
        return (), ()
    return ("rust: Cargo.toml",), (
        StageProposal("rust", "tests", ("cargo", "test"), "Cargo.toml"),
    )


def _detect_go(repo: Path) -> tuple[tuple[str, ...], tuple[StageProposal, ...]]:
    if not (repo / "go.mod").exists():
        return (), ()
    return ("go: go.mod",), (
        StageProposal("go", "tests", ("go", "test", "./..."), "go.mod"),
    )


def detect_stages(repo: Path) -> DetectionResult:
    signals: list[str] = []
    proposals: list[StageProposal] = []
    for detector in (_detect_python, _detect_node, _detect_rust, _detect_go):
        found_signals, found_proposals = detector(repo)
        signals.extend(found_signals)
        proposals.extend(found_proposals)
    return DetectionResult(tuple(signals), tuple(proposals))
