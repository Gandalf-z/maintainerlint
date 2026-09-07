# Maintainer workflow

MaintainerLint is built around a separation of responsibilities rather than a specific AI tool.

## Roles

### 1. Planner / reviewer

Before code changes, establish:

- the user or maintainer problem;
- current repository facts;
- what is already implemented;
- the smallest acceptable scope;
- files and contracts likely to change;
- tests that prove the change;
- what must remain human-verified;
- explicit stop conditions.

The planner can be a maintainer, ChatGPT, another model, or a human team member.

### 2. Execution agent

The execution agent should receive a bounded implementation packet and be asked to:

- read only task-relevant code and docs;
- implement the approved delta;
- run targeted tests;
- run the repository quality gate;
- inspect the final diff;
- open a PR;
- stop before merge unless the maintainer explicitly owns that action.

The execution role should not silently redesign the product or expand the issue.

### 3. Deterministic repository gates

MaintainerLint lives here. It does not judge product intent. It checks repository evidence such as:

- configured test/build/lint commands;
- `git diff --check` or other hygiene stages;
- changed-file scope boundaries declared by the maintainer;
- sanitized failure output;
- configured documentation-impact rules;
- high-confidence tracked-secret risks.

### 4. Human acceptance

Some checks are intentionally not automated:

- UI quality;
- real-device or real-OS behavior;
- production rollout decisions;
- destructive migrations;
- legal/compliance judgment;
- security-risk acceptance;
- whether the original user problem is actually solved.

A green CI run is evidence, not a substitute for maintainer responsibility.

## Shadow-first adoption

A maintainer should be able to understand what MaintainerLint wants to do before allowing it to write into an existing repository.

Start with:

```bash
maintainerlint inspect --repo /path/to/project
```

This is a read-only MaintainerLint operation: it detects supported ecosystem signals, prints proposed commands and policy, and explains what `init --detect` would create. It does not execute the proposed repository commands.

The initializer can be previewed independently:

```bash
cd /path/to/project
maintainerlint init --detect --dry-run
```

Only after the maintainer accepts the proposal should formal adoption create `maintainerlint.toml` or an optional PR template.

For a shadow `check`, keep MaintainerLint-owned logs outside the repository:

```bash
maintainerlint check \
  --repo /path/to/project \
  --config /tmp/project.toml \
  --state-dir ~/.cache/maintainerlint/project
```

This boundary is intentionally precise. MaintainerLint can make its **own** state/log writes external; the configured test/build/lint commands are still real repository commands and may write generated files. Treat those commands as executable policy and review them before running `check`.

## A compact implementation packet

A good agent packet should contain only what execution needs:

```text
Goal
Repository facts
Approved scope
Files / contracts to change
Do not change
Implementation steps
Targeted tests
MaintainerLint gates
Human acceptance checklist
Stop condition
```

This structure reduces exploratory token use and keeps the implementation auditable.

## Changed-file scope guard

For tasks with a known file boundary, encode that boundary in the final verification step:

```bash
maintainerlint scope \
  --base origin/main \
  --head HEAD \
  --allow "src/feature/**" \
  --allow "tests/feature/**" \
  --allow-support "docs/**" \
  --allow-support "CHANGELOG.md" \
  --strict
```

Use `--allow` for the primary implementation area. Use `--allow-support` for supporting artifacts that are expected to change alongside the implementation. Supporting paths are still evaluated independently by documentation-impact rules; scope permission is not documentation permission.

The guard is intentionally structural rather than semantic:

- modified/added/deleted paths must be inside the declared boundary;
- renames require both the old and new path to be allowed;
- copies require the destination path to be allowed because the source is not modified;
- an empty diff passes;
- `--strict` turns escaped paths into a non-zero exit status.

Do not use the scope guard when the task is genuinely exploratory or when the expected path boundary cannot be stated honestly. A fake broad allowlist is worse than omitting the guard and documenting why.

## Current truth and documentation drift

Long-lived projects often have multiple documents describing the same system. MaintainerLint recommends identifying a small set of current-truth documents, then using `docs.rules` to force reconsideration when contracts change.

Do not require a changelog update for every internal bug fix. Configure rules only where stale documentation would materially mislead maintainers or users.

## PR-readable and machine-readable evidence

Documentation-impact rules are evaluated once into one report. Choose the rendering that fits the next consumer:

```bash
# concise terminal output
maintainerlint impact --base origin/main --head HEAD --strict

# paste into a PR comment or check summary
maintainerlint impact --base origin/main --head HEAD --strict --format markdown

# feed deterministic evidence to another tool or agent
maintainerlint impact --base origin/main --head HEAD --strict --format json
```

Markdown and JSON do not perform new analysis. They render the exact same rule result used by text output, and `--strict` keeps the same exit status in every format. MaintainerLint intentionally does not post the Markdown to GitHub itself; CI, a maintainer, or another integration can decide where that evidence belongs.

For JSON consumers, use the explicit `schema` and `schema_version` fields rather than inferring a contract from presentation. See `docs/CONFIGURATION.md` for the v1 field contract and compatibility policy.

## Failure semantics

MaintainerLint prefers explicit failure states over optimistic guesses:

- a failed check stays failed;
- an escaped changed path stays escaped;
- a missing required document change stays missing;
- suspicious tracked secret material is not silently ignored;
- a command timeout is surfaced as a failure;
- full logs are sanitized before persistence.
