# Changelog

## Unreleased

- add a deterministic changed-file scope guard with repeatable primary/support allow patterns;
- fail strict scope checks when modified, deleted, or renamed paths escape the declared boundary;
- preserve documentation-impact checks as an independent gate even when docs/changelog are scope-allowed.

## 0.1.0 — 2026-09-06

Initial public release:

- low-output sequential verification stages;
- sanitized failure logs;
- deterministic documentation-impact rules;
- repository doctor for high-confidence tracked-secret risks;
- starter configuration and PR template;
- self-hosted GitHub Actions CI example.