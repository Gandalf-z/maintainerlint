# MaintainerLint agent guide

This file defines repository-level expectations for coding agents and human contributors using agentic tools.

## Read first

For a code change, read only what is relevant:

1. `README.md`
2. `docs/WORKFLOW.md`
3. `docs/CONFIGURATION.md` when CLI/config behavior is involved
4. `SECURITY.md` when logs, subprocesses, filesystem permissions, or credential detection are involved
5. the directly related source and tests

Do not scan unrelated history by default.

## Working rules

- Establish the current repository behavior before changing it.
- Keep the approved issue scope bounded; do not redesign adjacent features opportunistically.
- Prefer deterministic behavior over model inference.
- Runtime remains standard-library-only unless explicitly approved.
- Never add network upload of repository source/logs as an implicit behavior.
- Never print or commit real secrets.
- Keep full command output out of normal successful agent conversations; use MaintainerLint's concise gate and sanitized logs.
- Run targeted tests first, then `python -m maintainerlint check` before finalizing a non-trivial PR.
- Evaluate documentation drift with `python -m maintainerlint impact ... --strict` when configured rules trigger.
- Human acceptance items remain explicit; do not report them as passed unless actually performed.
- Stop when the issue acceptance criteria are met.

## Definition of done

A change is done when:

1. the scoped behavior is implemented;
2. relevant tests pass;
3. MaintainerLint quality gates pass or any allowed warning is explained;
4. the final diff contains no unrelated changes;
5. documentation-impact rules are satisfied;
6. no new secret-like tracked file or private log is introduced;
7. the PR states remaining human verification;
8. the agent does not merge unless explicitly authorized by the maintainer.
