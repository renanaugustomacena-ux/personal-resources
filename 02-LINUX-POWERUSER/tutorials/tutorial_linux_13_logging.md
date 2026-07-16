# Tutorial Linux 13 — Logging: rsyslog, journald, logrotate, audit log

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** centralizzazione log, rsyslog, journald, logrotate, log remoto, ELK
> **Prerequisiti:** `tutorial_linux_04_systemd.md`, `tutorial_linux_11_sicurezza.md`
> **Durata stimata:** 10-12 ore

---

## Mappa concettuale

```
Logging Linux
│
├── Sorgenti di log
│   ├── journald — systemd unified logging
│   ├── rsyslog — syslog daemon tradizionale
│   ├── kernel — dmesg / /proc/kmsg
│   └── applicazioni — log custom in /var/log/
│
├── journalctl — interrogazione journal
│   ├── Filtri: -u, -p, --since, -g
│   ├── Formati: -o json, short, cat
│   └── Persistenza: /var/log/journal/
│
├── rsyslog
│   ├── /etc/rsyslog.conf
│   ├── Facility.Severity routing
│   ├── Template per formati custom
│   └── Forwarding remoto (TCP/UDP/RELP)
│
├── logrotate
│   ├── /etc/logrotate.conf
│   ├── /etc/logrotate.d/
│   └── compress, rotate, dateext
│
└── Aggregazione centralizzata
    ├── Graylog
    ├── ELK (Elasticsearch + Logstash + Kibana)
    └── Loki + Grafana
```

---

# Parte A — journald

---

## A1. Configurazione journald persistente

```bash
# Per default journald scrive in memoria (/run/log/journal)
# Per renderlo persistente:
mkdir -p /var/log/journal
systemd-tmpfiles --create --prefix /var/log/journal

# /etc/systemd/journald.conf
cat > /etc/systemd/journald.conf << 'EOF'
[Journal]
# Persistenza su disco
Storage=persistent

# Dimensione massima
SystemMaxUse=2G
SystemKeepFree=500M
SystemMaxFileSize=100M

# Rotazione
MaxRetentionSec=1month
MaxFileSec=1week

# Compressione
Compress=yes

# Forward a syslog (rsyslog)
ForwardToSyslog=yes

# Rate limiting (per burst di log)
RateLimitIntervalSec=30s
RateLimitBurst=10000
EOF

systemctl restart systemd-journald
```

---

## A2. journalctl avanzato

```bash
# Filtri combinati
journalctl -u nginx -p err --since "1 hour ago"
journalctl -u nginx -u php8.1-fpm --since today

# Formato JSON (per parsing)
journalctl -u nginx -o json | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    print(d.get('MESSAGE', ''))
"

# Export per analisi offline
journalctl --since "2024-01-01" --until "2024-01-31" \
    -o json > /tmp/gennaio-log.json

# Campo specifico
journalctl -u nginx -o json | \
    jq -r '.PRIORITY as $p | select($p|tonumber <= 4) | .MESSAGE'

# Quanti log per servizio
journalctl --since today --until now -o json | \
    jq -r '._SYSTEMD_UNIT' | sort | uniq -c | sort -rn | head -20

# Disk usage
journalctl --disk-usage

# Pulizia log
journalctl --vacuum-time=30d        # rimuovi più vecchi di 30 giorni
journalctl --vacuum-size=1G         # riduci a max 1GB
journalctl --vacuum-files=10        # mantieni max 10 file

# Verifica integrità
journalctl --verify
```

> **Analogia:** journald è come un archivio aziendale centralizzato. Ogni messaggio ha metadati precisi: chi l'ha scritto (processo, utente), quando, con quale priorità. `journalctl` è il sistema di ricerca nell'archivio — puoi filtrare per mittente, periodo, urgenza, e ricevere i documenti in vari formati. Prima del giornale, ogni applicazione scriveva nei propri cassetti disordinati (file separati in /var/log).

---

# Parte B — rsyslog

---

## B1. Configurazione rsyslog

```bash
# /etc/rsyslog.conf
cat > /etc/rsyslog.conf << 'EOF'
# Moduli
module(load="imuxsock")      # log da applicazioni via socket
module(load="imklog")        # log kernel
module(load="imjournal"      # log da journald
    StateFile="imjournal.state")

# Se vuoi ricevere log remoti (UDP 514)
# module(load="imudp")
# input(type="imudp" port="514")

# Template JSON strutturato
template(name="json_template" type="string"
    string="{\"timestamp\":\"%timereported:::date-rfc3339%\",\"host\":\"%hostname%\",\"severity\":\"%syslogseverity-text%\",\"facility\":\"%syslogfacility-text%\",\"tag\":\"%syslogtag%\",\"message\":\"%msg:::json%\"}\n"
)

# Routing facility.severity → file
auth,authpriv.*          /var/log/auth.log
*.*;auth,authpriv.none   -/var/log/syslog
kern.*                   -/var/log/kern.log
mail.*                   -/var/log/mail.log
cron.*                   /var/log/cron.log

# Errori critici su canale dedicato
*.emerg                  :omusrmsg:*
*.crit                   /var/log/critical.log

# Includi configurazioni aggiuntive
$IncludeConfig /etc/rsyslog.d/*.conf
EOF

# Configura forwarding a server remoto
cat > /etc/rsyslog.d/90-remote.conf << 'EOF'
# Forwarding TCP a Graylog (porta 514 o custom)
# Template GELF per Graylog
template(name="gelf" type="list") {
    constant(value="{\"version\":\"1.1\",")
    constant(value="\"host\":\"")
    property(name="hostname")
    constant(value="\",\"short_message\":\"")
    property(name="msg" format="json")
    constant(value="\",\"level\":")
    property(name="syslogseverity")
    constant(value="}\n")
}

# Invia tutto a server centrale
*.* action(type="omfwd"
           Target="log-server.interno.it"
           Port="514"
           Protocol="tcp"
           action.resumeRetryCount="-1"
           Template="gelf"
           queue.type="LinkedList"
           queue.filename="rsyslog_queue"
           queue.maxdiskspace="256m"
           queue.saveonshutdown="on")
EOF

systemctl restart rsyslog

# Test
logger "Questo è un test rsyslog"
tail -1 /var/log/syslog
```

