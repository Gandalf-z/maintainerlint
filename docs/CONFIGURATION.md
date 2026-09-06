# Configuration reference

MaintainerLint reads `maintainerlint.toml` from the repository root by default.

## Version

```toml
version = 1
```

Only version `1` is currently accepted.

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

Add `.maintainerlint/` to `.gitignore`. On POSIX systems MaintainerLint attempts to create the directory with mode `0700` and log files with mode `0600`.
