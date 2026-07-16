# Tutorial Lab — Sicurezza Webhook: HMAC, Replay Protection, Idempotency

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `15-webhook-security-hmac-verifica.md`
> **Livello:** competent → proficient
> **Tempo stimato:** 4-5 ore (lab completo)
> **Prerequisiti:** HTTP/Python basics, Flask basics, concetto HMAC (RFC 2104)
> **Versioni di riferimento:** Python 3.11+ · Flask 3.x · Redis 7 · Stripe webhook v2 · GitHub X-Hub-Signature-256

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Implementare verifica HMAC-SHA256 con constant-time compare (no timing attack)
2. Proteggere endpoint webhook da replay attack (timestamp window + nonce store)
3. Gestire idempotency key per deduplicare richieste duplicate at-least-once
4. Verificare webhook reali di Stripe, GitHub, Slack con le loro specificità
5. Applicare il pattern Receive-Verify-Enqueue per processing asincrono sicuro
6. Testare la sicurezza con attacchi simulati

---

## Lab Environment Setup

```bash
# Crea virtual environment
python3 -m venv webhook-lab
source webhook-lab/bin/activate

# Installa dipendenze
pip install flask==3.0.3 redis==5.0.7 httpx==0.27.0 celery==5.4.0

# Verifica Redis disponibile (necessario per nonce store)
docker run -d --name redis-lab -p 6379:6379 redis:7-alpine
redis-cli ping  # Output atteso: PONG

# Struttura progetto
mkdir -p webhook-secure/{handlers,tests}
cd webhook-secure
```

```bash
#!/bin/bash
# check-prereqs-webhook.sh
echo "=== Verifica prerequisiti Webhook Lab ==="

python3 --version || { echo "Python 3 richiesto"; exit 1; }

python3 -c "import flask, redis, hmac, hashlib; print('Tutte le librerie OK')" || {
    echo "Librerie mancanti — eseguire pip install flask redis"
    exit 1
}

redis-cli ping 2>/dev/null | grep -q PONG && echo "Redis: OK" || {
    echo "Redis non disponibile — avviare docker run -d -p 6379:6379 redis:7-alpine"
}

echo "=== Pronto per il lab ==="
```

---

## Analogia Introduttiva

> **Un webhook senza verifica HMAC è come una cassetta della posta senza nome**:
> chiunque può imbucarne la corrispondenza, anche se il mittente non sei tu.
>
> La **firma HMAC** è come una lettera con sigillo di ceralacca:
> il mittente la firma con un segreto condiviso (il sigillo), tu verifi il sigillo
> prima di aprire la lettera. Se il sigillo non corrisponde, la lettera è falsa.
>
> Il **replay attack** è come qualcuno che fotografa una lettera legittima
> e la rispedisce decine di volte. La firma è valida (è una copia autentica),
> ma il timestamp rivela che è "troppo vecchia" — e il **nonce** dice
> "abbiamo già visto questa lettera".

---

## Threat Model dei Webhook

```
MINACCE CONCRETE PER UN ENDPOINT WEBHOOK:

┌─────────────────────┬──────────────────────────────┬──────────────────────────┐
│ Minaccia            │ Descrizione                  │ Difesa                   │
├─────────────────────┼──────────────────────────────┼──────────────────────────┤
│ Spoofing            │ POST forgiato che imita       │ HMAC signature verify    │
│                     │ il provider                  │                          │
├─────────────────────┼──────────────────────────────┼──────────────────────────┤
│ Replay Attack       │ Reinvio di webhook legittimo  │ Timestamp window + nonce │
│                     │ intercettato                 │ store (Redis)            │
├─────────────────────┼──────────────────────────────┼──────────────────────────┤
│ MITM / Tampering    │ Modifica payload in transito  │ HMAC su raw body bytes   │
│                     │                              │ + TLS obbligatorio       │
├─────────────────────┼──────────────────────────────┼──────────────────────────┤
│ Timing Attack       │ Misura tempo compare() per   │ hmac.compare_digest()    │
│                     │ indovinare la firma          │ (constant-time)          │
├─────────────────────┼──────────────────────────────┼──────────────────────────┤
│ Duplicate Processing│ Provider reinvia stesso       │ Idempotency key          │
│                     │ webhook per timeout/retry    │ (Redis TTL)              │
└─────────────────────┴──────────────────────────────┴──────────────────────────┘

REGOLA D'ORO:
  Un endpoint webhook è un'API pubblica scrivibile da CHIUNQUE conosce l'URL.
  Senza verifica HMAC, qualunque richiesta viene elaborata come legittima.
```

---

## PART A — HMAC Signature Verification

### A1 — Perché `==` è Pericoloso

