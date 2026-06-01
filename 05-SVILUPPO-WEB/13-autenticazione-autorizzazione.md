---
corso: "Sviluppo Web"
fase: "5 — Sicurezza"
modulo: "13"
titolo: "Autenticazione e Autorizzazione"
versione: "JWT / OAuth 2.0 / OIDC / Passkeys"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "10 — Node.js"
  - "14 — Sicurezza Web"
obiettivi:
  - "Implementare autenticazione con JWT, session e cookie sicuri"
  - "Integrare OAuth 2.0 e OpenID Connect con provider esterni"
  - "Gestire autorizzazione con RBAC e ABAC"
  - "Implementare Passkeys/WebAuthn per autenticazione passwordless"
  - "Proteggere token con rotation, revocation e secure storage"
  - "Configurare MFA e account recovery"
tag: [autenticazione, autorizzazione, JWT, OAuth2, OIDC, RBAC, Passkeys, WebAuthn]
---

# Autenticazione e Autorizzazione nelle Applicazioni Web

> **Modulo 13** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Node.js](10-nodejs.md), [Sicurezza Web](14-sicurezza-web.md)
>
> Al termine di questo modulo saprai:
> 1. Implementare autenticazione con JWT, session e cookie sicuri
> 2. Integrare OAuth 2.0 e OpenID Connect con provider esterni
> 3. Gestire autorizzazione con RBAC e ABAC
> 4. Implementare Passkeys/WebAuthn per autenticazione passwordless
> 5. Proteggere token con rotation, revocation e secure storage
> 6. Configurare MFA e account recovery
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **httpOnly + Secure + SameSite=Lax cookie per session token.** No localStorage.
2. **Refresh token rotation: ogni use, vecchio invalidato.** Detection theft.
3. **OAuth 2.1 (RFC 9700) deprecates implicit; auth code + PKCE always.**
4. **WebAuthn passkey > password.** Modern auth standard.
5. **Server-side session > pure JWT per revocation immediata.**


## Panoramica

La sicurezza delle applicazioni web si fonda su due pilastri distinti ma complementari: **autenticazione** (Authentication, AuthN) e **autorizzazione** (Authorization, AuthZ). Confondere questi due concetti è uno degli errori più comuni tra gli sviluppatori, eppure la distinzione è fondamentale per progettare sistemi sicuri.

**Autenticazione (AuthN)** risponde alla domanda: *"Chi sei?"*. È il processo di verifica dell'identità di un utente o di un sistema. Quando inserisci username e password in un form di login, stai attraversando un processo di autenticazione. Il sistema verifica che le credenziali corrispondano a un'identità nota e, in caso affermativo, ti riconosce come quell'utente.

**Autorizzazione (AuthZ)** risponde alla domanda: *"Cosa puoi fare?"*. Una volta stabilita l'identità, l'autorizzazione determina quali risorse e operazioni sono accessibili. Un utente autenticato come "Mario Rossi" potrebbe avere il permesso di leggere documenti ma non di cancellarli, oppure potrebbe accedere alla sezione admin se possiede il ruolo di amministratore.

La sequenza è sempre la stessa: prima l'autenticazione, poi l'autorizzazione. Non puoi determinare i permessi di qualcuno se non sai chi è. In un'applicazione web moderna, questi meccanismi si manifestano attraverso diversi pattern architetturali: sessioni server-side, token JWT, protocolli OAuth 2.0 e OpenID Connect, ciascuno con i propri vantaggi e compromessi.

```
┌─────────────────────────────────────────────────┐
│              Flusso di Sicurezza                │
│                                                 │
│  Utente ──► Autenticazione ──► Autorizzazione   │
│  (Chi?)       (Verifica)        (Permessi)      │
│                                                 │
│  Metodi AuthN:          Metodi AuthZ:           │
│  - Password             - RBAC (ruoli)          │
│  - Token JWT            - ABAC (attributi)      │
│  - OAuth 2.0            - Permission-based      │
│  - Certificati          - Policy-based          │
│  - Biometria            - ACL                   │
└─────────────────────────────────────────────────┘
```

---

## Autenticazione Session-Based

L'autenticazione basata su sessioni è il metodo più tradizionale e ancora oggi ampiamente utilizzato, specialmente nelle applicazioni server-rendered. Il principio è semplice: dopo un login riuscito, il server crea una sessione e invia al browser un cookie contenente l'identificativo di tale sessione.

### Come Funzionano i Cookie di Sessione

Quando un utente effettua il login, il server genera un **session ID** univoco, lo memorizza in uno store lato server (memoria, database, Redis) e lo invia al client tramite l'header `Set-Cookie`. Ad ogni richiesta successiva, il browser include automaticamente il cookie, permettendo al server di identificare l'utente.

```
┌──────────┐                        ┌──────────┐
│  Browser │  POST /login            │  Server  │
│          │  {email, password}      │          │
│          │ ──────────────────────► │          │
│          │                         │ Verifica │
│          │  Set-Cookie: sid=abc123 │ credenz. │
│          │ ◄────────────────────── │ Crea     │
│          │                         │ sessione │
│          │  GET /dashboard         │          │
│          │  Cookie: sid=abc123     │          │
│          │ ──────────────────────► │ Recupera │
│          │                         │ sessione │
│          │  200 OK (dati utente)   │          │
│          │ ◄────────────────────── │          │
└──────────┘                        └──────────┘
```

### Implementazione con express-session

Il middleware `express-session` è lo standard de facto per la gestione delle sessioni in Node.js con Express:

```javascript
const express = require('express');
const session = require('express-session');
const RedisStore = require('connect-redis').default;
const { createClient } = require('redis');

const app = express();

// Client Redis per lo storage delle sessioni
const redisClient = createClient({ url: 'redis://localhost:6379' });
redisClient.connect();

app.use(session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET,       // Chiave per firmare il cookie
  name: '__Host-sid',                        // Nome personalizzato del cookie
  resave: false,                             // Non risalvare sessioni invariate
  saveUninitialized: false,                  // Non creare sessioni vuote
  cookie: {
    secure: true,                            // Solo HTTPS
    httpOnly: true,                          // Non accessibile da JavaScript
    sameSite: 'lax',                         // Protezione CSRF base
    maxAge: 1000 * 60 * 60 * 24,            // Scadenza: 24 ore
    domain: 'example.com',                   // Dominio di appartenenza
    path: '/'                                // Path di validità
  }
}));

// Endpoint di login
app.post('/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await findUserByEmail(email);

  if (!user || !await verifyPassword(password, user.passwordHash)) {
    return res.status(401).json({ error: 'Credenziali non valide' });
  }

  // Rigenerare l'ID sessione dopo il login (prevenzione session fixation)
  req.session.regenerate((err) => {
    if (err) return res.status(500).json({ error: 'Errore interno' });

    req.session.userId = user.id;
    req.session.role = user.role;
    req.session.loginAt = Date.now();

    req.session.save((err) => {
      if (err) return res.status(500).json({ error: 'Errore interno' });
      res.json({ message: 'Login effettuato', user: { id: user.id, name: user.name } });
    });
  });
});

// Middleware di autenticazione
function requireAuth(req, res, next) {
  if (!req.session.userId) {
    return res.status(401).json({ error: 'Autenticazione richiesta' });
  }
  next();
}

// Endpoint di logout
app.post('/logout', requireAuth, (req, res) => {
  req.session.destroy((err) => {
    if (err) return res.status(500).json({ error: 'Errore durante il logout' });
    res.clearCookie('__Host-sid');
    res.json({ message: 'Logout effettuato' });
  });
});
```

### Flag di Sicurezza dei Cookie

Ogni flag del cookie ha un ruolo preciso nella difesa dell'applicazione:

| Flag | Valore | Scopo |
|------|--------|-------|
| `secure` | `true` | Il cookie viene trasmesso solo su connessioni HTTPS |
| `httpOnly` | `true` | Impedisce l'accesso al cookie tramite `document.cookie` (difesa XSS) |
| `sameSite` | `'strict'` o `'lax'` | Controlla l'invio del cookie nelle richieste cross-origin |
| `domain` | `'example.com'` | Limita il cookie al dominio specificato |
| `path` | `'/'` | Limita il cookie al percorso specificato |
| `maxAge` | millisecondi | Durata del cookie; assenza = cookie di sessione (dura fino alla chiusura del browser) |

Il prefisso `__Host-` nel nome del cookie è una misura di sicurezza aggiuntiva: garantisce che il cookie sia `secure`, che non abbia un attributo `domain` e che il `path` sia `/`, prevenendo attacchi di cookie injection da sottodomini.

### Protezione CSRF

L'attacco **Cross-Site Request Forgery** (CSRF) sfrutta il fatto che il browser invia automaticamente i cookie con ogni richiesta al dominio corrispondente. Un sito malevolo potrebbe indurre il browser dell'utente a inviare una richiesta autenticata all'applicazione target senza che l'utente ne sia consapevole.

```javascript
const csrf = require('csurf');
const cookieParser = require('cookie-parser');

app.use(cookieParser());

// Middleware CSRF con double-submit cookie pattern
const csrfProtection = csrf({
  cookie: {
    httpOnly: true,
    secure: true,
    sameSite: 'strict'
  }
});

// Endpoint per ottenere il token CSRF
app.get('/csrf-token', csrfProtection, (req, res) => {
  res.json({ csrfToken: req.csrfToken() });
});

// Le richieste POST/PUT/DELETE richiedono il token CSRF
app.post('/transfer', csrfProtection, requireAuth, (req, res) => {
  // Il middleware csrf verifica automaticamente il token
  // presente nell'header X-CSRF-Token o nel body _csrf
  processTransfer(req.body);
  res.json({ success: true });
});
```

