# Syllabus — Git Interno e Supply-Chain GitHub

> Lingua: italiano · Aggiornamento: 2026-04-27
> Versioni: Git 2.45+, GitHub Enterprise/Cloud, Actions runner v2.319+, ARC.

## Identita

**"Git interno e supply-chain GitHub"** — Git fluently dall'interno (objects, refs, hooks) + GitHub platform completo + Actions sicuri (SHA-pinning, OIDC, attestation SLSA).

**Target:** competent → proficient (3 → 4). Capace di hardening pipeline GHA + branch protection-as-code + supply-chain security.

## Prerequisiti

- CLI Linux/macOS; Git basic commands; HTTP basics.

## Obiettivi

1. Git internals: objects (blob, tree, commit), refs, packfiles.
2. Branching strategies (Gitflow, GitHub Flow, trunk-based).
3. Hooks pre-commit/pre-push.
4. GHA workflows: explicit `permissions: {}`, SHA pin, concurrency.
5. Webhook HMAC verify (constant-time, replay protection).
6. Branch protection-as-code (Terraform GitHub provider).
7. Self-hosted runner (ARC ephemeral, fork-PR isolation).
8. Reusable workflow + typed inputs.
9. OIDC cloud creds (no long-lived secret).
10. Supply-chain attestation SLSA (cosign + provenance).
11. CodeQL Advanced Security.

## Struttura

### Fase 1 — Git
- 01: Fondamenti git
- 02: Branching strategies
- 06-11: Git advanced (merge, internals, hooks, lfs, recovery, gitignore)
- 20: Workflow team

### Fase 2 — GitHub
- 03: Piattaforma
- 12: Repo management
- 13: Issues/Projects
- 14: Packages/Pages/Releases
- 15: API/CLI/Webhooks
- 16: Security scanning
- 22: Copilot/Codespaces
- 23: Migration

### Fase 3 — Actions
- 04: Actions intro
- 17: Workflow syntax
- 18: Actions advanced
- 19: CI/CD ricette
- 21: Self-hosted runners
- 26 (NEW): OIDC cloud creds
- 27 (NEW): Supply-chain attestation SLSA
- 28 (NEW): CodeQL Advanced Security

### Fase 4 — Integration
- 24: DevOps completo
- 05: Progetti pratici

## Capstone

GHA pipeline con OIDC AWS, attestation SLSA L2, cosign sign images, branch protection-as-code Terraform, ARC ephemeral runners, fork-PR isolation, security scanning CodeQL. Demo end-to-end.
