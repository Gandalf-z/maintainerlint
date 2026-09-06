import unittest

from maintainerlint.config import DocRule
from maintainerlint.impact import evaluate_rules


class ImpactTests(unittest.TestCase):
    def test_rule_requires_one_document(self):
        rule = DocRule("cli", ("src/**",), ("README.md", "docs/CLI.md"), ())
        result = evaluate_rules(("src/maintainerlint/cli.py",), (rule,))[0]
        self.assertFalse(result.satisfied)
        result = evaluate_rules(("src/maintainerlint/cli.py", "docs/CLI.md"), (rule,))[0]
        self.assertTrue(result.satisfied)

    def test_required_all(self):
        rule = DocRule("contract", ("src/api/**",), (), ("docs/API.md", "CHANGELOG.md"))
        result = evaluate_rules(("src/api/client.py", "docs/API.md"), (rule,))[0]
        self.assertEqual(result.missing_all, ("CHANGELOG.md",))
