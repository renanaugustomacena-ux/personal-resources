---
corso: "Sviluppo Web"
fase: "6 — Tecnologie Avanzate"
modulo: "18"
titolo: "PWA e Tecnologie Web Avanzate"
versione: "Service Worker API / Web Push / Web Components"
livello: "Avanzato"
prerequisiti:
  - "04 — JavaScript Fondamenti"
  - "05 — JavaScript Avanzato"
  - "17 — Performance Web"
obiettivi:
  - "Costruire Progressive Web App con Service Worker e manifest"
  - "Implementare offline-first con cache strategies (stale-while-revalidate)"
  - "Utilizzare Web Push per notifiche"
  - "Creare Web Components con Custom Elements e Shadow DOM"
  - "Comprendere WebAssembly e casi d'uso per performance critica"
  - "Implementare Web Share, File System Access e altre API moderne"
tag: [PWA, Service-Worker, Web-Push, Web-Components, WebAssembly, offline-first]
---

# PWA e Tecnologie Web Avanzate

> **Modulo 18** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [JavaScript Fondamenti](04-javascript-fondamenti.md), [JavaScript Avanzato](05-javascript-avanzato.md), [Performance Web](17-performance-web.md)
>
> Al termine di questo modulo saprai:
> 1. Costruire Progressive Web App con Service Worker e manifest
> 2. Implementare offline-first con cache strategies
> 3. Utilizzare Web Push per notifiche
> 4. Creare Web Components con Custom Elements e Shadow DOM
> 5. Comprendere WebAssembly e casi d'uso per performance critica
> 6. Implementare Web Share, File System Access e altre API moderne
>
> **Tempo stimato:** 6-8 ore · **Livello:** Avanzato

## Idee guida
1. **Service Worker = offline-first foundation.**
2. **WebAssembly per perf code compute-heavy.**
3. **WebGPU 2024+ replaces WebGL.**
4. **Workbox abstracts service worker complessita.**


## Panoramica sulle Progressive Web App

### Che Cosa Sono le PWA

Le **Progressive Web App** (PWA) rappresentano un paradigma di sviluppo web che combina il meglio delle applicazioni web tradizionali con le funzionalità tipiche delle app native. Introdotte da Google nel 2015, le PWA sfruttano le moderne Web API e strategie di progressive enhancement per offrire esperienze utente affidabili, veloci e coinvolgenti direttamente dal browser.

Una PWA non e un framework o una tecnologia specifica, ma piuttosto un insieme di principi e pattern che, applicati insieme, trasformano un sito web in un'esperienza simile a un'app nativa. I tre pilastri fondamentali sono:

- **Affidabilita**: l'applicazione si carica istantaneamente e funziona anche in assenza di connessione di rete, eliminando la schermata del dinosauro offline di Chrome.
- **Velocita**: le interazioni rispondono rapidamente grazie a strategie di caching intelligente e rendering ottimizzato.
- **Coinvolgimento**: l'app e installabile sulla schermata home del dispositivo, supporta le notifiche push e offre un'esperienza immersiva a schermo intero.

### Vantaggi delle PWA

Le PWA offrono numerosi vantaggi rispetto sia alle app native sia ai siti web tradizionali:

**Distribuzione senza app store**: non serve pubblicare su Google Play o App Store, eliminando i costi di commissione e i tempi di approvazione. Gli aggiornamenti sono istantanei poiche il codice e servito dal web.

**Un'unica codebase**: un solo progetto web serve tutti i dispositivi e le piattaforme, riducendo i costi di sviluppo e manutenzione rispetto allo sviluppo nativo separato per iOS e Android.

**Funzionamento offline**: grazie ai Service Worker, l'app puo funzionare senza connessione, memorizzando risorse e dati nella cache del browser.

**Installabilita**: gli utenti possono aggiungere la PWA alla schermata home del dispositivo con un singolo tap, ottenendo un'icona dedicata e un'esperienza di avvio senza barra degli indirizzi.

**Aggiornamenti automatici**: ogni volta che l'utente apre l'app, il Service Worker verifica se sono disponibili nuove versioni delle risorse e le aggiorna in background.

**Sicurezza**: le PWA richiedono HTTPS, garantendo che tutte le comunicazioni tra client e server siano crittografate.

**Indicizzabilita**: essendo pagine web, le PWA sono indicizzate dai motori di ricerca, combinando la scopribilita del web con l'esperienza utente delle app.

---

## Service Worker

### Concetto e Ciclo di Vita

Il **Service Worker** e il cuore tecnologico di ogni PWA. Si tratta di uno script JavaScript che il browser esegue in background, separato dalla pagina web, agendo come un proxy di rete programmabile tra l'applicazione e il server.

Il ciclo di vita di un Service Worker attraversa tre fasi principali:

**1. Installazione (install)**: quando il browser rileva un Service Worker nuovo o modificato, lo scarica e attiva l'evento `install`. Questa fase e ideale per pre-cacheare le risorse statiche essenziali (app shell).

```javascript
// sw.js
const CACHE_NAME = 'app-cache-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/styles/main.css',
  '/scripts/app.js',
  '/images/logo.png',
  '/offline.html'
];

self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installazione in corso...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Pre-caching delle risorse');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => {
        // Forza l'attivazione immediata senza attendere
        return self.skipWaiting();
      })
  );
});
```

**2. Attivazione (activate)**: dopo l'installazione, il Service Worker entra nello stato di attesa finche tutte le schede che usano la versione precedente non vengono chiuse. L'evento `activate` e il momento ideale per pulire le cache obsolete.

```javascript
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Attivazione in corso...');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME)
            .map((name) => {
              console.log(`[Service Worker] Eliminazione cache obsoleta: ${name}`);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        // Prende immediatamente il controllo di tutte le pagine
        return self.clients.claim();
      })
  );
});
```

**3. Intercettazione (fetch)**: una volta attivo, il Service Worker intercetta ogni richiesta di rete effettuata dalle pagine sotto il suo controllo, permettendo di implementare strategie di caching personalizzate.

### Deep-Dive: Ciclo di Vita e Stati del Service Worker

Il ciclo di vita del Service Worker e intenzionalmente complesso per garantire aggiornamenti sicuri senza interrompere le sessioni attive. Comprendere ogni transizione di stato e fondamentale per evitare bug sottili durante gli aggiornamenti.

#### Diagramma degli Stati

Un Service Worker attraversa i seguenti stati in sequenza: **parsed** (lo script e stato scaricato e analizzato), **installing** (l'evento `install` e in corso), **installed/waiting** (l'installazione e completata ma esiste ancora un Service Worker attivo precedente), **activating** (l'evento `activate` e in corso), **activated** (il Service Worker controlla le pagine), **redundant** (il Service Worker e stato sostituito o l'installazione e fallita).

La transizione critica e quella da **installed/waiting** ad **activating**: per impostazione predefinita, un nuovo Service Worker resta in stato di attesa finche tutte le schede controllate dal vecchio Service Worker non vengono chiuse. Questo previene situazioni in cui una pagina caricata con il vecchio codice riceve risorse dalla cache del nuovo Service Worker, potenzialmente incompatibili.

#### Controllo del Processo di Aggiornamento

Il browser verifica automaticamente la presenza di aggiornamenti del Service Worker in queste situazioni: quando l'utente naviga verso una pagina nello scope del Service Worker, quando un evento push o sync viene ricevuto e sono passate almeno 24 ore dall'ultimo controllo, quando viene chiamato `registration.update()` esplicitamente.

Il confronto avviene byte-per-byte: se anche un singolo byte del file del Service Worker e cambiato, il browser avvia il processo di installazione del nuovo worker. Per questo motivo, e sconsigliato includere hash o timestamp dinamici nel file del Service Worker stesso, poiche causerebbero aggiornamenti inutili a ogni caricamento.

```javascript
// Gestione avanzata degli aggiornamenti nel Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
  // ATTENZIONE: skipWaiting() forza l'attivazione immediata
  // Usare con cautela: la pagina potrebbe avere risorse incompatibili in memoria
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      // Pulisci le cache obsolete
      caches.keys().then((nomi) =>
        Promise.all(
          nomi.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n))
        )
      ),
      // Prendi il controllo delle pagine esistenti
      // Senza clients.claim(), il nuovo SW controlla solo le pagine caricate successivamente
      self.clients.claim()
    ])
  );
});
```

#### Comunicazione tra Service Worker e Pagina

Il Service Worker e la pagina sono contesti di esecuzione separati. La comunicazione avviene tramite `postMessage()` e l'interfaccia `MessageChannel`, fondamentale per coordinare aggiornamenti, sincronizzazioni e notifiche.

```javascript
// Dalla pagina: invia un messaggio al Service Worker
async function inviaAlServiceWorker(messaggio) {
  const registration = await navigator.serviceWorker.ready;
  registration.active.postMessage(messaggio);
}

// Dalla pagina: ascolta i messaggi dal Service Worker
navigator.serviceWorker.addEventListener('message', (event) => {
  const { tipo, dati } = event.data;
  switch (tipo) {
    case 'CACHE_AGGIORNATA':
      console.log('Cache aggiornata per:', dati.url);
      break;
    case 'SYNC_COMPLETATA':
      console.log('Sincronizzazione completata:', dati.risultato);
      aggiornaInterfaccia(dati.risultato);
      break;
  }
});

// Nel Service Worker: gestisci i messaggi dalla pagina
self.addEventListener('message', (event) => {
  const { tipo, dati } = event.data;

  switch (tipo) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;

    case 'INVALIDA_CACHE':
      caches.open(CACHE_NAME).then((cache) => cache.delete(dati.url));
      break;

    case 'RICHIEDI_STATO':
      // Rispondi usando il MessagePort
      event.source.postMessage({
        tipo: 'STATO',
        dati: { versione: CACHE_NAME, online: self.navigator?.onLine }
      });
      break;
  }
});

// Nel Service Worker: invia un messaggio a tutte le pagine controllate
async function notificaTuttiIClient(messaggio) {
  const clientList = await self.clients.matchAll({
    type: 'window',
    includeUncontrolled: false
  });

  clientList.forEach((client) => {
    client.postMessage(messaggio);
  });
}
```

#### Scope e Registrazione Multipla

Lo **scope** del Service Worker determina quali pagine ricadono sotto il suo controllo. Per impostazione predefinita, lo scope corrisponde alla directory che contiene il file del Service Worker. Un Service Worker in `/app/sw.js` controlla solo le pagine sotto `/app/`. Per controllare l'intero sito, il file deve essere nella root (`/sw.js`).

E possibile registrare piu Service Worker con scope diversi per aree distinte dell'applicazione, ad esempio un Service Worker dedicato per la sezione admin e uno per l'area pubblica. In caso di scope sovrapposti, il Service Worker con lo scope piu specifico ha la precedenza.

```javascript
// Registrazione di Service Worker con scope diversi
await navigator.serviceWorker.register('/sw-app.js', { scope: '/app/' });
await navigator.serviceWorker.register('/sw-admin.js', { scope: '/admin/' });
// /app/dashboard sara controllato da sw-app.js
// /admin/settings sara controllato da sw-admin.js
```

### Registrazione del Service Worker

La registrazione avviene dalla pagina principale dell'applicazione:

```javascript
// app.js
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'  // Controlla tutte le pagine del dominio
      });

      console.log('Service Worker registrato con successo:', registration.scope);

      // Verifica aggiornamenti periodicamente
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        console.log('Nuovo Service Worker trovato, stato:', newWorker.state);

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'activated') {
            // Notifica l'utente che e disponibile una nuova versione
            mostraNotificaAggiornamento();
          }
        });
      });
    } catch (errore) {
      console.error('Registrazione Service Worker fallita:', errore);
    }
  });
}
```

### Strategie di Cache

Le strategie di caching determinano come il Service Worker gestisce le richieste di rete. Le principali sono:

**Cache-First (Cache con fallback alla rete)**: cerca prima nella cache, ricorre alla rete solo se la risorsa non e presente. Ideale per risorse statiche che cambiano raramente (immagini, font, CSS).

```javascript
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse; // Risposta dalla cache
        }
        return fetch(event.request).then((networkResponse) => {
          // Salva la nuova risorsa in cache per le prossime richieste
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        });
      })
      .catch(() => {
        // Fallback alla pagina offline se la rete non e disponibile
        if (event.request.mode === 'navigate') {
          return caches.match('/offline.html');
        }
      })
  );
});
```

**Network-First (Rete con fallback alla cache)**: tenta prima la rete, ricorre alla cache in caso di errore. Ideale per contenuti dinamici come feed di notizie o dati API che devono essere aggiornati.

```javascript
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          // Aggiorna la cache con la risposta fresca
          const clonedResponse = networkResponse.clone();
          caches.open('api-cache').then((cache) => {
            cache.put(event.request, clonedResponse);
          });
          return networkResponse;
        })
        .catch(() => {
          // Rete non disponibile, usa la cache
          return caches.match(event.request);
        })
    );
  }
});
```

**Stale-While-Revalidate**: restituisce immediatamente la versione in cache (anche se potenzialmente obsoleta) e contemporaneamente aggiorna la cache in background con la risposta dalla rete. Offre il miglior compromesso tra velocita percepita e freschezza dei dati.

```javascript
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.match(event.request).then((cachedResponse) => {
        const fetchPromise = fetch(event.request).then((networkResponse) => {
          cache.put(event.request, networkResponse.clone());
          return networkResponse;
        });
        // Restituisce la cache immediatamente, aggiorna in background
        return cachedResponse || fetchPromise;
      });
    })
  );
});
```

### Workbox: Libreria per Service Worker

**Workbox** e una libreria sviluppata da Google che semplifica enormemente la gestione dei Service Worker. Fornisce moduli predefiniti per le strategie di caching, il precaching, il routing e molto altro.

```javascript
// sw.js con Workbox
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import {
  CacheFirst,
  NetworkFirst,
  StaleWhileRevalidate
} from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// Pre-cache delle risorse generate dal build tool
precacheAndRoute(self.__WB_MANIFEST);

// Immagini: cache-first con scadenza a 30 giorni
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 60,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 giorni
      }),
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
    ],
  })
);

// Chiamate API: network-first con fallback alla cache
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    networkTimeoutSeconds: 5,
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 5 * 60, // 5 minuti
      }),
    ],
  })
);

// CSS e JS: stale-while-revalidate
registerRoute(
  ({ request }) =>
    request.destination === 'style' || request.destination === 'script',
  new StaleWhileRevalidate({
    cacheName: 'static-resources',
  })
);
```

Per integrare Workbox con un bundler come Webpack:

```javascript
// webpack.config.js
const { InjectManifest } = require('workbox-webpack-plugin');

module.exports = {
  plugins: [
    new InjectManifest({
      swSrc: './src/sw.js',
      swDest: 'sw.js',
      maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5 MB
    }),
  ],
};
```

### Workbox Avanzato: Strategie, Routing e Background Sync

Oltre alla configurazione base, Workbox offre moduli avanzati che coprono scenari complessi di caching, sincronizzazione e comunicazione con la pagina principale. Comprendere questi moduli a fondo consente di costruire PWA robuste con strategie di caching ottimali per ogni tipo di risorsa.

#### Strategie di Caching Personalizzate

Workbox fornisce cinque strategie predefinite (`CacheFirst`, `NetworkFirst`, `StaleWhileRevalidate`, `NetworkOnly`, `CacheOnly`), ma consente anche di creare strategie personalizzate estendendo la classe base `Strategy`. Questo e utile quando la logica di caching non rientra nelle strategie standard, ad esempio per risorse che richiedono validazione condizionale o trasformazione della risposta prima del salvataggio.

