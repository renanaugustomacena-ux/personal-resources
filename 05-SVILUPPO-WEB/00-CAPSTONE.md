# Capstone — Sviluppo Web Full-Stack

> **Tempo stimato:** 30-50 ore in 4-6 settimane
> **Livello:** competent → proficient
> **Prerequisiti:** completamento di tutti i moduli del corso (Fasi 1-5)
> **Aggiornamento:** 2026-05-23

---

## Scenario

Sei il lead frontend/full-stack developer di una startup che sta lanciando una piattaforma di project management real-time. Il tuo compito è progettare e implementare un'applicazione Next.js 15 production-grade con autenticazione sicura, comunicazione WebSocket, security headers, testing E2E e deploy ottimizzato.

---

## Deliverable

### D1 — Progetto e Struttura (3-4 ore)

1. **Inizializzazione progetto Next.js 15 App Router**:
   - `create-next-app` con TypeScript strict, ESLint, Tailwind CSS
   - Struttura directory: `app/`, `components/`, `lib/`, `hooks/`, `types/`
   - `tsconfig.json` con `strict: true`, path aliases
   - `.env.local` con variabili tipizzate (Zod schema)

2. **Tooling configurato**:
   - ESLint + Prettier + Tailwind plugin
   - Playwright configurato per E2E
   - Vitest per unit test
   - Husky + lint-staged per pre-commit

### D2 — Autenticazione Completa (8-10 ore)

1. **Auth flow httpOnly**:
   - Login form → Server Action → set httpOnly cookie (access token)
   - Refresh token in cookie separato httpOnly + Secure + SameSite=Lax
   - Token rotation: ogni refresh genera nuovo refresh token e invalida il precedente
   - Revocation: logout invalida tutti i refresh token dell'utente nel database
   - Middleware Next.js per verifica automatica su ogni route protetta

2. **Passkey opt-in**:
   - WebAuthn registration flow
   - WebAuthn authentication flow
   - Fallback a password se passkey non disponibile

3. **Autorizzazione**:
   - RBAC (admin, member, viewer)
   - Middleware per route protection
   - Server-side permission check su ogni Server Action

### D3 — Security Headers e CSP (4-6 ore)

1. **CSP nonce middleware**:
   - `middleware.ts` genera nonce per ogni request
   - Nonce iniettato in `<script>` e `<style>` tags
   - CSP header: `script-src 'self' 'nonce-{RANDOM}'`
   - Blocco di `unsafe-inline` e `unsafe-eval`

2. **Security headers completi**:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
   - `Cross-Origin-Embedder-Policy: require-corp`
   - `Cross-Origin-Resource-Policy: same-origin`
   - SRI per script esterni

3. **Verifica**:
   - Test con `securityheaders.com` — grado A+
   - Nessun warning CSP in console
   - XSS test manuale fallisce (bloccato da CSP)

### D4 — WebSocket Real-Time (6-8 ore)

1. **WebSocket server**:
   - Autenticazione ticket-based (non token in URL)
   - Rate limiting per connessione (max messages/second)
   - Heartbeat con ping/pong (timeout 30s)
   - Graceful reconnection con exponential backoff

2. **Funzionalità real-time**:
   - Presence: utenti online nel progetto
   - Live updates: modifiche task visibili in tempo reale
   - Cursor sharing (opzionale): posizione cursore collaboratori

3. **Sicurezza WS**:
   - Frame validation (max size, type check)
   - Origin validation
   - Connection limit per IP
   - Audit log connessioni

### D5 — UI e Performance (4-6 ore)

1. **UI production-grade**:
   - Dashboard con Kanban board
   - Responsive (mobile-first)
   - Accessibilità WCAG 2.2 (keyboard nav, screen reader, contrast)
   - Dark/light mode con CSS custom properties

2. **Core Web Vitals**:
   - LCP < 2.5s (ottimizzare hero, fonts, images)
   - INP < 200ms (no long tasks, code splitting)
   - CLS < 0.1 (dimensioni esplicite, font-display: swap)
   - Bundle JS < 150kb gzipped (Vite tree-shaking, dynamic import)

