---
corso: "Sviluppo Web"
fase: "6 — Riferimenti"
modulo: "19"
titolo: "Troubleshooting e Guide Pratiche"
versione: "Chrome DevTools / Lighthouse / ESLint"
livello: "Intermedio"
prerequisiti:
  - "01-18 — Moduli precedenti"
obiettivi:
  - "Diagnosticare problemi di rendering e layout con DevTools"
  - "Risolvere errori comuni di JavaScript, TypeScript e build"
  - "Debuggare problemi di performance con Chrome Performance tab"
  - "Identificare e risolvere problemi di CORS e network"
  - "Applicare checklist di troubleshooting sistematiche"
  - "Utilizzare source maps e debugger per codice transpiled"
tag: [troubleshooting, DevTools, debugging, CORS, source-maps, diagnostica]
---

# Troubleshooting e Guide Pratiche

> **Modulo 19** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** moduli precedenti del corso
>
> Al termine di questo modulo saprai:
> 1. Diagnosticare problemi di rendering e layout con DevTools
> 2. Risolvere errori comuni di JavaScript, TypeScript e build
> 3. Debuggare problemi di performance con Chrome Performance tab
> 4. Identificare e risolvere problemi di CORS e network
> 5. Applicare checklist di troubleshooting sistematiche
> 6. Utilizzare source maps e debugger per codice transpiled
>
> **Tempo stimato:** 4-6 ore · **Livello:** Intermedio

## Idee guida
1. **Browser DevTools first stop.** Network, Console, Performance.
2. **CORS errors: read message exactly. Spesso preflight fail.**
3. **Memory leak: Performance Memory snapshot.**
4. **Network waterfall mostra render-blocking.**


## Panoramica

Il troubleshooting nello sviluppo web rappresenta una competenza trasversale che separa gli sviluppatori junior da quelli senior in modo netto. Scrivere codice funzionante è il punto di partenza; diagnosticare e risolvere problemi in ambienti complessi, sotto pressione temporale, con stack tecnologici interconnessi, e' la vera sfida quotidiana. Un bug in produzione che genera una pagina bianca per il 10% degli utenti, un memory leak che degrada le performance progressivamente, un errore CORS che blocca l'integrazione con un servizio esterno: sono situazioni che richiedono metodo, strumenti e esperienza.

Questa guida copre tre aree fondamentali. La prima parte analizza gli strumenti di debugging a disposizione dello sviluppatore web moderno, dai Browser DevTools al debugging di Node.js, passando per l'analisi del traffico di rete. La seconda parte cataloga gli errori piu' comuni sia frontend che backend, fornendo per ciascuno causa, diagnosi e soluzione. La terza parte presenta guide pratiche complete: il setup di un progetto full-stack da zero, il deployment in produzione su VPS, e la costruzione di una dashboard interna di amministrazione.

L'approccio e' orientato alla pratica. Ogni sezione contiene codice reale, comandi eseguibili e configurazioni pronte all'uso. I termini tecnici in inglese sono mantenuti quando rappresentano standard del settore (debugging, deployment, middleware, proxy), mentre le spiegazioni e il ragionamento sono in italiano.

---

## Browser DevTools

I Browser DevTools sono lo strumento primario di ogni sviluppatore frontend. Chrome DevTools, in particolare, offre un ecosistema completo di pannelli specializzati che coprono ogni aspetto dell'analisi e del debugging di un'applicazione web.

### Tab Elements

Il pannello Elements consente l'ispezione e la manipolazione live del DOM e dei CSS. La funzionalita' piu' utilizzata e' l'ispezione di un elemento tramite click destro e "Ispeziona": il pannello evidenzia il nodo DOM corrispondente e mostra tutti gli stili applicati, inclusi quelli ereditati e quelli sovrascritti.

Funzionalita' chiave:

- **Modifica live del DOM**: doppio click su qualsiasi nodo per modificare tag, attributi o contenuto testuale direttamente nel browser
- **Computed Styles**: visualizza il valore finale calcolato di ogni proprieta' CSS dopo la cascata, l'ereditarieta' e la specificita'
- **Box Model**: rappresentazione visiva di margin, border, padding e content area con valori numerici editabili
- **Event Listeners**: lista completa di tutti gli event listener registrati su un elemento, con link al codice sorgente
- **Forced States**: simulazione di pseudo-classi come `:hover`, `:focus`, `:active` senza dover interagire fisicamente con l'elemento
- **DOM Breakpoints**: interruzione dell'esecuzione JavaScript quando un nodo viene modificato, rimosso o quando cambiano i suoi attributi

```
// Trucco utile: selezionare un elemento nel pannello Elements
// e accedervi dalla Console con $0
$0.style.border = '2px solid red';
$0.getBoundingClientRect();

// $1, $2, $3, $4 fanno riferimento agli elementi selezionati precedentemente
```

### Tab Console

La Console e' il punto di interazione diretta con il runtime JavaScript della pagina. Oltre al classico `console.log()`, offre metodi avanzati spesso sottoutilizzati:

```javascript
// Raggruppamento logico dei log
console.group('Inizializzazione App');
console.log('Caricamento configurazione...');
console.log('Connessione al database...');
console.groupEnd();

// Tabelle per dati strutturati
console.table([
  { nome: 'Mario', ruolo: 'Admin', attivo: true },
  { nome: 'Lucia', ruolo: 'Editor', attivo: false },
]);

// Misurazione tempi di esecuzione
console.time('fetchUtenti');
await fetch('/api/utenti');
console.timeEnd('fetchUtenti'); // fetchUtenti: 142.3ms

// Contatore di invocazioni
function handleClick() {
  console.count('click'); // click: 1, click: 2, click: 3...
}

// Asserzioni condizionali — logga solo se la condizione e' false
console.assert(utenti.length > 0, 'Lista utenti vuota!');

// Stack trace esplicito
console.trace('Punto di esecuzione raggiunto');
```