```javascript
import { Strategy } from 'workbox-strategies';

class CacheConValidazione extends Strategy {
  async _handle(request, handler) {
    const rispostaCache = await handler.cacheMatch(request);

    // Se la cache ha meno di 5 minuti, restituiscila direttamente
    if (rispostaCache) {
      const dataCache = rispostaCache.headers.get('sw-cache-timestamp');
      const eta = Date.now() - parseInt(dataCache || '0', 10);
      if (eta < 5 * 60 * 1000) {
        return rispostaCache;
      }
    }

    // Altrimenti, richiedi alla rete e aggiorna la cache
    try {
      const rispostaRete = await handler.fetchAndCachePut(request);
      // Aggiungi un timestamp personalizzato alla risposta cachata
      const headers = new Headers(rispostaRete.headers);
      headers.set('sw-cache-timestamp', Date.now().toString());
      const rispostaModificata = new Response(rispostaRete.body, {
        status: rispostaRete.status,
        statusText: rispostaRete.statusText,
        headers
      });
      const cache = await caches.open(this.cacheName);
      await cache.put(request, rispostaModificata);
      return rispostaRete;
    } catch (errore) {
      // Fallback alla cache anche se obsoleta
      if (rispostaCache) return rispostaCache;
      throw errore;
    }
  }
}
```

#### Routing Avanzato con workbox-routing

Il modulo `workbox-routing` supporta tre tipi di matcher per instradare le richieste alle strategie appropriate: stringhe esatte, espressioni regolari e funzioni callback. Le funzioni callback offrono la massima flessibilita, ricevendo un oggetto con `url`, `request`, `event` e `sameOrigin`.

```javascript
import { registerRoute, Route, NavigationRoute } from 'workbox-routing';
import { NetworkFirst, CacheFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';

// Routing per espressione regolare: font di terze parti
registerRoute(
  /^https:\/\/fonts\.(googleapis|gstatic)\.com\/.*/,
  new CacheFirst({
    cacheName: 'google-fonts',
    plugins: [
      new ExpirationPlugin({ maxEntries: 30, maxAgeSeconds: 365 * 24 * 60 * 60 }),
    ],
  })
);

// Routing per funzione callback: solo richieste GET a /api/ con token valido
registerRoute(
  ({ url, request }) => {
    return url.pathname.startsWith('/api/') &&
           request.method === 'GET' &&
           url.searchParams.has('token');
  },
  new NetworkFirst({
    cacheName: 'api-autenticata',
    networkTimeoutSeconds: 3,
  })
);

// NavigationRoute: gestisce tutte le richieste di navigazione con un'app shell
const navigationRoute = new NavigationRoute(
  new NetworkFirst({ cacheName: 'pagine', networkTimeoutSeconds: 4 }),
  {
    allowlist: [/^\/app\//],  // Solo percorsi sotto /app/
    denylist: [/^\/api\//],   // Mai intercettare le API
  }
);
registerRoute(navigationRoute);

// Route personalizzata con gestione di fallback
const routeFallback = new Route(
  ({ request }) => request.destination === 'document',
  async ({ event }) => {
    try {
      return await new NetworkFirst({ cacheName: 'pagine' }).handle(event);
    } catch {
      return caches.match('/offline.html');
    }
  }
);
registerRoute(routeFallback);
```

#### workbox-background-sync: Coda di Richieste Offline

Il modulo `workbox-background-sync` implementa una coda persistente che salva le richieste fallite in IndexedDB e le ritenta automaticamente quando la connessione torna disponibile. Internamente sfrutta la Background Sync API dove supportata, con fallback a un meccanismo basato su timer.

```javascript
import { BackgroundSyncPlugin } from 'workbox-background-sync';
import { registerRoute } from 'workbox-routing';
import { NetworkOnly } from 'workbox-strategies';

// Coda per le richieste POST alle API
const codaSincronizzazione = new BackgroundSyncPlugin('coda-api', {
  maxRetentionTime: 24 * 60, // Conserva le richieste per 24 ore (in minuti)
  onSync: async ({ queue }) => {
    let voce;
    while ((voce = await queue.shiftRequest())) {
      try {
        const risposta = await fetch(voce.request.clone());
        if (!risposta.ok) {
          throw new Error(`Risposta ${risposta.status}`);
        }
        console.log('[BgSync] Richiesta sincronizzata:', voce.request.url);
      } catch (errore) {
        console.error('[BgSync] Errore, reinserimento in coda:', errore);
        await queue.unshiftRequest(voce);
        throw errore; // Interrompe la sincronizzazione, verra ritentata
      }
    }
  }
});

// Applica la coda a tutte le richieste POST verso /api/
registerRoute(
  ({ url, request }) =>
    url.pathname.startsWith('/api/') && request.method === 'POST',
  new NetworkOnly({ plugins: [codaSincronizzazione] })
);
```

#### workbox-broadcast-update: Notificare gli Aggiornamenti

Quando si usa la strategia Stale-While-Revalidate, l'utente riceve immediatamente la versione in cache. Se la risposta dalla rete e diversa, il modulo `workbox-broadcast-update` invia un messaggio alla pagina tramite la Broadcast Channel API, permettendo all'applicazione di mostrare un banner di aggiornamento.

```javascript
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate } from 'workbox-strategies';
import { BroadcastUpdatePlugin } from 'workbox-broadcast-update';

registerRoute(
  ({ url }) => url.pathname.startsWith('/api/feed'),
  new StaleWhileRevalidate({
    cacheName: 'feed-cache',
    plugins: [
      new BroadcastUpdatePlugin({
        headersToCheck: ['content-length', 'etag', 'last-modified'],
      }),
    ],
  })
);
```

```javascript
// Nella pagina principale: ascolta gli aggiornamenti
const canale = new BroadcastChannel('workbox');

canale.addEventListener('message', (event) => {
  if (event.data.meta === 'workbox-broadcast-update') {
    const { cacheName, updatedURL } = event.data.payload;
    console.log(`[Aggiornamento] ${updatedURL} in ${cacheName}`);
    mostraBannerAggiornamento('Nuovi contenuti disponibili. Aggiorna la pagina.');
  }
});
```

#### workbox-window: Gestione del Ciclo di Vita dal Main Thread

Il modulo `workbox-window` facilita la registrazione del Service Worker e la gestione degli aggiornamenti dalla pagina principale, offrendo un'API basata su eventi piu pulita rispetto alla registrazione manuale.

```javascript
import { Workbox } from 'workbox-window';

if ('serviceWorker' in navigator) {
  const wb = new Workbox('/sw.js');

  // Un nuovo Service Worker e stato installato ma attende l'attivazione
  wb.addEventListener('waiting', (event) => {
    const aggiorna = confirm(
      'Nuova versione disponibile. Vuoi aggiornare ora?'
    );
    if (aggiorna) {
      // Dice al Service Worker in attesa di prendere il controllo
      wb.messageSkipWaiting();
    }
  });

  // Il nuovo Service Worker ha preso il controllo
  wb.addEventListener('controlling', () => {
    // Ricarica la pagina per usare le nuove risorse
    window.location.reload();
  });

  // Il Service Worker e stato attivato per la prima volta
  wb.addEventListener('activated', (event) => {
    if (!event.isUpdate) {
      console.log('Service Worker attivato per la prima volta');
    }
  });

  wb.register();
}
```

---

## Web App Manifest

### Struttura del manifest.json

Il **Web App Manifest** e un file JSON che fornisce al browser le informazioni necessarie per installare la PWA sul dispositivo dell'utente. Definisce l'aspetto e il comportamento dell'app quando viene avviata dalla schermata home.

```json
{
  "name": "Gestione Progetti Pro",
  "short_name": "ProgettiPro",
  "description": "Applicazione completa per la gestione di progetti e team di lavoro",
  "start_url": "/dashboard?source=pwa",
  "scope": "/",
  "display": "standalone",
  "orientation": "any",
  "theme_color": "#1a73e8",
  "background_color": "#ffffff",
  "lang": "it-IT",
  "dir": "ltr",
  "categories": ["productivity", "business"],
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "screenshots": [
    {
      "src": "/screenshots/desktop.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide",
      "label": "Dashboard principale su desktop"
    },
    {
      "src": "/screenshots/mobile.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow",
      "label": "Dashboard principale su mobile"
    }
  ],
  "shortcuts": [
    {
      "name": "Nuovo Progetto",
      "short_name": "Nuovo",
      "url": "/projects/new",
      "icons": [{ "src": "/icons/new-project.png", "sizes": "96x96" }]
    },
    {
      "name": "I Miei Task",
      "short_name": "Task",
      "url": "/tasks",
      "icons": [{ "src": "/icons/tasks.png", "sizes": "96x96" }]
    }
  ],
  "related_applications": [],
  "prefer_related_applications": false
}
```

Il manifest viene collegato alla pagina HTML tramite un tag link:

```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#1a73e8">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="ProgettiPro">
<link rel="apple-touch-icon" href="/icons/icon-152x152.png">
```

### Modalita di Visualizzazione (Display Modes)

Il campo `display` controlla come l'app appare all'utente una volta installata:

- **`fullscreen`**: occupa l'intero schermo senza alcun elemento dell'interfaccia del browser. Ideale per giochi e presentazioni.
- **`standalone`**: l'app appare come un'applicazione nativa con la propria finestra, senza barra degli indirizzi. La scelta piu comune per le PWA.
- **`minimal-ui`**: simile a standalone ma con un set minimo di controlli di navigazione del browser.
- **`browser`**: l'app si apre in una scheda del browser standard. Non offre un'esperienza da app.

### Gestione del Prompt di Installazione

Il browser mostra automaticamente un banner di installazione quando i criteri PWA sono soddisfatti. Tuttavia, e possibile intercettare e personalizzare questo comportamento con l'evento `beforeinstallprompt`:

```javascript
let deferredPrompt;
const installButton = document.getElementById('btn-installa');

window.addEventListener('beforeinstallprompt', (event) => {
  // Impedisce la visualizzazione del mini-infobar predefinito
  event.preventDefault();
  // Salva l'evento per usarlo in seguito
  deferredPrompt = event;
  // Mostra il pulsante di installazione personalizzato
  installButton.style.display = 'block';
});

installButton.addEventListener('click', async () => {
  if (!deferredPrompt) return;

  // Mostra il prompt di installazione del browser
  deferredPrompt.prompt();

  // Attende la scelta dell'utente
  const { outcome } = await deferredPrompt.userChoice;

  if (outcome === 'accepted') {
    console.log('Utente ha accettato l\'installazione');
    analytics.track('pwa_installata');
  } else {
    console.log('Utente ha rifiutato l\'installazione');
  }

  // Il prompt puo essere usato una sola volta
  deferredPrompt = null;
  installButton.style.display = 'none';
});

// Rileva quando l'app e stata effettivamente installata
window.addEventListener('appinstalled', () => {
  console.log('PWA installata con successo');
  deferredPrompt = null;
});
```

---

## Supporto Offline

### Cache API

La **Cache API** fornisce un meccanismo di storage persistente per coppie request/response. A differenza della cache HTTP del browser, la Cache API offre un controllo programmatico completo su cosa viene memorizzato e per quanto tempo.

```javascript
// Operazioni fondamentali con la Cache API
async function gestisciCache() {
  // Apri o crea una cache
  const cache = await caches.open('dati-utente-v1');

  // Aggiungi una singola risorsa
  await cache.add('/api/profilo');

  // Aggiungi piu risorse contemporaneamente
  await cache.addAll(['/api/progetti', '/api/notifiche']);

  // Aggiungi una coppia request/response personalizzata
  const response = new Response(JSON.stringify({ stato: 'offline' }), {
    headers: { 'Content-Type': 'application/json' }
  });
  await cache.put('/api/stato', response);

  // Cerca una risorsa nella cache
  const risultato = await cache.match('/api/profilo');
  if (risultato) {
    const dati = await risultato.json();
    console.log('Dati dal cache:', dati);
  }

  // Rimuovi una singola risorsa
  await cache.delete('/api/vecchi-dati');

  // Elenca tutte le cache disponibili
  const nomiCache = await caches.keys();
  console.log('Cache disponibili:', nomiCache);

  // Elimina un'intera cache
  await caches.delete('dati-utente-v0');
}
```

### Cache API: Strategie Avanzate e Pattern

Oltre alle operazioni base, la Cache API supporta pattern avanzati fondamentali per PWA di produzione. La gestione corretta del versionamento, della dimensione e delle politiche di pulizia e essenziale per evitare che la cache cresca indefinitamente e degradi l'esperienza utente.

#### Versionamento della Cache

Il pattern di versionamento prevede l'uso di un prefisso costante e un suffisso di versione, con pulizia automatica durante l'attivazione del Service Worker. Questo garantisce che risorse obsolete non vengano mai servite dopo un aggiornamento.

```javascript
const CACHE_PREFIX = 'mia-app';
const CACHE_VERSION = 'v3';
const CACHE_NAME = `${CACHE_PREFIX}-${CACHE_VERSION}`;

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((nomi) => {
      return Promise.all(
        nomi
          .filter((nome) => nome.startsWith(CACHE_PREFIX) && nome !== CACHE_NAME)
          .map((nome) => {
            console.log(`[Cache] Eliminazione versione obsoleta: ${nome}`);
            return caches.delete(nome);
          })
      );
    })
  );
});
```

#### Gestione Quota di Storage

I browser impongono limiti sulla quantita di storage disponibile per ogni origine. La Storage Manager API permette di verificare lo spazio utilizzato e disponibile, fondamentale per evitare errori silenziosi di scrittura quando la quota e esaurita.

```javascript
async function verificaQuotaStorage() {
  if (!navigator.storage || !navigator.storage.estimate) {
    console.warn('StorageManager non supportato');
    return null;
  }

  const stima = await navigator.storage.estimate();
  const usato = stima.usage || 0;
  const quota = stima.quota || 0;
  const percentuale = ((usato / quota) * 100).toFixed(2);

  console.log(`Storage: ${(usato / 1024 / 1024).toFixed(1)} MB usati`);
  console.log(`Quota: ${(quota / 1024 / 1024).toFixed(1)} MB disponibili`);
  console.log(`Utilizzo: ${percentuale}%`);

  // Avvisa se lo storage supera l'80% della quota
  if (parseFloat(percentuale) > 80) {
    console.warn('[Storage] Quota quasi esaurita, avviare pulizia cache');
    await pulisciCacheVecchie();
  }

  return { usato, quota, percentuale: parseFloat(percentuale) };
}

// Richiedi storage persistente per evitare l'eviction automatica
async function richiediStoragePersistente() {
  if (navigator.storage && navigator.storage.persist) {
    const concesso = await navigator.storage.persist();
    console.log(`Storage persistente: ${concesso ? 'concesso' : 'negato'}`);
    return concesso;
  }
  return false;
}
```

#### Pattern Race: La Risposta Piu Veloce

Il pattern "race" (o "fastest") mette in competizione la cache e la rete, restituendo la prima risposta disponibile. E utile per risorse dove sia la velocita sia la freschezza contano, come le pagine di un sito editoriale.

```javascript
async function rispostaPiuVeloce(request) {
  const promessaCache = caches.match(request);
  const promessaRete = fetch(request).then((risposta) => {
    // Aggiorna la cache in background con la risposta dalla rete
    const clone = risposta.clone();
    caches.open('race-cache').then((cache) => cache.put(request, clone));
    return risposta;
  });

  // Restituisce la prima risposta che si risolve con successo
  return Promise.any([promessaCache, promessaRete]).catch(() => {
    return caches.match('/offline.html');
  });
}

self.addEventListener('fetch', (event) => {
  if (event.request.destination === 'document') {
    event.respondWith(rispostaPiuVeloce(event.request));
  }
});
```

#### Cache Condizionale per Header di Risposta

Non tutte le risposte devono essere cachate. Implementare il caching condizionale basato su header specifici (come `Cache-Control`, `Content-Type` o header personalizzati) consente un controllo granulare su cosa finisce nella cache.

```javascript
async function cacheCondizionale(request) {
  const risposta = await fetch(request);

  // Non cachare risposte con Cache-Control: no-store
  const cacheControl = risposta.headers.get('Cache-Control') || '';
  if (cacheControl.includes('no-store')) {
    return risposta;
  }

  // Non cachare risposte parziali o errori
  if (risposta.status !== 200) {
    return risposta;
  }

  // Non cachare risposte superiori a 5 MB
  const dimensione = parseInt(risposta.headers.get('Content-Length') || '0', 10);
  if (dimensione > 5 * 1024 * 1024) {
    return risposta;
  }

  // Risposta valida per il caching
  const cache = await caches.open('risposte-filtrate');
  await cache.put(request, risposta.clone());
  return risposta;
}
```

### IndexedDB per i Dati Strutturati

