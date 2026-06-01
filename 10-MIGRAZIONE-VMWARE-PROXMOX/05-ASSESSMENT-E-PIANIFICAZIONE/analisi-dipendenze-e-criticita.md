# Analisi delle Dipendenze e Classificazione delle Criticità

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 2 — Assessment · Modulo 05.2 (segue 05.1, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 05.1 (inventario VMware completo); concetti di Application Dependency Mapping (ADM); base di analisi del traffico di rete (NetFlow/IPFIX/sFlow); concetti di risk scoring.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. produrre un grafo di dipendenze applicative fra VM e servizi esterni, partendo dall'inventario di 05.1 e arricchendolo con dati NetFlow / IPFIX / sFlow / pcap;
> 2. classificare le VM per criticita business (Tier 0/1/2/3) usando criteri espliciti e tracciabili (ricavi-impact, normative, RTO/RPO, numero di utenti, vincoli di integrazione);
> 3. costruire una matrice di rischio per ogni VM con probabilita × impatto, motivando la scelta della strategia di migrazione (cold/warm/live/app-level) sulla base del rischio;
> 4. progettare le **wave** di migrazione con criteri di scelta espliciti: prima le VM stand-alone Tier 3, poi i servizi infrastrutturali (DNS, AD secondari, NTP), poi le applicazioni Tier 2, infine Tier 1/0 con piano di rollback rigoroso;
> 5. usare strumenti di ADM (NSX Intelligence, vRealize Network Insight, BloodHound, nfdump) e produrre output leggibili (JSON o GraphML) per integrazione con sistemi di project management;
> 6. comunicare i risultati con artefatti adatti alle audience: matrice di rischio per CIO/CTO, grafo di dipendenze per architetti, lista priorizzata wave per operatori.
> **Tempo stimato:** lettura 60-90 min · lab/analysis 240-480 min (dipende dalla scala dell'ambiente censito)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** vSphere 7.0/8.0 con NSX-T 3.x/4.x (per flow data), nfdump 1.7+, RVTools 4.x.

## Mappa concettuale

```
+======================================================+
|  Da inventario a piano: la pipeline di analisi       |
+======================================================+
|                                                      |
|   INPUT (da modulo 05.1)                             |
|   +-- vm-inventory.csv                               |
|   +-- vm-disks.csv                                   |
|   +-- portgroups.csv (VLAN + IP per VM)              |
|   +-- snapshot/dvSwitch/cluster CSV                  |
|         |                                            |
|         v                                            |
|   ARRICCHIMENTO con DATI DI FLUSSO                   |
|   +-- NetFlow / IPFIX (router, firewall)             |
|   +-- sFlow (switch top-of-rack)                     |
|   +-- VMware NSX-T flow                              |
|   +-- Eventuali agent (Datadog, Dynatrace)           |
|         |                                            |
|         v                                            |
|   ADM: GRAFO DI DIPENDENZE                           |
|     - Nodi: VM, servizi, gruppi applicativi          |
|     - Archi: connessioni IP/porta osservate          |
|     - Etichette: protocollo, frequenza, volume       |
|         |                                            |
|         v                                            |
|   CLASSIFICAZIONE CRITICITA                          |
|     Tier 0: indispensabile, downtime = no            |
|     Tier 1: business critical, RTO < 1h              |
|     Tier 2: importante, RTO < 4h                     |
|     Tier 3: standard, RTO 1 giorno                   |
|         |                                            |
|         v                                            |
|   RISK SCORING (probabilita x impatto)               |
|     Per ogni VM: rischio P*I + strategia migrazione  |
|         |                                            |
|         v                                            |
|   WAVE PLANNING                                      |
|     Wave 1: VM stand-alone Tier 3                    |
|     Wave 2: servizi infrastrutturali                 |
|     Wave 3: app Tier 2                               |
|     Wave 4: Tier 1 (cluster, DB primario)            |
|     Wave 5: Tier 0 (con DR pre-live)                 |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Le dipendenze nascoste sono il primo rischio.** Una VM "stand-alone" che dipende silenziosamente da un servizio Tier 0 (Active Directory, DNS interno, NTP, file share comune) puo bloccare il cutover. NetFlow/IPFIX dei 2-4 settimane *prima* della migrazione mostra il traffico reale, non quello dichiarato.
2. **La criticita non e auto-dichiarata.** Owner di applicazione e business sono parziali — tutti dichiarano "Tier 1". Usare criteri oggettivi: revenue contribution (€/ora), numero di utenti, presenza di SLA contrattuale, vincoli normativi (GDPR, NIS2, dato sanitario, dato finanziario).
3. **Risk score = probabilita × impatto, ma probabilita non e fissa.** La probabilita di problemi in migrazione varia per: HW version vecchia, snapshot stale, applicazione legacy non testata su KVM, dipendenze inverse (chi dipende dalla VM), dimensione del disco, frequenza di scrittura. Non si dichiara, si misura su VM analoghe gia migrate.
4. **Wave: dipendenze prima della criticita.** L'errore tipico e migrare per criticita decrescente (T3 → T0). Errore: i T0 hanno spesso dipendenze infrastrutturali che vivono in T1/T2; vanno migrate dopo che le dipendenze sono operative su Proxmox. La sequenza giusta: stand-alone T3 → infrastrutturali T1 (AD secondari, DNS) → app T2 → cluster app T1 → T0 con DR pre-live.
5. **ADM e un investimento, non una formalita.** Costa giorni ma evita settimane di rollback. Strumenti: NSX Intelligence (se gia in uso), vRealize Network Insight (a pagamento, ma 30 gg di trial), nfdump per chi ha solo flow esterni, BloodHound per AD-centric, Wireshark per spot-check. In assenza, almeno fare `ss -tnp` e `netstat -anp` su ogni VM e correlare.

## Indice
- [Panoramica](#panoramica)
- [Application Dependency Mapping](#application-dependency-mapping)
- [Analisi dei Flussi di Rete](#analisi-dei-flussi-di-rete)
- [Classificazione di Criticità (Tier 0-3)](#classificazione-di-criticità-tier-0-3)
- [Risk Scoring per Virtual Machine](#risk-scoring-per-virtual-machine)
- [Matrici di Dipendenza](#matrici-di-dipendenza)
- [Pianificazione delle Wave di Migrazione](#pianificazione-delle-wave-di-migrazione)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

L'analisi delle dipendenze è la fase che trasforma un inventario tecnico in una mappa operativa dell'ambiente. Conoscere quante vCPU e quanta RAM ha una VM è necessario ma insufficiente: per pianificare una migrazione sicura, bisogna comprendere quali VM comunicano tra loro, quali servizi dipendono da quali infrastrutture, e quale impatto avrebbe il fermo di ciascun componente sull'operatività aziendale.

Questa fase risponde a domande fondamentali: se migro la VM "app-server-01" a Proxmox, quali altri sistemi saranno impattati? Posso migrare il database server separatamente dall'application server? Quali VM devono essere migrate insieme nella stessa wave per evitare di spezzare dipendenze critiche? Qual è l'ordine corretto di migrazione per minimizzare il rischio?

Il risultato di questa analisi è una classificazione di criticità per ogni VM, una matrice di dipendenze che evidenzia i legami tra sistemi, e un piano di wave di migrazione che rispetta i vincoli operativi. Senza questo lavoro, il rischio di causare outage non pianificati durante la migrazione è significativamente più alto.

---

## Application Dependency Mapping

### Approcci alla Raccolta delle Dipendenze

Esistono tre approcci complementari per mappare le dipendenze applicative, e una strategia robusta li combina tutti:

**1. Approccio top-down (interviste e documentazione)**
Si parte dalla documentazione esistente — CMDB, diagrammi architetturali, runbook — e si conducono interviste strutturate con i team applicativi e infrastrutturali. Questo approccio cattura dipendenze logiche e di business che non sono visibili a livello di rete.

**2. Approccio bottom-up (analisi del traffico di rete)**
Si analizzano i flussi di rete reali per identificare quali VM comunicano tra loro, su quali porte e con quale frequenza. Questo approccio cattura dipendenze tecniche effettive, incluse quelle non documentate.

**3. Approccio agent-based (strumenti di discovery)**
Si installano agent sulle VM che raccolgono informazioni su processi, connessioni di rete, file system e configurazioni. Questo approccio fornisce il livello di dettaglio più alto ma richiede accesso ai guest OS.

### Strumenti per il Discovery delle Dipendenze

| Strumento | Tipo | Funzionalità Chiave | Costo |
|-----------|------|---------------------|-------|
| VMware Aria Operations (ex vROps) | Agentless + Agent | Topology map, capacity analytics | Licenza VMware |
| VMware Aria Migration (ex vR Network Insight) | Network flow analysis | NSX integration, flow visualization | Licenza VMware |
| netstat / ss (Linux) | Agent-based (manuale) | Connessioni attive per VM | Gratuito |
| Wireshark / tcpdump | Packet capture | Analisi dettagliata traffico | Gratuito |
| NetFlow/sFlow collector | Network-based | Flussi aggregati tra IP | Vario |
| nmap | Network scanner | Port scanning, service detection | Gratuito |

### Raccolta Manuale delle Dipendenze con Script

Quando strumenti commerciali non sono disponibili, si possono raccogliere dipendenze direttamente dai guest OS:

```bash
#!/bin/bash
# Script da eseguire su ogni VM Linux per raccogliere dipendenze di rete
# Output: connessioni attive, porte in ascolto, configurazioni DNS/hosts

HOSTNAME=$(hostname -f)
OUTPUT_DIR="/tmp/dep_analysis"
mkdir -p "$OUTPUT_DIR"

echo "=== Dependency Analysis: $HOSTNAME ===" > "$OUTPUT_DIR/report.txt"
echo "Data: $(date -Iseconds)" >> "$OUTPUT_DIR/report.txt"

# Porte in ascolto
echo -e "\n=== LISTENING PORTS ===" >> "$OUTPUT_DIR/report.txt"
ss -tlnp 2>/dev/null >> "$OUTPUT_DIR/report.txt"

# Connessioni stabilite (escluse loopback)
echo -e "\n=== ESTABLISHED CONNECTIONS ===" >> "$OUTPUT_DIR/report.txt"
ss -tnp state established '( not dst 127.0.0.0/8 )' 2>/dev/null >> "$OUTPUT_DIR/report.txt"

# Configurazione DNS
echo -e "\n=== DNS CONFIGURATION ===" >> "$OUTPUT_DIR/report.txt"
cat /etc/resolv.conf >> "$OUTPUT_DIR/report.txt"

# File hosts (dipendenze hardcoded)
echo -e "\n=== /etc/hosts ===" >> "$OUTPUT_DIR/report.txt"
grep -v "^#" /etc/hosts | grep -v "^$" >> "$OUTPUT_DIR/report.txt"

# Mount NFS/CIFS
echo -e "\n=== NETWORK MOUNTS ===" >> "$OUTPUT_DIR/report.txt"
mount | grep -E "nfs|cifs|smb" >> "$OUTPUT_DIR/report.txt"

# Crontab (dipendenze schedulte)
echo -e "\n=== SCHEDULED TASKS ===" >> "$OUTPUT_DIR/report.txt"
crontab -l 2>/dev/null >> "$OUTPUT_DIR/report.txt"
ls /etc/cron.d/ 2>/dev/null >> "$OUTPUT_DIR/report.txt"

# Servizi attivi
echo -e "\n=== ACTIVE SERVICES ===" >> "$OUTPUT_DIR/report.txt"
systemctl list-units --type=service --state=running --no-pager 2>/dev/null >> "$OUTPUT_DIR/report.txt"

echo "[*] Report salvato in $OUTPUT_DIR/report.txt"
```

Equivalente PowerShell per VM Windows:

```powershell
# Script da eseguire su ogni VM Windows per raccogliere dipendenze
$hostname = $env:COMPUTERNAME
$outputDir = "C:\DepAnalysis"
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$report = @()
$report += "=== Dependency Analysis: $hostname ==="
$report += "Data: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')"

# Porte in ascolto
$report += "`n=== LISTENING PORTS ==="
$report += (Get-NetTCPConnection -State Listen |
    Select-Object LocalPort, OwningProcess,
    @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} |
    Sort-Object LocalPort | Format-Table -AutoSize | Out-String)

# Connessioni stabilite (escluse loopback)
$report += "`n=== ESTABLISHED CONNECTIONS ==="
$report += (Get-NetTCPConnection -State Established |
    Where-Object { $_.RemoteAddress -notmatch '^127\.' -and $_.RemoteAddress -ne '::1' } |
    Select-Object LocalPort, RemoteAddress, RemotePort, OwningProcess,
    @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} |
    Format-Table -AutoSize | Out-String)

