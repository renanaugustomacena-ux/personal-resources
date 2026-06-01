# Case Study — Codecov bash uploader (2021)

> **Aggiornamento:** 2026-04-27

## Cronologia

**2021-01 → 2021-04** — Attaccante compromise Docker image GitLab usata da Codecov; modify bash uploader script; ogni run del script estrae env vars (incl. secrets/credentials) verso server attaccante.

**2021-04-15** — Codecov public disclosure post 3 mesi exposure.

**Impact:** 29000+ Codecov customer uploader scaricarono lo script compromesso. HashiCorp, Twilio, Cloudflare, Confluent, Mozilla tra noti vittime con secret exfiltrated.

## Lezioni supply-chain CI

1. **`curl | bash` antipattern.** Mai senza checksum/signature verification.
2. **Reading env vars in CI = ASA scenario worst-case.** Tutti secret dello stage exfiltrated.
3. **Pinning version + checksum.** Anche bash script, anche se lento.
4. **Secret scoping: minimum permission.** Rotation post-incident di TUTTI secret.
5. **Egress control da CI.** Outbound network restricted; attaccante non puo exfil.

## Riferimenti

- Codecov security update. https://about.codecov.io/security-update/
- HashiCorp postmortem. https://www.hashicorp.com/blog/

## Cross-links

- Modulo 07 — `../07-ci-cd.md`.
- Modulo 15 — `../15-secrets-management.md`.
- Modulo 20 — `../20-supply-chain-slsa-cosign.md`.