Mentre la Cache API e ottimale per le risorse HTTP, **IndexedDB** e il database NoSQL integrato nel browser ideale per memorizzare dati strutturati complessi, consentendo query avanzate e transazioni.

```javascript
class DatabaseLocale {
  constructor(nomeDb, versione = 1) {
    this.nomeDb = nomeDb;
    this.versione = versione;
    this.db = null;
  }

  async apri() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.nomeDb, this.versione);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Crea gli object store (tabelle)
        if (!db.objectStoreNames.contains('progetti')) {
          const store = db.createObjectStore('progetti', { keyPath: 'id' });
          store.createIndex('nome', 'nome', { unique: false });
          store.createIndex('dataCreazione', 'dataCreazione', { unique: false });
          store.createIndex('stato', 'stato', { unique: false });
        }

        if (!db.objectStoreNames.contains('sincronizzazione')) {
          db.createObjectStore('sincronizzazione', {
            keyPath: 'id',
            autoIncrement: true
          });
        }
      };

      request.onsuccess = (event) => {
        this.db = event.target.result;
        resolve(this.db);
      };

      request.onerror = (event) => {
        reject(event.target.error);
      };
    });
  }

  async inserisci(nomeStore, dati) {
    return new Promise((resolve, reject) => {
      const transazione = this.db.transaction(nomeStore, 'readwrite');
      const store = transazione.objectStore(nomeStore);
      const request = store.put(dati);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async leggi(nomeStore, chiave) {
    return new Promise((resolve, reject) => {
      const transazione = this.db.transaction(nomeStore, 'readonly');
      const store = transazione.objectStore(nomeStore);
      const request = store.get(chiave);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async leggiTutti(nomeStore) {
    return new Promise((resolve, reject) => {
      const transazione = this.db.transaction(nomeStore, 'readonly');
      const store = transazione.objectStore(nomeStore);
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async cercaPerIndice(nomeStore, nomeIndice, valore) {
    return new Promise((resolve, reject) => {
      const transazione = this.db.transaction(nomeStore, 'readonly');
      const store = transazione.objectStore(nomeStore);
      const indice = store.index(nomeIndice);
      const request = indice.getAll(valore);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async elimina(nomeStore, chiave) {
    return new Promise((resolve, reject) => {
      const transazione = this.db.transaction(nomeStore, 'readwrite');
      const store = transazione.objectStore(nomeStore);
      const request = store.delete(chiave);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}

// Utilizzo
const db = new DatabaseLocale('GestioneProgetti', 1);
await db.apri();
await db.inserisci('progetti', {
  id: 'prog-001',
  nome: 'Redesign Sito',
  stato: 'attivo',
  dataCreazione: new Date().toISOString()
});
const progettiAttivi = await db.cercaPerIndice('progetti', 'stato', 'attivo');
```

### IndexedDB Avanzato con Dexie.js

L'API nativa di IndexedDB e potente ma verbosa, basata su eventi e callback. **Dexie.js** (~5 KB minificato) e un wrapper che espone un'interfaccia Promise-based con query dichiarative, transazioni semplificate, migrazioni di schema versionato e operazioni bulk ottimizzate.

#### Schema Versionato e Migrazioni

Dexie gestisce le migrazioni di schema in modo incrementale: ogni chiamata a `version(n).stores()` definisce lo schema per quella versione, e le funzioni `upgrade()` migrano i dati esistenti.

```javascript
import Dexie from 'dexie';

const db = new Dexie('GestioneProgetti');

// Versione 1: schema iniziale
db.version(1).stores({
  progetti: 'id, nome, stato, dataCreazione',
  task: '++id, progettoId, titolo, completato'
});

// Versione 2: aggiunta campo priorita ai task
db.version(2).stores({
  progetti: 'id, nome, stato, dataCreazione',
  task: '++id, progettoId, titolo, completato, priorita'
}).upgrade((trans) => {
  return trans.table('task').toCollection().modify((task) => {
    task.priorita = task.priorita || 'media';
  });
});

// Versione 3: aggiunta tabella utenti con indice composto
db.version(3).stores({
  progetti: 'id, nome, stato, dataCreazione, [stato+dataCreazione]',
  task: '++id, progettoId, titolo, completato, priorita, assegnatoA',
  utenti: 'id, email, &username, ruolo'
});
```

#### Query Avanzate e Operazioni Bulk

Dexie supporta query complesse con filtri combinati, ordinamento, paginazione e operazioni bulk che sfruttano le ottimizzazioni interne di IndexedDB per inserimenti massivi senza ascoltare ogni singolo evento `onsuccess`.

```javascript
// Query con filtri combinati e paginazione
const taskUrgenti = await db.task
  .where('priorita').equals('alta')
  .and((task) => !task.completato)
  .sortBy('dataCreazione');

// Query su indice composto
const progettiRecenti = await db.progetti
  .where('[stato+dataCreazione]')
  .between(['attivo', '2026-01-01'], ['attivo', '2026-12-31'])
  .toArray();

// Paginazione con offset e limit
const pagina = await db.task
  .where('progettoId').equals('prog-001')
  .offset(20)
  .limit(10)
  .toArray();

// Operazioni bulk: inserimento massivo ottimizzato
const nuoviTask = Array.from({ length: 1000 }, (_, i) => ({
  progettoId: 'prog-001',
  titolo: `Task ${i + 1}`,
  completato: false,
  priorita: 'media'
}));
await db.task.bulkPut(nuoviTask);

// Aggiornamento bulk condizionale
await db.task
  .where('progettoId').equals('prog-vecchio')
  .modify({ progettoId: 'prog-nuovo' });
```

#### Transazioni Esplicite

Le transazioni garantiscono l'atomicita delle operazioni e prevengono race condition. In Dexie, ogni operazione singola e gia racchiusa in una transazione implicita, ma per operazioni multiple correlate conviene usare transazioni esplicite.

```javascript
// Transazione su piu tabelle: crea progetto con task iniziali
await db.transaction('rw', db.progetti, db.task, async () => {
  const idProgetto = 'prog-' + Date.now();

  await db.progetti.add({
    id: idProgetto,
    nome: 'Nuovo Progetto',
    stato: 'attivo',
    dataCreazione: new Date().toISOString()
  });

  await db.task.bulkAdd([
    { progettoId: idProgetto, titolo: 'Setup iniziale', completato: false, priorita: 'alta' },
    { progettoId: idProgetto, titolo: 'Configurazione CI', completato: false, priorita: 'media' },
    { progettoId: idProgetto, titolo: 'Documentazione', completato: false, priorita: 'bassa' }
  ]);

  // Se una qualsiasi operazione fallisce, tutte vengono annullate
});
```

### IndexedDB con idb

La libreria **idb** (~1.2 KB) offre un wrapper minimale che espone la stessa interfaccia di IndexedDB ma basata su Promise, senza aggiungere astrazioni aggiuntive. E la scelta ideale quando si vuole restare vicini all'API nativa con una sintassi piu pulita.

```javascript
import { openDB, deleteDB } from 'idb';

// Apertura del database con migrazioni
const db = await openDB('AppDB', 2, {
  upgrade(db, vecchiaVersione, nuovaVersione, transazione) {
    if (vecchiaVersione < 1) {
      const store = db.createObjectStore('note', { keyPath: 'id' });
      store.createIndex('data', 'dataCreazione');
      store.createIndex('categoria', 'categoria');
    }
    if (vecchiaVersione < 2) {
      const store = transazione.objectStore('note');
      store.createIndex('tag', 'tag', { multiEntry: true });
    }
  },
  blocked() {
    console.warn('Database bloccato da un\'altra scheda');
  },
  blocking() {
    // Un'altra scheda sta tentando di aggiornare il DB
    db.close();
  }
});

// Operazioni CRUD con idb
await db.put('note', {
  id: 'nota-001',
  titolo: 'Riunione progetto',
  contenuto: 'Discussione architettura...',
  dataCreazione: new Date().toISOString(),
  categoria: 'lavoro',
  tag: ['meeting', 'architettura', 'Q1']
});

// Lettura per indice
const notePerCategoria = await db.getAllFromIndex('note', 'categoria', 'lavoro');

// Lettura per indice multi-entry (tag)
const noteConTag = await db.getAllFromIndex('note', 'tag', 'architettura');

// Transazione esplicita
const tx = db.transaction('note', 'readwrite');
await Promise.all([
  tx.store.put({ id: 'nota-002', titolo: 'Altra nota', categoria: 'personale',
                  dataCreazione: new Date().toISOString(), tag: [] }),
  tx.store.delete('nota-vecchia'),
  tx.done
]);
```

#### Dexie.js vs idb: Quando Scegliere

| Criterio | Dexie.js | idb |
|---|---|---|
| **Dimensione** | ~5 KB min | ~1.2 KB min |
| **Query** | Ricche (where, and, sortBy, offset/limit) | Solo indici nativi IndexedDB |
| **Schema** | Versionamento dichiarativo con `upgrade()` | Manuale nell'handler `upgrade` |
| **Bulk** | `bulkPut`, `bulkAdd`, `bulkDelete` ottimizzati | Manuale con transazioni |
| **Live queries** | Si, con `liveQuery()` per React/Vue | No |
| **Caso d'uso** | App complesse con molte entita e relazioni | Caching semplice, pochi store |

### Background Sync

La **Background Sync API** consente di rinviare le azioni dell'utente finche non e disponibile una connessione stabile. Se l'utente compila un modulo offline, i dati vengono accodati e inviati automaticamente quando la rete torna disponibile.

```javascript
// Nella pagina principale: registra un evento di sincronizzazione
async function inviaModuloConSync(datiModulo) {
  const db = new DatabaseLocale('AppDB');
  await db.apri();

  // Salva i dati localmente
  await db.inserisci('sincronizzazione', {
    tipo: 'nuovo-progetto',
    dati: datiModulo,
    timestamp: Date.now()
  });

  // Registra la sincronizzazione in background
  const registration = await navigator.serviceWorker.ready;
  await registration.sync.register('sincronizza-progetti');
}

// Nel Service Worker: gestisci l'evento sync
self.addEventListener('sync', (event) => {
  if (event.tag === 'sincronizza-progetti') {
    event.waitUntil(sincronizzaDati());
  }
});

async function sincronizzaDati() {
  const db = await apriDatabase();
  const transazione = db.transaction('sincronizzazione', 'readwrite');
  const store = transazione.objectStore('sincronizzazione');
  const elementiDaSincronizzare = await store.getAll();

  for (const elemento of elementiDaSincronizzare) {
    try {
      await fetch('/api/progetti', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(elemento.dati)
      });
      // Rimuovi l'elemento sincronizzato con successo
      await store.delete(elemento.id);
    } catch (errore) {
      console.error('Sincronizzazione fallita, verra ritentata:', errore);
      throw errore; // Causa un nuovo tentativo
    }
  }
}
```

### Periodic Background Sync

La **Periodic Background Sync API** estende la Background Sync permettendo al Service Worker di eseguire sincronizzazioni periodiche in background, anche quando l'utente non sta interagendo con l'app. Questo consente di mantenere i contenuti aggiornati in modo proattivo, ad esempio pre-scaricando gli articoli di un feed RSS o aggiornando una dashboard.

```javascript
// Registrazione della sincronizzazione periodica dalla pagina
async function registraSyncPeriodica() {
  const registration = await navigator.serviceWorker.ready;

  // Verifica il supporto
  if (!('periodicSync' in registration)) {
    console.log('Periodic Background Sync non supportato');
    return;
  }

  // Verifica il permesso
  const stato = await navigator.permissions.query({ name: 'periodic-background-sync' });
  if (stato.state !== 'granted') {
    console.log('Permesso Periodic Sync negato');
    return;
  }

  await registration.periodicSync.register('aggiorna-contenuti', {
    minInterval: 12 * 60 * 60 * 1000, // Minimo ogni 12 ore
  });

  console.log('Sincronizzazione periodica registrata');
}

// Nel Service Worker: gestisci l'evento periodicsync
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'aggiorna-contenuti') {
    event.waitUntil(aggiornaContenutiInBackground());
  }
});

async function aggiornaContenutiInBackground() {
  try {
    const risposta = await fetch('/api/feed/ultimi');
    const articoli = await risposta.json();

    // Salva i nuovi articoli in IndexedDB
    const db = await apriDatabase();
    const tx = db.transaction('articoli', 'readwrite');
    for (const articolo of articoli) {
      await tx.objectStore('articoli').put(articolo);
    }

    // Pre-cache delle pagine degli articoli
    const cache = await caches.open('articoli-cache');
    for (const articolo of articoli.slice(0, 5)) {
      await cache.add(articolo.url);
    }
  } catch (errore) {
    console.error('[PeriodicSync] Aggiornamento fallito:', errore);
  }
}
```

### Architettura Offline-First

L'architettura **offline-first** inverte il paradigma tradizionale: invece di trattare l'offline come un caso eccezionale con un fallback, si progetta l'applicazione partendo dallo scenario senza connessione e si aggiungono le funzionalita online come miglioramento progressivo. L'utente non dovrebbe mai percepire l'assenza di rete come un blocco.

#### Principi Fondamentali

L'approccio offline-first si basa su quattro principi cardine:

**1. Local-first data**: tutti i dati vengono letti e scritti localmente (IndexedDB o Cache API). La rete e un canale di sincronizzazione, non la fonte primaria di verita durante l'interazione utente.

**2. Optimistic UI**: le azioni dell'utente aggiornano immediatamente l'interfaccia locale senza attendere la conferma dal server. Se il server rifiuta l'operazione successivamente, si esegue un rollback con feedback chiaro.

**3. Sync queue**: le operazioni di scrittura generate offline vengono accodate in una coda persistente (IndexedDB) e inviate al server quando la connessione torna disponibile, nell'ordine corretto.

**4. Conflict resolution**: quando piu dispositivi modificano lo stesso dato offline, servono strategie esplicite per risolvere i conflitti al momento della sincronizzazione.

#### Rilevamento dello Stato di Connessione

La proprieta `navigator.onLine` e gli eventi `online`/`offline` permettono di reagire ai cambiamenti di connettivita. Tuttavia, `navigator.onLine` indica solo la presenza di una connessione di rete, non la raggiungibilita effettiva del server: un WiFi captive portal risulta "online" anche senza accesso a Internet.

```javascript
class MonitorConnessione {
  constructor() {
    this.online = navigator.onLine;
    this.callback = new Set();

    window.addEventListener('online', () => this._aggiornaStato(true));
    window.addEventListener('offline', () => this._aggiornaStato(false));
  }

  _aggiornaStato(stato) {
    this.online = stato;
    this.callback.forEach((fn) => fn(stato));

    if (stato) {
      // Verifica la connettivita reale con un ping al server
      this._verificaConnettivita();
    }
  }

  async _verificaConnettivita() {
    try {
      const risposta = await fetch('/api/health', {
        method: 'HEAD',
        cache: 'no-store'
      });
      if (!risposta.ok) this._aggiornaStato(false);
    } catch {
      this._aggiornaStato(false);
    }
  }

  onCambioStato(fn) {
    this.callback.add(fn);
    return () => this.callback.delete(fn);
  }
}

// Utilizzo
const monitor = new MonitorConnessione();
monitor.onCambioStato((online) => {
  if (online) {
    mostraBanner('Connessione ripristinata. Sincronizzazione in corso...');
    avviaSincronizzazione();
  } else {
    mostraBanner('Modalita offline. Le modifiche verranno sincronizzate automaticamente.');
  }
});
```

#### Risoluzione dei Conflitti

Quando piu client modificano lo stesso record offline, la sincronizzazione genera conflitti. Le strategie principali sono:

**Last-Write-Wins (LWW)**: la modifica piu recente (basata su timestamp) sovrascrive le precedenti. Semplice da implementare, ma puo perdere dati silenziosamente.

```javascript
function risolviConflittoLWW(locale, remoto) {
  return locale.ultimaModifica > remoto.ultimaModifica ? locale : remoto;
}
```

**Merge field-level**: confronta i singoli campi e unisce le modifiche non conflittuali. Se lo stesso campo e stato modificato su entrambi i lati, si applica LWW a livello di campo o si richiede l'intervento dell'utente.