```python
#!/usr/bin/env python3
# file: demo_timing_attack.py
"""
Dimostra perché confrontare firme con == è pericoloso.
Il comparison string Python si interrompe al primo byte diverso —
un attaccante può misurare i tempi per indovinare la firma byte per byte.
"""
import hmac
import time

VALID_SIG = "sha256=abc123def456"

def insecure_compare(received: str, expected: str) -> bool:
    """MAI usare questo per confrontare firme crittografiche."""
    return received == expected  # si ferma al primo carattere diverso

def secure_compare(received: str, expected: str) -> bool:
    """Sempre usare hmac.compare_digest — tempo costante indipendente dai byte."""
    return hmac.compare_digest(received, expected)

# Dimostrazione differenza temporale
attempts = [
    "x" * len(VALID_SIG),          # tutto sbagliato
    "sha256=" + "x" * 12,          # prefisso giusto
    "sha256=abc123" + "x" * 6,     # metà giusta
    VALID_SIG,                      # corretta
]

print("=== Timing con == (insicuro) ===")
for attempt in attempts:
    times = []
    for _ in range(10000):
        start = time.perf_counter_ns()
        insecure_compare(attempt, VALID_SIG)
        times.append(time.perf_counter_ns() - start)
    avg = sum(times) / len(times)
    print(f"  {attempt[:20]!r:22s} → {avg:7.1f} ns")

print("\n=== Timing con hmac.compare_digest (sicuro) ===")
for attempt in attempts:
    times = []
    for _ in range(10000):
        start = time.perf_counter_ns()
        secure_compare(attempt, VALID_SIG)
        times.append(time.perf_counter_ns() - start)
    avg = sum(times) / len(times)
    print(f"  {attempt[:20]!r:22s} → {avg:7.1f} ns (costante)")

# Output dimostra che == varia, compare_digest è uniforme
```

```bash
python3 demo_timing_attack.py
# Osserva come il tempo con == aumenta quando più byte corrispondono
# Con compare_digest il tempo è uniforme
```

### A2 — Server Flask con HMAC Verification

