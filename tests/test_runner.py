from pathlib import Path
import tempfile
import unittest

from maintainerlint.config import Stage
from maintainerlint.runner import run_stage


class RunnerTests(unittest.TestCase):
    def test_stage_writes_sanitized_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            stage = Stage("secret-test", ("python", "-c", "print('API_KEY=supersecret')"))
            result = run_stage(stage, repo=repo, log_root=repo / ".maintainerlint" / "logs")
            self.assertTrue(result.passed)
            content = result.log_path.read_text()
            self.assertNotIn("supersecret", content)
            self.assertIn("<REDACTED>", content)

    def test_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            stage = Stage("fail", ("python", "-c", "import sys; print('FAILED demo::case'); sys.exit(1)"))
            result = run_stage(stage, repo=repo, log_root=repo / ".maintainerlint" / "logs")
            self.assertFalse(result.passed)
            self.assertIn("FAILED demo::case", result.failure_summary)