```javascript
function mergePerCampo(base, locale, remoto) {
  const risultato = { ...base };

  for (const campo of Object.keys(risultato)) {
    const modificatoLocale = locale[campo] !== base[campo];
    const modificatoRemoto = remoto[campo] !== base[campo];

    if (modificatoLocale && !modificatoRemoto) {
      risultato[campo] = locale[campo];
    } else if (!modificatoLocale && modificatoRemoto) {
      risultato[campo] = remoto[campo];
    } else if (modificatoLocale && modificatoRemoto) {
      // Entrambi modificati: usa il piu recente o chiedi all'utente
      if (locale[campo] !== remoto[campo]) {
        risultato[campo] = locale.ultimaModifica > remoto.ultimaModifica
          ? locale[campo]
          : remoto[campo];
        risultato._conflitti = risultato._conflitti || [];
        risultato._conflitti.push({ campo, locale: locale[campo], remoto: remoto[campo] });
      }
    }
  }

  return risultato;
}
```

**CRDT (Conflict-free Replicated Data Types)**: strutture dati progettate matematicamente per convergere allo stesso stato su tutti i nodi senza necessita di coordinamento. Adatte per editing collaborativo (contatori, set, testo). Librerie come **Yjs** e **Automerge** implementano CRDT pronti per la produzione.

#### Gestione della Quota di Storage

In un'architettura offline-first, lo storage locale e una risorsa critica. Implementare politiche di eviction e monitoraggio continuo previene errori silenziosi.

```javascript
async function gestisciQuotaOffline() {
  const stima = await navigator.storage.estimate();
  const percentualeUsata = (stima.usage / stima.quota) * 100;

  if (percentualeUsata > 90) {
    // Pulizia aggressiva: rimuovi dati vecchi
    await pulisciDatiObsoleti(30); // Rimuovi dati piu vecchi di 30 giorni
    await pulisciCachePesanti();
  } else if (percentualeUsata > 70) {
    // Pulizia conservativa: solo cache non critiche
    await pulisciCachePesanti();
  }

  // Richiedi storage persistente per i dati critici
  if (navigator.storage.persist) {
    const persistente = await navigator.storage.persist();
    if (!persistente) {
      console.warn('Storage non persistente: i dati potrebbero essere eliminati dal browser');
    }
  }
}
```

---

## Notifiche Push

### Push API e Notification API

Le **notifiche push** permettono di raggiungere gli utenti anche quando l'app non e aperta, inviando messaggi dal server al dispositivo tramite il Service Worker. Il processo coinvolge due API distinte:

- **Notification API**: gestisce la visualizzazione delle notifiche all'utente.
- **Push API**: gestisce la ricezione di messaggi push dal server.

```javascript
// Richiedi il permesso per le notifiche
async function richiediPermessoNotifiche() {
  const permesso = await Notification.requestPermission();

  if (permesso === 'granted') {
    console.log('Permesso notifiche concesso');
    await sottoscriviPush();
  } else if (permesso === 'denied') {
    console.log('Permesso notifiche negato');
  }
}

// Sottoscrivi le notifiche push
async function sottoscriviPush() {
  const registration = await navigator.serviceWorker.ready;

  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true, // Le notifiche devono essere visibili all'utente
    applicationServerKey: urlBase64ToUint8Array(CHIAVE_PUBBLICA_VAPID)
  });

  // Invia la sottoscrizione al server
  await fetch('/api/push/sottoscrivi', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subscription)
  });
}

// Funzione helper per convertire la chiave VAPID
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');
  const rawData = window.atob(base64);
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}
```

### Gestione delle Notifiche nel Service Worker

```javascript
// sw.js - Ricezione messaggi push
self.addEventListener('push', (event) => {
  let dati = { titolo: 'Notifica', corpo: 'Hai un nuovo messaggio' };

  if (event.data) {
    dati = event.data.json();
  }

  const opzioniNotifica = {
    body: dati.corpo,
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    image: dati.immagine || undefined,
    vibrate: [100, 50, 100],
    tag: dati.tag || 'notifica-generica', // Raggruppa notifiche simili
    renotify: true,
    requireInteraction: dati.importante || false,
    data: {
      url: dati.url || '/',
      idNotifica: dati.id
    },
    actions: [
      { action: 'apri', title: 'Apri', icon: '/icons/open.png' },
      { action: 'chiudi', title: 'Chiudi', icon: '/icons/close.png' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(dati.titolo, opzioniNotifica)
  );
});

// Gestione click sulla notifica
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'chiudi') return;

  const urlDestinazione = event.notification.data.url;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((listaClient) => {
        // Cerca se c'e gia una finestra aperta con quell'URL
        for (const client of listaClient) {
          if (client.url === urlDestinazione && 'focus' in client) {
            return client.focus();
          }
        }
        // Altrimenti apri una nuova finestra
        return clients.openWindow(urlDestinazione);
      })
  );
});
```

### Server-Side con web-push e Chiavi VAPID

Le chiavi **VAPID** (Voluntary Application Server Identification) autenticano il server presso il servizio push del browser. La libreria **web-push** semplifica l'invio di notifiche lato server.

```javascript
// server.js (Node.js)
const webpush = require('web-push');

// Genera le chiavi VAPID (da fare una sola volta)
// const vapidKeys = webpush.generateVAPIDKeys();

const VAPID_PUBLIC_KEY = 'BEl62iUYgUivxI...chiave-pubblica';
const VAPID_PRIVATE_KEY = 'UGXbX3Jg...chiave-privata';

webpush.setVapidDetails(
  'mailto:admin@miodominio.it',
  VAPID_PUBLIC_KEY,
  VAPID_PRIVATE_KEY
);

// Invia una notifica push
async function inviaNotificaPush(sottoscrizione, payload) {
  try {
    const risultato = await webpush.sendNotification(
      sottoscrizione,
      JSON.stringify({
        titolo: payload.titolo,
        corpo: payload.corpo,
        url: payload.url,
        tag: payload.tag,
        importante: payload.importante || false
      }),
      {
        TTL: 60 * 60, // Time To Live: 1 ora
        urgency: payload.importante ? 'high' : 'normal'
      }
    );
    console.log('Notifica inviata:', risultato.statusCode);
  } catch (errore) {
    if (errore.statusCode === 404 || errore.statusCode === 410) {
      // La sottoscrizione non e piu valida, rimuovila dal database
      await rimuoviSottoscrizione(sottoscrizione.endpoint);
    }
    console.error('Errore invio notifica:', errore);
  }
}
```

### VAPID: Approfondimento sul Protocollo

Il protocollo **VAPID** (Voluntary Application Server Identification, definito in RFC 8292) autentica il server applicativo presso il servizio push del browser, stabilendo una relazione di fiducia senza richiedere registrazioni o account specifici per ogni servizio push. Le chiavi VAPID sono una coppia asimmetrica basata su crittografia a curve ellittiche (ECDSA su curva P-256).

#### Come Funziona VAPID

Il flusso di autenticazione VAPID opera in tre fasi:

1. **Generazione delle chiavi**: il server genera una coppia di chiavi (pubblica e privata) una sola volta. La chiave pubblica viene condivisa con il client per la sottoscrizione, la chiave privata resta esclusivamente sul server.

2. **Sottoscrizione**: quando il client si sottoscrive alle notifiche push tramite `pushManager.subscribe()`, include la chiave pubblica VAPID come `applicationServerKey`. Il servizio push del browser associa questa chiave alla sottoscrizione.

3. **Invio della notifica**: quando il server invia una notifica, firma un JSON Web Token (JWT) con la chiave privata VAPID e lo include nell'header `Authorization` della richiesta POST al servizio push. Il servizio push verifica la firma usando la chiave pubblica associata alla sottoscrizione.

```javascript
// Generazione chiavi VAPID (da eseguire una sola volta)
const webpush = require('web-push');
const chiavi = webpush.generateVAPIDKeys();
console.log('Chiave pubblica:', chiavi.publicKey);
console.log('Chiave privata:', chiavi.privateKey);
// IMPORTANTE: salvare le chiavi in modo sicuro (variabili d'ambiente o secret manager)
// La chiave privata NON deve mai essere esposta al client o committata nel codice
```

#### Gestione Avanzata delle Sottoscrizioni

In produzione, la gestione delle sottoscrizioni richiede un sistema robusto di storage, pulizia e rispetto della privacy dell'utente.

```javascript
// Server: gestione completa delle sottoscrizioni
const express = require('express');
const webpush = require('web-push');
const router = express.Router();

webpush.setVapidDetails(
  'mailto:admin@miodominio.it',
  process.env.VAPID_PUBLIC_KEY,
  process.env.VAPID_PRIVATE_KEY
);

// Salva la sottoscrizione con metadati utili
router.post('/api/push/sottoscrivi', async (req, res) => {
  const { subscription, preferenze } = req.body;

  // Verifica la validita della sottoscrizione
  if (!subscription?.endpoint || !subscription?.keys?.p256dh || !subscription?.keys?.auth) {
    return res.status(400).json({ errore: 'Sottoscrizione non valida' });
  }

  await salvaSottoscrizione({
    endpoint: subscription.endpoint,
    chiavi: subscription.keys,
    preferenze: preferenze || { urgenti: true, aggiornamenti: true },
    dataCreazione: new Date().toISOString(),
    ultimoUtilizzo: new Date().toISOString()
  });

  res.json({ successo: true });
});

// Invio massivo con gestione errori e pulizia
async function inviaNotificaMassiva(payload, filtro) {
  const sottoscrizioni = await ottieniSottoscrizioni(filtro);
  const risultati = { inviate: 0, fallite: 0, rimosse: 0 };

  const promesse = sottoscrizioni.map(async (sub) => {
    try {
      await webpush.sendNotification(
        { endpoint: sub.endpoint, keys: sub.chiavi },
        JSON.stringify(payload),
        { TTL: 3600, urgency: payload.urgenza || 'normal' }
      );
      risultati.inviate++;
      await aggiornUltimoUtilizzo(sub.endpoint);
    } catch (errore) {
      risultati.fallite++;
      if (errore.statusCode === 404 || errore.statusCode === 410) {
        // Sottoscrizione scaduta o revocata: rimuovi dal database
        await rimuoviSottoscrizione(sub.endpoint);
        risultati.rimosse++;
      }
    }
  });

  // Limita la concorrenza per non sovraccaricare il servizio push
  const BATCH_SIZE = 50;
  for (let i = 0; i < promesse.length; i += BATCH_SIZE) {
    await Promise.allSettled(promesse.slice(i, i + BATCH_SIZE));
  }

  return risultati;
}
```

#### Best Practice per le Notifiche Push

La gestione delle notifiche push richiede attenzione sia tecnica sia di esperienza utente:

**Timing della richiesta di permesso**: non richiedere mai il permesso al primo caricamento della pagina. L'utente non ha ancora compreso il valore dell'app e rifiutera con alta probabilita. Mostra prima un prompt personalizzato (non quello nativo del browser) che spiega cosa ricevera, e solo dopo il consenso attiva la richiesta nativa.

**Frequenza e rilevanza**: ogni notifica deve offrire valore reale all'utente. Una frequenza eccessiva porta alla revoca del permesso o, peggio, alla disinstallazione della PWA. Implementa preferenze granulari (tipo di notifica, orari, frequenza) e rispettale rigorosamente.

**Payload minimale**: il payload della notifica push e limitato (tipicamente 4 KB) e transita attraverso il servizio push del browser. Non includere mai dati sensibili (PII, token, credenziali) nel payload. Invia solo un identificativo e scarica i dettagli completi dal server quando la notifica viene visualizzata.

**Gestione delle sottoscrizioni scadute**: le sottoscrizioni push possono scadere o essere revocate dall'utente in qualsiasi momento. Gestisci sempre le risposte 404 (sottoscrizione non trovata) e 410 (sottoscrizione scaduta) dal servizio push rimuovendo immediatamente la sottoscrizione dal database.

---

## Web Components

### Panoramica

I **Web Components** sono un insieme di standard web nativi che permettono di creare componenti riutilizzabili e incapsulati senza dipendere da framework esterni. I tre pilastri tecnologici sono:

### Custom Elements

I **Custom Elements** permettono di definire nuovi tag HTML con comportamento personalizzato:

```javascript
class CardProgetto extends HTMLElement {
  // Attributi osservati per il reactive rendering
  static get observedAttributes() {
    return ['titolo', 'stato', 'priorita'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    // Chiamato quando l'elemento viene inserito nel DOM
    this.render();
  }

  disconnectedCallback() {
    // Chiamato quando l'elemento viene rimosso dal DOM
    // Pulizia event listener, timer, ecc.
  }

  attributeChangedCallback(nome, vecchioValore, nuovoValore) {
    if (vecchioValore !== nuovoValore) {
      this.render();
    }
  }

  render() {
    const titolo = this.getAttribute('titolo') || 'Senza titolo';
    const stato = this.getAttribute('stato') || 'in-attesa';
    const priorita = this.getAttribute('priorita') || 'media';

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 16px;
          margin: 8px 0;
          font-family: system-ui, sans-serif;
        }
        :host([priorita="alta"]) {
          border-left: 4px solid #d32f2f;
        }
        .titolo { font-size: 1.2em; font-weight: 600; }
        .badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.85em;
          background: ${stato === 'completato' ? '#c8e6c9' : '#fff9c4'};
          color: ${stato === 'completato' ? '#2e7d32' : '#f57f17'};
        }
        ::slotted(p) { color: #555; }
      </style>
      <div class="titolo">${titolo}</div>
      <span class="badge">${stato}</span>
      <slot></slot>
    `;
  }
}

customElements.define('card-progetto', CardProgetto);
```

Utilizzo in HTML:

```html
<card-progetto titolo="Redesign Homepage" stato="in-corso" priorita="alta">
  <p>Ridisegnare l'interfaccia utente della homepage principale.</p>
</card-progetto>
```

### Shadow DOM

Lo **Shadow DOM** crea un albero DOM incapsulato, isolando gli stili e la struttura del componente dal resto della pagina. Gli stili definiti all'interno del Shadow DOM non influenzano il documento esterno e viceversa. Lo pseudo-selettore `:host` seleziona l'elemento radice del componente, mentre `::slotted()` permette di stilizzare il contenuto proiettato tramite gli slot.

### HTML Templates

I **template HTML** definiscono frammenti di markup riutilizzabili che non vengono renderizzati finche non sono esplicitamente clonati e inseriti nel DOM:

```html
<template id="template-lista-task">
  <style>
    .task-item { display: flex; align-items: center; padding: 8px; }
    .task-item.completato .testo { text-decoration: line-through; color: #999; }
  </style>
  <div class="task-item">
    <input type="checkbox" class="checkbox">
    <span class="testo"><slot name="testo-task"></slot></span>
  </div>
</template>

<script>
class TaskItem extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    const template = document.getElementById('template-lista-task');
    shadow.appendChild(template.content.cloneNode(true));

    shadow.querySelector('.checkbox').addEventListener('change', (e) => {
      const item = shadow.querySelector('.task-item');
      item.classList.toggle('completato', e.target.checked);
      this.dispatchEvent(new CustomEvent('task-toggle', {
        bubbles: true,
        composed: true, // Attraversa il confine del Shadow DOM
        detail: { completato: e.target.checked }
      }));
    });
  }
}
customElements.define('task-item', TaskItem);
</script>
```

### Lit: Framework per Web Components

**Lit** e un framework leggero (circa 5 KB) sviluppato da Google che semplifica la creazione di Web Components con template dichiarativi e reactive properties:

```javascript
import { LitElement, html, css } from 'lit';

class PannelloDashboard extends LitElement {
  static properties = {
    titolo: { type: String },
    elementi: { type: Array },
    caricamento: { type: Boolean, state: true } // state: proprietà interna
  };

  static styles = css`
    :host {
      display: block;
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 20px;
    }
    h2 { margin-top: 0; color: #1a1a1a; }
    .lista { list-style: none; padding: 0; }
    .lista li {
      padding: 12px;
      border-bottom: 1px solid #f0f0f0;
      transition: background 0.2s;
    }
    .lista li:hover { background: #f5f5f5; }
    .skeleton { background: #e0e0e0; border-radius: 4px; height: 20px;
                animation: pulse 1.5s infinite; }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `;

  constructor() {
    super();
    this.titolo = '';
    this.elementi = [];
    this.caricamento = false;
  }

