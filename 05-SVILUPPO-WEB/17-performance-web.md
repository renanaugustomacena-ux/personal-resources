---
corso: "Sviluppo Web"
fase: "5 — Qualità"
modulo: "17"
titolo: "Performance Web"
versione: "Core Web Vitals / Lighthouse 12.x"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01 — HTML5"
  - "02 — CSS3"
  - "04 — JavaScript Fondamenti"
obiettivi:
  - "Misurare e ottimizzare Core Web Vitals (LCP, INP, CLS)"
  - "Implementare lazy loading, code splitting e prefetching"
  - "Ottimizzare immagini con formati moderni (AVIF, WebP)"
  - "Ridurre bundle size e eliminare render-blocking resources"
  - "Configurare caching, CDN e compression"
  - "Utilizzare Lighthouse e Chrome DevTools per profiling"
tag: [performance, Core-Web-Vitals, Lighthouse, lazy-loading, code-splitting, caching, CDN]
---

# Performance Web

> **Modulo 17** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [HTML5](01-html5.md), [CSS3](02-css3.md), [JavaScript Fondamenti](04-javascript-fondamenti.md)
>
> Al termine di questo modulo saprai:
> 1. Misurare e ottimizzare Core Web Vitals (LCP, INP, CLS)
> 2. Implementare lazy loading, code splitting e prefetching
> 3. Ottimizzare immagini con formati moderni (AVIF, WebP)
> 4. Ridurre bundle size e eliminare render-blocking resources
> 5. Configurare caching, CDN e compression
> 6. Utilizzare Lighthouse e Chrome DevTools per profiling
>
> **Tempo stimato:** 5-7 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **Core Web Vitals: LCP < 2.5s, INP < 200ms, CLS < 0.1.**
2. **Image optimization mandatory: WebP/AVIF, responsive srcset.**
3. **Critical CSS inline; defer non-critical.**
4. **Code splitting + lazy load per JS pesante.**


## Panoramica

La performance web non è un requisito secondario né un'ottimizzazione da rimandare alla fase finale dello sviluppo: è un fattore architetturale che influenza direttamente i ricavi, la soddisfazione degli utenti e il posizionamento nei motori di ricerca. Google ha dimostrato che un ritardo di 100 millisecondi nel tempo di caricamento riduce le conversioni dell'1%. Amazon ha stimato che ogni 100ms aggiuntivi di latenza costano l'1% delle vendite. Walmart ha rilevato un incremento del 2% nelle conversioni per ogni secondo di miglioramento nel tempo di caricamento.

Gli utenti moderni sono impazienti: il 53% abbandona un sito mobile se il caricamento supera i 3 secondi. In mercati competitivi, dove decine di alternative sono a un clic di distanza, una pagina lenta equivale a un cliente perso. La performance non è un dettaglio tecnico — è un vantaggio competitivo misurabile.

Dal 2021, Google utilizza ufficialmente le metriche di performance come fattore di ranking attraverso il programma **Core Web Vitals**. Questo significa che siti lenti non solo perdono utenti, ma vengono penalizzati anche nella visibilità organica. Ottimizzare la performance è quindi una strategia che unifica obiettivi di business, esperienza utente e SEO.

### Core Web Vitals

I Core Web Vitals sono un insieme di tre metriche che Google considera essenziali per misurare l'esperienza utente reale:

| Metrica | Cosa Misura | Buono | Da Migliorare | Scarso |
|---------|-------------|-------|---------------|--------|
| **LCP** (Largest Contentful Paint) | Velocità di caricamento percepita — tempo necessario per renderizzare l'elemento visivo più grande nel viewport | ≤ 2.5s | 2.5s – 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | Reattività — latenza complessiva delle interazioni dell'utente durante l'intera visita | ≤ 200ms | 200ms – 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | Stabilità visiva — quantità di spostamenti imprevisti del layout durante il caricamento | ≤ 0.1 | 0.1 – 0.25 | > 0.25 |

Queste metriche vengono raccolte da utenti reali attraverso il Chrome User Experience Report (CrUX) e determinano il badge "page experience" nei risultati di ricerca. Il passaggio da FID a INP nel marzo 2024 ha segnato un'evoluzione significativa: mentre FID misurava solo il ritardo del primo input, INP considera tutte le interazioni durante l'intera sessione, fornendo una valutazione molto più accurata della reattività percepita.

---

## Metriche di Performance

Comprendere le metriche è il primo passo per migliorarle. Ogni metrica cattura un aspetto diverso dell'esperienza utente e richiede strategie di ottimizzazione specifiche.

### First Contentful Paint (FCP)

FCP misura il tempo tra la navigazione e il momento in cui il browser renderizza il primo contenuto dal DOM — testo, immagine, SVG o canvas non bianco. È il primo segnale visivo che qualcosa sta accadendo.

**Soglie:** buono ≤ 1.8s, da migliorare 1.8s – 3.0s, scarso > 3.0s.

FCP è influenzato da tutto ciò che blocca il rendering iniziale: CSS render-blocking, font web che ritardano la visualizzazione del testo, tempo di risposta del server lento.

```javascript
// Misurare FCP con la Performance API
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.name === 'first-contentful-paint') {
      console.log('FCP:', entry.startTime, 'ms');
    }
  }
});
observer.observe({ type: 'paint', buffered: true });
```

**Come migliorare FCP:**

- Ridurre il tempo di risposta del server (TTFB).
- Eliminare le risorse render-blocking: CSS inline per il contenuto above-the-fold, `defer` o `async` per gli script non critici.
- Utilizzare `font-display: swap` per evitare il FOIT (Flash of Invisible Text).
- Precaricare risorse critiche con `<link rel="preload">`.
- Comprimere le risorse con gzip o Brotli.

### Largest Contentful Paint (LCP)

LCP misura quando l'elemento più grande visibile nel viewport termina il rendering. Tipicamente si tratta di un'immagine hero, un video poster, un blocco di testo grande o un elemento di sfondo con immagine CSS. LCP è il Core Web Vital che rappresenta la velocità di caricamento percepita.

**Soglie:** buono ≤ 2.5s, da migliorare 2.5s – 4.0s, scarso > 4.0s.

```javascript
// Identificare l'elemento LCP
const observer = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lastEntry = entries[entries.length - 1]; // l'ultimo è il più accurato
  console.log('Elemento LCP:', lastEntry.element);
  console.log('LCP:', lastEntry.startTime, 'ms');
  console.log('Dimensione:', lastEntry.size);
  console.log('URL (se immagine):', lastEntry.url);
});
observer.observe({ type: 'largest-contentful-paint', buffered: true });
```

**Come migliorare LCP:**

- Preload dell'immagine LCP: `<link rel="preload" as="image" href="hero.webp">`.
- Servire immagini in formati moderni (WebP, AVIF) con dimensioni appropriate.
- Impostare `fetchpriority="high"` sull'immagine LCP.
- Evitare il lazy loading sull'immagine LCP (è above-the-fold).
- Ridurre le catene di richieste critiche.
- Utilizzare un CDN per ridurre la latenza di rete.
- Implementare server-side rendering per il contenuto principale.

### Interaction to Next Paint (INP)

INP misura la reattività complessiva di una pagina alle interazioni dell'utente. A differenza del precedente FID che considerava solo il primo input, INP osserva la latenza di tutte le interazioni (click, tap, pressione tasti) durante l'intera visita e seleziona una delle interazioni più lente come valore rappresentativo, specificamente il valore al 98° percentile (o il valore peggiore se le interazioni sono poche).

**Soglie:** buono ≤ 200ms, da migliorare 200ms – 500ms, scarso > 500ms.

La latenza di un'interazione comprende tre fasi: il ritardo dell'input (tempo tra l'evento e l'inizio del gestore), il tempo di elaborazione del gestore e il ritardo della presentazione (tempo tra la fine del gestore e il next paint).

```javascript
// Misurare INP con la libreria web-vitals
import { onINP } from 'web-vitals';

onINP((metric) => {
  console.log('INP:', metric.value, 'ms');
  console.log('Entries:', metric.entries);
  // Analizzare quale interazione ha generato il valore
  metric.entries.forEach(entry => {
    console.log('Tipo:', entry.name); // "click", "keydown", etc.
    console.log('Processing time:', entry.processingEnd - entry.processingStart);
    console.log('Input delay:', entry.processingStart - entry.startTime);
    console.log('Presentation delay:', entry.startTime + entry.duration - entry.processingEnd);
  });
});
```

**Come migliorare INP:**

- Suddividere i long task (>50ms) in task più piccoli con `scheduler.yield()` o `setTimeout`.
- Spostare il lavoro computazionale pesante in Web Workers.
- Ridurre la dimensione del DOM (target < 1400 elementi).
- Utilizzare `content-visibility: auto` per il rendering differito.
- Minimizzare i ricalcoli di stile ottimizzando i selettori CSS.
- Implementare debounce/throttle sugli event handler ad alta frequenza.

### Cumulative Layout Shift (CLS)

CLS quantifica la stabilità visiva della pagina misurando gli spostamenti imprevisti degli elementi durante il ciclo di vita della pagina. Un layout shift si verifica quando un elemento visibile cambia posizione tra due frame consecutivi senza essere stato innescato da un'interazione utente.

**Soglie:** buono ≤ 0.1, da migliorare 0.1 – 0.25, scarso > 0.25.

Il punteggio CLS viene calcolato come la somma dei punteggi delle "session window" — finestre di massimo 5 secondi con gap massimo di 1 secondo tra un shift e l'altro. Il valore finale è la session window con il punteggio più alto.

```javascript
// Monitorare i layout shifts
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) { // ignora shift causati da interazioni
      console.log('Layout shift:', entry.value);
      console.log('Elementi coinvolti:');
      entry.sources?.forEach(source => {
        console.log(' -', source.node, source.currentRect, source.previousRect);
      });
    }
  }
});
observer.observe({ type: 'layout-shift', buffered: true });
```

**Come migliorare CLS:**

- Specificare sempre `width` e `height` sulle immagini e i video (o usare `aspect-ratio`).
- Riservare spazio per contenuti dinamici (annunci, embed, iframe).
- Utilizzare `font-display: optional` o preload dei font per evitare FOUT.
- Non iniettare contenuto sopra il contenuto esistente (eccezione: in risposta a interazione utente).
- Preferire `transform` per le animazioni anziché proprietà che modificano il layout.
- Usare il tag `<link rel="preload">` per le risorse che influenzano il layout.

### Time to First Byte (TTFB)

TTFB misura il tempo tra la richiesta HTTP e il primo byte della risposta ricevuta dal browser. Include la risoluzione DNS, la connessione TCP, la negoziazione TLS e il tempo di elaborazione del server.

**Soglie:** buono ≤ 800ms, da migliorare 800ms – 1800ms, scarso > 1800ms.

Un TTFB elevato ritarda a cascata tutte le metriche successive. Se il server impiega 2 secondi a rispondere, è matematicamente impossibile ottenere un LCP inferiore a 2.5 secondi.

**Come migliorare TTFB:**

- Utilizzare un CDN per ridurre la distanza geografica tra server e utente.
- Ottimizzare le query al database (indici, caching, connection pooling).
- Implementare caching a livello di server (Redis, Memcached).
- Utilizzare stale-while-revalidate per servire contenuti cached durante l'aggiornamento.
- Aggiornare a HTTP/2 o HTTP/3 per ridurre l'overhead di connessione.
- Considerare edge computing per eseguire la logica vicino all'utente.

### Total Blocking Time (TBT)

TBT misura la quantità totale di tempo durante il quale il thread principale è bloccato abbastanza a lungo da impedire la risposta agli input dell'utente. Tecnicamente, TBT è la somma delle porzioni "bloccanti" di tutti i long task (>50ms) che si verificano tra FCP e Time to Interactive. La porzione bloccante di un task è la durata che eccede i 50ms.

**Soglie:** buono ≤ 200ms, da migliorare 200ms – 600ms, scarso > 600ms.

TBT è una metrica di laboratorio (non raccolta da utenti reali) ed è il migliore proxy di laboratorio per INP.

**Come migliorare TBT:**

- Ridurre il JavaScript eseguito durante il caricamento con code splitting.
- Implementare tree shaking per eliminare il codice morto.
- Differire il caricamento degli script non critici con `defer` o dynamic `import()`.
- Ottimizzare il parsing e la compilazione JS riducendo le dimensioni dei bundle.
- Evitare polyfill non necessari utilizzando `browserslist` e differential serving.

---

## Critical Rendering Path

Il Critical Rendering Path (CRP) è la sequenza di operazioni che il browser esegue per convertire HTML, CSS e JavaScript in pixel sullo schermo. Comprendere questo processo è fondamentale per identificare i colli di bottiglia e ottimizzare il tempo di rendering iniziale.

### Fasi del Rendering

**1. Parsing HTML e costruzione del DOM**

Il browser riceve i byte HTML dal server, li decodifica in caratteri secondo l'encoding specificato, li tokenizza in tag e li assembla nell'albero DOM (Document Object Model). Questo processo è incrementale: il browser inizia a costruire il DOM man mano che riceve l'HTML, senza attendere il download completo.

**2. Costruzione del CSSOM**

Quando il parser HTML incontra un tag `<link>` che referenzia un foglio di stile o un blocco `<style>`, il browser costruisce il CSSOM (CSS Object Model). A differenza del DOM, il CSSOM non può essere costruito incrementalmente: il browser deve attendere il download completo del CSS perché le regole successive possono sovrascrivere quelle precedenti (cascading). Il CSS è quindi una risorsa **render-blocking**.

**3. Costruzione del Render Tree**

Il browser combina DOM e CSSOM per creare il Render Tree, che contiene solo i nodi visibili con i loro stili computati. Gli elementi con `display: none` vengono esclusi, così come `<head>`, `<script>` e altri elementi non visibili. Pseudo-elementi come `::before` e `::after` vengono aggiunti anche se non esistono nel DOM.

**4. Layout (Reflow)**

Il browser calcola la geometria esatta di ogni elemento nel render tree: posizione, dimensioni, margini. Questo processo parte dalla radice e si propaga attraverso tutto l'albero. Un cambio di proprietà geometrica (width, height, top, left, margin, padding, font-size) innesca un nuovo layout, operazione costosa che coinvolge potenzialmente l'intera pagina.

**5. Paint**

Il browser converte il render tree in pixel, gestendo proprietà visive come colori, ombre, bordi, testo e immagini. Il painting avviene su layer separati per ottimizzare gli aggiornamenti successivi.

**6. Compositing**

I layer dipinti vengono combinati nell'ordine corretto (gestendo z-index, opacity, transform 3D) e rasterizzati nel frame finale. Il compositing avviene sulla GPU ed è l'operazione meno costosa, motivo per cui animare proprietà composite-only (transform, opacity) è enormemente più performante.

### Ottimizzare il Critical Rendering Path

```html
<!-- Strategia ottimale per il CRP -->
<head>
  <!-- CSS critico inline — evita richiesta di rete aggiuntiva -->
  <style>
    /* Solo gli stili necessari per il contenuto above-the-fold */
    body { margin: 0; font-family: system-ui; }
    .hero { min-height: 100vh; display: grid; place-items: center; }
    .hero h1 { font-size: clamp(2rem, 5vw, 4rem); }
  </style>

  <!-- CSS non critico caricato in modo asincrono -->
  <link rel="preload" href="/styles/main.css" as="style"
        onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="/styles/main.css"></noscript>

  <!-- Preconnect ai domini critici -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://cdn.example.com" crossorigin>

  <!-- Preload risorse critiche -->
  <link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/images/hero.avif" as="image" fetchpriority="high">

  <!-- Script critici con defer (non bloccano il parsing) -->
  <script src="/js/app.js" defer></script>
</head>
```

L'obiettivo è minimizzare il numero di risorse render-blocking, ridurre le dimensioni delle risorse critiche e abbreviare la lunghezza del critical path (il numero di round-trip necessari). Ogni risorsa CSS o JavaScript sincrono aggiunge latenza al rendering iniziale.

---

## Loading Performance

L'ottimizzazione del caricamento delle risorse è il primo livello di intervento per migliorare la performance percepita. Le strategie si concentrano sul caricare prima ciò che è critico, differire ciò che non lo è e minimizzare la dimensione di tutto.

### Resource Hints

