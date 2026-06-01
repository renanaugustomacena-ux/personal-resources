# Monitoraggio e Performance Windows — Guida Completa

> **Modulo 09** · **Aggiornamento:** 2026-05-22

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [Ruoli Server](03-ruoli-server.md) · [PowerShell](02-powershell.md) · [Sicurezza Windows](05-sicurezza-windows.md)
> **Obiettivi di apprendimento:**
> 1. Utilizzare Performance Monitor, Resource Monitor e Task Manager per l'analisi delle risorse
> 2. Configurare Data Collector Set e baseline di performance per il capacity planning
> 3. Implementare Windows Event Forwarding (WEF/WEC) per la centralizzazione degli eventi
> 4. Installare e configurare Sysmon per il monitoraggio avanzato di processi, rete e registro
> 5. Integrare strumenti di monitoraggio esterni (SCOM, Prometheus, Zabbix) con Windows
> **Tempo stimato:** lettura 75 min · lab 50 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida
1. **PerfMon: counter Windows nativi.**
2. **Event Viewer: Application/Security/System log.**
3. **`Get-Counter` PS cmdlet per scripting.**
4. **WAC (Windows Admin Center) modern UI.**
5. **Sysmon: visibilita` profonda su processi, rete, registro.**
6. **WEF/WEC: centralizzazione eventi enterprise.**
7. **Strumenti esterni (SCOM, Prometheus, Zabbix): monitoraggio su scala.**
8. **Baseline → Trending → Capacity Planning: il ciclo virtuoso.**


## Indice

- [Panoramica](#panoramica)
- [Performance Monitor (PerfMon)](#performance-monitor-perfmon)
- [Resource Monitor](#resource-monitor)
- [Contatori di Performance Chiave](#contatori-di-performance-chiave)
- [Task Manager Avanzato](#task-manager-avanzato)
- [Event Viewer](#event-viewer)
- [Windows Event Forwarding (WEF)](#windows-event-forwarding-wef)
- [Windows Admin Center](#windows-admin-center)
- [Monitoraggio con PowerShell](#monitoraggio-con-powershell)
- [WMI e CIM](#wmi-e-cim)
- [Sysmon](#sysmon)
- [SCOM (System Center Operations Manager)](#scom-system-center-operations-manager)
- [Prometheus windows_exporter](#prometheus-windows_exporter)
- [Zabbix Agent per Windows](#zabbix-agent-per-windows)
- [Metodologia Baseline](#metodologia-baseline)
- [Capacity Planning](#capacity-planning)
- [Troubleshooting — 20+ Scenari](#troubleshooting--20-scenari)
- [Best Practices](#best-practices)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Checklist Deployment Monitoraggio](#checklist-deployment-monitoraggio)

---

## Panoramica

Il monitoraggio delle performance in Windows si basa su contatori (Performance Monitor), eventi (Event Viewer), query WMI/CIM e strumenti moderni come Windows Admin Center. L'obiettivo è stabilire una baseline, identificare colli di bottiglia e pianificare la capacità.

### Architettura del Monitoraggio Windows

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LIVELLO PRESENTAZIONE                           │
│  Task Manager │ PerfMon │ Resource Monitor │ WAC │ Grafana │ SCOM Console│
├─────────────────────────────────────────────────────────────────────────┤
│                        LIVELLO RACCOLTA DATI                           │
│  Performance Counters │ ETW (Event Tracing) │ WMI/CIM │ Sysmon        │
│  Event Log Service    │ WinRM               │ WEF/WEC │ SNMP          │
├─────────────────────────────────────────────────────────────────────────┤
│                        LIVELLO ARCHIVIAZIONE                           │
│  .blg / .csv files │ Event Log (.evtx) │ SQL DB (SCOM) │ Prometheus   │
│  Zabbix DB          │ Azure Monitor      │ Elasticsearch │ Splunk      │
├─────────────────────────────────────────────────────────────────────────┤
│                        LIVELLO SORGENTE                                │
│  Kernel │ Driver │ Servizi │ Applicazioni │ .NET CLR │ IIS │ SQL Server│
└─────────────────────────────────────────────────────────────────────────┘
```

### Tassonomia delle Risorse

Ogni problema di performance ricade in una (o piu`) di queste categorie:

| Risorsa   | Sintomo Utente                  | Primo Strumento da Usare     |
|-----------|---------------------------------|------------------------------|
| CPU       | Applicazione bloccata, lentezza | Task Manager → PerfMon       |
| Memoria   | Out-of-memory, swap eccessivo   | Resource Monitor → PerfMon   |
| Disco     | Tempo di risposta alto          | Resource Monitor → iostat    |
| Rete      | Timeout, connessioni lente      | Resource Monitor → pktmon    |
| Handle/Thread | Leak progressivo            | Process Explorer → PerfMon   |

---

## Performance Monitor (PerfMon)

### Avvio e Interfaccia

```
Apertura:
  Win+R → perfmon.msc
  oppure: Win+R → perfmon /res   (apre direttamente Resource Monitor)
  oppure: Win+R → perfmon /sys   (apre System Performance report)

Interfaccia PerfMon:
├── Monitoring Tools
│   ├── Performance Monitor    → Grafico real-time dei contatori
│   └── Reports               → Report generati dai Data Collector Sets
├── Data Collector Sets
│   ├── User Defined           → Collector creati dall'utente
│   ├── System                 → Collector predefiniti (System Diagnostics, System Performance)
│   └── Event Trace Sessions   → Sessioni ETW attive
└── Reports
    ├── User Defined           → Report dai collector dell'utente
    └── System                 → Report di System Diagnostics / System Performance
```

### Contatori Fondamentali

```powershell
# PerfMon raccoglie dati tramite "contatori" organizzati in categorie

# CONTATORI CPU
# \Processor(_Total)\% Processor Time      → Utilizzo CPU totale
# \Processor(_Total)\% Privileged Time      → Tempo kernel (driver, OS)
# \Processor(_Total)\% User Time            → Tempo applicazioni
# \System\Processor Queue Length             → Processi in coda per CPU (> 2*core = collo di bottiglia)
# \System\Context Switches/sec              → Cambi contesto (alto = troppe interruzioni)

# CONTATORI MEMORIA
# \Memory\Available MBytes                  → Memoria disponibile (< 100MB = critico)
# \Memory\Pages/sec                         → Page fault (alto = troppo swap)
# \Memory\% Committed Bytes In Use          → Memoria commit usata
# \Memory\Pool Nonpaged Bytes               → Memoria kernel non paginabile
# \Paging File(_Total)\% Usage              → Utilizzo file di paging

# CONTATORI DISCO
# \PhysicalDisk(_Total)\% Disk Time         → Quanto il disco è occupato
# \PhysicalDisk(_Total)\Avg. Disk Queue Length → Richieste in coda (> 2 = lento)
# \PhysicalDisk(_Total)\Avg. Disk sec/Read  → Latenza lettura (> 20ms = lento su SSD)
# \PhysicalDisk(_Total)\Avg. Disk sec/Write → Latenza scrittura
# \PhysicalDisk(_Total)\Disk Transfers/sec  → IOPS
# \LogicalDisk(C:)\% Free Space             → Spazio libero

# CONTATORI RETE
# \Network Interface(*)\Bytes Total/sec     → Throughput totale
# \Network Interface(*)\Output Queue Length → Pacchetti in coda (> 2 = saturazione)
# \TCPv4\Connections Established            → Connessioni TCP attive
```

### Data Collector Sets

```powershell
# Creare Data Collector Set per raccolta continua
# PerfMon → Data Collector Sets → User Defined → New

# Via PowerShell (logman)
logman create counter "Baseline" -c "\Processor(_Total)\% Processor Time" `
    "\Memory\Available MBytes" "\PhysicalDisk(_Total)\Avg. Disk Queue Length" `
    "\Network Interface(*)\Bytes Total/sec" `
    -si 15 -f csv -o "C:\PerfLogs\Baseline" -rf 24:00:00

# Avviare/fermare
logman start "Baseline"
logman stop "Baseline"

# Schedule automatico
logman update counter "Baseline" -b 01/01/2024 00:00:00 -rf 24:00:00 `
    -r -f csv -o "C:\PerfLogs\Baseline"

# Data Collector Set predefiniti
logman query                       # Lista collector
logman start "System Performance"  # Collector predefinito completo

# Analizzare con PowerShell
Import-Csv "C:\PerfLogs\Baseline_000001.csv" | Where-Object {
    $_.'\\SERVER\Processor(_Total)\% Processor Time' -gt 80
} | Select-Object -First 10
```

### Data Collector Set — Scenari Tipici

```powershell
# ── SCENARIO: Baseline settimanale per server di produzione ──

logman create counter "Weekly-Baseline" `
    -c "\Processor(_Total)\% Processor Time" `
       "\Processor(_Total)\% Privileged Time" `
       "\System\Processor Queue Length" `
       "\Memory\Available MBytes" `
       "\Memory\Pages/sec" `
       "\Memory\Pool Nonpaged Bytes" `
       "\PhysicalDisk(_Total)\Avg. Disk Queue Length" `
       "\PhysicalDisk(_Total)\Avg. Disk sec/Read" `
       "\PhysicalDisk(_Total)\Avg. Disk sec/Write" `
       "\PhysicalDisk(_Total)\Disk Transfers/sec" `
       "\LogicalDisk(C:)\% Free Space" `
       "\Network Interface(*)\Bytes Total/sec" `
       "\Network Interface(*)\Output Queue Length" `
    -si 30 -f csv -o "C:\PerfLogs\Weekly" `
    -rf 168:00:00 -r

# ── SCENARIO: Troubleshooting memory leak (campionamento rapido) ──

logman create counter "MemLeak-Debug" `
    -c "\Process(*)\Working Set" `
       "\Process(*)\Private Bytes" `
       "\Process(*)\Handle Count" `
       "\Process(*)\Thread Count" `
       "\Memory\Committed Bytes" `
       "\Memory\Available MBytes" `
    -si 5 -f csv -o "C:\PerfLogs\MemLeak" `
    -rf 04:00:00

# ── SCENARIO: Diagnostica I/O per SQL Server ──

logman create counter "SQL-IO-Diag" `
    -c "\PhysicalDisk(*)\Avg. Disk sec/Read" `
       "\PhysicalDisk(*)\Avg. Disk sec/Write" `
       "\PhysicalDisk(*)\Disk Reads/sec" `
       "\PhysicalDisk(*)\Disk Writes/sec" `
       "\PhysicalDisk(*)\Current Disk Queue Length" `
       "\SQLServer:Buffer Manager\Page life expectancy" `
       "\SQLServer:Buffer Manager\Buffer cache hit ratio" `
       "\SQLServer:General Statistics\User Connections" `
    -si 10 -f csv -o "C:\PerfLogs\SQL-IO" `
    -rf 08:00:00
```

### Report e Analisi

```powershell
# PerfMon genera report automatici con i System Data Collector Sets

# Generare System Diagnostics Report (include hardware, driver, servizi, errori)
perfmon /report

# Il report si trova in:
# PerfMon → Reports → System → System Diagnostics → [data/ora]
# Include: Resource Overview, Software Config, Hardware Config, Warnings

# System Performance Report:
# PerfMon → Reports → System → System Performance → [data/ora]
# Include: CPU, Disk, Network, Memory summary con raccomandazioni

# ── Analisi automatizzata di CSV con PowerShell ──

function Analyze-PerfLog {
    param([string]$CsvPath)

    $data = Import-Csv $CsvPath
    $cpuCol = ($data[0].PSObject.Properties |
        Where-Object Name -like '*Processor Time*' |
        Select-Object -First 1).Name

    $memCol = ($data[0].PSObject.Properties |
        Where-Object Name -like '*Available MBytes*' |
        Select-Object -First 1).Name

    $cpuValues = $data.$cpuCol | Where-Object { $_ -ne '' } |
        ForEach-Object { [double]$_ }
    $memValues = $data.$memCol | Where-Object { $_ -ne '' } |
        ForEach-Object { [double]$_ }

    [PSCustomObject]@{
        'CPU Avg %'     = [math]::Round(($cpuValues | Measure-Object -Average).Average, 1)
        'CPU Max %'     = [math]::Round(($cpuValues | Measure-Object -Maximum).Maximum, 1)
        'CPU P95 %'     = [math]::Round(($cpuValues | Sort-Object)[[math]::Floor($cpuValues.Count * 0.95)], 1)
        'Mem Avg MB'    = [math]::Round(($memValues | Measure-Object -Average).Average, 0)
        'Mem Min MB'    = [math]::Round(($memValues | Measure-Object -Minimum).Minimum, 0)
        'Campioni'      = $cpuValues.Count
    }
}

Analyze-PerfLog "C:\PerfLogs\Baseline_000001.csv"
```

### Soglie e Alert

```powershell
# Performance Alerts
# PerfMon → Data Collector Sets → User Defined → New → Performance Counter Alert

# Soglie consigliate per alert:
# CPU > 80% per 5+ minuti          → Warning
# CPU > 95% per 2+ minuti          → Critical
# Available Memory < 500 MB        → Warning
# Available Memory < 100 MB        → Critical
# Disk Queue Length > 2             → Warning
# % Disk Time > 80%                → Warning
# % Free Space < 20%               → Warning
# % Free Space < 10%               → Critical
# Network Queue > 2                → Warning

# ── Configurare Alert via logman ──

logman create alert "CPU-High-Alert" `
    -th "\Processor(_Total)\% Processor Time>90" `
    -si 00:01:00 `
    -tn "HighCPU-Task"       # Task Scheduler task da eseguire al trigger

logman create alert "LowDisk-Alert" `
    -th "\LogicalDisk(C:)\% Free Space<10" `
    -si 00:05:00 `
    -tn "LowDisk-Notify"

# ── Azioni possibili sugli alert ──
# 1. Eseguire un Task Scheduler task (script PS, invio email, riavvio servizio)
# 2. Avviare un Data Collector Set (raccogliere dati dettagliati durante il problema)
# 3. Scrivere nel log eventi

# ── Alert con invio email (via Task Scheduler) ──
# Creare task in Task Scheduler:
#   Trigger: "On an event" o invocato da logman
#   Action: eseguire script PowerShell che invia email
#
# Esempio script alert-email.ps1:
# Send-MailMessage -From "monitor@corp.local" -To "admin@corp.local" `
#     -Subject "ALERT: CPU Alta su $env:COMPUTERNAME" `
#     -Body "CPU superiore al 90% rilevato." `
#     -SmtpServer "smtp.corp.local"
```

---

## Resource Monitor

```
Resource Monitor (resmon.exe) fornisce vista real-time con 5 tab:
```

### Tab Overview

```
Overview fornisce un colpo d'occhio su tutte e 4 le risorse:

┌─ CPU ─────────────────────────────────────────────────────────────────┐
│ Per-process CPU usage % con grafico a barre                          │
│ Colonne: Image, PID, Description, Status, Threads, CPU, Average CPU │
│ Checkbox per filtrare: seleziona un processo → gli altri tab         │
│ mostrano solo dati relativi a quel processo                          │
└───────────────────────────────────────────────────────────────────────┘
┌─ Disk ────────────────────────────────────────────────────────────────┐
│ Per-process I/O con Read/Write B/sec                                 │
└───────────────────────────────────────────────────────────────────────┘
┌─ Network ─────────────────────────────────────────────────────────────┐
│ Per-process network con Send/Receive B/sec                           │
└───────────────────────────────────────────────────────────────────────┘
┌─ Memory ──────────────────────────────────────────────────────────────┐
│ Per-process memory: Working Set, Shareable, Private                  │
│ Barra grafica: In Use | Modified | Standby | Free                    │
└───────────────────────────────────────────────────────────────────────┘
```

### Tab CPU — Dettaglio

```
CPU Tab:
- Per-process CPU usage con media temporale
- Servizi associati a ogni processo (espandere con freccia)
- Associated Handles: file, chiavi registry, sezioni, semafori aperti dal processo
- Associated Modules: DLL caricate dal processo

USO DIAGNOSTICO:
- Filtrare per processo (checkbox) → vedere quali servizi, DLL, handle usa
- Cercare handle su un file specifico: barra "Search Handles" in basso
  Esempio: cercare "database.mdf" per trovare chi ha il lock
- Servizi: utile per svchost.exe → mostra quali servizi Windows
  girano dentro quel processo svchost
- Colonna "Average CPU": piu` affidabile di "CPU" istantaneo per
  identificare consumatori persistenti
```

### Tab Memory — Dettaglio

```
Memory Tab:
- Working Set: memoria fisica usata dal processo (totale)
  - Shareable: porzione condivisibile con altri processi (DLL, mapped files)
  - Private: porzione esclusiva del processo (heap, stack)
- Hard Faults/sec: page fault che richiedono accesso a disco
  - Valore alto (> 100/sec sostenuto) = memoria insufficiente, paging eccessivo
- Commit (KB): memoria virtuale riservata dal processo

Physical Memory bar (fondamentale per diagnosi):
┌──────────┬──────────┬──────────┬──────┐
│ In Use   │ Modified │ Standby  │ Free │
└──────────┴──────────┴──────────┴──────┘

- In Use: pagine attivamente referenziate da processi
- Modified: pagine modificate non ancora scritte su disco
- Standby: pagine non attive ma mantenute in cache (riutilizzabili)
- Free: pagine completamente vuote (solitamente molto basso, non preoccupante)

NOTA: "Available" = Standby + Free. Windows usa quasi tutta la RAM
come cache — e` normale. Preoccuparsi solo se "In Use" e` vicino
al totale E hard faults sono alti.
```

### Tab Disk — Dettaglio

```
Disk Tab:
- Per-process I/O:
  - File: path completo del file in lettura/scrittura
  - Read (B/sec), Write (B/sec): throughput per file
  - I/O Priority: Normal, Low, Very Low (processi background usano Low)
  - Response Time (ms): latenza per operazione I/O

- Storage section (pannello inferiore):
  - Per-disk stats: Disk Queue, Read/Write B/sec, Active Time %
  - Utile per distinguere quale disco fisico e` il collo di bottiglia

USO DIAGNOSTICO:
1. Ordinare per "Total (B/sec)" per trovare il processo con piu` I/O
2. Espandere il processo → vedere i file specifici
3. Controllare Response Time: > 20ms su SSD = anomalo
4. Disk Queue Length nel pannello Storage: > 2 = disco sovraccarico
```

### Tab Network — Dettaglio

```
Network Tab:
- Network Activity: per-process con Send/Receive B/sec
- TCP Connections:
  - Local Address, Local Port
  - Remote Address, Remote Port
  - Packet Loss %
  - Latency (ms)
- Listening Ports:
  - Processo, indirizzo, porta, protocollo
  - Firewall Status (Allowed / Not allowed)

USO DIAGNOSTICO:
1. Identificare quale processo consuma banda
2. TCP Connections: vedere a quali server remoti si connette un processo
3. Packet Loss % > 0 = problema di rete (non del server)
4. Listening Ports: verificare quali processi espongono porte
   (utile per audit di sicurezza rapido)
```

---

## Contatori di Performance Chiave

Questa sezione elenca i contatori piu` importanti per categoria, con soglie operative e significato diagnostico.

### CPU

| Contatore | Soglia OK | Warning | Critical | Significato |
|-----------|-----------|---------|----------|-------------|
| `\Processor(_Total)\% Processor Time` | < 70% | 70-85% | > 85% sost. | Utilizzo CPU complessivo |
| `\Processor(_Total)\% Privileged Time` | < 30% | 30-50% | > 50% | Tempo in kernel mode — alto = driver o I/O problematico |
| `\Processor(_Total)\% User Time` | < 70% | 70-85% | > 85% | Tempo in user mode — applicazioni |
| `\System\Processor Queue Length` | < 2x core | 2-4x core | > 4x core | Thread in attesa di CPU |
| `\System\Context Switches/sec` | < 15000 | 15K-30K | > 30K | Cambi di contesto — alto = overhead scheduling |
| `\Processor(*)\% Processor Time` | vedi sopra | | | Per singolo core — identifica sbilanciamento |

```powershell
# Raccolta contatori CPU
Get-Counter '\Processor(_Total)\% Processor Time',
    '\System\Processor Queue Length',
    '\System\Context Switches/sec' -SampleInterval 2 -MaxSamples 5
```

### Memoria

| Contatore | Soglia OK | Warning | Critical | Significato |
|-----------|-----------|---------|----------|-------------|
| `\Memory\Available MBytes` | > 20% RAM | 10-20% | < 10% | RAM libera + standby utilizzabile |
| `\Memory\Pages/sec` | < 20 | 20-50 | > 50 sost. | Page fault al secondo — alto = swapping |
| `\Memory\% Committed Bytes In Use` | < 80% | 80-90% | > 90% | Commit charge vs commit limit |
| `\Memory\Pool Nonpaged Bytes` | < 200 MB | 200-400 MB | > 400 MB | Memoria kernel non paginabile (driver) |
| `\Memory\Pool Paged Bytes` | < 400 MB | 400-700 MB | > 700 MB | Memoria kernel paginabile |
| `\Paging File(_Total)\% Usage` | < 25% | 25-50% | > 50% | Uso del file di paging |
| `\Process(*)\Working Set` | - | - | crescita lineare | Per-processo: memory leak se cresce senza sosta |
| `\Process(*)\Private Bytes` | - | - | crescita lineare | Memoria privata del processo |
| `\Process(*)\Handle Count` | < 5000 | 5K-10K | > 10K | Handle leak se cresce |

```powershell
# Raccolta contatori memoria
Get-Counter '\Memory\Available MBytes',
    '\Memory\Pages/sec',
    '\Memory\% Committed Bytes In Use',
    '\Memory\Pool Nonpaged Bytes' -SampleInterval 5 -MaxSamples 10
```

### Disco

| Contatore | Soglia OK | Warning | Critical | Significato |
|-----------|-----------|---------|----------|-------------|
| `\PhysicalDisk(*)\% Idle Time` | > 50% | 20-50% | < 20% | Quanto tempo il disco e` libero |
| `\PhysicalDisk(*)\Avg. Disk Queue Length` | < 2 | 2-4 | > 4 | Richieste in coda (per spindle) |
| `\PhysicalDisk(*)\Current Disk Queue Length` | < 2 | 2-4 | > 4 | Coda istantanea |
| `\PhysicalDisk(*)\Avg. Disk sec/Read` | < 10ms SSD / < 20ms HDD | 10-20 / 20-50 | > 20 / > 50 | Latenza lettura |
| `\PhysicalDisk(*)\Avg. Disk sec/Write` | < 10ms SSD / < 20ms HDD | 10-20 / 20-50 | > 20 / > 50 | Latenza scrittura |
| `\PhysicalDisk(*)\Disk Transfers/sec` | dipende | - | - | IOPS totali |
| `\PhysicalDisk(*)\Disk Bytes/sec` | dipende | - | - | Throughput |
| `\LogicalDisk(*)\% Free Space` | > 20% | 10-20% | < 10% | Spazio libero |

```powershell
# Raccolta contatori disco
Get-Counter '\PhysicalDisk(_Total)\% Idle Time',
    '\PhysicalDisk(_Total)\Avg. Disk Queue Length',
    '\PhysicalDisk(_Total)\Avg. Disk sec/Read',
    '\PhysicalDisk(_Total)\Avg. Disk sec/Write' -SampleInterval 5 -MaxSamples 10
```

### Rete

| Contatore | Soglia OK | Warning | Critical | Significato |
|-----------|-----------|---------|----------|-------------|
| `\Network Interface(*)\Bytes Total/sec` | < 65% BW | 65-80% BW | > 80% BW | Throughput vs banda disponibile |
| `\Network Interface(*)\Output Queue Length` | 0-1 | 2 | > 2 | Pacchetti in coda per uscita |
| `\Network Interface(*)\Packets Outbound Errors` | 0 | qualsiasi | crescita | Errori invio — NIC o driver problematico |
| `\TCPv4\Connections Established` | < 1000 | 1K-5K | > 5K | Connessioni TCP attive |
| `\TCPv4\Connection Failures` | 0 | qualsiasi | crescita | Fallimenti connessione |
| `\Network Interface(*)\Bytes Received/sec` | - | - | - | Traffico in ingresso |
| `\Network Interface(*)\Bytes Sent/sec` | - | - | - | Traffico in uscita |

```powershell
# Raccolta contatori rete
Get-Counter '\Network Interface(*)\Bytes Total/sec',
    '\Network Interface(*)\Output Queue Length',
    '\TCPv4\Connections Established' -SampleInterval 5 -MaxSamples 10
```

---

## Task Manager Avanzato

### Tab Processes

```
Tab "Processes" (vista predefinita):
- Raggruppa per: Apps, Background processes, Windows processes
- Colonne predefinite: Name, Status, CPU, Memory, Disk, Network, GPU
- Colonne aggiuntive (tasto destro su intestazione):
  - Type (App, Background, Windows process)
  - Publisher
  - PID
  - Process name
  - Command line
  - Power usage / Power usage trend

FUNZIONALITA`:
- Expand (freccia): mostra finestre/tab per ogni processo
- End task: termina processo (SIGTERM poi SIGKILL dopo timeout)
- End process tree: termina processo + tutti i figli
- Tasto destro → "Go to details": salta al tab Details per quel PID
- Tasto destro → "Open file location": apre la cartella dell'eseguibile
- Tasto destro → "Search online": cerca il nome processo
- Tasto destro → "Create dump file": genera crash dump per debug
```

### Tab Performance

```powershell
# Tab Performance mostra grafici real-time:

# CPU:
# - Utilizzo %, velocita` corrente (GHz), processi/thread/handles, uptime
# - Grafico: Overall utilization (default) o Logical processors (tasto destro)
# - "Open Resource Monitor" link in basso

# Memory:
# - In use (GB), Available (GB), Committed, Cached, Paged/Non-paged pool
# - Composizione grafica: In Use | Modified | Standby | Free
# - Slots used (es. 2 of 4) e form factor
# - Speed (MHz), Hardware reserved

# Disk (per ogni disco fisico):
# - Active time %, Response time (ms)
# - Read/Write speed (KB/s o MB/s)
# - Capacity, Type (SSD/HDD), Formatted

# Ethernet / Wi-Fi:
# - Send/Receive (Kbps)
# - Adapter name, Connection type, IPv4/IPv6
# - Link speed (es. 1 Gbps)

# GPU (se presente):
# - 3D, Copy, Video Encode, Video Decode utilizzo %
# - Dedicated/Shared GPU memory
# - Driver version
```

### Tab App History

```
Tab "App History" (Windows 10/11 client):
- Mostra consumo risorse CUMULATIVO per app UWP/Store
- Colonne: CPU time, Network, Metered network, Tile updates
- Utile per identificare app che consumano risorse in background
- "Delete usage history" per resettare i contatori
- Nota: mostra solo app UWP, non app Win32 tradizionali
```

### Tab Startup

```
Tab "Startup" (solo client):
- Programmi che si avviano con l'utente
- Colonne: Name, Publisher, Status (Enabled/Disabled), Startup impact
  - Startup impact: High, Medium, Low, Not measured
  - Calcolato su CPU + I/O durante il boot
- "Last BIOS time": tempo impiegato dal BIOS/UEFI prima del boot OS
- Tasto destro → Disable/Enable
- Tasto destro → "Open file location"
- Tasto destro → "Search online"

# Equivalente PowerShell
Get-CimInstance Win32_StartupCommand |
    Select-Object Name, Command, Location, User
```

### Tab Services

```
Tab "Services":
- Lista tutti i servizi Windows con stato (Running/Stopped)
- Tasto destro → Start, Stop, Restart
- "Open Services": apre services.msc
- PID mostrato per servizi in esecuzione

# Nota: Task Manager mostra meno dettagli di services.msc
# Per gestione completa usare services.msc o PowerShell
```

### Tab Details — Colonne Avanzate

```powershell
# Tab "Details" e` il piu` potente per analisi processo:

# Colonne predefinite: Name, PID, Status, User name, CPU, Memory
# Colonne aggiuntive importanti (tasto destro → Select columns):
#
#   CPU Time          → Tempo CPU cumulativo (identifica consumatori storici)
#   I/O Read Bytes    → Totale byte letti da I/O
#   I/O Write Bytes   → Totale byte scritti
#   I/O Read/Write Ops → Numero operazioni I/O
#   Threads           → Numero thread attivi
#   Handles           → Numero handle aperti (file, registry, ecc.)
#   GDI Objects       → Oggetti grafici (alto = leak GUI)
#   USER Objects      → Oggetti finestra
#   Peak Working Set  → Picco memoria usata
#   Working Set Delta → Variazione memoria dall'ultimo refresh
#   Command Line      → Riga di comando completa
#   Image Path Name   → Path completo dell'eseguibile
#   Platform          → 32-bit o 64-bit
#   Elevated          → Se gira con privilegi elevati (Yes/No)
#   UAC Virtualization → Se attiva la virtualizzazione UAC

# Funzionalita`:
# - Tasto destro → Set Affinity: binding a core specifici
# - Tasto destro → Set Priority: Realtime/High/AboveNormal/Normal/BelowNormal/Low
# - Tasto destro → Analyze wait chain: mostra catena di attesa (deadlock detection)
# - Tasto destro → Create dump file: crash dump per WinDbg
# - Tasto destro → Open file location

# Equivalente PowerShell per info processo
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU,
    @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,2)}}, Id, Handles, Threads

