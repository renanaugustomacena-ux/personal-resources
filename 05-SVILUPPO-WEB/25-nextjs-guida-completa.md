---
corso: "Sviluppo Web Full-Stack"
fase: "7 — Architetture Avanzate"
modulo: 25
titolo: "Next.js 15 — Guida Completa"
versione: "Next.js 15 / React 19"
livello: "Avanzato"
prerequisiti: ["07-react", "06-typescript"]
obiettivi:
  - "Padroneggiare App Router con file-based routing e layout nidificati"
  - "Implementare data fetching con Server Components e 'use cache'"
  - "Progettare Server Actions per mutazioni inline senza API endpoint"
  - "Comprendere il sistema di caching stratificato (Route, Data, Router Cache)"
  - "Configurare deployment con Vercel, Docker e self-hosting"
tag: [next.js, app-router, rsc, server-actions, caching, ppr, deployment]
---

# Next.js 15 — Guida Completa

> **Modulo 25** · **Versione:** Next.js 15 · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Padroneggiare App Router con file-based routing e layout nidificati
> 2. Implementare data fetching con Server Components e `'use cache'`
> 3. Progettare Server Actions per mutazioni inline senza API endpoint
> 4. Comprendere il sistema di caching stratificato (Route, Data, Router Cache)
> 5. Configurare deployment con Vercel, Docker e self-hosting
>
> **Prerequisiti:** [React](07-react.md), [TypeScript](06-typescript.md)
> **Tempo stimato:** 8-10 ore · **Livello:** Avanzato

## Idee guida

1. **App Router + RSC = default.** Ogni componente e server component se non marcato `'use client'`.
2. **File-based routing con convenzioni.** `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx` — il filesystem e il router.
3. **Server Actions > API endpoints manuali.** Form submission, mutazione dati, revalidazione — tutto in-line.
4. **Caching stratificato.** Full Route Cache, Data Cache, Request Memoization, Router Cache — capirli tutti e quando invalidare.
5. **PPR (Partial Prerendering): il futuro.** Shell statica + streaming dinamico nella stessa route.

## Indice

