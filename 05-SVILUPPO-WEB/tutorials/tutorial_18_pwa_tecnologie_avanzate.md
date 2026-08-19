# Tutorial 18 — PWA e Tecnologie Avanzate: Dal Principiante all'Esperto

> **Companion a:** `18-pwa-e-tecnologie-avanzate.md`
> **Scope:** service worker e ciclo di vita, strategie di caching, manifest e installazione, funzionamento offline, sincronizzazione differita, notifiche push, IndexedDB, Web Components, WebAssembly, Server-Sent Events e WebRTC, API moderne, aggiornamenti e disinstallazione
> **Prerequisiti:** `tutorial_17_performance_web.md` — cache HTTP e budget; `tutorial_05_javascript_avanzato.md` — Promise, worker, eventi; `tutorial_14_sicurezza_web.md` — origini e HTTPS
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Service Worker API · Workbox 7 · IndexedDB · Web Push · WebAssembly

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Cos'è una PWA, e cosa non è](#a1-cosè-una-pwa-e-cosa-non-è)
  - [A2. Il service worker e il suo ciclo di vita](#a2-il-service-worker-e-il-suo-ciclo-di-vita)
  - [A3. Le cinque strategie di caching](#a3-le-cinque-strategie-di-caching)
  - [A4. Il manifest e l'installazione](#a4-il-manifest-e-linstallazione)
  - [A5. Funzionare offline](#a5-funzionare-offline)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. L'aggiornamento del service worker](#b1-laggiornamento-del-service-worker)
  - [B2. IndexedDB: lo stato che sopravvive](#b2-indexeddb-lo-stato-che-sopravvive)
  - [B3. Sincronizzazione differita e coda delle operazioni](#b3-sincronizzazione-differita-e-coda-delle-operazioni)
  - [B4. Notifiche push](#b4-notifiche-push)
  - [B5. Web Components: quando servono davvero](#b5-web-components-quando-servono-davvero)
  - [B6. WebAssembly: quando conviene](#b6-webassembly-quando-conviene)
  - [B7. SSE contro WebSocket contro polling](#b7-sse-contro-websocket-contro-polling)
  - [B8. Le API moderne e la degradazione](#b8-le-api-moderne-e-la-degradazione)
  - [B9. Il service worker come superficie di rischio](#b9-il-service-worker-come-superficie-di-rischio)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: la dashboard offline](#c2-mini-progetto-la-dashboard-offline)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Risoluzione dei conflitti](#d1-risoluzione-dei-conflitti)
  - [D2. Quota di archiviazione e persistenza](#d2-quota-di-archiviazione-e-persistenza)
  - [D3. Testare e diagnosticare un service worker](#d3-testare-e-diagnosticare-un-service-worker)
  - [D4. Disinstallare un service worker](#d4-disinstallare-un-service-worker)
  - [D5. Quando NON serve una PWA](#d5-quando-non-serve-una-pwa)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
        PAGINA                    SERVICE WORKER              RETE
        ──────                    ──────────────              ────
   fetch('/api/…')  ──────►  evento 'fetch'  ──────────►  server
                                   │
                             ┌─────┴─────┐
                             ▼           ▼
                        Cache API    IndexedDB
                        (risposte)   (dati strutturati)

   IL SERVICE WORKER È UN PROXY CHE GIRA NEL BROWSER: thread
   separato (nessun DOM), solo HTTPS, sopravvive alla chiusura della
   pagina e viene svegliato dagli eventi. Una volta registrato resta
   finché non lo si rimuove — la sua proprietà più utile e più
   pericolosa.

   ┌──────────────────────────────────────────────────────────┐
   │ LE QUATTRO COSE CHE UNA PWA AGGIUNGE A UN SITO           │
   │  1. funziona senza rete (o con rete pessima)             │
   │  2. si installa e si apre come un'applicazione           │
   │  3. riceve notifiche push                                │
   │  4. completa le operazioni quando la rete torna          │
   │  ⚠ Nessuna delle quattro serve a tutti i siti.           │
   └──────────────────────────────────────────────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Cos'è una PWA, e cosa non è

> **Analogia:** un negozio con la saracinesca automatica. Continua a funzionare durante un blackout perché ha un gruppo di continuità, e ha un'insegna sulla strada che porta direttamente all'ingresso. Non è diventato un altro negozio: è lo stesso, che ha smesso di dipendere dalla corrente.

```
UNA PWA È UN SITO WEB CHE HA TRE COSE
  1. HTTPS
  2. un SERVICE WORKER registrato
  3. un WEB APP MANIFEST
Non è una tecnologia nuova, non è un framework, e non richiede di
riscrivere nulla: si aggiunge a ciò che esiste.

COSA GUADAGNA DAVVERO
  ✅ funziona con rete assente o pessima
  ✅ si installa: icona, finestra propria, avvio dalla schermata
  ✅ notifiche push anche a pagina chiusa
  ✅ carica istantaneamente dalla cache alle visite successive

COSA NON GUADAGNA
  ❌ non è un'app nativa: alcune API di sistema restano fuori
     portata, e la disponibilità cambia molto fra i browser
  ❌ non entra negli store come un'app nativa (esistono percorsi,
     ma con vincoli)
  ❌ ⚠ IL SUPPORTO NON È UNIFORME: le notifiche push su iOS
     richiedono che l'utente abbia installato la PWA, e diverse API
     avanzate sono solo su Chromium. Ogni funzionalità va verificata
     su caniuse.com e degradata (vedi B8).
```

---

## A2. Il service worker e il suo ciclo di vita

```javascript
// La registrazione: nella pagina, dopo il caricamento per non
// competere con le risorse critiche
if ('serviceWorker' in navigator) {
  addEventListener('load', async () => {
    try {
      // Lo SCOPE è il percorso controllato: un file in /js/sw.js
      // controllerebbe solo /js/, quindi deve stare nella RADICE
      await navigator.serviceWorker.register('/sw.js', { scope: '/' })
    } catch (errore) {
      // La registrazione può fallire (HTTPS mancante, errore di
      // sintassi): il sito deve continuare a funzionare
      console.error('registrazione fallita', errore)
    }
  })
}
```

```
   IL CICLO DI VITA, E DOVE CI SI BLOCCA

   register() → INSTALLING ── evento 'install' ──► precache
                     ▼        (se fallisce, il SW è scartato)
              INSTALLED / WAITING  ⚠ QUI SI FERMA se un vecchio SW
                     ▼                controlla ancora delle pagine
              ACTIVATING ── evento 'activate' ──► pulizia cache
                     ▼
              ACTIVATED ── intercetta i 'fetch'
                     ▼
              REDUNDANT   sostituito o rimosso

   ⚠ LO STATO "WAITING" È LA CAUSA DEL 90% DELLA CONFUSIONE. Un
     service worker nuovo NON prende il controllo finché tutte le
     schede con il vecchio non sono chiuse. Ricaricare la pagina non
     basta: la scheda resta la stessa. Vedi B1.
```

```javascript
// sw.js — la forma minima, con i tre eventi del ciclo di vita
const VERSIONE = 'v3'
const CACHE_STATICA = `statica-${VERSIONE}`

self.addEventListener('install', (evento) => {
  evento.waitUntil(
    caches.open(CACHE_STATICA).then((c) => c.addAll(['/', '/offline.html', '/assets/app.css'])),
  )
})

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    (async () => {
      // Le cache delle versioni precedenti vanno eliminate, o lo
      // spazio cresce a ogni rilascio
      const nomi = await caches.keys()
      await Promise.all(nomi.filter((n) => n !== CACHE_STATICA).map((n) => caches.delete(n)))
      // Prende il controllo delle pagine già aperte
      await self.clients.claim()
    })(),
  )
})

self.addEventListener('fetch', (evento) => {
  // ⚠ Si intercettano SOLO le GET: servire una POST dalla cache
  //    produce comportamenti impossibili da diagnosticare
  if (evento.request.method !== 'GET') return

  evento.respondWith(
    caches.match(evento.request).then((risposta) => risposta ?? fetch(evento.request)),
  )
})
```

```
⚠ `evento.waitUntil()` È OBBLIGATORIO nei gestori del ciclo di vita:
  senza, il browser considera l'evento concluso e può terminare il
  service worker mentre l'operazione asincrona è in corso. E
  `evento.respondWith()` va chiamato SINCRONAMENTE, non dentro un
  `then`.
```

---
## A3. Le cinque strategie di caching

```
   CACHE FIRST          cache → (se manca) rete
     Il più veloce. Per ciò che NON cambia: asset con impronta nel
     nome, font, icone.
     ⚠ Se il contenuto cambia, l'utente vede il vecchio per sempre.
   NETWORK FIRST        rete → (se fallisce) cache
     Per i dati che devono essere freschi, con un ripiego offline.
     ⚠ Serve un TIMEOUT: senza, una rete lentissima blocca tutto
       invece di cadere sulla cache.
   STALE WHILE REVALIDATE   cache subito + aggiorna in sottofondo
     Il compromesso migliore per la maggior parte dei contenuti.
   NETWORK ONLY         mai in cache: pagamenti, autenticazione,
     qualunque scrittura.
   CACHE ONLY           per risorse precaricate che devono esistere
     sempre.
```

```javascript
// Cache first, con l'aggiunta alla cache al primo passaggio
async function cachePrima(richiesta, nomeCache) {
  const cache = await caches.open(nomeCache)
  const memorizzata = await cache.match(richiesta)
  if (memorizzata) return memorizzata

  const risposta = await fetch(richiesta)
  // ⚠ Solo le risposte valide: mettere in cache un 404 o un 500
  //   significa servirlo per sempre. `basic` esclude le risposte
  //   opache (cross-origin senza CORS), di cui non si conosce lo stato.
  if (risposta.ok && risposta.type === 'basic') {
    // La risposta va CLONATA: il corpo è uno stream, si consuma una volta
    cache.put(richiesta, risposta.clone())
  }
  return risposta
}

// Network first con timeout: la parte che quasi tutti dimenticano.
// Una rete lentissima è peggio di una assente: senza timeout,
// l'utente aspetta trenta secondi invece di vedere subito il dato
// di ieri.
async function retePrima(richiesta, nomeCache, timeoutMs = 3000) {
  const cache = await caches.open(nomeCache)
  try {
    const risposta = await Promise.race([
      fetch(richiesta),
      new Promise((_, rifiuta) => setTimeout(() => rifiuta(new Error('timeout')), timeoutMs)),
    ])
    if (risposta.ok) cache.put(richiesta, risposta.clone())
    return risposta
  } catch {
    return (await cache.match(richiesta)) ?? caches.match('/offline.html')
  }
}

// Stale while revalidate: risposta immediata, cache aggiornata per
// la volta successiva
async function obsoletaMentreRivalida(richiesta, nomeCache) {
  const cache = await caches.open(nomeCache)
  const memorizzata = await cache.match(richiesta)

  const aggiornamento = fetch(richiesta)
    .then((risposta) => {
      if (risposta.ok) cache.put(richiesta, risposta.clone())
      return risposta
    })
    .catch(() => memorizzata) // offline: si tiene ciò che c'è

  return memorizzata ?? aggiornamento
}
```

```
COME SI ASSEGNA UNA STRATEGIA A UNA RISORSA
  asset con impronta (app.a3f9.js)   cache first, per sempre
  HTML dei documenti                 network first con timeout
  API di lettura                     stale while revalidate
  API di scrittura                   network only (+ coda, vedi B3)
  immagini                           cache first con limite di numero
  font                               cache first, per sempre
```

---
## A4. Il manifest e l'installazione

```json
// public/manifest.webmanifest
{
  "name": "Cruscotto Aziendale",
  "short_name": "Cruscotto",
  "start_url": "/?fonte=pwa",
  "scope": "/",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#0f172a",
  "icons": [
    { "src": "/icone/192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icone/512.png", "sizes": "512x512", "type": "image/png" },
    {
      "src": "/icone/maskable-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
```

```
I CAMPI CHE CONTANO DAVVERO
  start_url    dove si apre l'app installata. `?fonte=pwa` permette
    di misurare quanti la usano installata.
  scope        i percorsi che le appartengono: un link fuori dallo
    scope apre il browser, non la finestra dell'app.
  display      `standalone` (finestra propria) è la scelta usuale.
  icons        ⚠ `purpose: "maskable"` è necessario su Android:
    senza, il sistema ritaglia l'icona e spesso taglia il logo. Il
    contenuto va tenuto nell'80% centrale.
  theme_color  colora la barra di sistema: va allineato al sito.
```

```javascript
// L'installazione: il browser propone da sé, ma solo quando decide.
// Intercettare l'evento permette di chiedere al momento giusto.
let promptInstallazione = null

addEventListener('beforeinstallprompt', (evento) => {
  evento.preventDefault() // impedisce la richiesta automatica
  promptInstallazione = evento
  mostraPulsanteInstalla()
})

pulsanteInstalla.addEventListener('click', async () => {
  if (!promptInstallazione) return
  // ⚠ Deve partire da un gesto dell'utente: chiamarlo all'avvio non
  //   funziona, ed è anche il modo migliore per farsi rifiutare
  promptInstallazione.prompt()
  const { outcome } = await promptInstallazione.userChoice

  promptInstallazione = null // l'evento si consuma
  nascondiPulsanteInstalla()
  if (outcome === 'accepted') registraEvento('pwa_installata')
})

// Rilevare se è già installata
const installata = matchMedia('(display-mode: standalone)').matches
```

```
⚠ `beforeinstallprompt` NON ESISTE SU SAFARI. Su iOS l'installazione
  è manuale ("Aggiungi alla schermata Home") e va spiegata con
  un'istruzione visiva, mostrata solo agli utenti iOS non già
  installati. Non esiste un modo di attivarla da codice.
```

---
## A5. Funzionare offline

```javascript
// La pagina di ripiego: il minimo perché offline non significhi
// "dinosauro del browser". `mode === 'navigate'` identifica una
// navigazione a una pagina, non il caricamento di una risorsa.
self.addEventListener('fetch', (evento) => {
  if (evento.request.method !== 'GET') return

  if (evento.request.mode === 'navigate') {
    evento.respondWith(
      retePrima(evento.request, 'documenti', 3000).catch(() => caches.match('/offline.html')),
    )
  }
})
```

```javascript
// Nella pagina: reagire ai cambi di stato della connessione.
// ⚠ `navigator.onLine` è INAFFIDABILE: dice solo che esiste
//    un'interfaccia di rete attiva, non che internet sia
//    raggiungibile. Un wifi senza uscita risulta "online".
addEventListener('online', () => {
  mostraBanner('Connessione ripristinata', 'successo')
  sincronizzaInSospeso()
})

addEventListener('offline', () => {
  mostraBanner('Sei offline. Le modifiche verranno salvate e inviate dopo.', 'avviso')
})

// Per sapere davvero, si prova
async function reteRaggiungibile() {
  try {
    const risposta = await fetch('/api/salute/vivo', {
      method: 'HEAD',
      cache: 'no-store',
      signal: AbortSignal.timeout(3000),
    })
    return risposta.ok
  } catch {
    return false
  }
}
```

```
IL PRINCIPIO CHE RENDE UTILE L'OFFLINE
  Non è "mostrare una pagina di errore più bella": è che l'utente
  possa CONTINUARE A LAVORARE — le pagine già visitate si aprono, i
  dati già scaricati si consultano, le modifiche si registrano
  localmente e partono quando la rete torna (B3), e l'interfaccia
  dice chiaramente cosa è in sospeso.
  Se offline l'utente non può fare nulla, la PWA non sta risolvendo
  il suo problema — sta solo mostrando un messaggio diverso.
```

---
# Parte B — Comprensione Profonda

---

## B1. L'aggiornamento del service worker

> **Analogia:** cambiare il portinaio mentre l'edificio è pieno. Il nuovo arriva, si prepara nel gabbiotto, ma non prende servizio finché l'ultimo inquilino che parlava con il vecchio non se ne va. Se nessuno esce mai, il nuovo resta in attesa per giorni.

```
COME IL BROWSER SCOPRE UN AGGIORNAMENTO
  · a ogni navigazione dentro lo scope, e comunque non più spesso di
    una volta ogni 24 ore
  · quando la pagina chiama `registration.update()`
  · il confronto è BYTE PER BYTE sul file del service worker

⚠ IL FILE sw.js NON DEVE ESSERE MESSO IN CACHE A LUNGO. Se il server
  lo serve con `max-age=86400`, l'aggiornamento arriva un giorno
  dopo. La regola: `Cache-Control: no-cache` sul service worker.
```

```javascript
// Nella pagina: rilevare l'aggiornamento e proporlo all'utente
const registrazione = await navigator.serviceWorker.register('/sw.js')

registrazione.addEventListener('updatefound', () => {
  const nuovo = registrazione.installing
  if (!nuovo) return

  nuovo.addEventListener('statechange', () => {
    // 'installed' + un controller esistente = aggiornamento in
    // attesa. Senza controller, è la PRIMA installazione.
    if (nuovo.state === 'installed' && navigator.serviceWorker.controller) {
      mostraBannerAggiornamento(() => nuovo.postMessage({ tipo: 'SALTA_ATTESA' }))
    }
  })
})

// Quando il nuovo prende il controllo, si ricarica UNA volta
let ricaricato = false
navigator.serviceWorker.addEventListener('controllerchange', () => {
  if (ricaricato) return
  ricaricato = true
  location.reload()
})

// sw.js — l'attivazione immediata SOLO su richiesta della pagina
// self.addEventListener('message', (e) => {
//   if (e.data?.tipo === 'SALTA_ATTESA') self.skipWaiting()
// })
```

```
⚠ `skipWaiting()` INCONDIZIONATO È UN ERRORE. Se il nuovo service
  worker si attiva mentre una pagina vecchia è aperta, quella pagina
  comincia a ricevere risposte da una cache con asset diversi da
  quelli che ha caricato: errori di caricamento dei moduli, pezzi di
  interfaccia rotti.
  ➜ `skipWaiting` solo quando l'utente accetta, seguito da un reload.

E IL CASO OPPOSTO: se non si propone mai l'aggiornamento, chi non
chiude mai la scheda resta su una versione vecchia per settimane. Il
banner non è una cortesia: è l'unico modo di aggiornarli.
```

---
## B2. IndexedDB: lo stato che sopravvive

```
QUALE ARCHIVIO, PER COSA
  Cache API     RISPOSTE HTTP complete. Chiave: la richiesta.
  IndexedDB     DATI STRUTTURATI con indici e transazioni. Grande,
    asincrono, disponibile nel service worker.
  localStorage  ⚠ SINCRONO: blocca il main thread. Pochi kilobyte,
    solo stringhe, NON disponibile nel service worker. Per
    preferenze minuscole, nient'altro.
```

```typescript
// L'API nativa è verbosa e basata su eventi: `idb` la avvolge in
// Promise senza aggiungere peso significativo
import { openDB, type DBSchema } from 'idb'

interface SchemaCruscotto extends DBSchema {
  ordini: {
    key: string
    value: { id: string; numero: string; stato: string; aggiornatoIl: number }
    // Gli indici permettono di interrogare senza scorrere tutto
    indexes: { 'per-stato': string }
  }
  inSospeso: {
    key: number
    value: { metodo: string; url: string; corpo: unknown; creatoIl: number }
  }
}

export const db = await openDB<SchemaCruscotto>('cruscotto', 1, {
  // upgrade gira solo quando la VERSIONE cambia: è l'unico punto in
  // cui si può modificare la struttura
  upgrade(database, versionePrecedente) {
    if (versionePrecedente < 1) {
      const ordini = database.createObjectStore('ordini', { keyPath: 'id' })
      ordini.createIndex('per-stato', 'stato')
      database.createObjectStore('inSospeso', { keyPath: 'id', autoIncrement: true })
    }
  },
})
```

```
⚠ TRE TRAPPOLE DI IndexedDB
  1. LE TRANSAZIONI SI CHIUDONO DA SOLE. Una transazione resta
     aperta finché ci sono richieste in coda; un `await` su qualcosa
     che NON è una sua operazione (una fetch, un timeout) la fa
     chiudere, e la scrittura successiva fallisce.
  2. LA VERSIONE SI CAMBIA SOLO IN AVANTI, e `upgrade` deve gestire
     tutti i passaggi intermedi: un utente può tornare dopo mesi con
     la versione 1 mentre tu sei alla 4.
  3. IL BROWSER PUÒ CANCELLARE TUTTO quando lo spazio scarseggia, a
     meno di chiedere la persistenza (D2). Non è un archivio garantito.
```

---
## B3. Sincronizzazione differita e coda delle operazioni

```
IL PROBLEMA: l'utente modifica qualcosa mentre è offline. Le due
risposte sbagliate sono "l'operazione fallisce" e "l'interfaccia
finge che sia andata". La risposta giusta: si registra, si mostra
come IN SOSPESO, e si invia quando la rete torna.
```

```javascript
// sw.js — l'invio, con il ritentativo che non perde le operazioni
self.addEventListener('sync', (evento) => {
  if (evento.tag === 'invia-in-sospeso') evento.waitUntil(inviaInSospeso())
})

async function inviaInSospeso() {
  for (const operazione of await leggiInSospeso()) {
    try {
      const risposta = await fetch(operazione.url, {
        method: operazione.metodo,
        headers: {
          'Content-Type': 'application/json',
          // ⚠ La chiave di idempotenza è indispensabile: la coda può
          //    inviare due volte la stessa operazione se il sync
          //    viene ripetuto (tutorial_11 §B4)
          'Idempotency-Key': operazione.id,
        },
        body: JSON.stringify(operazione.corpo),
      })

      if (risposta.ok || (risposta.status >= 400 && risposta.status < 500)) {
        // Successo, oppure errore PERMANENTE: in entrambi i casi si
        // toglie dalla coda. Un 422 non diventerà valido riprovando.
        await rimuoviInSospeso(operazione.id)
        if (!risposta.ok) await registraFallimento(operazione, risposta.status)
      }
      // 5xx: si lascia in coda, il prossimo sync riproverà
    } catch {
      // Rete ancora assente: si interrompe e si riprova dopo
      throw new Error('rete non disponibile')
    }
  }
}
```

```
⚠ SE `inviaInSospeso` SOLLEVA, IL BROWSER RIPROVERÀ IL SYNC PIÙ
  TARDI, con un backoff proprio: per questo l'errore di rete si
  propaga invece di essere ingoiato.

⚠ LA BACKGROUND SYNC API NON È SUPPORTATA OVUNQUE (su Safari no):
  il ripiego è l'evento `online` nella pagina, e un controllo della
  coda anche all'avvio.

L'INTERFACCIA DEVE MOSTRARE LA CODA. Un utente che ha modificato
cinque ordini offline deve vedere che sono in attesa, quali sono
partiti e quali hanno fallito. Una coda invisibile produce la
domanda peggiore: "ha salvato o no?".
```

---
## B4. Notifiche push

```
   COME FUNZIONA, IN CINQUE PASSI
   1. l'utente concede il permesso
   2. il browser crea una SUBSCRIPTION presso il suo push service
      (Google, Mozilla, Apple: dipende dal browser)
   3. la subscription — un endpoint più due chiavi — si invia al tuo
      server e si salva
   4. il server invia un messaggio CIFRATO a quell'endpoint
   5. il push service sveglia il service worker, che mostra la notifica

   ⚠ Il messaggio è cifrato end-to-end: il push service lo consegna
     senza poterlo leggere. Le chiavi VAPID identificano il tuo
     server presso il push service.
```

```typescript
// La richiesta del permesso: MAI all'avvio. Chiederlo appena la
// pagina si apre è il modo più efficace di farsi negare per sempre:
// il browser ricorda il rifiuto, e non si può più chiedere.
export async function attivaNotifiche(): Promise<boolean> {
  const permesso = await Notification.requestPermission()
  if (permesso !== 'granted') return false

  const registrazione = await navigator.serviceWorker.ready
  const iscrizione = await registrazione.pushManager.subscribe({
    // Obbligatorio: ogni push deve mostrare una notifica visibile
    userVisibleOnly: true,
    applicationServerKey: chiavePubblicaVapid,
  })

  await fetch('/api/notifiche/iscrizione', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(iscrizione),
  })
  return true
}
```

```javascript
// sw.js — ricevere, mostrare, e riusare una finestra già aperta
self.addEventListener('push', (evento) => {
  const dati = evento.data?.json() ?? {}
  evento.waitUntil(
    self.registration.showNotification(dati.titolo ?? 'Aggiornamento', {
      body: dati.corpo,
      icon: '/icone/192.png',
      // `tag` sostituisce una notifica precedente invece di
      // accumularne dieci
      tag: dati.tag ?? 'generico',
      data: { url: dati.url ?? '/' },
    }),
  )
})

self.addEventListener('notificationclick', (evento) => {
  evento.notification.close()
  const url = evento.notification.data?.url ?? '/'

  evento.waitUntil(
    (async () => {
      const finestre = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      const esistente = finestre.find((f) =>
        f.url.includes(new URL(url, self.location.origin).pathname),
      )
      return esistente ? esistente.focus() : self.clients.openWindow(url)
    })(),
  )
})
```

```
LE REGOLE CHE DECIDONO SE LE NOTIFICHE FUNZIONANO O DANNEGGIANO
  ✅ permesso chiesto al momento giusto, spiegando prima · solo
     notifiche chieste e utili adesso · `tag` per sostituire invece
     di accumulare · un modo evidente di disattivarle · gestire la
     subscription SCADUTA (il push dà 404 o 410: va eliminata)
  ❌ notifiche di marketing non richieste: l'utente blocca il
     permesso, e da quel momento non riceve più nemmeno quelle utili
```

---
## B5. Web Components: quando servono davvero

```typescript
// Un custom element con Shadow DOM: lo stile è incapsulato e non
// entra in conflitto con quello della pagina ospite
class ContatoreRegressivo extends HTMLElement {
  static observedAttributes = ['scadenza']
  #intervallo?: ReturnType<typeof setInterval>

  connectedCallback() {
    const shadow = this.attachShadow({ mode: 'open' })
    shadow.innerHTML = `
      <style>:host { display: inline-block; font-variant-numeric: tabular-nums; }</style>
      <span part="valore"></span>
    `
    this.#avvia()
  }

  // ⚠ La pulizia è obbligatoria: senza, ogni elemento rimosso lascia
  //   un intervallo attivo — una perdita di memoria garantita
  disconnectedCallback() {
    clearInterval(this.#intervallo)
  }

  attributeChangedCallback() {
    this.#avvia()
  }

  #avvia() {
    clearInterval(this.#intervallo)
    const scadenza = new Date(this.getAttribute('scadenza') ?? '').getTime()
    const span = this.shadowRoot?.querySelector('span')
    if (!span || Number.isNaN(scadenza)) return

    const aggiorna = () => (span.textContent = formattaDurata(scadenza - Date.now()))
    aggiorna()
    this.#intervallo = setInterval(aggiorna, 1000)
  }
}

customElements.define('contatore-regressivo', ContatoreRegressivo)
```

```
QUANDO UN WEB COMPONENT È LA SCELTA GIUSTA
  ✅ un widget da incorporare in siti che usano framework diversi (o
     nessuno): un selettore di date condiviso fra un'app React e una
     pagina WordPress
  ✅ un design system distribuito a più team con stack diversi
  ✅ un componente che deve sopravvivere a un cambio di framework
  ✅ l'incapsulamento dello stile è un requisito vero, perché il CSS
     dell'ospite è fuori controllo

QUANDO NON LO È
  ❌ dentro un'applicazione che usa già un framework: si perdono i
     tipi, il passaggio di dati complessi diventa scomodo, e gli
     strumenti di sviluppo funzionano peggio
  ❌ quando serve rendering sul server: il Shadow DOM dichiarativo
     esiste ma è più complesso di un componente normale
  ⚠ Il passaggio di dati è per ATTRIBUTI (stringhe) o per PROPRIETÀ
    (JavaScript): oggetti e funzioni passano solo come proprietà, e
    questo va documentato per chi usa il componente.
```

---
## B6. WebAssembly: quando conviene

```
WASM ESEGUE CODICE COMPILATO (C, C++, Rust, Go) nel browser, a
velocità vicina a quella nativa. Non sostituisce JavaScript: lo
affianca per il calcolo puro.

CONVIENE QUANDO
  ✅ calcolo intenso e prolungato: elaborazione di immagini e video,
     crittografia, simulazioni fisiche, compressione
  ✅ esiste già una libreria C/C++/Rust matura da riusare
     (ffmpeg, sqlite, un motore di rendering)
  ✅ il carico di lavoro è lungo abbastanza da ammortizzare il costo
     del passaggio dei dati

NON CONVIENE QUANDO
  ❌ il lavoro è manipolazione del DOM: WASM non lo tocca, e ogni
     accesso passa da JavaScript
  ❌ le operazioni sono brevi: il passaggio dei dati fra JavaScript
     e la memoria WASM costa più del calcolo
  ❌ il modulo è grande: centinaia di kilobyte da scaricare e
     compilare pesano sul percorso critico
```

```javascript
// Il caricamento: streaming, così la compilazione comincia mentre
// il file arriva
const { instance } = await WebAssembly.instantiateStreaming(fetch('/wasm/elabora.wasm'))

// ⚠ I dati NON si passano come oggetti: si scrivono nella memoria
//    lineare del modulo e si passa un puntatore. È qui che sta il
//    costo, ed è il motivo per cui su lavori brevi WASM perde.
const puntatore = instance.exports.alloca(pixel.byteLength)
new Uint8Array(instance.exports.memory.buffer, puntatore, pixel.byteLength).set(pixel)
instance.exports.applicaFiltro(puntatore, larghezza, altezza)
```

```
⚠ E LA COMBINAZIONE CHE FUNZIONA MEGLIO: WASM DENTRO UN WEB WORKER.
  Un calcolo pesante, per quanto veloce, blocca comunque il main
  thread se gira lì. Nel worker non lo tocca, e l'interfaccia resta
  reattiva (tutorial_17 §B4).
```

---

## B7. SSE contro WebSocket contro polling

| | Polling | SSE | WebSocket |
|---|---|---|---|
| Direzione | client → server | server → client | bidirezionale |
| Riconnessione automatica | — | ✅ nativa | ❌ da scrivere |
| Attraversa proxy e firewall | ✅ sempre | ✅ quasi sempre | ⚠ a volte no |
| Costo per connessione | alto | basso | basso |
| Complessità | minima | bassa | media |

```typescript
// SSE: la riconnessione e la ripresa dal punto giusto sono NATIVE —
// ed è il motivo principale per preferirlo quando il flusso è a
// senso unico. Non serve gestire l'errore: EventSource riprova da
// solo, con backoff, inviando Last-Event-ID per riprendere.
const flusso = new EventSource('/api/eventi')

flusso.addEventListener('ordine-aggiornato', (evento) => {
  aggiornaOrdine(JSON.parse(evento.data))
})
```

```typescript
// Il server: il formato è testo, e ogni messaggio finisce con una
// riga vuota
import type { RequestHandler } from 'express'

export const flussoEventi: RequestHandler = (richiesta, risposta) => {
  risposta.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
    // ⚠ Senza questo, nginx bufferizza e i messaggi arrivano a blocchi
    'X-Accel-Buffering': 'no',
  })

  const invia = (tipo: string, dati: unknown, id: string) =>
    risposta.write(`id: ${id}\nevent: ${tipo}\ndata: ${JSON.stringify(dati)}\n\n`)

  // Un commento periodico tiene viva la connessione attraverso i
  // proxy, che chiudono quelle inattive
  const battito = setInterval(() => risposta.write(': battito\n\n'), 30_000)
  const annulla = iscrivi((e) => invia(e.tipo, e.dati, e.id))

  richiesta.on('close', () => {
    clearInterval(battito)
    annulla()
  })
}
```

```
COME SI SCEGLIE
  Il server deve solo NOTIFICARE (aggiornamenti, notifiche,
  avanzamento) → SSE: più semplice, riconnessione gratuita, passa
  ovunque.
  Servono messaggi in ENTRAMBE le direzioni con bassa latenza (chat,
  collaborazione, giochi) → WebSocket (tutorial_23).
  Gli aggiornamenti sono RARI e la latenza non conta → polling. Non
  vergognarsene: è la soluzione più semplice da mantenere.
⚠ Su HTTP/1.1 il browser limita a circa sei connessioni per dominio,
  e una SSE ne occupa una in permanenza. Su HTTP/2 il limite non c'è.
```

---
## B8. Le API moderne e la degradazione

```javascript
// LA REGOLA UNICA: si verifica la disponibilità, e si degrada.
// Nessuna API avanzata è disponibile ovunque, e nessuna deve essere
// necessaria perché la funzione base funzioni.

// Condivisione nativa, con ripiego sulla copia negli appunti
export async function condividi(dati) {
  if (navigator.share && navigator.canShare?.(dati)) {
    try {
      await navigator.share(dati)
      return 'condiviso'
    } catch (errore) {
      // AbortError = l'utente ha annullato: non è un errore
      if (errore.name === 'AbortError') return 'annullato'
    }
  }

  await navigator.clipboard.writeText(dati.url)
  return 'copiato'
}
```

```
LE ALTRE API CHE VALE LA PENA CONOSCERE
  IntersectionObserver  caricamento pigro, scorrimento infinito,
    visibilità. Disponibile ovunque.
  ResizeObserver  reagire alla dimensione di un elemento, non della
    finestra.
  AbortSignal.timeout()  annullare una fetch lenta senza scrivere il
    timer a mano.
  View Transitions  animare il passaggio fra due stati del DOM.
  File System Access  leggere e scrivere file locali con permesso.
    ⚠ Solo Chromium.
  Web Share Target  la PWA fra le destinazioni di condivisione del
    sistema.  ·  Badging  un numero sull'icona dell'app installata.

Il rilevamento si fa sulla FUNZIONALITÀ — `if ('showOpenFilePicker'
in window)` — mai sul browser.

⚠ IL SNIFFING DELLO USER AGENT È SEMPRE SBAGLIATO: la stringa si
  falsifica, cambia a ogni versione, e non dice cosa il browser sa
  fare.

E LA DOMANDA CHE PRECEDE OGNI API NUOVA: cosa succede a chi non ce
l'ha? Se la risposta è "non può usare la funzione", va bene solo se
quella funzione è un miglioramento. Se è essenziale, serve un
percorso alternativo che funzioni ovunque.
```

---

## B9. Il service worker come superficie di rischio

```
UN SERVICE WORKER È IL PEZZO DI CODICE PIÙ POTENTE E PIÙ PERSISTENTE
CHE PUOI METTERE NEL BROWSER DI UN UTENTE
  · intercetta OGNI richiesta della sua origine
  · resta installato dopo la chiusura della scheda, e sopravvive ai
    riavvii
  · si aggiorna da solo dal tuo server
  ➜ Se qualcuno riesce a farne installare uno malevolo, controlla
    l'origine finché l'utente non lo rimuove a mano.
```

```
LE CINQUE REGOLE
  1. SOLO HTTPS — è imposto dal browser, e il motivo è questo: su
     HTTP un proxy potrebbe sostituire il file del service worker.
  2. IL FILE DALLA TUA ORIGINE, e lo SCOPE limitato al suo percorso:
     un service worker in /js/ non può controllare la radice, a meno
     di un header `Service-Worker-Allowed` usato con cognizione.
  3. NON METTERE MAI IN CACHE RISPOSTE AUTENTICATE senza pensarci:
     su un dispositivo condiviso il secondo utente vede i dati del
     primo. Si escludono, o si usa una chiave che include l'utente e
     si SVUOTA al logout.
  4. VERIFICARE COSA SI METTE IN CACHE: solo `response.ok`, e mai le
     risposte opache, di cui non si conosce lo stato.
  5. SVUOTARE TUTTO AL LOGOUT — cache di dati, IndexedDB, storage e
     coda. È il passo che quasi nessuno fa, e produce la fuga più
     banale che esista (vedi l'Esercizio 3).
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Correggere un service worker che serve contenuto vecchio

**Obiettivo:** gli utenti vedono la versione di due settimane fa, e "svuota la cache" è diventata la risposta standard dell'assistenza.

```javascript
// IL CODICE DA CORREGGERE
const CACHE = 'app-cache'

self.addEventListener('install', (evento) => {
  evento.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(['/', '/app.js', '/stili.css', '/api/config'])),
  )
})

self.addEventListener('fetch', (evento) => {
  evento.respondWith(caches.match(evento.request).then((r) => r || fetch(evento.request)))
})
```

```
# LA DIAGNOSI — sei problemi
# 1. IL NOME DELLA CACHE NON HA VERSIONE: la vecchia non viene mai
#    invalidata, e il precache di un file già presente non lo aggiorna
# 2. CACHE FIRST SU TUTTO, HTML compreso: la pagina viene servita
#    dalla cache per sempre. È la causa principale.
# 3. NESSUN 'activate': le cache vecchie restano e lo spazio cresce
# 4. NESSUN skipWaiting né claim: il SW nuovo resta in attesa finché
#    l'utente non chiude TUTTE le schede
# 5. SI INTERCETTANO ANCHE LE POST: una scrittura può ricevere una
#    risposta dalla cache
# 6. `/api/config` NEL PRECACHE: un dato dinamico congelato al
#    momento dell'installazione
```

```javascript
// LA SOLUZIONE
const VERSIONE = 'v4'
const STATICA = `statica-${VERSIONE}`
const DINAMICA = `dinamica-${VERSIONE}`

// Solo ciò che è davvero statico: gli asset con impronta nel nome
// non servono nel precache, perché a parità di nome non cambiano
const PRECACHE = ['/offline.html', '/icone/192.png', '/assets/app.a3f9c2.css']

self.addEventListener('install', (evento) => {
  evento.waitUntil(caches.open(STATICA).then((c) => c.addAll(PRECACHE)))
})

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    (async () => {
      const nomi = await caches.keys()
      await Promise.all(nomi.filter((n) => !n.endsWith(VERSIONE)).map((n) => caches.delete(n)))
      await self.clients.claim()
    })(),
  )
})

// L'attivazione immediata SOLO quando la pagina la chiede
self.addEventListener('message', (evento) => {
  if (evento.data?.tipo === 'SALTA_ATTESA') self.skipWaiting()
})

self.addEventListener('fetch', (evento) => {
  const richiesta = evento.request
  if (richiesta.method !== 'GET') return
  if (new URL(richiesta.url).origin !== self.location.origin) return

  // 1. I DOCUMENTI: rete prima, con ripiego offline. Così un
  //    rilascio arriva subito.
  if (richiesta.mode === 'navigate') {
    evento.respondWith(fetch(richiesta).catch(() => caches.match('/offline.html')))
    return
  }

  // 2. LE API: mai cache first. Stale-while-revalidate solo sulle
  //    letture NON autenticate.
  if (new URL(richiesta.url).pathname.startsWith('/api/')) {
    evento.respondWith(obsoletaMentreRivalida(richiesta, DINAMICA))
    return
  }

  // 3. GLI ASSET CON IMPRONTA: cache first, sono immutabili
  evento.respondWith(cachePrima(richiesta, STATICA))
})
```

```
# LA VERIFICA
#  1. rilascia una modifica → l'HTML nuovo arriva alla prima
#     navigazione, non dopo due settimane
#  2. DevTools → Application → Cache Storage: solo le cache -v4
#  3. modalità aereo → la pagina si apre dalla cache, e le rotte non
#     visitate mostrano offline.html
#  4. una POST offline NON riceve una risposta dalla cache
#
# ⚠ Il passo che chiude davvero il problema è il banner di
#   aggiornamento nella pagina (B1): senza, chi non chiude mai la
#   scheda resta comunque indietro.
```

---
### Esercizio 2 — Rendere utilizzabile un modulo offline

**Obiettivo:** un modulo di inserimento ordine che offline fallisce con "errore di rete". Renderlo utilizzabile, con l'operazione che parte quando la rete torna.

```typescript
// IL CODICE DA CORREGGERE
async function inviaOrdine(dati: DatiOrdine) {
  const risposta = await fetch('/api/ordini', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dati),
  })
  if (!risposta.ok) throw new Error('Errore di rete')
  return risposta.json()
}
```

```typescript
// LA SOLUZIONE
export async function inviaOrdine(dati: DatiOrdine): Promise<Esito> {
  // L'identificativo si genera QUI e serve come chiave di
  // idempotenza: la stessa operazione inviata due volte dalla coda
  // non produce due ordini (tutorial_11 §B4)
  const id = crypto.randomUUID()

  try {
    const risposta = await fetch('/api/ordini', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Idempotency-Key': id },
      body: JSON.stringify(dati),
      signal: AbortSignal.timeout(8000),
    })

    if (risposta.ok) return { stato: 'inviato', dati: await risposta.json() }

    // 4xx: l'errore è nei dati, riprovare non serve
    if (risposta.status < 500) return { stato: 'rifiutato', problema: await risposta.json() }

    throw new Error('server non disponibile') // 5xx: temporaneo → coda
  } catch {
    // Rete assente, timeout o 5xx: si accoda e si conferma all'utente
    await db.add('inSospeso', { id, metodo: 'POST', url: '/api/ordini', corpo: dati, creatoIl: Date.now() })

    const registrazione = await navigator.serviceWorker.ready
    if ('sync' in registrazione) {
      await (registrazione as SyncManagerHost).sync.register('invia-in-sospeso')
    }

    return { stato: 'in_attesa', id }
  }
}
```

```tsx
// L'INTERFACCIA — la parte che rende la soluzione accettabile:
// l'utente deve SAPERE cosa è in sospeso
export function StatoSincronizzazione() {
  const [inSospeso, setInSospeso] = useState<Operazione[]>([])
  const [online, setOnline] = useState(navigator.onLine)

  useEffect(() => {
    const aggiorna = () => void db.getAll('inSospeso').then(setInSospeso)
    aggiorna()

    const { signal } = new AbortController()
    addEventListener('online', () => setOnline(true), { signal })
    addEventListener('offline', () => setOnline(false), { signal })
    // Il service worker avvisa quando ha svuotato la coda
    navigator.serviceWorker.addEventListener('message', aggiorna, { signal })
  }, [])

  if (inSospeso.length === 0 && online) return null

  return (
    <div role="status">
      {!online && <p>Sei offline. Le modifiche verranno inviate al ritorno della connessione.</p>}
      {inSospeso.length > 0 && <p>{inSospeso.length} operazioni in attesa di invio</p>}
    </div>
  )
}
```

```
# LA VERIFICA
#  1. modalità aereo → l'ordine si invia, l'interfaccia dice "in
#     attesa", e il conteggio compare
#  2. si riattiva la rete → l'ordine parte e il conteggio scende
#  3. lo stesso ordine inviato due volte dalla coda → sul server ne
#     risulta UNO, grazie alla chiave di idempotenza
#  4. un ordine con dati non validi (422) → NON entra in coda, e
#     l'errore si mostra subito
#  5. si chiude la scheda offline e si riapre online → la coda è
#     ancora lì e parte
```

---
### Esercizio 3 — Chiudere una fuga di dati fra utenti

**Obiettivo:** su un dispositivo condiviso, dopo il logout il secondo utente vede i dati del primo. Trovare tutte le cause e correggerle.

```javascript
// IL CODICE DA CORREGGERE
async function logout() {
  await fetch('/api/auth/logout', { method: 'POST' })
  localStorage.removeItem('utente')
  location.href = '/accedi'
}

// sw.js
self.addEventListener('fetch', (evento) => {
  if (evento.request.url.includes('/api/')) {
    evento.respondWith(obsoletaMentreRivalida(evento.request, 'api-cache'))
  }
})
```

```
# LA DIAGNOSI — quattro fughe
# 1. LA CACHE DELLE API resta: /api/ordini contiene gli ordini del
#    primo utente, e il secondo li vede finché la cache non scade.
#    ⚠ È la fuga principale, e la meno evidente.
# 2. INDEXEDDB resta: gli ordini salvati per l'uso offline sono lì.
# 3. LA CODA IN SOSPESO resta: le operazioni del primo utente
#    verrebbero inviate con la sessione del secondo.
# 4. `localStorage.removeItem` toglie solo una chiave: preferenze e
#    bozze restano.
```

```javascript
// LA CORREZIONE 1 — non mettere in cache ciò che dipende
// dall'identità
self.addEventListener('fetch', (evento) => {
  const richiesta = evento.request
  if (richiesta.method !== 'GET') return

  const url = new URL(richiesta.url)
  if (!url.pathname.startsWith('/api/')) return

  const PERSONALI = ['/api/ordini', '/api/profilo', '/api/notifiche']
  if (PERSONALI.some((p) => url.pathname.startsWith(p))) {
    evento.respondWith(
      // Offline si legge da IndexedDB, che viene svuotato al logout
      // — non dalla Cache API
      fetch(richiesta).catch(() => rispostaDaArchivioLocale(url.pathname)),
    )
    return
  }

  // Solo i dati pubblici restano nella cache condivisa
  evento.respondWith(obsoletaMentreRivalida(richiesta, 'api-pubblica-v1'))
})
```

```typescript
// LA CORREZIONE 2 — un logout che pulisce TUTTO
export async function logout(): Promise<void> {
  // 1. Prima il server: la sessione va invalidata comunque
  await fetch('/api/auth/logout', { method: 'POST' }).catch(() => {})

  // 2. Tutte le cache che possono contenere dati personali
  const nomi = await caches.keys()
  await Promise.all(nomi.filter((n) => !n.startsWith('statica-')).map((n) => caches.delete(n)))

  // 3. IndexedDB, compresa la coda: le operazioni del primo utente
  //    NON devono partire con la sessione del secondo
  await new Promise<void>((risolvi) => {
    const richiesta = indexedDB.deleteDatabase('cruscotto')
    richiesta.onsuccess = richiesta.onerror = richiesta.onblocked = () => risolvi()
  })

  // 4. localStorage e sessionStorage per intero
  localStorage.clear()
  sessionStorage.clear()

  // 5. Il service worker, per lo stato che tiene in memoria
  navigator.serviceWorker.controller?.postMessage({ tipo: 'LOGOUT' })

  // 6. Una navigazione COMPLETA, non di routing: azzera anche lo
  //    stato in memoria dell'applicazione
  location.href = '/accedi'
}
```

```
# LA VERIFICA — su un dispositivo, con due utenti veri
#  1. utente A accede, usa l'applicazione, va offline e torna online
#  2. utente A esce
#  3. DevTools → Application: Cache Storage senza cache di dati,
#     IndexedDB assente, Local Storage vuoto
#  4. utente B accede → non vede NIENTE di A, nemmeno offline
#  5. e la coda: se A aveva operazioni in sospeso, non partono con
#     la sessione di B
#
# ⚠ Il punto 5 è quello che quasi nessuno prova, ed è il più grave:
#   un'operazione di A eseguita con l'identità di B.
```

---
## C2. Mini-progetto: la dashboard offline

L'esercizio chiave del modulo: rendere la dashboard dei tutorial precedenti utilizzabile senza rete, con sincronizzazione al ritorno della connessione.

```
cruscotto-pwa/
├── public/  manifest.webmanifest · offline.html · icone/
├── src/     sw.ts (build separata) · offline/{db,coda,stato}.ts ·
│            registrazione-sw.ts (registrazione + banner)
└── vite.config.ts  entry separata per il service worker

LE DECISIONI DI PROGETTO
  documenti        rete prima con timeout 3 s, ripiego offline.html
  asset (impronta) cache first, per sempre
  API pubbliche    stale-while-revalidate
  API personali    rete, con ripiego su IndexedDB — MAI in Cache API
  scritture        network only, e in coda quando fallisce
  aggiornamento    banner con conferma, mai skipWaiting automatico
  logout           svuota cache non statiche, IndexedDB, storage
```

```typescript
// src/registrazione-sw.ts — registrazione e banner in un posto solo
export async function registraServiceWorker(): Promise<void> {
  if (!('serviceWorker' in navigator)) return

  const registrazione = await navigator.serviceWorker.register('/sw.js', { scope: '/' })

  // Un controllo periodico: senza, chi non ricarica mai resta
  // indietro finché il browser non decide di controllare
  setInterval(() => void registrazione.update(), 60 * 60 * 1000)

  registrazione.addEventListener('updatefound', () => {
    const nuovo = registrazione.installing
    if (!nuovo) return
    nuovo.addEventListener('statechange', () => {
      if (nuovo.state === 'installed' && navigator.serviceWorker.controller) {
        mostraBannerAggiornamento(() => nuovo.postMessage({ tipo: 'SALTA_ATTESA' }))
      }
    })
  })

  let ricaricato = false
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (ricaricato) return
    ricaricato = true
    location.reload()
  })
}
```

```
# LA VERIFICA, IN ORDINE
# 1. INSTALLABILE  Lighthouse → PWA senza errori; il pulsante di
#    installazione compare (su Chromium) e funziona
# 2. OFFLINE UTILE  modalità aereo: le pagine visitate si aprono, i
#    dati già scaricati si consultano, le rotte mai viste mostrano
#    offline.html — non l'errore del browser
# 3. LA CODA  tre modifiche offline → mostrate in attesa → rete →
#    partono in ordine → il conteggio va a zero
# 4. IDEMPOTENZA  un sync ripetuto non crea duplicati sul server
# 5. AGGIORNAMENTO  rilascia una versione nuova con la scheda
#    aperta: compare il banner, e solo dopo la conferma si ricarica
# 6. NESSUNA FUGA  due utenti sullo stesso dispositivo: il secondo
#    non vede nulla del primo, nemmeno offline
# 7. QUOTA  navigator.storage.estimate() entro limiti ragionevoli, e
#    le cache vecchie eliminate a ogni attivazione
# 8. DISINSTALLABILE  esiste un percorso per rimuovere il service
#    worker e ripulire (D4): senza, un bug diventa permanente
```

---
# Parte D — Approfondimento per Esperti

---

## D1. Risoluzione dei conflitti

```
QUANDO IL CLIENT LAVORA OFFLINE, DUE PERSONE POSSONO MODIFICARE LA
STESSA COSA. Al ritorno della rete qualcuno deve decidere.

LE QUATTRO STRATEGIE, IN ORDINE DI SEMPLICITÀ
  1. L'ULTIMO VINCE  il server accetta l'ultima scrittura. Semplice,
     e accettabile solo se il conflitto è raro e il danno lieve.
  2. RIFIUTA E CHIEDI  il server confronta la versione (ETag,
     tutorial_11 §B5) e risponde 412: il client mostra le due
     versioni e fa scegliere l'utente. ⚠ Offline questo significa
     che l'operazione resta in sospeso finché l'utente non torna.
  3. UNIONE PER CAMPO  se A ha cambiato il nome e B la scadenza, si
     applicano entrambe. Funziona quando i campi sono indipendenti,
     e va deciso campo per campo.
  4. CRDT  strutture dati che convergono per costruzione, senza un
     arbitro. Potenti (Yjs, Automerge) e con un costo di complessità
     e di dimensione notevole: si scelgono per la collaborazione in
     tempo reale, non per un modulo d'ordine.
```

```
LA DOMANDA CHE ORIENTA LA SCELTA: cosa costa un conflitto risolto
male?  Una preferenza di visualizzazione → l'ultimo vince, e nessuno
se ne accorge. Una quantità in magazzino → il server deve arbitrare,
con un aggiornamento relativo (tutorial_12 §B4). Un documento
scritto a più mani → CRDT, o modifica esclusiva.

⚠ E LA REGOLA CHE VALE SEMPRE: il server è l'autorità. Il client
  offline propone, il server dispone. Un'architettura in cui il
  client decide l'esito finale produce divergenze che nessuno sa più
  ricomporre.
```

---

## D2. Quota di archiviazione e persistenza

```javascript
// Quanto spazio c'è e quanto se ne usa. La quota è tipicamente una
// frazione dello spazio libero del disco, e cambia fra browser e
// sistemi: non va assunta.
const { usage, quota } = await navigator.storage.estimate()

// Chiedere che i dati NON vengano eliminati quando lo spazio scarseggia
const persistente = await navigator.storage?.persist?.()
```

```
COME I BROWSER DECIDONO DI CONCEDERE LA PERSISTENZA
  Non c'è una richiesta esplicita all'utente: i browser valutano
  segnali di "impegno" — l'app è installata, l'utente la visita
  spesso, ha concesso le notifiche, l'ha aggiunta ai segnalibri.
  ⚠ I criteri esatti variano fra browser e cambiano nel tempo: vanno
    verificati sulla documentazione corrente, non dati per scontati.

COSA FARE COMUNQUE, PERCHÉ LA PERSISTENZA PUÒ ESSERE NEGATA
  1. LIMITARE CIÒ CHE SI CONSERVA: un tetto al numero di elementi
     nelle cache dinamiche, con eliminazione dei più vecchi
  2. GESTIRE `QuotaExceededError`: liberare spazio e riprovare,
     invece di fallire
  3. NON TRATTARE L'ARCHIVIO LOCALE COME UNA FONTE DI VERITÀ: è una
     copia, e il server è l'originale
  4. AVVISARE L'UTENTE se ci sono operazioni in sospeso da molto
     tempo: quei dati esistono solo lì
```

```javascript
// Un limite sul numero di elementi in una cache dinamica
async function limitaCache(nome, massimo) {
  const cache = await caches.open(nome)
  const chiavi = await cache.keys()
  // Le chiavi sono in ordine di inserimento: si eliminano le più
  // vecchie
  if (chiavi.length > massimo) {
    await Promise.all(chiavi.slice(0, chiavi.length - massimo).map((c) => cache.delete(c)))
  }
}
```

---

## D3. Testare e diagnosticare un service worker

```
GLI STRUMENTI, IN ORDINE DI UTILITÀ
  DevTools → Application → Service Workers  stato corrente,
    "Update on reload" (rilegge il file a ogni ricaricamento:
    indispensabile in sviluppo), "Bypass for network", "Offline"
  DevTools → Application → Cache Storage  cosa c'è dentro ogni cache
  DevTools → Application → Storage → "Clear site data"  azzera tutto:
    la mossa da usare quando lo stato è confuso
  chrome://serviceworker-internals  tutti i service worker
    registrati, con i log e la terminazione forzata
```

```typescript
// Un test end-to-end del comportamento offline con Playwright
import { test, expect } from '@playwright/test'

test('la dashboard si apre offline con i dati già scaricati', async ({ page, context }) => {
  await page.goto('/dashboard')
  // Si aspetta che il service worker abbia preso il controllo
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null)
  await expect(page.getByRole('table')).toBeVisible()

  await context.setOffline(true)
  await page.reload()

  await expect(page.getByRole('table')).toBeVisible()
  await expect(page.getByRole('status')).toContainText(/offline/i)
})
```

```
⚠ IL PROBLEMA DI TESTARE I SERVICE WORKER: sopravvivono fra i test.
  Ogni test deve partire da un contesto PULITO — con Playwright, un
  contesto nuovo per file. Altrimenti un test eredita la cache del
  precedente, e i fallimenti diventano non riproducibili.
```

---
## D4. Disinstallare un service worker

```
IL CASO CHE NESSUNO PREVEDE E CHE PRIMA O POI CAPITA: un service
worker con un bug serve una versione rotta, e gli utenti non
riescono più a caricare il sito. Poiché intercetta tutto, non basta
correggere il server: bisogna raggiungere il codice che gira già nei
browser.
➜ Prevedere il percorso di disinstallazione PRIMA di averne bisogno,
  e servirlo allo STESSO URL del service worker esistente.
```

```javascript
// sw.js — la versione "kill switch": si pubblica al posto di quello
// rotto, e disinstalla tutto
self.addEventListener('install', () => self.skipWaiting())

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    (async () => {
      const nomi = await caches.keys()
      await Promise.all(nomi.map((n) => caches.delete(n))) // 1. le cache
      await self.registration.unregister() // 2. si rimuove

      // 3. ricarica le pagine aperte, che a quel punto vanno in rete
      const finestre = await self.clients.matchAll({ type: 'window' })
      for (const finestra of finestre) finestra.navigate(finestra.url)
    })(),
  )
})
```

```
LE DUE PRECAUZIONI CHE EVITANO DI ARRIVARCI
  1. Il file del service worker servito con `Cache-Control: no-cache`:
     un aggiornamento arriva entro la navigazione successiva, non
     dopo un giorno.
  2. Una versione di prova su un sottodominio o dietro un flag prima
     di rilasciarla a tutti. Un service worker rotto in produzione è
     l'unico bug del frontend che non si corregge con un rilascio
     normale.
E un percorso di emergenza raggiungibile a mano (per esempio
/ripristina) che chiami `getRegistrations()` e `unregister()`, utile
anche per l'assistenza.
```

---
## D5. Quando NON serve una PWA

```
UNA PWA AGGIUNGE UN LIVELLO PERMANENTE FRA IL BROWSER E IL TUO SITO.
Quel livello va mantenuto, testato, versionato e — quando si rompe —
disinstallato dai browser altrui. È un costo reale.

NON SERVE QUANDO
  ❌ il sito è consultato una volta e via: non c'è nulla da riusare
  ❌ tutto il contenuto è dinamico e personale: la cache non aiuta,
     e diventa un rischio (B9)
  ❌ l'unico obiettivo è "farla installare": un'icona in più che
     nessuno apre
  ❌ non c'è nessuno che possa mantenerla: un service worker
     abbandonato serve contenuto di due anni fa

SERVE DAVVERO QUANDO
  ✅ l'utente lavora con rete instabile: un tecnico in cantiere, un
     magazziniere, chi viaggia
  ✅ l'applicazione si usa tutti i giorni e il tempo di avvio conta
  ✅ le operazioni devono completarsi anche se la rete cade a metà
  ✅ le notifiche push sono parte del flusso di lavoro

⚠ E LA VERSIONE MINIMA È SPESSO SUFFICIENTE: un manifest per
  l'installazione e una cache degli asset statici danno l'80% del
  beneficio con il 20% del rischio. Offline completo, coda e push si
  aggiungono quando servono davvero, non "perché è una PWA".
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
PWA E TECNOLOGIE AVANZATE — Mappa dei concetti

COS'È  HTTPS + service worker + manifest, su un sito che esiste già.
  Dà offline, installazione, push, avvio istantaneo. Non dà le API
  native, e il supporto NON è uniforme.

SERVICE WORKER
├── proxy nel browser, thread separato, nessun DOM, solo HTTPS
├── ciclo: installing → waiting → activating → activated
├── ⚠ "waiting" è la causa del 90% della confusione
├── waitUntil() nei gestori · respondWith() sincrono · solo GET
└── lo scope dipende dal percorso del file: deve stare nella radice

CACHING
├── cache first (asset con impronta) · network first + timeout
│     (documenti) · stale-while-revalidate (letture) · network only
│     (scritture) · cache only (precache)
├── mai in cache: risposte non ok, opache, e tutto ciò che dipende
│     dall'identità
└── clonare la risposta: il corpo è uno stream, si consuma una volta

AGGIORNAMENTO
├── confronto byte per byte del file sw.js
├── ⚠ Cache-Control: no-cache sul service worker
├── skipWaiting SOLO su conferma dell'utente, poi un reload
└── senza banner, chi non chiude la scheda resta indietro settimane

ARCHIVIAZIONE E OFFLINE
├── Cache API (risposte) · IndexedDB (dati) · localStorage (briciole)
├── IndexedDB: transazioni che si chiudono da sole, versioni solo in
│     avanti, e il browser può cancellare tutto
├── offline utile = poter continuare a lavorare, non un errore più bello
├── coda in IndexedDB + Background Sync (ripiego su 'online')
├── chiave di IDEMPOTENZA su ogni operazione accodata
├── 4xx esce dalla coda, 5xx ci resta
└── l'interfaccia DEVE mostrare cosa è in sospeso

PUSH E API
├── permesso chiesto al momento giusto, mai all'avvio
├── userVisibleOnly obbligatorio · tag per sostituire · gestire 404/410
├── SSE per il senso unico (riconnessione nativa), WebSocket per il
│     bidirezionale, polling quando basta
└── rilevamento della FUNZIONALITÀ, mai dello user agent

RISCHIO
├── il SW intercetta tutto e sopravvive alla chiusura
├── mai in cache dati personali senza chiave per utente
├── logout: svuotare cache, IndexedDB, storage, E la coda
└── prevedere il kill switch PRIMA di averne bisogno
```

---
## Checklist di competenze

**Parte A — Basi**

- [ ] Sai cosa una PWA aggiunge e cosa non aggiunge
- [ ] Sai perché lo scope dipende dal percorso del file
- [ ] Conosci i quattro stati del ciclo di vita e dove ci si blocca
- [ ] Sai perché `waitUntil` è obbligatorio e `respondWith` va chiamato sincronamente
- [ ] Sai perché non si intercettano le POST
- [ ] Conosci le cinque strategie di caching e a cosa si applicano
- [ ] Sai perché la risposta va clonata e perché il network first ha bisogno di un timeout
- [ ] Conosci i campi del manifest che contano, e cosa fa `maskable`
- [ ] Sai perché `navigator.onLine` non basta

**Parte B — Comprensione**

- [ ] Sai come il browser scopre un aggiornamento, e perché `sw.js` non va in cache
- [ ] Sai perché `skipWaiting()` incondizionato è un errore
- [ ] Sai scegliere fra Cache API, IndexedDB e localStorage
- [ ] Conosci le tre trappole di IndexedDB
- [ ] Progetti una coda offline con idempotenza e distinzione 4xx/5xx
- [ ] Sai perché il permesso delle notifiche non si chiede all'avvio
- [ ] Sai gestire una subscription push scaduta
- [ ] Sai quando un Web Component è la scelta giusta e quando no
- [ ] Sai quando WebAssembly conviene e perché va in un worker
- [ ] Scegli fra SSE, WebSocket e polling con una motivazione
- [ ] Rilevi le funzionalità e non lo user agent
- [ ] Sai perché un service worker è una superficie di rischio

**Parte C — Pratica**

- [ ] Hai trovato le sei cause del contenuto vecchio e le hai corrette
- [ ] Hai reso un modulo utilizzabile offline, con coda e riscontro visivo
- [ ] Hai verificato che un sync ripetuto non crei duplicati
- [ ] Hai chiuso le quattro fughe di dati fra utenti, coda compresa

**Parte D — Esperto**

- [ ] Conosci le quattro strategie di risoluzione dei conflitti, e perché il server resta l'autorità
- [ ] Gestisci la quota e `QuotaExceededError`
- [ ] Sai testare il comportamento offline con un contesto pulito
- [ ] Hai previsto il percorso di disinstallazione prima di averne bisogno
- [ ] Sai dire quando una PWA non serve

---
## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Cache first sull'HTML | Gli utenti restano su una versione vecchia per settimane | Network first con timeout e ripiego |
| Nome della cache senza versione, o nessun `activate` | Le vecchie non vengono mai eliminate e lo spazio cresce | Versione nel nome, pulizia in `activate` |
| `skipWaiting()` incondizionato | Una pagina aperta riceve asset incompatibili | Solo su conferma dell'utente, poi reload |
| Nessun banner di aggiornamento | Chi non chiude la scheda resta indietro | `updatefound` + proposta + `controllerchange` |
| `sw.js` con `max-age` lungo | L'aggiornamento arriva un giorno dopo | `Cache-Control: no-cache` |
| Intercettare le POST | Una scrittura può ricevere una risposta dalla cache | Solo `method === 'GET'` |
| Mettere in cache risposte non `ok` | Un 404 servito per sempre | Verificare `ok` e `type === 'basic'` |
| Cache di risposte autenticate | Il secondo utente del dispositivo vede i dati del primo | Escluderle, o chiave per utente + svuotamento al logout |
| Logout che rimuove una chiave | Cache, IndexedDB e coda restano | Svuotare tutto, coda compresa |
| Dati dinamici nel precache | Congelati al momento dell'installazione | Solo asset statici |
| Coda senza chiave di idempotenza | Un sync ripetuto crea duplicati | `Idempotency-Key` su ogni operazione |
| 4xx lasciato in coda | Riprovato all'infinito senza mai riuscire | 4xx esce dalla coda, 5xx ci resta |
| Coda invisibile all'utente | "Ha salvato o no?" | Stato in sospeso mostrato sempre |
| Permesso notifiche all'avvio | Rifiuto permanente: non si può più chiedere | Al momento utile, con una spiegazione |
| Notifiche senza `tag` | Si accumulano a decine | `tag` per sostituire |
| Subscription scadute non rimosse | Invii verso endpoint morti | Eliminare su 404/410 |
| `navigator.onLine` come verità | Un wifi senza uscita risulta online | Una richiesta di prova con timeout |
| Sniffing dello user agent | Si falsifica, invecchia, non dice cosa il browser sa fare | Rilevamento della funzionalità |
| Nessun percorso di disinstallazione | Un service worker rotto non si corregge con un rilascio | Kill switch previsto in anticipo |
| PWA "perché fa moderno" | Un livello permanente da mantenere, senza beneficio | Manifest + cache degli asset, e basta |

---

## Troubleshooting rapido

**Il service worker nuovo non si attiva**
- Causa: resta in `waiting` perché una scheda con il vecchio è ancora aperta
- Fix: banner con `skipWaiting` su conferma; in sviluppo "Update on reload"

**Le modifiche al codice non si vedono**
- Causa: cache first sugli asset, o `sw.js` messo in cache dal server
- Fix: `no-cache` sul service worker; verificare la strategia per tipo di risorsa

**`respondWith` solleva "already used"**
- Causa: il corpo della risposta è stato consumato — è uno stream, si legge una volta
- Fix: `risposta.clone()` prima di metterla in cache

**La cache cresce senza limite, o `QuotaExceededError`**
- Causa: nessuna pulizia in `activate`, o nessun tetto sulle cache dinamiche
- Fix: eliminare le versioni vecchie; limitare le voci; `navigator.storage.persist()`

**Il secondo utente vede i dati del primo**
- Causa: risposte autenticate in una cache condivisa, o IndexedDB non svuotato
- Fix: non metterle in cache; logout che pulisce tutto, coda compresa

**Le operazioni offline non partono al ritorno della rete**
- Causa: Background Sync non supportata, o l'evento `online` non gestito
- Fix: ripiego su `online`; verificare la coda anche all'avvio della pagina

**Le notifiche push non arrivano**
- Causa: permesso negato, subscription scaduta, o chiavi VAPID non corrispondenti
- Fix: verificare `Notification.permission`; rimuovere le subscription che danno 404/410

**Il pulsante di installazione non compare**
- Causa: manifest incompleto, HTTPS assente, service worker non attivo — o Safari, dove l'evento non esiste
- Fix: Lighthouse → PWA per i requisiti mancanti; istruzioni manuali per iOS

**Il sito è irraggiungibile per gli utenti dopo un rilascio**
- Causa: service worker con un bug che intercetta tutto
- Fix: pubblicare il kill switch allo stesso URL; prevenire con `no-cache` e un rilascio graduale

---
## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_19_troubleshooting.md` | Diagnosi in produzione quando il service worker è la causa |
| `tutorial_23_websocket_security.md` | Il tempo reale bidirezionale, dove SSE non basta |
| `tutorial_17_performance_web.md` | La cache HTTP sotto quella del service worker |
| `tutorial_14_sicurezza_web.md` | Origini, HTTPS e la superficie che un service worker aggiunge |
| `tutorial_11_api_design.md` | `Idempotency-Key`, indispensabile per la coda offline |

---

## Risorse di riferimento

**Documentazione:** [MDN — Progressive web apps](https://developer.mozilla.org/docs/Web/Progressive_web_apps) · [MDN — Service Worker API](https://developer.mozilla.org/docs/Web/API/Service_Worker_API) · [web.dev — Learn PWA](https://web.dev/learn/pwa) · [Web Push Protocol (RFC 8030)](https://www.rfc-editor.org/rfc/rfc8030.html)

**Approfondimenti:** [The Service Worker Lifecycle](https://web.dev/articles/service-worker-lifecycle), il testo che chiarisce lo stato "waiting" · [Offline Cookbook](https://web.dev/articles/offline-cookbook), il catalogo delle strategie · [WebAssembly — Concepts](https://developer.mozilla.org/docs/WebAssembly/Concepts)

**Strumenti:** [Workbox](https://developer.chrome.com/docs/workbox), che implementa le strategie di questo tutorial senza scriverle a mano · [idb](https://github.com/jakearchibald/idb) · [web-push](https://github.com/web-push-libs/web-push) per il lato server · [PWA Builder](https://www.pwabuilder.com/) per manifest e icone · [Lighthouse](https://developer.chrome.com/docs/lighthouse) per i requisiti di installabilità

---

> **Fine del Tutorial 18 — PWA e Tecnologie Avanzate**
>
> Prossimo tutorial: `tutorial_19_troubleshooting.md`
