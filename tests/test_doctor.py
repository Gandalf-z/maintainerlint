import unittest

from maintainerlint.doctor import suspicious_tracked_files


class DoctorTests(unittest.TestCase):
    def test_flags_high_confidence_secret_files(self):
        risky = suspicious_tracked_files((".env", "credentials.json", "docs/readme.md", "ops/credentials.json"), ())
        self.assertEqual(risky, (".env", "credentials.json", "ops/credentials.json"))

    def test_allows_examples(self):
        risky = suspicious_tracked_files((".env.example",), ())
        self.assertEqual(risky, ())

    def test_normalizes_windows_originated_tracked_paths(self):
        risky = suspicious_tracked_files(
            (r"ops\credentials.json", r"keys\id_ed25519", r"docs\readme.md", r".\secrets.json"),
            (),
        )
        self.assertEqual(risky, ("ops/credentials.json", "keys/id_ed25519", "secrets.json"))
