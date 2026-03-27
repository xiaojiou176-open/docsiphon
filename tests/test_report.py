# ====================
# Report tests
# ====================
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from docsiphon.report import (
    write_report,
    write_url_list,
    write_index,
    write_toc,
    write_report_html,
    write_index_from_manifest,
    write_toc_from_manifest,
    write_report_html_from_manifest,
)
from docsiphon.models import ErrorKind, FetchKind, FetchStatus, PageRecord, SourceKind


class TestReport(unittest.TestCase):
    def test_write_report_and_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = {"ok": 1, "failed": 2}
            write_report(tmp, data)
            write_url_list(tmp, ["https://example.com/a", "https://example.com/b"])
            records = [
                PageRecord(
                    url="https://example.com/<script>",
                    fetched_url="https://example.com/<script>",
                    source=SourceKind.SITEMAP,
                    fetch_kind=FetchKind.HTML,
                    status=FetchStatus.FAILED,
                    out_path=os.path.join(tmp, "a.md"),
                    error_snapshot=os.path.join(tmp, "_errors", "a.txt"),
                    error_kind=ErrorKind.HTTP_4XX,
                )
            ]
            write_index(tmp, records)
            write_toc(tmp, records)
            write_report_html(tmp, {"ok": 1}, records)

            report_path = os.path.join(tmp, "report.json")
            urls_path = os.path.join(tmp, "urls.txt")
            index_path = os.path.join(tmp, "index.json")
            toc_path = os.path.join(tmp, "toc.md")
            report_html_path = os.path.join(tmp, "report.html")
            self.assertTrue(os.path.exists(report_path))
            self.assertTrue(os.path.exists(urls_path))
            self.assertTrue(os.path.exists(index_path))
            self.assertTrue(os.path.exists(toc_path))
            self.assertTrue(os.path.exists(report_html_path))

            with open(report_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.assertEqual(payload, data)

            with open(urls_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()]
            self.assertEqual(lines, ["https://example.com/a", "https://example.com/b"])
            self.assertGreater(os.path.getsize(report_path), 0)
            self.assertGreater(os.path.getsize(urls_path), 0)
            with open(report_html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            self.assertIn("&lt;script&gt;", html_content)
            self.assertIn("_errors/a.txt", html_content)
            self.assertIn("<a href=", html_content)
            with open(index_path, "r", encoding="utf-8") as f:
                index_payload = json.load(f)
            self.assertEqual(index_payload[0]["run_id"], None)

    def test_safe_rel_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = PageRecord(
                url="https://example.com/a",
                fetched_url="https://example.com/a",
                source=SourceKind.SITEMAP,
                fetch_kind=FetchKind.HTML,
                status=FetchStatus.OK,
                out_path=os.path.join(tmp, "a.md"),
            )
            with patch("docsiphon.report.os.path.relpath", side_effect=OSError("boom")):
                write_toc(tmp, [record])

    def test_write_report_html_handles_error(self):
        with patch("docsiphon.report.open", side_effect=OSError("nope")):
            write_report_html("/tmp", {}, [])

    def test_write_report_html_orders_by_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = [
                PageRecord(
                    url="https://example.com/b",
                    fetched_url="https://example.com/b",
                    source=SourceKind.SITEMAP,
                    fetch_kind=FetchKind.HTML,
                    status=FetchStatus.FAILED,
                ),
                PageRecord(
                    url="https://example.com/a",
                    fetched_url="https://example.com/a",
                    source=SourceKind.SITEMAP,
                    fetch_kind=FetchKind.HTML,
                    status=FetchStatus.FAILED,
                ),
            ]
            write_report_html(tmp, {"ok": 1}, records)
            report_html_path = os.path.join(tmp, "report.html")
            with open(report_html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            idx_a = html_content.find("https://example.com/a")
            idx_b = html_content.find("https://example.com/b")
            self.assertGreater(idx_b, idx_a)

    def test_write_from_manifest_streaming(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = os.path.join(tmp, "manifest.jsonl")
            payloads = [
                {
                    "url": "https://example.com/a",
                    "status": "ok",
                    "fetch_kind": "markdown",
                    "http_status": 200,
                    "content_type": "text/markdown",
                    "bytes_written": 10,
                    "out_path": os.path.join(tmp, "a.md"),
                    "note": None,
                    "error": None,
                    "error_kind": None,
                    "run_id": "run123",
                },
                {
                    "url": "https://example.com/b",
                    "status": "failed",
                    "fetch_kind": "html",
                    "http_status": 500,
                    "content_type": "text/html",
                    "bytes_written": 0,
                    "out_path": None,
                    "note": "html_fetch_failed",
                    "error": "oops",
                    "error_kind": "http_5xx",
                    "run_id": "run123",
                },
            ]
            with open(manifest_path, "w", encoding="utf-8") as f:
                for p in payloads:
                    f.write(json.dumps(p) + "\n")
            summary = {
                "run_id": "run123",
                "status_counts": {"ok": 1, "failed": 1},
                "http_status_counts": {"200": 1, "500": 1},
                "note_counts": {"html_fetch_failed": 1},
                "error_kind_counts": {"http_5xx": 1},
                "extractor_counts": {"none": 2},
            }
            write_index_from_manifest(manifest_path, tmp)
            write_toc_from_manifest(manifest_path, tmp)
            write_report_html_from_manifest(manifest_path, tmp, summary)
            index_path = os.path.join(tmp, "index.json")
            self.assertTrue(os.path.exists(index_path))
            self.assertTrue(os.path.exists(os.path.join(tmp, "toc.md")))
            report_html_path = os.path.join(tmp, "report.html")
            self.assertTrue(os.path.exists(report_html_path))
            with open(index_path, "r", encoding="utf-8") as f:
                index_payload = json.load(f)
            self.assertEqual(index_payload[0]["run_id"], "run123")
            with open(report_html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            self.assertIn("run123", html_content)

    def test_write_report_handles_error(self):
        with patch("docsiphon.report.os.makedirs", side_effect=OSError("nope")):
            write_report("/invalid/path", {"x": 1})

    def test_write_url_list_handles_error(self):
        with patch("docsiphon.report.os.makedirs", side_effect=OSError("nope")):
            write_url_list("/invalid/path", ["a"])

    def test_write_url_list_open_error(self):
        with patch("docsiphon.report.open", side_effect=OSError("nope")):
            write_url_list("/tmp", ["a"])


if __name__ == "__main__":
    unittest.main()
