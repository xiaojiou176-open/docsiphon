#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "CITATION.cff",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "SUPPORT.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    ".env.example",
    "README.md",
    "docs/README.md",
    "docs/_config.yml",
    "docs/_layouts/default.html",
    "examples/README.md",
    "examples/canvas-quickstart.toml",
    "examples/rag-corpus.toml",
    "examples/strict-audit.toml",
    "docs/repo-map.md",
    "docs/robots.txt",
    "docs/sitemap.xml",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/release.yml",
    ".github/public-surface-ledger.yml",
    ".github/workflows/release-evidence.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/docs_site_compat.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/dependabot.yml",
    "scripts/clean_local_state.py",
)

README_REQUIRED_SNIPPETS = (
    "## Why Docsiphon",
    "## Who It Is For",
    "## Trade-offs / Not For",
    "## Quickstart",
    "## Common Commands",
    "## Real Example Output",
    "## Evidence Snapshot",
    "## Community Pulse",
    "## Release Shelf Truth",
    "## Documentation",
    "## Verification",
    "## Collaboration",
    "## Development Environment",
    "## FAQ",
    "## License",
    "examples/README.md",
    "See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the full contributor verification",
    "Security",
    "Contributing",
    "Docsiphon",
)

DOCS_README_REQUIRED_SNIPPETS = (
    "## Canonical Entrypoints",
    "## Release Shelf Truth",
    "## What Lives Where",
    "## Verification Entry Points",
    "## Support Boundary",
    "repo-side companion",
    "Docs landing page",
    "Repo map",
    "For the full contributor verification commands",
)

DOCS_INDEX_REQUIRED_SNIPPETS = (
    "## Fastest Path",
    "## Release Shelf Truth",
    "## Why It Exists",
    "## Best Fit",
    "GitHub repository front door",
    "Pages repo map",
)

REPO_MAP_REQUIRED_SNIPPETS = (
    "## Front Doors",
    "## Repository Layout",
    "## Execution Model",
    "## Output Semantics",
    "## Release Shelf Truth",
    "## Verification Entry Points",
    "## Support Boundary",
    "For the full contributor verification commands",
)

SECURITY_LEDGER_REQUIRED_SNIPPETS = (
    ".github/public-surface-ledger.yml",
    "private vulnerability reporting",
)

LEDGER_REQUIRED_ITEMS = (
    "description",
    "homepage",
    "topics",
    "discussions",
    "branch_protection_main",
    "release_shelf",
    "private_vulnerability_reporting",
    "custom_social_preview",
)

LEDGER_ALLOWED_STATUSES = {
    "verified",
    "manual_required",
    "unknown",
}

PUBLIC_ENGLISH_FIRST_FILES = (
    "README.md",
    "docs/README.md",
    "docs/index.md",
    "docs/repo-map.md",
    "docs/roadmap.md",
)

DISALLOWED_PUBLIC_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

RELEASE_SHELF_TRUTH_REQUIRED_SNIPPETS = {
    "README.md": (
        "newest **published**",
        "truth on `main`",
        "not the same shelf",
    ),
    "docs/README.md": (
        "newest published artifacts",
        "repository-side truth on",
        "newest tagged package set",
    ),
    "docs/index.md": (
        "published wheel, sdist, and starter-profile assets",
        "newest repository truth",
        "neighboring shelves",
    ),
    "docs/repo-map.md": (
        "newest published artifacts",
        "front-door truth on `main`",
        "Do not compress those into one claim",
    ),
}

RELEASE_EVIDENCE_REQUIRED_SNIPPETS = (
    "workflow_dispatch",
    "id-token: write",
    "attestations: write",
    "gh release upload",
)

DOCS_CONFIG_REQUIRED_SNIPPETS = (
    "url: https://xiaojiou176-open.github.io",
    "baseurl: /docsiphon",
)

ROBOTS_REQUIRED_SNIPPETS = (
    "User-agent: *",
    "Sitemap: https://xiaojiou176-open.github.io/docsiphon/sitemap.xml",
)

SITEMAP_REQUIRED_SNIPPETS = (
    "https://xiaojiou176-open.github.io/docsiphon/",
    "https://xiaojiou176-open.github.io/docsiphon/repo-map/",
    "https://xiaojiou176-open.github.io/docsiphon/roadmap/",
)

SECURITY_REQUIRED_SNIPPETS = (
    "Do **not** post vulnerability details in a public issue or PR.",
    "GitHub private vulnerability reporting",
)

SUPPORT_REQUIRED_SNIPPETS = (
    "best-effort",
    "repository map",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify repository governance files and README routing anchors."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to verify. Defaults to the current directory.",
    )
    return parser.parse_args()


