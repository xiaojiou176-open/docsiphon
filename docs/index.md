---
title: Docsiphon
description: Export documentation sites into AI-ready local Markdown corpora with preserved paths, reproducible runs, and audit artifacts.
---

# Docsiphon

Export documentation sites into **AI-ready local Markdown corpora** with
**preserved paths**, **reproducible runs**, and **audit artifacts**.

Docsiphon is for people who need something more trustworthy than
"mirror the site and hope for the best."

Current front-door rule: the public first-success path is still the `uvx`
quickstart below. If Docsiphon grows an MCP-aware surface later, that path will
remain a secondary surface until it ships its own install contract,
verification gate, public packet, and lane truth.

## Fastest Path

1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
2. Run Docsiphon directly from GitHub:

```bash
uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git \
  docsiphon "https://developerdocs.instructure.com/services/canvas" \
  --scope-prefix /services/canvas \
  --max-pages 6 \
  --out ./_outputs \
  --site-root auto
```

## Why It Exists

- Prefer Markdown twins when a docsite publishes them
- Keep path hierarchy intact so humans and pipelines can still reason about the output
- Leave behind reviewable artifacts like `manifest.jsonl`, `report.json`, `toc.md`, and `report.html`

## Best Fit

- AI / RAG corpus preparation
- offline documentation review
- repeatable doc exports with audit-friendly run artifacts

## Start Here

- Full README:
  [GitHub repository front door](https://github.com/xiaojiou176-open/docsiphon#readme)
- Repo map and support boundary:
  [Pages repo map](https://xiaojiou176-open.github.io/docsiphon/repo-map/)
- Current roadmap themes:
  [Pages roadmap](https://xiaojiou176-open.github.io/docsiphon/roadmap/)
- Downloadable starter profiles:
  [latest release](https://github.com/xiaojiou176-open/docsiphon/releases/latest)
- Community discussions:
  [GitHub Discussions](https://github.com/xiaojiou176-open/docsiphon/discussions)
