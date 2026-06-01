---
corso: "Sviluppo Web Full-Stack"
fase: "7 — Architetture Avanzate"
modulo: 23
titolo: "WebSocket Protocol e Sicurezza"
versione: "RFC 6455 / WSS / Socket.IO 4.x"
livello: "Avanzato"
prerequisiti: ["10-nodejs", "14-sicurezza-web"]
obiettivi:
  - "Descrivere l'handshake HTTP Upgrade e il framing binario WebSocket"
  - "Implementare autenticazione on-connect e validazione per-messaggio"
  - "Configurare WSS, origin check e rate limiting per connessione"
  - "Scalare WebSocket con Redis pub/sub e sticky sessions"
  - "Progettare architetture real-time sicure (chat, dashboard, collaboration)"
tag: [websocket, real-time, wss, socket-io, security, scaling, redis-pubsub]
---

# WebSocket Protocol e Sicurezza

> **Modulo 23** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Descrivere l'handshake HTTP Upgrade e il framing binario WebSocket
> 2. Implementare autenticazione on-connect e validazione per-messaggio
> 3. Configurare WSS, origin check e rate limiting per connessione
> 4. Scalare WebSocket con Redis pub/sub e sticky sessions
> 5. Progettare architetture real-time sicure (chat, dashboard, collaboration)
>
> **Prerequisiti:** [Node.js](10-nodejs.md), [Sicurezza Web](14-sicurezza-web.md)
> **Tempo stimato:** 5-7 ore · **Livello:** Avanzato

## Idee guida

1. **WSS (TLS) obbligatorio in produzione.** Plain WS = MITM triviale.
2. **Origin check sull'handshake.** Il browser non applica CORS ai WebSocket!
3. **Auth on connect, validazione per messaggio.** Token scaduto? Disconnect.
4. **Rate limit per connessione.** Una singola connessione può inondare il server.
5. **Limite dimensione messaggi + max connessioni per IP.** Prevenzione DoS.

---

## Panoramica

Il protocollo WebSocket (RFC 6455) rappresenta un cambio di paradigma nella comunicazione web. A differenza del modello request-response di HTTP, WebSocket stabilisce un canale bidirezionale full-duplex su una singola connessione TCP persistente. Questo consente al server di inviare dati al client senza che quest'ultimo debba effettuare polling, eliminando la latenza e il sovraccarico di header HTTP ripetuti.

Le applicazioni real-time moderne — chat, dashboard live, editing collaborativo, gaming multiplayer, notifiche push, streaming di dati finanziari — dipendono tutte da questa capacità. Tuttavia, la natura persistente della connessione WebSocket introduce superfici di attacco specifiche che non esistono nel modello HTTP tradizionale. Una connessione WebSocket aperta è un canale bidirezionale permanente: se compromessa, l'attaccante ottiene accesso continuo senza necessità di autenticazione ripetuta.

Questo modulo copre il protocollo WebSocket nella sua interezza — dall'handshake HTTP ai frame binari — e poi approfondisce ogni aspetto della sicurezza, dello scaling e delle architetture real-time.

---

## Il protocollo WebSocket

### Handshake HTTP Upgrade

La connessione WebSocket inizia come una normale richiesta HTTP che viene "upgraded" al protocollo WebSocket. Questo design consente ai WebSocket di attraversare proxy e firewall che comprendono HTTP.

```
# Richiesta del client (HTTP Upgrade)
GET /ws/chat HTTP/1.1
Host: api.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Sec-WebSocket-Protocol: chat, superchat
Origin: https://example.com
```

```
# Risposta del server (101 Switching Protocols)
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
Sec-WebSocket-Protocol: chat
```

Il valore di `Sec-WebSocket-Accept` è calcolato dal server concatenando il valore di `Sec-WebSocket-Key` con il GUID fisso `258EAFA5-E914-47DA-95CA-C5AB0DC85B11`, calcolando lo SHA-1 del risultato e codificandolo in Base64. Questo meccanismo non fornisce sicurezza: serve unicamente a confermare che il server comprende il protocollo WebSocket e a prevenire che risposte HTTP cache provochino upgrade accidentali.

```javascript
// Calcolo server-side di Sec-WebSocket-Accept
const crypto = require('node:crypto');

function computeAcceptKey(clientKey) {
  const GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';
  return crypto
    .createHash('sha1')
    .update(clientKey + GUID)
    .digest('base64');
}

// Esempio:
// computeAcceptKey('dGhlIHNhbXBsZSBub25jZQ==')
// => 's3pPLMBiTxaQ9kYGzzhZRbK+xOo='
```

### Frame WebSocket

Dopo l'handshake, la comunicazione avviene tramite **frame** binari. Ogni frame ha una struttura precisa definita nella RFC 6455:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |           (16/64)             |
|N|V|V|V|       |S|             |  (if payload len == 126/127)  |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
|     Extended payload length continued, if payload len == 127  |
+-------------------------------+-------------------------------+
|                               | Masking-key, if MASK set to 1 |
+-------------------------------+-------------------------------+
|          Masking-key (continued)       |   Payload Data       |
+-------------------------------- - - - - - - - - - - - - - - - +
|                     Payload Data continued ...                |
+---------------------------------------------------------------+
```

**FIN bit (1 bit):** indica se questo è il frame finale di un messaggio. Un messaggio può essere frammentato in più frame.

**RSV1, RSV2, RSV3 (1 bit ciascuno):** riservati per estensioni. Utilizzati ad esempio da `permessage-deflate` per la compressione.

**Opcode (4 bit):** tipo di frame.

**MASK (1 bit):** i frame inviati dal client al server DEVONO essere mascherati. I frame dal server al client NON devono essere mascherati.

**Masking key (32 bit):** chiave XOR usata per mascherare il payload dal client. Previene attacchi di cache poisoning su proxy intermedi.

### Opcode — tipi di frame

| Opcode | Tipo | Descrizione |
|--------|------|-------------|
| `0x0` | Continuation | Frame di continuazione di un messaggio frammentato |
| `0x1` | Text | Dati testuali (UTF-8) |
| `0x2` | Binary | Dati binari |
| `0x3-0x7` | Riservati | Per future estensioni non-control |
| `0x8` | Close | Richiesta di chiusura connessione |
| `0x9` | Ping | Heartbeat — il ricevente DEVE rispondere con Pong |
| `0xA` | Pong | Risposta a Ping |
| `0xB-0xF` | Riservati | Per future estensioni control |

### Close code — codici di chiusura

I close code seguono una semantica precisa. Conoscerli è fondamentale per il debugging:

| Codice | Nome | Significato |
|--------|------|-------------|
| `1000` | Normal Closure | Chiusura ordinata, scopo raggiunto |
| `1001` | Going Away | Server in shutdown o client che naviga altrove |
| `1002` | Protocol Error | Errore nel protocollo WebSocket |
| `1003` | Unsupported Data | Tipo di dato ricevuto non supportato |
| `1005` | No Status Received | Riservato — nessun codice presente nel frame di chiusura |
| `1006` | Abnormal Closure | Riservato — connessione chiusa senza frame di chiusura |
| `1007` | Invalid Payload Data | Dati non conformi al tipo (es. testo non UTF-8) |
| `1008` | Policy Violation | Violazione policy — generico (usato per auth failure) |
| `1009` | Message Too Big | Messaggio supera il limite di dimensione |
| `1010` | Mandatory Extension | Client richiede estensione che il server non supporta |
| `1011` | Internal Error | Errore interno del server |
| `1012` | Service Restart | Server in riavvio — il client dovrebbe riconnettersi |
| `1013` | Try Again Later | Server sovraccarico — il client dovrebbe riprovare più tardi |
| `1014` | Bad Gateway | Gateway ha ricevuto risposta invalida dall'upstream |
| `1015` | TLS Handshake Failure | Riservato — fallimento handshake TLS |
| `4000-4999` | Private Use | Range riservato per codici applicativi custom |

```javascript
// Utilizzo dei close code nel server
function handleProtocolViolation(ws, reason) {
  ws.close(1002, `Protocol error: ${reason}`);
}

function handleAuthFailure(ws) {
  ws.close(1008, 'Authentication failed');
}

function handleOverload(ws) {
  ws.close(1013, 'Server overloaded, try again later');
}

// Close code custom applicativi (range 4000-4999)
const APP_CLOSE_CODES = {
  TOKEN_EXPIRED:      4001,
  RATE_LIMITED:        4002,
  INVALID_CHANNEL:    4003,
  DUPLICATE_SESSION:  4004,
  MAINTENANCE_MODE:   4005,
};
```

### Ping / Pong — Heartbeat

Il meccanismo ping/pong è fondamentale per rilevare connessioni "morte" (half-open) dove una delle parti è caduta senza inviare un frame di chiusura.

```javascript
// Server-side heartbeat con la libreria ws
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

const HEARTBEAT_INTERVAL = 30_000; // 30 secondi
const PONG_TIMEOUT = 10_000;       // 10 secondi per rispondere

wss.on('connection', (ws) => {
  ws.isAlive = true;

  ws.on('pong', () => {
    ws.isAlive = true;
  });

  ws.on('close', () => {
    ws.isAlive = false;
  });
});

const heartbeatInterval = setInterval(() => {
  for (const ws of wss.clients) {
    if (!ws.isAlive) {
      ws.terminate();
      continue;
    }
    ws.isAlive = false;
    ws.ping();
  }
}, HEARTBEAT_INTERVAL);

wss.on('close', () => {
  clearInterval(heartbeatInterval);
});
```

### Frammentazione dei messaggi

Un messaggio può essere suddiviso in più frame. Il primo frame ha l'opcode del tipo di messaggio (text/binary) con FIN=0, i frame intermedi hanno opcode 0x0 (continuation) con FIN=0, e l'ultimo frame ha opcode 0x0 con FIN=1.

```javascript
// Esempio concettuale di frammentazione
// Frame 1: opcode=0x1 (text), FIN=0, payload="Hel"
// Frame 2: opcode=0x0 (continuation), FIN=0, payload="lo "
// Frame 3: opcode=0x0 (continuation), FIN=1, payload="World"
// Messaggio riassemblato: "Hello World"

// La libreria ws gestisce automaticamente la frammentazione.
// Per forzarla manualmente (raro):
const Sender = require('ws/lib/sender');
// Il 99% dei casi non richiede frammentazione manuale.
```

### Estensioni — permessage-deflate

L'estensione `permessage-deflate` comprime i messaggi WebSocket usando zlib, riducendo il traffico di rete. Viene negoziata durante l'handshake.

```javascript
const WebSocket = require('ws');

const wss = new WebSocket.Server({
  port: 8080,
  perMessageDeflate: {
    zlibDeflateOptions: {
      chunkSize: 1024,
      memLevel: 7,
      level: 3,
    },
    zlibInflateOptions: {
      chunkSize: 10 * 1024,
    },
    clientNoContextTakeover: true,
    serverNoContextTakeover: true,
    serverMaxWindowBits: 10,
    concurrencyLimit: 10,
    threshold: 1024, // comprimi solo messaggi > 1KB
  },
});
```

**Attenzione:** `perMessageDeflate` aumenta significativamente l'uso di memoria (fino a 300KB per connessione con le impostazioni di default). Per applicazioni con migliaia di connessioni, valutare attentamente o disabilitare.

---

## WebSocket vs HTTP vs SSE

### Confronto architetturale

| Caratteristica | HTTP | SSE | WebSocket |
|---------------|------|-----|-----------|
| Direzione | Client → Server | Server → Client | Bidirezionale |
| Protocollo | HTTP/1.1, HTTP/2 | HTTP/1.1, HTTP/2 | WS / WSS |
| Connessione | Nuova per ogni request | Persistente (stream) | Persistente (full-duplex) |
| Overhead per messaggio | Header completi (~800 byte) | ~0 (stream aperto) | 2-14 byte (frame header) |
| Riconnessione automatica | N/A | Sì (built-in) | No (manuale) |
| Supporto proxy/CDN | Eccellente | Buono | Variabile |
| Scalabilità orizzontale | Semplice (stateless) | Media | Complessa (stateful) |
| Tipo di dati | Qualsiasi | Solo testo (UTF-8) | Testo e binario |
| Browser support | Universale | Universale (no IE) | Universale |
| HTTP/2 multiplexing | Sì | Sì | No (connessione dedicata) |

### Quando usare WebSocket

**Scegli WebSocket quando:**
- Comunicazione bidirezionale in tempo reale (chat, gaming)
- Latenza sotto i 50ms è critica
- Alto volume di messaggi in entrambe le direzioni
- Dati binari (audio/video streaming, file transfer)
- Protocolli custom sopra il trasporto (es. multiplayer game protocol)

**Scegli SSE quando:**
- Solo push dal server al client (notifiche, feed live, dashboard)
- Riconnessione automatica è importante
- Compatibilità con proxy/CDN è prioritaria
- Il client invia dati raramente (usa HTTP POST separato)
- HTTP/2 è disponibile (multiplexing elimina il limite di 6 connessioni)

**Resta su HTTP quando:**
- Operazioni CRUD standard
- Polling a intervalli > 30 secondi è accettabile
- La complessità di connessioni persistenti non è giustificata
- Il sistema deve essere completamente stateless

### Server-Sent Events (SSE) — alternativa leggera

```javascript
// Server SSE con Node.js (senza dipendenze)
const http = require('node:http');

const server = http.createServer((req, res) => {
  if (req.url === '/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no', // disabilita buffering Nginx
    });

    // Invio commento keepalive ogni 15s per evitare timeout proxy
    const keepalive = setInterval(() => {
      res.write(':keepalive\n\n');
    }, 15_000);

    // Evento con ID per riconnessione automatica
    let eventId = 0;
    const dataInterval = setInterval(() => {
      eventId++;
      res.write(`id: ${eventId}\n`);
      res.write(`event: price-update\n`);
      res.write(`data: ${JSON.stringify({ symbol: 'BTC', price: 42000 + Math.random() * 1000 })}\n\n`);
    }, 1000);

    req.on('close', () => {
      clearInterval(keepalive);
      clearInterval(dataInterval);
    });

    return;
  }

  res.writeHead(404);
  res.end();
});

server.listen(3000);
```

```javascript
// Client SSE — riconnessione automatica built-in
const source = new EventSource('/events');

source.addEventListener('price-update', (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.symbol}: $${data.price.toFixed(2)}`);
});

// EventSource riconnette automaticamente con Last-Event-ID header
source.onerror = (event) => {
  if (source.readyState === EventSource.CONNECTING) {
    console.log('Riconnessione in corso...');
  }
};
```

---

## Implementazione WebSocket

### API nativa del browser

```javascript
// Connessione WebSocket lato client
const ws = new WebSocket('wss://api.example.com/ws');

// Lifecycle events
ws.addEventListener('open', (event) => {
  console.log('Connessione stabilita');
  ws.send(JSON.stringify({ type: 'subscribe', channel: 'prices' }));
});

ws.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  handleMessage(data);
});

ws.addEventListener('close', (event) => {
  console.log(`Connessione chiusa: code=${event.code}, reason=${event.reason}, clean=${event.wasClean}`);
});

ws.addEventListener('error', (event) => {
  console.error('Errore WebSocket:', event);
});

// Proprietà
console.log(ws.readyState);    // 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED
console.log(ws.bufferedAmount); // byte in coda da inviare
console.log(ws.protocol);      // sub-protocollo negoziato
console.log(ws.extensions);    // estensioni negoziate
```

### Libreria `ws` — Node.js

La libreria `ws` è l'implementazione WebSocket più diffusa per Node.js. Pura JavaScript (con binding C++ opzionali per performance), senza dipendenze, aderente alla RFC 6455.

```javascript
// Server WebSocket con ws
const { WebSocketServer } = require('ws');
const http = require('node:http');

// Creare il server HTTP separatamente per maggior controllo
const server = http.createServer();

const wss = new WebSocketServer({
  server,
  path: '/ws',
  maxPayload: 1024 * 1024, // 1MB limite dimensione messaggio
  clientTracking: true,
  perMessageDeflate: false, // disabilitare in produzione se non necessario
});

// Mappa connessioni -> metadati
const clients = new Map();

wss.on('connection', (ws, req) => {
  const clientIp = req.headers['x-forwarded-for']?.split(',')[0]?.trim()
    || req.socket.remoteAddress;

  const clientMeta = {
    ip: clientIp,
    connectedAt: Date.now(),
    messageCount: 0,
    userId: null,
    channels: new Set(),
  };
  clients.set(ws, clientMeta);

  console.log(`Nuova connessione da ${clientIp}. Totale: ${clients.size}`);

  ws.on('message', (data, isBinary) => {
    clientMeta.messageCount++;

    if (isBinary) {
      handleBinaryMessage(ws, data);
      return;
    }

    try {
      const message = JSON.parse(data.toString());
      handleTextMessage(ws, message, clientMeta);
    } catch {
      ws.close(1007, 'Invalid JSON');
    }
  });

  ws.on('close', (code, reason) => {
    console.log(`Disconnessione: code=${code}, reason=${reason.toString()}`);
    clients.delete(ws);
  });

  ws.on('error', (error) => {
    console.error(`Errore WebSocket: ${error.message}`);
    clients.delete(ws);
  });
});

function handleTextMessage(ws, message, meta) {
  switch (message.type) {
    case 'subscribe':
      meta.channels.add(message.channel);
      break;
    case 'unsubscribe':
      meta.channels.delete(message.channel);
      break;
    case 'broadcast':
      broadcastToChannel(message.channel, message.payload, ws);
      break;
    default:
      ws.send(JSON.stringify({ error: 'Unknown message type' }));
  }
}

function broadcastToChannel(channel, payload, sender) {
  for (const [ws, meta] of clients) {
    if (ws !== sender && meta.channels.has(channel) && ws.readyState === 1) {
      ws.send(JSON.stringify({ channel, payload }));
    }
  }
}

server.listen(8080);
```

### Socket.IO

Socket.IO non è un'implementazione WebSocket pura. È un protocollo di trasporto real-time che usa WebSocket come trasporto preferito, con fallback automatico su HTTP long-polling. Aggiunge funzionalità come riconnessione automatica, room/namespace, acknowledgment e multiplexing.

```javascript
// Server Socket.IO
const { Server } = require('socket.io');
const http = require('node:http');

const httpServer = http.createServer();

const io = new Server(httpServer, {
  cors: {
    origin: ['https://example.com'],
    methods: ['GET', 'POST'],
    credentials: true,
  },
  pingInterval: 25_000,
  pingTimeout: 20_000,
  maxHttpBufferSize: 1e6, // 1MB
  connectTimeout: 45_000,
  transports: ['websocket', 'polling'],
  allowUpgrades: true,
});

// Middleware di autenticazione
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  try {
    const decoded = verifyJwt(token);
    socket.userId = decoded.sub;
    socket.role = decoded.role;
    next();
  } catch {
    next(new Error('Authentication failed'));
  }
});

// Namespace per area funzionale
const chatNs = io.of('/chat');
const adminNs = io.of('/admin');

chatNs.on('connection', (socket) => {
  console.log(`User ${socket.userId} connesso a /chat`);

  // Join a una room
  socket.on('join-room', (roomId) => {
    if (canAccessRoom(socket.userId, roomId)) {
      socket.join(roomId);
      socket.to(roomId).emit('user-joined', { userId: socket.userId });
    }
  });

  // Messaggio con acknowledgment
  socket.on('send-message', (data, callback) => {
    const message = {
      id: generateId(),
      userId: socket.userId,
      text: sanitize(data.text),
      timestamp: Date.now(),
    };

    // Broadcast alla room
    socket.to(data.roomId).emit('new-message', message);

    // Conferma al mittente
    callback({ status: 'ok', messageId: message.id });
  });

  socket.on('disconnect', (reason) => {
    console.log(`User ${socket.userId} disconnesso: ${reason}`);
  });
});

// Admin namespace con middleware aggiuntivo
adminNs.use((socket, next) => {
  if (socket.role !== 'admin') {
    return next(new Error('Admin access required'));
  }
  next();
});

httpServer.listen(3000);
```

```javascript
// Client Socket.IO
import { io } from 'socket.io-client';

const socket = io('wss://api.example.com/chat', {
  auth: {
    token: getAuthToken(),
  },
  transports: ['websocket'],
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 30_000,
  timeout: 20_000,
});

socket.on('connect', () => {
  console.log(`Connesso con id: ${socket.id}`);
  socket.emit('join-room', 'general');
});

socket.on('new-message', (message) => {
  displayMessage(message);
});

// Emissione con acknowledgment
socket.emit('send-message', { roomId: 'general', text: 'Ciao!' }, (response) => {
  if (response.status === 'ok') {
    console.log(`Messaggio confermato: ${response.messageId}`);
  }
});

socket.on('connect_error', (error) => {
  console.error('Errore connessione:', error.message);
});
```

---

## Scaling WebSocket

Le connessioni WebSocket sono stateful: ogni connessione è legata a un processo server specifico. Questo rende lo scaling orizzontale più complesso rispetto alle API HTTP stateless.

### Il problema fondamentale

Con un singolo server, tutti i client connessi condividono lo stesso processo. Un broadcast raggiunge tutti i client. Quando si aggiungono server dietro un load balancer, i client si distribuiscono tra i server — un messaggio inviato al Server A non raggiunge i client connessi al Server B.

### Sticky sessions

La prima soluzione è garantire che un client si riconnetta sempre allo stesso server. Il load balancer instrada il traffico basandosi su un cookie di sessione o sull'IP del client.

```nginx
# Nginx sticky sessions per WebSocket
upstream websocket_backend {
    ip_hash;  # sticky sessions basate su IP

    server ws1.internal:8080;
    server ws2.internal:8080;
    server ws3.internal:8080;
}

server {
    listen 443 ssl;
    server_name ws.example.com;

    location /ws {
        proxy_pass http://websocket_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout per connessioni inattive
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

**Limiti delle sticky sessions:** se il server assegnato a un client va offline, quel client perde la connessione e deve riconnettersi a un altro server, perdendo eventuale stato in-memory.

### Redis Pub/Sub adapter

La soluzione standard per cross-server broadcasting è un message broker condiviso. Redis Pub/Sub è il più comune.

```javascript
// Socket.IO con Redis adapter
const { Server } = require('socket.io');
const { createAdapter } = require('@socket.io/redis-adapter');
const { createClient } = require('redis');

async function createSocketServer(httpServer) {
  const pubClient = createClient({ url: 'redis://redis.internal:6379' });
  const subClient = pubClient.duplicate();

  await Promise.all([pubClient.connect(), subClient.connect()]);

  const io = new Server(httpServer, {
    cors: { origin: 'https://example.com' },
  });

  io.adapter(createAdapter(pubClient, subClient));

  // Ora un emit su qualsiasi server raggiunge tutti i client
  io.on('connection', (socket) => {
    socket.on('broadcast-message', (data) => {
      // Questo messaggio arriva a TUTTI i client,
      // indipendentemente dal server a cui sono connessi
      io.emit('new-message', data);
    });
  });

  return io;
}
```

```javascript
// Adapter Redis con ws (senza Socket.IO)
const WebSocket = require('ws');
const Redis = require('ioredis');

const redisPub = new Redis('redis://redis.internal:6379');
const redisSub = new Redis('redis://redis.internal:6379');

const wss = new WebSocket.Server({ port: 8080 });
const SERVER_ID = `ws-server-${process.pid}`;

// Sottoscrizione ai canali Redis
redisSub.subscribe('ws:broadcast', 'ws:channel:*');

redisSub.on('message', (redisChannel, message) => {
  const parsed = JSON.parse(message);

  // Non reinviare i propri messaggi
  if (parsed.serverId === SERVER_ID) return;

  // Inoltra ai client locali
  for (const ws of wss.clients) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(parsed.payload));
    }
  }
});

