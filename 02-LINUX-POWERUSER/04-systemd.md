# Systemd — Guida Completa

> **Modulo 04** · **Aggiornamento:** 2026-04-27

## Idee guida
1. **systemd.exec(5): `ProtectSystem=strict`, `ProtectHome=true`, `PrivateTmp=true`.** Hardening.
2. **`NoNewPrivileges=yes` + `CapabilityBoundingSet=` per restrict capabilities.**
3. **Timer > cron per produzione: logging integrato journald.**
4. **`systemctl edit` per drop-in override; mai modificare unit upstream.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Systemd — Deep Dive](#architettura-systemd--deep-dive)
  - [PID 1 e il ruolo di init](#pid-1-e-il-ruolo-di-init)
  - [Integrazione con cgroups](#integrazione-con-cgroups)
  - [D-Bus e la comunicazione inter-processo](#d-bus-e-la-comunicazione-inter-processo)
  - [Componenti e demoni ausiliari](#componenti-e-demoni-ausiliari)
  - [Directory dei file unit](#directory-dei-file-unit)
- [Anatomia Completa di un Unit File](#anatomia-completa-di-un-unit-file)
  - [Sezione \[Unit\] — ogni direttiva](#sezione-unit--ogni-direttiva)
  - [Sezione \[Install\] — ogni direttiva](#sezione-install--ogni-direttiva)
- [Tipi di Unit — Guida Esaustiva](#tipi-di-unit--guida-esaustiva)
  - [Service (.service)](#service-service)
  - [Socket (.socket)](#socket-socket)
  - [Timer (.timer)](#timer-timer)
  - [Mount (.mount) e Automount (.automount)](#mount-mount-e-automount-automount)
  - [Swap (.swap)](#swap-swap)
  - [Path (.path)](#path-path)
  - [Slice (.slice)](#slice-slice)
  - [Scope (.scope)](#scope-scope)
  - [Target (.target)](#target-target)
- [Dipendenze e Ordinamento](#dipendenze-e-ordinamento)
- [Socket Activation — Deep Dive](#socket-activation--deep-dive)
- [Template Unit (@)](#template-unit-)
- [Drop-in Override](#drop-in-override)
- [Gestione Servizi — Comandi systemctl](#gestione-servizi--comandi-systemctl)
- [Creazione Servizi Personalizzati](#creazione-servizi-personalizzati)
- [Target e Boot Process](#target-e-boot-process)
- [Systemd Timers](#systemd-timers)
- [Resource Control — Cgroups](#resource-control--cgroups)
- [Security Sandboxing](#security-sandboxing)
- [Journald e Logging — Deep Dive](#journald-e-logging--deep-dive)
- [Systemd-networkd](#systemd-networkd)
- [Systemd-resolved](#systemd-resolved)
- [Systemd-homed](#systemd-homed)
- [Systemd-boot](#systemd-boot)
- [Systemd-nspawn — Container Leggeri](#systemd-nspawn--container-leggeri)
- [Portable Services](#portable-services)
- [Systemd-analyze — Ottimizzazione e Audit](#systemd-analyze--ottimizzazione-e-audit)
- [Boot Performance Tuning](#boot-performance-tuning)
- [Cgroup v2 — Controllo Risorse Avanzato](#cgroup-v2--controllo-risorse-avanzato)
- [Gerarchia Slice — System, User, Machine](#gerarchia-slice--system-user-machine)
- [Systemd-timesyncd](#systemd-timesyncd)
- [Systemd-oomd — OOM Killer Proattivo](#systemd-oomd--oom-killer-proattivo)
- [Systemd Credentials — Gestione Segreti](#systemd-credentials--gestione-segreti)
- [Journal Remote e Gateway — Logging Centralizzato](#journal-remote-e-gateway--logging-centralizzato)
- [Systemd-sysext — Estensioni di Sistema](#systemd-sysext--estensioni-di-sistema)
- [Best Practices](#best-practices)
- [Troubleshooting (20+)](#troubleshooting-20)
- [FAQ (15+)](#faq-15)

---

## Panoramica

Systemd è il sistema di init e gestore dei servizi standard nella quasi totalità delle distribuzioni Linux moderne (Debian, Ubuntu, Fedora, RHEL, Arch, SUSE). Ha sostituito SysVinit e Upstart, portando un'architettura parallela, basata su dipendenze, con gestione unificata di servizi, mount, timer, socket, device e molto altro. La comprensione di systemd è fondamentale per qualsiasi amministratore Linux: dal boot del sistema alla gestione dei servizi, dal logging alla limitazione delle risorse.

---

## Architettura Systemd — Deep Dive

### PID 1 e il ruolo di init

Systemd è il primo processo avviato dal kernel Linux (PID 1). Come PID 1 ha responsabilità
uniche che nessun altro processo possiede:

1. **Adozione degli orfani**: qualsiasi processo il cui padre termina viene ri-parentato a PID 1.
   Systemd raccoglie il loro exit status con `waitpid()`, evitando processi zombie
2. **Gestione dei segnali**: PID 1 non può essere ucciso da SIGKILL (protezione del kernel).
   Riceve SIGTERM solo durante lo shutdown ordinato del sistema
3. **Propagazione dello shutdown**: quando PID 1 termina, il kernel esegue un panic — per questo
   systemd non esce mai durante il funzionamento normale
4. **Montaggio dei filesystem virtuali**: systemd monta `/proc`, `/sys`, `/dev`, `/dev/shm`,
   `/dev/pts`, `/sys/fs/cgroup` durante le primissime fasi dell'avvio
5. **Avvio parallelo**: a differenza di SysVinit (sequenziale), systemd costruisce un grafo di
   dipendenze e avvia le unit in parallelo dove possibile, riducendo il tempo di boot

```
Sequenza PID 1 all'avvio:
  1. Kernel carica initramfs → esegue /sbin/init (symlink a systemd)
  2. systemd monta filesystem virtuali (/proc, /sys, /dev, cgroups)
  3. Legge la configurazione da /etc/systemd/system.conf
  4. Determina il default.target (tipicamente multi-user.target o graphical.target)
  5. Costruisce il transaction graph (grafo delle dipendenze)
  6. Avvia tutte le unit necessarie in parallelo rispettando le dipendenze
  7. Gestisce il ciclo di vita di tutti i servizi fino allo shutdown
```

File di configurazione globale di PID 1:

```ini
# /etc/systemd/system.conf — parametri globali di systemd
[Manager]
LogLevel=info                      # Livello log: emerg..debug
LogTarget=journal-or-kmsg          # Dove inviare i log
DefaultTimeoutStartSec=90s         # Timeout avvio globale per unit
DefaultTimeoutStopSec=90s          # Timeout arresto globale
DefaultRestartSec=100ms            # Delay restart default
DefaultStartLimitIntervalSec=10s   # Finestra rate-limit restart
DefaultStartLimitBurst=5           # Max restart nella finestra
DefaultLimitNOFILE=1024:524288     # Soft:Hard limit file descriptor
DefaultCPUAccounting=yes           # Abilita accounting CPU per tutti
DefaultMemoryAccounting=yes        # Abilita accounting memoria per tutti
DefaultTasksAccounting=yes         # Abilita accounting task per tutti
DefaultTasksMax=4096               # Max task default per unit
```

### Integrazione con cgroups

Systemd è il gestore esclusivo della gerarchia cgroups v2 (unified hierarchy) su sistemi
moderni. Ogni unit avviata da systemd viene automaticamente collocata in un cgroup dedicato.

```
Gerarchia cgroups v2 gestita da systemd:

/sys/fs/cgroup/                          ← root cgroup
├── init.scope/                          ← PID 1 stesso
├── system.slice/                        ← servizi di sistema
│   ├── nginx.service/                   ← cgroup per nginx
│   │   ├── cgroup.controllers           ← controller attivi (cpu, memory, io, pids)
│   │   ├── cgroup.procs                 ← PID dei processi nel cgroup
│   │   ├── memory.current               ← uso memoria corrente
│   │   ├── memory.max                   ← limite hard
│   │   ├── cpu.stat                     ← statistiche CPU
│   │   └── pids.current                 ← numero task correnti
│   ├── postgresql.service/
│   └── sshd.service/
├── user.slice/                          ← sessioni utente
│   ├── user-1000.slice/                 ← tutto l'utente UID 1000
│   │   └── session-42.scope/            ← sessione login
│   └── user-0.slice/                    ← root
└── machine.slice/                       ← container (nspawn, VM)
```

Controller cgroup supportati da systemd:

| Controller | Descrizione | Direttive systemd |
|---|---|---|
| `cpu` | Distribuzione tempo CPU | `CPUWeight=`, `CPUQuota=` |
| `cpuset` | Affinità core | `AllowedCPUs=`, `AllowedMemoryNodes=` |
| `memory` | Limiti e accounting memoria | `MemoryMax=`, `MemoryHigh=`, `MemorySwapMax=` |
| `io` | Banda e IOPS disco | `IOWeight=`, `IOReadBandwidthMax=` |
| `pids` | Numero massimo processi | `TasksMax=` |
| `rdma` | Risorse RDMA | (raro, uso specialistico) |

```bash
# Verificare la gerarchia cgroup di un servizio
systemctl status nginx.service | grep CGroup
# → CGroup: /system.slice/nginx.service

# Ispezionare direttamente il filesystem cgroup
cat /sys/fs/cgroup/system.slice/nginx.service/memory.current
cat /sys/fs/cgroup/system.slice/nginx.service/cpu.stat
cat /sys/fs/cgroup/system.slice/nginx.service/pids.current

# Monitoraggio in tempo reale di tutti i cgroup
systemd-cgtop

# Verificare quali controller sono attivi
cat /sys/fs/cgroup/cgroup.controllers
```

### D-Bus e la comunicazione inter-processo

Systemd espone una API completa tramite D-Bus (Desktop Bus), il sistema di IPC standard su
Linux. Ogni operazione di `systemctl` è in realtà una chiamata D-Bus al PID 1.

```bash
# systemctl start nginx è equivalente a:
busctl call org.freedesktop.systemd1 \
  /org/freedesktop/systemd1 \
  org.freedesktop.systemd1.Manager \
  StartUnit ss "nginx.service" "replace"

# Elencare tutte le unit via D-Bus
busctl call org.freedesktop.systemd1 \
  /org/freedesktop/systemd1 \
  org.freedesktop.systemd1.Manager \
  ListUnits

# Ispezionare il bus di sistema
busctl list                              # Tutti i servizi sul bus
busctl tree org.freedesktop.systemd1     # Struttura ad albero
busctl introspect org.freedesktop.systemd1 /org/freedesktop/systemd1

# Monitorare eventi D-Bus in tempo reale
busctl monitor org.freedesktop.systemd1
```

Interfacce D-Bus principali di systemd:

| Interfaccia | Scopo |
|---|---|
| `org.freedesktop.systemd1.Manager` | Gestione globale unit, job, snapshot |
| `org.freedesktop.systemd1.Unit` | Operazioni su singola unit |
| `org.freedesktop.systemd1.Service` | Proprietà specifiche dei servizi |
| `org.freedesktop.login1.Manager` | Sessioni, seat, gestione power (logind) |
| `org.freedesktop.hostname1` | Hostname e dati macchina |
| `org.freedesktop.timedate1` | Data/ora e timezone |
| `org.freedesktop.resolve1.Manager` | Operazioni DNS (resolved) |

I servizi di tipo `Type=dbus` vengono considerati "pronti" quando acquisiscono il nome
sul bus specificato da `BusName=`.

### Componenti e demoni ausiliari

```
systemd (PID 1) — Gestore centrale di unit e ciclo di vita
│
├── Comandi utente:
│   ├── systemctl              → Controlla unit (start/stop/enable/status)
│   ├── journalctl             → Query log strutturati
│   ├── systemd-analyze        → Analisi boot e verifica unit
│   ├── systemd-run            → Esegue comandi in scope/service transitori
│   ├── systemd-cat            → Pipe stdout/stderr verso il journal
│   ├── systemd-cgls           → Mostra gerarchia cgroup ad albero
│   ├── systemd-cgtop          → Top per cgroup (CPU, mem, I/O)
│   ├── systemd-delta          → Mostra override e differenze tra unit
│   ├── systemd-escape         → Escape/unescape stringhe per nomi unit
│   ├── loginctl               → Gestione sessioni (logind)
│   ├── hostnamectl            → Gestione hostname
│   ├── timedatectl            → Data/ora/timezone
│   ├── localectl              → Locale e layout tastiera
│   ├── resolvectl             → Query e gestione DNS
│   ├── networkctl             → Stato interfacce di rete
│   ├── busctl                 → Ispezione bus D-Bus
│   ├── portablectl            → Gestione portable services
│   ├── machinectl             → Gestione container (nspawn)
│   └── homectl                → Gestione home directory (homed)
│
├── Demoni:
│   ├── systemd-journald       → Logging strutturato binario
│   ├── systemd-logind         → Sessioni utente, seat, power management
│   ├── systemd-networkd       → Configurazione rete
│   ├── systemd-resolved       → Resolver DNS con cache
│   ├── systemd-timesyncd      → Sincronizzazione NTP leggera
│   ├── systemd-tmpfiles       → Creazione/pulizia file e directory temporanei
│   ├── systemd-udevd          → Gestione eventi dispositivi (udev)
│   ├── systemd-hostnamed      → Hostname via D-Bus
│   ├── systemd-localed        → Locale via D-Bus
│   ├── systemd-timedated      → Data/ora via D-Bus
│   ├── systemd-machined       → Container e VM
│   ├── systemd-homed          → Home directory portatili (LUKS, fscrypt)
│   ├── systemd-oomd           → OOM killer in userspace (proattivo)
│   ├── systemd-userdbd        → Database utenti multiplexing NSS/JSON
│   └── systemd-coredump       → Raccolta e gestione core dump
│
└── Boot e filesystem:
    ├── systemd-boot (sd-boot) → Boot loader UEFI leggero
    ├── systemd-nspawn          → Container OS leggeri
    ├── systemd-sysctl          → Applica parametri kernel da sysctl.d
    ├── systemd-modules-load    → Carica moduli kernel da modules-load.d
    ├── systemd-cryptsetup      → Setup LUKS/dm-crypt
    ├── systemd-veritysetup     → Setup dm-verity
    ├── systemd-growfs          → Espansione filesystem al boot
    └── systemd-makefs          → Creazione filesystem al primo boot
```

### Directory dei file unit

```bash
# Ordine di precedenza (dal più alto al più basso):
/etc/systemd/system/              # Configurazione admin (override) — PRIORITÀ MASSIMA
/run/systemd/system/              # Runtime (generato dinamicamente, non sopravvive al reboot)
/usr/lib/systemd/system/          # File installati dai pacchetti (non modificare MAI)

# Unit per utente (gestite da systemd --user):
~/.config/systemd/user/           # Unit utente personalizzate — PRIORITÀ MASSIMA
/etc/systemd/user/                # Unit utente globali (admin)
/run/systemd/user/                # Runtime utente
/usr/lib/systemd/user/            # Unit utente dai pacchetti

# Generator output (unit generate dinamicamente):
/run/systemd/generator.early/     # Priorità prima di /etc
/run/systemd/generator/           # Priorità tra /etc e /run
/run/systemd/generator.late/      # Priorità dopo /usr/lib

# Preset (regole di abilitazione default):
/etc/systemd/system-preset/       # Preset admin
/usr/lib/systemd/system-preset/   # Preset distribuzione
```

**Regola d'oro**: non modificare mai i file in `/usr/lib/systemd/system/`. Per personalizzare,
copiare in `/etc/systemd/system/` o usare i drop-in. I file in `/etc` hanno sempre precedenza.

```bash
# Vedere quali file sono stati sovrascritti o estesi
systemd-delta                             # Mostra tutti gli override
systemd-delta --type=overridden           # Solo file completamente sovrascritti
systemd-delta --type=extended             # Solo drop-in aggiunti
systemd-delta --type=masked               # Solo file mascherati
```

---

## Anatomia Completa di un Unit File

Un unit file è un file di testo in formato INI organizzato in sezioni. Ogni tipo di unit ha
sezioni specifiche, ma `[Unit]` e `[Install]` sono comuni a tutti i tipi.

### Sezione [Unit] — ogni direttiva

La sezione `[Unit]` contiene metadati e relazioni con altre unit. È identica per tutti i tipi.

| Direttiva | Descrizione |
|---|---|
| `Description=` | Descrizione leggibile. Appare in `systemctl status`, log, UI |
| `Documentation=` | Uno o più URI di documentazione (man:, https://, file:) |
| `After=` | Ordine: questa unit si avvia dopo le unit elencate. Non crea dipendenza |
| `Before=` | Ordine: questa unit si avvia prima delle unit elencate |
| `Requires=` | Dipendenza forte: le unit elencate vengono avviate insieme. Se falliscono, anche questa fallisce |
| `Wants=` | Dipendenza debole: le unit elencate vengono avviate insieme, ma il loro fallimento è ignorato |
| `BindsTo=` | Come `Requires` ma più stretto: se la unit legata si ferma, anche questa si ferma |
| `PartOf=` | Quando la unit elencata viene fermata/riavviata, anche questa viene fermata/riavviata |
| `Conflicts=` | Le unit elencate vengono fermate quando questa si avvia, e viceversa |
| `Requisite=` | Come `Requires`, ma la unit deve essere già attiva (non la avvia) |
| `OnFailure=` | Unit da avviare quando questa fallisce (utile per notifiche) |
| `OnSuccess=` | Unit da avviare quando questa termina con successo |
| `PropagatesReloadTo=` | Il reload di questa unit propaga il reload alle unit elencate |
| `ReloadPropagatedFrom=` | Il reload delle unit elencate propaga il reload a questa |
| `PropagatesStopTo=` | Lo stop di questa unit propaga lo stop alle unit elencate |
| `StopPropagatedFrom=` | Lo stop delle unit elencate propaga lo stop a questa |
| `JoinsNamespaceOf=` | Condivide namespace (mount, network, IPC) con le unit elencate |
| `RequiresMountsFor=` | Aggiunge dipendenze implicite per i mount necessari ai percorsi elencati |
| `ConditionPathExists=` | Avvia solo se il percorso esiste. Prefisso `!` per negare |
| `ConditionPathIsDirectory=` | Avvia solo se il percorso è una directory |
| `ConditionPathIsReadWrite=` | Avvia solo se il percorso è scrivibile |
| `ConditionDirectoryNotEmpty=` | Avvia solo se la directory non è vuota |
| `ConditionFileNotEmpty=` | Avvia solo se il file non è vuoto |
| `ConditionFileIsExecutable=` | Avvia solo se il file è eseguibile |
| `ConditionKernelCommandLine=` | Avvia solo se la command line del kernel contiene la stringa |
| `ConditionKernelVersion=` | Avvia solo se la versione del kernel corrisponde |
| `ConditionVirtualization=` | Avvia solo in determinati ambienti di virtualizzazione |
| `ConditionHost=` | Avvia solo sull'hostname specificato |
| `ConditionUser=` | Avvia solo se l'utente corrente corrisponde (unit utente) |
| `ConditionACPower=` | Avvia solo se alimentazione AC è presente/assente |
| `ConditionMemory=` | Avvia solo se la RAM totale corrisponde (es. `>=4G`) |
| `ConditionCPUs=` | Avvia solo se il numero di CPU corrisponde (es. `>=4`) |
| `ConditionEnvironment=` | Avvia solo se una variabile d'ambiente è impostata |
| `AssertPathExists=` | Come `Condition*`, ma il fallimento è un errore (non skip silenzioso) |
| `AssertFileIsExecutable=` | Idem — se il file non è eseguibile, errore |
| `SourcePath=` | Percorso del file sorgente del generatore |
| `StartLimitIntervalSec=` | Intervallo per il rate-limit dei restart (v248+, spostato da [Service]) |
| `StartLimitBurst=` | Numero massimo di avvii nella finestra di rate-limit |
| `StartLimitAction=` | Azione se il rate-limit viene raggiunto: none, reboot, reboot-force, poweroff |
| `FailureAction=` | Azione quando la unit entra in stato failed: none, reboot, poweroff, exit |
| `SuccessAction=` | Azione quando la unit termina con successo |
| `CollectMode=` | `inactive-or-failed`: raccoglie (dealloca) la unit quando non serve più |

### Sezione [Install] — ogni direttiva

La sezione `[Install]` definisce il comportamento di `systemctl enable/disable`. Non è
letta durante il runtime — solo durante enable/disable.

| Direttiva | Descrizione |
|---|---|
| `WantedBy=` | Crea un symlink nella directory `.wants/` del target elencato. Il target "vuole" questa unit |
| `RequiredBy=` | Crea un symlink nella directory `.requires/` del target. Dipendenza forte inversa |
| `Also=` | Quando questa unit viene abilitata/disabilitata, abilita/disabilita anche le unit elencate |
| `Alias=` | Crea nomi alternativi (symlink) per questa unit |
| `DefaultInstance=` | Istanza default per i template (es. `DefaultInstance=main` per `foo@.service`) |

```ini
# Esempio completo sezione [Install]
[Install]
WantedBy=multi-user.target         # Abilitato nel target multi-user
Also=myapp-worker.service          # Abilita anche il worker
Alias=webapp.service               # Nome alternativo
```

---

## Tipi di Unit — Guida Esaustiva

### Service (.service)

Le unit .service gestiscono processi e demoni. La sezione `[Service]` contiene tutte le
direttive specifiche.

#### Tipi di servizio (Type=)

```ini
# simple (default): ExecStart è il processo principale
# Systemd considera il servizio avviato immediatamente dopo il fork
Type=simple

# exec: come simple, ma "started" solo dopo che exec() ha successo
# Cattura errori come binario mancante o permessi insufficienti
Type=exec

# forking: il processo fa fork, il padre esce, il figlio continua
# Usare quando il demone si daemonizza da solo (vecchio stile)
Type=forking
PIDFile=/run/myapp.pid
GuessMainPID=yes                   # Fallback se PIDFile non è impostato

# oneshot: per script che eseguono un'azione e terminano
# L'unit successiva parte solo dopo che questo ha terminato
Type=oneshot
RemainAfterExit=yes                # Mantiene stato "active" dopo la terminazione
ExecStart=/usr/local/bin/setup-iptables.sh
ExecStart=/usr/local/bin/setup-routes.sh   # Più ExecStart in sequenza

# notify: il processo segnala a systemd quando è pronto
# Richiede sd_notify() nel codice o systemd-notify nel wrapper
Type=notify
NotifyAccess=main                  # Solo il processo principale può notificare
WatchdogSec=30                     # Il processo deve inviare keepalive ogni 30s

# notify-reload: come notify, ma supporta reload via SIGHUP + notifica
Type=notify-reload

# dbus: pronto quando acquisisce il nome D-Bus specificato
Type=dbus
BusName=org.example.MyApp

# idle: come simple, ma ritarda l'esecuzione finché tutti i job non sono terminati
# Utile per stampare messaggi sulla console senza mescolarli con l'output di boot
Type=idle
```

#### Direttive [Service] — riferimento completo

```ini
[Service]
# === IDENTITÀ PROCESSO ===
User=appuser                       # Utente (nome o UID)
Group=appgroup                     # Gruppo (nome o GID)
SupplementaryGroups=docker audio   # Gruppi supplementari
DynamicUser=yes                    # Crea utente/gruppo temporanei per l'esecuzione

# === AMBIENTE E DIRECTORY ===
WorkingDirectory=/opt/myapp        # Directory di lavoro
RootDirectory=/srv/chroot          # Chroot (per isolamento forte)
RootImage=/srv/images/myapp.raw    # Usa immagine disco come root
Environment=VAR1=val1 VAR2=val2    # Variabili d'ambiente inline
EnvironmentFile=/etc/myapp/env     # File con variabili (KEY=VALUE per riga)
EnvironmentFile=-/etc/myapp/opt    # "-" = non fallire se manca
PassEnvironment=LANG TZ            # Passa variabili dall'ambiente di systemd
UnsetEnvironment=SECRET_KEY        # Rimuovi variabili dall'ambiente ereditato

# === CICLO DI VITA ===
ExecStartPre=-/opt/myapp/pre.sh    # Esegui prima di ExecStart ("-" = ignora errori)
ExecStart=/usr/bin/node server.js  # Comando principale (obbligatorio)
ExecStartPost=/opt/myapp/post.sh   # Esegui dopo ExecStart
ExecReload=/bin/kill -HUP $MAINPID # Comando per reload (segnale o script)
ExecStop=/bin/kill -TERM $MAINPID  # Comando per stop (default: SIGTERM)
ExecStopPost=/opt/myapp/cleanup.sh # Esegui dopo lo stop (anche su crash)

# === POLITICHE DI RESTART ===
Restart=on-failure                 # Quando riavviare
  # no            → mai (default)
  # on-success    → solo su exit 0 / SIGHUP / SIGINT / SIGTERM / SIGPIPE
  # on-failure    → su exit != 0, segnale, timeout, watchdog
  # on-abnormal   → su segnale, timeout, watchdog (non su exit != 0)
  # on-watchdog   → solo su timeout watchdog
  # on-abort      → solo su segnale non catturato
  # always        → sempre (tranne systemctl stop)
RestartSec=5s                      # Pausa tra stop e restart
RestartMaxDelaySec=5min            # Delay max se RestartSteps è impostato
RestartSteps=10                    # Incremento graduale del delay
RestartPreventExitStatus=255       # Non riavviare su questo exit code
RestartForceExitStatus=SIGSEGV     # Forza restart su questo segnale
SuccessExitStatus=143              # Considera 143 (SIGTERM) come successo

# === TIMEOUT ===
TimeoutStartSec=90s                # Timeout per considerare l'avvio fallito
TimeoutStopSec=90s                 # Timeout prima di SIGKILL dopo SIGTERM
TimeoutAbortSec=90s                # Timeout per abort (core dump)
TimeoutSec=90s                     # Scorciatoia per Start + Stop
WatchdogSec=30s                    # Intervallo keepalive watchdog

# === SEGNALI ===
KillMode=control-group             # Cosa uccidere allo stop
  # control-group → tutti i processi nel cgroup (default, raccomandato)
  # mixed         → SIGTERM al processo principale, SIGKILL al resto
  # process       → solo il processo principale
  # none          → solo ExecStop, nessun segnale automatico
KillSignal=SIGTERM                 # Segnale iniziale di stop
FinalKillSignal=SIGKILL            # Segnale finale dopo timeout
SendSIGHUP=no                      # Invia SIGHUP dopo il segnale di stop
SendSIGKILL=yes                    # Invia SIGKILL dopo TimeoutStopSec

# === OUTPUT E LOG ===
StandardInput=null                 # Input: null, tty, socket, fd:name
StandardOutput=journal             # Output: inherit, null, tty, journal, kmsg, socket
StandardError=journal              # Errore: stessi valori di StandardOutput
SyslogIdentifier=myapp             # Identificativo nei log (default: nome processo)
SyslogFacility=daemon              # Facility syslog
SyslogLevel=info                   # Livello syslog default
LogLevelMax=notice                 # Scarta messaggi sopra questo livello

# === LIMITI RISORSE (setrlimit) ===
LimitCPU=infinity                  # CPU time (RLIMIT_CPU)
LimitFSIZE=infinity               # Max file size
LimitDATA=infinity                 # Max data segment
LimitSTACK=8M                     # Stack size
LimitCORE=0                       # Core dump size (0 = disabilitato)
LimitRSS=infinity                 # Max RSS
LimitNOFILE=1024:524288            # File descriptor (soft:hard)
LimitAS=infinity                   # Address space
LimitNPROC=4096                    # Max processi
LimitMEMLOCK=64M                  # Memoria lockabile
LimitLOCKS=infinity               # File lock
LimitSIGPENDING=128303             # Segnali pendenti
LimitMSGQUEUE=819200              # POSIX message queue
LimitNICE=0                       # Nice priority
LimitRTPRIO=0                     # Realtime priority
```

### Socket (.socket)

Le unit .socket definiscono socket IPC o di rete. Quando arriva una connessione, systemd
avvia automaticamente il servizio corrispondente (socket activation).

```ini
# /etc/systemd/system/myapp.socket
[Unit]
Description=MyApp Socket Activation

[Socket]
# === TIPO DI SOCKET ===
ListenStream=8080                  # TCP (stream) sulla porta 8080
# ListenStream=/run/myapp.sock    # Socket UNIX stream
# ListenDatagram=514              # UDP (datagram)
# ListenSequentialPacket=/run/x.sock  # UNIX sequential packet
# ListenFIFO=/run/myapp.fifo      # Named pipe (FIFO)
# ListenSpecial=/dev/input/event0  # Device speciale
# ListenNetlink=kobject-uevent 1   # Netlink
# ListenUSBFunction=...           # USB function

# === COMPORTAMENTO ===
Accept=no                          # no = un solo servizio per tutti i client
                                   # yes = un'istanza per ogni connessione (inetd-style)
MaxConnections=64                  # Max connessioni simultanee (se Accept=yes)
MaxConnectionsPerSource=8          # Max connessioni per IP sorgente
KeepAlive=yes                      # TCP keepalive
NoDelay=yes                        # TCP_NODELAY
Backlog=128                        # Dimensione coda listen
BindIPv6Only=default               # default, both, ipv6-only

# === PERMESSI (socket UNIX) ===
SocketUser=www-data                # Proprietario del file socket
SocketGroup=www-data               # Gruppo del file socket
SocketMode=0660                    # Permessi del file socket

# === OPZIONI AVANZATE ===
FileDescriptorName=http            # Nome del fd passato al servizio
TriggerLimitIntervalSec=2s         # Rate-limit: intervallo
TriggerLimitBurst=200              # Rate-limit: burst
Service=myapp.service              # Servizio da attivare (default: stesso nome)

[Install]
WantedBy=sockets.target
```

### Timer (.timer)

Le unit .timer attivano un'altra unit a intervalli definiti o in momenti specifici.
Sostituto moderno di cron con logging integrato, dipendenze, e persistenza.

(Dettaglio completo nella sezione [Systemd Timers](#systemd-timers).)

### Mount (.mount) e Automount (.automount)

Le unit .mount corrispondono a entry di `/etc/fstab`. Il nome del file deve corrispondere
al percorso di mount con gli slash sostituiti da trattini (es. `/srv/data` → `srv-data.mount`).

```ini
# /etc/systemd/system/srv-data.mount
[Unit]
Description=Montaggio dati su /srv/data
After=network-online.target
Wants=network-online.target

[Mount]
What=/dev/disk/by-uuid/xxxx-yyyy   # Dispositivo, UUID, label o share di rete
Where=/srv/data                    # Punto di mount
Type=ext4                          # Tipo filesystem
Options=defaults,noatime,nodiratime # Opzioni di mount
DirectoryMode=0755                 # Permessi della directory di mount
TimeoutSec=30s                     # Timeout per l'operazione
LazyUnmount=no                     # Unmount lazy (solo per debug)
ReadWriteOnly=no                   # Fallisci se read-only anziché fallback
ForceUnmount=no                    # Forza unmount con MNT_FORCE
SloppyOptions=no                   # Ignora opzioni non riconosciute

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/srv-data.automount
[Unit]
Description=Automount /srv/data on access

[Automount]
Where=/srv/data                    # Punto di mount (deve corrispondere al .mount)
TimeoutIdleSec=300                 # Smonta dopo 5 min di inattività (0 = mai)
DirectoryMode=0755                 # Permessi della directory autofs

[Install]
WantedBy=multi-user.target
```

```ini
# Esempio: mount NFS via systemd
# /etc/systemd/system/mnt-nfs.mount
[Unit]
Description=NFS Share
After=network-online.target
Requires=network-online.target

[Mount]
What=192.168.1.10:/export/data
Where=/mnt/nfs
Type=nfs
Options=rw,hard,intr,rsize=8192,wsize=8192

[Install]
WantedBy=multi-user.target
```

### Swap (.swap)

Le unit .swap gestiscono aree di swap. Il nome del file deve corrispondere al percorso
del device/file.

```ini
# /etc/systemd/system/dev-sdb2.swap
[Unit]
Description=Swap Partition sdb2

[Swap]
What=/dev/sdb2                     # Partizione o file di swap
Priority=10                        # Priorità swap (come swapon -p)
Options=discard                    # Opzioni di swap
TimeoutSec=30s                     # Timeout per swapon/swapoff

[Install]
WantedBy=swap.target
```

```ini
# Swap file
# /etc/systemd/system/swapfile.swap
[Unit]
Description=Swap File

[Swap]
What=/swapfile
Priority=5

[Install]
WantedBy=swap.target
```

### Path (.path)

Le unit .path monitorano il filesystem e attivano un servizio quando un percorso cambia.
Utile per trigger basati su file (hot folder, spool directory).

```ini
# /etc/systemd/system/upload-watcher.path
[Unit]
Description=Monitora directory upload

[Path]
PathExists=/srv/uploads/trigger    # Attiva quando il file esiste
PathExistsGlob=/srv/uploads/*.csv  # Attiva quando file matching il glob esistono
PathChanged=/srv/uploads/          # Attiva su qualsiasi modifica nella directory
PathModified=/srv/uploads/config   # Attiva quando il file viene modificato (scritto)
DirectoryNotEmpty=/srv/uploads/    # Attiva quando la directory non è vuota
MakeDirectory=yes                  # Crea la directory se non esiste
DirectoryMode=0755                 # Permessi della directory creata
TriggerLimitIntervalSec=5s         # Rate limiting
TriggerLimitBurst=10               # Max attivazioni nell'intervallo
Unit=upload-processor.service      # Servizio da attivare (default: stesso nome)

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/upload-processor.service
[Unit]
Description=Elabora file uploadati

[Service]
Type=oneshot
ExecStart=/usr/local/bin/process-uploads.sh
```

### Slice (.slice)

Le unit .slice definiscono nodi nella gerarchia cgroup per raggruppare servizi e applicare
limiti di risorse collettivi.

```ini
# /etc/systemd/system/webapps.slice
[Unit]
Description=Slice per applicazioni web

[Slice]
# Limiti applicati a TUTTI i servizi nel slice
CPUQuota=300%                      # Max 3 core per tutto il slice
MemoryMax=4G                       # Max 4GB RAM per tutto il slice
MemoryHigh=3G                      # Throttling a 3GB
TasksMax=2048                      # Max 2048 processi totali
IOWeight=200                       # Peso I/O relativo
```

```ini
# Assegnare un servizio a uno slice
[Service]
Slice=webapps.slice
```

### Scope (.scope)

Le unit .scope raggruppano processi avviati esternamente (non da systemd). Non possono essere
definite con file unit — vengono create programmaticamente via D-Bus. Usate da logind
per le sessioni utente e da `systemd-run --scope`.

```bash
# Eseguire un comando in uno scope con limiti di risorse
systemd-run --scope --unit=mybackup \
  -p MemoryMax=1G -p CPUQuota=50% \
  /usr/local/bin/backup.sh

# Lo scope apparirà in systemctl list-units
systemctl status mybackup.scope
```

### Target (.target)

Le unit .target raggruppano altre unit senza eseguire processi propri. Funzionano come
punti di sincronizzazione (equivalenti concettuali dei runlevel SysVinit).

```ini
# /etc/systemd/system/myapp-full.target
[Unit]
Description=MyApp Full Stack
Requires=myapp-web.service myapp-worker.service
After=myapp-web.service myapp-worker.service
Wants=myapp-monitoring.service

[Install]
WantedBy=multi-user.target
```

```bash
# Portare su tutto lo stack
sudo systemctl start myapp-full.target

# Verificare che tutto è attivo
systemctl list-dependencies myapp-full.target
```

---

## Dipendenze e Ordinamento

Systemd distingue nettamente tra **dipendenze** (cosa avviare) e **ordinamento** (in che
ordine avviare). Senza direttive di ordinamento, le unit con dipendenze vengono avviate
in parallelo.

### Matrice delle dipendenze

| Direttiva | Tipo | Se la dipendenza fallisce | Se la dipendenza si ferma | Avvia la dipendenza |
|---|---|---|---|---|
| `Wants=` | debole | questa continua | nulla | sì |
| `Requires=` | forte | questa fallisce | nulla | sì |
| `Requisite=` | forte+check | questa fallisce | nulla | no (deve essere già attiva) |
| `BindsTo=` | binding | questa fallisce | **questa si ferma** | sì |
| `PartOf=` | parziale | nulla | **questa si ferma** | no |
| `Conflicts=` | esclusione | — | — | ferma l'altra |

### Ordinamento: After= e Before=

```ini
# SOLO ORDINAMENTO (nessuna dipendenza — B non viene avviato automaticamente)
[Unit]
After=network.target               # "Avviami dopo network.target, se è in coda"

# DIPENDENZA + ORDINAMENTO (pattern comune)
[Unit]
Requires=postgresql.service        # "Ho bisogno di postgres"
After=postgresql.service           # "...e aspetta che sia pronto prima di avviarmi"

# ATTENZIONE: Requires senza After → avvio parallelo
# Se il servizio ha bisogno che postgres sia pronto, After è obbligatorio
```

### BindsTo vs Requires vs Wants

```ini
# Wants: "sarebbe bello averlo, ma non è essenziale"
[Unit]
Wants=redis.service                # Se redis fallisce, il mio servizio continua

# Requires: "ne ho bisogno per partire"
[Unit]
Requires=postgresql.service        # Se postgres fallisce all'avvio, anch'io fallisco
                                   # MA: se postgres si ferma dopo, io continuo

# BindsTo: "la mia vita dipende dalla sua"
[Unit]
BindsTo=openvpn.service            # Se openvpn si ferma per qualsiasi motivo, io mi fermo
                                   # Anche se openvpn viene fermato manualmente

# PartOf: "fermami/riavviami insieme a lui, ma non avviarmi"
[Unit]
PartOf=myapp.target                # Se myapp.target viene riavviato, anch'io vengo riavviato
                                   # MA: PartOf non avvia questa unit
```

### Conflicts

```ini
# Due servizi che non possono coesistere
# /etc/systemd/system/iptables.service
[Unit]
Conflicts=firewalld.service        # Se avvio iptables, firewalld viene fermato
                                   # Se avvio firewalld, iptables viene fermato
```

### Dipendenze implicite

Systemd aggiunge automaticamente alcune dipendenze:

```
# DefaultDependencies=yes (default per quasi tutte le unit)
# Aggiunge automaticamente:
#   Requires=sysinit.target
#   After=sysinit.target basic.target
#   Conflicts=shutdown.target
#   Before=shutdown.target
#
# Per unit molto precoci (prima di sysinit), disabilitare:
# DefaultDependencies=no
```

### Visualizzare le dipendenze

```bash
# Albero dipendenze completo
systemctl list-dependencies nginx.service

# Solo dipendenze dirette (non ricorsivo)
systemctl list-dependencies nginx.service --plain

# Dipendenze inverse: chi dipende da questa unit?
systemctl list-dependencies nginx.service --reverse

# Dipendenze Before/After (ordine)
systemctl list-dependencies nginx.service --before
systemctl list-dependencies nginx.service --after

# Verificare che una unit si avvia correttamente con tutte le dipendenze
systemd-analyze verify /etc/systemd/system/myapp.service
```

---

## Socket Activation — Deep Dive

La socket activation è uno dei meccanismi più potenti di systemd. Il principio: systemd
crea il socket e lo passa al servizio quando arriva la prima connessione. Vantaggi:

1. **Avvio on-demand**: il servizio parte solo quando qualcuno si connette
2. **Zero downtime deploy**: il socket resta aperto durante il restart del servizio
3. **Ordine di avvio semplificato**: il socket è disponibile subito, le dipendenze si risolvono
4. **Parallelismo**: i servizi che dipendono dal socket possono partire in parallelo

### Pattern: servizio TCP con socket activation

```ini
# /etc/systemd/system/myapi.socket
[Unit]
Description=MyAPI HTTP Socket

[Socket]
ListenStream=0.0.0.0:8080          # Ascolto su tutte le interfacce, porta 8080
NoDelay=yes                        # TCP_NODELAY
ReusePort=yes                      # SO_REUSEPORT per load-balancing tra worker
BindIPv6Only=default

[Install]
WantedBy=sockets.target
```

```ini
# /etc/systemd/system/myapi.service
[Unit]
Description=MyAPI Service
Requires=myapi.socket
After=network.target

[Service]
Type=simple
ExecStart=/opt/myapi/bin/server
# Il socket viene passato come file descriptor 3 (SD_LISTEN_FDS_START)
# Il servizio usa sd_listen_fds() o controlla $LISTEN_FDS e $LISTEN_PID

# Hardening
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes
DynamicUser=yes
StateDirectory=myapi

# Non avviare da solo — solo tramite socket
# Nessuna sezione [Install]
```

```bash
# Attivare il socket (non il servizio)
sudo systemctl enable --now myapi.socket

# Testare: la prima connessione avvia il servizio
curl http://localhost:8080/health

# Verificare lo stato
systemctl status myapi.socket
systemctl status myapi.service
```

### Pattern: socket UNIX con Accept=yes (inetd-style)

```ini
# /etc/systemd/system/myhandler.socket
[Unit]
Description=Handler per richieste individuali

[Socket]
ListenStream=/run/myhandler.sock
Accept=yes                         # Un'istanza per connessione
MaxConnections=100
MaxConnectionsPerSource=10
SocketMode=0666

[Install]
WantedBy=sockets.target
```

```ini
# /etc/systemd/system/myhandler@.service (NOTA il @ per template)
[Unit]
Description=Handler istanza %i

[Service]
Type=simple
ExecStart=/opt/myhandler/handler
StandardInput=socket               # Il socket viene passato come stdin
StandardOutput=socket              # L'output va al socket
StandardError=journal
DynamicUser=yes
```

### Pattern: attivazione multipla (socket + timer + path)

Un servizio può essere attivato da più sorgenti contemporaneamente:

```ini
# /etc/systemd/system/processor.service
[Unit]
Description=Processore dati multi-attivazione
# Nessuna sezione [Install] — attivato solo tramite socket/timer/path

[Service]
Type=oneshot
ExecStart=/opt/processor/run.sh
```

```ini
# Attivazione via socket
# /etc/systemd/system/processor.socket
[Socket]
ListenStream=/run/processor.sock
[Install]
WantedBy=sockets.target
```

```ini
# Attivazione via timer
# /etc/systemd/system/processor.timer
[Timer]
OnCalendar=*-*-* *:0/15:00
[Install]
WantedBy=timers.target
```

```ini
# Attivazione via filesystem
# /etc/systemd/system/processor.path
[Path]
DirectoryNotEmpty=/srv/inbox/
[Install]
WantedBy=multi-user.target
```

---

## Template Unit (@)

Le template unit permettono di definire un singolo file unit parametrizzato che genera
istanze multiple. Il nome contiene `@` tra il prefisso e il suffisso:
`nome@.service` è il template, `nome@istanza.service` è un'istanza.

### Specifier disponibili nelle template

| Specifier | Significato | Esempio (per `container@web1.service`) |
|---|---|---|
| `%i` | Nome istanza (non escaped) | `web1` |
| `%I` | Nome istanza (escaped) | `web1` |
| `%p` | Prefisso (nome prima di @) | `container` |
| `%P` | Prefisso (unescaped) | `container` |
| `%N` | Nome completo della unit | `container@web1.service` |
| `%n` | Nome completo (legacy) | `container@web1.service` |
| `%f` | Nome istanza come path (/ + unescaped %i) | `/web1` |
| `%t` | Directory runtime | `/run` (system) o `$XDG_RUNTIME_DIR` (user) |
| `%S` | State directory | `/var/lib` (system) |
| `%C` | Cache directory | `/var/cache` (system) |
| `%L` | Log directory | `/var/log` (system) |
| `%h` | Home directory dell'utente | `/home/user` (solo unit utente) |
| `%H` | Hostname della macchina | `myserver` |
| `%m` | Machine ID | `a1b2c3d4...` |
| `%b` | Boot ID | `x1y2z3...` |

### Esempio: container nspawn template

```ini
# /etc/systemd/system/container@.service
[Unit]
Description=Container nspawn %i
After=network.target
Wants=network.target

[Service]
Type=notify
ExecStart=/usr/bin/systemd-nspawn \
  --machine=%i \
  --directory=/var/lib/machines/%i \
  --boot \
  --network-veth
ExecStop=/usr/bin/machinectl terminate %i
KillMode=mixed
Restart=on-failure
RestartSec=10s

# Risorse per container
MemoryMax=2G
CPUQuota=100%
TasksMax=512

[Install]
WantedBy=multi-user.target
```

```bash
# Avviare istanze diverse dallo stesso template
sudo systemctl start container@web1.service
sudo systemctl start container@db1.service
sudo systemctl start container@cache1.service

# Abilitare al boot
sudo systemctl enable container@web1.service

# Override per una singola istanza
sudo systemctl edit container@web1.service
# → crea /etc/systemd/system/container@web1.service.d/override.conf
```

### Esempio: servizio multi-porta con template

```ini
# /etc/systemd/system/webapp@.service
[Unit]
Description=WebApp sulla porta %i
After=network.target

[Service]
Type=simple
ExecStart=/opt/webapp/server --port=%i
User=webapp
Environment=PORT=%i

ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
```

```bash
# Avviare su porte diverse
sudo systemctl start webapp@8001.service
sudo systemctl start webapp@8002.service
sudo systemctl start webapp@8003.service
```

### Esempio: servizio VPN multi-istanza

```ini
# /etc/systemd/system/openvpn@.service
[Unit]
Description=OpenVPN Tunnel %I
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
ExecStart=/usr/sbin/openvpn --config /etc/openvpn/%i.conf
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=10s

CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW CAP_DAC_OVERRIDE
ProtectSystem=strict
ProtectHome=yes
DeviceAllow=/dev/net/tun rw

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now openvpn@office.service
sudo systemctl enable --now openvpn@datacenter.service
```

---

## Drop-in Override

I drop-in permettono di sovrascrivere o estendere singole direttive di una unit senza
copiare l'intero file. Sono il metodo raccomandato per qualsiasi personalizzazione.

### Meccanismo

```
# Struttura del drop-in:
/etc/systemd/system/<unit-name>.d/
├── override.conf          # Creato da systemctl edit
├── 10-limits.conf         # Numerazione per ordinare i drop-in
├── 20-security.conf       # I numeri più alti hanno precedenza
└── 50-custom.conf
```

### Comportamento di merge

```ini
# SOVRASCRITTURA: le direttive scalari vengono sostituite dall'ultimo valore
# Se il file originale ha TimeoutStopSec=90s e il drop-in ha TimeoutStopSec=30s,
# il valore effettivo è 30s

# RESET + AGGIUNTA: le direttive lista (Environment, ExecStartPre, etc.)
# vengono appese. Per sostituirle, prima azzerarle con una riga vuota:
[Service]
Environment=                       # Azzera tutte le variabili precedenti
Environment=NEW_VAR=new_value      # Poi imposta la nuova

ExecStartPre=                      # Azzera tutti i pre-start precedenti
ExecStartPre=/opt/my-pre-start.sh  # Poi imposta il nuovo
```

### Comandi di gestione

```bash
# Creare un drop-in interattivamente (apre $EDITOR)
sudo systemctl edit nginx.service
# → crea /etc/systemd/system/nginx.service.d/override.conf

# Sovrascrivere completamente (sostituzione totale, non drop-in)
sudo systemctl edit --full nginx.service
# → copia in /etc/systemd/system/nginx.service

# Creare drop-in per una unit template (tutte le istanze)
sudo systemctl edit container@.service

# Creare drop-in per una singola istanza
sudo systemctl edit container@web1.service

# Vedere la configurazione risultante (merge di tutti i drop-in)
systemctl cat nginx.service

# Vedere ogni singola proprietà risolta
systemctl show nginx.service

# Vedere le differenze tra file originale e configurazione effettiva
systemd-delta

# Dopo qualsiasi modifica
sudo systemctl daemon-reload
sudo systemctl restart nginx.service
```

### Esempio pratico: hardening di nginx con drop-in

```ini
# /etc/systemd/system/nginx.service.d/hardening.conf
[Service]
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
NoNewPrivileges=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
ReadWritePaths=/var/log/nginx /var/lib/nginx /run/nginx
CapabilityBoundingSet=CAP_NET_BIND_SERVICE CAP_DAC_OVERRIDE
AmbientCapabilities=CAP_NET_BIND_SERVICE
```

```ini
# /etc/systemd/system/nginx.service.d/limits.conf
[Service]
LimitNOFILE=65536
MemoryMax=1G
TasksMax=512
```

---

## Gestione Servizi — Comandi systemctl

```bash
# === STATO ===
systemctl status nginx.service       # Stato dettagliato (PID, log recenti, risorse)
systemctl status nginx               # .service è implicito
systemctl is-active nginx            # Restituisce "active" o "inactive"
systemctl is-enabled nginx           # Restituisce "enabled" o "disabled"
systemctl is-failed nginx            # Verifica se in stato failed
systemctl show nginx                 # TUTTE le proprietà (formato key=value)
systemctl show nginx -p MainPID      # Singola proprietà
systemctl cat nginx                  # Contenuto del file unit (con drop-in)

# === AVVIO E ARRESTO ===
sudo systemctl start nginx           # Avvia il servizio
sudo systemctl stop nginx            # Ferma il servizio
sudo systemctl restart nginx         # Stop + start
sudo systemctl reload nginx          # Ricarica configurazione senza restart
sudo systemctl reload-or-restart nginx  # Reload se supportato, altrimenti restart
sudo systemctl try-restart nginx     # Restart solo se attivo
sudo systemctl try-reload-or-restart nginx  # Idem con reload

# === ABILITAZIONE AL BOOT ===
sudo systemctl enable nginx          # Abilita all'avvio (crea symlink)
sudo systemctl disable nginx         # Disabilita dall'avvio
sudo systemctl enable --now nginx    # Abilita + avvia immediatamente
sudo systemctl disable --now nginx   # Disabilita + ferma immediatamente
sudo systemctl reenable nginx        # Disable + enable (rigenera i symlink)
sudo systemctl preset nginx          # Applica il preset della distribuzione

# === MASCHERAMENTO (impedisce l'avvio anche manuale) ===
sudo systemctl mask nginx            # Maschera (link a /dev/null)
sudo systemctl unmask nginx          # Rimuovi mascheramento

# === LISTA E RICERCA ===
systemctl list-units                 # Tutte le unit caricate
systemctl list-units --type=service  # Solo servizi
systemctl list-units --state=failed  # Unit in errore
systemctl list-units --all           # Include unit inattive
systemctl list-unit-files            # Tutti i file unit (abilitati/disabilitati)
systemctl list-unit-files --type=service --state=enabled
systemctl list-dependencies nginx    # Albero dipendenze
systemctl list-dependencies --reverse nginx  # Chi dipende da nginx
systemctl list-timers                # Timer attivi
systemctl list-sockets               # Socket attivi
systemctl list-machines              # Container/VM

# === RESET E MANUTENZIONE ===
sudo systemctl daemon-reload         # Ricarica tutti i file unit (dopo modifica)
sudo systemctl daemon-reexec         # Riesegui il demone systemd (aggiornamento)
sudo systemctl reset-failed          # Reset stato failed di tutte le unit
sudo systemctl reset-failed nginx    # Reset stato failed di una unit

# === UTENTE (systemd --user) ===
systemctl --user status myapp        # Servizi dell'utente corrente
systemctl --user list-units
systemctl --user enable myapp.service
systemctl --user start myapp.service
```

---

## Creazione Servizi Personalizzati

### Esempio: Applicazione Node.js

```ini
# /etc/systemd/system/nodeapp.service
[Unit]
Description=Node.js Application
After=network.target

[Service]
Type=simple
User=nodeapp
Group=nodeapp
WorkingDirectory=/opt/nodeapp
ExecStart=/usr/bin/node app.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nodeapp
Environment=NODE_ENV=production PORT=3000

# Hardening
ProtectSystem=full
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
```

### Esempio: Script Python con Virtualenv

```ini
# /etc/systemd/system/pyapp.service
[Unit]
Description=Python Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=pyapp
Group=pyapp
WorkingDirectory=/opt/pyapp
ExecStart=/opt/pyapp/venv/bin/python main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
EnvironmentFile=/etc/pyapp/env

[Install]
WantedBy=multi-user.target
```

### Esempio: Servizio Oneshot (script di manutenzione)

```ini
# /etc/systemd/system/cleanup.service
[Unit]
Description=Pulizia File Temporanei

[Service]
Type=oneshot
ExecStart=/usr/local/bin/cleanup.sh
RemainAfterExit=no

# Nessuna sezione [Install] — attivato da timer
```

### Attivazione via Socket

```ini
# /etc/systemd/system/myapp.socket
[Unit]
Description=MyApp Socket

[Socket]
ListenStream=8080
Accept=no

[Install]
WantedBy=sockets.target
```

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=MyApp Service
Requires=myapp.socket

[Service]
Type=simple
ExecStart=/opt/myapp/server
StandardInput=socket
```

Il servizio viene avviato solo quando arriva una connessione sulla porta 8080 (socket activation).

---

## Target e Boot Process

### Boot Process Linux con Systemd

```
Firmware (UEFI/BIOS)
  → Boot loader (GRUB2)
    → Kernel + initramfs
      → systemd (PID 1)
        → default.target (tipicamente graphical.target o multi-user.target)
          → Tutte le unit dipendenti vengono avviate in parallelo
```

### Target Principali

| Target | Equivalente SysVinit | Descrizione |
|---|---|---|
| `poweroff.target` | Runlevel 0 | Spegnimento |
| `rescue.target` | Runlevel 1 | Single user, filesystem montato |
| `multi-user.target` | Runlevel 3 | Multi-user, rete, no GUI |
| `graphical.target` | Runlevel 5 | Multi-user + GUI |
| `reboot.target` | Runlevel 6 | Riavvio |
| `emergency.target` | — | Shell di emergenza (root filesystem read-only) |

### Gestione Target

```bash
# Vedere il target corrente
systemctl get-default

# Cambiare il target di default
sudo systemctl set-default multi-user.target    # Server senza GUI
sudo systemctl set-default graphical.target     # Desktop con GUI

# Cambiare target al volo (come cambiare runlevel)
sudo systemctl isolate multi-user.target        # Passa a multi-user
sudo systemctl isolate rescue.target            # Passa a rescue mode

# Spegnimento e riavvio
sudo systemctl poweroff
sudo systemctl reboot
sudo systemctl halt
sudo systemctl suspend
sudo systemctl hibernate

# Al boot (da GRUB): aggiungere al kernel command line
# systemd.unit=rescue.target      → avvia in rescue
# systemd.unit=emergency.target   → avvia in emergency
```

### Dipendenze dei Target

```bash
# Vedere cosa include un target
systemctl list-dependencies multi-user.target

# Vedere l'ordine di boot
systemd-analyze                    # Tempo totale di boot
systemd-analyze blame              # Tempo per ogni unit (ordine decrescente)
systemd-analyze critical-chain     # Catena critica (path più lento)
systemd-analyze plot > boot.svg    # Grafico SVG del boot
```

---

## Systemd Timers

I timer di systemd sono il sostituto moderno di cron. Offrono: logging integrato con journald, dipendenze da altre unit, attivazione monotonica o calendario, gestione errori con restart.

### Timer Monotonic (relativo al boot/attivazione)

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Backup Timer

[Timer]
OnBootSec=15min                   # 15 minuti dopo il boot
OnUnitActiveSec=6h                # Ogni 6 ore dall'ultima attivazione
AccuracySec=1min                  # Precisione (default 1min, riduce wakeup)
Persistent=yes                     # Recupera esecuzioni perse se il sistema era spento

[Install]
WantedBy=timers.target
```

### Timer Calendar (assoluto, come cron)

```ini
# /etc/systemd/system/report.timer
[Unit]
Description=Report Giornaliero

[Timer]
OnCalendar=*-*-* 02:00:00        # Ogni giorno alle 02:00
# OnCalendar=Mon *-*-* 09:00:00  # Ogni lunedì alle 09:00
# OnCalendar=*-*-01 00:00:00     # Primo del mese a mezzanotte
# OnCalendar=hourly               # Ogni ora
# OnCalendar=daily                # Ogni giorno a mezzanotte
# OnCalendar=weekly               # Ogni lunedì a mezzanotte
RandomizedDelaySec=30min           # Ritardo random (evita thundering herd)
Persistent=yes

[Install]
WantedBy=timers.target
```

### Formato OnCalendar

```
DayOfWeek Year-Month-Day Hour:Minute:Second

Esempi:
  Mon,Tue *-*-* 08:00:00          # Lunedì e martedì alle 8
  *-*-* *:00,30:00                # Ogni 30 minuti
  Sat *-*-1..7 00:00:00           # Primo sabato del mese
  *-01,07-01 00:00:00             # 1 gennaio e 1 luglio

# Validare un'espressione
systemd-analyze calendar "Mon *-*-* 08:00:00"
systemd-analyze calendar "daily" --iterations=5   # Prossime 5 esecuzioni
```

### Gestione Timer

```bash
# Abilitare e avviare
sudo systemctl enable --now backup.timer

# Lista timer attivi
systemctl list-timers --all

# Stato di un timer
systemctl status backup.timer

# Eseguire manualmente il servizio associato
sudo systemctl start backup.service

# Cron equivalenze
# */5 * * * *          → OnCalendar=*-*-* *:0/5:00
# 0 2 * * *           → OnCalendar=*-*-* 02:00:00
# 0 0 * * 0           → OnCalendar=Sun *-*-* 00:00:00
# 0 0 1 * *           → OnCalendar=*-*-01 00:00:00
```

### Timer Transient (temporaneo, senza file)

```bash
# Eseguire un comando tra 30 minuti
systemd-run --on-active=30min /usr/local/bin/cleanup.sh

# Eseguire a un orario specifico
systemd-run --on-calendar="2024-12-31 23:59:00" /usr/local/bin/happy-new-year.sh

# Con nome e descrizione
systemd-run --unit=mytask --description="Task temporaneo" --on-active=1h /usr/local/bin/task.sh
```

---

## Journald e Logging

### journalctl — Query dei Log

```bash
# QUERY BASE
journalctl                         # Tutti i log (dall'ultimo boot)
journalctl -b                      # Solo boot corrente
journalctl -b -1                   # Boot precedente
journalctl --list-boots             # Lista dei boot registrati

# FILTRI PER UNIT
journalctl -u nginx.service        # Log di nginx
journalctl -u nginx -u php-fpm     # Log di più unit

# FILTRI TEMPORALI
journalctl --since "2024-01-15 10:00:00"
journalctl --since "1 hour ago"
journalctl --since today
journalctl --since yesterday --until today

# FILTRI PER PRIORITÀ
journalctl -p err                  # Solo errori e più gravi
# Priorità: emerg(0), alert(1), crit(2), err(3), warning(4), notice(5), info(6), debug(7)
journalctl -p warning..err         # Da warning a err

# FILTRI PER PROCESSO/UTENTE
journalctl _PID=1234
journalctl _UID=1000
journalctl _COMM=sshd              # Per nome comando

# SEGUIRE IN TEMPO REALE
journalctl -f                      # Follow (come tail -f)
journalctl -fu nginx               # Follow di una unit specifica

# FORMATO OUTPUT
journalctl -o verbose              # Tutti i campi
journalctl -o json                 # JSON
journalctl -o json-pretty          # JSON formattato
journalctl -o short-iso            # Timestamp ISO 8601
journalctl -o cat                  # Solo messaggio, senza metadata

# PAGINAZIONE
journalctl -n 50                   # Ultime 50 righe
journalctl --no-pager              # Senza paginazione (per script)
journalctl --no-pager -n 100 -u nginx -p err  # Combinazione tipica

# DIMENSIONE LOG
journalctl --disk-usage            # Spazio usato dai log
```

### Configurazione Journald

```ini
# /etc/systemd/journald.conf

[Journal]
Storage=persistent                 # persistent = salva in /var/log/journal/
                                   # volatile = solo in /run/log/journal/ (RAM)
                                   # auto = persistent se /var/log/journal/ esiste
Compress=yes                       # Comprimi log
SystemMaxUse=500M                  # Spazio massimo su disco
SystemKeepFree=1G                  # Spazio minimo da mantenere libero
SystemMaxFileSize=50M              # Dimensione massima per file
RuntimeMaxUse=200M                 # Spazio massimo in RAM
MaxRetentionSec=1month             # Retention temporale
MaxLevelStore=info                 # Livello massimo da salvare
ForwardToSyslog=no                 # Inoltra a syslog (no se usi solo journald)
```

```bash
# Applicare le modifiche
sudo systemctl restart systemd-journald

# Pulizia manuale
sudo journalctl --vacuum-size=200M    # Riduci a 200MB
sudo journalctl --vacuum-time=30d     # Rimuovi log più vecchi di 30 giorni
sudo journalctl --vacuum-files=5      # Mantieni solo 5 file di log

# Verificare integrità
journalctl --verify
```

---

## Systemd-networkd e Systemd-resolved

### Systemd-networkd

Gestore di rete leggero, ideale per server e container. Alternativa a NetworkManager.

```ini
# /etc/systemd/network/20-wired.network
[Match]
Name=eth0                          # Interfaccia (supporta wildcard: en*)

[Network]
DHCP=yes                           # DHCP
# Oppure configurazione statica:
# Address=192.168.1.100/24
# Gateway=192.168.1.1
# DNS=8.8.8.8 8.8.4.4

[DHCPv4]
UseDNS=yes
UseNTP=yes
RouteMetric=100
```

```ini
# Configurazione statica
# /etc/systemd/network/10-static.network
[Match]
Name=eth0

[Network]
Address=10.0.0.10/24
Gateway=10.0.0.1
DNS=10.0.0.1
DNS=8.8.8.8
Domains=example.com
NTP=pool.ntp.org

[Route]
Gateway=10.0.0.1
Destination=172.16.0.0/16
```

```ini
# Bridge
# /etc/systemd/network/br0.netdev
[NetDev]
Name=br0
Kind=bridge

# /etc/systemd/network/br0.network
[Match]
Name=br0

[Network]
Address=192.168.1.1/24
```

```bash
# Abilitare
sudo systemctl enable --now systemd-networkd

# Stato
networkctl                          # Lista interfacce
networkctl status eth0              # Dettaglio interfaccia
networkctl list                     # Lista con stato
```

### Systemd-resolved

Resolver DNS con caching e DNSSEC.

```bash
# Abilitare
sudo systemctl enable --now systemd-resolved

# Collegare /etc/resolv.conf a resolved
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf

# Stato e diagnostica
resolvectl status                  # Stato generale
resolvectl query example.com       # Query DNS
resolvectl statistics              # Statistiche cache
resolvectl flush-caches            # Svuota cache

# Configurazione: /etc/systemd/resolved.conf
# [Resolve]
# DNS=8.8.8.8 8.8.4.4
# FallbackDNS=1.1.1.1
# DNSSEC=allow-downgrade
# DNSOverTLS=opportunistic
# Cache=yes
```

---

## Cgroups e Resource Control

Systemd usa i cgroups (control groups) del kernel per limitare e monitorare le risorse (CPU, memoria, I/O) dei servizi.

### Limitazione Risorse nei Servizi

```ini
# Nel file .service o in un drop-in
[Service]
# CPU
CPUQuota=50%                       # Max 50% di un core
CPUWeight=100                      # Peso relativo (default 100, range 1-10000)
AllowedCPUs=0-3                    # Solo core 0-3

# MEMORIA
MemoryMax=512M                     # Limite hard (OOM kill se superato)
MemoryHigh=400M                    # Limite soft (throttling)
MemorySwapMax=0                    # Disabilita swap per questo servizio

# I/O DISCO
IOWeight=100                       # Peso relativo I/O (1-10000)
IOReadBandwidthMax=/dev/sda 50M    # Limite lettura
IOWriteBandwidthMax=/dev/sda 20M   # Limite scrittura
IOReadIOPSMax=/dev/sda 1000        # Limite IOPS lettura

# PROCESSI
TasksMax=512                       # Numero massimo di processi/thread

# RETE (con eBPF, systemd 250+)
IPAddressAllow=192.168.1.0/24
IPAddressDeny=any
```

### Slice e Gerarchia Cgroup

```
-.slice (root)
├── system.slice         → Servizi di sistema
│   ├── nginx.service
│   ├── postgresql.service
│   └── ...
├── user.slice           → Sessioni utente
│   ├── user-1000.slice
│   └── user-1001.slice
└── machine.slice        → Container e VM
```

```bash
# Monitorare l'uso delle risorse
systemd-cgtop                      # Top per cgroup (CPU, memoria, I/O)
systemctl status nginx             # Mostra cgroup e risorse del servizio
systemctl show nginx -p MemoryCurrent  # Memoria attuale
systemctl show nginx -p CPUUsageNSec   # Tempo CPU usato

# Impostare limiti runtime (senza modificare il file)
sudo systemctl set-property nginx.service MemoryMax=1G
sudo systemctl set-property nginx.service CPUQuota=200%  # 2 core

# Creare uno slice personalizzato
# /etc/systemd/system/webapps.slice
[Unit]
Description=Web Applications Slice

[Slice]
MemoryMax=4G
CPUQuota=300%
```

```ini
# Assegnare un servizio a uno slice
[Service]
Slice=webapps.slice
```

### Monitoraggio Risorse

```bash
# Risorse per unit
systemctl status nginx.service
# → CGroup: /system.slice/nginx.service
#   Memory: 45.2M (max: 512.0M)
#   CPU: 1.234s

# Dettaglio completo
systemctl show nginx.service | grep -E 'Memory|CPU|Tasks|IO'

# Cgroup filesystem diretto
ls /sys/fs/cgroup/system.slice/nginx.service/
cat /sys/fs/cgroup/system.slice/nginx.service/memory.current
cat /sys/fs/cgroup/system.slice/nginx.service/cpu.stat
```

---

## Best Practices

1. **Drop-in override, mai modificare file del pacchetto**: usare `systemctl edit` o creare file in `.d/` per personalizzare. I file in `/usr/lib/systemd/system/` verranno sovrascritti dagli aggiornamenti
2. **Hardening dei servizi**: applicare `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateTmp=yes`, `NoNewPrivileges=yes` a ogni servizio custom. Usare `systemd-analyze security myapp.service` per un audit
3. **Timer invece di cron**: i timer di systemd offrono logging integrato, dipendenze, persistent (recupero esecuzioni perse), e gestione risorse. Migrare i cron job a systemd timer
4. **Log strutturati**: usare journald come primario. Configurare retention e dimensione massima. Per centralizzazione, esportare a un SIEM
5. **Resource control**: impostare `MemoryMax` e `TasksMax` su ogni servizio di produzione per evitare che un singolo servizio esaurisca le risorse del sistema
6. **Analisi del boot**: eseguire periodicamente `systemd-analyze blame` per identificare servizi che rallentano il boot. Disabilitare unit non necessarie
7. **Nomi descrittivi**: usare nomi .service chiari e `Description=` dettagliate per facilitare il troubleshooting

---

## Troubleshooting

**"Job for X.service failed"** → `systemctl status X.service` per il messaggio di errore. `journalctl -xeu X.service` per i log dettagliati. Verificare: il binario `ExecStart` esiste ed è eseguibile? L'utente `User=` esiste? Le directory esistono e hanno i permessi corretti? Testare il comando manualmente come lo stesso utente.

**"A]ctivation via systemd failed"** → `systemctl daemon-reload` dopo ogni modifica ai file unit. Verificare la sintassi con `systemd-analyze verify /etc/systemd/system/myapp.service`. Errori comuni: spazi prima di `=`, sezioni mancanti, direttive nella sezione sbagliata.

**"Start request repeated too quickly"** → Il servizio crasha ripetutamente e raggiunge `StartLimitBurst`. Risolvere la causa del crash (controllare i log). Per sbloccare temporaneamente: `sudo systemctl reset-failed X.service`, poi `sudo systemctl start X.service`. Per aumentare i limiti: `StartLimitBurst=10` e `StartLimitIntervalSec=120`.

**"Unit is masked"** → Il servizio è mascherato (link a `/dev/null`). `sudo systemctl unmask X.service` per sbloccarlo. Verificare chi e perché l'ha mascherato prima di riattivarlo.

**"Boot lento"** → `systemd-analyze blame` per identificare i servizi lenti. `systemd-analyze critical-chain` per il path critico. Soluzioni: disabilitare servizi non necessari, verificare timeout di servizi che aspettano risorse di rete (aggiungere `TimeoutStartSec=` più aggressivo), controllare mount di filesystem remoti.

**"Log che riempiono il disco"** → Configurare `SystemMaxUse=` e `MaxRetentionSec=` in `/etc/systemd/journald.conf`. Pulizia immediata: `journalctl --vacuum-size=200M`. Identificare il servizio che produce più log: `journalctl --disk-usage` e poi `journalctl -u servizio | wc -l` per ogni sospetto.

**"Servizio in stato degraded"** → `systemctl --failed` per elencare tutte le unit fallite. Per ogni unit fallita, verificare i log con `journalctl -xeu unit.service`. Se il servizio non è necessario, disabilitarlo o mascherarlo. Se è necessario, risolvere il problema e poi `systemctl reset-failed unit.service`.

**"ExecStart non trovato"** → Il binario specificato in `ExecStart=` non esiste o non è eseguibile. Verificare il percorso con `which` o `type`. Controllare che i permessi siano corretti (`chmod +x`). Se il servizio usa un virtualenv o un path non standard, usare il percorso assoluto completo.

**"Timeout durante l'avvio"** → Il servizio non segnala la prontezza entro `TimeoutStartSec=`. Per servizi `Type=notify`, verificare che il processo invii `sd_notify("READY=1")`. Per servizi `Type=forking`, verificare che il PIDFile sia scritto correttamente. Aumentare `TimeoutStartSec=` se il servizio ha legittimamente bisogno di più tempo (es. Java, database).

**"Permission denied su file socket"** → Controllare `SocketUser=`, `SocketGroup=`, `SocketMode=` nella unit .socket. Verificare che l'utente del servizio abbia accesso al socket. Per socket UNIX, controllare anche i permessi della directory contenente.

**"Dipendenza ciclica"** → `systemd-analyze verify myapp.service` rileva cicli. Rimuovere dipendenze non necessarie. Usare `After=` senza `Requires=` dove serve solo l'ordinamento. Verificare che non ci siano dipendenze implicite che creano il ciclo.

**"Cgroup: Killed process"** → Il kernel OOM killer o systemd-oomd ha terminato il processo per eccesso di memoria. Aumentare `MemoryMax=` se il servizio necessita legittimamente di più memoria. Verificare perdite di memoria nell'applicazione. Controllare `systemd-cgtop` per monitorare l'uso.

**"Socket activation non funziona"** → Verificare che il socket sia attivo (`systemctl status myapp.socket`) e il servizio no. Il servizio deve accettare i file descriptor passati da systemd (variabili `LISTEN_FDS` e `LISTEN_PID`). Verificare che `Accept=` nel socket corrisponda al design del servizio.

---

## Security Sandboxing

Il sandboxing di systemd è uno degli strumenti più potenti per la difesa in profondità su Linux.
Ogni servizio può essere confinato con decine di direttive che limitano l'accesso al filesystem,
alla rete, ai dispositivi, alle capability e ai namespace. L'obiettivo è ridurre la superficie
di attacco: anche se un servizio viene compromesso, l'attaccante ha accesso minimo al sistema.

### systemd-analyze security — Audit Automatico

```bash
# Audit di sicurezza di un singolo servizio
systemd-analyze security nginx.service
# Output: tabella con punteggio per ogni direttiva di hardening
# Punteggio finale: 0.0 (più sicuro) → 10.0 (meno sicuro)

# Audit di tutti i servizi
systemd-analyze security

# Output tipico:
#  UNIT                           EXPOSURE
#  systemd-journald.service       2.4 OK
#  sshd.service                   9.6 UNSAFE
#  nginx.service                  9.2 UNSAFE
#  myapp.service                  4.1 OK

# Audit con formato JSON (utile per automazione)
systemd-analyze security nginx.service --json=pretty

# Verificare la sintassi del file unit
systemd-analyze verify /etc/systemd/system/myapp.service

# Analizzare le capability effettive
systemd-analyze capability myapp.service
```

Il punteggio di esposizione valuta decine di direttive raggruppate in categorie:

| Categoria | Direttive valutate |
|---|---|
| Filesystem | `ProtectSystem=`, `ProtectHome=`, `ReadOnlyPaths=`, `InaccessiblePaths=` |
| Namespace | `PrivateTmp=`, `PrivateDevices=`, `PrivateNetwork=`, `PrivateUsers=` |
| Capability | `CapabilityBoundingSet=`, `AmbientCapabilities=`, `NoNewPrivileges=` |
| Syscall | `SystemCallFilter=`, `SystemCallArchitectures=` |
| Network | `RestrictAddressFamilies=`, `IPAddressDeny=` |
| Identità | `DynamicUser=`, `User=`, `SupplementaryGroups=` |

### Direttive di Hardening — Riferimento Completo

#### Protezione del Filesystem

```ini
[Service]
# === PROTECTSYSTEM ===
# Rende il filesystem read-only a livelli crescenti
ProtectSystem=no            # Nessuna protezione (default)
ProtectSystem=yes           # /usr e /boot read-only
ProtectSystem=full          # /usr, /boot e /etc read-only
ProtectSystem=strict        # Intero filesystem read-only tranne /dev, /proc, /sys
                            # Usare ReadWritePaths= per eccezioni

# === PROTECTHOME ===
ProtectHome=yes             # /home, /root, /run/user inaccessibili
ProtectHome=read-only       # Home directory in sola lettura
ProtectHome=tmpfs           # Mount tmpfs vuoto al posto di /home

# === PERCORSI PERSONALIZZATI ===
ReadWritePaths=/var/lib/myapp /var/log/myapp    # Eccezioni scrivibili
ReadOnlyPaths=/etc/myapp                        # Forzare sola lettura
InaccessiblePaths=/srv/secrets                  # Completamente inaccessibile
TemporaryFileSystem=/var:ro                     # Tmpfs temporaneo con opzioni
BindPaths=/data/shared:/mnt/data                # Bind mount nel namespace
BindReadOnlyPaths=/etc/ssl/certs                # Bind mount read-only

# === PROTEZIONE DIRECTORY DI STATO ===
# systemd crea e gestisce automaticamente queste directory
StateDirectory=myapp                  # → /var/lib/myapp (proprietà del servizio)
CacheDirectory=myapp                  # → /var/cache/myapp
LogsDirectory=myapp                   # → /var/log/myapp
ConfigurationDirectory=myapp          # → /etc/myapp
RuntimeDirectory=myapp                # → /run/myapp (cancellato allo stop)
RuntimeDirectoryPreserve=restart      # Preserva /run/myapp tra i restart
```

#### Namespace e Isolamento

```ini
[Service]
# === PRIVATE NAMESPACE ===
PrivateTmp=yes              # /tmp e /var/tmp isolati per il servizio
                            # Previene attacchi symlink e file temporanei condivisi

PrivateDevices=yes          # Accesso solo a /dev/null, /dev/zero, /dev/random
                            # Blocca accesso a dispositivi fisici (dischi, USB, ecc.)

PrivateNetwork=yes          # Network namespace isolato (solo loopback)
                            # Utile per servizi che non necessitano rete

PrivateUsers=yes            # User namespace isolato (nss mapping separato)
                            # Impedisce accesso a utenti/gruppi del sistema host

PrivateMounts=yes           # Mount namespace isolato
                            # I mount del servizio non sono visibili al sistema

PrivateIPC=yes              # IPC namespace isolato (shm, semafori, code messaggi)
                            # Previene interferenze IPC tra servizi (v253+)

PrivatePIDs=yes             # PID namespace isolato — il servizio vede solo i suoi PID
                            # Utile per container-like isolation (v256+)

# === MOUNT PROPAGATION ===
MountFlags=slave            # I mount del sistema si propagano al servizio
                            # ma non viceversa (default sicuro)

# === PROTEZIONE KERNEL ===
ProtectKernelTunables=yes   # /proc/sys, /sys read-only (no sysctl modifiche)
ProtectKernelModules=yes    # Blocca caricamento moduli kernel
ProtectKernelLogs=yes       # Blocca accesso al buffer log del kernel (/dev/kmsg)
ProtectHostname=yes         # Impedisce la modifica dell'hostname
ProtectClock=yes            # Impedisce la modifica dell'orologio di sistema
ProtectControlGroups=yes    # Gerarchia cgroup read-only

# === LOCK PERSONALITÀ ===
LockPersonality=yes         # Impedisce di cambiare la execution domain
                            # Previene attacchi via personality(2)

# === PROCFS/SYSFS ===
ProcSubset=pid              # Mostra solo /proc/pid, nasconde /proc/sched_debug ecc.
ProtectProc=invisible       # Nasconde processi di altri utenti in /proc
                            # Valori: default, invisible, noaccess, ptraceable
```

#### Capability e Privilegi

```ini
[Service]
# === NESSUN NUOVO PRIVILEGIO ===
NoNewPrivileges=yes         # Impedisce l'escalation di privilegi
                            # Blocca setuid, setgid, file capabilities
                            # DEVE essere abilitato su ogni servizio custom

# === CAPABILITY BOUNDING SET ===
# Limita le capability del processo (vedi capabilities(7))
CapabilityBoundingSet=                          # Rimuovi TUTTE le capability
CapabilityBoundingSet=CAP_NET_BIND_SERVICE      # Solo bind su porte <1024
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW # Per strumenti di rete
CapabilityBoundingSet=~CAP_SYS_ADMIN            # Tutte TRANNE SYS_ADMIN (con ~)

# === AMBIENT CAPABILITIES ===
# Capability passate ai processi figli (necessita NoNewPrivileges=no o capability ereditarie)
AmbientCapabilities=CAP_NET_BIND_SERVICE        # Il processo non-root può bindare porte basse

# === SECUREBITS ===
SecureBits=noroot-locked keep-caps-locked       # Blocca transizioni di privilegio root

# === FILTRO SYSCALL ===
SystemCallFilter=@system-service                # Consenti solo syscall tipiche dei servizi
SystemCallFilter=~@mount                        # Blocca syscall di mount
SystemCallFilter=~@debug                        # Blocca ptrace e debug
SystemCallFilter=~@clock                        # Blocca modifica orologio
SystemCallFilter=~@obsolete                     # Blocca syscall obsolete
SystemCallFilter=~@privileged                   # Blocca syscall privilegiate
SystemCallFilter=~@raw-io                       # Blocca I/O raw (accesso diretto disco)
SystemCallErrorNumber=EPERM                     # Errore restituito per syscall bloccate
                                                # (default: SIGSYS → kill del processo)
SystemCallArchitectures=native                  # Solo architettura nativa (no compat 32-bit)

# === RESTRIZIONI RETE ===
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX  # Solo IPv4, IPv6 e socket UNIX
RestrictAddressFamilies=~AF_NETLINK AF_PACKET     # Blocca netlink e raw packet

# === ALTRE RESTRIZIONI ===
RestrictNamespaces=yes      # Impedisce la creazione di nuovi namespace
RestrictRealtime=yes        # Impedisce scheduling realtime
RestrictSUIDSGID=yes        # Impedisce la creazione di file SUID/SGID
MemoryDenyWriteExecute=yes  # Blocca mappatura memoria W+X (anti exploit)
                            # NOTA: rompe JIT (Node.js, Java, Python con cextensions)
UMask=0077                  # Maschera permessi restrittiva per file creati
```

### Esempio Completo: Servizio Hardened

```ini
# /etc/systemd/system/webapp.service
[Unit]
Description=Web Application Hardened
After=network.target

[Service]
Type=exec
User=webapp
Group=webapp
ExecStart=/opt/webapp/bin/server

# === FILESYSTEM ===
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/var/lib/webapp /var/log/webapp
StateDirectory=webapp
LogsDirectory=webapp

# === NAMESPACE ===
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectHostname=yes
ProtectClock=yes
PrivateUsers=yes
PrivateIPC=yes

# === PRIVILEGI ===
NoNewPrivileges=yes
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
SecureBits=noroot-locked

# === SYSCALL ===
SystemCallFilter=@system-service
SystemCallFilter=~@mount @debug @clock @obsolete @raw-io
SystemCallArchitectures=native
SystemCallErrorNumber=EPERM

# === RETE ===
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

# === RESTRIZIONI AGGIUNTIVE ===
RestrictNamespaces=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
LockPersonality=yes
MemoryDenyWriteExecute=no  # Necessario per runtime con JIT
UMask=0077

# === RISORSE ===
MemoryMax=512M
TasksMax=256
CPUQuota=100%

# === RESTART ===
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
# Verificare il punteggio di hardening
systemd-analyze security webapp.service
# → Punteggio atteso: 1.5-2.5 (SAFE)

# Confrontare prima e dopo il hardening
systemd-analyze security webapp.service --json=short | jq '.exposure'
```

### Hardening Progressivo — Strategia Pratica

La strategia raccomandata per l'hardening è progressiva. Non attivare tutte le direttive
in una volta: procedere in fasi e testare dopo ogni modifica.

**Fase 1 — Base** (nessun impatto sulla maggior parte dei servizi):
```ini
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
```

**Fase 2 — Intermedio** (può richiedere aggiustamenti):
```ini
ProtectKernelLogs=yes
ProtectHostname=yes
ProtectClock=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
LockPersonality=yes
CapabilityBoundingSet=~CAP_SYS_ADMIN
```

**Fase 3 — Avanzato** (testare attentamente):
```ini
SystemCallFilter=@system-service
SystemCallArchitectures=native
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
RestrictNamespaces=yes
PrivateUsers=yes
MemoryDenyWriteExecute=yes  # Solo se il runtime lo supporta
```

---

## Systemd-analyze — Ottimizzazione e Audit

`systemd-analyze` è uno strumento multi-funzione per l'analisi delle prestazioni del boot,
la verifica delle configurazioni e il debugging delle dipendenze.

### Comandi Principali

```bash
# === ANALISI BOOT ===
systemd-analyze                          # Tempo totale: firmware, loader, kernel, userspace
systemd-analyze time                     # Stesso output (forma esplicita)

# Output tipico:
# Startup finished in 3.456s (firmware) + 1.234s (loader) + 2.567s (kernel) + 8.901s (userspace) = 16.158s
# graphical.target reached after 8.456s in userspace

# === BLAME — CHI RALLENTA IL BOOT ===
systemd-analyze blame                    # Lista unit ordinate per tempo di avvio
# Output:
# 5.432s NetworkManager-wait-online.service
# 2.345s plymouth-quit-wait.service
# 1.234s systemd-journal-flush.service
# 0.987s firewalld.service

# === CRITICAL-CHAIN — PERCORSO CRITICO ===
systemd-analyze critical-chain           # Catena di dipendenze più lenta
systemd-analyze critical-chain graphical.target  # Da un target specifico

# Output:
# graphical.target @8.456s
# └─multi-user.target @8.434s
#   └─nginx.service @7.234s +1.200s
#     └─network-online.target @7.200s
#       └─NetworkManager-wait-online.service @1.234s +5.966s

# === PLOT — GRAFICO SVG ===
systemd-analyze plot > /tmp/boot.svg     # Diagramma temporale completo del boot
# Aprire con un browser: firefox /tmp/boot.svg

# === DOT — GRAFO DIPENDENZE ===
systemd-analyze dot nginx.service | dot -Tsvg > /tmp/deps.svg
systemd-analyze dot --to-pattern='*.target' | dot -Tsvg > /tmp/targets.svg
systemd-analyze dot --from-pattern='sshd.*' --to-pattern='*.target'

# === VERIFICA UNIT ===
systemd-analyze verify /etc/systemd/system/myapp.service  # Controlla errori
systemd-analyze verify --user ~/.config/systemd/user/myapp.service

# === CALENDAR — VALIDAZIONE ESPRESSIONI TIMER ===
systemd-analyze calendar "Mon *-*-* 08:00:00"
systemd-analyze calendar "daily" --iterations=10   # Prossime 10 esecuzioni

# === CAT-CONFIG — CONFIGURAZIONE EFFETTIVA ===
systemd-analyze cat-config systemd/journald.conf   # Configurazione con tutti i drop-in

# === CONDITION — TEST CONDIZIONI ===
systemd-analyze condition 'ConditionPathExists=/etc/myapp/config.yml'
# Restituisce exit code 0 se la condizione è vera, 1 altrimenti

# === DUMP — STATO INTERNO COMPLETO ===
systemd-analyze dump                     # Dump di tutte le unit e il loro stato
systemd-analyze dump nginx.service       # Dump di una singola unit

# === UNIT-PATHS — PERCORSI DI RICERCA ===
systemd-analyze unit-paths               # Elenco di tutte le directory di ricerca unit
systemd-analyze unit-paths --user        # Per le unit utente

# === COMPARE-VERSIONS ===
systemd-analyze compare-versions 255 ge 250    # Test: 255 >= 250?
# Utile in script per logica condizionale basata sulla versione di systemd

# === INSPECT-ELF ===
systemd-analyze inspect-elf /usr/bin/myapp   # Analizza l'ELF per caratteristiche di sicurezza
# Verifica: PIE, RELRO, Stack Canary, NX, FORTIFY_SOURCE
```

### Analisi Avanzata delle Dipendenze

```bash
# Verificare perché una unit è stata avviata
systemctl show -p WantedBy,RequiredBy,TriggeredBy nginx.service

# Trovare dipendenze circolari
systemd-analyze verify --recursive-errors=yes /etc/systemd/system/

# Elencare unit che bloccano il boot
systemd-analyze critical-chain --fuzz=100ms    # Mostra solo unit con delay >100ms

# Analizzare i tempi di attivazione di tutti i socket
systemd-analyze blame | grep socket

# Confrontare due boot
systemd-analyze blame > /tmp/blame-before.txt
# (dopo le ottimizzazioni)
systemd-analyze blame > /tmp/blame-after.txt
diff /tmp/blame-before.txt /tmp/blame-after.txt
```

---

## Boot Performance Tuning

L'ottimizzazione dei tempi di avvio è critica per server, VM, container e dispositivi IoT.
Systemd offre strumenti precisi per identificare e risolvere i colli di bottiglia.

### Strategia di Ottimizzazione in 5 Fasi

**Fase 1: Misurare il baseline**

```bash
systemd-analyze                          # Tempo totale
systemd-analyze blame | head -20         # Top 20 servizi più lenti
systemd-analyze critical-chain           # Percorso critico
systemd-analyze plot > /tmp/boot-baseline.svg  # Salvataggio visuale
```

**Fase 2: Eliminare servizi non necessari**

```bash
# Identificare servizi abilitati ma non necessari
systemctl list-unit-files --state=enabled --type=service

# Servizi comuni da disabilitare su server headless
sudo systemctl disable bluetooth.service       # Bluetooth
sudo systemctl disable ModemManager.service    # Modem
sudo systemctl disable avahi-daemon.service    # mDNS/Zeroconf
sudo systemctl disable cups.service            # Stampa
sudo systemctl disable accounts-daemon.service # Account GUI

# Mascherare servizi non necessari (impedisce anche l'avvio manuale)
sudo systemctl mask plymouth-quit-wait.service  # Plymouth (splash screen)
```

**Fase 3: Ottimizzare i servizi lenti**

```bash
# NetworkManager-wait-online.service — spesso il più lento
# Ridurre il timeout
sudo systemctl edit NetworkManager-wait-online.service
# [Service]
# TimeoutStartSec=10s

# In alternativa, se la rete non è necessaria all'avvio
sudo systemctl disable NetworkManager-wait-online.service

# systemd-journal-flush.service — può essere lento su dischi meccanici
# Verificare la dimensione del journal
journalctl --disk-usage
# Se troppo grande, limitare
sudo journalctl --vacuum-size=100M
```

**Fase 4: Parallelizzare dove possibile**

```ini
# Rimuovere ordinamenti non necessari
# Se un servizio non ha realmente bisogno di network.target:
[Unit]
# PRIMA (serializzato):
# After=network.target network-online.target
# Requires=network.target

# DOPO (parallelo se non serve la rete):
Wants=network.target
# Nessun After= → avvio parallelo
```

**Fase 5: Misurare il risultato**

```bash
systemd-analyze                          # Confronto con baseline
systemd-analyze blame | head -20
systemd-analyze critical-chain
systemd-analyze plot > /tmp/boot-optimized.svg
```

### Ottimizzazione initramfs

```bash
# Verificare il tempo dell'initramfs
systemd-analyze                          # Riga "kernel" include initramfs

# Su sistemi con dracut
dracut --force --no-hostonly             # Rigenerare con meno moduli
dracut --list-modules                    # Moduli inclusi

# Su sistemi con mkinitcpio (Arch)
# Editare /etc/mkinitcpio.conf → rimuovere HOOKS non necessari
mkinitcpio -P                            # Rigenerare

# Su sistemi con initramfs-tools (Debian/Ubuntu)
# MODULES=dep in /etc/initramfs-tools/initramfs.conf
# → include solo moduli necessari anziché tutti
update-initramfs -u
```

### Parametri Kernel per il Boot Veloce

```
# In /etc/default/grub, GRUB_CMDLINE_LINUX:
quiet                          # Riduce output console
loglevel=3                     # Solo errori
rd.systemd.show_status=auto    # Status solo su errore
systemd.show_status=auto       # Idem per userspace
```

### Servizi On-Demand con Socket Activation

Convertire i servizi a socket activation riduce il tempo di boot perché il servizio
non viene avviato finché non riceve una connessione. Questo è particolarmente efficace
per servizi usati raramente ma che devono essere disponibili.

```bash
# Identificare servizi candidati alla socket activation
# Buoni candidati: servizi con porta in ascolto e uso infrequente
systemctl list-sockets --all

# Disabilitare il servizio diretto e abilitare solo il socket
sudo systemctl disable myapp.service
sudo systemctl enable --now myapp.socket
# → Il servizio si avvia solo alla prima connessione
```

### Monitoraggio Continuo dei Tempi di Boot

```bash
# Script per tracciare i tempi di boot nel tempo
cat > /usr/local/bin/boot-tracker.sh << 'SCRIPT'
#!/bin/bash
DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TOTAL=$(systemd-analyze | grep -oP 'finished in \K[0-9.]+s')
USERSPACE=$(systemd-analyze | grep -oP '\+ \K[0-9.]+s \(userspace\)')
TOP_BLAME=$(systemd-analyze blame --no-pager | head -5)
echo "${DATE} Total: ${TOTAL}" >> /var/log/boot-times.log
SCRIPT
chmod +x /usr/local/bin/boot-tracker.sh

# Eseguire a ogni boot con un servizio oneshot
# /etc/systemd/system/boot-tracker.service
# [Service]
# Type=oneshot
# ExecStart=/usr/local/bin/boot-tracker.sh
# [Install]
# WantedBy=multi-user.target
```

### Ottimizzazioni Specifiche per VM e Container

Per ambienti virtualizzati il boot rapido è ancora più critico (auto-scaling,
cold start di funzioni serverless):

```bash
# VM: disabilitare hardware detection non necessario
sudo systemctl mask systemd-modules-load.service   # Se i moduli sono builtin
sudo systemctl mask lvm2-monitor.service            # Se non si usa LVM
sudo systemctl mask multipathd.service              # Se non si usa multipath

# Container: usare un target minimale
# systemd.unit=multi-user.target (no graphical)
# Disabilitare servizi hardware-dipendenti

# Verifica: cosa sta consumando il tempo di boot
systemd-analyze critical-chain --fuzz=50ms
# → Mostra solo i colli di bottiglia >50ms
```

---

## Cgroup v2 — Controllo Risorse Avanzato

La gerarchia cgroup v2 (unified hierarchy) è la base del resource control moderno in systemd.
A differenza di cgroup v1 (che aveva gerarchie separate per ogni controller), cgroup v2
utilizza una singola gerarchia unificata con controllo granulare.

### Verifica e Abilitazione di Cgroup v2

```bash
# Verificare la versione cgroup attiva
mount | grep cgroup
# cgroup2 on /sys/fs/cgroup type cgroup2 → v2 attivo
# Se mostra cgroup (non cgroup2) → v1 legacy

# Verificare i controller disponibili
cat /sys/fs/cgroup/cgroup.controllers
# cpu cpuset io memory pids rdma misc

# Verificare i controller attivi per un cgroup
cat /sys/fs/cgroup/system.slice/cgroup.subtree_control

# Forzare cgroup v2 al boot (se il sistema usa ancora v1)
# Aggiungere al kernel command line:
# systemd.unified_cgroup_hierarchy=1
```

### Controller Avanzati

#### CPU — Distribuzione e Limiti

```ini
[Service]
# Peso relativo (proporzionale ad altri servizi nello stesso slice)
CPUWeight=200                  # Default 100, range 1-10000
                               # Un servizio con weight 200 riceve il doppio
                               # di CPU rispetto a uno con weight 100 sotto carico

# Quota assoluta
CPUQuota=150%                  # Max 1.5 core
                               # 100% = 1 core, 200% = 2 core

# Affinità CPU
AllowedCPUs=0-3                # Solo core 0, 1, 2, 3
AllowedMemoryNodes=0           # Solo NUMA node 0

# Burst (v252+)
CPUQuotaPeriodSec=100ms        # Periodo di sampling (default 100ms)
```

#### Memoria — Limiti e Pressione

```ini
[Service]
# Limite hard — OOM kill se superato
MemoryMax=2G

# Limite soft — throttling e reclaim aggressivo
MemoryHigh=1536M               # Il kernel inizia a reclamare pagine sopra questo valore
                               # Il servizio rallenta ma non viene ucciso

# Limite minimo garantito
MemoryMin=256M                 # Questa memoria non viene reclamata neanche sotto pressione
MemoryLow=512M                 # Soft minimum — il kernel evita il reclaim sotto questo valore

# Swap
MemorySwapMax=512M             # Limite swap per il servizio
MemorySwapMax=0                # Disabilita swap per il servizio
MemoryZSwapMax=256M            # Limite zswap (v254+)

# Accounting
MemoryAccounting=yes           # Abilita il tracking della memoria (default: yes se configurato)
```

#### I/O — Banda e IOPS

```ini
[Service]
# Peso relativo
IOWeight=200                   # Default 100, range 1-10000

# Limiti assoluti per dispositivo
IOReadBandwidthMax=/dev/sda 100M     # Max 100 MB/s lettura
IOWriteBandwidthMax=/dev/sda 50M     # Max 50 MB/s scrittura
IOReadIOPSMax=/dev/sda 5000          # Max 5000 IOPS lettura
IOWriteIOPSMax=/dev/sda 2000         # Max 2000 IOPS scrittura

# Latenza (v252+)
IODeviceLatencyTargetSec=/dev/sda 25ms  # Target latenza I/O
```

#### Task e PID

```ini
[Service]
TasksMax=1024                  # Numero massimo di processi/thread
                               # Previene fork bomb e resource exhaustion
                               # Default: 4096 (configurabile in system.conf)
```

### Accounting e Monitoraggio in Tempo Reale

```bash
# Top per cgroup — monitoraggio interattivo
systemd-cgtop                            # CPU, Memoria, I/O per ogni cgroup
systemd-cgtop -d 1                       # Aggiornamento ogni secondo
systemd-cgtop -m                         # Ordina per memoria
systemd-cgtop -p                         # Ordina per path

# Query diretta dei contatori cgroup
cat /sys/fs/cgroup/system.slice/nginx.service/memory.current     # Memoria usata
cat /sys/fs/cgroup/system.slice/nginx.service/memory.peak        # Picco memoria
cat /sys/fs/cgroup/system.slice/nginx.service/memory.events      # Eventi OOM, high, max
cat /sys/fs/cgroup/system.slice/nginx.service/cpu.stat           # Statistiche CPU
cat /sys/fs/cgroup/system.slice/nginx.service/io.stat            # Statistiche I/O
cat /sys/fs/cgroup/system.slice/nginx.service/pids.current       # Numero processi

# Pressure Stall Information (PSI) — cgroup v2
cat /sys/fs/cgroup/system.slice/nginx.service/memory.pressure
# some avg10=0.00 avg60=0.00 avg300=0.00 total=0
# full avg10=0.00 avg60=0.00 avg300=0.00 total=0
# "some" = almeno un task è in stallo
# "full" = tutti i task sono in stallo

cat /sys/fs/cgroup/system.slice/nginx.service/cpu.pressure
cat /sys/fs/cgroup/system.slice/nginx.service/io.pressure

# Via systemctl
systemctl show nginx.service -p MemoryCurrent,MemoryPeak,CPUUsageNSec,TasksCurrent
```

### Impostazione Limiti a Runtime

```bash
# Impostare limiti senza modificare il file unit
# I cambiamenti sono persistenti (salvati in drop-in)
sudo systemctl set-property nginx.service MemoryMax=1G
sudo systemctl set-property nginx.service CPUQuota=200%
sudo systemctl set-property nginx.service TasksMax=512

# Impostare limiti temporanei (non persistenti — persi al reboot)
sudo systemctl set-property --runtime nginx.service MemoryMax=2G

# I limiti persistenti creano un drop-in in:
# /etc/systemd/system.control/nginx.service.d/50-MemoryMax.conf
```

---

## Gerarchia Slice — System, User, Machine

La gerarchia degli slice è la spina dorsale del resource control di systemd. Ogni processo
in esecuzione appartiene a uno slice, e gli slice formano una struttura ad albero che determina
la distribuzione delle risorse.

### Anatomia della Gerarchia

```
-.slice (root slice — cgroup radice)
│
├── init.scope                         ← PID 1 (systemd stesso)
│
├── system.slice                       ← Tutti i servizi di sistema
│   ├── nginx.service                  ← Servizio web
│   ├── postgresql.service             ← Database
│   ├── sshd.service                   ← SSH
│   └── webapps.slice                  ← Slice personalizzato per webapp
│       ├── webapp-api.service         ← API backend
│       └── webapp-worker.service      ← Worker background
│
├── user.slice                         ← Tutte le sessioni utente
│   ├── user-1000.slice                ← Utente UID 1000
│   │   ├── session-1.scope            ← Sessione TTY/SSH
│   │   ├── user@1000.service          ← Istanza systemd --user
│   │   └── app.slice                  ← Slice utente personalizzato
│   │       └── myeditor.service       ← Servizio utente
│   └── user-1001.slice                ← Utente UID 1001
│
└── machine.slice                      ← Container e VM
    ├── machine-web1.scope             ← Container nspawn
    └── libvirt-qemu.slice             ← VM libvirt
```

### Configurazione degli Slice di Sistema

```ini
# /etc/systemd/system/system.slice.d/limits.conf
# Limiti globali per tutti i servizi di sistema
[Slice]
MemoryMax=80%                  # Max 80% della RAM per i servizi
CPUWeight=500                  # Peso CPU relativo alto (sistema > utenti)
```

```ini
# /etc/systemd/system/user.slice.d/limits.conf
# Limiti globali per tutti gli utenti
[Slice]
MemoryMax=30%                  # Max 30% della RAM per gli utenti
CPUWeight=100                  # Peso CPU relativo basso
TasksMax=4096                  # Max task per tutti gli utenti combinati
```

### Slice Personalizzati per Isolamento Applicativo

```ini
# /etc/systemd/system/database.slice
[Unit]
Description=Database Services Slice

[Slice]
MemoryMax=8G
MemoryHigh=6G
CPUWeight=300
IOWeight=500
TasksMax=2048
```

```ini
# /etc/systemd/system/batch.slice
[Unit]
Description=Batch Jobs Slice (bassa priorità)

[Slice]
MemoryMax=4G
CPUWeight=50                   # Bassa priorità CPU
IOWeight=50                    # Bassa priorità I/O
```

```ini
# Assegnare servizi ai rispettivi slice
# postgresql.service drop-in:
[Service]
Slice=database.slice

# backup.service drop-in:
[Service]
Slice=batch.slice
```

### Gestione Risorse Utente con loginctl

```bash
# Vedere le sessioni attive e i loro slice
loginctl list-sessions
loginctl session-status <SESSION-ID>

# Impostare limiti per utente
sudo systemctl set-property user-1000.slice MemoryMax=4G
sudo systemctl set-property user-1000.slice CPUQuota=200%

# Abilitare il lingering (servizi utente attivi anche senza login)
loginctl enable-linger username
loginctl disable-linger username

# Verificare le risorse per slice
systemctl status system.slice
systemctl status user.slice
systemctl status machine.slice
```

---

## Systemd-timesyncd

`systemd-timesyncd` è un client SNTP (Simple Network Time Protocol) integrato in systemd,
progettato per la sincronizzazione dell'orologio di sistema su macchine client. È un'alternativa
leggera a chrony e ntpd, adatta alla maggior parte degli scenari dove non è richiesta
precisione sub-millisecondo o funzionalità NTP server.

### Configurazione

```ini
# /etc/systemd/timesyncd.conf
[Time]
NTP=0.pool.ntp.org 1.pool.ntp.org 2.pool.ntp.org 3.pool.ntp.org
FallbackNTP=ntp.ubuntu.com time.google.com
RootDistanceMaxSec=5           # Massima distanza dalla sorgente root
PollIntervalMinSec=32          # Intervallo minimo di polling (secondi)
PollIntervalMaxSec=2048        # Intervallo massimo di polling
ConnectionRetrySec=30          # Ritardo tra tentativi di connessione
SaveIntervalSec=60             # Frequenza di salvataggio dell'offset su disco
```

### Gestione e Diagnostica

```bash
# Abilitare e avviare
sudo systemctl enable --now systemd-timesyncd

# Stato della sincronizzazione
timedatectl status
# Output:
#        Local time: Sat 2025-05-24 14:30:00 CEST
#    Universal time: Sat 2025-05-24 12:30:00 UTC
#          RTC time: Sat 2025-05-24 12:30:00
#         Time zone: Europe/Rome (CEST, +0200)
# System clock synchronized: yes
#               NTP service: active
#           RTC in local TZ: no

timedatectl show-timesync        # Dettagli sincronizzazione
timedatectl timesync-status      # Stato del server NTP corrente

# Gestione timezone
timedatectl list-timezones       # Lista timezone disponibili
sudo timedatectl set-timezone Europe/Rome
sudo timedatectl set-ntp true    # Abilita NTP (avvia timesyncd)

# Verificare i log
journalctl -u systemd-timesyncd --since "1 hour ago"
```

### Confronto con Chrony e NTPd

| Caratteristica | systemd-timesyncd | chrony | ntpd |
|---|---|---|---|
| Protocollo | SNTP (semplificato) | NTP completo | NTP completo |
| Modalità server | No | Sì | Sì |
| Sorgenti multiple | No (una alla volta) | Sì | Sì |
| Precisione tipica | 10-100 ms | < 1 ms | < 1 ms |
| Uso memoria | ~1 MB | ~2-3 MB | ~5 MB |
| Caso d'uso | Desktop, VM, container | Server, infrastruttura | Legacy |
| Compensazione frequenza | Basilare | Avanzata | Avanzata |
| Hardware timestamping | No | Sì | Sì |

**Quando usare timesyncd**: workstation, laptop, VM, container, qualsiasi macchina client
che non deve servire il tempo ad altri. **Quando usare chrony**: server di produzione,
ambienti dove la precisione del tempo è critica (database distribuiti, log forensi,
transazioni finanziarie), server NTP interni.

---

## Systemd-oomd — OOM Killer Proattivo

`systemd-oomd` è un demone userspace per la gestione proattiva delle situazioni di
esaurimento memoria (Out-Of-Memory). A differenza del kernel OOM killer (che interviene
quando è già troppo tardi e il sistema è completamente bloccato), systemd-oomd monitora
la Pressure Stall Information (PSI) e lo swap per intervenire prima del collasso.

### Requisiti

- Cgroup v2 (unified hierarchy) — obbligatorio
- Memory accounting abilitato per tutte le unit
- Swap abilitato (altamente raccomandato per un funzionamento ottimale)
- Kernel con supporto PSI (Linux 4.20+)

### Configurazione

```ini
# /etc/systemd/oomd.conf
[OOM]
SwapUsedLimit=90%              # Intervieni quando lo swap usato supera il 90%
DefaultMemoryPressureDurationSec=20s  # Durata della pressione prima di agire
                                      # (default: 20s per la maggior parte delle distribuzioni)
```

### Attivazione per Servizio

Le direttive `ManagedOOM*` si aggiungono alla sezione `[Service]` o `[Slice]`:

```ini
[Service]
# === GESTIONE SWAP ===
ManagedOOMSwap=kill            # Quando lo swap globale supera SwapUsedLimit,
                               # questo cgroup è candidato alla terminazione
                               # Valori: auto, kill

# === GESTIONE PRESSIONE MEMORIA ===
ManagedOOMMemoryPressure=kill  # Quando la pressione memoria di questo cgroup
                               # supera la soglia, termina i processi nel cgroup
                               # Valori: auto, kill

ManagedOOMMemoryPressureLimit=60%  # Soglia di pressione memoria per questo cgroup
                                   # (sovrascrive il default, tipicamente 60%)

# === PREFERENZA DI KILL ===
ManagedOOMPreference=avoid     # Evita di terminare questo cgroup se possibile
                               # Valori: avoid, none
                               # Usare "avoid" per servizi critici
```

### Esempio Pratico: Protezione Server Web

```ini
# /etc/systemd/system/nginx.service.d/oom.conf
[Service]
ManagedOOMSwap=kill
ManagedOOMMemoryPressure=kill
ManagedOOMPreference=avoid             # Non uccidere nginx se possibile

# /etc/systemd/system/batch-worker.service.d/oom.conf
[Service]
ManagedOOMSwap=kill
ManagedOOMMemoryPressure=kill
ManagedOOMPreference=none              # Può essere terminato per proteggere il sistema
ManagedOOMMemoryPressureLimit=40%      # Soglia più aggressiva
```

### Monitoraggio

```bash
# Stato di systemd-oomd
systemctl status systemd-oomd

# Log degli interventi OOM
journalctl -u systemd-oomd --since "1 day ago"

# Verificare la configurazione per un servizio
systemctl show myapp.service -p ManagedOOMSwap,ManagedOOMMemoryPressure,ManagedOOMPreference

# Monitorare la pressione in tempo reale
watch -n 1 cat /proc/pressure/memory
watch -n 1 cat /sys/fs/cgroup/system.slice/myapp.service/memory.pressure

# oomctl — strumento di diagnostica (v254+)
oomctl                                 # Mostra lo stato e i cgroup monitorati
```

### Differenze tra systemd-oomd e Kernel OOM Killer

| Aspetto | systemd-oomd | Kernel OOM Killer |
|---|---|---|
| Intervento | Proattivo (prima del collasso) | Reattivo (sistema già bloccato) |
| Granularità | Per cgroup/servizio | Per processo singolo |
| Criterio | PSI (pressione) + swap | Heuristiche `oom_score` |
| Configurabilità | `ManagedOOM*`, `oomd.conf` | `/proc/<pid>/oom_score_adj` |
| Log | journald strutturato | dmesg/kernel log |
| Richiede | cgroup v2, PSI | Nessun requisito speciale |

---

## Systemd Credentials — Gestione Segreti

Il sistema di credentials di systemd permette di passare segreti (chiavi, password, certificati,
token) ai servizi in modo sicuro, senza esporli nel file unit, nelle variabili d'ambiente
in chiaro, o nel filesystem accessibile a tutti. Le credenziali sono disponibili al servizio
in una directory temporanea montata in sola lettura, inaccessibile dopo la terminazione.

### Tipi di Credential

```ini
[Service]
# === CREDENTIAL DA FILE ===
LoadCredential=db-password:/etc/credstore/myapp-db-pass
# Il servizio riceve il file in $CREDENTIALS_DIRECTORY/db-password
# Il percorso sorgente deve essere leggibile dall'utente root

# === CREDENTIAL ENCRYPTED DA FILE ===
LoadCredentialEncrypted=api-key:/etc/credstore.encrypted/myapp-api-key
# Come LoadCredential, ma il file sorgente è cifrato
# systemd lo decifra prima di passarlo al servizio

# === CREDENTIAL INLINE (non cifrata) ===
SetCredential=app-mode:production
# Imposta un valore letterale — ATTENZIONE: visibile nel file unit
# Usare solo per valori non sensibili

# === CREDENTIAL INLINE CIFRATA ===
SetCredentialEncrypted=secret-token:<CIPHERTEXT_BASE64>
# Il valore è cifrato nel file unit — sicuro anche se il file è leggibile

# === IMPORT DA CREDENTIAL STORE ===
ImportCredential=myapp-*
# Importa tutte le credenziali che matchano il pattern
# Cerca in /etc/credstore/, /run/credstore/, /usr/lib/credstore/
# e nelle varianti .encrypted
```

### systemd-creds — Strumento di Gestione

```bash
# Cifrare un segreto (legato alla macchina + TPM se disponibile)
echo -n 'S3cretP@ssw0rd' | sudo systemd-creds encrypt - /etc/credstore.encrypted/myapp-db-pass
# → Il file cifrato può essere distribuito solo sulla stessa macchina

# Cifrare con scope specifico (servizio)
echo -n 'MyApiKey123' | sudo systemd-creds encrypt \
  --name=api-key \
  --not-after=2025-12-31 \
  - /etc/credstore.encrypted/myapp-api-key

# Decifrare per verifica
sudo systemd-creds decrypt /etc/credstore.encrypted/myapp-db-pass -
# Output: S3cretP@ssw0rd

# Generare un valore cifrato inline per SetCredentialEncrypted
echo -n 'MySecret' | sudo systemd-creds encrypt --pretty -p - -
# Output: testo base64 da incollare direttamente nel file unit

# Elencare credenziali disponibili
systemd-creds list

# Verificare le credenziali di un servizio
systemd-creds --system cat myapp-db-pass
```

### Esempio Completo: Servizio con Credenziali

```ini
# /etc/systemd/system/webapp.service
[Unit]
Description=Web Application con Credenziali Sicure
After=network.target

[Service]
Type=exec
User=webapp
ExecStart=/opt/webapp/bin/server

# Le credenziali sono disponibili in $CREDENTIALS_DIRECTORY/
# Il servizio legge $CREDENTIALS_DIRECTORY/db-password per la password del DB
LoadCredentialEncrypted=db-password:/etc/credstore.encrypted/webapp-db-pass
LoadCredentialEncrypted=api-key:/etc/credstore.encrypted/webapp-api-key
SetCredential=app-env:production
ImportCredential=webapp-*

# Il processo accede a:
# $CREDENTIALS_DIRECTORY/db-password  → password in chiaro (decifrata da systemd)
# $CREDENTIALS_DIRECTORY/api-key      → chiave API in chiaro
# $CREDENTIALS_DIRECTORY/app-env      → "production"

# Hardening
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
```

```bash
# Il servizio accede alle credenziali tramite:
# 1. Variabile d'ambiente $CREDENTIALS_DIRECTORY (path alla directory)
# 2. sd_bus_get_property() via API D-Bus
# 3. File in /run/credentials/webapp.service/ (gestito da systemd)
```

### Credential vs EnvironmentFile vs Environment

| Metodo | Sicurezza | Visibilità | Cifratura |
|---|---|---|---|
| `SetCredential=` | Media | Visibile nel file unit | No |
| `SetCredentialEncrypted=` | Alta | Cifrato nel file unit | Sì (TPM/macchina) |
| `LoadCredential=` | Media | File esterno | No |
| `LoadCredentialEncrypted=` | Alta | File esterno cifrato | Sì |
| `EnvironmentFile=` | Bassa | File in chiaro su disco | No |
| `Environment=` | Bassa | Visibile nel file unit + /proc | No |

---

## Journal Remote e Gateway — Logging Centralizzato

Systemd offre strumenti nativi per la centralizzazione dei log senza dipendere da stack
esterni. Il modello si basa su tre componenti: `systemd-journal-upload` (client push),
`systemd-journal-remote` (server ricevente) e `systemd-journal-gatewayd` (API REST per query).

### Architettura Push (Raccomandata)

```
┌─────────────┐     HTTPS      ┌──────────────────┐
│  Server A   │ ──────────────→│  Log Collector    │
│  (upload)   │                │  (journal-remote) │
└─────────────┘                │                   │
┌─────────────┐     HTTPS      │  /var/log/journal │
│  Server B   │ ──────────────→│  /remote/         │
│  (upload)   │                │                   │
└─────────────┘                └──────────────────┘
┌─────────────┐     HTTPS      ┌──────────────────┐
│  Server C   │ ──────────────→│  Gateway (API)    │
│  (upload)   │                │  :19531           │
└─────────────┘                └──────────────────┘
```

### Configurazione Server (Ricevente)

```ini
# /etc/systemd/journal-remote.conf
[Remote]
# ServerKeyFile=/etc/ssl/private/journal-remote.key
# ServerCertificateFile=/etc/ssl/certs/journal-remote.crt
# TrustedCertificateFile=/etc/ssl/ca/journal-ca.crt
Seal=false                     # Seal crittografico (richiede certificati)
SplitMode=host                 # Un file journal per host sorgente
                               # Valori: host, none (tutto in un file)
```

```bash
# Installare e abilitare sul server collector
sudo apt install systemd-journal-remote   # Debian/Ubuntu
sudo dnf install systemd-journal-remote   # RHEL/Fedora

# Abilitare il ricevitore
sudo systemctl enable --now systemd-journal-remote.socket

# I log remoti vengono salvati in:
# /var/log/journal/remote/remote-<hostname>.journal
```

### Configurazione Client (Inviante)

```ini
# /etc/systemd/journal-upload.conf
[Upload]
URL=https://logserver.example.com:19532
# ServerKeyFile=/etc/ssl/private/client.key
# ServerCertificateFile=/etc/ssl/certs/client.crt
# TrustedCertificateFile=/etc/ssl/ca/journal-ca.crt
```

```bash
# Abilitare l'upload sul client
sudo systemctl enable --now systemd-journal-upload
```

### Journal Gateway — API REST

```bash
# Abilitare il gateway (espone API REST sulla porta 19531)
sudo systemctl enable --now systemd-journal-gatewayd.socket

# Query via HTTP
curl -H "Accept: application/json" http://localhost:19531/entries
curl http://localhost:19531/entries?boot=0&PRIORITY=3   # Solo errori del boot corrente
curl http://localhost:19531/entries?_SYSTEMD_UNIT=nginx.service

# Formati supportati:
# Accept: text/plain                → formato testuale
# Accept: application/json          → JSON (un oggetto per entry)
# Accept: application/vnd.fdo.journal  → formato journal nativo
# Accept: text/event-stream         → Server-Sent Events (streaming)

# Output campi disponibili
curl http://localhost:19531/fields/PRIORITY
curl http://localhost:19531/fields/_SYSTEMD_UNIT
curl http://localhost:19531/machine-id
curl http://localhost:19531/boot-id

# Streaming in tempo reale (SSE)
curl -N -H "Accept: text/event-stream" http://localhost:19531/entries?follow
```

### Query dei Log Remoti con journalctl

```bash
# Leggere i log remoti direttamente dal server collector
journalctl --directory=/var/log/journal/remote/
journalctl --file=/var/log/journal/remote/remote-webserver.journal

# Filtrare per host e servizio
journalctl --directory=/var/log/journal/remote/ \
  _HOSTNAME=webserver -u nginx.service --since "2 hours ago"

# Combinare log locali e remoti
journalctl --directory=/var/log/journal/ --directory=/var/log/journal/remote/
```

### Sicurezza del Journal Remote

```bash
# Generare certificati per TLS mutua autenticazione
# (raccomandato per ambienti di produzione)

# Generare CA
openssl req -x509 -newkey rsa:4096 -days 3650 \
  -keyout /etc/ssl/ca/journal-ca.key \
  -out /etc/ssl/ca/journal-ca.crt \
  -subj "/CN=Journal CA"

# Generare certificato server
openssl req -newkey rsa:2048 \
  -keyout /etc/ssl/private/journal-remote.key \
  -out /etc/ssl/certs/journal-remote.csr \
  -subj "/CN=logserver.example.com"

openssl x509 -req -in /etc/ssl/certs/journal-remote.csr \
  -CA /etc/ssl/ca/journal-ca.crt \
  -CAkey /etc/ssl/ca/journal-ca.key \
  -out /etc/ssl/certs/journal-remote.crt \
  -days 365

# Verificare la comunicazione cifrata
journalctl -u systemd-journal-remote --since "10 min ago"
```

### Sealing Crittografico del Journal

```bash
# Il sealing Forward Secure Sealing (FSS) protegge i log da manomissione
# retroattiva: anche se un attaccante ottiene accesso alla chiave corrente,
# non può alterare i log passati

# Configurare il sealing
journalctl --setup-keys
# Output: chiave di verifica da conservare offline

# Verificare l'integrità
journalctl --verify
# → PASS se tutti i log sono integri
# → FAIL se rileva manomissione

# Abilitare il sealing in journald.conf
# [Journal]
# Seal=yes
# SplitMode=uid   (un file per utente per il sealing)
```

---

## Systemd-sysext — Estensioni di Sistema

`systemd-sysext` permette di estendere a runtime le directory `/usr/` e `/opt/` con file
aggiuntivi, senza modificare il filesystem di base. È particolarmente utile su sistemi
immutabili (Flatcar, CoreOS, SteamOS) dove il filesystem radice è read-only.

### Concetto

Le estensioni si presentano come immagini disco (`.raw`) o directory che vengono
"sovrapposte" (overlay) su `/usr/` e `/opt/`. Quando un'estensione viene attivata (merge),
i suoi file appaiono nel filesystem come se facessero parte dell'OS. Quando viene
disattivata (unmerge), i file scompaiono senza lasciare traccia.

### Directory di Ricerca

```
/etc/extensions/              # Estensioni admin (priorità massima)
/run/extensions/              # Estensioni runtime
/var/lib/extensions/          # Estensioni installate (persistenti)
```

### Creazione di un'Estensione

```bash
# Creare un'estensione con tool aggiuntivi
mkdir -p /var/lib/extensions/monitoring/usr/bin
mkdir -p /var/lib/extensions/monitoring/usr/lib/extension-release.d

# Copiare i binari nell'estensione
cp /path/to/custom-exporter /var/lib/extensions/monitoring/usr/bin/

# Creare il file di release (OBBLIGATORIO)
# Deve corrispondere al sistema operativo host
source /etc/os-release
cat > /var/lib/extensions/monitoring/usr/lib/extension-release.d/extension-release.monitoring <<EOF
ID=${ID}
VERSION_ID=${VERSION_ID}
EOF

# Attivare l'estensione
sudo systemd-sysext merge

# Verificare
which custom-exporter   # → /usr/bin/custom-exporter
systemd-sysext status   # Lista estensioni attive

# Disattivare
sudo systemd-sysext unmerge
```

### Estensione come Immagine Disco

```bash
# Creare un'immagine raw per l'estensione
mkdir -p /tmp/sysext-build/usr/bin
mkdir -p /tmp/sysext-build/usr/lib/extension-release.d

cp /path/to/tool /tmp/sysext-build/usr/bin/

source /etc/os-release
echo "ID=${ID}" > /tmp/sysext-build/usr/lib/extension-release.d/extension-release.tools
echo "VERSION_ID=${VERSION_ID}" >> /tmp/sysext-build/usr/lib/extension-release.d/extension-release.tools

# Creare l'immagine (con mksquashfs per compressione)
mksquashfs /tmp/sysext-build /var/lib/extensions/tools.raw

# Oppure con mkfs.erofs (più moderno, supportato da v252+)
mkfs.erofs /var/lib/extensions/tools.raw /tmp/sysext-build

# Attivare
sudo systemd-sysext merge
```

### Gestione con systemd-sysext

```bash
# Stato delle estensioni
systemd-sysext status

# Merge (attivazione) di tutte le estensioni trovate
sudo systemd-sysext merge

# Unmerge (disattivazione) di tutte le estensioni
sudo systemd-sysext unmerge

# Refresh (unmerge + merge — ricarica dopo aggiornamenti)
sudo systemd-sysext refresh

# Elencare le estensioni disponibili
systemd-sysext list

# Attivazione automatica al boot via servizio
sudo systemctl enable systemd-sysext
```

### confext — Estensioni di Configurazione

A partire da systemd v254, esiste anche `systemd-confext` che opera sullo stesso principio
di sysext ma per la directory `/etc/` anziché `/usr/`. Questo permette di sovrapporre
file di configurazione senza modificare il filesystem di base.

```bash
# Le confext si collocano in:
# /run/confexts/
# /var/lib/confexts/
# /etc/confexts/

# Attivare confext
sudo systemd-confext merge

# Stato
systemd-confext status

# Disattivare
sudo systemd-confext unmerge
```

### Casi d'Uso

- **Sistemi immutabili**: aggiungere strumenti di debug/monitoring senza modificare l'OS
- **Container host**: estendere Flatcar/CoreOS con tool di gestione
- **Ambienti CI/CD**: iniettare tool di build senza installazione permanente
- **Rollback**: disattivare un'estensione problematica in un comando (`sysext unmerge`)
- **A/B testing di configurazione**: con confext, testare configurazioni alternative senza toccare `/etc/` originale
- **Edge computing e IoT**: distribuire aggiornamenti incrementali come immagini sysext senza sostituire l'intero OS

---

## Systemd-homed

`systemd-homed` è un servizio che gestisce le home directory degli utenti come unità
auto-contenute e opzionalmente cifrate. L'obiettivo è rendere le home directory portatili,
sicure e indipendenti dal sistema host.

### Meccanismi di Storage

| Storage | Descrizione | Portabilità |
|---|---|---|
| `luks` | Filesystem in volume LUKS2 (cifrato) | Alta — file `.home` spostabile |
| `fscrypt` | Cifratura a livello filesystem (ext4/f2fs) | Media |
| `cifs` | Home su share di rete (SMB/CIFS) | Server-dipendente |
| `subvolume` | Subvolume Btrfs (non cifrato) | Bassa |
| `directory` | Directory classica (non cifrata) | Bassa |

### Creazione e Gestione Utenti con homectl

```bash
# Creare un utente con home cifrata LUKS
sudo homectl create alice \
  --storage=luks \
  --disk-size=10G \
  --fs-type=ext4 \
  --enforce-password-policy=yes \
  --password-hint="Animale domestico di infanzia"

# Creare un utente con fscrypt
sudo homectl create bob \
  --storage=fscrypt

# Creare un utente su directory classica
sudo homectl create carol \
  --storage=directory

# Elencare gli utenti gestiti da homed
homectl list

# Ispezionare un utente
homectl inspect alice
homectl inspect alice --json=pretty    # Output JSON dettagliato

# Modificare proprietà
sudo homectl update alice \
  --disk-size=20G \
  --real-name="Alice Rossi" \
  --shell=/bin/zsh \
  --member-of=developers,docker

# Cambiare password
sudo homectl passwd alice

# Attivare/disattivare la home (normalmente automatico al login)
sudo homectl activate alice
sudo homectl deactivate alice

# Ridimensionare
sudo homectl resize alice 30G

# Bloccare/sbloccare (utile per screensaver)
homectl lock alice
homectl unlock alice

# Rimuovere un utente
sudo homectl remove alice
```

### Configurazione del Record Utente

I metadati dell'utente sono salvati in un record JSON dentro il volume LUKS o nella directory
home, rendendo l'utente auto-descrittivo e portatile.

```bash
# Il record contiene:
# - Username, UID, GID, GECOS, shell
# - Parametri LUKS (cifratura, filesystem)
# - Limiti risorse (quota disco, max sessioni)
# - Policy password (scadenza, complessità)
# - Appartenenza a gruppi
# - Stato dell'account

# Esportare il record utente
homectl inspect alice --json=pretty > /tmp/alice-record.json

# Importare un utente su un'altra macchina (con il file .home)
sudo homectl create --identity=/tmp/alice-record.json
# + copiare il file .home nella directory di storage
```

### Sicurezza di systemd-homed

- La home directory viene montata solo durante il login (cifrata a riposo)
- La password utente è anche la passphrase LUKS (no password separata)
- Il volume LUKS supporta hardware token FIDO2 e PKCS#11
- Le credenziali sono legate al volume, non al sistema host
- La rimozione dell'utente cancella crittograficamente i dati

```bash
# Abilitare autenticazione FIDO2
sudo homectl update alice --fido2-device=auto

# Abilitare autenticazione con PKCS#11 (smartcard)
sudo homectl update alice --pkcs11-token-uri=auto

# Verificare stato di sicurezza
sudo homectl inspect alice | grep -E 'Storage|Encryption|FIDO2'
```

### Portabilità delle Home LUKS

Uno dei vantaggi principali di systemd-homed con storage LUKS è la portabilità.
La home directory è contenuta in un singolo file `.home` che può essere spostato
tra macchine diverse.

```bash
# Il file .home contiene tutto: filesystem, dati utente, metadati
ls -lh /home/alice.home
# → alice.home  10G  (volume LUKS2 con ext4 o btrfs all'interno)

# Spostare su un'altra macchina
scp /home/alice.home newhost:/home/

# Sulla nuova macchina, importare l'utente
sudo homectl activate --identity=/path/to/alice-record.json alice

# Con v258+, il comando adopt semplifica l'importazione
sudo homectl adopt /home/alice.home

# La password dell'utente è la passphrase LUKS
# → nessuna configurazione aggiuntiva necessaria sulla nuova macchina
```

### Limitazioni e Considerazioni

- systemd-homed non è compatibile con NFS o altri filesystem di rete per lo storage LUKS
- Il login su TTY e SSH funziona, ma richiede che PAM sia configurato per systemd-homed
- La cifratura aggiunge un overhead I/O misurabile su dispositivi lenti (HDD, USB 2.0)
- I servizi che devono accedere alla home di un utente non possono farlo prima del login
- La migrazione da `/etc/passwd` tradizionale richiede la ricreazione dell'utente con homectl

---

## Systemd-boot

`systemd-boot` (precedentemente gummiboot) è un boot loader UEFI leggero che supporta
solo sistemi UEFI con ESP (EFI System Partition). È un'alternativa minimale a GRUB2,
progettata per semplicità e velocità.

### Installazione e Configurazione

```bash
# Installare systemd-boot nella ESP
sudo bootctl install

# La ESP è tipicamente montata su /boot o /efi
# bootctl crea:
#   /boot/EFI/systemd/systemd-bootx64.efi    → Il boot loader
#   /boot/EFI/BOOT/BOOTX64.EFI               → Fallback entry
#   /boot/loader/loader.conf                  → Configurazione
#   /boot/loader/entries/                      → Boot entry

# Aggiornare
sudo bootctl update
```

### Configurazione del Loader

```ini
# /boot/loader/loader.conf
default @saved                # Ricorda l'ultima scelta
timeout 3                     # Secondi di attesa (0 = no menu)
console-mode auto             # Risoluzione console
editor no                     # Disabilita l'editor della command line (sicurezza!)
auto-entries yes              # Rileva automaticamente altri OS
auto-firmware yes             # Mostra opzione per firmware setup
beep no                       # Nessun beep
```

### Entry di Boot

```ini
# /boot/loader/entries/arch.conf
title   Arch Linux
linux   /vmlinuz-linux
initrd  /initramfs-linux.img
options root=PARTUUID=xxxx-yyyy rw quiet loglevel=3

# /boot/loader/entries/arch-fallback.conf
title   Arch Linux (Fallback)
linux   /vmlinuz-linux
initrd  /initramfs-linux-fallback.img
options root=PARTUUID=xxxx-yyyy rw
```

### Gestione con bootctl

```bash
# Stato del boot loader
bootctl status

# Lista delle entry
bootctl list

# Impostare la entry di default
bootctl set-default arch.conf

# Impostare la entry per il prossimo boot (una tantum)
bootctl set-oneshot arch-fallback.conf

# Aggiornare il boot loader
sudo bootctl update

# Rimuovere il boot loader
sudo bootctl remove

# Verifica integrità
bootctl is-installed
```

### Vantaggi rispetto a GRUB2

| Caratteristica | systemd-boot | GRUB2 |
|---|---|---|
| Supporto BIOS | No | Sì |
| Complessità | Minimale | Complessa |
| Configurazione | File INI semplici | Script + grub-mkconfig |
| Tempo di boot | Più veloce | Più lento |
| Secure Boot | Nativo | Richiede configurazione |
| Auto-discovery | Sì (Boot Loader Specification) | Limitato |

---

## Systemd-nspawn — Container Leggeri

`systemd-nspawn` è uno strumento per avviare container leggeri basati su namespace e cgroup.
È concepito come un `chroot` moderno con isolamento completo: filesystem, rete, PID, IPC,
utenti. È ideale per test, build e sviluppo.

### Creazione di un Container

```bash
# Da un'immagine debootstrap (Debian/Ubuntu)
sudo debootstrap stable /var/lib/machines/debian-test http://deb.debian.org/debian

# Da un'immagine dnf (Fedora/RHEL)
sudo dnf --releasever=40 --installroot=/var/lib/machines/fedora-test install -y systemd passwd dnf

# Da pacstrap (Arch)
sudo pacstrap -c /var/lib/machines/arch-test base

# Avviare il container
sudo systemd-nspawn -D /var/lib/machines/debian-test
# → Shell root nel container

# Avviare con boot completo (init dentro il container)
sudo systemd-nspawn -bD /var/lib/machines/debian-test
```

### Gestione con machinectl

```bash
# Elencare container
machinectl list
machinectl list-images

# Avviare/fermare
sudo machinectl start debian-test
sudo machinectl poweroff debian-test
sudo machinectl terminate debian-test   # Forza terminazione

# Login
sudo machinectl login debian-test
sudo machinectl shell debian-test       # Shell diretta (senza login)
sudo machinectl shell debian-test /bin/bash

# Copia file
sudo machinectl copy-to debian-test /local/file /container/path
sudo machinectl copy-from debian-test /container/file /local/path

# Gestione immagini
sudo machinectl clone debian-test debian-prod
sudo machinectl rename debian-test debian-staging
sudo machinectl remove debian-old

# Scaricare immagini
sudo machinectl pull-tar https://example.com/image.tar.xz myimage
sudo machinectl pull-raw https://example.com/image.raw.xz myimage
```

### Opzioni di Rete

```bash
# Rete host (condivisa — default)
sudo systemd-nspawn -bD /var/lib/machines/test

# Virtual Ethernet (veth pair — isolato)
sudo systemd-nspawn -bD /var/lib/machines/test --network-veth
# → Crea veth: ve-test (host) ↔ host0 (container)

# Bridge
sudo systemd-nspawn -bD /var/lib/machines/test --network-bridge=br0

# Nessuna rete
sudo systemd-nspawn -bD /var/lib/machines/test --private-network

# Port forwarding
sudo systemd-nspawn -bD /var/lib/machines/test \
  --network-veth \
  --port=tcp:8080:80           # Host:8080 → Container:80
```

### Limiti di Risorse

```bash
# CPU e memoria
sudo systemd-nspawn -bD /var/lib/machines/test \
  --property=CPUQuota=200% \
  --property=MemoryMax=2G \
  --property=TasksMax=512

# Oppure tramite file .nspawn
# /etc/systemd/nspawn/test.nspawn
```

```ini
# /etc/systemd/nspawn/test.nspawn
[Exec]
Boot=yes
PrivateUsers=pick                      # User namespace con UID mapping automatico
Capability=CAP_NET_ADMIN               # Capability aggiuntive

[Files]
Bind=/data/shared:/mnt/shared          # Bind mount dal host
BindReadOnly=/etc/resolv.conf          # DNS dal host

[Network]
VirtualEthernet=yes
Bridge=br0
Port=tcp:8080:80
```

---

## Portable Services

I Portable Services sono un concetto intermedio tra container e servizi tradizionali.
Un portable service è un'immagine (directory o file `.raw`) che contiene un albero OS
completo con i propri binari, librerie e file unit. systemd "attacca" l'immagine al
sistema host e i servizi vengono gestiti come normali unit systemd, ma eseguiti con
l'isolamento sandbox.

### Differenze Concettuali

| Aspetto | Servizio tradizionale | Portable Service | Container (nspawn) |
|---|---|---|---|
| Filesystem | Condiviso con host | Immagine propria + sandbox | Isolato completamente |
| Init system | systemd dell'host | systemd dell'host | systemd proprio nel container |
| Integrazione | Completa | Gestito come unit normale | machinectl / shell separata |
| Isolamento | Direttive hardening | Sandbox + profilo | Namespace completo |
| Portabilità | Dipende dai pacchetti host | Immagine auto-contenuta | Immagine auto-contenuta |

### Gestione con portablectl

```bash
# Elencare le immagini disponibili
portablectl list

# Ispezionare un'immagine
portablectl inspect /path/to/image.raw

# Attaccare un portable service
sudo portablectl attach /path/to/myservice.raw
# → Copia le unit file dall'immagine al sistema host
# → Crea i mount necessari per l'immagine

# Attaccare con profilo di sicurezza
sudo portablectl attach --profile=strict /path/to/myservice.raw
# Profili disponibili: default, nonetwork, strict, trusted

# Distaccare
sudo portablectl detach myservice

# Dopo l'attach, gestire come un servizio normale
sudo systemctl enable --now myservice.service
systemctl status myservice.service

# Ricaricare un'immagine aggiornata
sudo portablectl reattach /path/to/myservice-v2.raw
# → Zero-downtime: il vecchio servizio viene fermato e il nuovo avviato
```

### Profili di Sicurezza

| Profilo | Descrizione |
|---|---|
| `default` | Sandbox base (ProtectSystem, PrivateTmp) |
| `nonetwork` | Default + PrivateNetwork (nessun accesso rete) |
| `strict` | Hardening completo (NoNewPrivileges, ProtectKernel*, etc.) |
| `trusted` | Nessun sandbox — esecuzione con privilegi completi |

I profili sono file `.conf` in `/usr/lib/systemd/portable/profile/` che contengono
direttive drop-in applicate automaticamente al servizio durante l'attach.

### Creazione di un Portable Service

```bash
# 1. Preparare il filesystem dell'immagine
mkdir -p /tmp/myservice-portable/{usr/lib/systemd/system,usr/bin,usr/lib/extension-release.d}

# 2. Copiare il binario
cp /path/to/myapp /tmp/myservice-portable/usr/bin/

# 3. Creare il file unit
cat > /tmp/myservice-portable/usr/lib/systemd/system/myservice.service <<'EOF'
[Unit]
Description=My Portable Service

[Service]
Type=exec
ExecStart=/usr/bin/myapp
DynamicUser=yes

[Install]
WantedBy=multi-user.target
EOF

# 4. Creare il file di release (OBBLIGATORIO)
source /etc/os-release
echo "ID=${ID}" > /tmp/myservice-portable/usr/lib/extension-release.d/extension-release.myservice
echo "VERSION_ID=${VERSION_ID}" >> /tmp/myservice-portable/usr/lib/extension-release.d/extension-release.myservice

# 5. Creare l'immagine raw (opzionale, può anche essere directory)
mksquashfs /tmp/myservice-portable /var/lib/portables/myservice.raw

# 6. Attaccare e avviare
sudo portablectl attach /var/lib/portables/myservice.raw
sudo systemctl enable --now myservice.service
```

### Casi d'Uso Ideali per Portable Services

I Portable Services sono particolarmente adatti per ambienti dove si vuole distribuire applicazioni self-contained senza la complessità di un runtime container completo come Docker o Podman. Scenari tipici includono: distribuzione di agent di monitoraggio o raccolta log su flotte di server, deployment di microservizi stateless su sistemi embedded o IoT con risorse limitate, e aggiornamento atomico di servizi su sistemi immutabili (Fedora CoreOS, Ubuntu Core). Il vantaggio chiave rispetto ai container tradizionali è l'integrazione nativa con il sistema di init — journald, cgroup accounting e le direttive di hardening funzionano senza configurazione aggiuntiva.

---

## FAQ (15+)

**D: Qual è la differenza tra `systemctl restart` e `systemctl reload`?**
R: `restart` ferma e riavvia il processo (stop + start). `reload` invia un segnale (tipicamente SIGHUP) al processo perché rilegga la configurazione senza fermarsi. Non tutti i servizi supportano reload — usare `reload-or-restart` per un fallback automatico. Il reload è preferibile quando si vuole evitare downtime e il servizio lo supporta.

**D: Perché usare `systemctl edit` anziché modificare direttamente il file?**
R: `systemctl edit` crea un drop-in override in `/etc/systemd/system/unit.d/override.conf`. Il file originale in `/usr/lib/systemd/system/` non viene toccato, quindi gli aggiornamenti del pacchetto non sovrascriveranno le personalizzazioni. Inoltre, `systemctl edit --full` copia l'intero file in `/etc/` dove ha precedenza. Entrambi gli approcci eseguono automaticamente `daemon-reload` alla chiusura dell'editor.

**D: Come migrare un cron job a un timer systemd?**
R: Creare due file: un `.service` con `Type=oneshot` e il comando in `ExecStart=`, e un `.timer` con `OnCalendar=` che corrisponde all'espressione cron. Esempio: `*/5 * * * *` diventa `OnCalendar=*-*-* *:0/5:00`. Abilitare solo il timer con `systemctl enable --now mytask.timer`. I vantaggi: log in journald, `Persistent=yes` per recuperare esecuzioni perse, e gestione dipendenze.

**D: Cosa fa `DynamicUser=yes`?**
R: systemd crea un utente e gruppo temporanei (con UID/GID alto e casuale) per l'esecuzione del servizio. Quando il servizio si ferma, l'utente scompare. Non lascia tracce in `/etc/passwd` o `/etc/shadow`. Implica automaticamente `RemoveIPC=yes`, `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateTmp=yes`. Ideale per servizi stateless o che usano solo `StateDirectory=`, `CacheDirectory=`, `LogsDirectory=`.

**D: Come forzare un servizio a ripartire dopo N fallimenti?**
R: Usare `Restart=on-failure` con `RestartSec=` per il delay e `StartLimitBurst=` / `StartLimitIntervalSec=` per il rate limiting. Per un backoff esponenziale: `RestartSteps=10` e `RestartMaxDelaySec=5min` (v253+). Quando il rate limit viene raggiunto, `StartLimitAction=` definisce l'azione (none, reboot, poweroff).

**D: Qual è la differenza tra `After=network.target` e `After=network-online.target`?**
R: `network.target` indica che lo stack di rete è configurato e i dispositivi di rete sono stati trovati, ma non garantisce che la connessione sia funzionante. `network-online.target` attende che almeno un'interfaccia abbia una configurazione completa e connettività (IP, gateway, DNS). Per servizi che necessitano connessione attiva, usare `After=network-online.target` con `Wants=network-online.target`.

**D: Posso eseguire servizi systemd senza essere root?**
R: Sì, con le unit utente. Salvare i file in `~/.config/systemd/user/` e usare `systemctl --user start myapp.service`. I servizi utente si avviano al login e si fermano al logout. Per servizi persistenti, abilitare il "lingering" con `loginctl enable-linger username` — i servizi utente rimangono attivi anche senza sessione login.

**D: Come limitare un servizio a un singolo core CPU?**
R: Usare `CPUQuota=100%` (limita a 1 core) o `AllowedCPUs=3` (vincola al core 3). `CPUQuota=100%` è un limite temporale (il processo non può usare più del 100% di un core), mentre `AllowedCPUs=` vincola fisicamente il processo a specifici core (affinità).

**D: `ProtectSystem=strict` causa errori di scrittura. Come risolvere?**
R: `strict` rende tutto il filesystem read-only tranne `/dev`, `/proc`, `/sys`. Aggiungere eccezioni con `ReadWritePaths=/var/lib/myapp /var/log/myapp`. Meglio ancora, usare `StateDirectory=myapp`, `LogsDirectory=myapp`, `CacheDirectory=myapp` — systemd crea e gestisce queste directory automaticamente con i permessi corretti.

**D: Cosa succede se dimentico `daemon-reload` dopo aver modificato un unit file?**
R: systemd continua a usare la configurazione vecchia fino al reload. L'unità che modifica la configurazione non verrà influenzata finché non si esegue `systemctl daemon-reload`. systemd potrebbe mostrare un warning "Warning: unit file has changed on disk" quando si interagisce con la unit.

**D: Come verificare che il sealing del journal funziona?**
R: Eseguire `journalctl --verify`. Il comando controlla l'integrità di ogni file journal e restituisce PASS o FAIL. Il sealing FSS (Forward Secure Sealing) assicura che i log non possano essere modificati retroattivamente, anche se un attaccante ottiene la chiave corrente.

**D: systemd-oomd uccide i miei servizi. Come proteggerli?**
R: Aggiungere `ManagedOOMPreference=avoid` al servizio critico. Questo indica a systemd-oomd di preferire altri cgroup come candidati all'uccisione. In alternativa, assicurarsi che il servizio abbia un `MemoryMax=` adeguato e investigare eventuali memory leak nell'applicazione.

**D: Come creare un servizio che si avvia solo se un file esiste?**
R: Usare `ConditionPathExists=/path/to/file` nella sezione `[Unit]`. Se il file non esiste, la unit viene skippata silenziosamente (non errore). Per un errore esplicito, usare `AssertPathExists=` invece. Altre condizioni utili: `ConditionPathIsDirectory=`, `ConditionFileNotEmpty=`, `ConditionDirectoryNotEmpty=`.

**D: Qual è il modo corretto per gestire segreti nei servizi systemd?**
R: Usare il sistema di credentials: `LoadCredentialEncrypted=` per file cifrati, `SetCredentialEncrypted=` per valori inline cifrati. I segreti vengono decifrati a runtime e resi disponibili in `$CREDENTIALS_DIRECTORY/` in sola lettura. Evitare `Environment=` (visibile in `/proc/<pid>/environ`) e `EnvironmentFile=` (file in chiaro su disco).

**D: Come monitorare l'uso delle risorse di tutti i servizi in tempo reale?**
R: `systemd-cgtop` mostra CPU, memoria e I/O per ogni cgroup in tempo reale, simile a `top` ma per servizio/slice. Per un singolo servizio: `systemctl show myapp.service -p MemoryCurrent,CPUUsageNSec,TasksCurrent`. Per il filesystem cgroup diretto: `cat /sys/fs/cgroup/system.slice/myapp.service/memory.current`.

**D: Posso usare systemd-sysext su un sistema non immutabile?**
R: Sì, sysext funziona su qualsiasi sistema con systemd. Su sistemi non immutabili è meno comune perché si possono installare pacchetti normalmente, ma resta utile per estensioni temporanee (tool di debug, monitoring) o per mantenere una separazione netta tra OS base ed estensioni. L'unmerge rimuove tutto istantaneamente.
