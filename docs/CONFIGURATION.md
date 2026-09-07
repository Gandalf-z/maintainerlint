# Configuration reference

MaintainerLint uses two small, versioned TOML contracts:

- `maintainerlint.toml` describes repository-wide verification policy;
- a Task Contract describes one implementation task's diff boundary and optional targeted stages.

Both are local files. MaintainerLint does not fetch policy from a network service or call an LLM to interpret it.

## Repository policy version

```toml
version = 1
```

Only repository policy version `1` is currently accepted.

## Zero-write inspection and initializer preview

For the lowest-risk first look at an existing repository:

```bash
maintainerlint inspect --repo /path/to/project
```

`inspect` performs conservative ecosystem detection, prints proposed commands, renders the exact policy MaintainerLint would suggest, and lists what formal adoption would create. It does not create or modify repository files, execute proposed commands, install dependencies, call an LLM, or access the network.

The initializer has an equivalent preview mode:

```bash
maintainerlint init --detect --dry-run
```

`--dry-run` prints planned writes and the exact proposed `maintainerlint.toml`, but creates no files or directories. `--force` never writes while `--dry-run` is active.

This is specifically a **MaintainerLint-owned zero-write** guarantee. Arbitrary repository commands later executed by `check` or `verify` may still create generated files.

## Brownfield initializer detection

`maintainerlint init` keeps the generic starter behavior. Detection is explicit:

```bash
maintainerlint init --detect
```

Detection is read-only and local. Current conservative signals:

- Python: `tox.ini` proposes `python -m tox`; `pytest.ini` or `[tool.pytest.ini_options]` proposes `python -m pytest -q`;
- Node: recognized `package.json` scripts (`test`, `lint`, `typecheck`, `build`) use declared npm/pnpm/yarn when present;
- Rust: `Cargo.toml` proposes `cargo test`;
- Go: `go.mod` proposes `go test ./...`.

Automatic adoption requires exactly one supported ecosystem and at least one high-confidence proposal. Ambiguous or metadata-only repositories fall back to the generic starter.

## Verification stages

```toml
[[stages]]
name = "tests"
command = ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
timeout = 300
cwd = "."
allow_failure = false
```

Fields:

- `name`: unique non-empty stage name;
- `command`: non-empty argv array; MaintainerLint does not invoke a shell;
- `timeout`: positive integer seconds, default `300`;
- `cwd`: optional path relative to repository root; it may not escape the repository;
- `allow_failure`: failed stage becomes `WARN` instead of failing the overall `check` gate.

Stages run sequentially. Repeated executions of the same named stage receive distinct sanitized log files so evidence is not overwritten.

## External config and MaintainerLint-owned state

`--config` accepts either a repository-relative path or an absolute external path:

```bash
maintainerlint check \
  --repo /path/to/project \
  --config /tmp/project.toml \
  --state-dir ~/.cache/maintainerlint/project
```

For `check` and `verify`:

- default logs live under `<repo>/.maintainerlint/logs/`;
- `--state-dir DIR` places logs under `DIR/logs/`;
- `--log-dir DIR` places logs directly under `DIR` and overrides `--state-dir` for log placement;
- `~` is expanded for external paths.

Configured stages still run in the repository working tree and may write their own generated files.

## Task Contract v1

A Task Contract is a separate TOML file. It may live in the repository or at an external absolute path such as `/tmp/issue-167.toml`.

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

- `version`: required and currently must equal `1`;
- `base`: optional non-empty Git ref, default `HEAD~1`;
- `head`: optional non-empty Git ref, default `HEAD`;
- `allow`: required non-empty array of primary path globs;
- `support`: optional array of supporting path globs;
- `targeted_stages`: optional array of stage names from the repository policy.

Unknown top-level fields are rejected. This is intentional: a typo such as `allow_support` must not silently produce a weaker or different task boundary.

Relative `--task` paths are resolved from the repository root. Absolute paths remain external.

### Task-based scope

```bash
maintainerlint scope --task /tmp/issue-167.toml --strict
```

The legacy explicit form remains supported:

```bash
maintainerlint scope \
  --base origin/main \
  --head HEAD \
  --allow "src/feature/**" \
  --allow-support "docs/**" \
  --strict
```

When `--task` is supplied, it may not be combined with `--base`, `--head`, `--allow`, or `--allow-support`. One run has one source of scope truth.

## Unified agent verification

```bash
maintainerlint verify \
  --repo /path/to/project \
  --task /tmp/issue-167.toml \
  --config /tmp/project.toml \
  --state-dir /tmp/ml-state
```

`verify` is always a strict completion gate. It composes existing commands rather than defining new semantics:

1. `scope` from the Task Contract;
2. optional task `targeted_stages` through the existing check runner;
3. the full configured `check` gate;
4. strict documentation impact using task `base/head`;
5. `doctor` safety checks.

It continues through all sections so the final result can show independent scope/checks/docs/safety evidence even when one section fails.

Successful text output ends with:

```text
PASS scope
PASS checks
PASS docs
PASS safety
```

Only failing sections emit detailed captured command output before the summary.

### Verify JSON contract

```bash
maintainerlint verify ... --format json
```

JSON uses:

```json
{
  "schema": "maintainerlint.verify",
  "schema_version": 1,
  "status": "pass",
  "task": {
    "path": "/tmp/issue-167.toml",
    "version": 1,
    "base": "origin/main",
    "head": "HEAD",
    "allow": ["src/feature/**"],
    "support": ["docs/**"],
    "targeted_stages": ["tests"]
  },
  "sections": {
    "scope": {"status": "pass", "output": "..."},
    "checks": {"status": "pass", "targeted_stages": ["tests"], "output": "..."},
    "docs": {"status": "pass", "output": "..."},
    "safety": {"status": "pass", "output": "..."}
  }
}
```

Compatibility policy for `schema_version = 1`:

- consumers should use `status` and section status fields as the machine contract;
- `output` is diagnostic presentation text and should not be parsed as a stable schema;
- breaking removals, renames, type changes, or status-semantic changes require a new schema version;
- consumers should ignore unknown additional fields.

## Documentation rules

```toml
[docs]

[[docs.rules]]
name = "public API contract"
patterns = ["src/acme/api/**", "schemas/**"]
required_any = ["docs/API.md", "README.md"]
required_all = ["docs/COMPATIBILITY.md"]
```

When any changed path matches `patterns`:

- at least one `required_any` path must also be changed, if configured;
- every `required_all` path must also be changed, if configured.

`maintainerlint impact --strict` exits non-zero for unsatisfied triggered rules. `verify` invokes the same strict impact semantics using Task Contract `base/head`.

## Documentation-impact output formats

```bash
maintainerlint impact --strict --format text
maintainerlint impact --strict --format markdown
maintainerlint impact --strict --format json
```

`text`, `markdown`, and `json` render one shared result model. JSON uses the versioned `maintainerlint.impact` contract with `schema_version = 1`.

## Security allowlist

```toml
[security]
tracked_secret_allowlist = ["fixtures/fake.key"]
```

Only use this for deliberately fake fixtures that match a high-risk filename pattern. Avoid broad globs.

## Logs

By default, sanitized logs live under:

```text
.maintainerlint/logs/
```

On POSIX systems MaintainerLint attempts to create its state/log directories with mode `0700` and logs with mode `0600`. On Windows it leaves NTFS ACL management to the host. Use `--state-dir` or `--log-dir` when the target repository should receive no MaintainerLint-owned state/log writes.
