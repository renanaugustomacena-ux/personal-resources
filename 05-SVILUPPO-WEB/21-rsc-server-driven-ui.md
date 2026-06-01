---
corso: "Sviluppo Web Full-Stack"
fase: "7 — Architetture Avanzate"
modulo: 21
titolo: "React Server Components — Server-Driven UI"
versione: "React 19 / Next.js 15"
livello: "Avanzato"
prerequisiti: ["07-react", "25-nextjs-guida-completa"]
obiettivi:
  - "Comprendere l'architettura RSC e il confine server → client"
  - "Usare 'use client' e 'use server' in modo consapevole"
  - "Implementare streaming progressivo con Suspense boundaries"
  - "Progettare Server Actions per mutazioni senza API manuali"
  - "Applicare Partial Prerendering (PPR) per shell statica + dinamica"
tag: [react, rsc, server-components, next.js, streaming, suspense, ppr]
---

# React Server Components — Server-Driven UI

> **Modulo 21 (NEW)** · **Aggiornamento:** 2026-05-24 · **Versione:** React 19, Next.js 15

> **Obiettivi di apprendimento**
>
> 1. Comprendere l'architettura RSC e il confine server → client
> 2. Usare `'use client'` e `'use server'` in modo consapevole
> 3. Implementare streaming progressivo con Suspense boundaries
> 4. Progettare Server Actions per mutazioni senza API manuali
> 5. Applicare Partial Prerendering (PPR) per shell statica + dinamica
>
> **Prerequisiti:** [React](07-react.md), [Next.js](25-nextjs-guida-completa.md)
> **Tempo stimato:** 6-8 ore · **Livello:** Avanzato

## Idee guida

1. **RSC: rendering on server, zero JS inviato al client.** I Server Components sono il default nel Next.js App Router — il client riceve HTML statico e un payload RSC serializzato, non bundle JavaScript.
2. **`'use client'` è opt-in.** Solo i componenti che richiedono interattività (state, effetti, event handler del browser) devono dichiararsi client component. Tutto il resto resta server.
3. **Streaming + Suspense boundaries = UI progressiva.** Il server invia HTML in chunk: la shell appare subito, i contenuti costosi arrivano progressivamente senza bloccare il rendering iniziale.
4. **Server Actions: form submit + mutazioni + revalidation senza API endpoint manuale.** Una funzione `'use server'` è invocabile direttamente da un form o da codice client — Next.js gestisce serializzazione, CSRF, e revalidation automatica.
5. **`use cache` (Next.js 15) per data-fetching ottimizzato.** `fetch()` non è più cachato di default (breaking change da Next.js 14): il caching è opt-in tramite la direttiva `'use cache'` o le opzioni esplicite di `fetch`.
6. **Partial Prerendering (PPR) combina statico e dinamico nella stessa route.** La shell statica viene servita dalla CDN edge, i buchi dinamici si riempiono via streaming.

---

## Indice

