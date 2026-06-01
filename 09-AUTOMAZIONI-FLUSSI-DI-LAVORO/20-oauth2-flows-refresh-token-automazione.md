---
corso: "Automazioni e Flussi di Lavoro"
fase: "5 — Pattern Avanzati"
modulo: 20
titolo: "OAuth 2.0 e OIDC per Automazioni — Flows, Refresh Token, Vault"
versione: "OAuth 2.1 (RFC 9700), OIDC Core 1.0"
livello: "competent → proficient"
prerequisiti: ["Modulo 04 — Integrazione API", "HTTP/JSON/JWT basics", "Authorization vs Authentication"]
obiettivi:
  - "Implementare OAuth 2.1 auth code + PKCE per public client e client credentials per service-to-service"
  - "Configurare refresh token rotation con rilevamento compromissione e revoca automatica"
  - "Integrare private_key_jwt e DPoP per autenticazione client sicura senza shared secret"
  - "Progettare vault integration per storage sicuro di token e secret nelle automazioni"
  - "Diagnosticare e risolvere problemi comuni di OAuth in workflow automatizzati (token expiry, scope mismatch, CORS)"
tag: [oauth2, oidc, pkce, refresh-token, vault, jwt, security, client-credentials]
---

# OAuth 2.0 e OIDC per Automazioni — Flows, Refresh Token, Vault

> **Obiettivi di apprendimento**
> 1. Implementare OAuth 2.1 auth code + PKCE per public client e client credentials per service-to-service
> 2. Configurare refresh token rotation con rilevamento compromissione e revoca automatica
> 3. Integrare private_key_jwt e DPoP per autenticazione client sicura senza shared secret
> 4. Progettare vault integration per storage sicuro di token e secret nelle automazioni
> 5. Diagnosticare e risolvere problemi comuni di OAuth in workflow automatizzati (token expiry, scope mismatch, CORS)

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 2 — API & integrazione · Modulo 20
> **Prerequisiti:** Modulo 04; HTTP, JSON, JWT basics; concetto authorization vs authentication.
> **Obiettivi:** OAuth 2.1 flows (auth code + PKCE, client credentials); refresh token rotation; PKCE; private_key_jwt; vault integration.
> **Tempo:** lettura 90 min · lab 240 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** OAuth 2.1 (RFC 9700), OIDC Core 1.0.

## Idee guida

1. **OAuth 2.1 deprecates implicit flow.** Sempre auth code + PKCE per public client.
2. **Client credentials per service-to-service.** No refresh token; ri-acquisisci con creds ogni volta.
3. **Refresh token rotation = best practice.** Ogni refresh emette nuovo refresh + invalida vecchio.
4. **`private_key_jwt` > client_secret per high-security.** Asimmetrico, nessun secret condiviso.
5. **Token in vault, mai in code o env vars persistent.** Vault offre rotation, audit, revocation.
6. **Scope minimi assoluti.** Ogni workflow riceve solo i permessi strettamente necessari.
7. **Audit ogni operazione token.** Creazione, refresh, revoca, uso — tutto loggato.
8. **mTLS e DPoP per proof-of-possession.** Token rubati inutilizzabili senza la chiave del client.

---

## Indice

