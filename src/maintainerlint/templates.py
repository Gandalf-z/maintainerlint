from __future__ import annotations

import json

from .detect import StageProposal


_CONFIG_TAIL = '''# Documentation rules are opt-in and project-specific.
# A rule triggers when any `patterns` path changes.
# - required_any: at least one listed document must change.
# - required_all: every listed document must change.
[docs]

# Example:
# [[docs.rules]]
# name = "public CLI contract"
# patterns = ["src/myproject/cli.py", "src/myproject/config.py"]
# required_any = ["README.md", "docs/CLI.md"]

[security]
tracked_secret_allowlist = [".env.example"]
'''

DEFAULT_CONFIG = '''# MaintainerLint configuration
version = 1

# Each stage runs in order. MaintainerLint keeps full sanitized logs locally and
# prints only concise PASS/FAIL output unless a stage fails.
[[stages]]
name = "tests"
command = ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
timeout = 300

[[stages]]
name = "diff"
command = ["git", "diff", "--check"]
timeout = 60

''' + _CONFIG_TAIL


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_detected_config(proposals: tuple[StageProposal, ...]) -> str:
    if not proposals:
        return DEFAULT_CONFIG

    lines = [
        "# MaintainerLint configuration",
        "version = 1",
        "",
        "# Detected stages are conservative proposals derived from repository files.",
        "# Review these commands before committing this policy.",
    ]
    for proposal in proposals:
        lines.extend(
            [
                "",
                f"# detected from {proposal.reason}",
                "[[stages]]",
                f"name = {_toml_string(proposal.name)}",
                "command = [" + ", ".join(_toml_string(item) for item in proposal.command) + "]",
                "timeout = 300",
            ]
        )
    lines.extend(
        [
            "",
            "[[stages]]",
            'name = "diff"',
            'command = ["git", "diff", "--check"]',
            "timeout = 60",
            "",
        ]
    )
    return "\n".join(lines) + _CONFIG_TAIL


PR_TEMPLATE = '''## Scope

<!-- What does this PR change, and what is explicitly out of scope? -->

## Verification

- [ ] Targeted tests passed
- [ ] `maintainerlint check` passed
- [ ] `git diff --check` passed

## Documentation impact

- [ ] No documentation impact
- [ ] Current-state / architecture docs
- [ ] API / contract docs
- [ ] User docs
- [ ] Design / decision lifecycle docs

**Documentation drift review:** Does this PR make code/config/tests disagree with current-truth documentation?

## Human verification

<!-- List any real-environment checks that should remain human-owned. -->
'''
