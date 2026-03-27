#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


NOISE_PATTERNS = (
    "build",
    "htmlcov",
    ".pytest_cache",
    ".runtime-cache/temp",
    "**/__pycache__",
    "**/*.egg-info",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove local-only rebuildable noise without touching operator data such as _outputs/."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually remove the matched paths. Without this flag the script only prints a dry-run plan.",
    )
    return parser.parse_args()


def collect_targets(repo_root: Path) -> list[Path]:
    targets: set[Path] = set()
    for pattern in NOISE_PATTERNS:
        for candidate in repo_root.glob(pattern):
            if candidate == repo_root / "_outputs":
                continue
            if ".venv" in candidate.parts:
                continue
            if candidate.exists():
                targets.add(candidate)
    return sorted(targets, key=lambda path: path.as_posix())


def main() -> int:
    args = parse_args()
    repo_root = Path(".").resolve()
    targets = collect_targets(repo_root)

    if not targets:
        print("No local noise targets found.")
        return 0

    mode = "Removing" if args.apply else "Would remove"
    for target in targets:
        rel = target.relative_to(repo_root)
        print(f"{mode}: {rel}")
        if not args.apply:
            continue
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        else:
            target.unlink(missing_ok=True)

    if not args.apply:
        print("Dry run only. Re-run with --apply to delete these paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