# Configurazione DNS
$report += "`n=== DNS CONFIGURATION ==="
$report += (Get-DnsClientServerAddress | Format-Table -AutoSize | Out-String)

# File hosts
$report += "`n=== HOSTS FILE ==="
$report += (Get-Content "$env:SystemRoot\System32\drivers\etc\hosts" | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '\S' })

# Share di rete montati
$report += "`n=== NETWORK DRIVES ==="
$report += (Get-PSDrive -PSProvider FileSystem | Where-Object { $_.DisplayRoot } | Format-Table -AutoSize | Out-String)

# Servizi in esecuzione
$report += "`n=== RUNNING SERVICES ==="
$report += (Get-Service | Where-Object Status -eq 'Running' |
    Select-Object Name, DisplayName, StartType | Format-Table -AutoSize | Out-String)

# Scheduled Tasks
$report += "`n=== SCHEDULED TASKS ==="
$report += (Get-ScheduledTask | Where-Object State -eq 'Ready' |
    Select-Object TaskName, TaskPath | Format-Table -AutoSize | Out-String)

$report | Out-File "$outputDir\report.txt" -Encoding UTF8
Write-Host "[*] Report salvato in $outputDir\report.txt"
```

### Template di Intervista per Team Applicativi

Per ogni applicazione/servizio, raccogliere le seguenti informazioni:

```
SCHEDA DIPENDENZE APPLICATIVE
═══════════════════════════════

