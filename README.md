# Docsiphon

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-0f172a?logo=python&logoColor=ffd43b&labelColor=111827&color=2dd4bf)](./pyproject.toml)
[![CI](https://img.shields.io/github/actions/workflow/status/xiaojiou176-open/docsiphon/ci.yml?branch=main&label=ci)](https://github.com/xiaojiou176-open/docsiphon/actions/workflows/ci.yml)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/xiaojiou176-open/docsiphon/codeql.yml?branch=main&label=codeql)](https://github.com/xiaojiou176-open/docsiphon/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-0f172a?labelColor=111827&color=f59e0b)](./LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-0f172a?labelColor=111827&color=38bdf8)](./.pre-commit-config.yaml)

**Turn documentation sites into AI-ready local Markdown corpora with preserved
paths, reproducible exports, and audit artifacts.**

Docsiphon is a Python CLI for AI / RAG builders who need something better than
"just mirror the site and hope for the best." It keeps URL hierarchy intact,
prefers Markdown when the docsite exposes it, falls back to HTML extraction
when it does not, and writes a run ledger you can review, resume, or hand to
another operator.

[Quickstart](#quickstart) · [Example Output](#real-example-output) · [Release Draft](./.github/release-body-v0.1.1.md) · [Why Docsiphon](#why-docsiphon)

![Docsiphon hero showing scoped documentation export, preserved Markdown tree, and audit artifacts](./assets/docsiphon-hero.svg)

> If you build retrieval, eval, or offline doc pipelines, star this repo now.
> It is the kind of tool you do not need every day, but you will want to find
> instantly the next time a vendor docsite becomes your ingestion problem.

## Why Docsiphon

- **Ship an LLM-ready corpus, not a pile of scraped HTML.** Docsiphon prefers
  Markdown twins when a docsite publishes them and only falls back to HTML
  conversion when needed.
- **Keep structure humans and pipelines can still reason about.** Exported files
  preserve path hierarchy instead of flattening everything into opaque blobs.
- **Keep an audit trail for every run.** `manifest.jsonl`, `report.json`,
  `toc.md`, and `report.html` make the export inspectable, resumable, and easy
  to review.

## Who It Is For

- AI / RAG builders preparing retrieval corpora from vendor documentation
- Teams that want a local, reviewable snapshot before chunking or embedding
- Operators who need reproducible doc exports with a ledger, not one-off copy
  and paste sessions

## Why It Beats Naive Crawling

![Docsiphon before/after comparison between manual copying, generic mirrors, and an audit-friendly Markdown export](./assets/docsiphon-before-after.svg)

| Approach | Preserves path hierarchy | Prefers Markdown | Emits audit artifacts | Resume support | Filtering and scope controls | LLM ingestion friendliness |
| --- | --- | --- | --- | --- | --- | --- |
| Manual copy / paste | No | Sometimes | No | No | No | Low |
| Raw crawler | Rarely | No | Rarely | Rarely | Varies | Medium |
| Generic site mirror | Sometimes | No | No | Rarely | Medium | Medium |
| **Docsiphon** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **High** |

Docsiphon is not trying to be a universal web archiver. It is opinionated about
one job: turning documentation sites into clean local assets that are easier for
AI systems and humans to inspect.

## Quickstart

### 30-Second Quickstart

Run Docsiphon directly from GitHub with `uvx`:

```bash
uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git \
  docsiphon "https://developerdocs.instructure.com/services/canvas" \
  --scope-prefix /services/canvas \
  --max-pages 6 \
  --out ./_outputs \
  --site-root auto
```

This scoped sample export is intentionally small and fast. It is enough to show
the output tree, report artifacts, and path-preserving mapping without asking
you to mirror an entire vendor docsite on your first run.

Default output root: `./_outputs`

## Common Commands

Dry-run discovery before downloading content:

```bash
uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git \
  docsiphon "https://developerdocs.instructure.com/services/canvas" \
  --scope-prefix /services/canvas \
  --dry-run
```

Scoped crawl against a docs subtree:

```bash
uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git \
  docsiphon "https://example.com/docs/start" \
  --scope-prefix /docs \
  --max-pages 500
```

Resume an existing export:

```bash
uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git \
  docsiphon "https://example.com/docs/start" \
  --resume \
  --skip-existing
```

Use a profile file:

```bash
uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git \
  docsiphon "https://example.com/docs/start" \
  --profile ./config.toml
```

If you want the contributor workflow instead of the end-user path, jump to
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

## What You Get

Each non-dry run writes:

- exported Markdown or saved HTML files
- `manifest.jsonl` as the page-level ledger
- `report.json` as the run summary
- `index.json`, `toc.md`, and `report.html` as derived views
- `_errors/` snapshots when error sampling is enabled

## Real Example Output

![Docsiphon demo showing a scoped export command, report summary, and generated file tree](./assets/docsiphon-demo.gif)

The snapshot below comes from a real sample run against the Canvas developer
docs with `--scope-prefix /services/canvas --max-pages 6`.

```text
_outputs/
└── canvas/
    ├── basics.md
    ├── basics/
    │   ├── file.changelog.md
    │   ├── file.compound_documents.md
    │   ├── file.endpoint_attributes.md
    │   └── file.file_uploads.md
    ├── canvas.md
    ├── index.json
    ├── manifest.jsonl
    ├── report.html
    ├── report.json
    ├── toc.md
    └── urls.txt
```

```json
{
  "run_id": "06f0f84e0332",
  "discovery_source": "sitemap",
  "total": 334,
  "scheduled_urls": 6,
  "ok": 6,
  "failed": 0,
  "path_collisions": 0
}
```

The exported Markdown preserves path semantics instead of flattening everything
into generic filenames:

```md
---
source_url: https://developerdocs.instructure.com/services/canvas/basics
fetched_url: https://developerdocs.instructure.com/services/canvas/basics.md
---
# Basics

- [GraphQL](/services/canvas/basics/file.graphql.md)
- [API Change Log](/services/canvas/basics/file.changelog.md)
- [Pagination](/services/canvas/basics/file.pagination.md)
```

## Use Cases for AI / RAG

- Build a clean retrieval corpus before chunking and embedding vendor docs
- Snapshot third-party documentation into a reviewable tree for eval or audit
- Keep an offline Markdown mirror with a ledger you can diff, resume, and rerun

## Trade-offs / Not For

Docsiphon is a strong fit when the source is a documentation site and the goal
is to produce a clean local corpus.

It is **not** the right tool when:

- you need a universal website mirroring solution
- the site depends on heavy browser-side rendering or authenticated product UX
- you need to preserve every visual detail of a live site rather than extract
  structured, text-first content

## Why Not Just `wget` or a Generic Crawler?

Because the hard part is not fetching bytes. The hard part is getting a local
result that still feels like documentation, still maps back to source URLs, and
still leaves behind enough run evidence that you can trust what happened.

Generic crawlers are like dumping a filing cabinet onto the floor and saying
"technically, everything is here." Docsiphon is trying to put the papers into a
folder structure you can actually use again.

## How It Works

Docsiphon follows a CLI-driven export pipeline:

1. parse CLI arguments and optional profile settings
2. discover candidate URLs through `llms.txt`, sitemap, search index, or BFS
3. filter and normalize the candidate set
4. export each page through Markdown-first fetch with HTML fallback
5. write page artifacts and derived run artifacts

## Verification

### Verification / Trust

This repository keeps a thin public docs surface, but the trust boundary is
real:

- the CLI entrypoint is checked in CI
- repository contracts and hygiene gates are enforced
- tests cover the current documented behavior
- export runs produce reproducible operator artifacts instead of silent side
  effects

Current verification entrypoints:

```bash
uv run python scripts/check_contracts.py
uv run python scripts/check_repo_hygiene.py
uv run pre-commit run --all-files
uv run pytest tests
uv run docsiphon --help
```

## Documentation

The public docs surface stays intentionally thin and high-signal.

- Repository map, execution model, and support boundary: `docs/README.md`
- Release draft for the next public polish pass: `.github/release-body-v0.1.1.md`
- GitHub social preview upload source: `assets/docsiphon-social-preview.png`
- Contribution workflow: `CONTRIBUTING.md`
- Security reporting: `SECURITY.md`
- Support policy: `SUPPORT.md`

## Collaboration

- `CODEOWNERS` defines the review routing baseline
- PR and Issue templates are part of the live repository contract
- Generated outputs, caches, runtime state, and local editor files stay out of Git

## Development Environment

A minimal DevContainer is available under `.devcontainer/` for contributors who
prefer a containerized Python 3.11 + `uv` workflow.

## FAQ

### Does Docsiphon require a full checkout and local setup?

No. The public-first path is `uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git ...`.
Use the contributor workflow only if you plan to hack on the repository itself.

### Does it only work on sites that publish Markdown?

No. Docsiphon prefers Markdown when available, but it can fall back to HTML
fetch and extraction when the source site does not expose a Markdown twin.

### Is this a general browser automation crawler?

No. Docsiphon is optimized for documentation exports, not arbitrary product
surfaces that need a headless browser to render authenticated UI flows.

## Security

Use the process described in `SECURITY.md` for vulnerabilities or accidental
secret exposure. Do **not** post sensitive details in public issues.

## Contributing

See `CONTRIBUTING.md` for setup, validation, and pull-request expectations.

## License

Docsiphon is released under the MIT License. See `LICENSE`.
