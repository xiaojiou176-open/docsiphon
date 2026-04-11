# ====================
# Script integrity tests
# ====================
import os
import re
import struct
import unittest
from pathlib import Path


class TestScripts(unittest.TestCase):
    def _read(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _png_size(self, path: Path) -> tuple[int, int]:
        data = path.read_bytes()
        return struct.unpack(">II", data[16:24])

    def _gif_size(self, path: Path) -> tuple[int, int]:
        data = path.read_bytes()
        return struct.unpack("<HH", data[6:10])

    def _svg_size(self, path: Path) -> tuple[int, int]:
        text = path.read_text(encoding="utf-8")
        match = re.search(r'width="(\d+)"\s+height="(\d+)"', text)
        self.assertIsNotNone(match)
        assert match is not None
        return int(match.group(1)), int(match.group(2))

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
        self.assertIn("DOCS_INDEX_REQUIRED_SNIPPETS", content)
        self.assertIn("REPO_MAP_REQUIRED_SNIPPETS", content)
        self.assertIn("PUBLIC_ENGLISH_FIRST_FILES", content)
        self.assertIn("DISALLOWED_PUBLIC_CJK_RE", content)
        self.assertIn("RELEASE_SHELF_TRUTH_REQUIRED_SNIPPETS", content)
        self.assertIn("DOCS_CONFIG_REQUIRED_SNIPPETS", content)
        self.assertIn("ROBOTS_REQUIRED_SNIPPETS", content)
        self.assertIn("SITEMAP_REQUIRED_SNIPPETS", content)
        self.assertIn("SECURITY_REQUIRED_SNIPPETS", content)
        self.assertIn("SECURITY_LEDGER_REQUIRED_SNIPPETS", content)
        self.assertIn("SUPPORT_REQUIRED_SNIPPETS", content)
        self.assertIn("LEDGER_REQUIRED_ITEMS", content)
        self.assertIn("RELEASE_EVIDENCE_REQUIRED_SNIPPETS", content)
        self.assertIn("AGENTS.md", content)
        self.assertIn("CLAUDE.md", content)
        self.assertIn("CITATION.cff", content)
        self.assertIn("README.md", content)
        self.assertIn("docs/README.md", content)
        self.assertIn("docs/repo-map.md", content)
        self.assertIn("docs/robots.txt", content)
        self.assertIn("docs/sitemap.xml", content)
        self.assertIn(".github/public-surface-ledger.yml", content)
        self.assertIn(".github/workflows/release-evidence.yml", content)
        self.assertIn("scripts/clean_local_state.py", content)
        self.assertIn("## Release Shelf Truth", content)
        self.assertIn("Why Docsiphon", content)
        self.assertIn("Quickstart", content)
        self.assertIn("Real Example Output", content)
        self.assertIn("Evidence Snapshot", content)
        self.assertIn("Community Pulse", content)
        self.assertIn("Verification Entry Points", content)
        self.assertIn("Security", content)
        self.assertIn("Contributing", content)
        self.assertIn("See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the full contributor verification", content)

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
        self.assertIn("CITATION.cff", content)
        self.assertIn(".DS_Store", content)
        self.assertIn(".egg-info", content)
        self.assertIn(".pre-commit-config.yaml", content)
        self.assertIn("docsite_md_exporter", content)
        self.assertIn("requirements.txt", content)
        self.assertIn("git ls-files", content)
        self.assertIn("unexpected root item present", content)
        self.assertIn("unsupported workflow present", content)
        self.assertIn("repo-map.md", content)
        self.assertIn("robots.txt", content)
        self.assertIn("sitemap.xml", content)
        self.assertIn("release-evidence.yml", content)

    def test_docs_tree_contains_current_pages_surface(self):
        docs_root = Path("docs")
        self.assertTrue((docs_root / "README.md").exists())
        self.assertTrue((docs_root / "index.md").exists())
        self.assertTrue((docs_root / "roadmap.md").exists())
        self.assertTrue((docs_root / "_config.yml").exists())
        self.assertTrue((docs_root / "repo-map.md").exists())
        self.assertTrue((docs_root / "robots.txt").exists())
        self.assertTrue((docs_root / "sitemap.xml").exists())
        self.assertEqual(
            {p.name for p in docs_root.iterdir()},
            {"README.md", "index.md", "roadmap.md", "_config.yml", "repo-map.md", "robots.txt", "sitemap.xml"},
        )

    def test_public_visual_assets_exist(self):
        assets_root = Path("assets")
        self.assertTrue((assets_root / "docsiphon-hero.svg").exists())
        self.assertTrue((assets_root / "docsiphon-before-after.svg").exists())
        self.assertTrue((assets_root / "docsiphon-social-preview.svg").exists())
        self.assertTrue((assets_root / "docsiphon-social-preview.png").exists())
        self.assertTrue((assets_root / "docsiphon-demo.gif").exists())

    def test_public_visual_assets_keep_expected_dimensions(self):
        assets_root = Path("assets")
        self.assertEqual(self._svg_size(assets_root / "docsiphon-hero.svg"), (1600, 980))
        self.assertEqual(self._svg_size(assets_root / "docsiphon-before-after.svg"), (1600, 920))
        self.assertEqual(self._svg_size(assets_root / "docsiphon-social-preview.svg"), (1280, 640))
        self.assertEqual(self._png_size(assets_root / "docsiphon-social-preview.png"), (1280, 640))
        self.assertEqual(self._gif_size(assets_root / "docsiphon-demo.gif"), (960, 540))

    def test_release_draft_exists(self):
        self.assertTrue(Path(".github/release-body-v0.1.1.md").exists())

    def test_agent_navigation_files_exist(self):
        self.assertTrue(Path("AGENTS.md").exists())
        self.assertTrue(Path("CLAUDE.md").exists())

    def test_workflow_surface_matches_current_truth(self):
        workflows = {path.name for path in Path(".github/workflows").glob("*.yml")}
        self.assertEqual(workflows, {"ci.yml", "codeql.yml", "release-evidence.yml"})

    def test_workflows_pin_full_length_shas(self):
        for workflow in Path(".github/workflows").glob("*.yml"):
            content = self._read(str(workflow))
            refs = re.findall(r"(?m)^\s*(?:-\s*)?uses:\s+[A-Za-z0-9_.\-/]+@([^\s]+)", content)
            self.assertTrue(refs, msg=f"{workflow} should contain at least one uses reference")
            for ref in refs:
                self.assertRegex(ref, r"^[0-9a-f]{40}$", msg=f"{workflow} uses non-pinned action ref: {ref}")

    def test_collaboration_templates_exist(self):
        self.assertTrue(Path(".github/CODEOWNERS").exists())
        self.assertTrue(Path(".github/pull_request_template.md").exists())
        self.assertTrue(Path(".github/ISSUE_TEMPLATE/bug_report.yml").exists())
        self.assertTrue(Path(".github/ISSUE_TEMPLATE/docs_site_compat.yml").exists())
        self.assertTrue(Path(".github/ISSUE_TEMPLATE/feature_request.yml").exists())
        self.assertTrue(Path(".github/ISSUE_TEMPLATE/config.yml").exists())

    def test_repo_metadata_files_exist(self):
        self.assertTrue(Path("CITATION.cff").exists())
        self.assertTrue(Path(".github/dependabot.yml").exists())
        self.assertTrue(Path(".github/release.yml").exists())

    def test_public_example_profiles_exist(self):
        self.assertTrue(Path("examples/README.md").exists())
        self.assertTrue(Path("examples/canvas-quickstart.toml").exists())
        self.assertTrue(Path("examples/rag-corpus.toml").exists())
        self.assertTrue(Path("examples/strict-audit.toml").exists())

    def test_release_body_mentions_docs_and_profiles(self):
        content = self._read(".github/release-body-v0.1.1.md")
        self.assertIn("Public evidence snapshot", content)
        self.assertIn("Downloadable starter profiles", content)
        self.assertIn("GitHub docs entry", content)
        self.assertIn("GitHub Pages landing page", content)

    def test_gitignore_covers_local_secret_file_patterns(self):
        content = self._read(".gitignore")
        self.assertIn(".env.*", content)
        self.assertIn("!.env.example", content)
        self.assertIn(".npmrc", content)
        self.assertIn(".pypirc", content)
        self.assertIn("credentials*.json", content)
        self.assertIn("secrets.yml", content)
        self.assertIn("secrets.yaml", content)
        self.assertNotIn("exported_docs/", content)
        self.assertNotIn("导出文档(exported_docs)/", content)

    def test_public_surface_ledger_exists_with_required_items(self):
        content = self._read(".github/public-surface-ledger.yml")
        self.assertIn("schema_version: 1", content)
        for item in (
            "description",
            "homepage",
            "topics",
            "discussions",
            "branch_protection_main",
            "release_shelf",
            "private_vulnerability_reporting",
            "custom_social_preview",
        ):
            self.assertIn(f"item: {item}", content)
        self.assertIn("status: verified", content)
        self.assertIn("status: manual_required", content)

    def test_public_front_doors_keep_english_primary_language(self):
        pattern = re.compile(r"[\u4e00-\u9fff]")
        for path in (
            "README.md",
            "docs/README.md",
            "docs/index.md",
            "docs/repo-map.md",
            "docs/roadmap.md",
        ):
            content = self._read(path)
            self.assertIsNone(
                pattern.search(content),
                msg=f"{path} should stay English-first on the public-facing surface",
            )

    def test_clean_local_state_script_exists_and_targets_noise(self):
        content = self._read("scripts/clean_local_state.py")
        self.assertIn("NOISE_PATTERNS", content)
        self.assertIn(".runtime-cache/temp", content)
        self.assertIn("__pycache__", content)
        self.assertIn("*.egg-info", content)
        self.assertIn("_outputs", content)

    def test_thin_docs_and_agent_files_point_to_contributing_for_full_verification(self):
        for path in ("AGENTS.md", "CLAUDE.md", "docs/README.md", "docs/repo-map.md"):
            content = self._read(path)
            self.assertIn("CONTRIBUTING.md", content)
            self.assertNotIn("uv run python scripts/check_contracts.py", content)
            self.assertNotIn("uv run python scripts/check_repo_hygiene.py", content)

    def test_pages_index_keeps_main_landmark_and_link_visibility_styles(self):
        content = self._read("docs/index.md")
        self.assertIn('<main id="main-content" role="main" markdown="1">', content)
        self.assertIn("text-decoration: underline;", content)
        self.assertIn("text-underline-offset: 0.16em;", content)


if __name__ == "__main__":
    unittest.main()
