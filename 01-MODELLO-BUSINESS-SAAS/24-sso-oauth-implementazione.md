# SSO e OAuth — Implementazione per SaaS — Guida Approfondita

## Indice
- [Panoramica](#panoramica)
- [Fondamenti dell'Identity Management](#fondamenti-dellidentity-management)
- [OAuth 2.0 — Protocollo di Autorizzazione](#oauth-20--protocollo-di-autorizzazione)
  - [I Quattro Ruoli di OAuth 2.0](#i-quattro-ruoli-di-oauth-20)
  - [Authorization Code Grant](#authorization-code-grant)
  - [Authorization Code + PKCE — Deep Dive](#authorization-code--pkce--deep-dive)
  - [Client Credentials Grant — Machine-to-Machine](#client-credentials-grant--machine-to-machine)
  - [Device Code Grant — Dispositivi a Input Limitato](#device-code-grant--dispositivi-a-input-limitato)
  - [Grant Types Deprecati](#grant-types-deprecati)
- [OpenID Connect (OIDC) — Autenticazione su OAuth 2.0](#openid-connect-oidc--autenticazione-su-oauth-20)
  - [Cosa Aggiunge OIDC a OAuth 2.0](#cosa-aggiunge-oidc-a-oauth-20)
  - [Discovery e Well-Known Configuration](#discovery-e-well-known-configuration)
  - [Struttura dell'ID Token](#struttura-dellid-token)
- [JWT — Anatomia e Validazione](#jwt--anatomia-e-validazione)
  - [Struttura del JWT](#struttura-del-jwt)
  - [Validazione Completa di un JWT](#validazione-completa-di-un-jwt)
  - [JWKS e Rotazione delle Chiavi](#jwks-e-rotazione-delle-chiavi)
- [Authorization Code Flow con PKCE — Implementazione](#authorization-code-flow-con-pkce--implementazione)
- [Token Management — Access Token e Refresh Token](#token-management--access-token-e-refresh-token)
  - [Ciclo di Vita dei Token](#ciclo-di-vita-dei-token)
  - [Token Refresh Flow](#token-refresh-flow)
  - [Sicurezza dei Token](#sicurezza-dei-token)
  - [Token Revocation](#token-revocation)
- [Session Management](#session-management)
- [SAML 2.0 — Enterprise SSO](#saml-20--enterprise-sso)
  - [Perché SAML nel 2024+](#perché-saml-nel-2024)
  - [SAML 2.0 SP-Initiated Flow](#saml-20-sp-initiated-flow)
  - [SAML 2.0 IdP-Initiated Flow](#saml-20-idp-initiated-flow)
  - [Scambio Metadata e Configurazione](#scambio-metadata-e-configurazione)
  - [Implementazione SAML con python3-saml](#implementazione-saml-con-python3-saml)
  - [Configurazione Multi-Tenant SAML](#configurazione-multi-tenant-saml)
- [SSO Architecture Patterns](#sso-architecture-patterns)
- [Integrazione con Identity Provider Enterprise](#integrazione-con-identity-provider-enterprise)
  - [Confronto Identity Provider](#confronto-identity-provider)
  - [Okta Integration](#okta-integration)
  - [Azure AD (Entra ID) Integration](#azure-ad-entra-id-integration)
  - [Google Workspace Integration](#google-workspace-integration)
  - [KeyCloak — Self-Hosted IdP](#keycloak--self-hosted-idp)
  - [Auth0 Integration](#auth0-integration)
- [Social Login](#social-login)
- [SCIM — Provisioning Automatico degli Utenti](#scim--provisioning-automatico-degli-utenti)
  - [Cos'è SCIM](#cosè-scim)
  - [SCIM API Endpoints](#scim-api-endpoints)
  - [Implementazione SCIM](#implementazione-scim)
  - [Group Sync e Deprovisioning](#group-sync-e-deprovisioning)
  - [Riconciliazione SCIM](#riconciliazione-scim)
- [Implementazione Pratica Completa](#implementazione-pratica-completa)
- [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa)
  - [TOTP (Time-Based One-Time Password)](#totp-time-based-one-time-password)
  - [SMS e Email OTP](#sms-e-email-otp)
  - [Backup Codes](#backup-codes)
  - [Policy di Enforcement MFA](#policy-di-enforcement-mfa)
- [WebAuthn e Passkeys](#webauthn-e-passkeys)
- [Enterprise SSO — Implicazioni Commerciali](#enterprise-sso--implicazioni-commerciali)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Riferimenti](#riferimenti)

---

## Panoramica

L'autenticazione e l'autorizzazione sono tra le componenti più critiche di qualsiasi prodotto SaaS. Un sistema di identity management mal progettato espone l'applicazione a vulnerabilità di sicurezza, crea frizione nell'esperienza utente, e limita la capacità di servire clienti enterprise che richiedono integrazione con i propri Identity Provider (IdP) aziendali. Al contrario, un sistema robusto di Single Sign-On (SSO), OAuth 2.0 e SCIM è spesso il prerequisito tecnico per vendere a clienti enterprise e rappresenta un differenziatore competitivo significativo.

Questa guida copre l'intero spettro dell'identity management per SaaS: dai fondamenti di OAuth 2.0 e OpenID Connect (OIDC), passando per l'implementazione dell'Authorization Code Flow con PKCE, fino alla configurazione di SAML 2.0 per enterprise SSO, l'integrazione con Identity Provider come Okta e Azure AD, e il provisioning automatico degli utenti tramite SCIM. Per ogni protocollo e pattern, forniamo spiegazioni tecniche dettagliate, diagrammi dei flussi, codice di implementazione e considerazioni di sicurezza.

È importante distinguere subito tra autenticazione (AuthN — verificare chi sei) e autorizzazione (AuthZ — determinare cosa puoi fare). OAuth 2.0 è primariamente un protocollo di autorizzazione. OpenID Connect estende OAuth 2.0 aggiungendo l'autenticazione. SAML 2.0 combina entrambi in un singolo protocollo. Questa distinzione è fondamentale per comprendere quando e come utilizzare ciascun protocollo.

---

## Fondamenti dell'Identity Management

### Terminologia Essenziale

**Identity Provider (IdP)**: il servizio che autentica l'utente e gestisce le identità. Esempi: Okta, Azure AD, Google Workspace, Auth0. L'IdP mantiene le credenziali dell'utente e emette asserzioni o token che confermano l'identità.

**Service Provider (SP)** / **Relying Party (RP)**: l'applicazione che si affida all'IdP per l'autenticazione. Nel contesto SaaS, il proprio prodotto è il Service Provider che delega l'autenticazione all'IdP del cliente.

**Single Sign-On (SSO)**: la capacità di un utente di autenticarsi una sola volta presso l'IdP e accedere a molteplici Service Provider senza dover reinserire le credenziali. L'utente si autentica su Okta una volta e può accedere a Slack, Salesforce, e al proprio prodotto SaaS senza login aggiuntivi.

**Federation**: la capacità di stabilire relazioni di fiducia tra IdP e SP di organizzazioni diverse. La federazione permette a un utente dell'azienda A di autenticarsi presso il prodotto SaaS B utilizzando le credenziali aziendali di A.

**Claim/Attribute**: informazione sull'utente inclusa nel token o nell'asserzione. Esempi: email, nome, ruolo, gruppi, tenant_id.

**Consent**: il processo attraverso cui l'utente autorizza esplicitamente un'applicazione ad accedere a determinati dati o risorse per suo conto. Il consent screen mostra i permessi richiesti (scope) e l'utente può accettare o rifiutare.

**Scope**: un meccanismo di OAuth 2.0 per limitare l'accesso dell'applicazione. Esempi: `openid`, `profile`, `email`, `read:documents`. Lo scope definisce il perimetro dei permessi richiesti dal client.

### Protocolli a Confronto

| Caratteristica | OAuth 2.0 | OIDC | SAML 2.0 |
|---|---|---|---|
| Tipo | Autorizzazione | Autenticazione + Autorizzazione | Autenticazione + Autorizzazione |
| Formato token | JSON (JWT) | JSON (JWT) | XML |
| Trasporto | HTTP/REST | HTTP/REST | HTTP/POST, HTTP/Redirect |
| Complessità | Media | Media | Alta |
| Use case primario | API authorization | Social login, modern SSO | Enterprise SSO |
| Adozione | Universale | Universale (consumer + B2B) | Enterprise legacy |
| Mobile-friendly | Sì | Sì | Limitato |
| Dimensione tipica payload | ~1 KB | ~2 KB | ~5-15 KB |
| Standard claims | No (custom) | Sì (standardizzati) | Sì (attributi XML) |
| Discovery automatica | No | Sì (.well-known) | Sì (metadata XML) |
| Logout federato | No (richiede ext.) | Sì (RP-Initiated Logout) | Sì (SLO) |

### Quando Usare Quale Protocollo

**OIDC** è la scelta predefinita per nuove implementazioni: social login, SSO moderno, mobile/SPA. Se il cliente non ha requisiti specifici, OIDC è il protocollo da proporre.

**SAML 2.0** è obbligatorio quando il cliente enterprise lo richiede — e la maggior parte lo richiederà. L'admin IT non vuole configurare un nuovo protocollo quando ha già SAML funzionante con 200 applicazioni.

**OAuth 2.0 puro** (senza OIDC) è appropriato per autorizzazione API machine-to-machine, accesso a risorse di terze parti, e scenari dove l'identità dell'utente non è rilevante.

---

## OAuth 2.0 — Protocollo di Autorizzazione

### I Quattro Ruoli di OAuth 2.0

1. **Resource Owner**: l'utente che possiede i dati (es. l'utente che ha un account Google)
2. **Client**: l'applicazione che vuole accedere ai dati dell'utente (il nostro SaaS)
3. **Authorization Server**: il server che autentica l'utente e emette i token (Google, Okta)
4. **Resource Server**: il server che ospita i dati protetti (Google API, la nostra API)

### Authorization Code Grant

Il grant type più sicuro e raccomandato. L'utente viene reindirizzato all'Authorization Server, si autentica, e viene reindirizzato al client con un codice di autorizzazione monouso. Il client scambia il codice per un access token tramite una chiamata server-to-server.

Il codice di autorizzazione è un valore opaco, monouso, di breve durata (tipicamente 30-60 secondi). Questo meccanismo a due fasi è cruciale: il token non transita mai attraverso il browser dell'utente, ma viene scambiato server-to-server.

```
1. Client -> Authorization Server: redirect con client_id, redirect_uri, scope, state
2. Utente si autentica e acconsente
3. Authorization Server -> Client: redirect a redirect_uri con ?code=xxx&state=yyy
4. Client -> Authorization Server: POST token endpoint con code, client_id, client_secret
5. Authorization Server -> Client: access_token, refresh_token, id_token (se OIDC)
```

### Authorization Code + PKCE — Deep Dive

PKCE (Proof Key for Code Exchange, RFC 7636, pronunciato "pixy") aggiunge una protezione crittografica contro l'intercettazione del codice di autorizzazione. Originariamente progettato per client pubblici (mobile, SPA), la best practice attuale (RFC 9126, OAuth 2.1 draft) lo raccomanda per tutti i client.

**Come funziona PKCE**:

1. Il client genera un `code_verifier`: una stringa crittograficamente casuale di 43-128 caratteri (A-Z, a-z, 0-9, `-._~`)
2. Il client calcola il `code_challenge`: `BASE64URL(SHA256(code_verifier))`
3. Il client include `code_challenge` e `code_challenge_method=S256` nella richiesta di autorizzazione
4. L'Authorization Server memorizza il `code_challenge` associato al codice emesso
5. Al momento dello scambio, il client invia il `code_verifier` originale
6. L'Authorization Server verifica: `BASE64URL(SHA256(code_verifier_ricevuto)) == code_challenge_memorizzato`

**Perché è necessario**: senza PKCE, un attaccante che intercetta il codice di autorizzazione (tramite malware, log, deep link hijacking su mobile) può scambiarlo per un token. Con PKCE, l'attaccante avrebbe bisogno anche del `code_verifier`, che non transita mai nel redirect e rimane nel client originale.

```
Senza PKCE:
  Attaccante intercetta ?code=abc -> Scambia code per token -> Accesso!

Con PKCE:
  Attaccante intercetta ?code=abc -> Non ha il code_verifier -> Scambio fallisce
```

### Client Credentials Grant — Machine-to-Machine

Il Client Credentials Grant è progettato per comunicazione machine-to-machine (M2M) dove non c'è un utente umano coinvolto. Il client si autentica direttamente con le proprie credenziali.

**Casi d'uso tipici nel SaaS**:
- Microservizi che comunicano tra loro
- Cron job che accedono alle API
- Backend di partner che integrano con le API del SaaS
- Pipeline CI/CD che interagiscono con servizi protetti
- Sincronizzazione dati tra sistemi

**Flusso**:

```
┌──────────┐                       ┌─────────────────┐
│  Client  │                       │  Authorization   │
│  (M2M)   │                       │    Server        │
└────┬─────┘                       └───────┬──────────┘
     │                                     │
     │  1. POST /token                     │
     │     grant_type=client_credentials   │
     │     client_id=xxx                   │
     │     client_secret=yyy               │
     │     scope=api:read api:write        │
     │────────────────────────────────────>│
     │                                     │
     │  2. Validare client credentials     │
     │                                     │
     │  3. access_token (NO refresh token) │
     │<────────────────────────────────────│
     │                                     │
     │  4. Usare access_token per API      │
     │────────────────────────────────────>│ Resource Server
```

**Implementazione**:

```python
class M2MAuthClient:
    """Client per autenticazione machine-to-machine"""

    def __init__(self, token_endpoint: str, client_id: str, client_secret: str):
        self.token_endpoint = token_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self._token_cache = None
        self._token_expiry = None

    def get_access_token(self, scopes: list[str]) -> str:
        """Ottenere un access token, usando la cache se valido"""
        if self._token_cache and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._token_cache

        response = requests.post(
            self.token_endpoint,
            data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': ' '.join(scopes),
            },
            timeout=10,
        )

        if response.status_code != 200:
            raise M2MAuthError(f"Token request failed: {response.status_code}")

        tokens = response.json()
        self._token_cache = tokens['access_token']
        # Rinnovare 60 secondi prima della scadenza effettiva
        self._token_expiry = datetime.utcnow() + timedelta(
            seconds=tokens['expires_in'] - 60
        )
        return self._token_cache
```

**Sicurezza del Client Credentials Grant**:
- Il `client_secret` va trattato come una password: mai in codice sorgente, solo in variabili d'ambiente o secret manager
- Usare scope minimi (principio del least privilege)
- Il refresh token **non viene emesso** — il client può sempre ottenere un nuovo access token con le proprie credenziali
- Ruotare periodicamente il `client_secret` (ogni 90 giorni come minimo)
- Monitorare l'uso anomalo: pattern di accesso inusuali, volume eccessivo di richieste, accesso da IP inaspettati

### Device Code Grant — Dispositivi a Input Limitato

Il Device Code Grant (RFC 8628) è progettato per dispositivi con limitazioni di input: smart TV, CLI tools, dispositivi IoT, console di gaming. L'utente completa l'autenticazione su un dispositivo diverso (smartphone, computer).

**Flusso completo**:

```
┌──────────┐                ┌─────────────────┐           ┌──────────┐
│ Device   │                │  Authorization   │           │  User's  │
│ (es. TV) │                │    Server        │           │  Browser │
└────┬─────┘                └───────┬──────────┘           └────┬─────┘
     │                              │                           │
     │ 1. POST /device/code         │                           │
     │    client_id=xxx             │                           │
     │    scope=openid profile      │                           │
     │─────────────────────────────>│                           │
     │                              │                           │
     │ 2. device_code, user_code,   │                           │
     │    verification_uri,         │                           │
     │    interval, expires_in      │                           │
     │<─────────────────────────────│                           │
     │                              │                           │
     │ 3. Mostrare:                 │                           │
     │    "Vai a https://login.     │                           │
     │     example.com/device       │                           │
     │     e inserisci: ABCD-1234"  │                           │
     │                              │                           │
     │                              │    4. Utente visita URL   │
     │                              │<──────────────────────────│
     │                              │                           │
     │                              │    5. Inserisce user_code │
     │                              │<──────────────────────────│
     │                              │                           │
     │                              │    6. Login + consent     │
     │                              │<─────────────────────────>│
     │                              │                           │
     │ 7. Polling: POST /token      │                           │
     │    grant_type=                │                           │
     │    urn:ietf:params:oauth:     │                           │
     │    grant-type:device_code     │                           │
     │    device_code=xxx           │                           │
     │─────────────────────────────>│                           │
     │                              │                           │
     │ 8a. "authorization_pending"  │  (utente non ha ancora    │
     │<─────────────────────────────│   completato il login)    │
     │                              │                           │
     │ ... attende interval sec ... │                           │
     │                              │                           │
     │ 9. Polling: POST /token      │                           │
     │─────────────────────────────>│                           │
     │                              │                           │
     │ 10. access_token,            │  (utente ha completato)   │
     │     refresh_token            │                           │
     │<─────────────────────────────│                           │
```

**Implementazione del polling lato device**:

```python
class DeviceCodeFlow:
    def initiate(self, client_id: str, scopes: list[str]) -> dict:
        """Iniziare il Device Code Flow"""
        response = requests.post(
            f"{self.auth_server}/device/code",
            data={
                'client_id': client_id,
                'scope': ' '.join(scopes),
            }
        )
        return response.json()
        # Ritorna: device_code, user_code, verification_uri,
        #          verification_uri_complete, interval, expires_in

    def poll_for_token(self, client_id: str, device_code: str, interval: int) -> dict:
        """Polling fino a che l'utente non completa l'autenticazione"""
        deadline = time.time() + 600  # timeout massimo 10 minuti

        while time.time() < deadline:
            time.sleep(interval)

            response = requests.post(
                f"{self.auth_server}/token",
                data={
                    'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                    'client_id': client_id,
                    'device_code': device_code,
                }
            )

            data = response.json()

            if response.status_code == 200:
                return data  # Successo: access_token + refresh_token

            error = data.get('error')
            if error == 'authorization_pending':
                continue  # Utente non ha ancora completato
            elif error == 'slow_down':
                interval += 5  # Authorization server chiede di rallentare
            elif error == 'expired_token':
                raise DeviceCodeExpiredError("Device code scaduto, ricominciare il flusso")
            elif error == 'access_denied':
                raise AccessDeniedError("L'utente ha rifiutato l'autorizzazione")
            else:
                raise DeviceCodeError(f"Errore inaspettato: {error}")

        raise DeviceCodeTimeoutError("Timeout polling")
```

**Casi d'uso SaaS concreti**: CLI per sviluppatori (es. `gh auth login` di GitHub CLI), app per Apple TV o smart display, kiosk senza tastiera, tool da terminale per DevOps.

### Grant Types Deprecati

**Implicit Grant** (DEPRECATO in OAuth 2.1): il token viene restituito direttamente nel fragment dell'URL di redirect (`#access_token=xxx`). Non sicuro perché il token è esposto nella cronologia del browser, nei log dei server, e può essere intercettato. Sostituito da Authorization Code + PKCE.

**Resource Owner Password Credentials (ROPC)** (DEPRECATO in OAuth 2.1): l'utente fornisce username e password direttamente al client, che li inoltra all'Authorization Server. Viola il principio fondamentale di OAuth (le credenziali non dovrebbero mai essere condivise con il client). Utilizzabile solo in scenari di migrazione legacy con estrema cautela.

---

## OpenID Connect (OIDC) — Autenticazione su OAuth 2.0

### Cosa Aggiunge OIDC a OAuth 2.0

OIDC è un layer di identità costruito sopra OAuth 2.0. Aggiunge:

1. **ID Token**: un JWT che contiene informazioni sull'utente (claims). A differenza dell'access token (che è per l'autorizzazione), l'ID token è per l'autenticazione — conferma chi è l'utente.

2. **UserInfo Endpoint**: un endpoint API standard dove il client può recuperare informazioni aggiuntive sull'utente.

3. **Standard Claims**: un set standardizzato di attributi utente (sub, name, email, picture, etc.) con nomi e formati definiti dalla specifica.

4. **Discovery**: un meccanismo standard (`.well-known/openid-configuration`) che permette al client di scoprire automaticamente gli endpoint dell'IdP.

5. **Session Management**: meccanismi opzionali per gestire il logout e la verifica dello stato della sessione.

6. **Dynamic Client Registration**: possibilità per i client di registrarsi automaticamente presso l'IdP senza intervento manuale dell'admin.

### Discovery e Well-Known Configuration

L'endpoint `.well-known/openid-configuration` è il punto di partenza per qualsiasi integrazione OIDC. Permette al client di scoprire automaticamente tutti gli endpoint e le capability dell'IdP senza configurazione manuale.

**Richiesta**: `GET https://idp.example.com/.well-known/openid-configuration`

**Risposta tipica**:

```json
{
  "issuer": "https://idp.example.com",
  "authorization_endpoint": "https://idp.example.com/oauth2/authorize",
  "token_endpoint": "https://idp.example.com/oauth2/token",
  "userinfo_endpoint": "https://idp.example.com/oauth2/userinfo",
  "jwks_uri": "https://idp.example.com/oauth2/jwks",
  "registration_endpoint": "https://idp.example.com/oauth2/register",
  "end_session_endpoint": "https://idp.example.com/oauth2/logout",
  "revocation_endpoint": "https://idp.example.com/oauth2/revoke",
  "introspection_endpoint": "https://idp.example.com/oauth2/introspect",
  "scopes_supported": ["openid", "profile", "email", "address", "phone", "offline_access"],
  "response_types_supported": ["code", "id_token", "token id_token"],
  "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
  "subject_types_supported": ["public", "pairwise"],
  "id_token_signing_alg_values_supported": ["RS256", "ES256"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "private_key_jwt"],
  "claims_supported": ["sub", "iss", "aud", "exp", "iat", "name", "email", "email_verified", "picture", "locale"],
  "code_challenge_methods_supported": ["S256"]
}
```

**Campi chiave da consumare nel codice**:
- `issuer`: usato per validare il claim `iss` dell'ID token — deve corrispondere esattamente
- `jwks_uri`: URL per scaricare le chiavi pubbliche di firma — necessario per validare i JWT
- `authorization_endpoint`: dove reindirizzare l'utente per il login
- `token_endpoint`: dove scambiare il codice per i token
- `end_session_endpoint`: dove reindirizzare per il logout federato

**Best practice**: cacheare la risposta (tipicamente stabile per ore/giorni) ma implementare un refresh periodico (ogni ora) per catturare cambiamenti come la rotazione delle chiavi.

### Struttura dell'ID Token

```json
{
  "iss": "https://accounts.google.com",
  "sub": "110169484474386276334",
  "aud": "your-client-id.apps.googleusercontent.com",
  "exp": 1714234800,
  "iat": 1714231200,
  "nonce": "abc123",
  "email": "user@example.com",
  "email_verified": true,
  "name": "Mario Rossi",
  "picture": "https://lh3.googleusercontent.com/photo.jpg",
  "given_name": "Mario",
  "family_name": "Rossi",
  "locale": "it"
}
```

I claim fondamentali:
- **iss** (issuer): chi ha emesso il token
- **sub** (subject): identificatore univoco dell'utente presso l'IdP
- **aud** (audience): il client a cui il token è destinato
- **exp** (expiration): timestamp di scadenza
- **iat** (issued at): timestamp di emissione
- **nonce**: valore monouso per prevenire replay attack — deve corrispondere a quello inviato nella richiesta di autorizzazione
- **auth_time**: timestamp dell'ultima autenticazione attiva dell'utente
- **acr** (Authentication Context Class Reference): livello di autenticazione (es. MFA)
- **amr** (Authentication Methods Reference): metodi usati (es. `["pwd", "otp"]`)
- **azp** (Authorized Party): il client che ha richiesto il token (quando diverso da `aud`)

---

## JWT — Anatomia e Validazione

### Struttura del JWT

Un JSON Web Token (RFC 7519) è composto da tre parti separate da punti: `header.payload.signature`.

**Header** (JOSE Header):
```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "key-id-2024-03"
}
```
- `alg`: algoritmo di firma. RS256 (RSA + SHA-256) è il più comune. ES256 (ECDSA) è più efficiente. **MAI accettare `alg: "none"` — è un attacco noto (CVE-2015-9235).**
- `typ`: tipo del token (JWT)
- `kid`: identificatore della chiave usata per firmare — necessario per trovare la chiave corretta nel JWKS

**Payload** (Claims Set):
```json
{
  "iss": "https://auth.example.com",
  "sub": "user-uuid-12345",
  "aud": "my-saas-app",
  "exp": 1714234800,
  "iat": 1714231200,
  "nbf": 1714231200,
  "jti": "unique-token-id-abc",
  "scope": "openid profile email",
  "tenant_id": "acme-corp",
  "roles": ["admin", "editor"]
}
```

Claim registrati (RFC 7519):
- `nbf` (not before): il token non è valido prima di questo timestamp
- `jti` (JWT ID): identificatore univoco del token — utile per revocation e prevenzione replay

**Signature**:
```
RSASHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  private_key
)
```

La firma garantisce integrità (il payload non è stato modificato) e autenticità (solo chi possiede la chiave privata può firmare).

### Validazione Completa di un JWT

La validazione di un JWT non è semplicemente "decodificare il base64". Ogni passo è critico per la sicurezza:

```python
def validate_jwt(token_str: str, expected_audience: str, jwks_client) -> dict:
    """Validazione completa di un JWT secondo RFC 7519 e OIDC Core"""

    # 1. Decodificare l'header SENZA validare la firma
    header = jwt.get_unverified_header(token_str)

    # 2. Verificare l'algoritmo — BLOCCARE 'none' e algoritmi simmetrici inaspettati
    allowed_algorithms = ['RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512']
    if header.get('alg') not in allowed_algorithms:
        raise JWTValidationError(f"Algoritmo non permesso: {header.get('alg')}")

    # 3. Recuperare la chiave pubblica dal JWKS usando il kid
    kid = header.get('kid')
    if not kid:
        raise JWTValidationError("Header JWT mancante del kid")

    signing_key = jwks_client.get_signing_key(kid)
    if not signing_key:
        # Provare a refreshare il JWKS — la chiave potrebbe essere stata ruotata
        jwks_client.refresh()
        signing_key = jwks_client.get_signing_key(kid)
        if not signing_key:
            raise JWTValidationError(f"Chiave non trovata per kid: {kid}")

    # 4. Validare firma, scadenza, audience, issuer in un'unica operazione
    try:
        payload = jwt.decode(
            token_str,
            key=signing_key.key,
            algorithms=[header['alg']],
            audience=expected_audience,
            issuer=expected_issuer,
            options={
                'verify_exp': True,
                'verify_nbf': True,
                'verify_iat': True,
                'verify_aud': True,
                'verify_iss': True,
                'require': ['exp', 'iat', 'iss', 'sub', 'aud'],
            },
            leeway=30,  # tolleranza clock skew di 30 secondi
        )
    except jwt.ExpiredSignatureError:
        raise JWTValidationError("Token scaduto")
    except jwt.InvalidAudienceError:
        raise JWTValidationError("Audience non valido")
    except jwt.InvalidIssuerError:
        raise JWTValidationError("Issuer non valido")
    except jwt.InvalidSignatureError:
        raise JWTValidationError("Firma non valida")

    # 5. Validazioni business-specific
    if not payload.get('sub'):
        raise JWTValidationError("Claim 'sub' mancante")

    return payload
```

**Checklist di validazione JWT (tutti obbligatori)**:

| Controllo | Perché |
|---|---|
| Algoritmo in whitelist | Previene attacco `alg: none` e confusion attack |
| Firma crittografica | Garantisce autenticità e integrità |
| `exp` non scaduto | Token non più valido |
| `nbf` superato | Token non ancora valido |
| `iss` corrisponde | Previene token da IdP non fidati |
| `aud` corrisponde | Previene token destinati ad altre applicazioni |
| `kid` trovato nel JWKS | Chiave di firma corretta |

### JWKS e Rotazione delle Chiavi

Il JWKS (JSON Web Key Set) è l'endpoint che espone le chiavi pubbliche dell'Authorization Server. La rotazione delle chiavi è un'operazione di manutenzione critica.

**Struttura JWKS**:
```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "key-2024-Q3",
      "use": "sig",
      "alg": "RS256",
      "n": "0vx7agoebGcQSuu...",
      "e": "AQAB"
    },
    {
      "kty": "RSA",
      "kid": "key-2024-Q2",
      "use": "sig",
      "alg": "RS256",
      "n": "xNQmF9tGvj3...",
      "e": "AQAB"
    }
  ]
}
```

**Strategia di caching JWKS nel client**:

```python
class JWKSClient:
    """Client JWKS con caching e refresh automatico"""

    def __init__(self, jwks_uri: str, cache_ttl: int = 3600):
        self.jwks_uri = jwks_uri
        self.cache_ttl = cache_ttl
        self._keys = {}
        self._last_refresh = 0

    def get_signing_key(self, kid: str):
        """Ottenere la chiave per un kid specifico"""
        if kid in self._keys:
            return self._keys[kid]

        # Cache miss — provare a refreshare
        if time.time() - self._last_refresh > 60:  # Non refreshare più di 1 volta/minuto
            self.refresh()

        return self._keys.get(kid)

    def refresh(self):
        """Scaricare il JWKS dall'endpoint"""
        response = requests.get(self.jwks_uri, timeout=10)
        if response.status_code != 200:
            raise JWKSFetchError(f"JWKS fetch failed: {response.status_code}")

        jwks = response.json()
        self._keys = {}
        for key_data in jwks.get('keys', []):
            if key_data.get('use') == 'sig':
                kid = key_data.get('kid')
                self._keys[kid] = RSAAlgorithm.from_jwk(key_data)

        self._last_refresh = time.time()
```

**Rotazione delle chiavi — best practice**:
1. L'IdP aggiunge la nuova chiave al JWKS **prima** di iniziare a usarla per firmare (overlap period)
2. I token già emessi con la vecchia chiave continuano a essere validabili
3. Dopo un periodo sufficiente (almeno la durata massima dei token), la vecchia chiave viene rimossa dal JWKS
4. Il client deve gestire il cache miss del `kid` come trigger per refreshare il JWKS

---

## Authorization Code Flow con PKCE — Implementazione

### Il Flusso Completo

```
┌──────┐                ┌──────────┐              ┌─────────────────┐
│      │                │          │              │  Authorization   │
│ User │                │  Client  │              │    Server        │
│      │                │  (SaaS)  │              │  (IdP: Okta)     │
└──┬───┘                └────┬─────┘              └───────┬──────────┘
   │                         │                            │
   │  1. Click "Login"       │                            │
   │────────────────────────>│                            │
   │                         │                            │
   │                         │  2. Generate code_verifier │
   │                         │     + code_challenge       │
   │                         │     (SHA256 hash)          │
   │                         │                            │
   │  3. Redirect to IdP     │                            │
   │<────────────────────────│                            │
   │                         │                            │
   │  4. Login at IdP        │                            │
   │─────────────────────────────────────────────────────>│
   │                         │                            │
   │  5. Redirect back       │                            │
   │  with auth code         │                            │
   │<─────────────────────────────────────────────────────│
   │                         │                            │
   │  6. Pass auth code      │                            │
   │────────────────────────>│                            │
   │                         │                            │
   │                         │  7. Exchange code + verifier│
   │                         │     for tokens              │
   │                         │────────────────────────────>│
   │                         │                            │
   │                         │  8. Access Token +         │
   │                         │     ID Token +             │
   │                         │     Refresh Token          │
   │                         │<────────────────────────────│
   │                         │                            │
   │  9. Authenticated!      │                            │
   │<────────────────────────│                            │
```

### Implementazione in Python

```python
import hashlib
import base64
import secrets
import requests
from flask import Flask, redirect, request, session, jsonify
import jwt

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Configurazione OIDC
OIDC_CONFIG = {
    'client_id': os.environ.get('OIDC_CLIENT_ID'),
    'client_secret': os.environ.get('OIDC_CLIENT_SECRET'),
    'authorization_endpoint': 'https://your-idp.com/oauth2/authorize',
    'token_endpoint': 'https://your-idp.com/oauth2/token',
    'userinfo_endpoint': 'https://your-idp.com/oauth2/userinfo',
    'jwks_uri': 'https://your-idp.com/oauth2/jwks',
    'redirect_uri': 'https://your-app.com/auth/callback',
    'scopes': 'openid profile email',
}


def generate_pkce_pair():
    """Genera code_verifier e code_challenge per PKCE"""
    # code_verifier: stringa random di 43-128 caratteri
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).rstrip(b'=').decode('utf-8')

    # code_challenge: SHA256 hash del code_verifier, base64url encoded
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).rstrip(b'=').decode('utf-8')

    return code_verifier, code_challenge


@app.route('/auth/login')
def login():
    """Step 1-3: Iniziare il flusso di autenticazione"""

    # Generare PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()

    # Generare state per CSRF protection
    state = secrets.token_urlsafe(32)

    # Generare nonce per replay protection
    nonce = secrets.token_urlsafe(32)

    # Salvare in sessione per la verifica nel callback
    session['code_verifier'] = code_verifier
    session['state'] = state
    session['nonce'] = nonce

    # Costruire l'URL di autorizzazione
    auth_url = (
        f"{OIDC_CONFIG['authorization_endpoint']}?"
        f"client_id={OIDC_CONFIG['client_id']}&"
        f"response_type=code&"
        f"scope={OIDC_CONFIG['scopes']}&"
        f"redirect_uri={OIDC_CONFIG['redirect_uri']}&"
        f"state={state}&"
        f"nonce={nonce}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256"
    )

    return redirect(auth_url)


@app.route('/auth/callback')
def callback():
    """Step 6-9: Gestire il callback con il codice di autorizzazione"""

    # Verificare lo state per CSRF protection
    if request.args.get('state') != session.get('state'):
        return 'Invalid state parameter', 403

    # Verificare che non ci siano errori
    error = request.args.get('error')
    if error:
        return f'Authentication error: {error}', 400

    auth_code = request.args.get('code')

    # Scambiare il codice per i token (server-to-server)
    token_response = requests.post(
        OIDC_CONFIG['token_endpoint'],
        data={
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': OIDC_CONFIG['redirect_uri'],
            'client_id': OIDC_CONFIG['client_id'],
            'client_secret': OIDC_CONFIG['client_secret'],
            'code_verifier': session.get('code_verifier'),
        }
    )

    if token_response.status_code != 200:
        return 'Token exchange failed', 400

    tokens = token_response.json()
    access_token = tokens['access_token']
    id_token = tokens['id_token']
    refresh_token = tokens.get('refresh_token')

    # Validare l'ID token
    user_info = validate_id_token(id_token)

    if not user_info:
        return 'Invalid ID token', 400

    # Verificare il nonce
    if user_info.get('nonce') != session.get('nonce'):
        return 'Invalid nonce', 403

    # Trovare o creare l'utente locale
    user = find_or_create_user(user_info)

    # Creare la sessione applicativa
    session['user_id'] = user.id
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token

    # Pulire i dati temporanei dalla sessione
    session.pop('code_verifier', None)
    session.pop('state', None)
    session.pop('nonce', None)

    return redirect('/dashboard')


def validate_id_token(id_token_str):
    """Validare e decodificare l'ID token JWT"""
    try:
        # Recuperare le chiavi pubbliche dell'IdP
        jwks_response = requests.get(OIDC_CONFIG['jwks_uri'])
        jwks = jwks_response.json()

        # Decodificare l'header per trovare il kid
        header = jwt.get_unverified_header(id_token_str)
        kid = header.get('kid')

        # Trovare la chiave corrispondente
        key = None
        for jwk in jwks['keys']:
            if jwk['kid'] == kid:
                key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                break

        if not key:
            return None

        # Validare e decodificare il token
        payload = jwt.decode(
            id_token_str,
            key=key,
            algorithms=['RS256'],
            audience=OIDC_CONFIG['client_id'],
            issuer=OIDC_CONFIG['authorization_endpoint'].rsplit('/', 2)[0],
        )

        return payload

    except jwt.exceptions.InvalidTokenError as e:
        logger.error(f"ID token validation failed: {e}")
        return None


def find_or_create_user(user_info):
    """Trovare l'utente locale o crearne uno nuovo"""
    # Cercare per IdP subject identifier
    user = User.query.filter_by(
        idp_subject=user_info['sub'],
        idp_issuer=user_info['iss']
    ).first()

    if user:
        # Aggiornare le informazioni
        user.email = user_info.get('email', user.email)
        user.name = user_info.get('name', user.name)
        user.last_login = datetime.utcnow()
        db.session.commit()
        return user

    # Creare nuovo utente
    user = User(
        email=user_info['email'],
        name=user_info.get('name', ''),
        idp_subject=user_info['sub'],
        idp_issuer=user_info['iss'],
        email_verified=user_info.get('email_verified', False),
    )
    db.session.add(user)
    db.session.commit()
    return user
```

---

## Token Management — Access Token e Refresh Token

### Ciclo di Vita dei Token

**Access Token**: token di breve durata (tipicamente 5-60 minuti) utilizzato per autenticare le richieste API. Contiene i claim necessari per l'autorizzazione. Può essere un JWT (self-contained, verificabile senza chiamare l'IdP) o un opaque token (richiede introspezione presso l'IdP).

**Refresh Token**: token di lunga durata (giorni, settimane, o più) utilizzato per ottenere nuovi access token senza richiedere all'utente di ri-autenticarsi. Il refresh token viene scambiato per un nuovo access token quando quest'ultimo scade.

**ID Token**: token monouso utilizzato durante il flusso di autenticazione. Non dovrebbe essere usato per autorizzare richieste API successive.

**Confronto durate tipiche**:

| Token | Durata tipica | Dove salvarlo | Revocabile? |
|---|---|---|---|
| Access Token | 5-60 minuti | Server-side session o in-memory (SPA) | Sì (se opaque), No (se JWT senza blacklist) |
| Refresh Token | 7-90 giorni | Server-side session (mai nel browser) | Sì (sempre) |
| ID Token | Monouso | Non salvare | N/A |
| Authorization Code | 30-60 secondi | Non salvare | N/A (monouso) |

### Token Refresh Flow

```python
class TokenManager:
    def __init__(self, oidc_config):
        self.config = oidc_config

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Ottenere un nuovo access token usando il refresh token"""

        response = requests.post(
            self.config['token_endpoint'],
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.config['client_id'],
                'client_secret': self.config['client_secret'],
            }
        )

        if response.status_code != 200:
            raise TokenRefreshError(
                f"Token refresh failed: {response.json()}"
            )

        tokens = response.json()
        return {
            'access_token': tokens['access_token'],
            'refresh_token': tokens.get('refresh_token', refresh_token),
            'expires_in': tokens['expires_in'],
        }

    def ensure_valid_token(self, user_session) -> str:
        """Verificare che l'access token sia valido, rinnovarlo se necessario"""

        if not self.is_token_expired(user_session.access_token):
            return user_session.access_token

        # Token scaduto, usare il refresh token
        try:
            new_tokens = self.refresh_access_token(
                user_session.refresh_token
            )
            user_session.access_token = new_tokens['access_token']
            user_session.refresh_token = new_tokens['refresh_token']
            user_session.token_expires_at = (
                datetime.utcnow() +
                timedelta(seconds=new_tokens['expires_in'])
            )
            db.session.commit()
            return new_tokens['access_token']
        except TokenRefreshError:
            # Refresh token invalido — richiedere ri-autenticazione
            raise AuthenticationRequiredError()
```

### Sicurezza dei Token

**Storage dei token**:
- **Backend (server-side session)**: approccio più sicuro. I token non vengono mai esposti al frontend. La sessione è identificata da un cookie HttpOnly, Secure, SameSite.
- **Frontend (SPA)**: se i token devono risiedere nel frontend, utilizzare solo in-memory storage (variabili JavaScript). MAI localStorage o sessionStorage per access token.
- **Refresh token rotation**: ad ogni uso del refresh token, il server emette un nuovo refresh token e invalida il precedente. Se un refresh token viene usato due volte, tutti i token della sessione vengono invalidati (possibile compromissione).

**Token binding**: associare il token a un fingerprint del client (IP, User-Agent hash, device fingerprint) per limitare l'uso da parte di un attaccante che ruba il token.

### Token Revocation

La revoca dei token (RFC 7009) è necessaria per scenari come: logout esplicito, cambio password, account compromesso, dipendente che lascia l'azienda.

```python
class TokenRevocationService:
    def revoke_token(self, token: str, token_type_hint: str = 'refresh_token'):
        """Revocare un token presso l'Authorization Server"""
        response = requests.post(
            self.revocation_endpoint,
            data={
                'token': token,
                'token_type_hint': token_type_hint,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
        )
        # RFC 7009: il server DEVE rispondere 200 anche se il token non esiste
        return response.status_code == 200

    def revoke_all_user_tokens(self, user_id: str):
        """Revocare tutti i token attivi per un utente (es. cambio password)"""
        sessions = UserSession.query.filter_by(user_id=user_id, active=True).all()
        for s in sessions:
            if s.refresh_token:
                self.revoke_token(s.refresh_token, 'refresh_token')
            s.active = False
        db.session.commit()
```

Per JWT (access token self-contained), la revoca richiede una blacklist lato server poiché il token è auto-validante. Approcci:
- **Blacklist in-memory/Redis**: controllare il `jti` del token contro una lista di token revocati
- **Short expiration**: access token molto brevi (5 minuti) riducono la finestra di rischio
- **Token introspection**: usare opaque token e validare contro l'Authorization Server ad ogni richiesta

---

## Session Management

La gestione della sessione applicativa è il ponte tra il protocollo di autenticazione (OAuth/OIDC/SAML) e l'esperienza utente continua nell'applicazione.

### Sessione Server-Side vs. Stateless

**Server-side session** (raccomandato per la maggior parte dei SaaS):
```python
# Configurazione sessione sicura
app.config.update(
    SESSION_COOKIE_SECURE=True,          # Solo HTTPS
    SESSION_COOKIE_HTTPONLY=True,         # Non accessibile da JavaScript
    SESSION_COOKIE_SAMESITE='Lax',       # Protezione CSRF
    SESSION_COOKIE_NAME='__Host-sid',    # Prefisso __Host- per binding a dominio + secure
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),  # Timeout assoluto
)
```

**Token-based session** (JWT nel cookie): approccio stateless, ma la revoca è complessa (vedi sopra). Utile quando il backend è distribuito senza session store condiviso.

### Timeout e Politiche di Sessione

| Tipo di timeout | Durata tipica | Scopo |
|---|---|---|
| Idle timeout | 15-60 minuti | Sessione scade dopo inattività |
| Absolute timeout | 8-24 ore | Sessione scade indipendentemente dall'attività |
| MFA re-prompt | 4-8 ore | Richiedere MFA per operazioni sensibili |
| Privileged timeout | 5-15 minuti | Step-up auth per azioni critiche (cambio password, export dati) |

```python
class SessionManager:
    def validate_session(self, session_id: str) -> bool:
        """Validare una sessione attiva"""
        session = Session.query.get(session_id)
        if not session or not session.active:
            return False

        now = datetime.utcnow()

        # Absolute timeout
        if now > session.created_at + timedelta(hours=8):
            self.terminate_session(session_id)
            return False

        # Idle timeout
        if now > session.last_activity + timedelta(minutes=30):
            self.terminate_session(session_id)
            return False

        # Aggiornare last_activity
        session.last_activity = now
        db.session.commit()
        return True

    def terminate_session(self, session_id: str):
        """Terminare una sessione e pulire i dati"""
        session = Session.query.get(session_id)
        if session:
            session.active = False
            session.terminated_at = datetime.utcnow()
            # Revocare i token associati
            if session.refresh_token:
                token_revocation.revoke_token(session.refresh_token)
            db.session.commit()
```

### Session Fixation Prevention

Alla autenticazione, rigenerare sempre l'ID di sessione per prevenire attacchi di session fixation:

```python
@app.route('/auth/callback')
def auth_callback():
    # ... validazione token ...

    # CRITICO: rigenerare la sessione dopo l'autenticazione
    old_session_data = dict(session)
    session.clear()
    session.regenerate()  # Nuovo ID di sessione

    # Ripopolare solo i dati necessari
    session['user_id'] = user.id
    session['authenticated_at'] = datetime.utcnow().isoformat()
```

### Cross-Device Session Management

Per SaaS enterprise, offrire visibilità sulle sessioni attive:

```python
@app.route('/account/sessions')
def list_active_sessions():
    """Mostrare all'utente tutte le sue sessioni attive"""
    sessions = Session.query.filter_by(
        user_id=current_user.id,
        active=True,
    ).order_by(Session.last_activity.desc()).all()

    return jsonify([{
        'id': s.id,
        'device': s.user_agent_parsed,
        'ip_address': s.ip_address,
        'location': geoip_lookup(s.ip_address),
        'last_activity': s.last_activity.isoformat(),
        'current': s.id == session.get('session_id'),
    } for s in sessions])

@app.route('/account/sessions/<session_id>/revoke', methods=['POST'])
def revoke_session(session_id):
    """Permettere all'utente di revocare una sessione specifica"""
    target = Session.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()
    session_manager.terminate_session(session_id)
    return jsonify({'status': 'revoked'})
```

---

## SAML 2.0 — Enterprise SSO

### Perché SAML nel 2024+

Nonostante OIDC sia tecnicamente superiore e più moderno, SAML 2.0 rimane il protocollo dominante per l'SSO enterprise. La ragione è pratica: la maggior parte delle grandi aziende utilizza IdP che supportano SAML 2.0 da anni (Active Directory Federation Services, Okta, Ping Identity), e le configurazioni SAML sono già in produzione per centinaia di applicazioni. Per vendere a clienti enterprise, supportare SAML 2.0 è spesso un requisito non negoziabile.

### SAML 2.0 SP-Initiated Flow

Il flusso più comune per SaaS è l'SP-Initiated SSO, dove l'utente inizia il flusso dal Service Provider (il SaaS):

```
┌──────┐         ┌──────────┐         ┌──────────┐
│ User │         │    SP     │         │   IdP    │
│      │         │  (SaaS)  │         │  (Okta)  │
└──┬───┘         └────┬─────┘         └────┬─────┘
   │ 1. Accede a      │                    │
   │    app.saas.com   │                    │
   │──────────────────>│                    │
   │                   │                    │
   │ 2. Redirect con   │                    │
   │    AuthnRequest   │                    │
   │<──────────────────│                    │
   │                   │                    │
   │ 3. POST AuthnRequest                  │
   │───────────────────────────────────────>│
   │                   │                    │
   │ 4. Login (se non  │                    │
   │    già autenticato)│                   │
   │<──────────────────────────────────────>│
   │                   │                    │
   │ 5. POST SAML Response                 │
   │    con Assertion   │                   │
   │<───────────────────────────────────────│
   │                   │                    │
   │ 6. Forward SAML   │                    │
   │    Response al SP  │                   │
   │──────────────────>│                    │
   │                   │                    │
   │                   │ 7. Validare        │
   │                   │    Assertion       │
   │                   │                    │
   │ 8. Autenticato!   │                    │
   │<──────────────────│                    │
```

### SAML 2.0 IdP-Initiated Flow

Nell'IdP-Initiated flow, l'utente parte dal portale dell'IdP (es. il dashboard Okta) e clicca sull'icona dell'applicazione SaaS. L'IdP genera direttamente una SAML Response senza che il SP abbia inviato un AuthnRequest.

```
┌──────┐         ┌──────────┐         ┌──────────┐
│ User │         │   IdP    │         │    SP     │
│      │         │  (Okta)  │         │  (SaaS)  │
└──┬───┘         └────┬─────┘         └────┬─────┘
   │ 1. Click app     │                    │
   │    nel portale    │                    │
   │──────────────────>│                    │
   │                   │                    │
   │                   │ 2. Generare        │
   │                   │    SAML Response   │
   │                   │    (no AuthnReq)   │
   │                   │                    │
   │ 3. POST SAML Response al SP           │
   │<──────────────────│                    │
   │───────────────────────────────────────>│
   │                   │                    │
   │                   │ 4. Validare        │
   │                   │    Assertion       │
   │                   │                    │
   │ 5. Autenticato!   │                    │
   │<───────────────────────────────────────│
```

**Rischio di sicurezza dell'IdP-Initiated flow**: poiché non c'è un AuthnRequest con un `InResponseTo` da verificare, il flusso è vulnerabile a SAML Response replay. Mitigazioni: validare rigorosamente `NotOnOrAfter`, `NotBefore`, e usare una cache di `ResponseID` per prevenire replay.

### Scambio Metadata e Configurazione

Il metadata XML è il meccanismo di configurazione reciproca tra SP e IdP in SAML 2.0. Contiene gli endpoint, i certificati, e i binding supportati.

**SP Metadata** (che il SaaS espone all'IdP del cliente):
```xml
<md:EntityDescriptor
  entityID="https://your-app.com/saml/metadata"
  xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">

  <md:SPSSODescriptor
    protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"
    AuthnRequestsSigned="true"
    WantAssertionsSigned="true">

    <md:KeyDescriptor use="signing">
      <ds:KeyInfo>
        <ds:X509Data>
          <ds:X509Certificate>MIID...certificato-SP...</ds:X509Certificate>
        </ds:X509Data>
      </ds:KeyInfo>
    </md:KeyDescriptor>

    <md:AssertionConsumerService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="https://your-app.com/saml/acs"
      index="0"
      isDefault="true"/>

    <md:SingleLogoutService
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
      Location="https://your-app.com/saml/sls"/>

    <md:NameIDFormat>
      urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress
    </md:NameIDFormat>

  </md:SPSSODescriptor>
</md:EntityDescriptor>
```

**Flusso di configurazione tipico**:
1. L'admin del SaaS fornisce l'URL del metadata SP al cliente (`https://app.com/saml/metadata`)
2. L'admin IT del cliente configura l'applicazione nell'IdP usando il metadata SP
3. L'admin IT del cliente fornisce il metadata dell'IdP al SaaS (URL o file XML)
4. Il SaaS configura la connessione SAML per quel tenant con il metadata dell'IdP
5. Test con un utente pilota

### Implementazione SAML con python3-saml

```python
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

# Configurazione SAML (settings.json)
SAML_SETTINGS = {
    "sp": {
        "entityId": "https://your-app.com/saml/metadata",
        "assertionConsumerService": {
            "url": "https://your-app.com/saml/acs",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        },
        "singleLogoutService": {
            "url": "https://your-app.com/saml/sls",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
    },
    "idp": {
        "entityId": "https://customer-idp.okta.com/...",
        "singleSignOnService": {
            "url": "https://customer-idp.okta.com/app/.../sso/saml",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "x509cert": "MIID...certificate...",
    },
    "security": {
        "authnRequestsSigned": True,
        "wantAssertionsSigned": True,
        "wantNameIdEncrypted": False,
        "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
    }
}


@app.route('/saml/login')
def saml_login():
    """Iniziare il flusso SAML SP-Initiated"""
    auth = init_saml_auth(request)
    return redirect(auth.login())


@app.route('/saml/acs', methods=['POST'])
def saml_acs():
    """Assertion Consumer Service — ricevere la SAML Response"""
    auth = init_saml_auth(request)
    auth.process_response()

    errors = auth.get_errors()
    if errors:
        logger.error(f"SAML errors: {errors}")
        return f'SAML authentication failed: {errors}', 400

    if not auth.is_authenticated():
        return 'Authentication failed', 401

    # Estrarre gli attributi dall'assertion
    attributes = auth.get_attributes()
    name_id = auth.get_nameid()

    user_info = {
        'email': name_id,
        'name': attributes.get('name', [None])[0],
        'groups': attributes.get('groups', []),
        'department': attributes.get('department', [None])[0],
    }

    # Trovare o creare l'utente
    user = find_or_create_sso_user(user_info)

    # Creare la sessione
    session['user_id'] = user.id
    session['saml_session_index'] = auth.get_session_index()

    return redirect('/dashboard')


@app.route('/saml/metadata')
def saml_metadata():
    """Esporre il metadata SP per la configurazione dell'IdP"""
    auth = init_saml_auth(request)
    metadata = auth.get_settings().get_sp_metadata()
    errors = auth.get_settings().validate_metadata(metadata)

    if errors:
        return f'Metadata error: {errors}', 500

    return metadata, 200, {'Content-Type': 'text/xml'}
```

### Configurazione Multi-Tenant SAML

In un prodotto SaaS multi-tenant, ogni tenant enterprise può avere il proprio IdP con configurazione SAML diversa:

```python
class SAMLConfigStore:
    def get_config(self, tenant_id: str) -> dict:
        """Recuperare la configurazione SAML per un tenant specifico"""
        config = SAMLTenantConfig.query.filter_by(
            tenant_id=tenant_id
        ).first()

        if not config:
            return None

        return {
            "idp": {
                "entityId": config.idp_entity_id,
                "singleSignOnService": {
                    "url": config.idp_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": config.idp_certificate,
            },
            # SP config rimane uguale per tutti i tenant
            "sp": DEFAULT_SP_CONFIG,
            "security": DEFAULT_SECURITY_CONFIG,
        }
```

**Identificare il tenant dal login**: quando l'utente accede a `/login`, è necessario identificare il tenant per caricare la configurazione SAML corretta. Approcci comuni:

1. **Subdomain-based**: `acme.app.com` -> tenant = "acme"
2. **Email domain**: l'utente inserisce l'email -> lookup del dominio `@acme.com` -> configurazione SAML per acme
3. **Slug-based URL**: `app.com/org/acme/login`
4. **Custom login page**: ogni tenant ha un URL di login dedicato

---

## SSO Architecture Patterns

### Hub-and-Spoke

L'architettura hub-and-spoke ha un Identity Provider centrale (hub) che autentica gli utenti per molteplici applicazioni (spoke). Ogni applicazione ha una relazione di fiducia diretta con il singolo IdP.

```
                    ┌─────────────────┐
                    │   IdP (Hub)     │
                    │   es. Okta      │
                    │                 │
                    └────────┬────────┘
                   ┌─────────┼─────────┐
                   │         │         │
              ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐
              │ App A  │ │ App B  │ │ App C  │
              │ (SaaS) │ │ (SaaS) │ │ (SaaS) │
              └────────┘ └────────┘ └────────┘
```

**Vantaggi**: configurazione semplice, single source of truth per le identità, l'admin gestisce tutto da un punto.

**Svantaggi**: single point of failure, il passaggio a un IdP diverso richiede riconfigurazione di tutte le applicazioni.

**Quando usarlo**: la maggior parte delle PMI e mid-market che usano un solo IdP aziendale.

### Federation (Multi-IdP)

Nell'architettura federata, il SaaS deve supportare molteplici IdP contemporaneamente, ognuno per un tenant diverso.

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ IdP A    │  │ IdP B    │  │ IdP C    │
│ (Okta)   │  │ (AzureAD)│  │ (Google) │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     │    ┌────────▼────────┐    │
     └───>│    SaaS App     │<───┘
          │ (Multi-Tenant)  │
          │                 │
          │ Router per      │
          │ dominio/tenant  │
          └─────────────────┘
```

**Implementazione del router**:
```python
class SSORouter:
    """Determinare il flusso SSO corretto per ogni utente"""

    def resolve_sso_config(self, email_or_domain: str) -> dict:
        """Risolvere la configurazione SSO dal dominio email o tenant slug"""
        domain = email_or_domain.split('@')[-1] if '@' in email_or_domain else email_or_domain

        config = SSODomainMapping.query.filter_by(
            email_domain=domain, active=True
        ).first()

        if not config:
            return {'type': 'password'}  # Fallback a login con password

        return {
            'type': config.protocol,  # 'saml' o 'oidc'
            'tenant_id': config.tenant_id,
            'idp_config': config.get_idp_configuration(),
        }
```

### Identity Broker

Un identity broker è un intermediario che gestisce le relazioni con molteplici IdP, semplificando l'integrazione lato applicazione. L'applicazione comunica solo con il broker, che si occupa della traduzione dei protocolli.

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ IdP A    │  │ IdP B    │  │ IdP C    │
│ (SAML)   │  │ (OIDC)   │  │ (LDAP)   │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     │    ┌────────▼────────┐    │
     └───>│ Identity Broker │<───┘
          │ (KeyCloak, Auth0)│
          └────────┬────────┘
                   │ OIDC (protocollo unificato)
          ┌────────▼────────┐
          │    SaaS App     │
          └─────────────────┘
```

**Vantaggi**: l'applicazione implementa un solo protocollo (OIDC verso il broker), il broker gestisce la complessità di molteplici protocolli e IdP.

**Svantaggi**: latenza aggiuntiva, dependency su un servizio intermedio, costo del broker.

**Quando usarlo**: SaaS che deve supportare decine di IdP diversi (es. marketplace B2B), oppure organizzazioni con IdP legacy (LDAP, Kerberos) che vogliono modernizzare gradualmente.

---

## Integrazione con Identity Provider Enterprise

### Confronto Identity Provider

| Caratteristica | Okta | Auth0 | Azure AD (Entra ID) | Google Workspace | KeyCloak |
|---|---|---|---|---|---|
| **Tipo** | Cloud | Cloud | Cloud | Cloud | Self-hosted / Cloud |
| **SAML 2.0** | Completo | Completo | Completo | SP only | Completo (SP + IdP) |
| **OIDC** | Completo | Completo | Completo | Completo | Completo |
| **SCIM** | Completo | Sì (via ext.) | Sì | Parziale | Sì (via plugin) |
| **Pricing model** | Per utente/mese | Per MAU | Per utente/mese (M365) | Incluso in Workspace | Open source (gratuito) |
| **Prezzo entry** | ~$2/user/mese | Gratuito fino 7.500 MAU | Incluso in M365 E3+ | Incluso in Workspace | Gratuito |
| **MFA nativo** | Sì (Okta Verify) | Sì (Guardian) | Sì (Authenticator) | Sì (2FA Google) | Sì (TOTP, WebAuthn) |
| **Self-service setup** | Sì | Sì | Parziale | No | Sì |
| **Target** | Enterprise | Startup/Mid-market | Microsoft-shop | Google-shop | DevOps/On-prem |
| **Universal Directory** | Sì | Sì | Azure AD | Google Directory | Sì |
| **API maturity** | Eccellente | Eccellente | Buona (Graph API) | Buona | Buona |
| **Marketplace** | Okta Integration Network | Auth0 Marketplace | Azure AD Gallery | Google Workspace Marketplace | N/A |
| **Complessità setup** | Media | Bassa | Media-Alta | Bassa | Alta (self-hosted) |

### Okta Integration

Okta è il leader di mercato per l'identity management enterprise. L'integrazione tipica include:

1. **Configurazione dell'applicazione su Okta**: l'admin IT del cliente crea un'applicazione SAML/OIDC nella propria console Okta.
2. **Scambio di metadata**: il cliente fornisce il metadata dell'IdP, il SaaS provider fornisce il metadata del SP.
3. **Attribute mapping**: configurare il mapping tra gli attributi Okta (firstName, lastName, email, groups) e gli attributi attesi dal SP.
4. **Group assignment**: l'admin assegna i gruppi Okta che devono avere accesso all'applicazione SaaS.

**Okta Integration Network (OIN)**: per SaaS vendor, pubblicare l'integrazione sull'OIN (il marketplace Okta) semplifica drasticamente il setup per i clienti e dà visibilità nella directory. Requisiti: supporto SAML/OIDC, SCIM provisioning, documentazione di configurazione.

**Configurazione OIDC con Okta**:
```
Authorization Server: https://{your-domain}.okta.com/oauth2/default
Discovery URL: https://{your-domain}.okta.com/oauth2/default/.well-known/openid-configuration
Client ID: fornito da Okta dopo la registrazione dell'app
Client Secret: fornito da Okta (proteggere con secret manager)
Scopes: openid profile email groups
```

### Azure AD (Entra ID) Integration

Azure AD (ora Microsoft Entra ID) è il secondo IdP enterprise più comune. Supporta sia SAML 2.0 che OIDC nativamente. La configurazione segue un pattern simile a Okta, con le seguenti specificità:

- **Enterprise Application**: il SaaS viene registrato come Enterprise Application in Azure AD
- **App Registration**: per OIDC, richiede una App Registration con configurazione di redirect URI e permessi
- **Claims Mapping**: Azure AD ha un sistema di claims mapping specifico che può richiedere configurazione aggiuntiva per esporre attributi custom
- **Conditional Access**: Azure AD integra policy di accesso condizionale (richiedi MFA, blocca da paesi specifici, richiedi dispositivo gestito) che l'applicazione SaaS deve rispettare
- **Graph API**: per provisioning avanzato, l'API Microsoft Graph fornisce accesso programmatico a utenti, gruppi, e directory

**Endpoint tipici Azure AD**:
```
Authorization: https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize
Token: https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
JWKS: https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys
Discovery: https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration
```

**Attenzione a `{tenant-id}`**: può essere il GUID del tenant, il dominio (`contoso.onmicrosoft.com`), oppure `common` (multi-tenant) o `organizations` (solo account aziendali).

### Google Workspace Integration

Google Workspace supporta SAML 2.0 per SSO. La configurazione avviene nella Google Admin Console (Apps -> Web and mobile apps -> Add App -> SAML).

**Limitazioni**: Google Workspace funziona solo come IdP (non come SP nel contesto enterprise). Non supporta SCIM verso applicazioni esterne in modo nativo — per il provisioning, è necessario usare la Directory API di Google.

**OIDC con Google**:
```
Discovery: https://accounts.google.com/.well-known/openid-configuration
Authorization: https://accounts.google.com/o/oauth2/v2/auth
Token: https://oauth2.googleapis.com/token
JWKS: https://www.googleapis.com/oauth2/v3/certs
```

**Scopes utili per SaaS**: `openid`, `email`, `profile`, `https://www.googleapis.com/auth/admin.directory.user.readonly` (per leggere la directory aziendale, richiede consent dell'admin di dominio).

### KeyCloak — Self-Hosted IdP

KeyCloak è un IdP open source (Red Hat/CNCF) che può essere self-hosted. È la scelta per organizzazioni che:
- Richiedono controllo totale sull'infrastruttura di identità
- Hanno requisiti di data residency che impediscono l'uso di IdP cloud
- Vogliono evitare i costi per utente degli IdP cloud
- Hanno competenze DevOps per gestire l'infrastruttura

**Configurazione OIDC con KeyCloak**:
```
Discovery: https://keycloak.example.com/realms/{realm}/.well-known/openid-configuration
Authorization: https://keycloak.example.com/realms/{realm}/protocol/openid-connect/auth
Token: https://keycloak.example.com/realms/{realm}/protocol/openid-connect/token
```

**Funzionalità rilevanti per SaaS**: realm per tenant, identity brokering (KeyCloak come broker verso altri IdP), user federation (LDAP, Active Directory), custom authenticators, eventi audit.

### Auth0 Integration

Auth0 (Okta) è popolare per startup e mid-market SaaS. Offre un approccio developer-first con SDK per tutti i linguaggi principali.

**Punti di forza**: Universal Login (pagina di login personalizzabile), Actions (hook personalizzabili nel flusso di autenticazione), Organizations (supporto multi-tenant nativo), Connections (integrazione con social provider e enterprise IdP).

**Configurazione tipica**:
```
Discovery: https://{your-domain}.auth0.com/.well-known/openid-configuration
Authorization: https://{your-domain}.auth0.com/authorize
Token: https://{your-domain}.auth0.com/oauth/token
```

---

## Social Login

Il social login permette agli utenti di autenticarsi usando i propri account social (Google, GitHub, Apple, Microsoft) senza creare credenziali specifiche per il SaaS. È essenziale per prodotti B2C e PLG (Product-Led Growth).

### Flusso Standard Social Login

Il social login usa OIDC/OAuth 2.0 sotto il cofano. Ogni provider social è un Authorization Server.

```python
# Configurazione multi-provider
SOCIAL_PROVIDERS = {
    'google': {
        'client_id': os.environ['GOOGLE_CLIENT_ID'],
        'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
        'discovery_url': 'https://accounts.google.com/.well-known/openid-configuration',
        'scopes': ['openid', 'email', 'profile'],
    },
    'github': {
        'client_id': os.environ['GITHUB_CLIENT_ID'],
        'client_secret': os.environ['GITHUB_CLIENT_SECRET'],
        'authorization_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo_url': 'https://api.github.com/user',
        'scopes': ['user:email'],
    },
    'microsoft': {
        'client_id': os.environ['MICROSOFT_CLIENT_ID'],
        'client_secret': os.environ['MICROSOFT_CLIENT_SECRET'],
        'discovery_url': 'https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
        'scopes': ['openid', 'email', 'profile'],
    },
}
```

### Account Linking e Conflitti Email

Un problema comune: l'utente si registra con Google (`mario@gmail.com`), poi tenta il login con GitHub usando la stessa email.

**Strategia di account linking**:

```python
def find_or_create_social_user(provider: str, social_profile: dict) -> User:
    """Gestire account linking per social login"""

    # 1. Cercare una connessione social esistente per questo provider + sub
    link = SocialConnection.query.filter_by(
        provider=provider,
        provider_user_id=social_profile['sub'],
    ).first()

    if link:
        return link.user  # Utente già collegato a questo provider

    # 2. Cercare per email verificata
    email = social_profile.get('email')
    email_verified = social_profile.get('email_verified', False)

    if email and email_verified:
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            # Collegare il nuovo provider all'utente esistente
            new_link = SocialConnection(
                user_id=existing_user.id,
                provider=provider,
                provider_user_id=social_profile['sub'],
            )
            db.session.add(new_link)
            db.session.commit()
            return existing_user

    # 3. Email non verificata dal provider -> NON collegare automaticamente
    #    (rischio: attaccante crea account GitHub con email della vittima)
    if email and not email_verified:
        # Creare nuovo account separato, richiedere verifica email
        pass

    # 4. Creare nuovo utente
    user = User(email=email, name=social_profile.get('name', ''))
    link = SocialConnection(
        user=user,
        provider=provider,
        provider_user_id=social_profile['sub'],
    )
    db.session.add_all([user, link])
    db.session.commit()
    return user
```

**Regola critica**: collegare automaticamente account solo quando l'email è verificata dal provider. Email non verificate aprono attacchi di pre-hijacking.

### Sign in with Apple

Apple richiede implementazioni specifiche:
- L'email può essere nascosta (relay privato): `randomhash@privaterelay.appleid.com`
- Il `name` viene fornito solo al primo login (cacheare immediatamente)
- L'endpoint token restituisce l'ID token nella prima risposta POST (non nel redirect)
- Apple richiede un endpoint server-side per ricevere notifiche di revoca e cancellazione account

---

## SCIM — Provisioning Automatico degli Utenti

### Cos'è SCIM

SCIM (System for Cross-domain Identity Management) è uno standard per l'automazione del provisioning e deprovisioning degli utenti tra l'IdP e le applicazioni SaaS. Senza SCIM, l'admin IT deve creare manualmente gli account utente in ogni applicazione SaaS. Con SCIM, quando un dipendente viene aggiunto o rimosso dall'IdP (Okta, Azure AD), l'applicazione SaaS riceve automaticamente la notifica e crea o disabilita l'account.

### SCIM API Endpoints

Lo standard SCIM 2.0 (RFC 7644) definisce un set di endpoint REST:

```
GET    /scim/v2/Users          — Lista utenti (con filtering e paginazione)
POST   /scim/v2/Users          — Creare utente
GET    /scim/v2/Users/{id}     — Dettaglio utente
PUT    /scim/v2/Users/{id}     — Aggiornare utente (completo)
PATCH  /scim/v2/Users/{id}     — Aggiornare utente (parziale)
DELETE /scim/v2/Users/{id}     — Eliminare utente

GET    /scim/v2/Groups         — Lista gruppi
POST   /scim/v2/Groups         — Creare gruppo
GET    /scim/v2/Groups/{id}    — Dettaglio gruppo
PUT    /scim/v2/Groups/{id}    — Aggiornare gruppo
PATCH  /scim/v2/Groups/{id}    — Aggiornare gruppo (parziale)
DELETE /scim/v2/Groups/{id}    — Eliminare gruppo

GET    /scim/v2/ServiceProviderConfig — Capability del server SCIM
GET    /scim/v2/Schemas               — Schema supportati
GET    /scim/v2/ResourceTypes         — Tipi di risorsa supportati
```

### Implementazione SCIM

```python
@app.route('/scim/v2/Users', methods=['POST'])
def scim_create_user():
    """SCIM: provisioning di un nuovo utente"""
    # Autenticazione: Bearer token specifico per SCIM
    if not verify_scim_token(request):
        return jsonify({'detail': 'Unauthorized'}), 401

    data = request.json

    # Estrarre i dati SCIM
    email = data.get('emails', [{}])[0].get('value')
    given_name = data.get('name', {}).get('givenName', '')
    family_name = data.get('name', {}).get('familyName', '')
    active = data.get('active', True)

    # Creare l'utente locale
    user = User(
        email=email,
        name=f"{given_name} {family_name}",
        is_active=active,
        provisioned_via='scim',
    )
    db.session.add(user)
    db.session.commit()

    # Rispondere nel formato SCIM
    return jsonify({
        'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
        'id': str(user.id),
        'userName': user.email,
        'name': {
            'givenName': given_name,
            'familyName': family_name,
        },
        'emails': [{'value': email, 'primary': True}],
        'active': user.is_active,
        'meta': {
            'resourceType': 'User',
            'created': user.created_at.isoformat(),
            'lastModified': user.updated_at.isoformat(),
        }
    }), 201


@app.route('/scim/v2/Users/<user_id>', methods=['PATCH'])
def scim_update_user(user_id):
    """SCIM: aggiornamento parziale di un utente (es. deactivation)"""
    if not verify_scim_token(request):
        return jsonify({'detail': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'detail': 'User not found'}), 404

    data = request.json
    operations = data.get('Operations', [])

    for op in operations:
        if op['op'] == 'replace':
            if 'active' in op.get('value', {}):
                user.is_active = op['value']['active']
                if not user.is_active:
                    # Deprovisioning: disabilitare l'utente
                    revoke_all_sessions(user.id)

    db.session.commit()
    return jsonify(user_to_scim(user)), 200
```

### Group Sync e Deprovisioning

La sincronizzazione dei gruppi tramite SCIM permette di mappare i gruppi dell'IdP ai ruoli/permessi dell'applicazione SaaS.

```python
@app.route('/scim/v2/Groups', methods=['POST'])
def scim_create_group():
    """SCIM: creare un gruppo con i suoi membri"""
    if not verify_scim_token(request):
        return jsonify({'detail': 'Unauthorized'}), 401

    data = request.json
    display_name = data.get('displayName')
    members = data.get('members', [])

    group = Group(
        display_name=display_name,
        external_id=data.get('externalId'),
        provisioned_via='scim',
    )
    db.session.add(group)

    # Aggiungere membri al gruppo
    for member in members:
        user = User.query.get(member.get('value'))
        if user:
            group.members.append(user)
            # Mapping gruppo -> ruolo applicativo
            apply_role_mapping(user, display_name)

    db.session.commit()
    return jsonify(group_to_scim(group)), 201


@app.route('/scim/v2/Groups/<group_id>', methods=['PATCH'])
def scim_update_group(group_id):
    """SCIM: aggiungere/rimuovere membri da un gruppo"""
    if not verify_scim_token(request):
        return jsonify({'detail': 'Unauthorized'}), 401

    group = Group.query.get(group_id)
    if not group:
        return jsonify({'detail': 'Group not found'}), 404

    operations = request.json.get('Operations', [])

    for op in operations:
        if op['op'] == 'add' and 'members' in op.get('value', {}):
            for member in op['value']['members']:
                user = User.query.get(member['value'])
                if user and user not in group.members:
                    group.members.append(user)
                    apply_role_mapping(user, group.display_name)

        elif op['op'] == 'remove':
            # path: "members[value eq \"user-id-123\"]"
            user_id = extract_user_id_from_path(op.get('path', ''))
            if user_id:
                user = User.query.get(user_id)
                if user and user in group.members:
                    group.members.remove(user)
                    remove_role_mapping(user, group.display_name)

    db.session.commit()
    return jsonify(group_to_scim(group)), 200
```

**Deprovisioning edge cases**:
- L'utente viene disabilitato nell'IdP (PATCH active=false) -> disabilitare l'account, revocare tutte le sessioni, ma mantenere i dati (l'utente potrebbe essere riattivato)
- L'utente viene eliminato dall'IdP (DELETE) -> soft-delete nell'applicazione, mantenere i dati per audit e compliance, revocare tutto
- L'utente viene rimosso da un gruppo nell'IdP -> rimuovere il ruolo associato, ma non disabilitare l'account
- Il gruppo viene eliminato nell'IdP -> rimuovere il mapping ruolo, ma non disabilitare gli utenti membri

### Riconciliazione SCIM

La sincronizzazione SCIM è event-driven (push dall'IdP). Ma push può fallire (rete, downtime, bug). La riconciliazione periodica è necessaria.

```python
class SCIMReconciliation:
    """Job periodico per riconciliare utenti SCIM con l'IdP"""

    def run_reconciliation(self, tenant_id: str):
        """Confrontare gli utenti locali con la sorgente IdP"""
        local_users = User.query.filter_by(
            tenant_id=tenant_id,
            provisioned_via='scim',
        ).all()

        # Recuperare tutti gli utenti dall'IdP (via SCIM o API specifica)
        idp_users = self.fetch_idp_users(tenant_id)

        local_by_ext_id = {u.external_id: u for u in local_users if u.external_id}
        idp_by_ext_id = {u['externalId']: u for u in idp_users}

        discrepancies = []

        # Utenti nell'IdP ma non nel SaaS (provisioning mancato)
        for ext_id, idp_user in idp_by_ext_id.items():
            if ext_id not in local_by_ext_id:
                discrepancies.append({
                    'type': 'missing_local',
                    'external_id': ext_id,
                    'email': idp_user.get('email'),
                })

        # Utenti nel SaaS ma non nell'IdP (deprovisioning mancato)
        for ext_id, local_user in local_by_ext_id.items():
            if ext_id not in idp_by_ext_id and local_user.is_active:
                discrepancies.append({
                    'type': 'orphaned_local',
                    'user_id': local_user.id,
                    'email': local_user.email,
                })

        # Attributi non allineati
        for ext_id in set(local_by_ext_id) & set(idp_by_ext_id):
            local = local_by_ext_id[ext_id]
            idp = idp_by_ext_id[ext_id]
            if local.email != idp.get('email') or local.is_active != idp.get('active', True):
                discrepancies.append({
                    'type': 'attribute_mismatch',
                    'user_id': local.id,
                    'diff': {'email': (local.email, idp.get('email'))},
                })

        return discrepancies
```

---

## Multi-Factor Authentication (MFA)

### TOTP (Time-Based One-Time Password)

```python
import pyotp
import qrcode

class MFAManager:
    def enable_totp(self, user_id: int) -> dict:
        """Abilitare TOTP MFA per un utente"""
        secret = pyotp.random_base32()

        # Generare l'URI per l'app authenticator
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name='YourSaaS'
        )

        # Salvare il secret (criptato) nel database
        user.mfa_secret = encrypt(secret)
        user.mfa_enabled = False  # Sarà True dopo la verifica
        db.session.commit()

        return {
            'secret': secret,
            'qr_code_uri': provisioning_uri,
        }

    def verify_totp(self, user_id: int, code: str) -> bool:
        """Verificare un codice TOTP"""
        user = User.query.get(user_id)
        secret = decrypt(user.mfa_secret)
        totp = pyotp.TOTP(secret)

        return totp.verify(code, valid_window=1)  # ±30 secondi
```

### SMS e Email OTP

L'OTP via SMS ed email è meno sicuro del TOTP (vulnerabile a SIM swap, intercettazione email) ma offre un'esperienza utente più accessibile per utenti non tecnici.

```python
class OTPManager:
    def send_sms_otp(self, user_id: int) -> bool:
        """Inviare un codice OTP via SMS"""
        user = User.query.get(user_id)
        code = secrets.randbelow(900000) + 100000  # 6 cifre: 100000-999999

        # Salvare l'OTP con scadenza
        otp_record = OTPRecord(
            user_id=user_id,
            code_hash=hash_otp(str(code)),
            channel='sms',
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            attempts_remaining=3,  # Max 3 tentativi
        )
        db.session.add(otp_record)
        db.session.commit()

        # Inviare via provider SMS (es. Twilio)
        sms_provider.send(
            to=user.phone_number,
            body=f"Il tuo codice di verifica e': {code}. Valido per 5 minuti."
        )
        return True

    def verify_otp(self, user_id: int, code: str, channel: str) -> bool:
        """Verificare un codice OTP"""
        record = OTPRecord.query.filter_by(
            user_id=user_id,
            channel=channel,
        ).filter(
            OTPRecord.expires_at > datetime.utcnow(),
            OTPRecord.used == False,
            OTPRecord.attempts_remaining > 0,
        ).order_by(OTPRecord.created_at.desc()).first()

        if not record:
            return False

        record.attempts_remaining -= 1

        if verify_otp_hash(code, record.code_hash):
            record.used = True
            db.session.commit()
            return True

        db.session.commit()
        return False
```

### Backup Codes

I backup codes sono codici monouso che l'utente genera durante il setup MFA. Servono come fallback quando il dispositivo MFA è perso o non disponibile.

```python
class BackupCodeManager:
    def generate_backup_codes(self, user_id: int, count: int = 10) -> list[str]:
        """Generare codici di backup monouso"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4)  # 8 caratteri hex: es. "a3f2b1c8"
            formatted = f"{code[:4]}-{code[4:]}"  # "a3f2-b1c8"
            codes.append(formatted)

            # Salvare l'hash del codice
            backup = BackupCode(
                user_id=user_id,
                code_hash=hash_backup_code(formatted),
                used=False,
            )
            db.session.add(backup)

        db.session.commit()

        # Restituire i codici in chiaro SOLO in questo momento
        # L'utente deve salvarli — non saranno mai più visibili
        return codes

    def verify_backup_code(self, user_id: int, code: str) -> bool:
        """Verificare e consumare un codice di backup"""
        backups = BackupCode.query.filter_by(
            user_id=user_id, used=False
        ).all()

        for backup in backups:
            if verify_backup_hash(code, backup.code_hash):
                backup.used = True
                backup.used_at = datetime.utcnow()
                db.session.commit()

                # Avvisare l'utente se i codici stanno finendo
                remaining = BackupCode.query.filter_by(
                    user_id=user_id, used=False
                ).count()
                if remaining <= 2:
                    notify_low_backup_codes(user_id, remaining)

                return True
        return False
```

### Policy di Enforcement MFA

Per SaaS enterprise, l'MFA deve essere configurabile a livello di tenant:

```python
class MFAPolicy:
    """Policy MFA configurabile per tenant"""

    LEVELS = {
        'none': [],
        'optional': [],          # L'utente sceglie se abilitare
        'required_admins': ['admin', 'owner'],  # Solo admin
        'required_all': ['*'],   # Tutti gli utenti del tenant
    }

    def check_mfa_required(self, user: User, action: str = 'login') -> bool:
        """Determinare se MFA è richiesto per questo utente/azione"""
        tenant_policy = TenantMFAPolicy.query.filter_by(
            tenant_id=user.tenant_id
        ).first()

        if not tenant_policy:
            return False

        # MFA sempre richiesto per operazioni sensibili
        sensitive_actions = ['change_password', 'export_data', 'delete_account',
                           'invite_admin', 'change_billing', 'api_key_create']
        if action in sensitive_actions:
            return True

        # MFA richiesto per ruoli specifici
        required_roles = self.LEVELS.get(tenant_policy.level, [])
        if '*' in required_roles:
            return True
        if user.role in required_roles:
            return True

        return False
```

---

## WebAuthn e Passkeys

WebAuthn (Web Authentication, W3C) è lo standard per autenticazione passwordless usando crittografia a chiave pubblica. I passkeys (FIDO2) sono l'implementazione consumer-friendly di WebAuthn.

### Come Funziona WebAuthn

A differenza di TOTP (shared secret), WebAuthn usa una coppia di chiavi asimmetriche: la chiave privata resta nel dispositivo dell'utente (o in un security key), la chiave pubblica viene registrata nel server.

**Cerimonia di Registrazione (attestation)**:

```
┌──────┐         ┌──────────┐         ┌──────────────────┐
│ User │         │  Server  │         │ Authenticator     │
│      │         │  (RP)    │         │ (YubiKey/Touch ID)│
└──┬───┘         └────┬─────┘         └────────┬──────────┘
   │                  │                         │
   │ 1. "Registra     │                         │
   │    passkey"       │                         │
   │─────────────────>│                         │
   │                  │ 2. challenge +          │
   │                  │    rp_id + user_info    │
   │<─────────────────│                         │
   │                  │                         │
   │ 3. Presentare challenge all'authenticator  │
   │───────────────────────────────────────────>│
   │                  │                         │
   │                  │    4. Generare coppia    │
   │                  │       chiavi (privata    │
   │                  │       + pubblica)        │
   │                  │                         │
   │                  │    5. Firmare challenge  │
   │                  │       con chiave privata │
   │                  │                         │
   │ 6. credential_id + public_key + attestation│
   │<───────────────────────────────────────────│
   │                  │                         │
   │ 7. Inviare al    │                         │
   │    server        │                         │
   │─────────────────>│                         │
   │                  │ 8. Validare attestation │
   │                  │    Salvare public_key   │
   │                  │                         │
   │ 9. Registrato!   │                         │
   │<─────────────────│                         │
```

**Cerimonia di Autenticazione (assertion)**:

```python
# Server-side con py_webauthn
from webauthn import (
    generate_authentication_options,
    verify_authentication_response,
)

@app.route('/webauthn/login/begin', methods=['POST'])
def webauthn_login_begin():
    """Iniziare la cerimonia di autenticazione WebAuthn"""
    email = request.json.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        # Non rivelare se l'utente esiste
        # Generare opzioni fittizie con lo stesso timing
        return generate_fake_options()

    # Recuperare i credential registrati per l'utente
    credentials = WebAuthnCredential.query.filter_by(user_id=user.id).all()

    options = generate_authentication_options(
        rp_id="your-app.com",
        allow_credentials=[{
            'id': cred.credential_id,
            'type': 'public-key',
            'transports': cred.transports,
        } for cred in credentials],
        user_verification='preferred',
        timeout=60000,  # 60 secondi
    )

    # Salvare challenge in sessione per la verifica
    session['webauthn_challenge'] = options.challenge

    return jsonify(options_to_dict(options))


@app.route('/webauthn/login/complete', methods=['POST'])
def webauthn_login_complete():
    """Completare la cerimonia di autenticazione WebAuthn"""
    credential_response = request.json

    credential = WebAuthnCredential.query.filter_by(
        credential_id=credential_response['id']
    ).first()

    if not credential:
        return jsonify({'error': 'Credential non riconosciuto'}), 401

    try:
        verification = verify_authentication_response(
            credential=credential_response,
            expected_challenge=session.get('webauthn_challenge'),
            expected_rp_id="your-app.com",
            expected_origin="https://your-app.com",
            credential_public_key=credential.public_key,
            credential_current_sign_count=credential.sign_count,
        )

        # Aggiornare il sign count per rilevare credential clonati
        credential.sign_count = verification.new_sign_count
        db.session.commit()

        # Autenticazione riuscita
        session['user_id'] = credential.user_id
        return jsonify({'status': 'authenticated'})

    except Exception as e:
        return jsonify({'error': 'Verifica fallita'}), 401
```

### Platform Authenticator vs. Roaming Authenticator

| Tipo | Esempio | Pro | Contro |
|---|---|---|---|
| **Platform** (resident key) | Touch ID, Windows Hello, Face ID | Frictionless, sempre disponibile | Legato al dispositivo specifico |
| **Roaming** (cross-platform) | YubiKey, Titan Key | Portabile, indipendente dal dispositivo | Hardware aggiuntivo, possibile perdita |
| **Passkey sincronizzato** | iCloud Keychain, Google Password Manager | Backup automatico, multi-dispositivo | Legato all'ecosistema (Apple/Google) |

**Per SaaS**: supportare sia platform che roaming authenticator. I passkeys sincronizzati sono il futuro per l'adozione consumer. Per enterprise, le security key hardware (YubiKey) rimangono lo standard per compliance (FIDO2 Certified).

---

## Enterprise SSO — Implicazioni Commerciali

### Il Dibattito "SSO Tax"

Molti SaaS fanno pagare un sovrapprezzo per SSO, tipicamente richiedendo un upgrade al piano enterprise. Questo è noto come "SSO tax" nella community e genera controversie (vedi ssoready.com/blog/announce e sso.tax). L'argomento critico: SSO è una funzionalità di sicurezza, non una feature premium — farla pagare disincentiva l'adozione di pratiche di sicurezza.

**Approcci al pricing SSO**:

| Strategia | Descrizione | Esempi |
|---|---|---|
| **SSO incluso in tutti i piani** | SSO SAML/OIDC disponibile anche nel piano base | Slack (free), Notion |
| **SSO nel piano Business** | SSO disponibile dal piano mid-tier | Atlassian, Figma |
| **SSO solo Enterprise** | SSO richiede il piano enterprise (spesso con pricing custom) | Molti SaaS B2B |
| **SSO as add-on** | SSO acquistabile come modulo aggiuntivo a qualsiasi piano | Alcuni SaaS |

**Raccomandazione pragmatica**: OIDC è relativamente semplice da implementare. Includere OIDC SSO nel piano mid-tier è un investimento ragionevole che accelera la pipeline enterprise. SAML, SCIM, e funzionalità enterprise avanzate (audit log, directory sync) possono giustificare un prezzo enterprise.

### SSO nel Ciclo di Vendita Enterprise

Il supporto SSO impatta direttamente il ciclo di vendita:

1. **Compliance checkbox**: la maggior parte degli audit di sicurezza (SOC 2, ISO 27001) richiede SSO. Senza SSO, il prodotto non supera il security review.
2. **Procurement timeline**: SSO supportato = settimane di negoziazione in meno. L'IT non deve fare eccezioni alla policy.
3. **User provisioning**: SCIM riduce il tempo di onboarding da giorni (manuale) a minuti (automatico).
4. **Retention e lock-in**: utenti con SSO enterprise hanno churn rate significativamente più basso (l'IT deve attivamente rimuovere l'integrazione per cancellare).
5. **Competitive moat**: in RFP enterprise, l'assenza di SSO/SCIM è un eliminatore.

### Checklist Enterprise SSO per Vendita

Prima di contattare clienti enterprise, verificare:
- [ ] SAML 2.0 SP-Initiated flow funzionante
- [ ] OIDC Authorization Code + PKCE funzionante
- [ ] SCIM 2.0 provisioning/deprovisioning
- [ ] Multi-tenant: ogni tenant con IdP indipendente
- [ ] Forced SSO: possibilità di disabilitare login con password per un dominio
- [ ] Guida di configurazione per Okta, Azure AD, Google Workspace
- [ ] Metadata XML esposto (endpoint /saml/metadata)
- [ ] Audit log degli eventi di autenticazione
- [ ] JIT (Just-In-Time) provisioning come alternativa a SCIM
- [ ] MFA enforcement configurabile per tenant
- [ ] SLA e supporto per la configurazione SSO

---

## Best Practices

1. **Supportare sia OIDC che SAML**: OIDC per modern SSO e social login, SAML per enterprise SSO legacy. Molti clienti enterprise richiedono SAML.

2. **Usare Authorization Code + PKCE sempre**: anche per applicazioni server-side, PKCE aggiunge sicurezza senza costo.

3. **Non implementare l'auth da zero**: utilizzare librerie mature (python3-saml, passport.js, Spring Security) o servizi dedicati (Auth0, Clerk, WorkOS).

4. **Token rotation per refresh token**: invalidare il refresh token precedente ad ogni utilizzo.

5. **SCIM è un differenziatore enterprise**: il supporto SCIM riduce drasticamente il carico operativo per l'IT del cliente e accelera il ciclo di vendita enterprise.

6. **Logging completo degli eventi auth**: registrare ogni login, logout, login fallito, MFA challenge, e token refresh per audit e debugging.

7. **Separare autenticazione e autorizzazione**: l'IdP gestisce chi sei, l'applicazione gestisce cosa puoi fare.

8. **Force SSO per account enterprise**: quando un dominio è configurato per SSO, forzare tutti gli utenti di quel dominio a usare SSO (disabilitare login con password).

9. **Validare sempre l'issuer e l'audience dei JWT**: verificare che il token provenga dall'IdP atteso e sia destinato alla propria applicazione. Non saltare mai questa validazione.

10. **Implementare rate limiting sugli endpoint auth**: login, token refresh, SCIM. Prevenire brute force e abuse.

11. **Gestire la rotazione dei certificati**: i certificati SAML e le chiavi JWKS scadono. Monitorare le scadenze e implementare procedure di rotazione senza downtime (periodo di overlap con entrambi i certificati validi).

12. **Offrire self-service SSO setup**: un pannello di configurazione SSO nell'applicazione riduce il carico del supporto e accelera il deployment.

13. **Implementare JIT provisioning come fallback**: se SCIM non è configurato, creare automaticamente l'utente al primo login SSO (Just-In-Time provisioning) con attributi dal token.

14. **Testare con molteplici IdP**: ogni IdP ha le sue peculiarità. Testare regolarmente con Okta, Azure AD, e Google Workspace come minimo.

15. **Non esporre informazioni sensibili nei messaggi di errore**: "Autenticazione fallita" è sufficiente. Non rivelare se l'utente esiste, se la password è sbagliata, o dettagli sull'IdP.

---

## Troubleshooting

### 1. SAML Assertion Validation Fails

**Diagnosi**: errori comuni: certificato IdP scaduto o errato, clock skew tra SP e IdP (assertion timestamp out of range), ACS URL mismatch, audience restriction mismatch.

**Soluzione**: verificare il certificato nella configurazione, sincronizzare i clock (NTP), verificare che l'ACS URL nel SP config corrisponda esattamente a quello configurato nell'IdP, verificare che l'Entity ID corrisponda.

### 2. Token Refresh Fallisce Silenziosamente

**Diagnosi**: il refresh token potrebbe essere scaduto, revocato dall'IdP, o il client secret potrebbe essere cambiato.

**Soluzione**: implementare un fallback che reindirizza l'utente al login quando il refresh fallisce. Monitorare i tassi di refresh failure per rilevare problemi sistemici.

### 3. SCIM Provisioning Non Sincronizzato

**Diagnosi**: utenti creati nell'IdP non appaiono nel SaaS, o utenti disabilitati nell'IdP rimangono attivi nel SaaS.

**Soluzione**: verificare i log SCIM per errori. Implementare un endpoint di riconciliazione che confronta la lista utenti IdP con quella locale e segnala le discrepanze.

### 4. "Invalid State Parameter" nel Callback OAuth

**Diagnosi**: il parametro `state` nel callback non corrisponde a quello salvato in sessione. Cause: sessione scaduta tra il redirect e il callback, utente che apre il link di login in un browser diverso, cookie bloccati.

**Soluzione**: verificare la configurazione dei cookie (SameSite, Secure, Domain). Se l'utente impiega troppo tempo nell'IdP, la sessione del server potrebbe scadere — aumentare il TTL della sessione temporanea pre-auth.

### 5. "Invalid Audience" nell'ID Token

**Diagnosi**: il claim `aud` nel token non corrisponde al `client_id` configurato nell'applicazione.

**Soluzione**: verificare che il `client_id` usato nella richiesta di autorizzazione corrisponda esattamente a quello registrato nell'IdP. Attenzione ai multi-tenant Azure AD: il `client_id` è globale, ma l'`aud` potrebbe includere l'Application ID URI.

### 6. CORS Errors nelle SPA durante il Token Exchange

**Diagnosi**: il browser blocca la richiesta POST al token endpoint per violazione CORS.

**Soluzione**: il token exchange in una SPA deve avvenire server-side (BFF pattern) o tramite un proxy. Il token endpoint dell'IdP tipicamente non permette CORS da origini arbitrarie. Alternative: usare un backend leggero come proxy, oppure un service worker.

### 7. Utente Autenticato ma Senza Permessi ("403 dopo Login")

**Diagnosi**: l'autenticazione funziona (SSO riesce) ma l'utente non ha i ruoli/permessi necessari nell'applicazione.

**Soluzione**: verificare il mapping tra gruppi IdP e ruoli applicativi. Implementare una pagina di errore chiara ("Accesso riuscito, ma non hai i permessi per questa risorsa. Contatta l'amministratore."). Non mostrare un generico 403.

### 8. SAML Metadata Non Parsificabile

**Diagnosi**: l'IdP del cliente fornisce un metadata XML che il parser SAML rifiuta.

**Soluzione**: validare il metadata con un parser XML standard prima di processarlo. Errori comuni: encoding errato, namespace mancanti, certificato in formato sbagliato. Accettare sia URL del metadata che upload diretto del file XML.

### 9. Clock Skew nelle Asserzioni SAML

**Diagnosi**: `NotBefore` e `NotOnOrAfter` dell'assertion SAML cadono fuori dalla finestra temporale del server SP.

**Soluzione**: usare NTP su tutti i server. Configurare una tolleranza (skew) di 60-120 secondi nel parser SAML. Non superare i 300 secondi — oltre indica un problema di configurazione che va risolto.

### 10. Redirect Loop al Login

**Diagnosi**: l'utente viene rimbalzato continuamente tra il SaaS e l'IdP senza mai completare il login.

**Soluzione**: cause probabili: la sessione non viene creata correttamente dopo il callback (cookie non scritto), il middleware di autenticazione non riconosce la sessione appena creata, mismatch tra dominio del cookie e dominio dell'app. Verificare: cookie domain, SameSite, path, HTTPS.

### 11. PKCE Code Verifier Mismatch

**Diagnosi**: l'Authorization Server rifiuta lo scambio del codice con errore "invalid_grant" o "code_verifier mismatch".

**Soluzione**: verificare che il `code_verifier` salvato in sessione sia lo stesso usato per generare il `code_challenge`. Errori comuni: serializzazione/deserializzazione che corrompe il valore, sessione persa tra il redirect e il callback, encoding base64url non standard (padding `=` gestito in modo inconsistente).

### 12. ID Token con Claims Mancanti

**Diagnosi**: l'ID token non contiene i claim attesi (email, name, groups).

**Soluzione**: verificare gli scope richiesti nella richiesta di autorizzazione (`openid profile email`). Per claim custom (groups, department), verificare la configurazione dell'IdP: Okta richiede un Authorization Server custom, Azure AD richiede claims mapping nell'Enterprise Application.

### 13. SCIM Bearer Token Rifiutato ("401 Unauthorized")

**Diagnosi**: l'IdP non riesce ad autenticarsi contro l'endpoint SCIM del SaaS.

**Soluzione**: verificare che il token SCIM configurato nell'IdP corrisponda esattamente a quello nel SaaS. Il token è case-sensitive. Verificare anche che non ci siano proxy o WAF che strippano l'header Authorization.

### 14. Logout SSO Non Funziona (Sessione Persistente)

**Diagnosi**: l'utente fa logout dall'IdP ma la sessione nell'applicazione SaaS resta attiva.

**Soluzione**: implementare il Single Logout (SLO) per SAML, o RP-Initiated Logout per OIDC. In alternativa, usare access token con durata breve (5-15 minuti) in modo che la sessione scada naturalmente quando il token non può essere rinnovato.

### 15. Errore "Signature Algorithm Mismatch" in SAML

**Diagnosi**: il SP si aspetta SHA-256 ma l'IdP firma con SHA-1, o viceversa.

**Soluzione**: allineare l'algoritmo di firma tra SP e IdP. SHA-256 (`rsa-sha256`) è il minimo raccomandato. SHA-1 è deprecato e non dovrebbe essere accettato. Verificare sia la firma della Response che quella dell'Assertion (possono usare algoritmi diversi).

### 16. JIT Provisioning Crea Utenti Duplicati

**Diagnosi**: ogni login SSO crea un nuovo utente invece di riconoscere quello esistente.

**Soluzione**: il matching dell'utente deve basarsi sul `sub` (subject) dell'IdP + `iss` (issuer), non sull'email. L'email può cambiare (cambio cognome, alias). Se l'utente esiste già con un diverso `sub`, implementare un flusso di account linking con verifica.

### 17. Certificato SAML in Scadenza

**Diagnosi**: il certificato X.509 usato dall'IdP per firmare le asserzioni sta per scadere. Se scade, tutti i login SAML falliranno.

**Soluzione**: monitorare la scadenza dei certificati (alert a 30, 14, 7 giorni). Supportare molteplici certificati contemporaneamente durante la transizione (l'IdP aggiunge il nuovo certificato prima di rimuovere il vecchio). Il SP deve validare contro tutti i certificati configurati.

### 18. "Invalid Redirect URI" durante l'Autorizzazione

**Diagnosi**: l'Authorization Server rifiuta la richiesta perché il `redirect_uri` non corrisponde a quelli registrati.

**Soluzione**: il `redirect_uri` deve corrispondere **esattamente** (case-sensitive, incluso trailing slash, schema https). Registrare tutti gli ambienti: `https://app.com/auth/callback`, `https://staging.app.com/auth/callback`, `http://localhost:3000/auth/callback` (solo dev).

### 19. Token Exchange Restituisce "invalid_client"

**Diagnosi**: le credenziali del client sono rifiutate durante lo scambio del codice.

**Soluzione**: verificare `client_id` e `client_secret`. Controllare il metodo di autenticazione del client: alcuni IdP richiedono `client_secret_basic` (credenziali in header Authorization come Basic auth) anziché `client_secret_post` (credenziali nel body). Verificare nella discovery del provider il campo `token_endpoint_auth_methods_supported`.

### 20. Prestazioni Degradate con Validazione JWT

**Diagnosi**: ogni richiesta API valida il JWT scaricando il JWKS dall'IdP, causando latenza.

**Soluzione**: cacheare il JWKS localmente con TTL di 1 ora. Refreshare solo quando si incontra un `kid` sconosciuto (indica rotazione). Non scaricare il JWKS ad ogni richiesta — è un pattern anti-performante e potrebbe essere rate-limited dall'IdP.

### 21. SAML Response con Encoding Errato

**Diagnosi**: la SAML Response ricevuta dal browser non è parsificabile, errore di decoding.

**Soluzione**: la SAML Response viaggia come form POST base64-encoded. Verificare che il middleware web non tronchi il payload (limiti di dimensione del body POST). Aumentare il limite a almeno 100 KB per il body dell'endpoint ACS.

### 22. WebAuthn "NotAllowedError" nel Browser

**Diagnosi**: il browser rifiuta la cerimonia WebAuthn con NotAllowedError.

**Soluzione**: cause possibili: l'`rp_id` non corrisponde al dominio corrente (deve essere il dominio effettivo o un suffisso), l'utente ha rifiutato il prompt del dispositivo, timeout della cerimonia. Verificare che il sito sia servito via HTTPS (WebAuthn richiede un contesto sicuro).

---

## FAQ — Domande Frequenti

### 1. Qual è la differenza pratica tra OAuth 2.0, OIDC e SAML 2.0?

OAuth 2.0 è un protocollo di **autorizzazione**: permette a un'applicazione di accedere a risorse per conto dell'utente (es. leggere le email di Google). OIDC è un layer di **autenticazione** costruito sopra OAuth 2.0: conferma l'identità dell'utente con un ID Token standardizzato. SAML 2.0 è un protocollo enterprise che combina autenticazione e autorizzazione in formato XML. Nella pratica SaaS: OIDC per integrazioni moderne e social login, SAML per clienti enterprise con IdP già configurato.

### 2. Devo supportare sia SAML che OIDC nel mio SaaS?

Sì, se intendi vendere a clienti enterprise. SAML è il protocollo più richiesto dai dipartimenti IT delle grandi aziende (configurazioni esistenti, compliance). OIDC è più semplice da implementare e preferito per integrazioni moderne. Supportare entrambi copre la quasi totalità dei casi d'uso. Alternative: usare un servizio come WorkOS o Stytch che astraggono entrambi i protocolli.

### 3. Devo implementare l'autenticazione da zero o usare un servizio?

Dipende dal prodotto. Per la maggior parte dei SaaS: usa un servizio (Auth0, Clerk, WorkOS, Stytch). Il costo del servizio è nettamente inferiore al costo di sviluppo, manutenzione, e rischio di sicurezza di un'implementazione custom. Implementazione custom è giustificata quando: il volume di utenti è enorme (costo per MAU insostenibile), requisiti di data residency impediscono l'uso di servizi terzi, o l'autenticazione è il core business.

### 4. Come gestisco il "login with email" quando il dominio è configurato per SSO?

Quando un dominio email (es. `@acme.com`) è configurato per SSO, l'utente deve essere reindirizzato automaticamente al flusso SSO. Pattern: l'utente inserisce l'email, il backend verifica se il dominio ha una configurazione SSO attiva, e reindirizza al flusso appropriato (SAML o OIDC). Opzione "forced SSO": disabilitare completamente il login con password per quel dominio.

### 5. Come gestisco la registrazione di un utente che arriva tramite SSO per la prima volta?

Due approcci: **JIT (Just-In-Time) provisioning** — l'utente viene creato automaticamente al primo login SSO, con attributi estratti dall'ID Token o dall'asserzione SAML. **SCIM provisioning** — l'utente viene pre-creato dall'IdP prima del primo login. JIT è più semplice da implementare, SCIM offre più controllo (gruppi, ruoli, deprovisioning automatico).

### 6. Quanto è sicuro salvare i token JWT in localStorage?

Non sicuro. localStorage è accessibile da qualsiasi script JavaScript nella pagina (XSS). Un attaccante che inietta script nella pagina può rubare i token. Alternative sicure: **server-side session** con cookie HttpOnly (raccomandato), **in-memory** (variabili JS — persi al refresh della pagina), **BFF (Backend-for-Frontend)** pattern dove il backend gestisce i token.

### 7. Cosa succede se il refresh token viene rubato?

Se il refresh token viene rubato, l'attaccante può ottenere nuovi access token fino alla scadenza o revoca del refresh token. Mitigazioni: **token rotation** (ogni uso emette un nuovo refresh token e invalida il precedente — un doppio uso indica compromissione), **token binding** (legare il token a un device fingerprint), **short-lived refresh token** con ri-autenticazione periodica.

### 8. Come implemento il logout SSO?

Per OIDC: usare il **RP-Initiated Logout** (redirect al `end_session_endpoint` dell'IdP con `id_token_hint` e `post_logout_redirect_uri`). Per SAML: implementare il **Single Logout (SLO)** — il SP invia un LogoutRequest all'IdP, che a sua volta notifica tutti gli altri SP. Attenzione: SLO in SAML è notoriamente fragile nella pratica — se un SP non risponde, l'intero flusso si blocca. Alternativa pragmatica: session timeout breve + revoca dei token.

### 9. SCIM è obbligatorio per clienti enterprise?

Non strettamente obbligatorio, ma fortemente consigliato. Senza SCIM, l'admin IT deve creare/disabilitare manualmente gli utenti nel SaaS — un pain point significativo con 500+ utenti. SCIM è spesso nel checklist degli audit di sicurezza (SOC 2 Type II). Offrire SCIM differenzia il prodotto e accelera il ciclo di vendita.

### 10. Come gestisco i passkeys in un contesto multi-dispositivo?

I passkeys sincronizzati (iCloud Keychain, Google Password Manager) risolvono il problema multi-dispositivo per consumer. Per enterprise: le security key hardware (YubiKey) richiedono registrazione su ogni dispositivo. Best practice: permettere la registrazione di molteplici credenziali WebAuthn per utente, offrire TOTP come fallback, fornire backup codes per emergenze.

### 11. Un utente può avere sia login con password che SSO?

Sì, tecnicamente è possibile. Ma per sicurezza enterprise, quando SSO è configurato per un dominio, il login con password dovrebbe essere disabilitato (forced SSO). Motivo: l'IT vuole che tutti gli utenti passino attraverso l'IdP aziendale per applicare policy di sicurezza (MFA, conditional access, monitoraggio). Eccezione: account "break glass" (admin di emergenza) con password forte e MFA indipendente.

### 12. Come gestisco gli ambienti (dev, staging, produzione) con SSO?

Ogni ambiente dovrebbe avere una propria registrazione client nell'IdP. Non condividere `client_id`/`client_secret` tra ambienti. Per sviluppo locale: registrare `http://localhost:3000/auth/callback` come redirect URI nell'IdP (molti IdP lo permettono per ambienti dev). Per testing automatizzato: usare un IdP mock (es. Dex, mock SAML IdP) invece dell'IdP reale.

### 13. Come monitoro la salute dell'integrazione SSO?

Metriche chiave: tasso di login SSO riusciti vs. falliti, latenza del token exchange, errori SCIM (provisioning falliti), certificati in scadenza, token refresh failure rate. Implementare alerting su: spike di login falliti (possibile attacco o misconfiguration), certificato a 14 giorni dalla scadenza, SCIM failure rate > 5%.

### 14. Come gestisco il cambio di IdP da parte di un cliente?

Scenario: il cliente migra da Okta ad Azure AD. L'utente `sub` cambia (diverso IdP). Approccio: supportare un periodo di transizione dove entrambe le configurazioni IdP sono attive per lo stesso tenant. Il matching utente durante la migrazione si basa sull'email (unico attributo stabile). Dopo la migrazione, aggiornare il `sub` e l'`iss` dell'utente e rimuovere la vecchia configurazione.

### 15. Quali sono i requisiti di compliance che impattano l'SSO?

**SOC 2 Type II**: richiede centralizzazione dell'autenticazione, MFA, audit log degli accessi, provisioning/deprovisioning tempestivo. **ISO 27001**: richiede politiche di accesso, autenticazione forte, revisione periodica degli accessi. **HIPAA**: richiede autenticazione unica, audit trail, timeout di sessione, MFA. **GDPR**: impatta la gestione dei dati utente durante il provisioning SCIM (data minimization, right to deletion).

### 16. Qual è la latenza accettabile per un flusso SSO?

Il flusso completo (redirect all'IdP, login, redirect al SP, token exchange) dovrebbe completarsi in meno di 3-5 secondi per un utente già autenticato nell'IdP (sessione attiva). Per un primo login (senza sessione IdP), 5-10 secondi è accettabile. La componente controllabile dal SaaS (token exchange, creazione sessione) dovrebbe essere sotto i 200ms.

---

## Riferimenti

- RFC 6749: The OAuth 2.0 Authorization Framework
- RFC 7636: Proof Key for Code Exchange (PKCE) by OAuth Public Clients
- RFC 7519: JSON Web Token (JWT)
- RFC 7517: JSON Web Key (JWK)
- RFC 7009: OAuth 2.0 Token Revocation
- RFC 8628: OAuth 2.0 Device Authorization Grant
- RFC 7644: System for Cross-domain Identity Management (SCIM) Protocol
- RFC 7643: SCIM Core Schema
- OpenID Connect Core 1.0 Specification
- OpenID Connect Discovery 1.0
- OpenID Connect RP-Initiated Logout 1.0
- OASIS SAML 2.0 Technical Overview
- W3C Web Authentication (WebAuthn) Level 2
- FIDO2: Client to Authenticator Protocol (CTAP)
- OAuth 2.0 Security Best Current Practice (draft-ietf-oauth-security-topics)
- OAuth 2.1 Authorization Framework (draft-ietf-oauth-v2-1)
- Auth0 Documentation: https://auth0.com/docs
- Okta Developer Documentation: https://developer.okta.com
- WorkOS Documentation: https://workos.com/docs — SSO as a Service per SaaS
- Microsoft Identity Platform Documentation — Azure AD/Entra ID
- KeyCloak Documentation: https://www.keycloak.org/documentation
- "OAuth 2 in Action" — Justin Richer, Antonio Sanso (Manning)
- sso.tax — Database of SSO pricing across SaaS vendors
