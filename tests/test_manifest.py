# ====================
# Manifest writer tests
# ====================
import json
import os
import tempfile
import unittest

from docsiphon.models import FetchKind, FetchStatus, NoteKind, PageRecord, SourceKind
from docsiphon.storage import ManifestWriter


class TestManifestWriter(unittest.TestCase):
    def test_manifest_writes_enum_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            writer = ManifestWriter(tmp)
            record = PageRecord(
                url="https://example.com/a",
                fetched_url="https://example.com/a",
                source=SourceKind.SITEMAP,
                fetch_kind=FetchKind.MARKDOWN,
                status=FetchStatus.OK,
                http_status=200,
                content_type="text/markdown",
                bytes_written=12,
                out_path="out.md",
                note=NoteKind.MARKDOWN_NOT_AVAILABLE,
                error=None,
            )
            writer.write(record)
            path = os.path.join(tmp, "manifest.jsonl")
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                payload = json.loads(f.readline())
            self.assertEqual(payload["source"], "sitemap")
            self.assertEqual(payload["fetch_kind"], "markdown")
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["note"], "markdown_not_available")
            self.assertEqual(payload["manifest_version"], "1.1")


if __name__ == "__main__":
    unittest.main()