1. [Architettura e App Router](#1-architettura-e-app-router)
2. [Struttura del Progetto](#2-struttura-del-progetto)
3. [Routing Avanzato](#3-routing-avanzato)
4. [Data Fetching](#4-data-fetching)
5. [Server Actions](#5-server-actions)
6. [Strategie di Rendering](#6-strategie-di-rendering)
7. [Middleware](#7-middleware)
8. [Route Handlers](#8-route-handlers)
9. [Ottimizzazione Immagini](#9-ottimizzazione-immagini)
10. [Ottimizzazione Font](#10-ottimizzazione-font)
11. [Metadata API](#11-metadata-api)
12. [Sistema di Caching](#12-sistema-di-caching)
13. [Autenticazione](#13-autenticazione)
14. [Integrazione Database](#14-integrazione-database)
15. [Deployment](#15-deployment)
16. [Internazionalizzazione](#16-internazionalizzazione)
17. [Testing](#17-testing)
18. [Performance](#18-performance)
19. [Migrazione da Pages Router](#19-migrazione-da-pages-router)
20. [Turbopack](#20-turbopack)
21. [Troubleshooting](#21-troubleshooting)
22. [FAQ](#22-faq)
23. [Best Practices e Anti-Pattern](#23-best-practices-e-anti-pattern)
24. [Esercizi](#24-esercizi)
25. [Letture e Risorse](#25-letture-e-risorse)
26. [Glossario](#26-glossario)

---

## 1. Architettura e App Router

### Panoramica dell'architettura

Next.js 15 e un framework full-stack costruito su React 19. L'architettura ruota attorno all'**App Router**, introdotto in Next.js 13 e ora stabile e raccomandato come approccio principale. L'App Router sostituisce il Pages Router precedente e porta un cambio di paradigma fondamentale: i **React Server Components (RSC)** sono il default.

In termini architetturali, Next.js opera su tre layer distinti:

- **Build layer**: compilazione, bundling, ottimizzazione statica. Turbopack (dev) o Webpack (production) generano il bundle finale.
- **Server layer**: rendering server-side, route handlers, server actions, middleware. Questo layer opera sia su Node.js runtime sia su Edge runtime.
- **Client layer**: hydration dei client components, interattivita, navigazione client-side tramite il router cache.

### App Router vs Pages Router

Il Pages Router (`pages/` directory) usava un modello piu semplice: ogni file in `pages/` era una route, i dati si recuperavano con `getServerSideProps` o `getStaticProps`, e tutti i componenti erano client components. Funzionava, ma aveva limitazioni strutturali: nessun supporto per layout condivisi senza workaround, impossibilita di fare streaming, nessuna granularita nel decidere cosa fosse server e cosa client.

L'App Router (`app/` directory) risolve tutto questo:

| Caratteristica | Pages Router | App Router |
|---|---|---|
| Default rendering | Client Components | Server Components |
| Data fetching | `getServerSideProps` / `getStaticProps` | `async` component + `fetch` |
| Layout | Workaround con `_app.tsx` | `layout.tsx` nativo |
| Loading UI | Manuale | `loading.tsx` automatico |
| Error handling | `_error.tsx` globale | `error.tsx` per-route |
| Streaming | Non supportato | Nativo con Suspense |
| Server Actions | Non disponibile | Nativo |
| Parallel Routes | Non disponibile | `@slot` convention |

### React Server Components come default

In Next.js 15 ogni componente nel directory `app/` e un Server Component a meno che non contenga la directive `'use client'` in cima al file. Questo significa:

- Il codice del componente viene eseguito **solo sul server**
- Il JavaScript del componente **non viene inviato al browser**
- Si puo accedere direttamente a database, filesystem, variabili d'ambiente server-only
- Non si possono usare hooks come `useState`, `useEffect`, event handlers (`onClick`, etc.)

```tsx
// app/dashboard/page.tsx
// Questo e un Server Component (default)
import { db } from '@/lib/db';

export default async function DashboardPage() {
  // Query diretta al database — codice mai inviato al client
  const stats = await db.stats.getLatest();

  return (
    <main>
      <h1>Dashboard</h1>
      <p>Utenti totali: {stats.totalUsers}</p>
      <p>Vendite oggi: {stats.salesToday}</p>
    </main>
  );
}
```

Quando serve interattivita (stato, effetti, event handler), si marca il componente come client:

```tsx
// app/dashboard/counter.tsx
'use client';

import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return (
    <button onClick={() => setCount((c) => c + 1)}>
      Contatore: {count}
    </button>
  );
}
```

La regola d'oro: **spostare `'use client'` il piu in basso possibile** nell'albero dei componenti. Il boundary `'use client'` e transitivo — tutto cio che un client component importa diventa client code.

---

## 2. Struttura del Progetto

### Directory `app/`

La struttura canonica di un progetto Next.js 15:

```
my-app/
├── app/
│   ├── layout.tsx          # Root layout (obbligatorio)
│   ├── page.tsx            # Home page (/)
│   ├── loading.tsx         # Loading UI globale
│   ├── error.tsx           # Error boundary globale
│   ├── not-found.tsx       # Pagina 404
│   ├── global-error.tsx    # Error boundary root (copre anche layout)
│   ├── favicon.ico
│   ├── globals.css
│   ├── about/
│   │   └── page.tsx        # /about
│   ├── blog/
│   │   ├── page.tsx        # /blog
│   │   ├── [slug]/
│   │   │   └── page.tsx    # /blog/:slug
│   │   └── layout.tsx      # Layout condiviso per /blog/*
│   ├── dashboard/
│   │   ├── layout.tsx
│   │   ├── page.tsx        # /dashboard
│   │   ├── settings/
│   │   │   └── page.tsx    # /dashboard/settings
│   │   └── @analytics/     # Parallel route
│   │       ├── page.tsx
│   │       └── loading.tsx
│   └── api/
│       └── webhooks/
│           └── route.ts    # Route handler: POST /api/webhooks
├── components/
│   ├── ui/                 # Componenti UI riutilizzabili
│   └── features/           # Componenti feature-specifici
├── lib/
│   ├── db.ts               # Database client
│   ├── auth.ts             # Configurazione auth
│   └── utils.ts            # Utility functions
├── public/
│   └── images/
├── next.config.ts
├── tsconfig.json
├── package.json
└── .env.local
```

### File convenzionali

Ogni segmento di route puo contenere file con nomi riservati che Next.js gestisce automaticamente:

| File | Scopo | Rendering |
|---|---|---|
| `page.tsx` | UI principale della route — rende la route accessibile | Server |
| `layout.tsx` | Layout condiviso, preserva stato tra navigazioni | Server |
| `template.tsx` | Come layout, ma rimonta ad ogni navigazione | Server |
| `loading.tsx` | Loading UI (wrappa `page.tsx` in Suspense) | Server |
| `error.tsx` | Error boundary per il segmento | **Client** |
| `not-found.tsx` | UI per `notFound()` | Server |
| `global-error.tsx` | Error boundary root (copre il root layout) | **Client** |
| `route.ts` | Route handler (API endpoint) | Server |
| `default.tsx` | Fallback per parallel routes | Server |

### Layout

I layout sono componenti che wrappano le pagine figlie e **persistono tra navigazioni**. Lo stato del layout non viene resettato quando l'utente naviga tra le pagine figlie — cio significa che un sidebar, un header o qualsiasi stato nel layout rimane intatto.

```tsx
// app/layout.tsx — Root Layout (obbligatorio)
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: {
    template: '%s | MiaSPA',
    default: 'MiaSPA',
  },
  description: 'La piattaforma SaaS definitiva',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="it">
      <body className={inter.className}>
        <header>
          <nav>{/* Navigazione globale */}</nav>
        </header>
        <main>{children}</main>
        <footer>{/* Footer globale */}</footer>
      </body>
    </html>
  );
}
```

```tsx
// app/dashboard/layout.tsx — Layout annidato
import { Sidebar } from '@/components/features/sidebar';
import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  if (!session) redirect('/login');

  return (
    <div className="flex">
      <Sidebar user={session.user} />
      <div className="flex-1 p-6">{children}</div>
    </div>
  );
}
```

### Loading UI

`loading.tsx` viene automaticamente wrappato in un `<Suspense>` boundary attorno a `page.tsx`. Viene mostrato immediatamente mentre il contenuto della pagina carica.

```tsx
// app/dashboard/loading.tsx
export default function DashboardLoading() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 w-48 rounded bg-gray-200" />
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 rounded bg-gray-200" />
        ))}
      </div>
    </div>
  );
}
```

### Error Boundary

`error.tsx` deve essere un client component. Cattura errori nel sotto-albero e mostra una UI di fallback.

```tsx
// app/dashboard/error.tsx
'use client';

import { useEffect } from 'react';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log errore a servizio di monitoring
    console.error('Dashboard error:', error);
  }, [error]);

  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-6">
      <h2 className="text-lg font-semibold text-red-800">
        Qualcosa e andato storto
      </h2>
      <p className="mt-2 text-red-600">{error.message}</p>
      <button
        onClick={reset}
        className="mt-4 rounded bg-red-600 px-4 py-2 text-white"
      >
        Riprova
      </button>
    </div>
  );
}
```

### Not Found

```tsx
// app/not-found.tsx
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold">404</h1>
        <p className="mt-4 text-lg text-gray-600">Pagina non trovata</p>
        <Link
          href="/"
          className="mt-6 inline-block rounded bg-blue-600 px-6 py-3 text-white"
        >
          Torna alla home
        </Link>
      </div>
    </div>
  );
}
```

---

## 3. Routing Avanzato

### Segmenti Dinamici

I segmenti dinamici si definiscono con parentesi quadre nel nome della cartella.

```tsx
// app/blog/[slug]/page.tsx
type Params = Promise<{ slug: string }>;

export default async function BlogPost({ params }: { params: Params }) {
  const { slug } = await params;
  const post = await getPost(slug);

  if (!post) {
    notFound();
  }

  return (
    <article>
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: post.contentHtml }} />
    </article>
  );
}

// Generazione statica dei path a build time
export async function generateStaticParams() {
  const posts = await getAllPosts();
  return posts.map((post) => ({ slug: post.slug }));
}
```

### Catch-All Segments

```tsx
// app/docs/[...slug]/page.tsx — cattura /docs/a, /docs/a/b, /docs/a/b/c
type Params = Promise<{ slug: string[] }>;

export default async function DocsPage({ params }: { params: Params }) {
  const { slug } = await params;
  // slug = ['getting-started'] per /docs/getting-started
  // slug = ['api', 'auth'] per /docs/api/auth
  const doc = await getDoc(slug.join('/'));
  return <div>{doc.content}</div>;
}
```

```tsx
// app/docs/[[...slug]]/page.tsx — optional catch-all
// Matcha anche /docs (slug = undefined)
```

### Route Groups

Le route groups permettono di organizzare le route senza influenzare l'URL. Si definiscono con parentesi tonde.

```
app/
├── (marketing)/
│   ├── layout.tsx         # Layout solo per marketing
│   ├── page.tsx           # / (home)
│   ├── about/
│   │   └── page.tsx       # /about
│   └── pricing/
│       └── page.tsx       # /pricing
├── (dashboard)/
│   ├── layout.tsx         # Layout solo per dashboard
│   ├── dashboard/
│   │   └── page.tsx       # /dashboard
│   └── settings/
│       └── page.tsx       # /settings
└── layout.tsx             # Root layout
```

Caso d'uso principale: layout diversi per sezioni diverse dell'applicazione (es. marketing con header pubblico, dashboard con sidebar autenticata).

### Parallel Routes

Le parallel routes permettono di renderizzare piu pagine contemporaneamente nello stesso layout, ognuna con il proprio loading ed error state.

```
app/
├── layout.tsx
├── page.tsx
├── @team/
│   ├── page.tsx
│   └── loading.tsx
├── @analytics/
│   ├── page.tsx
│   └── loading.tsx
└── @notifications/
    ├── page.tsx
    └── default.tsx
```

```tsx
// app/layout.tsx — accetta gli slot come props
export default function Layout({
  children,
  team,
  analytics,
  notifications,
}: {
  children: React.ReactNode;
  team: React.ReactNode;
  analytics: React.ReactNode;
  notifications: React.ReactNode;
}) {
  return (
    <div>
      {children}
      <div className="grid grid-cols-2 gap-4">
        {team}
        {analytics}
      </div>
      {notifications}
    </div>
  );
}
```

Il file `default.tsx` serve come fallback quando Next.js non riesce a determinare lo stato attivo di uno slot parallelo dopo una navigazione soft.

### Intercepting Routes

Le intercepting routes permettono di "intercettare" una navigazione e mostrare il contenuto in un contesto diverso (tipicamente un modale), preservando la possibilita di accedere alla route originale via URL diretto.

Convenzione:
- `(.)` — stesso livello
- `(..)` — un livello sopra
- `(..)(..)` — due livelli sopra
- `(...)` — root

```
app/
├── feed/
│   ├── page.tsx           # Feed principale
│   ├── @modal/
│   │   ├── default.tsx    # Nessun modale attivo
│   │   └── (.)photo/[id]/
│   │       └── page.tsx   # Modale foto (intercettato)
│   └── layout.tsx
└── photo/[id]/
    └── page.tsx           # Pagina foto completa (URL diretto)
```

```tsx
// app/feed/@modal/(.)photo/[id]/page.tsx
import { Modal } from '@/components/ui/modal';
import { getPhoto } from '@/lib/data';

type Params = Promise<{ id: string }>;

export default async function PhotoModal({ params }: { params: Params }) {
  const { id } = await params;
  const photo = await getPhoto(id);

  return (
    <Modal>
      <img src={photo.url} alt={photo.alt} />
      <p>{photo.description}</p>
    </Modal>
  );
}
```

```tsx
// app/feed/layout.tsx
export default function FeedLayout({
  children,
  modal,
}: {
  children: React.ReactNode;
  modal: React.ReactNode;
}) {
  return (
    <>
      {children}
      {modal}
    </>
  );
}
```

---

## 4. Data Fetching

### Fetch nei Server Components

In Next.js 15, il data fetching avviene direttamente nei Server Components usando `fetch` o qualsiasi libreria asincrona. Non servono piu `getServerSideProps` o `getStaticProps`.

```tsx
// app/products/page.tsx
interface Product {
  id: string;
  name: string;
  price: number;
}

export default async function ProductsPage() {
  const res = await fetch('https://api.example.com/products', {
    // Opzioni di caching Next.js-specifiche
    next: { revalidate: 3600 }, // ISR: rivalidazione ogni ora
  });

  if (!res.ok) {
    throw new Error('Errore nel caricamento prodotti');
  }

  const products: Product[] = await res.json();

  return (
    <ul>
      {products.map((product) => (
        <li key={product.id}>
          {product.name} — EUR {product.price.toFixed(2)}
        </li>
      ))}
    </ul>
  );
}
```

### Opzioni di caching per `fetch`

Next.js 15 ha cambiato il default di caching: `fetch` **non viene piu cachato automaticamente** (breaking change rispetto a Next 14). Per abilitare il caching bisogna essere espliciti.

```tsx
// Nessun caching (default in Next.js 15)
const data = await fetch('https://api.example.com/data');

// Cache statica — equivale a SSG
const data = await fetch('https://api.example.com/data', {
  cache: 'force-cache',
});

// Nessun caching esplicito — equivale a SSR
const data = await fetch('https://api.example.com/data', {
  cache: 'no-store',
});

// ISR — rivalidazione time-based
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 60 }, // Rivalidazione ogni 60 secondi
});

// Tagging per rivalidazione on-demand
const data = await fetch('https://api.example.com/data', {
  next: { tags: ['products'] },
});
```

### Rivalidazione on-demand

```tsx
// app/actions/revalidate.ts
'use server';

import { revalidateTag, revalidatePath } from 'next/cache';

export async function revalidateProducts() {
  // Rivalidazione per tag — invalida tutti i fetch con tag 'products'
  revalidateTag('products');
}

export async function revalidateProductPage(id: string) {
  // Rivalidazione per path — invalida una route specifica
  revalidatePath(`/products/${id}`);
}

export async function revalidateAllProducts() {
  // Rivalidazione di un intero layout
  revalidatePath('/products', 'layout');
}
```

### Data fetching con ORM (senza `fetch`)

Quando si usa un ORM come Prisma o Drizzle, non si passa per `fetch` e quindi le opzioni `next.revalidate` non sono disponibili. Si usa `unstable_cache` (o il nuovo `use cache` nelle versioni canary) per cachare i risultati.

```tsx
import { unstable_cache } from 'next/cache';
import { db } from '@/lib/db';

const getCachedProducts = unstable_cache(
  async () => {
    return db.product.findMany({
      orderBy: { createdAt: 'desc' },
      take: 50,
    });
  },
  ['products-list'], // Cache key
  {
    revalidate: 3600,   // 1 ora
    tags: ['products'], // Per rivalidazione on-demand
  }
);

export default async function ProductsPage() {
  const products = await getCachedProducts();
  return <ProductList products={products} />;
}
```

### Fetch in parallelo

Per evitare waterfall nei data fetching, usare `Promise.all` o `Promise.allSettled`:

```tsx
export default async function DashboardPage() {
  // BUONO: fetch in parallelo
  const [users, orders, revenue] = await Promise.all([
    getUsers(),
    getOrders(),
    getRevenue(),
  ]);

  return (
    <div>
      <UsersCard count={users.length} />
      <OrdersCard count={orders.length} />
      <RevenueCard total={revenue.total} />
    </div>
  );
}
```

```tsx
// CATTIVO: waterfall — ogni fetch aspetta il precedente
export default async function DashboardPage() {
  const users = await getUsers();       // 200ms
  const orders = await getOrders();     // 300ms
  const revenue = await getRevenue();   // 150ms
  // Totale: 650ms invece di ~300ms
}
```

### Streaming con Suspense

Per evitare che il fetch piu lento blocchi l'intera pagina, usare Suspense per lo streaming progressivo:

```tsx
import { Suspense } from 'react';

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      {/* Mostra subito */}
      <Suspense fallback={<CardSkeleton />}>
        <UsersCard />
      </Suspense>
      {/* Mostra quando pronto */}
      <Suspense fallback={<CardSkeleton />}>
        <RevenueCard />
      </Suspense>
      {/* Indipendente dagli altri */}
      <Suspense fallback={<TableSkeleton />}>
        <RecentOrders />
      </Suspense>
    </div>
  );
}

// Ogni componente fa il proprio fetch
async function UsersCard() {
  const users = await getUsers(); // Fetch indipendente
  return <div>Utenti: {users.length}</div>;
}
```

---

## 5. Server Actions

### Fondamenti

Le Server Actions sono funzioni asincrone eseguite sul server, invocabili direttamente dai componenti client o server. Sostituiscono la necessita di creare API endpoint manuali per le mutazioni di dati.

Si definiscono con la directive `'use server'` — a livello di file (tutte le export diventano server actions) o inline (singola funzione).

```tsx
// app/actions/user.ts
'use server';

import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const CreateUserSchema = z.object({
  name: z.string().min(2).max(100),
  email: z.string().email(),
});

export async function createUser(formData: FormData) {
  const rawData = {
    name: formData.get('name'),
    email: formData.get('email'),
  };

  // Validazione server-side — mai fidarsi dell'input
  const parsed = CreateUserSchema.safeParse(rawData);
  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  try {
    await db.user.create({ data: parsed.data });
    revalidatePath('/users');
    return { success: true };
  } catch (err) {
    return { error: { _form: ['Errore nella creazione utente'] } };
  }
}
```

### Form con Server Actions

Le Server Actions funzionano con il tag `<form>` nativo, abilitando la **progressive enhancement**: il form funziona anche senza JavaScript attivo nel browser.

```tsx
// app/users/new/page.tsx — Server Component con form
import { createUser } from '@/app/actions/user';

export default function NewUserPage() {
  return (
    <form action={createUser}>
      <label htmlFor="name">Nome</label>
      <input id="name" name="name" type="text" required />

      <label htmlFor="email">Email</label>
      <input id="email" name="email" type="email" required />

      <button type="submit">Crea Utente</button>
    </form>
  );
}
```

### useActionState

`useActionState` (React 19) gestisce lo stato del form, errori di validazione e pending state in un unico hook.

```tsx
// app/users/new/form.tsx
'use client';

import { useActionState } from 'react';
import { createUser } from '@/app/actions/user';

const initialState = {
  error: null as Record<string, string[]> | null,
  success: false,
};

export function CreateUserForm() {
  const [state, formAction, isPending] = useActionState(
    createUser,
    initialState
  );

  return (
    <form action={formAction}>
      <div>
        <label htmlFor="name">Nome</label>
        <input id="name" name="name" type="text" required />
        {state.error?.name && (
          <p className="text-red-500">{state.error.name[0]}</p>
        )}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" required />
        {state.error?.email && (
          <p className="text-red-500">{state.error.email[0]}</p>
        )}
      </div>

      <button type="submit" disabled={isPending}>
        {isPending ? 'Creazione...' : 'Crea Utente'}
      </button>

      {state.success && (
        <p className="text-green-600">Utente creato con successo!</p>
      )}
    </form>
  );
}
```

### useFormStatus

`useFormStatus` fornisce lo stato del form padre. Utile per bottoni di submit riutilizzabili.

```tsx
// components/ui/submit-button.tsx
'use client';

import { useFormStatus } from 'react-dom';

interface SubmitButtonProps {
  children: React.ReactNode;
  pendingText?: string;
}

export function SubmitButton({
  children,
  pendingText = 'Invio...',
}: SubmitButtonProps) {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
    >
      {pending ? pendingText : children}
    </button>
  );
}
```

### Optimistic Updates con useOptimistic

```tsx
// app/todos/todo-list.tsx
'use client';

import { useOptimistic, useRef } from 'react';
import { addTodo } from '@/app/actions/todo';

interface Todo {
  id: string;
  text: string;
  sending?: boolean;
}

export function TodoList({ todos }: { todos: Todo[] }) {
  const formRef = useRef<HTMLFormElement>(null);

  const [optimisticTodos, addOptimisticTodo] = useOptimistic(
    todos,
    (state: Todo[], newTodo: string) => [
      ...state,
      { id: crypto.randomUUID(), text: newTodo, sending: true },
    ]
  );

  async function handleSubmit(formData: FormData) {
    const text = formData.get('text') as string;
    addOptimisticTodo(text);
    formRef.current?.reset();
    await addTodo(formData);
  }

  return (
    <div>
      <ul>
        {optimisticTodos.map((todo) => (
          <li key={todo.id} className={todo.sending ? 'opacity-50' : ''}>
            {todo.text}
          </li>
        ))}
      </ul>
      <form ref={formRef} action={handleSubmit}>
        <input name="text" type="text" required />
        <button type="submit">Aggiungi</button>
      </form>
    </div>
  );
}
```

### Server Actions non-form

Le Server Actions possono essere invocate anche al di fuori dei form, tramite event handler.

```tsx
// app/posts/[id]/like-button.tsx
'use client';

import { useTransition } from 'react';
import { likePost } from '@/app/actions/post';

export function LikeButton({ postId }: { postId: string }) {
  const [isPending, startTransition] = useTransition();

  function handleLike() {
    startTransition(async () => {
      await likePost(postId);
    });
  }

  return (
    <button onClick={handleLike} disabled={isPending}>
      {isPending ? '...' : 'Like'}
    </button>
  );
}
```

---

## 6. Strategie di Rendering

### SSR — Server-Side Rendering

Rendering dinamico ad ogni richiesta. E il default quando un componente legge dati dinamici (cookies, headers, searchParams).

```tsx
// app/profile/page.tsx — SSR: legge cookies
import { cookies } from 'next/headers';

export default async function ProfilePage() {
  const cookieStore = await cookies();
  const theme = cookieStore.get('theme')?.value ?? 'light';

  return <div data-theme={theme}>Profilo utente</div>;
}
```

### SSG — Static Site Generation

Pagine generate a build time. Si ottiene quando non ci sono dati dinamici e il fetch e cachato.

```tsx
// app/docs/[slug]/page.tsx — SSG con generateStaticParams
import { getAllDocs, getDoc } from '@/lib/docs';

export async function generateStaticParams() {
  const docs = await getAllDocs();
  return docs.map((doc) => ({ slug: doc.slug }));
}

export default async function DocPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const doc = await getDoc(slug);
  return <article dangerouslySetInnerHTML={{ __html: doc.html }} />;
}
```

### ISR — Incremental Static Regeneration

Pagine statiche che si rigenerano dopo un intervallo di tempo. Combinazione di SSG e SSR.

```tsx
// ISR a livello di fetch
const data = await fetch('https://api.example.com/posts', {
  next: { revalidate: 60 },
});

// ISR a livello di route segment
export const revalidate = 60; // Rivalidazione ogni 60 secondi
```

### Streaming

Next.js supporta lo streaming nativo — il server invia l'HTML progressivamente al browser man mano che i dati sono disponibili. Si attiva automaticamente con `loading.tsx` o manualmente con `<Suspense>`.

```tsx
import { Suspense } from 'react';

export default function Page() {
  return (
    <div>
      {/* Inviato immediatamente */}
      <header>
        <h1>Dashboard</h1>
      </header>

      {/* Streamed quando pronto */}
      <Suspense fallback={<p>Caricamento metriche...</p>}>
        <SlowMetrics />
      </Suspense>

      {/* Streamed indipendentemente */}
      <Suspense fallback={<p>Caricamento tabella...</p>}>
        <SlowTable />
      </Suspense>
    </div>
  );
}
```

### PPR — Partial Prerendering

PPR combina rendering statico e dinamico nella **stessa route**. La shell statica viene servita immediatamente dall'edge cache, e le parti dinamiche vengono stremate dal server. A partire da Next.js 15, PPR e uscito dalla fase sperimentale iniziale ed e disponibile per l'adozione incrementale in produzione.

#### Adozione incrementale

Il modo consigliato per iniziare con PPR in Next.js 15 e l'adozione incrementale, che permette di attivare PPR route per route senza impattare l'intera applicazione:

```tsx
// next.config.ts
import type { NextConfig } from 'next';

const config: NextConfig = {
  experimental: {
    ppr: 'incremental', // Adozione route-by-route
  },
};

export default config;
```

Per attivare PPR su una route specifica, esportare la configurazione `experimental_ppr` dalla pagina o dal layout:

```tsx
// app/product/[id]/page.tsx
export const experimental_ppr = true;
```

Tutte le route figlie di un layout con `experimental_ppr = true` ereditano l'impostazione. Le route senza questa configurazione continuano a funzionare con il rendering tradizionale.

#### Come funziona PPR

Il meccanismo di PPR opera in tre fasi:

1. **Build time:** Next.js analizza la route e identifica le parti statiche (markup che non dipende da dati dinamici) e le parti dinamiche (componenti wrappati in `<Suspense>` che accedono a cookies, headers, searchParams o dati non cachati).
2. **Request time:** la shell statica viene servita immediatamente dalla CDN/edge cache con status 200. I boundary `<Suspense>` mostrano il fallback.
3. **Streaming:** le parti dinamiche vengono calcolate sul server e stremate progressivamente al browser, sostituendo i fallback con il contenuto reale.

Il vantaggio rispetto al rendering tradizionale e che il Time to First Byte (TTFB) e quasi istantaneo (shell statica dalla cache), mentre il contenuto personalizzato arriva in streaming senza bloccare l'intera pagina.

#### dynamicIO e il futuro del caching

Next.js 15 ha introdotto il concetto di `dynamicIO`, un flag sperimentale che inverte il modello di caching: tutto e dinamico per default, e il developer opta esplicitamente in nel caching con `'use cache'`. Questo flag e il precursore del sistema **Cache Components** (stabile in Next.js 16), che unifica PPR, `dynamicIO` e `unstable_cache` in un modello coerente.

```tsx
// next.config.ts — attivare dynamicIO (sperimentale in Next.js 15)
const config: NextConfig = {
  experimental: {
    dynamicIO: true,
  },
};
```

Con `dynamicIO` attivo, il data fetching e dinamico per default (nessun caching automatico), e si usa la direttiva `'use cache'` per dichiarare esplicitamente cosa cachare. Questo elimina la classe di bug legata all'over-caching che affliggeva Next.js 14.

#### Configurazione PPR globale

Per attivare PPR su tutte le route contemporaneamente:

```tsx
// next.config.ts
import type { NextConfig } from 'next';

const config: NextConfig = {
  experimental: {
    ppr: true, // Tutte le route usano PPR
  },
};

export default config;
```

```tsx
// app/product/[id]/page.tsx — PPR
import { Suspense } from 'react';
import { ProductDetails } from './product-details';
import { ProductReviews } from './product-reviews';
import { AddToCartButton } from './add-to-cart';

export default function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <div>
      {/* STATICO — prerendered, servito da edge cache */}
      <h1>Il Nostro Prodotto</h1>
      <nav>Breadcrumbs statici</nav>

      {/* DINAMICO — streamato dal server */}
      <Suspense fallback={<ProductDetailsSkeleton />}>
        <ProductDetails params={params} />
      </Suspense>

      {/* DINAMICO — utente-specifico */}
      <Suspense fallback={<ButtonSkeleton />}>
        <AddToCartButton params={params} />
      </Suspense>

      {/* DINAMICO — contenuto generato dagli utenti */}
      <Suspense fallback={<ReviewsSkeleton />}>
        <ProductReviews params={params} />
      </Suspense>
    </div>
  );
}
```

### Forzare rendering statico o dinamico

```tsx
// Forza rendering dinamico
export const dynamic = 'force-dynamic';

// Forza rendering statico
export const dynamic = 'force-static';

// Nessun caching dei dati
export const fetchCache = 'force-no-store';

// Timeout per il rendering dinamico (secondi)
export const maxDuration = 30;
```

---

## 7. Middleware

### Fondamenti

Il middleware in Next.js esegue codice **prima** che una richiesta venga completata. Gira sull'**Edge Runtime** (V8 isolates), il che significa: bassa latenza, ma API limitate (no fs, no moduli Node.js nativi).

Il file middleware deve trovarsi alla root del progetto (stesso livello di `app/`).

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Accesso a cookies, headers, URL
  const token = request.cookies.get('auth-token')?.value;

  // Redirect se non autenticato
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Modifica headers della risposta
  const response = NextResponse.next();
  response.headers.set('x-custom-header', 'valore');

  return response;
}

// Configurazione: su quali path eseguire il middleware
export const config = {
  matcher: [
    // Matcha tutto tranne file statici e API interne
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
```

### Casi d'uso comuni

**Autenticazione e protezione route:**

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { verifyToken } from '@/lib/auth-edge';

const protectedPaths = ['/dashboard', '/settings', '/admin'];
const adminPaths = ['/admin'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = protectedPaths.some((p) => pathname.startsWith(p));

  if (!isProtected) {
    return NextResponse.next();
  }

  const token = request.cookies.get('session')?.value;
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  const payload = await verifyToken(token);
  if (!payload) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Controllo ruolo admin
  const isAdmin = adminPaths.some((p) => pathname.startsWith(p));
  if (isAdmin && payload.role !== 'admin') {
    return NextResponse.redirect(new URL('/unauthorized', request.url));
  }

  // Inietta user info nei headers (leggibili dai Server Components)
  const headers = new Headers(request.headers);
  headers.set('x-user-id', payload.userId);
  headers.set('x-user-role', payload.role);

  return NextResponse.next({ request: { headers } });
}
```

**Internazionalizzazione:**

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { match } from '@formatjs/intl-localematcher';
import Negotiator from 'negotiator';

const locales = ['it', 'en', 'de', 'fr'];
const defaultLocale = 'it';

function getLocale(request: NextRequest): string {
  const headers = { 'accept-language': request.headers.get('accept-language') ?? '' };
  const languages = new Negotiator({ headers }).languages();
  return match(languages, locales, defaultLocale);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Controlla se il pathname ha gia un locale
  const hasLocale = locales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (hasLocale) return NextResponse.next();

  // Redirect al locale rilevato
  const locale = getLocale(request);
  request.nextUrl.pathname = `/${locale}${pathname}`;
  return NextResponse.redirect(request.nextUrl);
}

export const config = {
  matcher: ['/((?!_next|api|favicon.ico).*)'],
};
```

**Rate limiting semplice (Edge-compatible):**

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const rateLimit = new Map<string, { count: number; resetTime: number }>();

export function middleware(request: NextRequest) {
  if (!request.nextUrl.pathname.startsWith('/api')) {
    return NextResponse.next();
  }

  const ip = request.headers.get('x-forwarded-for') ?? 'unknown';
  const now = Date.now();
  const windowMs = 60_000; // 1 minuto
  const maxRequests = 60;

  const entry = rateLimit.get(ip);
  if (!entry || now > entry.resetTime) {
    rateLimit.set(ip, { count: 1, resetTime: now + windowMs });
    return NextResponse.next();
  }

  if (entry.count >= maxRequests) {
    return NextResponse.json(
      { error: 'Troppe richieste' },
      { status: 429, headers: { 'Retry-After': '60' } }
    );
  }

  entry.count++;
  return NextResponse.next();
}
```

> **Nota:** questo rate limiter in-memory funziona solo in ambiente single-instance. In produzione usare un servizio esterno (Redis via Upstash, Cloudflare, etc.).

### CSP Nonces via Middleware

Una Content Security Policy (CSP) robusta richiede un **nonce** unico per ogni richiesta, che autorizza solo gli script legittimi. Il middleware e il punto ideale per generare il nonce e iniettarlo negli header.

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Genera un nonce crittograficamente sicuro per ogni richiesta
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');

  // CSP con nonce — solo script con questo nonce vengono eseguiti
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic';
    style-src 'self' 'nonce-${nonce}';
    img-src 'self' blob: data:;
    font-src 'self';
    connect-src 'self';
    frame-src 'none';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
  `.replace(/\s{2,}/g, ' ').trim();

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-nonce', nonce);

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  });

  response.headers.set('Content-Security-Policy', cspHeader);
  return response;
}
```

Lettura del nonce nei Server Components:

```tsx
// app/layout.tsx
import { headers } from 'next/headers';
import Script from 'next/script';

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const headersList = await headers();
  const nonce = headersList.get('x-nonce') ?? '';

  return (
    <html lang="it">
      <body>
        {children}
        <Script
          src="https://analytics.example.com/script.js"
          strategy="afterInteractive"
          nonce={nonce}
        />
      </body>
    </html>
  );
}
```

### Sicurezza delle Server Actions

Next.js 15 migliora la sicurezza delle Server Actions con diverse misure:

**Crittografia degli ID delle azioni.** Ogni Server Action viene compilata con un ID univoco. Next.js 15 critta questi ID tra un build e l'altro per prevenire l'esposizione di endpoint interni. Ad ogni `next build`, viene generata una nuova chiave di crittografia, il che significa che le azioni non sono compatibili tra build diversi.

Per deployment multi-server (dove piu istanze devono condividere la stessa chiave), impostare la variabile d'ambiente:

```bash
# Chiave stabile tra build — necessaria per deployment rolling
# Deve essere una stringa crittograficamente sicura (es. 32+ byte hex)
NEXT_SERVER_ACTIONS_ENCRYPTION_KEY=$(openssl rand -hex 32)
```

**Dead code elimination.** Le Server Actions non referenziate vengono rimosse dal bundle, riducendo la superficie d'attacco. Next.js analizza staticamente quali azioni sono effettivamente importate e usate.

**Validazione degli input.** Validare sempre gli input delle Server Actions con Zod o librerie equivalenti. Non fidarsi mai dei dati provenienti dal client:

```tsx
'use server';

import { z } from 'zod';
import { headers } from 'next/headers';

const TransferSchema = z.object({
  amount: z.number().positive().max(10000),
  toAccountId: z.string().uuid(),
});

export async function transferFunds(formData: FormData) {
  // 1. Verifica autenticazione
  const headersList = await headers();
  const userId = headersList.get('x-user-id');
  if (!userId) {
    throw new Error('Non autenticato');
  }

  // 2. Valida input — mai fidarsi del client
  const parsed = TransferSchema.safeParse({
    amount: Number(formData.get('amount')),
    toAccountId: formData.get('toAccountId'),
  });
  if (!parsed.success) {
    return { error: 'Dati non validi' };
  }

  // 3. Verifica autorizzazione sull'account sorgente
  const account = await db.account.findFirst({
    where: { userId, balance: { gte: parsed.data.amount } },
  });
  if (!account) {
    return { error: 'Fondi insufficienti o account non trovato' };
  }

  // 4. Esegui transazione atomica
  await db.$transaction([
    db.account.update({
      where: { id: account.id },
      data: { balance: { decrement: parsed.data.amount } },
    }),
    db.account.update({
      where: { id: parsed.data.toAccountId },
      data: { balance: { increment: parsed.data.amount } },
    }),
  ]);

  revalidatePath('/dashboard');
  return { success: true };
}
```

---

## 8. Route Handlers

### Fondamenti

I Route Handlers sostituiscono le API Routes del Pages Router. Si definiscono in un file `route.ts` all'interno della directory `app/`.

```tsx
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { z } from 'zod';

// GET /api/users
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const page = parseInt(searchParams.get('page') ?? '1', 10);
  const limit = parseInt(searchParams.get('limit') ?? '20', 10);

  const users = await db.user.findMany({
    skip: (page - 1) * limit,
    take: limit,
    orderBy: { createdAt: 'desc' },
  });

  const total = await db.user.count();

  return NextResponse.json({
    data: users,
    meta: { page, limit, total, totalPages: Math.ceil(total / limit) },
  });
}

// POST /api/users
const CreateUserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

export async function POST(request: NextRequest) {
  const body = await request.json();
  const parsed = CreateUserSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.flatten().fieldErrors },
      { status: 400 }
    );
  }

  const user = await db.user.create({ data: parsed.data });
  return NextResponse.json({ data: user }, { status: 201 });
}
```

### Route Handlers con parametri dinamici

```tsx
// app/api/users/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server';

type Params = { params: Promise<{ id: string }> };

export async function GET(request: NextRequest, { params }: Params) {
  const { id } = await params;
  const user = await db.user.findUnique({ where: { id } });

  if (!user) {
    return NextResponse.json({ error: 'Utente non trovato' }, { status: 404 });
  }

  return NextResponse.json({ data: user });
}

export async function DELETE(request: NextRequest, { params }: Params) {
  const { id } = await params;
  await db.user.delete({ where: { id } });
  return new NextResponse(null, { status: 204 });
}
```

### Streaming Response

```tsx
// app/api/stream/route.ts
export async function GET() {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      for (let i = 0; i < 10; i++) {
        const chunk = encoder.encode(`data: Messaggio ${i}\n\n`);
        controller.enqueue(chunk);
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
```

### Webhook Handler

```tsx
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = request.headers.get('stripe-signature');

  if (!signature) {
    return NextResponse.json({ error: 'Firma mancante' }, { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    return NextResponse.json({ error: 'Firma non valida' }, { status: 400 });
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutComplete(session);
      break;
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      await handlePaymentFailed(invoice);
      break;
    }
  }

  return NextResponse.json({ received: true });
}
```

### CORS nei Route Handlers

```tsx
// app/api/public/route.ts
import { NextRequest, NextResponse } from 'next/server';

const allowedOrigins = ['https://app.example.com', 'https://staging.example.com'];

function corsHeaders(origin: string | null) {
  const headers = new Headers();
  if (origin && allowedOrigins.includes(origin)) {
    headers.set('Access-Control-Allow-Origin', origin);
  }
  headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  headers.set('Access-Control-Max-Age', '86400');
  return headers;
}

export async function OPTIONS(request: NextRequest) {
  const origin = request.headers.get('origin');
  return new NextResponse(null, { status: 204, headers: corsHeaders(origin) });
}

export async function GET(request: NextRequest) {
  const origin = request.headers.get('origin');
  const data = { message: 'Hello from API' };
  return NextResponse.json(data, { headers: corsHeaders(origin) });
}
```

---

## 9. Ottimizzazione Immagini

### next/image

Il componente `next/image` ottimizza automaticamente le immagini: conversione in formati moderni (WebP, AVIF), resize responsivo, lazy loading, prevenzione CLS.

```tsx
import Image from 'next/image';

// Immagine locale — dimensioni rilevate automaticamente
import heroImage from '@/public/images/hero.jpg';

export function Hero() {
  return (
    <Image
      src={heroImage}
      alt="Hero dell'applicazione"
      priority // Precarica (LCP image)
      placeholder="blur" // Blur placeholder automatico per immagini locali
      quality={85}
      className="rounded-lg"
    />
  );
}
```

```tsx
// Immagine remota — dimensioni obbligatorie
export function UserAvatar({ avatarUrl }: { avatarUrl: string }) {
  return (
    <Image
      src={avatarUrl}
      alt="Avatar utente"
      width={64}
      height={64}
      className="rounded-full"
    />
  );
}
```

### Immagini responsive con `sizes`

```tsx
export function ProductImage({ src, alt }: { src: string; alt: string }) {
  return (
    <Image
      src={src}
      alt={alt}
      width={800}
      height={600}
      sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
      className="w-full h-auto"
    />
  );
}
```

### Fill mode per container-based sizing

```tsx
export function BackgroundImage({ src }: { src: string }) {
  return (
    <div className="relative h-96 w-full">
      <Image
        src={src}
        alt="Background"
        fill
        className="object-cover"
        sizes="100vw"
      />
    </div>
  );
}
```

### Blur placeholder per immagini remote

```tsx
// Per immagini remote serve generare il blurDataURL manualmente
import { getPlaiceholder } from 'plaiceholder';

async function getBlurDataUrl(src: string): Promise<string> {
  const buffer = await fetch(src).then(async (res) =>
    Buffer.from(await res.arrayBuffer())
  );
  const { base64 } = await getPlaiceholder(buffer);
  return base64;
}

export default async function PhotoPage() {
  const blurDataURL = await getBlurDataUrl('https://example.com/photo.jpg');

  return (
    <Image
      src="https://example.com/photo.jpg"
      alt="Foto"
      width={1200}
      height={800}
      placeholder="blur"
      blurDataURL={blurDataURL}
    />
  );
}
```

### Configurazione domini remoti

```tsx
// next.config.ts
import type { NextConfig } from 'next';

const config: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.example.com',
        pathname: '/uploads/**',
      },
      {
        protocol: 'https',
        hostname: '*.cloudinary.com',
      },
    ],
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
};

export default config;
```

---

## 10. Ottimizzazione Font

### next/font

`next/font` scarica i font a build time e li serve come file statici — zero richieste esterne a runtime, niente layout shift da FOUT (Flash of Unstyled Text).

### Google Fonts

```tsx
// app/layout.tsx
import { Inter, Playfair_Display } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

const playfair = Playfair_Display({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-playfair',
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="it" className={`${inter.variable} ${playfair.variable}`}>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

```css
/* globals.css — utilizzo con CSS custom properties */
h1, h2, h3 {
  font-family: var(--font-playfair), serif;
}

body {
  font-family: var(--font-inter), sans-serif;
}
```

### Font locali

```tsx
import localFont from 'next/font/local';

const customFont = localFont({
  src: [
    {
      path: '../public/fonts/CustomFont-Regular.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../public/fonts/CustomFont-Bold.woff2',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../public/fonts/CustomFont-Italic.woff2',
      weight: '400',
      style: 'italic',
    },
  ],
  display: 'swap',
  variable: '--font-custom',
});
```

### Variable Fonts

```tsx
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  axes: ['slnt'], // Assi variabili aggiuntivi
  display: 'swap',
});
```

---

## 11. Metadata API

### Metadata statica

```tsx
// app/layout.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: {
    template: '%s | MiaSPA',
    default: 'MiaSPA — La Piattaforma SaaS',
  },
  description: 'Gestisci il tuo business con la piattaforma SaaS piu avanzata.',
  metadataBase: new URL('https://miaspa.example.com'),
  openGraph: {
    type: 'website',
    locale: 'it_IT',
    siteName: 'MiaSPA',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'MiaSPA Preview',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    creator: '@miaspa',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'codice-verifica-google',
  },
};
```

### Metadata dinamica

```tsx
// app/blog/[slug]/page.tsx
import type { Metadata } from 'next';
import { getPost } from '@/lib/posts';

type Params = Promise<{ slug: string }>;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(slug);

  if (!post) {
    return { title: 'Post non trovato' };
  }

  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      type: 'article',
      publishedTime: post.publishedAt.toISOString(),
      authors: [post.author.name],
      images: [
        {
          url: post.coverImage,
          width: 1200,
          height: 630,
          alt: post.title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: post.title,
      description: post.excerpt,
      images: [post.coverImage],
    },
  };
}
```

### JSON-LD Structured Data

```tsx
// app/blog/[slug]/page.tsx
import { getPost } from '@/lib/posts';

export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.excerpt,
    datePublished: post.publishedAt.toISOString(),
    dateModified: post.updatedAt.toISOString(),
    author: {
      '@type': 'Person',
      name: post.author.name,
    },
    image: post.coverImage,
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <article>
        <h1>{post.title}</h1>
        <div dangerouslySetInnerHTML={{ __html: post.contentHtml }} />
      </article>
    </>
  );
}
```

### Sitemap e Robots

```tsx
// app/sitemap.ts
import type { MetadataRoute } from 'next';
import { getAllPosts } from '@/lib/posts';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const posts = await getAllPosts();
  const baseUrl = 'https://miaspa.example.com';

  const postEntries = posts.map((post) => ({
    url: `${baseUrl}/blog/${post.slug}`,
    lastModified: post.updatedAt,
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }));

  return [
    { url: baseUrl, lastModified: new Date(), changeFrequency: 'daily', priority: 1 },
    { url: `${baseUrl}/about`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.5 },
    ...postEntries,
  ];
}
```

```tsx
// app/robots.ts
import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/dashboard/', '/api/', '/admin/'],
      },
    ],
    sitemap: 'https://miaspa.example.com/sitemap.xml',
  };
}
```

---

## 12. Sistema di Caching

### Panoramica dei layer di cache

Next.js 15 ha un sistema di caching stratificato. Capirlo e fondamentale per evitare bug di stale data o performance degradate.

| Layer | Dove | Cosa cacha | Durata | Invalidazione |
|---|---|---|---|---|
| **Request Memoization** | Server | Risultati `fetch` duplicati nella stessa render pass | Durata della richiesta | Automatica |
| **Data Cache** | Server | Risultati `fetch` persistenti | Persistente (o `revalidate`) | `revalidateTag()`, `revalidatePath()` |
| **Full Route Cache** | Server | HTML e RSC Payload delle route statiche | Persistente (fino a revalidation) | `revalidateTag()`, `revalidatePath()` |
| **Router Cache** | Client (browser) | RSC Payload delle route visitate | Sessione (30s dynamic, 5min static) | `router.refresh()`, `revalidatePath()` |

### Request Memoization

React e Next.js deduplicano automaticamente le chiamate `fetch` con lo stesso URL e opzioni all'interno della stessa render pass. Questo significa che si puo chiamare la stessa fetch in piu componenti senza overhead.

```tsx
// Entrambi i componenti chiamano lo stesso endpoint
// ma la fetch viene eseguita UNA sola volta

async function UserName() {
  const user = await fetch('/api/user').then((r) => r.json());
  return <p>{user.name}</p>;
}

async function UserAvatar() {
  // Stessa URL — deduplicata automaticamente
  const user = await fetch('/api/user').then((r) => r.json());
  return <img src={user.avatar} alt={user.name} />;
}
```

La memoization si applica **solo** a `fetch` con metodo `GET`. Per ORM queries bisogna usare `React.cache()`:

```tsx
import { cache } from 'react';
import { db } from '@/lib/db';

// Deduplicazione manuale per query non-fetch
export const getUser = cache(async (id: string) => {
  return db.user.findUnique({ where: { id } });
});
```

### Data Cache

Il Data Cache persiste i risultati delle `fetch` tra richieste e deployment. In Next.js 15, il default e **non cachare** (`no-store`). Per attivare il caching:

```tsx
// Cachata indefinitamente
const data = await fetch(url, { cache: 'force-cache' });

// Cachata per 60 secondi
const data = await fetch(url, { next: { revalidate: 60 } });

// Con tag per invalidazione
const data = await fetch(url, { next: { tags: ['users'] } });
```

### Full Route Cache

Le route completamente statiche (nessuna funzione dinamica) vengono pre-renderizzate a build time. L'HTML e il RSC Payload vengono cachati e serviti senza rieseguire il rendering.

Funzioni che rendono una route dinamica (invalidano il Full Route Cache):
- `cookies()`
- `headers()`
- `searchParams`
- `connection()`
- `unstable_noStore()`

### Router Cache (Client-side)

Il browser cacha i payload RSC delle route navigate. Quando l'utente torna a una pagina gia visitata, il contenuto viene mostrato istantaneamente dalla cache locale.

In Next.js 15 il comportamento e cambiato:
- Le route **statiche** sono cachate per 5 minuti
- Le route **dinamiche** sono cachate per 30 secondi (impostazione `staleTimes`)
- Si puo personalizzare via `next.config.ts`:

```tsx
// next.config.ts
const config: NextConfig = {
  experimental: {
    staleTimes: {
      dynamic: 0,   // Disabilita cache per route dinamiche
      static: 300,  // 5 minuti per route statiche
    },
  },
};
```

### Invalidazione della cache

```tsx
// Server Action o Route Handler
'use server';

import { revalidateTag, revalidatePath } from 'next/cache';

// Per tag — invalida tutti i fetch con quel tag
export async function updateProduct(id: string, data: ProductData) {
  await db.product.update({ where: { id }, data });
  revalidateTag('products');      // Tutti i fetch con tag 'products'
  revalidateTag(`product-${id}`); // Fetch specifico del prodotto
}

// Per path — invalida una route specifica
export async function deleteProduct(id: string) {
  await db.product.delete({ where: { id } });
  revalidatePath('/products');           // Solo /products
  revalidatePath('/products', 'layout'); // /products e tutte le sotto-route
}
```

### Opt-out dal caching

```tsx
// A livello di route segment
export const dynamic = 'force-dynamic'; // Nessun caching per la route
export const revalidate = 0;            // Equivalente

// A livello di singolo fetch
const data = await fetch(url, { cache: 'no-store' });

// Con unstable_noStore() per codice non-fetch
import { unstable_noStore } from 'next/cache';

async function getData() {
  unstable_noStore();
  return db.user.findMany();
}
```

### La direttiva `'use cache'`

Con l'introduzione di `dynamicIO` (descritto nella sezione 6), Next.js 15 ha introdotto un nuovo modello di caching esplicito basato sulla direttiva `'use cache'`. Invece del vecchio approccio dove il framework decideva automaticamente cosa cachare (causando bug di over-caching in Next.js 14), ora il developer dichiara esplicitamente cosa cachare.

La direttiva `'use cache'` si puo applicare a tre livelli:

**1. A livello di file** — tutto il modulo viene cachato:

```tsx
'use cache';

export default async function ProductCatalog() {
  const products = await db.product.findMany();
  return (
    <ul>
      {products.map((p) => (
        <li key={p.id}>{p.name} — {p.price} EUR</li>
      ))}
    </ul>
  );
}
```

**2. A livello di componente** — singolo componente cachato:

```tsx
async function CachedSidebar() {
  'use cache';
  const categories = await db.category.findMany();
  return (
    <nav>
      {categories.map((c) => (
        <a key={c.id} href={`/categoria/${c.slug}`}>{c.name}</a>
      ))}
    </nav>
  );
}
```

**3. A livello di funzione** — cache granulare su singola funzione:

```tsx
async function getProductById(id: string) {
  'use cache';
  return db.product.findUnique({ where: { id } });
}
```

> **Nota:** `'use cache'` richiede il flag `dynamicIO` attivo in `next.config.ts`. Senza `dynamicIO`, il sistema di caching usa il modello tradizionale basato su `fetch` options e `unstable_cache`.

#### `cacheLife` — Profili di durata della cache

`cacheLife` definisce per quanto tempo un risultato cachato resta valido. Next.js include profili predefiniti, e se ne possono creare di personalizzati.

**Profili built-in:**

| Profilo | `stale` (client) | `revalidate` (server) | `expire` (max) |
|---|---|---|---|
| `"default"` | 5 minuti | 15 minuti | indefinito |
| `"seconds"` | 0 | 1 secondo | 1 secondo |
| `"minutes"` | 5 minuti | 1 minuto | 1 ora |
| `"hours"` | 5 minuti | 1 ora | 1 giorno |
| `"days"` | 5 minuti | 1 giorno | 1 settimana |
| `"weeks"` | 5 minuti | 1 settimana | 1 mese |
| `"max"` | 5 minuti | 1 mese | indefinito |

```tsx
import { cacheLife } from 'next/cache';

async function getExchangeRates() {
  'use cache';
  cacheLife('minutes'); // Rinnova ogni minuto, stale per 5 min client-side
  const res = await fetch('https://api.exchange.example/rates');
  return res.json();
}
```

**Profili personalizzati** — si definiscono in `next.config.ts`:

```tsx
// next.config.ts
const config: NextConfig = {
  experimental: {
    dynamicIO: true,
    cacheLife: {
      catalog: {
        stale: 300,      // 5 minuti client stale
        revalidate: 900,  // 15 minuti revalidazione server
        expire: 86400,    // 24 ore durata massima
      },
      realtime: {
        stale: 0,
        revalidate: 1,
        expire: 60,
      },
    },
  },
};
```

```tsx
import { cacheLife } from 'next/cache';

async function getProductCatalog() {
  'use cache';
  cacheLife('catalog'); // Usa il profilo personalizzato
  return db.product.findMany({ where: { active: true } });
}
```

Si possono anche passare valori inline senza definire un profilo:

```tsx
import { cacheLife } from 'next/cache';

async function getWeather(city: string) {
  'use cache';
  cacheLife({ stale: 60, revalidate: 300, expire: 3600 });
  const res = await fetch(`https://weather.example/api/${city}`);
  return res.json();
}
```

#### `cacheTag` — Invalidazione granulare per tag

`cacheTag` assegna tag a un risultato cachato, permettendo invalidazione mirata tramite `revalidateTag()`. A differenza del vecchio sistema basato su `fetch` tags, `cacheTag` funziona con qualsiasi dato cachato via `'use cache'`, incluse query ORM.

```tsx
import { cacheTag } from 'next/cache';

async function getProduct(id: string) {
  'use cache';
  cacheTag('products', `product-${id}`);
  return db.product.findUnique({ where: { id } });
}
```

Invalidazione in una Server Action:

```tsx
'use server';

import { revalidateTag } from 'next/cache';

export async function updateProduct(id: string, data: ProductData) {
  await db.product.update({ where: { id }, data });

  // Invalida sia la lista che il singolo prodotto
  revalidateTag('products');
  revalidateTag(`product-${id}`);
}
```

**Pattern completo — componente con `'use cache'`, `cacheLife` e `cacheTag`:**

```tsx
import { cacheLife, cacheTag } from 'next/cache';

async function ProductGrid({ categoryId }: { categoryId: string }) {
  'use cache';
  cacheLife('catalog');
  cacheTag('products', `category-${categoryId}`);

  const products = await db.product.findMany({
    where: { categoryId, active: true },
    orderBy: { createdAt: 'desc' },
  });

  return (
    <div className="grid grid-cols-3 gap-4">
      {products.map((p) => (
        <article key={p.id}>
          <h3>{p.name}</h3>
          <p>{p.price} EUR</p>
        </article>
      ))}
    </div>
  );
}
```

---

## 13. Autenticazione

### NextAuth.js v5 (Auth.js)

Auth.js v5 e il successore di NextAuth.js, completamente riscritto per supportare nativamente l'App Router e l'Edge Runtime.

```bash
npm install next-auth@beta
```

```tsx
// auth.ts (root del progetto)
import NextAuth from 'next-auth';
import GitHub from 'next-auth/providers/github';
import Google from 'next-auth/providers/google';
import Credentials from 'next-auth/providers/credentials';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/db';
import { z } from 'zod';
import bcrypt from 'bcryptjs';

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  session: { strategy: 'jwt' },
  pages: {
    signIn: '/login',
    error: '/auth/error',
  },
  providers: [
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    Credentials({
      async authorize(credentials) {
        const parsed = z
          .object({
            email: z.string().email(),
            password: z.string().min(8),
          })
          .safeParse(credentials);

        if (!parsed.success) return null;

        const user = await prisma.user.findUnique({
          where: { email: parsed.data.email },
        });

        if (!user?.hashedPassword) return null;

        const isValid = await bcrypt.compare(
          parsed.data.password,
          user.hashedPassword
        );

        return isValid ? user : null;
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.id = token.sub!;
      session.user.role = token.role as string;
      return session;
    },
  },
});
```

```tsx
// app/api/auth/[...nextauth]/route.ts
import { handlers } from '@/auth';

export const { GET, POST } = handlers;
```

### Protezione route con middleware

```tsx
// middleware.ts
import { auth } from '@/auth';

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isOnDashboard = req.nextUrl.pathname.startsWith('/dashboard');

  if (isOnDashboard && !isLoggedIn) {
    return Response.redirect(new URL('/login', req.nextUrl));
  }
});

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

### Accesso alla sessione nei Server Components

```tsx
// app/dashboard/page.tsx
import { auth } from '@/auth';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const session = await auth();

  if (!session) {
    redirect('/login');
  }

  return (
    <div>
      <h1>Benvenuto, {session.user.name}</h1>
      <p>Ruolo: {session.user.role}</p>
    </div>
  );
}
```

### Componenti client con sessione

```tsx
// app/components/user-menu.tsx
'use client';

import { useSession, signOut } from 'next-auth/react';

export function UserMenu() {
  const { data: session, status } = useSession();

  if (status === 'loading') return <div>Caricamento...</div>;
  if (!session) return <a href="/login">Accedi</a>;

  return (
    <div>
      <span>{session.user.name}</span>
      <button onClick={() => signOut()}>Esci</button>
    </div>
  );
}
```

```tsx
// app/layout.tsx — SessionProvider per i client components
import { SessionProvider } from 'next-auth/react';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
```

---

## 14. Integrazione Database

### Prisma

```tsx
// lib/db.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query'] : [],
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}
```

Il pattern `globalForPrisma` evita la creazione di connessioni multiple durante il hot reload in development.

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  role      String   @default("user")
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Post {
  id        String   @id @default(cuid())
  title     String
  content   String?
  published Boolean  @default(false)
  authorId  String
  author    User     @relation(fields: [authorId], references: [id])
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

### Drizzle ORM

Alternativa type-safe e leggera a Prisma, con query builder SQL-like.

```tsx
// lib/db.ts
import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from './schema';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
});

export const db = drizzle(pool, { schema });
```

```tsx
// lib/schema.ts
import { pgTable, text, timestamp, boolean } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text('email').notNull().unique(),
  name: text('name'),
  role: text('role').notNull().default('user'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

export const posts = pgTable('posts', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  title: text('title').notNull(),
  content: text('content'),
  published: boolean('published').notNull().default(false),
  authorId: text('author_id')
    .notNull()
    .references(() => users.id),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});
```

```tsx
// Utilizzo in un Server Component
import { db } from '@/lib/db';
import { users, posts } from '@/lib/schema';
import { eq, desc } from 'drizzle-orm';

export default async function UserPostsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const userPosts = await db
    .select()
    .from(posts)
    .where(eq(posts.authorId, id))
    .orderBy(desc(posts.createdAt));

  return (
    <ul>
      {userPosts.map((post) => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}
```

#### Relazioni in Drizzle

Drizzle supporta relazioni dichiarative tramite il modulo `relations`, separato dalla definizione delle tabelle:

```tsx
// lib/schema.ts — relazioni
import { relations } from 'drizzle-orm';
import { users, posts } from './tables';

export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
}));
```

Query con relazioni (Relational Query API):

```tsx
// Query con eager loading delle relazioni
const usersWithPosts = await db.query.users.findMany({
  with: {
    posts: {
      where: (posts, { eq }) => eq(posts.published, true),
      orderBy: (posts, { desc }) => [desc(posts.createdAt)],
      limit: 10,
    },
  },
});
```

#### Transazioni con Drizzle

```tsx
// Transazione atomica — tutto o niente
async function transferCredits(fromId: string, toId: string, amount: number) {
  await db.transaction(async (tx) => {
    const sender = await tx
      .select()
      .from(users)
      .where(eq(users.id, fromId))
      .for('update'); // Lock pessimistico

    if (!sender[0] || sender[0].credits < amount) {
      tx.rollback();
      return;
    }

    await tx
      .update(users)
      .set({ credits: sql`${users.credits} - ${amount}` })
      .where(eq(users.id, fromId));

    await tx
      .update(users)
      .set({ credits: sql`${users.credits} + ${amount}` })
      .where(eq(users.id, toId));
  });
}
```

#### Server Actions con Drizzle e Zod

Pattern completo per mutazioni type-safe con validazione:

```tsx
// app/actions/posts.ts
'use server';

import { db } from '@/lib/db';
import { posts } from '@/lib/schema';
import { eq } from 'drizzle-orm';
import { revalidateTag } from 'next/cache';
import { z } from 'zod';

const CreatePostSchema = z.object({
  title: z.string().min(3).max(200),
  content: z.string().min(10),
  categoryId: z.string().uuid(),
});

export async function createPost(formData: FormData) {
  const parsed = CreatePostSchema.safeParse({
    title: formData.get('title'),
    content: formData.get('content'),
    categoryId: formData.get('categoryId'),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  const [newPost] = await db
    .insert(posts)
    .values({
      ...parsed.data,
      authorId: await getCurrentUserId(),
    })
    .returning();

  revalidateTag('posts');
  return { success: true, postId: newPost.id };
}
```

#### Migrazioni con Drizzle Kit

```bash
# Genera migrazione SQL dalle differenze nello schema
npx drizzle-kit generate

# Applica le migrazioni pendenti
npx drizzle-kit migrate

# Visualizza lo schema nel browser (Drizzle Studio)
npx drizzle-kit studio
```

```tsx
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './lib/schema.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

### Connection Pooling

In ambienti serverless (Vercel, AWS Lambda), ogni invocazione apre una nuova connessione al database. Senza pooling, si esauriscono rapidamente le connessioni.

Soluzioni:
- **Prisma Accelerate** o **Neon Serverless Driver** — pooling gestito dal provider
- **PgBouncer** — proxy di connection pooling self-hosted
- **Supabase** — include pgBouncer integrato

```tsx
// Neon serverless driver con Drizzle
import { neon } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-http';

const sql = neon(process.env.DATABASE_URL!);
export const db = drizzle(sql);
```

---

## 15. Deployment

### Vercel (Piattaforma nativa)

Vercel e la piattaforma creata dal team di Next.js. Il deployment e automatico:

```bash
# CLI
npm i -g vercel
vercel
```

Configurazione environment variables nel dashboard Vercel o via CLI:

```bash
vercel env add DATABASE_URL production
vercel env add NEXTAUTH_SECRET production
```

### Self-hosted con standalone mode

```tsx
// next.config.ts
const config: NextConfig = {
  output: 'standalone',
};
```

```bash
npm run build
# L'output standalone e in .next/standalone/
node .next/standalone/server.js
```

### Docker

```dockerfile
# Dockerfile
FROM node:20-alpine AS base

# Fase 1: installazione dipendenze
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Fase 2: build
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Fase 3: runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - '3000:3000'
    env_file: .env.production
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ['CMD', 'wget', '-q', '--spider', 'http://localhost:3000/api/health']
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U myapp']
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### Edge Deployment

Per route handlers e middleware che girano sull'Edge Runtime:

```tsx
// app/api/edge-endpoint/route.ts
export const runtime = 'edge';

export async function GET() {
  return new Response('Hello from the Edge!');
}
```

L'Edge Runtime ha limitazioni: no `fs`, no moduli Node.js nativi, dimensione massima del bundle ridotta. Usare solo quando la latenza e critica.

### Health Check Endpoint

```tsx
// app/api/health/route.ts
import { db } from '@/lib/db';

export async function GET() {
  try {
    // Verifica connessione database
    await db.$queryRaw`SELECT 1`;

    return Response.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    });
  } catch {
    return Response.json(
      { status: 'unhealthy', timestamp: new Date().toISOString() },
      { status: 503 }
    );
  }
}
```

---

## 16. Internazionalizzazione

### Struttura con sub-path routing

```
app/
├── [locale]/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── about/
│   │   └── page.tsx
│   └── blog/
│       └── page.tsx
├── layout.tsx          # Root layout minimale
└── not-found.tsx
```

### Configurazione

```tsx
// lib/i18n/config.ts
export const locales = ['it', 'en', 'de', 'fr'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'it';
```

### Dizionari di traduzione

```tsx
// lib/i18n/dictionaries.ts
const dictionaries = {
  it: () => import('./dictionaries/it.json').then((m) => m.default),
  en: () => import('./dictionaries/en.json').then((m) => m.default),
  de: () => import('./dictionaries/de.json').then((m) => m.default),
  fr: () => import('./dictionaries/fr.json').then((m) => m.default),
};

export async function getDictionary(locale: Locale) {
  return dictionaries[locale]();
}
```

```json
// lib/i18n/dictionaries/it.json
{
  "nav": {
    "home": "Home",
    "about": "Chi siamo",
    "blog": "Blog",
    "contact": "Contatti"
  },
  "home": {
    "title": "Benvenuto nella nostra piattaforma",
    "subtitle": "La soluzione migliore per il tuo business",
    "cta": "Inizia ora"
  },
  "common": {
    "loading": "Caricamento...",
    "error": "Si e verificato un errore",
    "retry": "Riprova"
  }
}
```

### Layout con locale

```tsx
// app/[locale]/layout.tsx
import { notFound } from 'next/navigation';
import { locales, type Locale } from '@/lib/i18n/config';

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!locales.includes(locale as Locale)) {
    notFound();
  }

  return (
    <html lang={locale}>
      <body>{children}</body>
    </html>
  );
}
```

### Pagina con traduzioni

```tsx
// app/[locale]/page.tsx
import { getDictionary } from '@/lib/i18n/dictionaries';
import type { Locale } from '@/lib/i18n/config';

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const dict = await getDictionary(locale as Locale);

  return (
    <main>
      <h1>{dict.home.title}</h1>
      <p>{dict.home.subtitle}</p>
      <a href={`/${locale}/about`}>{dict.home.cta}</a>
    </main>
  );
}
```

### Formattazione date e numeri

```tsx
// lib/i18n/formatters.ts
export function formatDate(date: Date, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

export function formatCurrency(
  amount: number,
  locale: string,
  currency: string = 'EUR'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount);
}
```

### Alternare lingua

```tsx
// components/locale-switcher.tsx
'use client';

import { usePathname, useRouter } from 'next/navigation';
import { locales, type Locale } from '@/lib/i18n/config';

export function LocaleSwitcher({ currentLocale }: { currentLocale: Locale }) {
  const pathname = usePathname();
  const router = useRouter();

  function switchLocale(newLocale: Locale) {
    // Sostituisce il locale corrente nel path
    const segments = pathname.split('/');
    segments[1] = newLocale;
    router.push(segments.join('/'));
  }

  return (
    <select
      value={currentLocale}
      onChange={(e) => switchLocale(e.target.value as Locale)}
    >
      {locales.map((locale) => (
        <option key={locale} value={locale}>
          {locale.toUpperCase()}
        </option>
      ))}
    </select>
  );
}
```

---

## 17. Testing

### Setup Jest + React Testing Library

```bash
npm install -D jest @testing-library/react @testing-library/jest-dom \
  jest-environment-jsdom @types/jest ts-jest
```

```tsx
// jest.config.ts
import type { Config } from 'jest';
import nextJest from 'next/jest';

const createJestConfig = nextJest({
  dir: './',
});

const config: Config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};

export default createJestConfig(config);
```

```tsx
// jest.setup.ts
import '@testing-library/jest-dom';
```

### Testing di componenti

```tsx
// components/ui/__tests__/button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SubmitButton } from '@/components/ui/submit-button';

// Mock di useFormStatus
jest.mock('react-dom', () => ({
  ...jest.requireActual('react-dom'),
  useFormStatus: jest.fn(),
}));

import { useFormStatus } from 'react-dom';
const mockUseFormStatus = useFormStatus as jest.Mock;

describe('SubmitButton', () => {
  it('mostra il testo del bottone quando non in pending', () => {
    mockUseFormStatus.mockReturnValue({ pending: false });

    render(<SubmitButton>Invia</SubmitButton>);
    expect(screen.getByRole('button')).toHaveTextContent('Invia');
    expect(screen.getByRole('button')).not.toBeDisabled();
  });

  it('mostra il testo di pending e disabilita il bottone', () => {
    mockUseFormStatus.mockReturnValue({ pending: true });

    render(<SubmitButton pendingText="Invio in corso...">Invia</SubmitButton>);
    expect(screen.getByRole('button')).toHaveTextContent('Invio in corso...');
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### Testing di Server Components

I Server Components asincroni richiedono un approccio diverso:

```tsx
// app/products/__tests__/page.test.tsx
import { render, screen } from '@testing-library/react';
import ProductsPage from '@/app/products/page';

// Mock del modulo di data fetching
jest.mock('@/lib/data', () => ({
  getProducts: jest.fn().mockResolvedValue([
    { id: '1', name: 'Prodotto A', price: 29.99 },
    { id: '2', name: 'Prodotto B', price: 49.99 },
  ]),
}));

describe('ProductsPage', () => {
  it('mostra la lista dei prodotti', async () => {
    const Component = await ProductsPage();
    render(Component);

    expect(screen.getByText('Prodotto A')).toBeInTheDocument();
    expect(screen.getByText('Prodotto B')).toBeInTheDocument();
  });
});
```

### E2E con Playwright

```bash
npm install -D @playwright/test
npx playwright install
```

```tsx
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile', use: { ...devices['iPhone 14'] } },
  ],
  webServer: {
    command: 'npm run build && npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

```tsx
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Autenticazione', () => {
  test('redirect a login se non autenticato', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('login con credenziali valide', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Accedi' }).click();

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Benvenuto')).toBeVisible();
  });

  test('mostra errore con credenziali non valide', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('wrong@example.com');
    await page.getByLabel('Password').fill('wrongpass');
    await page.getByRole('button', { name: 'Accedi' }).click();

    await expect(page.getByText('Credenziali non valide')).toBeVisible();
  });
});
```

### MSW (Mock Service Worker) per mock API

```tsx
// mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: '1', name: 'Mario Rossi', email: 'mario@example.com' },
      { id: '2', name: 'Giulia Bianchi', email: 'giulia@example.com' },
    ]);
  }),

  http.post('/api/users', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(
      { id: '3', ...body },
      { status: 201 }
    );
  }),
];
```

```tsx
// mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

```tsx
// jest.setup.ts
import { server } from './mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Strategie di testing avanzate con Playwright

Oltre ai test di autenticazione base, Playwright eccelle nei test di navigazione, accessibilita e visual regression per applicazioni Next.js.

**Test di navigazione e layout:**

```tsx
// e2e/navigation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Navigazione App Router', () => {
  test('navigazione client-side non ricarica la pagina', async ({ page }) => {
    await page.goto('/');

    // Intercetta network per verificare che non avvenga un full page load
    const navigationPromise = page.waitForURL('/products');
    await page.getByRole('link', { name: 'Prodotti' }).click();
    await navigationPromise;

    // Il layout root non deve ri-renderizzare
    await expect(page.getByRole('banner')).toBeVisible();
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Prodotti');
  });

  test('loading.tsx mostra skeleton durante navigazione', async ({ page }) => {
    await page.goto('/');

    // Rallenta la risposta del server per catturare il loading state
    await page.route('**/products**', async (route) => {
      await new Promise((r) => setTimeout(r, 1000));
      await route.continue();
    });

    await page.getByRole('link', { name: 'Prodotti' }).click();
    // Verifica che il loading skeleton appaia
    await expect(page.getByTestId('products-skeleton')).toBeVisible();
    // Poi scompare quando i dati arrivano
    await expect(page.getByTestId('products-skeleton')).toBeHidden({ timeout: 5000 });
  });
});
```

**Test di accessibilita con axe-core:**

```bash
npm install -D @axe-core/playwright
```

```tsx
// e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibilita', () => {
  test('home page non ha violazioni a11y', async ({ page }) => {
    await page.goto('/');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });

  test('form di login ha label corretti', async ({ page }) => {
    await page.goto('/login');
    const results = await new AxeBuilder({ page })
      .include('form')
      .analyze();
    expect(results.violations).toEqual([]);
  });
});
```

### Configurazione `next/jest` avanzata

Il pacchetto `next/jest` configura automaticamente Jest per Next.js, gestendo transform, module mapping e l'ambiente jsdom. Configurazioni avanzate:

```tsx
// jest.config.ts
import type { Config } from 'jest';
import nextJest from 'next/jest';

const createJestConfig = nextJest({ dir: './' });

const config: Config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  // Escludi file di test E2E (gestiti da Playwright)
  testPathIgnorePatterns: ['<rootDir>/e2e/'],
  // Raccogli coverage solo dal codice sorgente
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
};

export default createJestConfig(config);
```

**Testing di Server Actions con mock:**

```tsx
// app/actions/__tests__/user.test.ts
import { createUser } from '../user';

// Mock del modulo database
jest.mock('@/lib/db', () => ({
  db: {
    user: {
      create: jest.fn().mockResolvedValue({ id: '1', name: 'Test' }),
    },
  },
}));

// Mock di revalidatePath
jest.mock('next/cache', () => ({
  revalidatePath: jest.fn(),
}));

describe('createUser Server Action', () => {
  it('crea utente con dati validi', async () => {
    const formData = new FormData();
    formData.set('name', 'Mario Rossi');
    formData.set('email', 'mario@example.com');

    const result = await createUser(formData);
    expect(result).toEqual({ success: true });
  });

  it('restituisce errore con email non valida', async () => {
    const formData = new FormData();
    formData.set('name', 'Mario');
    formData.set('email', 'non-una-email');

    const result = await createUser(formData);
    expect(result.error).toBeDefined();
  });
});
```

---

## 18. Performance

### Bundle Analysis

```bash
npm install -D @next/bundle-analyzer
```

```tsx
// next.config.ts
import withBundleAnalyzer from '@next/bundle-analyzer';

const config: NextConfig = {
  // ...configurazione
};

export default process.env.ANALYZE === 'true'
  ? withBundleAnalyzer({ enabled: true })(config)
  : config;
```

```bash
ANALYZE=true npm run build
```

### Core Web Vitals

```tsx
// app/components/web-vitals.tsx
'use client';

import { useReportWebVitals } from 'next/web-vitals';

export function WebVitals() {
  useReportWebVitals((metric) => {
    // Invia a servizio di analytics
    const body = JSON.stringify({
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      id: metric.id,
    });

    // Usa sendBeacon per non bloccare la navigazione
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/analytics', body);
    }
  });

  return null;
}
```

### Ottimizzazione del bundle

**Dynamic imports per codice pesante:**

```tsx
import dynamic from 'next/dynamic';

// Componente caricato solo client-side, con loading state
const HeavyChart = dynamic(() => import('@/components/heavy-chart'), {
  loading: () => <div className="h-64 animate-pulse bg-gray-200" />,
  ssr: false, // Disabilita SSR per componenti client-only
});

// Libreria caricata on-demand
async function handleExport() {
  const { exportToExcel } = await import('@/lib/export');
  exportToExcel(data);
}
```

**Tree shaking — importare solo cio che serve:**

```tsx
// BUONO: import selettivo
import { format } from 'date-fns/format';

// CATTIVO: importa l'intero pacchetto
import { format } from 'date-fns';
```

### Ottimizzazione delle immagini per LCP

```tsx
// La hero image deve avere priority e fetchpriority="high"
<Image
  src="/hero.jpg"
  alt="Hero"
  width={1920}
  height={1080}
  priority
  sizes="100vw"
/>
```

### Prefetching

Next.js prefetcha automaticamente le route linkate con `<Link>` quando entrano nel viewport. Si puo controllare:

```tsx
import Link from 'next/link';

// Prefetch attivo (default per route statiche)
<Link href="/about">Chi siamo</Link>

// Prefetch disabilitato
<Link href="/expensive-page" prefetch={false}>Pagina pesante</Link>
```

### Script esterni ottimizzati

```tsx
import Script from 'next/script';

// Caricato dopo l'hydration della pagina
<Script src="https://analytics.example.com/script.js" strategy="afterInteractive" />

// Caricato in un web worker (sperimentale)
<Script src="https://heavy-analytics.example.com/script.js" strategy="worker" />

// Caricato prima di qualsiasi codice Next.js
<Script src="https://polyfill.io/v3/polyfill.min.js" strategy="beforeInteractive" />

// Script inline con afterInteractive
<Script id="gtm" strategy="afterInteractive">
  {`(function(w,d,s,l,i){...})(window,document,'script','dataLayer','GTM-XXXXX');`}
</Script>
```

### `next/after` — Lavoro differito dopo la risposta

L'API `after()` (stabile in Next.js 15) permette di schedulare lavoro da eseguire **dopo** che la risposta e stata inviata al client. Casi d'uso tipici: logging, analytics, sincronizzazione con servizi esterni, pulizia. Il vantaggio fondamentale e che questo lavoro non blocca il TTFB e non rallenta la risposta per l'utente.

`after()` funziona in Server Components, Server Actions, Route Handlers e Middleware.

```tsx
// app/products/[id]/page.tsx
import { after } from 'next/server';
import { log } from '@/lib/analytics';

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await getProduct(id);

  // Schedulato DOPO che la risposta e inviata
  after(async () => {
    await log({
      event: 'product_view',
      productId: id,
      timestamp: new Date().toISOString(),
    });
  });

  return <ProductDetail product={product} />;
}
```

**In una Server Action:**

```tsx
'use server';

import { after } from 'next/server';
import { sendNotification } from '@/lib/notifications';

export async function createOrder(formData: FormData) {
  const order = await db.order.create({
    data: { /* ... */ },
  });

  // Notifica asincrona dopo che la risposta del form e stata inviata
  after(async () => {
    await sendNotification({
      type: 'order_created',
      orderId: order.id,
      userId: order.userId,
    });
  });

  revalidatePath('/orders');
  return { success: true, orderId: order.id };
}
```

**In un Route Handler:**

```tsx
// app/api/webhook/route.ts
import { after, NextResponse } from 'next/server';

export async function POST(request: Request) {
  const payload = await request.json();

  // Risponde immediatamente al webhook
  after(async () => {
    // Elaborazione pesante dopo la risposta
    await processWebhookPayload(payload);
    await updateAnalytics(payload.event);
  });

  return NextResponse.json({ received: true });
}
```

**In Middleware:**

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { after } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  after(async () => {
    await logRequest({
      path: request.nextUrl.pathname,
      method: request.method,
      userAgent: request.headers.get('user-agent'),
    });
  });

  return response;
}
```

> **Importante:** `after()` non estende la durata della funzione serverless su piattaforme che hanno timeout stretti. Su Vercel, il lavoro differito viene eseguito dentro lo stesso invocation. Su piattaforme self-hosted con Node.js, il lavoro continua normalmente dopo lo streaming della risposta.

### `instrumentation.ts` — Osservabilita e Tracing

Next.js 15 rileva automaticamente il file `instrumentation.ts` (o `.js`) nella root del progetto (o dentro `src/`). Questo file permette di inizializzare strumenti di osservabilita come **OpenTelemetry** prima che qualsiasi codice dell'applicazione venga eseguito.

Il file esporta una funzione `register()` chiamata una sola volta all'avvio del processo (sia per il server Node.js sia per l'Edge Runtime).

**Setup con `@vercel/otel` (consigliato per Vercel):**

```bash
npm install @vercel/otel @opentelemetry/sdk-logs @opentelemetry/api-logs
```

```tsx
// instrumentation.ts
import { registerOTel } from '@vercel/otel';

export function register() {
  registerOTel({
    serviceName: 'my-nextjs-app',
  });
}
```

**Setup con OpenTelemetry SDK nativo (self-hosted):**

```bash
npm install @opentelemetry/sdk-node @opentelemetry/resources \
  @opentelemetry/semantic-conventions @opentelemetry/sdk-trace-node \
  @opentelemetry/exporter-trace-otlp-http
```

```tsx
// instrumentation.ts
export async function register() {
  // Importazione dinamica per evitare caricare moduli Node nel Edge Runtime
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { NodeSDK } = await import('@opentelemetry/sdk-node');
    const { Resource } = await import('@opentelemetry/resources');
    const {
      ATTR_SERVICE_NAME,
    } = await import('@opentelemetry/semantic-conventions');
    const {
      SimpleSpanProcessor,
    } = await import('@opentelemetry/sdk-trace-node');
    const {
      OTLPTraceExporter,
    } = await import('@opentelemetry/exporter-trace-otlp-http');

    const sdk = new NodeSDK({
      resource: new Resource({
        [ATTR_SERVICE_NAME]: 'my-nextjs-app',
      }),
      spanProcessors: [
        new SimpleSpanProcessor(
          new OTLPTraceExporter({
            url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318/v1/traces',
          })
        ),
      ],
    });

    sdk.start();
  }
}
```

**Callback `onRequestError` per monitoraggio errori:**

```tsx
// instrumentation.ts
import { type Instrumentation } from 'next';

export const onRequestError: Instrumentation.onRequestError = async (
  err,
  request,
  context
) => {
  await fetch('https://sentry.example/api/errors', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: err.message,
      stack: err.stack,
      path: request.path,
      method: request.method,
      routerKind: context.routerKind,   // 'Pages Router' | 'App Router'
      routePath: context.routePath,     // '/products/[id]'
      routeType: context.routeType,     // 'render' | 'route' | 'action' | 'middleware'
      renderSource: context.renderSource, // 'react-server-components' | 'react-server-components-payload' | ...
    }),
  });
};
```

> **Nota:** `NEXT_RUNTIME` puo essere `'nodejs'` o `'edge'`. Usare import dinamici condizionali per evitare che moduli Node.js vengano caricati nell'Edge Runtime.

---

## 19. Migrazione da Pages Router

### Strategia incrementale

Next.js supporta la coesistenza di `pages/` e `app/` nello stesso progetto. La migrazione puo avvenire incrementalmente, route per route.

### Passi principali

**Passo 1: Abilitare l'App Router.**

Creare `app/layout.tsx` come root layout. Il Pages Router continua a funzionare in parallelo.

```tsx
// app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  );
}
```

**Passo 2: Migrare `_app.tsx` e `_document.tsx`.**

Il contenuto di `_app.tsx` (providers, layout globale) va nel root `layout.tsx`. `_document.tsx` (`<html>`, `<head>`, `<body>`) e gestito nativamente dal root layout.

**Passo 3: Migrare le pagine una alla volta.**

Mappa delle equivalenze:

| Pages Router | App Router |
|---|---|
| `pages/index.tsx` | `app/page.tsx` |
| `pages/about.tsx` | `app/about/page.tsx` |
| `pages/blog/[slug].tsx` | `app/blog/[slug]/page.tsx` |
| `pages/api/users.ts` | `app/api/users/route.ts` |
| `pages/_error.tsx` | `app/error.tsx` |
| `pages/404.tsx` | `app/not-found.tsx` |

**Passo 4: Migrare il data fetching.**

```tsx
// PRIMA (Pages Router)
export async function getServerSideProps() {
  const data = await fetchData();
  return { props: { data } };
}

export default function Page({ data }) {
  return <div>{data.title}</div>;
}

// DOPO (App Router)
export default async function Page() {
  const data = await fetchData();
  return <div>{data.title}</div>;
}
```

```tsx
// PRIMA (Pages Router — getStaticProps + getStaticPaths)
export async function getStaticPaths() {
  const posts = await getPosts();
  return {
    paths: posts.map((p) => ({ params: { slug: p.slug } })),
    fallback: 'blocking',
  };
}

export async function getStaticProps({ params }) {
  const post = await getPost(params.slug);
  return { props: { post }, revalidate: 60 };
}

// DOPO (App Router)
export async function generateStaticParams() {
  const posts = await getPosts();
  return posts.map((p) => ({ slug: p.slug }));
}

export default async function PostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);
  return <article>{post.title}</article>;
}

export const revalidate = 60;
```

**Passo 5: Migrare i client-side hooks.**

- `useRouter` dal Pages Router (`next/router`) diventa `useRouter` dall'App Router (`next/navigation`). Le API sono diverse.
- `router.query` non esiste piu — usare `useParams()` e `useSearchParams()`.
- `router.events` non esiste piu — usare `usePathname()` con `useEffect`.

```tsx
// PRIMA (Pages Router)
import { useRouter } from 'next/router';

function Component() {
  const router = useRouter();
  const { id } = router.query;
}

// DOPO (App Router)
import { useParams, useSearchParams } from 'next/navigation';

function Component() {
  const params = useParams();     // { id: '123' }
  const searchParams = useSearchParams(); // ?page=2
}
```

---

## 20. Turbopack

### Cos'e Turbopack

Turbopack e il bundler scritto in Rust sviluppato da Vercel come successore di Webpack per Next.js. In Next.js 15, Turbopack e **stabile per lo sviluppo** (`next dev --turbopack`). A partire da Next.js 15.3, i build di produzione (`next build --turbopack`) sono disponibili in **beta**, e dalla versione 15.5 il supporto produzione ha raggiunto una maturita sufficiente per progetti non critici. Il 100% dei test della suite Next.js passa con Turbopack in dev, e oltre il 99% passa per i build di produzione.

### Stato di maturita

| Modalita | Stato | Versione |
|---|---|---|
| `next dev --turbopack` | **Stabile** | Next.js 15.0+ |
| `next build --turbopack` | **Beta** | Next.js 15.3+ |
| Uso in produzione | Consigliato per early adopters | Next.js 15.5+ |

> **Nota pratica:** per progetti in produzione con requisiti di stabilita stretti, continuare a usare Webpack per `next build` fino a quando Turbopack produzione non raggiunge lo stato stabile (previsto per Next.js 16). Per lo sviluppo locale, Turbopack e gia il default raccomandato.

### Configurazione

```bash
# Avvio dev server con Turbopack (stabile)
npx next dev --turbopack

# Build di produzione con Turbopack (beta)
npx next build --turbopack
```

```json
// package.json — script personalizzati
{
  "scripts": {
    "dev": "next dev --turbopack",
    "dev:webpack": "next dev",
    "build": "next build",
    "build:turbo": "next build --turbopack",
    "start": "next start"
  }
}
```

### Turbopack vs Webpack

| Caratteristica | Turbopack | Webpack |
|---|---|---|
| Linguaggio | Rust | JavaScript |
| Cold start dev | ~300-500ms | ~2-5s |
| HMR | ~10-50ms | ~200-500ms |
| Incremental builds | Nativo (function-level) | Plugin-based |
| Produzione | Beta (15.3+) | Stabile |
| Configurazione custom | In crescita | Completa |
| Plugin ecosystem | In costruzione | Vasto |
| Memory footprint | Basso (shared struct) | Alto |

### Migrazione da Webpack a Turbopack

La migrazione e incrementale — non serve riscrivere la configurazione. Turbopack ignora il blocco `webpack()` in `next.config.ts` e usa la propria configurazione sotto il campo `turbopack`.

**Passo 1: Identificare incompatibilita.**

Eseguire `next dev --turbopack` e verificare gli errori. I problemi piu comuni:

- **Custom Webpack loaders** — devono essere dichiarati nella sezione `turbopack.rules`
- **Webpack plugins** — non supportati direttamente; cercare alternative native o configurare via `turbopack.rules`
- **Module aliases** — portare da `resolve.alias` di Webpack a `turbopack.resolveAlias`
- **Module federation** — non ancora supportato in Turbopack

**Passo 2: Portare i loader.**

```tsx
// next.config.ts — Webpack (prima)
const config: NextConfig = {
  webpack: (config) => {
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });
    return config;
  },
};

// next.config.ts — Turbopack (dopo)
const config: NextConfig = {
  turbopack: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },
};
```

**Passo 3: Portare gli alias.**

```tsx
// Webpack
const config: NextConfig = {
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      underscore: 'lodash',
    };
    return config;
  },
};

// Turbopack
const config: NextConfig = {
  turbopack: {
    resolveAlias: {
      underscore: 'lodash',
    },
  },
};
```

**Passo 4: Supporto simultaneo Webpack + Turbopack.**

Durante la transizione, si possono mantenere entrambe le configurazioni. La sezione `webpack` viene usata solo senza `--turbopack`, la sezione `turbopack` solo con `--turbopack`:

```tsx
// next.config.ts — supporto duale
const config: NextConfig = {
  // Usato solo con `next build` (senza --turbopack)
  webpack: (config) => {
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });
    return config;
  },
  // Usato solo con --turbopack
  turbopack: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },
};
```

### Limitazioni attuali

- Non tutti i plugin Webpack sono supportati — verificare la [documentazione ufficiale](https://nextjs.org/docs/app/api-reference/turbopack) per la lista di compatibilita
- La configurazione `webpack()` in `next.config.ts` non viene usata con Turbopack
- Module Federation non ancora disponibile
- Alcuni loader personalizzati richiedono adattamento
- Build di produzione in beta — testare accuratamente prima di adottare in produzione

### Configurazione avanzata Turbopack

```tsx
// next.config.ts
const config: NextConfig = {
  turbopack: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
      '*.graphql': {
        loaders: ['graphql-tag/loader'],
        as: '*.js',
      },
    },
    resolveAlias: {
      underscore: 'lodash',
      mocha: { browser: 'mocha/browser-entry.js' },
    },
    resolveExtensions: ['.tsx', '.ts', '.jsx', '.js', '.json'],
  },
};
```

---

## 21. Troubleshooting

### 1. Hydration Mismatch

**Errore:** `Text content does not match server-rendered HTML` oppure `Hydration failed because the initial UI does not match what was rendered on the server`.

**Causa:** il server genera HTML diverso da quello che il client tenta di hydrare. Cause comuni: `Date.now()`, `Math.random()`, accesso a `window`/`document`, estensioni browser che modificano il DOM.

**Soluzione:**

```tsx
// CATTIVO — genera valore diverso su server e client
function Component() {
  return <p>{new Date().toLocaleString()}</p>;
}