La Console supporta anche **Live Expressions** (icona dell'occhio), che valutano un'espressione in tempo reale senza inquinare il log. Utile per monitorare valori come `document.activeElement` o `performance.now()`.

### Tab Network

Il pannello Network registra ogni richiesta HTTP effettuata dalla pagina. E' fondamentale per diagnosticare problemi di comunicazione client-server, tempi di caricamento e configurazioni errate.

Elementi da analizzare per ogni richiesta:

- **Status Code**: 200 (successo), 301/302 (redirect), 400 (bad request), 401 (non autenticato), 403 (non autorizzato), 404 (non trovato), 500 (errore server)
- **Timing Breakdown**: DNS Lookup, TCP Connection, TLS Handshake, Time to First Byte (TTFB), Content Download
- **Headers**: Request Headers (cosa invia il client) e Response Headers (cosa risponde il server), fondamentali per debugging CORS, cache e autenticazione
- **Payload/Preview**: corpo della richiesta (per POST/PUT) e corpo della risposta
- **Initiator**: il file e la riga di codice che hanno generato la richiesta

Filtri essenziali:

```
// Filtrare per tipo di risorsa
XHR    — richieste AJAX/fetch
JS     — file JavaScript
CSS    — fogli di stile
Img    — immagini
Font   — web font
WS     — connessioni WebSocket

// Filtrare per testo nella URL
/api/   — mostra solo chiamate API
.chunk. — mostra solo chunk JavaScript
```

La checkbox **Preserve log** mantiene il registro anche dopo navigazione o refresh, essenziale per debugging di redirect. **Disable cache** forza il download di tutte le risorse, simulando la prima visita di un utente.

### Tab Performance

Il pannello Performance registra un profilo temporale dettagliato di tutto cio' che accade nel browser: parsing HTML, esecuzione JavaScript, calcolo stili, layout, paint e compositing.

Procedura di profiling:

1. Aprire il pannello Performance
2. Fare click sul pulsante di registrazione (cerchio)
3. Eseguire l'azione da analizzare (scroll, click, navigazione)
4. Fermare la registrazione
5. Analizzare il flame chart risultante

Il flame chart mostra la call stack nel tempo. Le barre larghe indicano funzioni che occupano molto tempo del main thread. La sezione **Main** evidenzia i Long Tasks (operazioni superiori a 50ms) con un triangolo rosso nell'angolo.

Metriche da monitorare:

- **Total Blocking Time (TBT)**: tempo totale in cui il main thread e' bloccato
- **Frames per Second (FPS)**: il grafico verde in alto dovrebbe restare vicino a 60fps
- **Layout Shifts**: spostamenti imprevisti di elementi durante il caricamento

### Tab Application

Il pannello Application gestisce lo storage locale e le risorse dell'applicazione:

- **Local Storage / Session Storage**: visualizzazione, modifica e cancellazione di coppie chiave-valore
- **Cookies**: ispezione di tutti i cookie con dettagli su dominio, path, scadenza, flag Secure/HttpOnly/SameSite
- **IndexedDB**: navigazione dei database locali con possibilita' di cancellare store o record specifici
- **Service Workers**: stato di registrazione, aggiornamento forzato, simulazione offline
- **Cache Storage**: contenuti delle cache gestite dai Service Worker
- **Manifest**: validazione del Web App Manifest per PWA

### Tecniche di Debugging Avanzate

```javascript
// Breakpoint condizionale: interrompe solo se la condizione e' vera
// Click destro sulla riga nel pannello Sources > "Add conditional breakpoint"
// Condizione: user.id === 42

// Logpoint: logga senza modificare il codice sorgente
// Click destro sulla riga > "Add logpoint"
// Messaggio: "Utente corrente:", user.name

// Blackboxing: esclude librerie di terze parti dallo step-through
// Sources > click destro su file > "Add script to ignore list"
// Ignora node_modules, React internals, ecc.

// Override locali: modifica file serviti dalla rete senza toccare il server
// Sources > Overrides > Seleziona cartella locale
// Modifica i file direttamente nel browser, le modifiche persistono tra i refresh

// Emulazione dispositivo: simula viewport mobile, DPR, touch, geolocalizzazione
// Toggle Device Toolbar (Ctrl+Shift+M)
// Throttling di rete e CPU per simulare dispositivi lenti
```

### Chrome DevTools — Performance Panel: Analisi Approfondita

Il pannello Performance merita un'analisi piu' dettagliata perche' e' lo strumento primario per diagnosticare problemi di rendering, jank visivo e reattivita' degradata. La schermata iniziale mostra le **Live Metrics**, che forniscono un riepilogo immediato delle performance basato sui tre Core Web Vitals: Largest Contentful Paint (LCP), Cumulative Layout Shift (CLS) e Interaction to Next Paint (INP).

**Configurazione ottimale prima della registrazione:**

```
1. Aprire le impostazioni del pannello Performance (icona ingranaggio)
2. Abilitare "CPU throttling" a 4x o 6x slowdown
   → Simula dispositivi con CPU meno potente
   → Fondamentale perche' il tuo MacBook Pro non rappresenta l'utente medio
3. Abilitare "Network throttling" su "Fast 3G" o "Slow 3G"
   → Rivela problemi che non appaiono su connessioni veloci
4. Selezionare "Screenshots" per catturare frame visivi durante la registrazione
5. Abilitare "Web Vitals" per evidenziare LCP, CLS e INP nel timeline
```

**Lettura del flame chart:**

Il flame chart e' organizzato in tracce orizzontali (tracks). Le tracce principali sono:

- **Network**: mostra le richieste HTTP con la loro durata, dimensione e priorita'. Le barre colorate indicano il tipo di risorsa (blu = HTML, arancione = JS, verde = CSS, viola = immagini). Richieste lunghe all'inizio del waterfall sono spesso render-blocking.
- **Frames**: indica il frame rate raggiunto. Zone rosse (sotto 60fps) segnalano jank visivo. Zone verdi indicano rendering fluido.
- **Timings**: evidenzia i marker Web Vitals (FP, FCP, LCP) con linee verticali. La distanza tra FCP e LCP indica quanto tempo passa dal primo contenuto visibile all'elemento piu' grande.
- **Main**: la traccia piu' importante. Mostra tutto cio' che accade sul main thread. Le barre larghe sono funzioni costose. I triangoli rossi nell'angolo superiore destro indicano Long Tasks (>50ms). Tasks gialli sono JavaScript, viola sono rendering/layout, verde sono paint.

**Analisi delle attivita':**

DevTools offre tre viste tabulari per analizzare le attivita' registrate:

- **Call Tree**: mostra le attivita' radice che causano piu' lavoro. Utile per capire quali funzioni inizializzano catene costose.
- **Bottom-Up**: mostra le attivita' dove il tempo e' stato speso direttamente. Utile per identificare le funzioni leaf che consumano piu' CPU.
- **Event Log**: mostra le attivita' nell'ordine cronologico in cui si sono verificate. Utile per ricostruire la sequenza di eventi che porta a un problema.

**Identificare Layout Thrashing:**

```javascript
// ERRATO — causa layout thrashing: lettura e scrittura alternate forzano
// il browser a ricalcolare il layout ad ogni iterazione
const elements = document.querySelectorAll('.card');
elements.forEach((el) => {
  const height = el.offsetHeight; // lettura → forza layout
  el.style.height = `${height + 10}px`; // scrittura → invalida layout
});

// CORRETTO — batch read, poi batch write
const elements = document.querySelectorAll('.card');
const heights = Array.from(elements).map((el) => el.offsetHeight); // tutte le letture
elements.forEach((el, i) => {
  el.style.height = `${heights[i] + 10}px`; // tutte le scritture
});
```

Nel flame chart, il layout thrashing si manifesta come una sequenza rapida di blocchi viola (Recalculate Style + Layout) intervallati da JavaScript giallo, tutti all'interno dello stesso task.

**Garbage Collection (GC) nel Performance Panel:**

Eventi GC frequenti e lunghi indicano memory pressure. Nel flame chart appaiono come blocchi etichettati "Minor GC" o "Major GC". Se i GC sono frequenti (piu' di 5-10 al secondo) e durano piu' di qualche millisecondo, il codice sta creando e distruggendo troppi oggetti temporanei. Questo suggerisce memory leak o pattern di allocazione inefficienti come la creazione di oggetti dentro loop stretti o callback ad alta frequenza (scroll handler, animation frame).

### Chrome DevTools — Memory Panel: Diagnosi Avanzata

Il pannello Memory offre tre modalita' di cattura per analizzare l'utilizzo della memoria:

**1. Heap Snapshot:**

Fotografia completa dell'heap JavaScript in un dato istante. Mostra tutti gli oggetti in memoria con dimensione, tipo e riferimenti. I due utilizzi principali sono:

- **Shallow Size vs Retained Size**: la Shallow Size e' la memoria occupata direttamente dall'oggetto. La Retained Size include anche tutti gli oggetti che verrebbero garbage-collected se l'oggetto fosse rimosso. Un oggetto con Shallow Size piccola ma Retained Size grande sta trattenendo un albero di riferimenti.
- **Comparison view**: dopo aver preso due snapshot, la vista Comparison mostra gli oggetti aggiunti e rimossi tra i due. Oggetti che crescono senza giustificazione tra uno snapshot e l'altro sono candidati per memory leak.

**2. Allocation Timeline:**

Registra le allocazioni di memoria nel tempo. Ogni barra blu indica un'allocazione; le barre che rimangono blu (non diventano grigie) al termine della registrazione rappresentano oggetti non garbage-collected. Utile per identificare *quando* durante l'esecuzione avvengono le allocazioni problematiche.

**3. Allocation Profiler (Allocation Sampling):**

Versione a basso overhead dell'Allocation Timeline, adatta per sessioni di profiling lunghe in produzione. Campiona le allocazioni invece di registrarle tutte, riducendo l'impatto sulle performance dell'applicazione.

**Identificare Detached DOM Trees:**

I DOM tree detached sono una causa comune di memory leak. Elementi rimossi dal DOM visibile ma ancora referenziati da JavaScript non possono essere garbage-collected.

```javascript
// Nella Console di DevTools, dopo aver preso un Heap Snapshot:
// 1. Cercare "Detached" nel filtro della vista Summary
// 2. Espandere ogni "Detached HTMLDivElement" per vedere il retainer chain
// 3. Il retainer chain mostra quale variabile JS tiene il riferimento

// Esempio di detached DOM tree:
let cachedElement = null;

function showModal() {
  const modal = document.createElement('div');
  modal.innerHTML = '<p>Contenuto modale</p>';
  document.body.appendChild(modal);
  cachedElement = modal; // riferimento mantenuto!
}

function hideModal() {
  cachedElement.remove(); // rimosso dal DOM visibile
  // Ma cachedElement tiene ancora il riferimento → memory leak
  // Soluzione: cachedElement = null;
}
```

**Event Listener come fonte di leak:**

Il pannello Memory permette di identificare event listener non rimossi. Nella sezione Event Listeners del pannello Elements, si possono vedere tutti i listener registrati su un elemento. Rimuovere listener non necessari puo' ridurre il consumo di memoria fino al 30% in applicazioni complesse con molti componenti dinamici.

### Chrome DevTools — Network Throttling e Simulazione

Il Network panel offre funzionalita' avanzate di throttling che vanno oltre i preset predefiniti:

**Profili di throttling personalizzati:**

```
1. Aprire il Network panel
2. Cliccare sul dropdown "No throttling"
3. Selezionare "Add custom profile..."
4. Definire: Download (kb/s), Upload (kb/s), Latency (ms)

Profili utili:
- "Utente medio Italia" → Download: 7000, Upload: 2000, Latency: 50ms
- "3G degradato"        → Download: 400, Upload: 400, Latency: 400ms
- "Satellite"           → Download: 1000, Upload: 256, Latency: 600ms
- "Edge rurale"         → Download: 200, Upload: 100, Latency: 800ms
```

**Request Blocking:**

La funzionalita' di Request Blocking (accessibile tramite Cmd+Shift+P > "Show Request Blocking") permette di bloccare richieste specifiche per testare il comportamento dell'applicazione quando risorse critiche non sono disponibili:

```
// Pattern di blocco utili:
*.js       — blocca tutti i JavaScript (testa il progressive enhancement)
*analytics* — blocca script di analytics (testa le performance senza tracking)
/api/*     — blocca tutte le chiamate API (testa gli stati di errore)
*.woff2    — blocca i font (testa il font fallback)
```

### Lighthouse: Audit Automatizzato Completo

Lighthouse, integrato direttamente in Chrome DevTools, esegue audit automatici su cinque categorie: Performance, Accessibility, Best Practices, SEO e Progressive Web App.

**Configurazione dell'audit:**

```
1. Aprire il pannello Lighthouse in Chrome DevTools
2. Selezionare le categorie da auditare (tutte raccomandate per un audit completo)
3. Scegliere il dispositivo: Mobile (piu' restrittivo, raccomandato) o Desktop
4. Cliccare "Analyze page load"
```

**Metriche Performance di Lighthouse:**

| Metrica | Target | Significato |
|---------|--------|-------------|
| FCP (First Contentful Paint) | < 1.8s | Primo pixel di contenuto visibile |
| LCP (Largest Contentful Paint) | < 2.5s | Elemento piu' grande completamente renderizzato |
| TBT (Total Blocking Time) | < 200ms | Somma dei blocchi del main thread > 50ms |
| CLS (Cumulative Layout Shift) | < 0.1 | Spostamenti imprevisti del layout |
| SI (Speed Index) | < 3.4s | Velocita' con cui il contenuto diventa visivamente completo |

**Interpretare i risultati:**

Ogni finding include una descrizione del problema, l'impatto stimato e un link alla documentazione. I finding sono ordinati per impatto potenziale: risolvere i primi 3-5 problemi tipicamente produce il miglioramento piu' significativo. I "Passed Audits" confermano le best practice gia' rispettate.

**Lighthouse CI per pipeline:**

```bash
# Installazione
npm install -g @lhci/cli

# Configurazione lhci
# lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000/', 'http://localhost:3000/dashboard'],
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:seo': ['warn', { minScore: 0.8 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};

# Esecuzione nella pipeline CI
lhci autorun
```

---

## Errori Comuni Frontend

### Errori CORS (Cross-Origin Resource Sharing)

L'errore CORS e' probabilmente il piu' frustrante per gli sviluppatori web, perche' il codice funziona perfettamente in locale ma fallisce quando frontend e backend sono su domini diversi.

**Messaggio tipico:**
```
Access to fetch at 'https://api.example.com/data' from origin 'https://app.example.com'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
on the requested resource.
```

**Causa:** il browser implementa la Same-Origin Policy come meccanismo di sicurezza. Quando il frontend (origin A) fa una richiesta a un server diverso (origin B), il browser invia prima una richiesta preflight OPTIONS per verificare che il server accetti richieste cross-origin.

**Soluzione backend (Express):**

```javascript
import cors from 'cors';

// Configurazione corretta — NON usare '*' con credenziali
app.use(cors({
  origin: ['https://app.example.com', 'http://localhost:3000'],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true, // necessario per cookie cross-origin
  maxAge: 86400,     // cache preflight per 24 ore
}));
```

**Errore comune:** usare `origin: '*'` insieme a `credentials: true` causa un errore specifico. Quando si inviano cookie o header Authorization, l'origin deve essere esplicito.

**Soluzione con proxy in sviluppo (Vite):**

```typescript
// vite.config.ts — elimina il problema CORS in sviluppo
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:4000',
        changeOrigin: true,
      },
    },
  },
});
```

### Risorse 404 (Not Found)

**Sintomi:** immagini rotte, CSS non caricato, JavaScript che non si esegue, font mancanti.

**Cause comuni e soluzioni:**

```
1. Path relativo vs assoluto
   ERRATO:  <img src="logo.png">         (relativo alla pagina corrente)
   CORRETTO: <img src="/images/logo.png"> (relativo alla root)

2. Case sensitivity sul server Linux
   ERRATO:  import Header from './header'  (il file si chiama Header.tsx)
   CORRETTO: import Header from './Header'

3. Base path errato in SPA con subroute
   // vite.config.ts
   export default defineConfig({
     base: '/app/', // necessario se l'app non e' servita dalla root
   });

4. Asset non incluso nella build
   // File nella cartella public/ sono copiati as-is
   // File in src/assets/ devono essere importati esplicitamente
   import logo from './assets/logo.svg'; // Vite gestisce hash e path
```

### Errori JavaScript Runtime

```javascript
// TypeError: Cannot read properties of undefined (reading 'map')
// Causa: dati non ancora caricati o risposta API con struttura diversa dall'atteso

// ERRATO
const users = data.users.map(u => u.name);

// CORRETTO — defensive programming
const users = data?.users?.map(u => u.name) ?? [];

// ReferenceError: X is not defined
// Causa: variabile non dichiarata, import mancante, typo nel nome

// Uncaught SyntaxError: Unexpected token '<'
// Causa: il server restituisce HTML (tipicamente la pagina 404) invece di JavaScript
// Soluzione: verificare che il path del bundle sia corretto e che il server
// gestisca correttamente il routing per SPA (historyApiFallback)

// RangeError: Maximum call stack size exceeded
// Causa: ricorsione infinita
// Debug: console.trace() nel punto sospetto per ispezionare la call stack
```

### Debugging JavaScript Avanzato: Source Maps, Breakpoint e Logpoint

**Source Maps — Debugging di codice transpiled:**

Quando si usa TypeScript, JSX o bundler come Vite/Webpack, il codice eseguito dal browser e' molto diverso dal codice sorgente. Le source maps creano la mappatura tra codice sorgente originale e codice trasformato, permettendo di debuggare nel formato leggibile.

```javascript
// In Vite, le source maps sono abilitate di default in development
// Per abilitarle esplicitamente:
// vite.config.ts
export default defineConfig({
  build: {
    sourcemap: true, // 'inline' | 'hidden' | true
    // 'hidden' genera la source map ma non aggiunge il commento di riferimento
    // nel bundle — utile per error tracking senza esporre il codice sorgente
  },
});

// In Webpack:
// webpack.config.js
module.exports = {
  devtool: 'source-map',        // produzione: mappa esterna separata
  // devtool: 'eval-source-map', // sviluppo: piu' veloce, in-memory
};
```

**Verifica source maps nel browser:**

```
1. Aprire il pannello Sources in DevTools
2. Nel file tree a sinistra, cercare la sezione "Authored" o "webpack://"
3. I file originali (.ts, .tsx, .vue) dovrebbero apparire nella struttura originale
4. Se non appaiono: verificare che il file .map sia servito correttamente
   → Controllare nel Network tab che il .map venga scaricato (status 200)
   → Controllare che il bundle contenga il commento:
     //# sourceMappingURL=main.js.map
```

**Breakpoint condizionali — casi d'uso avanzati:**

I breakpoint condizionali interrompono l'esecuzione solo quando una condizione JavaScript e' vera. Sono essenziali per debuggare loop, callback ad alta frequenza o problemi che si manifestano solo con dati specifici.

```javascript
// Click destro sulla riga nel pannello Sources > "Add conditional breakpoint"

// Esempi di condizioni utili:
// Fermare solo per un utente specifico:
user.id === 42

// Fermare solo alla N-esima iterazione di un loop:
i === 99

// Fermare solo quando un valore e' inaspettato:
response.status !== 200

// Fermare solo per errori specifici:
error.code === 'ECONNREFUSED'

// Fermare solo quando una collection supera una dimensione:
items.length > 1000
```

**Logpoint — logging senza modificare il codice:**

I Logpoint sono un'alternativa ai breakpoint che non interrompono l'esecuzione ma stampano un messaggio nella Console. Sono perfetti per il debugging non intrusivo di codice in produzione o di librerie di terze parti che non si vogliono modificare.

```javascript
// Click destro sulla riga nel pannello Sources > "Add logpoint"

// Sintassi: il messaggio e' un template string con espressioni tra {}

// Esempi:
// "Utente {user.name} ha ruolo {user.role}"
// "Risposta API: status={response.status}, body={JSON.stringify(data)}"
// "Tempo di esecuzione: {performance.now() - startTime}ms"
// "Array ha {items.length} elementi, primo={items[0]?.id}"

// I logpoint appaiono nella Console con un'icona arancione diversa
// dai normali console.log, rendendo facile distinguerli
```

**Debugging di codice asincrono:**

```javascript
// Il pannello Sources mostra la call stack completa per codice asincrono
// quando "Async" e' abilitato nella sezione Call Stack

// Per debuggare Promise rejection non gestite:
// 1. Aprire Sources > Breakpoints panel (a destra)
// 2. Nella sezione "Event Listener Breakpoints"
// 3. Espandere "Script" > selezionare "Uncaught Exceptions"
// 4. Opzionale: selezionare anche "Caught Exceptions" per vedere
//    tutte le eccezioni, incluse quelle gestite

// Per debuggare timing specifici:
// Event Listener Breakpoints > Timer > setTimeout fired / setInterval fired
// Utile per capire quale timer sta causando comportamenti inaspettati
```

### Problemi di Layout CSS

```css
/* Elemento che non si centra */
/* Verifica che il container abbia dimensioni definite */
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh; /* spesso dimenticato — senza altezza, niente centratura verticale */
}

/* Overflow orizzontale inaspettato */
/* Causa comune: elemento con width: 100% + padding/border */
* {
  box-sizing: border-box; /* risolve il 90% dei problemi di dimensionamento */
}

/* z-index che non funziona */
/* z-index richiede un positioning context (position: relative/absolute/fixed/sticky) */
.modal {
  position: fixed; /* senza position, z-index e' ignorato */
  z-index: 1000;
}

/* Flexbox: item che non si restringono */
.flex-item {
  min-width: 0; /* override del min-width: auto di default */
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Grid: colonne che non si adattano */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));
}
```

### Debugging CSS: Specificita', Stacking Context e Layout Avanzato

**Debugging della specificita' CSS:**

La specificita' CSS e' la causa piu' frequente di stili che "non si applicano". La cascata segue un ordine di priorita' preciso: inline styles > ID selectors > class/attribute/pseudo-class selectors > element/pseudo-element selectors.

```css
/* Esempio di conflitto di specificita' */

/* Specificita': 0-1-0 (una classe) */
.button { color: blue; }

/* Specificita': 0-1-1 (una classe + un elemento) — VINCE */
div.button { color: red; }

/* Specificita': 0-2-0 (due classi) — VINCE su entrambi */
.container .button { color: green; }

/* Specificita': 1-0-0 (un ID) — VINCE su tutto il resto */
#submit-btn { color: purple; }
```

**Strumenti di diagnosi della specificita':**

```
1. Nel pannello Elements di DevTools, selezionare l'elemento problematico
2. Nel pannello Styles a destra, gli stili sono ordinati per specificita'
3. Gli stili sovrascritti appaiono barrati con il nome del file sorgente
4. Passando il mouse su un selettore, DevTools mostra la specificita' calcolata
   come tupla (a, b, c) dove a=ID, b=classi, c=elementi

Regola pratica per evitare guerre di specificita':
- Usare una metodologia come BEM (.block__element--modifier)
- Evitare selettori ID nel CSS (usare classi)
- Evitare !important (quasi sempre indica un problema architetturale)
- Se necessario !important, documentare il motivo
- Usare :where() per selettori a specificita' zero
```

**Z-Index e Stacking Context:**

Il z-index e' una delle proprieta' CSS piu' fraintese. Il problema non e' quasi mai il valore numerico — e' il contesto di stacking.

Un nuovo stacking context e' creato da un elemento con:
- `position: fixed` o `position: sticky`
- `position: absolute` o `relative` con `z-index` diverso da `auto`
- `opacity` inferiore a 1
- `transform` diverso da `none`
- `filter` diverso da `none`
- `clip-path` diverso da `none`
- `isolation: isolate`
- `will-change` con valore che crea un nuovo contesto
- `contain: paint` o `contain: layout`

```css
/* PROBLEMA COMUNE: z-index non funziona tra stacking context diversi */

.header {
  position: relative;
  z-index: 100;
  /* Crea uno stacking context — tutti i figli sono confinati dentro */
}

.header .dropdown {
  position: absolute;
  z-index: 999999;
  /* NON apparira' sopra .modal se .modal ha un z-index > 100
     al livello del suo stacking context */
}

.modal {
  position: fixed;
  z-index: 200;
  /* Vince su .header (z-index 100) al livello root
     → il dropdown con z-index 999999 e' irrilevante */
}
```

**Diagnosi degli stacking context:**

```
1. Installare l'estensione "CSS Stacking Context Inspector" per Chrome/Firefox
2. L'estensione mostra la gerarchia dei contesti di stacking
3. Per ogni elemento si puo' vedere:
   - Il contesto padre
   - Se l'elemento crea un nuovo contesto
   - Il z-index effettivo nel contesto corrente

Approccio manuale:
1. Identificare l'elemento con z-index che non funziona
2. Risalire gli antenati nel DOM fino a trovare quello che crea lo stacking context
3. Confrontare il z-index dello stacking context con quello dell'elemento
   che deve apparire sotto/sopra
4. Risolvere al livello del contesto, non del figlio
```

**Soluzione moderna con `isolation`:**

```css
/* La proprieta' isolation crea uno stacking context esplicito
   senza effetti collaterali su opacity, transform o filter */
.component {
  isolation: isolate;
  /* Crea un contesto di stacking contenuto
     → previene z-index leakage tra componenti */
}

/* Particolarmente utile in architetture a componenti (React, Vue)
   dove ogni componente dovrebbe avere il proprio contesto */
```

**Debugging di Flexbox e Grid:**

Chrome DevTools offre strumenti visuamente ricchi per debuggare layout Flexbox e Grid:

```
Flexbox Inspector:
1. Selezionare un elemento flex nel pannello Elements
2. Cliccare il badge "flex" che appare accanto al tag
3. L'overlay mostra:
   - Direzione del flusso (main axis / cross axis)
   - Distribuzione dello spazio (justify-content / align-items)
   - Dimensione dei flex item con calcolo di flex-grow/shrink/basis

Grid Inspector:
1. Selezionare un elemento grid nel pannello Elements
2. Cliccare il badge "grid" per attivare l'overlay
3. L'overlay mostra:
   - Linee di griglia numerate
   - Gap tra celle
   - Aree nominate
   - Posizionamento degli item nelle celle
4. Nelle impostazioni dell'overlay, abilitare:
   - "Show track sizes" per le dimensioni delle tracce
   - "Show area names" per le aree CSS Grid nominate
   - "Extend grid lines" per estendere le linee oltre la griglia
```

### Hydration Mismatch (SSR)

Quando si usa Server-Side Rendering (Next.js, Nuxt, Remix), il server genera HTML statico che il client deve "idratare" collegando gli event listener React/Vue al DOM esistente. Se il DOM generato dal server differisce da quello che il client si aspetta, si verifica un hydration mismatch.

```javascript
// ERRATO — genera HTML diverso tra server e client
function Timestamp() {
  return <p>Generato alle {new Date().toLocaleTimeString()}</p>;
  // Il server genera un timestamp, il client un altro → mismatch
}

// CORRETTO — renderizzare valori dinamici solo lato client
function Timestamp() {
  const [time, setTime] = useState<string | null>(null);

  useEffect(() => {
    setTime(new Date().toLocaleTimeString());
  }, []);

  if (!time) return <p>Caricamento...</p>; // placeholder identico al server
  return <p>Generato alle {time}</p>;
}

// Altre cause comuni:
// - Estensioni del browser che modificano il DOM (ad blocker, traduttori)
// - Condizioni basate su window/localStorage (non disponibili sul server)
// - Rendering condizionale basato su typeof window !== 'undefined'
```

### Debugging Pagina Bianca

Una pagina completamente bianca e' uno degli scenari piu' stressanti. Procedura sistematica:

```
1. Aprire la Console del browser
   → Errori JavaScript rossi? Se si, il bundle non si carica o un errore
     blocca il rendering.

2. Controllare il tab Network
   → Il file HTML viene caricato? (status 200)
   → I bundle JS vengono caricati? (controllare status e dimensioni)
   → Errori CORS su risorse critiche?

3. Verificare il punto di mount React/Vue
   → L'elemento #root o #app esiste nell'HTML?
   → Il bundle viene caricato DOPO l'elemento nel DOM?

4. Controllare le variabili d'ambiente
   → In Vite: devono iniziare con VITE_ per essere esposte al client
   → Mancano variabili critiche come l'URL dell'API?

5. Verificare il routing
   → Il server gestisce il fallback per SPA?
   → Nginx: try_files $uri $uri/ /index.html;

6. Provare in modalita' incognito
   → Esclude estensioni del browser e cache corrotta

7. Controllare la build
   → Eseguire npm run build localmente
   → Verificare che la cartella dist/ contenga i file attesi
```

### React DevTools: Debugging di Componenti e Performance

React DevTools e' un'estensione browser che aggiunge due pannelli dedicati: **Components** e **Profiler**. Sono strumenti indispensabili per diagnosticare problemi specifici di React che non emergono dai DevTools standard del browser.

**Components Panel:**

Il pannello Components mostra l'albero completo dei componenti React con la loro gerarchia. Selezionando un componente, il pannello destro mostra:

- **Props**: tutte le props ricevute dal componente padre, con valori editabili per test rapidi
- **State**: lo stato interno del componente (useState, useReducer), editabile in tempo reale
- **Hooks**: elenco di tutti gli hook utilizzati con i loro valori correnti
- **Rendered by**: quale componente ha renderizzato quello selezionato
- **Source**: link diretto al file sorgente del componente

```
Funzionalita' chiave:
1. Ricerca componenti: Ctrl+F nel pannello per cercare per nome
2. Filtro componenti: icona filtro per nascondere componenti di terze parti
   → Settings > Components > "Hide components where..."
   → Filtrare per nome (es. nascondere tutti i componenti di react-router)
3. Sospensione componenti: click destro > "Suspend this component"
   → Testa il comportamento dei Suspense boundary
4. Inspect DOM element: click destro > "Inspect matching DOM element"
   → Salta al nodo DOM reale nel pannello Elements standard
5. Log component data: click destro > "Log this component's data"
   → Logga props, state e hooks nella Console per ispezione dettagliata
```

**Profiler Panel:**

Il Profiler registra le sessioni di rendering per identificare componenti che si re-renderizzano troppo spesso o troppo lentamente.

```
Configurazione essenziale:
1. Nelle impostazioni del Profiler (icona ingranaggio):
   → Abilitare "Record why each component rendered while profiling"
   → Questa opzione trasforma il Profiler in uno strumento diagnostico
     che spiega la CAUSA di ogni re-render
2. Avviare la registrazione (pulsante cerchio blu)
3. Interagire con l'applicazione (click, input, navigazione)
4. Fermare la registrazione

Analisi dei risultati:
- Il "Flamegraph" mostra i componenti renderizzati per ogni commit
- Componenti grigi NON si sono re-renderizzati (buona performance)
- Componenti colorati SI sono re-renderizzati:
  → Giallo/arancione = tempo di rendering significativo
  → Verde/azzurro = tempo di rendering breve
- Cliccando su un componente, la sezione "Why did this render?" mostra:
  → "Props changed" — quali props sono cambiate
  → "State changed" — quale parte dello state e' cambiata
  → "Hooks changed" — quale hook ha triggerato il re-render
  → "Parent rendered" — il padre si e' re-renderizzato
```

**Debugging di re-render non necessari:**

```javascript
// Problema comune: un componente si re-renderizza ad ogni render del padre
// anche se le sue props non sono cambiate

// CAUSA 1: oggetti creati inline come props
// ERRATO
<ChildComponent style={{ color: 'red' }} />
// { color: 'red' } e' un nuovo oggetto ad ogni render → re-render del figlio

// CORRETTO
const style = useMemo(() => ({ color: 'red' }), []);
<ChildComponent style={style} />

// CAUSA 2: callback create inline
// ERRATO
<ChildComponent onClick={() => handleClick(item.id)} />
// Arrow function nuova ad ogni render

// CORRETTO
const handleItemClick = useCallback(() => handleClick(item.id), [item.id]);
<ChildComponent onClick={handleItemClick} />

// CAUSA 3: context che cambia troppo spesso
// Se un context provider ha un value che cambia ad ogni render,
// TUTTI i consumer si re-renderizzano
// Soluzione: dividere context grandi in context piu' piccoli e mirati
```

---

## Errori Comuni Backend

### Connection Refused (ECONNREFUSED)

```
Error: connect ECONNREFUSED 127.0.0.1:5432
```

**Causa:** il servizio target (database, cache, servizio esterno) non e' in ascolto sulla porta specificata.

**Diagnosi:**

```bash
# Verificare che il servizio sia in esecuzione
sudo systemctl status postgresql

# Verificare che la porta sia in ascolto
ss -tlnp | grep 5432

# Verificare la connettivita' dal container Docker
docker exec -it app_container ping db_container

# Errore comune con Docker: usare 'localhost' invece del nome del servizio
# ERRATO:  DATABASE_URL=postgresql://user:pass@localhost:5432/db
# CORRETTO: DATABASE_URL=postgresql://user:pass@db:5432/db
```

### ECONNRESET

```
Error: read ECONNRESET
```

**Causa:** la connessione e' stata chiusa bruscamente dall'altra parte. Spesso si verifica con connessioni database idle che vengono terminate dal server o dal firewall.

```javascript
// Soluzione: configurare pool di connessioni con keepalive e retry
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
  keepAlive: true,
  keepAliveInitialDelayMillis: 10000,
});

// Gestione errori a livello di pool
pool.on('error', (err) => {
  console.error('Errore imprevisto sul client idle:', err);
  // Non terminare il processo — il pool ricreera' la connessione
});
```

### Unhandled Promise Rejection

```
UnhandledPromiseRejectionWarning: Error: something went wrong
```

A partire da Node.js 15+, le promise rejection non gestite terminano il processo. Questo e' il bug asincrono piu' comune.

```javascript
// ERRATO — promise rejection non catturata
app.get('/api/users', async (req, res) => {
  const users = await db.query('SELECT * FROM users'); // se fallisce, crash
  res.json(users);
});

// CORRETTO — try/catch esplicito
app.get('/api/users', async (req, res, next) => {
  try {
    const users = await db.query('SELECT * FROM users');
    res.json(users);
  } catch (error) {
    next(error); // passa all'error handler di Express
  }
});

// ANCORA MEGLIO — wrapper per eliminare la ripetizione
const asyncHandler = (fn) => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next);

app.get('/api/users', asyncHandler(async (req, res) => {
  const users = await db.query('SELECT * FROM users');
  res.json(users);
}));

// Rete di sicurezza globale (non sostituisce la gestione locale)
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection:', reason);
  // In produzione: logga su servizio di monitoring, poi graceful shutdown
});
```

### Memory Leak

I memory leak in Node.js si manifestano con un consumo di RAM crescente nel tempo che non viene recuperato dal garbage collector.

**Cause comuni:**

```javascript
// 1. Event listener non rimossi
class UserService {
  constructor(eventBus) {
    // ERRATO — ogni istanza aggiunge un listener che non viene mai rimosso
    eventBus.on('userUpdated', this.handleUpdate.bind(this));
  }
  // CORRETTO — rimuovere il listener nel cleanup
  destroy() {
    this.eventBus.off('userUpdated', this.boundHandler);
  }
}

// 2. Cache senza limiti
const cache = new Map();
function getCachedData(key) {
  if (!cache.has(key)) {
    cache.set(key, fetchExpensiveData(key));
    // La cache cresce indefinitamente!
  }
  return cache.get(key);
}

// Soluzione: usare una LRU cache con limite
import { LRUCache } from 'lru-cache';
const cache = new LRUCache({ max: 500, ttl: 1000 * 60 * 5 }); // max 500 entry, TTL 5 min

// 3. Closure che trattengono riferimenti
function processLargeData() {
  const hugeArray = new Array(1_000_000).fill('data');
  return function getLength() {
    return hugeArray.length; // hugeArray non puo' essere garbage collected
  };
}

// 4. Timer non cancellati
const interval = setInterval(() => {
  // operazione periodica
}, 1000);
// Se il modulo viene ricaricato (HMR), il vecchio interval continua a girare
// Soluzione: clearInterval(interval) nel cleanup
```

### N+1 Queries

Il problema N+1 e' uno dei piu' insidiosi: funziona correttamente ma scala in modo disastroso.

```javascript
// PROBLEMA N+1: 1 query per gli ordini + N query per gli utenti
const orders = await prisma.order.findMany(); // 1 query
for (const order of orders) {
  const user = await prisma.user.findUnique({
    where: { id: order.userId },
  }); // N query — una per ogni ordine!
  order.user = user;
}
// Con 1000 ordini → 1001 query al database

// SOLUZIONE: eager loading con include
const orders = await prisma.order.findMany({
  include: {
    user: true, // Prisma genera un JOIN o una query IN (...) ottimizzata
  },
}); // 1-2 query totali, indipendentemente dal numero di ordini

// SOLUZIONE alternativa con query SQL esplicita
const orders = await prisma.$queryRaw`
  SELECT o.*, u.name as user_name, u.email as user_email
  FROM orders o
  JOIN users u ON o.user_id = u.id
  WHERE o.created_at > ${startDate}
`;
```

### Timeout Errors

```javascript
// Errore: request timeout, gateway timeout (504), ETIMEDOUT

// 1. Timeout lato client fetch
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 secondi

try {
  const response = await fetch('/api/report', {
    signal: controller.signal,
  });
  clearTimeout(timeoutId);
  return await response.json();
} catch (error) {
  if (error.name === 'AbortError') {
    console.error('La richiesta ha superato il timeout di 10 secondi');
  }
  throw error;
}

// 2. Timeout operazioni database lunghe
// Soluzione: spostare operazioni pesanti in background job
import { Queue, Worker } from 'bullmq';

const reportQueue = new Queue('reports', { connection: redisConnection });

// L'API risponde immediatamente con un job ID
app.post('/api/reports', asyncHandler(async (req, res) => {
  const job = await reportQueue.add('generateReport', { params: req.body });
  res.json({ jobId: job.id, status: 'processing' });
}));

// Il worker elabora il report in background senza vincoli di timeout HTTP
new Worker('reports', async (job) => {
  const report = await generateComplexReport(job.data.params);
  await saveReport(report);
}, { connection: redisConnection });
```

---

## Debugging Node.js

### Flag --inspect e Chrome DevTools

Node.js integra un debugger V8 accessibile tramite il protocollo Chrome DevTools:

```bash
# Avviare l'applicazione in modalita' debug
node --inspect src/server.js
# Debugger listening on ws://127.0.0.1:9229/...

# Fermare l'esecuzione alla prima riga
node --inspect-brk src/server.js

# Per applicazioni con ts-node o tsx
node --inspect --import tsx src/server.ts
```

Apri Chrome e naviga a `chrome://inspect`. Clicca "Open dedicated DevTools for Node" per ottenere una finestra dedicata con:

- **Console**: come nel browser, ma con accesso al contesto Node.js
- **Sources**: navigazione del codice sorgente con breakpoint, step-through, watch expressions
- **Memory**: snapshot dell'heap per diagnosticare memory leak
- **Profiler**: profiling CPU per identificare colli di bottiglia

### Debugging con VS Code

VS Code offre l'esperienza di debugging piu' fluida per Node.js. Configurazione:

```jsonc
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Server",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/src/server.ts",
      "runtimeExecutable": "tsx",
      "console": "integratedTerminal",
      "env": {
        "NODE_ENV": "development",
        "PORT": "4000"
      },
      "envFile": "${workspaceFolder}/.env"
    },
    {
      "name": "Debug Current Test",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/node_modules/.bin/vitest",
      "args": ["run", "${relativeFile}", "--reporter=verbose"],
      "console": "integratedTerminal"
    },
    {
      "name": "Attach to Running Process",
      "type": "node",
      "request": "attach",
      "port": 9229,
      "restart": true,
      "sourceMaps": true
    }
  ]
}
```

Funzionalita' chiave del debugger VS Code:

- **Breakpoint condizionali**: click destro sulla pallina rossa, inserire una condizione JavaScript
- **Logpoint**: come un `console.log` temporaneo che non modifica il codice — il messaggio e' un template con espressioni tra `{}`
- **Watch Expressions**: monitorare il valore di variabili ed espressioni in tempo reale
- **Call Stack**: navigare lo stack delle chiamate per capire come si e' arrivati al punto corrente
- **Debug Console**: eseguire codice nel contesto del breakpoint corrente

### Memory Profiling

```bash
# Generare un heap snapshot da riga di comando
node --inspect src/server.js
# Poi in Chrome DevTools > Memory > Take Heap Snapshot

# Generare un heap snapshot programmaticamente
import v8 from 'node:v8';
import fs from 'node:fs';

function takeHeapSnapshot() {
  const snapshotStream = v8.writeHeapSnapshot();
  console.log(`Heap snapshot scritto in: ${snapshotStream}`);
}

// Esporre un endpoint per generare snapshot on-demand
app.get('/debug/heap-snapshot', (req, res) => {
  if (process.env.NODE_ENV !== 'development') {
    return res.status(403).json({ error: 'Solo in sviluppo' });
  }
  const filename = v8.writeHeapSnapshot();
  res.json({ filename });
});
```

Tecnica per individuare memory leak con heap snapshot:

1. Prendere uno snapshot dopo l'avvio dell'applicazione (baseline)
2. Eseguire l'operazione sospetta ripetutamente (es. 100 richieste)
3. Forzare il garbage collector: `global.gc()` (avviare node con `--expose-gc`)
4. Prendere un secondo snapshot
5. Confrontare i due snapshot nella tab "Comparison": gli oggetti che crescono senza giustificazione sono candidati per il leak

---

## Network Debugging

### Charles Proxy e Proxy HTTP

Charles Proxy (o mitmproxy come alternativa open-source) agisce come intermediario tra il client e il server, consentendo di ispezionare, modificare e simulare il traffico di rete, incluso HTTPS.

Casi d'uso principali:

- **Debugging traffico mobile**: configurare il dispositivo mobile per usare Charles come proxy, ispezionando richieste da app native
- **Simulazione errori**: Map Remote per redirigere richieste, Map Local per servire risposte da file locali, Rewrite per modificare header/body al volo
- **Throttling**: simulare connessioni lente (3G, Edge) per testare il comportamento dell'app in condizioni di rete degradate
- **SSL Proxying**: decifrare traffico HTTPS installando il certificato root di Charles sul dispositivo

```bash
# mitmproxy — alternativa open-source a Charles
pip install mitmproxy

# Avviare il proxy
mitmproxy --listen-port 8080

# Configurare il browser/sistema per usare il proxy HTTP su localhost:8080
# Installare il certificato: navigare a mitm.it dal browser configurato

# Filtrare richieste specifiche
mitmproxy --listen-port 8080 --set view_filter='~d api.example.com'
```

### Analisi Avanzata del Tab Network

```
// Filtraggio avanzato nella barra filtro del Network tab
status-code:500          — solo risposte con errore server
larger-than:1M           — risorse piu' grandi di 1MB
method:POST              — solo richieste POST
domain:api.example.com   — solo richieste a un dominio specifico
-domain:cdn.example.com  — escludi un dominio
has-response-header:set-cookie  — richieste che settano cookie
mime-type:application/json      — solo risposte JSON

// Analisi waterfall per ottimizzazione
// - Cercare richieste sequenziali che potrebbero essere parallelizzate
// - Identificare richieste bloccanti (JS sincrono nel <head>)
// - Controllare la dimensione dei bundle e l'efficacia della compressione (gzip/br)
// - Verificare i cache header (Cache-Control, ETag, Last-Modified)
```

### Debugging WebSocket

```javascript
// Il tab Network mostra le connessioni WebSocket nella sezione "WS"
// Cliccando sulla connessione si vedono i messaggi scambiati in tempo reale

// Debug lato client
const ws = new WebSocket('wss://api.example.com/ws');

ws.addEventListener('open', () => {
  console.log('[WS] Connessione stabilita');
});

ws.addEventListener('message', (event) => {
  console.log('[WS] Messaggio ricevuto:', JSON.parse(event.data));
});

ws.addEventListener('close', (event) => {
  console.log('[WS] Connessione chiusa:', event.code, event.reason);
  // Codici comuni:
  // 1000 — chiusura normale
  // 1001 — endpoint che va via (navigazione pagina)
  // 1006 — chiusura anomala (nessun close frame ricevuto)
  // 1008 — policy violation
  // 1011 — errore server imprevisto
});

ws.addEventListener('error', (event) => {
  console.error('[WS] Errore:', event);
});
```

---

## Network Debugging Avanzato

### Errori CORS: Diagnosi Approfondita

Oltre alla configurazione base del middleware CORS, esistono scenari complessi che richiedono una diagnosi piu' approfondita.

**Preflight request fallite:**

Le richieste preflight (OPTIONS) sono inviate automaticamente dal browser prima di richieste "non semplici". Una richiesta e' non semplice quando usa un metodo diverso da GET/HEAD/POST, quando include header custom (come `Authorization`), o quando usa un `Content-Type` diverso da `application/x-www-form-urlencoded`, `multipart/form-data` o `text/plain`.

```
Diagnosi nel pannello Network:
1. Filtrare per "method:OPTIONS"
2. Controllare lo status della risposta OPTIONS:
   → 204/200 = preflight riuscito, il problema e' altrove
   → 403/404/500 = il server non gestisce OPTIONS correttamente
   → Nessuna risposta = il server non risponde alle OPTIONS

3. Controllare gli header della risposta OPTIONS:
   → Access-Control-Allow-Origin deve corrispondere all'origin del frontend
   → Access-Control-Allow-Methods deve includere il metodo richiesto
   → Access-Control-Allow-Headers deve includere tutti gli header custom
   → Access-Control-Max-Age (opzionale) indica per quanto tempo il browser
     puo' cacheare il risultato del preflight
```

**Problemi specifici di CORS con cookie:**

```javascript
// ERRORE FREQUENTE:
// "The value of the 'Access-Control-Allow-Origin' header in the response
// must not be the wildcard '*' when the request's credentials mode is 'include'"

// Il problema si verifica quando:
// 1. Il frontend invia credentials: 'include' nella fetch
// 2. Il backend risponde con Access-Control-Allow-Origin: '*'

// Soluzione: specificare l'origin esatto
// E aggiungere Access-Control-Allow-Credentials: true

// Attenzione al SameSite cookie attribute:
// - SameSite=Strict → il cookie non viene MAI inviato cross-site
// - SameSite=Lax → il cookie viene inviato solo per navigazione top-level
// - SameSite=None → il cookie viene inviato cross-site, MA richiede Secure=true
```

### Mixed Content: HTTP su HTTPS

Il mixed content si verifica quando una pagina caricata su HTTPS include risorse su HTTP. I browser moderni bloccano il mixed content attivo (script, iframe) e segnalano il mixed content passivo (immagini, video).

```
Diagnosi:
1. Aprire la Console di DevTools
2. Cercare warning "Mixed Content":
   → "Mixed Content: The page was loaded over HTTPS, but requested an
      insecure resource 'http://...'. This request has been blocked"

Cause comuni:
- URL hardcoded con http:// nel codice o nel database
- CDN configurati senza HTTPS
- API di terze parti che non supportano HTTPS
- Immagini caricate da URL inseriti dagli utenti

Soluzioni:
1. Usare URL protocol-relative: //cdn.example.com/asset.js
   (ma preferire https:// esplicito)
2. Forzare HTTPS tramite Content-Security-Policy:
   Content-Security-Policy: upgrade-insecure-requests
3. Aggiornare tutti i riferimenti a http:// nel codice e nel database
4. Validare gli URL inseriti dagli utenti per richiedere HTTPS
```

### Problemi di Certificati SSL/TLS

```
Errori comuni e soluzioni:

1. NET::ERR_CERT_AUTHORITY_INVALID
   Causa: certificato autofirmato o CA non riconosciuta
   Soluzione: usare Let's Encrypt per certificati gratuiti e riconosciuti

2. NET::ERR_CERT_DATE_INVALID
   Causa: certificato scaduto
   Soluzione: configurare il rinnovo automatico
   → certbot renew --quiet (aggiungere al crontab)

3. NET::ERR_CERT_COMMON_NAME_INVALID
   Causa: il dominio nel certificato non corrisponde all'URL
   Soluzione: rigenerare il certificato con il dominio corretto
   → Verificare che il certificato copra sia www che non-www

4. In ambiente di sviluppo con mkcert:
   → mkcert -install (installa la CA locale)
   → mkcert localhost 127.0.0.1 ::1
   → Configurare il dev server per usare i certificati generati
```

---

## Build Tool Troubleshooting

### Errori Comuni di Vite

**"Failed to resolve import":**

```javascript
// Errore: [vite] Internal server error: Failed to resolve import
// "@/components/Button" from "src/pages/Home.tsx"

// Causa: alias non configurato sia in Vite che in TypeScript

// vite.config.ts — configurazione alias per il bundler
import path from 'node:path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});

// tsconfig.json — configurazione alias per TypeScript (type-checking)
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}

// ATTENZIONE: entrambe le configurazioni sono necessarie.
// Vite usa resolve.alias per il bundling.
// TypeScript usa paths per il type-checking.
// Se ne configuri solo una, avrai errori nell'altra.
```

**Vite non mostra errori TypeScript in dev mode:**

```bash
# Vite ignora gli errori TypeScript durante lo sviluppo per velocita'
# Gli errori emergono solo al momento della build

# Soluzione 1: plugin vite-plugin-checker
npm install -D vite-plugin-checker

# vite.config.ts
import checker from 'vite-plugin-checker';

export default defineConfig({
  plugins: [
    checker({ typescript: true }),
    // Mostra gli errori TypeScript come overlay nel browser
  ],
});

# Soluzione 2: eseguire tsc in parallelo
# package.json
{
  "scripts": {
    "dev": "tsc --noEmit --watch & vite",
    "build": "tsc --noEmit && vite build"
  }
}
```

**HMR (Hot Module Replacement) non funziona:**

```
Diagnosi:
1. Controllare la Console per errori "[vite] hmr..."
2. Verificare che il browser supporti WebSocket
3. Controllare che il firewall non blocchi la porta HMR

Cause comuni:
- React component non esporta il componente come default/named export
- Il file modifica variabili globali o ha effetti collaterali al top level
- Proxy che interfersice con la connessione WebSocket di HMR
- Docker: la porta HMR deve essere esposta e il polling potrebbe essere necessario

Soluzione Docker:
// vite.config.ts
export default defineConfig({
  server: {
    watch: {
      usePolling: true, // necessario in container Docker
    },
    hmr: {
      host: 'localhost',
      port: 5173,
    },
  },
});
```

### Errori Comuni di Webpack

```javascript
// "Module not found: Can't resolve 'X'"
// Causa: modulo non installato o path errato
// → npm install X
// → Controllare case-sensitivity del path su Linux

// "You may need an appropriate loader"
// Causa: Webpack non sa come processare il tipo di file
// → Aggiungere il loader appropriato (css-loader, file-loader, etc.)

// "Critical dependency: the request of a dependency is an expression"
// Causa: import() dinamico con variabile non risolvibile staticamente
// → import(`./locales/${lang}.json`) richiede un commento webpackChunkName

// Bundle troppo grande — analisi:
// → npx webpack-bundle-analyzer stats.json
// → npx vite-bundle-visualizer (per progetti Vite)
```

### Errori Comuni di TypeScript

```typescript
// TS2307: Cannot find module 'X' or its corresponding type declarations
// Causa: mancano i tipi per un pacchetto JavaScript
// Soluzione 1: installare i tipi
// npm install -D @types/nome-pacchetto

// Soluzione 2: creare una dichiarazione locale
// src/types/nome-pacchetto.d.ts
declare module 'nome-pacchetto';
// Oppure con tipi parziali:
declare module 'nome-pacchetto' {
  export function doSomething(input: string): Promise<void>;
}

// TS2322: Type 'X' is not assignable to type 'Y'
// Diagnosi: leggere TUTTO il messaggio — TypeScript mostra la catena
// di incompatibilita' partendo dal tipo piu' esterno
// → "Type '{ name: string; }' is not assignable to type 'User'"
// → "Property 'email' is missing in type '{ name: string; }'"
// La seconda riga indica il problema reale

// TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'
// Frequente con array methods:
// items.filter(item => item !== null) restituisce (T | null)[]
// Soluzione: items.filter((item): item is T => item !== null)

// TS18046: 'X' is of type 'unknown'
// Frequente nei catch block (TypeScript 4.4+):
// catch (error) { → error e' unknown
// Soluzione: if (error instanceof Error) { console.log(error.message); }

// Errori con moduleResolution:
// Se usi Vite, imposta moduleResolution: "bundler" in tsconfig.json
// Questo allinea la risoluzione dei moduli TypeScript con quella di Vite
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "module": "ESNext",
    "target": "ES2022"
  }
}
```

---

## Deployment Debugging

### Differenze tra Ambiente di Sviluppo e Produzione

I bug che appaiono solo in produzione sono tra i piu' difficili da diagnosticare. Le differenze principali tra i due ambienti sono:

```
Differenze critiche dev vs produzione:

1. MINIFICAZIONE
   Dev: codice leggibile con nomi di variabili originali
   Prod: codice minificato con nomi mangled (a, b, c)
   Impatto: stack trace illeggibili senza source maps
   → Soluzione: abilitare source maps hidden per produzione
   → Usare un servizio di error tracking (Sentry) che de-obfusca gli stack trace

2. TREE-SHAKING
   Dev: tutto il codice e' incluso
   Prod: il codice non utilizzato viene rimosso
   Impatto: codice che dipende da side-effect puo' essere rimosso
   → Soluzione: marcare i side-effect in package.json: "sideEffects": ["*.css"]

3. VARIABILI D'AMBIENTE
   Dev: caricate da .env locale
   Prod: definite nel server/container/CI
   Impatto: variabili mancanti causano errori a runtime
   → Soluzione: validare le variabili all'avvio dell'applicazione

4. API URL
   Dev: tipicamente localhost:4000
   Prod: dominio reale con HTTPS
   Impatto: URL hardcoded causano errori di connessione
   → Soluzione: usare variabili d'ambiente per tutti gli URL

5. CACHING
   Dev: cache disabilitata (Vite serve tutto fresco)
   Prod: cache aggressiva con content hashing
   Impatto: aggiornamenti non visibili per cache stale
   → Soluzione: content hash nei nomi dei file + cache-busting headers
```

**Troubleshooting delle variabili d'ambiente:**

```javascript
// Validazione delle variabili d'ambiente con Zod all'avvio
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32, 'JWT_SECRET deve avere almeno 32 caratteri'),
  PORT: z.coerce.number().default(4000),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  CORS_ORIGIN: z.string().url(),
  REDIS_URL: z.string().url().optional(),
});

// Fallisce immediatamente all'avvio se mancano variabili critiche
export const env = envSchema.parse(process.env);

// Prefissi per variabili d'ambiente frontend:
// Vite:    VITE_    → import.meta.env.VITE_API_URL
// Next.js: NEXT_PUBLIC_ → process.env.NEXT_PUBLIC_API_URL
// CRA:     REACT_APP_ → process.env.REACT_APP_API_URL
// ATTENZIONE: variabili senza il prefisso corretto NON sono esposte al client
```

**Build fallita in CI ma non in locale:**

```bash
# Cause comuni e diagnosi:

# 1. Versione Node.js diversa
# Locale: node v22, CI: node v20
# → Specificare in .nvmrc: 22
# → In GitHub Actions: actions/setup-node@v4 con node-version: 22

# 2. Dipendenze mancanti
# npm install installa devDependencies in locale
# npm ci --production in CI salta le devDependencies
# Se un tool di build e' in devDependencies, la build fallisce
# → Verificare che npm ci (senza --production) sia usato per la build

# 3. File system case-sensitive
# macOS/Windows: case-insensitive (Header.tsx = header.tsx)
# Linux/CI: case-sensitive (Header.tsx != header.tsx)
# → Rinominare i file per corrispondenza esatta con gli import

# 4. File generati non committati
# prisma generate, graphql codegen → file .ts generati
# Se questi file non sono nel repo, la build CI fallisce
# → Aggiungere il comando di generazione prima della build nel CI

# 5. Timeout e limiti di memoria
# NODE_OPTIONS="--max-old-space-size=4096" npm run build
```

---

## SEO Troubleshooting

### Diagnosi di Problemi SEO Tecnico

Il SEO tecnico riguarda gli aspetti che influenzano l'indicizzazione e il ranking di un sito web nei motori di ricerca. Gli sviluppatori web sono responsabili di garantire che il sito sia tecnicamente accessibile ai crawler.

**Errori di crawling e indicizzazione:**

```
Strumenti di diagnosi:
1. Google Search Console → Copertura → mostra pagine indicizzate, escluse, errori
2. robots.txt → verificare che non blocchi pagine importanti
3. Sitemap XML → verificare che includa tutte le pagine rilevanti

Errori comuni:

1. robots.txt troppo restrittivo
   Disallow: /           → blocca TUTTO il sito
   Disallow: /api/       → OK, blocca le API
   Disallow: /admin/     → OK, blocca l'area admin

2. Tag noindex accidentale
   <meta name="robots" content="noindex">
   → Spesso lasciato dalla configurazione di staging
   → Controllare con: curl -s URL | grep -i 'noindex'

3. Canonical URL errato
   <link rel="canonical" href="https://staging.example.com/page">
   → Punta a staging invece che a produzione
   → Deve corrispondere esattamente all'URL della pagina

4. Redirect chain eccessivi
   A → B → C → D (3 redirect) → Google segue max ~5, penalizza la lentezza
   → Risolvere con redirect diretto A → D
```

**Structured Data (Schema.org):**

```html
<!-- JSON-LD per un articolo — inserire nel <head> -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Titolo dell'articolo",
  "datePublished": "2026-05-24",
  "dateModified": "2026-05-24",
  "author": {
    "@type": "Person",
    "name": "Nome Autore"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Nome Sito",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  },
  "image": "https://example.com/article-image.jpg",
  "description": "Descrizione dell'articolo per i rich snippet"
}
</script>

<!-- Validazione: -->
<!-- 1. Google Rich Results Test: https://search.google.com/test/rich-results -->
<!-- 2. Schema.org Validator: https://validator.schema.org/ -->
<!-- 3. In Chrome DevTools: pannello Lighthouse > categoria SEO -->
```

**Problemi SEO con SPA (Single Page Application):**

Le SPA presentano sfide specifiche per il SEO perche' il contenuto e' generato dal JavaScript lato client. I crawler meno sofisticati potrebbero non eseguire JavaScript o eseguirlo con limitazioni.

```
Soluzioni:
1. Server-Side Rendering (SSR) con Next.js, Nuxt, Remix
   → Il server genera HTML completo per ogni pagina
   → Il crawler riceve HTML con contenuto gia' presente

2. Static Site Generation (SSG) per contenuti che non cambiano frequentemente
   → Le pagine sono generate al momento della build
   → Nessun costo server per il rendering

3. Meta tag dinamici con react-helmet-async o next/head:
   → Ogni pagina deve avere title e description unici
   → Open Graph tags per la condivisione sui social

4. Prerendering on-demand per SPA pure:
   → Servizi come prerender.io o puppeteer in serverless
   → Servono HTML pre-renderizzato solo ai bot dei motori di ricerca
```

---

## Accessibility Debugging

### Diagnosi Sistematica dei Problemi di Accessibilita'

L'accessibilita' web (a11y) garantisce che il sito sia utilizzabile da persone con disabilita'. Non e' solo un obbligo legale in molti paesi (European Accessibility Act 2025, ADA) ma anche una best practice che migliora l'usabilita' per tutti.

**Strumenti automatizzati:**

```bash
# 1. Lighthouse Accessibility Audit (integrato in Chrome DevTools)
# Pannello Lighthouse > selezionare "Accessibility" > "Analyze page load"
# Lighthouse usa axe-core come motore, controllando WCAG 2.1 Level AA

# 2. axe DevTools (estensione browser)
# Fornisce analisi piu' dettagliata di Lighthouse con:
# - Descrizione del problema
# - Impatto (critical, serious, moderate, minor)
# - Nodi DOM coinvolti
# - Suggerimento di correzione con codice

# 3. Pa11y (CLI per CI/CD)
npm install -g pa11y
pa11y https://example.com
# Oppure con reporter HTML:
pa11y --reporter html https://example.com > report.html

# 4. axe-core in test automatizzati (Playwright/Vitest)
npm install -D @axe-core/playwright
```

```typescript
// Test di accessibilita' con Playwright + axe-core
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('homepage deve essere accessibile', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});

test('form di login deve essere accessibile', async ({ page }) => {
  await page.goto('/login');

  const results = await new AxeBuilder({ page })
    .include('#login-form') // analizza solo il form
    .analyze();

  expect(results.violations).toEqual([]);
});
```

**Problemi comuni e soluzioni:**

```html
<!-- 1. Immagini senza alt text -->
<!-- ERRATO -->
<img src="hero.jpg">
<!-- CORRETTO: alt descrittivo per immagini informative -->
<img src="hero.jpg" alt="Dashboard con grafico delle vendite mensili">
<!-- CORRETTO: alt vuoto per immagini decorative -->
<img src="decorazione.svg" alt="" role="presentation">

<!-- 2. Contrasto colore insufficiente (WCAG AA: rapporto 4.5:1 per testo) -->
<!-- Verificare con Chrome DevTools: -->
<!-- Selezionare l'elemento > nel pannello Styles > cliccare sul quadrato colore -->
<!-- DevTools mostra il rapporto di contrasto e indica se passa AA/AAA -->

<!-- 3. Focus non visibile -->
<!-- ERRATO: rimuovere l'outline senza alternativa -->
<style>
*:focus { outline: none; } /* MAI fare questo */
</style>
<!-- CORRETTO: fornire un'alternativa visibile -->
<style>
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
</style>

<!-- 4. Form senza label associate -->
<!-- ERRATO -->
<input type="email" placeholder="Email">
<!-- CORRETTO -->
<label for="email">Indirizzo email</label>
<input type="email" id="email" placeholder="esempio@email.com">

<!-- 5. Heading hierarchy saltata -->
<!-- ERRATO: h1 → h3 (salta h2) -->
<!-- CORRETTO: h1 → h2 → h3 (sequenza rispettata) -->
```

**Testing con screen reader:**

```
Test manuali imprescindibili (nessun tool automatico puo' sostituirli):

1. Navigazione da tastiera:
   → Tab attraverso tutti gli elementi interattivi
   → Verificare che l'ordine di focus sia logico
   → Verificare che tutti gli elementi siano raggiungibili
   → Escape per chiudere modale/dropdown
   → Enter/Space per attivare bottoni e link

2. Screen reader test (almeno uno):
   → macOS: VoiceOver (Cmd+F5 per attivare)
   → Windows: NVDA (gratuito) o JAWS
   → Linux: Orca

3. Verifica ARIA:
   → aria-label per elementi senza testo visibile
   → aria-labelledby per collegare label complesse
   → aria-live="polite" per contenuto dinamico
   → role="alert" per notifiche urgenti
```

---

## Debugging Mobile

### Remote Debugging su Dispositivi Reali

Il debugging su dispositivi reali e' fondamentale perche' gli emulatori non replicano fedelmente le performance hardware, i gesti touch, le dimensioni reali dello schermo e il comportamento dei browser mobile nativi.

**Android + Chrome DevTools:**

```
1. Sul dispositivo Android:
   → Impostazioni > Opzioni sviluppatore > Debug USB → ON
   (Se "Opzioni sviluppatore" non e' visibile: Impostazioni > Info telefono
   → toccare "Numero build" 7 volte)

2. Collegare il dispositivo al computer via USB

3. Sul computer, aprire Chrome e navigare a:
   chrome://inspect/#devices

4. Il dispositivo apparira' con tutte le tab aperte
   → Cliccare "inspect" accanto alla tab da debuggare
   → Si apre una finestra DevTools completa connessa al dispositivo

5. La finestra DevTools include:
   - Console (con accesso al contesto della pagina mobile)
   - Network (traffico reale della rete mobile)
   - Performance (profiling su hardware reale)
   - Screencast (mirror dello schermo del dispositivo)
```

**iOS + Safari Web Inspector:**

```
1. Sul dispositivo iOS:
   → Impostazioni > Safari > Avanzate > Web Inspector → ON

2. Sul Mac, aprire Safari:
   → Preferenze > Avanzate > "Mostra menu Sviluppo"

3. Collegare il dispositivo iOS al Mac via USB (o WiFi con trust)

4. Nel menu Sviluppo di Safari desktop:
   → Selezionare il dispositivo → selezionare la tab da ispezionare

5. Si apre il Web Inspector di Safari con:
   - Console
   - Network
   - Elements
   - Timelines (equivalente del Performance panel)
```

**Problemi specifici del mobile:**

```css
/* 1. 300ms tap delay su browser mobile vecchi */
/* Soluzione moderna: gia' risolto con viewport meta tag */
<meta name="viewport" content="width=device-width, initial-scale=1">
/* Se ancora presente: */
html { touch-action: manipulation; }

/* 2. 100vh che non funziona su mobile (barra indirizzi) */
/* Il 100vh include la barra indirizzi che appare/scompare */
/* ERRATO */
.fullscreen { height: 100vh; }
/* CORRETTO — usa le unita' viewport dinamiche */
.fullscreen { height: 100dvh; } /* dvh = dynamic viewport height */
/* Fallback per browser piu' vecchi */
.fullscreen { height: 100vh; height: 100dvh; }

/* 3. Overflow orizzontale su mobile */
/* Diagnostica: */
/* DevTools > Console > */
document.querySelectorAll('*').forEach(el => {
  if (el.scrollWidth > document.documentElement.clientWidth) {
    console.log('Overflow:', el, el.scrollWidth);
  }
});
/* Cause comuni: tabelle senza overflow-x: auto, immagini senza max-width */

/* 4. Font troppo piccolo su mobile */
/* Minimum: 16px per il body text (evita lo zoom automatico di iOS su input) */
input, select, textarea { font-size: 16px; }
/* Con font < 16px, iOS zooma automaticamente quando si tocca un input */
```

**Simulazione di condizioni mobili in DevTools:**

```
Device Mode (Ctrl+Shift+M) in Chrome DevTools:

1. Selezionare un dispositivo dal dropdown o definire custom
2. Abilitare throttling:
   → CPU: 4x o 6x slowdown (simula processori mobile)
   → Network: 3G o custom profile
3. Simulare condizioni specifiche:
   → Geolocalizzazione: Sensors tab > Geolocation
   → Orientamento: ruotare il dispositivo simulato
   → Touch events: il click diventa tap
   → Device Pixel Ratio: 2x, 3x per schermi retina
```

---

## State Management Debugging

### Diagnosi di Problemi nello Stato dell'Applicazione

I bug legati allo state management sono tra i piu' insidiosi perche' spesso non producono errori espliciti ma comportamenti inaspettati: UI che non si aggiorna, dati stale, inconsistenze tra componenti.

**Debugging di Zustand:**

```javascript
// Zustand DevTools middleware — collega lo store a Redux DevTools
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

const useStore = create(
  devtools(
    (set) => ({
      count: 0,
      increment: () => set((state) => ({ count: state.count + 1 }), false, 'increment'),
      // Il terzo argomento di set e' il nome dell'azione in DevTools
    }),
    { name: 'CounterStore' } // nome dello store in DevTools
  )
);

// Con Redux DevTools Extension installata:
// 1. Aprire Redux DevTools nel browser
// 2. Ogni chiamata a set appare come azione con nome
// 3. Si puo' fare time-travel debugging (navigare tra stati precedenti)
// 4. Si puo' esportare/importare lo stato per ricreare bug
```

**Debugging di React Query (TanStack Query):**

```javascript
// React Query DevTools — pannello dedicato per lo stato delle query
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
      <ReactQueryDevtools initialIsOpen={false} />
      {/* Il pannello mostra:
          - Tutte le query con il loro stato (fresh, stale, fetching, error)
          - Il cache corrente con timestamp
          - La configurazione di ogni query (staleTime, cacheTime, retry)
          - I mutation in corso
          Utile per diagnosticare:
          - Query che ri-fetchano troppo spesso
          - Cache che non si invalida correttamente
          - Race condition tra mutation e query
      */}
    </QueryClientProvider>
  );
}
```

**Pattern comuni di bug nello state management:**

```javascript
// 1. Mutation accidentale dello stato (viola l'immutabilita')
// ERRATO
const [items, setItems] = useState([{ id: 1, name: 'A' }]);
const updateItem = (id, name) => {
  const item = items.find(i => i.id === id);
  item.name = name; // MUTAZIONE DIRETTA — React non rileva il cambiamento
  setItems(items); // stesso riferimento → nessun re-render
};

// CORRETTO
const updateItem = (id, name) => {
  setItems(items.map(i => i.id === id ? { ...i, name } : i));
  // Nuovo array + nuovo oggetto → React rileva il cambiamento
};

// 2. Stale closure — lo stato catturato nella closure e' obsoleto
// ERRATO
useEffect(() => {
  const interval = setInterval(() => {
    setCount(count + 1); // 'count' e' il valore al momento della creazione
    // della closure, non il valore corrente
  }, 1000);
  return () => clearInterval(interval);
}, []); // deps vuote → count e' sempre 0

// CORRETTO
useEffect(() => {
  const interval = setInterval(() => {
    setCount(prev => prev + 1); // functional update — usa il valore corrente
  }, 1000);
  return () => clearInterval(interval);
}, []);

// 3. Stato derivato duplicato
// ERRATO — stato sincronizzato manualmente
const [items, setItems] = useState([]);
const [filteredItems, setFilteredItems] = useState([]); // stato derivato!
const [filter, setFilter] = useState('');
useEffect(() => {
  setFilteredItems(items.filter(i => i.name.includes(filter)));
}, [items, filter]); // sincronizzazione manuale = fonte di bug

// CORRETTO — calcolare lo stato derivato durante il render
const [items, setItems] = useState([]);
const [filter, setFilter] = useState('');
const filteredItems = useMemo(
  () => items.filter(i => i.name.includes(filter)),
  [items, filter]
);
```

---

## API Integration Troubleshooting

### Problemi Comuni nell'Integrazione con API Esterne

L'integrazione con API di terze parti e' una fonte frequente di errori a causa della dipendenza da servizi esterni, differenze di formato dati e problemi di autenticazione.

**Rate limiting e throttling:**

```javascript
// Errore HTTP 429: Too Many Requests
// Il server ha un limite di richieste per intervallo di tempo

// Soluzione: implementare retry con backoff esponenziale
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);

      if (response.status === 429) {
        // Leggere l'header Retry-After se presente
        const retryAfter = response.headers.get('Retry-After');
        const delayMs = retryAfter
          ? parseInt(retryAfter, 10) * 1000
          : Math.min(1000 * Math.pow(2, attempt), 30000); // max 30 secondi

        console.warn(`Rate limited, retry tra ${delayMs}ms (tentativo ${attempt + 1})`);
        await new Promise(resolve => setTimeout(resolve, delayMs));
        continue;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (attempt === maxRetries) throw error;
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

**Differenze di formato tra API:**

```javascript
// Problema: l'API restituisce date in formati diversi
// "2026-05-24T10:30:00Z"    — ISO 8601 (standard)
// "1748083800"              — Unix timestamp (secondi)
// "1748083800000"           — Unix timestamp (millisecondi)
// "24/05/2026"              — formato europeo
// "05/24/2026"              — formato americano

// Soluzione: normalizzare al momento della ricezione
function parseApiDate(value) {
  if (typeof value === 'number') {
    // Distinguere secondi da millisecondi
    return value < 1e12 ? new Date(value * 1000) : new Date(value);
  }
  // Per stringhe, Date.parse gestisce ISO 8601 e formati comuni
  const date = new Date(value);
  if (isNaN(date.getTime())) {
    throw new Error(`Formato data non riconosciuto: ${value}`);
  }
  return date;
}

// Problema: paginazione con meccanismi diversi
// - Offset-based: ?page=2&limit=20
// - Cursor-based: ?cursor=eyJpZCI6MTAwfQ==
// - Link header: Link: <url>; rel="next"

// Soluzione: adapter pattern per normalizzare
function extractNextPage(response) {
  // Cursor-based
  if (response.data.nextCursor) {
    return { cursor: response.data.nextCursor };
  }
  // Link header
  const linkHeader = response.headers.get('Link');
  if (linkHeader) {
    const nextMatch = linkHeader.match(/<([^>]+)>;\s*rel="next"/);
    if (nextMatch) return { url: nextMatch[1] };
  }
  // Offset-based
  if (response.data.hasMore) {
    return { page: response.data.page + 1 };
  }
  return null; // nessuna pagina successiva
}
```

---

## Performance Bottleneck Identification

### Metodologia Sistematica per Identificare Colli di Bottiglia

L'ottimizzazione delle performance deve partire dalla misurazione, non dall'intuizione. Un collo di bottiglia identificato con gli strumenti corretti si risolve in minuti; un'ottimizzazione basata su ipotesi puo' peggiorare la situazione.

**Framework RAIL per la diagnosi:**

```
RAIL (Response, Animation, Idle, Load):

Response (< 100ms):
- L'utente clicca un bottone → la UI deve rispondere entro 100ms
- Diagnosi: Event Handlers nel Performance panel che superano 100ms
- Causa comune: operazioni sincrone nel click handler

Animation (< 16ms per frame = 60fps):
- Scroll, transizioni, animazioni devono essere fluide
- Diagnosi: frame rate nel Performance panel < 60fps
- Causa comune: animazioni su proprieta' che triggerano layout (width, height)

Idle (blocchi < 50ms):
- Durante l'idle, il browser esegue task differiti
- Diagnosi: Long Tasks nel Performance panel
- Causa comune: parsing di JSON grandi, calcoli pesanti nel main thread

Load (LCP < 2.5s):
- La pagina deve diventare interattiva rapidamente
- Diagnosi: Lighthouse performance score < 90
- Causa comune: bundle JS troppo grande, render-blocking resources
```

**Diagnosi di rendering lento:**

```javascript
// Misurare il tempo di rendering di un componente React
import { Profiler } from 'react';

function onRenderCallback(
  id,           // nome del Profiler
  phase,        // "mount" o "update"
  actualDuration, // tempo di rendering in ms
  baseDuration,   // tempo stimato senza memoizzazione
  startTime,      // quando il rendering e' iniziato
  commitTime      // quando il commit e' stato eseguito
) {
  if (actualDuration > 16) { // piu' di un frame a 60fps
    console.warn(`[Perf] ${id} ${phase}: ${actualDuration.toFixed(2)}ms`);
  }
}

<Profiler id="UserList" onRender={onRenderCallback}>
  <UserList users={users} />
</Profiler>
```

**Analisi delle performance di rete:**

```
Nel pannello Network di DevTools, ordinare per:

1. Size (descending) → identifica risorse troppo grandi
   - Bundle JS > 300KB gzipped → necessita code splitting
   - Immagini > 200KB → necessitano compressione/ridimensionamento
   - Font > 100KB → valutare subsetting

2. Time (descending) → identifica risorse lente
   - TTFB > 500ms → problema server-side (query lenta, cold start)
   - Download > 1s → risorsa troppo grande o connessione lenta
   - Stalled > 200ms → troppe connessioni parallele allo stesso dominio

3. Waterfall → identifica richieste sequenziali
   - Catene di dipendenze: A carica B che carica C
   - Soluzione: preload risorse critiche, parallelizzare richieste
```

---

## Catalogo dei Pattern di Errore Comuni

### Errori per Categoria con Diagnosi Rapida

Questa sezione cataloga gli errori piu' frequenti organizzati per categoria, con messaggio di errore esatto, causa tipica e soluzione immediata.

**Errori di rete:**

| Errore | Causa | Soluzione rapida |
|--------|-------|------------------|
| `net::ERR_CONNECTION_REFUSED` | Servizio non in ascolto sulla porta | Verificare che il server sia avviato |
| `net::ERR_CONNECTION_RESET` | Connessione chiusa dal server | Controllare timeout e keepalive |
| `net::ERR_CONNECTION_TIMED_OUT` | Nessuna risposta dal server | Verificare firewall e DNS |
| `net::ERR_NAME_NOT_RESOLVED` | DNS non risolto | Verificare il dominio e il DNS |
| `net::ERR_CERT_AUTHORITY_INVALID` | Certificato SSL non valido | Rinnovare o sostituire il certificato |
| `ERR_HTTP2_PROTOCOL_ERROR` | Incompatibilita' HTTP/2 | Verificare proxy/CDN, provare HTTP/1.1 |

**Errori JavaScript:**

| Errore | Causa | Soluzione rapida |
|--------|-------|------------------|
| `TypeError: X is not a function` | Chiamata di metodo su valore errato | Verificare il tipo con `typeof` |
| `TypeError: Cannot read properties of null` | Accesso a proprieta' di null | Usare optional chaining `?.` |
| `SyntaxError: Unexpected token '<'` | Server restituisce HTML invece di JS | Verificare il path del bundle |
| `ReferenceError: X is not defined` | Variabile non dichiarata | Verificare import e scope |
| `RangeError: Maximum call stack` | Ricorsione infinita | Aggiungere condizione di uscita |
| `ChunkLoadError` | Code-splitting fallito | Implementare retry o reload della pagina |

**Errori di build:**

| Errore | Causa | Soluzione rapida |
|--------|-------|------------------|
| `Module not found` | Import con path errato | Verificare case e alias |
| `ENOSPC: file watchers` | Limite sistema raggiunto | Aumentare `max_user_watches` |
| `ENOMEM: heap out of memory` | Memoria insufficiente per build | `NODE_OPTIONS=--max-old-space-size=4096` |
| `Conflicting peer dependency` | Versioni incompatibili | Usare `overrides` in package.json |
| `Declaration file not found` | Tipi mancanti per modulo JS | Installare `@types/X` o creare `.d.ts` |

**Errori Docker:**

| Errore | Causa | Soluzione rapida |
|--------|-------|------------------|
| `port is already allocated` | Porta gia' in uso | `docker compose down` o cambiare porta |
| `no space left on device` | Disco pieno | `docker system prune -a` |
| `exec format error` | Architettura CPU incompatibile | Specificare `--platform linux/amd64` |
| `COPY failed: file not found` | File non nel build context | Verificare il `.dockerignore` |

---

## Guida Pratica 1: Setup Progetto Full-Stack

Questa guida copre la creazione da zero di un progetto full-stack moderno con React + Vite per il frontend, Node.js + Express per il backend, PostgreSQL + Prisma come database, il tutto orchestrato con Docker Compose.

### Struttura del Progetto

```
fullstack-app/
├── docker-compose.yml
├── .env
├── .gitignore
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   └── client.ts
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       └── types/
├── backend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── server.ts
│       ├── routes/
│       │   └── users.ts
│       ├── middleware/
│       │   ├── errorHandler.ts
│       │   └── auth.ts
│       ├── services/
│       └── lib/
│           └── prisma.ts
└── prisma/
    ├── schema.prisma
    └── migrations/
```

### Docker Compose

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-admin}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secret}
      POSTGRES_DB: ${DB_NAME:-fullstack_db}
    ports:
      - '5432:5432'
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U ${DB_USER:-admin}']
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER:-admin}:${DB_PASSWORD:-secret}@db:5432/${DB_NAME:-fullstack_db}
      PORT: 4000
      JWT_SECRET: ${JWT_SECRET:-dev-secret-change-in-production}
      NODE_ENV: development
    ports:
      - '4000:4000'
    volumes:
      - ./backend/src:/app/src
      - ./prisma:/app/prisma
    depends_on:
      db:
        condition: service_healthy
    command: npx tsx watch src/server.ts

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - '3000:3000'
    volumes:
      - ./frontend/src:/app/src
    environment:
      VITE_API_URL: http://localhost:4000
    depends_on:
      - backend

volumes:
  pgdata:
```

### Backend — Server Express

```typescript
// backend/src/server.ts
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { userRoutes } from './routes/users.js';
import { errorHandler } from './middleware/errorHandler.js';

const app = express();
const PORT = process.env.PORT || 4000;

// Middleware globali
app.use(helmet());
app.use(cors({
  origin: process.env.NODE_ENV === 'production'
    ? 'https://app.example.com'
    : 'http://localhost:3000',
  credentials: true,
}));
app.use(morgan('dev'));
app.use(express.json({ limit: '10mb' }));

// Routes
app.use('/api/users', userRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handler globale — DEVE essere l'ultimo middleware
app.use(errorHandler);

app.listen(PORT, () => {
  console.log(`Server avviato su http://localhost:${PORT}`);
});
```

```typescript
// backend/src/middleware/errorHandler.ts
import { Request, Response, NextFunction } from 'express';

