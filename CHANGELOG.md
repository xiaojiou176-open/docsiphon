# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this file tracks repository-level changes. It does not, by itself, imply
that a hosted release pipeline or public release trust chain exists unless the
repository workflow surface and release evidence say so. The current release
evidence entrypoint is the manual `.github/workflows/release-evidence.yml`
workflow.

## [Unreleased]

### Added
- manual `release-evidence.yml` workflow for generating pinned release
  artifacts, checksums, SBOM, and provenance outside the PR required chain
- README evidence snapshot covering public probe, scoped export evidence,
  discovery coverage, and audit-artifact proof paths
- release-facing profile download links and stronger first-run routing for
  no-checkout evaluators
- a GitHub Pages-facing docs landing formalization plan covering `_config.yml`,
  `repo-map.md`, `robots.txt`, and `sitemap.xml`

### Changed
- pinned GitHub Actions workflows to full commit SHAs for supply-chain trust
- rewired the README first screen around a single canonical quickstart path,
  earlier fit boundaries, and fresher public proof numbers
- aligned `examples/canvas-quickstart.toml` with the six-page first-run story
- refreshed the public release body toward the current six-page sample proof
- sharpened docs routing so `docs/README.md` can act as the GitHub-facing docs
  entrypoint
- refreshed release body source toward clearer evidence, docs, and support
  entrypoints
- synced `uv.lock` with the public `chardet<8` dependency constraint
- raised the `requests` floor to `>=2.33.0` to close Dependabot alert
  `GHSA-gc5v-m9x4-r6x2` / `CVE-2026-25645`

## [0.1.2]

### Added
- release-shelf truth sections across the GitHub and Pages front doors so
  latest published release and current `main` truth are no longer flattened
- public-language contract checks for the English-first front door
- Pages landmark and footer landmark hardening that clears the live axe rerun

### Changed
- normalized the public front door to English-first wording
- extended the public surface ledger with `release_shelf`
- taught contract and hygiene gates about the Pages layout-backed footer
  landmark repair
- refreshed release-facing links and release-body references from `v0.1.1` to
  `v0.1.2`

## [0.1.1]

### Added
- Productized public-facing README with AI / RAG positioning, real-output
  examples, and visual assets under `assets/`
- Public release body source at `.github/release-body-v0.1.1.md`
- First public GitHub release announcement discussion
- Collaboration guardrails:
  - `.github/CODEOWNERS`
  - PR template
  - Issue templates
- Agent navigation files:
  - `AGENTS.md`
  - `CLAUDE.md`

### Changed
- Reduced the tracked docs tree to a thin but higher-signal public surface
- Refreshed package metadata toward AI-ready Markdown corpus export language
- Raised the `requests` dependency floor to avoid public `uvx` warning noise
- Pinned `chardet<6` so `uvx` installs stay on a Requests-compatible version
- Kept `scripts/verify_instructure.sh` as the only tracked example probe
- Tightened ignore rules for secrets, runtime state, and local-only surfaces
- Promoted collaboration templates and CODEOWNERS into the repository contract
- Aligned support and security wording with the live public repository surface

### Removed
- Archived and exploratory docs that no longer belong in the public surface
- Extra helper scripts that acted as maintainer-only bulk probes

## [0.1.0]

### Added
- Initial CLI-driven documentation export pipeline
- Discovery chain:
  - `llms.txt`
  - sitemap
  - search index
  - BFS fallback
- Markdown-first fetch with HTML fallback conversion
- Manifest, report, index, TOC, and HTML report outputs
- Retry matrix, rate limiting, and per-host concurrency controls
- Resume metadata support through `manifest.jsonl`
