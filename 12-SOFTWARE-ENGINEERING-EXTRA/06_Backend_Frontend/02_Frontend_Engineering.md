# Module 6.2: Frontend Engineering

> **Module 06.2** · **Last updated:** 2026-05-22

## Guiding ideas

1. **React 19 + RSC paradigm shift.**
2. **TypeScript strict mandatory.**
3. **TanStack Query > Redux for server state.**
4. **Core Web Vitals < target before launch.**
5. **Rendering strategy selection (CSR/SSR/SSG/ISR) is an architecture decision, not a framework default.**
6. **Signals and fine-grained reactivity are replacing the virtual DOM diffing model.**
7. **Progressive enhancement: the base experience works without JavaScript.**

---

## Table of Contents

1. [Rendering Strategies](#1-rendering-strategies)
2. [Hydration Deep Dive](#2-hydration-deep-dive)
3. [React Server Components](#3-react-server-components)
4. [Virtual DOM vs Signals](#4-virtual-dom-vs-signals)
5. [The Critical Rendering Path](#5-the-critical-rendering-path)
6. [Bundle Optimization](#6-bundle-optimization)
7. [Module Federation and Micro-Frontends](#7-module-federation-and-micro-frontends)
8. [Web Workers](#8-web-workers)
9. [Service Workers and Offline](#9-service-workers-and-offline)
10. [State Management](#10-state-management)
11. [Progressive Enhancement](#11-progressive-enhancement)
12. [Design Systems](#12-design-systems)
13. [Core Web Vitals Engineering](#13-core-web-vitals-engineering)
14. [CSS Architecture](#14-css-architecture)
15. [TypeScript Patterns for Frontend](#15-typescript-patterns-for-frontend)
16. [Testing Frontend Applications](#16-testing-frontend-applications)
17. [Accessibility Engineering](#17-accessibility-engineering)
18. [Exercises](#18-exercises)
19. [References](#19-references)

---

## 1. Rendering Strategies

### 1.1 Client-Side Rendering (CSR)

The server sends a minimal HTML shell. JavaScript downloads, parses, executes,
fetches data, and renders the UI entirely on the client.

```
Server response:
  <html>
    <body>
      <div id="root"></div>           ← empty
      <script src="/app.js"></script> ← 200KB+ JS
    </body>
  </html>

Timeline:
  ┌──────┐    ┌────────────┐    ┌──────────┐    ┌────────────┐
  │ HTML  │───→│ Download JS│───→│ Execute  │───→│  Render    │
  │(fast) │    │  (slow)    │    │  + fetch │    │  content   │
  └──────┘    └────────────┘    └──────────┘    └────────────┘
       FP                                           LCP
```

**Pros:** Simple deployment (static hosting), rich interactivity, SPA navigation.
**Cons:** Slow FCP/LCP (user sees blank page until JS executes), poor SEO
(crawlers may not execute JS), no content without JavaScript.

**Best for:** Authenticated dashboards, admin panels, internal tools where SEO
is irrelevant and users have good connections.

### 1.2 Server-Side Rendering (SSR)

The server renders full HTML for each request. The browser displays content
immediately; JavaScript hydrates afterward for interactivity.

```
Server:
  1. Receive request
  2. Fetch data
  3. Render React/Vue/Svelte to HTML string
  4. Send complete HTML + JS bundle

Client:
  1. Display HTML (fast FCP)
  2. Download JS
  3. Hydrate (attach event listeners)

Timeline:
  ┌──────────┐    ┌────────────┐    ┌───────────┐
  │ Full HTML │───→│ Download JS│───→│ Hydrate   │
  │ (FCP=fast)│    │            │    │ (TTI)     │
  └──────────┘    └────────────┘    └───────────┘
```

**Pros:** Fast FCP, good SEO, works without JavaScript (content visible).
**Cons:** Server compute per request (cost), TTFB depends on data fetching
latency, full page re-render on each navigation (unless using streaming).

**Best for:** Content-heavy pages, marketing sites, e-commerce product pages,
anything where first-paint matters.

### 1.3 Static Site Generation (SSG)

Pages are rendered at build time and served as static files. No server-side
computation per request.

```
Build time:
  For each page:
    1. Fetch data
    2. Render HTML
    3. Write static .html file

Runtime:
  CDN serves pre-built .html → instant response
```

**Pros:** Fastest TTFB (CDN-served static files), cheapest hosting, most secure
(no server to attack), best SEO.
**Cons:** Build time grows with page count, stale content until rebuild,
unsuitable for user-specific or frequently-changing content.

**Best for:** Documentation sites, blogs, marketing pages, landing pages.

### 1.4 Incremental Static Regeneration (ISR)

Pages are statically generated but regenerated in the background on a
configurable interval or on-demand.

```
Request 1 (cache miss):
  → Generate page server-side, serve and cache

Requests 2-N (cache hit, within revalidation window):
  → Serve cached static page instantly

Request N+1 (after revalidation interval):
  → Serve stale page instantly
  → Regenerate in background
  → Next request gets fresh page
```

**Next.js ISR:**
```typescript
// pages/products/[id].tsx (Pages Router)
export async function getStaticProps({ params }) {
  const product = await fetchProduct(params.id);
  return {
    props: { product },
    revalidate: 60, // regenerate at most every 60 seconds
  };
}

// app/products/[id]/page.tsx (App Router)
export const revalidate = 60;

export default async function ProductPage({ params }) {
  const product = await fetchProduct(params.id);
  return <ProductView product={product} />;
}
```

### 1.5 Streaming SSR

Instead of waiting for all data before sending HTML, stream chunks as they
become ready:

```
Traditional SSR:
  Server: fetch A (200ms) + fetch B (800ms) → render → send all at once
  Client: ────────── 1000ms ──────────→ see content

Streaming SSR:
  Server: fetch A (200ms) → send shell + A → fetch B (800ms) → stream B
  Client: ── 200ms → see shell + A ────── 1000ms → see B

  The user sees partial content 800ms earlier.
```

**React 18+ Streaming:**
```typescript
// Server component with Suspense boundaries
export default function Page() {
  return (
    <div>
      <Header />  {/* Sent immediately */}
      <Suspense fallback={<ProductSkeleton />}>
        <ProductList />  {/* Streamed when data is ready */}
      </Suspense>
      <Suspense fallback={<ReviewsSkeleton />}>
        <Reviews />  {/* Streamed independently */}
      </Suspense>
    </div>
  );
}
```

### 1.6 Comparison Table

| Strategy | TTFB | FCP | LCP | SEO | Hosting cost | Data freshness |
|---|---|---|---|---|---|---|
| **CSR** | Fast | Slow | Slow | Poor | Low (static) | Real-time |
| **SSR** | Slow | Fast | Fast | Great | High (server) | Real-time |
| **SSG** | Fastest | Fastest | Fastest | Great | Lowest (CDN) | Stale until rebuild |
| **ISR** | Fast | Fast | Fast | Great | Medium | Configurable |
| **Streaming** | Fast | Fast | Progressive | Great | High (server) | Real-time |

---

## 2. Hydration Deep Dive

### 2.1 What Hydration Is

Hydration is the process of attaching JavaScript event listeners and state
to server-rendered HTML. The browser already has the visual content (HTML), but
it is inert — buttons don't respond to clicks until hydration completes.

```
Server HTML: <button class="btn">Click me</button>  ← visible, non-interactive

After hydration:
  React traverses the DOM tree
  Matches server HTML to component tree
  Attaches onClick handler to <button>
  Button is now interactive
```

### 2.2 The Hydration Gap (Uncanny Valley)

The period between FCP (content visible) and TTI (content interactive) is the
"uncanny valley." The page looks ready but doesn't respond to interaction.

```
  FCP                                TTI
   │                                  │
   │ ── Content visible ──────────── │ ── Content interactive
   │    but non-interactive          │
   │                                  │
   │    user clicks button → nothing │
   │    user types in input → frozen │
   │                                  │
   └──── HYDRATION GAP ──────────────┘
```

This is a real UX problem. Users see a form, try to type, and nothing happens
for 1-3 seconds. On slow devices (low-end phones on 3G), this gap can be 5+ seconds.

### 2.3 Hydration Mismatch Errors

If the server-rendered HTML differs from what React would render on the client,
React throws a hydration mismatch warning and may discard the entire server tree
to re-render from scratch. This destroys the SSR performance benefit.

**Common causes:**
```typescript
// BAD: Non-deterministic rendering
function Component() {
  return <div>{Math.random()}</div>;  // Different on server vs client
}

// BAD: Browser-only APIs during render
function Component() {
  return <div>{window.innerWidth}px</div>;  // window doesn't exist on server
}

// BAD: Date/time differences
function Component() {
  return <div>{new Date().toLocaleString()}</div>;  // Server timezone ≠ client timezone
}

// GOOD: Use useEffect for browser-specific data
function Component() {
  const [width, setWidth] = useState(0);  // 0 matches server (no window)
  useEffect(() => {
    setWidth(window.innerWidth);  // runs only on client, after hydration
  }, []);
  return <div>{width}px</div>;
}
```

### 2.4 Partial Hydration

Instead of hydrating the entire page, only hydrate interactive components:

```
┌─────────────────────────────────┐
│ Header (static — no hydration)  │
├─────────────────────────────────┤
│ Article text (static)           │
│                                 │
│ ┌───────────────────────┐       │
│ │ Comment form (hydrate)│ ← only this component gets JS
│ └───────────────────────┘       │
│                                 │
│ Footer (static — no hydration)  │
└─────────────────────────────────┘
```

**Astro's Islands Architecture** is the canonical implementation:

```astro
---
// Astro component — zero JS by default
import Header from '../components/Header.astro';  // static, no hydration
import SearchBar from '../components/SearchBar.tsx';  // React, needs hydration
---

<Header />
<SearchBar client:visible />  <!-- Hydrated only when visible in viewport -->
```

**Hydration directives in Astro:**
- `client:load` — hydrate immediately on page load.
- `client:idle` — hydrate when browser is idle (requestIdleCallback).
- `client:visible` — hydrate when element enters viewport (IntersectionObserver).
- `client:media="(max-width: 768px)"` — hydrate only on matching viewport.
- `client:only="react"` — skip SSR entirely, CSR only.

### 2.5 Resumability (Qwik)

Qwik takes a different approach: instead of replaying the component tree to
attach listeners, the framework serializes the listener references into HTML
attributes. On interaction, only the relevant handler code is loaded and executed.

```html
<!-- Qwik output: event handler reference embedded in HTML -->
<button on:click="./chunk-abc123.js#handler_0">Click me</button>

<!-- On click: -->
<!-- 1. Browser intercepts click -->
<!-- 2. Loads chunk-abc123.js -->
<!-- 3. Executes handler_0 -->
<!-- No full hydration needed -->
```

Zero hydration cost at page load. Interaction cost is paid per-event, lazily.

---

## 3. React Server Components

### 3.1 The Mental Model

React Server Components (RSC) split components into two types:

| Aspect | Server Component | Client Component |
|---|---|---|
| **Runs on** | Server only | Server (SSR) + client (hydration) |
| **File convention** | Default (no directive) | `'use client'` at top of file |
| **Can use** | `async/await`, DB queries, fs, env vars | `useState`, `useEffect`, event handlers |
| **JS shipped to client** | Zero | Yes (in the bundle) |
| **Can import** | Server or Client components | Only Client components |
| **Re-renders** | On server, on navigation | On client, on state change |

```
Component Tree:
  ┌──────────────────────────────────────────┐
  │ Layout (Server)                           │
  │  ├── Header (Server) — 0 KB client JS    │
  │  ├── Sidebar (Server) — 0 KB client JS   │
  │  │    └── NavLinks (Server)              │
  │  ├── Main (Server)                        │
  │  │    ├── ArticleContent (Server)        │
  │  │    └── CommentSection (Client)        │  ← 'use client'
  │  │         ├── CommentForm (Client)      │  ← useState, handlers
  │  │         └── CommentList (Client)      │
  │  └── Footer (Server) — 0 KB client JS    │
  └──────────────────────────────────────────┘
```

### 3.2 How RSC Works

1. Server receives a request.
2. Server renders the component tree. Server Components are rendered to a
   special serialization format (RSC payload), not HTML.
3. Client Components are rendered on the server to HTML (SSR) and their
   code is sent as JS to the client.
4. The browser receives HTML (for immediate display) + RSC payload (for
   React to reconcile) + JS bundle (for client components).
5. React on the client reconciles the RSC payload with the DOM and hydrates
   only the client components.

### 3.3 Server Actions

Server Actions are async functions that run on the server, called from client
components via form actions or event handlers:

```typescript
// app/actions.ts
'use server';

export async function createComment(formData: FormData) {
  const text = formData.get('text') as string;

  // Validate input (server-side)
  if (!text || text.length > 1000) {
    return { error: 'Invalid comment' };
  }

  // Direct database access — no API route needed
  await db.comments.create({
    data: { text, authorId: getCurrentUser().id }
  });

  revalidatePath('/articles');
}
```

```typescript
// app/comment-form.tsx
'use client';

import { createComment } from './actions';

export function CommentForm() {
  return (
    <form action={createComment}>
      <textarea name="text" required />
      <button type="submit">Submit</button>
    </form>
  );
}
```

**Progressive enhancement:** This form works without JavaScript. The browser
submits a regular form POST. With JavaScript, React intercepts the submission
and handles it with a fetch call, providing loading states and optimistic updates.

### 3.4 RSC Composition Rules

```typescript
// Server Component CAN import Client Component
// (Server) Layout.tsx
import { InteractiveWidget } from './InteractiveWidget'; // 'use client'
export default function Layout({ children }) {
  const data = await fetchData(); // async — server only
  return (
    <div>
      <InteractiveWidget initialData={data} />
      {children}
    </div>
  );
}

// Client Component CANNOT import Server Component directly
// But CAN receive Server Components as children (composition)
// (Client) InteractiveWidget.tsx
'use client';
export function InteractiveWidget({ children }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button onClick={() => setOpen(!open)}>Toggle</button>
      {open && children}  {/* children can be a Server Component */}
    </div>
  );
}

// Usage in a Server Component:
<InteractiveWidget>
  <ServerRenderedContent />  {/* This is a Server Component passed as children */}
</InteractiveWidget>
```

### 3.5 Data Fetching in RSC

```typescript
// Direct data access in Server Components — no useEffect, no loading state
export default async function ProductPage({ params }: { params: { id: string } }) {
  // These run in parallel on the server
  const [product, reviews] = await Promise.all([
    db.products.findUnique({ where: { id: params.id } }),
    db.reviews.findMany({ where: { productId: params.id } }),
  ]);

  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <ReviewList reviews={reviews} />
    </div>
  );
}

// Request deduplication: React caches fetch() calls with the same URL
// within a single render pass
async function getUser() {
  // This fetch is automatically deduplicated — called once even if
  // multiple components call getUser()
  const res = await fetch('https://api.example.com/user');
  return res.json();
}
```

---

## 4. Virtual DOM vs Signals

### 4.1 Virtual DOM (React Model)

React re-renders the entire component subtree when state changes, diffs the
virtual DOM against the previous virtual DOM, and applies minimal DOM patches.

```
State change in Component B:
  1. Re-run Component B's render function → new VDOM subtree
  2. Diff old VDOM vs new VDOM
  3. Compute minimal DOM operations (patch list)
  4. Apply patches to real DOM

  ┌─────────┐         ┌─────────┐
  │ Old VDOM │  diff   │ New VDOM │
  │  ┌─A─┐  │ ──────→ │  ┌─A─┐  │ ──→ Patch: update B's text node
  │  │ B │  │         │  │ B'│  │
  │  │ C │  │         │  │ C │  │
  │  └───┘  │         │  └───┘  │
  └─────────┘         └─────────┘
```

**Cost:** Re-rendering the entire subtree is O(n) in component tree size, even
if only one leaf changed. React mitigates this with memoization (`React.memo`,
`useMemo`, `useCallback`), but the developer must opt in.

### 4.2 Signals (Fine-Grained Reactivity)

Signals track reactive values and their subscribers. When a signal updates,
only the specific DOM nodes that read that signal are updated — no diffing,
no virtual DOM, no re-rendering of parent components.

```
Signal: count = signal(0)

Component A reads count → subscribes to count
Component B does NOT read count → unaffected

count.set(1):
  Only Component A's DOM node updates
  No diffing, no re-render of parent, no VDOM
```

**Implementations:**
- **SolidJS:** Compiled, signals are the core primitive.
- **Preact Signals:** Drop-in for Preact, also works with React (via adapter).
- **Angular Signals:** Added in Angular 16+.
- **Vue Composition API:** `ref()` and `reactive()` are signal-like.
- **Svelte 5 (runes):** `$state`, `$derived`, `$effect` — compiler-aided signals.
- **Qwik:** Serializable signals for resumability.

### 4.3 SolidJS Signals Example

```typescript
import { createSignal, createEffect, createMemo } from 'solid-js';

function Counter() {
  const [count, setCount] = createSignal(0);

  // Derived value — recomputed only when count changes
  const doubled = createMemo(() => count() * 2);

  // Side effect — runs only when count changes
  createEffect(() => {
    console.log(`Count is now: ${count()}`);
  });

  return (
    <div>
      <p>Count: {count()}</p>       {/* This text node updates directly */}
      <p>Doubled: {doubled()}</p>   {/* This text node updates directly */}
      <button onClick={() => setCount(c => c + 1)}>Increment</button>
    </div>
  );
}
// The Counter function runs ONCE. Only the signal-reading DOM nodes update.
// In React, the entire function re-runs on every state change.
```

### 4.4 Comparison

| Aspect | Virtual DOM (React) | Signals (Solid/Vue/Svelte) |
|---|---|---|
| **Update granularity** | Component subtree | Individual DOM nodes |
| **Diffing** | O(n) tree diff per update | No diffing needed |
| **Memoization** | Manual (`React.memo`, `useMemo`) | Automatic (dependency tracking) |
| **Initial render** | Fast (JSX → VDOM → DOM) | Fast (JSX → DOM, no VDOM) |
| **Update perf** | Good (batched, concurrent) | Better (surgical DOM updates) |
| **Bundle size** | ~40KB (React + ReactDOM) | ~7KB (SolidJS) |
| **Mental model** | "Render = function of state" | "Reactive graph of dependencies" |
| **Ecosystem** | Massive | Growing |
| **Debugging** | React DevTools (component tree) | Harder (no component re-renders to trace) |

### 4.5 React Compiler (React 19+)

The React Compiler automatically memoizes components and values, eliminating
the need for manual `useMemo`, `useCallback`, and `React.memo`:

```typescript
// Before React Compiler: manual memoization
function TodoList({ todos, filter }) {
  const filtered = useMemo(
    () => todos.filter(t => t.status === filter),
    [todos, filter]
  );
  const handleClick = useCallback((id) => { /* ... */ }, []);
  return filtered.map(t => <TodoItem key={t.id} todo={t} onClick={handleClick} />);
}

// With React Compiler: write plain code, compiler adds memoization
function TodoList({ todos, filter }) {
  const filtered = todos.filter(t => t.status === filter);
  const handleClick = (id) => { /* ... */ };
  return filtered.map(t => <TodoItem key={t.id} todo={t} onClick={handleClick} />);
}
// Compiler detects what needs memoization and inserts it during build
```

---

## 5. The Critical Rendering Path

### 5.1 From HTML to Pixels

```
HTML bytes → Parse → DOM tree
                        │
                        ├──→ Render Tree (visible elements only)
                        │         │
CSS bytes → Parse → CSSOM tree ───┘         │
                                    Layout (geometry)
                                        │
                                    Paint (pixels)
                                        │
                                    Composite (layers → GPU)
```

**Step-by-step:**
1. **HTML → DOM:** Parser constructs the Document Object Model.
2. **CSS → CSSOM:** Parser constructs the CSS Object Model. CSS is
   render-blocking — the browser won't paint until CSSOM is complete.
3. **DOM + CSSOM → Render Tree:** Only visible elements (no `display: none`,
   no `<head>` contents).
4. **Layout (Reflow):** Calculate geometry: position, size, margins of every
   element. O(n) in element count.
5. **Paint:** Fill pixels: text, colors, images, borders, shadows. Recorded as
   a list of draw operations.
6. **Composite:** Assemble painted layers (z-index, transforms, opacity) on the
   GPU. Fastest step.

### 5.2 Render-Blocking Resources

**CSS is render-blocking:** The browser will not paint any content until all CSS
in `<head>` is downloaded and parsed. Critical CSS should be inlined.

**JavaScript is parser-blocking** (by default): When the parser encounters a
`<script>` tag, it stops DOM construction, downloads, and executes the script.

```html
<!-- Parser-blocking (bad for FCP) -->
<script src="/app.js"></script>

<!-- Defer: download in parallel, execute after DOM parse -->
<script defer src="/app.js"></script>

<!-- Async: download in parallel, execute immediately when ready -->
<!-- (order not guaranteed — only for independent scripts) -->
<script async src="/analytics.js"></script>

<!-- Module scripts are deferred by default -->
<script type="module" src="/app.js"></script>
```

### 5.3 CSS Triggers

Different CSS property changes trigger different pipeline stages:

```
transform, opacity       → Composite only    (cheapest)
color, background        → Paint + Composite
width, height, margin    → Layout + Paint + Composite (most expensive)
top, left, position      → Layout + Paint + Composite
font-size                → Layout + Paint + Composite
```

**Rule:** Animate only `transform` and `opacity` for smooth 60fps animations.
Use `will-change: transform` to promote an element to its own compositor layer
(but remove it when animation ends — keeping it permanently wastes GPU memory).

---

## 6. Bundle Optimization

### 6.1 Code Splitting

```typescript
// Route-based splitting (most impactful)
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}

// Component-based splitting (for heavy components)
const HeavyChart = lazy(() => import('./components/HeavyChart'));

function Dashboard() {
  return (
    <div>
      <Summary />  {/* loads with the page */}
      <Suspense fallback={<ChartSkeleton />}>
        <HeavyChart />  {/* loaded when rendered */}
      </Suspense>
    </div>
  );
}
```

### 6.2 Tree Shaking

Dead-code elimination based on ES module static analysis:

```typescript
// math.ts — ES modules (tree-shakeable)
export function add(a: number, b: number) { return a + b; }
export function multiply(a: number, b: number) { return a * b; }
export function complexUnusedFunction() { /* 500 lines */ }

// consumer.ts
import { add } from './math';  // only 'add' is included in bundle
// multiply and complexUnusedFunction are eliminated

// CJS modules are NOT tree-shakeable:
const math = require('./math');  // entire module included
```

**Tree shaking prerequisites:**
- ES module syntax (`import`/`export`).
- `"sideEffects": false` in `package.json` (tells bundler the module has no
  side effects, safe to eliminate unused exports).
- No dynamic `import()` of the target module.

### 6.3 Bundle Analysis

```bash
# webpack
npx webpack-bundle-analyzer dist/stats.json

# Vite
npx vite-bundle-visualizer

# Next.js
ANALYZE=true next build  # with @next/bundle-analyzer

# General: source-map-explorer
npx source-map-explorer dist/app.*.js
```

**What to look for:**
- Single large chunk (should be split).
- Duplicate dependencies (same library in multiple chunks).
- Dev-only code in production bundle (should be stripped).
- Unused library code (tree shaking not working, or CJS import).

### 6.4 Import Cost Awareness

| Library | Minified + gzipped | Alternative |
|---|---|---|
| moment.js | ~72 KB | date-fns (~1-5 KB per function, tree-shakeable) |
| lodash (full) | ~71 KB | lodash-es (tree-shakeable) or native JS |
| chart.js | ~62 KB | lightweight-charts, uPlot |
| antd (full) | ~200+ KB | cherry-pick imports + tree shaking |

### 6.5 Compression

```
Source → Minify → Compress → Serve

Minification: remove whitespace, shorten variables, dead code elimination
Compression: gzip (~70% reduction) or Brotli (~80% reduction)
```

```nginx
# Nginx: enable Brotli compression
brotli on;
brotli_types text/html text/css application/javascript application/json;
brotli_comp_level 6;

# Fallback to gzip for clients that don't support Brotli
gzip on;
gzip_types text/html text/css application/javascript application/json;
```

---

## 7. Module Federation and Micro-Frontends

### 7.1 The Problem

Large frontend applications with many teams become deployment bottlenecks.
Team A cannot ship their header update until Team B's footer fix passes CI.

### 7.2 Module Federation (Webpack 5 / Rspack)

Module Federation allows separately built applications to share code at runtime:

```
┌──────────────────┐          ┌──────────────────┐
│ Host App (Shell)  │          │ Remote App       │
│                   │ runtime  │ (Checkout)       │
│ import('checkout/ │←─import──│                  │
│   CheckoutFlow')  │          │ exposes:         │
│                   │          │   CheckoutFlow   │
│ has: React v18    │──shared──│ needs: React v18 │
│  (shared, single  │          │ (uses host's)    │
│   instance)       │          │                  │
└──────────────────┘          └──────────────────┘
```

**Host configuration (webpack):**
```javascript
// webpack.config.js (Host)
new ModuleFederationPlugin({
  name: 'host',
  remotes: {
    checkout: 'checkout@https://checkout.example.com/remoteEntry.js',
  },
  shared: {
    react: { singleton: true, requiredVersion: '^18.0.0' },
    'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
  },
});
```

**Remote configuration:**
```javascript
// webpack.config.js (Remote)
new ModuleFederationPlugin({
  name: 'checkout',
  filename: 'remoteEntry.js',
  exposes: {
    './CheckoutFlow': './src/components/CheckoutFlow',
  },
  shared: {
    react: { singleton: true, requiredVersion: '^18.0.0' },
    'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
  },
});
```

### 7.3 Alternative Approaches

| Approach | Mechanism | Communication | Deployment |
|---|---|---|---|
| **Module Federation** | Runtime JS import | Props, shared state | Independent builds |
| **iframes** | Browser isolation | postMessage | Fully independent |
| **Web Components** | Custom elements | Attributes, events | Framework-agnostic |
| **Import maps** | ES module URLs | ES module imports | Independent builds |
| **Build-time composition** | Package dependency | Props | Coordinated builds |

### 7.4 Micro-Frontend Pitfalls

- **Bundle duplication:** If shared dep versions diverge, both versions are loaded.
- **Routing conflicts:** Multiple routers fighting over the URL.
- **Styling leaks:** CSS from one micro-frontend affects another (use CSS Modules,
  shadow DOM, or naming conventions).
- **Performance:** Loading multiple `remoteEntry.js` files adds latency.
- **Complexity:** Distributed system problems (versioning, contracts, testing)
  now apply to the frontend.

**When NOT to use micro-frontends:** Small team, single codebase manageable,
deployment frequency is acceptable. Micro-frontends add complexity; they solve
organizational scaling, not technical scaling.

---

## 8. Web Workers

### 8.1 Main Thread Bottleneck

The browser's main thread handles: DOM rendering, CSS layout, JavaScript
execution, event handling, painting. Long-running JavaScript blocks all of these.

A 100ms computation freezes the UI for 100ms. At 60fps, each frame has 16.7ms.
Anything over ~50ms is perceptible jank.

### 8.2 Dedicated Workers

```typescript
// worker.ts
self.onmessage = (event: MessageEvent<{ data: number[] }>) => {
  const { data } = event.data;

  // CPU-heavy work — runs off main thread
  const result = data
    .map(n => expensiveComputation(n))
    .filter(n => n > threshold)
    .reduce((sum, n) => sum + n, 0);

  self.postMessage({ result });
};

// main.ts
const worker = new Worker(new URL('./worker.ts', import.meta.url), {
  type: 'module',
});

worker.onmessage = (event) => {
  console.log('Result:', event.data.result);
};

worker.postMessage({ data: largeDataset });
```

### 8.3 Transferable Objects

`postMessage` copies data by default (structured clone). For large `ArrayBuffer`s,
use transfer to move ownership without copying:

```typescript
// Main thread: transfer ArrayBuffer (zero-copy)
const buffer = new ArrayBuffer(100_000_000); // 100 MB
worker.postMessage({ buffer }, [buffer]);
// buffer is now detached — main thread can no longer access it

// Worker: receives the buffer directly, no copy
self.onmessage = (event) => {
  const { buffer } = event.data;
  const view = new Float64Array(buffer);
  // process the data
};
```

### 8.4 SharedArrayBuffer and Atomics

For true shared memory between threads:

```typescript
// Main thread
const sharedBuffer = new SharedArrayBuffer(1024);
const sharedArray = new Int32Array(sharedBuffer);

worker.postMessage({ buffer: sharedBuffer });

// Worker — same memory, no copying
self.onmessage = (event) => {
  const array = new Int32Array(event.data.buffer);
  Atomics.add(array, 0, 1);        // atomic increment
  Atomics.wait(array, 0, oldValue); // wait until value changes
  Atomics.notify(array, 0);        // wake up waiting threads
};
```

**Requirement:** `SharedArrayBuffer` requires CORS isolation headers:
```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

### 8.5 Comlink (Worker Ergonomics)

```typescript
// worker.ts
import { expose } from 'comlink';

const api = {
  async processImage(imageData: ImageData): Promise<ImageData> {
    // heavy computation
    return processedData;
  },
};

expose(api);

// main.ts
import { wrap } from 'comlink';

const worker = new Worker(new URL('./worker.ts', import.meta.url));
const api = wrap<typeof import('./worker')['api']>(worker);

// Looks like a normal async function call
const result = await api.processImage(imageData);
```

---

## 9. Service Workers and Offline

### 9.1 Service Worker Lifecycle

```
                    ┌──────────┐
     Registration──→│Installing│
                    └────┬─────┘
                         │ install event (precache assets)
                    ┌────▼─────┐
                    │ Waiting  │ (if old SW is still active)
                    └────┬─────┘
                         │ old SW terminates or skipWaiting()
                    ┌────▼─────┐
                    │  Active  │ ← intercepts fetch events
                    └────┬─────┘
                         │ replaced by new version
                    ┌────▼──────┐
                    │Redundant │
                    └───────────┘
```

### 9.2 Registration

```typescript
// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });
  });
}
```

### 9.3 Caching Strategies

```typescript
// sw.ts

// Strategy 1: Cache First (offline-first)
// Best for: static assets (CSS, JS, images, fonts)
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        const clone = response.clone();
        caches.open('static-v1').then((cache) => cache.put(event.request, clone));
        return response;
      });
    })
  );
});

// Strategy 2: Network First (freshness priority)
// Best for: API calls, HTML pages
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const clone = response.clone();
        caches.open('dynamic-v1').then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request))  // fallback to cache if offline
  );
});

// Strategy 3: Stale-While-Revalidate
// Best for: content that should load fast but stay fresh
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.open('swr-v1').then((cache) => {
      return cache.match(event.request).then((cached) => {
        const fetchPromise = fetch(event.request).then((response) => {
          cache.put(event.request, response.clone());
          return response;
        });
        return cached || fetchPromise;
      });
    })
  );
});
```

### 9.4 Workbox (Google)

```typescript
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { CacheFirst, NetworkFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';

// Precache build artifacts
precacheAndRoute(self.__WB_MANIFEST);

// Cache images with Cache First
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images',
    plugins: [new ExpirationPlugin({ maxEntries: 50, maxAgeSeconds: 30 * 24 * 60 * 60 })],
  })
);

