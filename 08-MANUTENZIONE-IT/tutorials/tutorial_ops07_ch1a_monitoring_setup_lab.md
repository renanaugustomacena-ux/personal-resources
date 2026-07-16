# Tutorial: Setup Monitoraggio Infrastruttura — Prometheus, Grafana e Alert

> **Documento di riferimento:** `07-monitoraggio-incidenti.md` (sezioni 2-3: Sistemi di Monitoraggio e Gestione Alert)
> **Dominio:** Operazioni IT — Monitoring & Observability
> **Ambito:** Prometheus + Node Exporter + Grafana, Windows Exporter, SNMP concetti, Loki per log, Uptime Kuma, soglie di alert, Alertmanager, alert fatigue, PromQL basi
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio — richiede ops03 (OS management) e conoscenza base Linux
> **Prerequisiti:** SRV-LINUX-01 con Docker, DC-LAB-01, connettività di rete lab
> **Ambiente:** SRV-LINUX-01 (Prometheus, Grafana, Node Exporter, Uptime Kuma via Docker)

---

## Lab Environment Setup

```bash
# Su SRV-LINUX-01 come lab-admin

echo "=== VERIFICA PREREQUISITI MONITORAGGIO LAB ==="

# Docker disponibile?
docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Docker mancante"

# Spazio disco (Prometheus + Grafana richiedono ~500MB immagini Docker)
df -h / | awk 'NR==2{print "Disco root:", $4, "disponibili"}'

# RAM disponibile (almeno 1GB raccomandato per lo stack)
free -m | awk 'NR==2{print "RAM disponibile:", $7, "MB"}'

# Porta 9090 (Prometheus) libera?
ss -tlnp | grep 9090 && echo "[INFO] Porta 9090 già in uso" || echo "[OK] Porta 9090 libera"
# Porta 3000 (Grafana) libera?
ss -tlnp | grep 3000 && echo "[INFO] Porta 3000 già in uso" || echo "[OK] Porta 3000 libera"

echo ""
echo "Struttura directory monitoring:"
sudo mkdir -p /monitoring/{prometheus,grafana,alertmanager,loki,promtail}
sudo chown -R lab-admin:lab-admin /monitoring
ls /monitoring
```

---

## PART A: FONDAMENTI — Vedere Prima di Agire

> Il monitoraggio è la differenza tra sapere che un problema sta per accadere e scoprirlo quando l'utente ti chiama furioso alle 3 di notte. Senza visibilità, un sysadmin lavora alla cieca: il disco si riempie senza preavviso, la memoria si esaurisce gradualmente, il certificato scade. Con un sistema di monitoraggio efficace, il team IT interviene preventivamente: il ticket aperto automaticamente dice "disco al 78%, azione richiesta entro 72 ore" — non "sistema down, tutti che urlano". Questo cambio di paradigma — da reattivo a proattivo — è la distinzione più importante tra un team IT maturo e uno che vive sempre in emergenza.

---

### Concetto A1: I Tre Pilastri dell'Observability

> **Analogia.** Per capire la salute di una persona, il medico ha tre strumenti: il monitor ECG (metriche — valori numerici nel tempo), la cartella clinica (log — storia degli eventi), e la TAC (trace — vista interna di un sistema in un momento specifico). Usati insieme, danno un quadro completo. Un solo strumento non basta: il monitor ECG mostra un'anomalia ma non dice cosa sta succedendo dentro; il log dice "errore database" ma non quando il sistema ha iniziato a degradarsi. L'observability moderna combina tutti e tre.

**I tre pilastri:**

```
METRICHE (Metrics):
  Cosa sono: valori numerici campionati nel tempo
  Esempio: CPU 73%, memoria 4.2GB/8GB, request_latency_p99=180ms
  Strumenti: Prometheus, Zabbix, Datadog, Graphite
  
  PRO: compressione straordinaria (un punto ogni 15s per sempre)
  PRO: query su aggregati (media CPU di tutti i server prod)
  PRO: base per gli alert con soglie
  CONTRO: non mostrano il "perché" — solo il "quanto"

LOG (Logs):
  Cosa sono: record testuali di eventi discreti
  Esempio: [2026-07-15 09:23:15] ERROR: Connection refused to DB
  Strumenti: ELK Stack, Loki+Grafana, Graylog
  
  PRO: mostrano cosa è successo esattamente (context completo)
  PRO: ricercabili (trova "Connection refused" nelle ultime 24h)
  CONTRO: volume enorme (GB/giorno su infrastruttura media)
  CONTRO: senza correlazione, difficili da usare in crisi

TRACE (Distributed Tracing):
  Cosa sono: percorso end-to-end di una richiesta attraverso i servizi
  Esempio: request_id=abc123 → nginx (5ms) → app (45ms) → DB (120ms)
  Strumenti: Jaeger, Zipkin, OpenTelemetry
  
  PRO: identificano DOVE la latenza si accumula
  PRO: visibilità sulle dipendenze tra servizi
  CONTRO: richiede instrumentazione delle applicazioni
  
NEL LAB:
  Metriche: Prometheus + Node Exporter
  Log: rsyslog + Loki (opzionale, se risorse permettono)
  Trace: non nel lab (richiede microservizi)
```

---

### Concetto A2: Prometheus — Il Modello Pull

> **Analogia.** Esistono due approcci per raccogliere le temperature di 100 uffici. Approccio push: ogni termostato si sveglia ogni minuto e manda il dato a un server centrale (100 connessioni simultanee in entrata). Approccio pull: il server centrale va a chiedere la temperatura a ogni termostato uno per volta (100 connessioni in uscita, controllate). Prometheus usa il modello pull: ogni 15 secondi va a "raschiare" (scrape) le metriche da ogni sistema. Questo rende il server Prometheus l'unico sistema che deve conoscere gli altri — non il contrario.

**Architettura Prometheus nel lab:**

```
┌─────────────────────────────────────────────────────────┐
│                    SRV-LINUX-01                         │
│                                                         │
│  ┌─────────────┐     scrape ogni 15s    ┌───────────┐  │
│  │  Prometheus  │ ──────────────────── → │   Node    │  │
│  │  :9090      │ ← metrics (CPU/RAM/IO)  │  Exporter │  │
│  └──────┬──────┘                         │   :9100   │  │
│         │ query                          └───────────┘  │
│  ┌──────▼──────┐                                        │
│  │   Grafana   │ → Dashboard per umani                  │
│  │   :3000     │                                        │
│  └─────────────┘                                        │
│                                                         │
│  ┌──────────────────┐  scrape ogni 15s  ┌────────────┐ │
│  │  Prometheus       │ ─────────────── → │  Windows   │ │
│  │  (same instance) │ ← CPU/disk/svcs   │  Exporter  │ │
│  └──────────────────┘                   │  :9182     │ │
│                                         │ (DC-LAB-01)│ │
│                                         └────────────┘ │
└─────────────────────────────────────────────────────────┘

FLUSSO DATI:
  1. Node Exporter espone metriche su http://localhost:9100/metrics
  2. Prometheus "scrapa" questa URL ogni 15 secondi
  3. Prometheus salva le metriche nel suo TSDB (Time Series Database)
  4. Grafana interroga Prometheus con query PromQL
  5. Grafana visualizza i dati in dashboard
```

