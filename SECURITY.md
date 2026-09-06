# Security policy

## Supported versions

MaintainerLint is pre-1.0. Security fixes are applied to the latest release line.

## Threat boundary

MaintainerLint executes commands configured by the repository maintainer. A `maintainerlint.toml` file is therefore executable policy: review it before running MaintainerLint in an untrusted repository.

MaintainerLint v0.1.0:

- runs configured commands without a shell;
- captures stdout/stderr locally;
- sanitizes common credential patterns and local repository/home paths before logs are persisted or printed;
- checks for a small set of high-confidence secret-like tracked filenames;
- does not upload source, logs, or credentials to an external service;
- has zero runtime third-party dependencies.

Redaction is defense-in-depth, **not** a guarantee that arbitrary secrets can never appear in output. Do not intentionally print secrets into build logs.

## Reporting a vulnerability

Please avoid filing public issues containing live credentials, private source, or exploit details that would put users at immediate risk. Contact the repository maintainer privately through the security-reporting method configured on the GitHub repository.