  render() {
    return html`
      <h2>${this.titolo}</h2>
      ${this.caricamento
        ? html`<div class="skeleton"></div>`
        : html`
          <ul class="lista">
            ${this.elementi.map((el) => html`
              <li @click=${() => this._gestisciClick(el)}>
                ${el.nome}
              </li>
            `)}
          </ul>
        `
      }
    `;
  }

  _gestisciClick(elemento) {
    this.dispatchEvent(new CustomEvent('elemento-selezionato', {
      detail: elemento,
      bubbles: true,
      composed: true
    }));
  }
}

customElements.define('pannello-dashboard', PannelloDashboard);
```

---

## WebAssembly

### Concetto

**WebAssembly** (Wasm) e un formato binario di istruzioni a basso livello progettato come target di compilazione per linguaggi come C, C++, Rust e altri. Eseguito in una sandbox sicura all'interno del browser, offre prestazioni vicine al codice nativo mantenendo la portabilita e la sicurezza del web.

WebAssembly non sostituisce JavaScript, ma lo complementa: i moduli Wasm possono essere richiamati da JavaScript e viceversa. I casi d'uso ideali includono:

- **Elaborazione intensiva**: algoritmi crittografici, compressione dati, calcolo scientifico.
- **Gaming**: motori di gioco, fisica, rendering 3D.
- **Elaborazione multimediale**: editing audio/video, filtri immagini, codifica.
- **CAD e modellazione**: applicazioni di progettazione che richiedono calcoli geometrici complessi.
- **Machine learning**: inferenza di modelli direttamente nel browser.

### Compilazione da Rust con wasm-pack

**Rust** e uno dei linguaggi piu adatti per WebAssembly grazie alle sue garanzie di sicurezza della memoria e alle prestazioni elevate. Lo strumento **wasm-pack** automatizza il processo di compilazione e packaging.

```rust
// src/lib.rs
use wasm_bindgen::prelude::*;
use web_sys::console;

// Funzione esportata verso JavaScript
#[wasm_bindgen]
pub fn calcola_fibonacci(n: u32) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    let mut a: u64 = 0;
    let mut b: u64 = 1;
    for _ in 2..=n {
        let temp = a + b;
        a = b;
        b = temp;
    }
    b
}

#[wasm_bindgen]
pub struct ElaboratoreImmagini {
    larghezza: u32,
    altezza: u32,
    pixel: Vec<u8>,
}

#[wasm_bindgen]
impl ElaboratoreImmagini {
    #[wasm_bindgen(constructor)]
    pub fn new(larghezza: u32, altezza: u32) -> Self {
        Self {
            larghezza,
            altezza,
            pixel: vec![0; (larghezza * altezza * 4) as usize],
        }
    }

    pub fn applica_scala_di_grigi(&mut self) {
        for i in (0..self.pixel.len()).step_by(4) {
            let grigio = (0.299 * self.pixel[i] as f64
                + 0.587 * self.pixel[i + 1] as f64
                + 0.114 * self.pixel[i + 2] as f64) as u8;
            self.pixel[i] = grigio;
            self.pixel[i + 1] = grigio;
            self.pixel[i + 2] = grigio;
        }
    }

    pub fn pixel_ptr(&self) -> *const u8 {
        self.pixel.as_ptr()
    }
}
```

Compilazione e utilizzo in JavaScript:

```bash
# Installa wasm-pack
cargo install wasm-pack

# Compila il progetto Rust in un modulo Wasm
wasm-pack build --target web
```

```javascript
// Caricamento e utilizzo del modulo Wasm
import init, { calcola_fibonacci, ElaboratoreImmagini } from './pkg/mio_modulo.js';

async function avvia() {
  await init(); // Inizializza il modulo WebAssembly

  // Calcolo ad alte prestazioni
  console.time('fibonacci-wasm');
  const risultato = calcola_fibonacci(50);
  console.timeEnd('fibonacci-wasm');
  console.log(`Fibonacci(50) = ${risultato}`);

  // Elaborazione immagini
  const elaboratore = new ElaboratoreImmagini(1920, 1080);
  elaboratore.applica_scala_di_grigi();
}

avvia();
```

Per compilare da **C/C++**, si utilizza **Emscripten**:

```bash
# Compila un file C in WebAssembly
emcc algoritmo.c -o algoritmo.js -s WASM=1 -s EXPORTED_FUNCTIONS='["_calcola"]' -O3
```

---

## Web API Moderne

### Fetch API con Streams

La **Fetch API** supporta gli stream per gestire risposte di grandi dimensioni in modo incrementale, senza caricare tutto in memoria:

```javascript
async function scaricaConProgresso(url, callbackProgresso) {
  const response = await fetch(url);

  if (!response.ok) throw new Error(`Errore HTTP: ${response.status}`);

  const dimensioneTotale = parseInt(response.headers.get('Content-Length'), 10);
  let dimensioneRicevuta = 0;
  const chunks = [];

  const reader = response.body.getReader();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    chunks.push(value);
    dimensioneRicevuta += value.length;

    if (callbackProgresso && dimensioneTotale) {
      callbackProgresso({
        ricevuti: dimensioneRicevuta,
        totale: dimensioneTotale,
        percentuale: Math.round((dimensioneRicevuta / dimensioneTotale) * 100)
      });
    }
  }

  // Combina i chunk in un unico Uint8Array
  const datiCompleti = new Uint8Array(dimensioneRicevuta);
  let posizione = 0;
  for (const chunk of chunks) {
    datiCompleti.set(chunk, posizione);
    posizione += chunk.length;
  }

  return datiCompleti;
}

// Utilizzo
scaricaConProgresso('/api/export/dati.zip', (progresso) => {
  console.log(`Scaricamento: ${progresso.percentuale}%`);
});
```

### File System Access API

La **File System Access API** permette alle applicazioni web di leggere e scrivere file direttamente nel file system dell'utente, con il suo esplicito consenso:

```javascript
// Apri un file dal file system
async function apriFile() {
  const [handle] = await window.showOpenFilePicker({
    types: [
      {
        description: 'Documenti di testo',
        accept: { 'text/plain': ['.txt', '.md'] }
      },
      {
        description: 'File JSON',
        accept: { 'application/json': ['.json'] }
      }
    ],
    multiple: false
  });

  const file = await handle.getFile();
  const contenuto = await file.text();
  return { handle, contenuto };
}

// Salva un file nel file system
async function salvaFile(handle, contenuto) {
  if (!handle) {
    handle = await window.showSaveFilePicker({
      suggestedName: 'documento.txt',
      types: [
        { description: 'Testo', accept: { 'text/plain': ['.txt'] } }
      ]
    });
  }

  const writable = await handle.createWritable();
  await writable.write(contenuto);
  await writable.close();
  return handle;
}
```

### Web Share API

La **Web Share API** consente di condividere contenuti utilizzando il meccanismo nativo di condivisione del sistema operativo:

```javascript
async function condividiContenuto(dati) {
  if (!navigator.share) {
    // Fallback per browser non supportati
    await navigator.clipboard.writeText(dati.url);
    mostraMessaggio('Link copiato negli appunti');
    return;
  }

  try {
    await navigator.share({
      title: dati.titolo,
      text: dati.descrizione,
      url: dati.url,
      // files: [file] // Supportato su alcune piattaforme
    });
    console.log('Contenuto condiviso con successo');
  } catch (errore) {
    if (errore.name !== 'AbortError') {
      console.error('Errore nella condivisione:', errore);
    }
  }
}
```

### Payment Request API

La **Payment Request API** standardizza il processo di pagamento, riducendo la frizione nell'inserimento dei dati di pagamento:

```javascript
async function avviaPagamento(dettagliOrdine) {
  const metodiPagamento = [
    {
      supportedMethods: 'https://google.com/pay',
      data: {
        environment: 'PRODUCTION',
        merchantInfo: { merchantName: 'Il Mio Negozio' },
        allowedPaymentMethods: [{
          type: 'CARD',
          parameters: {
            allowedAuthMethods: ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
            allowedCardNetworks: ['VISA', 'MASTERCARD']
          }
        }]
      }
    },
    { supportedMethods: 'basic-card' }
  ];

  const dettagli = {
    displayItems: dettagliOrdine.articoli.map((a) => ({
      label: a.nome,
      amount: { currency: 'EUR', value: a.prezzo.toFixed(2) }
    })),
    total: {
      label: 'Totale',
      amount: { currency: 'EUR', value: dettagliOrdine.totale.toFixed(2) }
    }
  };

  const request = new PaymentRequest(metodiPagamento, dettagli);
  const response = await request.show();

  // Elabora il pagamento sul server
  const risultato = await fetch('/api/pagamento', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(response.toJSON())
  });

  if (risultato.ok) {
    await response.complete('success');
  } else {
    await response.complete('fail');
  }
}
```

### Web Bluetooth e Web USB

Queste API permettono alle applicazioni web di comunicare con dispositivi hardware:

```javascript
// Web Bluetooth: connessione a un sensore di frequenza cardiaca
async function connettiSensoreCardiaco() {
  const dispositivo = await navigator.bluetooth.requestDevice({
    filters: [{ services: ['heart_rate'] }]
  });

  const server = await dispositivo.gatt.connect();
  const servizio = await server.getPrimaryService('heart_rate');
  const caratteristica = await servizio.getCharacteristic('heart_rate_measurement');

  caratteristica.addEventListener('characteristicvaluechanged', (event) => {
    const valore = event.target.value;
    const frequenza = valore.getUint8(1);
    console.log(`Frequenza cardiaca: ${frequenza} bpm`);
  });

  await caratteristica.startNotifications();
}

// Web USB: comunicazione con un dispositivo USB
async function connettiDispositivoUSB() {
  const dispositivo = await navigator.usb.requestDevice({
    filters: [{ vendorId: 0x1234 }]
  });

  await dispositivo.open();
  await dispositivo.selectConfiguration(1);
  await dispositivo.claimInterface(0);

  // Invio dati al dispositivo
  const dati = new Uint8Array([0x01, 0x02, 0x03]);
  await dispositivo.transferOut(1, dati);

  // Ricezione dati dal dispositivo
  const risultato = await dispositivo.transferIn(1, 64);
  console.log('Dati ricevuti:', new Uint8Array(risultato.data.buffer));
}
```

### Web Serial API

La **Web Serial API** permette alle applicazioni web di comunicare con dispositivi seriali come Arduino, microcontrollori, stampanti 3D, lettori RFID e altri hardware che espongono una porta seriale. A differenza di Web USB che lavora a livello di protocollo USB, Web Serial opera sullo stream seriale (RS-232 / UART), rendendo l'integrazione piu semplice per dispositivi che comunicano tramite testo o protocolli seriali.

La Web Serial API e disponibile solo su browser Chromium (Chrome, Edge) e richiede un contesto sicuro (HTTPS). Come Web Bluetooth e Web USB, richiede un gesto utente esplicito per la selezione del dispositivo tramite un dialog di permesso nativo.

```javascript
// Connessione a un dispositivo seriale (es. Arduino)
async function connettiSeriale() {
  // Richiedi la selezione del dispositivo all'utente
  const porta = await navigator.serial.requestPort({
    filters: [
      { usbVendorId: 0x2341 } // Arduino
    ]
  });

  // Apri la porta con i parametri di comunicazione
  await porta.open({
    baudRate: 9600,
    dataBits: 8,
    stopBits: 1,
    parity: 'none',
    flowControl: 'none'
  });

  return porta;
}

// Lettura dati dal dispositivo con stream
async function leggiDaSeriale(porta) {
  const decoder = new TextDecoderStream();
  const inputStream = porta.readable.pipeThrough(decoder);
  const reader = inputStream.getReader();

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      console.log('[Seriale] Ricevuto:', value);
      elaboraDatiSensore(value);
    }
  } catch (errore) {
    console.error('[Seriale] Errore lettura:', errore);
  } finally {
    reader.releaseLock();
  }
}

// Invio comandi al dispositivo
async function inviaComandoSeriale(porta, comando) {
  const encoder = new TextEncoderStream();
  const outputStream = encoder.readable.pipeTo(porta.writable);
  const writer = encoder.writable.getWriter();

  await writer.write(comando + '\n');
  writer.releaseLock();
}

// Invio dati binari al dispositivo
async function inviaBinarioSeriale(porta, dati) {
  const writer = porta.writable.getWriter();
  await writer.write(new Uint8Array(dati));
  writer.releaseLock();
}

// Gestione del ciclo di vita della connessione
navigator.serial.addEventListener('connect', (event) => {
  console.log('[Seriale] Dispositivo connesso:', event.target);
});

navigator.serial.addEventListener('disconnect', (event) => {
  console.log('[Seriale] Dispositivo disconnesso:', event.target);
  aggiornaInterfaccia('disconnesso');
});
```

Esempio di interazione con Arduino per il controllo di un LED:

```javascript
// Esempio completo: controllo LED Arduino via Web Serial
async function controllaLedArduino() {
  const porta = await connettiSeriale();

  // Accendi il LED
  await inviaComandoSeriale(porta, '1');

  // Attendi 2 secondi
  await new Promise((r) => setTimeout(r, 2000));

  // Spegni il LED
  await inviaComandoSeriale(porta, '0');

  // Chiudi la connessione
  await porta.close();
}
```

### Credential Management API

La **Credential Management API** semplifica l'autenticazione salvando e recuperando credenziali in modo sicuro:

```javascript
// Salva le credenziali dopo un login riuscito
async function salvaCredenziali(username, password) {
  if (!navigator.credentials) return;

  const credenziale = new PasswordCredential({
    id: username,
    password: password,
    name: username
  });

  await navigator.credentials.store(credenziale);
}

// Recupera le credenziali salvate per il login automatico
async function loginAutomatico() {
  if (!navigator.credentials) return null;

  const credenziale = await navigator.credentials.get({
    password: true,
    mediation: 'optional' // 'silent', 'optional', 'required'
  });

  if (credenziale) {
    // Effettua il login con le credenziali recuperate
    const risposta = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: credenziale.id,
        password: credenziale.password
      })
    });
    return risposta.json();
  }

  return null;
}
```

---

## Architettura Micro-Frontend

### Concetto

I **micro-frontend** estendono il concetto dei microservizi al frontend: l'applicazione viene suddivisa in parti piu piccole e indipendenti, ciascuna sviluppata, testata e distribuita autonomamente da team diversi, potenzialmente con tecnologie diverse.

I vantaggi principali sono: autonomia dei team, deploy indipendente, scalabilita organizzativa, possibilita di adottare gradualmente nuove tecnologie senza riscrivere l'intera applicazione.

### Module Federation (Webpack 5)

**Module Federation** e una funzionalita di Webpack 5 che permette a piu build separate di condividere moduli a runtime, senza dover creare un bundle monolitico:

```javascript
// webpack.config.js - App Host (Container)
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'host',
      remotes: {
        dashboard: 'dashboard@http://localhost:3001/remoteEntry.js',
        profilo: 'profilo@http://localhost:3002/remoteEntry.js',
        impostazioni: 'impostazioni@http://localhost:3003/remoteEntry.js'
      },
      shared: {
        react: { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' }
      }
    })
  ]
};

// webpack.config.js - App Remota (Dashboard)
module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'dashboard',
      filename: 'remoteEntry.js',
      exposes: {
        './DashboardApp': './src/DashboardApp'
      },
      shared: {
        react: { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' }
      }
    })
  ]
};
```

```jsx
// Host: caricamento dinamico del micro-frontend
const DashboardRemoto = React.lazy(() => import('dashboard/DashboardApp'));

function App() {
  return (
    <div>
      <Navigazione />
      <React.Suspense fallback={<Spinner />}>
        <Routes>
          <Route path="/dashboard/*" element={<DashboardRemoto />} />
          {/* Altri micro-frontend */}
        </Routes>
      </React.Suspense>
    </div>
  );
}
```

### single-spa

**single-spa** e un framework specificamente progettato per orchestrare micro-frontend, permettendo a piu framework (React, Vue, Angular) di coesistere nella stessa pagina:

```javascript
// root-config.js
import { registerApplication, start } from 'single-spa';

registerApplication({
  name: '@miaorg/navbar',
  app: () => System.import('@miaorg/navbar'),
  activeWhen: '/'  // Sempre attivo
});