1. [Architettura RSC](#architettura-rsc)
2. [Server Components in dettaglio](#server-components-in-dettaglio)
3. [Client Components](#client-components)
4. [Composizione: il confine server → client](#composizione-il-confine-server--client)
5. [Next.js App Router](#nextjs-app-router)
6. [Server Actions](#server-actions)
7. [Caching](#caching)
8. [Streaming e Suspense](#streaming-e-suspense)
9. [Data Fetching Patterns](#data-fetching-patterns)
10. [Server-Driven UI Patterns](#server-driven-ui-patterns)
11. [Autenticazione con RSC](#autenticazione-con-rsc)
12. [Performance](#performance)
13. [Partial Prerendering (PPR)](#partial-prerendering-ppr)
14. [Migrazione: Pages Router → App Router](#migrazione-pages-router--app-router)
15. [Testing RSC](#testing-rsc)
16. [Confronto: RSC vs SSR vs SSG vs ISR vs CSR](#confronto-rsc-vs-ssr-vs-ssg-vs-isr-vs-csr)
17. [Pattern comuni](#pattern-comuni)
18. [Troubleshooting](#troubleshooting)
19. [FAQ](#faq)
20. [Best Practices e Anti-Pattern](#best-practices-e-anti-pattern)
21. [Esercizi](#esercizi)
22. [Letture](#letture)
23. [Glossario](#glossario)

---

## Architettura RSC

### Il modello mentale

React Server Components introduce un cambio architetturale fondamentale rispetto al modello tradizionale React. Storicamente, React funzionava esclusivamente sul client: il browser scaricava l'intero bundle JavaScript, lo eseguiva, generava il Virtual DOM e lo iniettava nel DOM reale. Con SSR classico il server pre-renderizzava l'HTML, ma il browser doveva comunque scaricare ed eseguire tutto il JavaScript per l'hydration.

RSC cambia questa equazione. I Server Components vengono eseguiti **esclusivamente** sul server. Il loro output non è HTML grezzo, ma un formato di serializzazione intermedio chiamato **RSC Payload** — un protocollo streaming basato su righe che descrive l'albero dei componenti in modo che React lato client possa ricostruire il Virtual DOM senza rieseguire il codice dei Server Components.

Il flusso è il seguente:

1. Il browser invia una richiesta HTTP.
2. Il server esegue l'albero dei componenti partendo dalla root.
3. I Server Components vengono risolti completamente sul server — le loro `async` function terminano, i dati vengono fetchati, il JSX viene prodotto.
4. Quando il server incontra un Client Component (marcato con `'use client'`), non lo esegue: inserisce nel payload un **riferimento** (placeholder) che dice "qui va il componente X con queste props serializzate".
5. Il payload RSC viene inviato al browser, potenzialmente in streaming.
6. React lato client riceve il payload, ricostruisce il Virtual DOM, e per i Client Components scarica il bundle JavaScript corrispondente e li hydrata.

### RSC Payload: anatomia

Il RSC Payload è un formato wire proprietario di React. Non è JSON, non è HTML — è un protocollo line-based ottimizzato per lo streaming. Ogni riga rappresenta un'istruzione:

```
0:["$","div",null,{"children":[["$","h1",null,{"children":"Benvenuto"}],...]}]
1:["$","$L2",null,{"count":0}]
2:I["./Counter.js","Counter"]
```

- Le righe con `$` descrivono elementi JSX risolti (Server Components già eseguiti).
- Le righe con `$L` sono riferimenti a **Client Components** — contengono l'ID del modulo e le props serializzate.
- Le righe con `I` sono istruzioni per importare i moduli Client Component.

Questa struttura permette a React di:
- Ricostruire l'albero dei componenti senza rieseguire il codice server.
- Effettuare il merge con lo stato client esistente senza perdere lo state dei Client Components.
- Supportare aggiornamenti incrementali (navigazione client-side) senza full page reload.

### Server vs Client: regola d'oro

```
┌─────────────────────────────────────────────────┐
│                   SERVER                         │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ Server Comp. │  │ Server Comp. │              │
│  │ (async data) │  │ (layout)     │              │
│  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                      │
│         ▼                 ▼                      │
│  ┌──────────────────────────────┐                │
│  │      RSC Payload             │                │
│  │  (serialized tree + refs)    │                │
│  └──────────────┬───────────────┘                │
│                 │                                │
├─────────────────┼────────────────────────────────┤
│                 │         CLIENT                 │
│                 ▼                                │
│  ┌──────────────────────────────┐                │
│  │  React Runtime (client)      │                │
│  │  + hydrated Client Comps     │                │
│  └──────────────────────────────┘                │
└─────────────────────────────────────────────────┘
```

La regola è semplice: **tutto è Server Component per default**. Si passa a Client Component solo quando serve interattività (state, effetti, API del browser). Questa inversione del default è il cuore di RSC.

---

## Server Components in dettaglio

### Caratteristiche fondamentali

I Server Components hanno proprietà uniche che li distinguono radicalmente dai componenti React tradizionali.

**Zero JavaScript inviato al client.** Il codice di un Server Component non viene mai incluso nel bundle client. Se un Server Component importa una libreria da 500 KB per processare dati (ad esempio `marked` per parsare Markdown), quei 500 KB restano sul server. Il client riceve solo l'HTML risultante.

**Accesso diretto al backend.** Un Server Component può accedere direttamente al database, al filesystem, a servizi interni, a variabili d'ambiente server-side. Non serve un'API intermediaria.

```tsx
// app/articles/[slug]/page.tsx — Server Component (default)
import { db } from '@/lib/database';
import { readFile } from 'node:fs/promises';
import { compileMDX } from 'next-mdx-remote/rsc';

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  // Accesso diretto al database — nessuna API necessaria
  const article = await db.article.findUniqueOrThrow({
    where: { slug },
    include: { author: true, tags: true },
  });

  // Lettura filesystem — impossibile in un Client Component
  const mdxSource = await readFile(
    `./content/${slug}.mdx`,
    'utf-8'
  );
  const { content } = await compileMDX({ source: mdxSource });

  return (
    <article>
      <h1>{article.title}</h1>
      <p>Di {article.author.name}</p>
      <div>{content}</div>
    </article>
  );
}
```

**Async/await nativo.** I Server Components possono essere funzioni `async`. Il rendering è sospeso fino alla risoluzione delle Promise. Questo elimina la necessità di `useEffect` + `useState` per il data fetching — il pattern più comune e più fragile di React tradizionale.

**Automatic code splitting.** Quando un Server Component importa dinamicamente un Client Component, Next.js crea automaticamente un code split point. Non serve `React.lazy()` manuale — ogni Client Component viene caricato solo quando necessario.

### Cosa NON possono fare i Server Components

I Server Components hanno limitazioni precise perché vengono eseguiti in un ambiente senza browser:

- **No state:** `useState`, `useReducer` non sono disponibili.
- **No effetti:** `useEffect`, `useLayoutEffect` non esistono sul server.
- **No event handler del browser:** `onClick`, `onChange`, `onSubmit` sono API del browser.
- **No API del browser:** `window`, `document`, `localStorage`, `navigator` non esistono.
- **No context consumer con state:** `useContext` non è disponibile (il context è un meccanismo client-side in React 19).
- **No ref:** `useRef` non è disponibile.

Se serve una qualsiasi di queste funzionalità, il componente deve diventare un Client Component.

### Server-only modules

Per prevenire l'inclusione accidentale di codice server-only nel bundle client, React fornisce il pacchetto `server-only`:

```bash
npm install server-only
```

```tsx
// lib/database.ts
import 'server-only';
import { PrismaClient } from '@prisma/client';

export const db = new PrismaClient();
```

Se un Client Component prova a importare questo modulo, il build fallisce con un errore esplicito. Questo è un meccanismo di protezione critico: senza `server-only`, un `import` accidentale potrebbe esporre credenziali del database o logica server nel bundle client.

Il corrispettivo esiste per codice client-only:

```bash
npm install client-only
```

```tsx
// lib/analytics.ts
import 'client-only';

export function trackEvent(name: string) {
  window.gtag('event', name); // richiede window
}
```

---

## Client Components

### La direttiva `'use client'`

La direttiva `'use client'` in cima a un file marca quel modulo e tutti i suoi import come **Client Components**. Non è un commento — è una direttiva del compilatore che definisce un confine di serializzazione.

```tsx
'use client';

import { useState, useTransition } from 'react';
import { updateProfile } from '@/actions/profile';

interface ProfileEditorProps {
  initialName: string;
  initialBio: string;
}

export function ProfileEditor({
  initialName,
  initialBio,
}: ProfileEditorProps) {
  const [name, setName] = useState(initialName);
  const [bio, setBio] = useState(initialBio);
  const [isPending, startTransition] = useTransition();

  async function handleSave() {
    startTransition(async () => {
      await updateProfile({ name, bio });
    });
  }

  return (
    <form action={handleSave}>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        disabled={isPending}
      />
      <textarea
        value={bio}
        onChange={(e) => setBio(e.target.value)}
        disabled={isPending}
      />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Salvataggio...' : 'Salva'}
      </button>
    </form>
  );
}
```

### Hydration

I Client Components vengono prima renderizzati come HTML sul server (SSR tradizionale), poi **idratati** sul client. L'hydration è il processo con cui React aggancia gli event handler e lo state al DOM pre-renderizzato. Durante l'hydration:

1. React scarica il bundle JavaScript del Client Component.
2. Esegue il componente lato client per generare il Virtual DOM.
3. Confronta il Virtual DOM con il DOM HTML dal server.
4. Se corrispondono, React "adotta" il DOM esistente e aggancia gli handler.
5. Se non corrispondono, React segnala un **hydration mismatch error** e tenta un recovery.

### Quando usare `'use client'`

Checklist decisionale:

| Necessità | Server Component | Client Component |
|-----------|:---:|:---:|
| Fetch dati dal database | ✅ | ❌ (serve API) |
| Accesso filesystem | ✅ | ❌ |
| useState / useReducer | ❌ | ✅ |
| useEffect | ❌ | ✅ |
| onClick / onChange / onSubmit | ❌ | ✅ |
| window / document / localStorage | ❌ | ✅ |
| Librerie pesanti solo per rendering | ✅ (zero JS al client) | ❌ (incluse nel bundle) |
| Dati sensibili (DB credentials) | ✅ | ❌ (mai) |
| Interattività real-time | ❌ | ✅ |
| Animazioni browser-side | ❌ | ✅ |

### Prerendering dei Client Components

Un aspetto che genera confusione: i Client Components **vengono comunque pre-renderizzati sul server** come HTML statico. La differenza è che il loro JavaScript viene anche inviato al client per l'hydration. Il termine "Client Component" non significa "renderizzato solo sul client" — significa "renderizzato su server E client, con hydration".

---

## Composizione: il confine server → client

### Il pattern fondamentale

Il confine tra Server e Client Components è il punto architetturale più importante di RSC. La regola base è che un **Server Component può importare e renderizzare un Client Component**, ma un **Client Component non può importare un Server Component**.

```tsx
// app/dashboard/page.tsx — Server Component
import { db } from '@/lib/database';
import { DashboardChart } from '@/components/DashboardChart'; // 'use client'
import { DashboardTable } from '@/components/DashboardTable'; // 'use client'

export default async function DashboardPage() {
  const metrics = await db.metrics.findMany({
    where: { period: 'last_30_days' },
    orderBy: { date: 'asc' },
  });

  const serializedMetrics = metrics.map((m) => ({
    date: m.date.toISOString(),
    value: m.value,
    label: m.label,
  }));

  return (
    <div>
      <h1>Dashboard</h1>
      {/* Server Component passa dati serializzabili a Client Components */}
      <DashboardChart data={serializedMetrics} />
      <DashboardTable data={serializedMetrics} />
    </div>
  );
}
```

### Il pattern "children" (Server Component dentro Client Component)

Anche se un Client Component non può _importare_ un Server Component, può _riceverlo_ come `children` o prop. Questo è possibile perché i children vengono risolti dal componente parent (server-side) e passati come RSC Payload già serializzato.

```tsx
// components/InteractivePanel.tsx — Client Component
'use client';

import { useState } from 'react';
import type { ReactNode } from 'react';

interface InteractivePanelProps {
  title: string;
  children: ReactNode;
}

export function InteractivePanel({ title, children }: InteractivePanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="panel">
      <button onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? 'Chiudi' : 'Apri'} {title}
      </button>
      {isOpen && <div className="panel-content">{children}</div>}
    </div>
  );
}
```

```tsx
// app/products/page.tsx — Server Component
import { db } from '@/lib/database';
import { InteractivePanel } from '@/components/InteractivePanel';
import { ProductReviews } from './ProductReviews'; // Server Component

export default async function ProductsPage() {
  const products = await db.product.findMany();

  return (
    <InteractivePanel title="Prodotti">
      {/* Server Component come children di un Client Component — funziona */}
      <ProductReviews products={products} />
    </InteractivePanel>
  );
}
```

### Regole di serializzazione delle props

Le props passate da un Server Component a un Client Component devono essere **serializzabili**. Questo significa:

**Tipi ammessi:**
- Stringhe, numeri, booleani, null, undefined
- Array e oggetti plain (nesting ammesso)
- Date (serializzate come stringa ISO)
- Map, Set (React 19)
- TypedArray, ArrayBuffer
- FormData
- Elementi JSX (React elements) e Server Components pre-renderizzati
- Server Actions (funzioni `'use server'`)

**Tipi NON ammessi:**
- Funzioni (tranne Server Actions)
- Classi e istanze di classi
- Symbol
- Closures che catturano variabili non serializzabili
- Connessioni database, stream, handle di file

```tsx
// ❌ ERRORE: funzione non serializzabile
<ClientComponent onFilter={(item) => item.price > 100} />

// ✅ CORRETTO: passa il valore, la logica vive nel Client Component
<ClientComponent minPrice={100} />

// ✅ CORRETTO: Server Action è serializzabile
<ClientComponent onSave={saveAction} />
```

---

## Next.js App Router

### Struttura del file system

L'App Router di Next.js 15 utilizza una struttura basata su directory annidate all'interno di `app/`. Ogni directory rappresenta un segmento di route, e i file speciali all'interno della directory definiscono il comportamento della route.

```
app/
├── layout.tsx          # Root layout (obbligatorio)
├── page.tsx            # Homepage (/)
├── loading.tsx         # Loading UI per la root
├── error.tsx           # Error boundary per la root
├── not-found.tsx       # 404 personalizzato
├── global-error.tsx    # Error boundary globale
│
├── dashboard/
│   ├── layout.tsx      # Layout condiviso per /dashboard/*
│   ├── page.tsx        # /dashboard
│   ├── loading.tsx     # Loading UI per dashboard
│   │
│   ├── analytics/
│   │   └── page.tsx    # /dashboard/analytics
│   │
│   └── settings/
│       ├── page.tsx    # /dashboard/settings
│       └── error.tsx   # Error boundary per settings
│
├── blog/
│   ├── page.tsx        # /blog (lista articoli)
│   └── [slug]/
│       ├── page.tsx    # /blog/articolo-xyz
│       └── opengraph-image.tsx  # OG image dinamica
│
├── api/
│   └── webhooks/
│       └── route.ts    # API route /api/webhooks
│
└── (marketing)/        # Route group (non influisce sull'URL)
    ├── about/
    │   └── page.tsx    # /about
    └── pricing/
        └── page.tsx    # /pricing
```

### Layout e nesting

I layout sono componenti che avvolgono le pagine e persistono durante la navigazione. Un layout non viene ri-renderizzato quando l'utente naviga tra pagine che condividono lo stesso layout — lo state viene preservato.

```tsx
// app/layout.tsx — Root Layout (obbligatorio)
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: { template: '%s | MiaSaaS', default: 'MiaSaaS' },
  description: 'Piattaforma di gestione aziendale',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="it">
      <body className={inter.className}>
        <nav>{/* Navigazione globale */}</nav>
        <main>{children}</main>
        <footer>{/* Footer globale */}</footer>
      </body>
    </html>
  );
}
```

```tsx
// app/dashboard/layout.tsx — Layout annidato
import { Sidebar } from '@/components/Sidebar';
import { requireAuth } from '@/lib/auth';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await requireAuth(); // redirect se non autenticato

  return (
    <div className="dashboard-grid">
      <Sidebar user={user} />
      <section className="dashboard-content">{children}</section>
    </div>
  );
}
```

### Loading UI e Suspense

Il file `loading.tsx` crea automaticamente un Suspense boundary attorno alla pagina corrispondente:

```tsx
// app/dashboard/loading.tsx
export default function DashboardLoading() {
  return (
    <div className="dashboard-skeleton">
      <div className="skeleton-header" />
      <div className="skeleton-chart" />
      <div className="skeleton-table" />
    </div>
  );
}
```

Equivale a scrivere:

```tsx
<Suspense fallback={<DashboardLoading />}>
  <DashboardPage />
</Suspense>
```

### Error Boundaries

Il file `error.tsx` crea un Error Boundary React. Deve essere un Client Component perché gli Error Boundary usano state e lifecycle methods.

```tsx
// app/dashboard/error.tsx
'use client';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DashboardError({ error, reset }: ErrorProps) {
  return (
    <div role="alert">
      <h2>Errore nel dashboard</h2>
      <p>Si è verificato un problema nel caricamento dei dati.</p>
      {process.env.NODE_ENV === 'development' && (
        <pre>{error.message}</pre>
      )}
      <button onClick={reset}>Riprova</button>
    </div>
  );
}
```

### Parallel Routes

Le Parallel Routes permettono di renderizzare simultaneamente più pagine nella stessa vista. Si definiscono con la sintassi `@nomeslot`:

```
app/dashboard/
├── layout.tsx
├── page.tsx
├── @metrics/
│   ├── page.tsx       # Slot metrics
│   └── loading.tsx
├── @activity/
│   ├── page.tsx       # Slot activity
│   └── loading.tsx
└── @notifications/
    ├── page.tsx       # Slot notifications
    └── loading.tsx
```

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  metrics,
  activity,
  notifications,
}: {
  children: React.ReactNode;
  metrics: React.ReactNode;
  activity: React.ReactNode;
  notifications: React.ReactNode;
}) {
  return (
    <div className="dashboard-grid">
      <div className="main">{children}</div>
      <div className="sidebar-right">
        {metrics}
        {activity}
      </div>
      <div className="sidebar-bottom">{notifications}</div>
    </div>
  );
}
```

Ogni slot è un Suspense boundary indipendente: se `@metrics` è lento, `@activity` e `@notifications` vengono comunque mostrati immediatamente.

### Intercepting Routes

Le Intercepting Routes permettono di intercettare una navigazione e mostrare il contenuto in un contesto diverso (tipicamente un modale), mantenendo la possibilità di navigare alla route completa con un refresh o link diretto.

```
app/
├── feed/
│   ├── page.tsx                # Lista feed
│   └── (.)photo/[id]/          # Intercetta /photo/[id] (stessa directory)
│       └── page.tsx            # Mostra foto in modale
├── photo/
│   └── [id]/
│       └── page.tsx            # Pagina foto completa (hard navigation)
```

La convenzione usa prefissi per indicare la profondità di intercettazione:
- `(.)` — stesso livello
- `(..)` — un livello sopra
- `(..)(..)` — due livelli sopra
- `(...)` — dalla root `app`

---

## Server Actions

### Fondamenti

Le Server Actions sono funzioni asincrone eseguite sul server, invocabili direttamente dal client. Sono definite con la direttiva `'use server'` e possono essere usate come `action` di un `<form>`, invocate da event handler, o chiamate programmaticamente.

```tsx
// actions/posts.ts
'use server';

import { db } from '@/lib/database';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';

const PostSchema = z.object({
  title: z.string().min(3).max(200),
  content: z.string().min(10),
  categoryId: z.string().uuid(),
});

export async function createPost(prevState: unknown, formData: FormData) {
  const raw = {
    title: formData.get('title'),
    content: formData.get('content'),
    categoryId: formData.get('categoryId'),
  };

  const parsed = PostSchema.safeParse(raw);

  if (!parsed.success) {
    return {
      errors: parsed.error.flatten().fieldErrors,
      message: 'Validazione fallita',
    };
  }

  try {
    const post = await db.post.create({
      data: parsed.data,
    });

    revalidatePath('/posts');
    redirect(`/posts/${post.slug}`);
  } catch (error) {
    return {
      errors: {},
      message: 'Errore durante la creazione del post',
    };
  }
}
```

### Form con useActionState

React 19 introduce `useActionState` (precedentemente `useFormState`) per gestire lo stato del form legato a una Server Action:

```tsx
// components/PostForm.tsx
'use client';

import { useActionState } from 'react';
import { createPost } from '@/actions/posts';

export function PostForm() {
  const [state, formAction, isPending] = useActionState(
    createPost,
    { errors: {}, message: '' }
  );

  return (
    <form action={formAction}>
      <div>
        <label htmlFor="title">Titolo</label>
        <input id="title" name="title" required />
        {state.errors?.title && (
          <p className="error">{state.errors.title[0]}</p>
        )}
      </div>

      <div>
        <label htmlFor="content">Contenuto</label>
        <textarea id="content" name="content" required />
        {state.errors?.content && (
          <p className="error">{state.errors.content[0]}</p>
        )}
      </div>

      <button type="submit" disabled={isPending}>
        {isPending ? 'Pubblicazione...' : 'Pubblica'}
      </button>

      {state.message && <p className="feedback">{state.message}</p>}
    </form>
  );
}
```

### Il componente `next/form`

Next.js 15 introduce il componente `<Form>` da `next/form` che estende il form HTML nativo con funzionalità di prefetching e navigazione client-side:

```tsx
import Form from 'next/form';

export function SearchForm() {
  return (
    <Form action="/search">
      <input name="q" placeholder="Cerca..." />
      <button type="submit">Cerca</button>
    </Form>
  );
}
```

Quando l'utente invia il form, Next.js naviga a `/search?q=valore` usando la navigazione client-side (senza full page reload), e prefetcha la route di destinazione al momento del render del form.

### Revalidation

Le Server Actions possono invalidare la cache in due modi:

```tsx
'use server';

import { revalidatePath } from 'next/cache';
import { revalidateTag } from 'next/cache';

export async function updateProduct(id: string, data: FormData) {
  await db.product.update({ where: { id }, data: { /* ... */ } });

  // Opzione 1: invalida una route specifica
  revalidatePath('/products');
  revalidatePath(`/products/${id}`);

  // Opzione 2: invalida per tag
  revalidateTag('products');
  revalidateTag(`product-${id}`);
}
```

### Optimistic Updates

Per aggiornamenti ottimistici React 19 fornisce `useOptimistic`:

```tsx
'use client';

import { useOptimistic } from 'react';
import { toggleLike } from '@/actions/likes';

interface Post {
  id: string;
  title: string;
  liked: boolean;
  likeCount: number;
}

export function PostCard({ post }: { post: Post }) {
  const [optimisticPost, setOptimisticPost] = useOptimistic(
    post,
    (current, newLiked: boolean) => ({
      ...current,
      liked: newLiked,
      likeCount: current.likeCount + (newLiked ? 1 : -1),
    })
  );

  async function handleToggleLike() {
    setOptimisticPost(!optimisticPost.liked);
    await toggleLike(post.id);
  }

  return (
    <div>
      <h3>{optimisticPost.title}</h3>
      <button onClick={handleToggleLike}>
        {optimisticPost.liked ? '❤️' : '🤍'} {optimisticPost.likeCount}
      </button>
    </div>
  );
}
```

### Sicurezza delle Server Actions

Le Server Actions espongono endpoint HTTP POST. Considerazioni di sicurezza:

1. **Validazione input:** Ogni Server Action deve validare i propri input con Zod o simile. Mai fidarsi di `FormData` non validato.
2. **Autenticazione:** Verificare sempre la sessione dell'utente all'interno della Server Action, non solo nel componente che la invoca.
3. **Autorizzazione:** Controllare che l'utente abbia i permessi per l'operazione richiesta.
4. **CSRF:** Next.js gestisce automaticamente la protezione CSRF per le Server Actions.
5. **Rate limiting:** Implementare rate limiting lato server per prevenire abusi.

```tsx
'use server';

import { auth } from '@/lib/auth';
import { rateLimit } from '@/lib/rate-limit';

export async function deleteComment(commentId: string) {
  // 1. Rate limiting
  const limiter = await rateLimit('delete-comment', 10, '1m');
  if (!limiter.success) {
    throw new Error('Troppe richieste. Riprova tra poco.');
  }

  // 2. Autenticazione
  const session = await auth();
  if (!session?.user) {
    throw new Error('Non autenticato');
  }

  // 3. Autorizzazione
  const comment = await db.comment.findUnique({ where: { id: commentId } });
  if (!comment || comment.authorId !== session.user.id) {
    throw new Error('Non autorizzato');
  }

  // 4. Validazione
  if (typeof commentId !== 'string' || !commentId.match(/^[a-z0-9-]+$/)) {
    throw new Error('ID non valido');
  }

  // 5. Operazione
  await db.comment.delete({ where: { id: commentId } });
  revalidatePath('/comments');
}
```

### Sicurezza avanzata delle Server Actions

Le Server Actions espongono endpoint HTTP POST pubblici. Senza contromisure, sono vulnerabili a CSRF, input malevolo e abuso automatizzato.

#### Protezione CSRF

Next.js confronta automaticamente gli header `Origin` e `Host` per bloccare richieste cross-origin. Dietro reverse proxy o CDN, l'header `Host` può differire dall'origine effettiva. In questi casi, configurare esplicitamente le origini consentite:

```ts
// next.config.ts
const nextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: [
        'app.example.com',
        '*.preview.example.com', // wildcard per deploy preview
      ],
    },
  },
};
```

Ogni Server Action riceve un **action ID cifrato** generato per build. Questo ID cambia ad ogni deploy, impedendo che un attaccante possa invocare direttamente l'endpoint conoscendo solo l'URL. Le variabili catturate nella closure vengono anch'esse cifrate nel payload — ma attenzione: non inserire mai segreti (API key, token) nella closure di una Server Action, perché il payload cifrato viaggia comunque nel markup HTML iniziale.

#### Validazione strutturata con Zod

Per dati annidati e upload di file, Zod offre validazione dichiarativa type-safe:

```ts
'use server';

import { z } from 'zod';

const ContactSchema = z.object({
  name: z.string().min(2).max(100),
  email: z.string().email(),
  message: z.string().min(10).max(5000),
  attachment: z
    .instanceof(File)
    .refine((f) => f.size <= 5 * 1024 * 1024, 'File troppo grande (max 5MB)')
    .refine(
      (f) => ['image/png', 'image/jpeg', 'application/pdf'].includes(f.type),
      'Tipo file non consentito'
    )
    .optional(),
  honeypot: z.string().max(0, 'Bot rilevato'), // campo invisibile
});

export async function submitContact(formData: FormData) {
  const raw = Object.fromEntries(formData);
  const parsed = ContactSchema.safeParse({
    ...raw,
    attachment: formData.get('attachment'),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  // Solo qui i dati sono validati e tipizzati
  await db.contact.create({ data: parsed.data });
  return { success: true };
}
```

Il campo `honeypot` è un input nascosto via CSS: i bot lo compilano, gli utenti no. Se contiene testo, la validazione Zod rifiuta la richiesta.

#### Rate limiting con Redis

Per proteggere le Server Actions da abuso automatizzato, implementare rate limiting lato server:

```ts
// lib/rate-limit.ts
import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_URL!,
  token: process.env.UPSTASH_REDIS_TOKEN!,
});

export async function rateLimit(
  identifier: string,
  maxRequests = 10,
  windowSeconds = 60
): Promise<{ allowed: boolean; remaining: number }> {
  const key = `rate:${identifier}`;
  const current = await redis.incr(key);

  if (current === 1) {
    await redis.expire(key, windowSeconds);
  }

  return {
    allowed: current <= maxRequests,
    remaining: Math.max(0, maxRequests - current),
  };
}
```

```ts
// utilizzo nella Server Action
'use server';

import { headers } from 'next/headers';
import { rateLimit } from '@/lib/rate-limit';

export async function submitForm(formData: FormData) {
  const headersList = await headers();
  const ip = headersList.get('x-forwarded-for') ?? 'unknown';
  const { allowed, remaining } = await rateLimit(ip, 5, 60);

  if (!allowed) {
    return { error: 'Troppe richieste. Riprova tra un minuto.' };
  }

  // ... logica protetta
}
```

La combinazione di CSRF automatico, Zod validation, honeypot e rate limiting fornisce difesa in profondità: ogni livello blocca una classe diversa di attacco.

---

## Caching

### Panoramica del sistema di caching in Next.js 15

Next.js 15 ha introdotto un cambiamento fondamentale rispetto a Next.js 14: **`fetch()` non è più cachato di default**. In Next.js 14, tutte le richieste `fetch` venivano automaticamente cachate (equivalente a `{ cache: 'force-cache' }`). In Next.js 15, il default è `{ cache: 'no-store' }` — nessun caching a meno che non venga richiesto esplicitamente.

Questo cambiamento è stato motivato dalla confusione che il caching implicito generava tra gli sviluppatori. Ora il caching è sempre opt-in ed esplicito.

### I quattro livelli di cache

```
┌─────────────────────────────────────────────────────┐
│  1. Request Memoization (React)                     │
│     Deduplica fetch identiche nella stessa request  │
├─────────────────────────────────────────────────────┤
│  2. Data Cache (Next.js)                            │
│     Persiste risposte fetch tra richieste           │
├─────────────────────────────────────────────────────┤
│  3. Full Route Cache (Next.js)                      │
│     Cache dell'HTML e RSC Payload per route statiche│
├─────────────────────────────────────────────────────┤
│  4. Router Cache (Client-side)                      │
│     Cache in-memory del browser per navigazione     │
└─────────────────────────────────────────────────────┘
```

### 1. Request Memoization

React deduplica automaticamente le richieste `fetch` con lo stesso URL e opzioni all'interno di un singolo render pass. Se tre Server Components nella stessa pagina fetchano lo stesso endpoint, la richiesta viene effettuata una sola volta.

```tsx
// Questo fetch viene eseguito UNA sola volta per request,
// anche se chiamato da più componenti nello stesso render.
async function getUser(id: string) {
  const res = await fetch(`https://api.example.com/users/${id}`);
  return res.json();
}

// Componente A
async function UserHeader({ userId }: { userId: string }) {
  const user = await getUser(userId); // fetch #1
  return <h1>{user.name}</h1>;
}

// Componente B (stessa pagina)
async function UserSidebar({ userId }: { userId: string }) {
  const user = await getUser(userId); // deduplicata, usa risultato di #1
  return <aside>{user.bio}</aside>;
}
```

La memoization si applica solo a `fetch` con metodo `GET` e dura solo per il singolo render pass (una singola richiesta HTTP al server Next.js).

### 2. Data Cache

Per attivare il caching persistente dei dati, si usano le opzioni di `fetch`:

```tsx
// Cache permanente (fino a revalidation esplicita)
const res = await fetch('https://api.example.com/products', {
  cache: 'force-cache',
});

// Cache con revalidazione time-based (ogni 3600 secondi)
const res = await fetch('https://api.example.com/products', {
  next: { revalidate: 3600 },
});

// Cache con tag per revalidazione on-demand
const res = await fetch('https://api.example.com/products', {
  cache: 'force-cache',
  next: { tags: ['products'] },
});
```

### 3. La direttiva `'use cache'`

Next.js 15 introduce la direttiva `'use cache'` come meccanismo di caching dichiarativo a livello di funzione, componente, o intero modulo:

```tsx
// Cache a livello di funzione
async function getCategories() {
  'use cache';
  return db.category.findMany({ orderBy: { name: 'asc' } });
}

// Cache a livello di componente
async function CategoriesNav() {
  'use cache';
  const categories = await db.category.findMany();
  return (
    <nav>
      {categories.map((c) => (
        <a key={c.id} href={`/category/${c.slug}`}>{c.name}</a>
      ))}
    </nav>
  );
}
```

Per controllare la durata della cache si usa `cacheLife`:

```tsx
import { cacheLife } from 'next/cache';

async function getPopularProducts() {
  'use cache';
  cacheLife('hours'); // predefinito: 'default' | 'seconds' | 'minutes' | 'hours' | 'days' | 'weeks' | 'max'
  return db.product.findMany({
    orderBy: { salesCount: 'desc' },
    take: 10,
  });
}
```

Per associare tag alla cache (per invalidazione on-demand):

```tsx
import { cacheTag } from 'next/cache';

async function getProduct(id: string) {
  'use cache';
  cacheTag(`product-${id}`, 'products');
  return db.product.findUnique({ where: { id } });
}
```

### Approfondimento `'use cache'`: le tre proprietà temporali

La direttiva `'use cache'` funziona attraverso un sistema di **profili temporali** governato da tre proprietà distinte, ciascuna con una semantica precisa che regola il ciclo di vita dei dati cachati.

**`stale`** — Durata in secondi durante la quale il client può utilizzare i dati in cache senza contattare il server. Finché il timer `stale` è attivo, ogni richiesta viene soddisfatta istantaneamente dalla cache locale. Questo è il periodo in cui i dati sono considerati "freschi" e non viene generata alcuna richiesta di rete.

**`revalidate`** — Trascorso il periodo `stale`, le successive richieste continuano a servire i dati cachati, ma innescano una **rigenerazione in background** (stale-while-revalidate). Il server produce una nuova versione dei dati che sostituirà la cache al completamento. L'utente non percepisce latenza perché continua a vedere la versione precedente.

**`expire`** — Tempo massimo assoluto di sopravvivenza della cache. Se nessuna richiesta arriva entro questo intervallo, l'entry viene eliminata. La prossima richiesta dovrà attendere la generazione fresca dei dati (blocking fetch). Questo previene l'accumulo infinito di entry mai più utilizzate.

```tsx
import { cacheLife } from 'next/cache';

async function getDashboardMetrics() {
  'use cache';
  // stale: 60s — il client serve dalla cache per 1 minuto
  // revalidate: 300s — dopo lo stale, rigenera in background ogni 5 min
  // expire: 3600s — dopo 1 ora senza richieste, elimina l'entry
  cacheLife({ stale: 60, revalidate: 300, expire: 3600 });

  return db.metric.aggregate({
    _sum: { revenue: true },
    _count: { orderId: true },
  });
}
```

#### Profili predefiniti

Next.js fornisce profili nominali che coprono gli scenari più comuni, evitando la necessità di specificare valori numerici ad ogni chiamata:

| Profilo | `stale` | `revalidate` | `expire` | Caso d'uso tipico |
|---------|---------|-------------|----------|--------------------|
| `'seconds'` | 0 | 1s | 60s | Dati quasi-realtime (prezzi, stock) |
| `'minutes'` | 300s (5 min) | 60s | 3600s | Feed, notifiche |
| `'hours'` | 3600s (1 h) | 900s (15 min) | 86400s (1 g) | Catalogo prodotti, articoli |
| `'days'` | 86400s (1 g) | 3600s (1 h) | 604800s (1 sett) | Contenuti editoriali |
| `'weeks'` | 604800s (1 sett) | 86400s (1 g) | 2592000s (30 g) | Pagine quasi-statiche |
| `'max'` | 2592000s (30 g) | 604800s (1 sett) | Indefinito | Risorse immutabili |

#### Profili personalizzati in `next.config.ts`

Per esigenze specifiche del progetto, si possono definire profili custom nella configurazione:

```ts
// next.config.ts
import type { NextConfig } from 'next';

const config: NextConfig = {
  cacheLife: {
    // Profilo custom per il blog aziendale
    blog: {
      stale: 3600,     // 1 ora di cache client
      revalidate: 900, // rigenera ogni 15 minuti
      expire: 86400,   // elimina dopo 1 giorno senza accessi
    },
    // Profilo per dati finanziari ad alta frequenza
    'financial-data': {
      stale: 0,        // mai stale — sempre verifica
      revalidate: 5,   // rigenera ogni 5 secondi
      expire: 60,      // elimina dopo 1 minuto
    },
    // Profilo per asset statici (immagini profilo, avatar)
    'user-assets': {
      stale: 604800,   // 1 settimana
      revalidate: 86400, // rigenera ogni giorno
      expire: 2592000, // 30 giorni
    },
  },
};

export default config;
```

Una volta definiti, i profili si usano per nome:

```tsx
async function getBlogPosts() {
  'use cache';
  cacheLife('blog');
  return db.post.findMany({ where: { published: true } });
}

async function getStockPrice(ticker: string) {
  'use cache';
  cacheLife('financial-data');
  cacheTag(`stock-${ticker}`);
  const res = await fetch(`https://api.finance.example.com/quote/${ticker}`);
  return res.json();
}
```

Le proprietà omesse in un profilo custom ereditano i valori dal profilo `default`. Questo vale anche per gli oggetti inline passati direttamente a `cacheLife()`.

#### `'use cache'` a livello di modulo

Quando la direttiva è posta all'inizio del file (prima di qualsiasi import), **tutte le funzioni esportate** dal modulo vengono cachate:

```tsx
// lib/catalog.ts
'use cache';

import { db } from './database';
import { cacheLife, cacheTag } from 'next/cache';

// Tutte le funzioni sono automaticamente cachate
export async function getCategories() {
  cacheLife('hours');
  cacheTag('categories');
  return db.category.findMany({ orderBy: { name: 'asc' } });
}

export async function getBrands() {
  cacheLife('days');
  cacheTag('brands');
  return db.brand.findMany({ where: { active: true } });
}
```

#### `cacheComponents` e la transizione da `dynamicIO`

In Next.js 15 il sistema `'use cache'` richiedeva il flag sperimentale `experimental.dynamicIO`. A partire da Next.js 16, questo flag è stato rinominato e stabilizzato come `cacheComponents: true` nella configurazione top-level. La migrazione è diretta:

```ts
// Next.js 15 (sperimentale)
const config = {
  experimental: {
    dynamicIO: true, // deprecato
  },
};

// Next.js 16+ (stabile)
const config = {
  cacheComponents: true, // successore stabilizzato
};
```

Con `cacheComponents` attivo, `'use cache'`, `cacheLife`, `cacheTag` e la funzione `updateTag` (successore di `revalidateTag` per contesti cache-aware) sono disponibili come API stabili. `unstable_cache`, il workaround adottato in Next.js 14/15 per memoizzare chiamate non-`fetch`, è formalmente deprecato a favore della direttiva `'use cache'`.

### 4. Full Route Cache

Le route statiche (senza dati dinamici) vengono pre-renderizzate a build time e servite dalla cache come HTML + RSC Payload. Questo è il comportamento di default per le route che non usano funzioni dinamiche.

**Funzioni che rendono una route dinamica:**
- `cookies()`, `headers()`, `searchParams`
- `fetch` senza caching
- `connection()` (Next.js 15)
- Route segment config: `export const dynamic = 'force-dynamic'`

### 5. Router Cache (Client-side)

Il browser mantiene una cache in-memory dei payload RSC per le route visitate. In Next.js 15 il default è cambiato:

- **Pagine dinamiche:** non vengono cachate nel Router Cache (default `0` secondi).
- **Pagine statiche:** cachate per 5 minuti.
- Il comportamento è configurabile con `staleTimes` in `next.config.ts`.

```ts
// next.config.ts
import type { NextConfig } from 'next';

const config: NextConfig = {
  experimental: {
    staleTimes: {
      dynamic: 30,  // secondi di cache per route dinamiche
      static: 300,  // secondi di cache per route statiche
    },
  },
};

export default config;
```

### Strategie di revalidazione

| Strategia | Quando usarla | Implementazione |
|-----------|---------------|-----------------|
| Time-based | Dati che cambiano periodicamente | `revalidate: 3600` in fetch o segment config |
| On-demand (path) | Dopo una mutazione su una route specifica | `revalidatePath('/products')` |
| On-demand (tag) | Dopo una mutazione che invalida un gruppo di dati | `revalidateTag('products')` |
| No cache | Dati sempre freschi (user-specific, real-time) | Default in Next.js 15 (no-store) |

---

## Streaming e Suspense

### Come funziona lo streaming

Lo streaming permette al server di inviare l'HTML in chunk progressivi. Invece di attendere che l'intera pagina sia pronta (blocking rendering), il server:

1. Invia immediatamente la shell della pagina (layout, navigazione, contenuti statici).
2. Per ogni Suspense boundary il cui contenuto non è ancora pronto, invia il fallback (skeleton/placeholder).
3. Quando un chunk di dati diventa disponibile, il server invia l'HTML corrispondente in un `<script>` inline che sostituisce il fallback.

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react';
import { DashboardHeader } from './DashboardHeader';
import { RevenueChart } from './RevenueChart';
import { RecentOrders } from './RecentOrders';
import { UserActivity } from './UserActivity';
import {
  ChartSkeleton,
  TableSkeleton,
  ActivitySkeleton,
} from './skeletons';

export default function DashboardPage() {
  return (
    <div>
      {/* Renderizzato immediatamente (nessun dato async) */}
      <DashboardHeader />

      <div className="grid grid-cols-2 gap-4">
        {/* Chunk 1: Revenue (potrebbe richiedere 200ms) */}
        <Suspense fallback={<ChartSkeleton />}>
          <RevenueChart />
        </Suspense>

        {/* Chunk 2: Ordini recenti (potrebbe richiedere 500ms) */}
        <Suspense fallback={<TableSkeleton />}>
          <RecentOrders />
        </Suspense>

        {/* Chunk 3: Attività utente (potrebbe richiedere 1s) */}
        <Suspense fallback={<ActivitySkeleton />}>
          <UserActivity />
        </Suspense>
      </div>
    </div>
  );
}
```

### Granularità dei Suspense boundaries

La granularità dei Suspense boundary influenza l'esperienza utente:

**Troppo grossolani** (un solo boundary per l'intera pagina): l'utente non vede nulla fino a quando il dato più lento è pronto. Vanifica lo streaming.

**Troppo granulari** (un boundary per ogni riga di una tabella): effetto "popcorn" — elementi che appaiono in ordine casuale, disorientando l'utente.

**Bilanciato** (un boundary per ogni sezione semantica): ogni area della pagina appare indipendentemente, in un ordine che ha senso per l'utente.

### Streaming SSR e progressive rendering

Il flusso completo di una pagina con streaming:

```
Browser                        Server
  │                              │
  │── GET /dashboard ──────────▶│
  │                              │ Inizia il rendering
  │                              │ Layout + shell pronti
  │◀── HTML chunk 1 (shell) ────│
  │    Mostra layout + skeletons │
  │                              │ RevenueChart pronto (200ms)
  │◀── HTML chunk 2 (revenue) ──│
  │    Sostituisce skeleton      │
  │                              │ RecentOrders pronto (500ms)
  │◀── HTML chunk 3 (orders) ───│
  │    Sostituisce skeleton      │
  │                              │ UserActivity pronto (1s)
  │◀── HTML chunk 4 (activity) ─│
  │    Sostituisce skeleton      │
  │                              │ Fine stream
```

---

## Data Fetching Patterns

### Fetch nei Server Components

Il pattern più semplice e raccomandato: i Server Components fetchano i dati direttamente.

```tsx
// app/products/page.tsx
import { db } from '@/lib/database';

export default async function ProductsPage() {
  const products = await db.product.findMany({
    where: { published: true },
    include: { category: true },
    orderBy: { createdAt: 'desc' },
    take: 20,
  });

  return (
    <ul>
      {products.map((p) => (
        <li key={p.id}>
          <h2>{p.name}</h2>
          <p>{p.category.name} — {p.price.toFixed(2)} €</p>
        </li>
      ))}
    </ul>
  );
}
```

### Parallel fetching

Quando una pagina ha bisogno di dati da fonti indipendenti, fetchare in parallelo evita il "waterfall" sequenziale:

```tsx
// app/dashboard/page.tsx
import { db } from '@/lib/database';

async function getMetrics() {
  return db.metric.aggregate({
    _sum: { revenue: true },
    _count: { orderId: true },
  });
}

async function getRecentOrders() {
  return db.order.findMany({
    orderBy: { createdAt: 'desc' },
    take: 10,
    include: { customer: true },
  });
}

async function getTopProducts() {
  return db.product.findMany({
    orderBy: { salesCount: 'desc' },
    take: 5,
  });
}

export default async function DashboardPage() {
  // Parallel fetching con Promise.all
  const [metrics, recentOrders, topProducts] = await Promise.all([
    getMetrics(),
    getRecentOrders(),
    getTopProducts(),
  ]);

  return (
    <div>
      <MetricsCards metrics={metrics} />
      <OrdersTable orders={recentOrders} />
      <TopProductsList products={topProducts} />
    </div>
  );
}
```

### Sequential fetching (quando necessario)

A volte un fetch dipende dal risultato di un altro:

```tsx
async function getArtist(id: string) {
  const res = await fetch(`https://api.spotify.com/v1/artists/${id}`);
  return res.json();
}

async function getAlbums(artistId: string) {
  const res = await fetch(
    `https://api.spotify.com/v1/artists/${artistId}/albums`
  );
  return res.json();
}

export default async function ArtistPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  // Sequenziale: albums dipende dall'artist ID validato
  const artist = await getArtist(id);
  const albums = await getAlbums(artist.id);

  return (
    <div>
      <h1>{artist.name}</h1>
      <AlbumGrid albums={albums} />
    </div>
  );
}
```

### Preloading pattern

Per iniziare un fetch prima che il componente che lo consuma venga renderizzato:

```tsx
// lib/data.ts
import { cache } from 'react';

export const getProduct = cache(async (id: string) => {
  const product = await db.product.findUnique({
    where: { id },
    include: { reviews: true, category: true },
  });
  return product;
});

// Funzione di preload — avvia il fetch senza attendere il risultato
export function preloadProduct(id: string) {
  void getProduct(id);
}
```

```tsx
// app/products/[id]/page.tsx
import { getProduct, preloadProduct } from '@/lib/data';
import { ProductDetails } from './ProductDetails';
import { RelatedProducts } from './RelatedProducts';

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  // Avvia preload immediatamente
  preloadProduct(id);

  // Il preload è già in corso — questa chiamata usa il risultato in cache
  const product = await getProduct(id);

  return (
    <div>
      <ProductDetails product={product} />
      <RelatedProducts categoryId={product.categoryId} />
    </div>
  );
}
```

---

## Server-Driven UI Patterns

### Configuration-driven rendering

Il server decide quali componenti renderizzare e con quali dati, basandosi su configurazioni memorizzate nel backend:

```tsx
// lib/ui-config.ts
import 'server-only';

interface UIBlock {
  type: 'hero' | 'productGrid' | 'testimonials' | 'cta' | 'faq';
  props: Record<string, unknown>;
}

export async function getPageConfig(pageSlug: string): Promise<UIBlock[]> {
  return db.pageConfig.findMany({
    where: { pageSlug },
    orderBy: { order: 'asc' },
  });
}
```

```tsx
// app/[slug]/page.tsx
import { getPageConfig } from '@/lib/ui-config';
import { HeroSection } from '@/components/HeroSection';
import { ProductGrid } from '@/components/ProductGrid';
import { Testimonials } from '@/components/Testimonials';
import { CTASection } from '@/components/CTASection';
import { FAQSection } from '@/components/FAQSection';

const BLOCK_REGISTRY: Record<string, React.ComponentType<any>> = {
  hero: HeroSection,
  productGrid: ProductGrid,
  testimonials: Testimonials,
  cta: CTASection,
  faq: FAQSection,
};

export default async function DynamicPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const blocks = await getPageConfig(slug);

  return (
    <main>
      {blocks.map((block, i) => {
        const Component = BLOCK_REGISTRY[block.type];
        if (!Component) return null;
        return <Component key={`${block.type}-${i}`} {...block.props} />;
      })}
    </main>
  );
}
```

### A/B Testing con RSC

Con RSC l'A/B testing è puramente server-side — nessun flash of content, nessun bundle extra:

```tsx
// app/pricing/page.tsx
import { cookies } from 'next/headers';
import { PricingTableA } from './PricingTableA';
import { PricingTableB } from './PricingTableB';

export default async function PricingPage() {
  const cookieStore = await cookies();
  let variant = cookieStore.get('ab-pricing')?.value;

  if (!variant) {
    variant = Math.random() > 0.5 ? 'A' : 'B';
    // Il cookie viene impostato nel middleware o nella response
  }

  // Il server decide quale variante servire — zero JS aggiuntivo
  return variant === 'A' ? <PricingTableA /> : <PricingTableB />;
}
```

### Feature Flags

```tsx
// lib/feature-flags.ts
import 'server-only';

interface FeatureFlags {
  newDashboard: boolean;
  darkModeDefault: boolean;
  betaSearch: boolean;
}

export async function getFeatureFlags(userId: string): Promise<FeatureFlags> {
  // Da un servizio di feature flags (LaunchDarkly, Unleash, database)
  const flags = await db.featureFlag.findMany({
    where: {
      OR: [
        { scope: 'global' },
        { scope: 'user', scopeId: userId },
      ],
    },
  });

  return Object.fromEntries(
    flags.map((f) => [f.key, f.enabled])
  ) as FeatureFlags;
}
```

```tsx
// app/dashboard/page.tsx
import { auth } from '@/lib/auth';
import { getFeatureFlags } from '@/lib/feature-flags';
import { DashboardV1 } from './DashboardV1';
import { DashboardV2 } from './DashboardV2';

export default async function DashboardPage() {
  const session = await auth();
  const flags = await getFeatureFlags(session.user.id);

  return flags.newDashboard ? <DashboardV2 /> : <DashboardV1 />;
}
```

---

## Autenticazione con RSC

### Server-side auth

Con RSC l'autenticazione viene verificata direttamente nel Server Component — nessun token esposto al client, nessun flash of unauthenticated content:

```tsx
// lib/auth.ts
import 'server-only';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { jwtVerify } from 'jose';

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET!
);

export async function auth() {
  const cookieStore = await cookies();
  const token = cookieStore.get('session-token')?.value;

  if (!token) return null;

  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);
    return {
      user: {
        id: payload.sub as string,
        email: payload.email as string,
        role: payload.role as string,
      },
    };
  } catch {
    return null;
  }
}

export async function requireAuth() {
  const session = await auth();
  if (!session) redirect('/login');
  return session;
}

export async function requireRole(role: string) {
  const session = await requireAuth();
  if (session.user.role !== role) redirect('/unauthorized');
  return session;
}
```

### Middleware per protezione route

```tsx
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';
import { jwtVerify } from 'jose';

const PROTECTED_PATHS = ['/dashboard', '/settings', '/admin'];
const ADMIN_PATHS = ['/admin'];

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET!
);

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED_PATHS.some((p) =>
    pathname.startsWith(p)
  );

  if (!isProtected) return NextResponse.next();

  const token = request.cookies.get('session-token')?.value;

  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);

    const isAdmin = ADMIN_PATHS.some((p) => pathname.startsWith(p));
    if (isAdmin && payload.role !== 'admin') {
      return NextResponse.redirect(new URL('/unauthorized', request.url));
    }

    return NextResponse.next();
  } catch {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }
}

export const config = {
  matcher: ['/dashboard/:path*', '/settings/:path*', '/admin/:path*'],
};
```

### Protected layout pattern

```tsx
// app/(protected)/layout.tsx
import { requireAuth } from '@/lib/auth';

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await requireAuth(); // redirect a /login se non autenticato

  return (
    <div>
      <header>
        <span>Benvenuto, {session.user.email}</span>
      </header>
      {children}
    </div>
  );
}
```

---

## Performance

### Comprendere il RSC Payload

Il RSC Payload è il principale costo di trasferimento in una applicazione RSC. La sua dimensione dipende da:

1. **Quantità di HTML renderizzato.** Più grande è l'output dei Server Components, più grande il payload.
2. **Props passate ai Client Components.** Ogni prop viene serializzata nel payload. Liste enormi passate come props aumentano la dimensione.
3. **Numero di Client Component references.** Ogni riferimento a un Client Component include il path del modulo.

**Ottimizzazione chiave:** minimizzare la quantità di dati passati come props ai Client Components.

```tsx
// ❌ ANTI-PATTERN: passa l'intero oggetto user con tutti i campi
<UserAvatar user={fullUserObject} />

// ✅ OTTIMIZZATO: passa solo i campi necessari
<UserAvatar name={user.name} avatarUrl={user.avatarUrl} />
```

### Bundle analysis

Per analizzare il bundle JavaScript:

```bash
# Installa il bundle analyzer
npm install @next/bundle-analyzer

# next.config.ts
import withBundleAnalyzer from '@next/bundle-analyzer';

const config = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
})({
  // ... next config
});

export default config;
```

```bash
ANALYZE=true npm run build
```

Questo genera un report interattivo che mostra quali moduli vengono inclusi nel bundle client. L'obiettivo è che i Server Components non compaiano nel report — se appaiono, c'è un problema di confine server/client.

### Ottimizzare il First Load

1. **Minimizzare i Client Components.** Ogni `'use client'` aggiunge JavaScript al bundle. Spostare la logica interattiva nel componente più piccolo possibile.

2. **Dynamic imports per componenti pesanti.**

```tsx
import dynamic from 'next/dynamic';

const HeavyEditor = dynamic(
  () => import('@/components/RichTextEditor'),
  {
    loading: () => <div className="editor-skeleton" />,
    ssr: false, // se il componente non supporta SSR
  }
);
```

3. **Eliminare le dipendenze server-only dal bundle client.** Usare `server-only` per ogni modulo che contiene logica server.

4. **Ottimizzare le immagini.**

```tsx
import Image from 'next/image';

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority // per immagini above the fold
  sizes="(max-width: 768px) 100vw, 1200px"
/>
```

5. **Font optimization con `next/font`.**

```tsx
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
});
```

---

## Partial Prerendering (PPR)

### Cos'è PPR

Partial Prerendering è la feature architetturale più significativa di Next.js 15. PPR combina rendering statico e dinamico nella stessa route, eliminando la necessità di scegliere tra l'una o l'altra modalità per l'intera pagina.

Con PPR:
- La **shell statica** (layout, navigazione, contenuti che non cambiano) viene pre-renderizzata a build time e servita dalla CDN edge.
- I **buchi dinamici** (contenuti user-specific, dati real-time) vengono risolti via streaming al momento della richiesta.

### Come funziona

```
Richiesta browser ──▶ CDN Edge
                       │
                       ▼
              Shell HTML statica (cache hit)
              + <Suspense> placeholders
                       │
                       ▼
              Browser mostra la shell istantaneamente
                       │
                       ▼ (in parallelo)
              Server risolve i buchi dinamici
              e li invia come chunk streaming
                       │
                       ▼
              Browser sostituisce i placeholders
              con il contenuto dinamico
```

### Abilitare PPR

```ts
// next.config.ts
import type { NextConfig } from 'next';

const config: NextConfig = {
  experimental: {
    ppr: true, // abilita PPR globalmente
  },
};

export default config;
```

In alternativa, si può abilitare per singola route:

```tsx
// app/dashboard/page.tsx
export const experimental_ppr = true;
```

### Esempio pratico

```tsx
// app/shop/page.tsx — PPR in azione
import { Suspense } from 'react';
import { StaticHero } from './StaticHero';
import { StaticCategoryNav } from './StaticCategoryNav';
import { PersonalizedRecommendations } from './PersonalizedRecommendations';
import { CartSummary } from './CartSummary';
import { RecommendationsSkeleton, CartSkeleton } from './skeletons';

export const experimental_ppr = true;

export default function ShopPage() {
  return (
    <div>
      {/* STATICO: pre-renderizzato, servito da CDN */}
      <StaticHero />
      <StaticCategoryNav />

      {/* DINAMICO: risolto al momento della richiesta */}
      <Suspense fallback={<RecommendationsSkeleton />}>
        <PersonalizedRecommendations />
      </Suspense>

      <Suspense fallback={<CartSkeleton />}>
        <CartSummary />
      </Suspense>
    </div>
  );
}
```

`PersonalizedRecommendations` legge i cookie dell'utente (`cookies()`) rendendo quel sottoalbero dinamico. Il resto della pagina è statico. PPR rileva automaticamente il confine e gestisce la separazione.

### Performance reali di PPR

Il vantaggio misurabile di PPR è nel **Time to First Byte (TTFB)**: la shell statica viene servita direttamente dalla CDN edge in meno di 100ms, indipendentemente dalla latenza del data layer. L'utente vede immediatamente la struttura della pagina con i placeholder di Suspense, mentre i sottoalberi dinamici arrivano progressivamente via streaming.

Metriche tipiche osservate in produzione:

| Metrica | Senza PPR (full SSR) | Con PPR |
|---------|---------------------|---------|
| TTFB | 200-800ms (dipende dal DB) | < 100ms (CDN edge) |
| FCP | 300-900ms | 100-200ms |
| LCP (contenuto statico) | 400-1000ms | 150-300ms |
| LCP (contenuto dinamico) | Uguale al TTFB + render | TTFB + streaming delay |

#### Configurazione per-route vs globale

PPR può essere abilitato globalmente o per singola route. La configurazione granulare è preferibile per adozione incrementale:

```ts
// next.config.ts — abilitazione globale
const nextConfig = {
  experimental: {
    ppr: true, // stabile in Next.js 16
  },
};

// Oppure per singola route:
// app/products/page.tsx
export const experimental_ppr = true;
```

Quando PPR è attivo, il confine statico/dinamico è determinato dai `<Suspense>` boundary. Tutto ciò che sta **sopra** un Suspense boundary con contenuto che non invoca funzioni dinamiche (`cookies()`, `headers()`, `searchParams`) diventa parte della shell statica pre-renderizzata. Tutto ciò che sta **dentro** un Suspense che chiama funzioni dinamiche viene streamato a runtime.

**Attenzione critica:** una singola chiamata a `cookies()` o `headers()` in un componente rende **l'intero sottoalbero** da quel punto in giù dinamico. Se il componente padre chiama `cookies()`, tutti i suoi figli sono dinamici, anche se non ne hanno bisogno. Per massimizzare la porzione statica, isolare le chiamate dinamiche nei componenti foglia più profondi possibile.

#### Interazione PPR e `'use cache'`

PPR e `'use cache'` sono complementari. PPR decide *come* servire la pagina (shell statica + streaming dinamico). `'use cache'` decide *quanto* durino i dati cachati nei sottoalberi dinamici. Un sottoalbero dinamico che usa `'use cache'` con un profilo `revalidate: 60` verrà streamato, ma i dati sottostanti saranno serviti dalla cache per 60 secondi prima di una nuova fetch.

```tsx
// Componente dinamico con cache dei dati
async function TrendingProducts() {
  const products = await getTrendingProducts(); // usa 'use cache' internamente
  return <ProductGrid products={products} />;
}

// La pagina usa PPR: shell statica + trending streamato
export default async function HomePage() {
  return (
    <main>
      <HeroSection />       {/* statico — nella shell */}
      <CategoryNav />       {/* statico — nella shell */}
      <Suspense fallback={<ProductGridSkeleton />}>
        <TrendingProducts /> {/* dinamico — streamato, dati cachati */}
      </Suspense>
    </main>
  );
}
```

---

## Migrazione: Pages Router → App Router

### Strategia incrementale

La migrazione da Pages Router (`pages/`) ad App Router (`app/`) non deve essere big-bang. Next.js supporta la coesistenza di entrambi i router. La strategia raccomandata è:

1. **Creare la directory `app/` senza rimuovere `pages/`.** Le due coesistono.
2. **Migrare il layout globale** (`_app.tsx`, `_document.tsx`) al `app/layout.tsx`.
3. **Migrare una route alla volta**, partendo dalle più semplici.
4. **Convertire `getServerSideProps`/`getStaticProps`** in fetch diretto nei Server Components.
5. **Spostare le API routes** da `pages/api/` a `app/api/route.ts` (opzionale — le API routes in `pages/api` continuano a funzionare).

### Mappatura dei concetti

| Pages Router | App Router |
|---|---|
| `pages/index.tsx` | `app/page.tsx` |
| `pages/about.tsx` | `app/about/page.tsx` |
| `pages/blog/[slug].tsx` | `app/blog/[slug]/page.tsx` |
| `pages/_app.tsx` | `app/layout.tsx` |
| `pages/_document.tsx` | `app/layout.tsx` (tag `<html>`, `<body>`) |
| `pages/404.tsx` | `app/not-found.tsx` |
| `pages/_error.tsx` | `app/error.tsx` + `app/global-error.tsx` |
| `pages/api/users.ts` | `app/api/users/route.ts` |
| `getServerSideProps` | `async` Server Component con fetch diretto |
| `getStaticProps` | `async` Server Component + `revalidate` config |
| `getStaticPaths` | `generateStaticParams` |

### Esempio di migrazione: pagina con `getServerSideProps`

**Prima (Pages Router):**

```tsx
// pages/products/[id].tsx
import type { GetServerSideProps } from 'next';

interface ProductPageProps {
  product: Product;
}

export const getServerSideProps: GetServerSideProps<ProductPageProps> = async (
  context
) => {
  const { id } = context.params!;
  const res = await fetch(`${process.env.API_URL}/products/${id}`);

  if (!res.ok) {
    return { notFound: true };
  }

  const product = await res.json();
  return { props: { product } };
};

export default function ProductPage({ product }: ProductPageProps) {
  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <span>{product.price} €</span>
    </div>
  );
}
```

**Dopo (App Router):**

```tsx
// app/products/[id]/page.tsx
import { notFound } from 'next/navigation';
import { db } from '@/lib/database';

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await db.product.findUnique({ where: { id } });

  if (!product) notFound();

  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <span>{product.price.toFixed(2)} €</span>
    </div>
  );
}
```

### Esempio: `getStaticProps` + `getStaticPaths`

**Prima:**

```tsx
// pages/blog/[slug].tsx
export const getStaticPaths: GetStaticPaths = async () => {
  const posts = await fetch(`${process.env.API_URL}/posts`).then((r) =>
    r.json()
  );
  return {
    paths: posts.map((p: Post) => ({ params: { slug: p.slug } })),
    fallback: 'blocking',
  };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const post = await fetch(
    `${process.env.API_URL}/posts/${params!.slug}`
  ).then((r) => r.json());
  return { props: { post }, revalidate: 3600 };
};
```

**Dopo:**

```tsx
// app/blog/[slug]/page.tsx
import { db } from '@/lib/database';
import { notFound } from 'next/navigation';