// API calls with Network First
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({ cacheName: 'api-cache', networkTimeoutSeconds: 3 })
);
```

---

## 10. State Management

### 10.1 State Categories

| Category | Examples | Tool |
|---|---|---|
| **Server state** | API data, DB records | TanStack Query, SWR, tRPC |
| **Client state** | UI state, form state, local preferences | Zustand, Jotai, signals, useState |
| **URL state** | Filters, pagination, search params | URLSearchParams, router state |
| **Form state** | Field values, validation, dirty tracking | React Hook Form, Formik |

**Rule:** Do not duplicate server state into client stores. TanStack Query (or
equivalent) manages the cache, deduplication, refetching, and staleness.

### 10.2 TanStack Query (React Query)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function useProducts(category: string) {
  return useQuery({
    queryKey: ['products', category],
    queryFn: () => fetchProducts(category),
    staleTime: 5 * 60 * 1000,      // consider data fresh for 5 minutes
    gcTime: 30 * 60 * 1000,        // garbage collect after 30 minutes
    retry: 3,
    refetchOnWindowFocus: true,     // refetch when user returns to tab
  });
}

function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    // Optimistic update
    onMutate: async (newProduct) => {
      await queryClient.cancelQueries({ queryKey: ['products'] });
      const previous = queryClient.getQueryData(['products']);
      queryClient.setQueryData(['products'], (old) => [...old, newProduct]);
      return { previous };
    },
    onError: (err, newProduct, context) => {
      queryClient.setQueryData(['products'], context.previous);  // rollback
    },
  });
}
```

