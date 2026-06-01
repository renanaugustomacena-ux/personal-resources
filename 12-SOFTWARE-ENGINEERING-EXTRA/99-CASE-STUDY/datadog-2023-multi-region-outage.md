# Case Study — Datadog March 2023 Multi-Region Outage

> **Last updated:** 2026-04-27

## Timeline

**2023-03-08 (Wednesday)** — Datadog experiences ~24 hours global outage across multiple regions. Most monitoring tools (irony) cannot detect own outage.

**Root cause:** systemd config change auto-deployed via Datadog's own infrastructure tooling; bug in update caused systemd to crash on every Datadog node simultaneously globally.

**Recovery:** manual fix on every node; global recovery ~24h.

**Customer impact:** customers couldn't see their own observability metrics during outage. Cascading: those who relied on Datadog alerts missed their own incidents.

## Lessons

1. **Don't deploy infra-wide change synchronously across regions.**
2. **Bug in shared component = global blast radius.** Decoupling between regions critical.
3. **Customer alerting must have backup independent path.**
4. **Status page on independent infrastructure (Datadog status page was on Datadog).**
5. **24h recovery time = financial damage to customers + Datadog reputation.**

## References

- Datadog public postmortem (their blog).
- HN extensive discussion.

## Cross-links

- Module 05.5 — Observability.
- Module 05.3 — SRE.