// Equivalente di getStaticPaths
export async function generateStaticParams() {
  const posts = await db.post.findMany({ select: { slug: true } });
  return posts.map((p) => ({ slug: p.slug }));
}

// Equivalente di revalidate: 3600
export const revalidate = 3600;

export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await db.post.findUnique({ where: { slug } });
  if (!post) notFound();

  return (
    <article>
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: post.contentHtml }} />
    </article>
  );
}
```

### Checklist di migrazione

- [ ] `app/layout.tsx` creato con `<html>`, `<body>`, metadata
- [ ] Provider globali (theme, auth) spostati nel layout
- [ ] Font migrati a `next/font`
- [ ] `_app.tsx` e `_document.tsx` rimossi dopo migrazione completa
- [ ] `getServerSideProps` convertiti in fetch diretto nel Server Component
- [ ] `getStaticProps` convertiti in Server Component + `revalidate`
- [ ] `getStaticPaths` convertiti in `generateStaticParams`
- [ ] `useRouter` (`next/router`) sostituito con `useRouter` (`next/navigation`)
- [ ] `<Link>` non richiede più `<a>` come child (App Router lo genera automaticamente)
- [ ] `next/head` sostituito con `export const metadata` o `generateMetadata`
- [ ] Middleware aggiornato per il nuovo formato (se necessario)
- [ ] API routes migrate (opzionale) a Route Handlers

### Errori comuni durante la migrazione

La coesistenza di `pages/` e `app/` introduce trappole non ovvie. Ecco le più frequenti:

**1. Conflitto di route.** Se `pages/about.tsx` e `app/about/page.tsx` esistono contemporaneamente, Next.js genera un errore di build. Non è possibile avere la stessa route in entrambi i router. Rinominare o rimuovere la versione in `pages/` prima di creare quella in `app/`.

**2. Import `useRouter` errato.** In Pages Router si importa da `next/router`. In App Router da `next/navigation`. I due moduli espongono API diverse: `next/navigation` non ha `query`, `asPath`, né `events`. I parametri di ricerca si leggono con l'hook `useSearchParams()` e i parametri di route con `useParams()`. L'errore più subdolo è importare il vecchio `useRouter` in un componente `'use client'` dentro `app/` — il codice compila ma fallisce a runtime.

**3. Da `next/head` a Metadata API.** Pages Router usa `<Head>` come componente. App Router usa `export const metadata` (statico) o `export async function generateMetadata()` (dinamico). Un errore frequente è dimenticare di rimuovere il componente `<Head>` dopo la migrazione, causando tag duplicati nell'HTML.

**4. Caching implicito rimosso.** In Next.js 14 con Pages Router, `fetch` era cachato di default. In Next.js 15 con App Router, il default è `no-store`. Le pagine migrate da `getStaticProps` che si aspettano caching automatico perderanno le performance se non si aggiunge esplicitamente `{ cache: 'force-cache' }` o `'use cache'`.

**5. Compatibilità librerie.** Librerie come Framer Motion, chart.js, o react-datepicker usano hook client-side e accedono al DOM. In App Router servono il wrapper `'use client'`. Creare un file barrel di re-export:

```tsx
// components/client-wrappers.tsx
'use client';