---

### Concetto A3: PromQL — Interrogare le Metriche

> **Analogia.** Le metriche grezze sono come un database di tabelle: senza un linguaggio di query, sono solo numeri. SQL è il linguaggio per i database relazionali; PromQL è il linguaggio per le serie temporali di Prometheus. Come SQL, PromQL permette di filtrare, aggregare, calcolare e combinare metriche per rispondere a domande come "qual è la CPU media dei server di produzione negli ultimi 5 minuti?" o "quale disco si riempirà per primo nelle prossime 24 ore?"

**PromQL essenziale:**

```
QUERY BASE:
  node_cpu_seconds_total          → tutti i dati CPU (raw)
  node_memory_MemAvailable_bytes  → RAM disponibile (byte)
  node_filesystem_avail_bytes     → spazio disco disponibile

FILTRI (label selector):
  node_cpu_seconds_total{mode="idle"}         → solo CPU idle
  node_cpu_seconds_total{instance="srv-linux-01:9100", mode!="idle"}
  
RATE (tasso di variazione — per contatori che crescono sempre):
  rate(node_cpu_seconds_total{mode="idle"}[5m])
  → variazione media al secondo nell'ultimo 5 minuti
  
AGGREGAZIONI:
  avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)
  → CPU idle media PER HOST negli ultimi 5 min
  
OPERATORI MATEMATICI:
  # CPU utilization (percentuale)
  100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
  
  # Memoria utilizzata %
  (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100
  
  # Disco utilizzato %
  100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100)

PREDICT_LINEAR (previsione):
  predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 24*3600)
  → predice lo spazio disponibile tra 24h basandosi sull'ultimo 6h
  → usato per: "questo disco si riempirà entro 24h?"
```

---

### Concetto A4: Alert — Non Troppi, Non Troppo Pochi

> **Analogia.** Immagina un'auto con un sistema di allerta perfezionista: ti avverte quando la temperatura esterna è sopra 25°C, quando l'olio scende sotto il 90%, quando il carburante è sotto l'80%. Dopo 10 minuti di guida hai ricevuto 47 notifiche. Smetti di guardarle tutte. E perdi l'alert "FRENI NON FUNZIONANTI". Questo è l'alert fatigue. La soluzione non è meno sicurezza — è alert che richiedono SOLO azioni umane reali, con soglie calibrate sulla baseline del sistema, non su valori arbitrari.

**Framework per alert efficaci:**

```
REGOLA D'ORO:
  Ogni alert deve richiedere un'azione umana specifica.
  Se non c'è nulla da fare quando scatta, non è un alert — è un log.

STRUTTURA DI UN BUON ALERT:
  Name:        HighDiskUsage_Root
  Condition:   Disco / > 80% per 10 minuti
  Severity:    WARNING (85%) / CRITICAL (90%)
  Action:      Pulisci log vecchi, analizza crescita, pianifica espansione
  Runbook:     /dr/runbooks/disk-cleanup.sh
  
  Cosa NON fare:
  ✗ Alert su CPU > 50% (quasi sempre è normale)
  ✗ Alert su ogni errore 404 (sono normali)
  ✗ Alert senza runbook (cosa devo fare?)

TABELLA SOGLIE STANDARD (da 07-monitoraggio-incidenti.md):

  Metrica           | WARNING      | CRITICAL     | Finestra
  ────────────────────────────────────────────────────────
  CPU utilizzo      | > 80%        | > 95%        | 5 min
  Memoria           | > 85%        | > 95%        | 3 min
  Disco utilizzato  | > 80%        | > 90%        | 10 min
  Disco I/O wait    | > 20%        | > 40%        | 5 min
  Packet loss rete  | > 1%         | > 5%         | 5 min
  Latenza rete      | > 50ms       | > 200ms      | 5 min
  Risposta HTTP     | > 2s (P95)   | > 5s (P95)   | 5 min
  Certificato SSL   | < 30 giorni  | < 14 giorni  | daily
  Backup status     | parziale     | fallito      | daily
  Load average      | > N*1.5      | > N*3        | 5 min
  Zombie processes  | > 3          | > 10         | 5 min
  Connessioni DB    | > 80% pool   | > 95% pool   | 5 min
  (N = numero core CPU)

MATRICE DI ESCALATION:
  L1 (T+0):   On-call → Slack + push notification
  L2 (T+15m): Team lead → Slack + SMS (se L1 non ACK)
  L3 (T+30m): Architect → Telefono (se non risolto)
  L4 (T+60m): IT Manager → Telefono + email executive
```

---

### Concetto A5: SNMP — Il Protocollo del Network Monitoring

> **Analogia.** I dispositivi di rete (switch, router, firewall, UPS, stampanti) sono "scatole chiuse" — non puoi installare un agente Linux o un exe Windows al loro interno. SNMP è il protocollo universale di interrogazione di questi dispositivi: è come un dialetto standard che tutti i dispositivi di rete parlano. Chiedi "qual è il traffico sulla porta 24?" in SNMP, e lo switch risponde — qualunque sia il produttore.

```
SNMP VERSIONI:
  SNMPv1/v2c: community string in chiaro = INSICURO
              usare solo su reti completamente isolate
  SNMPv3:     autenticazione SHA + crittografia AES = SICURO
              obbligatorio in produzione

OID (Object Identifier) = "codice" della metrica:
  1.3.6.1.2.1.1.5.0 → nome del sistema (sysName)
  1.3.6.1.2.1.1.3.0 → uptime (sysUpTime)
  1.3.6.1.2.1.2.2.1.8 → stato interfaccia (1=up, 2=down)
  1.3.6.1.2.1.2.2.1.10 → traffico ingresso (byte)

COMANDI BASE:
  snmpget -v2c -c public 192.168.56.10 1.3.6.1.2.1.1.5.0
  → chiedi il nome del sistema a DC-LAB-01
  
  snmpwalk -v2c -c public 192.168.56.20 1.3.6.1.2.1.2.2.1.2
  → lista tutte le interfacce di rete di SRV-LINUX-01
```

---

## PART B: OPERAZIONI — Installare e Configurare il Lab di Monitoraggio

---

### Esercizio B1: Installare Prometheus + Node Exporter via Docker

**Obiettivo.** Avviare Prometheus e Node Exporter su SRV-LINUX-01 e verificare che le metriche del server siano raccolte correttamente.

**Background.** Usiamo Docker per semplicità: Prometheus, Grafana e Node Exporter sono disponibili come immagini ufficiali. In produzione, potresti installarli direttamente (binari) o su Kubernetes — il funzionamento è identico. Docker nel lab riduce le dipendenze e rende il setup riproducibile.