### 10.3 Zustand (Client State)

```typescript
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface UIStore {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

const useUIStore = create<UIStore>()(
  devtools(
    persist(
      (set) => ({
        sidebarOpen: true,
        theme: 'light',
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        setTheme: (theme) => set({ theme }),
      }),
      { name: 'ui-storage' }  // persists to localStorage
    )
  )
);

// Usage — component only re-renders when its specific selector changes
function Sidebar() {
  const open = useUIStore((s) => s.sidebarOpen);
  const toggle = useUIStore((s) => s.toggleSidebar);
  // ...
}
```

### 10.4 Jotai (Atomic State)

```typescript
import { atom, useAtom } from 'jotai';

// Primitive atom
const countAtom = atom(0);

// Derived atom (computed, like a selector)
const doubledAtom = atom((get) => get(countAtom) * 2);

// Async atom (integrates with Suspense)
const userAtom = atom(async (get) => {
  const id = get(userIdAtom);
  const response = await fetch(`/api/users/${id}`);
  return response.json();
});

// Write-only atom (action)
const incrementAtom = atom(null, (get, set) => {
  set(countAtom, get(countAtom) + 1);
});
```

### 10.5 URL as State

```typescript
import { useSearchParams } from 'react-router-dom';

function ProductList() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filter = searchParams.get('filter') || 'all';
  const sort = searchParams.get('sort') || 'newest';
  const page = parseInt(searchParams.get('page') || '1');

  const handleFilterChange = (newFilter: string) => {
    setSearchParams((prev) => {
      prev.set('filter', newFilter);
      prev.set('page', '1');  // reset page on filter change
      return prev;
    });
  };

  // URL: /products?filter=electronics&sort=price&page=2
  // Shareable, bookmarkable, back-button works
}
```

