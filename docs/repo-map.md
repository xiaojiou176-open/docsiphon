---
title: Repo Map
description: Thin HTML repository map for the Docsiphon Pages surface.
---

# Repo Map

This page is the rendered HTML map for the Docsiphon `docs/` surface.

Use it when you want the shortest answer to "what lives where?" without reading
the full repository README first.

## Front Doors

- Full README:
  [GitHub repository front door](https://github.com/xiaojiou176-open/docsiphon#readme)
- Pages home:
  [Docs landing page](https://xiaojiou176-open.github.io/docsiphon/)
- Stable roadmap summary:
  [Roadmap](https://xiaojiou176-open.github.io/docsiphon/roadmap/)
- Latest release:
  [Release entrypoint](https://github.com/xiaojiou176-open/docsiphon/releases/latest)

## Repository Layout

- `src/docsiphon/`: CLI package and export pipeline implementation
- `scripts/`: contract checks, repository hygiene checks, and example probes
- `tests/`: automated verification for the CLI and support code
- `examples/`: copyable starter profiles and sample inputs
- `docs/`: this thin public Pages surface

## Execution Model

Docsiphon is a CLI-first export pipeline:

1. parse CLI arguments and optional profile settings
2. discover candidate URLs through `llms.txt`, sitemap, search index, or BFS
3. filter and normalize the candidate set
4. export pages through Markdown-first fetch with HTML fallback
5. write page artifacts and derived run artifacts

The repository does not expose a hosted API or service tier.

## Output Semantics

The supported output root is `_outputs/`.

Important run artifacts:

- `manifest.jsonl`: page-level export ledger
- `report.json`: run summary
- `index.json`: derived machine-readable index
- `toc.md`: directory tree view
- `report.html`: human-readable report
- `_errors/`: sampled error snapshots

Generated outputs are operator data and must stay out of Git.

## Verification Entry Points

For the full contributor verification commands, use
[`CONTRIBUTING.md`](../CONTRIBUTING.md). This page stays focused on the public
repository map and execution model.

## Support Boundary

- `scripts/verify_instructure.sh` is a public example probe, not a compatibility
  promise for every documentation vendor
- Releases are published from the GitHub releases page, not from the Pages
  surface
- `CODEOWNERS`, PR templates, and Issue templates are part of the collaboration
  contract
- `SUPPORT.md` defines the best-effort maintainer support scope
- `SECURITY.md` defines private reporting expectations