export class AppError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public isOperational = true
  ) {
    super(message);
    Object.setPrototypeOf(this, AppError.prototype);
  }
}

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: err.message,
    });
  }

  console.error('Errore non gestito:', err);
  res.status(500).json({
    error: process.env.NODE_ENV === 'production'
      ? 'Errore interno del server'
      : err.message,
  });
}
```

### Prisma Schema e Client

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
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String
  role      Role     @default(USER)
  posts     Post[]
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  @@map("users")
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  authorId  Int      @map("author_id")
  author    User     @relation(fields: [authorId], references: [id], onDelete: Cascade)
  createdAt DateTime @default(now()) @map("created_at")

  @@map("posts")
}

enum Role {
  USER
  ADMIN
}
```

```typescript
// backend/src/lib/prisma.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === 'development'
    ? ['query', 'warn', 'error']
    : ['error'],
});

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;
```

### Frontend — Client API

```typescript
// frontend/src/api/client.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:4000';

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    };

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: `Errore HTTP ${response.status}`,
      }));
      throw new Error(error.error || `Errore ${response.status}`);
    }

    return response.json();
  }

  get<T>(endpoint: string) {
    return this.request<T>(endpoint);
  }

  post<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient(API_BASE);
```

### Avvio del Progetto

```bash
# Clonare e installare dipendenze
git clone <repo-url> fullstack-app && cd fullstack-app
cd backend && npm install && cd ..
cd frontend && npm install && cd ..

# Avviare tutto con Docker Compose
docker compose up -d

# Eseguire le migrazioni del database
docker compose exec backend npx prisma migrate dev --name init

# Verificare che tutto funzioni
curl http://localhost:4000/api/health
# Frontend disponibile su http://localhost:3000
```

