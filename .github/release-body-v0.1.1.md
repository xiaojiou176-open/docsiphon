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
- The repository now has seeded Discussions entrypoints for announcements,
  ideas, Q&A, and show-and-tell.

## Fastest way to try it

If you do not already have `uv`, start with the official install guide:
https://docs.astral.sh/uv/getting-started/installation/

```bash
uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git \
  docsiphon "https://developerdocs.instructure.com/services/canvas" \
  --scope-prefix /services/canvas \
  --max-pages 6 \
  --out ./_outputs \
  --site-root auto
```

This is the canonical first-run path. It is intentionally scoped to six pages
so evaluators can prove the file tree, report artifacts, and Markdown-first
path before they commit to a larger mirror.

## What you get

- a path-preserving local Markdown tree
- `manifest.jsonl` as a page-level ledger
- `report.json`, `toc.md`, and `report.html` as review surfaces
- a better starting point for AI / RAG ingestion than raw HTML mirrors
- release assets for the demo GIF, social preview PNG, hero SVG, and
  before/after SVG
- downloadable example profiles for quickstart, rag-corpus, and strict-audit

## Public evidence snapshot

- `scripts/verify_instructure.sh` currently confirms public Markdown twins for
  both the Canvas root page and a nested subpage
- a fresh scoped sample run against Canvas discovers `336` URLs via sitemap,
  schedules `6`, writes `6`, and fails `0` with `--max-pages 6`
- automated tests cover `llms.txt`, sitemap, search index, BFS fallback, and
  the audit artifact surfaces
- public proof last refreshed: `2026-03-26`

## Downloadable starter profiles

- https://github.com/xiaojiou176-open/docsiphon/releases/download/v0.1.1/canvas-quickstart.toml
- https://github.com/xiaojiou176-open/docsiphon/releases/download/v0.1.1/rag-corpus.toml
- https://github.com/xiaojiou176-open/docsiphon/releases/download/v0.1.1/strict-audit.toml

## Best fit

- AI / RAG corpus preparation
- offline documentation review
- repeatable doc exports with audit-friendly run artifacts
- teams that want copyable example profiles instead of rebuilding config from
  scratch

## Not the best fit

- fully generic website mirroring
- JS-heavy browser-rendered product surfaces
- sites that need a headless browser automation workflow to reveal content

## Community

- Discussions home: https://github.com/xiaojiou176-open/docsiphon/discussions
- Repo-local roadmap: https://github.com/xiaojiou176-open/docsiphon/blob/main/docs/roadmap.md
- Use the Discussions categories for announcements, ideas, Q&A, and show-and-tell.

## Docs and support entrypoints

- Repo front door: https://github.com/xiaojiou176-open/docsiphon
- GitHub docs entry: https://github.com/xiaojiou176-open/docsiphon/blob/main/docs/README.md
- GitHub Pages landing page: https://xiaojiou176-open.github.io/docsiphon/
- Copyable example profiles: https://github.com/xiaojiou176-open/docsiphon/tree/main/examples

## What is next

- broader docs-site compatibility coverage from real incoming reports
- tighter example profiles for common AI / RAG export workflows
- continued polish on audit-friendly output artifacts and review surfaces
- current roadmap issue queue:
  https://github.com/xiaojiou176-open/docsiphon/issues?q=is%3Aissue+is%3Aopen+label%3Aroadmap
