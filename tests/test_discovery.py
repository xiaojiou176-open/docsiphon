# ====================
# Discovery tests
# ====================
import gzip
import json
import unittest

import requests

from docsiphon.discovery import discover_llms_txt, discover_search_index, discover_sitemap
from docsiphon.models import SourceKind
from tests.utils.server_utils import TestServer


class TestDiscovery(unittest.TestCase):
    def test_discover_llms_txt(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/llms.txt"] = (
                200,
                {"Content-Type": "text/plain"},
                f"{base}/docs/a\n{base}/docs/b\nhttps://other.com/x\n",
            )
            session = requests.Session()
            result = discover_llms_txt(f"{base}/docs/start", session, 5)
            self.assertIsNotNone(result)
            self.assertEqual(result.source, SourceKind.LLMS_TXT)
            self.assertEqual(sorted(result.urls), sorted([f"{base}/docs/a", f"{base}/docs/b"]))

    def test_discover_sitemap_gz_and_relative_loc(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            sitemap_xml = (
                "<?xml version='1.0' encoding='UTF-8'?>"
                "<urlset>"
                "<url><loc>/docs/rel</loc></url>"
                f"<url><loc>{base}/docs/abs</loc></url>"
                "</urlset>"
            )
            routes["/sitemap.xml.gz"] = (
                200,
                {"Content-Type": "application/gzip"},
                gzip.compress(sitemap_xml.encode("utf-8")),
            )
            session = requests.Session()
            result = discover_sitemap(f"{base}/docs/start", session, 5)
            self.assertIsNotNone(result)
            self.assertEqual(result.source, SourceKind.SITEMAP)
            self.assertEqual(sorted(result.urls), sorted([f"{base}/docs/rel", f"{base}/docs/abs"]))

    def test_discover_search_index(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            data = [{"url": "/docs/a"}, {"location": f"{base}/docs/b"}]
            routes["/search_index.json"] = (
                200,
                {"Content-Type": "application/json"},
                json.dumps(data),
            )
            session = requests.Session()
            result = discover_search_index(f"{base}/docs/start", session, 5)
            self.assertIsNotNone(result)
            self.assertEqual(result.source, SourceKind.SEARCH_INDEX)
            self.assertEqual(sorted(result.urls), sorted([f"{base}/docs/a", f"{base}/docs/b"]))


if __name__ == "__main__":
    unittest.main()
