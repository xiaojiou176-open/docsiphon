# ====================
# Script integrity tests
# ====================
import os
import unittest
from pathlib import Path


class TestScripts(unittest.TestCase):
    def _read(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_batch_export_script_structure(self):
        self.assertFalse(Path("scripts/batch_export.sh").exists())

    def test_verify_instructure_script_structure(self):
        path = os.path.join("scripts", "verify_instructure.sh")
        content = self._read(path)
        self.assertTrue(content.startswith("#!/usr/bin/env bash"))
        self.assertIn("set -euo pipefail", content)
        self.assertIn("developerdocs.instructure.com", content)
        self.assertIn("robots.txt", content)
        self.assertIn("sitemap.xml", content)

    def test_check_contracts_script_structure(self):
        path = os.path.join("scripts", "check_contracts.py")
        content = self._read(path)
        self.assertIn("REQUIRED_FILES", content)
        self.assertIn("README_REQUIRED_SNIPPETS", content)
        self.assertIn("DOCS_README_REQUIRED_SNIPPETS", content)
        self.assertIn("SECURITY_REQUIRED_SNIPPETS", content)
        self.assertIn("SUPPORT_REQUIRED_SNIPPETS", content)
        self.assertIn("AGENTS.md", content)
        self.assertIn("CLAUDE.md", content)
        self.assertIn("README.md", content)
        self.assertIn("docs/README.md", content)
        self.assertIn("Why Docsiphon", content)
        self.assertIn("Quickstart", content)
        self.assertIn("Real Example Output", content)
        self.assertIn("Verification Entry Points", content)
        self.assertIn("Security", content)
        self.assertIn("Contributing", content)

    def test_check_repo_hygiene_script_structure(self):
        path = os.path.join("scripts", "check_repo_hygiene.py")
        content = self._read(path)
        self.assertIn("OLD_OUTPUT_ROOTS", content)
        self.assertIn("LEGACY_CURRENT_SURFACE_TERMS", content)
        self.assertIn("ROOT_ALLOWLIST", content)
        self.assertIn("ALLOWED_WORKFLOWS", content)
        self.assertIn("collect_docs_surface_errors", content)
        self.assertIn("collect_agent_navigation_errors", content)
        self.assertIn("AGENTS.md", content)
        self.assertIn("CLAUDE.md", content)
        self.assertIn("assets", content)
        self.assertIn(".DS_Store", content)
        self.assertIn(".egg-info", content)
        self.assertIn(".pre-commit-config.yaml", content)
        self.assertIn("docsite_md_exporter", content)
        self.assertIn("requirements.txt", content)
        self.assertIn("git ls-files", content)
        self.assertIn("unexpected root item present", content)
        self.assertIn("unsupported workflow present", content)

    def test_docs_tree_contains_current_and_history_layers(self):
        docs_root = Path("docs")
        self.assertTrue((docs_root / "README.md").exists())
        self.assertEqual({p.name for p in docs_root.iterdir()}, {"README.md"})

    def test_public_visual_assets_exist(self):
        assets_root = Path("assets")
        self.assertTrue((assets_root / "docsiphon-hero.svg").exists())
        self.assertTrue((assets_root / "docsiphon-before-after.svg").exists())
        self.assertTrue((assets_root / "docsiphon-social-preview.svg").exists())
        self.assertTrue((assets_root / "docsiphon-social-preview.png").exists())
        self.assertTrue((assets_root / "docsiphon-demo.gif").exists())

    def test_release_draft_exists(self):
        self.assertTrue(Path(".github/release-body-v0.1.1.md").exists())

    def test_agent_navigation_files_exist(self):
        self.assertTrue(Path("AGENTS.md").exists())
        self.assertTrue(Path("CLAUDE.md").exists())

    def test_workflow_surface_matches_current_truth(self):
        workflows = {path.name for path in Path(".github/workflows").glob("*.yml")}
        self.assertEqual(workflows, {"ci.yml", "codeql.yml"})

    def test_collaboration_templates_exist(self):
        self.assertTrue(Path(".github/CODEOWNERS").exists())
        self.assertTrue(Path(".github/pull_request_template.md").exists())
        self.assertTrue(Path(".github/ISSUE_TEMPLATE/bug_report.yml").exists())
        self.assertTrue(Path(".github/ISSUE_TEMPLATE/feature_request.yml").exists())
        self.assertTrue(Path(".github/ISSUE_TEMPLATE/config.yml").exists())

    def test_gitignore_covers_local_secret_file_patterns(self):
        content = self._read(".gitignore")
        self.assertIn(".env.*", content)
        self.assertIn("!.env.example", content)
        self.assertIn(".npmrc", content)
        self.assertIn(".pypirc", content)
        self.assertIn("credentials*.json", content)
        self.assertIn("secrets.yml", content)
        self.assertIn("secrets.yaml", content)


if __name__ == "__main__":
    unittest.main()
