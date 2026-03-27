# ====================
# E2E CLI test
# ====================
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.utils.server_utils import TestServer


class TestE2ECLI(unittest.TestCase):
    def test_cli_end_to_end_llms(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/llms.txt"] = (
                200,
                {"Content-Type": "text/plain"},
                f"{base}/docs/page\n",
            )
            routes["/docs/page.md"] = (
                200,
                {"Content-Type": "text/markdown"},
                "# Title\n\nBody\n",
            )

            with tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(__file__).resolve().parents[1]
                env = os.environ.copy()
                env["PYTHONPATH"] = f"{repo_root / 'src'}:{env.get('PYTHONPATH', '')}"
                cmd = [
                    sys.executable,
                    "-m",
                    "docsiphon.cli",
                    f"{base}/docs/start",
                    "--out",
                    tmp,
                    "--site-root",
                    "auto",
                    "--frontmatter",
                    "--frontmatter-no-timestamp",
                ]
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, msg=result.stderr)

                site_root = "start"
                markdown_path = os.path.join(tmp, site_root, "docs", "page.md")
                report_path = os.path.join(tmp, site_root, "report.json")
                urls_path = os.path.join(tmp, site_root, "urls.txt")
                manifest_path = os.path.join(tmp, site_root, "manifest.jsonl")

                self.assertTrue(os.path.exists(markdown_path))
                self.assertTrue(os.path.exists(report_path))
                self.assertTrue(os.path.exists(urls_path))
                self.assertTrue(os.path.exists(manifest_path))

                with open(markdown_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.assertIn("source_url:", content)
                self.assertNotIn("fetched_at_utc:", content)
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_lines = [line.strip() for line in f.readlines() if line.strip()]
                self.assertEqual(len(manifest_lines), 1)

    def test_cli_end_to_end_sitemap_html_fallback_resume(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/sitemap.xml"] = (
                200,
                {"Content-Type": "application/xml"},
                (
                    "<?xml version='1.0' encoding='UTF-8'?>"
                    "<urlset>"
                    f"<url><loc>{base}/docs/page</loc></url>"
                    f"<url><loc>{base}/docs/file.pdf</loc></url>"
                    "</urlset>"
                ),
            )
            routes["/docs/page.md"] = (404, {"Content-Type": "text/plain"}, "nope")
            routes["/docs/page"] = (
                200,
                {"Content-Type": "text/html"},
                "<html><body><main><h1>Doc</h1></main></body></html>",
            )
            routes["/docs/file.pdf"] = (200, {"Content-Type": "application/pdf"}, b"%PDF-1.4")

            with tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(__file__).resolve().parents[1]
                env = os.environ.copy()
                env["PYTHONPATH"] = f"{repo_root / 'src'}:{env.get('PYTHONPATH', '')}"
                cmd = [
                    sys.executable,
                    "-m",
                    "docsiphon.cli",
                    f"{base}/docs/start",
                    "--out",
                    tmp,
                    "--site-root",
                    "auto",
                    "--frontmatter-no-timestamp",
                    "--exclude-ext",
                    ".pdf",
                ]
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, msg=result.stderr)

                site_root = "start"
                report_path = os.path.join(tmp, site_root, "report.json")
                self.assertTrue(os.path.exists(report_path))
                with open(report_path, "r", encoding="utf-8") as f:
                    report = json.load(f)
                self.assertIn("note_counts", report)
                self.assertIn("excluded_extension", report["note_counts"])
                self.assertGreaterEqual(report["status_counts"]["ok"], 1)
                self.assertGreaterEqual(report["status_counts"]["skipped"], 1)

                # second run with resume should record not_modified if server replies 304
                routes["/docs/page.md"] = (304, {"Content-Type": "text/markdown"}, "")
                cmd_resume = cmd + ["--resume"]
                result_resume = subprocess.run(cmd_resume, env=env, capture_output=True, text=True)
                self.assertEqual(result_resume.returncode, 0, msg=result_resume.stderr)
                with open(report_path, "r", encoding="utf-8") as f:
                    report2 = json.load(f)
                self.assertIn("note_counts", report2)
                self.assertIn("not_modified", report2["note_counts"])
                manifest_path = os.path.join(tmp, site_root, "manifest.jsonl")
                with open(manifest_path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                self.assertGreaterEqual(len(lines), 2)

    def test_cli_end_to_end_retry_429(self):
        routes = {}
        with TestServer(routes) as server:
            base = server.base_url
            routes["/llms.txt"] = (
                200,
                {"Content-Type": "text/plain"},
                f"{base}/docs/page\n",
            )
            call_count = {"count": 0}

            def _page_md():
                call_count["count"] += 1
                if call_count["count"] == 1:
                    return (429, {"Content-Type": "text/plain"}, "rate limited")
                return (200, {"Content-Type": "text/markdown"}, "# OK\n")

            routes["/docs/page.md"] = _page_md

            with tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(__file__).resolve().parents[1]
                env = os.environ.copy()
                env["PYTHONPATH"] = f"{repo_root / 'src'}:{env.get('PYTHONPATH', '')}"
                cmd = [
                    sys.executable,
                    "-m",
                    "docsiphon.cli",
                    f"{base}/docs/start",
                    "--out",
                    tmp,
                    "--retry-429",
                    "1",
                    "--retry-backoff",
                    "0",
                ]
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                self.assertGreaterEqual(call_count["count"], 2)


if __name__ == "__main__":
    unittest.main()