// Quando un client locale invia un messaggio da broadcastare
function broadcastViaRedis(channel, payload) {
  redisPub.publish(channel, JSON.stringify({
    serverId: SERVER_ID,
    payload,
    timestamp: Date.now(),
  }));
}
```

### Pattern di scaling orizzontale

```
                    ┌─────────────────┐
                    │   Load Balancer  │
                    │  (Nginx/HAProxy) │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
        │ WS Server │ │ WS Server │ │ WS Server │
        │     1     │ │     2     │ │     3     │
        └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────┴────────┐
                    │  Redis Pub/Sub  │
                    │   (Cluster)     │
                    └─────────────────┘
```

**Linee guida per il capacity planning:**

| Metrica | Valore orientativo |
|---------|-------------------|
| Connessioni per processo Node.js | 10.000 - 50.000 (dipende dalla complessità dei messaggi) |
| Memoria per connessione (ws) | ~1-2 KB senza compressione, ~300KB con permessage-deflate |
| Memoria per connessione (Socket.IO) | ~5-10 KB |
| File descriptor per connessione | 1 |
| Limite file descriptor Linux | Aumentare `ulimit -n` a 100.000+ |

```bash
# Tuning kernel Linux per WebSocket ad alto traffico
# /etc/sysctl.conf

# Aumentare il range di porte effimere
net.ipv4.ip_local_port_range = 1024 65535

# Aumentare il backlog delle connessioni
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# Riutilizzo TIME_WAIT
net.ipv4.tcp_tw_reuse = 1

# Buffer TCP
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# Keepalive TCP (per rilevare connessioni morte)
net.ipv4.tcp_keepalive_time = 60
net.ipv4.tcp_keepalive_intvl = 10
net.ipv4.tcp_keepalive_probes = 6
```

---

## Autenticazione WebSocket

I WebSocket non supportano header custom durante l'handshake dal browser. L'API `new WebSocket(url, protocols)` accetta solo URL e sub-protocolli. Questo limita le strategie di autenticazione rispetto a HTTP.

### Token nel query parameter

Il metodo più semplice. Il token JWT viene passato come parametro dell'URL.

```javascript
// Client
const ws = new WebSocket(`wss://api.example.com/ws?token=${accessToken}`);
```

```javascript
// Server
const { WebSocketServer } = require('ws');
const jwt = require('jsonwebtoken');

const wss = new WebSocketServer({ noServer: true });

// Gestione upgrade manuale per validare prima di accettare la connessione
const server = require('http').createServer();

server.on('upgrade', (req, socket, head) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const token = url.searchParams.get('token');

  if (!token) {
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
    socket.destroy();
    return;
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET, {
      algorithms: ['HS256'],
      issuer: 'api.example.com',
    });

    wss.handleUpgrade(req, socket, head, (ws) => {
      ws.userId = decoded.sub;
      ws.role = decoded.role;
      ws.tokenExp = decoded.exp;
      wss.emit('connection', ws, req);
    });
  } catch (err) {
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
    socket.destroy();
  }
});

server.listen(8080);
```

**Rischi del token nel query parameter:**
- Il token appare nei log del server (access log)
- Il token appare nella cronologia del browser
- Il token può essere visibile in proxy log intermedi
- Mitigazione: usare token a breve scadenza (60s) dedicati all'handshake

### Token nel primo messaggio

Il client si connette e invia immediatamente un messaggio di autenticazione. Il server accetta la connessione TCP ma non processa altri messaggi finché l'autenticazione non è completata.

```javascript
// Server — autenticazione nel primo messaggio
const AUTH_TIMEOUT = 5000; // 5 secondi per autenticarsi

wss.on('connection', (ws) => {
  ws.isAuthenticated = false;

  // Timer: se non si autentica entro 5s, disconnetti
  const authTimer = setTimeout(() => {
    if (!ws.isAuthenticated) {
      ws.close(1008, 'Authentication timeout');
    }
  }, AUTH_TIMEOUT);

  ws.on('message', (data) => {
    if (!ws.isAuthenticated) {
      try {
        const msg = JSON.parse(data.toString());
        if (msg.type !== 'auth' || !msg.token) {
          ws.close(1008, 'First message must be auth');
          return;
        }

        const decoded = jwt.verify(msg.token, process.env.JWT_SECRET);
        ws.isAuthenticated = true;
        ws.userId = decoded.sub;
        ws.role = decoded.role;
        clearTimeout(authTimer);
        ws.send(JSON.stringify({ type: 'auth_success', userId: decoded.sub }));
      } catch {
        ws.close(1008, 'Invalid token');
      }
      return;
    }

    // Messaggi post-autenticazione
    handleAuthenticatedMessage(ws, data);
  });
});
```

### Autenticazione basata su cookie

Quando il client e il server WebSocket condividono lo stesso dominio, i cookie di sessione vengono inviati automaticamente durante l'handshake.

```javascript
// Server — autenticazione via cookie di sessione
const session = require('express-session');
const express = require('express');

const app = express();
const sessionParser = session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true,
    httpOnly: true,
    sameSite: 'strict',
    maxAge: 24 * 60 * 60 * 1000,
  },
});

app.use(sessionParser);

const server = app.listen(3000);

server.on('upgrade', (req, socket, head) => {
  // Parsificare la sessione dalla richiesta di upgrade
  sessionParser(req, {}, () => {
    if (!req.session?.userId) {
      socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
      socket.destroy();
      return;
    }

    wss.handleUpgrade(req, socket, head, (ws) => {
      ws.userId = req.session.userId;
      wss.emit('connection', ws, req);
    });
  });
});
```

### Ticket-based authentication

Approccio ibrido: il client ottiene un ticket monouso via HTTP (con autenticazione standard), poi lo usa per l'handshake WebSocket. Il ticket ha scadenza breve e può essere usato una sola volta.

```javascript
// Step 1: Client richiede ticket via HTTP
// POST /api/ws-ticket
// Authorization: Bearer <access-token>

// Server HTTP — emissione ticket
const crypto = require('node:crypto');
const tickets = new Map();

app.post('/api/ws-ticket', authenticateMiddleware, (req, res) => {
  const ticket = crypto.randomBytes(32).toString('hex');
  tickets.set(ticket, {
    userId: req.userId,
    role: req.role,
    createdAt: Date.now(),
    expiresAt: Date.now() + 30_000, // 30 secondi
  });
  res.json({ ticket });
});

// Step 2: Client connette con il ticket
// const ws = new WebSocket(`wss://api.example.com/ws?ticket=${ticket}`);

// Server WebSocket — validazione ticket
server.on('upgrade', (req, socket, head) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const ticket = url.searchParams.get('ticket');

  const ticketData = tickets.get(ticket);
  if (!ticketData || ticketData.expiresAt < Date.now()) {
    tickets.delete(ticket); // cleanup
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
    socket.destroy();
    return;
  }

  // Ticket monouso — eliminare dopo l'uso
  tickets.delete(ticket);

  wss.handleUpgrade(req, socket, head, (ws) => {
    ws.userId = ticketData.userId;
    ws.role = ticketData.role;
    wss.emit('connection', ws, req);
  });
});
```

### Rinnovo token durante la connessione

I token JWT scadono. Per connessioni WebSocket di lunga durata, è necessario un meccanismo di rinnovo.

```javascript
// Server — controllo scadenza token e rinnovo
wss.on('connection', (ws) => {
  // Controllo periodico scadenza
  const expiryCheck = setInterval(() => {
    if (ws.tokenExp && ws.tokenExp * 1000 < Date.now() + 60_000) {
      // Token scade tra meno di 60s, richiedere rinnovo
      ws.send(JSON.stringify({
        type: 'token_expiring',
        expiresIn: ws.tokenExp * 1000 - Date.now(),
      }));
    }

    if (ws.tokenExp && ws.tokenExp * 1000 < Date.now()) {
      ws.close(1008, 'Token expired');
    }
  }, 30_000);

  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());

    if (msg.type === 'token_refresh') {
      try {
        const decoded = jwt.verify(msg.newToken, process.env.JWT_SECRET);
        if (decoded.sub !== ws.userId) {
          ws.close(1008, 'User mismatch on refresh');
          return;
        }
        ws.tokenExp = decoded.exp;
        ws.send(JSON.stringify({ type: 'token_refreshed' }));
      } catch {
        ws.close(1008, 'Invalid refresh token');
      }
      return;
    }

    // ... gestione altri messaggi
  });

  ws.on('close', () => {
    clearInterval(expiryCheck);
  });
});
```

---

## Autorizzazione WebSocket

L'autenticazione verifica l'identità. L'autorizzazione controlla cosa l'utente autenticato può fare: a quali canali può iscriversi, quali messaggi può inviare, quali azioni può compiere.

### Autorizzazione per canale

```javascript
// Definizione permessi canale
const CHANNEL_PERMISSIONS = {
  'public': { roles: ['user', 'admin', 'guest'] },
  'team-*': { roles: ['user', 'admin'], checkTeamMembership: true },
  'admin-*': { roles: ['admin'] },
  'user-{userId}': { ownerOnly: true },
  'system': { roles: ['admin'], readOnly: true },
};

function canSubscribe(ws, channel) {
  for (const [pattern, rules] of Object.entries(CHANNEL_PERMISSIONS)) {
    if (matchChannel(pattern, channel)) {
      // Verifica ruolo
      if (rules.roles && !rules.roles.includes(ws.role)) {
        return false;
      }

      // Verifica appartenenza team
      if (rules.checkTeamMembership) {
        const teamId = channel.split('-')[1];
        if (!ws.teams?.includes(teamId)) {
          return false;
        }
      }

      // Verifica owner
      if (rules.ownerOnly) {
        const expectedUserId = channel.replace('user-', '');
        if (ws.userId !== expectedUserId) {
          return false;
        }
      }

      return true;
    }
  }
  return false; // default deny
}

function canPublish(ws, channel) {
  const rules = findChannelRules(channel);
  if (rules?.readOnly && ws.role !== 'admin') {
    return false;
  }
  return canSubscribe(ws, channel);
}
```

### Autorizzazione per messaggio

```javascript
// Schema messaggi con permessi
const MESSAGE_SCHEMAS = {
  'chat:send': {
    requiredRole: 'user',
    validate: (payload) => typeof payload.text === 'string' && payload.text.length <= 2000,
    rateLimit: { max: 30, window: 60_000 }, // 30 messaggi al minuto
  },
  'chat:delete': {
    requiredRole: 'user',
    validate: (payload) => typeof payload.messageId === 'string',
    ownerOrAdmin: true, // solo il proprietario o admin
  },
  'admin:broadcast': {
    requiredRole: 'admin',
    validate: (payload) => typeof payload.text === 'string',
    rateLimit: { max: 5, window: 60_000 },
  },
  'admin:kick': {
    requiredRole: 'admin',
    validate: (payload) => typeof payload.targetUserId === 'string',
    audit: true, // logga questa azione
  },
};

async function authorizeMessage(ws, messageType, payload) {
  const schema = MESSAGE_SCHEMAS[messageType];
  if (!schema) {
    return { allowed: false, reason: 'Unknown message type' };
  }

  // Verifica ruolo
  const roleHierarchy = { guest: 0, user: 1, moderator: 2, admin: 3 };
  if (roleHierarchy[ws.role] < roleHierarchy[schema.requiredRole]) {
    return { allowed: false, reason: 'Insufficient role' };
  }

  // Verifica payload
  if (schema.validate && !schema.validate(payload)) {
    return { allowed: false, reason: 'Invalid payload' };
  }

  // Verifica rate limit
  if (schema.rateLimit) {
    const key = `ratelimit:${ws.userId}:${messageType}`;
    const isLimited = await checkRateLimit(key, schema.rateLimit);
    if (isLimited) {
      return { allowed: false, reason: 'Rate limited' };
    }
  }

  // Audit logging
  if (schema.audit) {
    auditLog({
      action: messageType,
      userId: ws.userId,
      payload,
      timestamp: new Date().toISOString(),
    });
  }

  return { allowed: true };
}
```

---

## Minacce di sicurezza WebSocket

### CSWSH — Cross-Site WebSocket Hijacking

Questa è la vulnerabilità WebSocket più critica. I browser inviano automaticamente i cookie durante l'handshake WebSocket, indipendentemente dall'origin. Se il server autentica solo tramite cookie senza validare l'origin, un sito malevolo può stabilire una connessione WebSocket al server della vittima usando le credenziali dell'utente.

```javascript
// ATTACCO — pagina malevola su evil.com
// L'utente è autenticato su example.com (ha un cookie di sessione valido)
// evil.com apre un WebSocket verso example.com:
const ws = new WebSocket('wss://example.com/ws');
// I cookie di example.com vengono inviati automaticamente!
// Il server accetta la connessione perché i cookie sono validi.
// evil.com può ora leggere/inviare messaggi come l'utente vittima.
```

**Difesa — validazione rigorosa dell'Origin:**

```javascript
const ALLOWED_ORIGINS = new Set([
  'https://example.com',
  'https://app.example.com',
]);

server.on('upgrade', (req, socket, head) => {
  const origin = req.headers.origin;

  // CRITICO: Origin può essere assente per connessioni non-browser.
  // Decidere la policy: rifiutare se assente (più sicuro)
  // o accettare (necessario per client non-browser).
  if (!origin) {
    // Per applicazioni solo-browser, rifiutare
    socket.write('HTTP/1.1 403 Forbidden\r\n\r\n');
    socket.destroy();
    return;
  }

  if (!ALLOWED_ORIGINS.has(origin)) {
    console.warn(`CSWSH attempt blocked: origin=${origin}, ip=${req.socket.remoteAddress}`);
    socket.write('HTTP/1.1 403 Forbidden\r\n\r\n');
    socket.destroy();
    return;
  }

  // Procedere con l'upgrade
  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit('connection', ws, req);
  });
});
```

**Difesa combinata — Origin + CSRF token:**

```javascript
server.on('upgrade', (req, socket, head) => {
  const origin = req.headers.origin;
  const url = new URL(req.url, `http://${req.headers.host}`);
  const csrfToken = url.searchParams.get('csrf');

  // Validazione origin
  if (!ALLOWED_ORIGINS.has(origin)) {
    socket.write('HTTP/1.1 403 Forbidden\r\n\r\n');
    socket.destroy();
    return;
  }

  // Validazione CSRF token (ottenuto via API HTTP protetta)
  if (!csrfToken || !validateCsrfToken(csrfToken, req)) {
    socket.write('HTTP/1.1 403 Forbidden\r\n\r\n');
    socket.destroy();
    return;
  }

  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit('connection', ws, req);
  });
});
```

### Message Injection

I messaggi WebSocket non hanno la protezione naturale delle richieste HTTP (CSRF token, header validati). Un messaggio malevolo può manipolare lo stato dell'applicazione.

```javascript
// ATTACCO — messaggio injection
// L'attaccante invia un messaggio che tenta di impersonare un admin
ws.send(JSON.stringify({
  type: 'admin:broadcast',
  from: 'admin',          // campo forgiato
  role: 'admin',          // campo forgiato
  text: 'Manutenzione: aggiornate le credenziali su evil.com',
}));