export { motion, AnimatePresence } from 'framer-motion';
export { Chart } from 'react-chartjs-2';
```

Questo isola la direttiva `'use client'` e mantiene i componenti padre come Server Components.

**6. Dev server più lento senza Turbopack.** App Router con Webpack è significativamente più lento in sviluppo rispetto a Pages Router. Usare `next dev --turbopack` migliora i tempi di avvio e hot reload. Turbopack è stabile in Next.js 15+ per lo sviluppo.

---

## Testing RSC

### Unit testing dei Server Components

I Server Components sono funzioni `async` che ritornano JSX. Si possono testare come funzioni normali usando il rendering sperimentale di React Testing Library:

```tsx
// __tests__/ProductCard.test.tsx
import { render, screen } from '@testing-library/react';
import ProductCard from '@/app/products/ProductCard';

// Mock del database
vi.mock('@/lib/database', () => ({
  db: {
    product: {
      findUnique: vi.fn().mockResolvedValue({
        id: '1',
        name: 'Laptop Pro',
        price: 1299.99,
        description: 'Un laptop potente',
      }),
    },
  },
}));

describe('ProductCard', () => {
  it('mostra il nome e il prezzo del prodotto', async () => {
    const component = await ProductCard({
      params: Promise.resolve({ id: '1' }),
    });

    render(component);

    expect(screen.getByText('Laptop Pro')).toBeInTheDocument();
    expect(screen.getByText(/1299\.99/)).toBeInTheDocument();
  });
});
```

### Testing delle Server Actions

```tsx
// __tests__/actions/createPost.test.ts
import { createPost } from '@/actions/posts';

