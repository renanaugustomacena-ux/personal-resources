---
corso: "Automazioni e Flussi di Lavoro"
fase: "5 — Pattern Avanzati"
modulo: 15
titolo: "Sicurezza Webhook — Verifica HMAC, Replay Protection, Idempotency"
versione: "Stripe webhook v2, GitHub X-Hub-Signature-256, Square, Slack"
livello: "competent → proficient"
prerequisiti:
  - "Modulo 04"
  - "HMAC (RFC 2104)"
  - "HTTP request bytes parsing"
obiettivi:
  - "Implementare verifica HMAC-SHA256 lato ricevitore con constant-time compare"
  - "Proteggere endpoint webhook da replay attack con timestamp e nonce"
  - "Gestire idempotency key per deduplicazione richieste duplicate"
  - "Applicare il pattern Receive-Verify-Enqueue per elaborazione asincrona sicura"
  - "Configurare signature verification per provider reali (Stripe, GitHub, Slack, Square)"
tag: [webhook, hmac, sicurezza, replay-protection, idempotency, firma-digitale, api-security]
---

# Sicurezza Webhook — Verifica HMAC, Replay Protection, Idempotency

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 4 — Pattern di affidabilita · Modulo 15
> **Prerequisiti:** Modulo 04; HMAC concept (RFC 2104); HTTP request bytes parsing.
> **Obiettivi:** verifica HMAC-SHA256 lato ricevitore con constant-time compare; replay protection con timestamp + nonce; idempotency key handling.
> **Tempo:** lettura 60 min · lab 240 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** Stripe webhook signing v2, Square notification_url, GitHub webhook X-Hub-Signature-256.

## Idee guida

1. **HMAC verify e mandatory; secret in env, mai in code.** Senza HMAC, qualunque chi conosce l'URL puo iniettare eventi falsi.
2. **Constant-time compare per evitare timing attack.** Python: `hmac.compare_digest`, mai `==`.
3. **Replay protection: timestamp + nonce.** Se timestamp > 5 min in passato, reject. Nonce visto = duplicate.
4. **Idempotency key e responsabilita del ricevitore, non del sender.** Anche se sender invia stesso webhook 3 volte, il ricevitore deve elaborare 1 sola volta.
5. **Receive-Verify-Enqueue pattern.** Endpoint webhook fa solo: verify + enqueue. Processing async fuori dal critical path.

---

## Indice