---

## 11. Progressive Enhancement

### 11.1 Philosophy

Build the base experience with HTML and CSS. Layer JavaScript on top for
enhanced interactivity. If JavaScript fails (network error, ad blocker, old
browser), the base experience still works.

```
Layer 0: HTML — content structure, forms, links (works everywhere)
Layer 1: CSS — layout, styling, basic animations (works without JS)
Layer 2: JavaScript — rich interactivity, SPA navigation, real-time updates
```

### 11.2 Forms

```html
<!-- Progressive enhancement: form works without JS -->
<form method="POST" action="/api/subscribe">
  <input type="email" name="email" required />
  <button type="submit">Subscribe</button>
</form>

<!-- With JS: intercept and enhance -->
<script type="module">
  const form = document.querySelector('form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const response = await fetch(form.action, {
      method: 'POST',
      body: data,
    });
    // Show success message, update UI without page reload
  });
</script>
```

### 11.3 The `<noscript>` Trap

Don't use `<noscript>` as a catch-all. Instead, design the HTML to work by
default, then enhance with JavaScript. The HTML-first approach is superior
because it works even when JavaScript partially loads or errors.

---

## 12. Design Systems

### 12.1 What a Design System Contains

```
Design System
├── Design Tokens (variables)
│   ├── Colors
│   ├── Typography (families, sizes, weights, line heights)
│   ├── Spacing (scale)
│   ├── Borders (radii, widths)
│   ├── Shadows
│   └── Motion (durations, easings)
├── Components
│   ├── Primitives (Button, Input, Select, Checkbox)
│   ├── Composites (Card, Dialog, Dropdown, DataTable)
│   └── Patterns (Form layouts, Navigation patterns)
├── Documentation
│   ├── Usage guidelines
│   ├── Accessibility requirements
│   └── Do/don't examples
└── Tooling
    ├── Storybook (component playground)
    ├── Chromatic (visual regression testing)
    └── Token export pipeline (Figma → code)
```

