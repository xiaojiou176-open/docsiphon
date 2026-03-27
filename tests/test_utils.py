import unittest
from unittest.mock import patch

from docsiphon.utils import (
    candidate_base_paths,
    build_exclude_exts,
    is_excluded_by_extension,
    is_textual_content_type,
    matches_filters,
    compile_regex,
    classify_http_error,
    classify_exception,
    parse_header_args,
    parse_cookie_args,
    filter_same_origin,
    normalize_url,
    normalize_content_type,
    normalize_extension,
    same_origin,
    safe_relative_path,
    safe_relative_path_from_base,
    sanitize_segment,
    RateLimiter,
    HostConcurrencyLimiter,
    compute_backoff,
)


class TestUtils(unittest.TestCase):
    def test_normalize_url_removes_fragment(self):
        self.assertEqual(
            normalize_url("https://example.com/docs/page#section"),
            "https://example.com/docs/page",
        )
        self.assertEqual(
            normalize_url("HTTPS://EXAMPLE.COM/docs/page/"),
            "https://example.com/docs/page",
        )
        self.assertEqual(
            normalize_url("https://Example.Com/Path"),
            "https://example.com/Path",
        )
        self.assertEqual(
            normalize_url(
                "https://example.com/docs/page?utm_source=1&b=2",
                ignore_query_prefixes=("utm_",),
            ),
            "https://example.com/docs/page?b=2",
        )
        self.assertEqual(
            normalize_url("http://example.com:80/docs/page"),
            "http://example.com/docs/page",
        )
        self.assertEqual(
            normalize_url("https://example.com:443/docs/page"),
            "https://example.com/docs/page",
        )

    def test_safe_relative_path(self):
        self.assertEqual(safe_relative_path("https://example.com/"), "index")
        self.assertEqual(safe_relative_path("https://example.com/docs/intro"), "docs/intro")

    def test_safe_relative_path_from_base(self):
        base_url = "https://example.com/services/canvas"
        self.assertEqual(
            safe_relative_path_from_base("https://example.com/services/canvas", base_url, "canvas"),
            "canvas",
        )
        self.assertEqual(
            safe_relative_path_from_base("https://example.com/services/canvas/outcomes", base_url, "canvas"),
            "outcomes",
        )
        self.assertEqual(
            safe_relative_path_from_base("https://example.com/other/path", base_url, "canvas"),
            "other/path",
        )

    def test_safe_relative_path_query_normalization(self):
        a = safe_relative_path("https://example.com/docs/page?a=1&b=2")
        b = safe_relative_path("https://example.com/docs/page?b=2&a=1")
        c = safe_relative_path("https://example.com/docs/page?a=1&b=3")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertTrue(safe_relative_path("https://example.com/?a=1").startswith("index__q_"))

    def test_safe_relative_path_windows_reserved(self):
        self.assertNotEqual(safe_relative_path("https://example.com/con"), "con")

    def test_exclude_extensions_normalization(self):
        exts = build_exclude_exts(["pdf,.PNG", " .zip "])
        self.assertIn(".pdf", exts)
        self.assertIn(".png", exts)
        self.assertIn(".zip", exts)
        self.assertIn(".pdf", build_exclude_exts([]))

    def test_is_excluded_by_extension(self):
        exts = build_exclude_exts([])
        self.assertTrue(is_excluded_by_extension("https://example.com/file.pdf", exts))
        self.assertFalse(is_excluded_by_extension("https://example.com/docs/page", exts))
        self.assertFalse(is_excluded_by_extension("https://example.com/docs/page.txt", {".md"}))

    def test_textual_content_type(self):
        self.assertTrue(is_textual_content_type("text/html; charset=utf-8"))
        self.assertTrue(is_textual_content_type("text/plain"))
        self.assertTrue(is_textual_content_type("application/xhtml+xml"))
        self.assertFalse(is_textual_content_type("application/pdf"))
        self.assertEqual(normalize_content_type("text/html; charset=utf-8"), "text/html")

    def test_candidate_base_paths_and_origin(self):
        bases = candidate_base_paths("https://example.com/docs/start")
        self.assertIn("https://example.com", bases)
        self.assertIn("https://example.com/docs", bases)
        self.assertIn("https://example.com/docs/start", bases)
        self.assertTrue(same_origin("https://example.com/a", "https://example.com/b"))
        self.assertFalse(same_origin("https://example.com/a", "https://other.com/a"))

    def test_filters_and_parsers(self):
        include = compile_regex("docs")
        exclude = compile_regex("private")
        self.assertTrue(matches_filters("https://example.com/docs/a", include, exclude))
        self.assertFalse(matches_filters("https://example.com/private/a", include, exclude))
        self.assertIsNone(compile_regex("[bad"))
        self.assertEqual(classify_http_error(429), "http_429")
        self.assertEqual(classify_http_error(404), "http_4xx")
        self.assertEqual(classify_http_error(500), "http_5xx")
        headers = parse_header_args(["X-API: token", "Bad"])
        self.assertEqual(headers.get("X-API"), "token")
        cookies = parse_cookie_args(["sid=abc", "bad"])
        self.assertEqual(cookies.get("sid"), "abc")
        filtered = filter_same_origin(
            ["https://example.com/a", "https://other.com/b"], "https://example.com/base"
        )
        self.assertEqual(filtered, ["https://example.com/a"])

    def test_classify_exception(self):
        import requests

        self.assertEqual(classify_exception(requests.exceptions.Timeout()), "timeout")
        self.assertEqual(classify_exception(requests.exceptions.ConnectionError()), "connection")

    def test_normalize_extension(self):
        self.assertEqual(normalize_extension("PDF"), ".pdf")
        self.assertEqual(normalize_extension(".png"), ".png")
        self.assertEqual(normalize_extension(""), "")

    def test_sanitize_segment_and_long_hash(self):
        self.assertEqual(sanitize_segment("."), "_")
        long_name = "a" * 200
        sanitized = sanitize_segment(long_name)
        self.assertLess(len(sanitized), len(long_name))
        self.assertIn("_", sanitized)

    def test_rate_limiter_wait(self):
        limiter = RateLimiter(10.0)
        with patch(
            "docsiphon.utils.time.monotonic",
            side_effect=[0.0, 0.0, 0.05, 0.2, 0.25, 0.3],
        ), patch(
            "docsiphon.utils.time.sleep"
        ) as sleep_mock:
            limiter.wait()
            limiter.wait()
            sleep_mock.assert_called()

    def test_min_nonzero(self):
        from docsiphon.utils import min_nonzero

        self.assertEqual(min_nonzero(0, 2.0), 2.0)
        self.assertEqual(min_nonzero(2.0, 0), 2.0)
        self.assertEqual(min_nonzero(2.0, 3.0), 2.0)

    def test_compute_backoff(self):
        delay = compute_backoff(1, 0.5, 2.0, 0.0)
        self.assertEqual(delay, 0.5)
        delay2 = compute_backoff(3, 0.5, 1.0, 0.0)
        self.assertEqual(delay2, 1.0)

    def test_host_concurrency_limiter(self):
        limiter = HostConcurrencyLimiter(1)
        with limiter.slot("example.com"):
            self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