// DIFESA — mai fidarsi dei campi del messaggio
function handleMessage(ws, rawData) {
  const msg = JSON.parse(rawData.toString());

  // SEMPRE usare l'identità dal server, MAI dal messaggio
  const authenticatedUser = {
    userId: ws.userId,   // impostato durante l'autenticazione
    role: ws.role,       // impostato durante l'autenticazione
  };

  // Ignorare qualsiasi campo "from", "role", "userId" nel messaggio
  const sanitizedMessage = {
    type: msg.type,
    payload: sanitizePayload(msg.payload),
    from: authenticatedUser.userId,  // sovrascrivere sempre
    timestamp: Date.now(),           // timestamp del server
  };

  processMessage(authenticatedUser, sanitizedMessage);
}
```

### Denial of Service (DoS)

```javascript
// Vettori DoS WebSocket:
// 1. Apertura massiva di connessioni
// 2. Invio di messaggi enormi
// 3. Flood di messaggi piccoli
// 4. Slowloris WebSocket (connessione aperta, nessun dato)
// 5. Frame di continuazione infiniti (frammentazione abusata)

// DIFESA COMPLETA
const MAX_CONNECTIONS_PER_IP = 10;
const MAX_PAYLOAD_SIZE = 64 * 1024; // 64KB
const MAX_MESSAGES_PER_SECOND = 20;
const MAX_FRAMES_PER_MESSAGE = 100;
const CONNECTION_IDLE_TIMEOUT = 300_000; // 5 minuti

const connectionsByIp = new Map();

function getClientIp(req) {
  return req.headers['x-forwarded-for']?.split(',')[0]?.trim()
    || req.socket.remoteAddress;
}

server.on('upgrade', (req, socket, head) => {
  const ip = getClientIp(req);
  const currentConnections = connectionsByIp.get(ip) || 0;

  if (currentConnections >= MAX_CONNECTIONS_PER_IP) {
    socket.write('HTTP/1.1 429 Too Many Requests\r\n\r\n');
    socket.destroy();
    return;
  }

  connectionsByIp.set(ip, currentConnections + 1);

  wss.handleUpgrade(req, socket, head, (ws) => {
    ws.clientIp = ip;
    ws.messageTimestamps = [];
    ws.lastActivity = Date.now();

    wss.emit('connection', ws, req);
  });
});

wss.on('connection', (ws) => {
  // Idle timeout
  const idleTimer = setInterval(() => {
    if (Date.now() - ws.lastActivity > CONNECTION_IDLE_TIMEOUT) {
      ws.close(1000, 'Idle timeout');
    }
  }, 60_000);

  ws.on('message', (data) => {
    ws.lastActivity = Date.now();

    // Limite dimensione (ws ha anche maxPayload, doppio controllo)
    if (data.length > MAX_PAYLOAD_SIZE) {
      ws.close(1009, 'Message too big');
      return;
    }

    // Rate limiting basato su sliding window
    const now = Date.now();
    ws.messageTimestamps.push(now);
    ws.messageTimestamps = ws.messageTimestamps.filter(t => t > now - 1000);

    if (ws.messageTimestamps.length > MAX_MESSAGES_PER_SECOND) {
      ws.close(1008, 'Rate limit exceeded');
      return;
    }

    // ... gestione messaggio
  });

  ws.on('close', () => {
    clearInterval(idleTimer);
    const count = connectionsByIp.get(ws.clientIp) || 1;
    if (count <= 1) {
      connectionsByIp.delete(ws.clientIp);
    } else {
      connectionsByIp.set(ws.clientIp, count - 1);
    }
  });
});
```

---

## Validazione input

### Validazione schema server-side

Mai fidarsi dei dati ricevuti via WebSocket. Ogni messaggio deve essere validato prima di essere processato.

```javascript
// Validazione con Zod (type-safe)
const { z } = require('zod');

const MessageSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('chat:send'),
    channel: z.string().min(1).max(64).regex(/^[a-zA-Z0-9_-]+$/),
    text: z.string().min(1).max(2000).transform(sanitizeHtml),
  }),
  z.object({
    type: z.literal('chat:typing'),
    channel: z.string().min(1).max(64),
    isTyping: z.boolean(),
  }),
  z.object({
    type: z.literal('presence:update'),
    status: z.enum(['online', 'away', 'dnd', 'offline']),
  }),
  z.object({
    type: z.literal('subscribe'),
    channels: z.array(z.string().max(64)).min(1).max(20),
  }),
  z.object({
    type: z.literal('unsubscribe'),
    channels: z.array(z.string().max(64)).min(1).max(20),
  }),
]);

function validateMessage(ws, rawData) {
  // Step 1: verificare che sia una stringa valida
  let text;
  try {
    text = rawData.toString('utf-8');
  } catch {
    ws.close(1007, 'Invalid UTF-8');
    return null;
  }

  // Step 2: verificare che sia JSON valido
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    ws.close(1007, 'Invalid JSON');
    return null;
  }

  // Step 3: verificare contro lo schema
  const result = MessageSchema.safeParse(parsed);
  if (!result.success) {
    ws.send(JSON.stringify({
      type: 'error',
      code: 'VALIDATION_ERROR',
      details: result.error.issues.map(i => ({
        path: i.path.join('.'),
        message: i.message,
      })),
    }));
    return null;
  }

  return result.data;
}
```

### Sanitizzazione HTML

```javascript
// Sanitizzazione base senza dipendenze esterne
function sanitizeHtml(input) {
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

// Per HTML ricco, usare una libreria dedicata come DOMPurify (server-side con jsdom)
const createDOMPurify = require('dompurify');
const { JSDOM } = require('jsdom');

const window = new JSDOM('').window;
const DOMPurify = createDOMPurify(window);

function sanitizeRichText(html) {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'code', 'pre'],
    ALLOWED_ATTR: ['href'],
    ALLOW_DATA_ATTR: false,
  });
}
```

### Limiti dimensione e profondità

```javascript
const MAX_JSON_DEPTH = 5;
const MAX_STRING_LENGTH = 10_000;
const MAX_ARRAY_LENGTH = 100;

function checkDepth(obj, currentDepth = 0) {
  if (currentDepth > MAX_JSON_DEPTH) {
    throw new Error('JSON too deeply nested');
  }

  if (typeof obj === 'string' && obj.length > MAX_STRING_LENGTH) {
    throw new Error('String value too long');
  }

  if (Array.isArray(obj)) {
    if (obj.length > MAX_ARRAY_LENGTH) {
      throw new Error('Array too long');
    }
    for (const item of obj) {
      checkDepth(item, currentDepth + 1);
    }
  } else if (obj !== null && typeof obj === 'object') {
    for (const value of Object.values(obj)) {
      checkDepth(value, currentDepth + 1);
    }
  }
}
```

---

## Rate limiting per WebSocket

Il rate limiting per WebSocket richiede approcci diversi da HTTP. Una connessione è persistente: il rate limiting opera per connessione, non per richiesta.

### Sliding window per connessione

```javascript
class ConnectionRateLimiter {
  constructor(options = {}) {
    this.maxMessages = options.maxMessages || 30;
    this.windowMs = options.windowMs || 60_000;
    this.maxBurstSize = options.maxBurstSize || 10;
    this.burstWindowMs = options.burstWindowMs || 1000;
    this.timestamps = [];
  }

  canSend() {
    const now = Date.now();

    // Pulire timestamp vecchi
    this.timestamps = this.timestamps.filter(t => t > now - this.windowMs);

    // Controllo finestra lunga
    if (this.timestamps.length >= this.maxMessages) {
      return {
        allowed: false,
        retryAfter: this.timestamps[0] + this.windowMs - now,
        reason: 'Rate limit exceeded',
      };
    }

    // Controllo burst (messaggi in rapida successione)
    const recentBurst = this.timestamps.filter(t => t > now - this.burstWindowMs);
    if (recentBurst.length >= this.maxBurstSize) {
      return {
        allowed: false,
        retryAfter: recentBurst[0] + this.burstWindowMs - now,
        reason: 'Burst limit exceeded',
      };
    }

    this.timestamps.push(now);
    return { allowed: true };
  }
}

// Utilizzo
wss.on('connection', (ws) => {
  const limiter = new ConnectionRateLimiter({
    maxMessages: 30,
    windowMs: 60_000,
    maxBurstSize: 10,
    burstWindowMs: 1_000,
  });

  ws.on('message', (data) => {
    const check = limiter.canSend();
    if (!check.allowed) {
      ws.send(JSON.stringify({
        type: 'error',
        code: 'RATE_LIMITED',
        retryAfter: check.retryAfter,
        reason: check.reason,
      }));
      return;
    }

    // Processare il messaggio normalmente
    handleMessage(ws, data);
  });
});
```

### Rate limiting distribuito con Redis

Per deploymnent multi-server, il rate limiting deve essere centralizzato.

```javascript
const Redis = require('ioredis');
const redis = new Redis('redis://redis.internal:6379');

class DistributedRateLimiter {
  constructor(redis) {
    this.redis = redis;
  }

  async checkRate(userId, action, limit, windowSeconds) {
    const key = `ratelimit:${action}:${userId}`;
    const now = Date.now();
    const windowStart = now - windowSeconds * 1000;

    const pipeline = this.redis.pipeline();
    pipeline.zremrangebyscore(key, 0, windowStart);
    pipeline.zadd(key, now, `${now}:${Math.random()}`);
    pipeline.zcard(key);
    pipeline.expire(key, windowSeconds);

    const results = await pipeline.exec();
    const count = results[2][1];

    if (count > limit) {
      const oldestInWindow = await this.redis.zrange(key, 0, 0, 'WITHSCORES');
      const retryAfter = oldestInWindow.length >= 2
        ? parseInt(oldestInWindow[1]) + windowSeconds * 1000 - now
        : windowSeconds * 1000;

      return { allowed: false, remaining: 0, retryAfter };
    }

    return { allowed: true, remaining: limit - count, retryAfter: 0 };
  }
}

// Utilizzo
const rateLimiter = new DistributedRateLimiter(redis);

ws.on('message', async (data) => {
  const check = await rateLimiter.checkRate(ws.userId, 'ws:message', 100, 60);

  if (!check.allowed) {
    ws.send(JSON.stringify({
      type: 'error',
      code: 'RATE_LIMITED',
      remaining: check.remaining,
      retryAfterMs: check.retryAfter,
    }));
    return;
  }

  handleMessage(ws, data);
});
```

### Rate limiting per tipo di messaggio

```javascript
const RATE_LIMITS = {
  'chat:send':      { max: 30,  windowMs: 60_000 },
  'chat:typing':    { max: 5,   windowMs: 3_000 },
  'presence:update':{ max: 10,  windowMs: 60_000 },
  'file:upload':    { max: 5,   windowMs: 300_000 },
  'admin:broadcast':{ max: 3,   windowMs: 60_000 },
};

function createPerTypeLimiter() {
  const limiters = new Map();

  return function checkRate(messageType) {
    const config = RATE_LIMITS[messageType];
    if (!config) return { allowed: true };

    if (!limiters.has(messageType)) {
      limiters.set(messageType, new ConnectionRateLimiter({
        maxMessages: config.max,
        windowMs: config.windowMs,
      }));
    }

    return limiters.get(messageType).canSend();
  };
}
```

---

## TLS — WSS

### Configurazione WSS

```javascript
const https = require('node:https');
const fs = require('node:fs');
const { WebSocketServer } = require('ws');

const server = https.createServer({
  cert: fs.readFileSync('/etc/letsencrypt/live/ws.example.com/fullchain.pem'),
  key: fs.readFileSync('/etc/letsencrypt/live/ws.example.com/privkey.pem'),

  // Configurazione TLS sicura
  minVersion: 'TLSv1.2',
  ciphers: [
    'TLS_AES_256_GCM_SHA384',
    'TLS_CHACHA20_POLY1305_SHA256',
    'TLS_AES_128_GCM_SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES256-GCM-SHA384',
    'ECDHE-ECDSA-CHACHA20-POLY1305',
    'ECDHE-RSA-CHACHA20-POLY1305',
  ].join(':'),

  honorCipherOrder: true,
  ecdhCurve: 'X25519:P-256:P-384',
});

const wss = new WebSocketServer({ server });

wss.on('connection', (ws, req) => {
  // La connessione è ora cifrata
  console.log('Connessione WSS stabilita');
});

server.listen(443);
```

### Terminazione TLS con Nginx

In produzione, è comune terminare TLS al reverse proxy (Nginx, HAProxy) e usare WS non cifrato internamente.

```nginx
server {
    listen 443 ssl http2;
    server_name ws.example.com;

    ssl_certificate /etc/letsencrypt/live/ws.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ws.example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 1.1.1.1 8.8.8.8 valid=300s;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    location /ws {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

### Rinnovo certificati automatico

```bash
#!/bin/bash
# /etc/cron.d/renew-certs
# Rinnovo automatico Let's Encrypt con reload Nginx
0 3 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## Strategie di riconnessione

### Exponential backoff con jitter

```javascript
class WebSocketClient {
  constructor(url, options = {}) {
    this.url = url;
    this.options = {
      maxReconnectAttempts: options.maxReconnectAttempts ?? 15,
      baseDelay: options.baseDelay ?? 1000,
      maxDelay: options.maxDelay ?? 30_000,
      jitterFactor: options.jitterFactor ?? 0.3,
      ...options,
    };

    this.ws = null;
    this.reconnectAttempt = 0;
    this.intentionallyClosed = false;
    this.messageQueue = [];
    this.listeners = new Map();
  }

  connect() {
    this.intentionallyClosed = false;
    this.ws = new WebSocket(this.url);

    this.ws.addEventListener('open', () => {
      console.log('WebSocket connesso');
      this.reconnectAttempt = 0;
      this.flushQueue();
      this.emit('connected');
    });

    this.ws.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit('message', data);
      } catch {
        console.warn('Messaggio non-JSON ricevuto');
      }
    });

    this.ws.addEventListener('close', (event) => {
      this.emit('disconnected', event);

      if (!this.intentionallyClosed && !event.wasClean) {
        this.scheduleReconnect();
      }
    });

    this.ws.addEventListener('error', () => {
      // L'evento 'close' viene sempre emesso dopo 'error'
      // La riconnessione è gestita nel handler 'close'
    });
  }

  scheduleReconnect() {
    if (this.reconnectAttempt >= this.options.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('reconnect_failed');
      return;
    }

    const delay = this.calculateDelay();
    this.reconnectAttempt++;

    console.log(`Riconnessione #${this.reconnectAttempt} tra ${delay}ms`);
    this.emit('reconnecting', { attempt: this.reconnectAttempt, delay });

    setTimeout(() => this.connect(), delay);
  }

  calculateDelay() {
    // Exponential backoff: baseDelay * 2^attempt
    const exponentialDelay = this.options.baseDelay * Math.pow(2, this.reconnectAttempt);
    const cappedDelay = Math.min(exponentialDelay, this.options.maxDelay);

    // Aggiungere jitter per evitare thundering herd
    const jitter = cappedDelay * this.options.jitterFactor * (Math.random() * 2 - 1);
    return Math.max(0, Math.floor(cappedDelay + jitter));
  }

  send(data) {
    const message = typeof data === 'string' ? data : JSON.stringify(data);

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      // Accodare il messaggio per invio dopo la riconnessione
      this.messageQueue.push(message);
    }
  }

  flushQueue() {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(this.messageQueue.shift());
    }
  }

  close(code = 1000, reason = 'Client closing') {
    this.intentionallyClosed = true;
    this.ws?.close(code, reason);
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    for (const cb of callbacks) {
      cb(data);
    }
  }
}

// Utilizzo
const client = new WebSocketClient('wss://api.example.com/ws', {
  maxReconnectAttempts: 20,
  baseDelay: 500,
  maxDelay: 30_000,
});

client.on('connected', () => {
  client.send({ type: 'subscribe', channel: 'updates' });
});

client.on('message', (data) => {
  console.log('Ricevuto:', data);
});

client.on('reconnecting', ({ attempt, delay }) => {
  showNotification(`Riconnessione in corso (tentativo ${attempt})...`);
});

client.on('reconnect_failed', () => {
  showError('Connessione persa. Ricaricare la pagina.');
});

client.connect();
```

### Gestione stato connessione

```javascript
// State machine per la connessione WebSocket
const ConnectionState = Object.freeze({
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  AUTHENTICATING: 'authenticating',
  AUTHENTICATED: 'authenticated',
  RECONNECTING: 'reconnecting',
  FAILED: 'failed',
});

class ConnectionStateMachine {
  constructor() {
    this.state = ConnectionState.DISCONNECTED;
    this.listeners = [];
  }

  transition(newState) {
    const validTransitions = {
      [ConnectionState.DISCONNECTED]: [ConnectionState.CONNECTING],
      [ConnectionState.CONNECTING]: [ConnectionState.CONNECTED, ConnectionState.RECONNECTING, ConnectionState.FAILED],
      [ConnectionState.CONNECTED]: [ConnectionState.AUTHENTICATING, ConnectionState.DISCONNECTED],
      [ConnectionState.AUTHENTICATING]: [ConnectionState.AUTHENTICATED, ConnectionState.DISCONNECTED],
      [ConnectionState.AUTHENTICATED]: [ConnectionState.DISCONNECTED, ConnectionState.RECONNECTING],
      [ConnectionState.RECONNECTING]: [ConnectionState.CONNECTING, ConnectionState.FAILED],
      [ConnectionState.FAILED]: [ConnectionState.CONNECTING, ConnectionState.DISCONNECTED],
    };

    if (!validTransitions[this.state]?.includes(newState)) {
      console.warn(`Invalid transition: ${this.state} -> ${newState}`);
      return false;
    }

    const previousState = this.state;
    this.state = newState;
    this.notifyListeners(previousState, newState);
    return true;
  }

  notifyListeners(from, to) {
    for (const listener of this.listeners) {
      listener(from, to);
    }
  }

  onChange(listener) {
    this.listeners.push(listener);
  }
}
```

---

## Pattern di messaggi

### Request-Response

Simulare il pattern request-response su WebSocket, utile per operazioni che richiedono una risposta specifica.

```javascript
// Client — request con correlazione ID
class RequestResponseClient {
  constructor(ws) {
    this.ws = ws;
    this.pendingRequests = new Map();
    this.requestTimeout = 10_000;

    this.ws.addEventListener('message', (event) => {
      const msg = JSON.parse(event.data);
      if (msg.requestId && this.pendingRequests.has(msg.requestId)) {
        const { resolve, timer } = this.pendingRequests.get(msg.requestId);
        clearTimeout(timer);
        this.pendingRequests.delete(msg.requestId);
        resolve(msg);
      }
    });
  }

  request(type, payload) {
    return new Promise((resolve, reject) => {
      const requestId = crypto.randomUUID();

      const timer = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error(`Request timeout: ${type}`));
      }, this.requestTimeout);

      this.pendingRequests.set(requestId, { resolve, reject, timer });

      this.ws.send(JSON.stringify({ requestId, type, ...payload }));
    });
  }
}

// Utilizzo
const rpc = new RequestResponseClient(ws);
const user = await rpc.request('user:get', { userId: '123' });
```

```javascript
// Server — gestione request-response
ws.on('message', async (data) => {
  const msg = JSON.parse(data.toString());

  if (msg.requestId) {
    try {
      const result = await handleRequest(msg.type, msg);
      ws.send(JSON.stringify({
        requestId: msg.requestId,
        status: 'success',
        data: result,
      }));
    } catch (err) {
      ws.send(JSON.stringify({
        requestId: msg.requestId,
        status: 'error',
        error: err.message,
      }));
    }
  }
});
```

### Pub/Sub con canali

```javascript
// Server — sistema pub/sub
class PubSubServer {
  constructor(wss) {
    this.wss = wss;
    this.channels = new Map(); // channel -> Set<ws>
  }

