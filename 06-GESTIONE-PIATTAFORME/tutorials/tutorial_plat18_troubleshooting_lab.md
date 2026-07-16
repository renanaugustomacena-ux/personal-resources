# Tutorial: Troubleshooting Kubernetes — Debug, Runbook e Post-Mortem

> **Documento di riferimento:** `18-troubleshooting-e-guide-pratiche.md`
> **Dominio:** Gestione Piattaforme — Riferimenti Operativi
> **Ambito:** Metodologia strutturata di debug K8s, CrashLoopBackOff, OOMKilled, Pending pod, problemi networking e DNS, production readiness checklist, chaos engineering con LitmusChaos, runbook template, post-mortem blameless
> **Durata lab:** 5-6 ore
> **Livello:** Avanzato — richiede K3s cluster e familiarità con kubectl
> **Prerequisiti:** K3s o kind cluster locale, kubectl, helm 3.x, Python 3.10+
> **Ambiente:** Tutto locale — workload K8s appositamente rotti per praticare il debug

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI TROUBLESHOOTING LAB ===
echo "=== PREREQUISITI ==="

kubectl version --client --short 2>/dev/null && echo "[OK] kubectl" || echo "[FAIL] kubectl richiesto"
helm version --short 2>/dev/null && echo "[OK] helm" || echo "[FAIL] helm richiesto"

# Verificare cluster attivo
kubectl get nodes && echo "[OK] Cluster K8s attivo" || \
  echo "[FAIL] Nessun cluster — avviare K3s: curl -sfL https://get.k3s.io | sh -"

# Verificare che kubectl sia configurato
kubectl cluster-info 2>/dev/null | head -2

mkdir -p ~/debug-lab/{broken,fixed,runbooks,chaos}
cd ~/debug-lab

echo "[OK] Directory lab: ~/debug-lab"
```

### Mappa Mentale del Troubleshooting K8s

```
POD non funziona?
       │
       ▼
kubectl get pod → STATUS?
       │
       ├── Pending ────────── nessun nodo disponibile
       │                      ├── risorse insufficienti (OOM, CPU)
       │                      ├── taint/toleration mismatch
       │                      └── PVC non bound
       │
       ├── CrashLoopBackOff ─ il container crasha ripetutamente
       │                      ├── codice applicazione crashato
       │                      ├── configurazione errata (env vars mancanti)
       │                      └── liveness probe troppo aggressiva
       │
       ├── OOMKilled ───────── container ha superato il memory limit
       │                      ├── memory leak nell'applicazione
       │                      └── limit troppo basso per il workload
       │
       ├── ImagePullBackOff ── immagine non trovata o accesso negato
       │                      ├── tag errato / immagine non esistente
       │                      └── imagePullSecret mancante (registry privato)
       │
       └── Running ma non risponde → problema applicativo interno
                              ├── readiness probe non passa
                              └── errore logica applicativa
```

---

## PART A: METODOLOGIA DI TROUBLESHOOTING

> Un buon ingegnere non "prova a caso" finché qualcosa funziona.
> Applica il metodo scientifico: osserva lo stato, formula un'ipotesi,
> la verifica con un esperimento mirato, analizza il risultato.
> In Kubernetes, i tre comandi iniziali sono sempre gli stessi:
> kubectl describe, kubectl logs, kubectl get events.
> Questi tre da soli risolvono il 90% dei problemi.

---

### Concetto A1: I Tre Comandi Fondamentali

```bash
# ════ TOOLKIT TROUBLESHOOTING K8S ════════════════════════════════════════

# 1. kubectl describe — TUTTO sullo stato dell'oggetto (inclusi Events)
kubectl describe pod <nome-pod> -n <namespace>
# Cosa cercare:
#   Conditions: Ready, PodScheduled, Initialized, ContainersReady
#   Events: "FailedScheduling", "BackOff", "OOMKilling", "Pulled", "Started"
#   Limits e Requests: se OOM, guardare Memory Limits
#   Volumes: se PVC non bound, guardare qui