# Processo con command line
Get-CimInstance Win32_Process | Where-Object Name -eq "sqlservr.exe" |
    Select-Object ProcessId, CommandLine
```

### Tab Users

```
Tab "Users":
- Consumo risorse per sessione utente (CPU, Memory, Disk, Network)
- Espandere utente → vedere processi di quella sessione
- Tasto destro → Disconnect: disconnette sessione (RDP)
- Tasto destro → Sign off: termina sessione (logout)
- Utile per: Terminal Server / RDS con molti utenti
```

---

## Event Viewer

### Struttura Log

```
Event Viewer (eventvwr.msc)
├── Windows Logs
│   ├── Application    → Errori/warning applicazioni
│   ├── Security       → Login, audit, policy (CRITICO)
│   ├── System         → Driver, servizi, kernel
│   ├── Setup          → Installazione Windows/ruoli
│   └── Forwarded Events → Eventi raccolti da altri server
├── Applications and Services Logs
│   ├── Microsoft → Windows → specifici per ruolo
│   │   ├── DNS-Server
│   │   ├── DHCP-Server
│   │   ├── Hyper-V-VMMS
│   │   ├── TaskScheduler
│   │   ├── Sysmon/Operational      ← dopo installazione Sysmon
│   │   ├── PowerShell/Operational
│   │   ├── PrintService
│   │   └── ...
│   └── Active Directory Web Services
└── Subscriptions → Regole per raccogliere eventi da altri server
```

### Log Application — Event ID Importanti

```
Event ID   Sorgente               Significato
────────── ────────────────────── ─────────────────────────────────────────
1000       Application Error      Crash applicazione (exception non gestita)
1001       Windows Error Report   Dettagli crash (bucket, fault module)
1002       Application Hang       Applicazione non risponde (hung)
1026       .NET Runtime           Eccezione .NET non gestita
1033-1035  MsiInstaller           Installazione/aggiornamento/rimozione software
11707      MsiInstaller           Installazione completata con successo
11708      MsiInstaller           Installazione fallita
```

### Log System — Event ID Importanti

```
Event ID   Sorgente               Significato
────────── ────────────────────── ─────────────────────────────────────────
1074       User32                 Riavvio/spegnimento intenzionale (chi/quando)
6005       EventLog               Servizio Event Log avviato (= boot)
6006       EventLog               Servizio Event Log fermato (= shutdown pulito)
6008       EventLog               Spegnimento imprevisto (crash/power loss)
6013       EventLog               Uptime in secondi
7001       Service Control Mgr    Servizio dipendente non avviato
7034       Service Control Mgr    Servizio terminato in modo imprevisto
7036       Service Control Mgr    Servizio avviato/fermato
7040       Service Control Mgr    Tipo avvio servizio modificato
41         Kernel-Power           Riavvio imprevisto (kernel power failure)
55         Ntfs                   Corruzione file system
153        Disk                   Errore I/O disco (retry/fail)
129        storahci               Timeout I/O controller AHCI
219        Kernel-PnP             Driver non caricato (firma mancante)
```

### Log Security — Event ID Importanti

```
Event ID   Categoria              Significato
────────── ────────────────────── ─────────────────────────────────────────
4624       Logon                  Login riuscito
4625       Logon                  Login fallito (brute force detection!)
4634       Logoff                 Logoff
4648       Logon                  Login con credenziali esplicite (RunAs)
4720       Account Management     Account utente creato
4722       Account Management     Account abilitato
4725       Account Management     Account disabilitato
4726       Account Management     Account eliminato
4732       Account Management     Membro aggiunto a gruppo locale
4740       Account Management     Account lockout
4756       Account Management     Membro aggiunto a gruppo universale
4767       Account Management     Account unlocked
4771       Kerberos               Kerberos pre-auth fallita
4776       NTLM                   Validazione credenziali (NTLM)
4688       Process Tracking       Nuovo processo creato (se audit abilitato)
4689       Process Tracking       Processo terminato
1102       EventLog               Security log cancellato (ALERT!)
```

### Custom Views

```powershell
# ── Creare Custom Views nell'Event Viewer ──
# Event Viewer → Custom Views → Create Custom View
# Selezionare: Event level, log, source, event ID, keywords

# ── Custom Views utili da creare ──

# 1. "Crash e Hang" (Application):
#    - Log: Application
#    - Event IDs: 1000, 1001, 1002, 1026
#    - Livello: Error, Critical

# 2. "Riavvii e Shutdown" (System):
#    - Log: System
#    - Event IDs: 41, 1074, 6005, 6006, 6008
#    - Livello: tutti

# 3. "Servizi Falliti" (System):
#    - Log: System
#    - Event IDs: 7034, 7031
#    - Livello: Error, Critical

# 4. "Login Falliti" (Security):
#    - Log: Security
#    - Event IDs: 4625, 4771
#    - Livello: tutti

# 5. "Modifiche Account" (Security):
#    - Log: Security
#    - Event IDs: 4720, 4722, 4725, 4726, 4732, 4740, 4756

# ── Esportare Custom View come XML ──
# Tasto destro su Custom View → "Export Custom View..."
# Il file XML puo` essere importato su altri server
```

### Query PowerShell

```powershell
# Ultimi errori sistema
Get-WinEvent -LogName System -MaxEvents 50 |
    Where-Object LevelDisplayName -eq "Error" |
    Select-Object TimeCreated, Id, ProviderName, Message

# Filtri avanzati (più veloci di Where-Object)
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    Level = 2           # 1=Critical, 2=Error, 3=Warning, 4=Information
    StartTime = (Get-Date).AddDays(-1)
}

# Riavvii imprevisti
Get-WinEvent -FilterHashtable @{LogName='System'; Id=6008} -MaxEvents 10 |
    Select-Object TimeCreated, Message

# Servizi che si fermano
Get-WinEvent -FilterHashtable @{LogName='System'; Id=7034,7036} -MaxEvents 20 |
    Select-Object TimeCreated, Id, Message

# Errori applicazione
Get-WinEvent -FilterHashtable @{LogName='Application'; Level=2} -MaxEvents 20

# Login falliti nelle ultime 24 ore
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4625
    StartTime = (Get-Date).AddDays(-1)
} | ForEach-Object {
    [PSCustomObject]@{
        Time    = $_.TimeCreated
        Account = $_.Properties[5].Value   # TargetUserName
        Source  = $_.Properties[19].Value   # IpAddress
        Reason  = $_.Properties[8].Value    # FailureReason
    }
}

# Query XPath (piu` performante per grandi log)
Get-WinEvent -FilterXml @"
<QueryList>
  <Query Id="0" Path="Security">
    <Select Path="Security">
      *[System[(EventID=4625) and TimeCreated[timediff(@SystemTime) &lt;= 86400000]]]
    </Select>
  </Query>
</QueryList>
"@

# Esportare log
wevtutil epl System C:\Logs\system-backup.evtx

# Configurare dimensione
wevtutil sl System /ms:1073741824           # 1 GB
wevtutil sl Security /ms:4294967296         # 4 GB (per server con molti eventi)
```

---

## Windows Event Forwarding (WEF)

Windows Event Forwarding (WEF) e` il meccanismo nativo per centralizzare eventi da piu` server su un collector. Utilizza WinRM (porta 5985/5986) e non richiede agent aggiuntivi.

### Architettura WEF/WEC

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Source SRV1 │    │  Source SRV2 │    │  Source SRV3 │
│  (WinRM)     │    │  (WinRM)     │    │  (WinRM)     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │    WinRM (HTTP 5985 o HTTPS 5986)     │
       │                   │                   │
       ▼                   ▼                   ▼
    ┌──────────────────────────────────────────────┐
    │        WEC (Windows Event Collector)          │
    │        Forwarded Events log                   │
    │        → puo` essere inoltrato a SIEM         │
    └──────────────────────────────────────────────┘
```

### Configurazione Collector (WEC)

```powershell
# ── Sul server COLLECTOR (che riceve gli eventi) ──