I resource hints permettono al browser di anticipare operazioni di rete, riducendo la latenza percepita.

```html
<!-- dns-prefetch: risolve il DNS di un dominio in anticipo -->
<!-- Costo basso, utile per domini di terze parti non critici -->
<link rel="dns-prefetch" href="https://analytics.example.com">

<!-- preconnect: DNS + TCP + TLS in anticipo -->
<!-- Più aggressivo di dns-prefetch, usare per domini critici -->
<link rel="preconnect" href="https://api.example.com" crossorigin>

<!-- preload: scarica una risorsa necessaria nella pagina corrente -->
<!-- Alta priorità, il browser la scarica subito -->
<link rel="preload" href="/fonts/brand.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/images/hero.avif" as="image">
<link rel="preload" href="/js/critical-module.js" as="script">

<!-- prefetch: scarica risorse per navigazioni future -->
<!-- Bassa priorità, in idle time -->
<link rel="prefetch" href="/pages/about.html">
<link rel="prefetch" href="/js/dashboard.js" as="script">

<!-- modulepreload: preload ottimizzato per moduli ES -->
<link rel="modulepreload" href="/js/utils.js">
```

Le regole pratiche: `preconnect` per massimo 2-3 domini critici (ogni connessione consuma risorse); `preload` solo per risorse scoperte tardi dal browser (font nei CSS, immagini nei CSS, moduli dinamici); `prefetch` per le risorse della prossima probabile navigazione; `dns-prefetch` come fallback di `preconnect` per i browser meno recenti.

### Lazy Loading di Immagini e Iframe

Il lazy loading differisce il caricamento delle risorse below-the-fold fino a quando non sono prossime a entrare nel viewport, riducendo drasticamente i dati trasferiti al caricamento iniziale.

```html
<!-- Lazy loading nativo — supportato da tutti i browser moderni -->
<img src="product.webp" alt="Prodotto" loading="lazy" width="400" height="300">

<!-- Attenzione: NON usare lazy loading sulle immagini above-the-fold -->
<img src="hero.avif" alt="Hero" loading="eager" fetchpriority="high"
     width="1200" height="600">

<!-- Lazy loading per iframe -->
<iframe src="https://www.youtube.com/embed/xyz" loading="lazy"
        width="560" height="315" title="Video tutorial"></iframe>
```

```javascript
// Lazy loading avanzato con Intersection Observer
// Utile quando serve controllo fine (es. soglia personalizzata, callback)
const lazyImages = document.querySelectorAll('img[data-src]');

const imageObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      if (img.dataset.srcset) {
        img.srcset = img.dataset.srcset;
      }
      img.classList.add('loaded');
      observer.unobserve(img);
    }
  });
}, {
  rootMargin: '200px 0px' // inizia a caricare 200px prima del viewport
});

lazyImages.forEach(img => imageObserver.observe(img));
```

### Script Loading: async vs defer

La modalità di caricamento degli script ha un impatto diretto sul Critical Rendering Path.

```html
<!-- Script sincrono (default) — BLOCCA il parsing HTML -->
<!-- Il parser si ferma, scarica lo script, lo esegue, poi riprende -->
<script src="app.js"></script>

<!-- async — scarica in parallelo, ESEGUE appena disponibile -->
<!-- Blocca il parsing solo durante l'esecuzione -->
<!-- Ordine di esecuzione NON garantito tra più script async -->
<!-- Ideale per: analytics, annunci, script indipendenti -->
<script src="analytics.js" async></script>

<!-- defer — scarica in parallelo, ESEGUE dopo il parsing completo -->
<!-- Ordine di esecuzione GARANTITO tra più script defer -->
<!-- Esecuzione prima di DOMContentLoaded -->
<!-- Ideale per: la maggior parte degli script applicativi -->
<script src="framework.js" defer></script>
<script src="app.js" defer></script>

<!-- type="module" — si comporta come defer di default -->
<script type="module" src="main.js"></script>
```

La regola generale: usare `defer` per gli script applicativi che dipendono dal DOM o tra loro; `async` solo per script veramente indipendenti (analytics, tracking); evitare script sincroni nel `<head>` a meno che non siano CSS critico inline.

### Code Splitting

Il code splitting suddivide il bundle JavaScript in frammenti più piccoli che vengono caricati on-demand, riducendo il JavaScript iniziale che il browser deve scaricare, parsare e compilare.

```javascript
// Route-based splitting con React.lazy
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));
const Analytics = lazy(() => import('./pages/Analytics'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </Suspense>
  );
}

// Component-level splitting per componenti pesanti
const HeavyChart = lazy(() => import('./components/HeavyChart'));
const MarkdownEditor = lazy(() => import('./components/MarkdownEditor'));

// Dynamic import condizionale
async function loadPdfViewer() {
  if (userWantsPdf) {
    const { PdfViewer } = await import('./components/PdfViewer');
    renderPdfViewer(PdfViewer);
  }
}
```

### Tree Shaking

Il tree shaking è il processo attraverso cui il bundler (webpack, Rollup, esbuild) elimina il codice esportato ma mai importato, riducendo la dimensione finale del bundle. Funziona solo con i moduli ES (`import`/`export`), non con CommonJS (`require`).

```javascript
// utils.js — modulo con multiple esportazioni
export function formatDate(date) { /* ... */ }
export function formatCurrency(amount) { /* ... */ }
export function formatPhoneNumber(phone) { /* ... */ }
export function formatAddress(address) { /* ... */ }

// app.js — importa solo ciò che serve
import { formatDate, formatCurrency } from './utils';
// formatPhoneNumber e formatAddress vengono eliminati dal bundle

// ATTENZIONE: gli effetti collaterali impediscono il tree shaking
// Questo import viene mantenuto anche se non si usa nulla:
import './polyfills'; // effetto collaterale: modifica i prototipi globali

// Configurazione in package.json per dichiarare il pacchetto privo di side effects
// {
//   "name": "my-library",
//   "sideEffects": false
//   // oppure "sideEffects": ["*.css", "./src/setup.js"]
// }
```

Per massimizzare il tree shaking: preferire import con nome (`import { x }`) su import di default; evitare la re-esportazione barrel (`export * from`) su moduli grandi; verificare che le dipendenze offrano moduli ES (`"module"` nel `package.json`).

### Bundle Analysis

Analizzare la composizione del bundle rivela le dipendenze che contribuiscono maggiormente alla dimensione, guidando decisioni informate sull'ottimizzazione.

```bash
# webpack-bundle-analyzer — visualizzazione interattiva treemap
npx webpack --profile --json > stats.json
npx webpack-bundle-analyzer stats.json

# source-map-explorer — analisi basata su source map
npx source-map-explorer dist/js/*.js

# bundlephobia — controlla la dimensione di un pacchetto npm PRIMA di installarlo
# https://bundlephobia.com/package/lodash@4.17.21

# Vite: rollup-plugin-visualizer
# vite.config.js
import { visualizer } from 'rollup-plugin-visualizer';
export default {
  plugins: [
    visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true
    })
  ]
};
```

Strategie comuni dopo l'analisi: sostituire `lodash` con `lodash-es` o singole funzioni (`lodash/debounce`); sostituire `moment.js` con `date-fns` o l'API `Intl` nativa; verificare che le librerie di icone supportino il tree shaking; considerare alternative più leggere per le dipendenze pesanti.

---

## Rendering Performance

Una volta caricata la pagina, la performance durante l'interazione diventa critica. Un'interfaccia che risponde a 60 fps (16.67ms per frame) appare fluida; scendere sotto questa soglia produce visibile stuttering e degrada la percezione di qualità.

### requestAnimationFrame

`requestAnimationFrame` sincronizza le operazioni di aggiornamento visivo con il ciclo di refresh del display, evitando calcoli inutili e garantendo la massima fluidità.

```javascript
// ERRATO: aggiornare la posizione con setInterval
setInterval(() => {
  element.style.left = `${position++}px`; // non sincronizzato con il display
}, 16);

// CORRETTO: usare requestAnimationFrame
function animate(timestamp) {
  // Calcola il delta time per animazioni indipendenti dal frame rate
  const delta = timestamp - previousTimestamp;
  previousTimestamp = timestamp;

  // Aggiorna la posizione in base al tempo trascorso
  position += velocity * delta;
  element.style.transform = `translateX(${position}px)`;

  if (position < targetPosition) {
    requestAnimationFrame(animate);
  }
}
requestAnimationFrame(animate);

// Pattern: batch DOM reads e writes
function updateLayout() {
  // Prima: tutte le letture (non causano reflow se raggruppate)
  const height = element.offsetHeight;
  const width = container.offsetWidth;
  const scrollTop = document.documentElement.scrollTop;

  // Poi: tutte le scritture (un unico reflow)
  requestAnimationFrame(() => {
    element.style.height = `${height * 2}px`;
    other.style.width = `${width / 2}px`;
  });
}
```

### Virtual Scrolling

Quando una lista contiene migliaia di elementi, renderizzarli tutti nel DOM è proibitivamente costoso. Il virtual scrolling mantiene nel DOM solo gli elementi attualmente visibili, ricreandoli al volo durante lo scroll.

```javascript
// Principio del virtual scrolling
class VirtualList {
  constructor(container, items, itemHeight) {
    this.container = container;
    this.items = items;
    this.itemHeight = itemHeight;
    this.visibleCount = Math.ceil(container.clientHeight / itemHeight) + 2;

    // Elemento sentinella per lo scroll nativo
    this.spacer = document.createElement('div');
    this.spacer.style.height = `${items.length * itemHeight}px`;
    container.appendChild(this.spacer);

    this.content = document.createElement('div');
    this.content.style.position = 'relative';
    container.appendChild(this.content);

    container.addEventListener('scroll', () => this.render());
    this.render();
  }

  render() {
    const scrollTop = this.container.scrollTop;
    const startIndex = Math.floor(scrollTop / this.itemHeight);
    const endIndex = Math.min(startIndex + this.visibleCount, this.items.length);

    this.content.innerHTML = '';
    for (let i = startIndex; i < endIndex; i++) {
      const el = document.createElement('div');
      el.textContent = this.items[i];
      el.style.position = 'absolute';
      el.style.top = `${i * this.itemHeight}px`;
      el.style.height = `${this.itemHeight}px`;
      this.content.appendChild(el);
    }
  }
}

// In produzione, utilizzare librerie mature:
// React: @tanstack/react-virtual (TanStack Virtual)
// Vue: vue-virtual-scroller
// Vanilla: virtual-scroll
```

### CSS Containment

La proprietà CSS `contain` limita lo scope dei calcoli di layout, paint e stile, comunicando al browser che un sotto-albero è indipendente dal resto della pagina.

```css
/* contain: layout — il layout interno non influenza il layout esterno */
/* contain: paint — il contenuto non viene disegnato fuori dai bordi */
/* contain: size — la dimensione non dipende dal contenuto figlio */
/* contain: style — i contatori e le proprietà non fuoriescono */

/* Combinazione comune per componenti indipendenti */
.card {
  contain: layout paint;
}

/* contain: strict equivale a size layout paint style */
.widget-container {
  contain: strict;
  width: 300px;
  height: 200px;
}

/* content-visibility: auto — la forma più potente */
/* Il browser salta completamente il rendering degli elementi off-screen */
.article-section {
  content-visibility: auto;
  contain-intrinsic-size: auto 500px; /* dimensione stimata per lo scroll */
}
```

`content-visibility: auto` è particolarmente potente per pagine lunghe: il browser non esegue layout, paint e compositing per le sezioni non visibili, risparmiando potenzialmente centinaia di millisecondi di lavoro di rendering.

### will-change

La proprietà `will-change` avvisa il browser che un elemento sta per essere animato, permettendo ottimizzazioni preparatorie come la promozione su un layer dedicato.

```css
/* Corretto: applicare prima dell'animazione, rimuovere dopo */
.element:hover {
  will-change: transform, opacity;
}

.element.animating {
  will-change: transform;
  transition: transform 0.3s ease;
}

/* ERRATO: applicare a tutto indiscriminatamente */
/* Ogni will-change consuma memoria GPU per il layer */
* {
  will-change: transform; /* MAI fare questo */
}
```

Usare `will-change` con parsimonia: ogni layer dedicato consuma memoria GPU. Applicarlo solo su elementi che stanno effettivamente per essere animati e rimuoverlo al termine dell'animazione.

### Evitare il Layout Thrashing

Il layout thrashing si verifica quando JavaScript legge e scrive proprietà del layout in modo alternato, forzando il browser a ricalcolare il layout ripetutamente (forced synchronous layout).

```javascript
// ERRATO: layout thrashing — forza N reflow
const items = document.querySelectorAll('.item');
items.forEach(item => {
  const height = item.offsetHeight;     // LEGGE → forza reflow
  item.style.height = `${height * 2}px`; // SCRIVE → invalida il layout
  // Al prossimo ciclo, la lettura forza un altro reflow
});

// CORRETTO: separare letture e scritture
const heights = [];

// Fase 1: tutte le letture (un solo reflow)
items.forEach(item => {
  heights.push(item.offsetHeight);
});

// Fase 2: tutte le scritture (un solo reflow alla fine)
items.forEach((item, i) => {
  item.style.height = `${heights[i] * 2}px`;
});

// Alternativa: usare fastdom per batching automatico
import fastdom from 'fastdom';

items.forEach((item, i) => {
  fastdom.measure(() => {
    const height = item.offsetHeight;
    fastdom.mutate(() => {
      item.style.height = `${height * 2}px`;
    });
  });
});
```

Proprietà che causano reflow quando lette: `offsetTop/Left/Width/Height`, `scrollTop/Left/Width/Height`, `clientTop/Left/Width/Height`, `getComputedStyle()`, `getBoundingClientRect()`.

### Animazioni Composite-Only

Le animazioni che utilizzano solo `transform` e `opacity` vengono gestite dal compositor sulla GPU, senza coinvolgere il layout o il paint. Sono enormemente più performanti delle animazioni che modificano proprietà geometriche.

```css
/* LENTO: anima proprietà che causano layout */
.box-slow {
  transition: left 0.3s, top 0.3s, width 0.3s;
}

/* VELOCE: anima solo proprietà composite */
.box-fast {
  transition: transform 0.3s, opacity 0.3s;
}

/* Esempio pratico: menu slide-in */
.sidebar {
  transform: translateX(-100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar.open {
  transform: translateX(0);
}

/* Esempio: fade con scala */
.modal {
  opacity: 0;
  transform: scale(0.95);
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.modal.visible {
  opacity: 1;
  transform: scale(1);
}
```

---

## Image Optimization

Le immagini rappresentano tipicamente il 50-70% dei byte trasferiti in una pagina web. L'ottimizzazione delle immagini è spesso l'intervento con il maggiore impatto sulla performance.

### Formati Moderni: WebP e AVIF

| Formato | Compressione vs JPEG | Supporto Browser | Caratteristiche |
|---------|----------------------|-------------------|-----------------|
| JPEG | baseline | universale | Lossy, nessuna trasparenza |
| PNG | 2-3x più grande | universale | Lossless, trasparenza, ideale per grafiche semplici |
| WebP | 25-35% più piccolo | ~97% (2024) | Lossy e lossless, trasparenza, animazione |
| AVIF | 40-50% più piccolo | ~92% (2024) | Lossy e lossless, trasparenza, HDR, codifica più lenta |

```html
<!-- Servire il formato ottimale con l'elemento <picture> -->
<picture>
  <!-- AVIF per browser compatibili (massima compressione) -->
  <source srcset="hero.avif" type="image/avif">
  <!-- WebP come fallback intermedio -->
  <source srcset="hero.webp" type="image/webp">
  <!-- JPEG come fallback universale -->
  <img src="hero.jpg" alt="Immagine hero" width="1200" height="600"
       loading="eager" fetchpriority="high" decoding="async">
</picture>
```

### Responsive Images con srcset e sizes

`srcset` permette al browser di scegliere la dimensione ottimale dell'immagine in base alla viewport, alla densità di pixel del display e alle condizioni di rete.

