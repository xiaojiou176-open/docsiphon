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

## What You Get

一次最小成功应该给你 3 类东西，而不是一堆没法复盘的抓取碎片：

- preserved Markdown tree
- run ledger artifacts: `manifest.jsonl`, `report.json`, `toc.md`, `report.html`
- 一份可继续 diff、resume、handoff 的本地 docs corpus

## Why It Exists

- Prefer Markdown twins when a docsite publishes them
- Keep path hierarchy intact so humans and pipelines can still reason about the output
- Leave behind reviewable artifacts like `manifest.jsonl`, `report.json`, `toc.md`, and `report.html`

## Best Fit

- AI / RAG corpus preparation
- offline documentation review
- repeatable doc exports with audit-friendly run artifacts

## Why Not Generic Crawlers

因为真正麻烦的不是“抓到页面”，而是“以后还能看懂、还能对账、还能继续用”。

> 通用 crawler 更像把文件柜整柜倒在地上。
> Docsiphon 想做的是把文件按标签重新装回可用的文件夹。

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
