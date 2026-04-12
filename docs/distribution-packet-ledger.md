# Distribution Packet Ledger

This page is the top-level packing list for Docsiphon's public surfaces.

Use it when you need one simple answer:

> What is the flagship packet today, what is only a secondary host-native
> packet, and what should **not** be mistaken for a runtime/container lane?

Think of Docsiphon like a tool chest.
The CLI is the main drawer you open first. Host-native packets are labeled side
cases, not hidden engines that turn the repo into a different product.

## Current surface split

| Surface | What it really is | Current truth |
| --- | --- | --- |
| Flagship public packet | repo front door + `uvx` quickstart + release assets / example profiles | current primary surface |
| Release shelf | tagged `v0.1.2` assets and release notes | published shelf |
| Host-native public skill packet | self-contained reviewer packet for the CLI export lane | secondary lane only |
| Future MCP-aware secondary surface | possible later lane only after its own install contract and proof gate | not shipped |

## Canonical packet map

| Packet slice | Exact repo paths | Current status | What it does not prove |
| --- | --- | --- | --- |
| Flagship CLI-first packet | `README.md`, `docs/README.md`, `examples/README.md`, `.github/release-body-v0.1.2.md` | active front door | hosted runtime, container product, or MCP-first identity |
| Release shelf packet | release `v0.1.2` assets referenced from `README.md` and `examples/README.md` | published shelf | newest `main` wording or future secondary lanes |
| Host-native secondary packet | `public-skills/README.md`, `public-skills/docsiphon-doc-corpus-operator/README.md`, `public-skills/docsiphon-doc-corpus-operator/manifest.yaml` | packet-ready; ClawHub live, Goose review-pending, agent-skill.co blocked upstream, OpenHands closed-not-accepted, awesome-opencode not_honest_cargo_yet | repo-wide surface change, runtime/container fit, or a future opencode-native project/resource shape that does not exist today |

## Current lane truth

Keep these truths separate:

1. **CLI-first flagship packet**
   - this is the main product box
   - it teaches `uvx` export, scoped corpus creation, and audit artifact review
2. **Host-native packet**
   - useful for ClawHub / OpenHands-style reviewers
   - still secondary and still about the same CLI export lane
3. **Future secondary MCP-aware surface**
   - allowed later
   - not part of today's flagship or release shelf

## Heavy-lane order that stays honest

If a later wave wants to push harder, the current honest order is:

1. keep the CLI-first packet crisp
2. keep release shelf truth separate from `main`
3. keep host-native packet receipts in the secondary-lane bucket
4. do **not** invent Docker/runtime/container work just because a later lane
   exists in theory

## Misreadings to avoid

Do **not** use the current packet shape to imply:

- Docsiphon is a hosted documentation export service
- Docsiphon is a container/runtime repo
- Docsiphon is already an MCP-first product
- host-native packet publication replaces the CLI-first flagship surface
