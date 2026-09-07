from pathlib import Path
import tempfile
import unittest

from maintainerlint.task import TaskError, load_task


class TaskContractTests(unittest.TestCase):
    def test_loads_minimal_contract_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.toml"
            path.write_text('version = 1\nallow = ["src/**"]\n', encoding="utf-8")
            task = load_task(path)
            self.assertEqual(task.base, "HEAD~1")
            self.assertEqual(task.head, "HEAD")
            self.assertEqual(task.allow, ("src/**",))
            self.assertEqual(task.support, ())
            self.assertEqual(task.targeted_stages, ())

    def test_loads_external_full_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "issue-167.toml"
            path.write_text(
                'version = 1\n'
                'base = "origin/main"\n'
                'head = "HEAD"\n'
                'allow = ["src/**", "tests/**"]\n'
                'support = ["docs/**"]\n'
                'targeted_stages = ["tests"]\n',
                encoding="utf-8",
            )
            task = load_task(path)
            self.assertEqual(task.base, "origin/main")
            self.assertEqual(task.support, ("docs/**",))
            self.assertEqual(task.targeted_stages, ("tests",))

    def test_rejects_unsupported_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.toml"
            path.write_text('version = 2\nallow = ["src/**"]\n', encoding="utf-8")
            with self.assertRaisesRegex(TaskError, "unsupported task contract version"):
                load_task(path)

    def test_rejects_empty_allow(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.toml"
            path.write_text("version = 1\nallow = []\n", encoding="utf-8")
            with self.assertRaisesRegex(TaskError, "allow must be"):
                load_task(path)

    def test_rejects_unknown_fields_to_catch_typos(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.toml"
            path.write_text(
                'version = 1\nallow = ["src/**"]\nallow_support = ["docs/**"]\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(TaskError, "unknown task field"):
                load_task(path)


if __name__ == "__main__":
    unittest.main()
