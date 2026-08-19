# Tutorial 21 — React Server Components e Server-Driven UI: Dal Principiante all'Esperto

> **Companion a:** `21-rsc-server-driven-ui.md`
> **Scope:** architettura RSC, Server e Client Component, il confine fra i due, App Router, Server Action, caching a più livelli, streaming e Suspense, pattern di recupero dati, autenticazione, Partial Prerendering, migrazione, testing, debug del payload
> **Prerequisiti:** `tutorial_07_react.md` — componenti, hook, Suspense; `tutorial_10_nodejs.md` — server; `tutorial_11_api_design.md` — cosa resta di un'API quando il client scompare
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** React 19 · Next.js 15 App Router · TypeScript

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Perché esistono i Server Component](#a1-perché-esistono-i-server-component)
  - [A2. Server o client: la regola per decidere](#a2-server-o-client-la-regola-per-decidere)
  - [A3. Il confine, e cosa lo attraversa](#a3-il-confine-e-cosa-lo-attraversa)
  - [A4. Recuperare i dati dove stanno](#a4-recuperare-i-dati-dove-stanno)
  - [A5. Server Action: mutare senza scrivere un endpoint](#a5-server-action-mutare-senza-scrivere-un-endpoint)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Il payload RSC: cosa viaggia davvero](#b1-il-payload-rsc-cosa-viaggia-davvero)
  - [B2. Streaming e Suspense](#b2-streaming-e-suspense)
  - [B3. I quattro livelli di cache](#b3-i-quattro-livelli-di-cache)
  - [B4. Invalidazione: revalidatePath e revalidateTag](#b4-invalidazione-revalidatepath-e-revalidatetag)
  - [B5. Autenticazione e autorizzazione con RSC](#b5-autenticazione-e-autorizzazione-con-rsc)
  - [B6. Il waterfall, e come si evita](#b6-il-waterfall-e-come-si-evita)
  - [B7. Server-driven UI: l'interfaccia come dato](#b7-server-driven-ui-linterfaccia-come-dato)
  - [B8. Partial Prerendering](#b8-partial-prerendering)
  - [B9. RSC contro SSR, SSG, ISR e CSR](#b9-rsc-contro-ssr-ssg-isr-e-csr)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: la dashboard in App Router](#c2-mini-progetto-la-dashboard-in-app-router)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Testare i Server Component](#d1-testare-i-server-component)
  - [D2. Migrare dal Pages Router](#d2-migrare-dal-pages-router)
  - [D3. Sicurezza del confine](#d3-sicurezza-del-confine)
  - [D4. Debug del payload e delle cache](#d4-debug-del-payload-e-delle-cache)
  - [D5. Quando NON servono i Server Component](#d5-quando-non-servono-i-server-component)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   SERVER                                          CLIENT
   ──────                                          ──────
   Server Component                                Client Component
   · gira SOLO sul server                          · 'use client'
   · zero JavaScript nel bundle                    · idratato nel browser
   · accede a database, file, segreti              · stato, effetti, eventi
   · può essere async                              · hook, API del browser
          │                                               ▲
          │  serializza l'albero renderizzato             │
          └────────► PAYLOAD RSC ────────────────────────┘
                     (non HTML: una descrizione
                      dell'albero, in streaming)

   ┌──────────────────────────────────────────────────────────┐
   │  LA REGOLA CHE DECIDE TUTTO                              │
   │   Server per default. Client SOLO quando serve: stato o   │
   │   effetti · gestori di evento · API del browser · hook    │
   │   che dipendono da uno dei tre.                          │
   └──────────────────────────────────────────────────────────┘

   IL CONFINE È MONODIREZIONALE: un Server Component può contenere
   un Client Component; un Client Component NON può importare un
   Server Component — ma può RICEVERLO come `children`.
```

---

# Parte A — Basi Assolute

---

## A1. Perché esistono i Server Component

> **Analogia:** ordinare al ristorante. Nel modello a singola pagina il cameriere ti porta ingredienti, pentole e ricetta, e cucini al tavolo: tutto arriva a te, e più il piatto è complesso più roba devi ricevere. Con i Server Component il piatto arriva pronto: gli ingredienti restano in cucina, e a te arriva solo ciò che mangi.

```
IL PROBLEMA CHE RISOLVONO
  Una pagina che mostra un elenco di prodotti in una SPA classica:
  il browser scarica l'HTML vuoto → scarica il bundle (React, il
  router, la libreria di date, il client dell'API) → lo esegue →
  solo ORA parte la richiesta dei dati → arriva la risposta.
  ➜ quattro attese in fila prima del primo contenuto utile.

  Con un Server Component: il server legge i dati e renderizza, e il
  browser riceve la pagina già piena. La libreria di date, il client
  dell'API e la logica di formattazione NON entrano nel bundle.
```

```tsx
// app/prodotti/page.tsx — un Server Component: nessuna direttiva,
// è il PREDEFINITO in App Router
import { prisma } from '@/lib/database'
import { formattaEuro } from '@/lib/denaro'

// Può essere `async`: il rendering aspetta i dati
export default async function PaginaProdotti() {
  // Accesso DIRETTO al database: niente API, niente fetch, niente
  // stato di caricamento. Questo codice non arriverà mai al browser.
  const prodotti = await prisma.prodotto.findMany({
    where: { attivo: true },
    select: { id: true, nome: true, prezzoCentesimi: true },
    orderBy: { nome: 'asc' },
    take: 50,
  })

  return (
    <ul>
      {prodotti.map((p) => (
        <li key={p.id}>
          {p.nome} — {formattaEuro(p.prezzoCentesimi)}
        </li>
      ))}
    </ul>
  )
}
```

```
COSA GUADAGNA DAVVERO  meno JavaScript nel bundle (componenti,
  librerie e logica di recupero dati restano sul server) · nessun
  round-trip in più per i dati · i segreti restano segreti · nessuno
  stato di caricamento per il primo rendering

COSA NON GUADAGNA
  ❌ non sostituisce i Client Component: qualunque interazione ne ha
     bisogno
  ❌ non rende automaticamente veloce: un Server Component che fa
     cinque query in serie è lento quanto lo sarebbe altrove
  ❌ non è "SSR con un nome nuovo": vedi B9
```

---

## A2. Server o client: la regola per decidere

```
SERVER COMPONENT (il predefinito) — quando il componente
  · legge dati da database, file o API interne
  · usa segreti o variabili d'ambiente riservate
  · importa librerie pesanti usate solo per produrre l'output
    (Markdown, sintassi evidenziata, generazione PDF, date)
  · non ha bisogno di interattività

CLIENT COMPONENT ('use client') — quando il componente
  · ha stato o effetti · ha gestori di evento
  · usa API del browser (window, document, localStorage, …)
  · usa hook che dipendono da uno dei precedenti

❌ L'ERRORE PIÙ COMUNE: `'use client'` in cima alla pagina perché
   "un pulsante deve essere cliccabile". Così TUTTO l'albero diventa
   client — la tabella, i grafici, le librerie di date — e il
   vantaggio sparisce.
```

```tsx
// ✅ Il confine si sposta il PIÙ IN BASSO POSSIBILE: solo la parte
//    interattiva diventa client, e il filtro avviene sul SERVER —
//    con un indice, invece di scaricare diecimila prodotti per
//    mostrarne venti
// app/prodotti/page.tsx  — Server Component
import { FiltroProdotti } from './FiltroProdotti'

export default async function Pagina({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>
}) {
  const { q } = await searchParams
  const prodotti = await cercaProdotti(q)

  return (
    <>
      <FiltroProdotti valoreIniziale={q ?? ''} />
      <ul>
        {prodotti.map((p) => (
          <li key={p.id}>{p.nome}</li>
        ))}
      </ul>
    </>
  )
}
```

```tsx
// app/prodotti/FiltroProdotti.tsx — il SOLO pezzo che va nel bundle
'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useState, useTransition } from 'react'

export function FiltroProdotti({ valoreIniziale }: { valoreIniziale: string }) {
  const [valore, setValore] = useState(valoreIniziale)
  const [inTransizione, avviaTransizione] = useTransition()
  const router = useRouter()
  const parametri = useSearchParams()

  function aggiorna(nuovo: string) {
    setValore(nuovo)
    const query = new URLSearchParams(parametri)
    nuovo ? query.set('q', nuovo) : query.delete('q')

    // startTransition mantiene l'interfaccia reattiva mentre il
    // server rirenderizza: il campo non si blocca
    avviaTransizione(() => router.replace(`?${query}`))
  }

  return (
    <input
      value={valore}
      onChange={(e) => aggiorna(e.target.value)}
      aria-busy={inTransizione}
      placeholder="Cerca prodotti"
    />
  )
}
```

---
## A3. Il confine, e cosa lo attraversa

```
LE TRE REGOLE DEL CONFINE

1. `'use client'` MARCA UN PUNTO DI INGRESSO, non un file isolato.
   Tutto ciò che quel file IMPORTA diventa parte del bundle client.
   Un `'use client'` in cima a un file che importa mezza
   applicazione porta mezza applicazione nel browser.

2. UN CLIENT COMPONENT NON PUÒ IMPORTARE UN SERVER COMPONENT.
   Ma può RICEVERLO come `children` o come prop: il Server
   Component viene renderizzato sul server, e il risultato passa
   attraverso.

3. LE PROP CHE ATTRAVERSANO IL CONFINE DEVONO ESSERE
   SERIALIZZABILI. Passano: primitivi, oggetti e array semplici,
   Date, Map, Set, Promise, e i riferimenti ai componenti.
   NON passano: funzioni (tranne le Server Action), classi,
   Symbol, elementi del DOM.
```

```tsx
// ❌ NON FUNZIONA: un Client Component che importa un Server Component
//      'use client'
//      import { ElencoDalDatabase } from './ElencoDalDatabase'
//      → diventerebbe client, e il database non c'è

// ✅ FUNZIONA: il Server Component arriva come children
// app/pagina.tsx — Server Component
export default function Pagina() {
  return (
    <Pannello>
      <ElencoDalDatabase />
    </Pannello>
  )
}
```

```tsx
// Il pattern che ne deriva, e che risolve il 90% dei casi: i
// contenitori interattivi accettano children, e non sanno né
// devono sapere cosa contengono
'use client'
import { useState, type ReactNode } from 'react'

export function Fisarmonica({ titolo, children }: { titolo: string; children: ReactNode }) {
  const [aperta, setAperta] = useState(false)

  return (
    <section>
      <button onClick={() => setAperta((a) => !a)} aria-expanded={aperta}>
        {titolo}
      </button>
      {/* children può essere un Server Component che legge dal
          database: renderizzato sul server, passa di qui già pronto */}
      {aperta && children}
    </section>
  )
}
```

---

## A4. Recuperare i dati dove stanno

```tsx
// Il recupero avviene NEL componente che usa i dati, non in cima
// alla pagina: ogni componente chiede ciò che gli serve.
// ⚠ Sembra un N+1 e non lo è, se si usa la deduplica (vedi sotto).
export default async function PaginaOrdine({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return (
    <>
      <IntestazioneOrdine id={id} />
      <RigheOrdine id={id} />
      <StoricoSpedizione id={id} />
    </>
  )
}
```

```typescript
// lib/dati.ts — `cache` di React deduplica le chiamate con gli
// stessi argomenti DENTRO una singola richiesta: i tre componenti
// sopra chiedono lo stesso ordine, e la query viene eseguita UNA volta
import { cache } from 'react'
import { prisma } from './database'

export const leggiOrdine = cache(async (id: string) => {
  return prisma.ordine.findUnique({
    where: { id },
    select: { id: true, numero: true, stato: true, totaleCentesimi: true },
  })
})
```

```tsx
// Le richieste indipendenti vanno in PARALLELO: `await` in sequenza
// somma i tempi (200 + 180 + 240 = 620 ms), Promise.all prende il
// massimo (240 ms)
export default async function Pagina() {
  const [utente, ordini, notifiche] = await Promise.all([
    leggiUtente(),
    leggiOrdini(),
    leggiNotifiche(),
  ])

  return <Cruscotto utente={utente} ordini={ordini} notifiche={notifiche} />
}
```

```
⚠ IL `fetch` DI NEXT.JS È ESTESO: mette in cache e deduplica da
  solo, con opzioni per il comportamento.
    fetch(url, { cache: 'force-cache' })        memorizza
    fetch(url, { cache: 'no-store' })           mai
    fetch(url, { next: { revalidate: 60 } })    rigenera dopo 60 s
    fetch(url, { next: { tags: ['ordini'] } })  invalidabile per tag
  Le chiamate al database NON passano da `fetch`: per quelle si usa
  `cache` di React (deduplica dentro la richiesta) e
  `unstable_cache` o la cache di Next per la persistenza fra richieste.
```

---

## A5. Server Action: mutare senza scrivere un endpoint

```typescript
// app/azioni/ordini.ts
'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { z } from 'zod'
import { prisma } from '@/lib/database'
import { utenteCorrente } from '@/lib/autenticazione'

const SchemaOrdine = z.object({ cliente: z.string().trim().min(1).max(200) })

export async function creaOrdine(_stato: Stato, dati: FormData): Promise<Stato> {
  // ⚠ UNA SERVER ACTION È UN ENDPOINT HTTP PUBBLICO. Il fatto che si
  //   chiami come una funzione non la protegge: autenticazione,
  //   autorizzazione e validazione vanno fatte QUI, sempre.
  const utente = await utenteCorrente()
  if (!utente) return { esito: 'errore', messaggio: 'Non autenticato' }

  const analizzati = SchemaOrdine.safeParse(Object.fromEntries(dati))
  if (!analizzati.success) {
    return { esito: 'errore', campi: analizzati.error.flatten().fieldErrors }
  }

  const ordine = await prisma.ordine.create({
    data: { ...analizzati.data, utenteId: utente.id },
  })

  revalidatePath('/ordini') // senza, l'elenco mostra dati vecchi
  redirect(`/ordini/${ordine.id}`)
}
```

```tsx
// app/ordini/nuovo/ModuloOrdine.tsx
'use client'

import { useActionState } from 'react'
import { useFormStatus } from 'react-dom'
import { creaOrdine } from '@/app/azioni/ordini'

function PulsanteInvio() {
  // useFormStatus legge lo stato del form PADRE: funziona solo in
  // un componente figlio del <form>
  const { pending } = useFormStatus()
  return <button type="submit" disabled={pending}>{pending ? 'Creazione…' : 'Crea ordine'}</button>
}

export function ModuloOrdine() {
  const [stato, azione] = useActionState(creaOrdine, { esito: 'iniziale' })

  return (
    // ⚠ Il form funziona ANCHE SENZA JavaScript: è un <form> vero con
    //   un'azione. È il ripiego che le SPA non hanno mai avuto.
    <form action={azione}>
      <label htmlFor="cliente">Cliente</label>
      <input id="cliente" name="cliente" required aria-describedby="errore-cliente" />
      {stato.campi?.cliente && (
        <p id="errore-cliente" role="alert">{stato.campi.cliente[0]}</p>
      )}
      <PulsanteInvio />
    </form>
  )
}
```

```
LE QUATTRO REGOLE: sono endpoint pubblici, quindi validare,
autenticare e autorizzare · non restituire dati sensibili, perché il
risultato torna al client · `revalidatePath` o `revalidateTag` dopo
ogni mutazione · con `<form action>` funzionano anche senza
JavaScript, ed è un vantaggio che si perde usandole da `onClick`
```

---
# Parte B — Comprensione Profonda

---

## B1. Il payload RSC: cosa viaggia davvero

```
IL SERVER NON MANDA HTML AL CLIENT — o meglio, non solo. Manda una
DESCRIZIONE SERIALIZZATA dell'albero renderizzato, in un formato a
righe che arriva in streaming.

  0:["$","div",null,{"children":[["$","h1",null,{"children":"Ordini"}],
     ["$L1",null,{"id":"ord_1"}]]}]
  1:I["./FiltroOrdini.js",["chunk-a3f9"],"FiltroOrdini"]

  · "$" seguito da un tag = un elemento del DOM
  · "$L1" = un segnaposto: quel pezzo arriverà dopo (streaming)
  · "I[...]" = un riferimento a un CLIENT component, con il file da
    caricare

⚠ È QUI CHE SI VEDE LA DIFFERENZA CON L'HTML: il payload descrive
  l'albero di React, non il markup. Il client lo usa per aggiornare
  l'albero esistente senza ricostruire la pagina — ed è per questo
  che una navigazione in App Router conserva lo stato dei Client
  Component e la posizione dello scorrimento.
```

```
DUE CONSEGUENZE PRATICHE
1. TUTTO CIÒ CHE PASSA COME PROP A UN CLIENT COMPONENT FINISCE NEL
   PAYLOAD, e viaggia sulla rete. Passare un oggetto con quaranta
   campi per usarne due significa spedirne quaranta.
2. IL PAYLOAD È VISIBILE AL CLIENT. Un campo che non si vuole
   mostrare non va passato — anche se il componente non lo rende.
   ⚠ È lo stesso errore del `select` mancante in un'API: si
     restituisce l'oggetto intero, e `passwordHash` è nel payload.

  ❌ <PannelloUtente utente={utente} />
  ✅ <PannelloUtente nome={utente.nome} avatarUrl={utente.avatarUrl} />
```

---

## B2. Streaming e Suspense

> **Analogia:** un menù servito a portate invece che tutto insieme. Non aspetti il dolce per cominciare l'antipasto — e la cucina lavora mentre tu già mangi.

```tsx
// Senza Suspense: la pagina intera aspetta la parte più lenta
export default async function Pagina() {
  const [rapido, lento] = await Promise.all([leggiRapido(), leggiLento()]) // 2,4 s
  return (
    <>
      <SezioneRapida dati={rapido} />
      <SezioneLenta dati={lento} />
    </>
  )
}

// Con Suspense: la parte pronta si vede subito, il resto arriva dopo
export default function Pagina() {
  return (
    <>
      {/* Non c'è await qui: il componente si sospende da solo */}
      <SezioneRapida />

      <Suspense fallback={<ScheletroSezione />}>
        <SezioneLenta />
      </Suspense>
    </>
  )
}
```

```
COME FUNZIONA, SOTTO
  Il server invia l'HTML della parte pronta, con un segnaposto dove
  c'è il Suspense. Quando la parte lenta finisce, invia un secondo
  pezzo con il contenuto e uno script che lo mette al posto giusto.
  ➜ Il TTFB non dipende più dalla query più lenta, e l'LCP nemmeno
    (se l'elemento principale è nella parte veloce).

`app/ordini/loading.tsx` è il fallback automatico di un'intera rotta.
⚠ Uno scheletro con la FORMA del contenuto, non uno spinner: evita
  lo spostamento del layout quando i dati arrivano.

DOVE METTERE I CONFINI DI SUSPENSE
  ✅ intorno a ciò che è LENTO e NON critico: statistiche,
     raccomandazioni, attività recente
  ✅ intorno a sezioni indipendenti, così si sbloccano una per una
  ❌ intorno a TUTTO: si ottiene una pagina che è tutta scheletro,
     e nessun vantaggio
  ❌ intorno all'elemento LCP: mostrare uno scheletro dove dovrebbe
     esserci il contenuto principale peggiora la metrica

⚠ E LA TRAPPOLA: un `await` nel componente PADRE blocca tutto, anche
  se i figli sono in Suspense. Il confine va messo SOPRA il
  componente che aspetta, non intorno.
```

---

## B3. I quattro livelli di cache

```
   RICHIESTA
       │
   1. ROUTER CACHE (nel browser)
       │  il payload RSC delle rotte già visitate, per la
       │  navigazione indietro/avanti. Dura pochi minuti.
       ▼
   2. FULL ROUTE CACHE (sul server)
       │  l'HTML e il payload di una rotta STATICA, generati alla
       │  build. Persistente fino a un'invalidazione.
       ▼
   3. DATA CACHE (sul server)
       │  il risultato delle fetch, con `revalidate` e `tags`.
       │  Persiste fra richieste E fra rilasci.
       ▼
   4. REQUEST MEMOIZATION (dentro UNA richiesta)
          `cache()` di React e la deduplica di `fetch`: la stessa
          chiamata fatta da tre componenti viene eseguita una volta.

⚠ SONO QUATTRO COSE DIVERSE, E IL 90% DELLA CONFUSIONE SU RSC NASCE
  DAL CONFONDERLE. "Ho invalidato la cache e vedo ancora i dati
  vecchi" significa quasi sempre che si è invalidato il livello
  sbagliato.
```

```typescript
// Il controllo, livello per livello

// 4. dentro la richiesta — deduplica automatica
const ordine = await leggiOrdine(id) // cache() di React

// 3. fra le richieste — la Data Cache
const risposta = await fetch(url, { next: { revalidate: 60, tags: ['ordini'] } })

// 2. la rotta: dinamica o statica
export const dynamic = 'force-dynamic' // mai statica
export const revalidate = 3600 // statica, rigenerata ogni ora

// 1. il browser: si azzera con router.refresh()
```

```
COSA RENDE UNA ROTTA DINAMICA (e quindi non memorizzabile al punto 2)
  · `cookies()`, `headers()`, `searchParams`
  · `fetch` con `cache: 'no-store'`
  · `export const dynamic = 'force-dynamic'`
  · `connection()` chiamata esplicitamente

⚠ È FACILE RENDERE DINAMICA UNA PAGINA SENZA ACCORGERSENE: basta un
  componente in profondità che legge un cookie. Il risultato è che
  una pagina che poteva essere statica viene rigenerata a ogni
  visita. `next build` stampa il tipo di ogni rotta: va letto.
```

---

## B4. Invalidazione: revalidatePath e revalidateTag

```typescript
'use server'

import { revalidatePath, revalidateTag } from 'next/cache'

export async function aggiornaOrdine(id: string, dati: DatiOrdine) {
  await prisma.ordine.update({ where: { id }, data: dati })

  // Per PERCORSO: invalida quella rotta specifica
  revalidatePath(`/ordini/${id}`)
  // Con 'layout': invalida anche tutte le rotte annidate sotto
  revalidatePath('/ordini', 'layout')

  // Per TAG: invalida ogni fetch marcata con quel tag, ovunque sia
  revalidateTag('ordini')
}
```

```
QUALE DEI DUE
  revalidatePath  quando sai QUALI PAGINE mostrano quel dato. Preciso
    e limitato, ma va tenuto allineato: una pagina nuova che mostra
    gli ordini e che nessuno aggiunge alla lista resta con dati vecchi.
  revalidateTag   quando NON lo sai, o sono molte. Il tag si mette
    sulla fetch, e l'invalidazione lo raggiunge ovunque: è la forma
    più robusta, e quella da preferire.

I TAG SI PROGETTANO COME UNA GERARCHIA
  tags: ['ordini', `ordine-${id}`]
  ➜ `revalidateTag('ordini')` prende l'elenco e i dettagli,
    `revalidateTag('ordine-42')` solo quello.

⚠ TRE COSE CHE SORPRENDONO
  1. `revalidate*` NON aggiorna la pagina che l'utente sta
     guardando: marca la cache come obsoleta, e l'aggiornamento
     avviene alla navigazione successiva o con `router.refresh()`.
  2. La ROUTER CACHE del browser è separata: dopo una Server Action
     Next la aggiorna, ma una modifica fatta altrove no.
  3. Invalidare troppo largamente (`revalidatePath('/', 'layout')`)
     funziona sempre e costa carissimo: rigenera l'intero sito.
```

---

## B5. Autenticazione e autorizzazione con RSC

```typescript
// lib/autenticazione.ts — `cache` evita che dieci componenti
// verifichino la stessa sessione dieci volte nella stessa richiesta
import { cache } from 'react'
import { cookies } from 'next/headers'

export const utenteCorrente = cache(async () => {
  const token = (await cookies()).get('sessione')?.value
  if (!token) return null
  try {
    return await verificaSessione(token)
  } catch {
    return null
  }
})

// Il controllo che REINDIRIZZA: si usa nelle pagine
export async function richiediUtente() {
  const utente = await utenteCorrente()
  if (!utente) redirect('/accedi')
  return utente
}
```

```
⚠ IL MIDDLEWARE NON È UN CONTROLLO DI AUTORIZZAZIONE. Serve per i
  reindirizzamenti veloci sui percorsi, ma:
   · gira sull'edge, dove il database spesso non è raggiungibile
   · non copre le Server Action, che sono endpoint a sé
   · un matcher scritto male lascia scoperta una rotta, e nessuno se
     ne accorge
  ➜ IL CONTROLLO VA FATTO DOVE SI LEGGE IL DATO: nella pagina, nel
    layout protetto, e in OGNI Server Action.
```

```typescript
// Il pattern che rende difficile dimenticarsene: il controllo sta
// nella funzione che legge, non in un `if` che qualcuno deve scrivere
export const leggiOrdiniMiei = cache(async () => {
  const utente = await richiediUtente()

  // Il filtro sul proprietario è dentro la query, non aggiungibile
  // dopo. È lo stesso principio del tutorial_13 §B7.
  return prisma.ordine.findMany({
    where: { utenteId: utente.id },
    orderBy: { creatoIl: 'desc' },
  })
})
```

```typescript
// E in ogni Server Action, senza eccezioni. `deleteMany` con il
// filtro sul proprietario: zero righe eliminate significa "non
// esiste, o non è tuo" — e la risposta è la stessa.
'use server'

export async function eliminaOrdine(id: string) {
  const utente = await richiediUtente()
  const esito = await prisma.ordine.deleteMany({ where: { id, utenteId: utente.id } })
  if (esito.count === 0) return { esito: 'errore', messaggio: 'Ordine non trovato' }

  revalidateTag('ordini')
  return { esito: 'ok' }
}
```

---

## B6. Il waterfall, e come si evita

```
   IL WATERFALL: componenti annidati che aspettano uno dopo l'altro

   <Pagina>            await leggiUtente()       200 ms
     <Profilo>         await leggiProfilo()      180 ms   ← comincia
       <Preferenze>    await leggiPreferenze()   150 ms     solo dopo
                                                 ──────
                                                  530 ms

   Ognuno aspetta che il padre abbia finito di renderizzare per
   cominciare il proprio await. È lo stesso problema dell'N+1, in
   una forma diversa.
```

```tsx
// ✅ SOLUZIONE 1 — avviare le richieste IN ALTO, e passare le
//    Promise: le richieste partono insieme, e ogni componente
//    aspetta solo la sua
export default function Pagina() {
  // Nessun await qui: le tre richieste partono in parallelo
  const utente = leggiUtente()
  const profilo = leggiProfilo()
  const preferenze = leggiPreferenze()

  return (
    <>
      <Suspense fallback={<ScheletroProfilo />}>
        <Profilo utente={utente} profilo={profilo} />
      </Suspense>
      <Suspense fallback={<ScheletroPreferenze />}>
        <Preferenze dati={preferenze} />
      </Suspense>
    </>
  )
}

// I componenti ricevono la Promise e la consumano con `use`
import { use } from 'react'

function Profilo({ utente, profilo }: { utente: Promise<Utente>; profilo: Promise<Bio> }) {
  return <h1>{use(utente).nome} — {use(profilo).bio}</h1>
}
```

```tsx
// ✅ SOLUZIONE 2 — il preload: la richiesta parte PRIMA che il
//    componente venga renderizzato. `cache()` conserva il risultato,
//    quindi il componente la troverà già pronta.
export const preloadOrdine = (id: string) => void leggiOrdine(id)

export default async function Pagina({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  preloadOrdine(id)
  const utente = await richiediUtente() // nel frattempo si fa questo
  return <DettaglioOrdine id={id} utente={utente} />
}
```

```
⚠ IL WATERFALL È LA CAUSA PRINCIPALE DI UNA PAGINA RSC LENTA, e non
  si vede leggendo il codice: ogni componente sembra ragionevole. Si
  vede nella cascata delle tracce (tutorial_19 §B5), o attivando il
  logging delle query.
```

---

## B7. Server-driven UI: l'interfaccia come dato

```
L'IDEA: il server non manda solo i DATI, manda la DESCRIZIONE
dell'interfaccia. Il client ha un catalogo di componenti e li
compone secondo ciò che riceve.

  ✅ si cambia un'interfaccia senza rilasciare il client, si fanno
     test A/B sul server, si condivide un catalogo fra più prodotti
  ❌ un livello di indirezione in più, la type safety da costruire
     a mano, e il debug più difficile: l'interfaccia non è nel codice
```

```typescript
// La forma minima: uno schema chiuso, validato in entrambe le
// direzioni. ⚠ Senza lo schema, questo pattern degenera in "il
// server manda qualunque cosa e il client spera".
import { z } from 'zod'

const SchemaBlocco = z.discriminatedUnion('tipo', [
  z.object({ tipo: z.literal('intestazione'), titolo: z.string().max(200) }),
  z.object({
    tipo: z.literal('richiamo'),
    testo: z.string().max(500),
    azione: z.object({ etichetta: z.string().max(50), href: z.string() }),
  }),
])

export type Blocco = z.infer<typeof SchemaBlocco>
export const SchemaPagina = z.object({ blocchi: z.array(SchemaBlocco).max(30) })
```

```tsx
// Il rendering: una mappa da tipo a componente, con il caso
// sconosciuto gestito — arriva quando il server è più nuovo del
// client, e va ignorato invece di rompere la pagina
const COMPONENTI = { intestazione: Intestazione, richiamo: Richiamo } as const

export function RenderizzaBlocchi({ blocchi }: { blocchi: Blocco[] }) {
  return blocchi.map((blocco, indice) => {
    const Componente = COMPONENTI[blocco.tipo as keyof typeof COMPONENTI]
    return Componente ? <Componente key={indice} {...(blocco as never)} /> : null
  })
}
```

```
⚠ QUANDO NON USARLO: se il client e il server si rilasciano insieme,
  questo pattern aggiunge complessità e non risolve niente. Con RSC
  buona parte del beneficio si ottiene già gratis — il server decide
  cosa renderizzare, e lo fa in JSX leggibile. Il server-driven UI
  resta utile per i client che NON si possono rilasciare a comando:
  app mobili native, dispositivi, integrazioni.
```

---

## B8. Partial Prerendering

```
IL PROBLEMA CHE RISOLVE: una pagina è quasi tutta statica, ma un
pezzo dipende dall'utente (il nome nell'intestazione, il carrello).
Quel pezzo rende DINAMICA l'intera pagina, e si perde la cache.
PPR separa le due cose: la parte statica è generata alla build e
servita dalla CDN, i buchi dinamici arrivano in streaming nella
stessa risposta.
```

```tsx
// app/prodotti/[id]/page.tsx
export const experimental_ppr = true

export default function PaginaProdotto({ params }) {
  return (
    <>
      {/* STATICO: generato alla build, servito dalla CDN */}
      <DettaglioProdotto params={params} />

      {/* DINAMICO: il buco viene riempito in streaming */}
      <Suspense fallback={<ScheletroCarrello />}>
        <StatoCarrello />
      </Suspense>
    </>
  )
}
```

```
LA REGOLA: tutto ciò che usa `cookies()`, `headers()` o dati
dell'utente deve stare DENTRO un `<Suspense>`; ciò che sta fuori
viene prerenderizzato. IL GUADAGNO: il TTFB della parte statica è
quello di un file su CDN, e l'LCP dipende da quella — non dalla
query più lenta.

⚠ È SPERIMENTALE al momento della scrittura: l'API e il nome del
  flag possono cambiare. Va verificato sulla documentazione della
  versione che si usa prima di adottarlo in produzione.
```

---

## B9. RSC contro SSR, SSG, ISR e CSR

| | Dove renderizza | Quando | JS nel bundle | Dati freschi |
|---|---|---|---|---|
| CSR | Browser | a ogni visita | tutto | dopo il caricamento |
| SSG | Server | alla build | tutto (idratazione) | fermi alla build |
| ISR | Server | build + rigenerazione | tutto | entro `revalidate` |
| SSR | Server | a ogni richiesta | tutto | sempre |
| RSC | Server | a ogni richiesta o alla build | **solo i client component** | dipende dalla cache |

```
LA DIFFERENZA CHE CONTA, E CHE QUASI TUTTI SBAGLIANO
  SSR renderizza sul server e poi INVIA TUTTO IL CODICE al client
  per idratarlo: il componente esiste in entrambi i posti, e il suo
  JavaScript è nel bundle.
  RSC renderizza sul server e il codice del componente NON ARRIVA
  MAI al client. Non c'è idratazione per i Server Component: non
  hanno stato da ripristinare.

  ➜ "RSC è SSR con un nome nuovo" è falso proprio su questo punto.

E NON SI ESCLUDONO: in App Router una pagina può avere Server
Component (statici o dinamici), Client Component idratati, e parti
in streaming — tutto nella stessa risposta.
```

```
COME SI SCEGLIE, IN PRATICA
  contenuto pubblico che cambia raramente   → statico + ISR
  contenuto personalizzato                  → RSC dinamico
  pagina quasi statica con un pezzo personale → PPR
  app autenticata e molto interattiva       → RSC + client mirati
  interfaccia interamente interattiva senza SEO → CSR va benissimo
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Spostare il confine client

**Obiettivo:** una pagina interamente `'use client'` porta 340 kB nel bundle. Ridurre a meno di 60 kB spostando il confine.

```tsx
// IL CODICE DA CORREGGERE — app/ordini/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { it } from 'date-fns/locale'
import { Chart } from 'chart.js/auto'

export default function PaginaOrdini() {
  const [ordini, setOrdini] = useState([])
  const [filtro, setFiltro] = useState('')
  const [inCaricamento, setInCaricamento] = useState(true)

  useEffect(() => {
    fetch('/api/ordini')
      .then((r) => r.json())
      .then((d) => {
        setOrdini(d.elementi)
        setInCaricamento(false)
      })
  }, [])

  const filtrati = ordini.filter((o) => o.cliente.toLowerCase().includes(filtro.toLowerCase()))
  if (inCaricamento) return <p>Caricamento…</p>

  return (
    <>
      <input value={filtro} onChange={(e) => setFiltro(e.target.value)} />
      <GraficoFatturato ordini={ordini} />
      <table>
        {filtrati.map((o) => (
          <tr key={o.id}>
            <td>{o.cliente}</td>
            <td>{format(new Date(o.creatoIl), 'dd MMMM yyyy', { locale: it })}</td>
          </tr>
        ))}
      </table>
    </>
  )
}
```

```
# LA DIAGNOSI — cinque problemi
# 1. `'use client'` in cima: tutto entra nel bundle, date-fns e
#    chart.js compresi (280 kB dei 340)
# 2. Dati in useEffect: quattro attese in fila prima di vedere
#    qualcosa (bundle → esecuzione → fetch → risposta)
# 3. Filtro nel browser: diecimila record per mostrarne venti
# 4. Date formattate nel client: date-fns e il locale italiano nel
#    bundle, per una funzione
# 5. Nessuno stato di errore: se la fetch fallisce, resta
#    "Caricamento…" per sempre
```

```tsx
// LA SOLUZIONE — app/ordini/page.tsx (Server Component)
import { Suspense } from 'react'
import { FiltroOrdini } from './FiltroOrdini'
import { TabellaOrdini } from './TabellaOrdini'
import { GraficoFatturato } from './GraficoFatturato'

export default async function PaginaOrdini({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>
}) {
  const { q } = await searchParams

  return (
    <>
      {/* L'unico pezzo interattivo: ~4 kB */}
      <FiltroOrdini valoreIniziale={q ?? ''} />

      {/* Il grafico è pesante e non critico: arriva dopo */}
      <Suspense fallback={<ScheletroGrafico />}>
        <GraficoFatturato />
      </Suspense>

      {/* La chiave `q` rimonta la tabella quando il filtro cambia,
          mostrando il fallback invece della tabella vecchia */}
      <Suspense key={q} fallback={<ScheletroTabella />}>
        <TabellaOrdini filtro={q} />
      </Suspense>
    </>
  )
}
```

```tsx
// app/ordini/TabellaOrdini.tsx — Server Component: il filtro e la
// formattazione avvengono sul server, e date-fns resta lì
import { format } from 'date-fns'
import { it } from 'date-fns/locale'
import { prisma } from '@/lib/database'

export async function TabellaOrdini({ filtro }: { filtro?: string }) {
  const ordini = await prisma.ordine.findMany({
    // Il filtro va nella QUERY, con un indice: non si scaricano
    // diecimila record per scartarne 9.980
    where: filtro ? { cliente: { contains: filtro, mode: 'insensitive' } } : undefined,
    select: { id: true, cliente: true, creatoIl: true, totaleCentesimi: true },
    orderBy: { creatoIl: 'desc' },
    take: 50,
  })

  if (ordini.length === 0) return <p>Nessun ordine corrisponde alla ricerca.</p>

  return (
    <table>
      <tbody>
        {ordini.map((o) => (
          <tr key={o.id}>
            <td>{o.cliente}</td>
            <td>{format(o.creatoIl, 'dd MMMM yyyy', { locale: it })}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

```
# IL RISULTATO
#   bundle   340 kB → 52 kB
#   attese prima del contenuto:  quattro → una
#   date-fns e chart.js: fuori dal percorso critico
#   e in più: funziona senza JavaScript, ha uno stato vuoto, e il
#   filtro è nell'URL (condivisibile, e il tasto indietro funziona)
#
# ⚠ IL PASSO CHE VALE DI PIÙ È IL TERZO: filtrare nel database
#   invece che nel browser. Il bundle è visibile, ma diecimila
#   record trasferiti costano di più di 280 kB di JavaScript.
```

---
### Esercizio 2 — Eliminare un waterfall

**Obiettivo:** una pagina di dettaglio impiega 1,4 s di TTFB. Le query sono veloci; il problema è l'ordine.

```tsx
// IL CODICE DA CORREGGERE
export default async function PaginaOrdine({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const ordine = await leggiOrdine(id) // 180 ms
  return (
    <>
      <Intestazione ordine={ordine} />
      <DettaglioCliente clienteId={ordine.clienteId} />
      <Spedizione ordineId={id} />
    </>
  )
}

async function DettaglioCliente({ clienteId }: { clienteId: string }) {
  const cliente = await leggiCliente(clienteId) // 220 ms
  const storico = await leggiStoricoAcquisti(clienteId) // 340 ms
  return <SchedaCliente cliente={cliente} storico={storico} />
}

async function Spedizione({ ordineId }: { ordineId: string }) {
  const tracciamento = await leggiTracciamento(ordineId) // 680 ms
  return <StatoSpedizione dati={tracciamento} />
}
```

```
# LA DIAGNOSI — la cascata, letta dalle tracce
#   leggiOrdine            ████                       180 ms
#     leggiCliente             █████                  220 ms
#       leggiStoricoAcquisti        ███████           340 ms
#         leggiTracciamento              ████████████ 680 ms
#                                                     ────────
#                                                     1.420 ms
#
#   Tre problemi distinti:
#    1. `leggiStoricoAcquisti` aspetta `leggiCliente` senza motivo:
#       ha già il clienteId
#    2. `Spedizione` aspetta tutto l'albero, e serve solo l'ordineId
#       — disponibile fin dall'inizio
#    3. il tracciamento è la parte più lenta ed è la MENO importante:
#       blocca la pagina per qualcosa che l'utente guarda per ultimo
```

```tsx
// LA SOLUZIONE
import { Suspense, use } from 'react'

export default async function PaginaOrdine({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  // 1. Il tracciamento parte SUBITO: non dipende da nulla
  preloadTracciamento(id)

  const ordine = await leggiOrdine(id)

  // 2. Le due query del cliente partono insieme, non in sequenza
  const cliente = leggiCliente(ordine.clienteId)
  const storico = leggiStoricoAcquisti(ordine.clienteId)

  return (
    <>
      {/* Si vede subito: l'LCP non aspetta niente */}
      <Intestazione ordine={ordine} />

      <Suspense fallback={<ScheletroCliente />}>
        <DettaglioCliente cliente={cliente} storico={storico} />
      </Suspense>

      {/* 3. Il più lento è anche il meno importante: arriva per
             ultimo senza bloccare il resto */}
      <Suspense fallback={<ScheletroSpedizione />}>
        <Spedizione ordineId={id} />
      </Suspense>
    </>
  )
}

// I componenti consumano le Promise con `use`
function DettaglioCliente({
  cliente,
  storico,
}: {
  cliente: Promise<Cliente>
  storico: Promise<Acquisto[]>
}) {
  return <SchedaCliente cliente={use(cliente)} storico={use(storico)} />
}
```

```
# IL RISULTATO
#   leggiOrdine        ████                180 ms
#   leggiTracciamento  ████████████        680 ms  ← partito subito
#     leggiCliente         █████           220 ms  ← in parallelo
#     leggiStorico         ███████         340 ms    con il cliente
#
#   TTFB     1.420 → 190 ms   (l'intestazione si vede quasi subito)
#   completo 1.420 → 700 ms   (limitato dalla query più lenta)
#
# ⚠ Il TTFB scende dell'87% perché la prima parte non aspetta più
#   nessuno. È la differenza che l'utente sente: la pagina "c'è"
#   dopo 190 ms, e si completa mentre la sta già guardando.
```

---
### Esercizio 3 — Chiudere una Server Action non protetta

**Obiettivo:** una Server Action sembra sicura perché "si chiama come una funzione". Trovare i buchi e chiuderli.

```typescript
// IL CODICE DA CORREGGERE
'use server'

export async function aggiornaProfilo(dati: FormData) {
  const utenteId = dati.get('utenteId') as string

  await prisma.utente.update({
    where: { id: utenteId },
    data: Object.fromEntries(dati) as never,
  })

  revalidatePath('/profilo')
}
```

```
# LA DIAGNOSI — cinque buchi
# 1. NESSUNA AUTENTICAZIONE. Una Server Action è un endpoint HTTP
#    pubblico: si chiama con una POST, senza passare dalla pagina.
# 2. `utenteId` VIENE DAL FORM. Chiunque può modificare il profilo
#    di chiunque cambiando un campo nascosto.
# 3. MASS ASSIGNMENT. `Object.fromEntries(dati)` passa OGNI campo al
#    database: `ruolo=admin` diventa un'escalation di privilegi.
# 4. NESSUNA VALIDAZIONE di tipi, lunghezze o formati.
# 5. NESSUNA GESTIONE DELL'ERRORE: un'eccezione produce un errore
#    generico, e l'utente non sa cosa è andato storto.
```

```typescript
// LA SOLUZIONE
'use server'

import { z } from 'zod'
import { revalidateTag } from 'next/cache'
import { richiediUtente } from '@/lib/autenticazione'

// Lo schema elenca ciò che è modificabile: `.strict()` RIFIUTA i
// campi non previsti invece di ignorarli, così un tentativo di
// mass assignment diventa un errore visibile
const SchemaProfilo = z
  .object({
    nome: z.string().trim().min(1).max(100),
    bio: z.string().trim().max(500).optional(),
  })
  .strict()

export async function aggiornaProfilo(_stato: Stato, dati: FormData): Promise<Stato> {
  // 1. L'IDENTITÀ VIENE DALLA SESSIONE, mai dal form
  const utente = await richiediUtente()

  const analizzati = SchemaProfilo.safeParse(Object.fromEntries(dati))
  if (!analizzati.success) {
    return { esito: 'errore', campi: analizzati.error.flatten().fieldErrors }
  }

  try {
    await prisma.utente.update({
      // 2. L'id è quello della SESSIONE: non c'è modo di toccare il
      //    profilo di un altro
      where: { id: utente.id },
      // 3. Solo i campi validati: `ruolo` non c'è, e non può esserci
      data: analizzati.data,
    })
  } catch (errore) {
    // 5. L'errore interno resta nei log; all'utente un messaggio
    //    generico (tutorial_11 §A5)
    registro.error({ errore, utenteId: utente.id }, 'aggiornamento profilo fallito')
    return { esito: 'errore', messaggio: 'Non è stato possibile salvare. Riprova.' }
  }

  revalidateTag(`utente-${utente.id}`)
  return { esito: 'ok' }
}
```

```
# LA VERIFICA — si prova come un attaccante, non come un utente
#  1. chiamare l'azione senza sessione → deve fallire
#  2. inviare `utenteId` di un altro utente → IGNORATO
#  3. inviare `ruolo=admin` → errore di validazione, non silenzio
#  4. un nome di diecimila caratteri → 422, non un errore del database
#  5. cercare i dati sensibili nel payload RSC: non devono esserci
#
# ⚠ OGNI Server Action ha le stesse esigenze di un endpoint REST. Il
#   fatto che si scriva come una funzione è comodità di sintassi, non
#   una proprietà di sicurezza.
```

---

## C2. Mini-progetto: la dashboard in App Router

L'esercizio chiave del modulo: portare la dashboard dei tutorial precedenti in App Router, con il confine client al posto giusto.

```
app/
├── layout.tsx                 radice: font, providers minimi
├── (autenticato)/
│   ├── layout.tsx             richiediUtente() — protegge il gruppo
│   ├── page.tsx               cruscotto: sezioni in Suspense
│   ├── ordini/                page · loading · error · [id]/page
│   └── azioni/ordini.ts       'use server' — validate e autorizzate
├── accedi/page.tsx            pubblica
└── lib/                       dati.ts (cache + tag) · autenticazione.ts

LE DECISIONI DI PROGETTO
  · Server Component per default; 'use client' solo su filtro,
    ordinamento della tabella e grafici
  · il gruppo (autenticato) ha un layout che chiama richiediUtente():
    una rotta nuova aggiunta lì dentro è protetta per costruzione
  · ogni lettura passa da lib/dati.ts, dove il filtro sul
    proprietario è dentro la query
  · tag gerarchici: ['ordini'] e [`ordine-${id}`]
  · Suspense intorno alle sezioni lente e NON critiche; mai intorno
    all'elemento LCP
  · i filtri stanno nell'URL: condivisibili, e il tasto indietro
    funziona
```

```tsx
// app/(autenticato)/layout.tsx — la protezione per costruzione
import { richiediUtente } from '@/lib/autenticazione'

export default async function LayoutAutenticato({ children }: { children: React.ReactNode }) {
  // Reindirizza se non autenticato: vale per OGNI rotta del gruppo,
  // comprese quelle che qualcuno aggiungerà fra sei mesi
  const utente = await richiediUtente()

  return (
    <div className="cruscotto">
      {/* Solo i dati che servono attraversano il confine (B1) */}
      <BarraLaterale nome={utente.nome} ruoli={utente.ruoli} />
      <main>{children}</main>
    </div>
  )
}
```

```
# LA VERIFICA, IN ORDINE
# 1. IL BUNDLE  `next build` mostra il peso per rotta: il primo
#    caricamento condiviso deve stare sotto i ~100 kB
# 2. LE ROTTE STATICHE E DINAMICHE  `next build` le marca: una che
#    doveva essere statica e non lo è ha un `cookies()` di troppo
# 3. NESSUN WATERFALL  attiva il log delle query: le richieste
#    indipendenti devono partire insieme
# 4. FUNZIONA SENZA JAVASCRIPT  disattivalo: i form con
#    `<form action>` devono ancora inviare
# 5. AUTORIZZAZIONE  chiama ogni Server Action senza sessione e con
#    l'utente sbagliato: devono fallire tutte
# 6. IL PAYLOAD  cerca `passwordHash`, token ed email altrui nel
#    payload RSC: zero risultati
# 7. INVALIDAZIONE  crea un ordine: l'elenco si aggiorna senza
#    ricaricare a mano
# 8. GLI ERRORI  forza un errore in una sezione: solo quella mostra
#    il confine d'errore (`error.tsx`), il resto resta usabile —
#    e `error.digest` compare anche nei log del server
```

---
# Parte D — Approfondimento per Esperti

---

## D1. Testare i Server Component

```
IL PROBLEMA: un Server Component `async` non è renderizzabile da
Testing Library, che non sa gestire una Promise come componente. Il
supporto è in evoluzione, e la strategia che regge oggi è
differenziata per livello:
 1. LA LOGICA DI LETTURA si estrae in funzioni normali e si testa
    come tale — è dove sta la maggior parte dei bug
 2. I CLIENT COMPONENT con Testing Library, come sempre
 3. I SERVER COMPONENT end-to-end con Playwright: l'unico modo che
    verifica anche rendering sul server, streaming e idratazione
 4. LE SERVER ACTION come funzioni asincrone, con la sessione
    simulata al confine
```

```typescript
// 4. Le Server Action: si verifica il comportamento, autorizzazione
// compresa
import { describe, it, expect, vi } from 'vitest'
import { aggiornaProfilo } from '@/app/azioni/profilo'

describe('aggiornaProfilo', () => {
  it('rifiuta un campo non previsto invece di ignorarlo', async () => {
    vi.mocked(richiediUtente).mockResolvedValue({ id: 'u-1', ruoli: ['utente'] })

    const dati = new FormData()
    dati.set('nome', 'Mario')
    dati.set('ruolo', 'admin') // ← il tentativo di escalation

    const esito = await aggiornaProfilo({ esito: 'iniziale' }, dati)

    expect(esito.esito).toBe('errore')
    // ← LA VERIFICA CHE CONTA: il database non è stato toccato
    expect(vi.mocked(prisma.utente.update)).not.toHaveBeenCalled()
  })
})
```

```typescript
// 3. End-to-end: verifica lo streaming, che nessun test unitario vede
import { test, expect } from '@playwright/test'

test('la pagina mostra la parte veloce prima di quella lenta', async ({ page }) => {
  await page.goto('/ordini/ord_1')

  // L'intestazione è visibile mentre lo scheletro della spedizione
  // è ancora lì: è la prova che lo streaming funziona
  await expect(page.getByRole('heading', { name: /ORD-/ })).toBeVisible()
  await expect(page.getByTestId('scheletro-spedizione')).toBeVisible()

  await expect(page.getByTestId('stato-spedizione')).toBeVisible({ timeout: 5000 })
})
```

---
## D2. Migrare dal Pages Router

```
LA MIGRAZIONE È INCREMENTALE: `pages/` e `app/` convivono nello
stesso progetto, e `app/` ha la precedenza sulle rotte in conflitto.
L'ordine che funziona: abilitare `app/` senza spostare nulla →
migrare una rotta nuova o poco usata per imparare → poi quelle che
guadagnano di più dal minor JavaScript → per ultimo `_app` e
`_document`, che diventano `layout.tsx`.

LE CORRISPONDENZE
  getServerSideProps    → await dentro il componente
  getStaticProps        → await + `export const revalidate`
  getStaticPaths        → generateStaticParams()
  pages/api/*           → app/api/*/route.ts, oppure Server Action
  next/router           → next/navigation
  next/head             → export const metadata, o generateMetadata

⚠ LE QUATTRO TRAPPOLE
  1. `useRouter` di `next/navigation` HA UN'API DIVERSA: niente
     `query`, niente `pathname`. Importarlo dal posto sbagliato dà
     un errore a runtime, non a compilazione.
  2. I PROVIDER DI CONTESTO devono stare in un Client Component: un
     provider nel layout radice richiede un file separato con
     `'use client'` che avvolge `children`.
  3. LE LIBRERIE CHE NON DICHIARANO `'use client'` vanno avvolte in
     un proprio file client, o non funzionano.
  4. `searchParams` E `params` SONO PROMISE da Next 15: rompono
     silenziosamente il codice copiato da esempi più vecchi.
```

---

## D3. Sicurezza del confine

```
LA DOMANDA CHE SI FA A OGNI PROP: "questo dato lo mostrerei
all'utente se me lo chiedesse?" Se la risposta è no, non deve
attraversare il confine — anche se il componente non lo rende.

LE QUATTRO REGOLE
  1. `select` ESPLICITO nelle query, come in un'API. L'oggetto
     intero passato a un Client Component finisce nel payload.
  2. `import 'server-only'` nei moduli che non devono MAI finire
     nel bundle: se qualcuno li importa da un Client Component, la
     build fallisce invece di spedire il segreto.
  3. OGNI SERVER ACTION è un endpoint: autenticazione, autorizzazione
     e validazione, sempre.
  4. IL MIDDLEWARE NON BASTA (vedi B5): il controllo va dove si
     legge il dato.
```

```typescript
// lib/segreti.ts — se un Client Component importa questo file,
// `next build` fallisce con un errore chiaro invece di includere la
// chiave nel bundle. Il duale è `import 'client-only'`.
import 'server-only'

export const chiaveApiPagamenti = process.env['CHIAVE_PAGAMENTI']!
```

```
⚠ IL CASO CHE SORPRENDE DI PIÙ: un Server Component che passa
  `utente` a un Client Component per mostrarne il nome. Se `utente`
  viene da `findUnique` senza `select`, il payload contiene
  `passwordHash`, il segreto TOTP e le note interne — visibili
  guardando la risposta di rete. Il componente non li rende, ma ci sono.
```

---

## D4. Debug del payload e delle cache

```powershell
# Il payload RSC di una rotta, con l'header che Next usa per le
# navigazioni interne. In DevTools → Network le richieste con
# `?_rsc=` sono le stesse: nel loro corpo si cerca ciò che non
# dovrebbe esserci.
curl -H "RSC: 1" https://esempio.it/ordini
```

```
LE CINQUE DOMANDE QUANDO "LA CACHE NON FUNZIONA"
  1. QUALE livello? (B3) Router, Full Route, Data, o memoization?
  2. La rotta è statica o dinamica? `next build` lo dice: un
     `cookies()` in profondità la rende dinamica.
  3. La `fetch` ha `cache` o `revalidate` espliciti?
  4. `revalidateTag` usa lo STESSO tag della fetch? Un refuso non
     dà errore: semplicemente non invalida niente.
  5. La ROUTER CACHE del browser: `router.refresh()` la azzera.

⚠ E IL SINTOMO PIÙ FUORVIANTE: "funziona in sviluppo e non in
  produzione". In sviluppo la Full Route Cache è disattivata, quindi
  ogni pagina è dinamica: i problemi di cache si vedono SOLO con
  `next build && next start`.
```

```typescript
// next.config.ts — il logging delle fetch in sviluppo dice cosa è
// stato memorizzato e cosa no: il modo più rapido di capire un
// comportamento inatteso
export default { logging: { fetches: { fullUrl: true } } }
```

---

## D5. Quando NON servono i Server Component

```
RSC AGGIUNGE UN MODELLO MENTALE IN PIÙ: due tipi di componenti, un
confine con regole, quattro livelli di cache, e un insieme di
messaggi d'errore nuovi. È un costo reale.

NON SERVONO QUANDO
  ❌ l'applicazione è dietro autenticazione, interamente interattiva,
     e il SEO non conta (un editor, un cruscotto in tempo reale, uno
     strumento interno): una SPA classica è più semplice
  ❌ nessuno nel team può spiegare il confine: il costo si paga in
     bug sottili — dati sensibili nel payload, waterfall invisibili,
     cache che non si invalida
  ❌ serve comunque un backend separato per altri client: RSC non
     sostituisce l'API, e mantenere entrambi costa

SERVONO DAVVERO QUANDO
  ✅ il contenuto è pubblico e il SEO conta
  ✅ il bundle è grande per librerie usate solo a produrre l'output
  ✅ molte pagine leggono dati e ne mostrano pochi: il rapporto fra
     dati letti e dati mostrati è dove RSC guadagna di più
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
RSC E SERVER-DRIVEN UI — Mappa dei concetti

IL MODELLO
├── Server Component = il predefinito: async, accede a database e
│     segreti, e il suo codice NON arriva mai al client
├── Client Component = 'use client': stato, effetti, eventi, API
│     del browser
├── il confine è MONODIREZIONALE: un client component riceve un
│     server component come `children`, non lo importa
├── 'use client' marca un PUNTO DI INGRESSO: tutto ciò che quel file
│     importa entra nel bundle → si sposta il più IN BASSO possibile
└── RSC ≠ SSR: con SSR il codice arriva comunque al client

DATI
├── il recupero avviene nel componente che li usa
├── `cache()` deduplica dentro una richiesta
├── richieste indipendenti in Promise.all, non in sequenza
├── il WATERFALL è la causa principale di lentezza, e non si vede
│     leggendo il codice: si evita col preload o passando le Promise
└── le prop attraversano il confine e finiscono nel PAYLOAD

SERVER ACTION
├── sono ENDPOINT HTTP PUBBLICI: validare, autenticare, autorizzare
├── l'identità viene dalla SESSIONE, mai dal form
├── schema `.strict()` contro il mass assignment
├── revalidatePath o revalidateTag dopo ogni mutazione
└── con `<form action>` funzionano anche senza JavaScript

STREAMING E CACHE
├── Suspense intorno a ciò che è lento e NON critico; mai sull'LCP
├── un await nel PADRE blocca tutto, anche con i figli in Suspense
├── quattro livelli: router · full route · data · memoization —
│     confonderli è l'origine del 90% dei problemi di cache
├── i tag gerarchici sono più robusti dei percorsi
└── in sviluppo la Full Route Cache è spenta: i problemi si vedono
      solo con build && start

SICUREZZA E SCELTA
├── `select` esplicito: il payload è visibile al client
├── `import 'server-only'` fa fallire la build invece di spedire
│     un segreto
├── il middleware NON è un controllo di autorizzazione
└── statico + ISR per il contenuto pubblico · RSC dinamico per
      quello personalizzato · PPR per la pagina mista · e CSR va
      benissimo per un'app interattiva senza SEO
```

---
## Checklist di competenze

**Parte A — Basi**

- [ ] Sai spiegare le quattro attese che RSC elimina
- [ ] Decidi fra Server e Client Component con una regola, non a intuito
- [ ] Sposti il confine il più in basso possibile, e componi
      attraverso di esso col pattern `children`
- [ ] Sai quali prop attraversano il confine e quali no
- [ ] Usi `cache()` per deduplicare e `Promise.all` per parallelizzare
- [ ] Sai che una Server Action è un endpoint pubblico
- [ ] Scrivi un form che funziona anche senza JavaScript

**Parte B — Comprensione**

- [ ] Sai cosa contiene il payload RSC e perché è visibile al client
- [ ] Sai dove mettere i confini di Suspense, e dove non metterli
- [ ] Sai perché un `await` nel padre annulla lo streaming dei figli
- [ ] Distingui i quattro livelli di cache, e sai cosa rende dinamica
      una rotta senza volerlo
- [ ] Scegli fra `revalidatePath` e `revalidateTag` con una motivazione
- [ ] Sai perché il middleware non basta come autorizzazione
- [ ] Riconosci un waterfall e sai eliminarlo in due modi
- [ ] Sai quando il server-driven UI serve davvero, cosa aggiunge PPR
      e in cosa RSC differisce da SSR

**Parte C — Pratica**

- [ ] Hai ridotto un bundle spostando il confine e filtrando sul server
- [ ] Hai eliminato un waterfall con preload e Promise passate
- [ ] Hai chiuso i cinque buchi di una Server Action
- [ ] Hai verificato il payload cercando ciò che non dovrebbe esserci

**Parte D — Esperto**

- [ ] Conosci la strategia di test differenziata per livello
- [ ] Conosci le corrispondenze e le trappole della migrazione
- [ ] Usi `import 'server-only'` sui moduli con segreti
- [ ] Sai dire quando RSC non serve

---
## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| `'use client'` in cima alla pagina | Tutto l'albero e le sue librerie entrano nel bundle | Il confine il più in basso possibile |
| Recuperare i dati in `useEffect` | Quattro attese in fila prima del contenuto | `await` nel Server Component |
| Filtrare nel browser | Si scaricano diecimila record per mostrarne venti | Il filtro nella query, con un indice |
| Passare l'oggetto intero a un Client Component | Finisce nel payload, campi sensibili compresi | Solo i campi che servono |
| `await` nel padre con i figli in Suspense | Lo streaming non parte: blocca tutto | Il confine sopra il componente che aspetta |
| Suspense intorno all'elemento LCP | Uno scheletro dove serve il contenuto principale | Suspense su ciò che è lento e non critico |
| Server Action senza autenticazione | È un endpoint HTTP pubblico | Autenticare, autorizzare, validare |
| `utenteId` preso dal form | Si modifica il profilo di chiunque | L'identità dalla sessione |
| `Object.fromEntries(dati)` nel database | Mass assignment: `ruolo=admin` | Schema Zod `.strict()` |
| Nessuna invalidazione dopo una mutazione | L'interfaccia mostra dati vecchi | `revalidateTag` con tag gerarchici |
| Segreti in un modulo importabile dal client | Finiscono nel bundle | `import 'server-only'` |
| Testare la cache solo in sviluppo | La Full Route Cache è spenta: i problemi non si vedono | `next build && next start` |
| Server-driven UI dove client e server si rilasciano insieme | Complessità senza beneficio | JSX in un Server Component |

---

## Troubleshooting rapido

**"You're importing a component that needs useState"**
- Causa: un hook in un Server Component, o una libreria che non dichiara `'use client'`
- Fix: `'use client'` sul file giusto, o avvolgere la libreria in un proprio file client

**"Functions cannot be passed directly to Client Components"**
- Causa: si passa una funzione attraverso il confine
- Fix: una Server Action (che è serializzabile), o definire la funzione nel Client Component

**La pagina è lenta ma le query sono veloci**
- Causa: waterfall — i componenti aspettano uno dopo l'altro
- Fix: preload, o passare le Promise dall'alto e consumarle con `use`

**Lo streaming non funziona: la pagina appare tutta insieme**
- Causa: un `await` nel componente padre, o un proxy che bufferizza la risposta
- Fix: spostare il confine di Suspense sopra chi aspetta; verificare il proxy

**I dati non si aggiornano dopo una Server Action**
- Causa: manca `revalidatePath`/`revalidateTag`, o il tag non corrisponde
- Fix: verificare che il tag sia identico a quello della fetch; `router.refresh()` per la router cache

**Una pagina che doveva essere statica è dinamica**
- Causa: `cookies()`, `headers()` o `searchParams` usati in profondità
- Fix: `next build` marca il tipo di ogni rotta; isolare la parte dinamica in Suspense (PPR)

**Dati sensibili visibili nella risposta di rete**
- Causa: un oggetto passato interamente a un Client Component
- Fix: `select` nella query e solo i campi necessari come prop

---
## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_25_nextjs.md` | App Router, routing, metadata e deploy in profondità |
| `tutorial_17_performance_web.md` | Cosa guadagnano LCP e INP con meno JavaScript e lo streaming |
| `tutorial_13_autenticazione_autorizzazione.md` | Sessioni e permessi, che qui si applicano nel layout e nelle azioni |
| `tutorial_12_database_web.md` | Le query che i Server Component eseguono, e i loro indici |
| `tutorial_15_testing_web.md` | La strategia di test per componenti che girano sul server |
| `tutorial_11_api_design.md` | Cosa resta di un'API quando il client la chiama dal server |

---

## Risorse di riferimento

**Documentazione:** [React — Server Components](https://react.dev/reference/rsc/server-components) e [Server Functions](https://react.dev/reference/rsc/server-functions) · [Next.js — App Router](https://nextjs.org/docs/app), in particolare *Data Fetching*, *Caching* e *Rendering*

**Approfondimenti:** [RFC dei React Server Components](https://github.com/reactjs/rfcs/blob/main/text/0188-server-components.md), che spiega il perché prima del come · [Next.js — Caching](https://nextjs.org/docs/app/building-your-application/caching), da leggere per intero prima di combattere con l'invalidazione · [Server Actions Security](https://nextjs.org/blog/security-nextjs-server-components-actions)

**Strumenti:** [@next/bundle-analyzer](https://www.npmjs.com/package/@next/bundle-analyzer) per vedere cosa attraversa il confine · [React DevTools](https://react.dev/learn/react-developer-tools), che distingue Server e Client Component · [Playwright](https://playwright.dev/) per testare streaming e idratazione

---

> **Fine del Tutorial 21 — React Server Components e Server-Driven UI**
>
> Prossimo tutorial: `tutorial_22_rate_limiting_edge.md`