La combinazione `sameSite: 'lax'` nei cookie di sessione riduce significativamente la superficie di attacco CSRF. Con `sameSite: 'strict'`, i cookie non vengono mai inviati in richieste cross-site, ma questo può causare problemi di usabilità (ad esempio, cliccando un link da un'email si perde la sessione).

---

## JSON Web Token (JWT)

I JWT rappresentano un approccio stateless all'autenticazione: tutta l'informazione necessaria è contenuta nel token stesso, eliminando la necessità di consultare un database di sessioni ad ogni richiesta.

### Struttura del JWT

Un JWT è composto da tre parti separate da punti: `header.payload.signature`.

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ik1hcmlvIFJvc3NpIiwicm9sZSI6ImFkbWluIiwiaWF0IjoxNjk5MDAwMDAwLCJleHAiOjE2OTkwMDM2MDB9.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Header** — Specifica l'algoritmo di firma e il tipo di token:
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload** — Contiene i claims (dichiarazioni) sull'utente e metadati:
```json
{
  "sub": "1234567890",
  "name": "Mario Rossi",
  "role": "admin",
  "iat": 1699000000,
  "exp": 1699003600
}
```

I claims standard includono `sub` (subject), `iat` (issued at), `exp` (expiration), `iss` (issuer), `aud` (audience) e `jti` (JWT ID).

**Signature** — Garantisce l'integrità del token:
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

### HS256 vs RS256

La scelta dell'algoritmo di firma influenza profondamente l'architettura del sistema:

**HS256 (HMAC + SHA-256)** utilizza una chiave simmetrica: la stessa chiave firma e verifica il token. È semplice e performante, ma richiede che ogni servizio che deve verificare il token possieda la chiave segreta. Adatto a sistemi monolitici o microservizi con un singolo emittente.

**RS256 (RSA + SHA-256)** utilizza una coppia di chiavi asimmetriche: la chiave privata firma, la chiave pubblica verifica. Qualsiasi servizio può verificare i token senza possedere la chiave privata. Ideale per architetture distribuite e scenari multi-tenant.

```javascript
const jwt = require('jsonwebtoken');
const fs = require('fs');

// HS256 — chiave simmetrica
const symmetricToken = jwt.sign(
  { sub: userId, role: 'admin' },
  process.env.JWT_SECRET,
  { algorithm: 'HS256', expiresIn: '15m' }
);

// RS256 — chiave asimmetrica
const privateKey = fs.readFileSync('./keys/private.pem');
const asymmetricToken = jwt.sign(
  { sub: userId, role: 'admin' },
  privateKey,
  { algorithm: 'RS256', expiresIn: '15m', issuer: 'auth.example.com' }
);

// Verifica con chiave pubblica (qualsiasi servizio può farlo)
const publicKey = fs.readFileSync('./keys/public.pem');
const decoded = jwt.verify(asymmetricToken, publicKey, {
  algorithms: ['RS256'],
  issuer: 'auth.example.com'
});
```

### Pattern Access Token + Refresh Token

Un singolo token di lunga durata è un rischio: se compromesso, un attaccante ha accesso prolungato. Il pattern a doppio token mitiga questo rischio:

- **Access Token**: breve durata (5-15 minuti), usato per autenticare le richieste API
- **Refresh Token**: lunga durata (giorni/settimane), usato esclusivamente per ottenere nuovi access token

```javascript
// Generazione della coppia di token al login
function generateTokenPair(user) {
  const accessToken = jwt.sign(
    { sub: user.id, role: user.role, type: 'access' },
    process.env.JWT_SECRET,
    { expiresIn: '15m' }
  );

  const refreshToken = jwt.sign(
    { sub: user.id, type: 'refresh', jti: generateUniqueId() },
    process.env.REFRESH_SECRET,
    { expiresIn: '7d' }
  );

  // Salvare il refresh token nel database per poterlo revocare
  storeRefreshToken(user.id, refreshToken);

  return { accessToken, refreshToken };
}

// Endpoint di refresh
app.post('/auth/refresh', async (req, res) => {
  const { refreshToken } = req.body;

  try {
    const decoded = jwt.verify(refreshToken, process.env.REFRESH_SECRET);

    // Verificare che il refresh token esista nel database (non revocato)
    const storedToken = await findRefreshToken(decoded.jti);
    if (!storedToken) {
      return res.status(401).json({ error: 'Token revocato' });
    }

    const user = await findUserById(decoded.sub);

    // Rotation: invalidare il vecchio refresh token ed emetterne uno nuovo
    await revokeRefreshToken(decoded.jti);
    const newTokens = generateTokenPair(user);

    res.json(newTokens);
  } catch (error) {
    res.status(401).json({ error: 'Refresh token non valido' });
  }
});
```

### Storage dei Token nel Browser

Dove memorizzare i token nel browser è una decisione di sicurezza critica:

**localStorage** — Persistente, sopravvive alla chiusura del browser. Vulnerabile ad attacchi XSS: qualsiasi script malevolo può leggere `localStorage.getItem('token')`. Sconsigliato per access token.

**sessionStorage** — Simile a localStorage ma limitato alla tab corrente. Stessa vulnerabilità XSS, ma il token non persiste.

**Cookie httpOnly** — Non accessibile da JavaScript, quindi immune a XSS. Richiede protezione CSRF. Questo è l'approccio raccomandato: il server imposta l'access token in un cookie `httpOnly`, `secure`, `sameSite`.

**In memoria (variabile JavaScript)** — Il più sicuro contro XSS e CSRF, ma si perde al refresh della pagina. Combinato con un refresh token in cookie `httpOnly`, offre il miglior compromesso.

```javascript
// Approccio raccomandato: access token in memoria, refresh token in cookie httpOnly
app.post('/auth/login', async (req, res) => {
  const user = await authenticateUser(req.body);
  const { accessToken, refreshToken } = generateTokenPair(user);

  // Refresh token in cookie httpOnly
  res.cookie('refreshToken', refreshToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 7 * 24 * 60 * 60 * 1000,   // 7 giorni
    path: '/auth/refresh'                // Accessibile solo dall'endpoint refresh
  });

  // Access token nel body della risposta (il client lo terrà in memoria)
  res.json({ accessToken, user: { id: user.id, name: user.name } });
});
```

### Refresh Token Rotation

La rotation dei refresh token è una difesa contro il furto dei token. Ogni volta che un refresh token viene utilizzato, ne viene emesso uno nuovo e il vecchio viene invalidato. Se un attaccante tenta di usare un refresh token già utilizzato (rubato), il sistema rileva l'anomalia e invalida l'intera famiglia di token:

```javascript
async function handleRefreshRotation(oldTokenJti, userId) {
  const tokenFamily = await getTokenFamily(oldTokenJti);

  // Se il token è già stato usato, qualcuno ha rubato la catena
  if (tokenFamily.used) {
    // Revocare TUTTA la famiglia di token
    await revokeTokenFamily(tokenFamily.familyId);
    throw new Error('Rilevato riutilizzo del refresh token — famiglia revocata');
  }

  // Marcare il token corrente come usato
  await markTokenAsUsed(oldTokenJti);

  // Generare nuovo refresh token nella stessa famiglia
  const newRefreshToken = jwt.sign(
    { sub: userId, type: 'refresh', jti: generateUniqueId(), family: tokenFamily.familyId },
    process.env.REFRESH_SECRET,
    { expiresIn: '7d' }
  );

  await storeRefreshToken(userId, newRefreshToken, tokenFamily.familyId);
  return newRefreshToken;
}
```

---

## OAuth 2.0

OAuth 2.0 è un framework di autorizzazione che permette ad applicazioni di terze parti di ottenere accesso limitato alle risorse di un utente senza condividere le sue credenziali. Non è un protocollo di autenticazione di per sé, ma un framework di delega dell'autorizzazione.

### Ruoli in OAuth 2.0

| Ruolo | Descrizione | Esempio |
|-------|-------------|---------|
| **Resource Owner** | L'utente che possiede i dati | L'utente con un account Google |
| **Client** | L'applicazione che richiede accesso | La tua web app |
| **Authorization Server** | Emette i token dopo l'autenticazione | Google OAuth Server |
| **Resource Server** | Ospita le risorse protette | Google API (Calendar, Drive) |

### Grant Types

#### Authorization Code + PKCE

Il grant type più sicuro, raccomandato per tutte le applicazioni client-facing (SPA, mobile, server-side). PKCE (Proof Key for Code Exchange) aggiunge una protezione contro l'intercettazione del codice di autorizzazione.

```
┌──────────┐                                    ┌──────────────────┐
│  Browser  │                                    │ Authorization    │
│  (Client) │                                    │ Server           │
│           │                                    │                  │
│  1. Genera code_verifier (random)              │                  │
│     code_challenge = SHA256(code_verifier)      │                  │
│           │                                    │                  │
│  2. GET /authorize?                            │                  │
│     response_type=code&                        │                  │
│     client_id=xxx&                             │                  │
│     redirect_uri=xxx&                          │                  │
│     scope=openid profile&                      │                  │
│     code_challenge=xxx&                        │                  │
│     code_challenge_method=S256&                │                  │
│     state=random_state                         │                  │
│           │ ─────────────────────────────────► │                  │
│           │                                    │ 3. Utente si     │
│           │                                    │    autentica e   │
│           │                                    │    autorizza     │
│           │ ◄───────────────────────────────── │                  │
│  4. Redirect a redirect_uri?code=xxx&state=xxx │                  │
│           │                                    │                  │
│  5. POST /token                                │                  │
│     grant_type=authorization_code&             │                  │
│     code=xxx&                                  │                  │
│     code_verifier=original_verifier            │                  │
│           │ ─────────────────────────────────► │                  │
│           │                                    │ 6. Verifica      │
│           │                                    │    SHA256(verif.) │
│           │                                    │    == challenge   │
│           │ ◄───────────────────────────────── │                  │
│  7. { access_token, refresh_token, id_token }  │                  │
└──────────┘                                    └──────────────────┘
```

#### Client Credentials

Per la comunicazione machine-to-machine dove non c'è un utente coinvolto. Il client si autentica direttamente con le proprie credenziali:

```javascript
// Esempio: un microservizio che accede a un altro microservizio
const response = await fetch('https://auth.example.com/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: process.env.SERVICE_CLIENT_ID,
    client_secret: process.env.SERVICE_CLIENT_SECRET,
    scope: 'api:read api:write'
  })
});

const { access_token } = await response.json();
```

#### Device Code

Per dispositivi con input limitato (Smart TV, console, IoT). L'utente autorizza il dispositivo tramite un browser su un altro dispositivo:

```javascript
// 1. Il dispositivo richiede un codice
const deviceResponse = await fetch('https://auth.example.com/device/code', {
  method: 'POST',
  body: new URLSearchParams({
    client_id: DEVICE_CLIENT_ID,
    scope: 'openid profile'
  })
});

const { device_code, user_code, verification_uri } = await deviceResponse.json();
// Mostra all'utente: "Vai su verification_uri e inserisci user_code"

// 2. Il dispositivo esegue polling fino all'autorizzazione
const pollForToken = async () => {
  const tokenResponse = await fetch('https://auth.example.com/token', {
    method: 'POST',
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
      device_code: device_code,
      client_id: DEVICE_CLIENT_ID
    })
  });

  const data = await tokenResponse.json();
  if (data.error === 'authorization_pending') {
    setTimeout(pollForToken, 5000);  // Riprova tra 5 secondi
  } else {
    return data;  // { access_token, refresh_token }
  }
};
```

### Implementazione con Passport.js

Passport.js è il middleware di autenticazione più diffuso nell'ecosistema Node.js, basato su un'architettura a strategie (strategy pattern):

```javascript
const passport = require('passport');
const { Strategy: OAuth2Strategy } = require('passport-oauth2');

// Configurazione strategia OAuth 2.0 generica
passport.use('oauth2', new OAuth2Strategy({
    authorizationURL: 'https://provider.example.com/authorize',
    tokenURL: 'https://provider.example.com/token',
    clientID: process.env.OAUTH_CLIENT_ID,
    clientSecret: process.env.OAUTH_CLIENT_SECRET,
    callbackURL: 'https://myapp.com/auth/callback',
    scope: ['openid', 'profile', 'email'],
    pkce: true,
    state: true
  },
  async (accessToken, refreshToken, params, profile, done) => {
    try {
      // Cercare o creare l'utente nel database locale
      let user = await findUserByProviderId(profile.id);
      if (!user) {
        user = await createUser({
          providerId: profile.id,
          name: profile.displayName,
          email: profile.emails?.[0]?.value
        });
      }
      return done(null, user);
    } catch (error) {
      return done(error);
    }
  }
));

// Serializzazione per la sessione
passport.serializeUser((user, done) => done(null, user.id));
passport.deserializeUser(async (id, done) => {
  const user = await findUserById(id);
  done(null, user);
});

// Route
app.get('/auth/login', passport.authenticate('oauth2'));
app.get('/auth/callback',
  passport.authenticate('oauth2', { failureRedirect: '/login' }),
  (req, res) => res.redirect('/dashboard')
);
```

---

## OpenID Connect (OIDC)

OpenID Connect è un livello di identità costruito sopra OAuth 2.0. Mentre OAuth 2.0 si occupa di autorizzazione (accesso alle risorse), OIDC aggiunge l'autenticazione standardizzata, fornendo informazioni sull'identità dell'utente.

### ID Token

L'ID Token è un JWT che contiene claims sull'autenticazione dell'utente:

```json
{
  "iss": "https://accounts.google.com",
  "sub": "110169484474386276334",
  "aud": "your-client-id.apps.googleusercontent.com",
  "exp": 1699003600,
  "iat": 1699000000,
  "nonce": "random_nonce_value",
  "name": "Mario Rossi",
  "email": "mario.rossi@gmail.com",
  "email_verified": true,
  "picture": "https://lh3.googleusercontent.com/photo.jpg"
}
```

A differenza dell'access token (che è opaco al client e destinato al resource server), l'ID token è destinato al client e contiene informazioni sull'utente che il client può leggere e validare direttamente.

### Discovery

OIDC definisce un meccanismo di discovery automatico. Ogni provider espone un documento di configurazione all'URL `/.well-known/openid-configuration`:

```javascript
// Recuperare la configurazione del provider
const discoveryUrl = 'https://accounts.google.com/.well-known/openid-configuration';
const config = await fetch(discoveryUrl).then(r => r.json());

/*
Contiene:
  - authorization_endpoint
  - token_endpoint
  - userinfo_endpoint
  - jwks_uri (chiavi pubbliche per verificare i token)
  - scopes_supported
  - response_types_supported
  - claims_supported
*/

// Usare il JWKS per verificare i token
const jwksClient = require('jwks-rsa');
const client = jwksClient({ jwksUri: config.jwks_uri });

function getSigningKey(header, callback) {
  client.getSigningKey(header.kid, (err, key) => {
    const signingKey = key.getPublicKey();
    callback(null, signingKey);
  });
}

jwt.verify(idToken, getSigningKey, {
  algorithms: ['RS256'],
  audience: process.env.CLIENT_ID,
  issuer: 'https://accounts.google.com'
}, (err, decoded) => {
  // decoded contiene i claims dell'utente
});
```

### UserInfo Endpoint

L'endpoint UserInfo permette di ottenere claims aggiuntivi sull'utente autenticato, utilizzando l'access token:

```javascript
const userInfoResponse = await fetch(config.userinfo_endpoint, {
  headers: { Authorization: `Bearer ${accessToken}` }
});

const userInfo = await userInfoResponse.json();
// { sub, name, email, email_verified, picture, locale, ... }
```

---

## Social Login

Il social login semplifica la registrazione e l'accesso degli utenti delegando l'autenticazione a provider di identità consolidati. Passport.js offre strategie dedicate per ciascun provider.

### Google

```javascript
const GoogleStrategy = require('passport-google-oauth20').Strategy;

passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: '/auth/google/callback',
    scope: ['openid', 'profile', 'email']
  },
  async (accessToken, refreshToken, profile, done) => {
    const user = await findOrCreateUser({
      provider: 'google',
      providerId: profile.id,
      name: profile.displayName,
      email: profile.emails[0].value,
      avatar: profile.photos[0]?.value
    });
    done(null, user);
  }
));

app.get('/auth/google', passport.authenticate('google'));
app.get('/auth/google/callback',
  passport.authenticate('google', { failureRedirect: '/login' }),
  (req, res) => res.redirect('/dashboard')
);
```

### GitHub

```javascript
const GitHubStrategy = require('passport-github2').Strategy;

passport.use(new GitHubStrategy({
    clientID: process.env.GITHUB_CLIENT_ID,
    clientSecret: process.env.GITHUB_CLIENT_SECRET,
    callbackURL: '/auth/github/callback',
    scope: ['user:email']
  },
  async (accessToken, refreshToken, profile, done) => {
    // GitHub potrebbe non esporre l'email nel profilo
    let email = profile.emails?.[0]?.value;
    if (!email) {
      // Recuperare l'email tramite API
      const emails = await fetch('https://api.github.com/user/emails', {
        headers: { Authorization: `Bearer ${accessToken}` }
      }).then(r => r.json());
      email = emails.find(e => e.primary)?.email;
    }

    const user = await findOrCreateUser({
      provider: 'github',
      providerId: profile.id,
      name: profile.displayName || profile.username,
      email
    });
    done(null, user);
  }
));
```

### Microsoft

```javascript
const MicrosoftStrategy = require('passport-microsoft').Strategy;

passport.use(new MicrosoftStrategy({
    clientID: process.env.MICROSOFT_CLIENT_ID,
    clientSecret: process.env.MICROSOFT_CLIENT_SECRET,
    callbackURL: '/auth/microsoft/callback',
    scope: ['user.read', 'openid', 'profile', 'email'],
    tenant: 'common'   // 'common', 'organizations', 'consumers', o tenant ID
  },
  async (accessToken, refreshToken, profile, done) => {
    const user = await findOrCreateUser({
      provider: 'microsoft',
      providerId: profile.id,
      name: profile.displayName,
      email: profile.emails?.[0]?.value
    });
    done(null, user);
  }
));
```

Una best practice fondamentale è implementare il **collegamento degli account**: se un utente accede prima con Google e poi con GitHub usando la stessa email, il sistema deve riconoscerlo come lo stesso utente e collegare entrambi i provider al medesimo account.

---

## Autorizzazione

### RBAC — Role-Based Access Control

Il controllo d'accesso basato sui ruoli assegna permessi agli utenti attraverso ruoli predefiniti. È il modello più comune e intuitivo:

```javascript
// Definizione dei ruoli e dei permessi
const ROLES = {
  admin: {
    permissions: ['create', 'read', 'update', 'delete', 'manage_users', 'view_analytics']
  },
  editor: {
    permissions: ['create', 'read', 'update']
  },
  viewer: {
    permissions: ['read']
  }
};

// Middleware di autorizzazione basato sui ruoli
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Autenticazione richiesta' });
    }

    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Accesso negato: ruolo insufficiente' });
    }

    next();
  };
}

// Middleware basato sui permessi (più granulare)
function requirePermission(...requiredPermissions) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Autenticazione richiesta' });
    }

    const userPermissions = ROLES[req.user.role]?.permissions || [];
    const hasAllPermissions = requiredPermissions.every(p => userPermissions.includes(p));

    if (!hasAllPermissions) {
      return res.status(403).json({ error: 'Permessi insufficienti' });
    }

    next();
  };
}

// Uso nelle route
app.get('/articles', requirePermission('read'), getArticles);
app.post('/articles', requirePermission('create'), createArticle);
app.delete('/articles/:id', requirePermission('delete'), deleteArticle);
app.get('/admin/users', requireRole('admin'), listUsers);
```

### ABAC — Attribute-Based Access Control

ABAC è più flessibile di RBAC: le decisioni di accesso si basano su attributi dell'utente, della risorsa, dell'azione e del contesto ambientale:

```javascript
// Engine ABAC
function evaluatePolicy(user, resource, action, context) {
  const policies = [
    {
      name: 'Autori possono modificare i propri articoli',
      condition: (u, r, a) =>
        a === 'update' &&
        r.type === 'article' &&
        r.authorId === u.id
    },
    {
      name: 'Accesso solo in orario lavorativo',
      condition: (u, r, a, ctx) => {
        const hour = new Date(ctx.timestamp).getHours();
        return hour >= 8 && hour <= 18;
      }
    },
    {
      name: 'Manager del dipartimento possono approvare',
      condition: (u, r, a) =>
        a === 'approve' &&
        u.role === 'manager' &&
        u.department === r.department
    },
    {
      name: 'Documenti confidenziali solo per livello security >= 3',
      condition: (u, r, a) =>
        r.classification !== 'confidential' ||
        u.securityLevel >= 3
    }
  ];

  return policies.every(policy => policy.condition(user, resource, action, context));
}

// Middleware ABAC
function abacMiddleware(action) {
  return async (req, res, next) => {
    const resource = await getResource(req.params.id);
    const context = { timestamp: Date.now(), ip: req.ip };

    if (!evaluatePolicy(req.user, resource, action, context)) {
      return res.status(403).json({ error: 'Accesso negato dalla policy' });
    }

    req.resource = resource;
    next();
  };
}
```

### Libreria CASL

CASL (Isomorphic Authorization) è una libreria JavaScript isomorfica per la gestione dei permessi, utilizzabile sia lato server che lato client:

```javascript
const { AbilityBuilder, createMongoAbility } = require('@casl/ability');

// Definire le abilità in base al ruolo dell'utente
function defineAbilitiesFor(user) {
  const { can, cannot, build } = new AbilityBuilder(createMongoAbility);

  if (user.role === 'admin') {
    can('manage', 'all');  // Può fare tutto su qualsiasi risorsa
  } else if (user.role === 'editor') {
    can('read', 'Article');
    can('create', 'Article');
    can('update', 'Article', { authorId: user.id });     // Solo i propri articoli
    cannot('delete', 'Article');                          // Non può cancellare
    can('read', 'Comment');
    can('create', 'Comment');
    can('update', 'Comment', { authorId: user.id });
    can('delete', 'Comment', { authorId: user.id });
  } else {
    // Ruolo viewer
    can('read', 'Article', { published: true });          // Solo articoli pubblicati
    can('read', 'Comment');
    can('create', 'Comment');
  }

  return build();
}

// Middleware Express con CASL
function authorize(action, subject) {
  return (req, res, next) => {
    const ability = defineAbilitiesFor(req.user);

    if (ability.can(action, subject)) {
      next();
    } else {
      res.status(403).json({ error: 'Azione non consentita' });
    }
  };
}

// Filtrare i risultati del database in base ai permessi
const { accessibleBy } = require('@casl/mongoose');

app.get('/articles', requireAuth, async (req, res) => {
  const ability = defineAbilitiesFor(req.user);
  const articles = await Article.find(accessibleBy(ability, 'read'));
  res.json(articles);
});
```

---

## Multi-Factor Authentication (MFA)

L'autenticazione multi-fattore aggiunge livelli di sicurezza richiedendo due o più fattori di verifica indipendenti: qualcosa che sai (password), qualcosa che possiedi (telefono, chiave hardware) e qualcosa che sei (biometria).

### TOTP con speakeasy

Il TOTP (Time-Based One-Time Password) genera codici a 6 cifre che cambiano ogni 30 secondi. L'utente li visualizza tramite un'app come Google Authenticator o Authy:

```javascript
const speakeasy = require('speakeasy');
const QRCode = require('qrcode');

// 1. Generare il segreto durante il setup MFA
app.post('/mfa/setup', requireAuth, async (req, res) => {
  const secret = speakeasy.generateSecret({
    name: `MiaApp (${req.user.email})`,
    issuer: 'MiaApp',
    length: 32
  });

  // Salvare il segreto temporaneamente (non ancora confermato)
  await savePendingMfaSecret(req.user.id, secret.base32);

  // Generare il QR code per l'app authenticator
  const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url);

  res.json({
    qrCode: qrCodeUrl,
    manualEntry: secret.base32   // Per inserimento manuale
  });
});

// 2. Verificare e attivare MFA
app.post('/mfa/verify-setup', requireAuth, async (req, res) => {
  const { code } = req.body;
  const pendingSecret = await getPendingMfaSecret(req.user.id);

  const isValid = speakeasy.totp.verify({
    secret: pendingSecret,
    encoding: 'base32',
    token: code,
    window: 1     // Tolleranza: accetta codici +-30 secondi
  });

  if (!isValid) {
    return res.status(400).json({ error: 'Codice non valido' });
  }

  // Generare codici di recupero
  const recoveryCodes = generateRecoveryCodes(10);
  await enableMfa(req.user.id, pendingSecret, recoveryCodes);

  res.json({
    message: 'MFA attivato',
    recoveryCodes    // Mostrare una sola volta all'utente
  });
});

// 3. Verifica TOTP durante il login
app.post('/mfa/challenge', async (req, res) => {
  const { mfaToken, code } = req.body;  // mfaToken identifica la sessione MFA parziale
  const userId = await getMfaPendingUser(mfaToken);
  const secret = await getMfaSecret(userId);

  const isValid = speakeasy.totp.verify({
    secret,
    encoding: 'base32',
    token: code,
    window: 1
  });

  if (!isValid) {
    return res.status(401).json({ error: 'Codice MFA non valido' });
  }

  const user = await findUserById(userId);
  const tokens = generateTokenPair(user);
  res.json(tokens);
});
```

### WebAuthn / FIDO2 Passkeys

Le passkey rappresentano il futuro dell'autenticazione: utilizzano crittografia a chiave pubblica con autenticatori hardware o biometrici (impronta digitale, riconoscimento facciale), eliminando completamente le password.

```javascript
const {
  generateRegistrationOptions,
  verifyRegistrationResponse,
  generateAuthenticationOptions,
  verifyAuthenticationResponse
} = require('@simplewebauthn/server');

const rpName = 'MiaApp';
const rpID = 'example.com';
const origin = 'https://example.com';

// Registrazione passkey — Step 1: generare le opzioni
app.post('/webauthn/register/options', requireAuth, async (req, res) => {
  const userAuthenticators = await getUserAuthenticators(req.user.id);

  const options = await generateRegistrationOptions({
    rpName,
    rpID,
    userID: req.user.id,
    userName: req.user.email,
    userDisplayName: req.user.name,
    attestationType: 'none',
    excludeCredentials: userAuthenticators.map(auth => ({
      id: auth.credentialID,
      type: 'public-key'
    })),
    authenticatorSelection: {
      residentKey: 'preferred',
      userVerification: 'preferred'
    }
  });

  await saveChallenge(req.user.id, options.challenge);
  res.json(options);
});

// Registrazione passkey — Step 2: verificare la risposta
app.post('/webauthn/register/verify', requireAuth, async (req, res) => {
  const expectedChallenge = await getChallenge(req.user.id);

  const verification = await verifyRegistrationResponse({
    response: req.body,
    expectedChallenge,
    expectedOrigin: origin,
    expectedRPID: rpID
  });

  if (verification.verified) {
    const { credentialID, credentialPublicKey, counter } = verification.registrationInfo;
    await saveAuthenticator(req.user.id, {
      credentialID,
      credentialPublicKey,
      counter
    });
    res.json({ verified: true });
  }
});
```

### Backup SMS/Email

I codici di backup via SMS o email servono come alternativa quando l'autenticatore primario non è disponibile. L'SMS è considerato meno sicuro a causa degli attacchi SIM swapping, ma resta un'opzione pragmatica:

```javascript
// Invio codice di verifica via email
app.post('/mfa/email-code', async (req, res) => {
  const { mfaToken } = req.body;
  const userId = await getMfaPendingUser(mfaToken);
  const user = await findUserById(userId);

  const code = generateNumericCode(6);  // Es. "482937"
  const expiresAt = Date.now() + 10 * 60 * 1000;  // 10 minuti

  await storeVerificationCode(userId, {
    code: await hashCode(code),  // Salvare hashato
    expiresAt,
    attempts: 0
  });

  await sendEmail({
    to: user.email,
    subject: 'Codice di verifica MiaApp',
    text: `Il tuo codice di verifica è: ${code}\nScade tra 10 minuti.`
  });

  res.json({ message: 'Codice inviato all\'email registrata' });
});
```

---

## Sicurezza delle Password

### bcrypt e Argon2

Mai salvare le password in chiaro. L'hashing trasforma la password in un valore irreversibile. Algoritmi moderni come bcrypt e Argon2 includono un salt automatico e sono progettati per essere computazionalmente costosi, rendendo gli attacchi brute-force impraticabili.

```javascript
const bcrypt = require('bcrypt');
const argon2 = require('argon2');

// === bcrypt ===
const SALT_ROUNDS = 12;  // Costo computazionale (2^12 iterazioni)

async function hashPasswordBcrypt(password) {
  return bcrypt.hash(password, SALT_ROUNDS);
}

async function verifyPasswordBcrypt(password, hash) {
  return bcrypt.compare(password, hash);
}

// === Argon2 (raccomandato da OWASP) ===
async function hashPasswordArgon2(password) {
  return argon2.hash(password, {
    type: argon2.argon2id,      // Variante ibrida (resistente a side-channel e GPU)
    memoryCost: 65536,          // 64 MB di memoria
    timeCost: 3,                // 3 iterazioni
    parallelism: 4              // 4 thread paralleli
  });
}

async function verifyPasswordArgon2(password, hash) {
  return argon2.verify(hash, password);
}
```

### Salting

Il **salt** è un valore casuale univoco aggiunto alla password prima dell'hashing. Previene gli attacchi con rainbow table (tabelle pre-calcolate di hash). Sia bcrypt che Argon2 generano e includono automaticamente il salt nell'hash risultante, quindi non serve gestirlo manualmente.

### Password Policy

Una buona policy sulle password bilancia sicurezza e usabilità:

```javascript
const zxcvbn = require('zxcvbn');  // Stima della forza della password

function validatePassword(password, userInfo = {}) {
  const errors = [];

  // Lunghezza minima (NIST raccomanda almeno 8 caratteri)
  if (password.length < 10) {
    errors.push('La password deve essere di almeno 10 caratteri');
  }

  // Lunghezza massima (per prevenire DoS con password enormi)
  if (password.length > 128) {
    errors.push('La password non può superare i 128 caratteri');
  }

  // Non contenere informazioni personali dell'utente
  const personalValues = [userInfo.name, userInfo.email, userInfo.username]
    .filter(Boolean)
    .map(v => v.toLowerCase());

  if (personalValues.some(v => password.toLowerCase().includes(v))) {
    errors.push('La password non deve contenere informazioni personali');
  }

  // Verifica della complessità con zxcvbn
  const strength = zxcvbn(password);
  if (strength.score < 3) {  // Score 0-4
    errors.push(`Password troppo debole: ${strength.feedback.warning || 'usa una combinazione più complessa'}`);
  }

  return { valid: errors.length === 0, errors };
}
```

### Controllo HIBP (Have I Been Pwned)

Verificare se una password è stata compromessa in data breach noti, senza inviare la password in chiaro:

```javascript
const crypto = require('crypto');

async function isPasswordPwned(password) {
  // k-Anonymity: inviare solo i primi 5 caratteri dell'hash SHA-1
  const sha1 = crypto.createHash('sha1').update(password).digest('hex').toUpperCase();
  const prefix = sha1.slice(0, 5);
  const suffix = sha1.slice(5);

  const response = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`, {
    headers: { 'Add-Padding': 'true' }
  });

  const text = await response.text();
  const lines = text.split('\n');

  for (const line of lines) {
    const [hashSuffix, count] = line.split(':');
    if (hashSuffix.trim() === suffix) {
      return { pwned: true, count: parseInt(count) };
    }
  }

  return { pwned: false, count: 0 };
}