  subscribe(ws, channel) {
    if (!this.channels.has(channel)) {
      this.channels.set(channel, new Set());
    }
    this.channels.get(channel).add(ws);
  }

  unsubscribe(ws, channel) {
    this.channels.get(channel)?.delete(ws);
    if (this.channels.get(channel)?.size === 0) {
      this.channels.delete(channel);
    }
  }

  unsubscribeAll(ws) {
    for (const [channel, subscribers] of this.channels) {
      subscribers.delete(ws);
      if (subscribers.size === 0) {
        this.channels.delete(channel);
      }
    }
  }

  publish(channel, payload, excludeWs = null) {
    const subscribers = this.channels.get(channel);
    if (!subscribers) return 0;

    const message = JSON.stringify({
      type: 'channel:message',
      channel,
      payload,
      timestamp: Date.now(),
    });

    let delivered = 0;
    for (const ws of subscribers) {
      if (ws !== excludeWs && ws.readyState === 1) {
        ws.send(message);
        delivered++;
      }
    }
    return delivered;
  }

  getSubscriberCount(channel) {
    return this.channels.get(channel)?.size || 0;
  }

  getChannels() {
    return Array.from(this.channels.keys());
  }
}
```

### Room con presenza (presence)

```javascript
// Gestione room con tracciamento presenza
class RoomManager {
  constructor(pubsub) {
    this.pubsub = pubsub;
    this.rooms = new Map(); // roomId -> Map<userId, userMeta>
  }

  join(ws, roomId) {
    if (!this.rooms.has(roomId)) {
      this.rooms.set(roomId, new Map());
    }

    const room = this.rooms.get(roomId);
    room.set(ws.userId, {
      joinedAt: Date.now(),
      status: 'online',
    });

    this.pubsub.subscribe(ws, `room:${roomId}`);

    // Notifica gli altri nella room
    this.pubsub.publish(`room:${roomId}`, {
      type: 'presence:join',
      userId: ws.userId,
      members: this.getMembers(roomId),
    }, ws);

    // Invia lo stato corrente al nuovo membro
    ws.send(JSON.stringify({
      type: 'room:state',
      roomId,
      members: this.getMembers(roomId),
    }));
  }

  leave(ws, roomId) {
    const room = this.rooms.get(roomId);
    if (!room) return;

    room.delete(ws.userId);
    this.pubsub.unsubscribe(ws, `room:${roomId}`);

    if (room.size === 0) {
      this.rooms.delete(roomId);
    } else {
      this.pubsub.publish(`room:${roomId}`, {
        type: 'presence:leave',
        userId: ws.userId,
        members: this.getMembers(roomId),
      });
    }
  }

  getMembers(roomId) {
    const room = this.rooms.get(roomId);
    if (!room) return [];
    return Array.from(room.entries()).map(([userId, meta]) => ({
      userId,
      ...meta,
    }));
  }
}
```

---

## Architetture real-time

### Chat in tempo reale

```javascript
// Server chat completo con tipizzazione, cronologia e notifiche
const { WebSocketServer } = require('ws');
const { z } = require('zod');

const ChatMessageSchema = z.object({
  type: z.literal('chat:send'),
  roomId: z.string().max(64),
  text: z.string().min(1).max(4000),
  replyTo: z.string().optional(),
});

class ChatServer {
  constructor(wss, db) {
    this.wss = wss;
    this.db = db;
    this.rooms = new Map();
    this.typingTimers = new Map();
  }

  async handleMessage(ws, msg) {
    switch (msg.type) {
      case 'chat:send':
        await this.handleSendMessage(ws, msg);
        break;
      case 'chat:typing':
        this.handleTyping(ws, msg);
        break;
      case 'chat:history':
        await this.handleHistory(ws, msg);
        break;
      case 'chat:read':
        await this.handleReadReceipt(ws, msg);
        break;
    }
  }

  async handleSendMessage(ws, msg) {
    const validated = ChatMessageSchema.safeParse(msg);
    if (!validated.success) return;

    const message = {
      id: crypto.randomUUID(),
      roomId: validated.data.roomId,
      userId: ws.userId,
      text: sanitize(validated.data.text),
      replyTo: validated.data.replyTo || null,
      createdAt: new Date().toISOString(),
    };

    // Persistere nel database
    await this.db.messages.insert(message);

    // Broadcast alla room
    this.broadcastToRoom(validated.data.roomId, {
      type: 'chat:message',
      message,
    });

    // Notifiche push per utenti offline
    await this.notifyOfflineMembers(validated.data.roomId, message);
  }

  handleTyping(ws, msg) {
    const key = `${ws.userId}:${msg.roomId}`;

    // Cancellare il timer precedente
    if (this.typingTimers.has(key)) {
      clearTimeout(this.typingTimers.get(key));
    }

    // Broadcast "sta scrivendo"
    this.broadcastToRoom(msg.roomId, {
      type: 'chat:typing',
      userId: ws.userId,
      isTyping: true,
    }, ws);

    // Dopo 3 secondi senza nuovi eventi typing, inviare "ha smesso"
    this.typingTimers.set(key, setTimeout(() => {
      this.broadcastToRoom(msg.roomId, {
        type: 'chat:typing',
        userId: ws.userId,
        isTyping: false,
      });
      this.typingTimers.delete(key);
    }, 3000));
  }

  async handleHistory(ws, msg) {
    const messages = await this.db.messages.findMany({
      where: { roomId: msg.roomId },
      orderBy: { createdAt: 'desc' },
      take: msg.limit || 50,
      cursor: msg.before ? { id: msg.before } : undefined,
    });

    ws.send(JSON.stringify({
      type: 'chat:history',
      roomId: msg.roomId,
      messages: messages.reverse(),
      hasMore: messages.length === (msg.limit || 50),
    }));
  }

  broadcastToRoom(roomId, payload, excludeWs = null) {
    const message = JSON.stringify(payload);
    const room = this.rooms.get(roomId);
    if (!room) return;

    for (const memberWs of room) {
      if (memberWs !== excludeWs && memberWs.readyState === 1) {
        memberWs.send(message);
      }
    }
  }
}
```

### Dashboard live

```javascript
// Server per dashboard real-time con aggregazione
class DashboardServer {
  constructor(wss, dataSource) {
    this.wss = wss;
    this.dataSource = dataSource;
    this.subscriptions = new Map(); // ws -> Set<metricName>
    this.metricCache = new Map();
    this.updateIntervalMs = 1000;
  }

  start() {
    // Aggiornamento periodico delle metriche
    setInterval(async () => {
      const metrics = await this.dataSource.getLatestMetrics();

      for (const [name, value] of Object.entries(metrics)) {
        const cached = this.metricCache.get(name);

        // Inviare solo se il valore è cambiato (delta update)
        if (JSON.stringify(cached) !== JSON.stringify(value)) {
          this.metricCache.set(name, value);
          this.broadcastMetric(name, value);
        }
      }
    }, this.updateIntervalMs);
  }

  subscribe(ws, metricNames) {
    if (!this.subscriptions.has(ws)) {
      this.subscriptions.set(ws, new Set());
    }

    for (const name of metricNames) {
      this.subscriptions.get(ws).add(name);

      // Inviare immediatamente il valore corrente
      const cached = this.metricCache.get(name);
      if (cached) {
        ws.send(JSON.stringify({
          type: 'metric:update',
          name,
          value: cached,
          timestamp: Date.now(),
        }));
      }
    }
  }

  broadcastMetric(name, value) {
    const message = JSON.stringify({
      type: 'metric:update',
      name,
      value,
      timestamp: Date.now(),
    });

    for (const [ws, metrics] of this.subscriptions) {
      if (metrics.has(name) && ws.readyState === 1) {
        ws.send(message);
      }
    }
  }
}
```

### Editing collaborativo — Operational Transform (OT) semplificato

```javascript
// Server per editing collaborativo con CRDT-like conflict resolution
class CollaborativeDocument {
  constructor(docId) {
    this.docId = docId;
    this.content = '';
    this.version = 0;
    this.clients = new Map(); // ws -> { cursor, selection }
    this.history = []; // operazioni per undo/sync
  }

  applyOperation(ws, op) {
    // Trasformare l'operazione contro operazioni concorrenti
    const transformedOp = this.transformAgainstConcurrent(op);

    switch (transformedOp.type) {
      case 'insert':
        this.content =
          this.content.slice(0, transformedOp.position) +
          transformedOp.text +
          this.content.slice(transformedOp.position);
        break;

      case 'delete':
        this.content =
          this.content.slice(0, transformedOp.position) +
          this.content.slice(transformedOp.position + transformedOp.length);
        break;
    }

    this.version++;
    this.history.push({
      ...transformedOp,
      version: this.version,
      userId: ws.userId,
      timestamp: Date.now(),
    });

    // Broadcast a tutti tranne il mittente
    const message = JSON.stringify({
      type: 'doc:op',
      docId: this.docId,
      operation: transformedOp,
      version: this.version,
      userId: ws.userId,
    });

    for (const [clientWs] of this.clients) {
      if (clientWs !== ws && clientWs.readyState === 1) {
        clientWs.send(message);
      }
    }
  }

  transformAgainstConcurrent(op) {
    // Implementazione semplificata di OT
    // In produzione, usare una libreria OT/CRDT dedicata (Yjs, Automerge)
    return op;
  }

  getCursorPositions() {
    const cursors = [];
    for (const [ws, state] of this.clients) {
      cursors.push({
        userId: ws.userId,
        cursor: state.cursor,
        selection: state.selection,
      });
    }
    return cursors;
  }
}
```

### Notifiche real-time

```javascript
// Server notifiche con priorità e raggruppamento
class NotificationServer {
  constructor(wss, redis) {
    this.wss = wss;
    this.redis = redis;
    this.userConnections = new Map(); // userId -> Set<ws>
  }

  registerConnection(ws) {
    if (!this.userConnections.has(ws.userId)) {
      this.userConnections.set(ws.userId, new Set());
    }
    this.userConnections.get(ws.userId).add(ws);

    // Inviare notifiche non lette
    this.sendUnreadNotifications(ws);
  }

  async sendNotification(userId, notification) {
    const enrichedNotification = {
      id: crypto.randomUUID(),
      ...notification,
      createdAt: new Date().toISOString(),
      read: false,
    };

    // Persistere
    await this.redis.lpush(
      `notifications:${userId}`,
      JSON.stringify(enrichedNotification)
    );
    await this.redis.ltrim(`notifications:${userId}`, 0, 99);

    // Inviare in tempo reale se l'utente è connesso
    const connections = this.userConnections.get(userId);
    if (connections) {
      const message = JSON.stringify({
        type: 'notification:new',
        notification: enrichedNotification,
      });
      for (const ws of connections) {
        if (ws.readyState === 1) {
          ws.send(message);
        }
      }
    }
  }

  async sendUnreadNotifications(ws) {
    const raw = await this.redis.lrange(`notifications:${ws.userId}`, 0, -1);
    const notifications = raw
      .map(r => JSON.parse(r))
      .filter(n => !n.read);

    if (notifications.length > 0) {
      ws.send(JSON.stringify({
        type: 'notification:batch',
        notifications,
        unreadCount: notifications.length,
      }));
    }
  }
}
```

---

## Implementazioni server — confronto

| Caratteristica | ws (Node.js) | Socket.IO | Ably | Pusher | Supabase Realtime |
|---------------|-------------|-----------|------|--------|-------------------|
| Protocollo | WebSocket puro | Protocollo custom | Protocollo custom | Protocollo custom | WebSocket + Postgres |
| Trasporto fallback | No | HTTP long-polling | HTTP long-polling, SSE | HTTP long-polling | No |
| Riconnessione automatica | No (manuale) | Sì | Sì | Sì | Sì |
| Room/Canali | Manuale | Built-in | Built-in | Built-in | Built-in (topics) |
| Scaling | Manuale (Redis) | Redis adapter | Managed | Managed | Managed |
| Presenza | Manuale | Manuale | Built-in | Built-in | Built-in |
| Cronologia messaggi | Manuale | No | Sì (24h) | No | Sì (Postgres WAL) |
| Autenticazione | Manuale | Middleware | Token-based | App key + channel auth | RLS Postgres |
| Costo | Gratis (self-hosted) | Gratis (self-hosted) | Pay-per-message | Pay-per-message | Incluso in Supabase |
| Complessità operativa | Alta | Media | Bassa | Bassa | Bassa |
| Latenza | Minima | Bassa (overhead protocollo) | Bassa | Bassa | Media |

### Quando scegliere cosa

**ws (Node.js):** massimo controllo, performance, nessun overhead di protocollo. Ideale per protocolli custom, gaming, applicazioni con requisiti non standard.

**Socket.IO:** ecosistema maturo, room/namespace built-in, fallback automatico. Ideale per applicazioni web standard (chat, collaborazione, notifiche).

**Servizi managed (Ably, Pusher, Supabase Realtime):** nessuna infrastruttura da gestire. Ideale per team piccoli, MVP, applicazioni dove il real-time non è il core business.

### Supabase Realtime — esempio

```javascript
// Client Supabase Realtime (cambio dati Postgres in real-time)
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Ascolto INSERT sulla tabella messages
const channel = supabase
  .channel('room-1')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'messages',
      filter: 'room_id=eq.1',
    },
    (payload) => {
      console.log('Nuovo messaggio:', payload.new);
      displayMessage(payload.new);
    }
  )
  .subscribe();

// Presenza
const presenceChannel = supabase.channel('room-1-presence');

presenceChannel
  .on('presence', { event: 'sync' }, () => {
    const state = presenceChannel.presenceState();
    updateOnlineUsers(Object.values(state).flat());
  })
  .subscribe(async (status) => {
    if (status === 'SUBSCRIBED') {
      await presenceChannel.track({
        userId: currentUser.id,
        name: currentUser.name,
        onlineAt: new Date().toISOString(),
      });
    }
  });
```

---

## Monitoraggio

### Metriche essenziali

```javascript
// Classe di monitoraggio WebSocket
class WebSocketMetrics {
  constructor() {
    this.metrics = {
      connections: {
        active: 0,
        total: 0,
        failed: 0,
        rejected: 0,
      },
      messages: {
        sent: 0,
        received: 0,
        errors: 0,
        bytesIn: 0,
        bytesOut: 0,
      },
      latency: {
        samples: [],
        p50: 0,
        p95: 0,
        p99: 0,
      },
      errors: {
        authFailures: 0,
        rateLimited: 0,
        invalidMessages: 0,
        timeouts: 0,
      },
    };

    // Calcolo periodico percentili
    setInterval(() => this.computePercentiles(), 10_000);
  }

  onConnection() {
    this.metrics.connections.active++;
    this.metrics.connections.total++;
  }

  onDisconnection() {
    this.metrics.connections.active--;
  }

  onConnectionRejected() {
    this.metrics.connections.rejected++;
  }

  onMessageReceived(sizeBytes) {
    this.metrics.messages.received++;
    this.metrics.messages.bytesIn += sizeBytes;
  }

  onMessageSent(sizeBytes) {
    this.metrics.messages.sent++;
    this.metrics.messages.bytesOut += sizeBytes;
  }

  recordLatency(ms) {
    this.metrics.latency.samples.push(ms);
    // Mantenere solo gli ultimi 1000 campioni
    if (this.metrics.latency.samples.length > 1000) {
      this.metrics.latency.samples.shift();
    }
  }

  computePercentiles() {
    const sorted = [...this.metrics.latency.samples].sort((a, b) => a - b);
    if (sorted.length === 0) return;

    this.metrics.latency.p50 = sorted[Math.floor(sorted.length * 0.5)];
    this.metrics.latency.p95 = sorted[Math.floor(sorted.length * 0.95)];
    this.metrics.latency.p99 = sorted[Math.floor(sorted.length * 0.99)];
  }

  getSnapshot() {
    return {
      ...this.metrics,
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memoryUsage: process.memoryUsage(),
    };
  }
}

// Esporre metriche via endpoint HTTP (per Prometheus, Grafana)
app.get('/metrics/ws', (req, res) => {
  res.json(wsMetrics.getSnapshot());
});
```

### Integrazione con Prometheus

```javascript
// Metriche Prometheus per WebSocket
const client = require('prom-client');

const wsConnectionsGauge = new client.Gauge({
  name: 'ws_connections_active',
  help: 'Number of active WebSocket connections',
});

const wsMessagesCounter = new client.Counter({
  name: 'ws_messages_total',
  help: 'Total WebSocket messages processed',
  labelNames: ['direction', 'type'],
});

const wsLatencyHistogram = new client.Histogram({
  name: 'ws_message_latency_seconds',
  help: 'WebSocket message processing latency',
  buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1],
});

const wsErrorsCounter = new client.Counter({
  name: 'ws_errors_total',
  help: 'Total WebSocket errors',
  labelNames: ['type'],
});

// Instrumentazione nel server
wss.on('connection', (ws) => {
  wsConnectionsGauge.inc();

  ws.on('message', (data) => {
    const startTime = Date.now();
    wsMessagesCounter.inc({ direction: 'in', type: 'message' });

    handleMessage(ws, data).finally(() => {
      wsLatencyHistogram.observe((Date.now() - startTime) / 1000);
    });
  });

  ws.on('close', () => {
    wsConnectionsGauge.dec();
  });

  ws.on('error', () => {
    wsErrorsCounter.inc({ type: 'connection' });
  });
});
```

---

## Load testing WebSocket

### k6 — test di carico

```javascript
// k6-ws-test.js — test di carico WebSocket con k6
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const wsMessages = new Counter('ws_messages');
const wsLatency = new Trend('ws_message_latency');

export const options = {
  stages: [
    { duration: '30s', target: 100 },   // ramp up a 100 connessioni
    { duration: '2m',  target: 100 },   // mantieni 100 connessioni
    { duration: '1m',  target: 500 },   // scala a 500
    { duration: '2m',  target: 500 },   // mantieni 500
    { duration: '30s', target: 0 },     // ramp down
  ],
};

export default function () {
  const url = 'wss://api.example.com/ws';
  const params = { tags: { name: 'ws-load-test' } };

  const res = ws.connect(url, params, function (socket) {
    socket.on('open', () => {
      // Autenticazione
      socket.send(JSON.stringify({
        type: 'auth',
        token: __ENV.TEST_TOKEN,
      }));
    });

    socket.on('message', (data) => {
      wsMessages.add(1);
      const msg = JSON.parse(data);

      if (msg.type === 'auth_success') {
        // Dopo l'autenticazione, inviare messaggi periodici
        socket.setInterval(() => {
          const start = Date.now();
          socket.send(JSON.stringify({
            type: 'chat:send',
            roomId: 'load-test',
            text: `Test message ${Date.now()}`,
            sentAt: start,
          }));
        }, 1000); // un messaggio al secondo per connessione
      }

      if (msg.type === 'chat:message' && msg.message.sentAt) {
        wsLatency.add(Date.now() - msg.message.sentAt);
      }
    });

    socket.on('close', () => {});
    socket.on('error', (e) => {
      console.error('WebSocket error:', e.error());
    });

    // Mantieni la connessione per la durata del test
    socket.setTimeout(() => {
      socket.close();
    }, 300000); // 5 minuti
  });

  check(res, {
    'WebSocket connection established': (r) => r && r.status === 101,
  });
}
```

### Artillery — test di carico

```yaml
# artillery-ws-test.yml
config:
  target: "wss://api.example.com"
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 120
      arrivalRate: 50
      name: "Sustained load"
    - duration: 60
      arrivalRate: 100
      name: "Peak load"
  ws:
    rejectUnauthorized: false

