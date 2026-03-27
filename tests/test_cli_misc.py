# ====================
# CLI misc tests
# ====================
import argparse
import os
import tempfile
import unittest
import threading
from types import SimpleNamespace
from unittest.mock import patch

from docsiphon import cli
from docsiphon.config import RunConfig
from docsiphon.models import FetchKind, FetchStatus, PageRecord, SourceKind
from docsiphon.utils import HostConcurrencyLimiter, HostRateLimiter, RateLimiter


class TestCliMisc(unittest.TestCase):
    def test_markdown_url_and_site_root(self):
        self.assertEqual(cli._markdown_url("https://example.com/a"), "https://example.com/a.md")
        self.assertEqual(cli._markdown_url("https://example.com/a.md"), "https://example.com/a.md")
        self.assertEqual(cli._derive_site_root("https://example.com/docs/start"), "start")
        self.assertIsNone(cli._derive_site_root("https://example.com/"))

    def test_report_dir_site_root(self):
        config = RunConfig(base_url="x", output_dir="/tmp/out", site_root="CON")
        path = cli._report_dir(config)
        self.assertIn("/tmp/out", path)
        self.assertTrue(path.endswith("_CON_"))

    def test_filter_by_scope(self):
        urls = ["https://example.com/docs/a", "https://example.com/other/b"]
        filtered = cli._filter_by_scope(urls, "docs")
        self.assertEqual(filtered, ["https://example.com/docs/a"])
        filtered2 = cli._filter_by_scope(urls, "/docs")
        self.assertEqual(filtered2, ["https://example.com/docs/a"])

    def test_filter_by_scope_exception_path(self):
        urls = ["https://example.com/docs/a"]
        with patch("urllib.parse.urlparse", side_effect=RuntimeError("bad")):
            filtered = cli._filter_by_scope(urls, "/docs")
        self.assertEqual(filtered, [])

    def test_dedupe_by_output_path_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs", output_dir=tmp)
            with patch("docsiphon.cli.build_output_path", side_effect=RuntimeError("boom")):
                deduped, collisions = cli._dedupe_by_output_path(["https://example.com/docs/a"], config)
            self.assertEqual(deduped, ["https://example.com/docs/a"])
            self.assertEqual(collisions, [])

    def test_summarize_results(self):
        results = [
            PageRecord(
                url="u1",
                fetched_url="u1",
                source=SourceKind.SITEMAP,
                fetch_kind=FetchKind.MARKDOWN,
                status=FetchStatus.OK,
                http_status=200,
                content_type="text/html; charset=utf-8",
            ),
            PageRecord(
                url="u2",
                fetched_url="u2",
                source=SourceKind.SITEMAP,
                fetch_kind=FetchKind.HTML,
                status=FetchStatus.FAILED,
                http_status=None,
                content_type=None,
                error="err",
            ),
        ]
        summary = cli._summarize_results(results)
        self.assertEqual(summary["status_counts"]["ok"], 1)
        self.assertEqual(summary["status_counts"]["failed"], 1)
        self.assertEqual(summary["http_status_counts"]["none"], 1)
        self.assertEqual(summary["content_type_counts"]["text/html"], 1)
        self.assertEqual(summary["error_count"], 1)

    def test_convert_html_auto_fallback(self):
        html = "<html><body><main><h1>Title</h1></main></body></html>"
        with patch("docsiphon.cli.html_to_markdown") as to_md:
            to_md.side_effect = [None, None, "ok"]
            md, extractor = cli._convert_html(html, RunConfig(base_url="x", output_dir="/tmp"))
        self.assertEqual(md, "ok")

    def test_call_with_retry_timeout(self):
        attempts = {"count": 0}

        def _fetch():
            attempts["count"] += 1
            if attempts["count"] == 1:
                import requests

                return (None, None, FetchKind.MARKDOWN, None, requests.exceptions.Timeout(), None, None, None)
            return ("ok", "text/plain", FetchKind.MARKDOWN, 200, None, None, None, None)

        config = RunConfig(
            base_url="https://example.com/docs",
            output_dir="/tmp",
            retry_timeout=1,
            retry_connection=0,
            retry_dns=0,
            retry_http_429=0,
            retry_http_5xx=0,
            retry_unknown=0,
            retry_backoff_base=0.0,
            retry_backoff_max=0.0,
            retry_backoff_jitter=0.0,
        )
        with patch("docsiphon.cli.time.sleep") as sleep_mock:
            result = cli._call_with_retry(
                _fetch,
                RateLimiter(0),
                HostRateLimiter(0),
                HostConcurrencyLimiter(0),
                threading.Lock(),
                "example.com",
                config,
                3,
                4,
            )
        self.assertEqual(result[0], "ok")
        self.assertEqual(attempts["count"], 2)
        sleep_mock.assert_not_called()

    def test_extract_markdown_h1_skips_frontmatter(self):
        text = "---\nsource: x\n---\n\n# Title\n\nBody"
        h1 = cli._extract_markdown_h1(text)
        self.assertEqual(h1, "Title")

    def test_run_no_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs", output_dir=tmp)
            discovery = SimpleNamespace(urls=[], source=SourceKind.SITEMAP)
            with patch("docsiphon.cli.discover_llms_txt", return_value=discovery):
                code = cli.run(config)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(os.path.join(tmp, "report.json")))

    def test_run_fallback_to_crawl(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = RunConfig(base_url="https://example.com/docs", output_dir=tmp, dry_run=True)
            discovery = SimpleNamespace(urls=["https://example.com/docs/a"], source=SourceKind.BFS)
            with patch("docsiphon.cli.discover_llms_txt", return_value=None), patch(
                "docsiphon.cli.discover_sitemap", return_value=None
            ), patch("docsiphon.cli.discover_search_index", return_value=None), patch(
                "docsiphon.cli.crawl_site", return_value=discovery
            ):
                code = cli.run(config)
            self.assertEqual(code, 0)

    def test_main_keyboard_interrupt(self):
        args = SimpleNamespace(
            base_url="https://example.com/docs",
            out="/tmp",
            site_root=None,
            workers=1,
            timeout=1,
            rate=1.0,
            host_rate=None,
            host_concurrency=None,
            max_pages=10,
            max_depth=2,
            scope_prefix=None,
            frontmatter=False,
            frontmatter_no_timestamp=False,
            no_html=False,
            exclude_ext=[],
            include_regex=None,
            exclude_regex=None,
            ignore_query=None,
            ignore_query_prefix=None,
            content_extractor=None,
            save_html=None,
            save_error_html=None,
            ignore_robots=None,
            retry=None,
            retry_timeout=None,
            retry_connection=None,
            retry_dns=None,
            retry_429=None,
            retry_5xx=None,
            retry_unknown=None,
            retry_backoff=None,
            retry_backoff_max=None,
            retry_jitter=None,
            header=None,
            cookie=None,
            auth=None,
            token=None,
            report_dir=None,
            profile=None,
            profile_name=None,
            manifest_sorted=None,
            error_snapshot_max_bytes=None,
            error_snapshot_sample_ratio=None,
            error_snapshot_max_files=None,
            error_snapshot_max_total_bytes=None,
            user_agent=None,
            max_body_bytes=None,
            dry_run=False,
            resume=False,
            skip_existing=False,
            verbose=False,
            manifest_cache_max_entries=None,
        )

        parser = argparse.ArgumentParser()
        with patch("docsiphon.cli.build_parser", return_value=parser), patch.object(
            parser, "parse_args", return_value=args
        ), patch("docsiphon.cli.run", side_effect=KeyboardInterrupt), patch(
            "docsiphon.cli.sys.exit"
        ) as exit_mock:
            cli.main()
            exit_mock.assert_called_with(130)

    def test_main_exception(self):
        args = SimpleNamespace(
            base_url="https://example.com/docs",
            out="/tmp",
            site_root=None,
            workers=1,
            timeout=1,
            rate=1.0,
            host_rate=None,
            host_concurrency=None,
            max_pages=10,
            max_depth=2,
            scope_prefix=None,
            frontmatter=False,
            frontmatter_no_timestamp=False,
            no_html=False,
            exclude_ext=[],
            include_regex=None,
            exclude_regex=None,
            ignore_query=None,
            ignore_query_prefix=None,
            content_extractor=None,
            save_html=None,
            save_error_html=None,
            ignore_robots=None,
            retry=None,
            retry_timeout=None,
            retry_connection=None,
            retry_dns=None,
            retry_429=None,
            retry_5xx=None,
            retry_unknown=None,
            retry_backoff=None,
            retry_backoff_max=None,
            retry_jitter=None,
            header=None,
            cookie=None,
            auth=None,
            token=None,
            report_dir=None,
            profile=None,
            profile_name=None,
            manifest_sorted=None,
            error_snapshot_max_bytes=None,
            error_snapshot_sample_ratio=None,
            error_snapshot_max_files=None,
            error_snapshot_max_total_bytes=None,
            user_agent=None,
            max_body_bytes=None,
            dry_run=False,
            resume=False,
            skip_existing=False,
            verbose=False,
            manifest_cache_max_entries=None,
        )
        parser = argparse.ArgumentParser()
        with patch("docsiphon.cli.build_parser", return_value=parser), patch.object(
            parser, "parse_args", return_value=args
        ), patch("docsiphon.cli.run", side_effect=RuntimeError("boom")), patch(
            "docsiphon.cli.sys.exit"
        ) as exit_mock:
            cli.main()
            exit_mock.assert_called_with(1)


if __name__ == "__main__":
    unittest.main()
