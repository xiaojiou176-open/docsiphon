# ====================
# Storage tests
# ====================
import json
import os
import tempfile
import unittest

from docsiphon.config import RunConfig
from docsiphon.storage import (
    _ensure_md_extension,
    build_output_path,
    build_html_output_path,
    load_manifest_ok_urls,
    load_manifest_cache,
    write_markdown,
    write_html,
    write_error_snapshot,
    ManifestWriter,
)
from docsiphon.models import FetchKind, FetchStatus, PageRecord, SourceKind


class TestStorage(unittest.TestCase):
    def test_build_output_path_site_root_and_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs/start", output_dir=tmp, site_root="Docs")
            path = build_output_path("https://example.com/docs/start/intro", config)
            self.assertTrue(path.endswith(os.path.join("Docs", "intro.md")))
            self.assertEqual(_ensure_md_extension("a.md"), "a.md")
            self.assertEqual(_ensure_md_extension("a"), "a.md")

    def test_write_markdown_frontmatter_no_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(
                base_url="https://example.com/docs/start",
                output_dir=tmp,
                frontmatter=True,
                frontmatter_timestamp=False,
            )
            path, err = write_markdown("hello", "https://example.com/docs/a", "https://example.com/docs/a", config)
            self.assertIsNone(err)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("source_url:", content)
            self.assertIn("fetched_url:", content)
            self.assertNotIn("fetched_at_utc:", content)

    def test_write_markdown_frontmatter_with_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(
                base_url="https://example.com/docs/start",
                output_dir=tmp,
                frontmatter=True,
                frontmatter_timestamp=True,
            )
            path, err = write_markdown("hello", "https://example.com/docs/a", "https://example.com/docs/a", config)
            self.assertIsNone(err)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("fetched_at_utc:", content)

    def test_write_markdown_atomic_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs/start", output_dir=tmp)
            with unittest.mock.patch("docsiphon.storage._atomic_write", side_effect=OSError("fail")):
                path, err = write_markdown("hello", "https://example.com/docs/a", "https://example.com/docs/a", config)
            self.assertIsNone(path)
            self.assertIn("fail", err or "")

    def test_write_html_and_error_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs/start", output_dir=tmp)
            html_path, err = write_html("<html>ok</html>", "https://example.com/docs/a", config)
            self.assertIsNone(err)
            self.assertTrue(html_path.endswith(".html"))
            snapshot_path, err2 = write_error_snapshot(tmp, "https://example.com/docs/a", "oops", "html", "run123")
            self.assertIsNone(err2)
            self.assertTrue(snapshot_path.endswith(".txt"))
            self.assertIn("run123", os.path.basename(snapshot_path))

    def test_error_snapshot_respects_max_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = "x" * 200
            snapshot_path, err = write_error_snapshot(tmp, "https://example.com/docs/a", content, "html", max_bytes=32)
            self.assertIsNone(err)
            self.assertIsNotNone(snapshot_path)
            self.assertLessEqual(os.path.getsize(snapshot_path), 32)

    def test_error_snapshot_respects_quota(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = "x" * 10
            path1, err1 = write_error_snapshot(
                tmp,
                "https://example.com/docs/a",
                content,
                "html",
                max_files=1,
            )
            self.assertIsNone(err1)
            self.assertIsNotNone(path1)
            path2, err2 = write_error_snapshot(
                tmp,
                "https://example.com/docs/b",
                content,
                "html",
                max_files=1,
            )
            self.assertIsNone(path2)
            self.assertIsNotNone(err2)

    def test_build_html_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs/start", output_dir=tmp)
            path = build_html_output_path("https://example.com/docs/a", config)
            self.assertTrue(path.endswith("a.html"))
            path2 = build_html_output_path("https://example.com/docs/a.md.txt", config)
            self.assertTrue(path2.endswith("a.html"))

    def test_load_manifest_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            payloads = [
                {"url": "https://example.com/docs/a", "etag": "E1", "last_modified": "L1", "content_hash": "H1"},
                {"url": "https://example.com/docs/b", "status": "ok"},
            ]
            with open(os.path.join(tmp, "manifest.jsonl"), "w", encoding="utf-8") as f:
                for p in payloads:
                    f.write(json.dumps(p) + "\n")
            cache = load_manifest_cache(tmp)
            self.assertEqual(cache["https://example.com/docs/a"]["etag"], "E1")

    def test_manifest_sorted_finalize(self):
        with tempfile.TemporaryDirectory() as tmp:
            writer = ManifestWriter(tmp, sorted_mode=True)
            record_b = PageRecord(
                url="https://example.com/b",
                fetched_url="https://example.com/b",
                source=SourceKind.SITEMAP,
                fetch_kind=FetchKind.MARKDOWN,
                status=FetchStatus.OK,
            )
            record_a = PageRecord(
                url="https://example.com/a",
                fetched_url="https://example.com/a",
                source=SourceKind.SITEMAP,
                fetch_kind=FetchKind.MARKDOWN,
                status=FetchStatus.OK,
            )
            writer.write(record_b)
            writer.write(record_a)
            writer.finalize()
            path = os.path.join(tmp, "manifest.jsonl")
            with open(path, "r", encoding="utf-8") as f:
                lines = [json.loads(line)["url"] for line in f.readlines() if line.strip()]
            self.assertEqual(lines, ["https://example.com/a", "https://example.com/b"])

    def test_load_manifest_ok_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            payloads = [
                {"url": "https://example.com/docs/a", "status": "ok"},
                {"url": "https://example.com/docs/b", "status": "failed"},
            ]
            with open(os.path.join(tmp, "manifest.jsonl"), "w", encoding="utf-8") as f:
                for p in payloads:
                    f.write(json.dumps(p) + "\n")
                f.write("{bad json}\n")
            ok_urls = load_manifest_ok_urls(tmp)
            self.assertEqual(ok_urls, {"https://example.com/docs/a"})

    def test_load_manifest_ok_urls_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok_urls = load_manifest_ok_urls(tmp)
            self.assertEqual(ok_urls, set())


if __name__ == "__main__":
    unittest.main()