---

## Guida Pratica 2: Deploy in Produzione

Questa guida copre il deployment di un'applicazione full-stack su un VPS (Virtual Private Server) con Nginx come reverse proxy, SSL tramite Let's Encrypt, PM2 per il process management e CI/CD con GitHub Actions.

### Setup VPS Iniziale

```bash
# Connettersi al VPS
ssh root@your-server-ip

# Creare un utente non-root
adduser deploy
usermod -aG sudo deploy

# Configurare SSH key-based authentication
# Sul tuo computer locale:
ssh-copy-id deploy@your-server-ip

# Disabilitare login con password (sul server)
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
sudo systemctl restart sshd

# Aggiornare il sistema e installare dipendenze
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git nginx certbot python3-certbot-nginx ufw

# Configurare il firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Installare Node.js via nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22

# Installare PM2 globalmente
npm install -g pm2

# Installare Docker e Docker Compose
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker deploy
```

### Configurazione Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/app.example.com
server {
    listen 80;
    server_name app.example.com api.example.com;

    # Redirect HTTP a HTTPS (Certbot aggiungera' questo automaticamente)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.example.com;

    # Certificati SSL (gestiti da Certbot)
    ssl_certificate /etc/letsencrypt/live/app.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Servire il frontend statico
    root /var/www/app.example.com/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1000;

    # Cache per asset statici
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback — tutte le route non-file puntano a index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;

    location / {
        limit_req zone=api burst=50 nodelay;

        proxy_pass http://127.0.0.1:4000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

```bash
# Abilitare il sito e ottenere il certificato SSL
sudo ln -s /etc/nginx/sites-available/app.example.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo certbot --nginx -d app.example.com -d api.example.com
sudo systemctl reload nginx
```

### PM2 Process Management

```javascript
// ecosystem.config.cjs
module.exports = {
  apps: [
    {
      name: 'api',
      script: './backend/dist/server.js',
      instances: 'max',  // usa tutti i core della CPU
      exec_mode: 'cluster',
      env_production: {
        NODE_ENV: 'production',
        PORT: 4000,
      },
      max_memory_restart: '500M',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: './logs/api-error.log',
      out_file: './logs/api-out.log',
      merge_logs: true,
    },
  ],
};
```

```bash
# Avviare l'applicazione con PM2
pm2 start ecosystem.config.cjs --env production

# Comandi PM2 essenziali
pm2 status              # stato di tutti i processi
pm2 logs api            # log in tempo reale
pm2 monit               # dashboard interattiva
pm2 restart api         # riavvio
pm2 reload api          # riavvio zero-downtime (cluster mode)

# Salvare la configurazione per riavvio automatico dopo reboot
pm2 save
pm2 startup             # genera il comando per abilitare autostart
```

### Docker Deployment in Produzione

```yaml
# docker-compose.production.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U ${DB_USER}']
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile.production
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      PORT: 4000
      JWT_SECRET: ${JWT_SECRET}
      NODE_ENV: production
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'

  nginx:
    image: nginx:alpine
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./frontend/dist:/usr/share/nginx/html
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  pgdata:
```

### CI/CD con GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
          cache-dependency-path: |
            frontend/package-lock.json
            backend/package-lock.json

      - name: Install e test frontend
        working-directory: ./frontend
        run: |
          npm ci
          npm run lint
          npm run type-check
          npm run test -- --run

      - name: Install e test backend
        working-directory: ./backend
        run: |
          npm ci
          npm run lint
          npm run type-check
          npm run test -- --run

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Login al Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build e push immagine backend
        uses: docker/build-push-action@v6
        with:
          context: .
          file: backend/Dockerfile.production
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-backend:latest

      - name: Build frontend
        working-directory: ./frontend
        run: |
          npm ci
          npm run build

      - name: Upload frontend artifacts
        uses: actions/upload-artifact@v4
        with:
          name: frontend-dist
          path: frontend/dist

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest

    steps:
      - name: Download frontend artifacts
        uses: actions/download-artifact@v4
        with:
          name: frontend-dist
          path: frontend-dist

      - name: Deploy al server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/app
            docker compose -f docker-compose.production.yml pull
            docker compose -f docker-compose.production.yml up -d --remove-orphans
            docker image prune -f

      - name: Copia frontend al server
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          source: frontend-dist/*
          target: /var/www/app/frontend/dist
          strip_components: 1
```

---

## Guida Pratica 3: Dashboard Interna

Costruzione di una dashboard di amministrazione completa con React, TanStack Table per tabelle dati avanzate, Recharts per grafici, autenticazione JWT, operazioni CRUD e aggiornamenti in tempo reale.

### Setup e Dipendenze

```bash
# Creare il progetto con Vite
npm create vite@latest admin-dashboard -- --template react-ts
cd admin-dashboard

# Installare le dipendenze
npm install @tanstack/react-table @tanstack/react-query recharts
npm install react-router-dom react-hook-form @hookform/resolvers zod
npm install lucide-react clsx tailwind-merge
npm install -D tailwindcss @tailwindcss/vite
```

### Autenticazione

```typescript
// src/hooks/useAuth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '../api/client';

interface User {
  id: number;
  email: string;
  name: string;
  role: 'ADMIN' | 'USER';
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const { user, token } = await api.post<{ user: User; token: string }>(
          '/api/auth/login',
          { email, password }
        );
        api.setToken(token);
        set({ user, token, isAuthenticated: true });
      },

      logout: () => {
        api.setToken(null);
        set({ user: null, token: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, user: state.user }),
    }
  )
);
```

```tsx
// src/components/ProtectedRoute.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function ProtectedRoute() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
```

### Tabella Dati con TanStack Table

```tsx
// src/components/DataTable.tsx
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import { useState } from 'react';

interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T, unknown>[];
  searchPlaceholder?: string;
}

export function DataTable<T>({
  data,
  columns,
  searchPlaceholder = 'Cerca...',
}: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: { pageSize: 20 },
    },
  });

  return (
    <div className="space-y-4">
      {/* Barra di ricerca */}
      <input
        type="text"
        value={globalFilter}
        onChange={(e) => setGlobalFilter(e.target.value)}
        placeholder={searchPlaceholder}
        className="w-full max-w-sm rounded-md border px-3 py-2 text-sm"
      />

      {/* Tabella */}
      <div className="rounded-md border">
        <table className="w-full text-sm">
          <thead className="border-b bg-gray-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="cursor-pointer px-4 py-3 text-left font-medium"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {{ asc: ' ▲', desc: ' ▼' }[
                      header.column.getIsSorted() as string
                    ] ?? ''}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-b hover:bg-gray-50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginazione */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">
          Pagina {table.getState().pagination.pageIndex + 1} di{' '}
          {table.getPageCount()}
        </span>
        <div className="space-x-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="rounded border px-3 py-1 text-sm disabled:opacity-50"
          >
            Precedente
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="rounded border px-3 py-1 text-sm disabled:opacity-50"
          >
            Successiva
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Grafici con Recharts

