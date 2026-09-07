# Security policy

## Supported versions

MaintainerLint is pre-1.0. Security fixes are applied to the latest release line.

## Threat boundary

MaintainerLint executes commands configured by the repository maintainer. A `maintainerlint.toml` file is therefore executable policy: review it before running MaintainerLint in an untrusted repository.

MaintainerLint:

- runs configured commands without a shell;
- captures stdout/stderr locally;
- sanitizes common credential patterns and local repository/home paths before logs are persisted or printed;
- checks for a small set of high-confidence secret-like tracked filenames;
- does not upload source, logs, or credentials to an external service;
- has zero runtime third-party dependencies.

Redaction is defense-in-depth, **not** a guarantee that arbitrary secrets can never appear in output. Do not intentionally print secrets into build logs.

## MaintainerLint-owned zero-write modes

`maintainerlint inspect --repo ...` and `maintainerlint init --detect --dry-run` are designed as read-only evaluation paths. They do not create target files, persist MaintainerLint state, execute detected repository commands, install dependencies, call an LLM, or use the network.

`maintainerlint check` executes the commands in the selected policy. Use an external config plus `--state-dir` or `--log-dir` to keep MaintainerLint-owned configuration/log state outside the target repository, for example:

```bash
maintainerlint check \
  --repo /path/to/project \
  --config /tmp/project.toml \
  --state-dir ~/.cache/maintainerlint/project
```

This does **not** sandbox configured commands. A repository's test, build, formatter, code generator, package manager, or other configured command may create or modify files in its working directory. The zero-write claim applies only to writes owned by MaintainerLint itself.

## Local log permissions

On POSIX systems MaintainerLint explicitly attempts to set its state/log directories to mode `0700` and persisted log files to `0600`. On Windows it does not rewrite NTFS ACLs; log files inherit the selected directory permissions.

When the default `<repo>/.maintainerlint/logs/` location is undesirable, use `--state-dir` or `--log-dir` to place logs elsewhere. External failure-log paths are rendered without assuming they are repository-relative.

Path redaction recognizes both `\` and `/` spellings for Windows drive paths so common tool output cannot bypass repository/home path masking solely because it uses a different separator style.

## Reporting a vulnerability

Please avoid filing public issues containing live credentials, private source, or exploit details that would put users at immediate risk. Contact the repository maintainer privately through the security-reporting method configured on the GitHub repository.