**Step 1 — Crea configurazione Prometheus:**

```bash
# Su SRV-LINUX-01

mkdir -p /monitoring/prometheus
cat > /monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

# Regole di alerting (creeremo il file nella sezione B4)
rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  # Prometheus monitora se stesso
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # Node Exporter — metriche Linux di SRV-LINUX-01
  - job_name: "node_exporter"
    static_configs:
      - targets: ["node-exporter:9100"]
        labels:
          hostname: "srv-linux-01"
          env: "lab"

  # Windows Exporter — DC-LAB-01 (aggiungeremo in B3)
  # - job_name: "windows_exporter"
  #   static_configs:
  #     - targets: ["192.168.56.10:9182"]
  #       labels:
  #         hostname: "dc-lab-01"
  #         env: "lab"
EOF

echo "[OK] prometheus.yml creato"
cat /monitoring/prometheus/prometheus.yml
```

**Step 2 — Avvia lo stack con Docker:**

```bash
# Crea rete Docker dedicata per il monitoraggio
docker network create monitoring-net 2>/dev/null || echo "Rete già esistente"

# Avvia Node Exporter (raccoglie metriche di SRV-LINUX-01)
docker run -d \
    --name node-exporter \
    --network monitoring-net \
    --pid="host" \
    --volume="/:/host:ro,rslave" \
    -p 9100:9100 \
    --restart unless-stopped \
    prom/node-exporter:latest \
    --path.rootfs=/host

echo "Attendo avvio Node Exporter..."
sleep 5

# Verifica Node Exporter
if curl -s http://localhost:9100/metrics | grep -q "node_cpu_seconds_total"; then
    echo "[OK] Node Exporter attivo — metriche disponibili"
    echo "Esempio metriche:"
    curl -s http://localhost:9100/metrics | grep -E "^node_memory_MemTotal_bytes|^node_memory_MemAvailable_bytes" | head -3
else
    echo "[WARN] Node Exporter non risponde ancora — riprova tra 10s"
fi

# Crea directory per le regole Prometheus
mkdir -p /monitoring/prometheus/rules
```

**Step 3 — Avvia Prometheus:**

```bash
# Avvia Prometheus
docker run -d \
    --name prometheus \
    --network monitoring-net \
    -p 9090:9090 \
    --volume="/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
    --volume="/monitoring/prometheus/rules:/etc/prometheus/rules:ro" \
    --volume="/monitoring/prometheus/data:/prometheus" \
    --restart unless-stopped \
    prom/prometheus:latest \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus \
    --storage.tsdb.retention.time=30d \
    --web.enable-lifecycle

echo "Attendo avvio Prometheus..."
sleep 10

# Verifica Prometheus
if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus"; then
    echo "[OK] Prometheus attivo su http://192.168.56.20:9090"
else
    echo "[CHECK] Prometheus: $(curl -s http://localhost:9090/-/healthy 2>/dev/null || echo 'non risponde')"
fi

# Verifica targets (devono essere UP)
echo ""
echo "Targets configurati:"
curl -s http://localhost:9090/api/v1/targets 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for target in data.get('data', {}).get('activeTargets', []):
    print(f\"  {target['labels'].get('job','')} ({target['labels'].get('instance','')}) → {target['health']}\")" 2>/dev/null || \
    echo "  (apri http://192.168.56.20:9090/targets nel browser)"
```

**Step 4 — Prima query PromQL:**

```bash
# Test query PromQL via API (senza bisogno di aprire il browser)
echo "=== TEST QUERY PROMQL ==="

# CPU utilizzo approssimativo (più semplice della formula completa)
CPU_QUERY='100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
CPU_RESULT=$(curl -s "http://localhost:9090/api/v1/query?query=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$CPU_QUERY'))")" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('data',{}).get('result',[]); print(f'{float(r[0][\"value\"][1]):.1f}%' if r else 'no data')" 2>/dev/null)

echo "CPU utilizzo attuale: ${CPU_RESULT:-non disponibile ancora (attendi 1 minuto)}"

# Memoria disponibile
MEM_AVAILABLE=$(curl -s "http://localhost:9090/api/v1/query?query=node_memory_MemAvailable_bytes" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('data',{}).get('result',[]); print(f'{int(r[0][\"value\"][1])/1024/1024:.0f} MB' if r else 'no data')" 2>/dev/null)
echo "RAM disponibile: ${MEM_AVAILABLE:-non disponibile ancora}"

echo ""
echo "Apri il browser su http://192.168.56.20:9090"
echo "e prova queste query nella barra di ricerca:"
echo ""
echo "  # CPU utilization %:"
echo "  100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
echo ""
echo "  # RAM disponibile in MB:"
echo "  node_memory_MemAvailable_bytes / 1024 / 1024"
echo ""
echo "  # Disco radice usato %:"
echo "  100 - (node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"} * 100)"
```

**Checkpoint di verifica B1:**
- [ ] Node Exporter risponde su http://192.168.56.20:9100/metrics
- [ ] Prometheus avviato su http://192.168.56.20:9090
- [ ] Targets page mostra node-exporter con stato "UP"
- [ ] Prima query PromQL restituisce un valore di CPU

---

### Esercizio B2: Installare e Configurare Grafana

**Obiettivo.** Collegare Grafana a Prometheus e importare una dashboard pre-made per visualizzare le metriche di SRV-LINUX-01.

**Step 1 — Avvia Grafana:**

```bash
# Crea directory per dati persistenti Grafana
mkdir -p /monitoring/grafana/data

# Grafana container (in Linux va impostato il proprietario come UID 472)
docker run -d \
    --name grafana \
    --network monitoring-net \
    -p 3000:3000 \
    -e "GF_SECURITY_ADMIN_USER=admin" \
    -e "GF_SECURITY_ADMIN_PASSWORD=Lab@2024!" \
    -e "GF_USERS_ALLOW_SIGN_UP=false" \
    --volume="/monitoring/grafana/data:/var/lib/grafana" \
    --restart unless-stopped \
    grafana/grafana:latest

echo "Attendo avvio Grafana..."
sleep 15

# Verifica
if curl -s http://localhost:3000/api/health | grep -q "ok"; then
    echo "[OK] Grafana attivo su http://192.168.56.20:3000"
    echo "     Login: admin / Lab@2024!"
else
    echo "[CHECK] $(curl -s http://localhost:3000/api/health 2>/dev/null || echo 'non ancora pronto')"
fi
```

**Step 2 — Configura data source Prometheus via API:**

```bash
# Attendi che Grafana sia completamente avviato
sleep 10

echo "=== CONFIGURAZIONE DATA SOURCE PROMETHEUS ==="

# Aggiungi Prometheus come data source via API Grafana
GRAFANA_DS_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "admin:Lab@2024!" \
    http://localhost:3000/api/datasources \
    -d '{
        "name": "Prometheus-Lab",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": true,
        "jsonData": {
            "httpMethod": "POST",
            "scrapeInterval": "15s"
        }
    }' 2>/dev/null)

if echo "$GRAFANA_DS_RESPONSE" | grep -q '"id"'; then
    echo "[OK] Data source Prometheus configurato"
else
    echo "Risposta API: $GRAFANA_DS_RESPONSE"
    echo "[INFO] Se errore 'already exists', il data source è già configurato"
fi
```

