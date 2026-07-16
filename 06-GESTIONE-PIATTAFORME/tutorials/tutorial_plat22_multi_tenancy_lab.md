# Tutorial: Multi-Tenancy — vCluster, Namespace Isolation e PostgreSQL RLS

> **Documento di riferimento:** `22-multi-tenancy-isolation.md`
> **Dominio:** Gestione Piattaforme — Architetture Avanzate
> **Ambito:** Modelli multi-tenant (silo/pool/bridge), namespace isolation con NetworkPolicy e ResourceQuota, vCluster per tenant isolation hard, Row-Level Security PostgreSQL, noisy neighbor prevention, onboarding automatizzato
> **Durata lab:** 6-7 ore
> **Livello:** Avanzato — richiede K3s cluster, Docker, PostgreSQL, helm
> **Prerequisiti:** K3s cluster locale, helm 3.x, kubectl, Docker Engine, Python 3.10+
> **Ambiente:** vCluster 0.20.x su K3s, PostgreSQL 17 via Docker, script Python per RLS demo

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI MULTI-TENANCY LAB ===
echo "=== PREREQUISITI ==="

kubectl version --client --short 2>/dev/null && echo "[OK] kubectl" || echo "[FAIL] kubectl richiesto"
helm version --short 2>/dev/null && echo "[OK] helm" || echo "[FAIL] helm richiesto"
docker --version && echo "[OK] Docker" || echo "[FAIL] Docker richiesto"

# vCluster CLI
if ! command -v vcluster &>/dev/null; then
  curl -sSfL https://github.com/loft-sh/vcluster/releases/download/v0.20.0/vcluster-linux-amd64 \
    -o /usr/local/bin/vcluster && chmod +x /usr/local/bin/vcluster
  echo "[OK] vCluster CLI installato"
fi

vcluster version 2>/dev/null | head -2

mkdir -p ~/multitenancy-lab/{tenants,rls,vcluster,networking,quotas}
cd ~/multitenancy-lab

echo "[OK] Directory lab: ~/multitenancy-lab"
```

### Modelli Multi-Tenancy a Confronto

```
┌──────────────────────────────────────────────────────────────────────────┐
│              MULTI-TENANCY — TRE MODELLI                                 │
│                                                                          │
│  SILO (isolamento completo):                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│  │ Tenant A    │  │ Tenant B    │  │ Tenant C    │                    │
│  │ K8s cluster │  │ K8s cluster │  │ K8s cluster │                    │
│  │ DB istanza  │  │ DB istanza  │  │ DB istanza  │                    │
│  └─────────────┘  └─────────────┘  └─────────────┘                    │
│  Pro: massimo isolamento, compliance facile                              │
│  Contro: costo alto, overhead operativo moltiplicato                    │
│                                                                          │
│  POOL (risorse condivise):                                              │
│  ┌───────────────────────────────────────────────┐                     │
│  │           CLUSTER K8S CONDIVISO               │                     │
│  │  Namespace-A │ Namespace-B │ Namespace-C      │                     │
│  │  (tenant-A)  │ (tenant-B)  │ (tenant-C)       │                     │
│  │              DB: RLS per tenant               │                     │
│  └───────────────────────────────────────────────┘                     │
│  Pro: costo basso, semplice da gestire                                  │
│  Contro: noisy neighbor, blast radius alto                              │
│                                                                          │
│  BRIDGE (via vCluster):                                                 │
│  ┌───────────────────────────────────────────────┐                     │
│  │           HOST CLUSTER K8S                    │                     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │                    │
│  │  │ vCluster │  │ vCluster │  │ vCluster │    │                    │
│  │  │ tenant-A │  │ tenant-B │  │ tenant-C │    │                    │
│  │  │ (API K8s │  │ (API K8s │  │ (API K8s │    │                    │
│  │  │ dedicato)│  │ dedicato)│  │ dedicato)│    │                    │
│  │  └──────────┘  └──────────┘  └──────────┘    │                    │
│  └───────────────────────────────────────────────┘                     │
│  Pro: K8s API isolato per tenant, costo contenuto                       │
│  Contro: complessità overhead, non adatto per compliance stretta        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Multi-Tenancy in K8s

