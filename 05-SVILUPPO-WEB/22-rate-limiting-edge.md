---
corso: "Sviluppo Web Full-Stack"
fase: "7 — Architetture Avanzate"
modulo: 22
titolo: "Rate Limiting e Edge Computing per Applicazioni Web"
versione: "RFC 6585 / Cloudflare Workers / Vercel Edge Runtime"
livello: "Avanzato"
prerequisiti: ["10-nodejs", "14-sicurezza-web"]
obiettivi:
  - "Confrontare algoritmi di rate limiting (token bucket, sliding window, leaky bucket)"
  - "Implementare rate limiting distribuito con Redis e header standard"
  - "Progettare edge functions per geolocalizzazione, A/B testing e caching"
  - "Configurare protezione DDoS e WAF a livello edge"
  - "Gestire CDN caching con invalidazione selettiva"
tag: [rate-limiting, edge-computing, cdn, ddos, waf, cloudflare, vercel-edge]
---

# Rate Limiting e Edge Computing per Applicazioni Web

> **Modulo 22** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Confrontare algoritmi di rate limiting (token bucket, sliding window, leaky bucket)
> 2. Implementare rate limiting distribuito con Redis e header standard
> 3. Progettare edge functions per geolocalizzazione, A/B testing e caching
> 4. Configurare protezione DDoS e WAF a livello edge
> 5. Gestire CDN caching con invalidazione selettiva
>
> **Prerequisiti:** [Node.js](10-nodejs.md), [Sicurezza Web](14-sicurezza-web.md)
> **Tempo stimato:** 5-7 ore · **Livello:** Avanzato

---

## Indice