# 2. kubectl logs — output del container
kubectl logs <nome-pod>                  # log correnti
kubectl logs <nome-pod> --previous       # log del container morto prima del crash
kubectl logs <nome-pod> -c <container>   # per multi-container pod
kubectl logs <nome-pod> --tail=100 -f    # streaming ultimi 100 righe

# 3. kubectl get events — cronologia eventi nel namespace
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
kubectl get events -n <namespace> --field-selector reason=OOMKilling
kubectl get events -A --sort-by='.lastTimestamp' | tail -20

# ════ COMANDI DIAGNOSTICI AGGIUNTIVI ══════════════════════════════════════

# Stato risorse nodo
kubectl top nodes
kubectl top pods -n <namespace> --sort-by=memory

# Debug interattivo (entri nel container)
kubectl exec -it <pod> -- /bin/sh
kubectl exec -it <pod> -c <container> -- bash

# Debug con ephemeral container (K8s 1.23+)
kubectl debug -it <pod> --image=busybox --target=<container> -- sh

# Copia file da/verso container
kubectl cp <pod>:/app/logs/error.log ./error.log
kubectl cp ./config.yaml <pod>:/app/config.yaml

# Port-forward per test locale
kubectl port-forward pod/<pod> 8080:8080
kubectl port-forward svc/<service> 8080:80

# Watch pod (aggiornamento in tempo reale)
kubectl get pods -w -n <namespace>

# ════ NETWORK DEBUG ═══════════════════════════════════════════════════════

# DNS check dall'interno del cluster
kubectl run dns-test --image=busybox:1.36 --rm -it --restart=Never -- \
  nslookup kubernetes.default.svc.cluster.local

# Connettività tra pod
kubectl run nettest --image=busybox:1.36 --rm -it --restart=Never -- \
  sh -c "wget -q -O- http://<service>.<namespace>.svc.cluster.local"

# Verificare NetworkPolicy
kubectl get networkpolicy -A
```

---

## PART B: CRASHLOOPBACKOFF — DIAGNOSI E FIX

### Esercizio B1: Creare un Pod Rotto (CrashLoopBackOff)

```bash
cd ~/debug-lab

# Scenario 1: Applicazione che crasha per variabile d'ambiente mancante
cat > broken/crash-app.py << 'PYTHON'
"""App che crasha se la variabile DATABASE_URL non è impostata."""
import os
import sys
import time

print("Avvio applicazione...")

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("ERRORE FATALE: DATABASE_URL non impostata!", file=sys.stderr)
    sys.exit(1)   # exit code 1 → Kubernetes continua a restartare

print(f"Connessione a: {db_url}")
print("Applicazione avviata con successo!")

while True:
    time.sleep(60)
PYTHON

cat > broken/crash-app-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crash-demo
  namespace: default
  labels:
    app: crash-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crash-demo
  template:
    metadata:
      labels:
        app: crash-demo
    spec:
      containers:
        - name: app
          image: python:3.12-alpine
          command: ["/bin/sh", "-c", "pip install -q && python /app/crash-app.py"]
          # PROBLEMA: DATABASE_URL non è impostata!
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "100m"
              memory: "128Mi"
EOF

kubectl create configmap crash-demo-code \
  --from-file=crash-app.py=broken/crash-app.py \
  --dry-run=client -o yaml | kubectl apply -f -

# Deployment modificato per montare lo script
cat > broken/crash-complete.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crash-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crash-demo
  template:
    metadata:
      labels:
        app: crash-demo
    spec:
      containers:
        - name: app
          image: python:3.12-alpine
          command: ["python", "/code/crash-app.py"]
          # DATABASE_URL mancante → CrashLoopBackOff
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "100m"
              memory: "128Mi"
          volumeMounts:
            - name: code
              mountPath: /code
      volumes:
        - name: code
          configMap:
            name: crash-demo-code
EOF

kubectl apply -f broken/crash-complete.yaml

echo "Attendo CrashLoopBackOff (30 secondi)..."
sleep 30
```

---

### Esercizio B2: Diagnosticare CrashLoopBackOff

```bash
echo "=== DIAGNOSI: CrashLoopBackOff ==="

echo ""
echo "--- STEP 1: Vedere stato del pod ---"
kubectl get pod -l app=crash-demo

