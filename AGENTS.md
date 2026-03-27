# Agent Navigation

This repository keeps agent-facing guidance intentionally small.

## Canonical Paths

- Project front door: `README.md`
- Thin docs surface: `docs/README.md`
- Contribution workflow: `CONTRIBUTING.md`
- Security reporting: `SECURITY.md`
- Support policy: `SUPPORT.md`

## Repository Rules

- Keep generated outputs, caches, logs, and editor state out of Git.
- Treat `CODEOWNERS`, PR templates, and Issue templates as the collaboration
  contract.
- Prefer surgical changes and update the thin public docs surface when behavior
  or workflow expectations change.

## Verification

```bash
uv run python scripts/check_contracts.py
uv run python scripts/check_repo_hygiene.py
uv run pre-commit run --all-files
uv run pytest tests
uv run docsiphon --help
```