Nome Applicazione: ________________________________
Responsabile:      ________________________________
VM Coinvolte:      ________________________________

1. DIPENDENZE UPSTREAM (da chi dipende questa applicazione?)
   - Database:     ________________________________
   - Identity/SSO: ________________________________
   - File share:   ________________________________
   - API esterne:  ________________________________
   - Altro:        ________________________________

2. DIPENDENZE DOWNSTREAM (chi dipende da questa applicazione?)
   - Applicazioni: ________________________________
   - Utenti:       ________________________________
   - Batch/ETL:    ________________________________

3. FINESTRA DI MANUTENZIONE
   - Orario consentito:     ________________________________
   - Downtime massimo:      ________________________________
   - Periodo blackout:      ________________________________

4. PROCEDURA DI VERIFICA
   - Come si verifica il corretto funzionamento? ____________
   - URL health check:      ________________________________
   - Tempo di avvio:        ________________________________

5. REQUISITI SPECIALI
   - Hardware specifico (GPU, USB, dongle): ________________
   - Licenze legate a MAC/IP/hostname:      ________________
   - Certificati SSL/TLS:                   ________________
   - Configurazioni network specifiche:      ________________
```

---

## Analisi dei Flussi di Rete

### Utilizzo di NSX-T per Flow Analysis

Se l'ambiente VMware utilizza NSX-T (o NSX-V), è possibile sfruttare le funzionalità di flow monitoring integrate:

```
NSX Manager > Plan & Troubleshoot > Discover & Take Action > Discover
```

NSX raccoglie automaticamente i flussi di rete tra VM e li visualizza in una mappa topologica. I dati includono:
- IP sorgente e destinazione
- Porta sorgente e destinazione
- Protocollo (TCP, UDP, ICMP)
- Bytes trasferiti
- Timestamp

### NetFlow/IPFIX Collection

Per ambienti senza NSX, è possibile abilitare NetFlow sui virtual switch distribuiti (VDS):

```
vSphere Client > Networking > VDS > Configure > NetFlow
    Collector IP:     10.0.1.50
    Collector Port:   2055
    Switch IP:        10.0.1.10
    Active Timeout:   60
    Idle Timeout:     15
    Sampling Rate:    0 (nessun campionamento, tutti i flussi)
```

Per analizzare i dati NetFlow raccolti, si può utilizzare `nfdump`:

```bash
# Installazione nfcapd/nfdump
apt-get install nfdump

# Avvio collector
nfcapd -w -D -l /var/cache/nfdump -p 2055

# Analisi: top 20 flussi per volume tra VM
nfdump -R /var/cache/nfdump -o "fmt:%sa %da %sp %dp %pr %byt %fl" -s record/bytes -n 20

# Flussi specifici per una VM (es. 10.0.1.100)
nfdump -R /var/cache/nfdump -o long "'src ip 10.0.1.100 or dst ip 10.0.1.100'"

