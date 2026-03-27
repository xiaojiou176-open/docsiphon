# ====================
# CLI helper tests
# ====================
import tempfile
import unittest

from docsiphon.cli import (
    _dedupe_by_output_path,
    _apply_filters,
    _apply_robots,
    _load_robots,
    _parse_auth,
    _coerce_bool,
    _flatten_csv,
)
from docsiphon.config import RunConfig
from docsiphon.models import SourceKind, NoteKind
import urllib.robotparser


class TestCliHelpers(unittest.TestCase):
    def test_dedupe_by_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs", output_dir=tmp)
            urls = ["https://example.com/docs", "https://example.com/docs/"]
            deduped, collisions = _dedupe_by_output_path(urls, config)
            self.assertEqual(len(deduped), 1)
            self.assertEqual(len(collisions), 1)
            self.assertIn("https://example.com/docs", collisions[0])

    def test_apply_filters_regex_and_ext(self):
        config = RunConfig(
            base_url="https://example.com/docs",
            output_dir="/tmp",
            include_regex="^https://example.com/docs/",
            exclude_regex="/docs/private",
        )
        urls = [
            "https://example.com/docs/a",
            "https://example.com/docs/private/secret",
            "https://example.com/docs/file.pdf",
            "https://example.com/other",
        ]
        kept, filtered = _apply_filters(urls, config, SourceKind.SITEMAP)
        self.assertEqual(kept, ["https://example.com/docs/a"])
        notes = [r.note for r in filtered]
        self.assertIn(NoteKind.EXCLUDED_EXTENSION, notes)
        self.assertIn(NoteKind.FILTERED_OUT, notes)

    def test_apply_robots_disallow(self):
        config = RunConfig(base_url="https://example.com/docs", output_dir="/tmp")
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(["User-agent: *", "Disallow: /docs/private"])
        urls = ["https://example.com/docs/a", "https://example.com/docs/private/x"]
        kept, filtered = _apply_robots(urls, config, rp, SourceKind.SITEMAP)
        self.assertEqual(kept, ["https://example.com/docs/a"])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].note, NoteKind.ROBOTS_DISALLOW)

    def test_load_robots(self):
        class _Resp:
            def __init__(self):
                self.status_code = 200
                self.text = "User-agent: *\nDisallow: /x\n"

        class _Session:
            def get(self, url, timeout=5):
                return _Resp()

        rp = _load_robots("https://example.com/docs", _Session(), 5)
        self.assertIsNotNone(rp)
        self.assertFalse(rp.can_fetch("*", "https://example.com/x"))

    def test_parse_auth_and_helpers(self):
        self.assertEqual(_parse_auth("u:p"), ("u", "p"))
        self.assertEqual(_parse_auth({"username": "u", "password": "p"}), ("u", "p"))
        self.assertEqual(_parse_auth(["u", "p"]), ("u", "p"))
        self.assertTrue(_coerce_bool("true", False))
        self.assertFalse(_coerce_bool("false", True))
        self.assertEqual(_flatten_csv(["a,b", "c"]), ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