vi.mock('@/lib/database', () => ({
  db: {
    post: {
      create: vi.fn().mockResolvedValue({
        id: '1',
        slug: 'test-post',
        title: 'Test Post',
      }),
    },
  },
}));

vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  redirect: vi.fn(),
}));

describe('createPost', () => {
  it('valida i dati del form', async () => {
    const formData = new FormData();
    formData.set('title', 'ab'); // troppo corto (min 3)
    formData.set('content', 'contenuto valido lungo abbastanza');
    formData.set('categoryId', 'not-a-uuid');

    const result = await createPost(null, formData);

    expect(result.errors).toBeDefined();
    expect(result.errors.title).toBeDefined();
    expect(result.errors.categoryId).toBeDefined();
  });

  it('crea il post con dati validi', async () => {
    const formData = new FormData();
    formData.set('title', 'Titolo Valido');
    formData.set('content', 'Contenuto abbastanza lungo per la validazione');
    formData.set('categoryId', '550e8400-e29b-41d4-a716-446655440000');

    await createPost(null, formData);

    const { db } = await import('@/lib/database');
    expect(db.post.create).toHaveBeenCalledWith({
      data: expect.objectContaining({ title: 'Titolo Valido' }),
    });
  });
});
```

### E2E con Playwright

```tsx
// e2e/posts.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Gestione Post', () => {
  test.beforeEach(async ({ page }) => {
    // Seed del database di test
    await page.goto('/');
  });

  test('crea un nuovo post', async ({ page }) => {
    await page.goto('/posts/new');

    await page.fill('input[name="title"]', 'Post di Test E2E');
    await page.fill(
      'textarea[name="content"]',
      'Contenuto del post per il test end-to-end.'
    );
    await page.selectOption('select[name="categoryId"]', { index: 1 });

    await page.click('button[type="submit"]');

    // Verifica redirect alla pagina del post
    await expect(page).toHaveURL(/\/posts\/post-di-test-e2e/);
    await expect(page.locator('h1')).toHaveText('Post di Test E2E');
  });

  test('mostra errori di validazione', async ({ page }) => {
    await page.goto('/posts/new');

    await page.fill('input[name="title"]', 'ab'); // troppo corto
    await page.click('button[type="submit"]');

    await expect(page.locator('.error')).toBeVisible();
  });

  test('streaming: skeleton appare prima dei dati', async ({ page }) => {
    await page.goto('/dashboard');

    // Il skeleton appare immediatamente
    await expect(page.locator('.skeleton-chart')).toBeVisible();

    // I dati reali sostituiscono lo skeleton
    await expect(page.locator('.revenue-chart')).toBeVisible({
      timeout: 5000,
    });
    await expect(page.locator('.skeleton-chart')).not.toBeVisible();
  });
});
```

### Testing dei componenti con Suspense

```tsx
// __tests__/DashboardSection.test.tsx
import { render, screen } from '@testing-library/react';
import { Suspense } from 'react';

// Componente wrapper per testare Suspense
function TestSuspenseWrapper({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Suspense fallback={<div data-testid="loading">Caricamento...</div>}>
      {children}
    </Suspense>
  );
}

