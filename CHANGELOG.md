# Changelog

## Unreleased

- add a deterministic changed-file scope guard with repeatable primary/support allow patterns;
- fail strict scope checks when modified, deleted, or renamed paths escape the declared boundary;
- preserve documentation-impact checks as an independent gate even when docs/changelog are scope-allowed;
- add Markdown documentation-impact output suitable for PR comments and check summaries;
- add a versioned `maintainerlint.impact` JSON contract with stable v1 fields for tool/agent integrations;
- keep text, Markdown, and JSON output on one shared impact result model with identical strict-exit semantics;
- add opt-in `maintainerlint init --detect` proposals for high-confidence Python, Node, Rust, and Go repository signals;
- keep brownfield initialization non-destructive and fall back to the generic starter for empty, metadata-only, or multi-ecosystem repositories;
- print detected signals and proposed commands before policy creation without running package managers, installing dependencies, or using network/LLM inference.

## 0.1.0 — 2026-09-06

Initial public release:

- low-output sequential verification stages;
- sanitized failure logs;
- deterministic documentation-impact rules;
- repository doctor for high-confidence tracked-secret risks;
- starter configuration and PR template;
- self-hosted GitHub Actions CI example.
