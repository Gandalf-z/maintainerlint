import argparse
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from maintainerlint.cli import command_check, command_init, command_inspect


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)


def _config(command: list[str]) -> str:
    rendered = ", ".join(json.dumps(item) for item in command)
    return (
        "version = 1\n\n"
        "[[stages]]\n"
        'name = "trial"\n'
        f"command = [{rendered}]\n"
        "timeout = 60\n"
    )


class ShadowModeTests(unittest.TestCase):
    def test_init_detect_dry_run_writes_nothing_and_prints_exact_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text(
                json.dumps({"scripts": {"test": "vitest"}}),
                encoding="utf-8",
            )
            before = _snapshot(repo)
            args = argparse.Namespace(
                directory=str(repo),
                detect=True,
                force=False,
                dry_run=True,
                pr_template=True,
            )
            stream = StringIO()
            with redirect_stdout(stream):
                self.assertEqual(command_init(args), 0)

            output = stream.getvalue()
            self.assertEqual(_snapshot(repo), before)
            self.assertFalse((repo / "maintainerlint.toml").exists())
            self.assertFalse((repo / ".github").exists())
            self.assertIn("PROPOSE node/tests", output)
            self.assertIn("POLICY BEGIN maintainerlint.toml", output)
            self.assertIn('command = ["npm", "run", "test"]', output)
            self.assertIn("WOULD CREATE", output)
            self.assertIn("ZERO-WRITE dry-run", output)

    def test_dry_run_force_never_replaces_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "maintainerlint.toml").write_text("keep-me\n", encoding="utf-8")
            (repo / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
            before = _snapshot(repo)
            args = argparse.Namespace(
                directory=str(repo),
                detect=True,
                force=True,
                dry_run=True,
                pr_template=False,
            )
            stream = StringIO()
            with redirect_stdout(stream):
                self.assertEqual(command_init(args), 0)

            self.assertEqual(_snapshot(repo), before)
            self.assertEqual((repo / "maintainerlint.toml").read_text(), "keep-me\n")
            self.assertIn("WOULD REPLACE", stream.getvalue())

    def test_inspect_is_zero_write_and_does_not_execute_proposed_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git_init(repo)
            marker = repo / "should-not-exist"
            (repo / "package.json").write_text(
                json.dumps({"scripts": {"test": f"{sys.executable} -c \"open('should-not-exist','w').write('x')\""}}),
                encoding="utf-8",
            )
            before = _snapshot(repo)
            stream = StringIO()
            with redirect_stdout(stream):
                self.assertEqual(command_inspect(argparse.Namespace(repo=str(repo))), 0)

            output = stream.getvalue()
            self.assertEqual(_snapshot(repo), before)
            self.assertFalse(marker.exists())
            self.assertIn("INSPECT repository:", output)
            self.assertIn("PROPOSE node/tests", output)
            self.assertIn("POLICY BEGIN maintainerlint.toml", output)
            self.assertIn("ADOPT init --detect would create maintainerlint.toml", output)
            self.assertIn("ZERO-WRITE inspect", output)

    def test_check_accepts_external_config_and_routes_logs_to_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            _git_init(repo)
            external = root / "external"
            external.mkdir()
            config = external / "policy.toml"
            config.write_text(
                _config([sys.executable, "-c", "print('ok')"]),
                encoding="utf-8",
            )
            state_dir = external / "state"
            args = argparse.Namespace(
                repo=str(repo),
                config=str(config),
                stage=None,
                state_dir=str(state_dir),
                log_dir=None,
            )
            with redirect_stdout(StringIO()):
                self.assertEqual(command_check(args), 0)

            logs = list((state_dir / "logs").glob("*.log"))
            self.assertEqual(len(logs), 1)
            self.assertFalse((repo / ".maintainerlint").exists())

    def test_log_dir_overrides_state_dir_and_failure_path_renders_externally(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            _git_init(repo)
            config = root / "policy.toml"
            config.write_text(
                _config([sys.executable, "-c", "import sys; print('FAILED shadow::case'); sys.exit(1)"]),
                encoding="utf-8",
            )
            state_dir = root / "unused-state"
            log_dir = root / "logs-direct"
            args = argparse.Namespace(
                repo=str(repo),
                config=str(config),
                stage=None,
                state_dir=str(state_dir),
                log_dir=str(log_dir),
            )
            stream = StringIO()
            with redirect_stdout(stream):
                self.assertEqual(command_check(args), 1)

            logs = list(log_dir.glob("*.log"))
            output = stream.getvalue()
            self.assertEqual(len(logs), 1)
            self.assertFalse(state_dir.exists())
            self.assertFalse((repo / ".maintainerlint").exists())
            self.assertIn("  log: ", output)
            self.assertIn(log_dir.name, output)
            self.assertIn(".log", output)
            self.assertIn("FAILED shadow::case", output)


if __name__ == "__main__":
    unittest.main()
