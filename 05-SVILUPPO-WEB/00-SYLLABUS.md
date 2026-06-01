# Syllabus — Sviluppo Web Full-Stack (Moderno e Sicuro)

> **Lingua:** italiano · **Aggiornamento:** 2026-05-23
> **Versioni:** HTML Living Standard; CSS (Living Standard + W3C Drafts); ECMAScript 2024+; TypeScript 5.x; React 19; Vue 3.5; Svelte 5; Next.js 15; Node.js 22 LTS; Vite 6; Playwright 1.x; MSW 2.x.
> **Moduli:** 25 + 2 case study + scaffolding
> **Tempo stimato:** 18-24 settimane (studio part-time) + 4-6 settimane capstone

---

## Identità

**"Sviluppo web full-stack — moderno e sicuro"** — dallo standard HTML/CSS/JS al deploy production-grade con Next.js 15 App Router, autenticazione httpOnly con refresh rotation, CSP nonce middleware, WebSocket sicuri, rate limiting edge, GraphQL con DataLoader, testing E2E Playwright, Core Web Vitals sotto soglia.

**Target:** competent → proficient (Dreyfus 3 → 4). Capace di progettare, implementare e deployare un'applicazione web full-stack production-grade con mitigazione OWASP Top 10, test E2E, bundle budget, accessibility WCAG 2.2.

## Prerequisiti

HTTP/REST/JSON basics; Git fluente (corso 07); CLI Linux/macOS; programmazione base (variabili, funzioni, cicli).

## Obiettivi di Apprendimento

Al completamento del corso, lo studente sarà in grado di:

1. Scrivere markup HTML5 semantico conforme WCAG 2.2 (landmark, ARIA, contrast 4.5:1).
2. Utilizzare CSS moderno: Container Queries, `:has()`, CSS Nesting, `color-mix()`, Logical Properties, View Transitions.
3. Padroneggiare JavaScript ES2024+ (Temporal, async iteration, structured clone) e TypeScript 5.x (type narrowing, branded types, satisfies).
4. Sviluppare con i tre framework principali: React 19 (RSC, Server Actions, Suspense), Vue 3.5 (Composition API, Vapor), Svelte 5 (runes, fine-grained reactivity).
5. Progettare API REST con cursor pagination (RFC 5988), error format RFC 7807, e API GraphQL con schema-first, DataLoader, persisted queries.
6. Implementare autenticazione completa: httpOnly cookie + refresh token rotation + revocation + passkey WebAuthn.
7. Applicare security headers production-grade: CSP nonce middleware, HSTS preload, Permissions-Policy, CORP/COEP, SRI.
8. Testare con React Testing Library (async `act()`), MSW per mocking API, Playwright POM per E2E cross-browser.
9. Ottimizzare Core Web Vitals: LCP < 2.5s, INP < 200ms, CLS < 0.1, bundle budget < 150kb JS gzipped.
10. Implementare WebSocket sicuri con autenticazione ticket-based, rate limiting, heartbeat, e reconnection con backoff.
11. Configurare rate limiting edge con token bucket, sliding window, e protezione DDoS layer 7.
12. Deployare con Vite, Docker multi-stage, Vercel/Netlify, CI/CD con GitHub Actions.

## Struttura del Corso

### Fase 1 — Fondamenti Web (settimane 1-4)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 01 | [HTML5](01-html5.md) | Semantica strutturale, WCAG 2.2, Dialog/Popover API, form validation |
| 02 | [CSS3](02-css3.md) | Container Queries, :has(), Nesting, Logical Properties, View Transitions |
| 03 | [CSS Framework](03-css-framework.md) | Tailwind CSS 4, Bootstrap 5, design system, utility-first vs component |
| 04 | [JavaScript fondamenti](04-javascript-fondamenti.md) | ES2024+, closures, prototypes, event loop, promises |
| 05 | [JavaScript avanzato](05-javascript-avanzato.md) | CORS, modules, Web Workers, Proxy/Reflect, structured clone |
| 06 | [TypeScript](06-typescript.md) | Type narrowing, generics, branded types, satisfies, declaration files |