# Generazione matrice di comunicazione
nfdump -R /var/cache/nfdump -o "fmt:%sa,%da,%dp,%pr,%byt" -A srcip,dstip,dstport > flow_matrix.csv
```

### Costruzione della Mappa di Comunicazione

Dai dati di flusso raccolti, costruire una mappa che evidenzi:

```
┌──────────────────────────────────────────────────────────────────┐
│              MAPPA COMUNICAZIONE — Applicazione ERP              │
│                                                                  │
│  ┌──────────┐    :443     ┌──────────┐    :8080    ┌──────────┐ │
│  │  UTENTI   │───────────>│  web-01   │───────────>│  app-01   │ │
│  │ (esterni) │            │ (NGINX)   │            │ (Tomcat)  │ │
│  └──────────┘            └──────────┘            └─────┬────┘ │
│                                                         │       │
│                                           :1521         │       │
│                                                         v       │
│  ┌──────────┐    :389     ┌──────────┐    :1521    ┌──────────┐ │
│  │  AD/LDAP  │<───────────│  app-01   │───────────>│  db-01    │ │
│  │  (dc-01)  │            │ (Tomcat)  │            │ (Oracle)  │ │
│  └──────────┘            └──────────┘            └─────┬────┘ │
│                                                         │       │
│                                           :22           │       │
│                                                         v       │
│                                                  ┌──────────┐   │
│                                                  │ backup-01 │   │
│                                                  │ (Veeam)   │   │
│                                                  └──────────┘   │
│                                                                  │
│  LEGENDA: ──> Flusso TCP   ···> Flusso UDP   :NNN Porta dest.  │
└──────────────────────────────────────────────────────────────────┘
```

### Identificazione di Dipendenze Nascoste

Alcune dipendenze non sono visibili tramite analisi di rete standard:

| Tipo Dipendenza | Metodo di Rilevazione | Esempio |
|-----------------|----------------------|---------|
| DNS | Analisi query DNS (log DNS server) | App che risolve db.interno.local |
| NTP | Controllo configurazione NTP su ogni VM | Sincronizzazione oraria critica per Kerberos |
| Certificati | Scan certificati SSL/TLS | Certificato scade durante migrazione |
| Licenze | Intervista team applicativo | Licenza legata a MAC address |
| File share | Mount points su guest OS | NFS mount da NAS esterno |
| Backup agent | Verifica agent installati | Veeam, Commvault, NetBackup agent |
| Monitoring agent | Verifica agent installati | Zabbix, Nagios, Datadog agent |
| Hardcoded IP | Grep nei file di configurazione | IP in config invece di hostname |

```bash
# Ricerca IP hardcoded nei file di configurazione (Linux)
grep -rn --include="*.conf" --include="*.cfg" --include="*.ini" --include="*.xml" --include="*.properties" --include="*.yaml" --include="*.yml" --include="*.json" -E '([0-9]{1,3}\.){3}[0-9]{1,3}' /etc/ /opt/ /var/www/ 2>/dev/null | grep -v "127.0.0.1\|0.0.0.0\|255.255"
```

---

## Classificazione di Criticità (Tier 0-3)

### Definizione dei Tier

La classificazione in tier permette di assegnare priorità, definire SLA di migrazione e determinare il livello di rischio accettabile per ogni VM.

| Tier | Definizione | RTO | RPO | Esempi |
|------|-------------|-----|-----|--------|
| **Tier 0** | Infrastruttura core. Il fermo causa cascata su tutti i servizi | < 15 min | 0 (zero data loss) | Domain Controller, DNS, DHCP, vCenter, core switch/FW |
| **Tier 1** | Applicazioni business-critical. Il fermo causa impatto diretto sul fatturato | < 1 ora | < 15 min | ERP, CRM, piattaforma e-commerce, database di produzione |
| **Tier 2** | Applicazioni importanti. Il fermo causa disagi operativi significativi ma non blocco immediato | < 4 ore | < 1 ora | Email server, file server, sistemi di ticketing, intranet |
| **Tier 3** | Applicazioni a basso impatto. Il fermo è tollerabile per periodi prolungati | < 24 ore | < 24 ore | Ambienti di sviluppo, test, staging, tool interni secondari |

### Criteri di Assegnazione

Per assegnare un tier a ciascuna VM, valutare i seguenti criteri:

**Impatto business** (peso 40%):
- Quanti utenti sono impattati dal fermo?
- Qual è l'impatto economico per ora di downtime?
- Ci sono obblighi contrattuali (SLA con clienti)?
- Ci sono implicazioni di compliance o regolamentari?

**Dipendenze** (peso 30%):
- Quanti altri sistemi dipendono da questa VM?
- La VM è un single point of failure?
- Esistono meccanismi di ridondanza o failover?

**Complessità tecnica** (peso 20%):
- La VM ha configurazioni non standard?
- Il sistema operativo è supportato in Proxmox?
- Ci sono driver o hardware specifici?

**Sostituibilità** (peso 10%):
- Quanto tempo serve per ricostruire la VM da zero?
- Esistono procedure documentate di disaster recovery?
- C'è un ambiente DR già funzionante?

### Matrice di Classificazione Automatica

```powershell
# Script per classificazione automatica basata su euristiche
function Get-VMTier {
    param([PSCustomObject]$VMInfo)

    $score = 0

    # Euristica 1: Nome VM suggerisce criticità
    if ($VMInfo.Name -match "dc-|dns-|ad-|dhcp-|vcenter|pdc|bdc") { $score += 40 }
    elseif ($VMInfo.Name -match "db-|sql-|ora-|erp-|crm-|sap-") { $score += 30 }
    elseif ($VMInfo.Name -match "web-|app-|api-|mail-|exchange") { $score += 20 }
    elseif ($VMInfo.Name -match "dev-|test-|stg-|staging-|lab-") { $score += 5 }

    # Euristica 2: Risorse allocate (più risorse = più critica in genere)
    if ($VMInfo.MemoryGB -ge 32) { $score += 15 }
    elseif ($VMInfo.MemoryGB -ge 16) { $score += 10 }
    elseif ($VMInfo.MemoryGB -ge 8) { $score += 5 }

    # Euristica 3: VM accesa
    if ($VMInfo.PowerState -eq "PoweredOn") { $score += 10 }

    # Euristica 4: Ha snapshot (potenziale attenzione particolare)
    if ($VMInfo.SnapshotCount -gt 0) { $score += 5 }

    # Assegnazione tier
    switch ($true) {
        ($score -ge 45) { return "Tier 0" }
        ($score -ge 30) { return "Tier 1" }
        ($score -ge 15) { return "Tier 2" }
        default         { return "Tier 3" }
    }
}
```

**Importante**: la classificazione automatica è un punto di partenza, non il risultato finale. Ogni assegnazione deve essere validata con i team applicativi e il management. Una VM con nome "test-db-01" potrebbe in realtà ospitare dati di produzione; una VM con poche risorse potrebbe essere un servizio DNS critico per l'intero ambiente.

---

## Risk Scoring per Virtual Machine

### Modello di Risk Scoring

Il risk score quantifica il rischio associato alla migrazione di ciascuna VM su una scala da 1 (rischio minimo) a 100 (rischio massimo). Il punteggio è composto da più fattori:

```
Risk Score = (Criticità × 0.30) + (Complessità_Tecnica × 0.25) +
             (Dipendenze × 0.20) + (Dimensione × 0.15) +
             (Fattori_Speciali × 0.10)
```

#### Componente: Criticità (0-100)

| Condizione | Punteggio |
|------------|-----------|
| Tier 0 | 100 |
| Tier 1 | 75 |
| Tier 2 | 40 |
| Tier 3 | 10 |

#### Componente: Complessità Tecnica (0-100)

| Condizione | Punteggio |
|------------|-----------|
| RDM (Raw Device Mapping) | +30 |
| GPU passthrough o vGPU | +25 |
| USB passthrough | +20 |
| OS non supportato da virtio | +20 |
| VMware Tools non installati | +15 |
| Hardware version molto vecchia (< vmx-10) | +15 |
| Più di 4 dischi virtuali | +10 |
| Dischi in modalità Independent | +10 |
| NIC tipo e1000 (non vmxnet3) | +5 |
| Snapshot attivi | +10 |

#### Componente: Dipendenze (0-100)

| Condizione | Punteggio |
|------------|-----------|
| Più di 10 VM dipendenti | 100 |
| 5-10 VM dipendenti | 70 |
| 2-4 VM dipendenti | 40 |
| 1 VM dipendente | 20 |
| Nessuna dipendenza rilevata | 5 |

#### Componente: Dimensione (0-100)

| Condizione | Punteggio |
|------------|-----------|
| Disco totale > 2 TB | 90 |
| Disco totale 500 GB - 2 TB | 60 |
| Disco totale 100 - 500 GB | 30 |
| Disco totale < 100 GB | 10 |

#### Componente: Fattori Speciali (0-100)

| Condizione | Punteggio |
|------------|-----------|
| Licenza legata a hardware/MAC | +30 |
| Applicazione senza supporto vendor per KVM | +25 |
| Nessuna documentazione disponibile | +20 |
| Nessun owner identificato | +15 |
| SLA contrattuale stringente | +10 |

### Esempio di Calcolo

```
VM: db-prod-oracle-01
├── Criticità:         Tier 1 → 75 × 0.30 = 22.5
├── Complessità:       RDM(30) + 6 dischi(10) = 40 × 0.25 = 10.0
├── Dipendenze:        8 VM dipendenti → 70 × 0.20 = 14.0
├── Dimensione:        1.2 TB → 60 × 0.15 = 9.0
└── Fattori Speciali:  Licenza Oracle legata a CPU(30) = 30 × 0.10 = 3.0
                                                          ─────────────
                                               Risk Score = 58.5 / 100
                                               Categoria: RISCHIO ALTO
