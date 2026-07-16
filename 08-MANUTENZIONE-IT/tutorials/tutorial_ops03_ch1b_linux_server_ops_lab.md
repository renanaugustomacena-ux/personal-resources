# Tutorial: Gestione Linux Server — Operazioni Quotidiane e Avanzate — Hands-On Lab

> **Documento di riferimento:** `03-gestione-sistemi-operativi.md` (sezione Linux Server)
> **Dominio:** Gestione Sistemi Operativi
> **Ambito:** Ubuntu Server 22.04: patch management, systemd, journald, filesystem, utenti e permessi, sicurezza baseline
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio — richiede lab ops00 configurato, nozioni ITIL (ops01a), preferibilmente ops03a completato
> **Prerequisiti:** `tutorial_ops00` (lab con SRV-LINUX-01 Ubuntu 22.04)
> **Ambiente:** Principalmente SRV-LINUX-01 (Ubuntu 22.04) — accesso via SSH

---

## Lab Environment Setup

**Connessione SSH a SRV-LINUX-01 da WKS-LAB-01:**

```powershell
# Da WKS-LAB-01 (Windows), apri PowerShell o Windows Terminal
ssh lab-admin@192.168.56.20
# Password: Lab@2024!

# Verifica identità del server al primo accesso:
# Rispondi "yes" alla domanda sul fingerprint ECDSA
```

**Oppure da DC-LAB-01:**

```powershell
# PowerShell integra SSH client da Windows Server 2019 in poi
ssh lab-admin@192.168.56.20
```

**Verifica rapida che il lab sia funzionante:**

```bash
# Su SRV-LINUX-01
hostname && ip addr show enp0s8 | grep "inet " && uptime
```

Output atteso:
```
srv-linux-01
    inet 192.168.56.20/24 brd 192.168.56.255 scope global enp0s8
 14:30:22 up 2 days,  3:12,  1 user,  load average: 0.08, 0.05, 0.01
```

---

## PART A: FONDAMENTI — Linux Server come Piattaforma di Servizio

> Linux Server non è "Ubuntu con il desktop rimosso". È un ecosistema di tool filosoficamente diverso da Windows: ogni componente ha uno scopo preciso, si configura a riga di comando, e si compone con altri tool Unix. Capire questo modello è la chiave per diventare un Linux Server Administrator efficace.

---

### Concetto A1: Linux Server vs Windows Server — Una Filosofia Diversa

> **Analogia.** Windows Server è come un SUV premium: tutto integrato, GUI ricca, molte funzioni già configurate e nascoste sotto il cofano. Linux Server è come un'auto da rally: nessun optional innecessario, ogni componente è visibile e sostituibile, massima performance ma richiede il meccanico giusto per la manutenzione. Nessuno dei due è "migliore" — servono a scopi diversi.

| Caratteristica | Windows Server 2022 | Ubuntu Server 22.04 LTS |
|---|---|---|
| **Interfaccia predefinita** | GUI (opzionale: Server Core) | CLI only |
| **Configurazione** | Grafica + PowerShell | File di testo + comandi bash |
| **Init system** | Service Control Manager (SCM) | systemd |
| **Log system** | Event Log (.evtx) | journald + syslog |
| **Package manager** | Windows Update / WinGet | apt / dpkg |
| **Costo licenza** | Per-core + CAL | Gratuito (Ubuntu Pro: opzionale) |
| **Ciclo di vita** | 10 anni (LTSC) | 5 anni (LTS) / 10 anni (Ubuntu Pro) |
| **Patching riavvio** | Quasi sempre | Dipende dal componente (kernel → riavvio) |
| **Configurazione rete** | PowerShell / GUI | Netplan → networkd |

**La filosofia Unix in 3 principi:**

1. **Fai una cosa sola, ma falla bene**: `grep` cerca testo, `sort` ordina, `awk` processa. Si compongono con `|` (pipe).
2. **Tutto è un file**: la configurazione di rete è in `/etc/netplan/`, i processi sono in `/proc/`, i dispositivi in `/dev/`.
3. **Silenzioso se va bene**: i comandi Unix non stampano nulla se l'operazione è riuscita. Nessun output = successo.

---

### Concetto A2: La Struttura del Filesystem Linux — Dove si Trova Cosa

> **Analogia.** In un ristorante professionale, ogni cosa ha il suo posto preciso: i coltelli nella cassetta apposita, le spezie in fila alfabetica, i documenti nello studio del ristoratore. Se un cuoco mette la farina nel frigorifero "per comodità", il ristorante entra in crisi. Linux ha lo stesso approccio: ogni tipo di file ha una posizione standard definita dallo standard FHS (Filesystem Hierarchy Standard).

**Le directory fondamentali che un Linux Admin deve conoscere:**

| Directory | Scopo | Esempi |
|---|---|---|
| `/etc` | **Configurazione sistema** — LEGGERE, MODIFICARE | `/etc/ssh/sshd_config`, `/etc/netplan/`, `/etc/cron.d/` |
| `/var` | **Dati variabili** — log, spool, cache | `/var/log/`, `/var/lib/docker/`, `/var/cache/apt/` |
| `/opt` | **Software opzionale** | `/opt/glpi/`, applicazioni enterprise |
| `/home` | **Home directory utenti** | `/home/lab-admin/` |
| `/usr` | **Binari, librerie, documentazione** | `/usr/bin/`, `/usr/lib/`, `/usr/share/doc/` |
| `/tmp` | **File temporanei** (cancellati al riavvio) | Log temporanei, file lock |
| `/proc` | **Filesystem virtuale kernel** (solo lettura) | `/proc/cpuinfo`, `/proc/meminfo`, `/proc/PID/` |
| `/sys` | **Filesystem virtual hardware/kernel** | Parametri kernel, dispositivi |
| `/boot` | **Kernel e bootloader** | `vmlinuz-*`, `initrd.img-*`, `grub/` |
| `/dev` | **Device files** | `/dev/sda` (disco), `/dev/null`, `/dev/random` |

**Perché mi interessa?** — Quando un disco è pieno, sai dove cercare: `/var/log/` (log che crescono), `/var/cache/` (cache da pulire), `/tmp` (file temporanei dimenticati), `/home/` (utenti che scaricano troppo). Un comando come `du -sh /var/log/*` ti dice in 2 secondi dove sta il problema.

```bash
# Visualizza uso disco per directory di primo livello
df -h
du -sh /* 2>/dev/null | sort -rh | head -15
```

---

### Concetto A3: systemd — Il Cuore di Ubuntu Server

