# ====================
# CLI profile merge tests
# ====================
import argparse
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from docsiphon import cli


class TestCliProfileMerge(unittest.TestCase):
    def test_main_profile_merge(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".toml") as f:
            f.write(
                "[profile]\n"
                "output_dir = \"/tmp/profile_out\"\n"
                "rate_limit_per_sec = 2.5\n"
                "host_rate_limit_per_sec = 1.0\n"
                "include_regex = \"/docs/\"\n"
                "exclude_regex = \"/private/\"\n"
                "ignore_query_params = [\"a\", \"b\"]\n"
                "ignore_query_prefixes = [\"utm_\"]\n"
                "content_extractor = \"raw\"\n"
                "save_html = true\n"
                "save_error_html = false\n"
                "ignore_robots = true\n"
                "headers = { \"X-API\" = \"profile\" }\n"
                "cookies = { \"sid\" = \"profile\" }\n"
                "auth = { username = \"puser\", password = \"ppass\" }\n"
                "token = \"ptoken\"\n"
            )
            profile_path = f.name

        args = SimpleNamespace(
            base_url="https://example.com/docs/start",
            out=None,
            site_root="auto",
            workers=None,
            timeout=None,
            rate=None,
            host_rate=None,
            host_concurrency=None,
            max_pages=None,
            max_depth=None,
            scope_prefix=None,
            frontmatter=None,
            frontmatter_no_timestamp=None,
            no_html=None,
            exclude_ext=[".pdf,.png"],
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
            header=["X-API: cli"],
            cookie=["sid=cli"],
            auth="cuser:cpass",
            token="ctoken",
            report_dir=None,
            profile=profile_path,
            profile_name=None,
            manifest_sorted=None,
            error_snapshot_max_bytes=None,
            error_snapshot_sample_ratio=None,
            error_snapshot_max_files=None,
            error_snapshot_max_total_bytes=None,
            user_agent=None,
            max_body_bytes=None,
            dry_run=None,
            resume=None,
            skip_existing=None,
            verbose=None,
            manifest_cache_max_entries=None,
        )

        captured = {}

        def _capture(config):
            captured["config"] = config
            return 0

        parser = argparse.ArgumentParser()
        with patch("docsiphon.cli.build_parser", return_value=parser), patch.object(
            parser, "parse_args", return_value=args
        ), patch("docsiphon.cli.run", side_effect=_capture), patch(
            "docsiphon.cli.sys.exit"
        ):
            cli.main()

        try:
            config = captured["config"]
            self.assertEqual(config.output_dir, "/tmp/profile_out")
            self.assertEqual(config.site_root, "start")
            self.assertEqual(config.rate_limit_per_sec, 2.5)
            self.assertEqual(config.host_rate_limit_per_sec, 1.0)
            self.assertEqual(config.include_regex, "/docs/")
            self.assertEqual(config.exclude_regex, "/private/")
            self.assertEqual(config.content_extractor, "raw")
            self.assertTrue(config.save_html)
            self.assertFalse(config.save_error_html)
            self.assertTrue(config.ignore_robots)
            self.assertEqual(config.headers.get("X-API"), "cli")
            self.assertEqual(config.cookies.get("sid"), "cli")
            self.assertEqual(config.auth, ("cuser", "cpass"))
            self.assertEqual(config.token, "ctoken")
            self.assertIn(".pdf", config.exclude_exts)
            self.assertIn(".png", config.exclude_exts)
        finally:
            Path(profile_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