scenarios:
  - name: "Chat user simulation"
    engine: ws
    flow:
      # Connessione
      - send:
          type: "auth"
          token: "{{ $env.TEST_TOKEN }}"
      - think: 1

      # Join room
      - send:
          type: "subscribe"
          channel: "general"
      - think: 2

      # Invio messaggi
      - loop:
        - send:
            type: "chat:send"
            roomId: "general"
            text: "Load test message {{ $loopCount }}"
        - think: 3
        count: 20

      # Typing indicator
      - send:
          type: "chat:typing"
          roomId: "general"
          isTyping: true
      - think: 2
      - send:
          type: "chat:typing"
          roomId: "general"
          isTyping: false
```

### Script di test custom

```javascript
// ws-stress-test.js — test personalizzato con metriche dettagliate
const WebSocket = require('ws');

const CONFIG = {
  url: 'wss://api.example.com/ws',
  totalConnections: 1000,
  rampUpRate: 50,        // connessioni al secondo
  messageInterval: 2000, // ms tra messaggi per connessione
  testDuration: 300_000, // 5 minuti
};

const stats = {
  connectionsOpened: 0,
  connectionsFailed: 0,
  connectionsClosed: 0,
  messagesSent: 0,
  messagesReceived: 0,
  errors: 0,
  latencies: [],
  startTime: Date.now(),
};

const connections = [];

function createConnection() {
  return new Promise((resolve) => {
    const ws = new WebSocket(CONFIG.url);
    const connectStart = Date.now();

    ws.on('open', () => {
      stats.connectionsOpened++;
      const connectLatency = Date.now() - connectStart;
      stats.latencies.push(connectLatency);

      // Inviare messaggi periodicamente
      const interval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          const msg = JSON.stringify({
            type: 'ping',
            sentAt: Date.now(),
          });
          ws.send(msg);
          stats.messagesSent++;
        }
      }, CONFIG.messageInterval);

      ws.interval = interval;
      connections.push(ws);
      resolve(ws);
    });

    ws.on('message', () => {
      stats.messagesReceived++;
    });

    ws.on('error', () => {
      stats.errors++;
    });

    ws.on('close', () => {
      stats.connectionsClosed++;
      if (ws.interval) clearInterval(ws.interval);
    });

    setTimeout(() => {
      if (ws.readyState === WebSocket.CONNECTING) {
        stats.connectionsFailed++;
        ws.terminate();
        resolve(null);
      }
    }, 10_000);
  });
}

async function runTest() {
  console.log(`Avvio test: ${CONFIG.totalConnections} connessioni verso ${CONFIG.url}`);

  // Ramp up
  for (let i = 0; i < CONFIG.totalConnections; i++) {
    createConnection();
    if (i % CONFIG.rampUpRate === 0 && i > 0) {
      await new Promise(r => setTimeout(r, 1000));
      printStats();
    }
  }

  console.log('\nRamp up completato. Test in corso...');

  // Attendere la durata del test
  setTimeout(() => {
    console.log('\nTest completato. Chiusura connessioni...');
    for (const ws of connections) {
      if (ws.interval) clearInterval(ws.interval);
      if (ws.readyState === WebSocket.OPEN) ws.close();
    }
    printFinalStats();
    process.exit(0);
  }, CONFIG.testDuration);
}

function printStats() {
  const elapsed = (Date.now() - stats.startTime) / 1000;
  console.log(
    `[${elapsed.toFixed(0)}s] ` +
    `Connessioni: ${stats.connectionsOpened}/${CONFIG.totalConnections} | ` +
    `Msg TX/RX: ${stats.messagesSent}/${stats.messagesReceived} | ` +
    `Errori: ${stats.errors}`
  );
}

function printFinalStats() {
  const sorted = [...stats.latencies].sort((a, b) => a - b);
  console.log('\n=== RISULTATI FINALI ===');
  console.log(`Connessioni aperte: ${stats.connectionsOpened}`);
  console.log(`Connessioni fallite: ${stats.connectionsFailed}`);
  console.log(`Messaggi inviati: ${stats.messagesSent}`);
  console.log(`Messaggi ricevuti: ${stats.messagesReceived}`);
  console.log(`Errori: ${stats.errors}`);
  console.log(`Latenza connessione p50: ${sorted[Math.floor(sorted.length * 0.5)]}ms`);
  console.log(`Latenza connessione p95: ${sorted[Math.floor(sorted.length * 0.95)]}ms`);
  console.log(`Latenza connessione p99: ${sorted[Math.floor(sorted.length * 0.99)]}ms`);
}

runTest();
```

---

## Troubleshooting

### 1. Connessione rifiutata (HTTP 400/403 durante l'upgrade)

**Sintomi:** il client non riesce a stabilire la connessione WebSocket, ricevendo un errore HTTP.

**Cause comuni:**
- Header `Upgrade` mancante o errato
- Origin non consentito
- Proxy che blocca gli upgrade WebSocket
- Path errato

```javascript
// Diagnosi server-side
server.on('upgrade', (req, socket, head) => {
  console.log('Upgrade request:', {
    url: req.url,
    headers: {
      upgrade: req.headers.upgrade,
      connection: req.headers.connection,
      origin: req.headers.origin,
      'sec-websocket-key': req.headers['sec-websocket-key'],
      'sec-websocket-version': req.headers['sec-websocket-version'],
    },
  });
});
```

### 2. Connessione si chiude immediatamente dopo l'apertura

**Sintomi:** l'evento `open` si attiva ma `close` segue in pochi millisecondi.

**Cause comuni:**
- Autenticazione fallita
- Il server chiude la connessione perché l'utente non completa l'auth entro il timeout
- Rate limit raggiunto

```javascript
// Client-side — logga il motivo della chiusura
ws.addEventListener('close', (event) => {
  console.error('Chiusura WebSocket:', {
    code: event.code,
    reason: event.reason,
    wasClean: event.wasClean,
  });

  // Decodificare il close code
  const closeReasons = {
    1000: 'Chiusura normale',
    1001: 'Server in shutdown',
    1006: 'Connessione persa (nessun frame di chiusura)',
    1008: 'Policy violation (probabilmente auth)',
    1009: 'Messaggio troppo grande',
    1011: 'Errore interno del server',
    1012: 'Server in riavvio',
    1013: 'Server sovraccarico',
  };

  console.error('Motivo:', closeReasons[event.code] || 'Sconosciuto');
});
```

### 3. Connessioni "zombie" (half-open connections)

**Sintomi:** il server mantiene connessioni a client che non rispondono più, consumando risorse.

**Causa:** il client è crashato o ha perso la rete senza inviare un frame di chiusura.

**Soluzione:** implementare heartbeat con ping/pong (vedi sezione precedente) e timeout aggressivi.

```javascript
// Rilevamento connessioni zombie
const ZOMBIE_CHECK_INTERVAL = 30_000;
const MAX_MISSED_PONGS = 3;

wss.on('connection', (ws) => {
  ws.missedPongs = 0;

  ws.on('pong', () => {
    ws.missedPongs = 0;
  });
});

setInterval(() => {
  for (const ws of wss.clients) {
    ws.missedPongs++;
    if (ws.missedPongs >= MAX_MISSED_PONGS) {
      console.warn(`Zombie connection detected, terminating. Missed pongs: ${ws.missedPongs}`);
      ws.terminate();
      continue;
    }
    ws.ping();
  }
}, ZOMBIE_CHECK_INTERVAL);
```

### 4. Memory leak — connessioni non rilasciate

**Sintomi:** l'uso di memoria del server cresce nel tempo senza stabilizzarsi.

**Cause comuni:**
- Listener non rimossi quando la connessione si chiude
- Riferimenti alla connessione in strutture dati (Map, Set) non puliti
- Timer (setInterval, setTimeout) non cancellati alla disconnessione
- Closure che catturano riferimenti a oggetti pesanti

```javascript
// Pattern corretto — cleanup completo alla disconnessione
wss.on('connection', (ws) => {
  const timers = [];
  const subscriptions = [];

  // Registrare tutti i timer
  const heartbeat = setInterval(() => ws.ping(), 30_000);
  timers.push(heartbeat);

  const activityCheck = setInterval(() => {
    // ...
  }, 60_000);
  timers.push(activityCheck);

  ws.on('close', () => {
    // Cancellare TUTTI i timer
    for (const timer of timers) {
      clearInterval(timer);
    }

    // Rimuovere da tutte le strutture dati
    clients.delete(ws);
    for (const sub of subscriptions) {
      sub.unsubscribe();
    }

    // Nullificare riferimenti
    ws.removeAllListeners();
  });
});

