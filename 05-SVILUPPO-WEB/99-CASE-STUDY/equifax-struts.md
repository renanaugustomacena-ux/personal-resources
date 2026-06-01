# Case Study — Equifax Apache Struts breach (2017)

> **Aggiornamento:** 2026-04-27

## Cronologia

**2017-03-08** — Apache Struts CVE-2017-5638 (Jakarta Multipart parser RCE) disclosed.

**2017-03-09 → 2017-05-13** — Equifax non patched. Attaccante exploit la CVE per ottenere RCE su web facing app.

**2017-05-13 → 2017-07-29** — Lateral movement. Exfiltration di 147M records di credit data US (SSN, DOB, address, drivers license).

**2017-07-29** — Equifax detect intrusion.

**2017-09-07** — Public disclosure.

**Settlement:** $700M FTC settlement, miliardi di danni reputational.

## Lezioni

1. **Patch CVE critical in giorni, non mesi.** Equifax patch flow era broken.
2. **Inventory delle vulnerable application.** Equifax non sapeva dove Struts fosse usato.
3. **Network segmentation.** Web facing app non doveva avere accesso a DB con tutti i record.
4. **Encryption at rest per dati sensitive.**

## Riferimenti

- US House Oversight Committee report. https://oversight.house.gov/
- Apache Struts CVE-2017-5638. https://nvd.nist.gov/vuln/detail/cve-2017-5638

## Cross-links

- Modulo 14 — `../14-sicurezza-web.md`.