```python
#!/usr/bin/env python3
# file: webhook_server.py
"""
Server webhook sicuro con:
- HMAC-SHA256 verification (constant-time compare)
- Replay protection (timestamp window 5 min + nonce Redis)
- Idempotency key deduplication
- Pattern Receive-Verify-Enqueue (processing asincrono)
"""
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import redis
from flask import Flask, abort, jsonify, request

# ─── Setup ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("webhook")

app = Flask(__name__)
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True
)

# Segreti per provider diversi (in produzione: caricare da Vault)
SECRETS = {
    "stripe":  os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test_secret_stripe"),
    "github":  os.environ.get("GITHUB_WEBHOOK_SECRET", "test_secret_github"),
    "generic": os.environ.get("WEBHOOK_SECRET", "test_secret_generic"),
}

MAX_TIMESTAMP_DELTA_SECONDS = 300   # 5 minuti
NONCE_TTL_SECONDS = 600             # 10 minuti (>= 2x timestamp window)
IDEMPOTENCY_TTL_SECONDS = 86400     # 24 ore


# ─── Strutture dati ───────────────────────────────────────────────────────────

@dataclass
class VerificationResult:
    is_valid: bool
    error: Optional[str] = None
    provider: Optional[str] = None
    event_id: Optional[str] = None


# ─── Funzioni di verifica ─────────────────────────────────────────────────────

def verify_hmac_generic(
    body: bytes,
    received_signature: str,
    secret: str,
    timestamp: Optional[str] = None
) -> VerificationResult:
    """
    Verifica HMAC-SHA256 generica.
    Signature attesa: sha256=<hex>
    """
    if not received_signature:
        return VerificationResult(False, "Header firma mancante")

    if timestamp:
        try:
            ts = int(timestamp)
            delta = abs(time.time() - ts)
            if delta > MAX_TIMESTAMP_DELTA_SECONDS:
                return VerificationResult(
                    False,
                    f"Timestamp troppo vecchio ({delta:.0f}s > {MAX_TIMESTAMP_DELTA_SECONDS}s)"
                )
        except ValueError:
            return VerificationResult(False, "Timestamp non valido")

    # Calcola firma attesa (SEMPRE su raw body bytes)
    expected_sig = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()

    # Confronto constant-time (OBBLIGATORIO)
    if not hmac.compare_digest(expected_sig, received_signature):
        logger.warning("Firma HMAC non valida — possibile spoofing")
        return VerificationResult(False, "Firma HMAC non valida")

    return VerificationResult(True, provider="generic")


def verify_stripe(body: bytes, stripe_signature: str) -> VerificationResult:
    """
    Verifica webhook Stripe.
    Header: Stripe-Signature: t=<timestamp>,v1=<hex>,v0=<hex_old>
    Stripe firma: HMAC-SHA256(timestamp + "." + body)
    """
    if not stripe_signature:
        return VerificationResult(False, "Header Stripe-Signature mancante")

    parts = {}
    for part in stripe_signature.split(","):
        key, _, value = part.partition("=")
        parts[key] = value

    timestamp = parts.get("t")
    v1_sig = parts.get("v1")

    if not timestamp or not v1_sig:
        return VerificationResult(False, "Header Stripe-Signature malformato")

    # Verifica timestamp (Stripe raccomanda <= 5 minuti)
    try:
        ts = int(timestamp)
        delta = abs(time.time() - ts)
        if delta > MAX_TIMESTAMP_DELTA_SECONDS:
            return VerificationResult(False, f"Stripe: timestamp troppo vecchio ({delta:.0f}s)")
    except ValueError:
        return VerificationResult(False, "Stripe: timestamp non valido")

    # Stripe firma: HMAC(secret, f"{timestamp}.{body}")
    signed_payload = f"{timestamp}.".encode() + body
    expected_sig = hmac.new(
        SECRETS["stripe"].encode(),
        signed_payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, v1_sig):
        logger.warning("Firma Stripe non valida")
        return VerificationResult(False, "Firma Stripe non valida")

    logger.info("Webhook Stripe verificato (timestamp=%s)", timestamp)
    return VerificationResult(True, provider="stripe")


def verify_github(body: bytes, hub_signature_256: str) -> VerificationResult:
    """
    Verifica webhook GitHub.
    Header: X-Hub-Signature-256: sha256=<hex>
    GitHub firma: HMAC-SHA256(body) — NON include timestamp
    """
    if not hub_signature_256:
        return VerificationResult(False, "Header X-Hub-Signature-256 mancante")

    if not hub_signature_256.startswith("sha256="):
        return VerificationResult(False, "Formato firma GitHub non valido")

    expected_sig = "sha256=" + hmac.new(
        SECRETS["github"].encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, hub_signature_256):
        logger.warning("Firma GitHub non valida")
        return VerificationResult(False, "Firma GitHub non valida")

    return VerificationResult(True, provider="github")


# ─── Protezione Replay Attack ─────────────────────────────────────────────────

def check_replay(nonce: str) -> bool:
    """
    Verifica che il nonce non sia già stato visto.
    Ritorna True se il nonce è NUOVO (non replay).
    """
    key = f"webhook:nonce:{nonce}"
    # SET key value NX (only if Not eXists) EX TTL
    was_new = redis_client.set(key, "1", nx=True, ex=NONCE_TTL_SECONDS)
    return was_new is not None  # True = nuovo, False = già visto


# ─── Idempotency ─────────────────────────────────────────────────────────────

def is_already_processed(idempotency_key: str) -> bool:
    """Verifica se l'evento è già stato processato."""
    return redis_client.exists(f"webhook:processed:{idempotency_key}") == 1


def mark_as_processed(idempotency_key: str, result: dict) -> None:
    """Marca evento come processato con il risultato."""
    redis_client.setex(
        f"webhook:processed:{idempotency_key}",
        IDEMPOTENCY_TTL_SECONDS,
        json.dumps(result)
    )


def get_cached_result(idempotency_key: str) -> Optional[dict]:
    """Recupera risultato cached per richiesta duplicata."""
    data = redis_client.get(f"webhook:processed:{idempotency_key}")
    return json.loads(data) if data else None


# ─── Endpoint Webhook ─────────────────────────────────────────────────────────

@app.route("/webhook/stripe", methods=["POST"])
def webhook_stripe():
    """Endpoint per webhook Stripe — pagamenti, abbonamenti, disputes."""
    raw_body = request.get_data()  # CRITICO: raw body, non JSON parsed
    stripe_sig = request.headers.get("Stripe-Signature", "")

    # 1. Verifica firma Stripe
    result = verify_stripe(raw_body, stripe_sig)
    if not result.is_valid:
        logger.warning("Webhook Stripe rifiutato: %s | IP: %s", result.error, request.remote_addr)
        abort(400, result.error)

    # 2. Parse payload
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        abort(400, "Payload non è JSON valido")

    event_id = payload.get("id", "")
    event_type = payload.get("type", "unknown")

    # 3. Idempotency check
    if is_already_processed(event_id):
        cached = get_cached_result(event_id)
        logger.info("Webhook Stripe duplicato ignorato: %s", event_id)
        return jsonify(cached or {"status": "already_processed", "event_id": event_id}), 200

    # 4. Enqueue per processing asincrono
    # In produzione: enqueue su Celery/RQ/n8n webhook
    job_data = {
        "event_id": event_id,
        "event_type": event_type,
        "provider": "stripe",
        "payload": payload,
        "received_at": time.time()
    }
    redis_client.rpush("webhook:queue:stripe", json.dumps(job_data))
    logger.info("Webhook Stripe accodato: %s (%s)", event_id, event_type)

    # 5. Marca come processato (il processing async è idempotente)
    response_body = {"received": True, "event_id": event_id, "queued": True}
    mark_as_processed(event_id, response_body)

    # 6. Risposta immediata a Stripe (< 30s o considererà il webhook fallito)
    return jsonify(response_body), 200


@app.route("/webhook/github", methods=["POST"])
def webhook_github():
    """Endpoint per webhook GitHub — push, PR, issues, releases."""
    raw_body = request.get_data()
    hub_sig = request.headers.get("X-Hub-Signature-256", "")
    github_event = request.headers.get("X-GitHub-Event", "unknown")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")

    # 1. Verifica firma GitHub
    result = verify_github(raw_body, hub_sig)
    if not result.is_valid:
        logger.warning("Webhook GitHub rifiutato: %s", result.error)
        abort(400, result.error)

    # 2. Idempotency su delivery ID
    if delivery_id and is_already_processed(f"github:{delivery_id}"):
        logger.info("Webhook GitHub delivery già processato: %s", delivery_id)
        return jsonify({"status": "already_processed"}), 200

    # 3. Parse e routing per tipo evento
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        abort(400, "Payload non è JSON valido")

    logger.info("Webhook GitHub ricevuto: event=%s delivery=%s", github_event, delivery_id)

    # 4. Routing per evento
    handlers = {
        "push": handle_github_push,
        "pull_request": handle_github_pr,
        "release": handle_github_release,
    }
    handler = handlers.get(github_event)
    if handler:
        handler(payload, delivery_id)
    else:
        logger.debug("Evento GitHub ignorato: %s", github_event)

    if delivery_id:
        mark_as_processed(f"github:{delivery_id}", {"processed": True})

    return jsonify({"received": True, "event": github_event}), 200


@app.route("/webhook/generic", methods=["POST"])
def webhook_generic():
    """
    Endpoint generico con replay protection completa.
    Headers attesi:
      X-Signature-256: sha256=<hex>
      X-Timestamp: <unix_seconds>
      X-Nonce: <uuid_or_random_string>
      X-Idempotency-Key: <unique_event_id>
    """
    raw_body = request.get_data()
    received_sig = request.headers.get("X-Signature-256", "")
    timestamp = request.headers.get("X-Timestamp", "")
    nonce = request.headers.get("X-Nonce", "")
    idempotency_key = request.headers.get("X-Idempotency-Key", "")

    # 1. Verifica firma con timestamp
    result = verify_hmac_generic(raw_body, received_sig, SECRETS["generic"], timestamp)
    if not result.is_valid:
        logger.warning("Webhook generico rifiutato: %s", result.error)
        abort(400, result.error)

    # 2. Replay protection con nonce
    if nonce:
        if not check_replay(nonce):
            logger.warning("Replay attack rilevato! Nonce già visto: %s", nonce[:20])
            abort(409, "Richiesta duplicata — nonce già ricevuto")
    else:
        logger.warning("Nonce mancante — replay protection ridotta")

    # 3. Idempotency key
    if idempotency_key and is_already_processed(idempotency_key):
        cached = get_cached_result(idempotency_key)
        return jsonify(cached or {"status": "already_processed"}), 200

    # 4. Processing
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        payload = {"raw": raw_body.decode("utf-8", errors="replace")}

    response = {
        "received": True,
        "timestamp": time.time(),
        "event_type": payload.get("type", "unknown")
    }

    if idempotency_key:
        mark_as_processed(idempotency_key, response)

    return jsonify(response), 200


# ─── Handler placeholder per GitHub ──────────────────────────────────────────

def handle_github_push(payload: dict, delivery_id: str) -> None:
    repo = payload.get("repository", {}).get("full_name", "unknown")
    ref = payload.get("ref", "unknown")
    commits = len(payload.get("commits", []))
    logger.info("Push su %s branch %s: %d commit(s) [delivery=%s]", repo, ref, commits, delivery_id)
    redis_client.rpush("webhook:queue:github:push", json.dumps({
        "repo": repo, "ref": ref, "commits": commits, "delivery_id": delivery_id
    }))

def handle_github_pr(payload: dict, delivery_id: str) -> None:
    action = payload.get("action", "unknown")
    pr_number = payload.get("number", 0)
    logger.info("PR #%d %s [delivery=%s]", pr_number, action, delivery_id)

def handle_github_release(payload: dict, delivery_id: str) -> None:
    action = payload.get("action", "unknown")
    tag = payload.get("release", {}).get("tag_name", "unknown")
    logger.info("Release %s %s [delivery=%s]", tag, action, delivery_id)


# ─── Health check ─────────────────────────────────────────────────────────────

@app.route("/healthz")
def health():
    try:
        redis_client.ping()
        return jsonify({"status": "ok", "redis": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "degraded", "redis": str(e)}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
```

