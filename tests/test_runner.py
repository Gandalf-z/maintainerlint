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

    def test_windows_style_crlf_output_is_sanitized(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            script = (
                "import sys; "
                "sys.stdout.write('ERROR: The system cannot find the path specified.\\r\\n' "
                "+ 'API_KEY=windows-secret\\r\\n')"
            )
            stage = Stage("windows-output", ("python", "-c", script))
            result = run_stage(stage, repo=repo, log_root=repo / ".maintainerlint" / "logs")
            self.assertTrue(result.passed)
            content = result.log_path.read_text()
            self.assertNotIn("windows-secret", content)
            self.assertIn("The system cannot find the path specified", content)
            self.assertIn("<REDACTED>", content)

    def test_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            stage = Stage("fail", ("python", "-c", "import sys; print('FAILED demo::case'); sys.exit(1)"))
            result = run_stage(stage, repo=repo, log_root=repo / ".maintainerlint" / "logs")
            self.assertFalse(result.passed)
            self.assertIn("FAILED demo::case", result.failure_summary)
