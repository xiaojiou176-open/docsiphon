# Docsiphon v0.1.2

Docsiphon remains a CLI-first tool for turning documentation sites into
AI-ready local Markdown corpora with preserved paths and audit artifacts.

## Why this release matters

- the public GitHub and Pages front doors are now English-first
- `Release Shelf Truth` is explicit, so the latest published release is no
  longer flattened into current `main` wording
- the public surface now guards language drift and release-shelf truth through
  repo-owned contract checks
- the live Pages front door now includes the semantic landmarks required to
  clear the wave-level axe rerun

## Fastest way to try it

If you do not already have `uv`, start here:
https://docs.astral.sh/uv/getting-started/installation/

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
- `manifest.jsonl`, `report.json`, `toc.md`, and `report.html`
- downloadable starter profiles for a faster first run
- public front-door wording that now matches the current release shelf and
  current `main` truth more honestly

## Public evidence snapshot

- live GitHub Pages axe rerun now returns zero violations for the front door
- the latest release shelf remains the newest published packet, distinct from
  future `main`-only wording changes
- repo-owned tests and contract checks now block public language drift on the
  English-first surface

## Downloadable starter profiles

- https://github.com/xiaojiou176-open/docsiphon/releases/download/v0.1.2/canvas-quickstart.toml
- https://github.com/xiaojiou176-open/docsiphon/releases/download/v0.1.2/rag-corpus.toml
- https://github.com/xiaojiou176-open/docsiphon/releases/download/v0.1.2/strict-audit.toml

## Docs and support entrypoints

- Repo front door: https://github.com/xiaojiou176-open/docsiphon
- GitHub docs entry: https://github.com/xiaojiou176-open/docsiphon/blob/main/docs/README.md
- GitHub Pages landing page: https://xiaojiou176-open.github.io/docsiphon/
- Copyable example profiles: https://github.com/xiaojiou176-open/docsiphon/tree/main/examples