echo ""
echo "--- STEP 2: Descrivere il pod (Events + State) ---"
kubectl describe pod -l app=crash-demo | tail -30

echo ""
echo "--- STEP 3: Log del container corrente ---"
kubectl logs -l app=crash-demo --tail=20 2>/dev/null || \
  echo "[INFO] Container in crash — nessun log corrente"

echo ""
echo "--- STEP 4: Log del container PRECEDENTE (prima del crash) ---"
kubectl logs -l app=crash-demo --previous --tail=20 2>/dev/null

echo ""
echo "--- STEP 5: Vedere exit code ---"
kubectl get pod -l app=crash-demo -o jsonpath='{.items[0].status.containerStatuses[0].lastState}' | \
  python3 -m json.tool 2>/dev/null

echo ""
echo "--- DIAGNOSI: Il container esce con exit code 1 perché DATABASE_URL mancante ---"
echo ""
echo "=== FIX: Aggiungere DATABASE_URL come Secret ==="

# Creare il secret con la credenziale
kubectl create secret generic crash-demo-secret \
  --from-literal=database-url="postgresql://user:pass@db:5432/mydb" \
  --dry-run=client -o yaml | kubectl apply -f -

# Aggiungere la variabile d'ambiente
kubectl patch deployment crash-demo --type=json -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/env",
    "value": [
      {
        "name": "DATABASE_URL",
        "valueFrom": {
          "secretKeyRef": {
            "name": "crash-demo-secret",
            "key": "database-url"
          }
        }
      }
    ]
  }
]'

echo "Attendo restart con fix..."
kubectl rollout status deployment/crash-demo --timeout=60s

echo ""
echo "--- Verificare fix ---"
kubectl get pod -l app=crash-demo
kubectl logs -l app=crash-demo --tail=5
```

---

## PART C: OOMKILLED — MEMORIA INSUFFICIENTE

### Esercizio C1: OOM e Come Diagnosticarla

```bash
cd ~/debug-lab

cat > broken/oom-app.py << 'PYTHON'
"""App con memory leak intenzionale per dimostrare OOMKilled."""
import time

print("Avvio app con memory leak...")
data = []

for i in range(10000):
    # Allocare 1MB di dati alla volta → raggiungerà il limit
    data.append(b"X" * (1024 * 1024))  # 1MB
    if i % 100 == 0:
        print(f"Allocati {i} MB ({len(data)} blocchi)")
    time.sleep(0.01)

print("Completato (non dovrebbe arrivare qui)")
PYTHON

kubectl create configmap oom-demo-code \
  --from-file=oom-app.py=broken/oom-app.py \
  --dry-run=client -o yaml | kubectl apply -f -

cat > broken/oom-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oom-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: oom-demo
  template:
    metadata:
      labels:
        app: oom-demo
    spec:
      containers:
        - name: app
          image: python:3.12-alpine
          command: ["python", "/code/oom-app.py"]
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "100m"
              memory: "128Mi"    # ← memory limit basso intenzionalmente
          volumeMounts:
            - name: code
              mountPath: /code
      volumes:
        - name: code
          configMap:
            name: oom-demo-code
EOF

kubectl apply -f broken/oom-deployment.yaml

echo "Attendo OOMKilled (~30-60 secondi)..."
sleep 45

echo ""
echo "=== DIAGNOSI: OOMKilled ==="

echo ""
echo "--- STEP 1: Stato ---"
kubectl get pod -l app=oom-demo

echo ""
echo "--- STEP 2: Descrivere (reason=OOMKilling) ---"
kubectl describe pod -l app=oom-demo | grep -A5 "OOM\|Memory\|Reason\|Exit Code"

echo ""
echo "--- STEP 3: Vedere memoria usata in tempo reale ---"
kubectl top pod -l app=oom-demo 2>/dev/null || \
  echo "[INFO] metrics-server non disponibile — installare: kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"

echo ""
echo "--- STEP 4: Events OOM ---"
kubectl get events --field-selector reason=OOMKilling 2>/dev/null

