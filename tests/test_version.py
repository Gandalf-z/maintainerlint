import unittest
from pathlib import Path
import tomllib

import maintainerlint


class VersionTests(unittest.TestCase):
    def test_runtime_version_matches_project_metadata(self):
        repo = Path(__file__).resolve().parents[1]
        metadata = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(metadata["project"]["version"], maintainerlint.__version__)
