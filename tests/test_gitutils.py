import unittest

from maintainerlint.gitutils import GitError, parse_name_status_z


class GitUtilsTests(unittest.TestCase):
    def test_parse_name_status_handles_modify_rename_and_delete(self):
        entries = parse_name_status_z(
            "M\0src/a.py\0R100\0old.py\0new.py\0D\0gone.py\0"
        )
        self.assertEqual(entries[0].status, "M")
        self.assertEqual(entries[0].paths, ("src/a.py",))
        self.assertEqual(entries[1].status, "R100")
        self.assertEqual(entries[1].paths, ("old.py", "new.py"))
        self.assertEqual(entries[2].status, "D")
        self.assertEqual(entries[2].paths, ("gone.py",))

    def test_parse_name_status_rejects_truncated_rename(self):
        with self.assertRaises(GitError):
            parse_name_status_z("R100\0old.py\0")


if __name__ == "__main__":
    unittest.main()