# SIEM Architecture, Log Analysis e Forensic Readiness — Guida Completa

> **Modulo 25** · **Tempo:** ~120 min · **Aggiornamento:** 2026-05-07

## Idee guida

1. **Un SIEM senza detection engineering e un costoso database di log.** Il valore emerge solo dalle regole di correlazione, dal tuning continuo e dall'integrazione con i processi di incident response.
2. **Forensic readiness non e un afterthought.** Si progetta prima dell'incidente: retention, integrita, chain of custody, ammissibilita legale.
3. **Sigma come lingua franca.** Le detection rules devono essere portabili tra piattaforme; scrivere in Sigma e convertire per il backend specifico.
4. **Il threat hunting chiude il gap tra detection reattiva e proattiva.** Le regole catturano il noto; il hunting cerca l'ignoto.
5. **L'automazione SOAR moltiplica il SOC.** Playbook di enrichment e containment riducono MTTR da ore a minuti.

## Indice

1. [Architettura SIEM](#1-architettura-siem)
2. [Piattaforme SIEM](#2-piattaforme-siem)
3. [Log Collection e Normalizzazione](#3-log-collection-e-normalizzazione)
4. [Correlation Rules e Detection Engineering](#4-correlation-rules-e-detection-engineering)
5. [Analisi Forense dei Log](#5-analisi-forense-dei-log)
6. [Incident Detection Patterns](#6-incident-detection-patterns)
7. [Forensic Readiness Program](#7-forensic-readiness-program)
8. [Threat Hunting con SIEM](#8-threat-hunting-con-siem)
9. [Automazione e SOAR Integration](#9-automazione-e-soar-integration)
10. [Laboratorio Pratico](#10-laboratorio-pratico)

---

## 1. Architettura SIEM

### 1.1 Componenti Fondamentali

Un SIEM (Security Information and Event Management) si articola in cinque componenti logici, ciascuno con responsabilita ben definite. La comprensione di questi componenti e essenziale per dimensionare, troubleshootare e ottimizzare l'infrastruttura.

**Collector (Data Ingestion Layer)**

Il collector riceve eventi da sorgenti eterogenee: syslog UDP/TCP/TLS, Windows Event Forwarding, API REST, file tailing, SNMP trap, cloud provider trail (CloudTrail, Activity Log, Cloud Audit Logs). Il collector deve gestire burst di traffico senza perdita di eventi, implementando buffer locali e meccanismi di backpressure. In architetture distribuite, si utilizzano forwarder leggeri sui sistemi sorgente (Splunk Universal Forwarder, Elastic Agent, Wazuh agent) che inviano dati a collector centralizzati.

Metriche chiave del collector:

| Metrica | Target | Critico |
|---------|--------|---------|
| Events Per Second (EPS) | < 80% capacita | > 95% capacita |
| Queue depth | < 1000 eventi | > 10000 eventi |
| Drop rate | 0% | > 0.01% |
| Latency (ingestion) | < 5s | > 30s |

**Normalizer (Parsing and Enrichment Layer)**

Il normalizer trasforma eventi raw in un formato strutturato e uniforme. Questa fase include: parsing dei campi dal messaggio originale, mapping a un Common Information Model (CIM), enrichment con dati contestuali (GeoIP, threat intelligence feed, asset inventory, user directory). Un normalizer efficace mappa ogni evento a campi standardizzati: `timestamp`, `source_ip`, `dest_ip`, `source_port`, `dest_port`, `user`, `action`, `outcome`, `severity`.

**Correlator (Analytics Engine)**

Il correlator e il cuore del SIEM. Applica regole di correlazione agli eventi normalizzati per identificare pattern di attacco. Tipologie di correlazione:

- **Rule-based**: if-then deterministic (es. 5 login falliti in 60 secondi dallo stesso IP)
- **Statistical**: deviazione da baseline (es. volume di traffico DNS 3 sigma sopra la media)
- **Behavioral**: anomalie rispetto al profilo utente/entita (UEBA)
- **Sequence-based**: catena di eventi in ordine temporale (es. recon -> exploit -> lateral movement)
- **Aggregation-based**: conteggio di eventi distinti sopra soglia in finestra temporale

**Alerter (Notification and Response Layer)**

L'alerter gestisce la prioritizzazione, la deduplicazione e l'instradamento degli alert. Un alerter maturo implementa:

- Severity mapping (Critical/High/Medium/Low/Informational)
- Alert suppression per evitare duplicati entro una finestra temporale
- Routing basato su severity, asset criticality, business unit
- Integrazione con ticketing (ServiceNow, Jira), chat (Slack, Teams), paging (PagerDuty, Opsgenie)
- Escalation automatica se l'alert non viene acknowledged entro SLA

**Storage (Data Retention Layer)**

Lo storage deve bilanciare performance di query, costo e requisiti di retention. Architettura tipica a tre tier:

| Tier | Tecnologia | Retention | Use Case |
|------|-----------|-----------|----------|
| Hot | SSD / NVMe | 7-30 giorni | Query real-time, dashboard |
| Warm | HDD / object storage | 30-90 giorni | Investigation, hunting |
| Cold | Object storage (S3, GCS) | 1-7 anni | Compliance, forensics |
| Frozen | Glacier, Archive | 7+ anni | Legal hold, regulatory |

### 1.2 Modelli di Deployment

**On-Premises**

Controllo totale su dati e infrastruttura. Richiede team dedicato per hardware, patching, scaling. Costi CAPEX elevati, OPEX prevedibili. Adatto a organizzazioni con requisiti di data sovereignty stringenti (difesa, governo, finanza regolamentata). Architettura tipica: cluster di indexer dietro load balancer, search head separati, forwarder distribuiti.

**Cloud-Native**

SaaS SIEM gestiti dal vendor (Microsoft Sentinel, Splunk Cloud, Elastic Cloud, Chronicle). Scaling automatico, zero hardware management. Costi OPEX basati su volume di ingestione (GB/giorno) o EPS. Rischio vendor lock-in. Ideale per organizzazioni cloud-first con workload prevalentemente in cloud. La latenza di ingestione puo essere inferiore grazie alla prossimita con le sorgenti cloud.

**Hybrid**

Combinazione dei due modelli: SIEM on-prem per dati sensibili e sorgenti interne, cloud SIEM per workload cloud e SaaS log. Richiede federazione delle query e un unico pane of glass. Complessita operativa piu alta, ma massima flessibilita. Pattern comune: Splunk Enterprise on-prem + Splunk Cloud per AWS/Azure log, oppure Elastic on-prem + Elastic Cloud per SaaS.

### 1.3 Sizing e Capacity Planning

Il dimensionamento di un SIEM parte dal calcolo degli Events Per Second (EPS) e del volume giornaliero di ingestione.

Formula base per il calcolo dello storage:

```
Storage giornaliero (GB) = EPS_medio x 86400 x dimensione_media_evento_bytes / (1024^3)
Storage annuale (TB)     = Storage_giornaliero x 365 x fattore_compressione / 1024

Esempio:
  EPS medio      = 5000
  Dim. evento    = 800 bytes
  Compressione   = 0.5 (50%)
  Storage/giorno = 5000 x 86400 x 800 / 1073741824 = ~322 GB
  Storage/anno   = 322 x 365 x 0.5 / 1024 = ~57 TB
```

Regole pratiche per il sizing:

- CPU: 1 core ogni 500-1000 EPS per il parsing, 2 core per nodo di correlazione
- RAM: 16 GB minimo per nodo indexer, 32-64 GB per search head
- Disco: IOPS > 1000 per tier hot, throughput sequenziale per tier warm
- Rete: bandwidth >= 2x il throughput medio di ingestione per gestire burst
- Replica: fattore 2 o 3 per availability, moltiplica lo storage

```
+------------------+     +------------------+     +------------------+
|  Log Sources     |     |  Log Sources     |     |  Log Sources     |
|  (servers, FW,   |     |  (cloud trail,   |     |  (endpoints,     |
|   switches, IDS) |     |   SaaS audit)    |     |   workstations)  |
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         v                        v                        v
+--------+---------+     +--------+---------+     +--------+---------+
|  Forwarder/Agent |     |  API Poller      |     |  Agent (EDR/SIEM)|
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         +----------+-------------+-------------+----------+
                    |                           |
                    v                           v
           +-------+--------+         +--------+-------+
           |  Load Balancer  |         |  Message Queue |
           |  (HAProxy/NLB)  |         |  (Kafka/Redis) |
           +-------+--------+         +--------+-------+
                    |                           |
                    +-------------+-------------+
                                  |
                                  v
                    +-------------+-------------+
                    |     SIEM Cluster          |
                    |  +-----+ +-----+ +-----+ |
                    |  | Idx | | Idx | | Idx | |
                    |  +-----+ +-----+ +-----+ |
                    |  +--------+ +----------+  |
                    |  |Correlat| |Search Head|  |
                    |  +--------+ +----------+  |
                    +-------------+-------------+
                                  |
                    +-------------+-------------+
                    |  Storage Tiers            |
                    |  Hot -> Warm -> Cold       |
                    +---------------------------+
```

---

## 2. Piattaforme SIEM

### 2.1 Splunk Enterprise

Splunk e il SIEM commerciale piu diffuso, con un'architettura composta da Search Head (SH), Indexer (IDX) e Forwarder (UF/HF). Il linguaggio di query e SPL (Search Processing Language).

**Architettura Splunk:**

- **Universal Forwarder (UF)**: leggero, raccoglie e inoltra log raw. Nessun parsing locale.
- **Heavy Forwarder (HF)**: parsing, filtering e routing. Usato per sorgenti che richiedono trasformazione prima dell'indicizzazione.
- **Indexer**: riceve, indicizza e archivia gli eventi. Organizza i dati in bucket (hot/warm/cold/frozen).
- **Search Head**: esegue le query SPL, genera dashboard, gestisce alert e report.
- **Cluster Master / Manager**: coordina la replicazione tra indexer.
- **Deployer**: gestisce la configurazione dei search head in cluster.

**Esempi SPL per Detection:**

Brute force detection:

```spl
index=auth sourcetype=linux_secure "Failed password"
| stats count as failed_attempts dc(user) as targeted_users by src_ip
| where failed_attempts > 20 AND targeted_users > 3
| lookup threat_intel_ip ip AS src_ip OUTPUT threat_category
| table src_ip failed_attempts targeted_users threat_category
```

Lateral movement via PsExec:

```spl
index=wineventlog EventCode=7045 Service_Name="PSEXESVC"
| stats count by dest, Service_File_Name, Account_Name
| lookup asset_inventory host AS dest OUTPUT criticality, business_unit
| where criticality="high"
| table _time dest Account_Name Service_File_Name criticality
```

Rilevamento data exfiltration tramite DNS:

```spl
index=dns sourcetype=stream:dns query_type=TXT
| eval query_len=len(query)
| where query_len > 50
| stats count avg(query_len) as avg_len max(query_len) as max_len by src_ip query
| where count > 100 AND avg_len > 60
| table src_ip query count avg_len max_len
```

### 2.2 Elastic SIEM / Elastic Security

Elastic Security si basa sull'Elastic Stack (Elasticsearch, Kibana, Logstash/Fleet). Utilizza KQL (Kibana Query Language) per le ricerche e EQL (Event Query Language) per la correlazione di sequenze.

**Componenti chiave:**

- **Elasticsearch**: motore di ricerca e analytics distribuito, basato su Lucene
- **Kibana**: interfaccia web, dashboard, SIEM app, detection rules engine
- **Fleet / Elastic Agent**: gestione centralizzata degli agenti endpoint
- **Logstash / Ingest Pipelines**: parsing e trasformazione dei dati
- **Cross-cluster search**: federazione di query tra cluster

**Esempi KQL:**

Login falliti da IP esterni:

```kql
event.category: "authentication" and event.outcome: "failure"
  and source.ip: not (10.0.0.0/8 or 172.16.0.0/12 or 192.168.0.0/16)
```

**Esempio EQL (sequenza di attacco):**

```eql
sequence by host.name with maxspan=5m
  [process where process.name == "cmd.exe" and process.parent.name == "outlook.exe"]
  [file where file.extension in ("exe", "dll", "ps1") and file.path : "C:\\Users\\*\\AppData\\*"]
  [network where destination.port in (443, 8443, 4444) and not cidrmatch(destination.ip, "10.0.0.0/8")]
```

### 2.3 IBM QRadar

QRadar utilizza AQL (Ariel Query Language), un dialetto SQL-like per interrogare gli eventi e i flow.

**Architettura QRadar:**

- **Console**: interfaccia web, rule engine, reporting
- **Event Processor**: normalizzazione e correlazione
- **Event Collector**: raccolta da sorgenti remote
- **Flow Processor**: analisi dei flow di rete (NetFlow, sFlow, IPFIX)
- **Data Node**: storage distribuito per grandi deployment

**Esempio AQL:**

Rilevamento spray attack:

```sql
SELECT sourceip, COUNT(DISTINCT username) as user_count,
       COUNT(*) as attempt_count
FROM events
WHERE LOGSOURCETYPENAME(logsourceid) = 'Microsoft Windows Security Event Log'
  AND qid = 5000001
  AND CATEGORYNAME(category) = 'Authentication'
  AND eventdirection = 'R2L'
GROUP BY sourceip
HAVING user_count > 10 AND attempt_count > 50
ORDER BY attempt_count DESC
LAST 1 HOURS
```

### 2.4 Microsoft Sentinel

Sentinel e il SIEM cloud-native di Microsoft, integrato in Azure. Utilizza KQL (Kusto Query Language) e si basa su Log Analytics workspace.

**Punti di forza:**

- Integrazione nativa con Microsoft 365, Entra ID (Azure AD), Defender for Endpoint
- Connettori per centinaia di sorgenti (CEF, syslog, API)
- Workbook per visualizzazione, Playbook (Logic Apps) per automazione
- UEBA integrato
- Costo basato su GB ingerito (con commitment tier)

**Esempi KQL Sentinel:**

Impossible travel detection:

```kql
SigninLogs
| where ResultType == 0
| summarize
    locations = make_set(LocationDetails.city),
    timestamps = make_list(TimeGenerated),
    login_count = count()
    by UserPrincipalName
| mv-expand location = locations, ts = timestamps
| extend ts = todatetime(ts)
| sort by UserPrincipalName, ts asc
| serialize
| extend prev_location = prev(location), prev_ts = prev(ts), prev_user = prev(UserPrincipalName)
| where UserPrincipalName == prev_user
| extend time_diff_hours = datetime_diff('hour', ts, prev_ts)
| where location != prev_location and time_diff_hours < 2
| project UserPrincipalName, prev_location, location, prev_ts, ts, time_diff_hours
```

Rilevamento aggiunta di credenziali a Service Principal:

```kql
AuditLogs
| where OperationName has "Add service principal credentials"
| where Result == "success"
| extend
    actor = tostring(InitiatedBy.user.userPrincipalName),
    target_sp = tostring(TargetResources[0].displayName),
    target_sp_id = tostring(TargetResources[0].id)
| project TimeGenerated, actor, target_sp, target_sp_id, OperationName
```

### 2.5 Wazuh (Open-Source SIEM)

Wazuh e una piattaforma open-source che combina HIDS, log analysis, vulnerability detection e compliance monitoring. Si basa su un fork di OSSEC con dashboard Kibana/OpenSearch.

**Componenti:**

- **Wazuh Manager**: riceve eventi dagli agenti, esegue le regole di detection, genera alert
- **Wazuh Agent**: installato sugli endpoint, raccoglie log, monitora file integrity, esegue comandi
- **Wazuh Indexer**: Elasticsearch/OpenSearch per storage e ricerca
- **Wazuh Dashboard**: interfaccia web basata su OpenSearch Dashboards

**Esempio regola custom Wazuh (XML):**

Rilevamento creazione utente sospetto su Linux:

```xml
<group name="local,syslog,useradd">

  <rule id="100010" level="10">
    <if_sid>5901</if_sid>
    <match>useradd</match>
    <description>New user account created on system</description>
    <group>account_created,</group>
    <mitre>
      <id>T1136.001</id>
    </mitre>
  </rule>

  <rule id="100011" level="14">
    <if_sid>100010</if_sid>
    <time>10 pm - 6 am</time>
    <description>User account created during off-hours (potential persistence)</description>
    <group>account_created,suspicious_time,</group>
    <mitre>
      <id>T1136.001</id>
    </mitre>
  </rule>

  <rule id="100012" level="14">
    <if_sid>100010</if_sid>
    <match>uid=0</match>
    <description>New user created with UID 0 (root equivalent) — critical</description>
    <group>account_created,privilege_escalation,</group>
    <mitre>
      <id>T1136.001</id>
      <id>T1078.003</id>
    </mitre>
  </rule>

</group>
```

Rilevamento modifica di file critici (FIM alert):

```xml
<group name="local,syscheck">

  <rule id="100020" level="12">
    <if_sid>550</if_sid>
    <field name="file">/etc/shadow</field>
    <description>Critical file modified: /etc/shadow</description>
    <group>file_integrity,credential_access,</group>
    <mitre>
      <id>T1003.008</id>
    </mitre>
  </rule>

  <rule id="100021" level="12">
    <if_sid>550</if_sid>
    <field name="file">/etc/sudoers</field>
    <description>Sudoers file modified — potential privilege escalation</description>
    <group>file_integrity,privilege_escalation,</group>
    <mitre>
      <id>T1548.003</id>
    </mitre>
  </rule>

</group>
```

### 2.6 Graylog

Graylog e una piattaforma open-core per log management con funzionalita SIEM. Utilizza MongoDB per la configurazione e Elasticsearch/OpenSearch per lo storage dei log.

**Caratteristiche:**

- Pipeline processing con regole e stage ordinati
- Extractors per il parsing dei campi
- Streams per il routing dei messaggi
- Lookup table per enrichment
- Alert conditions con notification
- Content Packs per configurazioni riutilizzabili

**Confronto Piattaforme:**

| Caratteristica | Splunk | Elastic | QRadar | Sentinel | Wazuh | Graylog |
|---------------|--------|---------|--------|----------|-------|---------|
| Licenza | Commerciale | Open/Comm. | Commerciale | SaaS | Open Source | Open Core |
| Query Language | SPL | KQL/EQL | AQL | KQL | Wazuh API | Pipeline Rules |
| UEBA nativo | Si (ES) | Si | Si | Si | No | No |
| SOAR integrato | Si (SOAR) | No | Si (SOAR) | Si (Logic Apps) | No | No |
| Costo tipico | Alto | Medio | Alto | Variabile | Basso | Basso-Medio |
| Curva apprendimento | Media | Media-Alta | Alta | Media | Bassa | Bassa |
| Scalabilita | Eccellente | Eccellente | Buona | Eccellente | Buona | Buona |

---

## 3. Log Collection e Normalizzazione

### 3.1 Protocolli Syslog

**RFC 3164 (BSD Syslog) — Legacy Format:**

Formato semplice ma ambiguo. Nessuna strutturazione obbligatoria, timestamp senza anno e timezone.

```
<PRI>TIMESTAMP HOSTNAME APP-NAME[PID]: MESSAGE
<34>Oct 11 22:14:15 mymachine su[7456]: 'su root' failed for lonvick on /dev/pts/8
```

- PRI = facility * 8 + severity (0=Emergency ... 7=Debug)
- Facility: 0=kern, 1=user, 4=auth, 10=authpriv, 16-23=local0-local7
- Trasporto tipico: UDP/514 (unreliable, no encryption)

**RFC 5424 (Syslog Protocol) — Structured Format:**

Formato moderno con campi strutturati, timestamp ISO 8601, supporto UTF-8.

```
<PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [SD-ID SD-PARAM] MSG
<165>1 2026-05-07T12:34:56.003Z fw01.example.com pf - - [meta sequenceId="1234"]
  src=192.168.1.100 dst=10.0.0.1 proto=TCP dport=443 action=pass
```

- Trasporto raccomandato: TCP/TLS (RFC 5425) per reliability e confidentiality
- Structured Data (SD): coppie chiave-valore in sezioni delimitate da parentesi quadre
- IANA registered SD-IDs per interoperabilita

**Confronto protocolli di trasporto:**

| Protocollo | Porta | Affidabilita | Encryption | Uso |
|-----------|-------|-------------|------------|-----|
| Syslog UDP | 514 | No | No | Legacy, best-effort |
| Syslog TCP | 514/601 | Si | No | Reliable delivery |
| Syslog TLS | 6514 | Si | Si | Production, compliance |

### 3.2 Windows Event Forwarding (WEF)

Windows Event Forwarding e il meccanismo nativo Microsoft per centralizzare gli eventi Windows senza agenti di terze parti. Basato su WS-Management (WinRM).

**Architettura WEF:**

- **Source computer**: genera eventi e li inoltra al collector
- **WEC (Windows Event Collector)**: server che riceve e aggrega eventi
- **Subscription**: definisce quali eventi raccogliere e da quali source

**Configurazione subscription via GPO:**

```xml
<!-- Subscription XML per raccogliere eventi di sicurezza critici -->
<Subscription xmlns="http://schemas.microsoft.com/2006/03/windows/events/subscription">
  <SubscriptionId>SecurityCritical</SubscriptionId>
  <SubscriptionType>SourceInitiated</SubscriptionType>
  <Description>Critical security events from all servers</Description>
  <Enabled>true</Enabled>
  <Uri>http://schemas.microsoft.com/wbem/wsman/1/windows/EventLog</Uri>
  <Query>
    <![CDATA[
      <QueryList>
        <Query Id="0" Path="Security">
          <Select Path="Security">
            *[System[(EventID=4624 or EventID=4625 or EventID=4648 or
                      EventID=4672 or EventID=4688 or EventID=4698 or
                      EventID=4720 or EventID=4732 or EventID=4728 or
                      EventID=1102)]]
          </Select>
        </Query>
        <Query Id="1" Path="Microsoft-Windows-Sysmon/Operational">
          <Select Path="Microsoft-Windows-Sysmon/Operational">*</Select>
        </Query>
        <Query Id="2" Path="Microsoft-Windows-PowerShell/Operational">
          <Select Path="Microsoft-Windows-PowerShell/Operational">
            *[System[(EventID=4103 or EventID=4104)]]
          </Select>
        </Query>
      </QueryList>
    ]]>
  </Query>
</Subscription>
```

**Event ID critici per security monitoring:**

| EventID | Fonte | Descrizione | Rilevanza |
|---------|-------|-------------|-----------|
| 4624 | Security | Logon success | Baseline, lateral movement |
| 4625 | Security | Logon failure | Brute force |
| 4648 | Security | Explicit credentials logon | Lateral movement, runas |
| 4672 | Security | Special privileges assigned | Privilege escalation |
| 4688 | Security | Process creation | Execution tracking |
| 4698 | Security | Scheduled task created | Persistence |
| 4720 | Security | User account created | Persistence |
| 4732 | Security | Member added to local group | Privilege escalation |
| 1102 | Security | Audit log cleared | Anti-forensics |
| 7045 | System | Service installed | Persistence, lateral movement |
| 1 | Sysmon | Process create | Execution, full command line |
| 3 | Sysmon | Network connection | C2, exfiltration |
| 11 | Sysmon | File create | Payload drop |
| 13 | Sysmon | Registry value set | Persistence |
| 4104 | PowerShell | Script block logging | Script execution |

### 3.3 journald

systemd-journald e il sistema di logging nativo di distribuzioni Linux moderne. Log strutturati in formato binario, interrogabili via `journalctl`.

```bash
# Esportare eventi di autenticazione in formato JSON per ingestione SIEM
journalctl -u sshd --since "2026-05-06" --until "2026-05-07" \
  -o json --no-pager | \
  jq -c '{timestamp: .__REALTIME_TIMESTAMP, host: ._HOSTNAME,
          unit: ._SYSTEMD_UNIT, message: .MESSAGE, pid: ._PID}' \
  > /var/log/export/sshd-events.json

# Forwarding continuo a syslog remoto via systemd-journal-upload
# /etc/systemd/journal-upload.conf
# [Upload]
# URL=https://siem.example.com:19532
# ServerKeyFile=/etc/ssl/private/journal-upload.key
# ServerCertificateFile=/etc/ssl/certs/journal-upload.cert
# TrustedCertificateFile=/etc/ssl/ca/siem-ca.cert
```

### 3.4 Formati di Log Comuni

**CEF (Common Event Format):**

Formato sviluppato da ArcSight/Micro Focus. Header fisso + estensioni chiave-valore.

```
CEF:0|Vendor|Product|Version|SignatureID|Name|Severity|Extension
CEF:0|Fortinet|FortiGate|7.4|0419016384|Deny|5|src=192.168.1.50
  dst=10.0.0.80 dpt=3389 proto=TCP act=deny deviceExternalId=FG100F
  msg=RDP connection blocked by policy
```

**LEEF (Log Event Extended Format):**

Formato IBM per QRadar. Tab-separated.

```
LEEF:2.0|Palo Alto|Firewall|10.2|TRAFFIC|cat=TRAFFIC	src=10.1.1.5
  dst=203.0.113.50	dstPort=443	proto=TCP	action=allow
  totalBytes=154832	sessionDuration=45
```

**JSON structured logging:**

Formato moderno, self-describing, facile da parsare.

```json
{
  "timestamp": "2026-05-07T14:23:01.003Z",
  "level": "warning",
  "source": "fw-edge-01",
  "event_type": "connection_blocked",
  "src_ip": "192.168.1.100",
  "dst_ip": "10.0.0.50",
  "dst_port": 22,
  "protocol": "TCP",
  "action": "deny",
  "rule_id": "ACL-SSH-RESTRICTED",
  "bytes_sent": 0,
  "bytes_received": 0
}
```

### 3.5 Log Pipeline: Logstash, Fluentd, Vector

**Logstash Pipeline (Elastic Stack):**

```ruby
input {
  beats {
    port => 5044
    ssl_enabled => true
    ssl_certificate => "/etc/logstash/certs/logstash.crt"
    ssl_key => "/etc/logstash/certs/logstash.key"
  }
  syslog {
    port => 5514
    type => "syslog"
  }
}

filter {
  if [type] == "syslog" {
    grok {
      match => {
        "message" => "%{SYSLOGTIMESTAMP:syslog_timestamp} %{SYSLOGHOST:hostname} %{DATA:program}(?:\[%{POSINT:pid}\])?: %{GREEDYDATA:syslog_message}"
      }
    }
    date {
      match => ["syslog_timestamp", "MMM  d HH:mm:ss", "MMM dd HH:mm:ss"]
    }
    geoip {
      source => "src_ip"
      target => "geoip"
    }
    translate {
      field => "src_ip"
      destination => "threat_intel"
      dictionary_path => "/etc/logstash/threat_intel_ips.yml"
      fallback => "clean"
    }
  }

  if [event][code] == 4625 {
    mutate {
      add_tag => ["authentication_failure"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["https://es-node1:9200", "https://es-node2:9200"]
    index => "siem-%{+YYYY.MM.dd}"
    ssl_enabled => true
    api_key => "${ES_API_KEY}"
  }
}
```

**Fluentd Configuration:**

```xml
<source>
  @type tail
  path /var/log/auth.log
  pos_file /var/log/fluentd/auth.log.pos
  tag auth.linux
  <parse>
    @type regexp
    expression /^(?<time>[^ ]+ [^ ]+ [^ ]+) (?<host>[^ ]+) (?<ident>[^ ]+)(?:\[(?<pid>\d+)\])?: (?<message>.*)$/
    time_format %b %d %H:%M:%S
  </parse>
</source>

<filter auth.linux>
  @type record_transformer
  <record>
    environment production
    log_source linux_auth
  </record>
</filter>

<match auth.**>
  @type elasticsearch
  host siem-cluster.example.com
  port 9200
  index_name siem-auth
  type_name _doc
  logstash_format true
</match>
```

**Vector Configuration (Rust-based, high-performance):**

```toml
[sources.syslog_input]
type = "syslog"
address = "0.0.0.0:1514"
mode = "tcp"

[transforms.parse_auth]
type = "remap"
inputs = ["syslog_input"]
source = '''
  .event_type = "auth"
  .parsed = parse_syslog!(.message)
  if contains(string!(.message), "Failed password") {
    .alert_category = "brute_force"
    .severity = "high"
  }
'''

[sinks.elasticsearch]
type = "elasticsearch"
inputs = ["parse_auth"]
endpoints = ["https://siem:9200"]
bulk.index = "siem-auth-%Y-%m-%d"
```

### 3.6 Strategie di Deploy degli Agenti

| Strategia | Pro | Contro | Caso d'uso |
|-----------|-----|--------|------------|
| Agent-based | Ricco in dati, FIM, command audit | Overhead sul sistema, gestione agenti | Endpoint critici, server |
| Agentless (syslog) | Zero footprint | Dati limitati, UDP unreliable | Network device, appliance |
| API polling | Nessun agent, dati strutturati | Latenza, rate limit | SaaS, cloud service |
| File tailing | Semplice, nessuna modifica al servizio | Ritardo, rotazione log | Applicazioni legacy |
| Sidecar container | Isolato, scalabile | Complessita orchestrazione | Kubernetes, containerized apps |

---

## 4. Correlation Rules e Detection Engineering

### 4.1 Sigma Rules

Sigma e il formato standard aperto per la scrittura di detection rules portabili tra diverse piattaforme SIEM. Una regola Sigma viene compilata in SPL, KQL, AQL o qualsiasi altro linguaggio di backend tramite strumenti come `sigma-cli` o `pySigma`.

**Struttura di una regola Sigma:**

```yaml
title: Suspicious PowerShell Download Cradle
id: 3b6ab547-8ec2-4991-b5e8-4e1a26e5a5a8
status: stable
description: >
  Detects PowerShell commands commonly used as download cradles
  to fetch and execute remote payloads.
references:
  - https://attack.mitre.org/techniques/T1059/001/
  - https://attack.mitre.org/techniques/T1105/
author: SOC Team
date: 2026-05-07
modified: 2026-05-07
tags:
  - attack.execution
  - attack.t1059.001
  - attack.command_and_control
  - attack.t1105
logsource:
  category: process_creation
  product: windows
detection:
  selection_parent:
    ParentImage|endswith:
      - '\cmd.exe'
      - '\explorer.exe'
      - '\outlook.exe'
      - '\winword.exe'
      - '\excel.exe'
  selection_ps:
    Image|endswith: '\powershell.exe'
    CommandLine|contains:
      - 'IEX'
      - 'Invoke-Expression'
      - 'Invoke-WebRequest'
      - 'Net.WebClient'
      - 'DownloadString'
      - 'DownloadFile'
      - 'Start-BitsTransfer'
      - 'iwr '
      - 'curl '
      - 'wget '
  condition: selection_parent and selection_ps
falsepositives:
  - Legitimate admin scripts using download functionality
  - Software deployment tools
level: high
```

**Sigma rule: DCSync attack detection:**

```yaml
title: DCSync Attack Detected via Directory Replication
id: 9faec0c7-d141-4f45-9d7a-e0a6f8a7cf91
status: stable
description: >
  Detects potential DCSync attack by monitoring for DS-Replication-Get-Changes
  and DS-Replication-Get-Changes-All extended rights usage from non-DC sources.
references:
  - https://attack.mitre.org/techniques/T1003/006/
author: SOC Team
date: 2026-05-07
tags:
  - attack.credential_access
  - attack.t1003.006
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4662
    AccessMask: '0x100'
    Properties|contains:
      - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'
      - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'
      - '89e95b76-444d-4c62-991a-0facbeda640c'
  filter_dc:
    SubjectUserName|endswith: '$'
    SubjectUserName|contains:
      - 'DC01'
      - 'DC02'
  condition: selection and not filter_dc
falsepositives:
  - Legitimate replication from authorized domain controllers
  - Azure AD Connect service accounts
level: critical
```

### 4.2 Mapping MITRE ATT&CK

Ogni regola di detection deve essere mappata alla matrice MITRE ATT&CK. Il mapping segue la struttura Tactic -> Technique -> Sub-technique.

**Coverage map per un SOC maturo (esempio parziale):**

| Tactic | Technique | Sub-technique | Detection Rule | Data Source |
|--------|-----------|---------------|----------------|-------------|
| Initial Access | T1566 | .001 Spearphishing Attachment | Email attachment with macro | Email gateway logs |
| Execution | T1059 | .001 PowerShell | PS download cradle | Sysmon EventID 1 |
| Persistence | T1136 | .001 Local Account | User creation off-hours | Security EventID 4720 |
| Privilege Escalation | T1548 | .003 Sudo/Sudoers | Sudoers modification | FIM on /etc/sudoers |
| Defense Evasion | T1070 | .001 Clear Windows Event Logs | Audit log cleared | Security EventID 1102 |
| Credential Access | T1003 | .006 DCSync | DS-Replication request | Security EventID 4662 |
| Discovery | T1087 | .002 Domain Account | net user /domain | Sysmon EventID 1 |
| Lateral Movement | T1021 | .002 SMB/Windows Admin Shares | PsExec service install | System EventID 7045 |
| Collection | T1560 | .001 Archive via Utility | rar/7z/zip execution | Sysmon EventID 1 |
| Exfiltration | T1048 | .001 Over C2 Channel | Large DNS TXT queries | DNS logs |
| Command and Control | T1071 | .004 DNS | DNS tunneling | DNS query logs |

### 4.3 Metodologia di Sviluppo Use Case

Il processo di sviluppo di uno use case di detection segue un ciclo strutturato:

1. **Threat Assessment**: identificare la minaccia da rilevare (threat intel, risk assessment, post-incident lessons learned)
2. **Data Source Identification**: verificare che i log necessari siano disponibili e normalizzati
3. **Rule Development**: scrivere la regola in Sigma, poi compilare per il backend
4. **Testing in Lab**: eseguire la regola contro dati di test con true positive noti
5. **Baseline Tuning**: eseguire in modalita alert-only per 2-4 settimane, analizzare false positive
6. **False Positive Reduction**: aggiungere whitelist, esclusioni, contesto (asset criticality, user role)
7. **Production Deployment**: attivare l'azione di alert/response
8. **Continuous Improvement**: revisione trimestrale, aggiornamento con nuove TTP

### 4.4 Tipologie di Regole

**Threshold rules:**

```yaml
# Pseudo-rule: piu di N eventi di tipo X in T secondi
trigger: count(failed_login) > 10
window: 300 seconds
group_by: source_ip
action: alert(severity=high)
```

**Statistical rules (anomaly):**

```yaml
# Pseudo-rule: deviazione dalla baseline
metric: dns_query_count_per_host
baseline: rolling_average(7d)
trigger: current_value > baseline + (3 * standard_deviation)
action: alert(severity=medium)
```

**Behavioral rules (UEBA):**

```yaml
# Pseudo-rule: comportamento anomalo utente
entity: user
features:
  - login_time_deviation
  - new_source_ip
  - new_destination_accessed
  - unusual_application
risk_score: weighted_sum(features)
trigger: risk_score > 80
action: alert(severity=high), add_to_watchlist
```

### 4.5 Kill Chain Correlation

Correlare eventi attraverso le fasi della kill chain consente di rilevare attacchi multi-step che singole regole non catturerebbero.

```
Fase 1: Reconnaissance  ->  Port scan da IP esterno (firewall log)
         |
         v
Fase 2: Initial Access  ->  Phishing email con allegato (email gateway)
         |
         v
Fase 3: Execution        ->  PowerShell download cradle (Sysmon EID 1)
         |
         v
Fase 4: Persistence      ->  Scheduled task creato (Security EID 4698)
         |
         v
Fase 5: Lateral Movement ->  PsExec su server interno (System EID 7045)
         |
         v
Fase 6: Exfiltration     ->  DNS tunneling anomalo (DNS log)
```

Una regola di correlazione multi-step in pseudo-logica:

```
RULE: Advanced Threat Chain
WHEN:
  event_a = (external_port_scan targeting host_X) within last 24h
  AND event_b = (malicious_email delivered to user_on host_X) within 12h after event_a
  AND event_c = (powershell_download_cradle on host_X) within 2h after event_b
  AND event_d = (new_scheduled_task on host_X) within 1h after event_c
THEN:
  alert(severity=critical, title="Multi-stage attack chain detected",
        correlation_id=UUID, linked_events=[a,b,c,d])
```

### 4.6 False Positive Tuning

Il tuning dei falsi positivi e un processo continuo che richiede disciplina. Strategie:

- **Whitelist management**: mantenere liste di esclusione documentate e revisionate. Ogni whitelist entry deve avere un owner, una data di creazione e una data di scadenza.
- **Context enrichment**: aggiungere asset criticality, user role e business context per ridurre il rumore senza eliminare true positive.
- **Baseline adjustment**: per regole statistiche, ricalcolare le baseline periodicamente e dopo cambiamenti infrastrutturali.
- **Rule scoring**: assegnare un confidence score a ogni regola. Alert con score basso vanno in triage queue dedicata.
- **Feedback loop**: ogni false positive classificato dal SOC analyst deve alimentare il tuning della regola.

---

## 5. Analisi Forense dei Log

### 5.1 Ricostruzione Timeline

La timeline forensic e lo strumento piu potente per ricostruire la sequenza degli eventi durante un incidente. Combina log da sorgenti multiple in un'unica vista cronologica.

**Processo di ricostruzione:**

1. Identificare tutte le sorgenti di log rilevanti (SIEM, endpoint, network, cloud)
2. Normalizzare i timestamp a UTC (criticamente importante: verificare timezone di ogni sorgente)
3. Correlare eventi per entita (IP, hostname, user, process ID)
4. Costruire la timeline ordinata
5. Identificare gap temporali (possibili lacune nella raccolta o evidenza di tampering)
6. Documentare ogni entry con sorgente, affidabilita e interpretazione

**Script Python per generare una timeline da log multi-formato:**

```python
#!/usr/bin/env python3
"""Timeline generator: merges heterogeneous log files into a unified
chronological view suitable for forensic analysis."""

import json
import re
import sys
import hashlib
import gzip
from datetime import datetime, timezone
from pathlib import Path


_SYSLOG_RE = re.compile(
    r"^(?P<timestamp>\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})\s"
    r"(?P<host>\S+)\s(?P<program>\S+?)(?:\[(?P<pid>\d+)\])?:\s(?P<message>.+)$"
)

_WINEVENT_TS_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)"
)


def _parse_syslog_line(line: str, source_file: str, year: int = 2026):
    match = _SYSLOG_RE.match(line)
    if not match:
        return None
    raw_ts = match.group("timestamp")
    try:
        dt = datetime.strptime(f"{year} {raw_ts}", "%Y %b %d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return {
        "timestamp": dt.isoformat(),
        "host": match.group("host"),
        "program": match.group("program"),
        "pid": match.group("pid"),
        "message": match.group("message"),
        "source_file": source_file,
        "log_format": "syslog_rfc3164",
    }


def _parse_json_line(line: str, source_file: str):
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None
    ts_field = None
    for candidate in ("timestamp", "@timestamp", "time", "eventTime", "TimeGenerated"):
        if candidate in record:
            ts_field = candidate
            break
    if ts_field is None:
        return None
    record["source_file"] = source_file
    record["log_format"] = "json"
    record.setdefault("timestamp", record.pop(ts_field))
    return record


def _open_log(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def build_timeline(log_paths: list[str]) -> list[dict]:
    events = []
    for path_str in log_paths:
        path = Path(path_str)
        if not path.exists():
            print(f"[WARN] File not found: {path}", file=sys.stderr)
            continue
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        with _open_log(path) as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.rstrip("\n")
                if not line:
                    continue
                record = _parse_json_line(line, str(path))
                if record is None:
                    record = _parse_syslog_line(line, str(path))
                if record is None:
                    continue
                record["_line_number"] = line_no
                record["_source_hash"] = file_hash
                events.append(record)
    events.sort(key=lambda e: e.get("timestamp", ""))
    return events


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <logfile1> [logfile2] ...", file=sys.stderr)
        sys.exit(1)
    timeline = build_timeline(sys.argv[1:])
    for event in timeline:
        print(json.dumps(event, default=str))


if __name__ == "__main__":
    main()
```

### 5.2 Estrazione Artefatti

Gli artefatti forensi estratti dai log includono:

- **Indicatori di compromissione (IOC)**: IP, domain, URL, hash di file, user agent, email address
- **Artefatti di esecuzione**: command line, process tree, parent-child relationship
- **Artefatti di persistenza**: scheduled task, service, registry key, cron job, startup item
- **Artefatti di rete**: connessioni C2, DNS query anomale, proxy log, flow record
- **Artefatti di accesso**: logon event, authentication token, session ID, kerberos ticket

**Script Python per estrazione IOC da log:**

```python
#!/usr/bin/env python3
"""Extract IOCs (IPs, domains, URLs, hashes) from log lines."""

import re
import sys
import json
from collections import Counter

_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1?\d{1,2})\b"
)
_DOMAIN_RE = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)"
    r"{1,10}[a-zA-Z]{2,63}\b"
)
_URL_RE = re.compile(r"https?://[^\s\"'<>]+")
_MD5_RE = re.compile(r"\b[a-fA-F0-9]{32}\b")
_SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")

_PRIVATE_NETS = re.compile(
    r"^(?:10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.|127\.)"
)


def extract_iocs(text: str) -> dict:
    ips = [
        ip for ip in _IPV4_RE.findall(text)
        if not _PRIVATE_NETS.match(ip)
    ]
    return {
        "ipv4": Counter(ips),
        "domains": Counter(_DOMAIN_RE.findall(text)),
        "urls": Counter(_URL_RE.findall(text)),
        "md5": Counter(_MD5_RE.findall(text)),
        "sha256": Counter(_SHA256_RE.findall(text)),
    }


def main():
    text = sys.stdin.read()
    iocs = extract_iocs(text)
    for category, counts in iocs.items():
        if counts:
            print(f"\n=== {category.upper()} ===")
            for value, count in counts.most_common(50):
                print(f"  {count:>6}  {value}")


if __name__ == "__main__":
    main()
```

### 5.3 Chain of Custody per Evidenza Digitale

La chain of custody documenta il possesso, il controllo e la manipolazione dell'evidenza digitale dal momento della raccolta fino alla presentazione in sede legale. Ogni interruzione nella catena puo invalidare l'evidenza.

**Elementi obbligatori della documentazione:**

1. **Identificazione**: descrizione univoca dell'evidenza (hostname, path, hash, dimensione)
2. **Raccolta**: chi ha raccolto, quando (UTC ISO 8601), come, con quali strumenti
3. **Trasferimento**: ogni passaggio di mano documentato con firme, date, motivo
4. **Conservazione**: dove e conservata, protezioni fisiche e logiche, accesso controllato
5. **Analisi**: chi ha analizzato, quando, su quale copia (mai sull'originale), strumenti usati
6. **Restituzione/Distruzione**: disposizione finale dell'evidenza

**Template chain of custody entry:**

```
CHAIN OF CUSTODY RECORD
========================
Evidence ID:      EV-2026-0507-001
Description:      Windows Security Event Log (Security.evtx) from server DC01
Original Hash:    SHA-256: a1b2c3d4e5f6...
Collection Date:  2026-05-07T14:30:00Z
Collected By:     [Analyst Name], SOC Team
Collection Method: wevtutil epl Security C:\evidence\Security.evtx
Storage Location: Evidence locker, Room 401, encrypted USB (BitLocker)
Access Log:
  2026-05-07T14:30:00Z  [Analyst Name]    Collected from DC01
  2026-05-07T15:00:00Z  [Analyst Name]    Transferred to evidence locker
  2026-05-08T09:00:00Z  [Forensic Lead]   Retrieved for analysis (working copy)
  2026-05-08T17:00:00Z  [Forensic Lead]   Returned to evidence locker
Integrity Verified: Yes (hash match confirmed at each transfer)
```

### 5.4 Verifica Integrita dei Log con Hashing

L'integrita dei log e fondamentale per garantire che le evidenze non siano state alterate. Si utilizzano hash crittografici per creare un fingerprint di ogni file di log al momento della raccolta.

**Script per hash chain dei log:**

```python
#!/usr/bin/env python3
"""Create a hash chain for log files to verify integrity over time.
Each entry includes the file hash and a chain hash linking to the previous entry,
making any tampering detectable."""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_hash_chain(file_paths: list[str], output_path: str) -> None:
    chain = []
    previous_chain_hash = "GENESIS"

    for path_str in file_paths:
        path = Path(path_str)
        if not path.exists():
            print(f"[WARN] Skipping missing file: {path}", file=sys.stderr)
            continue

        file_hash = compute_sha256(path_str)
        chain_input = f"{previous_chain_hash}:{file_hash}:{path.name}"
        chain_hash = hashlib.sha256(chain_input.encode()).hexdigest()

        entry = {
            "file": str(path.resolve()),
            "file_size_bytes": path.stat().st_size,
            "sha256": file_hash,
            "chain_hash": chain_hash,
            "previous_chain_hash": previous_chain_hash,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        chain.append(entry)
        previous_chain_hash = chain_hash

    with open(output_path, "w") as f:
        json.dump(chain, f, indent=2)

    print(f"Hash chain written to {output_path} ({len(chain)} entries)")


def verify_hash_chain(chain_path: str) -> bool:
    with open(chain_path) as f:
        chain = json.load(f)

    previous_chain_hash = "GENESIS"
    for i, entry in enumerate(chain):
        current_file_hash = compute_sha256(entry["file"])
        if current_file_hash != entry["sha256"]:
            print(f"[FAIL] File hash mismatch at entry {i}: {entry['file']}")
            print(f"  Expected: {entry['sha256']}")
            print(f"  Actual:   {current_file_hash}")
            return False

        chain_input = f"{previous_chain_hash}:{entry['sha256']}:{Path(entry['file']).name}"
        expected_chain = hashlib.sha256(chain_input.encode()).hexdigest()
        if expected_chain != entry["chain_hash"]:
            print(f"[FAIL] Chain hash mismatch at entry {i}: chain broken")
            return False

        if entry["previous_chain_hash"] != previous_chain_hash:
            print(f"[FAIL] Previous chain hash mismatch at entry {i}")
            return False

        previous_chain_hash = entry["chain_hash"]

    print(f"[PASS] All {len(chain)} entries verified successfully")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} build <output.json> <file1> [file2] ...")
        print(f"       {sys.argv[0]} verify <chain.json>")
        sys.exit(1)

    command = sys.argv[1]
    if command == "build":
        build_hash_chain(sys.argv[3:], sys.argv[2])
    elif command == "verify":
        success = verify_hash_chain(sys.argv[2])
        sys.exit(0 if success else 1)
```

### 5.5 Rilevamento Anti-Forensics

Gli attaccanti sofisticati tentano di eliminare le tracce. Tecniche comuni e relative contromisure:

**Log Tampering e Deletion:**

| Tecnica Anti-Forensics | Indicatore di Detection | Sorgente |
|------------------------|------------------------|----------|
| `wevtutil cl Security` | EventID 1102 (audit log cleared) | Security log (se catturato prima della cancellazione) |
| Sovrascrittura di log file | Gap temporali, dimensione file anomala | FIM, SIEM metadata |
| Timestomping | Discrepanza tra $MFT timestamp e log timestamp | Filesystem forensics |
| Log rotation forzata | Rotazione fuori schedulazione | Monitoraggio cron/logrotate config |
| Modifica di syslog config | File integrity change su rsyslog.conf/syslog-ng.conf | FIM alert |
| Disabilitazione audit policy | EventID 4719 (audit policy changed) | Security log |
| Process injection nel logger | Comportamento anomalo del processo syslog | EDR, process monitoring |

**Contromisure:**

- **Write-once storage**: inviare log a storage immutabile (WORM, S3 Object Lock, append-only)
- **Real-time forwarding**: inviare log a SIEM remoto immediatamente, riducendo la finestra di tampering
- **Log integrity monitoring**: hash chain, digital signature sui log, FIM su file di log
- **Multi-destination logging**: inviare a 2+ destinazioni indipendenti
- **Kernel-level audit**: auditd con regole immutabili (`-e 2` lock), rendendo impossibile disabilitare l'audit senza reboot

Regola Sigma per rilevamento cancellazione log:

```yaml
title: Windows Audit Log Cleared
id: d99b79d2-0a6a-4f5e-9c91-6a04e7b37e35
status: stable
description: Detects clearing of Windows Security event log
references:
  - https://attack.mitre.org/techniques/T1070/001/
author: SOC Team
date: 2026-05-07
tags:
  - attack.defense_evasion
  - attack.t1070.001
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 1102
  condition: selection
falsepositives:
  - Legitimate log maintenance (should be extremely rare and scheduled)
level: critical
```

---

## 6. Incident Detection Patterns

### 6.1 Brute Force Detection

**Pattern caratteristici:**

- Multipli tentativi di login falliti dalla stessa sorgente in finestra temporale ristretta
- Password spray: pochi tentativi per utente, molti utenti dallo stesso IP
- Credential stuffing: coppie user/password da breach database, alta varieta

**SPL per brute force con soglia adattiva:**

```spl
index=auth sourcetype=linux_secure OR sourcetype=WinEventLog:Security
  ("Failed password" OR EventCode=4625)
| bin _time span=5m
| stats count as attempts dc(user) as unique_users values(user) as targeted_users
  by src_ip _time
| where attempts > 15 OR (unique_users > 5 AND attempts > 10)
| streamstats time_window=1h sum(attempts) as rolling_attempts by src_ip
| where rolling_attempts > 50
| table _time src_ip attempts unique_users targeted_users rolling_attempts
```

### 6.2 Lateral Movement Indicators

**Segnali di lateral movement:**

- Accesso amministrativo da workstation a workstation (non tipico)
- PsExec, WMI, WinRM, RDP tra host nella stessa subnet
- Pass-the-Hash: NTLM authentication da host non previsti
- Pass-the-Ticket: Kerberos ticket reuse da IP diversi

**KQL Sentinel per rilevamento lateral movement:**

```kql
SecurityEvent
| where EventID == 4624 and LogonType in (3, 10)
| where AccountType == "User"
| where not(IpAddress in ("127.0.0.1", "::1", "-"))
| summarize
    target_hosts = make_set(Computer),
    target_count = dcount(Computer),
    logon_count = count()
    by IpAddress, Account, bin(TimeGenerated, 1h)
| where target_count > 3
| extend alert_reason = strcat(Account, " accessed ", target_count,
    " hosts from ", IpAddress, " in 1 hour")
| project TimeGenerated, Account, IpAddress, target_count, target_hosts, alert_reason
```

### 6.3 Data Exfiltration Patterns

**Indicatori di exfiltration:**

- Volume anomalo di upload verso destinazioni esterne
- Compressione/cifratura di file prima del trasferimento
- Uso di canali non standard (DNS, ICMP, HTTPS to uncommon domains)
- Trasferimento fuori orario lavorativo

**SPL per rilevamento exfiltration via web:**

```spl
index=proxy sourcetype=squid OR sourcetype=bluecoat
| stats sum(bytes_out) as total_bytes_out dc(url) as unique_urls
  by src_ip dest_domain
| where total_bytes_out > 104857600
| eval mb_out=round(total_bytes_out/1048576,2)
| lookup domain_whitelist domain AS dest_domain OUTPUT is_whitelisted
| where is_whitelisted!="true"
| sort -total_bytes_out
| table src_ip dest_domain mb_out unique_urls
```

### 6.4 Privilege Escalation Signals

**Indicatori:**

- Modifica membership di gruppi privilegiati (Domain Admins, Enterprise Admins, Administrators)
- Sudoers file modification su Linux
- Token manipulation: SeDebugPrivilege, SeImpersonatePrivilege
- UAC bypass
- Kernel exploit artifact (crash dump, unexpected driver load)

**Sigma rule per privilege escalation via group membership:**

```yaml
title: User Added to High-Privilege Group
id: f7c3b5a1-2e8d-4b9c-a6f0-1d2e3f4a5b6c
status: stable
description: >
  Detects when a user is added to a high-privilege Active Directory group,
  which may indicate privilege escalation.
references:
  - https://attack.mitre.org/techniques/T1078/002/
author: SOC Team
date: 2026-05-07
tags:
  - attack.persistence
  - attack.privilege_escalation
  - attack.t1078.002
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID:
      - 4728  # Member added to security-enabled global group
      - 4732  # Member added to security-enabled local group
      - 4756  # Member added to security-enabled universal group
  selection_groups:
    TargetUserName|contains:
      - 'Domain Admins'
      - 'Enterprise Admins'
      - 'Schema Admins'
      - 'Administrators'
      - 'Account Operators'
      - 'Backup Operators'
      - 'DnsAdmins'
  condition: selection and selection_groups
falsepositives:
  - Legitimate administrative group management during onboarding
level: high
```

### 6.5 C2 Beacon Detection

I beacon C2 (Command and Control) presentano pattern di comunicazione caratteristici:

- **Periodic callback**: connessioni a intervalli regolari (con jitter)
- **Low-and-slow**: piccoli pacchetti, lunghi intervalli
- **HTTP(S) beaconing**: richieste GET/POST a intervalli fissi verso lo stesso dominio
- **DNS beaconing**: query DNS periodiche a sottodomini dello stesso dominio

**SPL per C2 beacon detection tramite analisi periodicita:**

```spl
index=proxy sourcetype=squid
| stats count values(url) as urls by src_ip dest_domain
| where count > 50
| join type=inner src_ip dest_domain
  [search index=proxy sourcetype=squid
   | sort 0 src_ip dest_domain _time
   | streamstats current=f window=1 last(_time) as prev_time by src_ip dest_domain
   | eval interval=_time-prev_time
   | where interval > 0
   | stats stdev(interval) as interval_stdev avg(interval) as interval_avg
     count as beacon_count by src_ip dest_domain
   | eval jitter_pct=round((interval_stdev/interval_avg)*100, 2)
   | where jitter_pct < 25 AND beacon_count > 20 AND interval_avg > 30
     AND interval_avg < 3600]
| table src_ip dest_domain beacon_count interval_avg jitter_pct urls
```

Un jitter inferiore al 25% con piu di 20 connessioni e un intervallo medio tra 30 secondi e 1 ora e altamente sospetto di beaconing C2.

### 6.6 DNS Tunneling Detection

Il DNS tunneling utilizza query e response DNS per trasferire dati, bypassando i controlli di sicurezza perimetrali.

**Indicatori:**

- Query con subdomain insolitamente lunghi (>50 caratteri)
- Elevato volume di query verso lo stesso dominio base
- Query di tipo TXT, NULL, CNAME in quantita anomale
- Entropia alta nel subdomain (dati codificati in base32/base64)
- Dominio base registrato di recente o con bassa reputazione

**KQL Sentinel per DNS tunneling:**

```kql
DnsEvents
| where QueryType in ("TXT", "NULL", "CNAME", "MX")
| extend subdomain = tostring(split(Name, ".")[0])
| extend subdomain_len = strlen(subdomain)
| extend base_domain = strcat(tostring(split(Name, ".")[-2]), ".",
    tostring(split(Name, ".")[-1]))
| where subdomain_len > 30
| summarize
    query_count = count(),
    unique_subdomains = dcount(subdomain),
    avg_subdomain_len = avg(subdomain_len),
    max_subdomain_len = max(subdomain_len),
    total_query_bytes = sum(subdomain_len)
    by ClientIP, base_domain, bin(TimeGenerated, 1h)
| where query_count > 100 and unique_subdomains > 50 and avg_subdomain_len > 40
| extend estimated_exfil_kb = round(total_query_bytes / 1024.0, 2)
| project TimeGenerated, ClientIP, base_domain, query_count, unique_subdomains,
    avg_subdomain_len, estimated_exfil_kb
```

### 6.7 Living-off-the-Land Binaries (LOLBins)

Gli attaccanti utilizzano binari legittimi del sistema operativo per eseguire azioni malevole, evadendo la detection basata su signature.

**LOLBins Windows piu comuni:**

| Binary | Uso malevolo | MITRE ID |
|--------|-------------|----------|
| `certutil.exe` | Download file, decode base64 | T1140, T1105 |
| `mshta.exe` | Esecuzione HTA/VBS/JS | T1218.005 |
| `regsvr32.exe` | Esecuzione DLL, bypass AppLocker | T1218.010 |
| `rundll32.exe` | Esecuzione DLL arbitrarie | T1218.011 |
| `msiexec.exe` | Installazione remota MSI malevoli | T1218.007 |
| `wmic.exe` | Recon, process exec, lateral movement | T1047 |
| `bitsadmin.exe` | Download file in background | T1197, T1105 |
| `cmstp.exe` | Bypass UAC, esecuzione profili INF | T1218.003 |

**Sigma rule per certutil download abuse:**

```yaml
title: Certutil Used to Download File
id: e4b6d2f1-7c3a-4d5e-8f9b-0a1c2d3e4f5a
status: stable
description: >
  Detects certutil.exe being used to download files, a common
  living-off-the-land technique for payload delivery.
references:
  - https://attack.mitre.org/techniques/T1105/
  - https://lolbas-project.github.io/#/execute
author: SOC Team
date: 2026-05-07
tags:
  - attack.command_and_control
  - attack.t1105
  - attack.defense_evasion
  - attack.t1140
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\certutil.exe'
    CommandLine|contains:
      - 'urlcache'
      - 'verifyctl'
      - '-decode'
      - '-decodehex'
      - '-encode'
      - '/decode'
      - '/decodehex'
      - '/encode'
      - '-urlcache'
      - '/urlcache'
  filter_legit:
    CommandLine|contains:
      - 'certificate'
      - '-addstore'
      - '-verify'
  condition: selection and not filter_legit
falsepositives:
  - IT administrators using certutil for legitimate certificate operations
level: high
```

---

## 7. Forensic Readiness Program

### 7.1 RFC 3227 — Ordine di Raccolta Evidenze

RFC 3227 ("Guidelines for Evidence Collection and Archiving") definisce l'ordine di raccolta delle evidenze digitali basato sulla volatilita. Le evidenze piu volatili devono essere raccolte per prime, perche si perdono piu rapidamente.

**Ordine di volatilita (dal piu volatile al meno volatile):**

1. **Registri CPU e cache**: contenuto dei registri, cache L1/L2/L3 — persi immediatamente allo spegnimento
2. **Tabelle di routing, cache ARP, tabelle dei processi, statistiche del kernel, memoria**: informazioni di stato del sistema operativo che cambiano continuamente
3. **File temporanei del sistema**: temp directory, swap, page file
4. **Disco**: filesystem, log su disco, database, file utente
5. **Log remoti e dati di monitoraggio**: syslog remoto, SIEM, NetFlow — conservati su sistemi separati
6. **Configurazione fisica**: topologia di rete, cablaggio, configurazione hardware
7. **Media di archivio**: backup su tape, storage offline, media rimovibili

**Implicazioni operative:**

- Non spegnere il sistema prima di aver acquisito la RAM
- Acquisire dump di memoria con strumenti forensi validati (WinPmem, LiME, AVML)
- Documentare ogni azione con timestamp UTC ISO 8601
- Fotografare lo schermo del sistema prima di qualsiasi intervento
- Isolare il sistema dalla rete (staccare il cavo, non spegnere)

### 7.2 Politiche di Retention per Framework di Compliance

| Framework | Requisito Minimo | Log Richiesti | Note |
|-----------|-----------------|---------------|------|
| PCI DSS v4.0 | 12 mesi (3 mesi immediately available) | Accesso ai dati cardholder, autenticazione, modifiche configurazione | Req. 10.7 |
| GDPR | Non specificato (proporzionalita) | Accesso a dati personali, consenso, data processing | Minimizzazione dati |
| HIPAA | 6 anni | Accesso a PHI, audit trail, user activity | 45 CFR 164.312(b) |
| SOX | 7 anni | Financial system access, change management, privileged access | Section 802 |
| SOC 2 | 1 anno (minimo) | Logical access, system changes, security events | Trust Services Criteria |
| NIST 800-171 | 3 anni | CUI access, authentication events, system changes | 3.3.1, 3.3.2 |
| ISO 27001 | Definito dall'organizzazione | Security events, access control, change management | A.12.4 |
| NIS2 (EU) | Non specificato (adeguato) | Incidenti, accesso, cambiamenti di configurazione | Art. 21 |

**Raccomandazione pragmatica:** conservare hot/warm per 90 giorni, cold per 1 anno, frozen per il massimo richiesto dal framework applicabile. Il costo dello storage cold/frozen e trascurabile rispetto al costo di non avere i log durante un'indagine.

### 7.3 Procedure di Preservazione delle Evidenze

**Procedura di acquisizione log per incident response:**

```
1. IDENTIFICARE le sorgenti di log rilevanti per l'incidente
   - SIEM: esportare query results per il periodo sospetto
   - Endpoint: acquisire evtx, auth.log, syslog, application log
   - Network: pcap, NetFlow, firewall log, proxy log
   - Cloud: CloudTrail, Activity Log, Cloud Audit Logs

2. ACQUISIRE preservando l'integrita
   - Calcolare hash SHA-256 di ogni file prima della copia
   - Copiare su media write-protected o storage con object lock
   - Verificare hash SHA-256 dopo la copia
   - Documentare strumento, versione, parametri usati

3. DOCUMENTARE la chain of custody
   - Compilare il modulo CoC per ogni evidenza
   - Firmare e datare ogni trasferimento
   - Conservare il modulo con l'evidenza

4. CONSERVARE in modo sicuro
   - Storage cifrato con accesso controllato
   - Ambiente separato da quello di produzione
   - Logging degli accessi al repository delle evidenze
   - Backup dell'evidenza su media separato
```

### 7.4 Requisiti di Ammissibilita Legale

Per essere ammissibili in procedimenti legali, le evidenze digitali devono soddisfare quattro criteri fondamentali:

1. **Autenticita**: dimostrare che l'evidenza e genuina e non e stata alterata. Hash crittografici, chain of custody ininterrotta, strumenti forensi validati.

2. **Affidabilita**: dimostrare che il processo di raccolta e analisi e riproducibile. Procedure documentate, strumenti standard, analisti qualificati.

3. **Completezza**: presentare tutta l'evidenza rilevante, non solo quella che supporta una tesi. Documentare anche le evidenze che contraddicono l'ipotesi investigativa.

4. **Proporzionalita**: la raccolta deve essere proporzionata all'obiettivo. Non acquisire piu dati del necessario (principio di minimizzazione).

**Standard di riferimento:**

- **ISO 27037**: Guidelines for identification, collection, acquisition and preservation of digital evidence
- **ISO 27042**: Guidelines for the analysis and interpretation of digital evidence
- **NIST SP 800-86**: Guide to Integrating Forensic Techniques into Incident Response
- **RFC 3227**: Guidelines for Evidence Collection and Archiving

### 7.5 Documentazione Chain of Custody

**Registro centralizzato delle evidenze:**

```
EVIDENCE REGISTER — Incident IR-2026-0042
=========================================

Evidence   Description                Hash (SHA-256)                   Collected By    Date (UTC)
--------   -------------------------  -------------------------------- --------------- -------------------
EV-001     Security.evtx from DC01    a1b2c3d4e5f6789...              [Analyst A]     2026-05-07T14:30:00Z
EV-002     auth.log from WEB-PROD-01  f6e5d4c3b2a1987...              [Analyst A]     2026-05-07T14:45:00Z
EV-003     RAM dump from WS-FINANCE   9a8b7c6d5e4f321...              [Analyst B]     2026-05-07T15:00:00Z
EV-004     pcap from FW-EDGE-01       3c2d1e0f9a8b765...              [Analyst C]     2026-05-07T15:15:00Z
EV-005     CloudTrail export (24h)    7f8e9d0c1b2a345...              [Analyst A]     2026-05-07T15:30:00Z

TRANSFER LOG:
Date (UTC)               From            To              Reason                  Verified Hash
-------------------      --------------- --------------- ----------------------  -------------
2026-05-07T16:00:00Z     [Analyst A]     Evidence Locker Initial deposit         Match
2026-05-08T09:00:00Z     Evidence Locker [Forensic Lead] Analysis (working copy) Match
2026-05-10T11:00:00Z     Evidence Locker Legal Counsel   Litigation hold         Match
```

---

## 8. Threat Hunting con SIEM

### 8.1 Hypothesis-Driven Hunting

Il threat hunting hypothesis-driven segue un ciclo strutturato:

1. **Formulare l'ipotesi**: basata su threat intel, TTP noti, risultati di vulnerability assessment, o intuizione dell'analista. Esempio: "Un attaccante potrebbe utilizzare PowerShell per scaricare ed eseguire payload da C2 server nella nostra rete."

2. **Identificare i dati necessari**: quali log, quale SIEM index, quale timeframe. Per l'ipotesi sopra: Sysmon EventID 1 (process creation), PowerShell script block logging (EventID 4104), proxy log per outbound HTTP.

3. **Sviluppare le query**: tradurre l'ipotesi in query SIEM specifiche.

4. **Eseguire e analizzare**: cercare evidenze che supportino o confutino l'ipotesi.

5. **Documentare i risultati**: finding positivi o negativi, entrambi hanno valore. Un finding negativo conferma che il controllo funziona o che la minaccia non e presente.

6. **Produrre output**: se la hunt trova attivita sospetta, escalare a incident response. Se trova gap di visibilita, raccomandare miglioramenti alla log collection. Se trova pattern ricorrenti, creare detection rule permanente.

### 8.2 IOC Sweep

IOC sweep e la ricerca retroattiva di indicatori di compromissione noti (IP, domain, hash, user agent) nei log storici. Tipicamente innescato da un advisory di threat intelligence, una breach disclosure da un fornitore, o un nuovo IOC pubblicato da un ISAC.

**SPL per IOC sweep multi-tipo:**

```spl
| inputlookup threat_intel_iocs.csv
| eval ioc_type=case(
    match(ioc, "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"), "ip",
    match(ioc, "^[a-f0-9]{32}$"), "md5",
    match(ioc, "^[a-f0-9]{64}$"), "sha256",
    true(), "domain")
| map maxsearches=100 search="search index=* earliest=-90d latest=now
    ($ioc_type$=$ioc$ OR dest=$ioc$ OR src=$ioc$ OR query=$ioc$
     OR url=\"*$ioc$*\" OR file_hash=$ioc$)
    | eval matched_ioc=\"$ioc$\", ioc_type=\"$ioc_type$\"
    | table _time index sourcetype src dest matched_ioc ioc_type"
```

### 8.3 Anomaly Detection

La detection di anomalie si basa sulla deviazione da una baseline di comportamento "normale". Richiede un periodo di baseline (tipicamente 14-30 giorni) e modelli statistici.

**Approcci:**

- **Volume-based**: traffico di rete, numero di eventi, dimensione trasferimenti
- **Time-based**: attivita in orari insoliti, picchi fuori schedulazione
- **Frequency-based**: accessi a risorse raramente utilizzate
- **Cardinality-based**: un utente che accede a un numero insolitamente alto di host
- **Geographic-based**: accessi da localita nuove o incoerenti

**KQL per anomaly detection su volumi di autenticazione:**

```kql
let baseline_period = 14d;
let detection_window = 1h;
let threshold_multiplier = 3;
SigninLogs
| where TimeGenerated between (ago(baseline_period) .. ago(detection_window))
| summarize baseline_avg = avg(todouble(1)), baseline_stdev = stdev(todouble(1))
    by UserPrincipalName, bin(TimeGenerated, 1h)
| summarize
    avg_hourly = avg(baseline_avg),
    stdev_hourly = avg(baseline_stdev)
    by UserPrincipalName
| join kind=inner (
    SigninLogs
    | where TimeGenerated > ago(detection_window)
    | summarize current_count = count() by UserPrincipalName
) on UserPrincipalName
| extend threshold = avg_hourly + (threshold_multiplier * stdev_hourly)
| where current_count > threshold
| extend deviation_factor = round(current_count / avg_hourly, 2)
| project UserPrincipalName, current_count, avg_hourly, threshold, deviation_factor
| sort by deviation_factor desc
```

### 8.4 TTP-Based Hunting Allineato ad ATT&CK

Il hunting basato su TTP cerca comportamenti associati a tecniche specifiche di ATT&CK, indipendentemente dagli strumenti usati dall'attaccante.

**Esempio: Hunting per T1053.005 (Scheduled Task)**

Ipotesi: "Un attaccante ha creato scheduled task per mantenere persistenza."

```spl
index=wineventlog sourcetype=WinEventLog:Security EventCode=4698
| spath input=TaskContent output=exec_command path=Task.Actions.Exec.Command
| spath input=TaskContent output=exec_args path=Task.Actions.Exec.Arguments
| eval full_command=exec_command." ".exec_args
| where NOT match(TaskName, "(?i)(Microsoft|Windows|Google|Adobe|Update)")
| where match(full_command, "(?i)(powershell|cmd|wscript|cscript|mshta|regsvr32|rundll32|certutil|bitsadmin)")
| eval risk_score=case(
    match(full_command, "(?i)(IEX|Invoke-Expression|DownloadString|Net\.WebClient)"), 90,
    match(full_command, "(?i)(certutil|bitsadmin).*http"), 80,
    match(full_command, "(?i)(mshta|regsvr32|rundll32)"), 70,
    match(full_command, "(?i)(powershell|cmd)"), 50,
    true(), 30)
| table _time Computer SubjectUserName TaskName full_command risk_score
| sort -risk_score
```

### 8.5 Hunting Playbook Template

Un hunting playbook documenta la procedura in modo riproducibile. Struttura:

```
HUNTING PLAYBOOK: [Nome]
=========================

METADATA
--------
Playbook ID:    HP-2026-015
Author:         [Analyst Name]
Created:        2026-05-07
Last Updated:   2026-05-07
ATT&CK Mapping: T1059.001 (PowerShell), T1105 (Ingress Tool Transfer)
Frequency:      Weekly

HYPOTHESIS
----------
Adversaries are using PowerShell download cradles to stage
tools from external C2 infrastructure within our network.

DATA SOURCES REQUIRED
---------------------
- Sysmon EventID 1 (Process Creation) with command line logging
- PowerShell Script Block Logging (EventID 4104)
- Proxy logs with URL and user agent
- DNS query logs

HUNT QUERIES
------------
[Insert SIEM-specific queries here]

EXPECTED OUTCOMES
-----------------
True Positive: PowerShell process spawned by suspicious parent, executing
  download commands to external URLs not in whitelist.
False Positive: Admin scripts using Invoke-WebRequest to internal repos.

RESPONSE ACTIONS
----------------
1. If suspicious activity found: create incident ticket
2. Isolate affected endpoint
3. Acquire volatile evidence (RAM dump)
4. Block C2 domain/IP at firewall and DNS sinkhole
5. Sweep for additional compromised hosts

DOCUMENTATION
-------------
- Record all findings in hunting journal
- If new detection opportunity found, create Sigma rule
- Update threat model with new intelligence
```

---

## 9. Automazione e SOAR Integration

### 9.1 Panoramica Piattaforme SOAR

Le piattaforme SOAR (Security Orchestration, Automation, and Response) automatizzano i workflow di incident response, riducendo il tempo medio di risposta e standardizzando le procedure.

**Cortex XSOAR (Palo Alto Networks):**

- Marketplace con centinaia di integrazioni predefinite (content pack)
- Playbook engine visuale con branching condizionale
- War Room per collaborazione real-time
- Indicator management con TLP classification
- Machine learning per classificazione automatica degli incidenti

**Splunk SOAR (formerly Phantom):**

- Integrazione nativa con Splunk Enterprise / Splunk Cloud
- Playbook in Python per logica complessa
- Visual Playbook Editor per workflow semplici
- App ecosystem con 350+ integrazioni
- Clustering per alta disponibilita

**Shuffle (Open-Source):**

- SOAR open-source con architettura a microservizi
- Workflow editor grafico basato su browser
- App framework per integrazioni custom
- API-first design
- Deployment container-based (Docker)

### 9.2 Progettazione Playbook

Un playbook SOAR efficace segue un pattern strutturato:

```
TRIGGER: Alert dal SIEM (es. "Brute Force Detected")
    |
    v
TRIAGE AUTOMATICO
    |- Arricchire IP sorgente (GeoIP, threat intel, whois)
    |- Verificare asset di destinazione (criticality, owner, business unit)
    |- Controllare se IP e in whitelist interna
    |- Controllare tentativi totali nelle ultime 24h
    |
    v
DECISIONE (condizionale)
    |-- Se IP whitelisted: chiudere come false positive, documentare
    |-- Se < 50 tentativi E non threat intel match: creare ticket low priority
    |-- Se > 50 tentativi O threat intel match:
    |       |
    |       v
    |   CONTAINMENT AUTOMATICO
    |       |- Bloccare IP al firewall perimetrale (regola temporanea 24h)
    |       |- Disabilitare account compromessi (se login success dopo brute force)
    |       |- Forzare reset password per account targeted
    |       |
    |       v
    |   NOTIFICA
    |       |- Creare incident ticket (ServiceNow/Jira) con severity HIGH
    |       |- Notificare SOC analyst via Slack/Teams
    |       |- Se asset critical: page on-call incident responder
    |       |
    |       v
    |   DOCUMENTAZIONE
    |       |- Allegare arricchimenti e timeline al ticket
    |       |- Registrare azioni di containment
    |       |- Aggiungere IOC al blocklist interno
```

### 9.3 Enrichment Automatico

L'arricchimento automatico aggiunge contesto agli alert, riducendo il tempo di triage dell'analista.

**Fonti di enrichment tipiche:**

| Fonte | Dato Aggiunto | Integrazione |
|-------|--------------|-------------|
| VirusTotal | Reputazione IP/domain/hash | API v3 |
| AbuseIPDB | Report di abuso, confidence score | API v2 |
| Shodan | Porte aperte, servizi, banner | API |
| MaxMind GeoIP | Geolocalizzazione, ASN | Database locale |
| MISP | IOC correlati, event context | API |
| Active Directory | User info, group membership, last logon | LDAP |
| CMDB | Asset criticality, owner, business unit | API/DB |
| Threat Intel Platform | TTP associati, campagne correlate | STIX/TAXII |

### 9.4 Azioni di Containment

Le azioni di containment devono essere reversibili, documentate e autorizzate:

| Azione | Strumento | Reversibilita | Rischio |
|--------|----------|---------------|---------|
| Block IP at firewall | API firewall (Palo Alto, Fortinet) | Si (remove rule) | Basso |
| DNS sinkhole | DNS server config / RPZ | Si (remove entry) | Basso |
| Disable user account | Active Directory / Entra ID | Si (re-enable) | Medio |
| Isolate endpoint | EDR (CrowdStrike, Defender) | Si (unisolate) | Alto |
| Revoke session token | Identity provider API | Si (re-auth needed) | Medio |
| Block hash at endpoint | EDR policy | Si (remove from blocklist) | Basso |

### 9.5 Integrazione Ticketing

Ogni alert che richiede azione umana deve generare un ticket. Il ticket deve contenere:

- Titolo descrittivo con severity e tipo di alert
- Timeline degli eventi correlati
- Arricchimenti automatici (threat intel, asset info, user info)
- Azioni di containment gia eseguite
- Recommended next steps per l'analista
- Link diretto alla query SIEM per il drill-down

Integrazione tipica: SOAR crea ticket via API in ServiceNow/Jira, allega artefatti, assegna al team corretto basato su routing rules (asset owner, severity, tipo di attacco).

---

## 10. Laboratorio Pratico

### 10.1 Architettura del Lab

Il laboratorio utilizza componenti open-source per costruire un ecosistema SIEM completo:

```
+----------------------------------------------------------+
|                    LAB NETWORK (10.0.0.0/24)             |
|                                                          |
|  +---------------+    +---------------+   +------------+ |
|  | Windows Server |    | Ubuntu Server  |   | Kali Linux | |
|  | (DC, target)   |    | (web, target)  |   | (attacker) | |
|  | 10.0.0.10      |    | 10.0.0.20      |   | 10.0.0.99  | |
|  | Wazuh Agent    |    | Wazuh Agent    |   |            | |
|  | Sysmon         |    | auditd         |   |            | |
|  +-------+-------+    +-------+-------+   +------+-----+ |
|          |                     |                  |       |
|          +----------+----------+------------------+       |
|                     |                                     |
|              +------+------+                              |
|              | pfSense FW  |                              |
|              | 10.0.0.1    |                              |
|              | Suricata IDS|                              |
|              +------+------+                              |
|                     |                                     |
|  +------------------+-----------------------------------+ |
|  |            SIEM STACK (10.0.0.0/24)                  | |
|  |                                                      | |
|  |  +-------------+  +-----------+  +---------------+  | |
|  |  | Wazuh Manager|  | TheHive   |  | MISP          |  | |
|  |  | + Indexer    |  | + Cortex  |  | (Threat Intel)|  | |
|  |  | 10.0.0.30   |  | 10.0.0.40 |  | 10.0.0.50     |  | |
|  |  +-------------+  +-----------+  +---------------+  | |
|  +------------------------------------------------------+ |
+----------------------------------------------------------+
```

### 10.2 Installazione Wazuh (Manager + Indexer + Dashboard)

```bash
# Requisiti minimi: 8 GB RAM, 4 CPU, 50 GB disco
# OS: Ubuntu 22.04 LTS

# Scaricare e eseguire l'installer assistito di Wazuh 4.x
curl -sO https://packages.wazuh.com/4.9/wazuh-install.sh
curl -sO https://packages.wazuh.com/4.9/config.yml

# Verificare intergrita (controllare SHA-512 dal sito ufficiale)
# sha512sum wazuh-install.sh
# confrontare con hash pubblicato su https://documentation.wazuh.com/current/installation-guide/

# Editare config.yml con gli IP del lab
# nodes:
#   indexer:
#     - name: wazuh-indexer
#       ip: 10.0.0.30
#   server:
#     - name: wazuh-server
#       ip: 10.0.0.30
#   dashboard:
#     - name: wazuh-dashboard
#       ip: 10.0.0.30

# Eseguire l'installazione (richiede root)
sudo bash wazuh-install.sh -a

# Dopo l'installazione, annotare la password admin generata
# Accedere alla dashboard: https://10.0.0.30:443
```

### 10.3 Deploy degli Agenti Wazuh

**Agente Linux (Ubuntu):**

```bash
# Aggiungere il repository Wazuh
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --dearmor \
  -o /usr/share/keyrings/wazuh.gpg

echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] \
  https://packages.wazuh.com/4.x/apt/ stable main" \
  | sudo tee /etc/apt/sources.list.d/wazuh.list

sudo apt-get update
sudo apt-get install wazuh-agent

# Configurare il manager address
sudo sed -i 's/MANAGER_IP/10.0.0.30/' /var/ossec/etc/ossec.conf

# Abilitare e avviare
sudo systemctl daemon-reload
sudo systemctl enable wazuh-agent
sudo systemctl start wazuh-agent

# Verificare la connessione
sudo /var/ossec/bin/agent-control -l
```

**Agente Windows (con Sysmon):**

```powershell
# Scaricare e installare Sysmon con configurazione SwiftOnSecurity
# Verificare hash del download prima dell'installazione
Invoke-WebRequest -Uri "https://download.sysinternals.com/files/Sysmon.zip" `
  -OutFile "C:\temp\Sysmon.zip"
Expand-Archive -Path "C:\temp\Sysmon.zip" -DestinationPath "C:\temp\Sysmon"

Invoke-WebRequest -Uri "https://raw.githubusercontent.com/SwiftOnSecurity/sysmon-config/master/sysmonconfig-export.xml" `
  -OutFile "C:\temp\sysmonconfig.xml"

# Installare Sysmon
C:\temp\Sysmon\Sysmon64.exe -accepteula -i C:\temp\sysmonconfig.xml

# Installare Wazuh agent
# Scaricare MSI dal sito Wazuh, poi:
msiexec.exe /i wazuh-agent-4.9.0-1.msi /q `
  WAZUH_MANAGER="10.0.0.30" `
  WAZUH_AGENT_NAME="win-dc01"

# Avviare il servizio
NET START Wazuh
```

### 10.4 Configurazione Wazuh per Sysmon

Aggiungere al file `ossec.conf` dell'agente Windows la raccolta dei log Sysmon:

```xml
<ossec_config>
  <localfile>
    <location>Microsoft-Windows-Sysmon/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>

  <localfile>
    <location>Security</location>
    <log_format>eventchannel</log_format>
    <query>
      Event/System[EventID=4624 or EventID=4625 or EventID=4648 or
                   EventID=4672 or EventID=4688 or EventID=4698 or
                   EventID=4720 or EventID=4732 or EventID=1102]
    </query>
  </localfile>

  <localfile>
    <location>Microsoft-Windows-PowerShell/Operational</location>
    <log_format>eventchannel</log_format>
    <query>
      Event/System[EventID=4103 or EventID=4104]
    </query>
  </localfile>
</ossec_config>
```

### 10.5 Installazione TheHive + Cortex

TheHive e una piattaforma di incident response; Cortex fornisce il motore di enrichment e response.

```bash
# TheHive 5 con Docker Compose (lab environment)
# Creare directory per i dati
sudo mkdir -p /opt/thehive/{db,data,index}
sudo mkdir -p /opt/cortex/{jobs,docker}

# docker-compose.yml (estratto chiave)
# ---
# services:
#   cassandra:
#     image: cassandra:4.1
#     volumes:
#       - /opt/thehive/db:/var/lib/cassandra
#     environment:
#       - CASSANDRA_CLUSTER_NAME=TheHive
#     restart: unless-stopped
#
#   elasticsearch:
#     image: docker.elastic.co/elasticsearch/elasticsearch:7.17.18
#     environment:
#       - discovery.type=single-node
#       - xpack.security.enabled=false
#       - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
#     volumes:
#       - /opt/thehive/index:/usr/share/elasticsearch/data
#     restart: unless-stopped
#
#   thehive:
#     image: strangebee/thehive:5.3
#     depends_on:
#       - cassandra
#       - elasticsearch
#     ports:
#       - "9000:9000"
#     volumes:
#       - /opt/thehive/data:/opt/thp/thehive/data
#     environment:
#       - JVM_OPTS=-Xms1g -Xmx1g
#     restart: unless-stopped
#
#   cortex:
#     image: thehiveproject/cortex:3.1.8
#     depends_on:
#       - elasticsearch
#     ports:
#       - "9001:9001"
#     volumes:
#       - /opt/cortex/jobs:/opt/cortex/jobs
#       - /var/run/docker.sock:/var/run/docker.sock
#     restart: unless-stopped

# Avviare lo stack
# docker compose up -d

# Accedere:
# TheHive:  http://10.0.0.40:9000 (admin@thehive.local / secret)
# Cortex:   http://10.0.0.40:9001
```

### 10.6 Installazione MISP

```bash
# MISP con Docker (lab environment)
# Repository ufficiale: https://github.com/MISP/misp-docker

# Clonare il repository
# git clone https://github.com/MISP/misp-docker.git /opt/misp-docker
# cd /opt/misp-docker

# Copiare e configurare il template
# cp template.env .env
# Editare .env:
#   MISP_BASEURL=https://10.0.0.50
#   MISP_ADMIN_EMAIL=admin@lab.local
#   MISP_ADMIN_PASSPHRASE=<strong-password>

# Avviare
# docker compose up -d

# Accedere: https://10.0.0.50 (admin@lab.local / password configurata)
```

### 10.7 Integrazione Wazuh con TheHive

Configurare Wazuh per inviare alert a TheHive tramite il modulo di integrazione:

```xml
<!-- /var/ossec/etc/ossec.conf sul Wazuh Manager -->
<ossec_config>
  <integration>
    <name>custom-thehive.py</name>
    <hook_url>http://10.0.0.40:9000</hook_url>
    <api_key>YOUR_THEHIVE_API_KEY</api_key>
    <level>10</level>
    <alert_format>json</alert_format>
  </integration>
</ossec_config>
```

**Script di integrazione custom (semplificato):**

```python
#!/usr/bin/env python3
"""Wazuh-TheHive integration: forwards high-severity Wazuh alerts
to TheHive as new alerts for SOC triage."""

import json
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError


THEHIVE_URL = "http://10.0.0.40:9000"
THEHIVE_API_KEY = ""  # Set via environment or config, never hardcoded

SEVERITY_MAP = {
    range(0, 5): 1,    # Low
    range(5, 10): 2,   # Medium
    range(10, 13): 3,  # High
    range(13, 16): 4,  # Critical
}


def _map_severity(level: int) -> int:
    for level_range, severity in SEVERITY_MAP.items():
        if level in level_range:
            return severity
    return 2


def create_thehive_alert(wazuh_alert: dict) -> None:
    rule = wazuh_alert.get("rule", {})
    agent = wazuh_alert.get("agent", {})

    alert_payload = {
        "type": "wazuh",
        "source": "Wazuh SIEM",
        "sourceRef": wazuh_alert.get("id", "unknown"),
        "title": f"[Wazuh] {rule.get('description', 'Unknown alert')}",
        "description": (
            f"**Rule ID:** {rule.get('id', 'N/A')}\n"
            f"**Level:** {rule.get('level', 'N/A')}\n"
            f"**Agent:** {agent.get('name', 'N/A')} ({agent.get('ip', 'N/A')})\n"
            f"**Full Log:**\n```\n{wazuh_alert.get('full_log', 'N/A')}\n```"
        ),
        "severity": _map_severity(rule.get("level", 5)),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000"),
        "tags": rule.get("groups", []),
        "artifacts": [],
    }

    # Extract observables from alert data
    src_ip = wazuh_alert.get("data", {}).get("srcip")
    if src_ip:
        alert_payload["artifacts"].append({
            "dataType": "ip",
            "data": src_ip,
            "message": "Source IP from Wazuh alert",
        })

    data = json.dumps(alert_payload).encode("utf-8")
    req = Request(
        f"{THEHIVE_URL}/api/alert",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {THEHIVE_API_KEY}",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                print(f"Alert created in TheHive: {rule.get('description')}")
            else:
                print(f"TheHive returned status {resp.status}", file=sys.stderr)
    except URLError as exc:
        print(f"Failed to send alert to TheHive: {exc}", file=sys.stderr)


def main():
    alert_file = sys.argv[1] if len(sys.argv) > 1 else None
    if alert_file is None:
        print("Usage: custom-thehive.py <alert_file>", file=sys.stderr)
        sys.exit(1)

    with open(alert_file) as f:
        alert_data = json.load(f)

    create_thehive_alert(alert_data)


if __name__ == "__main__":
    main()
```

### 10.8 Scrivere Detection Rules

**Esercizio 1: Rilevare SSH brute force su Linux**

Regola Wazuh custom:

```xml
<group name="local,sshd,brute_force">

  <rule id="100030" level="10" frequency="8" timeframe="120">
    <if_matched_sid>5710</if_matched_sid>
    <same_source_ip />
    <description>SSH brute force attack from same source (8+ failures in 2 min)</description>
    <group>authentication_failures,brute_force,</group>
    <mitre>
      <id>T1110.001</id>
    </mitre>
  </rule>

  <rule id="100031" level="12" frequency="20" timeframe="300">
    <if_matched_sid>5710</if_matched_sid>
    <same_source_ip />
    <description>Sustained SSH brute force attack (20+ failures in 5 min)</description>
    <group>authentication_failures,brute_force,</group>
    <mitre>
      <id>T1110.001</id>
    </mitre>
  </rule>

  <rule id="100032" level="14">
    <if_sid>5715</if_sid>
    <if_matched_sid>100030</if_matched_sid>
    <same_source_ip />
    <description>SSH login success after brute force — possible compromise</description>
    <group>authentication_success,brute_force,compromise,</group>
    <mitre>
      <id>T1110.001</id>
      <id>T1078</id>
    </mitre>
  </rule>

</group>
```

**Esercizio 2: Rilevare privilege escalation su Linux**

```xml
<group name="local,privilege_escalation">

  <rule id="100040" level="12">
    <if_sid>5401</if_sid>
    <match>COMMAND=</match>
    <regex>visudo|usermod|passwd|chattr|chmod.*/etc/shadow</regex>
    <description>Sensitive privilege escalation command executed via sudo</description>
    <group>sudo,privilege_escalation,</group>
    <mitre>
      <id>T1548.003</id>
    </mitre>
  </rule>

  <rule id="100041" level="14">
    <decoded_as>syslog</decoded_as>
    <match>pkexec</match>
    <regex>COMMAND=|Executing</regex>
    <description>pkexec command execution detected — potential CVE exploit</description>
    <group>privilege_escalation,</group>
    <mitre>
      <id>T1068</id>
    </mitre>
  </rule>

</group>
```

**Esercizio 3: Sigma rule per rilevare Mimikatz**

```yaml
title: Mimikatz Command Line Indicators
id: a642964e-bead-4bed-8910-1bb4d90a1cb6
status: stable
description: >
  Detects command line arguments commonly associated with Mimikatz,
  regardless of the binary name (handles renamed binaries).
references:
  - https://attack.mitre.org/software/S0002/
author: SOC Team
date: 2026-05-07
tags:
  - attack.credential_access
  - attack.t1003.001
  - attack.t1003.006
logsource:
  category: process_creation
  product: windows
detection:
  selection_commands:
    CommandLine|contains:
      - 'sekurlsa::logonpasswords'
      - 'sekurlsa::wdigest'
      - 'sekurlsa::kerberos'
      - 'lsadump::dcsync'
      - 'lsadump::lsa /patch'
      - 'lsadump::sam'
      - 'privilege::debug'
      - 'token::elevate'
      - 'kerberos::golden'
      - 'kerberos::ptt'
      - 'misc::skeleton'
  selection_binary:
    Image|endswith:
      - '\mimikatz.exe'
      - '\mimi.exe'
    OriginalFileName: 'mimikatz.exe'
  condition: selection_commands or selection_binary
falsepositives:
  - Legitimate penetration testing (verify with the security team)
level: critical
```

### 10.9 Analisi Forense di Timeline — Esercizio Guidato

**Scenario:** alle ore 14:30 UTC del 2026-05-07, il SOC riceve un alert per login success dopo brute force su SSH del server WEB-PROD-01. Ricostruire la timeline dell'attacco.

**Passo 1: Raccogliere i log rilevanti**

```bash
# Dal Wazuh Manager: esportare gli alert per l'agente WEB-PROD-01
# nelle ultime 24 ore
curl -s -k -X GET "https://10.0.0.30:55000/alerts?agents_list=002&limit=500" \
  -H "Authorization: Bearer $WAZUH_TOKEN" | \
  python3 -m json.tool > /tmp/evidence/wazuh_alerts_agent002.json

# Dal server target: copiare i log di autenticazione
# (su working copy, mai direttamente sull'evidenza)
scp admin@10.0.0.20:/var/log/auth.log /tmp/evidence/auth.log
sha256sum /tmp/evidence/auth.log > /tmp/evidence/auth.log.sha256

# Log di accesso del web server
scp admin@10.0.0.20:/var/log/nginx/access.log /tmp/evidence/nginx_access.log
sha256sum /tmp/evidence/nginx_access.log > /tmp/evidence/nginx_access.log.sha256
```

**Passo 2: Costruire la timeline unificata**

```bash
# Utilizzare lo script timeline_generator.py sviluppato nella sezione 5.1
python3 timeline_generator.py \
  /tmp/evidence/auth.log \
  /tmp/evidence/nginx_access.log \
  > /tmp/evidence/unified_timeline.jsonl
```

**Passo 3: Analizzare la timeline**

Cercare la sequenza di eventi tipica di un attacco:

```
14:10 UTC - Primi tentativi SSH falliti da IP esterno (203.0.113.42)
14:10-14:28 - 247 tentativi di brute force SSH (multipli username)
14:28 UTC - Login SSH success con utente "deploy" da 203.0.113.42
14:29 UTC - sudo su (escalation a root)
14:30 UTC - wget eseguito (download di strumento da IP 198.51.100.10)
14:31 UTC - Creazione utente "svc-backup" con UID 0
14:32 UTC - Installazione di reverse shell come servizio systemd
14:33 UTC - Connessione outbound sulla porta 4444 verso 198.51.100.10
14:35 UTC - Tentativo di cancellazione /var/log/auth.log (parziale)
```

**Passo 4: Documentare i finding**

```
FORENSIC FINDINGS — Incident IR-2026-0042
==========================================

Attack Vector:     SSH brute force from 203.0.113.42
Compromised Account: deploy (weak password)
Privilege Escalation: sudo su to root (deploy had NOPASSWD sudo)
Persistence:       1) User svc-backup with UID 0 created
                   2) Reverse shell systemd service installed
C2 Communication:  Outbound to 198.51.100.10:4444
Anti-Forensics:    Partial deletion of /var/log/auth.log (detected
                   via gap in log timeline and FIM alert)
Data Exfiltration:  Under investigation

IOCs Extracted:
  - 203.0.113.42 (attacker source IP)
  - 198.51.100.10 (C2 server)
  - /tmp/.x11-unix/svc (reverse shell binary, SHA-256: ...)
  - svc-backup (malicious user account)

Recommended Actions:
  1. Block 203.0.113.42 and 198.51.100.10 at perimeter firewall
  2. Kill reverse shell process, remove systemd service
  3. Delete svc-backup account
  4. Rotate credentials for deploy account
  5. Enforce key-based SSH auth, disable password authentication
  6. Remove NOPASSWD from deploy sudoers entry
  7. Sweep all hosts for IOCs
  8. Review SSH access policy across the environment
```

### 10.10 Configurazione auditd Immutabile per Linux

Il framework di audit del kernel Linux (`auditd`) e uno strumento fondamentale per il monitoraggio di sicurezza e la forensic readiness su sistemi Linux. Una configurazione corretta e immutabile garantisce che gli attaccanti non possano disabilitare il logging dopo aver ottenuto accesso privilegiato.

**Architettura del sistema auditd:**

Il sistema di audit Linux opera a livello kernel. Il componente `kauditd` nel kernel intercetta le system call e genera record di audit, che vengono inviati al demone userspace `auditd` tramite un socket netlink. `auditd` scrive i record nel file `/var/log/audit/audit.log`. Il tool `auditctl` gestisce le regole a runtime, mentre `ausearch` e `aureport` analizzano i log.

**Organizzazione delle regole in `/etc/audit/rules.d/`:**

Le regole vengono organizzate in file numerati per garantire l'ordine di caricamento corretto. La convenzione standard segue il pattern:

```
/etc/audit/rules.d/
├── 10-base-config.rules        # Configurazione base del buffer e failure mode
├── 20-filters.rules            # Filtri per escludere eventi ad alto volume non rilevanti
├── 30-stig-authentication.rules # Regole STIG per autenticazione
├── 31-stig-privileged.rules    # Regole STIG per comandi privilegiati
├── 32-power-abuse.rules        # Abuso di privilegi amministrativi
├── 33-file-integrity.rules     # Monitoraggio integrita file critici
├── 40-local-custom.rules       # Regole personalizzate per l'organizzazione
├── 50-persistence-detection.rules # Rilevamento tecniche di persistenza
├── 70-network-monitoring.rules # Monitoraggio connessioni di rete sospette
├── 90-finalize.rules           # Flag immutabile — DEVE essere l'ultimo file
```

**Esempio: 10-base-config.rules**

```bash
## Buffer e configurazione base
## Aumentare il buffer per ambienti ad alto volume
-b 8192

## Failure mode: 1 = printk (log), 2 = panic (arresta il sistema se l'audit fallisce)
## Per sistemi ad alta sicurezza, usare -f 2
-f 1

## Rate limit per prevenire DoS via audit flooding (0 = nessun limite)
-r 0
```

**Esempio: 33-file-integrity.rules**

```bash
## Monitoraggio file critici per il sistema
## /etc/passwd e /etc/shadow — creazione/modifica utenti
-w /etc/passwd -p wa -k identity_modification
-w /etc/shadow -p wa -k identity_modification
-w /etc/group -p wa -k identity_modification
-w /etc/gshadow -p wa -k identity_modification

## Configurazione di rete
-w /etc/hosts -p wa -k network_config
-w /etc/hostname -p wa -k network_config
-w /etc/resolv.conf -p wa -k network_config
-w /etc/sysctl.conf -p wa -k network_config

## Configurazione SSH
-w /etc/ssh/sshd_config -p wa -k ssh_config

## Configurazione cron (persistenza)
-w /etc/crontab -p wa -k cron_modification
-w /etc/cron.d/ -p wa -k cron_modification
-w /etc/cron.daily/ -p wa -k cron_modification
-w /etc/cron.hourly/ -p wa -k cron_modification
-w /var/spool/cron/ -p wa -k cron_modification

## Configurazione sudoers
-w /etc/sudoers -p wa -k sudoers_modification
-w /etc/sudoers.d/ -p wa -k sudoers_modification

## Configurazione systemd (persistenza tramite servizi)
-w /etc/systemd/ -p wa -k systemd_modification
-w /usr/lib/systemd/ -p wa -k systemd_modification

## Librerie condivise (DLL sideloading equivalente)
-w /etc/ld.so.conf -p wa -k library_config
-w /etc/ld.so.preload -p wa -k library_preload

## Configurazione PAM
-w /etc/pam.d/ -p wa -k pam_modification

## Configurazione audit stessa
-w /etc/audit/ -p wa -k audit_config_modification
-w /etc/audisp/ -p wa -k audit_config_modification
```

**Esempio: 50-persistence-detection.rules**

```bash
## Rilevamento tecniche di persistenza MITRE ATT&CK

## T1053.003 — Scheduled Task/Job: Cron
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/crontab -k T1053_cron
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/at -k T1053_at

## T1543.002 — Systemd Service
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/systemctl -k T1543_systemd

## T1136.001 — Create Account: Local Account
-a always,exit -F arch=b64 -S execve -F path=/usr/sbin/useradd -k T1136_useradd
-a always,exit -F arch=b64 -S execve -F path=/usr/sbin/adduser -k T1136_adduser

## T1222.002 — File and Directory Permissions Modification: Linux
-a always,exit -F arch=b64 -S chmod,fchmod,fchmodat -k T1222_chmod
-a always,exit -F arch=b64 -S chown,fchown,fchownat,lchown -k T1222_chown

## T1548.001 — Setuid/Setgid
-a always,exit -F arch=b64 -S chmod,fchmod,fchmodat -F a2&06000 -k T1548_setuid

## T1070.006 — Timestomping
-a always,exit -F arch=b64 -S utimes,utimensat,futimesat -k T1070_timestomp

## T1014 — Rootkit (kernel module loading)
-a always,exit -F arch=b64 -S init_module,finit_module,delete_module -k T1014_kernel_module

## T1059 — Command-Line Interface
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/python3 -k T1059_python
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/perl -k T1059_perl
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/ruby -k T1059_ruby
```

**Esempio: 90-finalize.rules**

```bash
## === FINALIZE: RENDERE LE REGOLE IMMUTABILI ===
## Questa riga DEVE essere l'ultima. Dopo l'applicazione, le regole
## non possono essere modificate a runtime. L'unico modo per cambiarle
## e riavviare il sistema.
## ATTENZIONE: testare TUTTE le regole prima di attivare questo flag.
-e 2
```

Dopo la creazione dei file, caricare le regole con:

```bash
# Rigenerare il file di regole aggregato
sudo augenrules --load

# Verificare che le regole siano caricate
sudo auditctl -l | wc -l

# Verificare lo stato immutabile
sudo auditctl -s
# Output atteso: enabled 2 (immutable)
```

**Forwarding dei log auditd al SIEM:**

Per inviare i log di audit al SIEM, si configura il plugin `audisp-remote` (o `audispd` nelle versioni precedenti) oppure si usa un agente SIEM dedicato. Configurazione tramite `audisp-remote`:

```bash
# /etc/audit/plugins.d/syslog.conf (per forwarding via syslog)
active = yes
direction = out
path = /sbin/audisp-syslog
type = always
args = LOG_LOCAL6
format = string

# Poi configurare rsyslog per inoltrare local6 al SIEM:
# /etc/rsyslog.d/audit-forward.conf
# local6.* @@siem.example.com:1514;RSYSLOG_SyslogProtocol23Format
```

In alternativa, utilizzare l'agente Wazuh che legge nativamente `/var/log/audit/audit.log` e invia gli eventi al manager con parsing automatico dei record di audit.

### 10.11 Checklist Operativa di Forensic Readiness

La seguente checklist copre tutti gli aspetti della forensic readiness trattati in questo modulo. Deve essere utilizzata come strumento di audit periodico (raccomandazione: revisione trimestrale).

```
CHECKLIST DI FORENSIC READINESS
================================
Data dell'audit: ____________
Auditor: ____________
Prossima revisione: ____________

1. INFRASTRUTTURA DI LOG COLLECTION
   [ ] Inventario completo delle sorgenti di log documentato e aggiornato
   [ ] Tutti i sistemi critici inviano log al SIEM
   [ ] Protocolli di trasporto sicuri (TLS) per tutte le sorgenti
   [ ] Buffer e backpressure configurati per gestire burst
   [ ] Monitoraggio del drop rate e della latenza di ingestione
   [ ] Agenti SIEM / forwarder aggiornati all'ultima versione stabile
   [ ] Log collection ridondante (almeno 2 destinazioni per sorgenti critiche)

2. NORMALIZZAZIONE E PARSING
   [ ] Tutti gli eventi mappati a Common Information Model (CIM)
   [ ] Timestamp normalizzati a UTC
   [ ] Sincronizzazione NTP verificata su tutti i sistemi (drift < 1s)
   [ ] Enrichment configurato (GeoIP, threat intel, asset inventory)
   [ ] Parser testati e validati per ogni sorgente

3. RETENTION E STORAGE
   [ ] Politica di retention documentata e approvata dal management
   [ ] Retention allineata ai requisiti normativi applicabili
       (PCI DSS: 12 mesi, HIPAA: 6 anni, SOX: 7 anni, NIS2/DORA: adeguato)
   [ ] Tier di storage configurati (hot/warm/cold/frozen)
   [ ] Capacity planning aggiornato (proiezione 12 mesi)
   [ ] Procedura di purging documentata e automatizzata
   [ ] Backup dei log su media separato

4. DETECTION ENGINEERING
   [ ] Regole di correlazione mappate a MITRE ATT&CK
   [ ] Copertura ATT&CK documentata e gap identificati
   [ ] Processo di tuning falsi positivi attivo e documentato
   [ ] Revisione trimestrale delle regole di detection
   [ ] Pipeline Detection-as-Code configurata (version control, CI/CD)
   [ ] Sigma rules convertite e testate per il backend SIEM in uso

5. INTEGRITA E CHAIN OF CUSTODY
   [ ] Hash chain implementata per i log archiviati
   [ ] Storage immutabile (WORM/Object Lock) per log di compliance
   [ ] Template chain of custody approvato e disponibile
   [ ] Personale formato sulla procedura di raccolta evidenze
   [ ] Strumenti di acquisizione forense validati e documentati
   [ ] Procedura di verifica integrita testata

6. INCIDENT RESPONSE READINESS
   [ ] Playbook SOAR configurati per i casi d'uso principali
   [ ] Enrichment automatico funzionante (threat intel, asset, identity)
   [ ] Azioni di containment testate e reversibili
   [ ] Integrazione ticketing attiva (ServiceNow/Jira)
   [ ] Escalation path documentati con SLA
   [ ] War room / canale di comunicazione predefinito

7. THREAT HUNTING
   [ ] Programma di threat hunting con cadenza regolare
   [ ] Hunting playbook documentati e aggiornati
   [ ] IOC sweep automatizzato con feed di threat intelligence
   [ ] Risultati del hunting documentati e condivisi

8. CONFIGURAZIONE SISTEMI SORGENTE
   [ ] Windows: audit policy avanzata configurata (EventID critici)
   [ ] Windows: Sysmon installato con configurazione community-vetted
   [ ] Windows: PowerShell Script Block Logging abilitato
   [ ] Linux: auditd configurato con regole immutabili (-e 2)
   [ ] Linux: File integrity monitoring attivo su file critici
   [ ] Cloud: CloudTrail/Activity Log/Audit Logs abilitati
   [ ] Cloud: log data-plane (S3, Lambda, ecc.) configurati dove necessario
   [ ] Network: firewall, IDS/IPS, proxy log centralizzati

9. CONFORMITA NORMATIVA
   [ ] Mapping tra requisiti normativi e sorgenti di log documentato
   [ ] Rapporti di compliance automatizzati
   [ ] Audit trail per accessi ai dati regolamentati (PCI, HIPAA, GDPR)
   [ ] Procedura di notifica breach entro i limiti temporali normativi
       (GDPR: 72h, NIS2: 24h early warning + 72h dettaglio, DORA: specifico)

10. TEST E VALIDAZIONE
    [ ] Simulazione di incidente eseguita almeno 1 volta/anno
    [ ] Capacita di ricostruire timeline verificata
    [ ] Regole di detection testate con true positive noti
    [ ] Tempo medio di detection (MTTD) misurato e tracciato
    [ ] Tempo medio di risposta (MTTR) misurato e tracciato
    [ ] Recovery procedure testate
```

---

## Esercizi di Consolidamento

### Esercizio A — Sigma Rule Writing

Scrivere tre regole Sigma per i seguenti scenari:

1. Rilevamento di `certutil -decode` usato per decodificare un payload (T1140)
2. Rilevamento di Windows Defender disabilitato tramite PowerShell (T1562.001)
3. Rilevamento di accesso anomalo a share di rete (accesso a piu di 10 share distinti in 5 minuti) (T1135)

Per ciascuna regola: definire logsource, detection con selection e condition, falsepositives, level, e tag ATT&CK.

### Esercizio B — SPL Query Development

Scrivere query SPL per:

1. Identificare tutti i processi lanciati da `outlook.exe` che effettuano connessioni di rete esterne (indicatore di phishing con macro)
2. Calcolare il baseline di login per utente (media e deviazione standard) e identificare anomalie nel giorno corrente
3. Correlare tentativi di login falliti con login success successivo dallo stesso IP entro 30 minuti

### Esercizio C — Lab Integration

1. Installare Wazuh nel lab seguendo le istruzioni della sezione 10.2
2. Deployare agenti su almeno 2 sistemi (1 Windows, 1 Linux)
3. Configurare la raccolta di Sysmon log su Windows
4. Scrivere e testare le regole custom delle sezioni 10.8
5. Eseguire un attacco simulato (SSH brute force da Kali) e verificare che gli alert vengano generati
6. Integrare Wazuh con TheHive e verificare che gli alert vengano trasformati in alert TheHive

### Esercizio D — Forensic Readiness Audit

Condurre un audit di forensic readiness sulla propria infrastruttura:

1. Inventariare tutte le sorgenti di log attive
2. Per ciascuna sorgente, documentare: formato, metodo di raccolta, retention attuale, gap di visibilita
3. Verificare che i timestamp siano sincronizzati (NTP) e in formato UTC
4. Testare la capacita di ricostruire una timeline per un incidente simulato
5. Verificare l'integrita dei log con hash chain
6. Documentare la procedura di chain of custody per le evidenze digitali
7. Identificare e pianificare la remediation dei gap

---

## Riferimenti

- MITRE ATT&CK Framework: https://attack.mitre.org/
- Sigma Rules Repository: https://github.com/SigmaHQ/sigma
- NIST SP 800-86: Guide to Integrating Forensic Techniques into Incident Response
- NIST SP 800-92: Guide to Computer Security Log Management
- RFC 3227: Guidelines for Evidence Collection and Archiving
- RFC 5424: The Syslog Protocol
- RFC 5425: Transport Layer Security (TLS) Transport Mapping for Syslog
- ISO 27037: Guidelines for identification, collection, acquisition and preservation of digital evidence
- ISO 27042: Guidelines for the analysis and interpretation of digital evidence
- Wazuh Documentation: https://documentation.wazuh.com/
- Elastic Security Documentation: https://www.elastic.co/guide/en/security/current/
- Splunk SPL Reference: https://docs.splunk.com/Documentation/Splunk/latest/SearchReference
- TheHive Project: https://thehive-project.org/
- MISP Project: https://www.misp-project.org/