def collect_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (repo_root / relative_path).is_file():
            errors.append(f"missing required file: {relative_path}")

    readme_path = repo_root / "README.md"
    if not readme_path.is_file():
        return errors

    readme_text = readme_path.read_text(encoding="utf-8")
    for snippet in README_REQUIRED_SNIPPETS:
        if snippet not in readme_text:
            errors.append(f"README.md missing required routing keyword: {snippet}")

    docs_readme_path = repo_root / "docs" / "README.md"
    if docs_readme_path.is_file():
        docs_readme_text = docs_readme_path.read_text(encoding="utf-8")
        for snippet in DOCS_README_REQUIRED_SNIPPETS:
            if snippet not in docs_readme_text:
                errors.append(f"docs/README.md missing required routing keyword: {snippet}")

    docs_index_path = repo_root / "docs" / "index.md"
    if docs_index_path.is_file():
        docs_index_text = docs_index_path.read_text(encoding="utf-8")
        for snippet in DOCS_INDEX_REQUIRED_SNIPPETS:
            if snippet not in docs_index_text:
                errors.append(f"docs/index.md missing required landing keyword: {snippet}")

    repo_map_path = repo_root / "docs" / "repo-map.md"
    if repo_map_path.is_file():
        repo_map_text = repo_map_path.read_text(encoding="utf-8")
        for snippet in REPO_MAP_REQUIRED_SNIPPETS:
            if snippet not in repo_map_text:
                errors.append(f"docs/repo-map.md missing required map keyword: {snippet}")

    docs_config_path = repo_root / "docs" / "_config.yml"
    if docs_config_path.is_file():
        docs_config_text = docs_config_path.read_text(encoding="utf-8")
        for snippet in DOCS_CONFIG_REQUIRED_SNIPPETS:
            if snippet not in docs_config_text:
                errors.append(f"docs/_config.yml missing required Pages config: {snippet}")

    robots_path = repo_root / "docs" / "robots.txt"
    if robots_path.is_file():
        robots_text = robots_path.read_text(encoding="utf-8")
        for snippet in ROBOTS_REQUIRED_SNIPPETS:
            if snippet not in robots_text:
                errors.append(f"docs/robots.txt missing required crawler policy text: {snippet}")

    sitemap_path = repo_root / "docs" / "sitemap.xml"
    if sitemap_path.is_file():
        sitemap_text = sitemap_path.read_text(encoding="utf-8")
        for snippet in SITEMAP_REQUIRED_SNIPPETS:
            if snippet not in sitemap_text:
                errors.append(f"docs/sitemap.xml missing required Pages URL: {snippet}")

    security_path = repo_root / "SECURITY.md"
    if security_path.is_file():
        security_text = security_path.read_text(encoding="utf-8")
        for snippet in SECURITY_REQUIRED_SNIPPETS:
            if snippet not in security_text:
                errors.append(f"SECURITY.md missing required trust-boundary text: {snippet}")
        for snippet in SECURITY_LEDGER_REQUIRED_SNIPPETS:
            if snippet not in security_text:
                errors.append(f"SECURITY.md missing required ledger-aware wording: {snippet}")

    support_path = repo_root / "SUPPORT.md"
    if support_path.is_file():
        support_text = support_path.read_text(encoding="utf-8")
        for snippet in SUPPORT_REQUIRED_SNIPPETS:
            if snippet not in support_text:
                errors.append(f"SUPPORT.md missing required trust-boundary text: {snippet}")

    ledger_path = repo_root / ".github" / "public-surface-ledger.yml"
    if ledger_path.is_file():
        ledger_text = ledger_path.read_text(encoding="utf-8")
        if "schema_version: 1" not in ledger_text:
            errors.append(".github/public-surface-ledger.yml missing schema_version: 1")
        if "items:" not in ledger_text:
            errors.append(".github/public-surface-ledger.yml missing items list")
        for item in LEDGER_REQUIRED_ITEMS:
            if f"item: {item}" not in ledger_text:
                errors.append(f".github/public-surface-ledger.yml missing required item: {item}")
        found_statuses = set()
        for line in ledger_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("status:"):
                found_statuses.add(stripped.split(":", 1)[1].strip())
        if not found_statuses:
            errors.append(".github/public-surface-ledger.yml missing status fields")
        invalid_statuses = found_statuses.difference(LEDGER_ALLOWED_STATUSES)
        for status in sorted(invalid_statuses):
            errors.append(f".github/public-surface-ledger.yml has invalid status: {status}")

    release_evidence_path = repo_root / ".github" / "workflows" / "release-evidence.yml"
    if release_evidence_path.is_file():
        release_evidence_text = release_evidence_path.read_text(encoding="utf-8")
        for snippet in RELEASE_EVIDENCE_REQUIRED_SNIPPETS:
            if snippet not in release_evidence_text:
                errors.append(f".github/workflows/release-evidence.yml missing required snippet: {snippet}")

    for relative_path in PUBLIC_ENGLISH_FIRST_FILES:
        path = repo_root / relative_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if DISALLOWED_PUBLIC_CJK_RE.search(text):
            errors.append(
                f"{relative_path} contains non-normalized Chinese text on the public English-first surface"
            )

    for relative_path, snippets in RELEASE_SHELF_TRUTH_REQUIRED_SNIPPETS.items():
        path = repo_root / relative_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                errors.append(
                    f"{relative_path} missing release-shelf truth detail: {snippet}"
                )

    return errors


def main() -> int:
    args = parse_args()
    repo_root = Path(args.root).resolve()
    errors = collect_errors(repo_root)

    if errors:
        print("Contract check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Contract check passed for {repo_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
