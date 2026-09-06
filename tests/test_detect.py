import json
from pathlib import Path
import tempfile
import unittest

from maintainerlint.detect import detect_stages


class DetectTests(unittest.TestCase):
    def test_python_pytest_config_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "pyproject.toml").write_text(
                "[tool.pytest.ini_options]\naddopts = '-q'\n",
                encoding="utf-8",
            )
            result = detect_stages(repo)
            self.assertTrue(result.usable)
            self.assertEqual(result.ecosystems, ("python",))
            self.assertEqual(result.proposals[0].command, ("python", "-m", "pytest", "-q"))

    def test_node_scripts_use_declared_package_manager(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text(
                json.dumps(
                    {
                        "packageManager": "pnpm@10.0.0",
                        "scripts": {"test": "vitest", "lint": "eslint ."},
                    }
                ),
                encoding="utf-8",
            )
            result = detect_stages(repo)
            self.assertTrue(result.usable)
            self.assertEqual(
                tuple(proposal.command for proposal in result.proposals),
                (("pnpm", "run", "test"), ("pnpm", "run", "lint")),
            )

    def test_node_default_placeholder_test_is_not_proposed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text(
                json.dumps({"scripts": {"test": "echo 'Error: no test specified' && exit 1"}}),
                encoding="utf-8",
            )
            result = detect_stages(repo)
            self.assertFalse(result.usable)
            self.assertEqual(result.proposals, ())

    def test_rust_cargo_test_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "Cargo.toml").write_text("[package]\nname = 'demo'\n", encoding="utf-8")
            result = detect_stages(repo)
            self.assertTrue(result.usable)
            self.assertEqual(result.proposals[0].command, ("cargo", "test"))

    def test_go_test_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
            result = detect_stages(repo)
            self.assertTrue(result.usable)
            self.assertEqual(result.proposals[0].command, ("go", "test", "./..."))

    def test_multiple_ecosystems_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "Cargo.toml").write_text("[package]\nname = 'demo'\n", encoding="utf-8")
            (repo / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
            result = detect_stages(repo)
            self.assertFalse(result.usable)
            self.assertIn("multiple ecosystems detected", result.fallback_reason)

    def test_empty_repository_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_stages(Path(tmp))
            self.assertFalse(result.usable)
            self.assertEqual(result.proposals, ())
            self.assertEqual(result.fallback_reason, "no supported repository signals found")


if __name__ == "__main__":
    unittest.main()