# 1. Abilitare il servizio Windows Event Collector
wecutil qc
# Risponde: "WinRM service is already running."
# Configura il servizio "Windows Event Collector" per auto-start

# 2. Verificare che WinRM sia attivo
winrm quickconfig

# 3. Creare una subscription (via GUI o XML)

# Metodo GUI:
# Event Viewer → Subscriptions → Create Subscription
# - Subscription name: "Security-Events-All-Servers"
# - Destination log: Forwarded Events
# - Subscription type: "Source computer initiated" (push, scalabile)
#   oppure "Collector initiated" (pull, per pochi server)
# - Source Computers: aggiungere computer o gruppi
# - Select Events: definire filtro (Event IDs, livelli, log)

# Metodo XML (subscription file):
```

### Subscription XML — Esempio

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Subscription xmlns="http://schemas.microsoft.com/2006/03/windows/events/subscription">
    <SubscriptionId>Security-Critical-Events</SubscriptionId>
    <SubscriptionType>SourceInitiated</SubscriptionType>
    <Description>Raccolta eventi sicurezza critici da tutti i server</Description>
    <Enabled>true</Enabled>
    <Uri>http://schemas.microsoft.com/wbem/wsman/1/windows/EventLog</Uri>

    <ConfigurationMode>Custom</ConfigurationMode>
    <Delivery Mode="Push">
        <Batching>
            <MaxLatencyTime>900000</MaxLatencyTime>  <!-- 15 minuti -->
        </Batching>
    </Delivery>

    <Query>
        <![CDATA[
        <QueryList>
          <Query Id="0">
            <Select Path="Security">
              *[System[(EventID=4624 or EventID=4625 or EventID=4720
                or EventID=4726 or EventID=4732 or EventID=4740 or EventID=1102)]]
            </Select>
            <Select Path="System">
              *[System[(EventID=7034 or EventID=7036 or EventID=41 or EventID=6008)]]
            </Select>
          </Query>
        </QueryList>
        ]]>
    </Query>

    <ReadExistingEvents>false</ReadExistingEvents>
    <TransportName>HTTP</TransportName>
    <AllowedSourceNonDomainComputers></AllowedSourceNonDomainComputers>
    <AllowedSourceDomainComputers>
        O:NSG:BAD:P(A;;GA;;;DC)S:   <!-- Domain Computers -->
    </AllowedSourceDomainComputers>
</Subscription>
```

```powershell
# Importare la subscription
wecutil cs C:\WEF\Security-Critical-Events.xml

# Verificare stato
wecutil gs "Security-Critical-Events"
wecutil gr "Security-Critical-Events"     # Runtime status per source

# Lista tutte le subscription
wecutil es

# Retry subscription su un source specifico
wecutil rs "Security-Critical-Events" /uri:http://source-server:5985
```

### Configurazione Source (via GPO)

```
# ── Sui server SOURCE (che inviano eventi) ──

# Opzione 1: GPO (consigliata per molti server)
# Computer Configuration → Administrative Templates →
#   Windows Components → Event Forwarding →
#   "Configure target Subscription Manager"
#
# Abilitare e aggiungere:
# Server=http://wec-server.corp.contoso.com:5985/wsman/SubscriptionManager/WEC
#
# Per HTTPS:
# Server=https://wec-server.corp.contoso.com:5986/wsman/SubscriptionManager/WEC,
#   Refresh=60,IssuerCA=THUMBPRINT

# Opzione 2: Manuale (per test)
winrm quickconfig
```

### Configurazione Dimensione Log e Retention

```powershell
# Il log "Forwarded Events" ha dimensione default piccola (20 MB)
# Per un collector che riceve da molti server, aumentare:

wevtutil sl ForwardedEvents /ms:4294967296    # 4 GB
wevtutil sl ForwardedEvents /rt:true          # Retention: true = non sovrascrivere

# Automatizzare archiviazione (Task Scheduler + script):
# Quando il log raggiunge X%, esportare e pulire
$logSize = (Get-WinEvent -ListLog ForwardedEvents).FileSize
$maxSize = (Get-WinEvent -ListLog ForwardedEvents).MaximumSizeInBytes
if ($logSize / $maxSize -gt 0.8) {
    $ts = Get-Date -Format "yyyyMMdd-HHmmss"
    wevtutil epl ForwardedEvents "C:\EventArchive\ForwardedEvents-$ts.evtx"
    wevtutil cl ForwardedEvents
}
```

---

## Windows Admin Center

```powershell
# WAC è la console web moderna per gestire Windows Server
# Sostituisce progressivamente: Server Manager, MMC snap-in, RSAT tools

# Installazione (su server di gestione, non sul DC)
# Scaricare WAC da Microsoft, installare con:
# msiexec /i WindowsAdminCenter.msi /qn /L*v log.txt SME_PORT=443 SSL_CERTIFICATE_OPTION=generate

# Funzionalità principali:
# ├── Overview          → Dashboard sistema (CPU, RAM, Disk, Network)
# ├── Files & Shares    → Gestione file e condivisioni
# ├── Firewall          → Gestione regole firewall
# ├── Events            → Event Viewer nel browser
# ├── Certificates      → Gestione certificati
# ├── PowerShell        → Console PowerShell nel browser
# ├── Registry          → Editor Registry nel browser
# ├── Roles & Features  → Installazione/rimozione ruoli
# ├── Storage           → Dischi, volumi, Storage Spaces
# ├── Updates           → Windows Update
# ├── Virtual Machines  → Gestione Hyper-V
# ├── Virtual Switches  → Switch virtuali Hyper-V
# └── Extensions        → Plugin aggiuntivi

# WAC gestisce: Windows Server 2012 R2+, Windows 10/11, Azure Stack HCI, Failover Cluster
# Accesso: https://wac-server.corp.contoso.com:443
```

### Capacita` di Monitoraggio in WAC

```
WAC fornisce monitoraggio in tempo reale per ogni server connesso:

Overview Dashboard:
├── CPU: grafico tempo reale, % utilizzo, core
├── Memory: usata/totale, trend temporale
├── Disk: I/O Read/Write, capacita` per volume
├── Network: Send/Receive per interfaccia
└── Alerts: eventi critici recenti

Performance Monitor (integrato):
- Contatori PerfMon selezionabili direttamente nel browser
- Grafici interattivi con zoom e selezione temporale
- Salvataggio configurazione contatori

Events (Event Viewer integrato):
- Ricerca full-text su eventi
- Filtri per livello, sorgente, ID
- Esportazione eventi
```

### Estensioni WAC

```
Estensioni disponibili (Extensions → Feed):

Estensioni Microsoft:
├── Active Directory        → Gestione AD (utenti, gruppi, OU)
├── Azure Backup            → Configurazione backup verso Azure
├── Azure File Sync         → Sincronizzazione file con Azure
├── Azure Site Recovery     → DR verso Azure
├── DNS                     → Gestione zone DNS
├── DHCP                    → Gestione scope DHCP
├── GPU Management          → Per server con GPU (ML/VDI)
└── Security                → Configurazione sicurezza

Estensioni Community / Third-party:
├── Dell OpenManage         → Hardware Dell
├── Lenovo XClarity         → Hardware Lenovo
├── HPE OneView             → Hardware HPE
└── DataON MUST             → Storage iperconvergente

Installazione estensione:
  WAC → Settings → Extensions → Available Extensions → Install
```

### Gestione Multi-Server e Cluster

```
# WAC supporta connessioni a molti server contemporaneamente

# Aggiungere server:
# WAC → All Connections → Add → Server → inserire FQDN o IP

# Importare da file CSV:
# WAC → All Connections → Add → Import servers
# CSV con colonna "ServerName"

# Gestione Failover Cluster:
# WAC → Add → Failover Cluster → inserire cluster name
# Dashboard cluster: nodi, VM, volumi, reti

# Azure Hybrid:
# WAC puo` registrarsi con Azure per:
# - Azure Monitor: inviare log e metriche a Log Analytics
# - Azure Update Management: gestire aggiornamenti
# - Azure Security Center: raccomandazioni sicurezza
# - Azure Backup: backup server fisici/VM
```

---

## Monitoraggio con PowerShell

### Get-Counter — Raccolta Contatori

```powershell
# ── Get-Counter: lettura contatori performance ──

# Lettura singola
Get-Counter '\Processor(_Total)\% Processor Time'

# Campionamento continuo (5 campioni ogni 2 secondi)
Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 5

# Contatori multipli
Get-Counter '\Processor(_Total)\% Processor Time',
    '\Memory\Available MBytes',
    '\PhysicalDisk(_Total)\% Idle Time',
    '\Network Interface(*)\Bytes Total/sec' -SampleInterval 5 -MaxSamples 10

# Campionamento continuo (senza limite)
Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -Continuous |
    ForEach-Object {
        $val = $_.CounterSamples[0].CookedValue
        if ($val -gt 80) {
            "$((Get-Date).ToString('HH:mm:ss')) ALERT: CPU $([math]::Round($val,1))%"
        }
    }

# Elencare tutti i contatori disponibili per una categoria
(Get-Counter -ListSet 'Processor').Counter
(Get-Counter -ListSet 'Memory').Counter
(Get-Counter -ListSet 'PhysicalDisk').Counter
(Get-Counter -ListSet 'Network Interface').Counter

# Cercare categorie di contatori
Get-Counter -ListSet * | Where-Object CounterSetName -like '*SQL*'

# Salvare su CSV
Get-Counter '\Processor(_Total)\% Processor Time',
    '\Memory\Available MBytes' -SampleInterval 10 -MaxSamples 360 |
    Export-Counter -Path "C:\PerfLogs\PS-Baseline.csv" -FileFormat CSV

# Salvare su BLG (formato nativo PerfMon, rianalizzabile in perfmon.msc)
Get-Counter '\Processor(_Total)\% Processor Time',
    '\Memory\Available MBytes' -SampleInterval 10 -MaxSamples 360 |
    Export-Counter -Path "C:\PerfLogs\PS-Baseline.blg" -FileFormat BLG

# Server remoti
Get-Counter '\Processor(_Total)\% Processor Time' -ComputerName SRV01, SRV02 `
    -SampleInterval 5 -MaxSamples 3
```

### Get-Process — Analisi Processi

```powershell
# ── Get-Process: dettaglio processi in esecuzione ──

# Top 10 per CPU cumulativa
Get-Process | Sort-Object CPU -Descending |
    Select-Object -First 10 Name, Id, CPU,
        @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,2)}},
        @{N='PrivMB';E={[math]::Round($_.PrivateMemorySize64/1MB,2)}},
        Handles, @{N='Threads';E={$_.Threads.Count}}

# Top 10 per memoria
Get-Process | Sort-Object WorkingSet64 -Descending |
    Select-Object -First 10 Name, Id,
        @{N='WS_MB';E={[math]::Round($_.WorkingSet64/1MB,1)}},
        @{N='Priv_MB';E={[math]::Round($_.PrivateMemorySize64/1MB,1)}},
        @{N='VM_MB';E={[math]::Round($_.VirtualMemorySize64/1MB,1)}}

# Processi con piu` handle (potenziale handle leak)
Get-Process | Where-Object Handles -gt 3000 |
    Sort-Object Handles -Descending |
    Select-Object Name, Id, Handles, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}

# Monitorare crescita memoria di un processo nel tempo (memory leak detection)
$processName = "w3wp"
1..60 | ForEach-Object {
    $p = Get-Process -Name $processName -ErrorAction SilentlyContinue
    if ($p) {
        [PSCustomObject]@{
            Time     = Get-Date -Format 'HH:mm:ss'
            PID      = $p.Id
            WS_MB    = [math]::Round($p.WorkingSet64/1MB, 1)
            Priv_MB  = [math]::Round($p.PrivateMemorySize64/1MB, 1)
            Handles  = $p.HandleCount
            Threads  = $p.Threads.Count
        }
    }
    Start-Sleep -Seconds 60
} | Export-Csv "C:\PerfLogs\$processName-memory-trend.csv" -NoTypeInformation

# Processi con moduli caricati (DLL)
(Get-Process -Name "explorer").Modules | Select-Object FileName, Size

# Terminare un processo
Stop-Process -Id 1234 -Force
Stop-Process -Name "notepad" -Force
```

### Get-WinEvent — Query Avanzate

```powershell
# ── Get-WinEvent: query log eventi ──

# Velocita`: FilterHashtable > FilterXml > Where-Object
# Usare SEMPRE FilterHashtable o FilterXml per log grandi

# Errori system nelle ultime 24h
Get-WinEvent -FilterHashtable @{
    LogName   = 'System'
    Level     = 1,2          # 1=Critical, 2=Error
    StartTime = (Get-Date).AddDays(-1)
} -MaxEvents 50

# Errori da un provider specifico
Get-WinEvent -FilterHashtable @{
    LogName      = 'System'
    ProviderName = 'Microsoft-Windows-Kernel-Power'
    StartTime    = (Get-Date).AddDays(-7)
}

# Contare eventi per Event ID (distribuzione)
Get-WinEvent -LogName Security -MaxEvents 10000 |
    Group-Object Id |
    Sort-Object Count -Descending |
    Select-Object -First 20 Count, Name

# Report login falliti per IP sorgente (threat hunting)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 1000 |
    ForEach-Object {
        [PSCustomObject]@{
            Time    = $_.TimeCreated
            Account = $_.Properties[5].Value
            Domain  = $_.Properties[6].Value
            IP      = $_.Properties[19].Value
            LogonType = $_.Properties[10].Value
        }
    } | Group-Object IP |
    Sort-Object Count -Descending |
    Select-Object Count, Name

# Cercare testo nel messaggio (lento, usare solo quando necessario)
Get-WinEvent -LogName Application -MaxEvents 5000 |
    Where-Object Message -like "*OutOfMemoryException*"

# Query su server remoto
Get-WinEvent -ComputerName SRV01 -FilterHashtable @{
    LogName = 'System'; Level = 1,2; StartTime = (Get-Date).AddHours(-6)
}

# Informazioni su un log
Get-WinEvent -ListLog * | Where-Object RecordCount -gt 0 |
    Sort-Object RecordCount -Descending |
    Select-Object LogName, RecordCount,
        @{N='SizeMB';E={[math]::Round($_.FileSize/1MB,1)}},
        @{N='MaxMB';E={[math]::Round($_.MaximumSizeInBytes/1MB,1)}}
```

### Script di Health Check Completo

```powershell
# ── Health Check Rapido (eseguire su ogni server) ──

function Get-ServerHealth {
    param([string]$ComputerName = $env:COMPUTERNAME)

    $os   = Get-CimInstance Win32_OperatingSystem -ComputerName $ComputerName
    $cpu  = Get-CimInstance Win32_Processor -ComputerName $ComputerName
    $disk = Get-CimInstance Win32_LogicalDisk -ComputerName $ComputerName -Filter "DriveType=3"

    $uptime    = (Get-Date) - $os.LastBootUpTime
    $memUsedPc = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) /
                               $os.TotalVisibleMemorySize * 100, 1)
    $memFreeMB = [math]::Round($os.FreePhysicalMemory / 1KB, 0)

    $critErrors = (Get-WinEvent -ComputerName $ComputerName -FilterHashtable @{
        LogName='System'; Level=1,2; StartTime=(Get-Date).AddDays(-1)
    } -ErrorAction SilentlyContinue | Measure-Object).Count

    [PSCustomObject]@{
        Computer     = $ComputerName
        OS           = $os.Caption
        Uptime       = "{0}d {1}h" -f $uptime.Days, $uptime.Hours
        'CPU %'      = $cpu.LoadPercentage
        'Mem Used %' = $memUsedPc
        'Mem Free MB'= $memFreeMB
        Disks        = ($disk | ForEach-Object {
            "{0} {1}% free" -f $_.DeviceID,
                [math]::Round($_.FreeSpace/$_.Size*100,1)
        }) -join '; '
        'Errors 24h' = $critErrors
    }
}

# Uso singolo
Get-ServerHealth

# Uso multi-server
'SRV01','SRV02','SRV03' | ForEach-Object { Get-ServerHealth $_ } | Format-Table -AutoSize
```

---

## WMI e CIM

### CIM vs WMI — Differenze

```
CIM (Common Information Model) — usare QUESTO:
- Cmdlet: Get-CimInstance, Invoke-CimMethod, New-CimSession
- Trasporto: WinRM (WS-Man) di default
- Sessioni: CimSession (riutilizzabili, efficienti)
- Firewall: porta 5985/5986 (WinRM)
- Supporto: attivamente sviluppato, cross-platform (PowerShell 7+)

WMI (Windows Management Instrumentation) — LEGACY:
- Cmdlet: Get-WmiObject (rimosso in PowerShell 7+)
- Trasporto: DCOM (RPC)
- Firewall: range porte dinamiche (135 + porte alte)
- Supporto: deprecato, solo Windows PowerShell 5.1

REGOLA: usare sempre Get-CimInstance al posto di Get-WmiObject
```

### Classi WMI/CIM Fondamentali

```powershell
# CIM (Common Information Model) è il successore moderno di WMI
# Preferire Get-CimInstance a Get-WmiObject

# Informazioni sistema
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version,
    LastBootUpTime, FreePhysicalMemory, TotalVisibleMemorySize

# CPU
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores,
    NumberOfLogicalProcessors, MaxClockSpeed, LoadPercentage

# Memoria
Get-CimInstance Win32_PhysicalMemory | Select-Object BankLabel, Capacity, Speed, Manufacturer

# Disco
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
    Select-Object DeviceID, Size, FreeSpace,
        @{N='FreePercent';E={[math]::Round($_.FreeSpace/$_.Size*100,1)}}

# Servizi
Get-CimInstance Win32_Service | Where-Object State -eq 'Running' |
    Select-Object Name, DisplayName, StartMode, ProcessId

# Software installato
Get-CimInstance Win32_Product | Select-Object Name, Version, Vendor | Sort-Object Name

