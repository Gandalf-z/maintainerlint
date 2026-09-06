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

## Failure semantics

MaintainerLint prefers explicit failure states over optimistic guesses:

- a failed check stays failed;
- an escaped changed path stays escaped;
- a missing required document change stays missing;
- suspicious tracked secret material is not silently ignored;
- a command timeout is surfaced as a failure;
- full logs are sanitized before persistence.