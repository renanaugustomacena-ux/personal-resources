# Tutorial Linux 04 — systemd: Servizi, Timer, Journal, Target

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** systemd units, service management, timer, journal, target, socket activation
> **Prerequisiti:** `tutorial_linux_03_gestione_pacchetti.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
systemd
│
├── Units — unità fondamentali
│   ├── .service — processo daemon
│   ├── .timer — cron alternativo
│   ├── .socket — socket activation
│   ├── .target — gruppo di unit
│   ├── .mount — filesystem mount
│   └── .path — file system watch
│
├── systemctl — controllo servizi
│   ├── start/stop/restart/reload
│   ├── enable/disable (boot)
│   ├── status / show
│   └── daemon-reload
│
├── journalctl — log centralizzato
│   ├── -u unit — filtra per unità
│   ├── -f — follow (tail -f)
│   ├── --since --until
│   └── -p err — per priorità
│
└── Target — runlevel moderni
    ├── multi-user.target (CLI)
    ├── graphical.target (GUI)
    └── rescue.target
```

---

# Parte A — Units di servizio

---

## A1. Anatomia di una .service unit

```ini
# /etc/systemd/system/mia-app.service

[Unit]
Description=La mia applicazione Python
Documentation=https://docs.esempio.it
# Dipendenze: avvia dopo network e database
After=network-online.target postgresql.service
Requires=postgresql.service       # fallisce se postgresql fallisce
Wants=redis.service               # raccomandato ma non obbligatorio

[Service]
Type=simple                       # exec: non ha bisogno di fork
User=appuser                      # NON root per sicurezza
Group=appuser
WorkingDirectory=/opt/mia-app

# Sicurezza: limita cosa può fare il processo
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

# Variabili d'ambiente (non usare per segreti sensibili)
EnvironmentFile=/etc/mia-app/env

# Comando di avvio
ExecStart=/opt/mia-app/venv/bin/python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4

# Comandi opzionali pre/post
ExecStartPre=/opt/mia-app/venv/bin/python -m alembic upgrade head
ExecStopPost=/bin/bash -c 'echo "App fermata" >> /var/log/mia-app.log'

# Riavvio automatico
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mia-app

[Install]
WantedBy=multi-user.target        # target da cui viene "voluta"
```

```bash
# Installa e avvia il servizio
systemctl daemon-reload           # rileggi tutti i file unit
systemctl enable mia-app          # avvia al boot
systemctl start mia-app           # avvia ora
systemctl enable --now mia-app    # enable + start in un comando

# Stato
systemctl status mia-app
● mia-app.service - La mia applicazione Python
     Loaded: loaded (/etc/systemd/system/mia-app.service; enabled)
     Active: active (running) since Mon 2024-01-15 10:00:00 UTC; 5min ago
   Main PID: 12345 (python)
      Tasks: 8 (limit: 4915)
     Memory: 45.2M
        CPU: 123ms

# Verifica log in tempo reale
journalctl -u mia-app -f
```

> **Analogia:** Una unit file di systemd è come un contratto di lavoro per un processo. Specifica chi è il "datore di lavoro" (User=), quali sono le dipendenze (After=, Requires=), cosa fare in caso di problemi (Restart=), e orari di reperibilità (Timer). systemd si occupa del resto: avvio, riavvio, log, e dipendenze tra servizi.

---

## A2. Tipi di servizio

```ini
# Type=simple (default)
# - ExecStart è il processo principale
# - systemd considera il servizio avviato immediatamente
Type=simple

# Type=exec
# - Come simple ma aspetta che exec sia completato
Type=exec

# Type=forking
# - Il processo padre fa fork e poi esce
# - Usato per daemon classici UNIX
Type=forking
PIDFile=/run/nginx.pid

# Type=notify
# - Il processo notifica systemd con sd_notify()
# - Avvio considerato completato quando il processo notifica
Type=notify

# Type=oneshot
# - Esegui e termina
# - Usato per script di setup, migration, etc.
# - RemainAfterExit=yes per sembrare "running" dopo exit 0
Type=oneshot
RemainAfterExit=yes
ExecStart=/opt/scripts/migrate.sh
```

---

## A3. Hardening sicurezza servizio

```ini
[Service]
# Impedisce privilege escalation
NoNewPrivileges=true

# Filesystem privato in /tmp
PrivateTmp=true

# /usr, /boot, /etc read-only
ProtectSystem=strict

# Blocca accesso a /home e /root
ProtectHome=true

# Namespace di rete privato (se non serve rete)
PrivateNetwork=true

# Solo il necessario può essere letto/scritto
ReadWritePaths=/var/lib/mia-app /var/log/mia-app

# Rimuovi capabilities non necessarie
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Limita risorse
LimitNOFILE=65536
LimitNPROC=512
MemoryMax=512M
CPUQuota=200%   # max 2 CPU cores
```

---

# Parte B — Timer (cron con systemd)

---

## B1. Creare un timer systemd

```ini
# /etc/systemd/system/backup-database.service
[Unit]
Description=Backup del database PostgreSQL

[Service]
Type=oneshot
User=postgres
ExecStart=/opt/scripts/backup-db.sh
```

