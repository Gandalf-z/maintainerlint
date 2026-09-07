# MaintainerLint

**Deterministic guardrails for AI-assisted software maintenance.**

MaintainerLint is a small, agent-agnostic CLI for maintainers who use coding agents but still want changes to remain bounded, reviewable, testable, documented, and human-owned.

It does **not** call an LLM. It sits around your existing tools—Codex, Claude Code, Copilot, local agents, or humans—and turns maintenance policy into deterministic repository evidence.

## Why MaintainerLint?

AI coding agents can produce code quickly. Maintainers still need deterministic answers to questions such as:

- Did the agent stay inside the approved task scope?
- Did targeted and repository-wide checks actually run?
- Did a code/config change make current documentation stale?
- Are failure logs safe to retain and share with an agent?
- Is a secret-like file accidentally tracked?
- Which acceptance decisions must remain human-owned?

MaintainerLint focuses on the parts that can be checked reproducibly.

## What MaintainerLint is not

MaintainerLint is intentionally narrow:

- it is **not an AI code reviewer** and does not score semantic correctness;
- it is **not an agent orchestrator** and does not assign work or run autonomous merge loops;
- it is **not a secret scanner replacement**; `doctor` catches only a small set of high-confidence mistakes;
- it does **not** sandbox repository test/build/lint commands;
- it is **not an autonomous merge bot**.

## Shadow-first adoption

Before allowing MaintainerLint to write anything into an existing repository, inspect what it understands:

```bash
maintainerlint inspect --repo /path/to/project
```

`inspect` prints supported ecosystem signals, proposed commands, the exact suggested TOML policy, and the files formal adoption would create. It does **not** create or modify target files, execute detected commands, install dependencies, call an LLM, or access the network.

Preview the initializer itself without writes:

```bash
cd /path/to/project
maintainerlint init --detect --dry-run
```

Only after review, adopt the policy:

```bash
maintainerlint init --detect --pr-template
```

This guarantee is deliberately called **MaintainerLint-owned zero-write**. MaintainerLint can keep its own files/state out of the repository; user-configured test/build/lint commands may still generate files when they are actually executed.

## Low-output verification gates

Define the repository's trusted checks once in `maintainerlint.toml`:

```toml
version = 1

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

On failure, MaintainerLint prints a bounded sanitized tail and stores the complete sanitized log under `.maintainerlint/logs/` by default.

To keep MaintainerLint-owned state outside the target repository:

```bash
maintainerlint check \
  --repo /path/to/project \
  --config /tmp/project.toml \
  --state-dir ~/.cache/maintainerlint/project
```

`--state-dir DIR` stores logs under `DIR/logs/`. `--log-dir DIR` overrides the log directory directly.

## Task Contract v1

Long `scope --allow ...` invocations are useful for one-off checks, but an agent task should have one explicit boundary source. A Task Contract makes that boundary portable and reviewable.

Example `/tmp/issue-167.toml`:

```toml
version = 1
base = "origin/main"
head = "HEAD"
allow = [
  "src/feature/**",
  "tests/feature/**",
]
support = [
  "docs/**",
  "CHANGELOG.md",
]
targeted_stages = ["tests"]
```

Fields:

- `version`: must be `1`;
- `base`: Git diff base, default `HEAD~1`;
- `head`: Git diff head, default `HEAD`;
- `allow`: required non-empty primary scope patterns;
- `support`: optional supporting-file patterns;
- `targeted_stages`: optional names of existing `maintainerlint.toml` stages to run before the full gate in `verify`.

Task files may live inside the repository or at an absolute external path such as `/tmp/issue-167.toml`.

Use the contract directly with the existing scope gate:

```bash
maintainerlint scope \
  --repo /path/to/project \
  --task /tmp/issue-167.toml \
  --strict
```

The existing explicit CLI form remains supported:

```bash
maintainerlint scope \
  --base origin/main \
  --head HEAD \
  --allow "src/feature/**" \
  --allow "tests/feature/**" \
  --allow-support "docs/**" \
  --strict
```

`--task` cannot be mixed with `--base`, `--head`, `--allow`, or `--allow-support`; one verification run has one source of scope truth. Unknown Task Contract keys are rejected so typos do not silently weaken the boundary.

Renames check both old and new paths, deletes check the deleted path, and copies check the destination path.

## One final Agent Verification command

At task completion, an agent no longer needs to remember a sequence of separate MaintainerLint commands:

```bash
maintainerlint verify \
  --repo /path/to/project \
  --task /tmp/issue-167.toml \
  --config /tmp/project.toml \
  --state-dir ~/.cache/maintainerlint/project
