# Documentation Map

This repository keeps a deliberately thin but high-signal docs surface.

Use the root [README](../README.md) as the front door. Use this file when you
need the repository map, the execution model, or the support boundary in one
place.

## Execution Model

Docsiphon is a CLI-driven export pipeline:

1. parse CLI arguments and optional profile settings
2. discover candidate URLs through `llms.txt`, sitemap, search index, or BFS
3. filter and normalize the candidate set
4. export each page through Markdown-first fetch with HTML fallback
5. write page artifacts and derived run artifacts

The source package lives in `src/docsiphon/`. The repository does not expose a
service layer or hosted API. Treat the root README as the landing page for
first-time users, and this file as the operator map for understanding what is
inside the repository.

## Output Semantics

The supported output root is `_outputs/`.

Important run artifacts:

- `manifest.jsonl`: page-level ledger
- `report.json`: run summary
- `index.json`: derived machine-readable index
- `toc.md`: directory tree view
- `report.html`: human-readable report
- `_errors/`: sampled error snapshots

Generated outputs are operator data and must stay out of Git.

## Verification Entry Points

```bash
uv run python scripts/check_contracts.py
uv run python scripts/check_repo_hygiene.py
uv run pre-commit run --all-files
uv run pytest tests
uv run docsiphon --help
```

## Support Boundary

- `scripts/verify_instructure.sh` is a public example probe, not a compatibility
  guarantee for every vendor
- `.github/release-body-v0.1.1.md` is a release draft artifact, not evidence
  that a public release tag already exists
- `CODEOWNERS`, PR templates, and Issue templates are part of the live
  collaboration contract
- `SECURITY.md` defines private reporting expectations
- `SUPPORT.md` defines the best-effort maintainer support scope

## Canonical Sources

- project overview and common commands: [README.md](../README.md)
- release draft for the next public polish pass: [../.github/release-body-v0.1.1.md](../.github/release-body-v0.1.1.md)
- contribution workflow: [CONTRIBUTING.md](../CONTRIBUTING.md)
- support policy: [SUPPORT.md](../SUPPORT.md)
- security reporting: [SECURITY.md](../SECURITY.md)