### 12.2 Design Tokens

```css
/* tokens.css */
:root {
  /* Color — using oklch for perceptual uniformity */
  --color-primary-50: oklch(97% 0.02 250);
  --color-primary-500: oklch(55% 0.18 250);
  --color-primary-900: oklch(25% 0.10 250);

  --color-surface: oklch(99% 0.005 0);
  --color-text: oklch(15% 0 0);
  --color-text-muted: oklch(45% 0 0);

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.8125rem);
  --text-sm: clamp(0.8125rem, 0.76rem + 0.26vw, 0.875rem);
  --text-base: clamp(1rem, 0.92rem + 0.4vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1rem + 0.5vw, 1.25rem);
  --text-xl: clamp(1.25rem, 1.1rem + 0.75vw, 1.5rem);

  /* Spacing (4px base) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;
  --space-16: 4rem;

  /* Motion */
  --duration-fast: 100ms;
  --duration-normal: 200ms;
  --duration-slow: 400ms;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
}
```

### 12.3 Headless Component Libraries

Headless libraries provide behavior and accessibility without styling:

| Library | Framework | Approach |
|---|---|---|
| **Radix UI** | React | Unstyled primitives, composable |
| **Headless UI** | React, Vue | Tailwind Labs, minimal |
| **Ark UI** | React, Vue, Solid | State machines (Zag.js) |
| **React Aria** | React | Adobe, accessibility-first |
| **Melt UI** | Svelte | Builder pattern |