// BUONO — usa useEffect per valori client-only
'use client';
import { useState, useEffect } from 'react';

function Component() {
  const [date, setDate] = useState<string>('');

  useEffect(() => {
    setDate(new Date().toLocaleString());
  }, []);

  return <p>{date || 'Caricamento...'}</p>;
}
```

```tsx
// Alternativa: suppressHydrationWarning per casi legittimi
<time dateTime={dateStr} suppressHydrationWarning>
  {new Date(dateStr).toLocaleDateString()}
</time>
```

### 2. "useState" o "useEffect" in un Server Component

**Errore:** `You're importing a component that needs useState/useEffect. It only works in a Client Component`.

**Soluzione:** aggiungere `'use client'` in cima al file del componente che usa hooks interattivi.

### 3. Dati stale dopo una mutazione

**Causa:** la cache non viene invalidata dopo un'operazione di scrittura.

**Soluzione:**

```tsx
'use server';

import { revalidatePath, revalidateTag } from 'next/cache';

export async function updateItem(id: string, data: ItemData) {
  await db.item.update({ where: { id }, data });
  // Invalidare TUTTI i layer coinvolti
  revalidateTag('items');
  revalidatePath('/items');
}
```

### 4. "Dynamic server usage" in una route statica

**Errore:** `Dynamic server usage: cookies/headers was called outside of request scope`.