registerApplication({
  name: '@miaorg/dashboard',
  app: () => System.import('@miaorg/dashboard'),
  activeWhen: '/dashboard'
});

registerApplication({
  name: '@miaorg/profilo',
  app: () => System.import('@miaorg/profilo'),
  activeWhen: '/profilo',
  customProps: {
    apiBaseUrl: 'https://api.miodominio.it'
  }
});

start(); // Avvia il routing
```

### Approccio con iframe

L'approccio basato su **iframe** e il metodo di integrazione piu semplice e offre un isolamento completo tra i micro-frontend, ma presenta limitazioni significative:

```html
<!-- Integrazione tramite iframe -->
<div id="app-container">
  <nav id="navigazione-principale"><!-- ... --></nav>
  <main>
    <iframe
      id="micro-frontend-frame"
      src="https://dashboard.miodominio.it"
      sandbox="allow-scripts allow-same-origin allow-forms"
      loading="lazy"
      title="Dashboard"
      style="width: 100%; height: 100vh; border: none;">
    </iframe>
  </main>
</div>

<script>
// Comunicazione tra iframe tramite postMessage
window.addEventListener('message', (event) => {
  if (event.origin !== 'https://dashboard.miodominio.it') return;

  const { tipo, payload } = event.data;
  switch (tipo) {
    case 'NAVIGAZIONE':
      aggiornaURL(payload.percorso);
      break;
    case 'NOTIFICA':
      mostraNotifica(payload.messaggio);
      break;
  }
});

// Invia dati all'iframe
function inviaAlMicroFrontend(dati) {
  const frame = document.getElementById('micro-frontend-frame');
  frame.contentWindow.postMessage(dati, 'https://dashboard.miodominio.it');
}
</script>
```

Gli svantaggi degli iframe includono: problemi di performance (ogni iframe e un contesto di navigazione separato), difficolta nel responsive design, complessita nella comunicazione, impossibilita di condividere stili globali, e problemi con l'accessibilita.

### Approccio con Web Components

I **Web Components** offrono un approccio elegante ai micro-frontend grazie al loro incapsulamento nativo:

```javascript
// Micro-frontend come Web Component
class MicroFrontendDashboard extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.caricaApp();
  }

  async caricaApp() {
    // Carica dinamicamente le risorse del micro-frontend
    const modulo = await import('https://cdn.miodominio.it/dashboard/bundle.js');
    modulo.mount(this.shadowRoot, {
      basePath: '/dashboard',
      onNavigate: (percorso) => {
        this.dispatchEvent(new CustomEvent('naviga', {
          detail: { percorso },
          bubbles: true,
          composed: true
        }));
      }
    });
  }

  disconnectedCallback() {
    // Smonta l'applicazione per evitare memory leak
    if (this._smonta) this._smonta();
  }
}

customElements.define('mf-dashboard', MicroFrontendDashboard);
```

```html
<!-- Utilizzo nell'app host -->
<mf-dashboard></mf-dashboard>
```

---

## Server-Sent Events vs WebSocket

### Confronto

Le **comunicazioni in tempo reale** sul web possono essere implementate con due tecnologie principali: **Server-Sent Events (SSE)** e **WebSocket**. Ciascuna ha caratteristiche e casi d'uso distinti.

| Caratteristica | Server-Sent Events | WebSocket |
|---|---|---|
| **Direzione** | Unidirezionale (server verso client) | Bidirezionale |
| **Protocollo** | HTTP/HTTPS standard | Protocollo ws:// / wss:// dedicato |
| **Riconnessione** | Automatica (integrata nel browser) | Manuale (da implementare) |
| **Formato dati** | Solo testo (UTF-8) | Testo e binario |
| **Compatibilita proxy/firewall** | Eccellente (e HTTP standard) | Possibili problemi con proxy aziendali |
| **Overhead** | Basso (una connessione HTTP aperta) | Minimo dopo l'handshake iniziale |
| **Scalabilita** | Buona con HTTP/2 multiplexing | Richiede gestione esplicita delle connessioni |
| **Complessita server** | Semplice (qualsiasi server HTTP) | Richiede supporto WebSocket specifico |

### Server-Sent Events: Implementazione

SSE e la scelta ideale quando il server deve inviare aggiornamenti al client senza necessita di comunicazione inversa: feed di notizie, dashboard in tempo reale, notifiche, aggiornamenti di stato.

```javascript
// Server Node.js con SSE
const express = require('express');
const app = express();

app.get('/api/eventi', (req, res) => {
  // Imposta gli header per SSE
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Access-Control-Allow-Origin': '*'
  });

  // Invia un commento per mantenere viva la connessione
  const keepAlive = setInterval(() => {
    res.write(':heartbeat\n\n');
  }, 30000);

  // Invia eventi al client
  function inviaEvento(tipo, dati) {
    res.write(`event: ${tipo}\n`);
    res.write(`data: ${JSON.stringify(dati)}\n`);
    res.write(`id: ${Date.now()}\n\n`);
  }

  // Esempio: invia aggiornamenti periodici
  const intervallo = setInterval(() => {
    inviaEvento('aggiornamento', {
      timestamp: new Date().toISOString(),
      valore: Math.random() * 100
    });
  }, 5000);

  // Pulizia alla disconnessione del client
  req.on('close', () => {
    clearInterval(intervallo);
    clearInterval(keepAlive);
    res.end();
  });
});
```

```javascript
// Client con EventSource
const sorgente = new EventSource('/api/eventi');

// Evento generico (senza tipo specifico)
sorgente.onmessage = (event) => {
  console.log('Messaggio:', JSON.parse(event.data));
};

// Eventi con tipo specifico
sorgente.addEventListener('aggiornamento', (event) => {
  const dati = JSON.parse(event.data);
  aggiornaDashboard(dati);
});

sorgente.addEventListener('notifica', (event) => {
  const dati = JSON.parse(event.data);
  mostraNotifica(dati);
});

// Gestione errori e riconnessione
sorgente.onerror = (event) => {
  if (sorgente.readyState === EventSource.CLOSED) {
    console.log('Connessione SSE chiusa dal server');
  } else {
    console.log('Errore SSE, riconnessione automatica in corso...');
  }
};
```

### WebSocket: Implementazione

WebSocket e la scelta ideale per comunicazione bidirezionale in tempo reale: chat, giochi multiplayer, editing collaborativo, trading finanziario.

```javascript
// Server WebSocket con ws (Node.js)
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

const clientConnessi = new Map();

wss.on('connection', (ws, req) => {
  const idClient = generaId();
  clientConnessi.set(idClient, ws);
  console.log(`Client connesso: ${idClient}`);

  // Gestione messaggi ricevuti
  ws.on('message', (messaggio) => {
    const dati = JSON.parse(messaggio);

    switch (dati.tipo) {
      case 'chat':
        // Broadcast a tutti i client tranne il mittente
        clientConnessi.forEach((client, id) => {
          if (id !== idClient && client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({
              tipo: 'chat',
              mittente: idClient,
              testo: dati.testo,
              timestamp: Date.now()
            }));
          }
        });
        break;

      case 'ping':
        ws.send(JSON.stringify({ tipo: 'pong' }));
        break;
    }
  });

  ws.on('close', () => {
    clientConnessi.delete(idClient);
    console.log(`Client disconnesso: ${idClient}`);
  });

  ws.on('error', (errore) => {
    console.error(`Errore WebSocket per ${idClient}:`, errore);
  });
});
```

```javascript
// Client WebSocket con riconnessione automatica
class WebSocketManager {
  constructor(url, opzioni = {}) {
    this.url = url;
    this.tentativi = 0;
    this.maxTentativi = opzioni.maxTentativi || 10;
    this.ritardoBase = opzioni.ritardoBase || 1000;
    this.gestori = new Map();
    this.connetti();
  }

  connetti() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connesso');
      this.tentativi = 0; // Reset dei tentativi al successo
    };

    this.ws.onmessage = (event) => {
      const dati = JSON.parse(event.data);
      const gestori = this.gestori.get(dati.tipo) || [];
      gestori.forEach((gestore) => gestore(dati));
    };

    this.ws.onclose = (event) => {
      if (!event.wasClean && this.tentativi < this.maxTentativi) {
        // Riconnessione con backoff esponenziale
        const ritardo = this.ritardoBase * Math.pow(2, this.tentativi);
        console.log(`Riconnessione tra ${ritardo}ms...`);
        setTimeout(() => {
          this.tentativi++;
          this.connetti();
        }, ritardo);
      }
    };
  }

  on(tipo, gestore) {
    if (!this.gestori.has(tipo)) {
      this.gestori.set(tipo, []);
    }
    this.gestori.get(tipo).push(gestore);
  }

  invia(tipo, dati) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ tipo, ...dati }));
    }
  }

  disconnetti() {
    this.maxTentativi = 0; // Impedisce la riconnessione
    this.ws.close();
  }
}

// Utilizzo
const chat = new WebSocketManager('wss://api.miodominio.it/ws');

chat.on('chat', (dati) => {
  aggiungiMessaggioChat(dati);
});

chat.invia('chat', { testo: 'Ciao a tutti!' });
```

### Quando Usare Ciascuna Tecnologia

**Usa Server-Sent Events quando**:
- Il flusso di dati e prevalentemente dal server al client.
- Serve la riconnessione automatica senza codice aggiuntivo.
- L'applicazione deve funzionare attraverso proxy e firewall restrittivi.
- Stai aggiornando dashboard, feed di notizie o notifiche.

**Usa WebSocket quando**:
- Serve comunicazione bidirezionale a bassa latenza.
- Devi trasmettere dati binari (file, audio, video).
- L'applicazione richiede interazione in tempo reale (chat, gaming, collaborazione).
- La latenza di ogni millisecondo conta (trading finanziario).

---

## WebRTC: Comunicazione Peer-to-Peer

### Concetto e Architettura

**WebRTC** (Web Real-Time Communication) e un insieme di API e protocolli che consentono la comunicazione audio, video e dati in tempo reale direttamente tra browser, senza intermediari per il transito dei media. Il traffico media viaggia peer-to-peer (P2P) quando possibile, riducendo latenza e costi server.

L'architettura WebRTC si compone di tre livelli:

- **MediaStream (getUserMedia)**: acquisizione di audio e video dalla fotocamera, microfono o schermo del dispositivo.
- **RTCPeerConnection**: gestione della connessione P2P, negoziazione codec, cifratura DTLS/SRTP e attraversamento NAT.
- **RTCDataChannel**: canale dati arbitrario a bassa latenza tra peer, con semantica configurabile (affidabile/ordinato oppure non affidabile).

### Signaling e Attraversamento NAT

WebRTC necessita di un canale di segnalazione (signaling) esterno per scambiare le informazioni di connessione (SDP offer/answer e candidati ICE) tra i peer. Il protocollo di signaling non e specificato da WebRTC: si puo usare WebSocket, SSE, HTTP polling o qualsiasi altro meccanismo.

Per attraversare firewall e NAT, WebRTC utilizza il framework **ICE** (Interactive Connectivity Establishment) con server **STUN** (Session Traversal Utilities for NAT) per scoprire l'indirizzo IP pubblico e server **TURN** (Traversal Using Relays around NAT) come relay quando la connessione diretta non e possibile.

```javascript
// Configurazione ICE con server STUN e TURN
const configurazione = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    {
      urls: 'turn:turn.miodominio.it:3478',
      username: 'utente',
      credential: 'password'
    }
  ],
  iceCandidatePoolSize: 10
};
```

### Implementazione di una Connessione Video

```javascript
class ConnessioneVideo {
  constructor(signaling) {
    this.signaling = signaling;
    this.peerConnection = null;
    this.streamLocale = null;
  }

  async avvia() {
    // Acquisisci audio e video dal dispositivo
    this.streamLocale = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        frameRate: { ideal: 30 }
      },
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    // Mostra il video locale
    document.getElementById('video-locale').srcObject = this.streamLocale;

    // Crea la connessione peer
    this.peerConnection = new RTCPeerConnection(configurazione);

    // Aggiungi le tracce locali alla connessione
    this.streamLocale.getTracks().forEach((traccia) => {
      this.peerConnection.addTrack(traccia, this.streamLocale);
    });

    // Gestisci le tracce remote in arrivo
    this.peerConnection.ontrack = (event) => {
      const videoRemoto = document.getElementById('video-remoto');
      if (videoRemoto.srcObject !== event.streams[0]) {
        videoRemoto.srcObject = event.streams[0];
      }
    };

    // Invia i candidati ICE al peer remoto tramite signaling
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        this.signaling.invia({
          tipo: 'ice-candidate',
          candidato: event.candidate
        });
      }
    };

    // Monitora lo stato della connessione
    this.peerConnection.onconnectionstatechange = () => {
      console.log('Stato connessione:', this.peerConnection.connectionState);
      if (this.peerConnection.connectionState === 'failed') {
        this.riavvia();
      }
    };
  }

  // Crea un'offerta SDP (il chiamante)
  async creaOfferta() {
    const offerta = await this.peerConnection.createOffer();
    await this.peerConnection.setLocalDescription(offerta);
    this.signaling.invia({ tipo: 'offerta', sdp: offerta });
  }

  // Gestisci un'offerta ricevuta e crea una risposta (il chiamato)
  async gestisciOfferta(offerta) {
    await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offerta));
    const risposta = await this.peerConnection.createAnswer();
    await this.peerConnection.setLocalDescription(risposta);
    this.signaling.invia({ tipo: 'risposta', sdp: risposta });
  }

  // Gestisci una risposta SDP ricevuta
  async gestisciRisposta(risposta) {
    await this.peerConnection.setRemoteDescription(new RTCSessionDescription(risposta));
  }

  // Aggiungi un candidato ICE ricevuto dal peer remoto
  async aggiungiCandidatoICE(candidato) {
    await this.peerConnection.addIceCandidate(new RTCIceCandidate(candidato));
  }

  // Chiudi la connessione
  chiudi() {
    this.streamLocale?.getTracks().forEach((t) => t.stop());
    this.peerConnection?.close();
  }
}
```

### RTCDataChannel: Dati Arbitrari P2P

Il **RTCDataChannel** consente di scambiare dati arbitrari tra peer con latenza minima, senza passare dal server. Supporta sia modalita affidabile (simile a TCP) sia non affidabile (simile a UDP), rendendolo adatto sia per chat testuali sia per gaming in tempo reale.

```javascript
// Creazione di un data channel (dal chiamante)
function creaDataChannel(peerConnection) {
  const canale = peerConnection.createDataChannel('dati-app', {
    ordered: true,         // Mantieni l'ordine dei messaggi
    maxRetransmits: 3      // Numero massimo di ritrasmissioni
  });

  canale.onopen = () => {
    console.log('DataChannel aperto');
    canale.send(JSON.stringify({ tipo: 'saluto', messaggio: 'Connesso!' }));
  };

  canale.onmessage = (event) => {
    const dati = JSON.parse(event.data);
    console.log('Dati ricevuti via DataChannel:', dati);
  };

  canale.onclose = () => console.log('DataChannel chiuso');

  return canale;
}