# Uptime
(Get-CimInstance Win32_OperatingSystem).LastBootUpTime
(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime

# Query remota
Get-CimInstance Win32_OperatingSystem -ComputerName SRV01, SRV02 |
    Select-Object PSComputerName, Caption, LastBootUpTime
```

### Classi CIM Avanzate

```powershell
# ── Hardware ──

# BIOS
Get-CimInstance Win32_BIOS | Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate

# Scheda madre
Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product, SerialNumber

# Temperature (se supportato dall'hardware)
Get-CimInstance MSAcpi_ThermalZoneTemperature -Namespace root/wmi -ErrorAction SilentlyContinue |
    Select-Object InstanceName, @{N='Celsius';E={($_.CurrentTemperature - 2732) / 10}}

# ── Rete ──

# Configurazione IP
Get-CimInstance Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True" |
    Select-Object Description, IPAddress, IPSubnet, DefaultIPGateway, DNSServerSearchOrder

# Adapter attivi
Get-CimInstance Win32_NetworkAdapter -Filter "NetEnabled=True" |
    Select-Object Name, MACAddress, Speed

# ── Storage ──

# Dischi fisici
Get-CimInstance Win32_DiskDrive | Select-Object Model, Size, MediaType, InterfaceType

# Partizioni
Get-CimInstance Win32_DiskPartition | Select-Object DiskIndex, Index, Size, Type

# Volume info
Get-CimInstance Win32_Volume -Filter "DriveType=3" |
    Select-Object Name, Label, Capacity, FreeSpace, FileSystem

# ── Processi ──

# Top 10 processi per memoria
Get-CimInstance Win32_Process |
    Sort-Object WorkingSetSize -Descending |
    Select-Object -First 10 Name, ProcessId, ThreadCount, HandleCount,
        @{N='WS_MB';E={[math]::Round($_.WorkingSetSize/1MB,1)}},
        @{N='Priv_MB';E={[math]::Round($_.PrivatePageCount/1MB,1)}}

# Command line di un processo
Get-CimInstance Win32_Process -Filter "Name='svchost.exe'" |
    Select-Object ProcessId, CommandLine
```

### Sessioni CIM Remote

```powershell
# ── CIM Session: connessioni remote riutilizzabili ──

# Creare sessione (WinRM, default)
$session = New-CimSession -ComputerName SRV01, SRV02, SRV03

# Usare la sessione per query multiple (piu` efficiente di -ComputerName)
Get-CimInstance Win32_OperatingSystem -CimSession $session |
    Select-Object PSComputerName, FreePhysicalMemory

Get-CimInstance Win32_LogicalDisk -CimSession $session -Filter "DriveType=3" |
    Select-Object PSComputerName, DeviceID, FreeSpace

# Chiudere la sessione
Remove-CimSession $session

# Sessione con credenziali diverse
$cred = Get-Credential
$session = New-CimSession -ComputerName SRV01 -Credential $cred

# Sessione DCOM (per server legacy senza WinRM)
$options = New-CimSessionOption -Protocol Dcom
$session = New-CimSession -ComputerName LEGACY-SRV -SessionOption $options
```

---

## Sysmon

Sysmon (System Monitor) e` uno strumento Sysinternals che fornisce logging avanzato di eventi di sistema. Si installa come servizio Windows e scrive nel log `Microsoft-Windows-Sysmon/Operational`.

### Installazione e Configurazione

```powershell
# ── Download e installazione ──
# Scaricare da: https://learn.microsoft.com/sysinternals/downloads/sysmon

# Installazione base (senza configurazione — logga tutto, sconsigliato)
sysmon64 -accepteula -i

# Installazione con file di configurazione (CONSIGLIATO)
sysmon64 -accepteula -i sysmonconfig.xml

# Aggiornare configurazione senza reinstallare
sysmon64 -c sysmonconfig.xml

# Verificare configurazione corrente
sysmon64 -c

# Disinstallare
sysmon64 -u

# Configurazioni community consigliate:
# - SwiftOnSecurity/sysmon-config:
#     github.com/SwiftOnSecurity/sysmon-config
#     Buon bilanciamento tra visibilita` e volume
# - olafhartong/sysmon-modular:
#     github.com/olafhartong/sysmon-modular
#     Modulare, componibile per esigenze specifiche
```

### Event ID Sysmon

```
ID   Nome                     Cosa Registra
──── ──────────────────────── ───────────────────────────────────────────
1    Process Create           Creazione processo (path, hash, parent, command line)
2    File Creation Time       Modifica timestamp file (anti-forensics detection)
3    Network Connect          Connessione di rete (source/dest IP:port, processo)
4    Sysmon Service State     Stato del servizio Sysmon (avvio/stop)
5    Process Terminate        Terminazione processo
6    Driver Loaded            Caricamento driver (hash, firma)
7    Image Loaded             Caricamento DLL/modulo (path, hash, firma)
8    CreateRemoteThread       Thread creato in un altro processo (injection!)
9    RawAccessRead            Lettura raw di disco (bypass filesystem)
10   Process Access           Accesso a processo (tipico: credential dumping)
11   File Create              Creazione file (path, processo creatore)
12   Registry Event           Creazione/cancellazione chiave/valore registry
13   Registry Value Set       Modifica valore registry
14   Registry Rename          Rinomina chiave/valore registry
15   File Create Stream Hash  Creazione Alternate Data Stream (ADS)
17   Pipe Created             Creazione named pipe (C2 communication)
18   Pipe Connected           Connessione a named pipe
19   WMI Event Filter         Registrazione filtro WMI (persistence)
20   WMI Event Consumer       Registrazione consumer WMI (persistence)
21   WMI Event Binding        Binding filtro-consumer WMI (persistence)
22   DNS Query                Query DNS (dominio, risposta, processo)
23   File Delete              Cancellazione file (con archiviazione opzionale)
24   Clipboard Change         Modifica clipboard
25   Process Tampering        Hollowing/herpaderping detection
26   File Delete Logged       Cancellazione file (solo log, no archiviazione)
27   File Block Executable    Blocco eseguibile in directory monitorata
28   File Block Shredding     Blocco sovrascrittura file
```

### Configurazione XML — Esempio Essenziale

```xml
<Sysmon schemaversion="4.90">
  <HashAlgorithms>SHA256</HashAlgorithms>
  <EventFiltering>

    <!-- EVENTO 1: Process Create — logga tutto tranne processi di sistema noti -->
    <RuleGroup name="ProcessCreate" groupRelation="or">
      <ProcessCreate onmatch="exclude">
        <Image condition="is">C:\Windows\System32\backgroundTaskHost.exe</Image>
        <Image condition="is">C:\Windows\System32\SearchProtocolHost.exe</Image>
        <Image condition="is">C:\Windows\System32\SearchFilterHost.exe</Image>
        <Image condition="is">C:\Windows\System32\audiodg.exe</Image>
      </ProcessCreate>
    </RuleGroup>

    <!-- EVENTO 3: Network Connect — logga connessioni sospette -->
    <RuleGroup name="NetworkConnect" groupRelation="or">
      <NetworkConnect onmatch="include">
        <DestinationPort condition="is">4444</DestinationPort>
        <DestinationPort condition="is">5555</DestinationPort>
        <DestinationPort condition="is">8080</DestinationPort>
        <Image condition="is">C:\Windows\System32\cmd.exe</Image>
        <Image condition="is">C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe</Image>
        <Image condition="is">C:\Windows\System32\rundll32.exe</Image>
        <Image condition="is">C:\Windows\System32\regsvr32.exe</Image>
      </NetworkConnect>
    </RuleGroup>

    <!-- EVENTO 10: Process Access — credential dumping detection -->
    <RuleGroup name="ProcessAccess" groupRelation="or">
      <ProcessAccess onmatch="include">
        <TargetImage condition="is">C:\Windows\System32\lsass.exe</TargetImage>
      </ProcessAccess>
    </RuleGroup>

    <!-- EVENTO 11: File Create — monitorare directory sensibili -->
    <RuleGroup name="FileCreate" groupRelation="or">
      <FileCreate onmatch="include">
        <TargetFilename condition="contains">\Startup\</TargetFilename>
        <TargetFilename condition="contains">\Start Menu\</TargetFilename>
        <TargetFilename condition="end with">.exe</TargetFilename>
        <TargetFilename condition="end with">.dll</TargetFilename>
        <TargetFilename condition="end with">.ps1</TargetFilename>
        <TargetFilename condition="end with">.bat</TargetFilename>
      </FileCreate>
    </RuleGroup>

    <!-- EVENTO 22: DNS Query — logga tutto tranne i domini interni -->
    <RuleGroup name="DnsQuery" groupRelation="or">
      <DnsQuery onmatch="exclude">
        <QueryName condition="end with">.corp.contoso.com</QueryName>
        <QueryName condition="end with">.in-addr.arpa</QueryName>
      </DnsQuery>
    </RuleGroup>

  </EventFiltering>
</Sysmon>
```

### Threat Hunting con Sysmon

```powershell
# ── Query Sysmon per threat hunting ──

# Processi sospetti (cmd/powershell lanciati da Office)
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; Id=1} |
    Where-Object {
        $_.Properties[20].Value -like '*WINWORD.EXE*' -or   # ParentImage
        $_.Properties[20].Value -like '*EXCEL.EXE*' -or
        $_.Properties[20].Value -like '*OUTLOOK.EXE*'
    } | ForEach-Object {
        [PSCustomObject]@{
            Time        = $_.TimeCreated
            Image       = $_.Properties[4].Value
            CommandLine = $_.Properties[10].Value
            ParentImage = $_.Properties[20].Value
            User        = $_.Properties[12].Value
        }
    }

# Accesso a LSASS (credential dumping)
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; Id=10} |
    Where-Object { $_.Properties[8].Value -like '*lsass.exe*' } |
    ForEach-Object {
        [PSCustomObject]@{
            Time        = $_.TimeCreated
            SourceImage = $_.Properties[4].Value
            TargetImage = $_.Properties[8].Value
            GrantedAccess = $_.Properties[10].Value
        }
    }

# Connessioni di rete da processi inusuali
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; Id=3} |
    Where-Object {
        $_.Properties[4].Value -like '*powershell*' -or
        $_.Properties[4].Value -like '*cmd.exe*' -or
        $_.Properties[4].Value -like '*rundll32*' -or
        $_.Properties[4].Value -like '*regsvr32*'
    } | ForEach-Object {
        [PSCustomObject]@{
            Time     = $_.TimeCreated
            Image    = $_.Properties[4].Value
            DestIP   = $_.Properties[14].Value
            DestPort = $_.Properties[16].Value
            User     = $_.Properties[12].Value
        }
    }

# Query DNS sospette (lunghezza dominio alta = possibile tunneling)
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; Id=22} |
    Where-Object { $_.Properties[4].Value.Length -gt 50 } |
    ForEach-Object {
        [PSCustomObject]@{
            Time       = $_.TimeCreated
            QueryName  = $_.Properties[4].Value
            Image      = $_.Properties[5].Value
            QueryLen   = $_.Properties[4].Value.Length
        }
    }

# Creazione file eseguibili in directory temp
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; Id=11} |
    Where-Object {
        ($_.Properties[6].Value -like '*\Temp\*' -or
         $_.Properties[6].Value -like '*\AppData\Local\Temp\*') -and
        ($_.Properties[6].Value -like '*.exe' -or
         $_.Properties[6].Value -like '*.dll')
    } | Select-Object -First 20 TimeCreated, @{
        N='TargetFile'; E={$_.Properties[6].Value}
    }, @{
        N='Process'; E={$_.Properties[4].Value}
    }
```

---

## SCOM (System Center Operations Manager)

### Architettura SCOM

```
SCOM e` la soluzione enterprise Microsoft per monitoraggio infrastruttura.
Richiede licenze System Center.

Componenti:
┌──────────────────────────────────────────────────────────────────────┐
│                     SCOM Architecture                                │
│                                                                      │
│  ┌──────────────────┐    ┌──────────────────┐                       │
│  │ Operations       │    │ Web Console      │  Browser-based        │
│  │ Console          │    │ (HTML5)          │  monitoring           │
│  └────────┬─────────┘    └────────┬─────────┘                       │
│           │                       │                                  │
│  ┌────────▼───────────────────────▼─────────┐                       │
│  │     Management Server (MS)                │  Cervello di SCOM    │
│  │     - Workflow engine                     │  - Riceve dati agenti│
│  │     - Alert processing                    │  - Esegue regole     │
│  │     - Notifiche                           │  - Genera alert      │
│  └────┬───────────┬──────────────┬──────────┘                       │
│       │           │              │                                   │
│  ┌────▼────┐ ┌────▼────┐  ┌─────▼──────┐                           │
│  │Oper. DB │ │ Data    │  │ Reporting  │                            │
│  │(SQL)    │ │Warehouse│  │ Server     │                            │
│  │         │ │(SQL DW) │  │ (SSRS)     │                            │
│  └─────────┘ └─────────┘  └────────────┘                            │
│       ▲           ▲                                                  │
│       │           │                                                  │
│  ┌────┴───────────┴──────────────────────┐                          │
│  │         Gateway Server (opzionale)     │  Per DMZ / domini       │
│  │         untrusted                      │  non trusted            │
│  └──────────────┬────────────────────────┘                          │
│                 │                                                     │
│  ┌──────────────▼────────────────────────┐                          │
│  │    Agent   │   Agent   │   Agent      │  Su ogni server          │
│  │    SRV01   │   SRV02   │   SRV03      │  monitorato              │
│  └────────────┴───────────┴──────────────┘                          │
└──────────────────────────────────────────────────────────────────────┘

Componenti chiave:
- Management Server: esegue workflow, processa alert, coordina agenti
- Management Group: un MS + i suoi agenti + database
- Operations Database: stato corrente, configurazione, alert attivi
- Data Warehouse: dati storici per trending e reporting
- Reporting Server: report SSRS personalizzabili
- Gateway Server: proxy per agenti in reti non trusted / DMZ
- Agent: installato su ogni server monitorato, esegue monitor e regole
```

### Management Pack

```
I Management Pack (MP) definiscono cosa monitorare e come:

Management Pack contiene:
├── Monitors            → Definiscono stato (Healthy/Warning/Critical)
├── Rules               → Raccolgono dati o generano alert
├── Tasks               → Azioni eseguibili da console (riavvio servizio, ecc.)
├── Views               → Dashboard e viste personalizzate
├── Knowledge           → Documentazione inline per troubleshooting
├── Discoveries         → Scoprono oggetti da monitorare
└── Overrides           → Personalizzazioni dei parametri

MP Essenziali:
─────────────────────────────────────────────────────────
Windows Server OS MP      → CPU, memoria, disco, servizi, Event Log
SQL Server MP             → Query performance, jobs, always-on health
IIS MP                    → App pool, siti, request performance
Active Directory MP       → Replication, FSMO, DNS, LDAP health
Exchange Server MP        → Mail flow, database, client connectivity
Hyper-V MP                → VM health, host performance
.NET Application MP       → Eccezioni, performance, GC health
Network Monitoring MP     → Switch, router, SNMP device monitoring
─────────────────────────────────────────────────────────

MP personalizzati:
- Creare con Visual Studio Authoring Extensions (VSAE)
- O con Management Pack Author (tool grafico)
- Esportare override in MP sealed separato
```

### Alerting e Notifiche SCOM

```powershell
# ── Configurazione alert e notifiche ──

# Alert severity:
#   0 = Information
#   1 = Warning
#   2 = Critical

# Canali di notifica (Channels):
# - Email (SMTP)
# - SMS (SMTP-to-SMS gateway)
# - Command (eseguire script/comando)
# - Instant Message (deprecato)

# Subscribers: chi riceve le notifiche
# Subscriptions: regole che collegano alert → subscribers

# ── Best practice alert tuning ──

# 1. Non abilitare alert su TUTTI i monitor — troppo rumore
# 2. Iniziare con severity Critical + Warning
# 3. Usare overrides per disabilitare monitor non rilevanti
# 4. Creare subscription per team:
#    - Alert SQL → DBA team
#    - Alert OS → Sysadmin team
#    - Alert Network → Network team
# 5. Review settimanale degli alert non risolti
# 6. Chiudere gli alert "noise" e documentare la reason

# ── PowerShell per SCOM ──
# (richiede Operations Manager Shell)

# Importare modulo
Import-Module OperationsManager

# Alert attivi
Get-SCOMAlert -ResolutionState 0 | Where-Object Severity -eq 2 |
    Select-Object Name, MonitoringObjectPath, TimeRaised, RepeatCount

# Contare alert per severity
Get-SCOMAlert -ResolutionState 0 | Group-Object Severity |
    Select-Object @{N='Severity';E={switch($_.Name){0{'Info'}1{'Warning'}2{'Critical'}}}}, Count

# Chiudere alert risolti
Get-SCOMAlert -Name "Logical Disk Free Space*" -ResolutionState 0 |
    Where-Object MonitoringObjectPath -like '*TempDisk*' |
    Set-SCOMAlert -ResolutionState 255 -Comment "Disco temp, ignorare"
```

---

## Prometheus windows_exporter