> Pensate a un condominio. Ogni appartamento è separato dagli altri,
> ma il palazzo condivide fondamenta, ascensore e riscaldamento centralizzato.
> Se l'inquilino dell'appartamento 3 mette su una festa rumorosa (noisy neighbor),
> gli altri inquilini ne risentono.
> In Kubernetes, il "rumore" si traduce in CPU/memoria consumate senza limiti,
> connessioni al database esaurite, o picchi di rete che degradano gli altri tenant.
> ResourceQuota, NetworkPolicy e LimitRange sono i "regolamenti del condominio".

---

### Concetto A1: Tipi di Isolamento

```
ISOLAMENTO IN KUBERNETES — LIVELLI:

1. PROCESSO (più debole):
   - Container isolation via namespaces Linux (PID, NET, MNT)
   - seccomp/AppArmor: filtro syscall
   - Non è isolamento tenant: processi su stesso kernel

2. NAMESPACE K8S:
   - RBAC: chi può fare cosa in questo namespace
   - ResourceQuota: max risorse per namespace
   - NetworkPolicy: traffico consentito/bloccato
   - Stesso kernel, stesso kube API → non adatto per compliance stretta

3. VCLUSTER (virtual cluster):
   - K8s API Server dedicato per ogni tenant (nel namespace host)
   - ETCD separato per ogni vCluster
   - Workload girano come normali pod nel cluster host
   - Tenant gestisce il proprio namespace autonomamente
   - Pro: ogni tenant ha kubectl autonomo, senza toccare il cluster host

4. CLUSTER SEPARATO (più forte):
   - Isolamento completo: kernel, rete, etcd, API
   - Per compliance: PCI-DSS, ISO27001 con dati separati fisicamente
   - Costo alto: ogni cluster ha i suoi control plane

SCELTA:
  SaaS startup (basso budget): namespace pool + RLS PostgreSQL
  SaaS crescita: vCluster per tenant premium, namespace per basic
  Enterprise regulated: cluster separati per dato sensibile
```

---

## PART B: NAMESPACE ISOLATION

### Esercizio B1: ResourceQuota e LimitRange