```ini
# /etc/systemd/system/backup-database.timer
[Unit]
Description=Esegui backup database ogni notte alle 2:00

[Timer]
# Avvio al boot se il timer è mancato (sistema spento)
Persistent=true
# Ogni giorno alle 2:00
OnCalendar=*-*-* 02:00:00
# Aggiunge una variazione casuale di ±30 minuti
# (utile per evitare thundering herd su molti server)
RandomizedDelaySec=1800

[Install]
WantedBy=timers.target
```

```bash
# Attiva il timer
systemctl enable --now backup-database.timer

# Lista tutti i timer
systemctl list-timers

# Verifica quando scatta il prossimo
systemctl status backup-database.timer

# Esegui manualmente
systemctl start backup-database.service

# Sintassi OnCalendar
# Ogni ora:           hourly
# Ogni giorno:        daily
# Ogni settimana:     weekly
# Ogni mese:          monthly
# Personalizzato:     Mon-Fri 09:00
#                     *-*-1 00:00    (primo del mese)
#                     *-*-* 02:00:00 (ogni giorno alle 2)
#                     *:0/15          (ogni 15 minuti)

# Verifica sintassi
systemd-analyze calendar "Mon-Fri *-*-* 09:00"
```

---

# Parte C — journalctl

---

## C1. Leggere i log

```bash
# Log di tutto il sistema
journalctl

# Segui i log in tempo reale
journalctl -f

# Log di una specifica unit
journalctl -u nginx
journalctl -u nginx -f        # follow
journalctl -u nginx -n 50     # ultime 50 righe

# Filtro per priorità
# 0=emerg 1=alert 2=crit 3=err 4=warning 5=notice 6=info 7=debug
journalctl -p err             # error e superiori
journalctl -p warning         # warning e superiori

# Filtro temporale
journalctl --since "2024-01-15 10:00"
journalctl --since "10 minutes ago"
journalctl --until "2024-01-15 12:00"
journalctl --since "2024-01-15" --until "2024-01-16"

# Formato output
journalctl -o json-pretty     # JSON
journalctl -o short-precise   # default con timestamp preciso
journalctl -o cat             # solo messaggio

# Boot corrente vs precedenti
journalctl -b                 # boot corrente
journalctl -b -1              # boot precedente
journalctl --list-boots       # lista tutti i boot

# Cerca nel log
journalctl -g "ERROR.*database"  # grep

# Usa disk space log
journalctl --disk-usage
journalctl --vacuum-size=500M   # riduci a max 500MB
journalctl --vacuum-time=30d    # rimuovi più vecchi di 30 giorni
```

---

# Parte D — Target e Runlevel

---

## D1. Target systemd

```bash
# Equivalenza runlevel → target
# 0 → poweroff.target
# 1 → rescue.target
# 3 → multi-user.target (CLI)
# 5 → graphical.target (GUI)
# 6 → reboot.target

# Vedi target corrente
systemctl get-default

# Cambia default
systemctl set-default multi-user.target   # CLI senza GUI

# Passa al target immediatamente
systemctl isolate rescue.target   # modalità manutenzione
systemctl isolate graphical.target

# Spegni / riavvia
systemctl poweroff
systemctl reboot
systemctl suspend
systemctl hibernate

# Mostra dipendenze
systemctl list-dependencies graphical.target
```

---

## D2. Analisi avvio sistema

```bash
# Quanto ha impiegato il boot?
systemd-analyze
# Startup finished in 2.015s (kernel) + 8.456s (userspace) = 10.471s

# Grafico delle unit che rallentano il boot
systemd-analyze blame | head -20

# Grafico SVG del boot
systemd-analyze plot > boot.svg

# Verifica unit con problemi
systemctl --failed
systemctl list-units --state=failed

# Verifica stato di una unit in dettaglio
systemctl show nginx
systemctl show nginx --property=ActiveState,SubState,MainPID
```

---

# Parte E — Riepilogo

## Comandi essenziali systemd

| Comando | Scopo |
|---|---|
| `systemctl start/stop/restart` | Controlla lo stato |
| `systemctl enable/disable` | Avvia/non avviare al boot |
| `systemctl enable --now` | Abilita e avvia subito |
| `systemctl status` | Stato e ultimi log |
| `systemctl daemon-reload` | Rileggi file unit modificati |
| `systemctl list-units` | Lista units attive |
| `systemctl list-timers` | Lista timer |
| `journalctl -u nome -f` | Segui log in tempo reale |
| `journalctl -p err` | Solo errori |
| `systemd-analyze blame` | Analisi boot lento |

## File unit: posizioni

| Percorso | Scopo |
|---|---|
| `/etc/systemd/system/` | Unit custom (priorità alta) |
| `/lib/systemd/system/` | Unit pacchetti (non modificare) |
| `~/.config/systemd/user/` | Unit per utente singolo |

## Prossimi passi

- `tutorial_linux_05_networking.md` — configurazione rete con ip/netplan
- `tutorial_linux_11_sicurezza.md` — hardening servizi systemd