// Uso durante la registrazione
app.post('/register', async (req, res) => {
  const { password } = req.body;

  const pwnedCheck = await isPasswordPwned(password);
  if (pwnedCheck.pwned) {
    return res.status(400).json({
      error: `Questa password è apparsa in ${pwnedCheck.count.toLocaleString()} data breach. Scegli una password diversa.`
    });
  }

  // Proseguire con la registrazione...
});
```

---

## Gestione delle Sessioni

### Session Fixation

L'attacco session fixation avviene quando un attaccante forza un session ID noto all'utente vittima. La difesa è rigenerare sempre il session ID dopo il login (come mostrato nell'esempio `express-session` precedente con `req.session.regenerate()`).

### Timeout delle Sessioni

Implementare sia un timeout di inattività (idle timeout) che un timeout assoluto:

```javascript
const SESSION_IDLE_TIMEOUT = 30 * 60 * 1000;     // 30 minuti di inattività
const SESSION_ABSOLUTE_TIMEOUT = 8 * 60 * 60 * 1000;  // 8 ore assolute

function sessionTimeoutMiddleware(req, res, next) {
  if (!req.session.userId) return next();

  const now = Date.now();

  // Timeout assoluto: la sessione scade dopo un periodo fisso dal login
  if (now - req.session.loginAt > SESSION_ABSOLUTE_TIMEOUT) {
    return req.session.destroy(() => {
      res.status(401).json({ error: 'Sessione scaduta. Effettua nuovamente il login.' });
    });
  }

  // Timeout di inattività: la sessione scade dopo un periodo senza attività
  if (req.session.lastActivity && (now - req.session.lastActivity > SESSION_IDLE_TIMEOUT)) {
    return req.session.destroy(() => {
      res.status(401).json({ error: 'Sessione scaduta per inattività.' });
    });
  }

  // Aggiornare il timestamp dell'ultima attività
  req.session.lastActivity = now;
  next();
}

app.use(sessionTimeoutMiddleware);
```

### Sessioni Concorrenti

Limitare il numero di sessioni attive contemporanee per un utente previene l'uso non autorizzato di credenziali condivise:

```javascript
const MAX_CONCURRENT_SESSIONS = 3;

async function enforceSessionLimit(userId, currentSessionId) {
  const activeSessions = await getActiveSessionsForUser(userId);

  if (activeSessions.length >= MAX_CONCURRENT_SESSIONS) {
    // Strategia 1: Rimuovere la sessione più vecchia
    const oldestSession = activeSessions
      .sort((a, b) => a.createdAt - b.createdAt)[0];
    await destroySession(oldestSession.id);

    // Strategia 2 (alternativa): Rifiutare il nuovo login
    // throw new Error('Numero massimo di sessioni attive raggiunto');
  }
}

// Endpoint per visualizzare le sessioni attive
app.get('/account/sessions', requireAuth, async (req, res) => {
  const sessions = await getActiveSessionsForUser(req.user.id);
  res.json(sessions.map(s => ({
    id: s.id,
    device: s.userAgent,
    ip: s.ipAddress,
    lastActive: s.lastActivity,
    current: s.id === req.sessionID
  })));
});

// Revocare una sessione specifica
app.delete('/account/sessions/:sessionId', requireAuth, async (req, res) => {
  await destroySession(req.params.sessionId);
  res.json({ message: 'Sessione revocata' });
});
```

### Revocazione

Per i JWT, la revocazione è complessa poiché i token sono stateless. Le strategie includono:

```javascript
// Strategia 1: Blocklist di token revocati (memorizzata in Redis)
const redis = require('redis').createClient();

async function revokeToken(token) {
  const decoded = jwt.decode(token);
  const ttl = decoded.exp - Math.floor(Date.now() / 1000);
  if (ttl > 0) {
    await redis.setEx(`revoked:${decoded.jti}`, ttl, '1');
  }
}

async function isTokenRevoked(token) {
  const decoded = jwt.decode(token);
  const result = await redis.get(`revoked:${decoded.jti}`);
  return result !== null;
}

// Middleware di verifica
async function verifyToken(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'Token mancante' });

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    if (await isTokenRevoked(token)) {
      return res.status(401).json({ error: 'Token revocato' });
    }

    req.user = decoded;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Token non valido' });
  }
}
```

---

## Single Sign-On (SSO)

Il Single Sign-On permette agli utenti di autenticarsi una sola volta e accedere a molteplici applicazioni senza ripetere il login.

### SAML (Security Assertion Markup Language)

SAML 2.0 è uno standard basato su XML, ancora molto diffuso in contesti enterprise. Il flusso prevede tre attori: l'utente, il **Service Provider** (SP, la tua applicazione) e l'**Identity Provider** (IdP, ad esempio Okta, Azure AD).

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Utente  │         │    SP    │         │   IdP    │
│ (Browser)│         │ (App)    │         │ (Okta)   │
│          │         │          │         │          │
│  1. Accede a       │          │         │          │
│     app.example.com│          │         │          │
│  ───────────────►  │          │         │          │
│          │         │ 2. Non   │         │          │
│          │         │ autent.  │         │          │
│  3. Redirect a IdP │          │         │          │
│  con SAMLRequest   │          │         │          │
│  ◄─────────────────│          │         │          │
│          │         │          │         │          │
│  4. Login su IdP   │          │         │          │
│  ──────────────────────────────────────►│          │
│          │         │          │         │ 5. Verif.│
│  6. Redirect a SP  │          │         │ credenz. │
│  con SAMLResponse  │          │         │          │
│  ◄──────────────────────────────────────│          │
│          │         │          │         │          │
│  7. POST SAMLResponse a SP             │          │
│  ───────────────►  │          │         │          │
│          │         │ 8. Valida│         │          │
│          │         │ asserzione         │          │
│  9. Sessione creata│          │         │          │
│  ◄─────────────────│          │         │          │
└──────────┘         └──────────┘         └──────────┘
```

```javascript
const saml2 = require('saml2-js');

const spOptions = {
  entity_id: 'https://app.example.com/metadata',
  assert_endpoint: 'https://app.example.com/auth/saml/callback',
  certificate: fs.readFileSync('./certs/sp-cert.pem', 'utf8'),
  private_key: fs.readFileSync('./certs/sp-key.pem', 'utf8')
};

const idpOptions = {
  sso_login_url: 'https://idp.example.com/saml/sso',
  sso_logout_url: 'https://idp.example.com/saml/logout',
  certificates: [fs.readFileSync('./certs/idp-cert.pem', 'utf8')]
};

const sp = new saml2.ServiceProvider(spOptions);
const idp = new saml2.IdentityProvider(idpOptions);

// Iniziare il flusso SSO
app.get('/auth/saml/login', (req, res) => {
  sp.create_login_request_url(idp, {}, (err, loginUrl) => {
    if (err) return res.status(500).send('Errore SSO');
    res.redirect(loginUrl);
  });
});

// Callback dopo l'autenticazione su IdP
app.post('/auth/saml/callback', (req, res) => {
  sp.post_assert(idp, { request_body: req.body }, async (err, samlResponse) => {
    if (err) return res.status(403).send('Asserzione SAML non valida');

    const { name_id, attributes } = samlResponse.user;
    const user = await findOrCreateSamlUser(name_id, attributes);

    req.session.userId = user.id;
    res.redirect('/dashboard');
  });
});
```

### SSO basato su OIDC

Rispetto a SAML, l'SSO basato su OpenID Connect è più moderno, più leggero (JSON invece di XML) e più adatto alle applicazioni web e mobile moderne. Il flusso è essenzialmente quello di OAuth 2.0 Authorization Code con OIDC, come descritto nelle sezioni precedenti.

I vantaggi di OIDC rispetto a SAML per nuove implementazioni:
- Formato JSON più semplice da gestire rispetto a XML/SOAP
- Migliore supporto per SPA e applicazioni mobile
- Discovery automatico tramite `.well-known/openid-configuration`
- Ecosistema di librerie più ampio e attivo

---

## Autenticazione API

### API Keys

