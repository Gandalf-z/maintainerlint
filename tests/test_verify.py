import argparse
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from maintainerlint.cli import command_scope, command_verify
from maintainerlint.task import TaskError


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _prepare_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "src").mkdir()
    (repo / "src" / "feature.py").write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "baseline")
    (repo / "src" / "feature.py").write_text("value = 2\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "change")
    return repo


def _write_config(path: Path, *, docs_rule: bool = False) -> None:
    text = (
        "version = 1\n\n"
        "[[stages]]\n"
        'name = "tests"\n'
        f"command = [{json.dumps(sys.executable)}, \"-c\", \"print('tests ok')\"]\n"
        "timeout = 60\n\n"
        "[[stages]]\n"
        'name = "diff"\n'
        'command = ["git", "diff", "--check"]\n'
        "timeout = 60\n"
    )
    if docs_rule:
        text += (
            "\n[docs]\n\n"
            "[[docs.rules]]\n"
            'name = "feature docs"\n'
            'patterns = ["src/**"]\n'
            'required_any = ["README.md"]\n'
        )
    path.write_text(text, encoding="utf-8")


def _write_task(path: Path, *, targeted: str = "tests") -> None:
    path.write_text(
        "version = 1\n"
        'base = "HEAD~1"\n'
        'head = "HEAD"\n'
        'allow = ["src/**"]\n'
        'support = ["docs/**", "CHANGELOG.md"]\n'
        f'targeted_stages = ["{targeted}"]\n',
        encoding="utf-8",
    )


class VerificationTests(unittest.TestCase):
    def test_scope_task_matches_equivalent_cli_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _prepare_repo(root)
            task = root / "task.toml"
            _write_task(task)

            with redirect_stdout(StringIO()):
                task_code = command_scope(
                    argparse.Namespace(
                        repo=str(repo), task=str(task), base=None, head=None,
                        allow=None, allow_support=None, strict=True,
                    )
                )
                cli_code = command_scope(
                    argparse.Namespace(
                        repo=str(repo), task=None, base="HEAD~1", head="HEAD",
                        allow=["src/**"], allow_support=["docs/**", "CHANGELOG.md"], strict=True,
                    )
                )
            self.assertEqual(task_code, 0)
            self.assertEqual(cli_code, 0)

    def test_scope_rejects_task_mixed_with_cli_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _prepare_repo(root)
            task = root / "task.toml"
            _write_task(task)
            with self.assertRaisesRegex(TaskError, "cannot be combined"):
                command_scope(
                    argparse.Namespace(
                        repo=str(repo), task=str(task), base=None, head=None,
                        allow=["src/**"], allow_support=None, strict=True,
                    )
                )

    def test_verify_passes_and_keeps_owned_logs_outside_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _prepare_repo(root)
            config = root / "policy.toml"
            task = root / "issue-167.toml"
            state = root / "state"
            _write_config(config)
            _write_task(task)

            stream = StringIO()
            with redirect_stdout(stream):
                code = command_verify(
                    argparse.Namespace(
                        repo=str(repo), task=str(task), config=str(config),
                        state_dir=str(state), log_dir=None, format="text",
                    )
                )

            self.assertEqual(code, 0)
            self.assertTrue(stream.getvalue().rstrip().endswith(
                "PASS scope\nPASS checks\nPASS docs\nPASS safety"
            ))
            self.assertFalse((repo / ".maintainerlint").exists())
            self.assertEqual(len(list((state / "logs").glob("*.log"))), 3)

    def test_verify_json_has_versioned_stable_section_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _prepare_repo(root)
            config = root / "policy.toml"
            task = root / "task.toml"
            _write_config(config)
            _write_task(task)

            stream = StringIO()
            with redirect_stdout(stream):
                code = command_verify(
                    argparse.Namespace(
                        repo=str(repo), task=str(task), config=str(config),
                        state_dir=str(root / "state"), log_dir=None, format="json",
                    )
                )
            self.assertEqual(code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["schema"], "maintainerlint.verify")
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(
                {name: section["status"] for name, section in payload["sections"].items()},
                {"scope": "pass", "checks": "pass", "docs": "pass", "safety": "pass"},
            )
            self.assertEqual(payload["task"]["targeted_stages"], ["tests"])

    def test_verify_aggregates_docs_failure_without_hiding_other_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _prepare_repo(root)
            config = root / "policy.toml"
            task = root / "task.toml"
            _write_config(config, docs_rule=True)
            _write_task(task)

            stream = StringIO()
            with redirect_stdout(stream):
                code = command_verify(
                    argparse.Namespace(
                        repo=str(repo), task=str(task), config=str(config),
                        state_dir=str(root / "state"), log_dir=None, format="text",
                    )
                )
            self.assertEqual(code, 1)
            output = stream.getvalue()
            self.assertIn("DETAIL docs", output)
            self.assertTrue(output.rstrip().endswith(
                "PASS scope\nPASS checks\nFAIL docs\nPASS safety"
            ))

    def test_verify_unknown_targeted_stage_fails_checks_clearly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _prepare_repo(root)
            config = root / "policy.toml"
            task = root / "task.toml"
            _write_config(config)
            _write_task(task, targeted="missing")

            stream = StringIO()
            with redirect_stdout(stream):
                code = command_verify(
                    argparse.Namespace(
                        repo=str(repo), task=str(task), config=str(config),
                        state_dir=str(root / "state"), log_dir=None, format="text",
                    )
                )
            self.assertEqual(code, 1)
            output = stream.getvalue()
            self.assertIn("ERROR unknown stage(s): missing", output)
            self.assertIn("FAIL checks", output)


if __name__ == "__main__":
    unittest.main()