```bash
cd ~/multitenancy-lab

# Script di onboarding tenant (crea namespace + quota + network policy)
cat > tenants/onboard-tenant.sh << 'SCRIPT'
#!/bin/bash
# Onboarding Tenant — crea ambiente isolato in K8s

TENANT_NAME="${1:?Specificare nome tenant}"
TIER="${2:-basic}"    # basic, professional, enterprise

NAMESPACE="tenant-${TENANT_NAME}"
echo "=== ONBOARDING TENANT: ${TENANT_NAME} (tier: ${TIER}) ==="

# Tier → risorse allocate
case "$TIER" in
  basic)
    CPU_REQUESTS="2"     # max 2 core totali
    MEM_REQUESTS="4Gi"
    CPU_LIMITS="4"
    MEM_LIMITS="8Gi"
    MAX_PODS="20"
    MAX_SERVICES="10"
    ;;
  professional)
    CPU_REQUESTS="8"
    MEM_REQUESTS="16Gi"
    CPU_LIMITS="16"
    MEM_LIMITS="32Gi"
    MAX_PODS="100"
    MAX_SERVICES="50"
    ;;
  enterprise)
    CPU_REQUESTS="32"
    MEM_REQUESTS="64Gi"
    CPU_LIMITS="64"
    MEM_LIMITS="128Gi"
    MAX_PODS="500"
    MAX_SERVICES="200"
    ;;
esac

# 1. Creare namespace con labels
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace "$NAMESPACE" \
  "tenant=${TENANT_NAME}" \
  "tier=${TIER}" \
  "managed-by=platform-team" \
  "isolation=namespace-based"

echo "[OK] Namespace creato: $NAMESPACE"

# 2. ResourceQuota — limiti assoluti del namespace
kubectl apply -f - << EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: ${NAMESPACE}
spec:
  hard:
    requests.cpu: "${CPU_REQUESTS}"
    requests.memory: "${MEM_REQUESTS}"
    limits.cpu: "${CPU_LIMITS}"
    limits.memory: "${MEM_LIMITS}"
    pods: "${MAX_PODS}"
    services: "${MAX_SERVICES}"
    persistentvolumeclaims: "10"
    secrets: "20"
    configmaps: "20"
EOF

echo "[OK] ResourceQuota applicata (tier=$TIER)"

# 3. LimitRange — default per ogni container nel namespace
kubectl apply -f - << EOF
apiVersion: v1
kind: LimitRange
metadata:
  name: tenant-limit-range
  namespace: ${NAMESPACE}
spec:
  limits:
    - type: Container
      default:
        cpu: "200m"
        memory: "256Mi"
      defaultRequest:
        cpu: "100m"
        memory: "128Mi"
      max:
        cpu: "2000m"
        memory: "4Gi"
      min:
        cpu: "50m"
        memory: "64Mi"
    - type: PersistentVolumeClaim
      max:
        storage: "50Gi"
      min:
        storage: "1Gi"
EOF

echo "[OK] LimitRange applicata"

# 4. NetworkPolicy — isolamento di rete
kubectl apply -f - << EOF
# Default deny: nessun traffico in/out
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: ${NAMESPACE}
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
EOF

kubectl apply -f - << EOF
# Permittiamo traffico ingress da ingress controller
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-from-controller
  namespace: ${NAMESPACE}
spec:
  podSelector: {}
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
EOF

kubectl apply -f - << EOF
# Permettiamo DNS egress (porta 53)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: ${NAMESPACE}
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
EOF

echo "[OK] NetworkPolicy applicate (default-deny + allow-ingress + allow-dns)"

# 5. ServiceAccount e RBAC per il tenant
kubectl create serviceaccount "tenant-${TENANT_NAME}-sa" -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f - << EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: tenant-operator-role
  namespace: ${NAMESPACE}
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps"]
    verbs: ["get", "list", "watch", "create", "update", "delete"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets"]
    verbs: ["get", "list", "watch", "create", "update", "delete"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list"]    # sola lettura sui secrets
EOF

kubectl create rolebinding "tenant-${TENANT_NAME}-binding" \
  --role="tenant-operator-role" \
  --serviceaccount="${NAMESPACE}:tenant-${TENANT_NAME}-sa" \
  -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

echo "[OK] RBAC configurato"
echo ""
echo "=== TENANT ${TENANT_NAME} ONBOARDED ==="
echo "  Namespace: ${NAMESPACE}"
echo "  Tier: ${TIER}"
echo "  CPU: ${CPU_REQUESTS} req / ${CPU_LIMITS} lim"
echo "  Memory: ${MEM_REQUESTS} req / ${MEM_LIMITS} lim"
SCRIPT

chmod +x tenants/onboard-tenant.sh

# Onboarding due tenant di esempio
bash tenants/onboard-tenant.sh acme-corp professional
bash tenants/onboard-tenant.sh startup-xyz basic

echo ""
echo "=== STATO NAMESPACE TENANT ==="
kubectl get namespaces -l managed-by=platform-team
kubectl get resourcequota -A | grep tenant
```

---

## PART C: POSTGRESQL ROW-LEVEL SECURITY

### Esercizio C1: RLS per Isolamento Dati