```tsx
// src/components/DashboardCharts.tsx
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

interface RevenueData {
  mese: string;
  ricavi: number;
  spese: number;
  profitto: number;
}

export function RevenueChart({ data }: { data: RevenueData[] }) {
  return (
    <div className="rounded-lg border bg-white p-6">
      <h3 className="mb-4 text-lg font-semibold">Andamento Ricavi</h3>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="mese" />
          <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
          <Tooltip
            formatter={(value: number) => [`€${value.toLocaleString('it-IT')}`, '']}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="ricavi"
            stroke="#3b82f6"
            fill="#93c5fd"
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="spese"
            stroke="#ef4444"
            fill="#fca5a5"
            fillOpacity={0.3}
          />
          <Line
            type="monotone"
            dataKey="profitto"
            stroke="#22c55e"
            strokeWidth={2}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function UserActivityChart({ data }: { data: { giorno: string; attivi: number; nuovi: number }[] }) {
  return (
    <div className="rounded-lg border bg-white p-6">
      <h3 className="mb-4 text-lg font-semibold">Attivita' Utenti</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="giorno" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="attivi" fill="#3b82f6" name="Utenti Attivi" />
          <Bar dataKey="nuovi" fill="#22c55e" name="Nuovi Utenti" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### Operazioni CRUD con React Query

```typescript
// src/hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  createdAt: string;
}