**Causa:** si tenta di usare `cookies()` o `headers()` in un componente che Next.js vuole rendere staticamente.

**Soluzione:** aggiungere `export const dynamic = 'force-dynamic'` alla pagina, oppure wrappare il componente dinamico in un Suspense boundary.

### 5. `fetch` non cachata come previsto

**Causa:** in Next.js 15, `fetch` NON e cachata di default (cambiamento rispetto a Next.js 14).

**Soluzione:** essere espliciti con le opzioni di caching.

```tsx
// Cachare esplicitamente
const data = await fetch(url, { cache: 'force-cache' });

// O usare revalidate
const data = await fetch(url, { next: { revalidate: 3600 } });
```

### 6. Circular dependency tra Server e Client Components

**Causa:** un server component importa un client component che re-importa il server component.

**Soluzione:** ristrutturare l'albero. Passare i dati dal server component al client component via props, non via import circolare.

### 7. Middleware non si attiva

**Cause comuni:**
- File `middleware.ts` non alla root del progetto
- Pattern `matcher` che esclude il path desiderato
- Typo nel nome del file

**Debug:** aggiungere un `console.log` nel middleware — appare nei log del server, non nella console del browser.

### 8. `params` non disponibile (App Router)

**Causa:** in Next.js 15, `params` e `searchParams` sono diventati **Promise**. Bisogna fare `await`.

