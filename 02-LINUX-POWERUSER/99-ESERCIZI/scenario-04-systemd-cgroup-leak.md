# Scenario 04 — Diagnosi Leak di Processi via cgroup systemd

> **Modulo di riferimento:** [04-systemd.md](../04-systemd.md), [09-gestione-processi.md](../09-gestione-processi.md)
> **Tempo stimato:** 1-1.5 ore
> **Livello:** proficient
> **Prerequisiti:** VM Debian 12, completamento moduli 04, 09, 08, 13
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

Il monitoring segnala che un server ha un numero crescente di processi zombie e task in cgroup orphaned. La memoria del sistema cresce lentamente nonostante nessun servizio mostri leak evidenti. Il tuo compito è:

1. Identificare i processi che fuoriescono dal controllo cgroup
2. Diagnosticare la causa
3. Contenere il problema
4. Applicare la correzione permanente

---

## Setup Lab (15 min)

### Creare il servizio che causa il leak

```bash
# Script che simula un servizio con leak di processi figli
cat > /usr/local/bin/leaky-service.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "[leaky] PID $$ starting"

cleanup() {
    echo "[leaky] Caught signal, exiting"
    exit 0
}
trap cleanup SIGTERM SIGINT

while true; do
    # Lancia un worker che a sua volta lancia sottoprocessi
    (
        sleep $((RANDOM % 10 + 5)) &
        # Il sottoprocesso diventa orphan quando il subshell esce
        nohup sleep 3600 > /dev/null 2>&1 &
        echo "[leaky] Spawned orphan worker PID $!"
    )
    sleep 2
done
SCRIPT_EOF
chmod 755 /usr/local/bin/leaky-service.sh

# Unit systemd (volutamente senza hardening)
cat > /etc/systemd/system/leaky-service.service << 'EOF'
[Unit]
Description=Leaky Service (lab scenario)
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/leaky-service.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start leaky-service

# Lasciare il servizio in esecuzione per 2-3 minuti
sleep 120
```

---

## Fase 1 — Rilevamento (15 min)

### 1.1 Osservare i sintomi

```bash
# Contare i processi totali
ps aux | wc -l

# Cercare processi sleep anomali
ps aux | grep "sleep 3600" | grep -v grep

# Contare processi orfani
ps aux | grep "sleep 3600" | grep -v grep | wc -l

# Verificare la crescita nel tempo
watch -n 5 'ps aux | grep "sleep 3600" | grep -v grep | wc -l'
```

### 1.2 Analisi cgroup

```bash
# Verificare i task nel cgroup del servizio
systemctl status leaky-service.service
# Cercare "Tasks:" — il numero dovrebbe essere >1 e crescente

# Dettaglio cgroup
systemd-cgls -u leaky-service.service

# Processi fuori dal cgroup del servizio
# I processi nohup-pati potrebbero essere migrati altrove
systemd-cgls /

# Cercare processi "sleep 3600" e il loro cgroup
for pid in $(pgrep -f "sleep 3600"); do
    echo "PID $pid → $(cat /proc/$pid/cgroup 2>/dev/null)"
done
```

### 1.3 Analisi con strumenti avanzati

```bash
# Albero dei processi
ps axjf | grep -B 2 "sleep 3600" | head -30

# Verificare PPID (parent PID)
# Se PPID = 1, il processo è stato adottato da init → orphan
ps -o pid,ppid,stat,comm -p $(pgrep -f "sleep 3600") | head -20

# Memoria consumata dagli orfani
ps -o pid,rss,comm -p $(pgrep -f "sleep 3600") | awk '{sum+=$2} END {print "Total RSS: " sum/1024 " MB"}'
```

---

## Fase 2 — Diagnosi Causa Root (15 min)

### 2.1 Analizzare il codice del servizio

```bash
# Leggere lo script
cat /usr/local/bin/leaky-service.sh

# Problemi identificati:
# 1. `nohup sleep 3600 &` → il processo sopravvive alla morte del parent
# 2. Nessun PID tracking dei figli
# 3. Nessun signal handler per SIGTERM ai figli
# 4. `KillMode=` non configurato nella unit
```

### 2.2 Verificare il KillMode

```bash
# Verificare come systemd termina il servizio
systemctl show leaky-service.service -p KillMode
# Default: KillMode=control-group (dovrebbe funzionare)

# Ma il problema è che nohup + disown + background
# possono far migrare il processo fuori dal cgroup originale
# se non c'è Delegate=yes e il processo fa setsid()
```

### 2.3 Test: fermare e riavviare il servizio

```bash
# Contare orfani prima
echo "Orphans prima: $(pgrep -f 'sleep 3600' | wc -l)"

# Fermare il servizio
systemctl stop leaky-service.service

# Contare orfani dopo
echo "Orphans dopo stop: $(pgrep -f 'sleep 3600' | wc -l)"

# Se il numero non diminuisce, i processi sono già fuori dal cgroup
```

---

## Fase 3 — Contenimento (10 min)

### 3.1 Terminare gli orfani