```html
<!-- srcset con descrittori di larghezza -->
<img
  srcset="
    product-320w.webp 320w,
    product-640w.webp 640w,
    product-960w.webp 960w,
    product-1280w.webp 1280w,
    product-1920w.webp 1920w
  "
  sizes="
    (max-width: 640px) 100vw,
    (max-width: 1024px) 50vw,
    33vw
  "
  src="product-960w.webp"
  alt="Prodotto in evidenza"
  width="960"
  height="640"
  loading="lazy"
  decoding="async"
>

<!-- srcset con descrittori di densità per immagini a dimensione fissa -->
<img
  srcset="logo.webp 1x, logo@2x.webp 2x, logo@3x.webp 3x"
  src="logo.webp"
  alt="Logo aziendale"
  width="200"
  height="50"
>
```

L'attributo `sizes` è fondamentale: senza di esso, il browser assume che l'immagine occupi l'intera viewport e potrebbe scaricare una versione troppo grande. Il valore deve corrispondere alla dimensione effettiva di rendering dell'immagine.

### CDN-Based Image Optimization

I servizi di ottimizzazione immagini basati su CDN automatizzano la conversione di formato, il ridimensionamento e la compressione, eliminando la necessità di generare manualmente ogni variante.

```html
<!-- Cloudinary: trasformazione tramite URL -->
<img src="https://res.cloudinary.com/demo/image/upload/w_800,f_auto,q_auto/products/shoe.jpg"
     alt="Scarpa" width="800" height="600">
<!-- f_auto: formato ottimale (AVIF/WebP/JPEG) basato sul browser -->
<!-- q_auto: qualità adattiva basata sul contenuto -->
<!-- w_800: ridimensiona a 800px di larghezza -->

<!-- Imgix: approccio simile -->
<img src="https://example.imgix.net/shoe.jpg?w=800&auto=format,compress"
     alt="Scarpa" width="800" height="600">

<!-- Vercel/Next.js Image Optimization integrata -->
<!-- next.config.js -->
<!-- images: { domains: ['cdn.example.com'], formats: ['image/avif', 'image/webp'] } -->
```

### Pattern next/image

Il componente `Image` di Next.js implementa automaticamente tutte le best practice di ottimizzazione immagini.

```jsx
import Image from 'next/image';

// Immagine con dimensioni note
export function ProductCard({ product }) {
  return (
    <Image
      src={product.imageUrl}
      alt={product.name}
      width={400}
      height={300}
      // Formati moderni, lazy loading, srcset automatici
      // placeholder="blur" per preview sfocata durante il caricamento
      placeholder="blur"
      blurDataURL={product.blurHash}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    />
  );
}

// Immagine che riempie il contenitore
export function HeroBanner({ src, alt }) {
  return (
    <div style={{ position: 'relative', width: '100%', height: '60vh' }}>
      <Image
        src={src}
        alt={alt}
        fill
        style={{ objectFit: 'cover' }}
        priority // disabilita lazy loading, aggiunge preload
        sizes="100vw"
      />
    </div>
  );
}
```

---

## Font Optimization

I font web possono causare testo invisibile (FOIT) o testo che cambia aspetto (FOUT) durante il caricamento, impattando sia LCP che CLS. Una strategia di caricamento ottimale minimizza questi effetti.

### font-display

La proprietà `font-display` controlla il comportamento del browser durante il download del font.

```css
@font-face {
  font-family: 'Brand Font';
  src: url('/fonts/brand.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;

  /* swap: mostra il fallback immediatamente, sostituisce quando il font è pronto */
  /* Ottimale per LCP (il testo è subito visibile) ma può causare CLS */
  font-display: swap;
}

@font-face {
  font-family: 'Body Font';
  src: url('/fonts/body.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;

  /* optional: usa il font solo se già in cache, altrimenti usa il fallback */
  /* Ottimale per CLS (nessuno scambio) ma il font potrebbe non apparire al primo caricamento */
  font-display: optional;
}
```

| Valore | Comportamento | Caso d'uso |
|--------|--------------|------------|
| `swap` | Fallback immediato, sostituisce quando pronto | Testo del corpo, heading principali |
| `optional` | Usa il font solo se disponibile velocemente (~100ms) | Font secondari, dove il CLS è prioritario |
| `fallback` | Breve periodo di blocco (~100ms), poi fallback, sostituisce entro ~3s | Compromesso tra swap e optional |
| `block` | Blocca il rendering del testo per ~3s | Icone font (dove il fallback non ha senso) |
| `auto` | Comportamento predefinito del browser | Da evitare |

### Preload dei Font

Il preload dei font è critico perché il browser scopre i font solo quando processa il CSS, aggiungendo latenza al percorso critico.

```html
<!-- Preload dei font critici — il browser li scarica SUBITO -->
<link rel="preload" href="/fonts/brand-regular.woff2" as="font"
      type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/brand-bold.woff2" as="font"
      type="font/woff2" crossorigin>

<!-- crossorigin è OBBLIGATORIO anche per font dello stesso dominio -->
<!-- Senza crossorigin, il browser scarica il font DUE VOLTE -->
```

Precaricare solo i font effettivamente utilizzati above-the-fold. Precaricare troppi font spreca banda e compete con risorse più critiche.

### WOFF2 e Subsetting

WOFF2 offre una compressione superiore del 30% rispetto a WOFF grazie all'algoritmo Brotli. Il subsetting rimuove i glifi non necessari, riducendo drasticamente la dimensione del file.

```bash
# Installare gli strumenti di subsetting
# pip install fonttools brotli

# Subset: mantieni solo i caratteri Latin, Latin Extended e la punteggiatura
pyftsubset "SourceFont.ttf" \
  --output-file="SourceFont-latin.woff2" \
  --flavor=woff2 \
  --layout-features="kern,liga,calt" \
  --unicodes="U+0000-00FF,U+0100-024F,U+2000-206F,U+20AC"
  # U+20AC = simbolo Euro

# Risultato tipico: da 200KB a 20-40KB
```

```css
/* Utilizzare unicode-range per caricare subset specifici on-demand */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+2000-206F;
}

@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-cyrillic.woff2') format('woff2');
  unicode-range: U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
}
/* Il browser scarica solo i subset con glifi effettivamente utilizzati nella pagina */
```

### Variable Fonts

Un variable font condensa tutte le varianti di peso, larghezza e stile in un unico file, riducendo il numero di richieste di rete ed eliminando il download di file separati per ogni variante.

```css
/* Un singolo file sostituisce regular, medium, semibold e bold */
@font-face {
  font-family: 'Inter Variable';
  src: url('/fonts/InterVariable.woff2') format('woff2-variations');
  font-weight: 100 900; /* range completo di pesi */
  font-style: normal;
  font-display: swap;
}

body {
  font-family: 'Inter Variable', system-ui, sans-serif;
}

h1 { font-weight: 750; } /* pesi intermedi impossibili con font statici */
h2 { font-weight: 650; }
p  { font-weight: 400; }

/* Font di sistema come fallback ottimale per le performance */
.system-font {
  font-family: system-ui, -apple-system, BlinkMacSystemFont,
               'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
```

---

## JavaScript Performance

JavaScript è tipicamente la risorsa più costosa in termini di performance: non solo deve essere scaricato, ma anche parsato, compilato e eseguito, ogni fase consumando tempo sul thread principale.

### Riduzione delle Dimensioni del Bundle

```javascript
// 1. Analizzare le importazioni e sostituire librerie pesanti
// PRIMA: importa l'intera libreria lodash (~70KB gzipped)
import _ from 'lodash';
_.debounce(fn, 300);

// DOPO: importa solo la funzione necessaria (~1KB gzipped)
import debounce from 'lodash/debounce';
debounce(fn, 300);

// MEGLIO: implementa utility semplici nativamente
function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

// 2. Sostituire moment.js (~300KB) con alternative leggere
// date-fns: ~10KB (con tree shaking), importazioni modulari
import { format, parseISO, differenceInDays } from 'date-fns';
import { it } from 'date-fns/locale';
format(new Date(), 'dd MMMM yyyy', { locale: it });

// Oppure usare le API native Intl (0KB aggiuntivi)
new Intl.DateTimeFormat('it-IT', {
  day: 'numeric', month: 'long', year: 'numeric'
}).format(new Date());
```

### Dynamic Import

Il dynamic import con `import()` permette di caricare moduli on-demand, eseguendo codice solo quando effettivamente necessario.

```javascript
// Caricare una libreria pesante solo quando serve
document.getElementById('export-btn').addEventListener('click', async () => {
  const { default: xlsx } = await import('xlsx');
  const workbook = xlsx.utils.book_new();
  // ... generazione del file Excel
});

// Caricare componenti condizionalmente
async function renderWidget(type) {
  const modules = {
    chart: () => import('./widgets/ChartWidget'),
    map: () => import('./widgets/MapWidget'),
    table: () => import('./widgets/TableWidget')
  };

  const { default: Widget } = await modules[type]();
  return new Widget();
}

// Prefetch di moduli su hover (caricare in anticipo senza eseguire)
link.addEventListener('mouseenter', () => {
  import('./pages/ProductDetail'); // il browser inizia a scaricare
});
```

### Web Workers per Task CPU-Intensive

I Web Workers eseguono codice JavaScript in un thread separato, evitando di bloccare il thread principale e mantenendo l'interfaccia reattiva durante operazioni pesanti.

```javascript
// worker.js — thread separato
self.onmessage = function(event) {
  const { data, operation } = event.data;

  switch (operation) {
    case 'sort':
      // Ordinamento di milioni di elementi senza bloccare la UI
      const sorted = data.sort((a, b) => a.value - b.value);
      self.postMessage({ result: sorted });
      break;

    case 'search':
      // Ricerca full-text su dataset grandi
      const { items, query } = data;
      const results = items.filter(item =>
        item.title.toLowerCase().includes(query.toLowerCase()) ||
        item.description.toLowerCase().includes(query.toLowerCase())
      );
      self.postMessage({ result: results });
      break;

    case 'transform':
      // Elaborazione immagine (es. filtri, resize)
      const processed = applyImageFilters(data.imageData, data.filters);
      self.postMessage({ result: processed }, [processed.buffer]);
      break;
  }
};

// main.js — thread principale
const worker = new Worker(new URL('./worker.js', import.meta.url));

function sortLargeDataset(data) {
  return new Promise((resolve) => {
    worker.onmessage = (e) => resolve(e.data.result);
    worker.postMessage({ operation: 'sort', data });
  });
}

// Con Comlink per un'API più ergonomica
import { wrap } from 'comlink';

const api = wrap(new Worker(new URL('./worker.js', import.meta.url)));
const result = await api.processData(largeDataset); // sembra una chiamata locale
```

### Debounce e Throttle

Debounce e throttle limitano la frequenza di esecuzione di funzioni associate a eventi ad alta frequenza (scroll, resize, input), prevenendo il sovraccarico del thread principale.

```javascript
// Debounce: esegue solo dopo che l'evento smette di verificarsi per N ms
// Caso d'uso: ricerca mentre si digita, resize, validazione input
function debounce(fn, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

const searchInput = document.getElementById('search');
searchInput.addEventListener('input', debounce(async (e) => {
  const results = await fetch(`/api/search?q=${e.target.value}`);
  renderResults(await results.json());
}, 300));

// Throttle: esegue al massimo una volta ogni N ms
// Caso d'uso: scroll handler, mousemove, analytics di tracciamento
function throttle(fn, interval) {
  let lastTime = 0;
  return function(...args) {
    const now = Date.now();
    if (now - lastTime >= interval) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}

window.addEventListener('scroll', throttle(() => {
  updateProgressBar();
  checkInfiniteScroll();
}, 100));
```

### Prevenzione dei Memory Leak

I memory leak degradano progressivamente la performance, causando rallentamenti crescenti e potenziali crash nelle sessioni prolungate.

```javascript
// Leak comune: event listener non rimossi
class Component {
  constructor() {
    this.handleScroll = this.handleScroll.bind(this);
    window.addEventListener('scroll', this.handleScroll);
  }

  handleScroll() { /* ... */ }

  // FONDAMENTALE: rimuovere il listener quando il componente viene distrutto
  destroy() {
    window.removeEventListener('scroll', this.handleScroll);
  }
}

// Leak comune: riferimenti in closure
function createHeavyProcessor() {
  const hugeArray = new Array(1_000_000).fill('data'); // 8MB+

  return {
    // Il metodo mantiene un riferimento a hugeArray anche se non lo usa
    process() {
      console.log('Processing...');
    }
  };
  // Soluzione: non catturare variabili non necessarie nella closure
}

// Leak comune: timer e intervalli dimenticati
const intervalId = setInterval(fetchUpdates, 5000);
// Se il componente viene smontato senza clearInterval, il timer continua

// Leak comune: observer non disconnessi
const observer = new MutationObserver(callback);
observer.observe(element, { childList: true });
// observer.disconnect() quando non più necessario

// Utilizzare WeakRef e FinalizationRegistry per riferimenti non-bloccanti
const cache = new Map();
function getCached(key, factory) {
  const ref = cache.get(key);
  if (ref) {
    const value = ref.deref();
    if (value !== undefined) return value;
  }
  const value = factory();
  cache.set(key, new WeakRef(value));
  return value;
}
```

---

## Server-Side Performance

La performance lato server definisce il limite inferiore della velocità percepita dall'utente: nessuna ottimizzazione frontend può compensare un server lento. La scelta dell'architettura di rendering, i protocolli di rete e le strategie di caching determinano il TTFB e il tempo totale di caricamento.

### SSR vs SSG vs ISR

| Strategia | Generazione | TTFB | Freschezza dati | Caso d'uso |
|-----------|-------------|------|-----------------|------------|
| **SSG** (Static Site Generation) | Al build | Minimo (file statico da CDN) | Dati aggiornati solo al rebuild | Blog, documentazione, landing page |
| **SSR** (Server-Side Rendering) | Ad ogni richiesta | Variabile (dipende dal server) | Sempre aggiornati | Dashboard, contenuti personalizzati |
| **ISR** (Incremental Static Regeneration) | Al build + rigenerazione in background | Minimo (cache) | Configurabile (revalidate: N secondi) | E-commerce, CMS, contenuti semi-dinamici |

```javascript
// Next.js — SSG con getStaticProps
export async function getStaticProps() {
  const products = await fetchProducts();
  return {
    props: { products },
    revalidate: 3600 // ISR: rigenera ogni ora
  };
}

// Next.js App Router — caching granulare
// app/products/page.tsx
async function ProductsPage() {
  // Cache per 1 ora, rigenera in background
  const products = await fetch('https://api.example.com/products', {
    next: { revalidate: 3600 }
  });

  // Dati sempre freschi (no cache)
  const inventory = await fetch('https://api.example.com/inventory', {
    cache: 'no-store'
  });

  return <ProductList products={products} inventory={inventory} />;
}
```

### Streaming SSR

Lo streaming SSR invia l'HTML al browser incrementalmente, permettendo al browser di iniziare il rendering prima che il server abbia completato la generazione dell'intera pagina. Questo riduce significativamente TTFB e FCP.

```jsx
// React 18 Streaming SSR con Suspense
import { Suspense } from 'react';

function ProductPage({ productId }) {
  return (
    <div>
      {/* Il header viene inviato immediatamente */}
      <Header />

      {/* Il prodotto viene streamato quando i dati sono pronti */}
      <Suspense fallback={<ProductSkeleton />}>
        <ProductDetails id={productId} />
      </Suspense>

      {/* Le recensioni vengono stremate in un secondo momento */}
      <Suspense fallback={<ReviewsSkeleton />}>
        <Reviews productId={productId} />
      </Suspense>

      {/* Il footer viene inviato subito (non ha dipendenze async) */}
      <Footer />
    </div>
  );
}

// Il server invia: Header → ProductSkeleton → ReviewsSkeleton → Footer
// Poi sostituisce gli skeleton con i dati reali man mano che arrivano
```

### Edge Computing

L'edge computing esegue la logica applicativa nei server CDN più vicini all'utente, riducendo la latenza di rete da centinaia a poche decine di millisecondi.

```javascript
// Vercel Edge Functions
export const config = { runtime: 'edge' };

export default async function handler(request) {
  const country = request.geo?.country || 'US';
  const data = await fetch(`https://api.example.com/products?region=${country}`);

  return new Response(JSON.stringify(await data.json()), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 's-maxage=300, stale-while-revalidate=600'
    }
  });
}

