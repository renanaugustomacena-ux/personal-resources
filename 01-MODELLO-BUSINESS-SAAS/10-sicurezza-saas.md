# Sicurezza SaaS — Guida Completa

## Indice

- [Panoramica](#panoramica)
- [Modello di Sicurezza SaaS](#modello-di-sicurezza-saas)
- [Architettura di Sicurezza: Zero Trust](#architettura-di-sicurezza-zero-trust)
- [Autenticazione e Autorizzazione](#autenticazione-e-autorizzazione)
- [Isolamento dei Tenant](#isolamento-dei-tenant)
- [Crittografia e Protezione Dati](#crittografia-e-protezione-dati)
- [Sicurezza delle API](#sicurezza-delle-api)
- [Sicurezza Applicativa (OWASP)](#sicurezza-applicativa-owasp)
- [Sicurezza Infrastrutturale](#sicurezza-infrastrutturale)
- [Gestione delle Vulnerabilità](#gestione-delle-vulnerabilita)
- [Sicurezza della Supply Chain](#sicurezza-della-supply-chain)
- [Security Monitoring e SIEM](#security-monitoring-e-siem)
- [Penetration Testing](#penetration-testing)
- [Incident Response](#incident-response)
- [SOC 2 Type II — Preparazione all'Audit](#soc-2-type-ii--preparazione-allaudit)
- [ISO 27001 — Roadmap di Implementazione](#iso-27001--roadmap-di-implementazione)
- [Matrice di Compliance per Standard](#matrice-di-compliance-per-standard)
- [Security per Enterprise Sales](#security-per-enterprise-sales)
- [Best Practices](#best-practices)
- [Checklist di Hardening Step-by-Step](#checklist-di-hardening-step-by-step)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)

---

## Panoramica

La sicurezza in un SaaS non è un feature — è un prerequisito. I clienti affidano i loro dati a un servizio terzo, e un singolo breach può distruggere la reputazione, causare sanzioni legali e perdere clienti in massa. La sicurezza SaaS copre: autenticazione/autorizzazione, crittografia, sicurezza applicativa (OWASP), sicurezza infrastrutturale, monitoring, incident response, e compliance. Per vendere all'enterprise, la sicurezza deve essere dimostrabile (SOC 2, ISO 27001, penetration test).

### Perché la Sicurezza SaaS è Diversa

Un'applicazione SaaS presenta sfide di sicurezza uniche rispetto al software tradizionale on-premise:

1. **Multi-tenancy**: dati di centinaia o migliaia di clienti coesistono sulla stessa infrastruttura. Un errore di isolamento espone i dati di tutti.
2. **Superficie di attacco espansa**: le API sono pubbliche per design, i dati transitano su Internet, gli utenti accedono da dispositivi non controllati.
3. **Aggiornamento continuo**: il deployment frequente (CI/CD) introduce nuove vulnerabilità a ogni release se la sicurezza non è integrata nel processo.
4. **Compliance multi-giurisdizionale**: clienti in EU (GDPR), USA (SOC 2, HIPAA, CCPA), Asia (PDPA, PIPL) richiedono conformità simultanea.
5. **Trust asimmetrico**: il cliente non può verificare direttamente la sicurezza. Deve fidarsi di certificazioni, audit e trasparenza del provider.

### Costo del Breach

Il costo medio di un data breach nel 2025 supera i $4.8M (fonte: IBM Cost of a Data Breach Report). Per un SaaS, il danno è amplificato:

- **Churn immediato**: clienti enterprise rescindono il contratto
- **Sanzioni regolamentari**: GDPR prevede fino al 4% del fatturato annuo globale
- **Costi legali**: class action, notifiche obbligatorie, consulenze forensi
- **Danno reputazionale**: tempo di recupero 2-5 anni
- **Costi operativi**: incident response, remediation, security improvements forzati

---

## Modello di Sicurezza SaaS

### Defense in Depth

La sicurezza si implementa a strati: se un layer viene compromesso, il successivo protegge.

```
Layer 1: PERIMETRO (WAF, DDoS protection, rate limiting)
  ↓
Layer 2: RETE (VPC, security group, network segmentation)
  ↓
Layer 3: APPLICAZIONE (input validation, output encoding, CSRF/XSS protection)
  ↓
Layer 4: AUTENTICAZIONE (MFA, session management, OAuth)
  ↓
Layer 5: AUTORIZZAZIONE (RBAC, tenant isolation, principle of least privilege)
  ↓
Layer 6: DATI (encryption at rest, encryption in transit, key management)
  ↓
Layer 7: MONITORING (audit log, SIEM, anomaly detection)
```

Ogni layer è indipendente: la compromissione del WAF non significa accesso ai dati, perché il layer di autenticazione, autorizzazione e crittografia opera indipendentemente.

### Principi di Design Sicuro

1. **Least Privilege**: ogni componente ha solo i permessi minimi necessari. Un microservizio che legge ordini non ha accesso in scrittura al database utenti.
2. **Fail Secure**: in caso di errore, il sistema nega l'accesso. Se il servizio di autorizzazione è down, l'accesso è bloccato, non aperto.
3. **Defense in Depth**: mai affidarsi a un singolo controllo. La validazione avviene sia lato client che server, sia a livello applicativo che database.
4. **Separation of Duties**: chi sviluppa non ha accesso diretto alla produzione. Chi opera non può modificare il codice.
5. **Security by Default**: le configurazioni di default sono sicure. L'utente deve esplicitamente scegliere di ridurre la sicurezza (opt-out), non di aumentarla (opt-in).

### Shared Responsibility Model

Nel cloud, la sicurezza è condivisa:
- **Cloud provider** (AWS/GCP/Azure): sicurezza dell'infrastruttura fisica, hypervisor, rete base
- **SaaS provider**: sicurezza dell'applicazione, dei dati, della configurazione cloud, degli accessi
- **Cliente**: sicurezza dei propri account (password, MFA), gestione dei permessi, dati inseriti

```
Responsabilità dettagliata:

Cloud Provider          SaaS Provider               Cliente
─────────────────────── ─────────────────────────── ──────────────────────
Data center fisico      Configurazione IAM cloud    Password sicure
Hypervisor/host OS      Patch OS/runtime            MFA abilitato
Rete fisica             Encryption key management   Gestione ruoli utenti
Hardware crypto (HSM)   Application code security   Classificazione dati
Certificazioni (FedRAMP)Network segmentation        Accesso dispositivi
DDoS base protection    Container/workload security Policy interne
                        API security                Training dipendenti
                        Logging/monitoring          Incident reporting
                        Backup/DR                   Compliance interna
                        Compliance (SOC2, ISO)      Contratti/DPA firmati
```

### Threat Model per SaaS

Il threat modeling è un processo strutturato per identificare minacce prima che diventino vulnerabilità. Il framework STRIDE è il più usato:

| Categoria | Descrizione | Esempio SaaS |
|-----------|-------------|--------------|
| **S**poofing | Impersonare un'identità | Furto di sessione JWT, phishing per credenziali admin |
| **T**ampering | Modificare dati in transito o a riposo | Manipolazione di parametri API, alterazione di log |
| **R**epudiation | Negare un'azione eseguita | Utente nega di aver cancellato dati senza audit log |
| **I**nformation Disclosure | Accesso a dati non autorizzati | Cross-tenant data leak, error message con stack trace |
| **D**enial of Service | Rendere il servizio indisponibile | DDoS su API, query pesanti che saturano il DB |
| **E**levation of Privilege | Ottenere permessi superiori | IDOR per diventare admin, privilege escalation via API |

Per ogni componente del sistema (API gateway, database, storage, cache, coda messaggi), mappare le minacce STRIDE e definire le contromisure.

---

## Architettura di Sicurezza: Zero Trust

### Principi Zero Trust

Il modello Zero Trust (ZTA, NIST SP 800-207) elimina il concetto di rete "fidata". Ogni richiesta è verificata, indipendentemente dalla sua origine.

I cinque pilastri:

1. **Identity**: ogni accesso è autenticato e autorizzato. Nessun utente o servizio è "trusted" per default.
2. **Device**: lo stato del dispositivo (patch level, compliance, posture) è verificato prima di concedere accesso.
3. **Network**: micro-segmentazione, nessuna fiducia implicita basata sulla posizione di rete.
4. **Application**: ogni applicazione e workload è autenticata, e la comunicazione è crittografata.
5. **Data**: i dati sono classificati, protetti e l'accesso è loggato.

### Implementazione Zero Trust per SaaS

```
Architettura Zero Trust - Flusso di accesso:

[Utente] → [Identity Provider] → [Policy Engine] → [Policy Enforcement Point]
                  ↑                     ↑                       ↓
            [MFA/Device Check]    [Context Signals]     [Risorsa Protetta]
                                       ↑
                              ┌────────┼────────┐
                              │        │        │
                          [Geo IP] [Behavior] [Risk Score]
```

**Componenti chiave:**

1. **Policy Decision Point (PDP)**: il cervello. Valuta ogni richiesta di accesso considerando identità, contesto, rischio, policy. Esempio: Open Policy Agent (OPA), AWS Verified Access.

2. **Policy Enforcement Point (PEP)**: il gateway. Blocca o permette l'accesso basandosi sulla decisione del PDP. Esempio: API gateway con middleware di autorizzazione, service mesh sidecar (Envoy + Istio).

3. **Context Engine**: raccoglie segnali per il calcolo del rischio:
   - Geolocalizzazione IP (accesso dal solito Paese?)
   - Device posture (dispositivo aziendale o BYOD?)
   - Comportamento utente (orario, frequenza, pattern anomali)
   - Threat intelligence feed (IP in blacklist?)

4. **Continuous Verification**: l'autenticazione non è un evento singolo. Le sessioni sono rivalutate continuamente. Se il rischio aumenta durante la sessione (cambio IP, comportamento anomalo), viene richiesta ri-autenticazione.

### Service-to-Service Zero Trust

In un'architettura microservizi, anche la comunicazione interna segue Zero Trust:

- **mTLS (mutual TLS)**: ogni servizio ha un certificato client. La comunicazione è autenticata in entrambe le direzioni.
- **Service Identity**: ogni microservizio ha un'identità (SPIFFE/SPIRE). I permessi sono definiti per identità, non per IP.
- **Service Mesh**: Istio o Linkerd gestiscono mTLS, policy e osservabilità senza modificare il codice applicativo.

```
Esempio mTLS in Kubernetes con Istio:

apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT

---
# AuthorizationPolicy: solo il servizio "orders" può chiamare "payments"
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: payments-access
  namespace: production
spec:
  selector:
    matchLabels:
      app: payments
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/orders-service"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/charges"]
```

---

## Autenticazione e Autorizzazione

### Autenticazione

**Password policy**: minimo 12 caratteri, no restrizioni artificiali (no "deve avere maiuscola + numero + simbolo" — favorisce password deboli come "Password1!"). Usare un password strength meter (zxcvbn).

**Multi-Factor Authentication (MFA)**: obbligatoria per admin, fortemente consigliata per tutti. Metodi in ordine di sicurezza:
1. Hardware key (YubiKey, FIDO2) — più sicuro
2. Authenticator app (Google Authenticator, Authy) — buono
3. SMS OTP — meglio di niente, ma vulnerabile a SIM swap

**Single Sign-On (SSO)**: per clienti enterprise, SSO è un requisito non negoziabile. Protocolli: SAML 2.0 (standard enterprise), OIDC (moderno, più semplice). Implementare con un identity provider (Okta, Azure AD, Auth0).

**Session management**: token JWT con scadenza breve (15-60 minuti) + refresh token con scadenza più lunga (7-30 giorni). Invalidare le sessioni al cambio password. Limite sessioni concorrenti per account.

### Protocolli di Autenticazione in Dettaglio

#### OAuth 2.0

OAuth 2.0 (RFC 6749) è il framework di autorizzazione standard. Non è un protocollo di autenticazione (per quello serve OIDC sopra OAuth 2.0).

**Grant Types per SaaS:**

| Grant Type | Uso | Sicurezza |
|------------|-----|-----------|
| Authorization Code + PKCE | Applicazioni web e mobile | Massima. PKCE previene code interception |
| Client Credentials | Comunicazione server-to-server | Alta. Secret condiviso, nessun utente coinvolto |
| Device Code | Dispositivi senza browser (IoT, TV) | Media. Polling-based |
| ~~Implicit~~ | ~~SPA legacy~~ | **Deprecato. Non usare.** |
| ~~Resource Owner Password~~ | ~~Legacy~~ | **Deprecato. Non usare.** |

```
Flusso Authorization Code + PKCE:

1. Client genera code_verifier (random 43-128 char)
2. Client calcola code_challenge = SHA256(code_verifier)
3. Client → Authorization Server:
   GET /authorize?
     response_type=code&
     client_id=CLIENT_ID&
     redirect_uri=REDIRECT_URI&
     scope=openid profile email&
     state=RANDOM_STATE&
     code_challenge=CODE_CHALLENGE&
     code_challenge_method=S256

4. Utente si autentica e autorizza
5. Authorization Server → Client: redirect con authorization code
6. Client → Authorization Server:
   POST /token
     grant_type=authorization_code&
     code=AUTH_CODE&
     redirect_uri=REDIRECT_URI&
     client_id=CLIENT_ID&
     code_verifier=CODE_VERIFIER

7. Authorization Server verifica code_verifier contro code_challenge
8. Authorization Server → Client: access_token + id_token + refresh_token
```

#### OpenID Connect (OIDC)

OIDC è un layer di identità sopra OAuth 2.0. Aggiunge il concetto di id_token (JWT che contiene informazioni sull'utente autenticato).

**Claims standard nel id_token:**
- `sub`: identificativo unico dell'utente
- `email`: indirizzo email
- `email_verified`: se l'email è verificata
- `name`: nome completo
- `iss`: issuer (chi ha emesso il token)
- `aud`: audience (per chi è il token)
- `exp`: scadenza
- `iat`: issued at
- `nonce`: per prevenire replay attack

**Discovery endpoint**: `/.well-known/openid-configuration` espone tutti gli endpoint (authorize, token, userinfo, jwks) e le capability del provider.

#### SAML 2.0

SAML (Security Assertion Markup Language) 2.0 è lo standard enterprise per il SSO. Basato su XML, più complesso di OIDC ma ancora dominante nelle grandi organizzazioni.

```
Flusso SAML SP-Initiated:

1. Utente accede a SaaS (Service Provider)
2. SaaS genera AuthnRequest XML
3. SaaS redirect utente a IdP con AuthnRequest (via HTTP-Redirect o HTTP-POST)
4. IdP autentica l'utente (login form, MFA)
5. IdP genera SAML Assertion (XML firmato digitalmente)
6. IdP redirect utente a SaaS con SAML Response (HTTP-POST)
7. SaaS verifica la firma della SAML Assertion
8. SaaS estrae attributi (email, ruolo, gruppi) dalla Assertion
9. SaaS crea sessione locale

Componenti della SAML Assertion:
- Subject: chi è l'utente (NameID)
- Conditions: validità temporale, audience restriction
- AuthnStatement: come l'utente si è autenticato
- AttributeStatement: attributi dell'utente (email, groups, role)
```

**Considerazioni di sicurezza SAML:**
- Validare sempre la firma XML (XML Signature Wrapping attack è un attacco noto)
- Verificare `Destination`, `Audience`, `InResponseTo`
- Usare `NotOnOrAfter` per prevenire replay
- Canonicalizzazione XML (Exclusive Canonical XML)

#### Passwordless Authentication

L'autenticazione senza password elimina il vettore di attacco più comune (credential theft).

**Metodi:**

1. **WebAuthn/FIDO2**: standard W3C. L'utente si autentica con biometria (impronta, face ID) o hardware key. Le credenziali sono legate al dominio (phishing-resistant). Il server non vede mai un segreto — solo challenge/response con crittografia asimmetrica.

2. **Magic Link**: email con link contenente token one-time. Semplice ma dipende dalla sicurezza dell'email.

3. **Passkey**: evoluzione di WebAuthn. Sincronizzato tra dispositivi via iCloud Keychain / Google Password Manager. Combinano sicurezza di FIDO2 con usabilità cross-device.

```
Flusso WebAuthn Registration:

1. Server genera challenge (random bytes)
2. Browser chiama navigator.credentials.create({
     publicKey: {
       challenge: challenge,
       rp: { name: "SaaS App", id: "app.example.com" },
       user: { id: userId, name: "user@example.com" },
       pubKeyCredParams: [{ type: "public-key", alg: -7 }],  // ES256
       authenticatorSelection: {
         authenticatorAttachment: "platform",
         residentKey: "required",
         userVerification: "required"
       }
     }
   })
3. Authenticator (biometria/pin) verifica l'utente
4. Authenticator genera keypair (privata rimane nel device)
5. Browser restituisce: credentialId + publicKey + attestation
6. Server salva credentialId + publicKey associati all'utente

Flusso WebAuthn Authentication:

1. Server genera challenge
2. Browser chiama navigator.credentials.get({ publicKey: { challenge } })
3. Authenticator firma il challenge con la chiave privata
4. Server verifica la firma con la chiave pubblica salvata
```

### Autorizzazione

**RBAC (Role-Based Access Control)**: il modello più comune. Definire ruoli (Owner, Admin, Member, Viewer) con permessi specifici.

```
Esempio RBAC per un project management SaaS:

  Owner:  tutto (billing, delete workspace, manage members)
  Admin:  manage members, create/edit/delete projects
  Member: create/edit projects, view all
  Viewer: view only (no edit, no create)

  Permessi per risorsa:
    Workspace: owner, admin
    Projects:  owner, admin, member (CRUD), viewer (R)
    Billing:   owner only
    Members:   owner, admin
```

#### Pattern di Implementazione RBAC

```
Schema database per RBAC:

users
├── id (UUID)
├── email
├── tenant_id (FK → tenants.id)
└── created_at

roles
├── id (UUID)
├── name (VARCHAR) -- 'owner', 'admin', 'member', 'viewer'
├── tenant_id (FK → tenants.id)
└── description

permissions
├── id (UUID)
├── resource (VARCHAR) -- 'workspace', 'project', 'billing'
├── action (VARCHAR) -- 'create', 'read', 'update', 'delete'
└── description

role_permissions
├── role_id (FK → roles.id)
└── permission_id (FK → permissions.id)

user_roles
├── user_id (FK → users.id)
├── role_id (FK → roles.id)
└── scope_id (UUID) -- opzionale: permessi per risorsa specifica
```

```
Middleware di autorizzazione (pseudocodice):

function authorize(user, resource, action):
    // 1. Recupera i ruoli dell'utente per il tenant corrente
    roles = getUserRoles(user.id, user.tenant_id)

    // 2. Per ogni ruolo, verifica se il permesso è concesso
    for role in roles:
        permissions = getRolePermissions(role.id)
        if permissions.any(p => p.resource == resource && p.action == action):
            return ALLOW

    // 3. Nessun ruolo ha il permesso → nega
    return DENY
```

**ABAC (Attribute-Based Access Control)**: per scenari complessi, i permessi dipendono da attributi (ruolo + dipartimento + progetto + orario). Più flessibile ma più complesso.

#### Pattern di Implementazione ABAC

ABAC utilizza policy basate su attributi dell'utente, della risorsa, dell'azione e dell'ambiente.

```
Struttura di una policy ABAC:

Policy:
  Subject Attributes:
    - role: "developer"
    - department: "engineering"
    - clearance_level: 3
  Resource Attributes:
    - type: "document"
    - classification: "confidential"
    - owner_department: "engineering"
  Action: "read"
  Environment Attributes:
    - time: "business_hours" (09:00-18:00)
    - location: "corporate_network"
    - device_compliance: true
  Decision: ALLOW

Esempio con Open Policy Agent (OPA) - Rego:

package authz

default allow = false

allow {
    input.user.role == "developer"
    input.resource.classification != "top_secret"
    input.resource.owner_department == input.user.department
    is_business_hours
    input.environment.device_compliant == true
}

is_business_hours {
    hour := time.clock(time.now_ns())[0]
    hour >= 9
    hour < 18
}
```

#### ReBAC (Relationship-Based Access Control)

ReBAC modella i permessi come relazioni in un grafo. Ispirato a Google Zanzibar (paper 2019), è il modello dietro sistemi come SpiceDB, OpenFGA, Ory Keto.

```
Modello ReBAC - Schema delle relazioni:

type user {}

type organization {
    relation member: user
    relation admin: user
    permission view = member + admin
    permission manage = admin
}

type project {
    relation organization: organization
    relation owner: user
    relation editor: user
    relation viewer: user
    permission view = viewer + editor + owner + organization->member
    permission edit = editor + owner + organization->admin
    permission delete = owner + organization->admin
}

type document {
    relation project: project
    relation creator: user
    permission view = creator + project->view
    permission edit = creator + project->edit
    permission delete = project->delete
}

Esempio di check:
  "L'utente U può editare il documento D?"

  1. U è il creator di D? → Sì → ALLOW
  2. U è editor/owner del project P di D? → Sì → ALLOW
  3. U è admin dell'organization O del project P di D? → Sì → ALLOW
  4. Nessuna relazione trovata → DENY
```

**Vantaggi di ReBAC rispetto a RBAC/ABAC:**
- Modella naturalmente gerarchie e condivisione (Google Drive, Notion)
- Performance: lookup O(1) con grafo materializzato
- Consistenza: ZookieDB/SpiceDB supportano consistency token (Zookie)
- Scalabilità: Google Zanzibar gestisce >10M check/sec

**Tenant isolation**: CRITICO nel SaaS multi-tenant. Ogni query, ogni API call deve verificare che l'utente acceda solo ai dati del proprio tenant. Row Level Security (PostgreSQL), middleware di tenant validation, test automatici per cross-tenant access.

---

## Isolamento dei Tenant

L'isolamento dei tenant è il requisito di sicurezza più critico in un SaaS multi-tenant. Un fallimento qui espone i dati di un cliente ad un altro.

### Strategie di Isolamento

#### Isolamento a Livello di Dati

**1. Database Separato per Tenant (Silo)**

```
Ogni tenant ha il proprio database:

tenant_acme    → database PostgreSQL dedicato
tenant_globex  → database PostgreSQL dedicato
tenant_initech → database PostgreSQL dedicato

Pro:
- Isolamento massimo (nessun rischio di cross-tenant query)
- Backup/restore per singolo tenant
- Performance prevedibili (no noisy neighbor)
- Compliance facilitata (dati in regione specifica)

Contro:
- Costo elevato (un database per tenant)
- Complessità operativa (migrazione schema su N database)
- Non scala oltre ~1000 tenant
- Connection pooling complesso
```

**2. Schema Separato per Tenant (Bridge)**

```
Stesso database, schema diverso per tenant:

database: saas_production
  ├── schema: tenant_acme    (tables: users, projects, documents)
  ├── schema: tenant_globex  (tables: users, projects, documents)
  └── schema: tenant_initech (tables: users, projects, documents)

Pro:
- Buon isolamento (schema-level access control)
- Meno costoso del silo completo
- Facilita backup per tenant

Contro:
- Migrazione schema su N schemi
- Limite pratico ~5000 schemi in PostgreSQL
- Connection handling più complesso
```

**3. Tabelle Condivise con tenant_id (Pool)**

```
Stesso database, stesse tabelle, colonna tenant_id:

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indice su tenant_id per performance
CREATE INDEX idx_projects_tenant ON projects(tenant_id);

-- Row Level Security (CRITICO)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON projects
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- Ogni connessione imposta il tenant corrente
SET app.current_tenant = 'uuid-del-tenant';

Pro:
- Scala a milioni di tenant
- Schema migration singola
- Operativamente semplice

Contro:
- Rischio cross-tenant se RLS mal configurato
- Noisy neighbor (tenant grande impatta gli altri)
- Backup per singolo tenant complesso
```

#### Isolamento a Livello di Compute

```
Strategie di isolamento compute:

1. Container Condiviso (Pool):
   Stessi container servono tutti i tenant.
   Rischio: side-channel, memory leak cross-tenant.
   Mitigazione: tenant context isolato per request.

2. Container per Tenant (Bridge):
   Ogni tenant ha container dedicati.
   Pro: isolamento di risorse, limiti CPU/RAM per tenant.
   Contro: overhead di gestione, scaling complesso.

3. Cluster Kubernetes per Tenant (Silo):
   Tenant critici (enterprise) hanno cluster dedicati.
   Pro: massimo isolamento, compliance.
   Contro: costo elevato, complessità operativa.

Pattern ibrido raccomandato:
   - SMB tenant: pool condiviso con RLS e limiti applicativi
   - Enterprise tenant: namespace Kubernetes dedicato con ResourceQuota
   - Regulated tenant: cluster o account cloud separato
```

#### Isolamento a Livello di Rete

```
Segmentazione di rete per tenant isolation:

1. Namespace Kubernetes con NetworkPolicy:

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tenant-isolation
  namespace: tenant-acme
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          tenant: acme
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          tenant: acme
    - namespaceSelector:
        matchLabels:
          role: shared-services

2. VPC Peering per tenant enterprise:
   Ogni tenant enterprise ha il proprio VPC.
   Comunicazione via VPC peering o PrivateLink.
   Il SaaS espone endpoint privati, non Internet-facing.

3. Security Group granulari:
   Database accessibile solo dal application layer.
   Application layer accessibile solo dal load balancer.
   Management plane accessibile solo via bastion/VPN.
```

### Test Automatici per Tenant Isolation

```
Test di isolamento (eseguire in CI/CD):

// test: cross-tenant data access deve fallire
test('tenant A non può accedere ai dati di tenant B', async () => {
    // Arrange: crea dati per tenant B
    const tenantB_project = await createProject({
        tenant_id: TENANT_B_ID,
        name: 'Secret Project'
    });

    // Act: utente di tenant A prova ad accedere
    const response = await api.get(`/projects/${tenantB_project.id}`, {
        headers: { Authorization: `Bearer ${TENANT_A_TOKEN}` }
    });

    // Assert: accesso negato
    expect(response.status).toBe(404); // 404, non 403 (non rivelare esistenza)
});

// test: query SQL non leaka dati cross-tenant
test('RLS previene accesso cross-tenant a livello DB', async () => {
    // Imposta contesto tenant A
    await db.query("SET app.current_tenant = $1", [TENANT_A_ID]);

    // Query tutti i progetti
    const result = await db.query("SELECT * FROM projects");

    // Nessun progetto di tenant B deve apparire
    const crossTenantLeaks = result.rows.filter(
        r => r.tenant_id !== TENANT_A_ID
    );
    expect(crossTenantLeaks).toHaveLength(0);
});

// test: API listing non include risorse di altri tenant
test('list projects ritorna solo progetti del tenant corrente', async () => {
    const response = await api.get('/projects', {
        headers: { Authorization: `Bearer ${TENANT_A_TOKEN}` }
    });

    for (const project of response.data) {
        expect(project.tenant_id).toBe(TENANT_A_ID);
    }
});
```

---

## Crittografia e Protezione Dati

### Encryption in Transit

Tutto il traffico deve essere crittografato con TLS 1.2+ (idealmente TLS 1.3). HTTPS obbligatorio, HTTP redirect a HTTPS. HSTS header per prevenire downgrade attack.

Configurazione: disabilitare cipher suite deboli, usare certificati da CA riconosciute (Let's Encrypt per gratis, o certificati EV per enterprise trust). Verificare con SSL Labs (ssllabs.com).

#### TLS 1.3 in Dettaglio

TLS 1.3 (RFC 8446) è il protocollo corrente. Rispetto a TLS 1.2:
- **1-RTT handshake** (vs 2-RTT di TLS 1.2): connessione più veloce
- **0-RTT resumption**: connessioni successive ancora più veloci (con trade-off replay attack)
- **Cipher suite semplificate**: solo AEAD cipher (AES-GCM, ChaCha20-Poly1305)
- **Rimossi**: RSA key exchange, CBC mode, SHA-1, RC4, DES, 3DES, export cipher
- **Forward secrecy obbligatorio**: solo ECDHE/DHE key exchange

```
Cipher suite raccomandate per TLS 1.3:

TLS_AES_256_GCM_SHA384        (preferito)
TLS_CHACHA20_POLY1305_SHA256  (buono per mobile/CPU senza AES-NI)
TLS_AES_128_GCM_SHA256        (accettabile)

Configurazione Nginx:

ssl_protocols TLSv1.3 TLSv1.2;
ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers off;  # In TLS 1.3, il client sceglie
ssl_session_timeout 1d;
ssl_session_cache shared:MozSSL:10m;
ssl_session_tickets off;  # Disabilitare per forward secrecy
ssl_stapling on;
ssl_stapling_verify on;

add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

#### Certificate Management

```
Lifecycle dei certificati TLS:

1. PROVISIONING
   - Let's Encrypt (ACME protocol) per certificati gratuiti auto-rinnovabili
   - cert-manager in Kubernetes per gestione automatica
   - Wildcard cert per *.app.example.com (un cert per tutti i tenant)
   - Certificati EV per pagine di payment/trust

2. ROTATION
   - Let's Encrypt: ogni 90 giorni (automatico con certbot/cert-manager)
   - Certificati commerciali: ogni anno
   - Certificati interni (mTLS): ogni 24-72 ore (short-lived)

3. REVOCATION
   - OCSP stapling per verifica revoca in tempo reale
   - CRL (Certificate Revocation List) come fallback
   - Monitorare Certificate Transparency Log per certificati non autorizzati

4. MONITORING
   - Alert 30 giorni prima della scadenza
   - Alert se il certificato è stato emesso da CA non prevista
   - Verificare CT Log per certificati emessi per il dominio
```

### Encryption at Rest

I dati devono essere crittografati quando salvati:
- **Database**: encryption a livello di disco (AWS RDS encryption, Azure Transparent Data Encryption). AES-256.
- **File storage**: S3 server-side encryption (SSE-S3 o SSE-KMS).
- **Backup**: crittografati con chiave separata.

#### AES-256-GCM in Dettaglio

AES-256-GCM (Galois/Counter Mode) è lo standard per encryption at rest:

```
Proprietà di AES-256-GCM:

- Chiave: 256 bit (32 byte)
- IV/Nonce: 96 bit (12 byte) — DEVE essere unico per ogni operazione
- Authentication Tag: 128 bit (16 byte)
- Modalità: AEAD (Authenticated Encryption with Associated Data)
- Fornisce: confidenzialità + integrità + autenticità

Livelli di encryption:

1. Full Disk Encryption (FDE):
   - Trasparente per l'applicazione
   - Protegge da furto fisico del disco
   - NON protegge da accesso logico (se il sistema è acceso, i dati sono decifrati)
   - AWS: EBS encryption, RDS encryption
   - GCP: default encryption at rest (chiavi gestite da Google)

2. Column-Level Encryption:
   - Campi specifici cifrati a livello applicativo
   - Protegge anche da DBA non autorizzati
   - Performance impact: ogni read/write richiede encrypt/decrypt
   - Uso: SSN, numeri carta di credito, dati sanitari

3. Application-Level Encryption (ALE):
   - L'applicazione cifra prima di scrivere nel database
   - Massima protezione: il dato è cifrato ovunque transiti
   - Complessità: key management, search su dati cifrati (impossibile con encryption standard)
   - Soluzione per search: tokenizzazione + indice separato, o searchable encryption

Envelope Encryption (pattern raccomandato):

1. Generare DEK (Data Encryption Key) unica per ogni tenant/record
2. Cifrare i dati con DEK (AES-256-GCM)
3. Cifrare DEK con KEK (Key Encryption Key) dal KMS
4. Salvare: dati cifrati + DEK cifrata + IV + tag
5. Per decifrare: KMS decifra DEK → DEK decifra dati

Vantaggio: rotazione chiavi veloce (solo ri-cifrare le DEK, non tutti i dati)
```

### Key Management

Le chiavi di crittografia devono essere gestite in modo sicuro:
- **Cloud KMS** (AWS KMS, GCP Cloud KMS): servizio gestito, rotation automatica, audit log. Standard consigliato.
- **BYOK (Bring Your Own Key)**: il cliente enterprise fornisce la propria chiave. Più complesso ma richiesto da alcuni settori (finanza, sanità).
- **Key rotation**: automatica ogni 90-365 giorni.

#### KMS e HSM — Architettura

```
Gerarchia delle chiavi:

                    ┌─────────────┐
                    │   Root Key   │  ← Dentro HSM, mai esportabile
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────┴─────┐┌────┴─────┐┌────┴─────┐
        │  KEK Prod  ││ KEK Dev  ││ KEK DR   │  ← Key Encryption Keys
        └─────┬─────┘└────┬─────┘└────┬─────┘
              │           │           │
     ┌────────┼────┐      │           │
     │        │    │      │           │
   ┌─┴──┐ ┌──┴─┐┌─┴──┐ ┌─┴──┐     ┌─┴──┐
   │DEK1│ │DEK2││DEK3│ │DEK4│     │DEK5│     ← Data Encryption Keys
   └────┘ └────┘└────┘ └────┘     └────┘       (una per tenant o record)

HSM (Hardware Security Module):
- FIPS 140-2 Level 3 o superiore
- Root key generata e usata SOLO dentro l'HSM
- Operazioni crittografiche eseguite dentro l'HSM
- Tamper-evident: se aperto fisicamente, le chiavi vengono distrutte
- AWS CloudHSM, Azure Dedicated HSM, Thales Luna

Rotazione delle chiavi:
- Root Key: mai (o ogni 3-5 anni con cerimonia formale)
- KEK: ogni 1 anno (automatica via KMS)
- DEK: ogni 90 giorni o per ogni record (envelope encryption)
- La rotazione ri-cifra solo il layer successivo, non tutti i dati
```

#### BYOK e HYOK

```
BYOK (Bring Your Own Key):
1. Il cliente genera una chiave master nel proprio HSM
2. La chiave viene importata (wrappata) nel KMS del SaaS
3. Il SaaS usa la chiave del cliente come KEK per i dati di quel tenant
4. Il cliente può revocare la chiave → i suoi dati diventano inaccessibili
5. Implementazione: AWS KMS Custom Key Store, Azure Key Vault BYOK

HYOK (Hold Your Own Key):
- La chiave non lascia MAI l'infrastruttura del cliente
- Il SaaS chiama il KMS del cliente per ogni operazione di encryption/decryption
- Latenza elevata ma massimo controllo per il cliente
- Richiesto in settori altamente regolamentati (difesa, intelligence)
```

### Dati Sensibili

Classificare i dati per sensibilità:
- **PII** (Personally Identifiable Information): nome, email, indirizzo, telefono → encryption + access control
- **Sensitive PII**: SSN, carta di credito, dati sanitari → encryption forte + tokenizzazione + accesso ristretto
- **Credentials**: password (bcrypt/argon2 hash, MAI in chiaro), API key (hash + prefix visibile), token (encrypted)

### Classificazione e Governance dei Dati

```
Schema di classificazione a 4 livelli:

Livello 1 — PUBBLICO
  Esempi: pagine marketing, documentazione API pubblica, prezzi
  Controlli: integrità (no tampering), disponibilità
  Encryption: in transit (TLS)

Livello 2 — INTERNO
  Esempi: metriche aggregate, log operativi, configurazioni non sensibili
  Controlli: accesso autenticato, audit log
  Encryption: in transit + at rest (disk-level)

Livello 3 — CONFIDENZIALE
  Esempi: dati cliente, email, progetti, documenti caricati
  Controlli: RBAC, audit log dettagliato, retention policy
  Encryption: in transit + at rest (column-level per campi sensibili)

Livello 4 — SEGRETO
  Esempi: credenziali, API key, dati sanitari, numeri carta di credito
  Controlli: accesso minimo, MFA obbligatoria, alert su ogni accesso
  Encryption: application-level encryption, tokenizzazione
  Retention: minima necessaria, cancellazione sicura
```

---

## Sicurezza delle API

Le API sono la superficie di attacco primaria di un SaaS. Ogni endpoint è un potenziale vettore di attacco.

### OWASP API Security Top 10 (2023)

| # | Vulnerabilità | Descrizione | Mitigazione |
|---|--------------|-------------|-------------|
| API1 | Broken Object Level Authorization (BOLA) | Accesso a risorse di altri utenti manipolando ID | Validare ownership per ogni richiesta. Usare UUID, non ID sequenziali |
| API2 | Broken Authentication | Autenticazione debole o assente | OAuth 2.0 + PKCE, rate limiting su login, MFA |
| API3 | Broken Object Property Level Authorization | Accesso a proprietà dell'oggetto non autorizzate | Filtrare output per ruolo, whitelist di campi |
| API4 | Unrestricted Resource Consumption | Nessun limite su risorse (CPU, memoria, banda) | Rate limiting, pagination obbligatoria, payload size limit |
| API5 | Broken Function Level Authorization | Accesso a funzioni admin da utente normale | Separare endpoint admin, verificare ruolo per ogni azione |
| API6 | Unrestricted Access to Sensitive Business Flows | Automazione di flussi business (scraping, bot) | CAPTCHA, rate limiting per business flow, anomaly detection |
| API7 | Server Side Request Forgery (SSRF) | Il server esegue richieste arbitrarie | Validare URL, bloccare IP interni, allowlist di domini |
| API8 | Security Misconfiguration | Configurazione di default insicura | Security header, CORS restrittivo, no debug in produzione |
| API9 | Improper Inventory Management | API non documentate, versioni obsolete | API inventory, deprecation policy, discovery scan |
| API10 | Unsafe Consumption of APIs | Fidarsi ciecamente di API terze parti | Validare risposte, timeout, circuit breaker, sanitizzare input |

### Rate Limiting

```
Strategia di rate limiting multi-livello:

1. GLOBALE (DDoS protection):
   - 10.000 request/minuto per IP
   - Implementato a livello WAF/CDN (Cloudflare, AWS Shield)

2. PER UTENTE AUTENTICATO:
   - 1.000 request/minuto per API key
   - Implementato a livello API gateway
   - Header di risposta:
     X-RateLimit-Limit: 1000
     X-RateLimit-Remaining: 847
     X-RateLimit-Reset: 1700000000
     Retry-After: 30

3. PER ENDPOINT:
   - POST /api/login: 5 tentativi/minuto (brute force protection)
   - POST /api/signup: 3/ora per IP (anti-bot)
   - GET /api/export: 10/ora per utente (anti-scraping)
   - POST /api/payments: 20/minuto per utente

4. PER TENANT:
   - Piano Free: 1.000 request/giorno
   - Piano Pro: 100.000 request/giorno
   - Piano Enterprise: custom, negoziabile

Algoritmi:
- Token Bucket: burst-friendly, usato da AWS API Gateway
- Sliding Window: più preciso, usato per per-user limits
- Fixed Window: semplice, rischio burst al confine finestra
- Leaky Bucket: rate costante, buono per background job
```

### Input Validation

```
Principi di validazione input per API:

1. SCHEMA VALIDATION:
   Ogni endpoint ha uno schema JSON/OpenAPI che definisce:
   - Tipi dei campi (string, integer, array)
   - Vincoli (minLength, maxLength, pattern, enum)
   - Campi obbligatori vs opzionali
   - Formato (email, URI, date-time, UUID)

   Validare con librerie come Zod, Joi, Pydantic, ajv.
   Rifiutare richieste non conformi con 400 Bad Request.

2. SANITIZZAZIONE:
   - Trim whitespace
   - Normalizzare unicode (NFC)
   - Rimuovere null bytes
   - Limitare profondità JSON (max 10 livelli)
   - Limitare dimensione payload (max 1 MB per default, 100 MB per upload)

3. BUSINESS LOGIC VALIDATION:
   Oltre allo schema, validare la logica:
   - L'utente ha i fondi sufficienti?
   - La risorsa esiste ed è del tenant corretto?
   - L'operazione è permessa nello stato corrente?

4. OUTPUT ENCODING:
   - Risposte JSON: Content-Type: application/json
   - Mai costruire HTML da input utente senza encoding
   - Mai riflettere input utente in header HTTP
```

### Autenticazione delle API

```
Token di autenticazione per API:

1. API Key:
   - Formato: prefisso visibile + segreto (sk_live_abc123...)
   - Storage: hash SHA-256 nel database (come password)
   - Mostrare il valore completo SOLO alla creazione
   - Permessi: per API key, non per utente
   - Scadenza: opzionale, consigliata
   - Revoca: immediata, propagata entro secondi

2. OAuth 2.0 Bearer Token:
   - Formato: JWT firmato o token opaco
   - Validazione: verifica firma (RS256/ES256) + scadenza + audience
   - Scadenza: 15-60 minuti (breve)
   - Refresh: tramite refresh token (scadenza 7-30 giorni)
   - Revoca: blacklist o short expiry

3. Webhook Signature:
   - HMAC-SHA256 del body con shared secret
   - Header: X-Webhook-Signature
   - Timestamp per prevenire replay attack
   - Il ricevente verifica HMAC prima di processare

Esempio validazione JWT (pseudocodice):

function validateToken(token):
    // 1. Decodifica header (senza verificare)
    header = decodeHeader(token)

    // 2. Recupera la chiave pubblica dal JWKS endpoint
    publicKey = getPublicKey(header.kid)

    // 3. Verifica firma
    if not verifySignature(token, publicKey, header.alg):
        return UNAUTHORIZED

    // 4. Decodifica payload
    payload = decodePayload(token)

    // 5. Verifica scadenza
    if payload.exp < currentTime():
        return UNAUTHORIZED

    // 6. Verifica audience
    if payload.aud != "https://api.example.com":
        return UNAUTHORIZED

    // 7. Verifica issuer
    if payload.iss != "https://auth.example.com":
        return UNAUTHORIZED

    return payload
```

---

## Sicurezza Applicativa (OWASP)

### OWASP Top 10 per SaaS

**1. Broken Access Control** (A01): utenti che accedono a dati/funzionalità non autorizzate. Nel SaaS: cross-tenant data access. Prevenzione: RBAC rigoroso, tenant isolation, test automatici.

**2. Cryptographic Failures** (A02): dati sensibili non criptati o criptati male. Prevenzione: TLS everywhere, encryption at rest, no dati sensibili nei log.

**3. Injection** (A03): SQL injection, NoSQL injection, command injection. Prevenzione: parametric queries (prepared statements), ORM, input validation, no concatenazione di stringhe nelle query.

```sql
-- VULNERABILE (SQL injection)
query = "SELECT * FROM users WHERE email = '" + email + "'"

-- SICURO (prepared statement)
query = "SELECT * FROM users WHERE email = $1"
params = [email]
```

**4. Insecure Design** (A04): difetti architetturali. Prevenzione: threat modeling, security review nel design phase, abuse case analysis.

**5. Security Misconfiguration** (A05): configurazioni di default, header mancanti, servizi esposti. Prevenzione: hardening checklist, security header (CSP, X-Frame-Options, X-Content-Type-Options), no servizi in ascolto non necessari.

**6. Vulnerable Components** (A06): librerie con vulnerabilità note. Prevenzione: Dependabot/Snyk per scanning automatico, aggiornamento regolare, SBOM (Software Bill of Materials).

**7. Authentication Failures** (A07): credential stuffing, brute force, session fixation. Prevenzione: rate limiting su login, MFA, session rotation, password policy solida.

**8. Data Integrity Failures** (A08): software update non verificato, CI/CD compromise. Prevenzione: firma dei build, integrity check, supply chain security.

**9. Logging Failures** (A09): eventi di sicurezza non loggati. Prevenzione: audit log per login, accesso dati, modifiche permessi, azioni admin. Centralizzare in SIEM.

**10. SSRF** (A10): Server-Side Request Forgery. L'attaccante fa eseguire richieste HTTP dal server. Prevenzione: validare e filtrare URL esterni, non permettere richieste a IP interni.

### Security Header

```
Content-Security-Policy: default-src 'self'; script-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### Sicurezza Applicativa Avanzata

#### Content Security Policy (CSP) per SaaS

```
CSP moderno con nonce per un SaaS:

Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-{SERVER_GENERATED_RANDOM}';
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  img-src 'self' data: blob: https://cdn.example.com;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' https://api.example.com wss://ws.example.com;
  frame-src 'self' https://js.stripe.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
  object-src 'none';
  upgrade-insecure-requests;
  report-uri /api/csp-violations;

Punti critici per SaaS:
- frame-ancestors 'none': previene clickjacking
- connect-src: limitare a API proprie + terze parti note
- frame-src: solo iframe necessari (Stripe, Intercom)
- report-uri: raccogliere violazioni CSP per tuning
- Nonce-based: evitare 'unsafe-inline' per script
```

#### Protezione CSRF

```
Pattern anti-CSRF per SaaS:

1. SYNCHRONIZER TOKEN:
   - Server genera token random per ogni sessione
   - Token incluso in hidden field o header custom
   - Server verifica token su ogni richiesta state-changing

2. DOUBLE SUBMIT COOKIE:
   - Token salvato in cookie (SameSite=Strict)
   - Stesso token inviato nell'header X-CSRF-Token
   - Server verifica che corrispondano

3. SAME-SITE COOKIE:
   Set-Cookie: session=abc123;
     SameSite=Strict;
     Secure;
     HttpOnly;
     Path=/;
     Max-Age=3600

   SameSite=Strict: il cookie non viene inviato per cross-site request
   SameSite=Lax: il cookie viene inviato solo per GET top-level navigation

4. CUSTOM HEADER:
   Le API JSON richiedono Content-Type: application/json
   I browser non inviano questo header in form automatici
   Verificare lato server che il Content-Type sia corretto
```

---

## Sicurezza Infrastrutturale

### Network Security

- **VPC** (Virtual Private Cloud): isolare le risorse in una rete privata
- **Security Groups**: firewall a livello di istanza. Principio: deny all, allow specific
- **Subnet segmentation**: public subnet (solo load balancer), private subnet (application), isolated subnet (database)
- **Bastion host / VPN**: accesso SSH/admin solo tramite bastion o VPN, mai direttamente esposto
- **WAF** (Web Application Firewall): protezione da OWASP top 10, bot detection, rate limiting. AWS WAF, Cloudflare WAF

### Architettura di Rete Sicura per SaaS

```
Architettura di rete multi-tier:

Internet
    │
    ▼
┌─────────────────────────────────────────────────┐
│              CDN / DDoS Protection               │
│         (Cloudflare, AWS CloudFront)             │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│            PUBLIC SUBNET (10.0.1.0/24)           │
│                                                  │
│  ┌─────────────────┐  ┌──────────────────────┐  │
│  │  Load Balancer   │  │   WAF / API Gateway   │  │
│  │  (ALB/NLB)       │  │                       │  │
│  └────────┬────────┘  └──────────┬───────────┘  │
└───────────┼──────────────────────┼──────────────┘
            │                      │
┌───────────▼──────────────────────▼──────────────┐
│          PRIVATE SUBNET (10.0.2.0/24)            │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐              │
│  │  App Server 1 │  │  App Server 2 │  (Auto-    │
│  │  (Container)  │  │  (Container)  │  scaling)  │
│  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                     │
│  ┌──────▼──────────────────▼───────┐             │
│  │         Service Mesh             │             │
│  │    (Istio / Linkerd mTLS)        │             │
│  └──────────────┬──────────────────┘             │
└─────────────────┼────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────┐
│         ISOLATED SUBNET (10.0.3.0/24)            │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐              │
│  │  PostgreSQL   │  │  Redis Cache  │             │
│  │  (Primary)    │  │  (Cluster)    │             │
│  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐              │
│  │  PostgreSQL   │  │  ElasticSearch│             │
│  │  (Replica)    │  │  (Cluster)    │             │
│  └──────────────┘  └──────────────┘              │
│                                                  │
│  NO accesso Internet diretto                     │
│  Accesso solo da Private Subnet                  │
│  NAT Gateway solo per update OS (outbound only)  │
└──────────────────────────────────────────────────┘
```

### Cloud Hardening

```
Checklist di hardening cloud (AWS):

IDENTITY & ACCESS:
□ Root account: MFA hardware, no API key, usato solo per emergenze
□ IAM: policy con least privilege, no inline policy, solo managed/custom
□ Service accounts: una per servizio, ruoli specifici
□ Password policy IAM: 14+ caratteri, rotazione 90 giorni
□ AWS SSO per accesso umano alla console
□ CloudTrail abilitato su tutte le regioni
□ GuardDuty abilitato

COMPUTE:
□ EC2: no SSH key → Systems Manager Session Manager
□ EC2: IMDSv2 obbligatorio (previene SSRF → metadata)
□ Lambda: runtime aggiornati, no segreti in variabili d'ambiente (→ Secrets Manager)
□ ECS/EKS: immagini da ECR privato, scanning abilitato
□ Auto-scaling con limiti sensati (anti-bill-shock)

STORAGE:
□ S3: Block Public Access a livello account
□ S3: bucket policy restrittive, no "s3:*"
□ S3: versioning abilitato per bucket critici
□ S3: server-side encryption (SSE-KMS per dati sensibili)
□ EBS: encryption di default abilitata
□ RDS: encryption at rest, SSL/TLS per connessioni

NETWORK:
□ VPC flow logs abilitati
□ Security group: no 0.0.0.0/0 su porte diverse da 443
□ NACL: default deny inbound/outbound
□ No risorse in public subnet (tranne ALB)
□ PrivateLink per servizi AWS (S3, SQS, etc.)
□ DNS over HTTPS / DNSSEC

LOGGING & MONITORING:
□ CloudTrail: management + data events
□ CloudWatch: allarmi su eventi critici
□ Config: regole di compliance automatiche
□ Access Analyzer: trovare risorse condivise esternamente
□ Security Hub: dashboard centralizzata
```

### Container Security

- **Immagini base minimali**: Alpine o distroless, non Ubuntu full
- **Scanning vulnerabilità**: Trivy, Snyk Container prima del deploy
- **Non root**: i container non devono girare come root
- **Read-only filesystem**: dove possibile, il filesystem del container è read-only
- **Network policy**: in Kubernetes, limitare la comunicazione tra pod

#### Container Security Avanzata

```
Dockerfile sicuro — best practices:

# Usa immagini distroless o Alpine
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production
COPY . .
RUN npm run build

# Multi-stage: immagine finale minimale
FROM gcr.io/distroless/nodejs22-debian12
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

# Non root
USER 1001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s CMD ["/nodejs/bin/node", "dist/healthcheck.js"]

# Read-only filesystem
# (impostato nel deploy, non nel Dockerfile)

EXPOSE 8080
CMD ["dist/server.js"]
```

```
Kubernetes Security Context:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: saas-api
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: api
        image: registry.example.com/saas-api:v2.3.1
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
              - ALL
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir:
          sizeLimit: 100Mi
```

### Secret Management

Mai secret nel codice o nei file di configurazione committati in Git.

- **AWS Secrets Manager / Parameter Store**: secret gestiti come servizio
- **HashiCorp Vault**: per scenari complessi (dynamic secrets, leasing)
- **Environment variables**: accettabili per staging, non ideali per produzione (visibili in process list)
- **Secret scanning**: tool come GitLeaks, TruffleHog per rilevare secret committati per errore

#### Architettura di Secret Management

```
Gerarchia di secret management:

Livello 1 — SECRET STORE:
  HashiCorp Vault / AWS Secrets Manager / GCP Secret Manager
  - Encryption at rest con KMS/HSM
  - Access control granulare (policy per servizio)
  - Audit log di ogni accesso
  - Versioning dei segreti
  - Rotation automatica

Livello 2 — SECRET INJECTION:
  Kubernetes: External Secrets Operator / Vault Agent Sidecar
  - Il segreto non è mai in ConfigMap o env var
  - Iniettato come file temporaneo nel pod
  - Ruotato automaticamente senza restart

Livello 3 — DYNAMIC SECRETS:
  Vault genera credenziali database on-demand
  - Ogni pod riceve credenziali uniche
  - TTL breve (1-24 ore)
  - Revoca automatica alla scadenza
  - Se un pod è compromesso, le sue credenziali scadono

Livello 4 — SECRET DETECTION:
  Pre-commit hook + CI pipeline:
  - GitLeaks: scan pattern noti (API key, password)
  - TruffleHog: scan entropia (stringhe random = possibile segreto)
  - Bloccare il commit/merge se segreto trovato
  - Se segreto committato: revocare immediatamente + ruotare

Errori comuni:
✗ Segreti nelle variabili d'ambiente (visibili in /proc, debug output)
✗ Segreti nel Dockerfile o docker-compose.yml
✗ Segreti in ConfigMap Kubernetes
✗ .env committato (anche se poi rimosso — è nella git history)
✗ Segreti nei log applicativi (loggare un request che contiene un token)
```

---

## Gestione delle Vulnerabilità

### Processo di Vulnerability Management

```
Ciclo di vita delle vulnerabilità:

1. DISCOVERY (scoperta):
   - Scanning automatico continuo (Snyk, Trivy, Dependabot)
   - Penetration test periodico (trimestrale/annuale)
   - Bug bounty / responsible disclosure
   - Threat intelligence feed
   - Scan di configurazione (AWS Config, ScoutSuite)

2. CLASSIFICATION (classificazione):
   - CVSS v3.1 score per severity oggettiva
   - Contesto: è esposta su Internet? Ci sono dati sensibili?
   - Exploitability: esiste un exploit pubblico?
   - Impact: confidenzialità, integrità, disponibilità

3. PRIORITIZATION (prioritizzazione):
   CVSS ≥ 9.0 (Critical): fix entro 24 ore
   CVSS 7.0-8.9 (High):    fix entro 7 giorni
   CVSS 4.0-6.9 (Medium):  fix entro 30 giorni
   CVSS < 4.0 (Low):       fix entro 90 giorni

   Fattori che alzano la priorità:
   - Exploit pubblico disponibile (EPSS score alto)
   - Vulnerabilità in componente esposto a Internet
   - Dati sensibili (PII, credentials) a rischio
   - Listed in CISA KEV (Known Exploited Vulnerabilities)

4. REMEDIATION (rimedio):
   - Patch: aggiornare la versione vulnerabile
   - Workaround: mitigare se il patch non è disponibile
   - Accept risk: documentare se il rischio è trascurabile
   - Compensating control: WAF rule se il patch richiede tempo

5. VERIFICATION (verifica):
   - Re-scan dopo il fix
   - Test di regressione
   - Verifica che il fix non introduca nuovi problemi

6. REPORTING (reportistica):
   - Dashboard: vulnerabilità aperte per severity, trend, SLA compliance
   - MTTR (Mean Time To Remediate) per severity
   - Report mensile per leadership
```

### Scanning Automatico

```
Pipeline di scanning integrata nella CI/CD:

PRE-COMMIT:
  ├── GitLeaks: secret scanning
  └── Semgrep: static analysis per pattern insicuri

PULL REQUEST:
  ├── Snyk/Dependabot: dependency vulnerability scanning
  ├── Trivy: container image scanning
  ├── SAST (Static Application Security Testing):
  │     Semgrep, SonarQube, CodeQL
  ├── License compliance: verificare licenze open source
  └── IaC scanning: Checkov, tfsec per Terraform/CloudFormation

PRE-DEPLOY:
  ├── DAST (Dynamic Application Security Testing):
  │     OWASP ZAP, Burp Suite (in staging)
  ├── Container scanning finale: Trivy su immagine production-ready
  └── Configuration audit: verifica hardening

POST-DEPLOY:
  ├── DAST continuo su production (non intrusivo)
  ├── Cloud posture scanning: ScoutSuite, Prowler
  └── Certificate monitoring: scadenza, CT log
```

### Patching Cadence

```
Calendario di patching:

INFRASTRUCTURE OS:
  - Patch critiche: entro 24 ore (fuori orario di business)
  - Patch security: settimanale (martedì patching)
  - Patch minori: mensile
  - Major version: trimestrale (con testing completo)

RUNTIME & FRAMEWORK:
  - Node.js LTS: seguire il release schedule (ogni 2 settimane check)
  - Python: aggiornare minor version entro 30 giorni
  - Framework (Next.js, Django, etc.): entro 14 giorni da security release

DIPENDENZE:
  - Dependabot/Renovate: PR automatiche, merge dopo CI verde
  - Critical: merge manuale entro 24 ore
  - High: merge entro 7 giorni
  - Medium/Low: batch settimanale

CONTAINER BASE IMAGE:
  - Rebuild weekly con base image aggiornata
  - Se CVE critico in base image: rebuild immediato
```

### Responsible Disclosure

```
Processo di responsible disclosure:

1. SECURITY.TXT (standard RFC 9116):
   Pubblicare /.well-known/security.txt:

   Contact: mailto:security@example.com
   Encryption: https://example.com/.well-known/pgp-key.txt
   Acknowledgments: https://example.com/security/thanks
   Preferred-Languages: en, it
   Canonical: https://example.com/.well-known/security.txt
   Policy: https://example.com/security/policy
   Expires: 2027-01-01T00:00:00.000Z

2. SECURITY POLICY (pagina pubblica):
   - Scope: quali domini/applicazioni sono in scope
   - Out of scope: attacchi DDoS, social engineering, phishing test
   - Come segnalare: email con PGP, oppure HackerOne/Bugcrowd
   - Cosa includere: descrizione, passi per riprodurre, impatto
   - Safe harbor: non perseguiremo legalmente chi opera in buona fede
   - Timeline: risposta entro 2 business day, fix entro 90 giorni

3. TRIAGE (ricevuto il report):
   - Conferma ricezione entro 24 ore
   - Valutazione severity entro 48 ore
   - Comunicazione timeline al researcher
   - Aggiornamenti ogni 7 giorni

4. DISCLOSURE:
   - Fix sviluppato e testato
   - Fix deployato in produzione
   - CVE assegnato (se applicabile)
   - Researcher notificato che può pubblicare
   - Credito pubblico nella hall of fame (se il researcher accetta)
```

---

## Sicurezza della Supply Chain

### Rischio della Supply Chain Software

La supply chain è diventata un vettore di attacco primario. SolarWinds (2020), Log4Shell (2021), XZ Utils (2024) hanno dimostrato la scala del rischio.

### SBOM (Software Bill of Materials)

```
SBOM — Cos'è e perché è necessario:

Un SBOM è l'inventario completo dei componenti software di un'applicazione.
Formati standard: SPDX (ISO), CycloneDX (OWASP).

Contenuto di un SBOM:
- Nome, versione, licenza di ogni dipendenza
- Dipendenze transitive (dipendenze delle dipendenze)
- Hash/checksum per verifica integrità
- Fornitore/autore del componente
- Vulnerabilità note (collegamento a CVE/NVD)

Generazione:
- Build time: Syft, Trivy, CycloneDX CLI
- Esempio: syft packages dir:. -o cyclonedx-json > sbom.json
- Integrare nella CI/CD: generare SBOM a ogni build
- Pubblicare SBOM per i clienti enterprise (richiesto da EO 14028 USA)

Utilizzo:
- Quando esce un CVE: cercare nel SBOM se il componente è presente
- License compliance: verificare che tutte le licenze siano compatibili
- Audit SOC 2/ISO 27001: fornire come evidenza di gestione dipendenze
- Risposta a incidenti: sapere immediatamente se si è impattati
```

### Third-Party Risk Management

```
Processo di valutazione fornitori terzi:

1. INVENTARIO:
   Catalogare ogni servizio/libreria/SaaS di terze parti:
   - Nome e versione
   - Categoria (auth, payment, analytics, infra)
   - Dati condivisi (PII? Dati clienti? Credenziali?)
   - SLA e uptime storico
   - Certificazioni (SOC 2, ISO 27001)
   - Contatto security del fornitore

2. RISK ASSESSMENT:
   Per ogni fornitore, valutare:

   | Criterio                | Peso | Score (1-5) |
   |-------------------------|------|-------------|
   | Accesso a dati sensibili| 30%  |             |
   | Criticità per il servizio| 25%  |             |
   | Security posture (SOC 2)| 20%  |             |
   | Maturità del fornitore  | 15%  |             |
   | Alternative disponibili | 10%  |             |

   Score totale:
   - High risk (>3.5): revisione trimestrale, DPA obbligatorio
   - Medium risk (2.5-3.5): revisione semestrale
   - Low risk (<2.5): revisione annuale

3. CONTRATTI:
   - Data Processing Agreement (DPA) per ogni fornitore con accesso a dati
   - SLA con penalità per downtime
   - Clausola di breach notification (entro 24-72 ore)
   - Diritto di audit
   - Exit strategy: portabilità dei dati, timeline di cancellazione

4. MONITORAGGIO CONTINUO:
   - Verificare certificazioni alla scadenza
   - Monitorare breach pubblici dei fornitori
   - Testare periodicamente le integrazioni
   - Aggiornare risk assessment annualmente
```

### Sicurezza della CI/CD Pipeline

```
Hardening della CI/CD pipeline:

1. SOURCE CODE:
   - Branch protection: PR obbligatorie, review richieste
   - Signed commits (GPG/SSH)
   - CODEOWNERS per file critici (security, auth, billing)
   - No force-push su main/master

2. BUILD:
   - Build riproducibili: stessa commit → stesso artifact
   - Dipendenze da registry privato (mirror di npm, PyPI)
   - Lock file committato (package-lock.json, go.sum)
   - Integrità verificata: npm audit signatures, go mod verify

3. ARTIFACT:
   - Container image firmata (cosign / Sigstore)
   - SBOM generato e allegato all'image
   - Image provenance attestation (SLSA Level 3)
   - Registry privato con vulnerability scanning

4. DEPLOY:
   - Infrastruttura come codice (Terraform, Pulumi)
   - GitOps: nessun accesso diretto al cluster
   - Rollback automatico se health check fallisce
   - Canary/blue-green per ridurre blast radius

5. SECRETS in CI/CD:
   - Mai in .env o YAML committati
   - Usare i secret manager del CI (GitHub Actions Secrets, etc.)
   - Rotare periodicamente
   - Scope minimo (solo i job che ne hanno bisogno)
```

---

## Security Monitoring e SIEM

### Architettura di Monitoring

```
Stack di security monitoring per SaaS:

FONTI DI LOG:
  ├── Application logs (strutturati, JSON)
  ├── API access logs (request/response, latenza, errori)
  ├── Authentication logs (login, MFA, SSO, failure)
  ├── Database query logs (slow query, errori, accessi)
  ├── Infrastructure logs (VPC flow, CloudTrail, WAF)
  ├── Container logs (stdout/stderr, audit)
  └── Third-party logs (IdP, payment, CDN)
          │
          ▼
COLLECTION & NORMALIZATION:
  ├── Fluent Bit / Fluentd (collection)
  ├── Vector (collection + transformation)
  └── Normalizzazione: Common Event Format (CEF) o ECS
          │
          ▼
STORAGE & ANALYSIS:
  ├── SIEM: Elastic Security, Splunk, Microsoft Sentinel, Sumo Logic
  ├── Data Lake: S3 + Athena per analisi a lungo termine
  └── Retention: 90 giorni hot, 1 anno warm, 7 anni cold (compliance)
          │
          ▼
DETECTION & ALERTING:
  ├── Detection rules (SIGMA format, portabile tra SIEM)
  ├── ML-based anomaly detection
  ├── Threat intelligence correlation
  └── Alert routing: PagerDuty, OpsGenie, Slack
          │
          ▼
RESPONSE:
  ├── Runbook automatizzati (SOAR)
  ├── Escalation path definito
  └── Incident tracking (Jira, dedicated tool)
```

### Detection Rules

```
Regole di detection critiche per SaaS:

1. BRUTE FORCE LOGIN:
   Condizione: >10 login falliti in 5 minuti per stesso account
   Azione: bloccare account per 30 minuti, alert al team
   Severity: HIGH

2. IMPOSSIBLE TRAVEL:
   Condizione: login da 2 geolocalizzazioni distanti in <2 ore
   Azione: alert, richiedere ri-autenticazione MFA
   Severity: HIGH

3. PRIVILEGE ESCALATION:
   Condizione: utente cambia il proprio ruolo a admin
   Azione: alert immediato, revert automatico
   Severity: CRITICAL

4. CROSS-TENANT ACCESS:
   Condizione: richiesta API restituisce dati con tenant_id diverso
   Azione: alert CRITICAL, bloccare endpoint, incident response
   Severity: CRITICAL

5. API ABUSE:
   Condizione: >5x il rate limit normale per un utente
   Azione: throttle, alert, possibile ban temporaneo
   Severity: MEDIUM

6. DATA EXFILTRATION:
   Condizione: download massivo (>1000 record/minuto da export API)
   Azione: bloccare export, alert, richiedere conferma
   Severity: HIGH

7. NEW ADMIN CREATED:
   Condizione: nuovo utente admin creato (specialmente fuori orario)
   Azione: alert, verifica con admin esistente
   Severity: HIGH

8. SENSITIVE DATA ACCESS:
   Condizione: accesso a dati di Livello 4 (credenziali, dati sanitari)
   Azione: log dettagliato, alert se accesso inusuale
   Severity: MEDIUM

9. CONFIGURATION CHANGE:
   Condizione: modifica a security group, IAM policy, encryption settings
   Azione: log, alert, review entro 24 ore
   Severity: MEDIUM

10. CERTIFICATE ANOMALY:
    Condizione: nuovo certificato TLS emesso per il dominio (CT Log)
    Azione: alert immediato, verificare legittimità
    Severity: HIGH
```

### Audit Log

```
Struttura di un audit log per SaaS:

{
  "timestamp": "2026-05-22T14:30:00.000Z",
  "event_id": "evt_abc123",
  "event_type": "resource.updated",
  "actor": {
    "type": "user",
    "id": "usr_def456",
    "email": "admin@acme.com",
    "ip": "198.51.100.42",
    "user_agent": "Mozilla/5.0...",
    "session_id": "ses_ghi789"
  },
  "tenant": {
    "id": "tnt_jkl012",
    "name": "Acme Corp"
  },
  "resource": {
    "type": "project",
    "id": "prj_mno345",
    "name": "Q4 Campaign"
  },
  "action": "update",
  "changes": {
    "before": { "status": "active" },
    "after": { "status": "archived" }
  },
  "context": {
    "source": "web_app",
    "request_id": "req_pqr678",
    "geo": { "country": "IT", "city": "Milano" }
  },
  "result": "success"
}

Requisiti per l'audit log:
- IMMUTABILE: append-only, nessuna modifica o cancellazione
- COMPLETO: ogni azione significativa loggata
- RETENTION: minimo 1 anno (SOC 2), 7 anni per finanza
- INTEGRITÀ: hash chain o firma per tamper detection
- RICERCABILE: indicizzato per actor, tenant, resource, timestamp
- ESPORTABILE: API per clienti enterprise che vogliono integrare con il proprio SIEM
```

---

## Penetration Testing

### Ambito e Frequenza

```
Programma di penetration testing per SaaS:

FREQUENZA:
  - Penetration test completo: annuale (minimo per SOC 2)
  - Test focalizzato: dopo major release o cambio architetturale
  - Scanning automatico DAST: settimanale
  - Red team exercise: annuale (per SaaS con >50M utenti)

AMBITO (SCOPE):
  In scope:
  - Applicazione web (tutte le funzionalità)
  - API (tutti gli endpoint documentati + discovery di endpoint nascosti)
  - Autenticazione e autorizzazione (SSO, MFA, RBAC)
  - Tenant isolation (cross-tenant access test)
  - Mobile app (se presente)
  - Infrastruttura cloud (configurazione, accesso)
  - Integrazioni terze parti (webhook, OAuth flow)

  Out of scope:
  - DDoS (può impattare altri clienti del cloud provider)
  - Social engineering su dipendenti (richiede consenso separato)
  - Infrastruttura fisica del cloud provider
  - Servizi terzi non di proprietà

METODOLOGIA:
  1. Ricognizione: mapping dell'applicazione, discovery endpoint
  2. Scanning: vulnerability scanner automatico
  3. Exploitation: tentativi di sfruttamento manuale
  4. Post-exploitation: lateral movement, privilege escalation
  5. Reporting: vulnerability, severity, PoC, remediation
  6. Re-test: verifica fix dopo remediation

REMEDIATION SLA:
  - Critical (CVSS ≥ 9.0): fix entro 7 giorni, re-test entro 14
  - High (CVSS 7.0-8.9): fix entro 30 giorni, re-test entro 45
  - Medium (CVSS 4.0-6.9): fix entro 90 giorni
  - Low (CVSS < 4.0): fix nel prossimo ciclo di sviluppo
  - Informational: a discrezione del team

DELIVERABLE:
  - Executive summary (1-2 pagine, per leadership e clienti)
  - Technical report (dettaglio per ogni vulnerabilità)
  - Remediation roadmap (prioritizzata)
  - Re-test report (conferma fix)
  - Letter of attestation (per condividere con clienti)
```

### Tipi di Test

```
Tipi di penetration test:

1. BLACK BOX:
   - Il tester non ha informazioni sull'applicazione
   - Simula un attaccante esterno
   - Trova vulnerabilità accessibili pubblicamente
   - Pro: scenario realistico
   - Contro: coverage limitata, richiede più tempo

2. GRAY BOX:
   - Il tester ha credenziali utente standard
   - Testa l'applicazione come utente autenticato
   - Trova vulnerabilità di autorizzazione, IDOR, tenant isolation
   - Pro: coverage buona per logica business
   - Contro: non simula il primo accesso

3. WHITE BOX:
   - Il tester ha accesso al codice sorgente e alla documentazione
   - Analisi statica + dinamica
   - Trova vulnerabilità profonde (race condition, logic flaw)
   - Pro: massima coverage
   - Contro: richiede più tempo e competenza

Raccomandazione per SaaS:
  - Anno 1: Gray box (trova più problemi con budget limitato)
  - Anno 2+: Alternare gray box e white box
  - Continuo: DAST automatico + bug bounty
```

---

## Incident Response

### Piano di Incident Response

```
FASI:

1. DETECTION (rilevamento)
   → Monitoring automatico: anomaly detection, SIEM alerts
   → Report esterno: cliente, security researcher, bug bounty
   → Interno: sviluppatore che nota comportamento anomalo

2. TRIAGE (classificazione)
   → Severity: Critical (breach attivo), High (vulnerabilità sfruttabile),
     Medium (vulnerabilità potenziale), Low (best practice mancante)
   → Assegnazione: incident commander, team di risposta

3. CONTAINMENT (contenimento)
   → Isolare il sistema compromesso
   → Revocare credenziali compromesse
   → Bloccare l'accesso dell'attaccante
   → NON spegnere il sistema (preservare le prove)

4. ERADICATION (eliminazione)
   → Identificare e rimuovere la causa root
   → Patchare la vulnerabilità
   → Verificare che l'attaccante non abbia persistenza

5. RECOVERY (ripristino)
   → Ripristinare il servizio da backup verificato
   → Monitorare per recidive
   → Verificare l'integrità dei dati

6. POST-MORTEM (analisi)
   → Timeline degli eventi
   → Cosa è andato storto
   → Cosa ha funzionato
   → Action item per prevenire ricorrenza
   → Comunicazione a clienti e autorità (se necessario)
```

### Ruoli nel Team di Incident Response

```
Ruoli durante un incidente di sicurezza:

INCIDENT COMMANDER (IC):
  - Coordina la risposta
  - Prende decisioni (containment, comunicazione)
  - Aggiorna leadership e stakeholder
  - Unico punto di contatto per comunicazioni esterne
  - Non lavora sul fix tecnico (coordina chi lo fa)

TECHNICAL LEAD:
  - Guida l'investigazione tecnica
  - Coordina gli sviluppatori/SRE
  - Identifica la root cause
  - Sviluppa e verifica il fix

COMMUNICATIONS LEAD:
  - Gestisce la comunicazione con clienti
  - Prepara status page updates
  - Coordina con legale per notifiche obbligatorie
  - Gestisce media/press se necessario

SCRIBE:
  - Documenta tutto in tempo reale
  - Timeline degli eventi
  - Decisioni prese e motivazioni
  - Comandi eseguiti, output osservati
  - Questa documentazione è cruciale per il post-mortem

On-Call Rotation:
  - Copertura 24/7 con almeno 2 persone (IC + Technical Lead)
  - Escalation path chiaro (chi chiamare se la severity aumenta)
  - Tempo di risposta: 15 minuti per Critical, 1 ora per High
  - Runbook accessibili offline (non dipendere dal sistema sotto attacco)
```

### Playbook di Risposta per Scenari Comuni

```
SCENARIO: Account Admin Compromesso

Trigger: login sospetto su account admin (IP anomalo, orario inusuale)

Containment (entro 15 minuti):
  1. Forzare logout di tutte le sessioni dell'account
  2. Disabilitare l'account temporaneamente
  3. Revocare tutte le API key associate
  4. Verificare gli ultimi 24 ore di audit log per quell'account

Investigation (entro 2 ore):
  1. Come è stato compromesso? (phishing, credential stuffing, token theft)
  2. Quali azioni ha eseguito l'attaccante? (audit log)
  3. Sono stati creati nuovi admin o backdoor?
  4. Dati esportati o modificati?

Eradication:
  1. Rimuovere eventuali backdoor (account, API key, webhook)
  2. Reset password forzato + reset MFA
  3. Se credential stuffing: verificare se le credenziali sono in data breach pubblici

Recovery:
  1. Riabilitare l'account dopo reset password + MFA
  2. Monitorare intensivamente per 30 giorni
  3. Notificare il cliente proprietario dell'account
  4. Se dati compromessi: attivare procedura di breach notification

---

SCENARIO: Cross-Tenant Data Leak

Trigger: SIEM alert o report cliente che vede dati di un altro tenant

Containment (entro 5 minuti):
  1. Identificare l'endpoint vulnerabile
  2. Disabilitare l'endpoint o applicare hotfix
  3. Identificare tutti i tenant potenzialmente impattati

Investigation (entro 4 ore):
  1. Analizzare i log per capire da quando il bug esiste
  2. Quanti tenant hanno potenzialmente acceduto a dati di altri?
  3. Quali dati sono stati esposti? (PII? Dati finanziari?)
  4. Root cause: RLS non applicato? Bug in query? Caching cross-tenant?

Eradication:
  1. Fix della vulnerabilità con test di regressione
  2. Aggiungere test automatico cross-tenant per l'endpoint
  3. Audit di tutti gli endpoint simili

Recovery:
  1. Deploy del fix
  2. Notifica OBBLIGATORIA a tutti i tenant impattati
  3. Se PII esposti: notifica al Garante entro 72 ore (GDPR)
  4. Fornire ai clienti il dettaglio di quali dati sono stati esposti
```

### Data Breach Notification

**GDPR**: notifica al Garante entro 72 ore. Notifica agli interessati se rischio elevato.

**Comunicazione ai clienti**: essere trasparenti. Cosa è successo, quando, quali dati sono stati impattati, cosa stiamo facendo, cosa devono fare loro. La trasparenza mantiene la fiducia; il silenzio la distrugge.

```
Template di comunicazione data breach:

Oggetto: Notifica di sicurezza — Incidente del [DATA]

[Nome Cliente],

Vi informiamo che il [DATA] abbiamo rilevato un incidente di sicurezza
che potrebbe aver impattato i vostri dati.

COSA È SUCCESSO:
[Descrizione fattuale dell'incidente, senza speculazioni]

QUANDO È SUCCESSO:
[Timeline: quando è iniziato, quando è stato rilevato, quando è stato contenuto]

QUALI DATI SONO STATI IMPATTATI:
[Lista specifica dei tipi di dati, non "i vostri dati personali"]

COSA ABBIAMO FATTO:
[Azioni già completate: contenimento, fix, indagine]

COSA STIAMO FACENDO:
[Azioni in corso: miglioramenti, audit aggiuntivi]

COSA DOVETE FARE VOI:
[Azioni concrete: cambiare password, verificare attività, etc.]

CONTATTO:
Per domande: security@example.com | +39 XXX XXX XXXX
Status page: status.example.com

[Nome del CEO o del CISO]
```

### Bug Bounty

Programma che incentiva security researcher esterni a trovare e segnalare vulnerabilità. Piattaforme: HackerOne, Bugcrowd. Costo: $500-50.000 per vulnerabilità (in base alla severity). Complementare ai penetration test, non sostitutivo. Iniziare con un programma "responsible disclosure" (nessun compenso, solo riconoscimento) e poi evolvere in bug bounty.

```
Struttura di un programma bug bounty:

SCOPE:
  In scope:
  - *.app.example.com (applicazione web)
  - api.example.com (API)
  - mobile.example.com (app mobile web)
  Out of scope:
  - marketing.example.com (sito marketing)
  - DDoS / DoS
  - Social engineering
  - Attacchi fisici

REWARD TABLE:
  | Severity | Bounty Range  | Esempio                            |
  |----------|---------------|------------------------------------|
  | Critical | $5.000-$20.000| RCE, SQLi con data exfil, auth bypass|
  | High     | $2.000-$5.000 | XSS stored, IDOR con PII, SSRF     |
  | Medium   | $500-$2.000   | CSRF su azioni critiche, info leak  |
  | Low      | $100-$500     | Open redirect, rate limit bypass    |

REGOLE:
  - No automated scanning massivo (impatta il servizio)
  - No accesso a dati di utenti reali (usare account test)
  - No condivisione pubblica prima del fix
  - Il primo reporter valido riceve la bounty
```

---

## SOC 2 Type II — Preparazione all'Audit

### Cos'è SOC 2

SOC 2 (System and Organization Controls 2) è un framework di audit sviluppato dall'AICPA (American Institute of Certified Public Accountants). È lo standard de facto per dimostrare la sicurezza di un SaaS ai clienti enterprise.

**Differenza tra Type I e Type II:**
- **Type I**: valuta il design dei controlli in un singolo punto nel tempo. "Avete i controlli giusti?"
- **Type II**: valuta l'efficacia operativa dei controlli in un periodo (tipicamente 6-12 mesi). "I controlli funzionano davvero?"

### Trust Service Criteria (TSC)

```
I 5 Trust Service Criteria di SOC 2:

1. SECURITY (obbligatorio):
   "Il sistema è protetto contro accessi non autorizzati."
   - Firewall, WAF, IDS/IPS
   - Autenticazione e autorizzazione
   - Encryption
   - Vulnerability management
   - Incident response
   - Change management

2. AVAILABILITY (opzionale):
   "Il sistema è disponibile come concordato."
   - SLA e uptime target
   - Disaster recovery
   - Backup e restore
   - Capacity planning
   - Monitoring e alerting

3. PROCESSING INTEGRITY (opzionale):
   "Il sistema processa i dati in modo completo, accurato e tempestivo."
   - Input validation
   - Output verification
   - Error handling
   - Quality assurance
   - Data reconciliation

4. CONFIDENTIALITY (opzionale):
   "Le informazioni confidenziali sono protette."
   - Classificazione dati
   - Encryption at rest e in transit
   - Access control
   - Data retention e disposal
   - NDA con dipendenti e fornitori

5. PRIVACY (opzionale):
   "I dati personali sono raccolti, usati, conservati e distrutti in conformità."
   - Privacy policy
   - Consenso dell'utente
   - Data minimization
   - Right to access/delete
   - Cross-border transfer safeguards

Raccomandazione per SaaS:
  Anno 1: Security + Availability (il minimo per enterprise sales)
  Anno 2: aggiungere Confidentiality
  Anno 3: aggiungere Privacy se si gestiscono PII significativi
```

### Raccolta Evidenze

```
Evidenze necessarie per SOC 2 Type II:

POLICY E PROCEDURE (documenti):
  □ Information Security Policy
  □ Access Control Policy
  □ Incident Response Plan
  □ Business Continuity / Disaster Recovery Plan
  □ Change Management Policy
  □ Vendor Management Policy
  □ Data Classification Policy
  □ Acceptable Use Policy
  □ Employee Onboarding/Offboarding checklist
  □ Risk Assessment document

EVIDENZE TECNICHE (prove operative):
  □ Log di accesso (chi ha accesso a cosa, review trimestrale)
  □ MFA enforcement (screenshot di configurazione IdP)
  □ Vulnerability scan reports (Snyk, Trivy)
  □ Penetration test report (annuale)
  □ Incident log (lista incidenti con resolution)
  □ Change log (ticket/PR per ogni modifica a produzione)
  □ Backup test log (restore test periodico)
  □ Uptime report (da monitoring tool)
  □ Encryption configuration (TLS, at-rest)
  □ Network diagram con security controls

EVIDENZE HR:
  □ Background check per nuovi dipendenti
  □ Security awareness training (annuale)
  □ NDA firmati
  □ Processo di offboarding (revoca accessi)
  □ Acknowledgment delle policy (firmato da ogni dipendente)

EVIDENZE CONTINUOUS MONITORING:
  □ Allarmi configurati e funzionanti
  □ Dashboard di security (screenshot mensili)
  □ Revisione degli accessi (trimestrale)
  □ Revisione delle policy (annuale)
```

### Timeline di Preparazione

```
Timeline SOC 2 Type II (12-18 mesi):

MESI 1-2: GAP ASSESSMENT
  - Valutare lo stato attuale vs requisiti SOC 2
  - Identificare i gap (policy mancanti, controlli assenti)
  - Scegliere un auditor (Vanta, Drata, Secureframe per automazione)
  - Definire scope (quali TSC, quali sistemi)

MESI 3-4: POLICY E PROCEDURE
  - Scrivere le policy mancanti (o adattare template)
  - Implementare i controlli tecnici mancanti
  - Configurare il tool di compliance automation
  - Far firmare le policy a tutti i dipendenti

MESI 5-6: IMPLEMENTAZIONE CONTROLLI
  - Configurare logging/monitoring
  - Implementare access review automatizzata
  - Configurare vulnerability scanning
  - Test di backup/restore
  - Security awareness training

MESI 7-12: OBSERVATION PERIOD (Type II)
  - I controlli devono funzionare per 6-12 mesi
  - Raccogliere evidenze continuamente
  - Correggere eventuali eccezioni
  - L'auditor può fare check intermedi

MESE 12-14: AUDIT
  - L'auditor esamina le evidenze del periodo
  - Interviste con il team (sicurezza, engineering, HR)
  - Test dei controlli (campionamento)
  - Report preliminare con eccezioni

MESE 14-15: REPORT FINALE
  - Report SOC 2 Type II emesso
  - Condividibile con clienti sotto NDA
  - Valido per 12 mesi (poi va rinnovato)

Costo indicativo:
  - Tool di compliance (Vanta/Drata): $10.000-$50.000/anno
  - Auditor esterno: $20.000-$80.000
  - Tempo interno: 200-500 ore di lavoro
  - Totale anno 1: $50.000-$150.000
  - Rinnovo annuale: $30.000-$80.000
```

---

## ISO 27001 — Roadmap di Implementazione

### Cos'è ISO 27001

ISO/IEC 27001 è lo standard internazionale per i sistemi di gestione della sicurezza delle informazioni (ISMS — Information Security Management System). A differenza di SOC 2 (specifico per service provider USA), ISO 27001 è riconosciuto globalmente.

### Struttura della ISO 27001

```
Clausole della ISO 27001:2022:

Clausola 4: CONTESTO DELL'ORGANIZZAZIONE
  - Comprendere l'organizzazione e il suo contesto
  - Comprendere le esigenze delle parti interessate
  - Determinare l'ambito dell'ISMS
  - Sistema di gestione della sicurezza delle informazioni

Clausola 5: LEADERSHIP
  - Leadership e impegno
  - Politica per la sicurezza delle informazioni
  - Ruoli, responsabilità e autorità

Clausola 6: PIANIFICAZIONE
  - Azioni per affrontare rischi e opportunità
  - Obiettivi di sicurezza delle informazioni
  - Pianificazione delle modifiche

Clausola 7: SUPPORTO
  - Risorse
  - Competenza
  - Consapevolezza
  - Comunicazione
  - Informazioni documentate

Clausola 8: ATTIVITÀ OPERATIVE
  - Pianificazione e controllo operativi
  - Valutazione dei rischi
  - Trattamento dei rischi

Clausola 9: VALUTAZIONE DELLE PRESTAZIONI
  - Monitoraggio, misurazione, analisi e valutazione
  - Audit interni
  - Riesame della direzione

Clausola 10: MIGLIORAMENTO
  - Non conformità e azioni correttive
  - Miglioramento continuo
```

### Annex A — Controlli di Sicurezza

```
ISO 27001:2022 Annex A — 93 controlli in 4 categorie:

A.5 CONTROLLI ORGANIZZATIVI (37 controlli):
  5.1  Politiche per la sicurezza delle informazioni
  5.2  Ruoli e responsabilità
  5.3  Separazione dei compiti
  5.4  Responsabilità della direzione
  5.5  Contatto con le autorità
  5.7  Threat intelligence
  5.8  Sicurezza nella gestione dei progetti
  5.9  Inventario delle informazioni
  5.10 Uso accettabile delle informazioni
  5.23 Sicurezza per servizi cloud
  5.30 Preparazione ICT per la continuità aziendale
  ...

A.6 CONTROLLI SULLE PERSONE (8 controlli):
  6.1  Screening
  6.2  Termini e condizioni di impiego
  6.3  Consapevolezza e formazione
  6.4  Processo disciplinare
  ...

A.7 CONTROLLI FISICI (14 controlli):
  7.1  Perimetro di sicurezza fisica
  7.4  Monitoraggio della sicurezza fisica
  7.9  Sicurezza degli asset fuori sede
  7.10 Supporti di memorizzazione
  ...

A.8 CONTROLLI TECNOLOGICI (34 controlli):
  8.1  Dispositivi endpoint dell'utente
  8.2  Diritti di accesso privilegiato
  8.3  Restrizione dell'accesso alle informazioni
  8.5  Autenticazione sicura
  8.7  Protezione contro il malware
  8.8  Gestione delle vulnerabilità tecniche
  8.9  Gestione della configurazione
  8.12 Prevenzione della fuga di dati
  8.15 Logging
  8.16 Attività di monitoraggio
  8.23 Filtraggio web
  8.24 Uso della crittografia
  8.25 Ciclo di vita dello sviluppo sicuro
  8.28 Codifica sicura
  8.29 Test di sicurezza in sviluppo e accettazione
  8.31 Separazione degli ambienti
  8.33 Informazioni di test
  8.34 Protezione durante test di audit
  ...
```

### Roadmap di Implementazione

```
Timeline ISO 27001 (12-24 mesi):

FASE 1: PREPARAZIONE (Mesi 1-3)
  □ Ottenere supporto del management
  □ Definire scope dell'ISMS
  □ Nominare il responsabile ISMS (o CISO)
  □ Formare il team di progetto
  □ Gap analysis rispetto ai controlli Annex A
  □ Budget e timeline

FASE 2: RISK ASSESSMENT (Mesi 3-5)
  □ Inventario degli asset informativi
  □ Identificazione delle minacce (STRIDE/PASTA)
  □ Valutazione del rischio (probabilità × impatto)
  □ Trattamento del rischio (mitigare, accettare, trasferire, evitare)
  □ Statement of Applicability (SoA): quali controlli Annex A si applicano

FASE 3: IMPLEMENTAZIONE (Mesi 5-12)
  □ Scrivere le policy obbligatorie
  □ Implementare i controlli tecnici
  □ Implementare i controlli organizzativi
  □ Formazione del personale
  □ Documentazione delle procedure
  □ Test dei controlli

FASE 4: OPERAZIONE (Mesi 12-18)
  □ Operare l'ISMS per almeno 3-6 mesi
  □ Audit interni (almeno 1)
  □ Riesame della direzione
  □ Azioni correttive per non conformità

FASE 5: CERTIFICAZIONE (Mesi 18-24)
  □ Stage 1 Audit: revisione documentale
  □ Risolvere eventuali osservazioni
  □ Stage 2 Audit: verifica implementazione
  □ Certificazione emessa (valida 3 anni)
  □ Audit di sorveglianza annuale (anni 2 e 3)
  □ Audit di ricertificazione al terzo anno

Costo indicativo:
  - Consulenza: €20.000-€80.000
  - Tool GRC: €5.000-€30.000/anno
  - Tempo interno: 500-1500 ore
  - Audit di certificazione: €10.000-€40.000
  - Totale: €50.000-€200.000
```

### ISO 27001 vs SOC 2

```
Confronto ISO 27001 e SOC 2:

| Aspetto              | ISO 27001                    | SOC 2 Type II              |
|----------------------|------------------------------|----------------------------|
| Standard body        | ISO/IEC                      | AICPA                      |
| Ambito geografico    | Globale                      | Principalmente USA/Canada  |
| Tipo                 | Certificazione               | Attestation report         |
| Validità             | 3 anni (+ sorveglianza)      | 12 mesi                    |
| Focus                | ISMS (sistema di gestione)   | Controlli su servizio      |
| Flessibilità         | SoA personalizzabile         | TSC fissi                  |
| Costo                | €50K-200K (iniziale)         | $50K-150K (iniziale)       |
| Tempo                | 12-24 mesi                   | 12-18 mesi                 |
| Riconoscimento       | Enterprise globale           | Enterprise USA/tech        |
| Compliance GDPR      | Allineamento forte           | Parziale                   |
| Consiglio per SaaS   | Se clienti globali/EU        | Se clienti USA/tech        |

Raccomandazione: iniziare con SOC 2 (più veloce, richiesto da clienti tech USA),
poi aggiungere ISO 27001 per espansione internazionale.
Molti controlli si sovrappongono (~70%), quindi il secondo costa meno del primo.
```

---

## Matrice di Compliance per Standard

```
Matrice di controlli per standard di sicurezza:

Controllo                    | SOC 2 | ISO 27001 | GDPR | HIPAA | PCI DSS
─────────────────────────────|───────|───────────|──────|───────|────────
MFA per admin                |  ✓    |   ✓ 8.5   |  ✓   |  ✓    |   ✓
Encryption at rest           |  ✓    |   ✓ 8.24  |  ✓   |  ✓    |   ✓
Encryption in transit (TLS)  |  ✓    |   ✓ 8.24  |  ✓   |  ✓    |   ✓
Access control (RBAC)        |  ✓    |   ✓ 8.3   |  ✓   |  ✓    |   ✓
Audit logging                |  ✓    |   ✓ 8.15  |  ✓   |  ✓    |   ✓
Incident response plan       |  ✓    |   ✓ 5.24  |  ✓   |  ✓    |   ✓
Vulnerability scanning       |  ✓    |   ✓ 8.8   |      |  ✓    |   ✓
Penetration testing          |  ✓    |   ✓ 8.29  |      |       |   ✓
Data classification          |  ✓    |   ✓ 5.9   |  ✓   |  ✓    |   ✓
Backup e recovery            |  ✓    |   ✓ 8.13  |  ✓   |  ✓    |   ✓
Security awareness training  |  ✓    |   ✓ 6.3   |  ✓   |  ✓    |   ✓
Vendor risk management       |  ✓    |   ✓ 5.21  |  ✓   |  ✓    |   ✓
Change management            |  ✓    |   ✓ 8.32  |      |  ✓    |   ✓
Breach notification          |       |   ✓ 5.26  |  ✓   |  ✓    |   ✓
Data retention policy        |  ✓    |   ✓ 5.9   |  ✓   |  ✓    |   ✓
Key management               |  ✓    |   ✓ 8.24  |  ✓   |  ✓    |   ✓
Network segmentation         |  ✓    |   ✓ 8.22  |      |  ✓    |   ✓
Anti-malware                 |  ✓    |   ✓ 8.7   |      |  ✓    |   ✓
Secure SDLC                  |  ✓    |   ✓ 8.25  |      |       |   ✓
Privacy impact assessment    |       |           |  ✓   |  ✓    |
Data portability             |       |           |  ✓   |       |
Right to erasure             |       |           |  ✓   |       |
DPO (Data Protection Officer)|       |           |  ✓   |       |
BAA (Business Associate Agmt)|       |           |      |  ✓    |
PAN masking                  |       |           |      |       |   ✓
Quarterly ASV scan           |       |           |      |       |   ✓
```

---

## Security per Enterprise Sales

I clienti enterprise richiedono evidenze di sicurezza prima di acquistare:

**Security questionnaire**: 100-500 domande su pratiche di sicurezza. Preparare un repository di risposte standard. Tool: Vanta, SafeBase per automatizzare.

**SOC 2 Type II report**: la risposta definitiva alla maggior parte delle domande. Avere il SOC 2 riduce il tempo di security review del 70%.

**Penetration test annuale**: condotto da terza parte indipendente. Report condivisibile con i clienti (executive summary, non il report completo).

**Security page pubblica**: pagina sul sito con: certificazioni, pratiche di sicurezza, link al DPA, contatto per segnalazioni. Esempio: trust.company.com.

### Trust Center

```
Struttura di una Trust Page pubblica:

trust.example.com/

├── /security
│   ├── Overview delle pratiche di sicurezza
│   ├── Certificazioni (badge SOC 2, ISO 27001)
│   ├── Architettura di sicurezza (high-level)
│   ├── Encryption practices
│   └── Contatto security: security@example.com
│
├── /compliance
│   ├── Lista certificazioni con date
│   ├── SOC 2 Type II report (download sotto NDA o self-serve con email)
│   ├── Penetration test attestation
│   └── Sub-processor list
│
├── /privacy
│   ├── Privacy Policy
│   ├── Data Processing Agreement (DPA)
│   ├── Cookie Policy
│   ├── Sub-processor list con notifica di cambiamenti
│   └── GDPR / CCPA compliance statement
│
├── /status
│   ├── Uptime corrente e storico
│   ├── Incident history
│   └── Maintenance schedule
│
└── /security.txt
    └── RFC 9116 compliant

Tool per trust center automatizzato:
- SafeBase: trust center + security questionnaire automation
- Vanta Trust Center: integrato con Vanta compliance
- Drata Trust Center: integrato con Drata compliance
```

---

## Best Practices

1. **Security by Default**: MFA incoraggiata per tutti, password policy solida, encryption ovunque, principio del minimo privilegio
2. **Tenant isolation testata**: scrivere test automatici che verificano che un utente non può accedere ai dati di un altro tenant
3. **Dependency scanning automatico**: Dependabot o Snyk nella CI pipeline. Aggiornare le dipendenze vulnerabili entro 7 giorni (critiche: 24 ore)
4. **Audit log completo**: loggare ogni accesso ai dati, ogni modifica ai permessi, ogni azione admin. Immutabile (append-only), con retention di almeno 1 anno
5. **Incident response plan documentato e testato**: non aspettare il breach per scoprire che non si sa cosa fare. Simulare un incident almeno 1 volta all'anno
6. **SOC 2 il prima possibile**: è l'investimento con il miglior ROI per vendere all'enterprise
7. **No security through obscurity**: la sicurezza non dipende dal segreto dell'implementazione. Open design, peer review, bug bounty
8. **Shift Left**: integrare la sicurezza nel ciclo di sviluppo, non dopo. SAST/DAST nella CI, threat modeling nel design, security review nel code review
9. **Assume Breach**: progettare i sistemi assumendo che un attaccante sia già dentro. Segmentazione, encryption, monitoring, least privilege limitano il danno
10. **Security Champion**: in ogni team di sviluppo, una persona è il referente per la sicurezza. Non è il CISO — è uno sviluppatore con formazione e interesse in sicurezza

---

## Checklist di Hardening Step-by-Step

### Fase 1: Fondamenta (Settimana 1-2)

```
IDENTITÀ E ACCESSO:
□ Implementare autenticazione con OIDC/OAuth 2.0 (Auth0, Clerk, WorkOS)
□ Abilitare MFA obbligatoria per tutti gli account admin
□ Password policy: minimo 12 caratteri, nessuna restrizione artificiale
□ Rate limiting su endpoint di login: 5 tentativi/minuto
□ Session management: JWT con scadenza 30 minuti + refresh token 7 giorni
□ Invalidare tutte le sessioni al cambio password
□ Account lockout dopo 10 tentativi falliti consecutivi

CRITTOGRAFIA BASE:
□ TLS 1.3 su tutti gli endpoint (TLS 1.2 come fallback minimo)
□ HSTS header con max-age=31536000
□ Redirect HTTP → HTTPS (301 permanente)
□ Certificato TLS valido, auto-rinnovamento configurato
□ Encryption at rest per database (AES-256)
□ Encryption at rest per file storage (SSE-S3/SSE-KMS)

HEADER DI SICUREZZA:
□ Content-Security-Policy (CSP) configurato
□ X-Frame-Options: DENY
□ X-Content-Type-Options: nosniff
□ Referrer-Policy: strict-origin-when-cross-origin
□ Permissions-Policy: camera=(), microphone=(), geolocation=()
□ Strict-Transport-Security configurato
```

### Fase 2: Applicazione (Settimana 3-4)

```
INPUT VALIDATION:
□ Schema validation su ogni endpoint API (Zod, Joi, Pydantic)
□ Payload size limit (1 MB default, configurabile per endpoint)
□ Prepared statement per TUTTE le query SQL (no concatenazione)
□ Output encoding per prevenire XSS
□ CSRF protection (SameSite cookie + token)
□ File upload: validare tipo, dimensione, contenuto (no solo extension)

AUTORIZZAZIONE:
□ RBAC implementato con test per ogni ruolo
□ Tenant isolation verificata con Row Level Security
□ Test automatici cross-tenant in CI/CD
□ Principle of least privilege per ogni ruolo e servizio
□ No IDOR: verificare ownership per ogni richiesta

SECRET MANAGEMENT:
□ Nessun segreto nel codice sorgente
□ .env NON committato (.gitignore)
□ Segreti in AWS Secrets Manager / Vault
□ Secret scanning pre-commit (GitLeaks)
□ Rotazione API key programmatica
```

### Fase 3: Infrastruttura (Settimana 5-6)

```
RETE:
□ VPC con subnet segmentation (public/private/isolated)
□ Security Group: default deny, allow specific
□ Database NON accessibile da Internet
□ Bastion host o Session Manager per accesso admin
□ VPC Flow Logs abilitati
□ WAF configurato (OWASP rules + rate limiting)

CONTAINER:
□ Immagini base minimali (Alpine/distroless)
□ Non root: USER nel Dockerfile
□ Read-only filesystem dove possibile
□ Resource limits (CPU, memory) su ogni container
□ Container image scanning nella CI (Trivy)
□ Vulnerability scanning periodico su registry

CLOUD:
□ Root account cloud: MFA hardware, no API key
□ IAM: policy con least privilege
□ CloudTrail / Cloud Audit Log abilitato
□ GuardDuty / Security Command Center abilitato
□ S3 Block Public Access a livello account
□ IMDSv2 obbligatorio per EC2 (se AWS)
```

### Fase 4: Monitoring e Response (Settimana 7-8)

```
LOGGING:
□ Audit log per: login, accesso dati, modifiche permessi, azioni admin
□ Audit log immutabile (append-only)
□ Log centralizzati in SIEM o log management
□ Retention: minimo 90 giorni hot, 1 anno totale
□ No dati sensibili nei log (PII, token, password)

MONITORING:
□ Alert per login falliti ripetuti
□ Alert per accesso da geo/IP anomalo
□ Alert per privilege escalation
□ Alert per configurazione cloud modificata
□ Uptime monitoring su tutti gli endpoint critici
□ Certificate expiry monitoring

INCIDENT RESPONSE:
□ Piano di incident response documentato
□ Ruoli definiti (IC, Technical Lead, Communications)
□ Canale di comunicazione out-of-band (non dipende dal sistema)
□ Runbook per scenari comuni (account compromesso, data leak, DDoS)
□ Simulazione di incidente almeno 1 volta/anno
□ Contatto legale identificato per breach notification
```

### Fase 5: Compliance e Governance (Mese 3+)

```
DOCUMENTAZIONE:
□ Information Security Policy scritta e approvata
□ Acceptable Use Policy
□ Incident Response Plan
□ Business Continuity / Disaster Recovery Plan
□ Data Classification Policy
□ Vendor Management Policy
□ Privacy Policy e DPA pubblicati

PROCESSI:
□ Access review trimestrale (chi ha accesso a cosa?)
□ Vulnerability scan settimanale con report
□ Penetration test annuale da terza parte
□ Security awareness training annuale per dipendenti
□ Background check per nuovi dipendenti
□ Offboarding checklist (revoca accessi entro 24 ore)

COMPLIANCE:
□ SOC 2 Type II: avviare preparazione (vedi sezione dedicata)
□ GDPR: DPA pronto, processo per data subject requests
□ security.txt pubblicato (RFC 9116)
□ Responsible disclosure policy pubblicata
□ Sub-processor list aggiornata e pubblica
```

---

## Troubleshooting

**"Cliente enterprise richiede SSO ma non l'abbiamo"** → SSO (SAML/OIDC) è un requisito non negoziabile per enterprise. Implementare con un identity provider (Auth0, WorkOS, Clerk). WorkOS è specificamente progettato per SaaS che devono aggiungere SSO rapidamente. Timeline: 2-4 settimane.

**"Vulnerability disclosure: qualcuno ha trovato un bug"** → Non ignorare, non minacciare azioni legali. Ringraziare il researcher, confermare la ricezione entro 24 ore, valutare la severity, patchare e comunicare la timeline. Rispettare il disclosure timeline (tipicamente 90 giorni).

**"Sospetto data breach"** → Attivare l'incident response plan. Containment immediato (isolare, revocare credenziali). NON comunicare prima di avere i fatti. Coinvolgere il legale. Notificare il Garante entro 72 ore (GDPR). Comunicare ai clienti impattati con trasparenza.

**"Security questionnaire da compilare per un deal enterprise"** → Preparare un repository di risposte standard (Vanta, SafeBase). Avere SOC 2, penetration test report, e DPA pronti. La prima volta è dolorosa; le successive sono copia-incolla.

**"JWT rubato — sessione compromessa"** → Revocare il refresh token associato. Con JWT, il token rimane valido fino alla scadenza (non revocabile senza blacklist). Mitigazione: scadenza breve (15-30 minuti), blacklist dei JWT revocati in Redis (check a ogni richiesta), binding del JWT all'IP o al device fingerprint.

**"SQL injection trovata in produzione"** → Severity CRITICAL. Containment: se possibile, disabilitare l'endpoint vulnerabile o applicare WAF rule. Fix: convertire a prepared statement. Investigare: analizzare i log per capire se è stata sfruttata. Se dati estratti: attivare procedura di breach notification.

**"Credenziali committate in Git"** → Il segreto è compromesso anche se il commit viene rimosso (la git history lo preserva). Azione immediata: revocare/ruotare il segreto. Poi: rimuovere dalla history (git filter-branch o BFG Repo-Cleaner). Prevenzione: installare GitLeaks come pre-commit hook.

**"DDoS in corso — il servizio è down"** → Attivare la protezione DDoS del CDN/cloud provider (Cloudflare Under Attack Mode, AWS Shield Advanced). Scalare l'infrastruttura se possibile. Identificare il pattern di attacco (layer 3/4 vs layer 7). Per layer 7: rate limiting aggressivo, CAPTCHA, blocco IP/range. Comunicare su status page.

**"Dipendenza con CVE critico (CVSS 9+)"** → Verificare se la vulnerabilità è effettivamente raggiungibile nel contesto dell'applicazione (non tutte le CVE sono exploitable). Se raggiungibile: aggiornare entro 24 ore. Se non aggiornabile: workaround (WAF rule, disabilitare feature). Documentare la decisione.

**"Cliente richiede che i dati risiedano in EU"** → Data residency è un requisito comune per GDPR. Opzioni: 1) Multi-region deployment con routing basato sulla regione dell'account. 2) Specific cloud region (eu-west-1, europe-west1). 3) Per tenant enterprise: deployment dedicato in regione. Verificare anche i sub-processor: dove risiedono i dati dei servizi terzi?

**"Penetration tester ha trovato IDOR"** → IDOR (Insecure Direct Object Reference) = un utente può accedere a risorse di altri utenti cambiando l'ID nella URL. Fix: verificare l'ownership della risorsa in ogni handler. Usare UUID invece di ID sequenziali (riduce l'enumerazione ma NON è un fix di sicurezza). Test: scrivere test automatici che verificano l'accesso cross-user e cross-tenant.

**"Alert di impossible travel: utente loggato da 2 paesi in 1 ora"** → Possibili cause: VPN (falso positivo), account compromesso (vero positivo). Azione: richiedere ri-autenticazione MFA alla prossima richiesta. Se MFA non configurato: forzare reset password. Notificare l'utente via email. Analizzare le azioni eseguite dalle sessioni sospette.

**"Container con vulnerabilità critica nel base image"** → Rebuild immediato con base image aggiornata. Verificare che il fix sia effettivo con scan post-build. Se l'immagine base non ha un fix disponibile: valutare immagine base alternativa. Implementare rebuild periodico automatico (weekly) per ridurre il drift.

**"Log mostrano accesso a dati di altro tenant"** → Severity CRITICAL. Questo è un data breach. Containment: identificare e disabilitare il percorso di accesso. Analisi: quanto è durato? Quanti tenant impattati? Quali dati esposti? Se PII: notifica obbligatoria (GDPR 72 ore). Comunicare a TUTTI i tenant potenzialmente impattati, anche se non c'è certezza di accesso.

**"SOC 2 auditor ha trovato un'eccezione"** → Un'eccezione non è automaticamente un fallimento dell'audit. L'auditor documenta l'eccezione nel report. Il SaaS deve: 1) Spiegare la root cause. 2) Descrivere le azioni correttive. 3) Dimostrare che i controlli compensativi erano in atto. Un report con poche eccezioni minori è comunque accettabile per i clienti.

**"Webhook endpoint sotto attacco (richieste false)"** → Verificare la firma HMAC-SHA256 del webhook su OGNI richiesta. Rifiutare richieste senza firma valida. Verificare il timestamp (tolleranza ±5 minuti per prevenire replay). Rate limiting sull'endpoint webhook. Logging di tutte le richieste rifiutate per analisi.

---

## FAQ — Domande Frequenti

**D: Devo avere SOC 2 prima di vendere all'enterprise?**
R: Non strettamente necessario, ma accelera enormemente il processo di vendita. Senza SOC 2, ogni deal enterprise richiede un security review manuale di 2-6 mesi. Con SOC 2, il review si riduce a 1-2 settimane. Iniziare il percorso SOC 2 quando si hanno i primi 2-3 clienti enterprise interessati, non prima (è costoso per una startup early-stage). In alternativa, iniziare con un security questionnaire pre-compilato e un penetration test report.

**D: RBAC o ABAC? Quale scegliere?**
R: RBAC per il 90% dei SaaS. È più semplice da implementare, debuggare e spiegare ai clienti. ABAC quando i permessi dipendono da attributi dinamici (orario, geolocalizzazione, classificazione del documento). ReBAC (basato su relazioni, stile Google Zanzibar) è la scelta migliore per SaaS con condivisione complessa (documenti condivisi, team gerarchici, permessi ereditati). Consiglio: iniziare con RBAC, evolvere a ReBAC quando il modello di sharing lo richiede.

**D: JWT o session cookie?**
R: JWT per API stateless (backend-for-frontend, mobile app, API pubblica). Session cookie per applicazioni web tradizionali (più semplice da revocare). Il pattern più comune nei SaaS moderni: JWT con scadenza breve (15-30 min) + refresh token opaco in database + sessione lato server come fallback per revoca immediata.

**D: Quanto costano SOC 2 e ISO 27001?**
R: SOC 2 Type II primo anno: $50.000-$150.000 (tool + auditor + tempo interno). Rinnovo: $30.000-$80.000/anno. ISO 27001 certificazione: €50.000-€200.000 (consulenza + auditor + tempo interno). Sorveglianza annuale: €10.000-€40.000. Il secondo standard costa meno del primo grazie alla sovrapposizione dei controlli (~70%).

**D: Multi-tenant o single-tenant per enterprise?**
R: Multi-tenant con tenant isolation rigorosa per la maggior parte dei clienti. Single-tenant (deploy dedicato) per clienti che lo richiedono contrattualmente (banche, sanità, difesa). Il modello ibrido è il più pragmatico: pool per SMB, bridge per mid-market, silo per enterprise regolamentati. Progettare per multi-tenant dal giorno 1 — passare da single a multi è costoso.

**D: Ogni quanto fare penetration test?**
R: Almeno annualmente (requisito SOC 2 e standard di mercato). Dopo ogni major release che modifica auth, autorizzazione, o gestione dati. Dopo cambio significativo dell'architettura. DAST automatico settimanale complementa il pen test manuale. Budget il pen test come costo operativo ricorrente, non come spesa una tantum.

**D: Come gestire la data residency (GDPR)?**
R: Opzioni in ordine di complessità crescente: 1) Scegliere una regione EU per tutti i dati (semplice, limita la latenza per clienti extra-EU). 2) Multi-region con routing per tenant (il tenant sceglie la regione). 3) Deploy separato per regione (massimo controllo, massima complessità operativa). Per i sub-processor: verificare dove processano i dati e avere DPA con ciascuno. Il GDPR non vieta il trasferimento extra-EU, ma richiede safeguard (Standard Contractual Clauses, adequacy decision).

**D: Bug bounty o penetration test? Sono alternativi?**
R: Complementari, non alternativi. Il penetration test è un assessment strutturato, limitato nel tempo, condotto da professionisti selezionati. Il bug bounty è continuo, con molti più occhi, ma meno profondità. Consiglio: iniziare con pen test annuale + programma di responsible disclosure (senza compenso). Quando il prodotto è maturo e il budget lo consente, evolvere in bug bounty (HackerOne, Bugcrowd).

**D: Come proteggere le API key dei clienti?**
R: Mai salvare in chiaro. Salvare l'hash SHA-256 della key nel database (come una password). Mostrare la key completa SOLO una volta, alla creazione. Consentire al cliente di ruotare la key (ne crea una nuova, invalida la vecchia). Formato consigliato: prefisso identificativo + segreto (es: sk_live_abc123def456). Il prefisso è salvato in chiaro per identificare la key nei log senza esporre il segreto.

**D: Che fare se un dipendente viene licenziato e aveva accesso a produzione?**
R: Revocare TUTTI gli accessi entro 1 ora dall'uscita. Checklist: disabilitare SSO, revocare VPN, rimuovere da cloud console, ruotare secret condivisi, invalidare sessioni attive, recuperare hardware aziendale, revocare accesso a repo Git, rimuovere da canali Slack/Teams, disabilitare email. Se l'uscita è conflittuale: monitorare i log per 30 giorni per accessi anomali con credenziali residue.

**D: Devo cifrare tutto il database o solo alcuni campi?**
R: Disk-level encryption (FDE) per TUTTO il database: è trasparente e protegge da furto fisico. Column-level encryption per campi altamente sensibili (SSN, carte di credito, dati sanitari): protegge anche da DBA e da SQL injection che estrae dati. Application-level encryption per dati dove anche il SaaS provider non dovrebbe avere accesso in chiaro (end-to-end encryption per messaggi, zero-knowledge encryption per vault).

**D: Come rispondo a un security questionnaire di 500 domande?**
R: La prima volta è dolorosa (40-80 ore). Dopo, è gestibile. Strategia: 1) Usare un tool (Vanta, SafeBase, Conveyor) che pre-popola risposte e impara dalle precedenti. 2) Avere SOC 2: risponde al 70% delle domande automaticamente. 3) Creare un repository di risposte standard per le domande più comuni. 4) Pubblicare un security whitepaper che copre le domande frequenti. 5) Per domande specifiche: coinvolgere l'SME giusto (DevOps per infra, Legal per privacy, Engineering per app security).

**D: WebAuthn/Passkey è pronto per la produzione?**
R: Sì. Supportato da tutti i browser moderni (Chrome, Firefox, Safari, Edge). I passkey sincronizzati (iCloud Keychain, Google Password Manager) risolvono il problema del recovery. Per un SaaS: offrire passkey come opzione MFA (non come unico metodo — supportare anche TOTP/authenticator app). Librerie server mature: SimpleWebAuthn (Node.js), py_webauthn (Python), webauthn-rs (Rust).

**D: Quanto costa un data breach per un SaaS?**
R: Il costo medio globale è $4.8M (2025). Per un SaaS: il costo principale è il churn. Un breach pubblica causa 10-30% di churn nei 12 mesi successivi. A questo si aggiungono: consulenza forense ($200-500/ora), notifiche ai clienti ($1-5 per persona), sanzioni GDPR (fino al 4% del fatturato), costi legali ($100K-1M+), costi di remediation ($50K-500K). Per una startup SaaS, un breach può essere un evento di estinzione. Investire in sicurezza è sempre meno costoso di un breach.

**D: Come implementare la cancellazione dei dati richiesta dal GDPR (diritto all'oblio)?**
R: Implementare un processo tecnico e organizzativo: 1) API endpoint per richiesta di cancellazione (self-serve o via support). 2) Verificare l'identità del richiedente. 3) Identificare TUTTI i sistemi dove i dati dell'utente risiedono (database, cache, backup, log, analytics, servizi terzi). 4) Soft delete immediato (dati non più accessibili). 5) Hard delete entro 30 giorni da tutti i sistemi attivi. 6) Backup: i dati nei backup saranno cancellati alla prossima rotazione (documentare il retention period). 7) Log e audit trail: possono essere conservati in forma anonimizzata. 8) Conferma scritta al richiedente entro 30 giorni.

**D: Come gestire la sicurezza quando si usa un ORM invece di query SQL dirette?**
R: L'ORM previene la SQL injection per design (usa prepared statement internamente). Attenzione ai pericoli: 1) Raw query nell'ORM: se l'ORM permette query raw, usare SEMPRE prepared statement. 2) Mass assignment: non esporre tutti i campi del modello — definire esplicitamente quali campi sono modificabili. 3) N+1 query: non è un problema di sicurezza ma di disponibilità (DoS accidentale). 4) Serializzazione: non serializzare automaticamente il modello ORM in JSON — usare un serializer esplicito che esclude campi sensibili (password_hash, secret, internal_notes).
