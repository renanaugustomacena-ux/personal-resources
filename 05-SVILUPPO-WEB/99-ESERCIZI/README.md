# 99-ESERCIZI — Sviluppo Web

## Lab

- `lab-01-nextjs-auth.md` — Next.js App Router con auth httpOnly + rotation + revocation.
- `lab-02-csp-nonce.md` — CSP nonce middleware Next.js + verify no XSS.
- `lab-03-webvitals.md` — Optimize CWV per landing page; LCP < 2.5s, INP < 200ms.

## Scenari

- `scenario-01-cors-nightmare.md` — CORS preflight fail; debug.
- `scenario-02-redos-detection.md` — Regex catastrofica in production code; identify + fix.
- `scenario-03-token-theft.md` — Refresh token rubato; rotation salvataggio.

## Lab 01 — Next.js auth completo

App Next.js 15 con:
1. Login form → server action → set httpOnly cookie + refresh token in cookie separato.
2. Middleware verifica cookie, refresh automatico se expired.
3. Logout invalida refresh in DB.
4. Test E2E: login, logout, expired token, theft detection.