`windows_exporter` (gia` noto come `wmi_exporter`) espone metriche Windows come endpoint Prometheus.

### Installazione e Configurazione

```powershell
# ── Installazione come servizio Windows ──

# Download da: https://github.com/prometheus-community/windows_exporter/releases
# Scegliere la versione .msi per installazione come servizio

# Installazione base (tutti i collector predefiniti)
msiexec /i windows_exporter-0.X.Y-amd64.msi

# Installazione con collector selezionati (consigliato, meno overhead)
msiexec /i windows_exporter-0.X.Y-amd64.msi `
    ENABLED_COLLECTORS="cpu,cs,logical_disk,memory,net,os,process,service,system,tcp"

# Installazione silenziosa con porta custom
msiexec /i windows_exporter-0.X.Y-amd64.msi /qn `
    LISTEN_PORT=9182 `
    ENABLED_COLLECTORS="cpu,cs,logical_disk,memory,net,os,service,system"

# Dopo installazione, metriche disponibili su:
# http://localhost:9182/metrics

# ── Collector disponibili ──
# cpu              → Metriche CPU per core e modalita`
# cs               → Computer system (hostname, domain)
# logical_disk     → Spazio e I/O per volume
# memory           → RAM, page file, pool
# net              → Interfacce di rete (byte, pacchetti, errori)
# os               → Versione OS, uptime, processi, utenti
# process          → Per-processo: CPU, memoria, I/O, handles
# service          → Stato servizi Windows
# system           → Context switches, threads, processor queue
# tcp              → Connessioni TCP per stato
# iis              → IIS worker process, richieste, connessioni
# mssql            → SQL Server (buffer, locks, transactions)
# ad               → Active Directory (replication, LDAP, bind)
# dns              → DNS Server queries e zone transfers
# hyperv           → Hyper-V host e VM
# textfile         → Metriche custom da file .prom
```

### Metriche Chiave e PromQL

```yaml
# ── Metriche CPU ──
# windows_cpu_time_total{core="0",mode="idle"}
# Mode: idle, user, privileged, interrupt, dpc

# CPU utilizzazione % (media 5 min, tutti i core)
# PromQL:
#   100 - (avg(rate(windows_cpu_time_total{mode="idle"}[5m])) * 100)

# CPU per core:
#   100 - (rate(windows_cpu_time_total{mode="idle"}[5m]) * 100)

# ── Metriche Memoria ──
# windows_os_physical_memory_free_bytes
# windows_cs_physical_memory_bytes (totale)
# windows_os_paging_free_bytes
# windows_memory_pool_nonpaged_bytes

# Memoria utilizzata %:
#   100 * (1 - windows_os_physical_memory_free_bytes / windows_cs_physical_memory_bytes)

# ── Metriche Disco ──
# windows_logical_disk_free_bytes{volume="C:"}
# windows_logical_disk_size_bytes{volume="C:"}
# windows_logical_disk_read_bytes_total
# windows_logical_disk_write_bytes_total
# windows_logical_disk_idle_seconds_total

# Spazio libero %:
#   100 * windows_logical_disk_free_bytes / windows_logical_disk_size_bytes

# IOPS (rate):
#   rate(windows_logical_disk_reads_total[5m]) + rate(windows_logical_disk_writes_total[5m])

# ── Metriche Rete ──
# windows_net_bytes_received_total{nic="Ethernet"}
# windows_net_bytes_sent_total{nic="Ethernet"}
# windows_net_packets_outbound_errors_total

# Throughput (byte/sec):
#   rate(windows_net_bytes_received_total[5m]) + rate(windows_net_bytes_sent_total[5m])

# ── Metriche Servizi ──
# windows_service_state{name="wuauserv",state="running"}
# Valore 1 = servizio in quello stato

# Servizi non running che dovrebbero esserlo:
#   windows_service_state{state="running"} == 0
#     AND windows_service_start_mode{start_mode="auto"} == 1

# ── Metriche OS ──
# windows_os_time (epoch timestamp)
# windows_os_info{product="...", version="..."}
# windows_os_process_count
```

### Configurazione Prometheus (scrape target)

```yaml
# ── prometheus.yml (aggiungere nella sezione scrape_configs) ──

scrape_configs:
  - job_name: 'windows-servers'
    scrape_interval: 30s
    scrape_timeout: 15s
    static_configs:
      - targets:
          - 'srv01.corp.contoso.com:9182'
          - 'srv02.corp.contoso.com:9182'
          - 'srv03.corp.contoso.com:9182'
        labels:
          env: 'production'
          role: 'app-server'

      - targets:
          - 'db01.corp.contoso.com:9182'
          - 'db02.corp.contoso.com:9182'
        labels:
          env: 'production'
          role: 'database'

    # Relabel per estrarre hostname dal target
    relabel_configs:
      - source_labels: [__address__]
        regex: '(.+):.*'
        target_label: 'instance'
        replacement: '${1}'
```

### Grafana Dashboard

```
# ── Dashboard Grafana per windows_exporter ──

# Dashboard community raccomandate (Grafana.com):
# - ID 14694: "Windows Exporter Dashboard" (panoramica completa)
# - ID 10467: "Windows Server" (compatto)

# Pannelli consigliati per dashboard custom:

# Riga 1: Overview
# ├── Gauge: CPU %
# ├── Gauge: Memory %
# ├── Gauge: Disk C: Free %
# └── Stat: Uptime

# Riga 2: Trend temporali
# ├── Time series: CPU % (rate 5m)
# ├── Time series: Memory Usage (bytes)
# └── Time series: Disk I/O (read+write rate)

# Riga 3: Rete
# ├── Time series: Network throughput (in+out)
# └── Time series: TCP connections

# Riga 4: Servizi
# └── Table: Servizi non running (filtro auto-start)

# Variabili dashboard (Template variables):
# - $instance: label_values(windows_os_info, instance)
# - $volume:   label_values(windows_logical_disk_size_bytes{instance="$instance"}, volume)
```

---

## Zabbix Agent per Windows

### Installazione e Configurazione Agent

```powershell
# ── Installazione Zabbix Agent 2 (Go-based, consigliato) ──

# Download: https://www.zabbix.com/download_agents
# Installare tramite MSI o ZIP

# Installazione MSI silenziosa
msiexec /i zabbix_agent2-7.X.Y-windows-amd64.msi /qn `
    SERVER=zabbix-server.corp.contoso.com `
    SERVERACTIVE=zabbix-server.corp.contoso.com `
    HOSTNAME=SRV01.corp.contoso.com `
    LISTENPORT=10050

# ── Configurazione: C:\Program Files\Zabbix Agent 2\zabbix_agent2.conf ──

# Parametri essenziali:
# Server=zabbix-server.corp.contoso.com          # IP/FQDN del Zabbix server
# ServerActive=zabbix-server.corp.contoso.com     # Per active checks
# Hostname=SRV01.corp.contoso.com                 # DEVE corrispondere al nome host in Zabbix
# ListenPort=10050                                # Porta agent (default)
# LogFile=C:\Program Files\Zabbix Agent 2\zabbix_agent2.log
# Timeout=10
# AllowKey=system.run[*]                          # Abilitare solo se necessario (rischio sicurezza)
# DenyKey=system.run[*]                           # Default deny (sicuro)
# TLSConnect=psk                                  # Crittografia PSK
# TLSAccept=psk
# TLSPSKIdentity=PSK-SRV01
# TLSPSKFile=C:\Program Files\Zabbix Agent 2\zabbix_agent2.psk

# ── Generare PSK per crittografia ──
# openssl rand -hex 32 > zabbix_agent2.psk
# Il contenuto del file (es. a1b2c3d4e5f6...) va inserito anche nel Zabbix server

# Riavviare servizio dopo modifica configurazione
Restart-Service "Zabbix Agent 2"
```

### Template e Item Predefiniti

```
Template consigliati (Zabbix server):
─────────────────────────────────────────────────────────
Template OS Windows by Zabbix agent       → Monitoraggio base
Template Module Windows services          → Stato servizi (LLD)
Template App IIS by Zabbix agent          → IIS monitoring
Template App MS SQL by Zabbix agent       → SQL Server
Template App AD DS by Zabbix agent        → Active Directory
─────────────────────────────────────────────────────────

Item chiave predefiniti (dal template OS Windows):

CPU:
  system.cpu.load[percpu,avg1]        → Load average per core (1 min)
  system.cpu.util[,user]              → CPU user %
  system.cpu.util[,privileged]        → CPU kernel %
  perf_counter_en["\System\Processor Queue Length"]

Memoria:
  vm.memory.size[total]               → RAM totale
  vm.memory.size[available]           → RAM disponibile
  vm.memory.size[pavailable]          → RAM disponibile %
  perf_counter_en["\Memory\Pages/sec"]
  perf_counter_en["\Memory\Pool Nonpaged Bytes"]

Disco:
  vfs.fs.size[C:,total]              → Dimensione totale volume
  vfs.fs.size[C:,free]               → Spazio libero
  vfs.fs.size[C:,pfree]             → Spazio libero %
  perf_counter_en["\PhysicalDisk(_Total)\Avg. Disk Queue Length"]

Rete:
  net.if.in["{#IFNAME}"]            → Byte ricevuti
  net.if.out["{#IFNAME}"]           → Byte inviati
  perf_counter_en["\Network Interface(*)\Output Queue Length"]

Sistema:
  system.uptime                       → Uptime in secondi
  system.hostname                     → Hostname
  system.uname                        → Versione OS
  eventlog[System,,"Error",,,,]       → Errori nel log System
```

### Low-Level Discovery (LLD)

```
LLD scopre automaticamente oggetti e crea item/trigger per ciascuno:

Discovery rule predefinite:

1. Filesystem Discovery:
   - Chiave: vfs.fs.discovery
   - Scopre tutti i volumi (C:, D:, ecc.)
   - Crea item per spazio libero/totale su ogni volume
   - Crea trigger per spazio insufficiente

2. Network Interface Discovery:
   - Chiave: net.if.discovery
   - Scopre tutte le interfacce di rete attive
   - Crea item per throughput in/out per interfaccia
   - Crea trigger per errori di rete

3. Windows Service Discovery:
   - Chiave: service.discovery
   - Scopre tutti i servizi con startup "automatic"
   - Crea item per stato di ogni servizio
   - Crea trigger se un servizio auto-start e` stopped

4. Physical Disk Discovery:
   - Scopre dischi fisici
   - Crea item per IOPS, latenza, queue length per disco
```

### Custom UserParameter

```powershell
# ── Item custom con UserParameter ──
# Aggiungere in zabbix_agent2.conf:

# Numero di connessioni TCP stabilite
# UserParameter=tcp.established,powershell -NoProfile -Command "(Get-NetTCPConnection -State Established | Measure-Object).Count"

# Dimensione cartella specifica (in byte)
# UserParameter=folder.size[*],powershell -NoProfile -Command "(Get-ChildItem -Path '$1' -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum"

# Ultimo riavvio (epoch)
# UserParameter=last.reboot,powershell -NoProfile -Command "[int](New-TimeSpan -Start (Get-Date '1970-01-01') -End (Get-CimInstance Win32_OperatingSystem).LastBootUpTime).TotalSeconds"

# Stato di un servizio specifico (1=running, 0=stopped)
# UserParameter=svc.check[*],powershell -NoProfile -Command "if((Get-Service '$1' -ErrorAction SilentlyContinue).Status -eq 'Running'){1}else{0}"

# Certificati in scadenza nei prossimi 30 giorni
# UserParameter=cert.expiring,powershell -NoProfile -Command "(Get-ChildItem Cert:\LocalMachine\My | Where-Object NotAfter -lt (Get-Date).AddDays(30) | Measure-Object).Count"

# Dopo la modifica, riavviare l'agent:
# Restart-Service "Zabbix Agent 2"

# Test dell'item da riga di comando (sul Zabbix server):
# zabbix_get -s SRV01.corp.contoso.com -k tcp.established
# zabbix_get -s SRV01.corp.contoso.com -k svc.check[wuauserv]
```

---

## Azure Monitor e Monitoraggio Ibrido

### Azure Monitor Agent (AMA) — Architettura

```
Azure Monitor Agent (AMA) e` il successore unificato di Log Analytics Agent (MMA)
e dell'agente Diagnostics. AMA supporta Windows Server 2012 R2+ e consente
la raccolta centralizzata di metriche, log, eventi e performance counter
sia per VM Azure sia per server on-premises collegati tramite Azure Arc.

Architettura:
                          ┌──────────────────┐
                          │  Azure Monitor    │
                          │  ┌──────────────┐ │
                          │  │ Log Analytics │ │
                          │  │  Workspace    │ │
                          │  └──────────────┘ │
                          │  ┌──────────────┐ │
                          │  │ Metrics DB    │ │
                          │  └──────────────┘ │
                          └────────┬─────────┘
                                   │ HTTPS 443
                    ┌──────────────┼──────────────┐
                    │              │              │
              ┌─────▼─────┐ ┌────▼────┐  ┌─────▼──────┐
              │ Azure VM  │ │ Arc     │  │ Arc        │
              │ + AMA     │ │ Server  │  │ Server     │
              │           │ │ + AMA   │  │ + AMA      │
              │ (cloud)   │ │ (on-pr) │  │ (on-prem)  │
              └───────────┘ └─────────┘  └────────────┘

Componenti chiave:
- Data Collection Rules (DCR): definiscono COSA raccogliere e DOVE inviare
- Data Collection Endpoints (DCE): endpoint regionali per ingestione
- Azure Arc: estende Azure management a server on-premises e multi-cloud
```

### Installazione Azure Arc per Server On-Premises

```powershell
# Passo 1: Scaricare e installare Azure Connected Machine Agent
# Scaricare da: https://aka.ms/AzureConnectedMachineAgent (MSI)
# Oppure via script generato dal portale Azure (consigliato)

# Passo 2: Registrare il server con Azure Arc (richiede credenziali)
& "$env:ProgramW6432\AzureConnectedMachineAgent\azcmagent.exe" connect `
    --resource-group "rg-monitoring" `
    --tenant-id "TENANT-ID" `
    --location "westeurope" `
    --subscription-id "SUB-ID"

# Passo 3: Verificare stato della connessione
& "$env:ProgramW6432\AzureConnectedMachineAgent\azcmagent.exe" show

# Output atteso:
# Resource Name   : SRV-PROD-01
# Resource Group  : rg-monitoring
# Agent Status    : Connected
# Agent Version   : 1.45.xxxxx

# Passo 4: Verificare dal portale Azure
# Azure Portal → Azure Arc → Servers → il server dovrebbe essere visibile
# con stato "Connected"

# Firewall: assicurarsi che il server raggiunga:
# - *.his.arc.azure.com (443)
# - *.guestconfiguration.azure.com (443)
# - login.microsoftonline.com (443)
# - management.azure.com (443)
# - *.blob.core.windows.net (443)
```

### Data Collection Rules (DCR)

```powershell
# Le DCR sostituiscono la configurazione per-workspace di MMA
# e permettono una granularita` molto superiore.

# Esempio: creare una DCR per raccogliere Performance Counter e Event Log
# Questo si fa normalmente via Azure Portal, ARM template, Bicep o Terraform.

# Esempio Bicep (Infrastructure as Code):
# resource dcr 'Microsoft.Insights/dataCollectionRules@2022-06-01' = {
#   name: 'dcr-windows-perf'
#   location: 'westeurope'
#   properties: {
#     dataSources: {
#       performanceCounters: [
#         {
#           name: 'perfCounterDataSource'
#           streams: ['Microsoft-Perf']
#           samplingFrequencyInSeconds: 60
#           counterSpecifiers: [
#             '\\Processor(_Total)\\% Processor Time'
#             '\\Memory\\Available MBytes'
#             '\\LogicalDisk(C:)\\% Free Space'
#             '\\Network Interface(*)\\Bytes Total/sec'
#             '\\PhysicalDisk(_Total)\\Avg. Disk sec/Read'
#           ]
#         }
#       ]
#       windowsEventLogs: [
#         {
#           name: 'eventLogDataSource'
#           streams: ['Microsoft-Event']
#           xPathQueries: [
#             'Application!*[System[(Level=1 or Level=2 or Level=3)]]'
#             'System!*[System[(Level=1 or Level=2 or Level=3)]]'
#             'Security!*[System[(EventID=4625 or EventID=4648)]]'
#           ]
#         }
#       ]
#     }
#     destinations: {
#       logAnalytics: [
#         {
#           workspaceResourceId: '/subscriptions/.../workspaces/law-prod'
#           name: 'lawDest'
#         }
#       ]
#     }
#     dataFlows: [
#       { streams: ['Microsoft-Perf'] destinations: ['lawDest'] }
#       { streams: ['Microsoft-Event'] destinations: ['lawDest'] }
#     ]
#   }
# }

# Associare la DCR a un server Arc (PowerShell Az module):
# New-AzDataCollectionRuleAssociation `
#     -TargetResourceId "/subscriptions/.../Microsoft.HybridCompute/machines/SRV01" `
#     -AssociationName "assoc-dcr-perf" `
#     -RuleId "/subscriptions/.../dataCollectionRules/dcr-windows-perf"
```

### Query KQL per Log Analytics

```
// KQL (Kusto Query Language) e` il linguaggio di query di Azure Monitor.

// CPU media per server nelle ultime 24 ore
Perf
| where TimeGenerated > ago(24h)
| where ObjectName == "Processor" and CounterName == "% Processor Time"
| where InstanceName == "_Total"
| summarize AvgCPU = avg(CounterValue) by Computer, bin(TimeGenerated, 1h)
| render timechart

// RAM disponibile — trend settimanale
Perf
| where TimeGenerated > ago(7d)
| where ObjectName == "Memory" and CounterName == "Available MBytes"
| summarize AvgRAM = avg(CounterValue) by Computer, bin(TimeGenerated, 4h)
| render timechart

// Spazio disco sotto soglia (< 20% libero)
Perf
| where TimeGenerated > ago(1h)
| where ObjectName == "LogicalDisk" and CounterName == "% Free Space"
| where InstanceName !in ("_Total", "HarddiskVolume1")
| where CounterValue < 20
| project Computer, InstanceName, CounterValue
| order by CounterValue asc

// Logon falliti (EventID 4625) raggruppati per IP sorgente
SecurityEvent
| where TimeGenerated > ago(24h)
| where EventID == 4625
| summarize FailedLogons = count() by IpAddress, TargetAccount
| where FailedLogons > 5
| order by FailedLogons desc

// Alert rule: CPU sostenuta > 90% per almeno 15 minuti
// (da configurare come Scheduled Query Rule in Azure Monitor)
Perf
| where TimeGenerated > ago(20m)
| where ObjectName == "Processor" and CounterName == "% Processor Time"
| where InstanceName == "_Total"
| summarize AvgCPU = avg(CounterValue) by Computer
| where AvgCPU > 90
```

### Confronto: Soluzioni On-Premises vs Ibride

```
Caratteristica       │ SCOM           │ Prometheus     │ Zabbix         │ Azure Monitor
─────────────────────┼────────────────┼────────────────┼────────────────┼───────────────
Modello              │ On-prem        │ On-prem        │ On-prem        │ Cloud/Hybrid
Costo licenza        │ System Center  │ Open source    │ Open source    │ Pay-per-GB
Agent Windows        │ SCOM Agent     │ windows_export │ Zabbix Agent 2 │ AMA
Linguaggio query     │ SCSM/SQL       │ PromQL         │ Trigger expr   │ KQL
Retention default    │ 7gg (DB), 400  │ 15gg (TSDB)    │ 365gg (dipende)│ 30gg (config.)
Scalabilita`         │ Migliaia       │ Milioni (Thano)│ Centinaia mig. │ Illimitata
Dashboard            │ SCOM Console   │ Grafana        │ Built-in       │ Azure Workbook
Alerting             │ Built-in       │ Alertmanager   │ Built-in       │ Action Groups
Multi-cloud          │ No             │ Si (exporters) │ Si (agent)     │ Si (Arc)
Best for             │ Enterprise MS  │ Cloud-native   │ Heterogeneous  │ Azure + hybrid

Strategia consigliata per ambienti enterprise misti:
- Azure Monitor + AMA per tutti i server (cloud e on-prem via Arc)
- Prometheus/Grafana per workload containerizzati e Kubernetes
- SCOM per applicazioni legacy .NET con management pack specifici
- Zabbix come alternativa open source per PMI con infrastruttura mista
```

---

## Metodologia Baseline

### Che Cos'e` una Baseline

```
Una baseline e` un insieme di misurazioni delle performance raccolte
in condizioni operative normali. Senza baseline:

- Non si puo` distinguere "lento" da "normale per quel server"
- Non si possono impostare soglie alert sensate
- Non si puo` fare capacity planning
- Non si possono correlare cambiamenti con impatti

WORKFLOW BASELINE:
1. Definire → cosa misurare, su quali server
2. Raccogliere → Data Collector Set per 1-2 settimane lavorative
3. Analizzare → calcolare avg, P95, peak per ogni contatore
4. Documentare → creare report baseline
5. Confrontare → periodicamente (mensile/trimestrale)
6. Aggiornare → dopo modifiche significative (upgrade HW, deploy applicazioni)
```

### Stabilire la Baseline

```powershell
# ── Fase 1: Definire i contatori ──

# Set minimo per ogni server:
$counters = @(
    '\Processor(_Total)\% Processor Time'
    '\Processor(_Total)\% Privileged Time'
    '\System\Processor Queue Length'
    '\Memory\Available MBytes'
    '\Memory\Pages/sec'
    '\Memory\% Committed Bytes In Use'
    '\Memory\Pool Nonpaged Bytes'
    '\PhysicalDisk(_Total)\Avg. Disk Queue Length'
    '\PhysicalDisk(_Total)\Avg. Disk sec/Read'
    '\PhysicalDisk(_Total)\Avg. Disk sec/Write'
    '\PhysicalDisk(_Total)\Disk Transfers/sec'
    '\LogicalDisk(C:)\% Free Space'
    '\Network Interface(*)\Bytes Total/sec'
    '\Network Interface(*)\Output Queue Length'
    '\TCPv4\Connections Established'
)

# ── Fase 2: Raccogliere (2 settimane, ogni 30 secondi) ──

logman create counter "Baseline-$(Get-Date -Format 'yyyyMM')" `
    -c $counters -si 30 -f csv `
    -o "C:\PerfLogs\Baseline\$(Get-Date -Format 'yyyyMM')" `
    -rf 336:00:00 -r    # 14 giorni

logman start "Baseline-$(Get-Date -Format 'yyyyMM')"

# ── Fase 3: Analizzare ──

function Get-BaselineStats {
    param([string]$CsvPath)

    $data = Import-Csv $CsvPath
    $results = @()

    foreach ($prop in ($data[0].PSObject.Properties | Where-Object Name -ne '(PDH-CSV 4.0)')) {
        $colName = $prop.Name
        $values = $data.$colName | Where-Object { $_ -ne '' -and $_ -ne ' ' } |
            ForEach-Object { [double]$_ }

        if ($values.Count -gt 0) {
            $sorted = $values | Sort-Object
            $results += [PSCustomObject]@{
                Counter = ($colName -replace '\\\\[^\\]+\\', '\')  # rimuovi hostname
                Avg     = [math]::Round(($sorted | Measure-Object -Average).Average, 2)
                Min     = [math]::Round(($sorted | Measure-Object -Minimum).Minimum, 2)
                Max     = [math]::Round(($sorted | Measure-Object -Maximum).Maximum, 2)
                P50     = [math]::Round($sorted[[math]::Floor($sorted.Count * 0.50)], 2)
                P95     = [math]::Round($sorted[[math]::Floor($sorted.Count * 0.95)], 2)
                P99     = [math]::Round($sorted[[math]::Floor($sorted.Count * 0.99)], 2)
                Samples = $values.Count
            }
        }
    }
    $results
}

Get-BaselineStats "C:\PerfLogs\Baseline\202601_000001.csv" | Format-Table -AutoSize
```

### Confronto Baseline

```powershell
# ── Confrontare baseline corrente con precedente ──

function Compare-Baselines {
    param(
        [string]$BaselinePath,
        [string]$CurrentPath,
        [double]$ThresholdPercent = 20    # alert se variazione > 20%
    )

    $baseline = Get-BaselineStats $BaselinePath
    $current  = Get-BaselineStats $CurrentPath

    foreach ($b in $baseline) {
        $c = $current | Where-Object Counter -eq $b.Counter
        if ($c) {
            $change = if ($b.Avg -ne 0) {
                [math]::Round(($c.Avg - $b.Avg) / $b.Avg * 100, 1)
            } else { 0 }

            $status = if ([math]::Abs($change) -gt $ThresholdPercent) { 'ALERT' } else { 'OK' }

            [PSCustomObject]@{
                Counter        = $b.Counter
                'Baseline Avg' = $b.Avg
                'Current Avg'  = $c.Avg
                'Change %'     = $change
                'Baseline P95' = $b.P95
                'Current P95'  = $c.P95
                Status         = $status
            }
        }
    }
}

Compare-Baselines "C:\PerfLogs\Baseline\202601.csv" "C:\PerfLogs\Baseline\202604.csv" |
    Format-Table -AutoSize
```

### Trending

```
Trending = analisi dell'andamento nel tempo dei contatori chiave.

Frequenza raccolta:
─────────────────────────────────────────────────────────
Contatore                      │ Intervallo │ Retention
───────────────────────────────┼────────────┼──────────
CPU %, Memory Available        │ 30 sec     │ 30 giorni
Disk Queue, Disk sec/Read      │ 30 sec     │ 30 giorni
Disk Free Space                │ 5 min      │ 1 anno
Network Throughput             │ 30 sec     │ 30 giorni
TCP Connections                │ 1 min      │ 90 giorni
─────────────────────────────────────────────────────────

Segnali di degrado:
- CPU avg in crescita mese su mese → carico crescente, pianificare scale-up
- Memory Available in calo costante → memory leak o crescita workload
- Disk Free Space in calo lineare → calcolare data esaurimento
- Disk Queue Length in crescita → storage insufficiente per carico I/O
- P95 in aumento rapido anche se avg stabile → picchi piu` frequenti
```

---

## Capacity Planning

### Metodologia

```
Il capacity planning prevede le risorse necessarie in futuro
basandosi su dati storici (baseline + trending).

PROCESSO:
1. RACCOGLIERE dati storici (almeno 3-6 mesi di baseline)
2. IDENTIFICARE trend (crescita, stagionalita`, eventi)
3. PROIETTARE nel futuro (regressione lineare, modelli)
4. DEFINIRE soglie di capacita` (quando serve intervento)
5. PIANIFICARE interventi (upgrade HW, ottimizzazione SW, cloud burst)
6. RIVEDERE trimestralmente

FORMULA BASE:
  Mesi_rimanenti = (Capacita_totale - Uso_corrente) / Crescita_mensile

Esempio:
  Disco 500 GB, uso corrente 350 GB, crescita 15 GB/mese
  (500 - 350) / 15 = 10 mesi prima di esaurimento
```

### Calcolo Proiezioni

```powershell
# ── Proiezione spazio disco ──

function Get-DiskExhaustion {
    param(
        [string]$DriveLetter = "C:",
        [int]$MonthsHistory = 6
    )

    $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$DriveLetter'"
    $totalGB = [math]::Round($disk.Size / 1GB, 1)
    $freeGB  = [math]::Round($disk.FreeSpace / 1GB, 1)
    $usedGB  = $totalGB - $freeGB

    # Simulazione: in produzione, leggere dati storici dal CSV
    # Qui usiamo il valore corrente come punto di partenza
    Write-Output "Volume $DriveLetter"
    Write-Output "  Totale:  $totalGB GB"
    Write-Output "  Usato:   $usedGB GB ($([math]::Round($usedGB/$totalGB*100,1))%)"
    Write-Output "  Libero:  $freeGB GB ($([math]::Round($freeGB/$totalGB*100,1))%)"

    # Inserire qui il tasso di crescita stimato (dal trending)
    $growthPerMonth = Read-Host "Crescita stimata (GB/mese)"
    if ([double]$growthPerMonth -gt 0) {
        $months = [math]::Floor($freeGB / [double]$growthPerMonth)
        $exhaustDate = (Get-Date).AddMonths($months)
        Write-Output "  Crescita: $growthPerMonth GB/mese"
        Write-Output "  Esaurimento stimato: $exhaustDate ($months mesi)"
        if ($months -lt 3) {
            Write-Output "  >>> AZIONE URGENTE: meno di 3 mesi rimanenti <<<"
        }
    }
}

Get-DiskExhaustion -DriveLetter "C:"

# ── Proiezione risorse multi-server ──

function Get-CapacityReport {
    param([string[]]$Servers)

    foreach ($srv in $Servers) {
        $os   = Get-CimInstance Win32_OperatingSystem -ComputerName $srv
        $cpu  = Get-CimInstance Win32_Processor -ComputerName $srv
        $disk = Get-CimInstance Win32_LogicalDisk -ComputerName $srv -Filter "DriveType=3"

        $memTotalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
        $memFreeGB  = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
        $memUsedPc  = [math]::Round(($memTotalGB - $memFreeGB) / $memTotalGB * 100, 1)

        [PSCustomObject]@{
            Server    = $srv
            CPU_Load  = $cpu.LoadPercentage
            'Mem GB'  = "$memFreeGB / $memTotalGB"
            'Mem %'   = $memUsedPc
            Disks     = ($disk | ForEach-Object {
                "{0} {1}%" -f $_.DeviceID, [math]::Round($_.FreeSpace/$_.Size*100,1)
            }) -join ' | '
            Status    = if ($memUsedPc -gt 90 -or $cpu.LoadPercentage -gt 85) { 'ATTENZIONE' } else { 'OK' }
        }
    }
}

Get-CapacityReport -Servers 'SRV01','SRV02','SRV03' | Format-Table -AutoSize
```

### Dimensionamento Risorse

```
Linee guida per dimensionamento server Windows:

Ruolo               │ CPU (core) │ RAM (GB) │ Disco Sistema │ Disco Dati
────────────────────┼────────────┼──────────┼───────────────┼──────────────
File Server         │ 2-4        │ 8-16     │ 60 GB SSD     │ Dimensionare
Print Server        │ 2          │ 4-8      │ 60 GB SSD     │ 20 GB
Web Server (IIS)    │ 4-8        │ 16-32    │ 60 GB SSD     │ App-dependent
SQL Server (small)  │ 4-8        │ 32-64    │ 60 GB SSD     │ SSD fast, dim.
SQL Server (medium) │ 8-16       │ 64-128   │ 60 GB SSD     │ SSD NVMe
DC (< 1000 utenti)  │ 2-4        │ 8-16     │ 80 GB SSD     │ N/A
DC (> 5000 utenti)  │ 4-8        │ 16-32    │ 100 GB SSD    │ N/A
SCOM Management     │ 4-8        │ 16-32    │ 80 GB SSD     │ 200+ GB
Hyper-V Host        │ 8-32       │ 64-512   │ 60 GB SSD     │ SSD per VM
RDS Session Host    │ 4+ (1/15u) │ 2GB/user │ 60 GB SSD     │ Profile disk

Regole pratiche:
- CPU: target avg < 60%, picchi < 85% (lasciare margine)
- RAM: target uso < 80% (page file non deve essere usato attivamente)
- Disco: > 20% libero sempre, > 30% per volumi con crescita
- Rete: < 60% banda utilizzata (headroom per picchi)
```

---

## Automazione Report e Alerting Proattivo

### Script PowerShell per Report HTML Automatizzato

```powershell
# Health-Report.ps1 — Genera un report HTML giornaliero dalle baseline

param(
    [string[]]$ComputerName = @("SRV-DC01", "SRV-APP01", "SRV-SQL01"),
    [string]$OutputPath = "C:\Reports\HealthReport_$(Get-Date -Format 'yyyyMMdd').html",
    [string]$SmtpServer = "smtp.corp.contoso.com",
    [string]$MailTo = "sysadmin@corp.contoso.com"
)

# Definire soglie (derivate dalla baseline — vedere sezione precedente)
$thresholds = @{
    CPUWarning       = 70
    CPUCritical      = 90
    RAMWarningPct    = 80
    RAMCriticalPct   = 90
    DiskWarningPct   = 20    # % libero sotto questa soglia → warning
    DiskCriticalPct  = 10    # % libero sotto questa soglia → critico
}

# Raccogliere dati da ogni server
$results = foreach ($server in $ComputerName) {
    try {
        $session = New-CimSession -ComputerName $server -ErrorAction Stop

        # CPU
        $cpu = (Get-CimInstance -CimSession $session Win32_Processor |
            Measure-Object -Property LoadPercentage -Average).Average

        # RAM
        $os = Get-CimInstance -CimSession $session Win32_OperatingSystem
        $ramUsedPct = [math]::Round(
            (($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) /
             $os.TotalVisibleMemorySize) * 100, 1)

        # Dischi
        $disks = Get-CimInstance -CimSession $session Win32_LogicalDisk -Filter "DriveType=3" |
            ForEach-Object {
                [PSCustomObject]@{
                    Drive     = $_.DeviceID
                    SizeGB    = [math]::Round($_.Size / 1GB, 1)
                    FreeGB    = [math]::Round($_.FreeSpace / 1GB, 1)
                    FreePct   = [math]::Round(($_.FreeSpace / $_.Size) * 100, 1)
                }
            }

        # Uptime
        $uptime = (Get-Date) - $os.LastBootUpTime

        # Servizi critici in stato diverso da Running
        $failedSvcs = Get-CimInstance -CimSession $session Win32_Service |
            Where-Object { $_.StartMode -eq 'Auto' -and $_.State -ne 'Running' } |
            Select-Object Name, State

        Remove-CimSession $session

        [PSCustomObject]@{
            Server       = $server
            CPU          = $cpu
            RAMUsedPct   = $ramUsedPct
            Disks        = $disks
            UptimeDays   = [math]::Round($uptime.TotalDays, 1)
            FailedSvcs   = $failedSvcs
            Status       = "OK"
        }
    }
    catch {
        [PSCustomObject]@{
            Server     = $server
            CPU        = -1
            RAMUsedPct = -1
            Disks      = @()
            UptimeDays = -1
            FailedSvcs = @()
            Status     = "UNREACHABLE: $($_.Exception.Message)"
        }
    }
}

# Generare HTML
$css = @"
<style>
    body { font-family: 'Segoe UI', sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; margin: 15px 0; }
    th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; }
    th { background: #0078D4; color: white; }
    .ok { background: #DFF6DD; }
    .warn { background: #FFF4CE; }
    .crit { background: #FDE7E9; color: #A80000; font-weight: bold; }
    .unreachable { background: #666; color: white; }
    h1 { color: #0078D4; }
    .timestamp { color: #666; font-size: 0.9em; }
</style>
"@

$htmlBody = "<html><head>$css</head><body>"
$htmlBody += "<h1>Health Report — $(Get-Date -Format 'dd MMMM yyyy HH:mm')</h1>"

foreach ($r in $results) {
    if ($r.Status -ne "OK") {
        $htmlBody += "<h2>$($r.Server) <span class='crit'>$($r.Status)</span></h2>"
        continue
    }

    # Determinare classe CSS per CPU e RAM
    $cpuClass = if ($r.CPU -ge $thresholds.CPUCritical) { "crit" }
                elseif ($r.CPU -ge $thresholds.CPUWarning) { "warn" }
                else { "ok" }
    $ramClass = if ($r.RAMUsedPct -ge $thresholds.RAMCriticalPct) { "crit" }
                elseif ($r.RAMUsedPct -ge $thresholds.RAMWarningPct) { "warn" }
                else { "ok" }

    $htmlBody += "<h2>$($r.Server)</h2>"
    $htmlBody += "<table><tr><th>Metrica</th><th>Valore</th><th>Stato</th></tr>"
    $htmlBody += "<tr><td>CPU</td><td>$($r.CPU)%</td><td class='$cpuClass'>$(if($cpuClass -eq 'ok'){'OK'}elseif($cpuClass -eq 'warn'){'WARNING'}else{'CRITICAL'})</td></tr>"
    $htmlBody += "<tr><td>RAM Utilizzata</td><td>$($r.RAMUsedPct)%</td><td class='$ramClass'>$(if($ramClass -eq 'ok'){'OK'}elseif($ramClass -eq 'warn'){'WARNING'}else{'CRITICAL'})</td></tr>"
    $htmlBody += "<tr><td>Uptime</td><td>$($r.UptimeDays) giorni</td><td class='ok'>INFO</td></tr>"

    foreach ($d in $r.Disks) {
        $dClass = if ($d.FreePct -le $thresholds.DiskCriticalPct) { "crit" }
                  elseif ($d.FreePct -le $thresholds.DiskWarningPct) { "warn" }
                  else { "ok" }
        $htmlBody += "<tr><td>Disco $($d.Drive)</td><td>$($d.FreeGB) GB liberi ($($d.FreePct)%)</td><td class='$dClass'>$(if($dClass -eq 'ok'){'OK'}elseif($dClass -eq 'warn'){'WARNING'}else{'CRITICAL'})</td></tr>"
    }

    if ($r.FailedSvcs.Count -gt 0) {
        $svcList = ($r.FailedSvcs | ForEach-Object { "$($_.Name) ($($_.State))" }) -join ", "
        $htmlBody += "<tr><td>Servizi Auto non Running</td><td>$svcList</td><td class='crit'>CRITICAL</td></tr>"
    }
    else {
        $htmlBody += "<tr><td>Servizi Auto</td><td>Tutti Running</td><td class='ok'>OK</td></tr>"
    }

    $htmlBody += "</table>"
}

$htmlBody += "<p class='timestamp'>Report generato: $(Get-Date -Format 'o')</p>"
$htmlBody += "</body></html>"

# Salvare e inviare
$htmlBody | Out-File -FilePath $OutputPath -Encoding UTF8

# Determinare se ci sono condizioni critiche
$hasCritical = $results | Where-Object {
    $_.Status -ne "OK" -or
    $_.CPU -ge $thresholds.CPUCritical -or
    $_.RAMUsedPct -ge $thresholds.RAMCriticalPct -or
    ($_.Disks | Where-Object { $_.FreePct -le $thresholds.DiskCriticalPct }) -or
    $_.FailedSvcs.Count -gt 0
}

$subject = if ($hasCritical) {
    "[CRITICAL] Health Report — $(Get-Date -Format 'dd/MM/yyyy')"
} else {
    "[OK] Health Report — $(Get-Date -Format 'dd/MM/yyyy')"
}

Send-MailMessage -From "monitoring@corp.contoso.com" `
    -To $MailTo `
    -Subject $subject `
    -Body $htmlBody `
    -BodyAsHtml `
    -SmtpServer $SmtpServer `
    -Encoding UTF8

Write-Host "Report salvato: $OutputPath"
```

### Schedulazione Automatica

```powershell
# Creare un Scheduled Task per esecuzione giornaliera alle 07:00
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\Scripts\Health-Report.ps1"

$trigger = New-ScheduledTaskTrigger -Daily -At "07:00"

$principal = New-ScheduledTaskPrincipal `
    -UserId "CORP\svc-monitoring" `
    -LogonType Password `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -WakeToRun

Register-ScheduledTask `
    -TaskName "DailyHealthReport" `
    -TaskPath "\Monitoring\" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Report giornaliero health check infrastruttura Windows"

# Verificare
Get-ScheduledTask -TaskPath "\Monitoring\" | Format-Table TaskName, State
```

### Alerting via Webhook (Teams / Slack)

```powershell
# Funzione per inviare alert a Microsoft Teams tramite webhook
function Send-TeamsAlert {
    param(
        [string]$WebhookUri,
        [string]$Server,
        [string]$Metric,
        [double]$Value,
        [string]$Severity  # OK, WARNING, CRITICAL
    )

    $color = switch ($Severity) {
        "CRITICAL" { "FF0000" }
        "WARNING"  { "FFC107" }
        default    { "00FF00" }
    }

    $body = @{
        "@type"      = "MessageCard"
        "@context"   = "http://schema.org/extensions"
        themeColor   = $color
        summary      = "[$Severity] $Server — $Metric"
        sections     = @(
            @{
                activityTitle = "Monitoraggio Infrastruttura"
                facts = @(
                    @{ name = "Server"; value = $Server }
                    @{ name = "Metrica"; value = $Metric }
                    @{ name = "Valore"; value = "$Value" }
                    @{ name = "Severita`"; value = $Severity }
                    @{ name = "Timestamp"; value = (Get-Date -Format 'o') }
                )
            }
        )
    } | ConvertTo-Json -Depth 5

    Invoke-RestMethod -Uri $WebhookUri -Method Post -Body $body `
        -ContentType "application/json; charset=utf-8"
}

# Utilizzo nel loop di monitoraggio:
# $webhookUri = $env:TEAMS_WEBHOOK_URI   # Mai hardcodare nel codice!
# if ($cpuAvg -ge 90) {
#     Send-TeamsAlert -WebhookUri $webhookUri -Server $server `
#         -Metric "CPU" -Value $cpuAvg -Severity "CRITICAL"
# }
```

---

## Troubleshooting — 20+ Scenari

### 1. CPU Alta Sostenuta

```powershell
# Sintomo: CPU > 85% per minuti/ore

# Passo 1: identificare il processo
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name, Id, CPU,
    @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}

# Passo 2: se e` un servizio (svchost.exe), identificare quale
Get-CimInstance Win32_Service | Where-Object ProcessId -eq <PID> |
    Select-Object Name, DisplayName

# Passo 3: verificare se e` processo legittimo (antivirus, backup, Windows Update)
Get-CimInstance Win32_Process -Filter "ProcessId=<PID>" | Select-Object CommandLine

# Passo 4: se il processo e` legittimo ma consuma troppo → limiti CPU
# (Process Lasso o SetPriority a BelowNormal)

# Passo 5: se e` un runaway process → terminate con cautela
Stop-Process -Id <PID> -Force
```

### 2. Memory Leak

```powershell
# Sintomo: memoria working set di un processo cresce nel tempo senza rilascio

# Passo 1: identificare il processo
Get-Process | Sort-Object WorkingSet64 -Descending |
    Select-Object -First 10 Name, Id,
        @{N='WS_MB';E={[math]::Round($_.WorkingSet64/1MB,1)}},
        @{N='Priv_MB';E={[math]::Round($_.PrivateMemorySize64/1MB,1)}},
        Handles

# Passo 2: monitorare crescita nel tempo
# (usare lo script memory trend nella sezione Get-Process)

# Passo 3: controllare handle count (handle leak spesso accompagna memory leak)
Get-Process | Where-Object Handles -gt 5000 | Sort-Object Handles -Descending

# Passo 4: per .NET app, verificare GC
Get-Counter '\\.NET CLR Memory(*)\# Bytes in all Heaps',
    '\\.NET CLR Memory(*)\Gen 2 Collections' -SampleInterval 10 -MaxSamples 3

# Passo 5: se e` un servizio → riavviare il servizio (workaround)
# Passo 6: se persiste → crash dump + WinDbg con !analyze e !heap
```

### 3. Disco I/O Lento

```powershell
# Sintomo: latenza disco alta, queue length > 2

# Passo 1: verificare quale disco
Get-Counter '\PhysicalDisk(*)\Avg. Disk sec/Read',
    '\PhysicalDisk(*)\Avg. Disk sec/Write',
    '\PhysicalDisk(*)\Current Disk Queue Length' -SampleInterval 2 -MaxSamples 5

# Passo 2: chi fa I/O → Resource Monitor → tab Disk
# Oppure:
Get-Counter '\Process(*)\IO Read Bytes/sec',
    '\Process(*)\IO Write Bytes/sec' -SampleInterval 5 -MaxSamples 1

# Passo 3: verificare spazio libero (< 10% degrada performance su HDD)
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
    Select-Object DeviceID, @{N='FreePercent';E={[math]::Round($_.FreeSpace/$_.Size*100,1)}}

# Passo 4: controllare frammentazione (solo HDD)
# Optimize-Volume -DriveLetter C -Analyze

# Passo 5: verificare salute disco
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, HealthStatus, OperationalStatus
```

### 4. Saturazione Rete

```powershell
# Sintomo: connessioni lente, timeout, throughput al limite della banda

# Passo 1: verificare utilizzo
Get-Counter '\Network Interface(*)\Bytes Total/sec',
    '\Network Interface(*)\Output Queue Length' -SampleInterval 2 -MaxSamples 5

# Passo 2: chi consuma banda → Resource Monitor → tab Network

# Passo 3: verificare errori di rete
Get-NetAdapterStatistics | Select-Object Name, ReceivedBytes, SentBytes,
    InboundDiscards, OutboundDiscards, InboundErrors, OutboundErrors

# Passo 4: controllare connessioni TCP
Get-NetTCPConnection | Group-Object State | Select-Object Count, Name | Sort-Object Count -Desc

# Passo 5: se molte TIME_WAIT → possibile connection leak dell'applicazione
Get-NetTCPConnection -State TimeWait | Measure-Object

# Passo 6: packet capture per analisi dettagliata
pktmon start -c --comp all -l real-time
# oppure: netsh trace start capture=yes tracefile=C:\Temp\nettrace.etl
```

### 5. Servizio in Crash Loop

```powershell
# Sintomo: servizio si ferma e riavvia ripetutamente

# Passo 1: identificare il servizio
Get-WinEvent -FilterHashtable @{LogName='System'; Id=7034,7031} -MaxEvents 20 |
    Select-Object TimeCreated, @{N='Service';E={$_.Properties[0].Value}}, Message

# Passo 2: verificare recovery actions
sc.exe qfailure <ServiceName>

# Passo 3: controllare Event Log Application per errori correlati
Get-WinEvent -FilterHashtable @{LogName='Application'; Level=1,2;
    StartTime=(Get-Date).AddHours(-1)}

# Passo 4: verificare dipendenze del servizio
sc.exe qc <ServiceName>
sc.exe enumdepend <ServiceName>

# Passo 5: controllare risorse (il servizio potrebbe crashare per OOM)
# Passo 6: crash dump del servizio per debug
```

### 6. Spazio Disco in Esaurimento

```powershell
# Passo 1: situazione corrente
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
    Format-Table DeviceID,
        @{N='Total GB';E={[math]::Round($_.Size/1GB,1)}},
        @{N='Free GB';E={[math]::Round($_.FreeSpace/1GB,1)}},
        @{N='Free %';E={[math]::Round($_.FreeSpace/$_.Size*100,1)}}

# Passo 2: cartelle piu` grandi
Get-ChildItem C:\ -Directory -ErrorAction SilentlyContinue |
    ForEach-Object {
        [PSCustomObject]@{
            Path = $_.FullName
            SizeGB = [math]::Round((Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue |
                Measure-Object -Property Length -Sum).Sum / 1GB, 2)
        }
    } | Sort-Object SizeGB -Descending | Select-Object -First 10

# Passo 3: pulizia rapida
# - Cleanmgr (Pulizia disco)
# - Pulire C:\Windows\Temp e C:\Users\*\AppData\Local\Temp
# - Pulire C:\Windows\SoftwareDistribution\Download
# - Rimuovere crash dump vecchi: C:\Windows\Minidump e C:\Windows\MEMORY.DMP
# - DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase

# Passo 4: file piu` grandi
Get-ChildItem C:\ -Recurse -File -ErrorAction SilentlyContinue |
    Sort-Object Length -Descending |
    Select-Object -First 20 @{N='SizeMB';E={[math]::Round($_.Length/1MB,1)}}, FullName
```

### 7. Boot Lento

```powershell
# Passo 1: misurare Last BIOS Time (Task Manager → Startup)
# Passo 2: verificare programmi in avvio
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location

# Passo 3: verificare servizi con avvio automatico (molti servizi = boot lento)
Get-Service | Where-Object StartType -eq 'Automatic' | Measure-Object
Get-Service | Where-Object StartType -eq 'Automatic' |
    Select-Object Name, DisplayName, Status | Sort-Object Name

# Passo 4: Event Log per errori durante boot
Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2,3;
    StartTime=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime} |
    Select-Object TimeCreated, Id, ProviderName, LevelDisplayName, Message

# Passo 5: driver lenti
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-Kernel-Boot'} -MaxEvents 10
```

### 8. Blue Screen (BSOD)

```powershell
# Passo 1: controllare minidump
Get-ChildItem C:\Windows\Minidump -ErrorAction SilentlyContinue

# Passo 2: Event Log per BugCheck
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-WER-SystemErrorReporting'} -MaxEvents 5

# Passo 3: Event ID 41 (Kernel-Power) = riavvio imprevisto
Get-WinEvent -FilterHashtable @{LogName='System'; Id=41} -MaxEvents 10 |
    Select-Object TimeCreated, Message

# Passo 4: analizzare con WinDbg
# windbg -z C:\Windows\Minidump\MMDDYY-XXXXX-01.dmp
# !analyze -v

# Passo 5: cause comuni
# - Driver difettoso (aggiornare o disabilitare)
# - RAM difettosa (mdsched.exe o memtest86)
# - Disco corrotto (chkdsk)
# - Surriscaldamento (controllare temperature)
```

### 9. Evento "Event Log Pieno" (ID 1104)

```powershell
# Passo 1: aumentare dimensione
wevtutil sl Security /ms:4294967296    # 4 GB
wevtutil sl System /ms:1073741824     # 1 GB
wevtutil sl Application /ms:1073741824

# Passo 2: configurare retention
# "Overwrite events as needed" (default, consigliato per produzione)
# "Archive the log when full" (per ambienti con requisiti compliance)
wevtutil sl Security /rt:false        # false = overwrite quando pieno

# Passo 3: archiviazione automatica (scheduled task)
# Creare task che esporta e pulisce periodicamente
```

### 10. Performance Post-Aggiornamento

```powershell
# Passo 1: confrontare contatori pre/post
# (usare la funzione Compare-Baselines descritta sopra)

# Passo 2: servizi nuovi
Get-Service | Where-Object Status -eq Running | Sort-Object Name

# Passo 3: task scheduler — nuovi task
Get-ScheduledTask | Where-Object State -eq 'Ready' |
    Where-Object TaskPath -notlike '\Microsoft\*' |
    Select-Object TaskName, TaskPath, State

# Passo 4: hotfix recenti
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10

# Passo 5: se necessario → rollback
# wusa /uninstall /kb:NNNNNNN /quiet /norestart
```

### 11. WMI Corrotto

```powershell
# Passo 1: verificare
winmgmt /verifyrepository

# Passo 2: tentare salvataggio (prima scelta)
winmgmt /salvagerepository

# Passo 3: reset completo (ultimo resort — perde configurazioni WMI custom)
winmgmt /resetrepository

# Passo 4: verificare che funzioni
Get-CimInstance Win32_OperatingSystem
```

### 12. Processo con Handle Leak

```powershell
# Sintomo: handle count di un processo cresce indefinitamente

# Passo 1: identificare
Get-Process | Where-Object Handles -gt 10000 |
    Select-Object Name, Id, Handles,
        @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}

# Passo 2: monitorare crescita
Get-Counter '\Process(<ProcessName>)\Handle Count' -SampleInterval 60 -MaxSamples 60

# Passo 3: tipo di handle (richiede handle.exe di Sysinternals)
# handle.exe -p <PID> | Group-Object {$_ -replace '\s+.*',''} | Sort-Object Count -Desc

# Passo 4: workaround temporaneo → riavvio periodico servizio
# Passo 5: fix permanente → analisi con Process Monitor (procmon)
```

### 13. Connessioni TCP in TIME_WAIT

```powershell
# Sintomo: troppe connessioni in TIME_WAIT, esaurimento porte

# Passo 1: contare
Get-NetTCPConnection | Group-Object State | Sort-Object Count -Descending

# Passo 2: identificare applicazione
Get-NetTCPConnection -State TimeWait |
    Group-Object OwningProcess |
    Sort-Object Count -Descending |
    Select-Object -First 5 Count, @{N='Process';E={
        (Get-Process -Id $_.Name -ErrorAction SilentlyContinue).Name
    }}

# Passo 3: se necessario, ridurre TIME_WAIT timeout (default 120s)
# HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters
# TcpTimedWaitDelay (DWORD) = 30 (secondi, minimo consigliato)

# Passo 4: aumentare range porte effimere
# netsh int ipv4 set dynamicport tcp start=10000 num=55536
```

### 14. DNS Lento

```powershell
# Passo 1: misurare latenza DNS
Resolve-DnsName google.com | Select-Object Name, Type, TTL, IPAddress
Measure-Command { Resolve-DnsName google.com }

# Passo 2: verificare server DNS configurati
Get-DnsClientServerAddress -AddressFamily IPv4

# Passo 3: controllare cache DNS locale
Get-DnsClientCache | Select-Object Entry, Data, TimeToLive

# Passo 4: svuotare cache se corrotta
Clear-DnsClientCache

# Passo 5: test con nslookup su server specifici
nslookup google.com 8.8.8.8
nslookup google.com 1.1.1.1
```

### 15. Pagefile Eccessivo

```powershell
# Passo 1: verificare utilizzo pagefile
Get-Counter '\Paging File(_Total)\% Usage' -SampleInterval 2 -MaxSamples 3

# Passo 2: se > 50% → memoria fisica insufficiente
Get-CimInstance Win32_OperatingSystem |
    Select-Object TotalVisibleMemorySize, FreePhysicalMemory,
        TotalVirtualMemorySize, FreeVirtualMemory

# Passo 3: trovare i consumatori di memoria
Get-Process | Sort-Object WorkingSet64 -Descending |
    Select-Object -First 10 Name, @{N='WS_MB';E={[math]::Round($_.WorkingSet64/1MB)}}

# Passo 4: soluzione → aggiungere RAM o ridurre workload
```

### 16. Antivirus che Rallenta

```powershell
# Sintomo: CPU alta da MsMpEng.exe (Windows Defender) o altro AV

# Passo 1: verificare
Get-Process MsMpEng | Select-Object CPU, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}}