echo ""
cat << 'OOM_GUIDE'
═══════════════════════════════════════════════════════════════
OOMKilled — DIAGNOSI E SOLUZIONI
═══════════════════════════════════════════════════════════════

IDENTIFICAZIONE:
  kubectl describe pod → "OOMKilled" in State.Last State
  kubectl get events → reason=OOMKilling
  exit code: 137 (SIGKILL da OOM killer del kernel)

CAUSE COMUNI:
  1. Memory limit troppo basso per il workload reale
     FIX: aumentare limits.memory (es. 512Mi → 1Gi)
     METODO: osservare kubectl top pods per 48h → settare limit al 130% del max osservato
  
  2. Memory leak nell'applicazione
     FIX: trovare e correggere il leak
     METODO: profiling (Python: tracemalloc, Java: heap dump, Go: pprof)
     INTERIM: impostare memory limits per contenere il blast radius
  
  3. JVM non vede i cgroup memory limits (Java pre-11)
     FIX: aggiungere -XX:+UseContainerSupport -XX:MaxRAMPercentage=75
     Java 11+: UseContainerSupport abilitato di default
  
  4. Node Pressure: nodo sotto pressione di memoria
     FIX: aggiungere nodi o aumentare il RAM
     SEGNALE: kubectl describe node → MemoryPressure=True

VERTICAL POD AUTOSCALER (VPA):
  # VPA osserva l'uso reale e suggerisce limits appropriati
  helm repo add fairwinds-stable https://charts.fairwinds.com/stable
  helm install vpa fairwinds-stable/vpa --namespace vpa --create-namespace

GOLDEN RULE:
  requests: memoria che il Pod GARANTISCE di avere
  limits: memoria MASSIMA che il Pod può usare
  
  Regola pratica: limits = 2× requests
  Produzione DB: limits = 80% RAM nodo dedicato
═══════════════════════════════════════════════════════════════
OOM_GUIDE

# Fix: aumentare i memory limits
kubectl patch deployment oom-demo -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"memory":"512Mi"}}}]}}}}'
```

---

## PART D: NETWORKING E DNS

### Esercizio D1: Debug DNS nel Cluster

```bash
echo "=== NETWORKING E DNS DEBUG ==="

# Pod temporaneo per test di rete
cat > broken/network-test.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: network-debug
  namespace: default
spec:
  containers:
    - name: debug
      image: nicolaka/netshoot:latest   # immagine con tutti gli strumenti di rete
      command: ["sleep", "infinity"]
      resources:
        requests:
          cpu: "50m"
          memory: "64Mi"
        limits:
          cpu: "100m"
          memory: "128Mi"
  restartPolicy: Never
EOF

kubectl apply -f broken/network-test.yaml
kubectl wait --for=condition=Ready pod/network-debug --timeout=60s

echo ""
echo "--- Test DNS: resolving cluster services ---"
kubectl exec network-debug -- nslookup kubernetes.default.svc.cluster.local
kubectl exec network-debug -- nslookup kube-dns.kube-system.svc.cluster.local 2>/dev/null

echo ""
echo "--- Test DNS: resolving esterni ---"
kubectl exec network-debug -- nslookup google.com 2>/dev/null || \
  echo "[INFO] DNS esterno non raggiungibile (normale in ambiente air-gapped)"

echo ""
echo "--- Vedere configurazione DNS del pod ---"
kubectl exec network-debug -- cat /etc/resolv.conf

echo ""
echo "--- Test connettività TCP tra pod ---"
# Testare connettività verso il kube API server
kubectl exec network-debug -- nc -zv kubernetes.default.svc.cluster.local 443 2>&1 | head -5

echo ""
echo "--- Tracciare il path di rete ---"
kubectl exec network-debug -- traceroute -n kubernetes.default.svc.cluster.local 2>/dev/null | head -5

echo ""
echo "=== COMUNI PROBLEMI DNS IN K8S ==="
cat << 'DNS_GUIDE'
PROBLEMA: nslookup fallisce per service name
VERIFICA: kubectl get svc -n <namespace>
FIX: usare il FQDN completo: svc-name.namespace.svc.cluster.local

