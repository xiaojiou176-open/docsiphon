# ====================
# Crawl edge tests
# ====================
import unittest

from docsiphon.config import RunConfig
from docsiphon.crawl import _in_scope, _scope_prefix


class TestCrawlMore(unittest.TestCase):
    def test_scope_prefix_root(self):
        config = RunConfig(base_url="https://example.com/", output_dir="/tmp")
        self.assertEqual(_scope_prefix(config), "/")
        config2 = RunConfig(base_url="https://example.com", output_dir="/tmp")
        self.assertEqual(_scope_prefix(config2), "/")

    def test_scope_prefix_file(self):
        config = RunConfig(base_url="https://example.com/docs/index.html", output_dir="/tmp")
        self.assertEqual(_scope_prefix(config), "/docs")
        config2 = RunConfig(base_url="https://example.com/docs/dir/", output_dir="/tmp")
        self.assertEqual(_scope_prefix(config2), "/docs/dir")

    def test_in_scope(self):
        base = "https://example.com/docs/start"
        self.assertTrue(_in_scope("https://example.com/docs/a", "/docs", base))
        self.assertFalse(_in_scope("https://other.com/docs/a", "/docs", base))
        self.assertFalse(_in_scope("https://example.com/other/a", "/docs", base))


if __name__ == "__main__":
    unittest.main()
