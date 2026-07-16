# Tutorial Linux 07 — Kernel: Moduli, sysctl, /proc, /sys, Parametri Boot

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** moduli kernel, sysctl, /proc/sys, cgroups, kernel parameters, dmesg
> **Prerequisiti:** `tutorial_linux_04_systemd.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
Kernel Linux
│
├── Moduli (device drivers, fs, net)
│   ├── lsmod — lista moduli caricati
│   ├── modprobe — carica/scarica
│   ├── insmod/rmmod — basso livello
│   └── /etc/modules, /etc/modprobe.d/
│
├── sysctl — parametri runtime
│   ├── /proc/sys/ — filesystem virtuale
│   ├── sysctl -w — modifica runtime
│   └── /etc/sysctl.d/ — permanenti
│
├── /proc — interfaccia kernel
│   ├── /proc/cpuinfo, /proc/meminfo
│   ├── /proc/[PID]/ — info processo
│   └── /proc/net/ — stack rete
│
├── /sys — sysfs
│   ├── /sys/block/ — block devices
│   ├── /sys/class/ — classi device
│   └── /sys/kernel/ — parametri kernel
│
├── cgroups v2
│   ├── CPU, Memory, IO limits
│   └── systemd slice/scope
│
└── Boot parameters (GRUB)
    ├── /etc/default/grub
    └── CMDLINE_LINUX
```

---

# Parte A — Moduli kernel

---

## A1. Gestione moduli

```bash
# Lista moduli caricati
lsmod
# Module                  Size  Used by
# dm_crypt               53248  1
# dm_mod                139264  9 dm_crypt

# Informazioni su un modulo
modinfo ext4              # dettagli modulo
modinfo -F depends ext4   # solo dipendenze
modinfo -F author nvme    # autore

# Carica modulo
modprobe nvme             # carica con dipendenze
modprobe -v br_netfilter  # verbose

# Scarica modulo
modprobe -r noveau        # rimuovi + dipendenze non usate
rmmod e1000               # forza rimozione (no dipendenze)

# Blacklist modulo — impedisce caricamento automatico
cat > /etc/modprobe.d/blacklist-noveau.conf << 'EOF'
# Disabilita driver open-source Nvidia (usa proprietario)
blacklist nouveau
options nouveau modeset=0
EOF
update-initramfs -u

# Opzioni modulo — parametri permanenti
cat > /etc/modprobe.d/kvm.conf << 'EOF'
options kvm_intel nested=1
options kvm_amd nested=1
EOF

# Carica moduli all'avvio
echo "br_netfilter" >> /etc/modules
echo "overlay" >> /etc/modules

# Oppure con file dedicato
cat > /etc/modules-load.d/containerd.conf << 'EOF'
overlay
br_netfilter
EOF

# Verifica
modprobe overlay && lsmod | grep overlay
```

> **Analogia:** I moduli kernel sono come le app dello smartphone: il kernel è il sistema operativo base, i moduli aggiungono funzionalità (driver WiFi, filesystem, protocolli di rete) senza doverli inclusi nel kernel stesso. `modprobe` è l'App Store — scarica il modulo richiesto e tutte le sue dipendenze. `blacklist` equivale a bloccare un'app dal presentarsi nell'elenco.

---

## A2. Compilare modulo kernel (esempio)

```bash
# Esempio: modulo "hello world"
# /tmp/hello_mod/hello.c
cat > /tmp/hello_mod/hello.c << 'EOF'
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Admin");
MODULE_DESCRIPTION("Modulo di test");

static int __init hello_init(void) {
    printk(KERN_INFO "Hello kernel!\n");
    return 0;
}

static void __exit hello_exit(void) {
    printk(KERN_INFO "Goodbye kernel!\n");
}

module_init(hello_init);
module_exit(hello_exit);
EOF

cat > /tmp/hello_mod/Makefile << 'EOF'
obj-m += hello.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
EOF

# Build
cd /tmp/hello_mod
apt install linux-headers-$(uname -r)
make

# Carica
insmod hello.ko
dmesg | tail -3    # "Hello kernel!"

# Scarica
rmmod hello
dmesg | tail -3    # "Goodbye kernel!"
```

---

# Parte B — sysctl: parametri kernel runtime

---

## B1. Parametri di sistema

```bash
# Lista tutti i parametri
sysctl -a
sysctl -a 2>/dev/null | grep net.core

# Leggi singolo parametro
sysctl net.ipv4.ip_forward
sysctl vm.swappiness

# Modifica runtime (non persiste al reboot)
sysctl -w net.ipv4.ip_forward=1
sysctl -w vm.swappiness=10

# Applica da file
sysctl -p                          # /etc/sysctl.conf
sysctl -p /etc/sysctl.d/mio.conf

# Parametri permanenti
cat > /etc/sysctl.d/99-produzione.conf << 'EOF'
# ==========================================
# Performance rete
# ==========================================
# Buffer socket
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 16777216
net.core.wmem_default = 16777216

# Buffer TCP
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728

# Backlog connessioni (evita drop sotto carico)
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# TIME_WAIT — riutilizza connessioni chiuse
net.ipv4.tcp_tw_reuse = 1

# ==========================================
# Sicurezza rete
# ==========================================
# Blocca IP spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Blocca ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Blocca source routing
net.ipv4.conf.all.accept_source_route = 0

# Abilita routing (SOLO se questo host è un router)
# net.ipv4.ip_forward = 1

# ==========================================
# Memoria e performance
# ==========================================
# Meno aggressivo nello swapping (0-100)
# 10 = swap solo se RAM <10%
vm.swappiness = 10

# Dirty pages — quando flusso su disco
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File inotify (per strumenti come watchdog, editors)
fs.inotify.max_user_watches = 524288

# File descriptor massimi
fs.file-max = 2097152
EOF

# Applica immediatamente
sysctl -p /etc/sysctl.d/99-produzione.conf
```