PROBLEMA: DNS lento (> 100ms per query)
CAUSA: ndots:5 richiede 5 tentativi prima di domain assoluto
FIX: impostare ndots:1 per applicazioni che usano FQDN
  dnsConfig:
    options:
      - name: ndots
        value: "1"

PROBLEMA: CoreDNS pod non avviati
VERIFICA: kubectl -n kube-system get pods -l k8s-app=kube-dns
FIX: kubectl -n kube-system describe pod -l k8s-app=kube-dns

PROBLEMA: NetworkPolicy blocca DNS (porta 53 UDP)
FIX: aggiungere egress rule per porta 53 verso kube-dns
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
DNS_GUIDE

kubectl delete pod network-debug --grace-period=0
```

---

## PART E: PRODUCTION READINESS CHECKLIST

### Esercizio E1: Checklist Deployment Produzione

```bash
cd ~/debug-lab

cat > runbooks/production-readiness.sh << 'SCRIPT'
#!/bin/bash
# Production Readiness Checker
# Verifica che un Deployment soddisfi i criteri minimi prima di andare in produzione

NAMESPACE="${1:-default}"
DEPLOYMENT="${2:-}"

if [ -z "$DEPLOYMENT" ]; then
  echo "Uso: $0 <namespace> <deployment>"
  echo "Esempio: $0 production myapp"
  exit 1
fi

echo "════════════════════════════════════════════════════════"
echo "PRODUCTION READINESS CHECK: ${NAMESPACE}/${DEPLOYMENT}"
echo "════════════════════════════════════════════════════════"

PASS=0
FAIL=0
WARN=0

check() {
  local desc="$1"
  local cmd="$2"
  local expected="$3"
  local actual
  
  actual=$(eval "$cmd" 2>/dev/null)
  
  if [ -z "$actual" ] || [ "$actual" = "null" ] || [ "$actual" = "" ]; then
    echo "  [FAIL] $desc"
    FAIL=$((FAIL + 1))
  else
    echo "  [OK]   $desc: $actual"
    PASS=$((PASS + 1))
  fi
}

warn_if_missing() {
  local desc="$1"
  local cmd="$2"
  local actual
  
  actual=$(eval "$cmd" 2>/dev/null)
  if [ -z "$actual" ] || [ "$actual" = "null" ] || [ "$actual" = "false" ]; then
    echo "  [WARN] $desc"
    WARN=$((WARN + 1))
  else
    echo "  [OK]   $desc"
    PASS=$((PASS + 1))
  fi
}

echo ""
echo "--- Resource Management ---"
check "CPU request definito" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].resources.requests.cpu}'"

check "CPU limit definito" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].resources.limits.cpu}'"

check "Memory request definito" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].resources.requests.memory}'"

check "Memory limit definito" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}'"

echo ""
echo "--- Health Checks ---"
check "Liveness probe configurata" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].livenessProbe}'"

check "Readiness probe configurata" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].readinessProbe}'"

echo ""
echo "--- Security ---"
check "runAsNonRoot: true" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].securityContext.runAsNonRoot}'"

warn_if_missing "allowPrivilegeEscalation: false" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].securityContext.allowPrivilegeEscalation}' | grep -c 'false'"

warn_if_missing "read-only root filesystem" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].securityContext.readOnlyRootFilesystem}' | grep -c 'true'"

echo ""
echo "--- Image Management ---"
check "Immagine con tag specifico (no :latest)" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].image}' | grep -v ':latest'"

warn_if_missing "imagePullPolicy: IfNotPresent" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].imagePullPolicy}' | grep -c 'IfNotPresent'"

echo ""
echo "--- Availability ---"
check "Replicas >= 2" \
  "kubectl get deployment/${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.replicas}' | awk '\$1>=2{print \$1}'"

warn_if_missing "PodDisruptionBudget configurato" \
  "kubectl get pdb -n ${NAMESPACE} 2>/dev/null | grep -c ${DEPLOYMENT}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RISULTATO: ${PASS} PASS | ${FAIL} FAIL | ${WARN} WARN"

if [ "$FAIL" -gt 0 ]; then
  echo "STATUS: NON PRONTO PER PRODUZIONE — risolvere i FAIL"
  exit 1
