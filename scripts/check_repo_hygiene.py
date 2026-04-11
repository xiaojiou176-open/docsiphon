#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


OLD_OUTPUT_ROOTS = (
    "exported_docs",
    "导出文档(exported_docs)",
)

NOISE_FILE_NAMES = {
    ".DS_Store",
}

NOISE_DIR_SUFFIXES = (
    ".egg-info",
    "__pycache__",
)

TEXT_SCAN_ROOTS = (
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "assets",
    "design-system",
    "examples",
    "scripts",
    "src",
    "tests",
    "docs",
    ".github",
)

TEXT_SCAN_EXCLUDED_DIRS = {
    "docs/history",
    ".agents",
    ".git",
    ".venv",
    ".pytest_cache",
    "_outputs",
    "__pycache__",
}

TEXT_SCAN_EXCLUDED_FILES = {
    "scripts/check_repo_hygiene.py",
    "tests/test_scripts.py",
}

LEGACY_CURRENT_SURFACE_TERMS = (
    "docsite_md_exporter",
    "requirements.txt",
)

ROOT_ALLOWLIST = {
    "AGENTS.md",
    ".devcontainer",
    ".env.example",
    ".github",
    ".gitignore",
    ".pre-commit-config.yaml",
    "assets",
    "CHANGELOG.md",
    "CLAUDE.md",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "design-system",
    "docs",
    "examples",
    "LICENSE",
    "pyproject.toml",
    "README.md",
    "scripts",
    "SECURITY.md",
    "src",
    "SUPPORT.md",
    "tests",
    "uv.lock",
}

LOCAL_ONLY_ROOT_ITEMS = {
    ".agents",
    ".pytest_cache",
    ".venv",
    ".vscode",
    "_outputs",
}

ALLOWED_WORKFLOWS = {
    "ci.yml",
    "codeql.yml",
    "release-evidence.yml",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check for legacy output roots and repository hygiene drift."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to verify. Defaults to the current directory.",
    )
    return parser.parse_args()


def _is_excluded(path: Path) -> bool:
    normalized = path.as_posix()
    return any(
        normalized == excluded or normalized.startswith(f"{excluded}/")
        for excluded in TEXT_SCAN_EXCLUDED_DIRS
    )


def _is_git_ignored(repo_root: Path, rel_path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(rel_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def collect_legacy_reference_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []

    for relative in TEXT_SCAN_ROOTS:
        candidate = repo_root / relative
        if not candidate.exists():
            continue

        if candidate.is_file():
            files = [candidate]
        else:
            files = [
                path for path in candidate.rglob("*")
                if path.is_file() and not _is_excluded(path.relative_to(repo_root))
            ]

        for path in files:
            rel = path.relative_to(repo_root)
            if rel.as_posix() == ".gitignore":
                continue
            if rel.as_posix() in TEXT_SCAN_EXCLUDED_FILES:
                continue
            if rel.suffix == ".pyc":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for old_root in OLD_OUTPUT_ROOTS:
                if old_root in text:
                    errors.append(f"legacy output root reference found in {rel}: {old_root}")

    return errors


def collect_legacy_current_surface_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []

    for relative in TEXT_SCAN_ROOTS:
        candidate = repo_root / relative
        if not candidate.exists():
            continue

        if candidate.is_file():
            files = [candidate]
        else:
            files = [
                path for path in candidate.rglob("*")
                if path.is_file() and not _is_excluded(path.relative_to(repo_root))
            ]

        for path in files:
            rel = path.relative_to(repo_root)
            if rel.as_posix() in TEXT_SCAN_EXCLUDED_FILES:
                continue
            if rel.suffix == ".pyc":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for legacy_term in LEGACY_CURRENT_SURFACE_TERMS:
                if legacy_term in text:
                    errors.append(f"legacy current-surface reference found in {rel}: {legacy_term}")

    return errors


def collect_noise_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []

    for path in repo_root.rglob("*"):
        rel = path.relative_to(repo_root)
        if _is_excluded(rel):
            continue
        if _is_git_ignored(repo_root, rel):
            continue
        if path.name in NOISE_FILE_NAMES:
            errors.append(f"noise file present: {rel}")
        if path.is_dir() and path.name.endswith(NOISE_DIR_SUFFIXES):
            errors.append(f"noise directory present: {rel}")

    return errors


def collect_tracked_output_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return [f"git ls-files failed with exit code {result.returncode}"]

    tracked_paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    forbidden_prefixes = (
        "_outputs/",
        "exported_docs/",
        "导出文档(exported_docs)/",
    )
    forbidden_suffixes = (
        ".DS_Store",
    )

    for tracked in tracked_paths:
        tracked_path = repo_root / tracked
        if not tracked_path.exists():
            continue
        if tracked.startswith(forbidden_prefixes):
            errors.append(f"tracked generated output present: {tracked}")
        if tracked.endswith(forbidden_suffixes):
            errors.append(f"tracked noise file present: {tracked}")

    return errors


def collect_root_allowlist_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in repo_root.iterdir():
        rel = path.relative_to(repo_root)
        if path.name == ".git":
            continue
        if path.name in LOCAL_ONLY_ROOT_ITEMS:
            continue
        if _is_git_ignored(repo_root, rel):
            continue
        if path.name not in ROOT_ALLOWLIST:
            errors.append(f"unexpected root item present: {path.name}")
    return errors


def collect_workflow_allowlist_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    workflows_dir = repo_root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return errors

    for path in workflows_dir.glob("*.yml"):
        if path.name not in ALLOWED_WORKFLOWS:
            errors.append(f"unsupported workflow present: .github/workflows/{path.name}")

    return errors


def collect_docs_surface_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    docs_root = repo_root / "docs"
    allowed_docs_files = {
        "README.md",
        "index.md",
        "roadmap.md",
        "_config.yml",
        "repo-map.md",
        "robots.txt",
        "sitemap.xml",
        "default.html",
    }
    allowed_docs_dirs = {
        docs_root / "_layouts",
    }

    if not docs_root.is_dir():
        errors.append("docs directory missing")
        return errors

    for path in docs_root.rglob("*"):
        rel = path.relative_to(repo_root)
        if path.is_dir():
            if path != docs_root and path not in allowed_docs_dirs:
                errors.append(f"unexpected docs directory present: {rel}")
            continue
        if path.name not in allowed_docs_files:
            errors.append(f"unexpected docs file present: {rel}")

    return errors


def collect_agent_navigation_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for required in ("AGENTS.md", "CLAUDE.md"):
        if not (repo_root / required).is_file():
            errors.append(f"missing agent navigation file: {required}")
    return errors


def collect_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(collect_legacy_reference_errors(repo_root))
    errors.extend(collect_legacy_current_surface_errors(repo_root))
    errors.extend(collect_noise_errors(repo_root))
    errors.extend(collect_tracked_output_errors(repo_root))
    errors.extend(collect_root_allowlist_errors(repo_root))
    errors.extend(collect_workflow_allowlist_errors(repo_root))
    errors.extend(collect_docs_surface_errors(repo_root))
    errors.extend(collect_agent_navigation_errors(repo_root))
    return errors


def main() -> int:
    args = parse_args()
    repo_root = Path(args.root).resolve()
    errors = collect_errors(repo_root)

    if errors:
        print("Repository hygiene check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Repository hygiene check passed for {repo_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