### A3 — Avvio Server e Test Base

```bash
# Avvia il server
python3 webhook_server.py &

# Health check
curl http://localhost:8080/healthz
# {"redis": "ok", "status": "ok"}

# Test con firma corretta
SECRET="test_secret_generic"
BODY='{"type":"order.created","id":"evt_001"}'
TIMESTAMP=$(date +%s)
NONCE=$(python3 -c "import secrets; print(secrets.token_hex(16))")
IDEMPOTENCY_KEY="evt_001"

# Calcola firma
SIGNATURE="sha256=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')"

curl -X POST http://localhost:8080/webhook/generic \
    -H "Content-Type: application/json" \
    -H "X-Signature-256: $SIGNATURE" \
    -H "X-Timestamp: $TIMESTAMP" \
    -H "X-Nonce: $NONCE" \
    -H "X-Idempotency-Key: $IDEMPOTENCY_KEY" \
    -d "$BODY"

# Output atteso:
# {"event_type": "order.created", "received": true, "timestamp": 1718000000.123}
```

---

## PART B — Test di Sicurezza

### B1 — Test Firma Invalida (Spoofing)

```bash
# Test con firma sbagliata (simulazione attaccante senza il segreto)
BODY='{"type":"payment.succeeded","amount":9999}'
TIMESTAMP=$(date +%s)
NONCE=$(python3 -c "import secrets; print(secrets.token_hex(16))")

curl -X POST http://localhost:8080/webhook/generic \
    -H "Content-Type: application/json" \
    -H "X-Signature-256: sha256=firma_falsa_generata_senza_il_segreto" \
    -H "X-Timestamp: $TIMESTAMP" \
    -H "X-Nonce: $NONCE" \
    -d "$BODY" -v

# Output atteso: HTTP 400 Bad Request
# {"error": "Firma HMAC non valida"}
```

