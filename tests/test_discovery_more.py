# ====================
# Discovery edge tests
# ====================
import json
import unittest
from unittest.mock import MagicMock, patch

import requests

from docsiphon.discovery import discover_llms_full, discover_llms_txt, discover_search_index, discover_sitemap
from tests.utils.server_utils import TestServer


class TestDiscoveryMore(unittest.TestCase):
    def test_discover_llms_txt_no_urls(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/llms.txt"] = (200, {"Content-Type": "text/plain"}, "not a url")
            session = requests.Session()
            result = discover_llms_txt(f"{base}/docs/start", session, 5)
            self.assertIsNone(result)

    def test_discover_llms_full_found(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/llms-full.txt"] = (200, {"Content-Type": "text/plain"}, "ok")
            session = requests.Session()
            url = discover_llms_full(f"{base}/docs/start", session, 5)
            self.assertEqual(url, f"{base}/llms-full.txt")

    def test_discover_sitemap_index(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/robots.txt"] = (
                200,
                {"Content-Type": "text/plain"},
                f"Sitemap: {base}/sitemap-index.xml",
            )
            routes["/sitemap-index.xml"] = (
                200,
                {"Content-Type": "application/xml"},
                (
                    "<?xml version='1.0' encoding='UTF-8'?>"
                    "<sitemapindex>"
                    f"<sitemap><loc>{base}/sitemap-sub.xml</loc></sitemap>"
                    "</sitemapindex>"
                ),
            )
            routes["/sitemap-sub.xml"] = (
                200,
                {"Content-Type": "application/xml"},
                (
                    "<?xml version='1.0' encoding='UTF-8'?>"
                    "<urlset>"
                    f"<url><loc>{base}/docs/a</loc></url>"
                    "</urlset>"
                ),
            )
            session = requests.Session()
            result = discover_sitemap(f"{base}/docs/start", session, 5)
            self.assertIsNotNone(result)
            self.assertEqual(result.urls, [f"{base}/docs/a"])

    def test_discover_sitemap_index_cycle(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/robots.txt"] = (
                200,
                {"Content-Type": "text/plain"},
                f"Sitemap: {base}/sitemap-index.xml",
            )
            routes["/sitemap-index.xml"] = (
                200,
                {"Content-Type": "application/xml"},
                (
                    "<?xml version='1.0' encoding='UTF-8'?>"
                    "<sitemapindex>"
                    f"<sitemap><loc>{base}/sitemap-index.xml</loc></sitemap>"
                    f"<sitemap><loc>{base}/sitemap-sub.xml</loc></sitemap>"
                    "</sitemapindex>"
                ),
            )
            routes["/sitemap-sub.xml"] = (
                200,
                {"Content-Type": "application/xml"},
                (
                    "<?xml version='1.0' encoding='UTF-8'?>"
                    "<urlset>"
                    f"<url><loc>{base}/docs/a</loc></url>"
                    "</urlset>"
                ),
            )
            session = requests.Session()
            result = discover_sitemap(f"{base}/docs/start", session, 5)
            self.assertIsNotNone(result)
            self.assertEqual(result.urls, [f"{base}/docs/a"])

    def test_discover_search_index_invalid_json(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/search_index.json"] = (200, {"Content-Type": "application/json"}, "{bad")
            session = requests.Session()
            result = discover_search_index(f"{base}/docs/start", session, 5)
            self.assertIsNone(result)

    def test_discover_sitemap_invalid_xml(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/sitemap.xml"] = (200, {"Content-Type": "application/xml"}, "<not-xml>")
            session = requests.Session()
            result = discover_sitemap(f"{base}/docs/start", session, 5)
            self.assertIsNone(result)

    def test_discover_sitemap_gzip_bad_content(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/sitemap.xml.gz"] = (200, {"Content-Type": "application/gzip"}, b"not-gzip")
            session = requests.Session()
            result = discover_sitemap(f"{base}/docs/start", session, 5)
            self.assertIsNone(result)

    def test_discover_llms_txt_respects_max_bytes(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/llms.txt"] = (200, {"Content-Type": "text/plain"}, (f"{base}/docs/a\n" * 50))
            session = requests.Session()
            result = discover_llms_txt(f"{base}/docs/start", session, 5, max_bytes=10)
            self.assertIsNone(result)

    def test_discover_search_index_respects_max_bytes(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/search_index.json"] = (
                200,
                {"Content-Type": "application/json"},
                json.dumps([{"url": f"/docs/{idx}"} for idx in range(50)]),
            )
            session = requests.Session()
            result = discover_search_index(f"{base}/docs/start", session, 5, max_bytes=20)
            self.assertIsNone(result)

    def test_discover_sitemap_respects_max_bytes(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            sitemap_xml = (
                "<?xml version='1.0' encoding='UTF-8'?>"
                "<urlset>"
                + "".join([f"<url><loc>{base}/docs/{idx}</loc></url>" for idx in range(40)])
                + "</urlset>"
            )
            routes["/sitemap.xml"] = (200, {"Content-Type": "application/xml"}, sitemap_xml)
            session = requests.Session()
            result = discover_sitemap(f"{base}/docs/start", session, 5, max_bytes=30)
            self.assertIsNone(result)

    def test_fetch_text_exception_path(self):
        session = MagicMock()
        session.get.side_effect = RuntimeError("boom")
        with patch("docsiphon.discovery.candidate_base_paths", return_value=["https://x"]):
            result = discover_llms_txt("https://x", session, 1, max_bytes=10)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