// Cloudflare Workers
export default {
  async fetch(request, env) {
    const cache = caches.default;
    let response = await cache.match(request);

    if (!response) {
      response = await fetch(request);
      response = new Response(response.body, response);
      response.headers.set('Cache-Control', 's-maxage=3600');
      await cache.put(request, response.clone());
    }

    return response;
  }
};
```

### HTTP/2 e HTTP/3

| Caratteristica | HTTP/1.1 | HTTP/2 | HTTP/3 |
|----------------|----------|--------|--------|
| Multiplexing | No (6 connessioni parallele per dominio) | Sì (stream multipli su una connessione) | Sì (stream indipendenti) |
| Compressione header | No | HPACK | QPACK |
| Server Push | No | Sì | Deprecato |
| Protocollo trasporto | TCP | TCP | QUIC (UDP) |
| Head-of-line blocking | Sì (per connessione) | Sì (a livello TCP) | No (ogni stream è indipendente) |
| Connessione 0-RTT | No | No | Sì |

HTTP/2 elimina la necessità di tecniche come domain sharding e sprite CSS. HTTP/3 (basato su QUIC) elimina il head-of-line blocking a livello di trasporto e supporta la migrazione di connessione (utile quando il dispositivo cambia rete). La maggior parte dei CDN moderni supporta HTTP/3 automaticamente.

### Compressione: gzip e Brotli

```nginx
# Nginx — configurazione Brotli (prioritario) e gzip (fallback)
# Brotli offre 15-25% di compressione in più rispetto a gzip

# Brotli
brotli on;
brotli_comp_level 6;        # 1-11, 6 è un buon compromesso velocità/compressione
brotli_types text/plain text/css text/javascript application/javascript
             application/json image/svg+xml application/xml;

# gzip come fallback
gzip on;
gzip_comp_level 6;          # 1-9
gzip_types text/plain text/css text/javascript application/javascript
           application/json image/svg+xml application/xml;

# Compressione statica: pre-comprimere i file al build time
gzip_static on;              # serve file .gz pre-compressi
brotli_static on;            # serve file .br pre-compressi
```

```javascript
// Compressione al build time con vite
// vite.config.js
import viteCompression from 'vite-plugin-compression';

export default {
  plugins: [
    viteCompression({ algorithm: 'brotliCompress' }),
    viteCompression({ algorithm: 'gzip' })
  ]
};
```

### Strategie di Caching

Il caching è la singola ottimizzazione con il maggiore impatto sulla performance per gli utenti di ritorno. Una strategia di caching efficace combina header HTTP, CDN e cache applicativa.

```
# Cache-Control — header fondamentale

# Asset statici immutabili (contenuto con hash nel filename)
# main.a1b2c3d4.js, styles.e5f6g7h8.css
Cache-Control: public, max-age=31536000, immutable

# HTML e dati API che cambiano frequentemente
Cache-Control: public, max-age=0, must-revalidate

# Dati privati dell'utente (no CDN cache)
Cache-Control: private, max-age=300

# Strategia stale-while-revalidate
# Servi dalla cache immediatamente, aggiorna in background
Cache-Control: public, max-age=300, stale-while-revalidate=86400

# No cache — forza sempre la rivalidazione col server
Cache-Control: no-cache
# (Nota: no-cache NON significa "non cachare", significa "rivalidare sempre")
# Per disabilitare completamente il caching: no-store
```

```
# ETag — rivalidazione basata sul contenuto
# Il server invia un hash del contenuto
ETag: "a1b2c3d4"

# Il browser nella richiesta successiva invia:
If-None-Match: "a1b2c3d4"

# Se il contenuto non è cambiato, il server risponde 304 Not Modified
# (nessun body, risparmio di banda)
```

La strategia ottimale: asset con hash nel filename (`main.abc123.js`) con cache immutabile di un anno; pagine HTML con `no-cache` o breve `max-age` con `stale-while-revalidate`; API con `Cache-Control` specifico per endpoint; CDN come layer di cache tra browser e server di origine.

---

## Strumenti di Misurazione

Misurare la performance è il prerequisito per migliorarla. Gli strumenti si dividono in due categorie: dati di laboratorio (sintetici, riproducibili) e dati di campo (utenti reali, condizioni variabili). Una strategia completa utilizza entrambi.

### Lighthouse

Lighthouse è lo strumento di auditing integrato in Chrome DevTools. Esegue una simulazione di caricamento della pagina e produce un punteggio di performance (0-100) con raccomandazioni specifiche.

```bash
# Lighthouse da CLI per integrazione in CI/CD
npm install -g lighthouse

# Audit completo con report HTML
lighthouse https://example.com --output html --output-path ./report.html

# Solo metriche di performance, formato JSON
lighthouse https://example.com \
  --only-categories=performance \
  --output json \
  --chrome-flags="--headless --no-sandbox"

# Programmatico con Node.js
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
const result = await lighthouse('https://example.com', {
  port: chrome.port,
  onlyCategories: ['performance']
});

console.log('Score:', result.lhr.categories.performance.score * 100);
console.log('LCP:', result.lhr.audits['largest-contentful-paint'].numericValue);
console.log('TBT:', result.lhr.audits['total-blocking-time'].numericValue);
console.log('CLS:', result.lhr.audits['cumulative-layout-shift'].numericValue);

await chrome.kill();
```

Lighthouse utilizza throttling simulato per rappresentare una connessione mobile media. I risultati sono utili per confronti relativi (prima/dopo) ma non rappresentano le condizioni di tutti gli utenti.

### PageSpeed Insights

PageSpeed Insights combina dati di laboratorio (Lighthouse) con dati di campo (CrUX) in un'unica interfaccia web. I dati di campo mostrano l'esperienza degli utenti reali negli ultimi 28 giorni, con distribuzione per percentili.

L'API di PageSpeed Insights può essere integrata in pipeline di CI/CD per monitoraggio automatizzato.

```bash
# API PageSpeed Insights
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?\
url=https://example.com&\
category=performance&\
strategy=mobile&\
key=YOUR_API_KEY"
```

### WebPageTest

WebPageTest offre test di performance da posizioni geografiche reali con browser reali, supportando configurazioni avanzate: multi-step test, throttling di rete personalizzato, scripted interaction, filmstrip comparison e analisi waterfall dettagliata.

Le funzionalità distintive includono: confronto side-by-side di due URL, test con browser multipli, analisi delle richieste con priorità e timing dettagliati, e la celebre metrica "Speed Index" che misura la velocità di riempimento visivo del viewport.

### Chrome DevTools Performance Tab

Il pannello Performance di Chrome DevTools fornisce la vista più dettagliata di ciò che accade durante il caricamento e l'interazione. Permette di registrare profili di performance e analizzarli frame per frame.

Funzionalità principali:

- **Flame Chart**: visualizza lo stack di esecuzione JavaScript nel tempo, evidenziando i long task (>50ms) in rosso.
- **Main thread activity**: mostra parsing, compilazione, esecuzione JS, calcolo stili, layout, paint e compositing.
- **Network waterfall**: timeline di tutte le richieste di rete con dimensioni e tempi.
- **Frames**: indica i frame persi (sotto 60fps) e il motivo.
- **Web Vitals lane**: mostra gli eventi LCP, CLS e INP direttamente nella timeline.

Per un'analisi efficace: registrare con CPU throttling 4x per simulare dispositivi più lenti; identificare i long task nel flame chart; cercare i "forced reflow" nel sommario delle attività; verificare che le animazioni utilizzino solo proprietà composite.

### Libreria web-vitals

La libreria `web-vitals` (sviluppata da Google) permette di raccogliere le metriche Core Web Vitals da utenti reali e inviarle a un sistema di analytics.

```javascript
import { onCLS, onINP, onLCP, onFCP, onTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,  // "good", "needs-improvement", "poor"
    delta: metric.delta,
    id: metric.id,
    navigationType: metric.navigationType,
    // Informazioni aggiuntive per il debug
    url: window.location.href,
    userAgent: navigator.userAgent,
    effectiveType: navigator.connection?.effectiveType
  });

  // navigator.sendBeacon non blocca la navigazione
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/analytics/vitals', body);
  } else {
    fetch('/api/analytics/vitals', { body, method: 'POST', keepalive: true });
  }
}

// Registrare tutte le metriche
onCLS(sendToAnalytics);
onINP(sendToAnalytics);
onLCP(sendToAnalytics);
onFCP(sendToAnalytics);
onTTFB(sendToAnalytics);

// Con attribution per debug avanzato
import { onLCP } from 'web-vitals/attribution';

onLCP((metric) => {
  console.log('Elemento LCP:', metric.attribution.element);
  console.log('URL risorsa:', metric.attribution.url);
  console.log('TTFB:', metric.attribution.timeToFirstByte);
  console.log('Ritardo caricamento risorsa:', metric.attribution.resourceLoadDelay);
  console.log('Tempo caricamento risorsa:', metric.attribution.resourceLoadDuration);
});
```

### CrUX (Chrome User Experience Report)

CrUX è il dataset pubblico di Google che raccoglie metriche di performance reali dagli utenti Chrome che hanno accettato la condivisione delle statistiche. È la fonte dati utilizzata per il ranking di Google e disponibile attraverso diverse interfacce.

```javascript
// CrUX API — dati a livello di origine o URL
const response = await fetch(
  'https://chromeuxreport.googleapis.com/v1/records:queryRecord?' +
  'key=YOUR_API_KEY',
  {
    method: 'POST',
    body: JSON.stringify({
      origin: 'https://example.com',
      // oppure: url: 'https://example.com/products'
      metrics: [
        'largest_contentful_paint',
        'interaction_to_next_paint',
        'cumulative_layout_shift',
        'experimental_time_to_first_byte'
      ]
    })
  }
);

const data = await response.json();
// data.record.metrics.largest_contentful_paint.percentiles.p75
// data.record.metrics.largest_contentful_paint.histogram
```

CrUX fornisce dati aggregati su 28 giorni: non mostra metriche per singole sessioni, ma distribuzioni percentili. Il valore al 75° percentile è quello utilizzato da Google per la valutazione dei Core Web Vitals.

---

## Performance Budget

Un performance budget è un insieme di limiti quantitativi sulle metriche di performance che una pagina non deve superare. Senza un budget, la performance degrada gradualmente con ogni nuova funzionalità, dipendenza e contenuto aggiunto — fenomeno noto come "performance regression".

### Definire un Budget

Il budget deve essere basato su dati concreti: le metriche attuali, i benchmark dei competitor e le aspettative degli utenti. Deve coprire diverse dimensioni.

```json
// budget.json — esempio di configurazione per Lighthouse CI
[
  {
    "path": "/*",
    "timings": [
      { "metric": "first-contentful-paint", "budget": 1800 },
      { "metric": "largest-contentful-paint", "budget": 2500 },
      { "metric": "interactive", "budget": 3800 },
      { "metric": "total-blocking-time", "budget": 200 },
      { "metric": "cumulative-layout-shift", "budget": 0.1 }
    ],
    "resourceSizes": [
      { "resourceType": "script", "budget": 300 },
      { "resourceType": "stylesheet", "budget": 100 },
      { "resourceType": "image", "budget": 500 },
      { "resourceType": "font", "budget": 100 },
      { "resourceType": "total", "budget": 1000 }
    ],
    "resourceCounts": [
      { "resourceType": "script", "budget": 15 },
      { "resourceType": "third-party", "budget": 10 },
      { "resourceType": "total", "budget": 50 }
    ]
  }
]
```

### Monitoraggio Automatizzato

```javascript
// Lighthouse CI — integrazione in GitHub Actions
// .github/workflows/lighthouse.yml
/*
name: Lighthouse CI
on: [push]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci && npm run build
      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v12
        with:
          urls: |
            http://localhost:3000/
            http://localhost:3000/products
          budgetPath: ./budget.json
          uploadArtifacts: true
*/
```

### Strumento bundlesize

`bundlesize` verifica che le dimensioni dei file di build non superino i limiti definiti, bloccando la PR in caso di violazione.

```json
// package.json
{
  "bundlesize": [
    {
      "path": "./dist/js/main.*.js",
      "maxSize": "150 kB",
      "compression": "gzip"
    },
    {
      "path": "./dist/js/vendor.*.js",
      "maxSize": "250 kB",
      "compression": "gzip"
    },
    {
      "path": "./dist/css/main.*.css",
      "maxSize": "50 kB",
      "compression": "gzip"
    }
  ],
  "scripts": {
    "check-size": "bundlesize"
  }
}
```

```bash
# Esecuzione manuale
npx bundlesize

# In CI/CD (es. GitHub Actions)
# bundlesize si integra con GitHub Status Checks
# per approvare o bloccare le pull request
```

Il concetto chiave del performance budget è la sua natura di vincolo preventivo: è molto più facile mantenere la performance che recuperarla dopo un degrado progressivo. Un budget ben configurato e monitorato in CI/CD impedisce regressioni prima che raggiungano la produzione.

---

## Ottimizzazione INP: Approfondimento

Come introdotto nella sezione sulle metriche, INP (Interaction to Next Paint) misura la reattivita complessiva osservando tutte le interazioni durante la visita. Dopo la sostituzione di FID nel marzo 2024, INP e diventata la metrica piu critica per la reattivita, e i dati del Web Almanac 2025 mostrano che meno del 25% dei siti mantiene la durata dei task sotto la soglia raccomandata di 50ms. Questa sezione approfondisce le strategie avanzate per ottimizzare INP.

### Anatomia di un'Interazione INP

La latenza di ogni interazione INP si compone di tre fasi distinte, ciascuna con cause e strategie di ottimizzazione diverse:

**1. Input Delay** — il tempo tra il momento in cui l'utente interagisce (click, tap, pressione tasto) e il momento in cui il browser inizia a eseguire il primo event handler. L'input delay e causato principalmente da long task gia in esecuzione sul main thread: se un task JavaScript sta occupando il thread quando l'utente clicca, l'event handler deve attendere la fine di quel task. Un input delay elevato indica che il main thread e sovraccarico al momento dell'interazione.

**2. Processing Time** — il tempo di esecuzione degli event handler associati all'interazione. Questo include tutti i listener `click`, `pointerup`, `keydown` etc. registrati sull'elemento e i suoi antenati (event bubbling). Un processing time elevato indica event handler troppo complessi che eseguono troppo lavoro sincronamente.

**3. Presentation Delay** — il tempo tra la fine dell'ultimo event handler e il momento in cui il browser completa il rendering del frame successivo (il "next paint"). Questo include il calcolo degli stili, il layout, il paint e il compositing. Un presentation delay elevato indica un DOM troppo grande, aggiornamenti CSS costosi o un numero eccessivo di elementi da ridisegnare.

```javascript
// Analisi dettagliata delle tre fasi INP con PerformanceObserver
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    // Solo interazioni, non misure generiche
    if (entry.interactionId) {
      const inputDelay = entry.processingStart - entry.startTime;
      const processingTime = entry.processingEnd - entry.processingStart;
      const presentationDelay = (entry.startTime + entry.duration) - entry.processingEnd;

      console.log(`Interazione: ${entry.name}`);
      console.log(`  Input delay:        ${inputDelay.toFixed(1)}ms`);
      console.log(`  Processing time:    ${processingTime.toFixed(1)}ms`);
      console.log(`  Presentation delay: ${presentationDelay.toFixed(1)}ms`);
      console.log(`  Durata totale:      ${entry.duration}ms`);

      // Identificare la fase dominante
      if (inputDelay > 100) {
        console.warn('  → Main thread occupato al momento del click');
      }
      if (processingTime > 100) {
        console.warn('  → Event handler troppo pesante');
      }
      if (presentationDelay > 100) {
        console.warn('  → Rendering post-handler troppo costoso');
      }
    }
  }
});
observer.observe({ type: 'event', buffered: true, durationThreshold: 16 });
```

### Long Task e Yielding al Main Thread

Un long task e qualsiasi task JavaScript che occupa il main thread per piu di 50ms. Durante l'esecuzione di un long task, il browser non puo rispondere agli input dell'utente, causando un input delay elevato. La strategia principale per ridurre INP e suddividere i long task in task piu piccoli, cedendo periodicamente il controllo al main thread.

**`scheduler.yield()` — l'API moderna per il yielding**

`scheduler.yield()` e una nuova API del browser che permette di cedere esplicitamente il controllo al main thread durante l'esecuzione di codice lungo, consentendo al browser di processare interazioni utente pendenti prima di continuare. A differenza di `setTimeout(fn, 0)`, che mette il continuation task in coda con bassa priorita, `scheduler.yield()` mantiene la priorita del task corrente, garantendo che il lavoro riprenda immediatamente dopo aver processato eventuali input dell'utente.

```javascript
// Pattern: suddividere un long task con scheduler.yield()
async function processLargeDataset(items) {
  const results = [];

  for (let i = 0; i < items.length; i++) {
    // Elaborazione di ogni elemento
    results.push(transform(items[i]));

    // Ogni 100 elementi, cede il main thread
    // Il browser puo processare click, scroll e altri input
    if (i % 100 === 0 && i > 0) {
      // scheduler.yield() con fallback per browser piu vecchi
      if ('scheduler' in globalThis && 'yield' in scheduler) {
        await scheduler.yield();
      } else {
        await new Promise(resolve => setTimeout(resolve, 0));
      }
    }
  }
  return results;
}

