# Tutorial Linux 22 — Troubleshooting: dmesg, journalctl, strace, tcpdump

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** metodologia diagnostica, tool avanzati, debug rete, boot issues, performance
> **Prerequisiti:** tutti i tutorial precedenti (02-21)
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
Troubleshooting Linux
│
├── Metodologia
│   ├── 1. Riproduci il problema
│   ├── 2. Isola il componente
│   ├── 3. Raccoglie dati
│   └── 4. Valida la soluzione
│
├── Sistema
│   ├── dmesg — kernel ring buffer
│   ├── journalctl — log systemd
│   └── /var/log/ — log tradizionali
│
├── Processi
│   ├── top/htop — risorse in tempo reale
│   ├── strace — syscall tracing
│   └── lsof — file/socket aperti
│
├── Rete
│   ├── tcpdump — cattura pacchetti
│   ├── netstat/ss — connessioni
│   └── traceroute/mtr — percorso
│
├── Disco e I/O
│   ├── iostat — statistiche I/O
│   ├── iotop — processi I/O
│   └── smartctl — salute disco
│
└── Boot
    ├── GRUB debug
    ├── systemd-analyze blame
    └── Emergency/rescue mode
```

---

# Parte A — Metodologia diagnostica

---

## A1. Framework sistematico

```bash
# USE Method (Brendan Gregg):
# U = Utilization (quanto è occupata la risorsa?)
# S = Saturation (ha lavoro in coda?)
# E = Errors (ci sono errori?)

# Per ogni risorsa: CPU, RAM, Disco, Rete, Bus

# 1. CPU
# U: top / mpstat
# S: vmstat -procs (colonna r > num CPU)
# E: dmesg | grep -i MCE   # Machine Check Exception

# 2. RAM
# U: free -h   (colonna used)
# S: vmstat -memory (si=so > 0 = swap attivo)
# E: dmesg | grep -i "out of memory\|oom"

# 3. Disco
# U: iostat -x (colonna %util)
# S: iostat -x (colonna avgqu-sz > 1 = saturo)
# E: dmesg | grep -i "I/O error\|ata\|disk"

# 4. Rete
# U: sar -n DEV   (rxkB/s txkB/s)
# S: ss -t state syn-recv | wc -l   (SYN backlog)
# E: ip -s link show eth0   (errori TX/RX)
```

> **Analogia:** Il troubleshooting sistemico è come la diagnosi medica. Non iniziare a trattare il primo sintomo che vedi — prima misura (dati vitali), poi isola il sistema interessato (quale organo/componente?), poi verifica ipotesi con test mirati. Un buon sysadmin diagnostica come un medico: sistemicamente, con dati, non per istinto.

---

# Parte B — Debug sistema

---

## B1. dmesg per problemi hardware e kernel

```bash
# Visualizza tutti i messaggi kernel
dmesg
dmesg -H               # human-readable con timestamp relativo
dmesg -T               # timestamp assoluto
dmesg --follow         # segui in tempo reale

# Filtra per severità
dmesg -l err           # solo errori
dmesg -l warn          # warning e superiori
dmesg -l err,crit,alert,emerg   # critico

# Pattern comuni problemi

# OOM Killer
dmesg | grep -i "out of memory\|killed process\|oom"
# → Increase RAM, aggiunge swap, profila memory usage

# Errori disco
dmesg | grep -i "ata[0-9]\|hd[a-z]\|sd[a-z]\|nvme\|i/o error\|sense key"
# → Controlla S.M.A.R.T., verifica filesystem

# Errori rete
dmesg | grep -i "link is not ready\|carrier lost\|reset adapter"
# → Controlla cavo, driver, configurazione

# Errori USB
dmesg | grep -i "usb\|device descriptor"

# MCE (Machine Check Exception) = errore hardware
dmesg | grep -i "MCE\|machine check"
# → Possibile errore CPU/RAM/Scheda madre

# Moduli
dmesg | grep "module\|driver\|loaded"
```

---

## B2. journalctl per diagnostica avanzata

```bash
# Log di avvio
journalctl -b              # boot corrente
journalctl -b -1           # boot precedente
journalctl --list-boots    # lista boot (con crash evidenti)

# Crash investigation
journalctl -b -1 -p err   # errori nell'ultimo boot (se è crashato)
journalctl -b -1 --since "10 minutes ago" -p emerg,alert,crit,err

# Correlazione temporale
# "Cosa succedeva alle 14:23:45 quando l'app è crashata?"
journalctl --since "14:23:40" --until "14:24:00"

# Kernel + specifico servizio nello stesso log
journalctl -k -u nginx --since today

# Cerca pattern
journalctl -g "connection refused" --since today
journalctl -g "error|fail|critical" -u postgresql

# Conta errori per servizio
journalctl -p err --since today | \
    grep -oP '_SYSTEMD_UNIT=\K[^ ]*' | sort | uniq -c | sort -rn

# Export per analisi
journalctl --since "2024-01-15" --until "2024-01-16" -o json \
    > /tmp/log-analisi.json
```

---

# Parte C — Debug rete

---

## C1. tcpdump avanzato

```bash
# Cattura su interfaccia con filtro
tcpdump -i eth0 -n -v host 10.0.0.5 and port 443

# Salva su file e analizza con Wireshark
tcpdump -i eth0 -w /tmp/capture.pcap -G 300 -W 12  # 12 file da 5 min
# Leggi con wireshark su desktop, o:
tcpdump -r /tmp/capture.pcap -n

# Problemi HTTP: vedi headers
tcpdump -A -i eth0 'port 80 and (tcp-data-offset) > 0' 2>/dev/null | grep -E "^(GET|POST|HTTP)"