interface CreateUserDTO {
  email: string;
  name: string;
  role: string;
}

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => api.get<User[]>('/api/users'),
    staleTime: 30_000, // 30 secondi prima di considerare i dati stale
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateUserDTO) => api.post<User>('/api/users', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: Partial<User> & { id: number }) =>
      api.put<User>(`/api/users/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/users/${id}`),
    // Optimistic update: rimuove l'utente dalla cache immediatamente
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['users'] });
      const previousUsers = queryClient.getQueryData<User[]>(['users']);
      queryClient.setQueryData<User[]>(['users'], (old) =>
        old?.filter((u) => u.id !== deletedId)
      );
      return { previousUsers };
    },
    onError: (err, id, context) => {
      // Rollback in caso di errore
      queryClient.setQueryData(['users'], context?.previousUsers);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}
```

### Aggiornamenti in Tempo Reale

```typescript
// src/hooks/useRealtimeUpdates.ts
import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export function useRealtimeUpdates() {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${import.meta.env.VITE_WS_HOST || 'localhost:4000'}/ws`;

    const connect = () => {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        switch (message.type) {
          case 'USER_CREATED':
          case 'USER_UPDATED':
          case 'USER_DELETED':
            queryClient.invalidateQueries({ queryKey: ['users'] });
            break;
          case 'STATS_UPDATED':
            queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
            break;
        }
      };

      ws.onclose = (event) => {
        if (event.code !== 1000) {
          // Riconnessione automatica con backoff esponenziale
          setTimeout(connect, 3000);
        }
      };
    };

    connect();

    return () => {
      wsRef.current?.close(1000, 'Componente smontato');
    };
  }, [queryClient]);
}
```

---

## Ambiente di Sviluppo

### VS Code: Estensioni Essenziali per Web Development

```jsonc
// .vscode/extensions.json — raccomandazioni per il team
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "prisma.prisma",
    "ms-vscode.vscode-typescript-next",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "usernamehw.errorlens",
    "eamodio.gitlens",
    "github.copilot",
    "vitest.explorer",
    "ms-azuretools.vscode-docker"
  ]
}
```

```jsonc
// .vscode/settings.json — configurazione progetto
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },
  "editor.rulers": [100],
  "editor.tabSize": 2,
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": true,

  "typescript.preferences.importModuleSpecifier": "non-relative",
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,

  "files.exclude": {
    "node_modules": true,
    ".next": true,
    "dist": true
  },

  "tailwindCSS.experimental.classRegex": [
    ["clsx\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"],
    ["cn\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"]
  ],

  "errorLens.enabledDiagnosticLevels": ["error", "warning"],
  "errorLens.excludeBySource": ["ts(80001)"]
}
```

### Configurazione ESLint + Prettier

```javascript
// eslint.config.js — ESLint flat config
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  { ignores: ['dist', 'node_modules', '*.config.*'] },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/consistent-type-imports': 'error',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
    },
  },
  prettier // deve essere l'ultimo — disabilita le regole in conflitto con Prettier
);
```

```jsonc
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf",
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

### Git Hooks con Husky + lint-staged

```bash
# Installazione
npm install -D husky lint-staged
npx husky init
```

```javascript
// package.json — aggiungere la configurazione lint-staged
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md,yml,yaml}": [
      "prettier --write"
    ],
    "*.css": [
      "prettier --write"
    ]
  }
}
```

```bash
# .husky/pre-commit
npx lint-staged
```

```bash
# .husky/commit-msg — validazione del formato dei commit
npx --no -- commitlint --edit ${1}
```

```javascript
// commitlint.config.js
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'chore', 'ci', 'revert'],
    ],
    'subject-max-length': [2, 'always', 72],
  },
};

