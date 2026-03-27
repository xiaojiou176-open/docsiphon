# ====================
# Crawl tests
# ====================
import unittest

import requests

from docsiphon.config import RunConfig
from docsiphon.crawl import crawl_site
from tests.utils.server_utils import TestServer


class TestCrawl(unittest.TestCase):
    def test_crawl_scope_and_static_filter(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/docs/index"] = (
                200,
                {"Content-Type": "text/html"},
                (
                    "<html><body>"
                    "<a href='/docs/a'>A</a>"
                    "<a href='/docs/dir/'>Dir</a>"
                    "<a href='/static/file.pdf'>PDF</a>"
                    "</body></html>"
                ),
            )
            routes["/docs/a"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body><a href='/docs/b'>B</a></body></html>",
            )
            routes["/docs/b"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body>OK</body></html>",
            )
            routes["/docs/dir/"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body><a href='/docs/dir/page'>P</a></body></html>",
            )
            routes["/docs/dir"] = routes["/docs/dir/"]
            routes["/docs/dir/page"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body>OK</body></html>",
            )
            routes["/static/file.pdf"] = (
                200,
                {"Content-Type": "application/pdf"},
                b"%PDF-1.4",
            )

            config = RunConfig(
                base_url=f"{base}/docs/index",
                output_dir="/tmp",
                max_pages=50,
                max_depth=3,
                rate_limit_per_sec=0,
            )
            session = requests.Session()
            result = crawl_site(config, session)
            self.assertIn(f"{base}/docs/index", result.urls)
            self.assertIn(f"{base}/docs/a", result.urls)
            self.assertIn(f"{base}/docs/b", result.urls)
            self.assertIn(f"{base}/docs/dir/page", result.urls)
            self.assertNotIn(f"{base}/static/file.pdf", result.urls)

    def test_crawl_respects_max_depth_and_normalizes_query(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/docs/index"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body><a href='/docs/a?b=2&a=1'>A</a></body></html>",
            )
            routes["/docs/a"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body><a href='/docs/deep'>Deep</a></body></html>",
            )
            routes["/docs/deep"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body>Deep</body></html>",
            )

            config = RunConfig(
                base_url=f"{base}/docs/index",
                output_dir="/tmp",
                max_pages=50,
                max_depth=1,
                rate_limit_per_sec=0,
            )
            session = requests.Session()
            result = crawl_site(config, session)
            self.assertIn(f"{base}/docs/index", result.urls)
            self.assertIn(f"{base}/docs/a?a=1&b=2", result.urls)
            self.assertNotIn(f"{base}/docs/deep", result.urls)

    def test_crawl_respects_robots(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/robots.txt"] = (
                200,
                {"Content-Type": "text/plain"},
                "User-agent: *\nDisallow: /docs/secret\n",
            )
            routes["/docs/index"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body><a href='/docs/secret'>S</a><a href='/docs/ok'>O</a></body></html>",
            )
            routes["/docs/ok"] = (200, {"Content-Type": "text/html"}, "<html><body>OK</body></html>")
            routes["/docs/secret"] = (200, {"Content-Type": "text/html"}, "<html><body>NO</body></html>")

            config = RunConfig(
                base_url=f"{base}/docs/index",
                output_dir="/tmp",
                max_pages=10,
                max_depth=2,
                rate_limit_per_sec=0,
            )
            session = requests.Session()
            result = crawl_site(config, session)
            self.assertIn(f"{base}/docs/ok", result.urls)
            self.assertNotIn(f"{base}/docs/secret", result.urls)

            config_ignore = RunConfig(
                base_url=f"{base}/docs/index",
                output_dir="/tmp",
                max_pages=10,
                max_depth=2,
                rate_limit_per_sec=0,
                ignore_robots=True,
            )
            result_ignore = crawl_site(config_ignore, session)
            self.assertIn(f"{base}/docs/secret", result_ignore.urls)

    def test_crawl_skips_non_html_and_oversize(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/docs/index"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body>"
                "<a href='/docs/plain'>Plain</a>"
                "<a href='/docs/large'>Large</a>"
                "</body></html>",
            )
            routes["/docs/plain"] = (200, {"Content-Type": "text/plain"}, "just text")
            routes["/docs/large"] = (
                200,
                {"Content-Type": "text/html"},
                "<html>" + ("x" * 200) + "</html>",
            )

            config = RunConfig(
                base_url=f"{base}/docs/index",
                output_dir="/tmp",
                max_pages=50,
                max_depth=2,
                rate_limit_per_sec=0,
                max_body_bytes=120,
            )
            session = requests.Session()
            result = crawl_site(config, session)
            self.assertIn(f"{base}/docs/index", result.urls)
            self.assertNotIn(f"{base}/docs/plain", result.urls)
            self.assertNotIn(f"{base}/docs/large", result.urls)


if __name__ == "__main__":
    unittest.main()