describe('DashboardSection con Suspense', () => {
  it('mostra il fallback durante il caricamento', async () => {
    // Simula un componente async lento
    let resolve: (value: unknown) => void;
    const promise = new Promise((r) => { resolve = r; });

    vi.mock('@/lib/database', () => ({
      db: {
        metric: {
          findMany: () => promise,
        },
      },
    }));

    const { MetricsPanel } = await import('@/components/MetricsPanel');

    render(
      <TestSuspenseWrapper>
        <MetricsPanel />
      </TestSuspenseWrapper>
    );

    expect(screen.getByTestId('loading')).toBeInTheDocument();
  });
});
```

---

## Confronto: RSC vs SSR vs SSG vs ISR vs CSR

### Matrice decisionale

| Caratteristica | CSR | SSR | SSG | ISR | RSC |
|---|:---:|:---:|:---:|:---:|:---:|
| **JS inviato al client** | Tutto | Tutto + hydration | Tutto + hydration | Tutto + hydration | Solo Client Components |
| **TTFB** | Veloce (HTML vuoto) | Lento (rendering server) | Velocissimo (CDN) | Velocissimo (CDN) | Veloce (streaming) |
| **LCP** | Lento (JS → render) | Buono | Ottimo | Ottimo | Ottimo (streaming) |
| **SEO** | Scarso | Ottimo | Ottimo | Ottimo | Ottimo |
| **Dati sempre freschi** | Sì (client fetch) | Sì | No (build time) | Parziale (revalidation) | Sì (server fetch) |
| **Costo server** | Nessuno (solo CDN) | Alto (ogni richiesta) | Nessuno (solo build) | Basso | Medio (streaming) |
| **Interattività** | Immediata post-JS | Dopo hydration | Dopo hydration | Dopo hydration | Selettiva (solo Client) |
| **Complessità** | Bassa | Media | Bassa | Media | Alta |
| **Bundle size client** | Grande | Grande | Grande | Grande | Ridotto |
| **Accesso diretto al backend** | No | Solo in getSSP | Solo in getSSP | Solo in getSSP | Sì (nativo) |

### Quando usare cosa

**CSR puro (Vite + React):**
- Dashboard interne senza SEO.
- Applicazioni altamente interattive (editor, tool grafici).
- Prototipazione rapida.
- Quando non serve SSR e il SEO non è rilevante.

**SSR classico (`getServerSideProps`):**
- Pagine che devono essere sempre aggiornate E richiedono SEO.
- Applicazioni Pages Router esistenti che non si migrano.
- Situazioni in cui la latenza di rendering server è accettabile.

**SSG (`getStaticProps`):**
- Blog, documentazione, landing page.
- Contenuti che cambiano raramente.
- Quando le performance sono la priorità assoluta.

**ISR (Incremental Static Regeneration):**
- E-commerce con catalogo vasto.
- Siti di notizie con aggiornamenti periodici.
- Quando serve SSG ma i dati cambiano ogni N minuti/ore.

**RSC (App Router):**
- Progetti nuovi (greenfield) — non c'è ragione per non usarli.
- Applicazioni con grandi dipendenze server-only (Markdown, parsing, data processing).
- Quando la riduzione del bundle client è prioritaria.
- Applicazioni con mix di contenuto statico e dinamico (PPR).
- Quando serve accesso diretto al database senza API intermedie.

### Albero decisionale

```
Il progetto è nuovo (greenfield)?
├─ Sì → USA RSC (App Router)
│       Serve SEO?
│       ├─ Sì → Server Components + metadata
│       └─ No → Server Components comunque (meno JS)
│
└─ No → Progetto esistente
        ├─ Pages Router
        │   ├─ Funziona bene? → Mantieni, migra incrementalmente
        │   └─ Problemi di performance/bundle → Migra a App Router
        │
        └─ Vite / CRA
            ├─ Serve SSR/SEO? → Considera migrazione a Next.js
            └─ Solo SPA → Resta con Vite
```

### RSC vs Islands Architecture

L'**Islands Architecture** (implementata da Astro, Fresh, Îles) e i **React Server Components** affrontano lo stesso problema — ridurre il JavaScript inviato al client — con filosofie opposte.

Nelle Islands, la pagina è HTML statico di default. Solo i componenti interattivi (le "isole") vengono idratati con JS. Ogni isola è indipendente: può usare React, Vue, Svelte o Solid nella stessa pagina. Il framework non mantiene stato di navigazione tra le pagine — ogni navigazione è un full page load (o prefetch MPA).

In RSC, l'intera applicazione è un albero React. I Server Components rendono su server senza inviare JS, ma i Client Components condividono un unico albero React che sopravvive alla navigazione. Lo stato client (modali aperti, scroll position, input compilati) persiste tra le navigazioni grazie al client-side router.

| Aspetto | RSC (Next.js) | Islands (Astro) |
|---------|---------------|-----------------|
| JS default | Zero per Server Components | Zero per componenti statici |
| Stato tra navigazioni | Persistente (SPA router) | Perso (MPA, full reload) |
| Framework mixing | Solo React | React + Vue + Svelte + Solid |
| Streaming | Sì, nativo | Limitato (dipende dall'adapter) |
| Build output | Server richiesto (o static export) | Static-first, server opzionale |
| Complessità mentale | Media-alta (server/client boundary) | Bassa (HTML + isole esplicite) |
| Caso d'uso ideale | App interattive, dashboard, e-commerce | Blog, docs, landing, content site |

**Quando scegliere RSC:** l'applicazione ha navigazione complessa, stato client persistente, form multi-step, real-time updates, o è già un progetto React. RSC eccelle quando il confine server/client attraversa molti componenti e la navigazione deve restare fluida.

**Quando scegliere Islands:** il sito è prevalentemente contenuto statico con pochi punti interattivi isolati (un form di contatto, un carosello, un widget di ricerca). Islands è ideale per siti content-first dove il JS totale deve restare sotto 50KB e non serve stato di navigazione.

Le due architetture non si escludono a vicenda in un'organizzazione: un sito marketing può usare Astro con Islands, mentre l'applicazione SaaS usa Next.js con RSC.

---

## Pattern comuni

### Data table con RSC

```tsx
// app/admin/users/page.tsx
import { db } from '@/lib/database';
import { UserTable } from '@/components/UserTable';

interface PageProps {
  searchParams: Promise<{
    page?: string;
    sort?: string;
    order?: string;
    search?: string;
  }>;
}

export default async function UsersAdminPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const page = Number(params.page) || 1;
  const pageSize = 20;
  const sortField = params.sort || 'createdAt';
  const sortOrder = params.order === 'asc' ? 'asc' : 'desc';
  const search = params.search || '';

  const where = search
    ? {
        OR: [
          { name: { contains: search, mode: 'insensitive' as const } },
          { email: { contains: search, mode: 'insensitive' as const } },
        ],
      }
    : {};

  const [users, totalCount] = await Promise.all([
    db.user.findMany({
      where,
      orderBy: { [sortField]: sortOrder },
      skip: (page - 1) * pageSize,
      take: pageSize,
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        createdAt: true,
        _count: { select: { posts: true } },
      },
    }),
    db.user.count({ where }),
  ]);

  const serializedUsers = users.map((u) => ({
    ...u,
    createdAt: u.createdAt.toISOString(),
    postCount: u._count.posts,
  }));

  return (
    <div>
      <h1>Gestione Utenti</h1>
      {/* Client Component per sorting, filtering, pagination interattiva */}
      <UserTable
        users={serializedUsers}
        totalCount={totalCount}
        currentPage={page}
        pageSize={pageSize}
        currentSort={sortField}
        currentOrder={sortOrder}
        currentSearch={search}
      />
    </div>
  );
}
```

### Form multi-step

```tsx
// components/CheckoutWizard.tsx
'use client';

import { useState, useActionState } from 'react';
import { processCheckout } from '@/actions/checkout';

type Step = 'shipping' | 'payment' | 'review';

export function CheckoutWizard({
  cartItems,
}: {
  cartItems: Array<{ id: string; name: string; price: number; qty: number }>;
}) {
  const [step, setStep] = useState<Step>('shipping');
  const [shippingData, setShippingData] = useState({
    address: '',
    city: '',
    postalCode: '',
  });
  const [paymentData, setPaymentData] = useState({
    cardNumber: '',
    expiry: '',
    cvv: '',
  });

  const [state, formAction, isPending] = useActionState(
    processCheckout,
    { success: false, orderId: null, errors: {} }
  );

  if (state.success && state.orderId) {
    return <OrderConfirmation orderId={state.orderId} />;
  }

  return (
    <div>
      <StepIndicator current={step} />

      {step === 'shipping' && (
        <ShippingForm
          data={shippingData}
          onChange={setShippingData}
          onNext={() => setStep('payment')}
        />
      )}

      {step === 'payment' && (
        <PaymentForm
          data={paymentData}
          onChange={setPaymentData}
          onBack={() => setStep('shipping')}
          onNext={() => setStep('review')}
        />
      )}

      {step === 'review' && (
        <form action={formAction}>
          <ReviewOrder
            cartItems={cartItems}
            shipping={shippingData}
          />
          <input
            type="hidden"
            name="shippingData"
            value={JSON.stringify(shippingData)}
          />
          <input
            type="hidden"
            name="paymentData"
            value={JSON.stringify(paymentData)}
          />
          <button
            type="button"
            onClick={() => setStep('payment')}
          >
            Indietro
          </button>
          <button type="submit" disabled={isPending}>
            {isPending ? 'Elaborazione...' : 'Conferma Ordine'}
          </button>
          {state.errors?.general && (
            <p className="error">{state.errors.general}</p>
          )}
        </form>
      )}
    </div>
  );
}
```

### Dashboard con parallel data loading

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react';
import {
  KPISkeleton,
  ChartSkeleton,
  TableSkeleton,
} from './skeletons';

export default function DashboardPage() {
  return (
    <div className="dashboard">
      <div className="kpi-row">
        <Suspense fallback={<KPISkeleton />}>
          <KPICards />
        </Suspense>
      </div>

      <div className="charts-row">
        <Suspense fallback={<ChartSkeleton />}>
          <RevenueChart />
        </Suspense>
        <Suspense fallback={<ChartSkeleton />}>
          <ConversionChart />
        </Suspense>
      </div>

      <Suspense fallback={<TableSkeleton />}>
        <RecentTransactions />
      </Suspense>
    </div>
  );
}

// Ogni componente fetcha i suoi dati indipendentemente
async function KPICards() {
  const kpis = await db.kpi.findMany({
    where: { period: 'current_month' },
  });
  return (
    <div className="kpi-grid">
      {kpis.map((kpi) => (
        <div key={kpi.id} className="kpi-card">
          <span className="kpi-label">{kpi.label}</span>
          <span className="kpi-value">{kpi.value}</span>
          <span className={`kpi-change ${kpi.change > 0 ? 'positive' : 'negative'}`}>
            {kpi.change > 0 ? '+' : ''}{kpi.change}%
          </span>
        </div>
      ))}
    </div>
  );
}
```

### E-commerce product page

```tsx
// app/products/[slug]/page.tsx
import { Suspense } from 'react';
import { db } from '@/lib/database';
import { notFound } from 'next/navigation';
import { AddToCartButton } from '@/components/AddToCartButton';
import { ReviewsList } from './ReviewsList';
import { RelatedProducts } from './RelatedProducts';
import type { Metadata } from 'next';

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const product = await db.product.findUnique({ where: { slug } });
  if (!product) return {};
  return {
    title: product.name,
    description: product.description.slice(0, 160),
    openGraph: {
      images: [{ url: product.imageUrl, width: 1200, height: 630 }],
    },
  };
}

export default async function ProductPage({ params }: PageProps) {
  const { slug } = await params;
  const product = await db.product.findUnique({
    where: { slug },
    include: {
      category: true,
      variants: { where: { inStock: true } },
    },
  });

  if (!product) notFound();

  return (
    <div className="product-page">
      <section className="product-main">
        <div className="product-gallery">
          <img src={product.imageUrl} alt={product.name} />
        </div>
        <div className="product-info">
          <h1>{product.name}</h1>
          <p className="price">{product.price.toFixed(2)} €</p>
          <p className="description">{product.description}</p>

          {/* Client Component: gestisce selezione variante e aggiunta al carrello */}
          <AddToCartButton
            productId={product.id}
            variants={product.variants.map((v) => ({
              id: v.id,
              label: v.label,
              surcharge: v.surcharge,
            }))}
          />
        </div>
      </section>

      {/* Streaming: le recensioni possono arrivare dopo */}
      <Suspense fallback={<div>Caricamento recensioni...</div>}>
        <ReviewsList productId={product.id} />
      </Suspense>

      <Suspense fallback={<div>Prodotti correlati...</div>}>
        <RelatedProducts categoryId={product.category.id} excludeId={product.id} />
      </Suspense>
    </div>
  );
}
```

---

## Debug del RSC Payload

Il **RSC Payload** è il formato binario con cui il server trasmette l'albero dei Server Components al client. Capire come ispezionarlo è essenziale per diagnosticare problemi di performance e dimensione.

### Ispezione con Chrome DevTools

Nel pannello **Network** di Chrome DevTools, filtrare per richieste con content-type `text/x-component` (navigazioni client-side) o cercare richieste che terminano con `?_rsc=...`. Il payload appare come una sequenza di righe con prefissi numerici (`0:`, `1:`, `2:`) che rappresentano chunk dello stream. Ogni riga è JSON serializzato che descrive nodi dell'albero React, riferimenti a Client Components, e dati props.

Per le navigazioni iniziali (full page load), il payload RSC è incorporato direttamente nell'HTML dentro tag `<script>` con attributo `self.__next_f.push(...)`. Cercare `__next_f` nel sorgente HTML della pagina per vedere i chunk inline.

### rsc-parser

Lo strumento open source **rsc-parser** (github.com/alvarlagerlof/rsc-parser) offre un'interfaccia visuale per decodificare il payload RSC. Si può usare come estensione Chrome o come CLI:

```bash
# installazione come dev dependency
npm install -D rsc-parser

# analisi di un URL
npx rsc-parser https://localhost:3000/dashboard
```

L'output mostra l'albero dei componenti serializzato, evidenziando i Client Component reference (`@1`, `@2`), i chunk di dati, e la dimensione di ogni segmento. È particolarmente utile per identificare **props troppo grandi** passate attraverso il confine server/client.

### Monitoraggio dimensione payload

Per pagine con molti dati, il payload RSC può superare le centinaia di KB. Monitorare la dimensione nel tempo previene regressioni:

```ts
// middleware.ts — logging dimensione RSC payload (solo dev)
import { NextResponse, type NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  if (process.env.NODE_ENV === 'development') {
    const response = NextResponse.next();
    const url = request.nextUrl.pathname;

    // Log per analisi manuale
    console.log(`[RSC] ${url} — request at ${new Date().toISOString()}`);

    return response;
  }
  return NextResponse.next();
}
```

La regola pratica: se una singola navigazione RSC supera 200KB di payload, rivalutare quanti dati passano attraverso i props dei Server Components. Spostare dati pesanti in chiamate separate o paginare i risultati.

### React DevTools Profiler

Il **Profiler** di React DevTools funziona anche con i Server Components nella visualizzazione dell'albero. I componenti server appaiono come nodi nell'albero ma senza hook o stato. Il Profiler misura il tempo di rendering lato client — per il tempo di rendering lato server, usare le API di Server Timing (`performance.measure()` in Node.js) e il pannello **Timing** di DevTools per correlare i tempi di rete con il rendering.

### Checklist di debug RSC

Quando si diagnosticano problemi con Server Components, seguire questa sequenza:

1. **Verificare il tipo di componente.** Aprire React DevTools: i Server Components mostrano un badge "Server" nell'albero. Se un componente dovrebbe essere server ma risulta client, controllare la catena di import — un import da un modulo `'use client'` forza tutto il sottoalbero a diventare client.

2. **Controllare la dimensione del payload.** Nel pannello Network, filtrare per `text/x-component`. Se il payload supera 200KB, i props contengono troppi dati. Serializzare solo ciò che serve al rendering, non interi oggetti database.

3. **Individuare serializzazione fallita.** Se il server lancia "cannot be serialized", significa che si sta passando un valore non serializzabile (funzione, classe, Date non gestita, Symbol) come prop da un Server Component a un Client Component. Solo JSON-serializable values attraversano il confine.

