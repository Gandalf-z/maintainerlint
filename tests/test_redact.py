from pathlib import Path
import unittest

from maintainerlint.redact import redact


class RedactTests(unittest.TestCase):
    def test_redacts_common_secrets_and_paths(self):
        text = "/work/repo API_KEY=abc123 Bearer very-secret sk-abcdefgh12345678 ghp_abcdefghijklmnopqrstuvwxyz"
        value = redact(text, repo=Path("/work/repo"), home=Path("/home/example"))
        self.assertNotIn("abc123", value)
        self.assertNotIn("very-secret", value)
        self.assertNotIn("sk-abcdefgh", value)
        self.assertNotIn("ghp_", value)
        self.assertIn("<REPO>", value)
