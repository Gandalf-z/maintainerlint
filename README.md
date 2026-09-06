# MaintainerLint

**Deterministic guardrails for AI-assisted software maintenance.**

MaintainerLint is a small, agent-agnostic CLI for maintainers who use coding agents but still want changes to remain bounded, reviewable, testable, documented, and human-owned.

It does **not** call an LLM. It sits around your existing tools—Codex, Claude Code, Copilot, local agents, or humans—and turns maintenance policy into deterministic checks.

## Why MaintainerLint?

AI coding agents can produce a lot of code quickly. Maintainers still have to answer harder questions:

- Did the agent stay inside the approved scope?
- Did the relevant tests actually run?
- Are failure logs safe to paste into an issue or agent session?
- Did a code/config change make the current documentation stale?
- Is a secret-like file accidentally tracked?
- Which checks should remain human-owned instead of being automated away?

MaintainerLint starts with the parts that can be made deterministic.

## What MaintainerLint is not

MaintainerLint is intentionally narrow:

- it is **not an AI code reviewer** and does not score whether a patch is semantically correct;
- it is **not an agent orchestrator** and does not assign work or run autonomous merge loops;
- it is **not a CI failure classifier**; it executes the checks your repository already trusts;
- it is **not a secret scanner replacement**; `doctor` only catches a small set of high-confidence tracked-file mistakes;
- it is **not an autonomous merge bot**.

Its job is repository policy: make the maintainer's existing quality, documentation, and safety expectations cheap for humans and coding agents to follow consistently.

## Current capabilities

### 1. Low-output verification gates

Define your normal checks once in `maintainerlint.toml`:

```toml
[[stages]]
name = "tests"
command = ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]

[[stages]]
name = "diff"
command = ["git", "diff", "--check"]
```

Then run:

```bash
maintainerlint check
```

Successful stages stay concise:

```text
PASS tests (0.4s)
PASS diff (0.0s)
```

On failure, MaintainerLint prints a bounded sanitized tail and stores the complete **sanitized** log under `.maintainerlint/logs/`.

### 2. Documentation-drift gates

Declare which source-of-truth documents must be reconsidered when specific contracts change:

```toml
[docs]

[[docs.rules]]
name = "public CLI contract"
patterns = ["src/myproject/cli.py", "src/myproject/config.py"]
required_any = ["README.md", "docs/CLI.md"]
```

Then:

```bash
maintainerlint impact --base origin/main --head HEAD --strict
```

If the CLI changes without either document changing, CI fails with an actionable explanation.

The exact same documentation-impact result can also be rendered for a PR or another tool:

```bash
maintainerlint impact --base origin/main --head HEAD --strict --format markdown
maintainerlint impact --base origin/main --head HEAD --strict --format json
```

`markdown` produces a PR/check-summary-friendly report. `json` uses the stable `maintainerlint.impact` schema with explicit `schema_version = 1`. Text, Markdown, and JSON all render one shared result model, so changing output format never changes `--strict` semantics. See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the JSON field contract.

### 3. Maintainer safety checks

```bash
maintainerlint doctor
```

The first release checks:

- Git is available;
- MaintainerLint config is valid;
- high-confidence secret-like files such as `.env`, private keys, or `credentials.json` are not tracked.

### 4. Changed-file scope guard

Declare the paths an implementation task is allowed to modify:

```bash
maintainerlint scope \
  --base origin/main \
  --head HEAD \
  --allow "src/payments/**" \
  --allow "tests/payments/**" \
  --allow-support "docs/**" \
  --allow-support "CHANGELOG.md" \
  --strict
```

`--allow` is the primary implementation boundary. `--allow-support` is for supporting artifacts such as documentation or changelog entries; it does **not** bypass `maintainerlint impact`.

In strict mode, an unexpected changed path exits non-zero and is listed explicitly. Renames check both the old and new path, deletions check the deleted path, and copies check the destination path.

### 5. Safe starter setup

```bash
maintainerlint init --pr-template
```

This creates a minimal `maintainerlint.toml` and an optional PR template that asks for scope, verification, documentation impact, documentation-drift review, and human verification.

## Install from source

MaintainerLint currently requires Python 3.11+.

```bash
git clone https://github.com/Gandalf-z/maintainerlint.git
cd maintainerlint
python -m pip install -e .
maintainerlint --version
```

The runtime has **zero third-party dependencies**.

## Recommended agent workflow

MaintainerLint is deliberately compatible with many coding agents. A practical workflow is:

```text
Issue / bug report
      ↓
Repository audit + scoped implementation plan
      ↓
Agent executes only the approved change
      ↓
maintainerlint scope --strict
      ↓
Targeted tests
      ↓
maintainerlint check
      ↓
maintainerlint impact --strict
      ↓
Pull request
      ↓
Human review / real-environment acceptance
      ↓
Merge
```

The key idea is simple: **agents may propose and implement; repository truth is established by deterministic checks and maintainer review.**

See [docs/WORKFLOW.md](docs/WORKFLOW.md) for the full model.

## CI example

```yaml
- name: MaintainerLint quality gate
  run: maintainerlint check

- name: Documentation drift gate
  if: github.event_name == 'pull_request'
  run: maintainerlint impact --base "${{ github.event.pull_request.base.sha }}" --head "${{ github.sha }}" --strict
```

For task-specific jobs, add a scope gate with the task's explicit allow patterns. Do not use one overly broad repository-wide allowlist merely to make the check green.

The repository itself uses MaintainerLint in CI.

## Design principles

- **Agent-agnostic.** No dependency on a specific AI vendor.
- **Deterministic first.** Automate what can be checked reproducibly.
- **Low-output by default.** Agents should not burn context on successful test logs.
- **Fail clearly, not silently.** Missing evidence should remain missing.
- **Human gates stay human.** Real-device, UX, release, or safety acceptance is not faked by CI.
- **Repository truth beats chat memory.** Code, tests, configuration, Git history, and current-state docs are the durable record.
- **No secret leakage for convenience.** Logs are sanitized before they are saved or printed.

## Project status

`v0.1.0` is the initial public baseline. New deterministic gates are developed through focused Issues and PRs and recorded in [CHANGELOG.md](CHANGELOG.md) and [docs/ROADMAP.md](docs/ROADMAP.md).

Good first contributions include deterministic checks, repository adoption improvements, machine-readable reports, and CI adapters.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and small, well-scoped pull requests are welcome.

## Security

MaintainerLint processes command output locally. See [SECURITY.md](SECURITY.md) for threat boundaries and reporting guidance.

## License

Apache-2.0.