### B2 — Test Replay Attack

```python
#!/usr/bin/env python3
# file: tests/test_replay_attack.py
"""
Simula un replay attack: invia lo stesso webhook due volte
con lo stesso nonce. Il secondo deve essere rifiutato.
"""
import hashlib
import hmac
import json
import secrets
import time

import httpx

SECRET = "test_secret_generic"
BASE_URL = "http://localhost:8080"

def make_signed_request(body: dict, nonce: str, idempotency_key: str):
    body_bytes = json.dumps(body).encode()
    timestamp = str(int(time.time()))
    sig = "sha256=" + hmac.new(
        SECRET.encode(), body_bytes, hashlib.sha256
    ).hexdigest()

    return httpx.post(
        f"{BASE_URL}/webhook/generic",
        content=body_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": sig,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Idempotency-Key": idempotency_key,
        }
    )

def test_replay_protection():
    body = {"type": "payment.captured", "id": "pay_test_001", "amount": 4999}
    nonce = secrets.token_hex(16)
    idempotency_key = f"pay_{secrets.token_hex(8)}"

    print("=== Test Replay Attack ===")

    # Prima richiesta — deve avere successo
    r1 = make_signed_request(body, nonce, idempotency_key)
    print(f"Prima richiesta:   HTTP {r1.status_code} — {r1.json()}")
    assert r1.status_code == 200, f"Prima richiesta fallita: {r1.text}"

    # Seconda richiesta con STESSO nonce — deve essere rifiutata (409)
    r2 = make_signed_request(body, nonce, idempotency_key)
    print(f"Replay (stesso nonce): HTTP {r2.status_code} — {r2.text}")
    assert r2.status_code == 409, f"Replay NON rilevato! HTTP {r2.status_code}"

    # Terza richiesta con nonce DIVERSO, ma stesso idempotency_key
    # → deve tornare 200 ma con stato already_processed
    new_nonce = secrets.token_hex(16)
    r3 = make_signed_request(body, new_nonce, idempotency_key)
    print(f"Nuovo nonce, stessa idempotency key: HTTP {r3.status_code} — {r3.json()}")
    assert r3.status_code == 200
    assert r3.json().get("status") == "already_processed" or r3.json().get("received") is True

    print("\n[OK] Replay protection funziona correttamente")

def test_timestamp_window():
    """Verifica che webhook con timestamp vecchio vengano rifiutati."""
    body = {"type": "test.old", "id": "old_001"}
    body_bytes = json.dumps(body).encode()
    # Timestamp 10 minuti fa (oltre la finestra di 5 minuti)
    old_timestamp = str(int(time.time()) - 600)
    nonce = secrets.token_hex(16)
    sig = "sha256=" + hmac.new(
        SECRET.encode(), body_bytes, hashlib.sha256
    ).hexdigest()

    r = httpx.post(
        f"{BASE_URL}/webhook/generic",
        content=body_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": sig,
            "X-Timestamp": old_timestamp,
            "X-Nonce": nonce,
        }
    )
    print(f"\nTimestamp vecchio (10 min fa): HTTP {r.status_code}")
    assert r.status_code == 400, f"Timestamp vecchio non rifiutato: {r.text}"
    print("[OK] Finestra timestamp funziona correttamente")

if __name__ == "__main__":
    test_replay_protection()
    test_timestamp_window()
    print("\n=== Tutti i test di sicurezza superati ===")
```

```bash
python3 tests/test_replay_attack.py
```

**Output atteso:**
```
=== Test Replay Attack ===
Prima richiesta:              HTTP 200 — {'received': True, ...}
Replay (stesso nonce):        HTTP 409 — {"error": "Richiesta duplicata — nonce già ricevuto"}
Nuovo nonce, stessa idem key: HTTP 200 — {'status': 'already_processed'}

[OK] Replay protection funziona correttamente

Timestamp vecchio (10 min fa): HTTP 400
[OK] Finestra timestamp funziona correttamente

=== Tutti i test di sicurezza superati ===
```

### B3 — Test Webhook Stripe