Le API key sono semplici da implementare ma offrono sicurezza limitata. Sono adatte per identificare il client (non l'utente) e per API pubbliche con rate limiting:

```javascript
const crypto = require('crypto');

// Generazione di una API key
function generateApiKey() {
  const prefix = 'mk';  // Identificatore dell'applicazione
  const key = crypto.randomBytes(32).toString('hex');
  return `${prefix}_${key}`;  // Es. "mk_a1b2c3d4..."
}

// Middleware di autenticazione API key
async function authenticateApiKey(req, res, next) {
  const apiKey = req.headers['x-api-key'] || req.query.api_key;

  if (!apiKey) {
    return res.status(401).json({ error: 'API key mancante' });
  }

  // Salvare l'hash della API key nel database (non la key in chiaro)
  const hashedKey = crypto.createHash('sha256').update(apiKey).digest('hex');
  const keyRecord = await findApiKeyByHash(hashedKey);

  if (!keyRecord || keyRecord.revokedAt) {
    return res.status(401).json({ error: 'API key non valida o revocata' });
  }

  // Aggiornare l'ultimo utilizzo
  await updateApiKeyLastUsed(keyRecord.id);

  req.apiClient = keyRecord;
  next();
}

app.use('/api/v1', authenticateApiKey);
```

### Bearer Tokens

I Bearer token (tipicamente JWT) sono lo standard per l'autenticazione API in architetture RESTful e GraphQL:

```javascript
// Middleware Bearer token
function authenticateBearer(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Bearer token mancante' });
  }

  const token = authHeader.slice(7);

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET, {
      algorithms: ['HS256'],
      issuer: 'auth.example.com',
      audience: 'api.example.com'
    });

    req.user = decoded;
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Token scaduto' });
    }
    res.status(401).json({ error: 'Token non valido' });
  }
}
```

### mTLS (Mutual TLS)

Il TLS mutuo richiede che sia il server che il client presentino un certificato X.509, garantendo l'autenticazione bidirezionale. È particolarmente adatto per la comunicazione tra microservizi:

```javascript
const https = require('https');
const fs = require('fs');

// Server che richiede il certificato client
const serverOptions = {
  key: fs.readFileSync('./certs/server-key.pem'),
  cert: fs.readFileSync('./certs/server-cert.pem'),
  ca: [fs.readFileSync('./certs/ca-cert.pem')],   // CA fidata per i certificati client
  requestCert: true,              // Richiedere il certificato client
  rejectUnauthorized: true        // Rifiutare client senza certificato valido
};

const server = https.createServer(serverOptions, app);

// Middleware per estrarre le informazioni dal certificato client
function extractClientCert(req, res, next) {
  const cert = req.socket.getPeerCertificate();

  if (!cert || !cert.subject) {
    return res.status(403).json({ error: 'Certificato client mancante' });
  }

  req.clientIdentity = {
    commonName: cert.subject.CN,
    organization: cert.subject.O,
    fingerprint: cert.fingerprint256,
    validTo: cert.valid_to
  };

  next();
}

app.use(extractClientCert);
```

---

## OAuth 2.1 — Evoluzione e Best Practice

Con la pubblicazione di **RFC 9700** (gennaio 2025), l'IETF ha formalizzato le best practice di sicurezza per OAuth 2.0, aggiornando il modello di minaccia e le raccomandazioni operative rispetto alle specifiche originali (RFC 6749, 6750, 6819). OAuth 2.1, attualmente in fase di finalizzazione, consolida queste raccomandazioni in una specifica unica che sostituirà di fatto OAuth 2.0 per le nuove implementazioni.

### Flussi Deprecati e Rimossi

OAuth 2.1 elimina formalmente due grant type considerati insicuri:

**Implicit Grant (response_type=token)** — Questo flusso restituiva l'access token direttamente nel fragment dell'URL di redirect. I problemi sono molteplici: il token è esposto nella cronologia del browser, nei log del web server, nei header `Referer`, e può essere intercettato da script malevoli nella pagina. Non esiste un meccanismo di verifica dell'integrità del token ricevuto, rendendo possibili attacchi di token injection e replay.

**Resource Owner Password Credentials (ROPC)** — Questo flusso richiedeva che l'applicazione client raccogliesse direttamente username e password dell'utente e li inviasse al server di autorizzazione. Viola il principio fondamentale di OAuth (delega dell'autorizzazione senza condivisione delle credenziali), impedisce all'utente di distinguere tra l'applicazione legittima e un'applicazione di phishing, e rende impossibile l'implementazione di MFA a livello di identity provider.

### PKCE Obbligatorio per Tutti i Client

Una delle modifiche più significative di OAuth 2.1 è rendere **PKCE obbligatorio** per tutti i tipi di client, non solo per i client pubblici. Anche i client confidenziali (server-side con `client_secret`) devono implementare PKCE come difesa in profondità. Il motivo è che PKCE protegge contro attacchi di authorization code injection anche quando il canale di comunicazione è sicuro, aggiungendo un livello di protezione indipendente dall'autenticazione del client.

```javascript
// OAuth 2.1: PKCE obbligatorio anche per client confidenziali
const crypto = require('crypto');

function generatePKCE() {
  // code_verifier: stringa random 43-128 caratteri (RFC 7636)
  const verifier = crypto.randomBytes(32)
    .toString('base64url')
    .slice(0, 128);

  // code_challenge: SHA-256 del verifier, codificato in base64url
  const challenge = crypto.createHash('sha256')
    .update(verifier)
    .digest('base64url');

  return { verifier, challenge };
}

// Il metodo 'plain' è deprecato in OAuth 2.1 — usare sempre S256
// plain: code_challenge = code_verifier (nessuna trasformazione)
// S256:  code_challenge = BASE64URL(SHA256(code_verifier))
```

### Nuovi Modelli di Minaccia

RFC 9700 introduce contromisure per minacce emerse dopo la pubblicazione originale di OAuth 2.0:

**Mix-Up Attack** — In scenari con più authorization server, un attaccante può ingannare il client facendogli inviare il codice di autorizzazione all'authorization server sbagliato. La contromisura è verificare che il `iss` (issuer) nell'authorization response corrisponda all'authorization server atteso:

```javascript
// Difesa contro mix-up attack: verificare l'issuer nella risposta
app.get('/auth/callback', async (req, res) => {
  const { code, state, iss } = req.query;
  const savedState = await getStoredState(state);

  // Verificare che l'issuer nella risposta corrisponda a quello atteso
  if (iss !== savedState.expectedIssuer) {
    return res.status(400).json({
      error: 'Issuer mismatch — possibile mix-up attack'
    });
  }

  // Procedere con lo scambio del codice
  const tokenResponse = await exchangeCode(code, savedState);
  // ...
});
```

**Redirect URI Validation** — OAuth 2.1 richiede il confronto esatto (exact string matching) tra la `redirect_uri` registrata e quella nella richiesta di autorizzazione. Non è più ammesso il pattern matching o la corrispondenza parziale. Questo previene attacchi di open redirect dove un attaccante sfrutta URI simili ma controllate.

**Token Leakage via Referrer** — L'access token o il codice di autorizzazione possono trapelare tramite l'header HTTP `Referer` se la pagina di callback contiene link esterni. La raccomandazione è impostare `Referrer-Policy: no-referrer` sulle pagine coinvolte nel flusso OAuth e non includere link o risorse esterne nella pagina di callback.

### Sender-Constrained Tokens

OAuth 2.1 promuove l'uso di **token vincolati al mittente** (sender-constrained tokens), che sono validi solo quando presentati dallo stesso client che li ha richiesti. Due meccanismi principali:

**DPoP (Demonstrating Proof-of-Possession, RFC 9449)** — Il client genera una coppia di chiavi asimmetriche e invia un proof JWT firmato con la chiave privata insieme all'access token. Il server verifica che il proof sia stato firmato dalla stessa chiave associata al token. Adatto per browser e applicazioni mobile:

```javascript
const jose = require('jose');

// Il client genera una coppia di chiavi DPoP (una sola volta, riutilizzata)
const { publicKey, privateKey } = await jose.generateKeyPair('ES256');

// Creare il DPoP proof per ogni richiesta
async function createDPoPProof(httpMethod, httpUri, accessToken) {
  const proof = await new jose.SignJWT({
    htm: httpMethod,          // HTTP method
    htu: httpUri,             // HTTP URI (senza query string)
    ath: await jose.base64url.encode(
      new Uint8Array(await crypto.subtle.digest(
        'SHA-256',
        new TextEncoder().encode(accessToken)
      ))
    )                         // Hash dell'access token
  })
    .setProtectedHeader({
      alg: 'ES256',
      typ: 'dpop+jwt',
      jwk: await jose.exportJWK(publicKey)   // Chiave pubblica nel header
    })
    .setJti(crypto.randomUUID())              // ID univoco del proof
    .setIssuedAt()
    .sign(privateKey);

  return proof;
}

// Invio della richiesta con DPoP
async function fetchWithDPoP(url, accessToken) {
  const proof = await createDPoPProof('GET', url, accessToken);

  return fetch(url, {
    headers: {
      'Authorization': `DPoP ${accessToken}`,    // Notare: DPoP, non Bearer
      'DPoP': proof
    }
  });
}
```

**mTLS Certificate-Bound Tokens (RFC 8705)** — Il token è vincolato al certificato TLS del client. Il server verifica che il certificato presentato nella connessione TLS corrisponda al thumbprint registrato nel token. Ideale per comunicazione machine-to-machine dove l'infrastruttura PKI è già presente.

---

## OIDC — Approfondimento Tecnico

OpenID Connect merita un approfondimento oltre la panoramica già presentata, in quanto la corretta implementazione dei suoi meccanismi è fondamentale per la sicurezza dell'autenticazione.

### Validazione Completa dell'ID Token

La validazione dell'ID Token non si limita a verificare la firma. L'OIDC Core Specification (Sezione 3.1.3.7) definisce una checklist di validazione precisa che ogni Relying Party (client) deve seguire:

```javascript
async function validateIdToken(idToken, config) {
  const { payload, protectedHeader } = await jose.jwtVerify(
    idToken,
    await getJWKS(config.jwks_uri),
    {
      algorithms: ['RS256', 'ES256'],            // Solo algoritmi accettati
      issuer: config.issuer,                      // 1. iss deve corrispondere
      audience: process.env.CLIENT_ID             // 2. aud deve contenere il client_id
    }
  );

  // 3. Se aud contiene più valori, verificare azp (authorized party)
  if (Array.isArray(payload.aud) && payload.aud.length > 1) {
    if (payload.azp !== process.env.CLIENT_ID) {
      throw new Error('azp claim non corrisponde al client_id');
    }
  }

  // 4. Verificare exp (scadenza) — jose.jwtVerify lo fa automaticamente

  // 5. Verificare iat (issued at) — rifiutare token troppo vecchi
  const maxAge = 600; // 10 minuti
  if (Date.now() / 1000 - payload.iat > maxAge) {
    throw new Error('ID token troppo vecchio');
  }

  // 6. Verificare nonce (se inviato nella richiesta di autorizzazione)
  if (config.expectedNonce && payload.nonce !== config.expectedNonce) {
    throw new Error('Nonce non corrisponde — possibile replay attack');
  }

  // 7. Verificare auth_time (se max_age era specificato nella richiesta)
  if (config.maxAge && payload.auth_time) {
    if (Date.now() / 1000 - payload.auth_time > config.maxAge) {
      throw new Error('Autenticazione troppo vecchia — richiedere re-autenticazione');
    }
  }

  // 8. Verificare at_hash (hash dell'access token) se presente
  if (payload.at_hash) {
    const atHash = await computeAtHash(config.accessToken, protectedHeader.alg);
    if (atHash !== payload.at_hash) {
      throw new Error('at_hash non corrisponde — token potenzialmente manomesso');
    }
  }

  return payload;
}

// Calcolo dell'at_hash secondo la specifica OIDC
async function computeAtHash(accessToken, alg) {
  const hashAlg = alg === 'RS256' || alg === 'ES256' ? 'SHA-256' : 'SHA-512';
  const hash = crypto.createHash(hashAlg.replace('-', ''))
    .update(accessToken)
    .digest();
  // Prendere la prima metà dell'hash e codificare in base64url
  const halfHash = hash.slice(0, hash.length / 2);
  return halfHash.toString('base64url');
}
```

### Claim Standard e Personalizzati

OIDC definisce un insieme di **claim standard** che i provider possono includere nell'ID token o restituire dall'endpoint UserInfo:

| Categoria | Claim | Descrizione |
|-----------|-------|-------------|
| **Identificazione** | `sub` | Identificatore univoco e stabile dell'utente presso il provider |
| | `name` | Nome completo visualizzabile |
| | `given_name` | Nome |
| | `family_name` | Cognome |
| | `preferred_username` | Username scelto dall'utente |
| **Contatto** | `email` | Indirizzo email |
| | `email_verified` | Boolean: l'email è stata verificata dal provider |
| | `phone_number` | Numero di telefono in formato E.164 |
| | `phone_number_verified` | Boolean: il telefono è stato verificato |
| **Profilo** | `picture` | URL dell'immagine del profilo |
| | `locale` | Locale dell'utente (es. `it-IT`) |
| | `zoneinfo` | Fuso orario (es. `Europe/Rome`) |
| | `updated_at` | Timestamp dell'ultimo aggiornamento del profilo |
| **Autenticazione** | `auth_time` | Timestamp dell'ultima autenticazione |
| | `nonce` | Valore anti-replay inviato dal client |
| | `acr` | Authentication Context Class Reference |
| | `amr` | Authentication Methods References (array) |

I **claim personalizzati** devono usare un namespace per evitare collisioni. La convenzione è utilizzare un URI come prefisso:

```json
{
  "sub": "user_12345",
  "name": "Mario Rossi",
  "https://miaapp.com/claims/tenant_id": "tenant_abc",
  "https://miaapp.com/claims/plan": "enterprise",
  "https://miaapp.com/claims/permissions": ["read:docs", "write:docs"]
}
```

### ID Token vs UserInfo Endpoint

Una decisione architetturale fondamentale è quali claim includere nell'ID token e quali ottenere dall'endpoint UserInfo:

**ID Token** — I claim sono disponibili immediatamente dopo l'autenticazione, senza richieste aggiuntive. Tuttavia, un ID token troppo grande aumenta la latenza (viene trasmesso in ogni redirect) e può superare i limiti di dimensione degli header HTTP o dei cookie. Includere solo i claim essenziali per l'autenticazione e l'identificazione iniziale.

**UserInfo Endpoint** — Richiede una richiesta HTTP aggiuntiva con l'access token, ma permette di ottenere claim dettagliati senza appesantire il token. I claim restituiti dall'endpoint UserInfo sono garantiti essere gli stessi dell'ID token (stesso `sub`), ma possono essere più completi. Utilizzare per claim di profilo dettagliati, preferenze utente e dati che cambiano frequentemente.

### Documento di Discovery — Campi Chiave

Il documento `/.well-known/openid-configuration` contiene tutti gli endpoint e le capacità del provider. I campi più rilevanti:

```javascript
// Campi essenziali del documento di discovery
const discoveryFields = {
  // Endpoint operativi
  issuer: 'https://auth.example.com',
  authorization_endpoint: 'https://auth.example.com/authorize',
  token_endpoint: 'https://auth.example.com/token',
  userinfo_endpoint: 'https://auth.example.com/userinfo',
  jwks_uri: 'https://auth.example.com/.well-known/jwks.json',
  registration_endpoint: 'https://auth.example.com/register',      // Dynamic Client Registration
  end_session_endpoint: 'https://auth.example.com/logout',          // RP-Initiated Logout

  // Capacità supportate
  scopes_supported: ['openid', 'profile', 'email', 'address', 'phone'],
  response_types_supported: ['code', 'code id_token'],
  grant_types_supported: ['authorization_code', 'refresh_token', 'client_credentials'],
  subject_types_supported: ['public', 'pairwise'],
  id_token_signing_alg_values_supported: ['RS256', 'ES256'],
  token_endpoint_auth_methods_supported: ['client_secret_basic', 'client_secret_post', 'private_key_jwt'],

  // Claim disponibili
  claims_supported: ['sub', 'name', 'email', 'email_verified', 'picture', 'locale'],

  // Sicurezza
  code_challenge_methods_supported: ['S256'],
  dpop_signing_alg_values_supported: ['ES256', 'EdDSA']
};
```

### Rotazione delle Chiavi JWKS

I provider OIDC pubblicano le chiavi pubbliche per la verifica dei token tramite l'endpoint JWKS (JSON Web Key Set). La rotazione periodica delle chiavi è una pratica di sicurezza fondamentale. Il client deve:

1. **Memorizzare le chiavi in cache** con un TTL ragionevole (tipicamente 1-24 ore)
2. **Gestire la rotazione** cercando una chiave sconosciuta nel JWKS aggiornato prima di rifiutare un token
3. **Supportare più chiavi contemporanee** tramite il campo `kid` (Key ID) nel header del JWT

```javascript
const jose = require('jose');

// Creare un JWKS remoto con cache automatica e refresh
const JWKS = jose.createRemoteJWKSet(
  new URL('https://auth.example.com/.well-known/jwks.json'),
  {
    cooldownDuration: 30000,      // Attesa minima tra refresh (30s)
    cacheMaxAge: 600000,          // Cache per 10 minuti
    timeoutDuration: 5000         // Timeout della richiesta HTTP
  }
);

// La verifica seleziona automaticamente la chiave corretta tramite kid
const { payload } = await jose.jwtVerify(token, JWKS, {
  issuer: 'https://auth.example.com',
  audience: 'my-client-id'
});
```

---

## PKCE — Flusso Tecnico Dettagliato

PKCE (Proof Key for Code Exchange, pronunciato "pixy", RFC 7636) è stato originariamente progettato per proteggere i client pubblici (SPA, app mobile) che non possono custodire un `client_secret`. Con OAuth 2.1, è diventato obbligatorio per tutti i tipi di client.

### Il Problema che PKCE Risolve

Senza PKCE, un attaccante che intercetta il codice di autorizzazione durante il redirect (tramite malware, URL scheme hijacking su mobile, o log di rete) può scambiarlo per un access token. Il codice di autorizzazione viaggia nell'URL di redirect, che è potenzialmente visibile a proxy, browser extension e applicazioni registrate per lo stesso URL scheme.

### Entropia e Generazione del code_verifier

Il `code_verifier` deve avere sufficiente entropia per resistere ad attacchi brute-force. RFC 7636 specifica:

- **Lunghezza**: 43-128 caratteri
- **Set di caratteri**: `[A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"` (unreserved URI characters)
- **Entropia minima raccomandata**: 256 bit (32 byte random codificati in base64url producono 43 caratteri)

```javascript
// Generazione corretta del code_verifier
function generateCodeVerifier() {
  // 32 byte = 256 bit di entropia
  const randomBytes = crypto.randomBytes(32);
  // base64url encoding produce ~43 caratteri
  return randomBytes.toString('base64url');
}

// Generazione del code_challenge con S256
function generateCodeChallenge(verifier) {
  return crypto.createHash('sha256')
    .update(verifier)
    .digest('base64url');
}

// ERRORE COMUNE: usare Math.random() — NON crittograficamente sicuro
// NON FARE: const verifier = Array.from({length: 43}, () => chars[Math.floor(Math.random() * chars.length)]).join('');
```

### S256 vs Plain

Il parametro `code_challenge_method` specifica come il `code_challenge` è derivato dal `code_verifier`:

- **`plain`**: `code_challenge = code_verifier` (nessuna trasformazione). Protegge solo se il canale di intercettazione non è lo stesso canale di scambio del token. **Deprecato in OAuth 2.1.**
- **`S256`**: `code_challenge = BASE64URL(SHA256(code_verifier))`. Il server memorizza il `code_challenge` hashato; il client invia il `code_verifier` in chiaro solo nello scambio del token (su canale TLS diretto). Anche se un attaccante intercetta il `code_challenge`, non può derivare il `code_verifier`.

### Flusso Completo Step-by-Step

```javascript
// === FASE 1: Inizializzazione (client-side) ===

const codeVerifier = generateCodeVerifier();
const codeChallenge = generateCodeChallenge(codeVerifier);
const state = crypto.randomBytes(16).toString('hex');
const nonce = crypto.randomBytes(16).toString('hex');

// Memorizzare verifier, state e nonce in sessione server-side
await storeAuthFlowState(sessionId, { codeVerifier, state, nonce });

// Costruire l'URL di autorizzazione
const authUrl = new URL('https://auth.example.com/authorize');
authUrl.searchParams.set('response_type', 'code');
authUrl.searchParams.set('client_id', CLIENT_ID);
authUrl.searchParams.set('redirect_uri', 'https://myapp.com/callback');
authUrl.searchParams.set('scope', 'openid profile email');
authUrl.searchParams.set('state', state);
authUrl.searchParams.set('nonce', nonce);
authUrl.searchParams.set('code_challenge', codeChallenge);
authUrl.searchParams.set('code_challenge_method', 'S256');

// Redirect dell'utente
res.redirect(authUrl.toString());

// === FASE 2: Callback (dopo l'autenticazione presso il provider) ===

app.get('/callback', async (req, res) => {
  const { code, state: returnedState, error } = req.query;

  // Gestire eventuali errori dal provider
  if (error) {
    return res.status(400).json({ error: req.query.error_description || error });
  }

  // Recuperare lo stato salvato
  const savedState = await getAuthFlowState(req.sessionID);

  // Verificare state (protezione CSRF)
  if (returnedState !== savedState.state) {
    return res.status(400).json({ error: 'State mismatch — possibile CSRF' });
  }

  // === FASE 3: Scambio del codice con i token ===
  const tokenResponse = await fetch('https://auth.example.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: 'https://myapp.com/callback',
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,        // Solo per client confidenziali
      code_verifier: savedState.codeVerifier  // Il server verifica SHA256(verifier) == challenge
    })
  });

  const tokens = await tokenResponse.json();

  // === FASE 4: Validazione dell'ID token ===
  const idTokenPayload = await validateIdToken(tokens.id_token, {
    jwks_uri: 'https://auth.example.com/.well-known/jwks.json',
    issuer: 'https://auth.example.com',
    expectedNonce: savedState.nonce,
    accessToken: tokens.access_token
  });

  // Pulire lo stato temporaneo del flusso
  await clearAuthFlowState(req.sessionID);

  // Creare la sessione locale
  req.session.userId = idTokenPayload.sub;
  req.session.email = idTokenPayload.email;
  res.redirect('/dashboard');
});
```

---

## Passkeys e WebAuthn — Architettura FIDO2

Le passkeys rappresentano l'evoluzione più significativa nell'autenticazione degli ultimi anni. Nel 2025, oltre 3 miliardi di passkeys sono in uso attivo a livello globale, con il 48% dei primi 100 siti web che le supportano. Le passkeys raggiungono un tasso di successo del login del 93% rispetto al 63% dei metodi tradizionali.

### Architettura FIDO2 e Componenti

FIDO2 è un framework composto da due specifiche complementari:

- **WebAuthn (Web Authentication API)** — Specifica W3C che definisce l'API JavaScript per il browser. Gestisce la comunicazione tra la Relying Party (applicazione web) e l'autenticatore tramite il browser.
- **CTAP2 (Client to Authenticator Protocol)** — Specifica FIDO Alliance che definisce il protocollo di comunicazione tra il browser (o il sistema operativo) e l'autenticatore fisico (USB, NFC, Bluetooth, integrato nel dispositivo).

```
┌──────────────┐      WebAuthn API      ┌──────────────┐      CTAP2       ┌──────────────┐
│   Relying    │◄─────────────────────►│   Browser /   │◄──────────────►│ Autenticatore │
│   Party      │   navigator.credentials│   OS Client   │  USB/NFC/BLE/  │  (Passkey)    │
│   (Server)   │   .create() / .get()  │               │  Platform      │               │
└──────────────┘                       └──────────────┘                 └──────────────┘
```

### Attestation vs Assertion

Due operazioni fondamentali caratterizzano il ciclo di vita di una passkey:

**Attestation (Registrazione)** — Il processo di creazione di una nuova credenziale. L'autenticatore genera una coppia di chiavi asimmetriche, memorizza la chiave privata internamente e restituisce la chiave pubblica al server insieme a un certificato di attestazione che prova il tipo e il modello dell'autenticatore. Il livello di attestazione può essere:

- `none` — Nessuna attestazione (raccomandato per la maggior parte dei casi consumer)
- `indirect` — Attestazione anonimizzata dal browser
- `direct` — Attestazione diretta dall'autenticatore
- `enterprise` — Attestazione enterprise con identificazione dell'autenticatore

**Assertion (Autenticazione)** — Il processo di verifica di una credenziale esistente. Il server invia una challenge, l'autenticatore firma la challenge con la chiave privata, e il server verifica la firma con la chiave pubblica memorizzata. Include un counter anti-replay che deve essere strettamente crescente.

### Discoverable Credentials e Conditional UI

Le **discoverable credentials** (precedentemente "resident keys") sono memorizzate sull'autenticatore con i metadati dell'utente (`user.id`, `user.name`). Questo permette al browser di offrire la lista delle passkeys disponibili senza che il server debba specificare `allowCredentials`, abilitando flussi "username-less".

La **Conditional UI** (Autofill-assisted) integra le passkeys nell'esperienza di autocompletamento del browser. L'utente vede le passkeys disponibili nel menu di autocompletamento accanto alle password salvate:

```html
<!-- Il campo input deve avere autocomplete="username webauthn" -->
<input type="text"
       autocomplete="username webauthn"
       placeholder="Email o passkey"
       id="loginField">
```

```javascript
// Client-side: Conditional UI con WebAuthn
async function initConditionalUI() {
  // Verificare che il browser supporti la Conditional UI
  if (!window.PublicKeyCredential ||
      !PublicKeyCredential.isConditionalMediationAvailable) {
    return; // Fallback a login tradizionale
  }

  const available = await PublicKeyCredential.isConditionalMediationAvailable();
  if (!available) return;

  // Ottenere le opzioni di autenticazione dal server (senza allowCredentials)
  const options = await fetch('/webauthn/login/options', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conditional: true })
  }).then(r => r.json());

  try {
    // mediation: 'conditional' attiva la Conditional UI
    const credential = await navigator.credentials.get({
      publicKey: options,
      mediation: 'conditional'    // Chiave: mostra nel menu autocompletamento
    });

    // Inviare l'assertion al server per la verifica
    const verifyResponse = await fetch('/webauthn/login/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credential)
    });

    if (verifyResponse.ok) {
      window.location.href = '/dashboard';
    }
  } catch (err) {
    console.error('Conditional UI WebAuthn error:', err);
  }
}
```

### Platform vs Roaming Authenticator

| Caratteristica | Platform Authenticator | Roaming Authenticator |
|---------------|----------------------|----------------------|
| **Esempio** | Touch ID, Face ID, Windows Hello | YubiKey, Google Titan, NFC key |
| **Collegamento** | Integrato nel dispositivo | Esterno, portatile |
| **Trasporto** | `internal` | `usb`, `nfc`, `ble` |
| **UX** | Biometria o PIN del dispositivo | Inserire/toccare la chiave fisica |
| **Multi-dispositivo** | Sincronizzato via cloud (Apple, Google, Microsoft) | Fisicamente portatile |
| **Resistenza phishing** | Sì (origin-bound) | Sì (origin-bound) |
| **Adozione** | 55-60% delle passkeys create | ~20% delle passkeys create |

### Pattern di Adozione Efficaci

L'esperienza dei grandi deployment (eBay, Amazon, Google) ha identificato pattern che massimizzano l'adozione delle passkeys:

1. **Enrollment post-login**: Proporre la creazione della passkey immediatamente dopo un login con password riuscito. eBay riporta che il 75% delle registrazioni di passkeys avviene con questo pattern.
2. **Spiegazione inline minima**: Una singola frase che spiega il beneficio ("Accedi più velocemente con l'impronta digitale") riduce l'abbandono del flusso dal 38% al 14%.
3. **Fallback trasparente**: Se il browser non supporta WebAuthn, l'utente non deve percepire alcuna differenza nell'esperienza di login tradizionale.
4. **Metriche reali**: Misurare la percentuale di login completati con passkey, non solo la percentuale di utenti che hanno creato una passkey.

---

## JWT — Approfondimento Tecnico

### Claim Registrati, Pubblici e Privati

La specifica JWT (RFC 7519) classifica i claim in tre categorie:

**Claim Registrati (RFC 7519, Sezione 4.1)** — Definiti dalla specifica con semantica standard:

| Claim | Nome Completo | Descrizione | Obbligatorio |
|-------|---------------|-------------|-------------|
| `iss` | Issuer | Chi ha emesso il token | Raccomandato |
| `sub` | Subject | L'entità identificata dal token | Raccomandato |
| `aud` | Audience | Destinatario previsto del token | Raccomandato |
| `exp` | Expiration Time | Timestamp Unix di scadenza | Raccomandato |
| `nbf` | Not Before | Il token non è valido prima di questo timestamp | Opzionale |
| `iat` | Issued At | Timestamp di emissione | Raccomandato |
| `jti` | JWT ID | Identificatore univoco del token (per revoca/replay) | Opzionale |

**Claim Pubblici** — Registrati nel IANA JSON Web Token Claims Registry per evitare collisioni. Esempi: `name`, `email`, `email_verified`, `picture` (definiti da OIDC).

**Claim Privati** — Definiti dall'applicazione per scopi specifici. Devono usare namespace per evitare collisioni con claim pubblici o di altre applicazioni.

### Confronto Algoritmi di Firma

| Algoritmo | Tipo | Chiave | Dimensione Firma | Prestazioni | Uso Raccomandato |
|-----------|------|--------|-------------------|-------------|-----------------|
| **HS256** | Simmetrico | HMAC-SHA256 | 32 byte | Molto veloce | Monoliti, sistemi chiusi |
| **HS384** | Simmetrico | HMAC-SHA384 | 48 byte | Veloce | Quando serve SHA-384 |
| **HS512** | Simmetrico | HMAC-SHA512 | 64 byte | Veloce | Massima sicurezza simmetrica |
| **RS256** | Asimmetrico | RSA-PKCS1-v1_5 + SHA-256 | 256 byte | Lento (firma), veloce (verifica) | Multi-servizio, OIDC |
| **RS384** | Asimmetrico | RSA-PKCS1-v1_5 + SHA-384 | 256 byte | Lento | Requisiti di compliance |
| **RS512** | Asimmetrico | RSA-PKCS1-v1_5 + SHA-512 | 256 byte | Lento | Massima sicurezza RSA |
| **ES256** | Asimmetrico | ECDSA P-256 + SHA-256 | 64 byte | Veloce | Mobile, IoT, dimensione ridotta |
| **ES384** | Asimmetrico | ECDSA P-384 + SHA-384 | 96 byte | Medio | Compliance FIPS |
| **EdDSA** | Asimmetrico | Ed25519 / Ed448 | 64 byte | Molto veloce | Nuovi progetti, massima performance |
| **PS256** | Asimmetrico | RSA-PSS + SHA-256 | 256 byte | Lento | Maggiore sicurezza di RS256 |

**Raccomandazione**: Per nuovi progetti, preferire **ES256** (buon compromesso dimensione/prestazioni) o **EdDSA** (prestazioni superiori, supporto crescente). Evitare HS256 per sistemi distribuiti o multi-tenant.

### JWE — JSON Web Encryption

Mentre JWS (JSON Web Signature) garantisce l'integrità e l'autenticità del token, **JWE** (JSON Web Encryption, RFC 7516) aggiunge la **confidenzialità**: il contenuto del token è cifrato e leggibile solo dal destinatario. Un JWE è composto da cinque parti separate da punti:

```
BASE64URL(Header) .
BASE64URL(Encrypted Key) .
BASE64URL(IV) .
BASE64URL(Ciphertext) .
BASE64URL(Authentication Tag)
```

1. **Header** — Contiene l'algoritmo di gestione della chiave (`alg`) e l'algoritmo di cifratura del contenuto (`enc`)
2. **Encrypted Key** — La Content Encryption Key (CEK) cifrata con la chiave pubblica del destinatario
3. **Initialization Vector (IV)** — Valore random per la cifratura del contenuto
4. **Ciphertext** — Il payload cifrato
5. **Authentication Tag** — Tag di autenticazione per verificare l'integrità del ciphertext

```javascript
const jose = require('jose');

// === Cifratura con JWE ===
async function createEncryptedToken(payload, recipientPublicKey) {
  const token = await new jose.EncryptJWT(payload)
    .setProtectedHeader({
      alg: 'RSA-OAEP-256',       // Algoritmo di key wrapping
      enc: 'A256GCM',            // Algoritmo di content encryption
      typ: 'JWT'
    })
    .setIssuedAt()
    .setExpirationTime('15m')
    .setIssuer('auth.example.com')
    .encrypt(recipientPublicKey);

  return token;
}

// === Decifratura ===
async function decryptToken(encryptedToken, privateKey) {
  const { payload } = await jose.jwtDecrypt(encryptedToken, privateKey, {
    issuer: 'auth.example.com',
    contentEncryptionAlgorithms: ['A256GCM'],
    keyManagementAlgorithms: ['RSA-OAEP-256']
  });

  return payload;
}

// === Nested JWT: firmato e poi cifrato (massima sicurezza) ===
async function createNestedJWT(payload, signingKey, encryptionKey) {
  // 1. Firmare il payload con JWS
  const signedToken = await new jose.SignJWT(payload)
    .setProtectedHeader({ alg: 'ES256', typ: 'JWT' })
    .setIssuedAt()
    .setExpirationTime('15m')
    .sign(signingKey);

  // 2. Cifrare il JWS con JWE
  const nestedToken = await new jose.CompactEncrypt(
    new TextEncoder().encode(signedToken)
  )
    .setProtectedHeader({
      alg: 'RSA-OAEP-256',
      enc: 'A256GCM',
      cty: 'JWT'                  // Content-Type: indica che il contenuto è un JWT
    })
    .encrypt(encryptionKey);

  return nestedToken;
}
```

### RFC 8725 — Best Practice per JWT

RFC 8725 (JSON Web Token Best Current Practices) codifica le lezioni apprese dagli attacchi reali ai JWT:

1. **Specificare sempre `alg` nell'allow-list** — Mai accettare `alg: "none"`. Attacchi documentati sfruttano varianti di case (`None`, `NONE`, `noNe`) per aggirare deny-list.
2. **Validare `typ` nel header** — Se l'applicazione emette sia access token che altri tipi di JWT, verificare che il `typ` corrisponda al tipo atteso.
3. **Non fidarsi del payload prima della verifica** — Mai decodificare e usare i claim senza prima verificare la firma.
4. **Limitare i claim nel payload** — Non includere dati sensibili (PII, credenziali, dati di pagamento) nel payload JWS. Se necessario, usare JWE.
5. **Usare `jti` per prevenire replay** — Registrare i `jti` dei token consumati in una cache con TTL pari alla durata del token.
6. **Chiavi di dimensione adeguata** — RSA: almeno 2048 bit. ECDSA P-256: 256 bit. Ed25519: 256 bit. Chiavi HMAC: almeno pari alla dimensione dell'hash output (256 bit per HS256).

---

## Gestione Avanzata delle Sessioni

### Sliding Sessions vs Absolute Timeout

Due strategie di timeout si complementano per bilanciare sicurezza e usabilità:

**Sliding Session (Sessione Scorrevole)** — Il timeout si resetta ad ogni attività dell'utente. Se l'utente è attivo, la sessione non scade mai per inattività. Questo offre un'esperienza utente fluida ma richiede un timeout assoluto come limite superiore.

**Absolute Timeout (Timeout Assoluto)** — La sessione scade dopo un periodo fisso dal login, indipendentemente dall'attività. Anche un utente costantemente attivo dovrà ri-autenticarsi. Essenziale per limitare il danno in caso di furto della sessione.

```javascript
// Implementazione combinata sliding + absolute timeout
const SLIDING_TIMEOUT = 30 * 60 * 1000;      // 30 minuti di inattività
const ABSOLUTE_TIMEOUT = 12 * 60 * 60 * 1000; // 12 ore dal login

function advancedSessionMiddleware(req, res, next) {
  if (!req.session?.userId) return next();

  const now = Date.now();
  const loginTime = req.session.loginAt;
  const lastActive = req.session.lastActivity || loginTime;

  // Timeout assoluto: forza re-autenticazione
  if (now - loginTime > ABSOLUTE_TIMEOUT) {
    const reason = 'absolute_timeout';
    return req.session.destroy(() => {
      res.status(401).json({
        error: 'Sessione scaduta',
        reason,
        message: 'Durata massima della sessione raggiunta. Effettua nuovamente il login.'
      });
    });
  }

  // Sliding timeout: scade per inattività
  if (now - lastActive > SLIDING_TIMEOUT) {
    const reason = 'idle_timeout';
    return req.session.destroy(() => {
      res.status(401).json({
        error: 'Sessione scaduta',
        reason,
        message: 'Sessione scaduta per inattività.'
      });
    });
  }

  // Aggiornare il timestamp dell'ultima attività (sliding)
  req.session.lastActivity = now;

  // Calcolare il tempo rimanente per il client
  const remainingAbsolute = ABSOLUTE_TIMEOUT - (now - loginTime);
  const remainingSliding = SLIDING_TIMEOUT;
  res.setHeader('X-Session-Expires-In',
    Math.min(remainingAbsolute, remainingSliding).toString()
  );

  next();
}
```

### Cookie Prefixes: __Host- e __Secure-

I prefissi dei cookie sono un meccanismo di sicurezza del browser che impone vincoli sulla configurazione del cookie:

**`__Host-` prefix** — Il cookie DEVE avere `Secure: true`, NON deve avere un attributo `Domain` (è implicito il dominio corrente, senza inclusione dei sottodomini), e DEVE avere `Path: /`. Questo previene attacchi dove un sottodominio compromesso inietta un cookie che sovrascrive quello dell'applicazione principale.

**`__Secure-` prefix** — Il cookie DEVE avere `Secure: true`. Meno restrittivo di `__Host-`, permette di specificare un `Domain` e un `Path` arbitrario.

```javascript
// Cookie di sessione con __Host- prefix (massima sicurezza)
res.cookie('__Host-session', sessionId, {
  httpOnly: true,
  secure: true,
  sameSite: 'lax',
  path: '/',
  maxAge: 24 * 60 * 60 * 1000
  // Nota: NON specificare 'domain' con __Host-
});

// Cookie con __Secure- prefix (quando serve specificare il dominio)
res.cookie('__Secure-prefs', preferencesToken, {
  httpOnly: true,
  secure: true,
  sameSite: 'lax',
  domain: '.example.com',       // Condiviso tra sottodomini
  path: '/',
  maxAge: 30 * 24 * 60 * 60 * 1000
});
```

### Session Binding e Fingerprinting

Il binding della sessione ad attributi aggiuntivi del client rende più difficile il furto della sessione, anche se l'attaccante ottiene il cookie:

```javascript
// Generare un fingerprint della sessione basato su attributi stabili del client
function generateSessionFingerprint(req) {
  const components = [
    req.headers['user-agent'] || '',
    req.headers['accept-language'] || '',
    req.ip
  ];

  return crypto.createHash('sha256')
    .update(components.join('|'))
    .digest('hex');
}

// Verificare il fingerprint ad ogni richiesta
function sessionBindingMiddleware(req, res, next) {
  if (!req.session?.userId) return next();

  const currentFingerprint = generateSessionFingerprint(req);

  if (req.session.fingerprint && req.session.fingerprint !== currentFingerprint) {
    // Il fingerprint è cambiato — possibile furto della sessione
    securityLogger('SESSION_FINGERPRINT_MISMATCH', {
      userId: req.session.userId,
      expected: req.session.fingerprint,
      received: currentFingerprint,
      ip: req.ip
    });

    // Invalidare la sessione per sicurezza
    return req.session.destroy(() => {
      res.status(401).json({
        error: 'Sessione invalidata per motivi di sicurezza'
      });
    });
  }

  next();
}
```

### Store Distribuiti per le Sessioni

In architetture multi-istanza, lo store delle sessioni deve essere condiviso tra i nodi:

| Store | Latenza | Persistenza | Scalabilità | Uso Raccomandato |
|-------|---------|-------------|-------------|------------------|
| **Redis** | ~1ms | Configurabile (AOF/RDB) | Cluster, Sentinel | Standard per la maggior parte dei casi |
| **Memcached** | ~1ms | Nessuna | Hash ring | Cache temporanea, tolleranza alla perdita |
| **PostgreSQL** | ~5ms | Sì | Read replicas | Quando Redis non è disponibile |
| **DynamoDB** | ~5ms | Sì | Auto-scaling | Ambiente AWS, carico variabile |
| **MongoDB** | ~3ms | Sì | Sharding | Quando già in uso nel progetto |

---

## ReBAC e Modelli di Autorizzazione Avanzati

Oltre a RBAC e ABAC, un terzo modello di autorizzazione ha guadagnato prominenza: **ReBAC** (Relationship-Based Access Control), ispirato dal sistema Zanzibar di Google.

### ReBAC — Relationship-Based Access Control

ReBAC definisce i permessi sulla base delle **relazioni** tra soggetti e risorse, piuttosto che su ruoli statici o attributi. Il modello è stato formalizzato da Google nel paper "Zanzibar: Google's Consistent, Global Authorization System" (2019), dove viene descritto il sistema che gestisce i permessi per tutti i prodotti Google (Drive, Docs, Calendar, Cloud IAM).

Il concetto fondamentale è semplice: "Mario può modificare il Documento X perché Mario è l'owner del Documento X" oppure "Maria può leggere il Documento X perché Maria è membro del Team Y e il Team Y è viewer della Cartella Z che contiene il Documento X".

```
// Schema delle relazioni in SpiceDB (sintassi Zanzibar-like)
definition user {}

definition team {
  relation member: user
}

definition folder {
  relation owner: user
  relation viewer: user | team#member
  relation parent: folder

  permission view = viewer + owner + parent->view
  permission edit = owner
}

definition document {
  relation owner: user
  relation parent: folder

  permission view = owner + parent->view
  permission edit = owner + parent->edit
  permission delete = owner
}
```

```javascript
// Esempio di query con SpiceDB (client JavaScript)
const { v1 } = require('@authzed/authzed-node');

const client = v1.NewClient('my-api-token', 'localhost:50051');

// Scrivere una relazione
await client.writeRelationships({
  updates: [{
    operation: v1.RelationshipUpdate_Operation.CREATE,
    relationship: {
      resource: { objectType: 'document', objectId: 'doc_123' },
      relation: 'owner',
      subject: { object: { objectType: 'user', objectId: 'mario' } }
    }
  }]
});

// Verificare un permesso
const result = await client.checkPermission({
  resource: { objectType: 'document', objectId: 'doc_123' },
  permission: 'view',
  subject: { object: { objectType: 'user', objectId: 'maria' } }
});

if (result.permissionship === v1.CheckPermissionResponse_Permissionship.HAS_PERMISSION) {
  // Maria può vedere il documento
}
```

### Confronto RBAC vs ABAC vs ReBAC

| Dimensione | RBAC | ABAC | ReBAC |
|-----------|------|------|-------|
| **Modello decisionale** | Ruolo dell'utente | Attributi di soggetto, risorsa, contesto | Relazioni tra entità |
| **Esempio** | "Gli admin possono cancellare" | "I manager del dipartimento X possono approvare documenti del dipartimento X" | "Mario può modificare perché è owner" |
| **Granularità** | Grossolana (per ruolo) | Fine (per attributo) | Fine (per relazione) |
| **Complessità** | Bassa | Media-Alta | Alta |
| **Scalabilità** | Limitata (role explosion) | Buona | Eccellente |
| **Caso d'uso ideale** | Applicazioni con ruoli ben definiti | Policy basate su contesto | Condivisione di risorse, gerarchie, collaborazione |
| **Strumenti** | Middleware custom, CASL | OPA, Cedar | SpiceDB, OpenFGA, Ory Keto |
| **Standard** | Nessuno formale | XACML, ALFA | Paper Zanzibar (Google) |
| **Mutabilità** | Statico (cambio ruolo = cambio permessi) | Dinamico (dipende da attributi runtime) | Dinamico (dipende da relazioni runtime) |

### Quando Usare Ciascun Modello

- **RBAC**: Applicazioni interne con ruoli chiari e stabili (admin, editor, viewer). La maggior parte delle applicazioni CRUD standard.
- **ABAC**: Quando le decisioni di accesso dipendono dal contesto (orario, dipartimento, livello di sicurezza, geolocalizzazione). Compliance e requisiti regolamentari complessi.
- **ReBAC**: Quando gli utenti condividono risorse tra loro (Google Docs, Dropbox, Notion). Gerarchie complesse (organizzazione → team → progetto → documento). Permessi ereditati attraverso relazioni.
- **Ibrido**: La maggior parte dei sistemi reali combina i modelli. RBAC per i permessi di base, ABAC per le policy contestuali, ReBAC per la condivisione e la collaborazione.

---

## Pattern Avanzati di Autenticazione API

### Progettazione degli Scope OAuth

Gli **scope** definiscono i limiti dell'accesso concesso a un client. Una progettazione efficace degli scope è fondamentale per applicare il principio del privilegio minimo nelle API:

```javascript
// Progettazione gerarchica degli scope
const SCOPE_HIERARCHY = {
  // Pattern: risorsa:azione
  'users:read':    { description: 'Leggere profili utente' },
  'users:write':   { description: 'Modificare profili utente', implies: ['users:read'] },
  'users:admin':   { description: 'Gestire utenti', implies: ['users:write'] },

  'posts:read':    { description: 'Leggere articoli' },
  'posts:write':   { description: 'Creare e modificare articoli', implies: ['posts:read'] },
  'posts:delete':  { description: 'Cancellare articoli', implies: ['posts:write'] },

  'billing:read':  { description: 'Visualizzare fatturazione' },
  'billing:write': { description: 'Modificare piano e pagamenti', implies: ['billing:read'] },

  // Scope compositi per casi comuni
  'api:read':      { description: 'Accesso in lettura completo', implies: ['users:read', 'posts:read'] },
  'api:write':     { description: 'Accesso in scrittura completo', implies: ['api:read', 'users:write', 'posts:write'] }
};

// Middleware di verifica scope
function requireScope(...requiredScopes) {
  return (req, res, next) => {
    const tokenScopes = req.user?.scope?.split(' ') || [];

    // Espandere gli scope impliciti
    const effectiveScopes = new Set();
    tokenScopes.forEach(scope => {
      effectiveScopes.add(scope);
      const hierarchy = SCOPE_HIERARCHY[scope];
      if (hierarchy?.implies) {
        hierarchy.implies.forEach(s => effectiveScopes.add(s));
      }
    });

    const hasRequiredScopes = requiredScopes.every(s => effectiveScopes.has(s));

    if (!hasRequiredScopes) {
      return res.status(403).json({
        error: 'insufficient_scope',
        required: requiredScopes,
        granted: Array.from(effectiveScopes)
      });
    }

    next();
  };
}

// Uso nelle route
app.get('/api/users/:id', requireScope('users:read'), getUser);
app.put('/api/users/:id', requireScope('users:write'), updateUser);
app.delete('/api/users/:id', requireScope('users:admin'), deleteUser);
```

### Pattern API Gateway per l'Autenticazione

In architetture a microservizi, l'API gateway centralizza la logica di autenticazione, permettendo ai servizi interni di concentrarsi sulla logica di business:

```
┌─────────┐       ┌──────────────┐       ┌─────────────┐
│  Client  │──────►│  API Gateway │──────►│ Servizio A  │
│          │  JWT  │              │ Header│ (interno)   │
│          │       │ 1. Validare  │ x-user│             │
│          │       │    JWT       │ x-role│             │
│          │       │ 2. Rate limit│       │             │
│          │       │ 3. Scoping   │       │             │
│          │       │ 4. Forward   │       │             │
│          │       │    user ctx  │       │             │
│          │       │              │──────►│ Servizio B  │
│          │       │              │ Header│ (interno)   │
│          │       │              │ x-user│             │
└─────────┘       └──────────────┘       └─────────────┘
```

```javascript
// API Gateway: validazione centralizzata e forwarding del contesto utente
async function gatewayAuthMiddleware(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) {
    return res.status(401).json({ error: 'Token mancante' });
  }

  try {
    const decoded = await verifyToken(token);

    // Impostare header interni per i microservizi downstream
    req.headers['x-user-id'] = decoded.sub;
    req.headers['x-user-role'] = decoded.role;
    req.headers['x-user-email'] = decoded.email;
    req.headers['x-auth-scope'] = decoded.scope;
    req.headers['x-request-id'] = crypto.randomUUID();

    // Rimuovere l'header Authorization per i servizi interni
    // (i servizi interni si fidano degli header x-user-*)
    delete req.headers.authorization;

    next();
  } catch (error) {
    res.status(401).json({ error: 'Token non valido' });
  }
}

// Nei microservizi interni: fidarsi degli header dal gateway
function internalAuthMiddleware(req, res, next) {
  const userId = req.headers['x-user-id'];
  if (!userId) {
    return res.status(401).json({ error: 'Contesto utente mancante' });
  }

  req.user = {
    id: userId,
    role: req.headers['x-user-role'],
    email: req.headers['x-user-email'],
    scope: req.headers['x-auth-scope']
  };

  next();
}
```

### DPoP per API Pubbliche

Per API pubbliche dove il furto del token è un rischio concreto, DPoP (Demonstrating Proof-of-Possession) lega il token al client che lo ha richiesto. Il server verifica che ogni richiesta includa un proof firmato dalla stessa chiave associata al token:

```javascript
// Verifica DPoP lato server
async function verifyDPoP(req) {
  const dpopHeader = req.headers['dpop'];
  const accessToken = req.headers.authorization?.replace('DPoP ', '');

  if (!dpopHeader || !accessToken) {
    throw new Error('DPoP proof o access token mancante');
  }

  // 1. Decodificare il DPoP proof senza verificare (per estrarre jwk)
  const { payload: proofPayload, protectedHeader } = await jose.jwtVerify(
    dpopHeader,
    jose.EmbeddedJWK,                   // La chiave pubblica è nel header
    { typ: 'dpop+jwt', maxTokenAge: '60s' }
  );

  // 2. Verificare htm (HTTP method) e htu (HTTP URI)
  if (proofPayload.htm !== req.method) {
    throw new Error('DPoP htm mismatch');
  }
  const requestUri = `${req.protocol}://${req.get('host')}${req.path}`;
  if (proofPayload.htu !== requestUri) {
    throw new Error('DPoP htu mismatch');
  }

  // 3. Verificare ath (hash dell'access token)
  const expectedAth = crypto.createHash('sha256')
    .update(accessToken)
    .digest('base64url');
  if (proofPayload.ath !== expectedAth) {
    throw new Error('DPoP ath mismatch');
  }

  // 4. Verificare che jti sia unico (prevenzione replay)
  const jtiUsed = await checkAndStoreJti(proofPayload.jti, 60);
  if (jtiUsed) {
    throw new Error('DPoP proof riutilizzato');
  }

  // 5. Verificare che la chiave pubblica nel proof corrisponda al token
  const tokenPayload = jwt.decode(accessToken);
  const proofJwkThumbprint = await jose.calculateJwkThumbprint(protectedHeader.jwk);
  if (tokenPayload.cnf?.jkt !== proofJwkThumbprint) {
    throw new Error('DPoP key binding mismatch');
  }

  return tokenPayload;
}
```

---

## Multi-Tenancy e Autenticazione

L'autenticazione in contesti multi-tenant aggiunge una dimensione di complessità: oltre a verificare *chi* è l'utente, il sistema deve determinare *a quale tenant* appartiene e garantire l'isolamento completo tra tenant.

### Tenant Resolution

Il primo passo è determinare il tenant della richiesta. Esistono diversi pattern:

```javascript
// Pattern 1: Tenant dal sottodominio
// acme.myapp.com → tenant: acme
function resolveTenantFromSubdomain(req) {
  const host = req.hostname;
  const parts = host.split('.');
  if (parts.length >= 3) {
    return parts[0];  // acme.myapp.com → 'acme'
  }
  return null;
}

// Pattern 2: Tenant dall'header personalizzato
// X-Tenant-ID: acme
function resolveTenantFromHeader(req) {
  return req.headers['x-tenant-id'];
}

// Pattern 3: Tenant dal path
// /t/acme/api/users → tenant: acme
function resolveTenantFromPath(req) {
  const match = req.path.match(/^\/t\/([^/]+)/);
  return match?.[1];
}

// Pattern 4: Tenant dal JWT claim
function resolveTenantFromToken(req) {
  return req.user?.['https://myapp.com/tenant_id'];
}

// Middleware composito di risoluzione tenant
function tenantResolutionMiddleware(req, res, next) {
  const tenant = resolveTenantFromSubdomain(req)
    || resolveTenantFromHeader(req)
    || resolveTenantFromPath(req)
    || resolveTenantFromToken(req);

  if (!tenant) {
    return res.status(400).json({ error: 'Tenant non identificato' });
  }

  req.tenantId = tenant;
  next();
}
```

### JWT con Claim Tenant

Nei sistemi multi-tenant, il JWT deve includere informazioni sul tenant per permettere la verifica dell'accesso senza query aggiuntive al database:

```javascript
// Generazione del token con claim tenant
function generateMultiTenantToken(user, tenant) {
  return jwt.sign({
    sub: user.id,
    email: user.email,
    role: user.role,
    tenant_id: tenant.id,
    tenant_plan: tenant.plan,                  // Per feature gating
    tenant_permissions: user.tenantPermissions  // Permessi specifici del tenant
  }, process.env.JWT_SECRET, {
    expiresIn: '15m',
    issuer: `https://${tenant.slug}.myapp.com`
  });
}

// Middleware di isolamento tenant
function tenantIsolationMiddleware(req, res, next) {
  if (!req.user?.tenant_id) {
    return res.status(403).json({ error: 'Contesto tenant mancante nel token' });
  }

  // Verificare che il tenant nel token corrisponda al tenant della richiesta
  if (req.tenantId && req.user.tenant_id !== req.tenantId) {
    securityLogger('TENANT_MISMATCH', {
      userId: req.user.sub,
      tokenTenant: req.user.tenant_id,
      requestTenant: req.tenantId
    });
    return res.status(403).json({ error: 'Accesso cross-tenant non consentito' });
  }

  // Impostare il contesto tenant per le query database
  req.tenantContext = {
    id: req.user.tenant_id,
    plan: req.user.tenant_plan
  };

  next();
}
```

### Pattern di Isolamento dei Dati

| Pattern | Isolamento | Complessità | Costo | Caso d'Uso |
|---------|-----------|-------------|-------|-----------|
| **Colonna tenant_id** | Basso (applicativo) | Bassa | Basso | SaaS standard, startup |
| **Schema per tenant** | Medio (database) | Media | Medio | Compliance moderata |
| **Database per tenant** | Alto (infrastrutturale) | Alta | Alto | Healthcare, finanza, governo |
| **Ibrido** | Variabile | Media-Alta | Variabile | Tier-based (free=shared, enterprise=dedicated) |

```javascript
// Esempio: isolamento con colonna tenant_id e middleware automatico
// Prisma middleware per filtraggio automatico per tenant
function prismaMultiTenantMiddleware(tenantId) {
  return async (params, next) => {
    // Aggiungere filtro tenant_id a tutte le query
    if (params.action === 'findMany' || params.action === 'findFirst') {
      params.args.where = { ...params.args.where, tenantId };
    }
    if (params.action === 'create') {
      params.args.data = { ...params.args.data, tenantId };
    }
    if (params.action === 'update' || params.action === 'delete') {
      params.args.where = { ...params.args.where, tenantId };
    }
    return next(params);
  };
}
```

### IdP per Tenant

Per applicazioni enterprise, ogni tenant può richiedere il proprio Identity Provider (IdP). L'applicazione deve supportare la configurazione OIDC/SAML per tenant:

```javascript
// Configurazione IdP dinamica per tenant
async function getTenantIdPConfig(tenantId) {
  const tenant = await getTenantById(tenantId);

  if (tenant.authMethod === 'oidc') {
    // Recuperare la configurazione OIDC del tenant
    const discoveryUrl = `${tenant.idpIssuer}/.well-known/openid-configuration`;
    const oidcConfig = await fetch(discoveryUrl).then(r => r.json());

    return {
      type: 'oidc',
      clientId: tenant.idpClientId,
      clientSecret: tenant.idpClientSecret,
      authorizationEndpoint: oidcConfig.authorization_endpoint,
      tokenEndpoint: oidcConfig.token_endpoint,
      jwksUri: oidcConfig.jwks_uri,
      issuer: oidcConfig.issuer
    };
  }

  if (tenant.authMethod === 'saml') {
    return {
      type: 'saml',
      ssoUrl: tenant.samlSsoUrl,
      certificate: tenant.samlCertificate,
      entityId: tenant.samlEntityId
    };
  }

  // Fallback: autenticazione locale (email + password)
  return { type: 'local' };
}
```

---

## SSO — Pattern di Implementazione Avanzati

### SP-Initiated vs IdP-Initiated SSO

Due flussi fondamentali caratterizzano le implementazioni SSO:

**SP-Initiated (Service Provider Initiated)** — L'utente accede prima all'applicazione (SP), che lo reindirizza all'IdP per l'autenticazione. È il flusso più comune e più sicuro, perché l'SP genera e verifica un `state` o `RelayState` anti-CSRF.

**IdP-Initiated** — L'utente si autentica prima sull'IdP (ad esempio un portale aziendale) e poi seleziona l'applicazione. L'IdP invia una SAMLResponse o un token all'SP senza che l'SP abbia iniziato il flusso. Questo flusso è più vulnerabile ad attacchi di replay e CSRF perché non c'è un `state` generato dall'SP. OWASP e le best practice OIDC sconsigliano l'IdP-Initiated SSO quando possibile.

### Session Propagation

Quando un utente si autentica tramite SSO, la sessione deve essere propagata tra le applicazioni dell'ecosistema:

```javascript
// Pattern: sessione centralizzata con token di sessione SSO
class SSOSessionManager {
  constructor(redisClient) {
    this.redis = redisClient;
  }

  // Creare una sessione SSO globale dopo l'autenticazione sul IdP
  async createGlobalSession(userId, idpSessionId) {
    const ssoSessionId = crypto.randomUUID();

    await this.redis.hSet(`sso:${ssoSessionId}`, {
      userId,
      idpSessionId,
      createdAt: Date.now().toString(),
      applications: JSON.stringify([])      // App che hanno creato sessioni locali
    });

    await this.redis.expire(`sso:${ssoSessionId}`, 8 * 60 * 60);  // 8 ore
    return ssoSessionId;
  }

  // Registrare una sessione locale di un'applicazione
  async registerAppSession(ssoSessionId, appId, appSessionId) {
    const session = await this.redis.hGetAll(`sso:${ssoSessionId}`);
    if (!session.userId) throw new Error('Sessione SSO non trovata');

    const apps = JSON.parse(session.applications);
    apps.push({ appId, appSessionId, registeredAt: Date.now() });

    await this.redis.hSet(`sso:${ssoSessionId}`, 'applications', JSON.stringify(apps));
  }

  // Single Logout: invalidare tutte le sessioni
  async globalLogout(ssoSessionId) {
    const session = await this.redis.hGetAll(`sso:${ssoSessionId}`);
    if (!session.userId) return;

    const apps = JSON.parse(session.applications);

    // Notificare ogni applicazione di invalidare la sessione locale
    for (const app of apps) {
      await this.notifyAppLogout(app.appId, app.appSessionId);
    }

    // Cancellare la sessione SSO globale
    await this.redis.del(`sso:${ssoSessionId}`);
  }

  async notifyAppLogout(appId, sessionId) {
    // Inviare richiesta di logout all'applicazione
    // (Back-Channel Logout OIDC o SAML SLO)
    const app = await getAppConfig(appId);
    await fetch(app.logoutUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        logout_token: await createLogoutToken(sessionId)
      })
    });
  }
}
```

### Single Logout (SLO)

OIDC definisce due meccanismi di logout:

**Front-Channel Logout** — L'IdP carica iframe nascosti con gli URL di logout di tutte le applicazioni nella pagina di logout. Semplice ma inaffidabile (blocco dei cookie di terze parti, browser che non caricano gli iframe).

**Back-Channel Logout (Raccomandato)** — L'IdP invia richieste HTTP POST direttamente ai server delle applicazioni con un `logout_token` JWT. Più affidabile e non dipende dal browser dell'utente.

---

## Strategie MFA/2FA Avanzate

### MFA Adattiva e Risk-Based

L'MFA adattiva (o risk-based) richiede il secondo fattore solo quando il livello di rischio della richiesta supera una soglia, riducendo l'attrito per gli utenti in contesti a basso rischio:

```javascript
// Engine di valutazione del rischio per MFA adattiva
function calculateRiskScore(req, user) {
  let score = 0;
  const factors = [];

  // Dispositivo sconosciuto (+30 punti)
  const deviceFingerprint = generateDeviceFingerprint(req);
  if (!user.knownDevices.includes(deviceFingerprint)) {
    score += 30;
    factors.push('unknown_device');
  }

  // IP sconosciuto (+20 punti)
  if (!user.knownIPs.includes(req.ip)) {
    score += 20;
    factors.push('unknown_ip');
  }

  // Geolocalizzazione anomala (+25 punti)
  const geoLocation = geoip.lookup(req.ip);
  if (geoLocation && user.lastCountry && geoLocation.country !== user.lastCountry) {
    score += 25;
    factors.push('geo_anomaly');
  }

  // Viaggio impossibile (+40 punti)
  if (user.lastLoginAt && user.lastLoginIP) {
    const timeDiff = Date.now() - user.lastLoginAt;
    const distance = calculateDistance(geoip.lookup(user.lastLoginIP), geoLocation);
    const maxPossibleDistance = timeDiff / 1000 / 3600 * 900;  // 900 km/h (aereo)
    if (distance > maxPossibleDistance) {
      score += 40;
      factors.push('impossible_travel');
    }
  }

  // Orario insolito (+15 punti)
  const hour = new Date().getHours();
  if (hour < 6 || hour > 23) {
    score += 15;
    factors.push('unusual_hour');
  }

  // Tentativi falliti recenti (+20 punti per tentativo)
  score += user.recentFailedAttempts * 20;
  if (user.recentFailedAttempts > 0) {
    factors.push('recent_failures');
  }

  return { score, factors };
}