1. [Panoramica](#panoramica)
2. [Concetti Fondamentali](#concetti-fondamentali)
   - [OAuth 2.0 vs OIDC](#oauth-20-vs-oidc)
   - [Ruoli e attori](#ruoli-e-attori)
   - [Tipologie di token](#tipologie-di-token)
   - [JWT structure e validazione](#jwt-structure-e-validazione)
3. [Guida Pratica: i quattro flow principali](#guida-pratica-i-quattro-flow-principali)
   - [Authorization Code (con PKCE)](#authorization-code-con-pkce)
   - [Client Credentials](#client-credentials)
   - [Device Authorization Grant](#device-authorization-grant)
   - [Resource Owner Password (deprecato)](#resource-owner-password-deprecato)
4. [Refresh Token e Rotation](#refresh-token-e-rotation)
5. [Configurazione](#configurazione)
   - [PKCE deep dive](#pkce-deep-dive)
   - [DPoP — Demonstrating Proof-of-Possession](#dpop--demonstrating-proof-of-possession)
   - [Scope design](#scope-design)
   - [Token storage nei workflow tools](#token-storage-nei-workflow-tools)
   - [Multi-tenant token vault](#multi-tenant-token-vault)
   - [OAuth Proxy per legacy app](#oauth-proxy-per-legacy-app)
   - [Provider OAuth interno con Keycloak](#provider-oauth-interno-con-keycloak)
6. [Implementazione completa Python — OAuth Client Library](#implementazione-completa-python--oauth-client-library)
7. [Integrazione provider-specific](#integrazione-provider-specific)
   - [Google Workspace](#google-workspace)
   - [Microsoft Graph / Azure AD](#microsoft-graph--azure-ad)
   - [GitHub Apps](#github-apps)
   - [Stripe Connect](#stripe-connect)
8. [private_key_jwt — autenticazione asimmetrica](#private_key_jwt--autenticazione-asimmetrica)
9. [Token lifecycle management per workflow](#token-lifecycle-management-per-workflow)
10. [Sicurezza avanzata](#sicurezza-avanzata)
11. [Monitoring e alerting](#monitoring-e-alerting)
12. [Best Practices](#best-practices)
13. [Troubleshooting — 18 problemi comuni](#troubleshooting--18-problemi-comuni)
14. [FAQ — 15 domande e risposte](#faq--15-domande-e-risposte)
15. [Esercizi](#esercizi)
16. [Auto-valutazione](#auto-valutazione)
17. [Riferimenti](#riferimenti)
18. [Collegamenti incrociati](#collegamenti-incrociati)
19. [Glossario locale](#glossario-locale)

---

## Panoramica

Quando un'automazione deve agire per conto di un utente o di un sistema esterno, la prima domanda non e "come chiamo l'API?" ma "come dimostro di essere autorizzato?". Per anni la risposta e stata: salva username e password in un campo cifrato del workflow tool e usali alla bisogna. E un approccio che oggi e semplicemente inaccettabile, sia per ragioni di sicurezza (un'unica credenziale che permette il pieno controllo dell'account, senza scope, senza scadenza, senza revoca selettiva) sia perche qualsiasi provider serio — Google Workspace, Microsoft 365, Salesforce, Stripe, Shopify, GitHub — ha smesso di accettare login con password per uso programmatico.

OAuth 2.0 risolve esattamente questo problema. E il framework standard, definito in RFC 6749 e successive estensioni, che permette a un'applicazione (il client) di ottenere un accesso limitato e revocabile alle risorse di un utente o di un sistema, senza mai vedere le credenziali primarie. Il principio e semplice: l'utente si autentica direttamente sul provider (l'authorization server), il provider chiede esplicitamente "vuoi dare a questa applicazione il permesso di leggere le tue email e creare eventi nel calendario?", e in caso di consenso emette un access token con scope definiti e durata limitata.

Per chi costruisce automazioni B2B o SaaS, OAuth 2.0 e critico per quattro ragioni concrete:

1. **Niente password storage**. Il workflow tool non vede mai la password dell'utente. Anche un dump del database del provider (n8n, Make, Zapier) non espone le credenziali primarie del cliente.
2. **Scope limitato**. Un token puo essere emesso con `read:invoices` e basta. Anche se compromesso, non permette di cancellare account, leggere email private o accedere ad altre aree.
3. **Revocabile**. L'utente puo, in qualsiasi momento, revocare l'accesso dalla console del provider. L'automazione smette di funzionare immediatamente, senza dover cambiare password.
4. **Audit nativo**. Ogni emissione di token, ogni refresh, ogni utilizzo e registrato dall'authorization server con metadati completi.

OpenID Connect (OIDC) costruisce sopra OAuth 2.0 un layer di autenticazione vero e proprio. La differenza concettuale e netta: OAuth 2.0 risponde alla domanda "questa applicazione puo accedere a queste risorse?" (autorizzazione), mentre OIDC risponde anche a "chi e l'utente che sta usando l'applicazione?" (autenticazione). OIDC introduce l'**ID token**, un JWT firmato che contiene claim verificati sull'identita dell'utente (sub, email, name, preferred_username), permettendo al client di costruire una sessione utente locale senza dover interrogare ulteriormente il provider.

In contesto automazione la distinzione e importante: per un workflow che invia fatture su Drive serve OAuth 2.0 puro (autorizzazione all'API Drive), mentre per un'automazione che fa SSO degli utenti su un portale interno serve OIDC (autenticazione + claim utente). Molti provider espongono entrambi sullo stesso endpoint discovery: `https://provider.example.com/.well-known/openid-configuration`.

Questo documento copre i quattro flow OAuth 2.0 piu rilevanti per l'automazione, il modello di refresh token con rotation introdotto da OAuth 2.1, le best practice per PKCE e DPoP, e — la parte spesso trascurata — come gestire in modo sicuro il vault dei token quando si scalano centinaia di tenant in un workflow tool.

---

## Concetti Fondamentali

### OAuth 2.0 vs OIDC

OAuth 2.0 e un framework di **delegated authorization**. L'utente delega a un'applicazione il diritto di accedere a un sottoinsieme delle proprie risorse, per un tempo limitato, su un authorization server fidato. Non dice nulla sull'identita dell'utente: il client riceve un access token opaco o un JWT, lo presenta all'API, l'API verifica che il token sia valido e che abbia gli scope richiesti.

OIDC aggiunge tre cose:

- Un **ID token** (sempre JWT) emesso insieme all'access token, contenente claim sull'utente.
- Un endpoint `/userinfo` che il client puo interrogare con l'access token per ottenere claim aggiuntivi.
- Un protocollo di discovery standardizzato (`/.well-known/openid-configuration`) che descrive endpoint, algoritmi supportati, claim disponibili.

In pratica:

- **Solo OAuth 2.0**: integrazione con Stripe, Shopify, Salesforce per uso macchina-a-macchina o per accedere a risorse utente.
- **OIDC**: SSO su portali interni, login federato, qualsiasi caso in cui il client deve sapere "chi e l'utente loggato".

### Ruoli e attori

OAuth 2.0 definisce quattro ruoli:

- **Resource Owner** — l'utente (o il sistema) proprietario delle risorse.
- **Client** — l'applicazione che vuole accedere alle risorse. Puo essere `confidential` (server con secret, es. backend n8n self-hosted) o `public` (browser, mobile, CLI — non puo custodire un secret).
- **Authorization Server (AS)** — il sistema che autentica l'utente ed emette i token. Esempi: `accounts.google.com`, `login.microsoftonline.com`, Keycloak self-hosted.
- **Resource Server (RS)** — l'API che ospita le risorse e valida i token in ingresso. Spesso AS e RS sono distinti ma gestiti dallo stesso vendor (Google: AS = `accounts.google.com`, RS = `www.googleapis.com`).

### Tipologie di token

**Access Token** — credenziale presentata al Resource Server per accedere alle risorse. Due varianti tecniche:

- **JWT (self-contained)**. Il RS valida la firma e legge i claim direttamente dal token, senza chiamare l'AS. Pro: latenza zero, scalabilita. Contro: revoca difficile (il token resta valido fino a scadenza naturale). Tipico di Auth0, Keycloak, Cognito, Azure AD.
- **Opaque (reference token)**. Stringa random opaca; il RS deve interrogare l'AS via introspection endpoint (RFC 7662) per validarla. Pro: revoca immediata. Contro: latenza aggiuntiva. Tipico di GitHub, Stripe.

**Refresh Token** — credenziale long-lived (giorni o mesi) usata per ottenere nuovi access token quando quello corrente scade. Mai presentato al RS, solo all'AS sull'endpoint `/token`. Va trattato come un secret di alto valore: la sua compromissione equivale alla compromissione dell'account per tutta la durata di validita.

**ID Token (OIDC)** — JWT con claim sull'identita utente. Mai presentato all'API: serve solo al client per costruire la sessione locale. Validare sempre `iss`, `aud`, `exp`, `nonce`.

### JWT structure e validazione

Un JWT e composto da tre parti separate da punti, codificate in base64url:

```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImFiYzEyMyJ9.
eyJpc3MiOiJodHRwczovL2F1dGguZXhhbXBsZS5jb20iLCJzdWIiOiJ1c2VyXzQyIiwiYXVkIjoiYXBpLmV4YW1wbGUuY29tIiwiZXhwIjoxNzE0MDAwMDAwLCJpYXQiOjE3MTM5OTY0MDAsInNjb3BlIjoicmVhZDppbnZvaWNlcyB3cml0ZTppbnZvaWNlcyJ9.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Header** — algoritmo di firma e key id:

```json
{ "alg": "RS256", "typ": "JWT", "kid": "abc123" }
```

**Payload** — i claim:

```json
{
  "iss": "https://auth.example.com",
  "sub": "user_42",
  "aud": "api.example.com",
  "exp": 1714000000,
  "iat": 1713996400,
  "scope": "read:invoices write:invoices"
}
```

**Signature** — firma calcolata su `base64url(header) + "." + base64url(payload)` con la chiave indicata da `kid`.

Algoritmi raccomandati:

- **RS256** (RSA + SHA-256) — piu diffuso, chiave pubblica scaricabile via JWKS endpoint.
- **ES256** (ECDSA P-256 + SHA-256) — piu piccolo e veloce di RS256, raccomandato per sistemi nuovi.
- **HS256** (HMAC + SHA-256) — chiave simmetrica condivisa tra AS e RS. Usabile solo se entrambi sono sotto il tuo controllo. **Mai** per token verificati da terze parti.

Validazione obbligatoria di un JWT in ingresso:

1. **Signature** — verifica con la chiave pubblica recuperata dal JWKS endpoint dell'issuer (`<iss>/.well-known/jwks.json`), selezionando la chiave con `kid` corrispondente.
2. **iss (issuer)** — deve corrispondere all'AS atteso. **Mai** fidarsi del valore senza confronto esatto.
3. **aud (audience)** — deve includere l'identificativo del Resource Server. Se il token e destinato a un'altra API, va rigettato.
4. **exp (expiration)** — il token deve essere ancora valido (con tolleranza max 30s per clock skew).
5. **nbf (not before)**, se presente — il token non deve essere usato prima di questo timestamp.
6. **alg** — deve corrispondere all'algoritmo atteso. Bug storico (`alg: none`): un AS configurato male puo accettare token non firmati. Mai accettare `none` in produzione.

Mai implementare la validazione JWT manualmente: usare librerie mature (`jose` per Node.js, `PyJWT` o `python-jose` per Python, `golang-jwt/jwt` per Go) che gestiscono correttamente edge case e algoritmi.

---

## Guida Pratica: i quattro flow principali

### Authorization Code (con PKCE)

Il flow piu diffuso e l'unico raccomandato per applicazioni web server-side, SPA e mobile dopo OAuth 2.1. Permette all'utente di autenticarsi sul provider e dare consenso esplicito agli scope richiesti.

**Quando usarlo**: web app server-side che integra Google Workspace per leggere Gmail, app mobile che si connette a Stripe per gestire pagamenti, qualsiasi caso in cui un essere umano deve dare consenso a un'applicazione di agire per suo conto.

**Sequenza completa** (con PKCE, obbligatorio in OAuth 2.1):

1. Il client genera un `code_verifier` random (43-128 caratteri) e calcola `code_challenge = base64url(SHA256(code_verifier))`.
2. Il client redirige l'utente all'AS:

```
GET https://accounts.google.com/o/oauth2/v2/auth?
  response_type=code&
  client_id=123-abc.apps.googleusercontent.com&
  redirect_uri=https://app.example.com/oauth/callback&
  scope=https://www.googleapis.com/auth/drive.file%20openid%20email&
  state=xyz789&
  code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&
  code_challenge_method=S256
```

3. L'utente si autentica e da consenso. L'AS redirige al `redirect_uri`:

```
GET https://app.example.com/oauth/callback?code=4/0AY0e-g7...&state=xyz789
```

4. Il client verifica `state` (deve corrispondere a quello inviato — protezione CSRF) e scambia il code per i token:

```http
POST /token HTTP/1.1
Host: oauth2.googleapis.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=4/0AY0e-g7...&
redirect_uri=https://app.example.com/oauth/callback&
client_id=123-abc.apps.googleusercontent.com&
client_secret=GOCSPX-xxxx&
code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

5. L'AS verifica che `SHA256(code_verifier) == code_challenge` salvato al passo 1, valida `client_secret`, ed emette i token:

```json
{
  "access_token": "ya29.a0AfH6SMB...",
  "expires_in": 3599,
  "refresh_token": "1//0g5Y...",
  "scope": "https://www.googleapis.com/auth/drive.file openid email",
  "token_type": "Bearer",
  "id_token": "eyJhbGc..."
}
```

**Errori frequenti**:

- `redirect_uri` non registrato esattamente sull'AS (deve essere identico carattere per carattere, incluso schema e porta).
- `state` non validato → CSRF su callback.
- `code_verifier` perso tra step 1 e 4 (es. sessione utente persa). Soluzione: salvarlo in una sessione lato server o in `sessionStorage` per SPA.
- Code riutilizzato (e single-use, scade entro 10 min).

### Client Credentials

Flow machine-to-machine. Non c'e utente, c'e un'applicazione che agisce per conto proprio. Il client si autentica direttamente con `client_id` + `client_secret` e ottiene un access token con scope di sistema.

**Quando usarlo**: backend che chiama un'API per uso interno, microservizio che pubblica eventi su un service bus, automazione n8n configurata come "OAuth2 Client Credentials" per chiamare l'API Stripe da un workflow scheduled. **Mai** per agire per conto di un utente: per definizione, non c'e consenso utente.

**Richiesta**:

```http
POST /token HTTP/1.1
Host: auth.stripe.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <base64(client_id:client_secret)>

grant_type=client_credentials&
scope=read:charges write:refunds
```

**Risposta**:

```json
{
  "access_token": "eyJhbGc...",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": "read:charges write:refunds"
}
```

Note importanti:

- **Niente refresh token** in questo flow. Quando il token scade, si richiede semplicemente un nuovo token con le stesse credenziali.
- Il client deve essere `confidential`: il `client_secret` deve essere custodito in un vault, mai esposto su client pubblici.
- Per limitare il blast radius di una compromissione, emettere un `client_id`/`client_secret` distinto per ogni automazione, con scope minimi.

In n8n, il nodo "OAuth2 API" supporta nativamente Client Credentials. E la scelta corretta per integrare API server-side senza intervento utente, e va preferito a "Header Auth" con un long-lived API key statico.

### Device Authorization Grant

RFC 8628. Pensato per dispositivi senza browser o con input limitato (CLI, IoT, smart TV, ambienti server senza interfaccia grafica).

**Quando usarlo**: CLI tool aziendale che si connette a Microsoft Graph per gestire utenti AD, dispositivo IoT che si registra a un cloud provider, qualsiasi caso in cui chiedere all'utente di completare un Authorization Code flow dal dispositivo stesso e scomodo o impossibile.

**Sequenza**:

1. Il dispositivo richiede un device code:

```http
POST /devicecode HTTP/1.1
Host: login.microsoftonline.com

client_id=abc123&
scope=https://graph.microsoft.com/User.Read.All offline_access
```

2. Risposta:

```json
{
  "device_code": "GMMhmHCXhWEzkobqIHGG_EnNYYsAkukHspeYUk9E8",
  "user_code": "WDJB-MJHT",
  "verification_uri": "https://microsoft.com/devicelogin",
  "expires_in": 900,
  "interval": 5
}
```

3. Il dispositivo mostra all'utente: "Apri https://microsoft.com/devicelogin sul tuo telefono e inserisci il codice WDJB-MJHT".

4. L'utente apre il browser su un altro device, fa login normalmente, inserisce il codice, da consenso.

5. Nel frattempo, il dispositivo fa polling sull'endpoint `/token`:

```http
POST /token HTTP/1.1
Host: login.microsoftonline.com

grant_type=urn:ietf:params:oauth:grant-type:device_code&
device_code=GMMhmHCXhWEzkobqIHGG_EnNYYsAkukHspeYUk9E8&
client_id=abc123
```

Risposte possibili:
- `authorization_pending` → utente non ha ancora completato. Continua il polling all'`interval` indicato.
- `slow_down` → polling troppo aggressivo, raddoppia l'intervallo.
- `expired_token` → utente non ha completato in tempo. Riavviare flow.
- Successo → access token + refresh token.

Il flow e elegante perche non richiede di esporre il dispositivo a un browser, e separa fisicamente il canale di consenso da quello operativo. E il flow corretto per script CLI distribuiti ai colleghi: ogni utente fa login con la propria identita senza che il client debba gestire credenziali dirette.

### Resource Owner Password (deprecato)

Il client raccoglie direttamente username e password dell'utente e li invia all'AS:

```http
POST /token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=password&
username=mario.rossi@example.com&
password=Segreto123!&
client_id=abc&
client_secret=xyz&
scope=read write
```

**Mai usarlo in nuovi sistemi**. E stato esplicitamente rimosso da OAuth 2.1 (BCP `draft-ietf-oauth-security-topics`). Tre motivi:

1. Annulla il vantaggio principale di OAuth: il client vede la password in chiaro.
2. Non funziona con MFA: non c'e alcun modo per il flow di gestire un secondo fattore.
3. Non funziona con identita federate (utente Google su un AS aziendale).

Esiste solo come scorciatoia legacy per migrazioni da sistemi Basic Auth a OAuth. Anche in quel caso, va sostituito con Authorization Code o Device Grant entro un orizzonte definito.

---

## Refresh Token e Rotation

Gli access token sono volutamente short-lived (5 minuti — 1 ora tipico) per limitare il blast radius di una fuga. Quando scadono, il client usa il refresh token per ottenerne uno nuovo senza disturbare l'utente:

```http
POST /token HTTP/1.1
Host: oauth2.googleapis.com
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=1//0g5Y...&
client_id=123-abc.apps.googleusercontent.com&
client_secret=GOCSPX-xxxx
```

Il problema: i refresh token sono long-lived (7-90 giorni tipico, a volte indefiniti). Una loro fuga compromette l'account per tutto quel periodo. OAuth 2.1 e il BCP `oauth-security-topics` introducono come default la **Refresh Token Rotation**:

1. Ogni volta che il client usa un refresh token, l'AS emette un **nuovo** refresh token e **invalida il vecchio**.
2. Se il vecchio refresh token viene riusato (es. perche un attaccante l'ha rubato), l'AS lo riconosce come compromesso e **revoca l'intera famiglia** di token derivati. Sia attaccante che client legittimo perdono l'accesso.
3. Il client legittimo se ne accorge perche il prossimo refresh fallisce con `invalid_grant`, costringendo a un nuovo login interattivo. Un attrito accettabile in cambio della rilevazione automatica della compromissione.

### Pattern consigliato per token lifetime

| Caso d'uso | Access TTL | Refresh TTL | Rotation |
|------------|-----------|-------------|----------|
| Web app sensibile (banking, sanita) | 5-15 min | 8 ore (sliding) | Si |
| Web app generica | 15-60 min | 7-30 giorni | Si |
| Mobile app | 30-60 min | 90 giorni | Si |
| CLI / IoT (Device Grant) | 1 ora | 90 giorni-indefinito | Opzionale |
| Server-to-server (Client Credentials) | 1 ora | N/A | N/A |

**Sliding window vs absolute expiration**:

- **Sliding**: ogni uso del refresh token resetta il TTL. Utente attivo non viene mai disconnesso.
- **Absolute**: il refresh token ha una scadenza assoluta dal momento dell'emissione. Login forzato dopo N giorni indipendentemente dall'attivita.

Pattern combinato: sliding + absolute (es. sliding 30 giorni, absolute 180). Massima usabilita con un floor sicuro.

### Gestione rotation in workflow headless

In un workflow tool come n8n, dove il sistema e "headless" e non c'e un utente a fare login interattivo, la rotation introduce complessita: se il workflow gira ogni notte e usa il refresh token, e per qualche ragione due esecuzioni concorrenti ricevono lo stesso refresh token salvato, una invalidera l'altra. Mitigazioni:

- Lock applicativo sul record credenziali durante l'esecuzione.
- Refresh anticipato con margine (rinnova il token quando manca il 20% alla scadenza, non quando e gia scaduto).
- Salvataggio atomico del nuovo refresh token (transazione DB).

### Implementazione refresh con retry e lock

```python
import time
import threading
from datetime import datetime, timezone, timedelta


class TokenManager:
    """Gestisce il ciclo di vita dei token OAuth con refresh rotation safe.

    Caratteristiche:
    - Lock per evitare refresh concorrenti
    - Refresh anticipato (20% prima della scadenza)
    - Retry con backoff esponenziale
    - Salvataggio atomico del nuovo refresh token
    """

    def __init__(self, token_store, oauth_client, credential_id: str):
        self._store = token_store
        self._client = oauth_client
        self._credential_id = credential_id
        self._lock = threading.Lock()

    def get_valid_access_token(self) -> str:
        """Ritorna un access token valido, eseguendo refresh se necessario.

        Thread-safe: il lock previene refresh concorrenti che
        invaliderebbero il refresh token con rotation attiva.
        """
        cred = self._store.get(self._credential_id)

        # Token ancora valido con margine?
        if self._is_token_fresh(cred):
            return cred["access_token"]

        # Serve refresh — acquisisci lock
        with self._lock:
            # Double-check: un altro thread potrebbe aver gia refreshato
            cred = self._store.get(self._credential_id)
            if self._is_token_fresh(cred):
                return cred["access_token"]

            return self._do_refresh(cred)

    def _is_token_fresh(self, cred: dict) -> bool:
        """Verifica se il token e ancora valido con margine del 20%."""
        expires_at = datetime.fromisoformat(cred["access_expires_at"])
        created_at = datetime.fromisoformat(cred.get("access_created_at", cred["access_expires_at"]))

        total_lifetime = (expires_at - created_at).total_seconds()
        margin = total_lifetime * 0.2  # 20% margin
        effective_expiry = expires_at - timedelta(seconds=margin)

        return datetime.now(timezone.utc) < effective_expiry

    def _do_refresh(self, cred: dict, max_retries: int = 3) -> str:
        """Esegue il refresh con retry e backoff."""
        for attempt in range(max_retries):
            try:
                response = self._client.refresh_token(
                    refresh_token=cred["refresh_token"],
                    client_id=cred["client_id"],
                    client_secret=cred["client_secret"],
                )

                # Salvataggio atomico (transazione DB)
                self._store.update_tokens(
                    credential_id=self._credential_id,
                    access_token=response["access_token"],
                    access_expires_at=(
                        datetime.now(timezone.utc)
                        + timedelta(seconds=response["expires_in"])
                    ).isoformat(),
                    # Se il provider fa rotation, usa il nuovo refresh token
                    refresh_token=response.get(
                        "refresh_token", cred["refresh_token"]
                    ),
                )

                return response["access_token"]

            except InvalidGrantError:
                # Refresh token revocato o gia usato (rotation collision)
                # Non ritentare: serve nuovo login interattivo
                raise TokenExpiredError(
                    f"Refresh token per {self._credential_id} invalidato. "
                    "Necessario nuovo consenso interattivo."
                )

            except (ConnectionError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    time.sleep(wait)
                    continue
                raise RefreshFailedError(f"Refresh fallito dopo {max_retries} tentativi: {e}")

        raise RefreshFailedError("Max retries exceeded")
```

---

## Configurazione

### PKCE deep dive

PKCE (Proof Key for Code Exchange, RFC 7636) nasce per proteggere il flow Authorization Code su client pubblici (mobile, SPA). In OAuth 2.1 e **obbligatorio anche per client confidenziali**.

Il problema che risolve: su mobile, il `redirect_uri` puo essere uno schema custom (`com.example.app://callback`). Un'altra app malevola installata sullo stesso telefono potrebbe registrare lo stesso schema e intercettare il `code`. Senza PKCE, l'attaccante potrebbe scambiare il code per un access token usando il `client_id` dell'app legittima (che e pubblico).

PKCE risolve facendo in modo che, oltre al `code`, serva conoscere il `code_verifier` originale, che resta sempre solo lato client legittimo.

**Calcolo**:

```
code_verifier = random_string(43-128 chars, [A-Z][a-z][0-9]-._~)
code_challenge = base64url(SHA256(code_verifier))
code_challenge_method = "S256"
```

Esempio in Python:

```python
import secrets
import hashlib
import base64

code_verifier = secrets.token_urlsafe(64)  # ~86 chars
challenge_bytes = hashlib.sha256(code_verifier.encode("ascii")).digest()
code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode("ascii").rstrip("=")
```

**Mai usare `plain` come `code_challenge_method`** — e ammesso dallo standard ma equivale a non avere PKCE. Sempre `S256`.

### DPoP — Demonstrating Proof-of-Possession

RFC 9449. Estensione che lega un access token a una specifica chiave privata in possesso del client. Anche se il token viene rubato (es. da un log o da un proxy), non e utilizzabile senza la chiave.

Funzionamento:

1. Il client genera una keypair locale (es. ES256).
2. Su ogni richiesta, costruisce un JWT chiamato `DPoP proof`, firmato con la chiave privata, contenente il metodo HTTP, l'URL e un timestamp.
3. Invia il proof nell'header `DPoP: <jwt>` insieme all'access token in `Authorization: DPoP <token>` (notare: `DPoP` invece di `Bearer`).
4. Il Resource Server verifica la firma del proof e verifica che la chiave pubblica corrisponda a quella legata al token (claim `cnf.jkt`).

```python
import time
import json
import hashlib
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import jwt  # PyJWT

class DPoPProofGenerator:
    """Genera DPoP proof JWT per ogni richiesta API."""

    def __init__(self):
        # Genera keypair ES256 (una volta, persisti la chiave)
        self._private_key = ec.generate_private_key(ec.SECP256R1())
        self._public_key = self._private_key.public_key()

    def get_jwk_thumbprint(self) -> str:
        """Calcola JWK thumbprint (RFC 7638) per il claim cnf.jkt."""
        pub_numbers = self._public_key.public_numbers()
        jwk = {
            "crv": "P-256",
            "kty": "EC",
            "x": base64.urlsafe_b64encode(
                pub_numbers.x.to_bytes(32, "big")
            ).decode().rstrip("="),
            "y": base64.urlsafe_b64encode(
                pub_numbers.y.to_bytes(32, "big")
            ).decode().rstrip("="),
        }
        jwk_json = json.dumps(jwk, separators=(",", ":"), sort_keys=True)
        return base64.urlsafe_b64encode(
            hashlib.sha256(jwk_json.encode()).digest()
        ).decode().rstrip("=")

    def generate_proof(self, method: str, url: str, access_token: str = "") -> str:
        """Genera DPoP proof JWT per una specifica richiesta.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL completo della richiesta
            access_token: Se presente, include ath (access token hash)
        """
        headers = {
            "typ": "dpop+jwt",
            "alg": "ES256",
            "jwk": self._get_public_jwk(),
        }
        payload = {
            "jti": secrets.token_urlsafe(16),
            "htm": method,
            "htu": url,
            "iat": int(time.time()),
        }
        if access_token:
            # Access token hash per binding
            ath = base64.urlsafe_b64encode(
                hashlib.sha256(access_token.encode()).digest()
            ).decode().rstrip("=")
            payload["ath"] = ath

        return jwt.encode(payload, self._private_key, algorithm="ES256", headers=headers)

    def _get_public_jwk(self) -> dict:
        """Ritorna la public key in formato JWK."""
        pub_numbers = self._public_key.public_numbers()
        return {
            "crv": "P-256",
            "kty": "EC",
            "x": base64.urlsafe_b64encode(
                pub_numbers.x.to_bytes(32, "big")
            ).decode().rstrip("="),
            "y": base64.urlsafe_b64encode(
                pub_numbers.y.to_bytes(32, "big")
            ).decode().rstrip("="),
        }
```

DPoP e un'alternativa piu leggera a mTLS-bound tokens (RFC 8705) e sta guadagnando trazione in scenari API con rischio elevato di token leak (es. open banking PSD2). Per integrazioni standard SaaS e ancora poco diffuso, ma vale la pena conoscerlo per provider che lo supportano (es. Auth0, alcuni AS bancari).

### Scope design

Lo scope e il principio di least privilege applicato a OAuth. Errori frequenti:

- **Scope monolitici** (`admin`, `full_access`). Compromissione di un token = compromissione totale.
- **Scope vaghi** (`user`, `data`). Difficile capire cosa permette davvero.
- **Mancanza di separazione read/write**. `invoices` invece di `read:invoices` + `write:invoices`.

Pattern consigliato — granularita verbo:risorsa:

```
read:invoices
write:invoices
read:customers
write:customers
admin:users   ← solo per task amministrativi, non per operativita quotidiana
```

In automazioni multi-tenant, valutare anche scope tenant-aware:

```
read:invoices:tenant_42
```

Anche se non standard, puo essere implementato in AS custom (Keycloak con scope dinamici) o tramite claim aggiuntivi (`tenant_id` nel payload del JWT) verificati lato Resource Server.

**Dynamic consent**: alcuni provider (Microsoft Graph, Google) permettono al client di richiedere scope incrementali. Si parte con scope minimi al primo login e si aggiungono nuovi scope solo quando servono, mostrando un nuovo consent screen all'utente. Riduce attrito iniziale e aumenta la fiducia.

### Token storage nei workflow tools

Ogni workflow tool ha il proprio modello di credenziali. Conoscerlo a fondo e critico per chi lavora con dati sensibili.

**n8n**:
- Le credenziali sono salvate in un campo `data` cifrato AES-256-CBC.
- La chiave di cifratura e definita in `N8N_ENCRYPTION_KEY` (variabile env). **Critico**: se la chiave si perde, le credenziali sono irrecuperabili. Backup separato della chiave obbligatorio.
- Il refresh token viene aggiornato automaticamente dal node OAuth2 al prossimo refresh.
- In modalita "External Secrets" (Enterprise), n8n puo leggere credenziali da Vault, AWS Secrets Manager, Infisical.

**Make (ex Integromat)**:
- Le "Connections" sono cifrate sui server EU di Make.
- Refresh automatico gestito dalla piattaforma.
- Consenti ad ogni scenario di vedere solo le connection necessarie (least privilege all'interno dell'organizzazione Make).

**Zapier**:
- "OAuth Apps" gestite centralmente.
- Refresh trasparente.
- Audit log degli accessi disponibile su piano Team+.

**Power Automate**:
- "Connection References" disaccoppiate dai flow: stesso flow esportato in dev/prod usa connection diverse senza modifiche.
- Token salvati nel data store di Microsoft, cifrati e gestiti dalla piattaforma.

**Custom (workflow scritti a mano)**:
- HashiCorp Vault con dynamic secret engine OAuth: Vault stesso fa il flow OAuth e fornisce access token al client per N minuti, poi rinnova in trasparenza.
- AWS Secrets Manager con rotation lambda custom che esegue il refresh.
- Mai salvare token in file `.env` committati in git.

### Multi-tenant token vault

Il caso piu complesso: un SaaS come FatturaFlow che gestisce 500 commercialisti, ognuno con credenziali OAuth verso decine di provider (Agenzia delle Entrate, banche, gestionali).

Pattern di riferimento:

1. **Schema DB**:
   ```sql
   CREATE TABLE credentials (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     tenant_id UUID NOT NULL REFERENCES tenants(id),
     provider TEXT NOT NULL,         -- "google", "stripe", "ade"
     scope TEXT NOT NULL,
     access_token_enc BYTEA NOT NULL,
     refresh_token_enc BYTEA,
     access_expires_at TIMESTAMPTZ NOT NULL,
     refresh_expires_at TIMESTAMPTZ,
     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
     updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
     last_used_at TIMESTAMPTZ,
     rotation_count INTEGER DEFAULT 0,
     UNIQUE (tenant_id, provider, scope)
   );

   -- Row Level Security
   ALTER TABLE credentials ENABLE ROW LEVEL SECURITY;
   CREATE POLICY tenant_isolation ON credentials
       USING (tenant_id = current_setting('app.current_tenant')::uuid);

   -- Audit log
   CREATE TABLE credential_audit (
     id BIGSERIAL PRIMARY KEY,
     credential_id UUID REFERENCES credentials(id),
     tenant_id UUID NOT NULL,
     action TEXT NOT NULL,  -- "create", "refresh", "use", "revoke"
     actor TEXT NOT NULL,
     timestamp_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
     details JSONB
   );
   ```

2. **Encryption at rest**: ogni `*_enc` e cifrato con AES-256-GCM, usando una chiave per tenant derivata da una root key in KMS (AWS KMS, GCP Cloud KMS, o Vault Transit). Compromissione del DB != compromissione dei token (servirebbe anche la root key).

3. **Audit log**: ogni accesso a `credentials` (lettura, refresh, uso) viene loggato in tabella separata con `who/when/why`. In caso di incidente forensics, si sa esattamente quali token sono stati toccati.

4. **Separazione netta tenant**: query a `credentials` sempre filtrate da `tenant_id`. Row-Level Security in Postgres come second line of defense.

5. **Rotation forzata**: job notturno che identifica refresh token piu vecchi di N giorni e li forza a re-auth interattiva del cliente.

6. **Revoca multi-tenant**: endpoint admin che permette di invalidare tutti i token di un tenant in un colpo solo (es. disdetta servizio, sospetta compromissione account utente).

### OAuth Proxy per legacy app

Scenario: un gestionale legacy supporta solo Basic Auth o API key statica, ma vogliamo che il workflow tool si autentichi con OAuth.

Pattern OAuth Proxy: un microservizio intermedio espone un endpoint OAuth standard al workflow tool, gestisce internamente la conversione in Basic Auth verso il legacy, custodisce le credenziali statiche in vault, registra ogni accesso.

```
[n8n] --OAuth Bearer--> [oauth-proxy] --Basic Auth--> [Legacy ERP]
                              |
                              +--> [Vault per credenziali legacy]
                              +--> [Audit log]
```

Vantaggi:
- Il workflow tool non vede mai la credenziale legacy.
- Si possono emettere "OAuth client" distinti per ogni team/automazione, con scope custom che il proxy traduce.
- Audit centralizzato.

### Provider OAuth interno con Keycloak

Quando si vuole avere un AS aziendale per i propri sistemi interni (no provider esterno), Keycloak e la scelta open-source standard. Setup minimo:

1. Deploy Keycloak (Docker, Kubernetes, o JAR standalone).
2. Crea **Realm** dedicato (`internal-tools`).
3. In Realm > Clients, crea un client per ogni applicazione:
   - `Client ID`: `n8n-prod`
   - `Client authentication`: ON (confidential)
   - `Authentication flow`: Standard flow + Direct access grants disabled
   - `Valid redirect URIs`: `https://n8n.example.com/rest/oauth2-credential/callback`
   - `PKCE Code Challenge Method`: S256
4. Definisci **Client Scopes** granulari (`read:invoices`, `write:invoices`).
5. Definisci **Roles** e mappali su scope se serve RBAC.
6. Configura **Token Lifespan**:
   - Access Token: 15 minuti.
   - Refresh Token: 8 ore con sliding, 30 giorni assoluto.
   - Refresh Token Rotation: ON.
7. Esporta `client_secret` e configuralo in n8n come "Generic OAuth2".
8. Endpoint discovery: `https://keycloak.example.com/realms/internal-tools/.well-known/openid-configuration`.

Hardening minimo: Keycloak dietro reverse proxy con HTTPS valido, TLS 1.2+, password policy forte per admin, MFA obbligatorio per admin, backup regolare del DB.

---

## Implementazione completa Python — OAuth Client Library

```python
"""
Client OAuth 2.0 completo per workflow automation.

Supporta:
- Authorization Code + PKCE
- Client Credentials
- Device Authorization Grant
- Refresh Token con rotation
- JWKS validation
- Token caching con thread safety
"""

import hashlib
import base64
import secrets
import time
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from typing import Optional

import requests


@dataclass
class OAuthConfig:
    """Configurazione del client OAuth."""
    client_id: str
    client_secret: str = ""
    authorization_endpoint: str = ""
    token_endpoint: str = ""
    device_authorization_endpoint: str = ""
    revocation_endpoint: str = ""
    jwks_uri: str = ""
    redirect_uri: str = ""
    scopes: list[str] = None

    @classmethod
    def from_discovery(cls, issuer_url: str, client_id: str, client_secret: str = "", **kwargs):
        """Carica configurazione da OpenID Discovery endpoint."""
        discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
        resp = requests.get(discovery_url, timeout=10)
        resp.raise_for_status()
        meta = resp.json()

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            authorization_endpoint=meta.get("authorization_endpoint", ""),
            token_endpoint=meta["token_endpoint"],
            device_authorization_endpoint=meta.get("device_authorization_endpoint", ""),
            revocation_endpoint=meta.get("revocation_endpoint", ""),
            jwks_uri=meta.get("jwks_uri", ""),
            **kwargs,
        )


@dataclass
class TokenResponse:
    """Risposta da un token endpoint."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str = ""
    scope: str = ""
    id_token: str = ""
    issued_at: float = 0.0

    @property
    def expires_at(self) -> datetime:
        return datetime.fromtimestamp(
            self.issued_at + self.expires_in, tz=timezone.utc
        )

    @property
    def is_expired(self) -> bool:
        margin = self.expires_in * 0.2  # 20% margin
        return time.time() > (self.issued_at + self.expires_in - margin)


class PKCEHelper:
    """Helper per generazione e gestione PKCE."""

    @staticmethod
    def generate() -> tuple[str, str]:
        """Genera code_verifier e code_challenge.

        Returns:
            (code_verifier, code_challenge)
        """
        verifier = secrets.token_urlsafe(64)
        challenge_bytes = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(challenge_bytes).decode("ascii").rstrip("=")
        return verifier, challenge


class OAuthClient:
    """Client OAuth 2.0 completo."""

    def __init__(self, config: OAuthConfig):
        self._config = config
        self._session = requests.Session()
        self._token: Optional[TokenResponse] = None
        self._lock = threading.Lock()

    # --- Authorization Code + PKCE ---

    def get_authorization_url(self, state: str = "", extra_params: dict = None) -> tuple[str, str, str]:
        """Genera URL di autorizzazione con PKCE.

        Returns:
            (authorization_url, code_verifier, state)
        """
        if not state:
            state = secrets.token_urlsafe(32)

        verifier, challenge = PKCEHelper.generate()

        params = {
            "response_type": "code",
            "client_id": self._config.client_id,
            "redirect_uri": self._config.redirect_uri,
            "scope": " ".join(self._config.scopes or []),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        if extra_params:
            params.update(extra_params)

        url = f"{self._config.authorization_endpoint}?{urlencode(params)}"
        return url, verifier, state

    def exchange_code(self, code: str, code_verifier: str) -> TokenResponse:
        """Scambia authorization code per token."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._config.redirect_uri,
            "client_id": self._config.client_id,
            "code_verifier": code_verifier,
        }
        if self._config.client_secret:
            data["client_secret"] = self._config.client_secret

        return self._token_request(data)

    # --- Client Credentials ---

    def client_credentials(self, scopes: list[str] = None) -> TokenResponse:
        """Esegue Client Credentials flow."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
        }
        if scopes:
            data["scope"] = " ".join(scopes)

        return self._token_request(data)

    # --- Device Authorization Grant ---

    def start_device_flow(self, scopes: list[str] = None) -> dict:
        """Avvia Device Authorization Grant.

        Returns:
            Dict con device_code, user_code, verification_uri, etc.
        """
        data = {
            "client_id": self._config.client_id,
        }
        if scopes:
            data["scope"] = " ".join(scopes)

        resp = self._session.post(
            self._config.device_authorization_endpoint,
            data=data,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def poll_device_flow(self, device_code: str, interval: int = 5, timeout: int = 900) -> TokenResponse:
        """Polling per completamento Device Authorization Grant.

        Blocca fino a quando l'utente completa l'autenticazione
        o il timeout scade.
        """
        deadline = time.time() + timeout
        current_interval = interval

        while time.time() < deadline:
            time.sleep(current_interval)

            try:
                data = {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                    "client_id": self._config.client_id,
                }
                return self._token_request(data)

            except OAuthError as e:
                if e.error == "authorization_pending":
                    continue
                elif e.error == "slow_down":
                    current_interval += 5
                    continue
                elif e.error == "expired_token":
                    raise DeviceFlowExpiredError("Device code expired. Restart the flow.")
                else:
                    raise

        raise DeviceFlowExpiredError("Device flow timed out")

    # --- Refresh ---

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Esegue refresh del token."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._config.client_id,
        }
        if self._config.client_secret:
            data["client_secret"] = self._config.client_secret

        return self._token_request(data)

    # --- Revoke ---

    def revoke_token(self, token: str, token_type_hint: str = "refresh_token") -> None:
        """Revoca un token presso l'AS."""
        if not self._config.revocation_endpoint:
            raise NotImplementedError("Revocation endpoint not configured")

        data = {
            "token": token,
            "token_type_hint": token_type_hint,
            "client_id": self._config.client_id,
        }
        if self._config.client_secret:
            data["client_secret"] = self._config.client_secret

        resp = self._session.post(
            self._config.revocation_endpoint,
            data=data,
            timeout=10,
        )
        resp.raise_for_status()

    # --- Token management ---

    def get_valid_token(self) -> str:
        """Ritorna un access token valido, con refresh automatico se necessario."""
        with self._lock:
            if self._token and not self._token.is_expired:
                return self._token.access_token

            if self._token and self._token.refresh_token:
                self._token = self.refresh_access_token(self._token.refresh_token)
                return self._token.access_token

            # Client credentials fallback
            if self._config.client_secret and not self._config.redirect_uri:
                self._token = self.client_credentials(self._config.scopes)
                return self._token.access_token

            raise TokenExpiredError("No valid token and no way to refresh")

    # --- Internal ---

    def _token_request(self, data: dict) -> TokenResponse:
        """Esegue richiesta al token endpoint."""
        resp = self._session.post(
            self._config.token_endpoint,
            data=data,
            timeout=30,
        )

        if resp.status_code != 200:
            error_data = resp.json()
            raise OAuthError(
                error=error_data.get("error", "unknown"),
                error_description=error_data.get("error_description", ""),
            )

        result = resp.json()
        token = TokenResponse(
            access_token=result["access_token"],
            token_type=result.get("token_type", "Bearer"),
            expires_in=result.get("expires_in", 3600),
            refresh_token=result.get("refresh_token", ""),
            scope=result.get("scope", ""),
            id_token=result.get("id_token", ""),
            issued_at=time.time(),
        )
        self._token = token
        return token


class OAuthError(Exception):
    def __init__(self, error: str, error_description: str = ""):
        self.error = error
        self.error_description = error_description
        super().__init__(f"{error}: {error_description}")


class TokenExpiredError(OAuthError):
    def __init__(self, message: str):
        super().__init__("token_expired", message)


class DeviceFlowExpiredError(OAuthError):
    def __init__(self, message: str):
        super().__init__("expired_token", message)
```

---

## Integrazione provider-specific

### Google Workspace

```python
# Configurazione per Google OAuth
google_config = OAuthConfig.from_discovery(
    issuer_url="https://accounts.google.com",
    client_id="123-abc.apps.googleusercontent.com",
    client_secret="GOCSPX-xxxx",
    redirect_uri="https://app.example.com/oauth/callback",
    scopes=[
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/gmail.send",
        "openid",
        "email",
    ],
)

client = OAuthClient(google_config)

# Google-specific: per ottenere il refresh token serve
# access_type=offline e prompt=consent
url, verifier, state = client.get_authorization_url(
    extra_params={
        "access_type": "offline",
        "prompt": "consent",
    }
)
```

**Quirk Google**:
- Il refresh token viene emesso solo al primo consenso con `access_type=offline&prompt=consent`.
- Se l'utente ha gia dato consenso, Google non riemette il refresh token a meno che non si forzi `prompt=consent`.
- Per revocare e riprovare: l'utente va su `myaccount.google.com/permissions` e rimuove l'app.
- Scope `drive.file` limita l'accesso ai soli file creati dall'app. Molto piu sicuro di `drive` (accesso a tutto Drive).

### Microsoft Graph / Azure AD

```python
# Azure AD / Microsoft Entra ID
microsoft_config = OAuthConfig(
    client_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    client_secret="your-client-secret",
    authorization_endpoint="https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
    token_endpoint="https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
    device_authorization_endpoint="https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode",
    revocation_endpoint="",  # Microsoft non supporta RFC 7009
    redirect_uri="https://app.example.com/auth/callback",
    scopes=[
        "https://graph.microsoft.com/User.Read",
        "https://graph.microsoft.com/Mail.Send",
        "offline_access",  # per refresh token
    ],
)
```

**Quirk Microsoft**:
- `{tenant}` puo essere: `common` (multi-tenant), `organizations` (solo aziendale), `consumers` (solo personale), o un tenant ID specifico.
- Gli scope Microsoft Graph richiedono prefisso completo (`https://graph.microsoft.com/User.Read`), tranne gli OIDC standard (`openid`, `email`, `profile`, `offline_access`).
- `offline_access` e uno scope esplicito necessario per ottenere il refresh token.
- Microsoft non supporta revocation endpoint (RFC 7009). Per revocare, usare l'API Graph: `DELETE /me/oauth2PermissionGrants/{id}`.
- Il consent admin (per scope che richiedono approvazione admin) va fatto da un admin globale della tenant Azure AD.

### GitHub Apps

```python
# GitHub App — autenticazione come app (non come utente)
# GitHub usa JWT per app authentication, non Client Credentials standard

import jwt  # PyJWT
import time
from cryptography.hazmat.primitives import serialization


def get_github_app_token(
    app_id: int,
    private_key_path: str,
    installation_id: int,
) -> str:
    """Ottiene un installation access token per una GitHub App.

    GitHub non usa OAuth Client Credentials standard.
    Il flow e:
    1. Crea un JWT firmato con la private key dell'app
    2. Scambia il JWT per un installation token
    """
    # Leggi private key
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Crea JWT per l'app
    now = int(time.time())
    payload = {
        "iat": now - 60,      # issued at (60s nel passato per clock skew)
        "exp": now + (10 * 60),  # scadenza 10 minuti
        "iss": app_id,
    }
    app_jwt = jwt.encode(payload, private_key, algorithm="RS256")

    # Scambia per installation token
    resp = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["token"]
```

**Quirk GitHub**:
- GitHub App usa JWT + installation token, non OAuth Client Credentials.
- L'installation token ha TTL di 1 ora e non e rinnovabile. Rigenera un nuovo JWT e richiedi un nuovo token.
- Per OAuth user-to-server (quando un utente autorizza l'app), GitHub supporta Authorization Code + PKCE standard.
- GitHub Personal Access Token (PAT) fine-grained: alternativa piu semplice per script, con scope granulari e scadenza configurabile.

### Stripe Connect

```python
# Stripe Connect — OAuth per marketplace multi-venditore
stripe_config = OAuthConfig(
    client_id="ca_xxxx",
    client_secret="sk_live_xxxx",  # Stripe usa la API key come secret
    authorization_endpoint="https://connect.stripe.com/oauth/authorize",
    token_endpoint="https://connect.stripe.com/oauth/token",
    revocation_endpoint="https://connect.stripe.com/oauth/deauthorize",
    redirect_uri="https://app.example.com/stripe/callback",
    scopes=["read_write"],
)

# Stripe-specific: la risposta token contiene anche l'account ID collegato
# {
#   "access_token": "sk_live_connected_account_xxxx",
#   "token_type": "bearer",
#   "stripe_user_id": "acct_xxxx",
#   "scope": "read_write",
#   "livemode": true,
#   "stripe_publishable_key": "pk_live_xxxx"
# }
```

---

## private_key_jwt — autenticazione asimmetrica

### Il problema di client_secret

`client_secret` e un segreto simmetrico condiviso tra client e AS. Problemi:

1. **Condivisione**: se l'AS viene compromesso, il secret e compromesso.
2. **Rotazione complessa**: cambiare il secret richiede coordinamento tra client e AS.
3. **Logging accidentale**: il secret puo finire nei log dell'AS se il token endpoint logga i parametri POST.

### private_key_jwt (RFC 7523)

Il client si autentica firmando un JWT con la propria chiave privata. L'AS verifica la firma con la chiave pubblica registrata. Nessun secret condiviso.

```python
import time
import uuid
import jwt  # PyJWT
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class PrivateKeyJWTAuth:
    """Autenticazione OAuth via private_key_jwt (RFC 7523)."""

    def __init__(self, client_id: str, private_key_path: str, token_endpoint: str):
        self._client_id = client_id
        self._token_endpoint = token_endpoint
        with open(private_key_path, "rb") as f:
            self._private_key = serialization.load_pem_private_key(
                f.read(), password=None
            )

    def create_client_assertion(self) -> str:
        """Crea il JWT di autenticazione client (client_assertion).

        Il JWT contiene:
        - iss: client_id
        - sub: client_id
        - aud: token endpoint dell'AS
        - jti: unique ID (anti-replay)
        - exp: scadenza (5 minuti)
        - iat: issued at
        """
        now = int(time.time())
        payload = {
            "iss": self._client_id,
            "sub": self._client_id,
            "aud": self._token_endpoint,
            "jti": str(uuid.uuid4()),
            "exp": now + 300,  # 5 minuti
            "iat": now,
        }
        return jwt.encode(payload, self._private_key, algorithm="RS256")

    def get_token_params(self) -> dict:
        """Ritorna i parametri per la richiesta token con private_key_jwt."""
        return {
            "client_id": self._client_id,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": self.create_client_assertion(),
        }


# Utilizzo con Client Credentials
auth = PrivateKeyJWTAuth(
    client_id="my-service",
    private_key_path="/etc/secrets/oauth-private-key.pem",
    token_endpoint="https://keycloak.example.com/realms/prod/protocol/openid-connect/token",
)

resp = requests.post(
    "https://keycloak.example.com/realms/prod/protocol/openid-connect/token",
    data={
        "grant_type": "client_credentials",
        "scope": "read:invoices",
        **auth.get_token_params(),
    },
    timeout=10,
)
token = resp.json()
```

### Setup Keycloak per private_key_jwt

1. Realm > Clients > `my-service` > Settings:
   - `Client authentication`: ON
   - `Client Assertion signing alg`: RS256
2. Credentials tab:
   - `Client Authenticator`: Signed JWT
   - Import la chiave pubblica (JWKS o PEM)
3. Il client non ha piu `client_secret` — solo la chiave pubblica registrata.

---

## Token lifecycle management per workflow

### Diagramma di stato del token

```
                    ┌──────────────┐
                    │   CREATED    │
                    │  (token      │
                    │   emesso)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   ACTIVE     │◄────────────┐
                    │  (valido,    │              │
                    │   in uso)    │              │ refresh
                    └──────┬──────┘              │ (nuovo access
                           │                     │  token)
                    ┌──────▼──────┐              │
                    │  EXPIRING    │──────────────┘
                    │  (< 20%     │
                    │   lifetime)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──┐  ┌──────▼──┐  ┌─────▼────┐
       │ EXPIRED  │  │ REVOKED  │  │ ROTATED  │
       │ (scaduto │  │ (utente  │  │ (refresh │
       │  naturale│  │  revoca) │  │  rotation│
       │ )        │  │          │  │  invalido│
       └─────────┘  └─────────┘  │  vecchio) │
                                  └──────────┘
```

### Token refresh scheduler per workflow

```python
import sched
import time
import threading
import logging

logger = logging.getLogger("token.scheduler")


class TokenRefreshScheduler:
    """Scheduler che mantiene i token sempre freschi per i workflow.

    Per ogni credenziale registrata, schedula il refresh
    prima della scadenza (con margine del 20%).
    """

    def __init__(self, token_manager: TokenManager):
        self._manager = token_manager
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._active = True
        self._thread = None

    def start(self):
        """Avvia lo scheduler in background."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self._active:
            self._schedule_all_refreshes()
            self._scheduler.run(blocking=True)
            time.sleep(60)  # check ogni minuto

    def _schedule_all_refreshes(self):
        """Schedula refresh per tutte le credenziali."""
        credentials = self._manager.list_credentials()

        for cred in credentials:
            expires_at = datetime.fromisoformat(cred["access_expires_at"])
            now = datetime.now(timezone.utc)
            remaining = (expires_at - now).total_seconds()

            if remaining <= 0:
                # Gia scaduto, refresh immediato
                self._scheduler.enter(0, 1, self._refresh, (cred["id"],))
            elif remaining < cred.get("expires_in", 3600) * 0.2:
                # Dentro il margine 20%, refresh subito
                self._scheduler.enter(0, 2, self._refresh, (cred["id"],))
            else:
                # Schedula refresh al 80% del lifetime
                refresh_in = remaining - (cred.get("expires_in", 3600) * 0.2)
                self._scheduler.enter(refresh_in, 3, self._refresh, (cred["id"],))

    def _refresh(self, credential_id: str):
        """Esegue refresh di una singola credenziale."""
        try:
            self._manager.get_valid_access_token(credential_id)
            logger.info("Token refreshed: %s", credential_id)
        except TokenExpiredError:
            logger.error(
                "Token %s requires interactive re-auth", credential_id
            )
            # Notifica il proprietario (email, Slack, etc.)
        except Exception as e:
            logger.error("Token refresh failed for %s: %s", credential_id, e)

    def stop(self):
        self._active = False
```

---

## Sicurezza avanzata

### Token binding con mTLS (RFC 8705)

mTLS-bound access token: il token e legato al certificato TLS del client. Anche se il token viene rubato, non e utilizzabile senza il certificato privato.

```python
# Richiesta token con mTLS binding
resp = requests.post(
    "https://as.example.com/token",
    data={
        "grant_type": "client_credentials",
        "client_id": "my-service",
    },
    cert=("/etc/certs/client.pem", "/etc/certs/client-key.pem"),
    timeout=10,
)

# Il token contiene claim cnf.x5t#S256 = thumbprint del certificato
# Il RS verifica che il certificato TLS della connessione corrente
# corrisponda al thumbprint nel token
```

### Checklist sicurezza token per workflow

| Controllo | Obbligatorio | Note |
|---|---|---|
| Token in vault, mai in env file | Si | Vault, KMS, Secrets Manager |
| Encryption at rest per refresh token | Si | AES-256-GCM con chiave in KMS |
| PKCE S256 su tutti i flow auth code | Si | Anche per confidential client |
| Scope minimi per workflow | Si | Un client per workflow |
| Validazione iss/aud/exp su ogni JWT | Si | Mai fidarsi senza verifica |
| Refresh anticipato (margine 20%) | Si | Evita race condition |
| Lock su refresh per concorrenza | Si | Un solo refresh alla volta |
| Revoca token su decommission workflow | Si | Cleanup esplicito |
| Audit log operazioni token | Si | Creazione, refresh, uso, revoca |
| Rate limiting su token endpoint | Consigliato | Protegge da brute force |
| DPoP o mTLS per high-value API | Consigliato | Proof-of-possession |
| JWKS cache con TTL | Si | Max 24h, refresh on miss |
| Monitoring `invalid_grant` rate | Si | Indicatore compromissione |

---

## Monitoring e alerting

### Metriche chiave

```python
from opentelemetry import metrics

meter = metrics.get_meter("oauth.tokens")

token_refreshes = meter.create_counter(
    "oauth.token.refresh.total",
    description="Token refresh per provider e stato",
)
token_refresh_duration = meter.create_histogram(
    "oauth.token.refresh.duration_seconds",
    description="Durata refresh token",
)
token_errors = meter.create_counter(
    "oauth.token.errors.total",
    description="Errori token per tipo",
)
active_tokens = meter.create_up_down_counter(
    "oauth.tokens.active",
    description="Token attivi per provider",
)
```

### Prometheus alerting rules

```yaml
groups:
  - name: oauth_token_health
    rules:
      - alert: OAuthRefreshFailureRate
        expr: |
          rate(oauth_token_errors_total{error="invalid_grant"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "OAuth refresh failure rate elevato"
          description: |
            Piu di 0.1 invalid_grant/sec per 5 minuti.
            Possibile token compromesso o provider issue.

      - alert: OAuthTokenExpiringSoon
        expr: |
          oauth_token_expiry_seconds < 300
          AND
          oauth_token_refresh_token_available == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Token OAuth in scadenza senza refresh token"
          description: |
            Token per {{ $labels.provider }} scade tra meno di 5 minuti
            e non c'e refresh token disponibile.
            Necessario intervento manuale per ri-autenticazione.

      - alert: OAuthProviderUnreachable
        expr: |
          rate(oauth_token_errors_total{error="connection_error"}[5m]) > 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Provider OAuth non raggiungibile"
```

---

## Best Practices

**Architetturali**:

- Un `client_id` distinto per ogni workflow/automazione. Mai riusare lo stesso client tra produzione, staging e sviluppo.
- Scope minimi assoluti. Se un workflow scrive solo su Drive in una cartella specifica, usa `drive.file` (file creati dall'app) invece di `drive` (tutto Drive).
- `redirect_uri` registrate come allowlist esatta. Mai wildcard, mai schema diversi (`http://` in dev, `https://` in prod).
- HTTPS obbligatorio per tutti i `redirect_uri` di produzione. Localhost in dev e l'unica eccezione tollerata.

**Implementative**:

- Validazione `state` su ogni callback Authorization Code. Generare `state` random crypto-safe (`secrets.token_urlsafe(32)`).
- Validazione `nonce` su ogni ID token OIDC. Lega il token alla sessione di login specifica.
- PKCE S256 sempre, anche su confidential client.
- Refresh anticipato: rinnova il token quando manca il 20% alla scadenza, non quando e gia scaduto. Evita race condition durante chiamate concorrenti.
- Backoff esponenziale su `429 Too Many Requests` dall'AS.

**Storage**:

- Mai loggare access token, refresh token, o ID token. Mai metterli in URL come query param (saranno nei log del web server, nei log del browser, nel referer header).
- Cifratura at rest dei refresh token con chiave gestita da KMS/Vault.
- Revoca esplicita all'endpoint `/revoke` quando un utente disinstalla l'integrazione.
- Audit log immutabile delle operazioni sui token (creazione, refresh, revoca).

**Operative**:

- Monitoring sui tassi di errore `invalid_grant`: un picco improvviso puo indicare rotation runaway o token leak.
- Alerting su uso di refresh token scaduti / revocati: e un possibile indicatore di compromissione.
- Audit periodico degli scope concessi: rimuovere quelli non piu usati (least privilege drift).
- Dry-run di revoca: prima di disattivare un'integrazione in produzione, simulare la revoca su un tenant di staging e verificare che non si rompa nulla in modo inatteso.

---

## Troubleshooting — 18 problemi comuni

### 1. `invalid_grant` su refresh token

Il refresh token e scaduto, revocato, o (caso comune con Refresh Token Rotation) gia usato. Soluzione: nuovo flow Authorization Code interattivo. Mitigazione: usare lock applicativo per evitare uso concorrente dello stesso refresh token.

### 2. `redirect_uri_mismatch`

L'URI inviato nel flow non corrisponde a quello registrato sull'AS. Confronto carattere per carattere:
- Trailing slash (`/callback` vs `/callback/`)
- Schema (`http` vs `https`)
- Porta esplicita (`localhost:3000` vs `localhost`)
- Encoding di caratteri speciali

### 3. `invalid_client` su Client Credentials

Tre cause comuni: client_secret errato, client non abilitato per Client Credentials grant, scope richiesti non assegnati al client su AS.

### 4. JWT signature verification fails

La chiave pubblica usata per validare non corrisponde a quella usata per firmare:
- `kid` nell'header del JWT non corrisponde a nessuna chiave nel JWKS endpoint
- L'algoritmo dichiarato in `alg` non e quello atteso (mai accettare `none`)
- Cache JWKS troppo vecchia: l'AS puo aver ruotato le chiavi. TTL cache max 24 ore, refresh on miss

### 5. Token validi ma 403 dal Resource Server

Gli scope nel token sono un sottoinsieme di quelli richiesti dall'API. Verifica `scope` claim del JWT, confronta con quelli documentati per l'endpoint.

### 6. Refresh token non emesso da Google

Google emette il refresh token solo al primo consenso e solo se richiesto esplicitamente con `access_type=offline&prompt=consent`. Se manca, revocare manualmente il consenso dall'account Google e ripetere il flow con i parametri corretti.

### 7. OAuth in n8n non rinnova il token

In alcune versioni n8n richiede di ri-salvare la credenziale dopo il primo login per attivare il refresh automatico. Verifica anche che `N8N_ENCRYPTION_KEY` non sia cambiato dall'ultima esecuzione (cambiarlo invalida tutte le credenziali esistenti).

### 8. `invalid_scope` su provider Microsoft

Gli scope Microsoft Graph richiedono prefisso completo (`https://graph.microsoft.com/User.Read`), non solo il nome. Eccezione: `openid`, `email`, `profile`, `offline_access` che sono OIDC standard e vanno senza prefisso.

### 9. Device Grant si blocca su `authorization_pending`

L'utente non ha completato il login. Controllare `expires_in` originale: se passato, il device code e scaduto e va riavviato il flow.

### 10. Rotation collision in workflow concorrenti

Due esecuzioni dello stesso workflow tentano di usare lo stesso refresh token contemporaneamente. La prima riesce, la seconda trova il vecchio token invalidato. Soluzione: lock distribuito (Redis, database lock) sull'operazione di refresh.

```python
import redis

r = redis.Redis()

def safe_refresh(credential_id: str) -> str:
    lock = r.lock(f"oauth:refresh:{credential_id}", timeout=30)
    if lock.acquire(blocking=True, blocking_timeout=10):
        try:
            return token_manager.get_valid_access_token(credential_id)
        finally:
            lock.release()
    else:
        raise RuntimeError("Could not acquire refresh lock")
```

### 11. Clock skew causa `exp` validation failure

Il server ha l'orologio sfasato rispetto all'AS. Il JWT appare scaduto anche se e stato emesso pochi secondi fa. Soluzione: configurare NTP (`chrony` o `systemd-timesyncd`). Tolleranza massima nel validatore: 30 secondi.

### 12. CORS error su SPA durante token exchange

Il browser blocca la richiesta POST al token endpoint per CORS. Soluzione: il token exchange deve avvenire lato server (backend-for-frontend pattern), non dal browser. La SPA invia il code al backend, il backend fa il token exchange.

### 13. Token troppo grande per header HTTP

Alcuni token JWT (specialmente con molti claim/group) superano i limiti di header dei web server (8KB default in Nginx). Soluzione: ridurre i claim nel token (non includere gruppi nel JWT), o usare opaque token + introspection.

### 14. JWKS endpoint non raggiungibile

L'AS e temporaneamente down e il RS non puo recuperare le chiavi per validare i JWT. Soluzione: cache locale delle chiavi JWKS con TTL lungo (24h) e refresh in background. Se la cache e popolata, il RS continua a funzionare anche con l'AS down.

### 15. `consent_required` inatteso su flow automatici

Alcuni AS richiedono consenso esplicito quando i scope cambiano o dopo un certo periodo. Per flow headless (Client Credentials, Device Grant), questo non dovrebbe accadere. Se accade su Authorization Code in un workflow, significa che serve intervento umano.

### 16. Token leak via Referer header

L'access token e stato messo come query parameter nell'URL. Il browser invia l'URL completo nel `Referer` header alle pagine successive. Soluzione: mai mettere token in URL. Usare sempre header `Authorization: Bearer <token>`.

### 17. Keycloak `invalid_redirect_uri` con port mismatch

Keycloak confronta la porta anche se e la porta default (80 per HTTP, 443 per HTTPS). Se il redirect_uri registrato e `https://app.example.com/callback` e la richiesta include `:443`, il match fallisce. Registrare entrambe le varianti o usare wildcard sulla porta (solo in dev).

### 18. Service account key file esposto in repository

Un file JSON di service account Google (`credentials.json`) e stato committato in git. Azione immediata: (1) revocare la chiave dalla console Google Cloud, (2) generare una nuova chiave, (3) usare `git filter-branch` o `bfg` per rimuovere il file dalla storia, (4) ruotare tutte le credenziali che il service account aveva accesso a.

---

## FAQ — 15 domande e risposte

### 1. OAuth 2.1 vs OAuth 2.0: cosa cambia?

OAuth 2.1 consolida le best practice emerse dal BCP `oauth-security-topics`:
- PKCE obbligatorio per tutti i client (non solo public)
- Implicit flow rimosso
- Resource Owner Password Credentials rimosso
- Refresh Token Rotation come default
- redirect_uri confronto esatto (no pattern matching)
- Bearer token in header, mai in query string

### 2. Quando usare opaque token vs JWT?

**Opaque**: quando serve revoca immediata, quando i claim cambiano frequentemente, quando il token e per un solo RS controllato. **JWT**: quando il RS deve validare senza chiamare l'AS, quando servono multi-RS, quando la latenza e critica.

### 3. Posso usare OAuth per autenticazione?

No, OAuth 2.0 e per autorizzazione. Per autenticazione, serve OIDC (che aggiunge l'ID token). Usare un access token come prova di identita e un errore di sicurezza (confused deputy attack).

### 4. Come gestisco la migrazione da API key a OAuth?

1. Implementa OAuth sul nuovo sistema in parallelo.
2. Crea un proxy che accetta entrambi (API key e Bearer token) durante la transizione.
3. Migra i client uno alla volta, monitorando i log.
4. Disabilita le API key dopo la migrazione completa.
5. Timeline tipica: 3-6 mesi per un ecosistema complesso.

### 5. Quanto dura un access token idealmente?

Dipende dal rischio: 5 minuti per banking/healthcare, 15-60 minuti per uso generico, 1 ora per server-to-server. Mai piu di 1 ora. Se serve piu, usa refresh token.

### 6. Devo usare PKCE anche per Client Credentials?

No, PKCE non si applica a Client Credentials perche non c'e authorization code da proteggere. E rilevante solo per Authorization Code flow.

### 7. Come testo OAuth in locale?

- Keycloak su Docker come AS locale: `docker run -p 8080:8080 quay.io/keycloak/keycloak:24.0.0 start-dev`
- `redirect_uri` su `http://localhost:3000/callback` (HTTP permesso solo su localhost)
- Tool: Postman OAuth2 helper, `oauth2-proxy` per test con browser

### 8. Cosa succede se perdo la `N8N_ENCRYPTION_KEY`?

Tutte le credenziali salvate in n8n sono irrecuperabili. Devi ri-autenticare ogni connessione OAuth. Backup della chiave separato e obbligatorio.

### 9. private_key_jwt vs mTLS per autenticazione client?

`private_key_jwt` e application-layer (piu facile da implementare, funziona ovunque). mTLS e transport-layer (piu forte, ma richiede gestione certificati PKI). Per la maggior parte dei casi, `private_key_jwt` e sufficiente. mTLS e preferito in open banking (PSD2) e ambienti regolamentati.

### 10. Come gestisco OAuth quando il provider e temporaneamente down?

Cache locale del JWKS (per validazione JWT). Retry con backoff esponenziale per refresh. Circuit breaker per evitare di sommergere il provider. Se il token e ancora valido, continuare a usarlo.

### 11. Posso condividere un refresh token tra piu istanze del servizio?

Si, ma con un lock distribuito sull'operazione di refresh per evitare rotation collision. Un solo nodo alla volta deve fare il refresh; gli altri usano il token aggiornato dal lock holder.

### 12. Come implemento il logout con OAuth/OIDC?

OIDC definisce RP-Initiated Logout (RFC proposal). Il client redirige a `end_session_endpoint` dell'AS con `id_token_hint` e `post_logout_redirect_uri`. Non tutti i provider lo supportano. Alternativa: revoca del refresh token + cancellazione sessione locale.

### 13. Devo validare il JWT su ogni richiesta?

Si. La validazione e veloce (verifica firma + check claim). La cache del JWKS riduce le chiamate di rete. Non validare = fidarsi ciecamente del token, che potrebbe essere scaduto, revocato, o forgiato.

### 14. Come gestisco scope che richiedono admin consent (Azure AD)?

L'admin globale della tenant Azure AD deve navigare a `https://login.microsoftonline.com/{tenant}/adminconsent?client_id={client_id}` e approvare. Dopo l'approvazione, tutti gli utenti della tenant possono usare quei scope senza consenso individuale.

### 15. Service account vs OAuth user token per workflow notturni?

Per workflow che girano senza utente presente: preferire service account (Client Credentials o Google Service Account) quando l'azione e "del sistema". Preferire OAuth user token con refresh quando l'azione e "per conto dell'utente" e servono i permessi specifici dell'utente.

---

## Esercizi

### Esercizio 1 — OAuth 2.1 auth code + PKCE (60 min)

Implementa un client Python che fa il flow completo verso Google OAuth:
1. Genera PKCE (code_verifier + code_challenge).
2. Apri il browser con l'authorization URL.
3. Ricevi il callback con un server HTTP locale.
4. Scambia il code per i token.
5. Salva il refresh token in un file cifrato.
6. Implementa il refresh automatico.

### Esercizio 2 — Client Credentials con Keycloak (45 min)

1. Deploy Keycloak con Docker.
2. Crea realm, client, scope.
3. Implementa Client Credentials flow in Python.
4. Verifica il JWT ricevuto (firma, iss, aud, exp, scope).

### Esercizio 3 — private_key_jwt (45 min)

1. Genera keypair RSA.
2. Registra la public key su Keycloak.
3. Implementa autenticazione private_key_jwt.
4. Verifica che non serve piu il client_secret.

### Esercizio 4 — Token lifecycle manager (60 min)

1. Implementa `TokenManager` con refresh anticipato e lock.
2. Simula 10 workflow concorrenti che usano lo stesso token.
3. Verifica che il refresh avvenga una sola volta (no rotation collision).
4. Simula un `invalid_grant` e verifica il fallback a re-auth.

### Esercizio 5 — Multi-tenant vault (90 min)

1. Crea schema PostgreSQL per credential vault multi-tenant.
2. Implementa encryption at rest con chiave per tenant.
3. Implementa Row Level Security.
4. Scrivi test che verifica l'isolation tra tenant.
5. Implementa audit log per ogni operazione sui token.

---

## Auto-valutazione

1. OAuth 2.1: cosa cambia da 2.0?
2. PKCE: a cosa serve e perche S256, non plain?
3. Refresh token rotation: come funziona la detection di compromissione?
4. `private_key_jwt` vs `client_secret_basic`: vantaggi e svantaggi.
5. Vault per token: quali feature di HashiCorp Vault sfruttare?
6. DPoP: come funziona il binding tra token e chiave?
7. Scope design: perche `read:invoices` e meglio di `invoices`?
8. Come gestire la concorrenza nel refresh con rotation?
9. JWT vs opaque token: quando usare quale?
10. Cosa succede se un token JWT viene rubato ma non e scaduto?
11. Come implementare token binding con mTLS?
12. Device Authorization Grant: quando preferirlo ad Authorization Code?
13. Come gestire un provider OAuth che non supporta PKCE?
14. Sliding vs absolute expiration per refresh token: trade-off?
15. Come monitorare la salute del sistema di token management?

---

## Riferimenti

**Specifiche IETF**:
- RFC 6749 — The OAuth 2.0 Authorization Framework.
- RFC 6750 — OAuth 2.0 Bearer Token Usage.
- RFC 7523 — JWT Profile for OAuth 2.0 Client Authentication (private_key_jwt).
- RFC 7636 — Proof Key for Code Exchange (PKCE).
- RFC 7662 — OAuth 2.0 Token Introspection.
- RFC 8628 — OAuth 2.0 Device Authorization Grant.
- RFC 8705 — OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens.
- RFC 9068 — JWT Profile for OAuth 2.0 Access Tokens.
- RFC 9449 — DPoP: Demonstrating Proof of Possession.
- RFC 9700 — OAuth 2.1.
- `draft-ietf-oauth-security-topics` — OAuth 2.0 Security Best Current Practice.

**OpenID Connect**:
- OpenID Connect Core 1.0.
- OpenID Connect Discovery 1.0.
- OpenID Connect RP-Initiated Logout 1.0.

**Documentazione provider**:
- Google Identity — OAuth 2.0 docs.
- Microsoft identity platform documentation.
- Auth0 — OAuth 2.0 and OIDC reference.
- Stripe — OAuth Connect.
- GitHub — Building GitHub Apps.
- Keycloak — Server Administration Guide.

**Librerie raccomandate**:
- Node.js: `jose`, `openid-client`.
- Python: `Authlib`, `PyJWT`, `python-jose`, `cryptography`.
- Go: `golang.org/x/oauth2`, `golang-jwt/jwt`.
- Java: `nimbus-jose-jwt`, Spring Security OAuth2.

**Tool diagnostici**:
- `jwt.io` — decoder JWT (mai incollare token di produzione).
- Postman — built-in OAuth 2.0 helper.
- Keycloak admin console — testbed per flow custom.
- `oauth2-proxy` — reverse proxy OAuth-aware per legacy app.

---

## Collegamenti incrociati

- Modulo 04 — `04-integrazione-api.md`: API auth basics.
- Modulo 12 — `12-python-automazione-avanzata.md`: implementare client OAuth.
- Modulo 24 — `24-audit-logging-compliance.md`: audit delle operazioni token.
- Modulo 25 — `25-multi-environment-promotion.md`: credenziali diverse per ambiente.

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **OAuth 2.0/2.1** | Standard authorization delegata (RFC 6749, RFC 9700). |
| **OIDC** | OpenID Connect; layer di autenticazione sopra OAuth 2.0. |
| **Auth code flow** | Flow standard per app con UI: utente da consenso, client riceve code, scambia per token. |
| **Client credentials** | Flow machine-to-machine senza utente. |
| **Device Authorization Grant** | Flow per dispositivi senza browser (RFC 8628). |
| **PKCE** | Proof Key for Code Exchange; protezione contro intercettazione del code (RFC 7636). |
| **Refresh token** | Credenziale long-lived per ri-emettere access token senza login. |
| **Refresh rotation** | Ogni refresh emette nuovo refresh, invalida vecchio. Rileva compromissione. |
| **`private_key_jwt`** | Autenticazione client via JWT firmato con chiave privata (RFC 7523). |
| **DPoP** | Demonstrating Proof-of-Possession; lega token a chiave del client (RFC 9449). |
| **mTLS** | Mutual TLS; autenticazione bidirezionale con certificati (RFC 8705). |
| **AS (Authorization Server)** | Server che emette token (Keycloak, Auth0, Google). |
| **RS (Resource Server)** | Server che valida token e serve le risorse (API). |
| **JWKS** | JSON Web Key Set; endpoint con le chiavi pubbliche dell'AS per verifica firma JWT. |
| **Opaque token** | Token senza informazioni leggibili; richiede introspection per validazione. |
| **JWT** | JSON Web Token; token self-contained con claim firmati. |
| **Scope** | Permesso specifico concesso al client (es. `read:invoices`). |
| **Consent** | Approvazione esplicita dell'utente agli scope richiesti dal client. |
| **Token binding** | Legame crittografico tra token e chiave/certificato del possessore (DPoP o mTLS). |
| **KMS** | Key Management Service; servizio per gestione chiavi di cifratura (AWS KMS, GCP Cloud KMS). |

---

## Letture e Riferimenti

- IETF — RFC 9700: The OAuth 2.1 Authorization Framework. https://datatracker.ietf.org/doc/rfc9700/
- IETF — RFC 7636: Proof Key for Code Exchange (PKCE). https://datatracker.ietf.org/doc/rfc7636/
- IETF — RFC 9449: OAuth 2.0 Demonstrating Proof of Possession (DPoP). https://datatracker.ietf.org/doc/rfc9449/
- IETF — RFC 7523: JWT Profile for OAuth 2.0 Client Authentication. https://datatracker.ietf.org/doc/rfc7523/
- OpenID Foundation — OpenID Connect Core 1.0. https://openid.net/specs/openid-connect-core-1_0.html
- HashiCorp — Vault secrets engine documentation. https://developer.hashicorp.com/vault/docs/secrets
- Auth0 — Refresh token rotation. https://auth0.com/docs/secure/tokens/refresh-tokens/refresh-token-rotation
- Richer, Justin; Sanso, Antonio. *OAuth 2 in Action*. Manning, 2017. — Implementazione pratica di OAuth 2.0.
- Madsen, Paul; Srinivas, Nat. *Solving Identity Management in Modern Applications*. Apress, 2022. — OIDC, federation, token management.
