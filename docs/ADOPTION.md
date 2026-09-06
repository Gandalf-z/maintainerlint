# Adoption guide

MaintainerLint is designed to be added to an existing repository without replacing its current CI or contributor process.

## 1. Install locally

From a checkout of MaintainerLint:

```bash
python -m pip install -e .
```

Once published as a package, projects will be able to pin a released version instead.

## 2. Create the starter policy

Inside the target repository:

```bash
maintainerlint init --pr-template
```

Review the generated `maintainerlint.toml` before committing it. The generated commands are examples, not project truth.

## 3. Map existing checks instead of inventing new ones

Add the commands maintainers already trust:

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