**Step 3 — Importa dashboard Node Exporter Full (ID: 1860):**

```bash
# Scarica e importa la dashboard Node Exporter Full
echo "=== IMPORTA DASHBOARD NODE EXPORTER FULL ==="
echo "Dashboard ID: 1860 (Node Exporter Full — comunità Grafana)"

# Metodo 1: Import via API
DASHBOARD_IMPORT=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "admin:Lab@2024!" \
    http://localhost:3000/api/dashboards/import \
    -d '{
        "dashboard": {"id": null},
        "inputs": [
            {
                "name": "DS_PROMETHEUS",
                "type": "datasource",
                "pluginId": "prometheus",
                "value": "Prometheus-Lab"
            }
        ],
        "overwrite": true,
        "folderId": 0,
        "gnetId": 1860
    }' 2>/dev/null)

if echo "$DASHBOARD_IMPORT" | grep -q '"uid"'; then
    DASH_URL=$(echo "$DASHBOARD_IMPORT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('importedUrl',''))" 2>/dev/null)
    echo "[OK] Dashboard importata: http://192.168.56.20:3000$DASH_URL"
else
    echo "[INFO] Import automatico non riuscito (potrebbe richiedere accesso internet)"
    echo "Procedura manuale:"
    echo "  1. Apri http://192.168.56.20:3000"
    echo "  2. Login admin / Lab@2024!"
    echo "  3. Menu → Dashboards → Import"
    echo "  4. Inserisci ID: 1860"
    echo "  5. Seleziona datasource: Prometheus-Lab"
    echo "  6. Import"
fi

echo ""
echo "=== RIEPILOGO STACK MONITORAGGIO ==="
docker ps --filter "name=prometheus" --filter "name=node-exporter" --filter "name=grafana" \
    --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Checkpoint di verifica B2:**
- [ ] Grafana accessibile su http://192.168.56.20:3000 (admin/Lab@2024!)
- [ ] Data source Prometheus-Lab configurato e testato (verde)
- [ ] Dashboard Node Exporter (ID:1860) importata o importabile manualmente
- [ ] Pannelli CPU/RAM/Disco mostrano dati reali di SRV-LINUX-01

---

### Esercizio B3: Windows Exporter su DC-LAB-01

**Obiettivo.** Installare Windows Exporter su DC-LAB-01 e aggiungere DC-LAB-01 al monitoraggio Prometheus.

**Step 1 — Installa Windows Exporter su DC-LAB-01:**

```powershell
# Su DC-LAB-01 come Administrator

Write-Host "=== INSTALLAZIONE WINDOWS EXPORTER ==="

# Metodo 1: via Chocolatey (se disponibile)
if (Get-Command choco -ErrorAction SilentlyContinue) {
    choco install prometheus-windows-exporter -y
    Write-Host "[OK] Installato via Chocolatey"
} else {
    # Metodo 2: download manuale
    Write-Host "Chocolatey non disponibile."
    Write-Host "Scarica Windows Exporter da:"
    Write-Host "  https://github.com/prometheus-community/windows_exporter/releases"
    Write-Host ""
    Write-Host "Installazione MSI da command line:"
    Write-Host "  msiexec /i windows_exporter-X.X.X-amd64.msi ENABLED_COLLECTORS=`"cpu,cs,logical_disk,memory,net,os,process,service,system`" /qn"
    Write-Host ""
    Write-Host "Alternativa — avvia exporter temporaneamente per test:"
    Write-Host "  .\windows_exporter.exe --collectors.enabled=cpu,memory,logical_disk,os,service"
}

# Verifica che la porta 9182 sia in ascolto
Start-Sleep -Seconds 3
$port9182 = Get-NetTCPConnection -LocalPort 9182 -ErrorAction SilentlyContinue
if ($port9182) {
    Write-Host "[OK] Windows Exporter in ascolto su porta 9182"
} else {
    Write-Host "[INFO] Porta 9182 non in ascolto — installazione manuale richiesta"
}
```

**Step 2 — Configura Windows Firewall per Prometheus:**

```powershell
# Apri la porta 9182 per permettere a Prometheus di fare scrape
$ruleName = "Prometheus-WindowsExporter"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

if (-not $existingRule) {
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 9182 `
        -RemoteAddress "192.168.56.0/24" `
        -Action Allow `
        -Description "Prometheus scrape Windows Exporter"
    Write-Host "[OK] Regola firewall creata: porta 9182 aperta per 192.168.56.0/24"
} else {
    Write-Host "[OK] Regola firewall già esistente"
}

# Verifica accesso da SRV-LINUX-01 (eseguire su SRV-LINUX-01):
Write-Host ""
Write-Host "Verifica da SRV-LINUX-01:"
Write-Host "  curl -s http://192.168.56.10:9182/metrics | head -20"
Write-Host ""
Write-Host "Metriche Windows chiave disponibili:"
$winMetrics = @(
    "windows_cpu_time_total",
    "windows_logical_disk_free_bytes",
    "windows_memory_available_bytes",
    "windows_service_state",
    "windows_os_info"
)
$winMetrics | ForEach-Object { Write-Host "  → $_" }
```

**Step 3 — Aggiorna prometheus.yml per includere DC-LAB-01:**

```bash
# Su SRV-LINUX-01

echo "=== AGGIORNAMENTO PROMETHEUS.YML ==="

# Verifica che DC-LAB-01:9182 sia raggiungibile
if curl -s --connect-timeout 5 http://192.168.56.10:9182/metrics 2>/dev/null | grep -q "windows_"; then
    echo "[OK] Windows Exporter su DC-LAB-01 raggiungibile"
    
    # Aggiorna la configurazione Prometheus
    sed -i 's/  # - job_name: "windows_exporter"/  - job_name: "windows_exporter"/' \
        /monitoring/prometheus/prometheus.yml
    sed -i 's/  #   static_configs:/    static_configs:/' \
        /monitoring/prometheus/prometheus.yml
    sed -i 's/  #     - targets: \["192.168.56.10:9182"\]/      - targets: ["192.168.56.10:9182"]/' \
        /monitoring/prometheus/prometheus.yml
    sed -i 's/  #       labels:/        labels:/' \
        /monitoring/prometheus/prometheus.yml
    sed -i 's/  #         hostname: "dc-lab-01"/          hostname: "dc-lab-01"/' \
        /monitoring/prometheus/prometheus.yml
    sed -i 's/  #         env: "lab"/          env: "lab"/' \
        /monitoring/prometheus/prometheus.yml
    
    # Ricarica configurazione Prometheus (senza riavvio)
    curl -s -X POST http://localhost:9090/-/reload
    echo "[OK] Prometheus ricaricato — DC-LAB-01 aggiunto al monitoraggio"