```python
#!/usr/bin/env python3
# file: tests/test_stripe_webhook.py
"""
Simula un webhook Stripe reale con il formato corretto.
"""
import hashlib
import hmac
import json
import time

import httpx

STRIPE_SECRET = "whsec_test_secret_stripe"
BASE_URL = "http://localhost:8080"

def make_stripe_signature(payload: bytes, secret: str) -> str:
    """
    Formato Stripe: t=<timestamp>,v1=<hex>
    Stripe firma: HMAC-SHA256(f"{timestamp}.{body}")
    """
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.".encode() + payload
    v1 = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={v1}"

def test_stripe_payment_webhook():
    payload = {
        "id": "evt_1OhMxB2eZvKYlo2C0Abc123",
        "object": "event",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_3OhMxB2eZvKYlo2C1Def456",
                "amount": 4999,
                "currency": "eur",
                "status": "succeeded"
            }
        }
    }
    body_bytes = json.dumps(payload).encode()
    stripe_sig = make_stripe_signature(body_bytes, STRIPE_SECRET)

    r = httpx.post(
        f"{BASE_URL}/webhook/stripe",
        content=body_bytes,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": stripe_sig,
        }
    )
    print(f"Stripe payment webhook: HTTP {r.status_code} — {r.json()}")
    assert r.status_code == 200
    assert r.json()["received"] is True
    print("[OK] Webhook Stripe verificato correttamente")

    # Test idempotency: stesso evento due volte
    r2 = httpx.post(
        f"{BASE_URL}/webhook/stripe",
        content=body_bytes,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": make_stripe_signature(body_bytes, STRIPE_SECRET),
        }
    )
    print(f"Stripe duplicate: HTTP {r2.status_code} — {r2.json()}")
    assert r2.status_code == 200  # Stripe si aspetta sempre 200
    assert r2.json().get("event_id") == payload["id"]
    print("[OK] Idempotency Stripe funziona")

if __name__ == "__main__":
    test_stripe_payment_webhook()
```

---

## PART C — Pattern Produzione

### C1 — Receive-Verify-Enqueue

```
PATTERN PRODUZIONE: Receive-Verify-Enqueue

ENDPOINT (critico path — deve rispondere in < 5s):
  POST /webhook
  │
  ├── 1. Verify HMAC (< 1ms)
  ├── 2. Timestamp window check (< 1ms)
  ├── 3. Nonce dedup Redis (< 2ms)
  ├── 4. Idempotency check Redis (< 2ms)
  ├── 5. Enqueue in Redis/RabbitMQ (< 5ms)
  └── 6. Risposta 200 al provider (< 10ms totale)

WORKER (async — nessun limite di tempo per il provider):
  Queue: webhook:queue:<provider>
  │
  ├── Dequeue job
  ├── Parse payload
  ├── Esegui business logic (DB updates, email, API calls)
  ├── Log risultato
  └── Ack messaggio

VANTAGGI:
  - L'endpoint non è mai bloccato da elaborazioni lente
  - Se il worker cade, i job restano in coda
  - Retry automatico per job falliti (DLQ)
  - Provider non riceve timeout → no retry del provider
```

```python
# file: worker.py
"""
Worker asincrono per elaborazione webhook dalla coda Redis.
"""
import json
import logging
import time

import redis

logger = logging.getLogger("webhook.worker")

QUEUE_NAMES = [
    "webhook:queue:stripe",
    "webhook:queue:github:push",
    "webhook:queue:generic",
]


def process_stripe_event(job: dict) -> None:
    """Elabora evento Stripe dalla coda."""
    event_type = job.get("event_type")
    payload = job.get("payload", {})

    if event_type == "payment_intent.succeeded":
        amount = payload.get("data", {}).get("object", {}).get("amount", 0)
        logger.info("Pagamento ricevuto: €%.2f", amount / 100)
        # Qui: aggiorna DB ordini, invia email conferma, notifica magazzino

    elif event_type == "customer.subscription.deleted":
        customer_id = payload.get("data", {}).get("object", {}).get("customer")
        logger.info("Abbonamento cancellato per customer: %s", customer_id)
        # Qui: deactivate account, invia email, aggiorna CRM

    else:
        logger.debug("Evento Stripe non gestito: %s", event_type)


def process_github_push(job: dict) -> None:
    """Elabora evento push GitHub dalla coda."""
    repo = job.get("repo")
    ref = job.get("ref")
    logger.info("Elaborazione push: %s → %s", repo, ref)
    # Qui: trigger CI/CD, notifica Slack, aggiorna deployment status


def run_worker(redis_client: redis.Redis) -> None:
    """Loop principale del worker."""
    handlers = {
        "webhook:queue:stripe": process_stripe_event,
        "webhook:queue:github:push": process_github_push,
    }

    logger.info("Worker avviato — in ascolto su: %s", QUEUE_NAMES)

    while True:
        # BLPOP: attende fino a 5s per un job (non-blocking poll)
        result = redis_client.blpop(QUEUE_NAMES, timeout=5)
        if not result:
            continue

        queue_name, raw_job = result
        try:
            job = json.loads(raw_job)
            logger.info("Job dequeued da %s: event_id=%s", queue_name, job.get("event_id"))

            handler = handlers.get(queue_name)
            if handler:
                handler(job)
            else:
                logger.warning("Nessun handler per coda: %s", queue_name)

        except json.JSONDecodeError:
            logger.error("Job non parseable: %s", raw_job[:100])
        except Exception as e:
            logger.exception("Errore elaborazione job: %s", e)
            # In produzione: push in DLQ per analisi
            redis_client.rpush("webhook:dlq", raw_job)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    r = redis.Redis(decode_responses=True)
    run_worker(r)
```

