# Contributing

Thanks for helping improve Docsiphon.

This repository keeps a thin public docs surface and a strict verification
baseline. The most useful contributions are still small, well-scoped changes
that clearly improve the real source of truth: code, tests, and repository
documentation.

## Before You Start

- Read `README.md` first for the current project overview and CLI usage.
- Read `docs/README.md` for the repository map and output model.
- Keep changes surgical. Avoid unrelated cleanup or opportunistic refactors.
- Do not commit generated export outputs, local caches, or editor noise such as
  `.DS_Store`, `__pycache__`, or `*.egg-info`.

## Local Setup

The official repository workflow uses `uv`.

```bash
uv sync --group dev
pre-commit run --all-files
```

If you want local hook enforcement in addition to manual runs, install the
hooks after sync:

```bash
pre-commit install
```

## Running Checks

This section is the **canonical** source of truth for contributor verification
commands. Other repo docs should link here instead of copying the full block.

The current repository truth is:

- the governance contracts should pass:

```bash
uv run python scripts/check_contracts.py
```

- the repository hygiene gate should pass:

```bash
uv run python scripts/check_repo_hygiene.py
```

- the pre-commit policy should pass on the tracked repository surface:

```bash
pre-commit run --all-files
```

- the CLI entrypoint should work locally:

```bash
uv run docsiphon --help
```

- the repository's current passing test entrypoint is:

```bash
uv run pytest tests
```

If you add or change behavior, run the narrowest relevant verification and then
run the full repository test suite above before handing work off.

## Clean Local State

Use the cleanup script when you want to remove rebuildable local noise without
touching operator data such as `_outputs/`.

```bash
uv run python scripts/clean_local_state.py --apply
```

This command is intended to clean local-only directories such as `build/`,
`*.egg-info/`, `__pycache__/`, `.pytest_cache/`, `.runtime-cache/temp/`, and
`htmlcov/`. It is **not** the right command for deleting `_outputs/`, because
that directory still belongs to operator data rather than disposable noise.

## Code and Documentation Expectations

- Match the repository's existing style and naming patterns.
- Fix root causes, not just symptoms.
- Update the thin public docs surface when user-visible behavior or setup
  expectations change.
- Keep public-facing claims anchored in runnable commands, real output, or code
  paths. Do not add decorative marketing copy that the repository cannot back
  up.
- Keep generated outputs out of Git.
- Prefer clear failure reporting over silent fallback behavior.
- Treat `.github/public-surface-ledger.yml` as the repository's current source
  of truth for GitHub-side metadata and manual-required settings.

## Pull Request Expectations

Each contribution should make it easy for the maintainer to verify what
changed.

Please include:

- a short summary of the change
- why the change is needed
- the files or areas affected
- the exact verification commands you ran
- any remaining risks or validation gaps

## Collaboration Guardrails

- Open work through the issue templates under `.github/ISSUE_TEMPLATE/` so the
  maintainer gets reproducible context instead of free-form guesses.
- Prefer the GitHub Discussions index for questions, ideas, and show-and-tell
  before opening a new issue:
  - Discussions home: `https://github.com/xiaojiou176-open/docsiphon/discussions`
  - Current roadmap themes: `docs/roadmap.md`
- Use pull requests for changes targeting `main`. The repository's collaboration
  baseline assumes branch protection and CI checks will be the merge gate.
- Treat `CODEOWNERS` review routing as the source of truth for who should be
  looped in on repository-wide changes.
- Do not use public issues for vulnerability details. Route security-sensitive
  reports through `SECURITY.md`.

## What Not to Do

- Do not rewrite unrelated files just to "clean things up."
- Do not add fake tests or placeholder assertions.
- Do not commit secrets, copied third-party documentation dumps, or personal
  local environment files.
- Do not re-track ignored local IDE files such as `.vscode/settings.json`.
- Do not reintroduce legacy output roots from the pre-`_outputs` era.
- Do not grow the public docs surface with new archive, rehearsal, or
  maintainer-only documentation.

## Questions and Coordination

If a correct fix would require changing public contracts, shared repository
policy, or files outside your assigned scope, stop and escalate instead of
guessing.
