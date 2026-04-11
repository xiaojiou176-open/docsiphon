# Example Profiles

These profiles are public, copyable starting points for common Docsiphon
workflows.

Use them when you already understand the README quickstart and want a template
you can adapt instead of rebuilding flags by hand.

## Included Profiles

- `canvas-quickstart.toml`: small scoped export for a fast first success
- `rag-corpus.toml`: a cleaner AI / RAG preparation baseline with frontmatter
  and sorted manifest output
- `strict-audit.toml`: more conservative audit-oriented export settings with
  saved HTML and tighter error snapshots

## Usage

Run a profile directly:

```bash
uvx --from git+https://github.com/xiaojiou176-open/docsiphon.git \
  docsiphon "https://developerdocs.instructure.com/services/canvas" \
  --profile ./examples/canvas-quickstart.toml
```

Or use named profiles if you consolidate your own TOML file under
`[profiles.<name>]`.

## Current Release Assets

If you do not want to clone the repository first, the current `v0.1.2` release
ships copyable profile assets directly:

- [canvas-quickstart.toml](https://github.com/xiaojiou176-open/docsiphon/releases/download/v0.1.2/canvas-quickstart.toml)
- [rag-corpus.toml](https://github.com/xiaojiou176-open/docsiphon/releases/download/v0.1.2/rag-corpus.toml)
- [strict-audit.toml](https://github.com/xiaojiou176-open/docsiphon/releases/download/v0.1.2/strict-audit.toml)

That path is meant for evaluators who want to try Docsiphon with `uvx` and a
ready-made profile before they decide whether the repository deserves a local
checkout.