// Pattern: yielding basato sul tempo trascorso
async function processWithTimeYielding(items, maxBlockTime = 50) {
  const results = [];
  let lastYield = performance.now();

  for (const item of items) {
    results.push(transform(item));

    // Yield se il task ha occupato il thread per piu di maxBlockTime ms
    if (performance.now() - lastYield > maxBlockTime) {
      if ('scheduler' in globalThis && 'yield' in scheduler) {
        await scheduler.yield();
      } else {
        await new Promise(resolve => setTimeout(resolve, 0));
      }
      lastYield = performance.now();
    }
  }
  return results;
}
```

**`scheduler.postTask()` — scheduling con priorita**

L'API `scheduler.postTask()` permette di schedulare task con livelli di priorita distinti, dando al browser informazioni esplicite su quale lavoro e urgente e quale puo attendere.

```javascript
// Tre livelli di priorita disponibili
// "user-blocking" — alta priorita, per risposte immediate all'utente
// "user-visible"  — priorita default, per aggiornamenti visibili
// "background"    — bassa priorita, per lavoro non urgente

// Esempio: aggiornamento UI ad alta priorita + analytics a bassa priorita
button.addEventListener('click', async () => {
  // Aggiornamento UI con priorita alta — viene eseguito subito
  await scheduler.postTask(() => {
    updateUIState();
    renderFeedback();
  }, { priority: 'user-blocking' });

  // Tracking analytics con priorita bassa — eseguito quando il browser e idle
  scheduler.postTask(() => {
    trackClickEvent('purchase-button', { timestamp: Date.now() });
  }, { priority: 'background' });
});

// AbortController per annullare task pendenti
const controller = new AbortController();

scheduler.postTask(expensiveComputation, {
  priority: 'background',
  signal: controller.signal
});

// Se l'utente naviga via, annullare il lavoro pendente
window.addEventListener('pagehide', () => controller.abort());
```

### Strategie Avanzate per Ridurre INP

**Riduzione del DOM size:** un DOM con piu di 1.400 elementi penalizza sia il processing time (piu nodi da attraversare per event bubbling) sia il presentation delay (piu elementi da ricalcolare nel layout). Implementare virtual scrolling per liste lunghe, rimuovere nodi non visibili dal DOM e utilizzare `content-visibility: auto` per differire il rendering di sezioni off-screen.

**Event delegation efficiente:** invece di registrare handler su centinaia di elementi figli, registrare un singolo handler sul contenitore e utilizzare `event.target` per determinare l'elemento cliccato. Questo riduce il numero di listener attivi e il consumo di memoria.

```javascript
// ERRATO: un listener per ogni elemento (1000 listener)
document.querySelectorAll('.list-item').forEach(item => {
  item.addEventListener('click', handleItemClick);
});

// CORRETTO: un singolo listener con event delegation
document.querySelector('.item-list').addEventListener('click', (e) => {
  const item = e.target.closest('.list-item');
  if (item) handleItemClick(item);
});
```

**`requestIdleCallback` per lavoro non urgente:** utilizzare `requestIdleCallback` per schedulare lavoro che non deve influenzare la reattivita dell'interfaccia, come pre-elaborazione di dati, aggiornamento di cache locali o logging.

```javascript
// Lavoro differito nei momenti di inattivita del browser
function processBackgroundQueue(queue) {
  requestIdleCallback((deadline) => {
    // Lavora finche c'e tempo libero (deadline.timeRemaining() > 0)
    while (queue.length > 0 && deadline.timeRemaining() > 5) {
      const task = queue.shift();
      task.execute();
    }
    // Se ci sono ancora task, schedula un altro callback
    if (queue.length > 0) {
      requestIdleCallback(() => processBackgroundQueue(queue));
    }
  }, { timeout: 2000 }); // timeout massimo: esegui entro 2s anche se il browser non e idle
}
```

---

## Ottimizzazione LCP: Approfondimento

Come introdotto nella sezione sulle metriche, LCP misura il tempo di rendering dell'elemento visibile piu grande nel viewport. Secondo il Web Almanac 2025, solo il 62% delle pagine mobile raggiunge un LCP "buono", rendendola la metrica Core Web Vital piu difficile da superare. L'ottimizzazione LCP richiede un approccio sistematico che affronta ogni fase del percorso di caricamento.

### Scomposizione del Tempo LCP

Il tempo LCP si compone di quattro sotto-metriche sequenziali, ciascuna un potenziale collo di bottiglia:

**1. Time to First Byte (TTFB)** — tempo dal click/navigazione al primo byte della risposta HTML. Target: < 800ms. Dipende dalla latenza di rete, dal tempo di elaborazione del server e dal protocollo di trasporto.

**2. Resource Load Delay** — tempo tra la ricezione dell'HTML e l'inizio del download della risorsa LCP (immagine, video, font). Questo ritardo e causato dal fatto che il browser deve prima parsare abbastanza HTML per scoprire la risorsa LCP. Se l'immagine LCP e referenziata da CSS (`background-image`) o caricata da JavaScript, il ritardo aumenta ulteriormente perche il browser deve prima scaricare, parsare ed eseguire quei file.

**3. Resource Load Duration** — tempo di download della risorsa LCP. Dipende dalla dimensione della risorsa, dalla velocita di connessione e dalla contesa con altre risorse in download contemporaneo.

**4. Element Render Delay** — tempo tra il completamento del download della risorsa e il rendering dell'elemento LCP. Causato da CSS render-blocking non ancora caricato, JavaScript che blocca il rendering o font web che ritardano la visualizzazione del testo.

### Resource Discovery: Eliminare il Load Delay

Il resource load delay e spesso la fase con maggiore potenziale di ottimizzazione. L'obiettivo e far si che il browser scopra la risorsa LCP il prima possibile.

```html
<!-- CASO OTTIMALE: l'immagine LCP e direttamente nell'HTML -->
<!-- Il browser la scopre durante il parsing dell'HTML, senza dover attendere CSS o JS -->
<img src="/images/hero.avif" alt="Hero" width="1200" height="600"
     fetchpriority="high" loading="eager" decoding="async">

<!-- CASO PROBLEMATICO: immagine LCP in CSS background -->
<!-- Il browser deve scaricare il CSS, parsarlo, e solo allora scopre l'immagine -->
<!-- Soluzione: preload esplicito nell'<head> -->
<link rel="preload" as="image" href="/images/hero-bg.avif"
      fetchpriority="high"
      imagesrcset="/images/hero-bg-400.avif 400w,
                   /images/hero-bg-800.avif 800w,
                   /images/hero-bg-1200.avif 1200w"
      imagesizes="100vw">

<!-- CASO PROBLEMATICO: immagine LCP caricata da JavaScript (framework SPA) -->
<!-- Il browser deve scaricare il JS, eseguirlo, e solo allora scopre l'immagine -->
<!-- Soluzione: SSR o preload esplicito -->
```

### `fetchpriority` per il Controllo delle Priorita

L'attributo `fetchpriority` consente di comunicare esplicitamente al browser l'importanza relativa di una risorsa, sovrascrivendo le euristiche predefinite del browser.

```html
<!-- fetchpriority="high" per l'immagine LCP —
     il browser la scarica con massima priorita -->
<img src="hero.avif" fetchpriority="high" loading="eager" alt="Hero"
     width="1200" height="600">

<!-- fetchpriority="low" per immagini below-the-fold visibili ma non critiche —
     il browser le scarica con priorita ridotta -->
<img src="decorative.webp" fetchpriority="low" loading="lazy" alt="Decorazione"
     width="200" height="200">

<!-- fetchpriority su preload per risorse critiche non visibili nell'HTML -->
<link rel="preload" as="image" href="/images/hero.avif" fetchpriority="high">

<!-- fetchpriority su fetch API per dati critici vs dati secondari -->
<script>
  // Dati necessari per il rendering above-the-fold: alta priorita
  fetch('/api/hero-content', { priority: 'high' });

  // Dati per sezioni below-the-fold: bassa priorita
  fetch('/api/recommendations', { priority: 'low' });
</script>
```

### Server Timing per Diagnostica LCP

L'header HTTP `Server-Timing` permette di comunicare metriche di timing dal server al browser, visibili nella Performance tab di DevTools e accessibili via JavaScript. Questo e fondamentale per diagnosticare se il collo di bottiglia LCP e nel TTFB.

```
# Header Server-Timing nella risposta HTTP
Server-Timing: db;dur=53.2;desc="Query prodotto",
               cache;desc="MISS",
               render;dur=12.8;desc="Template rendering",
               total;dur=78.4
```

```javascript
// Lettura di Server-Timing nel browser
const navigation = performance.getEntriesByType('navigation')[0];
navigation.serverTiming.forEach(({ name, duration, description }) => {
  console.log(`${name}: ${duration}ms (${description})`);
});
// db: 53.2ms (Query prodotto)
// cache: 0ms (MISS)
// render: 12.8ms (Template rendering)
```

### Ottimizzazione Pratica: Checklist LCP

1. Identificare l'elemento LCP con la Performance tab di DevTools o la libreria `web-vitals/attribution`.
2. Se l'elemento e un'immagine: applicare `fetchpriority="high"`, `loading="eager"`, preload nel `<head>`, servire in AVIF/WebP e verificare che non sia sovradimensionata rispetto alla viewport.
3. Se l'elemento e testo: assicurarsi che il font web sia precaricato con `<link rel="preload">` e che utilizzi `font-display: swap` o `optional`.
4. Eliminare il resource load delay: se la risorsa LCP e in CSS o JS, aggiungere un preload esplicito.
5. Ridurre il TTFB: implementare caching, CDN, edge computing e ottimizzare le query server.
6. Rimuovere risorse render-blocking tra l'HTML e l'elemento LCP: CSS inline critico, defer JavaScript.

---

## Ottimizzazione CLS: Approfondimento

Come introdotto nella sezione sulle metriche, CLS quantifica gli spostamenti inattesi del layout. Questa sezione approfondisce le cause meno ovvie di layout shift e le strategie avanzate per eliminarle.

### Cause Comuni e Meno Ovvie di Layout Shift

**Font web e FOUT (Flash of Unstyled Text):** quando un font web viene caricato e sostituisce il font di fallback, le differenze metriche (altezza x, spaziatura, kerning) tra i due font causano un ricalcolo del layout di tutti i paragrafi. Anche con `font-display: swap`, il cambio font genera CLS.

```css
/* Tecnica avanzata: @font-face size-adjust per minimizzare il FOUT shift */
/* Calcolare le metriche del font di sistema per avvicinarsi al font web */
@font-face {
  font-family: 'Brand Font';
  src: url('/fonts/brand.woff2') format('woff2');
  font-display: swap;
}

/* Override delle metriche del font di fallback */
@font-face {
  font-family: 'Brand Font Fallback';
  src: local('Arial');
  /* Queste proprieta regolano il fallback per avvicinarsi al font web */
  ascent-override: 90%;
  descent-override: 22%;
  line-gap-override: 0%;
  size-adjust: 107%;
}

body {
  font-family: 'Brand Font', 'Brand Font Fallback', sans-serif;
}
```

**Contenuto iniettato dinamicamente:** banner di cookie consent, toolbar di A/B testing, barre di notifica e annunci pubblicitari che vengono inseriti nel DOM dopo il caricamento iniziale causano shift se non e stato riservato spazio per loro.

```css
/* Riservare spazio per contenuti dinamici con min-height */
.cookie-banner-placeholder {
  min-height: 80px; /* altezza stimata del banner */
}

/* Usare overlay/position:fixed per contenuti che non devono spostare il layout */
.notification-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  /* Non causa CLS perche non influenza il layout degli altri elementi */
}

/* Utilizzare CSS contain per isolare sezioni che cambiano dimensione */
.ad-container {
  contain: layout size;
  width: 300px;
  height: 250px; /* dimensione fissa del formato pubblicitario */
}
```

**Lazy loading di immagini senza dimensioni:** se le immagini caricate con `loading="lazy"` non hanno attributi `width` e `height` (o `aspect-ratio` CSS), quando vengono caricate espandono il layout spostando il contenuto sottostante.

**Animazioni che causano layout shift:** animazioni CSS che modificano proprieta geometriche (`height`, `width`, `top`, `left`, `margin`, `padding`) causano layout shift. Le animazioni basate su `transform` e `opacity` non causano layout shift perche operano sul compositor senza modificare il layout.

```css
/* CAUSA CLS: animazione che modifica height */
.accordion-content {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease; /* lo spostamento del contenuto sotto genera CLS */
}
.accordion-content.open {
  max-height: 500px;
}

/* NON CAUSA CLS: animazione con transform */
.accordion-content {
  transform: scaleY(0);
  transform-origin: top;
  opacity: 0;
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.accordion-content.open {
  transform: scaleY(1);
  opacity: 1;
}
```

### bfcache e CLS

Il Back/Forward Cache (bfcache) e un meccanismo del browser che memorizza una snapshot completa della pagina quando l'utente naviga via, permettendo un ripristino istantaneo quando l'utente preme il tasto Indietro o Avanti. Una pagina ripristinata dal bfcache appare immediatamente nello stato esatto in cui e stata lasciata — senza alcun layout shift.

Garantire l'eligibilita al bfcache e una delle strategie piu efficaci per mantenere un CLS basso sulle navigazioni di ritorno. Le pagine sono eligibili al bfcache se rispettano queste condizioni:

```javascript
// Verificare l'eligibilita al bfcache
// 1. Non usare l'evento "unload" (impedisce bfcache)
// ERRATO:
window.addEventListener('unload', cleanup); // IMPEDISCE bfcache

// CORRETTO: usare "pagehide" al suo posto
window.addEventListener('pagehide', (event) => {
  if (event.persisted) {
    // La pagina sta entrando nel bfcache — non distruggerla
    console.log('Pagina salvata in bfcache');
  }
});

// 2. Chiudere le connessioni aperte quando la pagina viene nascosta
window.addEventListener('pagehide', () => {
  // Chiudere WebSocket, SSE, e connessioni persistenti
  websocket?.close();
  eventSource?.close();
});

// 3. Ripristinare lo stato quando si esce dal bfcache
window.addEventListener('pageshow', (event) => {
  if (event.persisted) {
    // La pagina e stata ripristinata dal bfcache
    // Ri-stabilire connessioni e aggiornare dati stale
    reconnectWebSocket();
    refreshStaleData();
  }
});

// Diagnostica: verificare perche una pagina non e entrata in bfcache
// Chrome DevTools → Application → Back/forward cache
// Mostra i motivi specifici del blocco
```

### Metriche CLS: Session Window

Il CLS non e semplicemente la somma di tutti i layout shift. Dal 2022, Chrome utilizza il metodo delle "session window": gli shift vengono raggruppati in finestre di massimo 5 secondi, con un gap massimo di 1 secondo tra uno shift e il successivo nella stessa finestra. Il valore CLS finale e il punteggio della session window con il valore piu alto. Questo approccio e piu equo per le pagine long-lived (SPA, infinite scroll) perche non penalizza accumulazioni di shift piccoli distribuiti in un lungo periodo.

---

## JavaScript Performance: Approfondimento

Oltre al code splitting e tree shaking introdotti nella sezione Loading Performance, esistono strategie avanzate per ridurre il costo del JavaScript sul main thread.

### Strategie Avanzate di Code Splitting

Il code splitting non si limita alla suddivisione per route. Le strategie piu efficaci combinano diversi livelli di granularita:

**Splitting per interazione:** caricare codice pesante solo quando l'utente interagisce con un elemento specifico, non quando la pagina si carica.

```javascript
// Esempio: editor Markdown caricato solo al focus sul campo
const editArea = document.querySelector('.edit-area');

editArea.addEventListener('focus', async () => {
  const { initMarkdownEditor } = await import('./markdown-editor');
  initMarkdownEditor(editArea);
}, { once: true }); // il listener si rimuove dopo il primo uso

// Esempio: mappa interattiva caricata solo quando la sezione diventa visibile
const mapSection = document.querySelector('#map-section');
const mapObserver = new IntersectionObserver(async (entries) => {
  if (entries[0].isIntersecting) {
    const { initMap } = await import('./map-component');
    initMap(mapSection);
    mapObserver.disconnect();
  }
});
mapObserver.observe(mapSection);
```

**`manualChunks` per vendor splitting ottimale:**

```javascript
// vite.config.js — separazione strategica dei chunk vendor
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // React e ReactDOM in un chunk dedicato (cambia raramente)
          if (id.includes('react-dom') || id.includes('react/')) {
            return 'react-vendor';
          }
          // Librerie di visualizzazione dati in chunk separato
          if (id.includes('chart.js') || id.includes('d3')) {
            return 'charts-vendor';
          }
          // Utility generiche
          if (id.includes('date-fns') || id.includes('lodash-es')) {
            return 'utils-vendor';
          }
          // Tutte le altre dipendenze node_modules
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        }
      }
    }
  }
});
```

### Tree Shaking Avanzato e Dead Code Elimination

Il tree shaking funziona solo con moduli ES (`import`/`export`) perche la loro struttura e determinabile staticamente. Come introdotto nella sezione Loading Performance, il campo `"sideEffects"` nel `package.json` e fondamentale per un tree shaking efficace. Questa sezione approfondisce le tecniche avanzate.

**Annotazione `/*#__PURE__*/` per funzioni con side effect apparente:**

```javascript
// Senza annotazione, il bundler non puo sapere se la chiamata ha side effect
// e la mantiene nel bundle anche se il risultato non viene usato
const unused = createComponent('sidebar');

