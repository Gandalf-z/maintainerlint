import argparse
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from maintainerlint.config import DocRule
from maintainerlint.impact import (
    IMPACT_SCHEMA,
    IMPACT_SCHEMA_VERSION,
    build_report,
    evaluate_rules,
    render_report,
)


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

    def test_formats_cover_satisfied_unsatisfied_and_no_trigger(self):
        rule = DocRule("api", ("src/api/**",), ("docs/API.md",), ())
        cases = {
            "satisfied": build_report(("src/api/client.py", "docs/API.md"), (rule,)),
            "unsatisfied": build_report(("src/api/client.py",), (rule,)),
            "no-trigger": build_report(("docs/API.md",), (rule,)),
        }

        for format_name in ("text", "markdown", "json"):
            for case_name, report in cases.items():
                with self.subTest(format=format_name, case=case_name):
                    rendered = render_report(report, format_name)
                    if format_name == "json":
                        payload = json.loads(rendered)
                        self.assertEqual(payload["status"], report.status)
                        self.assertEqual(len(payload["rules"]), len(report.rules))
                    elif case_name == "unsatisfied":
                        self.assertIn("FAIL", rendered)
                    else:
                        self.assertIn("PASS", rendered)

    def test_json_schema_is_explicit_and_stable(self):
        rule = DocRule("api", ("src/api/**",), ("docs/API.md",), ())
        payload = json.loads(render_report(build_report(("src/api/client.py",), (rule,)), "json"))
        self.assertEqual(payload["schema"], IMPACT_SCHEMA)
        self.assertEqual(payload["schema_version"], IMPACT_SCHEMA_VERSION)
        self.assertEqual(payload["summary"], {"triggered_rules": 1, "failed_rules": 1})
        self.assertEqual(payload["rules"][0]["status"], "fail")

    def test_no_trigger_output_is_concise(self):
        rule = DocRule("api", ("src/api/**",), ("docs/API.md",), ())
        report = build_report(("README.md",), (rule,))
        self.assertEqual(
            render_report(report, "text"),
            "PASS documentation impact: no configured rules triggered",
        )
        self.assertIn(
            "no configured documentation-impact rules triggered",
            render_report(report, "markdown"),
        )
        self.assertEqual(json.loads(render_report(report, "json"))["rules"], [])

    def test_strict_exit_is_nonzero_for_unsatisfied_report_in_every_format(self):
        from maintainerlint.cli import command_impact

        rule = DocRule("api", ("src/api/**",), ("docs/API.md",), ())
        config = type("Config", (), {"doc_rules": (rule,)})()

        for format_name in ("text", "markdown", "json"):
            args = argparse.Namespace(
                repo=None,
                config="maintainerlint.toml",
                base="HEAD~1",
                head="HEAD",
                changed=["src/api/client.py"],
                strict=True,
                format=format_name,
            )
            with self.subTest(format=format_name), \
                 patch("maintainerlint.cli._resolve_repo", return_value=Path(".")), \
                 patch("maintainerlint.cli.load_config", return_value=config), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(command_impact(args), 1)
