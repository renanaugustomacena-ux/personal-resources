# Case Study — Cloudflare Regex Outage 2019-07-02

> **Aggiornamento:** 2026-04-27

## Cronologia

**2019-07-02 13:42 UTC** — Cloudflare deploys nuovo WAF rule con regex catastrofica: `(?:(?:\"|'|\]|\}|\\\\|\\d|(?:nan|infinity|true|false|null|undefined|symbol|math)|\`|\\-|\\+)+[)]*;?((?:\\s|-|~|!|{}|\\|\\||\\+)*.*(?:.*=.*)))`.

**Effetto:** regex backtracking esponenziale → CPU 100% su tutti i server CF globalmente.

**Outage:** Cloudflare global down ~30 min. 27 minuti per identify root cause + revert.

**Impact:** internet "rotto" per molti siti che dependono da Cloudflare. Clienti major (Discord, GitHub, Shopify pages) down.

## Lezioni

1. **Catastrophic regex (ReDoS) e classe di vulnerability sottovalutata.**
2. **Test regex con input adversarial pre-deploy.**
3. **Engine regex linear-time (Rust regex, RE2) per produzione.** Backtracking-free.
4. **Kill switch deploy WAF rule rapido, no full revert pipeline.**
5. **Cloudflare postmortem pubblico, esempio di transparency.**

## Riferimenti

- Cloudflare postmortem. https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/
- ReDoS OWASP. https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS

## Cross-links

- Modulo 14 — `../14-sicurezza-web.md`.
- Modulo 22 — `../22-rate-limiting-edge.md`.