```bash
cd ~/multitenancy-lab

# Avviare PostgreSQL per il lab RLS
docker run -d \
  --name postgres-rls \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin-password \
  -e POSTGRES_DB=saasdb \
  -p 5432:5432 \
  postgres:17-alpine

sleep 5
echo "[OK] PostgreSQL avviato"

# Configurare RLS
docker exec -i postgres-rls psql -U admin -d saasdb << 'SQL'
-- ============================================================
-- SETUP MULTI-TENANT CON ROW-LEVEL SECURITY (RLS)
-- ============================================================

-- Tabella tenant: registry dei tenant
CREATE TABLE tenants (
    tenant_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,
    plan        TEXT CHECK (plan IN ('basic', 'professional', 'enterprise')),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO tenants (name, plan) VALUES
    ('acme-corp', 'professional'),
    ('startup-xyz', 'basic');

-- Tabella principale: ordini (per tutti i tenant nello stesso table)
-- MODELLO POOL: un'unica tabella condivisa, isolamento via RLS
CREATE TABLE orders (
    order_id    SERIAL PRIMARY KEY,
    tenant_id   UUID NOT NULL REFERENCES tenants(tenant_id),
    customer    TEXT NOT NULL,
    amount      DECIMAL(10,2) NOT NULL,
    status      TEXT DEFAULT 'pending',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Dati di test: ordini misti di due tenant
INSERT INTO orders (tenant_id, customer, amount) VALUES
    ((SELECT tenant_id FROM tenants WHERE name='acme-corp'), 'Cliente A1', 500.00),
    ((SELECT tenant_id FROM tenants WHERE name='acme-corp'), 'Cliente A2', 1200.50),
    ((SELECT tenant_id FROM tenants WHERE name='startup-xyz'), 'Cliente B1', 99.99),
    ((SELECT tenant_id FROM tenants WHERE name='startup-xyz'), 'Cliente B2', 49.90);

-- ============================================================
-- ABILITARE ROW-LEVEL SECURITY
-- ============================================================

-- STEP 1: abilitare RLS sulla tabella
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- STEP 2: FORCE RLS anche per i table owner (sicurezza aggiuntiva)
ALTER TABLE orders FORCE ROW LEVEL SECURITY;

-- STEP 3: creare policy RLS
-- La policy controlla QUALI righe ogni utente può vedere/modificare

-- Policy SELECT: ogni connessione vede solo i propri ordini
CREATE POLICY tenant_isolation_select ON orders
    FOR SELECT
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- Policy INSERT: può inserire solo per il proprio tenant
CREATE POLICY tenant_isolation_insert ON orders
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.tenant_id')::UUID);

-- Policy UPDATE: può aggiornare solo i propri ordini
CREATE POLICY tenant_isolation_update ON orders
    FOR UPDATE
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- Policy DELETE: può eliminare solo i propri ordini
CREATE POLICY tenant_isolation_delete ON orders
    FOR DELETE
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- ============================================================
-- UTENTI APPLICAZIONE (uno per tenant — o uno unico per l'app)
-- ============================================================

-- Utente unico per l'applicazione (imposta il tenant via SET)
CREATE USER app_user WITH PASSWORD 'app-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON orders TO app_user;
GRANT SELECT ON tenants TO app_user;
GRANT USAGE ON SEQUENCE orders_order_id_seq TO app_user;

-- Utente admin per bypass RLS (analytics, reporting)
CREATE USER admin_user WITH PASSWORD 'admin-user-password';
GRANT ALL ON ALL TABLES IN SCHEMA public TO admin_user;
-- admin_user bypassa RLS se ha BYPASSRLS: ALTER USER admin_user BYPASSRLS;

SELECT 'RLS configurata correttamente' AS status;
SQL

echo "[OK] PostgreSQL RLS configurato"
```

---

### Esercizio C2: Demo RLS in Python

