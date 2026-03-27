# Docsiphon v0.1.1

Docsiphon turns documentation sites into AI-ready local Markdown corpora with
preserved paths and audit artifacts.

## Why this release matters

- The public README now explains the product in end-user language instead of
  only implementation language.
- First-time users now have a copy-pasteable `uvx` path that runs Docsiphon
  directly from GitHub.
- The repository now ships a coherent visual system for README hero, before /
  after framing, demo motion, and social preview preparation.

## Fastest way to try it

```bash
uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git \
  docsiphon "https://developerdocs.instructure.com/services/canvas" \
  --scope-prefix /services/canvas \
  --max-pages 6 \
  --out ./_outputs \
  --site-root auto
```

## What you get

- a path-preserving local Markdown tree
- `manifest.jsonl` as a page-level ledger
- `report.json`, `toc.md`, and `report.html` as review surfaces
- a better starting point for AI / RAG ingestion than raw HTML mirrors

## Best fit

- AI / RAG corpus preparation
- offline documentation review
- repeatable doc exports with audit-friendly run artifacts

## Not the best fit

- fully generic website mirroring
- JS-heavy browser-rendered product surfaces
- sites that need a headless browser automation workflow to reveal content