elif [ "$WARN" -gt 0 ]; then
  echo "STATUS: ATTENZIONE — risolvere i WARN prima del deploy"
  exit 0
else
  echo "STATUS: PRODUCTION READY ✓"
  exit 0
fi
SCRIPT

chmod +x runbooks/production-readiness.sh
echo "[OK] Production readiness checker creato"

# Test su un deployment esistente
bash runbooks/production-readiness.sh default crash-demo 2>/dev/null || true
```

---

## PART F: POST-MORTEM BLAMELESS

### Esercizio F1: Template Post-Mortem

```bash
cd ~/debug-lab

cat > runbooks/post-mortem-template.md << 'MD'
# Post-Mortem: [Titolo Incidente]

> **Principio fondamentale:** Il post-mortem è blameless.
> L'obiettivo non è trovare il colpevole, ma migliorare il sistema.
> Le persone operano in buona fede con le informazioni disponibili al momento.

## Metadata

| Campo | Valore |
|-------|--------|
| Data incidente | 2026-XX-XX |
| Durata | Da HH:MM a HH:MM (N ore/minuti) |
| Severità | P1 / P2 / P3 |
| Servizi impattati | [lista] |
| Autori | [lista reviewer] |
| Review completata | 2026-XX-XX |

## Impatto

- **Utenti impattati:** N utenti (M% del totale)
- **Revenue impatto:** ~€X k di transazioni non processate
- **SLO:** 99.X% disponibilità (target: 99.9%) — Error Budget consumato: Y%
- **Servizi**: servizio-A (degradato), servizio-B (non raggiungibile)

## Timeline

| Ora (UTC) | Evento |
|-----------|--------|
| HH:MM | Prima alert Prometheus — latenza p99 > 2s |
| HH:MM | Ingegnere on-call notificato |
| HH:MM | Identificata causa root: OOMKilled su pod payments-v2 |
| HH:MM | Rollback a payments-v1 avviato |
| HH:MM | Rollback completato — sistema ripristinato |
| HH:MM | Monitoring stabile, incidente chiuso |

## Causa Root (5 Why)

1. **Perché** gli utenti vedevano errori 503?
   → Perché i pod payments-v2 erano in CrashLoopBackOff

2. **Perché** erano in CrashLoopBackOff?
   → Perché venivano OOMKilled dopo ~5 minuti dall'avvio

3. **Perché** venivano OOMKilled?
   → Perché il memory limit era 256Mi ma il nuovo codice usava 400Mi sotto carico

4. **Perché** il memory limit era rimasto a 256Mi?
   → Perché non c'era un test di carico nel pipeline CI/CD che misurasse il consumo

5. **Perché** non c'era il test di carico?
   → Perché il processo di deploy non lo richiedeva esplicitamente

**Root Cause:** Assenza di load testing nel pipeline CI/CD che verifichi il consumo di memoria.

## Cosa Ha Funzionato Bene

- Alert Prometheus configurato correttamente — rilevamento in < 5 min
- Runbook di rollback disponibile e testato — rollback completato in 8 min
- On-call ha risposto in < 2 min
- Comunicazione verso il team prodotto tempestiva

## Cosa Non Ha Funzionato

- Nessun test di carico nel pipeline — la regressione di memoria non è stata rilevata
- Memory limits non aggiornati dopo refactoring del codice
- Assenza di alerting proattivo su resource utilization (>80%)

## Action Items

| Azione | Responsabile | Scadenza | Stato |
|--------|-------------|----------|-------|
| Aggiungere load test (k6) nel pipeline CI | Team Platform | 2026-02-01 | TODO |
| Alert: memory utilization > 80% per 5min | Team Monitoring | 2026-01-25 | TODO |
| Processo di revisione limits pre-deploy | Team Engineering | 2026-02-15 | TODO |
| Aggiornare runbook con checklist memory | On-call lead | 2026-01-22 | TODO |

## Lessons Learned

- I memory limits devono essere basati su misurazioni reali di carico, non su stime
- Il pipeline CI/CD deve includere un test di carico minimo per workload critici
- L'utente finale non distingue "crash" da "lento" — entrambi = esperienza negativa
MD