```

### Categorie di Rischio

| Range Score | Categoria | Strategia di Migrazione |
|-------------|-----------|------------------------|
| 0 - 25 | Basso | Migrazione standard, wave iniziali |
| 26 - 50 | Medio | Migrazione con validazione extra, wave intermedie |
| 51 - 75 | Alto | Migrazione con piano di rollback dettagliato, wave finali |
| 76 - 100 | Critico | Assessment dedicato, possibile ricostruzione invece di migrazione |

---

## Matrici di Dipendenza

### Matrice di Adiacenza

La matrice di dipendenza mostra le relazioni tra VM in formato tabulare. Un "X" indica che la VM in riga dipende dalla VM in colonna:

```
              dc-01  dns-01  db-01  app-01  web-01  mail-01  file-01
  dc-01         -      .       .      .       .       .        .
  dns-01        X      -       .      .       .       .        .
  db-01         X      X       -      .       .       .        .
  app-01        X      X       X      -       .       .        X
  web-01        X      X       .      X       -       .        .
  mail-01       X      X       .      .       .       -        X
  file-01       X      X       .      .       .       .        -

  Legenda: X = dipendenza diretta   . = nessuna dipendenza   - = sé stesso
```

Dalla matrice si ricavano metriche importanti:

- **Fan-out** (dipendenze in uscita): quante VM dipendono da questa VM → colonne con più "X"
- **Fan-in** (dipendenze in ingresso): da quante VM dipende questa VM → righe con più "X"
- **Cluster di dipendenza**: gruppi di VM fortemente interconnesse che devono essere migrate insieme

Nell'esempio sopra, `dc-01` e `dns-01` hanno il fan-out più alto: tutte le VM dipendono da loro. Questo conferma la classificazione Tier 0.

### Generazione Automatica della Matrice

```python
#!/usr/bin/env python3
"""
Genera una matrice di dipendenze da dati di flusso di rete.
Input: CSV con colonne src_ip, dst_ip, dst_port, bytes
Output: matrice di adiacenza e grafo delle dipendenze
"""

import csv
import sys
from collections import defaultdict

def load_flows(csv_path):
    """Carica flussi di rete da CSV."""
    flows = defaultdict(lambda: defaultdict(set))
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = row['src_ip']
            dst = row['dst_ip']
            port = row['dst_port']
            flows[src][dst].add(port)
    return flows

def load_vm_ip_map(csv_path):
    """Carica mappatura VM → IP da CSV."""
    vm_map = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vm_map[row['ip']] = row['vm_name']
    return vm_map

def build_dependency_matrix(flows, vm_map):
    """Costruisce matrice di dipendenze tra VM."""
    vms = sorted(set(vm_map.values()))
    matrix = {vm: {other: set() for other in vms} for vm in vms}

    for src_ip, destinations in flows.items():
        src_vm = vm_map.get(src_ip)
        if not src_vm:
            continue
        for dst_ip, ports in destinations.items():
            dst_vm = vm_map.get(dst_ip)
            if not dst_vm or dst_vm == src_vm:
                continue
            matrix[src_vm][dst_vm].update(ports)

    return vms, matrix

def print_matrix(vms, matrix):
    """Stampa la matrice in formato leggibile."""
    max_name = max(len(vm) for vm in vms)
    header = " " * (max_name + 2) + "  ".join(f"{vm[:8]:>8}" for vm in vms)
    print(header)
    print("-" * len(header))
    for vm in vms:
        row = f"{vm:<{max_name}}  "
        for other in vms:
            if vm == other:
                row += f"{'   -':>8}  "
            elif matrix[vm][other]:
                ports = ",".join(sorted(matrix[vm][other])[:3])
                row += f"{ports:>8}  "
            else:
                row += f"{'   .':>8}  "
        print(row)

if __name__ == "__main__":
    flows = load_flows(sys.argv[1])
    vm_map = load_vm_ip_map(sys.argv[2])
    vms, matrix = build_dependency_matrix(flows, vm_map)
    print_matrix(vms, matrix)
