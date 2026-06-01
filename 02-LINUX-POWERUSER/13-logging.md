# Logging Linux — Guida Completa

> **Modulo 13** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **journald default; `Storage=persistent` mandatory.**
2. **rsyslog/syslog-ng per forward a SIEM.**
3. **logrotate (legacy file logs) o journald `SystemMaxUse`.**
4. **OTel logs SDK 2024+: vendor-neutral.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Logging Linux](#architettura-logging-linux)
  - [Pipeline completa: dal kernel al SIEM](#pipeline-completa-dal-kernel-al-siem)
  - [Kernel ring buffer](#kernel-ring-buffer)
  - [systemd-journald nel flusso](#systemd-journald-nel-flusso)
  - [rsyslog/syslog-ng nel flusso](#rsyslogsyslog-ng-nel-flusso)
  - [Storage e SIEM](#storage-e-siem)
- [Facility e Severity: Riferimento RFC 5424](#facility-e-severity-riferimento-rfc-5424)
  - [Tabella facility completa](#tabella-facility-completa)
  - [Tabella severity completa](#tabella-severity-completa)
  - [Mappatura pratica facility→file](#mappatura-pratica-facilityfile)
  - [Calcolo del PRI value](#calcolo-del-pri-value)
- [Journald: Deep Dive](#journald-deep-dive)
  - [Configurazione journald](#configurazione-journald)
  - [Storage persistente](#storage-persistente)
  - [Dimensionamento e rotazione journal](#dimensionamento-e-rotazione-journal)
  - [journalctl: filtri avanzati](#journalctl-filtri-avanzati)
  - [Filtri per unit](#filtri-per-unit)
  - [Filtri per priorità](#filtri-per-priorità)
  - [Filtri per tempo](#filtri-per-tempo)
  - [Filtri per boot](#filtri-per-boot)
  - [Filtri per PID, UID, GID](#filtri-per-pid-uid-gid)
  - [Filtri combinati e output](#filtri-combinati-e-output)
  - [Campi metadata e cursori](#campi-metadata-e-cursori)
  - [Journal remoto](#journal-remoto)
- [rsyslog: Deep Dive](#rsyslog-deep-dive)
  - [Architettura modulare rsyslog](#architettura-modulare-rsyslog)
  - [Moduli di input](#moduli-di-input)
  - [Moduli di output](#moduli-di-output)
  - [Template rsyslog](#template-rsyslog)
  - [Rulesets](#rulesets)
  - [Filtri property-based](#filtri-property-based)
  - [Nomi file dinamici](#nomi-file-dinamici)
  - [Queue rsyslog](#queue-rsyslog)
  - [TLS in rsyslog](#tls-in-rsyslog)
  - [File drop-in rsyslog](#file-drop-in-rsyslog)
- [syslog-ng: Configurazione e Confronto](#syslog-ng-configurazione-e-confronto)
  - [Sintassi di configurazione syslog-ng](#sintassi-di-configurazione-syslog-ng)
  - [Source syslog-ng](#source-syslog-ng)
  - [Destination syslog-ng](#destination-syslog-ng)
  - [Filter syslog-ng](#filter-syslog-ng)
  - [Log path syslog-ng](#log-path-syslog-ng)
  - [Confronto rsyslog vs syslog-ng](#confronto-rsyslog-vs-syslog-ng)
- [Logrotate: Gestione Rotazione](#logrotate-gestione-rotazione)
  - [Configurazione globale logrotate](#configurazione-globale-logrotate)
  - [Tutte le direttive logrotate](#tutte-le-direttive-logrotate)
  - [Esempi configurazione per servizio](#esempi-configurazione-per-servizio)
  - [Script personalizzati logrotate](#script-personalizzati-logrotate)
  - [Compressione avanzata](#compressione-avanzata)
  - [Debug e test logrotate](#debug-e-test-logrotate)
- [Logging Centralizzato](#logging-centralizzato)
  - [rsyslog → server remoto](#rsyslog--server-remoto)
  - [Stack ELK (Elasticsearch + Logstash + Kibana)](#stack-elk-elasticsearch--logstash--kibana)
  - [Stack EFK (Elasticsearch + Fluentd + Kibana)](#stack-efk-elasticsearch--fluentd--kibana)
  - [Loki + Grafana](#loki--grafana)
  - [Graylog](#graylog)
  - [Scelta dello stack](#scelta-dello-stack)
- [Logging Strutturato](#logging-strutturato)
  - [Formato JSON](#formato-json)
  - [Coppie chiave-valore](#coppie-chiave-valore)
  - [Correlation ID](#correlation-id)
  - [Structured logging in journald](#structured-logging-in-journald)
- [Best Practice per il Logging Applicativo](#best-practice-per-il-logging-applicativo)
  - [Livelli di log: quando usare cosa](#livelli-di-log-quando-usare-cosa)
  - [Contesto nei messaggi di log](#contesto-nei-messaggi-di-log)
  - [Rate limiting dei log](#rate-limiting-dei-log)
  - [Filtraggio dati sensibili](#filtraggio-dati-sensibili)
  - [Log e performance](#log-e-performance)
- [Audit Logging: auditd](#audit-logging-auditd)
  - [Architettura audit framework](#architettura-audit-framework)
  - [Regole auditd](#regole-auditd)
  - [aureport: reportistica](#aureport-reportistica)
  - [ausearch: ricerca eventi](#ausearch-ricerca-eventi)
  - [Compliance STIG e CIS](#compliance-stig-e-cis)
- [Kernel Logging](#kernel-logging)
  - [dmesg e ring buffer del kernel](#dmesg-e-ring-buffer-del-kernel)
  - [/dev/kmsg](#devkmsg)
  - [Livelli KERN_*](#livelli-kern)
  - [Crash dump e kdump](#crash-dump-e-kdump)
- [Strumenti di Analisi Log](#strumenti-di-analisi-log)
  - [Pattern grep/awk/sed](#pattern-grepawksed)
  - [lnav: navigatore log avanzato](#lnav-navigatore-log-avanzato)
  - [GoAccess: analisi log web](#goaccess-analisi-log-web)
  - [multitail: visualizzazione multi-file](#multitail-visualizzazione-multi-file)
  - [jq per log JSON](#jq-per-log-json)
- [Alerting Basato sui Log](#alerting-basato-sui-log)
  - [Pattern di alerting](#pattern-di-alerting)
  - [Anomaly detection](#anomaly-detection)
  - [Integrazione con sistemi di notifica](#integrazione-con-sistemi-di-notifica)
- [Policy di Retention dei Log](#policy-di-retention-dei-log)
  - [Requisiti regolamentari](#requisiti-regolamentari)
  - [GDPR e log](#gdpr-e-log)
  - [PCI-DSS e log](#pci-dss-e-log)
  - [Ottimizzazione dello storage](#ottimizzazione-dello-storage)
- [Logging Orientato alla Sicurezza](#logging-orientato-alla-sicurezza)
  - [Login falliti e brute force](#login-falliti-e-brute-force)
  - [Monitoraggio sudo](#monitoraggio-sudo)
  - [Accesso ai file sensibili](#accesso-ai-file-sensibili)
  - [Connessioni di rete](#connessioni-di-rete)
  - [Integrità dei log](#integrità-dei-log)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Guida Implementativa: Logging Centralizzato da Zero](#guida-implementativa-logging-centralizzato-da-zero)
- [Best Practices Finali](#best-practices-finali)

---

## Panoramica

I log sono la fonte primaria di informazione per diagnostica, sicurezza e compliance. Linux offre due sistemi di logging complementari: **journald** (strutturato, binario, parte di systemd) e **rsyslog** (tradizionale, testo, flessibile). La rotazione (logrotate) previene il riempimento del disco. In ambienti enterprise, il logging centralizzato (ELK, Loki) è essenziale per correlazione e analisi.

Il logging in Linux non è un singolo componente ma una **pipeline multi-stadio**: i messaggi nascono dal kernel o dalle applicazioni, attraversano uno o più demoni di logging, vengono scritti su disco locale o inoltrati a sistemi remoti, e infine vengono analizzati, correlati e archiviati. Comprendere ogni stadio di questa pipeline è essenziale per diagnosticare problemi, soddisfare requisiti di compliance e costruire infrastrutture di osservabilità robuste.

Questo modulo copre l'intera pipeline in profondità: dall'architettura fondamentale fino alle implementazioni enterprise, passando per ogni componente (journald, rsyslog, syslog-ng, auditd, logrotate), gli strumenti di analisi, le best practice di sicurezza e le policy di retention regolamentare.

---

## Architettura Logging Linux

### Pipeline completa: dal kernel al SIEM

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SORGENTI DEI MESSAGGI                           │
│                                                                        │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Kernel   │  │ Applicazioni │  │ systemd  │  │  Audit subsystem │   │
│  │(printk)  │  │ (syslog API) │  │ (units)  │  │    (auditd)      │   │
│  └────┬─────┘  └──────┬───────┘  └────┬─────┘  └────────┬─────────┘   │
│       │               │               │                  │             │
└───────┼───────────────┼───────────────┼──────────────────┼─────────────┘
        │               │               │                  │
        ▼               ▼               ▼                  ▼
┌───────────────────────────────────────────────┐  ┌───────────────────┐
│           systemd-journald                     │  │ /var/log/audit/   │
│  ┌──────────────────────────────────────────┐ │  │  audit.log        │
│  │ Journal binario strutturato              │ │  └───────────────────┘
│  │ /run/log/journal/ (volatile)             │ │
│  │ /var/log/journal/ (persistente)          │ │
│  └──────────────────┬───────────────────────┘ │
│                     │ forward via socket       │
└─────────────────────┼─────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              rsyslog / syslog-ng                                        │
│                                                                         │
│  ┌─────────┐    ┌──────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ Input   │───▶│ Parser   │───▶│  Filter /    │───▶│   Output      │  │
│  │ modules │    │ modules  │    │  Ruleset     │    │   modules     │  │
│  └─────────┘    └──────────┘    └──────────────┘    └───────┬───────┘  │
│                                                             │          │
└─────────────────────────────────────────────────────────────┼──────────┘
                                                              │
                      ┌───────────────────────────────────────┼────────┐
                      │                                       │        │
                      ▼                                       ▼        ▼
               ┌──────────────┐                   ┌────────────┐ ┌──────┐
               │ File locali  │                   │  Remote    │ │ SIEM │
               │ /var/log/*   │                   │  syslog    │ │ ELK  │
               └──────────────┘                   │  server    │ │ Loki │
                                                  └────────────┘ └──────┘
```

### Kernel ring buffer

Il kernel Linux mantiene un buffer circolare in memoria (ring buffer) per i messaggi di log generati tramite `printk()`. Questo buffer:

- Ha dimensione fissa configurabile via `log_buf_len=` nel boot (default: 128 KB - 2 MB a seconda dell'architettura)
- È accessibile via `/dev/kmsg` (lettura continua) o `dmesg` (snapshot)
- Contiene messaggi dal boot fino al presente; quando pieno, sovrascrive i più vecchi
- È disponibile anche quando nessun demone di logging è attivo (utile in fase di boot)
- I messaggi hanno timestamp monotonic (nanosecondi dal boot)

```bash
# Dimensione del ring buffer
dmesg | wc -l

# Leggere il ring buffer con timestamp leggibili
dmesg -T

# Leggere con livelli di priorità colorati
dmesg -H

# Solo messaggi di un certo livello
dmesg --level=err,warn

# Seguire nuovi messaggi (come tail -f)
dmesg -w

# Parametro kernel per aumentare il buffer
# In /etc/default/grub, GRUB_CMDLINE_LINUX:
# log_buf_len=4M
```

### systemd-journald nel flusso

`systemd-journald` è il primo aggregatore nella pipeline moderna. Raccoglie messaggi da:

1. **Kernel**: legge `/dev/kmsg` continuamente
2. **Applicazioni native systemd**: tramite `sd_journal_send()` o invio a socket `AF_UNIX`
3. **Syslog tradizionale**: ascolta su `/dev/log` (socket `/run/systemd/journal/dev-log`)
4. **stdout/stderr delle unit systemd**: catturati automaticamente
5. **Audit subsystem**: messaggi dal kernel audit framework

journald scrive in formato binario strutturato con indicizzazione, consentendo query veloci su campi arbitrari. Può opzionalmente inoltrare messaggi a rsyslog/syslog-ng tramite il socket `/run/systemd/journal/syslog`.

### rsyslog/syslog-ng nel flusso

I demoni syslog tradizionali operano a valle di journald (o in parallelo, ricevendo messaggi dallo stesso socket `/dev/log`). Il loro ruolo nella pipeline moderna:

1. **Ricezione**: messaggi locali da journald o direttamente da `/dev/log`, messaggi remoti via UDP/TCP/RELP
2. **Parsing**: estrazione di campi strutturati dal messaggio
3. **Filtraggio**: decisione su dove instradare ogni messaggio basata su facility, severity, hostname, programname, contenuto
4. **Trasformazione**: applicazione di template per formattare l'output
5. **Output**: scrittura su file locali, inoltro a server remoti, invio a database, code di messaggi

### Storage e SIEM

Lo stadio finale della pipeline è lo storage persistente e l'analisi:

- **File locali**: `/var/log/*` — il metodo tradizionale, gestito da logrotate
- **Journal binario**: `/var/log/journal/` — storage nativo di journald
- **Server syslog remoto**: aggregazione di log da più host
- **Elasticsearch/OpenSearch**: indicizzazione full-text, ricerca, aggregazione
- **Loki**: storage ottimizzato per log con label-based indexing
- **SIEM** (Splunk, QRadar, Wazuh): correlazione eventi, alerting, compliance

```
File di log principali per distribuzione:

Debian/Ubuntu:                      RHEL/CentOS/Fedora:
/var/log/syslog                     /var/log/messages
/var/log/auth.log                   /var/log/secure
/var/log/kern.log                   /var/log/kern.log (se configurato)
/var/log/dpkg.log                   /var/log/yum.log o /var/log/dnf.log
/var/log/apt/                       /var/log/audit/audit.log

Comuni a tutte:
/var/log/dmesg                      Boot messages (file, non live)
/var/log/cron                       Esecuzioni cron
/var/log/mail.log                   Mail server
/var/log/nginx/                     Nginx access/error
/var/log/apache2/ o /var/log/httpd/ Apache access/error
/var/log/mysql/ o /var/log/mariadb/ Database
/var/log/audit/audit.log            Audit framework (auditd)
/var/log/faillog                    Login falliti (pam_tally)
/var/log/wtmp                       Login riusciti (binario, leggere con last)
/var/log/btmp                       Login falliti (binario, leggere con lastb)
/var/log/lastlog                    Ultimo login per utente (lastlog)
```

---

## Facility e Severity: Riferimento RFC 5424

RFC 5424 (successore di RFC 3164) definisce il protocollo syslog e le sue classificazioni. Ogni messaggio syslog ha due dimensioni: **facility** (sorgente/categoria) e **severity** (gravità).

### Tabella facility completa

| Codice | Parola chiave | Descrizione |
|--------|---------------|-------------|
| 0 | kern | Messaggi del kernel |
| 1 | user | Messaggi a livello utente |
| 2 | mail | Sistema di posta |
| 3 | daemon | Demoni di sistema (senza facility specifica) |
| 4 | auth | Sicurezza/autorizzazione (login, su) |
| 5 | syslog | Messaggi generati internamente da syslogd |
| 6 | lpr | Sottosistema di stampa |
| 7 | news | Sottosistema network news (NNTP) |
| 8 | uucp | Sottosistema UUCP |
| 9 | cron | Demone cron e at |
| 10 | authpriv | Sicurezza/autorizzazione (messaggi privati) |
| 11 | ftp | Demone FTP |
| 12 | ntp | Sottosistema NTP (in alcune implementazioni) |
| 13 | security | Log audit (in alcune implementazioni) |
| 14 | console | Log console (in alcune implementazioni) |
| 15 | solaris-cron | Clock daemon (Solaris, non comune su Linux) |
| 16 | local0 | Uso locale 0 — personalizzabile |
| 17 | local1 | Uso locale 1 — personalizzabile |
| 18 | local2 | Uso locale 2 — personalizzabile |
| 19 | local3 | Uso locale 3 — personalizzabile |
| 20 | local4 | Uso locale 4 — personalizzabile |
| 21 | local5 | Uso locale 5 — personalizzabile |
| 22 | local6 | Uso locale 6 — personalizzabile |
| 23 | local7 | Uso locale 7 — personalizzabile |

Le facility `local0`–`local7` sono le più importanti per applicazioni custom. Convenzioni comuni:

- `local0` → applicazione web principale
- `local1` → database applicativo
- `local2` → servizi di autenticazione custom
- `local3` → load balancer/reverse proxy
- `local4` → applicazione di monitoraggio
- `local5` → servizi batch/scheduler
- `local6` → sicurezza/IDS
- `local7` → debug (boot loader su alcune distribuzioni)

### Tabella severity completa

| Codice | Parola chiave | Descrizione | Quando usare |
|--------|---------------|-------------|--------------|
| 0 | emerg | Sistema inutilizzabile | Kernel panic, filesystem root in read-only, OOM killer attivo |
| 1 | alert | Azione immediata necessaria | Database corrotto, perdita di connettività di rete critica |
| 2 | crit | Condizioni critiche | Hardware failure, disco in errore, servizio critico down |
| 3 | err | Errori | Operazione fallita, timeout connessione, errore applicativo |
| 4 | warning | Avvertimenti | Disco al 85%, certificato in scadenza, deprecation |
| 5 | notice | Condizioni normali significative | Servizio avviato/fermato, cambio configurazione, login root |
| 6 | info | Informativo | Operazioni normali, richieste gestite, connessioni accettate |
| 7 | debug | Debug | Dettagli interni, variabili di stato, flow di esecuzione |

### Mappatura pratica facility→file

Configurazione tipica rsyslog che mappa facility a file:

```bash
# /etc/rsyslog.d/50-default.conf (Debian/Ubuntu)

auth,authpriv.*                 /var/log/auth.log
*.*;auth,authpriv.none          -/var/log/syslog
kern.*                          -/var/log/kern.log
mail.*                          -/var/log/mail.log
mail.err                        /var/log/mail.err
cron.*                          /var/log/cron.log
daemon.*                        -/var/log/daemon.log
user.*                          -/var/log/user.log
local0.*                        /var/log/webapp.log
local6.*                        /var/log/security-ids.log

# Il trattino (-) prima del path disabilita fsync dopo ogni write
# (migliora performance, lieve rischio di perdita in caso di crash)
```

### Calcolo del PRI value

Ogni messaggio syslog contiene un valore PRI (priority) calcolato come:

```
PRI = facility × 8 + severity

Esempio: auth.err → 4 × 8 + 3 = 35
Esempio: kern.emerg → 0 × 8 + 0 = 0
Esempio: local7.debug → 23 × 8 + 7 = 191

Nel messaggio syslog appare come: <35> o <0> o <191>
```

Questo valore è usato internamente nel protocollo syslog (RFC 5424 header) e nei filtri avanzati. La comprensione del PRI è utile per il debug di messaggi raw catturati con `tcpdump` o analizzati con parser personalizzati.

---

## Journald: Deep Dive

### Configurazione journald

Il file di configurazione principale è `/etc/systemd/journald.conf`. Ogni opzione può anche essere specificata in file drop-in in `/etc/systemd/journald.conf.d/*.conf`.

```ini
# /etc/systemd/journald.conf
[Journal]
# --- Storage ---
Storage=persistent
# auto       = persistente se /var/log/journal/ esiste, altrimenti volatile
# persistent = crea /var/log/journal/ e scrive lì
# volatile   = solo /run/log/journal/ (perso al reboot)
# none       = scarta tutto (solo forward)

# --- Compressione ---
Compress=yes
# Comprime oggetti > 512 byte con XZ/LZ4/ZSTD

# --- Sigillatura ---
Seal=yes
# Forward Secure Sealing: protegge dall'alterazione retroattiva dei log
# Richiede setup chiavi con: journalctl --setup-keys

# --- Rate Limiting ---
RateLimitIntervalSec=30s
RateLimitBurst=10000
# Max 10000 messaggi ogni 30 secondi per servizio
# Oltre: messaggio "Suppressed N messages from <unit>"

# --- Dimensionamento (persistente) ---
SystemMaxUse=4G
# Spazio massimo totale su disco per il journal
SystemKeepFree=1G
# Spazio minimo da mantenere libero sulla partizione
SystemMaxFileSize=128M
# Dimensione massima di un singolo file journal
SystemMaxFiles=100
# Numero massimo di file journal archiviati

# --- Dimensionamento (volatile /run) ---
RuntimeMaxUse=256M
RuntimeKeepFree=64M
RuntimeMaxFileSize=32M
RuntimeMaxFiles=100

# --- Forward ---
ForwardToSyslog=yes
# Inoltra messaggi a syslog (/run/systemd/journal/syslog)
ForwardToKMsg=no
# Inoltra a /dev/kmsg (ring buffer kernel)
ForwardToConsole=no
# Inoltra a console di sistema
ForwardToWall=yes
# Inoltra emerg a tutti i terminali (wall)

# --- Livello massimo per destinazione ---
MaxLevelStore=debug
MaxLevelSyslog=debug
MaxLevelKMsg=notice
MaxLevelConsole=info
MaxLevelWall=emerg

# --- Split ---
SplitMode=uid
# uid    = journal separato per ogni utente (default)
# none   = un unico journal per tutti
```

```bash
# Applicare le modifiche
sudo systemctl restart systemd-journald

# Verificare la configurazione attiva
systemd-analyze cat-config systemd/journald.conf
```

### Storage persistente

Di default su molte distribuzioni, journald usa `Storage=auto`, che scrive in modo persistente solo se la directory `/var/log/journal/` esiste. Per garantire la persistenza:

```bash
# Creare la directory per lo storage persistente
sudo mkdir -p /var/log/journal

# Impostare i permessi corretti
sudo systemd-tmpfiles --create --prefix /var/log/journal

# Configurare storage persistente
sudo sed -i 's/^#Storage=auto/Storage=persistent/' /etc/systemd/journald.conf

# Riavviare journald
sudo systemctl restart systemd-journald

# Verificare che i file journal siano stati creati
ls -la /var/log/journal/

# Il machine-id determina la sottodirectory
cat /etc/machine-id
# Output: a1b2c3d4e5f6...
# Journal in: /var/log/journal/a1b2c3d4e5f6.../
```

Struttura dei file journal:

```
/var/log/journal/<machine-id>/
├── system.journal          # Journal corrente del sistema
├── system@<id>.journal     # Journal archiviati (ruotati)
├── user-1000.journal       # Journal utente UID 1000
└── user-1000@<id>.journal  # Journal utente archiviati
```

### Dimensionamento e rotazione journal

journald gestisce la rotazione autonomamente, senza logrotate. I parametri chiave:

```bash
# Verificare l'uso corrente del disco
journalctl --disk-usage
# Output: Archived and active journals take up 2.3G in the file system.

# Pulizia manuale — per dimensione
sudo journalctl --vacuum-size=1G
# Rimuove journal archiviati fino a rientrare in 1 GB

# Pulizia manuale — per tempo
sudo journalctl --vacuum-time=30d
# Rimuove journal archiviati più vecchi di 30 giorni

# Pulizia manuale — per numero di file
sudo journalctl --vacuum-files=10
# Mantiene solo gli ultimi 10 file journal archiviati

# Verificare integrità del journal
journalctl --verify
# Output: PASS per ogni file valido, FAIL per corrotti

# Rotazione forzata (chiude il file corrente e ne apre uno nuovo)
sudo journalctl --rotate
```

Raccomandazioni di dimensionamento per ambiente:

```
Desktop/laptop:     SystemMaxUse=1G,  SystemKeepFree=2G
Server singolo:     SystemMaxUse=4G,  SystemKeepFree=2G
Server applicativo: SystemMaxUse=8G,  SystemKeepFree=4G
Log server:         SystemMaxUse=50G, SystemKeepFree=10G

Nota: il journal non deve sostituire il logging centralizzato.
Lo storage locale è per debug e come buffer/fallback.
```

### journalctl: filtri avanzati

### Filtri per unit

```bash
# Log di una singola unit
journalctl -u nginx.service

# Log di più unit (OR logico)
journalctl -u nginx.service -u php-fpm.service

# Log di uno slice (gruppo di unit)
journalctl -u system.slice

# Log di un target
journalctl -u multi-user.target

# Log di un timer e del servizio associato
journalctl -u certbot.timer -u certbot.service

# Log del socket e del servizio attivato
journalctl -u sshd.socket -u sshd.service

# Filtrare per pattern nel nome unit (con glob)
journalctl -u 'docker-*'
journalctl -u 'nginx*'

# User unit (servizi utente)
journalctl --user -u pipewire.service
```

### Filtri per priorità

```bash
# Solo messaggi di una certa priorità e superiori
journalctl -p err                  # err + crit + alert + emerg
journalctl -p warning              # warning + err + crit + alert + emerg

# Range di priorità
journalctl -p warning..err         # Solo warning e err

# Priorità specifica per singola unit
journalctl -u nginx.service -p err

# Contare messaggi per priorità
journalctl -p emerg --no-pager | wc -l
journalctl -p crit --no-pager | wc -l

# Priorità con output compatto
journalctl -p err -o short-precise --no-pager
```

### Filtri per tempo

```bash
# Da una data specifica
journalctl --since "2026-05-20"
journalctl --since "2026-05-20 14:30:00"

# Fino a una data specifica
journalctl --until "2026-05-21 18:00:00"

# Range temporale
journalctl --since "2026-05-20 08:00" --until "2026-05-20 18:00"

# Espressioni relative
journalctl --since "1 hour ago"
journalctl --since "30 min ago"
journalctl --since "2 days ago"
journalctl --since yesterday
journalctl --since today
journalctl --since "2026-05-20" --until "1 hour ago"

# Combinare con unit e priorità
journalctl -u sshd --since "1 week ago" -p warning
```

### Filtri per boot

```bash
# Boot corrente
journalctl -b
journalctl -b 0

# Boot precedente
journalctl -b -1

# Due boot fa
journalctl -b -2

# Elencare tutti i boot registrati
journalctl --list-boots
# Output:
# -3 abc123... Mon 2026-05-17 09:00:00 CEST — Mon 2026-05-18 23:00:00 CEST
# -2 def456... Tue 2026-05-19 09:00:00 CEST — Wed 2026-05-20 08:00:00 CEST
# -1 ghi789... Wed 2026-05-20 09:00:00 CEST — Thu 2026-05-21 07:00:00 CEST
#  0 jkl012... Thu 2026-05-21 08:00:00 CEST — present

# Boot specifico per ID
journalctl -b abc123

# Errori nel boot precedente (debug post-crash)
journalctl -b -1 -p err

# Solo messaggi kernel del boot precedente
journalctl -b -1 -k
```

### Filtri per PID, UID, GID

```bash
# Per PID
journalctl _PID=1234

# Per UID
journalctl _UID=1000

# Per GID
journalctl _GID=33                 # www-data

# Per executable path
journalctl _EXE=/usr/sbin/nginx

# Per command name
journalctl _COMM=nginx

# Per transport (come il messaggio è arrivato a journald)
journalctl _TRANSPORT=kernel       # Solo messaggi kernel
journalctl _TRANSPORT=syslog       # Solo messaggi via syslog
journalctl _TRANSPORT=journal      # Solo messaggi via journal API
journalctl _TRANSPORT=stdout       # Solo stdout/stderr di unit
journalctl _TRANSPORT=audit        # Solo messaggi audit

# Combinare campi (AND logico tra campi diversi)
journalctl _UID=0 _COMM=sudo

# OR logico: ripetere lo stesso campo
journalctl _COMM=sudo + _COMM=su
```

### Filtri combinati e output

```bash
# Formato output
journalctl -o short                # Default: timestamp hostname unit message
journalctl -o short-precise        # Timestamp con microsecondi
journalctl -o short-iso            # Timestamp ISO 8601
journalctl -o short-iso-precise    # ISO 8601 con microsecondi
journalctl -o verbose              # Tutti i campi del messaggio
journalctl -o json                 # JSON (una riga per messaggio)
journalctl -o json-pretty          # JSON formattato
journalctl -o cat                  # Solo il testo del messaggio
journalctl -o export               # Formato binario per import/export

# Follow in tempo reale
journalctl -f                      # Come tail -f
journalctl -f -u nginx             # Follow di una unit
journalctl -f -p err               # Follow solo errori

# Ultime N righe
journalctl -n 50                   # Ultime 50 righe
journalctl -n 50 -u nginx         # Ultime 50 di nginx

# Reverse (più recenti prima)
journalctl -r

# Senza pager (per piping)
journalctl --no-pager

# Nessun hostname nell'output
journalctl --no-hostname

# Export completo per analisi esterna
journalctl -u nginx --since today -o json --no-pager > /tmp/nginx-today.json

# Contare messaggi per unit
journalctl -u nginx --since today --no-pager | wc -l

# Elencare tutti i campi disponibili
journalctl -o verbose -n 1

# Elencare valori unici di un campo
journalctl -F _COMM               # Tutti i command name
journalctl -F _SYSTEMD_UNIT       # Tutte le unit che hanno loggato
journalctl -F SYSLOG_IDENTIFIER   # Tutti i syslog identifier
```

### Campi metadata e cursori

Ogni entry nel journal ha campi strutturati accessibili con `-o verbose`:

```bash
journalctl -o verbose -n 1
# Output:
# Thu 2026-05-22 10:30:45.123456 CEST [s=abc...;i=1234;b=def...;m=999...]
#     _BOOT_ID=def456...
#     _MACHINE_ID=a1b2c3...
#     _HOSTNAME=web-server-01
#     PRIORITY=6
#     SYSLOG_FACILITY=3
#     SYSLOG_IDENTIFIER=nginx
#     _TRANSPORT=syslog
#     _PID=12345
#     _UID=33
#     _GID=33
#     _COMM=nginx
#     _EXE=/usr/sbin/nginx
#     _CMDLINE=nginx: worker process
#     _SYSTEMD_UNIT=nginx.service
#     _SYSTEMD_CGROUP=/system.slice/nginx.service
#     MESSAGE=GET /api/health HTTP/1.1 200

# Cursori: posizione univoca nel journal
journalctl -o export -n 1 | grep __CURSOR
# __CURSOR=s=abc...;i=1234;b=def...;m=999...

# Leggere a partire da un cursore (utile per polling incrementale)
journalctl --after-cursor="s=abc...;i=1234;b=def..."

# Filtrare per campo custom
journalctl MY_APP_REQUEST_ID=req-abc-123
```

### Journal remoto

`systemd-journal-remote` permette di inviare journal a un server centralizzato mantenendo il formato strutturato:

```bash
# --- Sul server ricevente ---
sudo apt install systemd-journal-remote   # Debian/Ubuntu
sudo dnf install systemd-journal-remote   # RHEL/Fedora

# Configurare /etc/systemd/journal-remote.conf
# [Remote]
# Seal=false
# SplitMode=host
# ServerKeyFile=/etc/ssl/private/journal-remote.key
# ServerCertificateFile=/etc/ssl/certs/journal-remote.crt
# TrustedCertificateFile=/etc/ssl/ca/journal-ca.crt

sudo systemctl enable --now systemd-journal-remote.socket
# Ascolta su porta 19532 (HTTPS) di default

# --- Sul client ---
sudo apt install systemd-journal-upload

# Configurare /etc/systemd/journal-upload.conf
# [Upload]
# URL=https://logserver.example.com:19532
# ServerKeyFile=/etc/ssl/private/journal-upload.key
# ServerCertificateFile=/etc/ssl/certs/journal-upload.crt
# TrustedCertificateFile=/etc/ssl/ca/journal-ca.crt

sudo systemctl enable --now systemd-journal-upload.service

# Verificare il flusso
journalctl -u systemd-journal-upload -f
```

---

## rsyslog: Deep Dive

### Architettura modulare rsyslog

rsyslog (rocket-fast system log) è costruito su un'architettura modulare:

```
                    ┌─────────────────────────────┐
                    │         rsyslog engine       │
                    │                              │
┌───────────┐      │  ┌─────────┐   ┌─────────┐  │      ┌───────────┐
│  Input     │─────▶│  │ Parser  │──▶│ Rules / │──│─────▶│  Output   │
│  Modules   │      │  │ Modules │   │ Filter  │  │      │  Modules  │
│  (im*)     │      │  │ (pm*)   │   │ Engine  │  │      │  (om*)    │
└───────────┘      │  └─────────┘   └─────────┘  │      └───────────┘
                    │                              │
                    │  ┌─────────┐   ┌─────────┐  │
                    │  │ Message │   │ String  │  │
                    │  │ Modif.  │   │ Gen.    │  │
                    │  │ (mm*)   │   │ (sm*)   │  │
                    │  └─────────┘   └─────────┘  │
                    └─────────────────────────────┘
```

Configurazione in RainerScript (sintassi moderna, raccomandata):

```bash
# /etc/rsyslog.conf — struttura base

# VARIABILI GLOBALI
global(
    workDirectory="/var/spool/rsyslog"
    maxMessageSize="64k"
    preserveFQDN="on"
)

# MODULI
module(load="imuxsock")    # Socket locale /dev/log
module(load="imklog")      # Messaggi kernel /proc/kmsg
module(load="immark"       # Messaggi marca temporale
       interval="600")     # Ogni 10 minuti

# INCLUDE DROP-IN
include(file="/etc/rsyslog.d/*.conf" mode="optional")
```

### Moduli di input

```bash
# --- imuxsock: socket locale Unix ---
module(load="imuxsock"
    SysSock.Use="on"
    SysSock.Name="/dev/log"
    SysSock.RateLimit.Interval="5"
    SysSock.RateLimit.Burst="200"
)

# --- imklog: messaggi kernel ---
module(load="imklog"
    PermitNonKernelFacility="on"
)

# --- imtcp: ricezione TCP (usare per log centralizzato) ---
module(load="imtcp"
    MaxSessions="500"
    StreamDriver.AuthMode="x509/name"
    StreamDriver.Mode="1"          # TLS
)
input(type="imtcp" port="514")
input(type="imtcp" port="10514" ruleset="remoteRuleset")

# --- imudp: ricezione UDP ---
module(load="imudp")
input(type="imudp" port="514")
input(type="imudp" port="514" address="192.168.1.10")  # Solo su una interfaccia

# --- imfile: monitorare file di testo (come tail -f) ---
module(load="imfile"
    PollingInterval="10"           # Secondi tra i poll
)
input(type="imfile"
    File="/var/log/nginx/access.log"
    Tag="nginx-access:"
    Severity="info"
    Facility="local6"
    readTimeout="2"
)
input(type="imfile"
    File="/var/log/myapp/*.log"    # Glob supportato
    Tag="myapp:"
    Severity="info"
    Facility="local0"
    addMetadata="on"
)

# --- imrelp: RELP (Reliable Event Logging Protocol) ---
module(load="imrelp")
input(type="imrelp" port="2514" tls="on"
    tls.caCert="/etc/rsyslog.d/certs/ca.pem"
    tls.myCert="/etc/rsyslog.d/certs/server-cert.pem"
    tls.myPrivKey="/etc/rsyslog.d/certs/server-key.pem"
    tls.authMode="name"
    tls.permittedPeer=["client1.example.com","client2.example.com"]
)

# --- imjournal: leggere direttamente dal journal systemd ---
module(load="imjournal"
    StateFile="imjournal.state"
    ratelimit.interval="600"
    ratelimit.burst="20000"
)

# --- immark: messaggi marca temporale ---
module(load="immark" interval="3600")  # Ogni ora
```

### Moduli di output

```bash
# --- omfile: scrittura su file ---
action(type="omfile"
    file="/var/log/messages"
    fileCreateMode="0640"
    fileOwner="syslog"
    fileGroup="adm"
    template="RSYSLOG_TraditionalFileFormat"
)

# --- omfwd: inoltro a server remoto ---
# TCP
action(type="omfwd"
    target="logserver.example.com"
    port="514"
    protocol="tcp"
    queue.type="LinkedList"
    queue.filename="fwdRule1"
    queue.maxdiskspace="1g"
    queue.saveonshutdown="on"
    action.resumeRetryCount="-1"     # Riprova indefinitamente
    action.resumeInterval="30"       # 30s tra i retry
)

# UDP
action(type="omfwd"
    target="logserver.example.com"
    port="514"
    protocol="udp"
)

# --- omrelp: inoltro RELP (affidabile, con ack) ---
module(load="omrelp")
action(type="omrelp"
    target="logserver.example.com"
    port="2514"
    tls="on"
    tls.caCert="/etc/rsyslog.d/certs/ca.pem"
    tls.myCert="/etc/rsyslog.d/certs/client-cert.pem"
    tls.myPrivKey="/etc/rsyslog.d/certs/client-key.pem"
)

# --- omelasticsearch: invio diretto a Elasticsearch ---
module(load="omelasticsearch")
action(type="omelasticsearch"
    server="es-node1.example.com"
    serverport="9200"
    searchIndex="syslog-index"
    dynSearchIndex="on"
    searchType="_doc"
    template="JsonTemplate"
    bulkmode="on"
    queue.type="LinkedList"
    queue.filename="elasticQueue"
    queue.maxdiskspace="2g"
    queue.saveonshutdown="on"
    action.resumeRetryCount="-1"
)

# --- omprog: invio a programma esterno via stdin ---
module(load="omprog")
action(type="omprog"
    binary="/usr/local/bin/log-processor.sh"
    template="RSYSLOG_TraditionalFileFormat"
)

# --- ommail: invio email su eventi critici ---
module(load="ommail")
action(type="ommail"
    server="smtp.example.com"
    port="587"
    mailfrom="alerts@example.com"
    mailto="admin@example.com"
    subject.template="MailSubject"
    body.enable="on"
)
```

### Template rsyslog

I template definiscono il formato di output dei messaggi. rsyslog supporta diversi tipi di template:

```bash
# --- Template di tipo string ---
template(name="TraditionalFormat" type="string"
    string="%timegenerated% %HOSTNAME% %syslogtag%%msg:::sp-if-no-1st-sp%%msg:::drop-last-lf%\n"
)

template(name="PreciseTimestamp" type="string"
    string="%timegenerated:::date-rfc3339% %HOSTNAME% %syslogtag% %msg%\n"
)

template(name="FilePerHost" type="string"
    string="/var/log/remote/%HOSTNAME%/%programname%.log"
)

# --- Template di tipo list (più flessibile) ---
template(name="DetailedFormat" type="list") {
    property(name="timegenerated" dateFormat="rfc3339")
    constant(value=" ")
    property(name="hostname")
    constant(value=" ")
    property(name="syslogtag")
    constant(value=" ")
    property(name="syslogseverity-text")
    constant(value=" ")
    property(name="msg" spifno1teleadingsp="on" droplastlf="on")
    constant(value="\n")
}

# --- Template JSON ---
template(name="JsonFormat" type="list") {
    constant(value="{")
    constant(value="\"@timestamp\":\"")
    property(name="timegenerated" dateFormat="rfc3339")
    constant(value="\",\"host\":\"")
    property(name="hostname")
    constant(value="\",\"severity\":\"")
    property(name="syslogseverity-text")
    constant(value="\",\"facility\":\"")
    property(name="syslogfacility-text")
    constant(value="\",\"program\":\"")
    property(name="programname")
    constant(value="\",\"message\":\"")
    property(name="msg" format="jsonf")
    constant(value="\"}\n")
}

# --- Template di tipo subtree (per output strutturato) ---
template(name="ElasticTemplate" type="subtree" subtree="$!")
# Usa la struttura dell'albero delle proprietà

# --- Template di tipo plugin ---
template(name="TplByPlugin" type="plugin" plugin="mmjsonparse")

# Applicare un template a un'azione
auth,authpriv.*     action(type="omfile"
                        file="/var/log/auth.log"
                        template="DetailedFormat")
```

Proprietà disponibili nei template:

```
msg             – Testo del messaggio
rawmsg          – Messaggio raw non processato
hostname        – Hostname sorgente
source          – Alias di hostname
fromhost        – Hostname da cui è stato ricevuto (per remoto)
fromhost-ip     – IP da cui è stato ricevuto
syslogtag       – Tag syslog (es. "nginx[1234]:")
programname     – Nome programma (senza PID)
procid          – Process ID
syslogfacility  – Facility numerica
syslogfacility-text – Facility testuale (kern, user, ...)
syslogseverity  – Severity numerica
syslogseverity-text – Severity testuale (err, warning, ...)
pri             – PRI value (facility*8+severity)
pri-text        – PRI testuale (facility.severity)
timegenerated   – Timestamp generazione messaggio
timereported    – Timestamp riportato dal messaggio
$now            – Data corrente YYYY-MM-DD
$year, $month, $day, $hour, $minute
inputname       – Nome dell'input che ha ricevuto il messaggio
```

### Rulesets

I ruleset permettono di applicare regole diverse a input diversi:

```bash
# Definire un ruleset
ruleset(name="remoteRuleset") {
    # Template per i log remoti
    template(name="RemoteFilePath" type="string"
        string="/var/log/remote/%HOSTNAME%/%programname%.log"
    )

    # Scrivere su file per host
    action(type="omfile"
        dynaFile="RemoteFilePath"
        fileCreateMode="0640"
        dirCreateMode="0755"
        dirOwner="syslog"
        dirGroup="adm"
    )

    # Inoltrare anche a Elasticsearch
    action(type="omelasticsearch"
        server="es.example.com"
        searchIndex="remote-syslog"
        template="JsonFormat"
        bulkmode="on"
    )
}

# Associare input a ruleset
input(type="imtcp" port="10514" ruleset="remoteRuleset")
input(type="imudp" port="10514" ruleset="remoteRuleset")

# Ruleset per log applicativi
ruleset(name="appLogs") {
    if $programname == "webapp" then {
        action(type="omfile" file="/var/log/webapp/app.log")
        if $syslogseverity <= 3 then {
            action(type="omfwd"
                target="alerts.example.com"
                port="514"
                protocol="tcp"
            )
        }
    }
}
```

### Filtri property-based

```bash
# --- Filtro per programname ---
if $programname == 'nginx' then {
    action(type="omfile" file="/var/log/nginx/syslog-nginx.log")
    stop
}

# --- Filtro per hostname (server di log) ---
if $hostname == 'web-server-01' then {
    action(type="omfile" file="/var/log/hosts/web-server-01.log")
}

# --- Filtro per contenuto messaggio ---
if $msg contains 'ERROR' then {
    action(type="omfile" file="/var/log/errors-all.log")
}

# --- Filtro regex ---
if re_match($msg, 'Failed password for .* from [0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+') then {
    action(type="omfile" file="/var/log/ssh-brute-force.log")
}

# --- Filtro per severity ---
if $syslogseverity <= 3 then {
    # err, crit, alert, emerg
    action(type="omfile" file="/var/log/critical-errors.log")
}

# --- Filtro per facility ---
if $syslogfacility-text == 'auth' then {
    action(type="omfile" file="/var/log/auth-verbose.log")
}

# --- Filtro combinato (AND) ---
if $programname == 'sshd' and $msg contains 'Failed' then {
    action(type="omfile" file="/var/log/ssh-failures.log")
}

# --- Filtro combinato (OR) ---
if $programname == 'sshd' or $programname == 'sudo' then {
    action(type="omfile" file="/var/log/access-control.log")
}

# --- Filtro per IP sorgente (log remoto) ---
if $fromhost-ip == '192.168.1.100' then {
    action(type="omfile" file="/var/log/remote/server100.log")
    stop
}

# --- Filtro negato ---
if not ($programname == 'systemd') then {
    action(type="omfile" file="/var/log/non-systemd.log")
}
```

### Nomi file dinamici

```bash
# File per hostname
template(name="DynPerHost" type="string"
    string="/var/log/remote/%HOSTNAME%/messages.log"
)
*.* action(type="omfile" dynaFile="DynPerHost"
    dirCreateMode="0755" fileCreateMode="0640")

# File per hostname e programma
template(name="DynPerHostProgram" type="string"
    string="/var/log/remote/%HOSTNAME%/%programname%.log"
)
*.* action(type="omfile" dynaFile="DynPerHostProgram")

# File per data
template(name="DynByDate" type="string"
    string="/var/log/archive/%$year%/%$month%/%$day%/messages.log"
)
*.* action(type="omfile" dynaFile="DynByDate")

# File per facility
template(name="DynByFacility" type="string"
    string="/var/log/by-facility/%syslogfacility-text%.log"
)
*.* action(type="omfile" dynaFile="DynByFacility")

# Combinazione: host + data + programma
template(name="DynFull" type="string"
    string="/var/log/remote/%HOSTNAME%/%$year%-%$month%-%$day%/%programname%.log"
)
```

### Queue rsyslog

rsyslog usa code (queue) per gestire il flusso dei messaggi, specialmente con destinazioni remote:

```bash
# --- Main queue (globale) ---
main_queue(
    queue.type="LinkedList"        # FixedArray, LinkedList, Direct, Disk
    queue.filename="mainQueue"     # Nome base per file su disco
    queue.maxdiskspace="2g"        # Spazio disco massimo
    queue.saveonshutdown="on"      # Salva coda allo shutdown
    queue.size="100000"            # Elementi massimi in memoria
    queue.dequeuebatchsize="1000"  # Batch di dequeue
    queue.timeoutenqueue="0"       # 0 = non bloccare se piena, scarta
    queue.highwatermark="80000"    # Inizia a scrivere su disco
    queue.lowwatermark="20000"     # Torna in memoria
)

# --- Action queue (per azione specifica) ---
action(type="omfwd"
    target="logserver.example.com"
    port="514"
    protocol="tcp"
    queue.type="LinkedList"
    queue.filename="fwdQueue"
    queue.maxdiskspace="1g"
    queue.saveonshutdown="on"
    queue.size="50000"
    queue.dequeuebatchsize="500"
    action.resumeRetryCount="-1"   # -1 = riprova per sempre
    action.resumeInterval="30"
)

# --- Disk-assisted queue (ibrida memoria+disco) ---
# Usa memoria normalmente, spilla su disco sotto pressione
action(type="omfwd"
    target="backup-log.example.com"
    port="514"
    protocol="tcp"
    queue.type="LinkedList"
    queue.filename="diskAssisted"
    queue.maxdiskspace="5g"
    queue.saveonshutdown="on"
    queue.highwatermark="50000"
    queue.lowwatermark="10000"
)
```

### TLS in rsyslog

```bash
# --- Configurazione TLS (server) ---
global(
    defaultNetstreamDriverCAFile="/etc/rsyslog.d/certs/ca.pem"
    defaultNetstreamDriverCertFile="/etc/rsyslog.d/certs/server-cert.pem"
    defaultNetstreamDriverKeyFile="/etc/rsyslog.d/certs/server-key.pem"
    defaultNetstreamDriver="gtls"  # oppure "ossl" per OpenSSL
)

module(load="imtcp"
    StreamDriver.Name="gtls"
    StreamDriver.Mode="1"          # TLS obbligatorio
    StreamDriver.AuthMode="x509/name"
    PermittedPeer=["client1.example.com","client2.example.com"]
)
input(type="imtcp" port="6514")    # Porta standard syslog TLS

# --- Configurazione TLS (client) ---
global(
    defaultNetstreamDriverCAFile="/etc/rsyslog.d/certs/ca.pem"
    defaultNetstreamDriverCertFile="/etc/rsyslog.d/certs/client-cert.pem"
    defaultNetstreamDriverKeyFile="/etc/rsyslog.d/certs/client-key.pem"
    defaultNetstreamDriver="gtls"
)

action(type="omfwd"
    target="logserver.example.com"
    port="6514"
    protocol="tcp"
    StreamDriver="gtls"
    StreamDriverMode="1"
    StreamDriverAuthMode="x509/name"
    StreamDriverPermittedPeers="logserver.example.com"
    queue.type="LinkedList"
    queue.filename="tlsFwd"
    queue.maxdiskspace="1g"
    queue.saveonshutdown="on"
    action.resumeRetryCount="-1"
)
```

### File drop-in rsyslog

```bash
# /etc/rsyslog.d/10-modules.conf — moduli aggiuntivi
module(load="imfile")
module(load="mmjsonparse")         # Parser JSON

# /etc/rsyslog.d/20-templates.conf — template custom
template(name="AppJsonLog" type="list") {
    constant(value="{")
    constant(value="\"timestamp\":\"")
    property(name="timegenerated" dateFormat="rfc3339")
    constant(value="\",\"host\":\"")
    property(name="hostname")
    constant(value="\",\"app\":\"")
    property(name="programname")
    constant(value="\",\"severity\":\"")
    property(name="syslogseverity-text")
    constant(value="\",\"message\":\"")
    property(name="msg" format="jsonf")
    constant(value="\"}\n")
}

# /etc/rsyslog.d/50-custom-apps.conf — regole applicative
# Log applicazione web
if $programname == 'webapp' then {
    action(type="omfile"
        file="/var/log/webapp/app.log"
        template="AppJsonLog"
    )
    stop
}

# Log microservizi
if $programname startswith 'svc-' then {
    action(type="omfile"
        dynaFile="DynPerHostProgram"
    )
    stop
}

# /etc/rsyslog.d/90-remote.conf — forwarding remoto
*.* action(type="omfwd"
    target="central-log.example.com"
    port="6514"
    protocol="tcp"
    StreamDriver="gtls"
    StreamDriverMode="1"
    StreamDriverAuthMode="x509/name"
    queue.type="LinkedList"
    queue.filename="remoteFwd"
    queue.maxdiskspace="2g"
    queue.saveonshutdown="on"
    action.resumeRetryCount="-1"
)
```

```bash
# Verificare configurazione
sudo rsyslogd -N1                  # Syntax check
sudo rsyslogd -N1 -f /etc/rsyslog.conf  # Check specifico

# Riavviare
sudo systemctl restart rsyslog

# Test
logger -p local0.err "Test errore webapp"
logger -t myapp -p user.notice "Messaggio di test"
logger -p auth.warning "Test warning autenticazione"
```

---

## syslog-ng: Configurazione e Confronto

syslog-ng (syslog next-generation) è un'alternativa a rsyslog, particolarmente popolare in ambienti enterprise per la sua sintassi di configurazione dichiarativa e le capacità avanzate di parsing.

### Sintassi di configurazione syslog-ng

La configurazione di syslog-ng si basa su quattro concetti fondamentali:
- **source**: da dove arrivano i messaggi
- **destination**: dove vanno i messaggi
- **filter**: quali messaggi selezionare
- **log**: collegamento source → filter → destination

```bash
# /etc/syslog-ng/syslog-ng.conf

@version: 4.6
@include "scl.conf"

# --- Opzioni globali ---
options {
    chain_hostnames(off);
    create_dirs(yes);
    dir_perm(0755);
    dns_cache(yes);
    flush_lines(0);
    group("adm");
    keep_hostname(yes);
    log_fifo_size(10000);
    log_msg_size(65536);
    perm(0640);
    stats_freq(3600);
    time_reopen(10);
    ts_format(iso);
    use_dns(persist_only);
    use_fqdn(yes);
};
```

### Source syslog-ng

```bash
# Sorgente locale (socket + kernel)
source s_local {
    system();       # Rileva automaticamente OS (equivale a internal + socket)
    internal();     # Messaggi interni di syslog-ng
};

# Sorgente di rete
source s_network_tcp {
    tcp(
        ip("0.0.0.0")
        port(514)
        max-connections(100)
        log-iw-size(10000)
    );
};

source s_network_udp {
    udp(
        ip("0.0.0.0")
        port(514)
    );
};

# Sorgente TLS
source s_network_tls {
    tcp(
        ip("0.0.0.0")
        port(6514)
        tls(
            key-file("/etc/syslog-ng/certs/server-key.pem")
            cert-file("/etc/syslog-ng/certs/server-cert.pem")
            ca-dir("/etc/syslog-ng/certs/ca.d/")
            peer-verify(required-trusted)
        )
    );
};

# Sorgente file
source s_nginx {
    file(
        "/var/log/nginx/access.log"
        follow-freq(1)
        flags(no-parse)
    );
};

# Sorgente journal (systemd)
source s_journal {
    systemd-journal(
        prefix(".journald.")
        max-field-size(65536)
    );
};
```

### Destination syslog-ng

```bash
# File locale
destination d_messages {
    file("/var/log/messages"
        template("${ISODATE} ${HOST} ${MSGHDR}${MSG}\n")
        frac_digits(3)
    );
};

destination d_auth {
    file("/var/log/auth.log"
        owner("root")
        group("adm")
        perm(0640)
    );
};

# File per host (log centralizzato)
destination d_remote_hosts {
    file("/var/log/remote/${HOST}/${PROGRAM}.log"
        create_dirs(yes)
        dir_perm(0755)
        perm(0640)
    );
};

# Server remoto TCP
destination d_remote_tcp {
    tcp(
        "logserver.example.com"
        port(514)
        log-fifo-size(10000)
        disk-buffer(
            mem-buf-size(10485760)
            disk-buf-size(2147483648)
            reliable(yes)
            dir("/var/spool/syslog-ng/")
        )
    );
};

# Elasticsearch
destination d_elasticsearch {
    elasticsearch-http(
        url("https://es.example.com:9200/_bulk")
        index("syslog-${YEAR}.${MONTH}.${DAY}")
        type("")
        template("$(format-json --scope rfc5424 --scope nv-pairs)")
        disk-buffer(
            mem-buf-size(10485760)
            disk-buf-size(1073741824)
            reliable(yes)
        )
    );
};

# Programma esterno
destination d_script {
    program("/usr/local/bin/process-log.sh"
        template("${ISODATE} ${HOST} ${MSG}\n")
    );
};
```

### Filter syslog-ng

```bash
# Per facility
filter f_kern { facility(kern); };
filter f_auth { facility(auth, authpriv); };
filter f_mail { facility(mail); };
filter f_cron { facility(cron); };

# Per severity
filter f_err { level(err..emerg); };
filter f_warning { level(warning..emerg); };
filter f_info { level(info); };
filter f_debug { level(debug); };
filter f_notice { level(notice); };

# Per programma
filter f_nginx { program("nginx"); };
filter f_sshd { program("sshd"); };

# Per contenuto messaggio
filter f_failed_login { match("Failed password" value("MESSAGE")); };
filter f_oom { match("Out of memory" value("MESSAGE")); };

# Per host
filter f_webservers { host("web-.*"); };  # Regex
filter f_specific_host { host("web-server-01"); };

# Filtri combinati
filter f_ssh_brute {
    program("sshd") and match("Failed password" value("MESSAGE"));
};

filter f_critical_not_kernel {
    level(crit..emerg) and not facility(kern);
};

filter f_local_apps {
    facility(local0..local7);
};

# Filtro negato
filter f_not_debug { not level(debug); };
```

### Log path syslog-ng

```bash
# Collegamento: source → filter → destination
log {
    source(s_local);
    filter(f_auth);
    destination(d_auth);
};

log {
    source(s_local);
    filter(f_kern);
    destination(d_messages);
};

# Log con flag
log {
    source(s_local);
    filter(f_err);
    destination(d_remote_tcp);
    flags(flow-control);         # Rallenta la sorgente se la coda è piena
};

# Log con più destinazioni
log {
    source(s_local);
    filter(f_ssh_brute);
    destination(d_auth);
    destination(d_remote_tcp);   # Invia anche al server remoto
};

# Log per messaggi remoti
log {
    source(s_network_tls);
    destination(d_remote_hosts);
    destination(d_elasticsearch);
};

# Log catch-all (tutto ciò che non è stato catturato)
log {
    source(s_local);
    filter(f_not_debug);
    destination(d_messages);
    flags(fallback);             # Solo se non matchato da altri log path
};
```

```bash
# Test configurazione
syslog-ng --syntax-only
syslog-ng -s

# Riavviare
sudo systemctl restart syslog-ng

# Statistiche
syslog-ng-ctl stats
```

### Confronto rsyslog vs syslog-ng

| Aspetto | rsyslog | syslog-ng |
|---------|---------|-----------|
| **Sintassi config** | RainerScript (procedurale) | Dichiarativa (source/filter/dest/log) |
| **Distribuzione default** | RHEL, Debian, Ubuntu, SUSE | Alcune enterprise, Arch Linux |
| **Performance** | Eccellente per volumi alti | Molto buona |
| **Moduli** | Vasto ecosistema (im*/om*) | Built-in + SCL |
| **Parser** | mmjsonparse, mmnormalize | Built-in (csv-parser, json-parser, kv-parser) |
| **TLS** | GnuTLS o OpenSSL | OpenSSL |
| **Reliable delivery** | RELP protocol | Disk buffer con reliability |
| **Elasticsearch output** | omelasticsearch | elasticsearch-http destination |
| **Template syntax** | String, list, subtree | Macro + template function |
| **Documentazione** | Ampia, community driven | Eccellente, One Identity |
| **Licenza** | GPL v3 | GPL v2 (OSE), Commerciale (PE) |
| **Disk-assisted queue** | Sì (action queue) | Sì (disk-buffer) |
| **Correlation** | Limitata (mmnormalize) | Built-in (grouping-by, correlazione pattern) |

Raccomandazione: usare rsyslog se è il default della distribuzione e soddisfa i requisiti. Considerare syslog-ng per parsing complesso e correlazione eventi nativi.

---

## Logrotate: Gestione Rotazione

logrotate previene che i file di log riempiano il disco. Ruota, comprime e rimuove i log vecchi. È tipicamente eseguito da un timer systemd o cron job giornaliero.

### Configurazione globale logrotate

```bash
# /etc/logrotate.conf — configurazione globale
# Questi valori sono i default; i file in logrotate.d possono sovrascriverli

weekly                              # Rotazione settimanale (default)
rotate 4                            # Mantieni 4 file ruotati
create                              # Crea nuovo file dopo rotazione
compress                            # Comprimi file ruotati (.gz)
dateext                             # Usa data nel nome (messages-20260522)
dateformat -%Y%m%d                  # Formato data
include /etc/logrotate.d            # Include file drop-in
```

### Tutte le direttive logrotate

```bash
# === FREQUENZA DI ROTAZIONE ===
daily                               # Ruota ogni giorno
weekly                              # Ruota ogni settimana
monthly                             # Ruota ogni mese
yearly                              # Ruota ogni anno

# === CRITERI DI DIMENSIONE ===
size 100M                           # Ruota solo se il file supera 100 MB
minsize 10M                         # Ruota solo se >= 10 MB (anche con daily/weekly)
maxsize 500M                        # Ruota immediatamente se > 500 MB
                                    # (anche se non è il momento programmato)

# === RETENTION ===
rotate 30                           # Mantieni 30 copie ruotate
maxage 365                          # Rimuovi file più vecchi di 365 giorni

# === CREAZIONE FILE ===
create 0640 syslog adm              # Crea nuovo file con permessi/owner/group
nocreate                            # Non creare nuovo file (l'app lo crea)
createolddir 0750 root adm          # Crea directory per file ruotati se non esiste

# === COMPRESSIONE ===
compress                            # Comprimi file ruotati
nocompress                          # Non comprimere
delaycompress                       # Comprimi alla rotazione successiva
                                    # (utile per app che tengono open il file vecchio)
compresscmd /usr/bin/zstd           # Comando di compressione (default: gzip)
compressext .zst                    # Estensione file compresso
compressoptions -19                 # Opzioni per il compressore
uncompresscmd /usr/bin/unzstd       # Comando di decompressione

# === NAMING ===
dateext                             # Usa data nel nome: file-20260522
nodateext                           # Usa numerazione: file.1, file.2
dateformat -%Y%m%d                  # Formato data
dateyesterday                       # Usa la data di ieri nel nome
extension .log                      # Mantieni estensione: file.20260522.log
                                    # invece di file.log.20260522

# === DIRECTORY ===
olddir /var/log/old                 # Sposta file ruotati in altra directory
noolddir                            # Mantieni nella stessa directory

# === COMPORTAMENTO ===
missingok                           # Non segnalare errore se il file non esiste
nomissingok                         # Errore se il file non esiste (default)
notifempty                          # Non ruotare se il file è vuoto
ifempty                             # Ruota anche se vuoto (default)
copytruncate                        # Copia e tronca il file originale
                                    # (per app che non rilasciano l'handle)
copy                                # Copia il file, non rinominare
sharedscripts                       # Esegui script una volta per tutti i file
                                    # nel blocco, non per ogni file
nosharedscripts                     # Esegui script per ogni file (default)
su root adm                         # Esegui logrotate come utente/gruppo specifico
                                    # (necessario se /var/log ha owner diverso)
tabooext + .bak .orig               # Estensioni da ignorare negli include

# === SCRIPT ===
prerotate                           # Eseguito PRIMA della rotazione
    /usr/bin/echo "Inizio rotazione"
endscript

postrotate                          # Eseguito DOPO la rotazione
    /usr/bin/systemctl reload nginx
endscript

firstaction                         # Eseguito PRIMA di qualsiasi operazione
    /usr/bin/echo "Inizio logrotate per il blocco"
endscript

lastaction                          # Eseguito DOPO tutte le operazioni del blocco
    /usr/bin/echo "Fine logrotate per il blocco"
endscript

# === MAIL (raramente usato) ===
mail admin@example.com              # Invia file ruotato via email
nomail                              # Non inviare (default)
mailfirst                           # Invia il file appena ruotato
maillast                            # Invia il file che sta per essere rimosso
```

### Esempi configurazione per servizio

```bash
# /etc/logrotate.d/nginx
/var/log/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
    endscript
}

# /etc/logrotate.d/postgresql
/var/log/postgresql/*.log {
    weekly
    rotate 10
    compress
    delaycompress
    missingok
    notifempty
    create 0640 postgres postgres
    su postgres postgres
    postrotate
        /usr/bin/pg_ctlcluster --skip-systemctl-redirect 16 main reload
    endscript
}

# /etc/logrotate.d/myapp — applicazione custom
/var/log/myapp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 myapp myapp
    maxsize 200M
    dateext
    dateformat -%Y%m%d-%s
    sharedscripts
    postrotate
        systemctl reload myapp 2>/dev/null || true
    endscript
}

# /etc/logrotate.d/docker-containers
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    maxsize 100M
}

# /etc/logrotate.d/audit
/var/log/audit/audit.log {
    weekly
    rotate 52
    compress
    delaycompress
    missingok
    notifempty
    create 0600 root root
    postrotate
        /sbin/service auditd rotate 2>/dev/null || true
    endscript
}

# /etc/logrotate.d/syslog
/var/log/syslog
/var/log/mail.log
/var/log/kern.log
/var/log/auth.log
/var/log/user.log
/var/log/cron.log
{
    rotate 7
    daily
    missingok
    notifempty
    delaycompress
    compress
    postrotate
        /usr/lib/rsyslog/rsyslog-rotate
    endscript
}
```

### Script personalizzati logrotate

```bash
# /etc/logrotate.d/custom-with-backup
/var/log/critical-app/*.log {
    daily
    rotate 90
    compress
    dateext
    missingok
    notifempty
    create 0640 app app

    prerotate
        # Verifica integrità prima di ruotare
        /usr/local/bin/verify-log-integrity.sh "$1" || exit 1
    endscript

    postrotate
        # Notifica l'applicazione
        systemctl reload critical-app || true

        # Copia di backup su storage remoto
        for f in /var/log/critical-app/*.gz; do
            if [ -f "$f" ]; then
                rsync -a "$f" backup-server:/backup/logs/critical-app/ 2>/dev/null || true
            fi
        done
    endscript

    lastaction
        # Verifica spazio disco dopo rotazione
        USAGE=$(df /var/log --output=pcent | tail -1 | tr -d ' %')
        if [ "$USAGE" -gt 85 ]; then
            echo "WARNING: /var/log al ${USAGE}%" | \
                mail -s "Disk space warning" admin@example.com
        fi
    endscript
}
```

### Compressione avanzata

```bash
# Compressione con zstd (più veloce di gzip, rapporto migliore)
/var/log/high-volume/*.log {
    daily
    rotate 30
    compresscmd /usr/bin/zstd
    compressext .zst
    compressoptions --long -19 -T0    # Multi-thread, rapporto massimo
    uncompresscmd /usr/bin/unzstd
    delaycompress
    missingok
    notifempty
}

# Compressione con xz (massimo rapporto, lento)
/var/log/archive/*.log {
    monthly
    rotate 12
    compresscmd /usr/bin/xz
    compressext .xz
    compressoptions -9e
    uncompresscmd /usr/bin/unxz
    missingok
    notifempty
}
```

### Debug e test logrotate

```bash
# Dry run (simula, non esegue)
sudo logrotate -d /etc/logrotate.conf
sudo logrotate -d /etc/logrotate.d/nginx

# Verbose (mostra cosa fa)
sudo logrotate -v /etc/logrotate.conf

# Forza rotazione (ignora criteri di tempo/dimensione)
sudo logrotate -f /etc/logrotate.d/nginx

# Stato: quando è stata l'ultima rotazione per ogni file
cat /var/lib/logrotate/status
# Output:
# "/var/log/nginx/access.log" 2026-5-22-3:0:0
# "/var/log/nginx/error.log" 2026-5-22-3:0:0
# "/var/log/syslog" 2026-5-22-3:0:0

# Se logrotate è gestito da systemd timer
systemctl status logrotate.timer
systemctl list-timers logrotate*

# Se gestito da cron
cat /etc/cron.daily/logrotate

# Reset stato (forza rotazione al prossimo run)
sudo truncate -s 0 /var/lib/logrotate/status
```

---

## Logging Centralizzato

### rsyslog → server remoto

Configurazione base per un'infrastruttura di log centralizzato con rsyslog:

```bash
# ===== SERVER RSYSLOG (ricevente) =====
# /etc/rsyslog.d/10-remote-server.conf

# Moduli di ricezione
module(load="imtcp")
module(load="imudp")

# Ascolta su TCP e UDP porta 514
input(type="imtcp" port="514" ruleset="remoteRules")
input(type="imudp" port="514" ruleset="remoteRules")

# Template per organizzare per host e data
template(name="RemoteHostLog" type="string"
    string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log"
)

template(name="RemoteHostDaily" type="string"
    string="/var/log/remote/%HOSTNAME%/%$year%-%$month%-%$day%.log"
)

# Ruleset per messaggi remoti
ruleset(name="remoteRules") {
    # Log per host/programma
    action(type="omfile"
        dynaFile="RemoteHostLog"
        dirCreateMode="0755"
        fileCreateMode="0640"
        dirOwner="syslog"
        dirGroup="adm"
    )

    # Log aggregato giornaliero per host
    action(type="omfile"
        dynaFile="RemoteHostDaily"
        dirCreateMode="0755"
        fileCreateMode="0640"
    )
}

# Logrotate per i log remoti
# /etc/logrotate.d/remote-logs
/var/log/remote/*/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 syslog adm
    sharedscripts
    postrotate
        /usr/lib/rsyslog/rsyslog-rotate
    endscript
}

# ===== CLIENT RSYSLOG (invio) =====
# /etc/rsyslog.d/90-forward.conf

# Invia tutto al server centralizzato via TCP
*.* action(type="omfwd"
    target="logserver.example.com"
    port="514"
    protocol="tcp"
    queue.type="LinkedList"
    queue.filename="fwdToLogServer"
    queue.maxdiskspace="1g"
    queue.saveonshutdown="on"
    action.resumeRetryCount="-1"
    action.resumeInterval="30"
)
```

### Stack ELK (Elasticsearch + Logstash + Kibana)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  Server 1..N │────▶│   Filebeat   │────▶│   Logstash   │────▶│Elastic-  │
│  (sorgenti)  │     │ (raccolta)   │     │ (processing) │     │search    │
└──────────────┘     └──────────────┘     └──────────────┘     └────┬─────┘
                                                                     │
                                                                     ▼
                                                              ┌──────────┐
                                                              │  Kibana  │
                                                              │(dashboard)│
                                                              └──────────┘
```

**Filebeat** (agent di raccolta sui server sorgente):

```yaml
# /etc/filebeat/filebeat.yml

filebeat.inputs:
  - type: filestream
    id: syslog
    paths:
      - /var/log/syslog
      - /var/log/auth.log
    fields:
      log_type: syslog
    fields_under_root: true

  - type: filestream
    id: nginx-access
    paths:
      - /var/log/nginx/access.log
    fields:
      log_type: nginx-access
    fields_under_root: true
    parsers:
      - ndjson:
          target: ""
          add_error_key: true

  - type: filestream
    id: nginx-error
    paths:
      - /var/log/nginx/error.log
    fields:
      log_type: nginx-error
    fields_under_root: true

  - type: journald
    id: journald
    include_matches:
      - "_SYSTEMD_UNIT=sshd.service"
      - "_SYSTEMD_UNIT=nginx.service"

# Processori (elaborazione leggera sul client)
processors:
  - add_host_metadata: ~
  - add_cloud_metadata: ~
  - drop_fields:
      fields: ["agent.ephemeral_id", "agent.id"]

output.logstash:
  hosts: ["logstash.example.com:5044"]
  ssl.certificate_authorities: ["/etc/filebeat/ca.pem"]
  ssl.certificate: "/etc/filebeat/client-cert.pem"
  ssl.key: "/etc/filebeat/client-key.pem"

# Alternativa: output diretto a Elasticsearch
# output.elasticsearch:
#   hosts: ["https://es.example.com:9200"]
#   index: "filebeat-%{+yyyy.MM.dd}"
#   username: "filebeat_writer"
#   password: "${ES_PASSWORD}"
#   ssl.certificate_authorities: ["/etc/filebeat/ca.pem"]
```

**Logstash** (processing):

```ruby
# /etc/logstash/conf.d/01-beats-input.conf
input {
  beats {
    port => 5044
    ssl_enabled => true
    ssl_certificate => "/etc/logstash/certs/logstash-cert.pem"
    ssl_key => "/etc/logstash/certs/logstash-key.pem"
    ssl_certificate_authorities => ["/etc/logstash/certs/ca.pem"]
  }
}

# /etc/logstash/conf.d/10-syslog-filter.conf
filter {
  if [log_type] == "syslog" {
    grok {
      match => {
        "message" => "%{SYSLOGTIMESTAMP:syslog_timestamp} %{SYSLOGHOST:syslog_hostname} %{DATA:syslog_program}(?:\[%{POSINT:syslog_pid}\])?: %{GREEDYDATA:syslog_message}"
      }
    }
    date {
      match => [ "syslog_timestamp", "MMM  d HH:mm:ss", "MMM dd HH:mm:ss" ]
    }
    mutate {
      remove_field => ["message"]
      rename => { "syslog_message" => "message" }
    }
  }

  if [log_type] == "nginx-access" {
    grok {
      match => {
        "message" => '%{IPORHOST:remote_addr} - %{DATA:remote_user} \[%{HTTPDATE:time_local}\] "%{WORD:method} %{URIPATHPARAM:request} HTTP/%{NUMBER:http_version}" %{INT:status} %{INT:body_bytes_sent} "%{DATA:http_referer}" "%{DATA:http_user_agent}"'
      }
    }
    geoip {
      source => "remote_addr"
      target => "geoip"
    }
    mutate {
      convert => {
        "status" => "integer"
        "body_bytes_sent" => "integer"
      }
    }
  }
}

# /etc/logstash/conf.d/90-output.conf
output {
  elasticsearch {
    hosts => ["https://es-node1:9200", "https://es-node2:9200"]
    index => "logs-%{log_type}-%{+YYYY.MM.dd}"
    user => "logstash_writer"
    password => "${ES_PASSWORD}"
    ssl_enabled => true
    ssl_certificate_authorities => ["/etc/logstash/certs/ca.pem"]
  }
}
```

### Stack EFK (Elasticsearch + Fluentd + Kibana)

Alternativa a ELK con Fluentd al posto di Logstash (comune in ambienti Kubernetes):

```xml
<!-- /etc/fluent/fluent.conf (o td-agent.conf) -->

<!-- Sorgente: syslog -->
<source>
  @type syslog
  port 5140
  protocol_type tcp
  tag syslog
</source>

<!-- Sorgente: file log -->
<source>
  @type tail
  path /var/log/nginx/access.log
  pos_file /var/log/td-agent/nginx-access.log.pos
  tag nginx.access
  <parse>
    @type nginx
  </parse>
</source>

<!-- Filtro: aggiungere hostname -->
<filter **>
  @type record_transformer
  <record>
    hostname "#{Socket.gethostname}"
  </record>
</filter>

<!-- Output: Elasticsearch -->
<match **>
  @type elasticsearch
  host es.example.com
  port 9200
  logstash_format true
  logstash_prefix fluentd
  include_tag_key true
  <buffer>
    @type file
    path /var/log/td-agent/buffer/elasticsearch
    flush_interval 10s
    chunk_limit_size 8m
    retry_max_interval 30
    retry_forever true
  </buffer>
</match>
```

### Loki + Grafana

Stack leggero per logging, ideale quando Prometheus/Grafana è già in uso:

```yaml
# --- Loki server: /etc/loki/config.yaml ---
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /var/lib/loki
  storage:
    filesystem:
      chunks_directory: /var/lib/loki/chunks
      rules_directory: /var/lib/loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h    # 7 giorni
  max_query_series: 5000
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20

storage_config:
  tsdb_shipper:
    active_index_directory: /var/lib/loki/tsdb-index
    cache_location: /var/lib/loki/tsdb-cache

compactor:
  working_directory: /var/lib/loki/compactor
  retention_enabled: true
  retention_delete_delay: 2h
  delete_request_store: filesystem

# --- Promtail agent: /etc/promtail/config.yaml ---
server:
  http_listen_port: 9080

positions:
  filename: /var/lib/promtail/positions.yaml

clients:
  - url: http://loki.example.com:3100/loki/api/v1/push
    tenant_id: default

scrape_configs:
  - job_name: syslog
    static_configs:
      - targets: [localhost]
        labels:
          job: syslog
          host: web-server-01
          __path__: /var/log/syslog

  - job_name: auth
    static_configs:
      - targets: [localhost]
        labels:
          job: auth
          host: web-server-01
          __path__: /var/log/auth.log

  - job_name: nginx
    static_configs:
      - targets: [localhost]
        labels:
          job: nginx
          host: web-server-01
          __path__: /var/log/nginx/*.log
    pipeline_stages:
      - regex:
          expression: '^(?P<remote_addr>\S+) .* \[(?P<time_local>.*)\] "(?P<method>\S+) (?P<request>\S+) .*" (?P<status>\d+) (?P<bytes>\d+)'
      - labels:
          method:
          status:

  - job_name: journal
    journal:
      max_age: 12h
      labels:
        job: journal
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: 'unit'
      - source_labels: ['__journal__hostname']
        target_label: 'hostname'
      - source_labels: ['__journal_priority_keyword']
        target_label: 'severity'
```

### Graylog

Alternativa enterprise open source con UI ricca per ricerca e alerting:

```bash
# Graylog riceve messaggi via GELF (Graylog Extended Log Format)
# Configurare rsyslog per inviare in formato GELF via TCP

# /etc/rsyslog.d/60-graylog.conf
module(load="omfwd")

template(name="GELFFormat" type="list") {
    constant(value="{\"version\":\"1.1\",\"host\":\"")
    property(name="hostname")
    constant(value="\",\"short_message\":\"")
    property(name="msg" format="jsonf")
    constant(value="\",\"full_message\":\"")
    property(name="rawmsg" format="jsonf")
    constant(value="\",\"timestamp\":")
    property(name="timegenerated" dateformat="unixtimestamp")
    constant(value=",\"level\":")
    property(name="syslogseverity")
    constant(value=",\"facility\":\"")
    property(name="syslogfacility-text")
    constant(value="\"}\n")
}

*.* action(type="omfwd"
    target="graylog.example.com"
    port="12201"
    protocol="tcp"
    template="GELFFormat"
    queue.type="LinkedList"
    queue.filename="graylogQueue"
    queue.maxdiskspace="1g"
    queue.saveonshutdown="on"
)
```

### Scelta dello stack

| Stack | Pro | Contro | Ideale per |
|-------|-----|--------|------------|
| **rsyslog remoto** | Semplice, nativo, basso overhead | No UI, analisi limitata | Piccole infrastrutture, aggregazione base |
| **ELK** | Potente, full-text search, dashboard | Risorse elevate, complessità | Enterprise, analisi avanzata, compliance |
| **EFK** | Kubernetes-native, plugin ricchi | Meno immediato di Logstash per syslog | Ambienti Kubernetes |
| **Loki+Grafana** | Leggero, label-based, si integra con Prometheus | No full-text search per default | Chi usa già Grafana/Prometheus |
| **Graylog** | UI buona, alerting, pipeline processing | Richiede MongoDB + ES | Team che vogliono UI senza Kibana |

---

## Logging Strutturato

### Formato JSON

Il logging strutturato sostituisce il testo libero con formati machine-parseable, facilitando query, aggregazione e correlazione:

```json
{
    "@timestamp": "2026-05-22T10:30:45.123Z",
    "level": "error",
    "logger": "com.example.api.UserService",
    "message": "Failed to create user",
    "error": {
        "type": "ValidationException",
        "message": "Email already registered",
        "stack_trace": "..."
    },
    "context": {
        "request_id": "req-abc-123-def",
        "user_email_hash": "sha256:a1b2c3...",
        "endpoint": "POST /api/v1/users",
        "duration_ms": 45
    },
    "host": "api-server-03",
    "service": "user-service",
    "environment": "production"
}
```

Vantaggi rispetto al testo libero:

```
# Testo libero — parsing fragile
2026-05-22 10:30:45 ERROR UserService - Failed to create user: Email already registered (request: req-abc-123)

# JSON — ogni campo è indicizzabile e queryable
{"timestamp":"2026-05-22T10:30:45Z","level":"error","service":"user-service","message":"Failed to create user","error_type":"ValidationException"}
```

### Coppie chiave-valore

Formato intermedio tra testo libero e JSON, leggibile sia da umani che da parser:

```
# Formato key=value (usato da systemd, alcuni web server)
timestamp=2026-05-22T10:30:45Z level=error service=user-service action=create_user result=failure reason="email_already_registered" duration_ms=45 request_id=req-abc-123

# rsyslog può parsarlo con mmpstrucdata o mmkv
module(load="mmkv")
action(type="mmkv")
```

### Correlation ID

Il correlation ID (o request ID, trace ID) è un identificatore unico che segue una richiesta attraverso tutti i servizi di un sistema distribuito:

```
# Generare un correlation ID all'ingresso nel sistema
# (API gateway, load balancer, primo servizio)
REQUEST_ID=$(uuidgen)
# oppure in formato più compatto:
REQUEST_ID=$(openssl rand -hex 8)

# Propagare negli header HTTP
X-Request-ID: req-abc-123-def-456

# Ogni servizio include il correlation ID in ogni log
{"request_id":"req-abc-123-def-456","service":"api-gateway","message":"Received POST /users"}
{"request_id":"req-abc-123-def-456","service":"user-service","message":"Creating user"}
{"request_id":"req-abc-123-def-456","service":"email-service","message":"Sending welcome email"}
{"request_id":"req-abc-123-def-456","service":"audit-service","message":"User created event logged"}

# Query per correlation ID (es. in Elasticsearch/Loki)
# Mostra l'intero percorso della richiesta attraverso i servizi
```

### Structured logging in journald

journald è intrinsecamente strutturato. Le applicazioni possono inviare campi personalizzati:

```bash
# Dalla shell con systemd-cat
echo "Operazione completata" | systemd-cat -t myapp -p info

# Con logger e campi strutturati
logger --journald <<EOF
MESSAGE=Utente creato con successo
PRIORITY=6
SYSLOG_IDENTIFIER=myapp
REQUEST_ID=req-abc-123
USER_ACTION=create_user
RESULT=success
DURATION_MS=45
EOF

# Query per campo custom
journalctl REQUEST_ID=req-abc-123
journalctl USER_ACTION=create_user RESULT=failure

# In Python con python-systemd
# import systemd.journal
# systemd.journal.send(
#     MESSAGE="User created",
#     PRIORITY=6,
#     SYSLOG_IDENTIFIER="myapp",
#     REQUEST_ID="req-abc-123",
#     USER_ACTION="create_user",
#     RESULT="success"
# )

# In C con sd_journal_send
# sd_journal_send("MESSAGE=User created",
#                 "PRIORITY=6",
#                 "REQUEST_ID=req-abc-123",
#                 NULL);
```

---

## Best Practice per il Logging Applicativo

### Livelli di log: quando usare cosa

```
FATAL/EMERG  → L'applicazione non può continuare. Crash imminente.
              Esempio: "Cannot bind to port 443: Address already in use"
              Azione: page on-call, riavvio necessario

ERROR        → Operazione fallita, ma l'applicazione continua.
              Esempio: "Failed to process payment for order #12345"
              Azione: alert, investigazione necessaria

WARNING      → Situazione anomala, potenziale problema futuro.
              Esempio: "Connection pool at 90% capacity (45/50)"
              Azione: monitorare, potrebbe richiedere azione

INFO         → Eventi di business significativi, operazioni normali.
              Esempio: "User john@example.com logged in from 192.168.1.5"
              Azione: nessuna, utile per audit trail

DEBUG        → Dettagli tecnici per sviluppatori.
              Esempio: "SQL query took 234ms: SELECT * FROM users WHERE..."
              Azione: nessuna, solo per troubleshooting

TRACE        → Massimo dettaglio, flusso di esecuzione.
              Esempio: "Entering validateInput(), params: {name: '...', ...}"
              Azione: nessuna, solo per debugging approfondito
```

Regola pratica per la produzione:

```
Produzione:   INFO (default), WARNING per servizi critici
Staging:      DEBUG
Sviluppo:     DEBUG o TRACE
Troubleshooting produzione: abbassare temporaneamente a DEBUG per il servizio specifico
```

### Contesto nei messaggi di log

Un buon messaggio di log risponde a: chi, cosa, quando, perché, con quale risultato?

```
# CATTIVO — poco contesto
"Error processing request"
"File not found"
"Connection failed"

# BUONO — contesto completo
"Failed to process payment: gateway timeout after 30s [order_id=12345, user_id=67890, gateway=stripe, amount=99.99EUR]"
"Configuration file not found: /etc/myapp/config.yaml (checked: /etc/myapp/, ~/.config/myapp/, ./config/)"
"Database connection failed: PostgreSQL at db-primary:5432, retrying in 5s (attempt 3/10) [error=connection_refused]"
```

Campi consigliati per ogni messaggio:

```
- timestamp (automatico)
- level (automatico)
- service/component name
- operation/action
- result (success/failure)
- duration (per operazioni misurabili)
- identifiers (request_id, user_id, order_id...)
- error details (per failure)
- context rilevante (non sensibile)
```

### Rate limiting dei log

Log flooding può saturare disco, rete e sistemi di logging centralizzato:

```bash
# journald rate limiting (in journald.conf)
RateLimitIntervalSec=30s
RateLimitBurst=10000
# Max 10000 messaggi ogni 30s per service/PID
# Messaggio: "Suppressed N messages from <unit>"

# rsyslog rate limiting
# Globale:
global(
    processInternalMessages="on"
)
# Per action:
action(type="omfile"
    file="/var/log/noisy-app.log"
    action.execOnlyEveryNthTime="10"     # Scrivi solo 1 su 10
)

# Per input (imuxsock):
module(load="imuxsock"
    SysSock.RateLimit.Interval="5"       # Intervallo in secondi
    SysSock.RateLimit.Burst="200"        # Max messaggi per intervallo
)

# syslog-ng rate limiting
# Nelle opzioni di una source:
source s_local {
    system();
    internal();
};
# Nelle opzioni del log path:
log {
    source(s_local);
    destination(d_messages);
    flags(flow-control);                  # Back-pressure sulla sorgente
};

# A livello applicativo: implementare log sampling
# es. loggare solo 1% delle richieste 200 OK,
# ma 100% degli errori
```

### Filtraggio dati sensibili

Mai loggare: password, token, session ID, numeri di carta, SSN, dati sanitari, chiavi private.

```bash
# Esempio: sanificazione in rsyslog con mmanon
module(load="mmanon")
action(type="mmanon"
    # Anonimizza IPv4 (ultimi 2 ottetti)
    ipv4.bits="16"
    ipv4.mode="random-consistent"
)

# Esempio: rimuovere pattern sensibili con mmexternal
# Script esterno che filtra i campi
action(type="mmexternal"
    binary="/usr/local/bin/sanitize-logs.sh"
)

# Esempio generico di sanificazione (pseudocodice):
# PRIMA: "User login: email=user@example.com password=s3cr3t token=abc123"
# DOPO:  "User login: email=u***@example.com password=*** token=***"

# In rsyslog con property replacer
template(name="SanitizedLog" type="string"
    string="%timegenerated% %hostname% %programname%: %msg:R,ERE,0,FIELD:password=[^ ]*--end:R,ERE,0,BLANK%\n"
)
```

### Log e performance

```bash
# Impatto I/O: log sincrono vs asincrono
# rsyslog: il trattino (-) prima del path disabilita fsync
*.info                          -/var/log/messages    # Asincrono (performance)
auth,authpriv.*                 /var/log/auth.log     # Sincrono (sicurezza)

# journald: compressione e flush
# Compress=yes riduce I/O su disco
# In /etc/systemd/journald.conf:
# SyncIntervalSec=5min    # Flush su disco ogni 5 minuti (default)

# Log asincrono nelle applicazioni:
# - Scrivere in un buffer in memoria
# - Flush periodico o a soglia di dimensione
# - Accettare la possibilità di perdere messaggi recenti in caso di crash

# Monitorare l'I/O dei log
sudo iotop -oP | grep -E 'rsyslog|journal|syslog'
```

---

## Audit Logging: auditd

### Architettura audit framework

```
┌─────────────────────────────────────────────────┐
│                   Kernel Space                   │
│                                                  │
│  ┌───────────┐    ┌───────────────────────────┐ │
│  │ Syscalls  │───▶│   Audit subsystem         │ │
│  │ File ops  │    │   (kauditd)               │ │
│  │ Network   │    │                           │ │
│  └───────────┘    └────────────┬──────────────┘ │
│                                │                 │
└────────────────────────────────┼─────────────────┘
                                 │ netlink
                                 ▼
┌────────────────────────────────────────────────────┐
│                   User Space                        │
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌───────────────┐  │
│  │ auditd   │──▶│audit.log │   │ audispd       │  │
│  │ (demone) │   │          │   │ (dispatcher)  │  │
│  └──────────┘   └──────────┘   └───────┬───────┘  │
│                                         │          │
│  ┌──────────┐   ┌──────────┐   ┌───────▼───────┐  │
│  │aureport  │   │ausearch  │   │ Plugin:       │  │
│  │(report)  │   │(search)  │   │ - syslog      │  │
│  └──────────┘   └──────────┘   │ - remote      │  │
│                                 │ - af_unix     │  │
│  ┌──────────┐                  └───────────────┘  │
│  │auditctl  │                                      │
│  │(control) │                                      │
│  └──────────┘                                      │
└────────────────────────────────────────────────────┘
```

Il framework di audit Linux cattura eventi a livello kernel: syscall, accesso a file, operazioni di rete, cambio di privilegi. È distinto da syslog/journald.

```bash
# Verificare che auditd sia attivo
sudo systemctl status auditd

# Stato del framework
sudo auditctl -s
# Output:
# enabled 1
# failure 1          # 0=silent, 1=printk, 2=panic
# pid 1234
# rate_limit 0
# backlog_limit 8192
# lost 0
# backlog 0

# Configurazione demone
# /etc/audit/auditd.conf
# log_file = /var/log/audit/audit.log
# log_format = ENRICHED     # o RAW
# max_log_file = 50          # MB
# max_log_file_action = ROTATE
# num_logs = 5
# space_left = 75            # MB
# space_left_action = SYSLOG
# admin_space_left = 50      # MB
# admin_space_left_action = HALT
# disk_full_action = HALT
# disk_error_action = HALT
```

### Regole auditd

Le regole si definiscono in `/etc/audit/rules.d/` e si caricano con `augenrules`.

```bash
# /etc/audit/rules.d/10-base.rules

# Eliminare tutte le regole precedenti
-D

# Impostare il buffer (aumentare se si ricevono messaggi di backlog)
-b 8192

# Rendere la configurazione immutabile dopo il caricamento (richiede reboot per cambiare)
# -e 2    # Decommentare in produzione

# /etc/audit/rules.d/30-access.rules

# === WATCH RULES (monitorare file/directory) ===
# Sintassi: -w <path> -p <permissions> -k <key>
# Permissions: r=read, w=write, x=execute, a=attribute change

# Monitorare /etc/passwd e /etc/shadow
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/gshadow -p wa -k identity

# Monitorare sudoers
-w /etc/sudoers -p wa -k sudo_config
-w /etc/sudoers.d/ -p wa -k sudo_config

# Monitorare configurazione SSH
-w /etc/ssh/sshd_config -p wa -k sshd_config

# Monitorare configurazione di rete
-w /etc/hosts -p wa -k network_config
-w /etc/sysconfig/network -p wa -k network_config
-w /etc/resolv.conf -p wa -k network_config

# Monitorare cron
-w /etc/crontab -p wa -k cron_config
-w /etc/cron.d/ -p wa -k cron_config
-w /var/spool/cron/ -p wa -k cron_config

# Monitorare moduli kernel
-w /sbin/insmod -p x -k kernel_modules
-w /sbin/modprobe -p x -k kernel_modules
-w /sbin/rmmod -p x -k kernel_modules

# Monitorare i log stessi (anti-tampering)
-w /var/log/audit/ -p wa -k audit_log_access
-w /var/log/auth.log -p wa -k auth_log_access

# /etc/audit/rules.d/40-syscall.rules

# === SYSCALL RULES ===
# Sintassi: -a <list>,<action> -F <field>=<value> -S <syscall> -k <key>

# Monitorare esecuzione di comandi (execve)
-a always,exit -F arch=b64 -S execve -k exec_commands
-a always,exit -F arch=b32 -S execve -k exec_commands

# Monitorare tentativi di accesso non autorizzato
-a always,exit -F arch=b64 -S open,openat,creat -F exit=-EACCES -k access_denied
-a always,exit -F arch=b64 -S open,openat,creat -F exit=-EPERM -k access_denied

# Monitorare cancellazione file
-a always,exit -F arch=b64 -S unlink,unlinkat,rename,renameat -k file_delete

# Monitorare mount/unmount
-a always,exit -F arch=b64 -S mount,umount2 -k mount_ops

# Monitorare cambio di orario
-a always,exit -F arch=b64 -S adjtimex,settimeofday -k time_change
-a always,exit -F arch=b64 -S clock_settime -k time_change
-w /etc/localtime -p wa -k time_change

# Monitorare cambio di hostname
-a always,exit -F arch=b64 -S sethostname,setdomainname -k hostname_change

# Monitorare operazioni di root privilegiate
-a always,exit -F arch=b64 -S setuid,setgid,setreuid,setregid -F a0!=0 -k privilege_escalation
```

```bash
# Caricare le regole
sudo augenrules --load

# Verificare le regole caricate
sudo auditctl -l

# Aggiungere una regola temporanea (non sopravvive al reboot)
sudo auditctl -w /tmp/sensitive-file -p rwa -k temp_watch

# Rimuovere una regola temporanea
sudo auditctl -W /tmp/sensitive-file -p rwa -k temp_watch
```

### aureport: reportistica

```bash
# Report sommario
sudo aureport --summary

# Report autenticazione
sudo aureport -au                  # Tentativi di autenticazione
sudo aureport -au --failed         # Solo quelli falliti

# Report login
sudo aureport -l                   # Tutti i login
sudo aureport -l --failed          # Login falliti

# Report esecuzione comandi
sudo aureport -x                   # Comandi eseguiti
sudo aureport -x --summary         # Sommario comandi

# Report accesso file
sudo aureport -f                   # Accessi a file
sudo aureport -f --failed          # Accessi negati

# Report per chiave
sudo aureport -k                   # Raggruppati per audit key

# Report anomalie
sudo aureport --anomaly            # Eventi anomali

# Report per periodo
sudo aureport -au --start 05/20/2026 00:00:00 --end 05/22/2026 23:59:59

# Report MAC (Mandatory Access Control — SELinux/AppArmor)
sudo aureport -m                   # Eventi MAC
sudo aureport -m --failed          # Violazioni MAC
```

### ausearch: ricerca eventi

```bash
# Cercare per chiave
sudo ausearch -k identity           # Eventi con key "identity"
sudo ausearch -k sudo_config        # Modifiche a sudoers

# Cercare per timestamp
sudo ausearch -ts today             # Da oggi
sudo ausearch -ts recent            # Ultimi 10 minuti
sudo ausearch -ts 05/20/2026 08:00:00 -te 05/22/2026 18:00:00

# Cercare per utente
sudo ausearch -ua 1000              # UID 1000
sudo ausearch -ua root              # root

# Cercare per tipo evento
sudo ausearch -m USER_LOGIN         # Login
sudo ausearch -m EXECVE             # Esecuzione comandi
sudo ausearch -m USER_AUTH          # Autenticazione
sudo ausearch -m AVC                # SELinux violations

# Cercare per file
sudo ausearch -f /etc/passwd        # Accessi a /etc/passwd

# Cercare per processo
sudo ausearch -p 12345              # PID specifico

# Cercare per syscall
sudo ausearch -sc open              # Syscall open

# Output interpretato (più leggibile)
sudo ausearch -k identity -i

# Output raw (per script)
sudo ausearch -k identity --raw

# Combinazioni
sudo ausearch -k exec_commands -ua root -ts today -i
```

### Compliance STIG e CIS

I benchmark STIG (Security Technical Implementation Guide) e CIS (Center for Internet Security) definiscono regole audit obbligatorie:

```bash
# /etc/audit/rules.d/99-compliance.rules

# CIS Benchmark 4.1.4: Ensure events that modify date and time
# information are collected
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-a always,exit -F arch=b32 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# CIS 4.1.5: Ensure events that modify user/group information
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

# CIS 4.1.6: Ensure events that modify the network environment
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-a always,exit -F arch=b32 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/hostname -p wa -k system-locale

# CIS 4.1.7: Ensure events that modify MAC policy
-w /etc/apparmor/ -p wa -k MAC-policy
-w /etc/apparmor.d/ -p wa -k MAC-policy

# CIS 4.1.8: Ensure login and logout events
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins

# CIS 4.1.9: Ensure session initiation information
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k logins
-w /var/log/btmp -p wa -k logins

# CIS 4.1.11: Ensure use of privileged commands
# Generare automaticamente:
# find / -xdev -type f -perm -4000 -o -perm -2000 2>/dev/null | \
#   awk '{print "-a always,exit -F path=" $1 " -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged"}'

# CIS 4.1.14: Ensure changes to system administration scope
-w /etc/sudoers -p wa -k scope
-w /etc/sudoers.d/ -p wa -k scope

# CIS 4.1.15: Ensure system administrator command executions
-a always,exit -F arch=b64 -S execve -C uid!=euid -F euid=0 -k actions
-a always,exit -F arch=b32 -S execve -C uid!=euid -F euid=0 -k actions

# CIS 4.1.17: Ensure kernel module loading/unloading
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k modules

# Rendere le regole immutabili (ultimo)
-e 2
```

---

## Kernel Logging

### dmesg e ring buffer del kernel

```bash
# Leggere il ring buffer del kernel
dmesg                              # Output completo
dmesg -T                           # Timestamp leggibile (approssimativo)
dmesg -H                           # Output "human" con pager e colori
dmesg --color=always | less -R     # Colori con pager

# Filtrare per livello
dmesg --level=err                  # Solo errori
dmesg --level=err,warn             # Errori e warning
dmesg --level=emerg,alert,crit,err # Tutto da err in su

# Filtrare per facility
dmesg --facility=kern              # Solo kernel
dmesg --facility=user              # Solo user-space

# Seguire nuovi messaggi
dmesg -w                           # Come tail -f per il kernel ring buffer
dmesg -wH                          # Follow con formato human

# Cancellare il ring buffer (richiede root)
sudo dmesg -c                     # Stampa e cancella
sudo dmesg -C                     # Cancella senza stampare

# Decodificare oops/panic (se disponibile)
dmesg | grep -A 20 "Oops\|BUG\|RIP\|Call Trace"

# Cercare errori hardware
dmesg | grep -iE 'error|fail|warn|bad|corrupt|timeout'
dmesg | grep -i 'ata\|scsi\|sd[a-z]\|nvme'   # Errori disco
dmesg | grep -i 'edac\|mce\|ecc'              # Errori memoria
dmesg | grep -i 'eth\|wlan\|wlp\|enp'         # Errori rete

# Informazioni utili dal boot
dmesg | grep -i 'memory\|cpu\|bios'           # Hardware rilevato
dmesg | grep -i 'usb'                          # Dispositivi USB
dmesg | grep -i 'firmware'                     # Firmware caricati
```

### /dev/kmsg

`/dev/kmsg` è l'interfaccia al ring buffer del kernel, usata da journald e altri demoni:

```bash
# Leggere direttamente (formato raw)
sudo cat /dev/kmsg
# Output: <6>  [12345.678901] eth0: link up

# Scrivere nel ring buffer (utile per marker/debug)
echo "<6>MyApp: custom kernel log message" | sudo tee /dev/kmsg

# Il formato è: <priority>[timestamp] message
# Priority = facility * 8 + severity (come syslog PRI)
# <0> = kern.emerg, <1> = kern.alert, ..., <7> = kern.debug

# journald legge da /dev/kmsg automaticamente
# rsyslog usa il modulo imklog per lo stesso scopo
```

### Livelli KERN_*

I livelli di log del kernel, definiti in `<linux/kern_levels.h>`:

```
KERN_EMERG   (0)  – Sistema instabile, crash imminente
KERN_ALERT   (1)  – Azione immediata richiesta
KERN_CRIT    (2)  – Condizione critica (hardware, driver)
KERN_ERR     (3)  – Errore di operazione
KERN_WARNING (4)  – Condizione di warning
KERN_NOTICE  (5)  – Condizione normale ma significativa
KERN_INFO    (6)  – Informativo
KERN_DEBUG   (7)  – Debug (solo con CONFIG_DYNAMIC_DEBUG o livello impostato)

# Controllare il livello corrente di log della console
cat /proc/sys/kernel/printk
# Output: 4    4    1    7
#          │    │    │    └─ default_console_loglevel
#          │    │    └────── minimum_console_loglevel
#          │    └─────────── default_message_loglevel
#          └──────────────── console_loglevel (attuale)

# Impostare il livello della console (temporaneo)
echo 7 | sudo tee /proc/sys/kernel/printk    # Mostra anche debug
echo 4 | sudo tee /proc/sys/kernel/printk    # Solo warning e superiori

# Impostare permanentemente in sysctl
# /etc/sysctl.d/99-kernel-log.conf
# kernel.printk = 4 4 1 7

# Dynamic debug (moduli specifici)
echo 'module e1000e +p' | sudo tee /sys/kernel/debug/dynamic_debug/control
# Abilita debug per il driver e1000e
echo 'file drivers/net/* +p' | sudo tee /sys/kernel/debug/dynamic_debug/control
# Abilita debug per tutti i driver di rete
```

### Crash dump e kdump

kdump cattura un dump della memoria quando il kernel va in panic, per analisi post-mortem:

```bash
# Installare kdump
sudo apt install kdump-tools crash    # Debian/Ubuntu
sudo dnf install kexec-tools crash    # RHEL/Fedora

# Configurare il kernel per riservare memoria al crash kernel
# In /etc/default/grub:
# GRUB_CMDLINE_LINUX="... crashkernel=256M"
# sudo update-grub && sudo reboot

# Verificare che kdump sia attivo
sudo systemctl status kdump
cat /sys/kernel/kexec_crash_loaded    # 1 = pronto

# Configurare la directory per i dump
# /etc/kdump.conf (RHEL) o /etc/default/kdump-tools (Debian)
# path /var/crash
# core_collector makedumpfile -l --message-level 7 -d 31

# Analizzare un crash dump
sudo crash /var/crash/*/vmcore /usr/lib/debug/boot/vmlinux-$(uname -r)
# crash> bt           # Backtrace
# crash> log          # Log del kernel al momento del crash
# crash> ps           # Processi
# crash> files        # File aperti
# crash> vm           # Stato memoria virtuale

# Testare kdump (attenzione: causa un crash reale del sistema)
# echo c | sudo tee /proc/sysrq-trigger
```

---

## Strumenti di Analisi Log

### Pattern grep/awk/sed

```bash
# === CONTARE E AGGREGARE ===

# Contare errori per tipo
grep -c "error" /var/log/syslog
grep -ci "fail" /var/log/auth.log

# Top IP con login falliti (SSH brute force detection)
grep "Failed password" /var/log/auth.log | \
    awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -20

# Errori raggruppati per ora
grep "error" /var/log/syslog | \
    awk '{print $1, $2, substr($3,1,2)":00"}' | sort | uniq -c

# Distribuzione per severity nei log syslog
awk '{print $6}' /var/log/syslog | sort | uniq -c | sort -rn

# === ANALISI WEB LOG ===

# Richieste HTTP per status code
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

# Top URL per errore 404
awk '$9 == "404" {print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head

# Top IP per volume richieste
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20

# Richieste lente (>5 secondi, formato combined con request time)
awk -F'"' '$NF > 5 {print $0}' /var/log/nginx/access.log

# Traffico per ora
awk '{print $4}' /var/log/nginx/access.log | cut -d: -f1-2 | sort | uniq -c

# Bandwidth per IP
awk '{sum[$1]+=$10} END {for(ip in sum) print sum[ip], ip}' \
    /var/log/nginx/access.log | sort -rn | head -20

# Top user-agent (detection bot)
awk -F'"' '{print $6}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20

# === ANALISI SICUREZZA ===

# Utenti con sudo
grep "sudo:" /var/log/auth.log | awk '{print $6}' | sort | uniq -c | sort -rn

# Comandi sudo eseguiti
grep "COMMAND=" /var/log/auth.log | sed 's/.*COMMAND=//' | sort | uniq -c | sort -rn

# Login riusciti per utente
grep "Accepted" /var/log/auth.log | awk '{print $9}' | sort | uniq -c | sort -rn

# Sessioni SSH per IP e durata
grep "session opened\|session closed" /var/log/auth.log | \
    awk '{print $1,$2,$3,$11}' | head -20

# Account lockout
grep "pam_tally\|faillock" /var/log/auth.log

# === ANALISI KERNEL ===

# OOM killer events
grep "Out of memory\|oom-kill\|Killed process" /var/log/kern.log

# Errori I/O disco
grep -i "i/o error\|bad sector\|read error" /var/log/kern.log

# Errori memoria (ECC, MCE)
grep -i "edac\|mce\|hardware error" /var/log/kern.log

# === FOLLOW IN TEMPO REALE ===
tail -f /var/log/syslog | grep --line-buffered "error"
journalctl -f -p err
tail -f /var/log/nginx/access.log | awk '$9 >= 500'

# === CORRELAZIONE MULTI-FILE ===
# Trovare tutti gli eventi per un IP specifico in tutti i log
IP="192.168.1.100"
grep -rn "$IP" /var/log/ --include="*.log" 2>/dev/null

# Trovare tutti gli eventi in un intervallo di tempo
grep "May 22 1[0-1]:" /var/log/syslog /var/log/auth.log /var/log/kern.log
```

### lnav: navigatore log avanzato

lnav è un visualizzatore di log avanzato con auto-detection di formato, ricerca, filtri e SQL:

```bash
# Installare
sudo apt install lnav               # Debian/Ubuntu
sudo dnf install lnav               # RHEL/Fedora

# Uso base
lnav /var/log/syslog                 # Singolo file
lnav /var/log/syslog /var/log/auth.log  # Più file, merged cronologicamente
lnav /var/log/nginx/                 # Directory intera

# Leggere da journalctl
journalctl -o short-iso | lnav

# Comandi dentro lnav:
# /pattern       → Cerca pattern (evidenzia)
# :filter-in <regex>   → Mostra solo righe che matchano
# :filter-out <regex>  → Nascondi righe che matchano
# :set-min-log-level error  → Solo error e superiori
# ;SELECT * FROM logline WHERE log_level = 'error'  → Query SQL
# ;SELECT log_hostname, count(*) FROM logline GROUP BY log_hostname  → Aggregazione
# i                → Mostra istogramma temporale
# TAB              → Passa ai file/filtri
# q                → Esci

# lnav supporta formati auto-riconosciuti:
# syslog, Apache combined, nginx, strace, generic timestamps
```

### GoAccess: analisi log web

GoAccess è un analizzatore di log web in tempo reale con output terminale e HTML:

```bash
# Installare
sudo apt install goaccess            # Debian/Ubuntu
sudo dnf install goaccess            # RHEL/Fedora

# Analisi interattiva in terminale
goaccess /var/log/nginx/access.log --log-format=COMBINED

# Generare report HTML
goaccess /var/log/nginx/access.log --log-format=COMBINED -o /var/www/html/report.html

# Report HTML in tempo reale (websocket)
goaccess /var/log/nginx/access.log --log-format=COMBINED -o /var/www/html/report.html --real-time-html

# Formati predefiniti
goaccess /var/log/nginx/access.log --log-format=COMBINED
goaccess /var/log/apache2/access.log --log-format=COMBINED
goaccess /var/log/nginx/access.log --log-format=VCOMBINED  # Virtual host

# File multipli
zcat /var/log/nginx/access.log.*.gz | \
    goaccess --log-format=COMBINED -

# Configurazione personalizzata in ~/.goaccessrc o /etc/goaccess/goaccess.conf
```

### multitail: visualizzazione multi-file

```bash
# Installare
sudo apt install multitail

# Seguire più file in pannelli separati
multitail /var/log/syslog /var/log/auth.log

# Pannelli in colonne
multitail -s 2 /var/log/syslog /var/log/auth.log /var/log/kern.log /var/log/nginx/error.log

# Con colorazione per pattern
multitail -e "error" -e "warning" /var/log/syslog

# Seguire output di comandi
multitail -l "journalctl -f -u nginx" -l "journalctl -f -u php-fpm"

# Merge di più file con distinzione per colore
multitail --mergeall /var/log/syslog /var/log/auth.log
```

### jq per log JSON

```bash
# Se i log sono in formato JSON (uno per riga — NDJSON)

# Estrarre campi specifici
cat app.log | jq '.timestamp, .level, .message'

# Filtrare per livello
cat app.log | jq 'select(.level == "error")'

# Filtrare per campo nested
cat app.log | jq 'select(.context.request_id == "req-abc-123")'

# Aggregare (contare per livello)
cat app.log | jq -r '.level' | sort | uniq -c | sort -rn

# Estrarre in formato tabulare
cat app.log | jq -r '[.timestamp, .level, .message] | @tsv'

# Combinare con journalctl
journalctl -u myapp -o json --no-pager | \
    jq 'select(.PRIORITY == "3") | {time: .__REALTIME_TIMESTAMP, msg: .MESSAGE}'

# Cercare pattern nel messaggio
cat app.log | jq 'select(.message | test("timeout|connection refused"))'

# Calcolare durata media delle richieste
cat app.log | jq '[select(.duration_ms != null) | .duration_ms] | add / length'
```

---

## Alerting Basato sui Log

### Pattern di alerting

```bash
# === ALERTING CON SCRIPT CRON ===

#!/bin/bash
# /usr/local/bin/log-alert.sh — eseguire ogni 5 minuti da cron

THRESHOLD_SSH_FAIL=10
THRESHOLD_OOM=1
THRESHOLD_DISK_ERROR=1
WEBHOOK_URL="https://hooks.slack.example.com/services/xxx/yyy/zzz"
INTERVAL="5 minutes ago"

# Contare login SSH falliti
SSH_FAILS=$(journalctl -u sshd --since "$INTERVAL" --no-pager 2>/dev/null | \
    grep -c "Failed password")

if [ "$SSH_FAILS" -ge "$THRESHOLD_SSH_FAIL" ]; then
    TOP_IPS=$(journalctl -u sshd --since "$INTERVAL" --no-pager | \
        grep "Failed password" | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -5)
    curl -s -X POST "$WEBHOOK_URL" \
        -H 'Content-type: application/json' \
        -d "{\"text\":\"SSH Brute Force Alert: $SSH_FAILS failed attempts in 5 min\nTop IPs:\n$TOP_IPS\"}" \
        >/dev/null 2>&1
fi

# OOM killer
OOM_COUNT=$(journalctl -k --since "$INTERVAL" --no-pager 2>/dev/null | \
    grep -c "Out of memory")

if [ "$OOM_COUNT" -ge "$THRESHOLD_OOM" ]; then
    KILLED=$(journalctl -k --since "$INTERVAL" --no-pager | \
        grep "Killed process" | tail -5)
    curl -s -X POST "$WEBHOOK_URL" \
        -H 'Content-type: application/json' \
        -d "{\"text\":\"OOM Killer Alert: $OOM_COUNT events\n$KILLED\"}" \
        >/dev/null 2>&1
fi

# Errori disco
DISK_ERRS=$(dmesg --since "$INTERVAL" 2>/dev/null | grep -ci "i/o error\|bad sector" || \
    journalctl -k --since "$INTERVAL" --no-pager 2>/dev/null | grep -ci "i/o error\|bad sector")

if [ "$DISK_ERRS" -ge "$THRESHOLD_DISK_ERROR" ]; then
    curl -s -X POST "$WEBHOOK_URL" \
        -H 'Content-type: application/json' \
        -d "{\"text\":\"Disk I/O Error Alert: $DISK_ERRS errors detected\"}" \
        >/dev/null 2>&1
fi

# === CRON ENTRY ===
# */5 * * * * /usr/local/bin/log-alert.sh
```

### Anomaly detection

```bash
# === BASELINE + DEVIAZIONE ===

#!/bin/bash
# /usr/local/bin/log-anomaly.sh

# Calcolare baseline: media errori per ora negli ultimi 7 giorni
BASELINE=$(for i in $(seq 1 7); do
    journalctl --since "$i days ago 00:00" --until "$i days ago 01:00" \
        -p err --no-pager 2>/dev/null | wc -l
done | awk '{sum+=$1; count++} END {print int(sum/count)}')

# Errori nell'ultima ora
CURRENT=$(journalctl --since "1 hour ago" -p err --no-pager | wc -l)

# Alert se > 3x baseline
THRESHOLD=$((BASELINE * 3))
if [ "$CURRENT" -gt "$THRESHOLD" ] && [ "$THRESHOLD" -gt 0 ]; then
    echo "ANOMALY: $CURRENT errors in last hour (baseline: $BASELINE, threshold: $THRESHOLD)"
    # Inviare alert via webhook
fi

# === PATTERN NUOVI (mai visti) ===

# Estrarre pattern unici di errore degli ultimi 7 giorni
journalctl -p err --since "7 days ago" --no-pager -o cat 2>/dev/null | \
    sed 's/[0-9]\+/NUM/g' | sort -u > /tmp/known-patterns.txt

# Pattern dell'ultima ora
journalctl -p err --since "1 hour ago" --no-pager -o cat 2>/dev/null | \
    sed 's/[0-9]\+/NUM/g' | sort -u > /tmp/current-patterns.txt

# Pattern nuovi (mai visti)
comm -23 /tmp/current-patterns.txt /tmp/known-patterns.txt > /tmp/new-patterns.txt

if [ -s /tmp/new-patterns.txt ]; then
    echo "NEW ERROR PATTERNS detected:"
    cat /tmp/new-patterns.txt
fi
```

### Integrazione con sistemi di notifica

```bash
# === WEBHOOK GENERICO (Slack, Mattermost, Discord, Teams) ===

send_webhook() {
    local message="$1"
    local severity="$2"     # info, warning, critical
    local webhook_url="$3"

    # Escape JSON
    message=$(echo "$message" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')

    curl -s -X POST "$webhook_url" \
        -H 'Content-type: application/json' \
        -d "{\"text\": $message}" \
        --max-time 10 \
        >/dev/null 2>&1
}

# === EMAIL (via sendmail o msmtp) ===

send_email_alert() {
    local subject="$1"
    local body="$2"
    local recipient="$3"

    echo -e "Subject: [LOG ALERT] $subject\n\n$body" | \
        /usr/sbin/sendmail "$recipient"
}

# === SYSLOG → ALERTING PIPELINE ===
# rsyslog può inoltrare pattern critici direttamente a uno script

# /etc/rsyslog.d/80-alerts.conf
module(load="omprog")

if $syslogseverity <= 2 then {
    action(type="omprog"
        binary="/usr/local/bin/critical-alert.sh"
        template="RSYSLOG_TraditionalFileFormat"
    )
}

# Script /usr/local/bin/critical-alert.sh
#!/bin/bash
while IFS= read -r line; do
    # Ogni riga è un messaggio syslog con severity crit/alert/emerg
    curl -s -X POST "$WEBHOOK_URL" \
        -H 'Content-type: application/json' \
        -d "{\"text\":\"CRITICAL: $line\"}" \
        --max-time 5 \
        >/dev/null 2>&1
done
```

---

## Policy di Retention dei Log

### Requisiti regolamentari

| Regolamento | Retention minima | Cosa loggare | Note |
|-------------|-----------------|--------------|------|
| **GDPR** | Non specificata (principio di minimizzazione) | Accessi a dati personali, consensi, trasferimenti | Diritto alla cancellazione si applica anche ai log |
| **PCI-DSS** | 1 anno (3 mesi online) | Accessi a dati carta, autenticazione, azioni admin | Req. 10: audit trail per tutti gli accessi |
| **SOX** | 7 anni | Transazioni finanziarie, modifiche ai sistemi contabili | Integrità log obbligatoria |
| **HIPAA** | 6 anni | Accessi a dati sanitari (PHI), modifiche, trasmissioni | Business Associate Agreement copre i log |
| **SOC 2** | 1 anno | Tutti gli eventi di sicurezza, accessi, modifiche | Type II richiede monitoraggio continuo |
| **ISO 27001** | Definito nel ISMS | Eventi di sicurezza, accessi, modifiche | A.12.4 richiede logging e monitoring |
| **NIS2** | Non specificata (adeguata al rischio) | Incidenti, vulnerabilità, misure di sicurezza | Obbligo di notifica entro 24h |

### GDPR e log

```bash
# Il GDPR richiede:
# 1. Minimizzazione: loggare solo ciò che è necessario
# 2. Finalità: i log devono servire a scopi legittimi (sicurezza, debug)
# 3. Retention limitata: non conservare log oltre il necessario
# 4. Diritto alla cancellazione: se i log contengono dati personali,
#    il soggetto può richiederne la cancellazione

# Strategia pratica:
# - Anonimizzare IP nei log web (ultimi 2 ottetti)
# - Non loggare dati personali non necessari
# - Rotation a 90 giorni per log applicativi
# - Retention di 1 anno per log di sicurezza/audit
# - Documentare nel registro dei trattamenti

# rsyslog: anonimizzazione IP automatica
module(load="mmanon")
action(type="mmanon" ipv4.bits="16" ipv4.mode="random-consistent")

# logrotate: retention limitata
/var/log/webapp/*.log {
    daily
    rotate 90
    maxage 90          # Rimuovi file > 90 giorni
    compress
}
```

### PCI-DSS e log

```bash
# PCI-DSS Requirement 10 richiede:

# 10.2.1: Log di tutti gli accessi individuali ai dati dei titolari di carta
# 10.2.2: Tutte le azioni di chiunque con privilegi root/admin
# 10.2.3: Accesso a tutti gli audit trail
# 10.2.4: Tentativi di accesso logico non validi
# 10.2.5: Uso e modifiche dei meccanismi di identificazione e autenticazione
# 10.2.6: Inizializzazione, arresto o pausa dei log di audit
# 10.2.7: Creazione e cancellazione di oggetti a livello di sistema

# 10.5: Proteggere gli audit trail dall'alterazione
# - Separazione dei ruoli (chi genera vs chi gestisce i log)
# - Integrità dei file di log (checksums, WORM storage)
# - Centralizzazione su server dedicato

# 10.7: Conservare l'audit trail per almeno un anno,
#        con un minimo di tre mesi immediatamente disponibili per l'analisi

# Implementazione pratica:
# Rotazione: logrotate mantiene 90 giorni locali
# Archiviazione: script muove file compressi in storage a lungo termine
# Centralizzazione: rsyslog/ELK con retention 1 anno

#!/bin/bash
# /usr/local/bin/archive-logs.sh — eseguire mensilmente
ARCHIVE_DIR="/backup/logs/archive"
YEAR=$(date +%Y)
MONTH=$(date +%m)

# Comprimere e archiviare
mkdir -p "$ARCHIVE_DIR/$YEAR/$MONTH"
find /var/log/remote/ -name "*.gz" -mtime +90 -exec mv {} "$ARCHIVE_DIR/$YEAR/$MONTH/" \;

# Calcolare checksum per integrità
find "$ARCHIVE_DIR/$YEAR/$MONTH/" -type f -exec sha256sum {} \; > "$ARCHIVE_DIR/$YEAR/$MONTH/CHECKSUMS.sha256"
```

### Ottimizzazione dello storage

```bash
# === COMPRESSIONE ===
# Rapporto di compressione tipico per log di testo:
# gzip -6:   ~90% riduzione (default logrotate)
# gzip -9:   ~92% riduzione
# zstd -19:  ~95% riduzione (più veloce di gzip in decompressione)
# xz -9:     ~96% riduzione (più lento)

# Esempio: 1 GB di log → ~100 MB con gzip, ~50 MB con zstd -19

# === TIERED STORAGE ===
# Hot (SSD, locale):     7 giorni, accesso immediato
# Warm (HDD, locale):    30-90 giorni, accesso veloce
# Cold (NAS/S3):         1-7 anni, accesso lento
# Frozen (tape/Glacier): 7+ anni, accesso molto lento

# === JOURNALD: controllo dimensione ===
# In /etc/systemd/journald.conf:
# SystemMaxUse=4G          # Limite assoluto
# SystemKeepFree=2G        # Spazio minimo libero
# MaxRetentionSec=6month   # Retention massima

# Pulizia manuale
journalctl --vacuum-size=2G
journalctl --vacuum-time=90d

# === MONITORARE L'USO DISCO ===
du -sh /var/log/* | sort -rh | head -20
journalctl --disk-usage
df -h /var/log
```

---

## Logging Orientato alla Sicurezza

### Login falliti e brute force

```bash
# Monitorare login SSH falliti
journalctl -u sshd --since "1 hour ago" | grep "Failed password"

# Contare per IP
journalctl -u sshd --since today | grep "Failed password" | \
    awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -20

# Contare per utente
journalctl -u sshd --since today | grep "Failed password" | \
    awk '{print $9}' | sort | uniq -c | sort -rn | head -20

# Login riusciti dopo tentativi falliti (potenziale brute force riuscito)
grep "Accepted password" /var/log/auth.log | awk '{print $9, $11}' | sort -u

# Ultimo login per tutti gli utenti
lastlog

# Login recenti (wtmp)
last -20

# Login falliti recenti (btmp)
sudo lastb -20

# Account lockout (pam_faillock)
faillock --user username

# File utili per analisi:
# /var/log/auth.log (Debian) o /var/log/secure (RHEL)
# /var/log/btmp (login falliti, binario — leggere con lastb)
# /var/log/wtmp (login riusciti, binario — leggere con last)
# /var/log/faillog (fallimenti, binario — leggere con faillog)
```

### Monitoraggio sudo

```bash
# Tutti i comandi sudo eseguiti
grep "COMMAND=" /var/log/auth.log

# Sudo falliti
grep "NOT" /var/log/auth.log | grep sudo

# Sudo per utente
grep "sudo:" /var/log/auth.log | awk '{print $6}' | sort | uniq -c | sort -rn

# Top comandi sudo
grep "COMMAND=" /var/log/auth.log | sed 's/.*COMMAND=//' | sort | uniq -c | sort -rn | head -20

# Sudo con journalctl
journalctl _COMM=sudo --since today

# Configurare logging dettagliato di sudo
# In /etc/sudoers o /etc/sudoers.d/:
# Defaults log_input, log_output
# Defaults iolog_dir="/var/log/sudo-io/%{user}"

# auditd per sudo
# -w /usr/bin/sudo -p x -k sudo_exec
# -w /etc/sudoers -p wa -k sudo_config
```

### Accesso ai file sensibili

```bash
# auditd: monitorare accesso a file critici
sudo auditctl -w /etc/passwd -p rwa -k passwd_access
sudo auditctl -w /etc/shadow -p rwa -k shadow_access
sudo auditctl -w /etc/ssh/ -p rwa -k ssh_config
sudo auditctl -w /root/.ssh/ -p rwa -k root_ssh
sudo auditctl -w /home/ -p rwa -k home_access

# Cercare accessi registrati
sudo ausearch -k passwd_access -i
sudo ausearch -k shadow_access -ts today -i

# inotifywait: monitoraggio in tempo reale (non persistente)
sudo apt install inotify-tools
inotifywait -m -r -e access,modify,create,delete /etc/ssh/ &

# Monitorare con journalctl (se auditd è integrato con journal)
journalctl _TRANSPORT=audit AUDIT_FIELD_KEY=shadow_access
```

### Connessioni di rete

```bash
# Log connessioni con iptables/nftables
# iptables: loggare connessioni droppate
sudo iptables -A INPUT -j LOG --log-prefix "IPT_DROP: " --log-level 4
# I messaggi vanno in kern.log

# Analizzare le connessioni droppate
grep "IPT_DROP" /var/log/kern.log | \
    awk '{for(i=1;i<=NF;i++) if($i ~ /SRC=/) print $i}' | \
    sort | uniq -c | sort -rn | head -20

# nftables: loggare
# nft add rule inet filter input counter log prefix "NFT_DROP: " drop

# conntrack: connessioni attive
sudo conntrack -L | awk '{print $4}' | sort | uniq -c | sort -rn

# ss/netstat: snapshot connessioni
ss -tunapl | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn

# auditd: monitorare connessioni di rete
# -a always,exit -F arch=b64 -S connect -k network_connect
# -a always,exit -F arch=b64 -S accept -k network_accept
# -a always,exit -F arch=b64 -S bind -k network_bind
```

### Integrità dei log

```bash
# === PROTEZIONE BASE ===

# Attributo append-only (immutable append)
sudo chattr +a /var/log/auth.log
sudo chattr +a /var/log/audit/audit.log
# Ora il file può solo ricevere append, non essere troncato/cancellato
# Per rimuovere: chattr -a (richiede root)
# Attenzione: logrotate potrebbe non funzionare con +a

# === JOURNALD FORWARD SECURE SEALING ===
# Protegge i journal dall'alterazione retroattiva

# Setup chiavi
sudo journalctl --setup-keys
# Output:
# New keys have been generated...
# QR code for verification key:
# [QR code]
# Verification key: abc123-def456-...
# SALVARE LA VERIFICATION KEY OFFLINE

# Verificare integrità
journalctl --verify-key=abc123-def456-...

# === CHECKSUMS ===
# Calcolare hash dei log prima dell'archiviazione
find /var/log/ -name "*.gz" -exec sha256sum {} \; > /var/log/checksums-$(date +%F).sha256

# Verificare
sha256sum -c /var/log/checksums-2026-05-22.sha256

# === CENTRALIZZAZIONE COME PROTEZIONE ===
# Log su server remoto non sono modificabili dall'host compromesso
# Usare rsyslog con TLS e RELP per garanzia di consegna
# Il server di log deve essere hardened e accessibile solo da admin dedicati
```

---

## Troubleshooting

**"Disco pieno per i log"** → `du -sh /var/log/* | sort -rh | head` per identificare il colpevole. `journalctl --vacuum-size=500M` per journald. Verificare logrotate: `cat /var/lib/logrotate/status`. Forzare rotazione: `logrotate -f /etc/logrotate.d/colpevole`. Lungo termine: rivedere la retention policy e il livello di log dei servizi verbosi.

**"Log non vengono scritti"** → Verificare: rsyslog attivo? `systemctl status rsyslog`. journald attivo? `systemctl status systemd-journald`. Permessi sulla directory? `ls -la /var/log/`. Disco pieno? `df -h /var`. SELinux/AppArmor bloccano? `ausearch -m AVC -ts recent`.

**"Log remoti non arrivano al server"** → (1) Firewall: porta 514 (UDP/TCP) aperta? `ss -tuln | grep 514`. (2) rsyslog sul server ha i moduli imudp/imtcp caricati? `rsyslogd -N1`. (3) Il client sta effettivamente inviando? `tcpdump -i eth0 port 514` sul server. (4) SELinux/AppArmor bloccano? (5) DNS risolve il nome del server? (6) TLS: i certificati sono validi e corrispondono?

**"logrotate non ruota"** → `logrotate -d /etc/logrotate.d/service` per dry run. Errori comuni: path sbagliato nel file config, wildcard che non matcha, script postrotate che fallisce, file di stato corrotto (`/var/lib/logrotate/status` — rinominare e riavviare). Permessi insufficienti? Usare `su <user> <group>` nella config.

**"journalctl mostra solo il boot corrente"** → Storage non persistente. Verificare: `ls /var/log/journal/`. Se non esiste: `mkdir -p /var/log/journal && systemd-tmpfiles --create --prefix /var/log/journal`. Impostare `Storage=persistent` in `/etc/systemd/journald.conf` e riavviare journald.

**"journald usa troppo disco"** → Controllare: `journalctl --disk-usage`. Impostare limiti in `/etc/systemd/journald.conf`: `SystemMaxUse=2G`, `SystemKeepFree=1G`. Pulizia immediata: `journalctl --vacuum-size=1G` o `journalctl --vacuum-time=30d`. Verificare se qualche servizio è eccessivamente verboso: `journalctl --since today -o short-monotonic | awk '{print $5}' | sort | uniq -c | sort -rn | head`.

**"Messaggio 'Suppressed N messages'"** → Rate limiting di journald attivo. Un servizio sta generando troppi messaggi. Identificare: guardare quale unit è menzionata. Soluzione: (1) Risolvere il root cause (il servizio è in errore loop). (2) Aumentare i limiti solo se necessario: `RateLimitIntervalSec=60s`, `RateLimitBurst=20000` in journald.conf. (3) Per un singolo servizio: `LogRateLimitIntervalSec=` e `LogRateLimitBurst=` nella unit override.

**"rsyslog perde messaggi sotto carico"** → Verificare `rsyslogd -N1` per errori. Controllare le code: aumentare `queue.size`, usare `queue.type="LinkedList"` con disk-assisted backup. Se il problema è l'output: usare `action.resumeRetryCount="-1"` e `action.resumeInterval="30"`. Verificare: `tail -f /var/log/syslog | grep rsyslog` per messaggi di warning/error interni.

**"Timestamp dei log errati o inconsistenti"** → (1) NTP configurato? `timedatectl status`. (2) Timezone corretta? `timedatectl set-timezone Europe/Rome`. (3) Per log remoti: il client e il server hanno orari sincronizzati? (4) In rsyslog, usare `preserveFQDN="on"` e template con `date-rfc3339` per timestamp precisi. (5) journalctl mostra UTC di default: usare `journalctl --utc` o `--output-fields=__REALTIME_TIMESTAMP`.

**"Log di un servizio mancanti in journalctl"** → (1) Il servizio usa syslog direttamente e non stdout/stderr? Controllare `StandardOutput=` e `StandardError=` nella unit. (2) Il servizio scrive in un file proprio? Controllare la configurazione dell'applicazione. (3) Il servizio gira in un namespace di mount? (4) Il servizio ha un `LogNamespace=` configurato?

**"rsyslog non si avvia dopo modifica configurazione"** → `rsyslogd -N1` per trovare l'errore di sintassi. Errori comuni: parentesi mancante in RainerScript, modulo non installato (`omrelp`, `omelasticsearch`), path del certificato TLS errato, porta già in uso (`ss -tuln | grep <porta>`).

**"auditd genera troppi log"** → (1) Regole troppo ampie, soprattutto `execve` su tutto: restringere con `-F auid>=1000` per escludere servizi di sistema. (2) Verificare: `aureport -x --summary` per capire quali comandi generano più eventi. (3) Escludere path specifici: `-a never,exit -F dir=/var/cache -k exclude_cache`. (4) Regola mai/exit deve venire PRIMA della regola always/exit corrispondente.

**"Journal corrotto, journalctl mostra errori"** → `journalctl --verify` per identificare file corrotti. File corrotti: `mv /var/log/journal/<machine-id>/system@<corrupt>.journal /tmp/corrupt-journals/`. Riavviare journald: `systemctl restart systemd-journald`. I file validi rimangono accessibili. Se tutto il journal è corrotto: `rm -rf /var/log/journal/<machine-id>/*` (perde tutti i log storici), riavviare journald.

**"Log flooding da un singolo servizio"** → (1) Identificare il servizio: `journalctl --since "5 min ago" | awk '{print $5}' | sort | uniq -c | sort -rn | head -5`. (2) Rate limiting per unit: aggiungere `LogRateLimitIntervalSec=30s` e `LogRateLimitBurst=1000` alla sezione `[Service]` della unit. (3) Cambiare log level dell'applicazione a WARNING/ERROR. (4) Se è un loop di errore: risolvere il bug/misconfiguration che causa il loop.

**"Log persi durante il reboot"** → journald con `Storage=volatile` scrive in `/run/log/journal/` che è tmpfs (perso al reboot). Soluzione: `Storage=persistent` + `mkdir -p /var/log/journal`. Per rsyslog: se la coda (`queue.saveonshutdown="on"`) non era configurata, i messaggi in transito sono persi.

**"Impossibile leggere log remoti con formati diversi"** → Standardizzare il formato di invio. Su tutti i client rsyslog usare lo stesso template. Per syslog-ng, definire un template uniforme. Se i formati variano: usare Logstash/Fluentd come normalizzatore prima di Elasticsearch. Parser grok in Logstash per formati multipli.

---

## FAQ

**D1: Devo usare journald o rsyslog (o entrambi)?**
Entrambi. journald è il collettore primario su sistemi con systemd: cattura stdout/stderr delle unit, messaggi kernel, e offre query strutturate veloci. rsyslog è essenziale per: inoltro a server remoti, scrittura su file di testo (necessari per tool legacy), filtraggio avanzato, output verso Elasticsearch e altri backend. La configurazione predefinita su Debian/Ubuntu e RHEL usa entrambi in tandem.

**D2: Come ridurre l'uso disco dei log senza perdere dati importanti?**
Strategia a livelli: (1) Abbassare il log level dei servizi verbosi (da DEBUG a INFO). (2) Comprimere con logrotate (`compress`, preferibilmente `zstd`). (3) Impostare `SystemMaxUse` in journald.conf. (4) Archiviare log vecchi su storage economico (NAS, S3). (5) Centralizzare: i log locali possono avere retention breve se quelli centralizzati hanno retention lunga. (6) Non loggare dati inutili (health check ogni secondo, richieste 200 OK con nessun valore).

**D3: Come garantire che nessun log venga perso nel forwarding remoto?**
Usare RELP (Reliable Event Logging Protocol) tra rsyslog client e server: ha ack a livello applicativo. In alternativa, TCP con disk-assisted queue (`queue.type="LinkedList"`, `queue.filename=...`, `queue.maxdiskspace="2g"`, `queue.saveonshutdown="on"`, `action.resumeRetryCount="-1"`). Il disk buffer preserva i messaggi durante i periodi di disconnessione.

**D4: È meglio Elasticsearch/ELK o Loki/Grafana per i log?**
Dipende. ELK/OpenSearch: full-text search potente, dashboard ricche, ecosistema maturo, ma richiede molte risorse (RAM, disco SSD). Loki/Grafana: leggero, label-based (non indicizza il testo completo), ideale se hai già Grafana/Prometheus, costi storage molto più bassi. Regola: se cerchi spesso nel testo dei log → ELK. Se filtri principalmente per servizio/host/livello → Loki.

**D5: Come loggare in formato JSON con rsyslog?**
Usare un template di tipo `list` che costruisce JSON:
```
template(name="JsonLog" type="list") {
    constant(value="{\"ts\":\"") property(name="timegenerated" dateFormat="rfc3339")
    constant(value="\",\"host\":\"") property(name="hostname")
    constant(value="\",\"msg\":\"") property(name="msg" format="jsonf")
    constant(value="\"}\n")
}
```
Per parsare JSON in ingresso: `module(load="mmjsonparse")` e `action(type="mmjsonparse")`.

**D6: Quanto influiscono i log sulle performance del sistema?**
Con configurazione corretta, l'impatto è minimo (<1-2% CPU). Fattori critici: (1) I/O sincrono vs asincrono — usare il trattino (`-/var/log/messages`) per log non critici. (2) Rate limiting — journald limita automaticamente. (3) Log level — DEBUG in produzione può generare 10-100x il volume di INFO. (4) Compressione journald — riduce I/O. Problema reale: il log flooding di un servizio in errore loop può saturare I/O e CPU.

**D7: Come implementare la retention log per il GDPR?**
(1) Documentare la finalità del logging nel registro dei trattamenti. (2) Anonimizzare dati personali nei log dove possibile (IP, email). (3) Definire retention proporzionale: 7 giorni per debug, 90 giorni per applicativi, 1 anno per audit/sicurezza. (4) Automatizzare la cancellazione con logrotate `maxage`. (5) Se un utente esercita il diritto alla cancellazione, i log con dati personali devono essere gestiti (possibile eccezione per log di sicurezza, documentare la base giuridica).

**D8: auditd e journald sono la stessa cosa? Si sovrappongono?**
No, sono sistemi distinti. auditd opera a livello kernel, monitora syscall, accessi a file e network con regole granulari, ed è richiesto dai framework di compliance (PCI-DSS, STIG, CIS). journald raccoglie log applicativi/servizi da syslog, stdout/stderr delle unit systemd. Si sovrappongono solo per i messaggi del kernel. In ambienti regulated, servono entrambi.

**D9: Come proteggere i log dalla cancellazione da parte di un attaccante?**
(1) Centralizzare su server remoto dedicato — l'attaccante dovrebbe compromettere anche quello. (2) `chattr +a` sui file di log critici locali. (3) Forward Secure Sealing di journald (rileva alterazioni). (4) WORM storage per archivio (S3 Object Lock, tape). (5) Separazione dei ruoli: gli admin dei server non devono avere accesso al log server. (6) Monitorare l'accesso ai log stessi con auditd.

**D10: Posso usare syslog-ng e rsyslog insieme sullo stesso host?**
Tecnicamente possibile ma sconsigliato. Entrambi ascoltano su `/dev/log` e competono per i messaggi. Se necessario: (1) Usarne uno come primario su `/dev/log`. (2) L'altro legge da un socket dedicato o via rete. (3) In pratica, scegliere l'uno o l'altro. Non c'è vantaggio a usarli entrambi.

**D11: Come diagnosticare che logrotate non sta funzionando?**
(1) `logrotate -d /etc/logrotate.d/<file>` — dry run, mostra cosa farebbe. (2) `cat /var/lib/logrotate/status` — ultima rotazione per ogni file. (3) `systemctl status logrotate.timer` — il timer è attivo? (4) `journalctl -u logrotate.service` — errori nelle esecuzioni recenti. (5) Errori comuni: path errato, wildcard che non matcha file, `su` mancante quando la directory ha owner diverso, script postrotate che fallisce.

**D12: Come gestire i log di container Docker?**
Docker scrive log in `/var/lib/docker/containers/<id>/<id>-json.log` di default. Opzioni: (1) Configurare il log driver: `--log-driver=journald` per integrare con journald. (2) `--log-driver=syslog` per inviare a rsyslog/syslog-ng. (3) `--log-opt max-size=50m --log-opt max-file=5` per limitare la dimensione. (4) Per Kubernetes: fluentd/fluent-bit come DaemonSet raccoglie log da stdout dei container.

**D13: Qual è la differenza tra `@` e `@@` in rsyslog?**
`@` = invio via UDP (singolo tentativo, nessuna garanzia di consegna). `@@` = invio via TCP (connessione persistente, retry automatico). UDP è più leggero ma perde messaggi sotto carico o se il server è down. TCP è raccomandato per production. Per la massima affidabilità: usare RELP (`omrelp`), che aggiunge acknowledgement a livello applicativo sopra TCP.

**D14: Come correlare eventi tra log di servizi diversi?**
(1) Correlation ID: generare un UUID all'ingresso nel sistema, propagarlo via header HTTP, includerlo in ogni riga di log. Query: `journalctl REQUEST_ID=abc-123` o ricerca in Elasticsearch. (2) Timestamp preciso: usare `dateFormat="rfc3339"` con microsecondi per ordinare eventi cross-servizio. (3) In Elasticsearch: query per range temporale + campo host + messaggio. (4) Per architetture a microservizi: implementare distributed tracing (OpenTelemetry).

**D15: Come evitare che un crash dump riempia il disco?**
(1) Configurare kdump per salvare su partizione dedicata o server remoto. (2) `makedumpfile -d 31` per salvare solo la memoria utile (esclude pagine libere, cache). (3) Impostare `MaxRetentionSec=` in kdump.conf. (4) Monitorare lo spazio in `/var/crash/`. (5) Su sistemi con molta RAM, il dump completo può essere enorme: usare compressione e filtraggio.

**D16: Come migrare da rsyslog a syslog-ng (o viceversa)?**
(1) Installare il nuovo demone senza rimuovere il vecchio. (2) Tradurre la configurazione (le regole facility.severity sono simili, i template differiscono). (3) Far girare entrambi in parallelo, con il nuovo che scrive in una directory di test. (4) Verificare che tutti i log attesi arrivino. (5) Aggiornare i file logrotate. (6) Fermare il vecchio demone e configurare il nuovo come primario. (7) Aggiornare i client remoti se applicabile.

**D17: Perché i miei log hanno timestamp in UTC e non in ora locale?**
journalctl mostra timestamp in locale di default, ma `journalctl --utc` forza UTC. rsyslog usa il timestamp del messaggio: se il client invia in UTC e il server è in un altro fuso, i log mostreranno UTC. Soluzioni: (1) `timedatectl set-timezone Europe/Rome` su tutti i server. (2) In rsyslog, il template `%timegenerated%` usa l'ora del sistema ricevente. (3) Standardizzare su UTC nei log centralizzati e convertire solo nella visualizzazione (Kibana, Grafana).

---

## Guida Implementativa: Logging Centralizzato da Zero

Questa guida copre l'implementazione passo-passo di un'infrastruttura di logging centralizzato per un ambiente con 10-100 server.

### Fase 1: Pianificazione

```
Requisiti da definire:
1. Volume stimato: N server × messaggi/giorno × dimensione media
   Esempio: 50 server × 100k messaggi/giorno × 500 byte = ~2.5 GB/giorno
2. Retention: 90 giorni online + 1 anno archivio
3. Storage: 2.5 GB/giorno × 90 giorni × 0.1 (compressione) = ~22.5 GB + overhead indici
4. Query: ricerca full-text o solo per label? → determina ELK vs Loki
5. Alerting: quali eventi richiedono notifica?
6. Compliance: GDPR, PCI-DSS, SOC2?
7. Disponibilità: singolo server o cluster?
```

### Fase 2: Setup del server di log

```bash
# ===== Opzione A: rsyslog come server centralizzato =====

# 1. Server dedicato, hardened
# - Disco dedicato per /var/log/remote (RAID 1 o 10)
# - Accesso limitato (solo admin log, non admin applicativi)

# 2. Installare rsyslog con moduli
sudo apt install rsyslog rsyslog-gnutls rsyslog-relp

# 3. Generare certificati TLS
# (usare una CA interna, non self-signed in produzione)
mkdir -p /etc/rsyslog.d/certs/
# Copiare ca.pem, server-cert.pem, server-key.pem

# 4. Configurazione server
cat > /etc/rsyslog.d/10-server.conf << 'RSYSEOF'
# Moduli
module(load="imtcp"
    StreamDriver.Name="gtls"
    StreamDriver.Mode="1"
    StreamDriver.AuthMode="x509/name"
)
module(load="imrelp" tls="on")

# Certificati
global(
    defaultNetstreamDriverCAFile="/etc/rsyslog.d/certs/ca.pem"
    defaultNetstreamDriverCertFile="/etc/rsyslog.d/certs/server-cert.pem"
    defaultNetstreamDriverKeyFile="/etc/rsyslog.d/certs/server-key.pem"
    defaultNetstreamDriver="gtls"
    workDirectory="/var/spool/rsyslog"
    maxMessageSize="64k"
)

# Input TLS TCP
input(type="imtcp" port="6514" ruleset="remote")

# Input RELP (più affidabile)
input(type="imrelp" port="2514" ruleset="remote"
    tls="on"
    tls.caCert="/etc/rsyslog.d/certs/ca.pem"
    tls.myCert="/etc/rsyslog.d/certs/server-cert.pem"
    tls.myPrivKey="/etc/rsyslog.d/certs/server-key.pem"
)

# Template per file per host
template(name="PerHostFile" type="string"
    string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log"
)

template(name="PerHostDaily" type="string"
    string="/var/log/remote/%HOSTNAME%/%$year%-%$month%-%$day%.log"
)

# Template JSON per analisi
template(name="JsonRemote" type="list") {
    constant(value="{\"@timestamp\":\"")
    property(name="timegenerated" dateFormat="rfc3339")
    constant(value="\",\"host\":\"")
    property(name="hostname")
    constant(value="\",\"facility\":\"")
    property(name="syslogfacility-text")
    constant(value="\",\"severity\":\"")
    property(name="syslogseverity-text")
    constant(value="\",\"program\":\"")
    property(name="programname")
    constant(value="\",\"message\":\"")
    property(name="msg" format="jsonf")
    constant(value="\"}\n")
}

# Ruleset per messaggi remoti
ruleset(name="remote") {
    # File per host e programma
    action(type="omfile"
        dynaFile="PerHostFile"
        dirCreateMode="0755"
        fileCreateMode="0640"
        dirOwner="syslog"
        dirGroup="adm"
    )

    # File JSON aggregato (per import in Elasticsearch)
    action(type="omfile"
        file="/var/log/remote/all-json.log"
        template="JsonRemote"
    )
}
RSYSEOF

# 5. Creare directory e impostare permessi
sudo mkdir -p /var/log/remote
sudo chown syslog:adm /var/log/remote
sudo mkdir -p /var/spool/rsyslog

# 6. Verificare e avviare
sudo rsyslogd -N1
sudo systemctl restart rsyslog
```

### Fase 3: Configurazione dei client

```bash
# Su ogni server client:

# 1. Installare moduli rsyslog
sudo apt install rsyslog rsyslog-gnutls rsyslog-relp

# 2. Copiare certificati
sudo mkdir -p /etc/rsyslog.d/certs/
# Copiare ca.pem, client-cert.pem, client-key.pem

# 3. Configurare forwarding
cat > /etc/rsyslog.d/90-forward.conf << 'RSYSEOF'
global(
    defaultNetstreamDriverCAFile="/etc/rsyslog.d/certs/ca.pem"
    defaultNetstreamDriverCertFile="/etc/rsyslog.d/certs/client-cert.pem"
    defaultNetstreamDriverKeyFile="/etc/rsyslog.d/certs/client-key.pem"
    defaultNetstreamDriver="gtls"
)

# Invia tutto via RELP con TLS
module(load="omrelp")
*.* action(type="omrelp"
    target="logserver.example.com"
    port="2514"
    tls="on"
    tls.caCert="/etc/rsyslog.d/certs/ca.pem"
    tls.myCert="/etc/rsyslog.d/certs/client-cert.pem"
    tls.myPrivKey="/etc/rsyslog.d/certs/client-key.pem"
    queue.type="LinkedList"
    queue.filename="fwdToLogServer"
    queue.maxdiskspace="1g"
    queue.saveonshutdown="on"
    action.resumeRetryCount="-1"
    action.resumeInterval="30"
)
RSYSEOF

# 4. Verificare e avviare
sudo rsyslogd -N1
sudo systemctl restart rsyslog

# 5. Test
logger -p auth.err "Test log centralizzato da $(hostname)"
```

### Fase 4: Logrotate per i log remoti

```bash
# Sul server di log: /etc/logrotate.d/remote-logs
/var/log/remote/*/*.log {
    daily
    rotate 90
    compress
    compresscmd /usr/bin/zstd
    compressext .zst
    compressoptions -19
    uncompresscmd /usr/bin/unzstd
    delaycompress
    missingok
    notifempty
    create 0640 syslog adm
    sharedscripts
    postrotate
        /usr/lib/rsyslog/rsyslog-rotate
    endscript
    lastaction
        # Archiviare log > 90 giorni su storage a lungo termine
        find /var/log/remote/ -name "*.zst" -mtime +90 \
            -exec mv {} /backup/logs/archive/ \;
    endscript
}
```

### Fase 5: Aggiungere Elasticsearch e Kibana (opzionale)

```bash
# Sul server di log, aggiungere output a Elasticsearch

# 1. Installare il modulo
sudo apt install rsyslog-elasticsearch

# 2. Aggiungere alla configurazione
cat >> /etc/rsyslog.d/10-server.conf << 'RSYSEOF'

# Output a Elasticsearch
module(load="omelasticsearch")

template(name="ESIndex" type="string" string="syslog-%$year%.%$month%.%$day%")

ruleset(name="remote") {
    # ... (regole precedenti) ...

    # Invio a Elasticsearch
    action(type="omelasticsearch"
        server="localhost"
        serverport="9200"
        searchIndex="ESIndex"
        dynSearchIndex="on"
        searchType="_doc"
        template="JsonRemote"
        bulkmode="on"
        queue.type="LinkedList"
        queue.filename="esQueue"
        queue.maxdiskspace="2g"
        queue.saveonshutdown="on"
        action.resumeRetryCount="-1"
        action.resumeInterval="30"
    )
}
RSYSEOF

# 3. Installare Elasticsearch e Kibana
# (vedi documentazione ufficiale per la versione corrente)
# Elasticsearch: porta 9200
# Kibana: porta 5601

# 4. Configurare Index Lifecycle Management (ILM) in Elasticsearch
# per gestire la retention automaticamente:
# - Hot: 7 giorni (SSD)
# - Warm: 30 giorni (HDD)
# - Cold: 90 giorni (storage economico)
# - Delete: dopo 1 anno
```

### Fase 6: Monitoring e alerting

```bash
# Monitorare l'infrastruttura di logging stessa

# 1. Spazio disco sul log server
cat > /usr/local/bin/check-log-storage.sh << 'SCRIPTEOF'
#!/bin/bash
USAGE=$(df /var/log/remote --output=pcent | tail -1 | tr -d ' %')
if [ "$USAGE" -gt 85 ]; then
    echo "Log storage at ${USAGE}% — cleanup needed" | \
        logger -p local0.warning -t log-monitor
fi
SCRIPTEOF
chmod +x /usr/local/bin/check-log-storage.sh

# 2. Verificare che tutti i client stanno inviando log
cat > /usr/local/bin/check-log-freshness.sh << 'SCRIPTEOF'
#!/bin/bash
EXPECTED_HOSTS="web01 web02 db01 app01 app02"
for host in $EXPECTED_HOSTS; do
    LAST_LOG=$(find /var/log/remote/$host/ -type f -printf '%T@\n' 2>/dev/null | sort -rn | head -1)
    if [ -z "$LAST_LOG" ]; then
        echo "No logs from $host" | logger -p local0.warning -t log-monitor
        continue
    fi
    NOW=$(date +%s)
    AGE=$(echo "$NOW - ${LAST_LOG%.*}" | bc)
    if [ "$AGE" -gt 3600 ]; then
        echo "Stale logs from $host (${AGE}s old)" | logger -p local0.warning -t log-monitor
    fi
done
SCRIPTEOF
chmod +x /usr/local/bin/check-log-freshness.sh

# 3. Cron jobs
# */30 * * * * /usr/local/bin/check-log-storage.sh
# */15 * * * * /usr/local/bin/check-log-freshness.sh
```

### Fase 7: Verifica e test

```bash
# 1. Verificare la catena completa

# Sul client:
logger -p auth.err "VERIFICATION-TEST-$(date +%s) from $(hostname)"

# Sul server, entro 30 secondi:
grep "VERIFICATION-TEST" /var/log/remote/$(hostname)/auth.log

# In Elasticsearch (se configurato):
curl -s "http://localhost:9200/syslog-*/_search?q=VERIFICATION-TEST" | jq '.hits.hits[0]'

# 2. Test di resilienza

# Fermare rsyslog sul server → i client devono bufferizzare su disco
sudo systemctl stop rsyslog  # Sul server
# Sul client: i messaggi vanno nella disk queue
logger "Test during server down"
# Riavviare il server → i messaggi bufferizzati devono arrivare
sudo systemctl start rsyslog  # Sul server
sleep 60
grep "Test during server down" /var/log/remote/*/syslog.log

# 3. Test di carico
# Generare 10000 messaggi e verificare che arrivino tutti
for i in $(seq 1 10000); do
    logger -p local0.info "LOAD-TEST-$i"
done
sleep 120
grep -c "LOAD-TEST" /var/log/remote/$(hostname)/local0.log
# Deve mostrare 10000
```

---

## Best Practices Finali

1. **Centralizzare i log**: su ambienti con più server, inviare i log a un sistema centralizzato (ELK, Loki, Graylog). I log solo locali possono essere cancellati da un attaccante.

2. **Retention policy**: definire per quanto tempo mantenere i log. Compliance può richiedere 1-7 anni. logrotate per rotazione, archivio per retention lunga.

3. **Log strutturati**: dove possibile, loggare in formato JSON. Facilita parsing, query e analisi. journald è già strutturato.

4. **Separare per servizio**: ogni servizio ha il suo file di log. Non mischiare tutto in syslog.

5. **Monitorare lo spazio**: i log possono riempire il disco rapidamente. Alarm su `/var/log` > 80%. `journalctl --disk-usage` per journald.

6. **Non loggare dati sensibili**: password, token, numeri di carta NON devono finire nei log. Sanificare prima di loggare.

7. **Alert sui pattern critici**: configurare alert per: login falliti ripetuti, errori kernel, servizi che crashano, disk full.

8. **TLS per log remoti**: mai inviare log in chiaro su rete non trusted. Usare TLS con certificati verificati. RELP per garanzia di consegna.

9. **Timezone e NTP**: sincronizzare l'orario con NTP su tutti i server. Timestamp inconsistenti rendono impossibile la correlazione.

10. **Immutabilità dei log**: usare `chattr +a`, Forward Secure Sealing, WORM storage per proteggere i log dalla manomissione.

11. **Rate limiting**: configurare rate limiting a tutti i livelli (journald, rsyslog, applicazione) per prevenire log flooding che può causare denial of service.

12. **Test dell'infrastruttura di logging**: verificare periodicamente che i log arrivino al server centralizzato, che logrotate funzioni, che gli alert si attivino. Un sistema di logging silenziosamente rotto è peggio di non averne uno.

13. **Documentare**: mappare quale servizio logga dove, con quale formato, quale retention, chi ha accesso. Senza documentazione, l'infrastruttura di logging diventa tech debt.

14. **Separazione dei ruoli**: gli amministratori dei server applicativi non dovrebbero poter cancellare o modificare i log sul server centralizzato.

15. **Audit dell'audit**: monitorare l'accesso ai log stessi con auditd. Chi legge i log? Chi li cancella? Questo è un requisito di compliance comune.

16. **Log level dinamico**: progettare le applicazioni per cambiare log level a runtime (es. via API, signal, file di configurazione) senza restart. Permette di attivare DEBUG temporaneamente per troubleshooting senza deployment.

---

> **Prossimi passi consigliati**: dopo aver configurato l'infrastruttura di logging, integrare con il modulo di monitoraggio (Prometheus/Grafana) per correlare metriche e log, e con il modulo di sicurezza (auditd + SIEM) per detection e risposta agli incidenti.
