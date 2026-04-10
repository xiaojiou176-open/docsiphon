---
title: Docs Surface README
description: Thin repository-side companion for the Docsiphon Pages surface.
---

# Docs Surface README

This file is the repo-side companion to the Pages docs surface.

Use the GitHub repo front door when you want the full onboarding story. Use the
rendered Pages map when you want the shortest HTML path through the public docs
surface.

This thin Pages surface follows the same current boundary as the repo front
door: Docsiphon is still `CLI-first` today, and any future MCP-aware secondary
surface stays outside this Pages entry path until it earns its own install
contract, verification gate, public packet, and lane truth.

The current product front door still lives in `README.md` + the `uvx`
quickstart. This Pages companion stays a thin routing surface, not a second
primary surface.

## Canonical Entrypoints

- Full README:
  [GitHub repository front door](https://github.com/xiaojiou176-open/docsiphon#readme)
- Pages home:
  [Docs landing page](https://xiaojiou176-open.github.io/docsiphon/)
- Pages repo map:
  [Repo map](https://xiaojiou176-open.github.io/docsiphon/repo-map/)
- Pages roadmap:
  [Roadmap](https://xiaojiou176-open.github.io/docsiphon/roadmap/)
- Latest public release:
  [Release entrypoint](https://github.com/xiaojiou176-open/docsiphon/releases/latest)

## What Lives Where

- `docs/index.md`: the smallest public landing page for Pages visitors
- `docs/repo-map.md`: the rendered HTML map for repository structure and support
  boundaries
- `docs/roadmap.md`: the stable public roadmap summary
- `README.md`: the full project front door with install, usage, and verification
  guidance

## Verification Entry Points

For the full contributor verification commands, use
[`CONTRIBUTING.md`](../CONTRIBUTING.md). This thin docs surface keeps only the
public routing and support boundary, not a second copy of the full verification
playbook.

## Support Boundary

- Docsiphon is a CLI export pipeline, not a hosted API or managed service
- Any future MCP-aware surface remains future secondary until it ships its own
  install contract, verification gate, public packet, and lane truth
- `scripts/verify_instructure.sh` is a public example probe, not a vendor-wide
  compatibility promise
- `CODEOWNERS`, PR templates, and Issue templates are part of the collaboration
  contract
- `SUPPORT.md` defines the best-effort maintainer support scope
- `SECURITY.md` defines private reporting expectations