Build your design system on top of a headless library to get accessibility and
keyboard navigation for free, then apply your own styling.

---

## 13. Core Web Vitals Engineering

### 13.1 Metrics

| Metric | Full name | Measures | Target |
|---|---|---|---|
| **LCP** | Largest Contentful Paint | Loading performance | < 2.5s |
| **INP** | Interaction to Next Paint | Responsiveness | < 200ms |
| **CLS** | Cumulative Layout Shift | Visual stability | < 0.1 |

### 13.2 LCP Optimization

Common LCP elements: hero images, large text blocks, video poster images.

```html
<!-- Preload the LCP image -->
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high" />

<!-- Use fetchpriority on the img element -->
<img
  src="/hero.webp"
  alt="Hero"
  width="1200"
  height="600"
  fetchpriority="high"
  loading="eager"
  decoding="async"
/>

<!-- Avoid lazy-loading the LCP image -->
<!-- loading="lazy" on the LCP element delays it -->
```

**LCP checklist:**
- Preload the LCP resource.
- Eliminate render-blocking CSS/JS before LCP.
- Use CDN for static assets.
- Compress images (AVIF > WebP > JPEG).
- Server response time (TTFB) under 800ms.

### 13.3 INP Optimization

INP measures the time from user interaction (click, tap, keypress) to the
next visual update. Long main-thread tasks are the primary cause.

