# Automazione per Linux — Guida Completa

> **Modulo 21** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **Ansible > Puppet/Chef per modern; agentless.**
2. **systemd timer > cron per scheduled task.**
3. **Bash script per simple; Python per complex.**
4. **GitOps approach: configs in Git, CI applies.**
5. **Idempotenza sempre: ogni operazione deve poter essere rieseguita senza effetti collaterali.**
6. **Event-driven > polling quando possibile: reagire ai cambiamenti, non interrogare ciclicamente.**
7. **Runbook come codice: ogni procedura manuale è un bug in attesa di automazione.**


## Indice

- [Panoramica](#panoramica)
- [Cron: Scheduling Classico](#cron-scheduling-classico)
- [systemd Timers](#systemd-timers)
- [at e batch: Esecuzione Differita](#at-e-batch-esecuzione-differita)
- [Shell Scripting per Automazione](#shell-scripting-per-automazione)
- [Ansible: Fondamenti](#ansible-fondamenti)
- [Ansible Playbook](#ansible-playbook)
- [Ansible: Ottimizzazione delle Prestazioni](#ansible-ottimizzazione-delle-prestazioni)
- [Confronto Configuration Management](#confronto-configuration-management)
- [Ansible Molecule: Testing dei Ruoli](#ansible-molecule-testing-dei-ruoli)
- [Terraform per Linux](#terraform-per-linux)
- [Cloud-init: Provisioning](#cloud-init-provisioning)
- [Patching Automatizzato](#patching-automatizzato)
- [Monitoring Automatizzato](#monitoring-automatizzato)
- [User Provisioning Automatizzato](#user-provisioning-automatizzato)
- [Security Scanning Automatizzato](#security-scanning-automatizzato)
- [Automazione Event-Driven](#automazione-event-driven)
- [ChatOps](#chatops)
- [Runbook Automation](#runbook-automation)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Step-by-Step: Provisioning Completo di un Server](#step-by-step-provisioning-completo-di-un-server)

---

## Panoramica

L'automazione è il moltiplicatore di forza dell'amministratore di sistema. Ogni operazione manuale ripetitiva è un rischio: un passo dimenticato, un errore di battitura, un'inconsistenza tra server. L'automazione elimina questi problemi trasformando procedure in codice versionato, testabile e riproducibile.

Il panorama dell'automazione Linux si articola su più livelli:

| Livello | Strumenti | Scopo |
|---------|-----------|-------|
| **Scheduling** | cron, systemd timers, at/batch | Esecuzione temporizzata di task |
| **Scripting** | Bash, Python | Logica di automazione custom |
| **Configuration Management** | Ansible, Puppet, Chef, Salt | Stato desiderato dei sistemi |
| **Provisioning** | Terraform, cloud-init | Creazione infrastruttura |
| **Patching** | unattended-upgrades, dnf-automatic | Aggiornamenti automatici |
| **Monitoring** | Prometheus, Grafana, script-driven | Osservabilità |
| **Event-driven** | inotifywait, systemd path units | Reazione a eventi |
| **ChatOps** | Hubot, Mattermost bots | Operazioni conversazionali |

Ansible permette di configurare e gestire centinaia di server con codice dichiarativo (Infrastructure as Code). Terraform gestisce il provisioning dell'infrastruttura cloud. Cloud-init automatizza la configurazione iniziale delle VM e istanze cloud. Insieme, questi strumenti eliminano le operazioni manuali ripetitive, garantiscono consistenza e riducono gli errori umani.

---

## Cron: Scheduling Classico

Cron è il servizio di scheduling più antico e diffuso su Unix/Linux. Il demone `crond` (o `cron`) legge le crontab e esegue comandi agli orari specificati.

### Sintassi crontab

La crontab utente ha **5 campi temporali** seguiti dal comando:

```
+------- minuto (0-59)
| +------- ora (0-23)
| | +------- giorno del mese (1-31)
| | | +------- mese (1-12 o jan-dec)
| | | | +------- giorno della settimana (0-7, 0 e 7 = domenica, o sun-sat)
| | | | |
* * * * *  comando
```

La crontab di sistema (`/etc/crontab`) ha **6 campi**: i 5 temporali + il campo utente prima del comando:

```bash
# /etc/crontab
SHELL=/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=root

# m  h  dom mon dow  user    command
17   *  *   *   *    root    cd / && run-parts --report /etc/cron.hourly
25   6  *   *   *    root    test -x /usr/sbin/anacron || run-parts --report /etc/cron.daily
47   6  *   *   7    root    test -x /usr/sbin/anacron || run-parts --report /etc/cron.weekly
52   6  1   *   *    root    test -x /usr/sbin/anacron || run-parts --report /etc/cron.monthly
```

**Operatori nei campi:**

| Operatore | Significato | Esempio |
|-----------|-------------|---------|
| `*` | Ogni valore | `* * * * *` = ogni minuto |
| `,` | Lista di valori | `1,15,30` = al minuto 1, 15 e 30 |
| `-` | Intervallo | `1-5` = da lunedi a venerdi |
| `/` | Passo | `*/5` = ogni 5 unita |

**Stringhe speciali:**

```bash
@reboot     # Esegui una volta all'avvio
@yearly     # 0 0 1 1 *   (1 gennaio, mezzanotte)
@annually   # Sinonimo di @yearly
@monthly    # 0 0 1 * *   (primo del mese, mezzanotte)
@weekly     # 0 0 * * 0   (domenica, mezzanotte)
@daily      # 0 0 * * *   (ogni giorno, mezzanotte)
@midnight   # Sinonimo di @daily
@hourly     # 0 * * * *   (ogni ora, al minuto 0)
```

**Esempi pratici:**

```bash
# Ogni 15 minuti
*/15 * * * * /usr/local/bin/check-service.sh

# Alle 3:30 AM ogni giorno
30 3 * * * /usr/local/bin/backup.sh

# Ogni lunedi alle 8:00
0 8 * * 1 /usr/local/bin/report-settimanale.sh

# Primo e quindicesimo giorno del mese alle 6:00
0 6 1,15 * * /usr/local/bin/pulizia-log.sh

# Ogni 5 minuti, dal lunedi al venerdi, orario lavorativo
*/5 8-18 * * 1-5 /usr/local/bin/monitor-business.sh

# Due volte al giorno: 8:00 e 20:00
0 8,20 * * * /usr/local/bin/sync-dati.sh

# Ogni 2 ore
0 */2 * * * /usr/local/bin/check-disk.sh

# All'avvio del sistema
@reboot /usr/local/bin/startup-tasks.sh
```

### Cron di sistema vs cron utente

**Crontab utente** — gestita con il comando `crontab`:

```bash
crontab -e                    # Modifica la crontab dell'utente corrente
crontab -l                    # Elenca la crontab corrente
crontab -r                    # Rimuove la crontab (attenzione: nessuna conferma!)
crontab -u alice -e           # Modifica crontab di alice (richiede root)
```

Le crontab utente sono salvate in `/var/spool/cron/crontabs/` (Debian/Ubuntu) o `/var/spool/cron/` (RHEL/CentOS). Non modificare direttamente questi file.

**Crontab di sistema** — file `/etc/crontab` e directory `/etc/cron.d/`:

```bash
# Differenza chiave: la crontab di sistema ha il campo utente
# File: /etc/crontab o /etc/cron.d/mio-job
0 3 * * * root /usr/local/bin/backup-sistema.sh
#         ^^^^ campo utente (assente nelle crontab utente)
```

**Ambiente di esecuzione**: cron esegue i comandi con un ambiente minimale. Le variabili come `PATH`, `HOME`, `SHELL` sono limitate. Specificare sempre percorsi assoluti:

```bash
# SBAGLIATO - "node" potrebbe non essere nel PATH di cron
* * * * * node /app/script.js

# CORRETTO - percorso assoluto
* * * * * /usr/bin/node /app/script.js

# ALTERNATIVA - definire PATH nella crontab
PATH=/usr/local/bin:/usr/bin:/bin
* * * * * node /app/script.js
```

**Variabili di ambiente nella crontab:**

```bash
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=admin@esempio.it                  # Destinatario output (vuoto = no mail)
HOME=/home/admin
CRON_TZ=Europe/Rome                      # Timezone (non supportato ovunque)
```

### /etc/cron.d e directory periodiche

La directory `/etc/cron.d/` contiene frammenti di crontab in formato sistema (con campo utente). Ogni file e un job indipendente installabile da pacchetti:

```bash
# /etc/cron.d/certbot
0 */12 * * * root test -x /usr/bin/certbot && perl -e 'sleep int(rand(43200))' && certbot -q renew

# /etc/cron.d/sysstat
*/10 * * * * root /usr/lib/sysstat/debian-sa1 1 1
```

**Directory periodiche** — script eseguiti da `run-parts`:

```
/etc/cron.hourly/     # Eseguiti ogni ora
/etc/cron.daily/      # Eseguiti ogni giorno
/etc/cron.weekly/     # Eseguiti ogni settimana
/etc/cron.monthly/    # Eseguiti ogni mese
```

Gli script in queste directory devono:
- Essere eseguibili (`chmod +x`)
- NON avere estensione (`.sh`, `.py` ecc.) — `run-parts` ignora file con punti nel nome
- Avere nomi che rispettano la regex `^[a-zA-Z0-9_-]+$`

```bash
# Verificare quali script verrebbero eseguiti
run-parts --test /etc/cron.daily

# Creare un job giornaliero
cat > /etc/cron.daily/pulizia-tmp << 'SCRIPT'
#!/bin/bash
find /tmp -type f -mtime +7 -delete
find /tmp -type d -empty -delete
SCRIPT
chmod +x /etc/cron.daily/pulizia-tmp
```

### Anacron

Anacron gestisce job periodici su macchine non sempre accese (laptop, workstation). Garantisce che i job vengano eseguiti anche se la macchina era spenta all'orario previsto.

```bash
# /etc/anacrontab
# periodo  ritardo  identificatore  comando
1          5        cron.daily      run-parts /etc/cron.daily
7          10       cron.weekly     run-parts /etc/cron.weekly
@monthly   15       cron.monthly    run-parts /etc/cron.monthly
```

| Campo | Significato |
|-------|-------------|
| `periodo` | Frequenza in giorni (o `@monthly`) |
| `ritardo` | Minuti di attesa dopo l'avvio prima dell'esecuzione |
| `identificatore` | Nome univoco del job (usato per il timestamp) |
| `comando` | Comando da eseguire |

Anacron registra l'ultima esecuzione in `/var/spool/anacron/`:

```bash
cat /var/spool/anacron/cron.daily
# 20260522     <- data dell'ultima esecuzione

# Forzare esecuzione immediata
anacron -f -n    # -f = forza, -n = senza ritardo
```

Su Debian/Ubuntu moderno, anacron e integrato con cron: i job in `/etc/cron.daily/` ecc. sono gestiti da anacron se installato.

### cron.allow e cron.deny

Controllano quali utenti possono usare `crontab`:

```bash
/etc/cron.allow    # Se esiste: SOLO gli utenti elencati possono usare cron
/etc/cron.deny     # Se esiste (e cron.allow non esiste): utenti elencati NON possono usare cron
```

**Logica di accesso:**

1. Se `/etc/cron.allow` esiste -> solo gli utenti elencati possono usare crontab
2. Se `/etc/cron.allow` non esiste ma `/etc/cron.deny` esiste -> tutti possono tranne quelli elencati
3. Se nessuno dei due esiste -> comportamento dipende dalla distribuzione:
   - Debian/Ubuntu: tutti gli utenti possono usare crontab
   - RHEL/CentOS: solo root

```bash
# Permettere solo admin e deploy di usare cron
echo "admin" > /etc/cron.allow
echo "deploy" >> /etc/cron.allow

# Bloccare un utente specifico
echo "utente-problematico" >> /etc/cron.deny
```

### Logging di cron

```bash
# Debian/Ubuntu - cron logga in syslog
grep CRON /var/log/syslog
journalctl -u cron

# RHEL/CentOS - file dedicato
cat /var/log/cron

# Redirigere output dei job
*/5 * * * * /usr/local/bin/mio-script.sh >> /var/log/mio-script.log 2>&1

# Logging con timestamp
*/5 * * * * /usr/local/bin/mio-script.sh 2>&1 | ts '[%Y-%m-%d %H:%M:%S]' >> /var/log/mio-script.log

# Inviare output via mail (se MAILTO configurato)
MAILTO=admin@esempio.it
0 3 * * * /usr/local/bin/backup.sh

# Silenziare output (solo se non serve logging)
0 3 * * * /usr/local/bin/backup.sh > /dev/null 2>&1
```

**Monitorare job cron mancati:**

```bash
#!/bin/bash
# check-backup-cron.sh - verifica che il backup sia stato eseguito
MARKER_FILE="/var/run/backup-completato"
MAX_AGE=$((26 * 3600))  # 26 ore

if [ ! -f "$MARKER_FILE" ]; then
    echo "CRITICAL: Marker file del backup non trovato"
    exit 2
fi

file_age=$(( $(date +%s) - $(stat -c %Y "$MARKER_FILE") ))
if [ "$file_age" -gt "$MAX_AGE" ]; then
    echo "WARNING: Ultimo backup piu vecchio di 26 ore ($((file_age / 3600))h fa)"
    exit 1
fi
echo "OK: Backup eseguito $((file_age / 3600))h fa"
exit 0
```

---

## systemd Timers

I timer di systemd sono l'alternativa moderna a cron. Offrono logging integrato con journald, dipendenze da altri servizi, esecuzione condizionale, persistenza dei timer mancati e sandboxing di sicurezza.

### Struttura timer + service

Un timer systemd richiede due unit file: un `.timer` che definisce quando eseguire, e un `.service` che definisce cosa eseguire.

```ini
# /etc/systemd/system/backup-giornaliero.service
[Unit]
Description=Backup giornaliero dei dati
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=backup
Group=backup
ExecStart=/usr/local/bin/backup-giornaliero.sh
StandardOutput=journal
StandardError=journal
TimeoutStartSec=3600
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/mnt/backup /var/log/backup
NoNewPrivileges=yes
```

```ini
# /etc/systemd/system/backup-giornaliero.timer
[Unit]
Description=Timer per backup giornaliero

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
RandomizedDelaySec=900
AccuracySec=60

[Install]
WantedBy=timers.target
```

```bash
# Attivare il timer
systemctl daemon-reload
systemctl enable --now backup-giornaliero.timer

# Verificare lo stato
systemctl status backup-giornaliero.timer
systemctl status backup-giornaliero.service

# Eseguire manualmente (test)
systemctl start backup-giornaliero.service
```

### OnCalendar e monotonic timers

**OnCalendar** — timer basati su orario reale (realtime):

```ini
# Sintassi: DayOfWeek Year-Month-Day Hour:Minute:Second
OnCalendar=Mon..Fri *-*-* 08:00:00    # Lunedi-venerdi alle 8:00
OnCalendar=*-*-* 03:00:00              # Ogni giorno alle 3:00
OnCalendar=*-*-01 06:00:00             # Primo del mese alle 6:00
OnCalendar=Sat *-*-* 22:00:00          # Ogni sabato alle 22:00
OnCalendar=*-01,07-01 00:00:00         # 1 gennaio e 1 luglio
OnCalendar=hourly                       # Ogni ora
OnCalendar=daily                        # Ogni giorno a mezzanotte
OnCalendar=weekly                       # Ogni lunedi a mezzanotte
OnCalendar=monthly                      # Primo del mese a mezzanotte
OnCalendar=*-*-* *:00/15:00            # Ogni 15 minuti
OnCalendar=*-*-* 08..18:00/30:00       # Ogni 30 min, ore 8-18
```

**Validare espressioni OnCalendar:**

```bash
systemd-analyze calendar "Mon..Fri *-*-* 08:00:00"
#  Original form: Mon..Fri *-*-* 08:00:00
#     Next elapse: Mon 2026-05-25 08:00:00 CEST
#        From now: 2 days left

systemd-analyze calendar --iterations=5 "daily"
# Mostra le prossime 5 occorrenze
```

**Timer monotoni** — basati su intervalli relativi a un evento:

```ini
[Timer]
OnBootSec=5min                   # 5 minuti dopo il boot
OnActiveSec=30s                  # 30 secondi dopo l'attivazione del timer
OnUnitActiveSec=1h               # 1 ora dopo l'ultima esecuzione del service
OnUnitInactiveSec=30min          # 30 min dopo la fine dell'ultima esecuzione

# Combinabili - prima esecuzione 2 min dopo boot, poi ogni 15 min
OnBootSec=2min
OnUnitActiveSec=15min
```

**Esempio completo — health check ogni 5 minuti:**

```ini
# /etc/systemd/system/health-check.service
[Unit]
Description=Health check dei servizi

[Service]
Type=oneshot
ExecStart=/usr/local/bin/health-check.sh
```

```ini
# /etc/systemd/system/health-check.timer
[Unit]
Description=Health check periodico

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

### Persistent e AccuracySec

**Persistent=true**: se il timer avrebbe dovuto scattare mentre la macchina era spenta, esegue il job al boot successivo. Essenziale per backup e manutenzione.

**AccuracySec**: controlla la granularita di scheduling. systemd raggruppa timer vicini per ridurre i wakeup. Default: 1 minuto.

```ini
[Timer]
AccuracySec=1us          # Massima precisione
AccuracySec=1min         # Default
AccuracySec=1h           # OK per pulizia log non urgente
```

**RandomizedDelaySec**: ritardo casuale per evitare thundering herd (tutti i server che eseguono lo stesso job contemporaneamente):

```ini
[Timer]
OnCalendar=*-*-* 03:00:00
RandomizedDelaySec=1800   # Esecuzione tra le 03:00 e le 03:30
```

### Monitoraggio con systemctl

```bash
# Lista di tutti i timer attivi
systemctl list-timers

# Tutti i timer (anche inattivi)
systemctl list-timers --all

# Log dell'ultima esecuzione
journalctl -u backup-giornaliero.service --since today

# Stato dettagliato del timer
systemctl show backup-giornaliero.timer

# Timer transitori (senza file permanenti)
systemd-run --on-calendar="*-*-* 03:00:00" /usr/local/bin/mio-script.sh
systemd-run --on-boot=5m --on-unit-active=10m /usr/local/bin/monitor.sh
systemd-run --on-active=30s echo "Eseguito tra 30 secondi"
```

**Confronto cron vs systemd timer:**

| Caratteristica | cron | systemd timer |
|----------------|------|---------------|
| Logging | Syslog, manuale | journald integrato |
| Dipendenze | No | Si (After=, Wants=) |
| Persistent | Anacron separato | Persistent=true |
| Sicurezza | Ambiente utente | Sandboxing completo |
| Monitoraggio | Manuale | systemctl list-timers |
| Precisione | 1 minuto | Sub-secondo |
| Output | Redirect manuali | Automatico in journal |
| Condizionale | No | ConditionPathExists= ecc. |
| Randomizzazione | No | RandomizedDelaySec= |

### Pattern Avanzati systemd Timer

Oltre alla configurazione base, systemd offre pattern avanzati per scenari enterprise e IoT.

**WakeSystem** — risveglia il sistema dalla sospensione per eseguire il task:

```ini
# /etc/systemd/system/backup-notturno.timer
[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
WakeSystem=true             # Sveglia da suspend/hibernate
RandomizedDelaySec=600

[Install]
WantedBy=timers.target
```

Utile per laptop e sistemi embedded che vanno in sospensione. Il timer risveglia la macchina, esegue il job, e il sistema puo tornare in sospensione dopo.

**FixedRandomDelay** — ritardo deterministico per-macchina:

```ini
[Timer]
OnCalendar=daily
RandomizedDelaySec=3600
FixedRandomDelay=true       # Stesso ritardo ad ogni esecuzione
                            # Calcolato da machine-id, stabile tra reboot
```

A differenza di `RandomizedDelaySec` puro (ritardo diverso ogni volta), `FixedRandomDelay=true` genera un offset fisso basato sul machine-id. Ogni server ha il suo ritardo costante, evitando thundering herd senza perdere prevedibilita nei log.

**OnClockChange e OnTimezoneChange** — reagire a modifiche dell'orologio:

```ini
[Timer]
OnClockChange=true          # Scatta quando l'orologio di sistema cambia
OnTimezoneChange=true       # Scatta quando cambia il fuso orario
```

Utile per sistemi che ricevono aggiornamenti NTP dopo il boot (es. Raspberry Pi senza RTC) o ambienti dove il timezone puo cambiare (container, VM migrate tra datacenter).

**Timer Template Unit** — un singolo timer parametrizzato per piu servizi:

```ini
# /etc/systemd/system/backup@.timer
[Unit]
Description=Backup timer per %i

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
RandomizedDelaySec=1800
FixedRandomDelay=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/backup@.service
[Unit]
Description=Backup di %i

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh %i
```

```bash
# Attivare backup per directory diverse con lo stesso template
systemctl enable --now backup@database.timer
systemctl enable --now backup@configs.timer
systemctl enable --now backup@media.timer

# Ogni istanza ha il suo timer indipendente
systemctl list-timers 'backup@*'
```

**Combinazione monotonic + realtime** — per task che devono partire sia al boot che a orario:

```ini
[Timer]
OnBootSec=5min              # 5 minuti dopo il boot
OnCalendar=*-*-* 06,18:00:00  # Alle 6:00 e alle 18:00
Persistent=true
```

**Condizioni avanzate** — eseguire solo se certe condizioni sono soddisfatte:

```ini
[Unit]
Description=Pulizia log condizionale
ConditionPathExists=/var/log/app
ConditionDirectoryNotEmpty=/var/log/app
ConditionACPower=true       # Solo se alimentato da rete (non batteria)

[Service]
Type=oneshot
ExecStart=/usr/local/bin/pulisci-log.sh
```

```ini
[Timer]
OnCalendar=hourly
Persistent=true
```

Le condizioni in `[Unit]` del `.service` vengono valutate al momento dell'attivazione. Se una condizione fallisce, il timer salta l'esecuzione silenziosamente (visibile con `systemctl status`).

**Dipendenze tra timer** — ordinare esecuzioni correlate:

```ini
# /etc/systemd/system/export-db.service
[Unit]
Description=Export database
After=backup-db.service     # Solo dopo il backup
Wants=backup-db.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/export-db.sh
```

**Override di timer di sistema** — personalizzare timer installati da pacchetti senza modificare i file originali:

```bash
# Creare override per un timer di sistema (es. apt-daily)
sudo systemctl edit apt-daily.timer
```

```ini
# /etc/systemd/system/apt-daily.timer.d/override.conf
[Timer]
# Svuota le impostazioni originali
OnCalendar=
RandomizedDelaySec=

# Nuove impostazioni: aggiornamenti solo di notte
OnCalendar=*-*-* 04:00:00
RandomizedDelaySec=1800
Persistent=true
```

```bash
# Verificare la configurazione effettiva (originale + override)
systemctl cat apt-daily.timer
systemd-analyze calendar "*-*-* 04:00:00"

# Verificare prossima esecuzione
systemctl list-timers apt-daily.timer
```

**Monitoring e alerting per timer falliti:**

```ini
# /etc/systemd/system/notify-timer-failure@.service
[Unit]
Description=Notifica fallimento timer %i

[Service]
Type=oneshot
ExecStart=/usr/local/bin/alert-failure.sh %i
```

```bash
#!/bin/bash
# /usr/local/bin/alert-failure.sh
UNIT="$1"
HOSTNAME=$(hostname)
STATUS=$(systemctl status "$UNIT" --no-pager 2>&1 | head -20)

# Invia notifica via webhook (Slack, Teams, Mattermost)
curl -s -X POST "$ALERT_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d "{
    \"text\": \"Timer FALLITO: ${UNIT} su ${HOSTNAME}\",
    \"details\": \"$(echo "$STATUS" | head -5)\"
  }"
```

```ini
# Aggiungere OnFailure a qualsiasi service associato a un timer
# /etc/systemd/system/backup-giornaliero.service.d/on-failure.conf
[Unit]
OnFailure=notify-timer-failure@%n.service
```

Questo pattern crea un sistema di alerting generico: qualsiasi service con `OnFailure=notify-timer-failure@%n.service` inviera una notifica in caso di fallimento. Il `%n` passa il nome dell'unita fallita come parametro.

**Timer con sandboxing avanzato** — limitare risorse e permessi del servizio associato:

```ini
# /etc/systemd/system/pulizia-log.service
[Unit]
Description=Pulizia log giornaliera

[Service]
Type=oneshot
ExecStart=/usr/local/bin/pulisci-log.sh

# Sandboxing
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectControlGroups=true
MemoryDenyWriteExecute=true

# Limiti risorse
MemoryMax=256M
CPUQuota=25%
IOWeight=50
TimeoutStartSec=600         # Timeout di 10 minuti
```

Combinare sandboxing con timer garantisce che anche script eseguiti come root operino con privilegi minimi e risorse limitate.

---

## at e batch: Esecuzione Differita

`at` schedula comandi per un'esecuzione futura unica (non ricorrente). `batch` li esegue quando il carico del sistema e basso.

```bash
# Installazione
sudo apt install at                     # Debian/Ubuntu
sudo dnf install at                     # RHEL/Fedora
sudo systemctl enable --now atd

# Schedulare un job
at 3:00 AM                              # Alle 3:00 di oggi (o domani)
at 3:00 AM tomorrow                     # Domani alle 3:00
at now + 2 hours                        # Tra 2 ore
at now + 30 minutes                     # Tra 30 minuti
at 4pm + 3 days                         # Tra 3 giorni alle 16:00
at midnight                             # A mezzanotte
at noon                                 # A mezzogiorno
```

**Uso interattivo e da script:**

```bash
# Interattivo - inserire comandi, terminare con Ctrl+D
at 3:00 AM tomorrow
at> /usr/local/bin/backup.sh
at> echo "Backup completato" | mail -s "Backup" admin@esempio.it
at> <EOT>   # Ctrl+D

# Da script con here-doc
at 3:00 AM tomorrow << 'EOF'
/usr/local/bin/backup.sh
echo "Backup completato" | mail -s "Backup" admin@esempio.it
EOF

# Da pipe
echo "/usr/local/bin/backup.sh" | at 3:00 AM tomorrow

# Da file
at 3:00 AM tomorrow -f /usr/local/bin/comandi-batch.sh
```

**Gestione dei job:**

```bash
atq                                     # Lista job pendenti
at -c 42                                # Mostra il contenuto del job 42
atrm 42                                 # Rimuove il job 42
```

**batch** — esecue quando il load average scende sotto 1.5 (configurabile):

```bash
# Esegui quando il sistema e scarico
batch << 'EOF'
/usr/local/bin/report-pesante.sh
/usr/local/bin/compressione-log.sh
EOF

# Il load average soglia e configurabile con atd
# atd -l 0.8    # Esegui solo se load < 0.8
```

**Controllo accesso:** come per cron, esistono `/etc/at.allow` e `/etc/at.deny` con la stessa logica.

---

## Shell Scripting per Automazione

Gli script Bash sono il collante dell'automazione Linux. Ogni sysadmin deve padroneggiare pattern ricorrenti per config management, log rotation, health check e backup.

### Pattern di configuration management

```bash
#!/bin/bash
# config-enforcer.sh - garantisce lo stato desiderato di configurazioni
set -euo pipefail

SSHD_CONFIG="/etc/ssh/sshd_config"
CHANGED=0

# Funzione idempotente: imposta un parametro solo se diverso
ensure_config() {
    local file="$1" key="$2" value="$3"
    if grep -q "^${key}\s" "$file"; then
        if ! grep -q "^${key} ${value}$" "$file"; then
            sed -i "s|^${key}.*|${key} ${value}|" "$file"
            echo "[CHANGED] ${key} = ${value}"
            CHANGED=1
        else
            echo "[OK] ${key} = ${value}"
        fi
    else
        echo "${key} ${value}" >> "$file"
        echo "[ADDED] ${key} = ${value}"
        CHANGED=1
    fi
}

# Hardening SSH
ensure_config "$SSHD_CONFIG" "PermitRootLogin" "no"
ensure_config "$SSHD_CONFIG" "PasswordAuthentication" "no"
ensure_config "$SSHD_CONFIG" "X11Forwarding" "no"
ensure_config "$SSHD_CONFIG" "MaxAuthTries" "3"
ensure_config "$SSHD_CONFIG" "ClientAliveInterval" "300"
ensure_config "$SSHD_CONFIG" "ClientAliveCountMax" "2"
ensure_config "$SSHD_CONFIG" "Protocol" "2"

if [ "$CHANGED" -eq 1 ]; then
    sshd -t && systemctl reload sshd
    echo "[RELOAD] sshd ricaricato"
else
    echo "[SKIP] Nessuna modifica necessaria"
fi
```

**Pattern: lock file per evitare esecuzioni concorrenti:**

```bash
#!/bin/bash
LOCKFILE="/var/run/mio-script.lock"

# Tentativo di acquisire il lock
exec 200>"$LOCKFILE"
if ! flock -n 200; then
    echo "Un'altra istanza e gia in esecuzione. Uscita."
    exit 1
fi

# Cleanup automatico all'uscita
trap 'rm -f "$LOCKFILE"' EXIT

# ... logica dello script ...
```

### Log rotation manuale

```bash
#!/bin/bash
# rotate-logs.sh - rotazione log applicativi
set -euo pipefail

LOG_DIR="/var/log/myapp"
RETENTION_DAYS=30
MAX_SIZE_MB=100
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

rotate_log() {
    local logfile="$1"
    local size_kb
    size_kb=$(stat -c%s "$logfile" 2>/dev/null || echo 0)
    size_kb=$((size_kb / 1024))

    if [ "$size_kb" -gt $((MAX_SIZE_MB * 1024)) ]; then
        local rotated="${logfile}.${TIMESTAMP}"
        cp "$logfile" "$rotated"
        : > "$logfile"  # Svuota il file (mantiene inode per processi aperti)
        gzip "$rotated"
        echo "[ROTATED] ${logfile} -> ${rotated}.gz"
    fi
}

# Ruota tutti i log .log
for logfile in "${LOG_DIR}"/*.log; do
    [ -f "$logfile" ] || continue
    rotate_log "$logfile"
done

# Elimina log vecchi
find "$LOG_DIR" -name "*.gz" -mtime +${RETENTION_DAYS} -delete
echo "[CLEANUP] Rimossi log piu vecchi di ${RETENTION_DAYS} giorni"
```

**Nota**: per la produzione, preferire `logrotate` con configurazione in `/etc/logrotate.d/`. Lo script sopra e utile per applicazioni custom o quando logrotate non e disponibile.

### Health check

```bash
#!/bin/bash
# health-check.sh - controllo salute servizi e sistema
set -euo pipefail

ALERT_EMAIL="ops@esempio.it"
HOSTNAME=$(hostname -f)
ERRORS=()

# --- Controllo servizi ---
check_service() {
    local service="$1"
    if ! systemctl is-active --quiet "$service"; then
        ERRORS+=("SERVIZIO DOWN: $service")
        # Tentativo di riavvio automatico
        systemctl restart "$service" 2>/dev/null || true
    fi
}

check_service nginx
check_service postgresql
check_service redis-server

# --- Controllo disco ---
check_disk() {
    local mount="$1" threshold="$2"
    local usage
    usage=$(df "$mount" --output=pcent | tail -1 | tr -d ' %')
    if [ "$usage" -ge "$threshold" ]; then
        ERRORS+=("DISCO PIENO: $mount al ${usage}% (soglia: ${threshold}%)")
    fi
}

check_disk / 85
check_disk /var 90
check_disk /home 80

# --- Controllo memoria ---
mem_available_mb=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
if [ "$mem_available_mb" -lt 512 ]; then
    ERRORS+=("MEMORIA BASSA: ${mem_available_mb}MB disponibili")
fi

# --- Controllo load average ---
load_1m=$(awk '{print $1}' /proc/loadavg)
cpu_count=$(nproc)
if (( $(echo "$load_1m > $cpu_count * 2" | bc -l) )); then
    ERRORS+=("LOAD ALTO: ${load_1m} (CPUs: ${cpu_count})")
fi

# --- Controllo certificati SSL ---
check_cert() {
    local domain="$1" days_warning="$2"
    local expiry
    expiry=$(echo | openssl s_client -servername "$domain" -connect "${domain}:443" 2>/dev/null \
             | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    if [ -n "$expiry" ]; then
        local expiry_epoch days_left
        expiry_epoch=$(date -d "$expiry" +%s)
        days_left=$(( (expiry_epoch - $(date +%s)) / 86400 ))
        if [ "$days_left" -lt "$days_warning" ]; then
            ERRORS+=("CERT SCADENZA: ${domain} scade tra ${days_left} giorni")
        fi
    fi
}

check_cert "esempio.it" 30

# --- Controllo connettivita ---
check_connectivity() {
    local target="$1"
    if ! ping -c 1 -W 3 "$target" > /dev/null 2>&1; then
        ERRORS+=("CONNETTIVITA: impossibile raggiungere $target")
    fi
}

check_connectivity 8.8.8.8
check_connectivity 1.1.1.1

# --- Report ---
if [ ${#ERRORS[@]} -gt 0 ]; then
    REPORT="HEALTH CHECK FALLITO su ${HOSTNAME}\n\n"
    for err in "${ERRORS[@]}"; do
        REPORT+="  - ${err}\n"
    done
    REPORT+="\nTimestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo -e "$REPORT"
    echo -e "$REPORT" | mail -s "[ALERT] Health check ${HOSTNAME}" "$ALERT_EMAIL"
    exit 1
else
    echo "OK: Tutti i controlli superati su ${HOSTNAME}"
    exit 0
fi
```

### Backup script

```bash
#!/bin/bash
# backup-completo.sh - backup incrementale con rsync e retention
set -euo pipefail

# --- Configurazione ---
BACKUP_SRC="/var/www /etc /home"
BACKUP_DST="/mnt/backup"
RETENTION_DAILY=7
RETENTION_WEEKLY=4
RETENTION_MONTHLY=6
EXCLUDE_FILE="/etc/backup-exclude.txt"
LOG_FILE="/var/log/backup.log"
MARKER="/var/run/backup-completato"

# --- Lock ---
LOCKFILE="/var/run/backup.lock"
exec 200>"$LOCKFILE"
if ! flock -n 200; then
    echo "Backup gia in esecuzione" | tee -a "$LOG_FILE"
    exit 1
fi

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] $*" | tee -a "$LOG_FILE"; }

TODAY=$(date +%Y-%m-%d)
DAY_OF_WEEK=$(date +%u)
DAY_OF_MONTH=$(date +%d)

# Determina tipo di backup
if [ "$DAY_OF_MONTH" = "01" ]; then
    BACKUP_TYPE="monthly"
elif [ "$DAY_OF_WEEK" = "7" ]; then
    BACKUP_TYPE="weekly"
else
    BACKUP_TYPE="daily"
fi

BACKUP_DIR="${BACKUP_DST}/${BACKUP_TYPE}/${TODAY}"
LATEST_LINK="${BACKUP_DST}/latest"

log "Inizio backup ${BACKUP_TYPE}: ${TODAY}"

# Crea directory
mkdir -p "$BACKUP_DIR"

# File di esclusione
if [ ! -f "$EXCLUDE_FILE" ]; then
    cat > "$EXCLUDE_FILE" << 'EXCL'
*.tmp
*.swp
*.cache
__pycache__
node_modules
.git
/var/cache
/var/tmp
EXCL
fi

# Rsync con hard link all'ultimo backup (deduplicazione)
RSYNC_OPTS=(
    -aAXv
    --delete
    --exclude-from="$EXCLUDE_FILE"
    --stats
)

if [ -L "$LATEST_LINK" ]; then
    RSYNC_OPTS+=(--link-dest="$LATEST_LINK")
fi

for src in $BACKUP_SRC; do
    if [ -d "$src" ]; then
        log "Backup di: $src"
        rsync "${RSYNC_OPTS[@]}" "$src" "$BACKUP_DIR/" 2>&1 | tee -a "$LOG_FILE"
    else
        log "SKIP: $src non esiste"
    fi
done

# Aggiorna link simbolico
rm -f "$LATEST_LINK"
ln -s "$BACKUP_DIR" "$LATEST_LINK"

# --- Retention ---
cleanup_old() {
    local type="$1" keep="$2"
    local dir="${BACKUP_DST}/${type}"
    if [ -d "$dir" ]; then
        local count
        count=$(find "$dir" -maxdepth 1 -mindepth 1 -type d | wc -l)
        if [ "$count" -gt "$keep" ]; then
            find "$dir" -maxdepth 1 -mindepth 1 -type d | sort | head -n -"$keep" | while read -r old; do
                log "CLEANUP: rimozione $old"
                rm -rf "$old"
            done
        fi
    fi
}

cleanup_old "daily" "$RETENTION_DAILY"
cleanup_old "weekly" "$RETENTION_WEEKLY"
cleanup_old "monthly" "$RETENTION_MONTHLY"

# Marker per monitoraggio
touch "$MARKER"
log "Backup completato: ${BACKUP_DIR}"
```

---

## Ansible: Fondamenti

Ansible e agentless: si connette via SSH e non richiede software sui target.

```bash
# Installazione
sudo apt install ansible                # Debian/Ubuntu
sudo dnf install ansible-core           # RHEL/Fedora
pip install ansible                     # Via pip (versione piu recente)

# File principali
/etc/ansible/ansible.cfg               # Configurazione globale
/etc/ansible/hosts                     # Inventario globale
~/.ansible.cfg                         # Configurazione utente
./ansible.cfg                          # Configurazione progetto (priorita massima)
```

### Inventario avanzato

```ini
# inventory.ini
[webservers]
web1 ansible_host=10.0.0.1
web2 ansible_host=10.0.0.2

[dbservers]
db1 ansible_host=10.0.0.10
db2 ansible_host=10.0.0.11

[monitoring]
grafana ansible_host=10.0.0.20

[all:vars]
ansible_user=admin
ansible_ssh_private_key_file=~/.ssh/id_ed25519

[webservers:vars]
http_port=80

[staging:children]
webservers
dbservers

[production:children]
webservers
dbservers
monitoring
```

**Inventario dinamico** — script che genera JSON:

```bash
# Usare script che ritorna JSON
ansible -i ./dynamic-inventory.py all -m ping

# Inventario da cloud provider
ansible -i aws_ec2.yml all -m ping

# Plugin cloud per inventario dinamico
# ansible.cfg:
# [inventory]
# enable_plugins = aws_ec2, azure_rm, gcp_compute
```

**Inventario YAML** (alternativa):

```yaml
# inventory.yml
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 10.0.0.1
        web2:
          ansible_host: 10.0.0.2
    dbservers:
      hosts:
        db1:
          ansible_host: 10.0.0.10
      vars:
        db_port: 5432
  vars:
    ansible_user: admin
```

### Comandi Ad-hoc

```bash
# Ping tutti gli host
ansible all -m ping

# Eseguire comando
ansible webservers -m command -a "uptime"
ansible all -m shell -a "df -h | grep sda"

# Gestire pacchetti (Debian)
ansible webservers -m apt -a "name=nginx state=present" -b

# Gestire pacchetti (RHEL)
ansible webservers -m dnf -a "name=nginx state=present" -b

# Gestire servizi
ansible webservers -m service -a "name=nginx state=started enabled=yes" -b

# Copiare file
ansible webservers -m copy -a "src=nginx.conf dest=/etc/nginx/nginx.conf" -b

# Raccogliere fatti
ansible web1 -m setup                  # Tutti i fatti
ansible web1 -m setup -a "filter=ansible_distribution*"
```

### Moduli principali

**apt / dnf / yum** — gestione pacchetti:

```yaml
# apt (Debian/Ubuntu)
- name: Installa pacchetti
  apt:
    name:
      - nginx
      - python3-pip
      - curl
    state: present
    update_cache: yes
    cache_valid_time: 3600    # Non aggiornare cache se < 1 ora

- name: Rimuovi pacchetto
  apt:
    name: apache2
    state: absent
    purge: yes                # Rimuove anche i file di configurazione

# dnf (RHEL 8+/Fedora)
- name: Installa pacchetti RHEL
  dnf:
    name:
      - nginx
      - python3-pip
    state: present

- name: Aggiorna tutti i pacchetti
  dnf:
    name: "*"
    state: latest
    exclude: kernel*          # Escludi kernel
```

**service / systemd** — gestione servizi:

```yaml
- name: Avvia e abilita nginx
  service:
    name: nginx
    state: started
    enabled: yes

- name: Riavvia servizio
  systemd:
    name: nginx
    state: restarted
    daemon_reload: yes        # Ricarica unit files prima del restart
```

**copy / template** — deploy file:

```yaml
# Copy: copia file statici
- name: Copia configurazione
  copy:
    src: files/nginx.conf
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: '0644'
    backup: yes               # Crea backup del file precedente

# Template: copia con variabili Jinja2
- name: Deploy configurazione dinamica
  template:
    src: templates/nginx.conf.j2
    dest: /etc/nginx/sites-available/{{ domain }}.conf
    owner: root
    group: root
    mode: '0644'
    validate: nginx -t -c %s  # Valida prima di applicare
  notify: Reload Nginx
```

**user / group** — gestione utenti:

```yaml
- name: Crea gruppo applicativo
  group:
    name: appgroup
    gid: 1500
    state: present

- name: Crea utente applicativo
  user:
    name: appuser
    uid: 1500
    group: appgroup
    groups: sudo,docker
    shell: /bin/bash
    home: /home/appuser
    create_home: yes
    password: "{{ password_hash }}"
    state: present

- name: Aggiungi chiave SSH
  authorized_key:
    user: appuser
    key: "{{ lookup('file', 'files/id_ed25519.pub') }}"
    state: present

- name: Rimuovi utente
  user:
    name: vecchio-utente
    state: absent
    remove: yes               # Rimuove home directory
```

**file** — gestione file e directory:

```yaml
- name: Crea directory
  file:
    path: /opt/myapp
    state: directory
    owner: appuser
    group: appgroup
    mode: '0755'

- name: Crea link simbolico
  file:
    src: /opt/myapp/current
    dest: /var/www/html
    state: link

- name: Imposta permessi ricorsivi
  file:
    path: /opt/myapp/data
    state: directory
    recurse: yes
    owner: appuser
    group: appgroup
```

**lineinfile / blockinfile** — modifiche mirate a file:

```yaml
- name: Assicura riga in file
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^PermitRootLogin'
    line: 'PermitRootLogin no'
    state: present
  notify: Restart sshd

- name: Aggiungi blocco di configurazione
  blockinfile:
    path: /etc/hosts
    block: |
      10.0.0.1  web1.interno
      10.0.0.2  web2.interno
      10.0.0.10 db1.interno
    marker: "# {mark} ANSIBLE MANAGED - server interni"
```

**cron** — gestione job cron via Ansible:

```yaml
- name: Crea job cron per backup
  cron:
    name: "backup giornaliero"
    minute: "30"
    hour: "3"
    job: "/usr/local/bin/backup.sh >> /var/log/backup.log 2>&1"
    user: root
    state: present

- name: Crea job cron con variabile speciale
  cron:
    name: "pulizia al reboot"
    special_time: reboot
    job: "/usr/local/bin/cleanup-tmp.sh"
```

---

## Ansible Playbook

### Playbook Base

```yaml
# site.yml
---
- name: Configurazione Web Server
  hosts: webservers
  become: yes
  vars:
    http_port: 80
    server_name: "{{ inventory_hostname }}"

  tasks:
    - name: Aggiorna pacchetti
      apt:
        update_cache: yes
        upgrade: safe

    - name: Installa Nginx
      apt:
        name: nginx
        state: present

    - name: Copia configurazione
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/sites-available/default
        owner: root
        group: root
        mode: '0644'
      notify: Reload Nginx

    - name: Abilita Nginx
      service:
        name: nginx
        state: started
        enabled: yes

    - name: Apri porta firewall
      ufw:
        rule: allow
        port: "{{ http_port }}"
        proto: tcp

  handlers:
    - name: Reload Nginx
      service:
        name: nginx
        state: reloaded
```

### Playbook con Ruoli

```
project/
├── site.yml
├── inventory.ini
├── ansible.cfg
├── group_vars/
│   ├── all.yml
│   └── webservers.yml
├── host_vars/
│   └── web1.yml
└── roles/
    ├── common/
    │   ├── tasks/main.yml
    │   ├── handlers/main.yml
    │   ├── templates/
    │   ├── files/
    │   └── defaults/main.yml
    ├── nginx/
    │   ├── tasks/main.yml
    │   ├── handlers/main.yml
    │   ├── templates/
    │   └── defaults/main.yml
    └── postgresql/
        ├── tasks/main.yml
        ├── handlers/main.yml
        ├── templates/
        └── defaults/main.yml
```

```yaml
# site.yml con ruoli
---
- name: Configurazione base tutti i server
  hosts: all
  become: yes
  roles:
    - common

- name: Configurazione web server
  hosts: webservers
  become: yes
  roles:
    - nginx

- name: Configurazione database
  hosts: dbservers
  become: yes
  roles:
    - postgresql
```

```yaml
# roles/common/tasks/main.yml
---
- name: Aggiorna sistema
  apt:
    update_cache: yes
    upgrade: safe

- name: Installa pacchetti comuni
  apt:
    name:
      - vim
      - htop
      - curl
      - wget
      - unzip
      - fail2ban
      - ufw
    state: present

- name: Configura timezone
  timezone:
    name: Europe/Rome

- name: Configura NTP
  service:
    name: chrony
    state: started
    enabled: yes

- name: Hardening sysctl
  sysctl:
    name: "{{ item.name }}"
    value: "{{ item.value }}"
    sysctl_set: yes
    reload: yes
  loop:
    - { name: 'net.ipv4.ip_forward', value: '0' }
    - { name: 'net.ipv4.conf.all.rp_filter', value: '1' }
    - { name: 'net.ipv4.tcp_syncookies', value: '1' }
    - { name: 'kernel.randomize_va_space', value: '2' }
```

```yaml
# roles/common/defaults/main.yml
---
common_timezone: Europe/Rome
common_ntp_service: chrony
common_packages:
  - vim
  - htop
  - curl
  - wget
  - unzip
  - fail2ban
  - ufw
```

### Ansible Vault in profondita

Ansible Vault cripta file e variabili per proteggere secret nei repository Git.

```bash
# Creare file criptato
ansible-vault create secrets.yml

# Criptare file esistente
ansible-vault encrypt group_vars/all/vault.yml

# Decriptare file
ansible-vault decrypt secrets.yml

# Modificare file criptato
ansible-vault edit secrets.yml

# Visualizzare contenuto senza decriptare su disco
ansible-vault view secrets.yml

# Cambiare password
ansible-vault rekey secrets.yml
```

**Criptare singole variabili** (inline con `encrypt_string`):

```bash
# Cripta una stringa
ansible-vault encrypt_string 'MiaPasswordSegreta' --name 'db_password'
# Output:
# db_password: !vault |
#   $ANSIBLE_VAULT;1.1;AES256
#   61626364...

# Usare nel playbook
vars:
  db_password: !vault |
    $ANSIBLE_VAULT;1.1;AES256
    61626364656667...
```

**Vault ID multipli** — password diverse per ambienti diversi:

```bash
# Creare con vault-id
ansible-vault create --vault-id prod@prompt secrets-prod.yml
ansible-vault create --vault-id staging@prompt secrets-staging.yml

# Eseguire con vault-id specifico
ansible-playbook site.yml --vault-id prod@prompt --vault-id staging@prompt

# Password da file (per CI/CD)
echo "password-prod" > ~/.vault-pass-prod
chmod 600 ~/.vault-pass-prod
ansible-playbook site.yml --vault-password-file ~/.vault-pass-prod

# In ansible.cfg
# [defaults]
# vault_password_file = ~/.vault-pass
```

**Pattern consigliato per secrets** — separare variabili criptate:

```
group_vars/
  all/
    vars.yml          # Variabili normali
    vault.yml         # Variabili criptate (prefisso vault_)
```

```yaml
# group_vars/all/vault.yml (criptato)
vault_db_password: "MiaPasswordSegreta"
vault_api_key: "abc123"

# group_vars/all/vars.yml (non criptato, referenzia vault_)
db_password: "{{ vault_db_password }}"
api_key: "{{ vault_api_key }}"
```

### Integrazione con Secret Manager Esterni

Ansible Vault cripta file localmente, ma in ambienti enterprise i secret vengono gestiti centralmente da strumenti come HashiCorp Vault, AWS Secrets Manager o Azure Key Vault. La collection `community.hashi_vault` permette di recuperare secret dinamici a runtime senza mai scriverli su disco.

```bash
# Installare la collection HashiCorp Vault
ansible-galaxy collection install community.hashi_vault

# Prerequisiti Python sull'Ansible controller
pip install hvac                 # Client Python per HashiCorp Vault
```

**Autenticazione AppRole** — metodo consigliato per automazione (non interattivo):

```yaml
# group_vars/all/vault_config.yml
# Questi valori NON sono secret — identificano l'applicazione
vault_addr: "https://vault.azienda.it:8200"
vault_auth_method: approle
vault_role_id: "{{ lookup('env', 'VAULT_ROLE_ID') }}"
vault_secret_id: "{{ lookup('env', 'VAULT_SECRET_ID') }}"
```

```yaml
# Recuperare secret da HashiCorp Vault
- name: Leggi credenziali database da Vault
  ansible.builtin.set_fact:
    db_password: >-
      {{ lookup('community.hashi_vault.hashi_vault',
         'secret/data/produzione/database',
         auth_method='approle',
         role_id=vault_role_id,
         secret_id=vault_secret_id,
         url=vault_addr
      )['password'] }}
  no_log: true    # MAI mostrare secret nei log

- name: Configura applicazione con secret dinamico
  ansible.builtin.template:
    src: app-config.j2
    dest: /opt/app/config.yml
    mode: '0600'
    owner: app
  no_log: true

# Secret dinamici — credenziali database temporanee
- name: Genera credenziali database temporanee
  community.hashi_vault.vault_read:
    url: "{{ vault_addr }}"
    auth_method: approle
    role_id: "{{ vault_role_id }}"
    secret_id: "{{ vault_secret_id }}"
    path: "database/creds/app-readonly"
  register: db_creds
  no_log: true

# db_creds.data.username e db_creds.data.password
# sono credenziali con TTL limitato (es. 1 ora)
- name: Configura connessione database
  ansible.builtin.template:
    src: db-connection.j2
    dest: /opt/app/db.conf
    mode: '0600'
  vars:
    db_user: "{{ db_creds.data.username }}"
    db_pass: "{{ db_creds.data.password }}"
  no_log: true
```

**Vault password da CI/CD** — per pipeline automatiche:

```bash
# GitLab CI: la password vault viene da una variabile CI masked
# .gitlab-ci.yml
deploy:
  script:
    - echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/.vault-pass
    - chmod 600 /tmp/.vault-pass
    - ansible-playbook -i inventory site.yml --vault-password-file /tmp/.vault-pass
    - rm -f /tmp/.vault-pass
  variables:
    ANSIBLE_VAULT_PASSWORD: $CI_VAULT_PASSWORD   # Variabile masked in GitLab

# Alternativa: script wrapper per vault password
# vault-pass.sh
#!/bin/bash
echo "$ANSIBLE_VAULT_PASSWORD"
# In ansible.cfg: vault_password_file = ./vault-pass.sh
```

**Multi-vault** — vault-id per ambienti separati (dev, staging, prod):

```bash
# Creare vault con ID diversi
ansible-vault create --vault-id dev@prompt group_vars/dev/vault.yml
ansible-vault create --vault-id prod@~/.vault-pass-prod group_vars/prod/vault.yml

# Eseguire con multipli vault-id
ansible-playbook site.yml \
  --vault-id dev@prompt \
  --vault-id prod@~/.vault-pass-prod
```

**Regole di sicurezza per secrets:**

- `no_log: true` su OGNI task che manipola secret
- Mai usare `debug` per stampare variabili contenenti password
- Prefix `vault_` per tutte le variabili criptate (convenzione visiva)
- Rotazione periodica dei secret e della vault password
- In CI: usare variabili masked/protected, mai committare file `.vault-pass`
- Aggiungere `.vault-pass*` al `.gitignore`

### Ansible Galaxy e Collections

```bash
# Cercare ruoli su Galaxy
ansible-galaxy search nginx

# Installare ruoli da Galaxy
ansible-galaxy install geerlingguy.nginx
ansible-galaxy install geerlingguy.postgresql

# Installare da requirements file
cat > requirements.yml << 'EOF'
---
roles:
  - name: geerlingguy.nginx
    version: "3.1.4"
  - name: geerlingguy.postgresql
    version: "3.4.1"

collections:
  - name: community.general
    version: ">=7.0.0"
  - name: ansible.posix
    version: ">=1.5.0"
EOF

ansible-galaxy install -r requirements.yml
ansible-galaxy collection install -r requirements.yml

# Creare struttura ruolo
ansible-galaxy init mio-ruolo
```

### Ecosistema Collections e Galaxy NG

A partire da Ansible 2.10, le collection sono il metodo primario per distribuire moduli, plugin e ruoli. Ogni modulo ha un **Fully Qualified Collection Name (FQCN)** che elimina ambiguita:

```yaml
# FQCN - forma raccomandata (obbligatoria da Ansible 2.10+)
- name: Installa pacchetto
  ansible.builtin.apt:          # Non piu solo "apt"
    name: nginx
    state: present

- name: Gestisci utente
  ansible.builtin.user:
    name: deploy
    groups: docker
    append: true

- name: File da template
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf

# Moduli da collection esterne
- name: Gestisci container
  community.docker.docker_container:
    name: app
    image: myapp:latest

- name: Configura firewall
  ansible.posix.firewalld:
    port: 8080/tcp
    permanent: true
    state: enabled
```

**Struttura di una collection:**

```
mio_namespace/mia_collection/
├── galaxy.yml              # Metadati (namespace, nome, versione, dipendenze)
├── plugins/
│   ├── modules/            # Moduli custom
│   ├── inventory/          # Plugin inventario
│   ├── lookup/             # Plugin lookup
│   ├── filter/             # Filtri Jinja2 custom
│   ├── callback/           # Plugin callback
│   └── connection/         # Plugin connessione
├── roles/                  # Ruoli inclusi nella collection
│   └── webserver/
├── playbooks/              # Playbook di esempio
├── docs/                   # Documentazione
├── tests/                  # Test (Molecule, integration)
└── meta/
    └── runtime.yml         # Redirect e deprecation di moduli
```

```yaml
# galaxy.yml della collection
namespace: mia_azienda
name: infrastruttura
version: 2.1.0
readme: README.md
authors:
  - Ops Team <ops@azienda.it>
description: Collection per infrastruttura interna
license: GPL-3.0-or-later
repository: https://gitlab.azienda.it/ansible/infra-collection

dependencies:
  ansible.posix: ">=1.5.0"
  community.general: ">=7.0.0"
  community.crypto: ">=2.0.0"

# Versione minima Ansible richiesta
requires_ansible: ">=2.15.0"
```

**Galaxy NG vs Ansible Galaxy** — Galaxy NG e il backend di nuova generazione basato su Pulp, usato sia da galaxy.ansible.com pubblico che da **Private Automation Hub** (AAP) per repository interni:

```bash
# Configurare repository privato (Private Automation Hub / Galaxy NG)
cat >> ansible.cfg << 'EOF'
[galaxy]
server_list = private_hub, galaxy

[galaxy_server.private_hub]
url=https://hub.azienda.it/api/galaxy/
token=mio_token_api
# Il server privato ha priorita (elencato per primo)

[galaxy_server.galaxy]
url=https://galaxy.ansible.com/
EOF

# Installare collection da hub privato
ansible-galaxy collection install mia_azienda.infrastruttura

# Pubblicare collection su hub privato
ansible-galaxy collection build
ansible-galaxy collection publish \
  mia_azienda-infrastruttura-2.1.0.tar.gz \
  --server private_hub
```

**Pinning e gestione dipendenze** — in produzione, pinnare sempre le versioni:

```yaml
# requirements.yml - best practice per produzione
---
collections:
  - name: ansible.posix
    version: "1.5.4"          # Versione esatta, no range
  - name: community.general
    version: "8.2.0"
  - name: community.docker
    version: "3.7.0"
  - name: mia_azienda.infrastruttura
    source: https://hub.azienda.it/api/galaxy/
    version: "2.1.0"

roles:
  - name: geerlingguy.nginx
    version: "3.2.0"
  - name: geerlingguy.certbot
    version: "5.1.0"
```

```bash
# Installare tutto da requirements.yml
ansible-galaxy install -r requirements.yml --force
ansible-galaxy collection install -r requirements.yml --force

# Verificare collection installate
ansible-galaxy collection list

# Verificare versione specifica
ansible-galaxy collection verify community.general
```

### Esecuzione e opzioni avanzate

```bash
# Eseguire playbook
ansible-playbook -i inventory.ini site.yml

# Opzioni principali
ansible-playbook site.yml -l webservers        # Solo un gruppo
ansible-playbook site.yml --check              # Dry run
ansible-playbook site.yml --diff               # Mostra differenze
ansible-playbook site.yml --tags "nginx"       # Solo task con tag
ansible-playbook site.yml --skip-tags "slow"   # Salta task con tag
ansible-playbook site.yml -e "http_port=8080"  # Override variabili
ansible-playbook site.yml --ask-become-pass    # Password sudo
ansible-playbook site.yml --start-at-task "Installa Nginx"  # Riprendi da task
ansible-playbook site.yml --step               # Conferma ogni task
ansible-playbook site.yml -v                   # Verbose (-vvvv max)
ansible-playbook site.yml --list-tasks         # Lista task senza eseguire
ansible-playbook site.yml --list-hosts         # Lista host target

# Parallelismo
ansible-playbook site.yml -f 20               # 20 fork paralleli (default: 5)

# Vault
ansible-playbook site.yml --ask-vault-pass
ansible-playbook site.yml --vault-password-file ~/.vault-pass
```

---

## Ansible: Ottimizzazione delle Prestazioni

Ansible puo risultare lento su flotte grandi o con playbook complessi. Esistono numerose tecniche per accelerare significativamente l'esecuzione, dalla configurazione SSH fino a plugin di terze parti che riscrivono il meccanismo di trasporto.

### SSH Pipelining

Il pipelining e la singola ottimizzazione piu impattante. Riduce il numero di connessioni SSH necessarie per eseguire un modulo, eliminando la copia temporanea dei file sul target:

```ini
# ansible.cfg
[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o PreferHostKeyChecking=no
```

**Requisito**: `requiretty` deve essere disabilitato in `/etc/sudoers` sui target. Verificare che non esista la riga `Defaults requiretty`. Se presente, commentarla o aggiungere un'eccezione per l'utente Ansible:

```bash
# Sul target: /etc/sudoers.d/ansible
Defaults:ansible !requiretty
```

Il pipelining riduce i round-trip SSH da 5-6 a 2 per ogni modulo eseguito, con miglioramenti tipici del 30-50% sul tempo totale.

### Mitogen Strategy Plugin

Mitogen e un plugin che sostituisce l'implementazione shell-centrica di Ansible con equivalenti pure-Python, invocati tramite chiamate di procedura remota ad interpreti persistenti tunnellati su SSH. Il risultato e un incremento di velocita da 1.25x a 7x rispetto all'esecuzione standard, con riduzione dell'utilizzo CPU di almeno 2x.

```bash
# Installazione
pip install mitogen

# ansible.cfg
[defaults]
strategy_plugins = /path/to/mitogen/ansible_mitogen/plugins/strategy
strategy = mitogen_linear
```

**Benchmark tipico**: un playbook che impiega 68 secondi in modalita standard scende a circa 8 secondi con Mitogen — un miglioramento dell'88%. Il vantaggio e massimo con task ripetitivi su molti host.

**Limitazioni**: Mitogen puo avere problemi di compatibilita con alcune versioni di ansible-core. Verificare la matrice di compatibilita prima dell'adozione. Non supporta tutti i connection plugin (es: `network_cli`).

### Fork e Parallelismo

Il parametro `forks` controlla quanti host vengono configurati in parallelo. Il default e 5, troppo basso per flotte medie:

```ini
# ansible.cfg
[defaults]
forks = 50          # 25-50 per flotte medie, 100+ per grandi
```

```bash
# Override da riga di comando
ansible-playbook site.yml -f 50
```

**Regola empirica**: impostare forks pari al numero di CPU del control node moltiplicato per 5, senza superare il numero totale di host. Monitorare l'utilizzo di memoria e CPU del control node durante l'esecuzione.

### Fact Caching

Il gathering dei fatti (`setup` module) puo richiedere 5-10 secondi per host. Con il caching, i fatti vengono raccolti una sola volta e riutilizzati nelle esecuzioni successive:

```ini
# ansible.cfg
[defaults]
gathering = smart                    # Raccoglie solo se non in cache
fact_caching = jsonfile              # Backend: jsonfile, redis, memcached
fact_caching_connection = /tmp/ansible_fact_cache
fact_caching_timeout = 3600          # Scadenza cache in secondi
```

**Backend Redis** per ambienti multi-operatore:

```ini
[defaults]
fact_caching = redis
fact_caching_connection = localhost:6379:0
fact_caching_timeout = 7200
```

Per playbook che non necessitano di fatti (es: solo copia file), disabilitare completamente il gathering:

```yaml
- name: Deploy veloce
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Copia configurazione
      copy:
        src: app.conf
        dest: /etc/app/app.conf
```

### Task Asincroni

I task asincroni permettono di lanciare operazioni lunghe senza bloccare il playbook. Il parametro `async` imposta il timeout massimo, `poll` controlla l'intervallo di polling (0 = fire-and-forget):

```yaml
- name: Aggiornamento pacchetti (asincrono)
  apt:
    upgrade: dist
    update_cache: yes
  async: 3600          # Timeout 1 ora
  poll: 0              # Non attendere
  register: apt_job

- name: Altre operazioni indipendenti...
  debug:
    msg: "Eseguito mentre apt lavora in background"

- name: Attendi completamento aggiornamento
  async_status:
    jid: "{{ apt_job.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 60
  delay: 60
```

### Strategy Plugin

Ansible supporta diverse strategie di esecuzione che cambiano come i task vengono distribuiti tra gli host:

```ini
# ansible.cfg
[defaults]
strategy = free        # Ogni host procede indipendentemente
# strategy = linear    # Default: tutti gli host completano il task prima del successivo
# strategy = debug     # Interattivo per debugging
```

**`free` strategy**: ogni host procede al task successivo appena completa il corrente, senza attendere gli altri. Ideale per flotte eterogenee dove alcuni host sono piu veloci. Non adatta quando l'ordine dei task tra host e importante.

**`linear` strategy** (default): tutti gli host devono completare il task corrente prima che qualsiasi host inizi il successivo. Garantisce ordine ma e piu lenta su flotte grandi.

### Callback Plugin per Profiling

I callback plugin permettono di identificare i task piu lenti e ottimizzare selettivamente:

```ini
# ansible.cfg
[defaults]
callbacks_enabled = ansible.posix.profile_tasks, ansible.posix.timer

# Output esempio:
# Wednesday 22 May 2026  03:15:00 +0200 (0:00:32.456) 0:05:12.789 ****
# Installa pacchetti ------------------------------------------ 32.46s
# Deploy configurazione --------------------------------------- 12.11s
# Hardening SSH ------------------------------------------------ 3.22s
```

### Riepilogo Ottimizzazioni

| Tecnica | Impatto | Complessita |
|---------|---------|-------------|
| Pipelining SSH | 30-50% | Bassa |
| Mitogen | 125-700% | Media |
| Forks >5 | 20-80% | Bassa |
| Fact caching | 10-40% | Bassa |
| `gather_facts: false` | 5-15% per play | Bassa |
| Task asincroni | Variabile | Media |
| Strategy `free` | 20-60% | Bassa |
| Profile callback | Diagnostico | Bassa |

**Pipeline di ottimizzazione consigliata**: (1) abilitare pipelining SSH, (2) aumentare forks, (3) abilitare fact caching, (4) disabilitare gathering dove non necessario, (5) valutare Mitogen per ambienti compatibili, (6) usare async per task lunghi indipendenti.

---

## Confronto Configuration Management

| Caratteristica | **Ansible** | **Puppet** | **Chef** | **Salt** |
|----------------|-------------|------------|----------|----------|
| **Architettura** | Agentless (SSH) | Agent-based (pull) | Agent-based (pull) | Agent o agentless |
| **Linguaggio** | YAML (dichiarativo) | DSL Puppet (dichiarativo) | Ruby DSL (imperativo) | YAML + Jinja (dichiarativo) |
| **Curva di apprendimento** | Bassa | Media | Alta | Media |
| **Scalabilita** | Buona (< 5000 nodi) | Eccellente | Eccellente | Eccellente |
| **Idempotenza** | Moduli nativi | Core del linguaggio | Risorse convergenti | Moduli nativi |
| **Comunita** | Molto grande | Grande | Media | Media |
| **Caso d'uso ideale** | Config management, orchestrazione, provisioning | Grandi flotte enterprise, compliance | Infrastrutture complesse cloud-native | Grandi flotte, esecuzione remota |
| **Gestione secret** | Vault integrato | Hiera + eyaml | Data bags criptati | Pillar criptato |
| **Orchestrazione** | Nativa | MCollective/Bolt | Chef Automate | Nativa (eccellente) |
| **Testing** | Molecule | rspec-puppet, Beaker | Test Kitchen, InSpec | Kitchen-salt |
| **Installazione server** | Nessuna | Puppet Server | Chef Server | Salt Master |

**Quando scegliere cosa:**

- **Ansible**: team piccolo-medio, infrastruttura mista, primo approccio a IaC, orchestrazione multi-step
- **Puppet**: enterprise con migliaia di nodi, compliance rigorosa, team dedicato
- **Chef**: team con esperienza Ruby, infrastruttura cloud complessa, forte testing culture
- **Salt**: necessita di esecuzione remota real-time, grandi flotte, event-driven automation

```bash
# Esempio equivalente: installare nginx

# --- Ansible ---
# playbook.yml
- apt:
    name: nginx
    state: present

# --- Puppet ---
# manifests/nginx.pp
package { 'nginx':
  ensure => installed,
}

# --- Chef ---
# recipes/nginx.rb
package 'nginx' do
  action :install
end

# --- Salt ---
# states/nginx.sls
nginx:
  pkg.installed
```

---

## Ansible Molecule: Testing dei Ruoli

Molecule e il framework standard per testare ruoli e collezioni Ansible in ambienti isolati. Supporta multiple driver (Docker, Podman, Vagrant, cloud provider), esegue lint, converge, idempotency check e verifica, e si integra nativamente con pipeline CI/CD.

### Installazione e Inizializzazione

```bash
# Installazione con driver Docker (piu comune)
pip install molecule molecule-plugins[docker]

# Oppure con Podman (rootless, piu sicuro)
pip install molecule molecule-plugins[podman]

# Inizializzare testing per un ruolo esistente
cd roles/mio-ruolo/
molecule init scenario -d docker

# Inizializzare un ruolo nuovo con Molecule gia configurato
molecule init role mio_namespace.mio_ruolo -d docker
```

La struttura generata:

```
roles/mio-ruolo/
├── molecule/
│   └── default/              # Scenario "default"
│       ├── molecule.yml      # Configurazione scenario
│       ├── converge.yml      # Playbook di convergenza
│       ├── verify.yml        # Playbook di verifica
│       ├── prepare.yml       # Preparazione pre-converge (opzionale)
│       └── cleanup.yml       # Pulizia post-test (opzionale)
├── tasks/
├── handlers/
├── defaults/
├── meta/
└── ...
```

### Configurazione molecule.yml

```yaml
# molecule/default/molecule.yml
---
dependency:
  name: galaxy
  options:
    requirements-file: requirements.yml

driver:
  name: docker

platforms:
  - name: instance-ubuntu
    image: geerlingguy/docker-ubuntu2404-ansible
    pre_build_image: true
    privileged: true               # Necessario per systemd
    command: /lib/systemd/systemd
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host

  - name: instance-rocky
    image: geerlingguy/docker-rockylinux9-ansible
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd

provisioner:
  name: ansible
  config_options:
    defaults:
      callbacks_enabled: profile_tasks
  inventory:
    host_vars:
      instance-ubuntu:
        ansible_python_interpreter: /usr/bin/python3
      instance-rocky:
        ansible_python_interpreter: /usr/bin/python3

verifier:
  name: ansible    # Default: verifica con playbook Ansible
  # In alternativa: testinfra (Python)
  # name: testinfra

scenario:
  test_sequence:
    - dependency
    - lint
    - cleanup
    - destroy
    - syntax
    - create
    - prepare
    - converge
    - idempotence       # Riesegue converge e verifica zero "changed"
    - side_effect
    - verify
    - cleanup
    - destroy
```

### Lifecycle dei Comandi

```bash
# Ciclo completo di test (tutta la sequenza)
molecule test

# Solo convergenza (utile durante sviluppo)
molecule converge

# Verifica senza ricreare
molecule verify

# Login nel container per debug
molecule login --host instance-ubuntu

# Idempotency check separato
molecule idempotence

# Destroy ambienti
molecule destroy

# Reset completo
molecule reset

# Lista scenari disponibili
molecule list

# Eseguire uno scenario specifico
molecule test -s scenario-avanzato
```

### Converge e Verify Playbook

```yaml
# molecule/default/converge.yml
---
- name: Converge
  hosts: all
  become: true

  pre_tasks:
    - name: Aggiorna cache apt
      ansible.builtin.apt:
        update_cache: true
      when: ansible_os_family == "Debian"

  roles:
    - role: mio_namespace.mio_ruolo
      vars:
        http_port: 8080
        enable_ssl: false
```

```yaml
# molecule/default/verify.yml
---
- name: Verify
  hosts: all
  gather_facts: false
  become: true

  tasks:
    - name: Verifica che nginx sia installato
      ansible.builtin.package:
        name: nginx
        state: present
      check_mode: true
      register: pkg_check
      failed_when: pkg_check.changed

    - name: Verifica che nginx sia in esecuzione
      ansible.builtin.service:
        name: nginx
        state: started
      check_mode: true
      register: svc_check
      failed_when: svc_check.changed

    - name: Verifica porta in ascolto
      ansible.builtin.wait_for:
        port: 8080
        timeout: 5

    - name: Verifica configurazione nginx
      ansible.builtin.command: nginx -t
      changed_when: false
      register: nginx_test
      failed_when: nginx_test.rc != 0

    - name: Verifica contenuto pagina
      ansible.builtin.uri:
        url: "http://localhost:8080"
        return_content: true
      register: page
      failed_when: "'Welcome' not in page.content"
```

### Verifica con Testinfra (Python)

Per verifiche piu complesse, Testinfra offre un'API Python ricca:

```python
# molecule/default/tests/test_default.py
import pytest

def test_nginx_is_installed(host):
    nginx = host.package("nginx")
    assert nginx.is_installed

def test_nginx_running_and_enabled(host):
    nginx = host.service("nginx")
    assert nginx.is_running
    assert nginx.is_enabled

def test_nginx_listening(host):
    socket = host.socket("tcp://0.0.0.0:8080")
    assert socket.is_listening

def test_nginx_config_valid(host):
    cmd = host.run("nginx -t")
    assert cmd.rc == 0

def test_config_file_exists(host):
    f = host.file("/etc/nginx/nginx.conf")
    assert f.exists
    assert f.user == "root"
    assert f.mode == 0o644

def test_no_default_page(host):
    """Verifica che la pagina default sia stata rimossa"""
    f = host.file("/var/www/html/index.nginx-debian.html")
    assert not f.exists
```

### Multi-Scenario

Scenari multipli permettono di testare configurazioni diverse dello stesso ruolo:

```bash
# Creare scenario aggiuntivo
molecule init scenario -s con-ssl -d docker
molecule init scenario -s cluster -d docker
```

```yaml
# molecule/con-ssl/converge.yml
---
- name: Converge con SSL
  hosts: all
  become: true
  roles:
    - role: mio_namespace.mio_ruolo
      vars:
        enable_ssl: true
        ssl_cert_path: /etc/ssl/certs/test.pem
        ssl_key_path: /etc/ssl/private/test.key
```

### Integrazione CI/CD

```yaml
# .gitlab-ci.yml
molecule_test:
  stage: test
  image: python:3.12-slim
  services:
    - docker:dind
  variables:
    DOCKER_HOST: tcp://docker:2375
    PY_COLORS: "1"
    ANSIBLE_FORCE_COLOR: "1"
  before_script:
    - pip install molecule molecule-plugins[docker] ansible-core
  script:
    - cd roles/mio-ruolo
    - molecule test --all    # Esegue tutti gli scenari
  rules:
    - changes:
        - roles/mio-ruolo/**/*
```

```yaml
# GitHub Actions equivalente
name: Molecule Test
on:
  push:
    paths: ['roles/**']
  pull_request:
    paths: ['roles/**']

jobs:
  molecule:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        scenario: [default, con-ssl]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install molecule molecule-plugins[docker] ansible-core
      - run: molecule test -s ${{ matrix.scenario }}
        working-directory: roles/mio-ruolo
```

**Best practice Molecule:**

- Usare `pre_build_image: true` con immagini gia preparate per velocizzare i test
- Testare sempre l'idempotenza (due convergenze consecutive, zero changed)
- Usare immagini di Jeff Geerling (`geerlingguy/docker-*-ansible`) per container con systemd funzionante
- Separare scenari per varianti significative (SSL/no-SSL, cluster/standalone)
- In CI, eseguire `molecule test --all` per coprire tutti gli scenari
- Usare `molecule converge` durante lo sviluppo iterativo, `molecule test` per validazione completa

### Molecule: Prepare e Cleanup

Il playbook `prepare.yml` esegue setup necessario prima della convergenza (installare dipendenze, creare directory, configurare prerequisiti non gestiti dal ruolo sotto test):

```yaml
# molecule/default/prepare.yml
---
- name: Prepare
  hosts: all
  become: true
  tasks:
    - name: Installa prerequisiti non gestiti dal ruolo
      ansible.builtin.apt:
        name:
          - python3-pip
          - ca-certificates
          - curl
        state: present
        update_cache: true
      when: ansible_os_family == "Debian"

    - name: Crea directory per certificati di test
      ansible.builtin.file:
        path: /etc/ssl/test-certs
        state: directory
        mode: '0755'

    - name: Genera certificato self-signed per test SSL
      ansible.builtin.command:
        cmd: >-
          openssl req -x509 -nodes -days 365
          -newkey rsa:2048
          -keyout /etc/ssl/test-certs/test.key
          -out /etc/ssl/test-certs/test.crt
          -subj "/CN=test.local"
        creates: /etc/ssl/test-certs/test.crt
```

Il playbook `cleanup.yml` pulisce risorse esterne create durante il test (utile quando il test interagisce con servizi reali):

```yaml
# molecule/default/cleanup.yml
---
- name: Cleanup
  hosts: all
  become: true
  tasks:
    - name: Rimuovi entry DNS temporanee
      ansible.builtin.lineinfile:
        path: /etc/hosts
        regexp: 'test\.local'
        state: absent

    - name: Pulisci artefatti di test
      ansible.builtin.file:
        path: "{{ item }}"
        state: absent
      loop:
        - /tmp/test-artifacts
        - /etc/ssl/test-certs
```

### Molecule: Side Effect e Debug

Il playbook `side_effect.yml` simula condizioni esterne (es. failover, cambio configurazione) per testare la resilienza del ruolo:

```yaml
# molecule/default/side_effect.yml
---
- name: Side Effect - Simula failover
  hosts: all
  become: true
  tasks:
    - name: Ferma il servizio per simulare crash
      ansible.builtin.service:
        name: nginx
        state: stopped

    - name: Corrompi configurazione
      ansible.builtin.copy:
        content: "INVALID CONFIG"
        dest: /etc/nginx/sites-enabled/default
        mode: '0644'
```

Dopo il side effect, Molecule riesegue converge per verificare che il ruolo ripristini lo stato corretto — test di self-healing.

### Molecule: Matrice di Test Multi-Piattaforma

```yaml
# molecule/default/molecule.yml — test su 4 distribuzioni
platforms:
  - name: ubuntu-2404
    image: geerlingguy/docker-ubuntu2404-ansible
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd

  - name: ubuntu-2204
    image: geerlingguy/docker-ubuntu2204-ansible
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd

  - name: rocky-9
    image: geerlingguy/docker-rockylinux9-ansible
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd

  - name: debian-12
    image: geerlingguy/docker-debian12-ansible
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd
```

**Confronto verifier:**

| Verifier | Linguaggio | Vantaggi | Svantaggi |
|----------|-----------|----------|-----------|
| **ansible** (default) | YAML | Nessuna dipendenza extra, same language | Meno espressivo per asserzioni complesse |
| **testinfra** | Python | API ricca, pytest, facile da estendere | Richiede Python, dipendenza aggiuntiva |

---

## Terraform per Linux

Terraform gestisce il provisioning di VM e infrastruttura, non la configurazione interna (quella e Ansible).

```hcl
# main.tf - Esempio: VM su Proxmox
terraform {
  required_providers {
    proxmox = {
      source = "telmate/proxmox"
    }
  }
}

provider "proxmox" {
  pm_api_url      = "https://proxmox:8006/api2/json"
  pm_user         = "root@pam"
  pm_password     = var.proxmox_password
  pm_tls_insecure = true
}

resource "proxmox_vm_qemu" "web_server" {
  name        = "web-server-01"
  target_node = "pve"
  clone       = "ubuntu-template"

  cores   = 2
  memory  = 4096
  sockets = 1

  disk {
    size    = "40G"
    type    = "scsi"
    storage = "local-lvm"
  }

  network {
    model  = "virtio"
    bridge = "vmbr0"
  }

  ipconfig0 = "ip=10.0.0.100/24,gw=10.0.0.1"

  lifecycle {
    ignore_changes = [network]
  }
}
```

```bash
terraform init                              # Inizializza
terraform plan                              # Mostra cosa fara
terraform apply                             # Applica
terraform destroy                           # Distruggi
terraform state list                        # Lista risorse
```

**Terraform con output per Ansible** — pipeline completa:

```hcl
# outputs.tf
output "web_server_ip" {
  value = proxmox_vm_qemu.web_server.default_ipv4_address
}

# Generare inventario Ansible automaticamente
resource "local_file" "ansible_inventory" {
  content = templatefile("inventory.tftpl", {
    web_servers = proxmox_vm_qemu.web_server[*].default_ipv4_address
    db_servers  = proxmox_vm_qemu.db_server[*].default_ipv4_address
  })
  filename = "${path.module}/generated-inventory.ini"
}
```

```bash
# Pipeline: Terraform crea, Ansible configura
terraform apply -auto-approve
ansible-playbook -i generated-inventory.ini site.yml
```

### Pattern di Integrazione Terraform + Ansible

La separazione e chiara: Terraform provisiona l'infrastruttura (VM, reti, dischi, DNS), Ansible configura il software all'interno. Esistono diversi pattern per collegare i due.

**Pattern 1: null_resource con local-exec** — Terraform invoca Ansible come post-provisioning:

```hcl
# provisioner.tf
resource "null_resource" "ansible_provisioner" {
  depends_on = [proxmox_vm_qemu.web_server]

  # Ri-esegui quando l'IP cambia
  triggers = {
    server_ip = proxmox_vm_qemu.web_server.default_ipv4_address
  }

  # Attendi che SSH sia disponibile
  provisioner "remote-exec" {
    inline = ["echo 'SSH pronto'"]
    connection {
      host        = proxmox_vm_qemu.web_server.default_ipv4_address
      user        = "admin"
      private_key = file("~/.ssh/id_ed25519")
      timeout     = "3m"
    }
  }

  # Esegui Ansible dopo che SSH e pronto
  provisioner "local-exec" {
    command = <<-EOT
      ANSIBLE_HOST_KEY_CHECKING=False \
      ansible-playbook -i '${proxmox_vm_qemu.web_server.default_ipv4_address},' \
        -u admin --private-key ~/.ssh/id_ed25519 \
        playbooks/configure-webserver.yml \
        -e "http_port=8080 env=production"
    EOT
  }
}
```

**Pattern 2: terraform-inventory** — inventario dinamico dal state Terraform:

```bash
# Installare terraform-inventory
# https://github.com/adammck/terraform-inventory
wget https://github.com/adammck/terraform-inventory/releases/latest/download/terraform-inventory_linux_amd64
chmod +x terraform-inventory_linux_amd64
sudo mv terraform-inventory_linux_amd64 /usr/local/bin/terraform-inventory

# Usare come inventario dinamico
TF_STATE=./terraform.tfstate ansible-playbook \
  -i /usr/local/bin/terraform-inventory \
  site.yml
```

**Pattern 3: generazione inventario da output** — piu flessibile e mantenibile:

```hcl
# inventory.tftpl — template per inventario Ansible
[webservers]
%{ for ip in web_ips ~}
${ip} ansible_user=admin ansible_ssh_private_key_file=~/.ssh/id_ed25519
%{ endfor ~}

[dbservers]
%{ for ip in db_ips ~}
${ip} ansible_user=admin ansible_ssh_private_key_file=~/.ssh/id_ed25519
%{ endfor ~}

[all:vars]
ansible_python_interpreter=/usr/bin/python3
env=${environment}
```

```hcl
# outputs.tf
resource "local_file" "inventory" {
  content = templatefile("inventory.tftpl", {
    web_ips     = proxmox_vm_qemu.web[*].default_ipv4_address
    db_ips      = proxmox_vm_qemu.db[*].default_ipv4_address
    environment = var.environment
  })
  filename        = "${path.module}/inventory-${var.environment}.ini"
  file_permission = "0644"
}
```

**Pattern 4: pipeline CI/CD completa** — orchestrazione in GitLab CI o GitHub Actions:

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - provision
  - configure
  - verify

terraform_validate:
  stage: validate
  image: hashicorp/terraform:1.8
  script:
    - terraform init -backend-config=backend.hcl
    - terraform validate
    - terraform plan -out=plan.bin
  artifacts:
    paths: [plan.bin, inventory-*.ini]

terraform_apply:
  stage: provision
  image: hashicorp/terraform:1.8
  script:
    - terraform init -backend-config=backend.hcl
    - terraform apply plan.bin
  artifacts:
    paths: [inventory-*.ini, terraform.tfstate]
  when: manual    # Approvazione manuale per apply

ansible_configure:
  stage: configure
  image: python:3.12-slim
  needs: [terraform_apply]
  before_script:
    - pip install ansible-core
    - ansible-galaxy install -r requirements.yml
  script:
    - ansible-playbook -i inventory-${CI_ENVIRONMENT_NAME}.ini site.yml
  environment:
    name: $CI_ENVIRONMENT_NAME

smoke_test:
  stage: verify
  needs: [ansible_configure]
  script:
    - ansible-playbook -i inventory-${CI_ENVIRONMENT_NAME}.ini playbooks/smoke-test.yml
```

**Convenzione per separazione responsabilita:**

| Responsabilita | Strumento | Esempi |
|---------------|-----------|--------|
| Infrastruttura | Terraform | VM, reti, dischi, DNS, load balancer |
| Configurazione OS | Ansible | Pacchetti, utenti, firewall, hardening |
| Deploy applicativo | Ansible | Container, servizi, certificati |
| Secret runtime | HashiCorp Vault | Credenziali DB, API key, certificati |

**Anti-pattern da evitare nell'integrazione Terraform + Ansible:**

- Non usare `remote-exec` per configurazione complessa — e fragile, senza idempotenza, e duplica logica che appartiene ad Ansible
- Non gestire pacchetti software con Terraform `user_data` — usare cloud-init per il bootstrap minimo, poi Ansible per la configurazione completa
- Non hardcodare IP negli inventari statici — generare sempre l'inventario da Terraform output o usare inventari dinamici
- Non eseguire `terraform destroy` e `terraform apply` nella stessa pipeline senza conferma manuale — il destroy e distruttivo e irreversibile
- Non mischiare state Terraform tra ambienti — usare workspace o backend separati per dev/staging/prod

---

## Cloud-init: Provisioning

Cloud-init e lo standard per la configurazione iniziale di istanze cloud e VM.

```yaml
# cloud-init.yml (user-data)
#cloud-config
hostname: web-server-01
manage_etc_hosts: true
timezone: Europe/Rome

users:
  - name: admin
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... admin@workstation

packages:
  - nginx
  - htop
  - fail2ban
  - ufw

package_update: true
package_upgrade: true

write_files:
  - path: /etc/nginx/sites-available/default
    content: |
      server {
          listen 80;
          root /var/www/html;
          index index.html;
      }

runcmd:
  - systemctl enable --now nginx
  - ufw allow 22/tcp
  - ufw allow 80/tcp
  - ufw --force enable
  - systemctl enable --now fail2ban

final_message: "Cloud-init completed in $UPTIME seconds"
```

```bash
# Verificare cloud-init su una VM
cloud-init status                           # Stato
cloud-init status --wait                    # Aspetta completamento
cat /var/log/cloud-init.log                 # Log
cat /var/log/cloud-init-output.log          # Output comandi

# Per VM locali (libvirt)
virt-install --cloud-init user-data=cloud-init.yml ...
```

**Cloud-init avanzato** — partizioni, mount, script custom:

```yaml
#cloud-config
disk_setup:
  /dev/sdb:
    table_type: gpt
    layout: true
    overwrite: false

fs_setup:
  - label: data
    filesystem: ext4
    device: /dev/sdb1

mounts:
  - [/dev/sdb1, /mnt/data, ext4, "defaults,noatime", "0", "2"]

# Configurazione SSH hardening
ssh_pwauth: false
disable_root: true

ssh_keys:
  ed25519_private: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    ...
    -----END OPENSSH PRIVATE KEY-----
  ed25519_public: ssh-ed25519 AAAA...

# Esecuzione script
bootcmd:
  - echo "Fase boot" >> /var/log/cloud-init-custom.log

runcmd:
  - |
    #!/bin/bash
    set -euo pipefail
    # Script complesso inline
    apt-get update
    apt-get install -y docker.io
    systemctl enable --now docker
    usermod -aG docker admin

phone_home:
  url: https://provisioning.esempio.it/callback
  post:
    - instance_id
    - hostname
    - fqdn
```

---

## Patching Automatizzato

### unattended-upgrades (Debian/Ubuntu)

```bash
# Installazione
sudo apt install unattended-upgrades apt-listchanges

# Configurazione interattiva
sudo dpkg-reconfigure -plow unattended-upgrades
```

```bash
# /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}:${distro_codename}-updates";
    // "${distro_id}:${distro_codename}-proposed";
};

// Pacchetti da NON aggiornare
Unattended-Upgrade::Package-Blacklist {
    "linux-image*";
    "linux-headers*";
    "postgresql*";
    "mysql-server*";
};

// Riavvio automatico se necessario
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";

// Notifica via mail
Unattended-Upgrade::Mail "admin@esempio.it";
Unattended-Upgrade::MailReport "on-change";

// Rimuovi dipendenze non necessarie
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";

// Limita banda (KB/s)
Acquire::http::Dl-Limit "1000";
```

```bash
# /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Download-Upgradeable-Packages "1";
```

```bash
# Test (dry-run)
sudo unattended-upgrades --dry-run --debug

# Esecuzione manuale
sudo unattended-upgrades -v

# Log
cat /var/log/unattended-upgrades/unattended-upgrades.log
cat /var/log/unattended-upgrades/unattended-upgrades-dpkg.log
```

### dnf-automatic (RHEL/Fedora)

```bash
# Installazione
sudo dnf install dnf-automatic

# Configurazione
sudo vi /etc/dnf/automatic.conf
```

```ini
# /etc/dnf/automatic.conf
[commands]
# Cosa fare: download, apply, notify
apply_updates = yes
upgrade_type = security      # solo security, oppure "default" per tutti

[emitters]
emit_via = email,stdio

[email]
email_from = root@server.esempio.it
email_to = admin@esempio.it
email_host = localhost

[command_email]
# Alternativa: inviare output via comando
# email_command = /usr/bin/mail -s "DNF Automatic" admin@esempio.it
```

```bash
# Abilitare il timer
sudo systemctl enable --now dnf-automatic-install.timer

# Varianti di timer disponibili:
# dnf-automatic.timer              - solo download
# dnf-automatic-install.timer      - download + install
# dnf-automatic-notifyonly.timer   - solo notifica

# Verificare
systemctl list-timers | grep dnf

# Test manuale
sudo dnf-automatic
```

### Scheduling e esclusioni

**Con Ansible — patching orchestrato su flotta:**

```yaml
# patch-servers.yml
---
- name: Patching server con rolling update
  hosts: webservers
  serial: 1                          # Un server alla volta
  become: yes
  max_fail_percentage: 0             # Ferma se un server fallisce

  tasks:
    - name: Rimuovi dal load balancer
      uri:
        url: "https://lb.interno/api/pool/{{ inventory_hostname }}"
        method: DELETE
      delegate_to: localhost

    - name: Attendi drain connessioni
      pause:
        seconds: 30

    - name: Aggiorna pacchetti security
      apt:
        upgrade: safe
        update_cache: yes
      register: upgrade_result

    - name: Riavvia se necessario
      reboot:
        reboot_timeout: 300
      when: upgrade_result.changed

    - name: Verifica servizi
      wait_for:
        port: 80
        timeout: 60

    - name: Riaggiungi al load balancer
      uri:
        url: "https://lb.interno/api/pool/{{ inventory_hostname }}"
        method: PUT
      delegate_to: localhost

    - name: Verifica health check
      uri:
        url: "http://{{ inventory_hostname }}/health"
        status_code: 200
      retries: 5
      delay: 10
```

---

## Monitoring Automatizzato

Deploy script-driven di Prometheus + Grafana con Ansible.

```yaml
# roles/prometheus/tasks/main.yml
---
- name: Crea utente prometheus
  user:
    name: prometheus
    system: yes
    shell: /usr/sbin/nologin
    create_home: no

- name: Crea directory
  file:
    path: "{{ item }}"
    state: directory
    owner: prometheus
    group: prometheus
    mode: '0755'
  loop:
    - /etc/prometheus
    - /var/lib/prometheus

- name: Download Prometheus
  get_url:
    url: "https://github.com/prometheus/prometheus/releases/download/v{{ prometheus_version }}/prometheus-{{ prometheus_version }}.linux-amd64.tar.gz"
    dest: /tmp/prometheus.tar.gz
    checksum: "sha256:{{ prometheus_checksum }}"

- name: Estrai Prometheus
  unarchive:
    src: /tmp/prometheus.tar.gz
    dest: /tmp/
    remote_src: yes

- name: Installa binari
  copy:
    src: "/tmp/prometheus-{{ prometheus_version }}.linux-amd64/{{ item }}"
    dest: "/usr/local/bin/{{ item }}"
    remote_src: yes
    mode: '0755'
  loop:
    - prometheus
    - promtool

- name: Deploy configurazione
  template:
    src: prometheus.yml.j2
    dest: /etc/prometheus/prometheus.yml
    owner: prometheus
    group: prometheus
    validate: promtool check config %s
  notify: Restart Prometheus

- name: Deploy systemd unit
  template:
    src: prometheus.service.j2
    dest: /etc/systemd/system/prometheus.service
  notify:
    - Reload systemd
    - Restart Prometheus

- name: Avvia Prometheus
  systemd:
    name: prometheus
    state: started
    enabled: yes
    daemon_reload: yes
```

```yaml
# templates/prometheus.yml.j2
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/rules/*.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node'
    static_configs:
      - targets:
{% for host in groups['all'] %}
          - '{{ hostvars[host].ansible_host }}:9100'
{% endfor %}

  - job_name: 'nginx'
    static_configs:
      - targets:
{% for host in groups['webservers'] %}
          - '{{ hostvars[host].ansible_host }}:9113'
{% endfor %}
```

```yaml
# roles/grafana/tasks/main.yml
---
- name: Aggiungi repository Grafana
  apt_repository:
    repo: "deb https://packages.grafana.com/oss/deb stable main"
    state: present
    filename: grafana

- name: Aggiungi chiave GPG Grafana
  apt_key:
    url: https://packages.grafana.com/gpg.key
    state: present

- name: Installa Grafana
  apt:
    name: grafana
    state: present
    update_cache: yes

- name: Deploy configurazione
  template:
    src: grafana.ini.j2
    dest: /etc/grafana/grafana.ini
  notify: Restart Grafana

- name: Provisioning datasource Prometheus
  copy:
    content: |
      apiVersion: 1
      datasources:
        - name: Prometheus
          type: prometheus
          access: proxy
          url: http://{{ prometheus_host }}:9090
          isDefault: true
    dest: /etc/grafana/provisioning/datasources/prometheus.yml
  notify: Restart Grafana

- name: Avvia Grafana
  systemd:
    name: grafana-server
    state: started
    enabled: yes
```

---

## User Provisioning Automatizzato

Gestione automatica del ciclo di vita degli utenti: creazione, modifica, disabilitazione, rimozione.

```yaml
# user-provisioning.yml
---
- name: User provisioning automatizzato
  hosts: all
  become: yes

  vars_files:
    - users.yml

  tasks:
    # --- Utenti attivi ---
    - name: Crea gruppi
      group:
        name: "{{ item }}"
        state: present
      loop: "{{ user_groups | default([]) }}"

    - name: Crea utenti attivi
      user:
        name: "{{ item.username }}"
        uid: "{{ item.uid | default(omit) }}"
        group: "{{ item.primary_group | default(omit) }}"
        groups: "{{ item.groups | default([]) | join(',') }}"
        shell: "{{ item.shell | default('/bin/bash') }}"
        home: "/home/{{ item.username }}"
        create_home: yes
        state: present
        password: "{{ item.password_hash | default('!') }}"
        comment: "{{ item.full_name | default('') }}"
      loop: "{{ active_users }}"
      loop_control:
        label: "{{ item.username }}"

    - name: Deploy chiavi SSH
      authorized_key:
        user: "{{ item.username }}"
        key: "{{ item.ssh_key }}"
        exclusive: yes
        state: present
      loop: "{{ active_users }}"
      when: item.ssh_key is defined
      loop_control:
        label: "{{ item.username }}"

    - name: Configura sudo
      copy:
        content: "{{ item.username }} {{ item.sudo_spec }}\n"
        dest: "/etc/sudoers.d/{{ item.username }}"
        mode: '0440'
        validate: visudo -cf %s
      loop: "{{ active_users }}"
      when: item.sudo_spec is defined
      loop_control:
        label: "{{ item.username }}"

    # --- Utenti da disabilitare ---
    - name: Disabilita utenti
      user:
        name: "{{ item }}"
        shell: /usr/sbin/nologin
        password: '!'
        expires: 0
      loop: "{{ disabled_users | default([]) }}"

    - name: Termina sessioni utenti disabilitati
      command: "pkill -u {{ item }}"
      loop: "{{ disabled_users | default([]) }}"
      failed_when: false
      changed_when: false

    # --- Utenti da rimuovere ---
    - name: Rimuovi utenti
      user:
        name: "{{ item }}"
        state: absent
        remove: yes
      loop: "{{ removed_users | default([]) }}"

    - name: Rimuovi sudoers rimossi
      file:
        path: "/etc/sudoers.d/{{ item }}"
        state: absent
      loop: "{{ removed_users | default([]) }}"
```

```yaml
# users.yml
---
user_groups:
  - developers
  - operators
  - dbadmins

active_users:
  - username: mario.rossi
    uid: 2001
    full_name: "Mario Rossi"
    primary_group: developers
    groups: [sudo, docker]
    ssh_key: "ssh-ed25519 AAAA... mario@workstation"
    sudo_spec: "ALL=(ALL) NOPASSWD:ALL"

  - username: anna.bianchi
    uid: 2002
    full_name: "Anna Bianchi"
    primary_group: operators
    groups: [docker]
    ssh_key: "ssh-ed25519 AAAA... anna@workstation"

disabled_users:
  - ex.dipendente

removed_users:
  - vecchio.account
```

**Integrazione LDAP/AD** — autenticazione centralizzata:

```yaml
# roles/ldap-client/tasks/main.yml
---
- name: Installa pacchetti SSSD
  apt:
    name:
      - sssd
      - sssd-ldap
      - sssd-tools
      - libpam-sss
      - libnss-sss
    state: present

- name: Configura SSSD
  template:
    src: sssd.conf.j2
    dest: /etc/sssd/sssd.conf
    owner: root
    group: root
    mode: '0600'
  notify: Restart SSSD

- name: Configura PAM per SSSD
  command: pam-auth-update --enable sss --force
  changed_when: false

- name: Configura NSS
  lineinfile:
    path: /etc/nsswitch.conf
    regexp: "^{{ item.db }}:"
    line: "{{ item.db }}:         files sss"
  loop:
    - { db: passwd }
    - { db: group }
    - { db: shadow }

- name: Abilita creazione home directory automatica
  lineinfile:
    path: /etc/pam.d/common-session
    line: "session optional pam_mkhomedir.so skel=/etc/skel umask=077"
    insertafter: "session.*pam_sss.so"

- name: Avvia SSSD
  systemd:
    name: sssd
    state: started
    enabled: yes
```

```ini
# templates/sssd.conf.j2
[sssd]
domains = {{ ldap_domain }}
services = nss, pam, sudo
config_file_version = 2

[nss]
filter_groups = root
filter_users = root

[pam]
offline_credentials_expiration = 7

[domain/{{ ldap_domain }}]
id_provider = ldap
auth_provider = ldap
ldap_uri = ldaps://{{ ldap_server }}
ldap_search_base = {{ ldap_base_dn }}
ldap_tls_reqcert = demand
ldap_tls_cacert = /etc/ssl/certs/ca-certificates.crt

# Mapping attributi
ldap_user_search_base = ou=users,{{ ldap_base_dn }}
ldap_group_search_base = ou=groups,{{ ldap_base_dn }}
ldap_user_object_class = posixAccount
ldap_group_object_class = posixGroup

# Cache
cache_credentials = true
entry_cache_timeout = 300

# Accesso
access_provider = ldap
ldap_access_filter = (memberOf=cn=linux-users,ou=groups,{{ ldap_base_dn }})

# Sudo
sudo_provider = ldap
ldap_sudo_search_base = ou=sudoers,{{ ldap_base_dn }}
```

---

## Security Scanning Automatizzato

### Lynis — audit di sicurezza

```bash
#!/bin/bash
# security-scan-lynis.sh - scansione automatizzata con Lynis
set -euo pipefail

REPORT_DIR="/var/log/security-scans"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="${REPORT_DIR}/lynis-${TIMESTAMP}.log"

mkdir -p "$REPORT_DIR"

# Aggiorna Lynis se installato via Git
if [ -d /opt/lynis/.git ]; then
    cd /opt/lynis && git pull --quiet
fi

# Esegui audit
lynis audit system \
    --no-colors \
    --quiet \
    --logfile "$REPORT_FILE" \
    --report-file "${REPORT_DIR}/lynis-report-${TIMESTAMP}.dat"

# Estrai punteggio e warning
HARDENING_INDEX=$(grep "hardening_index" "${REPORT_DIR}/lynis-report-${TIMESTAMP}.dat" | cut -d= -f2)
WARNINGS=$(grep -c "^warning\[\]" "${REPORT_DIR}/lynis-report-${TIMESTAMP}.dat" || true)
SUGGESTIONS=$(grep -c "^suggestion\[\]" "${REPORT_DIR}/lynis-report-${TIMESTAMP}.dat" || true)

echo "Lynis Audit Report - $(date)"
echo "Hardening Index: ${HARDENING_INDEX}"
echo "Warnings: ${WARNINGS}"
echo "Suggestions: ${SUGGESTIONS}"

# Alert se punteggio basso
if [ "${HARDENING_INDEX:-0}" -lt 70 ]; then
    echo "ALERT: Hardening index sotto 70!" | \
        mail -s "[SECURITY] Lynis score basso su $(hostname)" admin@esempio.it
fi
```

### OpenSCAP — compliance automatizzata

```bash
#!/bin/bash
# openscap-scan.sh - scansione CIS benchmark
set -euo pipefail

REPORT_DIR="/var/log/security-scans/openscap"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$REPORT_DIR"

# Installa se necessario
if ! command -v oscap &>/dev/null; then
    apt-get install -y libopenscap8 ssg-base ssg-debderived 2>/dev/null || \
    dnf install -y openscap-scanner scap-security-guide 2>/dev/null
fi

# Identifica profilo e datastream
DISTRO=$(. /etc/os-release && echo "$ID")
case "$DISTRO" in
    ubuntu)
        DATASTREAM="/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml"
        PROFILE="xccdf_org.ssgproject.content_profile_cis_level1_server"
        ;;
    rhel|centos|rocky|alma)
        DATASTREAM="/usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml"
        PROFILE="xccdf_org.ssgproject.content_profile_cis"
        ;;
    *)
        echo "Distribuzione non supportata: $DISTRO"
        exit 1
        ;;
esac

# Esegui scansione
oscap xccdf eval \
    --profile "$PROFILE" \
    --results "${REPORT_DIR}/results-${TIMESTAMP}.xml" \
    --report "${REPORT_DIR}/report-${TIMESTAMP}.html" \
    --oval-results \
    "$DATASTREAM" 2>&1 | tee "${REPORT_DIR}/scan-${TIMESTAMP}.log"

echo "Report HTML: ${REPORT_DIR}/report-${TIMESTAMP}.html"

# Genera fix Ansible per le regole fallite
oscap xccdf generate fix \
    --fix-type ansible \
    --result-id "" \
    "${REPORT_DIR}/results-${TIMESTAMP}.xml" \
    > "${REPORT_DIR}/remediation-${TIMESTAMP}.yml" 2>/dev/null || true

echo "Playbook remediation: ${REPORT_DIR}/remediation-${TIMESTAMP}.yml"
```

**Ansible per scansione automatizzata su flotta:**

```yaml
# security-scan.yml
---
- name: Security scanning automatizzato
  hosts: all
  become: yes

  tasks:
    - name: Installa Lynis
      apt:
        name: lynis
        state: present
      when: ansible_os_family == "Debian"

    - name: Esegui Lynis audit
      command: lynis audit system --no-colors --quiet
      register: lynis_output
      changed_when: false

    - name: Salva report
      copy:
        content: "{{ lynis_output.stdout }}"
        dest: "/var/log/lynis-{{ ansible_date_time.date }}.log"

    - name: Controlla punteggio
      shell: grep "Hardening index" /var/log/lynis-report.dat | cut -d= -f2
      register: score
      changed_when: false

    - name: Alert se score basso
      debug:
        msg: "WARNING: Hardening score {{ score.stdout }} su {{ inventory_hostname }}"
      when: score.stdout | int < 70
```

---

## Automazione Event-Driven

L'automazione event-driven reagisce a cambiamenti nel sistema senza polling continuo. E piu efficiente e responsiva.

### Event-Driven Ansible (EDA) e Rulebook

Event-Driven Ansible (EDA) estende Ansible con un motore di regole basato su **Drools** (Java). A differenza dei playbook tradizionali (esecuzione manuale o schedulata), EDA e un servizio long-running che ascolta eventi da sorgenti esterne e reagisce automaticamente eseguendo azioni predefinite.

**Architettura EDA:**

```
┌──────────────────────────────────────────────────────────┐
│                    Sorgenti Eventi                        │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────┐ │
│  │ Webhook  │  │  Kafka   │  │Alertmanager│  │ File   │ │
│  │ (HTTP)   │  │          │  │(Prometheus)│  │ Watch  │ │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └───┬────┘ │
│       └──────────────┴──────────────┴─────────────┘      │
│                          │                                │
│               ┌──────────▼──────────┐                    │
│               │   ansible-rulebook  │                    │
│               │  (Drools engine)    │                    │
│               └──────────┬──────────┘                    │
│                          │ Match regole                   │
│               ┌──────────▼──────────┐                    │
│               │      Azioni         │                    │
│               │  - run_playbook     │                    │
│               │  - run_module       │                    │
│               │  - set_fact         │                    │
│               │  - post_event       │                    │
│               │  - debug            │                    │
│               └─────────────────────┘                    │
└──────────────────────────────────────────────────────────┘
```

**Installazione:**

```bash
# Installazione EDA controller
pip install ansible-rulebook ansible-core

# Installare collection con sorgenti eventi
ansible-galaxy collection install ansible.eda

# Prerequisiti Java (Drools richiede JRE)
sudo apt install default-jre-headless
```

**Struttura di un rulebook:**

Un rulebook YAML contiene tre elementi: **sources** (da dove arrivano gli eventi), **rules** (condizioni da valutare), e **actions** (cosa fare quando una condizione e vera).

```yaml
# rulebook-webhook.yml - Reagire a webhook
---
- name: Reagisci a deploy webhook
  hosts: all
  sources:
    - ansible.eda.webhook:
        host: 0.0.0.0
        port: 5000

  rules:
    - name: Deploy su push al branch main
      condition: >-
        event.payload.ref == "refs/heads/main" and
        event.payload.repository.name == "mia-app"
      action:
        run_playbook:
          name: playbooks/deploy.yml
          extra_vars:
            app_version: "{{ event.payload.after[:8] }}"
            deployer: "{{ event.payload.pusher.name }}"

    - name: Rollback su webhook di errore
      condition: event.payload.action == "rollback"
      action:
        run_playbook:
          name: playbooks/rollback.yml
```

**Rulebook con Alertmanager (Prometheus):**

```yaml
# rulebook-alertmanager.yml - Auto-remediation da alert Prometheus
---
- name: Auto-remediation infrastruttura
  hosts: all
  sources:
    - ansible.eda.alertmanager:
        host: 0.0.0.0
        port: 8680

  rules:
    - name: Riavvia servizio se down
      condition: >-
        event.alert.labels.alertname == "ServiceDown" and
        event.alert.status == "firing"
      action:
        run_playbook:
          name: playbooks/riavvia-servizio.yml
          extra_vars:
            servizio: "{{ event.alert.labels.service }}"
            host_target: "{{ event.alert.labels.instance }}"

    - name: Scala orizzontalmente su carico alto
      condition: >-
        event.alert.labels.alertname == "HighCPU" and
        event.alert.status == "firing" and
        event.alert.labels.severity == "critical"
      action:
        run_playbook:
          name: playbooks/scale-out.yml

    - name: Libera spazio disco
      condition: >-
        event.alert.labels.alertname == "DiskSpaceLow" and
        event.alert.annotations.disk_usage | int > 90
      action:
        run_module:
          name: ansible.builtin.shell
          module_args:
            cmd: "journalctl --vacuum-size=500M && apt clean"
```

**Rulebook con Kafka:**

```yaml
# rulebook-kafka.yml - Consumare eventi da topic Kafka
---
- name: Processa eventi da Kafka
  hosts: localhost
  sources:
    - ansible.eda.kafka:
        host: kafka.azienda.it
        port: 9092
        topic: infra-events
        group_id: eda-consumer

  rules:
    - name: Provisioning nuovo server
      condition: event.body.event_type == "new_server_request"
      action:
        run_playbook:
          name: playbooks/provision-server.yml
          extra_vars:
            server_name: "{{ event.body.hostname }}"
            server_role: "{{ event.body.role }}"

    - name: Revoca accesso utente
      condition: event.body.event_type == "user_offboarding"
      action:
        run_playbook:
          name: playbooks/revoca-utente.yml
          extra_vars:
            username: "{{ event.body.username }}"
```

**Esecuzione del rulebook:**

```bash
# Avviare il rulebook (servizio long-running)
ansible-rulebook --rulebook rulebook-webhook.yml -i inventory.ini

# Con verbose per debug
ansible-rulebook --rulebook rulebook-webhook.yml -i inventory.ini -vv

# Specificare un Decision Environment (container con dipendenze)
ansible-rulebook --rulebook rulebook-webhook.yml \
  --decision-env quay.io/ansible/eda-decision-env:latest
```

**Decision Environment** — container OCI con Python, ansible-core, collection e dipendenze Java pre-installate. Garantisce riproducibilita e isolamento dell'ambiente EDA in produzione.

**Differenze chiave EDA vs playbook tradizionale:**

| Aspetto | Playbook | EDA Rulebook |
|---------|----------|-------------|
| Esecuzione | Singola, su richiesta | Continua, long-running |
| Trigger | Manuale o schedulato | Evento esterno |
| Motore | Ansible engine | Drools rule engine |
| Uso tipico | Provisioning, deploy | Auto-remediation, scaling |
| Latenza | Minuti (avvio SSH) | Secondi (gia connesso) |

**EDA: Throttling e condizioni avanzate:**

I rulebook supportano condizioni complesse con operatori logici, throttling per evitare cascate di azioni, e combinazioni di eventi multipli:

```yaml
# Condizioni avanzate con throttling
- name: Auto-remediation con rate limiting
  hosts: all
  sources:
    - ansible.eda.alertmanager:
        host: 0.0.0.0
        port: 8680

  rules:
    - name: Riavvia servizio max 3 volte in 10 minuti
      condition: >-
        event.alert.labels.alertname == "ServiceDown" and
        event.alert.status == "firing"
      throttle:
        once_within: 10 minutes
        group_by:
          - event.alert.labels.instance
          - event.alert.labels.service
      action:
        run_playbook:
          name: playbooks/riavvia-servizio.yml

    # Condizione multi-evento: correla due alert
    - name: Scala solo se CPU alto E memoria alta
      condition:
        all:
          - event.alert.labels.alertname == "HighCPU"
          - event.alert.labels.alertname == "HighMemory"
      action:
        run_playbook:
          name: playbooks/scale-out.yml
```

**EDA come servizio systemd** — deployment in produzione:

```ini
# /etc/systemd/system/eda-controller.service
[Unit]
Description=Event-Driven Ansible Controller
After=network-online.target
Wants=network-online.target
Documentation=https://ansible.readthedocs.io/projects/rulebook/

[Service]
Type=simple
User=eda
Group=eda
WorkingDirectory=/opt/eda
ExecStart=/opt/eda/venv/bin/ansible-rulebook \
  --rulebook /opt/eda/rulebooks/main.yml \
  --inventory /opt/eda/inventory.ini \
  --verbose
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/eda/logs
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now eda-controller.service
journalctl -u eda-controller -f   # Seguire log in tempo reale
```

**Sorgenti eventi disponibili nella collection `ansible.eda`:**

| Sorgente | Uso | Protocollo |
|----------|-----|-----------|
| `webhook` | Riceve HTTP POST da CI/CD, GitHub, GitLab | HTTP |
| `kafka` | Consuma messaggi da topic Kafka | Kafka |
| `alertmanager` | Riceve alert da Prometheus Alertmanager | HTTP |
| `url_check` | Monitora URL periodicamente | HTTP polling |
| `file_watch` | Monitora file/directory (inotify-like) | inotify |
| `range` | Genera eventi sequenziali (testing) | Locale |
| `tick` | Genera eventi periodici (heartbeat) | Locale |

**Creare sorgenti eventi custom** — per integrare sistemi proprietari, si puo scrivere un plugin sorgente Python che implementa l'interfaccia `Source`:

```python
# plugins/event_source/syslog_source.py
import asyncio
import socket
from typing import Any

async def main(queue: asyncio.Queue, args: dict[str, Any]):
    """Sorgente eventi: riceve messaggi syslog UDP"""
    host = args.get("host", "0.0.0.0")
    port = args.get("port", 514)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    sock.setblocking(False)
    loop = asyncio.get_event_loop()

    while True:
        data = await loop.sock_recv(sock, 4096)
        message = data.decode("utf-8", errors="replace")
        await queue.put({
            "syslog_message": message,
            "source_host": host,
            "source_port": port,
        })
```

```yaml
# Uso della sorgente custom nel rulebook
- name: Reagisci a log syslog
  hosts: all
  sources:
    - mia_azienda.monitoring.syslog_source:
        host: 0.0.0.0
        port: 514
  rules:
    - name: Blocca IP dopo troppi errori SSH
      condition: >-
        "sshd" in event.syslog_message and
        "Failed password" in event.syslog_message
      action:
        run_playbook:
          name: playbooks/blocca-ip.yml
```

### inotifywait

`inotifywait` (pacchetto `inotify-tools`) monitora cambiamenti nel filesystem in tempo reale:

```bash
# Installazione
sudo apt install inotify-tools

# Monitorare una directory
inotifywait -m -r -e modify,create,delete /etc/nginx/

# Script: ricarica nginx quando la configurazione cambia
#!/bin/bash
# auto-reload-nginx.sh
set -euo pipefail

WATCH_DIR="/etc/nginx"

inotifywait -m -r -e modify,create,delete --format '%w%f %e' "$WATCH_DIR" | \
while read -r file event; do
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] Cambiamento: $file ($event)"

    # Valida configurazione prima di ricaricare
    if nginx -t 2>/dev/null; then
        systemctl reload nginx
        echo "Nginx ricaricato con successo"
    else
        echo "ERRORE: configurazione nginx non valida, reload saltato"
    fi
done
```

**Script: sincronizzazione automatica di file:**

```bash
#!/bin/bash
# auto-sync.sh - sincronizza file modificati verso server remoto
WATCH_DIR="/opt/app/config"
REMOTE="admin@server2:/opt/app/config"

inotifywait -m -r -e modify,create,delete --format '%w%f' "$WATCH_DIR" | \
while read -r file; do
    rsync -avz --delete "$WATCH_DIR/" "$REMOTE/"
    echo "[$(date)] Sincronizzato: $file"
done
```

**Servizio systemd per inotifywait:**

```ini
# /etc/systemd/system/config-watcher.service
[Unit]
Description=Watcher configurazione Nginx
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/auto-reload-nginx.sh
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
```

### systemd path units

Le path unit di systemd monitorano file/directory e attivano un servizio quando cambia qualcosa:

```ini
# /etc/systemd/system/config-deploy.path
[Unit]
Description=Monitora directory di deploy configurazioni

[Path]
PathModified=/opt/deploy/configs
PathExistsGlob=/opt/deploy/configs/*.yml
# Alternative:
# PathExists=       -> attiva quando il path esiste
# PathExistsGlob=   -> attiva quando un glob matcha
# PathChanged=      -> attiva quando il file cambia (chiusura dopo scrittura)
# PathModified=     -> attiva quando il file viene modificato
# DirectoryNotEmpty= -> attiva quando la directory non e vuota
MakeDirectory=yes
DirectoryMode=0755

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/config-deploy.service
[Unit]
Description=Applica configurazioni deployate

[Service]
Type=oneshot
ExecStart=/usr/local/bin/apply-configs.sh
User=root
```

```bash
# Attivare
systemctl enable --now config-deploy.path

# Test
touch /opt/deploy/configs/test.yml
# -> config-deploy.service viene avviato automaticamente
```

**Esempio: processamento automatico upload:**

```ini
# /etc/systemd/system/process-upload.path
[Unit]
Description=Monitora nuovi upload

[Path]
DirectoryNotEmpty=/var/spool/uploads

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/process-upload.service
[Unit]
Description=Processa file uploadati

[Service]
Type=oneshot
ExecStart=/usr/local/bin/process-uploads.sh
```

### auditd triggers

auditd puo attivare azioni quando vengono rilevati eventi specifici:

```bash
# Regole auditd per monitorare modifiche critiche
# /etc/audit/rules.d/automation.rules

# Monitorare modifiche a /etc/passwd
-w /etc/passwd -p wa -k user_modification
-w /etc/shadow -p wa -k password_change
-w /etc/group -p wa -k group_modification
-w /etc/sudoers -p wa -k sudo_modification

# Monitorare file di configurazione
-w /etc/ssh/sshd_config -p wa -k sshd_config_change
-w /etc/nginx/ -p wa -k nginx_config_change
```

```bash
#!/bin/bash
# audit-reactor.sh - reagisce a eventi auditd
# Eseguire come servizio che monitora il log audit

tail -F /var/log/audit/audit.log | while read -r line; do
    # Modifica a /etc/shadow (cambio password)
    if echo "$line" | grep -q 'key="password_change"'; then
        USER=$(echo "$line" | grep -oP 'uid=\K[0-9]+')
        USERNAME=$(getent passwd "$USER" | cut -d: -f1)
        echo "[$(date)] Password cambiata per utente: $USERNAME" >> /var/log/security-events.log
    fi

    # Modifica sudoers
    if echo "$line" | grep -q 'key="sudo_modification"'; then
        echo "[$(date)] ALERT: modifica a sudoers rilevata" >> /var/log/security-events.log
        # Invia notifica
        echo "Modifica a sudoers su $(hostname)" | \
            mail -s "[SECURITY] sudoers modificato" admin@esempio.it
    fi
done
```

---

## ChatOps

ChatOps integra le operazioni IT nelle piattaforme di chat (Slack, Mattermost), permettendo di eseguire comandi operativi direttamente dalla conversazione.

**Architettura ChatOps:**

```
Operatore -> Chat (Slack/Mattermost) -> Bot (Hubot/custom)
                                          |
                                          v
                                    Script/Ansible/API
                                          |
                                          v
                                    Server target
                                          |
                                          v
                                    Risposta -> Chat
```

**Bot Mattermost con webhook — esempio Python:**

```python
#!/usr/bin/env python3
# chatops-bot.py - bot per operazioni via Mattermost
import json
import subprocess
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler

WEBHOOK_SECRET = "configurare-via-env"  # Mai hardcoded in produzione
ALLOWED_USERS = {"mario.rossi", "anna.bianchi"}

COMMANDS = {
    "!status": {
        "cmd": "systemctl status nginx --no-pager",
        "description": "Stato di nginx",
        "require_approval": False,
    },
    "!disk": {
        "cmd": "df -h --output=target,pcent,avail | head -20",
        "description": "Spazio disco",
        "require_approval": False,
    },
    "!restart-nginx": {
        "cmd": "systemctl restart nginx",
        "description": "Riavvia nginx",
        "require_approval": True,
    },
    "!deploy": {
        "cmd": "/usr/local/bin/deploy.sh",
        "description": "Deploy applicazione",
        "require_approval": True,
    },
}

class ChatOpsHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        data = json.loads(body)

        user = data.get("user_name", "")
        text = data.get("text", "").strip()

        if user not in ALLOWED_USERS:
            response = f"Utente {user} non autorizzato per ChatOps"
        elif text == "!help":
            lines = ["**Comandi ChatOps disponibili:**"]
            for cmd, info in COMMANDS.items():
                lines.append(f"- `{cmd}` - {info['description']}")
            response = "\n".join(lines)
        elif text in COMMANDS:
            cmd_info = COMMANDS[text]
            try:
                result = subprocess.run(
                    cmd_info["cmd"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                response = f"**{text}** eseguito da {user}:\n```\n{result.stdout}\n```"
                if result.returncode != 0:
                    response += f"\n**stderr:** ```\n{result.stderr}\n```"
            except subprocess.TimeoutExpired:
                response = f"**{text}**: timeout dopo 60 secondi"
        else:
            response = f"Comando sconosciuto: `{text}`. Usa `!help` per la lista."

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"text": response}).encode())

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8065), ChatOpsHandler)
    print("ChatOps bot in ascolto su :8065")
    server.serve_forever()
```

**Pattern Hubot (CoffeeScript/JS) per Slack:**

```javascript
// scripts/ops.js - comandi operativi Hubot
module.exports = (robot) => {
  robot.respond(/status (.+)/i, (msg) => {
    const service = msg.match[1];
    const { exec } = require("child_process");
    exec(`systemctl status ${service} --no-pager`, (err, stdout) => {
      msg.reply(`\`\`\`\n${stdout}\n\`\`\``);
    });
  });

  robot.respond(/deploy (.+)/i, (msg) => {
    const app = msg.match[1];
    msg.reply(`Avvio deploy di ${app}...`);
    const { exec } = require("child_process");
    exec(`/usr/local/bin/deploy.sh ${app}`, (err, stdout, stderr) => {
      if (err) {
        msg.reply(`Deploy fallito:\n\`\`\`\n${stderr}\n\`\`\``);
      } else {
        msg.reply(`Deploy completato:\n\`\`\`\n${stdout}\n\`\`\``);
      }
    });
  });
};
```

**Sicurezza ChatOps:**
- Autenticazione: verificare l'identita dell'utente (webhook secret, token)
- Autorizzazione: whitelist di utenti per comandi pericolosi
- Audit: loggare ogni comando eseguito con timestamp, utente, risultato
- Sanitizzazione: mai passare input utente direttamente a shell senza validazione
- Rate limiting: limitare la frequenza dei comandi

---

## Runbook Automation

Un runbook e una procedura documentata per gestire un evento operativo. L'automazione dei runbook converte queste procedure manuali in script idempotenti.

**Principi di conversione runbook -> script:**

1. **Idempotenza**: lo script deve poter essere eseguito piu volte senza effetti collaterali
2. **Verifiche pre-condizione**: controllare lo stato prima di agire
3. **Rollback**: prevedere un meccanismo di annullamento
4. **Logging**: ogni azione deve essere tracciata
5. **Alerting**: notificare il completamento o il fallimento

```bash
#!/bin/bash
# runbook-disk-full.sh - Runbook: disco pieno
# Procedura originale manuale convertita in script
set -euo pipefail

LOG_FILE="/var/log/runbook-disk-full.log"
THRESHOLD=90
ALERT_EMAIL="ops@esempio.it"

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] $*" | tee -a "$LOG_FILE"; }

log "=== Inizio runbook: disco pieno ==="

# Step 1: Identifica partizioni piene
log "Step 1: Analisi spazio disco"
FULL_PARTITIONS=$(df -h --output=target,pcent | tail -n +2 | \
    awk -v t=$THRESHOLD '{gsub(/%/,"",$2); if($2 >= t) print $1, $2"%"}')

if [ -z "$FULL_PARTITIONS" ]; then
    log "Nessuna partizione sopra ${THRESHOLD}%. Nessuna azione necessaria."
    exit 0
fi

log "Partizioni sopra soglia: $FULL_PARTITIONS"

# Step 2: Pulizia log compressi vecchi
log "Step 2: Pulizia log vecchi"
FREED_LOGS=$(find /var/log -name "*.gz" -mtime +30 -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1)
find /var/log -name "*.gz" -mtime +30 -delete 2>/dev/null || true
log "Spazio liberato da log compressi: ${FREED_LOGS:-0}"

# Step 3: Pulizia cache APT
log "Step 3: Pulizia cache pacchetti"
apt-get clean 2>/dev/null || dnf clean all 2>/dev/null || true

# Step 4: Pulizia /tmp
log "Step 4: Pulizia file temporanei"
find /tmp -type f -atime +7 -delete 2>/dev/null || true
find /var/tmp -type f -atime +30 -delete 2>/dev/null || true

# Step 5: Pulizia journal systemd
log "Step 5: Pulizia journal"
journalctl --vacuum-time=7d --vacuum-size=500M 2>/dev/null || true

# Step 6: Identifica file grandi
log "Step 6: File piu grandi"
du -ah / 2>/dev/null | sort -rh | head -20 > /tmp/large-files-report.txt
log "Report file grandi salvato in /tmp/large-files-report.txt"

# Step 7: Verifica risultato
log "Step 7: Verifica post-pulizia"
STILL_FULL=$(df -h --output=target,pcent | tail -n +2 | \
    awk -v t=$THRESHOLD '{gsub(/%/,"",$2); if($2 >= t) print $1, $2"%"}')

if [ -n "$STILL_FULL" ]; then
    log "WARNING: Partizioni ancora sopra soglia: $STILL_FULL"
    log "Intervento manuale necessario"
    echo "Runbook disk-full: partizioni ancora piene su $(hostname): $STILL_FULL" | \
        mail -s "[ALERT] Disco pieno - intervento manuale" "$ALERT_EMAIL"
    exit 1
else
    log "OK: Tutte le partizioni sotto soglia"
    exit 0
fi
```

**Pattern di idempotenza per runbook:**

```bash
# Pattern: check-then-act (idempotente)
ensure_service_running() {
    local service="$1"
    if ! systemctl is-active --quiet "$service"; then
        systemctl start "$service"
        echo "[CHANGED] $service avviato"
    else
        echo "[OK] $service gia in esecuzione"
    fi
}

# Pattern: marker file (evita riesecuzione)
run_once() {
    local marker="/var/run/runbook-${1}.done"
    if [ -f "$marker" ]; then
        echo "[SKIP] $1 gia eseguito"
        return 0
    fi
    shift
    "$@"
    touch "$marker"
}

# Pattern: backup-before-change
safe_edit() {
    local file="$1"
    cp "$file" "${file}.bak.$(date +%Y%m%d%H%M%S)"
    # ... modifica ...
}
```

---

## Best Practices

1. **Idempotenza**: ogni playbook Ansible deve poter essere eseguito piu volte senza effetti collaterali. Usare moduli dichiarativi (`state: present`) anziche comandi shell.

2. **Versionare tutto**: playbook, inventory, configurazioni in Git. L'infrastruttura e codice.

3. **Test prima di applicare**: `--check --diff` per vedere cosa cambierebbe. In ambienti critici: applicare prima su staging.

4. **Vault per i secret**: mai password in chiaro nei playbook. Usare Ansible Vault o un secrets manager esterno.

5. **Ruoli per riusabilita**: organizzare il codice in ruoli. Un ruolo per servizio (nginx, postgresql, monitoring). Riutilizzabili tra progetti.

6. **Terraform per il provisioning, Ansible per la configurazione**: non mischiare i ruoli. Terraform crea le VM, Ansible le configura.

7. **Lock file**: ogni script di automazione deve usare lock file per prevenire esecuzioni concorrenti.

8. **Logging strutturato**: ogni operazione automatizzata deve produrre log con timestamp, azione, risultato.

9. **Notifiche di fallimento**: configurare alerting per ogni automazione critica. Un'automazione silenziosa che fallisce e peggio di nessuna automazione.

10. **Rolling update**: per aggiornamenti su flotte, procedere un server alla volta verificando la salute dopo ogni step.

11. **Dry-run sempre disponibile**: ogni script deve supportare una modalita di test che mostra cosa farebbe senza farlo.

12. **Separazione ambienti**: inventari separati per staging e produzione. Mai applicare su produzione senza aver testato su staging.

13. **Timeout e retry**: ogni operazione di rete deve avere timeout e politica di retry.

14. **Pulizia risorse**: dopo task lunghi, verificare che non rimangano processi zombie o file temporanei.

---

## Troubleshooting

**"Cron job non si avvia"** — Cause comuni:

1. Il servizio cron non e in esecuzione: `systemctl status cron` (Debian) o `systemctl status crond` (RHEL)
2. PATH non definito: cron usa un PATH minimale. Usare percorsi assoluti nel job
3. Permessi: lo script non e eseguibile (`chmod +x`). Verificare anche i permessi della directory
4. Output non catturato: aggiungere `>> /var/log/mio-job.log 2>&1` per catturare errori
5. Variabili d'ambiente: cron non carica `.bashrc` o `.profile`. Definire le variabili nella crontab
6. File crontab corrotto: `crontab -l` mostra errori? Ricreare con `crontab -e`

**"Cron job funziona manualmente ma non da cron"** — Il problema e quasi sempre l'ambiente di esecuzione. Cron non carica il profilo utente. Testare con: `env -i /bin/bash -c '/percorso/allo/script.sh'` per simulare l'ambiente cron.

**"Crontab con estensione in cron.daily non esegue"** — `run-parts` ignora i file con punti nel nome. Rinominare `backup.sh` in `backup` (senza estensione). Verificare con `run-parts --test /etc/cron.daily/`.

**"systemd timer non scatta"** — Verificare:
1. Timer abilitato: `systemctl is-enabled mio.timer`
2. Timer attivo: `systemctl is-active mio.timer`
3. Espressione corretta: `systemd-analyze calendar "ESPRESSIONE"`
4. `systemctl list-timers` per vedere quando e prevista la prossima esecuzione
5. Il file `.service` corrispondente esiste e ha lo stesso nome base

**"Ansible: unreachable"** — SSH funziona manualmente? `ssh user@host`. Chiave SSH corretta nell'inventario? Utente corretto? Porta SSH? `ansible host -m ping -vvvv` per debug dettagliato.

**"Ansible: permission denied"** — `become: yes` nel playbook? L'utente ha permessi sudo? Se sudo richiede password: `--ask-become-pass`. Verificare `/etc/sudoers` sul target.

**"Ansible: modulo non trovato"** — Verificare la versione di Ansible: `ansible --version`. Moduli di collection richiedono installazione separata: `ansible-galaxy collection install community.general`. Controllare il FQCN del modulo (es: `ansible.builtin.apt` vs `apt`).

**"Ansible playbook lento"** — Cause:
1. Gathering facts disabilitabile se non necessario: `gather_facts: false`
2. Aumentare parallelismo: `-f 20` (fork)
3. Usare `serial` per rolling update solo quando necessario
4. Pipelining: `pipelining = True` in `ansible.cfg` (riduce connessioni SSH)
5. Mitogen: plugin che accelera significativamente l'esecuzione

**"Ansible: template Jinja2 non renderizza"** — Verificare:
1. Variabile definita? Usare `{{ variable | default('fallback') }}`
2. Tipo corretto? `{{ port }}` vs `"{{ port }}"` (stringa vs intero nel YAML)
3. Escaping: `{% raw %}{{ non_ansible }}{% endraw %}` per contenuto letterale

**"Terraform: Error acquiring state lock"** — Un altro processo Terraform e in esecuzione, o un processo precedente e crashato. `terraform force-unlock LOCK_ID` per sbloccare (con cautela).

**"Terraform: drift tra state e realta"** — `terraform plan` mostra cambiamenti inattesi. `terraform refresh` aggiorna lo state. Per risorse gestite esternamente: `lifecycle { ignore_changes = [field] }`.

**"Cloud-init non esegue"** — `cloud-init status` per lo stato. Log: `/var/log/cloud-init.log`. Il file user-data e YAML valido? Errori di indentazione sono la causa piu comune. Validare con `cloud-init schema --config-file cloud-init.yml`.

**"unattended-upgrades non funziona"** — Verificare:
1. Servizio attivo: `systemctl status unattended-upgrades`
2. Timer APT: `systemctl status apt-daily.timer` e `apt-daily-upgrade.timer`
3. Dry-run: `sudo unattended-upgrades --dry-run --debug`
4. Log: `/var/log/unattended-upgrades/unattended-upgrades.log`
5. Origins corretti in `/etc/apt/apt.conf.d/50unattended-upgrades`

**"Script di backup fallisce silenziosamente"** — Aggiungere `set -euo pipefail` all'inizio. Usare lock file per evitare esecuzioni concorrenti. Verificare spazio disco sulla destinazione prima di iniziare. Controllare permessi dell'utente che esegue il backup.

**"inotifywait si ferma dopo un po'"** — Il limite di inotify watches potrebbe essere raggiunto. Verificare: `cat /proc/sys/fs/inotify/max_user_watches`. Aumentare: `sysctl fs.inotify.max_user_watches=524288`. Rendere permanente in `/etc/sysctl.conf`.

**"Ansible Vault: errore di decifrazione"** — Password sbagliata? Vault ID corretto? Verificare che il file sia effettivamente criptato: `head -1 file.yml` deve mostrare `$ANSIBLE_VAULT;`. Se la password e in un file, verificare che non ci siano newline finali: `cat -A ~/.vault-pass`.

---

## FAQ — Domande Frequenti

**D1: Quando usare cron e quando systemd timer?**

Usare **cron** per job semplici e portabili (script che devono funzionare su qualsiasi Unix). Usare **systemd timer** quando servono dipendenze, logging integrato, sandboxing di sicurezza, persistenza (esecuzione mancata durante spegnimento), o monitoraggio con `systemctl list-timers`. Per nuove installazioni su Linux moderno, preferire systemd timer.

**D2: Come testo un playbook Ansible senza applicare cambiamenti?**

`ansible-playbook site.yml --check --diff`. Il flag `--check` simula l'esecuzione senza modificare nulla, `--diff` mostra le differenze che verrebbero applicate. Nota: alcuni moduli (es: `shell`, `command`) non supportano `--check` perche non possono predire l'output.

**D3: Come posso criptare solo una variabile e non un intero file con Ansible Vault?**

Usare `ansible-vault encrypt_string`: `ansible-vault encrypt_string 'valore-segreto' --name 'nome_variabile'`. L'output puo essere incollato direttamente nel file YAML. Il resto del file rimane leggibile.

**D4: Come faccio a schedulare un job che deve girare solo se il precedente e terminato?**

Con systemd timer e `OnUnitInactiveSec` (scatta N secondi dopo la fine dell'ultima esecuzione). Con cron, usare un lock file: `flock -n /tmp/mio-job.lock /usr/local/bin/mio-job.sh`. Se il lock e gia preso, flock esce immediatamente.

**D5: Come gestisco secret nei playbook Ansible in CI/CD?**

Non usare `--ask-vault-pass` in CI. Salvare la password vault in un file protetto (`chmod 600`) e usare `--vault-password-file`. In pipeline CI come GitLab CI, usare variabili d'ambiente masked: `ANSIBLE_VAULT_PASSWORD_FILE` o generare il file da un secret CI.

**D6: Qual e la differenza tra `command` e `shell` in Ansible?**

`command` esegue il comando direttamente (senza shell). Non supporta pipe (`|`), redirezioni (`>`), variabili d'ambiente inline, o glob. `shell` passa il comando a `/bin/sh`, supportando tutte queste feature. Preferire `command` quando possibile per sicurezza (nessuna shell injection).

**D7: Come aggiorno tutti i server senza downtime?**

Usare `serial` nel playbook Ansible per aggiornare un server alla volta. Prima di aggiornare, rimuovere il server dal load balancer. Dopo l'aggiornamento, verificare il health check e riaggiungerlo. Se un server fallisce, fermare l'intero processo (`max_fail_percentage: 0`).

**D8: Come migro da cron a systemd timer?**

Per ogni crontab entry: (1) creare un file `.service` con `Type=oneshot` e il comando, (2) creare un file `.timer` con `OnCalendar` equivalente, (3) `systemctl enable --now nome.timer`, (4) verificare con `systemctl list-timers`, (5) rimuovere la entry crontab.

**D9: Come faccio debug di un playbook Ansible che fallisce su un singolo host?**

Usare `-l host-specifico` per limitare l'esecuzione. Aumentare verbosita: `-vvvv`. Usare `--start-at-task "nome task"` per riprendere dal task fallito. Controllare i fatti dell'host: `ansible host -m setup`. Verificare la connessione: `ansible host -m ping -vvvv`.

**D10: Che differenza c'e tra Ansible e Terraform? Quando li uso insieme?**

Terraform crea l'infrastruttura (VM, reti, storage, DNS). Ansible configura i sistemi operativi e le applicazioni all'interno. Pipeline tipica: Terraform `apply` -> genera inventario Ansible -> Ansible `playbook` configura i server creati. Non usare Ansible per creare VM e non usare Terraform per configurare pacchetti.

**D11: Come rendere uno script di automazione idempotente?**

Verificare lo stato prima di agire: `if ! grep -q "linea" /file; then echo "linea" >> /file; fi`. Usare `mkdir -p` invece di `mkdir`. Usare `ln -sf` per link simbolici. Per servizi: controllare con `systemctl is-active` prima di riavviare. In Ansible, usare moduli dichiarativi con `state: present/absent`.

**D12: Come monitoro che le mie automazioni funzionino?**

Usare marker file con timestamp: lo script scrive un file marker alla fine dell'esecuzione. Un health check separato verifica che il marker non sia troppo vecchio. Con Prometheus: esportare metriche custom (es: `backup_last_success_timestamp`). Con systemd: `systemctl list-timers` mostra l'ultima esecuzione e la prossima.

**D13: Come gestisco il rollback in caso di fallimento dell'automazione?**

Pattern: (1) snapshot/backup prima dell'operazione, (2) esecuzione con trapping degli errori (`trap cleanup EXIT`), (3) funzione di cleanup che ripristina lo stato precedente. Con Ansible: usare `block/rescue/always` per gestire errori e rollback. Con Terraform: `terraform destroy` o rollback dello state file.

**D14: Come configuro l'autenticazione SSH senza password per Ansible?**

Generare una chiave dedicata: `ssh-keygen -t ed25519 -f ~/.ssh/ansible_key -N ""`. Distribuire la chiave pubblica: `ssh-copy-id -i ~/.ssh/ansible_key.pub admin@target`. Nell'inventario: `ansible_ssh_private_key_file=~/.ssh/ansible_key`. Per sicurezza: limitare la chiave con `command=` e `from=` in `authorized_keys` sui target.

**D15: Come automatizzo la pulizia di immagini Docker vecchie?**

```bash
# Crontab o systemd timer
0 3 * * * docker system prune -af --filter "until=168h" 2>&1 | logger -t docker-cleanup
```
Con Ansible:
```yaml
- name: Pulisci immagini Docker vecchie
  community.docker.docker_prune:
    images: yes
    images_filters:
      dangling: false
      until: 168h
    containers: yes
    volumes: yes
  become: yes
```

**D16: Come eseguo un playbook Ansible solo su server con una certa caratteristica?**

Usare i fact di Ansible con `when`:
```yaml
- name: Solo su Ubuntu
  apt: name=nginx state=present
  when: ansible_distribution == "Ubuntu"

- name: Solo su server con > 8GB RAM
  debug: msg="Server con molta RAM"
  when: ansible_memtotal_mb > 8192
```
Oppure filtrare nell'inventario con gruppi e `--limit`.

**D17: Che differenza c'e tra `at` e `batch`?**

`at` esegue un comando a un orario specifico, indipendentemente dal carico del sistema. `batch` esegue il comando quando il load average del sistema scende sotto la soglia (default: 1.5). Usare `batch` per operazioni pesanti non urgenti che non devono competere con il carico di produzione.

---

## Step-by-Step: Provisioning Completo di un Server

Questa sezione dimostra il workflow completo di automazione: dalla creazione della VM alla configurazione completa, usando Terraform, cloud-init e Ansible.

### Fase 1: Preparazione

```bash
# Struttura del progetto
mkdir -p server-provisioning/{terraform,ansible/{roles,templates,group_vars,host_vars}}
cd server-provisioning

# Inizializzare Git
git init
cat > .gitignore << 'EOF'
*.tfstate
*.tfstate.backup
.terraform/
*.retry
vault-pass
*.log
EOF
```

### Fase 2: Provisioning con Terraform

```hcl
# terraform/main.tf
terraform {
  required_version = ">= 1.5"
  required_providers {
    proxmox = {
      source  = "telmate/proxmox"
      version = "~> 3.0"
    }
  }
  backend "local" {
    path = "terraform.tfstate"
  }
}

variable "proxmox_password" {
  type      = string
  sensitive = true
}

variable "server_count" {
  type    = number
  default = 2
}

provider "proxmox" {
  pm_api_url      = "https://proxmox.interno:8006/api2/json"
  pm_user         = "terraform@pve"
  pm_password     = var.proxmox_password
  pm_tls_insecure = false
}

resource "proxmox_vm_qemu" "web_server" {
  count       = var.server_count
  name        = "web-${format("%02d", count.index + 1)}"
  target_node = "pve01"
  clone       = "ubuntu-2404-template"
  full_clone  = true

  cores   = 2
  memory  = 4096
  sockets = 1

  disk {
    size    = "40G"
    type    = "scsi"
    storage = "local-lvm"
  }

  network {
    model  = "virtio"
    bridge = "vmbr0"
  }

  ipconfig0 = "ip=10.0.1.${10 + count.index}/24,gw=10.0.1.1"

  cicustom = "user=local:snippets/cloud-init-web.yml"
}

# Generazione automatica inventario Ansible
resource "local_file" "ansible_inventory" {
  content = templatefile("${path.module}/inventory.tftpl", {
    web_servers = [
      for i, vm in proxmox_vm_qemu.web_server : {
        name = vm.name
        ip   = "10.0.1.${10 + i}"
      }
    ]
  })
  filename        = "${path.module}/../ansible/inventory.ini"
  file_permission = "0644"
}

output "server_ips" {
  value = [for vm in proxmox_vm_qemu.web_server : vm.name]
}
```

```bash
# terraform/inventory.tftpl
[webservers]
%{ for server in web_servers ~}
${server.name} ansible_host=${server.ip}
%{ endfor ~}

[webservers:vars]
ansible_user=admin
ansible_ssh_private_key_file=~/.ssh/ansible_ed25519
```

### Fase 3: Cloud-init per configurazione base

```yaml
# terraform/cloud-init-web.yml
#cloud-config
hostname: web-server
manage_etc_hosts: true
timezone: Europe/Rome

users:
  - name: admin
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: true
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... ansible@control-node

package_update: true
package_upgrade: true

packages:
  - qemu-guest-agent
  - python3
  - python3-apt

ssh_pwauth: false
disable_root: true

runcmd:
  - systemctl enable --now qemu-guest-agent

final_message: "Cloud-init completato in $UPTIME secondi"
```

### Fase 4: Configurazione con Ansible

```yaml
# ansible/site.yml
---
- name: Configurazione base
  hosts: all
  become: yes
  roles:
    - common
    - hardening

- name: Configurazione web server
  hosts: webservers
  become: yes
  roles:
    - nginx
    - monitoring-agent

- name: Verifica finale
  hosts: all
  become: yes
  tasks:
    - name: Verifica servizi attivi
      systemd:
        name: "{{ item }}"
        state: started
      loop:
        - nginx
        - node_exporter
        - fail2ban
        - ufw

    - name: Verifica porte aperte
      wait_for:
        port: "{{ item }}"
        timeout: 10
      loop:
        - 80
        - 443
        - 9100

    - name: Health check HTTP
      uri:
        url: "http://{{ ansible_host }}/health"
        status_code: 200
      register: health
      retries: 5
      delay: 5
```

```yaml
# ansible/roles/common/tasks/main.yml
---
- name: Aggiorna sistema
  apt:
    update_cache: yes
    upgrade: safe

- name: Installa pacchetti base
  apt:
    name:
      - vim
      - htop
      - iotop
      - curl
      - wget
      - unzip
      - jq
      - net-tools
      - dnsutils
      - chrony
      - logrotate
    state: present

- name: Configura timezone
  timezone:
    name: Europe/Rome

- name: Avvia NTP
  systemd:
    name: chrony
    state: started
    enabled: yes

- name: Configura limite file aperti
  lineinfile:
    path: /etc/security/limits.conf
    line: "{{ item }}"
  loop:
    - "* soft nofile 65536"
    - "* hard nofile 65536"
```

```yaml
# ansible/roles/hardening/tasks/main.yml
---
- name: Hardening SSH
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
  loop:
    - { regexp: '^#?PermitRootLogin', line: 'PermitRootLogin no' }
    - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
    - { regexp: '^#?X11Forwarding', line: 'X11Forwarding no' }
    - { regexp: '^#?MaxAuthTries', line: 'MaxAuthTries 3' }
    - { regexp: '^#?ClientAliveInterval', line: 'ClientAliveInterval 300' }
    - { regexp: '^#?ClientAliveCountMax', line: 'ClientAliveCountMax 2' }
  notify: Restart sshd

- name: Configura firewall UFW
  ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop:
    - "22"
    - "80"
    - "443"
    - "9100"

- name: Abilita UFW
  ufw:
    state: enabled
    policy: deny
    direction: incoming

- name: Installa e configura fail2ban
  apt:
    name: fail2ban
    state: present

- name: Deploy configurazione fail2ban
  copy:
    content: |
      [DEFAULT]
      bantime = 3600
      findtime = 600
      maxretry = 3

      [sshd]
      enabled = true
      port = ssh
      filter = sshd
      logpath = /var/log/auth.log
      maxretry = 3
    dest: /etc/fail2ban/jail.local
  notify: Restart fail2ban

- name: Hardening sysctl
  sysctl:
    name: "{{ item.name }}"
    value: "{{ item.value }}"
    sysctl_set: yes
    reload: yes
  loop:
    - { name: 'net.ipv4.ip_forward', value: '0' }
    - { name: 'net.ipv4.conf.all.send_redirects', value: '0' }
    - { name: 'net.ipv4.conf.all.accept_redirects', value: '0' }
    - { name: 'net.ipv4.conf.all.rp_filter', value: '1' }
    - { name: 'net.ipv4.tcp_syncookies', value: '1' }
    - { name: 'net.ipv4.icmp_echo_ignore_broadcasts', value: '1' }
    - { name: 'kernel.randomize_va_space', value: '2' }

  handlers:
    - name: Restart sshd
      systemd:
        name: sshd
        state: restarted

    - name: Restart fail2ban
      systemd:
        name: fail2ban
        state: restarted
```

### Fase 5: Esecuzione completa

```bash
#!/bin/bash
# provision.sh - pipeline completa di provisioning
set -euo pipefail

LOG_FILE="provision-$(date +%Y%m%d-%H%M%S).log"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG_FILE"; }

# --- Step 1: Terraform ---
log "=== FASE 1: Provisioning infrastruttura ==="
cd terraform
terraform init
terraform plan -out=plan.tfplan
terraform apply plan.tfplan
cd ..

log "Attesa boot VM (60 secondi)..."
sleep 60

# --- Step 2: Verifica connettivita ---
log "=== FASE 2: Verifica connettivita ==="
cd ansible
ansible all -i inventory.ini -m ping --timeout=30
if [ $? -ne 0 ]; then
    log "ERRORE: impossibile raggiungere tutti gli host"
    exit 1
fi

# --- Step 3: Ansible ---
log "=== FASE 3: Configurazione server ==="
ansible-playbook -i inventory.ini site.yml --diff

# --- Step 4: Verifica ---
log "=== FASE 4: Verifica finale ==="
ansible all -i inventory.ini -m shell -a "systemctl is-active nginx fail2ban ufw"

# --- Step 5: Security scan ---
log "=== FASE 5: Security scan ==="
ansible all -i inventory.ini -m shell -a "lynis audit system --quick --quiet" -b

log "=== Provisioning completato ==="
log "Server pronti. Vedi $LOG_FILE per dettagli."
```

### Fase 6: Verifica e validazione

```bash
# Verifica manuale post-provisioning
# 1. Connessione SSH
ssh -i ~/.ssh/ansible_ed25519 admin@10.0.1.10

# 2. Verifica servizi
systemctl status nginx fail2ban ufw

# 3. Verifica firewall
sudo ufw status verbose

# 4. Test HTTP
curl -I http://10.0.1.10/

# 5. Verifica hardening SSH
ssh -o PasswordAuthentication=yes root@10.0.1.10
# Deve fallire (root login e password disabilitati)

# 6. Verifica monitoring
curl http://10.0.1.10:9100/metrics | head

# 7. Lynis audit
sudo lynis audit system
```

Questo workflow e replicabile e versionabile. Ogni esecuzione produce lo stesso risultato (idempotenza). La pipeline puo essere integrata in CI/CD per provisioning automatico di nuovi ambienti.