# Passo 2: aggiungere esclusioni per directory con alto I/O
# (SQL data files, IIS content, build output, ecc.)
Add-MpPreference -ExclusionPath "D:\SQLData"
Add-MpPreference -ExclusionPath "D:\IIS\wwwroot"
Add-MpPreference -ExclusionProcess "sqlservr.exe"

# Passo 3: schedulare scan completo in orari non lavorativi
Set-MpPreference -ScanScheduleQuickScanTime 03:00:00
```

### 17. RDP Lento

```powershell
# Passo 1: verificare risorse sul server RDS
Get-Counter '\Processor(_Total)\% Processor Time',
    '\Memory\Available MBytes' -SampleInterval 2 -MaxSamples 3

# Passo 2: sessioni attive
quser

# Passo 3: profili utente grandi → caricamento lento
Get-ChildItem C:\Users -Directory |
    ForEach-Object {
        [PSCustomObject]@{
            User = $_.Name
            SizeMB = [math]::Round((Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue |
                Measure-Object Length -Sum).Sum / 1MB, 0)
        }
    } | Sort-Object SizeMB -Descending

# Passo 4: controllare latenza di rete
Test-NetConnection -ComputerName <RDPServer> -Port 3389 |
    Select-Object TcpTestSucceeded, PingReplyDetails
