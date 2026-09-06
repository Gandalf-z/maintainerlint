# Releasing MaintainerLint

MaintainerLint keeps release publication maintainer-owned. Agents may prepare and verify a release PR, but they do not create tags, publish packages, or create GitHub Releases unless the maintainer explicitly authorizes those actions and the required tooling is available.

## Release candidate checklist

Before merging a release PR:

- confirm the target version matches in `pyproject.toml` and `src/maintainerlint/__init__.py`;
- ensure `tests/test_version.py` passes;
- move shipped changes from `Unreleased` into the dated release section in `CHANGELOG.md`;
- prepare `docs/releases/vX.Y.Z.md` as the intended GitHub Release body;
- run the complete hosted CI matrix on Linux Python 3.11, 3.12, 3.13 and Windows;
- confirm `maintainerlint check`, documentation-impact checks, and `maintainerlint doctor` are green;
- inspect the final release PR diff for unrelated changes or private material.

## Publishing after merge

After the release PR is merged and `main` is green:

1. identify the exact `main` commit to release;
2. create tag `vX.Y.Z` on that exact commit;
3. publish a GitHub Release from that tag using `docs/releases/vX.Y.Z.md` as the release notes source;
4. verify the GitHub Release points to the intended commit and is publicly visible;
5. only publish to a package index if a separate, explicit publishing workflow has been reviewed and authorized.

Do not move an existing release tag to a different commit. If a published release is wrong, document the correction and publish a new version rather than rewriting public history.

## Current package policy

- runtime remains standard-library-only;
- supported Python versions are 3.11, 3.12, and 3.13;
- release publication does not add network behavior to the MaintainerLint runtime;
- PyPI publication is intentionally separate from GitHub release preparation until credentials and provenance are handled explicitly.