1. [Idee guida](#idee-guida)
2. [Algoritmi di rate limiting](#algoritmi-di-rate-limiting)
3. [Implementazione](#implementazione)
    - [Rate limiting distribuito con Redis Cluster](#rate-limiting-distribuito-con-redis-cluster)
4. [Dimensioni di rate limiting](#dimensioni-di-rate-limiting)
5. [Header HTTP per rate limiting](#header-http-per-rate-limiting)
6. [Design API rate limiting](#design-api-rate-limiting)
7. [Protezione DDoS](#protezione-ddos)
8. [Edge computing](#edge-computing)
9. [Limitazioni degli edge runtime](#limitazioni-degli-edge-runtime)
10. [Casi d'uso edge](#casi-duso-edge)
11. [CDN e caching all'edge](#cdn-e-caching-alledge)
12. [WAF — Web Application Firewall](#waf--web-application-firewall)
13. [Bot management](#bot-management)
14. [Rate limiting lato client e strategie di retry](#rate-limiting-lato-client-e-strategie-di-retry)
15. [Rate limiting per connessioni WebSocket](#rate-limiting-per-connessioni-websocket)
16. [Gestione quote API](#gestione-quote-api)
17. [Rate limiting nativo ai CDN edge](#rate-limiting-nativo-ai-cdn-edge)
18. [Rate limiting adattivo e mitigazione DDoS all'edge](#rate-limiting-adattivo-e-mitigazione-ddos-alledge)
19. [Monitoraggio e alerting avanzato](#monitoraggio-e-alerting-avanzato)
20. [Matrice decisionale](#matrice-decisionale)
22. [Troubleshooting](#troubleshooting)
23. [Strategie di testing per rate limiting](#strategie-di-testing-per-rate-limiting)
24. [FAQ](#faq)
25. [Esercizi](#esercizi)
26. [Letture e risorse](#letture-e-risorse)
27. [Glossario](#glossario)

---

## Idee guida

1. **Rate limit all'edge > all'origin.** Applicare limiti il più vicino possibile all'utente riduce latenza, carico sull'infrastruttura di backend e costi di elaborazione. Un reject a 429 dall'edge non attraversa mai il load balancer né raggiunge l'application server.

2. **Nessun algoritmo è universale.** Token bucket tollera burst; sliding window è più equo nel tempo; leaky bucket garantisce throughput costante. La scelta dipende dal profilo di traffico e dalla semantica dell'API.

3. **Rate limit multi-dimensionale.** Limitare solo per IP è insufficiente: utenti dietro NAT condividono IP, bot ruotano IP. Combinare IP, user ID, API key ed endpoint fornisce una difesa stratificata.

4. **Header `X-RateLimit-*` e `Retry-After` sono contratto con il client.** Senza questi header il client non sa quando riprovare e genera retry storm.

5. **Limiti differenziati per endpoint.** `/auth/login` deve essere molto più restrittivo di `/api/products`. Endpoint di scrittura più limitati di quelli di lettura.

6. **Edge computing non è solo CDN.** Cloudflare Workers, Vercel Edge Functions, Lambda@Edge e Deno Deploy consentono logica arbitraria — autenticazione, A/B testing, personalizzazione — a latenza sub-50ms.

7. **WAF e bot management complementano il rate limiting.** Rate limit da solo non basta: serve riconoscere pattern di abuso, fingerprinting, e challenge adattivi.

8. **Monitorare prima di bloccare.** Attivare rate limit in modalità log-only prima di enforcement evita falsi positivi su traffico legittimo.

---

## Algoritmi di rate limiting

### 1. Fixed Window Counter

L'algoritmo più semplice: si divide il tempo in finestre fisse (es. 1 minuto) e si conta ogni richiesta nella finestra corrente. Al termine della finestra il contatore si resetta a zero.

**Vantaggi:**
- Semplicissimo da implementare
- Basso overhead di memoria (un contatore per chiave)
- Facile da capire per chi consuma l'API

**Svantaggi:**
- Soffre del problema "boundary burst": un client può inviare il doppio delle richieste ammesse concentrandole a cavallo di due finestre consecutive (fine della finestra N + inizio della finestra N+1)
- Non è equo per tutti i punti della finestra temporale

**Diagramma concettuale:**

```
Finestra 1 (00:00 - 00:59)    Finestra 2 (01:00 - 01:59)
┌──────────────────────────┐   ┌──────────────────────────┐
│ req req req req req       │   │ req req                   │
│ count = 5                 │   │ count = 2                 │
│ limit = 10 → OK           │   │ limit = 10 → OK           │
└──────────────────────────┘   └──────────────────────────┘

Problema boundary burst:
  ... 8 req a 00:58-00:59 + 10 req a 01:00-01:01 = 18 req in 2 secondi!
```

**Implementazione TypeScript:**

```typescript
interface FixedWindowState {
  count: number;
  windowStart: number;
}

class FixedWindowRateLimiter {
  private windows: Map<string, FixedWindowState> = new Map();

  constructor(
    private readonly maxRequests: number,
    private readonly windowSizeMs: number,
  ) {}

  check(key: string): { allowed: boolean; remaining: number; resetAt: number } {
    const now = Date.now();
    const windowStart = Math.floor(now / this.windowSizeMs) * this.windowSizeMs;
    const resetAt = windowStart + this.windowSizeMs;

    const state = this.windows.get(key);

    // Nuova finestra o finestra scaduta
    if (!state || state.windowStart !== windowStart) {
      this.windows.set(key, { count: 1, windowStart });
      return { allowed: true, remaining: this.maxRequests - 1, resetAt };
    }

    if (state.count >= this.maxRequests) {
      return { allowed: false, remaining: 0, resetAt };
    }

    state.count += 1;
    return {
      allowed: true,
      remaining: this.maxRequests - state.count,
      resetAt,
    };
  }

  /** Pulizia periodica delle finestre scadute */
  cleanup(): void {
    const now = Date.now();
    const currentWindow = Math.floor(now / this.windowSizeMs) * this.windowSizeMs;
    for (const [key, state] of this.windows) {
      if (state.windowStart < currentWindow) {
        this.windows.delete(key);
      }
    }
  }
}

// Utilizzo
const limiter = new FixedWindowRateLimiter(100, 60_000); // 100 req/min
const result = limiter.check('192.168.1.1');
if (!result.allowed) {
  // Rispondere con 429
}
```

---

### 2. Sliding Window Log

Tiene traccia del timestamp esatto di ogni richiesta in un log ordinato. Per verificare il limite, conta le richieste nel log che cadono nell'intervallo `[now - windowSize, now]`.

**Vantaggi:**
- Precisione perfetta: nessun boundary burst
- Comportamento equo indipendente dal momento della richiesta

**Svantaggi:**
- Alto consumo di memoria: O(n) per client dove n è il numero di richieste ammesse
- Richiede ordinamento e scansione ad ogni check

**Implementazione TypeScript:**

```typescript
class SlidingWindowLogLimiter {
  private logs: Map<string, number[]> = new Map();

  constructor(
    private readonly maxRequests: number,
    private readonly windowSizeMs: number,
  ) {}

  check(key: string): { allowed: boolean; remaining: number; retryAfterMs: number } {
    const now = Date.now();
    const windowStart = now - this.windowSizeMs;

    let timestamps = this.logs.get(key);
    if (!timestamps) {
      timestamps = [];
      this.logs.set(key, timestamps);
    }

    // Rimuovi timestamp fuori dalla finestra
    while (timestamps.length > 0 && timestamps[0] <= windowStart) {
      timestamps.shift();
    }

    if (timestamps.length >= this.maxRequests) {
      // Calcola quando la prossima richiesta sarà ammessa
      const oldestInWindow = timestamps[0];
      const retryAfterMs = oldestInWindow + this.windowSizeMs - now;
      return { allowed: false, remaining: 0, retryAfterMs };
    }

    timestamps.push(now);
    return {
      allowed: true,
      remaining: this.maxRequests - timestamps.length,
      retryAfterMs: 0,
    };
  }

  cleanup(): void {
    const cutoff = Date.now() - this.windowSizeMs;
    for (const [key, timestamps] of this.logs) {
      const filtered = timestamps.filter((t) => t > cutoff);
      if (filtered.length === 0) {
        this.logs.delete(key);
      } else {
        this.logs.set(key, filtered);
      }
    }
  }
}
```

---

### 3. Sliding Window Counter

Un compromesso tra fixed window (bassa memoria) e sliding window log (alta precisione). Mantiene contatori per la finestra corrente e quella precedente, poi interpola linearmente in base a quanto si è avanzato nella finestra corrente.

**Formula:**

```
peso_finestra_precedente = 1 - (elapsed_in_current_window / window_size)
conteggio_stimato = (count_prev * peso_finestra_precedente) + count_current
```

**Vantaggi:**
- Memoria costante: solo due contatori per chiave
- Buona approssimazione, elimina la maggior parte dei boundary burst
- Ideale per sistemi distribuiti (pochi dati da sincronizzare)

**Svantaggi:**
- Non è perfettamente preciso: è una stima pesata

**Implementazione TypeScript:**

```typescript
interface SlidingWindowCounterState {
  prevCount: number;
  prevWindowStart: number;
  currCount: number;
  currWindowStart: number;
}

class SlidingWindowCounterLimiter {
  private states: Map<string, SlidingWindowCounterState> = new Map();

  constructor(
    private readonly maxRequests: number,
    private readonly windowSizeMs: number,
  ) {}

  check(key: string): { allowed: boolean; remaining: number; resetAt: number } {
    const now = Date.now();
    const currWindowStart = Math.floor(now / this.windowSizeMs) * this.windowSizeMs;
    const prevWindowStart = currWindowStart - this.windowSizeMs;

    let state = this.states.get(key);

    if (!state) {
      state = { prevCount: 0, prevWindowStart, currCount: 0, currWindowStart };
      this.states.set(key, state);
    }

    // Se siamo entrati in una nuova finestra, ruota i contatori
    if (state.currWindowStart !== currWindowStart) {
      if (currWindowStart - state.currWindowStart >= this.windowSizeMs * 2) {
        // Due o più finestre fa: azzera tutto
        state.prevCount = 0;
        state.currCount = 0;
      } else {
        state.prevCount = state.currCount;
        state.currCount = 0;
      }
      state.prevWindowStart = state.currWindowStart;
      state.currWindowStart = currWindowStart;
    }

    // Calcola peso della finestra precedente
    const elapsedInCurrent = now - currWindowStart;
    const prevWeight = 1 - elapsedInCurrent / this.windowSizeMs;

    const estimatedCount = state.prevCount * prevWeight + state.currCount;

    if (estimatedCount >= this.maxRequests) {
      return {
        allowed: false,
        remaining: 0,
        resetAt: currWindowStart + this.windowSizeMs,
      };
    }

    state.currCount += 1;
    const newEstimate = state.prevCount * prevWeight + state.currCount;
    return {
      allowed: true,
      remaining: Math.max(0, Math.floor(this.maxRequests - newEstimate)),
      resetAt: currWindowStart + this.windowSizeMs,
    };
  }
}
```

---

### 4. Token Bucket

Ogni client ha un "secchio" con un numero massimo di token. Ogni richiesta consuma un token. I token vengono aggiunti a un tasso fisso (refill rate). Se il secchio è vuoto, la richiesta è rifiutata.

**Vantaggi:**
- Tollera burst naturali: un client inattivo accumula token
- Parametri intuitivi: capacità del bucket (burst) e tasso di riempimento (sustained)
- Standard de facto per API commerciali (Stripe, GitHub, AWS)

**Svantaggi:**
- Richiede tracking dello stato per client (ultimo refill, token rimanenti)
- Più complesso di fixed window

**Diagramma:**

```
Bucket capacity = 10 tokens
Refill rate = 2 tokens/sec

t=0   [■■■■■■■■■■] 10 tokens  → 5 richieste → [■■■■■_____]  5 tokens
t=1   [■■■■■■■___]  7 tokens  → refill +2
t=2   [■■■■■■■■■_]  9 tokens  → refill +2, cap a 10
t=3   [■■■■■■■■■■] 10 tokens  → burst di 10 → [__________]  0 tokens
t=3.1 richiesta → RIFIUTATA (bucket vuoto, retry tra 500ms)
```

**Implementazione TypeScript:**

```typescript
interface TokenBucketState {
  tokens: number;
  lastRefillTime: number;
}

class TokenBucketRateLimiter {
  private buckets: Map<string, TokenBucketState> = new Map();

  constructor(
    private readonly capacity: number,
    private readonly refillRatePerSec: number,
  ) {}

  check(key: string, tokensRequired: number = 1): {
    allowed: boolean;
    remaining: number;
    retryAfterMs: number;
  } {
    const now = Date.now();
    let state = this.buckets.get(key);

    if (!state) {
      state = { tokens: this.capacity, lastRefillTime: now };
      this.buckets.set(key, state);
    }

    // Calcola token da aggiungere dal refill
    const elapsedMs = now - state.lastRefillTime;
    const tokensToAdd = (elapsedMs / 1000) * this.refillRatePerSec;
    state.tokens = Math.min(this.capacity, state.tokens + tokensToAdd);
    state.lastRefillTime = now;

    if (state.tokens < tokensRequired) {
      // Calcola quando ci saranno abbastanza token
      const deficit = tokensRequired - state.tokens;
      const retryAfterMs = Math.ceil((deficit / this.refillRatePerSec) * 1000);
      return { allowed: false, remaining: 0, retryAfterMs };
    }

    state.tokens -= tokensRequired;
    return {
      allowed: true,
      remaining: Math.floor(state.tokens),
      retryAfterMs: 0,
    };
  }
}

// Utilizzo: 100 token di capacità, 10 token/sec di refill
const limiter = new TokenBucketRateLimiter(100, 10);

// Richiesta pesante che costa 5 token (es. batch API)
const result = limiter.check('user:42', 5);
```

---

### 5. Leaky Bucket

Modello complementare al token bucket. Le richieste entrano in una coda (bucket) e vengono processate a un tasso fisso. Se la coda è piena, le nuove richieste vengono scartate. Garantisce un tasso di uscita costante.

**Vantaggi:**
- Output rate perfettamente costante, ideale per API che non tollerano burst
- Smoothing naturale del traffico
- Semplice da ragionare: "massimo N richieste al secondo, sempre"

**Svantaggi:**
- Non tollera burst legittimi: penalizza pattern di traffico "bursty" ma legittimi
- La coda introduce latenza aggiuntiva
- Meno adatto ad API consumer-facing dove gli utenti si aspettano risposte immediate

**Implementazione TypeScript:**

```typescript
interface LeakyBucketState {
  queueSize: number;
  lastLeakTime: number;
}

class LeakyBucketRateLimiter {
  private buckets: Map<string, LeakyBucketState> = new Map();

  constructor(
    private readonly capacity: number,      // dimensione massima della coda
    private readonly leakRatePerSec: number, // richieste processate al secondo
  ) {}

  check(key: string): {
    allowed: boolean;
    remaining: number;
    retryAfterMs: number;
  } {
    const now = Date.now();
    let state = this.buckets.get(key);

    if (!state) {
      state = { queueSize: 0, lastLeakTime: now };
      this.buckets.set(key, state);
    }

    // "Svuota" il bucket in base al tempo trascorso
    const elapsedMs = now - state.lastLeakTime;
    const leaked = (elapsedMs / 1000) * this.leakRatePerSec;
    state.queueSize = Math.max(0, state.queueSize - leaked);
    state.lastLeakTime = now;

    if (state.queueSize >= this.capacity) {
      const retryAfterMs = Math.ceil(
        ((state.queueSize - this.capacity + 1) / this.leakRatePerSec) * 1000,
      );
      return { allowed: false, remaining: 0, retryAfterMs };
    }

    state.queueSize += 1;
    return {
      allowed: true,
      remaining: Math.floor(this.capacity - state.queueSize),
      retryAfterMs: 0,
    };
  }
}

// 50 slot di coda, 10 richieste al secondo processate
const leaky = new LeakyBucketRateLimiter(50, 10);
```

---

### 6. GCRA (Generic Cell Rate Algorithm)

Il GCRA è una variante elegante del leaky bucket originata dalla tecnologia ATM (Asynchronous Transfer Mode, RFC 2212). La sua caratteristica distintiva è l'efficienza: traccia solo un singolo timestamp per client (il TAT — Theoretical Arrival Time), dimezzando il consumo di memoria rispetto al leaky bucket classico che necessita di timestamp e contatore della coda.

**Principio di funzionamento:**

Il GCRA calcola l'intervallo di emissione `T = period / limit` (il tempo minimo tra due richieste conformi). Quando arriva una richiesta, l'algoritmo confronta il momento corrente con il TAT:

- Se `now >= TAT`: la richiesta è conforme. Il nuovo TAT diventa `max(now, TAT) + T`.
- Se `now < TAT - burst_tolerance`: la richiesta è non conforme (il client sta inviando troppo velocemente).
- Se `TAT - burst_tolerance <= now < TAT`: la richiesta è conforme (entro la tolleranza burst). Il nuovo TAT avanza di `T`.

```
Emission Interval T = 60s / 10 = 6s (10 req/min)
Burst tolerance τ = T * burst_capacity = 6s * 5 = 30s

Richiesta 1 (t=0):   TAT=0, now=0  → now >= TAT ✓  → nuovo TAT = 0 + 6 = 6
Richiesta 2 (t=1):   TAT=6, now=1  → TAT-τ=-24 ≤ 1 < 6 ✓ (burst) → TAT = 6+6 = 12
Richiesta 3 (t=2):   TAT=12, now=2 → TAT-τ=-18 ≤ 2 < 12 ✓ (burst) → TAT = 12+6 = 18
...
Richiesta 6 (t=3):   TAT=36, now=3 → TAT-τ=6 > 3 ✗ → RIFIUTATA (troppo burst)
```

**Vantaggi:**
- Memoria minima: un solo timestamp per client (vs timestamp + contatore del leaky bucket)
- Nessuna struttura dati complessa: niente code, niente sorted set
- Implementazione Redis in un'unica chiave con `GET` + `SET`
- Naturalmente adatto a rate limiting distribuito (una chiave, un'operazione atomica)
- Precisione equivalente al leaky bucket

**Svantaggi:**
- Meno intuitivo concettualmente rispetto al token bucket
- Il calcolo del TAT richiede aritmetica temporale precisa
- Debug più complesso: il "remaining" richiede calcolo inverso dal TAT

**Implementazione TypeScript:**

```typescript
interface GcraState {
  tat: number; // Theoretical Arrival Time in ms
}

class GcraRateLimiter {
  private states: Map<string, GcraState> = new Map();
  private readonly emissionIntervalMs: number;
  private readonly burstToleranceMs: number;

  constructor(
    private readonly limit: number,       // richieste per periodo
    private readonly periodMs: number,     // durata del periodo
    private readonly burstCapacity: number, // richieste burst extra
  ) {
    this.emissionIntervalMs = periodMs / limit;
    this.burstToleranceMs = this.emissionIntervalMs * burstCapacity;
  }

  check(key: string): {
    allowed: boolean;
    remaining: number;
    retryAfterMs: number;
  } {
    const now = Date.now();
    const state = this.states.get(key);
    const tat = state?.tat ?? now; // Prima richiesta: TAT = now

    // Aggiusta TAT: non può essere nel passato lontano
    const adjustedTat = Math.max(tat, now);

    // Verifica conformità
    const newTat = adjustedTat + this.emissionIntervalMs;
    const allowAt = newTat - this.burstToleranceMs - this.emissionIntervalMs;

    if (now < allowAt) {
      // Non conforme: troppo presto
      const retryAfterMs = Math.ceil(allowAt - now);
      const remaining = 0;
      return { allowed: false, remaining, retryAfterMs };
    }

    // Conforme: aggiorna TAT
    this.states.set(key, { tat: newTat });

    // Calcola remaining: quante richieste possono ancora essere fatte
    // prima di raggiungere il limite burst
    const remainingMs = this.burstToleranceMs - (newTat - now);
    const remaining = Math.max(0, Math.floor(remainingMs / this.emissionIntervalMs));

    return { allowed: true, remaining, retryAfterMs: 0 };
  }

  cleanup(): void {
    const now = Date.now();
    for (const [key, state] of this.states) {
      if (now - state.tat > this.periodMs * 2) {
        this.states.delete(key);
      }
    }
  }
}

// Utilizzo: 100 req/min con burst di 20
const gcra = new GcraRateLimiter(100, 60_000, 20);
const result = gcra.check('user:42');
```

**Implementazione Redis (Lua script atomico):**

Il GCRA è particolarmente efficiente in Redis perché opera su una singola chiave.

```typescript
const LUA_GCRA = `
  local key = KEYS[1]
  local emission_interval = tonumber(ARGV[1])  -- ms tra richieste
  local burst_tolerance = tonumber(ARGV[2])     -- ms di tolleranza burst
  local now = tonumber(ARGV[3])                 -- timestamp corrente in ms
  local ttl_seconds = tonumber(ARGV[4])         -- TTL della chiave

  local tat = tonumber(redis.call('GET', key) or now)

  -- Aggiusta: TAT non può essere nel passato
  if tat < now then
    tat = now
  end

  local new_tat = tat + emission_interval
  local allow_at = new_tat - burst_tolerance - emission_interval

  if now < allow_at then
    -- Non conforme
    local retry_after = math.ceil((allow_at - now) / 1000)
    return {0, 0, retry_after}
  end

  -- Conforme: aggiorna TAT
  redis.call('SET', key, new_tat, 'PX', ttl_seconds * 1000)

  -- Calcola remaining
  local remaining_ms = burst_tolerance - (new_tat - now)
  local remaining = math.max(0, math.floor(remaining_ms / emission_interval))

  return {1, remaining, 0}
`;
```

Il GCRA è usato in produzione da servizi come Stripe (per il loro rate limiting interno) e Shopify. È particolarmente adatto quando la memoria per client è un vincolo critico, come nei sistemi con milioni di chiavi attive.

---

## Implementazione

### In-memory

Adatto a singola istanza o sviluppo locale. Le implementazioni sopra utilizzano `Map` in-memory. Limitazioni critiche:

- **Non condiviso tra processi:** ogni worker/istanza ha il proprio stato. Un utente può ottenere N × il limite se ci sono N istanze.
- **Perdita allo restart:** tutti i contatori si azzerano al riavvio.
- **Crescita di memoria:** senza cleanup periodico, le entry scadute accumulano.

**Pattern di cleanup con `setInterval`:**

```typescript
class InMemoryRateLimitStore {
  private store: Map<string, { count: number; expiresAt: number }> = new Map();
  private cleanupTimer: ReturnType<typeof setInterval>;

  constructor(cleanupIntervalMs: number = 60_000) {
    this.cleanupTimer = setInterval(() => this.cleanup(), cleanupIntervalMs);
  }

  increment(key: string, windowMs: number): { count: number; expiresAt: number } {
    const now = Date.now();
    const existing = this.store.get(key);

    if (existing && existing.expiresAt > now) {
      existing.count += 1;
      return { count: existing.count, expiresAt: existing.expiresAt };
    }

    const entry = { count: 1, expiresAt: now + windowMs };
    this.store.set(key, entry);
    return entry;
  }

  private cleanup(): void {
    const now = Date.now();
    for (const [key, val] of this.store) {
      if (val.expiresAt <= now) {
        this.store.delete(key);
      }
    }
  }

  destroy(): void {
    clearInterval(this.cleanupTimer);
    this.store.clear();
  }
}
```

---

### Redis-based: INCR + EXPIRE

Il pattern classico per rate limiting distribuito. Usa `INCR` atomico per incrementare il contatore e `EXPIRE` per auto-pulizia.

```typescript
import { Redis } from 'ioredis';

class RedisFixedWindowLimiter {
  constructor(
    private readonly redis: Redis,
    private readonly maxRequests: number,
    private readonly windowSizeSeconds: number,
  ) {}

  async check(key: string): Promise<{
    allowed: boolean;
    remaining: number;
    resetAt: number;
  }> {
    const redisKey = `ratelimit:${key}`;
    const now = Math.floor(Date.now() / 1000);
    const windowStart = Math.floor(now / this.windowSizeSeconds) * this.windowSizeSeconds;
    const windowKey = `${redisKey}:${windowStart}`;

    // MULTI per atomicità
    const pipeline = this.redis.pipeline();
    pipeline.incr(windowKey);
    pipeline.expire(windowKey, this.windowSizeSeconds + 1); // +1 per sicurezza

    const results = await pipeline.exec();
    if (!results) {
      throw new Error('Redis pipeline returned null');
    }

    const count = results[0][1] as number;
    const resetAt = (windowStart + this.windowSizeSeconds) * 1000;

    return {
      allowed: count <= this.maxRequests,
      remaining: Math.max(0, this.maxRequests - count),
      resetAt,
    };
  }
}
```

**Attenzione alla race condition INCR/EXPIRE:** se il processo crasha tra `INCR` e `EXPIRE`, la chiave resta senza TTL. Soluzione: usare un Lua script atomico.

```typescript
const LUA_FIXED_WINDOW = `
  local key = KEYS[1]
  local limit = tonumber(ARGV[1])
  local window = tonumber(ARGV[2])

  local current = redis.call('INCR', key)
  if current == 1 then
    redis.call('EXPIRE', key, window)
  end

  if current > limit then
    return {0, 0, redis.call('TTL', key)}
  end

  return {1, limit - current, redis.call('TTL', key)}
`;

class RedisLuaLimiter {
  constructor(
    private readonly redis: Redis,
    private readonly maxRequests: number,
    private readonly windowSizeSeconds: number,
  ) {
    this.redis.defineCommand('rateLimit', {
      numberOfKeys: 1,
      lua: LUA_FIXED_WINDOW,
    });
  }

  async check(key: string): Promise<{
    allowed: boolean;
    remaining: number;
    ttl: number;
  }> {
    const result = await (this.redis as any).rateLimit(
      `ratelimit:${key}`,
      this.maxRequests,
      this.windowSizeSeconds,
    );

    return {
      allowed: result[0] === 1,
      remaining: result[1],
      ttl: result[2],
    };
  }
}
```

---

### Redis-based: Sorted Sets (Sliding Window Log)

Usa `ZADD` con timestamp come score per implementare sliding window log in Redis. Più preciso del fixed window, ma con costo O(log N) per operazione.

```typescript
class RedisSlidingWindowLimiter {
  constructor(
    private readonly redis: Redis,
    private readonly maxRequests: number,
    private readonly windowSizeMs: number,
  ) {}

  async check(key: string): Promise<{
    allowed: boolean;
    remaining: number;
    retryAfterMs: number;
  }> {
    const now = Date.now();
    const windowStart = now - this.windowSizeMs;
    const redisKey = `ratelimit:sw:${key}`;
    const member = `${now}:${Math.random().toString(36).slice(2, 10)}`;

    const pipeline = this.redis.pipeline();
    // Rimuovi entry scadute
    pipeline.zremrangebyscore(redisKey, '-inf', windowStart);
    // Aggiungi la richiesta corrente
    pipeline.zadd(redisKey, now, member);
    // Conta le richieste nella finestra
    pipeline.zcard(redisKey);
    // Imposta TTL per auto-pulizia
    pipeline.pexpire(redisKey, this.windowSizeMs);

    const results = await pipeline.exec();
    if (!results) {
      throw new Error('Redis pipeline returned null');
    }

    const count = results[2][1] as number;

    if (count > this.maxRequests) {
      // Rimuovi la richiesta appena aggiunta (è stata rifiutata)
      await this.redis.zrem(redisKey, member);

      // Trova il timestamp più vecchio per calcolare retry
      const oldest = await this.redis.zrange(redisKey, 0, 0, 'WITHSCORES');
      const retryAfterMs =
        oldest.length >= 2
          ? Number(oldest[1]) + this.windowSizeMs - now
          : this.windowSizeMs;

      return { allowed: false, remaining: 0, retryAfterMs };
    }

    return {
      allowed: true,
      remaining: this.maxRequests - count,
      retryAfterMs: 0,
    };
  }
}
```

---

### Rate limiting distribuito

In un'architettura multi-region con più istanze, sincronizzare lo stato di rate limiting è la sfida principale.

**Strategie:**

| Strategia | Pro | Contro |
|---|---|---|
| **Redis centralizzato** | Stato unico, coerente | Latenza cross-region, SPOF |
| **Redis per region + sync asincrono** | Bassa latenza locale | Eventual consistency, possibile over-count |
| **CRDT counter** | Merge senza conflitti, AP del CAP | Complessità implementativa |
| **Local + periodic flush** | Latenza zero per check | Limiti imprecisi tra flush |
| **Sticky sessions per region** | Stato locale è sufficiente | Vincolato al routing |

**Pattern: local counter con sync periodico a Redis centrale:**

```typescript
class DistributedRateLimiter {
  private localCounts: Map<string, number> = new Map();
  private syncTimer: ReturnType<typeof setInterval>;

  constructor(
    private readonly redis: Redis,
    private readonly maxRequests: number,
    private readonly windowSizeSeconds: number,
    private readonly regionId: string,
    syncIntervalMs: number = 5_000,
  ) {
    this.syncTimer = setInterval(() => this.syncToRedis(), syncIntervalMs);
  }

  /** Check locale veloce + margine conservativo */
  async check(key: string): Promise<{ allowed: boolean; remaining: number }> {
    const localCount = this.localCounts.get(key) ?? 0;

    // Controlla il totale globale periodicamente
    const globalKey = `ratelimit:global:${key}`;
    const globalCount = Number(await this.redis.get(globalKey)) || 0;

    const totalEstimate = globalCount + localCount;

    if (totalEstimate >= this.maxRequests) {
      return { allowed: false, remaining: 0 };
    }

    this.localCounts.set(key, localCount + 1);
    return {
      allowed: true,
      remaining: Math.max(0, this.maxRequests - totalEstimate - 1),
    };
  }

  /** Flush dei contatori locali verso Redis */
  private async syncToRedis(): Promise<void> {
    const pipeline = this.redis.pipeline();

    for (const [key, count] of this.localCounts) {
      if (count > 0) {
        const globalKey = `ratelimit:global:${key}`;
        pipeline.incrby(globalKey, count);
        pipeline.expire(globalKey, this.windowSizeSeconds + 10);
      }
    }

    await pipeline.exec();
    this.localCounts.clear();
  }

  destroy(): void {
    clearInterval(this.syncTimer);
  }
}
```

---

### Rate limiting distribuito con Redis Cluster

Redis Cluster partiziona i dati in 16384 hash slot distribuiti su più nodi. Questo introduce vincoli specifici per il rate limiting: i Lua script atomici possono operare solo su chiavi che risiedono nello stesso hash slot. Se le chiavi del rate limiter finiscono su nodi diversi, lo script fallisce con `CROSSSLOT` error.

**Il problema CROSSSLOT:**

```
// ERRORE: queste due chiavi possono finire su slot diversi
EVAL "local a = redis.call('GET', KEYS[1]); local b = redis.call('GET', KEYS[2])" 2
  "ratelimit:user42:current" "ratelimit:user42:previous"
// → CROSSSLOT Keys in request don't hash to the same slot
```

**Soluzione: Hash Tags**

I Redis Hash Tags `{...}` forzano la parte tra parentesi come unico input per il calcolo dello hash slot. Tutte le chiavi con lo stesso hash tag finiscono sullo stesso nodo.

```typescript
/**
 * Sliding Window Counter su Redis Cluster con hash tags.
 * Tutte le chiavi per lo stesso client usano {userId} come hash tag.
 */
const LUA_SLIDING_WINDOW_CLUSTER = `
  local curr_key = KEYS[1]    -- ratelimit:{user42}:current
  local prev_key = KEYS[2]    -- ratelimit:{user42}:previous
  local limit = tonumber(ARGV[1])
  local window = tonumber(ARGV[2])
  local now = tonumber(ARGV[3])

  local curr_window = math.floor(now / window) * window
  local prev_window = curr_window - window
  local elapsed = now - curr_window

  -- Rotazione finestre: se la finestra corrente è cambiata
  local stored_window = tonumber(redis.call('HGET', curr_key, 'window') or '0')
  if stored_window ~= curr_window then
    -- Copia il conteggio corrente nel precedente
    local curr_count = tonumber(redis.call('HGET', curr_key, 'count') or '0')
    redis.call('HSET', prev_key, 'count', curr_count, 'window', stored_window)
    redis.call('EXPIRE', prev_key, window * 2 / 1000)
    redis.call('HSET', curr_key, 'count', 0, 'window', curr_window)
  end

  -- Calcola conteggio stimato con interpolazione
  local prev_count = tonumber(redis.call('HGET', prev_key, 'count') or '0')
  local curr_count = tonumber(redis.call('HGET', curr_key, 'count') or '0')
  local prev_weight = 1 - (elapsed / window)
  local estimated = prev_count * prev_weight + curr_count

  if estimated >= limit then
    return {0, 0, math.ceil((curr_window + window - now) / 1000)}
  end

  -- Incrementa
  redis.call('HINCRBY', curr_key, 'count', 1)
  redis.call('EXPIRE', curr_key, window * 2 / 1000)

  return {1, math.floor(limit - estimated - 1), math.ceil((curr_window + window - now) / 1000)}
`;

class RedisClusterRateLimiter {
  constructor(
    private readonly redis: Redis, // ioredis con cluster mode
    private readonly maxRequests: number,
    private readonly windowMs: number,
  ) {
    this.redis.defineCommand('clusterRateLimit', {
      numberOfKeys: 2,
      lua: LUA_SLIDING_WINDOW_CLUSTER,
    });
  }

  async check(identifier: string): Promise<{
    allowed: boolean;
    remaining: number;
    ttl: number;
  }> {
    // Hash tag: {identifier} garantisce same-slot
    const currKey = `ratelimit:{${identifier}}:current`;
    const prevKey = `ratelimit:{${identifier}}:previous`;

    const result = await (this.redis as any).clusterRateLimit(
      currKey,
      prevKey,
      this.maxRequests,
      this.windowMs,
      Date.now(),
    );

    return {
      allowed: result[0] === 1,
      remaining: result[1],
      ttl: result[2],
    };
  }
}
```

**Best practice per Redis Cluster e rate limiting:**

| Pratica | Motivo |
|---|---|
| Usare hash tags `{userId}` per tutte le chiavi di uno stesso utente | Evita CROSSSLOT in Lua script |
| Evitare operazioni multi-chiave cross-slot | Lua script atomico richiede same-slot |
| Monitorare la distribuzione degli hash slot | Hotspot se molti utenti attivi finiscono sullo stesso nodo |
| Usare `CLUSTER KEYSLOT` per debug | Verifica che le chiavi finiscano dove previsto |
| Limitare la complessità del Lua script | Redis Cluster esegue lo script su un singolo nodo, bloccando quel nodo |
| Impostare TTL su tutte le chiavi | Senza TTL le chiavi crescono indefinitamente; con hash tag il cleanup non è automatico |

---

## Dimensioni di rate limiting

Il rate limiting efficace opera su più dimensioni contemporaneamente. Ogni dimensione intercetta un tipo diverso di abuso.

### Per IP

```typescript
function getClientIp(request: Request): string {
  // Ordine di priorità header, dal più affidabile al meno
  const cfConnectingIp = request.headers.get('cf-connecting-ip');
  if (cfConnectingIp) return cfConnectingIp;

  const xForwardedFor = request.headers.get('x-forwarded-for');
  if (xForwardedFor) {
    // Prendi il PRIMO IP (client originale) solo se il proxy è trusted
    return xForwardedFor.split(',')[0].trim();
  }

  const xRealIp = request.headers.get('x-real-ip');
  if (xRealIp) return xRealIp;

  // Fallback: IP della connessione diretta (varia per runtime)
  return 'unknown';
}
```

**Cautele:**
- `X-Forwarded-For` è spoofabile se il primo proxy non lo sanitizza
- Utenti dietro CGNAT/NAT condividono IP → falsi positivi
- IPv6 richiede normalizzazione a `/64` o `/48` per evitare rotazione per-address

### Per User ID

Applicato dopo autenticazione. Previene abuso da singoli account indipendentemente dall'IP.

```typescript
function getRateLimitKey(request: Request, user: AuthenticatedUser | null): string {
  if (user) {
    return `user:${user.id}`;
  }
  return `ip:${getClientIp(request)}`;
}
```

### Per API Key

Comune per API B2B. Ogni API key ha il proprio tier di limiti.

```typescript
interface ApiKeyConfig {
  key: string;
  tier: 'free' | 'pro' | 'enterprise';
  rateLimit: number;       // req/min
  burstLimit: number;      // max burst
  dailyQuota: number;      // req/giorno
}

const TIER_LIMITS: Record<string, { rateLimit: number; burst: number; daily: number }> = {
  free:       { rateLimit: 60,    burst: 10,   daily: 1_000 },
  pro:        { rateLimit: 600,   burst: 100,  daily: 50_000 },
  enterprise: { rateLimit: 6_000, burst: 1000, daily: 1_000_000 },
};
```

### Per Endpoint

Endpoint sensibili (login, registrazione, password reset) hanno limiti molto più stretti.

```typescript
const ENDPOINT_LIMITS: Record<string, { maxRequests: number; windowSeconds: number }> = {
  'POST /auth/login':          { maxRequests: 5,    windowSeconds: 300 },   // 5/5min
  'POST /auth/register':       { maxRequests: 3,    windowSeconds: 3600 },  // 3/ora
  'POST /auth/reset-password': { maxRequests: 3,    windowSeconds: 3600 },  // 3/ora
  'GET /api/products':         { maxRequests: 100,  windowSeconds: 60 },    // 100/min
  'POST /api/orders':          { maxRequests: 30,   windowSeconds: 60 },    // 30/min
  'GET /api/search':           { maxRequests: 30,   windowSeconds: 60 },    // 30/min
  'POST /api/upload':          { maxRequests: 10,   windowSeconds: 60 },    // 10/min
  '*':                         { maxRequests: 200,  windowSeconds: 60 },    // default
};

function getEndpointLimit(method: string, path: string): { maxRequests: number; windowSeconds: number } {
  const key = `${method} ${path}`;
  return ENDPOINT_LIMITS[key] ?? ENDPOINT_LIMITS['*'];
}
```

### Per regione geografica

Utile per conformità normativa o per proteggere da traffico anomalo da regioni inattese.

```typescript
const REGION_MULTIPLIERS: Record<string, number> = {
  'EU':   1.0,   // limiti standard
  'US':   1.0,
  'APAC': 1.0,
  'RU':   0.5,   // limiti più stretti
  'CN':   0.5,
};

function adjustLimitByRegion(
  baseLimit: number,
  countryCode: string,
): number {
  const region = countryToRegion(countryCode);
  const multiplier = REGION_MULTIPLIERS[region] ?? 0.8;
  return Math.floor(baseLimit * multiplier);
}
```

### Combinazione multi-dimensionale

```typescript
interface RateLimitResult {
  allowed: boolean;
  dimension: string;
  remaining: number;
  retryAfterMs: number;
}

async function multiDimensionalCheck(
  request: Request,
  user: AuthenticatedUser | null,
  limiters: Map<string, TokenBucketRateLimiter>,
): Promise<RateLimitResult> {
  const ip = getClientIp(request);
  const method = request.method;
  const path = new URL(request.url).pathname;

  // Controlla tutte le dimensioni, la prima che fallisce blocca
  const checks: Array<{ dimension: string; key: string; tokens: number }> = [
    { dimension: 'ip',       key: `ip:${ip}`,                     tokens: 1 },
    { dimension: 'endpoint', key: `endpoint:${method}:${path}`,   tokens: 1 },
  ];

  if (user) {
    checks.push({ dimension: 'user', key: `user:${user.id}`, tokens: 1 });
  }

  for (const { dimension, key, tokens } of checks) {
    const limiter = limiters.get(dimension);
    if (!limiter) continue;

    const result = limiter.check(key, tokens);
    if (!result.allowed) {
      return {
        allowed: false,
        dimension,
        remaining: result.remaining,
        retryAfterMs: result.retryAfterMs,
      };
    }
  }

  return { allowed: true, dimension: 'none', remaining: -1, retryAfterMs: 0 };
}
```

---

## Header HTTP per rate limiting

Gli header di rate limiting sono essenziali per comunicare al client lo stato dei suoi limiti. Senza questi header, i client non possono implementare backoff intelligente e generano retry storm.

### Header standard e draft IETF

| Header | Descrizione | Esempio |
|---|---|---|
| `X-RateLimit-Limit` | Numero massimo di richieste nella finestra | `X-RateLimit-Limit: 100` |
| `X-RateLimit-Remaining` | Richieste rimanenti nella finestra corrente | `X-RateLimit-Remaining: 42` |
| `X-RateLimit-Reset` | Unix timestamp di reset della finestra | `X-RateLimit-Reset: 1716400000` |
| `Retry-After` | Secondi (o HTTP-date) prima di riprovare | `Retry-After: 30` |
| `RateLimit` (draft) | Header unificato IETF draft-ietf-httpapi-ratelimit-headers | `RateLimit: limit=100, remaining=42, reset=30` |

**Nota:** `Retry-After` è l'unico header standardizzato (RFC 9110 §10.5.4). Gli `X-RateLimit-*` sono convenzioni de facto. Lo IETF draft propone di unificarli nell'header `RateLimit`.

### Middleware Express con header

```typescript
import type { Request, Response, NextFunction } from 'express';

interface RateLimitMiddlewareOptions {
  limiter: TokenBucketRateLimiter;
  keyExtractor: (req: Request) => string;
  limit: number;
}

function rateLimitMiddleware(options: RateLimitMiddlewareOptions) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const key = options.keyExtractor(req);
    const result = options.limiter.check(key);

    // Imposta header su OGNI risposta, non solo su 429
    res.setHeader('X-RateLimit-Limit', options.limit);
    res.setHeader('X-RateLimit-Remaining', result.remaining);

    const resetAtSeconds = Math.ceil(
      (result.retryAfterMs > 0 ? Date.now() + result.retryAfterMs : Date.now() + 60_000) / 1000,
    );
    res.setHeader('X-RateLimit-Reset', resetAtSeconds);

    if (!result.allowed) {
      const retryAfterSeconds = Math.ceil(result.retryAfterMs / 1000);
      res.setHeader('Retry-After', retryAfterSeconds);
      res.status(429).json({
        error: 'Too Many Requests',
        message: `Limite superato. Riprova tra ${retryAfterSeconds} secondi.`,
        retryAfter: retryAfterSeconds,
      });
      return;
    }

    next();
  };
}
```

### Risposta 429 ben formata

```json
{
  "error": "Too Many Requests",
  "message": "Hai superato il limite di 100 richieste al minuto.",
  "retryAfter": 23,
  "limit": 100,
  "remaining": 0,
  "resetAt": "2026-05-22T14:30:00Z",
  "docs": "https://api.example.com/docs/rate-limits"
}
```

Includere sempre:
- Un messaggio leggibile dall'umano
- Il `retryAfter` in secondi nel body JSON (oltre all'header)
- Link alla documentazione dei limiti
- Non esporre dettagli interni dell'implementazione (quale algoritmo, quale store)

---

## Design API rate limiting

### Limiti a livelli (tiered)

Le API commerciali offrono limiti diversi per piano tariffario.

```typescript
interface TierConfig {
  name: string;
  requestsPerMinute: number;
  requestsPerDay: number;
  burstSize: number;
  concurrentRequests: number;
  costPerRequest: number; // in crediti
}

const TIERS: Record<string, TierConfig> = {
  free: {
    name: 'Free',
    requestsPerMinute: 20,
    requestsPerDay: 500,
    burstSize: 5,
    concurrentRequests: 2,
    costPerRequest: 1,
  },
  starter: {
    name: 'Starter',
    requestsPerMinute: 100,
    requestsPerDay: 10_000,
    burstSize: 20,
    concurrentRequests: 10,
    costPerRequest: 0.5,
  },
  pro: {
    name: 'Pro',
    requestsPerMinute: 1_000,
    requestsPerDay: 100_000,
    burstSize: 200,
    concurrentRequests: 50,
    costPerRequest: 0.1,
  },
  enterprise: {
    name: 'Enterprise',
    requestsPerMinute: 10_000,
    requestsPerDay: 1_000_000,
    burstSize: 2_000,
    concurrentRequests: 500,
    costPerRequest: 0.01,
  },
};
```

### Burst vs sustained

- **Burst limit:** numero massimo di richieste in un intervallo brevissimo (es. 1 secondo). Protegge da spike improvvisi. Corrisponde alla capacità del token bucket.
- **Sustained limit:** tasso medio su un periodo più lungo (es. per minuto, per ora). Corrisponde al refill rate del token bucket.

Un buon design espone entrambi:

```
Tier Pro:
  - Burst: fino a 200 richieste istantanee
  - Sustained: 1.000 richieste/minuto (≈16.7/sec)
  - Daily quota: 100.000 richieste/giorno
```

### Cost-based (weighted) rate limiting

Non tutte le richieste costano uguale. Una `GET /users` è economica; una `POST /reports/generate` che avvia un job pesante dovrebbe consumare più quota.

```typescript
const ENDPOINT_COSTS: Record<string, number> = {
  'GET /api/users':              1,
  'GET /api/users/:id':          1,
  'POST /api/users':             5,
  'GET /api/reports':            2,
  'POST /api/reports/generate':  50,  // operazione costosa
  'POST /api/ai/completions':    100, // chiamata LLM
  'GET /api/search':             3,
  'POST /api/upload':            10,
  'DELETE /api/users/:id':       5,
};

function getRequestCost(method: string, path: string): number {
  // Normalizza i path parametrici
  const normalizedPath = path.replace(/\/[a-f0-9-]{36}/g, '/:id')
                              .replace(/\/\d+/g, '/:id');
  const key = `${method} ${normalizedPath}`;
  return ENDPOINT_COSTS[key] ?? 1;
}

// Integrazione con token bucket
async function costBasedRateLimit(
  request: Request,
  limiter: TokenBucketRateLimiter,
  user: AuthenticatedUser,
): Promise<{ allowed: boolean; cost: number; remaining: number }> {
  const method = request.method;
  const path = new URL(request.url).pathname;
  const cost = getRequestCost(method, path);

  const result = limiter.check(`user:${user.id}`, cost);
  return { allowed: result.allowed, cost, remaining: result.remaining };
}
```

---

## Rate limiting lato client e strategie di retry

Un rate limiter efficace ha due facce: la faccia server che blocca le richieste in eccesso e la faccia client che gestisce i blocchi in modo intelligente. Senza strategie di retry adeguate lato client, un singolo 429 può innescare una retry storm che peggiora il problema.

### Backoff esponenziale con jitter

L'algoritmo standard per il retry dopo un 429 è il backoff esponenziale con jitter. Il backoff esponenziale aumenta il tempo di attesa ad ogni tentativo; il jitter aggiunge casualità per evitare il thundering herd.

```typescript
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterType: 'full' | 'equal' | 'decorrelated';
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 5,
  baseDelayMs: 1000,
  maxDelayMs: 30_000,
  jitterType: 'full',
};

function calculateRetryDelay(
  attempt: number,
  config: RetryConfig,
  retryAfterHeader?: string,
): number {
  // Se il server fornisce Retry-After, usalo come minimo
  const serverSuggestedMs = retryAfterHeader
    ? parseRetryAfter(retryAfterHeader)
    : 0;

  // Backoff esponenziale: delay = base * 2^attempt
  const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);

  // Applica jitter in base alla strategia
  let jitteredDelay: number;
  switch (config.jitterType) {
    case 'full':
      // Full jitter: random tra 0 e exponentialDelay
      // Distribuzione ottimale secondo AWS
      jitteredDelay = Math.random() * exponentialDelay;
      break;
    case 'equal':
      // Equal jitter: metà fissa + metà random
      jitteredDelay = exponentialDelay / 2 + Math.random() * (exponentialDelay / 2);
      break;
    case 'decorrelated':
      // Decorrelated: ogni delay è random tra base e 3 * delay precedente
      jitteredDelay = Math.random() * (exponentialDelay * 3 - config.baseDelayMs)
        + config.baseDelayMs;
      break;
  }

  // Il delay effettivo è il massimo tra jittered e server-suggested
  const effectiveDelay = Math.max(jitteredDelay, serverSuggestedMs);

  // Non superare il max
  return Math.min(effectiveDelay, config.maxDelayMs);
}

function parseRetryAfter(header: string): number {
  const seconds = Number(header);
  if (!Number.isNaN(seconds)) return seconds * 1000;

  // HTTP-date format
  const date = new Date(header);
  if (!Number.isNaN(date.getTime())) {
    return Math.max(0, date.getTime() - Date.now());
  }
  return 0;
}
```

### Client con retry e circuit breaker integrati

Un client HTTP robusto combina retry con backoff, circuit breaker e rate limiting locale per evitare di sovraccaricare il server.

```typescript
type CircuitState = 'closed' | 'open' | 'half-open';

class ResilientApiClient {
  private circuitState: CircuitState = 'closed';
  private failureCount = 0;
  private lastFailureTime = 0;
  private readonly failureThreshold = 5;
  private readonly resetTimeoutMs = 30_000;
  private localBucket: { tokens: number; lastRefill: number };

  constructor(
    private readonly baseUrl: string,
    private readonly retryConfig: RetryConfig = DEFAULT_RETRY_CONFIG,
    private readonly localRateLimit: number = 50, // max req/sec lato client
  ) {
    this.localBucket = { tokens: localRateLimit, lastRefill: Date.now() };
  }

  async request(
    path: string,
    options: RequestInit = {},
  ): Promise<Response> {
    // 1. Check circuit breaker
    if (this.circuitState === 'open') {
      if (Date.now() - this.lastFailureTime > this.resetTimeoutMs) {
        this.circuitState = 'half-open';
      } else {
        throw new Error(
          `Circuito aperto: servizio ${this.baseUrl} non disponibile. ` +
          `Riprova tra ${Math.ceil((this.resetTimeoutMs - (Date.now() - this.lastFailureTime)) / 1000)}s`,
        );
      }
    }

    // 2. Rate limiting locale: non inviare più di N req/sec
    this.refillLocalBucket();
    if (this.localBucket.tokens < 1) {
      const waitMs = Math.ceil(1000 / this.localRateLimit);
      await this.delay(waitMs);
      this.refillLocalBucket();
    }
    this.localBucket.tokens -= 1;

    // 3. Retry loop
    let lastError: Error | null = null;
    for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
      try {
        const response = await fetch(`${this.baseUrl}${path}`, options);

        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After') ?? undefined;
          const delayMs = calculateRetryDelay(attempt, this.retryConfig, retryAfter);

          if (attempt < this.retryConfig.maxRetries) {
            await this.delay(delayMs);
            continue;
          }
          this.recordFailure();
          throw new Error(`Rate limited dopo ${attempt + 1} tentativi`);
        }

        if (response.status >= 500) {
          this.recordFailure();
          if (attempt < this.retryConfig.maxRetries) {
            const delayMs = calculateRetryDelay(attempt, this.retryConfig);
            await this.delay(delayMs);
            continue;
          }
          throw new Error(`Server error ${response.status} dopo ${attempt + 1} tentativi`);
        }

        // Successo: reset circuit breaker
        this.recordSuccess();
        return response;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        if (attempt < this.retryConfig.maxRetries) {
          const delayMs = calculateRetryDelay(attempt, this.retryConfig);
          await this.delay(delayMs);
        }
      }
    }

    this.recordFailure();
    throw lastError ?? new Error('Richiesta fallita');
  }

  private recordFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    if (this.failureCount >= this.failureThreshold) {
      this.circuitState = 'open';
    }
  }

  private recordSuccess(): void {
    this.failureCount = 0;
    if (this.circuitState === 'half-open') {
      this.circuitState = 'closed';
    }
  }

  private refillLocalBucket(): void {
    const now = Date.now();
    const elapsed = (now - this.localBucket.lastRefill) / 1000;
    this.localBucket.tokens = Math.min(
      this.localRateLimit,
      this.localBucket.tokens + elapsed * this.localRateLimit,
    );
    this.localBucket.lastRefill = now;
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
```

### Pre-flight rate limit check

Un pattern avanzato: il client chiede al server la quota rimanente prima di inviare un batch di richieste, evitando 429 prevenibili.

```typescript
interface QuotaStatus {
  remaining: number;
  resetAt: string;
  limit: number;
}

async function prefetchQuota(client: ResilientApiClient): Promise<QuotaStatus> {
  const res = await client.request('/api/rate-limit-status');
  return await res.json() as QuotaStatus;
}

async function batchWithQuotaAwareness(
  client: ResilientApiClient,
  items: unknown[],
  batchSize: number,
): Promise<void> {
  const quota = await prefetchQuota(client);

  // Se la quota è insufficiente, attendi il reset
  if (quota.remaining < items.length) {
    const resetTime = new Date(quota.resetAt).getTime();
    const waitMs = Math.max(0, resetTime - Date.now());
    if (waitMs > 0 && waitMs < 120_000) {
      await new Promise((r) => setTimeout(r, waitMs));
    }
  }

  // Invia in batch rispettando la quota
  const effectiveBatch = Math.min(batchSize, quota.remaining);
  for (let i = 0; i < items.length; i += effectiveBatch) {
    const batch = items.slice(i, i + effectiveBatch);
    await Promise.all(
      batch.map((item) =>
        client.request('/api/process', {
          method: 'POST',
          body: JSON.stringify(item),
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
  }
}
```

---

## Rate limiting per connessioni WebSocket

Le connessioni WebSocket sono persistenti e bidirezionali, il che rende il rate limiting HTTP tradizionale (basato su richieste HTTP individuali) inapplicabile. Un client apre una singola connessione e può inviare migliaia di messaggi senza nuove richieste HTTP. Servono strategie specifiche.

### Dimensioni di rate limiting per WebSocket

| Dimensione | Cosa limita | Tipico |
|---|---|---|
| **Connessioni per IP** | Numero di WebSocket aperti dallo stesso IP | 5-10 |
| **Connessioni per utente** | Numero di WebSocket per utente autenticato | 3-5 |
| **Messaggi per connessione/minuto** | Tasso di messaggi inviati dal client | 60-120/min |
| **Dimensione messaggio** | Payload massimo per singolo frame | 64 KB - 1 MB |
| **Bandwidth per connessione** | Bytes totali per secondo | 100 KB/s |
| **Connessioni totali** | Limite globale del server | Dipende da RAM |

### Rate limiting a livello di messaggio

```typescript
interface WebSocketRateLimitState {
  messageCount: number;
  windowStart: number;
  totalBytes: number;
  warnings: number;
}

class WebSocketMessageLimiter {
  private states: Map<string, WebSocketRateLimitState> = new Map();

  constructor(
    private readonly maxMessagesPerMinute: number,
    private readonly maxBytesPerMinute: number,
    private readonly maxWarnings: number = 3,
  ) {}

  /**
   * Verifica se un messaggio in arrivo è ammesso.
   * Restituisce l'azione da intraprendere.
   */
  checkMessage(
    connectionId: string,
    messageSize: number,
  ): 'allow' | 'warn' | 'throttle' | 'disconnect' {
    const now = Date.now();
    const windowMs = 60_000;

    let state = this.states.get(connectionId);
    if (!state || now - state.windowStart > windowMs) {
      state = { messageCount: 0, windowStart: now, totalBytes: 0, warnings: 0 };
      this.states.set(connectionId, state);
    }

    state.messageCount++;
    state.totalBytes += messageSize;

    // Messaggio troppo grande
    if (messageSize > 1_048_576) { // 1 MB
      return 'disconnect';
    }

    // Superato il limite di messaggi
    if (state.messageCount > this.maxMessagesPerMinute) {
      state.warnings++;
      if (state.warnings > this.maxWarnings) return 'disconnect';
      return 'throttle';
    }

    // Superato il limite di bandwidth
    if (state.totalBytes > this.maxBytesPerMinute) {
      state.warnings++;
      if (state.warnings > this.maxWarnings) return 'disconnect';
      return 'throttle';
    }

    // Vicino al limite: warning
    if (state.messageCount > this.maxMessagesPerMinute * 0.8) {
      return 'warn';
    }

    return 'allow';
  }

  removeConnection(connectionId: string): void {
    this.states.delete(connectionId);
  }
}
```

### Integrazione con WebSocket server

```typescript
import { WebSocketServer, WebSocket } from 'ws';

const wss = new WebSocketServer({ port: 8080 });
const limiter = new WebSocketMessageLimiter(120, 5_242_880); // 120 msg/min, 5 MB/min
const connectionsPerIp = new Map<string, number>();
const MAX_CONNECTIONS_PER_IP = 5;

wss.on('connection', (ws: WebSocket, request) => {
  const ip = request.headers['x-forwarded-for']?.toString().split(',')[0]?.trim()
    ?? request.socket.remoteAddress
    ?? 'unknown';

  // Rate limit connessioni per IP
  const currentCount = connectionsPerIp.get(ip) ?? 0;
  if (currentCount >= MAX_CONNECTIONS_PER_IP) {
    ws.close(1008, 'Troppo connessioni da questo IP');
    return;
  }
  connectionsPerIp.set(ip, currentCount + 1);

  const connectionId = `${ip}:${Date.now()}:${Math.random().toString(36).slice(2)}`;

  ws.on('message', (data: Buffer) => {
    const action = limiter.checkMessage(connectionId, data.length);

    switch (action) {
      case 'allow':
        handleMessage(ws, data);
        break;
      case 'warn':
        handleMessage(ws, data);
        ws.send(JSON.stringify({
          type: 'rate_limit_warning',
          message: 'Stai per raggiungere il limite di messaggi',
        }));
        break;
      case 'throttle':
        ws.send(JSON.stringify({
          type: 'rate_limit_exceeded',
          message: 'Limite messaggi superato. Messaggio ignorato.',
          retryAfterMs: 5000,
        }));
        break;
      case 'disconnect':
        ws.close(1008, 'Rate limit superato: disconnessione');
        break;
    }
  });

  ws.on('close', () => {
    limiter.removeConnection(connectionId);
    const count = connectionsPerIp.get(ip) ?? 1;
    if (count <= 1) {
      connectionsPerIp.delete(ip);
    } else {
      connectionsPerIp.set(ip, count - 1);
    }
  });
});

function handleMessage(ws: WebSocket, data: Buffer): void {
  // Logica di business
}
```

### Heartbeat budget

Per WebSocket con heartbeat, includere i messaggi di heartbeat nel budget di rate limiting è scorretto: penalizzerebbe connessioni inattive. Il pattern heartbeat budget separa il conteggio.

```typescript
interface WebSocketBudget {
  heartbeatCount: number;
  dataMessageCount: number;
  lastHeartbeat: number;
}

function isHeartbeat(data: Buffer): boolean {
  try {
    const msg = JSON.parse(data.toString());
    return msg.type === 'ping' || msg.type === 'pong' || msg.type === 'heartbeat';
  } catch {
    return false;
  }
}

// Nel message handler:
// if (isHeartbeat(data)) { budget.heartbeatCount++; return; }
// else { budget.dataMessageCount++; limiter.checkMessage(...); }
```

---

## Gestione quote API

Le quote API sono concettualmente diverse dal rate limiting, anche se nella pratica si implementano con strumenti simili. Il rate limiting controlla il tasso istantaneo (richieste per secondo/minuto); la quota controlla il volume totale su periodi lunghi (giorno, mese).

### Quota vs Rate Limit

| Aspetto | Rate Limit | Quota |
|---|---|---|
| **Periodo** | Secondi, minuti | Ore, giorni, mesi |
| **Scopo** | Protezione infrastruttura | Controllo commerciale / fatturazione |
| **Reset** | Automatico e frequente | A cadenza fissa (mezzanotte, 1° del mese) |
| **Granularità** | Per IP, per endpoint | Per account, per API key |
| **Superamento** | 429 immediato | 429 o fatturazione overage |
| **Comunicazione** | Header X-RateLimit-* | Dashboard utente, email alert |

### Lifecycle di una quota

```
Allocazione → Consumo → Monitoraggio → Warning → Esaurimento → Reset/Rinnovo
    │              │           │             │            │            │
    ▼              ▼           ▼             ▼            ▼            ▼
  Tier plan    Decrement    Dashboard    Email 80%    Hard block    Midnight
  upgrade      per request  real-time    alert         o overage     UTC reset
```

### Implementazione quota con Redis

```typescript
interface QuotaConfig {
  dailyLimit: number;
  monthlyLimit: number;
  overagePolicy: 'block' | 'charge' | 'warn';
  warningThresholds: number[]; // percentuali: [50, 80, 90, 100]
}

class ApiQuotaManager {
  constructor(
    private readonly redis: Redis,
    private readonly configs: Map<string, QuotaConfig>,
  ) {}

  async consumeQuota(
    apiKeyId: string,
    cost: number = 1,
  ): Promise<{
    allowed: boolean;
    dailyUsed: number;
    dailyRemaining: number;
    monthlyUsed: number;
    monthlyRemaining: number;
    warnings: string[];
  }> {
    const config = this.configs.get(apiKeyId);
    if (!config) throw new Error(`Nessuna configurazione per API key ${apiKeyId}`);

    const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    const month = today.slice(0, 7); // YYYY-MM

    const dailyKey = `quota:daily:${apiKeyId}:${today}`;
    const monthlyKey = `quota:monthly:${apiKeyId}:${month}`;

    // Incremento atomico di entrambe le quote
    const pipe = this.redis.pipeline();
    pipe.incrby(dailyKey, cost);
    pipe.expire(dailyKey, 86400 + 3600); // TTL: 25 ore (margine)
    pipe.incrby(monthlyKey, cost);
    pipe.expire(monthlyKey, 32 * 86400); // TTL: 32 giorni (margine)

    const results = await pipe.exec();
    if (!results) throw new Error('Redis pipeline failed');

    const dailyUsed = results[0][1] as number;
    const monthlyUsed = results[2][1] as number;

    const dailyRemaining = Math.max(0, config.dailyLimit - dailyUsed);
    const monthlyRemaining = Math.max(0, config.monthlyLimit - monthlyUsed);

    // Calcola warning
    const warnings: string[] = [];
    const dailyPercent = (dailyUsed / config.dailyLimit) * 100;
    const monthlyPercent = (monthlyUsed / config.monthlyLimit) * 100;

    for (const threshold of config.warningThresholds) {
      if (dailyPercent >= threshold && dailyPercent - cost / config.dailyLimit * 100 < threshold) {
        warnings.push(`Quota giornaliera al ${threshold}% (${dailyUsed}/${config.dailyLimit})`);
      }
      if (monthlyPercent >= threshold && monthlyPercent - cost / config.monthlyLimit * 100 < threshold) {
        warnings.push(`Quota mensile al ${threshold}% (${monthlyUsed}/${config.monthlyLimit})`);
      }
    }

    // Applica policy di overage
    const exceeded = dailyUsed > config.dailyLimit || monthlyUsed > config.monthlyLimit;
    let allowed = true;

    if (exceeded) {
      switch (config.overagePolicy) {
        case 'block':
          allowed = false;
          break;
        case 'charge':
          allowed = true; // fatturazione extra gestita altrove
          warnings.push('Quota superata: addebito overage attivo');
          break;
        case 'warn':
          allowed = true;
          warnings.push('Quota superata: nessun blocco ma raccomandato upgrade');
          break;
      }
    }

    return { allowed, dailyUsed, dailyRemaining, monthlyUsed, monthlyRemaining, warnings };
  }
}
```

### Endpoint di stato quota

Esporre un endpoint dedicato permette ai client di controllare il proprio consumo senza dover aspettare un 429.

```typescript
// GET /api/quota/status
// Risposta:
{
  "plan": "pro",
  "rate_limit": {
    "limit": 1000,
    "remaining": 847,
    "reset": "2026-05-24T14:30:00Z"
  },
  "quota": {
    "daily": {
      "limit": 100000,
      "used": 23456,
      "remaining": 76544,
      "reset": "2026-05-25T00:00:00Z"
    },
    "monthly": {
      "limit": 1000000,
      "used": 345678,
      "remaining": 654322,
      "reset": "2026-06-01T00:00:00Z"
    }
  },
  "overage_policy": "charge",
  "upgrade_url": "https://example.com/pricing"
}
```

### Grace period e soft limit

Un blocco immediato al superamento della quota è frustrante per gli utenti. Il pattern grace period concede un margine temporale o volumetrico prima del blocco effettivo, dando all'utente il tempo di reagire.

```typescript
interface GracePeriodConfig {
  enabled: boolean;
  extraPercentage: number;    // es. 10% extra dopo il limite
  durationMinutes: number;     // durata del grace period
  notifyOnEntry: boolean;      // invia notifica all'ingresso nel grace
}

function isInGracePeriod(
  used: number,
  limit: number,
  grace: GracePeriodConfig,
): 'within_limit' | 'in_grace' | 'exceeded' {
  if (used <= limit) return 'within_limit';

  if (!grace.enabled) return 'exceeded';

  const graceLimit = limit * (1 + grace.extraPercentage / 100);
  if (used <= graceLimit) return 'in_grace';

  return 'exceeded';
}
```

---

## Protezione DDoS

Il rate limiting è la prima linea di difesa, ma la protezione DDoS richiede misure stratificate.

### Difesa application-layer (L7)

Gli attacchi L7 imitano traffico legittimo e sono i più difficili da mitigare. Tecniche:

1. **Rate limiting adattivo:** alzare/abbassare i limiti in base al carico corrente del sistema
2. **Slowloris defense:** timeout aggressivi su connessioni lente
3. **Request size limiting:** bloccare payload anomalmente grandi
4. **Pattern detection:** identificare sequenze ripetitive di endpoint

```typescript
interface AdaptiveRateLimitConfig {
  baseLimit: number;
  minLimit: number;
  loadThresholds: Array<{ loadPercent: number; limitMultiplier: number }>;
}

function getAdaptiveLimit(
  config: AdaptiveRateLimitConfig,
  currentLoadPercent: number,
): number {
  // Ordina per loadPercent decrescente per match più specifico
  const sorted = [...config.loadThresholds].sort(
    (a, b) => b.loadPercent - a.loadPercent,
  );

  for (const threshold of sorted) {
    if (currentLoadPercent >= threshold.loadPercent) {
      return Math.max(
        config.minLimit,
        Math.floor(config.baseLimit * threshold.limitMultiplier),
      );
    }
  }

  return config.baseLimit;
}

// Esempio: sotto carico pesante, riduci i limiti progressivamente
const adaptiveConfig: AdaptiveRateLimitConfig = {
  baseLimit: 100,
  minLimit: 10,
  loadThresholds: [
    { loadPercent: 90, limitMultiplier: 0.1 },  // 90%+ load → 10 req/min
    { loadPercent: 75, limitMultiplier: 0.3 },  // 75%+ load → 30 req/min
    { loadPercent: 50, limitMultiplier: 0.6 },  // 50%+ load → 60 req/min
  ],
};
```

### Challenge pages

Quando il traffico è sospetto ma non certamente malevolo, interporre una challenge prima di servire contenuto.

**Tipologie di challenge:**
- **JavaScript challenge:** esegue un piccolo calcolo nel browser. Bot senza JS engine falliscono.
- **CAPTCHA:** interazione umana esplicita. Intrusivo ma efficace.
- **Proof of Work:** il client deve calcolare un hash con proprietà specifiche. Penalizza chi fa molte richieste.

```typescript
interface ChallengeDecision {
  action: 'allow' | 'challenge' | 'block';
  challengeType?: 'js' | 'captcha' | 'pow';
  reason: string;
}

function decideChallengeAction(
  requestScore: number,   // 0-100, più alto = più sospetto
  isAuthenticated: boolean,
  hasValidSession: boolean,
): ChallengeDecision {
  if (requestScore < 20) {
    return { action: 'allow', reason: 'Traffico normale' };
  }

  if (requestScore < 50) {
    if (isAuthenticated && hasValidSession) {
      return { action: 'allow', reason: 'Utente autenticato con sessione valida' };
    }
    return {
      action: 'challenge',
      challengeType: 'js',
      reason: 'Traffico sospetto, JS challenge richiesta',
    };
  }

  if (requestScore < 80) {
    return {
      action: 'challenge',
      challengeType: 'captcha',
      reason: 'Traffico molto sospetto',
    };
  }

  return { action: 'block', reason: 'Traffico malevolo con alta probabilità' };
}
```

### Bot detection

Segnali per distinguere bot da utenti reali:

| Segnale | Bot tipico | Utente reale |
|---|---|---|
| User-Agent | Assente, generico, o noto come bot | Browser reale con versione |
| TLS fingerprint (JA3/JA4) | Librerie HTTP standard | Browser fingerprint unico |
| Timing tra richieste | Uniformemente distribuito (troppo regolare) | Variabile, pattern umano |
| Mouse/keyboard events | Assenti | Presenti (se page JS) |
| Cookie handling | Ignora o replay meccanico | Gestisce normalmente |
| JavaScript execution | Spesso assente | Presente |
| WebDriver flag | `navigator.webdriver = true` | `false` |
| Canvas/WebGL fingerprint | Assente o generico | Unico per hardware |

---

## Edge computing

### Cloudflare Workers

Runtime V8 isolate, non Node.js. Esecuzione in 300+ PoP globali. Cold start quasi zero (~0ms) grazie a pre-warm degli isolate.

```typescript
// cloudflare-worker-rate-limit.ts
export interface Env {
  RATE_LIMITER: DurableObjectNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const ip = request.headers.get('cf-connecting-ip') ?? 'unknown';
    const country = request.headers.get('cf-ipcountry') ?? 'XX';
    const url = new URL(request.url);

    // Rate limit usando Durable Objects per stato distribuito
    const id = env.RATE_LIMITER.idFromName(ip);
    const stub = env.RATE_LIMITER.get(id);

    const limitResponse = await stub.fetch(
      new Request('https://internal/check', {
        method: 'POST',
        body: JSON.stringify({
          ip,
          country,
          path: url.pathname,
          method: request.method,
        }),
      }),
    );

    const limitResult = await limitResponse.json<{
      allowed: boolean;
      remaining: number;
      resetAt: number;
    }>();

    if (!limitResult.allowed) {
      return new Response(
        JSON.stringify({ error: 'Too Many Requests' }),
        {
          status: 429,
          headers: {
            'Content-Type': 'application/json',
            'Retry-After': '60',
            'X-RateLimit-Limit': '100',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': String(limitResult.resetAt),
          },
        },
      );
    }

    // Proxy all'origin
    const response = await fetch(request);
    const newResponse = new Response(response.body, response);
    newResponse.headers.set('X-RateLimit-Remaining', String(limitResult.remaining));
    return newResponse;
  },
};

// Durable Object per stato persistente
export class RateLimiterDO implements DurableObject {
  private requests: number[] = [];
  private readonly limit = 100;
  private readonly windowMs = 60_000;

  constructor(private state: DurableObjectState) {}

  async fetch(request: Request): Promise<Response> {
    const now = Date.now();

    // Sliding window log
    this.requests = this.requests.filter((t) => t > now - this.windowMs);

    if (this.requests.length >= this.limit) {
      return Response.json({
        allowed: false,
        remaining: 0,
        resetAt: Math.ceil((this.requests[0] + this.windowMs) / 1000),
      });
    }

    this.requests.push(now);
    return Response.json({
      allowed: true,
      remaining: this.limit - this.requests.length,
      resetAt: Math.ceil((now + this.windowMs) / 1000),
    });
  }
}
```

---

### Vercel Edge Functions (Edge Middleware)

Runtime basato su Edge Runtime (V8, non Node.js). Esegue prima di Next.js routing. Utile per rate limiting, geolocation, A/B testing.

```typescript
// middleware.ts (Next.js Edge Middleware)
import { NextRequest, NextResponse } from 'next/server';

// In produzione usare Upstash Redis, non in-memory
// import { Ratelimit } from '@upstash/ratelimit';
// import { Redis } from '@upstash/redis';

const rateLimitMap = new Map<string, { count: number; resetTime: number }>();
const LIMIT = 50;
const WINDOW_MS = 60_000;

export function middleware(request: NextRequest): NextResponse {
  const ip = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim()
    ?? request.headers.get('x-real-ip')
    ?? '127.0.0.1';

  const now = Date.now();
  const key = `rl:${ip}`;
  const entry = rateLimitMap.get(key);

  if (!entry || entry.resetTime <= now) {
    rateLimitMap.set(key, { count: 1, resetTime: now + WINDOW_MS });
    const response = NextResponse.next();
    response.headers.set('X-RateLimit-Limit', String(LIMIT));
    response.headers.set('X-RateLimit-Remaining', String(LIMIT - 1));
    return response;
  }

  if (entry.count >= LIMIT) {
    const retryAfter = Math.ceil((entry.resetTime - now) / 1000);
    return new NextResponse(
      JSON.stringify({ error: 'Rate limit exceeded' }),
      {
        status: 429,
        headers: {
          'Content-Type': 'application/json',
          'Retry-After': String(retryAfter),
          'X-RateLimit-Limit': String(LIMIT),
          'X-RateLimit-Remaining': '0',
        },
      },
    );
  }

  entry.count += 1;
  const response = NextResponse.next();
  response.headers.set('X-RateLimit-Limit', String(LIMIT));
  response.headers.set('X-RateLimit-Remaining', String(LIMIT - entry.count));
  return response;
}

export const config = {
  matcher: ['/api/:path*'],
};
```

**Con Upstash (produzione):**

```typescript
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';
import { NextRequest, NextResponse } from 'next/server';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, '60 s'),
  analytics: true,
  prefix: 'api-ratelimit',
});

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const ip = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ?? '127.0.0.1';
  const { success, limit, remaining, reset } = await ratelimit.limit(ip);

  const headers = new Headers();
  headers.set('X-RateLimit-Limit', String(limit));
  headers.set('X-RateLimit-Remaining', String(remaining));
  headers.set('X-RateLimit-Reset', String(reset));

  if (!success) {
    return new NextResponse(
      JSON.stringify({ error: 'Too Many Requests' }),
      { status: 429, headers },
    );
  }

  const response = NextResponse.next();
  response.headers.set('X-RateLimit-Limit', String(limit));
  response.headers.set('X-RateLimit-Remaining', String(remaining));
  return response;
}
```

---

### AWS Lambda@Edge

Esegue funzioni Lambda nei PoP CloudFront. Quattro trigger point: viewer request, viewer response, origin request, origin response.

```typescript
// lambda-edge-rate-limit.ts
// Lambda@Edge non supporta env vars: configurazione hardcoded o da S3/DynamoDB
import type {
  CloudFrontRequestEvent,
  CloudFrontRequestResult,
} from 'aws-lambda';

// In Lambda@Edge: DynamoDB per stato, ma attenzione alla latenza
// Alternative: usare CloudFront + WAF rate-based rules (gestito)

export async function handler(
  event: CloudFrontRequestEvent,
): Promise<CloudFrontRequestResult> {
  const request = event.Records[0].cf.request;
  const clientIp = request.clientIp;

  // Nota: Lambda@Edge ha limiti stretti:
  // - Viewer request/response: max 5 sec, 128 MB RAM
  // - Origin request/response: max 30 sec, 3008 MB RAM
  // - Nessuna env var
  // - Nessun VPC access da viewer trigger
  // - Package max 1 MB (viewer) o 50 MB (origin)

  // Per rate limiting reale, preferire WAF rate-based rules
  // o CloudFront Functions (più leggere, ma JavaScript puro, non Node.js)

  // Esempio semplificato senza stato persistente:
  const headers = request.headers;
  const userAgent = headers['user-agent']?.[0]?.value ?? '';

  // Blocca UA noti come bot malevoli
  const blockedUAs = ['curl/', 'python-requests/', 'Go-http-client/'];
  if (blockedUAs.some((ua) => userAgent.includes(ua))) {
    return {
      status: '403',
      statusDescription: 'Forbidden',
      body: 'Access denied',
      headers: {
        'content-type': [{ key: 'Content-Type', value: 'text/plain' }],
      },
    };
  }

  return request;
}
```

**Limitazioni specifiche di Lambda@Edge:**
- Nessuna variabile d'ambiente (configurazione hardcoded o da store esterno)
- Timeout ridotti per viewer trigger (5 secondi)
- Dimensione del pacchetto limitata (1 MB viewer, 50 MB origin)
- Nessun accesso VPC da viewer trigger
- Deploy solo in us-east-1 (replica automatica ai PoP)

---

### Deno Deploy

Runtime basato su Deno, distribuito globalmente. Supporta Web Standard APIs. Cold start <10ms.

```typescript
// deno-deploy-rate-limit.ts
// Usa Deno.openKv() per stato persistente distribuito

const kv = await Deno.openKv();

interface RateLimitEntry {
  count: number;
  windowStart: number;
}

const LIMIT = 100;
const WINDOW_MS = 60_000;

Deno.serve(async (request: Request): Promise<Response> => {
  const url = new URL(request.url);

  // Solo API endpoints
  if (!url.pathname.startsWith('/api/')) {
    return new Response('Not Found', { status: 404 });
  }

  const ip = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim()
    ?? 'unknown';

  const now = Date.now();
  const windowStart = Math.floor(now / WINDOW_MS) * WINDOW_MS;
  const kvKey = ['ratelimit', ip, windowStart];

  // Operazione atomica su Deno KV
  const entry = await kv.get<RateLimitEntry>(kvKey);

  if (entry.value && entry.value.count >= LIMIT) {
    const resetAt = windowStart + WINDOW_MS;
    const retryAfter = Math.ceil((resetAt - now) / 1000);
    return new Response(
      JSON.stringify({ error: 'Too Many Requests' }),
      {
        status: 429,
        headers: {
          'Content-Type': 'application/json',
          'Retry-After': String(retryAfter),
          'X-RateLimit-Limit': String(LIMIT),
          'X-RateLimit-Remaining': '0',
        },
      },
    );
  }

  const newCount = (entry.value?.count ?? 0) + 1;

  // Atomic check-and-set per evitare race condition
  const result = await kv.atomic()
    .check(entry)
    .set(kvKey, { count: newCount, windowStart }, { expireIn: WINDOW_MS + 5_000 })
    .commit();

  if (!result.ok) {
    // Conflitto: un'altra richiesta ha modificato il valore. Riprova.
    return new Response(
      JSON.stringify({ error: 'Conflict, retry' }),
      { status: 503, headers: { 'Retry-After': '1' } },
    );
  }

  const remaining = LIMIT - newCount;

  // Proxy all'origin o gestisci direttamente
  return new Response(
    JSON.stringify({ message: 'OK', path: url.pathname }),
    {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'X-RateLimit-Limit': String(LIMIT),
        'X-RateLimit-Remaining': String(Math.max(0, remaining)),
      },
    },
  );
});
```

---

## Rate limiting nativo ai CDN edge

Oltre alle edge function custom, i principali CDN offrono rate limiting come servizio gestito. Questo approccio non richiede codice: si configurano regole tramite dashboard o API, e il CDN le applica automaticamente a livello di PoP.

### Cloudflare Rate Limiting Rules

Cloudflare ha sostituito il vecchio Rate Limiting API (deprecato a giugno 2025) con le Rate Limiting Rules integrate nel WAF. Le regole operano a livello di PoP con contatori per data center.

**Caratteristiche:**
- Contatori scoped per data center (`cf.colo.id` è sempre incluso come caratteristica obbligatoria)
- Supporto per IP, header, query parameter, cookie, ASN come caratteristiche di conteggio
- Azioni: block, challenge, managed challenge, JS challenge, log
- Finestre di conteggio: 10 secondi, 1 minuto, 10 minuti, 1 ora
- Mitigation timeout configurabile separato dalla finestra di conteggio

**Configurazione tramite Rulesets API (Terraform):**

```hcl
resource "cloudflare_ruleset" "rate_limiting" {
  zone_id     = var.zone_id
  name        = "Rate limiting rules"
  description = "Rate limiting per API"
  kind        = "zone"
  phase       = "http_ratelimit"

  rules {
    action = "block"
    ratelimit {
      characteristics     = ["cf.colo.id", "ip.src"]
      period              = 60
      requests_per_period = 100
      mitigation_timeout  = 120
    }
    expression  = "(http.request.uri.path matches \"^/api/\")"
    description = "Limita API a 100 req/min per IP per data center"
    enabled     = true
  }

  rules {
    action = "managed_challenge"
    ratelimit {
      characteristics     = ["cf.colo.id", "ip.src"]
      period              = 300
      requests_per_period = 5
      mitigation_timeout  = 600
    }
    expression  = "(http.request.uri.path eq \"/api/auth/login\" and http.request.method eq \"POST\")"
    description = "Login: 5 tentativi/5min, poi challenge"
    enabled     = true
  }
}
```

**Attenzione:** i contatori sono per PoP, non globali. Un utente che colpisce 3 PoP diversi può effettivamente fare 3× il limite configurato. Per limiti globali è necessario usare Workers con Durable Objects o un servizio esterno come Upstash.

### Cloudflare Workers Rate Limiting Binding

In alternativa alle WAF rules, i Workers possono usare il binding `RateLimiter` nativo per un controllo programmatico.

```typescript
// wrangler.toml
// [[rate_limiting]]
// binding = "MY_RATE_LIMITER"
// namespace_id = "1001"
// simple = { period = 60, limit = 100 }

export interface Env {
  MY_RATE_LIMITER: RateLimit;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const ip = request.headers.get('cf-connecting-ip') ?? 'unknown';

    const { success } = await env.MY_RATE_LIMITER.limit({
      key: ip,
    });

    if (!success) {
      return new Response('Too Many Requests', { status: 429 });
    }

    return fetch(request);
  },
};
```

### Fastly Edge Rate Limiting

Fastly implementa il rate limiting tramite due primitive VCL: `ratecounter` (contatore) e `penaltybox` (blocco temporaneo). Il rate limiting è integrato direttamente nel VCL processing pipeline.

**Caratteristiche:**
- Finestre di conteggio: 1 secondo, 10 secondi, 60 secondi
- Contatori per PoP (come Cloudflare)
- Imprecisione dichiarata fino al 10% (possibile under-count)
- Supporto per rate e burst check simultanei con `ratelimit.check_rates`
- Integrazione con il penalty box per blocco temporale

**Configurazione VCL:**

```vcl
# Dichiarazione del ratecounter e penaltybox
ratecounter api_rc {}
penaltybox api_pb {}

sub vcl_recv {
  # Controlla se il client è nel penalty box
  if (ratelimit.penaltybox_has(api_pb, client.ip)) {
    error 429 "Too Many Requests";
  }

  # Controlla il rate: 100 req in 60 secondi
  # Se superato, metti nel penalty box per 120 secondi
  if (ratelimit.check_rate(
    client.ip,     # chiave di conteggio
    api_rc,        # ratecounter
    1,             # incremento
    60,            # finestra in secondi
    100,           # limite
    api_pb,        # penalty box
    120s           # durata penalty
  )) {
    error 429 "Too Many Requests";
  }
}

sub vcl_error {
  if (obj.status == 429) {
    set obj.http.Content-Type = "application/json";
    set obj.http.Retry-After = "120";
    synthetic {"{"error":"Too Many Requests","retryAfter":120}"};
    return (deliver);
  }
}
```

**Dual rate check (burst + sustained):**

```vcl
ratecounter api_burst_rc {}
ratecounter api_sustained_rc {}
penaltybox api_pb {}

sub vcl_recv {
  if (ratelimit.penaltybox_has(api_pb, client.ip)) {
    error 429 "Too Many Requests";
  }

  # Check doppio: burst (20 req in 1s) e sustained (200 req in 60s)
  if (ratelimit.check_rates(
    client.ip,
    api_burst_rc, 1, 1, 20,        # burst: 20/sec
    api_sustained_rc, 1, 60, 200,   # sustained: 200/min
    api_pb, 60s                      # penalty: 60 secondi
  )) {
    error 429 "Too Many Requests";
  }
}
```

### Confronto rate limiting CDN nativo

| Aspetto | Cloudflare WAF Rules | Cloudflare Workers Binding | Fastly VCL |
|---|---|---|---|
| **Configurazione** | Dashboard/API/Terraform | Codice TypeScript | Codice VCL |
| **Granularità conteggio** | Per PoP | Per PoP | Per PoP |
| **Precisione** | Buona | Buona | ±10% (dichiarato) |
| **Logica custom** | Espressioni wirefilter | Arbitraria | VCL + Rust/Go (Compute) |
| **Burst + sustained** | Due regole separate | Codice custom | `check_rates` nativo |
| **Stato persistente** | No (solo WAF counters) | Via Durable Objects/KV | No (solo ratecounter) |
| **Costo** | Incluso in piani business/enterprise | Workers pricing | Enterprise / attivazione manuale |
| **Cold start** | Nessuno (regola WAF) | ~0ms (V8 isolate) | Nessuno (VCL compilato) |

---

## Limitazioni degli edge runtime

Gli edge runtime non sono Node.js. Comprendere i vincoli evita errori a runtime.

### API non disponibili

| API / Modulo | Edge Runtime | Motivo |
|---|---|---|
| `fs` (filesystem) | Non disponibile | Nessun filesystem locale |
| `child_process` | Non disponibile | Nessuna shell, nessun spawn |
| `net`, `dgram` | Non disponibile | Nessun socket raw |
| `crypto` (Node.js) | Parziale | Usare `crypto.subtle` (Web Crypto API) |
| `Buffer` | Variabile | Disponibile su CF Workers, limitato su Vercel Edge |
| `__dirname`, `__filename` | Non disponibile | Non è un filesystem |
| `process.env` | Variabile | CF usa `env` param; Vercel usa `process.env` in modo limitato |
| `require()` | Non disponibile | Solo ESM (import) |
| `eval()`, `Function()` | Bloccato su CF Workers | Limitazione di sicurezza V8 isolates |
| `setTimeout` (arbitrario) | Limitato | Durata limitata al lifecycle della richiesta |
| `setInterval` | Non disponibile | Nessun loop persistente |

### Limiti di dimensione e tempo

| Piattaforma | Script Size | CPU Time | Wall Time | Memoria |
|---|---|---|---|---|
| Cloudflare Workers (free) | 1 MB | 10 ms | - | 128 MB |
| Cloudflare Workers (paid) | 10 MB | 50 ms (30s cron) | - | 128 MB |
| Vercel Edge Functions | 4 MB (code+deps) | - | 30 sec | 128 MB |
| Lambda@Edge (viewer) | 1 MB | - | 5 sec | 128 MB |
| Lambda@Edge (origin) | 50 MB | - | 30 sec | 3008 MB |
| Deno Deploy | 20 MB | - | ~50 sec | 512 MB |
| CloudFront Functions | 10 KB | <1ms | 1 sec | 2 MB |

### Moduli npm con problemi all'edge

Molte librerie npm dipendono da API Node.js non disponibili. Librerie problematiche comuni:

- **`bcrypt`** / **`bcryptjs`**: usare `@noble/hashes` o Web Crypto `PBKDF2`
- **`jsonwebtoken`**: usare `jose` (pure JS, compatibile edge)
- **`axios`**: usare `fetch` nativo
- **`pg`** / **`mysql2`**: usare HTTP-based connectors (Neon serverless driver, PlanetScale serverless)
- **`sharp`**: non disponibile, usare servizi di image optimization (Cloudflare Images, imgproxy)
- **`puppeteer`**: non disponibile all'edge
- **`node-fetch`**: inutile, `fetch` è nativo

---

## Casi d'uso edge

### Geolocation

L'edge riceve header di geolocalizzazione dal CDN senza latenza aggiuntiva.

```typescript
// Cloudflare Workers: usa cf object
interface CfProperties {
  country: string;
  city: string;
  continent: string;
  latitude: string;
  longitude: string;
  region: string;
  timezone: string;
  postalCode: string;
  asn: number;
  asOrganization: string;
}

export default {
  async fetch(request: Request): Promise<Response> {
    const cf = (request as any).cf as CfProperties;

    // Redirect per paese
    if (cf.country === 'IT') {
      return Response.redirect('https://example.com/it/', 302);
    }

    // Contenuto localizzato
    const content = await getContentForRegion(cf.country, cf.city);

    // Pricing per regione
    const currency = getCurrencyForCountry(cf.country);

    return new Response(JSON.stringify({ content, currency, geo: cf }), {
      headers: { 'Content-Type': 'application/json' },
    });
  },
};
```

### A/B testing

Assegnazione all'edge senza round-trip al server. Il cookie garantisce persistenza dell'assegnazione.

```typescript
// a-b-testing-edge.ts
function getExperimentVariant(
  request: Request,
  experimentId: string,
  variants: string[],
): { variant: string; isNew: boolean } {
  const cookieName = `exp_${experimentId}`;
  const cookies = request.headers.get('cookie') ?? '';

  // Controlla se l'utente ha già un'assegnazione
  const match = cookies.match(new RegExp(`${cookieName}=([^;]+)`));
  if (match && variants.includes(match[1])) {
    return { variant: match[1], isNew: false };
  }

  // Nuova assegnazione: hash deterministico basato su IP + UA per consistenza
  const ip = request.headers.get('cf-connecting-ip') ?? '';
  const ua = request.headers.get('user-agent') ?? '';
  const seed = `${ip}:${ua}:${experimentId}`;

  // Hash semplice per distribuzione
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0;
  }
  const index = Math.abs(hash) % variants.length;

  return { variant: variants[index], isNew: true };
}

export default {
  async fetch(request: Request): Promise<Response> {
    const { variant, isNew } = getExperimentVariant(
      request,
      'homepage-redesign-2026',
      ['control', 'variant-a', 'variant-b'],
    );

    // Rewrite URL o modifica header per il backend
    const url = new URL(request.url);
    url.searchParams.set('variant', variant);

    const response = await fetch(url.toString(), request);
    const newResponse = new Response(response.body, response);

    if (isNew) {
      newResponse.headers.append(
        'Set-Cookie',
        `exp_homepage-redesign-2026=${variant}; Path=/; Max-Age=2592000; SameSite=Lax`,
      );
    }

    return newResponse;
  },
};
```

### Autenticazione all'edge

Validare JWT all'edge per bloccare richieste non autenticate prima che raggiungano l'origin.

```typescript
// edge-jwt-validation.ts
// Usa la libreria 'jose' compatibile con edge runtime

async function verifyJwt(
  token: string,
  publicKeyJwk: JsonWebKey,
): Promise<{ valid: boolean; payload?: Record<string, unknown>; error?: string }> {
  try {
    const key = await crypto.subtle.importKey(
      'jwk',
      publicKeyJwk,
      { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
      false,
      ['verify'],
    );

    const [headerB64, payloadB64, signatureB64] = token.split('.');
    if (!headerB64 || !payloadB64 || !signatureB64) {
      return { valid: false, error: 'Formato JWT non valido' };
    }

    const signingInput = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
    const signature = base64UrlDecode(signatureB64);

    const valid = await crypto.subtle.verify(
      'RSASSA-PKCS1-v1_5',
      key,
      signature,
      signingInput,
    );

    if (!valid) {
      return { valid: false, error: 'Firma non valida' };
    }

    const payload = JSON.parse(atob(payloadB64.replace(/-/g, '+').replace(/_/g, '/')));

    // Controlla scadenza
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
      return { valid: false, error: 'Token scaduto' };
    }

    return { valid: true, payload };
  } catch {
    return { valid: false, error: 'Errore di validazione' };
  }
}

function base64UrlDecode(input: string): ArrayBuffer {
  const base64 = input.replace(/-/g, '+').replace(/_/g, '/');
  const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}
```

### Personalizzazione

Servire contenuto diverso in base a device, lingua, AB variant, o user segment — tutto all'edge senza latenza.

```typescript
function personalizeRequest(request: Request): Request {
  const url = new URL(request.url);
  const ua = request.headers.get('user-agent') ?? '';
  const acceptLanguage = request.headers.get('accept-language') ?? '';

  // Device detection
  const isMobile = /Mobile|Android|iPhone/i.test(ua);
  url.searchParams.set('device', isMobile ? 'mobile' : 'desktop');

  // Language detection
  const preferredLang = acceptLanguage.split(',')[0]?.split(';')[0]?.trim() ?? 'en';
  url.searchParams.set('lang', preferredLang.slice(0, 2));

  // Returning visitor detection
  const cookies = request.headers.get('cookie') ?? '';
  const isReturning = cookies.includes('visited=true');
  url.searchParams.set('returning', String(isReturning));

  return new Request(url.toString(), request);
}
```

### Image optimization

Trasformazioni immagini all'edge senza inviare traffico all'origin per resize/format.

```typescript
// Cloudflare Image Resizing all'edge
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (!url.pathname.startsWith('/images/')) {
      return fetch(request);
    }

    const ua = request.headers.get('user-agent') ?? '';
    const acceptHeader = request.headers.get('accept') ?? '';

    // Scegli formato ottimale
    let format: 'avif' | 'webp' | 'jpeg' = 'jpeg';
    if (acceptHeader.includes('image/avif')) {
      format = 'avif';
    } else if (acceptHeader.includes('image/webp')) {
      format = 'webp';
    }

    // Scegli dimensione in base al device
    const isMobile = /Mobile|Android|iPhone/i.test(ua);
    const width = isMobile ? 640 : 1280;

    // Cloudflare Image Resizing
    return fetch(request, {
      cf: {
        image: {
          width,
          quality: 80,
          format,
          fit: 'cover',
        },
      },
    } as RequestInit);
  },
};
```

---

## CDN e caching all'edge

### Cache-Control

Header fondamentale per il controllo della cache a tutti i livelli (browser, CDN, edge).

```
Cache-Control: public, max-age=3600, s-maxage=86400, stale-while-revalidate=3600
```

| Direttiva | Significato |
|---|---|
| `public` | Qualsiasi cache può memorizzare la risposta |
| `private` | Solo la cache del browser, non CDN |
| `no-cache` | Cache ammessa ma deve rivalidare con origin prima di servire |
| `no-store` | Nessuna cache in nessun punto |
| `max-age=N` | La cache del browser può servire per N secondi |
| `s-maxage=N` | La cache CDN/edge può servire per N secondi (sovrascrive max-age per shared cache) |
| `stale-while-revalidate=N` | Servi contenuto stale per N secondi mentre rivalidi in background |
| `stale-if-error=N` | Servi contenuto stale per N secondi se l'origin è in errore |
| `must-revalidate` | Non servire stale dopo scadenza; rivalidare o errore |
| `immutable` | Il contenuto non cambierà mai (per URL con hash nel filename) |

**Strategie per tipo di contenuto:**

```typescript
const CACHE_STRATEGIES: Record<string, string> = {
  // Asset statici con hash nel filename → cache aggressiva
  'static-hashed':
    'public, max-age=31536000, immutable',

  // HTML di pagine → cache breve con revalidation
  'html':
    'public, max-age=0, s-maxage=60, stale-while-revalidate=300',

  // API responses → nessuna cache di default
  'api-default':
    'private, no-cache',

  // API responses pubbliche cacheable → cache breve
  'api-public':
    'public, max-age=0, s-maxage=30, stale-while-revalidate=60',

  // Dati utente → mai cacheare su CDN
  'user-data':
    'private, no-store',

  // Font → cache lunga
  'font':
    'public, max-age=31536000, immutable',

  // Immagini → cache media con revalidation
  'image':
    'public, max-age=86400, s-maxage=604800, stale-while-revalidate=86400',
};
```

### Stale-While-Revalidate

Pattern fondamentale per bilanciare freschezza dei dati e latenza percepita. L'edge serve il contenuto stale immediatamente e richiede una copia fresca dall'origin in background.

```
Timeline:
t=0    Client richiede risorsa → CDN serve dalla cache (fresca) → latenza ~5ms
t=60   max-age scade → risorsa è "stale"
t=61   Client richiede → CDN serve stale (latenza ~5ms) + richiede aggiornamento a origin
t=61.5 Origin risponde → CDN aggiorna la cache
t=62   Prossima richiesta → CDN serve la versione fresca
t=360  stale-while-revalidate scade → CDN non serve più stale, attende origin
```

### Edge-Side Includes (ESI)

Standard per assemblare pagine all'edge da frammenti con TTL diversi. Supportato da Cloudflare, Akamai, Fastly (con alcune variazioni).

```html
<!-- Pagina principale: cache 1 ora -->
<html>
<body>
  <!-- Header con nome utente: no cache -->
  <esi:include src="/fragments/user-header" />

  <!-- Contenuto principale: cache 1 ora -->
  <main>
    <h1>Prodotti in evidenza</h1>
    <!-- Widget prodotti: cache 5 minuti -->
    <esi:include src="/fragments/featured-products" />
  </main>

  <!-- Footer: cache 24 ore -->
  <esi:include src="/fragments/footer" />
</body>
</html>
```

Ogni frammento ha il proprio TTL, permettendo personalizzazione parziale senza invalidare l'intera pagina.

### Surrogate Keys / Cache Tags

Invalidazione granulare della cache edge. Invece di purgare per URL, si taggano le risposte e si purga per tag.

```typescript
// All'origin: tagga la risposta
function addCacheTags(
  response: Response,
  tags: string[],
): Response {
  const newResponse = new Response(response.body, response);
  // Cloudflare usa Cache-Tag, Fastly usa Surrogate-Key
  newResponse.headers.set('Cache-Tag', tags.join(','));
  newResponse.headers.set('Surrogate-Key', tags.join(' '));
  return newResponse;
}

// Esempio: pagina prodotto taggata con categoria e prodotto ID
// Cache-Tag: product-42, category-electronics, page-product
// Quando il prodotto 42 viene aggiornato: purga "product-42"
// Quando la categoria cambia: purga "category-electronics"
```

---

## WAF — Web Application Firewall

Il WAF opera all'edge, tra il client e l'origin, filtrando richieste malevole prima che raggiungano l'applicazione.

### Tipi di regole

| Tipo | Descrizione | Esempio |
|---|---|---|
| **Managed rulesets** | Regole mantenute dal provider | OWASP Core Rule Set, Cloudflare Managed Rules |
| **Custom rules** | Regole specifiche per l'applicazione | Blocca pattern specifici di abuso |
| **Rate-based rules** | Limitano traffico basandosi su frequenza | Blocca IP con >100 req/5min su `/api/login` |
| **IP reputation** | Basate su threat intelligence | Blocca IP noti come botnet |
| **Geo-blocking** | Basate su paese/regione | Blocca traffico da paesi non serviti |
| **Bot score rules** | Basate su punteggio bot | Challenge se bot score > 50 |

### Regole WAF custom — Cloudflare (esempio)

```json
{
  "rules": [
    {
      "description": "Blocca SQL injection in query params",
      "expression": "(http.request.uri.query contains \"UNION SELECT\" or http.request.uri.query contains \"1=1\" or http.request.uri.query contains \"OR 1\")",
      "action": "block"
    },
    {
      "description": "Rate limit login endpoint",
      "expression": "(http.request.uri.path eq \"/api/auth/login\" and http.request.method eq \"POST\")",
      "action": "challenge",
      "ratelimit": {
        "requests_per_period": 5,
        "period": 300
      }
    },
    {
      "description": "Blocca User-Agent vuoti su API",
      "expression": "(http.request.uri.path matches \"^/api/\" and not http.user_agent ne \"\")",
      "action": "block"
    },
    {
      "description": "Richiedi challenge per paesi ad alto rischio",
      "expression": "(ip.geoip.country in {\"XX\" \"YY\"} and http.request.uri.path matches \"^/api/\")",
      "action": "managed_challenge"
    }
  ]
}
```

### Rate-based rules vs application rate limiting

| Aspetto | WAF rate-based rules | Application rate limiting |
|---|---|---|
| Dove esegue | Edge/WAF | Application server |
| Granularità | IP, header, path pattern | User ID, API key, custom logic |
| Configurazione | Dashboard/API del provider | Codice applicativo |
| Flessibilità | Regole pattern-based | Logica arbitraria |
| Costo | Incluso nel piano WAF | Richiede infrastruttura (Redis) |
| Velocità di attivazione | Immediata (edge) | Richiede deploy |
| Uso ideale | Difesa volumetrica, DDoS L7 | Business logic, quota management |

Nella pratica si usano entrambi: WAF per la difesa perimetrale gross-grained, application rate limiting per logica fine-grained di business.

---

## Bot management

### Fingerprinting

Il fingerprinting combina molteplici segnali per creare un identificatore univoco del client, anche senza cookie.

**Segnali lato server:**
- TLS fingerprint (JA3/JA4 hash)
- HTTP/2 fingerprint (settings, window size, priority)
- Header order e capitalizzazione
- IP + ASN + geolocation
- Accept-Language, Accept-Encoding pattern

**Segnali lato client (JavaScript):**
- Canvas fingerprint
- WebGL renderer
- Screen resolution + color depth
- Timezone + locale
- Font enumeration
- Audio context fingerprint
- Battery API (deprecato su molti browser)
- Hardware concurrency

```typescript
// Calcolo del punteggio bot lato server
interface RequestSignals {
  userAgent: string;
  acceptLanguage: string;
  acceptEncoding: string;
  ja3Hash: string;
  httpVersion: string;
  headerOrder: string[];
  ipReputation: number;     // 0 = pulito, 100 = botnet nota
  asn: number;
  country: string;
  requestTimingMs: number;  // tempo tra richieste successive
}

function calculateBotScore(signals: RequestSignals): number {
  let score = 0; // 0 = certamente umano, 100 = certamente bot

  // User-Agent assente o sospetto
  if (!signals.userAgent) score += 30;
  if (/bot|crawler|spider|scraper/i.test(signals.userAgent)) score += 20;
  if (/python|curl|wget|go-http|java\//i.test(signals.userAgent)) score += 25;

  // Accept-Language assente (bot spesso non lo inviano)
  if (!signals.acceptLanguage) score += 10;

  // Timing troppo regolare tra richieste (< 5% varianza)
  if (signals.requestTimingMs > 0 && signals.requestTimingMs < 100) score += 15;

  // IP reputation
  score += signals.ipReputation * 0.3;

  // JA3 hash noto come bot
  const knownBotJA3 = new Set([
    // Inserire hash noti di bot frameworks
  ]);
  if (knownBotJA3.has(signals.ja3Hash)) score += 40;

  // ASN di hosting provider (non residenziale)
  const hostingASNs = new Set([
    // AWS, GCP, Azure, DigitalOcean, etc.
  ]);
  if (hostingASNs.has(signals.asn)) score += 15;

  return Math.min(100, score);
}
```

### CAPTCHA

Tipi di challenge in ordine di intrusività crescente:

1. **Invisible challenge:** nessuna interazione utente. Analisi comportamentale passiva.
2. **Checkbox ("Non sono un robot"):** basso attrito, analisi di mouse movement.
3. **Visual challenge:** seleziona immagini, trascrivi testo. Alto attrito.
4. **Proof of Work:** calcolo computazionale nel browser. Nessuna interazione.

**Integrazione edge con hCaptcha:**

```typescript
async function verifyCaptcha(
  token: string,
  secret: string,
  remoteIp: string,
): Promise<{ success: boolean; score: number }> {
  const response = await fetch('https://hcaptcha.com/siteverify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      secret,
      response: token,
      remoteip: remoteIp,
    }),
  });

  const result = await response.json<{
    success: boolean;
    score: number;
    'error-codes': string[];
  }>();

  return { success: result.success, score: result.score ?? 0 };
}
```

### Analisi comportamentale

Monitoraggio del comportamento nel tempo per distinguere bot sofisticati da utenti reali.

**Indicatori:**
- **Velocità di navigazione:** bot visitano pagine troppo velocemente
- **Pattern di crawling:** bot seguono strutture (A→B→C→D); umani sono erratici
- **Assenza di risorse secondarie:** bot spesso non caricano CSS, JS, immagini
- **Session depth:** bot visitano molte pagine senza interazione
- **Form filling speed:** compilazione form < 2 secondi è sospetta
- **Mouse movement entropy:** movimenti troppo lineari o assenti

```typescript
interface SessionBehavior {
  pagesVisited: number;
  sessionDurationMs: number;
  resourcesLoaded: boolean;    // JS, CSS, immagini caricate?
  mouseMovements: number;
  scrollEvents: number;
  formFillingTimeMs: number;
  errorRate: number;           // % di richieste con errore
}

function analyzeBehavior(session: SessionBehavior): {
  botProbability: number;
  flags: string[];
} {
  const flags: string[] = [];
  let botProbability = 0;

  // Pagine per minuto > 60 è sospetto
  const pagesPerMinute = session.pagesVisited / (session.sessionDurationMs / 60_000);
  if (pagesPerMinute > 60) {
    flags.push('navigazione_troppo_veloce');
    botProbability += 25;
  }

  // Nessuna risorsa secondaria caricata
  if (!session.resourcesLoaded && session.pagesVisited > 3) {
    flags.push('risorse_non_caricate');
    botProbability += 20;
  }

  // Nessuna interazione mouse/scroll
  if (session.mouseMovements === 0 && session.scrollEvents === 0 && session.pagesVisited > 5) {
    flags.push('nessuna_interazione');
    botProbability += 30;
  }

  // Form compilato troppo velocemente
  if (session.formFillingTimeMs > 0 && session.formFillingTimeMs < 2_000) {
    flags.push('form_troppo_veloce');
    botProbability += 20;
  }

  return {
    botProbability: Math.min(100, botProbability),
    flags,
  };
}
```

---

## Rate limiting adattivo e mitigazione DDoS all'edge

Il rate limiting statico con soglie fisse è il punto di partenza, ma presenta un limite fondamentale: le soglie corrette in condizioni normali diventano troppo permissive durante un attacco e troppo restrittive durante picchi legittimi (lancio prodotto, evento virale, Black Friday). Il rate limiting adattivo risolve questo problema regolando dinamicamente i limiti in base a metriche di sistema in tempo reale.

### Feedback loop adattivo

Il pattern fondamentale è un loop di retroazione: misura → analizza → regola → misura.

```typescript
interface SystemMetrics {
  cpuUtilization: number;       // 0-100%
  memoryUtilization: number;    // 0-100%
  p99LatencyMs: number;         // latenza P99 delle risposte
  errorRate: number;            // % di risposte 5xx
  activeConnections: number;    // connessioni concorrenti
  queueDepth: number;           // richieste in coda
  requestsPerSecond: number;    // RPS corrente
}

interface AdaptiveLimits {
  globalRps: number;
  perIpRps: number;
  perUserRps: number;
  burstMultiplier: number;
}

class AdaptiveRateLimitController {
  private currentLimits: AdaptiveLimits;
  private readonly baseLimits: AdaptiveLimits;
  private readonly minLimits: AdaptiveLimits;
  private history: SystemMetrics[] = [];

  constructor(baseLimits: AdaptiveLimits) {
    this.baseLimits = { ...baseLimits };
    this.currentLimits = { ...baseLimits };
    this.minLimits = {
      globalRps: baseLimits.globalRps * 0.05,   // minimo 5% del base
      perIpRps: Math.max(1, baseLimits.perIpRps * 0.1),
      perUserRps: Math.max(1, baseLimits.perUserRps * 0.1),
      burstMultiplier: 1.0,
    };
  }

  /**
   * Ricalcola i limiti in base allo stato corrente del sistema.
   * Chiamato periodicamente (ogni 5-10 secondi).
   */
  adjustLimits(metrics: SystemMetrics): AdaptiveLimits {
    this.history.push(metrics);
    if (this.history.length > 60) this.history.shift(); // ultimi 5 minuti a 5s

    // Calcola un "health score" composito (0 = sistema in crisi, 100 = sano)
    const healthScore = this.computeHealthScore(metrics);

    // Mappa lo health score a un moltiplicatore dei limiti
    let multiplier: number;
    if (healthScore >= 80) {
      // Sistema sano: limiti normali o leggermente elevati
      multiplier = 1.0 + (healthScore - 80) * 0.01; // max 1.2
    } else if (healthScore >= 50) {
      // Sotto stress: riduzione graduale
      multiplier = 0.3 + (healthScore - 50) * 0.023; // 0.3 a 1.0
    } else if (healthScore >= 20) {
      // Stress severo: riduzione aggressiva
      multiplier = 0.1 + (healthScore - 20) * 0.0067; // 0.1 a 0.3
    } else {
      // Crisi: limiti minimi
      multiplier = 0.05;
    }

    // Applica smoothing per evitare oscillazioni (EWMA)
    const alpha = 0.3; // smoothing factor
    const prevMultiplier =
      this.currentLimits.globalRps / this.baseLimits.globalRps;
    const smoothedMultiplier =
      alpha * multiplier + (1 - alpha) * prevMultiplier;

    this.currentLimits = {
      globalRps: Math.max(
        this.minLimits.globalRps,
        Math.floor(this.baseLimits.globalRps * smoothedMultiplier),
      ),
      perIpRps: Math.max(
        this.minLimits.perIpRps,
        Math.floor(this.baseLimits.perIpRps * smoothedMultiplier),
      ),
      perUserRps: Math.max(
        this.minLimits.perUserRps,
        Math.floor(this.baseLimits.perUserRps * smoothedMultiplier),
      ),
      burstMultiplier: Math.max(1.0, smoothedMultiplier),
    };

    return this.currentLimits;
  }

  private computeHealthScore(m: SystemMetrics): number {
    let score = 100;

    // CPU: penalizza sopra il 60%
    if (m.cpuUtilization > 60) {
      score -= (m.cpuUtilization - 60) * 1.5; // max -60
    }

    // Latenza: penalizza sopra 200ms P99
    if (m.p99LatencyMs > 200) {
      score -= Math.min(30, (m.p99LatencyMs - 200) / 10);
    }

    // Error rate: penalizza pesantemente
    if (m.errorRate > 1) {
      score -= m.errorRate * 5; // 5% error rate → -25
    }

    // Trend: se le metriche peggiorano rispetto ai 30s precedenti, penalizza extra
    if (this.history.length >= 6) {
      const recent = this.history.slice(-6);
      const latencyTrend =
        recent[5].p99LatencyMs - recent[0].p99LatencyMs;
      if (latencyTrend > 100) score -= 10; // latenza in crescita rapida
    }

    return Math.max(0, Math.min(100, score));
  }
}
```

### DDoS application-layer (L7) all'edge

Gli attacchi DDoS L7 sono i più insidiosi perché imitano traffico legittimo. A differenza degli attacchi volumetrici (L3/L4) che possono essere mitigati con BGP blackholing o scrubbing center, gli attacchi L7 richiedono ispezione della richiesta.

**Pattern di attacco L7 comuni:**

| Pattern | Descrizione | Segnali di rilevamento |
|---|---|---|
| **HTTP flood** | Alto volume di GET/POST valide | RPS anomalo, distribuzione IP sospetta |
| **Slowloris** | Connessioni lente che tengono occupati i thread | Timeout connection elevati, bassa bandwidth per conn |
| **Low-and-slow** | Richieste lente ma continue, sotto la soglia di rate limiting | Latenza crescente senza picco RPS |
| **Cache busting** | Query param casuali per bypassare la CDN cache | Cache hit ratio in calo, URL unici in aumento |
| **API abuse** | Richieste valide ma costose (search, report) | Costo computazionale per IP anomalo |
| **Credential stuffing** | Login massivo con credenziali rubate | Spike su `/login`, error rate alto |

**Strategia di mitigazione multi-livello all'edge:**

```
┌────────────────────────────────────────────────────────────────┐
│ Livello 1 — CDN/Edge (Cloudflare, Fastly, AWS Shield)         │
│   ├── IP reputation blocklist                                  │
│   ├── Rate limit WAF (pattern-based, 429)                     │
│   ├── Challenge page (JS challenge, managed challenge)         │
│   └── Geo-blocking per regioni non servite                    │
├────────────────────────────────────────────────────────────────┤
│ Livello 2 — Edge Function (Workers, Edge Middleware)           │
│   ├── Bot score calculation (JA3, header fingerprint)          │
│   ├── Adaptive rate limiting (health score feedback)           │
│   ├── Proof of Work per richieste sospette                    │
│   └── Request costing (blocca richieste troppo costose)       │
├────────────────────────────────────────────────────────────────┤
│ Livello 3 — Application Rate Limiting                          │
│   ├── Per-user / per-API-key limiting                          │
│   ├── Concurrency limiting                                     │
│   ├── Queue-based throttling                                   │
│   └── Circuit breaker su dipendenze                           │
├────────────────────────────────────────────────────────────────┤
│ Livello 4 — Infrastructure                                     │
│   ├── Auto-scaling                                             │
│   ├── Load shedding                                            │
│   └── Graceful degradation                                     │
└────────────────────────────────────────────────────────────────┘
```

### Proof of Work all'edge come anti-DDoS

Il Proof of Work (PoW) client-side è un meccanismo che costringe il client a spendere risorse computazionali prima di poter effettuare una richiesta. Questo rende gli attacchi DDoS economicamente svantaggiosi per l'attaccante.

```typescript
// Edge Worker: verifica Proof of Work
interface PowChallenge {
  difficulty: number;   // numero di zeri iniziali richiesti nell'hash
  prefix: string;       // prefisso casuale della challenge
  timestamp: number;    // timestamp di emissione
  maxAgeMs: number;     // validità massima della challenge
}

async function verifyProofOfWork(
  challenge: PowChallenge,
  nonce: string,
): Promise<boolean> {
  const now = Date.now();

  // Verifica scadenza
  if (now - challenge.timestamp > challenge.maxAgeMs) return false;

  // Calcola hash della soluzione
  const input = `${challenge.prefix}:${challenge.timestamp}:${nonce}`;
  const hashBuffer = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(input),
  );
  const hashHex = Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  // Verifica che l'hash inizi con N zeri
  const requiredPrefix = '0'.repeat(challenge.difficulty);
  return hashHex.startsWith(requiredPrefix);
}

// Difficulty adattiva: sotto attacco, aumenta la difficulty
function getAdaptiveDifficulty(healthScore: number): number {
  if (healthScore >= 80) return 0;  // nessuna PoW necessaria
  if (healthScore >= 50) return 3;  // facile (~8 tentativi medi)
  if (healthScore >= 20) return 4;  // medio (~16 tentativi)
  return 5;                          // difficile (~32 tentativi)
}
```

### Load shedding all'edge

Quando il sistema è sotto carico estremo, il load shedding scarica selettivamente traffico meno prioritario per proteggere le funzionalità critiche.

```typescript
type RequestPriority = 'critical' | 'high' | 'normal' | 'low' | 'background';

function classifyRequestPriority(
  request: Request,
  isAuthenticated: boolean,
): RequestPriority {
  const url = new URL(request.url);
  const path = url.pathname;

  // Pagamenti e checkout: sempre critici
  if (path.startsWith('/api/payments') || path.startsWith('/api/checkout')) {
    return 'critical';
  }

  // API autenticate di core business
  if (isAuthenticated && path.startsWith('/api/orders')) return 'high';

  // Ricerca e navigazione
  if (path.startsWith('/api/search') || path.startsWith('/api/products')) {
    return 'normal';
  }

  // Analytics, tracking, non essenziali
  if (path.startsWith('/api/analytics') || path.startsWith('/api/tracking')) {
    return 'background';
  }

  return 'low';
}

function shouldShedRequest(
  priority: RequestPriority,
  healthScore: number,
): boolean {
  const shedThresholds: Record<RequestPriority, number> = {
    critical:   0,    // non scaricare mai
    high:       15,   // solo in crisi estrema
    normal:     40,   // sotto stress moderato
    low:        60,   // appena il sistema rallenta
    background: 80,   // quasi sempre sotto qualsiasi pressione
  };

  return healthScore < shedThresholds[priority];
}
```

---

## Monitoraggio e alerting avanzato

### Monitoraggio dedicato al rate limiting

Oltre alle metriche base già descritte, un sistema di rate limiting maturo richiede monitoraggio specifico per l'edge e per il rate limiting adattivo.

**Metriche aggiuntive per rate limiting adattivo:**

| Metrica | Descrizione | Allarme se |
|---|---|---|
| `adaptive_health_score` | Health score corrente del sistema | < 30 per > 2 minuti |
| `adaptive_limit_multiplier` | Moltiplicatore corrente dei limiti | < 0.2 (limiti ridotti all'80%) |
| `adaptive_adjustments_total` | Numero di aggiustamenti dei limiti | > 20 in 5 minuti (oscillazione) |
| `pow_challenges_issued` | Challenge PoW emesse | > 0 indica stress |
| `pow_challenges_failed` | Challenge PoW fallite (possibili bot) | > 50% delle emesse |
| `load_shed_total` | Richieste scaricate per load shedding | > 0 indica emergenza |
| `load_shed_by_priority` | Richieste scaricate per priorità | Richieste 'high' scaricate |
| `edge_rate_limit_latency` | Latenza del check all'edge | > 5ms (edge dovrebbe essere <1ms) |

**Dashboard consigliata per rate limiting adattivo:**

```
┌──────────────────────────────────────────────────────────┐
│ Panel 1: Health Score nel tempo                          │
│   Grafico a linea: health_score vs tempo                 │
│   Soglie: verde >80, giallo >50, rosso <50               │
├──────────────────────────────────────────────────────────┤
│ Panel 2: Limiti effettivi vs limiti base                  │
│   Due linee sovrapposte: base_limit, current_limit       │
│   Evidenzia gap tra le due                               │
├──────────────────────────────────────────────────────────┤
│ Panel 3: Distribuzione 429 per dimensione                │
│   Stacked bar: IP, user, endpoint, API key               │
├──────────────────────────────────────────────────────────┤
│ Panel 4: Top 10 IP/user bloccati                         │
│   Tabella aggiornata ogni 30s                            │
├──────────────────────────────────────────────────────────┤
│ Panel 5: Tasso di load shedding per priorità             │
│   Area chart: critical, high, normal, low, background    │
└──────────────────────────────────────────────────────────┘
```

### Metriche chiave

| Metrica | Descrizione | Allarme se |
|---|---|---|
| `rate_limit_total` | Richieste totali | Baseline per trend |
| `rate_limit_rejected` | Richieste bloccate (429) | > 5% del totale |
| `rate_limit_rejected_by_dimension` | Blocchi per IP/user/endpoint | Concentrazione su pochi IP |
| `unique_ips_limited` | IP distinti limitati | Spike improvviso |
| `p99_latency_rate_check` | Latenza del check rate limit | > 10ms (in-memory) o > 50ms (Redis) |
| `redis_rate_limit_errors` | Errori Redis | > 0 per 5 minuti |
| `false_positive_reports` | Segnalazioni utenti bloccati | Qualsiasi |
| `bot_score_distribution` | Distribuzione punteggi bot | Bimodale anomala |

### Dashboard

```typescript
// Esempio di metriche Prometheus-style
interface RateLimitMetrics {
  requestsTotal: Counter;
  requestsRejected: Counter;
  requestsRejectedByDimension: Counter; // labels: dimension
  rateLimitCheckDuration: Histogram;
  redisErrors: Counter;
  activeLimitedKeys: Gauge;
}

// Pseudo-implementazione con labels
function recordRateLimitDecision(
  metrics: RateLimitMetrics,
  result: { allowed: boolean; dimension: string; durationMs: number },
): void {
  metrics.requestsTotal.inc();
  metrics.rateLimitCheckDuration.observe(result.durationMs);

  if (!result.allowed) {
    metrics.requestsRejected.inc();
    metrics.requestsRejectedByDimension.inc({ dimension: result.dimension });
  }
}
```

### Alerting

Regole di alerting raccomandate:

```yaml
# Pseudo-configurazione alerting
alerts:
  - name: HighRateLimitRejectionRate
    condition: rate(rate_limit_rejected[5m]) / rate(rate_limit_total[5m]) > 0.10
    severity: warning
    message: "Più del 10% delle richieste rifiutate negli ultimi 5 minuti"

  - name: RateLimitStoreDown
    condition: rate(redis_rate_limit_errors[1m]) > 0
    severity: critical
    message: "Errori Redis per rate limiting — fallback a in-memory?"

  - name: SingleIPFlood
    condition: max(rate_limit_rejected_by_ip) > 1000
    severity: warning
    message: "Singolo IP con oltre 1000 richieste bloccate"

  - name: RateLimitCheckLatency
    condition: histogram_quantile(0.99, rate_limit_check_duration) > 0.050
    severity: warning
    message: "P99 latenza rate limit check > 50ms"

  - name: BotScoreAnomaly
    condition: avg(bot_score) > 50
    severity: info
    message: "Punteggio bot medio anomalmente alto — verificare traffico"
```

### Logging

Ogni reject dovrebbe produrre un log strutturato per analisi forensica:

```typescript
interface RateLimitLogEntry {
  timestamp: string;          // ISO 8601 UTC
  clientIp: string;
  userId: string | null;
  apiKey: string | null;      // maskerato: "sk-...abc"
  method: string;
  path: string;
  dimension: string;          // quale dimensione ha bloccato
  limit: number;
  currentCount: number;
  country: string;
  userAgent: string;
  botScore: number;
  action: 'reject' | 'challenge' | 'allow_monitored';
}

function logRateLimitEvent(entry: RateLimitLogEntry): void {
  // Maskerare API key per sicurezza
  const maskedKey = entry.apiKey
    ? `${entry.apiKey.slice(0, 3)}...${entry.apiKey.slice(-3)}`
    : null;

  console.log(JSON.stringify({
    ...entry,
    apiKey: maskedKey,
    // Non loggare User-Agent completo se troppo lungo
    userAgent: entry.userAgent.slice(0, 200),
  }));
}
```

---

## Matrice decisionale

### Confronto algoritmi di rate limiting

| Criterio | Fixed Window | Sliding Window Log | Sliding Window Counter | Token Bucket | Leaky Bucket | GCRA |
|---|---|---|---|---|---|---|
| **Precisione** | Bassa (boundary burst) | Perfetta | Buona (~) | Buona | Buona | Buona |
| **Memoria per chiave** | O(1) — un contatore | O(n) — log di timestamp | O(1) — due contatori | O(1) — token + timestamp | O(1) — queue + timestamp | O(1) — un timestamp |
| **Complessità impl.** | Molto bassa | Media | Bassa | Media | Media | Media |
| **Tolleranza burst** | No (sì al boundary) | No | Parziale | Sì (configurabile) | No | Sì (via τ) |
| **Throughput costante** | No | No | No | No | Sì | Sì |
| **Adatto a Redis** | Sì (INCR+EXPIRE) | Sì (ZADD+ZCOUNT) | Sì (2 INCR) | Sì (Lua script) | Sì (Lua script) | Sì (GET+SET) |
| **Uso tipico** | API semplici, MVP | Sicurezza, anti-abuse | API generiche | API commerciali | Traffic shaping | API ad alta scala |
| **Equità temporale** | Bassa | Alta | Media-alta | Media | Alta | Alta |

> **Nota:** la colonna GCRA è aggiunta come sesto algoritmo. GCRA è una variante del leaky bucket con la metà della memoria necessaria (un solo timestamp per client). Per dettagli vedi la sezione [GCRA](#6-gcra-generic-cell-rate-algorithm).

### Quando usare cosa

| Scenario | Algoritmo consigliato | Motivo |
|---|---|---|
| MVP / prototipo | Fixed Window | Implementazione in 20 righe |
| API pubblica commerciale | Token Bucket | Burst tollerato, parametri intuitivi per utenti |
| Anti-brute-force login | Sliding Window Log | Precisione massima, nessun boundary exploit |
| API interna ad alto traffico | Sliding Window Counter | Buon compromesso precisione/memoria |
| Streaming / queue processing | Leaky Bucket | Output rate costante |
| Multi-tenant con tier | Token Bucket + cost-based | Capacità e refill diversi per tier |
| Edge/CDN rate limiting | Fixed/Sliding Window Counter | Bassa memoria, adatto a KV store |
| Protezione DDoS L7 | WAF rate-based + adaptive | Gestito dal provider, reazione rapida |

### Confronto piattaforme edge

| Criterio | Cloudflare Workers | Vercel Edge | Lambda@Edge | Deno Deploy |
|---|---|---|---|---|
| **Runtime** | V8 Isolates | V8 (Edge Runtime) | Node.js (limitato) | Deno (V8) |
| **Cold start** | ~0ms | <100ms | 100-500ms | <10ms |
| **Stato persistente** | Durable Objects, KV | Nessuno (serve Upstash) | DynamoDB (esterno) | Deno KV |
| **Size limit** | 10 MB (paid) | 4 MB | 1-50 MB | 20 MB |
| **Timeout** | Non applicabile (CPU time) | 30s | 5-30s | ~50s |
| **Costo base** | Free tier generoso | Con Vercel Pro | Pay-per-request | Free tier |
| **Node.js compat** | Parziale (polyfill) | Parziale | Sì (con limiti) | Parziale (npm compat) |
| **PoP globali** | 300+ | ~60 | 200+ (CloudFront) | 35+ |
| **Rate limit integrato** | Sì (Durable Objects) | No (serve Upstash) | No (serve WAF) | Sì (Deno KV) |
| **Ideal use case** | Full edge apps | Next.js middleware | CloudFront customization | Deno-native apps |

---

## Troubleshooting

### Problema 1 — Falsi positivi su utenti dietro NAT/CGNAT

**Sintomo:** Molti utenti legittimi bloccati dallo stesso IP.

**Causa:** Carrier-grade NAT (CGNAT) fa sì che migliaia di utenti condividano un singolo IP pubblico. Limitare per IP blocca tutti.

**Soluzione:** Non usare IP come unica dimensione. Combinare IP + fingerprint del browser, o richiedere autenticazione per endpoint sensibili. Per utenti anonimi, usare limiti più generosi per IP e aggiungere un cookie di sessione come discriminante aggiuntivo.

---

### Problema 2 — Boundary burst con Fixed Window

**Sintomo:** Picchi di traffico a cavallo di due finestre consecutive superano il limite effettivo.

**Causa:** Client concentra richieste alla fine della finestra N e all'inizio della finestra N+1.

**Soluzione:** Sostituire Fixed Window con Sliding Window Counter. Costo minimo di implementazione, elimina il 95% dei boundary burst.

---

### Problema 3 — Race condition su INCR + EXPIRE in Redis

**Sintomo:** Chiavi Redis senza TTL che crescono all'infinito.

**Causa:** Crash tra `INCR` e `EXPIRE`. La chiave esiste ma non scade mai.

**Soluzione:** Usare un Lua script atomico che esegue `INCR` e `EXPIRE` in un'unica operazione. In alternativa, includere il window timestamp nella chiave (es. `ratelimit:user42:1716400000`) e impostare `EXPIRE` solo al primo `INCR` (quando `INCR` ritorna 1).

---

### Problema 4 — Stato distribuito inconsistente tra regioni

**Sintomo:** Un utente in Europa vede limiti diversi rispetto allo stesso utente reindirizzato in US.

**Causa:** Rate limiter usa Redis locale per regione senza sincronizzazione.

**Soluzione:** Usare Redis con replica cross-region (es. Upstash Global) o accettare limiti per-region indipendenti (Ns × il limite globale, dove Ns è il numero di regioni). Documentare il comportamento.

---

### Problema 5 — Edge cold start su Lambda@Edge

**Sintomo:** Prime richieste dopo un periodo di inattività hanno latenza 300-500ms.

**Causa:** Lambda@Edge crea un nuovo container per ogni PoP al primo invoke.

**Soluzione:** Usare CloudFront Functions per logica leggera (rate limiting semplice) che non ha cold start. Per logica complessa, usare provisioned concurrency o ping periodico (warm-up cron). Valutare migrazione a Cloudflare Workers che non ha cold start.

---

### Problema 6 — Retry storm dopo risposta 429

**Sintomo:** Dopo un blocco di rate limiting, il traffico aumenta invece di diminuire.

**Causa:** Client non implementano backoff esponenziale. Riprovano immediatamente e continuamente.

**Soluzione:** Includere sempre `Retry-After` header con valore preciso. Nella documentazione API, specificare il backoff atteso. Server-side: considerare penalty escalation (il retry immediato dopo 429 alza il tempo di blocco).

---

### Problema 7 — Rate limiter diventa bottleneck

**Sintomo:** Latenza P99 del rate limit check supera 100ms.

**Causa:** Redis sovraccarico con troppe operazioni `ZADD`/`ZRANGEBYSCORE` (sliding window log).

**Soluzione:** Sostituire sliding window log con sliding window counter (O(1) per operazione). Usare Redis pipeline per batch. Aggiungere un local cache in-memory con TTL breve (1-5s) per chiavi ad alto traffico.

---

### Problema 8 — Bypass tramite rotazione IP

**Sintomo:** Bot cambia IP ad ogni richiesta, il rate limit per IP è inefficace.

**Causa:** Botnet con pool di IP residenziali o proxy rotanti.

**Soluzione:** Rate limit per IP non è sufficiente. Aggiungere fingerprinting (JA3, header order), behavioral analysis, e challenge page. Integrare IP reputation feed. Per API autenticate, limitare per user ID / API key.

---

### Problema 9 — Memory leak nel rate limiter in-memory

**Sintomo:** Consumo di memoria del processo cresce indefinitamente.

**Causa:** Nessun cleanup delle entry scadute nella `Map`.

**Soluzione:** Implementare cleanup periodico con `setInterval`. Usare `WeakRef` dove applicabile. Impostare un hard limit sul numero di chiavi e applicare LRU eviction.

---

### Problema 10 — Rate limit non rispettato con Server-Sent Events o WebSocket

**Sintomo:** Un client apre una singola connessione SSE/WebSocket e riceve dati illimitati.

**Causa:** Il rate limiter conta solo richieste HTTP, non messaggi su connessioni persistenti.

**Soluzione:** Implementare rate limiting a livello di messaggio, non di connessione. Contare i messaggi inviati per connessione e disconnettere se superano il limite. Per WebSocket, usare frame-level throttling.

---

### Problema 11 — Header X-Forwarded-For spoofati

**Sintomo:** Client malevoli inviano header `X-Forwarded-For: 1.2.3.4` con IP falsi, bypassando il rate limit per IP.

**Causa:** Il server si fida dell'header senza verificare la catena di proxy.

**Soluzione:** Usare l'IP inserito dall'ultimo proxy trusted. Se dietro Cloudflare, usare `CF-Connecting-IP`. Se dietro AWS ALB, prendere l'ultimo IP di `X-Forwarded-For` (quello inserito dall'ALB). Non fidarsi mai del primo IP se il proxy non lo sanitizza.

---

### Problema 12 — Durable Objects raggiungono il limite di throughput

**Sintomo:** Rate limiter basato su Durable Objects restituisce errori 503 sotto carico elevato.

**Causa:** Un singolo Durable Object gestisce tutte le richieste per una chiave. Sotto carico elevato (>100 req/s per chiave), diventa bottleneck.

**Soluzione:** Sharding: distribuire le richieste su più Durable Objects usando un hash della chiave. Es. `RATE_LIMITER.idFromName(${key}:${hash % 10})` e sommare i contatori. Accettare imprecisione marginale in cambio di scalabilità.

---

### Problema 13 — Rate limit troppo aggressivo su webhook

**Sintomo:** Webhook di partner/integrazioni bloccati da rate limiting generico.

**Causa:** Webhook IP o endpoint non esclusi dalle regole generiche.

**Soluzione:** Creare allowlist per IP noti dei webhook provider. Usare chiavi API dedicate per webhook con limiti separati. Validare la firma del webhook prima di contare la richiesta nel rate limit.

---

### Problema 14 — Failover Redis non gestito

**Sintomo:** Quando Redis non è disponibile, tutte le richieste sono bloccate (o tutte passano).

**Causa:** Nessuna strategia di fallback per il rate limiter.

**Soluzione:** Implementare fallback a in-memory rate limiting quando Redis è down. Politica di default: "fail open" (accetta tutte le richieste) è meglio di "fail closed" (blocca tutto) per la user experience, a meno che non ci siano motivi di sicurezza per fare il contrario. Loggare ogni failover per analisi.

```typescript
async function resilientRateLimit(
  redisLimiter: RedisFixedWindowLimiter,
  memoryLimiter: FixedWindowRateLimiter,
  key: string,
): Promise<{ allowed: boolean; source: 'redis' | 'memory' | 'failopen' }> {
  try {
    const result = await redisLimiter.check(key);
    return { ...result, source: 'redis' };
  } catch (error) {
    // Redis down: fallback a in-memory
    console.error('Redis rate limit fallback', { error, key });
    try {
      const result = memoryLimiter.check(key);
      return { ...result, source: 'memory' };
    } catch {
      // Anche in-memory fallito: fail open
      return { allowed: true, source: 'failopen' };
    }
  }
}
```

---

### Problema 15 — Limiti non documentati causano frustrazione sviluppatori

**Sintomo:** Sviluppatori terzi segnalano errori 429 inaspettati. Supporto tecnico sovraccarico.

**Causa:** I limiti non sono documentati o gli header non sono presenti nelle risposte.

**Soluzione:** Documentare i limiti per ogni tier nella API reference. Includere header `X-RateLimit-*` su ogni risposta (non solo su 429). Fornire un endpoint `/api/rate-limit-status` che mostra la quota corrente dell'utente.

---

### Problema 16 — Edge function supera il limite di CPU time

**Sintomo:** Cloudflare Worker termina con errore "Exceeded CPU time limit" su operazioni di rate limiting complesse.

**Causa:** Logica troppo complessa (es. calcolo hash crittografico + query KV + Durable Object fetch) supera il budget CPU di 10-50ms.

**Soluzione:** Semplificare la logica all'edge: usare Fixed Window con KV store (una lettura + una scrittura). Spostare logica complessa (behavioral analysis, aggregazione multi-dimensionale) a un servizio backend asincrono. L'edge fa solo il check veloce.

---

## FAQ

### 1. Qual è la differenza tra rate limiting e throttling?

**Rate limiting** rifiuta le richieste che superano il limite (risposta 429). **Throttling** rallenta le richieste in eccesso mettendole in coda o ritardandole (la risposta arriva, ma con latenza aumentata). Il rate limiting è più comune per API; il throttling è più adatto a sistemi interni dove si preferisce rallentare piuttosto che rifiutare.

---

### 2. Devo usare rate limiting per IP o per utente?

Entrambi. Per IP intercetta traffico anonimo e bot; per utente previene abuso da account autenticati. Implementa prima per IP (difesa perimetrale), poi aggiungi per utente per API autenticate. Considerare anche per API key per scenari B2B.

---

### 3. Come gestisco il rate limiting con microservizi?

Centralizzare lo stato in Redis o in un servizio dedicato di rate limiting. Ogni microservizio consulta lo stesso store. In alternativa, usare un API gateway (Kong, Envoy, AWS API Gateway) come punto unico di enforcement dei limiti.

---

### 4. È sicuro usare rate limiting in-memory in produzione?

Solo se hai una singola istanza e puoi accettare il reset dei contatori al riavvio. Con più istanze, ogni processo ha il proprio contatore e l'utente ottiene N× il limite. Per produzione multi-istanza, usare Redis o un equivalente distribuito.

---

### 5. Come scelgo tra Cloudflare Workers e Vercel Edge Functions?

- **Cloudflare Workers:** scegli se serve stato persistente all'edge (Durable Objects, KV), cold start zero, o PoP in 300+ location. Ideale per applicazioni standalone all'edge.
- **Vercel Edge Functions:** scegli se usi già Next.js. Integrazione nativa con il framework. Per rate limiting serve Upstash Redis (esterno).
- **Lambda@Edge:** scegli se usi già CloudFront e hai bisogno di logica su viewer/origin request/response. Cold start significativo.
- **Deno Deploy:** scegli per progetti Deno-native con Deno KV come store integrato.

---

### 6. Come evito di bloccare i crawler legittimi (Googlebot, Bingbot)?

Verificare l'IP del crawler tramite DNS reverse lookup (l'IP deve risolvere a `*.googlebot.com` o `*.search.msn.com`). Non fidarsi solo dello User-Agent (spoofabile). Mantenere una allowlist di IP verificati. Applicare limiti più generosi ai crawler verificati.

---

### 7. Quanto deve essere lungo il `Retry-After`?

Il `Retry-After` deve riflettere il tempo reale prima che la quota si rinnovi. Per fixed window: secondi rimanenti nella finestra. Per token bucket: secondi necessari per accumulare almeno un token. Non usare valori fissi arbitrari — causano retry non necessari o attese troppo lunghe.

---

### 8. È possibile fare rate limiting senza stato (stateless)?

In senso stretto, no: devi contare le richieste e quindi serve stato. Ma puoi approssimare usando token a tempo limitato (signed timestamp nel cookie/header). Il client include il token, il server verifica la firma e il timestamp senza consultare un database. Funziona per scenari semplici ma non per limiti precisi.

---

### 9. Come implemento rate limiting in un'architettura serverless?

Le funzioni serverless non hanno memoria condivisa. Opzioni:
1. **Upstash Redis** — serverless-native, HTTP-based, compatibile con edge
2. **DynamoDB** con `UpdateItem` atomico e TTL
3. **Cloudflare Durable Objects** — stato persistente all'edge
4. **Deno KV** — per Deno Deploy
5. **API Gateway managed** — AWS API Gateway, Cloudflare API Shield

---

### 10. Rate limiting protegge dal DDoS?

Il rate limiting applicativo protegge da DDoS L7 (application layer) ma non da DDoS L3/L4 (volumetrici). Per DDoS volumetrici serve protezione a livello di rete (CDN, scrubbing center, Cloudflare/AWS Shield). Il rate limiting è un layer di difesa, non l'unico.

---

### 11. Come testo il mio rate limiter?

1. **Unit test:** verifica che l'algoritmo blocchi dopo il limite e permetta dopo il reset.
2. **Load test:** usa `k6`, `wrk`, o `autocannon` per generare traffico e verificare i 429.
3. **Chaos test:** simula Redis down e verifica il fallback.
4. **Edge case:** testa boundary burst (fine/inizio finestra), orologi disallineati, chiavi molto lunghe.
5. **Staging first:** attiva in modalità log-only (non blocca, solo registra) per verificare i limiti su traffico reale.

---

### 12. Come gestisco rate limiting per GraphQL?

GraphQL complica il rate limiting perché una singola richiesta HTTP può contenere query di complessità molto diversa. Opzioni:
1. **Complessità della query:** assegnare un costo a ogni campo/resolver e limitare il costo totale per richiesta.
2. **Depth limiting:** rifiutare query con profondità > N.
3. **Batch limiting:** limitare il numero di query in un batch.
4. **Ibrido:** rate limit classico per endpoint + cost-based per complessità.

---

### 13. Cos'è il "jitter" nel backoff e perché è importante?

Il jitter aggiunge casualità al tempo di retry. Senza jitter, se 1000 client ricevono un 429 allo stesso momento, tutti riproveranno allo stesso istante (thundering herd). Con jitter, i retry si distribuiscono nel tempo.

Formula: `retryDelay = baseDelay * 2^attempt + random(0, baseDelay)`

---

### 14. Posso fare rate limiting basato su costo monetario?

Sì, ed è sempre più comune. Ogni endpoint ha un "costo" in crediti. L'utente ha un budget di crediti che si ricarica nel tempo. Endpoint costosi (chiamate LLM, generazione report) consumano più crediti. Questo modello è usato da OpenAI, Anthropic, e molte API AI. Implementare con token bucket dove il "token" rappresenta un credito.

---

### 15. Come funziona il rate limiting con CDN e contenuto cacheato?

Le richieste servite dalla cache CDN (hit) non raggiungono l'origin e non dovrebbero contare nel rate limit dell'applicazione. Solo i cache miss arrivano all'origin. Tuttavia, il CDN stesso può avere rate limiting (WAF rate-based rules) che conta anche gli hit. Distinguere: rate limit CDN (protezione infrastruttura) vs rate limit applicativo (protezione business logic).

---

### 16. Devo loggare le richieste bloccate dal rate limit?

Sì, ma con attenzione al volume. Sotto un DDoS, le richieste bloccate possono essere milioni al minuto. Strategie:
- Loggare un campione (es. 1 su 100 richieste bloccate)
- Aggregare per IP/endpoint e loggare i totali ogni minuto
- Loggare sempre i blocchi per utente autenticato (volume inferiore, più rilevante)
- Non loggare body delle richieste bloccate (spreco di storage)

---

## Strategie di testing per rate limiting

Il testing del rate limiting richiede approcci specifici perché i test sono intrinsecamente sensibili al timing: una variazione di millisecondi può trasformare un test deterministico in un test flaky. Un rate limiter non testato è un rate limiter che non funziona — o che blocca utenti legittimi in produzione.

### Categorie di test

| Categoria | Obiettivo | Strumento consigliato |
|---|---|---|
| **Unit test** | Verifica logica algoritmica | Jest, Vitest, framework del linguaggio |
| **Integration test** | Verifica interazione con Redis/KV | Testcontainers, Redis in-memory |
| **Load test** | Verifica enforcement sotto carico reale | k6, wrk, autocannon |
| **Boundary test** | Verifica edge case temporali | Clock mocking, faketime |
| **Chaos test** | Verifica fallback e resilienza | Redis shutdown, network partition |
| **Contract test** | Verifica header e formato risposta 429 | Supertest, Playwright API |
| **Regression test** | Verifica che i limiti non cambino involontariamente | CI/CD pipeline con k6 |

### Unit testing con clock mocking

Il segreto per test affidabili di rate limiting è il controllo totale del tempo. Iniettare una funzione `now()` consente di simulare il passare del tempo senza `setTimeout` reali.

```typescript
// rate-limiter-testable.ts
class TestableTokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private readonly capacity: number,
    private readonly refillRate: number,
    private readonly clock: () => number = Date.now, // iniettabile
  ) {
    this.tokens = capacity;
    this.lastRefill = clock();
  }

  check(cost: number = 1): { allowed: boolean; remaining: number } {
    const now = this.clock();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.capacity, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;

    if (this.tokens < cost) {
      return { allowed: false, remaining: Math.floor(this.tokens) };
    }
    this.tokens -= cost;
    return { allowed: true, remaining: Math.floor(this.tokens) };
  }
}

// Test
import { describe, it, expect } from 'vitest';

describe('TestableTokenBucket', () => {
  it('blocca dopo esaurimento token', () => {
    let fakeTime = 1000000;
    const clock = () => fakeTime;
    const bucket = new TestableTokenBucket(5, 1, clock);

    // Consuma tutti i token
    for (let i = 0; i < 5; i++) {
      expect(bucket.check().allowed).toBe(true);
    }
    expect(bucket.check().allowed).toBe(false);
  });

  it('rigenera token nel tempo', () => {
    let fakeTime = 1000000;
    const clock = () => fakeTime;
    const bucket = new TestableTokenBucket(5, 2, clock); // 2 token/sec

    // Consuma tutto
    for (let i = 0; i < 5; i++) bucket.check();
    expect(bucket.check().allowed).toBe(false);

    // Avanza di 3 secondi → 6 token rigenerati, cap a 5
    fakeTime += 3000;
    expect(bucket.check().allowed).toBe(true);
    expect(bucket.check().remaining).toBe(3); // 5 - 1 (primo check) - 1 (secondo)
  });

  it('gestisce boundary burst nel fixed window', () => {
    let fakeTime = 0;
    const clock = () => fakeTime;
    // ... test specifico per boundary burst
  });
});
```

### Load testing con k6

k6 è lo strumento più adatto per testare rate limiting in ambiente realistico. Consente di controllare precisamente il tasso di richieste e di verificare che le risposte 429 arrivino al momento corretto.

```javascript
// k6-rate-limit-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';

const rateLimitHits = new Counter('rate_limit_429');
const rateLimitRate = new Rate('rate_limit_rate');

export const options = {
  scenarios: {
    burst_test: {
      executor: 'constant-arrival-rate',
      rate: 120,               // 120 req/sec (sopra il limite di 100/min)
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 50,
      maxVUs: 100,
    },
  },
  thresholds: {
    // Almeno il 15% delle richieste deve essere 429
    'rate_limit_rate': ['rate>0.15'],
    // Le prime richieste devono passare
    'http_req_duration{status:200}': ['p(95)<500'],
  },
};

export default function () {
  const res = http.get('https://api.example.com/endpoint', {
    headers: { 'Authorization': `Bearer ${__ENV.API_KEY}` },
  });

  const is429 = res.status === 429;
  rateLimitHits.add(is429 ? 1 : 0);
  rateLimitRate.add(is429);

  if (is429) {
    check(res, {
      'ha header Retry-After': (r) => r.headers['Retry-After'] !== undefined,
      'ha header X-RateLimit-Remaining 0': (r) =>
        r.headers['X-RateLimit-Remaining'] === '0',
      'body contiene retryAfter': (r) => {
        const body = JSON.parse(r.body);
        return body.retryAfter !== undefined;
      },
    });
  } else {
    check(res, {
      'status 200': (r) => r.status === 200,
      'ha header X-RateLimit-Remaining': (r) =>
        r.headers['X-RateLimit-Remaining'] !== undefined,
    });
  }
}
```

**Esecuzione e analisi:**

```bash
# Test base
k6 run --env API_KEY=sk-test-xxx k6-rate-limit-test.js

# Con output Prometheus per dashboard
k6 run --out experimental-prometheus-rw k6-rate-limit-test.js

# Test per tier specifico
k6 run --env API_KEY=sk-free-xxx --env EXPECTED_LIMIT=60 k6-rate-limit-test.js
```

### Test dei boundary burst

Il boundary burst è il caso limite più critico per Fixed Window. Il test deve verificare che il sistema si comporti correttamente quando le richieste si concentrano a cavallo di due finestre.

```typescript
describe('Boundary burst detection', () => {
  it('fixed window è vulnerabile a boundary burst', () => {
    let fakeTime = 59_500; // 500ms prima della fine della finestra (60s)
    const clock = () => fakeTime;
    const limiter = new FixedWindowRateLimiter(100, 60_000);

    // Invia 80 richieste negli ultimi 500ms della finestra 0
    for (let i = 0; i < 80; i++) {
      expect(limiter.check('test').allowed).toBe(true);
    }

    // Avanza alla finestra 1 (appena 500ms dopo)
    fakeTime = 60_000;

    // Invia altre 100 richieste nei primi 500ms della finestra 1
    for (let i = 0; i < 100; i++) {
      expect(limiter.check('test').allowed).toBe(true);
    }

    // RISULTATO: 180 richieste in 1 secondo effettivo — il doppio del limite!
  });

  it('sliding window counter mitiga il boundary burst', () => {
    let fakeTime = 59_500;
    const clock = () => fakeTime;
    const limiter = new SlidingWindowCounterLimiter(100, 60_000);

    for (let i = 0; i < 80; i++) limiter.check('test');

    fakeTime = 60_000;

    // Il contatore sliding interpola: le 80 della finestra precedente pesano
    // 59500/60000 ≈ 0.99 → ~79 conteggio stimato + nuove richieste
    let accepted = 0;
    for (let i = 0; i < 100; i++) {
      if (limiter.check('test').allowed) accepted++;
    }

    // Significativamente meno di 100 vengono accettate
    expect(accepted).toBeLessThan(30);
  });
});
```

### Chaos testing: Redis failure

Verificare che il rate limiter gestisca correttamente la perdita di Redis è critico. Usare Testcontainers per simulare crash e network partition.

```typescript
import { GenericContainer, StartedTestContainer } from 'testcontainers';
import Redis from 'ioredis';

describe('Rate limiter resilienza Redis', () => {
  let container: StartedTestContainer;
  let redis: Redis;

  beforeAll(async () => {
    container = await new GenericContainer('redis:7-alpine')
      .withExposedPorts(6379)
      .start();
    redis = new Redis({
      host: container.getHost(),
      port: container.getMappedPort(6379),
    });
  });

  it('fallback a in-memory quando Redis è down', async () => {
    const limiter = new ResilientRateLimiter(redis, 100, 60);

    // Verifica funzionamento normale
    const r1 = await limiter.check('test');
    expect(r1.allowed).toBe(true);
    expect(r1.source).toBe('redis');

    // Ferma Redis
    await container.stop();

    // Il limiter deve fare fallback
    const r2 = await limiter.check('test');
    expect(r2.allowed).toBe(true);
    expect(r2.source).toBe('memory'); // o 'failopen'
  });

  afterAll(async () => {
    await redis?.quit();
  });
});
```

### Test in CI/CD pipeline

Integrare il testing del rate limiting nella pipeline CI/CD richiede accortezze specifiche:

1. **Isolamento:** usare API key di test con limiti noti e dedicati
2. **Non parallelizzare:** i test di rate limiting non devono girare in parallelo con altri test che colpiscono lo stesso endpoint
3. **Tolleranza temporale:** aggiungere un margine del 10-20% sui limiti attesi per compensare latenza di rete e scheduling del CI runner
4. **Ambiente dedicato:** usare un Redis di test separato, non condiviso con altri job
5. **Cleanup:** resettare i contatori tra una suite e l'altra con `FLUSHDB` (solo in ambiente di test)

```yaml
# .github/workflows/rate-limit-test.yml (pseudo-config)
rate-limit-tests:
  runs-on: ubuntu-latest
  services:
    redis:
      image: redis:7-alpine
      ports: ["6379:6379"]
  steps:
    - uses: actions/checkout@v4
    - run: npm ci
    - run: npm run test:rate-limit -- --no-parallel
      env:
        REDIS_URL: redis://localhost:6379
        RATE_LIMIT_TEST: true
```

---

## Esercizi

### Lab 1 — Implementa un rate limiter multi-algoritmo

Crea un modulo TypeScript che espone un'interfaccia unificata `RateLimiter` con implementazioni per tutti e cinque gli algoritmi (Fixed Window, Sliding Window Log, Sliding Window Counter, Token Bucket, Leaky Bucket). Scrivi test che verificano:
- Il blocco dopo il superamento del limite
- Il reset corretto dopo la scadenza della finestra
- Il boundary burst per Fixed Window vs l'assenza in Sliding Window
- La tolleranza burst per Token Bucket

---

### Lab 2 — Rate limiting Redis con Lua script

Implementa un rate limiter sliding window counter in Redis usando uno script Lua atomico. Verifica che non ci siano race condition avviando 100 richieste concorrenti con lo stesso key. Confronta il comportamento con l'implementazione INCR + EXPIRE non atomica.

---

### Lab 3 — Cloudflare Worker rate limit con Durable Objects

Crea un Cloudflare Worker che limita le richieste a 100/minuto per IP usando Durable Objects come store. Implementa gli header `X-RateLimit-*`. Testa con `wrk` o `k6` da più location.

---

### Lab 4 — Next.js Edge Middleware con Upstash

Configura un progetto Next.js con Edge Middleware che applica rate limiting usando `@upstash/ratelimit`. Implementa limiti differenziati: 5 req/5min su `/api/auth/*`, 100 req/min su `/api/*`, nessun limite su pagine statiche.

---

### Lab 5 — Bot detection score

Crea un servizio che calcola un bot score basato su User-Agent, timing tra richieste, presenza di JavaScript, e header pattern. Testa con `curl`, un browser reale, e Playwright per verificare che il punteggio sia coerente.

---

### Lab 6 — Dashboard di monitoraggio

Implementa un endpoint `/admin/rate-limit-stats` che espone metriche aggregate: richieste totali, bloccate, top 10 IP limitati, distribuzione per endpoint. Visualizza con un semplice frontend o esporta metriche in formato Prometheus.

---

### Lab 7 — Resilienza e fallback

Simula un'interruzione Redis (chiudi il container). Verifica che il rate limiter fallback a in-memory funzioni. Misura la differenza di precisione tra i due. Implementa alerting quando il fallback è attivo.

---

### Stretch — Rate limiting cross-region

Configura Upstash Redis Global (o simile) con repliche in 2+ regioni. Implementa rate limiting e verifica il comportamento: quanto tempo ci vuole perché un blocco in una regione sia visibile nell'altra? Misura l'imprecisione.

---

## Letture e risorse

- **Cloudflare Rate Limiting Rules** — https://developers.cloudflare.com/waf/rate-limiting-rules/
- **Upstash Ratelimit** — https://github.com/upstash/ratelimit
- **Cloudflare Workers Docs** — https://developers.cloudflare.com/workers/
- **Vercel Edge Functions** — https://vercel.com/docs/functions/edge-functions
- **Deno Deploy** — https://docs.deno.com/deploy/manual
- **AWS Lambda@Edge** — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-at-the-edge.html
- **IETF draft-ietf-httpapi-ratelimit-headers** — https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
- **RFC 9110 §15.5.29 (429 Too Many Requests)** — https://httpwg.org/specs/rfc9110.html
- **Google Cloud — Rate limiting strategies** — https://cloud.google.com/architecture/rate-limiting-strategies-techniques
- **Stripe API Rate Limiting** — https://stripe.com/docs/rate-limits
- **Figma — How we rate limit** — https://www.figma.com/blog/an-alternative-approach-to-rate-limiting/
- **Kong Rate Limiting Plugin** — https://docs.konghq.com/hub/kong-inc/rate-limiting/
- **OWASP — Denial of Service** — https://owasp.org/www-community/attacks/Denial_of_Service

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [14 — Sicurezza Web](14-sicurezza-web.md) | OWASP Top 10, CSP e header di sicurezza complementari al rate limiting |
| [10 — Node.js](10-nodejs.md) | Runtime server e middleware Express/Fastify per rate limiting applicativo |
| [11 — API Design](11-api-design.md) | Design di API RESTful con policy di throttling e header standard |
| [16 — Build Tools e Deploy](16-build-tools-e-deploy.md) | Deploy su Vercel/Cloudflare e configurazione edge functions |
| [17 — Performance Web](17-performance-web.md) | CDN caching, Core Web Vitals e ottimizzazione latenza |
| [12 — Database Web](12-database-web.md) | Redis come store distribuito per contatori rate limiting |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Edge runtime** | Ambiente di esecuzione distribuito nei PoP del CDN, vicino all'utente finale. Non è Node.js: è un runtime V8 con API Web Standard. |
| **Token bucket** | Algoritmo di rate limiting che tollera burst. I token vengono consumati per richiesta e rigenerati a un tasso fisso. |
| **Leaky bucket** | Algoritmo che processa le richieste a un tasso costante, scartando quelle in eccesso quando la coda è piena. |
| **Fixed window** | Rate limiting che divide il tempo in finestre fisse e conta le richieste per finestra. Semplice ma soggetto a boundary burst. |
| **Sliding window** | Rate limiting che usa una finestra temporale mobile, eliminando il problema del boundary burst. |
| **Sliding window counter** | Variante che interpola tra finestra corrente e precedente. Compromesso tra precisione e memoria. |
| **Sliding window log** | Variante che registra ogni timestamp. Perfettamente preciso ma costoso in memoria. |
| **Burst** | Picco temporaneo di traffico che supera il tasso medio sostenuto. |
| **Sustained rate** | Tasso medio di richieste su un periodo lungo. |
| **`Retry-After`** | Header HTTP (RFC 9110) che indica al client quanti secondi attendere prima di riprovare. |
| **HTTP 429** | Codice di stato "Too Many Requests". Il client ha superato il rate limit. |
| **`X-RateLimit-Limit`** | Header (non standard) che indica il limite massimo di richieste nella finestra. |
| **`X-RateLimit-Remaining`** | Header (non standard) che indica le richieste rimanenti nella finestra corrente. |
| **`X-RateLimit-Reset`** | Header (non standard) con il timestamp Unix di reset della finestra. |
| **Durable Objects** | Primitiva Cloudflare per stato persistente e consistente all'edge, con singolo punto di coordinamento. |
| **V8 Isolates** | Meccanismo di sandboxing usato da Cloudflare Workers. Ogni Worker esegue in un isolate V8, senza overhead di container/VM. |
| **CGNAT** | Carrier-Grade NAT: tecnologia dove migliaia di utenti condividono lo stesso IP pubblico. |
| **JA3/JA4** | Fingerprint del client TLS basato sui parametri di handshake. Utile per identificare bot. |
| **WAF** | Web Application Firewall: filtra e monitora il traffico HTTP tra client e applicazione web. |
| **CDN** | Content Delivery Network: rete di server distribuiti che servono contenuto dalla location più vicina all'utente. |
| **PoP** | Point of Presence: location fisica dove un CDN ha server. |
| **ESI** | Edge-Side Includes: standard per assemblare pagine da frammenti all'edge, ognuno con proprio TTL. |
| **Surrogate Key** | Tag associato a una risposta cache che permette invalidazione granulare per gruppo. |
| **Stale-While-Revalidate** | Direttiva `Cache-Control` che permette di servire contenuto scaduto mentre si richiede un aggiornamento in background. |
| **Bot score** | Punteggio numerico (0-100) che indica la probabilità che una richiesta provenga da un bot. |
| **Fail open** | Politica di fallback che accetta tutte le richieste quando il sistema di rate limiting non è disponibile. |
| **Fail closed** | Politica di fallback che rifiuta tutte le richieste quando il sistema di rate limiting non è disponibile. |
| **Thundering herd** | Problema in cui molti client riprovano simultaneamente dopo un'interruzione, causando un nuovo sovraccarico. |
| **Backoff esponenziale** | Strategia di retry dove il tempo di attesa raddoppia ad ogni tentativo fallito. |
| **Cost-based rate limiting** | Rate limiting dove richieste diverse consumano quantità diverse di quota in base alla loro complessità/costo. |
| **Proof of Work** | Challenge che richiede al client di eseguire un calcolo computazionalmente costoso prima di ottenere accesso. |
| **GCRA** | Generic Cell Rate Algorithm: variante del leaky bucket che traccia solo un timestamp (TAT) per client, dimezzando il consumo di memoria rispetto al leaky bucket classico. |
| **TAT** | Theoretical Arrival Time: timestamp teorico di arrivo della prossima richiesta conforme, usato dal GCRA per decidere se ammettere o rifiutare. |
| **Emission Interval** | Intervallo temporale tra due richieste conformi nel GCRA. Derivato dal tasso di riempimento: `T = window / limit`. |
| **Redis Cluster** | Architettura distribuita di Redis in cui i dati sono partizionati in 16384 hash slot distribuiti su più nodi. |
| **Hash Tag** | Pattern `{tag}` nelle chiavi Redis Cluster che forza il routing allo stesso hash slot. Necessario per Lua script multi-chiave. |
| **VCL** | Varnish Configuration Language: linguaggio di configurazione usato da Fastly per definire logica edge, incluso il rate limiting. |
| **Ratecounter** | Primitiva Fastly che conta le richieste per client in una finestra temporale configurabile (1s, 10s, 60s). |
| **Penalty Box** | Meccanismo Fastly che blocca un client per un periodo configurabile dopo il superamento del rate limit. |
| **Quota** | Budget di richieste assegnato a un client su un periodo lungo (giornaliero, mensile), distinto dal rate limit che opera su intervalli brevi. |
| **Circuit Breaker** | Pattern di resilienza che interrompe temporaneamente tutte le richieste verso un servizio degradato, evitando di peggiorare la situazione con retry inutili. |
| **Rate limiting adattivo** | Sistema che modifica dinamicamente i limiti in base a metriche di carico, latenza o anomalie di traffico, anziché usare soglie statiche. |
| **Backpressure** | Meccanismo per cui un sistema sovraccarico segnala ai produttori di rallentare, propagando la pressione verso l'origine del traffico. |
| **Frame-level throttling** | Rate limiting applicato ai singoli frame WebSocket anziché alle connessioni HTTP, necessario per protocolli persistenti. |
| **Grace period** | Periodo di tolleranza dopo il superamento di una quota, durante il quale le richieste sono ancora ammesse (eventualmente con warning) prima del blocco effettivo. |
