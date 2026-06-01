# Case Study — Cloudflare October 2024 Incident

> **Last updated:** 2026-04-27 (synthesis)

## Timeline

**2024-10-25** — Cloudflare experiences degraded service across multiple regions for ~3 hours. Workers, Pages, Stream affected. R2 storage partially impacted.

**Root cause:** internal config change deployed via Cloudflare's own CDN; config corrupted; cascading failure across edge nodes attempting to fetch new config.

**Mitigation:** rollback config + force re-fetch from origin.

**Recovery:** 100% recovered ~3 hours after incident start.

## Lessons

1. **Self-hosted config delivery has SPOF risk.** Cloudflare hosting Cloudflare's config = circular dependency.
2. **Config rollout: canary + gradual.** Avoid global synchronous push.
3. **Independent verification of critical changes pre-deploy.**
4. **Status page hosting separate from main infra.** Dependencies leak otherwise.

## References

- Cloudflare blog postmortem (search status.cloudflare.com archives).
- HN discussion thread.

## Cross-links

- Module 05.5 — Observability.
- Module 08.7 — Incident Response.