```typescript
// BAD: long synchronous task blocks the main thread
button.addEventListener('click', () => {
  const result = expensiveComputation(data);  // 200ms blocking
  updateDOM(result);
});

// GOOD: yield to the browser between chunks
button.addEventListener('click', async () => {
  // Process in chunks, yielding between each
  for (const chunk of chunks) {
    processChunk(chunk);
    await scheduler.yield();  // let browser paint and handle events
  }
  updateDOM(results);
});

// GOOD: move computation off main thread
button.addEventListener('click', () => {
  worker.postMessage({ data });  // non-blocking
});
worker.onmessage = (e) => updateDOM(e.data.result);
```

### 13.4 CLS Optimization

Layout shifts occur when visible elements change position without user input.

```html
<!-- BAD: image without dimensions causes layout shift -->
<img src="/photo.jpg" alt="Photo" />

<!-- GOOD: explicit dimensions reserve space -->
<img src="/photo.jpg" alt="Photo" width="800" height="600" />

<!-- GOOD: aspect-ratio for responsive images -->
<img src="/photo.jpg" alt="Photo" style="aspect-ratio: 4/3; width: 100%;" />
```

**CLS causes:**
- Images without width/height.
- Ads/embeds injected dynamically.
- Web fonts causing FOUT/FOIT.
- Dynamic content inserted above existing content.

---

## 14. CSS Architecture

### 14.1 Methodologies

| Methodology | Convention | Example |
|---|---|---|
| **BEM** | Block__Element--Modifier | `.card__title--highlighted` |
| **CSS Modules** | Auto-scoped class names | `styles.cardTitle` → `.cardTitle_a1b2c3` |
| **Tailwind CSS** | Utility-first | `class="flex items-center gap-4 p-2"` |
| **CSS-in-JS** | Runtime styles | `styled.div\`color: red\`` |
| **Vanilla Extract** | Zero-runtime CSS-in-TS | `style({ color: 'red' })` |

### 14.2 CSS Layers (Cascade Layers)

```css
/* Define layer order — specificity within layers respects this order */
@layer reset, base, components, utilities;

@layer reset {
  *, *::before, *::after { box-sizing: border-box; margin: 0; }
}

@layer base {
  body { font-family: var(--font-sans); color: var(--color-text); }
}

@layer components {
  .card { padding: var(--space-4); border-radius: 0.5rem; }
}

@layer utilities {
  .sr-only { position: absolute; width: 1px; height: 1px; clip: rect(0 0 0 0); }
}
```

### 14.3 Container Queries

```css
/* Component responds to its container size, not viewport */
.card-container {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 1fr 2fr;
  }
}

@container card (max-width: 399px) {
  .card {
    display: flex;
    flex-direction: column;
  }
}
```

### 14.4 View Transitions API

```typescript
// Single-page app transitions
document.startViewTransition(() => {
  // Update the DOM
  root.innerHTML = newPageContent;
});

/* CSS for the transition */
::view-transition-old(root) {
  animation: fade-out 200ms ease-out;
}

::view-transition-new(root) {
  animation: fade-in 200ms ease-in;
}

/* Named transitions for specific elements */
.hero-image {
  view-transition-name: hero;
}
```

---

## 15. TypeScript Patterns for Frontend

### 15.1 Strict Configuration

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "verbatimModuleSyntax": true
  }
}
```

### 15.2 Discriminated Unions for State

```typescript
// Model loading states as discriminated unions, not booleans
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function renderProducts(state: AsyncState<Product[]>) {
  switch (state.status) {
    case 'idle':
      return null;
    case 'loading':
      return <Skeleton />;
    case 'success':
      return <ProductGrid products={state.data} />;
    case 'error':
      return <ErrorMessage error={state.error} />;
    // TypeScript enforces exhaustive handling
  }
}
```

### 15.3 Branded Types

```typescript
// Prevent mixing up IDs of different entities
type UserId = string & { readonly __brand: 'UserId' };
type OrderId = string & { readonly __brand: 'OrderId' };

function getUser(id: UserId): Promise<User> { /* ... */ }
function getOrder(id: OrderId): Promise<Order> { /* ... */ }

const userId = 'usr_123' as UserId;
const orderId = 'ord_456' as OrderId;

getUser(userId);    // OK
getUser(orderId);   // Type error: OrderId is not assignable to UserId
```

### 15.4 Component Props Patterns

```typescript
// Polymorphic component (render as different HTML elements)
type ButtonProps<T extends React.ElementType = 'button'> = {
  as?: T;
  variant: 'primary' | 'secondary' | 'ghost';
  children: React.ReactNode;
} & Omit<React.ComponentPropsWithoutRef<T>, 'as' | 'variant'>;

function Button<T extends React.ElementType = 'button'>({
  as,
  variant,
  children,
  ...props
}: ButtonProps<T>) {
  const Component = as || 'button';
  return <Component className={`btn btn-${variant}`} {...props}>{children}</Component>;
}

// Usage
<Button variant="primary" onClick={handleClick}>Submit</Button>
<Button as="a" variant="secondary" href="/about">About</Button>
```

---

## 16. Testing Frontend Applications

### 16.1 Testing Pyramid for Frontend

```
        ┌─────────┐
        │   E2E   │  Few, slow, high confidence
        │ (Playwright) │
        ├─────────┤
        │Integration│  Moderate count
        │(Testing   │  (component + hook tests
        │ Library)  │   with mocked APIs)
        ├─────────┤
        │  Unit    │  Many, fast
        │(Vitest)  │  (pure functions, utilities)
        └─────────┘
