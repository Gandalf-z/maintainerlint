# Maintainer workflow

MaintainerLint is built around a separation of responsibilities rather than a specific AI tool.

## Roles

### 1. Planner / reviewer

Before code changes, establish:

- the user or maintainer problem;
- current repository facts;
- the smallest acceptable scope;
- files/contracts likely to change;
- targeted verification;
- what remains human-owned;
- explicit stop conditions.

The planner can be a maintainer, ChatGPT, another model, or a human teammate.

### 2. Execution agent

The execution agent should receive a bounded implementation packet and be asked to:

- read only task-relevant code/docs;
- implement the approved delta;
- run focused checks while working;
- run the final MaintainerLint verification gate;
- inspect the final diff;
- open a PR;
- stop before merge unless the maintainer explicitly owns that action.

The execution role should not silently redesign adjacent product behavior or expand the issue.

### 3. Deterministic repository gates

MaintainerLint checks repository evidence such as:

- configured test/build/lint commands;
- task changed-file scope;
- sanitized failure output;
- documentation-impact rules;
- high-confidence tracked-secret risks.

### 4. Human acceptance

Some checks remain intentionally human-owned:

- UI quality;
- real-device / real-OS behavior beyond automated coverage;
- production rollout decisions;
- destructive migrations;
- legal/compliance judgment;
- security-risk acceptance;
- whether the original user problem is actually solved.

A green `verify` result is evidence, not a substitute for maintainer acceptance.

## Shadow-first adoption

Before writing policy into an existing repository:

```bash
maintainerlint inspect --repo /path/to/project
```

Then preview the initializer:

```bash
cd /path/to/project
maintainerlint init --detect --dry-run
```

For executed checks, MaintainerLint-owned logs can stay external:

```bash
maintainerlint check \
  --repo /path/to/project \
  --config /tmp/project.toml \
  --state-dir ~/.cache/maintainerlint/project
```

This is a MaintainerLint-owned zero-write boundary. User-configured repository commands may still write generated files.

## Task Contract as the bounded implementation packet

The first machine-readable part of an implementation packet is the Task Contract:

```toml
version = 1
base = "origin/main"
head = "HEAD"
allow = ["src/feature/**", "tests/feature/**"]
support = ["docs/**", "CHANGELOG.md"]
targeted_stages = ["tests"]
```

This deliberately starts small. It encodes repository-verifiable facts rather than prose intent:

- which Git range defines the task diff;
- which primary paths may change;
- which supporting paths may change;
- which existing check stages should be run as targeted evidence first.

It can live outside the target repository, for example `/tmp/issue-167.toml`, so an agent can receive task scope without adding project files.

The longer-term roadmap can extend this into an issue-to-implementation-packet schema with goal, constraints, human acceptance, and stop conditions. Those richer fields are **not** claimed as part of Task Contract v1.

## Task-based changed-file scope

Use the contract directly:

```bash
maintainerlint scope \
  --repo /path/to/project \
  --task /tmp/issue-167.toml \
  --strict
```

The legacy explicit CLI boundary remains available for one-off use. Do not combine it with `--task`; one run should have one source of scope truth.

Scope remains structural, not semantic:

- added/modified/deleted paths must be allowed;
- renames require old and new paths to be allowed;
- copies require the destination path to be allowed;
- support scope does not bypass documentation-impact rules.

## Final Agent Verification

At completion, prefer one final command:

```bash
maintainerlint verify \
  --repo /path/to/project \
  --task /tmp/issue-167.toml \
  --config /tmp/project.toml \
  --state-dir ~/.cache/maintainerlint/project
```

`verify` is orchestration, not a new checker. It invokes existing MaintainerLint behavior in order:

1. strict `scope` from the Task Contract;
2. optional task `targeted_stages` through the existing check runner;
3. full `check` policy;
4. strict `impact` using the task `base/head`;
5. `doctor` safety checks.

It runs every section and then summarizes the independent evidence:

```text
PASS scope
PASS checks
PASS docs
PASS safety
```

If one section fails, its underlying deterministic output is shown before the final summary. The other sections still run, so an agent gets one complete completion report rather than a first-error-only transcript.

### Machine-readable final evidence

```bash
maintainerlint verify ... --format json
```

The JSON contract is `maintainerlint.verify`, `schema_version = 1`. Consumers should rely on overall and section `status` fields. Captured human-readable output is diagnostic evidence, not a parsing contract.

## Why targeted stages may run twice

If a Task Contract declares:

```toml
targeted_stages = ["tests"]
```

`verify` runs `tests` first as targeted evidence and then runs the full repository `check`, which may contain `tests` again. This intentionally mirrors the common agent workflow of focused verification followed by the complete gate.

MaintainerLint therefore gives every stage execution a unique log filename; repeated fast executions cannot overwrite earlier evidence.

## Documentation truth

Long-lived projects often have multiple documents describing the same system. Use `docs.rules` to force reconsideration only when stale documentation would materially mislead maintainers or users.

`verify` does not implement a second docs checker. It invokes the same strict impact result used by standalone `maintainerlint impact`.

## Failure semantics

MaintainerLint prefers explicit failure states over optimistic guesses:

- an escaped task path stays escaped;
- an unknown Task Contract key is rejected;
- an unknown targeted stage fails checks clearly;
- a failed repository check stays failed;
- missing required documentation stays missing;
- suspicious tracked secret material is not silently ignored;
- timeouts are failures;
- full command logs are sanitized before persistence.

## Human merge gate

A recommended end-to-end flow is:

```text
Issue
  ↓
Planner defines Task Contract + human acceptance
  ↓
Agent implements
  ↓
Agent runs maintainerlint verify
  ↓
PR with deterministic evidence
  ↓
Maintainer performs remaining human checks
  ↓
Maintainer decides merge
```

MaintainerLint intentionally stops before autonomous merge ownership.
