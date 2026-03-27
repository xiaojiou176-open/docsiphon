# Security Policy

## Scope

This policy covers the source repository, the CLI implementation, tracked
helper scripts, and repository-managed documentation.

Generated exports, local profiles, caches, and third-party documentation
artifacts are operator data. Review redistribution rights before publishing any
captured output.

## Reporting a Vulnerability

Do **not** post vulnerability details in a public issue or PR.

Use one of these private paths:

1. GitHub private vulnerability reporting, if the repository UI offers it.
2. The repository owner profile contact path, if private reporting is not
   available in the UI.

Include:

- affected version or commit
- a short impact summary
- reproduction steps or a minimal proof of concept
- known mitigations or workarounds

## Secrets and Sensitive Data

- Never commit real API keys, tokens, passwords, cookies, private keys, or
  customer data.
- Treat exported documentation snapshots as potentially sensitive until their
  redistribution rights are confirmed.
- If a secret is exposed, rotate or revoke it first, then report the incident
  through a private channel.

## Disclosure Expectations

This repository does not publish a formal response SLA. Valid reports are
reviewed as maintainer availability allows.

Please avoid public disclosure until the issue has been triaged and a
remediation path is in place.