echo "[OK] Template post-mortem creato: runbooks/post-mortem-template.md"
```

---

## PART G: CHAOS ENGINEERING

### Esercizio G1: Simulazione Guasti con LitmusChaos

```bash
echo "=== CHAOS ENGINEERING — LITMUECHAOS ==="

cat << 'CHAOS_GUIDE'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHAOS ENGINEERING — PRINCIPI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Il chaos engineering non è fare cose a caso.
È eseguire esperimenti controllati per scoprire
debolezze prima che lo faccia un incidente reale."
— Principi di Chaos Engineering (principlesofchaos.org)

PROCESSO:
  1. Definire lo "Steady State": come appare il sistema sano?
     (SLO 99.9%, latenza p99 < 200ms, 0 errori 5xx)
  
  2. Ipotizzare: cosa succede se X si rompe?
     ("Se un pod payments crasha, il circuit breaker attiva il fallback?")
  
  3. Progettare l'esperimento: iniettare il guasto controllato
     (LitmusChaos: pod-delete, cpu-stress, network-partition)
  
  4. Osservare: il sistema mantiene lo Steady State?
  
  5. Correggere le debolezze trovate

LITMUECHAOS — ESPERIMENTI DISPONIBILI:
  pod-delete: elimina pod random → verifica HA e restart
  pod-cpu-hog: stess CPU → verifica HPA e throttling
  pod-memory-hog: stress RAM → verifica OOM handling
  network-latency: aggiunge latenza 200ms → verifica timeout
  network-loss: drop 30% pacchetti → verifica retry
  node-drain: drain nodo → verifica pod rescheduling

INSTALLAZIONE LITMUECHAOS 3.x:
  helm repo add litmuschaos https://litmuschaos.github.io/litmus-helm/
  helm install chaos litmuschaos/litmus \
    --namespace litmus --create-namespace \
    --set portal.frontend.service.type=NodePort

ESPERIMENTO POD DELETE (esempio):
  # Crea ChaosEngine che esegue pod-delete su Deployment myapp
  apiVersion: litmuschaos.io/v1alpha1
  kind: ChaosEngine
  metadata:
    name: myapp-chaos
    namespace: default
  spec:
    appinfo:
      appns: "default"
      applabel: "app=myapp"
      appkind: "deployment"
    chaosServiceAccount: litmus-admin
    experiments:
      - name: pod-delete
        spec:
          components:
            env:
              - name: TOTAL_CHAOS_DURATION
                value: "60"        # durata esperimento: 60 secondi
              - name: CHAOS_INTERVAL
                value: "15"        # elimina un pod ogni 15 secondi
              - name: FORCE
                value: "false"     # graceful shutdown (non SIGKILL)

ALTERNATIVA LEGGERA: chaos-mesh
  helm repo add chaos-mesh https://charts.chaos-mesh.org
  helm install chaos-mesh chaos-mesh/chaos-mesh \
    --namespace=chaos-mesh --create-namespace

GAME DAY — PROCEDURA:
  1. Avvisare il team (no surprises)
  2. Definire i BLAST RADIUS minimi (solo namespace dev)
  3. Avere il "kill switch" pronto (kubectl delete chaosengine)
  4. Monitoring attivo durante l'esperimento
  5. Documentare findings nel post-mortem
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHAOS_GUIDE

# Simulazione manuale senza LitmusChaos
echo ""
echo "=== CHAOS MANUALE: eliminare pod e vedere recovery ==="

# Creare un deployment con 3 repliche
kubectl create deployment resilient-app \
  --image=nginx:1.27.0 \
  --replicas=3 \
  --dry-run=client -o yaml | \
  kubectl set resources -f - --requests=cpu=50m,memory=64Mi --limits=cpu=100m,memory=128Mi \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout status deployment/resilient-app --timeout=60s

echo ""
echo "--- Stato PRIMA del chaos ---"
kubectl get pods -l app=resilient-app

echo ""
echo "--- CHAOS: eliminare un pod random ---"
VICTIM=$(kubectl get pods -l app=resilient-app -o jsonpath='{.items[0].metadata.name}')
echo "Eliminando pod: $VICTIM"
kubectl delete pod "$VICTIM" --grace-period=0

