# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this file tracks repository-level changes. It does not, by itself, imply
that a hosted release pipeline, signed artifacts, or release provenance are
already in place.

## [Unreleased]

### Added
- Productized public-facing README with AI / RAG positioning, real-output
  examples, and visual assets under `assets/`
- Public release draft source at `.github/release-body-v0.1.1.md`
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