// Monitoraggio periodico per rilevare leak
setInterval(() => {
  const memUsage = process.memoryUsage();
  console.log('Memory:', {
    rss: `${(memUsage.rss / 1024 / 1024).toFixed(1)}MB`,
    heapUsed: `${(memUsage.heapUsed / 1024 / 1024).toFixed(1)}MB`,
    heapTotal: `${(memUsage.heapTotal / 1024 / 1024).toFixed(1)}MB`,
    external: `${(memUsage.external / 1024 / 1024).toFixed(1)}MB`,
    connections: wss.clients.size,
  });
}, 60_000);
```

### 5. Problemi con proxy e load balancer

**Sintomi:** WebSocket funziona in locale ma non in produzione.

**Cause comuni:**
- Nginx/Apache non configurato per WebSocket upgrade
- AWS ALB con timeout troppo brevi (default 60s)
- Cloudflare proxy che limita la durata delle connessioni (100s free plan)

```nginx
# Nginx — configurazione completa per WebSocket
location /ws {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # CRITICO: timeout sufficientemente lungo
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;

    # Disabilitare buffering
    proxy_buffering off;

    # Header forwarding
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 6. Messaggi persi durante la riconnessione

**Sintomi:** dopo una riconnessione, il client manca dei messaggi inviati durante il downtime.

**Soluzione:** implementare un meccanismo di message sequencing e replay.

```javascript
// Server — sequencing e replay
class MessageSequencer {
  constructor(redis, retentionSeconds = 3600) {
    this.redis = redis;
    this.retention = retentionSeconds;
  }

  async publish(channel, payload) {
    const sequence = await this.redis.incr(`seq:${channel}`);
    const message = { sequence, payload, timestamp: Date.now() };

    await this.redis.zadd(
      `history:${channel}`,
      Date.now(),
      JSON.stringify(message)
    );

    // Pulizia messaggi vecchi
    await this.redis.zremrangebyscore(
      `history:${channel}`,
      0,
      Date.now() - this.retention * 1000
    );

    return message;
  }

  async getMessagesSince(channel, lastSequence) {
    const all = await this.redis.zrange(`history:${channel}`, 0, -1);
    return all
      .map(m => JSON.parse(m))
      .filter(m => m.sequence > lastSequence);
  }
}

// Client — richiesta messaggi persi dopo riconnessione
ws.addEventListener('open', () => {
  if (lastReceivedSequence > 0) {
    ws.send(JSON.stringify({
      type: 'replay',
      channel: 'general',
      sinceSequence: lastReceivedSequence,
    }));
  }
});
```

### 7. Errore: "Max payload size exceeded"

**Sintomi:** il server chiude la connessione con codice 1009.

**Soluzione:** verificare `maxPayload` sia lato server (nella configurazione `ws`) sia lato client. Per file grandi, usare chunking.

```javascript
// Chunking per messaggi grandi
const CHUNK_SIZE = 16 * 1024; // 16KB

function sendLargeMessage(ws, data) {
  const totalChunks = Math.ceil(data.length / CHUNK_SIZE);
  const messageId = crypto.randomUUID();

  for (let i = 0; i < totalChunks; i++) {
    const chunk = data.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE);
    ws.send(JSON.stringify({
      type: 'chunk',
      messageId,
      index: i,
      total: totalChunks,
      data: chunk.toString('base64'),
    }));
  }
}
```

### 8. Throughput degradato sotto carico

**Sintomi:** la latenza dei messaggi aumenta con il numero di connessioni.

**Diagnosi e soluzioni:**
- Verificare `bufferedAmount` lato client (messaggi in coda)
- Controllare l'event loop di Node.js (blocco sincrono)
- Ridurre la frequenza dei broadcast

```javascript
// Monitoraggio event loop lag
const { monitorEventLoopDelay } = require('node:perf_hooks');
const h = monitorEventLoopDelay({ resolution: 20 });
h.enable();

setInterval(() => {
  console.log('Event loop delay:', {
    min: `${(h.min / 1e6).toFixed(1)}ms`,
    max: `${(h.max / 1e6).toFixed(1)}ms`,
    mean: `${(h.mean / 1e6).toFixed(1)}ms`,
    p99: `${(h.percentile(99) / 1e6).toFixed(1)}ms`,
  });
  h.reset();
}, 30_000);
```

### 9. CORS non funziona con WebSocket

**Spiegazione:** CORS non si applica ai WebSocket. Il browser invia l'header `Origin` durante l'handshake, ma non applica la same-origin policy. La validazione dell'origin è interamente responsabilità del server.

### 10. "Error: listen EADDRINUSE"

**Causa:** un altro processo usa già la porta, oppure un precedente processo non è stato terminato correttamente.

```bash
# Trovare il processo che usa la porta
lsof -i :8080
# oppure
ss -tlnp | grep 8080

# Terminare il processo
kill -SIGTERM <PID>
```

### 11. Connessione WebSocket lenta su mobile

**Cause:** keep-alive troppo aggressivo, compressione non abilitata, payload troppo grandi.

**Soluzioni:**
- Ridurre la frequenza di heartbeat su reti mobili
- Usare delta update (inviare solo le differenze)
- Implementare message batching

```javascript
// Message batching per ridurre il numero di frame
class MessageBatcher {
  constructor(ws, flushIntervalMs = 100) {
    this.ws = ws;
    this.queue = [];
    this.timer = setInterval(() => this.flush(), flushIntervalMs);
  }

  enqueue(message) {
    this.queue.push(message);
  }

  flush() {
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0);
    this.ws.send(JSON.stringify({
      type: 'batch',
      messages: batch,
      count: batch.length,
    }));
  }

  destroy() {
    clearInterval(this.timer);
    this.flush();
  }
}
```

### 12. File descriptor exhaustion

**Sintomi:** "Error: EMFILE, too many open files" — il server non può accettare nuove connessioni.

```bash
# Verificare limiti correnti
ulimit -n

# Aumentare per la sessione corrente
ulimit -n 100000

# Aumentare permanentemente in /etc/security/limits.conf
# wsuser    soft    nofile    100000
# wsuser    hard    nofile    100000

# Verificare file descriptor in uso
ls /proc/<PID>/fd | wc -l
```

### 13. Problemi con permessage-deflate

**Sintomi:** alto consumo di memoria, CPU elevata, incompatibilità con alcuni client.

```javascript
// Disabilitare permessage-deflate se causa problemi
const wss = new WebSocketServer({
  port: 8080,
  perMessageDeflate: false, // disabilitare completamente
});

// Oppure configurare in modo conservativo
const wss2 = new WebSocketServer({
  port: 8081,
  perMessageDeflate: {
    serverNoContextTakeover: true,  // riduce memoria server
    clientNoContextTakeover: true,  // riduce memoria client
    threshold: 4096,                // comprimi solo msg > 4KB
  },
});
```

### 14. Token JWT esposto nei log

**Sintomi:** il token di autenticazione appare negli access log del server o del reverse proxy.

**Causa:** il token è nel query parameter dell'URL di handshake.

```nginx
# Nginx — mascherare token nei log
log_format ws_safe '$remote_addr - $remote_user [$time_local] '
                   '"$request_method $uri" $status $body_bytes_sent '
                   '"$http_referer" "$http_user_agent"';
# Usare $uri invece di $request_uri per escludere i query parameters
```

### 15. WebSocket attraverso proxy aziendali

**Sintomi:** la connessione WebSocket fallisce in reti aziendali con proxy HTTP.

**Soluzione:** Socket.IO con fallback su long-polling, oppure tunnel WebSocket attraverso HTTPS.

```javascript
// Socket.IO con ordine di trasporto ottimale
const socket = io('https://api.example.com', {
  transports: ['websocket', 'polling'], // tenta WebSocket, fallback su polling
  upgrade: true,                        // upgrade da polling a WebSocket se possibile
  rememberUpgrade: true,                // ricorda l'upgrade per connessioni future
});
```

### 16. Debugging con wscat e websocat

```bash
# wscat — client WebSocket da terminale
npx wscat -c wss://api.example.com/ws

# Con header custom
npx wscat -c wss://api.example.com/ws -H "Origin: https://example.com"

# websocat — alternativa più potente
websocat wss://api.example.com/ws

# websocat con autenticazione via header
websocat -H "Authorization: Bearer <token>" wss://api.example.com/ws
```

---

## Approfondimento: meccanica del framing e masking

### L'algoritmo di masking — RFC 6455 sezione 5.3

Il masking è un requisito obbligatorio per tutti i frame inviati dal client al server. L'obiettivo non è la confidenzialità (il masking è reversibile), ma la prevenzione di un attacco specifico: il **cache poisoning su proxy intermedi**. Senza masking, un client malevolo potrebbe costruire un payload WebSocket che, interpretato da un proxy HTTP ignaro del protocollo WebSocket, verrebbe scambiato per una risposta HTTP legittima e cacheata, avvelenando la cache per tutti gli utenti.

L'algoritmo è un XOR byte-per-byte con una chiave rotante di 4 byte:

```javascript
// Implementazione dell'algoritmo di masking RFC 6455
function maskPayload(payload, maskingKey) {
  const masked = Buffer.alloc(payload.length);
  for (let i = 0; i < payload.length; i++) {
    masked[i] = payload[i] ^ maskingKey[i % 4];
  }
  return masked;
}

function unmaskPayload(maskedPayload, maskingKey) {
  // L'operazione è identica: XOR è la sua stessa inversa
  return maskPayload(maskedPayload, maskingKey);
}

// Esempio pratico
const payload = Buffer.from('Hello');
const maskingKey = Buffer.from([0x37, 0xfa, 0x21, 0x3d]);

const masked = maskPayload(payload, maskingKey);
console.log('Masked:', masked.toString('hex'));
// => '7f9b4d5158'

const unmasked = unmaskPayload(masked, maskingKey);
console.log('Unmasked:', unmasked.toString('utf-8'));
// => 'Hello'
```

**Requisiti di sicurezza per la masking key:**

- Deve essere generata in modo **crittograficamente casuale** per ogni frame
- Non deve essere prevedibile dall'attaccante
- La stessa chiave non deve essere riutilizzata tra frame consecutivi
- La libreria `ws` usa `crypto.randomBytes(4)` internamente

```javascript
// Parsing manuale di un frame WebSocket — scopo didattico
function parseWebSocketFrame(buffer) {
  let offset = 0;

  const byte0 = buffer[offset++];
  const fin  = (byte0 & 0x80) !== 0;
  const rsv1 = (byte0 & 0x40) !== 0; // usato da permessage-deflate
  const rsv2 = (byte0 & 0x20) !== 0;
  const rsv3 = (byte0 & 0x10) !== 0;
  const opcode = byte0 & 0x0F;

  const byte1 = buffer[offset++];
  const isMasked = (byte1 & 0x80) !== 0;
  let payloadLength = byte1 & 0x7F;

  // Extended payload length
  if (payloadLength === 126) {
    payloadLength = buffer.readUInt16BE(offset);
    offset += 2;
  } else if (payloadLength === 127) {
    // I primi 4 byte del campo a 64 bit devono essere 0
    // (non supportiamo payload > 2^32 in JavaScript)
    const highBits = buffer.readUInt32BE(offset);
    if (highBits !== 0) {
      throw new Error('Payload troppo grande per JavaScript');
    }
    payloadLength = buffer.readUInt32BE(offset + 4);
    offset += 8;
  }

  let maskingKey = null;
  if (isMasked) {
    maskingKey = buffer.slice(offset, offset + 4);
    offset += 4;
  }

  let payload = buffer.slice(offset, offset + payloadLength);
  if (isMasked && maskingKey) {
    payload = unmaskPayload(payload, maskingKey);
  }

  return { fin, rsv1, rsv2, rsv3, opcode, isMasked, payloadLength, payload };
}
```

### Control frame e loro vincoli

I frame di controllo (Ping, Pong, Close) hanno vincoli specifici imposti dalla RFC 6455:

- **Dimensione massima payload:** 125 byte. Un frame di controllo con payload > 125 byte è una violazione del protocollo.
- **FIN bit:** deve essere sempre 1. I frame di controllo non possono essere frammentati.
- **Interleaving:** i frame di controllo possono essere inseriti tra i frame di un messaggio frammentato. Ad esempio, durante l'invio di un messaggio di testo suddiviso in 3 frame, il server può inviare un Ping tra il secondo e il terzo frame.

```javascript
// Validazione lato server dei control frame
function validateControlFrame(frame) {
  if (frame.payloadLength > 125) {
    throw new ProtocolError(
      1002,
      `Control frame payload exceeds 125 bytes: ${frame.payloadLength}`
    );
  }

  if (!frame.fin) {
    throw new ProtocolError(
      1002,
      'Control frame must not be fragmented (FIN must be 1)'
    );
  }

  // Close frame: il payload deve contenere almeno 2 byte (close code)
  // oppure essere vuoto
  if (frame.opcode === 0x8 && frame.payloadLength === 1) {
    throw new ProtocolError(
      1002,
      'Close frame payload must be 0 or >= 2 bytes'
    );
  }

  // Close frame: se presente, il close code deve essere nel range valido
  if (frame.opcode === 0x8 && frame.payloadLength >= 2) {
    const closeCode = frame.payload.readUInt16BE(0);
    const validCodes = [1000, 1001, 1002, 1003, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014];
    const isPrivateRange = closeCode >= 3000 && closeCode <= 4999;
    if (!validCodes.includes(closeCode) && !isPrivateRange) {
      throw new ProtocolError(1002, `Invalid close code: ${closeCode}`);
    }
  }
}
```

---

## Gestione del ciclo di vita della connessione

### State machine completa della connessione

Il ciclo di vita di una connessione WebSocket attraversa stati ben definiti. Una gestione rigorosa di questi stati è essenziale per evitare race condition, perdita di messaggi e memory leak.

```javascript
// State machine completa con gestione di tutti gli stati transitori
const WS_LIFECYCLE = Object.freeze({
  INITIAL:          'initial',
  DNS_RESOLVING:    'dns_resolving',
  TCP_CONNECTING:   'tcp_connecting',
  TLS_HANDSHAKING:  'tls_handshaking',
  HTTP_UPGRADING:   'http_upgrading',
  WS_OPEN:          'ws_open',
  AUTHENTICATING:   'authenticating',
  READY:            'ready',
  DRAINING:         'draining',      // server ha chiesto di chiudere
  CLOSING:          'closing',       // close frame inviato
  CLOSED:           'closed',
  FAILED:           'failed',
});

class ConnectionLifecycle {
  constructor(wsUrl, options = {}) {
    this.url = wsUrl;
    this.state = WS_LIFECYCLE.INITIAL;
    this.stateHistory = [];
    this.options = options;
    this.pendingMessages = [];
    this.ws = null;
  }

  transitionTo(newState, metadata = {}) {
    const timestamp = new Date().toISOString();
    this.stateHistory.push({
      from: this.state,
      to: newState,
      timestamp,
      ...metadata,
    });

    console.log(`[${timestamp}] ${this.state} -> ${newState}`, metadata);
    this.state = newState;
  }

  async connect() {
    this.transitionTo(WS_LIFECYCLE.TCP_CONNECTING);

    this.ws = new WebSocket(this.url);

    this.ws.addEventListener('open', () => {
      this.transitionTo(WS_LIFECYCLE.HTTP_UPGRADING);
      this.transitionTo(WS_LIFECYCLE.WS_OPEN);

      if (this.options.authToken) {
        this.transitionTo(WS_LIFECYCLE.AUTHENTICATING);
        this.ws.send(JSON.stringify({
          type: 'auth',
          token: this.options.authToken,
        }));
      } else {
        this.transitionTo(WS_LIFECYCLE.READY);
        this.flushPending();
      }
    });

    this.ws.addEventListener('message', (event) => {
      const msg = JSON.parse(event.data);

      if (this.state === WS_LIFECYCLE.AUTHENTICATING) {
        if (msg.type === 'auth_success') {
          this.transitionTo(WS_LIFECYCLE.READY);
          this.flushPending();
        } else if (msg.type === 'auth_failure') {
          this.transitionTo(WS_LIFECYCLE.FAILED, { reason: msg.reason });
          this.ws.close(1008, 'Auth failed');
        }
        return;
      }

      if (msg.type === 'server_draining') {
        this.transitionTo(WS_LIFECYCLE.DRAINING, {
          reason: msg.reason,
          reconnectAfter: msg.reconnectAfter,
        });
      }

      this.options.onMessage?.(msg);
    });

    this.ws.addEventListener('close', (event) => {
      this.transitionTo(WS_LIFECYCLE.CLOSED, {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
      });
    });

    this.ws.addEventListener('error', () => {
      if (this.state !== WS_LIFECYCLE.CLOSED) {
        this.transitionTo(WS_LIFECYCLE.FAILED);
      }
    });
  }

  send(message) {
    if (this.state === WS_LIFECYCLE.READY) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.pendingMessages.push(message);
    }
  }

  flushPending() {
    while (this.pendingMessages.length > 0) {
      const msg = this.pendingMessages.shift();
      this.ws.send(JSON.stringify(msg));
    }
  }

  getDiagnostics() {
    return {
      currentState: this.state,
      stateHistory: this.stateHistory,
      pendingMessages: this.pendingMessages.length,
      readyState: this.ws?.readyState,
      bufferedAmount: this.ws?.bufferedAmount,
    };
  }
}
```

### Graceful draining — server-side

Quando il server deve riavviarsi (deploy, manutenzione), le connessioni attive devono essere gestite con un processo di **draining** che minimizza l'impatto sugli utenti:

```javascript
class GracefulDrainManager {
  constructor(wss, options = {}) {
    this.wss = wss;
    this.drainTimeoutMs = options.drainTimeoutMs || 30_000;
    this.isDraining = false;
  }

  startDrain(reason = 'Server maintenance') {
    this.isDraining = true;

    // Fase 1: Notificare tutti i client
    for (const ws of this.wss.clients) {
      if (ws.readyState === 1) {
        ws.send(JSON.stringify({
          type: 'server_draining',
          reason,
          reconnectAfter: 5000, // suggerimento al client
          deadline: Date.now() + this.drainTimeoutMs,
        }));
      }
    }

    // Fase 2: Rifiutare nuove connessioni
    // (gestito dall'event handler 'upgrade' che controlla this.isDraining)

    // Fase 3: Attendere che i client chiudano volontariamente
    setTimeout(() => {
      // Fase 4: Forzare la chiusura delle connessioni rimaste
      let remaining = 0;
      for (const ws of this.wss.clients) {
        remaining++;
        ws.close(1012, 'Server restarting');
      }

      if (remaining > 0) {
        console.warn(`Forced close of ${remaining} remaining connections`);
      }

      // Fase 5: Terminazione finale dopo un breve ritardo
      setTimeout(() => {
        for (const ws of this.wss.clients) {
          ws.terminate();
        }
        this.wss.close();
      }, 5000);
    }, this.drainTimeoutMs);
  }
}

// Integrazione con SIGTERM
const drainManager = new GracefulDrainManager(wss);
process.on('SIGTERM', () => drainManager.startDrain('Deployment'));
process.on('SIGINT', () => drainManager.startDrain('Operator shutdown'));
```

### Gestione della backpressure

La backpressure si verifica quando il server produce messaggi più velocemente di quanto il client riesca a consumarli (o viceversa). Senza gestione, i buffer crescono fino a causare out-of-memory.

```javascript
// Monitoraggio e gestione della backpressure
const BACKPRESSURE_THRESHOLD = 1024 * 1024; // 1MB di dati in coda
const BACKPRESSURE_RESUME = 512 * 1024;     // riprendere a 512KB

function sendWithBackpressure(ws, message) {
  const data = typeof message === 'string' ? message : JSON.stringify(message);

  if (ws.bufferedAmount > BACKPRESSURE_THRESHOLD) {
    // Il client non sta consumando abbastanza velocemente
    console.warn(
      `Backpressure on connection ${ws.userId}: ` +
      `buffered=${ws.bufferedAmount} bytes`
    );

    // Opzione 1: Scartare i messaggi non critici
    if (message.priority !== 'high') {
      ws._droppedMessages = (ws._droppedMessages || 0) + 1;
      return false;
    }

    // Opzione 2: Accodare e riprovare quando il buffer si svuota
    // (rischio: la coda cresce indefinitamente)
  }

  ws.send(data, (err) => {
    if (err) {
      console.error(`Send error for ${ws.userId}:`, err.message);
    }
  });

  return true;
}

// Monitoraggio periodico della backpressure su tutte le connessioni
setInterval(() => {
  for (const ws of wss.clients) {
    if (ws.bufferedAmount > BACKPRESSURE_THRESHOLD) {
      console.warn(`Slow consumer detected: userId=${ws.userId}, ` +
        `buffered=${(ws.bufferedAmount / 1024).toFixed(0)}KB, ` +
        `dropped=${ws._droppedMessages || 0}`);
    }
  }
}, 10_000);
```

---

## Approfondimento: compressione WebSocket (RFC 7692)

### Internals di permessage-deflate

L'estensione `permessage-deflate` (RFC 7692) applica l'algoritmo DEFLATE (RFC 1951) ai messaggi WebSocket prima della trasmissione. La negoziazione avviene durante l'handshake HTTP tramite l'header `Sec-WebSocket-Extensions`.

```
# Negoziazione durante l'handshake
# Richiesta client:
Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits

# Risposta server:
Sec-WebSocket-Extensions: permessage-deflate; server_no_context_takeover;
  client_no_context_takeover; server_max_window_bits=10;
  client_max_window_bits=10
```

**Parametri di negoziazione:**

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `server_max_window_bits` | 15 (32KB) | Dimensione della finestra LZ77 lato server. Valori inferiori riducono la memoria ma peggiorano la compressione. |
| `client_max_window_bits` | 15 (32KB) | Dimensione della finestra LZ77 lato client. |
| `server_no_context_takeover` | false | Se true, il server reinizializza il contesto di compressione per ogni messaggio. Riduce la memoria ma degrada il rapporto di compressione. |
| `client_no_context_takeover` | false | Se true, il client reinizializza il contesto per ogni messaggio. |

### Impatto sulla memoria e trade-off

Il contesto di compressione zlib consuma memoria proporzionale alla dimensione della finestra. Con le impostazioni di default (`window_bits=15`), ogni direzione di comunicazione alloca fino a **32 KB** per il contesto. Con context takeover abilitato (default), il contesto persiste tra messaggi, migliorando la compressione per messaggi simili ma mantenendo la memoria allocata per l'intera durata della connessione.

```javascript
// Calcolo dell'impatto sulla memoria
function estimateCompressionMemory(connections, config) {
  const windowSize = Math.pow(2, config.windowBits || 15);

  // Memoria per contesto: ~(1 << windowBits) per direzione
  // Con context takeover: 2 contesti (send + receive) per connessione
  // Senza context takeover: i contesti vengono liberati tra messaggi
  const perConnectionBytes = config.noContextTakeover
    ? 0 // contesto allocato solo durante la compressione
    : windowSize * 2; // send + receive

  // Overhead aggiuntivo delle strutture interne di zlib
  const zlibOverhead = config.noContextTakeover ? 0 : 100_000; // ~100KB

  const totalMB = (connections * (perConnectionBytes + zlibOverhead)) / (1024 * 1024);

  return {
    perConnectionKB: ((perConnectionBytes + zlibOverhead) / 1024).toFixed(1),
    totalMB: totalMB.toFixed(0),
    connections,
  };
}

// Esempio: 10.000 connessioni con default
console.log(estimateCompressionMemory(10_000, { windowBits: 15 }));
// { perConnectionKB: '161.5', totalMB: '1577', connections: 10000 }

// Esempio: 10.000 connessioni con impostazioni conservative
console.log(estimateCompressionMemory(10_000, { windowBits: 10, noContextTakeover: true }));
// { perConnectionKB: '0.0', totalMB: '0', connections: 10000 }
```

### Quando abilitare o disabilitare la compressione

**Abilitare quando:**
- I messaggi sono prevalentemente testuali (JSON, XML) con alta ridondanza
- La larghezza di banda è un collo di bottiglia (utenti su reti mobili)
- Il numero di connessioni simultanee è relativamente basso (< 5.000)
- I messaggi sono grandi (> 1 KB) — per messaggi piccoli l'overhead di compressione supera il risparmio

**Disabilitare quando:**
- Il server gestisce decine di migliaia di connessioni simultanee
- I messaggi sono piccoli (< 256 byte) — l'overhead supera il beneficio
- I dati sono già compressi (immagini, audio, dati binari)
- La CPU è il collo di bottiglia, non la banda
- La latenza è critica (la compressione aggiunge latenza di elaborazione)

```javascript
// Configurazione ottimizzata per alta scalabilità
const wss = new WebSocketServer({
  port: 8080,
  perMessageDeflate: {
    zlibDeflateOptions: {
      level: 1,          // compressione minima, massima velocità
      memLevel: 4,       // riduce uso di memoria per compressione
    },
    zlibInflateOptions: {
      chunkSize: 4 * 1024, // chunk di decompressione più piccoli
    },
    clientNoContextTakeover: true,  // fondamentale per alta scalabilità
    serverNoContextTakeover: true,  // fondamentale per alta scalabilità
    serverMaxWindowBits: 10,        // finestra ridotta (1KB vs 32KB default)
    threshold: 2048,                // comprimi solo messaggi > 2KB
  },
});
```

---

## Approfondimento: Server-Sent Events vs WebSocket

### Architettura interna di SSE

SSE (Server-Sent Events) usa una connessione HTTP persistente con `Content-Type: text/event-stream`. Il protocollo è testuale e ogni evento segue un formato semplice:

```
id: <event-id>\n
event: <event-type>\n
data: <payload>\n
retry: <milliseconds>\n
\n
```

La differenza architetturale fondamentale rispetto a WebSocket:

- **SSE opera sopra HTTP.** Beneficia di tutto lo stack HTTP: caching, compressione gzip/brotli, proxy, CDN, load balancing, autenticazione standard con header.
- **WebSocket opera accanto a HTTP.** Dopo l'upgrade, il protocollo è completamente diverso. Nessuna delle infrastrutture HTTP si applica direttamente.

### SSE con HTTP/2 — multiplexing

Con HTTP/2, SSE diventa significativamente più potente. HTTP/1.1 limita a 6 connessioni per dominio nel browser, quindi 6 stream SSE esauriscono il budget. HTTP/2 multiplica centinaia di stream su una singola connessione TCP, eliminando questo limite.

```javascript
// Server SSE avanzato con supporto a più canali su un singolo stream
class SSEMultiChannelServer {
  constructor() {
    this.clients = new Map(); // clientId -> { res, channels }
  }

  handleConnection(req, res) {
    const clientId = req.headers['x-client-id'] || crypto.randomUUID();
    const channels = req.query.channels?.split(',') || ['default'];

    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
      'Access-Control-Allow-Origin': 'https://example.com',
    });

    // Invio del retry interval
    res.write(`retry: 3000\n\n`);

    this.clients.set(clientId, { res, channels: new Set(channels) });

    // Keepalive con commento (invisibile al client EventSource)
    const keepalive = setInterval(() => res.write(':ping\n\n'), 15_000);

    req.on('close', () => {
      clearInterval(keepalive);
      this.clients.delete(clientId);
    });
  }

  publish(channel, eventType, data, eventId = null) {
    for (const [, client] of this.clients) {
      if (client.channels.has(channel)) {
        let message = '';
        if (eventId) message += `id: ${eventId}\n`;
        message += `event: ${eventType}\n`;
        message += `data: ${JSON.stringify(data)}\n\n`;
        client.res.write(message);
      }
    }
  }
}
```

### Matrice decisionale: SSE vs WebSocket

| Criterio | SSE | WebSocket | Vincitore |
|----------|-----|-----------|-----------|
| Server → Client unidirezionale | Nativo | Overhead (ignora una direzione) | **SSE** |
| Bidirezionale ad alta frequenza | HTTP POST separato (latenza) | Nativo, stessa connessione | **WebSocket** |
| Riconnessione automatica | Built-in con `Last-Event-ID` | Manuale (exponential backoff) | **SSE** |
| Attraversamento proxy/CDN | Trasparente (è HTTP) | Richiede configurazione specifica | **SSE** |
| Dati binari | Non supportato nativamente | Nativo (opcode 0x2) | **WebSocket** |
| Compressione | gzip/brotli HTTP standard | permessage-deflate (custom) | **SSE** |
| Autenticazione | Header HTTP standard | Limitata (no custom header dal browser) | **SSE** |
| Overhead per evento | ~0 byte (stream aperto) | 2-14 byte (frame header) | Pari |
| Scalabilità orizzontale | Semplice (compatibile con LB standard) | Complessa (sticky sessions, Redis pub/sub) | **SSE** |

### Pattern ibrido SSE + HTTP POST

Per molte applicazioni, la combinazione SSE (server → client) + HTTP POST (client → server) è più semplice da operare rispetto a WebSocket, offrendo prestazioni comparabili.

```javascript
// Pattern ibrido: SSE per ricezione, HTTP POST per invio
// Server
const express = require('express');
const app = express();
app.use(express.json());

const sseServer = new SSEMultiChannelServer();

// Stream SSE per ricezione eventi
app.get('/events', (req, res) => sseServer.handleConnection(req, res));

// HTTP POST per invio messaggi
app.post('/messages', authenticateMiddleware, async (req, res) => {
  const { channel, text } = req.body;

  const message = {
    id: crypto.randomUUID(),
    userId: req.userId,
    text: sanitize(text),
    timestamp: new Date().toISOString(),
  };

  await db.messages.insert(message);

  // Pubblica via SSE a tutti i client iscritti
  sseServer.publish(channel, 'new-message', message, message.id);

  res.json({ status: 'ok', messageId: message.id });
});
```

---

## Strategie di testing WebSocket

### Test unitari — logica di gestione messaggi

I test unitari per WebSocket si concentrano sulla logica di business isolata dal trasporto. I message handler, i validatori e le trasformazioni dei dati sono testabili senza una connessione reale.

```javascript
// message-handler.js — logica pura, testabile senza WebSocket
function processMessage(userId, role, rawMessage) {
  const parsed = JSON.parse(rawMessage);

  if (!parsed.type || typeof parsed.type !== 'string') {
    return { error: 'INVALID_TYPE', code: 1007 };
  }

  if (parsed.type === 'admin:broadcast' && role !== 'admin') {
    return { error: 'FORBIDDEN', code: 1008 };
  }

  if (parsed.type === 'chat:send') {
    if (!parsed.text || parsed.text.length > 4000) {
      return { error: 'INVALID_PAYLOAD', code: 1007 };
    }

    return {
      action: 'broadcast',
      channel: parsed.channel,
      message: {
        id: `msg_${Date.now()}`,
        userId,
        text: parsed.text.trim(),
        timestamp: new Date().toISOString(),
      },
    };
  }

  return { error: 'UNKNOWN_TYPE', code: 1007 };
}

module.exports = { processMessage };
```

```javascript
// message-handler.test.js — test unitari con Vitest / Jest
const { describe, it, expect } = require('vitest');
const { processMessage } = require('./message-handler');

describe('processMessage', () => {
  it('rifiuta messaggi senza tipo', () => {
    const result = processMessage('user1', 'user', '{}');
    expect(result.error).toBe('INVALID_TYPE');
  });

  it('rifiuta admin:broadcast da utente non-admin', () => {
    const msg = JSON.stringify({ type: 'admin:broadcast', text: 'hello' });
    const result = processMessage('user1', 'user', msg);
    expect(result.error).toBe('FORBIDDEN');
  });

  it('processa chat:send correttamente', () => {
    const msg = JSON.stringify({
      type: 'chat:send',
      channel: 'general',
      text: 'Ciao a tutti',
    });
    const result = processMessage('user1', 'user', msg);
    expect(result.action).toBe('broadcast');
    expect(result.message.text).toBe('Ciao a tutti');
    expect(result.message.userId).toBe('user1');
  });

  it('rifiuta messaggi con testo troppo lungo', () => {
    const msg = JSON.stringify({
      type: 'chat:send',
      channel: 'general',
      text: 'x'.repeat(4001),
    });
    const result = processMessage('user1', 'user', msg);
    expect(result.error).toBe('INVALID_PAYLOAD');
  });
});
```

### Test di integrazione — connessione server reale

I test di integrazione verificano il comportamento del server WebSocket con connessioni reali, includendo autenticazione, routing dei messaggi e gestione degli errori.

```javascript
// ws-server.integration.test.js
const { describe, it, expect, beforeAll, afterAll } = require('vitest');
const { WebSocket } = require('ws');
const { createTestServer } = require('./test-helpers');

describe('WebSocket Server Integration', () => {
  let server;
  let serverUrl;

  beforeAll(async () => {
    server = await createTestServer({ port: 0 }); // porta casuale
    serverUrl = `ws://localhost:${server.address().port}/ws`;
  });

  afterAll(async () => {
    await server.close();
  });

  function connectClient(token) {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(`${serverUrl}?token=${token}`);
      ws.on('open', () => resolve(ws));
      ws.on('error', reject);
      setTimeout(() => reject(new Error('Connection timeout')), 5000);
    });
  }

  function waitForMessage(ws, predicate, timeoutMs = 5000) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(
        () => reject(new Error('Message timeout')),
        timeoutMs
      );

      ws.on('message', function handler(data) {
        const msg = JSON.parse(data.toString());
        if (predicate(msg)) {
          clearTimeout(timer);
          ws.off('message', handler);
          resolve(msg);
        }
      });
    });
  }

  it('rifiuta connessioni senza token', async () => {
    const ws = new WebSocket(serverUrl);
    const closeEvent = await new Promise((resolve) => {
      ws.on('close', (code) => resolve(code));
      ws.on('error', () => {}); // prevenire crash
    });
    expect(closeEvent).toBe(1008);
  });

  it('consente broadcast tra client nella stessa room', async () => {
    const client1 = await connectClient('valid-token-user1');
    const client2 = await connectClient('valid-token-user2');

    // Entrambi si iscrivono alla room
    client1.send(JSON.stringify({ type: 'subscribe', channel: 'test-room' }));
    client2.send(JSON.stringify({ type: 'subscribe', channel: 'test-room' }));

    // Breve attesa per la sottoscrizione
    await new Promise((r) => setTimeout(r, 100));

    // Client 1 invia un messaggio
    client1.send(JSON.stringify({
      type: 'chat:send',
      channel: 'test-room',
      text: 'Test message',
    }));

    // Client 2 deve ricevere il messaggio
    const received = await waitForMessage(
      client2,
      (msg) => msg.type === 'chat:message'
    );

    expect(received.message.text).toBe('Test message');

    client1.close();
    client2.close();
  });

  it('applica rate limiting per connessione', async () => {
    const client = await connectClient('valid-token-user3');

    // Inviare messaggi oltre il limite
    for (let i = 0; i < 35; i++) {
      client.send(JSON.stringify({
        type: 'chat:send',
        channel: 'spam-test',
        text: `Message ${i}`,
      }));
    }

    const rateLimitMsg = await waitForMessage(
      client,
      (msg) => msg.type === 'error' && msg.code === 'RATE_LIMITED'
    );

    expect(rateLimitMsg.code).toBe('RATE_LIMITED');
    client.close();
  });
});
```

### Test E2E con Playwright

Playwright consente di testare l'intera catena: interazione utente → WebSocket → aggiornamento UI.

```javascript
// chat-e2e.spec.js — test E2E con Playwright
const { test, expect } = require('@playwright/test');

