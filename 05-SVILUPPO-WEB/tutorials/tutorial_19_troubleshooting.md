# Tutorial 19 — Troubleshooting: Dal Principiante all'Esperto

> **Companion a:** `19-troubleshooting-e-guide-pratiche.md`
> **Scope:** metodo di diagnosi, DevTools, errori frontend ricorrenti, debug di Node.js, rete e CORS, build che si rompe solo in produzione, osservabilità e log correlati, memoria e perdite, mobile e dispositivi reali, bisezione, post-mortem
> **Prerequisiti:** tutti i tutorial precedenti — questo è il modulo che li usa insieme; in particolare `tutorial_17_performance_web.md`, `tutorial_16_build_tools_deploy.md` e `tutorial_12_database_web.md`
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Chrome DevTools · Node.js inspector · pino · OpenTelemetry · git bisect

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Il metodo: prima di toccare il codice](#a1-il-metodo-prima-di-toccare-il-codice)
  - [A2. Leggere un errore fino in fondo](#a2-leggere-un-errore-fino-in-fondo)
  - [A3. DevTools: i pannelli che risolvono davvero](#a3-devtools-i-pannelli-che-risolvono-davvero)
  - [A4. Gli errori frontend che si ripetono](#a4-gli-errori-frontend-che-si-ripetono)
  - [A5. Debug di Node.js](#a5-debug-di-nodejs)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Isolare: bisezione nello spazio e nel tempo](#b1-isolare-bisezione-nello-spazio-e-nel-tempo)
  - [B2. Rete: leggere una richiesta che fallisce](#b2-rete-leggere-una-richiesta-che-fallisce)
  - [B3. "Funziona in locale": le sei cause](#b3-funziona-in-locale-le-sei-cause)
  - [B4. Log che servono a qualcosa](#b4-log-che-servono-a-qualcosa)
  - [B5. Tracce e correlazione fra servizi](#b5-tracce-e-correlazione-fra-servizi)
  - [B6. Memoria: trovare una perdita](#b6-memoria-trovare-una-perdita)
  - [B7. I bug che si vedono solo a volte](#b7-i-bug-che-si-vedono-solo-a-volte)
  - [B8. Diagnosticare su dispositivi reali](#b8-diagnosticare-su-dispositivi-reali)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: dal sintomo al post-mortem](#c2-mini-progetto-dal-sintomo-al-post-mortem)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Debug in produzione senza fermare nulla](#d1-debug-in-produzione-senza-fermare-nulla)
  - [D2. Quando il problema è una dipendenza](#d2-quando-il-problema-è-una-dipendenza)
  - [D3. Il caso peggiore: non si riproduce](#d3-il-caso-peggiore-non-si-riproduce)
  - [D4. Il post-mortem senza colpe](#d4-il-post-mortem-senza-colpe)
  - [D5. Rendere il sistema diagnosticabile](#d5-rendere-il-sistema-diagnosticabile)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   IL SINTOMO                    LA DIAGNOSI                  LA CURA
   ──────────                    ───────────                  ───────
   "non funziona"     →   1. RIPRODURRE          →   correzione minima
   un errore in log       2. RESTRINGERE             + un test che
   una metrica          → 3. FORMULARE UN'IPOTESI →    fallisce prima
   un utente che        → 4. VERIFICARLA CON UNA →   + la domanda
   segnala                   MISURA                    "perché non lo
                          5. spiegare TUTTO           avevamo visto?"

   ┌──────────────────────────────────────────────────────────┐
   │  LE QUATTRO DOMANDE, IN QUEST'ORDINE                     │
   │   1. cosa DOVREBBE succedere, esattamente?               │
   │   2. cosa succede INVECE, esattamente?                   │
   │   3. cosa è CAMBIATO fra quando funzionava e adesso?     │
   │   4. qual è il pezzo PIÙ PICCOLO che riproduce il bug?   │
   └──────────────────────────────────────────────────────────┘

   DOVE GUARDARE, PER SINTOMO
     pagina bianca            → console del browser, poi rete
     errore 500               → log del server, con l'id di richiesta
     lento                    → profilo, non intuizione (tutorial_17)
     funziona a volte         → concorrenza, tempo, cache, dati
     "in locale funziona"     → ambiente, versioni, dati, build
```

---

# Parte A — Basi Assolute

---

## A1. Il metodo: prima di toccare il codice

> **Analogia:** un medico che prescrive prima di visitare. A volte indovina, e quando indovina impara la lezione sbagliata — che tirare a indovinare funziona. La diagnosi non è più lenta della congettura: è più lenta della congettura *fortunata*, e più veloce di tutte le altre.

```
IL METODO IN CINQUE PASSI, E PERCHÉ L'ORDINE CONTA

1. RIPRODURRE  finché non riesci a farlo accadere a comando, non
   stai correggendo: stai sperando. E non saprai se la correzione
   ha funzionato.
2. RESTRINGERE  dimezzare lo spazio del problema, ripetutamente.
   Frontend o backend? Questa funzione o quella? Prima o dopo questo
   commit? Ogni domanda deve ELIMINARE metà delle possibilità.
3. FORMULARE UN'IPOTESI PRECISA  "credo che X causi Y perché Z".
   Un'ipotesi che non si può smentire non è un'ipotesi.
4. VERIFICARLA CON UNA MISURA  un log, un breakpoint, una query.
   Non con una modifica: modificare e vedere se sparisce confonde
   la causa con il sintomo.
5. SPIEGARE TUTTO  se la tua spiegazione lascia fuori un dettaglio
   osservato ("ma perché succedeva solo il lunedì?"), non hai
   finito. Quel dettaglio è la seconda metà del bug.

⚠ IL PASSO CHE SI SALTA PIÙ SPESSO È IL PRIMO. "L'ho corretto" senza
  aver mai riprodotto significa "il sintomo non si è ripresentato
  nei dieci minuti in cui ho guardato".
```

```
LE TRE ABITUDINI CHE FANNO PIÙ DANNI
  ❌ CAMBIARE PIÙ COSE INSIEME. Se funziona, non sai quale. Se non
     funziona, hai aggiunto due variabili nuove.
  ❌ "PROVIAMO A RIAVVIARE". A volte risolve, e nasconde la causa:
     il problema torna, e la seconda volta è più difficile perché
     nessuno ha guardato la prima.
  ❌ CORREGGERE IL SINTOMO. Un `try/catch` che ingoia l'errore fa
     sparire il messaggio, non il problema — e sposta il guasto in
     un punto più lontano dalla causa.
```

---

## A2. Leggere un errore fino in fondo

```
Cannot read properties of undefined (reading 'nome')
    at ProfiloUtente (ProfiloUtente.tsx:14:23)
    at renderWithHooks (react-dom.development.js:16305:18)
    at mountIndeterminateComponent (react-dom.development.js:20074:13)
    …
```

```
COSA DICE, PEZZO PER PEZZO
  · IL TIPO: "Cannot read properties of undefined" — non è un valore
    sbagliato, è un valore ASSENTE
  · LA PROPRIETÀ: 'nome' — l'oggetto che doveva averla è undefined
  · IL PUNTO: ProfiloUtente.tsx riga 14, colonna 23 — il TUO codice
  · IL RESTO dello stack è dentro React: si salta

⚠ SI LEGGE DALLA PRIMA RIGA DEL PROPRIO CODICE, non dalla cima.
  Le righe della libreria dicono come ci si è arrivati, non perché.

E LA DOMANDA GIUSTA NON È "come evito l'errore" — un `?.` lo
nasconde — MA "perché quel valore è undefined?". Le risposte tipiche:
i dati non sono ancora arrivati, la richiesta è fallita, il campo si
chiama diversamente, l'utente non esiste.
```

```tsx
// ❌ Nascondere l'errore: la pagina non si rompe più, e mostra il
//    vuoto senza spiegare niente
//      const nome = utente?.nome ?? ''

// ✅ Distinguere i quattro stati, che sono quattro cose diverse
export function ProfiloUtente({ inCaricamento, errore, utente }: Proprieta) {
  if (inCaricamento) return <Scheletro />
  if (errore) return <Avviso>Non è stato possibile caricare il profilo.</Avviso>
  if (!utente) return <Avviso>Utente non trovato.</Avviso>
  return <h1>{utente.nome}</h1>
}
```

```
GLI ERRORI CHE NON DICONO NIENTE, E COSA SIGNIFICANO DAVVERO
  "Script error."               un errore in uno script di un'altra
    origine. Serve `crossorigin="anonymous"` sul tag e l'header CORS
    sulla risorsa, altrimenti il browser nasconde i dettagli.
  "Network error" / "Failed to fetch"  può essere: rete assente,
    CORS, certificato non valido, richiesta annullata, o un blocco
    dell'estensione. Il pannello Network distingue.
  "undefined is not a function"  spesso un import sbagliato:
    `import X` invece di `import { X }`, o un modulo CJS/ESM misto.
```

---

## A3. DevTools: i pannelli che risolvono davvero

```
CONSOLE
  · `console.table(elenco)` per gli array di oggetti: si legge
  · `console.group` / `groupEnd` per annidare
  · il filtro per livello, e "Preserve log" per non perdere tutto a
    ogni navigazione
  ⚠ "Hide network" nascosto nelle impostazioni fa sparire gli errori
    di rete dalla console: se la console è stranamente vuota,
    controllalo.

SOURCES
  · breakpoint condizionale: clic destro sul numero di riga →
    "Add conditional breakpoint" → `id === 42`. Evita di fermarsi
    mille volte.
  · logpoint: come un console.log, ma senza modificare il codice —
    e senza rischiare di committarlo
  · "Pause on exceptions", anche su quelle catturate: trova gli
    errori che qualcuno sta ingoiando
  · "Never pause here" per saltare il codice delle librerie

NETWORK
  · la colonna "Initiator" dice CHI ha fatto la richiesta
  · "Copy as fetch" ricrea la richiesta nella console, per provarla
  · "Disable cache" con DevTools aperti
  · il filtro `status-code:500` o `larger-than:1M`

APPLICATION
  · cookie con i loro flag, storage, cache del service worker
  · "Clear site data" quando lo stato locale è la causa

PERFORMANCE e MEMORY  → tutorial_17
```

```javascript
// I console meno noti, e più utili di console.log
console.assert(totale > 0, 'totale non positivo', { totale, righe })
console.count('render')              // quante volte si passa di qui
console.time('query'); console.timeEnd('query')
console.trace()                      // come ci si è arrivati

// E la tecnica che risolve i bug "chi ha cambiato questo valore":
// un getter/setter temporaneo che si ferma alla scrittura
let _stato = stato
Object.defineProperty(oggetto, 'stato', {
  get: () => _stato,
  set(valore) {
    debugger // eslint-disable-line no-debugger
    _stato = valore
  },
})
```

---

## A4. Gli errori frontend che si ripetono

```
1. "Cannot read properties of undefined"
   → i dati non sono ancora arrivati. Non si tappa con `?.`: si
     distinguono caricamento, errore, vuoto e successo (A2).

2. LA PAGINA È BIANCA E LA CONSOLE È VUOTA
   → un errore durante il rendering che ha smontato tutto, oppure
     lo script non è stato caricato affatto. Guarda PRIMA il
     pannello Network: se il bundle è 404, la console non dirà nulla.
     E aggiungi un Error Boundary, che almeno mostra qualcosa.

3. "Objects are not valid as a React child"
   → si sta rendendo un oggetto invece di una sua proprietà.
     Spesso è un errore: `{errore}` invece di `{errore.message}`.

4. L'INTERFACCIA NON SI AGGIORNA DOPO UNA MODIFICA
   → si è mutato lo stato invece di sostituirlo.
     `elenco.push(x); setElenco(elenco)` non cambia il riferimento,
     e React non ridisegna. `setElenco([...elenco, x])` sì.

5. UN CICLO INFINITO DI RENDERING
   → un `useEffect` che imposta uno stato che è anche fra le sue
     dipendenze, o un oggetto/array creato inline nelle dipendenze
     (è nuovo a ogni render).

6. GLI ELEMENTI DI UNA LISTA SI COMPORTANO IN MODO STRANO
   → `key={indice}`: quando l'elenco si riordina, React associa lo
     stato alla posizione invece che all'elemento. La chiave deve
     essere l'identificativo stabile del dato.

7. IL VALORE È SEMPRE QUELLO INIZIALE DENTRO UN CALLBACK
   → closure stale: il callback ha catturato lo stato di quel
     render. La forma funzionale (`setX(x => x + 1)`) o un ref
     risolvono.

8. "Hydration failed" / "Text content did not match"
   → il server e il client hanno prodotto HTML diverso. Le cause:
     `Date.now()`, `Math.random()`, `window` letto durante il
     rendering, o HTML non valido (un `<div>` dentro un `<p>`).
```

---

## A5. Debug di Node.js

```powershell
# L'inspector: si connette Chrome DevTools a un processo Node
node --inspect dist/server.js
# --inspect-brk si ferma alla prima riga: per i problemi di avvio
node --inspect-brk dist/server.js
# Poi: chrome://inspect → "Open dedicated DevTools for Node"

# Su un processo GIÀ IN ESECUZIONE, senza riavviarlo
node --inspect=0.0.0.0:9229 dist/server.js
# ⚠ MAI esporre la porta 9229 su internet: dà esecuzione di codice
#   arbitrario. In produzione si apre un tunnel SSH.
```

```typescript
// I flag diagnostici che risolvono senza debugger
//   --trace-warnings      l'origine di ogni avviso, stack compreso
//   --trace-uncaught      lo stack completo delle eccezioni non gestite
//   --trace-exit          chi ha chiamato process.exit()
//   --cpu-prof            un profilo della CPU, apribile in DevTools

// E i due eventi che non vanno mai lasciati senza gestore
process.on('unhandledRejection', (motivo) => {
  registro.fatal({ motivo }, 'promise rifiutata senza gestore')
  process.exit(1)
})

process.on('uncaughtException', (errore) => {
  registro.fatal({ errore }, 'eccezione non catturata')
  // ⚠ Si REGISTRA e si TERMINA: dopo un'eccezione non catturata lo
  //   stato del processo è inaffidabile, e proseguire produce bug
  //   peggiori del crash
  process.exit(1)
})
```

```
I TRE SINTOMI PIÙ COMUNI SUL SERVER
  IL SERVER NON RISPONDE PIÙ, senza errori
    → qualcosa blocca l'event loop: un ciclo lungo, una regex
      catastrofica, `nextTick` ricorsivo. `monitorEventLoopDelay`
      lo conferma, `--cpu-prof` trova la funzione (tutorial_10 §B1).
  LA MEMORIA CRESCE E NON SCENDE
    → perdita: due heap snapshot a confronto (B6).
  LE RICHIESTE SI ACCODANO
    → il pool di connessioni al database è saturo, o una query è
      diventata lenta (tutorial_12 §B5).
```

---

# Parte B — Comprensione Profonda

---

## B1. Isolare: bisezione nello spazio e nel tempo

> **Analogia:** una serie di lampadine natalizie che non si accende. Provarle una per una su cinquanta lampadine sono cinquanta prove. Staccare a metà e vedere quale metà è spenta sono sei prove. È la stessa differenza fra cercare un bug leggendo il codice e dimezzare.

```
BISEZIONE NELLO SPAZIO — dove
  1. Frontend o backend?  la stessa richiesta con curl: se fallisce
     anche lì, il frontend è innocente.
  2. Il tuo codice o una dipendenza?  un esempio minimo che usa solo
     la libreria.
  3. Quale parte del componente?  si commenta metà del JSX.
  4. Quali dati?  con un record va e con un altro no → è nei dati,
     non nel codice.

⚠ OGNI DOMANDA DEVE DIMEZZARE. "Provo a cambiare questa riga" non
  dimezza niente: è una congettura travestita da esperimento.
```

```powershell
# BISEZIONE NEL TEMPO — quando. `git bisect` trova il commit
# colpevole in log2(n) prove: su mille commit, dieci.
git bisect start
git bisect bad                 # HEAD è rotto
git bisect good v2.3.0         # questo tag funzionava
# git propone un commit a metà; si prova e si risponde:
git bisect good   # oppure: git bisect bad
# … dieci volte, e stampa il commit colpevole
git bisect reset
```

```powershell
# E la forma automatica: uno script che esce 0 se va bene e 1 se no
git bisect start HEAD v2.3.0
git bisect run pnpm vitest run test/riproduce-il-bug.test.ts
# Trova il commit da solo, mentre fai altro
```

```
⚠ PERCHÉ `git bisect run` VALE PIÙ DI QUANTO SEMBRI: costringe a
  scrivere PRIMA un test che riproduce il bug. Quel test resta, ed è
  la parte più duratura della correzione.

⚠ E IL CASO IN CUI SI INCEPPA: un commit intermedio che non compila.
  `git bisect skip` lo salta; se sono molti, conviene bisecare sui
  merge (`--first-parent`).
```

---

## B2. Rete: leggere una richiesta che fallisce

```
IL PANNELLO NETWORK, IN ORDINE DI LETTURA
  1. LA RICHIESTA C'È?  se no, il problema è PRIMA: il codice non
     l'ha inviata, o un'estensione l'ha bloccata.
  2. LO STATO
     (failed)  rete, DNS, certificato, CORS, o annullata
     0         quasi sempre CORS o richiesta annullata
     4xx       il client ha sbagliato: guarda il corpo della risposta
     5xx       il server ha sbagliato: vai nei suoi log con l'id
     304       non modificata: sta usando la cache, ed è corretto
  3. LE INTESTAZIONI  di richiesta E di risposta. La metà dei
     problemi di rete si vede qui.
  4. IL TEMPO  la scheda "Timing" separa DNS, connessione, TLS,
     attesa del server (TTFB) e download. Dice DOVE si perde tempo.
```

```
GLI ERRORI CORS, E COSA SIGNIFICANO DAVVERO
  "No 'Access-Control-Allow-Origin' header"
    → il server non ha risposto con l'header. ⚠ Spesso perché la
      richiesta ha prodotto un ERRORE prima di arrivare al middleware
      CORS: un 500 senza header CORS si presenta come errore CORS, e
      si cerca nel posto sbagliato.
  "Response to preflight request doesn't pass"
    → la OPTIONS non è gestita, o un header personalizzato non è in
      `allowedHeaders`. Guarda la richiesta OPTIONS, non la POST.
  "credentials mode is 'include'"
    → non si può usare `*` con le credenziali: serve l'origine esatta.
  ⚠ CORS È UNA REGOLA DEL BROWSER: `curl` funziona sempre. Se curl
    va e il browser no, il problema è nelle intestazioni, non nel
    server.
```

```powershell
# Riprodurre fuori dal browser separa le variabili
curl -i -X POST https://api.esempio.it/ordini `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $env:TOKEN" `
  -d '{"cliente":"prova"}'

# Simulare il preflight: se questo fallisce, la POST non partirà mai
curl -i -X OPTIONS https://api.esempio.it/ordini `
  -H "Origin: https://app.esempio.it" `
  -H "Access-Control-Request-Method: POST" `
  -H "Access-Control-Request-Headers: content-type,authorization"
```

---

## B3. "Funziona in locale": le sei cause

```
1. VERSIONI DIVERSE
   Node, il gestore di pacchetti, il database. `.nvmrc`,
   `packageManager` e `engines` chiudono il caso (tutorial_16 §A3).

2. VARIABILI D'AMBIENTE
   Una manca, o ha un valore diverso. ⚠ La validazione all'avvio con
   Zod trasforma un bug incomprensibile in un messaggio chiaro.

3. DATI DIVERSI
   In locale ci sono dieci record puliti; in produzione due milioni
   con valori nulli, accenti, date del 1900 e duplicati. Molti bug
   sono nei dati, e si riproducono solo con una copia anonimizzata
   della produzione.

4. FILESYSTEM CASE-INSENSITIVE
   Windows e macOS aprono `./Utente.ts` anche se il file si chiama
   `utente.ts`. Linux no, e la build in CI fallisce.

5. LA BUILD È DIVERSA DALLO SVILUPPO
   Vite in sviluppo non impacchetta. Minificazione, tree shaking e
   pre-bundling esistono solo nella build.
   ➜ `pnpm build && pnpm preview` prima di ogni push.

6. CONCORRENZA E LATENZA
   In locale la risposta arriva in 2 ms e l'ordine degli eventi è
   sempre lo stesso. In produzione una richiesta lenta cambia
   l'ordine, e un bug di concorrenza che non si vedeva compare.
   ➜ DevTools → Network → "Slow 4G" riproduce metà di questi casi.
```

```powershell
# Riprodurre l'ambiente di produzione in locale: il modo più rapido
# di eliminare le prime cinque cause insieme
docker compose -f compose.yml -f compose.prod.yml up --build

# E un dump anonimizzato della produzione per la causa 3
pg_dump --schema-only produzione | psql locale
psql produzione -c "COPY (SELECT … con i dati mascherati) TO STDOUT" | psql locale
```

---

## B4. Log che servono a qualcosa

```
❌ IL LOG CHE NON SERVE
   console.log('qui')
   console.log(dati)
   console.log('errore', e)

   Non ha un livello, non ha un contesto, non è cercabile, e in
   produzione si perde in mezzo a diecimila righe uguali.
```

```typescript
// ✅ Log strutturato: ogni riga è JSON, con livello e contesto
import pino from 'pino'

export const registro = pino({
  level: process.env['LOG_LEVEL'] ?? 'info',
  // ⚠ La redazione va CONFIGURATA, non lasciata alla disciplina di
  //   chi scrive le chiamate (tutorial_13 §D5)
  redact: ['req.headers.authorization', 'req.headers.cookie', '*.password', '*.token'],
  formatters: { level: (etichetta) => ({ level: etichetta }) },
})

// Ogni riga porta il contesto: si può cercare, filtrare, aggregare
registro.info({ idRichiesta, idUtente, idOrdine, durataMs: 142 }, 'ordine creato')
registro.error({ idRichiesta, errore, query: 'elencaOrdini' }, 'query fallita')
```

```
I LIVELLI, E QUANDO USARLI
  fatal  il processo sta per terminare
  error  un'operazione è fallita e qualcuno deve saperlo
  warn   qualcosa di anomalo che non ha impedito l'operazione
  info   eventi di dominio: ordine creato, utente autenticato
  debug  dettagli utili solo mentre si indaga. Spento in produzione,
         e accendibile per un singolo utente o per una finestra di
         tempo — non per tutti.
  trace  quasi mai

⚠ IL LIVELLO SBAGLIATO È PEGGIO DEL LOG ASSENTE. Se tutto è `error`,
  gli allarmi diventano rumore e nessuno li guarda più; se tutto è
  `info`, i problemi veri sono invisibili.

E LA REGOLA CHE RENDE UN LOG UTILE A CHI INDAGA: deve rispondere a
"cosa stava succedendo", non a "sono arrivato qui". Un log senza
identificativo di richiesta e senza i valori in gioco è un
`console.log('qui')` con una formattazione più elegante.
```

---

## B5. Tracce e correlazione fra servizi

```
IL PROBLEMA: una richiesta attraversa il frontend, un gateway, due
servizi e un database. L'utente vede un errore. In quale dei cinque?
Senza correlazione, si guardano cinque insiemi di log separati e si
confrontano gli orari.
```

```typescript
// L'identificativo di richiesta: la versione minima, e già
// sufficiente per il 90% dei casi
import { AsyncLocalStorage } from 'node:async_hooks'
import { randomUUID } from 'node:crypto'
import type { RequestHandler } from 'express'

const contesto = new AsyncLocalStorage<{ idRichiesta: string }>()

export const correlazione: RequestHandler = (richiesta, risposta, prossimo) => {
  // Se arriva da monte, si PROPAGA invece di generarne uno nuovo:
  // è ciò che tiene insieme i servizi
  const idRichiesta = richiesta.get('X-Request-Id') ?? randomUUID()
  risposta.setHeader('X-Request-Id', idRichiesta)
  contesto.run({ idRichiesta }, () => prossimo())
}

// Ogni log lo porta con sé, senza che nessuno lo passi come parametro
export const registroConContesto = registro.child({
  get idRichiesta() {
    return contesto.getStore()?.idRichiesta
  },
})
```

```
IL TRACCIAMENTO DISTRIBUITO (OpenTelemetry) fa lo stesso, in modo
strutturato: ogni operazione è uno SPAN con durata, e gli span si
annidano in una TRACCIA. Il risultato è un diagramma a cascata che
mostra dove sono andati i 3,2 secondi — e nove volte su dieci la
risposta è visibile senza leggere una riga di codice.

  richiesta HTTP           ████████████████████ 3200 ms
    ├─ autenticazione      ██                     45 ms
    ├─ query ordini        ████                  180 ms
    └─ servizio spedizioni ████████████████     2900 ms  ← eccolo
         └─ timeout + 2 ritentativi

⚠ E LA PARTE CHE RENDE TUTTO INUTILE SE MANCA: l'identificativo deve
  arrivare fino al CLIENT, ed essere mostrato nel messaggio d'errore.
  Senza, l'utente scrive "non funziona" e si cerca "intorno alle
  14:30 di ieri" fra centomila richieste.
```

---

## B6. Memoria: trovare una perdita

```
IL SINTOMO: la memoria cresce e non scende mai. Nel browser, la
scheda diventa lenta dopo venti minuti; sul server, il processo
viene terminato dal sistema o va in "heap out of memory".

⚠ NON OGNI CRESCITA È UNA PERDITA: la garbage collection è pigra, e
  la memoria sale e scende a denti di sega. Il segnale è il MINIMO
  che sale: dopo ogni raccolta il livello di base è più alto di prima.
```

```
LA PROCEDURA, NEL BROWSER
  1. DevTools → Memory → Heap snapshot subito dopo il caricamento
  2. usare l'applicazione: navigare, aprire e chiudere la stessa
     vista dieci volte
  3. forzare la garbage collection (l'icona del cestino)
  4. secondo snapshot → "Comparison": cosa è cresciuto e non è sceso
  5. il segnale più chiaro sono i "Detached HTMLElement": nodi
     rimossi dal DOM che qualcosa trattiene ancora

LE QUATTRO CAUSE, IN ORDINE DI FREQUENZA
  1. listener non rimossi (trattengono la closure, e con essa tutto)
  2. timer non fermati
  3. osservatori non disconnessi
  4. una Map o un array globale che cresce e non si svuota
```

```typescript
// Un AbortController risolve tre cause su quattro con una riga
export function monta(elemento: HTMLElement) {
  const controller = new AbortController()
  const { signal } = controller

  addEventListener('resize', suRidimensionamento, { signal })
  addEventListener('scroll', suScorrimento, { signal, passive: true })

  const osservatore = new IntersectionObserver(suIntersezione)
  osservatore.observe(elemento)

  return () => {
    controller.abort() // rimuove TUTTI i listener registrati col signal
    osservatore.disconnect()
  }
}
```

```powershell
# SUL SERVER: uno snapshot a comando, senza riavviare
node --heapsnapshot-signal=SIGUSR2 dist/server.js
# poi, da un altro terminale:
kill -USR2 <pid>
# Il file .heapsnapshot si apre in Chrome DevTools → Memory
```

---

## B7. I bug che si vedono solo a volte

```
"A VOLTE" NON ESISTE: esiste una condizione che non hai ancora
identificato. Le sei famiglie, con il modo di riconoscerle.

1. CONCORRENZA  due operazioni che si sovrappongono. Si riconosce
   perché succede sotto carico, o con un doppio clic, o quando la
   rete è lenta. → tutorial_12 §B4 (lost update), §B5 (pool)
2. TEMPO  fallisce a fine mese, a mezzanotte, in un fuso diverso, o
   al cambio dell'ora legale. → fissare TZ e usare un orologio finto
3. CACHE  la prima richiesta va e la seconda no (o viceversa).
   → provare con la cache disabilitata, e in incognito
4. ORDINE  dipende da quale richiesta arriva prima. Due `fetch` in
   parallelo che scrivono lo stesso stato: vince l'ultima che
   risponde, non l'ultima che è partita.
5. DATI  succede solo su certi record: un valore nullo, un accento,
   una stringa vuota, un numero molto grande.
6. AMBIENTE  solo su un browser, un dispositivo, una rete aziendale
   con un proxy.
```

```typescript
// La corsa fra due richieste: il bug d'ordine più comune nel
// frontend. L'utente digita "ab", partono due ricerche, e quella
// per "a" risponde DOPO quella per "ab": si vedono i risultati
// sbagliati.
let ultimaRichiesta = 0

async function cerca(termine: string) {
  const mia = ++ultimaRichiesta
  const risultati = await fetch(`/api/cerca?q=${encodeURIComponent(termine)}`).then((r) => r.json())

  // Si scarta il risultato se nel frattempo ne è partita un'altra
  if (mia !== ultimaRichiesta) return
  mostra(risultati)
}

// La forma migliore: annullare la precedente, così non si spreca
// nemmeno la banda
let controller: AbortController | null = null

async function cercaConAnnullamento(termine: string) {
  controller?.abort()
  controller = new AbortController()

  try {
    const risposta = await fetch(`/api/cerca?q=${encodeURIComponent(termine)}`, {
      signal: controller.signal,
    })
    mostra(await risposta.json())
  } catch (errore) {
    // AbortError è previsto: non è un errore da mostrare
    if ((errore as Error).name !== 'AbortError') throw errore
  }
}
```

```
COME SI RENDE DETERMINISTICO UN BUG INTERMITTENTE
  · ESAGERARE LA CONDIZIONE: rallentare la rete a 20 kB/s, mettere
    un `await sleep(2000)` nel punto sospetto, lanciare cento
    richieste in parallelo
  · RIPETERE: `--repeat-each=50` su un test end-to-end
  · REGISTRARE TUTTO nel punto sospetto e lasciarlo girare finché
    non si ripresenta: il log del momento vale più di dieci ipotesi
```

---

## B8. Diagnosticare su dispositivi reali

```
IL SIMULATORE NON BASTA: non ha lo stesso motore di rendering, la
stessa memoria, la stessa gestione del tocco, né le stesse
estensioni e impostazioni di privacy.

ANDROID  chrome://inspect da desktop, con il telefono collegato via
  USB e il debug USB attivo: DevTools completi sulla pagina reale.
IOS      Safari desktop → Sviluppo → il dispositivo. Richiede
  "Web Inspector" attivo nelle impostazioni di Safari sul telefono.
⚠ Su iOS TUTTI i browser usano WebKit: provare su Chrome per iOS non
  è provare su Chrome.

QUANDO IL DISPOSITIVO NON È COLLEGABILE
  · un raccoglitore di errori (Sentry) con l'user agent e il contesto
  · un endpoint di diagnostica che registra `navigator.userAgent`,
    la dimensione dello schermo e le funzionalità disponibili
  · far riprodurre all'utente con una registrazione dello schermo
```

```
I PROBLEMI CHE SI VEDONO SOLO SU MOBILE
  · 100vh include la barra degli indirizzi, che compare e scompare:
    il layout salta. → `100dvh`
  · l'input zooma se il font è sotto i 16px su iOS
  · `:hover` resta "attaccato" dopo un tocco
  · la memoria è molto minore: una lista lunga che sul desktop
    scorre, sul telefono fa terminare la scheda
  · le impostazioni di privacy bloccano cookie di terze parti e
    storage in modi che il desktop non riproduce
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Dalla pagina bianca alla causa

**Obiettivo:** la dashboard mostra una pagina bianca in produzione. In locale funziona. Trovare la causa con il metodo, non a tentativi.

```
# I DATI DI PARTENZA
#   · la pagina è bianca, nessun contenuto
#   · in locale funziona
#   · è successo dopo il rilascio di stamattina
```

```
# PASSO 1 — RIPRODURRE
#   Apri la produzione con DevTools. Riproduce sempre? Sì.
#   → si può indagare.

# PASSO 2 — GUARDARE, IN QUEST'ORDINE
#   1. CONSOLE
#      Uncaught SyntaxError: Unexpected token '<' (at index.a3f9.js:1)
#      ← Un file JavaScript che comincia con '<' non è JavaScript:
#        è HTML. Il server ha risposto con una pagina invece del bundle.
#   2. NETWORK
#      index.a3f9.js   200   text/html   1,2 kB
#      ← Stato 200, ma il TIPO è text/html e la dimensione è
#        assurdamente piccola. È la pagina 404 del server, servita
#        con stato 200 dal fallback della SPA.
#   3. Il contenuto della risposta: <!DOCTYPE html>… conferma.

# PASSO 3 — L'IPOTESI PRECISA
#   "Il file index.a3f9.js non esiste sul server; il fallback della
#    SPA restituisce index.html per qualunque percorso non trovato,
#    quindi con stato 200 invece di 404."

# PASSO 4 — VERIFICARLA
#   curl -I https://esempio.it/assets/index.a3f9.js
#     → content-type: text/html   ✅ ipotesi confermata
#   E sul server: ls dist/assets/ → il file si chiama index.b1e4.js
#   ← l'impronta è DIVERSA
```

```
# LA CAUSA
#   index.html è stato servito dalla CDN con una cache lunga: punta
#   ancora agli asset della build PRECEDENTE, che il rilascio ha
#   sostituito. Il browser chiede un file che non esiste più.
#
# LA CORREZIONE — due parti
#   1. IMMEDIATA: invalidare index.html sulla CDN
#   2. STRUTTURALE, perché non si ripeta:
#      · index.html → Cache-Control: no-cache (verifica sempre)
#      · gli asset con impronta → immutable, un anno
#      · il fallback della SPA NON deve rispondere per /assets/*:
#        un file mancante deve dare 404, non una pagina HTML
#      · conservare gli asset delle build precedenti per qualche
#        giorno: chi ha la pagina aperta durante il rilascio non si
#        rompe
```

```typescript
// La difesa lato client, che trasforma un errore incomprensibile in
// un'azione: un import dinamico fallito propone il ricaricamento
window.addEventListener('vite:preloadError', (evento) => {
  evento.preventDefault()
  mostraAvviso('È disponibile una versione aggiornata.', {
    azione: { etichetta: 'Ricarica', esegui: () => location.reload() },
  })
})
```

```
# PASSO 5 — SPIEGARE TUTTO
#   "Perché in locale funzionava?" Perché in locale non c'è CDN e
#   index.html non è in cache. Il dettaglio torna: la spiegazione è
#   completa.
#   "Perché non ce ne siamo accorti?" Nessun controllo dopo il
#   rilascio. → un test di fumo che carica la pagina e verifica che
#   il bundle risponda con application/javascript (tutorial_16 §C2).
```

---

### Esercizio 2 — Un endpoint lento in modo intermittente

**Obiettivo:** `/api/ordini` risponde in 80 ms di solito e in 4 secondi qualche volta. Trovare la causa.

```
# I DATI DI PARTENZA
#   p50  82 ms · p95  310 ms · p99  4.100 ms
#   ← La media (140 ms) direbbe che va tutto bene: è il p99 a
#     mostrare il problema, e riguarda un utente su cento.
```

```sql
-- PASSO 1 — È IL DATABASE? pg_stat_statements ordinato per tempo
SELECT round(mean_exec_time::numeric, 1)   AS ms_medi,
       round(stddev_exec_time::numeric, 1) AS deviazione,
       calls, left(query, 70)
FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 5;

--   ms_medi  deviazione  calls    query
--     12.4       3.1     84.201   SELECT … FROM ordini WHERE utente_id = $1
--   1840.2    1620.8      1.204   SELECT … FROM ordini WHERE creato_il > $1
--                ↑ deviazione enorme: a volte veloce, a volte no
```

```
# PASSO 2 — L'IPOTESI, E LA VERIFICA
#   "La seconda query a volte usa l'indice e a volte no."
#
#   EXPLAIN ANALYZE con due parametri diversi:
#     creato_il > now() - interval '1 day'   → Index Scan,   8 ms
#     creato_il > now() - interval '90 days' → Seq Scan,  1900 ms
#
#   ← Il planner stima che oltre una certa quota di righe la
#     scansione completa sia più veloce dell'indice. Ha ragione in
#     astratto: il problema è che l'utente chiede novanta giorni e
#     poi ne guarda venti.
```

```
# PASSO 3 — MA C'È UN SECONDO SINTOMO CHE NON TORNA
#   Il p99 è 4.100 ms, e la query più lenta ne fa 1.900. Mancano
#   duemila millisecondi: la spiegazione è INCOMPLETA.
#
#   pg_stat_activity durante un picco:
#     wait_event_type = 'Client' su 18 connessioni su 20
#   ← Il pool è saturo. Mentre la query lenta occupa una connessione
#     per due secondi, le altre richieste ASPETTANO di averne una.
#
#   Ecco la seconda metà: la query lenta non rallenta solo se stessa,
#   rallenta tutti quelli che arrivano nel frattempo.
```

```sql
-- LA CORREZIONE 1 — l'indice parziale, e un limite sull'intervallo
CREATE INDEX CONCURRENTLY idx_ordini_recenti
  ON ordini (creato_il DESC, id DESC)
  WHERE stato IN ('pagato', 'spedito');
```

```typescript
// LA CORREZIONE 2 — l'intervallo massimo diventa parte del
// contratto: senza, un client può sempre chiedere tre anni
const SchemaFiltri = z
  .object({
    da: z.coerce.date(),
    a: z.coerce.date(),
    limite: z.coerce.number().int().min(1).max(100).default(20),
  })
  .refine((f) => f.a.getTime() - f.da.getTime() <= 31 * 24 * 3600 * 1000, {
    message: "L'intervallo non può superare 31 giorni",
    path: ['a'],
  })
```

```
# LA CORREZIONE 3 — E LA PARTE STRUTTURALE
#   · `statement_timeout = '5s'` sul ruolo dell'applicazione: una
#     query fuori controllo viene interrotta invece di occupare una
#     connessione. Il singolo utente riceve un errore; gli altri
#     novantanove continuano a essere serviti.
#   · un allarme sul p99, non sulla media
#
# IL RISULTATO
#   p50 78 ms · p95 96 ms · p99 210 ms
#
# ⚠ La lezione del passo 3: quando i numeri non tornano, la
#   spiegazione è incompleta. Fermarsi alla prima causa avrebbe
#   lasciato in piedi metà del problema.
```

---

### Esercizio 3 — Il bug che si vede solo qualche volta

**Obiettivo:** ogni tanto un ordine risulta con il totale sbagliato. Nessuno riesce a riprodurlo.

```
# I DATI DI PARTENZA
#   · circa un ordine su duecento ha un totale che non corrisponde
#     alla somma delle righe
#   · sempre PIÙ BASSO del corretto
#   · nessun errore nei log
```

```
# PASSO 1 — RESTRINGERE CON I DATI, non con il codice
#   La query che trova gli ordini sbagliati è già metà diagnosi:
#
#   SELECT o.id, o.creato_il, o.totale_centesimi,
#          sum(r.quantita * r.prezzo_unitario_centesimi) AS atteso
#   FROM ordini o JOIN righe_ordine r ON r.ordine_id = o.id
#   GROUP BY o.id HAVING o.totale_centesimi <> sum(…);
#
#   Il risultato mostra due cose:
#    · succede solo a ordini con PIÙ DI UNA riga
#    · la differenza è sempre il valore di UNA riga esatta
#    · e gli orari sono a gruppi: due o tre ordini nello stesso secondo
#
#   ← Tre indizi che puntano tutti nella stessa direzione: la
#     concorrenza.
```

```typescript
// PASSO 2 — IL CODICE, riletto con l'ipotesi in mente
export async function aggiungiRiga(ordineId: bigint, riga: NuovaRiga) {
  await db.rigaOrdine.create({ data: { ordineId, ...riga } })

  // ⚠ LEGGI-CALCOLA-SCRIVI su una risorsa condivisa, fuori da una
  //   transazione: è il lost update del tutorial_12 §B4
  const righe = await db.rigaOrdine.findMany({ where: { ordineId } })
  const totale = righe.reduce((s, r) => s + r.quantita * r.prezzoUnitarioCentesimi, 0)

  await db.ordine.update({ where: { id: ordineId }, data: { totaleCentesimi: totale } })
}

// La sequenza che produce il bug:
//   A inserisce la riga 1        B inserisce la riga 2
//   A legge: [riga1]             B legge: [riga1, riga2]
//   B scrive: totale = 1+2       A scrive: totale = 1   ← sovrascrive
```

```typescript
// PASSO 3 — RIPRODURLO, che è la prova che l'ipotesi è giusta
it('due righe aggiunte insieme non perdono il totale', async () => {
  const ordine = await creaOrdine()

  await Promise.all([
    aggiungiRiga(ordine.id, { quantita: 1, prezzoUnitarioCentesimi: 1000 }),
    aggiungiRiga(ordine.id, { quantita: 1, prezzoUnitarioCentesimi: 2000 }),
  ])

  const aggiornato = await db.ordine.findUniqueOrThrow({ where: { id: ordine.id } })
  expect(aggiornato.totaleCentesimi).toBe(3000) // ← fallisce, come previsto
})
```

```typescript
// PASSO 4 — LA CORREZIONE: il calcolo dentro la transazione, e la
// riga bloccata finché non si è finito
export async function aggiungiRiga(ordineId: bigint, riga: NuovaRiga) {
  return db.$transaction(async (tx) => {
    // FOR UPDATE blocca l'ordine: la seconda transazione aspetta
    // qui, e quando riparte legge il totale aggiornato
    await tx.$executeRaw`SELECT id FROM ordini WHERE id = ${ordineId} FOR UPDATE`

    await tx.rigaOrdine.create({ data: { ordineId, ...riga } })

    const righe = await tx.rigaOrdine.findMany({ where: { ordineId } })
    const totale = righe.reduce((s, r) => s + r.quantita * r.prezzoUnitarioCentesimi, 0)

    await tx.ordine.update({ where: { id: ordineId }, data: { totaleCentesimi: totale } })
  })
}
```

```
# PASSO 5 — E LA DIFESA CHE VALE PIÙ DELLA CORREZIONE
#   Un vincolo che rende lo stato incoerente IMPOSSIBILE, invece di
#   improbabile: un trigger che ricalcola il totale a ogni modifica
#   delle righe. Così il totale non è un dato che qualcuno deve
#   ricordarsi di aggiornare — è una conseguenza.
#
#   E una query di controllo periodica che confronta i totali: se un
#   giorno un percorso nuovo aggirasse il trigger, si scoprirebbe in
#   un'ora invece che da una contestazione.
#
# ⚠ LA LEZIONE: "non si riproduce" quasi sempre significa
#   "non ho ancora identificato la condizione". Qui la condizione
#   era nei DATI (ordini con più righe, creati nello stesso secondo),
#   e si è trovata interrogando il database — non leggendo il codice.
```

---

## C2. Mini-progetto: dal sintomo al post-mortem

L'esercizio chiave del modulo: prendere un incidente reale e portarlo dalla segnalazione alla correzione strutturale, documentando ogni passo.

```
LA STRUTTURA DI UN'INDAGINE, DA RIEMPIRE MENTRE SI LAVORA

1. SINTOMO      cosa vede l'utente, con parole sue e con un esempio
                concreto (un id, un orario, uno screenshot)
2. IMPATTO      quanti utenti, da quando, quanto è grave. Decide
                l'urgenza — e se serve una mitigazione immediata.
3. RIPRODUZIONE i passi esatti. Se non si riproduce, cosa si è
                provato e cosa si sa delle condizioni.
4. INDAGINE     ogni ipotesi, come è stata verificata, e l'esito —
                comprese quelle SCARTATE: senza, la persona
                successiva le riproverà tutte.
5. CAUSA        la spiegazione che copre TUTTI i sintomi osservati
6. CORREZIONE   immediata (mitigazione) e strutturale (perché non
                si ripeta)
7. PREVENZIONE  il test, l'allarme, il vincolo. È la parte che
                distingue una correzione da una lezione imparata.
```

```
# UN ESEMPIO COMPILATO
#
# SINTOMO   "Il carrello si svuota da solo" — segnalato da 3 utenti,
#           esempio: ordine ORD-2026-0412, 14:32 del 18/08
# IMPATTO   ~2% delle sessioni negli ultimi 3 giorni, dal rilascio
#           v2.4.0. Nessuna perdita di dati, ma abbandono del carrello.
# RIPRODUZIONE  1. aggiungi un articolo  2. lascia la scheda aperta
#           15 minuti  3. aggiungi un secondo articolo → il primo
#           sparisce.  Riproduce 10 volte su 10.
# INDAGINE
#   ipotesi 1: la sessione scade → SCARTATA: l'utente resta autenticato
#   ipotesi 2: il carrello è in localStorage e viene sovrascritto →
#     SCARTATA: è sul server
#   ipotesi 3: la seconda richiesta invia un carrello VECCHIO,
#     letto quando la pagina è stata caricata → CONFERMATA dal
#     corpo della richiesta nel pannello Network
# CAUSA     il client invia l'INTERO carrello a ogni aggiunta,
#           partendo dalla copia in memoria. Dopo 15 minuti quella
#           copia è vecchia, e l'invio sovrascrive lo stato del
#           server. È un lost update, con il client come autore.
# CORREZIONE
#   immediata: l'endpoint accetta un'operazione ("aggiungi questo
#     articolo") invece dello stato completo
#   strutturale: ETag + If-Match sul carrello, così un invio basato
#     su una versione vecchia riceve 412 invece di sovrascrivere
# PREVENZIONE
#   · un test che riproduce i tre passi
#   · una regola: gli endpoint che accettano uno stato completo
#     richiedono If-Match (tutorial_11 §B5)
#   · un allarme sul tasso di 412: se sale, ci sono client con dati
#     vecchi
```

```
# LA VERIFICA DELL'INDAGINE — le domande a cui deve rispondere
# 1. La causa spiega TUTTI i sintomi, compresi i dettagli strani?
# 2. Il test riproduce il bug PRIMA della correzione?
# 3. La correzione strutturale impedisce l'intera CLASSE di
#    problemi, non solo questo caso?
# 4. Se si ripresentasse domani in un'altra forma, ce ne
#    accorgeremmo? (allarme, log, vincolo)
# 5. Le ipotesi scartate sono scritte, con il motivo?
# 6. Qualcun altro potrebbe rifare l'indagine leggendo il documento?
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Debug in produzione senza fermare nulla

```
IN PRODUZIONE NON SI METTONO BREAKPOINT: fermare un processo che
serve richieste è un secondo incidente. Gli strumenti che si usano
invece, in ordine di invasività crescente:

1. LOG A LIVELLO DEBUG, ACCESI SELETTIVAMENTE
   Per un singolo utente, o per una finestra di dieci minuti, non
   per tutti: `LOG_LEVEL=debug` globale su un servizio trafficato
   produce gigabyte e rallenta.

2. IL PROFILO DELLA CPU A COMANDO
   Un endpoint protetto che avvia e ferma `Profiler` via
   `node:inspector` (tutorial_10 §D1). Costa poco e dice dove va il
   tempo.

3. LO HEAP SNAPSHOT
   `--heapsnapshot-signal=SIGUSR2`, poi `kill -USR2`. ⚠ Blocca il
   processo per qualche secondo e produce un file grande: si fa su
   un'istanza tolta dal bilanciatore.

4. UN'ISTANZA "CANARINO"
   Una copia con il logging verboso, che riceve l'1% del traffico.
   È il modo migliore di osservare un problema raro senza pagarne il
   costo su tutti.
```

```typescript
// Il logging condizionale per utente: si accende dal database o da
// una variabile, senza rilasciare
export function registroPer(idUtente: string) {
  const verboso = utentiSottoOsservazione.has(idUtente)
  return registro.child({ idUtente }, { level: verboso ? 'debug' : 'info' })
}
```

```
⚠ E LA REGOLA CHE VIENE PRIMA DI TUTTE: prima si MITIGA, poi si
  indaga. Se il servizio è degradato, tornare all'ultima versione
  buona non è una sconfitta: è ripristinare il servizio. L'indagine
  si fa dopo, con calma, sui log e sulle tracce che si sono già
  raccolti.
```

---

## D2. Quando il problema è una dipendenza

```
LA PROCEDURA, IN QUATTRO PASSI
  1. CONFERMARE che sia la dipendenza: un esempio minimo che usa
     SOLO quella libreria e riproduce il comportamento. Nove volte
     su dieci il problema è nel proprio uso, non nella libreria.
  2. CERCARE: le issue aperte E CHIUSE del repository, il changelog
     fra la tua versione e l'ultima. Spesso è già noto e risolto.
  3. LEGGERE IL CODICE della libreria. È in node_modules, e nessuno
     lo apre mai: la risposta è quasi sempre lì, in venti righe.
  4. SEGNALARE con l'esempio minimo. Una issue con una riproduzione
     viene corretta; una senza resta aperta per mesi.
```

```
LE VIE D'USCITA MENTRE SI ASPETTA
  · FISSARE la versione precedente che funzionava
  · `pnpm.overrides` per forzare una versione in tutto l'albero,
    anche nelle dipendenze transitive
  · una PATCH LOCALE: `pnpm patch <pacchetto>` produce un file
    applicato a ogni installazione. ⚠ Va rimossa quando la
    correzione arriva a monte, e va documentata: una patch
    dimenticata blocca gli aggiornamenti per anni.
  · avvolgere la libreria dietro una propria interfaccia, così
    sostituirla non tocca il resto del codice
```

```powershell
# Chi ha portato dentro questo pacchetto, e in quale versione
pnpm why lodash
pnpm ls --depth=10 lodash

# Il diff fra due versioni, senza scaricare nulla
# (utile per capire cosa è cambiato quando un aggiornamento rompe)
pnpm dlx npm-diff lodash@4.17.20 lodash@4.17.21
```

---

## D3. Il caso peggiore: non si riproduce

```
QUANDO NON SI RIPRODUCE, SI CAMBIA STRATEGIA: invece di cercare la
causa, si costruisce la capacità di OSSERVARLA quando succede.

  1. AUMENTARE L'OSSERVABILITÀ nel punto sospetto. Log con tutti i
     valori in gioco, e lasciarli girare finché non si ripresenta.
  2. RACCOGLIERE IL CONTESTO DI OGNI OCCORRENZA: user agent, versione
     dell'applicazione, ora, utente, dispositivo, dimensione dello
     schermo, funzionalità disponibili. Il pattern emerge dai numeri.
  3. CERCARE LA CORRELAZIONE, non la causa: succede solo su Safari?
     Solo sotto una certa versione? Solo a chi ha un carrello con più
     di dieci articoli? Solo il lunedì mattina, quando parte il job
     notturno?
  4. RIPRODURRE LE CONDIZIONI ESTREME: rete a 20 kB/s, CPU rallentata
     sei volte, cento richieste in parallelo, un dataset di
     produzione.
  5. ACCETTARE UNA MITIGAZIONE se il costo dell'indagine supera il
     danno: un ritentativo automatico, un messaggio chiaro, un
     controllo di coerenza. ⚠ Ma va SCRITTO che è una mitigazione e
     non una correzione, altrimenti fra sei mesi nessuno lo sa più.
```

```typescript
// Registrare il contesto completo alla prima occorrenza: costa
// poco, e la volta dopo l'indagine parte da dati invece che da zero
export function registraAnomalia(nome: string, dettagli: Record<string, unknown>) {
  registro.warn(
    {
      anomalia: nome,
      versione: import.meta.env['VITE_VERSIONE'],
      userAgent: navigator.userAgent,
      schermo: `${screen.width}x${screen.height}`,
      connessione: (navigator as { connection?: { effectiveType?: string } }).connection
        ?.effectiveType,
      memoriaDispositivo: (navigator as { deviceMemory?: number }).deviceMemory,
      ...dettagli,
    },
    'anomalia rilevata',
  )
}
```

---

## D4. Il post-mortem senza colpe

```
UN POST-MORTEM SERVE A CAMBIARE IL SISTEMA, NON A TROVARE UN
RESPONSABILE. Il momento in cui diventa inutile è quello in cui
qualcuno comincia a difendersi: da lì in poi si smette di raccontare
cosa è successo davvero, e senza quello non si impara niente.

LA STRUTTURA
  · COSA È SUCCESSO   una cronologia con gli orari
  · IMPATTO           utenti coinvolti, durata, danno misurabile
  · CAUSA RADICE      la catena completa, non "un errore umano"
  · COSA HA FUNZIONATO  l'allarme è scattato, il rollback è stato
    rapido: va detto, perché va conservato
  · COSA NON HA FUNZIONATO  cosa ha reso possibile l'errore, cosa ha
    ritardato la scoperta, cosa ha reso lenta la correzione
  · AZIONI            con un proprietario e una data, altrimenti non
    esistono
```

```
LA REGOLA DEI "CINQUE PERCHÉ", E DOVE SI FERMA
  "Il sito è andato giù."
   perché? Il database ha esaurito le connessioni.
   perché? Un rilascio ha decuplicato il pool per istanza.
   perché? Nessuno sapeva che il pool è totale, non per processo.
   perché? Non era documentato e non c'era un controllo.
   perché? Non esiste una revisione delle modifiche infrastrutturali.
  ➜ L'azione è "un controllo automatico sul numero totale di
    connessioni", non "fare più attenzione".

⚠ SE LA CATENA DEI PERCHÉ FINISCE SU UNA PERSONA, NON È FINITA. "Ha
  sbagliato a configurare" apre la domanda successiva: perché il
  sistema ha permesso quella configurazione? Le persone sbagliano
  sempre; i sistemi possono rendere l'errore impossibile, o
  reversibile, o almeno visibile.
```

---

## D5. Rendere il sistema diagnosticabile

```
LA DIAGNOSTICABILITÀ SI PROGETTA PRIMA. Un sistema che non si può
osservare produce indagini che durano giorni; uno progettato bene le
riduce a minuti — e la differenza si costruisce quando si scrive il
codice, non quando l'incidente è in corso.

LE SETTE COSE CHE FANNO LA DIFFERENZA
  1. IDENTIFICATIVO DI RICHIESTA propagato fino al client e mostrato
     negli errori. Il singolo intervento con il rapporto
     costo/beneficio migliore che esista.
  2. LOG STRUTTURATI con contesto e livelli usati sul serio.
  3. ERRORI TIPIZZATI con un codice stabile: `SALDO_INSUFFICIENTE`
     si cerca nei log, "Operazione non riuscita" no.
  4. `/salute` CHE DICE QUALCOSA: non solo "ok", ma lo stato delle
     dipendenze e la versione in esecuzione.
  5. METRICHE per endpoint e per versione, con annotazione dei
     rilasci sui grafici.
  6. VINCOLI NEL DATABASE: un dato incoerente che non può esistere
     è un'indagine che non si farà mai.
  7. AMBIENTI RIPRODUCIBILI: se non puoi ricreare la produzione in
     locale, ogni indagine parte in salita.
```

```typescript
// L'endpoint di salute che serve davvero durante un incidente
app.get('/salute/dettaglio', richiedeRuolo('operazioni'), async (_richiesta, risposta) => {
  const controlli = await Promise.allSettled([
    db.$queryRaw`SELECT 1`,
    redis.ping(),
    fetch(process.env['URL_SERVIZIO_PAGAMENTI'] + '/salute', {
      signal: AbortSignal.timeout(2000),
    }),
  ])

  const [database, cache, pagamenti] = controlli.map((c) => c.status === 'fulfilled')

  risposta.status(database ? 200 : 503).json({
    versione: process.env['VERSIONE_APP'],
    avviatoIl: new Date(Date.now() - process.uptime() * 1000).toISOString(),
    dipendenze: { database, cache, pagamenti },
    memoriaMb: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
    connessioniAttive: await contaConnessioniAttive(),
  })
})
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
TROUBLESHOOTING — Mappa dei concetti

IL METODO
├── 1. riprodurre  2. restringere  3. ipotesi precisa
├── 4. verificare con una MISURA  5. spiegare TUTTI i sintomi
├── una spiegazione che lascia fuori un dettaglio è incompleta
└── mai cambiare più cose insieme; mai correggere il sintomo

LEGGERE UN ERRORE
├── dalla prima riga del PROPRIO codice, non dalla cima
├── la domanda è "perché è undefined", non "come lo evito"
├── caricamento, errore, vuoto e successo sono quattro stati diversi
└── "Script error." = manca crossorigin; "Failed to fetch" = molte cose

DEVTOOLS
├── breakpoint condizionali e logpoint invece di console.log
├── "Pause on caught exceptions" trova gli errori ingoiati
├── Network: Initiator dice CHI, Timing dice DOVE si perde tempo
└── Application: cookie, storage, cache del service worker

ISOLARE
├── ogni domanda deve DIMEZZARE lo spazio del problema
├── curl separa frontend e backend in dieci secondi
├── git bisect run trova il commit in log2(n) prove
└── e costringe a scrivere prima il test che riproduce

"FUNZIONA IN LOCALE" — le sei cause
├── versioni · variabili d'ambiente · dati · maiuscole nei percorsi
├── build ≠ sviluppo · concorrenza e latenza
└── build && preview prima di ogni push

OSSERVABILITÀ
├── log strutturati con contesto, livelli veri, redazione configurata
├── identificativo di richiesta propagato FINO AL CLIENT
├── tracce: il diagramma a cascata mostra dove sono andati i secondi
└── un log senza contesto è un console.log più elegante

MEMORIA E INTERMITTENZA
├── perdita = il MINIMO che sale dopo ogni raccolta
├── due snapshot a confronto; cercare i "Detached HTMLElement"
├── AbortController risolve tre cause su quattro
├── "a volte" = una condizione non ancora identificata
└── sei famiglie: concorrenza, tempo, cache, ordine, dati, ambiente

PRODUZIONE
├── prima si MITIGA, poi si indaga
├── mai breakpoint; log debug selettivi, profilo a comando, canarino
├── post-mortem senza colpe: se la catena finisce su una persona,
│     non è finita
└── la diagnosticabilità si progetta prima, non durante l'incidente
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Segui i cinque passi, e non salti il primo
- [ ] Sai perché cambiare più cose insieme rende inutile l'esperimento
- [ ] Leggi uno stack trace partendo dal tuo codice
- [ ] Distingui i quattro stati di un caricamento invece di usare `?.`
- [ ] Sai cosa significano "Script error." e "Failed to fetch"
- [ ] Usi breakpoint condizionali e logpoint
- [ ] Riconosci gli otto errori frontend ricorrenti e la loro causa
- [ ] Sai collegare l'inspector a un processo Node, e perché non si espone la porta
- [ ] Gestisci `unhandledRejection` e `uncaughtException` terminando

**Parte B — Comprensione**

- [ ] Formuli domande che dimezzano lo spazio del problema
- [ ] Usi `git bisect run` con un test che riproduce
- [ ] Leggi il pannello Network nell'ordine giusto
- [ ] Sai perché un 500 può presentarsi come errore CORS
- [ ] Riproduci con curl per separare browser e server
- [ ] Conosci le sei cause di "funziona in locale"
- [ ] Scrivi log strutturati con contesto e livelli usati correttamente
- [ ] Propaghi l'identificativo di richiesta fra i servizi e fino al client
- [ ] Distingui una crescita normale della memoria da una perdita
- [ ] Trovi una perdita con due snapshot e riconosci i nodi staccati
- [ ] Riconosci le sei famiglie di bug intermittenti
- [ ] Sai risolvere una corsa fra due richieste
- [ ] Sai diagnosticare su un dispositivo reale, e perché il simulatore non basta

**Parte C — Pratica**

- [ ] Hai trovato la causa della pagina bianca leggendo console e rete
- [ ] Hai spiegato anche il "perché in locale funzionava"
- [ ] Hai notato che i numeri non tornavano e cercato la seconda causa
- [ ] Hai riprodotto un bug intermittente partendo dai dati
- [ ] Hai reso lo stato incoerente impossibile, non solo improbabile

**Parte D — Esperto**

- [ ] Sai indagare in produzione senza fermare il servizio
- [ ] Mitighi prima di indagare
- [ ] Confermi che il problema sia in una dipendenza con un esempio minimo
- [ ] Conosci le vie d'uscita, e documenti le patch locali
- [ ] Sai cosa fare quando un bug non si riproduce
- [ ] Conduci un post-mortem che non finisce su una persona
- [ ] Sai elencare le sette cose che rendono un sistema diagnosticabile

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Correggere senza aver riprodotto | Non saprai se hai corretto qualcosa | Riprodurre a comando, prima |
| Cambiare più cose insieme | Se funziona non sai quale, se no hai aggiunto variabili | Una modifica per volta |
| "Proviamo a riavviare" | Nasconde la causa: torna, e la seconda volta è peggio | Osservare prima di intervenire |
| `try/catch` che ingoia l'errore | Il guasto si sposta lontano dalla causa | Registrare e propagare |
| `?.` per far sparire un errore | Nasconde il perché il valore è assente | Distinguere i quattro stati |
| Leggere lo stack dalla cima | Le righe della libreria dicono come, non perché | Partire dal proprio codice |
| `console.log('qui')` | Nessun livello, contesto o ricercabilità | Log strutturato con contesto |
| Tutto a livello `error` | Gli allarmi diventano rumore e nessuno li guarda | Livelli usati sul serio |
| `LOG_LEVEL=debug` globale in produzione | Gigabyte di log e servizio rallentato | Debug selettivo per utente o finestra |
| Breakpoint in produzione | Ferma un processo che serve richieste | Log, profilo a comando, canarino |
| Indagare prima di mitigare | Il servizio resta degradato mentre si studia | Rollback, poi indagine sui dati raccolti |
| Nessun identificativo di richiesta | "Intorno alle 14:30 di ieri" fra centomila righe | Propagarlo fino al client |
| Fermarsi alla prima causa | I numeri non tornano: metà problema resta | La spiegazione deve coprire tutto |
| "Non si riproduce" come conclusione | La condizione esiste, non è stata trovata | Aumentare l'osservabilità e correlare |
| Guardare la media invece dei percentili | Un utente su cento aspetta quattro secondi, invisibile | p95 e p99 |
| Patch locale non documentata | Blocca gli aggiornamenti per anni | Annotarla, e rimuoverla quando arriva a monte |
| Post-mortem che cerca un colpevole | Le persone smettono di raccontare cosa è successo | Cambiare il sistema, non le persone |
| Azioni senza proprietario né data | Non esistono | Nome e scadenza per ognuna |

---

## Troubleshooting rapido

**Pagina bianca, console vuota**
- Causa: il bundle non è stato caricato (404 servito come 200), o un errore ha smontato tutto
- Fix: pannello Network prima della console; un Error Boundary che mostri qualcosa

**`Unexpected token '<'` in un file JavaScript**
- Causa: il server ha risposto HTML — il file non esiste e il fallback della SPA ha restituito index.html
- Fix: escludere `/assets/*` dal fallback; `no-cache` su index.html

**L'interfaccia non si aggiorna dopo una modifica**
- Causa: stato mutato invece di sostituito, o chiave di lista instabile
- Fix: creare un nuovo riferimento; `key` dall'identificativo del dato

**Errore CORS che non si spiega**
- Causa: la richiesta ha prodotto un 500 prima del middleware CORS, oppure il preflight fallisce
- Fix: guardare la OPTIONS e il corpo della risposta; riprovare con curl

**Funziona con curl e non dal browser**
- Causa: CORS, cookie, o un'estensione che blocca
- Fix: confrontare le intestazioni delle due richieste; provare in incognito

**Il server smette di rispondere senza errori**
- Causa: qualcosa blocca l'event loop
- Fix: `monitorEventLoopDelay` per confermarlo, `--cpu-prof` per la funzione

**La memoria cresce e non scende**
- Causa: listener, timer o osservatori non ripuliti; o una cache senza limite
- Fix: due snapshot a confronto; cercare i "Detached HTMLElement"

**Un test passa da solo e fallisce insieme agli altri**
- Causa: stato condiviso fra i test
- Fix: ripristinare i mock, isolare i dati (tutorial_15 §B6)

**L'errore compare solo per alcuni utenti**
- Causa: dati, dispositivo, versione o rete
- Fix: registrare il contesto completo alla prima occorrenza e cercare la correlazione

**Dopo un rilascio gli utenti vedono errori di caricamento dei moduli**
- Causa: la pagina aperta prima del deploy chiede un pezzo che non esiste più
- Fix: conservare gli artefatti precedenti; intercettare l'errore e proporre il ricaricamento

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_17_performance_web.md` | Quando il sintomo è "lento": profilo, non intuizione |
| `tutorial_12_database_web.md` | Query lente, lock, pool saturo, lost update |
| `tutorial_15_testing_web.md` | Il test che riproduce, scritto prima della correzione |
| `tutorial_16_build_tools_deploy.md` | Rollback rapido e osservabilità del rilascio |
| `tutorial_14_sicurezza_web.md` | La risposta all'incidente quando la causa è un attacco |
| `tutorial_10_nodejs.md` | Event loop bloccato, profiling e heap snapshot sul server |

---

## Risorse di riferimento

**Documentazione:** [Chrome DevTools](https://developer.chrome.com/docs/devtools) — in particolare *Debug JavaScript* e *Network reference* · [Node.js — Debugging](https://nodejs.org/en/learn/getting-started/debugging) e [Diagnostics](https://nodejs.org/en/learn/diagnostics/) · [MDN — Debugging](https://developer.mozilla.org/docs/Learn/Tools_and_testing)

**Approfondimenti:** [Debugging: The 9 Indispensable Rules](https://debuggingrules.com/), le regole di David Agans — il testo più utile mai scritto sul metodo · [Google SRE Book](https://sre.google/sre-book/effective-troubleshooting/), il capitolo sul troubleshooting efficace e quello sui post-mortem senza colpe · [Julia Evans — debugging zines](https://wizardzines.com/)

**Strumenti:** [Sentry](https://sentry.io/) per la raccolta degli errori · [OpenTelemetry](https://opentelemetry.io/docs/languages/js/) per le tracce · [pino](https://getpino.io/) · [Clinic.js](https://clinicjs.org/) per la diagnostica di Node · [git bisect](https://git-scm.com/docs/git-bisect)

---

> **Fine del Tutorial 19 — Troubleshooting**
>
> Prossimo tutorial: `tutorial_21_rsc_server_driven_ui.md`
