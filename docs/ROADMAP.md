# Roadmap

MaintainerLint is intentionally shipping in small, testable layers.

## v0.1 — deterministic maintenance gates

- [x] low-output sequential check runner;
- [x] sanitized local logs;
- [x] documentation-drift rules;
- [x] tracked-secret doctor;
- [x] starter config and PR template;
- [x] self-hosting CI.

## v0.2 — better repository adoption

- [ ] `maintainerlint init` detects common Python/Node/Rust/Go checks without overwriting existing config;
- [ ] richer glob semantics and rule diagnostics;
- [x] Markdown documentation-impact output for PR/check summaries;
- [ ] explicit generated-file consistency stage helpers;
- [x] Windows path/redaction fixtures and CI coverage;
- [ ] examples for Python, Node, and mixed repositories.

## v0.3 — maintainer automation

- [ ] optional GitHub PR check summary;
- [ ] issue-to-implementation-packet schema;
- [x] bounded changed-file scope guard;
- [x] versioned machine-readable documentation-impact JSON schema for agent integrations;
- [ ] release checklist gate.

## Non-goals

MaintainerLint will not become:

- an autonomous merge bot;
- an LLM proxy;
- a replacement for tests;
- a tool that uploads private source/logs by default;
- a system that pretends human UX/security/release acceptance can always be automated.