4. **Ispezionare `__next_f` nel sorgente.** Fare View Source sulla pagina e cercare `self.__next_f.push`. Il numero di chunk e la loro dimensione rivelano quanto dato viene inviato inline nel documento HTML iniziale. Chunk molto grandi rallentano il First Contentful Paint perché il parser HTML deve processarli prima di mostrare contenuto.

5. **Misurare il waterfall.** Usare il pannello Performance di DevTools per registrare il caricamento completo. Identificare gap tra la fine del documento HTML e l'inizio dello streaming RSC — gap lunghi indicano colli di bottiglia nel data layer del server.

---

## Troubleshooting

### 1. Hydration mismatch

**Sintomo:** Warning in console: "Text content does not match server-rendered HTML" o "Hydration failed because the server rendered HTML didn't match the client."

**Cause comuni:**
- Uso di `Date.now()`, `Math.random()`, o timestamp nel render.
- Accesso a `window`, `localStorage`, o `navigator` durante il render (non esiste sul server).
- Estensioni browser che modificano il DOM prima dell'hydration.
- HTML invalido (es. `<p>` dentro `<p>`, `<div>` dentro `<p>`).
- Librerie CSS-in-JS che generano classname diversi su server e client.

**Soluzioni:**

```tsx
// ❌ CAUSA MISMATCH: valore diverso server vs client
function Timestamp() {
  return <span>{new Date().toLocaleString()}</span>;
}

// ✅ SOLUZIONE 1: stato client-only con suppressHydrationWarning
function Timestamp() {
  const [time, setTime] = useState<string>('');
  useEffect(() => {
    setTime(new Date().toLocaleString());
  }, []);
  return <span suppressHydrationWarning>{time || 'Caricamento...'}</span>;
}

// ✅ SOLUZIONE 2: passare il valore dal server come prop
// Nel Server Component parent:
<Timestamp initialTime={new Date().toISOString()} />
```

### 2. "Functions cannot be passed directly to Client Components"

**Sintomo:** Errore a runtime: "Functions cannot be passed directly to Client Components unless you explicitly expose it by marking it with 'use server'."

**Soluzione:** Le funzioni passate come props da Server a Client Component devono essere Server Actions (`'use server'`).

```tsx
// ❌ ERRORE
<ClientComponent onFilter={(item) => item.active} />

// ✅ CORRETTO: usa una Server Action o sposta la logica nel Client Component
<ClientComponent showOnlyActive={true} />
```

### 3. "Cannot import server-only module in Client Component"

**Sintomo:** Build error quando un Client Component importa (direttamente o transitivamente) un modulo marcato con `import 'server-only'`.

**Soluzione:** Ristrutturare le import. Il Client Component non deve importare moduli server. Passare i dati come props dal Server Component parent.

### 4. Infinite fetch loop nei Server Components

**Sintomo:** La pagina effettua richieste infinite al proprio endpoint.