# Connessioni TCP che non si chiudono (TIME_WAIT)
tcpdump -i eth0 'tcp[tcpflags] & (tcp-fin|tcp-rst) != 0'

# Solo SYN (nuove connessioni)
tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack = 0'

# Latenza alta: vedi RTT
tcpdump -i eth0 -tttt host 10.0.0.5

# Traffico DNS
tcpdump -i eth0 udp port 53 -v

# Problemi ICMP
tcpdump -i eth0 icmp -v
# ICMP type 3 = destination unreachable
# code 0 = net unreachable
# code 1 = host unreachable
# code 3 = port unreachable
```

---

## C2. Diagnostica connettività sistematica

```bash
# Script di diagnosi rete
diagnosi_rete() {
    local TARGET="${1:-8.8.8.8}"
    echo "=== Diagnosi rete verso $TARGET ==="

    echo "1. Interfacce:"
    ip link show | grep "state UP"

    echo "2. Indirizzi IP:"
    ip addr show | grep "inet " | grep -v "127.0.0.1"

    echo "3. Default gateway:"
    ip route show default

    echo "4. Ping gateway:"
    GW=$(ip route | grep default | awk '{print $3}')
    ping -c 2 -W 2 "$GW" && echo "OK" || echo "FALLITO"

    echo "5. Ping target:"
    ping -c 2 -W 2 "$TARGET" && echo "OK" || echo "FALLITO"

    echo "6. DNS:"
    cat /etc/resolv.conf | grep nameserver
    dig +short +timeout=3 google.com && echo "DNS OK" || echo "DNS FALLITO"

    echo "7. Traceroute:"
    traceroute -m 10 "$TARGET" 2>/dev/null | head -12

    echo "=== Fine diagnosi ==="
}

diagnosi_rete 8.8.8.8
```

---

# Parte D — Boot e recovery

---

## D1. Debug boot lento

```bash
# Analisi tempo avvio
systemd-analyze                   # tempo totale
systemd-analyze blame | head -20  # servizi più lenti
systemd-analyze critical-chain    # catena critica

# Grafico SVG
systemd-analyze plot > /tmp/boot.svg
# Apri con browser: file:///tmp/boot.svg

# Identifica servizi bloccati
systemctl list-units --state=failed
journalctl -b | grep "Timeout\|time-out\|failed\|error"

# Bypassa servizi lenti (debug)
systemctl mask NetworkManager-wait-online.service  # spesso causa 30s di attesa
# ATTENZIONE: riabilita dopo il debug
systemctl unmask NetworkManager-wait-online.service
```

---

## D2. Recovery mode

```bash
# Accedi a GRUB menu all'avvio (Shift o Esc)
# Seleziona: "Advanced options" → "Recovery mode"
# oppure: modifica kernel params, aggiungi "single" o "init=/bin/bash"

# Emergency mode (problema più grave)
# Aggiungi a kernel cmdline: systemd.unit=emergency.target

# In rescue mode
mount -o remount,rw /    # monta root in scrittura
# Ora puoi:
# - riparare fstab
# - cambiare password root
# - riparare grub
# - controllare filesystem

# Ripara filesystem corrotto
# Prima trova il disco root
lsblk
# Smonta se montato (non sempre possibile da root FS)
# Usa live USB se root FS è corrotto

# Fsck
e2fsck -f /dev/sda1    # forza check su ext4
xfs_repair /dev/sda2   # XFS

# Ripara GRUB (da live USB)
mount /dev/sda3 /mnt
mount --bind /dev /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
chroot /mnt
grub-install /dev/sda
update-grub
exit
umount /mnt/{dev,proc,sys}
umount /mnt
reboot
```

---

# Parte E — Checklist troubleshooting

## Processo sistematico

```bash
# 1. RACCOGLIE INFORMAZIONI
uptime && free -h && df -h && ip addr show

# 2. LOG RECENTI
dmesg -T | tail -50
journalctl --since "1 hour ago" -p err

# 3. PROCESSI
ps aux --sort=-%cpu | head -20
ps aux --sort=-%mem | head -20

# 4. CONNESSIONI DI RETE
ss -tulpn     # porte in ascolto
ss -tnp       # connessioni stabilite

# 5. DISCO
df -h         # spazio
iostat -x 1 3 # I/O wait

# 6. LOG APPLICAZIONE SPECIFICA
journalctl -u nome-servizio -n 100 --since "1 hour ago"

# 7. PERMESSI
ls -la /percorso/problematico

# 8. CONFIGURAZIONE
nginx -t      # verifica configurazione
systemctl cat nome-servizio  # vedi unit file
```

## Quick diagnostic script

```bash
#!/usr/bin/env bash
# quick-health.sh — report rapido stato sistema
echo "=== SISTEMA $(hostname) - $(date) ==="
echo "Uptime: $(uptime -p)"
echo "--- CPU ---"
top -bn1 | grep "Cpu(s)"
echo "--- MEMORIA ---"
free -h | grep Mem
echo "--- DISCO ---"
df -h | grep -v tmpfs
echo "--- PROCESSI FALLITI ---"
systemctl --failed --no-legend 2>/dev/null || echo "Nessuno"
echo "--- ULTIMI 10 ERRORI ---"
journalctl -p err --since "1 hour ago" -n 10 --no-pager 2>/dev/null
```

## Prossimi passi

- `tutorial_linux_23_bash_scripting_avanzato.md` — scripting complesso
- `tutorial_linux_34_hardening.md` — hardening avanzato