```

### 16.2 Component Testing (Testing Library)

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('/api/products', () => {
    return HttpResponse.json([
      { id: '1', name: 'Widget', price: 29.99 },
    ]);
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('renders product list from API', async () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  render(
    <QueryClientProvider client={queryClient}>
      <ProductList />
    </QueryClientProvider>
  );

  // Verify loading state
  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  // Wait for data
  await waitFor(() => {
    expect(screen.getByText('Widget')).toBeInTheDocument();
    expect(screen.getByText('$29.99')).toBeInTheDocument();
  });
});
```

### 16.3 E2E Testing (Playwright)

```typescript
import { test, expect } from '@playwright/test';

test('checkout flow', async ({ page }) => {
  await page.goto('/products');

  // Add product to cart
  await page.getByRole('button', { name: 'Add to cart' }).first().click();

  // Navigate to checkout
  await page.getByRole('link', { name: 'Cart (1)' }).click();

  // Fill shipping info
  await page.getByLabel('Email').fill('test@example.com');
  await page.getByLabel('Address').fill('123 Main St');

  // Submit order
  await page.getByRole('button', { name: 'Place order' }).click();

  // Verify confirmation
  await expect(page.getByText('Order confirmed')).toBeVisible();
});

// Visual regression test
test('homepage visual regression', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png', {
    fullPage: true,
    maxDiffPixels: 100,
  });
});
```

---

## 17. Accessibility Engineering

### 17.1 ARIA Landmarks

```html
<header role="banner">
  <nav aria-label="Main navigation">
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/products" aria-current="page">Products</a></li>
    </ul>
  </nav>
</header>

<main role="main">
  <section aria-labelledby="products-heading">
    <h1 id="products-heading">Products</h1>
    <!-- content -->
  </section>
</main>

<aside role="complementary" aria-label="Related products">
  <!-- sidebar -->
</aside>

<footer role="contentinfo">
  <!-- footer -->
</footer>
```

### 17.2 Focus Management

```typescript
// After route change, move focus to main content
function RouteChangeAnnouncer() {
  const location = useLocation();
  const mainRef = useRef<HTMLElement>(null);

  useEffect(() => {
    mainRef.current?.focus();
  }, [location.pathname]);

  return <main ref={mainRef} tabIndex={-1}>{/* content */}</main>;
}

// Trap focus in modal
function Modal({ isOpen, onClose, children }) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const focusable = modalRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    // Focus first element, trap Tab key within modal
  }, [isOpen]);

  return (
    <div role="dialog" aria-modal="true" ref={modalRef}>
      {children}
    </div>
  );
}
```

### 17.3 Reduced Motion

```css
/* Respect user's motion preference */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

```typescript
// React hook
function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mql = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(mql.matches);
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);
  return reduced;
}
```

---

## 18. Exercises

### Exercise 1: Rendering Strategy Selection

Given these requirements, choose and justify a rendering strategy:
1. Marketing landing page with mostly static content, updated weekly.
2. Real-time stock trading dashboard with sub-second data updates.
3. E-commerce product catalog with 50,000 products, SEO-critical.
4. Internal admin panel for 50 users, behind auth.
5. Documentation site with 500 pages, open-source, community-contributed.

### Exercise 2: Hydration Performance Audit

1. Build a Next.js page with SSR.
2. Add a deliberately slow component (simulate 2s data fetch).
3. Measure the hydration gap using Performance API.
4. Fix using Suspense boundaries and streaming SSR.
5. Compare LCP and TTI before and after.

### Exercise 3: Bundle Diet

1. Take a React project and run `npx source-map-explorer`.
2. Identify the top 3 largest dependencies.
3. For each: find a lighter alternative or implement code splitting.
4. Measure the bundle size reduction.
5. Target: under 150 KB gzipped for the initial load.

### Exercise 4: Service Worker Offline Support

1. Create a simple web app with a list fetched from an API.
2. Implement a service worker with Workbox.
3. Use Network First for API calls, Cache First for static assets.
4. Test offline: disconnect network, verify the app still works.
5. Add an offline indicator banner.

### Exercise 5: Web Worker Computation

1. Create an image processing feature (blur, grayscale, resize).
2. First implement on the main thread. Measure frame drops during processing.
3. Move the computation to a Web Worker.
4. Use Transferable Objects for the ImageData buffer.
5. Compare: main thread vs worker — measure INP impact.

### Exercise 6: Design System Tokens

1. Define a design token system (colors, typography, spacing, motion).
2. Implement as CSS custom properties.
3. Build three components (Button, Card, Input) using only tokens.
4. Add dark mode via a theme class that overrides token values.
5. Set up Storybook with both themes.

### Exercise 7: State Management Architecture

1. Build a product listing page with filters, search, and pagination.
2. Use TanStack Query for server state (product data).
3. Use URL search params for filters, search, and page number.
4. Use Zustand for client-only state (sidebar open/closed, view mode).
5. Verify: refreshing the page preserves filter state (URL), data is
   re-fetched (TanStack Query cache), UI preferences persist (Zustand + localStorage).

### Exercise 8: Accessibility Audit

1. Take an existing web application.
2. Run axe-core automated checks. Fix all critical and serious issues.
3. Test keyboard navigation: can you complete all flows with Tab, Enter, Escape?
4. Test with a screen reader (VoiceOver or NVDA).
5. Add `prefers-reduced-motion` support.

---

## 19. References

- Patterns.dev — rendering patterns. https://www.patterns.dev/
- web.dev — Core Web Vitals. https://web.dev/vitals/
- React documentation. https://react.dev/
- Next.js documentation. https://nextjs.org/docs
- Astro islands architecture. https://docs.astro.build/en/concepts/islands/
- Qwik resumability. https://qwik.dev/docs/concepts/resumable/
- SolidJS reactivity. https://www.solidjs.com/tutorial/introduction_signals
- Module Federation. https://module-federation.io/
- Workbox. https://developer.chrome.com/docs/workbox/
- Testing Library. https://testing-library.com/
- Playwright. https://playwright.dev/
- WCAG 2.2. https://www.w3.org/TR/WCAG22/
- MDN Web Docs — Performance. https://developer.mozilla.org/en-US/docs/Web/Performance