// Ricezione di un data channel (dal chiamato)
peerConnection.ondatachannel = (event) => {
  const canale = event.channel;

  canale.onmessage = (event) => {
    const dati = JSON.parse(event.data);
    gestisciMessaggioP2P(dati);
  };
};
```

### Condivisione Schermo

La condivisione dello schermo utilizza `getDisplayMedia()` per acquisire il contenuto del display dell'utente, che puo poi essere trasmesso tramite la stessa `RTCPeerConnection` usata per il video della fotocamera.

```javascript
async function condividiSchermo(peerConnection) {
  const streamSchermo = await navigator.mediaDevices.getDisplayMedia({
    video: {
      cursor: 'always',
      displaySurface: 'monitor'
    },
    audio: true // Audio di sistema (se supportato)
  });

  // Sostituisci la traccia video corrente con la condivisione schermo
  const tracciaVideo = streamSchermo.getVideoTracks()[0];
  const sender = peerConnection.getSenders()
    .find((s) => s.track?.kind === 'video');

  if (sender) {
    await sender.replaceTrack(tracciaVideo);
  }

  // Rileva quando l'utente interrompe la condivisione
  tracciaVideo.onended = () => {
    console.log('Condivisione schermo terminata');
    ripristinaFotocamera(peerConnection);
  };

  return streamSchermo;
}
```

### Sicurezza WebRTC

Tutti i componenti WebRTC usano cifratura obbligatoria. Il traffico media e protetto da **SRTP** (Secure Real-time Transport Protocol) con chiavi negoziate tramite **DTLS** (Datagram Transport Layer Security). I data channel usano **DTLS** direttamente. La cifratura e obbligatoria e non puo essere disabilitata: non esiste un equivalente di "HTTP" non cifrato per WebRTC.

---

## Project Fugu e Web Capabilities

### Panoramica del Progetto

**Project Fugu** e un'iniziativa collaborativa di Google, Microsoft e Intel il cui obiettivo e colmare il divario di funzionalita tra le applicazioni web e quelle native. Il nome deriva dal pesce palla giapponese (fugu): potenzialmente pericoloso se preparato male, ma straordinariamente prezioso se gestito con competenza. Analogamente, queste API espongono capacita potenti del dispositivo al web, ma richiedono un modello di sicurezza rigoroso con permessi espliciti dell'utente.

### API Chiave di Project Fugu

Le API di Project Fugu coprono un ampio spettro di funzionalita hardware e di sistema. Alcune sono gia stabili e ampiamente supportate, altre sono in fase sperimentale. Ecco le piu significative per lo sviluppo PWA.

#### Badging API

Permette di impostare un badge numerico o un indicatore sull'icona della PWA installata, come fanno le app native per indicare messaggi non letti o notifiche pendenti.

```javascript
// Imposta un badge numerico sull'icona dell'app
if ('setAppBadge' in navigator) {
  // Mostra il conteggio di notifiche non lette
  await navigator.setAppBadge(5);

  // Mostra un indicatore generico (punto) senza numero
  await navigator.setAppBadge();

  // Rimuovi il badge
  await navigator.clearAppBadge();
}
```

#### Screen Wake Lock API

Impedisce allo schermo di spegnersi mentre l'utente sta utilizzando l'app, utile per presentazioni, ricette di cucina, navigazione GPS o lettori musicali.

```javascript
let wakeLock = null;

async function attivaBloccoSchermo() {
  if (!('wakeLock' in navigator)) return;

  try {
    wakeLock = await navigator.wakeLock.request('screen');
    console.log('Blocco schermo attivato');

    wakeLock.addEventListener('release', () => {
      console.log('Blocco schermo rilasciato');
    });
  } catch (errore) {
    console.error('Impossibile attivare il blocco schermo:', errore);
  }
}

// Riattiva il blocco quando la pagina torna in primo piano
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && !wakeLock) {
    attivaBloccoSchermo();
  }
});

// Rilascia il blocco quando non serve piu
async function rilasciaBloccoSchermo() {
  if (wakeLock) {
    await wakeLock.release();
    wakeLock = null;
  }
}
```

#### Contact Picker API

Consente all'utente di selezionare contatti dalla rubrica del dispositivo e condividerli con l'applicazione web, senza esporre l'intera rubrica.

```javascript
async function selezionaContatti() {
  if (!('contacts' in navigator && 'ContactsManager' in window)) {
    console.log('Contact Picker API non supportata');
    return;
  }

  const proprieta = ['name', 'email', 'tel', 'icon'];
  const opzioni = { multiple: true };

  const contatti = await navigator.contacts.select(proprieta, opzioni);

  for (const contatto of contatti) {
    console.log(`Nome: ${contatto.name?.join(', ')}`);
    console.log(`Email: ${contatto.email?.join(', ')}`);
    console.log(`Telefono: ${contatto.tel?.join(', ')}`);
  }

  return contatti;
}
```

#### Idle Detection API

Rileva quando l'utente e inattivo (non interagisce con tastiera, mouse o touchscreen) o quando lo schermo e bloccato. Utile per app di chat (stato "assente"), strumenti di collaborazione o kiosk.

```javascript
async function monitoraInattivita() {
  if (!('IdleDetector' in window)) return;

  const stato = await IdleDetector.requestPermission();
  if (stato !== 'granted') return;

  const detector = new IdleDetector();

  detector.addEventListener('change', () => {
    const statoUtente = detector.userState;     // 'active' o 'idle'
    const statoSchermo = detector.screenState;  // 'locked' o 'unlocked'

    if (statoUtente === 'idle') {
      aggiornaPresenza('assente');
    } else {
      aggiornaPresenza('online');
    }

    if (statoSchermo === 'locked') {
      sospendiFunzionalitaPesanti();
    }
  });

  await detector.start({ threshold: 60000 }); // Soglia di 60 secondi
}
```

#### Window Controls Overlay

Consente alle PWA installate di personalizzare la barra del titolo della finestra, occupando l'area normalmente riservata ai controlli del sistema operativo. Questo permette di creare un'interfaccia piu integrata e nativa.

```json
{
  "display_override": ["window-controls-overlay"],
  "display": "standalone"
}
```

```css
/* Stile per l'area della barra del titolo personalizzata */
.barra-titolo {
  position: fixed;
  top: 0;
  left: env(titlebar-area-x, 0);
  width: env(titlebar-area-width, 100%);
  height: env(titlebar-area-height, 33px);
  -webkit-app-region: drag; /* Permette il trascinamento della finestra */
  display: flex;
  align-items: center;
  padding: 0 16px;
  background: var(--colore-primario);
  color: white;
}

.barra-titolo button {
  -webkit-app-region: no-drag; /* I pulsanti restano cliccabili */
}
```

#### EyeDropper API

Permette all'utente di selezionare un colore da qualsiasi pixel dello schermo, utile per editor grafici, strumenti di design e selettori colore avanzati.

```javascript
async function selezionaColoreDaSchermo() {
  if (!('EyeDropper' in window)) {
    console.log('EyeDropper API non supportata');
    return;
  }

  const pipetta = new EyeDropper();

  try {
    const risultato = await pipetta.open();
    console.log('Colore selezionato:', risultato.sRGBHex); // es. "#ff5733"
    return risultato.sRGBHex;
  } catch {
    console.log('Selezione colore annullata');
  }
}
```

#### Barcode Detection API

Rileva e decodifica codici a barre e QR code direttamente dalle immagini o dal flusso video della fotocamera, senza librerie di terze parti.

```javascript
async function scansionaCodiceBarre(immagine) {
  if (!('BarcodeDetector' in window)) {
    console.log('BarcodeDetector non supportato');
    return;
  }

  // Verifica i formati supportati
  const formati = await BarcodeDetector.getSupportedFormats();
  console.log('Formati supportati:', formati);

  const detector = new BarcodeDetector({
    formats: ['qr_code', 'ean_13', 'ean_8', 'code_128']
  });

  const codici = await detector.detect(immagine);

  for (const codice of codici) {
    console.log(`Formato: ${codice.format}, Valore: ${codice.rawValue}`);
  }

  return codici;
}

// Scansione continua da fotocamera
async function scansioneContinuaDaFotocamera() {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: 'environment' }
  });

  const video = document.getElementById('video-scanner');
  video.srcObject = stream;

  const detector = new BarcodeDetector({ formats: ['qr_code'] });

  const intervallo = setInterval(async () => {
    const codici = await detector.detect(video);
    if (codici.length > 0) {
      clearInterval(intervallo);
      stream.getTracks().forEach((t) => t.stop());
      gestisciCodiceScansionato(codici[0]);
    }
  }, 500);
}
```

### Pattern di Capability Detection

Per ogni API di Project Fugu, il pattern di feature detection e fondamentale per garantire il progressive enhancement. Tutte queste API richiedono un contesto sicuro (HTTPS) e molte richiedono un gesto utente esplicito per motivi di sicurezza e privacy. Il tracker ufficiale del progetto su chromestatus.com permette di monitorare lo stato di implementazione di ogni singola API nei vari browser, distinguendo tra le fasi di proposta, origin trial, implementazione e disponibilita stabile.

```javascript
// Pattern generico di capability detection
function verificaCapacita() {
  const capacita = {
    wakeLock: 'wakeLock' in navigator,
    contacts: 'contacts' in navigator && 'ContactsManager' in window,
    idleDetection: 'IdleDetector' in window,
    eyeDropper: 'EyeDropper' in window,
    barcodeDetection: 'BarcodeDetector' in window,
    badging: 'setAppBadge' in navigator,
    webSerial: 'serial' in navigator,
    webBluetooth: 'bluetooth' in navigator,
    webUSB: 'usb' in navigator,
    fileSystemAccess: 'showOpenFilePicker' in window,
    webShare: 'share' in navigator,
    windowControlsOverlay: 'windowControlsOverlay' in navigator,
  };

  console.table(capacita);
  return capacita;
}
```

---

## Testing PWA con Lighthouse e Strumenti Dedicati

### Lighthouse: Audit PWA

**Lighthouse** e lo strumento di riferimento per verificare la conformita di una PWA ai criteri di installabilita, performance, accessibilita e best practice. Disponibile come tab nei DevTools di Chrome, come CLI e come modulo Node.js integrabile nella pipeline CI/CD.

I criteri di installabilita PWA verificati da Lighthouse includono: Service Worker registrato e funzionante, manifest valido con icone nelle dimensioni richieste, HTTPS abilitato, pagina reattiva anche offline, contenuto visibile senza JavaScript, reindirizzamento da HTTP a HTTPS.

#### Esecuzione da CLI

```bash
# Installazione globale
npm install -g lighthouse

# Audit completo con report HTML
lighthouse https://mia-pwa.it --output html --output-path ./report-pwa.html

# Audit solo categorie PWA e performance
lighthouse https://mia-pwa.it --only-categories=pwa,performance --output json

# Audit con throttling per simulare rete 3G
lighthouse https://mia-pwa.it --throttling.cpuSlowdownMultiplier=4 \
  --throttling.downloadThroughputKbps=1600
```

#### Lighthouse CI nella Pipeline

**Lighthouse CI** automatizza gli audit in ogni build, impostando soglie minime che bloccano il deploy se non raggiunte.

```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000/', 'http://localhost:3000/dashboard'],
      numberOfRuns: 3, // Media di 3 esecuzioni per risultati stabili
      startServerCommand: 'npm run serve',
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:pwa': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['warn', { minScore: 0.85 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'service-worker': 'error',
        'installable-manifest': 'error',
        'splash-screen': 'warn',
        'themed-omnibox': 'warn',
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

```bash
# Esecuzione nella CI
npx lhci autorun
```

#### Testing Offline con Playwright

Playwright consente di testare il comportamento offline della PWA simulando la disconnessione dalla rete, verificando che il Service Worker serva le risorse dalla cache.

```javascript
import { test, expect } from '@playwright/test';

test('la PWA funziona offline dopo il primo caricamento', async ({ page, context }) => {
  // Primo caricamento online per popolare la cache
  await page.goto('https://mia-pwa.it');
  await page.waitForLoadState('networkidle');

  // Verifica che il Service Worker sia registrato
  const swRegistrato = await page.evaluate(() => {
    return navigator.serviceWorker.ready.then(() => true);
  });
  expect(swRegistrato).toBe(true);

  // Simula la modalita offline
  await context.setOffline(true);

  // Ricarica la pagina offline
  await page.reload();

  // Verifica che il contenuto sia ancora visibile
  const titolo = page.locator('h1');
  await expect(titolo).toBeVisible();

  // Verifica che la pagina offline non mostri errori di rete
  const erroreRete = page.locator('.errore-rete');
  await expect(erroreRete).not.toBeVisible();

  // Ripristina la connessione
  await context.setOffline(false);
});

test('le notifiche push vengono gestite correttamente', async ({ page }) => {
  await page.goto('https://mia-pwa.it');

  // Concedi il permesso per le notifiche
  await page.context().grantPermissions(['notifications']);

  // Verifica che il pulsante di sottoscrizione sia presente
  const btnNotifiche = page.locator('#btn-attiva-notifiche');
  await expect(btnNotifiche).toBeVisible();
});
```

---

## Performance Budget per le PWA

### Definizione e Importanza

Un **performance budget** e un insieme di limiti quantitativi sulle metriche di performance che un'applicazione non deve superare. Per le PWA, dove l'esperienza deve competere con le app native, rispettare budget rigorosi e essenziale per garantire tempi di caricamento rapidi, specialmente su reti mobili lente.

### Budget Raccomandati per PWA

| Risorsa | Budget (gzipped) | Razionale |
|---|---|---|
| JavaScript totale | < 200 KB | Parsing e esecuzione JS sono il collo di bottiglia su mobile |
| CSS totale | < 50 KB | CSS blocca il rendering, minimizzare e critico |
| Immagini hero | < 100 KB | LCP dipende dall'immagine principale |
| Font personalizzati | < 50 KB | Subset e max 2 famiglie |
| App Shell HTML | < 15 KB | Primo byte significativo |
| Service Worker | < 50 KB | Registrazione e installazione rapida |

### Strumenti per il Monitoraggio del Budget

#### size-limit

```bash
# Installazione
npm install --save-dev size-limit @size-limit/preset-app

# package.json
{
  "size-limit": [
    {
      "path": "dist/js/*.js",
      "limit": "200 KB",
      "gzip": true
    },
    {
      "path": "dist/css/*.css",
      "limit": "50 KB",
      "gzip": true
    }
  ]
}
```

```bash
# Verifica nella CI
npx size-limit
```

#### Budget in Lighthouse

Lighthouse supporta la definizione di budget direttamente nella configurazione, bloccando la build se i limiti vengono superati.

```json
{
  "budgets": [
    {
      "resourceSizes": [
        { "resourceType": "script", "budget": 200 },
        { "resourceType": "stylesheet", "budget": 50 },
        { "resourceType": "image", "budget": 300 },
        { "resourceType": "font", "budget": 50 },
        { "resourceType": "total", "budget": 600 }
      ],
      "resourceCounts": [
        { "resourceType": "script", "budget": 10 },
        { "resourceType": "third-party", "budget": 5 }
      ],
      "timings": [
        { "metric": "first-contentful-paint", "budget": 1500 },
        { "metric": "interactive", "budget": 3000 },
        { "metric": "largest-contentful-paint", "budget": 2500 }
      ]
    }
  ]
}
```

#### Analisi del Bundle

Per identificare le dipendenze che consumano piu spazio nel bundle JavaScript, strumenti come `webpack-bundle-analyzer` e `source-map-explorer` visualizzano la composizione del bundle con mappe interattive.

```bash
# Analisi del bundle Webpack
npx webpack-bundle-analyzer dist/stats.json

# Analisi basata su source map (funziona con qualsiasi bundler)
npx source-map-explorer dist/js/*.js
```

### Monitoraggio della Memoria

Per le PWA che restano aperte a lungo (dashboard, editor, chat), monitorare l'uso della memoria previene degradi progressivi e crash.

```javascript
// Verifica periodica dell'uso di memoria (solo Chrome)
async function monitoraMemoria() {
  if (!performance.measureUserAgentSpecificMemory) return;

  setInterval(async () => {
    try {
      const memoria = await performance.measureUserAgentSpecificMemory();
      const mbUsati = (memoria.bytes / 1024 / 1024).toFixed(1);
      console.log(`Memoria usata: ${mbUsati} MB`);

      if (memoria.bytes > 200 * 1024 * 1024) { // > 200 MB
        console.warn('[Memoria] Utilizzo elevato, avviare pulizia');
        liberaRisorseNonCritiche();
      }
    } catch (errore) {
      // API richiede cross-origin isolation
      console.debug('measureUserAgentSpecificMemory non disponibile');
    }
  }, 30000); // Ogni 30 secondi
}
```

---

## Best Practice

### 1. Adottare una Strategia di Cache Progressiva

Non pre-cacheare tutto all'installazione del Service Worker. Inizia con l'app shell (HTML, CSS e JS essenziali), poi usa una strategia cache-on-demand per le risorse secondarie. Questo riduce il tempo di installazione e lo spazio di storage consumato.

### 2. Implementare Aggiornamenti Trasparenti

Quando il Service Worker rileva una nuova versione, informa l'utente con un banner discreto che propone l'aggiornamento, invece di forzare un reload automatico. Usa `skipWaiting()` e `clients.claim()` con cautela, poiche possono causare incoerenze se la nuova versione modifica le API.

