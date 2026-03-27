# ====================
# CLI run tests
# ====================
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from docsiphon.cli import run
from docsiphon.config import RunConfig
from docsiphon.models import DiscoveryResult, FetchKind, FetchStatus, NoteKind, PageRecord, SourceKind


class TestCliRun(unittest.TestCase):
    def test_run_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs", output_dir=tmp, dry_run=True)
            discovery = DiscoveryResult(source=SourceKind.SITEMAP, urls=["https://example.com/docs/a"])
            with patch("docsiphon.cli.discover_llms_txt", return_value=discovery), patch(
                "docsiphon.cli.discover_llms_full", return_value=None
            ):
                code = run(config)
            self.assertEqual(code, 0)
            urls_path = os.path.join(tmp, "urls.txt")
            self.assertTrue(os.path.exists(urls_path))
            with open(urls_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()]
            self.assertEqual(lines, ["https://example.com/docs/a"])

    def test_run_with_collisions_resume_and_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(
                base_url="https://example.com/docs",
                output_dir=tmp,
                resume=True,
                skip_existing=True,
            )
            urls = ["https://example.com/docs"]
            discovery = DiscoveryResult(source=SourceKind.LLMS_TXT, urls=urls)

            # create existing file to trigger skip_existing
            out_path = os.path.join(tmp, "docs.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("existing")

            with patch("docsiphon.cli.discover_llms_txt", return_value=discovery), patch(
                "docsiphon.cli.discover_llms_full", return_value=None
            ), patch("docsiphon.cli._fetch_one") as fetch_one:
                fetch_one.return_value = PageRecord(
                    url="https://example.com/docs/other",
                    fetched_url="https://example.com/docs/other",
                    source=SourceKind.LLMS_TXT,
                    fetch_kind=FetchKind.HTML,
                    status=FetchStatus.OK,
                    bytes_written=2,
                )
                code = run(config)
                self.assertEqual(fetch_one.call_count, 0)

            self.assertEqual(code, 0)
            report_path = os.path.join(tmp, "report.json")
            self.assertTrue(os.path.exists(report_path))
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            self.assertIn("run_id", report)
            self.assertIn("started_at_utc", report)
            self.assertEqual(report["path_collisions"], 0)
            self.assertIn("note_counts", report)
            self.assertIn(NoteKind.SKIP_EXISTING.value, report["note_counts"])
            self.assertEqual(report["scheduled_urls"], 0)

    def test_run_respects_robots_delay(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(
                base_url="https://example.com/docs",
                output_dir=tmp,
            )
            discovery = DiscoveryResult(source=SourceKind.SITEMAP, urls=["https://example.com/docs/a"])

            class _Robots:
                def can_fetch(self, ua, url):
                    return True

                def crawl_delay(self, ua):
                    return 2.0

            rates = {"global": None, "host": None}

            class _Limiter:
                def __init__(self, rate):
                    rates["global"] = rate

                def wait(self):
                    return None

            class _HostLimiter:
                def __init__(self, rate):
                    rates["host"] = rate

                def wait(self, host):
                    return None

            with patch("docsiphon.cli.discover_llms_txt", return_value=discovery), patch(
                "docsiphon.cli.discover_llms_full", return_value=None
            ), patch("docsiphon.cli._load_robots", return_value=_Robots()), patch(
                "docsiphon.cli.RateLimiter", side_effect=_Limiter
            ), patch(
                "docsiphon.cli.HostRateLimiter", side_effect=_HostLimiter
            ), patch(
                "docsiphon.cli._fetch_one"
            ) as fetch_one:
                fetch_one.return_value = PageRecord(
                    url="https://example.com/docs/a",
                    fetched_url="https://example.com/docs/a",
                    source=SourceKind.SITEMAP,
                    fetch_kind=FetchKind.HTML,
                    status=FetchStatus.OK,
                )
                code = run(config)

            self.assertEqual(code, 0)
            self.assertEqual(rates["global"], 0.5)
            self.assertEqual(rates["host"], 0.5)

    def test_run_applies_max_pages_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs", output_dir=tmp, max_pages=1)
            discovery = DiscoveryResult(
                source=SourceKind.SITEMAP,
                urls=[
                    "https://example.com/docs/b",
                    "https://example.com/docs/a",
                    "https://example.com/docs/c",
                ],
            )
            with patch("docsiphon.cli.discover_llms_txt", return_value=discovery), patch(
                "docsiphon.cli.discover_llms_full", return_value=None
            ), patch("docsiphon.cli._fetch_one") as fetch_one:
                fetch_one.return_value = PageRecord(
                    url="https://example.com/docs/a",
                    fetched_url="https://example.com/docs/a",
                    source=SourceKind.SITEMAP,
                    fetch_kind=FetchKind.HTML,
                    status=FetchStatus.OK,
                )
                code = run(config)

            self.assertEqual(code, 0)
            report_path = os.path.join(tmp, "report.json")
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            self.assertIn("run_id", report)
            self.assertIn("started_at_utc", report)
            self.assertEqual(report["scheduled_urls"], 1)
            self.assertEqual(report["limited_urls"], 2)
            self.assertIn(NoteKind.MAX_PAGES_LIMIT.value, report["note_counts"])
            urls_path = os.path.join(tmp, "urls.txt")
            with open(urls_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()]
            self.assertEqual(lines, ["https://example.com/docs/a"])


if __name__ == "__main__":
    unittest.main()