---

## B2. Parametri specifici per container (Kubernetes/Docker)

```bash
cat > /etc/sysctl.d/99-kubernetes.conf << 'EOF'
# Richiesto da Kubernetes
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1

# Memoria hugepages per database (opzionale)
vm.nr_hugepages = 512
EOF

# Richiede modulo br_netfilter
modprobe br_netfilter
sysctl -p /etc/sysctl.d/99-kubernetes.conf
```

---

# Parte C — /proc e /sys

---

## C1. /proc: vista sul kernel

```bash
# CPU
cat /proc/cpuinfo
cat /proc/cpuinfo | grep "model name" | uniq
nproc                         # numero CPU logiche

# RAM
cat /proc/meminfo
free -h                       # versione human-readable

# Uptime
cat /proc/uptime
uptime                        # human-readable

# Processi in esecuzione
ls /proc/ | grep '^[0-9]'     # PID di ogni processo
ls /proc/1234/                # dettagli processo 1234
cat /proc/1234/cmdline        # riga di comando
cat /proc/1234/status         # stato (PID, PPID, UID, GID, memoria...)
cat /proc/1234/fd/ | wc -l    # numero file descriptor aperti
cat /proc/1234/net/tcp        # connessioni TCP del processo

# Stack rete
cat /proc/net/dev              # statistiche interfacce
cat /proc/net/tcp              # connessioni TCP (hex)
cat /proc/net/route            # tabella routing

# Parametri kernel via /proc/sys
# Equivalente a sysctl
cat /proc/sys/net/ipv4/ip_forward
echo 1 > /proc/sys/net/ipv4/ip_forward   # modifica (come sysctl -w)
```

---

## C2. dmesg: log del kernel

```bash
# Messaggi kernel all'avvio e runtime
dmesg                          # tutto
dmesg -H                       # human-readable con timestamp relativo
dmesg -T                       # timestamp assoluto
dmesg -l err                   # solo errori
dmesg -l warn                  # warning
dmesg -f kern                  # solo kernel
dmesg --follow                 # come tail -f
dmesg -C                       # clear ring buffer

# Filtra messaggi comuni
dmesg | grep -i "error\|fail\|warn"
dmesg | grep -i "ssd\|nvme\|sata"     # problemi disco
dmesg | grep -i "oom"                  # Out of Memory killer

# OOM killer — quando Linux uccide processi per RAM
# Log tipico:
# [ 1234.567] Out of memory: Kill process 5678 (python3) score 850
# Soluzione: aumenta RAM, aggiungi swap, riduci vm.swappiness

# Log kernel in tempo reale
journalctl -k -f               # journal kernel messages
```

---

# Parte D — Parametri boot GRUB

---

## D1. Configurazione GRUB

```bash
# File principale
cat /etc/default/grub
# GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"  # parametri default
# GRUB_CMDLINE_LINUX=""                      # parametri aggiuntivi

# Parametri utili
# quiet             → meno messaggi boot
# splash            → schermata grafica
# nomodeset         → disabilita kernel mode setting (fix video)
# mem=4G            → limita RAM
# console=ttyS0,115200 → output seriale
# intel_iommu=on    → IOMMU (virtualizzazione GPU passthrough)
# nmi_watchdog=0    → disabilita watchdog (VPS che riavvia)
# transparent_hugepage=never → per database (Redis, MongoDB)

# Modifica e ricompila
nano /etc/default/grub
# Aggiungi: GRUB_CMDLINE_LINUX_DEFAULT="quiet transparent_hugepage=never"
update-grub           # Debian/Ubuntu
grub2-mkconfig -o /boot/grub2/grub.cfg  # RHEL

# Verifica parametri attuali
cat /proc/cmdline

# Kernel in uso
uname -r              # versione kernel
uname -a              # tutte le info

# Kernel disponibili
ls /boot/vmlinuz*
dpkg --list | grep linux-image   # Debian
rpm -qa kernel                   # RHEL
```

---

# Parte E — Riepilogo

## sysctl più usati

| Parametro | Valore consigliato | Scopo |
|---|---|---|
| `vm.swappiness` | 10 | Meno swap, più RAM |
| `net.core.somaxconn` | 65535 | Più connessioni in coda |
| `net.ipv4.ip_forward` | 1 | Router/container |
| `fs.inotify.max_user_watches` | 524288 | File watcher (dev tools) |
| `net.ipv4.tcp_tw_reuse` | 1 | Riusa porte TIME_WAIT |

## Workflow debugging kernel

```bash
# 1. Controlla messaggi recenti
dmesg -T | tail -50
journalctl -k --since "1 hour ago"

# 2. Controlla se ci sono errori hardware
dmesg | grep -i "error\|fail\|bug"

# 3. OOM killer all'opera?
journalctl | grep -i "oom\|killed process"

# 4. Moduli problematici?
lsmod
dmesg | grep -i "module\|driver"
```

## Prossimi passi

- `tutorial_linux_08_performance.md` — top/htop, vmstat, iostat
- `tutorial_linux_09_gestione_processi.md` — ps, strace, lsof