else
    echo "[INFO] DC-LAB-01:9182 non raggiungibile"
    echo "  1. Verifica che Windows Exporter sia installato e avviato su DC-LAB-01"
    echo "  2. Verifica regola firewall su DC-LAB-01 (porta 9182)"
    echo "  3. Rimuovi il commento dalla configurazione windows_exporter in prometheus.yml"
fi
```

**Checkpoint di verifica B3:**
- [ ] Windows Exporter installato su DC-LAB-01 (o procedura nota)
- [ ] Porta 9182 aperta nel firewall di DC-LAB-01 per 192.168.56.0/24
- [ ] DC-LAB-01 visibile nei targets Prometheus (se raggiungibile)
- [ ] Query `windows_memory_available_bytes` funziona in Prometheus

---

### Esercizio B4: Configurare Regole di Alert in Prometheus

**Obiettivo.** Configurare le regole di alert Prometheus per CPU, disco, RAM e disponibilità dei servizi.

**Step 1 — Crea regole di alert:**

```bash
# Su SRV-LINUX-01

mkdir -p /monitoring/prometheus/rules

cat > /monitoring/prometheus/rules/lab-alerts.yml << 'EOF'
groups:
  - name: lab_infrastructure
    # Intervallo di valutazione delle regole
    interval: 30s
    rules:

      # ─── CPU ─────────────────────────────────────────────────────
      - alert: HighCPUUsage
        expr: |
          100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "CPU alta su {{ $labels.instance }}"
          description: "CPU utilizzo {{ $value | humanize }}% da 5 minuti (soglia: 80%)"
          runbook: "Verifica con 'top' o 'ps aux --sort=-%cpu | head -10'"

      - alert: CriticalCPUUsage
        expr: |
          100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 95
        for: 3m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "CPU CRITICA su {{ $labels.instance }}"
          description: "CPU utilizzo {{ $value | humanize }}% (soglia critica: 95%)"
          runbook: "Identifica processo anomalo, considera kill o riavvio servizio"

      # ─── MEMORIA ──────────────────────────────────────────────────
      - alert: HighMemoryUsage
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Memoria alta su {{ $labels.instance }}"
          description: "RAM usata {{ $value | humanize }}% (soglia: 85%)"

      - alert: CriticalMemoryUsage
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 95
        for: 3m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Memoria CRITICA su {{ $labels.instance }}"
          description: "RAM usata {{ $value | humanize }}% - rischio OOM killer"

      # ─── DISCO ────────────────────────────────────────────────────
      - alert: HighDiskUsage
        expr: |
          100 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs"} /
                  node_filesystem_size_bytes * 100) > 80
        for: 10m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Disco quasi pieno su {{ $labels.instance }}:{{ $labels.mountpoint }}"
          description: "Utilizzo {{ $value | humanize }}% su {{ $labels.mountpoint }}"
          runbook: "Pulizia log: journalctl --vacuum-size=500M, find /var/log -name '*.gz' -delete"

      - alert: CriticalDiskUsage
        expr: |
          100 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs"} /
                  node_filesystem_size_bytes * 100) > 90
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Disco CRITICO su {{ $labels.instance }}:{{ $labels.mountpoint }}"
          description: "Utilizzo {{ $value | humanize }}% — azione immediata!"

      # ─── DISCO IN ESAURIMENTO (PREVISIONE) ───────────────────────
      - alert: DiskWillFillIn24h
        expr: |
          predict_linear(
            node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs"}[6h],
            24 * 3600
          ) < 0
        for: 30m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Disco si esaurirà in 24h: {{ $labels.instance }}:{{ $labels.mountpoint }}"
          description: "Basandosi sul trend attuale, il disco si riempirà entro 24 ore"

      # ─── HOST DOWN ────────────────────────────────────────────────
      - alert: InstanceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "HOST NON RAGGIUNGIBILE: {{ $labels.instance }}"
          description: "{{ $labels.instance }} ({{ $labels.job }}) non risponde da 2 minuti"
          runbook: "Verifica: ping {{ $labels.instance }}, SSH, stato VM nell'hypervisor"

      # ─── LOAD AVERAGE ─────────────────────────────────────────────
      - alert: HighLoadAverage
        expr: |
          node_load5 > on (instance) (count by (instance) (node_cpu_seconds_total{mode="idle"}) * 1.5)
        for: 10m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Load average elevato su {{ $labels.instance }}"
          description: "Load 5m: {{ $value | humanize }} (soglia: N_CPU * 1.5)"
EOF

echo "[OK] Regole alert create in /monitoring/prometheus/rules/lab-alerts.yml"
echo "Ricarico configurazione Prometheus..."
curl -s -X POST http://localhost:9090/-/reload && echo "[OK] Prometheus ricaricato"

