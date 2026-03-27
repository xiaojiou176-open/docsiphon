# ====================
# Fetch tests
# ====================
import unittest
from unittest.mock import MagicMock, patch

from docsiphon.config import RunConfig
from docsiphon.fetch import (
    OversizeError,
    _build_md_url,
    _pick_main_container,
    fetch_html,
    fetch_markdown,
    html_to_markdown,
)
from docsiphon.models import FetchKind


class _FakeResponse:
    def __init__(self, status_code: int, text: str, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class TestFetch(unittest.TestCase):
    def setUp(self) -> None:
        self.config = RunConfig(base_url="https://example.com/docs", output_dir="/tmp")

    def test_build_md_url(self):
        self.assertEqual(_build_md_url("https://example.com/a"), "https://example.com/a.md")
        self.assertEqual(_build_md_url("https://example.com/a.md"), "https://example.com/a.md")
        self.assertEqual(_build_md_url("https://example.com/a.md.txt"), "https://example.com/a.md.txt")

    def test_fetch_markdown_success(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(200, "# Title", {"content-type": "text/markdown"})
        text, content_type, kind, status, error, etag, last_modified, error_body = fetch_markdown(
            "https://example.com/a", session, self.config
        )
        self.assertEqual(text, "# Title")
        self.assertEqual(content_type, "text/markdown")
        self.assertEqual(kind, FetchKind.MARKDOWN)
        self.assertEqual(status, 200)
        self.assertIsNone(error)
        self.assertIsNone(error_body)

    def test_fetch_markdown_html_disguised(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(200, "<html>no</html>", {"content-type": "text/html"})
        text, content_type, kind, status, error, etag, last_modified, error_body = fetch_markdown(
            "https://example.com/a", session, self.config
        )
        self.assertIsNone(text)
        self.assertEqual(content_type, "text/html")
        self.assertEqual(kind, FetchKind.MARKDOWN)
        self.assertEqual(status, 200)
        self.assertIsNone(error)
        self.assertEqual(error_body, "<html>no</html>")
        self.assertTrue(session.get.called)

    def test_fetch_markdown_non_text(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(200, "%PDF-1.4", {"content-type": "application/pdf"})
        text, content_type, kind, status, error, etag, last_modified, error_body = fetch_markdown(
            "https://example.com/a", session, self.config
        )
        self.assertIsNone(text)
        self.assertEqual(content_type, "application/pdf")
        self.assertEqual(kind, FetchKind.MARKDOWN)
        self.assertEqual(status, 200)
        self.assertIsNone(error)
        self.assertIsNone(error_body)

    def test_fetch_markdown_html_in_text_plain(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(200, "<!doctype html><html></html>", {"content-type": "text/plain"})
        text, content_type, kind, status, error, etag, last_modified, error_body = fetch_markdown(
            "https://example.com/a", session, self.config
        )
        self.assertIsNone(text)
        self.assertEqual(content_type, "text/plain")
        self.assertEqual(kind, FetchKind.MARKDOWN)
        self.assertEqual(status, 200)
        self.assertIsNone(error)
        self.assertEqual(error_body, "<!doctype html><html></html>")

    def test_fetch_markdown_status_not_ok(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(404, "no", {"content-type": "text/plain"})
        text, content_type, kind, status, error, etag, last_modified, error_body = fetch_markdown(
            "https://example.com/a", session, self.config
        )
        self.assertIsNone(text)
        self.assertEqual(content_type, "text/plain")
        self.assertEqual(kind, FetchKind.MARKDOWN)
        self.assertEqual(status, 404)
        self.assertIsNone(error)
        self.assertEqual(error_body, "no")

    def test_fetch_markdown_md_txt(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(200, "ok", {"content-type": "text/plain"})
        text, content_type, kind, status, error, etag, last_modified, error_body = fetch_markdown(
            "https://example.com/a.md.txt", session, self.config
        )
        self.assertEqual(text, "ok")
        self.assertEqual(kind, FetchKind.MARKDOWN_TXT)
        self.assertEqual(status, 200)
        self.assertIsNone(error)
        self.assertIsNone(error_body)

    def test_fetch_markdown_exception(self):
        session = MagicMock()
        session.get.side_effect = RuntimeError("boom")
        text, content_type, kind, status, error, etag, last_modified, error_body = fetch_markdown(
            "https://example.com/a", session, self.config
        )
        self.assertIsNone(text)
        self.assertIsNone(content_type)
        self.assertEqual(kind, FetchKind.MARKDOWN)
        self.assertIsNone(status)
        self.assertIsNotNone(error)
        self.assertIsNone(error_body)

    def test_fetch_markdown_oversize(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(200, "# Title", {"content-length": "100", "content-type": "text/plain"})
        config = RunConfig(base_url="https://example.com/docs", output_dir="/tmp", max_body_bytes=10)
        text, content_type, kind, status, error, etag, last_modified, error_body = fetch_markdown(
            "https://example.com/a", session, config
        )
        self.assertIsNone(text)
        self.assertIsInstance(error, OversizeError)

    def test_fetch_html_success(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(200, "<html>ok</html>", {"content-type": "text/html"})
        text, content_type, status, error, etag, last_modified = fetch_html("https://example.com/a", session, self.config)
        self.assertEqual(text, "<html>ok</html>")
        self.assertEqual(content_type, "text/html")
        self.assertEqual(status, 200)
        self.assertIsNone(error)

    def test_fetch_html_status_not_ok(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(500, "err", {"content-type": "text/html"})
        text, content_type, status, error, etag, last_modified = fetch_html("https://example.com/a", session, self.config)
        self.assertEqual(text, "err")
        self.assertEqual(content_type, "text/html")
        self.assertEqual(status, 500)
        self.assertIsNone(error)

    def test_fetch_html_exception(self):
        session = MagicMock()
        session.get.side_effect = RuntimeError("oops")
        text, content_type, status, error, etag, last_modified = fetch_html("https://example.com/a", session, self.config)
        self.assertIsNone(text)
        self.assertIsNone(content_type)
        self.assertIsNone(status)
        self.assertIsNotNone(error)

    def test_fetch_html_oversize(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(200, "<html>ok</html>", {"content-length": "999"})
        config = RunConfig(base_url="https://example.com/docs", output_dir="/tmp", max_body_bytes=10)
        text, content_type, status, error, etag, last_modified = fetch_html("https://example.com/a", session, config)
        self.assertIsNone(text)
        self.assertIsInstance(error, OversizeError)

    def test_fetch_html_oversize_body(self):
        session = MagicMock()
        session.get.return_value = _FakeResponse(200, "<html>" + ("x" * 100) + "</html>", {"content-type": "text/html"})
        config = RunConfig(base_url="https://example.com/docs", output_dir="/tmp", max_body_bytes=10)
        text, content_type, status, error, etag, last_modified = fetch_html("https://example.com/a", session, config)
        self.assertIsNone(text)
        self.assertIsInstance(error, OversizeError)

    def test_html_to_markdown_success(self):
        html = "<html><body><main><h1>Title</h1></main></body></html>"
        md = html_to_markdown(html)
        self.assertIn("# Title", md or "")

    def test_pick_main_container_article(self):
        html = "<html><body><article><h2>Hi</h2></article></body></html>"
        fragment = _pick_main_container(html)
        self.assertIn("<article>", fragment)

    def test_pick_main_container_body(self):
        html = "<html><body><div>Body</div></body></html>"
        fragment = _pick_main_container(html)
        self.assertIn("<body>", fragment)

    def test_pick_main_container_fallback(self):
        html = "<div>No body</div>"
        fragment = _pick_main_container(html)
        self.assertEqual(fragment, html)

    def test_html_to_markdown_failure(self):
        with patch("docsiphon.fetch.md_convert", side_effect=RuntimeError("bad")):
            html = "<html><body><p>oops</p></body></html>"
            md = html_to_markdown(html)
            self.assertIsNone(md)


if __name__ == "__main__":
    unittest.main()
