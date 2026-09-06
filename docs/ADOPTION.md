# Adoption guide

MaintainerLint is designed to be added to an existing repository without replacing its current CI or contributor process.

## 1. Install locally

From a checkout of MaintainerLint:

```bash
python -m pip install -e .
```

Once published as a package, projects will be able to pin a released version instead.

## 2. Create or detect a starter policy

The generic starter remains available:

```bash
maintainerlint init --pr-template
```

For a brownfield repository, explicitly request conservative detection:

```bash
maintainerlint init --detect --pr-template
```

Detection prints repository signals and every proposed command before writing `maintainerlint.toml`. It does not execute those commands, install dependencies, use an LLM, or access the network.

Examples of high-confidence proposals:

```text
DETECT node: package.json
PROPOSE node/tests: npm run test (package.json scripts.test)
PROPOSE node/lint: npm run lint (package.json scripts.lint)
USE detected node stages
CREATE /repo/maintainerlint.toml
```

Only one supported ecosystem with at least one high-confidence proposal is auto-adopted. Empty repositories, metadata-only signals, or multi-ecosystem repositories fall back to the generic starter. This is intentional: a mixed monorepo needs maintainer judgment instead of a guessed test strategy.

Existing `maintainerlint.toml` files are never overwritten unless `--force` is supplied. Even with `--force`, ambiguous detection still falls back rather than selecting an ecosystem arbitrarily.

Review every generated command before committing the policy. Detection is evidence-based assistance, not project truth.

## 3. Map existing checks instead of inventing new ones

Keep or replace detected proposals with the commands maintainers already trust:

```toml
[[stages]]
name = "unit-tests"
command = ["python", "-m", "pytest", "-q"]

[[stages]]
name = "lint"
command = ["ruff", "check", "."]

[[stages]]
name = "diff"
command = ["git", "diff", "--check"]
```

Prefer a few meaningful gates over a giant generic checklist.

## 4. Add documentation rules only for real contracts

Good rule targets include:

- public API schemas;
- CLI flags and config formats;
- runtime topology;
- compatibility policy;
- security/privacy boundaries;
- user-visible workflows.

Avoid forcing a changelog edit for every internal fix. The point is to prevent misleading current-truth documentation, not create paperwork.

## 5. Add CI after local validation

A minimal pull-request job:

```yaml
- name: MaintainerLint quality gate
  run: maintainerlint check

- name: Documentation drift gate
  run: maintainerlint impact --base "${{ github.event.pull_request.base.sha }}" --head "${{ github.sha }}" --strict

- name: Repository doctor
  run: maintainerlint doctor
```

Use a full Git checkout when comparing arbitrary PR base/head SHAs.

## 6. Keep human gates explicit

Examples that should often stay outside MaintainerLint:

- visually judging a UI;
- testing on a physical device;
- approving a destructive migration;
- production rollout approval;
- deciding whether a security risk is acceptable;
- confirming that a product problem is actually solved.

Record these in the PR instead of pretending CI performed them.

## Brownfield rule

For a mature repository, first run MaintainerLint in advisory mode. Tighten rules only after the current repository can satisfy them without unrelated cleanup. A governance tool should reduce maintainer load, not freeze delivery.
