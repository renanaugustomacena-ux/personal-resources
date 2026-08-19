# Tutorial 25 — Next.js 15: Dal Principiante all'Esperto

> **Companion a:** `25-nextjs-guida-completa.md`
> **Scope:** App Router e file convenzionali · layout, template e stato persistente · segmenti dinamici, route group e `generateStaticParams` · Route Handler contro Server Action · cosa rende dinamica una rotta · middleware e i suoi limiti · CSP con nonce · sicurezza delle Server Action · metadata, immagini e font · parallel e intercepting route · confini d'errore · hydration mismatch · deploy standalone e self-hosting · test, migrazione e Turbopack
> **Prerequisiti:** `tutorial_07_react.md`, `tutorial_21_rsc_server_driven_ui.md`, `tutorial_16_build_tools_deploy.md`, `tutorial_14_sicurezza_web.md` — conosci React, il modello dei Server Component e i quattro livelli di cache
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Next.js 15 · React 19 · TypeScript 5.7 · Playwright · Docker

---

## Indice Generale

- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Il filesystem è il router](#a1-il-filesystem-è-il-router)
  - [A2. I file convenzionali](#a2-i-file-convenzionali)
  - [A3. Layout, template e lo stato che sopravvive](#a3-layout-template-e-lo-stato-che-sopravvive)
  - [A4. Segmenti dinamici, route group, generateStaticParams](#a4-segmenti-dinamici-route-group-generatestaticparams)
  - [A5. Route Handler o Server Action](#a5-route-handler-o-server-action)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Cosa rende dinamica una rotta](#b1-cosa-rende-dinamica-una-rotta)
  - [B2. Il middleware: cosa può e cosa non può](#b2-il-middleware-cosa-può-e-cosa-non-può)
  - [B3. CSP con nonce, dal middleware](#b3-csp-con-nonce-dal-middleware)
  - [B4. Le Server Action sono endpoint pubblici](#b4-le-server-action-sono-endpoint-pubblici)
  - [B5. Immagini, font e metadata](#b5-immagini-font-e-metadata)
  - [B6. Parallel e intercepting route](#b6-parallel-e-intercepting-route)
  - [B7. I confini d'errore, e quale copre cosa](#b7-i-confini-derrore-e-quale-copre-cosa)
  - [B8. L'idratazione che non corrisponde](#b8-lidratazione-che-non-corrisponde)
  - [B9. Il deploy fuori da Vercel](#b9-il-deploy-fuori-da-vercel)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: il portale in App Router](#c2-mini-progetto-il-portale-in-app-router)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Testare un'applicazione App Router](#d1-testare-unapplicazione-app-router)
  - [D2. Migrare dal Pages Router](#d2-migrare-dal-pages-router)
  - [D3. Osservare: instrumentation e after](#d3-osservare-instrumentation-e-after)
  - [D4. Turbopack e i tempi di build](#d4-turbopack-e-i-tempi-di-build)
  - [D5. Quando NON serve Next.js](#d5-quando-non-serve-nextjs)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   RICHIESTA
       │
   ┌───▼──────────────────────────────────────────────┐
   │ MIDDLEWARE (edge) — reindirizzamenti, header,    │
   │ nonce CSP. NON è autorizzazione (§B2)            │
   └───┬──────────────────────────────────────────────┘
       │
   ┌───▼──────────────────────────────────────────────┐
   │ ROUTING — il filesystem                          │
   │   app/(gruppo)/settore/[id]/page.tsx             │
   │   layout · template · loading · error            │
   └───┬──────────────────────────────────────────────┘
       │
   ┌───▼───────────────────┬──────────────────────────┐
   │ page.tsx              │ route.ts                 │
   │ Server Component      │ Route Handler (HTTP)     │
   │ + Server Action       │ per client non-browser   │
   └───┬───────────────────┴──────────────────────────┘
       │
   STATICA  o  DINAMICA — lo decide `cookies()`, `headers()`,
   `searchParams`, o una fetch senza cache (§B1)
```

---

# Parte A — Basi Assolute

---

## A1. Il filesystem è il router

> **Analogia:** gli scaffali di una biblioteca. Non c'è un registro che dice dove sta ogni libro: la posizione *è* la classificazione. Sposti la cartella, e l'indirizzo cambia con lei.

```
app/
├── layout.tsx              ► obbligatorio: contiene <html> e <body>
├── page.tsx                ► /
├── chi-siamo/
│   └── page.tsx            ► /chi-siamo
├── prodotti/
│   ├── page.tsx            ► /prodotti
│   └── [id]/
│       ├── page.tsx        ► /prodotti/42
│       └── recensioni/
│           └── page.tsx    ► /prodotti/42/recensioni
└── api/
    └── stato/
        └── route.ts        ► GET /api/stato

⚠ UNA CARTELLA NON È UNA ROTTA. Diventa raggiungibile solo se
  contiene `page.tsx` o `route.ts`. `app/utils/` con dentro solo
  funzioni non produce l'URL `/utils`, e questo permette di tenere
  i file accanto a dove servono invece che in una cartella lontana.
```

```
LE TRE DIFFERENZE CHE CONTANO RISPETTO AL PAGES ROUTER

  1. il file si chiama SEMPRE `page.tsx`, e la cartella dà il nome
     alla rotta — invece di `pages/prodotti/[id].tsx`
  2. i layout sono ANNIDATI e persistono fra le navigazioni (§A3)
  3. i componenti sono SERVER per difetto: `'use client'` è
     l'eccezione, non la regola (tutorial_21 §A2)
```

⚠ `app/` e `pages/` convivono nello stesso progetto, e per le rotte in conflitto vince `app/`. È ciò che rende possibile una migrazione incrementale (§D2).

---

## A2. I file convenzionali

| File | Cosa fa | Dove gira |
|---|---|---|
| `page.tsx` | l'interfaccia della rotta — senza, la rotta non esiste | Server |
| `layout.tsx` | l'involucro condiviso: **non** si rimonta navigando fra i figli | Server |
| `template.tsx` | come `layout`, ma **si rimonta** a ogni navigazione | Server |
| `loading.tsx` | il fallback: Next avvolge `page.tsx` in un `<Suspense>` | Server |
| `error.tsx` | il confine d'errore del segmento | **Client** |
| `global-error.tsx` | il confine che copre anche il root layout | **Client** |
| `not-found.tsx` | ciò che si vede dopo `notFound()` | Server |
| `route.ts` | un endpoint HTTP: non può stare accanto a `page.tsx` | Server |
| `default.tsx` | il ripiego di uno slot parallelo (§B6) | Server |

```
⚠ TRE COSE CHE SORPRENDONO

  1. `error.tsx` È SEMPRE UN CLIENT COMPONENT: lo richiede React,
     perché un confine d'errore ha bisogno di stato — e `'use
     client'` va scritto comunque, o la build fallisce
  2. `loading.tsx` NON È UNO SPINNER GENERICO: è un confine di
     Suspense sull'INTERA pagina, quindi uno spinner lì rende la
     pagina intera uno spinner anche se è lento un pezzo solo
     (tutorial_21 §B2)
  3. `page.tsx` E `route.ts` NON POSSONO CONVIVERE nella stessa
     cartella: sarebbero due risposte per lo stesso URL
```

---

## A3. Layout, template e lo stato che sopravvive

```tsx
// app/layout.tsx — il root layout è obbligatorio, ed è l'unico
// posto dove compaiono <html> e <body>
import type { Metadata } from 'next'

export const metadata: Metadata = {
  // `template` si applica al titolo delle pagine figlie
  title: { template: '%s · Portale', default: 'Portale' },
  description: 'Il portale aziendale',
}

export default function LayoutRadice({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body>
        <Intestazione />
        <main>{children}</main>
      </body>
    </html>
  )
}
```

```tsx
// app/(riservata)/layout.tsx — annidato. Il controllo qui vale per
// TUTTE le pagine sotto: è il posto giusto per ciò che accomuna,
// non per l'autorizzazione fine (§B2).
export default async function LayoutRiservata({ children }: { children: React.ReactNode }) {
  const utente = await utenteCorrente()
  if (!utente) redirect('/accedi')

  return (
    <div className="griglia">
      <BarraLaterale utente={utente} />
      <div>{children}</div>
    </div>
  )
}
```

```
LA DIFFERENZA FRA LAYOUT E TEMPLATE, e quando conta

  LAYOUT     l'istanza SOPRAVVIVE alla navigazione fra i figli. Lo
             scorrimento della barra laterale resta dov'era, un
             lettore audio continua a suonare, lo stato non si
             azzera.
  TEMPLATE   una istanza NUOVA a ogni navigazione: lo stato si
             azzera, gli effetti ripartono, le animazioni di
             ingresso si rivedono.

➜ IL PREDEFINITO GIUSTO È `layout`. `template` serve nei casi in
  cui il non-rimontaggio è il problema: un'animazione di ingresso
  per pagina, un `useEffect` che deve registrare ogni visita, un
  form che deve ripartire vuoto.

⚠ UN LAYOUT NON RICEVE `searchParams`. Riceve `params`, ma non la
  query string — perché non si rirenderizza quando questa cambia.
  Chi ha bisogno dei parametri di ricerca li legge nella `page`,
  o con `useSearchParams` in un Client Component.
```

---

## A4. Segmenti dinamici, route group, generateStaticParams

```
app/
├── (marketing)/            ► ROUTE GROUP: le parentesi NON entrano
│   ├── layout.tsx            nell'URL. Serve a dare layout diversi
│   ├── page.tsx              a sezioni diverse: /  e  /prezzi
│   └── prezzi/page.tsx       hanno il layout marketing…
├── (riservata)/
│   ├── layout.tsx            …e /cruscotto ha il suo
│   └── cruscotto/page.tsx
├── blog/
│   └── [slug]/page.tsx     ► /blog/qualcosa
├── negozio/
│   └── [...percorso]/page.tsx  ► /negozio/a/b/c — catch-all
└── documenti/
    └── [[...percorso]]/page.tsx ► anche /documenti — catch-all opzionale
```

```tsx
// app/blog/[slug]/page.tsx
// ⚠ DA NEXT 15 `params` E `searchParams` SONO PROMISE. Il codice
//   copiato da un esempio più vecchio compila e restituisce
//   `undefined` a runtime: è la rottura silenziosa più comune.
export default async function PaginaArticolo({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const articolo = await leggiArticolo(slug)
  if (!articolo) notFound() // rende `not-found.tsx`, con stato 404

  return <article>{articolo.titolo}</article>
}
```

```tsx
// Lo stesso file: `generateStaticParams` dice a `next build` quali
// pagine pre-generare. Senza, la rotta è dinamica e si renderizza
// a ogni richiesta.
export async function generateStaticParams() {
  const articoli = await leggiArticoliPubblicati({ limite: 200 })
  return articoli.map((a) => ({ slug: a.slug }))
}

// Le pagine NON elencate: `true` le genera al primo accesso e le
// mette in cache (è l'ISR); `false` restituisce 404.
export const dynamicParams = true

// E la rigenerazione periodica di quelle già generate
export const revalidate = 3600
```

⚠ `generateStaticParams` che restituisce diecimila slug significa diecimila pagine renderizzate a ogni build, e una build che passa da due minuti a quaranta. Si pre-generano le più visitate — le prime duecento coprono quasi sempre il 90% del traffico — e il resto arriva su richiesta.

---

## A5. Route Handler o Server Action

```
LA DOMANDA È: CHI CHIAMA?

  IL TUO STESSO FRONTEND, con un form o un pulsante
    ► SERVER ACTION. Niente endpoint da scrivere, niente `fetch`
      da parte del client, niente schema di richiesta da
      concordare. E il form funziona anche senza JavaScript.

  QUALCUNO CHE NON È IL TUO FRONTEND
    ► ROUTE HANDLER. Un'app mobile, un webhook di un fornitore, un
      cron esterno, un client che deve leggere lo stato HTTP.

⚠ UNA SERVER ACTION NON È PRIVATA: è un endpoint HTTP con un id
  generato, richiamabile da chiunque lo conosca (§B4). La scelta
  fra le due è di ergonomia, non di sicurezza.
```

```typescript
// app/api/webhook/pagamenti/route.ts — un webhook: il chiamante
// non è il tuo frontend, e vuole un codice di stato HTTP
import { after } from 'next/server'

export async function POST(richiesta: Request): Promise<Response> {
  const corpo = await richiesta.text() // il testo GREZZO: la firma è su quello

  // ⚠ La verifica della firma va fatta PRIMA di analizzare il JSON:
  //   analizzare e riserializzare cambia i byte e la firma non torna
  if (!firmaValida(corpo, richiesta.headers.get('x-firma'))) {
    return new Response('firma non valida', { status: 401 })
  }

  const evento = JSON.parse(corpo)
  // Si risponde SUBITO: il fornitore ha un timeout, e il lavoro
  // pesante va dopo la risposta (§D3)
  after(() => elaboraEvento(evento))
  return Response.json({ ricevuto: true })
}
```

```
⚠ TRE COSE DEI ROUTE HANDLER CHE SI SCOPRONO TARDI

  1. `GET` È STATICO PER DIFETTO se non usa niente di dinamico: il
     risultato si congela alla build. Se serve fresco, ci vuole
     `export const dynamic = 'force-dynamic'` o l'uso di `request`.
     Gli altri verbi non sono mai statici.
  2. NON C'È CORS AUTOMATICO: gli header vanno scritti a mano, e
     serve un handler `OPTIONS` per il preflight.
```

---

# Parte B — Comprensione Profonda

---

## B1. Cosa rende dinamica una rotta

```
IL PROBLEMA: una pagina che dovrebbe essere statica viene
renderizzata a ogni richiesta, e nessuno lo nota finché la fattura
o la latenza non lo dicono. La causa è quasi sempre una riga in
profondità, in un componente scritto da qualcun altro.

  COSA RENDE DINAMICA UNA ROTTA — l'elenco completo
   · `cookies()` o `headers()`, ovunque nell'albero
   · `searchParams` letto nella `page`
   · `connection()`, o `draftMode()`
   · una `fetch` con `cache: 'no-store'`
   · `export const dynamic = 'force-dynamic'`
   · una funzione di autenticazione che, dentro, legge un cookie
     ◄── è questa, nove volte su dieci
```

```powershell
# `next build` lo dice, e va letto a ogni rilascio:
#   ○ Static     pre-renderizzato alla build
#   ●  SSG       pre-renderizzato con generateStaticParams
#   ƒ Dynamic    renderizzato a ogni richiesta
#
# Una rotta che era ○ e diventa ƒ è una regressione, esattamente
# come un test che passa da verde a rosso.
npx next build
```

```tsx
// LA CURA: isolare la parte dinamica dentro un Suspense, così il
// resto della pagina resta statico. È il Partial Prerendering
// (tutorial_21 §B8).
export const experimental_ppr = true

export default function PaginaProdotto({ params }: { params: Promise<{ id: string }> }) {
  return (
    <>
      {/* STATICO: generato alla build, servito dalla CDN */}
      <DettaglioProdotto params={params} />

      {/* DINAMICO: legge i cookie, e sta dentro un confine */}
      <Suspense fallback={<ScheletroCarrello />}>
        <StatoCarrello />
      </Suspense>
    </>
  )
}
```

```
⚠ E IL CONTROLLO CHE MANCA QUASI SEMPRE: in sviluppo la Full Route
  Cache è SPENTA. Ogni pagina sembra dinamica, e i problemi di
  staticità non si vedono. Vanno provati con `next build && next
  start`, sempre — è lo stesso avvertimento del tutorial_21 §B3, e
  vale la pena ripeterlo perché costa incidenti.
```

---

## B2. Il middleware: cosa può e cosa non può

```
IL MIDDLEWARE GIRA PRIMA DEL ROUTING, sull'edge, per OGNI richiesta
che il suo `matcher` intercetta.

  ✅ CIÒ PER CUI È FATTO
     · reindirizzare in base al percorso o a un cookie
     · riscrivere l'URL (test A/B, internazionalizzazione)
     · aggiungere header di risposta — CSP, sicurezza (§B3)
     · rifiutare presto ciò che è chiaramente da rifiutare

  ❌ CIÒ CHE NON PUÒ FARE
     · leggere il database: gira sull'edge, dove spesso non è
       raggiungibile, e aggiungerebbe latenza a OGNI richiesta
     · usare API di Node: niente `fs`, niente `crypto` di Node
     · lavoro pesante: c'è un limite di CPU (tutorial_22 §B7)
```

```typescript
// middleware.ts
import { NextResponse, type NextRequest } from 'next/server'

export function middleware(richiesta: NextRequest): NextResponse {
  // Un controllo SUPERFICIALE: c'è un cookie di sessione? Basta a
  // evitare di renderizzare una pagina che finirebbe comunque in
  // un reindirizzamento.
  const sessione = richiesta.cookies.get('sessione')?.value
  if (!sessione && richiesta.nextUrl.pathname.startsWith('/cruscotto')) {
    const destinazione = new URL('/accedi', richiesta.url)
    destinazione.searchParams.set('da', richiesta.nextUrl.pathname)
    return NextResponse.redirect(destinazione)
  }
  return NextResponse.next()
}

// Il matcher esclude ciò che non ha bisogno di passare di qui:
// senza, il middleware gira anche su ogni immagine e ogni file
// statico, e si paga su ogni singola risorsa della pagina
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|svg)$).*)'],
}
```

```
⚠ IL MIDDLEWARE NON È UN CONTROLLO DI AUTORIZZAZIONE, e questo è
  l'errore architetturale più costoso di Next:

   1. NON COPRE LE SERVER ACTION: quelle sono endpoint a sé, e chi
      le chiama direttamente non passa dal matcher (§B4)
   2. NON PUÒ VERIFICARE LA SESSIONE per davvero: senza database,
      controlla al massimo che un cookie esista — non che sia
      valido, non revocato, non scaduto
   3. UN MATCHER SBAGLIATO lascia scoperta una rotta, e nessuno se
      ne accorge finché non è troppo tardi

  ➜ IL CONTROLLO VERO VA DOVE SI LEGGE IL DATO: nel layout
    protetto, nella pagina, e in OGNI Server Action. Il middleware
    è un'ottimizzazione dell'esperienza, non una difesa.
```

---

## B3. CSP con nonce, dal middleware

```
IL PROBLEMA: una Content-Security-Policy seria non può usare
`'unsafe-inline'` (tutorial_14 §B5), ma Next inietta script inline
per l'idratazione. La soluzione è un NONCE: un valore casuale per
richiesta, che autorizza solo gli script che lo portano.

➜ IL MIDDLEWARE È L'UNICO POSTO dove si può generare qualcosa di
  diverso a ogni richiesta E metterlo sia negli header di risposta
  sia in quelli di richiesta, dove i Server Component lo leggono.
```

```typescript
// middleware.ts
export function middleware(richiesta: NextRequest): NextResponse {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')

  // `strict-dynamic` fa sì che gli script caricati da uno script
  // autorizzato siano a loro volta autorizzati: è ciò che permette
  // al chunk loader di Next di funzionare senza aprire la policy
  const csp = [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
    `style-src 'self' 'nonce-${nonce}'`,
    `img-src 'self' blob: data:`,
    `object-src 'none'`,
    `base-uri 'self'`,
    `frame-ancestors 'none'`,
  ].join('; ')

  // Il nonce viaggia in un header di RICHIESTA, così i Server
  // Component possono leggerlo con `headers()`
  const intestazioni = new Headers(richiesta.headers)
  intestazioni.set('x-nonce', nonce)

  const risposta = NextResponse.next({ request: { headers: intestazioni } })
  risposta.headers.set('Content-Security-Policy', csp)
  return risposta
}
```

```tsx
// app/layout.tsx — il nonce si legge e si passa a ogni script
import { headers } from 'next/headers'
import Script from 'next/script'

export default async function LayoutRadice({ children }: { children: React.ReactNode }) {
  const nonce = (await headers()).get('x-nonce') ?? ''

  return (
    <html lang="it">
      <body>
        {children}
        <Script src="https://statistiche.esempio.it/s.js" nonce={nonce} />
      </body>
    </html>
  )
}
```

⚠ Leggere `headers()` nel root layout rende **dinamica ogni pagina dell'applicazione** (§B1). È un compromesso reale: o si accetta, o si applica la CSP con nonce solo alle rotte che sono già dinamiche, tenendo per quelle statiche una policy basata su hash. Con PPR il costo si riduce, ma va misurato, non dato per scontato.

---

## B4. Le Server Action sono endpoint pubblici

```
COSA SUCCEDE ALLA COMPILAZIONE: ogni Server Action riceve un id, e
quell'id diventa un endpoint HTTP. Il client lo chiama con una POST.

  ➜ CHIUNQUE CONOSCA L'ID PUÒ CHIAMARLA, senza passare dalla tua
    interfaccia, senza passare dal middleware, con i parametri che
    preferisce.

  ➜ IL FATTO CHE SI SCRIVA COME UNA FUNZIONE NON LA PROTEGGE. È la
    stessa cosa che scrivere `app.post('/azione', …)` e dimenticare
    l'autenticazione.
```

```typescript
'use server'

import { z } from 'zod'
import { revalidateTag } from 'next/cache'

// ⚠ `.strict()` NON È DECORATIVO: senza, `Object.fromEntries(dati)`
//   fa passare qualunque campo aggiunto al form — `ruolo=admin`
//   compreso. È il mass assignment, con un nome nuovo.
const SchemaAggiornamento = z
  .object({ nome: z.string().trim().min(1).max(120) })
  .strict()

export async function aggiornaProfilo(_stato: Stato, dati: FormData): Promise<Stato> {
  // ① AUTENTICARE — sempre, dentro l'azione
  const utente = await utenteCorrente()
  if (!utente) return { esito: 'errore', messaggio: 'Non autenticato' }

  // ② VALIDARE — i dati vengono dal client
  const analizzati = SchemaAggiornamento.safeParse(Object.fromEntries(dati))
  if (!analizzati.success) {
    return { esito: 'errore', campi: analizzati.error.flatten().fieldErrors }
  }

  // ③ AUTORIZZARE — l'identità dalla SESSIONE, mai dal form. Un
  //    `utenteId` nascosto nel form si modifica con gli strumenti
  //    di sviluppo, e si aggiorna il profilo di chiunque.
  await prisma.utente.update({ where: { id: utente.id }, data: analizzati.data })

  // ④ INVALIDARE — senza, l'interfaccia mostra i dati vecchi
  revalidateTag(`utente:${utente.id}`)
  return { esito: 'ok' }
}
```

```
LE DIFESE CHE NEXT AGGIUNGE DA SOLO: gli id delle azioni sono
cifrati e cambiano a ogni build · le azioni non referenziate
spariscono dal bundle · c'è un controllo dell'origin sulle POST.

  ❌ NESSUNA DI QUESTE sostituisce autenticazione, validazione e
     autorizzazione dentro l'azione

⚠ E UN DETTAGLIO DI DEPLOY: la chiave di cifratura degli id cambia
  a ogni build, quindi durante un rilascio progressivo le istanze
  vecchie e nuove non si capiscono, e le azioni falliscono per
  qualche minuto. Si fissa con
  `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`, uguale su tutte le istanze.
```

---

## B5. Immagini, font e metadata

```
QUESTE TRE COSE NON SONO COMODITÀ: sono le tre cause più comuni di
un LCP e un CLS cattivi (tutorial_17), e Next le risolve se le usi
come previsto.
```

```tsx
// next/image fa quattro cose insieme: ridimensiona e converte in
// AVIF/WebP, riserva lo spazio nel layout, carica pigro ciò che è
// fuori schermo, e serve la dimensione giusta per lo schermo.
import Image from 'next/image'

export function Copertina({ prodotto }: { prodotto: Prodotto }) {
  return (
    <Image
      src={prodotto.immagine}
      alt={prodotto.nome}
      width={800}
      height={600}
      // ⚠ `priority` SOLO sull'immagine LCP, ed è la ragione per cui
      //   esiste: toglie il caricamento pigro e aggiunge un preload.
      //   Metterlo su dieci immagini annulla il beneficio, perché
      //   dieci preload competono fra loro.
      priority
      // `sizes` dice al browser quanto sarà larga: senza, scarica
      // la variante più grande anche su un telefono
      sizes="(max-width: 768px) 100vw, 800px"
      placeholder="blur"
      blurDataURL={prodotto.anteprima}
    />
  )
}
```

```tsx
// next/font scarica il font alla BUILD e lo serve dal tuo dominio:
// niente richiesta a Google in runtime, niente terza parte nella
// catena critica, e le metriche di ripiego calcolate — che è ciò
// che elimina lo spostamento del testo. Si applica al root layout
// come `className={inter.variable}` su <html>.
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], display: 'swap', variable: '--carattere' })
```

```tsx
// I metadata: statici quando si conoscono, generati quando
// dipendono dai dati. `generateMetadata` e la pagina condividono
// la stessa fetch grazie alla memoizzazione di richiesta.
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const articolo = await leggiArticolo((await params).slug)
  if (!articolo) return { title: 'Non trovato' }

  return {
    title: articolo.titolo,
    description: articolo.sommario,
    openGraph: { images: [articolo.immagine] },
    // ⚠ Senza `alternates.canonical`, le varianti con parametri di
    //   tracciamento diventano pagine distinte per i motori
    alternates: { canonical: `/blog/${articolo.slug}` },
  }
}
```

⚠ `next/image` con un host remoto richiede che l'host sia elencato in `images.remotePatterns`. È una difesa, non un fastidio: senza, la tua funzione di ottimizzazione diventa un proxy aperto che chiunque può usare per ridimensionare immagini a tue spese.

---

## B6. Parallel e intercepting route

```
PARALLEL ROUTE — più pagine nello stesso layout, ognuna con il suo
caricamento e il suo errore. Le cartelle cominciano con @.

  app/cruscotto/
  ├── layout.tsx        riceve `children`, `squadra`, `statistiche`
  ├── page.tsx          → `children`
  ├── @squadra/
  │   ├── page.tsx
  │   ├── loading.tsx   ► questa sezione ha il SUO scheletro
  │   └── default.tsx   ► e il suo ripiego
  └── @statistiche/     ► idem

  ➜ SERVE QUANDO le sezioni caricano a velocità diverse e devono
    apparire indipendentemente. Con un `<Suspense>` si ottiene quasi
    lo stesso; la differenza è che uno slot è una ROTTA, quindi ha
    il proprio error boundary e può navigare per conto suo.
```

```tsx
// app/cruscotto/layout.tsx — gli slot arrivano come prop
export default function LayoutCruscotto({
  children,
  squadra,
  statistiche,
}: {
  children: React.ReactNode
  squadra: React.ReactNode
  statistiche: React.ReactNode
}) {
  return (
    <>
      {children}
      <div className="griglia">
        {squadra}
        {statistiche}
      </div>
    </>
  )
}
```

```
⚠ `default.tsx` È OBBLIGATORIO SU OGNI SLOT, e la sua assenza dà
  l'errore più oscuro dell'App Router. Dopo una navigazione soft
  Next non sa quale stato mostrare per uno slot che non partecipa
  alla nuova rotta: senza `default.tsx` risponde 404 per l'intera
  pagina, e il messaggio non nomina lo slot.
```

```
INTERCEPTING ROUTE — la stessa rotta mostrata in due contesti: un
modale se ci arrivi da dentro, una pagina intera se apri il link.

  app/
  ├── galleria/page.tsx
  ├── @modale/(.)foto/[id]/page.tsx   ► il modale, navigando dal feed
  └── foto/[id]/page.tsx              ► la pagina intera, per l'URL
                                        diretto e il ricarica

  (.) stesso livello · (..) uno sopra · (...) dalla radice

  ➜ È IL PATTERN "modale con URL condivisibile": l'indirizzo cambia,
    il link funziona per chi lo riceve, e il tasto indietro chiude
    il modale. Costa due file per la stessa pagina.
```

---

## B7. I confini d'errore, e quale copre cosa

```
LA GERARCHIA, dall'interno verso l'esterno

  error.tsx di un segmento    ► cattura gli errori di quel segmento
                                e dei suoi figli. NON cattura quelli
                                del PROPRIO layout: sta dentro di
                                esso.
  error.tsx del segmento padre► cattura quelli del layout figlio
  global-error.tsx            ► l'unico che copre il ROOT layout, e
                                deve quindi rendere <html> e <body>
                                da sé. Si vede solo in produzione.

⚠ È LA COSA CHE CONFONDE DI PIÙ: se il tuo root layout va in
  errore, `app/error.tsx` non lo cattura. Serve `global-error.tsx`,
  ed è la ragione per cui esiste.
```

```tsx
// app/cruscotto/error.tsx
'use client' // ← obbligatorio: un confine d'errore ha stato

export default function ErroreCruscotto({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  // `digest` è l'unico aggancio ai log: in produzione il messaggio
  // vero è nascosto al client, e nei log del server c'è lo stesso
  useEffect(() => segnalaErrore(error, { digest: error.digest }), [error])

  return (
    <div role="alert">
      <h2>Il cruscotto non è disponibile</h2>
      {error.digest && <p>Riferimento: {error.digest}</p>}
      {/* `reset` ritenta il rendering del segmento senza ricaricare */}
      <button onClick={reset}>Riprova</button>
    </div>
  )
}
```

```
⚠ IN PRODUZIONE IL MESSAGGIO DELL'ERRORE NON ARRIVA AL CLIENT: Next
  lo sostituisce con un testo generico e un `digest`. È corretto —
  i messaggi contengono nomi di tabelle e percorsi — e significa che
  l'unico modo di indagare è cercare quel digest nei log. Un confine
  d'errore che non lo mostra all'utente rende impossibile
  l'assistenza.

  E `notFound()` NON È UN ERRORE: solleva un'eccezione speciale che
  Next intercetta per rendere `not-found.tsx` con stato 404. Un
  `try/catch` troppo largo intorno a una funzione che la chiama la
  cattura e trasforma un 404 in un 500 — vale anche per `redirect()`.
```

---

## B8. L'idratazione che non corrisponde

> **Analogia:** due persone che ricopiano lo stesso disegno, una a Roma e una a Milano, e poi li sovrappongono. Se uno dei due ha guardato l'orologio mentre disegnava, i due fogli non combaciano.

```
COSA SUCCEDE: il server produce l'HTML, il client rirenderizza lo
stesso albero per attaccarci gli eventi. Se i due risultati
differiscono, React scarta l'HTML del server e ridisegna tutto —
lampeggio visibile, e un avviso in console.

  LE CAUSE, in ordine di frequenza
   1. `new Date()`, `Date.now()`, `Math.random()` nel rendering
   2. `window`, `localStorage`, `navigator` fuori da un effetto
   3. HTML non valido — un `<div>` dentro un `<p>`: il browser lo
      corregge, e l'albero non è più quello che React si aspetta
   4. un'estensione del browser che modifica il DOM: falso positivo
      frequente, e non è colpa tua
   5. contenuto che dipende dal fuso orario o dalla lingua di sistema
```

```tsx
// ❌ SBAGLIATO — il server ha un'ora, il client ne ha un'altra
export function Orologio() {
  return <span>{new Date().toLocaleTimeString('it-IT')}</span>
}

// ✅ CORRETTO — il primo rendering è uguale ovunque, e il valore
//    che dipende dal client arriva DOPO l'idratazione
'use client'
export function OrologioCorretto() {
  const [ora, impostaOra] = useState<string | null>(null)
  useEffect(() => {
    const t = setInterval(() => impostaOra(new Date().toLocaleTimeString('it-IT')), 1000)
    return () => clearInterval(t)
  }, [])
  return <span>{ora ?? '--:--:--'}</span>
}
```

```tsx
// ✅ La formattazione di una data si fa sul SERVER, con un fuso
//    esplicito: così il valore è deciso una volta sola
export function DataArticolo({ quando }: { quando: Date }) {
  const formattata = new Intl.DateTimeFormat('it-IT', {
    dateStyle: 'long',
    timeZone: 'Europe/Rome', // senza, server e client usano il proprio
  }).format(quando)
  return <time dateTime={quando.toISOString()}>{formattata}</time>
}
```

⚠ `suppressHydrationWarning` **non risolve niente**: silenzia l'avviso e lascia la differenza. Ha un solo uso legittimo — un attributo che un'estensione o uno script di tema modifica prima dell'idratazione, tipicamente su `<html>` — e su qualunque altro elemento è un difetto nascosto sotto il tappeto.

---

## B9. Il deploy fuori da Vercel

```
NEXT.JS GIRA OVUNQUE, ma alcune funzionalità sono INTEGRAZIONI
della piattaforma, non parti del framework. Fuori da Vercel vanno
ricostruite, e conviene saperlo prima di scegliere.

  ottimizzazione immagini ► usa il TUO processo Node e `sharp`,
      che è CPU-intensivo: serve una CDN davanti, o un loader verso
      un servizio esterno
  ISR e revalidateTag ► la cache è su DISCO, e con più istanze
      ognuna ha la sua: serve un `cacheHandler` condiviso (Redis)
  middleware ► gira nel processo Node, non su 300 PoP: la latenza
      non è più trascurabile, e il matcher va tenuto stretto
  logging e metriche ► da configurare (§D3)
```

```dockerfile
# Dockerfile — `output: 'standalone'` in next.config produce una
# cartella che contiene SOLO le dipendenze davvero usate: l'immagine
# passa da ~1,2 GB a ~150 MB.
FROM node:22-alpine AS dipendenze
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

FROM node:22-alpine AS costruzione
WORKDIR /app
COPY --from=dipendenze /app/node_modules ./node_modules
COPY . .
# ⚠ LE VARIABILI `NEXT_PUBLIC_*` SONO INCORPORATE QUI, alla build:
#   passarle a runtime non ha effetto, perché sono già nel bundle
RUN corepack enable && pnpm build

FROM node:22-alpine AS esecuzione
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S nodejs && adduser -S nextjs -G nodejs

COPY --from=costruzione /app/public ./public
COPY --from=costruzione --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=costruzione --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

```
⚠ TRE COSE CHE ROMPONO IL DEPLOY, e sempre le stesse

  1. `.next/static` NON COPIATO: la build passa, il sito si carica
     senza CSS e senza JavaScript. `standalone` non lo include, va
     copiato a parte — è la riga che si dimentica.
  2. `NEXT_PUBLIC_*` PASSATE A RUNTIME: sono sostituite nel codice
     alla build. Cambiare l'URL dell'API senza ricostruire non ha
     effetto, e il debug è lungo.
  3. NESSUN `cacheHandler` CON PIÙ REPLICHE: `revalidateTag` tocca
     una replica sola, e le altre continuano a servire il vecchio.
     L'incidente si presenta come "a volte vedo i dati aggiornati".
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — La rotta che doveva essere statica

**Obiettivo:** il blog costa dieci volte il previsto e il TTFB è di 800 ms. `next build` marca `/blog/[slug]` come `ƒ Dynamic`. Trovare le tre cause.

```tsx
// app/blog/[slug]/page.tsx
import { intestazioneConUtente } from '@/componenti/intestazione'

export default async function PaginaArticolo({ params, searchParams }) {
  const { slug } = await params
  const { evidenzia } = await searchParams
  const articolo = await fetch(`${API}/articoli/${slug}`, { cache: 'no-store' })
    .then((r) => r.json())

  return (
    <>
      <IntestazioneConUtente />
      <article>{evidenzia ? evidenziaTesto(articolo.corpo, evidenzia) : articolo.corpo}</article>
    </>
  )
}
```

```
LA DIAGNOSI — tre cause, e ognuna da sola basta
 1. `searchParams` LETTO NELLA PAGE: rende dinamica la rotta anche
    se il valore non serve quasi mai (§B1)
 2. `cache: 'no-store'` su un articolo che cambia una volta al mese
 3. `<IntestazioneConUtente />` LEGGE UN COOKIE dentro di sé: è la
    causa invisibile, perché sta in un altro file e nessuno la
    collega alla staticità della pagina
 ⚠ E manca `generateStaticParams`: nemmeno le pagine più viste
   sono pre-generate.
```

```tsx
// LA SOLUZIONE — la pagina torna statica, e ciò che è dinamico
// vive dentro un confine
export const revalidate = 3600
export const experimental_ppr = true

export async function generateStaticParams() {
  // Le duecento più viste: coprono il grosso del traffico senza
  // far esplodere il tempo di build (§A4)
  const articoli = await leggiArticoliPiuVisti(200)
  return articoli.map((a) => ({ slug: a.slug }))
}

export default async function PaginaArticolo({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  // 2. Con `revalidate` invece di `no-store`: l'articolo è statico
  //    e si rigenera ogni ora
  const articolo = await fetch(`${API}/articoli/${slug}`, {
    next: { revalidate: 3600, tags: [`articolo:${slug}`] },
  }).then((r) => r.json())
  if (!articolo) notFound()

  return (
    <>
      {/* 3. Il pezzo che legge i cookie sta dentro un Suspense: il
             resto della pagina resta prerenderizzato */}
      <Suspense fallback={<ScheletroIntestazione />}>
        <IntestazioneConUtente />
      </Suspense>
      <article dangerouslySetInnerHTML={{ __html: articolo.corpoHtml }} />
    </>
  )
}
```

E il punto 1: l'evidenziazione si sposta in un Client Component che legge `useSearchParams()` e agisce in un effetto. Un hook non rende dinamica la pagina — è `searchParams` letto nella `page` a farlo.

```
# VERIFICA — si legge l'output di `next build`
# prima: ƒ /blog/[slug]                    Dynamic
# dopo:  ● /blog/[slug]                    SSG  (200 pagine)
#        ○ le restanti generate su richiesta e messe in cache
# E il TTFB misurato con `next build && next start`, non in
# sviluppo, dove la Full Route Cache è spenta (§B1).
```

---

### Esercizio 2 — Il middleware che non protegge

**Obiettivo:** un test di sicurezza ha letto i dati di altri utenti senza essere autenticato. La protezione c'è. Trovare i tre buchi.

```typescript
// middleware.ts — "l'applicazione è protetta"
export function middleware(richiesta: NextRequest) {
  if (!richiesta.cookies.get('sessione')) {
    return NextResponse.redirect(new URL('/accedi', richiesta.url))
  }
  return NextResponse.next()
}

export const config = { matcher: ['/cruscotto/:path*'] }
```

```typescript
// app/azioni/utenti.ts
'use server'

export async function leggiUtente(id: string) {
  return prisma.utente.findUnique({ where: { id } })
}
```

```
LA DIAGNOSI — tre buchi, e il terzo è quello che è stato usato
 1. IL MIDDLEWARE CONTROLLA CHE IL COOKIE ESISTA, non che sia
    valido: `sessione=qualsiasi-cosa` passa, perché sull'edge non
    c'è il database per verificarlo (§B2)
 2. IL MATCHER COPRE SOLO `/cruscotto/*`: ogni altra pagina
    riservata non passa di lì
 3. LA SERVER ACTION NON PASSA DAL MIDDLEWARE, non autentica, e
    accetta un `id` qualunque: chiamandola direttamente si legge
    l'anagrafica di chiunque (§B4). È l'unica dei tre che permette
    di leggere dati, ed è quella che il test ha usato.
```

```typescript
// LA SOLUZIONE — il controllo dove si legge il dato
// lib/autenticazione.ts
import { cache } from 'react'

// `cache` evita che dieci componenti verifichino la stessa sessione
// dieci volte nella stessa richiesta
export const utenteCorrente = cache(async () => {
  const token = (await cookies()).get('sessione')?.value
  if (!token) return null
  try {
    return await verificaSessione(token) // qui il database C'È
  } catch {
    return null
  }
})

export async function richiediUtente() {
  const utente = await utenteCorrente()
  if (!utente) redirect('/accedi')
  return utente
}
```

```typescript
// 3. Ogni Server Action autentica e autorizza, senza eccezioni
'use server'

export async function leggiUtente(id: string) {
  const richiedente = await richiediUtente()

  // L'autorizzazione è nella QUERY, non in un `if` che qualcuno
  // deve ricordarsi di scrivere
  return prisma.utente.findFirst({
    where: {
      id,
      OR: [{ id: richiedente.id }, { organizzazioneId: richiedente.organizzazioneId }],
    },
    select: { id: true, nome: true, email: true }, // mai l'oggetto intero
  })
}
```

Il middleware resta, con il ruolo giusto — evitare di renderizzare pagine che finirebbero comunque in un reindirizzamento — e il suo `matcher` si estende a tutto ciò che è riservato, non al solo cruscotto.

```
# VERIFICA — le tre prove
# 1. cookie `sessione=falso` → il middleware lascia passare, ma il
#    layout riservato reindirizza: il comportamento è corretto
# 2. `/impostazioni` senza cookie → reindirizza
# 3. la Server Action chiamata con curl e l'id di un altro utente
#    → 'Non autenticato', e con una sessione valida di un'altra
#    organizzazione → nessuna riga
```

---

### Esercizio 3 — L'idratazione che non corrisponde

**Obiettivo:** la pagina lampeggia al caricamento e la console mostra un avviso di idratazione. In sviluppo si vede a intermittenza. Trovare le tre cause.

```tsx
'use client'

export function ElencoNotifiche({ notifiche }: { notifiche: Notifica[] }) {
  const compatta = localStorage.getItem('vista') === 'compatta'

  return (
    <p className={compatta ? 'compatta' : ''}>
      {notifiche.map((n) => (
        <div key={n.id}>
          {n.testo} — {new Date(n.quando).toLocaleString()}
          {Date.now() - n.quando < 60_000 && <span>nuova</span>}
        </div>
      ))}
    </p>
  )
}
```

```
LA DIAGNOSI — tre cause
 1. `localStorage` LETTO DURANTE IL RENDERING: sul server non
    esiste, quindi il primo rendering differisce — e su Next è
    anche un errore di riferimento nel rendering lato server
 2. `toLocaleString()` E `Date.now()` senza fuso né istante
    fissati: server e client producono stringhe diverse, e
    l'etichetta "nuova" può comparire su uno e non sull'altro
 3. UN `<div>` DENTRO UN `<p>`: il browser chiude il `<p>` da
    solo, e l'albero reale non è quello che React si aspetta.
    L'idratazione fallisce anche senza le altre due cause, ed è il
    caso più difficile da vedere perché il codice sembra corretto.
```

```tsx
// LA SOLUZIONE
'use client'

export function ElencoNotifiche({ notifiche }: { notifiche: NotificaResa[] }) {
  // 1. Il valore dal browser parte dal predefinito del server e si
  //    aggiorna DOPO l'idratazione: il primo rendering combacia
  const [compatta, impostaCompatta] = useState(false)
  useEffect(() => {
    impostaCompatta(localStorage.getItem('vista') === 'compatta')
  }, [])

  return (
    // 3. `<ul>`/`<li>`: struttura valida, e anche più corretta dal
    //    punto di vista semantico
    <ul className={compatta ? 'compatta' : ''}>
      {notifiche.map((n) => (
        <li key={n.id}>
          {n.testo} — <time dateTime={n.iso}>{n.formattata}</time>
          {n.recente && <span>nuova</span>}
        </li>
      ))}
    </ul>
  )
}
```

```tsx
// 2. La formattazione e il confronto con "adesso" avvengono UNA
//    VOLTA, sul server, con un fuso esplicito. Il client riceve
//    stringhe e booleani, non date da interpretare.
const formato = new Intl.DateTimeFormat('it-IT', {
  dateStyle: 'short',
  timeStyle: 'short',
  timeZone: 'Europe/Rome',
})

export async function SezioneNotifiche() {
  const grezze = await leggiNotifiche()
  const adesso = Date.now()

  return (
    <ElencoNotifiche
      notifiche={grezze.map((n) => ({
        id: n.id,
        testo: n.testo,
        iso: new Date(n.quando).toISOString(),
        formattata: formato.format(n.quando),
        recente: adesso - n.quando < 60_000,
      }))}
    />
  )
}
```

```
# VERIFICA — l'avviso di idratazione va cercato dove si vede
# 1. `next build && next start`: nessun avviso in console
# 2. con una lingua e un fuso diversi nel browser: nessun avviso
# 3. l'HTML servito dal server, con `curl`, contiene già le date
#    formattate — è la prova che il punto 2 è risolto davvero
# ⚠ Se resta un avviso solo su alcuni browser, si prova in finestra
#   anonima senza estensioni: le estensioni modificano il DOM e
#   generano falsi positivi.
```

---

## C2. Mini-progetto: il portale in App Router

**Obiettivo:** il portale aziendale del corso, con la struttura e le difese che questo tutorial ha reso obbligatorie.

```
LA STRUTTURA

  app/
  ├── layout.tsx              root: <html>, font, metadata template
  ├── global-error.tsx        l'unico che copre il root layout (§B7)
  ├── (pubblica)/
  │   ├── page.tsx            statica, con revalidate
  │   └── blog/[slug]/        SSG sui 200 più visti + ISR (§A4)
  ├── (riservata)/
  │   ├── layout.tsx          `richiediUtente()` — il controllo VERO
  │   ├── error.tsx           il confine del segmento
  │   ├── cruscotto/
  │   │   ├── page.tsx        PPR: shell statica, dati in Suspense
  │   │   └── @attivita/      slot con default.tsx (§B6)
  │   └── impostazioni/page.tsx
  ├── azioni/                 le Server Action, ognuna con le
  │                           quattro fasi del §B4
  └── api/
      ├── stato/route.ts      health check per il container
      └── webhook/…/route.ts  i chiamanti che non sono il frontend

  middleware.ts   nonce CSP + reindirizzamento superficiale (§B2, §B3)
  next.config.ts  output: 'standalone', remotePatterns, cacheHandler
```

```typescript
// next.config.ts
import type { NextConfig } from 'next'

const configurazione: NextConfig = {
  // Per il Docker del §B9: l'immagine passa da ~1,2 GB a ~150 MB
  output: 'standalone',

  images: {
    // Senza questa lista l'ottimizzatore sarebbe un proxy aperto
    remotePatterns: [{ protocol: 'https', hostname: 'contenuti.esempio.it' }],
  },

  // Con più repliche la cache su disco non basta: `revalidateTag`
  // toccherebbe una sola istanza (§B9)
  cacheHandler: require.resolve('./cache-redis.js'),
  cacheMaxMemorySize: 0,

  experimental: { ppr: 'incremental' },
}

export default configurazione
```

```typescript
// app/api/stato/route.ts — il health check che il container usa.
// `force-dynamic` perché una risposta cachata direbbe "sano" anche
// a database spento.
export const dynamic = 'force-dynamic'

export async function GET(): Promise<Response> {
  try {
    await prisma.$queryRaw`SELECT 1`
    return Response.json({ stato: 'ok' })
  } catch {
    return Response.json({ stato: 'degradato' }, { status: 503 })
  }
}
```

```
# ESTENSIONI, in ordine di utilità
# 1. L'internazionalizzazione con `app/[locale]/`, che cambia il
#    modo in cui si scrivono tutti i link: va decisa presto
# 2. Il `cacheHandler` Redis provato davvero con due repliche e un
#    `revalidateTag` — è la verifica che il §B9 punto 3 non morda
# 3. `instrumentation.ts` e le tracce del §D3, prima del primo
#    incidente e non dopo
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Testare un'applicazione App Router

```
IL PROBLEMA: un Server Component `async` non è renderizzabile da
Testing Library, che non sa gestire una Promise come componente. La
strategia che regge è differenziata per livello:
 1. LA LOGICA si estrae in funzioni normali e si testa come tale
 2. I CLIENT COMPONENT con Testing Library, come sempre
 3. LE SERVER ACTION come funzioni asincrone, con la sessione
    simulata — ed è lì che si testa l'autorizzazione, con DUE utenti
 4. IL RESTO end-to-end con Playwright: è l'unico livello che vede
    routing, streaming, idratazione e middleware
```

```typescript
// Le Server Action si testano come quello che sono: funzioni
import { describe, it, expect, vi } from 'vitest'
import { aggiornaProfilo } from '@/app/azioni/profilo'

vi.mock('@/lib/autenticazione')

describe('aggiornaProfilo', () => {
  it('rifiuta chi non è autenticato', async () => {
    vi.mocked(utenteCorrente).mockResolvedValue(null)
    const esito = await aggiornaProfilo({}, new FormData())
    expect(esito).toMatchObject({ esito: 'errore' })
  })

  it('ignora i campi non previsti dallo schema', async () => {
    vi.mocked(utenteCorrente).mockResolvedValue({ id: 'u1', ruolo: 'utente' })
    const dati = new FormData()
    dati.set('nome', 'Ada')
    dati.set('ruolo', 'admin') // il tentativo di mass assignment
    await aggiornaProfilo({}, dati)

    // `.strict()` fa fallire la validazione: nessun aggiornamento
    expect(prisma.utente.update).not.toHaveBeenCalled()
  })
})
```

```typescript
// Playwright per ciò che solo il browser vede
import { test, expect } from '@playwright/test'

test('il cruscotto reindirizza chi non è autenticato', async ({ page }) => {
  await page.goto('/cruscotto')
  await expect(page).toHaveURL(/\/accedi/)
})

test('il form funziona anche senza JavaScript', async ({ browser }) => {
  // ⚠ È il test che dimostra il vantaggio delle Server Action su
  //   `<form action>`, e nessun altro livello può farlo
  const contesto = await browser.newContext({ javaScriptEnabled: false })
  const pagina = await contesto.newPage()
  await pagina.goto('/impostazioni')
  await pagina.fill('[name=nome]', 'Ada Lovelace')
  await pagina.click('button[type=submit]')
  await expect(pagina.getByText('Salvato')).toBeVisible()
})
```

⚠ Il test che manca quasi sempre è quello sull'**output di `next build`**: una rotta che passa da statica a dinamica è una regressione di prestazioni e di costo, e in CI si può verificare confrontando il manifesto delle rotte con quello atteso. È l'unico modo di accorgersene prima della fattura.

---

## D2. Migrare dal Pages Router

```
LA MIGRAZIONE È INCREMENTALE: `pages/` e `app/` convivono, e `app/`
vince sulle rotte in conflitto. L'ordine che funziona:

  1. abilitare `app/` senza spostare niente, e verificare che la
     build passi
  2. migrare una rotta NUOVA o poco usata, per imparare sul campo
  3. poi quelle che guadagnano di più dal minor JavaScript
  4. per ultimo `_app` e `_document`, che diventano `layout.tsx`

LE CORRISPONDENZE
  getServerSideProps  → await dentro il componente
  getStaticProps      → await + `export const revalidate`
  getStaticPaths      → generateStaticParams()
  pages/api/*         → app/api/*/route.ts, oppure Server Action
  next/router         → next/navigation
  next/head           → export const metadata, o generateMetadata
```

```
⚠ LE QUATTRO TRAPPOLE

  1. `useRouter` DI `next/navigation` HA UN'API DIVERSA: niente
     `query`, niente `pathname`, niente `events`. Importarlo dal
     posto sbagliato dà un errore a runtime, non a compilazione.
  2. I PROVIDER DI CONTESTO devono stare in un Client Component: un
     provider nel root layout richiede un file separato con
     `'use client'` che avvolge `children`.
  3. LE LIBRERIE CHE NON DICHIARANO `'use client'` vanno avvolte in
     un proprio file client, o non funzionano.
  4. `params` E `searchParams` SONO PROMISE (§A4): rompono
     silenziosamente il codice copiato da esempi più vecchi.
```

---

## D3. Osservare: instrumentation e after

```typescript
// instrumentation.ts — gira UNA VOLTA all'avvio del processo, prima
// di servire qualunque richiesta. È il posto per il tracciamento e
// per i controlli di configurazione.
export async function register(): Promise<void> {
  // Il controllo che vale di più: le variabili mancanti si scoprono
  // all'avvio, non alla prima richiesta che le usa
  verificaAmbiente()

  if (process.env['NEXT_RUNTIME'] === 'nodejs') {
    await import('./strumentazione-node') // OpenTelemetry, solo su Node
  }
}

// E il gancio per gli errori del server, che altrimenti si vedono
// solo nei log grezzi
export function onRequestError(
  errore: unknown,
  richiesta: { path: string },
  contesto: { routerKind: string; renderSource: string },
): void {
  segnalaErrore(errore, { percorso: richiesta.path, ...contesto })
}
```

```typescript
// `after` esegue DOPO che la risposta è stata inviata: il lavoro
// che non deve far aspettare l'utente esce dal percorso critico
import { after } from 'next/server'

export async function POST(richiesta: Request): Promise<Response> {
  const risultato = await elabora(await richiesta.json())

  after(async () => {
    // Registrazione, statistiche, invalidazioni, notifiche
    await registraEvento({ tipo: 'elaborato', id: risultato.id })
  })

  return Response.json(risultato)
}
```

```
⚠ `after` NON È UNA CODA. Se il processo muore fra la risposta e
  l'esecuzione, quel lavoro è perso e nessuno lo saprà. Va bene per
  statistiche e log; per un'email di conferma o un addebito serve
  una coda vera, con conferma e ritentativi.

E LE METRICHE CHE CONTANO in un'applicazione Next:
  · quante rotte sono statiche contro dinamiche, per rilascio
  · il TTFB separato fra statiche e dinamiche: mediarle insieme
    nasconde entrambi i problemi
  · gli errori per `digest`, l'unico aggancio al client (§B7)
  · il tasso di successo delle Server Action, per azione, e la
    dimensione del bundle per rotta che `next build` dà già
```

---

## D4. Turbopack e i tempi di build

```
TURBOPACK sostituisce Webpack. In sviluppo è stabile e la
differenza si sente: l'avvio a freddo e il ricaricamento a caldo
passano da secondi a decine di millisecondi su progetti grandi.

  `next dev --turbopack`     ► stabile
  `next build --turbopack`   ► verificare lo stato sulla versione
                               che si usa prima di adottarlo in CI

⚠ COSA NON FUNZIONA, e va controllato prima di migrare
   · i loader Webpack personalizzati e i plugin non sono supportati:
     `next.config` con una sezione `webpack` va ripensato
   · alcune configurazioni di CSS-in-JS che dipendono dal bundler
   · le opzioni si spostano da `webpack` a `turbopack`, con una
     sintassi diversa per le regole

➜ LA STRATEGIA CHE COSTA MENO: Turbopack in sviluppo subito, dove
  il guadagno è immediato e il rischio è nullo — se qualcosa non va
  si toglie il flag. In CI si passa quando la build produce lo
  stesso risultato, confrontando l'output di `next build` fra i due.
```

---

## D5. Quando NON serve Next.js

```
NEXT AGGIUNGE: un framework che decide molte cose al posto tuo, un
sistema di cache a quattro livelli da capire, un confine
server/client da sorvegliare, un accoppiamento reale con le scelte
del framework, e una piattaforma che dà il meglio su Vercel.

NON SERVE QUANDO
  ❌ è un'applicazione interna dietro autenticazione, senza SEO e
     interamente interattiva: una SPA con Vite è più semplice e non
     ha nessuno dei problemi di questo tutorial
  ❌ è un sito di contenuti statici: Astro produce meno JavaScript
     e si capisce in un pomeriggio
  ❌ serve comunque un backend separato per altri client: Next non
     sostituisce l'API, e mantenerne due costa
  ❌ nessuno nel team sa spiegare il confine server/client: il
     costo si paga in bug sottili — dati nel payload, waterfall
     invisibili, cache che non si invalida

SERVE DAVVERO QUANDO
  ✅ il contenuto è pubblico, il SEO conta, e le pagine sono molte
  ✅ serve una miscela di statico e dinamico nella stessa
     applicazione — è ciò che Next fa meglio di chiunque
  ✅ il primo caricamento è la metrica che decide
  ✅ la squadra lavora full-stack sullo stesso repository
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
NEXT.JS 15 — Mappa dei concetti

IL ROUTING
├── il filesystem è il router: una cartella diventa rotta solo con
│     `page.tsx` o `route.ts`
├── i route group `(nome)` non entrano nell'URL: servono a dare
│     layout diversi a sezioni diverse
├── `layout` persiste fra le navigazioni, `template` si rimonta
├── un layout NON riceve `searchParams`
└── `params` e `searchParams` sono PROMISE da Next 15

STATICO O DINAMICO
├── lo decidono `cookies()`, `headers()`, `searchParams`, una fetch
│     senza cache, o `force-dynamic` — spesso in profondità
├── `next build` lo dice per ogni rotta, e va letto a ogni rilascio
├── la cura è isolare il dinamico in un Suspense (PPR)
└── in sviluppo la Full Route Cache è spenta: si prova con
      `build && start`

IL MIDDLEWARE
├── reindirizzamenti, riscritture, header, nonce CSP
├── NON è autorizzazione: non copre le Server Action, non può
│     verificare la sessione, e un matcher sbagliato scopre rotte
├── il matcher va stretto, o gira anche sulle immagini
└── il nonce CSP nel root layout rende dinamica ogni pagina

LE SERVER ACTION
├── sono ENDPOINT HTTP PUBBLICI: autenticare, validare, autorizzare
├── l'identità dalla SESSIONE, mai dal form
├── schema `.strict()` contro il mass assignment
└── `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` per i rilasci progressivi

LE OTTIMIZZAZIONI INTEGRATE
├── `next/image`: `priority` solo sull'LCP, `sizes` sempre, e
│     `remotePatterns` o è un proxy aperto
├── `next/font`: scaricato alla build, servito dal tuo dominio
└── `generateMetadata` condivide la fetch con la pagina

GLI ERRORI E L'IDRATAZIONE
├── `error.tsx` non cattura il PROPRIO layout; il root layout lo
│     copre solo `global-error.tsx`
├── in produzione al client arriva solo il `digest`: mostrarlo è
│     ciò che rende possibile l'assistenza
├── `notFound()` e `redirect()` sono eccezioni: un try/catch largo
│     le trasforma in 500
├── date, casualità, `localStorage` e HTML non valido rompono
│     l'idratazione — l'ultimo è il più difficile da vedere
└── `suppressHydrationWarning` nasconde, non risolve

IL DEPLOY
├── `output: 'standalone'` e `.next/static` copiato a parte
├── `NEXT_PUBLIC_*` sono incorporate alla BUILD
├── con più repliche serve un `cacheHandler` condiviso
└── fuori da Vercel: immagini, ISR e middleware vanno ricostruiti
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Sai quando una cartella diventa una rotta e quando no
- [ ] Conosci i file convenzionali e sai quale gira dove
- [ ] Distingui `layout` da `template`, sai perché un layout non
      riceve `searchParams`, e usi i route group per dare layout
      diversi a sezioni diverse
- [ ] Sai che `params` e `searchParams` sono Promise
- [ ] Usi `generateStaticParams` senza far esplodere il tempo di build
- [ ] Scegli fra Route Handler e Server Action con una motivazione

**Parte B — Comprensione**

- [ ] Sai elencare cosa rende dinamica una rotta, leggerlo da
      `next build`, e isolare il dinamico in un Suspense
- [ ] Sai perché i problemi di cache si vedono solo con `build && start`
- [ ] Sai cosa il middleware può fare, cosa non può, e perché non
      è un controllo di autorizzazione
- [ ] Configuri una CSP con nonce, e ne conosci il costo
- [ ] Tratti ogni Server Action come un endpoint pubblico
- [ ] Usi `priority`, `sizes` e `remotePatterns` correttamente, e
      sai perché serve `default.tsx` su ogni slot parallelo
- [ ] Sai quale confine d'errore copre cosa, e cosa arriva al client
- [ ] Sai riconoscere le cinque cause di un hydration mismatch
- [ ] Sai cosa va ricostruito in self-hosting e perché

**Parte C — Pratica**

- [ ] Hai riportato a statica una rotta che era diventata dinamica
- [ ] Hai spostato l'autorizzazione dove si legge il dato
- [ ] Hai eliminato tre cause di hydration mismatch
- [ ] Hai costruito un portale con struttura, difese e deploy

**Parte D — Esperto**

- [ ] Testi ai quattro livelli, con Playwright per ciò che solo lui vede
- [ ] Verifichi in CI che le rotte statiche restino statiche
- [ ] Conosci le corrispondenze e le trappole della migrazione
- [ ] Usi `instrumentation.ts` e `after`, e sai cosa `after` non garantisce
- [ ] Sai cosa Turbopack non supporta ancora
- [ ] Sai dire quando Next.js non serve

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Middleware come unico controllo | Non copre le Server Action, e non verifica la sessione | Il controllo dove si legge il dato |
| Server Action senza autenticazione | È un endpoint HTTP pubblico | Autenticare, validare, autorizzare, sempre |
| `Object.fromEntries(dati)` nel database | Mass assignment: `ruolo=admin` | Schema Zod `.strict()` |
| `cookies()` in un componente in profondità | Rende dinamica tutta la pagina senza volerlo | Isolare in un Suspense; leggere `next build` |
| `generateStaticParams` con diecimila voci | Build da quaranta minuti | Le più visitate, e il resto su richiesta |
| `remotePatterns` non configurato | L'ottimizzatore diventa un proxy aperto | La lista degli host, esplicita |
| Slot parallelo senza `default.tsx` | 404 sull'intera pagina, con un messaggio oscuro | Un `default.tsx` per ogni slot |
| Confine d'errore che non mostra il `digest` | Nessun modo di collegare la segnalazione ai log | Mostrarlo, e cercarlo nei log |
| `new Date()` nel rendering | Hydration mismatch, e lampeggio | Formattare sul server con fuso esplicito |
| `suppressHydrationWarning` per zittire | Nasconde una differenza che resta | Correggere la causa |
| `.next/static` non copiato nel Docker | Il sito si carica senza CSS né JavaScript | Copiarlo a parte dopo `standalone` |
| Più repliche senza `cacheHandler` | `revalidateTag` tocca una sola istanza | Un handler condiviso |

---

## Troubleshooting rapido

**`params` o `searchParams` sono `undefined`**
- Causa: da Next 15 sono Promise
- Fix: `const { id } = await params`

**Una rotta che doveva essere statica è `ƒ Dynamic`**
- Causa: `cookies()`, `headers()` o `searchParams` in profondità
- Fix: cercarli nell'albero; isolare la parte dinamica in un Suspense

**Hydration mismatch**
- Causa: date, casualità, `localStorage`, o HTML non valido
- Fix: rendering identico al primo giro; l'HTML si valida separatamente

**"useState can only be used in Client Components"**
- Causa: un hook in un Server Component, o una libreria senza `'use client'`
- Fix: `'use client'` sul file giusto, o avvolgere la libreria

**I dati non si aggiornano dopo una Server Action**
- Causa: manca `revalidatePath`/`revalidateTag`, o il tag non corrisponde
- Fix: verificare che il tag sia identico a quello della fetch

**Il sito in Docker si carica senza stili**
- Causa: `.next/static` non copiato nell'immagine
- Fix: aggiungere il `COPY` dopo quello di `standalone`

**404 su una pagina con parallel route**
- Causa: manca `default.tsx` su uno slot
- Fix: aggiungerlo a ogni slot

**Le Server Action falliscono durante un rilascio**
- Causa: la chiave di cifratura degli id cambia a ogni build
- Fix: `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` fissa su tutte le istanze

**`revalidateTag` funziona a intermittenza**
- Causa: più repliche, ognuna con la sua cache su disco
- Fix: un `cacheHandler` condiviso

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_21_rsc_server_driven_ui.md` | Il modello dei Server Component e i quattro livelli di cache, in profondità |
| `tutorial_17_performance_web.md` | Le metriche che `next/image` e `next/font` migliorano, e come misurarle |
| `tutorial_16_build_tools_deploy.md` | La pipeline attorno al `next build`, e il rilascio |
| `tutorial_14_sicurezza_web.md` | La CSP di cui il §B3 è l'applicazione |

---

## Risorse di riferimento

**Documentazione:** [Next.js — App Router](https://nextjs.org/docs/app), in particolare *Rendering* e *Caching*, da leggere per intero prima di combattere con l'invalidazione · [File Conventions](https://nextjs.org/docs/app/api-reference/file-conventions) come riferimento rapido · [Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting), che elenca ciò che il §B9 riassume

**Approfondimenti:** [Security in Next.js](https://nextjs.org/blog/security-nextjs-server-components-actions), scritto dal team e più preciso di qualunque riassunto · [React — Server Components](https://react.dev/reference/rsc/server-components) · [Turbopack](https://nextjs.org/docs/app/api-reference/turbopack), da verificare sulla versione in uso

**Strumenti:** [@next/bundle-analyzer](https://www.npmjs.com/package/@next/bundle-analyzer) per vedere cosa attraversa il confine · [Playwright](https://playwright.dev/) per i test che solo il browser può fare · [next-secure-headers](https://github.com/jagaapple/next-secure-headers) come punto di partenza per gli header di sicurezza

---

> **Fine del Tutorial 25 — Next.js 15**
>
> Con questo si chiude il percorso di `05-SVILUPPO-WEB`. Il passo successivo non è un altro tutorial: è costruire qualcosa e romperlo.