```

---

## Pianificazione delle Wave di Migrazione

### Principi di Composizione delle Wave

Le wave di migrazione devono rispettare vincoli tecnici e operativi:

1. **Integrità delle dipendenze**: VM con dipendenze reciproche forti vanno nella stessa wave
2. **Rischio incrementale**: le prime wave contengono VM a basso rischio, le ultime quelle critiche
3. **Validazione progressiva**: ogni wave serve anche come validazione del processo per le successive
4. **Capacità di rollback**: ogni wave deve poter essere annullata indipendentemente
5. **Finestra temporale**: ogni wave deve completarsi entro la finestra di manutenzione disponibile

### Struttura Tipica delle Wave

```
┌─────────────────────────────────────────────────────────┐
│                   PIANO WAVE DI MIGRAZIONE               │
├──────────┬──────────────────────────────────────────────┤
│ Wave 0   │ PILOTA                                       │
│ (Sett 1) │ • 2-3 VM non critiche (dev/test)             │
│          │ • Scopo: validare processo e tooling          │
│          │ • Risk score: < 20                            │
├──────────┼──────────────────────────────────────────────┤
│ Wave 1   │ AMBIENTI NON PRODUZIONE                      │
│ (Sett 2) │ • VM di sviluppo e staging                   │
│          │ • 10-15 VM per wave                           │
│          │ • Risk score: 20-35                           │
├──────────┼──────────────────────────────────────────────┤
│ Wave 2   │ APPLICAZIONI TIER 3                          │
│ (Sett 3) │ • Tool interni, servizi secondari            │
│          │ • Prima wave con impatto utenti               │
│          │ • Risk score: 25-40                           │
├──────────┼──────────────────────────────────────────────┤
│ Wave 3   │ APPLICAZIONI TIER 2                          │
│ (Sett 4) │ • Email, file server, intranet               │
│          │ • Richiede finestra di manutenzione           │
│          │ • Risk score: 35-55                           │
├──────────┼──────────────────────────────────────────────┤
│ Wave 4   │ APPLICAZIONI TIER 1                          │
│ (Sett 5) │ • ERP, CRM, database produzione              │
│          │ • Finestra di manutenzione estesa             │
│          │ • Piano rollback dettagliato                  │
│          │ • Risk score: 50-75                           │
├──────────┼──────────────────────────────────────────────┤
│ Wave 5   │ INFRASTRUTTURA CORE (TIER 0)                 │
│ (Sett 6) │ • Domain Controller, DNS                     │
│          │ • Migrazione con ricostruzione                │
│          │ • Risk score: 70-100                          │
│          │ • Possibile approccio blue-green              │
├──────────┼──────────────────────────────────────────────┤
│ Wave 6   │ CLEANUP E DECOMMISSIONING                    │
│ (Sett 7) │ • Spegnimento host VMware                    │
│          │ • Rimozione licenze                           │
│          │ • Documentazione finale                       │
└──────────┴──────────────────────────────────────────────┘
```

### Algoritmo di Assegnazione alle Wave

```python
def assign_waves(vms, dependency_matrix, risk_scores, tiers):
    """
    Assegna VM alle wave rispettando dipendenze e ordinamento per rischio.
    Algoritmo: topological sort delle dipendenze + raggruppamento per tier.
    """
    waves = {}
    assigned = set()

    # Wave 0: Pilota (VM Tier 3, risk score più basso, nessuna dipendenza critica)
    pilot_candidates = [
        vm for vm in vms
        if tiers[vm] == 3 and risk_scores[vm] < 20
    ]
    waves[0] = sorted(pilot_candidates, key=lambda v: risk_scores[v])[:3]
    assigned.update(waves[0])

    # Wave successive: per tier decrescente di criticità
    wave_num = 1
    for tier in [3, 2, 1, 0]:
        tier_vms = [
            vm for vm in vms
            if tiers[vm] == tier and vm not in assigned
        ]
        # Ordina per risk score crescente all'interno del tier
        tier_vms.sort(key=lambda v: risk_scores[v])

        # Suddividi in gruppi di max 15 VM per wave
        for i in range(0, len(tier_vms), 15):
            batch = tier_vms[i:i+15]

            # Aggiungi dipendenze non ancora assegnate
            expanded = set(batch)
            for vm in batch:
                for dep_vm, ports in dependency_matrix[vm].items():
                    if ports and dep_vm not in assigned:
                        expanded.add(dep_vm)

            waves[wave_num] = sorted(expanded, key=lambda v: risk_scores[v])
            assigned.update(expanded)
            wave_num += 1

    return waves
