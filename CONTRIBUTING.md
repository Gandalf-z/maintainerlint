# Contributing

Thanks for helping improve MaintainerLint.

## Before opening a PR

1. Open or reference a focused issue for non-trivial changes.
2. Keep one PR to one coherent problem.
3. Add or update tests for changed behavior.
4. Run:

```bash
python -m unittest discover -s tests -v
python -m maintainerlint check
```

5. Evaluate documentation impact. If public CLI/config/security behavior changes, update the relevant current documentation in the same PR.
6. Keep real-environment or subjective acceptance in the PR's **Human verification** section rather than inventing fake automation.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

Runtime code should remain standard-library-only unless a dependency has a strong maintenance justification.

## Pull requests

PRs should state:

- scope and explicit non-goals;
- verification performed;
- documentation impact;
- whether the PR creates documentation drift;
- human verification still required.

Maintainers may ask for changes to be split if a PR mixes unrelated refactors or features.
