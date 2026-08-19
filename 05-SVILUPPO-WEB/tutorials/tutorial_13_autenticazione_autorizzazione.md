# Tutorial 13 — Autenticazione e Autorizzazione: Dal Principiante all'Esperto

> **Companion a:** `13-autenticazione-autorizzazione.md`
> **Scope:** password e hashing, sessioni con cookie, JWT, access e refresh token con rotazione, dove conservare i token nel browser, CSRF, OAuth 2.1 e PKCE, OpenID Connect, RBAC e ABAC, MFA con TOTP e passkey, revoca, difesa dalla forza bruta
> **Prerequisiti:** `tutorial_10_nodejs.md` — middleware ed errori; `tutorial_12_database_web.md` — dove finiscono utenti e sessioni; `tutorial_11_api_design.md` — la differenza fra 401 e 403
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Node.js LTS · Express 5 · PostgreSQL 17 · argon2 · jose · OAuth 2.1 · WebAuthn

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Autenticazione e autorizzazione non sono la stessa cosa](#a1-autenticazione-e-autorizzazione-non-sono-la-stessa-cosa)
  - [A2. Le password: come si conservano](#a2-le-password-come-si-conservano)
  - [A3. Le sessioni con cookie](#a3-le-sessioni-con-cookie)
  - [A4. CSRF: l'attacco che i cookie rendono possibile](#a4-csrf-lattacco-che-i-cookie-rendono-possibile)
  - [A5. JWT: cosa è e cosa non è](#a5-jwt-cosa-è-e-cosa-non-è)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Sessioni o token: la scelta e i suoi costi](#b1-sessioni-o-token-la-scelta-e-i-suoi-costi)
  - [B2. Access token e refresh token](#b2-access-token-e-refresh-token)
  - [B3. Dove conservare i token nel browser](#b3-dove-conservare-i-token-nel-browser)
  - [B4. Rotazione dei refresh token e rilevamento del furto](#b4-rotazione-dei-refresh-token-e-rilevamento-del-furto)
  - [B5. OAuth 2.1: il flusso che resta, e perché](#b5-oauth-21-il-flusso-che-resta-e-perché)
  - [B6. OpenID Connect e la validazione dell'ID token](#b6-openid-connect-e-la-validazione-dellid-token)
  - [B7. Autorizzazione: RBAC, ABAC e dove metterla](#b7-autorizzazione-rbac-abac-e-dove-metterla)
  - [B8. MFA: TOTP e passkey](#b8-mfa-totp-e-passkey)
  - [B9. Revoca, e il problema che nessuno risolve del tutto](#b9-revoca-e-il-problema-che-nessuno-risolve-del-tutto)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: sistema di autenticazione completo](#c2-mini-progetto-sistema-di-autenticazione-completo)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Difendersi dalla forza bruta e dal credential stuffing](#d1-difendersi-dalla-forza-bruta-e-dal-credential-stuffing)
  - [D2. Reimpostazione della password fatta bene](#d2-reimpostazione-della-password-fatta-bene)
  - [D3. Autenticazione fra servizi](#d3-autenticazione-fra-servizi)
  - [D4. Multi-tenancy e SSO aziendale](#d4-multi-tenancy-e-sso-aziendale)
  - [D5. Cosa registrare, e cosa non registrare mai](#d5-cosa-registrare-e-cosa-non-registrare-mai)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   AUTENTICAZIONE            AUTORIZZAZIONE
   "chi sei?"                "cosa puoi fare?"
   → 401 se fallisce         → 403 se fallisce
        │                          │
        ▼                          ▼
  ┌───────────────┐        ┌────────────────────┐
  │ password+MFA  │        │ ruoli (RBAC)       │
  │ OAuth/OIDC    │        │ attributi (ABAC)   │
  │ passkey       │        │ proprietà della    │
  └───────┬───────┘        │ risorsa            │
          │                └────────────────────┘
          ▼
   ┌──────────────────────────────────────────────┐
   │ SESSIONE (stato sul server)                  │
   │   cookie HttpOnly+Secure+SameSite            │
   │   revoca immediata · richiede difesa CSRF    │
   ├──────────────────────────────────────────────┤
   │ TOKEN (stato nel token)                      │
   │   access breve (5-15 min) + refresh lungo    │
   │   scala senza stato · la revoca è il problema│
   └──────────────────────────────────────────────┘

   LE QUATTRO COSE CHE NON SI SBAGLIANO MAI
     1. le password si hashano con argon2id o scrypt, mai con SHA
     2. i token non stanno in localStorage
     3. i refresh token ruotano, e il riuso invalida la famiglia
     4. l'autorizzazione si applica sul SERVER, sempre
```

---

# Parte A — Basi Assolute

---

## A1. Autenticazione e autorizzazione non sono la stessa cosa

> **Analogia:** l'ingresso di un'azienda. Il badge dice *chi sei* — è autenticazione. Il fatto che il tuo badge apra la porta del laboratorio ma non quella della sala server è *cosa puoi fare* — è autorizzazione. Sono due controlli distinti, fatti in momenti diversi, e confonderli produce sia buchi sia interfacce incomprensibili.

```
AUTENTICAZIONE  stabilisce l'identità. Fallisce → 401 Unauthorized
  (il nome dello stato è storicamente sbagliato: significa
  "non autenticato"). Il client reagisce mostrando il login.

AUTORIZZAZIONE  stabilisce i permessi di un'identità già nota.
  Fallisce → 403 Forbidden. Rifare il login non serve a nulla, e il
  client deve mostrare un messaggio, non la schermata di accesso.

⚠ Confonderli produce il ciclo infinito: l'utente accede, viene
  rimandato indietro, riaccede, e non capisce mai che semplicemente
  non ha i diritti.
```

```
I TRE FATTORI DI AUTENTICAZIONE
  QUALCOSA CHE SAI      password, PIN
  QUALCOSA CHE HAI      telefono con app TOTP, chiave hardware
  QUALCOSA CHE SEI      impronta, volto

MFA significa fattori di CATEGORIE DIVERSE. Password più domanda di
sicurezza sono due cose che sai: non è MFA, è una password più
debole (la risposta si trova sui social).
```

---

## A2. Le password: come si conservano

```typescript
// ❌ TRE MODI DI SBAGLIARE, in ordine di gravità
//  1. in chiaro — al primo accesso non autorizzato al database, tutti
//     i tuoi utenti hanno perso anche gli account degli altri siti
//  2. cifrate — reversibili: chi ottiene la chiave le ottiene tutte
//  3. con SHA-256 o MD5 — sono funzioni VELOCI, progettate per essere
//     veloci. Una GPU ne prova miliardi al secondo: un dizionario da
//     dieci miliardi di password si esaurisce in pochi minuti.
```

```typescript
// ✅ argon2id: lento di proposito, e con un costo di MEMORIA che
//    rende inefficaci le GPU
import argon2 from 'argon2'

const OPZIONI_ARGON2 = {
  type: argon2.argon2id,
  memoryCost: 19 * 1024, // 19 MiB — il minimo raccomandato da OWASP
  timeCost: 2,           // iterazioni
  parallelism: 1,
} as const

export async function hashPassword(password: string): Promise<string> {
  // Il salt è generato e incluso nell'hash: non serve una colonna
  // separata, e due utenti con la stessa password hanno hash diversi
  return argon2.hash(password, OPZIONI_ARGON2)
}

export async function verificaPassword(hash: string, password: string): Promise<boolean> {
  try {
    return await argon2.verify(hash, password)
  } catch {
    // Un hash malformato non deve distinguersi da una password errata
    return false
  }
}
```

```
PERCHÉ IL SALT NON BASTA E SERVE LA LENTEZZA
  Il SALT rende inutili le rainbow table: due utenti con la stessa
  password hanno hash diversi, e nessuna tabella precalcolata serve.
  Non rallenta però l'attacco a UNA password specifica.
  Il COSTO DI CALCOLO fa quello: se verificare una password richiede
  50 ms, un attaccante ne prova venti al secondo invece di miliardi.

I PARAMETRI, E COME SI SCELGONO
  Si aumentano finché la verifica sul TUO hardware costa 50-100 ms.
  Meno è debole; molto di più diventa un modo per esaurire la CPU
  del server con richieste di login.
  Alternative accettabili: scrypt (nel core di Node) e bcrypt
  (⚠ tronca oltre 72 byte: le password lunghe perdono la coda).
```

```
LE REGOLE SULLE PASSWORD CHE OGGI SI CONSIDERANO CORRETTE
  ✅ lunghezza minima 8-12, MASSIMA almeno 64
  ✅ confronto con gli elenchi di password compromesse (HIBP con
     k-anonymity: si invia solo il prefisso dell'hash, mai la password)
  ✅ ammettere tutti i caratteri, spazi ed emoji compresi
  ❌ scadenza periodica obbligatoria — produce Password1!, Password2!
  ❌ regole di composizione ("una maiuscola, un simbolo") — riducono
     lo spazio delle scelte invece di aumentarlo
  ❌ domande di sicurezza: la risposta è pubblica sui social
```

---

## A3. Le sessioni con cookie

```
COME FUNZIONA, IN QUATTRO PASSI
  1. l'utente invia email e password
  2. il server verifica, crea una riga di sessione e genera un
     identificativo casuale
  3. il server risponde con Set-Cookie: sid=<identificativo>
  4. il browser rimanda il cookie a OGNI richiesta successiva,
     automaticamente

Il cookie contiene solo un identificativo opaco: i dati stanno sul
server. Chi lo ruba può impersonare l'utente — da qui i flag.
```

```typescript
// I flag del cookie di sessione, uno per uno
import type { Response } from 'express'

export function impostaCookieSessione(risposta: Response, idSessione: string): void {
  risposta.cookie('sid', idSessione, {
    // JavaScript non può leggerlo: un XSS non ruba la sessione
    httpOnly: true,
    // Solo su HTTPS: senza, viaggia in chiaro su una rete pubblica
    secure: true,
    // 'lax' è il predefinito dei browser moderni e blocca il CSRF
    // sulle richieste POST cross-site. 'strict' è più sicuro ma
    // rompe l'arrivo da un link esterno (l'utente sembra disconnesso).
    sameSite: 'lax',
    // Limita il cookie al percorso e al dominio necessari
    path: '/',
    maxAge: 24 * 60 * 60 * 1000,
    // ⚠ MAI impostare domain su un dominio padre condiviso: il
    //    cookie viaggerebbe verso ogni sottodominio, compresi quelli
    //    di terzi ospitati lì
  })
}
```

```
DUE ERRORI CHE ANNULLANO TUTTO IL RESTO

1. NON RIGENERARE L'IDENTIFICATIVO AL LOGIN (session fixation).
   Se un attaccante riesce a far impostare alla vittima un id di
   sessione che conosce, dopo il login quella sessione è
   autenticata — e lui la sta già usando. Al login si DISTRUGGE la
   sessione anonima e se ne crea una nuova.

2. LOGOUT CHE CANCELLA SOLO IL COOKIE. Il cookie sparisce dal
   browser, ma la riga di sessione resta valida sul server: chi
   l'aveva copiata continua a entrare. Il logout ELIMINA la sessione
   dall'archivio, e solo dopo cancella il cookie.
```

---

## A4. CSRF: l'attacco che i cookie rendono possibile

> **Analogia:** una delega firmata in bianco. Il browser allega il cookie a *ogni* richiesta verso il tuo sito, anche a quelle partite da un altro sito. Se `evil.example` contiene un modulo che invia una POST alla tua banca, il browser ci mette il cookie della banca — e la banca vede una richiesta autenticata.

```html
<!-- La pagina dell'attaccante: basta che la vittima la apra -->
<form action="https://banca.example/api/bonifici" method="POST" id="f">
  <input type="hidden" name="iban" value="IT00ATTACCANTE" />
  <input type="hidden" name="importo" value="5000" />
</form>
<script>
  document.getElementById('f').submit()
</script>
```

```
LE TRE DIFESE, IN ORDINE DI EFFICACIA

1. SameSite=Lax (o Strict) SUL COOKIE
   Il browser NON allega il cookie alle richieste POST che arrivano
   da un altro sito. È il predefinito dei browser moderni e da solo
   blocca l'attacco sopra. ⚠ Non basta se il tuo sito ha un
   sottodominio compromesso: per il browser è lo stesso sito.

2. TOKEN ANTI-CSRF (double submit o sincronizzato)
   Il server genera un valore casuale, lo mette in un campo del
   modulo (o in un header) e lo verifica alla ricezione. L'attaccante
   non può leggerlo, perché la same-origin policy glielo impedisce.

3. VERIFICA DELL'ORIGINE
   Controllare `Origin` o `Sec-Fetch-Site` sulle richieste che
   modificano lo stato. Semplice ed efficace come difesa aggiuntiva.
```

```typescript
// Il pattern "double submit" senza stato sul server: il token sta
// in un cookie leggibile e in un header, e i due devono combaciare
import { randomBytes, timingSafeEqual } from 'node:crypto'
import type { RequestHandler } from 'express'

const METODI_SICURI = new Set(['GET', 'HEAD', 'OPTIONS'])

export const protezioneCsrf: RequestHandler = (richiesta, risposta, prossimo) => {
  if (METODI_SICURI.has(richiesta.method)) {
    // Il token si emette sulle richieste di lettura
    if (!richiesta.cookies['csrf']) {
      // NON httpOnly: il JavaScript della pagina deve poterlo leggere
      // per rispedirlo nell'header. È sicuro perché un altro sito non
      // può leggere i cookie del tuo dominio.
      risposta.cookie('csrf', randomBytes(32).toString('base64url'), {
        secure: true,
        sameSite: 'lax',
      })
    }
    return prossimo()
  }

  const daCookie = richiesta.cookies['csrf'] ?? ''
  const daHeader = richiesta.get('X-CSRF-Token') ?? ''

  const a = Buffer.from(daCookie)
  const b = Buffer.from(daHeader)

  if (a.length === 0 || a.length !== b.length || !timingSafeEqual(a, b)) {
    risposta.status(403).json({ errore: 'Token CSRF mancante o non valido' })
    return
  }

  prossimo()
}
```

```
⚠ IL CSRF RIGUARDA LE CREDENZIALI CHE IL BROWSER INVIA DA SOLO:
  cookie, autenticazione HTTP di base, certificati client. Un'API che
  usa `Authorization: Bearer` non è vulnerabile, perché quell'header
  il browser non lo aggiunge da sé — deve metterlo il JavaScript, che
  su un altro sito non ha accesso al token.
```

---

## A5. JWT: cosa è e cosa non è

```
UN JWT È TRE PARTI IN BASE64URL, SEPARATE DA PUNTI
  eyJhbGciOiJFUzI1NiJ9 . eyJzdWIiOiJ1c3JfMSJ9 . MEUCIQD…
  └── header ──────────┘ └── payload ────────┘ └ firma ┘

  header   l'algoritmo di firma
  payload  i claim: sub (soggetto), exp (scadenza), iss (emittente),
           aud (destinatario), più i tuoi
  firma    HMAC o firma asimmetrica su header+payload
```

```
⚠ IL PAYLOAD È CODIFICATO, NON CIFRATO. Chiunque abbia il token lo
  legge: base64url è una codifica, non un lucchetto. Non ci si mette
  MAI un dato che non si mostrerebbe all'utente — e nemmeno uno che
  non si mostrerebbe a chi gli ruba il token.

LA FIRMA GARANTISCE L'INTEGRITÀ, NON LA SEGRETEZZA: dice che il
contenuto non è stato modificato, non che nessuno l'ha letto.
```

```typescript
// La verifica con `jose`: la libreria fa i controlli che a mano si
// dimenticano
import { SignJWT, jwtVerify } from 'jose'

const chiave = new TextEncoder().encode(process.env['JWT_SECRET'])

export async function firmaAccessToken(idUtente: string, ruoli: string[]) {
  return new SignJWT({ ruoli })
    .setProtectedHeader({ alg: 'HS256' })
    .setSubject(idUtente)
    .setIssuer('https://api.esempio.it')
    .setAudience('esempio-web')
    .setIssuedAt()
    .setExpirationTime('10m')
    .sign(chiave)
}

export async function verificaAccessToken(token: string) {
  // issuer e audience NON sono facoltativi: senza, un token emesso
  // da un altro sistema con la stessa chiave viene accettato
  const { payload } = await jwtVerify(token, chiave, {
    issuer: 'https://api.esempio.it',
    audience: 'esempio-web',
    algorithms: ['HS256'], // ⚠ la lista chiusa: vedi sotto
  })
  return payload
}
```

```
LE TRE VULNERABILITÀ STORICHE DEI JWT, E PERCHÉ LA LISTA DI
ALGORITMI VA DICHIARATA

1. alg: "none"  — alcune librerie accettavano token senza firma.
2. CONFUSIONE HS256/RS256 — un attaccante prende la chiave PUBBLICA
   (che è pubblica) e la usa come segreto HMAC. Se il server accetta
   entrambi gli algoritmi, la verifica passa.
3. `kid` NON VALIDATO — l'identificativo della chiave, se usato per
   costruire un percorso di file o una query, diventa un'iniezione.

Tutte e tre si chiudono dichiarando `algorithms: [...]` e non
lasciando che sia il TOKEN a dire come va verificato.
```

---

# Parte B — Comprensione Profonda

---

## B1. Sessioni o token: la scelta e i suoi costi

| | Sessione sul server | JWT senza stato |
|---|---|---|
| Dove sta lo stato | Database o Redis | Nel token |
| Revoca immediata | ✅ elimini la riga | ❌ vale fino alla scadenza |
| Costo per richiesta | Una lettura dell'archivio | Solo verifica della firma |
| Scala orizzontale | Serve un archivio condiviso | Nessuno stato da condividere |
| Cambio di permessi | Effetto immediato | Effetto alla scadenza |
| Vulnerabile a CSRF | ✅ (usa cookie) | Dipende da dove sta il token |
| Dimensione trasferita | ~40 byte | 300-800 byte a richiesta |

```
LA SCELTA, SENZA IDEOLOGIA
  Applicazione web con un backend proprio → SESSIONI. La revoca
    immediata vale più della scalabilità che non ti serve, e Redis
    regge centomila letture al secondo su una macchina piccola.
  API consumata da client diversi, o molti servizi che devono
    verificare senza chiamare un servizio centrale → TOKEN.
  Ibrido, ed è quello che fanno in molti: refresh token in un cookie
    HttpOnly (con revoca sul server) e access token brevissimo in
    memoria. Si ottengono entrambe le proprietà.

⚠ "I JWT scalano meglio" è vero solo se la verifica sostituisce
  davvero una lettura. Se poi carichi comunque l'utente dal database
  a ogni richiesta, hai il costo della lettura E la revoca lenta.
```

---

## B2. Access token e refresh token

```
   IL PROBLEMA: un token che vale un'ora è comodo ma pericoloso;
   uno che vale cinque minuti è sicuro ma costringe a riautenticarsi
   di continuo. I due token risolvono il compromesso.

   ACCESS TOKEN    breve (5-15 min), inviato a ogni richiesta,
                   verificato senza toccare il database
   REFRESH TOKEN   lungo (giorni), inviato SOLO all'endpoint di
                   rinnovo, memorizzato sul server, revocabile

   login  → access(10m) + refresh(30g)
   ogni richiesta → access
   access scaduto → POST /auth/refresh con il refresh
                    → nuovo access + NUOVO refresh (rotazione)
   logout → il refresh viene invalidato sul server
```

```typescript
// L'endpoint di rinnovo. Il refresh viaggia in un cookie HttpOnly
// limitato al percorso: non è accessibile al JavaScript e non viene
// inviato agli altri endpoint.
import type { RequestHandler } from 'express'
import { createHash, randomBytes } from 'node:crypto'

export const rinnova: RequestHandler = async (richiesta, risposta) => {
  const presentato = richiesta.cookies['rt']
  if (!presentato) {
    risposta.status(401).json({ errore: 'Nessun refresh token' })
    return
  }

  // Nel database si conserva l'HASH, non il token: chi legge la
  // tabella non ottiene credenziali utilizzabili
  const impronta = createHash('sha256').update(presentato).digest('hex')
  const salvato = await db.refreshToken.findUnique({ where: { impronta } })

  if (!salvato || salvato.scadeIl < new Date()) {
    risposta.status(401).json({ errore: 'Refresh token non valido' })
    return
  }

  const nuovo = randomBytes(32).toString('base64url')

  await db.$transaction([
    // Il vecchio viene marcato usato, non eliminato: serve a
    // rilevare il riuso (B4)
    db.refreshToken.update({ where: { impronta }, data: { usatoIl: new Date() } }),
    db.refreshToken.create({
      data: {
        impronta: createHash('sha256').update(nuovo).digest('hex'),
        utenteId: salvato.utenteId,
        famiglia: salvato.famiglia,
        scadeIl: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      },
    }),
  ])

  risposta.cookie('rt', nuovo, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    path: '/auth/refresh', // ⚠ non viaggia verso gli altri endpoint
    maxAge: 30 * 24 * 60 * 60 * 1000,
  })

  risposta.json({ accessToken: await firmaAccessToken(salvato.utenteId, salvato.ruoli) })
}
```

---

## B3. Dove conservare i token nel browser

```
localStorage        ❌ leggibile da QUALUNQUE script della pagina.
  Un XSS — anche in una dipendenza di terze parti caricata da una
  CDN — legge il token e lo esfiltra. È l'errore più diffuso, ed è
  quello che trasforma un XSS in una compromissione dell'account.

sessionStorage      ❌ stesso problema, con in più la perdita del
  token a ogni scheda nuova.

cookie NON HttpOnly ❌ il peggio dei due mondi: leggibile dal
  JavaScript E inviato automaticamente (quindi anche vulnerabile a CSRF).

cookie HttpOnly + Secure + SameSite   ✅ per il REFRESH token.
  Il JavaScript non lo vede, il browser lo invia solo al percorso
  dichiarato. ⚠ Richiede la difesa CSRF sugli endpoint che modificano
  lo stato.

memoria JavaScript (una variabile)    ✅ per l'ACCESS token.
  Sparisce a ogni ricaricamento della pagina — ed è esattamente ciò
  che si vuole: il refresh in cookie lo rigenera all'avvio.
```

```typescript
// Il pattern: access in memoria, refresh nel cookie, rinnovo
// automatico e UNA SOLA richiesta di rinnovo anche con più
// chiamate in parallelo
let accessToken: string | null = null
let rinnovoInCorso: Promise<string> | null = null

async function ottieniAccessToken(): Promise<string> {
  if (accessToken) return accessToken

  // Senza questa deduplica, dieci fetch che scadono insieme
  // lanciano dieci rinnovi — e con la rotazione nove falliscono
  rinnovoInCorso ??= fetch('/auth/refresh', { method: 'POST', credentials: 'include' })
    .then(async (risposta) => {
      if (!risposta.ok) throw new Error('sessione scaduta')
      const dati = (await risposta.json()) as { accessToken: string }
      accessToken = dati.accessToken
      return dati.accessToken
    })
    .finally(() => {
      rinnovoInCorso = null
    })

  return rinnovoInCorso
}

export async function richiestaAutenticata(url: string, opzioni: RequestInit = {}) {
  const token = await ottieniAccessToken()

  const risposta = await fetch(url, {
    ...opzioni,
    headers: { ...opzioni.headers, Authorization: `Bearer ${token}` },
  })

  // Un 401 significa che l'access è scaduto fra il controllo e l'uso:
  // si azzera e si riprova UNA volta
  if (risposta.status === 401) {
    accessToken = null
    const nuovo = await ottieniAccessToken()
    return fetch(url, {
      ...opzioni,
      headers: { ...opzioni.headers, Authorization: `Bearer ${nuovo}` },
    })
  }

  return risposta
}
```

---

## B4. Rotazione dei refresh token e rilevamento del furto

> **Analogia:** una chiave che si autodistrugge a ogni uso e ne consegna una nuova. Se qualcuno copia la chiave e la usa, alla volta successiva il proprietario presenta una chiave che risulta già consumata — e a quel punto si sa che c'è stata una copia, anche se non si sa da chi.

```
   IL RILEVAMENTO, PASSO PER PASSO
   1. il login crea il refresh R1, con una FAMIGLIA (un identificativo
      condiviso da tutta la catena di rinnovi)
   2. ogni rinnovo marca il vecchio "usato" e ne emette uno nuovo
      della stessa famiglia
   3. se arriva un token GIÀ USATO, significa che due parti hanno
      avuto lo stesso token: una è un ladro
   4. non si può sapere quale → si invalida l'INTERA FAMIGLIA e si
      costringe al login

   attaccante ruba R2 e lo usa   → riceve R3', la famiglia continua
   la vittima usa R2 (già usato) → RIUSO RILEVATO
                                 → famiglia invalidata: entrambi fuori
```

```typescript
// Il controllo che rende la rotazione una difesa e non una formalità
export async function rilevaRiuso(impronta: string): Promise<'ok' | 'riuso'> {
  const salvato = await db.refreshToken.findUnique({ where: { impronta } })
  if (!salvato) return 'riuso' // token inesistente: già ripulito, o falso

  if (salvato.usatoIl !== null) {
    // Il token era già stato scambiato: qualcuno ne ha una copia
    await db.refreshToken.updateMany({
      where: { famiglia: salvato.famiglia, revocatoIl: null },
      data: { revocatoIl: new Date() },
    })
    registro.warn(
      { utenteId: salvato.utenteId, famiglia: salvato.famiglia },
      'riuso di refresh token: famiglia revocata',
    )
    return 'riuso'
  }

  return 'ok'
}
```

```
⚠ IL FALSO POSITIVO CHE FA ARRABBIARE GLI UTENTI: due schede aperte
  rinnovano insieme, la seconda presenta un token appena consumato, e
  l'utente viene buttato fuori senza motivo. Le due difese:
   · deduplicare il rinnovo lato client (vedi B3)
   · una finestra di grazia di pochi secondi in cui il token appena
     ruotato è ancora accettato, restituendo lo stesso nuovo token
```

---

## B5. OAuth 2.1: il flusso che resta, e perché

```
OAuth NON È AUTENTICAZIONE. È DELEGA DI AUTORIZZAZIONE: permette a
un'applicazione di accedere a una risorsa PER CONTO dell'utente,
senza vederne la password. "Accedi con Google" funziona perché sopra
OAuth c'è OpenID Connect (B6), che aggiunge l'identità.

I QUATTRO RUOLI
  resource owner  l'utente          client  la tua applicazione
  authorization server  chi emette i token (Google, il tuo IdP)
  resource server  l'API che accetta i token

OAuth 2.1 ha RIMOSSO i flussi che non si potevano rendere sicuri:
  ❌ implicit — il token viaggiava nel frammento dell'URL, finiva
     nella cronologia e nei log
  ❌ password grant — l'applicazione vedeva la password: l'opposto
     dello scopo di OAuth
  ✅ resta authorization code + PKCE, per TUTTI i client, anche
     quelli con un segreto
```

```
   AUTHORIZATION CODE + PKCE
   1. il client genera un `code_verifier` casuale e ne calcola lo
      `code_challenge` = base64url(sha256(verifier))
   2. reindirizza all'authorization server con il challenge
   3. l'utente si autentica e acconsente
   4. l'authorization server rimanda un CODICE monouso al redirect_uri
   5. il client scambia codice + VERIFIER con i token

   Perché PKCE: se qualcuno intercetta il codice (un'app malevola
   registrata sullo stesso schema URL, un log di proxy), non può
   scambiarlo senza il verifier — che non ha mai lasciato il client.
```

```typescript
import { createHash, randomBytes } from 'node:crypto'

export function generaPkce() {
  // 32 byte casuali: il verifier NON deve essere prevedibile
  const verifier = randomBytes(32).toString('base64url')
  const challenge = createHash('sha256').update(verifier).digest('base64url')
  // S256, mai "plain": con plain il challenge È il verifier e la
  // protezione sparisce
  return { verifier, challenge, metodo: 'S256' as const }
}
```

```
I TRE CONTROLLI DA NON SALTARE
  1. `state` — un valore casuale legato alla sessione, verificato al
     ritorno: senza, un attaccante può far completare alla vittima un
     flusso che collega l'account della vittima al SUO profilo.
  2. `redirect_uri` — confronto ESATTO con la lista registrata. Le
     corrispondenze parziali sono la vulnerabilità più sfruttata:
     `https://tuosito.it.attaccante.example` passa un `startsWith`.
  3. il codice è MONOUSO e dura pochi secondi. Un secondo scambio
     deve fallire, e l'authorization server deve revocare i token
     già emessi con quel codice.
```

---

## B6. OpenID Connect e la validazione dell'ID token

```
OIDC è un livello sottile SOPRA OAuth 2.0 che aggiunge l'IDENTITÀ:
  · lo scope `openid` nella richiesta
  · un ID TOKEN (un JWT) accanto all'access token
  · un endpoint `/userinfo` e un documento di DISCOVERY
    (/.well-known/openid-configuration) da cui si leggono endpoint,
    algoritmi e URL delle chiavi pubbliche (JWKS)

⚠ ID TOKEN E ACCESS TOKEN NON SONO INTERCAMBIABILI.
  ID token   dice CHI È l'utente → si valida e si consuma nel CLIENT
  Access token  dà ACCESSO a un'API → si manda all'API, e il client
    non deve nemmeno provare a leggerlo (può essere opaco)
  Mandare l'ID token a un'API come se fosse un access token è un
  errore ricorrente: l'API accetterebbe un token emesso per un altro
  destinatario.
```

```typescript
// La validazione completa. Saltare anche un solo controllo apre
// un buco: `jose` li fa tutti se glieli si chiede.
import { createRemoteJWKSet, jwtVerify } from 'jose'

// Le chiavi pubbliche si scaricano dal JWKS e si mettono in cache:
// l'IdP le ruota, e il codice non deve essere aggiornato
const jwks = createRemoteJWKSet(new URL('https://accounts.google.com/.well-known/jwks.json'))

export async function validaIdToken(idToken: string, nonceAtteso: string) {
  const { payload } = await jwtVerify(idToken, jwks, {
    issuer: 'https://accounts.google.com',      // chi lo ha emesso
    audience: process.env['GOOGLE_CLIENT_ID']!, // per CHI è stato emesso
    algorithms: ['RS256'],
    clockTolerance: 30, // tolleranza sullo scarto di orologio
  })

  // Il nonce lega il token alla RICHIESTA che lo ha originato:
  // senza, un token valido catturato altrove può essere riproposto
  if (payload['nonce'] !== nonceAtteso) throw new Error('nonce non corrispondente')

  // `email_verified` non è un dettaglio: un provider che permette
  // email non verificate consente di rivendicare l'indirizzo altrui
  if (payload['email'] && payload['email_verified'] !== true) {
    throw new Error('email non verificata dal provider')
  }

  return payload
}
```

```
⚠ COLLEGARE GLI ACCOUNT SULL'EMAIL È PERICOLOSO. Se un utente si
  registra con la password usando mario@example.it, e poi qualcuno
  accede con un provider che afferma la stessa email SENZA averla
  verificata, i due account si fondono e l'attaccante entra. Si
  collega solo su email verificata, e meglio ancora si chiede una
  conferma esplicita all'utente già autenticato.
```

---

## B7. Autorizzazione: RBAC, ABAC e dove metterla

```
RBAC — i permessi passano per i RUOLI
  utente → ruolo → permessi
  Semplice, leggibile, e sufficiente per la maggior parte dei casi.
  Il limite: non esprime "il proprio", e "il proprio" è la
  condizione più comune di tutte.

ABAC — la decisione dipende dagli ATTRIBUTI di soggetto, risorsa,
  azione e contesto. Esprime "il proprietario può modificare il
  proprio documento finché è in bozza". Più potente, più difficile
  da leggere e da testare.

IN PRATICA: RBAC per le sezioni ("solo gli admin vedono il pannello")
e un controllo di PROPRIETÀ sulla singola risorsa. Il secondo è
quello che si dimentica.
```

```typescript
// ❌ IL BUCO PIÙ COMUNE (OWASP lo chiama IDOR): il ruolo è
//    verificato, la PROPRIETÀ no
app.get('/api/fatture/:id', richiedeRuolo('cliente'), async (richiesta, risposta) => {
  // Qualunque cliente autenticato legge la fattura di chiunque altro
  // cambiando l'id nell'URL
  risposta.json(await db.fattura.findUnique({ where: { id: richiesta.params.id } }))
})

// ✅ La proprietà entra nella QUERY, non in un `if` successivo:
//    così non c'è un ramo che qualcuno possa dimenticare
app.get('/api/fatture/:id', richiedeAutenticazione, async (richiesta, risposta) => {
  const fattura = await db.fattura.findFirst({
    where: { id: richiesta.params.id, clienteId: richiesta.utente!.id },
  })

  // 404 e non 403: un 403 confermerebbe che quella fattura esiste
  if (!fattura) throw new ErroreNonTrovato('Fattura', richiesta.params.id)

  risposta.json(fattura)
})
```

```
LE QUATTRO REGOLE DELL'AUTORIZZAZIONE
  1. NEGARE PER DEFAULT. Un endpoint nuovo senza controllo deve
     essere inaccessibile, non pubblico. Si ottiene applicando il
     middleware a livello di router e togliendolo esplicitamente
     dove serve.
  2. SUL SERVER, SEMPRE. Nascondere un pulsante è interfaccia, non
     sicurezza: la richiesta si costruisce a mano in dieci secondi.
  3. VICINO AL DATO. Un controllo nella query non si dimentica; un
     `if` in un handler sì.
  4. IN UN POSTO SOLO. Le regole sparse in venti file divergono. Una
     funzione `puo(utente, azione, risorsa)` è testabile; venti `if`
     no.
```

---

## B8. MFA: TOTP e passkey

```typescript
// TOTP (RFC 6238): un codice a sei cifre derivato da un segreto
// condiviso e dall'ora corrente, valido per una finestra di 30 s
import { authenticator } from 'otplib'

export function preparaTotp(email: string) {
  const segreto = authenticator.generateSecret() // 20 byte, base32
  const uri = authenticator.keyuri(email, 'Esempio', segreto)
  // L'URI diventa un QR code; il segreto si salva CIFRATO, non in chiaro
  return { segreto, uri }
}

export function verificaTotp(codice: string, segreto: string): boolean {
  // window: 1 accetta anche la finestra precedente e la successiva,
  // per tollerare orologi leggermente sfasati
  authenticator.options = { window: 1 }
  return authenticator.verify({ token: codice, secret: segreto })
}
```

```
LE TRE COSE CHE MANCANO A QUASI TUTTE LE IMPLEMENTAZIONI TOTP
  1. IL CODICE USATO NON PUÒ ESSERE RIUSATO. Senza, chi lo intercetta
     lo riusa per trenta secondi. Si memorizza l'ultimo contatore
     accettato e si rifiuta lo stesso.
  2. IL LIMITE DI TENTATIVI. Sei cifre sono un milione di
     combinazioni: senza limite si forzano in poche ore.
  3. I CODICI DI RECUPERO. Generati una volta, mostrati una volta,
     conservati come HASH e monouso. Senza, chi perde il telefono
     perde l'account — e l'assistenza diventa il punto debole.
```

```
LE PASSKEY (WebAuthn/FIDO2) SONO UNA CATEGORIA DIVERSA
  Una coppia di chiavi generata dal dispositivo: la privata non lo
  lascia mai, il server conserva solo la pubblica.
  ✅ NON esiste un segreto condiviso da rubare dal database
  ✅ IMMUNI AL PHISHING: la firma è legata all'ORIGINE, quindi una
     passkey per esempio.it non funziona su esemplo.it — ed è
     l'unico metodo che chiude davvero il phishing
  ✅ nessun codice da digitare
  ⚠ il recupero resta il punto difficile: le passkey sincronizzate
    (iCloud, Google) lo risolvono per gli utenti comuni; per gli
    altri serve un secondo metodo registrato.
```

---

## B9. Revoca, e il problema che nessuno risolve del tutto

```
CON LE SESSIONI la revoca è banale: si elimina la riga, e alla
richiesta successiva l'utente è fuori.

CON I JWT SENZA STATO non è possibile: il token è valido perché la
firma è valida, e il server non consulta nulla. Le quattro risposte,
con i loro costi:

1. ACCESS TOKEN MOLTO BREVI (5-15 minuti)
   Non è una revoca, è una finestra accettabilmente piccola. È la
   risposta giusta nella maggior parte dei casi, e costa nulla.

2. LISTA DI REVOCA (denylist) del `jti` in Redis, con TTL pari alla
   scadenza residua. Funziona, ma reintroduce la lettura per
   richiesta — cioè il costo che i JWT dovevano evitare.

3. UN CONTATORE DI VERSIONE per utente, incluso nel token e
   confrontato con quello nel database: incrementarlo invalida tutti
   i token di quell'utente. Utile per "esci da tutti i dispositivi"
   e per il cambio di password. Anche qui serve una lettura, ma è
   una sola e si mette in cache facilmente.

4. TOKEN OPACHI + INTROSPEZIONE: il token non contiene nulla e l'API
   chiede all'authorization server se è valido. Revoca perfetta,
   costo di rete a ogni richiesta.
```

```
QUANDO LA REVOCA DEVE ESSERE IMMEDIATA, E NON C'È COMPROMESSO
  · cambio o reimpostazione della password → invalidare TUTTE le
    sessioni e le famiglie di refresh
  · sospensione o licenziamento di un utente
  · revoca di un ruolo con privilegi elevati
  · sospetto di compromissione dell'account
  In questi casi, un access token che vive altri dieci minuti può
  non essere accettabile: serve il contatore di versione, oppure le
  sessioni.
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Trovare i difetti in un endpoint di login

**Obiettivo:** elencare tutti i problemi di questo codice e riscriverlo.

```typescript
// IL CODICE DA CORREGGERE
import { createHash } from 'node:crypto'

app.post('/login', async (richiesta, risposta) => {
  const { email, password } = richiesta.body

  const utente = await db.utente.findUnique({ where: { email } })
  if (!utente) {
    return risposta.status(404).json({ errore: 'Email non registrata' })
  }

  const hash = createHash('sha256').update(password).digest('hex')
  if (hash !== utente.passwordHash) {
    return risposta.status(401).json({ errore: 'Password errata' })
  }

  const token = jwt.sign({ id: utente.id, email: utente.email }, 'segreto123')
  risposta.json({ token, utente })
})
```

```
# SOLUZIONE — otto difetti

1. SHA-256 PER LA PASSWORD  funzione veloce: una GPU prova miliardi
   di combinazioni al secondo. → argon2id
2. NESSUN SALT  due utenti con la stessa password hanno lo stesso
   hash, e le rainbow table funzionano. → incluso in argon2
3. CONFRONTO CON !==  esce al primo byte diverso: attacco a tempo.
   → argon2.verify, che è a tempo costante
4. 404 SU EMAIL INESISTENTE  enumerazione degli account: si scopre
   chi è registrato provando indirizzi. → 401 identico in entrambi
   i casi, e stesso TEMPO di risposta
5. SEGRETO IN CHIARO NEL CODICE  finisce nel repository e nella
   cronologia git. → variabile d'ambiente, validata all'avvio
6. TOKEN SENZA SCADENZA  vale per sempre. → exp, più iss e aud
7. NESSUN LIMITE DI TENTATIVI  forza bruta senza ostacoli.
   → limite per IP E per account (vedi D1)
8. RESTITUISCE L'INTERO OGGETTO UTENTE  passwordHash compreso.
   → select esplicito dei campi pubblici
```

```typescript
// LA VERSIONE CORRETTA
import argon2 from 'argon2'
import { z } from 'zod'
import type { RequestHandler } from 'express'

const SchemaLogin = z.object({
  email: z.string().email().max(320),
  password: z.string().min(1).max(1024),
})

// Un hash fittizio con gli stessi parametri: si verifica anche
// quando l'utente non esiste, così il tempo di risposta non rivela
// se l'email è registrata
const HASH_FITTIZIO = await argon2.hash('utente-inesistente', OPZIONI_ARGON2)

export const login: RequestHandler = async (richiesta, risposta, prossimo) => {
  const { email, password } = SchemaLogin.parse(richiesta.body)

  if (!(await consumaTentativo(richiesta.ip, email))) {
    risposta.setHeader('Retry-After', '60')
    risposta.status(429).json({ errore: 'Troppi tentativi. Riprova più tardi.' })
    return
  }

  const utente = await db.utente.findUnique({
    where: { email: email.toLowerCase() },
    select: { id: true, email: true, nome: true, passwordHash: true, attivo: true, ruoli: true },
  })

  const valida = await argon2.verify(utente?.passwordHash ?? HASH_FITTIZIO, password)

  // Un messaggio SOLO: qualunque distinzione è un canale di
  // informazione per chi enumera gli account
  if (!utente || !valida || !utente.attivo) {
    risposta.status(401).json({ errore: 'Credenziali non valide' })
    return
  }

  await azzeraTentativi(email)
  await avviaSessione(risposta, utente)

  risposta.json({ utente: { id: utente.id, email: utente.email, nome: utente.nome } })
}
```

---

### Esercizio 2 — Rotazione dei refresh token con rilevamento del riuso

**Obiettivo:** implementare la rotazione e dimostrare con un test che il furto viene rilevato.

```sql
-- Lo schema. L'IMPRONTA, non il token: chi legge la tabella non
-- ottiene credenziali utilizzabili.
CREATE TABLE refresh_token (
  impronta    char(64) PRIMARY KEY,
  utente_id   bigint NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
  -- La famiglia lega tutti i token nati da uno stesso login
  famiglia    uuid NOT NULL,
  usato_il    timestamptz,
  revocato_il timestamptz,
  scade_il    timestamptz NOT NULL,
  creato_il   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_refresh_famiglia ON refresh_token (famiglia) WHERE revocato_il IS NULL;
CREATE INDEX idx_refresh_utente   ON refresh_token (utente_id);
```

```typescript
// SOLUZIONE — src/auth/refresh.ts
import { createHash, randomBytes, randomUUID } from 'node:crypto'

const DURATA_MS = 30 * 24 * 60 * 60 * 1000
const GRAZIA_MS = 10_000 // tolleranza per le schede concorrenti

const impronta = (token: string) => createHash('sha256').update(token).digest('hex')

export async function emettiRefresh(utenteId: bigint, famiglia = randomUUID()) {
  const token = randomBytes(32).toString('base64url')
  await db.refreshToken.create({
    data: {
      impronta: impronta(token),
      utenteId,
      famiglia,
      scadeIl: new Date(Date.now() + DURATA_MS),
    },
  })
  return token
}

export async function ruota(presentato: string): Promise<string> {
  const salvato = await db.refreshToken.findUnique({ where: { impronta: impronta(presentato) } })

  if (!salvato || salvato.revocatoIl || salvato.scadeIl < new Date()) {
    throw new ErroreAutenticazione('refresh non valido')
  }

  if (salvato.usatoIl) {
    // Finestra di grazia: due schede che rinnovano insieme non sono
    // un furto
    if (Date.now() - salvato.usatoIl.getTime() < GRAZIA_MS && salvato.sostituitoDa) {
      return salvato.sostituitoDa
    }

    // Riuso vero: non si può sapere chi è il ladro → fuori entrambi
    await db.refreshToken.updateMany({
      where: { famiglia: salvato.famiglia, revocatoIl: null },
      data: { revocatoIl: new Date() },
    })
    registro.warn({ utenteId: salvato.utenteId, famiglia: salvato.famiglia }, 'riuso rilevato')
    throw new ErroreAutenticazione('refresh riutilizzato: sessione terminata')
  }

  const nuovo = await emettiRefresh(salvato.utenteId, salvato.famiglia)

  await db.refreshToken.update({
    where: { impronta: salvato.impronta },
    data: { usatoIl: new Date(), sostituitoDa: nuovo },
  })

  return nuovo
}
```

```typescript
// IL TEST CHE DIMOSTRA LA DIFESA
import { describe, it, expect } from 'vitest'

describe('rotazione dei refresh token', () => {
  it('un token usato due volte revoca tutta la famiglia', async () => {
    const r1 = await emettiRefresh(1n)
    const r2 = await ruota(r1) // il legittimo rinnova

    // L'attaccante aveva copiato r1 e prova a usarlo: oltre la
    // finestra di grazia è un riuso
    await new Promise((r) => setTimeout(r, 11_000))
    await expect(ruota(r1)).rejects.toThrow('riutilizzato')

    // ← LA VERIFICA CHE CONTA: anche il token del legittimo è morto
    await expect(ruota(r2)).rejects.toThrow('non valido')
  }, 20_000)

  it('due schede che rinnovano insieme ricevono lo stesso token', async () => {
    const r1 = await emettiRefresh(1n)
    const [a, b] = await Promise.all([ruota(r1), ruota(r1)])
    expect(a).toBe(b)
  })
})
```

---

### Esercizio 3 — Chiudere un IDOR

**Obiettivo:** un endpoint verifica il ruolo ma non la proprietà. Trovare tutte le occorrenze e correggerle in modo che l'errore non sia ripetibile.

```typescript
// IL CODICE DA CORREGGERE — tre endpoint, lo stesso difetto
app.get('/api/documenti/:id', richiedeRuolo('utente'), async (richiesta, risposta) => {
  risposta.json(await db.documento.findUnique({ where: { id: richiesta.params.id } }))
})

app.patch('/api/documenti/:id', richiedeRuolo('utente'), async (richiesta, risposta) => {
  risposta.json(
    await db.documento.update({ where: { id: richiesta.params.id }, data: richiesta.body }),
  )
})

app.delete('/api/documenti/:id', richiedeRuolo('utente'), async (richiesta, risposta) => {
  await db.documento.delete({ where: { id: richiesta.params.id } })
  risposta.status(204).end()
})
```

```
# LA DIAGNOSI
#   `richiedeRuolo('utente')` verifica che ci sia un utente
#   autenticato: è AUTENTICAZIONE travestita da autorizzazione.
#   Chiunque abbia un account legge, modifica e cancella i documenti
#   di chiunque altro cambiando l'id nell'URL.
#
#   La correzione ovvia — aggiungere `if (doc.proprietarioId !== …)`
#   in ogni handler — funziona finché qualcuno non aggiunge il quarto
#   endpoint e se ne dimentica. Serve una forma in cui dimenticarsene
#   sia difficile.
```

```typescript
// LA SOLUZIONE — la proprietà entra nella QUERY, e la query passa
// per un repository che non espone un modo di scriverla senza
export function repositoryDocumenti(utenteId: bigint) {
  // Il filtro è nel costruttore: non c'è un metodo che permetta di
  // saltarlo, e un endpoint nuovo lo eredita per costruzione
  const mio = { proprietarioId: utenteId }

  return {
    trova: (id: bigint) => db.documento.findFirst({ where: { id, ...mio } }),

    aggiorna: async (id: bigint, dati: AggiornamentoDocumento) => {
      // updateMany accetta un WHERE composto; update no. Zero righe
      // aggiornate significa "non esiste, o non è tuo": la stessa
      // risposta in entrambi i casi.
      const esito = await db.documento.updateMany({ where: { id, ...mio }, data: dati })
      return esito.count === 1
    },

    elimina: async (id: bigint) => {
      const esito = await db.documento.deleteMany({ where: { id, ...mio } })
      return esito.count === 1
    },
  }
}
```

```typescript
// Gli endpoint diventano tutti uguali, e il difetto non è
// riproducibile per distrazione
app.get('/api/documenti/:id', richiedeAutenticazione, async (richiesta, risposta) => {
  const documento = await repositoryDocumenti(richiesta.utente!.id).trova(
    BigInt(richiesta.params.id),
  )

  // 404 e non 403: un 403 confermerebbe che il documento esiste, e
  // permetterebbe di enumerare gli identificativi altrui
  if (!documento) throw new ErroreNonTrovato('Documento', richiesta.params.id)

  risposta.json(documento)
})
```

```
# IL TEST CHE DEVE ESISTERE PER OGNI RISORSA
#   1. l'utente A crea un documento
#   2. l'utente B, autenticato, chiede GET/PATCH/DELETE su quell'id
#   3. tutte e tre devono rispondere 404 — non 403, non 200
#   4. e il documento deve essere ancora lì, invariato
#
#   ⚠ Questo test va scritto UNA VOLTA e riusato per ogni risorsa:
#     è l'unico modo perché la copertura non dipenda dalla memoria
#     di chi aggiunge l'endpoint successivo.
```

---

## C2. Mini-progetto: sistema di autenticazione completo

L'esercizio chiave del modulo: registrazione, login, refresh token, ruoli utente e protezione delle rotte sul frontend e sul backend.

```
auth-completo/
├── prisma/schema.prisma      utenti · refresh_token · tentativi_login
├── src/
│   ├── auth/
│   │   ├── password.ts       argon2 + verifica con HIBP
│   │   ├── token.ts          firma e verifica dell'access token
│   │   ├── refresh.ts        emissione, rotazione, rilevamento riuso
│   │   └── sessione.ts       cookie, avvio e chiusura
│   ├── middleware/
│   │   ├── autenticazione.ts popola richiesta.utente, non blocca
│   │   ├── autorizzazione.ts richiedeAutenticazione · richiedeRuolo
│   │   ├── csrf.ts           double submit
│   │   └── limite-login.ts   per IP E per account
│   └── rotte/auth.ts         registrazione · login · refresh · logout
└── test/
    ├── autenticazione.test.ts
    └── autorizzazione.test.ts   il test IDOR riusabile

LE DECISIONI DI PROGETTO, E IL PERCHÉ
  access token in MEMORIA, refresh in cookie HttpOnly con
    path=/auth/refresh, SameSite=strict
  access di 10 minuti: la finestra di revoca accettata
  rotazione del refresh con famiglia e finestra di grazia di 10 s
  ruoli in una colonna array sull'utente, e un contatore di versione
    per invalidare i token quando i ruoli cambiano
  CSRF double-submit sugli endpoint che modificano lo stato
  limite di tentativi per IP e per ACCOUNT, con backoff crescente
```

```typescript
// src/middleware/autorizzazione.ts — il "negare per default" reso
// difficile da aggirare: il router protetto è un oggetto diverso
import { Router } from 'express'

export function routerProtetto(...ruoli: string[]): Router {
  const router = Router()
  router.use(richiedeAutenticazione)
  if (ruoli.length > 0) router.use(richiedeRuolo(...ruoli))
  return router
}

// L'uso: chi aggiunge una rotta al router protetto eredita il
// controllo; chi vuole una rotta pubblica deve dichiararlo
// esplicitamente su un router diverso
export const rotteAmministrazione = routerProtetto('admin')
export const rottePubbliche = Router()
```

```
# LA VERIFICA, IN ORDINE
# 1. LE PASSWORD  nel database nessun valore in chiaro, e l'hash
#    inizia con $argon2id$. La verifica costa 50-100 ms: misurala.
# 2. L'ENUMERAZIONE  login con email inesistente e con password
#    sbagliata → stesso stato, stesso corpo, tempi indistinguibili
# 3. IL FURTO DEL REFRESH  usa lo stesso token due volte oltre la
#    finestra di grazia → entrambe le parti fuori
# 4. LA REVOCA  cambia la password → tutte le sessioni e le famiglie
#    esistenti smettono di funzionare
# 5. L'IDOR  il test riusabile su ogni risorsa: 404 per l'utente B
# 6. IL CSRF  una POST da un'altra origine senza header → 403
# 7. I COOKIE  in DevTools: HttpOnly ✓ Secure ✓ SameSite ✓, e il
#    refresh NON viene inviato agli endpoint diversi da /auth/refresh
# 8. I LOG  cerca la password e i token nei log: zero occorrenze
# 9. IL LIMITE  venti login falliti sullo stesso account da IP
#    diversi → bloccato comunque
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Difendersi dalla forza bruta e dal credential stuffing

```
DUE ATTACCHI DIVERSI, DUE DIFESE DIVERSE
  FORZA BRUTA  molte password su UN account. Si ferma limitando i
    tentativi per ACCOUNT.
  CREDENTIAL STUFFING  una coppia email/password (rubata altrove)
    su MOLTI account, da molti IP. Il limite per account non lo
    vede: ogni account riceve un solo tentativo.

⚠ Limitare solo per IP non basta e fa danni: una rete aziendale
  dietro NAT condivide un indirizzo, e centinaia di utenti legittimi
  vengono bloccati insieme.
```

```typescript
// Il limite su DUE dimensioni, con backoff crescente per account
const SOGLIE = [
  { tentativi: 5, attesaSecondi: 60 },
  { tentativi: 10, attesaSecondi: 300 },
  { tentativi: 20, attesaSecondi: 3600 },
]

export async function consumaTentativo(ip: string, email: string): Promise<boolean> {
  const [perIp, perAccount] = await Promise.all([
    redis.incr(`login:ip:${ip}`),
    redis.incr(`login:acc:${email.toLowerCase()}`),
  ])

  await Promise.all([
    redis.expire(`login:ip:${ip}`, 3600),
    redis.expire(`login:acc:${email.toLowerCase()}`, 3600),
  ])

  // Il limite per IP è largo: deve fermare uno script, non una
  // rete aziendale
  if (perIp > 100) return false

  const soglia = SOGLIE.findLast((s) => perAccount >= s.tentativi)
  return soglia === undefined
}
```

```
LE DIFESE OLTRE AL CONTEGGIO
  · CAPTCHA dopo N fallimenti, non prima: prima è un costo per tutti
  · ritardo COSTANTE sulla risposta di login (300-500 ms), che
    nasconde anche le differenze di tempo fra i rami
  · notifica all'utente sui tentativi falliti e sugli accessi da
    dispositivi nuovi: è la difesa che l'utente può usare
  · MFA, che rende inefficace il credential stuffing anche quando la
    password è corretta
  · confronto con gli elenchi di password compromesse: impedisce che
    la credenziale rubata sia riutilizzabile in partenza
```

---

## D2. Reimpostazione della password fatta bene

```
IL FLUSSO, CON I CONTROLLI CHE CONTANO
  1. l'utente chiede la reimpostazione per un'email
  2. la risposta è SEMPRE la stessa, esista o no l'indirizzo:
     "se l'indirizzo è registrato, riceverai un messaggio"
  3. si genera un token casuale di 32 byte, se ne salva l'HASH con
     scadenza di 15-30 minuti, e si invia il token in chiaro SOLO
     nell'email
  4. alla reimpostazione: il token è verificato, MONOUSO, e viene
     eliminato subito
  5. si invalidano TUTTE le sessioni e le famiglie di refresh
  6. si notifica l'utente che la password è cambiata

⚠ QUATTRO ERRORI RICORRENTI
  · il token nella query string finisce nei log del server e nel
    referrer verso i siti esterni → meglio nel frammento, o in un
    POST subito dopo l'apertura
  · il token salvato in chiaro: chi legge il database reimposta le
    password di tutti
  · nessuna scadenza, o token riutilizzabile
  · non invalidare le sessioni: chi aveva rubato l'account resta
    dentro anche dopo che la vittima ha cambiato la password
```

---

## D3. Autenticazione fra servizi

```
NON SI USANO CREDENZIALI UTENTE FRA SERVIZI: nessun servizio deve
poter agire "come l'amministratore".

LE TRE OPZIONI, IN ORDINE DI ROBUSTEZZA
  CHIAVE API  semplice, e sufficiente dentro una rete privata.
    Va conservata come hash, ruotabile senza interruzione (due
    chiavi valide contemporaneamente durante la rotazione) e legata
    a permessi ristretti.
  CLIENT CREDENTIALS (OAuth 2.1)  il servizio ottiene un token
    breve dall'authorization server con il proprio identificativo e
    segreto. Scadenza e scope inclusi.
  mTLS  entrambe le parti presentano un certificato. È l'unica che
    autentica anche il SERVER verso il client, e non ha segreti da
    trasmettere. Costo: gestire una PKI e la rotazione.

⚠ LA PROPAGAZIONE DELL'IDENTITÀ UTENTE fra servizi non si fa
  inoltrando il token dell'utente ovunque: ogni servizio che lo
  riceve può impersonarlo. Si usa token exchange (RFC 8693), oppure
  si passa l'identità come dato firmato con un pubblico ristretto.
```

---

## D4. Multi-tenancy e SSO aziendale

```
IL REQUISITO CHE ARRIVA CON IL PRIMO CLIENTE GRANDE: "vogliamo che i
nostri dipendenti accedano con il nostro identity provider". Da lì
in poi l'autenticazione non è più una sola.

  · ogni tenant ha un metodo di accesso proprio: password, OIDC
    verso il suo IdP, o SAML per quelli più vecchi
  · l'utente digita l'email, il sistema riconosce il DOMINIO e lo
    instrada al metodo giusto (home realm discovery)
  · ⚠ il dominio va VERIFICATO (record DNS) prima di associarlo a un
    tenant: senza, chiunque registri un tenant può dirottare gli
    accessi di quel dominio
  · SCIM per il provisioning: quando l'azienda licenzia qualcuno,
    l'accesso deve sparire senza che nessuno lo faccia a mano
  · un utente può appartenere a più tenant: l'identità è una, le
    autorizzazioni sono per tenant

SAML si incontra ancora spesso nelle aziende. È XML e ha una
superficie di attacco sgradevole (XML signature wrapping, entità
esterne): non lo si implementa a mano, si usa una libreria mantenuta
e si verifica la firma sull'assertion, non solo sulla risposta.
```

---

## D5. Cosa registrare, e cosa non registrare mai

```
DA REGISTRARE SEMPRE
  · accessi riusciti e falliti, con IP, user agent e istante
  · cambi di password, email e MFA
  · assegnazione o revoca di ruoli, con CHI l'ha fatta
  · riuso di refresh token rilevato
  · accessi negati a risorse altrui (i tentativi di IDOR)
  · uso e revoca delle chiavi API

DA NON REGISTRARE MAI
  ❌ password, nemmeno hashate, nemmeno nei tentativi falliti
  ❌ token di qualunque tipo, interi o parziali
  ❌ segreti TOTP, codici di recupero
  ❌ il corpo completo delle richieste di autenticazione
  ❌ i cookie e l'header Authorization

⚠ La redazione va configurata nel logger, non lasciata alla
  disciplina di chi scrive le chiamate. Con pino:
    redact: ['req.headers.authorization', 'req.headers.cookie',
             'req.body.password', 'req.body.token', '*.passwordHash']
  E poi si verifica: `grep` della password di prova nei log dopo un
  test di login deve dare zero risultati.
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
AUTENTICAZIONE E AUTORIZZAZIONE — Mappa dei concetti

I DUE CONCETTI
├── autenticazione = chi sei → 401 → il client mostra il login
├── autorizzazione = cosa puoi fare → 403 → il client mostra un
│     messaggio; rifare il login non serve
└── MFA = fattori di CATEGORIE diverse (sai · hai · sei)

PASSWORD
├── argon2id (19 MiB, t=2) o scrypt; mai SHA, mai MD5, mai cifratura
├── il salt ferma le rainbow table, il COSTO ferma la forza bruta
├── parametri tarati su 50-100 ms sul tuo hardware
└── minimo 8-12, massimo ≥64, confronto con HIBP, niente scadenze
      periodiche né regole di composizione

SESSIONI
├── cookie HttpOnly + Secure + SameSite, path e domain ristretti
├── rigenerare l'id al login (session fixation)
├── il logout ELIMINA la sessione dall'archivio, non solo il cookie
└── CSRF: SameSite + token double-submit + verifica dell'origine

JWT
├── il payload è CODIFICATO, non cifrato: nessun dato sensibile
├── verificare SEMPRE alg (lista chiusa), iss, aud, exp
├── le tre vulnerabilità storiche: alg:none, confusione HS/RS, kid
└── access breve in MEMORIA + refresh in cookie HttpOnly

REFRESH TOKEN
├── nel database si salva l'IMPRONTA, non il token
├── rotazione a ogni uso, con famiglia condivisa
├── il riuso revoca l'INTERA famiglia
└── finestra di grazia + deduplica lato client contro i falsi positivi

OAUTH 2.1 E OIDC
├── OAuth = delega di autorizzazione, NON autenticazione
├── resta solo authorization code + PKCE (S256), per tutti i client
├── verificare state, redirect_uri ESATTO, codice monouso
├── OIDC aggiunge l'ID token: si valida nel CLIENT, non si manda all'API
└── collegare gli account solo su email VERIFICATA

AUTORIZZAZIONE
├── RBAC per le sezioni, controllo di PROPRIETÀ sulla risorsa
├── la proprietà entra nella QUERY, non in un `if` successivo
├── 404 invece di 403 per non confermare l'esistenza
└── negare per default · sul server · vicino al dato · in un posto solo

MFA E REVOCA
├── TOTP: codice monouso, limite di tentativi, codici di recupero
├── passkey: nessun segreto condiviso, immuni al phishing
├── revoca: access brevi · denylist · contatore di versione · opachi
└── immediata su cambio password, sospensione, revoca di privilegi

PRODUZIONE
├── limite di tentativi per IP E per account, con backoff
├── reimpostazione: token hashato, monouso, scadenza, invalida tutto
├── fra servizi: chiave API, client credentials, o mTLS
└── log: gli eventi sì, le credenziali mai — con redazione verificata
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Distingui autenticazione e autorizzazione, e sai quale stato HTTP usare
- [ ] Sai perché SHA-256 è la scelta sbagliata per le password
- [ ] Sai cosa fa il salt e cosa fa il costo di calcolo, separatamente
- [ ] Sai tarare i parametri di argon2 sul tuo hardware
- [ ] Conosci i flag di un cookie di sessione e cosa protegge ciascuno
- [ ] Sai cos'è la session fixation e perché il logout deve toccare il server
- [ ] Sai spiegare un attacco CSRF e le tre difese
- [ ] Sai perché un'API con `Authorization: Bearer` non è vulnerabile a CSRF
- [ ] Sai che il payload di un JWT è leggibile da chiunque
- [ ] Verifichi `alg`, `iss`, `aud` ed `exp`, e sai perché la lista di algoritmi va chiusa

**Parte B — Comprensione**

- [ ] Scegli fra sessioni e token con una motivazione, non per abitudine
- [ ] Sai perché l'access token va in memoria e il refresh in un cookie
- [ ] Sai perché `localStorage` trasforma un XSS in una compromissione
- [ ] Implementi la rotazione con famiglia e rilevamento del riuso
- [ ] Sai perché serve una finestra di grazia, e cosa succede senza
- [ ] Sai quali flussi OAuth 2.1 ha rimosso e perché
- [ ] Sai a cosa serve PKCE e perché `plain` non basta
- [ ] Verifichi `state` e il `redirect_uri` esatto
- [ ] Distingui ID token e access token e sai dove va ciascuno
- [ ] Sai perché collegare gli account su email non verificata è pericoloso
- [ ] Metti il controllo di proprietà nella query e rispondi 404
- [ ] Conosci le tre lacune tipiche di un TOTP e perché le passkey chiudono il phishing
- [ ] Conosci le quattro strategie di revoca e i loro costi

**Parte C — Pratica**

- [ ] Hai trovato tutti e otto i difetti dell'endpoint di login
- [ ] Hai reso indistinguibili nel tempo il caso "email inesistente" e "password errata"
- [ ] Hai dimostrato con un test che il riuso di un refresh revoca la famiglia
- [ ] Hai chiuso l'IDOR in una forma che un endpoint nuovo eredita
- [ ] Hai scritto il test IDOR riusabile e lo hai applicato a ogni risorsa

**Parte D — Esperto**

- [ ] Distingui forza bruta e credential stuffing, e limiti su due dimensioni
- [ ] Sai perché limitare solo per IP fa danni
- [ ] Progetti una reimpostazione password con token hashato e monouso
- [ ] Sai perché la reimpostazione deve invalidare tutte le sessioni
- [ ] Conosci le tre opzioni di autenticazione fra servizi
- [ ] Sai perché inoltrare il token dell'utente fra servizi è pericoloso
- [ ] Sai perché il dominio di un tenant va verificato prima di associarlo
- [ ] Configuri la redazione dei log e VERIFICHI che funzioni

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Password con SHA-256 o MD5 | Funzioni veloci: miliardi di tentativi al secondo su GPU | `argon2id`, o `scrypt` |
| Confronto dell'hash con `===` | Attacco a tempo: la password si ricostruisce | `argon2.verify`, o `timingSafeEqual` |
| 404 su email non registrata | Enumerazione degli account | Stesso stato, stesso corpo, stesso tempo |
| Token in `localStorage` | Un XSS in qualunque dipendenza li ruba | Access in memoria, refresh in cookie HttpOnly |
| Cookie senza `HttpOnly`/`Secure`/`SameSite` | Furto via XSS, intercettazione, CSRF | Tutti e tre, sempre |
| Non rigenerare l'id di sessione al login | Session fixation | Distruggere la sessione anonima e crearne una nuova |
| Logout che cancella solo il cookie | La sessione resta valida sul server | Eliminarla dall'archivio |
| JWT senza `exp`, `iss`, `aud` | Token eterni, o accettati da un altro sistema | Impostarli e verificarli tutti |
| Accettare l'algoritmo dichiarato nel token | `alg:none`, confusione HS256/RS256 | `algorithms: ['…']` esplicito |
| Dati sensibili nel payload del JWT | Il payload è leggibile da chiunque | Solo identificativi e claim pubblici |
| Refresh token salvato in chiaro | Chi legge la tabella ha credenziali usabili | Salvare l'impronta SHA-256 |
| Refresh senza rotazione | Un token rubato vale per settimane, senza segnali | Rotazione con famiglia e rilevamento del riuso |
| Flusso implicit o password grant | Rimossi da OAuth 2.1: non si possono rendere sicuri | Authorization code + PKCE |
| `redirect_uri` confrontato con `startsWith` | `https://sito.it.attaccante.example` passa | Confronto esatto con la lista registrata |
| ID token usato come access token | L'API accetta un token emesso per un altro destinatario | Access token all'API, ID token nel client |
| Collegare gli account sull'email non verificata | Si rivendica l'indirizzo altrui | Solo su `email_verified`, meglio con conferma |
| Ruolo verificato, proprietà no | IDOR: si legge tutto cambiando l'id nell'URL | La proprietà nella query, risposta 404 |
| Autorizzazione solo nel frontend | La richiesta si costruisce a mano in dieci secondi | Sul server, sempre |
| Limite di tentativi solo per IP | Il credential stuffing passa; il NAT aziendale viene bloccato | Per IP e per account, con backoff |
| Reimpostazione che non invalida le sessioni | Chi aveva rubato l'account resta dentro | Revocare sessioni e famiglie di refresh |
| Token dell'utente inoltrato fra servizi | Ogni servizio può impersonarlo | Token exchange, o identità firmata |
| Credenziali nei log | Un incidente permanente, e spesso non rilevato | Redazione configurata nel logger, e verificata |

---

## Troubleshooting rapido

**L'utente viene disconnesso a caso**
- Causa: rotazione del refresh senza deduplica lato client — due schede rinnovano insieme e il riuso scatta
- Fix: deduplicare il rinnovo; finestra di grazia di pochi secondi

**Il cookie di sessione non arriva al server**
- Causa: `Secure` senza HTTPS, dominio o percorso sbagliati, oppure `SameSite=Strict` con arrivo da un link esterno
- Fix: verificare i tre attributi in DevTools; `Lax` se l'arrivo esterno deve funzionare

**Il login funziona in locale e non in produzione**
- Causa: cookie cross-site senza `SameSite=None; Secure`, o frontend e API su domini diversi senza `credentials: 'include'` e CORS con `credentials: true`
- Fix: allineare CORS, `credentials` e gli attributi del cookie

**`JWTExpired` subito dopo l'emissione**
- Causa: orologi sfasati fra chi firma e chi verifica
- Fix: `clockTolerance` di 30 s, e sincronizzare gli orologi (NTP)

**La verifica della firma fallisce dopo una rotazione delle chiavi**
- Causa: JWKS in cache troppo a lungo, o `kid` non usato per scegliere la chiave
- Fix: `createRemoteJWKSet` con cache breve; selezionare la chiave dal `kid`

**Ogni richiesta riceve 403 dopo aver aggiunto il CSRF**
- Causa: il client non rimanda il token nell'header, oppure il cookie del token è `httpOnly`
- Fix: il cookie del token CSRF NON è httpOnly; il client lo legge e lo copia nell'header

**Il login è lentissimo sotto carico**
- Causa: i parametri di argon2 sono troppo alti per il numero di login al secondo
- Fix: misurare, e ridurre `memoryCost`/`timeCost` restando sopra i minimi OWASP

**Un utente sospeso continua ad accedere**
- Causa: access token ancora valido, e nessun controllo di revoca
- Fix: token brevi; contatore di versione confrontato a ogni richiesta

**Il flusso OAuth torna con `invalid_grant`**
- Causa: codice già usato o scaduto, `redirect_uri` diverso da quello della prima chiamata, o `code_verifier` sbagliato
- Fix: il codice è monouso; il `redirect_uri` deve essere identico in entrambe le chiamate

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_14_sicurezza_web.md` | XSS, CSP e il resto della OWASP Top 10: il contesto in cui questi token vivono |
| `tutorial_15_testing_web.md` | Come si testa l'autenticazione senza rendere i test fragili |
| `tutorial_12_database_web.md` | Row-Level Security, che porta l'autorizzazione dentro il database |
| `tutorial_22_rate_limiting_edge.md` | Gli algoritmi dietro il limite sui tentativi di login |
| `tutorial_23_websocket_security.md` | Autenticare una connessione che non porta header a ogni messaggio |
| `tutorial_25_nextjs.md` | Sessioni e middleware in un'applicazione con rendering sul server |

---

## Risorse di riferimento

**Specifiche:** [RFC 9700 — Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700.html) · [OAuth 2.1 (draft)](https://oauth.net/2.1/) · [RFC 7636 — PKCE](https://www.rfc-editor.org/rfc/rfc7636.html) · [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html) · [RFC 6238 — TOTP](https://www.rfc-editor.org/rfc/rfc6238.html) · [WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/)

**Guide:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) — in particolare *Authentication*, *Password Storage*, *Session Management* e *Cross-Site Request Forgery Prevention* · [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/), il capitolo 2 come lista di controllo · [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html), l'origine delle raccomandazioni moderne sulle password

**Strumenti:** [jose](https://github.com/panva/jose) per JWT e JWKS · [argon2](https://github.com/ranisalt/node-argon2) · [SimpleWebAuthn](https://simplewebauthn.dev/) per le passkey · [Have I Been Pwned — Passwords](https://haveibeenpwned.com/API/v3#PwnedPasswords) con k-anonymity

---

> **Fine del Tutorial 13 — Autenticazione e Autorizzazione**
>
> Prossimo tutorial: `tutorial_14_sicurezza_web.md`
