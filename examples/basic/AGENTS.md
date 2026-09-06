# Agent instructions

Before changing code:

1. Read the issue and only the repository docs directly relevant to it.
2. Confirm the current behavior from code/tests/config instead of relying on chat history.
3. State the bounded scope, tests, and stop condition.

Before opening a PR:

1. Run targeted tests.
2. Run `maintainerlint check`.
3. Run the configured documentation-impact gate.
4. Inspect the final diff for unrelated changes and secret-like files.
5. List any real-environment checks that still require a human.
6. Do not merge unless the maintainer explicitly authorizes it.
