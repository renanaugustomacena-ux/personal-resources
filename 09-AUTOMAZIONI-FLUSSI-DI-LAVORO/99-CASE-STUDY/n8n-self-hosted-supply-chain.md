# Case Study — n8n Self-Hosted Supply Chain Risks

> **Tipo:** scenari di rischio supply-chain per n8n self-hosted.
> **Aggiornamento:** 2026-04-27

## Scenari di rischio

### Docker image compromise

n8n ufficiale Docker image e firmata, ma se l'attaccante compromise il registry o sostituisce l'immagine in private registry locale, il workflow runtime ha codice arbitrario. **Mitigazione**: cosign verify, image digest pinning, internal registry con scan SCA.

### Custom node injection

n8n permette di installare custom node da npm. Un node malicious puo esfiltrare credentials. **Mitigazione**: review dei custom node, isolamento (container separato per n8n), egress firewall.

### Dependency vulnerabilities

n8n e un Node.js project con ~600+ dependency. Vulnerability in transitive dep si propaga. **Mitigazione**: `npm audit` in CI, Dependabot, image rebuild settimanale.

### Credential exfiltration via workflow

Un utente con accesso n8n puo creare un workflow che dump tutte le credentials a un endpoint esterno. **Mitigazione**: RBAC stretto, audit log, alert su workflow che invia credenziali a domini sconosciuti.

## Lezioni operative

1. **Self-hosted ≠ piu sicuro automaticamente.** Aumenta surface, sposta responsabilita a te.
2. **Zero-trust per il workflow engine.** Egress firewall + audit + scan.
3. **Subscription/OSS canale aggiornamenti.** Conoscere CVE n8n al rilascio.
4. **Backup disaster scenario: encryption key persa.** Documenta procedure recovery.

## Riferimenti

- n8n security advisories. https://github.com/n8n-io/n8n/security
- npm — security best practices. https://docs.npmjs.com/about-audit-reports
- OWASP — Software Supply Chain Security top 10.

## Collegamenti incrociati

- Modulo 09 — `../09-n8n-guida-completa-self-hosted.md`.
- Modulo 12 — `../../12-SOFTWARE-ENGINEERING-EXTRA/` (quando scaffolded; security topics).
