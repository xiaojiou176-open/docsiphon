# ====================
# Config profile tests
# ====================
import tempfile
import unittest
from pathlib import Path

from docsiphon.config import load_profile


class TestConfigProfile(unittest.TestCase):
    def test_load_profile(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".toml") as f:
            f.write(
                "[profile]\n"
                "rate_limit_per_sec = 2.5\n"
                "include_regex = \"/docs/\"\n"
                "headers = { \"X-API\" = \"token\" }\n"
            )
            path = f.name
        try:
            data = load_profile(path)
            self.assertEqual(data.get("rate_limit_per_sec"), 2.5)
            self.assertEqual(data.get("include_regex"), "/docs/")
            self.assertEqual(data.get("headers", {}).get("X-API"), "token")
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_profile_named(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".toml") as f:
            f.write(
                "[profiles.team]\n"
                "rate_limit_per_sec = 1.0\n"
                "include_regex = \"/docs/\"\n"
            )
            path = f.name
        try:
            data = load_profile(path, "team")
            self.assertEqual(data.get("rate_limit_per_sec"), 1.0)
        finally:
            Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