---

## B2. Log applicazione custom

```bash
# Logger — invia log a syslog da shell
logger "Servizio avviato"
logger -t myapp "Operazione completata"
logger -p local0.err "Errore critico"
logger -p user.warning -t webserver "404 frequenti"

# Facility custom: local0 - local7 (riservate per applicazioni)
# Configura in rsyslog.d/
cat > /etc/rsyslog.d/20-myapp.conf << 'EOF'
# Log di myapp in file dedicato
if $programname == 'myapp' then /var/log/myapp/app.log
& stop    # non duplicare in syslog
EOF

# Python: invia log a syslog
cat > /tmp/test_syslog.py << 'EOF'
import logging
import logging.handlers

logger = logging.getLogger('myapp')
handler = logging.handlers.SysLogHandler(
    address='/dev/log',
    facility=logging.handlers.SysLogHandler.LOG_LOCAL0
)
formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logger.info("Applicazione avviata")
logger.warning("Memoria alta: 85%")
logger.error("Connessione DB fallita")
EOF
python3 /tmp/test_syslog.py
journalctl -t myapp -n 5
```

---

# Parte C — logrotate

---

## C1. Configurazione logrotate

```bash
# /etc/logrotate.conf — configurazione globale
cat /etc/logrotate.conf

# /etc/logrotate.d/myapp — configurazione per applicazione
cat > /etc/logrotate.d/myapp << 'EOF'
/var/log/myapp/*.log {
    # Ruota giornalmente
    daily
    
    # Mantieni 30 copie
    rotate 30
    
    # Comprimi i vecchi log
    compress
    # Non comprimere il più recente (potrebbe essere ancora scritto)
    delaycompress
    
    # Non fallire se file non esiste
    missingok
    
    # Non ruotare se vuoto
    notifempty
    
    # Aggiungi data al nome (myapp-20240115.log.gz)
    dateext
    dateformat -%Y%m%d
    
    # Crea nuovo file dopo rotazione
    create 0640 appuser appgroup
    
    # Comandi da eseguire dopo rotazione
    postrotate
        # Segnala all'app di riaprire i file di log
        systemctl reload myapp 2>/dev/null || true
    endscript
}

# Log nginx
/var/log/nginx/*.log {
    weekly
    rotate 52
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 $(cat /var/run/nginx.pid)
        fi
    endscript
}
EOF

# Test senza eseguire
logrotate -d /etc/logrotate.d/myapp

# Forza rotazione
logrotate -f /etc/logrotate.d/myapp

# Status rotazioni
cat /var/lib/logrotate/status
```

---

# Parte D — Aggregazione centralizzata

---

## D1. Loki + Promtail (lightweight)

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki-data:/loki
      - ./loki-config.yml:/etc/loki/config.yml
    command: -config.file=/etc/loki/config.yml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  loki-data:
  grafana-data:
```

```yaml
# promtail-config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: system
    static_configs:
      - targets: ['localhost']
        labels:
          job: syslog
          host: mio-server
          __path__: /var/log/syslog

  - job_name: nginx
    static_configs:
      - targets: ['localhost']
        labels:
          job: nginx
          __path__: /var/log/nginx/*.log
    pipeline_stages:
      - regex:
          expression: '(?P<ip>\S+) .* \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+).*" (?P<status>\d+) (?P<size>\d+)'
      - labels:
          method:
          status:
```

---

# Parte E — Riepilogo

## Priorità syslog

| Valore | Nome | Quando usare |
|---|---|---|
| 0 | emerg | Sistema inutilizzabile |
| 1 | alert | Azione immediata richiesta |
| 2 | crit | Condizione critica |
| 3 | err | Condizione di errore |
| 4 | warning | Condizione di avviso |
| 5 | notice | Normale ma significativo |
| 6 | info | Messaggio informativo |
| 7 | debug | Debug |

## Comandi essenziali

```bash
# Segui log sistema in tempo reale
journalctl -f

# Log di un servizio
journalctl -u nginx -n 100

# Errori recenti
journalctl -p err --since "1 hour ago"

# Log autenticazione
tail -f /var/log/auth.log

# Forza rotazione log
logrotate -f /etc/logrotate.conf

# Test configurazione rsyslog
rsyslogd -N1 -f /etc/rsyslog.conf
```

## Prossimi passi

- `tutorial_linux_14_containerizzazione.md` — cgroups, Docker, Podman
- `tutorial_linux_20_monitoring.md` — Prometheus + Grafana