```bash
cat > rls/rls_demo.py << 'PYTHON'
"""
Demo Row-Level Security PostgreSQL con Python.
Dimostra che ogni "connessione tenant" vede solo i propri dati.
"""
import psycopg2
from contextlib import contextmanager
from uuid import UUID

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "saasdb",
    "user": "app_user",
    "password": "app-password"
}

ADMIN_CONFIG = {
    **DB_CONFIG,
    "user": "admin",
    "password": "admin-password"
}


@contextmanager
def tenant_connection(tenant_name: str):
    """
    Context manager che imposta il tenant context.
    L'app imposta app.tenant_id PRIMA di ogni query.
    RLS usa current_setting('app.tenant_id') per filtrare le righe.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # Prima operazione: leggere il tenant_id dal nome
            cur.execute(
                "SELECT tenant_id FROM tenants WHERE name = %s",
                (tenant_name,)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Tenant non trovato: {tenant_name}")
            
            tenant_id = str(row[0])
            
            # Impostare il contesto per questa transazione
            # RLS usa current_setting() per filtrare automaticamente
            cur.execute(
                "SET LOCAL app.tenant_id = %s",
                (tenant_id,)
            )
        
        yield conn, tenant_id
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def demo_rls():
    print("=" * 60)
    print("DEMO ROW-LEVEL SECURITY — ISOLAMENTO TENANT")
    print("=" * 60)
    
    # ── Test 1: acme-corp vede solo i propri ordini ─────────────
    print("\n--- Tenant: acme-corp ---")
    with tenant_connection("acme-corp") as (conn, tenant_id):
        with conn.cursor() as cur:
            cur.execute("SELECT order_id, customer, amount FROM orders ORDER BY order_id")
            rows = cur.fetchall()
            print(f"  Ordini visibili (tenant_id={tenant_id[:8]}...):")
            for row in rows:
                print(f"    [OK] order_id={row[0]} customer={row[1]} amount={row[2]}")
    
    # ── Test 2: startup-xyz vede solo i propri ordini ───────────
    print("\n--- Tenant: startup-xyz ---")
    with tenant_connection("startup-xyz") as (conn, tenant_id):
        with conn.cursor() as cur:
            cur.execute("SELECT order_id, customer, amount FROM orders ORDER BY order_id")
            rows = cur.fetchall()
            print(f"  Ordini visibili (tenant_id={tenant_id[:8]}...):")
            for row in rows:
                print(f"    [OK] order_id={row[0]} customer={row[1]} amount={row[2]}")
    
    # ── Test 3: acme NON PUÒ vedere ordini startup-xyz ──────────
    print("\n--- Test cross-tenant access (deve fallire) ---")
    with tenant_connection("acme-corp") as (conn, _):
        with conn.cursor() as cur:
            # Tentativo di leggere tutti gli ordini ignorando il tenant
            cur.execute("SELECT count(*) FROM orders")
            total = cur.fetchone()[0]
            
            # Recuperare tenant_id di startup-xyz (simulazione tentativo)
            conn2 = psycopg2.connect(**ADMIN_CONFIG)
            with conn2.cursor() as cur2:
                cur2.execute("SELECT tenant_id FROM tenants WHERE name='startup-xyz'")
                startup_id = str(cur2.fetchone()[0])
            conn2.close()
            
            # Tentativo diretto (bypass SET LOCAL non funziona in stessa transazione)
            cur.execute(
                "SELECT count(*) FROM orders WHERE tenant_id = %s",
                (startup_id,)
            )
            crossed = cur.fetchone()[0]
            
            print(f"  Total ordini visibili a acme: {total}")
            print(f"  Ordini startup-xyz visibili a acme (deve essere 0): {crossed}")
            
            if crossed == 0:
                print("  [OK] Cross-tenant data leakage PREVENUTO dalla RLS!")
            else:
                print("  [FAIL] RLS NON sta funzionando!")
    
    # ── Test 4: Insert con tenant sbagliato (deve fallire) ──────
    print("\n--- Test insert con tenant_id sbagliato (deve essere bloccato) ---")
    
    try:
        with tenant_connection("startup-xyz") as (conn, startup_id):
            # Recuperare acme tenant_id
            with psycopg2.connect(**ADMIN_CONFIG) as admin_conn:
                with admin_conn.cursor() as cur:
                    cur.execute("SELECT tenant_id FROM tenants WHERE name='acme-corp'")
                    acme_id = str(cur.fetchone()[0])
            
            with conn.cursor() as cur:
                # Tentativo: inserire ordine con tenant_id di ACME mentre connesso come STARTUP
                cur.execute(
                    "INSERT INTO orders (tenant_id, customer, amount) VALUES (%s, %s, %s)",
                    (acme_id, "Hacker", 99999.99)
                )
            conn.commit()
            print("  [FAIL] Insert cross-tenant riuscito — RLS non funziona!")
    except psycopg2.errors.CheckViolation:
        print("  [OK] Insert cross-tenant bloccato dalla policy WITH CHECK!")
    except Exception as e:
        print(f"  [INFO] Errore (comportamento atteso): {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("RIEPILOGO:")
    print("  acme-corp vede SOLO i propri ordini: ✓")
    print("  startup-xyz vede SOLO i propri ordini: ✓")
    print("  Cross-tenant leakage prevenuto: ✓")
    print("  Insert cross-tenant bloccato: ✓")


if __name__ == "__main__":
    demo_rls()
PYTHON

pip3 install psycopg2-binary 2>/dev/null
python3 rls/rls_demo.py
```

---

## PART D: VCLUSTER — K8S VIRTUALE PER TENANT

### Esercizio D1: Setup vCluster