```

### 18. Scheduled Task Fallisce

```powershell
# Passo 1: verificare history
Get-ScheduledTask -TaskName "TaskName" | Get-ScheduledTaskInfo

# Passo 2: ultimo risultato
Get-ScheduledTask | Where-Object State -ne 'Disabled' |
    Get-ScheduledTaskInfo |
    Where-Object LastTaskResult -ne 0 |
    Select-Object TaskName, LastRunTime, LastTaskResult

# Passo 3: errori comuni
# 0x1 = Incorrect function (script non trovato o errore)
# 0x41301 = Task is currently running
# 0x41303 = Task has not yet run
# 0x80070005 = Access Denied (permessi insufficienti)
# 0x800710E0 = Operator or user has refused the request

# Passo 4: Event Log TaskScheduler
Get-WinEvent -FilterHashtable @{
    LogName='Microsoft-Windows-TaskScheduler/Operational'; Level=2,3
} -MaxEvents 20
```

### 19. Windows Update Bloccato

```powershell
# Passo 1: verificare stato
Get-WindowsUpdateLog    # genera log leggibile da ETL

# Passo 2: servizi necessari
Get-Service wuauserv, bits, cryptsvc | Select-Object Name, Status, StartType

# Passo 3: pulire cache update
Stop-Service wuauserv, bits
Remove-Item C:\Windows\SoftwareDistribution\* -Recurse -Force
Start-Service wuauserv, bits

# Passo 4: DISM repair
DISM /Online /Cleanup-Image /ScanHealth
DISM /Online /Cleanup-Image /RestoreHealth

# Passo 5: SFC
sfc /scannow
```

### 20. Corruzione File System

```powershell
# Passo 1: verificare salute disco
Get-PhysicalDisk | Select-Object FriendlyName, HealthStatus, OperationalStatus

# Passo 2: errori Event Log
Get-WinEvent -FilterHashtable @{LogName='System'; Id=55,153,129} -MaxEvents 10

# Passo 3: chkdsk (schedule al prossimo riavvio se volume di sistema)
# chkdsk C: /F /R /X   # attenzione: richiede riavvio per volume di sistema

# Passo 4: DISM per componenti Windows
DISM /Online /Cleanup-Image /CheckHealth
DISM /Online /Cleanup-Image /RestoreHealth

# Passo 5: sfc per file di sistema
sfc /scannow
```

### 21. Processo Zombie / Orfano

```powershell
# Sintomo: processo che non risponde, non puo` essere terminato dal Task Manager

# Passo 1: tentare terminazione con PID
Stop-Process -Id <PID> -Force

# Passo 2: se non funziona, controllare se e` un processo kernel
Get-CimInstance Win32_Process -Filter "ProcessId=<PID>" |
    Select-Object Name, CommandLine, KernelModeTime, UserModeTime