// Middleware MFA adattiva
async function adaptiveMfaMiddleware(req, res, next) {
  const MFA_THRESHOLD = 50;       // Richiedere MFA se score >= 50
  const BLOCK_THRESHOLD = 90;     // Bloccare se score >= 90

  const { score, factors } = calculateRiskScore(req, req.user);

  if (score >= BLOCK_THRESHOLD) {
    securityLogger('LOGIN_BLOCKED_HIGH_RISK', {
      userId: req.user.id,
      score,
      factors,
      ip: req.ip
    });
    return res.status(403).json({
      error: 'Accesso bloccato per attività sospetta',
      supportCode: crypto.randomBytes(8).toString('hex')
    });
  }

  if (score >= MFA_THRESHOLD && !req.session.mfaVerified) {
    return res.status(403).json({
      error: 'mfa_required',
      mfaToken: await createMfaChallenge(req.user.id),
      riskFactors: factors
    });
  }

  next();
}
```

### Step-Up Authentication

Lo step-up authentication richiede una ri-autenticazione più forte per operazioni sensibili, anche se l'utente è già autenticato:

```javascript
// Step-up authentication per operazioni critiche
function requireStepUp(maxAge = 300) {  // 5 minuti
  return async (req, res, next) => {
    const lastStepUp = req.session.lastStepUpAt;

    // Verificare che lo step-up sia recente
    if (!lastStepUp || (Date.now() - lastStepUp > maxAge * 1000)) {
      return res.status(403).json({
        error: 'step_up_required',
        message: 'Questa operazione richiede una ri-autenticazione',
        methods: await getAvailableStepUpMethods(req.user.id)
        // ['totp', 'webauthn', 'password', 'email_code']
      });
    }

    next();
  };
}