echo ""
echo "--- Stato DURANTE il recovery ---"
sleep 3
kubectl get pods -l app=resilient-app

echo ""
echo "--- Stato DOPO il recovery ---"
sleep 10
kubectl get pods -l app=resilient-app

echo ""
echo "[INFO] Kubernetes ha automaticamente creato un nuovo pod per sostituire quello eliminato"
echo "[INFO] Il Deployment mantiene sempre N replicas in stato Running"

kubectl delete deployment resilient-app 2>/dev/null
```

---

## Conclusioni e Prossimi Passi

```
TROUBLESHOOTING KUBERNETES — RIEPILOGO:

I TRE COMANDI FONDAMENTALI:
  ✓ kubectl describe pod: stato, conditions, events
  ✓ kubectl logs --previous: log del container morto
  ✓ kubectl get events --sort-by=.lastTimestamp: cronologia

CRASHLOOPBACKOFF:
  ✓ Causa: exit code ≠ 0 all'avvio
  ✓ Diagnosi: kubectl logs --previous + exit code
  ✓ Comune: variabile d'ambiente mancante, file config non trovato
  ✓ Fix: aggiungere env var, corregger configmap, correggere il codice

OOMKILLED:
  ✓ Causa: superato memory limit
  ✓ Diagnosi: kubectl describe → OOMKilled, exit code 137
  ✓ Fix 1: aumentare limits.memory (base 2× del max osservato)
  ✓ Fix 2: trovare e correggere il memory leak
  ✓ Tool: VPA per suggerire i valori corretti automaticamente

PENDING:
  ✓ Causa: nessun nodo può soddisfare le richieste
  ✓ Diagnosi: kubectl describe pod → Events "FailedScheduling"
  ✓ Comune: Insufficient cpu/memory, taint, nodeSelector, PVC non bound

NETWORKING:
  ✓ DNS: nslookup service.namespace.svc.cluster.local
  ✓ NetworkPolicy: controllare se blocca il traffico (default-deny)
  ✓ Tool: kubectl run nettest --image=nicolaka/netshoot

PRODUCTION READINESS:
  ✓ Resource limits obbligatori
  ✓ Liveness + readiness probe
  ✓ runAsNonRoot: true, allowPrivilegeEscalation: false
  ✓ Replicas >= 2 + PodDisruptionBudget
  ✓ Tag immagine specifico (no :latest)

CHAOS ENGINEERING:
  ✓ Steady State → Hypothesis → Experiment → Observe → Fix
  ✓ LitmusChaos: pod-delete, cpu-stress, network-latency
  ✓ GameDay: avvisare il team, blast radius minimo, kill switch pronto

POST-MORTEM BLAMELESS:
  ✓ No blame: le persone fanno del loro meglio
  ✓ Timeline precisa
  ✓ 5 Why per trovare la root cause (non la causa immediata)
  ✓ Action items SMART: Specific, Measurable, Assignee, Realistic, Time-bound
  ✓ Share widely: benefici condivisi con tutto il team/organizzazione
```

```bash
# Pulizia completa
kubectl delete deployment crash-demo oom-demo 2>/dev/null
kubectl delete configmap crash-demo-code oom-demo-code 2>/dev/null
kubectl delete secret crash-demo-secret 2>/dev/null
rm -rf ~/debug-lab
echo "[OK] Lab Troubleshooting completato"
```

---

> **Nota versioni:** kubectl 1.30-1.32, Kubernetes 1.30-1.32, LitmusChaos 3.12.x (CNCF incubating).
> Ephemeral containers (kubectl debug): stable da K8s 1.25.
> VPA (Vertical Pod Autoscaler): Helm chart fairwinds-stable/vpa 9.x.
> Chaos Mesh 2.7.x: alternativa CNCF a LitmusChaos, dashboard web inclusa.
> nicola/netshoot: immagine standard per debug networking K8s (2024 aggiornamento).
> Principi Chaos Engineering: https://principlesofchaos.org (6 principi, 2019).