```bash
# Terminare tutti i processi sleep 3600
pkill -f "sleep 3600"

# Verificare
sleep 2
pgrep -f "sleep 3600" | wc -l
# Deve essere 0

# Se qualcuno resiste:
pkill -9 -f "sleep 3600"
```

### 3.2 Verificare la memoria recuperata

```bash
# Controllare memoria prima/dopo
free -h
```

---

## Fase 4 — Correzione Permanente (20 min)

### 4.1 Hardening della unit systemd

```bash
cat > /etc/systemd/system/leaky-service.service << 'EOF'
[Unit]
Description=Leaky Service (hardened)
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/leaky-service.sh
Restart=on-failure
RestartSec=5s

# === Correzione leak ===
# Terminare TUTTI i processi nel cgroup, non solo il main PID
KillMode=control-group
KillSignal=SIGTERM
TimeoutStopSec=30

# Limitare il numero di task
TasksMax=20

# Impedire la creazione di nuovi namespace (previene escape dal cgroup)
RestrictNamespaces=yes

# Limitare risorse
MemoryMax=256M
CPUQuota=50%

# Hardening addizionale
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
```

### 4.2 Correggere lo script

```bash
cat > /usr/local/bin/leaky-service-fixed.sh << 'SCRIPT_EOF'
#!/bin/bash
set -euo pipefail

PIDS=()

cleanup() {
    echo "[leaky-fixed] Cleaning up ${#PIDS[@]} children"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait
    echo "[leaky-fixed] Cleanup complete"
    exit 0
}

trap cleanup SIGTERM SIGINT EXIT

echo "[leaky-fixed] PID $$ starting"

while true; do
    # Lanciare worker tracciando il PID
    sleep $((RANDOM % 10 + 5)) &
    PIDS+=($!)

    # Rimuovere PID terminati dall'array
    local_pids=()
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            local_pids+=("$pid")
        fi
    done
    PIDS=("${local_pids[@]}")

    echo "[leaky-fixed] Active children: ${#PIDS[@]}"
    sleep 2
done
SCRIPT_EOF
chmod 755 /usr/local/bin/leaky-service-fixed.sh
```

### 4.3 Aggiornare e testare

```bash
# Aggiornare ExecStart
sed -i 's|leaky-service.sh|leaky-service-fixed.sh|' \
    /etc/systemd/system/leaky-service.service

systemctl daemon-reload
systemctl restart leaky-service

# Monitorare per 2 minuti
watch -n 5 'systemctl status leaky-service.service | grep Tasks; echo "---"; pgrep -cf "sleep"'

# Verificare che Tasks non cresca indefinitamente
# e che stop termini tutti i figli
systemctl stop leaky-service

sleep 2
echo "Orphans residui: $(pgrep -f 'sleep 3600' 2>/dev/null | wc -l)"
# Deve essere 0
```

---

## Fase 5 — Monitoring Preventivo (10 min)

### 5.1 Alert su task count

```bash
# Se Prometheus è installato, aggiungere alert:
cat >> /etc/prometheus/rules/alerts.yml << 'EOF'

  - name: cgroup_alerts
    rules:
      - alert: HighTaskCount
        expr: node_systemd_unit_tasks_current > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alto numero di task in {{ $labels.name }}"
          description: "{{ $labels.name }} ha {{ $value }} task attivi."
EOF
```

### 5.2 Script di monitoraggio manuale

```bash
cat > /usr/local/sbin/check-orphan-tasks.sh << 'CHECK_EOF'
#!/bin/bash
# Trova processi il cui PPID è 1 (orfani adottati da init)
# escludendo processi di sistema noti

THRESHOLD=50
ORPHANS=$(ps -eo ppid,pid,comm | awk '$1 == 1 {count++} END {print count}')

if [ "$ORPHANS" -gt "$THRESHOLD" ]; then
    echo "WARNING: $ORPHANS orphan processes detected (threshold: $THRESHOLD)"
    echo "Top orphan processes:"
    ps -eo ppid,pid,rss,comm | awk '$1 == 1' | sort -k3 -rn | head -10
    exit 1
fi
echo "OK: $ORPHANS orphan processes"
CHECK_EOF
chmod 755 /usr/local/sbin/check-orphan-tasks.sh
```

---

## Criteri di Completamento

- [ ] Leak riprodotto e osservato (processi crescenti)
- [ ] Causa root identificata (nohup/background senza tracking)
- [ ] Orfani terminati con successo
- [ ] Unit hardened con TasksMax, KillMode=control-group
- [ ] Script corretto con trap e PID tracking
- [ ] Stop del servizio termina tutti i figli
- [ ] Monitoring configurato per prevenire recidive

---

## Riferimenti

- systemd.resource-control(5) — `man systemd.resource-control` (consultato: 2026-05-23)
- systemd.kill(5) — `man systemd.kill` (consultato: 2026-05-23)
- [04-systemd.md](../04-systemd.md)
- [09-gestione-processi.md](../09-gestione-processi.md)
- [23-bash-scripting-progetti-avanzati.md](../23-bash-scripting-progetti-avanzati.md)
