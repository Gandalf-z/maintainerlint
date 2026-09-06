# Configuration reference

MaintainerLint reads `maintainerlint.toml` from the repository root by default.

## Version

```toml
version = 1
```

Only version `1` is currently accepted.

## Initializer detection

`maintainerlint init` keeps the original generic starter behavior. Brownfield detection is explicit:

```bash
maintainerlint init --detect
```

Detection is local and read-only. It never installs packages, runs package-manager commands, calls an LLM, or uses the network. Signals and proposed commands are printed before the policy file is written.

Current conservative rules:

- Python: `tox.ini` proposes `python -m tox`; `pytest.ini` or `[tool.pytest.ini_options]` proposes `python -m pytest -q`;
- Node: recognized `package.json` scripts (`test`, `lint`, `typecheck`, `build`) are proposed through the declared `packageManager` when it is `npm`, `pnpm`, or `yarn`, otherwise `npm`; the default `no test specified` placeholder is ignored;
- Rust: `Cargo.toml` proposes `cargo test`;
- Go: `go.mod` proposes `go test ./...`.

Automatic adoption requires exactly one supported ecosystem and at least one high-confidence proposal. Empty repositories, metadata-only signals, malformed metadata, or multiple supported ecosystems fall back to the generic starter rather than guessing.

An existing `maintainerlint.toml` is not overwritten unless `--force` is explicitly supplied. `--force` permits replacement; it does not make ambiguous detection acceptable, so ambiguous repositories still receive the generic starter.

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

- `name`: unique human-readable stage name;
- `command`: argv array; MaintainerLint does not invoke a shell;
- `timeout`: positive integer seconds, default `300`;
- `cwd`: optional path relative to the repository root;
- `allow_failure`: if `true`, a failed stage prints `WARN` and does not fail the overall `check` command.

Commands run sequentially in v0.1.0. This makes output deterministic and avoids multiple agents/checks mutating the same workspace at once.

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

`maintainerlint impact --strict` exits non-zero for unsatisfied triggered rules.

Rules are intentionally exact and project-defined. MaintainerLint does not use an LLM to guess documentation impact.

## Documentation-impact output formats

The `impact` command evaluates rules once and can render the same result three ways:

```bash
maintainerlint impact --strict --format text
maintainerlint impact --strict --format markdown
maintainerlint impact --strict --format json
```

`text` is the concise terminal default. `markdown` is suitable for a PR comment or check summary. `json` is intended for agents and other tooling. Output format never changes rule semantics or `--strict` exit behavior.

### JSON contract

JSON output uses an explicitly versioned top-level contract:

```json
{
  "schema": "maintainerlint.impact",
  "schema_version": 1,
  "status": "pass",
  "changed": ["src/acme/api/client.py", "docs/API.md"],
  "summary": {
    "triggered_rules": 1,
    "failed_rules": 0
  },
  "rules": [
    {
      "name": "public API contract",
      "status": "pass",
      "satisfied": true,
      "triggered_by": ["src/acme/api/client.py"],
      "missing_any": [],
      "missing_all": []
    }
  ]
}
```

Compatibility policy for `schema_version = 1`:

- existing fields keep their meaning and type;
- breaking removals, renames, or semantic changes require a new schema version;
- consumers should ignore unknown additional fields so compatible metadata can be added later;
- `rules` contains only triggered rules; a no-trigger result has `status = "pass"`, zero summary counts, and an empty `rules` array.

This schema is a reporting contract only. It does not add network access or GitHub authentication to the runtime.

## Security allowlist

```toml
[security]
tracked_secret_allowlist = ["fixtures/fake.key"]
```

Only use this for deliberately fake fixtures that match a high-risk filename pattern. Avoid broad globs.

## Logs

`maintainerlint check` stores sanitized logs under:

```text
.maintainerlint/logs/
```

Add `.maintainerlint/` to `.gitignore`. On POSIX systems MaintainerLint attempts to create the directory with mode `0700` and log files with mode `0600`. On Windows those POSIX mode guarantees do not apply: MaintainerLint leaves NTFS ACL management to the host and the files inherit the working tree directory permissions.
