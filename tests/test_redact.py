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

    def test_redacts_windows_repo_and_home_with_either_separator(self):
        repo = Path(r"C:\Users\Gandalf\src\project")
        home = Path(r"C:\Users\Gandalf")
        text = (
            r"C:\Users\Gandalf\src\project\build\result.txt"
            "\r\n"
            r"c:/users/gandalf/AppData/Local/tool/cache.txt"
        )
        value = redact(text, repo=repo, home=home)
        self.assertNotIn("project", value.lower())
        self.assertNotIn("c:/users/gandalf", value.lower())
        self.assertNotIn(r"c:\users\gandalf", value.lower())
        self.assertIn("<REPO>", value)
        self.assertIn("<HOME>", value)