// Operazioni che richiedono step-up
app.put('/account/email', requireStepUp(300), changeEmail);
app.delete('/account', requireStepUp(60), deleteAccount);          // 1 minuto
app.post('/billing/payment-method', requireStepUp(300), addPaymentMethod);
app.post('/admin/role-change', requireStepUp(120), changeUserRole); // 2 minuti
```

### FIDO2 come MFA Resistente al Phishing

NIST SP 800-63B (aggiornamento 2024) classifica WebAuthn/FIDO2 come autenticatore **phishing-resistant**, il livello più alto di garanzia per l'MFA. A differenza di TOTP o SMS, le passkeys sono vincolate all'origin (dominio) del sito web, rendendo impossibile l'invio delle credenziali a un sito di phishing. Un sito `phishing-example.com` non può attivare le credenziali registrate per `example.com`, nemmeno se l'interfaccia è visivamente identica.

---

## Security Headers per l'Autenticazione

### CORS per Autenticazione Cookie-Based

La configurazione CORS è critica per le applicazioni che usano cookie per l'autenticazione. Errori comuni portano a vulnerabilità o a malfunzionamenti dell'autenticazione cross-origin:

```javascript
const cors = require('cors');

// Configurazione CORS per autenticazione con cookie
app.use(cors({
  // MAI usare '*' con credentials — il browser lo rifiuta
  origin: function(origin, callback) {
    const allowedOrigins = [
      'https://app.example.com',
      'https://admin.example.com',
      'https://staging.example.com'
    ];

    // Permettere richieste senza origin (server-to-server, curl)
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, origin);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,              // Necessario per inviare/ricevere cookie
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-CSRF-Token'],
  exposedHeaders: ['X-Session-Expires-In'],
  maxAge: 86400                    // Preflight cache: 24 ore
}));
```

**Regole fondamentali:**
- `Access-Control-Allow-Origin: *` e `Access-Control-Allow-Credentials: true` sono mutuamente esclusivi. Il browser rifiuta questa combinazione.
- Con `credentials: true`, l'origin deve essere esplicita (non wildcard).
- `SameSite: None` richiede `Secure: true` ed è necessario per cookie cross-site (ma espone a CSRF — usare token CSRF aggiuntivo).

### Content Security Policy per Pagine di Autenticazione

Le pagine di login e registrazione richiedono una CSP particolarmente restrittiva per prevenire l'iniezione di script che potrebbero rubare le credenziali:

```javascript
// CSP restrittiva per pagine di autenticazione
app.use('/auth/*', (req, res, next) => {
  const nonce = crypto.randomBytes(16).toString('base64');
  res.locals.cspNonce = nonce;

  res.setHeader('Content-Security-Policy', [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}'`,     // Solo script con nonce
    "style-src 'self' 'unsafe-inline'",        // Inline styles per i form
    "img-src 'self' data: https://cdn.example.com",
    "font-src 'self' https://fonts.gstatic.com",
    "connect-src 'self'",                      // Solo API del proprio dominio
    "frame-src 'none'",                        // Nessun iframe
    "object-src 'none'",                       // Nessun plugin
    "base-uri 'self'",                         // Prevenire base tag injection
    "form-action 'self'",                      // Form inviabili solo al proprio dominio
    "frame-ancestors 'none'",                  // Non incorporabile in iframe
    "upgrade-insecure-requests"
  ].join('; '));

  // Header aggiuntivi per le pagine di autenticazione
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'no-referrer');

  next();
});
```

### SameSite — Scenari Dettagliati

L'attributo `SameSite` controlla quando il browser invia il cookie con le richieste:

| Scenario | `Strict` | `Lax` | `None` |
|----------|----------|-------|--------|
| Link diretto da sito esterno (`<a href>`) | Cookie NON inviato | Cookie inviato | Cookie inviato |
| Form POST da sito esterno | Cookie NON inviato | Cookie NON inviato | Cookie inviato |
| Fetch/XMLHttpRequest cross-origin | Cookie NON inviato | Cookie NON inviato | Cookie inviato |
| Iframe cross-origin | Cookie NON inviato | Cookie NON inviato | Cookie inviato |
| Immagine cross-origin | Cookie NON inviato | Cookie NON inviato | Cookie inviato |
| Navigazione top-level GET | Cookie NON inviato | Cookie inviato | Cookie inviato |

**Raccomandazione**: `SameSite=Lax` è il default nei browser moderni e offre un buon compromesso. Usare `Strict` per cookie di sessione in applicazioni che non richiedono navigazione da link esterni. `None` solo quando strettamente necessario (widget embedded, flussi SSO cross-domain) e sempre con protezione CSRF aggiuntiva.

---

## Confronto Librerie di Autenticazione

La scelta della libreria di autenticazione ha un impatto significativo su velocità di sviluppo, vendor lock-in, costi e flessibilità. La tabella seguente confronta le soluzioni più rilevanti nel 2025:

| Dimensione | Auth.js v5 (ex NextAuth) | Clerk | Supabase Auth | Better Auth | Lucia |
|-----------|--------------------------|-------|---------------|-------------|-------|
| **Tipo** | Libreria open-source | Servizio SaaS | Parte della piattaforma Supabase | Libreria open-source | **Deprecata** (marzo 2025) |
| **Prezzo** | Gratuito | Gratuito fino 10.000 MAU, poi per-utente | Gratuito fino 50.000 MAU | Gratuito | N/A |
| **Setup time** | 2-4 ore | 30 minuti | 1 ora (con Supabase) | 1-2 ore | N/A |
| **Vendor lock-in** | Nessuno | Alto | Medio (Supabase) | Nessuno | N/A |
| **Provider sociali** | 80+ (via adapter) | 25+ preconfigurati | Google, Apple, GitHub, + SAML | 50+ | N/A |
| **MFA** | Manuale | TOTP, SMS, Backup codes | TOTP | TOTP, WebAuthn | N/A |
| **Passkeys** | Plugin community | Sì (nativo) | Sì | Sì (nativo) | N/A |
| **UI precostruita** | No (solo API) | Sì (componenti React) | Sì (@supabase/auth-ui-react) | No | N/A |
| **Database** | Qualsiasi (via adapter) | Gestito da Clerk | PostgreSQL (Supabase) | Qualsiasi (via adapter) | N/A |
| **SSO/SAML** | Limitato | Sì (Enterprise) | Sì | Limitato | N/A |
| **RLS integration** | No | No | Sì (auth.uid() nelle policy) | No | N/A |
| **Latenza auth** | Dipende dall'implementazione | ~12.5ms | ~15ms | Dipende dall'implementazione | N/A |
| **Maturità** | Alta (dal 2020) | Alta (dal 2021) | Alta (dal 2020) | Media (dal 2024) | Deprecata |

### Raccomandazioni per Caso d'Uso

**Startup / MVP veloce** → **Clerk**: UI pre-costruita, setup in 30 minuti, gestione utenti completa. Il costo per-utente diventa un problema solo a scala.

**Data sovereignty / budget** → **Auth.js v5** o **Better Auth**: zero vendor lock-in, dati nel proprio database, costo zero. Auth.js ha l'ecosistema più maturo; Better Auth è più recente ma progettato per le esigenze del 2025.

**Piattaforma Supabase** → **Supabase Auth**: l'integrazione RLS (`auth.uid()` disponibile in ogni policy PostgreSQL) elimina la necessità di scrivere logica di autorizzazione nell'applicazione. Il vantaggio è significativo per applicazioni data-driven.

**Enterprise / SAML / SSO** → **Clerk** (SaaS) o **WorkOS** (alternativa specializzata in SSO enterprise): gestione completa di SAML, SCIM provisioning, directory sync. Auth.js richiede implementazione manuale.

**Lucia** → **Non usare** per nuovi progetti. La libreria è stata deprecata nel marzo 2025, con i maintainer che sono passati a risorse educative. Se un progetto esistente usa Lucia, pianificare la migrazione a Better Auth o Auth.js.

---

## Sicurezza dello Storage dei Token

### Backend for Frontend (BFF) Pattern

Il pattern BFF (Backend for Frontend) è la soluzione architetturale raccomandata per le SPA che necessitano di autenticazione sicura. Invece di gestire i token direttamente nel browser, un server leggero (il BFF) funge da proxy tra la SPA e l'authorization server:

```
┌─────────────┐        Cookie         ┌──────────┐       Token        ┌──────────────┐
│     SPA     │◄──────httpOnly───────►│   BFF    │◄────Bearer────────►│ API / Auth   │
│  (Browser)  │   (nessun token       │ (Server) │  (token in memoria │  Server      │
│             │    nel browser)       │          │   del server)      │              │
└─────────────┘                      └──────────┘                    └──────────────┘
```

```javascript
// BFF: gestisce i token per conto della SPA
const express = require('express');
const session = require('express-session');