### 3. Progettare Offline-First

Progetta l'esperienza utente partendo dallo scenario offline e aggiungi le funzionalita online come miglioramento progressivo. Mostra chiaramente lo stato della connessione, sincronizza i dati in background con la Background Sync API e gestisci i conflitti di dati con strategie di merge esplicite.

### 4. Ottimizzare il Web App Manifest

Fornisci icone in tutte le dimensioni richieste, includi icone maskable per Android, aggiungi screenshot per arricchire l'esperienza di installazione, e definisci shortcut per le azioni piu frequenti. Testa sempre il manifest con Lighthouse e la tab Application dei DevTools di Chrome.

### 5. Rispettare il Consenso dell'Utente per le Notifiche Push

Non richiedere il permesso per le notifiche al primo caricamento della pagina. Mostra prima il valore che le notifiche offrono e usa un prompt personalizzato prima di quello nativo del browser. Rispetta il rifiuto dell'utente e offri sempre un modo per disattivare le notifiche nelle impostazioni dell'app.

### 6. Testare la PWA con Lighthouse

Esegui regolarmente audit Lighthouse per verificare i requisiti PWA: Service Worker registrato, manifest valido, HTTPS, tempo di risposta sotto i 3 secondi, reindirizzamento da HTTP a HTTPS, contenuto visibile anche senza JavaScript. Automatizza questi controlli nella pipeline CI/CD.

### 7. Incapsulare i Web Components Correttamente

Usa sempre il Shadow DOM per isolare gli stili dei componenti. Comunica tra componenti tramite attributi, proprieta e custom events (con `composed: true` per attraversare il confine del Shadow DOM). Evita di manipolare direttamente il DOM interno di altri componenti.

### 8. Usare WebAssembly Solo Dove Serve

Non sostituire JavaScript con WebAssembly per logica semplice: il costo di serializzazione tra JS e Wasm puo annullare i benefici prestazionali. Riserva Wasm per calcoli computazionalmente intensivi dove la differenza di performance e misurabile e significativa.

### 9. Garantire il Progressive Enhancement

La PWA deve funzionare come un sito web standard su browser che non supportano le funzionalita avanzate. Usa feature detection (`if ('serviceWorker' in navigator)`) prima di accedere a qualsiasi API avanzata. L'esperienza base deve essere sempre accessibile.

### 10. Gestire la Dimensione della Cache con Limiti Espliciti

Imposta limiti massimi per il numero di elementi e la durata della cache. Senza questi limiti, la cache cresce indefinitamente e puo consumare tutto lo spazio di storage disponibile. Workbox offre `ExpirationPlugin` per automatizzare questa gestione con politiche di scadenza configurabili.

---

> **Nota**: le tecnologie presentate in questa guida sono in continua evoluzione. Verifica sempre la compatibilita dei browser tramite [Can I Use](https://caniuse.com/) e le documentazioni ufficiali su [MDN Web Docs](https://developer.mozilla.org/) prima di adottare una nuova API in produzione.

---

## Esercizi

### Esercizio 1 — PWA Offline-First con Service Worker Manuale

**Obiettivo:** costruire una PWA che funzioni completamente offline implementando il Service Worker senza librerie di astrazione.

Crea un'applicazione "Note Offline" con le seguenti caratteristiche:

- Implementa un Service Worker manuale (senza Workbox) che gestisca tre strategie di caching: Cache-First per asset statici (CSS, JS, immagini), Network-First per le API, Stale-While-Revalidate per le pagine HTML
- Configura il ciclo di vita completo: `install` (pre-cache degli asset critici), `activate` (pulizia delle cache obsolete con versionamento), `fetch` (routing alle strategie corrette)
- Implementa un meccanismo di sincronizzazione delle note create offline usando la Background Sync API
- Crea un `manifest.json` completo con icone in 192x192 e 512x512 (standard e maskable), colori tema, display standalone, shortcut per "Nuova Nota"
- Mostra un banner personalizzato per l'installazione usando l'evento `beforeinstallprompt`
- Testa con Lighthouse: il punteggio PWA deve essere 100

### Esercizio 2 — Web Push Notifications con Backend

**Obiettivo:** implementare un sistema completo di notifiche push con subscription management e invio dal server.

Costruisci un sistema di notifiche per un'applicazione di task management:

- Genera le chiavi VAPID (pubblica e privata) con la libreria `web-push` per Node.js
- Implementa la subscription lato client: richiesta del permesso, creazione della subscription tramite `pushManager.subscribe()`, invio dell'endpoint e delle chiavi al server
- Crea un backend Express con endpoint: `POST /api/subscribe` (salva subscription), `POST /api/notify` (invia notifica a tutte le subscription), `DELETE /api/unsubscribe` (rimuove subscription)
- Gestisci le notifiche nel Service Worker con `push` event e `notificationclick` per navigare alla pagina pertinente
- Implementa la gestione del rifiuto del permesso e la revoca della subscription
- Testa su Chrome e Firefox, documentando le differenze di comportamento tra i due browser

### Esercizio 3 — Web Components: Libreria di Componenti Riutilizzabili

**Obiettivo:** creare una libreria di Web Components nativi utilizzabili in qualsiasi framework.

Sviluppa 3 Custom Elements con Shadow DOM e Slot:

- `<app-modal>`: modale con apertura/chiusura animata, trap del focus (il focus non esce dalla modale quando aperta), chiusura con Escape, slot per header/body/footer, attributi `open` e `close-on-backdrop`
- `<app-tabs>`: sistema di tab con navigazione da tastiera (frecce sinistra/destra), attributo `active-tab`, slot per ogni pannello, evento `tab-change` con `composed: true`
- `<app-toast>`: notifiche toast con posizionamento configurabile (top-right, bottom-center, ecc.), auto-dismiss con timer, tipi (success, error, warning, info), animazione di entrata/uscita
- Ogni componente deve usare CSS custom properties per la personalizzazione del tema dall'esterno
- Scrivi test con Playwright che verifichino il funzionamento di ogni componente
- Pubblica la libreria come pacchetto npm con `package.json` che esporti i componenti come ES modules

### Esercizio 4 — WebAssembly: Modulo di Elaborazione Immagini

**Obiettivo:** compilare un modulo Rust in WebAssembly e integrarlo in un'applicazione web per elaborazione immagini client-side.

Implementa un editor di immagini nel browser con elaborazione Wasm:

- Scrivi un modulo Rust con `wasm-bindgen` che esponga le funzioni: `grayscale(pixels)`, `blur(pixels, radius)`, `resize(pixels, width, height, newWidth, newHeight)`, `adjust_brightness(pixels, factor)`
- Compila con `wasm-pack` targeting `web` e genera i bindings JavaScript
- Crea un'interfaccia web che permetta di caricare un'immagine, applicare i filtri e scaricare il risultato
- Usa un Web Worker per eseguire le operazioni Wasm senza bloccare il main thread
- Confronta le performance di ogni operazione tra l'implementazione Wasm e un'equivalente implementazione in JavaScript puro usando `performance.now()`
- Documenta i risultati del benchmark con una tabella di confronto per immagini di dimensioni diverse (500x500, 1000x1000, 2000x2000)

### Esercizio 5 — Applicazione Completa con API Moderne del Browser

**Obiettivo:** costruire un'applicazione che integri molteplici API web moderne con progressive enhancement.

Crea un'applicazione "Media Vault" per la gestione di file multimediali:

- Usa la File System Access API per aprire, leggere e salvare file locali con `showOpenFilePicker()` e `showSaveFilePicker()`
- Implementa la Web Share API per condividere file e testo con altre applicazioni
- Usa la Web Clipboard API per copiare/incollare immagini e testo formattato
- Implementa drag-and-drop con la Drag and Drop API per importare file nell'applicazione
- Usa IndexedDB (tramite `idb` wrapper) per la persistenza locale dei metadati dei file
- Implementa feature detection per ogni API e fornisci fallback funzionali (es. `<input type="file">` come fallback per File System Access API)
- Testa su almeno 3 browser (Chrome, Firefox, Safari) e documenta il supporto di ogni API per ciascuno

---

## Letture e Riferimenti

### Documentazione ufficiale

- **MDN — Progressive Web Apps** — guida completa di Mozilla sulle PWA, Service Worker e manifest. https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps (consultato: 2026-05-24)
- **web.dev — Progressive Web Apps** — corsi e articoli di Google su architettura PWA e best practices. https://web.dev/explore/progressive-web-apps (consultato: 2026-05-24)
- **Workbox** — libreria Google per semplificare la gestione dei Service Worker e le strategie di caching. https://developer.chrome.com/docs/workbox/ (consultato: 2026-05-24)
- **MDN — Web Components** — specifica Custom Elements, Shadow DOM, HTML Templates e Slot. https://developer.mozilla.org/en-US/docs/Web/API/Web_components (consultato: 2026-05-24)
- **WebAssembly** — specifica ufficiale e documentazione del formato binario per codice ad alte prestazioni nel browser. https://webassembly.org/ (consultato: 2026-05-24)
- **wasm-bindgen** — strumento per facilitare l'interazione tra Rust e JavaScript tramite WebAssembly. https://rustwasm.github.io/docs/wasm-bindgen/ (consultato: 2026-05-24)
- **Web Push Protocol** — specifica IETF RFC 8030 per il protocollo di push notification. https://datatracker.ietf.org/doc/html/rfc8030 (consultato: 2026-05-24)
- **VAPID** — specifica IETF RFC 8292 per l'identificazione volontaria del server applicativo nelle notifiche push. https://datatracker.ietf.org/doc/html/rfc8292 (consultato: 2026-05-24)
- **MDN — WebRTC API** — documentazione completa su RTCPeerConnection, MediaStream e RTCDataChannel. https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API (consultato: 2026-05-24)
- **Dexie.js** — wrapper minimale per IndexedDB con query dichiarative e migrazioni di schema. https://dexie.org/ (consultato: 2026-05-24)
- **idb** — wrapper leggero per IndexedDB basato su Promise, mantenuto da Jake Archibald. https://github.com/jakearchibald/idb (consultato: 2026-05-24)
- **Project Fugu** — tracker delle nuove capacita web in fase di sviluppo. https://www.chromium.org/teams/web-capabilities-fugu/ (consultato: 2026-05-24)
- **Fugu API Showcase** — raccolta di applicazioni web che utilizzano le API di Project Fugu. https://developer.chrome.com/docs/capabilities/fugu-showcase (consultato: 2026-05-24)
- **Lighthouse CI** — integrazione di Lighthouse nelle pipeline di continuous integration. https://github.com/GoogleChrome/lighthouse-ci (consultato: 2026-05-24)
- **Web Serial API** — specifica per la comunicazione con dispositivi seriali dal browser. https://developer.mozilla.org/en-US/docs/Web/API/Web_Serial_API (consultato: 2026-05-24)

### Libri e approfondimenti

- Jason Grigsby, *Progressive Web Apps*, A Book Apart, 2018.
- Nicola Nicolo, *Building Progressive Web Applications with Vue.js*, Apress, 2020.
- Nicola Nicolo, *Progressive Web Apps with Angular*, Apress, 2021.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Promises, async/await e API del browser necessarie per Service Worker e API moderne |
| [05 — JavaScript Avanzato](05-javascript-avanzato.md) | Web Worker, SharedArrayBuffer e pattern avanzati usati con WebAssembly |
| [14 — Sicurezza Web](14-sicurezza-web.md) | HTTPS obbligatorio per Service Worker, gestione sicura delle chiavi VAPID per Web Push |
| [17 — Performance Web](17-performance-web.md) | Le strategie di caching del Service Worker sono tecniche di ottimizzazione delle performance |
| [01 — HTML5](01-html5.md) | Il manifest e le meta tag PWA sono fondamenti HTML necessari per l'installabilita |
| [15 — Testing Web](15-testing-web.md) | Testing di Service Worker, Web Components e API offline richiede setup specifici con Playwright |
| [06 — Node.js](06-nodejs.md) | Il server-side delle notifiche push con web-push e VAPID richiede conoscenza di Node.js e Express |
| [09 — API e Backend](09-api-e-backend.md) | Le strategie di sincronizzazione offline-first e il Background Sync interagiscono direttamente con gli endpoint API del backend |
| [12 — Database](12-database.md) | IndexedDB come database locale NoSQL nel browser, Dexie.js e idb come wrapper per operazioni CRUD e transazioni |

---

## Glossario

| Termine | Definizione |
|---|---|
| **PWA** | Progressive Web App: applicazione web che offre funzionalita native (installazione, offline, notifiche push) tramite API del browser. |
| **Service Worker** | Script JavaScript eseguito in background dal browser, separato dal main thread, che intercetta le richieste di rete e gestisce la cache. |
| **Web App Manifest** | File JSON che descrive nome, icone, colori e comportamento di visualizzazione di una PWA per l'installazione. |
| **Cache-First** | Strategia di caching che serve sempre dalla cache locale e aggiorna la cache in background solo se necessario. |
| **Network-First** | Strategia di caching che tenta la rete prima e ricade sulla cache solo in caso di errore di connettivita. |
| **Stale-While-Revalidate** | Strategia che serve la risposta dalla cache immediatamente e aggiorna la cache in background con la risposta di rete. |
| **VAPID** | Voluntary Application Server Identification: protocollo di identificazione del server per Web Push che usa chiavi crittografiche. |
| **Custom Element** | API del browser che permette di definire nuovi tag HTML con comportamento personalizzato tramite classi JavaScript. |
| **Shadow DOM** | Sotto-albero DOM incapsulato che isola stili e markup di un componente dal resto della pagina. |
| **Slot** | Meccanismo di composizione dei Web Components che permette al contenuto esterno di essere proiettato all'interno del Shadow DOM. |
| **WebAssembly (Wasm)** | Formato binario a basso livello eseguibile nel browser con performance vicine al codice nativo, compilato da C/C++/Rust. |
| **Background Sync** | API che consente al Service Worker di differire operazioni di rete finche il dispositivo non ha connettivita stabile. |
| **IndexedDB** | Database NoSQL integrato nel browser per la persistenza strutturata di grandi quantita di dati lato client. |
| **Workbox** | Libreria Google che astrae la complessita dei Service Worker fornendo strategie di caching e precaching dichiarative. |
| **WebRTC** | Web Real-Time Communication: insieme di API e protocolli per comunicazione audio, video e dati peer-to-peer direttamente tra browser. |
| **RTCPeerConnection** | Interfaccia WebRTC che gestisce la connessione P2P, negoziazione codec, cifratura e attraversamento NAT tra due peer. |
| **RTCDataChannel** | Canale dati arbitrario a bassa latenza tra peer WebRTC, con semantica configurabile (affidabile o non affidabile). |
| **ICE** | Interactive Connectivity Establishment: framework per l'attraversamento NAT che utilizza server STUN e TURN. |
| **Dexie.js** | Wrapper minimale per IndexedDB (~5 KB) che espone query dichiarative, transazioni semplificate e migrazioni di schema versionato. |
| **idb** | Wrapper leggero (~1.2 KB) per IndexedDB che sostituisce i callback con Promise mantenendo la vicinanza all'API nativa. |
| **CRDT** | Conflict-free Replicated Data Type: struttura dati progettata per convergere automaticamente allo stesso stato su nodi distribuiti senza coordinamento. |
| **Periodic Background Sync** | API che consente al Service Worker di eseguire sincronizzazioni periodiche in background, anche quando l'utente non interagisce con l'app. |
| **Project Fugu** | Iniziativa collaborativa di Google, Microsoft e Intel per colmare il divario di funzionalita tra applicazioni web e native. |
| **Web Serial API** | API del browser per comunicare con dispositivi seriali (Arduino, microcontrollori) tramite porte RS-232/UART. |
| **Lighthouse** | Strumento di audit automatizzato per verificare performance, accessibilita, best practice e conformita PWA di una pagina web. |
| **Performance Budget** | Insieme di limiti quantitativi sulle metriche di performance che un'applicazione non deve superare per garantire un'esperienza utente rapida. |
| **Wake Lock** | API che impedisce allo schermo del dispositivo di spegnersi durante attivita che richiedono la visualizzazione continua. |
| **Badging API** | API per impostare badge numerici o indicatori sull'icona di una PWA installata, simile ai badge delle app native. |