### D6 — Testing E2E (4-6 ore)

1. **Test suite Playwright**:
   - Page Object Model per ogni pagina
   - Test auth flow: login, logout, expired token, refresh rotation
   - Test WebSocket: connessione, messaggio, disconnessione
   - Test CRUD: create/read/update/delete task
   - Test responsive: mobile viewport
   - Test accessibility: axe-core integration

2. **Unit + Integration test**:
   - Vitest per utility functions
   - MSW per mock API
   - Testing Library per componenti React
   - Coverage ≥ 80%

### D7 — Deploy e Demo (3-4 ore)

1. **Deploy**:
   - Vercel con custom domain + HTTPS
   - Environment variables configurate
   - Database PostgreSQL (Neon/Supabase)
   - CI/CD GitHub Actions: lint, type-check, test, deploy

2. **Demo live** (15 minuti):
   - Auth flow completo (login → dashboard → logout)
   - Real-time: due browser, modifiche sincronizzate
   - Security: CSP block dimostrato, headers verificati
   - Performance: Lighthouse score ≥ 90
   - Test E2E: run Playwright suite

---

## Rubric di Valutazione

| Area | Peso | Pass (70%) | Distinction (90%) |
|------|------|------------|-------------------|
| **Auth + Security** | 25% | Login/logout httpOnly funzionante | Refresh rotation, revocation, passkey, RBAC |
| **CSP + Headers** | 15% | CSP base funzionante | Nonce middleware, tutti gli headers, A+ securityheaders |
| **WebSocket** | 15% | Connessione WS base funzionante | Ticket auth, rate limiting, heartbeat, reconnection |
| **UI + Performance** | 15% | UI responsive base | WCAG 2.2, CWV sotto soglia, bundle budget rispettato |
| **Testing** | 15% | Test base funzionanti | Playwright POM, MSW, coverage 80%+, a11y test |
| **Deploy + CI** | 15% | Deploy funzionante | CI/CD completa, custom domain, monitoring |

**Totale: 100%. Pass ≥ 70%, Distinction ≥ 90%.**

---

## Vincoli

- **Framework**: Next.js 15 App Router (non Pages Router)
- **Linguaggio**: TypeScript 5.x strict mode
- **Styling**: Tailwind CSS 4 (non CSS Modules/styled-components per il capstone)
- **Database**: PostgreSQL (Neon, Supabase, o Docker locale)
- **ORM**: Prisma o Drizzle ORM
- **Auth**: Implementazione custom (non NextAuth/Auth.js per il capstone — scopo didattico)
- **Testing**: Playwright + Vitest + Testing Library
- **Deploy**: Vercel o Netlify
- **Node.js**: 22 LTS

---

## Suggerimenti

1. **Auth first** — il flusso httpOnly + rotation è il pezzo più complesso. Inizia da qui.
2. **CSP nonce subito** — configurare il middleware CSP prima di aggiungere script. Retrofare è doloroso.
3. **WebSocket dopo auth** — il ticket-based auth richiede che il sistema auth sia completo.
4. **Test while you build** — ogni feature aggiunta ha il suo test Playwright. Non lasciare alla fine.
5. **Performance last** — ottimizza CWV quando l'app è funzionalmente completa.

---

## Cross-link al percorso

| Deliverable | Moduli chiave |
|-------------|---------------|
| D1 Struttura | 06 (TypeScript), 25 (Next.js), 16 (build tools) |
| D2 Auth | 13 (autenticazione), 14 (sicurezza), 25 (Next.js middleware) |
| D3 CSP | 14 (sicurezza web), 05 (CORS), 22 (rate limiting) |
| D4 WebSocket | 23 (WebSocket security), 10 (Node.js), 22 (rate limiting) |
| D5 UI/Perf | 01 (HTML5 a11y), 02 (CSS3), 17 (performance), 07 (React) |
| D6 Testing | 15 (testing), 19 (troubleshooting) |
| D7 Deploy | 16 (deploy), 25 (Next.js deploy) |