// Esempi di commit validi:
// feat: aggiunge filtro utenti nella dashboard
// fix: risolve errore CORS su endpoint /api/reports
// refactor: estrae logica autenticazione in hook dedicato
```

---

## Risorse e Riferimenti

### Documentazione Ufficiale

- **MDN Web Docs** (developer.mozilla.org): riferimento definitivo per HTML, CSS, JavaScript e Web API
- **Node.js Documentation** (nodejs.org/docs): guida alle API core di Node.js
- **TypeScript Handbook** (typescriptlang.org/docs): guida completa al type system
- **React Documentation** (react.dev): documentazione ufficiale con tutorial interattivi
- **Vite Documentation** (vite.dev): configurazione e plugin
- **Prisma Documentation** (prisma.io/docs): schema, query, migrazioni
- **Docker Documentation** (docs.docker.com): containerizzazione e orchestrazione

### Strumenti di Debugging e Monitoring

- **Chrome DevTools Documentation** (developer.chrome.com/docs/devtools): guide dettagliate per ogni pannello
- **Sentry** (sentry.io): error tracking e performance monitoring in produzione
- **LogRocket** (logrocket.com): session replay per riprodurre bug frontend esattamente come li ha visti l'utente
- **Grafana + Prometheus**: monitoring di metriche server, database e applicative
- **Lighthouse** (integrato in Chrome DevTools): audit automatico di performance, accessibilita', SEO e best practice

### Community e Apprendimento

- **Stack Overflow** (stackoverflow.com): risposte a problemi specifici, verificare sempre la data delle risposte
- **GitHub Issues**: spesso il messaggio di errore cercato ha gia' una issue aperta con soluzione
- **Dev.to** e **Hashnode**: articoli tecnici aggiornati dalla community
- **Discord**: canali ufficiali di React, Vue, Svelte, Node.js, Prisma, Vite per supporto diretto

---

## Best Practices

1. **Riproduci prima di risolvere.** Non modificare il codice finche' non puoi riprodurre il bug in modo consistente. Se non riesci a riprodurlo, non puoi essere certo di averlo risolto. Crea un test case minimale che isolaa il problema.

2. **Leggi il messaggio di errore completamente.** Sembra ovvio, ma la maggior parte degli sviluppatori legge solo la prima riga. Lo stack trace indica il percorso esatto dell'errore. Il messaggio spesso contiene suggerimenti sulla soluzione (typo nel nome del modulo, versione incompatibile, flag mancante).

3. **Dividi e conquista.** Quando un sistema complesso fallisce, isola i componenti. Il problema e' nel frontend o nel backend? Nella query SQL o nella logica applicativa? Nella rete o nel codice? Usa `curl` per testare l'API indipendentemente dal frontend. Usa query SQL dirette per testare il database indipendentemente dall'ORM.

4. **Controlla cosa e' cambiato.** Il bug e' nuovo? `git log --oneline -20` e `git diff HEAD~5` mostrano le modifiche recenti. `git bisect` automatizza la ricerca del commit che ha introdotto il bug, dimezzando lo spazio di ricerca ad ogni passo.

5. **Monitora le risorse.** Prima di cercare bug nel codice, verifica che il sistema abbia risorse sufficienti: `htop` per CPU e RAM, `df -h` per lo spazio disco, `ss -tlnp` per le porte in ascolto, `docker stats` per i container. Un database lento spesso indica semplicemente disco pieno o RAM esaurita.

6. **Logga in modo strutturato.** Abbandona `console.log('qui')` in favore di logging strutturato con contesto: `logger.error('Pagamento fallito', { userId, orderId, errorCode, stack })`. Usa livelli di log appropriati (debug, info, warn, error) e un formato parsabile (JSON) per facilitare la ricerca nei log aggregati.

7. **Automatizza la prevenzione.** TypeScript cattura errori a compile time. ESLint cattura pattern problematici. Test automatizzati catturano regressioni. Pre-commit hook impediscono di committare codice non conforme. CI/CD impedisce di deployare codice che non passa i test. Ogni errore risolto manualmente piu' di una volta merita un controllo automatico.

8. **Mantieni gli ambienti allineati.** La frase "funziona sulla mia macchina" nasce dalla divergenza tra ambienti. Docker, file `.env.example`, lockfile (`package-lock.json`), versione Node specificata in `.nvmrc` o `package.json` (campo `engines`): ogni strumento che riduce la variabilita' tra ambienti riduce i bug specifici dell'ambiente.

9. **Documenta i bug non ovvi.** Quando risolvi un bug la cui causa non era evidente, aggiungi un commento nel codice che spieghi il perche' della soluzione. Tra sei mesi, tu stesso (o un collega) potresti essere tentato di rimuovere quella riga apparentemente inutile che in realta' previene un race condition sottile.

10. **Misura, non indovinare.** Per problemi di performance, usa gli strumenti di profiling (Chrome DevTools Performance, Node.js --inspect, `EXPLAIN ANALYZE` per SQL) invece di ottimizzare a intuito. L'ottimizzazione prematura basata su ipotesi spesso peggiora la leggibilita' senza migliorare le performance reali, perche' il collo di bottiglia era altrove.

---

*Questa guida copre gli scenari di troubleshooting e le pratiche di sviluppo piu' comuni nello sviluppo web moderno. Ogni sezione e' progettata per essere consultata indipendentemente: torna a una specifica sezione quando incontri un problema simile, e integra le guide pratiche nel tuo workflow quotidiano.*

---

## Esercizi

### Esercizio 1 — Diagnosi Sistematica con Chrome DevTools

**Obiettivo:** utilizzare tutti i pannelli principali di Chrome DevTools per diagnosticare problemi in una pagina web reale.

Scegli un sito web con problemi di performance evidenti (o usa un progetto locale volutamente degradato) e conduci un'analisi completa:

- Pannello **Network**: identifica le risorse render-blocking, le richieste che superano 1MB, le catene di reindirizzamento e le risorse senza caching (manca `Cache-Control`)
- Pannello **Performance**: registra un profilo di 5 secondi durante il caricamento, identifica i Long Task (> 50ms), il layout thrashing e il main thread blocking
- Pannello **Console**: filtra per warning e errori, identifica deprecation warning e mixed content
- Pannello **Application**: verifica lo stato dei Service Worker, il contenuto della cache, i cookie e il Local Storage
- Pannello **Lighthouse**: esegui un audit completo e confronta i risultati con quelli dei pannelli precedenti
- Produci un report con almeno 5 problemi identificati, ognuno con: pannello di diagnosi, descrizione del problema, impatto stimato e soluzione proposta

### Esercizio 2 — Debugging di Errori CORS e Network

**Obiettivo:** riprodurre, diagnosticare e risolvere scenari comuni di errori CORS e problemi di rete.

Crea un setup con un frontend (porta 3000) e un backend Express (porta 4000):

- Scenario 1: richiesta GET semplice bloccata da CORS — diagnostica leggendo il messaggio di errore completo nella Console, identifica l'header mancante, risolvi con `cors()` middleware configurato correttamente (non `*` in produzione)
- Scenario 2: richiesta POST con `Content-Type: application/json` bloccata al preflight — identifica la richiesta OPTIONS nel pannello Network, configura gli header `Access-Control-Allow-Methods` e `Access-Control-Allow-Headers`
- Scenario 3: richiesta con credenziali (`credentials: 'include'`) fallita — configura `Access-Control-Allow-Credentials: true` e `Access-Control-Allow-Origin` con il dominio specifico (non `*`)
- Scenario 4: timeout di rete — implementa retry con backoff esponenziale e timeout configurabile
- Documenta ogni scenario con: errore esatto nella Console, request/response headers nel pannello Network, soluzione applicata

### Esercizio 3 — Risoluzione di Memory Leak in Applicazione React

**Obiettivo:** identificare e risolvere memory leak in un'applicazione React usando gli strumenti di profiling.

Crea un'applicazione React con i seguenti memory leak intenzionali, poi diagnosticali e risolvili:

- Leak 1: un `useEffect` con `setInterval` che non viene pulito nel cleanup, causando aggiornamenti di stato su componente smontato
- Leak 2: un event listener globale (`window.addEventListener`) registrato nel mount ma mai rimosso
- Leak 3: una closure che mantiene un riferimento a un array di grandi dimensioni dopo che il componente viene smontato
- Leak 4: un'istanza di `AbortController` non utilizzata per cancellare fetch in corso quando il componente si smonta
- Per ogni leak: registra uno snapshot dell'heap nel pannello Memory di DevTools prima e dopo la navigazione ripetuta, identifica gli oggetti che crescono, applica la correzione e verifica che lo snapshot post-fix non mostri crescita anomala
- Documenta il delta di memoria per ogni leak prima e dopo la correzione

### Esercizio 4 — Troubleshooting di Build e Dipendenze

**Obiettivo:** diagnosticare e risolvere errori comuni di build, conflitti di dipendenze e problemi di configurazione TypeScript.

Parti da un progetto volutamente configurato con problemi e risolvili uno alla volta:

- Problema 1: `Module not found` per un path alias `@/components/Button` — verifica la configurazione di `paths` in `tsconfig.json` e `resolve.alias` in `vite.config.ts`
- Problema 2: conflitto di versione tra `react@18` e un pacchetto che richiede `react@17` come peer dependency — usa `npm ls react` per mappare l'albero delle dipendenze, risolvi con `overrides` in `package.json`
- Problema 3: errore TypeScript `Cannot find module 'X' or its corresponding type declarations` — installa `@types/X` o crea un file di dichiarazione `src/types/X.d.ts`
- Problema 4: build che produce un bundle di 2MB a causa di un import errato (`import _ from 'lodash'` invece di import cherry-pick) — usa `npx vite-bundle-visualizer` per identificare il colpevole, correggi l'import
- Problema 5: `ENOSPC: System limit for number of file watchers reached` su Linux — diagnostica con `cat /proc/sys/fs/inotify/max_user_watches`, risolvi con `sysctl`
- Per ogni problema: documenta l'errore esatto, il percorso di diagnosi e la soluzione definitiva

### Esercizio 5 — Checklist di Troubleshooting Automatizzata

**Obiettivo:** creare uno script di diagnostica automatizzata che verifichi la salute di un progetto web.

Scrivi uno script Node.js `healthcheck.mjs` che esegua i seguenti controlli e produca un report:

- Verifica che `node` e `npm` siano nelle versioni specificate in `package.json` (campo `engines`)
- Controlla che `package-lock.json` sia in sync con `package.json` (nessuna dipendenza mancante o in eccesso)
- Verifica che non ci siano vulnerabilita note con `npm audit --json` e parsa il risultato
- Controlla che i file `.env.example` e `.env` abbiano le stesse chiavi (segnala chiavi mancanti in `.env`)
- Verifica che TypeScript compili senza errori (`tsc --noEmit`)
- Controlla che ESLint non riporti errori (warning sono accettabili)
- Verifica che le porte necessarie (3000, 4000, 5432) non siano gia occupate
- Produce un report finale con stato (PASS/WARN/FAIL) per ogni controllo, tempo di esecuzione totale e suggerimenti per i controlli falliti

---

## Letture e Riferimenti

### Documentazione ufficiale

- **Chrome DevTools** — documentazione completa di tutti i pannelli di debugging, profiling e analisi. https://developer.chrome.com/docs/devtools/ (consultato: 2026-05-24)
- **Firefox Developer Tools** — strumenti di sviluppo di Firefox con funzionalita uniche come il CSS Grid Inspector. https://firefox-source-docs.mozilla.org/devtools-user/ (consultato: 2026-05-24)
- **Node.js Debugging Guide** — guida ufficiale al debugging di applicazioni Node.js con `--inspect` e Chrome DevTools. https://nodejs.org/en/learn/getting-started/debugging (consultato: 2026-05-24)
- **MDN — CORS** — specifica completa del Cross-Origin Resource Sharing con esempi di preflight e credenziali. https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS (consultato: 2026-05-24)
- **TypeScript — Troubleshooting** — guida ufficiale alla risoluzione degli errori di compilazione TypeScript. https://www.typescriptlang.org/docs/handbook/2/troubleshooting.html (consultato: 2026-05-24)
- **Vite — Troubleshooting** — sezione dedicata ai problemi comuni di configurazione e build con Vite. https://vite.dev/guide/troubleshooting (consultato: 2026-05-24)

### Libri e approfondimenti

- Paul Irish et al., *Chrome DevTools Documentation*, Google, aggiornamento continuo.
- James Shore, *The Art of Agile Development: Debugging*, O'Reilly, 2022.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Comprensione di scope, closure, event loop e prototype necessaria per debuggare errori JS |
| [06 — TypeScript](06-typescript.md) | Errori di compilazione TypeScript sono tra i problemi di build piu frequenti da diagnosticare |
| [10 — Node.js](10-nodejs.md) | Debugging server-side con `--inspect`, gestione errori asincroni e problemi di processo |
| [14 — Sicurezza Web](14-sicurezza-web.md) | CORS, CSP e mixed content sono problemi di sicurezza diagnosticati con gli strumenti trattati qui |
| [16 — Build Tools e Deploy](16-build-tools-e-deploy.md) | Errori di build, conflitti di dipendenze e configurazione della pipeline CI/CD |
| [17 — Performance Web](17-performance-web.md) | Il pannello Performance di DevTools e Lighthouse sono strumenti di diagnosi delle performance |

---

## Glossario

| Termine | Definizione |
|---|---|
| **DevTools** | Strumenti di sviluppo integrati nel browser per debugging, profiling e analisi di applicazioni web. |
| **CORS** | Cross-Origin Resource Sharing: meccanismo HTTP che permette a un server di indicare quali origini diverse possono accedere alle sue risorse. |
| **Preflight** | Richiesta OPTIONS inviata automaticamente dal browser prima di una richiesta cross-origin non semplice per verificare i permessi del server. |
| **Source map** | File che associa il codice minificato o transpiled al codice sorgente originale, permettendo il debugging nel formato leggibile. |
| **Stack trace** | Sequenza ordinata delle chiamate di funzione al momento di un errore, dal punto di origine fino alla funzione piu esterna. |
| **Memory leak** | Condizione in cui la memoria allocata non viene rilasciata quando non e piu necessaria, causando consumo crescente di RAM. |
| **Heap snapshot** | Fotografia della memoria heap del processo JavaScript in un dato istante, utilizzata per identificare oggetti non rilasciati. |
| **Long Task** | Operazione JavaScript che blocca il main thread per piu di 50 millisecondi, degradando la reattivita dell'interfaccia. |
| **Layout thrashing** | Degradazione delle performance causata da letture e scritture DOM alternate che forzano ricalcoli multipli del layout. |
| **Mixed content** | Caricamento di risorse HTTP su una pagina HTTPS, bloccato o segnalato dal browser come rischio di sicurezza. |
| **Breakpoint** | Punto di interruzione impostato nel debugger che sospende l'esecuzione del codice per ispezionare variabili e stato. |
| **Watch expression** | Espressione monitorata nel debugger il cui valore viene aggiornato automaticamente ad ogni passo di esecuzione. |
| **Network waterfall** | Visualizzazione temporale delle richieste di rete che mostra sequenza, durata e dipendenze tra le risorse caricate. |
| **Hot reload** | Aggiornamento del codice nel browser durante lo sviluppo senza perdere lo stato dell'applicazione, abilitato da HMR. |