```bash
cd ~/multitenancy-lab

echo "=== VCLUSTER — KUBERNETES VIRTUALE PER TENANT ==="

# vCluster: ogni tenant ha il proprio K8s API server (etcd + kube-api-server)
# ma i workload girano come pod nel cluster host

# Creare namespace host per il vCluster del tenant
kubectl create namespace vcluster-acme --dry-run=client -o yaml | kubectl apply -f -

# Installare vCluster per tenant acme-corp
helm repo add loft-sh https://charts.loft.sh --force-update
helm repo update

helm upgrade --install acme-vcluster loft-sh/vcluster \
  --namespace vcluster-acme \
  --create-namespace \
  --set controlPlane.distro.k3s.enabled=true \
  --set controlPlane.coredns.embedded=true \
  --set sync.toHost.ingresses.enabled=true \
  --wait \
  --timeout 120s

kubectl -n vcluster-acme get pods

echo "[OK] vCluster per acme-corp creato"

# Connettersi al vCluster (ottiene kubeconfig dedicato)
echo ""
echo "--- Connessione al vCluster acme ---"
vcluster connect acme-vcluster \
  --namespace vcluster-acme \
  --update-current=false \
  --print 2>/dev/null | head -5 || \
  echo "[INFO] vCluster in avvio — attendere 30 secondi"

sleep 30

# Verificare che il vCluster abbia il proprio namespace
vcluster connect acme-vcluster --namespace vcluster-acme -- \
  kubectl get namespaces 2>/dev/null || \
  echo "[INFO] Connessione: vcluster connect acme-vcluster --namespace vcluster-acme"

echo ""
echo "=== CONFRONTO: VCLUSTER VS NAMESPACE ==="
cat << 'COMPARISON'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NAMESPACE ISOLATION vs VCLUSTER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                        Namespace       vCluster
Isolamento API K8s      No              Sì (API dedicato)
ETCD                    Condiviso       Dedicato per vCluster
Costo overhead          Nessuno         ~500MB RAM + CPU
Tenant admin cluster    No              Sì (sono "admin")
CRD per tenant          No              Sì (CRD isolate)
NetworkPolicy           Richiesta       Inclusa nel vCluster
Blast radius            Alto            Basso
Compliance stretta      Difficile       Più facile
Tempo setup             Secondi         2-5 minuti
Scalabilità             Alta            Medio-alta

QUANDO USARE VCLUSTER:
  ✓ Tenant premium che richiedono isolamento K8s API
  ✓ Tenant con CRD customizzate (non condivisibili)
  ✓ Tenant che devono essere "cluster admin" del proprio env
  ✓ Testing: CI/CD con cluster K8s temporanei

QUANDO USARE NAMESPACE:
  ✓ Molti tenant (>100): overhead vCluster troppo alto
  ✓ Tenant trust simile (stesso livello di sicurezza)
  ✓ Costo è il vincolo principale
  ✓ Workload semplici senza CRD speciali
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPARISON
```

---

## PART E: NOISY NEIGHBOR PREVENTION

### Esercizio E1: Fair Queuing e Priority Class

```bash
echo "=== NOISY NEIGHBOR PREVENTION ==="

# PriorityClass: definisce l'importanza dei pod per lo scheduler
# Pod a priorità alta → vengono schedulati prima e evitati da preemption

cat > quotas/priority-classes.yaml << 'EOF'
# PriorityClass: Enterprise tenant (massima priorità)
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-enterprise
value: 1000
globalDefault: false
description: "Tenant enterprise — alta priorità"

---
# PriorityClass: Professional tenant
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-professional
value: 500
globalDefault: false
description: "Tenant professional — media priorità"

---
# PriorityClass: Basic tenant (preemptible da enterprise)
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-basic
value: 100
globalDefault: true
description: "Tenant basic — bassa priorità"

---
# LimitRange per garantire che nessun singolo pod occupi tutto
apiVersion: v1
kind: LimitRange
metadata:
  name: per-pod-limit
  namespace: tenant-acme-corp
spec:
  limits:
    - type: Container
      max:
        cpu: "4000m"     # max 4 core per container (no monopolio)
        memory: "8Gi"
      min:
        cpu: "50m"
        memory: "64Mi"
EOF

kubectl apply -f quotas/priority-classes.yaml 2>/dev/null

echo "[OK] PriorityClass configurate"

echo ""
echo "=== RESOURCE QUOTA PER TIER ==="
kubectl describe resourcequota -A | grep -A10 "tenant" | head -40

echo ""
echo "=== CHECKLIST ANTI NOISY-NEIGHBOR ==="
cat << 'CHECKLIST'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI NOISY-NEIGHBOR CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

K8S LAYER:
[ ] ResourceQuota per namespace: max CPU, memory, pods
[ ] LimitRange: default + min + max per container
[ ] PriorityClass: enterprise > professional > basic
[ ] PodDisruptionBudget: garantisce disponibilità minima
[ ] HPA: scale out invece di consumare tutto su un pod

DATABASE LAYER:
[ ] Connection pooling (PgBouncer): max conn per tenant
[ ] statement_timeout: nessuna query può bloccare il DB
[ ] pg_stat_statements: identificare query lente per tenant
[ ] RLS: isolamento dati (sicurezza, non performance)
[ ] Per tenant premium: DB dedicato o schema separato

RETE:
[ ] NetworkPolicy: nessun tenant comunica con gli altri
[ ] Ingress rate limiting (Kong/Nginx): max req/s per tenant
[ ] Kubernetes Service Quality (QoS): Guaranteed > Burstable > BestEffort

MONITORING:
[ ] Alert su quota utilization > 80%
[ ] Dashboard per tenant: ogni tenant vede solo le proprie metriche
[ ] SLO per-tenant: latenza p99, error rate per ogni tenant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHECKLIST
```

