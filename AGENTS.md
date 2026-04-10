# Agent Navigation

This repository keeps agent-facing guidance intentionally small.

## Canonical Paths

- Project front door: `README.md`
- Thin docs surface: `docs/README.md`
- Contribution workflow: `CONTRIBUTING.md`
- Security reporting: `SECURITY.md`
- Support policy: `SUPPORT.md`

## Product Boundary

- `Only current primary surface and front door today`: `CLI-first`
- Current flagship public packet: GitHub repo front door + `uvx` quickstart + release assets / example profiles
- MCP-aware secondary surface is allowed in the future, but it remains future secondary until it has its own install contract, verification gate, public packet, and lane truth
- Route first-time operators through `README.md` + the `uvx` quickstart before treating any future secondary surface as part of the current flagship path

## Repository Rules

- Keep generated outputs, caches, logs, and editor state out of Git.
- Treat `CODEOWNERS`, PR templates, and Issue templates as the collaboration
  contract.
- Prefer surgical changes and update the thin public docs surface when behavior
  or workflow expectations change.

## Host Safety

- Treat host-process control as a hard boundary, even in a docs-first repo.
- Do not introduce `killall`, `pkill`, `killpg(...)`, negative/zero PID
  signaling, `osascript`, `System Events`, `loginwindow`, Force Quit APIs, or
  detached browser-launch helpers into tracked automation.
- If future tooling needs local process management, keep it exact-scope,
  repo-owned, auditable, and fail-closed by default.

## Verification

Use [`CONTRIBUTING.md`](./CONTRIBUTING.md) as the canonical source for full
verification commands and the default local cleanup lane.