# Passo 3: controllare se ha thread in stato di attesa
# (richiede Process Explorer di Sysinternals)

# Passo 4: se il processo ha file aperti che bloccano altri processi
# handle.exe -p <PID>   (Sysinternals)

# Passo 5: ultimo resort → riavvio server
```

### 22. Certificate Scaduto

```powershell
# Passo 1: controllare certificati in scadenza
Get-ChildItem Cert:\LocalMachine\My -ExpiringInDays 30 |
    Select-Object Subject, Thumbprint, NotAfter

# Passo 2: tutti i certificati con data scadenza
Get-ChildItem Cert:\LocalMachine\My |
    Where-Object NotAfter -lt (Get-Date).AddDays(60) |
    Select-Object Subject, Thumbprint, NotAfter,
        @{N='DaysLeft';E={($_.NotAfter - (Get-Date)).Days}}

# Passo 3: IIS binding con certificato scaduto
Get-ChildItem IIS:\SslBindings -ErrorAction SilentlyContinue |
    ForEach-Object {
        $cert = Get-ChildItem "Cert:\LocalMachine\My\$($_.Thumbprint)" -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            Binding = "$($_.IPAddress):$($_.Port)"
            Subject = $cert.Subject
            Expires = $cert.NotAfter
        }
    }
```

---

## Best Practices

1. **Stabilire baseline**: raccogliere dati performance per 1-2 settimane in condizioni normali. Senza baseline, non si può dire se un valore è "normale" o anomalo

2. **Monitoraggio proattivo**: Data Collector Set schedulati, alert su soglie, review settimanale

3. **Dimensionare i log**: Event Log di default è troppo piccolo. Security: almeno 1 GB, System/Application: almeno 256 MB

4. **Windows Admin Center**: installare WAC come console centralizzata per tutti i server

5. **Centralizzare eventi**: Windows Event Forwarding (WEF) per raccogliere eventi di sicurezza da tutti i server

6. **Documentare ogni intervento**: data, problema, dati raccolti, causa identificata, azione correttiva

7. **Sysmon su ogni server**: installare con configurazione SwiftOnSecurity o equivalente per visibilita` su processi, rete e file

8. **Contatori minimi**: monitorare sempre almeno CPU %, Available MBytes, Disk Queue Length, Network Output Queue Length

9. **Alert intelligenti**: non generare alert su ogni anomalia. Usare soglie basate sulla baseline, non su valori assoluti generici

10. **Capacity planning trimestrale**: rivedere trend di crescita ogni trimestre, proiettare esaurimento risorse

11. **Separare dati e OS**: disco separato per dati applicativi. Monitorare separatamente

12. **Retention policy**: definire per quanto tempo conservare dati di performance e log. Minimo 90 giorni per troubleshooting, 1 anno per trending

13. **Automazione**: script di health check eseguiti quotidianamente via Task Scheduler con report via email

14. **Multi-tool approach**: nessuno strumento copre tutto. Combinare PerfMon + Sysmon + WEF + strumento esterno (Prometheus/Zabbix/SCOM)

15. **Test before production**: ogni nuova regola di monitoraggio va testata in ambiente di test prima di applicarla in produzione

---

## FAQ — Domande Frequenti

**D1: Qual e` la differenza tra Performance Monitor e Resource Monitor?**
PerfMon raccoglie contatori con campionamento configurabile, supporta Data Collector Set, alert, report storici. E` lo strumento per analisi a lungo termine e baseline. Resource Monitor mostra dati in tempo reale con dettaglio per-processo su CPU, memoria, disco e rete. E` lo strumento per diagnosi immediata di "chi sta consumando cosa adesso".

**D2: Get-WmiObject o Get-CimInstance?**
Sempre `Get-CimInstance`. `Get-WmiObject` usa DCOM (porte dinamiche, problemi firewall), e` deprecato, ed e` stato rimosso in PowerShell 7+. `Get-CimInstance` usa WinRM (porta 5985), supporta sessioni riutilizzabili, e funziona cross-platform.

**D3: Quanto spazio allocare per i log di Security?**
Minimo 1 GB per un server standard. Per Domain Controller con molti utenti o server con audit dettagliato, 4 GB. Per server con compliance requirements (PCI-DSS, SOX), considerare log forwarding verso SIEM con retention piu` lunga.

**D4: Come faccio a sapere se la CPU alta e` normale o problematica?**
Confrontare con la baseline. Se la baseline mostra CPU avg 40% e ora e` al 85%, c'e` un problema. Se la baseline mostra CPU avg 75% durante orario lavorativo, il 85% potrebbe essere un normale picco. Il valore assoluto da solo non basta — serve contesto.

**D5: Pages/sec alto significa sempre un problema?**
No. `Pages/sec` include sia hard page fault (disco → RAM) che soft page fault (redistribuzione pagine in RAM). Solo gli hard page fault indicano carenza di memoria. Verificare anche `Memory\Available MBytes` e `Hard Faults/sec` in Resource Monitor.

**D6: Processor Queue Length: quando preoccuparsi?**
Regola pratica: preoccuparsi quando supera 2x il numero di core logici in modo sostenuto. Un server con 8 core logici puo` tollerare un queue length occasionale di 16, ma se resta sopra 16 per minuti, i processi stanno aspettando troppo per la CPU.

**D7: Sysmon influisce sulle performance del server?**
Con una configurazione ragionevole (come SwiftOnSecurity), l'impatto e` trascurabile: < 1% CPU, < 50 MB RAM. Senza configurazione (log tutto), il volume di eventi puo` diventare enorme e impattare I/O disco. Usare sempre un file di configurazione con esclusioni.

**D8: WEF o agent SIEM (Splunk/Elastic)?**
WEF e` nativo, gratuito, e non richiede agent. Ideale per raccogliere eventi Windows su un collector centrale. Agent SIEM e` necessario quando si vuole: parsing avanzato, correlazione cross-platform, dashboard personalizzate, retention a lungo termine, alerting complesso. I due non si escludono: WEF puo` alimentare il SIEM.

**D9: Prometheus o Zabbix per server Windows?**
Prometheus + Grafana e` eccellente per metriche numeriche, grafici personalizzati e alerting basato su query (PromQL). Zabbix e` piu` completo out-of-the-box per Windows: template predefiniti, LLD, trigger, escalation. Prometheus richiede piu` configurazione iniziale ma e` piu` flessibile. In ambienti misti Linux/Windows, Prometheus e` spesso gia` presente.

**D10: Come monitorare macchine virtuali Hyper-V?**
Usare i contatori PerfMon specifici: `\Hyper-V Hypervisor Virtual Processor(*)\% Guest Run Time`, `\Hyper-V Dynamic Memory VM(*)\Current Pressure`. Nel guest, monitorare normalmente. Nell'host, monitorare sia le risorse fisiche che l'overhead dell'hypervisor.

**D11: Il Pool Nonpaged Bytes e` alto. Cosa significa?**
Pool Nonpaged e` memoria kernel che non puo` essere swappata su disco. Valori alti (> 200-400 MB) indicano un driver o un componente kernel che consuma memoria. Usare `poolmon.exe` (Windows SDK) per identificare il tag del pool che cresce. Cause comuni: driver di rete, filtro antivirus, driver storage.

**D12: Come impostare il monitoraggio su un server appena installato?**
1. Installare Sysmon con configurazione community. 2. Dimensionare i log (Security 1 GB+, System/Application 256 MB+). 3. Creare Data Collector Set baseline per 2 settimane. 4. Installare agent di monitoraggio (Zabbix/Prometheus exporter). 5. Configurare WEF verso il collector aziendale. 6. Documentare la configurazione.

**D13: Posso usare Performance Monitor su server remoti?**
Si`. PerfMon → tasto destro su "Performance Monitor" → "Connect to another computer". Oppure via PowerShell: `Get-Counter -ComputerName SRV01 '\Processor(_Total)\% Processor Time'`. Requisiti: WinRM o RPC abilitato, permessi amministrativi sul server remoto.

**D14: Come distinguere un problema di disco da un problema di memoria?**
Se `Avg. Disk Queue Length` e` alto E `Available MBytes` e` basso E `Pages/sec` e` alto → il disco e` lento PERCHE` il sistema sta facendo paging (problema di memoria). Se `Avg. Disk Queue Length` e` alto MA `Available MBytes` e` OK → il disco e` il collo di bottiglia (troppo I/O applicativo, disco lento, o frammentazione).

**D15: Qual e` il costo delle diverse soluzioni di monitoraggio?**
Task Manager, PerfMon, Resource Monitor, Event Viewer, WEF: gratuiti (inclusi in Windows). Sysmon: gratuito (Sysinternals). WAC: gratuito. Prometheus + Grafana: gratuiti (open source), costo = infrastruttura + tempo di configurazione. Zabbix: gratuito (open source), costo = infrastruttura + tempo. SCOM: richiede licenze System Center (~$1300-3600 per server, verifica pricing corrente). Soluzioni SaaS (Datadog, Azure Monitor): costo variabile per host/mese.

**D16: Come automatizzare la generazione di report di performance?**
Creare uno script PowerShell che: 1. Legge i CSV dei Data Collector Set. 2. Calcola statistiche (funzione Get-BaselineStats). 3. Compara con baseline precedente (funzione Compare-Baselines). 4. Genera un report HTML con ConvertTo-Html. 5. Invia via email con Send-MailMessage. 6. Schedulare con Task Scheduler (settimanale).

---

## Checklist Deployment Monitoraggio

### Pre-Deployment

```
[ ] Inventario server: lista completa con ruolo, OS version, risorse
[ ] Definire SLA/SLO per ogni servizio (tempo di risposta, uptime target)
[ ] Scegliere stack di monitoraggio (nativo + esterno)
[ ] Definire retention policy per log e metriche
[ ] Pianificare risorse per collector/SIEM (CPU, RAM, disco)
[ ] Definire matrice di escalation (chi riceve quale alert)
```

### Configurazione Base (ogni server)

```
[ ] Dimensionare Event Log:
    [ ] Security: >= 1 GB (DC: >= 4 GB)
    [ ] System: >= 256 MB
    [ ] Application: >= 256 MB
[ ] Installare Sysmon con configurazione community
[ ] Configurare WinRM: winrm quickconfig
[ ] Configurare WEF source (GPO con target Subscription Manager)
[ ] Creare Data Collector Set baseline (CPU, Memory, Disk, Network)
    [ ] Avviare raccolta baseline (minimo 2 settimane)
[ ] Installare agent monitoraggio esterno (Zabbix agent / windows_exporter)
[ ] Configurare firewall:
    [ ] WinRM in ingresso (5985/5986) dal collector
    [ ] Agent monitoring (10050 Zabbix / 9182 Prometheus) dal server
[ ] Verificare NTP sincronizzato (per correlazione eventi tra server)
```

### Configurazione Collector / Server Centrale

```
[ ] WEF Collector:
    [ ] wecutil qc (abilitare servizio)
    [ ] Creare subscription per eventi critici di sicurezza
    [ ] Creare subscription per eventi operativi (servizi, riavvii)
    [ ] Dimensionare log ForwardedEvents (>= 4 GB)
    [ ] Configurare archiviazione automatica
[ ] Zabbix Server / Prometheus:
    [ ] Aggiungere host con template appropriati
    [ ] Configurare trigger e soglie basate su baseline
    [ ] Configurare notifiche (email, Slack, Teams)
    [ ] Creare dashboard per ruoli server
[ ] SIEM (se presente):
    [ ] Configurare parsing log Windows
    [ ] Creare regole di correlazione
    [ ] Configurare alert per scenari di sicurezza
```

### Post-Deployment

```
[ ] Verificare ricezione eventi su collector WEF
[ ] Verificare metriche su Zabbix/Prometheus/SCOM
[ ] Generare report baseline dopo 2 settimane di raccolta
[ ] Documentare soglie e giustificazione
[ ] Test alert: simulare scenario (disco pieno, CPU alta) e verificare notifica
[ ] Formare il team sugli strumenti e sulle procedure di escalation
[ ] Schedulare review mensile degli alert (noise reduction)
[ ] Schedulare review trimestrale di capacity planning
[ ] Documentare procedura di troubleshooting per i 10 scenari piu` comuni
```

### Manutenzione Continua

```
[ ] Settimanale:
    [ ] Review alert non risolti
    [ ] Verificare che tutti gli agent siano attivi e riportano dati
[ ] Mensile:
    [ ] Confronto metriche con baseline
    [ ] Aggiornare esclusioni Sysmon se necessario
    [ ] Pulizia alert rumorosi (tuning soglie)
[ ] Trimestrale:
    [ ] Report capacity planning
    [ ] Aggiornare baseline se il workload e` cambiato
    [ ] Aggiornare Sysmon e configurazione
    [ ] Verificare retention e archiviazione log
[ ] Annuale:
    [ ] Review architettura monitoraggio completa
    [ ] Valutare nuovi strumenti/tecnologie
    [ ] Aggiornare documentazione e procedure
```

---

## Esercizi

1. Spiega la differenza tra un contatore di performance e un evento del log di sistema: quando useresti l'uno piuttosto che l'altro per diagnosticare un problema di lentezza?
2. **Lab:** Crea un Data Collector Set in PerfMon che raccolga CPU (% Processor Time), RAM (Available MBytes), disco (Avg. Disk Queue Length) e rete (Bytes Total/sec) per 30 minuti. Analizza il report generato e identifica eventuali colli di bottiglia.
3. Un server web mostra latenze elevate durante l'orario lavorativo ma i contatori CPU e RAM sono normali. Descrivi un piano di troubleshooting sistematico usando gli strumenti trattati nel modulo.
4. Progetta un'architettura di monitoraggio WEF/WEC per un dominio con 500 client e 20 server: quanti collector, quali subscription, quale retention policy? Motiva le scelte.

## Auto-valutazione

<details><summary>1. Che differenza c'e tra Performance Monitor e Resource Monitor?</summary>
PerfMon e uno strumento di raccolta dati a lungo termine con Data Collector Set, report e contatori configurabili. Resource Monitor mostra lo stato in tempo reale di CPU, memoria, disco e rete con granularita per processo. PerfMon e per il trending e il capacity planning, Resource Monitor per il troubleshooting immediato — vedi sezioni corrispondenti.
</details>

<details><summary>2. A cosa serve un Data Collector Set?</summary>
Raccoglie contatori di performance, eventi ETW e configurazioni di sistema su schedule configurabile. I dati raccolti vengono salvati come file .blg/.csv e possono essere analizzati successivamente per creare baseline e confronti — vedi sezione PerfMon.
</details>

<details><summary>3. Come si centralizzano gli eventi con WEF/WEC?</summary>
Windows Event Forwarding (WEF) configura i client come event source; Windows Event Collector (WEC) raccoglie gli eventi su un server centrale. Le subscription definiscono quali eventi raccogliere. Si configura via GPO (source-initiated) o via `wecutil` (collector-initiated) — vedi sezione WEF.
</details>

<details><summary>4. Cosa monitora Sysmon che Event Viewer standard non mostra?</summary>
Sysmon registra creazione processi con hash e command line completa, connessioni di rete per processo, modifiche al registro, caricamento driver e DLL, accesso a file e named pipe. Essenziale per la security forensics — vedi sezione Sysmon.
</details>

<details><summary>5. Qual e la differenza tra WMI e CIM?</summary>
WMI (Windows Management Instrumentation) usa DCOM/RPC, e legacy. CIM (Common Information Model) usa WS-Man/WinRM, e piu moderno, firewall-friendly e cross-platform. I cmdlet `Get-CimInstance` sostituiscono `Get-WmiObject` — vedi sezione WMI e CIM.
</details>

<details><summary>6. Come si usa Get-Counter per il monitoraggio via script?</summary>
`Get-Counter -Counter "\Processor(_Total)\% Processor Time" -SampleInterval 5 -MaxSamples 60` raccoglie 60 campioni ogni 5 secondi. L'output puo essere esportato in CSV o usato per trigger automatici con logica condizionale — vedi sezione Monitoraggio con PowerShell.
</details>

<details><summary>7. Cosa significa "baseline" nel contesto del performance monitoring?</summary>
Una baseline e la raccolta di metriche di riferimento durante il funzionamento normale del sistema. Serve come confronto per identificare deviazioni, pianificare la capacita e giustificare upgrade hardware — vedi Idee guida e sezione Capacity Planning.
</details>

## Letture primarie consigliate

- Microsoft Learn — Performance monitoring tools for Windows Server: <https://learn.microsoft.com/windows-server/administration/performance-tuning/> (consultato: 2026-05-23)
- Microsoft Learn — Windows Event Forwarding: <https://learn.microsoft.com/windows/security/operating-system-security/device-management/windows-event-forwarding/> (consultato: 2026-05-23)
- Microsoft Sysinternals — Sysmon: <https://learn.microsoft.com/sysinternals/downloads/sysmon> (consultato: 2026-05-23)
- Microsoft Learn — Windows Admin Center: <https://learn.microsoft.com/windows-server/manage/windows-admin-center/overview> (consultato: 2026-05-23)

## Collegamenti incrociati

- [Sicurezza Windows](05-sicurezza-windows.md) — audit policy, log di sicurezza, correlazione eventi
- [PowerShell](02-powershell.md) — cmdlet Get-Counter, Get-WinEvent, automazione monitoraggio
- [Troubleshooting](19-troubleshooting.md) — analisi problemi, diagnosi guidata dai dati
- [Windows Defender e Endpoint Security](24-windows-defender-endpoint-security.md) — integrazione Sysmon con EDR
- [Ruoli Server](03-ruoli-server.md) — contatori specifici per ruolo (DNS, DHCP, file server)

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| PerfMon | Performance Monitor: strumento Windows per la raccolta e analisi di contatori di performance |
| Data Collector Set | Insieme configurato di contatori, eventi e dati di configurazione da raccogliere su schedule |
| Baseline | Raccolta di metriche di riferimento durante il funzionamento normale, usata come confronto |
| WEF | Windows Event Forwarding: meccanismo per inoltrare eventi dai client a un collector centrale |
| WEC | Windows Event Collector: servizio che riceve e archivia eventi inoltrati dai client WEF |
| Sysmon | System Monitor: driver Sysinternals che registra attivita dettagliata su processi, rete e registro |
| ETW | Event Tracing for Windows: infrastruttura kernel-level per il tracing ad alte prestazioni |
| WMI | Windows Management Instrumentation: interfaccia legacy per la gestione e il monitoraggio di Windows |
| CIM | Common Information Model: standard moderno per la gestione dei sistemi, usa WS-Man/WinRM |
| SCOM | System Center Operations Manager: piattaforma enterprise per il monitoraggio su scala |
