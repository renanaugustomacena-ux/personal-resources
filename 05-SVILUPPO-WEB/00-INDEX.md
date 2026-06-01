# Indice — Sviluppo Web Full-Stack

> **Corso:** Sviluppo web full-stack — moderno e sicuro
> **Aggiornamento:** 2026-05-23
> **Moduli:** 25 + 2 case study + scaffolding
> **Percorso consigliato:** vedi [00-SYLLABUS.md](00-SYLLABUS.md)

---

## File di Scaffolding

| File | Scopo | Stato |
|------|-------|-------|
| [00-SYLLABUS.md](00-SYLLABUS.md) | Percorso formativo, fasi, prerequisiti, capstone | stable |
| [00-INDEX.md](00-INDEX.md) | Questo file — indice completo | stable |
| [00-GLOSSARIO.md](00-GLOSSARIO.md) | Glossario termini introdotti nel corso | stable |
| [00-BIBLIOGRAFIA.md](00-BIBLIOGRAFIA.md) | Fonti primarie consolidate | stable |
| [00-CAPSTONE.md](00-CAPSTONE.md) | Progetto finale: brief, deliverable, rubric | stable |
| [00-guida-allo-studio.md](00-guida-allo-studio.md) | Guida allo studio originale (legacy) | base |

---

## Moduli del Corso

### Fase 1 — Fondamenti Web

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 01 | [html5.md](01-html5.md) | Semantica strutturale, WCAG 2.2, Dialog, Popover API, form validation HTML5 | stable |
| 02 | [css3.md](02-css3.md) | Container Queries, :has(), Nesting, Logical Properties, View Transitions, color-mix() | stable |
| 03 | [css-framework.md](03-css-framework.md) | Tailwind CSS 4, Bootstrap 5, design system, utility-first, component library | stable |
| 04 | [javascript-fondamenti.md](04-javascript-fondamenti.md) | ES2024+, closures, prototypes, event loop, promises, error handling | stable |
| 05 | [javascript-avanzato.md](05-javascript-avanzato.md) | CORS deep dive, modules ESM, Web Workers, Proxy, structured clone, Private Network Access | stable |
| 06 | [typescript.md](06-typescript.md) | Type narrowing, generics, branded types, satisfies, conditional types, declaration files | stable |

### Fase 2 — Framework Frontend

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 07 | [react.md](07-react.md) | React 19, RSC, Server Actions, Suspense, hooks, context, state management | stable |
| 08 | [vue.md](08-vue.md) | Vue 3.5, Composition API, Pinia, Vapor mode, SSR/SSG con Nuxt 3 | stable |
| 09 | [svelte.md](09-svelte.md) | Svelte 5 runes, fine-grained reactivity, SvelteKit, form actions, transitions | stable |
| 21 | [rsc-server-driven-ui.md](21-rsc-server-driven-ui.md) | React Server Components, streaming HTML, selective hydration, cache layers | stable |
| 25 | [nextjs-guida-completa.md](25-nextjs-guida-completa.md) | Next.js 15 App Router, middleware, ISR, Server Actions, deploy Vercel | stable |

### Fase 3 — Backend, Dati e API

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 10 | [nodejs.md](10-nodejs.md) | Node.js 22 LTS, ESM, streams, worker threads, clustering, diagnostics | stable |
| 11 | [api-design.md](11-api-design.md) | REST cursor pagination, RFC 7807, versioning, HATEOAS, rate limiting intro | stable |
| 24 | [graphql-guida-completa.md](24-graphql-guida-completa.md) | Schema-first, resolvers, DataLoader, subscriptions, persisted queries, security | stable |
| 12 | [database-web.md](12-database-web.md) | PostgreSQL, Prisma, Drizzle ORM, Redis, connection pooling, migrations | stable |

### Fase 4 — Sicurezza e Autenticazione

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 13 | [autenticazione-autorizzazione.md](13-autenticazione-autorizzazione.md) | httpOnly cookie, refresh rotation, revocation, passkey WebAuthn, OAuth 2.1 | stable |
| 14 | [sicurezza-web.md](14-sicurezza-web.md) | CSP nonce, OWASP Top 10 2023, HSTS, CORP/COEP, SRI, Helmet, Permissions-Policy | stable |
| 22 | [rate-limiting-edge.md](22-rate-limiting-edge.md) | Token bucket, sliding window, edge middleware, DDoS L7, Cloudflare/Vercel | stable |
| 23 | [websocket-security.md](23-websocket-security.md) | Ticket-based auth, frame validation, rate limiting WS, heartbeat, reconnection | stable |

### Fase 5 — Quality e Production

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 15 | [testing-web.md](15-testing-web.md) | RTL async act(), MSW, Playwright POM, visual regression, a11y testing | stable |
| 16 | [build-tools-e-deploy.md](16-build-tools-e-deploy.md) | Vite 6, Rollup, esbuild, Docker, Vercel, Netlify, CI/CD GitHub Actions | stable |
| 17 | [performance-web.md](17-performance-web.md) | Core Web Vitals, bundle budget, lazy loading, image optimization, prefetch | stable |
| 18 | [pwa-e-tecnologie-avanzate.md](18-pwa-e-tecnologie-avanzate.md) | Service Worker, Web Push, WebAssembly, WebGPU, View Transitions API | stable |
| 19 | [troubleshooting-e-guide-pratiche.md](19-troubleshooting-e-guide-pratiche.md) | DevTools avanzato, network debug, memory leaks, common pitfalls, recipes | stable |

---

## Materiale Supplementare

### Case Study

| File | Argomento |
|------|-----------|
| [99-CASE-STUDY/equifax-struts.md](99-CASE-STUDY/equifax-struts.md) | Equifax 2017: CVE-2017-5638 Apache Struts, data breach 147M record |
| [99-CASE-STUDY/cloudflare-regex-2019.md](99-CASE-STUDY/cloudflare-regex-2019.md) | Cloudflare 2019-07-02: ReDoS in WAF rule, outage globale 27 minuti |

### Esercizi Extra

| Directory | Contenuto |
|-----------|-----------|
| [99-ESERCIZI/](99-ESERCIZI/) | Lab e scenari pratici per modulo |