```tsx
// PRIMA (Next.js 14)
export default function Page({ params }: { params: { id: string } }) {
  const { id } = params; // Sincrono
}

// DOPO (Next.js 15)
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params; // Asincrono
}
```

### 9. Build fallisce con "Module not found"

**Cause:**
- Import di moduli Node.js (`fs`, `path`) in client components
- Import di librerie server-only in codice client

**Soluzione:** usare il pacchetto `server-only` per marcare codice server-only:

```bash
npm install server-only
```

```tsx
// lib/db.ts
import 'server-only';
import { PrismaClient } from '@prisma/client';

// Questo file genera un errore di build se importato da un client component
```

### 10. Layout che si rimonta ad ogni navigazione

**Causa:** i layout NON si rimontano per design. Se serve un componente che si rimonta, usare `template.tsx` al posto di `layout.tsx`.

### 11. Errore CORS nei Route Handlers

**Soluzione:** implementare i CORS headers manualmente (vedi sezione Route Handlers).

### 12. next/image non mostra immagini remote

**Causa:** dominio non configurato in `next.config.ts`.

**Soluzione:** aggiungere il pattern in `images.remotePatterns`.

### 13. Server Action timeout in produzione

**Causa:** le server actions hanno un timeout di default (30 secondi su Vercel).