> **Analogia.** systemd è come il direttore di un'orchestra: gestisce l'avvio del sistema (determina l'ordine con cui gli strumenti entrano), dirige i servizi (fa suonare ogni musicista al momento giusto), e reagisce ai problemi (se un violino smette di suonare, lo fa ripartire). Prima di systemd, c'erano script di init che si chiamavano a vicenda in modo caotico — come un'orchestra senza direttore.

**I concetti fondamentali di systemd:**

```
systemd ──────────────────────────────────────────────────
│
├── Units (unità di gestione)
│     ├── service (.service) — processi da avviare (nginx, sshd, docker)
│     ├── timer (.timer) — schedulazione temporale (equivalente cron)
│     ├── socket (.socket) — attivazione su richiesta di connessione
│     ├── mount (.mount) — punti di montaggio filesystem
│     └── target (.target) — gruppi di unit (equivalente runlevel)
│
├── Journal (sistema di log)
│     └── journalctl — interfaccia per leggere i log
│
└── Targets principali
      ├── multi-user.target — avvio normale (no GUI)
      ├── graphical.target — avvio con GUI
      └── rescue.target — single-user mode
```

**I comandi systemctl fondamentali:**

```bash
# Stato di un servizio
systemctl status sshd.service

# Avviare / fermare / riavviare
sudo systemctl start  nginx.service
sudo systemctl stop   nginx.service
sudo systemctl restart nginx.service

# Abilitare all'avvio / disabilitare
sudo systemctl enable  nginx.service
sudo systemctl disable nginx.service

# Trovare servizi in stato "failed"
systemctl --failed

# Tutti i servizi con stato
systemctl list-units --type=service --all
```

**L'output di `systemctl status` — come leggerlo:**

```
● ssh.service - OpenBSD Secure Shell server
     Loaded: loaded (/lib/systemd/system/ssh.service; enabled; ...)
     Active: active (running) since Tue 2026-07-15 10:32:14 UTC; 4h 12min ago
   Main PID: 892 (sshd)
      Tasks: 1 (limit: 4614)
     Memory: 5.3M
        CPU: 423ms
     CGroup: /system.slice/ssh.service
             └─892 "sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups"
```

Riga per riga:
- `Loaded: loaded ... enabled` → il servizio è installato e parte al boot
- `Active: active (running)` → il servizio è in esecuzione ora
- `Main PID: 892` → il PID del processo principale
- `Memory: 5.3M` → la memoria consumata (grazie a cgroups)

---

### Concetto A4: journald — Il Sistema di Log Linux

> **Analogia.** Il Windows Event Log è come un archivio di buste lettere: ogni voce è in un file binario strutturato (.evtx). Il journald di Linux è come un database binario con un'interfaccia di query potente: puoi filtrare per servizio, per tempo, per priorità, per PID — e tutto con un solo strumento.

**journalctl — la sintassi base:**

```bash
# Tutti i log (dal sistema al boot corrente)
journalctl

# Log in tempo reale (come tail -f per syslog)
journalctl -f

# Log di un servizio specifico
journalctl -u sshd.service
journalctl -u docker.service --since "2 hours ago"

# Log degli ultimi 50 errori
journalctl -p err -n 50

# Log del boot corrente
journalctl -b

# Log del boot precedente
journalctl -b -1

# Log per timeframe
journalctl --since "2026-07-15 08:00" --until "2026-07-15 10:00"

# Log in formato breve (come syslog tradizionale)
journalctl -o short-iso

# Log in JSON (per parsing automatico)
journalctl -o json | head -5
```

**I file di log tradizionali (sempre presenti in Ubuntu):**

```bash
# Auth log — login, sudo, SSH
tail -f /var/log/auth.log

# Syslog — messaggi di sistema generali
tail -f /var/log/syslog

# Kernel ring buffer — messaggi hardware/kernel
dmesg | tail -30
dmesg -T | grep -i error   # Con timestamp e filtro errori

# Log apt — installazioni/aggiornamenti
cat /var/log/apt/history.log | tail -40
```

---

### Concetto A5: Utenti, Gruppi e Permessi Linux

> **Analogia.** Il sistema di permessi Linux è come un sistema di badge aziendali: ogni file ha un "proprietario" (chi lo ha creato), un "gruppo" (il reparto a cui appartiene), e poi "tutti gli altri". Il badge di ogni persona determina cosa può fare: leggere il documento, modificarlo, o eseguirlo. `root` è il CEO con accesso a tutto; gli utenti normali hanno solo il loro spazio.

**Il modello utente/gruppo/permessi:**

```
File: -rwxr-xr-- 1 lab-admin developers 4096 Jul 15 10:00 script.sh
       │││││││││ │     │           │       │
       ││││││││└─┘     │           │       └── dimensione (byte)
       │││││││└── altri: r-- (solo lettura)
       ││││└┴┴─── gruppo: r-x (lettura + esecuzione)
       │└┴┴────── proprietario: rwx (tutto)
       └────────── tipo: - (file), d (directory), l (symlink)
```

**Comandi essenziali di gestione utenti:**

```bash
# Aggiungere un utente
sudo adduser mario.rossi         # interattivo, crea home dir
sudo useradd -m -s /bin/bash -G sudo mario.rossi  # non interattivo

# Modificare un utente
sudo usermod -aG docker mario.rossi   # aggiunge al gruppo docker
sudo usermod -L mario.rossi           # blocca l'account (Lock)
sudo usermod -U mario.rossi           # sblocca l'account (Unlock)

# Eliminare un utente
sudo deluser mario.rossi             # rimuove utente ma lascia home
sudo deluser --remove-home mario.rossi  # rimuove anche la home dir

# Verificare chi è loggato ora
who
w

# Verificare le ultime sessioni di login
last | head -20
lastb | head -10  # tentativi di login falliti
```

**sudo — l'escalation dei privilegi sicura:**

```bash
# Verificare i permessi sudo di un utente
sudo -l -U lab-admin

# File di configurazione sudo (NON modificare direttamente!)
# Usa sempre: sudo visudo
sudo visudo

# Aggiungere un utente al gruppo sudo (Ubuntu)
sudo usermod -aG sudo mario.rossi

# Verificare i gruppi di un utente
id mario.rossi
groups mario.rossi
```

---

### Concetto A6: Il Ciclo di Vita di un Servizio Linux — Dalla Installazione al Monitoring

> **Analogia.** Installare un servizio su Linux è come assumere un nuovo dipendente: prima fai il colloquio (installi il software), poi gli assegni la scrivania (configuri i file), poi lo presenti ai colleghi (abiliti il servizio), e infine verifichi che stia lavorando bene (monitori i log). Se la performance cala, prima capisci il problema (journalctl), poi intervieni.

**Il ciclo completo di esempio con nginx:**

```bash
# 1. Installazione
sudo apt install nginx -y

# 2. Configurazione (modifica il file di config)
sudo nano /etc/nginx/sites-available/default
sudo nginx -t  # verifica sintassi configurazione

# 3. Abilitazione e avvio
sudo systemctl enable nginx
sudo systemctl start nginx

# 4. Verifica funzionamento
systemctl status nginx
curl -s http://localhost | head -5

# 5. Monitoring continuo
journalctl -u nginx -f

# 6. Troubleshooting rapido se qualcosa non va
sudo nginx -t                   # controlla config
cat /var/log/nginx/error.log    # leggi errori
ss -tlnp | grep nginx           # porta aperta?
```

Questo ciclo — installazione → configurazione → abilitazione → verifica → monitoring — è lo stesso per ogni servizio Linux.

---

## PART B: OPERAZIONI — Amministrare Ubuntu Server 22.04 (SRV-LINUX-01)

> Tutti gli esercizi seguenti si eseguono su SRV-LINUX-01. Connettiti via SSH: `ssh lab-admin@192.168.56.20`

---

### Esercizio B1: Configurazione Iniziale e Hardening Base

**Obiettivo.** Partendo dall'installazione base di Ubuntu 22.04, applicare la configurazione iniziale di sicurezza che ogni server deve avere prima di andare in produzione.

**Step 1 — Aggiornamento sistema completo**

```bash
# Aggiorna la lista dei pacchetti e installa tutti gli aggiornamenti
sudo apt update && sudo apt upgrade -y

# Installa pacchetti essenziali per l'amministrazione
sudo apt install -y \
    vim \
    htop \
    curl \
    wget \
    git \
    net-tools \
    dnsutils \
    tree \
    ncdu \
    unzip \
    jq

# Verifica se è necessario un riavvio
[ -f /var/run/reboot-required ] && echo "RIAVVIO NECESSARIO" || echo "Nessun riavvio necessario"
cat /var/run/reboot-required.pkgs 2>/dev/null
```

**Step 2 — Configurazione hostname e timezone**

```bash
# Verifica hostname attuale
hostnamectl

# Imposta il hostname corretto (se non già configurato in ops00)
sudo hostnamectl set-hostname srv-linux-01

# Imposta la timezone italiana
sudo timedatectl set-timezone Europe/Rome
timedatectl status
```

Output atteso di `timedatectl`:
```
               Local time: Wed 2026-07-15 14:35:22 CEST
           Universal time: Wed 2026-07-15 12:35:22 UTC
                 RTC time: Wed 2026-07-15 12:35:22
                Time zone: Europe/Rome (CEST, +0200)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```

**Step 3 — Hardening SSH (configurazione sicura)**

```bash
# Backup della configurazione originale
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.original

# Crea configurazione SSH hardenata
sudo tee /etc/ssh/sshd_config.d/99-lab-hardening.conf << 'EOF'
# Lab SSH Hardening Configuration
PermitRootLogin no
PasswordAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30
Banner /etc/ssh/banner.txt
EOF

# Crea un banner di accesso
sudo tee /etc/ssh/banner.txt << 'EOF'
==============================================================
 SISTEMA DI LAB IT — ACCESSO AUTORIZZATO SOLO AGLI UTENTI
 ISCRITTI AL CORSO. TUTTI GLI ACCESSI SONO REGISTRATI.
==============================================================
EOF

# Verifica la sintassi della configurazione SSH
sudo sshd -t
echo "Configurazione SSH valida: exit code $?"

# Applica la nuova configurazione (ricarica senza disconnettere la sessione corrente)
sudo systemctl reload sshd
```

**Checkpoint B1:**
- [ ] `apt update && apt upgrade` completato senza errori
- [ ] Hostname impostato: `srv-linux-01`
- [ ] Timezone: `Europe/Rome`, NTP sincronizzato
- [ ] SSH: banner visibile al prossimo login, PermitRootLogin=no

---

### Esercizio B2: Gestione Pacchetti — Ciclo Completo apt

**Obiettivo.** Padroneggiare `apt` per la gestione di pacchetti in un ambiente di produzione: non solo installare, ma gestire repository, bloccare versioni, pulire.

**Step 1 — Inventario dei pacchetti installati**

```bash
# Lista completa dei pacchetti esplicitamente installati (non dipendenze)
apt-mark showmanual | head -30

# Numero totale di pacchetti installati
dpkg -l | grep -c "^ii"

# Pacchetti che occupano più spazio
dpkg-query -W --showformat='${Installed-Size}\t${Package}\n' | \
    sort -rn | head -20 | awk '{printf "%s MB\t%s\n", $1/1024, $2}'

# Verifica la coerenza del database dei pacchetti
sudo apt-get check
```

**Step 2 — Aggiornamenti di sicurezza only**

```bash
# Lista solo gli aggiornamenti di sicurezza disponibili
sudo unattended-upgrade --dry-run -d 2>&1 | grep "Packages that will be upgraded"

# Installare solo i pacchetti di sicurezza (senza aggiornare il resto)
sudo unattended-upgrade -d

# Configura unattended-upgrades per il lab
sudo apt install unattended-upgrades -y

# Abilita gli aggiornamenti automatici di sicurezza
sudo dpkg-reconfigure -plow unattended-upgrades
# Scegli "Yes" alla domanda se abilitare gli aggiornamenti automatici

# Verifica configurazione
cat /etc/apt/apt.conf.d/20auto-upgrades
```

**Step 3 — Bloccare un pacchetto (package hold)**

In produzione può essere necessario bloccare l'aggiornamento di un pacchetto perché la versione nuova romperebbe un'applicazione.

```bash
# Blocca la versione corrente di nginx
sudo apt install nginx -y
sudo apt-mark hold nginx

# Verifica quali pacchetti sono in hold
apt-mark showhold

# Tentativo di aggiornamento — nginx verrà saltato
sudo apt upgrade -y

# Rimuovi il blocco quando sei pronto ad aggiornare
sudo apt-mark unhold nginx
apt-mark showhold  # deve essere vuoto ora
```

**Step 4 — Cleanup e manutenzione database apt**

```bash
# Rimuovi pacchetti non più necessari (orfani di dipendenze)
sudo apt autoremove -y

# Pulisci la cache dei pacchetti scaricati (libera spazio)
sudo apt autoclean
sudo apt clean

# Quante dimensioni occupava la cache?
du -sh /var/cache/apt/archives/ 2>/dev/null || echo "Cache pulita"

# Verifica la salute del database apt
sudo dpkg --audit
```

**Checkpoint B2:**
- [ ] `dpkg -l | grep -c "^ii"` mostra il numero di pacchetti installati
- [ ] `unattended-upgrades` installato e abilitato
- [ ] `apt-mark hold nginx` funzionante (nginx rimane nella versione corrente dopo apt upgrade)
- [ ] `apt autoremove && apt clean` eseguiti

---

### Esercizio B3: systemd — Gestione e Monitoraggio Servizi

**Obiettivo.** Padroneggiare `systemctl` per gestire il ciclo di vita dei servizi, comprendere lo stato del sistema all'avvio, e configurare l'auto-restart in caso di crash.

**Step 1 — Audit completo dei servizi**

```bash
# Tutti i servizi — stato, tipo, descrizione
systemctl list-units --type=service --all | head -30

# Solo i servizi in stato "failed" (critico da verificare sempre!)
systemctl --failed

# Servizi abilitati all'avvio (startup)
systemctl list-unit-files --type=service --state=enabled

# Analisi del tempo di avvio
systemd-analyze
systemd-analyze blame | head -15
systemd-analyze critical-chain
```

**Step 2 — Creare un servizio systemd custom**

Creiamo un servizio che esegue uno script di health check al boot:

```bash
# Prima: crea lo script di health check
sudo mkdir -p /opt/lab-scripts

sudo tee /opt/lab-scripts/startup-health-check.sh << 'SCRIPT'
#!/bin/bash
# startup-health-check.sh — Verifiche al boot di SRV-LINUX-01

LOG="/var/log/lab-startup-check.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "=== Boot Health Check: $DATE ===" >> "$LOG"

# Verifica disco
DISK_PCT=$(df / | awk 'NR==2{print $5}' | tr -d '%')
if [ "$DISK_PCT" -gt 85 ]; then
    echo "[WARN] Disco root: ${DISK_PCT}% utilizzato" >> "$LOG"
else
    echo "[ OK] Disco root: ${DISK_PCT}% utilizzato" >> "$LOG"
fi

# Verifica RAM
RAM_FREE=$(free -m | awk 'NR==2{print $7}')
echo "[ OK] RAM disponibile: ${RAM_FREE} MB" >> "$LOG"

# Verifica SSH
if systemctl is-active --quiet sshd; then
    echo "[ OK] SSH attivo" >> "$LOG"
else
    echo "[ERR] SSH non attivo!" >> "$LOG"
fi

# Verifica Docker (se installato)
if command -v docker &>/dev/null; then
    if systemctl is-active --quiet docker; then
        CONTAINERS=$(docker ps -q 2>/dev/null | wc -l)
        echo "[ OK] Docker attivo: $CONTAINERS container in esecuzione" >> "$LOG"
    else
        echo "[WARN] Docker installato ma non attivo" >> "$LOG"
    fi
fi

echo "=== Fine Health Check ===" >> "$LOG"
SCRIPT

sudo chmod +x /opt/lab-scripts/startup-health-check.sh

# Crea il file unit per systemd
sudo tee /etc/systemd/system/lab-startup-check.service << 'UNIT'
[Unit]
Description=Lab Startup Health Check
After=network.target docker.service
Wants=docker.service

[Service]
Type=oneshot
ExecStart=/opt/lab-scripts/startup-health-check.sh
StandardOutput=journal
StandardError=journal
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT

# Ricarica systemd, abilita e avvia
sudo systemctl daemon-reload
sudo systemctl enable lab-startup-check.service
sudo systemctl start lab-startup-check.service

# Verifica esecuzione
systemctl status lab-startup-check.service
cat /var/log/lab-startup-check.log
```

**Step 3 — Configurare auto-restart per un servizio critico**

In produzione, un servizio critico deve ripartire automaticamente se crasha:

```bash
# Visualizza la configurazione attuale di nginx (o ssh se nginx non è installato)
systemctl cat sshd.service | grep -A5 "\[Service\]"

# Crea un override per aggiungere auto-restart
sudo systemctl edit sshd.service
# L'editor si apre — incolla questo contenuto:
```

Quando l'editor si apre (nano di default), inserisci:

```ini
[Service]
Restart=on-failure
RestartSec=5s
StartLimitIntervalSec=60s
StartLimitBurst=3
```

Poi salva e chiudi:

```bash
# Applica le modifiche
sudo systemctl daemon-reload
sudo systemctl restart sshd.service

# Verifica che l'override sia attivo
systemctl show sshd.service | grep -E "Restart|StartLimit"
```

**Checkpoint B3:**
- [ ] `systemctl --failed` non mostra servizi problematici
- [ ] `systemd-analyze blame` mostra i servizi che rallentano il boot
- [ ] Servizio `lab-startup-check` creato, abilitato, e log visibile in `/var/log/lab-startup-check.log`
- [ ] Override sshd con auto-restart configurato

---

### Esercizio B4: Log Management — journald e logrotate

**Obiettivo.** Padroneggiare `journalctl` per investigare problemi e configurare `logrotate` per prevenire log che riempiono il disco.

**Step 1 — Query journald avanzate**

```bash
# Tutti gli errori dal boot corrente
journalctl -b -p err

# Log SSH degli ultimi 30 minuti con timestamp ISO
journalctl -u sshd --since "30 minutes ago" -o short-iso

# Conta i tentativi di login SSH falliti
journalctl _SYSTEMD_UNIT=sshd.service | grep -c "Failed password"

# Log in real-time di più servizi contemporaneamente
journalctl -f -u sshd -u docker 

# Dimensione attuale del journal
journalctl --disk-usage

# Cerca un testo specifico in tutti i log
journalctl --grep="Out of memory" | tail -20

# Log di un processo per PID
journalctl _PID=1234
```

**Step 2 — Simula un problema di log e indaga**

```bash
# Genera un fallimento SSH ripetuto (da un'altra finestra terminal o da DC-LAB-01)
# In PowerShell su WKS-LAB-01:
# for ($i=1; $i -le 5; $i++) { ssh wronguser@192.168.56.20 }

# Su SRV-LINUX-01: analizza i tentativi di login falliti
sudo grep "Failed password" /var/log/auth.log | tail -10
sudo grep "Invalid user" /var/log/auth.log | tail -10

# Conta i tentativi per IP sorgente
sudo grep "Failed password" /var/log/auth.log | \
    awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -10

# Con journalctl (metodo moderno)
journalctl _SYSTEMD_UNIT=sshd.service --since "1 hour ago" | \
    grep "Failed" | awk '{print $NF}' | sort | uniq -c | sort -rn
```

**Step 3 — Configurare logrotate per un log personalizzato**

```bash
# Crea un log fittizio che cresce (simula un'applicazione che scrive molto)
sudo touch /var/log/lab-app.log

# Scrivi 1000 righe di log di prova
for i in $(seq 1 1000); do
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Evento applicazione numero $i" | \
        sudo tee -a /var/log/lab-app.log > /dev/null
done

ls -lh /var/log/lab-app.log

# Crea la configurazione logrotate per questo log
sudo tee /etc/logrotate.d/lab-app << 'LOGRULE'
/var/log/lab-app.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 root adm
    postrotate
        # In produzione: ricarica il servizio qui
        # systemctl reload myapp 2>/dev/null || true
        echo "Log ruotato: $(date)" >> /var/log/logrotate-lab.log
    endscript
}
LOGRULE

# Testa la configurazione (dry-run — non ruota davvero)
sudo logrotate -d /etc/logrotate.d/lab-app

# Forza la rotazione per testare
sudo logrotate -f /etc/logrotate.d/lab-app

# Verifica il risultato
ls -lh /var/log/lab-app*
```

**Step 4 — Pulizia e retention del journal**

```bash
# Configura retention del journal
sudo mkdir -p /etc/systemd/journald.conf.d/

sudo tee /etc/systemd/journald.conf.d/99-lab-retention.conf << 'JCONF'
[Journal]
Storage=persistent
SystemMaxUse=500M
SystemKeepFree=200M
SystemMaxFileSize=50M
MaxRetentionSec=30day
Compress=yes
JCONF

# Applica la configurazione
sudo systemctl restart systemd-journald

# Verifica la configurazione applicata
journalctl --disk-usage
sudo journalctl --verify
```

**Checkpoint B4:**
- [ ] `journalctl -b -p err` eseguito — nessun errore critico inaspettato
- [ ] Tentativi SSH falliti trovati e analizzati (grep o journalctl)
- [ ] Configurazione logrotate per `lab-app.log` creata e testata
- [ ] Journal con retention configurata: max 500M, 30 giorni

---

### Esercizio B5: Monitoraggio Filesystem e Performance

**Obiettivo.** Stabilire la baseline di performance di SRV-LINUX-01 e creare un sistema di alerting per disco pieno.

**Step 1 — Inventario completo disco e filesystem**

```bash
# Uso disco per filesystem
df -hT

# Uso inode (un filesystem può esaurire gli inode prima dello spazio!)
df -ih

# Le 20 directory che occupano più spazio
sudo du -sh /* 2>/dev/null | sort -rh | head -20

# Tool interattivo per esplorare l'uso disco
# ncdu (installato in B1)
ncdu /var

# Trova file più grandi di 100MB
sudo find / -xdev -type f -size +100M -exec ls -lh {} \; 2>/dev/null | \
    sort -k5 -rh | head -10
```

**Step 2 — Monitoraggio performance sistema**

```bash
# Snapshot performance corrente
echo "=== SISTEMA ===" && uname -r && uptime
echo "=== CPU ===" && top -bn1 | head -15
echo "=== MEMORIA ===" && free -h
echo "=== DISCO ===" && df -h | grep -v tmpfs
echo "=== RETE ===" && ip -s link show enp0s8

# htop — monitor interattivo (q per uscire)
htop

# iostat — I/O disco in tempo reale (installa sysstat se non presente)
sudo apt install sysstat -y
iostat -x 2 3

# vmstat — memoria, swap, I/O
vmstat 2 5

# ss — connessioni di rete attive
ss -tlnp    # porte TCP in ascolto
ss -tunp    # tutte le connessioni UDP e TCP
```

**Step 3 — Script di alerting disco**

```bash
# Crea script di monitoraggio disco con alerting
sudo tee /opt/lab-scripts/disk-alert.sh << 'SCRIPT'
#!/bin/bash
# disk-alert.sh — Alert quando il disco supera la soglia

THRESHOLD=80
LOG="/var/log/disk-alert.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Controllo disco..." >> "$LOG"

# Controlla ogni filesystem montato
while IFS= read -r line; do
    USAGE=$(echo "$line" | awk '{print $5}' | tr -d '%')
    MOUNT=$(echo "$line" | awk '{print $6}')
    DEVICE=$(echo "$line" | awk '{print $1}')
    
    if [ "$USAGE" -gt "$THRESHOLD" ] 2>/dev/null; then
        MSG="[ALERT] $DATE — Disco $DEVICE montato in $MOUNT: ${USAGE}% usato (soglia: ${THRESHOLD}%)"
        echo "$MSG" >> "$LOG"
        # In produzione: invia email, notifica Slack, apri ticket GLPI
        echo "$MSG"  # Per ora: stampa a schermo
    fi
done < <(df -h | grep "^/dev/" | grep -v tmpfs)

echo "[$DATE] Controllo completato." >> "$LOG"
SCRIPT

sudo chmod +x /opt/lab-scripts/disk-alert.sh

# Testa subito
sudo /opt/lab-scripts/disk-alert.sh

# Pianifica con cron ogni 15 minuti
(sudo crontab -l 2>/dev/null; echo "*/15 * * * * /opt/lab-scripts/disk-alert.sh") | \
    sudo crontab -

# Verifica il cron dell'utente root
sudo crontab -l
```

**Checkpoint B5:**
- [ ] `df -hT` mostra i filesystem e i tipi (ext4, tmpfs, ecc.)
- [ ] `df -ih` mostra l'uso degli inode (nessun filesystem al 100%)
- [ ] `iostat` installato e output di I/O disco interpretato
- [ ] Script `disk-alert.sh` creato e pianificato ogni 15 minuti con cron

---

### Esercizio B6: Gestione Utenti e Hardening Sicurezza

**Obiettivo.** Creare la struttura di utenti del lab simulando un ambiente aziendale, e verificare la postura di sicurezza con strumenti standard.

**Step 1 — Struttura utenti aziendale su Linux**

```bash
# Crea gruppi per dipartimento
sudo groupadd it-team
sudo groupadd developers
sudo groupadd readonly-users

# Crea utenti (in un'azienda reale, questi vengono da LDAP/AD)
sudo useradd -m -s /bin/bash -G it-team   -c "Mario Rossi - IT Team"  mario.rossi
sudo useradd -m -s /bin/bash -G developers -c "Anna Bianchi - DevOps"  anna.bianchi
sudo useradd -m -s /bin/bash -G readonly-users -c "Luca Ferrari - Auditor" luca.ferrari

# Imposta password
echo "mario.rossi:Lab@2024!" | sudo chpasswd
echo "anna.bianchi:Lab@2024!" | sudo chpasswd
echo "luca.ferrari:Lab@2024!" | sudo chpasswd

# Aggiungi mario.rossi al gruppo sudo (ha privilegi admin IT)
sudo usermod -aG sudo mario.rossi

# Verifica la struttura creata
echo "--- Utenti creati ---"
grep -E "mario.rossi|anna.bianchi|luca.ferrari" /etc/passwd
echo "--- Gruppi ---"
grep -E "it-team|developers|readonly-users" /etc/group
echo "--- Sudo ---"
groups mario.rossi
```

**Step 2 — Configurare sudo con privilegi granulari**

```bash
# Principio del minimo privilegio: anna.bianchi può solo gestire Docker
sudo tee /etc/sudoers.d/90-lab-permissions << 'SUDOERS'
# anna.bianchi: può gestire Docker ma non può fare tutto
anna.bianchi ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose

# mario.rossi: pieno accesso sudo (già nel gruppo sudo)
# luca.ferrari: nessun accesso sudo

# Log tutti i comandi sudo nel syslog
Defaults logfile="/var/log/sudo.log"
SUDOERS

# Verifica la sintassi (IMPORTANTE: errori nel file sudoers possono bloccare il sistema!)
sudo visudo -c
sudo visudo -c -f /etc/sudoers.d/90-lab-permissions

echo "File sudoers valido"
```

**Step 3 — Audit di sicurezza del sistema**

```bash
# Trova file con permessi SUID pericolosi
echo "--- File SUID (possibile escalation privilegi) ---"
sudo find / -perm -4000 -type f -exec ls -la {} \; 2>/dev/null | head -15

# Trova file world-writable (scrivibili da chiunque)
echo "--- File world-writable ---"
sudo find / -xdev -perm -0002 -type f -not -path "/proc/*" -not -path "/sys/*" \
    2>/dev/null | head -10

# Verifica le porte in ascolto (superficie d'attacco di rete)
echo "--- Porte in ascolto ---"
sudo ss -tlnp

# Verifica i servizi abilitati all'avvio
echo "--- Servizi abilitati ---"
systemctl list-unit-files --type=service --state=enabled | grep -v "@"

# Controlla gli utenti con UID 0 (solo root deve avere UID 0)
echo "--- Utenti con UID 0 ---"
awk -F: '($3 == 0) {print $1}' /etc/passwd

# Utenti con shell valida (non /usr/sbin/nologin)
echo "--- Utenti con shell di login ---"
grep -v "/usr/sbin/nologin\|/bin/false" /etc/passwd | grep -v "^#"
```

**Checkpoint B6:**
- [ ] 3 utenti (mario.rossi, anna.bianchi, luca.ferrari) creati con gruppi corretti
- [ ] mario.rossi ha accesso sudo
- [ ] luca.ferrari NON ha accesso sudo (`sudo -l -U luca.ferrari` mostra "not allowed")
- [ ] File `/etc/sudoers.d/90-lab-permissions` valido (visudo -c non mostra errori)
- [ ] Audit sicurezza eseguito: nessun file world-writable critico, solo root ha UID 0

---

## PART C: SISTEMATIZZARE — Governance delle Operazioni Linux Server

---

### Progetto C1: SOP Linux Server — Monthly Health Check

Crea il file `/opt/lab-scripts/SOPs/SOP-LNX-001_monthly_health_check.md`:

```bash
sudo mkdir -p /opt/lab-scripts/SOPs
sudo tee /opt/lab-scripts/SOPs/SOP-LNX-001_monthly_health_check.md << 'SOP'
# SOP-LNX-001: Linux Server Monthly Health Check

**Versione:** 1.0  
**Data creazione:** 2026-07-15  
**Owner:** IT Operations  
**Applicabilità:** Tutti i server Ubuntu/Debian in produzione  

---

## 1. Scopo

Definire le attività mensili per garantire la salute di ogni Linux Server.

## 2. Frequenza

Prima settimana del mese, durante la maintenance window concordata.

## 3. Prerequisiti

- [ ] Snapshot VM creato (VirtualBox / VMware / Proxmox)
- [ ] Change Request aperta in GLPI con stato "Approvato"
- [ ] Accesso SSH con utente sudo verificato

## 4. Procedura

### 4.1 Aggiornamenti di Sicurezza (10 min)

    sudo apt update
    apt list --upgradable 2>/dev/null | grep -c upgradable
    sudo apt-get -s upgrade | grep "^Inst" | grep -i securi
    # Se ci sono aggiornamenti di sicurezza: installa dopo approvazione CAB

### 4.2 Servizi Falliti (5 min)

    systemctl --failed
    # Esito accettabile: "0 loaded units listed"

### 4.3 Disco e Filesystem (10 min)

    df -h
    df -ih
    # Soglia allarme: qualsiasi filesystem > 80%

### 4.4 Log di Sicurezza (15 min)

    sudo grep "Failed password" /var/log/auth.log | wc -l
    sudo grep "Invalid user" /var/log/auth.log | tail -5
    sudo last | head -20

### 4.5 Processi Anomali (5 min)

    ps aux --sort=-%cpu | head -10
    ps aux --sort=-%mem | head -10

### 4.6 Dimensione Journal (5 min)

    journalctl --disk-usage
    # Se > 500MB: journalctl --vacuum-size=400M

## 5. Criteri di Accettazione

- 0 servizi in stato "failed"
- Nessun filesystem > 80%
- < 100 tentativi di login falliti in un mese (per lab)
- Journal < 500 MB

## 6. Escalation

| Evento | Azione |
|--------|--------|
| Filesystem al 100% | Incident P1 immediato |
| Servizi critici falliti (sshd, docker) | Incident P2 + restart |
| > 1000 tentativi login | Incident P1 + analisi sicurezza |
SOP

echo "SOP creata."
cat /opt/lab-scripts/SOPs/SOP-LNX-001_monthly_health_check.md
```

---

### Progetto C2: Script Automazione — Monthly Linux Health Report

```bash
sudo tee /opt/lab-scripts/monthly_linux_health_report.sh << 'SCRIPT'
#!/bin/bash
# monthly_linux_health_report.sh — Report di salute mensile Linux Server
# Esegui: sudo /opt/lab-scripts/monthly_linux_health_report.sh

REPORT_DIR="/var/log/lab-reports"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M')
REPORT="$REPORT_DIR/linux_health_${TIMESTAMP}.txt"
HOSTNAME=$(hostname)

mkdir -p "$REPORT_DIR"

# --- Header ---
{
echo "========================================================"
echo " LINUX SERVER MONTHLY HEALTH REPORT"
echo " Host: $HOSTNAME | Data: $(date '+%Y-%m-%d %H:%M')"
echo "========================================================"

# --- Sistema ---
echo ""
echo "=== 1. INFORMAZIONI SISTEMA ==="
echo "OS: $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"
echo "Uptime: $(uptime -p)"
echo "Ultima riavvio: $(who -b | awk '{print $3, $4}')"

# --- Disco ---
echo ""
echo "=== 2. DISCO E FILESYSTEM ==="
df -h | grep -E "^/dev|^Filesystem"
echo ""
echo "Inode usage:"
df -ih | grep -E "^/dev|^Filesystem"

# Trova directory grandi
echo ""
echo "Top 5 directory per dimensione in /var:"
du -sh /var/* 2>/dev/null | sort -rh | head -5

# --- Memoria ---
echo ""
echo "=== 3. MEMORIA ==="
free -h
echo ""
SWAP_USED=$(free | awk 'NR==3{if($2>0) printf "%.0f", $3/$2*100; else print 0}')
echo "Swap utilizzato: ${SWAP_USED}%"
if [ "$SWAP_USED" -gt 20 ]; then
    echo "[WARN] Swap usage > 20% — possibile carenza RAM"
fi

# --- Servizi ---
echo ""
echo "=== 4. SERVIZI SYSTEMD ==="
FAILED=$(systemctl --failed --no-legend --no-pager 2>/dev/null | wc -l)
echo "Servizi in stato 'failed': $FAILED"
if [ "$FAILED" -gt 0 ]; then
    echo "[WARN] Servizi falliti:"
    systemctl --failed --no-legend --no-pager
fi

echo ""
echo "Servizi critici:"
for svc in ssh docker nginx mariadb postgresql; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo "  [ OK] $svc"
    elif systemctl is-enabled --quiet "$svc" 2>/dev/null; then
        echo "  [ERR] $svc abilitato ma non attivo!"
    fi
done

# --- Aggiornamenti disponibili ---
echo ""
echo "=== 5. AGGIORNAMENTI DISPONIBILI ==="
apt-get -s upgrade 2>/dev/null | grep "^Inst" | wc -l | \
    xargs -I{} echo "Pacchetti da aggiornare: {}"
apt-get -s upgrade 2>/dev/null | grep "^Inst" | grep -i securi | wc -l | \
    xargs -I{} echo "Di cui sicurezza: {}"

# --- Sicurezza ---
echo ""
echo "=== 6. SICUREZZA (ultimi 30 giorni) ==="
if [ -f /var/log/auth.log ]; then
    FAILED_LOGIN=$(grep -c "Failed password" /var/log/auth.log 2>/dev/null || echo 0)
    INVALID_USER=$(grep -c "Invalid user" /var/log/auth.log 2>/dev/null || echo 0)
    echo "Login SSH falliti: $FAILED_LOGIN"
    echo "Utenti non validi tentati: $INVALID_USER"
    
    echo ""
    echo "Top 5 IP con più tentativi falliti:"
    grep "Failed password" /var/log/auth.log 2>/dev/null | \
        awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -5 | \
        awk '{printf "  %s tentativi da %s\n", $1, $2}'
fi

# Utenti con UID 0
UID0=$(awk -F: '($3==0){print $1}' /etc/passwd | grep -v "^root$" | wc -l)
if [ "$UID0" -gt 0 ]; then
    echo "[ALERT] Trovati $UID0 utenti non-root con UID 0!"
    awk -F: '($3==0){print $1}' /etc/passwd | grep -v "^root$"
else
    echo "[ OK] Solo root ha UID 0"
fi

# --- Journal ---
echo ""
echo "=== 7. JOURNAL ==="
journalctl --disk-usage 2>/dev/null
JOURNAL_ERRORS=$(journalctl -b -p err --no-pager 2>/dev/null | wc -l)
echo "Errori nel journal (boot corrente): $JOURNAL_ERRORS"

echo ""
echo "========================================================"
echo " FINE REPORT"
echo "========================================================"
} | tee "$REPORT"

echo ""
echo "Report salvato in: $REPORT"
SCRIPT

sudo chmod +x /opt/lab-scripts/monthly_linux_health_report.sh

# Esegui subito il report
sudo /opt/lab-scripts/monthly_linux_health_report.sh
```

---

### Progetto C3: Connessione ITIL — Linux Server nelle Pratiche ITIL v4

**Mappatura delle operazioni Linux alle pratiche ITIL v4:**

| Attività Linux | Pratica ITIL v4 | Perché è importante |
|---|---|---|
| `apt upgrade` mensile | **Release Management** + **Change Control** | Ogni upgrade è un change che richiede test e approvazione |
| `systemctl --failed` giornaliero | **Monitoring and Event Management** | Rilevamento proattivo di failure prima che impattino utenti |
| `journalctl` analysis | **Problem Management** | Analisi causa radice di problemi ricorrenti |
| Creazione utenti/gruppi | **Identity and Access Management** | Controllo accesso con principio del minimo privilegio |
| `df -h` e disk-alert.sh | **Capacity and Performance Management** | Prevenire esaurimento risorse |
| Backup snapshot + logrotate | **Service Continuity Management** | Garantire restore e recupero dati |
| SOP-LNX-001 | **Service Configuration Management** | Documentare configurazioni standard |
| Audit sicurezza (SUID, world-writable) | **Information Security Management** | Ridurre superficie d'attacco |

**Il Linux Admin come ITIL Practitioner:**

Ogni comando che esegui su un server Linux incide su una delle 34 pratiche ITIL. Il sistema di log (journald) è il tuo audit trail; il cron per il disk-alert è il tuo monitoring; il SOP è il tuo documented procedure. Linux non ti dà un'interfaccia grafica che nasconde la complessità — ti costringe a capire esattamente cosa sta succedendo, che è esattamente quello che ITIL richiede a un IT Operations professional.

---

## Checklist di Validazione — Tutorial ops03b Completato

### Fondamenti (Part A)
- [ ] Sai elencare 5 differenze fondamentali tra Linux Server e Windows Server
- [ ] Sai spiegare le 10 directory principali del filesystem Linux e il loro scopo
- [ ] Sai usare `systemctl status`, `start`, `stop`, `enable`, `disable`
- [ ] Sai usare `journalctl` per filtrare per servizio, priorità, e tempo
- [ ] Sai leggere l'output di `ls -la` e interpretare i permessi rwx

### Operazioni (Part B)
- [ ] `apt update && apt upgrade` eseguito, sistema aggiornato
- [ ] Hostname: `srv-linux-01`, Timezone: `Europe/Rome`, NTP sincronizzato
- [ ] SSH hardening: PermitRootLogin=no, banner attivo, configurazione testata con `sshd -t`
- [ ] `unattended-upgrades` installato e configurato per sicurezza
- [ ] `apt-mark hold nginx` testato (nginx bloccato da upgrade)
- [ ] Servizio custom `lab-startup-check.service` creato, abilitato, funzionante
- [ ] Override auto-restart su sshd configurato con `systemctl edit`
- [ ] `journalctl` query avanzate eseguite (errori, servizi, timeframe)
- [ ] `logrotate` configurato per `/var/log/lab-app.log`
- [ ] Journal retention configurata (max 500MB, 30 giorni)
- [ ] `disk-alert.sh` creato, testato, pianificato con cron ogni 15 minuti
- [ ] 3 utenti (mario.rossi, anna.bianchi, luca.ferrari) creati con gruppi e privilegi corretti
- [ ] Audit sicurezza: solo root ha UID 0, file world-writable noti identificati

### Governance (Part C)
- [ ] SOP-LNX-001 creata in `/opt/lab-scripts/SOPs/`
- [ ] Script `monthly_linux_health_report.sh` eseguito con successo
- [ ] Report HTML generato in `/var/log/lab-reports/`
- [ ] Sai mappare almeno 5 attività Linux alle corrispondenti pratiche ITIL v4

---

## Appendice A: Comandi Linux — Riferimento Rapido

### Gestione Pacchetti (apt)
```bash
apt update                          # Aggiorna indice repository
apt upgrade -y                      # Aggiorna tutti i pacchetti
apt install pacchetto -y            # Installa
apt remove pacchetto                # Rimuovi (lascia config)
apt purge pacchetto                 # Rimuovi + config
apt autoremove -y                   # Rimuovi orfani
apt list --installed | grep nginx   # Cerca pacchetto installato
apt-cache show nginx                # Info su un pacchetto
dpkg -l | grep nginx                # Stato installazione
apt-mark hold nginx                 # Blocca versione
apt-mark unhold nginx               # Sblocca versione
```

### systemd
```bash
systemctl start|stop|restart svc   # Gestione base
systemctl enable|disable svc       # Avvio automatico
systemctl status svc               # Stato + log recenti
systemctl --failed                  # Servizi in errore
systemctl list-units --type=service # Lista servizi
systemctl daemon-reload             # Ricarica config unit
systemctl edit svc                  # Override config servizio
systemd-analyze blame               # Boot timing
```

### journalctl
```bash
journalctl -f                       # Log in real-time
journalctl -b                       # Boot corrente
journalctl -b -1                    # Boot precedente
journalctl -u nginx                 # Log di un servizio
journalctl -p err                   # Solo errori
journalctl --since "2h ago"         # Ultimi 2 ore
journalctl --disk-usage             # Spazio journal
journalctl --vacuum-size=500M       # Riduci a 500MB
journalctl -o json                  # Output JSON
```

### Filesystem e Disco
```bash
df -hT                              # Spazio + tipo filesystem
df -ih                              # Uso inode
du -sh /var/*                       # Dimensione directory
find / -size +1G -type f 2>/dev/null # File > 1GB
ncdu /var                           # Explorer interattivo
lsblk                               # Struttura disco
fdisk -l                            # Partizioni
```

### Utenti e Permessi
```bash
id utente                           # UID, GID, gruppi
groups utente                       # Gruppi dell'utente
who | w                             # Chi è loggato
last                                # Storico login
useradd -m -s /bin/bash utente     # Crea utente
passwd utente                       # Cambia password
usermod -aG gruppo utente           # Aggiungi a gruppo
usermod -L utente                   # Blocca account
chown user:group file               # Cambia proprietario
chmod 640 file                      # Imposta permessi
```

---

## Appendice B: File di Configurazione Critici

| File | Scopo | Quando Modificare |
|---|---|---|
| `/etc/ssh/sshd_config` | Configurazione server SSH | Hardening, porte, autenticazione |
| `/etc/sysctl.conf` o `/etc/sysctl.d/` | Parametri kernel | Performance tuning, sicurezza rete |
| `/etc/sudoers` (via `visudo`) | Permessi sudo | Aggiungere/rimuovere privilegi |
| `/etc/crontab` o `crontab -e` | Task schedulati | Automazione operativa |
| `/etc/logrotate.d/` | Rotazione log per applicazione | Prevenire disco pieno |
| `/etc/systemd/journald.conf.d/` | Retention journal | Limitare spazio journal |
| `/etc/apt/apt.conf.d/` | Comportamento apt | Aggiornamenti automatici |
| `/etc/netplan/` | Configurazione rete | IP statici, bond, VLAN |
| `/etc/hosts` | Risoluzione nomi locale | Lab senza DNS |

---

## Appendice C: Troubleshooting Rapido — Problemi Comuni Linux

### "Il server non risponde via SSH"

```bash
# Da un'altra VM o dalla console VirtualBox:
# 1. Verifica che il processo SSH sia attivo
ps aux | grep sshd

# 2. Verifica che la porta 22 sia in ascolto
ss -tlnp | grep :22

# 3. Verifica il log SSH per errori di configurazione
journalctl -u sshd -n 50

# 4. Testa la configurazione SSH (deve fare exit 0)
sudo sshd -t

# 5. Riavvia il servizio
sudo systemctl restart sshd
```

### "Il disco è pieno"

```bash
# Trova i responsabili
du -sh /var/log/* | sort -rh | head -5    # Log troppo grandi
du -sh /var/cache/apt/archives/            # Cache apt non pulita
find /tmp -mtime +7 -type f -delete       # File temporanei vecchi
journalctl --vacuum-size=100M             # Riduce journal a 100MB
sudo apt clean                            # Pulisce cache apt
```

### "Un servizio va in loop di crash"

```bash
# Visualizza i log del crash
journalctl -u nome-servizio -n 100 --no-pager

# Controlla quante volte è ripartito
systemctl show nome-servizio | grep NRestarts

# Se ha raggiunto il limite di restart, reset e riparti
sudo systemctl reset-failed nome-servizio
sudo systemctl start nome-servizio

# Analizza la causa
journalctl -u nome-servizio --since "10 minutes ago" -p err
```

### "Processore al 100% — chi è il responsabile?"

```bash
# Top 5 processi per CPU
ps aux --sort=-%cpu | head -6

# In tempo reale (interattivo)
htop

# Nome del processo per PID
cat /proc/PID/cmdline | tr '\0' ' '
```

---

## Riferimenti

| Risorsa | Posizione | Contenuto |
|---|---|---|
| Documento sorgente | `../03-gestione-sistemi-operativi.md` (sez. Linux) | Gestione Linux Server |
| Ubuntu Server Guide | ubuntu.com/server/docs | Documentazione ufficiale Ubuntu |
| systemd man pages | `man systemctl`, `man journalctl` | Reference completo |
| FHS (Filesystem Hierarchy) | refspecs.linuxfoundation.org | Standard struttura filesystem |
| Tutorial ops03a | `tutorial_ops03_ch1a_windows_server_ops_lab.md` | Windows Server Ops (parallel) |
| Tutorial ops04a | `tutorial_ops04_ch1a_dns_dhcp_ntp_lab.md` | Servizi infrastruttura (next) |

---

*Fine tutorial ops03b — Prossimo: `tutorial_ops04_ch1a_dns_dhcp_ntp_lab.md`*
