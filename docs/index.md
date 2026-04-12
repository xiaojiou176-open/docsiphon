---
title: Docsiphon
description: Export documentation sites into AI-ready local Markdown corpora with preserved paths, reproducible runs, and audit artifacts.
---

<style>
.markdown-body a {
  color: #0550ae;
  text-decoration: underline;
  text-underline-offset: 0.16em;
}
</style>

<main id="main-content" role="main" markdown="1">

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

A minimal first success should give you three kinds of output, not a pile of
untraceable crawl fragments:

- preserved Markdown tree
- run ledger artifacts: `manifest.jsonl`, `report.json`, `toc.md`, `report.html`
- a local docs corpus you can diff, resume, and hand off

## Proof Ladder

Use the front door like a short evidence ladder, not like a maze:

| Step | Open this next | What it proves |
| --- | --- | --- |
| `1` | the `uvx` command above | Docsiphon is a real `CLI-first` tool you can run immediately, not a concept page |
| `2` | `manifest.jsonl`, `report.json`, `toc.md`, `report.html` in the export output | the run left behind reviewable artifacts instead of a pile of unlabeled crawl residue |
| `3` | the repo map and latest release shelf below | current repository truth and newest published artifacts are related, but they are not the same thing |

## Why It Exists

- Prefer Markdown twins when a docsite publishes them
- Keep path hierarchy intact so humans and pipelines can still reason about the output
- Leave behind reviewable artifacts like `manifest.jsonl`, `report.json`, `toc.md`, and `report.html`

## Best Fit

- AI / RAG corpus preparation
- offline documentation review
- repeatable doc exports with audit-friendly run artifacts

## Why Not Generic Crawlers

Because the hard part is not "did we fetch the page?" The hard part is whether
the result is still understandable, auditable, and reusable later.

> A generic crawler is closer to dumping the whole filing cabinet onto the
> floor.
> Docsiphon is trying to put the papers back into labeled folders you can use
> again.

## Release Shelf Truth

The latest release entrypoint is the right place to look for the newest
published wheel, sdist, and starter-profile assets.

This Pages surface and the repo front door describe the newest repository truth
on `main`, which can move ahead before the next tagged release is cut.

Treat "latest release" and "current main" as neighboring shelves, not as the
same object.

## Open The Right Next Door

After the first `uvx` run succeeds, the narrowest honest routing is:

| If you want to... | Open this | Why this is the right next door |
| --- | --- | --- |
| understand where the repo keeps its moving parts | [Pages repo map](https://xiaojiou176-open.github.io/docsiphon/repo-map/) | it is the structural map, not a second marketing page |
| grab the newest published wheel, sdist, and starter-profile assets | [latest release](https://github.com/xiaojiou176-open/docsiphon/releases/latest) | that is the published shelf, separate from repository-side wording on `main` |
| inspect packet and lane truth after the product story is already clear | [distribution packet ledger](https://github.com/xiaojiou176-open/docsiphon/blob/main/docs/distribution-packet-ledger.md) | distribution status is a second-ring proof surface, not the first success path |
| see roadmap and discussion once the basics are proven | [Pages roadmap](https://xiaojiou176-open.github.io/docsiphon/roadmap/) and [GitHub Discussions](https://github.com/xiaojiou176-open/docsiphon/discussions) | planning and community belong after the first run, not before it |

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

</main>