// Con annotazione, il bundler puo rimuovere la chiamata se il risultato non e usato
const unused = /*#__PURE__*/ createComponent('sidebar');

// Esempio pratico con styled-components o librerie CSS-in-JS
export const StyledButton = /*#__PURE__*/ styled.button`
  background: blue;
  color: white;
`;
// Se StyledButton non viene importato, l'intero blocco viene eliminato
```

**Granularita delle importazioni per librerie pesanti:**

```javascript
// PROBLEMATICO: importa l'intera libreria di icone (>500KB)
import { IconHome, IconUser } from '@heroicons/react/solid';
// Anche con tree shaking, alcune librerie non sono ottimizzate

// OTTIMALE: importazione diretta del file specifico
import IconHome from '@heroicons/react/solid/HomeIcon';
import IconUser from '@heroicons/react/solid/UserIcon';

// VERIFICA: controllare se una libreria e tree-shakeable
// 1. Ha "module" o "exports" nel package.json?
// 2. Usa import/export ES (non require/module.exports)?
// 3. Ha "sideEffects": false nel package.json?
// Se la risposta e "no" a qualcuna: importare il percorso specifico
```

**Dead code elimination condizionale con variabili d'ambiente:**

```javascript
// Il bundler elimina l'intero blocco if in produzione
if (process.env.NODE_ENV === 'development') {
  // Codice di debug, logging verbose, strumenti di sviluppo
  // Rimosso completamente dal bundle di produzione
  enableDevTools();
  initPerformanceMonitor();
}

// Vite usa import.meta.env
if (import.meta.env.DEV) {
  console.log('Debug info:', state);
}
```

---

## Rendering Performance: Approfondimento

Come introdotto nella sezione sul rendering, le animazioni composite-only sono la strategia fondamentale per la fluidita visiva. Questa sezione approfondisce il funzionamento interno del compositor, la gestione dei layer GPU e le strategie di paint containment.

### Compositor Layers e Pipeline GPU

Il browser moderno utilizza una pipeline di rendering multi-thread. Il thread principale gestisce JavaScript, calcolo stili, layout e paint (generazione delle istruzioni di disegno). Il thread del compositor prende queste istruzioni e coordina la rasterizzazione su thread worker dedicati e sulla GPU. Ogni compositor layer e un'unita indipendente che puo essere trasformata, scalata o resa trasparente senza ricalcolare il layout o ridisegnare gli altri layer.

Un elemento viene promosso a un proprio compositor layer quando:

- Ha una proprieta `transform` 3D (`translate3d`, `rotate3d`, `perspective`)
- Ha `will-change: transform`, `will-change: opacity` o altre proprieta composite
- Ha `opacity` < 1 con una transizione/animazione attiva
- Ha un `<video>`, `<canvas>` o un contenuto WebGL
- Utilizza `position: fixed` o `position: sticky`
- E un overlay sopra un layer gia promosso (implicit compositing)

```javascript
// Diagnostica: controllare i layer nel browser
// Chrome DevTools → More tools → Layers
// Mostra tutti i compositor layer, la loro dimensione in memoria e il motivo
// della promozione

// Monitorare la memoria GPU consumata dai layer
// Performance tab → Abilitare "Advanced paint instrumentation"
// Cercare "Composite Layers" nel flame chart
```

**Costo della promozione a layer:** ogni layer consuma memoria GPU proporzionale alla sua dimensione in pixel. Un elemento 1920x1080 a 4 byte per pixel consuma circa 8MB di memoria GPU. Su dispositivi mobili con GPU memory limitata (256-512MB), promuovere troppi elementi degrada la performance invece di migliorarla. La regola: promuovere solo gli elementi che vengono effettivamente animati, e solo per la durata dell'animazione.

### Paint Containment

La proprieta CSS `contain: paint` comunica al browser che il contenuto di un elemento non sara mai disegnato fuori dai suoi bordi. Questo consente al browser di saltare il painting dell'elemento quando e fuori dal viewport e di non ricalcolare il paint degli elementi circostanti quando il contenuto interno cambia.

```css
/* Combinare contain con content-visibility per massimo beneficio */
.section-below-fold {
  /* contain: paint evita che il paint si propaghi fuori dai bordi */
  contain: layout paint;

  /* content-visibility: auto salta completamente rendering delle sezioni off-screen */
  content-visibility: auto;

  /* contain-intrinsic-size fornisce una dimensione stimata per lo scrollbar */
  /* "auto" ricorda la dimensione reale dopo il primo rendering */
  contain-intrinsic-size: auto 600px;
}

/* Isolare i sotto-alberi costosi con contain: strict */
.complex-widget {
  contain: strict; /* equivale a: size layout paint style */
  width: 400px;
  height: 300px;
  /* Il browser sa che questo widget non influenza il resto della pagina */
  /* Qualsiasi cambiamento interno non innesca reflow/repaint esterni */
}
```

### `will-change` Avanzato: Quando e Come Usarlo

Come introdotto nella sezione sul rendering, `will-change` promuove un elemento su un layer dedicato. L'uso avanzato prevede l'applicazione e la rimozione dinamica per evitare il consumo permanente di memoria GPU.

```javascript
// Pattern: applicare will-change prima dell'animazione, rimuovere dopo
const animatedElement = document.querySelector('.card');

animatedElement.addEventListener('mouseenter', () => {
  // Prepara il layer PRIMA che l'animazione inizi
  animatedElement.style.willChange = 'transform, opacity';
});

animatedElement.addEventListener('transitionend', () => {
  // Rilascia il layer DOPO che l'animazione termina
  animatedElement.style.willChange = 'auto';
});

// Pattern: will-change per scroll-linked animations
// Applicare solo sugli elementi che stanno per entrare nel viewport
const scrollObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.willChange = 'transform, opacity';
    } else {
      entry.target.style.willChange = 'auto';
    }
  });
}, { rootMargin: '200px' }); // prepara 200px prima che l'elemento sia visibile
```

---

## Network Optimization: Approfondimento

Come introdotto nella sezione Server-Side Performance, HTTP/2 e HTTP/3 offrono multiplexing e compressione header. Questa sezione approfondisce le strategie di rete avanzate per ridurre la latenza e accelerare la delivery delle risorse.

### HTTP/3 e QUIC: Vantaggi Pratici

HTTP/3 sostituisce TCP con il protocollo QUIC (basato su UDP), eliminando diversi colli di bottiglia fondamentali:

**Eliminazione dell'head-of-line blocking a livello di trasporto:** in HTTP/2, tutti gli stream condividono una singola connessione TCP. Se un pacchetto TCP viene perso, tutti gli stream si fermano fino alla ritrasmissione — anche quelli i cui dati sono gia arrivati. In HTTP/3, ogni stream QUIC e indipendente: la perdita di un pacchetto blocca solo lo stream interessato.

**Connessione 0-RTT:** QUIC supporta la ripresa di connessione con zero round-trip aggiuntivi per connessioni ripetute allo stesso server. Al primo collegamento, il handshake TLS e incluso nel protocollo QUIC (1-RTT vs 2-RTT di TCP+TLS). Nelle connessioni successive, QUIC puo inviare dati immediatamente (0-RTT), riducendo la latenza di connessione da 100-300ms a quasi zero.

**Migrazione di connessione:** quando un dispositivo mobile cambia rete (da Wi-Fi a 4G o viceversa), le connessioni TCP si interrompono perche cambiano gli indirizzi IP. QUIC identifica le connessioni tramite un Connection ID indipendente dall'IP, permettendo la continuita senza interruzione — particolarmente importante per le applicazioni mobile.

```
# Verifica supporto HTTP/3 del server
# Header Alt-Svc nella risposta HTTP/2 indica la disponibilita di HTTP/3
Alt-Svc: h3=":443"; ma=86400

# Nginx — abilitare HTTP/3 (richiede build con QUIC)
# nginx.conf
server {
    listen 443 quic reuseport;
    listen 443 ssl;
    http2 on;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Informare il browser della disponibilita di HTTP/3
    add_header Alt-Svc 'h3=":443"; ma=86400';

    # Header QUIC transport parameters
    quic_retry on;
}
```

### Early Hints (103): Anticipare il Download delle Risorse

Lo status code HTTP 103 Early Hints e un meccanismo per inviare una risposta preliminare al browser mentre il server sta ancora generando la risposta principale (200). Questo permette al browser di iniziare a scaricare risorse critiche durante il "think time" del server — il tempo che il server impiega per query al database, rendering di template e altre operazioni.

```
# Flusso temporale senza Early Hints:
# t=0ms   Browser → Server: GET /products
# t=0ms   Server inizia elaborazione (query DB, rendering)
# t=300ms Server → Browser: 200 OK + HTML
# t=300ms Browser inizia a parsare HTML e scopre le risorse
# t=350ms Browser inizia download di CSS, JS, font

# Flusso con Early Hints:
# t=0ms   Browser → Server: GET /products
# t=1ms   Server → Browser: 103 Early Hints (preload CSS, font, immagine LCP)
# t=1ms   Browser inizia download di CSS, font, immagine LCP
# t=300ms Server → Browser: 200 OK + HTML
# t=300ms Browser ha gia scaricato le risorse critiche!
```

```
# Implementazione con Nginx
location /products {
    # Invia 103 Early Hints con le risorse critiche
    add_header Link "</css/main.css>; rel=preload; as=style" early;
    add_header Link "</fonts/brand.woff2>; rel=preload; as=font; crossorigin" early;
    add_header Link "</images/hero.avif>; rel=preload; as=image" early;
    add_header Link "<https://cdn.example.com>; rel=preconnect; crossorigin" early;

    proxy_pass http://backend;
}
```

```javascript
// Implementazione con Node.js (Express/Fastify)
// Node.js >= 18.11 supporta 103 Early Hints nativamente

import express from 'express';
const app = express();

app.get('/products', (req, res) => {
  // Invia 103 Early Hints immediatamente
  res.writeEarlyHints({
    link: [
      '</css/main.css>; rel=preload; as=style',
      '</fonts/brand.woff2>; rel=preload; as=font; crossorigin',
      '</images/hero.avif>; rel=preload; as=image',
    ]
  });

  // Il server continua a elaborare la richiesta
  // mentre il browser scarica le risorse indicate
  const products = await fetchProductsFromDB();
  res.render('products', { products });
});
```

Early Hints e supportato da Chrome, Safari, Firefox e Opera. I CDN piu diffusi (Cloudflare, Akamai, Fastly) supportano 103 Early Hints automaticamente, intercettando le risorse dal primo caricamento e inviandole come hints nelle richieste successive.

### Server Push Deprecato e Alternative

HTTP/2 Server Push permetteva al server di inviare risorse al browser senza che il browser le richiedesse. E stato deprecato in Chrome 106 e rimosso progressivamente per diversi motivi: complessita di implementazione, rischio di inviare risorse gia in cache del browser (spreco di banda), e interazioni problematiche con i CDN. Le alternative moderne sono:

1. **103 Early Hints** — il sostituto diretto, descritto sopra
2. **`<link rel="preload">`** — il browser scarica la risorsa appena incontra il tag nel HTML
3. **Speculation Rules API** — per pre-scaricare o pre-renderizzare intere pagine (descritto nella sezione successiva)

---

## Resource Hints Avanzati e Speculation Rules API

Come introdotto nella sezione Loading Performance, i resource hints (`preconnect`, `preload`, `prefetch`) permettono di anticipare operazioni di rete. Questa sezione approfondisce le strategie avanzate e introduce la Speculation Rules API come evoluzione dei resource hints tradizionali.

### Gerarchia dei Resource Hints

I resource hints hanno costi e benefici diversi, e devono essere usati con criterio per evitare contesa con risorse critiche:

| Hint | Azione | Costo | Quando usare |
|------|--------|-------|-------------|
| `dns-prefetch` | Risolve solo il DNS | Minimo (~1KB) | Domini di terze parti non critici |
| `preconnect` | DNS + TCP + TLS | Basso (~5KB) | Max 2-3 domini critici |
| `preload` | Scarica la risorsa completa | Alto (dimensione risorsa) | Risorse scoperte tardi (font in CSS, immagini in background) |
| `prefetch` | Scarica per navigazione futura | Medio | Risorse della prossima probabile pagina |
| `modulepreload` | Preload + parse + compile modulo ES | Alto | Moduli JS critici del percorso di import |

Regole pratiche: non usare piu di 2-3 `preconnect` (ogni connessione consuma CPU e memoria); non precaricare risorse che non verranno usate entro pochi secondi; utilizzare `prefetch` con cautela su connessioni mobili (consuma dati dell'utente).

### Speculation Rules API

La Speculation Rules API e un sistema moderno per istruire il browser a pre-scaricare (prefetch) o pre-renderizzare (prerender) pagine intere prima che l'utente navighi effettivamente verso di esse. A differenza dei resource hints tradizionali che operano su singole risorse, la Speculation Rules API opera su navigazioni complete.

Quando una pagina viene pre-renderizzata, il browser la carica completamente in background — scarica le risorse, esegue il JavaScript, costruisce il DOM, applica il CSS — e la tiene pronta in un tab nascosto. Quando l'utente clicca il link, la pagina pre-renderizzata viene visualizzata istantaneamente, con un LCP effettivo di quasi zero.

```html
<!-- Speculation Rules inline nel documento HTML -->
<script type="speculationrules">
{
  "prerender": [
    {
      "source": "list",
      "urls": ["/products", "/about", "/contact"]
    }
  ],
  "prefetch": [
    {
      "source": "list",
      "urls": ["/blog", "/faq"]
    }
  ]
}
</script>

