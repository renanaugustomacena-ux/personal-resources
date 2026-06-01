# Kernel Linux — Guida Completa

> **Modulo 07** · **Aggiornamento:** 2026-05-24

## Idee guida
1. **LTS kernel test matrix: 6.1 (until 2026-12), 6.6 (until 2026-12), 6.12 (until 2034-12).**
2. **DKMS per moduli RHEL/Fedora; vermagic mismatch potential.**
3. **sysctl benchmark pre/post (es. net.core.rmem_max).**
4. **Live patching: kpatch (RHEL), Ubuntu Pro Livepatch.**
5. **Cite kernel.org docs primarie.**


## Indice

- [Panoramica](#panoramica)
- [Novita del Kernel 6.x](#novita-del-kernel-6x)
  - [Rust nel Kernel](#rust-nel-kernel)
  - [io_uring — Maturita e Adozione](#io_uring--maturita-e-adozione)
  - [MGLRU — Multi-Gen LRU](#mglru--multi-gen-lru)
  - [EEVDF Scheduler](#eevdf-scheduler)
- [Architettura del Kernel Linux](#architettura-del-kernel-linux)
  - [Monolitico vs Microkernel](#monolitico-vs-microkernel)
  - [Design ibrido di Linux](#design-ibrido-di-linux)
  - [Kernel Space vs User Space](#kernel-space-vs-user-space)
  - [Componenti principali](#componenti-principali)
  - [Informazioni sul kernel](#informazioni-sul-kernel)
- [Processo di Boot](#processo-di-boot)
  - [BIOS/UEFI](#biosuefi)
  - [Bootloader GRUB2](#bootloader-grub2)
  - [Kernel e initramfs](#kernel-e-initramfs)
  - [Init system (systemd)](#init-system-systemd)
- [GRUB2 — Configurazione Avanzata](#grub2--configurazione-avanzata)
- [initramfs / initrd](#initramfs--initrd)
- [Moduli Kernel](#moduli-kernel)
- [Parametri Kernel (sysctl)](#parametri-kernel-sysctl)
  - [Gerarchia /proc/sys](#gerarchia-procsys)
  - [Parametri importanti](#parametri-importanti)
  - [Persistenza con sysctl.d](#persistenza-con-sysctld)
- [Compilazione Kernel Personalizzato](#compilazione-kernel-personalizzato)
  - [Ottimizzazione della Compilazione](#ottimizzazione-della-compilazione)
- [DKMS — Driver Management](#dkms--driver-management)
- [Gestione della Memoria](#gestione-della-memoria)
  - [Memoria virtuale](#memoria-virtuale)
  - [Page cache](#page-cache)
  - [Swap](#swap)
  - [OOM Killer](#oom-killer)
  - [Huge Pages](#huge-pages)
  - [NUMA](#numa)
- [Schedulazione dei Processi](#schedulazione-dei-processi)
  - [CFS e EEVDF](#cfs-e-eevdf)
  - [Schedulazione real-time](#schedulazione-real-time)
  - [cgroups v2](#cgroups-v2)
  - [nice, ionice, chrt](#nice-ionice-chrt)
- [I/O Scheduling](#io-scheduling)
- [Gestione Dispositivi](#gestione-dispositivi)
  - [udev](#udev)
  - [Device mapper](#device-mapper)
  - [sysfs e /dev](#sysfs-e-dev)
- [Sicurezza Kernel](#sicurezza-kernel)
  - [Capabilities](#capabilities)
  - [seccomp](#seccomp)
  - [Namespaces](#namespaces)
  - [AppArmor e SELinux](#apparmor-e-selinux)
  - [Landlock — Sandboxing Non Privilegiato](#landlock--sandboxing-non-privilegiato)
- [eBPF](#ebpf)
  - [eBPF LSM — Sicurezza Programmabile](#ebpf-lsm--sicurezza-programmabile)
  - [CO-RE — Compile Once, Run Everywhere](#co-re--compile-once-run-everywhere)
  - [Ecosistema eBPF in Produzione](#ecosistema-ebpf-in-produzione)
- [Kernel Debugging](#kernel-debugging)
  - [dmesg](#dmesg)
  - [ftrace](#ftrace)
  - [perf](#perf)
  - [kdump e crash dumps](#kdump-e-crash-dumps)
- [Kernel Live Patching](#kernel-live-patching)
  - [Workflow Creazione Patch con kpatch](#workflow-creazione-patch-con-kpatch)
- [Tuning Kernel per Performance](#tuning-kernel-per-performance)
  - [Tuning Rete ad Alta Banda (10G/25G/100G)](#tuning-rete-ad-alta-banda-10g25g100g)
  - [Checklist per workload](#checklist-per-workload)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

Il kernel Linux e il cuore del sistema operativo: gestisce hardware, processi, memoria, filesystem, rete e sicurezza. La comprensione del kernel — dalla gestione dei moduli al tuning dei parametri, dalla compilazione personalizzata alla diagnostica — e una competenza avanzata essenziale per l'amministratore di sistema. Il kernel Linux e monolitico modulare: il core e un unico binario (vmlinuz), ma funzionalita aggiuntive possono essere caricate come moduli a runtime.

Il kernel opera come intermediario tra hardware e software applicativo. Ogni applicazione in user space interagisce con l'hardware esclusivamente tramite system call, che attraversano il confine kernel/user space e invocano funzionalita del kernel. Questo modello garantisce isolamento, sicurezza e stabilita: un crash in user space non compromette il kernel (salvo bug kernel-side), e il kernel puo imporre policy di accesso su ogni risorsa.

Il kernel Linux viene rilasciato con un modello di versioning `MAJOR.MINOR.PATCH`. Le release LTS (Long Term Support) ricevono backport di sicurezza e bugfix per anni. La matrice LTS attuale:

| Versione | Fine supporto | Scheduler predefinito | Note |
|---|---|---|---|
| 6.1 | 2026-12 | CFS | Ultima LTS con CFS |
| 6.6 | 2026-12 | EEVDF | Prima LTS con EEVDF |
| 6.12 | 2034-12 | EEVDF | Super LTS |

---

## Novita del Kernel 6.x

### Rust nel Kernel

A partire dal kernel 6.1 (dicembre 2022), il supporto Rust e entrato ufficialmente nel tree del kernel Linux come infrastruttura sperimentale. Con il kernel 6.13 il codice Rust ha superato le 13.000 righe, e a dicembre 2025 Linus Torvalds ha dichiarato il supporto Rust **permanente**: non sara mai rimosso dal kernel, indipendentemente dal ritmo di adozione da parte dei maintainer dei singoli sottosistemi.

Il primo driver Rust in-tree e il binding per il framework DRM (Direct Rendering Manager), usato dal driver Nova per le GPU NVIDIA di nuova generazione. Apple ha contribuito un driver GPU per i SoC M1/M2 scritto interamente in Rust. Il vantaggio principale e la **safety a compile-time**: il borrow checker previene use-after-free, data race e buffer overflow a costo zero in runtime. Questo e particolarmente rilevante considerando che circa il 65-70% delle CVE del kernel sono errori di memoria.

L'infrastruttura Rust nel kernel include:
- **Bindings C → Rust** generati automaticamente con `bindgen`
- **Modello di ownership** che previene leak di risorse kernel (refcount, lock, allocation)
- **Trait `Module`** per definire moduli caricabili con init/exit safety-checked
- **Supporto `alloc`** con allocatore kernel (kmalloc/vmalloc) integrato
- **Compilazione con `rustc` >= 1.78** e LLVM backend condiviso con Clang

Per compilare un kernel con supporto Rust:

```bash
# Verificare toolchain
rustup component add rust-src
make LLVM=1 rustavailable        # Controlla se rustc e compatibile

# Abilitare nella configurazione
make menuconfig                  # General setup → Rust support [Y]
make LLVM=1 -j$(nproc)
```

### io_uring — Maturita e Adozione

io_uring, introdotto nel kernel 5.1, ha raggiunto piena maturita nelle versioni 6.x diventando l'interfaccia I/O asincrono di riferimento per applicazioni ad alte prestazioni. Ogni release ha aggiunto capacita significative:

| Kernel | Funzionalita | Impatto |
|--------|-------------|---------|
| 6.1 | Multi-shot accept, send/recv ZC | Riduzione syscall per server TCP |
| 6.7 | io_uring_cmd per NVMe passthrough | Bypass VFS per storage ad alte prestazioni |
| 6.13 | Ring resizing dinamico | Adattamento a runtime senza ricreare il ring |
| 6.15 | Zero-copy receive (ZC Rx) | Eliminazione copie di pacchetti in ricezione |

**Architettura a submission queue (SQ) e completion queue (CQ)**: l'applicazione inserisce richieste nella SQ tramite memory-mapped ring buffer, il kernel le processa e deposita i risultati nella CQ. Non servono syscall nel percorso critico (grazie a `IORING_SETUP_SQPOLL` che mantiene un kernel thread dedicato a consumare la SQ).

Benchmark reali mostrano:
- **2-5x throughput** rispetto a epoll + read/write per I/O su disco NVMe
- **40-60% riduzione latenza P99** per server HTTP ad alto carico
- Adozione in produzione: liburing, Tokio (Rust), io_uring backend di libuv, RocksDB, TigerBeetle

```bash
# Verificare supporto io_uring
cat /proc/config.gz | gunzip | grep CONFIG_IO_URING  # =y
# Parametri sysctl rilevanti
sysctl kernel.io_uring_disabled     # 0=tutti, 1=non-privilegiati disabilitati, 2=disabilitato
```

### MGLRU — Multi-Gen LRU

MGLRU (Multi-Generational Least Recently Used) e stato integrato nel kernel 6.1 come evoluzione del tradizionale algoritmo LRU a due liste (active/inactive) usato dal memory management del kernel. L'approccio classico soffriva di decisioni di eviction imprecise sotto pressione di memoria, causando OOM prematuri e thrashing eccessivo.

MGLRU introduce **piu generazioni** (tipicamente 4) per le pagine, ognuna con un contatore di eta. Le pagine vengono promosse a generazioni piu recenti quando accedute e demotate progressivamente quando non usate. Questo fornisce una granularita molto superiore nella decisione di quali pagine evitare.

Risultati misurati in produzione:
- **Google (ChromeOS)**: 40% riduzione CPU di kswapd, 85% riduzione OOM kill
- **Android**: 18% riduzione uccisioni di app in background sotto pressione di memoria
- **Server con database**: riduzione significativa di latenza P99 durante flush di page cache

```bash
# Verificare stato MGLRU
cat /sys/kernel/mm/lru_gen/enabled
# 0x0007 = completamente abilitato (anon + file + forza)

# Abilitare MGLRU
echo 7 > /sys/kernel/mm/lru_gen/enabled

# Parametri di tuning
cat /sys/kernel/mm/lru_gen/min_ttl_ms   # TTL minimo prima di eviction (default 0)
echo 1000 > /sys/kernel/mm/lru_gen/min_ttl_ms  # Proteggi pagine recenti per 1s
```

### EEVDF Scheduler

Il kernel 6.6 ha sostituito CFS (Completely Fair Scheduler) con **EEVDF** (Earliest Eligible Virtual Deadline First). EEVDF assegna a ogni task una deadline virtuale e seleziona sempre il task con la deadline piu vicina tra quelli eleggibili. Questo elimina la necessita degli heuristic di "sleeper fairness" di CFS e riduce la latenza di scheduling per task interattivi.

Vantaggi principali:
- Latenza piu prevedibile senza bisogno di `CONFIG_SCHED_AUTOGROUP`
- Eliminazione di starvation per task a bassa priorita con deadline ravvicinate
- Migliore risposta per workload misti (batch + interattivo)

---

## Architettura del Kernel Linux

### Monolitico vs Microkernel

Esistono due architetture fondamentali per i kernel dei sistemi operativi:

**Kernel monolitico** — Tutto il codice del kernel (scheduler, memory manager, driver, filesystem, stack di rete) esegue in un unico spazio di indirizzamento con privilegi massimi (ring 0 su x86). Vantaggi: prestazioni elevate (nessun overhead di IPC tra componenti), accesso diretto alle strutture dati condivise. Svantaggi: un bug in un driver puo corrompere l'intero kernel, superficie d'attacco piu ampia.

**Microkernel** — Solo le funzionalita minime (scheduling, IPC, gestione memoria base) risiedono nel kernel. Driver, filesystem e stack di rete eseguono come processi in user space. Esempi: Minix 3, QNX, L4. Vantaggi: isolamento dei componenti (un driver che crasha non abbatte il sistema), superficie d'attacco ridotta. Svantaggi: overhead significativo per la comunicazione tra componenti via IPC.

```
Kernel Monolitico                    Microkernel
┌────────────────────┐              ┌────────────────────┐
│     User Space     │              │     User Space     │
│  App  App  App     │              │ App  FS  Driver Net│
├────────────────────┤              ├────────────────────┤
│   Kernel Space     │              │   Kernel Space     │
│ ┌────────────────┐ │              │ ┌────────────────┐ │
│ │ Scheduler      │ │              │ │ Scheduler      │ │
│ │ Memory Mgr     │ │              │ │ IPC            │ │
│ │ VFS            │ │              │ │ Memory Mgr     │ │
│ │ Network Stack  │ │              │ └────────────────┘ │
│ │ Device Drivers │ │              │    (solo base)     │
│ │ Security (LSM) │ │              └────────────────────┘
│ └────────────────┘ │
│  (tutto in ring 0) │
└────────────────────┘
```

### Design ibrido di Linux

Linux adotta un design **monolitico modulare** (talvolta chiamato "ibrido pragmatico"). Il core e monolitico — tutto esegue in kernel space — ma il sistema di moduli caricabili (LKM, Loadable Kernel Modules) permette di estendere il kernel a runtime senza ricompilazione. I moduli condividono lo spazio di indirizzamento del kernel (non c'e isolamento come in un microkernel), ma possono essere caricati e rimossi dinamicamente.

Caratteristiche chiave:
- **Monolitico nel core**: scheduler, memory manager, VFS, network stack tutti in ring 0
- **Modulare nell'estensione**: driver, filesystem, protocolli come moduli `.ko`
- **Nessun IPC overhead**: i moduli accedono direttamente alle API interne del kernel
- **Trade-off consapevole**: un modulo buggato puo causare kernel panic, ma le prestazioni sono massime

```bash
# Verificare la natura modulare del kernel
cat /proc/modules | wc -l        # Numero moduli caricati (tipicamente 100-200)
ls /lib/modules/$(uname -r)/kernel/ | head -20
# crypto/  drivers/  fs/  lib/  net/  sound/  ...
# Ogni directory contiene moduli .ko per quel sottosistema
```

### Kernel Space vs User Space

La separazione kernel/user space e il fondamento dell'architettura di sicurezza e stabilita di Linux.

**Kernel space** (ring 0 su x86, EL1 su ARM64):
- Accesso completo a tutta la memoria fisica e ai registri hardware
- Esegue codice privilegiato (istruzioni I/O, gestione interrupt, manipolazione page table)
- Un crash qui = kernel panic, sistema fermo
- Il codice deve essere attentamente verificato

**User space** (ring 3 su x86, EL0 su ARM64):
- Memoria virtuale isolata per ogni processo
- Nessun accesso diretto all'hardware
- Comunica col kernel esclusivamente via system call (syscall)
- Un crash qui = il processo muore, il sistema continua

```
┌───────────────────────────────────────────────────┐
│                   User Space                       │
│                                                   │
│   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│   │ bash │  │nginx │  │ java │  │python│        │
│   └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘        │
│      │         │         │         │              │
│      └─────────┴────┬────┴─────────┘              │
│                     │                              │
│              ┌──────▼──────┐                       │
│              │  glibc /    │                       │
│              │  libc (C    │                       │
│              │  library)   │                       │
│              └──────┬──────┘                       │
├─────────────────────┼─────────────────────────────┤
│              syscall interface                     │
│  ────────────── ring boundary ──────────────────  │
├─────────────────────┼─────────────────────────────┤
│                Kernel Space                        │
│              ┌──────▼──────┐                       │
│              │ System Call │                       │
│              │  Dispatcher │                       │
│              └──────┬──────┘                       │
│    ┌────────┬───────┼───────┬────────┐            │
│    ▼        ▼       ▼       ▼        ▼            │
│ Scheduler  MM     VFS    NetStack  Drivers        │
└───────────────────────────────────────────────────┘
```

Le system call sono il gateway. Ogni interazione user-kernel passa attraverso una syscall:
- `open()`, `read()`, `write()`, `close()` — file I/O
- `fork()`, `execve()`, `wait()` — gestione processi
- `mmap()`, `brk()` — gestione memoria
- `socket()`, `bind()`, `connect()` — networking
- `ioctl()` — controllo dispositivi

```bash
# Contare le syscall disponibili sul sistema
ausyscall --dump 2>/dev/null | wc -l

# Tracciare le syscall di un processo
strace -c ls /tmp                  # Sommario syscall
strace -f -e trace=open,read ls    # Filtra syscall specifiche

# Verificare la protezione user/kernel
cat /proc/self/status | grep -i cap    # Capabilities del processo corrente
cat /proc/self/maps | head -20          # Mappa memoria virtuale
```

### Componenti principali

```
User Space
─────────────────────────────────
  System Call Interface (syscall)
─────────────────────────────────
Kernel Space
├── Process Scheduler          → Schedulazione CPU (CFS su ≤6.5, EEVDF su ≥6.6)
├── Memory Manager             → Paginazione, swap, OOM killer, hugepages, NUMA
├── Virtual File System (VFS)  → Astrazione filesystem (ext4, XFS, Btrfs, NFS...)
├── Network Stack              → TCP/IP, socket, netfilter, eBPF networking
├── Device Drivers             → Hardware abstraction (block, char, net devices)
├── IPC (Inter-Process Comm)   → Pipe, shared memory, semafori, socket Unix
├── Security (LSM)             → SELinux, AppArmor, seccomp, capabilities
├── Block Layer                → I/O scheduling, device mapper, RAID
├── cgroups                    → Resource control (CPU, memoria, I/O, rete)
└── Tracing/Perf               → ftrace, perf_events, eBPF, kprobes
─────────────────────────────────
  Hardware
```

### Informazioni sul kernel

```bash
uname -r                           # Versione kernel
uname -a                           # Tutte le info (kernel, hostname, arch)
cat /proc/version                  # Versione dettagliata (compiler, build date)
cat /proc/cmdline                  # Parametri boot del kernel
hostnamectl                        # Info sistema (include kernel)

# File del kernel in /boot/
ls /boot/
# vmlinuz-6.6.0-generic            → Kernel compresso (bzImage)
# initrd.img-6.6.0-generic         → Initial ramdisk (initramfs)
# config-6.6.0-generic             → Configurazione compilazione (.config)
# System.map-6.6.0-generic         → Mappa simboli (indirizzi funzioni kernel)

# Pseudo-filesystem informativi
/proc/                             # Informazioni processi e kernel (procfs)
/sys/                              # Interfaccia sysfs (dispositivi, driver, moduli)
/proc/cpuinfo                      # Info CPU (modello, cache, flag)
/proc/meminfo                      # Info memoria (totale, libera, cached, swap)
/proc/interrupts                   # Interrupt hardware (IRQ per CPU)
/proc/sys/                         # Parametri kernel modificabili (sysctl)
/proc/kallsyms                     # Tabella simboli kernel (tutti gli indirizzi)
/proc/slabinfo                     # Allocatore slab (cache oggetti kernel)
/proc/vmstat                       # Statistiche memoria virtuale
/proc/diskstats                    # Statistiche I/O disco
/proc/net/                         # Statistiche networking

# Info specifiche per processo
/proc/PID/status                   # Stato processo (memoria, thread, capabilities)
/proc/PID/maps                     # Mappa memoria virtuale
/proc/PID/fd/                      # File descriptor aperti
/proc/PID/limits                   # Limiti risorse (ulimit)
/proc/PID/cgroup                   # Appartenenza cgroup
/proc/PID/ns/                      # Namespaces
```

---

## Processo di Boot

Il processo di boot Linux segue una sequenza precisa dal power-on fino al login utente. Comprendere ogni fase e essenziale per diagnosticare problemi di avvio.

```
Power On
   │
   ▼
┌──────────┐    ┌───────────┐    ┌────────────┐    ┌───────────┐    ┌──────────┐
│BIOS/UEFI │───▶│ Bootloader│───▶│   Kernel   │───▶│ initramfs │───▶│ systemd  │
│ (POST +  │    │  (GRUB2)  │    │ (vmlinuz)  │    │ (initrd)  │    │ (PID 1)  │
│ hardware)│    │           │    │            │    │           │    │          │
└──────────┘    └───────────┘    └────────────┘    └───────────┘    └──────────┘
   ~2s             ~1-3s           ~1-2s             ~1-5s           ~2-10s
```

### BIOS/UEFI

**BIOS (Basic Input/Output System)** — Firmware legacy:
- Esegue POST (Power-On Self-Test): verifica RAM, CPU, periferiche
- Cerca il bootloader nel MBR (Master Boot Record, primi 512 byte del disco)
- Limitazione MBR: max 4 partizioni primarie, max 2 TB per disco
- Modalita in estinzione, sostituita da UEFI

**UEFI (Unified Extensible Firmware Interface)** — Firmware moderno:
- Legge la tabella partizioni GPT (GUID Partition Table)
- Cerca i bootloader nella ESP (EFI System Partition), tipicamente `/boot/efi/`
- Supporta Secure Boot: verifica firme crittografiche del bootloader e del kernel
- Supporta dischi > 2 TB, > 128 partizioni
- Include un boot manager integrato (puo avviare direttamente il kernel senza GRUB)

```bash
# Verificare se il sistema e UEFI o BIOS
ls /sys/firmware/efi 2>/dev/null && echo "UEFI" || echo "BIOS/Legacy"

# Tabella boot UEFI
efibootmgr -v                     # Lista entry UEFI con path
efibootmgr -o 0001,0002,0003      # Cambia ordine di boot

# Contenuto ESP
ls /boot/efi/EFI/
# ubuntu/  debian/  Microsoft/  ...
# Ogni OS ha la sua directory con il bootloader .efi

# Secure Boot
mokutil --sb-state                 # Stato Secure Boot
# SecureBoot enabled / SecureBoot disabled
```

### Bootloader GRUB2

GRUB2 (GRand Unified Bootloader 2) e il bootloader standard per la maggior parte delle distribuzioni Linux.

**Fasi di caricamento GRUB2:**
1. **Stage 1** (BIOS) o **EFI stub** (UEFI) — Codice minimo nel MBR o nella ESP
2. **Stage 1.5** (solo BIOS) — Codice nel gap post-MBR, contiene driver filesystem
3. **Stage 2** — GRUB completo, legge `grub.cfg`, mostra menu, carica kernel

```bash
# GRUB2 carica il kernel con questi parametri:
# linux /vmlinuz-6.6.0 root=UUID=xxxx ro quiet splash
# initrd /initrd.img-6.6.0

# Il kernel riceve root=, ro, quiet, splash come parametri da /proc/cmdline
cat /proc/cmdline
# BOOT_IMAGE=/vmlinuz-6.6.0 root=UUID=abc123 ro quiet splash
```

### Kernel e initramfs

Una volta che GRUB carica il kernel in memoria:

1. **Decompressione**: il kernel (vmlinuz = compressed vmlinux) si auto-decomprime
2. **Inizializzazione hardware base**: CPU, interrupt controller, timer
3. **Setup della memoria**: page table iniziali, zone di memoria
4. **Montaggio initramfs**: il kernel monta l'initramfs come root filesystem temporaneo
5. **Esecuzione /init**: il kernel esegue `/init` dall'initramfs (tipicamente uno script o systemd)
6. **initramfs carica i driver**: driver disco, driver filesystem, driver LVM/RAID/LUKS
7. **switch_root**: il vero root filesystem viene montato e si passa a `/sbin/init`

```bash
# Il kernel stampa i messaggi di boot nel ring buffer (dmesg)
dmesg | head -50                   # Prime righe: decompressione, CPU, memoria
dmesg | grep -i "command line"     # Parametri ricevuti da GRUB
dmesg | grep -i "mount"           # Montaggio root filesystem
```

### Init system (systemd)

Dopo switch_root, il kernel esegue il primo processo (PID 1):

```bash
# Su sistemi moderni, PID 1 e systemd
ps -p 1 -o comm=                   # systemd

# systemd monta i filesystem da /etc/fstab
# Avvia i servizi secondo le dipendenze dei target
# Il target predefinito:
systemctl get-default              # graphical.target o multi-user.target

# Analisi tempi di boot
systemd-analyze                    # Tempo totale boot
systemd-analyze blame              # Servizi piu lenti
systemd-analyze critical-chain     # Catena critica (path piu lungo)
systemd-analyze plot > boot.svg    # Grafico SVG del boot

# Sequenza target systemd:
# sysinit.target → basic.target → multi-user.target → graphical.target
```

---

## GRUB2 — Configurazione Avanzata

GRUB2 si configura tramite file in `/etc/default/grub` e script in `/etc/grub.d/`. Il file finale `grub.cfg` viene generato automaticamente — non modificarlo direttamente.

### File di configurazione principale

```bash
# /etc/default/grub — parametri principali

GRUB_DEFAULT=0                     # Voce di menu predefinita (0 = prima)
# GRUB_DEFAULT=saved               # Usa l'ultimo kernel selezionato
# GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 6.6.0"

GRUB_TIMEOUT=5                     # Secondi di attesa prima del boot automatico
GRUB_TIMEOUT_STYLE=menu            # menu|countdown|hidden

GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
# Parametri passati SOLO al kernel predefinito
# quiet = meno output, splash = schermata grafica

GRUB_CMDLINE_LINUX=""
# Parametri passati a TUTTI i kernel (incluso recovery)
# Esempio per server: "console=ttyS0,115200n8"

GRUB_DISABLE_RECOVERY="false"      # true = nasconde le voci recovery
GRUB_DISABLE_OS_PROBER="false"     # true = non cerca altri OS (dual boot)

# UEFI specifico
GRUB_ENABLE_CRYPTODISK=y           # Se /boot e su LUKS

# Console seriale (server headless)
GRUB_TERMINAL="serial console"
GRUB_SERIAL_COMMAND="serial --speed=115200 --unit=0 --word=8 --parity=no --stop=1"
```

### Generazione grub.cfg

```bash
# Debian/Ubuntu
sudo update-grub                   # Wrapper per grub-mkconfig
# equivale a:
sudo grub-mkconfig -o /boot/grub/grub.cfg

# RHEL/Fedora
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
# Su UEFI:
sudo grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg

# Gli script in /etc/grub.d/ generano le sezioni:
# 00_header       → Impostazioni base
# 05_debian_theme → Tema (Debian/Ubuntu)
# 10_linux        → Voci kernel Linux
# 20_linux_xen    → Voci Xen
# 30_os-prober    → Altri OS (Windows, ecc.)
# 40_custom       → Voci personalizzate
# 41_custom       → Include file custom

# Aggiungere una voce personalizzata:
# sudo nano /etc/grub.d/40_custom
# Poi: sudo update-grub
```

### Parametri kernel comuni al boot

```bash
# Parametri passati tramite GRUB_CMDLINE_LINUX o dalla riga di comando GRUB

# === DEBUG E DIAGNOSTICA ===
debug                              # Abilita messaggi debug kernel
loglevel=7                         # Livello log (0=emerg, 7=debug)
earlyprintk=vga                    # Messaggi kernel prima della console normale
nomodeset                          # Disabilita KMS (utile per problemi driver GPU)
nosplash                           # Disabilita splash screen

# === RECOVERY ===
single                             # Boot in single-user mode
init=/bin/bash                     # Avvia bash come PID 1 (bypass systemd)
rd.break                           # Interrompi in initramfs (utile per reset password)
systemd.unit=rescue.target         # Boot in rescue mode (con systemd)
systemd.unit=emergency.target      # Boot in emergency mode (filesystem minimo)

# === HARDWARE ===
acpi=off                           # Disabilita ACPI (problemi hardware)
noapic                             # Disabilita APIC
pci=nomsi                          # Disabilita MSI (problemi interrupt PCI)
iommu=pt                           # Passthrough IOMMU (VM/GPU passthrough)
intel_iommu=on                     # Abilita IOMMU Intel (VT-d)
amd_iommu=on                       # Abilita IOMMU AMD (AMD-Vi)

# === SICUREZZA ===
selinux=0                          # Disabilita SELinux (temporaneo debug)
apparmor=0                         # Disabilita AppArmor
lockdown=integrity                 # Kernel lockdown mode (integrity o confidentiality)

# === MEMORIA ===
mem=4G                             # Limita la RAM visibile al kernel
hugepagesz=2M hugepages=1024       # Pre-alloca 2GB di huge pages
transparent_hugepage=never         # Disabilita THP (database)

# === RETE ===
ip=dhcp                            # Configura rete in initramfs via DHCP
```

### Rescue mode

```bash
# Accesso al rescue mode:
# 1. Al menu GRUB, selezionare "Advanced options"
# 2. Scegliere la voce con "(recovery mode)"
# Oppure: premere 'e' su una voce, aggiungere "single" alla riga linux, Ctrl+X

# Se GRUB non appare (boot troppo veloce):
# Tenere premuto SHIFT (BIOS) o premere ESC (UEFI) durante il boot

# Se GRUB e corrotto e non appare:
# Avviare da USB live e reinstallare GRUB:
sudo mount /dev/sda2 /mnt
sudo mount /dev/sda1 /mnt/boot/efi   # Solo UEFI
for fs in proc sys dev dev/pts run; do
    sudo mount --bind /$fs /mnt/$fs
done
sudo chroot /mnt
update-grub
grub-install /dev/sda              # BIOS
# oppure:
grub-install --target=x86_64-efi --efi-directory=/boot/efi   # UEFI
exit
sudo umount -R /mnt
```

---

## initramfs / initrd

L'initramfs (initial RAM filesystem) e un archivio cpio compresso che contiene un filesystem temporaneo caricato in RAM dal bootloader. Il suo scopo e fornire al kernel i driver e gli strumenti necessari per montare il vero root filesystem.

### Perche serve l'initramfs

Il kernel compilato dalla distribuzione non puo includere tutti i driver possibili come built-in (sarebbe enorme). L'initramfs contiene solo i driver necessari per il sistema specifico:
- Driver controller disco (ahci, nvme, virtio_blk, megaraid_sas...)
- Driver filesystem del root (ext4, xfs, btrfs...)
- Driver LVM, RAID software (dm-mod, md-mod)
- Driver LUKS/crittografia (dm-crypt, cryptsetup)
- Driver rete (se root e NFS)
- udev per il rilevamento dinamico dei dispositivi

```bash
# Esaminare il contenuto dell'initramfs
lsinitramfs /boot/initrd.img-$(uname -r) | head -30    # Debian/Ubuntu
lsinitrd /boot/initramfs-$(uname -r).img | head -30     # RHEL/Fedora

# Estrarre per ispezione (senza modificare)
mkdir /tmp/initramfs && cd /tmp/initramfs
unmkinitramfs /boot/initrd.img-$(uname -r) .            # Debian/Ubuntu

# Struttura tipica dell'initramfs:
# /init                   → Script di avvio (o systemd)
# /bin/                   → Busybox o binari essenziali
# /lib/modules/           → Moduli kernel necessari
# /etc/                   → Configurazione minima
# /scripts/               → Script hook (Debian)
# /usr/lib/dracut/        → Hook dracut (RHEL)
```

### Creazione e rigenerazione

```bash
# === DEBIAN/UBUNTU (mkinitramfs / update-initramfs) ===

# Rigenerare initramfs per il kernel corrente
sudo update-initramfs -u                           # Update (-u)

# Rigenerare per un kernel specifico
sudo update-initramfs -u -k 6.6.0-generic

# Rigenerare per TUTTI i kernel installati
sudo update-initramfs -u -k all

# Creare da zero
sudo mkinitramfs -o /boot/initrd.img-6.6.0-generic 6.6.0-generic

# Configurazione: /etc/initramfs-tools/initramfs.conf
# MODULES=most                     # most|dep|list (most = carica piu moduli possibili)
# COMPRESS=zstd                    # gzip|lz4|xz|zstd
# UMASK=0077                       # Permessi restrittivi

# Moduli aggiuntivi: /etc/initramfs-tools/modules
# dm-crypt                         # Un modulo per riga
# aesni_intel

# === RHEL/FEDORA (dracut) ===

# Rigenerare initramfs per il kernel corrente
sudo dracut --force

# Rigenerare per un kernel specifico
sudo dracut --force /boot/initramfs-6.6.0.img 6.6.0

# Rigenerare per TUTTI i kernel
sudo dracut --regenerate-all --force

# Con moduli aggiuntivi
sudo dracut --add-drivers "dm-crypt aesni_intel" --force

# Con moduli dracut (non kernel modules)
sudo dracut --add "crypt lvm" --force

# Configurazione: /etc/dracut.conf.d/custom.conf
# add_dracutmodules+=" crypt lvm "
# add_drivers+=" dm-crypt "
# compress="zstd"
# hostonly="yes"                   # Solo driver per questo host (piu piccolo)
# hostonly="no"                    # Tutti i driver (portable, piu grande)
```

### Troubleshooting initramfs

```bash
# initramfs corrotto — sintomo: kernel panic "Unable to mount root fs"
# Fix: avviare da kernel precedente (GRUB) e rigenerare
sudo update-initramfs -u           # Debian/Ubuntu
sudo dracut --force                # RHEL/Fedora

# initramfs manca moduli — sintomo: "waiting for root device" al boot
# Fix: verificare che il driver del controller disco sia incluso
lsinitramfs /boot/initrd.img-$(uname -r) | grep -E "nvme|ahci|virtio"

# Se manca, aggiungerlo:
echo "nvme" >> /etc/initramfs-tools/modules     # Debian/Ubuntu
sudo update-initramfs -u

# Accesso alla shell initramfs (debug):
# Aggiungere "rd.break" o "break=premount" ai parametri kernel in GRUB
# Si otterra una shell BusyBox nell'initramfs
```

---

## Moduli Kernel

I moduli kernel sono componenti caricabili a runtime che estendono le funzionalita del kernel senza ricompilazione. Tipicamente: driver hardware, filesystem, protocolli di rete, funzionalita di sicurezza.

I moduli sono file `.ko` (kernel object) compilati per una specifica versione del kernel. La stringa `vermagic` all'interno del modulo deve corrispondere alla versione del kernel in esecuzione, altrimenti il caricamento fallisce.

### Gestione dei moduli

```bash
# === LISTA MODULI CARICATI ===
lsmod                              # Lista con dimensione e dipendenze
lsmod | grep -i nvidia             # Cerca modulo specifico
lsmod | wc -l                      # Conta moduli caricati
lsmod | sort -k2 -n -r | head -10  # Top 10 per dimensione

# === INFORMAZIONI MODULO ===
modinfo ext4                       # Info dettagliate (autore, licenza, parametri)
modinfo -p ext4                    # Solo parametri disponibili
modinfo -F depends ext4            # Solo dipendenze
modinfo -F vermagic ext4           # Stringa vermagic (versione kernel richiesta)
modinfo -F filename ext4           # Path del file .ko

# === CARICARE MODULO ===
sudo modprobe vfat                 # Carica modulo (risolve dipendenze automaticamente)
sudo modprobe bonding mode=1       # Carica con parametri
sudo modprobe -v vfat              # Verbose (mostra cosa fa)
sudo modprobe -n vfat              # Dry-run (mostra senza eseguire)

# insmod — caricamento a basso livello (senza risolvere dipendenze)
sudo insmod /lib/modules/$(uname -r)/kernel/fs/vfat/vfat.ko
# Usato raramente; modprobe e quasi sempre preferibile

# === RIMUOVERE MODULO ===
sudo modprobe -r vfat              # Rimuovi (e dipendenze non piu usate)
sudo modprobe -r -v vfat           # Verbose
sudo rmmod vfat                    # Rimuovi senza gestire dipendenze
sudo rmmod -f vfat                 # Forza rimozione (PERICOLOSO, puo causare panic)

# === DIPENDENZE ===
sudo depmod -a                     # Ricostruisci database dipendenze (modules.dep)
sudo depmod -a 6.6.0-generic       # Per un kernel specifico

# Visualizzare dipendenze
modprobe --show-depends ext4       # Mostra catena di dipendenze
```

### Blacklist — impedire il caricamento

```bash
# File: /etc/modprobe.d/blacklist-custom.conf

# Blacklist semplice: impedisce il caricamento automatico
blacklist nouveau                  # Non caricare il driver nouveau (conflitto con NVIDIA)
blacklist pcspkr                   # Disabilita beep di sistema

# Blacklist forte: impedisce anche il caricamento indiretto (da dipendenze)
install nouveau /bin/false         # Qualsiasi tentativo di caricare nouveau fallisce
install nouveau /bin/true          # Alternativa silenziosa

# Blacklist con messaggio di log
install nouveau /bin/echo "nouveau bloccato in favore di nvidia-driver"

# Dopo modifica blacklist, rigenerare initramfs:
sudo update-initramfs -u           # Debian/Ubuntu
sudo dracut --force                # RHEL/Fedora

# Verificare che un modulo sia in blacklist
grep -r nouveau /etc/modprobe.d/

# Blacklist temporanea al boot: aggiungere a GRUB
# modprobe.blacklist=nouveau,pcspkr
```

### Caricamento automatico al boot

```bash
# File: /etc/modules-load.d/custom.conf
# Un modulo per riga — caricati da systemd-modules-load.service
bonding
br_netfilter
overlay
vhost_net
nbd

# Parametri modulo persistenti
# File: /etc/modprobe.d/custom.conf
options bonding mode=1 miimon=100
options snd_hda_intel power_save=1 power_save_controller=Y
options kvm_intel nested=1                   # Virtualizzazione annidata
options usbcore autosuspend=-1               # Disabilita USB autosuspend

# Verificare parametri correnti di un modulo caricato
cat /sys/module/bonding/parameters/mode
cat /sys/module/kvm_intel/parameters/nested

# Alcuni parametri possono essere modificati a runtime via sysfs
echo 1 | sudo tee /sys/module/kvm_intel/parameters/nested
```

### Moduli comuni

| Modulo | Funzione | Note |
|---|---|---|
| `ext4` | Filesystem ext4 | Piu diffuso |
| `xfs` | Filesystem XFS | Default RHEL |
| `btrfs` | Filesystem Btrfs | CoW, snapshot |
| `nfs` / `nfsd` | Client / Server NFS | Network filesystem |
| `bonding` | Link aggregation | mode=1 (active-backup), mode=4 (LACP) |
| `bridge` | Network bridging | VM, container |
| `br_netfilter` | Netfilter per bridge | Kubernetes, iptables su bridge |
| `overlay` | Overlay filesystem | Docker, Podman |
| `vfat` | Filesystem FAT32 | USB, ESP |
| `dm_crypt` | Crittografia disco | LUKS |
| `kvm` / `kvm_intel` / `kvm_amd` | Virtualizzazione KVM | Hardware virtualization |
| `nf_conntrack` | Connection tracking | Firewall stateful |
| `wireguard` | VPN WireGuard | Kernel ≥ 5.6 |
| `vhost_net` | Virtio networking | Performance VM |
| `nbd` | Network block device | Connessione a block device remoti |
| `ip_tables` / `nf_tables` | Netfilter framework | Firewall |
| `tun` / `tap` | Virtual network interfaces | VPN, VM |

---

## Parametri Kernel (sysctl)

sysctl permette di visualizzare e modificare i parametri del kernel a runtime tramite il filesystem `/proc/sys/`. Ogni file in `/proc/sys/` corrisponde a un parametro kernel.

### Gerarchia /proc/sys

```bash
/proc/sys/
├── kernel/                    # Parametri kernel generali
│   ├── hostname               # Nome host
│   ├── osrelease              # Versione kernel
│   ├── pid_max                # PID massimo
│   ├── threads-max            # Thread massimi di sistema
│   ├── randomize_va_space     # ASLR
│   ├── shmmax                 # Shared memory massima
│   ├── panic                  # Secondi prima del reboot dopo panic
│   ├── panic_on_oops          # Panic su kernel oops
│   ├── dmesg_restrict         # dmesg solo per root
│   ├── kptr_restrict          # Nasconde indirizzi kernel
│   └── yama/
│       └── ptrace_scope       # Restrizioni ptrace
│
├── vm/                        # Memoria virtuale
│   ├── swappiness             # Aggressivita swap (0-200, default 60)
│   ├── dirty_ratio            # % per flush sincrono
│   ├── dirty_background_ratio # % per flush background
│   ├── overcommit_memory      # Policy overcommit (0/1/2)
│   ├── overcommit_ratio       # % per overcommit mode 2
│   ├── min_free_kbytes        # Memoria minima libera
│   ├── vfs_cache_pressure     # Pressione cache inode/dentry
│   ├── nr_hugepages           # Numero huge pages
│   └── zone_reclaim_mode      # Reclaim NUMA locale
│
├── net/                       # Networking
│   ├── core/
│   │   ├── somaxconn          # Backlog socket
│   │   ├── netdev_max_backlog # Coda pacchetti
│   │   ├── rmem_max           # Buffer ricezione max
│   │   └── wmem_max           # Buffer invio max
│   ├── ipv4/
│   │   ├── ip_forward         # Routing IP
│   │   ├── tcp_syncookies     # Protezione SYN flood
│   │   ├── tcp_fin_timeout    # Timeout FIN_WAIT2
│   │   ├── tcp_keepalive_time # Keepalive
│   │   ├── tcp_fastopen       # TCP Fast Open
│   │   ├── tcp_congestion_control  # Algoritmo congestione (cubic, bbr)
│   │   └── conf/
│   │       ├── all/
│   │       │   ├── rp_filter  # Reverse path filtering
│   │       │   └── accept_redirects
│   │       └── eth0/          # Per-interface
│   └── ipv6/
│       └── conf/
│           └── all/
│               └── forwarding
│
├── fs/                        # Filesystem
│   ├── file-max               # Max file descriptor di sistema
│   ├── file-nr                # FD usati / 0 / massimo
│   ├── inotify/
│   │   ├── max_user_watches   # Watch inotify per utente
│   │   └── max_user_instances # Istanze inotify per utente
│   └── aio-max-nr             # Async I/O max
│
└── dev/                       # Parametri per dispositivi specifici
```

### Comandi sysctl

```bash
# VISUALIZZARE
sysctl -a                          # Tutti i parametri (1000+)
sysctl -a | wc -l                  # Quanti parametri
sysctl net.ipv4.ip_forward         # Parametro specifico
sysctl -a -r "net.ipv4.tcp"        # Regex: tutti i parametri TCP
cat /proc/sys/net/ipv4/ip_forward  # Equivalente via /proc

# MODIFICARE (temporaneo — perso al reboot)
sudo sysctl -w net.ipv4.ip_forward=1
# Equivalente:
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# MODIFICARE MULTIPLI
sudo sysctl -w net.ipv4.ip_forward=1 net.ipv4.tcp_syncookies=1

# CARICARE DA FILE
sudo sysctl -p /etc/sysctl.d/99-custom.conf
sudo sysctl --system                # Ricarica TUTTI i file sysctl (ordine di precedenza)
```

### Persistenza con sysctl.d

```bash
# Ordine di caricamento (ultimo vince):
# /usr/lib/sysctl.d/*.conf        → Default distribuzione
# /run/sysctl.d/*.conf            → Runtime
# /etc/sysctl.d/*.conf            → Amministratore (priorita massima)
# /etc/sysctl.conf                → Legacy (ancora supportato)

# Convenzione numerazione:
# 10-*.conf  → Sicurezza base
# 50-*.conf  → Tuning generico
# 90-*.conf  → Tuning specifico workload
# 99-*.conf  → Override finali
```

### Parametri importanti

```bash
# === NETWORKING ===
net.ipv4.ip_forward = 1                          # Routing tra interfacce
net.ipv4.conf.all.rp_filter = 1                  # Reverse path filtering (anti-spoofing)
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1         # Ignora ping broadcast (anti-smurf)
net.ipv4.conf.all.accept_redirects = 0           # No ICMP redirect
net.ipv4.conf.all.send_redirects = 0
net.ipv4.tcp_syncookies = 1                      # Protezione SYN flood
net.ipv4.tcp_max_syn_backlog = 4096              # Coda SYN
net.core.somaxconn = 65535                        # Backlog socket
net.core.netdev_max_backlog = 5000               # Coda pacchetti in ingresso
net.ipv4.tcp_fin_timeout = 30                    # Timeout FIN_WAIT2
net.ipv4.tcp_keepalive_time = 600                # Keepalive TCP
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.ip_local_port_range = 1024 65535        # Range porte effimere
net.ipv4.tcp_fastopen = 3                        # TCP Fast Open (client+server)
net.ipv4.tcp_congestion_control = bbr            # BBR congestione (Google)
net.core.default_qdisc = fq                      # Fair Queue per BBR
net.core.rmem_max = 16777216                     # Buffer ricezione max (16MB)
net.core.wmem_max = 16777216                     # Buffer invio max (16MB)
net.ipv4.tcp_rmem = 4096 87380 16777216          # Min/default/max ricezione TCP
net.ipv4.tcp_wmem = 4096 65536 16777216          # Min/default/max invio TCP
net.ipv4.tcp_mtu_probing = 1                     # Path MTU discovery

# === MEMORIA ===
vm.swappiness = 10                               # Quanto usare swap (0-200, basso = meno swap)
vm.dirty_ratio = 20                              # % RAM per dirty page prima di flush sincrono
vm.dirty_background_ratio = 10                   # % RAM per dirty page prima di flush background
vm.dirty_expire_centisecs = 3000                 # Eta max dirty page (30 sec)
vm.dirty_writeback_centisecs = 500               # Intervallo writeback (5 sec)
vm.overcommit_memory = 0                         # 0=heuristic, 1=always, 2=never
vm.overcommit_ratio = 50                         # % per mode 2 (RAM*ratio + swap)
vm.min_free_kbytes = 65536                       # Memoria minima libera
vm.vfs_cache_pressure = 50                       # Pressione cache inode/dentry (< 100 = mantieni)
vm.zone_reclaim_mode = 0                         # 0=no reclaim locale NUMA

# === FILESYSTEM ===
fs.file-max = 2097152                            # Max file descriptor di sistema
fs.inotify.max_user_watches = 524288             # Max watch inotify (utile per IDE, Docker)
fs.inotify.max_user_instances = 1024             # Istanze inotify per utente
fs.aio-max-nr = 1048576                          # Async I/O requests massime

# === KERNEL ===
kernel.pid_max = 4194304                         # Max PID (default 32768, max 4M)
kernel.threads-max = 256000                      # Thread massimi
kernel.panic = 10                                # Reboot dopo 10 sec da kernel panic
kernel.panic_on_oops = 1                         # Panic su oops (per server critici)
kernel.sched_autogroup_enabled = 1               # Autogroup scheduling (desktop)

# === SICUREZZA ===
kernel.randomize_va_space = 2                    # ASLR (Address Space Layout Randomization)
kernel.dmesg_restrict = 1                        # dmesg solo per root
kernel.kptr_restrict = 2                         # Nasconde indirizzi kernel in /proc/kallsyms
kernel.yama.ptrace_scope = 1                     # Limita ptrace (1=solo parent)
kernel.unprivileged_bpf_disabled = 1             # Disabilita eBPF non privilegiato
net.ipv4.conf.all.log_martians = 1               # Log pacchetti con sorgente impossibile
kernel.perf_event_paranoid = 2                   # Limita perf a root
kernel.core_uses_pid = 1                         # Core dump con PID nel nome
```

---

## Compilazione Kernel Personalizzato

Compilare un kernel personalizzato permette di: abilitare/disabilitare funzionalita specifiche, applicare patch personalizzate, ottimizzare per hardware specifico, includere moduli non upstream, applicare hardening aggiuntivo.

### Prerequisiti

```bash
# Debian/Ubuntu
sudo apt install build-essential libncurses-dev bison flex libssl-dev \
  libelf-dev bc dwarves git cpio zstd

# RHEL/Fedora
sudo dnf groupinstall "Development Tools"
sudo dnf install ncurses-devel bison flex elfutils-libelf-devel \
  openssl-devel bc dwarves git perl

# Spazio disco necessario: ~25-30 GB
# Tempo compilazione: 15-90 minuti (dipende da hardware e .config)
```

### Metodo 1: da kernel.org (tarball)

```bash
# 1. Scaricare sorgenti
cd /usr/src
sudo wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.80.tar.xz
sudo wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.80.tar.sign

# 2. Verificare la firma GPG (SICUREZZA)
xz -d linux-6.6.80.tar.xz
gpg --locate-keys torvalds@kernel.org
gpg --verify linux-6.6.80.tar.sign linux-6.6.80.tar
# Deve riportare "Good signature from Linus Torvalds"

# 3. Estrarre
sudo tar xf linux-6.6.80.tar
cd linux-6.6.80
```

### Metodo 2: da git (clone)

```bash
# Clone completo (lento, ~3 GB)
git clone https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git
cd linux
git checkout v6.6.80

# Clone shallow (piu veloce, solo l'ultimo commit)
git clone --depth 1 --branch v6.6.80 \
  https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git
cd linux
```

### Configurazione

```bash
# === OPZIONE A: partire dalla config corrente ===
cp /boot/config-$(uname -r) .config
make olddefconfig                  # Accetta default per nuove opzioni
# oppure:
make oldconfig                     # Chiede interattivamente per ogni nuova opzione

# === OPZIONE B: configurazione interattiva ===
make menuconfig                    # Interfaccia ncurses (il piu usato)
# make nconfig                     # ncurses alternativa (piu moderna)
# make xconfig                     # Interfaccia Qt5 (richiede libqt5-dev)
# make gconfig                     # Interfaccia GTK

# Navigazione menuconfig:
# [*] = built-in     Compilato nel kernel (vmlinuz)
# [M] = module       Compilato come modulo caricabile (.ko)
# [ ] = disabilitato Non compilato
# Frecce = navigazione, Spazio = toggle, / = ricerca, ? = help

# === OPZIONE C: config minima per questo hardware ===
make localmodconfig                # Config basata sui moduli attualmente caricati
# ATTENZIONE: se un dispositivo non e collegato ora, il suo driver non sara incluso

# === OPZIONE D: config minimale di default ===
make defconfig                     # Config di default dell'architettura
make tinyconfig                    # Config minima assoluta (per embedded/test)

# Opzioni importanti in menuconfig:
# General setup → Local version: -custom (suffisso versione)
# General setup → Default hostname: (hostname)
# Processor type → Processor family: (scegliere la propria CPU)
# Enable loadable module support: [*] (sempre abilitato)
# Enable the block layer → IO Schedulers: (scegliere gli scheduler)
# File systems → (abilitare i filesystem necessari)
# Device Drivers → (driver per il proprio hardware)
# Security options → (SELinux, AppArmor, seccomp)
# Kernel hacking → (opzioni debug, solo per sviluppo)
```

### Compilazione e installazione

```bash
# 4. Compilazione
make -j$(nproc)                    # Compila con tutti i core CPU
# oppure con verbosita:
make -j$(nproc) V=1                # Verbose (mostra comandi gcc)

# Solo moduli:
make -j$(nproc) modules

# Cross-compilazione (esempio per ARM64):
make -j$(nproc) ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-

# 5. Installazione moduli
sudo make modules_install          # Installa in /lib/modules/6.6.80-custom/

# 6. Installazione kernel
sudo make install                  # Copia vmlinuz, System.map, aggiorna bootloader
# Questo comando:
# - Copia arch/x86/boot/bzImage → /boot/vmlinuz-6.6.80-custom
# - Copia System.map → /boot/System.map-6.6.80-custom
# - Copia .config → /boot/config-6.6.80-custom
# - Genera initramfs (update-initramfs / dracut)
# - Aggiorna GRUB (update-grub / grub2-mkconfig)

# 7. Verifica GRUB
grep -c menuentry /boot/grub/grub.cfg   # Numero di voci kernel

# 8. Riavvio
sudo reboot
# Selezionare il nuovo kernel da GRUB se necessario

# 9. Verifica post-boot
uname -r                           # Dovrebbe mostrare 6.6.80-custom
dmesg | head -20                   # Verificare messaggi di avvio
```

### Pulizia e manutenzione

```bash
# Pulizia sorgenti
make clean                         # Rimuovi file oggetto (.o), mantieni .config
make mrproper                      # Rimuovi tutto (incluso .config, preparati)
make distclean                     # Come mrproper + rimuovi file editor/backup

# Rimuovere un kernel installato
sudo rm /boot/vmlinuz-6.6.80-custom
sudo rm /boot/initrd.img-6.6.80-custom
sudo rm /boot/System.map-6.6.80-custom
sudo rm /boot/config-6.6.80-custom
sudo rm -rf /lib/modules/6.6.80-custom/
sudo update-grub                   # Rigenera GRUB

# Applicare una patch
cd /usr/src/linux-6.6.80
patch -p1 < /path/to/patch.diff
# oppure:
git apply /path/to/patch.diff
```

### Ottimizzazione della Compilazione

#### Compilazione con LLVM/Clang

Dal kernel 5.12, LLVM/Clang e un compilatore supportato ufficialmente per il kernel Linux. Google, Android e ChromeOS usano Clang per le build di produzione. Vantaggi rispetto a GCC:

- **ThinLTO** (Link-Time Optimization): ottimizzazione cross-modulo senza il costo di memoria di Full LTO. Attivabile con `make LLVM=1 LLVM_IAS=1 CONFIG_LTO_CLANG_THIN=y`
- **CFI** (Control-Flow Integrity): protezione contro hijacking di puntatori a funzione, attiva di default su Android kernel
- **Sanitizer integrati**: KASAN, KCSAN, KMSAN con overhead inferiore rispetto a GCC

```bash
# Build con LLVM completo (compiler + assembler + linker)
make LLVM=1 -j$(nproc)

# ThinLTO — ottimizzazione cross-translation-unit
scripts/config --enable CONFIG_LTO_CLANG_THIN

# Shadow Call Stack (arm64) — protezione stack return address
scripts/config --enable CONFIG_SHADOW_CALL_STACK
```

#### PGO — Profile-Guided Optimization

PGO (Profile-Guided Optimization) compila il kernel in due passaggi: prima genera un profilo di esecuzione dal workload reale, poi ricompila ottimizzando i percorsi caldi (hot paths). Google riporta un **miglioramento del 5-15% su throughput I/O** con PGO su kernel di produzione.

```bash
# Passo 1: Build con strumentazione
scripts/config --enable CONFIG_PGO_CLANG
make LLVM=1 -j$(nproc)
# Boot e esegui workload rappresentativo per 10-30 minuti

# Passo 2: Raccogliere profilo
cp /sys/kernel/debug/pgo/profraw vmlinux.profraw
llvm-profdata merge -output=vmlinux.profdata vmlinux.profraw

# Passo 3: Rebuild con profilo
make LLVM=1 KCFLAGS="-fprofile-use=vmlinux.profdata" -j$(nproc)
```

#### Configurazione per Workload Specifici

| Workload | Flag chiave | Effetto |
|----------|------------|---------|
| Server web / proxy | `CONFIG_HZ_1000=y`, `CONFIG_PREEMPT_VOLUNTARY=y` | Bassa latenza networking |
| Database (PostgreSQL, MySQL) | `CONFIG_TRANSPARENT_HUGEPAGE_MADVISE=y`, `CONFIG_CGROUP_HUGETLB=y` | Riduzione TLB miss |
| Storage NVMe | `CONFIG_IO_URING=y`, `CONFIG_BLK_DEV_NVME=y` built-in | Bypass modulo, boot veloce |
| Virtualizzazione KVM | `CONFIG_KVM=y`, `CONFIG_VHOST_NET=y` built-in | Evita caricamento moduli |
| Real-time audio/video | `CONFIG_PREEMPT_RT=y`, `CONFIG_HZ_1000=y` | Latenza deterministrica < 100us |
| Container host | `CONFIG_CGROUP_BPF=y`, `CONFIG_BPF_LSM=y` | Policy granulari per container |

```bash
# Ridurre tempo di compilazione — solo moduli necessari
make localmodconfig         # Configura solo moduli attualmente caricati
lsmod > /tmp/modlist
make LSMOD=/tmp/modlist localmodconfig
```

---

## DKMS — Driver Management

DKMS (Dynamic Kernel Module Support) ricompila automaticamente i moduli di terze parti quando il kernel viene aggiornato. Indispensabile per driver out-of-tree (NVIDIA, VirtualBox, ZFS, WireGuard su kernel vecchi).

```bash
# Installazione
sudo apt install dkms              # Debian/Ubuntu
sudo dnf install dkms              # RHEL/Fedora

# Stato
dkms status                        # Moduli DKMS installati
# nvidia/535.183.01, 6.6.0-generic, x86_64: installed
# virtualbox/7.0.14, 6.6.0-generic, x86_64: installed

# Aggiungere un modulo manualmente
sudo dkms add -m modulo -v 1.0
sudo dkms build -m modulo -v 1.0
sudo dkms install -m modulo -v 1.0

# Rimuovere
sudo dkms remove -m modulo -v 1.0 --all

# Ricostruire per un kernel specifico
sudo dkms build -m nvidia -v 535.183.01 -k 6.6.0-generic
sudo dkms install -m nvidia -v 535.183.01 -k 6.6.0-generic

# Struttura directory DKMS
# /usr/src/modulo-1.0/
# ├── dkms.conf          → Configurazione DKMS
# └── *.c, Makefile       → Sorgenti modulo
```

```ini
# Esempio dkms.conf
PACKAGE_NAME="mymodule"
PACKAGE_VERSION="1.0"
BUILT_MODULE_NAME[0]="mymodule"
DEST_MODULE_LOCATION[0]="/updates"
AUTOINSTALL="yes"
MAKE[0]="make -C ${kernel_source_dir} M=${dkms_tree}/${PACKAGE_NAME}/${PACKAGE_VERSION}/build"
CLEAN="make -C ${kernel_source_dir} M=${dkms_tree}/${PACKAGE_NAME}/${PACKAGE_VERSION}/build clean"
```

### Problema vermagic mismatch

```bash
# Se DKMS fallisce con "module version mismatch":
dkms status                        # Verificare versioni
ls /usr/src/ | grep modulo         # Sorgenti presenti?

# Forzare la ricostruzione
sudo dkms remove -m modulo -v 1.0 --all
sudo dkms add -m modulo -v 1.0
sudo dkms build -m modulo -v 1.0 -k $(uname -r)
sudo dkms install -m modulo -v 1.0 -k $(uname -r)

# Se i sorgenti kernel non sono installati:
sudo apt install linux-headers-$(uname -r)       # Debian/Ubuntu
sudo dnf install kernel-devel-$(uname -r)        # RHEL/Fedora
```

---

## Gestione della Memoria

Il sottosistema di gestione della memoria del kernel e uno dei componenti piu complessi e critici per le prestazioni.

### Memoria virtuale

Ogni processo ha il proprio spazio di indirizzi virtuali, tradotto in indirizzi fisici dal MMU (Memory Management Unit) della CPU tramite page table gestite dal kernel.

```
Spazio di indirizzamento virtuale (64-bit):

0x0000000000000000 ┌────────────────────┐
                   │  User Space        │  128 TB (configurabile)
                   │  ├── Text (codice) │
                   │  ├── Data/BSS      │
                   │  ├── Heap ↓        │
                   │  │                  │
                   │  ├── mmap region   │
                   │  │                  │
                   │  └── Stack ↑       │
0x00007FFFFFFFFFFF └────────────────────┘
                   ┌────────────────────┐
                   │  Canonical hole    │  Non mappato
                   └────────────────────┘
0xFFFF800000000000 ┌────────────────────┐
                   │  Kernel Space      │  128 TB
                   │  ├── Direct map    │  Mappa tutta la RAM fisica
                   │  ├── vmalloc area  │  Allocazioni kernel non contigue
                   │  ├── kmap          │  Mapping temporaneo (32-bit legacy)
                   │  └── Modules       │  Spazio moduli caricabili
0xFFFFFFFFFFFFFFFF └────────────────────┘
```

```bash
# Informazioni memoria di sistema
free -h                            # Panoramica rapida
cat /proc/meminfo                  # Dettaglio completo (50+ campi)

# Campi importanti di /proc/meminfo:
# MemTotal        → RAM totale
# MemFree         → RAM non usata (ma non e "disponibile"!)
# MemAvailable    → RAM effettivamente disponibile (include cache reclaimable)
# Buffers         → Cache metadata filesystem
# Cached          → Page cache (file letti da disco)
# SwapTotal       → Swap totale
# SwapFree        → Swap libero
# Dirty           → Pagine sporche (da scrivere su disco)
# AnonPages       → Pagine anonime (heap, stack, mmap)
# Mapped          → Pagine mappate in memoria (shared libraries, mmap files)
# Slab            → Memoria usata dal slab allocator (cache oggetti kernel)
# SReclaimable    → Porzione slab reclaimable
# HugePages_Total → Huge pages allocate
# HugePages_Free  → Huge pages libere

# Statistiche dettagliate
cat /proc/vmstat                   # 100+ contatori VM
cat /proc/zoneinfo                 # Info per zone di memoria (DMA, DMA32, Normal)

# Per processo
cat /proc/PID/status | grep -i vm  # VmRSS, VmSize, VmSwap
cat /proc/PID/smaps_rollup         # Sommario memoria del processo
pmap -x PID                        # Mappa memoria dettagliata
```

### Page cache

Il kernel usa la RAM non utilizzata dai processi come cache per i file letti da disco (page cache). Questo velocizza enormemente gli accessi ripetuti ai file.

```bash
# Dimensione page cache
grep -E "Cached|Buffers" /proc/meminfo

# La page cache viene rilasciata automaticamente quando serve RAM
# Per forzare il rilascio (SOLO per debug/test, MAI in produzione regolarmente):
echo 1 | sudo tee /proc/sys/vm/drop_caches   # Page cache
echo 2 | sudo tee /proc/sys/vm/drop_caches   # Slab objects
echo 3 | sudo tee /proc/sys/vm/drop_caches   # Entrambi

# Parametri di tuning della cache
sysctl vm.vfs_cache_pressure                   # Default 100
# <100 = mantieni piu cache inode/dentry (buono per molti file piccoli)
# >100 = libera cache piu aggressivamente

sysctl vm.dirty_ratio                          # Default 20
sysctl vm.dirty_background_ratio               # Default 10
# dirty_background_ratio: quando le dirty page superano questa % di RAM,
#   il kernel avvia il writeback in background (pdflush/writeback)
# dirty_ratio: quando le dirty page superano questa %, i processi che scrivono
#   vengono BLOCCATI fino a che il writeback non riduce le dirty page
```

### Swap

Lo swap e spazio su disco usato come estensione della RAM quando la memoria fisica e insufficiente.

```bash
# Visualizzare swap
swapon --show                      # Dispositivi swap attivi
free -h                            # Include info swap
cat /proc/swaps                    # Dettaglio swap

# Creare un file di swap
sudo fallocate -l 4G /swapfile     # Allocare 4 GB
sudo chmod 600 /swapfile           # Permessi restrittivi (sicurezza)
sudo mkswap /swapfile              # Formattare come swap
sudo swapon /swapfile              # Attivare

# Persistenza in /etc/fstab:
# /swapfile   none   swap   sw   0   0

# vm.swappiness controlla l'aggressivita dello swap
sysctl vm.swappiness               # Default 60
# 0   = swap solo in emergenza (non disabilita lo swap)
# 10  = buon valore per server (meno swap, piu page cache eviction)
# 60  = default (bilanciato)
# 100 = aggressivo (pre-kernel 5.8: massimo; post 5.8: calcolato diversamente)
# 200 = massimo (kernel recenti con zswap/zram)

# Disattivare swap temporaneamente
sudo swapoff -a                    # Disattiva tutto lo swap
# ATTENZIONE: se la RAM non e sufficiente, OOM killer interverra
sudo swapon -a                     # Riattiva

# zswap — compressione swap in RAM (prima di scrivere su disco)
# Abilitato di default su molte distro recenti
cat /sys/module/zswap/parameters/enabled   # Y o N
echo Y | sudo tee /sys/module/zswap/parameters/enabled
echo lz4 | sudo tee /sys/module/zswap/parameters/compressor

# zram — swap compresso interamente in RAM (nessun disco)
sudo modprobe zram
echo lz4 | sudo tee /sys/block/zram0/comp_algorithm
echo 2G | sudo tee /sys/block/zram0/disksize
sudo mkswap /dev/zram0
sudo swapon -p 100 /dev/zram0     # Priorita alta (usato prima del disco)
```

### OOM Killer

L'OOM Killer (Out-Of-Memory Killer) e il meccanismo del kernel che termina processi quando la memoria e completamente esaurita. E l'ultima risorsa prima del kernel panic.

```bash
# Verificare se l'OOM killer ha agito
dmesg | grep -i "oom\|out of memory\|killed process"
journalctl -k | grep -i oom

# Output tipico OOM:
# Out of memory: Killed process 1234 (java) total-vm:8192000kB,
# anon-rss:4096000kB, file-rss:128kB, shmem-rss:0kB, UID:1000
# oom_score_adj: 0

# Ogni processo ha un punteggio OOM (0-1000):
cat /proc/PID/oom_score            # Punteggio corrente (calcolato dal kernel)
cat /proc/PID/oom_score_adj        # Aggiustamento (-1000 a 1000)

# Proteggere un processo dall'OOM killer
echo -1000 | sudo tee /proc/PID/oom_score_adj   # Immune (quasi) all'OOM
# Per systemd:
# [Service]
# OOMScoreAdjust=-1000

# Rendere un processo bersaglio preferenziale
echo 1000 | sudo tee /proc/PID/oom_score_adj    # Primo a essere terminato

# Disabilitare l'OOM killer (PERICOLOSO — puo causare kernel panic)
sysctl vm.panic_on_oom             # 0=oom killer, 1=kernel panic
# Non disabilitare l'OOM killer senza una strategia alternativa

# Configurare overcommit per prevenire OOM
sudo sysctl -w vm.overcommit_memory=2            # Mai overcommit
sudo sysctl -w vm.overcommit_ratio=80            # Commit limit = RAM*80% + swap
# Con mode 2, malloc() fallisce PRIMA dell'OOM invece di mentire
```

### Huge Pages

Le pagine standard su x86_64 sono 4 KB. Le huge pages (2 MB o 1 GB) riducono la pressione sulla TLB (Translation Lookaside Buffer) e migliorano le prestazioni per applicazioni con grandi dataset in memoria (database, VM, HPC).

```bash
# Verificare supporto
grep -i huge /proc/meminfo
# HugePages_Total:     0        → Huge pages allocate
# HugePages_Free:      0        → Huge pages libere
# HugePages_Rsvd:      0        → Huge pages riservate
# HugePages_Surp:      0        → Surplus
# Hugepagesize:     2048 kB     → Dimensione (2 MB)

# Allocare huge pages (persistente)
# /etc/sysctl.d/90-hugepages.conf
vm.nr_hugepages = 1024            # 1024 * 2 MB = 2 GB

# Allocare a runtime
echo 1024 | sudo tee /proc/sys/vm/nr_hugepages

# Montare hugetlbfs (per applicazioni che usano mmap)
sudo mkdir -p /mnt/hugepages
sudo mount -t hugetlbfs none /mnt/hugepages
# /etc/fstab:
# none  /mnt/hugepages  hugetlbfs  defaults  0  0

# Transparent Huge Pages (THP) — gestione automatica del kernel
cat /sys/kernel/mm/transparent_hugepage/enabled
# [always] madvise never
# always = THP per tutte le applicazioni
# madvise = THP solo per chi chiede via madvise(MADV_HUGEPAGE)
# never = THP disabilitato

# ATTENZIONE: database (PostgreSQL, Redis, MongoDB) spesso soffrono con THP
# a causa della latenza di compattazione. Raccomandazione:
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/defrag
```

### NUMA

NUMA (Non-Uniform Memory Access) — su sistemi multi-socket, ogni CPU ha la sua RAM locale. L'accesso alla RAM locale e piu veloce dell'accesso alla RAM di un'altra CPU (remote access).

```bash
# Verificare la topologia NUMA
numactl --hardware
# available: 2 nodes (0-1)
# node 0 cpus: 0 1 2 3 4 5 6 7
# node 0 size: 32768 MB
# node 1 cpus: 8 9 10 11 12 13 14 15
# node 1 size: 32768 MB
# node distances:
# node   0   1
#   0:  10  21     ← accesso locale=10, remoto=21 (2.1x piu lento)
#   1:  21  10

# Statistiche NUMA
numastat                           # Hit/miss per nodo
numastat -m                        # Dettaglio memoria per nodo

# Lanciare un processo su un nodo specifico
numactl --cpunodebind=0 --membind=0 ./my-database
# Vincola CPU e memoria al nodo 0

# Politiche di allocazione
numactl --interleave=all ./my-app  # Interleave tra tutti i nodi (buono per HPC)
numactl --preferred=0 ./my-app     # Preferisci nodo 0 ma non vincolare

# Per database: tipicamente --membind al nodo locale
# Per HPC: spesso --interleave=all per distribuire la banda

# Parametro kernel
sysctl vm.zone_reclaim_mode        # 0=no reclaim locale (default, buono)
# 1 = reclaim pagine locali prima di usare nodo remoto
# Quasi sempre lasciare a 0: il reclaim aggressivo danneggia le prestazioni
```

---

## Schedulazione dei Processi

Il process scheduler del kernel decide quale processo esegue su quale CPU e per quanto tempo. E il componente che determina la reattivita e l'equita del sistema.

### CFS e EEVDF

**CFS (Completely Fair Scheduler)** — Scheduler predefinito dal kernel 2.6.23 fino al 6.5. Modella un processore ideale che esegue tutti i processi contemporaneamente, assegnando a ciascuno una fetta proporzionale di CPU. Usa un red-black tree ordinato per "virtual runtime" (vruntime): il processo con il vruntime piu basso esegue per primo.

**EEVDF (Earliest Eligible Virtual Deadline First)** — Ha sostituito CFS come scheduler predefinito dal kernel 6.6. Aggiunge il concetto di "deadline virtuale": ogni processo ha un tempo entro cui dovrebbe ricevere la sua fetta di CPU. EEVDF riduce la latenza per i processi interattivi senza richiedere le euristiche di CFS.

```bash
# Verificare lo scheduler in uso
# Kernel ≤ 6.5: CFS
# Kernel ≥ 6.6: EEVDF
uname -r

# Classi di scheduling (in ordine di priorita):
# SCHED_DEADLINE (99)  → Deadline scheduling (real-time hard)
# SCHED_FIFO    (1-99) → Real-time FIFO (esegue fino a completamento o preemption)
# SCHED_RR      (1-99) → Real-time Round Robin (come FIFO con time quantum)
# SCHED_OTHER   (0)    → Normal scheduling (CFS/EEVDF) — la maggior parte dei processi
# SCHED_BATCH   (0)    → Per batch jobs (meno preemption)
# SCHED_IDLE    (0)    → Priorita minima assoluta

# Verificare la policy di un processo
chrt -p PID
# pid PID's current scheduling policy: SCHED_OTHER
# pid PID's current scheduling priority: 0

# Statistiche scheduler
cat /proc/schedstat                # Statistiche globali
cat /proc/PID/sched                # Statistiche per processo
```

### Schedulazione real-time

```bash
# Impostare un processo come real-time FIFO con priorita 50
sudo chrt -f 50 ./my-realtime-app

# Impostare un processo come real-time Round Robin con priorita 30
sudo chrt -r 30 ./my-rt-app

# Cambiare la policy di un processo esistente
sudo chrt -f -p 80 PID            # FIFO, priorita 80
sudo chrt -o -p 0 PID             # Torna a SCHED_OTHER

# Priorita real-time: 1 (minima) a 99 (massima)
# ATTENZIONE: un processo RT a priorita 99 che non cede la CPU puo
# bloccare il sistema. Usare con cautela.

# Limiti RT per utenti non-root: /etc/security/limits.conf
# audio   -   rtprio     95
# audio   -   memlock    unlimited

# Throttling RT (protezione da lockup)
cat /proc/sys/kernel/sched_rt_runtime_us    # 950000 (95% di ogni secondo)
cat /proc/sys/kernel/sched_rt_period_us     # 1000000 (1 secondo)
# I processi RT possono usare max 95% della CPU, il restante 5% e per SCHED_OTHER
```

### nice, ionice, chrt

```bash
# === nice / renice — priorita CPU per processi normali ===
# Nice va da -20 (priorita massima) a +19 (priorita minima)
# Default: 0

nice -n 10 make -j$(nproc)        # Compila con priorita bassa
nice -n -5 ./important-job         # Priorita alta (richiede root per < 0)

renice -n 15 -p PID               # Cambia nice di un processo esistente
renice -n -10 -u postgres         # Cambia nice per tutti i processi di un utente

# Verificare il nice di un processo
ps -eo pid,ni,comm | grep PID

# === ionice — priorita I/O ===
# Classi: 0=none, 1=realtime, 2=best-effort, 3=idle
# Priorita intra-classe: 0 (massima) a 7 (minima)

ionice -c 3 tar czf backup.tar.gz /data    # I/O idle (solo quando il disco e libero)
ionice -c 2 -n 0 dd if=/dev/sda of=disk.img # Best-effort, priorita massima
ionice -c 1 -n 4 ./realtime-app             # RT I/O (richiede root)

ionice -p PID                      # Mostra classe e priorita I/O correnti
ionice -c 3 -p PID                 # Cambia a idle

# === chrt — scheduling policy ===
# (vedi sezione schedulazione real-time sopra)
chrt -m                            # Mostra min/max priorita per ogni policy
```

### cgroups v2

cgroups (control groups) permettono di limitare, isolare e monitorare le risorse (CPU, memoria, I/O, rete) per gruppi di processi.

```bash
# Verificare se cgroups v2 e attivo
mount | grep cgroup2
# cgroup2 on /sys/fs/cgroup type cgroup2

# Se il sistema usa cgroups v1 (legacy):
# Aggiungere al kernel cmdline: systemd.unified_cgroup_hierarchy=1

# Controller disponibili
cat /sys/fs/cgroup/cgroup.controllers
# cpuset cpu io memory hugetlb pids rdma misc

# === LIMITARE CPU ===
# Creare un cgroup
sudo mkdir /sys/fs/cgroup/my-service
echo "+cpu +memory +io" | sudo tee /sys/fs/cgroup/cgroup.subtree_control

# Limitare al 50% di un core
echo "50000 100000" | sudo tee /sys/fs/cgroup/my-service/cpu.max
# formato: quota periodo (in microsecondi)
# 50000/100000 = 50% di un core

# Limitare a 2 core massimo
echo "200000 100000" | sudo tee /sys/fs/cgroup/my-service/cpu.max

# === LIMITARE MEMORIA ===
echo "512M" | sudo tee /sys/fs/cgroup/my-service/memory.max      # Limite hard
echo "256M" | sudo tee /sys/fs/cgroup/my-service/memory.high     # Limite soft (throttling)

# === LIMITARE I/O ===
# device_major:minor rbps wbps riops wiops
echo "8:0 rbps=50000000 wbps=20000000" | sudo tee /sys/fs/cgroup/my-service/io.max

# Aggiungere un processo al cgroup
echo PID | sudo tee /sys/fs/cgroup/my-service/cgroup.procs

# === SYSTEMD + CGROUPS ===
# systemd usa cgroups nativamente per ogni servizio
systemctl show nginx.service | grep -i cgroup
systemd-cgls                       # Albero cgroups
systemd-cgtop                      # Top per cgroups (real-time)

# Limiti via unit file systemd:
# [Service]
# CPUQuota=150%              → Max 1.5 core
# MemoryMax=2G               → Max 2 GB RAM
# MemoryHigh=1G              → Throttling sopra 1 GB
# IOWeight=50                → Peso I/O (default 100)
# TasksMax=512               → Max processi/thread
```

---

## I/O Scheduling

Lo scheduler I/O del kernel decide l'ordine in cui le richieste di I/O vengono inviate al dispositivo di storage. Dal kernel 5.0+, il framework multi-queue (blk-mq) e l'unico supportato.

### Scheduler disponibili (blk-mq)

| Scheduler | Uso ideale | Descrizione |
|---|---|---|
| `mq-deadline` | SSD SATA, HDD, VM | Ordina per deadline, evita starvation. Default su molti sistemi |
| `bfq` (Budget Fair Queueing) | Desktop, multimedia, I/O misto | Equita tra processi, bassa latenza interattiva. Piu overhead CPU |
| `kyber` | SSD NVMe veloci | Leggero, target di latenza, min overhead. Per device veloci |
| `none` | NVMe, device molto veloci | Nessuno scheduling, FIFO diretto. Minimo overhead |

```bash
# Verificare lo scheduler corrente
cat /sys/block/sda/queue/scheduler
# [mq-deadline] kyber bfq none

# Cambiare scheduler (temporaneo)
echo bfq | sudo tee /sys/block/sda/queue/scheduler

# Cambiare permanentemente via udev rule:
# /etc/udev/rules.d/60-io-scheduler.rules
# HDD (rotazionali) → mq-deadline
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", \
  ATTR{queue/scheduler}="mq-deadline"

# SSD SATA → mq-deadline o bfq
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", \
  ATTR{queue/scheduler}="mq-deadline"

# NVMe → none (il controller NVMe ha il suo scheduling interno)
ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="none"

# Verificare se un disco e rotazionale
cat /sys/block/sda/queue/rotational   # 1=HDD, 0=SSD

# Parametri scheduler
ls /sys/block/sda/queue/iosched/       # Parametri tunabili per lo scheduler corrente

# mq-deadline: read_expire, write_expire, fifo_batch, writes_starved, front_merges
# bfq: low_latency, slice_idle, back_seek_max, strict_guarantees
# kyber: read_lat_nsec, write_lat_nsec

# Esempio tuning bfq per desktop:
echo 1 | sudo tee /sys/block/sda/queue/iosched/low_latency
```

### Scelta dello scheduler

```
HDD (rotazionale, seek time significativo)
  → mq-deadline: ordina le richieste per ridurre i seek
  → bfq: se l'equita tra processi e importante (desktop con molti utenti/app)

SSD SATA/AHCI (nessun seek, ma latenza media)
  → mq-deadline: buon bilanciamento
  → bfq: desktop con priorita sulla reattivita

NVMe (latenza molto bassa, parallelismo alto)
  → none: il controller NVMe e gia ottimizzato, lo scheduler aggiunge solo overhead
  → kyber: se serve target di latenza (es. mixed read/write workload)

VM (disco virtuale, lo scheduling e fatto dall'host)
  → mq-deadline o none: evitare double scheduling
```

---

## Gestione Dispositivi

### udev

udev e il gestore dei dispositivi in user space. Rileva automaticamente l'hardware (tramite eventi kernel via netlink), crea i nodi `/dev/`, carica i moduli necessari e applica regole personalizzate.

```bash
# Monitorare eventi udev in tempo reale
udevadm monitor                   # Tutti gli eventi
udevadm monitor --property        # Con proprieta

# Informazioni su un dispositivo
udevadm info /dev/sda             # Info complete
udevadm info --query=all --name=/dev/sda
udevadm info --attribute-walk --name=/dev/sda   # Catena di attributi (per scrivere regole)

# Testare una regola senza applicarla
udevadm test /sys/class/block/sda

# Ricaricare le regole
sudo udevadm control --reload-rules
sudo udevadm trigger              # Riesegui le regole sui device esistenti
```

### Scrivere regole udev

```bash
# Le regole vanno in /etc/udev/rules.d/ con prefisso numerico
# Formato: CONDIZIONE, CONDIZIONE, ..., AZIONE

# /etc/udev/rules.d/99-usb-backup.rules
# Quando si collega una specifica chiavetta USB, monta automaticamente
ACTION=="add", SUBSYSTEM=="block", ATTRS{idVendor}=="0781", \
  ATTRS{idProduct}=="5567", SYMLINK+="usb-backup", \
  RUN+="/usr/local/bin/auto-mount.sh"

# Regola per dare permessi a un gruppo
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="1234", \
  GROUP="plugdev", MODE="0660"

# Regola per nomi persistenti di interfacce di rete
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="aa:bb:cc:dd:ee:ff", \
  NAME="eth-lan"

# Chiavi di match (condizioni):
# ACTION        → add, remove, change
# SUBSYSTEM     → block, net, usb, input, ...
# KERNEL        → Nome kernel del device (sda, eth0, ...)
# ATTR{...}     → Attributo sysfs del device
# ATTRS{...}    → Attributo sysfs del device o dei parent
# ENV{...}      → Variabile d'ambiente

# Chiavi di assegnazione (azioni):
# NAME          → Rinomina il device
# SYMLINK       → Crea symlink in /dev/
# OWNER, GROUP  → Proprietario e gruppo
# MODE          → Permessi
# RUN           → Esegui comando
# IMPORT        → Importa variabili da programma
```

### Device mapper

Il device mapper e un framework kernel per la creazione di dispositivi a blocchi virtuali. E la base di LVM, LUKS, dm-raid, multipath.

```bash
# Dispositivi device mapper
ls /dev/mapper/
dmsetup ls                         # Lista dispositivi DM
dmsetup info                       # Info su tutti i DM
dmsetup table                      # Tabella di mapping

# LVM usa device mapper
lvs                                # Lista logical volume
pvs                                # Lista physical volume
vgs                                # Lista volume group

# LUKS usa device mapper
cryptsetup status luks-root        # Info dispositivo criptato
```

### sysfs e /dev

```bash
# /sys/ (sysfs) — interfaccia kernel-space per dispositivi, driver, moduli
/sys/class/                        # Dispositivi per classe (net, block, input)
/sys/block/                        # Dispositivi a blocchi
/sys/devices/                      # Albero dispositivi fisici
/sys/module/                       # Moduli kernel caricati
/sys/bus/                          # Bus (pci, usb, i2c, ...)
/sys/fs/                           # Filesystem speciali (cgroup, ext4, ...)
/sys/kernel/                       # Parametri kernel

# /dev/ — nodi dispositivo (creati da udev)
/dev/sda, /dev/nvme0n1             # Block device (disco)
/dev/tty*, /dev/pts/*              # Terminali
/dev/null, /dev/zero               # Dispositivi speciali
/dev/random, /dev/urandom          # Generatori di numeri casuali
/dev/loop*                         # Loopback devices
/dev/mapper/*                      # Device mapper (LVM, LUKS)

# Esempi di lettura sysfs
cat /sys/class/net/eth0/speed      # Velocita interfaccia di rete (Mbps)
cat /sys/class/net/eth0/address    # MAC address
cat /sys/block/sda/size            # Dimensione disco in settori
cat /sys/block/sda/queue/rotational # 1=HDD, 0=SSD
cat /sys/class/thermal/thermal_zone0/temp  # Temperatura CPU (milligradi)
```

---

## Sicurezza Kernel

Il kernel Linux implementa molteplici livelli di sicurezza per isolare processi, limitare privilegi e mitigare exploit.

### Capabilities

Le capabilities frammentano i privilegi di root in unita discrete. Invece di dare "tutti i privilegi" (root) o "nessun privilegio" (user), si possono assegnare solo le capabilities necessarie.

```bash
# Capabilities principali:
# CAP_NET_BIND_SERVICE  → Bind su porte < 1024
# CAP_NET_RAW           → Socket raw (ping, tcpdump)
# CAP_NET_ADMIN         → Configurazione rete
# CAP_SYS_ADMIN         → Catch-all amministrativo (mount, ioctl, ...)
# CAP_SYS_PTRACE        → ptrace() su qualsiasi processo
# CAP_DAC_OVERRIDE      → Bypassare permessi file
# CAP_CHOWN             → Cambiare proprietario file
# CAP_SETUID/SETGID     → Cambiare UID/GID
# CAP_SYS_TIME          → Modificare orologio di sistema
# CAP_KILL              → Inviare segnali a qualsiasi processo
# CAP_FOWNER            → Bypassare controlli proprietario
# CAP_SYS_RAWIO         → Accesso I/O diretto

# Visualizzare capabilities di un file
getcap /usr/bin/ping
# /usr/bin/ping cap_net_raw=ep

# Assegnare capabilities
sudo setcap cap_net_bind_service=ep /usr/local/bin/myserver
# Ora myserver puo fare bind su porta 80 senza root

# Rimuovere capabilities
sudo setcap -r /usr/local/bin/myserver

# Capabilities di un processo in esecuzione
cat /proc/PID/status | grep -i cap
# CapInh: 0000000000000000    → Inheritable
# CapPrm: 0000003fffffffff    → Permitted
# CapEff: 0000003fffffffff    → Effective
# CapBnd: 0000003fffffffff    → Bounding set
# CapAmb: 0000000000000000    → Ambient

# Decodificare il valore hex
capsh --decode=0000003fffffffff

# In systemd, limitare le capabilities di un servizio:
# [Service]
# CapabilityBoundingSet=CAP_NET_BIND_SERVICE CAP_NET_RAW
# AmbientCapabilities=CAP_NET_BIND_SERVICE
# NoNewPrivileges=true
```

### seccomp

seccomp (Secure Computing) limita le system call che un processo puo eseguire. Fondamentale per sandboxing (container, browser, servizi).

```bash
# seccomp ha due modalita:
# 1. SECCOMP_MODE_STRICT: solo read(), write(), exit(), sigreturn()
# 2. SECCOMP_MODE_FILTER (seccomp-bpf): filtro BPF personalizzato

# Attivazione programmatica:
# prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);

# Verificare se un processo usa seccomp
grep Seccomp /proc/PID/status
# Seccomp:  0  → disabilitato
# Seccomp:  1  → strict
# Seccomp:  2  → filter (seccomp-bpf)

# Docker usa seccomp-bpf per limitare le syscall dei container
# Profilo default Docker: ~300 syscall permesse su ~435 totali
docker inspect --format '{{.HostConfig.SecurityOpt}}' container_name

# Syscall bloccate di default da Docker seccomp:
# - mount, umount2 (mount filesystem)
# - reboot (reboot sistema)
# - swapon, swapoff (gestione swap)
# - kexec_load (caricamento nuovo kernel)
# - bpf (eBPF non privilegiato)
# - userfaultfd (usata in exploit)

# Testare syscall disponibili
seccomp-tools dump /usr/bin/ls     # Se installato (gem install seccomp-tools)

# In systemd:
# [Service]
# SystemCallFilter=@system-service     # Preset: syscall tipiche per servizi
# SystemCallFilter=~@mount @reboot     # Nega mount e reboot
# SystemCallErrorNumber=EPERM          # Errore restituito al processo
```

### Namespaces

I namespaces isolano risorse kernel per gruppi di processi. Sono il fondamento tecnologico dei container (Docker, Podman, LXC).

```bash
# Tipi di namespace:
# mnt      → Mount points (filesystem isolati)
# pid      → Process IDs (PID 1 nel container)
# net      → Network stack (interfacce, routing, iptables indipendenti)
# ipc      → IPC (shared memory, semafori, message queue)
# uts      → Hostname e NIS domain
# user     → UID/GID mapping (utente non-root nel container = root nel namespace)
# cgroup   → Cgroup root isolato
# time     → Orologi separati (kernel 5.6+)

# Visualizzare i namespace di un processo
ls -la /proc/PID/ns/
# lrwxrwxrwx 1 root root 0  → cgroup -> cgroup:[4026531835]
# lrwxrwxrwx 1 root root 0  → ipc -> ipc:[4026531839]
# lrwxrwxrwx 1 root root 0  → mnt -> mnt:[4026531840]
# lrwxrwxrwx 1 root root 0  → net -> net:[4026531992]
# lrwxrwxrwx 1 root root 0  → pid -> pid:[4026531836]
# lrwxrwxrwx 1 root root 0  → user -> user:[4026531837]
# lrwxrwxrwx 1 root root 0  → uts -> uts:[4026531838]

# Creare un processo in namespace isolati
unshare --mount --pid --fork --mount-proc bash
# Ora sei in un namespace mount+pid isolato

# Entrare nel namespace di un container
nsenter -t PID --all               # Tutti i namespace del PID
nsenter -t PID --net --pid         # Solo net e pid

# lsns — lista namespace del sistema
lsns                               # Tutti i namespace
lsns -t net                        # Solo namespace di rete
```

### AppArmor e SELinux

AppArmor e SELinux sono Linux Security Modules (LSM) che implementano Mandatory Access Control (MAC) — controlli di accesso obbligatori definiti dall'amministratore, che si aggiungono ai permessi DAC (user/group/other) standard.

```bash
# === APPARMOR (Ubuntu, Debian, SUSE) ===
# Verifica stato
sudo aa-status                     # Profili caricati, modalita (enforce/complain)
cat /sys/module/apparmor/parameters/enabled   # Y o N

# Modalita:
# enforce   → Regole applicate, violazioni bloccate e loggati
# complain  → Violazioni solo loggate (non bloccate)
# unconfined → Nessuna restrizione (profilo non attivo)

# Gestione profili
sudo aa-enforce /etc/apparmor.d/usr.sbin.nginx    # Modalita enforce
sudo aa-complain /etc/apparmor.d/usr.sbin.nginx   # Modalita complain
sudo aa-disable /etc/apparmor.d/usr.sbin.nginx    # Disabilita profilo

# Log violazioni
journalctl -k | grep apparmor
dmesg | grep apparmor

# === SELINUX (RHEL, Fedora, CentOS) ===
# Verifica stato
getenforce                         # Enforcing, Permissive, Disabled
sestatus                           # Stato dettagliato

# Cambiare modalita (temporaneo)
sudo setenforce 0                  # Permissive
sudo setenforce 1                  # Enforcing

# Cambiare modalita (persistente): /etc/selinux/config
# SELINUX=enforcing
# SELINUXTYPE=targeted

# Gestione contesti
ls -Z /var/www/html/               # Mostra contesto SELinux dei file
chcon -t httpd_sys_content_t /var/www/html/index.html   # Cambia contesto
restorecon -Rv /var/www/html/      # Ripristina contesto di default

# Boolean SELinux
getsebool -a | grep httpd          # Lista boolean per httpd
sudo setsebool -P httpd_can_network_connect on   # Persistente

# Log violazioni
ausearch -m AVC -ts recent         # Ultime violazioni
sealert -a /var/log/audit/audit.log # Analisi dettagliata (se installato)
```

### Landlock — Sandboxing Non Privilegiato

Landlock e un LSM (Linux Security Module) che permette a **processi non privilegiati** di limitare i propri diritti di accesso senza richiedere root o configurazione amministrativa. A differenza di AppArmor e SELinux, che sono policy globali gestite dall'amministratore, Landlock e progettato per l'auto-sandboxing delle applicazioni.

**Evoluzione delle capacita**:

| Kernel | ABI | Capacita aggiunta |
|--------|-----|-------------------|
| 5.13 | v1 | Restrizione accesso filesystem (lettura, scrittura, esecuzione) |
| 5.19 | v2 | Restrizione riferimento file (rename, link) |
| 6.2 | v3 | Troncamento file (`LANDLOCK_ACCESS_FS_TRUNCATE`) |
| 6.4 | v4 | Restrizione rete TCP (bind, connect su porte specifiche) |
| 6.7 | v5 | Restrizione segnali IOCTL |

**Principio di funzionamento**: il processo crea un **ruleset** che definisce cosa puo fare, poi lo applica a se stesso con `landlock_restrict_self()`. Da quel momento, il processo e tutti i suoi figli sono vincolati dalle regole — impossibile rimuoverle o allargarle.

```c
// Esempio semplificato: processo che si limita a leggere /usr e /tmp
struct landlock_ruleset_attr attr = {
    .handled_access_fs = LANDLOCK_ACCESS_FS_READ_FILE |
                         LANDLOCK_ACCESS_FS_READ_DIR  |
                         LANDLOCK_ACCESS_FS_EXECUTE,
};
int ruleset_fd = landlock_create_ruleset(&attr, sizeof(attr), 0);

// Aggiungere regola: accesso in lettura a /usr
struct landlock_path_beneath_attr path_attr = {
    .allowed_access = LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_EXECUTE,
    .parent_fd = open("/usr", O_PATH | O_CLOEXEC),
};
landlock_add_rule(ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, &path_attr, 0);

// Applicare restrizioni
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);  // Necessario
landlock_restrict_self(ruleset_fd, 0);
```

**Restrizioni rete (kernel >= 6.4)**:

```c
struct landlock_ruleset_attr attr = {
    .handled_access_net = LANDLOCK_ACCESS_NET_BIND_TCP |
                          LANDLOCK_ACCESS_NET_CONNECT_TCP,
};
// Permettere bind solo su porta 8080
struct landlock_net_port_attr net_attr = {
    .allowed_access = LANDLOCK_ACCESS_NET_BIND_TCP,
    .port = 8080,
};
landlock_add_rule(ruleset_fd, LANDLOCK_RULE_NET_PORT, &net_attr, 0);
```

**Strumenti pratici**:
- **`sandboxer`** (incluso nei sample del kernel): wrapper CLI per eseguire comandi con restrizioni Landlock
- **`ll-sandbox`**: libreria Go per integrare Landlock in applicazioni
- **Supporto in systemd**: `ProtectSystem=` e `ProtectHome=` usano Landlock internamente nelle versioni recenti

Landlock e complementare a seccomp: seccomp filtra le **syscall** permesse, Landlock filtra le **risorse** accessibili. Un'applicazione sicura puo usare entrambi.

---

## eBPF

eBPF (extended Berkeley Packet Filter) e una tecnologia che permette di eseguire programmi sandboxed nel kernel senza modificarlo o caricare moduli. E una delle innovazioni piu significative del kernel Linux degli ultimi anni.

### Architettura

```
User Space                           Kernel Space
┌──────────────┐                    ┌────────────────────────┐
│  BPF Program │  ──── load ────▶  │  BPF Verifier          │
│  (C/Rust →   │                    │  (verifica sicurezza,  │
│   bytecode)  │                    │   terminazione, bounds)│
└──────────────┘                    └────────┬───────────────┘
                                             │ JIT compile
┌──────────────┐                    ┌────────▼───────────────┐
│  BPF Maps    │  ◄── read ─────   │  Esecuzione nativa     │
│  (hash, array│                    │  (attach a tracepoint, │
│   ringbuf)   │                    │   kprobe, XDP, cgroup, │
│              │                    │   socket, ...)         │
└──────────────┘                    └────────────────────────┘
```

### Casi d'uso

- **Networking**: XDP (eXpress Data Path) — processing pacchetti prima dello stack TCP/IP, filtraggio ad alte prestazioni, load balancing (Cilium, Katran)
- **Tracing**: profilazione kernel e applicazioni, tracing di funzioni kernel (kprobe) e user space (uprobe), tracepoint
- **Sicurezza**: monitoraggio syscall, policy enforcement a runtime, LSM-BPF
- **Osservabilita**: metriche custom, aggregazione dati in-kernel, riduzione overhead rispetto a strumenti tradizionali

### bpftrace — esempi pratici

```bash
# Installazione
sudo apt install bpftrace          # Debian/Ubuntu
sudo dnf install bpftrace          # RHEL/Fedora

# Tracciare le aperture di file
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat {
    printf("%s %s\n", comm, str(args.filename));
}'

# Distribuzione latenza I/O per disco
sudo bpftrace -e 'tracepoint:block:block_rq_complete {
    @usecs = hist(args.nr_sector);
}'

# Contare syscall per processo
sudo bpftrace -e 'tracepoint:raw_syscalls:sys_enter {
    @[comm] = count();
}'

# Tracciare connessioni TCP (connect)
sudo bpftrace -e 'kprobe:tcp_connect {
    printf("%s connecting...\n", comm);
}'

# Monitorare OOM killer
sudo bpftrace -e 'kprobe:oom_kill_process {
    printf("OOM kill triggered by %s\n", comm);
}'

# Latenza read() per processo
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_read {
    @start[tid] = nsecs;
}
tracepoint:syscalls:sys_exit_read /@start[tid]/ {
    @read_ns[comm] = hist(nsecs - @start[tid]);
    delete(@start[tid]);
}'

# Contare page fault per processo
sudo bpftrace -e 'software:page-faults:1 {
    @[comm] = count();
}'
```

### BCC tools

```bash
# BCC (BPF Compiler Collection) — strumenti pre-costruiti basati su eBPF
sudo apt install bpfcc-tools       # Debian/Ubuntu
sudo dnf install bcc-tools         # RHEL/Fedora

# Strumenti principali (in /usr/share/bcc/tools/ o /usr/sbin/):
execsnoop-bpfcc                    # Traccia ogni exec() (nuovi processi)
opensnoop-bpfcc                    # Traccia ogni open() (file aperti)
biolatency-bpfcc                   # Istogramma latenza I/O blocchi
biosnoop-bpfcc                     # Traccia ogni I/O a blocchi
tcpconnect-bpfcc                   # Traccia connessioni TCP in uscita
tcpaccept-bpfcc                    # Traccia connessioni TCP in ingresso
tcplife-bpfcc                      # Vita delle connessioni TCP
funccount-bpfcc                    # Conta chiamate a funzioni kernel
stackcount-bpfcc                   # Conta stack trace
ext4slower-bpfcc                   # Operazioni ext4 lente
runqlat-bpfcc                      # Latenza run queue (tempo attesa CPU)
cachestat-bpfcc                    # Hit/miss page cache
```

### eBPF LSM — Sicurezza Programmabile

A partire dal kernel 5.7, eBPF puo agganciarsi direttamente ai **LSM hooks** (Linux Security Module) tramite il tipo di programma `BPF_PROG_TYPE_LSM`. Questo permette di implementare policy di sicurezza personalizzate senza scrivere moduli kernel, con la garanzia del verificatore eBPF che il programma non possa crashare il sistema.

Casi d'uso principali:
- Bloccare esecuzione di binari non firmati
- Impedire mount di filesystem in container
- Audit granulare di operazioni privilegiate
- Policy di accesso file basate su cgroup o namespace

```bash
# Abilitare BPF LSM (deve essere nella lista lsm= al boot)
# In /etc/default/grub:
GRUB_CMDLINE_LINUX="lsm=landlock,lockdown,yama,integrity,apparmor,bpf"

# Verificare
cat /sys/kernel/security/lsm
# Output include: ...apparmor,bpf
```

### CO-RE — Compile Once, Run Everywhere

CO-RE (Compile Once, Run Everywhere) risolve il problema storico di eBPF: i programmi dovevano essere ricompilati per ogni versione di kernel perche gli offset delle strutture dati cambiano. CO-RE combina tre tecnologie:

1. **BTF** (BPF Type Format): metadati di tipo embeddati nel kernel (`CONFIG_DEBUG_INFO_BTF=y`)
2. **libbpf**: libreria che usa BTF per ricalcolare gli offset a runtime
3. **BPF skeleton**: header generato da `bpftool gen skeleton` che integra il bytecode BPF

```bash
# Verificare supporto BTF
ls /sys/kernel/btf/vmlinux       # Presente = BTF abilitato
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# Compilare programma CO-RE
clang -g -O2 -target bpf -D__TARGET_ARCH_x86 \
  -I/usr/include -c prog.bpf.c -o prog.bpf.o
bpftool gen skeleton prog.bpf.o > prog.skel.h
```

### Ecosistema eBPF in Produzione

L'ecosistema eBPF si e evoluto da strumento di osservabilita a piattaforma completa per networking, sicurezza e runtime enforcement:

| Progetto | Funzione | Uso principale |
|----------|----------|---------------|
| **Cilium** | CNI per Kubernetes | Networking, service mesh, network policy senza iptables |
| **Tetragon** | Runtime security | Enforcement policy a livello kernel, process tree tracking |
| **Falco** (con eBPF probe) | Threat detection | Rilevamento anomalie syscall in tempo reale |
| **Tracee** (Aqua Security) | Security tracing | Rilevamento comportamenti sospetti basato su eventi kernel |
| **Pixie** | Observability | Auto-instrumentazione applicazioni senza modifiche al codice |
| **Katran** | Load balancer L4 | XDP-based, usato da Meta per gestire milioni di connessioni/sec |
| **bpftrace** | One-liner tracing | Script ad-hoc per debug e performance analysis |

**Cilium** ha sostituito kube-proxy in molti cluster Kubernetes di produzione. Usa eBPF per implementare service routing, network policy e load balancing direttamente nel datapath del kernel, eliminando le catene iptables. In cluster con >10.000 servizi, Cilium riduce la latenza di routing del 30-50% rispetto a iptables.

**Tetragon** esegue policy di sicurezza direttamente nei hook eBPF del kernel. Puo bloccare in tempo reale: esecuzione di binari non autorizzati, connessioni di rete verso destinazioni vietate, accesso a file sensibili. A differenza degli agent userspace (come i tradizionali HIDS), Tetragon agisce prima che il processo veda il risultato della syscall.

```bash
# bpftrace — esempi avanzati
# Latenza di ogni syscall read per processo
bpftrace -e 'tracepoint:syscalls:sys_enter_read { @start[tid] = nsecs; }
              tracepoint:syscalls:sys_exit_read /@start[tid]/ {
                @us[comm] = hist((nsecs - @start[tid]) / 1000);
                delete(@start[tid]);
              }'

# Top 10 processi per allocazioni kernel (kmalloc)
bpftrace -e 'tracepoint:kmem:kmalloc { @bytes[comm] = sum(args->bytes_alloc); }
              interval:s:5 { print(@bytes, 10); clear(@bytes); }'
```

---

## Kernel Debugging

### dmesg

Il ring buffer del kernel contiene tutti i messaggi del kernel dall'avvio. E il primo strumento da consultare per qualsiasi problema hardware, driver o kernel.

```bash
# Visualizzare messaggi
dmesg                              # Tutti i messaggi
dmesg -T                           # Con timestamp leggibili
dmesg -H                           # Paginato e colorato (human readable)
dmesg --level=err,warn             # Solo errori e warning
dmesg -T --level=err               # Solo errori con timestamp

# Filtrare per facility
dmesg -f kern                      # Solo messaggi kernel
dmesg -f daemon                    # Solo daemon

# Seguire in tempo reale
dmesg -w                           # Watch mode (come tail -f)
dmesg -wT                          # Watch con timestamp

# Cancellare il ring buffer (dopo averlo salvato!)
dmesg > /tmp/dmesg-backup.txt
sudo dmesg -C                     # Clear

# Dimensione ring buffer
cat /proc/sys/kernel/printk        # current default minimum boot-time-default
# Aumentare: aggiungere log_buf_len=16M ai parametri kernel in GRUB

# Livelli di log (0=piu critico, 7=debug):
# 0 KERN_EMERG     → Sistema inutilizzabile
# 1 KERN_ALERT     → Azione immediata richiesta
# 2 KERN_CRIT      → Condizione critica
# 3 KERN_ERR       → Errore
# 4 KERN_WARNING   → Warning
# 5 KERN_NOTICE    → Normale ma significativo
# 6 KERN_INFO      → Informativo
# 7 KERN_DEBUG     → Debug
```

### ftrace

ftrace e il tracing framework integrato nel kernel. Permette di tracciare funzioni kernel, eventi, latenze, context switch senza strumenti esterni.

```bash
# ftrace opera tramite /sys/kernel/debug/tracing/ (o /sys/kernel/tracing/)
FTRACE=/sys/kernel/tracing

# Verificare i tracer disponibili
cat $FTRACE/available_tracers
# hwlat blk mmiotrace function_graph wakeup_dl wakeup_rt wakeup function nop

# === Function tracer ===
echo function | sudo tee $FTRACE/current_tracer
echo 1 | sudo tee $FTRACE/tracing_on
# ... eseguire il workload da tracciare ...
echo 0 | sudo tee $FTRACE/tracing_on
cat $FTRACE/trace | head -100

# Filtrare per funzioni specifiche
echo "ext4_*" | sudo tee $FTRACE/set_ftrace_filter
echo function | sudo tee $FTRACE/current_tracer
echo 1 | sudo tee $FTRACE/tracing_on

# === Function graph tracer (call tree) ===
echo function_graph | sudo tee $FTRACE/current_tracer
echo "do_sys_openat2" | sudo tee $FTRACE/set_graph_function
echo 1 | sudo tee $FTRACE/tracing_on
cat /dev/null                      # Trigger una open()
echo 0 | sudo tee $FTRACE/tracing_on
cat $FTRACE/trace

# Reset
echo nop | sudo tee $FTRACE/current_tracer
echo | sudo tee $FTRACE/set_ftrace_filter

# === trace-cmd (frontend per ftrace) ===
sudo trace-cmd record -p function_graph -g do_sys_openat2 -- ls /tmp
sudo trace-cmd report | head -50
```

### perf

perf e lo strumento di profilazione principale del kernel Linux. Usa i contatori hardware (PMU) e i tracepoint software per profilare CPU, cache, branch prediction, I/O.

```bash
# Installazione
sudo apt install linux-tools-$(uname -r)   # Debian/Ubuntu
sudo dnf install perf                       # RHEL/Fedora

# Profilare un comando
sudo perf stat ls /tmp             # Contatori hardware (cycle, instructions, cache-misses)
sudo perf stat -d ./my-app         # Con dettaglio cache e branch

# Profilare CPU di sistema per 10 secondi
sudo perf record -g -a -- sleep 10
sudo perf report                   # Visualizzare i risultati (TUI interattiva)
sudo perf report --stdio           # Versione testuale

# Top dei processi per CPU (real-time)
sudo perf top                      # Come top, ma con simboli kernel
sudo perf top -p PID               # Solo un processo

# Flamegraph
sudo perf record -g -a -- sleep 30
sudo perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg

# Contare eventi specifici
sudo perf stat -e cache-misses,cache-references,instructions,cycles ./my-app

# Tracciare syscall (alternativa a strace, meno overhead)
sudo perf trace ls /tmp
sudo perf trace -p PID             # Processo esistente

# Lista eventi disponibili
sudo perf list                     # Centinaia di eventi (hardware, software, tracepoint)
```

### kdump e crash dumps

kdump cattura un dump della memoria kernel (vmcore) quando si verifica un kernel panic. Permette analisi post-mortem con il tool `crash`.

```bash
# Installazione
sudo apt install kdump-tools crash   # Debian/Ubuntu
sudo dnf install kexec-tools crash   # RHEL/Fedora

# kdump funziona cosi:
# 1. Al boot, il kernel principale riserva memoria per un "capture kernel"
# 2. In caso di panic, kexec avvia il capture kernel nella memoria riservata
# 3. Il capture kernel monta il disco e salva il vmcore
# 4. Il sistema si riavvia

# Configurazione: riservare memoria per il capture kernel
# In GRUB_CMDLINE_LINUX:
# crashkernel=256M                  # Riserva 256 MB per kdump
# crashkernel=256M,high             # Per sistemi con > 4GB RAM

# Verificare che kdump sia attivo
systemctl status kdump             # Stato servizio
cat /proc/cmdline | grep crashkernel   # Memoria riservata

# Configurazione dump: /etc/kdump.conf (RHEL) o /etc/default/kdump-tools (Debian)
# path /var/crash                  # Directory per i dump
# core_collector makedumpfile -l --message-level 1 -d 31

# Testare kdump (ATTENZIONE: causa un crash reale!)
# echo c | sudo tee /proc/sysrq-trigger   # Trigger kernel panic

# Analisi post-mortem
sudo crash /usr/lib/debug/boot/vmlinux-$(uname -r) /var/crash/vmcore
# crash> bt         → Backtrace del crash
# crash> log        → Dmesg al momento del crash
# crash> ps         → Processi al momento del crash
# crash> vm PID     → Memoria del processo
# crash> files PID  → File aperti dal processo
# crash> quit       → Uscire
```

---

## Kernel Live Patching

Il live patching permette di applicare patch di sicurezza al kernel senza riavviare il sistema. Essenziale per server con SLA elevati (uptime 99.99%+).

### kpatch (RHEL/CentOS)

```bash
# kpatch e sviluppato da Red Hat per RHEL/CentOS
# I patch sono disponibili con subscription RHEL

# Installazione
sudo dnf install kpatch kpatch-dnf

# Verificare patch disponibili
sudo kpatch list                   # Patch installate
sudo dnf list available kpatch-patch-* # Patch disponibili

# Applicare un patch
sudo dnf install kpatch-patch-6_6_0-1
sudo kpatch load kpatch_6_6_0_1   # Caricamento manuale

# Verificare
sudo kpatch list
# Loaded patch modules:
#   kpatch_6_6_0_1 [enabled]

# kpatch opera tramite ftrace: redirige le chiamate alle funzioni
# patchate verso le versioni corrette
```

### Ubuntu Pro Livepatch

```bash
# Livepatch e il servizio Canonical per Ubuntu Pro/Server

# Abilitare (richiede token Ubuntu Pro)
sudo pro attach TOKEN
sudo pro enable livepatch

# Oppure standalone:
sudo snap install canonical-livepatch
sudo canonical-livepatch enable TOKEN

# Stato
canonical-livepatch status --verbose

# I livepatch vengono applicati automaticamente
# Nessun riavvio necessario per patch di sicurezza
```

### Confronto

| Caratteristica | kpatch (RHEL) | Livepatch (Ubuntu) |
|---|---|---|
| Prerequisito | RHEL subscription | Ubuntu Pro |
| Meccanismo | ftrace function redirect | ftrace function redirect |
| Applicazione | Manuale o dnf | Automatica (snap daemon) |
| Scope | Solo patch di sicurezza | Solo patch di sicurezza |
| Limitazioni | Non puo patchare cambi struttura dati | Idem |
| Rollback | `kpatch unload` | Automatico |

**Limitazione importante**: il live patching puo correggere solo funzioni. Non puo modificare strutture dati kernel, aggiungere nuove syscall, o cambiare layout di strutture. Per questi cambiamenti, il reboot resta necessario.

### Workflow Creazione Patch con kpatch

Il processo di creazione di una live patch con kpatch-build automatizza la generazione del modulo `.ko` partendo da un diff del sorgente kernel:

```bash
# Installare kpatch-build (RHEL/Fedora)
sudo dnf install kpatch-build

# Creare una patch dal diff
kpatch-build -s /usr/src/kernels/$(uname -r) \
  --vmlinux /usr/lib/debug/lib/modules/$(uname -r)/vmlinux \
  security-fix.patch

# Output: livepatch-security-fix.ko

# Caricare la patch
sudo kpatch load livepatch-security-fix.ko

# Verificare stato
kpatch list
# Loaded patch modules:
# livepatch-security-fix [enabled]

# Rendere persistente (sopravvive reboot fino a nuovo kernel)
sudo kpatch install livepatch-security-fix.ko
# Copia in /var/lib/kpatch/$(uname -r)/ e crea unit systemd
```

**Meccanismo interno (ftrace)**: kpatch registra un handler ftrace per ogni funzione patchata. Quando il kernel chiama la funzione originale, ftrace intercetta l'entry point e redirige l'esecuzione alla versione corretta. Il processo di transizione e **consistency model**: kpatch attende che tutti i task escano dalla funzione originale prima di attivare il redirect, garantendo che nessun task esegua un mix di codice vecchio e nuovo.

**Matrice decisionale — Live Patch vs Reboot**:

| Scenario | Live Patch | Reboot |
|----------|-----------|--------|
| CVE con fix in una singola funzione | Si | Non necessario |
| Aggiornamento versione kernel | No | Necessario |
| Fix che modifica struttura dati (struct) | No | Necessario |
| Fix urgente in produzione (SLA critico) | Si (preferito) | Ultima risorsa |
| Accumulo di >5 live patch | Valutare reboot | Consigliato |

**Monitoraggio in produzione**:

```bash
# Stato moduli live patching
cat /sys/kernel/livepatch/*/enabled     # 1 = attivo
cat /sys/kernel/livepatch/*/transition  # 1 = transizione in corso

# Log
dmesg | grep livepatch
# livepatch: enabling patch 'livepatch-security-fix'
# livepatch: 'livepatch-security-fix': patching complete
```

---

## Tuning Kernel per Performance

### Server Web/Application

```bash
# /etc/sysctl.d/90-webserver.conf
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_keepalive_time = 300
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
fs.file-max = 2097152
vm.swappiness = 10
```

### Server Database

```bash
# /etc/sysctl.d/90-database.conf
vm.swappiness = 1                  # Quasi zero swap
vm.dirty_ratio = 40                # Permetti piu dirty page (database gestiscono il flush)
vm.dirty_background_ratio = 10
vm.overcommit_memory = 2           # No overcommit (PostgreSQL)
vm.overcommit_ratio = 80
kernel.shmmax = 17179869184        # 16GB shared memory
kernel.shmall = 4194304
fs.file-max = 2097152
fs.aio-max-nr = 1048576            # Async I/O per database
net.core.somaxconn = 4096
net.ipv4.tcp_keepalive_time = 300

# Transparent Huge Pages: DISABILITARE per database!
# /etc/systemd/system/disable-thp.service o via kernel cmdline:
# transparent_hugepage=never
```

### Server Virtualizzazione (KVM/QEMU)

```bash
# /etc/sysctl.d/90-virtualization.conf
vm.swappiness = 1
vm.dirty_ratio = 40
vm.dirty_background_ratio = 5
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
kernel.shmmax = 34359738368        # 32GB
fs.file-max = 2097152
# KSM (Kernel Same-page Merging) per VM:
# echo 1 | sudo tee /sys/kernel/mm/ksm/run
```

### Server Container (Kubernetes/Docker)

```bash
# /etc/sysctl.d/90-container.conf
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
net.ipv4.conf.all.forwarding = 1
net.ipv6.conf.all.forwarding = 1
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 1024
fs.file-max = 2097152
net.core.somaxconn = 65535
kernel.pid_max = 4194304           # Molti container = molti PID
vm.max_map_count = 262144          # Per Elasticsearch
net.netfilter.nf_conntrack_max = 1048576   # Molte connessioni
```

### Desktop / Workstation

```bash
# /etc/sysctl.d/90-desktop.conf
vm.swappiness = 10                 # Meno swap, piu reattivita
vm.vfs_cache_pressure = 50         # Mantieni cache filesystem
vm.dirty_ratio = 10                # Flush frequente (perdita dati minimizzata)
vm.dirty_background_ratio = 5
kernel.sched_autogroup_enabled = 1 # Autogroup per interattivita
fs.inotify.max_user_watches = 524288   # Per IDE e file manager
```

### Tuning Rete ad Alta Banda (10G/25G/100G)

Per server con NIC ad alta velocita, i buffer TCP di default (tipicamente 128K-4M) diventano il collo di bottiglia. Il **bandwidth-delay product** (BDP) determina la dimensione ottimale dei buffer: per una connessione 100 Gbps con 10ms RTT, il BDP e ~125 MB.

```bash
# /etc/sysctl.d/91-highbandwidth.conf

# Buffer TCP — dimensionati per 100G
net.core.rmem_max = 536870912          # 512M — massimo buffer ricezione
net.core.wmem_max = 536870912          # 512M — massimo buffer invio
net.core.rmem_default = 16777216       # 16M default
net.core.wmem_default = 16777216
net.ipv4.tcp_rmem = 4096 1048576 536870912   # min 4K, default 1M, max 512M
net.ipv4.tcp_wmem = 4096 1048576 536870912
net.core.netdev_max_backlog = 30000    # Coda pacchetti in ingresso
net.core.somaxconn = 65535             # Backlog listen()

# Congestion control — BBR + fq
net.ipv4.tcp_congestion_control = bbr  # Bottleneck Bandwidth & RTT
net.core.default_qdisc = fq           # Fair Queueing (necessario per BBR)
# BBR v3 (kernel 6.x): migliore equita con flussi Reno/CUBIC

# SYN flood protection
net.ipv4.tcp_max_syn_backlog = 8192   # Coda SYN per listener ad alto traffico
net.ipv4.tcp_syncookies = 1           # SYN cookies (protezione DDoS)
net.ipv4.tcp_tw_reuse = 1             # Riuso porte TIME_WAIT

# Busy polling — riduce latenza a costo di CPU
net.core.busy_read = 50               # Microsecondi di busy-poll su read
net.core.busy_poll = 50               # Microsecondi di busy-poll su poll/select

# Ottimizzazioni generali alta banda
net.ipv4.tcp_fastopen = 3             # TFO client + server
net.ipv4.tcp_mtu_probing = 1          # MTU probing per jumbo frame
net.ipv4.tcp_no_metrics_save = 1      # Non cachare metriche TCP stale
net.ipv4.tcp_slow_start_after_idle = 0 # No slow start dopo idle
```

**Configurazione NIC per 100G**:

```bash
# Ring buffer — aumentare per ridurre packet drop
ethtool -G eth0 rx 8192 tx 8192

# Interrupt coalescing — batch interrupt per ridurre overhead
ethtool -C eth0 adaptive-rx on adaptive-tx on

# RSS — Receive Side Scaling (distribuire interrupt su piu CPU)
ethtool -L eth0 combined 16           # 16 code hardware

# XPS — Transmit Packet Steering
# Assegnare CPU 0-7 alla coda TX
echo "ff" > /sys/class/net/eth0/queues/tx-0/xps_cpus

# Verificare configurazione
ethtool -S eth0 | grep -E "drop|error|miss"
# Se rx_dropped > 0: aumentare ring buffer o backlog
```

**BBR vs CUBIC**: BBR (Bottleneck Bandwidth and Round-trip propagation time) stima attivamente la banda disponibile e il RTT minimo, invece di reagire alla perdita di pacchetti come CUBIC. Su link con >1% packet loss, BBR mantiene ~80% del throughput massimo dove CUBIC scende a <10%. BBR v3 (kernel 6.x) migliora l'equita con flussi concorrenti e aggiunge supporto ECN.

### Limiti Utente (/etc/security/limits.conf)

```bash
# /etc/security/limits.conf o /etc/security/limits.d/99-custom.conf
*    soft    nofile    65536          # File descriptor (soft)
*    hard    nofile    131072         # File descriptor (hard)
*    soft    nproc     65536          # Processi
*    hard    nproc     131072

# Per utente specifico
postgres  soft  nofile  65536
postgres  hard  nofile  131072

# Per processi real-time
audio     -  rtprio     95
audio     -  memlock    unlimited

# Verificare
ulimit -n                          # File descriptor corrente
ulimit -a                          # Tutti i limiti
cat /proc/PID/limits               # Limiti di un processo specifico
```

### Checklist per workload

**Pre-tuning (SEMPRE):**
- [ ] Raccogliere baseline con `vmstat 1`, `iostat -x 1`, `sar`
- [ ] Documentare i valori correnti: `sysctl -a > /tmp/sysctl-baseline.txt`
- [ ] Identificare il collo di bottiglia PRIMA di applicare tuning

**Web server:**
- [ ] `somaxconn` e `tcp_max_syn_backlog` adeguati al carico
- [ ] `tcp_fin_timeout` ridotto (15-30 sec)
- [ ] BBR abilitato come congestion control
- [ ] `file-max` sufficiente per connessioni simultanee
- [ ] Limiti ulimit adeguati per l'utente del web server

**Database:**
- [ ] `swappiness` a 0-1
- [ ] `overcommit_memory=2` per PostgreSQL
- [ ] THP disabilitato
- [ ] Huge pages allocate e configurate
- [ ] Scheduler I/O ottimale per il tipo di disco

**Container/Kubernetes:**
- [ ] IP forwarding abilitato
- [ ] Bridge netfilter abilitato
- [ ] `pid_max` aumentato
- [ ] `inotify` watches sufficienti
- [ ] `nf_conntrack_max` adeguato

**Post-tuning (SEMPRE):**
- [ ] Verificare che i parametri siano effettivi: `sysctl parametro`
- [ ] Benchmark comparativo con baseline
- [ ] Test di stabilita sotto carico
- [ ] Documentare i cambiamenti e il razionale

---

## Best Practices

1. **Non compilare kernel in produzione**: compilare in ambiente di test, poi distribuire. In produzione, usare i kernel della distribuzione con eventuali backport di sicurezza

2. **sysctl incrementale**: creare file numerati in `/etc/sysctl.d/` (es. `90-networking.conf`, `91-security.conf`) anziche modificare `/etc/sysctl.conf`

3. **DKMS per moduli terzi**: usare sempre DKMS per moduli non upstream. Garantisce la ricompilazione automatica ad ogni aggiornamento kernel

4. **Blacklist documentata**: ogni modulo in blacklist deve avere un commento che spiega perche e stato bloccato e la data della decisione

5. **Monitorare dmesg**: `dmesg -T --level=err,warn` per errori kernel. Automatizzare con alert. Integrare con journald/rsyslog per persistenza

6. **Backup prima del tuning**: salvare i parametri sysctl correnti prima di applicare modifiche. Un parametro sbagliato puo rendere il sistema instabile o irraggiungibile via rete

7. **Kernel LTS in produzione**: usare sempre kernel LTS (Long Term Support) in produzione. Le versioni non-LTS hanno ciclo di vita di ~3 mesi

8. **Mantenere il kernel precedente**: non rimuovere mai l'ultimo kernel funzionante. GRUB permette di selezionare un kernel precedente in caso di regressione

9. **Aggiornamenti kernel regolari**: applicare aggiornamenti di sicurezza entro 72 ore dalla disclosure. Usare live patching se il reboot non e possibile

10. **cgroups per isolamento risorse**: usare cgroups v2 (via systemd) per limitare CPU, memoria e I/O per ogni servizio. Previene che un servizio impazzito consumi tutte le risorse

11. **Secure boot su server**: abilitare Secure Boot con UEFI per prevenire bootkit e rootkit che modificano il kernel o l'initramfs

12. **Hardening sysctl**: applicare un baseline di sicurezza sysctl (ASLR, kptr_restrict, dmesg_restrict, yama ptrace_scope) su tutti i server

---

## Troubleshooting

**"Kernel panic — not syncing: VFS: Unable to mount root fs"** → Il kernel non riesce a montare il root filesystem. Cause: initramfs corrotto o mancante dei driver necessari, UUID sbagliato in GRUB, driver controller disco non presente. Fix: avviare da un kernel precedente (menu GRUB), verificare UUID con `blkid`, rigenerare initramfs (`update-initramfs -u` o `dracut --force`).

**"Kernel panic — not syncing: Attempted to kill init!"** → PID 1 (systemd/init) e crashato. Cause: filesystem root corrotto, librerie condivise danneggiate, errore systemd critico. Fix: avviare con `init=/bin/bash` nei parametri GRUB, eseguire `fsck` sul root filesystem, verificare `/sbin/init` e le librerie.

**"Kernel Oops"** → Errore kernel non fatale (puo continuare a funzionare). Un oops indica un bug nel kernel o in un modulo. `dmesg | grep -A 20 "Oops"` per il backtrace. Se ripetuto, identificare il modulo colpevole dal backtrace e aggiornarlo o rimuoverlo.

**"BUG: soft lockup — CPU#X stuck for XXs!"** → Una CPU e bloccata in kernel space senza cedere per troppo tempo (default 22 secondi). Cause: loop infinito nel kernel, driver buggato, interrupt storm. Verificare `dmesg` per identificare la funzione bloccata. Possibile workaround temporaneo: `sysctl kernel.softlockup_panic=0`.

**"BUG: workqueue lockup — pool is stuck"** → Un work queue del kernel e bloccato. Simile al soft lockup ma specifico per i work queue. Tipicamente causato da un driver o un sottosistema che blocca un worker thread.

**"Modulo non si carica (modprobe: FATAL: Module not found)"** → `modprobe -v modulo` per output dettagliato. Cause: modulo non compilato per questo kernel (`ls /lib/modules/$(uname -r)/`), dipendenza mancante (`depmod -a`), in blacklist (`grep -r modulo /etc/modprobe.d/`), header non installati per DKMS.

**"module: disagrees about version of symbol"** → Mismatch vermagic: il modulo e stato compilato per una versione diversa del kernel. Fix: ricompilare il modulo per il kernel corrente, usare DKMS, o installare la versione corretta del modulo. `modinfo modulo | grep vermagic` per verificare.

**"OOM killer termina processi"** → Memoria insufficiente. `dmesg | grep -i oom` per dettagli. Soluzioni: aggiungere RAM, aumentare swap, configurare `vm.overcommit_memory`, aumentare `vm.min_free_kbytes`, limitare memoria per servizio con systemd (`MemoryMax=`). Verificare quale processo consuma piu memoria: `ps aux --sort=-%mem | head -10`.

**"Too many open files"** → Limite file descriptor raggiunto. Per processo: `ulimit -n` (aumentare in limits.conf). Per sistema: `sysctl fs.file-max`. Verificare: `cat /proc/sys/fs/file-nr` (usati / 0 / massimo). Per un servizio systemd: `LimitNOFILE=65536` nella unit file.

**"sysctl: permission denied"** → Usare `sudo`. Se con sudo fallisce: il parametro potrebbe non essere scrivibile (read-only a runtime) o il kernel non supporta quella funzionalita. Verificare con `sysctl -a | grep parametro`.

**"GRUB: error: no such partition"** → GRUB non trova la partizione. Cause: UUID cambiato (dopo ridimensionamento/sostituzione disco), disco rimosso. Fix: avviare da USB live, montare root, verificare `/etc/fstab` e `/etc/default/grub`, eseguire `update-grub`.

**"systemd-modules-load: Failed to find module 'xxx'"** → Un modulo elencato in `/etc/modules-load.d/` non esiste. Causa: modulo rimosso dal kernel aggiornato, typo nel nome. Fix: verificare il nome con `modinfo xxx`, rimuovere o correggere il file in `/etc/modules-load.d/`.

**"nvidia: version magic mismatch"** → Driver NVIDIA compilato per un kernel diverso. Fix: `sudo dkms autoinstall` per ricompilare, oppure reinstallare il driver NVIDIA. Verificare con `dkms status`.

**"Kernel tainted"** → Il kernel e stato "contaminato" da un modulo non-GPL, un firmware proprietario, o un'azione amministrativa. `cat /proc/sys/kernel/tainted` restituisce un bitmask. Non e necessariamente un problema, ma i report di bug kernel con tainted kernel hanno priorita minore. Flag comuni: P=proprietary module, F=firmware bug, W=warning.

**"hung_task_timeout_secs: blocked for more than N seconds"** → Un task e in stato D (uninterruptible sleep) troppo a lungo. Tipicamente I/O bloccato (NFS timeout, disco guasto, LUKS che aspetta password). `cat /proc/PID/wchan` per vedere dove e bloccato. Aumentare il timeout: `sysctl kernel.hung_task_timeout_secs=300`.

**"irq XX: nobody cared"** → Un interrupt hardware non viene gestito da nessun driver. Causa: driver mancante, conflitto IRQ, hardware difettoso. `cat /proc/interrupts` per vedere la distribuzione degli interrupt.

**"ACPI Error"** → Errori nel firmware ACPI della scheda madre. Spesso non fatali ma fastidiosi. `dmesg | grep -i acpi`. Workaround: `acpi_osi="Windows 2020"` nei parametri GRUB (forza il BIOS a esporre tabelle ACPI per Windows, spesso piu testate).

**"EDAC: error"** → Errori di memoria (ECC Error Detection And Correction). Indicano RAM difettosa. `edac-util -s` per il sommario. Se gli errori sono ricorrenti, sostituire il modulo RAM indicato.

**"PCIe Bus Error: severity=Corrected/Uncorrected"** → Errori sul bus PCIe. Corrected = hardware ha corretto, informativo. Uncorrected = potenziale problema. Cause: slot PCIe sporco, scheda non ben inserita, hardware difettoso. Provare: risedere la scheda, aggiornare firmware/BIOS.

**"RCU stall detected"** → Un task sta impedendo la quiescenza RCU (Read-Copy-Update). Indica un loop stretto nel kernel senza punti di preemption. Grave — puo portare a lockup. Analizzare il backtrace in dmesg per identificare il colpevole.

**"clocksource: timekeeping watchdog: Marking clocksource 'tsc' as unstable"** → Il TSC (Time Stamp Counter) e instabile. Comune su VM o hardware con CPU frequency scaling problematico. Il kernel passa a un clocksource alternativo (hpet, acpi_pm). Non critico ma puo impattare le prestazioni. Fix per VM: `clocksource=kvm-clock` nei parametri kernel.

**"EXT4-fs error: device sdX: comm: checksum error"** → Errore di checksum su filesystem ext4. Indica corruzione. Fix: `sudo fsck.ext4 -f /dev/sdX` (da filesystem smontato o rescue mode). Verificare anche la salute del disco con `smartctl -a /dev/sdX`.

---

## FAQ

**D: Come verificare quale versione del kernel e in uso?**
R: `uname -r` mostra solo la versione. `uname -a` mostra versione, architettura, data di compilazione, hostname. `cat /proc/version` include anche il compilatore usato.

**D: Posso avere piu kernel installati contemporaneamente?**
R: Si, e altamente raccomandato. GRUB mostra tutti i kernel installati nel menu di avvio (Advanced options). Mantenere almeno il kernel precedente funzionante come fallback. Le distribuzioni tipicamente mantengono 2-3 kernel.

**D: Qual e la differenza tra `insmod` e `modprobe`?**
R: `insmod` carica un modulo dal path esatto senza risolvere dipendenze — se il modulo dipende da altri non caricati, fallisce. `modprobe` cerca il modulo in `/lib/modules/$(uname -r)/`, risolve e carica automaticamente tutte le dipendenze, e rispetta le opzioni in `/etc/modprobe.d/`. Usare sempre `modprobe`.

**D: Come disabilitare un modulo kernel permanentemente?**
R: Aggiungerlo in `/etc/modprobe.d/blacklist-custom.conf` con `blacklist modulo`. Per impedire anche il caricamento indiretto (da dipendenze): `install modulo /bin/false`. Poi rigenerare initramfs (`update-initramfs -u` o `dracut --force`).

**D: vm.swappiness=0 disabilita lo swap?**
R: No. Con `swappiness=0` il kernel preferira fortemente evitare lo swap, ma lo usera comunque in caso di pressione di memoria critica. Per disabilitare realmente lo swap: `swapoff -a` (temporaneo) oppure rimuovere la voce swap da `/etc/fstab` e commentare/rimuovere il file/partizione swap.

**D: Quando usare `vm.overcommit_memory=2`?**
R: Per database (specialmente PostgreSQL) e applicazioni che non tollerano OOM kill. Con mode 2, `malloc()` fallisce quando il sistema supera il commit limit (`RAM * overcommit_ratio/100 + swap`), invece di promettere memoria che non c'e. L'applicazione gestisce il fallimento malloc() gracefully invece di essere terminata dall'OOM killer.

**D: Come cambio lo scheduler I/O?**
R: Temporaneamente: `echo bfq | sudo tee /sys/block/sda/queue/scheduler`. Permanentemente: creare una regola udev in `/etc/udev/rules.d/60-io-scheduler.rules`. Lo scheduler corretto dipende dal tipo di disco: `none` per NVMe, `mq-deadline` per SSD SATA e HDD, `bfq` per desktop interattivi.

**D: Cos'e il kernel tainted e devo preoccuparmi?**
R: Il flag tainted indica che il kernel esegue codice non verificabile dalla community (driver proprietari come NVIDIA, moduli out-of-tree). Non e un errore di per se, ma i bug report kernel con taint flag hanno minore priorita. `cat /proc/sys/kernel/tainted` — se il valore e 0, il kernel e "puro".

**D: Come ottenere un core dump da un kernel panic?**
R: Configurare kdump: installare `kexec-tools`, aggiungere `crashkernel=256M` ai parametri kernel in GRUB, riavviare. Al prossimo panic, il dump verra salvato (tipicamente in `/var/crash/`). Analizzare con `crash vmlinux vmcore`.

**D: Posso patchare il kernel senza riavviare?**
R: Si, tramite kernel live patching: kpatch (RHEL con subscription) o Canonical Livepatch (Ubuntu Pro). Limitazione: solo patch a funzioni, non a strutture dati. Copre la maggior parte dei CVE kernel.

**D: Qual e la differenza tra CFS e EEVDF?**
R: CFS (Completely Fair Scheduler, default fino al kernel 6.5) assegna CPU proporzionalmente alla priorita, usando vruntime. EEVDF (Earliest Eligible Virtual Deadline First, default dal kernel 6.6) aggiunge deadline virtuali, migliorando la latenza per processi interattivi senza euristiche. Per l'utente finale, EEVDF si traduce in una migliore reattivita del desktop.

**D: Come si configura BBR come congestion control TCP?**
R: BBR (Bottleneck Bandwidth and Round-trip propagation time) e sviluppato da Google. Abilitare: `sysctl -w net.ipv4.tcp_congestion_control=bbr` e `sysctl -w net.core.default_qdisc=fq`. Persistente: aggiungere in `/etc/sysctl.d/90-bbr.conf`. Verificare: `sysctl net.ipv4.tcp_congestion_control`. BBR migliora significativamente il throughput su reti con packet loss.

**D: Come ridurre il tempo di boot?**
R: 1) `systemd-analyze blame` per identificare i servizi lenti. 2) Disabilitare servizi non necessari. 3) Usare `systemd-analyze critical-chain` per trovare il path critico. 4) Considerare la compilazione di un kernel custom con solo i driver necessari (riduce il tempo di init kernel). 5) Usare `hostonly=yes` per dracut (initramfs piu piccolo). 6) Verificare che non ci siano timeout di rete all'avvio (DHCP, NFS).

**D: Le Transparent Huge Pages (THP) vanno disabilitate sempre?**
R: No. THP sono generalmente benefiche per applicazioni con grande footprint di memoria e accesso uniforme (HPC, calcolo scientifico). Vanno disabilitate (o impostate a `madvise`) per database (PostgreSQL, MongoDB, Redis, MySQL) dove la compattazione THP causa latenza imprevedibile. L'impostazione `madvise` e un buon compromesso: solo le applicazioni che esplicitamente richiedono THP le ottengono.

**D: Come verificare se il mio sistema supporta IOMMU per GPU passthrough?**
R: 1) Verificare che la CPU supporti VT-d (Intel) o AMD-Vi: `grep -E "vmx|svm" /proc/cpuinfo`. 2) Abilitare nel BIOS/UEFI. 3) Aggiungere `intel_iommu=on` o `amd_iommu=on` ai parametri kernel. 4) Verificare: `dmesg | grep -i iommu`. 5) Verificare i gruppi IOMMU: `find /sys/kernel/iommu_groups/ -type l`.