**Soluzione:**

```tsx
// next.config.ts
const config: NextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

// A livello di route segment
export const maxDuration = 60; // 60 secondi
```

### 14. "searchParams" spariscono nel layout

**Causa:** i `searchParams` non sono accessibili nei layout, solo nelle pagine. Questo e intenzionale.

**Soluzione:** accedere a `searchParams` nella `page.tsx` e passarli ai componenti tramite props, oppure usare `useSearchParams()` in un client component.

### 15. Hot reload lento o non funzionante

**Soluzioni:**
- Usare Turbopack: `next dev --turbopack`
- Controllare il numero di file watched — escludere `node_modules` e `.next`
- Su Linux, aumentare il limite degli inotify: `echo 524288 | sudo tee /proc/sys/fs/inotify/max_user_watches`

### 16. Memoria esaurita durante il build

**Soluzione:**

```bash
# Aumentare la memoria per Node.js
NODE_OPTIONS='--max-old-space-size=8192' npm run build
```

### 17. generateStaticParams non pre-renderizza tutte le pagine

**Causa:** `dynamicParams` e `true` di default — le pagine non listate vengono generate on-demand. Se si vuole un 404 per path non listati:

```tsx
export const dynamicParams = false; // 404 per path non in generateStaticParams
```

### 18. Redirect loop infinito nel middleware

