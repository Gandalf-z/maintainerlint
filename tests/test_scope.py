import unittest

from maintainerlint.gitutils import ChangeEntry
from maintainerlint.scope import evaluate_scope


class ScopeTests(unittest.TestCase):
    def test_allowed_only(self):
        result = evaluate_scope(
            (ChangeEntry("M", ("src/maintainerlint/cli.py",)),),
            ("src/**",),
        )
        self.assertTrue(result.satisfied)
        self.assertEqual(result.escaped_paths, ())

    def test_one_escaped_path(self):
        result = evaluate_scope(
            (
                ChangeEntry("M", ("src/maintainerlint/cli.py",)),
                ChangeEntry("M", ("scripts/unrelated.py",)),
            ),
            ("src/**",),
        )
        self.assertFalse(result.satisfied)
        self.assertEqual(result.escaped_paths, ("scripts/unrelated.py",))

    def test_rename_checks_both_old_and_new_paths(self):
        result = evaluate_scope(
            (ChangeEntry("R100", ("legacy/tool.py", "src/tool.py")),),
            ("src/**",),
        )
        self.assertEqual(result.escaped_paths, ("legacy/tool.py",))

    def test_delete_is_checked(self):
        result = evaluate_scope(
            (ChangeEntry("D", ("legacy/tool.py",)),),
            ("src/**",),
        )
        self.assertEqual(result.escaped_paths, ("legacy/tool.py",))

    def test_support_patterns_allow_docs_without_weakening_code_scope(self):
        result = evaluate_scope(
            (
                ChangeEntry("M", ("src/tool.py",)),
                ChangeEntry("M", ("docs/WORKFLOW.md",)),
                ChangeEntry("M", ("CHANGELOG.md",)),
            ),
            ("src/**",),
            ("docs/**", "CHANGELOG.md"),
        )
        self.assertTrue(result.satisfied)

    def test_empty_diff_passes(self):
        result = evaluate_scope((), ("src/**",))
        self.assertTrue(result.satisfied)


if __name__ == "__main__":
    unittest.main()