```

---

## Best Practices

- **Non fidarsi della sola analisi di rete**. Le dipendenze applicative includono aspetti logici (ordine di avvio, processi batch, sincronizzazioni temporali) che non sono visibili a livello di rete. Combinare sempre analisi tecnica con interviste ai team applicativi.
- **Raccogliere dati di flusso per almeno 30 giorni**. Molte dipendenze si manifestano solo durante operazioni periodiche come chiusure mensili, batch notturni, o processi di fine trimestre.
- **Classificare ogni VM, anche se sembra ovvia**. La mancata classificazione di una singola VM può causare la sua esclusione dal piano di migrazione, con conseguente scoperta tardiva durante le wave.
- **Validare le dipendenze con test reali**. Dopo aver costruito la matrice, verificare le dipendenze critiche spegnendo temporaneamente la VM in ambiente di test e osservando gli effetti.
- **Documentare le dipendenze hardcoded**. IP hardcoded nei file di configurazione sono la causa più frequente di problemi post-migrazione. Catalogarli e pianificare la remediation prima della migrazione.
- **Mantenere la matrice di dipendenze aggiornata**. L'ambiente cambia durante il progetto di migrazione. Aggiornare la matrice dopo ogni wave completata.
- **Coinvolgere il business nella classificazione dei tier**. La criticità è una decisione di business, non tecnica. Un sistema con risorse minime può essere Tier 0 se il suo fermo blocca operazioni critiche.
- **Pianificare le wave con margine**. Ogni wave dovrebbe essere completabile nel 70% della finestra di manutenzione disponibile, lasciando il 30% per troubleshooting e rollback.
- **Definire criteri Go/No-Go per ogni wave**. Prima di procedere con la wave successiva, validare che la wave corrente sia completamente funzionante e stabile.

---

## Troubleshooting

### Problema: Dipendenze circolari tra gruppi di VM
**Sintomi**: Due o più gruppi di VM dipendono reciprocamente, rendendo impossibile stabilire un ordine di migrazione.
**Causa**: Architetture con accoppiamento forte, servizi che si autenticano reciprocamente, o cluster applicativi con dipendenze bidirezionali.
**Soluzione**: Identificare il punto di rottura meno impattante nella catena circolare. Opzioni: (1) migrare l'intero gruppo nella stessa wave; (2) introdurre un componente bridge temporaneo (es. load balancer che punta sia a VMware che a Proxmox durante la transizione); (3) ri-architetturare la dipendenza circolare prima della migrazione.
**Prevenzione**: Identificare le dipendenze circolari nella fase di analisi e pianificare la strategia di risoluzione prima di iniziare le wave.

### Problema: Owner della VM non identificabile
**Sintomi**: Nessun team rivendica la proprietà di una VM, il CMDB non contiene informazioni, le annotations in vCenter sono vuote.
**Causa**: VM create anni fa da personale non più in azienda, VM "temporanee" mai documentate, CMDB non aggiornato.
**Soluzione**: (1) Analizzare i log di accesso alla VM (SSH/RDP) per identificare chi la utilizza; (2) monitorare il traffico di rete per identificare i consumatori del servizio; (3) spegnere la VM in ambiente controllato e attendere segnalazioni; (4) se nessuno protesta dopo un periodo concordato (tipicamente 30 giorni), classificare come candidata alla dismissione.
**Prevenzione**: Stabilire una policy di ownership obbligatoria per tutte le VM. Utilizzare tag o custom attributes in vCenter per tracciare il proprietario.

### Problema: Discrepanza tra dipendenze documentate e reali
**Sintomi**: L'analisi di rete mostra comunicazioni non presenti nella documentazione, o la documentazione elenca dipendenze non confermate dal traffico di rete.
**Causa**: Documentazione obsoleta, configurazioni legacy, servizi abilitati ma non utilizzati, dipendenze latenti (attive solo durante batch periodici).
**Soluzione**: Utilizzare i dati di rete come fonte primaria e la documentazione come fonte secondaria. Per dipendenze documentate ma non confermate dal traffico, verificare se si tratta di comunicazioni periodiche che non sono occorse durante il periodo di osservazione. Estendere il periodo di raccolta dati se necessario.
**Prevenzione**: Raccogliere dati di flusso per almeno un ciclo completo di business (tipicamente un mese, idealmente un trimestre).

### Problema: VM con moltissime dipendenze rende la wave troppo grande
**Sintomi**: Una VM ha connessioni con 30+ altre VM, e il rispetto del vincolo "dipendenze nella stessa wave" crea wave enormi e ingestibili.
**Causa**: La VM è un servizio infrastrutturale (DNS, AD, proxy, monitoring) utilizzato trasversalmente.
**Soluzione**: Distinguere tra dipendenze "hard" (il servizio non funziona senza la VM) e "soft" (il servizio funziona in modo degradato). Solo le dipendenze hard devono essere nella stessa wave. Per servizi infrastrutturali, pianificare un approccio dual-stack: il servizio viene replicato in Proxmox prima della migrazione delle VM dipendenti.
**Prevenzione**: Identificare i servizi infrastrutturali cross-cutting all'inizio e pianificare la loro migrazione (o duplicazione) come prerequisito delle wave applicative.

### Problema: Classificazione tier contestata tra team
**Sintomi**: Il team IT classifica una VM come Tier 2 ma il team business insiste che sia Tier 0. Oppure diversi team business rivendicano priorità diverse per le stesse risorse.
**Causa**: Mancanza di criteri oggettivi condivisi, percezione diversa dell'impatto, mancanza di un processo decisionale chiaro.
**Soluzione**: Utilizzare metriche oggettive come base (impatto economico per ora di downtime, numero utenti impattati, obblighi contrattuali). Definire un comitato di revisione con rappresentanti IT e business che abbia l'autorità finale sulla classificazione. Documentare le decisioni e le motivazioni.
**Prevenzione**: Stabilire criteri oggettivi e condivisi per la classificazione prima di iniziare l'assessment. Ottenere approvazione del management su criteri e processo decisionale.

### Problema: Dati NetFlow/IPFIX incompleti o rumorosi
**Sintomi**: I dati di flusso contengono troppo rumore (broadcast, multicast, ARP) o mancano flussi tra alcune VM.
**Causa**: Configurazione errata del collector, sampling rate troppo alto che perde flussi, flussi intra-host non catturati dal virtual switch, traffico cifrato non analizzabile.
**Soluzione**: (1) Ridurre o eliminare il sampling rate per catturare tutti i flussi; (2) filtrare il rumore in fase di analisi (escludere broadcast 255.255.255.255, multicast 224.0.0.0/4, DHCP, ARP); (3) per flussi intra-host, abilitare il port mirroring sul virtual switch o utilizzare agent-based monitoring; (4) per traffico cifrato, analizzare solo metadati (IP sorgente/destinazione, porta) senza deep packet inspection.
**Prevenzione**: Testare la configurazione NetFlow su un piccolo subset prima di abilitarla sull'intero ambiente. Validare i dati raccolti confrontandoli con connessioni note.

---

## Riferimenti

- VMware Aria Operations Documentation: https://docs.vmware.com/en/VMware-Aria-Operations/index.html
- VMware NSX Documentation — Flow Monitoring: https://docs.vmware.com/en/VMware-NSX/index.html
- NIST SP 800-53 — Risk Assessment Framework: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- nfdump Documentation: https://github.com/phaag/nfdump
- OWASP Risk Rating Methodology: https://owasp.org/www-community/OWASP_Risk_Rating_Methodology
- Proxmox VE Migration Planning: https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE
- ITIL Service Transition — Change Management: https://www.axelos.com/best-practice-solutions/itil

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — eBPF/Tetragon per ADM senza agent.** Per ambienti senza NSX Intelligence o vRNI, una alternativa moderna e l'uso di sonde eBPF (es. Cilium Tetragon, Pixie) deployate sui nodi VMware (richiede ESXi 8 con script di hook) o sulle VM stesse. Producono mappa di flussi per processo (TCP connect, DNS query, DB connection) senza scrivere agent custom. Per il contesto migrazione VMware → Proxmox, e piu pratico farlo dopo aver migrato un primo gruppo: deployare Tetragon sui nodi Proxmox e usarlo come baseline per documentare le dipendenze applicative *post-migrazione* in vista delle wave successive.

> **Errore comune — confondere "probabilita" e "rischio percepito".** Spesso il risk scoring in fase di assessment si basa sull'opinione del team: "la VM X e rischiosa perche ci ha gia dato problemi". Quando si tratta di migrazione, la probabilita di problemi va calcolata con criteri tracciabili e ricalibrati su VM gia migrate: HW version, eta del kernel guest, presenza di driver paravirt VMware (PVSCSI/VMXNET3), dimensione disco, presenza di RDM/passthrough. Il "feeling" non si scarta del tutto, ma si registra a parte come categoria "soft signals" per non inquinare il risk score quantitativo.

> **Caso reale — DNS interno migrato per ultimo.** Un'azienda ha migrato per criticita decrescente: T3 → T2 → T1 → T0. Il DNS interno (T0 per definizione) e stato migrato per ultimo. Conseguenza: durante la migrazione di T1 (cluster app), molte VM nuove su Proxmox cercavano DNS sul vecchio DNS-VM su VMware via nome FQDN, che pero richiedeva DNS lookup ricorsivo... bloccando 4 ore di cutover. Lezione: i servizi infrastrutturali (DNS, AD secondari, NTP) vanno *prima* dei servizi applicativi anche se sono "T0", perche da loro dipende l'operativita di tutto il resto.

---

## Esercizi

1. **Concettuale — risk score di una VM.** Per una VM Linux (HW vmx-15, kernel 4.19, disco 500 GB, snapshot stale 30 gg, RDM physical, dipendenze inverse: 12 VM la usano via NFS), calcolare un risk score con la seguente formula: `score = (1 + snapshot_stale/30) * (1 + RDM_physical*2) * (1 + dipendenze_inverse/10)`. *Risposta:* `score = 2 * 3 * 2.2 ≈ 13.2` → rischio alto. Strategia raccomandata: cold migration con doppio snapshot pre-shutdown, RDM physical convertito a virtio-scsi pass-through, NFS export migrato *prima* delle 12 VM dipendenti.

2. **Lab — costruire un grafo di dipendenze da NetFlow.** Su un router/firewall pfSense o un dispositivo MikroTik, abilitare NetFlow v9 con esportazione verso un nodo Linux. Installare `nfdump` + `nfsen` (o `goflow2` come alternativa moderna). Lasciar girare 7 giorni. Estrarre le top-100 conversazioni IP-IP-port. Dato l'inventario VM con i loro IP, mappare le conversazioni sul grafo. Output: `dependencies.graphml` (formato GraphML per Gephi/yEd) o `dependencies.json` (formato semplice {source, target, port, protocol, freq}).

3. **Scenario — wave plan per 35 VM, 4 tier.** Dato il seguente inventario sintetico: 5 Tier 0 (DC primari AD, DNS, file server cluster), 8 Tier 1 (DB cluster Postgres, ERP), 12 Tier 2 (web app, jobs schedulati, internal CRM), 10 Tier 3 (dev/staging, lab, monitoring), proporre un piano a 5 wave con 1 wave/settimana, motivando l'ordine. *Risposta attesa:* W1 = 8 di Tier 3 (subset stand-alone) come pilota; W2 = restanti Tier 3 + AD secondari (Tier 0); W3 = Tier 2 web; W4 = DB Tier 1 con failover Postgres; W5 = restanti Tier 0/1 (file server cluster, DC primario, ERP) con DR pre-live e finestra notte/weekend.

4. **Stretch — risk-aware automation.** Scrivere uno script che legge `vm-inventory.csv`, applica una funzione di risk scoring custom e produce `migration-plan.csv` con colonne `vmid, name, tier, risk_score, recommended_strategy (cold|warm|live|app), wave_n, wave_date, owner, comm_template_id`. Includere un campo `block_dependencies` che lista (a partire da `dependencies.graphml`) le VM che *devono* essere migrate prima di questa.

## Auto-valutazione

1. Cosa fanno NSX Intelligence e vRealize Network Insight (vRNI) e che differenza c'e?
2. Come si abilita NetFlow su un dvSwitch e dove si esportano i dati?
3. Differenza fra ADM "live traffic-based" e ADM "static configuration-based"?
4. Tier 0 vs Tier 1 in classificazione enterprise — criterio decisivo?
5. Dato un risk score, qual e la strategia di migrazione raccomandata per score basso (< 5), medio (5-15), alto (> 15)?
6. Perche le wave si ordinano per dipendenze e non per pure criticita decrescente?
7. Quale strumento permette di mappare AD trust e dipendenze utente/computer (e non e per la migrazione VM ma per asset crit)?
8. Cosa bisogna sempre includere nel "communication plan" associato a ogni wave?

## Letture primarie consigliate

- VMware Aria Operations for Networks (ex vRNI). https://docs.vmware.com/en/VMware-Aria-Operations-for-Networks/
- VMware NSX Intelligence (NSX-T 4.x). https://docs.vmware.com/en/VMware-NSX/index.html
- nfdump documentation. https://github.com/phaag/nfdump
- goflow2 (modern NetFlow/sFlow/IPFIX collector). https://github.com/netsampler/goflow2
- BloodHound (AD attack-path mapping, applicabile per dipendenze AD). https://bloodhoundenterprise.io/resources/
- [`NIST-800-53`] NIST SP 800-53 — Risk Assessment Framework. https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
- OWASP Risk Rating Methodology. https://owasp.org/www-community/OWASP_Risk_Rating_Methodology

## Collegamenti incrociati

- Modulo 05.1 — `inventario-vmware-assessment.md`: l'input di questo modulo.
- Modulo 05.3 — `dimensionamento-proxmox-capacity-planning.md`: usa la classificazione tier per dimensionare capacity con margini diversi per tier.
- Modulo 05.4 — `timeline-e-risk-assessment.md`: timeline e finestre di downtime per wave.
- Modulo 06.1 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/strategie-metodi-migrazione.md`: usa la classificazione per scegliere cold/warm/live.
- Modulo 09.* — `../09-SCENARI-MIGRAZIONE-SPECIFICI/`: usa il tier per applicare scenari diversi (DB Tier 1, app stateful Tier 1/2, Windows Server Tier 0/1).
- Modulo 16.1, 16.2 — `../16-PROCEDURE-OPERATIVE-E-RUNBOOK/`: il wave plan diventa input dei runbook eseguibili.