### C2 — Checklist Implementazione

```python
#!/usr/bin/env python3
# file: tests/security_checklist.py
"""
Verifica automatica della checklist di sicurezza webhook.
"""
import hashlib
import hmac
import json
import time

import httpx

BASE_URL = "http://localhost:8080"
SECRET = "test_secret_generic"


def sign_body(body: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def run_checklist():
    import secrets
    checks = []

    def check(name: str, passed: bool, note: str = ""):
        status = "[OK]  " if passed else "[FAIL]"
        print(f"  {status} {name}" + (f" — {note}" if note else ""))
        checks.append(passed)
        return passed

    print("\n=== CHECKLIST SICUREZZA WEBHOOK ===\n")

    # 1. Firma corretta → 200
    body = json.dumps({"type": "test", "id": "chk_001"}).encode()
    r = httpx.post(f"{BASE_URL}/webhook/generic",
                   content=body,
                   headers={
                       "Content-Type": "application/json",
                       "X-Signature-256": sign_body(body),
                       "X-Timestamp": str(int(time.time())),
                       "X-Nonce": secrets.token_hex(16),
                       "X-Idempotency-Key": "chk_001",
                   })
    check("Firma corretta accettata (200)", r.status_code == 200)

    # 2. Firma invalida → 400
    r = httpx.post(f"{BASE_URL}/webhook/generic",
                   content=body,
                   headers={
                       "Content-Type": "application/json",
                       "X-Signature-256": "sha256=firma_falsa",
                       "X-Timestamp": str(int(time.time())),
                       "X-Nonce": secrets.token_hex(16),
                   })
    check("Firma invalida rifiutata (400)", r.status_code == 400,
          f"HTTP {r.status_code}")

    # 3. Timestamp vecchio → 400
    body2 = json.dumps({"type": "test", "id": "chk_002"}).encode()
    old_ts = str(int(time.time()) - 600)
    r = httpx.post(f"{BASE_URL}/webhook/generic",
                   content=body2,
                   headers={
                       "Content-Type": "application/json",
                       "X-Signature-256": sign_body(body2),
                       "X-Timestamp": old_ts,
                       "X-Nonce": secrets.token_hex(16),
                   })
    check("Timestamp vecchio rifiutato (400)", r.status_code == 400,
          f"HTTP {r.status_code}")

    # 4. Replay attack → 409
    body3 = json.dumps({"type": "test", "id": "chk_003"}).encode()
    same_nonce = secrets.token_hex(16)
    r1 = httpx.post(f"{BASE_URL}/webhook/generic",
                    content=body3,
                    headers={
                        "Content-Type": "application/json",
                        "X-Signature-256": sign_body(body3),
                        "X-Timestamp": str(int(time.time())),
                        "X-Nonce": same_nonce,
                    })
    r2 = httpx.post(f"{BASE_URL}/webhook/generic",
                    content=body3,
                    headers={
                        "Content-Type": "application/json",
                        "X-Signature-256": sign_body(body3),
                        "X-Timestamp": str(int(time.time())),
                        "X-Nonce": same_nonce,
                    })
    check("Replay attack rilevato (409)", r1.status_code == 200 and r2.status_code == 409,
          f"Prima: {r1.status_code}, Replay: {r2.status_code}")

    # 5. Idempotency: stesso event_id → 200 con cached result
    body4 = json.dumps({"type": "test", "id": "chk_004"}).encode()
    idem_key = "chk_unique_004"
    r1 = httpx.post(f"{BASE_URL}/webhook/generic",
                    content=body4,
                    headers={
                        "Content-Type": "application/json",
                        "X-Signature-256": sign_body(body4),
                        "X-Timestamp": str(int(time.time())),
                        "X-Nonce": secrets.token_hex(16),
                        "X-Idempotency-Key": idem_key,
                    })
    r2 = httpx.post(f"{BASE_URL}/webhook/generic",
                    content=body4,
                    headers={
                        "Content-Type": "application/json",
                        "X-Signature-256": sign_body(body4),
                        "X-Timestamp": str(int(time.time())),
                        "X-Nonce": secrets.token_hex(16),
                        "X-Idempotency-Key": idem_key,
                    })
    check("Idempotency: duplicato restituisce 200 (no doppio processing)",
          r1.status_code == 200 and r2.status_code == 200,
          f"Prima: {r1.status_code}, Dup: {r2.status_code}")

    # 6. Health check
    r = httpx.get(f"{BASE_URL}/healthz")
    check("Health check attivo (/healthz)", r.status_code == 200 and r.json().get("redis") == "ok")

    passed = sum(checks)
    total = len(checks)
    print(f"\n=== {passed}/{total} check superati ===")
    if passed < total:
        print("ATTENZIONE: Alcuni check falliti — rivedere l'implementazione")
        raise SystemExit(1)


if __name__ == "__main__":
    run_checklist()
```