- [Panoramica](#panoramica)
- [Threat Model dei Webhook](#threat-model-dei-webhook)
- [HMAC Signature Verification](#hmac-signature-verification)
- [Implementazione Python](#implementazione-python)
- [Implementazione Node.js](#implementazione-nodejs)
- [Implementazione PHP](#implementazione-php)
- [Verifica Webhook GitHub](#verifica-webhook-github)
- [Verifica Webhook Stripe](#verifica-webhook-stripe)
- [Verifica Webhook Slack](#verifica-webhook-slack)
- [Verifica Webhook Shopify](#verifica-webhook-shopify)
- [Verifica Webhook Square](#verifica-webhook-square)
- [mTLS come Alternativa per B2B Critico](#mtls-come-alternativa-per-b2b-critico)
- [Replay Attack Prevention](#replay-attack-prevention)
- [Idempotency Keys](#idempotency-keys)
- [Retry Semantics: At-Least-Once + Idempotency](#retry-semantics-at-least-once--idempotency)
- [Webhook in n8n / Make / Zapier](#webhook-in-n8n--make--zapier)
- [TLS, IP Allowlist, Headers Sicurezza](#tls-ip-allowlist-headers-sicurezza)
- [Pattern Produzione: Receive-Verify-Enqueue-Process](#pattern-produzione-receive-verify-enqueue-process)
- [Monitoring e Alerting](#monitoring-e-alerting)
- [Casi d'Uso Reali Italiani](#casi-duso-reali-italiani)
- [Checklist Sicurezza Webhook](#checklist-sicurezza-webhook)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Un webhook è un endpoint HTTP che un servizio chiama per notificare un evento al consumer. Diversamente dalle API "pull" classiche (il consumer interroga il provider), nel modello webhook è il provider a contattare il consumer. Questa inversione implica che il consumer espone un URL pubblico raggiungibile dall'esterno — e quindi diventa un potenziale bersaglio.

La regola di sopravvivenza è una sola: **non accettare mai un payload non verificato**. Un webhook senza verifica è un'API pubblica scrivibile da chiunque. Se il payload provoca side effect (creazione di ordini, modifica di stato pagamento, invio di email, attivazione di workflow), l'attaccante che indovina l'URL può manipolare il sistema. Casi reali documentati hanno portato a frodi finanziarie, attivazione di rimborsi non dovuti, esfiltrazione di dati clienti.

Questo documento copre le tre difese fondamentali da combinare sempre: verifica della firma HMAC sul body raw, protezione contro replay attack tramite timestamp + nonce store, e idempotency lato consumer per gestire correttamente i retry. Aggiunge il dettaglio dei meccanismi specifici dei principali provider (GitHub, Stripe, Slack, Shopify, Square), un'analisi delle limitazioni dei platform no-code (n8n, Make, Zapier) nella verifica HMAC, e un pattern di riferimento per produzione. Tutti gli esempi sono runnable in Python e Node.js, con varianti curl per test rapidi.

---

## Threat Model dei Webhook

Prima di scegliere le difese, serve modellare le minacce. Per un endpoint webhook esposto pubblicamente le minacce concrete sono:

### 1. Spoofing

Un attaccante invia POST al nostro endpoint fingendosi il provider legittimo. Se l'unica "autenticazione" è "il payload assomiglia a quello di Stripe", chiunque conosca lo schema può forgiare richieste. Difesa: HMAC signature verification.

### 2. Replay Attack

L'attaccante intercetta un webhook legittimo (sniffing su rete non sicura, leak da log) e lo reinvia 100 volte sperando di triggerare 100 esecuzioni della logica downstream. La firma HMAC è valida (perché il payload è autentico) ma il timing è anomalo. Difesa: timestamp window + nonce store.

### 3. Man-in-the-Middle (MITM)

L'attaccante intercetta il traffico tra provider e consumer e modifica il payload in transito. Difesa: TLS 1.3 obbligatorio, certificate validation, eventualmente mTLS per B2B critico.

### 4. Payload Tampering

Variante del MITM: l'attaccante riesce a modificare alcuni byte del payload prima che arrivi. La firma HMAC calcolata sul body originale non corrisponde più al body manipolato. Difesa: HMAC su raw body bytes (non su JSON re-serializzato).

### 5. Timing Attack

Quando si confronta una firma calcolata vs ricevuta con `==` standard, il tempo di confronto può rivelare quanti byte iniziali sono uguali. Su molte richieste, un attaccante può inferire byte per byte la firma corretta. Difesa: confronto a tempo costante (`hmac.compare_digest` in Python, `crypto.timingSafeEqual` in Node.js).

### 6. URL Enumeration

Se l'URL del webhook è prevedibile (es. `/webhook/stripe`), un attaccante può tentare richieste cieche. Difesa: URL con segreto random nell'path (es. `/webhook/stripe/9f3b8c1a-...`) come "shared secret" debole, da combinare comunque con HMAC.

### 7. Denial of Service

Flood di richieste verso l'endpoint, anche solo per consumare risorse o causare costi. Difesa: rate limiting, IP allowlist quando disponibile, WAF.

### 8. Information Disclosure

Risposte di errore troppo verbose rivelano se l'HMAC è errato vs se il payload è malformato vs se l'utente non esiste. Difesa: risposte uniformi, log dettagliati solo lato server.

---

## HMAC Signature Verification

HMAC (Hash-based Message Authentication Code, RFC 2104) è il meccanismo standard per autenticare l'integrità e l'origine di un messaggio usando una chiave segreta condivisa. Il provider calcola `signature = HMAC(secret, body)` e include la firma in un header. Il consumer ricalcola la firma sul body ricevuto e la confronta con quella nell'header.

### Perché HMAC e non HASH puro

Un hash semplice (SHA-256 sul payload) non basta: chiunque può calcolarlo, perché non c'è segreto. HMAC introduce una chiave segreta condivisa che solo provider e consumer conoscono. Senza la chiave, l'attaccante non può generare una firma valida.

### Algoritmi

Lo standard de facto è **HMAC-SHA256**. Si trova ancora HMAC-SHA1 in sistemi legacy (es. vecchi webhook Slack), ma SHA-1 è considerato debole — preferire SHA-256 ovunque possibile. SHA-512 è valido ma raramente usato per webhook.

### Body Raw, Non JSON Parsato

Errore frequentissimo: il framework web parsa automaticamente il body come JSON, e poi si tenta di calcolare HMAC sul JSON re-serializzato. La re-serializzazione cambia spaziatura, ordine chiavi, escape — e quindi cambia il digest. **HMAC va sempre calcolato sui byte raw del body, prima di qualsiasi parsing**.

In Express.js (Node.js) questo richiede di disabilitare il body parser di default su quella route e usare `express.raw({ type: '*/*' })`. In FastAPI (Python) richiede di leggere `await request.body()` invece di usare il parser Pydantic. Vedi sezioni dedicate per gli esempi.

### Confronto a Tempo Costante

Confrontare due stringhe con `==` o `===` rivela il tempo che impiega: l'operazione termina al primo byte diverso. Un attaccante che misura migliaia di tentativi può inferire byte per byte. Le librerie crypto offrono confronti a tempo costante:

- Python: `hmac.compare_digest(a, b)`
- Node.js: `crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b))`
- PHP: `hash_equals($a, $b)`
- Go: `hmac.Equal(a, b)`

---

## Implementazione Python

Esempio completo con Flask, body raw, HMAC-SHA256, confronto sicuro.

```python
import hmac
import hashlib
import os
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"].encode("utf-8")

def verify_signature(raw_body: bytes, received_signature: str) -> bool:
    """Verifica HMAC-SHA256 a tempo costante.

    received_signature: stringa hex come arriva nell'header
    """
    expected = hmac.new(WEBHOOK_SECRET, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received_signature)

@app.route("/webhook", methods=["POST"])
def webhook():
    raw_body = request.get_data()  # bytes raw, prima del parsing
    sig_header = request.headers.get("X-Signature", "")

    # Header tipicamente nel formato "sha256=<hex>"
    if not sig_header.startswith("sha256="):
        abort(400, "Signature header malformato")
    received_sig = sig_header.split("=", 1)[1]

    if not verify_signature(raw_body, received_sig):
        abort(401, "Firma non valida")

    # Solo ora è sicuro parsare e processare
    payload = request.get_json(force=True, silent=False)
    # ... business logic ...

    return "", 204
```

Note critiche:

- `request.get_data()` restituisce bytes raw. Non usare `request.json` o `request.form` prima della verifica.
- `WEBHOOK_SECRET` letto da env variable, mai hardcoded.
- Risposta 401 generica: non rivelare dettagli sul perché la firma è invalida.
- Status 204 No Content per success: provider non si aspettano body.

### Variante FastAPI

```python
from fastapi import FastAPI, Request, HTTPException
import hmac, hashlib, os

app = FastAPI()
SECRET = os.environ["WEBHOOK_SECRET"].encode()

@app.post("/webhook")
async def webhook(request: Request):
    raw = await request.body()
    sig = request.headers.get("x-signature", "").removeprefix("sha256=")
    expected = hmac.new(SECRET, raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=401, detail="invalid signature")
    # ... process ...
    return {"status": "ok"}
```

---

## Implementazione Node.js

Esempio Express con body raw esplicito.

```javascript
const express = require('express');
const crypto = require('crypto');

const app = express();
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET;

// CRUCIALE: body raw, niente JSON parser su questa route
app.post(
  '/webhook',
  express.raw({ type: '*/*' }),
  (req, res) => {
    const sigHeader = req.header('X-Signature') || '';
    const received = sigHeader.startsWith('sha256=')
      ? sigHeader.slice('sha256='.length)
      : sigHeader;

    const expected = crypto
      .createHmac('sha256', WEBHOOK_SECRET)
      .update(req.body) // req.body qui è un Buffer raw
      .digest('hex');

    const a = Buffer.from(expected, 'hex');
    const b = Buffer.from(received, 'hex');

    if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
      return res.status(401).end();
    }

    // Solo ora si può parsare
    let payload;
    try {
      payload = JSON.parse(req.body.toString('utf8'));
    } catch (e) {
      return res.status(400).end();
    }

    // ... business logic ...
    res.status(204).end();
  }
);

app.listen(3000);
```

Note:

- `express.raw({ type: '*/*' })` applicato solo alla route webhook. Le altre route possono usare `express.json()` normalmente.
- `crypto.timingSafeEqual` richiede Buffer della stessa lunghezza, altrimenti throw. Controllare lunghezza prima.
- `req.body` qui è un `Buffer`, non una stringa: passa direttamente a `update()`.

---

## Implementazione PHP

```php
<?php
$secret = getenv('WEBHOOK_SECRET');
$rawBody = file_get_contents('php://input');
$sigHeader = $_SERVER['HTTP_X_SIGNATURE'] ?? '';

$received = str_starts_with($sigHeader, 'sha256=')
    ? substr($sigHeader, 7)
    : $sigHeader;

$expected = hash_hmac('sha256', $rawBody, $secret);

if (!hash_equals($expected, $received)) {
    http_response_code(401);
    exit;
}

$payload = json_decode($rawBody, true);
if ($payload === null) {
    http_response_code(400);
    exit;
}

// ... business logic ...

http_response_code(204);
```

`hash_equals` è il confronto a tempo costante di PHP. `php://input` legge il body raw prima del parsing automatico.

---

## Verifica Webhook GitHub

GitHub firma i webhook con HMAC-SHA256 e include la firma nell'header `X-Hub-Signature-256` (formato `sha256=<hex>`). Esiste anche `X-Hub-Signature` con SHA-1 per retro-compatibilità — **non usarlo, è deprecato**.

Il segreto si configura nelle webhook settings del repo (Settings → Webhooks → Add webhook → Secret).

```python
import hmac, hashlib

def verify_github(raw_body: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header.startswith("sha256="):
        return False
    received = signature_header[len("sha256="):]
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)
```

Test con curl:

```bash
PAYLOAD='{"action":"opened","number":42}'
SECRET="my-shared-secret"
SIG=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')
curl -X POST http://localhost:3000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$SIG" \
  -d "$PAYLOAD"
```

GitHub fornisce anche header utili: `X-GitHub-Event` (tipo evento), `X-GitHub-Delivery` (UUID univoco — usabile come idempotency key naturale), `X-GitHub-Hook-ID`.

---

## Verifica Webhook Stripe

Stripe usa uno schema più sofisticato: include un timestamp nell'header per prevenire replay attack, e firma `timestamp + body` (non solo body).

Header: `Stripe-Signature: t=<timestamp>,v1=<signature>,v0=<deprecato>`

Algoritmo:

1. Estrarre `t` e `v1` dall'header.
2. Costruire `signed_payload = t + "." + raw_body`.
3. Calcolare `expected = HMAC-SHA256(secret, signed_payload)`.
4. Confronto a tempo costante con `v1`.
5. Verificare che `|now - t| < 300` secondi (5 minuti), per prevenire replay con webhook vecchi.

```python
import hmac, hashlib, time

STRIPE_SECRET = b"whsec_..."  # signing secret di Stripe (non l'API key)

def verify_stripe(raw_body: bytes, sig_header: str, tolerance: int = 300) -> bool:
    items = dict(item.split("=", 1) for item in sig_header.split(","))
    timestamp = items.get("t")
    received = items.get("v1")
    if not timestamp or not received:
        return False

    # Tolerance window
    if abs(time.time() - int(timestamp)) > tolerance:
        return False

    signed_payload = f"{timestamp}.".encode() + raw_body
    expected = hmac.new(STRIPE_SECRET, signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)
```

Stripe fornisce SDK ufficiali (`stripe-python`, `stripe-node`) con `stripe.Webhook.construct_event()` che fa tutto: verifica firma, controllo tolleranza, parsing. **In produzione usare l'SDK ufficiale**: l'implementazione manuale serve solo per capire cosa succede sotto.

```python
import stripe

stripe.api_key = os.environ["STRIPE_API_KEY"]
endpoint_secret = os.environ["STRIPE_WEBHOOK_SECRET"]

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    raw = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(raw, sig, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(401)
    # event è un oggetto Stripe Event tipizzato
    if event.type == "invoice.paid":
        handle_invoice_paid(event.data.object)
    return {"received": True}
```

---

## Verifica Webhook Slack

Slack firma usando HMAC-SHA256 con timestamp, simile a Stripe ma con formato diverso.

Header: `X-Slack-Signature: v0=<hex>`, e separatamente `X-Slack-Request-Timestamp: <unix_timestamp>`.

Base string: `"v0:" + timestamp + ":" + raw_body`.

```python
def verify_slack(raw_body: bytes, sig_header: str, ts_header: str, secret: str, tolerance: int = 300) -> bool:
    if not sig_header.startswith("v0="):
        return False
    received = sig_header[len("v0="):]

    if abs(time.time() - int(ts_header)) > tolerance:
        return False

    base = f"v0:{ts_header}:".encode() + raw_body
    expected = hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)
```

Il segreto è il "Signing Secret" della Slack App (visibile nelle impostazioni dell'app, sezione "Basic Information").

---

## Verifica Webhook Shopify

Shopify firma con HMAC-SHA256 ma encoda il digest in **base64**, non hex.

Header: `X-Shopify-Hmac-SHA256: <base64>`

```python
import hmac, hashlib, base64

def verify_shopify(raw_body: bytes, sig_header: str, secret: str) -> bool:
    expected = base64.b64encode(
        hmac.new(secret.encode(), raw_body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(expected, sig_header)
```

Note Shopify-specifiche:

- Il segreto è la "API Secret Key" dell'app, oppure il segreto generato per webhook custom.
- Header `X-Shopify-Topic` indica l'evento (`orders/create`, `customers/update`, ecc.).
- Header `X-Shopify-Shop-Domain` indica lo shop sorgente.

---

## Verifica Webhook Square

Square usa HMAC-SHA256 e include un meccanismo di delay configurabile (`SQUARE-INITIAL-DELAY`).

Header: `x-square-hmacsha256-signature: <base64>`

Base string: `notification_url + raw_body` (dove `notification_url` è l'URL completo configurato in Square Developer Dashboard, esattamente come Square lo conosce).

```python
def verify_square(raw_body: bytes, sig_header: str, notification_url: str, secret: str) -> bool:
    base = (notification_url + raw_body.decode("utf-8")).encode("utf-8")
    expected = base64.b64encode(
        hmac.new(secret.encode(), base, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(expected, sig_header)
```

Trappola comune: se il proxy davanti all'app riscrive l'URL (rimuove path prefix, cambia host), `notification_url` deve essere quello originale che Square usa, non quello che vede l'app dietro al proxy. Configurare `X-Forwarded-*` headers e usarli per ricostruire l'URL.

---

## mTLS come Alternativa per B2B Critico

Per integrazioni B2B critiche (es. webhook tra istituti finanziari, sistemi sanitari, partner enterprise), **mutual TLS** è un'alternativa o un'aggiunta a HMAC.

### Come Funziona

In TLS standard solo il server presenta certificato. In mTLS anche il client deve presentare un certificato valido, firmato da una CA fidata dal server. Senza certificato client, la connessione TCP/TLS si chiude prima ancora di arrivare al layer HTTP.

### Vantaggi

- Autenticazione mutua a livello trasporto, prima di qualsiasi byte applicativo.
- Resistenza a leak dei segreti applicativi (HMAC secret) — il certificato privato è separato.
- Audit trail crittografico forte.

### Svantaggi

- Setup complesso: gestione PKI, rotazione certificati, distribuzione CA root.
- Non tutti i provider/consumer supportano mTLS nativamente.
- Difficile da debuggare quando va storto.

### Quando Usarlo

- Integrazioni con SDI (fatturazione PA italiana) o sistemi PA che lo richiedono.
- Webhook tra banche, payment processor, clearing house.
- Integrazioni sanitarie soggette a vincoli regolatori stringenti.

mTLS si combina bene con HMAC: mTLS autentica il canale, HMAC autentica il singolo messaggio. Belt and suspenders.

---

## Replay Attack Prevention

HMAC garantisce che un payload sia autentico, ma non impedisce di reinviare un payload autentico più volte. Esempio: un webhook "payment received" reinviato 100 volte può triggerare 100 conferme d'ordine, 100 email al cliente, 100 record duplicati.

### Difesa 1: Timestamp Window

Tutti i provider seri (Stripe, Slack) includono timestamp nell'header. Il consumer:

1. Verifica firma su `timestamp + body`.
2. Verifica che `|now - timestamp| < tolerance` (tipicamente 5 minuti).

Un payload più vecchio del tolerance window viene rifiutato anche se la firma è valida. Un attaccante che intercetta un webhook deve replicarlo entro pochi minuti.

### Difesa 2: Nonce Store

Il timestamp window non è sufficiente: un attaccante può comunque replicare migliaia di volte nei 5 minuti di finestra. Aggiungere uno **nonce store**: per ogni webhook ricevuto, salvare un identificatore univoco e rifiutare se già visto.

Identificatori utilizzabili come nonce:

- Header dedicato del provider (es. `X-GitHub-Delivery` UUID, Stripe `event.id`).
- Hash SHA-256 del payload + timestamp.
- Combinazione `(event_type, event_id)`.

Implementazione con Redis usando `SETNX` (set if not exists) atomico:

```python
import redis

r = redis.Redis()

def check_and_store_nonce(nonce: str, ttl_seconds: int = 600) -> bool:
    """Restituisce True se nonce è nuovo (non visto), False se duplicato.

    SETNX è atomico: garantisce che solo il primo richiedente "vinca".
    """
    return r.set(f"webhook:nonce:{nonce}", "1", nx=True, ex=ttl_seconds) is True

# Uso
event_id = event["id"]  # es. Stripe event.id
if not check_and_store_nonce(event_id, ttl_seconds=600):
    return Response(status=200)  # già processato, idempotent return
# ... process ...
```

TTL del nonce store: deve essere almeno pari al timestamp tolerance. Tipicamente 10-15 minuti basta. Per audit più lunghi, salvare gli ID processati anche su DB persistente con cleanup periodico.

### Difesa 3: Sequence Number

Alcuni provider includono un sequence number monotonico. Il consumer mantiene "ultimo seq processato" e rifiuta seq <= ultimo. Vulnerabile a out-of-order delivery, ma efficace se combinato con tolerance window.

---

## Idempotency Keys

Idempotency è la proprietà per cui eseguire la stessa operazione N volte produce lo stesso risultato di eseguirla una volta. È **complementare** ad HMAC: HMAC autentica chi invia, idempotency garantisce che non ci siano effetti collaterali se lo stesso messaggio arriva due volte.

### Pattern Stripe Idempotency-Key

Stripe (e molti altri) supporta header `Idempotency-Key` lato outbound API: il client genera un UUID, lo include nell'header, e Stripe garantisce che la stessa key non causi due esecuzioni anche in caso di retry. Stesso pattern applicato lato consumer di webhook:

```python
def process_webhook(event_id: str, event_data: dict):
    """Processa evento con idempotency lato DB."""
    try:
        with db.transaction():
            # Inserimento con UNIQUE constraint su event_id
            db.execute(
                "INSERT INTO webhook_events (event_id, payload, processed_at) VALUES (%s, %s, NOW())",
                (event_id, json.dumps(event_data))
            )
            # Side effect: solo se INSERT ha avuto successo
            create_order_from_event(event_data)
    except UniqueViolation:
        # Già processato: ritorna senza errore
        return
```

Lo schema DB:

```sql
CREATE TABLE webhook_events (
    event_id      TEXT PRIMARY KEY,
    payload       JSONB NOT NULL,
    processed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_webhook_events_processed_at ON webhook_events(processed_at);
```

UNIQUE constraint sul primary key garantisce che solo il primo INSERT abbia successo. Il `try/except` sul `UniqueViolation` (o `IntegrityError`) trasforma il duplicato in un no-op silente.

### Variante Redis

Per workload ad altissimo volume dove l'INSERT su DB principale è troppo costoso, si può usare Redis come idempotency store con TTL e poi confermare su DB asincrono:

```python
def is_duplicate(event_id: str) -> bool:
    return r.set(f"webhook:processed:{event_id}", "1", nx=True, ex=86400) is False
```

TTL di 24h-7gg in base alla finestra di retry del provider.

### Idempotency a Livello Business Logic

Anche con idempotency su event_id, la business logic deve essere idempotente. Esempio: "se ricevi `payment.succeeded`, segna l'ordine come pagato" — eseguire più volte è innocuo (lo stato è già "pagato"). Ma "se ricevi `payment.succeeded`, INCREMENTA il counter pagamenti" — eseguire due volte è doppio conteggio.

Pattern corretto: usare update con condizione (`UPDATE ... WHERE status != 'paid'`) o state machine esplicita.

---

## Retry Semantics: At-Least-Once + Idempotency

I provider di webhook quasi tutti adottano semantica **at-least-once**: garantiscono che il webhook arrivi almeno una volta, ma può arrivare più volte. Le ragioni:

- Il consumer ha risposto con timeout o errore 5xx → retry.
- Il consumer ha risposto 200 ma la conferma si è persa per network glitch → retry.
- Riavvio del provider mentre era in coda di invio → retry.

**Exactly-once delivery in sistemi distribuiti è impossibile in generale** (vedi teorema delle Two Generals). Il pattern realistico è:

```
Provider: at-least-once delivery
Consumer: idempotent processing
─────────────────────────────────
Risultato effettivo: exactly-once semantics
```

### Politiche di Retry Tipiche

- **Stripe**: retry esponenziale fino a 3 giorni se il consumer risponde non-2xx.
- **GitHub**: retry per 5xx fino a 30 volte in 24h, poi disabilita il webhook.
- **Shopify**: retry per 19 tentativi in 48 ore, poi disabilita.
- **Slack**: 3 tentativi totali, poi droppa.

### Cosa Deve Fare il Consumer

1. Rispondere 2xx **solo** dopo aver garantito la persistenza dell'evento (almeno l'INSERT idempotency record). Se la business logic è lunga, restituire 200 e processare async (vedi pattern Receive-Verify-Enqueue).
2. Mai rispondere 4xx per problemi temporanei: il provider non riproverà sui 4xx (interpretati come "richiesta malformata, inutile riprovare").
3. Rispondere 5xx solo per veri errori server (DB down, dipendenza esterna giù): innesca retry.
4. Rispondere entro il timeout del provider (tipicamente 5-30 secondi).

---

## Webhook in n8n / Make / Zapier

I platform no-code introducono complicazioni nella verifica HMAC perché spesso parsano automaticamente il body come JSON, perdendo i bytes raw originali.

### n8n

Il nodo "Webhook" di n8n offre opzione "Raw Body" — abilitarla è essenziale per HMAC. Con Raw Body abilitato, il payload è disponibile come `$binary` o stringa raw, e si può calcolare HMAC nel nodo successivo (Function/Code).

Esempio nodo Code in n8n:

```javascript
const crypto = require('crypto');
const secret = $env.WEBHOOK_SECRET;
const rawBody = $input.first().binary.data; // stringa base64
const buf = Buffer.from(rawBody, 'base64');
const sigHeader = $input.first().json.headers['x-hub-signature-256'];
const received = sigHeader.replace('sha256=', '');
const expected = crypto.createHmac('sha256', secret).update(buf).digest('hex');
const ok = crypto.timingSafeEqual(
  Buffer.from(expected, 'hex'),
  Buffer.from(received, 'hex')
);
if (!ok) throw new Error('Invalid signature');
return $input.all();
```

### Make

Il modulo "Custom Webhook" di Make parsa JSON automaticamente. Per webhook HMAC affidabili in Make ci sono due strade:

1. **Custom Webhook con "JSON pass-through"**: configurare il webhook per ricevere come stringa raw, poi parsare manualmente in un modulo successivo. Limitato e fragile.
2. **Middleware esterno**: mettere un Cloudflare Worker o un piccolo servizio Node davanti, che verifica HMAC e poi inoltra a Make solo se la firma è valida. Pattern raccomandato per produzione.

Esempio Cloudflare Worker:

```javascript
export default {
  async fetch(request, env) {
    const raw = await request.text();
    const sig = request.headers.get('x-hub-signature-256') || '';
    const received = sig.replace('sha256=', '');
    const key = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(env.WEBHOOK_SECRET),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    const signature = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(raw));
    const expected = [...new Uint8Array(signature)]
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    if (expected !== received) {
      return new Response('Invalid signature', { status: 401 });
    }
    // Forward a Make
    return fetch(env.MAKE_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: raw
    });
  }
};
```

### Zapier

Stesso problema: "Catch Hook" parsa JSON. Esiste "Catch Raw Hook" che preserva il body raw come stringa, da cui si può calcolare HMAC in uno step "Code by Zapier". Ma Code by Zapier ha timeout brevi e niente accesso a librerie esterne — pattern fattibile per webhook semplici, fragile per produzione.

In tutti i casi, durante lo **sviluppo locale** servirà un tunnel: ngrok, cloudflared tunnel, o tailscale funnel per esporre `localhost:3000` ad un URL pubblico HTTPS.

```bash
ngrok http 3000
# → https://abc123.ngrok.io  (usare questo come webhook URL)
```

---

## TLS, IP Allowlist, Headers Sicurezza

### TLS 1.3 Obbligatorio

L'endpoint webhook deve essere HTTPS only. TLS 1.2 è ancora accettato come fallback ma TLS 1.3 è il default raccomandato. Configurazione nginx tipica:

```nginx
server {
    listen 443 ssl http2;
    server_name webhooks.aziendaitaliana.it;

    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE-ECDSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    location /webhook/ {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 1m;
    }
}
```

### IP Allowlist

Quando il provider pubblica una lista di IP da cui inviano webhook, configurare allowlist a livello firewall/WAF. Esempi:

- GitHub: `https://api.github.com/meta` → campo `hooks`.
- Stripe: lista pubblicata in documentazione.
- Shopify: lista pubblicata in documentazione.

Esempio nginx:

```nginx
location /webhook/github {
    allow 192.30.252.0/22;
    allow 185.199.108.0/22;
    allow 140.82.112.0/20;
    deny all;
    proxy_pass http://localhost:3000;
}
```

Limite: gli IP cambiano. Automatizzare la sincronizzazione (cron job che aggiorna l'allowlist da API meta del provider) o usare CIDR ampi documentati.

### Rate Limiting

Anche con HMAC, è prudente rate limit per IP per evitare flood:

```nginx
limit_req_zone $binary_remote_addr zone=webhook:10m rate=100r/s;

location /webhook/ {
    limit_req zone=webhook burst=200 nodelay;
    proxy_pass http://localhost:3000;
}
```

---

## Pattern Produzione: Receive-Verify-Enqueue-Process

Il pattern raccomandato per webhook ad alto volume o con processing pesante:

```
HTTP POST → [1. Receive] → [2. Verify HMAC] → [3. Enqueue su queue] → 200 OK (entro 5s)
                                                       ↓
                                            [4. Worker async processa]
                                                       ↓
                                            [5. Idempotency check + business logic]
```

### Vantaggi

- **Risposta veloce**: il provider riceve 200 entro pochi millisecondi, evitando timeout e retry.
- **Disaccoppiamento**: il processing pesante non blocca la ricezione.
- **Resilienza**: se la business logic ha bug, gli eventi sono salvati in queue e possono essere riprocessati.
- **Scalabilità**: worker indipendenti processano in parallelo.

### Implementazione con Redis Queue

```python
import redis, json
from rq import Queue

r = redis.Redis()
q = Queue("webhooks", connection=r)

@app.post("/webhook")
async def webhook(request: Request):
    raw = await request.body()
    sig = request.headers.get("x-signature", "")
    if not verify_signature(raw, sig):
        raise HTTPException(401)
    # Enqueue per processing async
    q.enqueue(process_webhook_event, raw.decode())
    return Response(status_code=204)

def process_webhook_event(raw_payload: str):
    """Worker function — processata da rq worker."""
    event = json.loads(raw_payload)
    event_id = event["id"]
    if is_duplicate(event_id):
        return
    # ... business logic ...
```

### Implementazione con AWS SQS / Cloud Pub/Sub

Stesso pattern, queue managed:

```python
import boto3
sqs = boto3.client("sqs")

@app.post("/webhook")
async def webhook(request: Request):
    raw = await request.body()
    if not verify_signature(raw, request.headers.get("x-signature", "")):
        raise HTTPException(401)
    sqs.send_message(
        QueueUrl=os.environ["SQS_URL"],
        MessageBody=raw.decode(),
        MessageGroupId="webhooks"
    )
    return Response(status_code=204)
```

Il consumer SQS (Lambda, ECS task, worker) processa idempotentemente.

---

## Monitoring e Alerting

### Metriche Chiave

- **Rate webhook ricevuti**: per provider, per evento. Drop improvvisi = problema.
- **Rate firme fallite**: deve essere ~0. Picchi indicano attacco o rotazione segreto sbagliata.
- **Latency end-to-end**: dalla ricezione all'esecuzione completa.
- **Lag della queue**: numero eventi in attesa di processing.
- **Rate retry dal provider**: se il provider sta ritentando molto, il consumer è lento o instabile.

### Alerting

Configurare alert su:

- Firma HMAC fallita > 10 in 5 minuti → possibile attacco.
- Rate webhook = 0 per 30 minuti su provider attivo → endpoint giù o provider giù.
- Queue lag > 1000 eventi → worker insufficienti o processing rotto.
- Latency p99 > soglia → degradazione performance.

### Dashboard

Esempio metriche Prometheus:

```python
from prometheus_client import Counter, Histogram

webhook_received = Counter("webhook_received_total", "Webhook ricevuti", ["provider", "event_type"])
webhook_signature_failed = Counter("webhook_signature_failed_total", "Firme HMAC fallite", ["provider"])
webhook_processing_duration = Histogram("webhook_processing_seconds", "Durata processing", ["provider"])
```

Grafana dashboard con: rate webhook per provider, errori firma, latency distribution, queue depth.

### Log Strutturato

Loggare ogni webhook con contesto:

```json
{
  "timestamp": "2026-04-22T14:30:00Z",
  "provider": "stripe",
  "event_id": "evt_abc123",
  "event_type": "invoice.paid",
  "signature_valid": true,
  "duplicate": false,
  "processing_duration_ms": 142,
  "result": "ok"
}
```

**Mai loggare il body completo** se contiene PII o segreti. Loggare solo metadata e ID.

---

## Casi d'Uso Reali Italiani

### Webhook Fattura PA da SDI

Per le aziende che integrano fatturazione elettronica con SDI (Sistema di Interscambio dell'Agenzia delle Entrate), i webhook arrivano da intermediari (provider come Aruba, TeamSystem, Fatture in Cloud) e notificano cambi di stato (`accettata`, `rifiutata`, `consegnata`, `decorrenza-termini`, `mancata-consegna`). Considerazioni:

- L'intermediario fornisce signing secret tipicamente HMAC-SHA256.
- Il payload include riferimenti a fatture con dati fiscali — trattamento GDPR rigoroso.
- Idempotency essenziale: lo stato fattura è macchina a stati, evitare regressioni.
- Tolerance window stretto (1-2 minuti) per stati critici.
- Audit log obbligatorio per compliance — salvare ogni evento con timestamp e firma originale.
- L'identificativo SDI (IdentificativoSdI) è ottimo come idempotency key naturale.
- Stato di "decorrenza termini" indica che il destinatario PA non ha confermato/rifiutato entro 15 giorni — gestire come stato terminale separato.
- Per audit fiscali, conservare gli eventi grezzi per almeno 10 anni (norma di conservazione fatture italiane).
- Mai usare il payload XML re-serializzato per HMAC: la canonicalizzazione XML cambia il digest. Conservare e firmare i bytes raw originali.

### Webhook Stripe per Subscription PMI

Tipico SaaS italiano con clienti PMI usa Stripe per abbonamenti. Eventi critici:

- `checkout.session.completed` → attivare account.
- `invoice.paid` → confermare pagamento.
- `invoice.payment_failed` → notificare cliente, attivare dunning.
- `customer.subscription.deleted` → disattivare account dopo grace period.

Pattern produzione: Stripe SDK per verifica, Redis nonce store su `event.id`, queue per processing async, state machine esplicita per stato subscription.

### Webhook GitHub Actions per Trigger Interno

Repository privato aziendale che, su ogni push a `main`, deve triggerare un workflow interno (deploy, sync con sistema legacy, notifica team). GitHub invia webhook a un endpoint interno aziendale dietro VPN. Difese combinate:

- mTLS sul reverse proxy (perché siamo in B2B critico).
- HMAC su payload (X-Hub-Signature-256).
- IP allowlist sui CIDR pubblicati da GitHub.
- X-GitHub-Delivery come idempotency key.
- Queue interna con worker che esegue il deploy, con timeout e rollback.
- Filtro early su `X-GitHub-Event` per accettare solo eventi previsti (`push`, `pull_request`) e scartare tutto il resto con 204 — riduce la superficie d'attacco lato logica.
- Verifica ramo nel payload (`ref == "refs/heads/main"`) prima di triggerare il deploy: un push su feature branch non deve passare alla pipeline produzione.

### Webhook PSP per E-commerce PMI

Una PMI italiana con shop e-commerce su WooCommerce o PrestaShop riceve webhook dal PSP (Stripe, PayPal, Nexi, Satispay) per stati pagamento. Pattern tipico:

- Ogni PSP ha il suo schema HMAC: usare gli SDK ufficiali, non implementare a mano.
- Dedup su transazione_id (non su evento_id, perché un evento "captured" può seguire un "authorized" sulla stessa transazione).
- State machine ordine: `pending → authorized → captured → fulfilled` oppure `pending → failed/cancelled`. Webhook fuori sequenza vanno ignorati con 200, non rifiutati.
- Timeout consumer molto stretto: i PSP riducono retry per webhook che timeout-ano, e il rischio è perdere notifiche di pagamento.
- Riconciliazione periodica via API pull (notturna): confronto tra stato ordini e stato PSP per recuperare webhook persi.

---

## Checklist Sicurezza Webhook

Prima di mettere in produzione un endpoint webhook:

- [ ] Endpoint HTTPS only, TLS 1.3 (TLS 1.2 fallback accettabile).
- [ ] HMAC verification implementata su raw body bytes (non su JSON parsato).
- [ ] Confronto firma a tempo costante (`hmac.compare_digest` / `crypto.timingSafeEqual` / `hash_equals`).
- [ ] Algoritmo SHA-256 (no SHA-1).
- [ ] Segreto HMAC letto da env variable o secret manager, mai hardcoded.
- [ ] Segreto HMAC ruotabile senza downtime (dual-key support).
- [ ] Timestamp tolerance window verificato (300s tipicamente).
- [ ] Nonce store con TTL >= tolerance window per replay protection.
- [ ] Idempotency su event_id con UNIQUE constraint DB o SETNX Redis.
- [ ] Risposta 2xx entro 5 secondi (idealmente < 1s).
- [ ] Processing pesante delegato a worker async via queue.
- [ ] IP allowlist quando provider pubblica lista.
- [ ] Rate limiting sull'endpoint.
- [ ] Risposte di errore generiche (no information disclosure).
- [ ] Log strutturato senza PII / body completo.
- [ ] Metriche Prometheus + alerting configurato.
- [ ] Procedura documentata per rotazione segreto.
- [ ] Test automatici per firma valida, firma invalida, replay, payload tampering.
- [ ] Runbook per "endpoint giù", "tempo riscontri firme errate", "queue lag elevato".

---

## Troubleshooting

### "Firma sempre invalida"

Cause più comuni:

1. **Body parsato prima della verifica**: il framework ha già fatto JSON.parse e re-serializzato. Soluzione: usare body raw (`express.raw`, `request.body()` async, `php://input`).
2. **Charset / encoding**: il body contiene caratteri unicode e l'encoding usato per HMAC differisce. Sempre UTF-8, sempre bytes.
3. **Trailing newline**: alcuni provider includono o rimuovono `\n` finale. Verificare con dump esadecimale.
4. **Header con prefisso**: `sha256=...` vs solo `<hex>`. Strippare il prefisso prima del confronto.
5. **Hex vs base64**: alcuni provider (Shopify) usano base64, altri (GitHub) hex. Verificare formato atteso.
6. **Segreto sbagliato**: copiato con spazi extra, da ambiente sbagliato (test vs prod).

### "Webhook arriva due volte"

È normale: at-least-once delivery. Implementare idempotency. Se arriva 100 volte, il provider sta facendo retry perché il consumer non risponde 2xx in tempo: indagare latency.

### "Provider segnala webhook disabilitato"

Il consumer ha risposto non-2xx troppe volte di fila. Riabilitare manualmente nelle settings del provider, e investigare la causa root (downtime, bug, deploy che ha rotto endpoint).

### "Time-out su processing pesante"

Spostare processing in queue async. Rispondere 200 immediatamente dopo verify + enqueue. Il worker processerà in background con tempi più rilassati.

### "Replay attack sospetto in log"

Eventi recenti reinviati dopo finestra di tolleranza, oppure stesso event_id più volte vicino: nonce store sta funzionando ma l'attaccante (o un bug) sta tentando. Verificare:

- Se IP coincide con provider legittimo → probabile retry naturale.
- Se IP è altro → possibile attacco. Bloccare IP, rotare segreto se necessario.

### "Errore '401 invalid signature' dal provider durante test"

Probabilmente stiamo restituendo 401 al provider, e il provider lo interpreta come "credenziali sbagliate" e disabilita. Le firme errate da parte del provider sono indice di:

- Segreto disallineato tra dashboard provider e nostra env.
- Endpoint dietro proxy che modifica il body (es. gzip, decompressione).
- Payload modificato in transito (raro su TLS, ma possibile su middleware buggato).

---

## Riferimenti

- RFC 2104 — HMAC: Keyed-Hashing for Message Authentication
- RFC 6234 — US Secure Hash Algorithms (SHA family)
- OWASP Webhook Security Cheat Sheet: `cheatsheetseries.owasp.org`
- Stripe Webhook signatures: `stripe.com/docs/webhooks/signatures`
- GitHub Webhook security: `docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries`
- Slack Verifying requests: `api.slack.com/authentication/verifying-requests-from-slack`
- Shopify Verifying webhooks: `shopify.dev/docs/apps/webhooks/configuration/https#step-5-verify-the-webhook`
- Square Webhook signature: `developer.squareup.com/docs/webhooks/step3validate`
- Cloudflare Workers crypto: `developers.cloudflare.com/workers/runtime-apis/web-crypto/`
- "Idempotency in distributed systems" — articoli di Stripe Engineering Blog
- Documenti correlati in questa libreria: `09-n8n-guida-completa-self-hosted.md`, `10-make-integromat-guida-operativa.md`, `14-zapier-guida-operativa.md`.

---

## Esercizi

1. **Lab — Stripe webhook receiver.** Endpoint Python (FastAPI) che riceve Stripe webhook, verifica `Stripe-Signature`, gestisce timestamp tolerance (5 min), idempotency via Redis dedup.
2. **Lab — replay attack simulation.** Simula attacker che intercetta + replay webhook valido. Verifica che la replay protection lo blocchi.
3. **Stretch — multi-provider gateway.** Endpoint singolo che riceve webhook da Stripe + Square + GitHub + Slack; verifica HMAC per ognuno con secret diverso, route a downstream coda.

## Auto-valutazione

1. HMAC: cos'e e perche serve constant-time compare?
2. Timing attack: come funziona?
3. Replay protection: cosa serve oltre HMAC?
4. Idempotency key: dove memorizzarla? TTL?
5. Receive-Verify-Enqueue pattern: vantaggi.

## Letture primarie consigliate

- RFC 2104 — HMAC. https://datatracker.ietf.org/doc/html/rfc2104
- Stripe — Verifying webhook signatures. Vedi `00-BIBLIOGRAFIA.md`.
- IETF draft — Idempotency Key. Vedi `00-BIBLIOGRAFIA.md`.

## Collegamenti incrociati

- Modulo 04 — `04-integrazione-api.md`: API security basics.
- Modulo 17 — `17-retry-idempotency-pattern.md`: idempotency deep dive.

## Glossario locale

| Termine | Definizione |
|---|---|
| **HMAC** | Hash-based Message Authentication Code. |
| **Constant-time compare** | Confronto che non leak timing info. |
| **Timing attack** | Estrazione info via misurazione tempi. |
| **Replay attack** | Riutilizzo di richieste valide intercettate. |
| **Nonce** | Number used once; previene replay. |
| **Idempotency key** | UUID per dedup richieste duplicate. |
| **Receive-Verify-Enqueue** | Pattern: ricevi, valida, metti in coda async. |
| **`Stripe-Signature`** | Header con timestamp + signature Stripe webhook. |