test.describe('Chat WebSocket E2E', () => {
  test('due utenti possono scambiarsi messaggi in tempo reale', async ({
    browser,
  }) => {
    // Creare due contesti browser separati (due utenti)
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    // Login utente 1
    await page1.goto('/login');
    await page1.fill('[name=email]', 'user1@test.com');
    await page1.fill('[name=password]', 'testpass');
    await page1.click('button[type=submit]');
    await page1.waitForURL('/chat');

    // Login utente 2
    await page2.goto('/login');
    await page2.fill('[name=email]', 'user2@test.com');
    await page2.fill('[name=password]', 'testpass');
    await page2.click('button[type=submit]');
    await page2.waitForURL('/chat');

    // Monitorare WebSocket su page1
    const wsMessages = [];
    page1.on('websocket', (ws) => {
      ws.on('framereceived', (frame) => {
        wsMessages.push(JSON.parse(frame.payload));
      });
    });

    // Utente 2 invia un messaggio
    await page2.fill('[data-testid=message-input]', 'Ciao da utente 2!');
    await page2.click('[data-testid=send-button]');

    // Utente 1 deve vedere il messaggio nell'interfaccia
    await expect(
      page1.locator('[data-testid=message-list]')
    ).toContainText('Ciao da utente 2!', { timeout: 5000 });

    // Verificare che il WebSocket ha ricevuto il frame
    expect(wsMessages.some(m => m.type === 'chat:message')).toBe(true);

    await context1.close();
    await context2.close();
  });

  test('riconnessione automatica dopo interruzione', async ({ page }) => {
    await page.goto('/chat');
    // ... login ...

    // Verificare che la connessione WebSocket è attiva
    const wsConnected = page.locator('[data-testid=connection-status]');
    await expect(wsConnected).toHaveText('Connesso');

    // Simulare interruzione di rete
    await page.context().setOffline(true);
    await expect(wsConnected).toHaveText('Disconnesso', { timeout: 10_000 });

    // Ripristinare la rete
    await page.context().setOffline(false);
    await expect(wsConnected).toHaveText('Connesso', { timeout: 30_000 });
  });
});
```

### Mock WebSocket con Playwright

Playwright supporta il routing delle connessioni WebSocket per test deterministici senza dipendenza dal server reale.

```javascript
// Mock WebSocket con page.routeWebSocket (Playwright 1.48+)
test('mostra notifica quando arriva un messaggio', async ({ page }) => {
  // Intercettare e mockare la connessione WebSocket
  await page.routeWebSocket('wss://api.example.com/ws', (ws) => {
    ws.onMessage((message) => {
      const msg = JSON.parse(message);
      if (msg.type === 'auth') {
        ws.send(JSON.stringify({ type: 'auth_success', userId: 'test-user' }));
      }

      if (msg.type === 'subscribe') {
        // Simulare un messaggio in arrivo dopo 500ms
        setTimeout(() => {
          ws.send(JSON.stringify({
            type: 'chat:message',
            message: {
              id: 'mock-1',
              userId: 'other-user',
              text: 'Messaggio di test',
              timestamp: new Date().toISOString(),
            },
          }));
        }, 500);
      }
    });
  });

  await page.goto('/chat');

  // Verificare che la notifica appare
  await expect(
    page.locator('[data-testid=notification]')
  ).toContainText('Messaggio di test');
});
```

---

## Monitoraggio e observability avanzati

### Structured logging per WebSocket

I log delle connessioni WebSocket devono essere strutturati (JSON) per consentire l'analisi con strumenti come ELK Stack, Loki o CloudWatch Logs Insights.

```javascript
const pino = require('pino');

const logger = pino({
  level: 'info',
  redact: ['token', 'password', '*.token', '*.password'],
  serializers: {
    wsConnection: (conn) => ({
      userId: conn.userId,
      ip: conn.clientIp,
      connectedAt: conn.connectedAt,
      messageCount: conn.messageCount,
      channels: Array.from(conn.channels || []),
    }),
  },
});

// Log strutturati per ogni evento del ciclo di vita
wss.on('connection', (ws, req) => {
  const connId = crypto.randomUUID();

  logger.info({
    event: 'ws.connection.open',
    connId,
    ip: req.headers['x-forwarded-for'] || req.socket.remoteAddress,
    userAgent: req.headers['user-agent'],
    origin: req.headers.origin,
    protocol: ws.protocol,
    totalConnections: wss.clients.size,
  });

  ws.on('close', (code, reason) => {
    logger.info({
      event: 'ws.connection.close',
      connId,
      userId: ws.userId,
      code,
      reason: reason.toString(),
      duration: Date.now() - ws._connectedAt,
      messagesProcessed: ws._messageCount || 0,
    });
  });

  ws.on('error', (error) => {
    logger.error({
      event: 'ws.connection.error',
      connId,
      userId: ws.userId,
      error: error.message,
      stack: error.stack,
    });
  });
});
```

### Dashboard Grafana — query PromQL essenziali

```
# Connessioni attive in tempo reale
ws_connections_active

# Tasso di messaggi al secondo (media su 5 minuti)
rate(ws_messages_total[5m])

# Latenza p99 di elaborazione messaggi
histogram_quantile(0.99, rate(ws_message_latency_seconds_bucket[5m]))

# Tasso di errori di autenticazione
rate(ws_errors_total{type="auth_failure"}[5m])

# Rapporto connessioni rifiutate / totali
rate(ws_connections_rejected_total[5m]) /
  (rate(ws_connections_total[5m]) + rate(ws_connections_rejected_total[5m]))

# Spike di disconnessioni (utile per rilevare problemi di rete)
increase(ws_disconnections_total[1m])
```

### Alerting — soglie raccomandate

```yaml
# alerts.yml — Alertmanager / Grafana Alerting
groups:
  - name: websocket_alerts
    rules:
      - alert: WSHighConnectionRate
        expr: rate(ws_connections_total[1m]) > 500
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Spike di nuove connessioni WebSocket"
          runbook: "https://wiki.internal/runbooks/ws-connection-spike"

      - alert: WSHighErrorRate
        expr: >
          rate(ws_errors_total[5m]) /
          (rate(ws_messages_total{direction="in"}[5m]) + 0.001) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Tasso errori WebSocket > 5%"
          runbook: "https://wiki.internal/runbooks/ws-high-errors"

      - alert: WSHighLatency
        expr: >
          histogram_quantile(0.95,
            rate(ws_message_latency_seconds_bucket[5m])
          ) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latenza p95 WebSocket > 500ms"

      - alert: WSConnectionLeaks
        expr: >
          ws_connections_active > 0.9 *
          ws_connections_max_capacity
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Connessioni WebSocket al 90% della capacità"

      - alert: WSBackpressure
        expr: ws_backpressure_events_total > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Backpressure frequente — client lenti"
```

### Health check per WebSocket

Un health check HTTP tradizionale non verifica la capacità del server di accettare connessioni WebSocket. È necessario un health check dedicato.

```javascript
// Health check che verifica effettivamente la capacità WebSocket
app.get('/health/ws', async (req, res) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    connections: {
      active: wss.clients.size,
      max: MAX_CONNECTIONS,
      utilization: (wss.clients.size / MAX_CONNECTIONS * 100).toFixed(1) + '%',
    },
    memory: {
      heapUsedMB: (process.memoryUsage().heapUsed / 1024 / 1024).toFixed(1),
      rssMB: (process.memoryUsage().rss / 1024 / 1024).toFixed(1),
    },
    eventLoop: {
      lagMs: eventLoopLag.toFixed(1),
    },
    redis: {
      connected: redisPub.status === 'ready',
    },
  };

  // Determinare lo stato complessivo
  if (wss.clients.size >= MAX_CONNECTIONS * 0.95) {
    health.status = 'degraded';
    res.status(503);
  } else if (!redisPub || redisPub.status !== 'ready') {
    health.status = 'degraded';
    res.status(503);
  } else {
    res.status(200);
  }

  res.json(health);
});
```

---

## WebSocket in produzione: configurazione infrastrutturale

### HAProxy — configurazione completa

HAProxy rileva automaticamente l'upgrade WebSocket e commuta in modalità tunnel. La configurazione richiede timeout specifici per le connessioni di lunga durata.

```
# /etc/haproxy/haproxy.cfg — sezione WebSocket

frontend ws_frontend
    bind *:443 ssl crt /etc/ssl/certs/combined.pem alpn h2,http/1.1
    mode http

    # ACL per identificare richieste WebSocket
    acl is_websocket hdr(Upgrade) -i websocket
    acl is_websocket hdr(Connection) -i upgrade

    # Instradare WebSocket al backend dedicato
    use_backend ws_servers if is_websocket
    default_backend http_servers

backend ws_servers
    mode http
    balance source           # sticky sessions basate su IP sorgente
    option httpchk GET /health/ws
    http-check expect status 200

    # Timeout critici per WebSocket
    timeout server  86400s   # 24 ore — connessioni di lunga durata
    timeout tunnel  86400s   # 24 ore — modalità tunnel dopo upgrade
    timeout client  86400s   # 24 ore — lato client
    timeout connect 5s       # timeout connessione al backend

    # Cookie-based sticky sessions (più affidabile di source IP)
    cookie WSSERVERID insert indirect nocache

    server ws1 10.0.1.10:8080 check cookie ws1
    server ws2 10.0.1.11:8080 check cookie ws2
    server ws3 10.0.1.12:8080 check cookie ws3
```

### AWS Application Load Balancer (ALB)

AWS ALB supporta WebSocket nativamente. Rileva l'header `Connection: Upgrade` e mantiene la connessione aperta con il backend.

```hcl
# Terraform — configurazione ALB per WebSocket
resource "aws_lb_target_group" "websocket" {
  name     = "ws-target-group"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  # Stickiness per WebSocket
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400  # 24 ore
    enabled         = true
  }

  health_check {
    path                = "/health/ws"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  # Deregistration delay per graceful shutdown
  deregistration_delay = 300  # 5 minuti per drenare le connessioni
}

resource "aws_lb_listener_rule" "websocket" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.websocket.arn
  }

  condition {
    path_pattern {
      values = ["/ws", "/ws/*"]
    }
  }
}

# CRITICO: aumentare il timeout idle dell'ALB
resource "aws_lb" "main" {
  # ...
  idle_timeout = 3600  # 1 ora (default 60s è troppo breve per WebSocket)
}
```

### Considerazioni su CDN e WebSocket

I CDN tradizionali (CloudFront, Akamai, Fastly) hanno supporto variabile per WebSocket:

| CDN | Supporto WebSocket | Timeout max | Note |
|-----|-------------------|-------------|------|
| Cloudflare | Sì | 100s (free), configurabile (enterprise) | Il piano gratuito limita a 100 secondi di inattività |
| AWS CloudFront | Sì (dal 2018) | 86400s (24h) | Richiede comportamento di cache dedicato per il path WebSocket |
| Fastly | Sì | Configurabile | Supporto nativo, performance eccellente |
| Akamai | Sì | Configurabile | Richiede configurazione specifica nell'edge configuration |

```json
// Cloudflare — esempio di configurazione API per aumentare
// il timeout WebSocket (richiede piano Business o Enterprise)
{
  "websockets": "on",
  "websocket_timeout": 3600
}
```

### Deployment con container — Kubernetes

```yaml
# k8s deployment con supporto WebSocket
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ws-server
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # zero-downtime: mai rimuovere pod prima che il nuovo sia ready
  template:
    spec:
      terminationGracePeriodSeconds: 300  # 5 minuti per il draining
      containers:
        - name: ws-server
          image: registry.example.com/ws-server:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          readinessProbe:
            httpGet:
              path: /health/ws
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health/ws
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 20
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "kill -SIGTERM 1 && sleep 280"]
---
apiVersion: v1
kind: Service
metadata:
  name: ws-service
  annotations:
    # Per Nginx Ingress Controller
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$remote_addr"
spec:
  type: ClusterIP
  ports:
    - port: 8080
  selector:
    app: ws-server
```

---

## Strategie avanzate di error recovery

### Riconnessione con sincronizzazione dello stato

La riconnessione non è sufficiente: il client deve anche sincronizzare lo stato perso durante la disconnessione. Questo richiede un protocollo di reconciliazione.

```javascript
class ResilientWebSocketClient {
  constructor(url, options = {}) {
    this.url = url;
    this.options = options;
    this.lastEventId = null;      // ultimo evento ricevuto
    this.subscriptions = [];       // canali attivi
    this.pendingAcks = new Map();  // messaggi non confermati
    this.connectionAttempt = 0;
    this.state = 'disconnected';
  }

  connect() {
    this.state = 'connecting';
    const reconnectParams = this.lastEventId
      ? `?lastEventId=${this.lastEventId}`
      : '';

    this.ws = new WebSocket(`${this.url}${reconnectParams}`);

    this.ws.addEventListener('open', () => {
      this.state = 'connected';
      this.connectionAttempt = 0;

      // Fase 1: Autenticazione
      this.ws.send(JSON.stringify({
        type: 'auth',
        token: this.options.getToken(),
      }));
    });

    this.ws.addEventListener('message', (event) => {
      const msg = JSON.parse(event.data);

      // Tracciare l'ultimo evento ricevuto
      if (msg.eventId) {
        this.lastEventId = msg.eventId;
      }

      // Gestire ACK dal server
      if (msg.type === 'ack' && this.pendingAcks.has(msg.requestId)) {
        const { resolve } = this.pendingAcks.get(msg.requestId);
        this.pendingAcks.delete(msg.requestId);
        resolve(msg);
      }

      // Dopo l'autenticazione, ri-iscriversi ai canali
      if (msg.type === 'auth_success') {
        this.state = 'ready';
        this.resubscribeAll();
        this.retryPendingMessages();
      }

      // Replay di messaggi persi dal server
      if (msg.type === 'replay_batch') {
        for (const replayedMsg of msg.messages) {
          this.options.onMessage?.(replayedMsg);
        }
        console.log(`Replayed ${msg.messages.length} missed messages`);
      }

      this.options.onMessage?.(msg);
    });

    this.ws.addEventListener('close', (event) => {
      this.state = 'disconnected';

      // Non riconnettersi per chiusure intenzionali
      if (event.code === 1000 || event.code === 1008) return;

      this.scheduleReconnect();
    });
  }

