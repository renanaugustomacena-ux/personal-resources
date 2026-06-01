# Glossario — Sviluppo Web Full-Stack

> **Aggiornamento:** 2026-05-23
> **Nota:** Termini introdotti nei moduli del corso. Per definizioni estese, consultare il modulo indicato.

---

## A

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **ARIA** | Accessible Rich Internet Applications — attributi per accessibilità widget dinamici. | 01 |
| **App Router** | Sistema di routing Next.js 15 basato su filesystem con `app/` directory. | 25 |
| **`act()`** | Wrapper React Testing Library per trigger state updates in test. | 15 |
| **Auth code + PKCE** | OAuth 2.1 flow standard con Proof Key for Code Exchange (RFC 7636). | 13 |
| **AVIF** | AV1 Image Format — compressione lossy/lossless moderna per web. | 17 |

## B–C

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **Branded type** | TypeScript pattern per tipi nominali via intersection con campo unico. | 06 |
| **Bundle budget** | Limite massimo JS/CSS per pagina (es. 150kb gzipped). | 17 |
| **CDN** | Content Delivery Network — distribuzione statica edge. | 16, 17 |
| **CLS** | Cumulative Layout Shift — metrica stabilità visiva (target < 0.1). | 17 |
| **Container Query** | CSS query basata su container size (`@container`). | 02 |
| **`color-mix()`** | CSS function per miscelare colori in spazio colore specificato. | 02 |
| **Composition API** | Vue 3 pattern per logica componenti con `setup()`, `ref()`, `computed()`. | 08 |
| **CORP** | Cross-Origin Resource Policy — header per protezione risorse cross-origin. | 14 |
| **COEP** | Cross-Origin Embedder Policy — header per isolamento cross-origin. | 14 |
| **CORS** | Cross-Origin Resource Sharing — meccanismo permessi cross-origin. | 05, 14 |
| **Core Web Vitals** | Metriche Google performance: LCP, INP, CLS. | 17 |
| **CSP** | Content Security Policy — header per whitelist risorse eseguibili. | 14 |
| **CSP nonce** | Token one-time per autorizzare inline script/style in CSP. | 14 |
| **CSRF** | Cross-Site Request Forgery — attacco che sfrutta sessione autenticata. | 14 |
| **CSR** | Client-Side Rendering — rendering interamente nel browser. | 07, 21 |
| **CSS Nesting** | Sintassi CSS nativa per annidare selettori (`& .child`). | 02 |
| **Cursor pagination** | Paginazione basata su cursore opaco (non offset). | 11, 24 |

## D–E

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **DataLoader** | Pattern batching + caching per GraphQL resolvers (evita N+1). | 11, 24 |
| **Drizzle ORM** | ORM TypeScript-first con SQL-like query builder. | 12 |
| **Dynamic import** | `import()` asincrono per code splitting on-demand. | 04, 17 |
| **Edge runtime** | Ambiente esecuzione leggero (V8 isolates) per middleware edge. | 22, 25 |
| **ESM** | ECMAScript Modules — sistema moduli nativo (`import`/`export`). | 04, 10 |
| **`esbuild`** | Bundler Go-based ultra-veloce, usato da Vite per transform. | 16 |
| **Event loop** | Ciclo single-threaded di Node.js/browser per I/O non-bloccante. | 04, 10 |

## F–G

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`fetchpriority`** | Attributo HTML per prioritizzare caricamento risorse (high/low/auto). | 17 |
| **`font-display`** | Proprietà CSS per strategia visualizzazione font durante caricamento. | 02, 17 |
| **Form Action** | SvelteKit/Next.js pattern per progressive enhancement form. | 09, 25 |
| **GraphQL** | Query language per API con type system e singolo endpoint. | 24 |

## H–I

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`:has()`** | CSS pseudo-class per selezionare parent basandosi su child. | 02 |
| **Heartbeat** | Meccanismo ping/pong per verificare connessione WebSocket attiva. | 23 |
| **Helmet** | Middleware Node.js per impostare security headers automaticamente. | 14 |
| **HSTS** | HTTP Strict Transport Security — forza HTTPS (RFC 6797). | 14 |
| **httpOnly cookie** | Cookie inaccessibile a JavaScript (protezione XSS). | 13 |
| **Hydration** | Processo di attach event handler a HTML server-rendered. | 07, 21 |
| **Idempotency** | Proprietà: operazione ripetuta produce stesso risultato. | 11 |
| **INP** | Interaction to Next Paint — metrica reattività (target < 200ms). | 17 |
| **ISR** | Incremental Static Regeneration — rigenerazione pagine statiche on-demand. | 25 |

## J–L

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **JWT** | JSON Web Token — token compatto per claims (RFC 7519). | 13 |
| **LCP** | Largest Contentful Paint — metrica caricamento (target < 2.5s). | 17 |
| **Layout shift** | Spostamento inatteso di elementi durante caricamento pagina. | 17 |
| **Lazy loading** | Caricamento differito di risorse non visibili (`loading="lazy"`). | 17 |
| **Logical Properties** | CSS properties RTL/LTR-aware (`margin-inline-start` vs `margin-left`). | 02 |

