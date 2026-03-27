# ====================
# CLI _fetch_one tests
# ====================
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

from docsiphon.cli import _fetch_one
from docsiphon.config import RunConfig
from docsiphon.models import FetchKind, FetchStatus, NoteKind
from docsiphon.fetch import OversizeError
from docsiphon.storage import ManifestWriter
from docsiphon.utils import RateLimiter, HostRateLimiter, HostConcurrencyLimiter


class TestCliFetchOne(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.config = RunConfig(base_url="https://example.com/docs", output_dir=self.tmp.name)
        self.manifest = ManifestWriter(self.tmp.name)
        self.limiter = RateLimiter(0)
        self.host_limiter = HostRateLimiter(0)
        self.host_concurrency = HostConcurrencyLimiter(0)
        self.lock = threading.Lock()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_markdown_success(self):
        with patch("docsiphon.cli.fetch_markdown") as fetch_md, patch(
            "docsiphon.cli.write_markdown"
        ) as write_md:
            write_md.return_value = ("/tmp/out.md", None)
            fetch_md.return_value = ("# Title", "text/markdown", FetchKind.MARKDOWN, 200, None, None, None, None)
            record = _fetch_one(
                "https://example.com/docs/a",
                self.config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.OK)
            self.assertEqual(record.fetch_kind, FetchKind.MARKDOWN)
            self.assertEqual(record.bytes_written, len("# Title".encode("utf-8")))
            self.assertIsNone(record.note)
            self.assertEqual(record.http_status, 200)
            self.assertEqual(record.content_type, "text/markdown")
            self.assertTrue(record.fetched_url.endswith(".md"))

    def test_markdown_html_no_fallback(self):
        config = RunConfig(base_url="https://example.com/docs", output_dir=self.tmp.name, html_fallback=False)
        with patch("docsiphon.cli.fetch_markdown") as fetch_md:
            fetch_md.return_value = (None, "text/html", FetchKind.MARKDOWN, 200, None, None, None, "<html></html>")
            record = _fetch_one(
                "https://example.com/docs/a",
                config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.SKIPPED)
            self.assertEqual(record.note, NoteKind.MARKDOWN_IS_HTML)
            self.assertEqual(record.http_status, 200)
            self.assertEqual(record.content_type, "text/html")

    def test_markdown_non_text_no_fallback(self):
        config = RunConfig(base_url="https://example.com/docs", output_dir=self.tmp.name, html_fallback=False)
        with patch("docsiphon.cli.fetch_markdown") as fetch_md:
            fetch_md.return_value = (None, "application/pdf", FetchKind.MARKDOWN, 200, None, None, None, None)
            record = _fetch_one(
                "https://example.com/docs/a",
                config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.SKIPPED)
            self.assertEqual(record.note, NoteKind.MARKDOWN_NON_TEXT)
            self.assertEqual(record.http_status, 200)

    def test_excluded_extension(self):
        config = RunConfig(
            base_url="https://example.com/docs",
            output_dir=self.tmp.name,
        )
        with patch("docsiphon.cli.fetch_markdown") as fetch_md:
            fetch_md.return_value = (None, "text/plain", FetchKind.MARKDOWN, 404, None, None, None, "not found")
            record = _fetch_one(
                "https://example.com/docs/file.pdf",
                config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.SKIPPED)
            self.assertEqual(record.note, NoteKind.EXCLUDED_EXTENSION)
            self.assertEqual(record.fetch_kind, FetchKind.NONE)
            self.assertEqual(record.http_status, 404)

    def test_html_fetch_failed(self):
        with patch("docsiphon.cli.fetch_markdown") as fetch_md, patch(
            "docsiphon.cli.fetch_html"
        ) as fetch_html:
            fetch_md.return_value = (None, None, FetchKind.MARKDOWN, None, None, None, None, None)
            fetch_html.return_value = (None, "text/html", 500, RuntimeError("err"), None, None)
            record = _fetch_one(
                "https://example.com/docs/a",
                self.config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.FAILED)
            self.assertEqual(record.note, NoteKind.HTML_FETCH_FAILED)
            self.assertEqual(record.http_status, 500)
            self.assertIsNotNone(record.error_snapshot)

    def test_html_fetch_failed_uses_markdown_snapshot(self):
        with patch("docsiphon.cli.fetch_markdown") as fetch_md, patch(
            "docsiphon.cli.fetch_html"
        ) as fetch_html:
            fetch_md.return_value = (None, "text/plain", FetchKind.MARKDOWN, 500, None, None, None, "md error")
            fetch_html.return_value = (None, "text/html", 500, None, None, None)
            record = _fetch_one(
                "https://example.com/docs/a",
                self.config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.FAILED)
            self.assertEqual(record.note, NoteKind.HTML_FETCH_FAILED)
            self.assertIsNotNone(record.error_snapshot)
            self.assertTrue(os.path.exists(record.error_snapshot))

    def test_html_non_text_content_type(self):
        with patch("docsiphon.cli.fetch_markdown") as fetch_md, patch(
            "docsiphon.cli.fetch_html"
        ) as fetch_html:
            fetch_md.return_value = (None, None, FetchKind.MARKDOWN, None, None, None, None, None)
            fetch_html.return_value = ("<html>ok</html>", "application/pdf", 200, None, None, None)
            record = _fetch_one(
                "https://example.com/docs/a",
                self.config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.SKIPPED)
            self.assertEqual(record.note, NoteKind.NON_TEXT_CONTENT_TYPE)
            self.assertEqual(record.fetch_kind, FetchKind.HTML)
            self.assertEqual(record.http_status, 200)

    def test_html_non_html_text(self):
        with patch("docsiphon.cli.fetch_markdown") as fetch_md, patch(
            "docsiphon.cli.fetch_html"
        ) as fetch_html:
            fetch_md.return_value = (None, None, FetchKind.MARKDOWN, None, None, None, None, None)
            fetch_html.return_value = ("plain text", "text/plain", 200, None, None, None)
            record = _fetch_one(
                "https://example.com/docs/a",
                self.config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.SKIPPED)
            self.assertEqual(record.note, NoteKind.NON_HTML_TEXT)
            self.assertIsNotNone(record.error_snapshot)

    def test_html_to_markdown_failed(self):
        with patch("docsiphon.cli.fetch_markdown") as fetch_md, patch(
            "docsiphon.cli.fetch_html"
        ) as fetch_html, patch("docsiphon.cli.html_to_markdown") as to_md:
            fetch_md.return_value = (None, None, FetchKind.MARKDOWN, None, None, None, None, None)
            fetch_html.return_value = ("<html>ok</html>", "text/html", 200, None, None, None)
            to_md.return_value = None
            record = _fetch_one(
                "https://example.com/docs/a",
                self.config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.FAILED)
            self.assertEqual(record.note, NoteKind.HTML_TO_MARKDOWN_FAILED)
            self.assertEqual(record.http_status, 200)

    def test_html_text_plain_with_html_body(self):
        with patch("docsiphon.cli.fetch_markdown") as fetch_md, patch(
            "docsiphon.cli.fetch_html"
        ) as fetch_html, patch("docsiphon.cli.html_to_markdown") as to_md, patch(
            "docsiphon.cli.write_markdown"
        ) as write_md:
            fetch_md.return_value = (None, None, FetchKind.MARKDOWN, None, None, None, None, None)
            fetch_html.return_value = ("<html>ok</html>", "text/plain", 200, None, None, None)
            to_md.return_value = "ok"
            write_md.return_value = ("/tmp/out.md", None)
            record = _fetch_one(
                "https://example.com/docs/a",
                self.config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.OK)
            self.assertEqual(record.fetch_kind, FetchKind.HTML)

    def test_html_success(self):
        with patch("docsiphon.cli.fetch_markdown") as fetch_md, patch(
            "docsiphon.cli.fetch_html"
        ) as fetch_html, patch("docsiphon.cli.html_to_markdown") as to_md, patch(
            "docsiphon.cli.write_markdown"
        ) as write_md:
            fetch_md.return_value = (None, None, FetchKind.MARKDOWN, None, None, None, None, None)
            fetch_html.return_value = ("<html>ok</html>", "text/html", 200, None, None, None)
            to_md.return_value = "ok"
            write_md.return_value = ("/tmp/out.md", None)
            record = _fetch_one(
                "https://example.com/docs/a",
                self.config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.OK)
            self.assertEqual(record.fetch_kind, FetchKind.HTML)
            self.assertEqual(record.bytes_written, len("ok".encode("utf-8")))
            self.assertEqual(record.http_status, 200)

    def test_markdown_oversize(self):
        with patch("docsiphon.cli.fetch_markdown") as fetch_md:
            fetch_md.return_value = (None, "text/plain", FetchKind.MARKDOWN, 200, OversizeError("big"), None, None, None)
            record = _fetch_one(
                "https://example.com/docs/a",
                self.config,
                self.limiter,
                self.host_limiter,
                self.host_concurrency,
                self.lock,
                self.manifest,
                None,
                {},
            )
            self.assertEqual(record.status, FetchStatus.SKIPPED)
            self.assertEqual(record.note, NoteKind.OVERSIZE)


if __name__ == "__main__":
    unittest.main()