**Causa:** il middleware applica un redirect che ri-matcha il middleware stesso.

**Soluzione:** escludere il path di destinazione dal matcher:

```tsx
export const config = {
  matcher: ['/((?!login|_next|api).*)'],
};
```

### 19. CSS non applicato in produzione

**Cause:**
- CSS importato in un server component ma usato in un client component
- Ordine di import CSS non deterministico

**Soluzione:** importare il CSS nel file piu vicino a dove viene usato. Per CSS globale, importarlo nel root `layout.tsx`.

### 20. Deploy Docker fallisce con standalone mode

**Cause:**
- `output: 'standalone'` non configurato in `next.config.ts`
- File `public/` e `.next/static` non copiati nell'immagine finale

**Soluzione:** seguire il Dockerfile multi-stage nella sezione Deployment.

### 21. Errore "Unsupported Server Component type"

**Causa:** si tenta di passare una funzione, una classe, o un oggetto non-serializzabile come prop da un server component a un client component.

**Soluzione:** passare solo dati serializzabili (stringhe, numeri, oggetti plain, array) come props. Le funzioni vanno definite nel client component o passate come server actions.

### 22. Parallel routes che mostrano il fallback sbagliato

**Causa:** manca il file `default.tsx` nello slot parallelo.

**Soluzione:** aggiungere `default.tsx` in ogni slot `@nome/`:

```tsx
// app/@analytics/default.tsx
export default function AnalyticsDefault() {
  return null; // Niente da mostrare di default
}
```

---

## 22. FAQ

### Q1: Devo usare App Router o Pages Router per un nuovo progetto?

**App Router.** Il Pages Router e in modalita di manutenzione. Tutte le nuove feature (RSC, Server Actions, Streaming, PPR) sono esclusive dell'App Router.

### Q2: Quando conviene usare `'use client'`?

Quando il componente ha bisogno di: `useState`, `useEffect`, `useContext`, event handlers (`onClick`, `onChange`), API browser (`window`, `document`, `localStorage`). Altrimenti, mantienilo server component.

### Q3: Posso usare un ORM senza `fetch`? Come gestisco il caching?

Si, con `unstable_cache` o `React.cache()`. Vedi la sezione Data Fetching.

### Q4: Come scelgo tra ISR, SSR e SSG?

- **SSG** (statico): contenuto che non cambia mai o cambia raramente (docs, landing pages)
- **ISR**: contenuto che cambia periodicamente ma non ad ogni richiesta (blog, catalogo)
- **SSR**: contenuto personalizzato per utente o real-time (dashboard, feed social)

### Q5: Devo creare API endpoints separati o usare Server Actions?

**Server Actions per mutazioni** (create, update, delete) invocate da form o click. **Route Handlers per**: webhook, integrazioni terze parti, API pubblica consumata da client esterni.

### Q6: Come gestisco gli errori globali?

Il root `layout.tsx` non e coperto da `error.tsx`. Per errori a quel livello, usare `global-error.tsx`:

```tsx
// app/global-error.tsx
'use client';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <h2>Errore critico</h2>
        <button onClick={reset}>Riprova</button>
      </body>
    </html>
  );
}
```

### Q7: Come faccio redirect in un Server Component?