## Glossario locale

| Termine | Definizione |
|---|---|
| **ADM (Application Dependency Mapping)** | Tecnica/strumento per scoprire e documentare le dipendenze fra applicazioni e infrastruttura. |
| **Tier** | Categoria di criticita business (T0 indispensabile, T1 business-critical, T2 important, T3 standard). |
| **RTO** | Recovery Time Objective — tempo massimo tollerato prima del ripristino dopo un incidente. |
| **RPO** | Recovery Point Objective — perdita massima di dati tollerata in caso di incidente (in ore/minuti di backup). |
| **NetFlow** | Protocollo Cisco (RFC 3954) per esportare metadati di flussi di rete da router/switch/firewall. |
| **IPFIX** | Standard IETF (RFC 7011) successor di NetFlow v9. |
| **sFlow** | Protocollo di sampling industry-standard (sFlow.org); meno granulare di NetFlow ma piu efficiente. |
| **ADM "live"** | Mappatura basata sul traffico osservato (NetFlow/IPFIX/agent). |
| **ADM "static"** | Mappatura basata su configurazione (`netstat`, file `/etc/`, dichiarazioni). |
| **Risk score** | Valore numerico = probabilita × impatto, usato per ordinare i rischi. |
| **Wave** | Gruppo di VM/servizi migrati assieme in una finestra di tempo. |
| **Pilot wave** | Prima wave, fatta con VM a basso rischio per validare il processo end-to-end. |
| **Communication plan** | Documento che lista chi viene informato, quando, con che template, prima/durante/dopo ogni wave. |
| **Failback plan** | Piano di rollback se la migrazione di una VM fallisce: come riportare il servizio sull'origine VMware. |