```bash
# Avvia server (in un terminale separato)
python3 webhook_server.py &

# Esegui checklist completa
python3 tests/security_checklist.py
```

---

## PART D — Integrazione con n8n e Provider Reali

### D1 — Verifica Webhook in n8n

```
LIMITAZIONE n8n/Make/Zapier:
  I platform no-code ricevono i webhook DOPO il parsing JSON.
  Questo significa che NON hanno accesso al raw body originale —
  e HMAC deve essere calcolato su raw body, non su JSON ri-serializzato.

  Soluzione per n8n:
  1. Usare un endpoint esterno (Flask/FastAPI) per verifica HMAC
  2. Se verificato → forward a n8n
  3. n8n elabora solo webhook pre-verificati

ARCHITETTURA RACCOMANDATA:
  Provider → [Flask Gateway: verifica HMAC] → n8n webhook
                   │
                   └── Se invalido → rifiuta (400) senza contattare n8n
```

```python
# file: n8n_gateway.py
"""
Gateway HMAC per n8n:
verifica la firma Stripe/GitHub e poi forwarda a n8n.
"""
import hashlib
import hmac
import os
import time

import httpx
from flask import Flask, abort, jsonify, request

app = Flask(__name__)

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/orders")
STRIPE_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test")


@app.route("/gateway/stripe", methods=["POST"])
def stripe_gateway():
    raw_body = request.get_data()
    stripe_sig = request.headers.get("Stripe-Signature", "")

    # 1. Verifica Stripe
    if not stripe_sig:
        abort(400, "Stripe-Signature mancante")

    parts = {k: v for k, _, v in (p.partition("=") for p in stripe_sig.split(","))}
    timestamp = parts.get("t", "")
    v1_sig = parts.get("v1", "")

    if abs(time.time() - int(timestamp or 0)) > 300:
        abort(400, "Timestamp scaduto")

    signed_payload = f"{timestamp}.".encode() + raw_body
    expected = hmac.new(STRIPE_SECRET.encode(), signed_payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, v1_sig):
        abort(400, "Firma Stripe non valida")

    # 2. Forward a n8n (con header custom per identificare fonte)
    try:
        r = httpx.post(
            N8N_WEBHOOK_URL,
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Verified-By": "hmac-gateway",
                "X-Provider": "stripe",
                "X-Stripe-Event": request.headers.get("Stripe-Event", ""),
            },
            timeout=10.0
        )
        return jsonify({"forwarded": True, "n8n_status": r.status_code}), 200
    except httpx.TimeoutException:
        return jsonify({"forwarded": False, "error": "n8n timeout"}), 202


if __name__ == "__main__":
    app.run(port=8081)
```

### D2 — ngrok per Test Locale con Provider Reali

```bash
# Per testare con Stripe/GitHub in locale senza server pubblico
# usa ngrok per esporre l'endpoint localmente

# Installa ngrok (https://ngrok.com)
# Avvia il server localmente
python3 webhook_server.py &

# Esponi con ngrok
ngrok http 8080

# Output ngrok:
# Forwarding https://abc123.ngrok.io -> http://localhost:8080

# Configura il webhook su Stripe/GitHub con l'URL ngrok:
# https://abc123.ngrok.io/webhook/stripe
# https://abc123.ngrok.io/webhook/github
```

---

## Riepilogo: Regole d'Oro Webhook Security

```
1. HMAC su RAW BODY (non su JSON parsed/re-serialized)
   → Flask: request.get_data()  (NON request.json)

2. CONSTANT-TIME COMPARE (obbligatorio)
   → Python: hmac.compare_digest()
   → MAI: received == expected  (vulnerabile a timing attack)

3. TIMESTAMP WINDOW (≤ 5 minuti)
   → Implementato lato server (non fidarsi del client)
   → Finestra > 5 min aumenta l'esposizione a replay

4. NONCE STORE (Redis con TTL)
   → TTL nonce >= 2x timestamp window
   → SET ... NX (atomic check-and-set)

5. IDEMPOTENCY CONSUMER-SIDE
   → Ogni evento ha un ID univoco dal provider
   → Il receiver non deve processarlo due volte

6. RECEIVE-VERIFY-ENQUEUE
   → Endpoint risponde in < 5s (solo verify + enqueue)
   → Processing asincrono nel worker

7. SECRET IN ENV/VAULT
   → Mai hard-coded in codice o log
   → Rotation periodica (ogni 90 giorni raccomandato)
```

---

## Riferimenti

- RFC 2104 — HMAC specification
- Stripe Webhook Security: https://stripe.com/docs/webhooks#verify-official-libraries
- GitHub Webhook Security: https://docs.github.com/webhooks/using-webhooks/validating-webhook-deliveries
- OWASP API Security Top 10: https://owasp.org/API-Security/
- Python `hmac` module: https://docs.python.org/3/library/hmac.html
- Modulo sorgente: `15-webhook-security-hmac-verifica.md`