### Fase 2 — Framework Frontend (settimane 5-8)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 07 | [React](07-react.md) | React 19, RSC, Server Actions, Suspense, hooks, state management |
| 08 | [Vue](08-vue.md) | Vue 3.5, Composition API, Pinia, Vapor mode, SSR/SSG con Nuxt |
| 09 | [Svelte](09-svelte.md) | Svelte 5 runes, fine-grained reactivity, SvelteKit, form actions |
| 21 | [RSC e Server-Driven UI](21-rsc-server-driven-ui.md) | React Server Components, streaming, selective hydration, cache layers |
| 25 | [Next.js](25-nextjs-guida-completa.md) | Next.js 15 App Router, middleware, ISR, Server Actions, deploy |

### Fase 3 — Backend, Dati e API (settimane 9-12)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 10 | [Node.js](10-nodejs.md) | Node.js 22 LTS, ESM, streams, worker threads, clustering |
| 11 | [API Design](11-api-design.md) | REST cursor pagination, RFC 7807, versioning, GraphQL intro |
| 24 | [GraphQL](24-graphql-guida-completa.md) | Schema-first, resolvers, DataLoader, subscriptions, persisted queries |
| 12 | [Database Web](12-database-web.md) | PostgreSQL, Prisma, Drizzle, Redis, connection pooling, migrations |

### Fase 4 — Sicurezza e Autenticazione (settimane 13-15)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 13 | [Autenticazione e Autorizzazione](13-autenticazione-autorizzazione.md) | httpOnly cookie, refresh rotation, revocation, passkey, OAuth 2.1 |
| 14 | [Sicurezza Web](14-sicurezza-web.md) | CSP nonce, OWASP Top 10 2023, HSTS, CORP/COEP, SRI, Helmet |
| 22 | [Rate Limiting Edge](22-rate-limiting-edge.md) | Token bucket, sliding window, edge middleware, DDoS L7 |
| 23 | [WebSocket Security](23-websocket-security.md) | Ticket-based auth, frame validation, rate limiting, heartbeat |

### Fase 5 — Quality e Production (settimane 16-20)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 15 | [Testing Web](15-testing-web.md) | RTL async act(), MSW, Playwright POM, visual regression, a11y test |
| 16 | [Build Tools e Deploy](16-build-tools-e-deploy.md) | Vite 6, Rollup, esbuild, Docker, Vercel, Netlify, CI/CD |
| 17 | [Performance Web](17-performance-web.md) | Core Web Vitals, bundle budget, lazy loading, image optimization |
| 18 | [PWA e Tecnologie Avanzate](18-pwa-e-tecnologie-avanzate.md) | Service Worker, Web Push, WebAssembly, WebGPU, View Transitions |
| 19 | [Troubleshooting](19-troubleshooting-e-guide-pratiche.md) | DevTools, network debug, memory leaks, common pitfalls, recipes |

### Fase 6 — Capstone (settimane 21-26)

Vedi [00-CAPSTONE.md](00-CAPSTONE.md) per il brief completo.

---

## Materiale Supplementare

| Risorsa | Scopo |
|---------|-------|
| [00-INDEX.md](00-INDEX.md) | Indice completo con sinossi |
| [00-GLOSSARIO.md](00-GLOSSARIO.md) | Glossario termini del corso |
| [00-BIBLIOGRAFIA.md](00-BIBLIOGRAFIA.md) | Fonti primarie consolidate |
| [00-CAPSTONE.md](00-CAPSTONE.md) | Progetto finale: brief, deliverable, rubric |
| [00-guida-allo-studio.md](00-guida-allo-studio.md) | Guida allo studio originale (legacy) |
| [99-CASE-STUDY/](99-CASE-STUDY/) | Case study: Equifax Struts, Cloudflare regex 2019 |
| [99-ESERCIZI/](99-ESERCIZI/) | Esercizi aggiuntivi per modulo |

---

## Valutazione

| Componente | Peso |
|------------|------|
| Capstone: Next.js App + Auth httpOnly | 25% |
| Capstone: CSP + Security Headers | 15% |
| Capstone: WebSocket + Rate Limiting | 15% |
| Capstone: Testing E2E Playwright | 15% |
| Capstone: Performance CWV | 15% |
| Capstone: Deploy + CI/CD | 15% |

**Pass ≥ 70%, Distinction ≥ 90%.** Vedi [00-CAPSTONE.md](00-CAPSTONE.md) per la rubric dettagliata.