  resubscribeAll() {
    for (const channel of this.subscriptions) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        channel,
      }));
    }
  }

  retryPendingMessages() {
    for (const [requestId, { message }] of this.pendingAcks) {
      this.ws.send(JSON.stringify({ ...message, requestId }));
    }
  }

  // Invio con garanzia at-least-once
  sendReliable(message) {
    return new Promise((resolve, reject) => {
      const requestId = crypto.randomUUID();
      const timeout = setTimeout(() => {
        this.pendingAcks.delete(requestId);
        reject(new Error('Message delivery timeout'));
      }, 10_000);

      this.pendingAcks.set(requestId, {
        resolve: (ack) => {
          clearTimeout(timeout);
          resolve(ack);
        },
        message,
        timestamp: Date.now(),
      });

      if (this.state === 'ready') {
        this.ws.send(JSON.stringify({ ...message, requestId }));
      }
      // Se non connesso, verrà re-inviato in retryPendingMessages()
    });
  }

  scheduleReconnect() {
    const delay = Math.min(
      1000 * Math.pow(2, this.connectionAttempt),
      30_000
    );
    const jitter = delay * 0.3 * (Math.random() * 2 - 1);
    this.connectionAttempt++;

    setTimeout(() => this.connect(), Math.max(0, delay + jitter));
  }
}
```

### Circuit breaker per WebSocket

Quando il server è continuamente irraggiungibile, il circuit breaker evita tentativi di riconnessione inutili che consumano risorse e generano log rumorosi.

```javascript
class WebSocketCircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeoutMs = options.resetTimeoutMs || 60_000;
    this.halfOpenMaxAttempts = options.halfOpenMaxAttempts || 1;

    this.state = 'closed';     // closed = operativo
    this.failureCount = 0;
    this.lastFailureTime = 0;
    this.halfOpenAttempts = 0;
  }

  canConnect() {
    switch (this.state) {
      case 'closed':
        return true;
      case 'open':
        // Verificare se è il momento di provare half-open
        if (Date.now() - this.lastFailureTime > this.resetTimeoutMs) {
          this.state = 'half-open';
          this.halfOpenAttempts = 0;
          return true;
        }
        return false;
      case 'half-open':
        return this.halfOpenAttempts < this.halfOpenMaxAttempts;
      default:
        return false;
    }
  }

  recordSuccess() {
    this.failureCount = 0;
    this.state = 'closed';
  }

  recordFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === 'half-open') {
      this.state = 'open';
      this.halfOpenAttempts++;
    } else if (this.failureCount >= this.failureThreshold) {
      this.state = 'open';
      console.warn(
        `Circuit breaker OPEN after ${this.failureCount} failures. ` +
        `Will retry in ${this.resetTimeoutMs / 1000}s`
      );
    }
  }

  getState() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      lastFailure: this.lastFailureTime
        ? new Date(this.lastFailureTime).toISOString()
        : null,
    };
  }
}

// Integrazione con il client WebSocket
const breaker = new WebSocketCircuitBreaker();

function attemptConnect() {
  if (!breaker.canConnect()) {
    console.log(`Circuit breaker ${breaker.state} — skip`);
    setTimeout(attemptConnect, breaker.resetTimeoutMs);
    return;
  }

  const ws = new WebSocket(url);
  ws.addEventListener('open', () => breaker.recordSuccess());
  ws.addEventListener('error', () => breaker.recordFailure());
  ws.addEventListener('close', (event) => {
    if (!event.wasClean) {
      breaker.recordFailure();
      attemptConnect();
    }
  });
}
```

---

## Esercizi

1. **Lab — server WebSocket sicuro.** Implementare un server `ws` con: autenticazione JWT su handshake, validazione origin, rate limiting per connessione (max 30 msg/min), heartbeat ping/pong. Testare con wscat.

2. **Lab — chat room con presenza.** Implementare un sistema di chat con room, join/leave, indicatore "sta scrivendo", lista utenti online. Usare `ws` o Socket.IO.

3. **Lab — CSWSH.** Creare un server WebSocket vulnerabile a CSWSH (autenticazione solo via cookie, nessun controllo origin). Creare una pagina su un dominio diverso che sfrutta la vulnerabilità. Poi implementare la difesa.

4. **Lab — riconnessione con replay.** Implementare un client con exponential backoff + jitter, message queue per messaggi durante la disconnessione, e replay dei messaggi persi via sequencing server-side.

5. **Lab — scaling con Redis.** Creare due istanze server WebSocket dietro un load balancer Nginx. Usare Redis pub/sub per garantire che un messaggio inviato a un server raggiunga i client connessi all'altro.

6. **Lab — load test.** Scrivere un test di carico con k6 o con script custom che apre 1000 connessioni simultanee, invia messaggi a intervalli regolari, e misura latenza p50/p95/p99.

7. **Lab — dashboard metriche.** Creare un endpoint `/metrics` che espone connessioni attive, messaggi al secondo, latenza, errori. Visualizzare con un client HTML + Chart.js che si aggiorna via WebSocket.

8. **Stretch — rate limiter distribuito.** Implementare un rate limiter basato su Redis sorted set che funziona correttamente in un deployment multi-server. Testare con connessioni distribuite su server diversi.

---

## FAQ

### 1. WebSocket è sicuro di default?

No. Il protocollo `ws://` trasmette dati in chiaro. In produzione usare sempre `wss://` (WebSocket over TLS). Inoltre, WebSocket non ha protezioni CORS native — il server deve validare esplicitamente l'header `Origin`.

### 2. Posso inviare header HTTP custom nell'handshake WebSocket dal browser?

No. L'API `new WebSocket(url, protocols)` del browser non consente header custom. Per autenticazione, le opzioni sono: query parameter, cookie (automatici), sub-protocollo, o autenticazione nel primo messaggio. Librerie non-browser (come `ws` in Node.js) possono inviare header arbitrari.

### 3. Qual è la differenza tra `ws.close()` e `ws.terminate()`?

`ws.close()` invia un frame di chiusura e attende la risposta dell'altra parte (chiusura pulita). `ws.terminate()` chiude la connessione TCP immediatamente senza frame di chiusura (chiusura brusca). Usare `terminate()` per connessioni zombie o quando `close()` non riceve risposta entro un timeout.

### 4. Quante connessioni WebSocket può gestire un singolo server Node.js?

Dipende dalla complessità della logica per messaggio. Con messaggi semplici e heartbeat, 50.000-100.000 connessioni per processo sono raggiungibili. Il collo di bottiglia è generalmente la memoria (1-10 KB per connessione) e i file descriptor del sistema operativo.

### 5. Devo usare Socket.IO o WebSocket puro (`ws`)?

**Socket.IO** se serve: riconnessione automatica, room, fallback su polling, broadcasting semplice. **ws puro** se serve: massima performance, controllo completo sul protocollo, nessun overhead. Socket.IO non è interoperabile con client WebSocket standard — richiede il client Socket.IO.

### 6. Come gestisco l'autenticazione per connessioni WebSocket di lunga durata?

Usare JWT con scadenza breve per l'handshake. Implementare un meccanismo di refresh: il server avvisa il client quando il token sta per scadere, il client invia un nuovo token ottenuto via refresh HTTP. Se il token scade senza rinnovo, il server chiude la connessione con codice 1008.

### 7. WebSocket funziona con HTTP/2?

RFC 8441 definisce WebSocket over HTTP/2 ("bootstrapping WebSocket with HTTP/2"), che consente di stabilire connessioni WebSocket su stream HTTP/2, beneficiando del multiplexing. Il supporto nei browser è ancora limitato. In pratica, la maggior parte delle implementazioni usa ancora l'upgrade HTTP/1.1.

### 8. Come prevengo gli attacchi DDoS via WebSocket?

Combinare: limite connessioni per IP, rate limiting per connessione, autenticazione obbligatoria sull'handshake, dimensione massima messaggi, timeout per inattività, e monitoraggio delle anomalie. Un WAF (Web Application Firewall) con supporto WebSocket (es. Cloudflare, AWS WAF) aggiunge protezione a livello infrastrutturale.

### 9. Posso usare WebSocket con serverless (AWS Lambda, Vercel Functions)?

AWS API Gateway supporta WebSocket API con Lambda come backend. Le funzioni Lambda sono invocate per ogni evento ($connect, $disconnect, messaggio). Il routing e la gestione dello stato sono diversi dal modello server tradizionale. Vercel e molti altri provider serverless non supportano nativamente WebSocket persistenti.

### 10. Come gestisco il fallback quando WebSocket non è disponibile?

Usare Socket.IO (che gestisce il fallback automaticamente) oppure implementare manualmente: tentare WebSocket, in caso di fallimento ricadere su SSE (Server-Sent Events) per la ricezione + HTTP POST per l'invio, e come ultima risorsa HTTP long-polling.

### 11. Perché il browser chiude la connessione WebSocket quando l'utente cambia tab?

I browser moderni possono sospendere i tab in background per risparmiare risorse (Tab Freezing). Le connessioni WebSocket in tab congelati non ricevono ping/pong, causando timeout sul server. Soluzione: implementare riconnessione automatica quando il tab torna attivo usando l'evento `visibilitychange`.

```javascript
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    if (ws.readyState !== WebSocket.OPEN) {
      reconnect();
    }
  }
});
```

### 12. Come debuggo i messaggi WebSocket nel browser?

Chrome DevTools: tab Network → filtro "WS" → selezionare la connessione → tab "Messages" mostra tutti i frame inviati e ricevuti con timestamp. Firefox ha funzionalità analoghe. Per test automatizzati, usare Playwright con `page.on('websocket')`.

### 13. Qual è il limite di dimensione dei messaggi WebSocket?

Il protocollo supporta messaggi fino a 2^63 byte (teoricamente). In pratica, il server dovrebbe imporre un limite molto più basso (es. 1 MB) tramite la configurazione `maxPayload` per prevenire abusi. Per trasferire file grandi, usare chunking o un upload HTTP separato con notifica via WebSocket.

### 14. Come implemento la crittografia end-to-end su WebSocket?

WSS (TLS) protegge il trasporto client-server, ma il server può leggere i messaggi. Per E2E encryption (server non può leggere), usare una libreria di crittografia lato client (es. libsodium-wrappers) per cifrare il payload prima di inviarlo e decifrare dopo la ricezione. Lo scambio di chiavi avviene fuori banda o tramite un protocollo come X3DH (Signal Protocol).

### 15. WebSocket è adatto per il gaming multiplayer?

Sì per giochi turn-based, giochi casual, e giochi dove la latenza di 10-50ms è accettabile. Per giochi FPS competitivi o simulazioni real-time dove serve latenza sotto i 5ms e pacchetti UDP, WebSocket (che usa TCP) non è ottimale — considerare WebRTC Data Channel (che supporta UDP-like unreliable delivery) o WebTransport.

### 16. Come gestisco il graceful shutdown del server WebSocket?

```javascript
process.on('SIGTERM', () => {
  console.log('SIGTERM ricevuto. Graceful shutdown...');

  // 1. Smettere di accettare nuove connessioni
  wss.close();

  // 2. Notificare i client connessi
  for (const ws of wss.clients) {
    ws.close(1012, 'Server restarting');
  }

  // 3. Attendere che le connessioni si chiudano (con timeout)
  setTimeout(() => {
    // Terminare connessioni rimaste
    for (const ws of wss.clients) {
      ws.terminate();
    }
    server.close(() => {
      process.exit(0);
    });
  }, 10_000); // 10 secondi di grazia
});
```

---

## Checklist di sicurezza per il deployment WebSocket

### Trasporto

- [ ] WSS (TLS) obbligatorio — mai `ws://` in produzione
- [ ] TLS 1.2 minimo, preferire TLS 1.3
- [ ] Certificati validi con rinnovo automatico (Let's Encrypt)
- [ ] HSTS header configurato
- [ ] Cipher suite aggiornate e sicure

### Autenticazione

- [ ] Token validato PRIMA di accettare l'upgrade (non dopo la connessione)
- [ ] Token a breve scadenza per l'handshake se nel query parameter
- [ ] Meccanismo di rinnovo token per connessioni di lunga durata
- [ ] Sessioni invalidate immediatamente in caso di logout/cambio password
- [ ] Timeout per connessioni non autenticate (max 5 secondi)

### Autorizzazione

- [ ] Verifica permessi per ogni operazione, non solo alla connessione
- [ ] Identità dell'utente derivata dal server, mai dal messaggio client
- [ ] Principio del minimo privilegio per accesso a canali/room
- [ ] Default deny per canali non esplicitamente permessi

### Validazione

- [ ] Ogni messaggio validato contro uno schema (Zod, Joi, ajv)
- [ ] Sanitizzazione HTML per contenuto user-generated
- [ ] Limite profondità JSON (max 5 livelli)
- [ ] Limite lunghezza stringhe
- [ ] Limite dimensione array

### Rate limiting

- [ ] Limite messaggi per connessione (es. 30/min)
- [ ] Limite burst (es. 10 messaggi/secondo)
- [ ] Limite connessioni per IP (es. 10)
- [ ] Limite dimensione payload (es. 64 KB)
- [ ] Rate limit per tipo di messaggio (operazioni costose più restrittive)
- [ ] Rate limiting distribuito (Redis) in deployment multi-server

### DoS prevention

- [ ] maxPayload configurato nel server WebSocket
- [ ] Timeout per connessioni inattive (es. 5 minuti)
- [ ] Heartbeat ping/pong per rilevare connessioni zombie
- [ ] Limite totale connessioni per server
- [ ] Protezione contro frame di continuazione infiniti

### Origin e CSWSH

- [ ] Validazione rigorosa dell'header Origin sull'handshake
- [ ] Whitelist di origin consentiti (non regex troppo permissive)
- [ ] Token CSRF aggiuntivo per connessioni autenticate via cookie
- [ ] Logging dei tentativi di connessione da origin non consentiti

### Logging e monitoraggio

- [ ] Log di connessioni e disconnessioni con IP e userId
- [ ] Log di errori di autenticazione e autorizzazione
- [ ] Metriche: connessioni attive, messaggi/secondo, latenza, errori
- [ ] Alert su anomalie (spike di connessioni, flood di messaggi, errori)
- [ ] Token/credenziali MAI nei log
- [ ] Retention policy per i log

### Infrastruttura

- [ ] Reverse proxy (Nginx/HAProxy) configurato per WebSocket upgrade
- [ ] Timeout proxy sufficientemente lunghi (> 60s)
- [ ] ulimit / file descriptor adeguati al numero di connessioni attese
- [ ] Graceful shutdown implementato (SIGTERM handler)
- [ ] Health check che verifica la capacità di accettare nuove connessioni

---

## Letture

- RFC 6455 — The WebSocket Protocol. https://datatracker.ietf.org/doc/html/rfc6455
- RFC 8441 — Bootstrapping WebSockets with HTTP/2. https://datatracker.ietf.org/doc/html/rfc8441
- OWASP Testing Guide — Testing WebSockets. https://owasp.org/www-project-web-security-testing-guide/
- OWASP WebSocket Security Cheat Sheet. https://cheatsheetseries.owasp.org/
- Christian Schneider — Cross-Site WebSocket Hijacking. https://christian-schneider.net/CrossSiteWebSocketHijacking.html
- ws — Node.js WebSocket library. https://github.com/websockets/ws
- Socket.IO documentation. https://socket.io/docs/v4/
- k6 WebSocket testing. https://grafana.com/docs/k6/latest/javascript-api/k6-ws/

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [14 — Sicurezza Web](14-sicurezza-web.md) | TLS, CORS, CSRF e header di sicurezza per l'handshake HTTP |
| [13 — Autenticazione](13-autenticazione-autorizzazione.md) | JWT e token-based auth per connessioni WebSocket |
| [10 — Node.js](10-nodejs.md) | Runtime server, libreria `ws`, e gestione connessioni persistenti |
| [22 — Rate Limiting](22-rate-limiting-edge.md) | Rate limiting per connessione e protezione DDoS su WebSocket |
| [12 — Database Web](12-database-web.md) | Redis pub/sub per scaling orizzontale di WebSocket multi-nodo |
| [15 — Testing Web](15-testing-web.md) | Test E2E e load testing di connessioni WebSocket con k6/Playwright |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **WS / WSS** | WebSocket / WebSocket Secure (over TLS). |
| **Handshake** | Processo di upgrade da HTTP a WebSocket. Inizia con una richiesta HTTP 101 Switching Protocols. |
| **Frame** | Unità minima di dati nel protocollo WebSocket. Contiene opcode, payload e flag di mascheramento. |
| **Opcode** | Codice a 4 bit che identifica il tipo di frame (text, binary, ping, pong, close, continuation). |
| **Close code** | Codice numerico (1000-4999) che indica il motivo della chiusura della connessione. |
| **Heartbeat** | Meccanismo ping/pong periodico per verificare che la connessione sia attiva. |
| **Masking** | XOR del payload con una chiave a 32 bit. Obbligatorio per frame client→server per prevenire cache poisoning sui proxy. |
| **Origin** | Header HTTP inviato dal browser durante l'handshake. Il server deve validarlo per prevenire CSWSH. |
| **CSWSH** | Cross-Site WebSocket Hijacking. Attacco in cui un sito malevolo apre una connessione WebSocket usando i cookie della vittima. |
| **SSE** | Server-Sent Events. Alternativa unidirezionale (server→client) basata su HTTP con riconnessione automatica. |
| **Sticky session** | Tecnica di load balancing che instrada un client sempre allo stesso server backend. |
| **Pub/Sub** | Pattern publish-subscribe. I client si iscrivono a canali e ricevono messaggi pubblicati su quei canali. |
| **Room** | Gruppo logico di connessioni WebSocket. Un messaggio inviato a una room raggiunge tutti i membri. |
| **Namespace** | In Socket.IO, un canale di comunicazione separato sulla stessa connessione fisica. Consente multiplexing. |
| **Backoff esponenziale** | Strategia di riconnessione in cui il ritardo raddoppia a ogni tentativo fallito (1s, 2s, 4s, 8s, ...). |
| **Jitter** | Variazione casuale aggiunta al delay di riconnessione per evitare che tutti i client si riconnettano simultaneamente (thundering herd). |
| **Half-open connection** | Connessione TCP in cui una delle parti è caduta senza inviare un frame di chiusura. Rilevabile via heartbeat. |
| **permessage-deflate** | Estensione WebSocket per la compressione dei messaggi usando zlib. Riduce il traffico ma aumenta l'uso di CPU e memoria. |
| **Full-duplex** | Comunicazione simultanea in entrambe le direzioni su un singolo canale. |
| **Operational Transform (OT)** | Algoritmo per la risoluzione di conflitti in editing collaborativo real-time. |
| **CRDT** | Conflict-free Replicated Data Type. Struttura dati che si replica automaticamente senza conflitti. Alternative a OT per editing collaborativo. |
| **WebTransport** | Protocollo emergente basato su HTTP/3 e QUIC che supporta stream bidirezionali e datagrammi (UDP-like). Potenziale successore di WebSocket per casi d'uso a bassa latenza. |