<!-- Speculation Rules con document rules — piu flessibili -->
<script type="speculationrules">
{
  "prerender": [
    {
      "source": "document",
      "where": {
        "and": [
          { "href_matches": "/*" },
          { "not": { "href_matches": "/logout" } },
          { "not": { "href_matches": "/admin/*" } },
          { "not": { "selector_matches": ".no-prerender" } }
        ]
      },
      "eagerness": "moderate"
    }
  ]
}
</script>
```

**Livelli di eagerness:**

| Livello | Comportamento | Caso d'uso |
|---------|--------------|------------|
| `immediate` | Pre-renderizza appena la regola viene scoperta | Link nella navigazione principale |
| `eager` | Pre-renderizza rapidamente, con minimo ritardo | Link prominenti above-the-fold |
| `moderate` | Pre-renderizza al hover del mouse (200ms) | Link standard nel contenuto |
| `conservative` | Pre-renderizza solo al mousedown/touchstart | Link con costo elevato |

```javascript
// Speculation Rules dinamiche aggiunte via JavaScript
function addSpeculationRule(url, action = 'prerender') {
  // Verificare il supporto del browser
  if (!HTMLScriptElement.supports?.('speculationrules')) {
    // Fallback a prefetch tradizionale
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    document.head.appendChild(link);
    return;
  }

  const script = document.createElement('script');
  script.type = 'speculationrules';
  script.textContent = JSON.stringify({
    [action]: [{ source: 'list', urls: [url] }]
  });
  document.head.appendChild(script);
}

// Pre-renderizza la pagina quando l'utente mostra intenzione di navigare
document.querySelectorAll('a[data-prerender]').forEach(link => {
  link.addEventListener('mouseenter', () => {
    addSpeculationRule(link.href, 'prerender');
  }, { once: true });
});
```

**Impatto misurato:** Ray-Ban ha implementato speculation rules prerender e ha ottenuto un miglioramento LCP del 43% su mobile (da 4.69s a 2.66s), con un raddoppio del tasso di conversione. WordPress 6.8 ha integrato le speculation rules nel core da marzo 2025, e secondo il Web Almanac 2025 il 35% dei siti mobile le utilizza.

La Speculation Rules API e attualmente supportata dai browser basati su Chromium. Gli altri browser ignorano le regole senza effetti negativi (progressive enhancement).

---

## Performance Monitoring: Approfondimento

Come introdotto nella sezione sugli strumenti di misurazione, la libreria `web-vitals` e CrUX forniscono i dati fondamentali. Questa sezione approfondisce le strategie di monitoraggio continuo con Real User Monitoring (RUM), l'uso della build attribution della libreria web-vitals e l'integrazione dei performance budget nel CI/CD.

### Real User Monitoring (RUM) vs Dati Sintetici

I dati sintetici (Lighthouse, WebPageTest) sono riproducibili e utili per il debugging, ma non catturano la variabilita del mondo reale: dispositivi lenti, reti instabili, estensioni browser, cache fredde o calde, variazioni geografiche. RUM raccoglie metriche dagli utenti effettivi, fornendo la visione completa della performance in produzione.

Le differenze chiave tra CrUX e una soluzione RUM proprietaria:

| Aspetto | CrUX | RUM Proprietario |
|---------|------|-----------------|
| Raccolta | Automatica da Chrome | Codice JS nella pagina |
| Granularita | Aggregato 28 giorni, per origine/URL | Per sessione, per pagina, real-time |
| Segmentazione | Limitata (dispositivo, connessione) | Illimitata (utente, campagna, A/B test) |
| Debug | Solo metriche numeriche | Attribution, stack trace, elemento LCP |
| Costo | Gratuito | Variabile (self-hosted o SaaS) |
| Copertura browser | Solo Chrome | Tutti i browser con supporto PerformanceObserver |

### web-vitals Attribution Build

La build `attribution` della libreria web-vitals fornisce informazioni diagnostiche dettagliate che identificano la causa specifica di un valore CWV scarso, non solo il valore numerico.

```javascript
// Importare dalla build attribution (circa 2KB aggiuntivi)
import { onLCP, onINP, onCLS } from 'web-vitals/attribution';

onLCP((metric) => {
  const { attribution } = metric;
  sendToAnalytics({
    name: 'LCP',
    value: metric.value,
    rating: metric.rating,
    // Attribution LCP: capire PERCHE il LCP e lento
    lcpElement: attribution.element,         // es. "img.hero-image"
    lcpUrl: attribution.url,                 // URL della risorsa LCP
    ttfb: attribution.timeToFirstByte,       // TTFB del documento
    resourceLoadDelay: attribution.resourceLoadDelay,  // tempo prima dell'inizio download
    resourceLoadDuration: attribution.resourceLoadDuration, // durata download
    elementRenderDelay: attribution.elementRenderDelay  // tempo dal download al render
  });
});

onINP((metric) => {
  const { attribution } = metric;
  sendToAnalytics({
    name: 'INP',
    value: metric.value,
    rating: metric.rating,
    // Attribution INP: capire QUALE interazione e lenta e PERCHE
    eventTarget: attribution.eventTarget,    // es. "button#submit"
    eventType: attribution.eventType,        // es. "click"
    inputDelay: attribution.inputDelay,
    processingDuration: attribution.processingDuration,
    presentationDelay: attribution.presentationDelay,
    // Script piu lungo durante l'interazione
    longAnimationFrameEntries: attribution.longAnimationFrameEntries
  });
});

onCLS((metric) => {
  const { attribution } = metric;
  sendToAnalytics({
    name: 'CLS',
    value: metric.value,
    rating: metric.rating,
    // Attribution CLS: capire QUALI elementi si spostano
    largestShiftTarget: attribution.largestShiftTarget,  // es. "div.ad-container"
    largestShiftValue: attribution.largestShiftValue,
    largestShiftTime: attribution.largestShiftTime,
    loadState: attribution.loadState  // "loading", "dom-interactive", "complete"
  });
});
```

### Integrazione Performance Budget nel CI/CD

L'integrazione dei performance budget nel CI/CD trasforma il monitoraggio da reattivo (rilevare problemi in produzione) a preventivo (bloccare regressioni prima del deploy).

```yaml
# .github/workflows/perf-budget.yml
# Pipeline completa: build → serve → Lighthouse CI → bundlesize → report
name: Performance Budget
on:
  pull_request:
    branches: [main]

jobs:
  perf-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }

      - run: npm ci
      - run: npm run build

      # 1. Verifica dimensioni bundle
      - name: Bundle size check
        run: npx bundlesize

      # 2. Lighthouse CI con budget
      - name: Lighthouse CI
        uses: treosh/lighthouse-ci-action@v12
        with:
          configPath: .lighthouserc.json
          uploadArtifacts: true
          temporaryPublicStorage: true

      # 3. Commento automatico sulla PR con i risultati
      - name: Comment PR
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          header: lighthouse
          path: lighthouse-report.md