**Causa:** Un Server Component che fetcha il proprio URL (l'app chiama se stessa).

**Soluzione:** Accedere direttamente al database o alla logica di business invece di passare per HTTP.

### 5. "Dynamic server usage" errore durante il build

**Sintomo:** `Error: Dynamic server usage: cookies` o `headers` durante `next build` su una pagina che dovrebbe essere statica.

**Causa:** Uso di `cookies()`, `headers()`, o `searchParams` in una pagina che Next.js tenta di renderizzare staticamente.

**Soluzioni:**
- Aggiungere `export const dynamic = 'force-dynamic'` se la pagina deve essere dinamica.
- Spostare la logica dinamica sotto un Suspense boundary (con PPR abilitato).
- Rivedere se l'accesso ai cookie/header è realmente necessario.

### 6. Server Action ritorna undefined

**Sintomo:** La Server Action viene invocata ma il risultato è sempre `undefined`.

**Causa:** La Server Action termina con `redirect()` (che lancia un'eccezione interna) o non ritorna esplicitamente un valore.

**Soluzione:** Non usare `redirect()` se si vuole ritornare un valore. Oppure gestire il redirect nel Client Component dopo aver ricevuto il risultato.

### 7. `revalidatePath` non aggiorna la pagina

**Sintomo:** Dopo `revalidatePath('/products')` la pagina mostra ancora i dati vecchi.

**Cause:**
- Il Router Cache del client mostra ancora la versione cached.
- Il path non corrisponde esattamente (case sensitivity, trailing slash).
- La revalidazione avviene su un layout che non viene ri-renderizzato.

**Soluzioni:**
- Usare `router.refresh()` nel Client Component dopo la Server Action.
- Verificare che il path sia esattamente corretto.
- Usare `revalidateTag` per invalidazione più precisa.

### 8. Dati stale dopo navigazione client-side

**Sintomo:** La navigazione con `<Link>` mostra dati vecchi anche dopo una mutazione.

**Causa:** Il Router Cache (client-side) serve la versione cached della route.

**Soluzione:**

```tsx
'use client';

import { useRouter } from 'next/navigation';

export function RefreshButton() {
  const router = useRouter();
  return (
    <button onClick={() => router.refresh()}>
      Aggiorna dati
    </button>
  );
}
```

### 9. Server Component re-render quando non dovrebbe

**Sintomo:** Un Server Component viene ri-renderizzato ad ogni navigazione anche quando i suoi dati non cambiano.

**Causa:** Il componente si trova fuori da un layout persistente, quindi viene ri-eseguito ad ogni richiesta.

**Soluzione:** Spostare il componente in un layout (che persiste durante la navigazione) o implementare caching con `'use cache'`.

### 10. "Cannot read properties of undefined" con `params`

**Sintomo:** Errore a runtime `Cannot read properties of undefined (reading 'slug')` in un dynamic route.

**Causa (Next.js 15):** In Next.js 15, `params` e `searchParams` sono **Promise** e devono essere awaited.

```tsx
// ❌ Next.js 14 style (non funziona in 15)
export default function Page({ params }: { params: { slug: string } }) {
  const slug = params.slug; // ERRORE: params è una Promise
}

// ✅ Next.js 15 style
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params; // CORRETTO
}
```

### 11. Serialization error con Date objects

**Sintomo:** Errore "Only plain objects, and a few built-ins, can be passed to Client Components" quando si passano oggetti con Date.

**Soluzione:** Convertire le Date in stringhe ISO prima di passarle come props.

```tsx
// ❌ ERRORE: Date non è plain object (in alcune versioni)
<ClientComponent createdAt={post.createdAt} />

// ✅ CORRETTO: serializza a stringa
<ClientComponent createdAt={post.createdAt.toISOString()} />
```

### 12. CSS/stili mancanti durante lo streaming

**Sintomo:** I contenuti streamati appaiono senza stili per un momento (FOUC).

**Soluzione:** Assicurarsi che il CSS sia caricato nel layout (che viene inviato nel primo chunk). Usare CSS Modules o Tailwind (inline via PostCSS). Evitare CSS-in-JS runtime che richiede JS per iniettare gli stili.

### 13. `useEffect` non viene eseguito in Server Component

**Sintomo:** `useEffect` non fa nulla — nessun errore, nessun effetto.

**Causa:** Il componente è un Server Component (default). `useEffect` non esiste sul server.

**Soluzione:** Aggiungere `'use client'` in cima al file, o spostare la logica con effetti in un Client Component figlio dedicato.

### 14. "Unsupported Server Component type" con librerie UI

**Sintomo:** Librerie UI (Radix, shadcn, MUI) non funzionano come Server Components.

**Causa:** Queste librerie usano internamente hooks (`useState`, `useRef`, `useContext`) e devono essere Client Components.

**Soluzione:** Wrappare i componenti della libreria in un file con `'use client'`:

```tsx
// components/ui/dialog.tsx
'use client';

// Re-export dei componenti della libreria come Client Components
export { Dialog, DialogTrigger, DialogContent } from '@radix-ui/react-dialog';
```

### 15. Build lentissimo con molti Server Components

**Sintomo:** `next build` impiega molto tempo perché ogni Server Component viene eseguito durante il build.

**Soluzioni:**
- Usare `export const dynamic = 'force-dynamic'` per le pagine che non devono essere pre-renderizzate.
- Limitare `generateStaticParams` a un sottoinsieme (es. gli articoli più popolari).
- Aumentare le risorse del build server.
- Usare `dynamicParams = true` per permettere il rendering on-demand delle pagine non pre-generate.

### 16. Server Action file upload non funziona

**Sintomo:** File caricati tramite Server Action sono vuoti o corrotti.

**Soluzione:** Usare `FormData` con il tipo `File` e processare correttamente lato server:

```tsx
'use server';

export async function uploadFile(formData: FormData) {
  const file = formData.get('file') as File;
  if (!file || file.size === 0) {
    return { error: 'Nessun file selezionato' };
  }

  // Validazione
  const MAX_SIZE = 5 * 1024 * 1024; // 5 MB
  if (file.size > MAX_SIZE) {
    return { error: 'File troppo grande (max 5 MB)' };
  }

  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
  if (!ALLOWED_TYPES.includes(file.type)) {
    return { error: 'Tipo file non supportato' };
  }

  const bytes = await file.arrayBuffer();
  const buffer = Buffer.from(bytes);

  // Salva su filesystem o object storage
  await writeFile(`./uploads/${file.name}`, buffer);

  return { success: true, filename: file.name };
}
```

---

## FAQ

### 1. RSC sostituisce SSR?

No. RSC e SSR sono complementari. SSR pre-renderizza l'HTML sul server per il primo caricamento. RSC determina *quali* componenti vengono eseguiti sul server e *quali* sul client. I Client Components vengono comunque pre-renderizzati via SSR — la differenza è che il loro JavaScript viene anche inviato al client per l'hydration. RSC aggiunge il concetto di componenti che sono *esclusivamente* server-side e non richiedono hydration.

### 2. Posso usare RSC senza Next.js?

Tecnicamente sì, ma ad oggi (2026) Next.js è l'unico framework con supporto RSC maturo e production-ready. Waku è un'alternativa sperimentale più leggera. Il protocollo RSC di React è framework-agnostic, ma l'implementazione del bundler, del server, e del routing è complessa e richiede integrazione profonda.

### 3. Come gestisco lo stato globale con RSC?

Lo stato globale client-side (Zustand, Jotai, Redux) funziona normalmente nei Client Components. La differenza è che con RSC si dovrebbe avere **meno** stato client: i dati che prima venivano fetchati sul client e messi nello store ora vengono fetchati direttamente nei Server Components e passati come props. Lo store client dovrebbe contenere solo state UI (modali aperte, selezioni temporanee, theme).

### 4. Le Server Actions sono sicure?

Le Server Actions espongono endpoint HTTP POST. Next.js gestisce automaticamente la protezione CSRF. Tuttavia, **ogni Server Action deve validare i propri input e verificare autenticazione/autorizzazione** — esattamente come un API endpoint tradizionale. Non fidarsi mai che i dati arrivino da un form fidato, perché chiunque può invocare l'endpoint con dati arbitrari.

### 5. Posso usare un ORM (Prisma, Drizzle) nei Server Components?

Sì, è uno dei vantaggi principali di RSC. I Server Components possono importare direttamente il client Prisma/Drizzle e eseguire query. Il codice dell'ORM resta sul server e non finisce nel bundle client. È importante marcare il modulo database con `import 'server-only'` per prevenire import accidentali nei Client Components.

### 6. Come funziona il caching in Next.js 15?

In Next.js 15 **nulla è cachato di default** (a differenza di Next.js 14). Per cachare i dati si usano: la direttiva `'use cache'` a livello di funzione/componente, le opzioni `cache: 'force-cache'` o `next: { revalidate: N }` in `fetch()`, oppure il segment config `export const revalidate = N`. La revalidazione on-demand usa `revalidatePath()` o `revalidateTag()`.

### 7. Come gestisco gli errori nei Server Components?

I Server Components che lanciano un'eccezione vengono catturati dal più vicino `error.tsx` (Error Boundary). Per errori 404, si usa `notFound()` da `next/navigation` che attiva il `not-found.tsx`. Per errori di validazione nelle Server Actions, si ritorna un oggetto errore strutturato invece di lanciare eccezioni.

### 8. Le librerie CSS-in-JS funzionano con RSC?

Le librerie CSS-in-JS runtime (styled-components, Emotion) richiedono JavaScript lato client per iniettare gli stili. Funzionano nei Client Components ma non nei Server Components. Soluzioni raccomandate per RSC: CSS Modules, Tailwind CSS, o soluzioni zero-runtime come vanilla-extract o Panda CSS.

### 9. Come testo i Server Components?

I Server Components sono funzioni async che ritornano JSX. Si possono testare invocandoli direttamente e renderizzando il risultato con React Testing Library. I mock dei moduli server (database, fetch) seguono lo stesso pattern dei test tradizionali. Per E2E, Playwright funziona senza modifiche — testa l'output HTML senza distinzione tra Server e Client Components.

### 10. Cos'è il Partial Prerendering (PPR)?

PPR è una feature sperimentale di Next.js 15 che combina rendering statico e dinamico nella stessa pagina. La shell statica viene pre-renderizzata a build time e servita dalla CDN. I "buchi" dinamici (contenuti che richiedono `cookies()`, `headers()`, o dati real-time) vengono risolti tramite streaming al momento della richiesta. L'effetto è un TTFB velocissimo (cache hit sulla CDN) con contenuti personalizzati che appaiono progressivamente.

### 11. Qual è la differenza tra `'use client'` e `'use server'`?

`'use client'` marca un modulo come Client Component boundary — il componente e i suoi import verranno inclusi nel bundle client e idratati. `'use server'` marca una funzione (o un modulo intero) come Server Action — una funzione eseguita sul server che può essere invocata dal client tramite RPC automatico. Non sono opposti: un Client Component può invocare una Server Action.

### 12. Come migro un progetto grande da Pages Router a App Router?

Incrementalmente. Le due directory (`pages/` e `app/`) coesistono in Next.js. Si inizia migrando il layout globale, poi una route alla volta, partendo dalle più semplici. `getServerSideProps` diventa un fetch diretto nel Server Component. `getStaticProps` diventa un Server Component con `revalidate` config. Si possono mantenere le API routes in `pages/api/` anche durante la migrazione.

### 13. I Server Components supportano WebSocket o connessioni persistenti?

No direttamente. I Server Components vengono eseguiti una volta per generare l'output e poi terminano — non mantengono connessioni persistenti. Per WebSocket o real-time, serve un Client Component che gestisce la connessione. Il Server Component può fornire i dati iniziali, e il Client Component si aggiorna via WebSocket.

### 14. Come gestisco i redirect nei Server Components?

Usando `redirect()` da `next/navigation`. Questa funzione lancia internamente un'eccezione (NEXT_REDIRECT) che Next.js intercetta per effettuare il redirect. Non scrivere codice dopo `redirect()` — non verrà eseguito.

```tsx
import { redirect } from 'next/navigation';

export default async function ProtectedPage() {
  const session = await auth();
  if (!session) redirect('/login');
  // ...
}
```

### 15. Qual è il costo di performance di RSC?

Il costo principale è l'esecuzione dei Server Components ad ogni richiesta (per le route dinamiche). Questo consuma CPU server e aggiunge latenza rispetto a pagine pre-renderizzate staticamente. Il vantaggio è un bundle client significativamente più piccolo e un LCP migliore. Il trade-off dipende dall'applicazione: per siti ad alto traffico con contenuti statici, SSG resta più efficiente. Per applicazioni con dati dinamici, RSC è generalmente superiore a CSR perché elimina il round-trip client → API → client.

### 16. Come gestisco l'internazionalizzazione (i18n) con RSC?

I Server Components possono leggere il locale dai cookie, dall'header `Accept-Language`, o dal segmento URL e caricare le traduzioni appropriate lato server — senza inviare tutte le lingue nel bundle client. Librerie come `next-intl` hanno supporto nativo per RSC. Il pattern consigliato è passare solo le traduzioni rilevanti al Client Component come props.

---

## Best Practices e Anti-Pattern

### Best Practices

**1. Default server, opt-in client.** Non aggiungere `'use client'` "per sicurezza". Iniziare senza e aggiungerlo solo quando il componente richiede hooks, event handler, o API del browser.

**2. Minimizzare la surface del Client Component.** Se un componente ha 200 righe e solo 10 righe richiedono interattività, estrarre quelle 10 righe in un piccolo Client Component e tenere il resto come Server Component.

```tsx
// ✅ CORRETTO: solo il bottone è un Client Component
// app/products/[id]/page.tsx (Server Component)
export default async function ProductPage({ params }) {
  const { id } = await params;
  const product = await db.product.findUnique({ where: { id } });

  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <p>{product.price.toFixed(2)} €</p>
      {/* Solo questo è un Client Component */}
      <AddToCartButton productId={product.id} />
    </div>
  );
}
```

**3. Validare sempre le Server Actions.** Trattare ogni Server Action come un endpoint API pubblico — validazione input, autenticazione, autorizzazione, rate limiting.

**4. Serializzare solo il necessario.** Non passare interi oggetti database come props ai Client Components. Selezionare e trasformare solo i campi necessari.

**5. Usare Suspense per UX progressiva.** Ogni sezione con dati asincroni indipendenti dovrebbe avere il proprio Suspense boundary con un fallback adeguato (skeleton, non spinner generico).

**6. Preferire `revalidateTag` a `revalidatePath`.** I tag permettono invalidazione granulare e sono più prevedibili dei path.

**7. Usare `'use cache'` per dati costosi ma tolleranti alla latenza.** Configurare `cacheLife` appropriatamente.

**8. Marcare i moduli server con `import 'server-only'`.** Ogni modulo che accede al database, filesystem, o segreti deve impedire l'import accidentale nei Client Components.

**9. Usare `next/image` e `next/font` per performance automatica.** Ottimizzazione immagini, font subsetting, e preloading sono gestiti automaticamente.

**10. Strutturare per route group.** Usare route groups `(nome)` per organizzare le route senza influenzare l'URL.

### Anti-Pattern

**1. ❌ `'use client'` su tutto.** Trasforma RSC in una SPA tradizionale con SSR, perdendo tutti i vantaggi.

**2. ❌ Fetch nel Client Component per dati disponibili sul server.** Se il dato può essere fetchato in un Server Component e passato come prop, farlo sempre. Il fetch nel Client Component aggiunge un round-trip extra.

**3. ❌ Passare funzioni callback come props da server a client.**

```tsx
// ❌ ANTI-PATTERN
<ClientComponent onSave={(data) => db.save(data)} />

// ✅ CORRETTO: usa una Server Action
<ClientComponent onSave={saveAction} />
```

**4. ❌ Stato globale per dati server.** Non mettere i dati fetchati dal server in Redux/Zustand. I Server Components li passano direttamente come props — lo store globale è per state UI client-only.

**5. ❌ `useEffect` per data fetching.** Con RSC, il data fetching appartiene ai Server Components. `useEffect` per fetch è un code smell che indica un componente che dovrebbe essere (parzialmente) server.

**6. ❌ Un unico grande Suspense boundary.** Vanifica lo streaming — l'utente non vede nulla fino a quando il dato più lento è pronto.

**7. ❌ `export const dynamic = 'force-dynamic'` ovunque.** Disabilita la static generation per route che potrebbero essere cachate, perdendo performance gratuite.

**8. ❌ Ignorare le regole di serializzazione.** Passare oggetti non serializzabili (classi, funzioni, Symbol) genera errori a runtime difficili da diagnosticare.

**9. ❌ Server Action senza validazione.** Equivale a un endpoint API senza input validation — vulnerabilità injection garantita.

**10. ❌ Mixing di CSS-in-JS runtime con Server Components.** Le librerie CSS-in-JS che richiedono JavaScript runtime (styled-components senza SSR config) causano FOUC e hydration mismatch.

---

## Esercizi

### Lab 1 — RSC vs CSR: confronto quantitativo

Implementare la stessa pagina (lista di prodotti con filtro e ordinamento) in due versioni:
1. **Versione RSC:** Server Component con `<Link>` per filtro/sort via searchParams + piccolo Client Component per l'input di ricerca.
2. **Versione CSR:** `'use client'` con `useState`, `useEffect`, e fetch API.

Misurare e confrontare: bundle size (JS inviato al client), TTFB, LCP, FCP. Documentare i risultati.

### Lab 2 — Server Action con validazione e feedback

Creare un form di registrazione utente con Server Action che include:
- Validazione Zod (email, password forte, conferma password).
- Feedback errori per campo con `useActionState`.
- Loading state durante il submit.
- Redirect a `/welcome` dopo registrazione riuscita.
- Rate limiting (max 5 tentativi per minuto per IP).

### Lab 3 — Dashboard con streaming progressivo

Costruire una dashboard con almeno 4 sezioni di dati indipendenti, ognuna con:
- Suspense boundary dedicato.
- Skeleton di caricamento personalizzato.
- Fetch simulato con `setTimeout` di durata diversa (100ms, 500ms, 1s, 2s) per osservare il rendering progressivo.

### Lab 4 — Migrazione Pages Router → App Router

Prendere un progetto Next.js con Pages Router esistente (o crearne uno minimale con 3-4 pagine) e migrarlo all'App Router:
- Convertire `_app.tsx` e `_document.tsx` in `layout.tsx`.
- Convertire `getServerSideProps` in Server Component con fetch diretto.
- Convertire `getStaticProps` + `getStaticPaths` in `generateStaticParams` + segment config.
- Verificare che tutte le funzionalità esistenti continuino a funzionare.

### Lab 5 — Server-Driven UI con A/B testing

Implementare una landing page la cui struttura (ordine delle sezioni, varianti di copy, colori dei CTA) è determinata da una configurazione nel database:
- Creare un sistema di configurazione pagine nel database (Prisma/Drizzle).
- Implementare un registry di componenti per il rendering dinamico.
- Aggiungere A/B testing server-side con assegnazione tramite cookie.
- Nessun JavaScript extra per il testing (tutto server-side).

### Lab 6 — Autenticazione full-stack con RSC

Implementare un sistema di autenticazione completo:
- Login/Register con Server Actions.
- JWT in cookie HttpOnly.
- Middleware per protezione route.
- Layout protetto con info utente.
- Ruoli (admin, user) con guard nei Server Components.
- Pagina profilo con modifica via Server Action.

### Stretch — PPR e performance profiling

Abilitare PPR su una pagina e-commerce e misurare:
- TTFB con e senza PPR.
- Dimensione del RSC Payload.
- Tempo di streaming dei chunk dinamici.
- Bundle size dei Client Components.

Usare Chrome DevTools Performance panel e `next build --profile` per l'analisi.

---

## Letture

- React Server Components — Documentazione ufficiale React. https://react.dev/reference/rsc/server-components
- React `'use client'` — Documentazione ufficiale. https://react.dev/reference/rsc/use-client
- React `'use server'` — Documentazione ufficiale. https://react.dev/reference/rsc/use-server
- Next.js App Router — Documentazione ufficiale. https://nextjs.org/docs/app
- Next.js Caching — Documentazione caching Next.js 15. https://nextjs.org/docs/app/building-your-application/caching
- Next.js Server Actions — Documentazione ufficiale. https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations
- Next.js Partial Prerendering — Documentazione PPR. https://nextjs.org/docs/app/building-your-application/rendering/partial-prerendering
- Dan Abramov — "RSC from Scratch" (serie tecnica). https://github.com/reactwg/server-components/discussions/5
- Josh Comeau — "Making Sense of React Server Components". https://www.joshwcomeau.com/react/server-components/
- Vercel Blog — "Understanding React Server Components". https://vercel.com/blog/understanding-react-server-components
- Lee Robinson — "Next.js App Router migration guide". https://nextjs.org/docs/app/building-your-application/upgrading/app-router-migration

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [07 — React](07-react.md) | Fondamenti React 19 necessari per comprendere il modello RSC |
| [25 — Next.js](25-nextjs-guida-completa.md) | App Router, caching stratificato e deployment di applicazioni RSC |
| [17 — Performance Web](17-performance-web.md) | Metriche Core Web Vitals e Lighthouse per misurare i benefici di RSC |
| [13 — Autenticazione](13-autenticazione-autorizzazione.md) | JWT, sessioni e protezione route in contesto server/client |
| [06 — TypeScript](06-typescript.md) | Type safety end-to-end tra Server e Client Components |
| [15 — Testing Web](15-testing-web.md) | Strategie di test per Server Components e Server Actions |

---

## Glossario

| Termine | Definizione |
|---|---|
| **RSC** | React Server Components — componenti React eseguiti esclusivamente sul server, il cui JavaScript non viene mai inviato al client. |
| **RSC Payload** | Formato di serializzazione wire utilizzato da React per trasmettere l'albero dei componenti dal server al client. Protocollo line-based ottimizzato per lo streaming. |
| **Server Component** | Componente React di default (in App Router) che viene eseguito solo sul server. Può essere `async`, accedere al database, al filesystem, e alle variabili d'ambiente. |
| **Client Component** | Componente React marcato con `'use client'` che viene pre-renderizzato sul server (SSR), inviato come HTML, e poi idratato sul client con il suo bundle JavaScript. Supporta state, effetti, e event handler. |
| **`'use client'`** | Direttiva del compilatore che marca un modulo (e i suoi import) come boundary dei Client Components. |
| **`'use server'`** | Direttiva che marca una funzione o un modulo come Server Action — funzione eseguita sul server invocabile dal client via RPC. |
| **`'use cache'`** | Direttiva Next.js 15 che abilita il caching a livello di funzione o componente. Sostituisce il caching implicito di `fetch` in Next.js 14. |
| **Hydration** | Processo lato client in cui React aggancia event handler e state al DOM HTML pre-renderizzato dal server, rendendo la pagina interattiva. |
| **Streaming** | Tecnica di invio progressivo dell'HTML dal server al client in chunk, usando `Transfer-Encoding: chunked`. Permette al browser di renderizzare contenuti prima che l'intera risposta sia completa. |
| **Suspense boundary** | Componente React `<Suspense>` che definisce un confine per il caricamento asincrono. Mostra un fallback mentre i componenti figli asincroni si risolvono. |
| **SSR** | Server-Side Rendering — tecnica di pre-rendering dell'HTML sul server ad ogni richiesta. |
| **SSG** | Static Site Generation — tecnica di pre-rendering dell'HTML a build time, servito poi come file statici. |
| **ISR** | Incremental Static Regeneration — estensione di SSG che permette di rigenerare pagine statiche dopo il deploy, con una finestra di revalidazione temporale. |
| **CSR** | Client-Side Rendering — rendering interamente nel browser. Il server serve un HTML minimo e il client scarica ed esegue tutto il JavaScript. |
| **PPR** | Partial Prerendering — feature Next.js 15 che combina shell statica (CDN) con contenuti dinamici (streaming) nella stessa route. |
| **Server Action** | Funzione asincrona marcata `'use server'`, eseguita sul server, invocabile da form HTML o codice client. Next.js gestisce serializzazione, CSRF, e trasporto. |
| **App Router** | Architettura di routing di Next.js basata su directory annidate in `app/`, con supporto nativo per RSC, layout persistenti, streaming, e parallel routes. |
| **Pages Router** | Architettura di routing legacy di Next.js basata su file in `pages/`, con `getServerSideProps`, `getStaticProps`, e `_app.tsx`/`_document.tsx`. |
| **Route Handler** | File `route.ts` nell'App Router che definisce endpoint API (equivalente di `pages/api/`). Supporta tutti i metodi HTTP. |
| **Parallel Routes** | Meccanismo App Router per renderizzare più pagine simultaneamente nella stessa vista, usando slot `@nome`. Ogni slot ha un Suspense boundary indipendente. |
| **Intercepting Routes** | Meccanismo App Router per intercettare una navigazione e mostrare il contenuto in un contesto diverso (es. modale), mantenendo la URL completa per hard navigation. |
| **Request Memoization** | Meccanismo React che deduplica chiamate `fetch` identiche all'interno dello stesso render pass server. |
| **Data Cache** | Cache persistente di Next.js per risposte `fetch`. In Next.js 15 è opt-in (non più default). |
| **Full Route Cache** | Cache di Next.js che memorizza HTML + RSC Payload per route statiche pre-renderizzate a build time. |
| **Router Cache** | Cache in-memory lato client che memorizza il RSC Payload delle route visitate per navigazione istantanea. |
| **`revalidatePath`** | Funzione Next.js per invalidare la cache di una route specifica dopo una mutazione. |
| **`revalidateTag`** | Funzione Next.js per invalidare tutti i dati associati a un tag specifico dopo una mutazione. |
| **`cacheLife`** | Funzione Next.js 15 per specificare la durata della cache quando si usa la direttiva `'use cache'`. |
| **`cacheTag`** | Funzione Next.js 15 per associare tag di invalidazione a dati cachati con `'use cache'`. |
| **`generateStaticParams`** | Funzione App Router equivalente a `getStaticPaths` — definisce quali parametri dinamici pre-renderizzare a build time. |
| **`generateMetadata`** | Funzione App Router per generare metadata SEO dinamici (title, description, OG tags) basati sui dati della pagina. |
| **`server-only`** | Pacchetto npm che, importato in un modulo, impedisce l'inclusione di quel modulo nel bundle client (errore a build time). |
| **`dynamicIO`** | Flag sperimentale Next.js 15 legato al sistema di caching `'use cache'`. |
| **Error Boundary** | Componente React che cattura errori JavaScript nei componenti figli e mostra un UI di fallback. In App Router si implementa con `error.tsx`. |
| **`notFound()`** | Funzione Next.js che attiva il rendering del `not-found.tsx` più vicino nell'albero dei componenti. |
| **Route Group** | Directory con nome tra parentesi `(nome)` che organizza le route senza influenzare l'URL. Utile per layout condivisi e organizzazione logica. |
| **Middleware** | File `middleware.ts` alla root del progetto Next.js che intercetta ogni richiesta HTTP prima del rendering. Usato per autenticazione, redirect, header personalizzati. |
| **`next/form`** | Componente Next.js 15 che estende il form HTML nativo con prefetching della route di destinazione e navigazione client-side. |
