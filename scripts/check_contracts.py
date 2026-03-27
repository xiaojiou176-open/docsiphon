#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "SUPPORT.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    ".env.example",
    "README.md",
    "docs/README.md",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
)

README_REQUIRED_SNIPPETS = (
    "## Why Docsiphon",
    "## Who It Is For",
    "## Quickstart",
    "## Common Commands",
    "## Real Example Output",
    "## Documentation",
    "## Verification",
    "## Collaboration",
    "## Development Environment",
    "## FAQ",
    "## License",
    "Security",
    "Contributing",
    "Docsiphon",
)

DOCS_README_REQUIRED_SNIPPETS = (
    "## Execution Model",
    "## Output Semantics",
    "## Verification Entry Points",
    "## Support Boundary",
    "## Canonical Sources",
    "thin but high-signal",
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

    security_path = repo_root / "SECURITY.md"
    if security_path.is_file():
        security_text = security_path.read_text(encoding="utf-8")
        for snippet in SECURITY_REQUIRED_SNIPPETS:
            if snippet not in security_text:
                errors.append(f"SECURITY.md missing required trust-boundary text: {snippet}")

    support_path = repo_root / "SUPPORT.md"
    if support_path.is_file():
        support_text = support_path.read_text(encoding="utf-8")
        for snippet in SUPPORT_REQUIRED_SNIPPETS:
            if snippet not in support_text:
                errors.append(f"SUPPORT.md missing required trust-boundary text: {snippet}")

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