const bff = express();

// La SPA si autentica con il BFF tramite cookie di sessione
bff.use(session({
  name: '__Host-bff-sid',
  secret: process.env.BFF_SESSION_SECRET,
  cookie: { httpOnly: true, secure: true, sameSite: 'strict' },
  resave: false,
  saveUninitialized: false
}));

// Login: il BFF esegue il flusso OAuth e memorizza i token in sessione
bff.get('/bff/login', (req, res) => {
  const pkce = generatePKCE();
  req.session.pkce = pkce;
  req.session.state = crypto.randomBytes(16).toString('hex');
  res.redirect(buildAuthUrl(req.session.state, pkce.challenge));
});

bff.get('/bff/callback', async (req, res) => {
  // Scambiare il codice per i token
  const tokens = await exchangeCodeForTokens(req.query.code, req.session.pkce.verifier);

  // I token NON vanno MAI al browser — restano nel BFF
  req.session.accessToken = tokens.access_token;
  req.session.refreshToken = tokens.refresh_token;
  req.session.tokenExpiry = Date.now() + tokens.expires_in * 1000;

  res.redirect('/');
});

// Proxy API: la SPA chiama il BFF, il BFF aggiunge il Bearer token
bff.all('/bff/api/*', requireBffAuth, async (req, res) => {
  // Refresh automatico del token se scaduto
  if (Date.now() > req.session.tokenExpiry - 60000) {
    const newTokens = await refreshAccessToken(req.session.refreshToken);
    req.session.accessToken = newTokens.access_token;
    req.session.refreshToken = newTokens.refresh_token;
    req.session.tokenExpiry = Date.now() + newTokens.expires_in * 1000;
  }

  // Forward della richiesta all'API con il token
  const apiPath = req.path.replace('/bff/api', '');
  const apiResponse = await fetch(`${API_BASE_URL}${apiPath}`, {
    method: req.method,
    headers: {
      'Authorization': `Bearer ${req.session.accessToken}`,
      'Content-Type': req.headers['content-type']
    },
    body: ['POST', 'PUT', 'PATCH'].includes(req.method) ? JSON.stringify(req.body) : undefined
  });

  const data = await apiResponse.json();
  res.status(apiResponse.status).json(data);
});
```

### httpOnly Cookies con Path Scoping

Il path scoping limita l'invio dei cookie solo agli endpoint che ne hanno bisogno, riducendo la superficie di attacco:

```javascript
// Refresh token: inviato SOLO all'endpoint di refresh
res.cookie('__Host-rt', refreshToken, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  path: '/auth/refresh',           // Solo per /auth/refresh
  maxAge: 7 * 24 * 60 * 60 * 1000
});

// Session cookie: inviato a tutte le richieste
res.cookie('__Host-sid', sessionId, {
  httpOnly: true,
  secure: true,
  sameSite: 'lax',
  path: '/',
  maxAge: 24 * 60 * 60 * 1000
});

// CSRF token: accessibile da JavaScript (non httpOnly), per il double-submit pattern
res.cookie('__Secure-csrf', csrfToken, {
  httpOnly: false,                  // Leggibile da JS per invio nell'header
  secure: true,
  sameSite: 'strict',
  path: '/',
  maxAge: 24 * 60 * 60 * 1000
});
```

### Rischi di localStorage e sessionStorage

| Vettore di Attacco | localStorage | sessionStorage | httpOnly Cookie |
|-------------------|-------------|---------------|-----------------|
| XSS | Vulnerabile | Vulnerabile | Immune |
| CSRF | Immune | Immune | Vulnerabile (mitigabile con SameSite) |
| Persistenza | Permanente | Tab corrente | Configurabile (maxAge) |
| Dimensione max | ~5-10 MB | ~5-10 MB | ~4 KB per cookie |
| Accesso JS | `localStorage.getItem()` | `sessionStorage.getItem()` | Non accessibile |
| Browser extension | Accessibile | Accessibile | Non accessibile |

La regola è chiara: **mai memorizzare token di autenticazione in localStorage**. Un singolo XSS (e nessuna applicazione web complessa è immune al 100% da XSS) compromette tutti i token. I cookie `httpOnly` eliminano completamente questa classe di attacchi.

---

## Rate Limiting e Protezione Brute-Force

### Strategie di Rate Limiting

Una protezione efficace contro gli attacchi brute-force combina limitazione per IP e per account:

```javascript
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis');

// === Rate limiting per IP ===
const ipLimiter = rateLimit({
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
  windowMs: 15 * 60 * 1000,           // Finestra di 15 minuti
  max: 10,                             // Max 10 tentativi per IP
  skipSuccessfulRequests: true,         // Non contare i login riusciti
  standardHeaders: true,               // RateLimit-* headers
  legacyHeaders: false,
  keyGenerator: (req) => req.ip,
  message: { error: 'Troppi tentativi da questo indirizzo IP. Riprova tra 15 minuti.' }
});

// === Rate limiting per account ===
async function accountLimiter(req, res, next) {
  const { email } = req.body;
  if (!email) return next();

  const key = `login_attempts:${email.toLowerCase()}`;
  const attempts = await redisClient.incr(key);

  // Impostare TTL al primo tentativo
  if (attempts === 1) {
    await redisClient.expire(key, 900);   // 15 minuti
  }

  // Limiti progressivi
  if (attempts > 10) {
    return res.status(429).json({
      error: 'Account temporaneamente bloccato',
      retryAfter: await redisClient.ttl(key),
      message: 'Troppi tentativi di login. L\'account sarà sbloccato automaticamente.'
    });
  }

  // Delay crescente dopo 3 tentativi (exponential backoff)
  if (attempts > 3) {
    const delay = Math.min(Math.pow(2, attempts - 3) * 1000, 30000);  // Max 30s
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  next();
}

// Applicare entrambi i limiter
app.post('/auth/login', ipLimiter, accountLimiter, loginHandler);
```

### Exponential Backoff e Account Lockout

Due strategie complementari, con trade-off diversi:

**Exponential Backoff** — Introduce ritardi crescenti tra i tentativi falliti senza bloccare l'account. Vantaggi: l'utente legittimo non viene mai bloccato completamente. Svantaggio: un attaccante paziente può continuare a provare.

**Account Lockout** — Blocca l'account dopo N tentativi falliti per un periodo. Vantaggi: ferma l'attacco immediatamente. Svantaggio: un attaccante può causare un DoS bloccando account legittimi (account enumeration + lockout = DoS).

```javascript
// Strategia ibrida: backoff + lockout temporaneo + notifica
async function handleFailedLogin(email, ip) {
  const accountKey = `failed:${email.toLowerCase()}`;
  const ipKey = `failed_ip:${ip}`;

  const [accountAttempts, ipAttempts] = await Promise.all([
    redisClient.incr(accountKey),
    redisClient.incr(ipKey)
  ]);

  // TTL di 30 minuti per entrambi i contatori
  await Promise.all([
    redisClient.expire(accountKey, 1800),
    redisClient.expire(ipKey, 1800)
  ]);

  // Notifica email dopo 5 tentativi falliti
  if (accountAttempts === 5) {
    const user = await findUserByEmail(email);
    if (user) {
      await sendEmail({
        to: email,
        subject: 'Tentativi di accesso sospetti',
        text: `Sono stati rilevati ${accountAttempts} tentativi di accesso falliti al tuo account da ${ip}. Se non sei tu, ti consigliamo di cambiare la password.`
      });
    }
  }

  // Lockout temporaneo dopo 10 tentativi (30 minuti)
  if (accountAttempts >= 10) {
    await redisClient.set(`locked:${email.toLowerCase()}`, '1', { EX: 1800 });
    securityLogger('ACCOUNT_LOCKED', { email, ip, attempts: accountAttempts });
  }

  return {
    locked: accountAttempts >= 10,
    remainingAttempts: Math.max(0, 10 - accountAttempts),
    retryAfter: accountAttempts >= 10 ? await redisClient.ttl(`locked:${email.toLowerCase()}`) : null
  };
}

// Verificare il lockout prima del login
async function checkAccountLockout(req, res, next) {
  const { email } = req.body;
  if (!email) return next();

  const isLocked = await redisClient.get(`locked:${email.toLowerCase()}`);
  if (isLocked) {
    const ttl = await redisClient.ttl(`locked:${email.toLowerCase()}`);
    return res.status(423).json({
      error: 'Account temporaneamente bloccato',
      retryAfter: ttl,
      message: `Troppi tentativi falliti. Riprova tra ${Math.ceil(ttl / 60)} minuti.`
    });
  }

  next();
}
```

### CAPTCHA Intelligente

L'uso di CAPTCHA deve essere proporzionale al rischio, evitando di penalizzare gli utenti legittimi:

```javascript
// CAPTCHA trigger progressivo
async function captchaMiddleware(req, res, next) {
  const { email } = req.body;
  const attempts = await getFailedAttempts(email, req.ip);

  // Nessun CAPTCHA per i primi 3 tentativi
  if (attempts < 3) return next();

  // CAPTCHA richiesto dopo 3 tentativi
  const captchaToken = req.body.captchaToken;
  if (!captchaToken) {
    return res.status(428).json({
      error: 'captcha_required',
      message: 'Verifica di sicurezza richiesta',
      captchaType: attempts < 7 ? 'invisible' : 'interactive'
    });
  }

  // Verificare il token CAPTCHA
  const captchaValid = await verifyCaptchaToken(captchaToken);
  if (!captchaValid) {
    return res.status(400).json({ error: 'Verifica CAPTCHA fallita' });
  }

  next();
}

app.post('/auth/login',
  checkAccountLockout,
  ipLimiter,
  captchaMiddleware,
  accountLimiter,
  loginHandler
);
```

---

## Best Practices

Dieci principi fondamentali per un sistema di autenticazione e autorizzazione robusto:

**1. Utilizzare HTTPS ovunque.** Tutto il traffico dell'applicazione deve transitare su connessioni TLS/HTTPS. Senza crittografia del trasporto, qualsiasi meccanismo di autenticazione è inutile: credenziali, token e cookie possono essere intercettati in transito. Configurare HSTS (HTTP Strict Transport Security) per forzare HTTPS e prevenire attacchi di downgrade.

**2. Applicare il principio del privilegio minimo.** Ogni utente, servizio e componente dovrebbe avere esclusivamente i permessi strettamente necessari per svolgere la propria funzione. Un endpoint di sola lettura non deve accettare richieste di scrittura; un servizio che invia email non deve avere accesso al database degli utenti. Questo limita il danno potenziale in caso di compromissione.

**3. Validare e sanitizzare sempre gli input.** Le credenziali, i token e qualsiasi dato proveniente dal client devono essere validati rigorosamente. Non fidarsi mai del client: un token JWT potrebbe essere manipolato (verificare sempre la firma), un parametro `role` nel body di una richiesta potrebbe essere iniettato da un utente malevolo (i ruoli devono provenire dal server, mai dal client).

**4. Implementare rate limiting e protezione brute-force.** Limitare il numero di tentativi di login falliti per IP e per account. Dopo un certo numero di fallimenti, introdurre ritardi crescenti (exponential backoff) o blocchi temporanei. Strumenti come `express-rate-limit` e `express-slow-down` sono essenziali. Considerare anche CAPTCHA dopo tentativi ripetuti.

```javascript
const rateLimit = require('express-rate-limit');

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,    // Finestra di 15 minuti
  max: 5,                       // Max 5 tentativi per finestra
  skipSuccessfulRequests: true,  // Non contare i login riusciti
  standardHeaders: true,
  message: { error: 'Troppi tentativi di login. Riprova tra 15 minuti.' }
});