```

```json
// .lighthouserc.json — configurazione Lighthouse CI
{
  "ci": {
    "collect": {
      "startServerCommand": "npm run preview",
      "url": ["http://localhost:4173/", "http://localhost:4173/products"],
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "total-blocking-time": ["warn", { "maxNumericValue": 200 }],
        "interactive": ["warn", { "maxNumericValue": 3800 }],
        "resource-summary:script:size": ["error", { "maxNumericValue": 307200 }],
        "resource-summary:stylesheet:size": ["warn", { "maxNumericValue": 102400 }]
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

---

## Font Optimization: Approfondimento

Come introdotto nella sezione sui font, le strategie di base includono `font-display`, preload e WOFF2 con subsetting. Questa sezione approfondisce le tecniche avanzate per eliminare quasi completamente l'impatto dei font su LCP e CLS.

### Font Metric Override per Eliminare il CLS del FOUT

Quando il browser passa dal font di fallback al font web (FOUT), le differenze metriche causano un ricalcolo del layout. Le proprieta CSS `ascent-override`, `descent-override`, `line-gap-override` e `size-adjust` permettono di calibrare il font di fallback per avvicinarsi il piu possibile alle metriche del font web, riducendo o eliminando il layout shift.

```css
/* Passo 1: definire il font web */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-latin.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC;
}

/* Passo 2: definire un override del font di fallback con metriche calibrate */
/* I valori si ottengono con strumenti come https://screenspan.net/fallback */
@font-face {
  font-family: 'Inter Fallback';
  src: local('Arial');
  ascent-override: 89.62%;
  descent-override: 22.25%;
  line-gap-override: 0%;
  size-adjust: 107.64%;
}

/* Passo 3: usare entrambi nel font stack */
body {
  font-family: 'Inter', 'Inter Fallback', system-ui, sans-serif;
}
/* Il testo non "salta" quando Inter viene caricato, perche le metriche
   di 'Inter Fallback' sono calibrate per occupare lo stesso spazio */
```

### Preload Condizionale e Caricamento Adattivo

Non tutti gli utenti necessitano di tutti i font. Il caricamento adattivo riduce il consumo di banda caricando font diversi in base alle condizioni dell'utente.

```javascript
// Caricare font pesanti solo su connessioni veloci
if (navigator.connection?.effectiveType === '4g') {
  // Connessione veloce: preload del font brand premium
  const link = document.createElement('link');
  link.rel = 'preload';
  link.href = '/fonts/brand-variable.woff2';
  link.as = 'font';
  link.type = 'font/woff2';
  link.crossOrigin = 'anonymous';
  document.head.appendChild(link);
} else {
  // Connessione lenta: usare font di sistema, nessun download
  document.documentElement.style.fontFamily = 'system-ui, sans-serif';
}

// Caricare subset diversi in base alla lingua della pagina
const lang = document.documentElement.lang;
const fontSubset = lang === 'ja' ? 'japanese' :
                   lang === 'ar' ? 'arabic' :
                   lang === 'ru' ? 'cyrillic' : 'latin';

const fontLink = document.createElement('link');
fontLink.rel = 'preload';
fontLink.href = `/fonts/inter-${fontSubset}.woff2`;
fontLink.as = 'font';
fontLink.type = 'font/woff2';
fontLink.crossOrigin = 'anonymous';
document.head.appendChild(fontLink);
```

---

## Gestione degli Script di Terze Parti

Gli script di terze parti — analytics, tag manager, widget social, chat, pixel pubblicitari — rappresentano una delle cause principali di degradazione delle performance. Secondo le ricerche di Chrome, gli script di terze parti piu problematici bloccano il main thread per oltre 1.6 secondi su piu della meta dei siti analizzati. Oltre il 50% del tempo medio di caricamento di una pagina web e attribuibile a script di terze parti.

### Facade Pattern

Il facade pattern sostituisce embed pesanti di terze parti con placeholder leggeri che caricano il widget completo solo quando l'utente interagisce. Questo approccio e particolarmente efficace per embed video, mappe, widget di chat e player social.

```javascript
// Facade per YouTube — risparmia 600KB+ per utenti che non cliccano play
class YouTubeFacade extends HTMLElement {
  connectedCallback() {
    const videoId = this.getAttribute('videoid');
    const posterUrl = `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`;

    this.innerHTML = `
      <div class="youtube-facade" style="position:relative;cursor:pointer;
           background:url(${posterUrl}) center/cover;aspect-ratio:16/9">
        <button aria-label="Riproduci video"
          style="position:absolute;inset:0;display:grid;place-items:center;
                 background:rgba(0,0,0,.3);border:none;cursor:pointer">
          <svg width="68" height="48" viewBox="0 0 68 48">
            <path d="M66.5 7.7s-.7-4.7-2.8-6.8C60.7-2 57.2-2 55.6-2.2
              46.4-3 34-3 34-3s-12.4 0-21.6.8C10.8-2 7.3-2 4.3.9
              2.2 3 1.5 7.7 1.5 7.7S.8 13.3.8 18.9v5.2c0 5.6.7 11.2.7
              11.2s.7 4.7 2.8 6.8c3 3.1 6.9 3 8.7 3.3 6.3.6 26.8.9
              26.8.9s12.5 0 21.6-.8c1.6-.2 5.1-.2 8.1-3.1 2.1-2.1
              2.8-6.8 2.8-6.8s.7-5.6.7-11.2v-5.2c0-5.6-.7-11.2-.7-11.2Z"
              fill="red"/>
            <path d="M27.2 33.7 45.3 24l-18.1-9.7Z" fill="#fff"/>
          </svg>
        </button>
      </div>`;

    this.addEventListener('click', () => {
      // Solo al click: carica il player completo di YouTube
      this.innerHTML = `<iframe
        src="https://www.youtube.com/embed/${videoId}?autoplay=1"
        width="100%" style="aspect-ratio:16/9;border:0"
        allow="autoplay;encrypted-media" allowfullscreen></iframe>`;
    }, { once: true });
  }
}
customElements.define('youtube-facade', YouTubeFacade);

// Utilizzo: <youtube-facade videoid="dQw4w9WgXcQ"></youtube-facade>
```

### Partytown: Script di Terze Parti nel Web Worker

Partytown e una libreria che sposta l'esecuzione degli script di terze parti dal main thread a un web worker, eliminando il loro impatto su INP e TBT. Il main thread rimane libero per gestire le interazioni dell'utente, mentre analytics, tag manager e pixel tracking vengono eseguiti in un thread separato.

```html
<!-- Integrazione Partytown -->
<script>
  // Configurazione Partytown
  partytown = {
    // Specificare quali script eseguire nel worker
    forward: ['dataLayer.push', 'gtag'],
    // Script di debug (disabilitare in produzione)
    debug: false
  };
</script>
<script src="/~partytown/partytown.js"></script>

<!-- Gli script con type="text/partytown" vengono eseguiti nel web worker -->
<script type="text/partytown" src="https://www.googletagmanager.com/gtag/js?id=G-XXXXX"></script>
<script type="text/partytown">
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'G-XXXXX');
</script>
```

### Governance degli Script di Terze Parti

Senza un processo di governance, ogni campagna marketing, ogni richiesta di analisi e ogni test di vendor aggiunge script al tag manager che raramente vengono rimossi. Strategie di governance:

1. **Inventario:** mantenere un registro di tutti gli script di terze parti con proprietario, scopo, data di aggiunta e impatto misurato sulle performance (TBT, peso in KB).
2. **Budget per terze parti:** stabilire un budget massimo per il TBT attribuibile a terze parti (es. < 300ms) e per il numero di richieste di terze parti (es. < 10).
3. **Revisione periodica:** ogni trimestre, verificare che ogni script sia ancora necessario e che il suo impatto sia giustificato dal valore di business.
4. **Caricamento condizionale:** caricare script di analytics e marketing solo dopo il consenso dell'utente (GDPR) e solo quando il main thread e idle.
5. **SRI (Subresource Integrity):** per gli script serviti da CDN di terze parti, utilizzare hash SRI per verificare che il contenuto non sia stato manomesso.

```html
<!-- Script con Subresource Integrity -->
<script src="https://cdn.example.com/lib.js"
        integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8w"
        crossorigin="anonymous" defer></script>
```

---

## Edge Computing e Strategie CDN: Approfondimento

Come introdotto nella sezione Server-Side Performance, l'edge computing esegue la logica applicativa nei server piu vicini all'utente. Questa sezione approfondisce le architetture edge avanzate, i pattern di caching CDN e le strategie di distribuzione geografica.

### Architetture Edge: Modelli di Esecuzione

Le piattaforme edge offrono modelli di esecuzione diversi, ciascuno con caratteristiche di performance specifiche:

**V8 Isolates (Cloudflare Workers, Vercel Edge Functions):** utilizzano isolati V8 invece di container o VM. Un isolato V8 si avvia in meno di 1ms (vs 100-1000ms per un container Docker), consuma pochi KB di memoria e condivide un processo con migliaia di altri isolati. Questa architettura permette di distribuire logica su oltre 300 PoP (Points of Presence) di Cloudflare o 18 regioni Vercel con cold start quasi zero.

**Container-based (AWS Lambda@Edge, Azure Functions):** utilizzano container Docker o micro-VM con cold start di 100-500ms. Offrono compatibilita completa con Node.js e accesso a librerie native. Ideali per logica complessa che richiede dipendenze specifiche.

```javascript
// Pattern: routing edge con personalizzazione
// Cloudflare Worker — eseguito su 300+ PoP globali
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const country = request.cf?.country || 'US';
    const device = request.headers.get('Sec-CH-UA-Mobile') === '?1' ? 'mobile' : 'desktop';

    // Contenuto statico: servire dalla cache edge
    if (url.pathname.startsWith('/static/')) {
      const cache = caches.default;
      let response = await cache.match(request);
      if (response) return response;

      response = await fetch(request);
      response = new Response(response.body, response);
      response.headers.set('Cache-Control', 'public, max-age=31536000, immutable');
      await cache.put(request, response.clone());
      return response;
    }

    // HTML: personalizzazione edge con cache differenziata
    if (url.pathname === '/') {
      const cacheKey = new Request(`${url.origin}/?country=${country}&device=${device}`);
      const cache = caches.default;
      let response = await cache.match(cacheKey);

      if (!response) {
        response = await fetch(`${env.ORIGIN_URL}/?country=${country}&device=${device}`);
        response = new Response(response.body, response);
        response.headers.set('Cache-Control', 's-maxage=300, stale-while-revalidate=3600');
        response.headers.set('Vary', 'Sec-CH-UA-Mobile');
        await cache.put(cacheKey, response.clone());
      }
      return response;
    }

    return fetch(request);
  }
};
```

### Strategie di Caching CDN Avanzate

**Stale-While-Revalidate al livello CDN:** il CDN serve la risposta dalla cache immediatamente (anche se scaduta) e aggiorna la cache in background. L'utente riceve sempre una risposta rapida; la freschezza e garantita per le richieste successive.

**Cache Tagging e Purging:** i CDN moderni supportano tag sui contenuti cached per permettere invalidazione selettiva. Quando un prodotto viene aggiornato nel CMS, si invalida solo la cache delle pagine che contengono quel prodotto, senza purgare l'intera cache.

```
# Header di cache con tag per invalidazione selettiva
Cache-Control: public, s-maxage=86400
Cache-Tag: product-123, category-shoes, homepage
Surrogate-Key: product-123 category-shoes homepage

# Invalidazione selettiva via API del CDN
# Cloudflare: POST /zones/{zone}/purge_cache { "tags": ["product-123"] }
# Fastly: POST /service/{id}/purge/product-123
# Akamai: POST /ccu/v3/invalidate/tag/production { "objects": ["product-123"] }
```

**Edge Side Includes (ESI):** permettono di comporre una pagina da frammenti con policy di caching diverse. L'header della pagina (cambia raramente) viene cachato per un'ora; il corpo con il listino prezzi (cambia ogni 5 minuti) viene cachato per 5 minuti; il conteggio del carrello (personalizzato per utente) non viene cachato.

### Cosa Spostare Edge vs Cosa Mantenere all'Origine

| Adatto per l'edge | Mantenere all'origine |
|-------------------|----------------------|
| Autenticazione (verifica JWT) | Registrazione utente, cambio password |
| A/B test assignment | Logica di business complessa |
| Routing geografico | Transazioni database |
| Personalizzazione leggera (lingua, valuta) | Pagamenti e operazioni finanziarie |
| Redirect e rewrite URL | API con stato complesso |
| Trasformazione immagini | Operazioni batch |
| Rate limiting | Integrazioni con servizi backend |
| Risposta da cache con revalidazione | Query aggregate su grandi dataset |

La regola generale: spostare edge tutto cio che e stateless, read-heavy e latency-sensitive. Mantenere all'origine tutto cio che richiede consistenza forte, transazioni ACID o accesso a risorse condivise.

---

## Best Practices

Le seguenti dieci pratiche fondamentali sintetizzano le strategie di ottimizzazione più impattanti e dovrebbero diventare abitudini integrate nel processo di sviluppo quotidiano.

**1. Misurare prima di ottimizzare.** Non ottimizzare sulla base di intuizioni. Utilizzare Lighthouse, CrUX e il pannello Performance di DevTools per identificare i colli di bottiglia reali. Un'ottimizzazione basata su dati è sempre più efficace di una basata su supposizioni. Stabilire metriche di baseline prima di qualsiasi intervento per quantificare l'impatto effettivo delle modifiche.

**2. Definire e monitorare un performance budget.** Stabilire limiti per le dimensioni dei bundle JavaScript (< 300KB gzipped per il bundle principale), il numero di richieste HTTP, il tempo LCP (< 2.5s) e il CLS (< 0.1). Integrare il monitoraggio nel processo di CI/CD con Lighthouse CI o bundlesize in modo che le violazioni vengano rilevate automaticamente prima del deployment in produzione.

**3. Ottimizzare le immagini come priorità assoluta.** Le immagini rappresentano la quota maggiore di byte trasferiti nella maggioranza dei siti web. Servire formati moderni (AVIF con fallback WebP), utilizzare `srcset` e `sizes` per le dimensioni responsive, implementare il lazy loading per le immagini below-the-fold e specificare sempre `width` e `height` per prevenire layout shift. Utilizzare `fetchpriority="high"` e `loading="eager"` sull'immagine LCP.

**4. Minimizzare e differire il JavaScript.** Implementare code splitting per caricare solo il codice necessario per la vista corrente. Utilizzare `defer` per gli script applicativi, dynamic `import()` per funzionalità on-demand e tree shaking per eliminare il codice morto. Analizzare regolarmente la composizione del bundle per identificare dipendenze pesanti sostituibili con alternative più leggere o API native del browser.

**5. Eliminare le risorse render-blocking.** Incorporare il CSS critico (above-the-fold) inline nel `<head>` e caricare il resto in modo asincrono. Utilizzare `defer` per tutti gli script non critici. Preconnettere ai domini essenziali e precaricare le risorse critiche scoperte tardi dal parser (font referenziati nel CSS, immagini in background CSS).

**6. Ottimizzare i font web.** Utilizzare `font-display: swap` o `optional` per evitare testo invisibile. Precaricare i font critici con `<link rel="preload">` e l'attributo `crossorigin`. Servire esclusivamente il formato WOFF2 con subset dei soli glifi necessari. Valutare l'uso di variable fonts quando si utilizzano tre o più varianti della stessa famiglia tipografica.

**7. Implementare strategie di caching aggressive.** Utilizzare hash nel filename degli asset statici e servirli con `Cache-Control: public, max-age=31536000, immutable`. Configurare `stale-while-revalidate` per contenuti dinamici. Sfruttare un CDN per ridurre la latenza geografica e assorbire i picchi di traffico. Implementare caching a livello applicativo (Redis/Memcached) per le query al database più frequenti.

**8. Prioritizzare le animazioni composite.** Utilizzare esclusivamente `transform` e `opacity` per le animazioni CSS. Evitare di animare proprietà che causano layout (width, height, top, left, margin) o paint (background-color, box-shadow). Separare le letture e le scritture del DOM per prevenire il layout thrashing. Utilizzare `will-change` con parsimonia solo sugli elementi effettivamente animati.

**9. Adottare il rendering progressivo.** Utilizzare streaming SSR con React Suspense per inviare il contenuto al browser incrementalmente. Implementare skeleton screen per comunicare progresso durante il caricamento. Caricare il contenuto above-the-fold con priorità massima e differire tutto il resto. Considerare ISR per pagine che beneficiano del caching statico ma richiedono aggiornamenti periodici.

---

## Esercizi

### Esercizio 1 — Audit Lighthouse e Piano di Ottimizzazione

**Obiettivo:** eseguire un audit completo di un sito web esistente e produrre un piano di intervento prioritizzato.

Scegli un sito web pubblico (o un progetto personale) e conduci un'analisi sistematica:

- Esegui Lighthouse in Chrome DevTools in modalita incognito (per evitare interferenze di estensioni) su almeno 3 pagine: homepage, una pagina con molte immagini, una pagina con form interattivo
- Documenta i punteggi per Performance, Accessibility, Best Practices e SEO
- Per ogni metrica Core Web Vitals (LCP, INP, CLS), identifica l'elemento specifico responsabile usando il pannello Performance
- Crea un piano di ottimizzazione con priorita (alta/media/bassa), stima dell'impatto su CWV e complessita di implementazione
- Identifica le risorse render-blocking e proponi una strategia di caricamento alternativa per ciascuna

### Esercizio 2 — Ottimizzazione Immagini con Formati Moderni

**Obiettivo:** implementare una pipeline di ottimizzazione immagini completa con AVIF, WebP e responsive images.

Crea una pagina galleria con almeno 8 immagini di dimensioni diverse:

- Converti tutte le immagini in AVIF (compressione quality 60) e WebP (quality 75) con fallback JPEG usando `sharp` o `squoosh-cli`
- Implementa l'elemento `<picture>` con `<source>` per AVIF, WebP e fallback per ogni immagine
- Usa `srcset` con breakpoint a 400w, 800w, 1200w, 1600w e l'attributo `sizes` appropriato per ogni contesto
- Configura `loading="lazy"` per tutte le immagini below-the-fold e `loading="eager"` con `fetchpriority="high"` per l'immagine hero
- Specifica `width` e `height` su ogni `<img>` per prevenire CLS
- Misura il risparmio di byte totale rispetto alle immagini JPEG originali e il CLS prima/dopo

### Esercizio 3 — Code Splitting e Lazy Loading Avanzato

**Obiettivo:** ridurre il bundle JavaScript iniziale del 50% usando code splitting strategico e prefetching.

Parti da un'applicazione React SPA con almeno 5 route e dipendenze pesanti:

- Implementa route-based splitting con `React.lazy()` e `Suspense` per ogni pagina
- Configura `manualChunks` in `vite.config.ts` per separare vendor (react, chart.js, date-fns) in chunk dedicati
- Implementa prefetching delle route usando `<link rel="prefetch">` per le destinazioni piu probabili (es. dalla homepage verso la dashboard)
- Usa dynamic `import()` per caricare librerie pesanti solo quando necessario (es. `chart.js` solo quando l'utente naviga alla pagina analytics)
- Configura `rollup-plugin-visualizer` e confronta la dimensione del bundle prima e dopo l'ottimizzazione
- Il TTI (Time to Interactive) deve migliorare di almeno il 30%

### Esercizio 4 — Strategia di Caching Multi-Livello

**Obiettivo:** implementare una strategia di caching completa che copra browser, CDN e application layer.

Configura un progetto Express + React con:

- Header `Cache-Control` per asset statici con hash nel filename: `public, max-age=31536000, immutable`
- Header `Cache-Control` per HTML: `no-cache` con `ETag` per revalidazione
- Header `Cache-Control` per API: `private, max-age=0, stale-while-revalidate=60`
- Implementa un Service Worker con strategia Cache-First per asset statici e Network-First per API
- Configura Redis come cache applicativo per le query al database piu frequenti con TTL di 5 minuti
- Crea un endpoint `/api/cache-stats` che mostri hit rate, miss rate e dimensione della cache
- Misura il miglioramento del TTFB (Time to First Byte) prima e dopo l'implementazione

### Esercizio 5 — Performance Budget e Monitoraggio in CI/CD

**Obiettivo:** configurare un sistema di performance budget automatizzato che previene regressioni in produzione.

Integra il monitoraggio delle performance nella pipeline di sviluppo:

- Configura Lighthouse CI con budget per: performance score >= 90, LCP < 2.5s, CLS < 0.1, bundle JS < 300KB gzipped
- Crea un workflow GitHub Actions che esegua Lighthouse CI su ogni pull request e blocchi il merge se i budget vengono superati
- Configura `bundlesize` con limiti per ogni chunk: main < 150KB, vendor < 200KB, pagine lazy < 50KB ciascuna
- Implementa un dashboard HTML statico che mostri l'andamento delle metriche nel tempo (almeno le ultime 20 build)
- Configura alert (GitHub comment o Slack webhook) quando una metrica degrada di piu del 10% rispetto alla baseline
- Documenta la baseline corrente e le soglie scelte con la motivazione per ciascuna

---

## Letture e Riferimenti

### Documentazione ufficiale

- **web.dev/performance** — guida completa di Google alle metriche di performance web e strategie di ottimizzazione. https://web.dev/performance/ (consultato: 2026-05-24)
- **Core Web Vitals** — definizione ufficiale delle metriche LCP, INP e CLS con soglie e metodologia di misurazione. https://web.dev/vitals/ (consultato: 2026-05-24)
- **Lighthouse** — strumento automatizzato di audit per performance, accessibilita e best practices. https://developer.chrome.com/docs/lighthouse/ (consultato: 2026-05-24)
- **Chrome DevTools Performance** — documentazione del pannello Performance per profiling di runtime e rendering. https://developer.chrome.com/docs/devtools/performance/ (consultato: 2026-05-24)
- **MDN Web Performance** — risorse Mozilla su metriche, API e tecniche di ottimizzazione delle performance web. https://developer.mozilla.org/en-US/docs/Web/Performance (consultato: 2026-05-24)
- **Squoosh** — tool di compressione immagini con supporto AVIF, WebP e confronto qualita visiva. https://squoosh.app/ (consultato: 2026-05-24)
- **Lighthouse CI** — integrazione di Lighthouse nelle pipeline CI/CD con budget e confronto tra build. https://github.com/GoogleChrome/lighthouse-ci (consultato: 2026-05-24)

### Libri e approfondimenti

- Addy Osmani, *Learning Patterns*, free online, 2022.
- Jeremy Wagner, *Web Performance in Action*, Manning, 2017.
- Lara Hogan, *Designing for Performance*, O'Reilly, 2014.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [01 — HTML5](01-html5.md) | Struttura semantica e attributi (`loading`, `fetchpriority`, `srcset`) fondamentali per LCP e CLS |
| [02 — CSS3](02-css3.md) | CSS critico, animazioni composite e `will-change` per evitare layout thrashing |
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Conoscenza del runtime JS necessaria per comprendere il blocking del main thread |
| [16 — Build Tools e Deploy](16-build-tools-e-deploy.md) | Bundling, tree shaking e code splitting sono operazioni di build con impatto diretto sulle performance |
| [18 — PWA e Tecnologie Avanzate](18-pwa-e-tecnologie-avanzate.md) | Service Worker e cache strategies per performance offline e stale-while-revalidate |
| [25 — Next.js](25-nextjs-guida-completa.md) | SSR, ISR e streaming per ottimizzazione del rendering lato server |

---

## Glossario

| Termine | Definizione |
|---|---|
| **LCP** | Largest Contentful Paint: tempo di rendering dell'elemento visibile piu grande nel viewport (soglia: < 2.5s). |
| **INP** | Interaction to Next Paint: latenza massima tra l'input dell'utente e il prossimo aggiornamento visivo (soglia: < 200ms). |
| **CLS** | Cumulative Layout Shift: somma cumulativa degli spostamenti inattesi degli elementi visibili durante il caricamento (soglia: < 0.1). |
| **FCP** | First Contentful Paint: tempo di rendering del primo contenuto visibile (testo, immagine, canvas). |
| **TTFB** | Time to First Byte: tempo tra la richiesta HTTP e la ricezione del primo byte della risposta dal server. |
| **TTI** | Time to Interactive: momento in cui la pagina risponde in modo affidabile all'input dell'utente entro 50ms. |
| **Render-blocking** | Risorsa (CSS, JS sincrono) che impedisce al browser di renderizzare contenuto finche non viene scaricata e processata. |
| **Critical CSS** | Sottoinsieme minimo di CSS necessario per renderizzare il contenuto above-the-fold, inserito inline nel `<head>`. |
| **Lazy loading** | Tecnica di caricamento differito che scarica risorse (immagini, script, componenti) solo quando entrano nel viewport. |
| **Code splitting** | Suddivisione del bundle JavaScript in chunk separati caricati on-demand per ridurre il payload iniziale. |
| **Tree shaking** | Eliminazione statica del codice morto (esportazioni non importate) durante il processo di bundling. |
| **CDN** | Content Delivery Network: rete di server edge che distribuisce contenuti statici dalla posizione geografica piu vicina all'utente. |
| **Performance budget** | Limite quantitativo (dimensione bundle, tempo di caricamento, punteggio Lighthouse) che non deve essere superato. |
| **Stale-while-revalidate** | Strategia di caching che serve la risposta dalla cache immediatamente e aggiorna la cache in background. |
| **Layout thrashing** | Degradazione delle performance causata da letture e scritture alternate del DOM che forzano ricalcoli di layout ripetuti. |

**10. Monitorare la performance degli utenti reali.** I dati di laboratorio non catturano la variabilità delle condizioni reali: dispositivi lenti, reti instabili, estensioni browser. Integrare la libreria `web-vitals` per raccogliere LCP, INP, CLS e TTFB dagli utenti reali. Segmentare i dati per tipo di dispositivo, paese e tipo di connessione. Configurare alert automatici quando le metriche al 75° percentile superano le soglie "buono" dei Core Web Vitals per intervenire tempestivamente prima che il degrado diventi sistematico.