echo ""
echo "Verifica regole caricate:"
curl -s http://localhost:9090/api/v1/rules 2>/dev/null | python3 -c "
import sys,json
d = json.load(sys.stdin)
for group in d.get('data',{}).get('groups',[]):
    for rule in group.get('rules',[]):
        if rule.get('type') == 'alerting':
            print(f\"  [{rule.get('state','unknown').upper()}] {rule.get('name')}\")
" 2>/dev/null || echo "  (apri http://192.168.56.20:9090/alerts)"
```

**Step 2 — Verifica alert in Prometheus UI:**

```bash
echo ""
echo "=== VERIFICA ALERT ==="
echo "Apri: http://192.168.56.20:9090/alerts"
echo ""
echo "Dovresti vedere:"
echo "  - Tutte le regole in stato INACTIVE (nessun problema attivo = buono!)"
echo "  - Regole verde = sane"
echo "  - Regole gialle/rosse = problema rilevato"
echo ""

# Simula un alert di disco per test (crea file temporaneo grande)
echo "Vuoi testare un alert? (simula disco pieno su /tmp)"
echo "  # Crea file da 1GB in /tmp (occupazione temporanea):"
echo "  dd if=/dev/zero of=/tmp/testfile bs=1M count=500"
echo "  # Elimina dopo il test:"
echo "  rm /tmp/testfile"
echo ""
echo "ATTENZIONE: esegui solo se hai spazio sufficiente (/tmp)"

# Test query per stato disco attuale
DISK_PCT=$(curl -s 'http://localhost:9090/api/v1/query?query=100%20-%20(node_filesystem_avail_bytes%7Bmountpoint%3D%22%2F%22%7D%20%2F%20node_filesystem_size_bytes%7Bmountpoint%3D%22%2F%22%7D%20*%20100)' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('data',{}).get('result',[]); print(f'{float(r[0][\"value\"][1]):.1f}%' if r else 'N/A')" 2>/dev/null || echo "N/A")
echo "Disco root attuale: ${DISK_PCT}"
```

**Checkpoint di verifica B4:**
- [ ] File lab-alerts.yml creato con almeno 6 regole
- [ ] Prometheus carica le regole senza errori
- [ ] Regole visibili nella sezione /alerts di Prometheus
- [ ] Almeno una query di test restituisce dati corretti

---

### Esercizio B5: Uptime Kuma — Monitoraggio Sintetico

**Obiettivo.** Installare Uptime Kuma per il monitoraggio sintetico degli endpoint del lab (GLPI, DC-LAB-01 RDP, SRV-LINUX-01 SSH).

**Background.** Uptime Kuma è il modo più rapido per avere un monitoraggio "dall'esterno" dei servizi: simula la prospettiva dell'utente finale. Mentre Node Exporter dice "la CPU di SRV-LINUX-01 è al 45%", Uptime Kuma dice "il sito GLPI risponde in 230ms con HTTP 200 OK" — esattamente quello che l'utente sperimenta.

**Step 1 — Installa Uptime Kuma:**

```bash
# Su SRV-LINUX-01

docker run -d \
    --name uptime-kuma \
    -p 3001:3001 \
    --volume="/monitoring/uptime-kuma:/app/data" \
    --restart unless-stopped \
    louislam/uptime-kuma:latest

echo "Attendo avvio Uptime Kuma..."
sleep 10

if curl -s http://localhost:3001 | grep -q "Uptime\|html"; then
    echo "[OK] Uptime Kuma avviato su http://192.168.56.20:3001"
    echo "     Prima configurazione: crea account admin alla prima visita"
else
    echo "[CHECK] $(docker logs uptime-kuma 2>&1 | tail -5)"
fi
```

**Step 2 — Configura monitor via API (dopo primo setup manuale):**

```bash
echo ""
echo "=== CONFIGURAZIONE UPTIME KUMA ==="
echo ""
echo "PRIMO ACCESSO — procedura manuale:"
echo "  1. Apri http://192.168.56.20:3001"
echo "  2. Crea account admin: admin / Lab@2024!"
echo "  3. Aggiungi monitor per ogni servizio del lab:"
echo ""
echo "  MONITOR 1 — GLPI Web Interface:"
echo "    Tipo: HTTP(s)"
echo "    URL: http://192.168.56.20:8080/glpi"
echo "    Intervallo: 60 secondi"
echo "    Timeout: 30 secondi"
echo "    Keyword attesa: 'GLPI' (content check)"
echo ""
echo "  MONITOR 2 — DC-LAB-01 ping:"
echo "    Tipo: Ping"
echo "    Hostname: 192.168.56.10"
echo "    Intervallo: 60 secondi"
echo ""
echo "  MONITOR 3 — SSH SRV-LINUX-01:"
echo "    Tipo: TCP Port"
echo "    Hostname: 192.168.56.20"
echo "    Porta: 22"
echo "    Intervallo: 60 secondi"
echo ""
echo "  MONITOR 4 — Prometheus:"
echo "    Tipo: HTTP(s)"
echo "    URL: http://192.168.56.20:9090/-/healthy"
echo "    Intervallo: 30 secondi"
echo ""
echo "  MONITOR 5 — Grafana:"
echo "    Tipo: HTTP(s)"
echo "    URL: http://192.168.56.20:3000/api/health"
echo "    Intervallo: 60 secondi"
```

**Step 3 — Crea status page pubblica:**

```bash
echo ""
echo "=== STATUS PAGE ==="
echo "In Uptime Kuma → Status Pages → New:"
echo "  Nome: LAB Infrastructure Status"
echo "  Slug: lab-status"
echo "  Aggiungi tutti i monitor configurati"
echo ""
echo "Risultato: http://192.168.56.20:3001/status/lab-status"
echo "Questa pagina può essere mostrata agli utenti durante un'interruzione"
echo "(nessun login richiesto — accesso pubblico)"
echo ""
echo "=== RIEPILOGO STACK COMPLETO ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAME|prometheus|grafana|node-exporter|uptime-kuma"
```

**Checkpoint di verifica B5:**
- [ ] Uptime Kuma avviato su http://192.168.56.20:3001
- [ ] Almeno 3 monitor configurati (GLPI, DC-LAB-01 ping, SRV-LINUX-01 SSH)
- [ ] Monitor mostrano stato UP
- [ ] Status page creata e accessibile senza login

---

## PART C: SISTEMATIZZARE — Monitoraggio come Pratica Operativa

---

### Progetto C1: SOP-MON-001 — Revisione Alert Mensile

```
Documento: SOP-MON-001
Titolo:    Revisione Mensile Alert e Dashboard Monitoraggio
Versione:  1.0
Owner:     IT Operations
Frequenza: Primo lunedì del mese
Durata:    30-45 minuti

OBIETTIVO:
  Garantire che il sistema di monitoraggio sia calibrato:
  - Alert che scattano inutilmente → alzare soglia
  - Problemi passati inosservati → abbassare soglia o aggiungere alert
  - Dashboard non usate → rimuoverle (riduce cognitive load)

CHECKLIST MENSILE:

[ ] 1. ANALISI ALERT SCATTATI NEL MESE:
    Prometheus UI → Alertmanager → History
    (o: grep /var/log/alertmanager/alertmanager.log | grep -c "alert")
    
    Per ogni alert scattato > 10 volte nel mese:
    - Era un problema reale? → No? Alza la soglia
    - Ha richiesto un'azione? → No? Trasforma in log invece di alert
    
    Per ogni problema segnalato dagli utenti che NON ha generato alert:
    - Aggiungi alert appropriato
    - Abbassa soglia se troppo permissiva

[ ] 2. REVISIONE SOGLIE:
    Verifica che le soglie siano ancora appropriate:
    □ CPU: il server ha cambiato carico di lavoro? Aggiungi pattern stagionali?
    □ Disco: calcola la crescita media mensile, aggiorna predict_linear()
    □ Certificati SSL: lista certificati in scadenza entro 90gg
    
    Query utile per certificati:
    curl -s 'http://localhost:9090/api/v1/query?query=probe_ssl_earliest_cert_expiry'

[ ] 3. VERIFICA COPERTURA:
    Tutti i sistemi critici hanno monitor in Uptime Kuma?
    □ GLPI (http)
    □ DC-LAB-01 (ping)
    □ SRV-LINUX-01 SSH (tcp:22)
    □ Prometheus (http)
    □ Grafana (http)
    
    Tutti i sistemi critici hanno Node Exporter / Windows Exporter?
    □ SRV-LINUX-01 (node-exporter:9100)
    □ DC-LAB-01 (windows-exporter:9182)

[ ] 4. TEST DASHBOARD:
    Apri ogni dashboard in Grafana:
    - Tutti i pannelli mostrano dati? (nessun "No data")
    - Le query sono ancora valide (metriche non rinominate)?
    - I pannelli coprono le esigenze attuali?

[ ] 5. AGGIORNAMENTO DOCUMENTAZIONE:
    Aggiorna /monitoring/README.md con:
    - Qualsiasi modifica a soglie o alert
    - Nuovi monitor aggiunti
    - Problemi noti del sistema di monitoraggio
```

---

### Progetto C2: Script monitoring_health.sh

```bash
#!/usr/bin/env bash
# monitoring_health.sh — Verifica salute dello stack di monitoraggio
# Uso: ./monitoring_health.sh [--json]

set -euo pipefail

PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"
UPTIME_KUMA_URL="http://localhost:3001"
ISSUES=()
WARNINGS=()
STATUS="OK"
JSON_OUTPUT=false
[[ "${1:-}" == "--json" ]] && JSON_OUTPUT=true

log() { [[ "$JSON_OUTPUT" != true ]] && echo "[$(date '+%H:%M:%S')] $*"; }

# ─── CHECK 1: CONTAINER DOCKER ────────────────────────────────────
check_containers() {
    log "CHECK 1: Container Docker monitoraggio..."
    for container in prometheus node-exporter grafana uptime-kuma; do
        STATUS_C=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")
        if [[ "$STATUS_C" == "running" ]]; then
            log "  [OK] $container: running"
        elif [[ "$STATUS_C" == "not_found" ]]; then
            WARNINGS+=("CONTAINER: $container non trovato (potrebbe non essere installato)")
        else
            ISSUES+=("CONTAINER: $container in stato '$STATUS_C' (non running)")
        fi
    done
}

# ─── CHECK 2: ENDPOINT HTTP ───────────────────────────────────────
check_endpoints() {
    log "CHECK 2: Endpoint HTTP..."
    
    # Prometheus health
    if curl -s --connect-timeout 5 "$PROMETHEUS_URL/-/healthy" 2>/dev/null | grep -q "Prometheus"; then
        log "  [OK] Prometheus: healthy"
    else
        ISSUES+=("ENDPOINT: Prometheus non risponde su $PROMETHEUS_URL")
    fi
    
    # Grafana health
    if curl -s --connect-timeout 5 "$GRAFANA_URL/api/health" 2>/dev/null | grep -q "ok"; then
        log "  [OK] Grafana: healthy"
    else
        WARNINGS+=("ENDPOINT: Grafana non risponde su $GRAFANA_URL")
    fi
    
    # Node Exporter metrics
    if curl -s --connect-timeout 5 "http://localhost:9100/metrics" 2>/dev/null | grep -q "node_cpu"; then
        log "  [OK] Node Exporter: metriche disponibili"
    else
        ISSUES+=("ENDPOINT: Node Exporter non espone metriche su :9100")
    fi
}

# ─── CHECK 3: TARGETS PROMETHEUS ─────────────────────────────────
check_prometheus_targets() {
    log "CHECK 3: Target Prometheus..."
    
    local targets_json
    targets_json=$(curl -s --connect-timeout 5 "$PROMETHEUS_URL/api/v1/targets" 2>/dev/null || echo '{}')
    
    # Conta target UP vs DOWN
    local up_count down_count
    up_count=$(echo "$targets_json" | python3 -c "import sys,json; d=json.load(sys.stdin); targets=d.get('data',{}).get('activeTargets',[]); print(sum(1 for t in targets if t.get('health')=='up'))" 2>/dev/null || echo 0)
    down_count=$(echo "$targets_json" | python3 -c "import sys,json; d=json.load(sys.stdin); targets=d.get('data',{}).get('activeTargets',[]); print(sum(1 for t in targets if t.get('health')!='up'))" 2>/dev/null || echo 0)
    
    log "  Target UP: $up_count | Target DOWN: $down_count"
    
    if [[ "$down_count" -gt 0 ]]; then
        # Elenca target down
        local down_targets
        down_targets=$(echo "$targets_json" | python3 -c "
import sys,json
d = json.load(sys.stdin)
for t in d.get('data',{}).get('activeTargets',[]):
    if t.get('health') != 'up':
        print(f\"  - {t.get('labels',{}).get('job','')} ({t.get('labels',{}).get('instance','')})\")
" 2>/dev/null)
        ISSUES+=("TARGETS: $down_count target non raggiungibili:$down_targets")
    fi
}

# ─── CHECK 4: REGOLE ALERT ────────────────────────────────────────
check_alert_rules() {
    log "CHECK 4: Regole alert Prometheus..."
    
    local rules_json
    rules_json=$(curl -s --connect-timeout 5 "$PROMETHEUS_URL/api/v1/rules" 2>/dev/null || echo '{}')
    
    local total_rules firing_count
    total_rules=$(echo "$rules_json" | python3 -c "
import sys,json; d=json.load(sys.stdin)
count = sum(len(g.get('rules',[])) for g in d.get('data',{}).get('groups',[]))
print(count)" 2>/dev/null || echo 0)
    
    firing_count=$(echo "$rules_json" | python3 -c "
import sys,json; d=json.load(sys.stdin)
count = sum(1 for g in d.get('data',{}).get('groups',[]) 
            for r in g.get('rules',[]) if r.get('state')=='firing')
print(count)" 2>/dev/null || echo 0)
    
    log "  Regole totali: $total_rules | Firing: $firing_count"
    
    if [[ "$total_rules" -eq 0 ]]; then
        WARNINGS+=("RULES: nessuna regola alert configurata")
    fi
    
    if [[ "$firing_count" -gt 0 ]]; then
        WARNINGS+=("RULES: $firing_count alert attivi — verifica Prometheus alerts")
    fi
}

# ─── ESEGUI ──────────────────────────────────────────────────────
log "=========================================="
log "MONITORING STACK HEALTH CHECK"
log "$(date '+%Y-%m-%d %H:%M:%S')"
log "=========================================="

check_containers
check_endpoints
check_prometheus_targets
check_alert_rules

[[ "${#ISSUES[@]}"   -gt 0 ]] && STATUS="CRITICAL"
[[ "${#WARNINGS[@]}" -gt 0 ]] && [[ "$STATUS" == "OK" ]] && STATUS="WARNING"

if [[ "$JSON_OUTPUT" == true ]]; then
    cat << EOF
{
  "timestamp": "$(date '+%Y-%m-%d %H:%M:%S')",
  "status": "$STATUS",
  "issues": $(printf '%s\n' "${ISSUES[@]:-}" | jq -R . | jq -s .),
  "warnings": $(printf '%s\n' "${WARNINGS[@]:-}" | jq -R . | jq -s .)
}
EOF
else
    log ""
    log "STATUS: $STATUS | Issues: ${#ISSUES[@]} | Warnings: ${#WARNINGS[@]}"
    for i in "${ISSUES[@]}"; do log "  [ISSUE] $i"; done
    for w in "${WARNINGS[@]}"; do log "  [WARN]  $w"; done
fi

case "$STATUS" in
    "OK")       exit 0 ;;
    "WARNING")  exit 1 ;;
    *)          exit 2 ;;
esac
```

**Installazione:**

```bash
sudo cp /tmp/monitoring_health.sh /usr/local/bin/monitoring_health.sh
sudo chmod +x /usr/local/bin/monitoring_health.sh

# Test
bash /usr/local/bin/monitoring_health.sh
bash /usr/local/bin/monitoring_health.sh --json

# Cron: check ogni ora
echo "0 * * * * lab-admin /usr/local/bin/monitoring_health.sh >> /var/log/monitoring_health.log 2>&1"
```

---

### Progetto C3: Integrazione ITIL — Monitoraggio e Service Management

```
ITIL v4 PRACTICE: Monitoraggio e Gestione degli Event

Il monitoraggio non è un'attività tecnica isolata: è il sistema
nervoso del Service Management. Ogni alert è un "evento" nel
vocabolario ITIL, e deve essere gestito in modo strutturato.

TIPI DI EVENTO ITIL:
  Informational: CPU 45% (dato normale, nessuna azione)
  Warning:       CPU 82% (da tenere d'occhio)
  Exception:     CPU 97% → genera INCIDENT automatico

INTEGRAZIONE PROMETHEUS → GLPI:

  Quando Alertmanager riceve un alert critico, può aprire 
  automaticamente un ticket in GLPI tramite webhook:
  
  Alertmanager → webhook → script Python → API GLPI
  
  Script Python di base (webhook receiver):
  
  from flask import Flask, request
  import requests
  
  app = Flask(__name__)
  GLPI_URL = "http://192.168.56.20:8080/glpi"
  GLPI_TOKEN = "xxx"
  
  @app.route("/webhook", methods=["POST"])
  def receive_alert():
      for alert in request.json.get("alerts", []):
          if alert["status"] == "firing":
              # Crea ticket GLPI
              requests.post(f"{GLPI_URL}/apirest.php/Ticket", ...)
      return "OK", 200

MAPPING EVENTI → ITIL:

  Evento                  | ITIL Practice         | GLPI Action
  ─────────────────────────────────────────────────────────────────
  HostDown (Critical)     | Incident Management   | Ticket P1 auto
  HighDiskUsage (Warning) | Event Management      | Ticket P3 auto
  CriticalMemory          | Incident Management   | Ticket P2 auto
  DiskWillFill24h         | Problem Management    | Ticket tipo Problem
  CertScadenza30gg        | Change Management     | Change Request cert
  BackupFallito           | Availability Mgmt     | Ticket P2 + escalation

METRICHE ITIL DA ESPORRE IN GRAFANA:
  Dashboard "ITIL KPI" con:
  - MTTR (Mean Time To Repair): avg tempo chiusura ticket P1/P2
  - MTTD (Mean Time To Detect): tempo da evento a apertura ticket
  - Availability: % uptime per sistema (da Prometheus)
  - Incident Volume: trend mensile ticket aperti
  (Dati da GLPI API + Prometheus)
```

---

## Checklist di Validazione Lab — ops07a

```
FONDAMENTI (Part A):
  [ ] A1: Sai spiegare i tre pilastri dell'observability (metrics/logs/traces)
  [ ] A2: Conosci il modello pull di Prometheus (scrape → TSDB → query)
  [ ] A3: Sai scrivere una query PromQL per CPU%, RAM%, disco%
  [ ] A4: Conosci la regola d'oro degli alert e le soglie standard
  [ ] A5: Sai perché SNMPv3 è obbligatorio e a cosa servono gli OID

OPERAZIONI (Part B):
  [ ] B1: Prometheus e Node Exporter avviati e comunicanti (target UP)
  [ ] B2: Grafana collegato a Prometheus, dashboard Node Exporter importata
  [ ] B3: Windows Exporter su DC-LAB-01 installato o procedura documentata
  [ ] B4: Regole alert create con 6+ regole per CPU/RAM/disco/host down
  [ ] B5: Uptime Kuma avviato con almeno 3 monitor configurati

SISTEMATIZZARE (Part C):
  [ ] C1: SOP-MON-001 letta e capita
  [ ] C2: Script monitoring_health.sh installato e funzionante
  [ ] C3: Collegamento GLPI/ITIL documentato o webhook pianificato
```

---

## Appendice A: Comandi Prometheus/Grafana Rapidi

```bash
# ─── GESTIONE STACK DOCKER ────────────────────────────────────────
# Verifica stato
docker ps --filter "name=prometheus" --filter "name=grafana" \
    --filter "name=node-exporter" --filter "name=uptime-kuma"

# Ricarica configurazione Prometheus (senza riavvio)
curl -X POST http://localhost:9090/-/reload

# Logs Prometheus
docker logs prometheus --tail 50

# Logs Grafana
docker logs grafana --tail 50

# Riavvio singolo container
docker restart prometheus
docker restart grafana

# ─── QUERY PROMQL UTILI ───────────────────────────────────────────
# CPU utilizzo per host
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Top 3 processi per CPU (richiede process exporter)
topk(3, process_cpu_seconds_total)

# Disco in esaurimento — previsione 24h
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 86400)

# Traffico di rete (bytes/s)
rate(node_network_receive_bytes_total{device!="lo"}[5m])

# Tasso errori HTTP (se applicazione espone metriche)
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# ─── GRAFANA API ──────────────────────────────────────────────────
# Lista datasources
curl -s -u admin:Lab@2024! http://localhost:3000/api/datasources

# Lista dashboard
curl -s -u admin:Lab@2024! http://localhost:3000/api/search | python3 -m json.tool

# Health check
curl -s http://localhost:3000/api/health
```

---

## Appendice B: Tabella Comparativa Strumenti Monitoraggio

```
Strumento      | Tipo          | Forza             | Limite            | Lab/Prod
───────────────────────────────────────────────────────────────────────────────────
Prometheus     | Metriche pull | PromQL potente    | No retention lunga | Entrambi
Grafana        | Visualiz.     | Dashboard flessib | Non raccoglie dati | Entrambi
Node Exporter  | Agent Linux   | 200+ metriche OS  | Solo Linux        | Entrambi
Win. Exporter  | Agent Windows | 50+ metriche OS   | Solo Windows      | Entrambi
Uptime Kuma    | Sintetico     | Semplice, rapido  | No PromQL         | Lab/PMI
Zabbix         | All-in-one    | Completo, SNMP    | Curva apprendim.  | Produzione
ELK/Loki       | Log           | Ricerca potente   | Risorse elevate   | Produzione
Alertmanager   | Alert routing | Grouping/dedup    | Config verbosa    | Entrambi
```

---

## Riferimenti

- `07-monitoraggio-incidenti.md` — sezioni 2 (sistemi) e 3 (alert management)
- Prometheus documentation: https://prometheus.io/docs/
- Grafana dashboard community: https://grafana.com/grafana/dashboards/
- Node Exporter Full dashboard (ID 1860): Grafana community
- ITIL v4 Practice Guide: Monitoring and Event Management
- **Tutorial successivo:** `tutorial_ops07_ch1b_incident_management_lab.md`