app.post('/login', loginLimiter, loginHandler);
```

**5. Centralizzare la logica di autenticazione.** Evitare di duplicare i controlli di autenticazione e autorizzazione in ogni endpoint. Utilizzare middleware centralizzati e un servizio di autenticazione dedicato. Questo riduce la superficie di errore e semplifica gli aggiornamenti di sicurezza.

**6. Loggare gli eventi di sicurezza.** Registrare ogni tentativo di login (riuscito e fallito), ogni cambio di password, ogni attivazione/disattivazione MFA, ogni escalation di privilegi. Questi log sono essenziali per il rilevamento di intrusioni e per le indagini forensi. Non includere mai password o token nei log.

```javascript
function securityLogger(event, details) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    event,                       // 'LOGIN_SUCCESS', 'LOGIN_FAILURE', 'MFA_ENABLED', ...
    userId: details.userId,
    ip: details.ip,
    userAgent: details.userAgent,
    metadata: details.metadata   // Informazioni aggiuntive (mai credenziali)
  };

  // Inviare a un sistema di log centralizzato (ELK, Datadog, ecc.)
  logger.info(logEntry);
}
```

**7. Gestire correttamente gli errori senza rivelare informazioni.** I messaggi di errore non devono indicare quale parte delle credenziali è errata. "Email o password non corretti" va bene; "Password non corretta per l'account mario@example.com" rivela che quell'account esiste. Analogamente, la pagina "password dimenticata" non deve confermare l'esistenza di un account.

**8. Ruotare regolarmente le chiavi e i segreti.** Le chiavi di firma JWT, i session secret, le API key e le credenziali dei servizi devono essere ruotate periodicamente. Implementare un meccanismo che supporti più chiavi attive contemporaneamente (key rollover) per evitare interruzioni durante la rotazione.

**9. Implementare il logout completo.** Il logout deve invalidare sia la sessione server-side che i token client-side. Per i JWT, questo significa aggiungere il token alla blocklist, revocare il refresh token nel database e cancellare tutti i cookie. Un logout incompleto lascia sessioni fantasma che un attaccante potrebbe sfruttare.

**10. Aggiornare le dipendenze e monitorare le vulnerabilità.** Le librerie di autenticazione sono bersagli frequenti di ricerche di sicurezza. Monitorare gli advisory CVE per le dipendenze utilizzate (con `npm audit` o strumenti come Snyk), aggiornare tempestivamente e seguire le raccomandazioni OWASP. Un sistema di autenticazione costruito su librerie obsolete è un sistema vulnerabile, indipendentemente dalla qualità del codice applicativo.

---

Progettare un sistema di autenticazione e autorizzazione sicuro non è un'attività una tantum, ma un processo continuo di revisione, aggiornamento e adattamento alle nuove minacce. I pattern e le implementazioni presentati in questa guida costituiscono una base solida, ma devono essere integrati con test di sicurezza regolari, penetration testing e un monitoraggio costante degli eventi di sicurezza. La sicurezza è tanto forte quanto il suo anello più debole: ogni componente, dalla password policy al logout, merita la stessa attenzione e rigore implementativo.

---

## Esercizi

### Esercizio 1 — Autenticazione session-based con cookie sicuri

**Obiettivo:** Implementare un sistema di autenticazione classico basato su sessioni server-side.

Costruire un server Express/Fastify con autenticazione session-based:

- Registrazione utente con email e password: hashing con Argon2 (o bcrypt con cost factor 12), validazione forza password (minimo 12 caratteri, almeno una maiuscola, un numero, un carattere speciale)
- Login con verifica credenziali e creazione sessione server-side (memorizzata in Redis con TTL 24h)
- Cookie di sessione con attributi: `httpOnly: true`, `secure: true`, `sameSite: 'lax'`, `path: '/'`, `maxAge: 86400000`
- Middleware `requireAuth` che verifichi la sessione su ogni richiesta protetta
- Endpoint protetto `GET /me` che restituisca i dati dell'utente corrente
- Logout che invalidi la sessione in Redis e cancelli il cookie
- Protezione brute-force: blocco temporaneo dell'account dopo 5 tentativi falliti in 15 minuti (con contatore in Redis)
- Test: registrazione, login, accesso a risorsa protetta, logout, tentativo di accesso dopo logout, blocco brute-force

### Esercizio 2 — Autenticazione JWT con refresh token rotation

**Obiettivo:** Implementare un flusso JWT sicuro con rotazione dei refresh token.

Costruire un sistema di autenticazione JWT completo:

- Access token JWT con durata 15 minuti, firmato con algoritmo `RS256` (coppia di chiavi RSA), payload con campi `sub`, `email`, `role`, `iat`, `exp`
- Refresh token opaco (UUID v4) memorizzato nel database con: `userId`, `tokenHash` (SHA-256 del token), `expiresAt` (7 giorni), `familyId` (per rilevamento riuso), `replacedBy` (punta al token successivo nella chain)
- Endpoint `POST /auth/refresh`: valida il refresh token, lo invalida, ne genera uno nuovo (rotation), rilascia un nuovo access token
- **Rilevamento furto**: se un refresh token già invalidato viene riutilizzato, invalidare tutta la famiglia (`familyId`) e forzare il re-login
- Refresh token inviato in cookie `httpOnly` separato dal path `/auth/refresh` (non inviato ad altri endpoint)
- Endpoint `POST /auth/logout` che invalidi tutti i refresh token dell'utente
- Endpoint `GET /auth/sessions` che elenchi le sessioni attive dell'utente con informazioni su IP e user agent
- Test per ogni scenario: token valido, token scaduto, refresh rotation, rilevamento furto, logout globale

### Esercizio 3 — OAuth 2.0 con PKCE e OpenID Connect

**Obiettivo:** Integrare un provider OAuth 2.0 esterno con il flusso Authorization Code + PKCE.

Implementare il flusso OAuth 2.0 Authorization Code con PKCE per un'applicazione web:

- Integrare almeno un provider OIDC (GitHub o Google) con i seguenti passi:
  1. Generare `code_verifier` (random 43-128 caratteri) e `code_challenge` (SHA-256 + base64url del verifier)
  2. Redirect alla pagina di autorizzazione con parametri: `response_type=code`, `client_id`, `redirect_uri`, `scope=openid email profile`, `state` (anti-CSRF), `code_challenge`, `code_challenge_method=S256`
  3. Callback handler che verifichi `state`, scambi il `code` + `code_verifier` per i token
  4. Validare l'`id_token` JWT verificando firma, `iss`, `aud`, `exp`, `nonce`
  5. Creare o aggiornare l'utente locale con le informazioni dal `userinfo` endpoint
- Memorizzare `code_verifier` e `state` in sessione server-side durante il flusso (non nel client)
- Gestire il caso di account linking: se l'email del provider corrisponde a un utente esistente, collegare l'account OAuth
- Implementare il logout che invalidi sia la sessione locale sia il token presso il provider (se supporta end_session_endpoint)
- Test del flusso completo con mock del provider OAuth

### Esercizio 4 — Sistema RBAC con permessi granulari

**Obiettivo:** Progettare un sistema di autorizzazione flessibile con ruoli e permessi.

Implementare un sistema RBAC (Role-Based Access Control) completo:

- Schema database con tabelle: `roles` (id, name, description), `permissions` (id, resource, action — es. `posts:create`, `users:delete`), `role_permissions` (many-to-many), `user_roles` (many-to-many con `assignedAt` e `assignedBy`)
- Ruoli predefiniti: `admin` (tutti i permessi), `editor` (CRUD su posts e commenti), `viewer` (solo lettura), `moderator` (gestione commenti e segnalazioni)
- Middleware `requirePermission('posts:create')` che verifichi se l'utente corrente possiede il permesso richiesto attraverso i suoi ruoli
- Middleware `requireRole('admin')` per controlli basati sul ruolo
- API di gestione ruoli (solo admin): `POST /roles`, `PUT /roles/:id/permissions`, `POST /users/:id/roles`, `DELETE /users/:id/roles/:roleId`
- Caching dei permessi dell'utente in Redis con invalidazione alla modifica dei ruoli
- Implementare il principio del privilegio minimo: un nuovo utente parte senza ruoli e deve essere assegnato esplicitamente
- Audit log per ogni modifica ai ruoli e permessi (chi, cosa, quando)
- Test per ogni combinazione: utente con ruolo sufficiente, utente con ruolo insufficiente, utente senza ruoli, utente con ruoli multipli

### Esercizio 5 — Autenticazione passwordless con WebAuthn/Passkeys

**Obiettivo:** Implementare l'autenticazione moderna basata su passkeys secondo lo standard WebAuthn.

Costruire un flusso di registrazione e login con Passkeys:

- Backend con `@simplewebauthn/server` (o equivalente) per generare e verificare le challenge WebAuthn
- Registrazione passkey:
  1. `POST /webauthn/register/options` — generare `PublicKeyCredentialCreationOptions` con `rp` (relying party), `user`, `challenge`, `pubKeyCredParams` (almeno ES256 e RS256), `authenticatorSelection` (preferenza per platform authenticator)
  2. Il client chiama `navigator.credentials.create()` con le opzioni ricevute
  3. `POST /webauthn/register/verify` — verificare l'`attestation`, estrarre la chiave pubblica, memorizzare nel database con `credentialId`, `publicKey`, `counter`, `transports`
- Login con passkey:
  1. `POST /webauthn/login/options` — generare `PublicKeyCredentialRequestOptions` con challenge e `allowCredentials`
  2. Il client chiama `navigator.credentials.get()`
  3. `POST /webauthn/login/verify` — verificare l'`assertion`, controllare il counter (anti-replay), emettere sessione o JWT
- Supportare più passkeys per utente e un endpoint per elencare/revocare le passkey registrate
- Fallback: se il browser non supporta WebAuthn, offrire login tradizionale con password + MFA
- Implementare MFA con TOTP (Google Authenticator): generazione del secret, QR code, verifica del codice con finestra temporale di tolleranza
- Test end-to-end con mock dell'API WebAuthn del browser

---

## Letture e Riferimenti

### Documentazione ufficiale

- **RFC 9700 — OAuth 2.1** — consolidamento di OAuth 2.0 con PKCE obbligatorio e deprecazione del flusso implicit. https://www.rfc-editor.org/rfc/rfc9700 (consultato: 2026-05-24)
- **RFC 7519 — JSON Web Token (JWT)** — specifica del formato JWT per token di autenticazione. https://www.rfc-editor.org/rfc/rfc7519 (consultato: 2026-05-24)
- **OpenID Connect Core 1.0** — layer di identità costruito sopra OAuth 2.0 per autenticazione. https://openid.net/specs/openid-connect-core-1_0.html (consultato: 2026-05-24)
- **WebAuthn Specification (Level 2)** — standard W3C per autenticazione passwordless con credenziali a chiave pubblica. https://www.w3.org/TR/webauthn-2/ (consultato: 2026-05-24)
- **OWASP Authentication Cheat Sheet** — linee guida OWASP per l'implementazione sicura dell'autenticazione. https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html (consultato: 2026-05-24)
- **OWASP Session Management Cheat Sheet** — best practice per la gestione sicura delle sessioni. https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html (consultato: 2026-05-24)
- **Passkeys.dev** — guida per sviluppatori sull'implementazione delle passkeys. https://passkeys.dev/ (consultato: 2026-05-24)

### Libri e approfondimenti

- Richer, Justin; Sanso, Antonio, *OAuth 2 in Action*, Manning, 2017.
- Madden, Neil, *API Security in Action*, Manning, 2020.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [10 — Node.js](10-nodejs.md) | Prerequisito: middleware, session management e HTTP server implementati in ambiente Node.js |
| [14 — Sicurezza Web](14-sicurezza-web.md) | Prerequisito: XSS, CSRF, cookie security e security headers necessari per proteggere il flusso di autenticazione |
| [11 — API Design](11-api-design.md) | OAuth 2.0, API key e JWT applicati come security scheme nelle API RESTful e GraphQL |
| [12 — Database Web](12-database-web.md) | Sessioni, refresh token, ruoli e permessi persistiti e gestiti a livello database |
| [23 — WebSocket Security](23-websocket-security.md) | Autenticazione e autorizzazione applicate alle connessioni WebSocket |
| [25 — Next.js Guida Completa](25-nextjs-guida-completa.md) | Implementazione di autenticazione con next-auth/Auth.js in applicazioni full-stack |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Autenticazione (AuthN)** | Processo di verifica dell'identità di un utente o sistema tramite credenziali. |
| **Autorizzazione (AuthZ)** | Processo di verifica dei permessi di un'identità autenticata per accedere a risorse specifiche. |
| **JWT** | JSON Web Token: token firmato contenente claim codificati in JSON, usato per autenticazione stateless. |
| **OAuth 2.0** | Framework di autorizzazione che consente a un'applicazione di accedere a risorse per conto di un utente senza conoscerne le credenziali. |
| **OIDC** | OpenID Connect: layer di identità sopra OAuth 2.0 che aggiunge autenticazione e un `id_token` standardizzato. |
| **PKCE** | Proof Key for Code Exchange: estensione OAuth 2.0 che protegge il flusso authorization code da intercettazione. |
| **RBAC** | Role-Based Access Control: modello di autorizzazione basato su ruoli assegnati agli utenti. |
| **ABAC** | Attribute-Based Access Control: modello di autorizzazione basato su attributi del soggetto, della risorsa e del contesto. |
| **Passkey** | Credenziale a chiave pubblica conforme allo standard WebAuthn, memorizzata nel dispositivo o nel cloud. |
| **Refresh Token** | Token a lunga durata utilizzato per ottenere nuovi access token senza richiedere il re-login dell'utente. |
| **MFA** | Multi-Factor Authentication: autenticazione che richiede almeno due fattori indipendenti (conoscenza, possesso, inerenza). |
| **TOTP** | Time-based One-Time Password: codice numerico generato da un algoritmo basato sul tempo, usato come secondo fattore. |
| **Session Hijacking** | Attacco in cui un aggressore ruba l'identificatore di sessione per impersonare un utente autenticato. |
| **Token Rotation** | Pratica di invalidare un refresh token ogni volta che viene usato, rilasciandone uno nuovo per rilevare il furto. |
| **ReBAC** | Relationship-Based Access Control: modello di autorizzazione che determina i permessi in base alle relazioni tra soggetti e risorse, ispirato da Google Zanzibar. |
| **DPoP** | Demonstrating Proof-of-Possession (RFC 9449): meccanismo che vincola un token OAuth al client che lo ha richiesto tramite una prova crittografica. |
| **JWE** | JSON Web Encryption (RFC 7516): formato per token cifrati che garantisce la confidenzialità del contenuto, composto da cinque parti. |
| **JWS** | JSON Web Signature (RFC 7515): formato per token firmati che garantisce integrità e autenticità senza cifratura del payload. |
| **mTLS** | Mutual TLS: autenticazione bidirezionale dove sia client che server presentano un certificato X.509, garantendo l'identità di entrambe le parti. |
| **BFF** | Backend for Frontend: pattern architetturale dove un server proxy gestisce i token per conto della SPA, evitando l'esposizione dei token nel browser. |
| **Sliding Session** | Sessione con timeout che si resetta ad ogni attività dell'utente, prolungando la durata finché l'utente resta attivo. |
| **Sender-Constrained Token** | Token vincolato al client che lo ha richiesto, inutilizzabile se rubato da un altro client (implementato via DPoP o mTLS). |
| **Conditional UI** | Funzionalità WebAuthn che integra le passkeys nel menu di autocompletamento del browser per un'esperienza di login trasparente. |
| **Step-Up Authentication** | Ri-autenticazione con fattore aggiuntivo richiesta per operazioni sensibili, anche se l'utente è già autenticato. |
| **Attestation** | Processo WebAuthn di registrazione di una nuova credenziale, dove l'autenticatore genera una coppia di chiavi e restituisce la chiave pubblica. |
| **Assertion** | Processo WebAuthn di autenticazione con una credenziale esistente, dove l'autenticatore firma una challenge con la chiave privata. |
| **Multi-Tenancy** | Architettura in cui una singola istanza applicativa serve più organizzazioni (tenant) con isolamento dei dati e dell'identità. |
| **CTAP2** | Client to Authenticator Protocol: protocollo FIDO Alliance per la comunicazione tra browser/OS e autenticatori fisici (USB, NFC, BLE). |
| **JWKS** | JSON Web Key Set: endpoint che espone le chiavi pubbliche di un provider OIDC per la verifica dei token firmati, con supporto per rotazione e multi-chiave tramite `kid`. |
