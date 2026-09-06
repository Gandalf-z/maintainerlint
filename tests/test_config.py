from pathlib import Path
import tempfile
import unittest

from maintainerlint.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def test_loads_stages_and_doc_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "maintainerlint.toml"
            path.write_text('''version = 1\n[[stages]]\nname="tests"\ncommand=["python","-V"]\n[docs]\n[[docs.rules]]\nname="cli"\npatterns=["src/**"]\nrequired_any=["README.md"]\n[security]\ntracked_secret_allowlist=[".env.example"]\n''')
            config = load_config(path)
            self.assertEqual(config.stages[0].name, "tests")
            self.assertEqual(config.doc_rules[0].required_any, ("README.md",))

    def test_rejects_duplicate_stage_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "maintainerlint.toml"
            path.write_text('''[[stages]]\nname="x"\ncommand=["true"]\n[[stages]]\nname="x"\ncommand=["true"]\n''')
            with self.assertRaises(ConfigError):
                load_config(path)