```tsx
import { redirect } from 'next/navigation';

export default async function Page() {
  const session = await auth();
  if (!session) {
    redirect('/login'); // Non ritorna — lancia un'eccezione interna
  }
  // ...
}
```

### Q8: Posso usare Tailwind CSS con Next.js?

Si. Next.js 15 ha supporto nativo per Tailwind CSS v4 (o v3 con PostCSS). Basta configurarlo nel progetto.

### Q9: Come proteggo le environment variables?

- Variabili con prefisso `NEXT_PUBLIC_` sono esposte al browser — mai usarle per secrets
- Variabili senza prefisso sono accessibili solo server-side
- Usare `.env.local` per development (mai committare nel repository)

### Q10: Next.js funziona con React 19?

Si. Next.js 15 e costruito su React 19 e sfrutta pienamente le sue feature: `use`, `useActionState`, `useFormStatus`, `useOptimistic`, Server Components, Server Actions.

### Q11: Qual e la differenza tra `layout.tsx` e `template.tsx`?

`layout.tsx` persiste tra navigazioni (lo stato viene mantenuto). `template.tsx` viene rimontato ad ogni navigazione (nuovo stato, nuovi effetti). Usare `template.tsx` quando serve un'animazione di ingresso o un reset dello stato.

### Q12: Come gestisco l'autenticazione nelle Parallel Routes?

L'autenticazione va nel layout che wrappa le parallel routes, non nei singoli slot. Il layout controlla l'accesso prima di rendere qualsiasi slot.

### Q13: Posso fare deploy su piattaforme diverse da Vercel?

Si. Con `output: 'standalone'` si ottiene un server Node.js autosufficiente. Si puo fare deploy su: Docker (qualsiasi cloud), AWS (EC2, ECS, Lambda), Google Cloud Run, DigitalOcean App Platform, Fly.io, Railway, Render. Le feature edge-specific (Edge Runtime, ISR on-demand) possono richiedere adattamenti.

### Q14: Come monitoro le performance in produzione?

- `useReportWebVitals` per Core Web Vitals
- Vercel Analytics (se su Vercel)
- OpenTelemetry con `instrumentation.ts`
- Sentry, Datadog, o New Relic per APM completo

### Q15: Come gestisco il file upload?

```tsx
// app/actions/upload.ts
'use server';

import { writeFile } from 'fs/promises';
import { join } from 'path';

export async function uploadFile(formData: FormData) {
  const file = formData.get('file') as File;
  if (!file) return { error: 'Nessun file selezionato' };

  // Validazione tipo e dimensione
  const maxSize = 5 * 1024 * 1024; // 5MB
  if (file.size > maxSize) return { error: 'File troppo grande (max 5MB)' };

  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowedTypes.includes(file.type)) return { error: 'Tipo file non supportato' };

  const bytes = await file.arrayBuffer();
  const buffer = Buffer.from(bytes);

  const filename = `${Date.now()}-${file.name}`;
  const path = join(process.cwd(), 'public', 'uploads', filename);
  await writeFile(path, buffer);

  return { success: true, path: `/uploads/${filename}` };
}
```

### Q16: Come implemento la ricerca con debounce?

```tsx
'use client';

import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { useDebouncedCallback } from 'use-debounce';

export function SearchInput() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const { replace } = useRouter();

  const handleSearch = useDebouncedCallback((term: string) => {
    const params = new URLSearchParams(searchParams);
    if (term) {
      params.set('q', term);
    } else {
      params.delete('q');
    }
    params.set('page', '1');
    replace(`${pathname}?${params.toString()}`);
  }, 300);

  return (
    <input
      type="search"
      placeholder="Cerca..."
      defaultValue={searchParams.get('q') ?? ''}
      onChange={(e) => handleSearch(e.target.value)}
    />
  );
}
```

---

## 23. Best Practices e Anti-Pattern

### Best Practices

**1. Boundary `'use client'` il piu in basso possibile.**

Spezzare i componenti in parti server e client. Il server component fa il fetch e il rendering statico; il client component gestisce solo l'interattivita.

```tsx
// BUONO: solo il bottone interattivo e client
// app/products/[id]/page.tsx (Server Component)
import { AddToCartButton } from './add-to-cart';

export default async function ProductPage({ params }) {
  const { id } = await params;
  const product = await getProduct(id);

  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      {/* Solo questo e client-side */}
      <AddToCartButton productId={product.id} price={product.price} />
    </div>
  );
}
```

**2. Collocare il data fetching nel componente che usa i dati.**

Non passare dati attraverso molti livelli di props. Grazie alla request memoization, la stessa fetch in componenti diversi non causa richieste duplicate.

**3. Usare `loading.tsx` e Suspense per lo streaming.**

Non lasciare il fetch piu lento bloccare l'intera pagina.

**4. Validare sempre gli input delle Server Actions.**

Le Server Actions sono endpoint pubblici — chiunque puo invocarle con qualsiasi payload.

```tsx
'use server';
import { z } from 'zod';

const schema = z.object({ /* ... */ });

export async function action(formData: FormData) {
  const parsed = schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { error: parsed.error.flatten() };
  }
  // Procedere con dati validati
}
```

**5. Usare `server-only` per codice che non deve mai finire nel bundle client.**

**6. Pre-generare le route statiche con `generateStaticParams`.**

**7. Configurare metadata per ogni pagina.** Titolo, descrizione, Open Graph — fondamentali per SEO.

**8. Usare `<Link>` per la navigazione interna, mai `<a>`.** `<Link>` abilita la navigazione client-side, il prefetch, e il mantenimento della cache.

**9. Organizzare le Server Actions in file dedicati.** Non inline nelle page — meglio in `app/actions/` o `lib/actions/`.

**10. Monitoring in produzione.** `instrumentation.ts` per OpenTelemetry, `useReportWebVitals` per CWV.

### Anti-Pattern

**1. `'use client'` su tutta la pagina.**

Rende l'intera pagina un client component, eliminando tutti i vantaggi dei RSC (bundle piu grande, no fetch server-side diretto, no streaming).

**2. Fetch nel layout.**

I layout non si ri-rendono tra navigazioni delle pagine figlie. Se i dati devono cambiare per pagine diverse, il fetch va nella `page.tsx`.

**3. Mutazioni via `GET`.**

Le Server Actions usano `POST` per design. Non esporre mutazioni su Route Handlers `GET`.

**4. Ignorare il sistema di caching.**

Mettere `export const dynamic = 'force-dynamic'` ovunque "per sicurezza" disabilita tutti i benefici della cache. Capire i layer di caching e invalidare chirurgicamente.

**5. Fetch waterfall nei Server Components.**

```tsx
// ANTI-PATTERN: waterfall
export default async function Page() {
  const user = await getUser();    // 200ms
  const posts = await getPosts();  // 300ms — aspetta che getUser finisca
}

// CORRETTO: parallelo
export default async function Page() {
  const [user, posts] = await Promise.all([getUser(), getPosts()]);
}
```

**6. Stato globale condiviso tra server e client.**

I Server Components non condividono stato con i Client Components. Non provare a usare un global store per passare dati — usare props o context (solo client).

**7. Testare solo il "happy path".**

Testare anche error boundaries, loading states, not-found, form validation errors.

**8. Non gestire il `revalidatePath` / `revalidateTag` dopo le mutazioni.**

Se manca la rivalidazione, l'utente vedra dati stale fino allo scadere della cache.

**9. Usare `useEffect` per data fetching.**

Nel paradigma App Router, il fetch va nei Server Components o tramite TanStack Query nel client. `useEffect(() => fetch(...))` e un anti-pattern che causa waterfall, flickering e complessita inutile.

**10. Bloccare il rendering con un singolo Suspense boundary.**

Usare piu Suspense boundaries granulari per abilitare lo streaming indipendente delle varie sezioni della pagina.

---

## 24. Esercizi

### Lab 1 — Progetto base con App Router

Creare un'applicazione Next.js 15 con:
- Root layout con navigazione
- Tre pagine statiche (Home, Chi siamo, Contatti)
- Un layout annidato per la sezione blog
- `loading.tsx` e `error.tsx` personalizzati
- Pagina 404 personalizzata

### Lab 2 — Blog con ISR

Creare un blog con:
- Lista articoli con ISR (rivalidazione ogni 60 secondi)
- Pagina singolo articolo con `generateStaticParams`
- Metadata dinamica per ogni articolo
- JSON-LD structured data

### Lab 3 — Dashboard con Server Actions

Creare una dashboard CRUD con:
- Autenticazione via NextAuth.js
- Server Actions per create, update, delete
- Form con validazione Zod e `useActionState`
- Optimistic updates con `useOptimistic`
- Loading e error states granulari con Suspense

### Lab 4 — E-commerce con Parallel Routes

Creare una pagina prodotto con:
- Parallel routes per recensioni, prodotti correlati, FAQ
- Intercepting route per quick-view modale
- Image optimization con `next/image`
- Streaming indipendente delle varie sezioni

### Lab 5 — Internazionalizzazione

Creare un sito multilingua (IT, EN, DE) con:
- Sub-path routing (`/it/`, `/en/`, `/de/`)
- Middleware per rilevamento lingua
- Dizionari di traduzione con import dinamico
- Formattazione date e valute locale-aware
- Sitemap multilingua

### Lab 6 — Migrazione Pages to App Router

Partendo da un progetto con Pages Router:
- Migrare incrementalmente 5 pagine all'App Router
- Convertire `getServerSideProps` in Server Components
- Convertire `getStaticProps` con `generateStaticParams`
- Verificare che entrambi i router coesistano

### Stretch — Performance audit

Su uno degli esercizi precedenti:
- Eseguire bundle analysis
- Ottimizzare il Lighthouse score (target: 90+ su tutte le categorie)
- Implementare `useReportWebVitals`
- Documentare le ottimizzazioni applicate

---

## 25. Letture e Risorse

### Documentazione ufficiale

- Next.js Docs. https://nextjs.org/docs
- Next.js Learn. https://nextjs.org/learn
- React Docs (RSC). https://react.dev/reference/rsc/server-components
- Auth.js (NextAuth v5). https://authjs.dev

### Risorse di approfondimento

- Vercel Blog. https://vercel.com/blog
- Next.js GitHub. https://github.com/vercel/next.js
- Next.js Examples. https://github.com/vercel/next.js/tree/canary/examples
- Prisma Docs. https://www.prisma.io/docs
- Drizzle ORM Docs. https://orm.drizzle.team
- Playwright Docs. https://playwright.dev/docs/intro

### Corsi e tutorial

- Next.js Official Tutorial (App Router). https://nextjs.org/learn
- Lee Robinson YouTube. https://youtube.com/@leerob

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [07 — React](07-react.md) | Fondamenti React 19, hook e component model alla base di Next.js |
| [21 — RSC](21-rsc-server-driven-ui.md) | Architettura RSC, streaming, Suspense e Server Actions in dettaglio |
| [06 — TypeScript](06-typescript.md) | Type safety per page props, Server Actions e API route handlers |
| [13 — Autenticazione](13-autenticazione-autorizzazione.md) | Auth.js/NextAuth, JWT e protezione route con middleware |
| [17 — Performance Web](17-performance-web.md) | Core Web Vitals, Lighthouse e ottimizzazione bundle Next.js |
| [16 — Build Tools e Deploy](16-build-tools-e-deploy.md) | Vercel, Docker e strategie di deployment per Next.js |

---

## 26. Glossario

| Termine | Definizione |
|---|---|
| **App Router** | Sistema di routing basato sulla directory `app/`, default in Next.js 13+. |
| **Pages Router** | Sistema di routing legacy basato su `pages/`, in manutenzione. |
| **RSC** | React Server Components — componenti eseguiti solo sul server. |
| **`'use client'`** | Directive che marca un componente come Client Component. |
| **`'use server'`** | Directive che marca una funzione come Server Action. |
| **Server Action** | Funzione asincrona eseguita sul server, invocabile da client o form. |
| **SSR** | Server-Side Rendering — rendering ad ogni richiesta. |
| **SSG** | Static Site Generation — rendering a build time. |
| **ISR** | Incremental Static Regeneration — SSG con rivalidazione periodica. |
| **PPR** | Partial Prerendering — shell statica + contenuto dinamico streamato. |
| **Streaming** | Invio progressivo dell'HTML dal server al browser. |
| **Suspense** | React boundary che mostra un fallback durante il caricamento. |
| **Layout** | Componente che wrappa pagine figlie, persiste tra navigazioni. |
| **Template** | Come layout, ma si rimonta ad ogni navigazione. |
| **Route Group** | Cartella `(nome)` che organizza le route senza influenzare l'URL. |
| **Parallel Route** | Slot `@nome` che renderizza piu pagine in parallelo nello stesso layout. |
| **Intercepting Route** | Route che intercetta una navigazione per mostrare contenuto alternativo (es. modale). |
| **Middleware** | Codice eseguito prima del completamento della richiesta, gira sull'Edge Runtime. |
| **Route Handler** | File `route.ts` che definisce un endpoint API nell'App Router. |
| **Edge Runtime** | Runtime V8 leggero per middleware e route handlers con bassa latenza. |
| **Data Cache** | Cache server-side persistente per i risultati di `fetch`. |
| **Full Route Cache** | Cache dell'HTML e RSC Payload delle route statiche. |
| **Router Cache** | Cache client-side dei payload RSC delle route navigate. |
| **Request Memoization** | Deduplicazione delle fetch duplicate nella stessa render pass. |
| **Turbopack** | Bundler Rust di Vercel, successore di Webpack per Next.js. |
| **`revalidateTag()`** | Invalida tutte le fetch associate a un tag specifico. |
| **`revalidatePath()`** | Invalida la cache di una route specifica. |
| **`generateStaticParams()`** | Genera i parametri statici per le route dinamiche a build time. |
| **`generateMetadata()`** | Genera metadata dinamica per SEO e social sharing. |
| **`next/image`** | Componente per immagini ottimizzate con lazy loading e formati moderni. |
| **`next/font`** | Sistema di ottimizzazione font con zero-layout-shift. |
| **`next/link`** | Componente per navigazione client-side con prefetch automatico. |
| **`next/script`** | Componente per caricamento ottimizzato di script esterni. |
| **Auth.js** | Libreria di autenticazione (ex NextAuth.js v5) per Next.js. |
| **Prisma** | ORM type-safe per Node.js e TypeScript. |
| **Drizzle** | ORM leggero con query builder SQL-like per TypeScript. |
| **Zod** | Libreria di validazione schema per TypeScript. |
| **MSW** | Mock Service Worker — intercetta richieste di rete per testing. |
