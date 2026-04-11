---
title: Repo Map
description: Thin HTML repository map for the Docsiphon Pages surface.
---

# Repo Map

This page is the rendered HTML map for the Docsiphon `docs/` surface.

Use it when you want the shortest answer to "what lives where?" without reading
the full repository README first.

The current product front door still stays in `README.md` + the `uvx`
quickstart. This repo map is the Pages companion, not a second primary
surface.

## Front Doors

- Full README:
  [GitHub repository front door](https://github.com/xiaojiou176-open/docsiphon#readme)
- Pages home:
  [Docs landing page](https://xiaojiou176-open.github.io/docsiphon/)
- Stable roadmap summary:
  [Roadmap](https://xiaojiou176-open.github.io/docsiphon/roadmap/)
- Latest release:
  [Release entrypoint](https://github.com/xiaojiou176-open/docsiphon/releases/latest)

The rule behind this map is simple: current public onboarding still starts from
the CLI-first README and `uvx` quickstart. Any future MCP-aware surface remains
secondary until it has its own install contract, verification gate, public
packet, and lane truth.

## At A Glance

| Area | What lives here | Why it exists |
| --- | --- | --- |
| Front Door | README + `uvx` quickstart | Get visitors to a real first success fast |
| Execution Model | CLI-driven export pipeline | Explain how it works without pretending it is a hosted platform |
| Output Artifacts | `manifest.jsonl`, `report.json`, `index.json`, `toc.md`, `report.html` | Prove the result is reviewable, not a one-shot scrape |
| Support Boundary | `CLI-first`, no hosted API, future MCP stays secondary | Stop future ideas from being misread as current shipping surfaces |

## Repository Layout

- `src/docsiphon/`: CLI package and export pipeline implementation
- `scripts/`: contract checks, repository hygiene checks, and example probes
- `tests/`: automated verification for the CLI and support code
- `design-system/`: front-door hierarchy, proof ladder, and asset rules
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

## Release Shelf Truth

- Use the GitHub release entrypoint for the newest published artifacts and
  starter profiles.
- Use `README.md`, `docs/index.md`, and this map for the newest repository-side
  front-door truth on `main`.
- Do not compress those into one claim. A release shelf can lag behind current
  docs and governance wording until the next tagged cut is published.

## Verification Entry Points

For the full contributor verification commands, use
[`CONTRIBUTING.md`](../CONTRIBUTING.md). This page stays focused on the public
repository map and execution model.

## Support Boundary

- Any future MCP-aware surface remains future secondary until it ships its own
  install contract, verification gate, public packet, and lane truth
- `scripts/verify_instructure.sh` is a public example probe, not a compatibility
  promise for every documentation vendor
- Releases are published from the GitHub releases page, not from the Pages
  surface
- `CODEOWNERS`, PR templates, and Issue templates are part of the collaboration
  contract
- `SUPPORT.md` defines the best-effort maintainer support scope
- `SECURITY.md` defines private reporting expectations