## M–N

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **Middleware** | Funzione intercettore request/response (Next.js, Express, Edge). | 14, 22, 25 |
| **MSW** | Mock Service Worker — intercetta network requests per test. | 15 |
| **MPA** | Multi-Page Application — navigazione tradizionale con full reload. | 18 |

## O–P

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **OWASP Top 10** | Le 10 vulnerabilità web più critiche (classificazione 2021). | 14 |
| **Page Object Model** | Pattern Playwright per incapsulare interazione pagina in test. | 15 |
| **Passkey** | Credenziale WebAuthn per autenticazione passwordless. | 13 |
| **`Permissions-Policy`** | Header per disabilitare API browser (camera, mic, geolocation). | 14 |
| **Persisted queries** | GraphQL: query pre-registrate sul server, client invia solo hash. | 24 |
| **Pinia** | State management ufficiale Vue 3 (successore di Vuex). | 08 |
| **POM** | Page Object Model — pattern test E2E. | 15 |
| **Prefetch** | Caricamento anticipato di risorse per navigazione futura. | 17, 25 |
| **Prisma** | ORM TypeScript con schema declarativo e type-safe queries. | 12 |
| **Progressive enhancement** | Strategia: funzionalità base senza JS, miglioramenti con JS. | 09, 18 |
| **PWA** | Progressive Web App — web app con capabilities native. | 18 |

## R

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **Rate limiting** | Limite richieste per unità di tempo per client/IP. | 22 |
| **ReDoS** | Regular Expression Denial of Service — regex catastrofica. | 14, 19 |
| **Refresh rotation** | Refresh token sostituito a ogni uso (mitiga theft). | 13 |
| **`Referrer-Policy`** | Header che controlla invio Referer nelle richieste. | 14 |
| **RFC 7807** | Problem Details for HTTP APIs — formato standard errori. | 11 |
| **RSC** | React Server Components — componenti renderizzati esclusivamente sul server. | 07, 21 |
| **RTL** | React Testing Library — test componenti React user-centric. | 15 |
| **Runes** | Svelte 5 primitivi reattivi (`$state`, `$derived`, `$effect`). | 09 |

## S

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`SameSite`** | Cookie attribute per protezione CSRF (Strict/Lax/None). | 13, 14 |
| **`satisfies`** | TypeScript operator per type-checking senza widening. | 06 |
| **Selective hydration** | React pattern: hydrate componenti in ordine di priorità/interazione. | 21 |
| **Server Action** | Funzione server-side invocabile direttamente da form/client. | 07, 25 |
| **Service Worker** | Worker script per caching, offline, push notifications. | 18 |
| **Sliding window** | Algoritmo rate limiting con finestra temporale mobile. | 22 |
| **SPA** | Single-Page Application — navigazione client-side senza reload. | 07 |
| **SRI** | Subresource Integrity — verifica hash script/style esterni. | 14 |
| **SSG** | Static Site Generation — pre-rendering pagine al build time. | 25 |
| **SSR** | Server-Side Rendering — rendering lato server per ogni request. | 07, 25 |
| **Streaming** | Invio progressivo HTML durante rendering server-side. | 21, 25 |
| **Structured clone** | Algoritmo deep copy nativo (`structuredClone()`). | 05 |
| **Suspense** | React boundary per gestire stati loading/fallback. | 07, 21 |

## T

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **TanStack Query** | Libreria data fetching per React (ex React Query). | 07, 12 |
| **Ticket-based auth** | Autenticazione WebSocket via token temporaneo ottenuto via HTTP. | 23 |
| **Token bucket** | Algoritmo rate limiting con capacità burst. | 22 |
| **Tree shaking** | Eliminazione codice morto dal bundle (basata su ESM). | 16, 17 |
| **Type narrowing** | TypeScript: restringere tipo tramite control flow analysis. | 06 |

## U–V

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **Vapor mode** | Vue 3 rendering ottimizzato senza virtual DOM. | 08 |
| **View Transitions** | API browser per animare transizioni tra stati/pagine. | 02, 18 |
| **Vite** | Build tool moderno basato su ESM + Rollup (HMR nativo). | 16 |
| **Vitest** | Test runner Vite-native, compatibile API Jest. | 15 |

## W–Z

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **WAF** | Web Application Firewall — filtraggio traffico layer 7. | 14, 22 |
| **WCAG 2.2** | Web Content Accessibility Guidelines — standard accessibilità W3C. | 01 |
| **Web Push** | API per push notification via Service Worker. | 18 |
| **WebAssembly** | Formato binario per esecuzione near-native nel browser. | 18 |
| **WebAuthn** | Web Authentication API per credenziali biometriche/hardware. | 13 |
| **WebGPU** | API moderna per GPU computation e rendering nel browser. | 18 |
| **WebSocket** | Protocollo bidirezionale persistente su TCP (RFC 6455). | 23 |
| **Worker threads** | Node.js: thread paralleli per CPU-intensive work. | 10 |
| **XSS** | Cross-Site Scripting — iniezione script malevolo in pagina. | 14 |
| **Zustand** | State management React minimale con hook-based API. | 07 |

---

> **Conteggio termini:** ~130
> **Ultimo aggiornamento:** 2026-05-23
