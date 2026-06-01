# Monitoraggio e Gestione Incidenti — Guida Completa

> **Modulo 07** · **Tempo:** 90 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **Three pillars: traces + logs + metrics, correlated by trace_id.**
2. **Multi-window/multi-burn-rate alert > soglia statica.** Riduce alert fatigue.
3. **Incident commander e role per durata incident, non gerarchia permanente.**
4. **War room + comms updates ogni 30min during incident.**


## Indice

1. [Panoramica](#panoramica)
2. [Sistemi di Monitoraggio](#sistemi-di-monitoraggio)
   - [Panoramica Strumenti](#panoramica-strumenti)
   - [Zabbix](#zabbix)
   - [Prometheus e Grafana](#prometheus-e-grafana)
   - [SNMP Monitoring](#snmp-monitoring)
   - [Log Management Centralizzato](#log-management-centralizzato)
   - [Monitoraggio Sintetico](#monitoraggio-sintetico)
3. [Gestione Alert](#gestione-alert)
   - [Configurazione Soglie](#configurazione-soglie)
   - [Alert Routing e Notifiche](#alert-routing-e-notifiche)
   - [Alertmanager Configuration](#alertmanager-configuration)
4. [Gestione Incidenti](#gestione-incidenti)
   - [Processo Incident Management](#processo-incident-management)
   - [War Room / Incident Response](#war-room--incident-response)
   - [Incident Communication](#incident-communication)
   - [Post-Mortem / Post-Incident Review](#post-mortem--post-incident-review)
5. [Performance Monitoring](#performance-monitoring)
   - [Capacity Planning](#capacity-planning)
   - [Application Performance](#application-performance)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Panoramica

Il monitoraggio dell'infrastruttura IT rappresenta il pilastro fondamentale su cui si costruisce ogni strategia di manutenzione proattiva. Senza un sistema di monitoraggio adeguato, il team IT opera alla cieca, reagendo ai problemi soltanto quando gli utenti segnalano disservizi, quando i sistemi sono gia degradati o, nel peggiore dei casi, quando si verifica un'interruzione completa del servizio.

Il concetto chiave alla base del monitoraggio moderno e il passaggio da un approccio **reattivo** a uno **proattivo**: non si attende che il disco si riempia, ma si interviene quando l'utilizzo supera il 75%; non si aspetta che il server diventi irraggiungibile, ma si rileva il degrado delle prestazioni prima che impatti gli utenti finali. Questo cambio di paradigma riduce drasticamente i tempi di inattivita (downtime), migliora la soddisfazione degli utenti e consente al team IT di pianificare interventi durante finestre di manutenzione controllate anziche gestire emergenze.

Un sistema di monitoraggio completo copre diversi livelli dell'infrastruttura:

- **Infrastruttura fisica e virtuale**: server, switch, router, firewall, storage, hypervisor
- **Sistemi operativi**: CPU, memoria, disco, rete, processi, servizi
- **Servizi e applicazioni**: web server, database, code di messaggi, API
- **Rete**: latenza, throughput, packet loss, disponibilita delle interfacce
- **Sicurezza**: tentativi di accesso non autorizzato, eventi anomali, compliance
- **Log**: raccolta, aggregazione, analisi e correlazione dei log da tutti i sistemi
- **Esperienza utente**: tempi di risposta percepiti, disponibilita degli endpoint

La gestione degli incidenti, strettamente collegata al monitoraggio, definisce i processi strutturati attraverso i quali un'organizzazione rileva, classifica, assegna, risolve e documenta le interruzioni di servizio e le degradazioni delle prestazioni. Un processo maturo di incident management riduce il tempo medio di risoluzione (MTTR), migliora la comunicazione durante le crisi e alimenta un ciclo di miglioramento continuo attraverso le analisi post-mortem.

---

## Sistemi di Monitoraggio

### Panoramica Strumenti

La scelta dello strumento di monitoraggio dipende da numerosi fattori: dimensione dell'infrastruttura, budget, competenze del team, tipologia dei sistemi da monitorare, requisiti di scalabilita e integrazioni necessarie. La tabella seguente offre un confronto sintetico dei principali strumenti disponibili sul mercato.

| Strumento | Licenza | Modello | Punti di Forza | Limiti | Caso d'Uso Ideale |
|-----------|---------|---------|----------------|--------|-------------------|
| **Zabbix** | Open-source (GPLv2) | Agent-based + agentless | Completo, scalabile, template ricchi | Curva di apprendimento ripida, UI datata | Infrastrutture on-premise medio-grandi |
| **Prometheus + Grafana** | Open-source (Apache 2.0) | Pull-based, cloud-native | Eccellente per container/K8s, PromQL potente | Nessuno storage a lungo termine nativo | Ambienti cloud-native, Kubernetes |
| **Nagios/Icinga** | Open-source (GPL) | Plugin-based | Maturo, enorme ecosistema di plugin | Configurazione tramite file, scalabilita limitata | Infrastrutture tradizionali consolidate |
| **PRTG** | Commerciale | Sensor-based | Facile da usare, setup rapido | Costo elevato su larga scala (per-sensor) | PMI, team con risorse limitate |
| **Datadog** | SaaS commerciale | Agent + integrazioni | Integrazioni vastissime, AI/ML | Costo molto elevato, vendor lock-in | Enterprise multi-cloud |
| **New Relic** | SaaS commerciale | Agent + OpenTelemetry | APM eccellente, full-stack observability | Costo basato su ingestione dati | Focus su application performance |
| **Checkmk** | Open-source + Enterprise | Hybrid (agent + agentless) | Configurazione rapida, auto-discovery | Versione open limitata rispetto a Enterprise | Infrastrutture eterogenee |

Nella pratica, molte organizzazioni adottano una combinazione di strumenti: per esempio, Prometheus e Grafana per l'infrastruttura cloud-native e i container, Zabbix per i server fisici e gli apparati di rete, e uno stack ELK o Loki per la gestione centralizzata dei log. La chiave e costruire un ecosistema di monitoraggio coerente, evitando sovrapposizioni inutili e garantendo che tutti i livelli dell'infrastruttura siano coperti.

---

### Zabbix

Zabbix e una delle piattaforme di monitoraggio open-source piu complete e mature disponibili. Supporta il monitoraggio di server, macchine virtuali, apparati di rete, database, applicazioni e servizi cloud attraverso una combinazione di agent installati sui sistemi e protocolli agentless come SNMP, IPMI, JMX e HTTP.

#### Architettura

L'architettura di Zabbix si compone di tre elementi principali:

- **Zabbix Server**: il componente centrale che riceve i dati di monitoraggio, valuta i trigger, invia le notifiche e memorizza i dati nel database. Richiede un database backend (PostgreSQL o MySQL/MariaDB) e un web server per l'interfaccia utente.
- **Zabbix Proxy**: componente opzionale che opera come intermediario tra gli agent e il server. Indispensabile per il monitoraggio di siti remoti, reti con latenza elevata o infrastrutture distribuite. Il proxy raccoglie i dati localmente e li inoltra periodicamente al server, riducendo il carico di rete e garantendo la continuita del monitoraggio anche in caso di interruzioni temporanee della connettivita.
- **Zabbix Agent**: software leggero installato sugli host da monitorare. Disponibile in due varianti: l'agent classico (zabbix_agent) e il piu recente Agent 2 (zabbix_agent2), scritto in Go, che offre plugin nativi per il monitoraggio di Docker, MySQL, PostgreSQL, Redis e altri servizi senza necessita di script esterni.

#### Installazione e Setup Iniziale

L'installazione di Zabbix su un sistema Linux (Debian/Ubuntu) segue questi passaggi fondamentali:

```bash
# Aggiungere il repository Zabbix
wget https://repo.zabbix.com/zabbix/7.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_latest_7.0+ubuntu24.04_all.deb
sudo dpkg -i zabbix-release_latest_7.0+ubuntu24.04_all.deb
sudo apt update

# Installare server, frontend e agent
sudo apt install zabbix-server-pgsql zabbix-frontend-php php8.3-pgsql zabbix-apache-conf zabbix-sql-scripts zabbix-agent2

# Creare il database
sudo -u postgres createuser --pwprompt zabbix
sudo -u postgres createdb -O zabbix zabbix

# Importare lo schema iniziale
zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix

# Configurare la password del database in zabbix_server.conf
sudo sed -i 's/# DBPassword=/DBPassword=LA_TUA_PASSWORD/' /etc/zabbix/zabbix_server.conf

# Avviare i servizi
sudo systemctl enable --now zabbix-server zabbix-agent2 apache2
```

Dopo l'installazione, l'interfaccia web guida attraverso la configurazione iniziale: connessione al database, timezone, credenziali di accesso (default: Admin / zabbix).

#### Configurazione Host e Template

Ogni sistema monitorato viene aggiunto come **host** in Zabbix. Un host e definito da:

- **Nome**: identificativo univoco del sistema
- **Gruppi**: raggruppamento logico (es. "Server Linux", "Switch di rete", "Database")
- **Interfacce**: metodo di comunicazione (Agent, SNMP, JMX, IPMI) con indirizzo IP o DNS
- **Template**: collezione di item, trigger, grafici e regole di discovery associata all'host

I template sono il meccanismo piu potente di Zabbix: definiscono cosa monitorare e come reagire. Un singolo template puo contenere centinaia di metriche preconfigurate. I template chiave includono:

- **Linux by Zabbix agent**: CPU, memoria, disco, rete, processi, filesystem
- **Windows by Zabbix agent**: CPU, memoria, disco, servizi Windows, Event Log
- **Network Generic Device by SNMP**: interfacce, traffico, errori, stato operativo
- **VMware by HTTP**: hypervisor, datastore, macchine virtuali, performance
- **MySQL by Zabbix agent 2**: connessioni, query, buffer pool, replication
- **Docker by Zabbix agent 2**: container, immagini, volumi, risorse

#### Tipi di Item

Gli item definiscono le singole metriche raccolte. Zabbix supporta diversi tipi:

- **Zabbix Agent (attivo/passivo)**: l'agent raccoglie i dati localmente. In modalita attiva, l'agent invia i dati al server; in modalita passiva, il server interroga l'agent.
- **SNMP Agent**: raccoglie dati tramite protocollo SNMP, fondamentale per switch, router, stampanti, UPS e qualsiasi dispositivo che supporti SNMP.
- **JMX Agent**: monitoraggio di applicazioni Java (Tomcat, WildFly, Kafka) tramite Java Management Extensions.
- **HTTP Agent**: interroga endpoint HTTP/HTTPS, analizza risposte JSON o XML, verifica codici di stato e tempi di risposta.
- **Calculated Items**: metriche derivate calcolate a partire da altri item tramite formule.
- **External Check**: esecuzione di script esterni sul server Zabbix.

#### Trigger ed Espressioni

I trigger definiscono le condizioni che generano un alert. Utilizzano un linguaggio di espressioni che permette confronti complessi:

```
# CPU utilizzazione media superiore al 90% negli ultimi 5 minuti
avg(/Linux by Zabbix agent/system.cpu.util,5m) > 90

# Spazio disco sotto il 10% disponibile
last(/Linux by Zabbix agent/vfs.fs.pused[/]) > 90

# Host irraggiungibile da piu di 3 minuti
nodata(/Linux by Zabbix agent/agent.ping,3m) = 1

# Numero di processi zombie superiore a 5
last(/Linux by Zabbix agent/proc.num[,,zomb]) > 5
```

I livelli di severita in Zabbix sono sei: Not classified, Information, Warning, Average, High, Disaster. Ogni livello puo essere associato a azioni diverse: invio email per Warning, SMS per High, chiamata telefonica per Disaster.

#### Auto-Discovery

Zabbix offre due meccanismi di scoperta automatica:

- **Network Discovery**: scansione di range IP per individuare automaticamente nuovi dispositivi. Utilizza ping ICMP, controlli di porte TCP, query SNMP o verifiche dell'agent Zabbix.
- **Low-Level Discovery (LLD)**: scoperta automatica di entita all'interno di un host, come filesystem, interfacce di rete, istanze di database, container Docker. LLD crea automaticamente item, trigger e grafici per ogni entita scoperta.

#### Macro e Finestre di Manutenzione

Le **macro** permettono di parametrizzare i template: {$CPU_WARN_THRESHOLD} puo valere 80 per un server di produzione e 95 per un server di sviluppo, senza duplicare il template. Le macro possono essere definite a livello globale, di template o di singolo host.

Le **finestre di manutenzione** sopprimono la generazione di alert durante periodi pianificati. Si configurano specificando: periodo temporale, host o gruppi interessati, e se raccogliere comunque i dati (opzione consigliata per non perdere le metriche durante la manutenzione).

---

### Prometheus e Grafana

Prometheus e il sistema di monitoraggio e alerting di riferimento per gli ambienti cloud-native. Nato all'interno del progetto SoundCloud e successivamente donato alla Cloud Native Computing Foundation (CNCF), Prometheus utilizza un modello **pull-based**: il server interroga periodicamente gli endpoint (target) per raccogliere le metriche, anziche ricevere dati inviati dagli agenti.

#### Architettura

L'ecosistema Prometheus si compone di:

- **Prometheus Server**: componente centrale che esegue lo scraping delle metriche, le memorizza nel database time-series locale (TSDB) e valuta le regole di alerting. Ogni istanza Prometheus e autonoma e non richiede dipendenze esterne per funzionare.
- **Exporter**: programmi che espongono metriche in formato Prometheus su un endpoint HTTP (tipicamente `/metrics`). Esistono exporter per praticamente qualsiasi sistema: Node Exporter (Linux), Windows Exporter, mysqld_exporter, postgres_exporter, blackbox_exporter, snmp_exporter e centinaia di altri.
- **Alertmanager**: riceve gli alert generati da Prometheus, li raggruppa, deduplica e instrada verso i canali di notifica configurati (email, Slack, PagerDuty, OpsGenie, Teams, webhook).
- **Grafana**: piattaforma di visualizzazione che si connette a Prometheus come data source e permette di creare dashboard interattive, grafici, tabelle e pannelli di ogni tipo.

#### Configurazione prometheus.yml

Il file di configurazione principale definisce gli intervalli di scraping e i target da monitorare:

```yaml
global:
  scrape_interval: 15s          # Intervallo di default tra scrape
  evaluation_interval: 15s       # Intervallo di valutazione regole
  scrape_timeout: 10s            # Timeout per ogni scrape

# Regole di alerting
rule_files:
  - "rules/*.yml"

# Configurazione Alertmanager
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - "alertmanager:9093"

# Target da monitorare
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "node_exporter"
    static_configs:
      - targets:
          - "server-web-01:9100"
          - "server-web-02:9100"
          - "server-db-01:9100"
        labels:
          env: "production"
      - targets:
          - "server-dev-01:9100"
        labels:
          env: "development"

  - job_name: "windows_exporter"
    static_configs:
      - targets:
          - "win-server-01:9182"
          - "win-server-02:9182"

  - job_name: "blackbox_http"
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - "https://www.esempio.it"
          - "https://api.esempio.it/health"
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: "blackbox-exporter:9115"
```

#### Node Exporter per Linux

Node Exporter espone centinaia di metriche relative al sistema operativo Linux:

```bash
# Installazione
wget https://github.com/prometheus/node_exporter/releases/download/v1.8.2/node_exporter-1.8.2.linux-amd64.tar.gz
tar xzf node_exporter-1.8.2.linux-amd64.tar.gz
sudo cp node_exporter-1.8.2.linux-amd64/node_exporter /usr/local/bin/

# Creazione servizio systemd
sudo tee /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Prometheus Node Exporter
After=network-online.target

[Service]
Type=simple
User=node_exporter
ExecStart=/usr/local/bin/node_exporter \
    --collector.systemd \
    --collector.processes \
    --collector.tcpstat
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter
```

Le metriche principali esposte includono: `node_cpu_seconds_total`, `node_memory_MemAvailable_bytes`, `node_filesystem_avail_bytes`, `node_network_receive_bytes_total`, `node_disk_io_time_seconds_total`, `node_load1`, `node_load5`, `node_load15`.

#### Windows Exporter

Per i server Windows, il Windows Exporter (precedentemente noto come wmi_exporter) raccoglie metriche tramite le Performance Counters e WMI:

```powershell
# Installazione tramite MSI
msiexec /i windows_exporter-0.28.1-amd64.msi ENABLED_COLLECTORS="cpu,cs,logical_disk,memory,net,os,process,service,system,tcp,thermalzone" /qn
```

Metriche chiave: `windows_cpu_time_total`, `windows_logical_disk_free_bytes`, `windows_memory_available_bytes`, `windows_service_state`, `windows_os_info`.

#### Basi di PromQL

PromQL (Prometheus Query Language) e il linguaggio per interrogare le metriche. Le funzioni fondamentali:

```promql
# Tasso di utilizzo CPU (percentuale)
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memoria utilizzata in percentuale
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Traffico di rete in entrata (bytes/s)
rate(node_network_receive_bytes_total{device!="lo"}[5m])

# Spazio disco utilizzato in percentuale
100 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes * 100)

# Percentile 95 dei tempi di risposta HTTP
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Tasso di errori HTTP (5xx)
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# Top 5 filesystem per utilizzo
topk(5, 100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100))

# Aggregazione con increase (numero totale di richieste nell'ultima ora)
increase(http_requests_total[1h])
```

#### Recording Rules

Le recording rules pre-calcolano query PromQL complesse e salvano il risultato come nuove metriche, migliorando le prestazioni delle dashboard:

```yaml
groups:
  - name: node_rules
    interval: 30s
    rules:
      - record: instance:node_cpu_utilization:ratio
        expr: 1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))

      - record: instance:node_memory_utilization:ratio
        expr: 1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

      - record: instance:node_filesystem_utilization:ratio
        expr: 1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes)
```

#### Dashboard Grafana

Grafana si connette a Prometheus come data source e permette di costruire dashboard sofisticate. Le dashboard piu utilizzate dalla community includono:

- **Node Exporter Full (ID: 1860)**: dashboard completa per server Linux con oltre 50 pannelli organizzati per CPU, memoria, disco, rete, filesystem
- **Windows Server (ID: 14694)**: equivalente per server Windows
- **Prometheus Stats (ID: 2)**: monitoraggio dello stesso Prometheus

Per importare una dashboard: Grafana > Dashboards > Import > inserire l'ID o caricare il file JSON. Le variabili di template permettono di filtrare per host, job, ambiente, rendendo una singola dashboard utilizzabile per tutti i server.

Il sistema di alerting di Grafana permette di definire regole direttamente nelle dashboard o in modo centralizzato tramite la sezione Alerting, con supporto per condizioni multi-query, periodi di valutazione personalizzati e integrazione con canali di notifica multipli.

---

### SNMP Monitoring

Il Simple Network Management Protocol (SNMP) rimane il protocollo standard per il monitoraggio di apparati di rete (switch, router, firewall, access point), UPS, stampanti e qualsiasi dispositivo che non supporti l'installazione di agent software.

#### Versioni SNMP e Sicurezza

| Caratteristica | SNMPv1 | SNMPv2c | SNMPv3 |
|---------------|--------|---------|--------|
| **Autenticazione** | Community string (testo in chiaro) | Community string (testo in chiaro) | Username + password (MD5/SHA) |
| **Crittografia** | Nessuna | Nessuna | DES/AES-128/AES-256 |
| **Integrita** | Nessuna | Nessuna | HMAC-MD5/HMAC-SHA |
| **Modello di sicurezza** | Community-based | Community-based | User-based (USM) |
| **Raccomandazione** | Deprecato | Solo reti isolate | Obbligatorio in produzione |

SNMPv3 con livello di sicurezza `authPriv` (autenticazione e crittografia) e l'unica opzione accettabile per ambienti di produzione. Le community string di SNMPv1/v2c viaggiano in chiaro sulla rete e possono essere intercettate banalmente.

#### Struttura MIB e OID

Le Management Information Base (MIB) definiscono la struttura gerarchica delle informazioni accessibili via SNMP. Ogni metrica e identificata da un Object Identifier (OID), una sequenza numerica puntata che segue una struttura ad albero:

```
iso(1).org(3).dod(6).internet(1).mgmt(2).mib-2(1)
   |
   +-- system(1)
   |     +-- sysDescr(1)        -> 1.3.6.1.2.1.1.1
   |     +-- sysUpTime(3)       -> 1.3.6.1.2.1.1.3
   |     +-- sysName(5)         -> 1.3.6.1.2.1.1.5
   |
   +-- interfaces(2)
   |     +-- ifTable(2)
   |           +-- ifEntry(1)
   |                 +-- ifDescr(2)       -> 1.3.6.1.2.1.2.2.1.2
   |                 +-- ifOperStatus(8)  -> 1.3.6.1.2.1.2.2.1.8
   |                 +-- ifInOctets(10)   -> 1.3.6.1.2.1.2.2.1.10
   |                 +-- ifOutOctets(16)  -> 1.3.6.1.2.1.2.2.1.16
   |
   +-- host(25)
         +-- hrStorage(2)
         |     +-- hrStorageUsed(6)  -> 1.3.6.1.2.1.25.2.3.1.6
         +-- hrProcessorLoad(3)     -> 1.3.6.1.2.1.25.3.3.1.2
```

#### OID Comuni per il Monitoraggio

| Descrizione | OID | Tipo |
|-------------|-----|------|
| Descrizione sistema | 1.3.6.1.2.1.1.1.0 | STRING |
| Uptime del sistema | 1.3.6.1.2.1.1.3.0 | TimeTicks |
| Nome del sistema | 1.3.6.1.2.1.1.5.0 | STRING |
| Stato interfaccia di rete | 1.3.6.1.2.1.2.2.1.8 | INTEGER (1=up, 2=down) |
| Traffico in ingresso (byte) | 1.3.6.1.2.1.2.2.1.10 | Counter32 |
| Traffico in uscita (byte) | 1.3.6.1.2.1.2.2.1.16 | Counter32 |
| Carico CPU | 1.3.6.1.2.1.25.3.3.1.2 | INTEGER (percentuale) |
| Storage utilizzato | 1.3.6.1.2.1.25.2.3.1.6 | INTEGER |

#### Comandi snmpwalk e snmpget

```bash
# Interrogazione singola (sysName)
snmpget -v2c -c public 192.168.1.1 1.3.6.1.2.1.1.5.0

# SNMPv3 con autenticazione e crittografia
snmpget -v3 -l authPriv -u monitorUser -a SHA -A "AuthPass123" -x AES -X "PrivPass456" 192.168.1.1 1.3.6.1.2.1.1.3.0

# Walk di tutte le interfacce di rete
snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.2.2.1.2

# Walk completo di un host (attenzione: genera molto traffico)
snmpwalk -v3 -l authPriv -u monitorUser -a SHA -A "AuthPass123" -x AES -X "PrivPass456" 192.168.1.1 .1.3.6.1
```

#### Configurazione SNMP Trap

Gli SNMP Trap sono notifiche asincrone inviate dal dispositivo al sistema di monitoraggio quando si verifica un evento significativo (link down, errore hardware, superamento soglia). La configurazione di snmptrapd su Linux:

```bash
# /etc/snmp/snmptrapd.conf
authCommunity log,execute,net public
traphandle default /usr/sbin/snmptthandler

# Per SNMPv3
createUser -e 0x80001F88043... monitorUser SHA "AuthPass123" AES "PrivPass456"
authUser log monitorUser
```

L'integrazione con le piattaforme di monitoraggio avviene tipicamente tramite il componente snmptrapd che riceve i trap e li inoltra a Zabbix (tramite zabbix_trap_receiver.pl), Prometheus (tramite snmp_exporter) o altri sistemi.

---

### Log Management Centralizzato

La gestione centralizzata dei log e indispensabile per la risoluzione dei problemi, la conformita normativa, la sicurezza e l'analisi delle tendenze. Dispersi su centinaia di server, i log sono di difficile consultazione; centralizzati, diventano una risorsa potentissima per la diagnostica e il monitoraggio.

#### ELK Stack (Elasticsearch, Logstash, Kibana)

Lo stack ELK e la soluzione di riferimento per la gestione dei log su larga scala:

- **Elasticsearch**: motore di ricerca e analisi distribuito basato su Apache Lucene. Memorizza i log in indici, supporta ricerche full-text, aggregazioni e analisi in tempo reale. Scalabile orizzontalmente aggiungendo nodi al cluster.
- **Logstash**: pipeline di elaborazione dati che riceve log da molteplici sorgenti (file, syslog, Beats, Kafka), li analizza (parsing), li arricchisce (geoip, dns, translate) e li invia a Elasticsearch o altre destinazioni.
- **Kibana**: interfaccia web per la visualizzazione e l'esplorazione dei dati in Elasticsearch. Offre Discover per la ricerca interattiva, Dashboard per creare visualizzazioni, e Lens per l'analisi visiva dei dati.
- **Beats (Filebeat, Winlogbeat, Metricbeat)**: agent leggeri installati sui sistemi sorgente. Filebeat raccoglie log da file, Winlogbeat raccoglie gli Event Log di Windows, Metricbeat raccoglie metriche di sistema.

Architettura tipica di produzione:

```
[Server Linux]---Filebeat--->|                    |
[Server Windows]--Winlogbeat->|  Logstash/Kafka  |---> Elasticsearch Cluster ---> Kibana
[Appliance]------Syslog----->|   (Buffer/Parse)   |
[Container]------Filebeat--->|                    |
```

#### Loki + Grafana (Alternativa Leggera)

Loki, sviluppato da Grafana Labs, e un sistema di aggregazione log progettato per essere economico e facile da operare. A differenza di Elasticsearch, Loki **non indicizza il contenuto dei log** ma solo le label (etichette), riducendo drasticamente i requisiti di storage e risorse:

```yaml
# Configurazione Promtail (agent per Loki)
server:
  http_listen_port: 9080
positions:
  filename: /tmp/positions.yaml
clients:
  - url: http://loki:3100/loki/api/v1/push
scrape_configs:
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: syslog
          host: server-web-01
          __path__: /var/log/syslog
  - job_name: nginx
    static_configs:
      - targets:
          - localhost
        labels:
          job: nginx
          host: server-web-01
          __path__: /var/log/nginx/*.log
```

LogQL, il linguaggio di query di Loki, e ispirato a PromQL:

```logql
# Log di errore dal servizio nginx
{job="nginx"} |= "error"

# Log con parsing e filtraggio
{job="nginx"} | json | status >= 500

# Tasso di errori per host
sum(rate({job="nginx"} |= "error" [5m])) by (host)
```

#### Graylog

Graylog offre un'esperienza intermedia tra la complessita di ELK e la semplicita di Loki. Si distingue per le funzionalita di alerting integrate, il supporto nativo per i pipeline di elaborazione e una UI focalizzata sulla ricerca e analisi dei log. Utilizza Elasticsearch come storage backend e MongoDB per la configurazione.

#### Windows Event Forwarding (WEF) e Sysmon

Per gli ambienti Windows, WEF permette di centralizzare gli Event Log senza software di terze parti:

```powershell
# Sul collector (server centrale)
wecutil qc /q:true

# Creare una subscription per raccogliere eventi di sicurezza
wecutil cs SecuritySubscription.xml
```

Sysmon (System Monitor), parte di Sysinternals, genera log dettagliati su creazione processi, connessioni di rete, modifiche al filesystem e caricamento driver. Combinato con WEF o Filebeat/Winlogbeat, fornisce visibilita profonda sull'attivita dei sistemi Windows.

#### rsyslog e syslog-ng per Linux

Per i sistemi Linux, rsyslog (presente di default sulla maggior parte delle distribuzioni) puo essere configurato per l'invio centralizzato dei log:

```bash
# /etc/rsyslog.d/50-remote.conf (sul client)
*.* @@logserver.esempio.it:514    # TCP
# oppure
*.* @logserver.esempio.it:514     # UDP

# /etc/rsyslog.conf (sul server)
module(load="imtcp")
input(type="imtcp" port="514")

template(name="RemoteLogs" type="string"
    string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log")
*.* ?RemoteLogs
```

#### Retention e Gestione Storage

La gestione della retention dei log e cruciale per bilanciare requisiti normativi, costi di storage e prestazioni:

- **Hot storage** (SSD): ultimi 7-30 giorni, per ricerche frequenti e in tempo reale
- **Warm storage** (HDD): 30-90 giorni, per analisi occasionali
- **Cold storage** (archivio/object storage): 90 giorni - 7 anni, per compliance e audit
- **Index Lifecycle Management (ILM)** in Elasticsearch automatizza la transizione tra le fasi

---

### Monitoraggio Sintetico

Il monitoraggio sintetico verifica la disponibilita e le prestazioni dei servizi simulando le richieste degli utenti finali. A differenza del monitoraggio basato su agent che osserva le metriche interne dei server, il monitoraggio sintetico misura l'esperienza effettiva dall'esterno.

#### HTTP/HTTPS Endpoint Monitoring

Il controllo degli endpoint web verifica che i siti e le API rispondano correttamente, misurando tempi di risposta, codici di stato e contenuto della risposta.

#### API Health Check

Le API critiche espongono endpoint di health check dedicati (es. `/health`, `/status`, `/ready`) che restituiscono informazioni sullo stato dei componenti interni: connessione database, coda messaggi, cache, servizi dipendenti.

#### Monitoraggio Certificati SSL/TLS

La scadenza dei certificati SSL/TLS e una delle cause piu comuni e prevedibili di interruzione del servizio. Il monitoraggio automatico con alert a 30, 14 e 7 giorni dalla scadenza previene questi disservizi:

```bash
# Controllo scadenza certificato con OpenSSL
echo | openssl s_client -servername esempio.it -connect esempio.it:443 2>/dev/null | openssl x509 -noout -dates

# Monitoraggio con Blackbox Exporter (Prometheus)
# Metrica: probe_ssl_earliest_cert_expiry
# Alert: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 30
```

#### Strumenti

- **Uptime Kuma**: soluzione open-source self-hosted con interfaccia moderna, supporto per HTTP(S), TCP, DNS, Docker, Steam, gRPC, keyword check. Notifiche verso 90+ canali.
- **Blackbox Exporter**: componente di Prometheus per probe HTTP, TCP, DNS, ICMP. I risultati diventano metriche Prometheus interrogabili con PromQL e visualizzabili in Grafana.

---

## Gestione Alert

### Configurazione Soglie

La configurazione delle soglie di alert e un'attivita critica che richiede un approccio metodologico. Soglie troppo strette generano un numero eccessivo di falsi positivi (alert fatigue); soglie troppo permissive lasciano passare problemi significativi senza notifica.

#### Metodologia per la Definizione delle Baseline

1. **Raccolta dati**: monitorare le metriche senza alert per almeno 2-4 settimane, coprendo diversi cicli operativi (giorni lavorativi, weekend, fine mese, periodi di carico elevato).
2. **Analisi statistica**: calcolare media, mediana, deviazione standard, percentili (P95, P99) per ogni metrica.
3. **Identificazione pattern**: riconoscere i pattern ciclici (carico elevato durante orario lavorativo, batch notturni, picchi settimanali).
4. **Definizione soglie**: basare le soglie Warning su valori P95 storici + margine, e le soglie Critical su condizioni che impattano realmente il servizio.
5. **Iterazione**: raffinare le soglie nel tempo basandosi sui falsi positivi e sui problemi non rilevati.

#### Soglie Statiche vs Dinamiche

Le **soglie statiche** sono valori fissi configurati manualmente (es. CPU > 90% = Critical). Semplici da implementare e comprendere, sono adeguate per metriche con comportamento prevedibile.

Le **soglie dinamiche** (o anomaly detection) calcolano automaticamente i limiti accettabili basandosi sullo storico. Strumenti come Datadog e Dynatrace offrono questa funzionalita nativamente; con Prometheus, si possono approssimare usando `predict_linear()` e medie mobili.

#### Tabella Soglie di Riferimento

| Metrica | Warning | Critical | Note |
|---------|---------|----------|------|
| **CPU Utilizzo** | > 80% per 5 min | > 95% per 3 min | Media su tutti i core |
| **Memoria Utilizzata** | > 85% | > 95% | Considerare swap usage |
| **Disco Utilizzato** | > 80% | > 90% | Per partizione, escludere tmpfs |
| **Disco I/O Wait** | > 20% per 5 min | > 40% per 3 min | Indica bottleneck storage |
| **Rete Packet Loss** | > 1% | > 5% | Misurata su intervallo 5 min |
| **Rete Latenza** | > 50ms | > 200ms | Verso gateway/servizi critici |
| **Disponibilita Servizio** | < 99.9% (rolling 1h) | Servizio down | Monitoraggio endpoint |
| **Tempo Risposta HTTP** | > 2s (P95) | > 5s (P95) | Personalizzare per servizio |
| **Certificato SSL** | Scadenza < 30 giorni | Scadenza < 14 giorni | Nessuna soppressione |
| **Backup Status** | Backup parziale | Backup fallito | Controllare completezza |
| **Errori HTTP 5xx** | > 1% delle richieste | > 5% delle richieste | Tasso su finestra 5 min |
| **Processi Zombie** | > 3 | > 10 | Indicatore di problemi applicativi |
| **Connessioni DB** | > 80% pool | > 95% pool | Rischio esaurimento |
| **Load Average** | > N core * 1.5 | > N core * 3 | N = numero core CPU |
| **Swap Usage** | > 10% | > 50% | Dovrebbe essere minimo |

---

### Alert Routing e Notifiche

Un sistema di alert efficace non si limita a generare notifiche: deve instradare ogni alert al destinatario giusto, nel momento giusto, attraverso il canale appropriato, evitando notifiche duplicate e garantendo l'escalation automatica se un alert non viene gestito.

#### Matrice di Escalation

| Livello | Tempo dalla Rilevazione | Destinatario | Canale |
|---------|------------------------|--------------|--------|
| L1 | 0 min | Tecnico on-call | Slack + push notification |
| L2 | 15 min (se non ACK) | Team lead | Slack + SMS |
| L3 | 30 min (se non risolto) | System architect | Telefono + SMS |
| L4 | 60 min (se non risolto) | IT Manager | Telefono + email executive |

#### Rotazione On-Call

La rotazione on-call definisce chi e responsabile della risposta agli alert fuori orario lavorativo. Principi fondamentali:

- Rotazioni settimanali o bisettimanali per evitare il burnout
- Almeno 2 persone in ogni turno (primario e backup)
- Handoff formale con briefing sullo stato attuale
- Compensazione equa per il servizio di reperibilita
- Strumenti come PagerDuty o OpsGenie gestiscono automaticamente schedule, escalation e override

#### Canali di Notifica

| Canale | Uso Appropriato | Latenza | Affidabilita |
|--------|----------------|---------|--------------|
| **Email** | Informational, report, riepiloghi | Alta (minuti) | Media |
| **Slack/Teams** | Warning, collaborazione in tempo reale | Bassa (secondi) | Alta |
| **SMS** | Critical, fuori orario | Bassa (secondi) | Alta |
| **Push notification** | Warning/Critical, on-call | Molto bassa | Media |
| **PagerDuty/OpsGenie** | Critical, escalation automatica | Molto bassa | Molto alta |
| **Telefono** | Disaster, escalation L3+ | Immediata | Alta |

#### Prevenzione dell'Alert Fatigue

L'alert fatigue e la condizione in cui il team riceve cosi tanti alert da iniziare a ignorarli, inclusi quelli critici. Strategie di prevenzione:

- **Raggruppamento**: aggregare alert correlati in un'unica notifica (es. tutti i servizi di un server che vanno giu)
- **Deduplicazione**: evitare notifiche ripetute per lo stesso problema
- **Soglie appropriate**: come descritto nella sezione precedente
- **Silencing**: sopprimere alert durante manutenzioni pianificate
- **Revisione periodica**: analizzare mensilmente gli alert generati, eliminare quelli che non hanno portato ad azioni
- **Regola d'oro**: ogni alert deve richiedere un'azione umana; se non richiede azione, non dovrebbe essere un alert

---

### Alertmanager Configuration

Alertmanager e il componente di Prometheus dedicato alla gestione delle notifiche. Riceve gli alert dal server Prometheus e li instrada secondo regole configurabili.

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.esempio.it:587'
  smtp_from: 'alertmanager@esempio.it'
  smtp_auth_username: 'alertmanager@esempio.it'
  smtp_auth_password: 'password_sicura'
  smtp_require_tls: true
  slack_api_url: 'https://hooks.slack.com/services/T00/B00/XXXXXXXXX'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

# Struttura di routing
route:
  receiver: 'slack-default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s           # Attesa prima di inviare il primo alert del gruppo
  group_interval: 5m        # Intervallo tra notifiche dello stesso gruppo
  repeat_interval: 4h       # Intervallo per ri-notificare un alert non risolto

  routes:
    # Alert critici -> PagerDuty + Slack
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      group_wait: 10s
      repeat_interval: 1h
      continue: true         # Continua a valutare le route successive

    - match:
        severity: critical
      receiver: 'slack-critical'

    # Alert warning -> solo Slack
    - match:
        severity: warning
      receiver: 'slack-warning'
      repeat_interval: 8h

    # Alert relativi ai database -> team DBA
    - match_re:
        alertname: '(MySQL|PostgreSQL|Redis).*'
      receiver: 'slack-dba'

# Regole di inibizione
inhibit_rules:
  # Se un host e down, sopprimere tutti gli altri alert per quell'host
  - source_match:
      alertname: 'HostDown'
    target_match_re:
      alertname: '.+'
    equal: ['instance']

  # Se un alert critical esiste, sopprimere il warning equivalente
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']

# Definizione dei receiver
receivers:
  - name: 'slack-default'
    slack_configs:
      - channel: '#monitoring'
        send_resolved: true
        title: '{{ .GroupLabels.alertname }}'
        text: >-
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Descrizione:* {{ .Annotations.description }}
          *Severita:* {{ .Labels.severity }}
          *Istanza:* {{ .Labels.instance }}
          {{ end }}

  - name: 'slack-critical'
    slack_configs:
      - channel: '#incidents'
        send_resolved: true
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'

  - name: 'slack-warning'
    slack_configs:
      - channel: '#monitoring-warnings'
        send_resolved: true

  - name: 'slack-dba'
    slack_configs:
      - channel: '#dba-alerts'
        send_resolved: true

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'CHIAVE_SERVIZIO_PAGERDUTY'
        severity: 'critical'

  - name: 'email-management'
    email_configs:
      - to: 'it-management@esempio.it'
        send_resolved: true
```

Esempio di regola di alert in Prometheus che invia ad Alertmanager:

```yaml
# rules/node_alerts.yml
groups:
  - name: node_alerts
    rules:
      - alert: HostHighCpuUsage
        expr: instance:node_cpu_utilization:ratio > 0.90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU elevata su {{ $labels.instance }}"
          description: "L'utilizzo CPU su {{ $labels.instance }} e al {{ $value | humanizePercentage }} da oltre 5 minuti."

      - alert: HostOutOfDiskSpace
        expr: instance:node_filesystem_utilization:ratio > 0.90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Spazio disco critico su {{ $labels.instance }}"
          description: "Il filesystem {{ $labels.mountpoint }} su {{ $labels.instance }} e al {{ $value | humanizePercentage }}."

      - alert: HostDown
        expr: up == 0
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Host {{ $labels.instance }} non raggiungibile"
          description: "L'host {{ $labels.instance }} non risponde da oltre 3 minuti."

      - alert: SSLCertExpiringSoon
        expr: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificato SSL in scadenza per {{ $labels.instance }}"
          description: "Il certificato SSL scadra tra {{ $value | humanize }} giorni."
```

---

## Gestione Incidenti

### Processo Incident Management

La gestione degli incidenti segue un processo strutturato che garantisce una risposta rapida, coordinata e documentata a qualsiasi interruzione o degradazione del servizio. Il processo si articola in cinque fasi:

#### 1. Detection (Rilevazione)

L'incidente viene rilevato attraverso:
- **Alert automatici** dal sistema di monitoraggio (canale preferenziale)
- **Segnalazione utenti** tramite help desk o canali di comunicazione
- **Controlli manuali** durante attivita di routine
- **Segnalazione fornitori** (provider cloud, ISP, vendor software)

Il tempo di rilevazione (TTD - Time To Detect) e una metrica chiave: minore e il TTD, prima inizia il processo di risposta.

#### 2. Triage (Classificazione e Prioritizzazione)

Il triage determina la severita dell'incidente e l'urgenza della risposta. La classificazione avviene secondo una scala a quattro livelli:

| Severita | Definizione | Esempio | Risposta Richiesta |
|----------|-------------|---------|-------------------|
| **SEV1 - Critico** | Servizio completamente non disponibile per tutti gli utenti; perdita dati in corso; violazione sicurezza confermata | Database di produzione inaccessibile; ransomware attivo; sito web principale completamente down | Immediata, tutti le risorse necessarie, comunicazione a management |
| **SEV2 - Grave** | Funzionalita critica degradata significativamente; workaround parziale disponibile | Tempi di risposta 10x superiori al normale; servizio di pagamento intermittente; replica database interrotta | Entro 15 minuti, team dedicato |
| **SEV3 - Moderato** | Funzionalita non critica impattata; workaround disponibile | Report giornaliero fallito; servizio email lento; un server su tre nel pool non funzionante | Entro 1 ora, durante orario lavorativo |
| **SEV4 - Basso** | Impatto minimo; problema estetico o funzionalita minore | Errore di formattazione in un report; lentezza sporadica di un servizio non critico; warning nel log senza impatto | Entro 4 ore, durante orario lavorativo, pianificabile |

#### 3. Investigation (Indagine)

La fase di indagine mira a identificare la causa radice (root cause) dell'incidente. Approccio strutturato:

- **Raccolta informazioni**: quando e iniziato il problema? Cosa e cambiato di recente? (deployment, patch, configurazione, modifica infrastruttura) Chi e impattato? Quali servizi sono coinvolti?
- **Analisi dei log**: ricerca di errori, warning, eccezioni nei log dei sistemi coinvolti
- **Correlazione temporale**: confrontare la timeline dell'incidente con deployment, modifiche di configurazione, eventi infrastrutturali
- **Verifica delle metriche**: analizzare le dashboard di monitoraggio per individuare anomalie (spike di CPU, esaurimento memoria, saturazione disco, aumento latenza)
- **Test e isolamento**: verificare se il problema e riproducibile, isolare il componente responsabile

#### 4. Resolution (Risoluzione)

La risoluzione puo avvenire attraverso:

- **Fix immediato**: correzione diretta della causa (riavvio servizio, rollback deployment, patch di emergenza)
- **Workaround**: soluzione temporanea che ripristina il servizio mentre si lavora alla correzione definitiva (es. redirect traffico su server secondario, failover manuale)
- **Escalation**: coinvolgimento di specialisti, vendor o team di sviluppo se la risoluzione richiede competenze specifiche

Metriche chiave:
- **MTTA** (Mean Time To Acknowledge): tempo medio dalla rilevazione alla presa in carico
- **MTTR** (Mean Time To Resolve): tempo medio dalla rilevazione alla risoluzione completa
- **MTTF** (Mean Time To Failure): tempo medio tra un incidente e il successivo (indica l'affidabilita)

#### 5. Post-Mortem (Analisi Retrospettiva)

Documentata nella sezione dedicata piu avanti, e la fase in cui si analizza l'incidente per prevenire che si ripeta.

#### SLA di Risposta per Severita

| Severita | Acknowledgement | Aggiornamento | Target Risoluzione |
|----------|----------------|---------------|-------------------|
| SEV1 | 5 minuti | Ogni 15 minuti | 1 ora |
| SEV2 | 15 minuti | Ogni 30 minuti | 4 ore |
| SEV3 | 1 ora | Ogni 2 ore | 24 ore (business hours) |
| SEV4 | 4 ore | Giornaliero | 72 ore (business hours) |

---

### War Room / Incident Response

Quando viene dichiarato un incidente SEV1 o SEV2, si attiva una war room: uno spazio (fisico o virtuale) dedicato alla risoluzione dell'incidente con comunicazione in tempo reale.

#### Setup della War Room

**War room virtuale** (piu comune in contesti moderni):
- Canale Slack/Teams dedicato (es. `#inc-2026-0326-db-outage`)
- Bridge telefonico o videochiamata permanente
- Documento condiviso per timeline e appunti in tempo reale
- Dashboard di monitoraggio proiettate o condivise a schermo

**War room fisica** (per incidenti prolungati o particolarmente gravi):
- Sala riunioni dedicata con schermi per dashboard
- Connessione stabile alla rete e ai sistemi
- Whiteboard per diagrammi e timeline
- Accesso diretto a tutti gli strumenti necessari

#### Ruoli durante l'Incidente

| Ruolo | Responsabilita | Competenze |
|-------|---------------|------------|
| **Incident Commander (IC)** | Coordina la risposta, prende decisioni, gestisce il flusso di lavoro, dichiara la risoluzione. Non lavora direttamente sulla risoluzione tecnica. | Leadership, comunicazione, conoscenza dei processi |
| **Communications Lead** | Aggiorna gli stakeholder interni, gestisce la status page, prepara le comunicazioni esterne. | Comunicazione scritta, gestione stakeholder |
| **Technical Lead** | Guida l'analisi tecnica, coordina le azioni di debug e risoluzione, assegna i task ai tecnici. | Competenza tecnica approfondita sui sistemi coinvolti |
| **Scribe** | Documenta la timeline, le azioni intraprese, le decisioni prese. Fondamentale per il post-mortem. | Attenzione al dettaglio, velocita di annotazione |
| **Subject Matter Experts (SME)** | Specialisti dei sistemi coinvolti, chiamati in causa secondo necessita. | Competenza profonda su specifici componenti |

#### Comunicazione durante l'Incidente

La comunicazione segue un ritmo predefinito basato sulla severita. Ogni aggiornamento include:

- Stato attuale (in indagine / causa identificata / fix in corso / monitoraggio post-fix)
- Impatto corrente (servizi impattati, utenti coinvolti)
- Prossimi passi pianificati
- Tempo stimato per il prossimo aggiornamento

---

### Incident Communication

La comunicazione durante gli incidenti e tanto critica quanto la risoluzione tecnica. Una comunicazione inefficace amplifica l'impatto percepito dell'incidente, erode la fiducia degli stakeholder e genera confusione.

#### Template Notifica Interna

```
INCIDENTE [SEV1/SEV2/SEV3] - [Titolo Breve]
Data/Ora: [YYYY-MM-DD HH:MM UTC+1]
Incident Commander: [Nome]

STATO: [INDAGINE IN CORSO / CAUSA IDENTIFICATA / FIX IN CORSO / RISOLTO]

IMPATTO:
- Servizi impattati: [elenco servizi]
- Utenti impattati: [tutti / gruppo specifico / regione]
- Funzionalita degradate: [descrizione]

DESCRIZIONE:
[Breve descrizione del problema e di come si manifesta]

AZIONI IN CORSO:
- [Azione 1 - responsabile]
- [Azione 2 - responsabile]

PROSSIMO AGGIORNAMENTO: [HH:MM UTC+1]
CANALE DI COORDINAMENTO: [#inc-YYYY-MMDD-descrizione]
```

#### Template Notifica Esterna (Clienti)

```
[Nome Servizio] - Interruzione del Servizio

Siamo consapevoli di un problema che sta impattando [descrizione generica].

Impatto: [Descrizione dell'impatto dal punto di vista dell'utente]

Il nostro team sta lavorando attivamente alla risoluzione.
Forniremo un aggiornamento entro [orario].

Ci scusiamo per il disagio.
```

#### Status Page

Una status page pubblica fornisce trasparenza sullo stato dei servizi. Strumenti disponibili:

- **Statuspage.io** (Atlassian): SaaS commerciale, integrazione con Jira e OpsGenie
- **Cachet**: open-source, self-hosted, scritto in PHP
- **Upptime**: open-source, basato su GitHub Actions, senza necessita di server dedicato
- **Gatus**: open-source, health dashboard con monitoraggio integrato

La status page deve mostrare: stato corrente di ogni servizio (Operational, Degraded Performance, Partial Outage, Major Outage), cronologia degli incidenti recenti, metriche di uptime e manutenzioni pianificate.

---

### Post-Mortem / Post-Incident Review

Il post-mortem (o Post-Incident Review, PIR) e il processo strutturato di analisi che segue ogni incidente significativo (tipicamente SEV1 e SEV2, opzionalmente SEV3). Il suo scopo non e assegnare colpe, ma comprendere cosa e successo, perche e successo, e come prevenire che si ripeta.

#### Principi del Blameless Post-Mortem

Il concetto di post-mortem "blameless" (senza colpe) e fondamentale per una cultura di apprendimento efficace:

- **Le persone non sono la causa radice**: i sistemi devono essere progettati per prevenire e tollerare gli errori umani. Se un operatore ha potuto causare un'interruzione, il problema e nel sistema, non nell'operatore.
- **Trasparenza totale**: ogni dettaglio viene condiviso apertamente, senza omissioni per proteggere individui o team.
- **Focus sul miglioramento**: l'obiettivo e generare action items concreti che migliorino la resilienza del sistema.
- **Partecipazione di tutti i coinvolti**: chi ha lavorato all'incidente partecipa attivamente alla review.
- **Cultura dell'apprendimento**: gli incidenti sono opportunita di apprendimento, non fallimenti da nascondere.

#### Template PIR (Post-Incident Review)

```markdown
# Post-Incident Review: [Titolo Incidente]
**Data Incidente**: [YYYY-MM-DD]
**Durata**: [HH:MM - HH:MM UTC+1] ([durata totale])
**Severita**: [SEV1/SEV2/SEV3]
**Incident Commander**: [Nome]
**Autore PIR**: [Nome]
**Data PIR**: [YYYY-MM-DD]
**Partecipanti PIR**: [Nomi]

## Riepilogo Esecutivo
[2-3 frasi che descrivono cosa e successo, l'impatto e la causa radice]

## Impatto
- Durata totale: [minuti/ore]
- Servizi impattati: [elenco]
- Utenti impattati: [numero/percentuale]
- Impatto finanziario stimato: [se applicabile]
- SLA violati: [si/no, dettagli]

## Timeline Dettagliata
| Ora (UTC+1) | Evento |
|-------------|--------|
| HH:MM | [Primo segnale anomalo rilevato dal monitoraggio] |
| HH:MM | [Alert generato / segnalazione ricevuta] |
| HH:MM | [Incident Commander assegnato] |
| HH:MM | [Prima ipotesi investigata] |
| HH:MM | [Causa radice identificata] |
| HH:MM | [Fix applicato] |
| HH:MM | [Servizio ripristinato] |
| HH:MM | [Monitoraggio post-fix confermato stabile] |
| HH:MM | [Incidente dichiarato risolto] |

## Causa Radice
[Descrizione dettagliata della causa radice. Non "errore umano" ma
"il sistema permetteva di eseguire X senza conferma/validazione"]

## Fattori Contribuenti
- [Fattore 1: es. mancanza di alert per la condizione specifica]
- [Fattore 2: es. documentazione non aggiornata del runbook]
- [Fattore 3: es. assenza di test automatici per lo scenario]

## Cosa ha Funzionato Bene
- [Es. alert di monitoraggio rilevato il problema in 2 minuti]
- [Es. comunicazione interna tempestiva e chiara]
- [Es. procedura di rollback eseguita correttamente]

## Cosa Puo Essere Migliorato
- [Es. tempo di rilevazione troppo lungo per la tipologia di problema]
- [Es. mancanza di runbook per questo scenario specifico]
- [Es. escalation troppo lenta]

## Action Items
| # | Azione | Responsabile | Priorita | Scadenza | Stato |
|---|--------|-------------|----------|----------|-------|
| 1 | [Aggiungere alert per condizione X] | [Nome] | Alta | [Data] | Aperto |
| 2 | [Creare runbook per scenario Y] | [Nome] | Media | [Data] | Aperto |
| 3 | [Implementare test automatico per Z] | [Nome] | Alta | [Data] | Aperto |
| 4 | [Rivedere processo di deployment] | [Nome] | Media | [Data] | Aperto |

## Lezioni Apprese
[Riflessioni generali applicabili oltre questo specifico incidente]
```

#### Condivisione e Apprendimento

I post-mortem devono essere condivisi con tutta l'organizzazione tecnica, non solo con il team coinvolto. Le modalita includono:

- Repository centralizzato dei PIR (wiki interna, Confluence, GitLab wiki)
- Presentazione durante riunioni periodiche del team IT
- Newsletter interna con i PIR piu significativi
- Revisione periodica degli action items per garantirne l'esecuzione
- Analisi delle tendenze: se gli stessi problemi si ripresentano, il processo di miglioramento non sta funzionando

---

## Performance Monitoring

### Capacity Planning

Il capacity planning e il processo di analisi delle risorse IT per garantire che l'infrastruttura sia adeguata a sostenere il carico attuale e futuro, evitando sia il sovradimensionamento (spreco di risorse) sia il sottodimensionamento (rischio di saturazione).

#### Trending dell'Utilizzo Risorse

L'analisi dei trend richiede la raccolta storica delle metriche su periodi significativi (almeno 3-6 mesi, idealmente 12 mesi per catturare stagionalita). Le metriche chiave per il capacity planning includono:

- **CPU**: utilizzo medio, P95, P99, trend di crescita
- **Memoria**: utilizzo medio, picchi, tendenza
- **Storage**: spazio utilizzato, tasso di crescita, IOPS, throughput
- **Rete**: utilizzo banda, picchi, latenza
- **Database**: connessioni attive, query per secondo, dimensione dati

#### Previsione di Crescita

La funzione `predict_linear()` di Prometheus permette di stimare quando una risorsa raggiungera una soglia critica:

```promql
# Predizione: quando il disco sara pieno (basato sugli ultimi 7 giorni di trend)
predict_linear(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}[7d], 30*24*3600) < 0
# Questa query restituisce true se il disco sara pieno entro 30 giorni

# Predizione crescita database
predict_linear(mysql_global_status_data_length[30d], 90*24*3600)
```

#### Report di Capacity Planning

Un report di capacity planning trimestrale dovrebbe includere:

1. **Stato attuale**: utilizzo corrente di ogni risorsa critica con confronto rispetto al trimestre precedente
2. **Trend**: grafici di andamento con proiezioni a 3, 6 e 12 mesi
3. **Allarmi previsivi**: risorse che raggiungeranno la soglia critica nel periodo di previsione
4. **Raccomandazioni**: azioni proposte (upgrade hardware, ottimizzazione software, migrazione, dismissione)
5. **Budget**: stima dei costi per le azioni proposte
6. **Rischi**: conseguenze del mancato intervento

---

### Application Performance

Il monitoraggio delle prestazioni applicative (APM - Application Performance Monitoring) va oltre le metriche infrastrutturali per misurare l'esperienza reale degli utenti e le prestazioni del codice applicativo.

#### Concetti Fondamentali dell'APM

L'APM si concentra su tre pilastri:

- **Metriche (Metrics)**: misurazioni quantitative delle prestazioni (tempi di risposta, throughput, tasso di errore)
- **Tracce (Traces)**: registrazione del percorso completo di una richiesta attraverso i componenti del sistema
- **Log**: registrazione dettagliata degli eventi a livello applicativo

#### Metriche Chiave dell'APM

Le metriche fondamentali per l'APM, spesso indicate come **RED metrics** (Rate, Errors, Duration):

- **Rate (Throughput)**: numero di richieste al secondo. Indica il carico sul sistema e le variazioni rispetto alla baseline.
- **Error Rate**: percentuale di richieste che risultano in errore (HTTP 5xx, eccezioni non gestite, timeout). Un aumento improvviso segnala un problema.
- **Duration (Response Time)**: tempo necessario per completare una richiesta. Si analizzano media, mediana, P95 e P99. Il P99 e particolarmente importante perche rappresenta l'esperienza dell'1% degli utenti peggio serviti.

Ulteriori metriche rilevanti:
- **Apdex score**: indice di soddisfazione utente (0-1) basato su soglie di tempo di risposta configurabili
- **Saturazione**: quanto le risorse sono vicine alla capacita massima
- **Connessioni al database**: pool usage, query lente, lock

#### Distributed Tracing

In architetture a microservizi, una singola richiesta utente puo attraversare decine di servizi. Il distributed tracing segue la richiesta attraverso tutti i componenti, visualizzando tempi e dipendenze:

- **Jaeger** (CNCF): tracing open-source sviluppato da Uber, ottima integrazione con Kubernetes
- **Zipkin**: sistema di tracing distribuito originariamente sviluppato da Twitter
- **OpenTelemetry**: standard emergente che unifica metriche, log e tracce in un unico framework. Supporta l'esportazione verso Jaeger, Zipkin, Grafana Tempo e sistemi commerciali

Ogni traccia (trace) e composta da **span**: segmenti che rappresentano un'operazione in un servizio specifico. Ogni span registra: nome operazione, servizio, tempo di inizio e durata, tag e log associati.

#### Real User Monitoring (RUM)

Il RUM raccoglie dati sulle prestazioni direttamente dal browser o dal dispositivo dell'utente finale:

- **Page load time**: tempo totale di caricamento della pagina
- **First Contentful Paint (FCP)**: tempo alla prima renderizzazione di contenuto
- **Largest Contentful Paint (LCP)**: tempo alla renderizzazione dell'elemento piu grande
- **First Input Delay (FID)**: ritardo alla prima interazione dell'utente
- **Cumulative Layout Shift (CLS)**: stabilita visiva della pagina

Strumenti come Grafana Faro (open-source), Datadog RUM e New Relic Browser forniscono questa visibilita. I dati RUM, correlati con le metriche server-side, offrono un quadro completo delle prestazioni percepite.

---

## Best Practices

1. **Monitorare cio che conta per l'utente finale**: partire sempre dall'esperienza utente e scendere verso l'infrastruttura, non viceversa. Se l'utente percepisce lentezza, il monitoraggio deve rilevarlo anche se tutte le metriche di sistema sono nella norma. Definire Service Level Indicators (SLI) e Service Level Objectives (SLO) per ogni servizio critico.

2. **Adottare un approccio stratificato**: monitorare a tutti i livelli dell'infrastruttura (rete, sistema operativo, servizi, applicazione, esperienza utente) con strumenti appropriati per ogni livello. Evitare lacune nella copertura che creano punti ciechi nella visibilita operativa.

3. **Mantenere le soglie aggiornate**: le soglie di alert non sono configurazioni statiche. Rivederle trimestralmente, confrontandole con i dati reali, eliminando quelle che generano falsi positivi cronici e aggiungendo quelle necessarie per nuovi pattern di problemi. Documentare la motivazione dietro ogni soglia.

4. **Automatizzare la risposta dove possibile**: per problemi noti e ricorrenti con soluzione deterministica, implementare auto-remediation (riavvio automatico servizi, pulizia disco, scaling automatico). L'automazione riduce il MTTR e libera il team per attivita a maggior valore aggiunto. Ogni automazione deve essere loggata e monitorata.

5. **Implementare il post-mortem come cultura, non come obbligo**: i post-mortem devono essere blameless, condivisi apertamente e seguiti da action items tracciati fino alla completa implementazione. Un post-mortem senza action items completati e un esercizio inutile. Misurare la percentuale di action items completati entro la scadenza come indicatore di maturita del processo.

6. **Centralizzare i log e correlare con le metriche**: log dispersi su centinaia di server sono inutilizzabili durante un incidente. Centralizzare i log, arricchirli con metadata contestuali (hostname, servizio, ambiente, request ID) e correlarli temporalmente con le metriche di monitoraggio per accelerare la diagnostica.

7. **Testare il sistema di monitoraggio e alerting**: un sistema di monitoraggio non testato e un sistema inaffidabile. Verificare periodicamente che gli alert funzionino simulando condizioni di errore, che le notifiche raggiungano i destinatari corretti e che le escalation si attivino nei tempi previsti. Includere il monitoraggio nei test di disaster recovery.

8. **Documentare e mantenere aggiornati i runbook**: per ogni alert significativo, creare un runbook che descriva la causa probabile, i passi diagnostici, le azioni correttive e i criteri di escalation. Un runbook aggiornato riduce il tempo di risoluzione e permette anche a personale meno esperto di gestire problemi noti.

9. **Pianificare la capacita proattivamente**: non aspettare che le risorse si esauriscano. Utilizzare i dati storici per prevedere la crescita, generare report trimestrali di capacity planning e pianificare gli interventi con anticipo sufficiente per evitare emergenze. Integrare il capacity planning nel ciclo di budgeting IT.

10. **Minimizzare l'alert fatigue con disciplina**: ogni alert deve richiedere un'azione umana specifica. Alert informativi che non richiedono azione devono essere degradati a dashboard o report. Revisionare mensilmente le statistiche degli alert (numero totale, tasso di falsi positivi, alert ignorati) e agire per ridurre il rumore. Un team sommerso dagli alert e un team che non risponde agli alert.

---

## Troubleshooting

### Problema: Alert non Ricevuti

**Sintomi**: il sistema di monitoraggio rileva il problema ma le notifiche non raggiungono il destinatario.

**Diagnosi e Risoluzione**:
- Verificare la configurazione del canale di notifica (credenziali SMTP, token Slack, chiavi API PagerDuty)
- Controllare i log del componente di notifica (Alertmanager, Zabbix action log)
- Verificare che l'alert non sia in stato "silenced" o in una finestra di manutenzione
- Controllare i filtri anti-spam per le notifiche email
- Testare il canale di notifica inviando un alert di test manuale
- Verificare la raggiungibilita di rete verso il servizio di notifica (firewall, proxy)
- In Alertmanager, verificare che il routing corrisponda ai label dell'alert

### Problema: Troppi Falsi Positivi

**Sintomi**: il team riceve centinaia di alert al giorno, la maggior parte dei quali non richiede azione.

**Diagnosi e Risoluzione**:
- Analizzare statisticamente gli alert dell'ultimo mese: categorizzare per tipo, severita, actionability
- Identificare gli alert con il tasso piu alto di falsi positivi
- Aumentare le soglie o i tempi di valutazione (`for` in Prometheus, durata valutazione in Zabbix)
- Aggiungere regole di inibizione per evitare cascate di alert correlati
- Implementare hysteresis: soglia di attivazione piu alta rispetto alla soglia di disattivazione
- Convertire gli alert informativi in metriche di dashboard
- Eliminare completamente gli alert che non portano mai ad azione

### Problema: Gap nei Dati di Monitoraggio

**Sintomi**: le dashboard mostrano interruzioni nella raccolta dati, grafici con buchi.

**Diagnosi e Risoluzione**:
- Verificare lo stato degli agent/exporter sui sistemi monitorati (`systemctl status node_exporter`)
- Controllare la connettivita di rete tra server di monitoraggio e target
- Verificare che il server di monitoraggio non sia sovraccarico (scrape duration, queue size)
- Controllare i limiti di risorse: Prometheus potrebbe avere problemi di memoria o disco
- Per Zabbix: verificare la dimensione della coda interna (queue), lo stato dei proxy
- Verificare che i timeout di scrape non siano troppo bassi per target lenti
- Controllare l'orologio di sistema (NTP) su tutti i componenti

### Problema: Dashboard Lente in Grafana

**Sintomi**: le dashboard Grafana impiegano molto tempo a caricarsi o vanno in timeout.

**Diagnosi e Risoluzione**:
- Ridurre il range temporale delle query (da "Last 30 days" a "Last 24 hours")
- Utilizzare recording rules in Prometheus per pre-calcolare query complesse
- Ridurre il numero di pannelli per dashboard (massimo 20-25 per dashboard)
- Verificare che le query non utilizzino regex non necessari o aggregazioni su troppe serie
- Aumentare le risorse (CPU, memoria) del server Grafana e di Prometheus
- Utilizzare variabili di template per filtrare le query anziche interrogare tutti gli host
- Verificare che Prometheus non abbia troppe serie temporali attive (cardinality explosion)

### Problema: Elasticsearch Lento o Instabile

**Sintomi**: le ricerche in Kibana sono lente, Elasticsearch non risponde, cluster in stato yellow o red.

**Diagnosi e Risoluzione**:
- Controllare lo stato del cluster: `curl -s localhost:9200/_cluster/health?pretty`
- Verificare l'allocazione degli shard: `curl -s localhost:9200/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason`
- Controllare lo spazio disco sui nodi (Elasticsearch richiede almeno il 15% libero per funzionare)
- Verificare l'heap JVM: non deve superare il 75% dell'allocazione (`_nodes/stats/jvm`)
- Implementare ILM per la rotazione automatica degli indici
- Ridurre il numero di shard per indice (un problema comune e l'over-sharding)
- Forzare il merge dei segmenti su indici vecchi: `POST /indice/_forcemerge?max_num_segments=1`

### Problema: Agent/Exporter Non Raggiungibile

**Sintomi**: il target risulta "down" nel sistema di monitoraggio ma il server e attivo.

**Diagnosi e Risoluzione**:
- Verificare che l'agent/exporter sia in esecuzione sul sistema target
- Controllare il binding della porta (es. `ss -tlnp | grep 9100` per Node Exporter)
- Verificare le regole del firewall locale (iptables, firewalld, Windows Firewall)
- Controllare le ACL di rete e i security group (in ambienti cloud)
- Verificare che l'agent sia configurato per accettare connessioni dall'IP del server di monitoraggio
- Per Zabbix Agent: controllare `AllowedIP` e `Server` in `zabbix_agentd.conf`
- Per exporter Prometheus: verificare con `curl http://target:porta/metrics` dal server Prometheus

### Problema: Incidente Ricorrente

**Sintomi**: lo stesso tipo di incidente si verifica ripetutamente nonostante le correzioni.

**Diagnosi e Risoluzione**:
- Rivedere i post-mortem precedenti per lo stesso tipo di incidente
- Verificare che gli action items dei PIR precedenti siano stati completati
- Analizzare se la causa radice identificata precedentemente era corretta o se era solo un sintomo
- Considerare fattori sistemici: architettura inadeguata, debito tecnico, mancanza di ridondanza
- Implementare test automatizzati che simulino la condizione di errore (chaos engineering)
- Escalare il problema a livello architetturale se le correzioni puntuali non sono sufficienti
- Considerare l'adozione di pattern di resilienza: circuit breaker, bulkhead, retry with backoff, fallback

### Problema: Perdita di Contesto durante Incident Response

**Sintomi**: durante gli incidenti, il team fatica a coordinarsi, le informazioni si perdono, le azioni si sovrappongono.

**Diagnosi e Risoluzione**:
- Definire e addestrare i ruoli di incident response (IC, Communications Lead, Technical Lead)
- Utilizzare un canale di comunicazione dedicato e strutturato per ogni incidente
- Nominare sempre uno scribe che documenti in tempo reale la timeline
- Implementare un processo formale di handoff quando l'IC o i tecnici cambiano turno
- Preparare template pre-compilati per le comunicazioni standard
- Condurre esercitazioni periodiche (tabletop exercise, game day) per familiarizzare il team con il processo
- Avere runbook facilmente accessibili e aggiornati per i tipi di incidente piu comuni

---

> **Nota finale**: il monitoraggio e la gestione degli incidenti non sono progetti con una fine definita, ma processi ciclici di miglioramento continuo. Ogni incidente e un'opportunita per rafforzare il sistema di monitoraggio, migliorare i processi di risposta e aumentare la resilienza dell'infrastruttura. La maturita di un'organizzazione IT si misura non dall'assenza di incidenti, ma dalla velocita e dall'efficacia con cui li rileva, li risolve e ne previene la ricorrenza.

---

## SLI, SLO, Error Budget e Multi-Burn-Rate Alerting

### Definizioni Fondamentali

Il framework SLI/SLO/SLA rappresenta il fondamento dell'ingegneria dell'affidabilita (Site Reliability Engineering). Questi concetti, formalizzati da Google e adottati universalmente nell'industria, definiscono un linguaggio comune per misurare, concordare e monitorare l'affidabilita dei servizi.

**Service Level Indicator (SLI)**: misura quantitativa della qualita del servizio dal punto di vista dell'utente. Esempi concreti:

- **Disponibilita**: percentuale di richieste completate con successo rispetto al totale delle richieste. Formula: `richieste_successo / richieste_totali * 100`
- **Latenza**: percentuale di richieste completate entro una soglia di tempo accettabile. Formula: `richieste_sotto_soglia / richieste_totali * 100`
- **Throughput**: capacita del sistema di gestire un volume di richieste adeguato. Formula: `richieste_gestite / richieste_attese * 100`
- **Correttezza**: percentuale di risposte corrette rispetto al totale delle risposte. Formula: `risposte_corrette / risposte_totali * 100`

**Service Level Objective (SLO)**: valore target per un SLI specifico, concordato internamente dall'organizzazione. Lo SLO definisce il livello di affidabilita che il team si impegna a mantenere. Esempi:

- "Il 99.9% delle richieste API deve completarsi con successo" (disponibilita)
- "Il 95% delle richieste deve completarsi in meno di 200ms" (latenza P95)
- "Il 99% delle query al database deve restituire risultati corretti" (correttezza)

**Service Level Agreement (SLA)**: contratto formale tra fornitore e cliente che stabilisce le conseguenze (penali, crediti, rimborsi) in caso di mancato rispetto degli SLO concordati. Lo SLA e sempre meno stringente dello SLO interno: se lo SLO interno e 99.95%, lo SLA contrattuale potrebbe essere 99.9%, lasciando un margine di sicurezza.

### SLO Stratificati per Criticita del Servizio

Non tutti i servizi richiedono lo stesso livello di affidabilita. La strategia consigliata prevede SLO differenziati in base alla criticita aziendale:

| Livello Criticita | SLO Disponibilita | SLO Latenza (P99) | Downtime Mensile Ammesso | Esempi Servizi |
|-------------------|--------------------|--------------------|--------------------------|----------------|
| **Tier 1 - Critico** | 99.99% | < 100ms | 4.3 minuti | Sistemi di pagamento, autenticazione, database primario |
| **Tier 2 - Alto** | 99.9% | < 300ms | 43.8 minuti | API principali, portale clienti, email |
| **Tier 3 - Medio** | 99.5% | < 1s | 3.6 ore | Dashboard interne, sistemi di reportistica |
| **Tier 4 - Basso** | 99.0% | < 3s | 7.3 ore | Ambienti di sviluppo, servizi batch, analytics |

La regola pratica e iniziare con 2-3 SLI per servizio per evitare la complessita eccessiva e l'alert fatigue. Concentrarsi sugli indicatori che hanno impatto diretto sull'esperienza utente.

### Error Budget

L'error budget e il concetto complementare allo SLO: rappresenta la quantita massima di errori o indisponibilita che un servizio puo tollerare senza violare il proprio SLO. Si calcola come:

```
Error Budget = 100% - SLO

Esempio:
SLO = 99.9%
Error Budget = 0.1%
In un mese di 30 giorni:
  Error Budget in minuti = 30 * 24 * 60 * 0.001 = 43.2 minuti
```

L'error budget crea un equilibrio fondamentale tra affidabilita e velocita di innovazione:

- **Error budget disponibile**: il team puo procedere con deployment, sperimentazioni e nuove funzionalita, accettando un rischio calcolato di instabilita temporanea
- **Error budget esaurito o in esaurimento rapido**: il team deve fermare i rilasci non critici e concentrarsi sulla stabilizzazione, sulla correzione dei bug e sul miglioramento dell'affidabilita
- **Error budget costantemente non consumato**: lo SLO potrebbe essere troppo permissivo, oppure il team sta investendo troppo in affidabilita a scapito dell'innovazione

#### Politiche di Error Budget

Le politiche di error budget definiscono le azioni automatiche o manuali da intraprendere in base allo stato del budget:

| Stato Error Budget | Azione | Responsabile |
|--------------------|--------|--------------|
| > 50% disponibile | Operazioni normali, deployment consentiti | Team di sviluppo |
| 25-50% disponibile | Attenzione elevata, revisione dei deployment pianificati | Tech Lead |
| 10-25% disponibile | Sospensione dei deployment non critici, focus su stabilita | Engineering Manager |
| < 10% disponibile | Freeze totale dei rilasci, tutto il team su affidabilita | VP Engineering |
| 0% (SLO violato) | Post-mortem obbligatorio, azioni correttive immediate | Incident Commander + Management |

### Multi-Window Multi-Burn-Rate Alerting

L'approccio tradizionale all'alerting basato su soglie statiche (es. "CPU > 90% per 5 minuti") presenta limiti significativi: non considera il contesto di business, genera falsi positivi e non si adatta al concetto di error budget. L'alerting basato su burn rate risolve questi problemi.

Il **burn rate** indica la velocita con cui si sta consumando l'error budget. Un burn rate di 1 significa che il budget si esaurira esattamente alla fine della finestra SLO (tipicamente 30 giorni). Un burn rate di 10 significa che il budget si esaurira in 3 giorni anziche 30.

```
Burn Rate = (Tasso di Errore Corrente) / (Tasso di Errore Ammesso dallo SLO)

Esempio:
SLO = 99.9% (tasso errore ammesso = 0.1%)
Tasso errore corrente = 0.5%
Burn Rate = 0.5% / 0.1% = 5

Con burn rate 5, l'error budget di 30 giorni si esaurira in 6 giorni.
```

L'approccio **multi-window multi-burn-rate** utilizza finestre temporali di diversa ampiezza per distinguere tra problemi acuti (che richiedono intervento immediato) e degrado lento (che richiede attenzione ma non urgenza):

| Tipo Alert | Burn Rate | Finestra Lunga | Finestra Corta | Tempo Esaurimento Budget | Azione |
|------------|-----------|----------------|----------------|--------------------------|--------|
| **Pagina critica** | 14.4x | 1 ora | 5 minuti | ~2 giorni | Sveglia on-call, intervento immediato |
| **Pagina urgente** | 6x | 6 ore | 30 minuti | ~5 giorni | Notifica on-call, intervento entro 30 min |
| **Ticket prioritario** | 3x | 3 giorni | 6 ore | ~10 giorni | Ticket ad alta priorita, risoluzione in giornata |
| **Ticket informativo** | 1x | 30 giorni | 3 giorni | 30 giorni (budget intero) | Ticket a priorita normale, pianificazione |

La finestra corta serve a evitare falsi positivi: un breve spike di errori che rientra rapidamente non deve generare un alert critico. L'alert si attiva solo se entrambe le finestre indicano un consumo anomalo del budget.

#### Implementazione PromQL per Burn Rate Alert

```yaml
# rules/slo_burn_rate.yml
groups:
  - name: slo_burn_rate_alerts
    rules:
      # Definizione SLO come recording rule
      - record: slo:api_availability:target
        expr: 0.999  # SLO 99.9%

      # Tasso di errore corrente su varie finestre
      - record: slo:api_error_rate:ratio_rate1h
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[1h]))
          /
          sum(rate(http_requests_total[1h]))

      - record: slo:api_error_rate:ratio_rate6h
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[6h]))
          /
          sum(rate(http_requests_total[6h]))

      - record: slo:api_error_rate:ratio_rate3d
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[3d]))
          /
          sum(rate(http_requests_total[3d]))

      # Alert: burn rate critico (14.4x su 1h E 5m)
      - alert: SLOBurnRateCritical
        expr: |
          slo:api_error_rate:ratio_rate1h > (14.4 * (1 - 0.999))
          and
          slo:api_error_rate:ratio_rate5m > (14.4 * (1 - 0.999))
        for: 2m
        labels:
          severity: critical
          slo: api_availability
        annotations:
          summary: "Burn rate critico per API availability"
          description: >
            Il burn rate corrente e {{ $value | humanize }}x.
            A questo ritmo, l'error budget di 30 giorni si esaurira
            in circa 2 giorni. Intervento immediato richiesto.

      # Alert: burn rate elevato (6x su 6h E 30m)
      - alert: SLOBurnRateHigh
        expr: |
          slo:api_error_rate:ratio_rate6h > (6 * (1 - 0.999))
          and
          slo:api_error_rate:ratio_rate30m > (6 * (1 - 0.999))
        for: 5m
        labels:
          severity: warning
          slo: api_availability
        annotations:
          summary: "Burn rate elevato per API availability"
          description: >
            Il burn rate corrente e {{ $value | humanize }}x.
            L'error budget si esaurira in circa 5 giorni.

      # Alert: burn rate sostenuto (3x su 3d E 6h)
      - alert: SLOBurnRateSustained
        expr: |
          slo:api_error_rate:ratio_rate3d > (3 * (1 - 0.999))
          and
          slo:api_error_rate:ratio_rate6h > (3 * (1 - 0.999))
        for: 30m
        labels:
          severity: info
          slo: api_availability
        annotations:
          summary: "Burn rate sostenuto per API availability"
          description: >
            Degrado lento rilevato. L'error budget si esaurira
            in circa 10 giorni al ritmo attuale.
```

#### Dashboard SLO in Grafana

Una dashboard SLO efficace deve includere i seguenti pannelli:

1. **Valore SLI corrente**: gauge che mostra la percentuale di successo attuale rispetto al target SLO
2. **Error budget rimanente**: barra che mostra quanto budget e stato consumato nel periodo corrente (30 giorni rolling)
3. **Burn rate nel tempo**: grafico time-series che mostra l'andamento del burn rate, con soglie di alert visualizzate come linee orizzontali
4. **Storico SLO compliance**: tabella o heatmap che mostra se lo SLO e stato rispettato nei periodi precedenti
5. **Ripartizione errori**: breakdown degli errori per tipo (5xx, timeout, errori applicativi) per facilitare la diagnosi

---

## OpenTelemetry e Observability Unificata

### I Tre Pilastri dell'Osservabilita

L'osservabilita moderna si fonda su tre segnali fondamentali che, correlati tra loro, offrono una visione completa del comportamento dei sistemi:

- **Metriche (Metrics)**: misurazioni numeriche aggregate nel tempo. Rispondono alla domanda "qual e lo stato generale del sistema in questo momento?" Esempi: richieste al secondo, latenza P99, percentuale di errori, utilizzo CPU. Le metriche sono economiche da raccogliere e memorizzare, ideali per dashboard e alerting.

- **Tracce (Traces)**: registrazioni del percorso completo di una richiesta attraverso i componenti di un sistema distribuito. Ogni traccia e composta da span che rappresentano le singole operazioni. Rispondono alla domanda "perche questa specifica richiesta e stata lenta o ha fallito?" Le tracce sono indispensabili in architetture a microservizi dove una richiesta puo attraversare decine di servizi.

- **Log**: registrazioni testuali discrete di eventi con timestamp. Rispondono alla domanda "cosa e successo esattamente in questo momento in questo componente?" I log offrono il massimo dettaglio ma sono i piu costosi da memorizzare e indicizzare.

La chiave dell'osservabilita moderna non e avere i tre segnali separati, ma **correlare** metriche, tracce e log tramite identificatori condivisi. Quando un alert basato su metriche segnala un aumento del tasso di errore, l'operatore deve poter passare immediatamente alle tracce delle richieste fallite, e da ogni traccia ai log dettagliati di ogni componente coinvolto. Questa correlazione si ottiene propagando un `trace_id` univoco attraverso tutti i segnali.

### OpenTelemetry (OTel): lo Standard di Fatto

OpenTelemetry e il framework open-source vendor-neutral per la generazione, raccolta e esportazione di dati di telemetria (tracce, metriche e log). Sviluppato sotto l'egida della Cloud Native Computing Foundation (CNCF), OTel e diventato lo standard di fatto adottato da tutti i principali vendor di osservabilita: Grafana, Datadog, New Relic, Dynatrace, Splunk, Honeycomb e molti altri supportano nativamente il protocollo OTLP (OpenTelemetry Protocol).

#### Componenti Principali

- **SDK**: librerie per ogni linguaggio (Java, Python, Go, .NET, JavaScript, Rust, C++, PHP, Ruby) che instrumentano il codice applicativo, generando tracce, metriche e log. L'instrumentazione puo essere automatica (auto-instrumentation, zero o minime modifiche al codice) o manuale (per logiche custom).

- **OTel Collector**: componente indipendente che riceve, processa e esporta dati di telemetria. Funziona come un pipeline centralizzato con tre stadi:
  - **Receiver**: riceve dati da varie sorgenti (OTLP, Jaeger, Zipkin, Prometheus, syslog, filelog)
  - **Processor**: trasforma i dati (batching, filtraggio, sampling, arricchimento con attributi)
  - **Exporter**: invia i dati verso le destinazioni configurate (Grafana Tempo, Loki, Mimir, Elasticsearch, Jaeger, Datadog, New Relic)

#### Configurazione OTel Collector

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-collector'
          scrape_interval: 10s
          static_configs:
            - targets: ['0.0.0.0:8888']
  filelog:
    include:
      - /var/log/app/*.log
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.time
          layout: '%Y-%m-%dT%H:%M:%S.%LZ'

processors:
  batch:
    timeout: 5s
    send_batch_size: 1024
  memory_limiter:
    limit_mib: 512
    spike_limit_mib: 128
    check_interval: 5s
  attributes:
    actions:
      - key: environment
        value: production
        action: upsert
  resource:
    attributes:
      - key: service.namespace
        value: infrastruttura-aziendale
        action: upsert

exporters:
  otlp/tempo:
    endpoint: "tempo:4317"
    tls:
      insecure: true
  loki:
    endpoint: "http://loki:3100/loki/api/v1/push"
  prometheusremotewrite:
    endpoint: "http://mimir:9009/api/v1/push"
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, attributes]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp, filelog]
      processors: [memory_limiter, batch, resource]
      exporters: [loki]
```

### Lo Stack LGTM (Loki, Grafana, Tempo, Mimir)

Lo stack LGTM di Grafana Labs rappresenta la soluzione open-source piu completa per l'osservabilita unificata. Ogni componente e ottimizzato per un tipo di segnale specifico:

- **Loki** (Log): sistema di aggregazione log con architettura index-free. A differenza di Elasticsearch, Loki non indicizza il contenuto dei log ma solo le label, riducendo i costi di storage fino a 10x. I log vengono compressi in chunk temporali e interrogati con LogQL. Supporta multi-tenancy nativa.

- **Tempo** (Tracce): backend di tracing distribuito che memorizza le tracce come span immutabili senza indicizzazione, consentendo lookup a tempo costante tramite trace ID e campionamento probabilistico per carichi di miliardi di span al giorno. Compatibile con i formati Jaeger, Zipkin e OTLP.

- **Mimir** (Metriche): sistema di storage metriche che scala Prometheus orizzontalmente tramite sharding basato su ring e compattazione su object storage. Supporta multi-tenancy, alta disponibilita e retention a lungo termine. Compatibile al 100% con PromQL.

- **Grafana** (Visualizzazione): piattaforma di dashboard che si connette a tutti e tre i backend, permettendo di navigare fluidamente tra metriche, tracce e log. La funzionalita chiave e il "drill-down correlato": da un pannello metrica si passa alle tracce del periodo anomalo, da una traccia ai log dei servizi coinvolti.

#### Deployment Docker Compose dello Stack LGTM

```yaml
# docker-compose-lgtm.yml
version: "3.8"
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.100.0
    volumes:
      - ./otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
    depends_on:
      - tempo
      - loki
      - mimir

  tempo:
    image: grafana/tempo:2.6.0
    volumes:
      - ./tempo-config.yaml:/etc/tempo/config.yaml
      - tempo-data:/var/tempo
    ports:
      - "3200:3200"   # API Tempo
    command: ["-config.file=/etc/tempo/config.yaml"]

  loki:
    image: grafana/loki:3.2.0
    volumes:
      - ./loki-config.yaml:/etc/loki/config.yaml
      - loki-data:/loki
    ports:
      - "3100:3100"   # API Loki
    command: ["-config.file=/etc/loki/config.yaml"]

  mimir:
    image: grafana/mimir:2.14.0
    volumes:
      - ./mimir-config.yaml:/etc/mimir/config.yaml
      - mimir-data:/data
    ports:
      - "9009:9009"   # API Mimir
    command: ["-config.file=/etc/mimir/config.yaml"]

  grafana:
    image: grafana/grafana:11.2.0
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - ./grafana-datasources.yaml:/etc/grafana/provisioning/datasources/datasources.yaml
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - tempo
      - loki
      - mimir

volumes:
  tempo-data:
  loki-data:
  mimir-data:
  grafana-data:
```

#### Correlazione dei Segnali nella Pratica

La correlazione tra i tre segnali avviene tramite il `trace_id`, un identificatore univoco generato all'inizio di ogni richiesta e propagato attraverso tutti i componenti. In Grafana, questa correlazione si configura tramite i data source:

```yaml
# grafana-datasources.yaml
apiVersion: 1
datasources:
  - name: Mimir
    type: prometheus
    url: http://mimir:9009/prometheus
    jsonData:
      exemplarTraceIdDestinations:
        - name: traceID
          datasourceUid: tempo

  - name: Tempo
    type: tempo
    uid: tempo
    url: http://tempo:3200
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        filterByTraceID: true
        filterBySpanID: true
      tracesToMetrics:
        datasourceUid: mimir
      serviceMap:
        datasourceUid: mimir

  - name: Loki
    type: loki
    url: http://loki:3100
    jsonData:
      derivedFields:
        - name: TraceID
          matcherRegex: "trace_id=(\\w+)"
          url: "${__value.raw}"
          datasourceUid: tempo
```

Con questa configurazione, l'operatore puo seguire il flusso investigativo completo: un alert su metrica (aumento errori 5xx in Mimir) porta direttamente alle tracce delle richieste fallite (in Tempo), e da ogni span della traccia si accede ai log dettagliati (in Loki) del servizio che ha generato l'errore.

---

## Checkmk: Approfondimento

### Architettura e Modello di Funzionamento

Checkmk e un sistema di monitoraggio ibrido che combina agent-based e agentless monitoring con un'enfasi sulla configurazione automatizzata. Nato come estensione di Nagios, si e evoluto in una piattaforma indipendente con il proprio core di monitoraggio (CMC, Checkmk Micro Core) che offre prestazioni significativamente superiori rispetto al core Nagios originale.

Checkmk e disponibile in tre edizioni:

- **Checkmk Raw**: open-source (GPLv2), basata sul core Nagios, include oltre 2.000 plugin di monitoraggio. Adatta per piccole e medie infrastrutture.
- **Checkmk Enterprise**: licenza commerciale, include il CMC ad alte prestazioni, agent bakery per la distribuzione automatizzata degli agent, reporting avanzato, clustering e supporto tecnico.
- **Checkmk Cloud**: versione ottimizzata per ambienti cloud con monitoraggio nativo di AWS, Azure e GCP, auto-discovery dei servizi cloud, e dashboard specifiche.

#### Installazione e Auto-Discovery

L'installazione di Checkmk segue un approccio basato su "site", dove ogni istanza e un ambiente isolato:

```bash
# Installazione su Debian/Ubuntu
wget https://download.checkmk.com/checkmk/2.3.0p12/check-mk-raw-2.3.0p12_0.jammy_amd64.deb
sudo dpkg -i check-mk-raw-2.3.0p12_0.jammy_amd64.deb
sudo apt-get install -f

# Creazione di un site
sudo omd create monitoring
sudo omd start monitoring

# Accesso web: http://server/monitoring
# Credenziali iniziali mostrate durante la creazione del site
```

Il punto di forza di Checkmk e l'auto-discovery: una volta aggiunto un host e installato l'agent, Checkmk scopre automaticamente tutti i servizi monitorabili (filesystem, interfacce di rete, processi, database, container) e propone la configurazione ottimale. L'operatore deve solo confermare o personalizzare.

#### Rule-Based Configuration

A differenza di Zabbix (basato su template) e Prometheus (basato su file YAML), Checkmk utilizza un sistema di regole gerarchiche: le regole si applicano in base a cartelle, tag degli host, label e condizioni. Questo approccio consente di gestire eccezioni senza duplicare la configurazione:

```
Regola globale: "Soglia disco Warning = 80%, Critical = 90%"
  └── Eccezione per cartella "Database Servers": "Soglia disco Warning = 70%, Critical = 85%"
      └── Eccezione per host "db-archive-01": "Soglia disco Warning = 90%, Critical = 95%"
```

#### Notifiche e Integrazione

Checkmk supporta notifiche tramite email, SMS, Slack, Teams, PagerDuty, OpsGenie, e webhook personalizzati. Il sistema di notifiche basato su regole permette di configurare chi riceve quale notifica in base a host, servizio, severita, orario e ruolo dell'utente.

---

## PRTG Network Monitor: Approfondimento

### Modello a Sensori

PRTG utilizza un modello di licenza basato su sensori, dove ogni metrica monitorata corrisponde a un sensore. Un singolo server Windows monitorato con CPU, memoria, disco e interfacce di rete puo consumare 15-30 sensori. Questo modello rende PRTG estremamente semplice da comprendere e prevedere in termini di costi, ma puo diventare oneroso per infrastrutture di grandi dimensioni.

L'architettura si compone di:

- **PRTG Core Server**: componente centrale che gestisce la configurazione, i dati e l'interfaccia web. Funziona esclusivamente su Windows Server.
- **PRTG Probe**: componente distribuito che esegue il monitoraggio effettivo. Il Core Server include una Local Probe; Remote Probe aggiuntive possono essere installate su siti remoti per il monitoraggio distribuito.
- **Sensori**: le unita fondamentali di monitoraggio. PRTG include oltre 250 tipi di sensori pre-configurati per SNMP, WMI, SSH, HTTP, database, cloud e molto altro.

### Configurazione e Auto-Discovery

PRTG si distingue per la facilita di setup iniziale. L'auto-discovery basata su range IP o segmenti di rete individua automaticamente i dispositivi e propone i sensori appropriati:

```
1. Installazione: wizard grafico, completamento in 15-20 minuti
2. Auto-Discovery: scansione della rete, identificazione dispositivi
3. Aggiunta sensori: proposta automatica basata sul tipo di dispositivo
4. Personalizzazione: soglie, notifiche, dashboard
```

#### Tipi di Sensori Principali

| Categoria | Sensori Chiave | Protocollo |
|-----------|---------------|------------|
| **Rete** | Ping, SNMP Traffic, Packet Sniffer, NetFlow/sFlow | ICMP, SNMP, Flow |
| **Server Windows** | CPU, Memoria, Disco, Servizi, Event Log, Performance Counter | WMI, SNMP |
| **Server Linux** | SSH Script, SNMP Linux, SSH Disk Space | SSH, SNMP |
| **Web** | HTTP, HTTP Content, SSL Certificate, REST API | HTTP/HTTPS |
| **Database** | SQL Server, MySQL, PostgreSQL, Oracle | Nativo/ODBC |
| **Cloud** | AWS CloudWatch, Azure Monitor, Office 365 | API REST |
| **Virtualizzazione** | VMware vCenter, Hyper-V, Citrix XenServer | API nativa |

#### Mappe e Reporting

PRTG offre mappe interattive personalizzabili dove e possibile posizionare i sensori su planimetrie, diagrammi di rete o rappresentazioni geografiche. Il sistema di reporting genera automaticamente report HTML e PDF con grafici storici, tabelle di disponibilita e analisi delle tendenze, utili per la presentazione al management e per la documentazione della conformita SLA.

#### Limiti e Considerazioni

Il principale limite di PRTG e il costo a scalare: per infrastrutture con migliaia di dispositivi, il costo per sensore diventa significativo. Inoltre, il Core Server funziona solo su Windows, il che puo essere un vincolo in ambienti prevalentemente Linux. Per infrastrutture di grandi dimensioni, Zabbix o Checkmk offrono un rapporto costo-funzionalita migliore.

---

## Piattaforme di Incident Management

### PagerDuty

PagerDuty e la piattaforma leader di mercato per la gestione degli incidenti e l'orchestrazione on-call. Le funzionalita principali includono:

- **On-Call Scheduling**: gestione delle rotazioni, override temporanei, schedule multi-livello con rotazioni primarie e secondarie
- **Escalation Policies**: definizione automatica di chi contattare e dopo quanto tempo in caso di mancata risposta
- **Event Intelligence**: raggruppamento automatico degli alert correlati, riduzione del rumore fino al 90%
- **Incident Workflows**: automazione delle azioni di risposta tramite workflow personalizzabili
- **Status Dashboard**: pagina di stato interna per la visibilita sugli incidenti in corso

#### Configurazione Escalation Policy in PagerDuty

Una policy di escalation tipica per un servizio critico:

```
Livello 1 (0 min): Notifica l'ingegnere on-call primario
  - Canali: Push notification + SMS + Telefono
  - Timeout: 5 minuti

Livello 2 (5 min): Se nessun ACK, notifica il backup on-call
  - Canali: Push notification + SMS + Telefono
  - Timeout: 10 minuti

Livello 3 (15 min): Se nessun ACK, notifica il Team Lead
  - Canali: Telefono + SMS + Email
  - Timeout: 15 minuti

Livello 4 (30 min): Se nessun ACK, notifica il CTO
  - Canali: Telefono
  - Loop: Ripetere dal Livello 1
```

#### Integrazione PagerDuty con Alertmanager

```yaml
# In alertmanager.yml
receivers:
  - name: 'pagerduty-infrastruttura'
    pagerduty_configs:
      - routing_key: 'ROUTING_KEY_SERVIZIO'
        severity: '{{ .CommonLabels.severity }}'
        description: '{{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'
          num_alerts: '{{ .Alerts | len }}'
        links:
          - href: 'https://grafana.esempio.it/d/dashboard-id'
            text: 'Dashboard Grafana'
          - href: 'https://wiki.esempio.it/runbook/{{ .CommonLabels.alertname }}'
            text: 'Runbook'
```

### OpsGenie (Atlassian)

OpsGenie, parte dell'ecosistema Atlassian, offre funzionalita simili a PagerDuty con forte integrazione con Jira, Confluence e Statuspage. Le caratteristiche distintive:

- **Integrazione Jira bidirezionale**: creazione automatica di ticket Jira dagli incidenti, sincronizzazione dello stato
- **Team Routing**: instradamento degli alert basato su team, non solo su singoli individui
- **Heartbeat Monitoring**: verifica che i sistemi di monitoraggio stessi siano operativi, inviando alert se un heartbeat manca
- **Incident Timeline**: timeline interattiva degli eventi dell'incidente per il post-mortem

### Grafana OnCall (Open-Source)

Grafana OnCall e l'alternativa open-source per la gestione on-call, integrata nativamente nello stack Grafana:

- **Schedule Management**: rotazioni, override, sincronizzazione con Google Calendar
- **Escalation Chains**: catene di escalation configurabili con delay, condizioni e azioni
- **ChatOps Nativo**: integrazione bidirezionale con Slack e Microsoft Teams
- **Alertmanager Integration**: ricezione diretta degli alert da Prometheus Alertmanager

```yaml
# Esempio escalation chain Grafana OnCall
Passaggio 1: Notifica utenti del gruppo on-call corrente
  - Metodo: SMS + Push + Slack DM
  - Attesa: 5 minuti

Passaggio 2: Se nessun ACK, ripetere passaggio 1

Passaggio 3: Se nessun ACK dopo 10 minuti, notifica il manager
  - Metodo: Telefono + SMS
  - Attesa: 10 minuti

Passaggio 4: Se nessun ACK, dichiara l'incidente come "Unacknowledged"
  - Azione: Post su canale Slack #incidents
  - Azione: Creazione ticket Jira automatica
```

### Gestione della Rotazione On-Call: Buone Pratiche

La rotazione on-call e uno degli aspetti piu delicati della gestione operativa. Una rotazione mal gestita porta al burnout del team, alla diminuzione della qualita della risposta e all'aumento del turnover del personale. Le buone pratiche consolidate includono:

**Durata della rotazione**: le rotazioni settimanali sono le piu comuni e offrono il miglior equilibrio tra continuita e distribuzione del carico. Rotazioni giornaliere sono preferibili per team numerosi (8+ persone) dove si vuole distribuire il carico piu uniformemente. Rotazioni bisettimanali sono accettabili solo per servizi con basso volume di alert.

**Dimensione del team on-call**: il minimo raccomandato e di 6 persone per garantire che ogni individuo sia on-call non piu di una settimana su sei. Il Google SRE Workbook raccomanda un massimo di 2-3 incidenti azionabili per turno come baseline sostenibile. Se il team riceve costantemente 8-10 alert per turno, il problema e nell'alerting, non nell'on-call.

**Handoff strutturato**: ogni transizione tra turni deve includere una riunione di 30 minuti (massimo) dove l'ingegnere uscente e quello entrante revisionano:

- Incidenti attivi e il loro stato corrente
- Alert silenziati e la motivazione
- Modifiche infrastrutturali pianificate nei prossimi giorni
- Rischi noti o aree di attenzione

**Compensazione**: il servizio di reperibilita deve essere compensato equamente, sia con retribuzione aggiuntiva sia con giorni di riposo compensativo. La percezione di equita nella distribuzione del carico on-call e cruciale per il morale del team.

**Revisione periodica**: analizzare trimestralmente le statistiche on-call: numero di alert per turno, orario degli alert (quanti di notte), tempo medio di acknowledgement, falsi positivi. Utilizzare questi dati per migliorare l'alerting e bilanciare il carico.

---

## ChatOps e Automazione della Risposta agli Incidenti

### ChatOps per l'Incident Management

ChatOps e l'approccio che centralizza la comunicazione e l'automazione operativa all'interno delle piattaforme di messaggistica (Slack, Microsoft Teams). Nell'ambito dell'incident management, ChatOps trasforma i canali di chat in centri di comando dove le azioni operative vengono eseguite direttamente dalla conversazione, garantendo trasparenza, tracciabilita e velocita.

#### Vantaggi del ChatOps nell'Incident Response

- **Contesto condiviso**: tutti i partecipanti vedono le stesse informazioni in tempo reale, eliminando la necessita di aggiornamenti separati
- **Tracciabilita automatica**: ogni azione eseguita dalla chat viene registrata automaticamente, facilitando il post-mortem
- **Riduzione del context switching**: l'ingegnere non deve passare tra terminale, dashboard e chat, ma opera da un'unica interfaccia
- **Onboarding accelerato**: i nuovi membri del team possono osservare come gli incidenti vengono gestiti leggendo i canali storici

#### Workflow ChatOps Tipico per un Incidente

```
1. Alert critico ricevuto da PagerDuty/OpsGenie
2. Bot crea automaticamente un canale Slack dedicato:
   #inc-2026-0524-api-timeout
3. Bot invita automaticamente:
   - Ingegnere on-call (da rotazione)
   - Team lead del servizio impattato
   - Communications lead
4. Bot posta nel canale:
   - Dettagli dell'alert (servizio, severita, metriche)
   - Link alla dashboard Grafana rilevante
   - Link al runbook per il tipo di incidente
   - Template per gli aggiornamenti di stato
5. L'IC dichiara i ruoli nel canale:
   "/incident role @mario technical-lead"
   "/incident role @giulia communications"
6. Aggiornamenti di stato tramite comandi bot:
   "/incident status investigating"
   "/incident update 'Causa identificata: connection pool esaurito su db-replica-02'"
7. Risoluzione:
   "/incident resolve 'Pool DB aumentato da 100 a 200 connessioni, deployment completato'"
8. Bot genera automaticamente la bozza del post-mortem con la timeline dal canale
```

### Runbook Automation

I runbook sono documenti operativi che descrivono, passo per passo, le procedure da seguire per diagnosticare e risolvere problemi specifici. L'automazione dei runbook porta questo concetto a un livello superiore, trasformando le procedure manuali in workflow eseguibili.

#### Struttura di un Runbook Operativo

Ogni runbook deve seguire una struttura standardizzata:

```markdown
# Runbook: [Nome Alert / Tipo Incidente]
**Ultimo aggiornamento**: [YYYY-MM-DD]
**Autore**: [Nome]
**Servizio**: [Nome servizio]
**Severita tipica**: [SEV1-SEV4]

## Descrizione
[Cosa significa questo alert / tipo di incidente]

## Impatto
[Che cosa percepisce l'utente finale]

## Prerequisiti
- Accesso SSH ai server [elenco]
- Accesso alla dashboard [link]
- Credenziali per [servizio] (nel vault: [percorso])

## Diagnosi
1. Verificare [cosa] con il comando:
   ```
   [comando specifico da eseguire]
   ```
   Output atteso: [descrizione]

2. Controllare [cosa] nella dashboard:
   [link specifico alla dashboard]

3. Analizzare i log:
   ```
   [query LogQL / Kibana specifica]
   ```

## Risoluzione
### Scenario A: [Descrizione causa]
1. [Azione specifica con comando]
2. [Verifica con comando]
3. [Conferma risoluzione]

### Scenario B: [Descrizione causa alternativa]
1. [Azione specifica]
2. [Verifica]

## Escalation
Se nessuno scenario risolve il problema entro [tempo]:
- Contattare: [nome/ruolo] tramite [canale]
- Informazioni da fornire: [elenco]

## Post-Risoluzione
- [ ] Verificare che le metriche tornino alla baseline entro 15 minuti
- [ ] Aggiornare il canale incidente con la risoluzione
- [ ] Determinare se e necessario un post-mortem
```

### Auto-Remediation

L'auto-remediation e l'esecuzione automatica di azioni correttive in risposta a problemi noti e ricorrenti. L'automazione e appropriata solo per scenari ben compresi, deterministici e con rischio limitato.

#### Scenari Adatti all'Auto-Remediation

| Scenario | Azione Automatica | Safeguard |
|----------|-------------------|-----------|
| Spazio disco > 90% | Pulizia log vecchi, rotazione, svuotamento temp | Non eliminare mai log < 24h, notificare il team |
| Servizio crashato | Riavvio automatico tramite systemd/supervisor | Massimo 3 riavvii in 15 minuti, poi escalation |
| Certificato SSL < 14 giorni | Rinnovo automatico via certbot/ACME | Notificare il team, verificare il rinnovo |
| Connection pool esaurito | Restart controllato dell'applicazione | Solo fuori orario di picco, notificare |
| Pod Kubernetes in CrashLoopBackOff | Rollback al deployment precedente | Solo se il deployment precedente era healthy |

#### Scenari NON Adatti all'Auto-Remediation

- Corruzione dati o inconsistenze nel database
- Problemi di sicurezza o accessi non autorizzati
- Errori di logica applicativa
- Problemi di rete complessi con cause multiple
- Qualsiasi scenario non completamente compreso e testato

La regola fondamentale dell'auto-remediation e: **l'automazione deve diagnosticare, non indovinare**. Se l'azione automatica ha una probabilita non trascurabile di peggiorare la situazione, richiede supervisione umana. Le piattaforme moderne implementano il pattern "human-in-the-loop": l'automazione identifica il problema e propone l'azione, ma attende la conferma umana prima di eseguirla per gli scenari a rischio elevato.

#### Esempio Auto-Remediation con Alertmanager Webhook

```yaml
# alertmanager.yml - webhook per auto-remediation
receivers:
  - name: 'auto-remediation'
    webhook_configs:
      - url: 'http://remediation-service:8080/api/v1/remediate'
        send_resolved: true
        max_alerts: 10

route:
  routes:
    - match:
        severity: warning
        auto_remediate: "true"
      receiver: 'auto-remediation'
      group_wait: 30s
      repeat_interval: 30m
```

```python
# remediation-service: esempio semplificato
# ATTENZIONE: in produzione aggiungere autenticazione,
# autorizzazione, audit logging e circuit breaker

import subprocess
import logging

REMEDIATION_MAP = {
    "DiskSpaceLow": {
        "command": ["bash", "/opt/remediation/cleanup-disk.sh"],
        "max_retries": 1,
        "human_approval_required": False,
    },
    "ServiceDown": {
        "command": ["systemctl", "restart", "{service_name}"],
        "max_retries": 3,
        "cooldown_seconds": 300,
        "human_approval_required": False,
    },
    "DatabaseConnectionPoolExhausted": {
        "command": ["bash", "/opt/remediation/restart-app.sh"],
        "max_retries": 1,
        "human_approval_required": True,  # Richiede conferma umana
    },
}
```

---

## Chaos Engineering e Game Day

### Fondamenti del Chaos Engineering

Il chaos engineering e la disciplina che consiste nell'introdurre deliberatamente guasti controllati nei sistemi per verificarne la resilienza e scoprire debolezze prima che si manifestino in produzione sotto forma di incidenti reali. Il principio fondamentale e semplice: se un sistema non e stato testato sotto stress, non si puo sapere come si comportera quando lo stress arrivera inevitabilmente.

Il processo segue un ciclo strutturato:

1. **Definire lo stato stabile**: identificare le metriche che indicano il funzionamento normale del sistema (latenza, throughput, tasso di errore, disponibilita)
2. **Formulare un'ipotesi**: "Se il database primario diventa irraggiungibile, il sistema effettuera il failover sul secondario entro 30 secondi senza perdita di richieste"
3. **Progettare l'esperimento**: definire il tipo di guasto da iniettare, la durata, il blast radius (porzione del sistema impattata) e i criteri di interruzione automatica (abort conditions)
4. **Eseguire l'esperimento**: iniettare il guasto in un ambiente controllato, monitorando attentamente tutte le metriche
5. **Analizzare i risultati**: confrontare il comportamento osservato con l'ipotesi, identificare le divergenze
6. **Implementare miglioramenti**: correggere le debolezze scoperte, migliorare i runbook, aggiornare gli alert
7. **Iterare**: ripetere con scenari progressivamente piu complessi

### Strumenti di Chaos Engineering

| Strumento | Ambiente | Licenza | Caratteristiche Principali |
|-----------|----------|---------|---------------------------|
| **Gremlin** | Cloud, Bare-metal, Container | Commerciale | Interfaccia intuitiva, ampia libreria di attacchi, safety controls avanzati, reporting dettagliato |
| **Litmus** | Kubernetes | Open-source (Apache 2.0) | CNCF project, ChaosHub con esperimenti predefiniti, integrazione CI/CD nativa, GitOps-driven |
| **Chaos Monkey** | Cloud (AWS) | Open-source (Apache 2.0) | Pioniere del chaos engineering (Netflix), terminazione casuale di istanze |
| **AWS Fault Injection Service** | AWS | Incluso in AWS | Integrazione nativa con servizi AWS, esperimenti su EC2, ECS, EKS, RDS |
| **Azure Chaos Studio** | Azure | Incluso in Azure | Integrazione nativa con servizi Azure, fault library estesa |
| **Pumba** | Docker | Open-source (Apache 2.0) | Chaos testing per container Docker: kill, pause, network delay/loss |
| **tc + iptables** | Linux | Incluso nel kernel | Simulazione di latenza, packet loss, partizioni di rete a livello di sistema operativo |

### Tipi di Guasti da Iniettare

#### Guasti Infrastrutturali

- **Terminazione di istanze/server**: verifica che il sistema gestisca la perdita di un nodo senza interruzione del servizio
- **Saturazione CPU**: verifica il comportamento sotto carico estremo, la capacita di auto-scaling e i timeout
- **Esaurimento memoria**: verifica il comportamento dell'OOM killer, la resilienza delle applicazioni
- **Esaurimento disco**: verifica gli alert, i meccanismi di pulizia automatica, il comportamento dei database

#### Guasti di Rete

- **Latenza artificiale**: aggiunta di ritardo alle comunicazioni tra servizi per verificare i timeout e i retry
- **Packet loss**: perdita di pacchetti per verificare il comportamento dei protocolli di comunicazione
- **Partizione di rete**: isolamento di un segmento di rete per verificare il comportamento dei sistemi distribuiti (split-brain)
- **DNS failure**: interruzione della risoluzione DNS per verificare la resilienza della service discovery

#### Guasti Applicativi

- **Terminazione di processi**: kill di servizi applicativi per verificare il restart automatico e la gestione del failover
- **Database failover**: simulazione di failover del database primario verso la replica
- **Cache invalidation**: svuotamento della cache per verificare il comportamento sotto cold start
- **Dependency failure**: interruzione di un servizio dipendente per verificare circuit breaker e fallback

### Game Day: Esercitazioni Pianificate

Un Game Day e un evento pianificato durante il quale il team simula scenari di incidente per testare la prontezza delle procedure, degli strumenti e delle persone. A differenza degli esperimenti di chaos engineering automatizzati, il Game Day coinvolge attivamente l'intero team e testa anche i processi umani di comunicazione e coordinamento.

#### Template di Pianificazione Game Day

```markdown
# Game Day Plan
**Data**: [YYYY-MM-DD]
**Orario**: [HH:MM - HH:MM]
**Facilitatore**: [Nome]
**Partecipanti**: [Lista nomi e ruoli]

## Obiettivi
1. Verificare il tempo di failover del database primario
2. Testare la procedura di comunicazione durante incidente SEV1
3. Validare i runbook per lo scenario "database irraggiungibile"

## Pre-Requisiti
- [ ] Backup completo dell'ambiente verificato
- [ ] Tutti i partecipanti informati e disponibili
- [ ] Stakeholder non tecnici informati (per evitare panico)
- [ ] Abort criteria definiti e condivisi
- [ ] Canale di comunicazione di emergenza configurato
- [ ] Rollback plan documentato e testato

## Scenario
Alle ore [HH:MM], il facilitatore simulera l'irraggiungibilita
del database primario PostgreSQL (db-prod-01) interrompendo
la connettivita di rete del server.

## Metriche da Osservare
- Tempo di rilevazione dell'alert (target: < 2 min)
- Tempo di failover automatico alla replica (target: < 30 sec)
- Tempo di notifica al team on-call (target: < 1 min)
- Impatto sulle richieste utente (target: < 5% errori)
- Tempo di ripristino completo (target: < 15 min)

## Abort Criteria
Interrompere immediatamente l'esercitazione se:
- Impatto su ambienti non previsti
- Perdita di dati reali
- Impossibilita di rollback entro 5 minuti
- Incidente reale si sovrappone all'esercitazione

## Debrief
Riunione post-esercitazione entro 1 ora dalla conclusione.
Documentare: cosa ha funzionato, cosa migliorare, action items.
```

#### Frequenza e Maturita

La frequenza delle esercitazioni dipende dal livello di maturita dell'organizzazione:

| Livello Maturita | Frequenza Game Day | Complessita Scenari | Ambiente |
|-------------------|--------------------|---------------------|----------|
| **Iniziale** | Trimestrale | Singolo componente, scenari semplici | Staging/Pre-produzione |
| **Intermedio** | Mensile | Multi-componente, scenari combinati | Staging + Produzione (orari a basso traffico) |
| **Avanzato** | Settimanale (automatizzato) + Mensile (manuale) | Scenari complessi, failure cascade | Produzione (qualsiasi orario) |
| **Elite** | Continuo (chaos automatizzato in CI/CD) + Trimestrale (disaster scenario) | Scenari regionali, multi-datacenter | Produzione (traffico reale) |

Il principio guida e progressivita: iniziare con esperimenti semplici in ambienti controllati e aumentare gradualmente la complessita e il realismo man mano che la fiducia e le capacita del team crescono.

---

## ITIL v4 e Incident Management: Approfondimento

### Evoluzione da ITIL v3 a ITIL v4

ITIL v4, pubblicato nel 2019 e continuamente aggiornato, rappresenta un cambio di paradigma rispetto alla versione precedente. Le differenze principali che impattano l'incident management:

- **Da processi a pratiche**: ITIL v4 definisce 34 pratiche (non piu "processi"), riconoscendo che l'incident management non e un flusso rigido ma un insieme di attivita, risorse e competenze che si adattano al contesto
- **Integrazione con DevOps e Agile**: ITIL v4 non e piu in contrasto con le metodologie agili, ma le integra esplicitamente. Il concetto di "shift-left" (spostare la capacita di risoluzione piu vicino al punto di rilevazione) e pienamente abbracciato
- **Focus sulla co-creazione di valore**: l'obiettivo non e solo "ripristinare il servizio" ma "minimizzare l'impatto negativo sull'utente e sul valore aziendale"
- **Service Value System (SVS)**: l'incident management e una pratica all'interno del SVS, collegata a change management, problem management, knowledge management e continual improvement

### Knowledge Management nell'Incident Response

ITIL v4 enfatizza il ruolo della gestione della conoscenza nell'accelerare la risoluzione degli incidenti. Il principio e semplice: se un problema e gia stato risolto in passato, la soluzione deve essere immediatamente accessibile a chiunque affronti lo stesso problema.

#### Knowledge Base Operativa

Una knowledge base efficace per l'incident management deve includere:

- **Known Error Database (KEDB)**: errori noti con workaround documentati, collegati ai Configuration Item (CI) interessati
- **Runbook library**: raccolta organizzata e aggiornata dei runbook operativi, indicizzata per servizio e tipo di alert
- **Post-mortem archive**: archivio ricercabile di tutte le Post-Incident Review, con tagging per causa radice, servizi coinvolti e azioni correttive
- **FAQ tecniche**: risposte rapide alle domande piu frequenti del team operativo

Il ciclo di vita della conoscenza nell'incident management:

```
Incidente → Risoluzione → Documentazione → Revisione → Pubblicazione
     ↑                                                        |
     └─── Consultazione durante il prossimo incidente ←───────┘
```

Ogni risoluzione di incidente che non alimenta la knowledge base e un'opportunita di apprendimento persa. Il team deve dedicare tempo alla documentazione post-risoluzione come parte integrante del processo di incident management, non come attivita opzionale.

### Continual Improvement e Metriche di Maturita

ITIL v4 collega l'incident management al modello di miglioramento continuo attraverso metriche specifiche che indicano la maturita del processo:

| Metrica | Formula | Target Iniziale | Target Maturo |
|---------|---------|-----------------|---------------|
| **MTTD** (Mean Time To Detect) | Media(timestamp_alert - timestamp_inizio_problema) | < 15 minuti | < 2 minuti |
| **MTTA** (Mean Time To Acknowledge) | Media(timestamp_ack - timestamp_alert) | < 15 minuti | < 3 minuti |
| **MTTR** (Mean Time To Resolve) | Media(timestamp_risoluzione - timestamp_alert) | < 4 ore (SEV1) | < 1 ora (SEV1) |
| **MTTF** (Mean Time To Failure) | Media(timestamp_prossimo_incidente - timestamp_risoluzione_precedente) | Crescente nel tempo | Crescente nel tempo |
| **Tasso di Ricorrenza** | Incidenti_ricorrenti / Incidenti_totali | < 20% | < 5% |
| **First Contact Resolution** | Incidenti_risolti_L1 / Incidenti_totali | > 40% | > 70% |
| **SLO Compliance** | Periodi_in_SLO / Periodi_totali | > 95% | > 99% |
| **Action Item Completion Rate** | Action_items_completati / Action_items_totali | > 60% | > 90% |
| **Alert-to-Incident Ratio** | Alert_totali / Incidenti_reali | < 20:1 | < 5:1 |

Queste metriche devono essere tracciate nel tempo e presentate in report mensili o trimestrali per evidenziare i trend di miglioramento o regressione. Un processo di incident management maturo mostra un MTTR in diminuzione, un MTTF in crescita e un tasso di ricorrenza in calo.

### Processo di Major Incident in ITIL v4

ITIL v4 distingue tra incidenti normali e major incident (incidenti gravi), prevedendo per questi ultimi un processo dedicato con caratteristiche specifiche:

- **Attivazione immediata**: un major incident bypassa le code di supporto L1 e viene immediatamente escalato al team dedicato
- **Incident Commander designato**: un singolo punto di coordinamento con autorita decisionale durante l'incidente
- **Comunicazione proattiva**: aggiornamenti regolari a tutti gli stakeholder, inclusi clienti e management, secondo un ritmo predefinito
- **Priorita alla ripristino**: l'obiettivo primario e ristabilire il servizio, anche con soluzioni temporanee (workaround); l'analisi della causa radice avviene dopo
- **Post-Incident Review obbligatoria**: ogni major incident genera una PIR entro 48-72 ore dalla risoluzione, con partecipazione di tutti i team coinvolti

Il processo formale per un major incident:

```
Rilevazione
  → Classificazione come Major Incident (criteri predefiniti)
    → Attivazione del Major Incident Manager (IC)
      → Convocazione del team di risposta
        → Apertura canale di comunicazione dedicato
          → Ciclo: Diagnosi → Azione → Verifica → Comunicazione
            → Risoluzione confermata
              → Chiusura canale, notifica stakeholder
                → PIR entro 48-72 ore
                  → Action items tracciati e assegnati
                    → Chiusura formale solo dopo completamento AI
```

### Relazione con Problem Management

ITIL v4 distingue nettamente tra incident management e problem management:

- **Incident management**: reattivo, focalizzato sul ripristino rapido del servizio. "Il servizio e giu, ripristiniamolo."
- **Problem management**: proattivo e investigativo, focalizzato sull'eliminazione della causa radice. "Perche il servizio e andato giu e come impedire che accada di nuovo?"

Un incidente puo generare un problema (problem record) quando:

- L'incidente si ripete (ricorrenza)
- La causa radice non e stata identificata durante l'incidente
- Il workaround applicato e temporaneo e necessita di una correzione permanente
- L'analisi post-mortem rivela una debolezza sistemica

Il problem management alimenta il KEDB con gli errori noti e i workaround, che a loro volta accelerano la risoluzione degli incidenti futuri. Questo ciclo virtuoso tra incident e problem management e uno dei pilastri della maturita operativa ITIL.

---

### AIOps e Incident Management Predittivo: Evoluzione 2025-2026

Il panorama dell'incident management e dell'observability sta attraversando una trasformazione radicale guidata dall'adozione crescente dell'intelligenza artificiale per le operazioni IT (AIOps). Il mercato AIOps, stimato a 11,08 miliardi di dollari nel 2025, e' proiettato a raggiungere i 14,44 miliardi nel 2026 con un tasso di crescita annuo composto del 30,2%, a conferma dell'accelerazione nell'adozione di queste tecnologie a livello enterprise.

**Dalla correlazione reattiva all'observability predittiva.** Il cambiamento piu' significativo nel 2025-2026 e' il passaggio dalla tradizionale correlazione reattiva dei log a una vera observability predittiva. Le piattaforme moderne integrano modelli di intelligenza artificiale causale e ragionamento neuro-simbolico che consentono non soltanto di rilevare anomalie, ma di comprendere il motivo per cui si verificano. Questo approccio riduce drasticamente il Mean Time To Detect (MTTD) e, in molti casi, consente di intervenire prima che un'anomalia si trasformi in un incidente visibile agli utenti. Le organizzazioni stanno abbandonando il monitoraggio puramente reattivo a favore di operazioni IT predittive, rilevando pattern precoci, riducendo il carico operativo sui team e supportando ambienti ibridi e multi-cloud sempre piu' complessi.

**Sistemi autonomi e self-healing.** Secondo le previsioni di Gartner, entro il 2026 oltre il 60% delle grandi organizzazioni avra' implementato sistemi self-healing alimentati da piattaforme AIOps. L'evoluzione procede dalla semplice rilevazione e raccomandazione verso sistemi capaci di diagnosticare problemi, attivare azioni correttive approvate, verificare gli esiti e migliorare nel tempo sulla base dei risultati. Questo passaggio dall'automazione basica a operazioni intelligenti a ciclo chiuso (closed-loop) riduce significativamente l'intervento manuale nella gestione degli incidenti di routine. Un esempio concreto: quando una piattaforma AIOps rileva un incremento anomalo della latenza su un microservizio, puo' automaticamente scalare le risorse, ridirigere il traffico e aprire un ticket di follow-up, il tutto senza intervento umano e in tempi dell'ordine di secondi anziche' minuti.

**Event Intelligence e riclassificazione del mercato.** Gartner ha riformulato nel 2025 la categoria di mercato "AIOps Platforms" come "Event Intelligence Solutions", citando l'uso eccessivo del termine AIOps da parte dei vendor, la confusione risultante e la disillusione tra i leader dell'infrastruttura e delle operazioni. Questa riclassificazione riflette una maturazione del settore: le piattaforme di event intelligence si concentrano sulla correlazione intelligente degli eventi, sulla riduzione del rumore (noise reduction) e sulla prioritizzazione automatica degli incidenti. Per i team operativi, la distinzione e' importante: non si tratta semplicemente di aggiungere AI al monitoraggio esistente, ma di ripensare l'intero flusso dall'evento grezzo all'azione risolutiva, con l'intelligenza artificiale che funge da tessuto connettivo tra raccolta dati, analisi, decisione e rimedio.

**Agentic AI nell'incident response.** La tendenza piu' recente e' l'adozione di agenti AI autonomi (agentic AI) nel processo di risposta agli incidenti. Questi agenti sono in grado di eseguire indagini preliminari automatizzate: raccogliere log rilevanti, correlare metriche tra servizi interdipendenti, interrogare knowledge base interne e proporre ipotesi sulla causa radice, tutto prima che l'incident commander umano abbia completato il triage iniziale. L'integrazione con strumenti di collaborazione come Slack, Microsoft Teams e PagerDuty consente a questi agenti di partecipare attivamente nelle war room virtuali, fornendo aggiornamenti contestuali in tempo reale e suggerendo runbook pertinenti. Il 78% delle organizzazioni nel 2025 utilizza l'AI per almeno una funzione operativa, in crescita rispetto al 72% dell'inizio 2024, con l'observability e l'incident management tra le applicazioni piu' diffuse.

**Implicazioni operative per i team IT.** L'adozione di AIOps non elimina la necessita' di competenze umane nell'incident management, ma ne trasforma radicalmente il profilo. I team devono sviluppare competenze nella configurazione e nel tuning dei modelli AI, nella definizione delle policy di automazione (quali azioni possono essere eseguite autonomamente e quali richiedono approvazione umana), e nella supervisione dei sistemi self-healing. Il ruolo dell'Incident Commander evolve da coordinatore operativo a supervisore strategico che valida le decisioni prese dall'intelligenza artificiale e interviene nelle situazioni che superano le capacita' dei sistemi automatizzati. La sfida principale resta la fiducia: costruire un livello di confidenza sufficiente affinche' i team accettino che un agente AI possa eseguire azioni correttive in produzione richiede un percorso graduale di validazione, partendo da ambienti non critici e ampliando progressivamente il perimetro di autonomia.

---

## Esercizi
1. **Lab — incident drill.** Simulato; misura time-to-detect, time-to-mitigate, comms quality.
2. **Stretch — multi-burn-rate alert.** Setup Prometheus + Alertmanager con burn rate alerts.

## Auto-valutazione
1. Three pillars: cosa sono?
2. Burn rate vs threshold alert.
3. Incident commander: chi e quando?

## Glossario locale
| Termine | Definizione |
|---|---|
| **IC (Incident Commander)** | Owner durante incident. |
| **Burn rate** | Velocita consumo error budget. |
| **MTTR** | Mean Time To Resolve. |
| **MTTD** | Mean Time To Detect. |
| **War room** | Coordinamento durante incident. |
