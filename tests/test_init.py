import argparse
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import tomllib
import unittest

from maintainerlint.cli import command_init


class InitTests(unittest.TestCase):
    def _args(self, directory: str, *, detect: bool, force: bool = False):
        return argparse.Namespace(
            directory=directory,
            detect=detect,
            force=force,
            pr_template=False,
        )

    def test_detected_proposal_is_printed_before_policy_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text(
                json.dumps({"scripts": {"test": "vitest"}}),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                self.assertEqual(command_init(self._args(tmp, detect=True)), 0)

            output = stream.getvalue()
            self.assertLess(output.index("PROPOSE node/tests"), output.index("CREATE "))
            config = tomllib.loads((repo / "maintainerlint.toml").read_text(encoding="utf-8"))
            self.assertEqual(config["stages"][0]["command"], ["npm", "run", "test"])
            self.assertEqual(config["stages"][-1]["command"], ["git", "diff", "--check"])

    def test_existing_policy_is_not_overwritten_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            config = repo / "maintainerlint.toml"
            config.write_text("do-not-replace\n", encoding="utf-8")
            (repo / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
            stream = StringIO()
            with redirect_stdout(stream):
                self.assertEqual(command_init(self._args(tmp, detect=True)), 0)
            self.assertEqual(config.read_text(encoding="utf-8"), "do-not-replace\n")
            self.assertIn("SKIP maintainerlint.toml already exists", stream.getvalue())

    def test_force_can_replace_existing_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            config = repo / "maintainerlint.toml"
            config.write_text("do-not-replace\n", encoding="utf-8")
            (repo / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(command_init(self._args(tmp, detect=True, force=True)), 0)
            parsed = tomllib.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(parsed["stages"][0]["command"], ["go", "test", "./..."])

    def test_ambiguous_repository_falls_back_to_generic_starter(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "Cargo.toml").write_text("[package]\nname = 'demo'\n", encoding="utf-8")
            (repo / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
            stream = StringIO()
            with redirect_stdout(stream):
                self.assertEqual(command_init(self._args(tmp, detect=True)), 0)
            output = stream.getvalue()
            self.assertIn("FALLBACK generic starter: multiple ecosystems detected", output)
            parsed = tomllib.loads((repo / "maintainerlint.toml").read_text(encoding="utf-8"))
            self.assertEqual(
                parsed["stages"][0]["command"],
                ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
            )


if __name__ == "__main__":
    unittest.main()