```

`verify` does **not** invent new gate semantics. It composes the existing commands in this order:

1. strict task scope;
2. optional `targeted_stages` from the Task Contract;
3. full configured `maintainerlint check`;
4. strict documentation impact using the task `base/head`;
5. `maintainerlint doctor` safety checks.

A successful text result ends with:

```text
PASS scope
PASS checks
PASS docs
PASS safety
```

Only failing sections print detailed underlying command evidence before the summary. This keeps successful agent handoffs small while leaving failures actionable.

For tool/agent integrations:

```bash
maintainerlint verify ... --format json
```

JSON uses the explicit `maintainerlint.verify` schema with `schema_version = 1`, overall status, task metadata, and stable `scope/checks/docs/safety` section statuses. Consumers should use the status fields rather than parsing human-readable section output.

When `targeted_stages` are configured, those stages intentionally run before the complete `check` gate even if the full gate contains the same stage. MaintainerLint preserves each execution in a unique sanitized log file.

## Documentation-drift gates

Declare current-truth documents that must be reconsidered when specific contracts change:

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

The same result can also be rendered for a PR or another tool:

```bash
maintainerlint impact --base origin/main --head HEAD --strict --format markdown
maintainerlint impact --base origin/main --head HEAD --strict --format json
```

`json` uses the versioned `maintainerlint.impact` schema. Text, Markdown, and JSON render one shared result model, so output format does not change strict semantics.

## Maintainer safety checks

```bash
maintainerlint doctor
```

Current checks include:

- Git is available;
- MaintainerLint config is valid;
- high-confidence secret-like tracked files such as `.env`, private keys, or `credentials.json` are not tracked.

## Installation and release status

MaintainerLint requires Python 3.11+ and has **zero third-party runtime dependencies**.

`v0.2.0` is the first tagged public GitHub Release. It contains the tagged baseline through conservative brownfield detection, scope/documentation gates, machine-readable impact output, and Windows CI verification.

The shadow-mode (`inspect`, `init --dry-run`, external state routing), Task Contract, and unified `verify` workflow were developed **after** the `v0.2.0` tag and are current-main / next-release capabilities. Do not install `v0.2.0` expecting those later commands.

Install the tagged v0.2.0 baseline:

```bash
python -m pip install "https://github.com/Gandalf-z/maintainerlint/archive/refs/tags/v0.2.0.zip"
```

For development or evaluation of current `main` capabilities:

```bash
git clone https://github.com/Gandalf-z/maintainerlint.git
cd maintainerlint
python -m pip install -e .
maintainerlint --version
```

A new tagged release should be cut only after the current-main shadow/task/verify workflow has passed maintainer acceptance.

## Recommended agent workflow

```text
Issue / bug report
      ↓
Planner defines Task Contract
      ↓
Agent implements the approved delta
      ↓
Agent runs targeted local checks while working
      ↓
maintainerlint verify --task /path/task.toml ...
      ↓
PASS scope / checks / docs / safety
      ↓
Pull request
      ↓
Human review / real-environment acceptance
      ↓
Merge
```

The key idea is simple: **agents may propose and implement; deterministic repository gates establish evidence; maintainers own acceptance and merge.**

See [docs/WORKFLOW.md](docs/WORKFLOW.md) and [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the complete contracts.

## CI example

Repository-wide CI can keep using independent gates:

```yaml
- name: MaintainerLint quality gate
  run: maintainerlint check

- name: Documentation drift gate
  if: github.event_name == 'pull_request'
  run: maintainerlint impact --base "${{ github.event.pull_request.base.sha }}" --head "${{ github.sha }}" --strict
```

For task-specific agent completion, prefer a reviewed Task Contract plus `maintainerlint verify` instead of an overly broad global scope allowlist.

## Design principles

- **Agent-agnostic.** No dependency on a specific AI vendor.
- **Deterministic first.** Automate what can be checked reproducibly.
- **One source of task truth.** Task scope should not be duplicated across agent prompts and CLI flags.
- **Low-output by default.** Successful verification should not burn agent context.
- **Fail clearly, not silently.** Missing or contradictory evidence stays visible.
- **Human gates stay human.** Real-device, UX, release, security-risk, and product acceptance are not faked by CI.
- **Repository truth beats chat memory.** Code, tests, config, Git history, and current-state docs are durable evidence.
- **No secret leakage for convenience.** Logs are sanitized before persistence or printing.
- **Shadow before adoption.** Maintainers should be able to inspect policy without target-repository writes.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and small, well-scoped pull requests are welcome.

## Security

See [SECURITY.md](SECURITY.md) for threat boundaries and reporting guidance.

## License

Apache-2.0.