---

## Conclusioni e Prossimi Passi

```
MULTI-TENANCY — RIEPILOGO:

MODELLI:
  ✓ Silo: cluster dedicato per tenant → massimo isolamento, costo alto
  ✓ Pool: namespace condivisi → basso costo, rischio noisy neighbor
  ✓ Bridge (vCluster): K8s API dedicato → equilibrio costo/isolamento

NAMESPACE ISOLATION:
  ✓ ResourceQuota: max risorse (CPU, memory, pods) per namespace
  ✓ LimitRange: default e max per ogni container
  ✓ NetworkPolicy: default-deny-all + allow esplicito per DNS e ingress
  ✓ RBAC: ogni tenant ha Role limitata nel proprio namespace
  ✓ PriorityClass: enterprise > professional > basic

POSTGRESQL RLS:
  ✓ ALTER TABLE t ENABLE ROW LEVEL SECURITY: abilita RLS
  ✓ Policy USING: filtra righe SELECT/UPDATE/DELETE
  ✓ Policy WITH CHECK: valida righe INSERT/UPDATE
  ✓ current_setting('app.tenant_id'): ogni connessione imposta il contesto
  ✓ SET LOCAL: imposta per la transazione corrente (resettato al commit)
  ✓ Vantaggio: isolamento a livello di SQL, non applicativo

VCLUSTER:
  ✓ K8s API server dedicato per tenant (etcd separato)
  ✓ Tenant è "cluster-admin" del proprio vCluster
  ✓ I pod girano come pod normali nel cluster host
  ✓ Sincronizzazione bidirezionale: Service → host, Ingress → host
  ✓ Costo: ~500MB RAM overhead per vCluster

NOISY NEIGHBOR:
  ✓ ResourceQuota: limite assoluto per namespace
  ✓ PriorityClass: pod enterprise resistono a preemption
  ✓ Connection pool: max conn DB per tenant
  ✓ Ingress rate limiting: max req/s per tenant
  ✓ Monitoring per-tenant: ogni team vede le proprie metriche

ONBOARDING AUTOMATICO:
  ✓ Script: crea namespace + quota + network policy + RBAC in < 30s
  ✓ Produzione: Terraform o Pulumi per IaC
  ✓ GitOps: PR → ArgoCD applica le risorse del nuovo tenant

CELL-BASED ARCHITECTURE (scala estrema):
  Pool di cluster ("cell") geograficamente distribuiti
  Ogni tenant assegnato a una cell
  Failure di una cell → impatta solo i tenant in quella cell (blast radius limitato)
  Es: Shopify, Atlassian, Notion usano architetture cell-based
```

```bash
# Pulizia
vcluster delete acme-vcluster --namespace vcluster-acme 2>/dev/null
kubectl delete namespace vcluster-acme tenant-acme-corp tenant-startup-xyz 2>/dev/null
docker rm -f postgres-rls 2>/dev/null
rm -rf ~/multitenancy-lab
echo "[OK] Lab Multi-Tenancy completato"
```

---

> **Nota versioni:** vCluster 0.20.x (Loft, novembre 2024), PostgreSQL 17 RLS (PostgreSQL 9.5+).
> Capsule (Projectcapsule.dev) 0.7.x: alternativa a vCluster per multi-tenancy a livello namespace.
> HNC (Hierarchical Namespace Controller): K8s SIG gestisce namespace gerarchici.
> NIST SP 800-53 AC-4: Information Flow Enforcement — controllo dei flussi tra tenant.
> AWS SaaS Lens (Well-Architected): framework per architetture SaaS su AWS (2024).
> CycloneX: standard emergente per multi-tenant policy (2025).
