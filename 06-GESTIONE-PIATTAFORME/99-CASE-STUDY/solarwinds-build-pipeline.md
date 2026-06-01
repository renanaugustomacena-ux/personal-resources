# Case Study — SolarWinds Build Pipeline (2020 SUNBURST)

> **Aggiornamento:** 2026-04-27

## Cronologia

**2019-2020** — Russian state actor (APT29/Cozy Bear) compromise SolarWinds Orion build pipeline. Inserito malware (SUNBURST) in 2 versioni di Orion; firmate con cert SolarWinds legitimo; distribuite a 18000 clienti via auto-update.

**2020-12-13** — FireEye (vittima) public disclosure.

**Impact:** 100+ orgs compromise inclusi US Gov agencies (Treasury, DoJ, DoD parziale), Microsoft, Cisco, Mimecast.

## Lezioni supply-chain

1. **Build pipeline e target high-value.** Compromettere build = distribuire malware a tutti i clienti.
2. **Code signing alone NON e sicurezza.** Firma legittima se attaccante ha accesso a build.
3. **SLSA principles addressano questo: hermetic builds, attestation, two-party review.**
4. **SBOM + CVE scan in CI/CD: detect malicious dependency.**
5. **Reproducible builds: chiunque puo verificare l'output.**

## Riferimenti

- US-CERT advisory. https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-352a
- FireEye/Mandiant report. https://cloud.google.com/blog/topics/threat-intelligence/

## Cross-links

- Modulo 20 — `../20-supply-chain-slsa-cosign.md`.
- Modulo 13 — `../13-sicurezza-piattaforme.md`.
