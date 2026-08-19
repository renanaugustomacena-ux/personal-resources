# Tutorial 22 — Rate Limiting e Edge Computing: Dal Principiante all'Esperto

> **Companion a:** `22-rate-limiting-edge.md`
> **Scope:** algoritmi di rate limiting · rate limiting distribuito con Redis · header e risposta 429 · scelta della chiave · limiti a costo e a livelli · backoff e retry lato client · edge runtime e i suoi vincoli · caching e invalidazione all'edge · WAF e bot management · monitoraggio e test
> **Prerequisiti:** `tutorial_10_nodejs.md`, `tutorial_11_api_design.md`, `tutorial_14_sicurezza_web.md` — sai scrivere un middleware, progettare un'API e riconoscere le minacce comuni del web
> **Durata stimata:** 5-7 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** RFC 9110 · RFC 9457 · draft-ietf-httpapi-ratelimit-headers · Redis 7 · Cloudflare Workers · Vercel Edge Runtime · Next.js 15

---

## Indice Generale

- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Perché un limite esiste](#a1-perché-un-limite-esiste)
  - [A2. I cinque algoritmi, e quale scegliere](#a2-i-cinque-algoritmi-e-quale-scegliere)
  - [A3. Il primo rate limiter, e perché non basta](#a3-il-primo-rate-limiter-e-perché-non-basta)
  - [A4. Gli header: il contratto con il client](#a4-gli-header-il-contratto-con-il-client)
  - [A5. La chiave non è mai solo l'IP](#a5-la-chiave-non-è-mai-solo-lip)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Distribuito: perché INCR + EXPIRE si rompe](#b1-distribuito-perché-incr--expire-si-rompe)
  - [B2. Sliding window in Redis, e quanto costa](#b2-sliding-window-in-redis-e-quanto-costa)
  - [B3. Quando il rate limiter è il guasto](#b3-quando-il-rate-limiter-è-il-guasto)
  - [B4. Non tutte le richieste costano uguale](#b4-non-tutte-le-richieste-costano-uguale)
  - [B5. Il lato client: backoff, jitter, retry storm](#b5-il-lato-client-backoff-jitter-retry-storm)
  - [B6. L'edge, e perché il 429 dovrebbe nascere lì](#b6-ledge-e-perché-il-429-dovrebbe-nascere-lì)
  - [B7. Cosa NON c'è in un edge runtime](#b7-cosa-non-cè-in-un-edge-runtime)
  - [B8. La cache all'edge e la sua invalidazione](#b8-la-cache-alledge-e-la-sua-invalidazione)
  - [B9. WAF, bot management e rate limiting](#b9-waf-bot-management-e-rate-limiting)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: il limitatore dell'API ordini](#c2-mini-progetto-il-limitatore-dellapi-ordini)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Testare un rate limiter](#d1-testare-un-rate-limiter)
  - [D2. Limiti adattivi e load shedding](#d2-limiti-adattivi-e-load-shedding)
  - [D3. Osservare prima di bloccare](#d3-osservare-prima-di-bloccare)
  - [D4. Multi-region: lo stato che non si sincronizza](#d4-multi-region-lo-stato-che-non-si-sincronizza)
  - [D5. Quando NON serve un rate limiter](#d5-quando-non-serve-un-rate-limiter)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
                       RICHIESTA
                          │
   ┌──────────────────────▼──────────────────────┐
   │  EDGE (300+ PoP)                            │
   │   WAF → bot score → rate limit → cache      │
   │   il 429 nasce qui: non attraversa la rete  │
   └──────────────────────┬──────────────────────┘
                          │ ciò che passa
   ┌──────────────────────▼──────────────────────┐
   │  ORIGIN                                     │
   │   rate limit per utente e per costo         │
   │   quota giornaliera · autorizzazione        │
   └──────────────────────┬──────────────────────┘
                          │
                    STATO CONDIVISO
                     Redis · Durable Object

   ALGORITMO ──── fixed · sliding · token bucket · leaky · GCRA
   CHIAVE ─────── IP · utente · API key · endpoint · combinazioni
   CONTRATTO ──── X-RateLimit-* · Retry-After · 429 + RFC 9457
   CLIENT ─────── backoff esponenziale + jitter · circuit breaker
```

---

# Parte A — Basi Assolute

---

## A1. Perché un limite esiste

> **Analogia:** i tornelli della metropolitana. Non servono a impedirti di entrare: servono a impedire che duemila persone entrino nello stesso secondo e schiaccino chi sta scendendo le scale. Il tornello lascia passare tutti, uno alla volta, a un ritmo che la banchina regge.

Un'API senza limiti non ha un problema di sicurezza. Ha un problema di aritmetica.

```
COSA SUCCEDE SENZA UN LIMITE

  · uno sviluppatore sbaglia un ciclo e chiama l'endpoint 40.000
    volte al minuto — non è malizia, è un `while` senza `break`
  · un client mobile va in retry senza attesa: quando il server
    rallenta, ogni utente diventa dieci utenti
  · uno scraper legge l'intero catalogo ogni notte, e qualcuno
    prova 500.000 password sul login
  · un endpoint che chiama un modello linguistico costa quattro
    centesimi a richiesta, e la fattura non ha un tetto

⚠ I PRIMI DUE CASI SONO I PIÙ FREQUENTI, e nessuno dei due è un
  attacco. Il rate limiting è prima di tutto una misura di
  stabilità: la sicurezza viene dopo.
```

Il codice di stato è `429 Too Many Requests` (RFC 9110 §15.5.30). È una risposta di errore del client — significa "hai chiesto troppo", non "sono rotto", che sarebbe `503`. La differenza conta: un client scritto bene tratta il `429` come un invito ad attendere, e il `503` come un guasto da segnalare.

```
LE TRE DOMANDE, IN QUEST'ORDINE
  1. QUANTO? il limite: 100 richieste al minuto
  2. A CHI?  la chiave: IP, utente, API key, endpoint, o una loro
     combinazione (§A5)
  3. COME?   l'algoritmo, cioè come si conta il tempo (§A2)

La terza è quella su cui si discute di più, ed è quella che conta di
meno: un fixed window con la chiave giusta protegge meglio di un
GCRA impeccabile applicato al solo indirizzo IP.
```

---

## A2. I cinque algoritmi, e quale scegliere

Tutti rispondono alla stessa domanda — "questa richiesta passa?" — contando il tempo in modi diversi.

```
1. FIXED WINDOW  ·  un contatore per finestra, azzerato alla fine

   00:00────────────00:59 │ 01:00────────────01:59
   [ 8 richieste       ]  │ [ 10 richieste      ]
                       ↑  ↑
                       └──┴─ 18 RICHIESTE IN DUE SECONDI, con un
                             limite di 10/minuto. È il boundary
                             burst, ed è il difetto dell'algoritmo.

2. SLIDING WINDOW LOG  ·  la lista dei timestamp, esatta

   ora ─ 60s ◄════════ finestra che scorre ════════► ora
   Nessun boundary burst, e memoria proporzionale alle richieste.

3. SLIDING WINDOW COUNTER  ·  il compromesso: il contatore della
   finestra precedente pesato sulla porzione ancora dentro —
   (60-20)/60 × 8 + 3 = 8,3. Errore sotto l'1%, memoria costante.

4. TOKEN BUCKET  ·  un secchio che si riempie a un ritmo fisso

   capacità 10, ricarica 2 token/secondo
   t=0  [■■■■■■■■■■] → 10 richieste → [__________]
   t=1  [■■________] rifiuta finché non torna un token
   ➜ chi è stato fermo accumula credito: tollera i burst

5. LEAKY BUCKET  ·  una coda svuotata a ritmo costante

   ➜ uscita perfettamente regolare, burst legittimi penalizzati
```

```
LA REGOLA DI SCELTA

  API pubblica generica ────────► TOKEN BUCKET
    quello di Stripe, GitHub e AWS. Due parametri spiegabili a un
    cliente: burst e ritmo sostenuto.
  login ed endpoint sensibili ──► SLIDING WINDOW
    il boundary burst regala il doppio dei tentativi a chi li
    concentra sul confine
  coda verso un sistema fragile ─► LEAKY BUCKET
    quando a valle c'è qualcosa che non tollera i picchi
  conteggio grezzo, molte chiavi ► FIXED WINDOW
    una sola INCR, memoria minima, dove il burst non fa danno

⚠ GCRA (RFC 2212, dal mondo ATM) merita una menzione: tiene UN solo
  timestamp per client invece di timestamp più contatore, e dà la
  precisione dello sliding window con la memoria di un fixed window.
  Vale quando le chiavi sono milioni.
```

```typescript
// Token bucket in memoria: il ricalcolo avviene alla lettura, non
// con un timer. Un timer per chiave, con un milione di chiavi,
// sarebbe un milione di timer.
export interface EsitoLimite {
  consentito: boolean
  rimanenti: number
  riprovaTraMs: number
}

export class LimitatoreTokenBucket {
  private secchi = new Map<string, { token: number; ultimaRicarica: number }>()

  constructor(
    private readonly capacita: number,
    private readonly ricaricaAlSecondo: number,
  ) {}

  verifica(chiave: string, costo = 1): EsitoLimite {
    const adesso = Date.now()
    let stato = this.secchi.get(chiave)
    if (!stato) {
      stato = { token: this.capacita, ultimaRicarica: adesso }
      this.secchi.set(chiave, stato)
    }

    const trascorsiMs = adesso - stato.ultimaRicarica
    stato.token = Math.min(
      this.capacita,
      stato.token + (trascorsiMs / 1000) * this.ricaricaAlSecondo,
    )
    stato.ultimaRicarica = adesso

    if (stato.token < costo) {
      const mancanti = costo - stato.token
      return {
        consentito: false,
        rimanenti: 0,
        riprovaTraMs: Math.ceil((mancanti / this.ricaricaAlSecondo) * 1000),
      }
    }

    stato.token -= costo
    return { consentito: true, rimanenti: Math.floor(stato.token), riprovaTraMs: 0 }
  }
}
```

---

## A3. Il primo rate limiter, e perché non basta

La versione in memoria del paragrafo precedente funziona, e ha tre difetti che si scoprono tutti in produzione.

```
❌ NON SOPRAVVIVE A PIÙ ISTANZE — con quattro processi dietro un
   load balancer il limite effettivo è quattro volte quello scritto,
   e in autoscaling non è nemmeno prevedibile
❌ NON SOPRAVVIVE A UN RIAVVIO — ogni rilascio azzera i contatori
❌ LA MAPPA CRESCE PER SEMPRE — una voce per ogni IP mai visto. Il
   processo muore per esaurimento di memoria, e non subito: il che
   è peggio, perché succede la notte del terzo giorno.
```

```typescript
// La pulizia periodica è obbligatoria in ogni limitatore in memoria.
// `unref()` impedisce al timer di tenere vivo il processo quando
// tutto il resto ha finito.
export class SecchioConPulizia extends LimitatoreTokenBucket {
  private readonly timer: NodeJS.Timeout

  constructor(capacita: number, ricaricaAlSecondo: number, intervalloMs = 60_000) {
    super(capacita, ricaricaAlSecondo)
    this.timer = setInterval(() => this.pulisci(), intervalloMs)
    this.timer.unref()
  }

  /** Elimina i secchi tornati pieni: sono clienti inattivi. */
  private pulisci(): void {
    const soglia = Date.now() - 10 * 60_000
    for (const [chiave, stato] of this['secchi']) {
      if (stato.ultimaRicarica < soglia) this['secchi'].delete(chiave)
    }
  }

  ferma(): void {
    clearInterval(this.timer)
  }
}
```

In memoria va benissimo su un servizio a istanza singola, come limite di secondo livello dietro quello vero all'edge (§B6), e come ripiego quando Redis non risponde (§B3). Non va come *unico* limite di un'API pubblica in autoscaling: il numero scritto nella documentazione non è quello che si applica.

---

## A4. Gli header: il contratto con il client

> **Analogia:** il display alla fermata dell'autobus. Senza, la gente si affaccia in strada ogni venti secondi. Con "prossimo autobus: 6 minuti", si siede e aspetta.

Un `429` senza header dice al client "no" e nient'altro. Il client ragionevole riprova subito. E siccome tutti i client bloccati riprovano subito, il carico dopo il blocco è più alto di quello prima: è la **retry storm** (§B5), e la si previene qui, non lato client.

| Header | Cosa dice | Stato |
|---|---|---|
| `Retry-After` | secondi, o una data HTTP, prima di riprovare | Standard, RFC 9110 §10.2.3 |
| `X-RateLimit-Limit` | il tetto della finestra | Convenzione de facto |
| `X-RateLimit-Remaining` | quante ne restano | Convenzione de facto |
| `X-RateLimit-Reset` | quando riparte la finestra | Convenzione de facto |
| `RateLimit` | i tre valori in un header solo | draft IETF httpapi |

```
⚠ DUE REGOLE CHE VENGONO SBAGLIATE QUASI SEMPRE

  1. GLI HEADER VANNO SU OGNI RISPOSTA, non solo sul 429. Un client
     che vede `Remaining: 3` rallenta da solo; uno che scopre il
     limite sbattendoci contro non può fare altro che sbattere.
  2. `X-RateLimit-Reset` NON HA UN'UNITÀ CONCORDATA: GitHub manda un
     timestamp Unix, altri i secondi mancanti. Va documentato quale
     dei due, o si usa `Retry-After`, che è inequivocabile.
```

```typescript
// Il middleware Express: gli header prima del verdetto, sempre.
import type { Request, Response, NextFunction } from 'express'

export function limitatore(
  secchio: LimitatoreTokenBucket,
  estraiChiave: (req: Request) => string,
  tetto: number,
) {
  return (req: Request, res: Response, avanti: NextFunction): void => {
    const esito = secchio.verifica(estraiChiave(req))

    res.setHeader('X-RateLimit-Limit', tetto)
    res.setHeader('X-RateLimit-Remaining', esito.rimanenti)

    if (esito.consentito) return void avanti()

    const attesa = Math.ceil(esito.riprovaTraMs / 1000)
    res.setHeader('Retry-After', attesa)
    // RFC 9457: lo stesso formato d'errore del resto dell'API
    // (tutorial_11 §B4), non un JSON inventato per l'occasione
    res.status(429).type('application/problem+json').json({
      type: 'https://api.esempio.it/problemi/limite-superato',
      title: 'Too Many Requests',
      status: 429,
      detail: `Limite di ${tetto} richieste al minuto superato. Riprova tra ${attesa} secondi.`,
      retryAfter: attesa,
    })
  }
}
```

⚠ Nel corpo dell'errore non va mai il dettaglio dell'implementazione — quale algoritmo, quale store, quale soglia interna ha scattato. Dice a chi sta sondando l'API esattamente come aggirarla.

---

## A5. La chiave non è mai solo l'IP

```
IL PROBLEMA CON L'IP, IN TRE FATTI
  · un'azienda di quattrocento dipendenti esce da un solo IP, e il
    limite per IP la tratta come una persona sola
  · le reti mobili usano CGNAT: decine di migliaia di abbonati
    dietro lo stesso indirizzo
  · chi ha un pool di IP residenziali ne cambia uno a ogni
    richiesta, e il limite per IP non lo vede mai

➜ L'IP NON IDENTIFICA UNA PERSONA. Serve dove non c'è altro, ma da
  solo sbaglia in entrambe le direzioni: blocca chi non doveva, e
  non blocca chi doveva.
```

```typescript
// La chiave si sceglie in ordine di affidabilità: l'identità
// verificata batte sempre l'indirizzo di rete.
export function chiaveDiLimite(req: Request): string {
  const utente = req.auth?.userId
  if (utente) return `utente:${utente}`

  const apiKey = req.get('x-api-key')
  if (apiKey) return `chiave:${impronta(apiKey)}` // mai la chiave in chiaro

  return `ip:${ipAffidabile(req)}`
}
```

```typescript
// ❌ SBAGLIATO — X-Forwarded-For è scritto dal client: chi vuole
//    aggirare il limite manda un indirizzo nuovo a ogni richiesta
const ip = req.get('x-forwarded-for')?.split(',')[0]

// ✅ CORRETTO — si conta da DESTRA e ci si ferma al primo proxy non
//    nostro. Con `trust proxy` configurato sul numero esatto di
//    proxy davanti all'app, Express lo fa già in `req.ip`.
export function ipAffidabile(req: Request): string {
  const catena = (req.get('x-forwarded-for') ?? '').split(',').map((s) => s.trim())
  const NOSTRI_PROXY = 2 // load balancer + CDN: il numero VERO
  return catena[catena.length - 1 - NOSTRI_PROXY] ?? req.socket.remoteAddress ?? 'ignoto'
}
```

```
⚠ DIETRO UN CDN SI USA IL SUO HEADER FIRMATO: `cf-connecting-ip` su
  Cloudflare, `true-client-ip` su Akamai e Fastly. Lo riscrive il CDN
  e il client non può falsificarlo — a patto che l'origin sia
  raggiungibile SOLO attraverso il CDN, altrimenti si aggira tutto
  chiamandolo direttamente.
```

Le difese vere si sovrappongono: `/auth/login` limitato per IP **e** per email tentata **e** globalmente. Tre limiti che vanno superati tutti, dove ognuno copre il buco dell'altro.

```typescript
export const LIMITI: Record<string, { tetto: number; finestraS: number; per: 'ip' | 'utente' | 'globale' }[]> = {
  'POST /auth/login': [
    { tetto: 5, finestraS: 300, per: 'ip' },
    { tetto: 10, finestraS: 3600, per: 'utente' },   // l'email tentata
    { tetto: 1000, finestraS: 60, per: 'globale' },  // credential stuffing distribuito
  ],
  'POST /api/ordini': [{ tetto: 30, finestraS: 60, per: 'utente' }],
}
```

---

# Parte B — Comprensione Profonda

---

## B1. Distribuito: perché INCR + EXPIRE si rompe

Con più istanze, il contatore deve stare fuori dal processo. Redis è la scelta ovvia, e il primo tentativo contiene un difetto sottile.

```typescript
// ❌ SBAGLIATO — due comandi, non uno. Se il processo muore, la rete
//    cade o Redis fa failover fra l'INCR e l'EXPIRE, la chiave resta
//    SENZA TTL: quel client è bloccato per sempre, e nessun log lo
//    dice. È una race che si manifesta una volta ogni centomila
//    richieste, cioè tutti i giorni su un'API vera.
export async function limitaSbagliato(chiave: string, finestraSecondi: number) {
  await redis.incr(chiave)
  await redis.expire(chiave, finestraSecondi)
}
```

```typescript
// ✅ CORRETTO — uno script Lua: Redis lo esegue atomicamente, e in
//    un round trip solo invece di due.
export const LUA_FINESTRA_FISSA = `
  local corrente = redis.call('INCR', KEYS[1])
  if corrente == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
  end
  local ttl = redis.call('TTL', KEYS[1])
  if corrente > tonumber(ARGV[1]) then
    return {0, 0, ttl}
  end
  return {1, tonumber(ARGV[1]) - corrente, ttl}
`
```

```typescript
import { Redis } from 'ioredis'

export class LimitatoreRedis {
  constructor(
    private readonly redis: Redis,
    private readonly tetto: number,
    private readonly finestraSecondi: number,
  ) {
    this.redis.defineCommand('limita', { numberOfKeys: 1, lua: LUA_FINESTRA_FISSA })
  }

  async verifica(chiave: string): Promise<EsitoLimite> {
    const adesso = Math.floor(Date.now() / 1000)
    const inizio = Math.floor(adesso / this.finestraSecondi) * this.finestraSecondi
    const [ok, rimanenti, ttl] = await (this.redis as never as {
      limita(k: string, tetto: number, finestra: number): Promise<[number, number, number]>
    }).limita(`limite:${chiave}:${inizio}`, this.tetto, this.finestraSecondi)

    return { consentito: ok === 1, rimanenti, riprovaTraMs: ttl * 1000 }
  }
}
```

```
⚠ REDIS CLUSTER: uno script Lua può toccare solo chiavi dello
  stesso hash slot, altrimenti risponde CROSSSLOT. Chiavi che vanno
  usate insieme — il contatore e la finestra precedente — si legano
  con un hash tag: le graffe dicono quale porzione determina lo slot.

    limite:{utente:42}:corrente
    limite:{utente:42}:precedente
             └────────┘ stesso slot garantito

  ➜ Il costo è che tutte le chiavi di un utente molto attivo
    finiscono sullo stesso nodo, ed è accettabile: il traffico di un
    singolo utente è per definizione limitato.
```

---

## B2. Sliding window in Redis, e quanto costa

Il sorted set con il timestamp come punteggio dà la precisione dello sliding window log.

```typescript
export class LimitatoreScorrevole {
  constructor(
    private readonly redis: Redis,
    private readonly tetto: number,
    private readonly finestraMs: number,
  ) {}

  async verifica(chiave: string): Promise<EsitoLimite> {
    const adesso = Date.now()
    const k = `limite:sw:${chiave}`
    const membro = `${adesso}:${crypto.randomUUID()}`

    const risultati = await this.redis
      .pipeline()
      .zremrangebyscore(k, '-inf', adesso - this.finestraMs) // scadute via
      .zadd(k, adesso, membro)
      .zcard(k)
      .pexpire(k, this.finestraMs)
      .exec()

    const conteggio = risultati?.[2]?.[1] as number

    if (conteggio > this.tetto) {
      // La richiesta rifiutata non deve restare nel log, altrimenti
      // un client che insiste allunga la propria punizione
      await this.redis.zrem(k, membro)
      const [, piuVecchio] = await this.redis.zrange(k, 0, 0, 'WITHSCORES')
      return {
        consentito: false,
        rimanenti: 0,
        riprovaTraMs: piuVecchio ? Number(piuVecchio) + this.finestraMs - adesso : this.finestraMs,
      }
    }

    return { consentito: true, rimanenti: this.tetto - conteggio, riprovaTraMs: 0 }
  }
}
```

```
IL COSTO, DETTO CON I NUMERI
  memoria ► una settantina di byte per richiesta nel sorted set: con
      un limite di 1.000/minuto e 50.000 client attivi, il caso
      peggiore è 50 milioni di membri, cioè gigabyte di Redis
  tempo ► O(log N) per ZADD e ZREMRANGEBYSCORE, contro O(1) di INCR

➜ SI USA DOVE LA PRECISIONE VALE IL PREZZO: login, pagamenti,
  endpoint costosi. Per la lettura generica, un fixed window con
  finestre corte costa una frazione e sbaglia poco.
```

⚠ La pipeline **non** è atomica come uno script Lua: i quattro comandi arrivano insieme ma altri client possono interporsi. Con `MULTI`/`EXEC` o Lua diventa atomica; senza, sotto forte concorrenza il conteggio può eccedere di poco il tetto. Per un rate limiter è quasi sempre tollerabile — vale la pena saperlo, non necessariamente correggerlo.

---

## B3. Quando il rate limiter è il guasto

```
IL PROBLEMA: il limitatore sta sul percorso di OGNI richiesta. Se
Redis smette di rispondere ci sono due comportamenti possibili, e
nessuno dei due è gratis:
  FAIL-OPEN   passa tutto  ➜ l'API resta viva ma indifesa
  FAIL-CLOSED blocca tutto ➜ Redis giù significa sito giù

⚠ FAIL-CLOSED SU UN LIMITATORE È IL MODO PIÙ RAPIDO DI TRASFORMARE
  il guasto di una dipendenza secondaria in un'interruzione totale.
  Il limitatore protegge il servizio: non deve poterlo spegnere.
```

```typescript
// La regola: fail-open per il traffico normale, fail-closed solo
// dove il danno di una richiesta in più supera quello del blocco —
// login, pagamenti, invio di codici via SMS.
export class LimitatoreConRipiego {
  private readonly locale = new LimitatoreTokenBucket(20, 0.33)
  private degradato = false

  constructor(
    private readonly remoto: LimitatoreRedis,
    private readonly critico: boolean,
  ) {}

  async verifica(chiave: string): Promise<EsitoLimite> {
    try {
      const esito = await conScadenza(this.remoto.verifica(chiave), 50)
      this.degradato = false
      return esito
    } catch {
      if (!this.degradato) {
        this.degradato = true
        metriche.incrementa('rate_limit.ripiego_attivo')
      }
      // Il ripiego locale è più stretto del limite vero: con N
      // istanze, ognuna ne lascia passare 1/N
      return this.critico
        ? { consentito: false, rimanenti: 0, riprovaTraMs: 5000 }
        : this.locale.verifica(chiave)
    }
  }
}

/** Un limitatore lento è peggio di un limitatore assente. */
export function conScadenza<T>(promessa: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promessa,
    new Promise<T>((_, rifiuta) => setTimeout(() => rifiuta(new Error('scaduto')), ms).unref()),
  ])
}
```

⚠ Il timeout di 50 ms non è decorativo: senza, una latenza di Redis a due secondi diventa due secondi su ogni richiesta dell'API, le connessioni si accumulano e il servizio cade con Redis ancora acceso. La metrica `ripiego_attivo` deve generare un alert — si sta girando senza protezione vera.

---

## B4. Non tutte le richieste costano uguale

Un `GET /prodotti/42` legge una riga per indice. Un `POST /report/genera` avvia un job che occupa un core per venti secondi. Contarle come una richiesta ciascuna è la ragione per cui un limite "generoso" può comunque far cadere il sistema.

```typescript
// Il costo si esprime in token del secchio (§A2): il limitatore
// resta lo stesso, cambia quanto ogni richiesta consuma.
const COSTO: Record<string, number> = {
  'GET /api/prodotti': 1,
  'GET /api/ricerca': 3,
  'POST /api/ordini': 5,
  'POST /api/upload': 10,
  'POST /api/report/genera': 50,
  'POST /api/ai/completamento': 100,
}

export function costoDi(metodo: string, percorso: string): number {
  // I path parametrici vanno normalizzati, altrimenti ogni id è una
  // voce diversa e non corrisponde mai
  const normalizzato = percorso
    .replace(/\/[0-9a-f]{8}-[0-9a-f-]{27}/gi, '/:id')
    .replace(/\/\d+/g, '/:id')
  return COSTO[`${metodo} ${normalizzato}`] ?? 1
}
```

```
IL LIMITE A LIVELLI: lo stesso algoritmo, parametri per piano

  piano        burst   sostenuto     quota giornaliera
  free            5     20/min          500
  pro           200  1.000/min      100.000
  enterprise  2.000 10.000/min   1.000.000

⚠ QUOTA ≠ RATE LIMIT, e vanno applicate entrambe:
   · il RATE LIMIT protegge l'infrastruttura — finestra di secondi
     o minuti, si ricarica da sola, il 429 è temporaneo
   · la QUOTA protegge il modello di business — finestra di un mese,
     si azzera alla fatturazione, e superarla è una conversazione
     commerciale, non un errore tecnico
```

Nel 429 conviene dire anche quanto costava la richiesta: un client che legge "servivano 50 token, ne avevi 12" può aspettare il tempo giusto invece di riprovare a vuoto.

---

## B5. Il lato client: backoff, jitter, retry storm

> **Analogia:** mille persone davanti a un ascensore guasto. Se tutte ripremono il pulsante ogni cinque secondi, l'ascensore riparte e si riempie subito, e resta guasto. Se ognuna aspetta un tempo diverso, entrano in ordine.

```
LA RETRY STORM, PASSO PER PASSO
  1. il servizio rallenta e comincia a restituire 429
  2. mille client lo ricevono nello stesso istante e riprovano
     dopo un secondo esatto, tutti insieme
  3. il servizio rallenta ancora, e si torna al punto 2 con più
     client di prima

➜ SI SPEZZA IN DUE PUNTI, e servono entrambi: `Retry-After` dal
  server (§A4), e il JITTER dal client. Il backoff esponenziale da
  solo non basta — sincronizza i tentativi invece di distribuirli,
  perché tutti raddoppiano l'attesa nello stesso momento.
```

```typescript
// Il "full jitter" di AWS: l'attesa è un valore CASUALE fra zero e
// il tetto esponenziale, non il tetto stesso. È la variante che
// distribuisce meglio i tentativi.
export function attesaMs(tentativo: number, baseMs = 500, tettoMs = 30_000): number {
  const esponenziale = Math.min(tettoMs, baseMs * 2 ** tentativo)
  return Math.random() * esponenziale
}
```

```typescript
export async function chiamaConRitentativi(
  url: string,
  opzioni: RequestInit = {},
  massimoTentativi = 5,
): Promise<Response> {
  for (let tentativo = 0; ; tentativo++) {
    const risposta = await fetch(url, opzioni)

    // 4xx diversi da 429 sono errori del client: ritentare non serve
    if (risposta.status !== 429 && risposta.status < 500) return risposta
    if (tentativo >= massimoTentativi) return risposta

    // Se il server ha detto quanto aspettare, si obbedisce — con un
    // po' di jitter comunque, perché l'ha detto a tutti insieme
    const indicato = risposta.headers.get('retry-after')
    const attesa = indicato
      ? Number(indicato) * 1000 + Math.random() * 1000
      : attesaMs(tentativo)

    await new Promise((r) => setTimeout(r, attesa))
  }
}
```

```
⚠ IL RITENTATIVO VA FATTO SOLO SU OPERAZIONI IDEMPOTENTI. Un POST
  ritentato può creare due ordini. La soluzione è una chiave di
  idempotenza (tutorial_11 §B6): il client la genera una volta e la
  ripete a ogni tentativo, il server riconosce il duplicato.

⚠ E VA MESSO IN UN SOLO PUNTO. Tre livelli che ritentano tre volte
  ciascuno sono ventisette richieste per una: l'amplificazione del
  retry è il modo classico di trasformare un rallentamento in un
  crollo. Un circuit breaker che si apre dopo N fallimenti
  consecutivi taglia il ciclo alla radice.
```

---

## B6. L'edge, e perché il 429 dovrebbe nascere lì

```
DOVE MUORE UNA RICHIESTA RIFIUTATA

  All'ORIGIN  client → CDN → load balancer → app → limitatore
              un processo occupato, e banda pagata due volte
  All'EDGE    client → PoP più vicino → limitatore → 429
              niente attraversa la dorsale

➜ È LA DIFFERENZA fra un buttafuori all'ingresso e uno al bancone:
  nel secondo caso la calca c'è comunque.
```

Un edge runtime non è Node.js: è un V8 isolate, un contesto JavaScript isolato dentro un processo condiviso. Non c'è un container per richiesta — per questo l'avvio è quasi istantaneo, e per questo mancano metà delle API a cui sei abituato (§B7).

```typescript
// Cloudflare Worker: `cf-connecting-ip` lo scrive Cloudflare, e il
// client non può falsificarlo. Il Durable Object dà il conteggio
// coerente che un isolate da solo non può avere.
export interface Ambiente {
  LIMITATORE: DurableObjectNamespace
}

export default {
  async fetch(richiesta: Request, ambiente: Ambiente): Promise<Response> {
    const ip = richiesta.headers.get('cf-connecting-ip') ?? 'ignoto'
    const oggetto = ambiente.LIMITATORE.get(ambiente.LIMITATORE.idFromName(ip))
    const esito = await oggetto
      .fetch('https://interno/verifica')
      .then((r) => r.json<{ consentito: boolean; rimanenti: number }>())

    if (!esito.consentito) {
      return new Response(JSON.stringify({ title: 'Too Many Requests', status: 429 }), {
        status: 429,
        headers: {
          'content-type': 'application/problem+json',
          'retry-after': '60',
          'x-ratelimit-remaining': '0',
        },
      })
    }

    const daOrigin = await fetch(richiesta)
    const risposta = new Response(daOrigin.body, daOrigin)
    risposta.headers.set('x-ratelimit-remaining', String(esito.rimanenti))
    return risposta
  },
}
```

```
⚠ IL DURABLE OBJECT È UNA SINGOLA ISTANZA GLOBALE per chiave, con
  esecuzione serializzata: coerenza forte senza Redis, e due
  conseguenze. Vive in UNA regione, quindi da un altro continente il
  round trip è reale. E un singolo oggetto ha un tetto di
  throughput: per una chiave globale molto calda si partiziona in
  `globale:${hash % 16}`, dividendo il limite per sedici.
```

Molte piattaforme offrono un rate limiting nativo, dichiarativo, senza scrivere codice: le Rate Limiting Rules di Cloudflare, le regole rate-based del WAF di AWS. Coprono il caso "per IP, per percorso, per finestra" con zero manutenzione, e conviene usarle per quello — riservando il codice ai limiti che dipendono dall'identità o dal costo.

---

## B7. Cosa NON c'è in un edge runtime

```
IL PRIMO DEPLOY ALL'EDGE FALLISCE QUASI SEMPRE PER LO STESSO MOTIVO:
una dipendenza transitiva importa un modulo Node.js che non esiste.

  fs · child_process · net · dgram ─► non c'è filesystem né shell
  require()                        ─► solo ESM
  setInterval                      ─► la vita dell'isolate è la
                                      richiesta: niente cicli
  eval() e new Function()          ─► bloccati per sicurezza
  crypto di Node                   ─► c'è `crypto.subtle`
  Buffer                           ─► dipende dalla piattaforma
```

| Al posto di | Si usa | Perché |
|---|---|---|
| `bcrypt` | `@noble/hashes`, o PBKDF2 di Web Crypto | dipendenza nativa |
| `jsonwebtoken` | `jose` | usa il `crypto` di Node |
| `axios` | `fetch` nativo | `fetch` c'è già ovunque |
| `pg`, `mysql2` | driver HTTP (Neon, PlanetScale) | servono socket TCP |

```
E I LIMITI DI ESECUZIONE, che nessuno legge finché non li supera:

  Cloudflare Workers   10 ms di CPU (piano gratuito), 50 ms a pagamento
  Vercel Edge          4 MB di bundle, 30 s di wall time
  Lambda@Edge viewer   1 MB, 5 s
  CloudFront Functions 10 KB, meno di 1 ms

⚠ IL LIMITE È SUL TEMPO DI CPU, NON SULL'ATTESA: si può aspettare
  una fetch molto più a lungo di 50 ms. Quello che non si può fare è
  CALCOLARE per 50 ms — niente hashing di password, niente
  elaborazione di immagini, niente parsing di file grossi.
```

---

## B8. La cache all'edge e la sua invalidazione

Il rate limiting decide chi passa; la cache decide chi non ha bisogno di passare. Sulla stessa infrastruttura, e con lo stesso effetto sul carico all'origin.

```
Cache-Control: public, max-age=0, s-maxage=60, stale-while-revalidate=300

  max-age ► quanto tiene il BROWSER
  s-maxage ► quanto tiene la CDN, e vince su max-age
  stale-while-revalidate ► per quanto la CDN può servire una copia
      scaduta mentre ne chiede una fresca (stale-if-error fa lo
      stesso quando l'origin è giù)
  immutable ► non cambierà mai, per gli URL con hash nel nome
  private ► solo il browser, MAI la CDN
  no-store ► nessuna cache, da nessuna parte
```

| Contenuto | Direttiva |
|---|---|
| asset con hash nel nome | `public, max-age=31536000, immutable` |
| pagina HTML pubblica | `public, max-age=0, s-maxage=60, stale-while-revalidate=300` |
| risposta API pubblica | `public, max-age=0, s-maxage=30, stale-while-revalidate=60` |
| qualunque dato di un utente | `private, no-store` |

```
⚠ `private, no-store` SU TUTTO CIÒ CHE DIPENDE DALLA SESSIONE. Una
  sola risposta personalizzata con `public` finisce nella cache
  condivisa e la CDN la serve al visitatore successivo: è il classico
  "vedo il carrello di un altro". Prima di mettere `public`, la
  domanda è se il corpo cambia in funzione di un cookie o di un
  header `Authorization` — e `Vary: Authorization` non risolve,
  perché frammenta la cache per token e la rende inutile.
```

Lo `stale-while-revalidate` è il compromesso che conta: il primo utente dopo la scadenza riceve la copia vecchia in cinque millisecondi invece di aspettare l'origin, e la copia fresca arriva a quello dopo. Nessuno aspetta, e il contenuto ha al massimo qualche decina di secondi.

```typescript
// I cache tag: invalidare per CATEGORIA invece che per URL. Cambia
// il prezzo del prodotto 42 e cadono tutte le pagine che lo
// mostrano — la scheda, l'elenco, la home — senza doverle elencare.
export function conTag(risposta: Response, tag: string[]): Response {
  const nuova = new Response(risposta.body, risposta)
  nuova.headers.set('Cache-Tag', tag.join(','))       // Cloudflare
  nuova.headers.set('Surrogate-Key', tag.join(' '))   // Fastly, Akamai
  return nuova
}

// La pagina prodotto: Cache-Tag: prodotto-42, categoria-audio, listino
// L'aggiornamento del prezzo purga `prodotto-42`; un cambio di
// listino purga `listino` e basta.
```

---

## B9. WAF, bot management e rate limiting

Sono tre livelli diversi, e vengono confusi perché stanno tutti all'edge.

```
WAF               guarda il CONTENUTO di una richiesta
                  ➜ blocca l'iniezione SQL, l'XSS, il path traversal
                  ➜ una richiesta sola può essere malevola

RATE LIMITING     guarda la FREQUENZA
                  ➜ blocca l'abuso di un endpoint legittimo
                  ➜ ogni singola richiesta è innocua

BOT MANAGEMENT    guarda il COMPORTAMENTO nel tempo
                  ➜ distingue una persona da uno script
                  ➜ le richieste sono innocue E a bassa frequenza

⚠ NESSUNO DEI TRE SOSTITUISCE GLI ALTRI. Uno scraper che legge una
  pagina ogni tre secondi da mille IP passa il rate limit e il WAF,
  e lo ferma solo il terzo.
```

```typescript
// Un punteggio, non un verdetto: i segnali sono deboli presi uno per
// uno, e nessuno di loro merita da solo un blocco.
export function punteggioBot(richiesta: Request, storico: Storico): number {
  let punti = 0
  const ua = richiesta.headers.get('user-agent') ?? ''

  if (!ua) punti += 30
  if (/curl|python-requests|scrapy|headless/i.test(ua)) punti += 40

  // La regolarità è il segnale più forte: una persona non clicca
  // ogni 1000 ms esatti. La deviazione standard degli intervalli su
  // dieci richieste separa gli script dagli umani meglio di
  // qualunque analisi dello User-Agent.
  if (storico.intervalli.length >= 10 && deviazione(storico.intervalli) < 50) punti += 45

  if (storico.percorsiUnici > 50 && storico.durataSessioneS < 60) punti += 25
  return Math.min(100, punti)
}
```

```
LA RISPOSTA È GRADUATA, E IL BLOCCO È L'ULTIMA OPZIONE
   0-30 passa · 31-60 rate limit più stretto, che costa poco a chi
   è umano · 61-85 challenge · 86-100 blocca

⚠ NON BLOCCARE MAI I CRAWLER DEI MOTORI DI RICERCA. Googlebot ha uno
  User-Agent dichiarato e nessun `accept-language`: prende 20 punti
  gratis. Va verificato con il reverse DNS — l'IP deve risolvere a
  `googlebot.com` e quel nome di nuovo allo stesso IP — e messo in
  lista di permesso. Bloccarlo si paga in posizionamento per
  settimane, e la causa non è ovvia.
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Il limite che non limita

**Obiettivo:** trovare i quattro difetti in un limitatore che sembra ragionevole, e correggerli.

```typescript
// Il codice in produzione, con un limite dichiarato di 100/minuto
const conteggi = new Map<string, number>()

setInterval(() => conteggi.clear(), 60_000)

export function verifica(req: Request, res: Response, avanti: NextFunction): void {
  const ip = req.headers['x-forwarded-for'] as string
  const n = (conteggi.get(ip) ?? 0) + 1
  conteggi.set(ip, n)

  if (n > 100) {
    res.status(429).send('Too Many Requests')
    return
  }
  avanti()
}
```

```
LA DIAGNOSI — quattro difetti
 1. `x-forwarded-for` LETTO DAL CLIENT: chi manda un valore casuale
    a ogni richiesta non incontra mai il limite (§A5)
 2. FINESTRA FISSA GLOBALE: la clear() azzera tutti insieme, quindi
    200 richieste a cavallo del secondo 59 passano (§A2)
 3. NESSUN HEADER: il client non sa il limite, non sa quanto resta,
    non sa quando riprovare — e riprova subito (§A4)
 4. IN MEMORIA CON PIÙ ISTANZE: con sei processi il limite vero è
    600/minuto, non 100 (§A3)
```

```typescript
// LA SOLUZIONE — sliding window in Redis, chiave affidabile, header
// su ogni risposta, ripiego se Redis non risponde
import type { Request, Response, NextFunction } from 'express'

const TETTO = 100
const FINESTRA_MS = 60_000

export function verificaCorretta(limitatore: LimitatoreConRipiego) {
  return async (req: Request, res: Response, avanti: NextFunction): Promise<void> => {
    // 1. La chiave viene dall'identità se c'è, e l'IP è quello
    //    firmato dal CDN o contato a partire dal nostro proxy
    const chiave = chiaveDiLimite(req)

    // 2. e 4. Lo stato sta in Redis, con finestra scorrevole
    const esito = await limitatore.verifica(chiave)

    // 3. Gli header ci sono SEMPRE, anche quando la richiesta passa
    res.setHeader('X-RateLimit-Limit', TETTO)
    res.setHeader('X-RateLimit-Remaining', esito.rimanenti)
    res.setHeader('X-RateLimit-Reset', Math.ceil((Date.now() + FINESTRA_MS) / 1000))

    if (esito.consentito) return void avanti()

    const attesa = Math.max(1, Math.ceil(esito.riprovaTraMs / 1000))
    res.setHeader('Retry-After', attesa)
    res.status(429).type('application/problem+json').json({
      type: 'https://api.esempio.it/problemi/limite-superato',
      title: 'Too Many Requests',
      status: 429,
      detail: `Massimo ${TETTO} richieste al minuto. Riprova tra ${attesa} secondi.`,
    })
  }
}
```

```
# VERIFICA — 100 richieste al secondo 59, 100 al secondo 61
#   prima → 200 passano, con un limite dichiarato di 100
#   dopo  → le seconde 100 sono rifiutate: la finestra scorrevole
#           vede ancora le prime
```

---

### Esercizio 2 — Il limitatore che ha spento il sito

**Obiettivo:** capire perché un guasto di Redis è diventato un'interruzione totale, e renderlo impossibile.

```typescript
// Il codice, e l'incidente: Redis ha fatto failover per 40 secondi.
// Il sito è rimasto giù 11 minuti.
export async function limita(chiave: string): Promise<boolean> {
  const n = await redis.incr(`limite:${chiave}`)   // ① senza timeout
  await redis.expire(`limite:${chiave}`, 60)       // ② non atomico
  return n <= 100
}

export async function middleware(req: Request, res: Response, avanti: NextFunction) {
  if (!(await limita(req.ip))) {                   // ③ eccezione = 500
    return res.status(429).send()
  }
  avanti()
}
```

```
LA DIAGNOSI — tre difetti che si sono sommati
 1. NESSUN TIMEOUT: durante il failover ogni richiesta ha aspettato
    il timeout TCP predefinito. Le connessioni si sono accumulate e
    il pool si è esaurito — il sito era giù con Redis già tornato.
 2. INCR + EXPIRE NON ATOMICI: alcune chiavi sono rimaste senza TTL
    (§B1). Quei client sono restati bloccati per sempre: sono gli
    11 minuti di coda dopo i 40 secondi di guasto.
 3. FAIL-CLOSED PER OMISSIONE: l'eccezione di Redis è diventata un
    500 su ogni richiesta. Nessuno l'aveva scelto — è successo (§B3).
```

```typescript
// LA SOLUZIONE — timeout, atomicità, e un ripiego dichiarato
export class LimitatoreResiliente {
  private readonly locale = new LimitatoreTokenBucket(20, 0.33)
  private ripiegoDa: number | null = null

  constructor(private readonly redis: Redis, private readonly tetto: number) {
    // Lo script Lua rende INCR ed EXPIRE una cosa sola
    this.redis.defineCommand('limita', { numberOfKeys: 1, lua: LUA_FINESTRA_FISSA })
  }

  async verifica(chiave: string): Promise<EsitoLimite> {
    try {
      const esito = await conScadenza(this.chiamaRedis(chiave), 50)
      if (this.ripiegoDa) {
        metriche.osserva('rate_limit.durata_ripiego_ms', Date.now() - this.ripiegoDa)
        this.ripiegoDa = null
      }
      return esito
    } catch (errore) {
      // Il fallimento è ATTESO e GESTITO: si passa al conteggio
      // locale, più stretto, e si accende un allarme
      this.ripiegoDa ??= Date.now()
      metriche.incrementa('rate_limit.ripiego', { motivo: nomeErrore(errore) })
      return this.locale.verifica(chiave)
    }
  }

  private async chiamaRedis(chiave: string): Promise<EsitoLimite> {
    const [ok, rimanenti, ttl] = await (this.redis as never as {
      limita(k: string, t: number, f: number): Promise<[number, number, number]>
    }).limita(`limite:${chiave}`, this.tetto, 60)
    return { consentito: ok === 1, rimanenti, riprovaTraMs: ttl * 1000 }
  }
}
```

```
# VERIFICA — docker stop redis, e si guarda l'API
# Atteso: il traffico continua, `rate_limit.ripiego` sale, arriva
#   l'alert, e non compare nessun 500. Il limite effettivo diventa
#   più stretto, non più largo.
# docker start redis → la metrica si ferma e `durata_ripiego_ms`
#   registra quanto è durato.
```

---

### Esercizio 3 — La tempesta di ritentativi

**Obiettivo:** un client mobile amplifica ogni rallentamento del server. Trovare i tre moltiplicatori.

```typescript
// Il client, in produzione su 80.000 dispositivi
export async function chiamaApi(percorso: string): Promise<unknown> {
  for (let i = 0; i < 3; i++) {                    // ①
    const r = await fetch(`https://api.esempio.it${percorso}`)
    if (r.ok) return r.json()
    await new Promise((res) => setTimeout(res, 1000))  // ②
  }
  throw new Error('non riuscito')
}

export async function sincronizza(): Promise<void> {
  // ③ chiamato dallo scheduler ogni 15 minuti, all'ora esatta
  for (const risorsa of ['ordini', 'prodotti', 'clienti']) {
    await chiamaApi(`/api/${risorsa}`)
  }
}
```

```
LA DIAGNOSI — tre moltiplicatori che si compongono
 1. RITENTATIVI SU QUALUNQUE ERRORE: un 400 e un 404 vengono
    ritentati tre volte. Non guariranno mai, e il carico è triplo.
 2. ATTESA FISSA E SENZA JITTER: mille client bloccati insieme
    riprovano insieme, esattamente un secondo dopo (§B5).
 3. LO SCHEDULER ALL'ORA ESATTA: 80.000 dispositivi chiamano nello
    stesso secondo, quattro volte l'ora. Il picco è 240.000
    richieste in un secondo su una media di 90/secondo.
```

```typescript
// LA SOLUZIONE — ritentare solo ciò che può guarire, distribuire
// nel tempo, e smettere quando è chiaro che il server è in
// difficoltà
export async function chiamaApiCorretta(percorso: string, massimo = 4): Promise<unknown> {
  if (interruttore.aperto()) throw new Error('servizio non disponibile')

  for (let tentativo = 0; ; tentativo++) {
    const risposta = await fetch(`https://api.esempio.it${percorso}`)
    if (risposta.ok) {
      interruttore.registraSuccesso()
      return risposta.json()
    }

    // 1. Solo 429 e 5xx possono guarire ritentando
    const ritentabile = risposta.status === 429 || risposta.status >= 500
    if (!ritentabile) throw new Error(`errore ${risposta.status}`)

    interruttore.registraFallimento()
    if (tentativo >= massimo || interruttore.aperto()) {
      throw new Error(`non riuscito dopo ${tentativo + 1} tentativi`)
    }

    // 2. Retry-After se c'è, altrimenti backoff con full jitter
    const indicato = risposta.headers.get('retry-after')
    const attesa = indicato ? Number(indicato) * 1000 + Math.random() * 2000 : attesaMs(tentativo)
    await new Promise((r) => setTimeout(r, attesa))
  }
}

// 3. Lo scheduler si spalma su cinque minuti, in modo STABILE per
//    dispositivo: un valore casuale a ogni avvio riallineerebbe la
//    flotta dopo ogni aggiornamento
export function ritardoSincronizzazioneMs(idDispositivo: string): number {
  let h = 0
  for (const c of idDispositivo) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return (h % 300) * 1000
}
```

```
# VERIFICA — il picco misurato sul server
# prima: 240.000 richieste nel secondo :00 di ogni quarto d'ora
# dopo:  ~800 al secondo, distribuite su 300 secondi — e sotto
#        errore il circuito si apre dopo cinque fallimenti invece
#        di insistere
```

---

## C2. Mini-progetto: il limitatore dell'API ordini

**Obiettivo:** proteggere l'API ordini del corso con quattro livelli che si coprono a vicenda.

```
IL PROGETTO — quattro livelli, dal più esterno al più interno

  1. EDGE (Vercel Edge Middleware)
     · 300 req/min per IP su tutto, 5 req/5min su /api/auth/*
     ➜ ciò che cade qui non raggiunge mai il server
  2. ORIGIN, per identità
     · token bucket per utente, burst e sostenuto dal piano (§B4)
  3. ORIGIN, per costo
     · POST /ordini costa 5, POST /report/genera costa 50
     ➜ un limite in richieste non protegge da dieci report
  4. QUOTA MENSILE
     · contatore separato, azzerato alla fatturazione, con un
       avviso all'80% perché l'utente non ci sbatta contro

  OSSERVABILITÀ, trasversale
     · ogni rifiuto emette un evento con chiave, livello e costo
     · una settimana in sola osservazione prima di attivarlo (§D3)
```

```typescript
// middleware.ts — livello 1, all'edge
import { Ratelimit } from '@upstash/ratelimit'
import { Redis } from '@upstash/redis'
import { NextResponse, type NextRequest } from 'next/server'

const generale = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(300, '60 s'),
  analytics: true,
  prefix: 'edge:generale',
})

const autenticazione = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(5, '300 s'),
  prefix: 'edge:auth',
})

export async function middleware(richiesta: NextRequest): Promise<NextResponse> {
  const ip = richiesta.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ?? '0.0.0.0'
  const suAuth = richiesta.nextUrl.pathname.startsWith('/api/auth/')
  const esito = await (suAuth ? autenticazione : generale).limit(ip)

  const intestazioni = new Headers({
    'x-ratelimit-limit': String(esito.limit),
    'x-ratelimit-remaining': String(esito.remaining),
    'x-ratelimit-reset': String(esito.reset),
  })

  if (!esito.success) {
    intestazioni.set('retry-after', String(Math.ceil((esito.reset - Date.now()) / 1000)))
    intestazioni.set('content-type', 'application/problem+json')
    return new NextResponse(
      JSON.stringify({ title: 'Too Many Requests', status: 429 }),
      { status: 429, headers: intestazioni },
    )
  }

  const risposta = NextResponse.next()
  intestazioni.forEach((v, k) => risposta.headers.set(k, v))
  return risposta
}

export const config = { matcher: ['/api/:path*'] }
```

```typescript
// lib/limiti.ts — livelli 2, 3 e 4 all'origin
const PIANI = { free: { burst: 5, alMinuto: 20, alMese: 5_000 } } as const

export async function verificaOrigin(
  utente: { id: string; piano: keyof typeof PIANI },
  metodo: string,
  percorso: string,
): Promise<{ consentito: boolean; motivo?: string; attesaS?: number }> {
  const piano = PIANI[utente.piano]
  const costo = costoDi(metodo, percorso)

  // Livelli 2 e 3 insieme: il costo è quanti token consuma
  const secchio = new LimitatoreTokenBucket(piano.burst, piano.alMinuto / 60)
  const esito = secchio.verifica(`utente:${utente.id}`, costo)
  if (!esito.consentito) {
    return { consentito: false, motivo: 'ritmo', attesaS: Math.ceil(esito.riprovaTraMs / 1000) }
  }

  // Livello 4: la quota è un contatore separato, con la sua finestra
  const usati = await quota.consuma(utente.id, costo)
  if (usati > piano.alMese) {
    return { consentito: false, motivo: 'quota' } // niente Retry-After: non basta aspettare
  }
  if (usati > piano.alMese * 0.8) avvisaUnaVoltaAlGiorno(utente.id, usati / piano.alMese)

  return { consentito: true }
}
```

```
# ESTENSIONI, in ordine di utilità
# 1. Il punteggio bot del §B9 come quinto livello, in osservazione
#    per due settimane prima di collegarlo
# 2. GET /api/quota che espone consumo e reset: toglie la maggior
#    parte dei ticket di assistenza
# 3. Limiti adattivi (§D2) e un test di carico k6 (§D1) che
#    verifica il tetto dichiarato
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Testare un rate limiter

```
IL PROBLEMA: un rate limiter dipende dal TEMPO, e i test che
aspettano davvero sono lenti e instabili. La soluzione è iniettare
l'orologio, non usare `Date.now()` direttamente.
```

```typescript
// Con un orologio iniettato, un'ora di traffico si simula in un
// millisecondo — e il test non è mai instabile
import { describe, it, expect, vi } from 'vitest'

describe('token bucket', () => {
  it('ricarica al ritmo previsto e non supera la capacità', () => {
    vi.useFakeTimers()
    vi.setSystemTime(0)
    const secchio = new LimitatoreTokenBucket(10, 2)

    for (let i = 0; i < 10; i++) expect(secchio.verifica('a').consentito).toBe(true)
    expect(secchio.verifica('a').consentito).toBe(false)

    vi.setSystemTime(3_000) // tre secondi → sei token
    expect(secchio.verifica('a', 6).consentito).toBe(true)
    expect(secchio.verifica('a').consentito).toBe(false)
    vi.useRealTimers()
  })

  it('la finestra fissa soffre il boundary burst, la scorrevole no', async () => {
    // Il test che dimostra il difetto del §A2: 2×N richieste a
    // cavallo del confine passano con la prima, non con la seconda
  })
})
```

```
LE QUATTRO CATEGORIE, E COSA COPRE CIASCUNA
  unità ► l'algoritmo con l'orologio finto: confini, ricarica,
      costo, azzeramento
  concorrenza ► 100 richieste simultanee sulla stessa chiave devono
      dare esattamente N passate: smaschera le race di §B1
  carico ► k6 o simili: il tetto DICHIARATO è quello applicato,
      sotto traffico vero e con più istanze attive
  guasto ► si spegne Redis a metà del test di carico, e l'API deve
      restare in piedi (§B3)

⚠ IL TEST DI CONCORRENZA VA FATTO CONTRO REDIS VERO, non contro un
  mock: la race sta nell'interazione con Redis, e un mock la
  nasconde per costruzione. Testcontainers (tutorial_15 §D2) avvia
  un Redis effimero per la suite.
```

---

## D2. Limiti adattivi e load shedding

```
IL LIMITE FISSO HA UN DIFETTO STRUTTURALE: è tarato sul caso
peggiore previsto. Se è troppo alto non protegge quando il sistema è
già in difficoltà; se è troppo basso spreca capacità il 99% del tempo.

IL LIMITE ADATTIVO guarda la SALUTE del sistema, non solo il
conteggio:
    latenza p99 sotto la soglia   ─► allarga, fino a un tetto
    latenza p99 sopra la soglia   ─► stringe, subito e di molto
```

```typescript
// Il moltiplicatore si applica sopra i limiti per piano: sale piano
// e scende in fretta, che è l'asimmetria giusta — allargare troppo
// presto ricrea la congestione appena risolta.
export class LimiteAdattivo {
  private moltiplicatore = 1

  aggiorna(p99Ms: number, sogliaMs = 500): void {
    this.moltiplicatore =
      p99Ms > sogliaMs * 2 ? Math.max(0.2, this.moltiplicatore * 0.5)
      : p99Ms > sogliaMs ? Math.max(0.2, this.moltiplicatore * 0.9)
      : Math.min(1, this.moltiplicatore * 1.05)
  }

  tettoEffettivo(base: number): number {
    return Math.max(1, Math.floor(base * this.moltiplicatore))
  }
}
```

```
IL LOAD SHEDDING è il gradino successivo: quando il sistema è
saturo, non si rifiuta a caso — si rifiuta per PRIORITÀ.

  0 pagamenti e login ► mai · 1 scrittura ► per ultimi
  2 lettura ► prima · 3 analytics e prefetch ► subito

⚠ E SI RIFIUTA PRESTO. Un 429 restituito dopo aver già eseguito la
  query è carico sprecato due volte: la decisione va presa prima di
  toccare il database.
```

---

## D3. Osservare prima di bloccare

```
LA REGOLA, E NON HA ECCEZIONI: un limite nuovo entra in produzione
in SOLA OSSERVAZIONE. Si registra chi lo avrebbe superato, non lo si
blocca. Dopo una settimana — che comprende un lunedì mattina e un
fine settimana — si guarda l'elenco.

Nella lista di chi "sarebbe stato bloccato" ci sono quasi sempre:
  · il cliente più grosso, che fa un import notturno legittimo
  · il monitoraggio interno
  · un'integrazione di un partner che nessuno ricordava
  · e, in fondo, il traffico che si voleva davvero fermare
```

```typescript
// La modalità si sceglie per limite, non per servizio: si passa a
// enforce un limite alla volta.
export type Modalita = 'osserva' | 'applica'

export function applicaLimite(
  nome: string,
  modalita: Modalita,
  esito: EsitoLimite,
  contesto: { chiave: string; percorso: string },
): boolean {
  if (esito.consentito) return true

  metriche.incrementa('rate_limit.superato', { limite: nome, modalita, percorso: contesto.percorso })
  registro.warn('limite superato', { limite: nome, modalita, ...contesto })
  return modalita === 'osserva' // in osservazione, passa comunque
}
```

```
LE METRICHE CHE SERVONO DAVVERO, e i loro allarmi

  tasso di rifiuto per endpoint ► sopra il 5% dove prima era zero:
      qualcosa è cambiato, e spesso è un rilascio, non un attacco
  chiavi distinte bloccate ► una sola è un client rotto, migliaia
      sono un attacco distribuito
  latenza del limitatore ► sta sul percorso di ogni richiesta: il
      suo p99 è il pavimento del p99 dell'API
  ripiego attivo (§B3) ► allarme immediato: si sta girando senza
      protezione vera

⚠ NON LOGGARE UNA RIGA PER OGNI RICHIESTA BLOCCATA. Sotto attacco
  sono milioni di righe al minuto, e il costo del logging diventa
  il secondo guasto. Si campiona, o si aggregano contatori.
```

---

## D4. Multi-region: lo stato che non si sincronizza

```
IL PROBLEMA: con istanze in tre continenti, un contatore coerente
richiede un round trip al nodo che lo possiede — su OGNI richiesta,
per proteggerne una su mille.

  LE TRE STRATEGIE, e cosa si perde con ciascuna
    Redis unico globale ► coerente, ma la latenza è quella del
        continente più lontano
    Redis per regione ► veloce, ma il limite effettivo è N volte
        quello dichiarato
    locale + flush periodico ► latenza zero sulla verifica, e uno
        sforamento pari al traffico di un intervallo di flush
```

```typescript
// Il compromesso che si usa in pratica: si conta in locale, si
// sincronizza ogni pochi secondi, e si tiene un margine.
export class LimitatoreMultiRegione {
  private locali = new Map<string, number>()

  constructor(
    private readonly redis: Redis,
    private readonly tetto: number,
    intervalloMs = 3_000,
  ) {
    setInterval(() => void this.sincronizza(), intervalloMs).unref()
  }

  async verifica(chiave: string): Promise<boolean> {
    const locale = (this.locali.get(chiave) ?? 0) + 1
    this.locali.set(chiave, locale)

    // La quota locale è il tetto diviso le regioni, meno un margine
    // per lo sfasamento fra un flush e l'altro
    const globale = Number(await this.redis.get(`globale:${chiave}`)) || 0
    return globale + locale <= this.tetto * 0.9
  }

  private async sincronizza(): Promise<void> {
    const pipeline = this.redis.pipeline()
    for (const [chiave, n] of this.locali) {
      if (n > 0) pipeline.incrby(`globale:${chiave}`, n).expire(`globale:${chiave}`, 120)
    }
    await pipeline.exec()
    this.locali.clear()
  }
}
```

⚠ Lo sforamento massimo è calcolabile, e va scritto nella documentazione: con N regioni e un flush ogni T secondi, nel caso peggiore passano `N × ritmo × T` richieste in più. Con tre regioni, 100/minuto e flush ogni 3 secondi sono quindici richieste — accettabile per un'API di lettura, non per un tentativo di login.

---

## D5. Quando NON serve un rate limiter

```
UN RATE LIMITER È CODICE SUL PERCORSO DI OGNI RICHIESTA: aggiunge
latenza, una dipendenza che può guastarsi e una classe di incidenti
nuova. Il costo è reale.

NON SERVE, O NON ANCORA, QUANDO
  ❌ il servizio è interno e i chiamanti sono noti e pochi: un
     limite di concorrenza sul pool di connessioni protegge già
  ❌ c'è già davanti una piattaforma che lo fa in modo dichiarativo:
     riscriverlo in codice aggiunge un secondo posto dove sbagliare
  ❌ il problema vero è un'API troppo cara: rendere l'endpoint dieci
     volte più leggero risolve meglio che limitarne l'uso
SERVE, SENZA DISCUSSIONE, QUANDO
  ✅ l'API è pubblica, o comunque raggiungibile da internet
  ✅ c'è un endpoint di autenticazione — sempre, dal primo giorno
  ✅ una richiesta costa denaro misurabile (modelli linguistici,
     SMS, servizi a consumo)
  ✅ un solo client può degradare il servizio per tutti gli altri
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
RATE LIMITING E EDGE — Mappa dei concetti

L'ALGORITMO
├── fixed window: una INCR, e il boundary burst
├── sliding window: preciso, memoria o calcolo in più
├── token bucket: burst più ritmo sostenuto — la scelta predefinita
├── leaky bucket: uscita costante, burst penalizzati
└── GCRA: la precisione dello sliding con un timestamp solo

LA CHIAVE
├── l'IP non identifica una persona: NAT in un verso, rotazione
│     nell'altro — e l'identità verificata lo batte sempre
├── X-Forwarded-For è scritto dal client: si conta dal proprio
│     proxy, o si usa l'header firmato dal CDN
└── i limiti si sovrappongono: IP e utente e globale

IL CONTRATTO
├── header su OGNI risposta, non solo sul 429: senza, il client
│     riprova subito e nasce la retry storm
├── Retry-After è l'unico standardizzato — gli X-RateLimit-* no
└── il corpo del 429 in RFC 9457, senza dettagli d'implementazione

DISTRIBUITO
├── INCR + EXPIRE non è atomico: Lua, o chiavi senza TTL
├── Redis Cluster: hash tag per evitare CROSSSLOT
├── timeout stretto e FAIL-OPEN: il limitatore non deve spegnere
│     il servizio che protegge
└── multi-region: si sceglie fra latenza e precisione, e si
      documenta lo sforamento

IL CLIENT
├── backoff esponenziale CON jitter — senza, i tentativi si
│     risincronizzano
├── ritentare solo 429 e 5xx, e solo se l'operazione è idempotente
├── il retry in UN solo livello: tre livelli fanno 27 richieste
└── circuit breaker per smettere quando è chiaro che non serve

L'EDGE
├── il 429 che nasce all'edge non attraversa la rete
├── V8 isolate, non Node: niente fs, niente socket, CPU contata
├── Durable Object per la coerenza, con un limite di throughput
├── cache: s-maxage e stale-while-revalidate, mai public sui dati
│     di sessione
└── WAF (contenuto), rate limit (frequenza) e bot (comportamento):
      tre livelli distinti e non sostituibili

IN PRODUZIONE
├── sola osservazione per una settimana prima di applicare, e
│     allarme su tasso di rifiuto e ripiego attivo
└── quota ≠ rate limit: proteggono cose diverse, servono entrambe
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Sai perché un limite esiste, e che i casi più frequenti non sono attacchi
- [ ] Distingui i cinque algoritmi e sai quale scegliere, con la motivazione
- [ ] Sai cos'è il boundary burst e su quali endpoint non è tollerabile
- [ ] Scrivi un token bucket che ricalcola alla lettura, senza timer
- [ ] Sai perché un limitatore in memoria non regge più istanze
- [ ] Metti gli header su ogni risposta, e sai che solo
      `Retry-After` è standardizzato
- [ ] Non usi mai `X-Forwarded-For` così come arriva

**Parte B — Comprensione**

- [ ] Sai perché `INCR` + `EXPIRE` va sostituito da uno script Lua
- [ ] Sai cos'è un errore CROSSSLOT e come si evita
- [ ] Sai quanto costa uno sliding window in Redis, in memoria e in tempo
- [ ] Scegli fail-open o fail-closed per endpoint, e metti sempre
      un timeout sul limitatore
- [ ] Assegni un costo diverso agli endpoint costosi, e distingui
      quota da rate limit
- [ ] Sai perché il backoff senza jitter non risolve la retry storm
- [ ] Sai perché un 429 all'edge costa meno di uno all'origin, e
      conosci i vincoli di un edge runtime
- [ ] Sai quando una risposta non può essere `public`
- [ ] Sai perché WAF, rate limit e bot management non si sostituiscono

**Parte C — Pratica**

- [ ] Hai corretto un limitatore con chiave falsificabile e senza header
- [ ] Hai reso un limitatore incapace di spegnere il servizio
- [ ] Hai eliminato tre moltiplicatori di carico da un client
- [ ] Hai costruito una difesa a quattro livelli che si coprono

**Parte D — Esperto**

- [ ] Testi un rate limiter con l'orologio iniettato, e la concorrenza contro Redis vero
- [ ] Sai cos'è un limite adattivo e come si compone con il load shedding
- [ ] Attivi ogni limite nuovo in sola osservazione
- [ ] Sai calcolare lo sforamento di un limitatore multi-region
- [ ] Sai dire quando un rate limiter non serve

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| `X-Forwarded-For` letto così com'è | Un valore nuovo a ogni richiesta aggira il limite | Contare dal proprio proxy, o header firmato dal CDN |
| Limitare solo per IP | Blocca le aziende dietro NAT, non ferma la rotazione | Chiave per identità, con limiti sovrapposti |
| `INCR` + `EXPIRE` separati | Chiavi senza TTL: blocco permanente e silenzioso | Uno script Lua atomico |
| Nessun timeout su Redis | Una latenza di Redis diventa un'interruzione dell'API | Timeout stretto e ripiego dichiarato |
| Fail-closed sul traffico generico | Redis giù significa sito giù | Fail-open, tranne su login e pagamenti |
| Header solo sul 429 | Il client non può rallentare da solo | Header su ogni risposta |
| Contare le richieste, non il costo | Dieci report pesano come dieci letture | Costo in token per endpoint |
| Backoff senza jitter | I client si risincronizzano e la tempesta si ripete | Full jitter, e obbedire a `Retry-After` |
| `public` su una risposta personalizzata | La CDN serve i dati di un utente a un altro | `private, no-store` su tutto ciò che dipende dalla sessione |
| Un limite nuovo attivato subito | Blocca il cliente più grosso il primo giorno | Una settimana in sola osservazione |
| Bloccare per User-Agent sospetto | Googlebot sparisce dai risultati per settimane | Punteggio graduato, verifica reverse DNS, lista di permesso |

---

## Troubleshooting rapido

**Il limite dichiarato non corrisponde a quello applicato**
- Causa: conteggio in memoria con più istanze, oppure sforamento multi-region
- Fix: stato condiviso; se il conteggio è locale, dividere il tetto per il numero di istanze

**Un client resta bloccato anche a traffico fermo**
- Causa: chiave rimasta senza TTL dopo un guasto fra `INCR` ed `EXPIRE`
- Fix: script Lua atomico; `TTL chiave` in Redis per confermare, poi rimuovere le chiavi orfane

**L'API è lenta e le query sono veloci**
- Causa: il limitatore attende Redis senza timeout
- Fix: timeout sotto i 50 ms e ripiego locale; misurare il p99 del limitatore separatamente

**Errore `CROSSSLOT keys don't hash to the same slot`**
- Causa: uno script Lua su più chiavi in Redis Cluster
- Fix: hash tag comune, `limite:{utente:42}:*`

**Il traffico legittimo di un cliente viene bloccato**
- Causa: chiave per IP con molti utenti dietro lo stesso indirizzo
- Fix: chiave per identità dove disponibile; limite più alto per le API key note

**La CDN serve dati di un utente a un altro**
- Causa: `Cache-Control: public` su una risposta che dipende dalla sessione
- Fix: `private, no-store`; verificare ogni risposta `public` contro cookie e `Authorization`

**Googlebot ha smesso di indicizzare**
- Causa: rate limit o bot detection che colpisce i crawler
- Fix: verifica reverse DNS e lista di permesso; controllare Search Console per i 429

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_23_websocket_security.md` | Il rate limiting su una connessione persistente: si contano i messaggi, non le richieste |
| `tutorial_24_graphql.md` | Una sola richiesta può costare quanto mille: il costo si calcola sulla query, non sull'endpoint |
| `tutorial_25_nextjs.md` | Il middleware all'edge nel contesto completo del framework |
| `tutorial_14_sicurezza_web.md` | Il WAF e il bot management dentro il quadro delle minacce |

---

## Risorse di riferimento

**Specifiche:** [RFC 9110 §15.5.30 — 429](https://httpwg.org/specs/rfc9110.html#status.429) e [§10.2.3 — Retry-After](https://httpwg.org/specs/rfc9110.html#field.retry-after) · [draft-ietf-httpapi-ratelimit-headers](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/) · [RFC 9457 — Problem Details](https://www.rfc-editor.org/rfc/rfc9457)

**Documentazione:** [Cloudflare Workers](https://developers.cloudflare.com/workers/) e [Rate Limiting Rules](https://developers.cloudflare.com/waf/rate-limiting-rules/) · [Vercel Edge Functions](https://vercel.com/docs/functions/edge-functions) · [Upstash Ratelimit](https://github.com/upstash/ratelimit) · [Redis — pattern di rate limiting](https://redis.io/docs/latest/develop/use-cases/)

**Approfondimenti:** [Figma — un approccio alternativo al rate limiting](https://www.figma.com/blog/an-alternative-approach-to-rate-limiting/), che spiega perché hanno scelto GCRA · [AWS — Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/), l'articolo che ha reso standard il full jitter · [Stripe — rate limits](https://stripe.com/docs/rate-limits) come esempio di contratto pubblico ben scritto

---

> **Fine del Tutorial 22 — Rate Limiting e Edge Computing**
>
> Prossimo tutorial: `tutorial_23_websocket_security.md`
