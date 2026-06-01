# WSL — Windows Subsystem for Linux

> **Modulo 17** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Corso** | Windows per ingegneri di sistema |
| **Fase** | Ambienti di sviluppo e interoperabilità |
| **Modulo del corso** | 17 — WSL (Windows Subsystem for Linux) |
| **Versioni di riferimento** | Windows 11 24H2, Windows Server 2025, WSL 2.x, WSLg 1.x, Docker Desktop 4.x |
| **Livello** | Competent / Proficient |
| **Prerequisiti** | Fondamenti Linux CLI (→ `14-batch-scripting.md`), networking Windows (→ `06-rete-windows.md`), concetti di virtualizzazione Hyper-V (→ `23-hyper-v-guida-completa.md`) |
| **Obiettivi di apprendimento** | 1) Comprendere l'architettura WSL 2 basata su Hyper-V e le differenze rispetto a WSL 1 · 2) Installare, importare ed esportare distribuzioni Linux personalizzate · 3) Configurare networking (mirrored mode, port forwarding) e filesystem interop per performance ottimali · 4) Integrare Docker Desktop con WSL 2 backend per workflow di sviluppo container-native · 5) Abilitare GPU passthrough (CUDA/DirectML) per workload di machine learning |
| **Tempo stimato** | lettura 90 min · lab 120 min |
| **Ultimo aggiornamento** | 2026-05-23 |

## Idee guida
1. **WSL 2 (Hyper-V) > WSL 1 (translation layer).**
2. **`wsl --import` per custom distro deployment.**
3. **systemd support in WSL2 2022+.**
4. **WSLg per GUI app Linux su Windows.**
5. **Networking mirrored mode elimina la complessità NAT.**
6. **Il filesystem corretto determina la performance: ext4 per progetti Linux, NTFS per progetti Windows.**
7. **GPU passthrough abilita CUDA/DirectML per ML direttamente in WSL.**
8. **Docker in WSL2 = esperienza nativa Linux senza overhead di una VM tradizionale.**


## Indice

- [1. Panoramica e storia](#1-panoramica-e-storia)
- [2. Architettura WSL 2](#2-architettura-wsl-2)
- [3. WSL 1 vs WSL 2 — Confronto dettagliato](#3-wsl-1-vs-wsl-2--confronto-dettagliato)
- [4. Installazione](#4-installazione)
- [5. Gestione Distribuzioni](#5-gestione-distribuzioni)
- [6. Configurazione — .wslconfig e wsl.conf](#6-configurazione--wslconfig-e-wslconf)
- [7. Networking](#7-networking)
- [8. Filesystem e interop](#8-filesystem-e-interop)
- [9. Docker Desktop con WSL 2](#9-docker-desktop-con-wsl-2)
- [10. Applicazioni grafiche — WSLg](#10-applicazioni-grafiche--wslg)
- [11. Sviluppo con WSL](#11-sviluppo-con-wsl)
- [12. Supporto systemd](#12-supporto-systemd)
- [13. Supporto GPU — CUDA, DirectML, Machine Learning](#13-supporto-gpu--cuda-directml-machine-learning)
- [14. Operazioni avanzate](#14-operazioni-avanzate)
- [15. WSL per sysadmin](#15-wsl-per-sysadmin)
- [16. Sicurezza](#16-sicurezza)
- [17. Integrazione con Windows Terminal](#17-integrazione-con-windows-terminal)
- [18. Troubleshooting](#18-troubleshooting)
- [19. FAQ](#19-faq)
- [20. Best Practices per ambiente di sviluppo](#20-best-practices-per-ambiente-di-sviluppo)

---

## 1. Panoramica e storia

WSL (Windows Subsystem for Linux) permette di eseguire distribuzioni Linux nativamente su Windows senza VM tradizionali o dual-boot. WSL 2 utilizza un vero kernel Linux in una VM leggera Hyper-V, offrendo compatibilità completa con le system call Linux, performance I/O native sul filesystem Linux, e integrazione trasparente con Windows (accesso ai file, rete, GPU).

### Evoluzione storica

| Versione | Data | Novità principali |
|----------|------|-------------------|
| WSL 1 | Agosto 2016 | Translation layer per syscall Linux → NT kernel |
| WSL 2 | Maggio 2019 | Kernel Linux reale in VM Hyper-V leggera |
| WSLg | Aprile 2021 | Supporto app grafiche Linux (Wayland/X11) |
| systemd | Settembre 2022 | Supporto systemd nativo in WSL 2 |
| Mirrored networking | Settembre 2023 | Modalità di rete specchiata (stesso IP di Windows) |
| DNS tunneling | 2023 | Risoluzione DNS migliorata attraverso VPN |
| autoMemoryReclaim | 2023 | Rilascio automatico della RAM inutilizzata |
| Dev Drive support | 2024 | Integrazione con ReFS Dev Drive per performance |
| Sparse VHD | 2024 | Compattazione automatica dei dischi virtuali |

### Casi d'uso principali

- **Sviluppo software cross-platform**: compilare, testare e distribuire software Linux senza lasciare Windows
- **DevOps e infrastruttura**: eseguire Ansible, Terraform, kubectl, Docker nativamente
- **Data science e ML**: CUDA e DirectML per TensorFlow/PyTorch direttamente in WSL
- **Sysadmin**: strumenti Linux (grep, awk, sed, ssh, rsync) disponibili su macchine Windows
- **Cybersecurity**: strumenti di pentest Linux (nmap, Burp, Metasploit) su workstation Windows
- **Apprendimento Linux**: ambiente Linux completo senza rischio di compromettere il sistema host

---

## 2. Architettura WSL 2

### Schema architetturale completo

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Windows 11 Host                              │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                  Hyper-V Hypervisor Layer                      │  │
│  │                                                                │  │
│  │  ┌──────────────────────────────────────────────────────────┐  │  │
│  │  │            Lightweight Utility VM (WSL 2)                │  │  │
│  │  │                                                          │  │  │
│  │  │  ┌──────────────────────────────────────────────────┐    │  │  │
│  │  │  │  Linux Kernel 5.15+ (Microsoft-maintained)       │    │  │  │
│  │  │  │  - Full syscall compatibility                    │    │  │  │
│  │  │  │  - cgroups v2, namespaces, eBPF                  │    │  │  │
│  │  │  │  - /dev/dxg (GPU paravirtualization)             │    │  │  │
│  │  │  └──────────────────────────────────────────────────┘    │  │  │
│  │  │                                                          │  │  │
│  │  │  ┌───────────────┐  ┌───────────────┐                   │  │  │
│  │  │  │   Ubuntu       │  │   Debian       │  ← Distribuzioni │  │  │
│  │  │  │   (ext4 VHDX)  │  │   (ext4 VHDX)  │    separate      │  │  │
│  │  │  │   /home/user/  │  │   /home/user/  │                   │  │  │
│  │  │  └───────────────┘  └───────────────┘                   │  │  │
│  │  │                                                          │  │  │
│  │  │  ┌──────────────────────┐                                │  │  │
│  │  │  │  init system          │                                │  │  │
│  │  │  │  (systemd o init)     │                                │  │  │
│  │  │  └──────────────────────┘                                │  │  │
│  │  └──────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Communication Layer                                          │  │
│  │  ├── 9P Protocol (filesystem bridge Windows ↔ Linux)          │  │
│  │  ├── vsock / Hyper-V sockets (networking, IPC)                │  │
│  │  ├── WSLg (Wayland compositor + PulseAudio per GUI/audio)     │  │
│  │  └── /dev/dxg → DirectX GPU driver (CUDA, DirectML, OpenGL)  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Windows      │  │ Windows      │  │ File Explorer │              │
│  │ Terminal     │  │ Apps         │  │ (\\wsl$\)     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────────────────────────┘
```

### Componenti chiave

**Lightweight Utility VM**: a differenza di una VM tradizionale, la VM di WSL 2 è ottimizzata per avvio rapido (~1-2 secondi), consumo di memoria dinamico e condivisione delle risorse con l'host Windows. Non ha un BIOS completo, non emula hardware arbitrario e condivide il kernel tra tutte le distribuzioni installate.

**Kernel Linux Microsoft**: Microsoft mantiene un fork del kernel Linux (basato su kernel.org mainline) con patch specifiche per l'integrazione Hyper-V, il filesystem 9P e la GPU paravirtualization. Il codice sorgente è pubblico su GitHub (`microsoft/WSL2-Linux-Kernel`).

**Protocollo 9P**: il filesystem bridge tra Windows e Linux. Quando da WSL si accede a `/mnt/c/`, le operazioni di I/O vengono tradotte in chiamate 9P verso il filesystem NTFS di Windows. Questo introduce latenza significativa rispetto all'accesso diretto al filesystem ext4 nativo della distribuzione.

**VHDX (Virtual Hard Disk)**: ogni distribuzione WSL 2 ha il proprio disco virtuale in formato VHDX, formattato ext4. La dimensione cresce dinamicamente fino a un massimo configurabile (default 1 TB). Con l'opzione `sparseVhd=true`, lo spazio non utilizzato viene recuperato automaticamente.

**GPU Paravirtualization (/dev/dxg)**: il device `/dev/dxg` espone le API DirectX del GPU host dentro la VM WSL 2. Questo permette a framework CUDA, DirectML e OpenCL di funzionare dentro WSL senza un driver GPU Linux separato — il driver Windows viene condiviso.

### Ciclo di vita della VM

```
1. Utente apre terminale WSL (o esegue `wsl`)
2. Windows lancia la Lightweight Utility VM (se non già attiva)
3. Il kernel Linux si avvia (~1-2 secondi)
4. Il processo init (systemd o init custom) parte
5. La distribuzione richiesta viene montata (VHDX → ext4)
6. La shell utente viene avviata (/bin/bash, /bin/zsh, ecc.)

Shutdown:
- `wsl --terminate <distro>`: termina una distribuzione specifica
- `wsl --shutdown`: termina TUTTE le distribuzioni + spegne la VM
- Timeout automatico: dopo N secondi di inattività (configurabile)
```

### Memoria e risorse

La VM WSL 2 utilizza memoria in modo dinamico:

- **Allocazione iniziale**: la VM parte con poca memoria e cresce secondo necessità
- **Default**: fino al 50% della RAM fisica dell'host (o 8 GB, il minore dei due)
- **Page cache**: Linux usa aggressivamente la RAM per il page cache; questo può far sembrare che WSL "consumi troppa memoria"
- **autoMemoryReclaim**: con questa opzione sperimentale, la VM rilascia gradualmente la memoria del page cache quando non è più necessaria

---

## 3. WSL 1 vs WSL 2 — Confronto dettagliato

### Tabella di confronto

| Caratteristica | WSL 1 | WSL 2 |
|----------------|-------|-------|
| **Architettura** | Translation layer (syscall → NT kernel) | Kernel Linux reale in VM Hyper-V |
| **Compatibilità syscall** | Parziale (~70% delle syscall) | Completa (100% delle syscall) |
| **Kernel** | Nessun kernel Linux | Kernel Linux 5.15+ Microsoft-maintained |
| **File I/O su filesystem Linux** | Lento (traduzione per ogni operazione) | Nativo, veloce (ext4 diretto) |
| **File I/O su filesystem Windows** | Veloce (accesso diretto NTFS) | Lento (via protocollo 9P) |
| **Networking** | Condiviso con Windows (stesso IP) | NAT separato (IP diverso) o mirrored |
| **Consumo memoria** | Condivisa con Windows | VM dedicata (dinamica) |
| **Docker** | Non supportato | Supporto nativo completo |
| **systemd** | Non supportato | Supportato (opt-in) |
| **GUI apps (WSLg)** | Non supportato | Supportato nativamente |
| **GPU passthrough** | Non supportato | CUDA, DirectML, OpenCL |
| **Tempo di avvio** | Istantaneo | ~1-2 secondi |
| **Compatibilità software** | Limitata (no Docker, no fuse, ecc.) | Completa (tutto ciò che gira su Linux) |
| **Nested virtualization** | Non applicabile | Supportata (KVM in WSL) |
| **cgroups/namespaces** | Non supportati | Supporto completo |
| **eBPF** | Non supportato | Supportato |
| **FUSE** | Non supportato | Supportato |
| **inotify cross-filesystem** | Supportato per file Windows | Non supportato per file su /mnt/c/ |

### Quando usare WSL 1

WSL 1 resta utile in scenari molto specifici:

1. **Performance I/O su file Windows**: se il progetto risiede su NTFS e non può essere spostato, WSL 1 ha accesso diretto senza il collo di bottiglia 9P
2. **Compatibilità con ambienti senza Hyper-V**: alcuni vecchi PC o configurazioni corporate disabilitano Hyper-V
3. **inotify su file Windows**: WSL 1 supporta il file watching su `/mnt/c/`, WSL 2 no (limitazione 9P)
4. **Basso consumo di memoria**: WSL 1 non alloca memoria per una VM separata

### Quando usare WSL 2 (quasi sempre)

1. **Docker/container**: impossibile su WSL 1
2. **Compatibilità software**: qualsiasi software Linux funziona (incluso software che usa syscall non tradotte in WSL 1)
3. **Performance I/O su filesystem Linux**: ordini di grandezza più veloce di WSL 1
4. **GPU computing**: CUDA, DirectML, TensorFlow, PyTorch
5. **systemd**: servizi, timer, socket activation
6. **App grafiche**: WSLg richiede WSL 2

### Benchmark I/O indicativi

```
Operazione                      WSL 1 (NTFS)    WSL 2 (ext4)    WSL 2 (/mnt/c)
─────────────────────────────────────────────────────────────────────────────────
npm install (node_modules)       ~45s            ~8s             ~120s
git clone (large repo)           ~30s            ~6s             ~90s
grep -r su 10K file              ~12s            ~2s             ~35s
Compilazione kernel Linux        ~25min          ~4min           ~60min+
SQLite bulk insert (1M rows)     ~15s            ~3s             ~45s
```

**Conclusione**: per la quasi totalità dei casi, WSL 2 è la scelta corretta. L'unica regola ferrea è tenere i file di progetto nel filesystem nativo della piattaforma che li usa — ext4 per progetti Linux, NTFS per progetti Windows.

---

## 4. Installazione

### Installazione rapida (Windows 10 2004+ / Windows 11)

```powershell
# Installazione one-liner (richiede riavvio)
wsl --install
# Installa: Virtual Machine Platform, WSL, Ubuntu (default)

# Installare una distribuzione specifica
wsl --install -d Ubuntu-22.04
wsl --install -d Ubuntu-24.04
wsl --install -d Debian
wsl --install -d openSUSE-Leap-15.5
wsl --install -d kali-linux
wsl --install -d Fedora
wsl --install -d OracleLinux_9_1

# Elencare distribuzioni disponibili online
wsl --list --online

# Installazione senza distribuzione (solo il subsystem)
wsl --install --no-distribution

# Aggiornare WSL all'ultima versione
wsl --update

# Forzare aggiornamento da Microsoft Store
wsl --update --web-download

# Verificare versione installata
wsl --version

# Impostare WSL 2 come versione predefinita
wsl --set-default-version 2

# Convertire distribuzione esistente da WSL 1 a WSL 2
wsl --set-version Ubuntu 2
```

### Installazione manuale (componenti separati)

Per ambienti dove `wsl --install` non è disponibile o in contesti enterprise con restrizioni:

```powershell
# Passo 1: Abilitare Windows Subsystem for Linux
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Passo 2: Abilitare Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Passo 3: RIAVVIARE il PC

# Passo 4: Scaricare e installare il Linux Kernel Update Package
# https://aka.ms/wsl2kernel

# Passo 5: Impostare WSL 2 come default
wsl --set-default-version 2

# Passo 6: Installare distribuzione dal Microsoft Store o via CLI
wsl --install -d Ubuntu-24.04
```

### Prerequisiti hardware e software

```
Requisiti minimi:
├── CPU: x64 con supporto virtualizzazione (Intel VT-x / AMD-V)
│   └── Deve essere abilitato nel BIOS/UEFI
├── RAM: 4 GB minimo (8 GB+ raccomandato)
├── OS: Windows 10 versione 2004+ (build 19041+) o Windows 11
├── Spazio disco: ~1 GB per WSL + distribuzione
└── Hyper-V: abilitato (WSL 2 lo richiede)

Verifica virtualizzazione:
└── Task Manager → Performance → CPU → "Virtualization: Enabled"
```

### Installare distribuzioni custom (non dal Microsoft Store)

```powershell
# Metodo 1: Importare da un tarball
# Scaricare il rootfs di una distribuzione (es. Alpine, Arch Linux)
wsl --import Alpine C:\WSL\Alpine C:\Downloads\alpine-minirootfs.tar.gz

# Metodo 2: Importare da un'immagine Docker
# Esportare un container Docker come tarball
docker run -t alpine:latest true
docker export $(docker ps -lq) > alpine-docker.tar
wsl --import AlpineDocker C:\WSL\AlpineDocker alpine-docker.tar

# Metodo 3: Creare da zero con debootstrap (per Debian-based)
# All'interno di una distribuzione WSL esistente:
sudo debootstrap --variant=minbase bookworm /tmp/mydebian http://deb.debian.org/debian
cd /tmp && sudo tar -czf /mnt/c/Users/Renan/mydebian.tar.gz -C mydebian .
# Su PowerShell:
wsl --import MyDebian C:\WSL\MyDebian C:\Users\Renan\mydebian.tar.gz

# Metodo 4: Importare da file .vhdx esistente
wsl --import-in-place ArchWSL C:\WSL\ArchWSL\ext4.vhdx
```

### Installazione in ambienti enterprise

```powershell
# Installazione offline (senza Microsoft Store)
# 1. Scaricare l'appx bundle della distribuzione
Invoke-WebRequest -Uri "https://aka.ms/wslubuntu" -OutFile "Ubuntu.appx" -UseBasicParsing

# 2. Installare l'appx
Add-AppxPackage .\Ubuntu.appx

# 3. Oppure: distribuire via DISM per deployment di massa
dism.exe /online /Add-AppxProvisionedPackage /PackagePath:.\Ubuntu.appx /SkipLicense

# Group Policy per abilitare/disabilitare WSL in ambienti corporate:
# Computer Configuration → Administrative Templates → Windows Components
# → Windows Subsystem for Linux
```

---

## 5. Gestione Distribuzioni

### Comandi di gestione

```powershell
# Elencare distribuzioni installate con dettagli
wsl --list --verbose
# NAME            STATE           VERSION
# * Ubuntu        Running         2
#   Debian        Stopped         2
#   Alpine        Stopped         2

# Avviare distribuzione
wsl                              # Distribuzione default
wsl -d Debian                    # Distribuzione specifica
wsl -d Ubuntu -u root            # Come utente root
wsl -d Ubuntu -e /bin/zsh        # Con shell specifica

# Impostare distribuzione default
wsl --set-default Ubuntu

# Terminare distribuzione
wsl --terminate Ubuntu
wsl --shutdown                   # Termina TUTTE le distribuzioni + VM

# Esportare distribuzione (backup completo)
wsl --export Ubuntu C:\Backup\ubuntu-backup.tar
# Con compressione (WSL recente):
wsl --export Ubuntu C:\Backup\ubuntu-backup.tar.gz --vhd

# Esportare come file VHD (preserva struttura ext4)
wsl --export Ubuntu C:\Backup\ubuntu-backup.vhdx --vhd

# Importare distribuzione
wsl --import MyUbuntu C:\WSL\MyUbuntu C:\Backup\ubuntu-backup.tar
# Importare VHD in-place (senza copiare):
wsl --import-in-place MyUbuntu C:\WSL\MyUbuntu\ext4.vhdx

# Eliminare distribuzione
wsl --unregister Ubuntu
# ATTENZIONE: cancella tutti i dati irreversibilmente!

# Eseguire comando singolo senza entrare nella shell
wsl -d Ubuntu -- ls -la /home
wsl -d Ubuntu -- bash -c "apt update && apt upgrade -y"
wsl -d Ubuntu -- cat /etc/os-release

# Stato generale di WSL
wsl --status

# Montare un disco fisico in WSL (es. ext4 su USB)
wsl --mount \\.\PHYSICALDRIVE2 --partition 1 --type ext4
wsl --unmount \\.\PHYSICALDRIVE2
```

### Gestione degli utenti nelle distribuzioni

```bash
# Creare un nuovo utente nella distribuzione
sudo adduser devuser
sudo usermod -aG sudo devuser

# Impostare l'utente di default (in /etc/wsl.conf)
# [user]
# default=devuser

# Oppure da PowerShell (metodo distro-specific)
ubuntu config --default-user devuser
```

### Spostare una distribuzione su un altro disco

```powershell
# WSL salva le distribuzioni in %LOCALAPPDATA%\Packages\ di default
# Per spostarle (es. da C: a D:):

# Passo 1: Esportare
wsl --export Ubuntu C:\temp\ubuntu-export.tar

# Passo 2: Eliminare la vecchia installazione
wsl --unregister Ubuntu

# Passo 3: Importare nella nuova posizione
wsl --import Ubuntu D:\WSL\Ubuntu C:\temp\ubuntu-export.tar

# Passo 4: Reimpostare l'utente di default
ubuntu config --default-user renan
# Oppure aggiungere a /etc/wsl.conf:
# [user]
# default=renan

# Passo 5: Verificare
wsl -d Ubuntu -- whoami
```

### Clonare una distribuzione

```powershell
# Utile per creare ambienti isolati (dev, test, staging)
wsl --export Ubuntu C:\temp\ubuntu-template.tar
wsl --import Ubuntu-Dev D:\WSL\Ubuntu-Dev C:\temp\ubuntu-template.tar
wsl --import Ubuntu-Test D:\WSL\Ubuntu-Test C:\temp\ubuntu-template.tar
wsl --import Ubuntu-Staging D:\WSL\Ubuntu-Staging C:\temp\ubuntu-template.tar
```

---

## 6. Configurazione — .wslconfig e wsl.conf

### .wslconfig (globale, lato Windows)

Questo file si trova in `%USERPROFILE%\.wslconfig` e si applica a **tutte** le distribuzioni WSL 2. Richiede `wsl --shutdown` dopo le modifiche.

```ini
# %USERPROFILE%\.wslconfig
# Si applica a TUTTE le distribuzioni WSL 2
# Richiede: wsl --shutdown && wsl per applicare le modifiche

[wsl2]
# ─── Risorse ───────────────────────────────────────────────
memory=8GB                 # RAM massima per la VM WSL (default: 50% della RAM o 8GB)
processors=4               # CPU massime assegnate alla VM
swap=4GB                   # Dimensione dello swap
swapFile=C:\\WSL\\swap.vhdx  # Posizione del file di swap

# ─── Networking ────────────────────────────────────────────
networkingMode=mirrored    # mirrored = stesso IP di Windows (Win 11 22H2+)
                           # NAT = IP separato (default)
dnsTunneling=true          # DNS tunneling migliorato (risolve problemi con VPN)
autoProxy=true             # Usa le impostazioni proxy di Windows
firewall=true              # Applica le regole firewall di Windows anche a WSL

# ─── Kernel ────────────────────────────────────────────────
# kernel=C:\\WSL\\custom-kernel        # Path a un kernel personalizzato
# kernelCommandLine=                   # Parametri kernel aggiuntivi

# ─── Virtualizzazione ─────────────────────────────────────
nestedVirtualization=true  # Abilita KVM dentro WSL (per Android emulator, ecc.)

# ─── Disco ─────────────────────────────────────────────────
# defaultVhdSize=274877906944         # Dimensione max VHD in byte (default 256GB)

# ─── GPU ───────────────────────────────────────────────────
# gpuCountForWSL2VM=1                 # Numero di GPU virtuali esposte

[experimental]
autoMemoryReclaim=gradual  # Rilascia memoria inutilizzata (dropcache | gradual | disabled)
sparseVhd=true             # Compatta automaticamente il disco VHDX
bestEffortDnsParsing=true  # Parsing DNS migliorato
useWindowsDnsCache=true    # Usa la cache DNS di Windows
# hostAddressLoopback=true # Permette a WSL di raggiungere servizi Windows su localhost
```

### Dettaglio delle opzioni di memoria

```ini
# Scenari tipici di configurazione memoria:

# Workstation con 16 GB RAM — sviluppo generico
[wsl2]
memory=6GB
swap=4GB

# Workstation con 32 GB RAM — machine learning
[wsl2]
memory=16GB
swap=8GB
processors=8

# Workstation con 64 GB RAM — compilazioni pesanti + ML
[wsl2]
memory=32GB
swap=16GB
processors=12

# Laptop con 8 GB RAM — uso leggero
[wsl2]
memory=3GB
swap=2GB
processors=2

[experimental]
autoMemoryReclaim=gradual  # Fondamentale su laptop con poca RAM
```

### wsl.conf (per distribuzione, lato Linux)

Questo file si trova in `/etc/wsl.conf` all'interno di ogni distribuzione e configura il comportamento specifico di quella distribuzione. Richiede `wsl --terminate <distro>` dopo le modifiche.

```ini
# /etc/wsl.conf — configurazione per la singola distribuzione
# Richiede: wsl --terminate <distro> per applicare le modifiche

[boot]
systemd=true               # Abilitare systemd (WSL 0.67.6+)
# command="service cron start"  # Comando eseguito al boot della distribuzione

[automount]
enabled=true               # Montare automaticamente i dischi Windows
root=/mnt/                  # Mount point per i dischi Windows (/mnt/c, /mnt/d, ecc.)
options="metadata,umask=22,fmask=11"   # Permessi corretti sui file Windows
                            # metadata: preserva permessi Linux su NTFS
                            # umask=22: directory 755
                            # fmask=11: file 644

[network]
generateHosts=true         # Genera /etc/hosts basato su Windows
generateResolvConf=true    # Genera /etc/resolv.conf basato su Windows
hostname=dev-wsl           # Hostname personalizzato per la distribuzione

[interop]
enabled=true               # Permette di eseguire comandi Windows da Linux
appendWindowsPath=true     # Aggiunge il PATH di Windows al PATH di Linux
                           # false se si vuole un PATH Linux pulito

[user]
default=renan              # Utente di login di default
```

### Opzioni automount dettagliate

```ini
# Opzioni di mount per il filesystem Windows

[automount]
enabled=true
root=/mnt/
# Opzioni disponibili:
# metadata    → Salva permessi Linux come metadata NTFS (fondamentale per git, ssh)
# umask=22    → Permessi default directory: 755 (rwxr-xr-x)
# fmask=11    → Permessi default file: 644 (rw-r--r--)
# uid=1000    → Owner dei file (ID utente Linux)
# gid=1000    → Gruppo dei file (ID gruppo Linux)
# case=dir    → Case sensitivity per directory (off | dir | force)
options="metadata,umask=22,fmask=11"
# mountFsTab=true  → Monta anche i filesystem definiti in /etc/fstab

# Esempio /etc/fstab per montare un network share:
# //server/share /mnt/share cifs credentials=/home/user/.smb,uid=1000,gid=1000 0 0
```

### Disabilitare la generazione automatica di resolv.conf

```ini
# Scenario: DNS custom necessario (es. VPN corporate, Pi-hole, ecc.)

# 1. Disabilitare la generazione in /etc/wsl.conf:
[network]
generateResolvConf=false

# 2. Riavviare la distribuzione:
# wsl --terminate Ubuntu

# 3. Creare /etc/resolv.conf manualmente:
# sudo rm /etc/resolv.conf  (è un symlink)
# sudo nano /etc/resolv.conf
```

```bash
# /etc/resolv.conf personalizzato
nameserver 192.168.10.10     # DNS primario (corporate)
nameserver 1.1.1.1           # DNS secondario (Cloudflare)
nameserver 8.8.8.8           # DNS terziario (Google)
search corp.contoso.com      # Dominio di ricerca
```

```bash
# Rendere il file immutabile (impedisce sovrascrittura)
sudo chattr +i /etc/resolv.conf
```

---

## 7. Networking

### Modalità NAT (default)

In modalità NAT, WSL 2 ha un indirizzo IP separato da Windows, su una rete virtuale interna. Il traffico viene tradotto (NAT) per raggiungere la rete esterna.

```bash
# Da WSL: ottenere il proprio IP
ip addr show eth0 | grep "inet " | awk '{print $2}'
# Tipicamente: 172.x.x.x

# Da WSL: ottenere l'IP di Windows (gateway)
ip route show default | awk '{print $3}'
# Es: 172.28.176.1

# Da WSL: raggiungere un servizio Windows
curl http://$(ip route show default | awk '{print $3}'):8080

# Da Windows: raggiungere un servizio WSL
# Port forwarding automatico: localhost funziona per le porte in ascolto
# Es: server web su WSL porta 3000 → Windows può usare http://localhost:3000
```

### Limitazioni della modalità NAT

```
Problemi comuni con NAT:
├── IP di WSL cambia ad ogni riavvio
├── Servizi esterni non possono raggiungere WSL direttamente
├── VPN su Windows può interrompere la connettività WSL
├── mDNS/Bonjour non funziona cross-boundary
├── Multicast non attraversa il boundary NAT
└── Port forwarding automatico funziona solo per TCP su localhost
```

### Modalità Mirrored (raccomandata — Windows 11 22H2+)

La modalità mirrored elimina la maggior parte dei problemi NAT: WSL ottiene lo stesso IP di Windows e condivide le interfacce di rete.

```ini
# %USERPROFILE%\.wslconfig
[wsl2]
networkingMode=mirrored
dnsTunneling=true
autoProxy=true
firewall=true
```

```
Vantaggi della modalità mirrored:
├── WSL ha lo stesso IP di Windows
├── Nessun problema di port forwarding
├── VPN su Windows funziona automaticamente in WSL
├── IPv6 supportato nativamente
├── mDNS funziona
├── Servizi WSL raggiungibili dalla rete locale
└── DNS condiviso con Windows (incluso tunnel DNS per VPN)
```

### Port forwarding manuale (per modalità NAT)

```powershell
# Se il port forwarding automatico non funziona (es. per accesso dalla rete locale):

# Ottenere IP WSL
$wslIP = (wsl hostname -I).Trim()

# Creare port forwarding
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=$wslIP

# Aggiungere regola firewall
New-NetFirewallRule -DisplayName "WSL Port 8080" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8080

# Elencare port forwarding attivi
netsh interface portproxy show all

# Rimuovere port forwarding
netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0
```

### Accesso bidirezionale Windows ↔ WSL

```bash
# ─── Da WSL verso Windows ───────────────────────────────────
# Il gateway della rete virtuale è l'IP di Windows:
WIN_IP=$(ip route show default | awk '{print $3}')
# Oppure con mirrored mode: localhost funziona direttamente

# Accedere a SQL Server su Windows:
sqlcmd -S $WIN_IP,1433 -U sa -P 'password'

# Accedere a un servizio Windows:
curl http://$WIN_IP:5000/api/health

# ─── Da Windows verso WSL ───────────────────────────────────
# Con port forwarding automatico:
# http://localhost:<porta>  → funziona per TCP

# Accedere a un database PostgreSQL in WSL:
# Da PowerShell: psql -h localhost -p 5432 -U myuser -d mydb

# ─── Eseguire comandi Windows da Linux ──────────────────────
# (richiede [interop] enabled=true in wsl.conf)
cmd.exe /c "dir C:\Users"
powershell.exe -Command "Get-Process | Select-Object Name,CPU"
explorer.exe .    # Apre File Explorer nella directory corrente

# ─── Eseguire comandi Linux da Windows ──────────────────────
wsl -d Ubuntu -- grep -r "TODO" /home/renan/project/
wsl -d Ubuntu -- python3 /home/renan/scripts/analyze.py
```

### Configurazione DNS avanzata

```bash
# Problema: DNS non funziona in WSL (comune con VPN corporate)

# Soluzione 1: Abilitare DNS tunneling (raccomandata)
# In .wslconfig:
# [wsl2]
# dnsTunneling=true

# Soluzione 2: DNS manuale
sudo rm /etc/resolv.conf
sudo bash -c 'cat > /etc/resolv.conf << EOF
nameserver 8.8.8.8
nameserver 1.1.1.1
EOF'
sudo chattr +i /etc/resolv.conf

# In /etc/wsl.conf:
# [network]
# generateResolvConf=false

# Soluzione 3: DNS con split-tunnel VPN
# In .wslconfig:
# [wsl2]
# networkingMode=mirrored
# dnsTunneling=true

# Verifica DNS:
nslookup google.com
dig google.com
resolvectl status  # Se systemd è abilitato
```

### Funzionalità di rete avanzate WSL 2.4+

A partire dalla release WSL 2.0.0 (settembre 2023) e consolidate nelle versioni 2.1–2.4 (2024–2025), le funzionalità di rete di WSL 2 sono state significativamente migliorate per risolvere i problemi storici di connettività in ambienti aziendali, VPN e configurazioni di rete complesse.

#### Mirrored networking — meccanismo interno

La modalità mirrored non si limita a condividere l'indirizzo IP: replica l'intera topologia delle interfacce di rete Windows dentro la VM Linux. Ogni interfaccia di rete dell'host (Ethernet, Wi-Fi, VPN adapter) viene specchiata come interfaccia virtuale all'interno di WSL, con lo stesso indirizzo IP, subnet mask e configurazione DNS. Questo approccio elimina completamente il livello NAT e il virtual switch Hyper-V usato nella modalità predefinita.

```
Architettura Mirrored Mode:
┌────────────────────────────────────────────────────────────┐
│ Windows Host                                               │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Ethernet     │  │ Wi-Fi        │  │ VPN Adapter  │    │
│  │ 192.168.1.10 │  │ 10.0.0.5     │  │ 172.16.0.3   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │              │
│  ┌──────▼─────────────────▼─────────────────▼──────────┐  │
│  │ WSL 2 VM (mirrored interfaces)                      │  │
│  │                                                      │  │
│  │  eth0: 192.168.1.10   wlan0: 10.0.0.5               │  │
│  │  vpn0: 172.16.0.3                                    │  │
│  │                                                      │  │
│  │  → Stesso routing table di Windows                   │  │
│  │  → Stesse regole firewall (Hyper-V firewall)         │  │
│  │  → IPv6 nativo su tutte le interfacce                │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘

Vantaggi rispetto a NAT:
├── Servizi WSL raggiungibili direttamente dalla LAN
├── mDNS e Bonjour funzionano senza workaround
├── Multicast attraversa il boundary host ↔ WSL
├── Nessun port forwarding manuale necessario
├── VPN client su Windows copre automaticamente WSL
└── IPv6 end-to-end senza tunnel aggiuntivi
```

#### DNS tunneling — risoluzione oltre il network stack

Il DNS tunneling utilizza una funzionalità di virtualizzazione Hyper-V per comunicare direttamente con il risolutore DNS di Windows, senza inviare pacchetti di rete convenzionali. Invece di generare una query DNS UDP/TCP e instradarla attraverso l'interfaccia di rete virtuale (che può essere bloccata da VPN split-tunnel, firewall o proxy), WSL passa la richiesta DNS direttamente al servizio DNS di Windows tramite un canale di comunicazione interno alla VM.

```bash
# Comportamento senza DNS tunneling (problematico con VPN):
# App WSL → query DNS → interfaccia virtuale NAT → routing → potenziale blocco VPN

# Comportamento con DNS tunneling:
# App WSL → query DNS → canale Hyper-V diretto → Windows DNS resolver → risposta

# Configurazione in .wslconfig:
# [wsl2]
# dnsTunneling=true

# Opzioni complementari:
# [experimental]
# bestEffortDnsParsing=true    # Parsing robusto dei record DNS complessi
# useWindowsDnsCache=true      # Sfrutta la cache DNS di Windows

# Verifica funzionamento:
nslookup internal.corp.contoso.com
# Con DNS tunneling: risolve usando il DNS server della VPN
# Senza DNS tunneling: potrebbe fallire se la VPN intercetta il routing
```

#### autoProxy — proxy aziendale trasparente

L'opzione `autoProxy=true` in `.wslconfig` configura automaticamente le variabili d'ambiente HTTP_PROXY e HTTPS_PROXY in WSL basandosi sulle impostazioni proxy di Windows (inclusi PAC file e WPAD). Questo è fondamentale in ambienti corporate dove tutto il traffico passa attraverso un proxy.

```bash
# Con autoProxy=true, le variabili sono impostate automaticamente:
echo $HTTP_PROXY
# Esempio output: http://proxy.corp.contoso.com:8080

echo $HTTPS_PROXY
# Esempio output: http://proxy.corp.contoso.com:8080

# Per tool che non rispettano le variabili d'ambiente standard:
# Configurare manualmente in .bashrc come fallback:
# export http_proxy=$HTTP_PROXY
# export https_proxy=$HTTPS_PROXY
# export no_proxy="localhost,127.0.0.1,.corp.contoso.com"
```

#### Hyper-V firewall — regole condivise

A partire da WSL 2.0.9 e Windows 11 22H2, le regole del Windows Firewall si applicano automaticamente anche al traffico di rete delle distribuzioni WSL. Questa funzionalità, attiva di default nelle versioni recenti, garantisce che le policy di sicurezza di rete configurate sull'host Windows (incluse quelle distribuite via GPO o Intune) proteggano anche l'ambiente Linux.

```powershell
# Le regole firewall Windows si applicano automaticamente a WSL
# Esempio: bloccare il traffico in uscita da WSL verso una subnet:
New-NetFirewallRule -DisplayName "Block WSL to Lab Network" `
    -Direction Outbound -Action Block `
    -RemoteAddress "10.99.0.0/16" `
    -Profile Any

# Configurare in .wslconfig per abilitare/disabilitare:
# [wsl2]
# firewall=true    # Applica regole firewall Windows a WSL (default: true)

# Verificare da WSL che il firewall sia attivo:
# Le regole sono trasparenti — un pacchetto bloccato dal firewall Windows
# viene semplicemente droppato, senza errore specifico in WSL
```

---

## 8. Filesystem e interop

### Struttura del filesystem in WSL 2

```
/                          ← Root del filesystem Linux (ext4, su VHDX)
├── home/
│   └── renan/             ← Home directory (ext4 nativo, VELOCE)
│       └── projects/      ← Posizione ideale per i progetti
├── mnt/
│   ├── c/                 ← C:\ di Windows (via 9P, LENTO)
│   ├── d/                 ← D:\ di Windows (via 9P, LENTO)
│   └── wsl/               ← Mount point condivisi tra distribuzioni
├── tmp/                   ← Temporanei (ext4)
├── usr/                   ← Software di sistema (ext4)
└── etc/                   ← Configurazione (ext4)

Da Windows:
\\wsl$\Ubuntu\             ← Accesso al filesystem Linux da Windows
\\wsl.localhost\Ubuntu\    ← Equivalente (più affidabile con VPN)
```

### Performance filesystem — regola fondamentale

```
┌────────────────────────────────────────────────────────────────┐
│  REGOLA D'ORO: i file di progetto devono stare nel filesystem  │
│  della piattaforma che li usa principalmente.                  │
│                                                                │
│  Progetto Linux/Docker → /home/user/projects/    (ext4)       │
│  Progetto Windows      → C:\Users\...\projects\  (NTFS)       │
│                                                                │
│  Cross-filesystem I/O (9P) è 10-100x più lento.               │
└────────────────────────────────────────────────────────────────┘

Benchmark indicativi (operazioni su 10.000 file):
├── ext4 nativo (dentro WSL):        ~2 secondi
├── NTFS da Windows nativo:          ~3 secondi
├── NTFS da WSL via 9P (/mnt/c/):   ~45 secondi
└── ext4 da Windows via \\wsl$\:     ~20 secondi
```

### Accesso cross-filesystem

```bash
# ─── Da Linux a Windows ───────────────────────────────────────
ls /mnt/c/Users/                     # C:\Users\
ls /mnt/d/                           # D:\
cp /home/renan/report.pdf /mnt/c/Users/Renan/Desktop/

# Creare symlink per accesso rapido
ln -s /mnt/c/Users/Renan/Documents ~/win-docs
ln -s /mnt/c/Users/Renan/Downloads ~/win-downloads

# ─── Da Windows a Linux ──────────────────────────────────────
# File Explorer: digitare \\wsl$\Ubuntu nella barra degli indirizzi
# PowerShell:
cd \\wsl.localhost\Ubuntu\home\renan
# CMD:
dir \\wsl$\Ubuntu\home\renan

# Aprire File Explorer dalla directory corrente in WSL:
explorer.exe .

# Copiare file da WSL a Windows
cp /home/renan/project/build/app.exe /mnt/c/Users/Renan/Desktop/
```

### Permessi e metadata

```bash
# Il flag metadata (in automount options) è fondamentale per:
# - git: senza metadata, tutti i file appaiono come 777
# - ssh: le chiavi SSH richiedono permessi 600
# - script: i permessi di esecuzione devono essere preservati

# Configurazione in /etc/wsl.conf:
# [automount]
# options="metadata,umask=22,fmask=11"

# Verificare permessi su file Windows:
ls -la /mnt/c/Users/Renan/
# Con metadata: permessi realistici (644, 755, ecc.)
# Senza metadata: tutto è 777

# Impostare permessi su file Windows montati:
chmod 600 /mnt/c/Users/Renan/.ssh/id_ed25519
# Funziona solo con metadata abilitato

# DrvFS mount options per controllo granulare:
# In /etc/fstab:
# C:\  /mnt/c  drvfs  rw,noatime,uid=1000,gid=1000,metadata,umask=22,fmask=11  0 0
```

### Condivisione file tra distribuzioni WSL

```bash
# Ogni distribuzione WSL 2 ha il proprio filesystem ext4 separato
# Per condividere file tra distribuzioni:

# Opzione 1: usare /mnt/wsl/ (tmpfs condiviso)
# I file in /mnt/wsl/ sono visibili a tutte le distribuzioni attive
# ATTENZIONE: è un tmpfs, i file si perdono al shutdown

# Opzione 2: accedere al filesystem di un'altra distribuzione
# Da Ubuntu, accedere ai file di Debian:
ls /mnt/wsl/instances/Debian/home/

# Opzione 3: usare una directory Windows condivisa
# Entrambe le distribuzioni accedono a /mnt/c/Shared/

# Opzione 4: montare un disco condiviso
# wsl --mount per montare un disco fisico accessibile da tutte le distribuzioni
```

### Case sensitivity

```bash
# NTFS su Windows è case-insensitive di default
# ext4 su Linux è case-sensitive

# Questo può causare problemi con repository git che hanno file
# con nomi che differiscono solo per case (es. File.js e file.js)

# Abilitare case sensitivity per una directory Windows:
fsutil.exe file setCaseSensitiveInfo C:\Projects\MyRepo enable

# Verificare:
fsutil.exe file queryCaseSensitiveInfo C:\Projects\MyRepo

# In /etc/wsl.conf per il mount automatico:
# [automount]
# options="metadata,case=dir"
# case=dir: rispetta la case sensitivity per directory
# case=off: tutto case-insensitive (default Windows)
# case=force: tutto case-sensitive
```

---

## 9. Docker Desktop con WSL 2

### Architettura Docker + WSL 2

```
┌──────────────────────────────────────────────────────────┐
│ Windows 11                                               │
│                                                          │
│  ┌────────────────────────┐                              │
│  │ Docker Desktop         │                              │
│  │ (Windows process)      │                              │
│  │ ├── UI / Tray icon     │                              │
│  │ └── Docker CLI         │                              │
│  └────────┬───────────────┘                              │
│           │                                              │
│  ┌────────▼───────────────────────────────────────────┐  │
│  │ WSL 2 VM                                           │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │ docker-desktop (distribuzione interna)       │  │  │
│  │  │ ├── dockerd (daemon)                         │  │  │
│  │  │ ├── containerd                               │  │  │
│  │  │ └── Docker socket (/var/run/docker.sock)     │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │ Ubuntu       │  │ Debian       │               │  │
│  │  │ (docker CLI  │  │ (docker CLI  │  ← CLI via    │  │
│  │  │  disponibile)│  │  disponibile)│    socket      │  │
│  │  └──────────────┘  └──────────────┘               │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Configurazione Docker Desktop + WSL 2

```
Installazione:
1. Installare Docker Desktop per Windows
2. Settings → General → "Use the WSL 2 based engine" ✓
3. Settings → Resources → WSL Integration
   → Abilitare le distribuzioni dove si vuole usare Docker
4. Applicare e riavviare

Verifica dalla distribuzione WSL:
$ docker --version
Docker version 27.x.x, build xxxxx

$ docker compose version
Docker Compose version v2.x.x

$ docker run hello-world
Hello from Docker!
```

### Uso di Docker da WSL

```bash
# Docker è accessibile nativamente da tutte le distribuzioni WSL abilitate

# Eseguire container
docker run -d -p 8080:80 nginx
docker compose up -d

# Build multi-stage
docker build -t myapp:latest .

# Sviluppo con hot-reload (montare il filesystem Linux)
docker run -v /home/renan/project:/app -p 3000:3000 node:20 npm run dev
# NOTA: montare da /home/ (ext4), NON da /mnt/c/ (9P) per performance

# Docker Compose per sviluppo locale
cat > docker-compose.yml << 'EOF'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - .:/app           # Funziona bene se il progetto è in /home/
      - /app/node_modules # Named volume per node_modules
    environment:
      - NODE_ENV=development
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: devpass
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  pgdata:
EOF

docker compose up -d
```

### Risorse e limiti

```ini
# Docker Desktop condivide le risorse della VM WSL 2
# I limiti in .wslconfig si applicano anche a Docker:

# %USERPROFILE%\.wslconfig
[wsl2]
memory=12GB      # RAM condivisa tra Docker e tutte le distribuzioni WSL
processors=6     # CPU condivise
swap=4GB

# Per limitare i singoli container:
# docker run --memory=2g --cpus=2 myapp

# Monitorare risorse Docker:
# docker stats
# docker system df
```

### Alternative a Docker Desktop: Podman in WSL

```bash
# Podman è un'alternativa rootless e daemonless a Docker

# Installazione in Ubuntu WSL:
sudo apt update
sudo apt install -y podman

# Configurazione rootless
# (richiede systemd abilitato in wsl.conf)
podman system migrate

# Uso (compatibile con la sintassi Docker):
podman run -d -p 8080:80 docker.io/library/nginx
podman build -t myapp .
podman compose up -d  # Con podman-compose

# Vantaggi di Podman in WSL:
# - Non richiede Docker Desktop (no licenza per uso commercial)
# - Rootless di default (più sicuro)
# - Daemonless (nessun processo in background)
# - Compatibile con Dockerfile e immagini Docker
# - Supporto pod (come Kubernetes)
```

### Docker Engine nativo in WSL (senza Docker Desktop)

```bash
# Installare Docker Engine direttamente nella distribuzione WSL
# Utile per evitare Docker Desktop (es. licenza)

# Prerequisito: systemd abilitato in /etc/wsl.conf

# Installazione su Ubuntu:
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Aggiungere utente al gruppo docker
sudo usermod -aG docker $USER
newgrp docker

# Avviare Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verifica
docker run hello-world
```

### Dev Containers e ambienti di sviluppo containerizzati

L'integrazione tra WSL 2, Docker e Visual Studio Code tramite **Dev Containers** (precedentemente "Remote - Containers") rappresenta il pattern più avanzato per standardizzare ambienti di sviluppo. L'idea centrale è definire l'intero ambiente — runtime, dipendenze, tool, estensioni dell'editor — in un file `.devcontainer/devcontainer.json` versionato nel repository, eliminando il classico problema "funziona sulla mia macchina".

```
Architettura Dev Containers su WSL 2 + Docker Desktop:

┌──────────────────────────────────────────────────────────────┐
│ Windows Host                                                  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ VS Code (Windows)                                       │ │
│  │  ├── Extension: Dev Containers                          │ │
│  │  ├── Extension: WSL                                     │ │
│  │  └── UI locale → comunica via JSON-RPC con il server    │ │
│  └──────────────────────┬──────────────────────────────────┘ │
│                         │ JSON-RPC over stdio/socket          │
│  ┌──────────────────────▼──────────────────────────────────┐ │
│  │ WSL 2 VM (Hyper-V lightweight)                          │ │
│  │                                                         │ │
│  │  ┌───────────────────────────────────────────────────┐  │ │
│  │  │ Docker Engine (Docker Desktop backend)            │  │ │
│  │  │                                                   │  │ │
│  │  │  ┌─────────────────────────────────────────────┐  │  │ │
│  │  │  │ Dev Container                               │  │  │ │
│  │  │  │  ├── vscode-server (esegue estensioni)      │  │  │ │
│  │  │  │  ├── Runtime (Node 20, Python 3.12, ecc.)   │  │  │ │
│  │  │  │  ├── Tool (git, linter, formatter, ecc.)    │  │  │ │
│  │  │  │  └── /workspace ← bind mount dal repo WSL   │  │  │ │
│  │  │  └─────────────────────────────────────────────┘  │  │ │
│  │  └───────────────────────────────────────────────────┘  │ │
│  │                                                         │ │
│  │  /home/utente/repo/  ← sorgenti su filesystem ext4     │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Best practice per le performance dei bind mount**: il repository sorgente deve risiedere nel filesystem ext4 di WSL (`/home/utente/progetto/`), mai in `/mnt/c/`. Docker Desktop monta i volumi dalla distribuzione WSL tramite il filesystem nativo Linux, evitando il layer di traduzione 9P/Virtio-9P che penalizza drasticamente le operazioni I/O. In test reali, le build `npm install` su un progetto medio risultano 3-5 volte più veloci con sorgenti su ext4 rispetto a `/mnt/c/`.

```jsonc
// .devcontainer/devcontainer.json — esempio per sviluppo Node.js + PostgreSQL
{
  "name": "Node.js & PostgreSQL",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",

  // Features: aggiungono tool senza modificare il Dockerfile
  "features": {
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers/features/node:1": { "version": "20" }
  },

  // Estensioni installate DENTRO il container, non nell'host
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "ms-azuretools.vscode-docker"
      ],
      "settings": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode"
      }
    }
  },

  // Post-create: eseguito dopo la creazione del container
  "postCreateCommand": "npm ci && npm run db:migrate",

  // Forwarding delle porte: accessibili da Windows
  "forwardPorts": [3000, 5432],
  "portsAttributes": {
    "3000": { "label": "App", "onAutoForward": "openBrowser" },
    "5432": { "label": "PostgreSQL", "onAutoForward": "silent" }
  },

  // Utente non-root dentro il container
  "remoteUser": "node"
}
```

```yaml
# .devcontainer/docker-compose.yml
services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached  # Bind mount dal filesystem ext4 WSL
      - node_modules:/workspace/node_modules  # Named volume per node_modules
    command: sleep infinity
    depends_on:
      - db

  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_USER: dev
      POSTGRES_DB: app_dev
      POSTGRES_PASSWORD: devpass  # Solo per sviluppo locale
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  node_modules:
  pgdata:
```

**Gestione risorse condivise tra Docker e WSL**: Docker Desktop e le distribuzioni WSL condividono la stessa VM Hyper-V leggera. La memoria allocata in `.wslconfig` è il tetto massimo per l'intero ecosistema. Quando si eseguono Dev Containers pesanti insieme ad altre distribuzioni WSL, è fondamentale monitorare il consumo complessivo:

```bash
# Monitorare memoria totale della VM WSL (include Docker)
free -h              # Dentro una distribuzione WSL
docker stats         # Consumo per container

# Se la VM consuma troppa RAM, usare autoMemoryReclaim:
# .wslconfig → [experimental] → autoMemoryReclaim=gradual

# Limitare i container singolarmente:
docker run --memory=2g --cpus=1.5 --memory-swap=3g myapp

# Pattern consigliato per .wslconfig con Dev Containers attivi:
# [wsl2]
# memory=16GB           # Su macchine con 32GB+ RAM
# processors=8          # Lasciare almeno 2-4 core a Windows
# swap=8GB              # Swap su SSD per elasticità
# [experimental]
# autoMemoryReclaim=gradual
# sparseVhd=true        # VHDX cresce ma può anche ridursi
```

---

## 10. Applicazioni grafiche — WSLg

### Architettura WSLg

```
┌──────────────────────────────────────────────────────────────┐
│ Windows 11 Host                                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ WSL 2 VM                                               │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │ WSLg System Distro (distro di sistema interna)  │  │  │
│  │  │                                                  │  │  │
│  │  │  ┌────────────┐  ┌────────────┐  ┌───────────┐  │  │  │
│  │  │  │ Weston     │  │ XWayland   │  │ PulseAudio│  │  │  │
│  │  │  │ (Wayland   │  │ (compat.   │  │ (audio    │  │  │  │
│  │  │  │ compositor)│  │ X11)       │  │ server)   │  │  │  │
│  │  │  └─────┬──────┘  └─────┬──────┘  └─────┬─────┘  │  │  │
│  │  │        │               │               │         │  │  │
│  │  │        └───────┬───────┘               │         │  │  │
│  │  │                │                       │         │  │  │
│  │  │         RDP transport            RDP transport   │  │  │
│  │  └────────────────┼───────────────────────┼─────────┘  │  │
│  │                   │                       │            │  │
│  │  ┌────────────────▼───────────────────────▼─────────┐  │  │
│  │  │ Ubuntu (distro utente)                           │  │  │
│  │  │                                                  │  │  │
│  │  │  ┌─────────┐  ┌──────────┐  ┌─────────────────┐ │  │  │
│  │  │  │ Firefox │  │ Nautilus │  │ VS Code (Linux) │ │  │  │
│  │  │  │ (GUI)   │  │ (GUI)    │  │ (GUI)           │ │  │  │
│  │  │  └─────────┘  └──────────┘  └─────────────────┘ │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────┐                                │
│  │ mstsc.exe (RDP client)   │ ← Renderizza le finestre      │
│  │ integrato nel desktop    │    Linux come finestre Windows │
│  └──────────────────────────┘                                │
└──────────────────────────────────────────────────────────────┘
```

WSLg (Windows Subsystem for Linux GUI) permette di eseguire app grafiche Linux integrate nel desktop Windows. Le finestre Linux appaiono come normali finestre Windows, con taskbar, Alt+Tab e clipboard condivisa.

### Prerequisiti

```
Requisiti:
├── Windows 11 (build 22000+) oppure Windows 10 21H2+ con aggiornamento WSL
├── Driver GPU aggiornato (vGPU/WSLg driver):
│   ├── Intel:   https://www.intel.com/content/www/us/en/download/19344/
│   ├── NVIDIA:  https://developer.nvidia.com/cuda/wsl (driver Windows)
│   └── AMD:     https://www.amd.com/en/support (driver Windows Adrenalin)
├── WSL aggiornato: wsl --update
└── Display: qualsiasi risoluzione
```

### Eseguire app grafiche Linux

```bash
# Le app grafiche funzionano automaticamente dopo l'installazione
# Non serve configurare DISPLAY o X server manualmente

# Installare e lanciare app grafiche comuni:

# File manager
sudo apt install -y nautilus
nautilus &

# Browser
sudo apt install -y firefox
firefox &

# Editor di testo
sudo apt install -y gedit
gedit &

# Visualizzatore immagini
sudo apt install -y eog
eog image.png &

# GIMP
sudo apt install -y gimp
gimp &

# LibreOffice
sudo apt install -y libreoffice
libreoffice &

# Terminale grafico
sudo apt install -y gnome-terminal
gnome-terminal &

# IDE (IntelliJ IDEA, PyCharm, ecc.)
# Scaricare il tarball Linux e lanciare
./idea.sh &

# Strumenti di sicurezza con GUI
sudo apt install -y wireshark
sudo wireshark &
```

### Configurazione display e audio

```bash
# WSLg imposta automaticamente le variabili d'ambiente:
echo $DISPLAY          # Tipicamente :0
echo $WAYLAND_DISPLAY  # Tipicamente wayland-0
echo $PULSE_SERVER     # Server PulseAudio

# Se un'app non trova il display:
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0

# Audio: PulseAudio è configurato automaticamente
# Testare audio:
sudo apt install -y pulseaudio-utils
paplay /usr/share/sounds/freedesktop/stereo/bell.oga

# Per app che richiedono specificamente X11:
# XWayland è già in esecuzione, la maggior parte delle app X11 funziona

# Per app che richiedono OpenGL (3D):
sudo apt install -y mesa-utils
glxinfo | grep "OpenGL renderer"
# Dovrebbe mostrare il GPU dell'host (via D3D12 → OpenGL translation)

glxgears  # Test rendering 3D
```

### Integrazione con il desktop Windows

```
Funzionalità di integrazione WSLg:
├── Finestre Linux appaiono come finestre Windows normali
├── Alt+Tab include le finestre Linux
├── Clipboard condivisa (copia/incolla bidirezionale)
├── Drag & drop supportato (con limitazioni)
├── Notifiche del sistema Linux appaiono in Windows
├── Icone nella taskbar per le app Linux attive
└── Snap layout funziona con le finestre Linux
```

---

## 11. Sviluppo con WSL

### VS Code + WSL (Remote - WSL)

```bash
# Installare l'estensione "WSL" (precedentemente "Remote - WSL") in VS Code

# Da WSL, aprire VS Code nella directory corrente:
code .
# VS Code si connette automaticamente alla sessione WSL

# Oppure da Windows:
# VS Code → Ctrl+Shift+P → "WSL: Connect to WSL"
# VS Code → Ctrl+Shift+P → "WSL: Connect to WSL using Distro..."
```

```
Architettura VS Code Remote - WSL:
┌──────────────────────┐     ┌──────────────────────────┐
│ Windows              │     │ WSL 2                     │
│                      │     │                           │
│ VS Code UI           │────►│ VS Code Server            │
│ (frontend)           │     │ (backend)                 │
│                      │     │ ├── File system access    │
│                      │     │ ├── Terminal              │
│                      │     │ ├── Debugger              │
│                      │     │ ├── Extensions (server)   │
│                      │     │ └── Language servers       │
└──────────────────────┘     └──────────────────────────┘

Vantaggi:
├── File I/O nativo su ext4 (velocissimo)
├── Extensions eseguono nel contesto Linux
├── Debugging nel contesto Linux
├── Terminal integrato = shell Linux
├── Git usa il git di Linux
├── Tutti i tool di sviluppo sono quelli Linux
└── Nessun overhead di sincronizzazione file
```

### Git in WSL

```bash
# Git in WSL è completamente separato dal Git di Windows
# Configurazione iniziale:
git config --global user.name "Renan Augusto Macena"
git config --global user.email "ciupsciups@libero.it"
git config --global core.autocrlf input    # Fondamentale per cross-platform
git config --global init.defaultBranch main

# Line endings: WSL usa LF, Windows usa CRLF
# Regola: impostare core.autocrlf=input in WSL
# Questo converte CRLF → LF al commit, non tocca i file al checkout

# .gitattributes nel progetto (raccomandato):
cat > .gitattributes << 'EOF'
* text=auto eol=lf
*.{cmd,bat,ps1} text eol=crlf
*.{png,jpg,gif,ico} binary
*.{zip,tar,gz} binary
EOF

# SSH keys per git:
# Opzione 1: Chiavi separate in WSL
ssh-keygen -t ed25519 -C "renan@wsl"
cat ~/.ssh/id_ed25519.pub  # → Aggiungere a GitHub/GitLab

# Opzione 2: Condividere le chiavi di Windows
cp /mnt/c/Users/Renan/.ssh/id_ed25519 ~/.ssh/
cp /mnt/c/Users/Renan/.ssh/id_ed25519.pub ~/.ssh/
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

# Opzione 3: Usare ssh-agent di Windows da WSL
# (evita di duplicare le chiavi)
# In .bashrc o .zshrc:
# eval $(/mnt/c/Windows/System32/OpenSSH/ssh-agent.exe)

# Credential manager condiviso con Windows:
git config --global credential.helper "/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe"
```

### Setup ambiente di sviluppo completo

```bash
# ═══════════════════════════════════════════════════════════
# Setup tipico per una workstation di sviluppo WSL
# ═══════════════════════════════════════════════════════════

# Aggiornare il sistema
sudo apt update && sudo apt upgrade -y

# ─── Strumenti essenziali ──────────────────────────────────
sudo apt install -y \
  build-essential gcc g++ make cmake \
  git curl wget unzip jq \
  htop tree ncdu \
  tmux screen \
  net-tools dnsutils iputils-ping \
  apt-transport-https ca-certificates gnupg lsb-release

# ─── Shell e terminale ─────────────────────────────────────
# Zsh + Oh My Zsh (opzionale)
sudo apt install -y zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Starship prompt (opzionale, cross-shell)
curl -sS https://starship.rs/install.sh | sh

# ─── Node.js (via nvm) ────────────────────────────────────
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
source ~/.bashrc
nvm install --lts
nvm install 22
node --version
npm --version

# ─── Python ───────────────────────────────────────────────
sudo apt install -y python3 python3-pip python3-venv python3-dev
python3 -m pip install --user pipx
pipx ensurepath

# pyenv per gestire versioni Python multiple
curl -fsSL https://pyenv.run | bash
# Aggiungere al .bashrc:
# export PYENV_ROOT="$HOME/.pyenv"
# command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
# eval "$(pyenv init -)"

# ─── Go ───────────────────────────────────────────────────
# Installazione manuale (versione specifica)
GO_VERSION="1.23.0"
wget "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz"
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz"
rm "go${GO_VERSION}.linux-amd64.tar.gz"
echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> ~/.bashrc

# ─── Rust ─────────────────────────────────────────────────
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env

# ─── Java (via SDKMAN) ───────────────────────────────────
curl -s "https://get.sdkman.io" | bash
source "$HOME/.sdkman/bin/sdkman-init.sh"
sdk install java 21.0.2-tem

# ─── Kubernetes ───────────────────────────────────────────
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install kubectl /usr/local/bin/
rm kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# k9s (TUI per Kubernetes)
curl -sS https://webinstall.dev/k9s | bash

# ─── IaC e DevOps ────────────────────────────────────────
# Terraform (via tfenv)
git clone https://github.com/tfutils/tfenv.git ~/.tfenv
echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
tfenv install latest
tfenv use latest

# Ansible
pipx install ansible-core
pipx inject ansible-core ansible-lint

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws/

# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# ─── Database clients ────────────────────────────────────
sudo apt install -y postgresql-client redis-tools
```

### Gestione dei language runtimes

```bash
# Pattern raccomandato: usare version manager per ogni linguaggio

# Node.js: nvm
nvm install 20
nvm install 22
nvm use 22
nvm alias default 22

# Python: pyenv
pyenv install 3.12.4
pyenv install 3.11.9
pyenv global 3.12.4
pyenv local 3.11.9  # Per progetto specifico

# Go: goenv o installazione manuale
# La gestione delle versioni Go è meno critica — una versione basta

# Java: SDKMAN
sdk install java 21.0.2-tem
sdk install java 17.0.11-tem
sdk use java 21.0.2-tem

# Ruby: rbenv
# Rust: rustup (gestisce toolchain e versioni)
```

---

## 12. Supporto systemd

### Abilitare systemd

```ini
# /etc/wsl.conf
[boot]
systemd=true
```

```bash
# Riavviare la distribuzione dopo la modifica:
# Da PowerShell: wsl --terminate Ubuntu
# Poi riaprire la distribuzione

# Verificare che systemd sia attivo:
systemctl list-units --type=service --state=running
ps -p 1 -o comm=
# Output: systemd (se attivo)
# Output: init (se non attivo)
```

### Gestione servizi con systemd

```bash
# Con systemd abilitato, i servizi funzionano come su un Linux reale

# ─── Docker ────────────────────────────────────────────────
sudo systemctl start docker
sudo systemctl enable docker
sudo systemctl status docker

# ─── SSH Server ────────────────────────────────────────────
sudo apt install -y openssh-server
sudo systemctl start ssh
sudo systemctl enable ssh
# SSH sarà disponibile sulla porta 22 della distribuzione WSL

# ─── Database ─────────────────────────────────────────────
sudo apt install -y postgresql
sudo systemctl start postgresql
sudo systemctl enable postgresql

sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# ─── Cron ──────────────────────────────────────────────────
sudo systemctl start cron
sudo systemctl enable cron
crontab -e

# ─── Nginx ─────────────────────────────────────────────────
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# ─── Comandi systemctl comuni ──────────────────────────────
sudo systemctl start <servizio>
sudo systemctl stop <servizio>
sudo systemctl restart <servizio>
sudo systemctl enable <servizio>     # Avvio automatico al boot WSL
sudo systemctl disable <servizio>
sudo systemctl status <servizio>
sudo systemctl is-active <servizio>

# Vedere tutti i servizi attivi
systemctl list-units --type=service --state=running

# Vedere i log di un servizio
journalctl -u docker -f
journalctl -u ssh --since "1 hour ago"
```

### Snap con systemd

```bash
# Con systemd abilitato, snap funziona in WSL
sudo apt install -y snapd
sudo snap install core

# Installare app via snap:
sudo snap install --classic code        # VS Code
sudo snap install --classic go          # Go
sudo snap install --classic kubectl     # kubectl

# Nota: le snap con interfaccia grafica richiedono WSLg
```

### Timer systemd (alternativa a cron)

```bash
# Creare un timer systemd per task periodici

# Servizio:
sudo tee /etc/systemd/system/backup-projects.service << 'EOF'
[Unit]
Description=Backup dei progetti di sviluppo

[Service]
Type=oneshot
ExecStart=/home/renan/scripts/backup.sh
User=renan
EOF

# Timer:
sudo tee /etc/systemd/system/backup-projects.timer << 'EOF'
[Unit]
Description=Timer per backup giornaliero

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now backup-projects.timer
systemctl list-timers
```

### Boot command personalizzato

```ini
# /etc/wsl.conf
[boot]
systemd=true
# Comando eseguito al boot (prima dell'accesso utente)
command="mount --make-rshared / ; /usr/local/bin/custom-init.sh"
```

---

## 13. Supporto GPU — CUDA, DirectML, Machine Learning

### Architettura GPU in WSL 2

```
┌────────────────────────────────────────────────────────────┐
│ Windows Host                                               │
│                                                            │
│  GPU Hardware (NVIDIA, AMD, Intel)                         │
│       │                                                    │
│  GPU Driver Windows (NVIDIA/AMD/Intel)                     │
│       │                                                    │
│  ┌────▼─────────────────────────────────────────────────┐  │
│  │ WSL 2 VM                                              │  │
│  │                                                       │  │
│  │  /dev/dxg (paravirtualized GPU device)                │  │
│  │       │                                               │  │
│  │  ┌────▼────────────────────────────────┐              │  │
│  │  │  libd3d12.so (DirectX 12 in Linux)  │              │  │
│  │  │       │                              │              │  │
│  │  │  ┌────▼────┐  ┌───────────┐         │              │  │
│  │  │  │ CUDA    │  │ DirectML  │         │              │  │
│  │  │  │ toolkit │  │           │         │              │  │
│  │  │  └────┬────┘  └─────┬─────┘         │              │  │
│  │  │       │             │                │              │  │
│  │  │  ┌────▼─────────────▼────────────┐   │              │  │
│  │  │  │ TensorFlow / PyTorch /        │   │              │  │
│  │  │  │ ONNX Runtime / etc.           │   │              │  │
│  │  │  └───────────────────────────────┘   │              │  │
│  │  └──────────────────────────────────────┘              │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘

NOTA: Non installare driver GPU Linux dentro WSL!
Il driver Windows viene condiviso automaticamente via /dev/dxg.
```

### Prerequisiti GPU

```bash
# 1. Installare il driver GPU Windows più recente
#    NVIDIA: https://developer.nvidia.com/cuda/wsl (versione WSL)
#    AMD: driver Adrenalin standard
#    Intel: driver standard

# 2. Verificare che il GPU sia visibile in WSL:
nvidia-smi    # Per NVIDIA
# Dovrebbe mostrare il GPU e la versione del driver

# Se nvidia-smi non funziona:
ls /dev/dxg
# Se esiste, il GPU è esposto a WSL
# Se non esiste, aggiornare il driver Windows e WSL
```

### CUDA in WSL

```bash
# NOTA CRITICA: NON installare il driver NVIDIA Linux in WSL!
# Il driver Windows viene condiviso automaticamente.
# Installare SOLO il CUDA toolkit.

# Installare CUDA Toolkit (senza driver):
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-6  # Solo toolkit, non cuda (che include il driver)

# Aggiungere al PATH:
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Verificare:
nvcc --version
nvidia-smi

# Test CUDA:
cd /usr/local/cuda/samples/1_Utilities/deviceQuery
sudo make
./deviceQuery
# Dovrebbe mostrare: Result = PASS
```

### Machine Learning in WSL

```bash
# ─── PyTorch con CUDA ─────────────────────────────────────
python3 -m venv ~/ml-env
source ~/ml-env/bin/activate

# PyTorch con supporto CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verifica:
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
"

# ─── TensorFlow con CUDA ─────────────────────────────────
pip install tensorflow[and-cuda]

python3 -c "
import tensorflow as tf
print(f'TensorFlow version: {tf.__version__}')
print(f'GPU devices: {tf.config.list_physical_devices(\"GPU\")}')
"

# ─── DirectML (per GPU AMD e Intel) ──────────────────────
pip install tensorflow-directml
pip install torch-directml

# DirectML funziona con QUALSIASI GPU (NVIDIA, AMD, Intel)
# tramite la traduzione DirectX 12

# ─── Jupyter Notebook ────────────────────────────────────
pip install jupyterlab
jupyter lab --no-browser --port=8888
# Accessibile da Windows su http://localhost:8888

# ─── Hugging Face + Transformers ─────────────────────────
pip install transformers datasets accelerate
```

### Performance GPU in WSL vs Linux nativo

```
Overhead GPU in WSL 2:
├── Training ML: ~5-10% overhead rispetto a Linux nativo
├── Inference: ~2-5% overhead
├── CUDA compute: ~3-8% overhead
└── OpenGL rendering (via WSLg): ~10-20% overhead

Per la maggior parte dei casi, l'overhead è accettabile.
Per workload di produzione pesanti, Linux nativo resta preferibile.
```

---

## 14. Operazioni avanzate

### Creare una distribuzione custom

```bash
# Metodo 1: Da un Dockerfile
cat > Dockerfile << 'EOF'
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    sudo wget curl git vim nano \
    build-essential python3 python3-pip \
    && apt-get clean

# Creare utente
RUN useradd -m -s /bin/bash devuser && \
    echo "devuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Configurazione WSL
RUN echo '[user]\ndefault=devuser\n[boot]\nsystemd=true' > /etc/wsl.conf

USER devuser
WORKDIR /home/devuser
EOF

docker build -t my-wsl-distro .
docker run -t my-wsl-distro ls /
docker export $(docker ps -lq) > my-wsl-distro.tar

# Importare in WSL:
wsl --import MyDistro C:\WSL\MyDistro my-wsl-distro.tar
wsl -d MyDistro
```

```bash
# Metodo 2: Da un rootfs minimo (Alpine)
curl -LO https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/x86_64/alpine-minirootfs-3.20.0-x86_64.tar.gz
wsl --import Alpine C:\WSL\Alpine alpine-minirootfs-3.20.0-x86_64.tar.gz

# Configurare Alpine dopo l'import:
wsl -d Alpine
apk update
apk add bash sudo shadow
adduser -D -s /bin/bash devuser
echo "devuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
```

```bash
# Metodo 3: Da un rootfs Arch Linux
# Scaricare il bootstrap tarball da archlinux.org
curl -LO https://geo.mirror.pkgbuild.com/iso/latest/archlinux-bootstrap-x86_64.tar.zst
# Estrarre il rootfs
zstd -d archlinux-bootstrap-x86_64.tar.zst
wsl --import Arch C:\WSL\Arch archlinux-bootstrap-x86_64.tar
```

### Esportare e importare distribuzioni

```powershell
# ─── Backup completo ──────────────────────────────────────
# Formato tar (universale)
wsl --export Ubuntu C:\Backup\ubuntu-2026-05-22.tar

# Formato VHD (preserva struttura ext4, più veloce)
wsl --export Ubuntu C:\Backup\ubuntu-2026-05-22.vhdx --vhd

# ─── Restore ──────────────────────────────────────────────
# Da tar
wsl --import Ubuntu-Restore D:\WSL\Ubuntu-Restore C:\Backup\ubuntu-2026-05-22.tar

# Da VHD (in-place, senza copia)
wsl --import-in-place Ubuntu-Restore C:\Backup\ubuntu-2026-05-22.vhdx

# ─── Automazione backup ──────────────────────────────────
# Script PowerShell per backup schedulato:
$timestamp = Get-Date -Format "yyyy-MM-dd"
$backupDir = "D:\Backup\WSL"
New-Item -ItemType Directory -Path $backupDir -Force
wsl --export Ubuntu "$backupDir\ubuntu-$timestamp.tar"
# Aggiungere a Task Scheduler per esecuzione settimanale
```

### Gestione disco VHDX

```powershell
# I dischi VHDX di WSL crescono ma non si riducono automaticamente
# (a meno che sparseVhd=true non sia abilitato in .wslconfig)

# Trovare il file VHDX:
# %LOCALAPPDATA%\Packages\CanonicalGroupLimited.Ubuntu*\LocalState\ext4.vhdx

# Compattare manualmente il VHDX:
wsl --shutdown
# PowerShell (come Admin):
Optimize-VHD -Path "C:\Users\Renan\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx" -Mode Full

# Oppure via diskpart:
wsl --shutdown
diskpart
# select vdisk file="C:\...\ext4.vhdx"
# compact vdisk
# exit

# Abilitare compattazione automatica:
# In .wslconfig:
# [experimental]
# sparseVhd=true
```

### Ridimensionare il disco VHDX

```bash
# Il disco VHDX ha un limite massimo di default (256 GB per le distro recenti)
# Per aumentarlo:

# Da PowerShell (come Admin):
wsl --shutdown
$vhdxPath = "$env:LOCALAPPDATA\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx"
Resize-VHD -Path $vhdxPath -SizeBytes 512GB

# Da dentro WSL, espandere la partizione:
sudo mount -t devtmpfs none /dev
sudo resize2fs /dev/sdc   # Il device può variare
```

### Kernel personalizzato

```bash
# Compilare un kernel custom per WSL 2

# Clonare il sorgente del kernel WSL
git clone https://github.com/microsoft/WSL2-Linux-Kernel.git
cd WSL2-Linux-Kernel
git checkout linux-msft-wsl-6.6.y   # Branch raccomandato

# Configurare (partire dalla config Microsoft)
cp Microsoft/config-wsl .config
make menuconfig   # Modificare opzioni

# Compilare
make -j$(nproc) KCONFIG_CONFIG=.config

# Il kernel compilato è in: arch/x86/boot/bzImage
# Copiarlo su Windows:
cp arch/x86/boot/bzImage /mnt/c/WSL/custom-kernel

# Configurare .wslconfig:
# [wsl2]
# kernel=C:\\WSL\\custom-kernel

# Riavviare WSL:
# wsl --shutdown
# wsl
# Verificare: uname -r
```

### Nested virtualization (KVM in WSL)

```ini
# In .wslconfig:
[wsl2]
nestedVirtualization=true
```

```bash
# Verificare supporto KVM:
ls /dev/kvm
# Se esiste, KVM è disponibile

# Installare QEMU:
sudo apt install -y qemu-kvm libvirt-daemon-system
sudo systemctl start libvirtd

# Utile per:
# - Android Emulator dentro WSL
# - VM dentro WSL per test
# - Minikube con driver KVM
```

---

## 15. WSL per sysadmin

### Strumenti Linux su Windows

```bash
# WSL dà accesso a tutto l'arsenale di strumenti Linux
# su una workstation Windows corporate

# ─── Ricerca e manipolazione testo ─────────────────────────
# Cercare in tutti i log Windows da WSL:
grep -r "ERROR" /mnt/c/Windows/Logs/
find /mnt/c/Users/Renan/ -name "*.log" -mtime -7 -exec grep -l "fail" {} \;
awk '{print $1}' /mnt/c/inetpub/logs/LogFiles/W3SVC1/u_ex*.log | sort | uniq -c | sort -rn | head -20

# ─── SSH e gestione remota ─────────────────────────────────
# SSH nativo (più affidabile di PuTTY)
ssh -i ~/.ssh/id_ed25519 admin@server.corp.com
ssh -J bastion.corp.com admin@internal-server.corp.com

# SSH tunneling
ssh -L 8080:internal-db:5432 bastion.corp.com
# Ora PostgreSQL su internal-db è accessibile da Windows su localhost:8080

# SSH config per gestire molti server:
cat > ~/.ssh/config << 'EOF'
Host bastion
    HostName bastion.corp.com
    User admin
    IdentityFile ~/.ssh/corp_key

Host web-*
    ProxyJump bastion
    User deploy
    IdentityFile ~/.ssh/deploy_key

Host web-prod
    HostName 10.0.1.10

Host web-staging
    HostName 10.0.2.10
EOF

ssh web-prod   # Connessione tramite bastion jump automatico
```

### Ansible da WSL

```bash
# WSL è perfetto per eseguire Ansible (che richiede Linux/macOS)

# Installazione:
pipx install ansible-core
pipx inject ansible-core ansible-lint pywinrm

# Gestire server Linux da WSL:
ansible all -i inventory.ini -m ping

# Gestire server Windows da WSL (via WinRM):
cat > inventory.ini << 'EOF'
[windows]
winserver1 ansible_host=192.168.1.100

[windows:vars]
ansible_user=Administrator
ansible_password={{ vault_win_password }}
ansible_connection=winrm
ansible_winrm_transport=ntlm
ansible_winrm_server_cert_validation=ignore
ansible_port=5985
EOF

ansible windows -i inventory.ini -m win_ping

# Playbook per configurare server Windows:
cat > configure-windows.yml << 'EOF'
---
- name: Configurare server Windows
  hosts: windows
  tasks:
    - name: Installare IIS
      win_feature:
        name: Web-Server
        state: present

    - name: Configurare firewall
      win_firewall_rule:
        name: Allow HTTP
        localport: 80
        action: allow
        direction: in
        protocol: tcp
        state: present
EOF

ansible-playbook -i inventory.ini configure-windows.yml
```

### Scripting cross-platform

```bash
# Eseguire comandi PowerShell da WSL:
powershell.exe -Command "Get-Service | Where-Object {$_.Status -eq 'Running'}"
powershell.exe -Command "Get-EventLog -LogName System -Newest 50"
powershell.exe -Command "Get-WmiObject -Class Win32_Processor"

# Combinare tool Linux e Windows in pipeline:
powershell.exe -Command "Get-EventLog -LogName System -Newest 1000 | ConvertTo-Csv" | \
  grep -i "error" | \
  awk -F',' '{print $6}' | \
  sort | uniq -c | sort -rn

# Script che usa entrambi i mondi:
#!/bin/bash
# system-report.sh — genera report con strumenti Linux e Windows

echo "=== Report Sistema $(date -Iseconds) ==="

echo -e "\n--- Risorse WSL ---"
free -h
df -h /

echo -e "\n--- Servizi Windows ---"
powershell.exe -Command "Get-Service | Where Status -eq Running | Measure-Object | Select Count"

echo -e "\n--- Porte in ascolto (Linux) ---"
ss -tlnp

echo -e "\n--- Porte in ascolto (Windows) ---"
powershell.exe -Command "Get-NetTCPConnection -State Listen | Select LocalPort,OwningProcess | Sort LocalPort"

echo -e "\n--- Ultimi errori log Windows ---"
powershell.exe -Command "Get-EventLog -LogName System -EntryType Error -Newest 10 | Format-Table TimeGenerated,Source,Message -AutoSize"
```

### Monitoring e automazione

```bash
# Monitorare risorse WSL:
htop                    # Monitor interattivo
vmstat 1                # Statistiche VM ogni secondo
iostat -x 1             # I/O disk
sar -u 1 5              # CPU usage (installare sysstat)

# Creare alerting con script:
#!/bin/bash
# alert-memory.sh
THRESHOLD=80
USAGE=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
if [ "$USAGE" -gt "$THRESHOLD" ]; then
    # Notifica Windows via PowerShell:
    powershell.exe -Command "
        [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
        [System.Windows.Forms.MessageBox]::Show('WSL Memory: ${USAGE}%', 'Alert', 'OK', 'Warning')
    "
fi
```

---

## 16. Sicurezza

### Modello di sicurezza WSL

```
┌──────────────────────────────────────────────────────────────┐
│ Considerazioni di sicurezza WSL                              │
│                                                              │
│  1. WSL esegue con i privilegi dell'utente Windows corrente  │
│     → root in WSL ≠ admin in Windows                         │
│     → Ma: root in WSL può accedere a TUTTI i file           │
│       dell'utente Windows (via /mnt/c/)                      │
│                                                              │
│  2. Il filesystem Linux è accessibile da Windows             │
│     → Antivirus Windows scansiona anche i file WSL           │
│     → Ma: malware Windows potrebbe accedere ai file WSL      │
│                                                              │
│  3. La rete WSL (NAT) è isolata ma non firewalled            │
│     → Il traffico WSL esce dalla NIC Windows                 │
│     → VPN Windows copre anche WSL (con mirrored mode)        │
│                                                              │
│  4. I processi WSL sono visibili da Windows                  │
│     → Task Manager mostra "Vmmem" (la VM WSL)                │
│     → Ma: i singoli processi Linux non sono visibili         │
└──────────────────────────────────────────────────────────────┘
```

### Hardening WSL

```bash
# ─── Permessi file SSH ─────────────────────────────────────
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_*
chmod 644 ~/.ssh/id_*.pub
chmod 644 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/config

# ─── Limitare l'interop con Windows ───────────────────────
# Se non serve eseguire comandi Windows da WSL:
# /etc/wsl.conf:
# [interop]
# enabled=false
# appendWindowsPath=false

# ─── Firewall WSL (Windows 11 22H2+) ─────────────────────
# In .wslconfig:
# [wsl2]
# firewall=true
# → Le regole del Windows Firewall si applicano anche a WSL

# ─── Disabilitare automount se non necessario ─────────────
# /etc/wsl.conf:
# [automount]
# enabled=false
# → WSL non monta automaticamente i dischi Windows

# ─── Audit dei servizi in ascolto ─────────────────────────
ss -tlnp          # Porte TCP in ascolto
ss -ulnp          # Porte UDP in ascolto
# Disabilitare servizi non necessari:
sudo systemctl disable --now ssh   # Se SSH non serve

# ─── Aggiornamenti di sicurezza ───────────────────────────
# Abilitare aggiornamenti automatici:
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Isolamento tra distribuzioni

```bash
# Ogni distribuzione WSL 2 ha:
# ├── Filesystem ext4 separato (VHDX diverso)
# ├── Namespace di processo separato
# ├── Utenti separati
# └── Configurazione separata (/etc/wsl.conf)

# MA condividono:
# ├── Lo stesso kernel Linux
# ├── La stessa VM Hyper-V
# ├── La rete (stesso IP in mirrored mode)
# ├── L'accesso al filesystem Windows (/mnt/c/)
# └── Il GPU

# Per isolamento forte tra ambienti:
# → Usare container Docker dentro WSL
# → Oppure VM separate (Hyper-V, non WSL)
```

### Protezione dei segreti

```bash
# Non lasciare segreti in chiaro nel filesystem WSL
# Il VHDX è un file accessibile da Windows

# Opzione 1: Usare un password manager CLI
sudo apt install -y pass
gpg --gen-key
pass init <gpg-key-id>
pass insert cloud/aws-access-key

# Opzione 2: Variabili d'ambiente (per sessione)
# In .bashrc (NON committare mai in git):
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# Opzione 3: Credential manager di Windows da WSL
git config --global credential.helper "/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe"

# Opzione 4: 1Password CLI / Bitwarden CLI
# Integrazioni native disponibili per WSL

# ATTENZIONE: il file VHDX è leggibile come file da Windows
# Un utente Windows con accesso al profilo può montare il VHDX
# e leggere tutti i file, inclusi segreti e chiavi SSH
```

### Windows Defender e WSL

```
Windows Defender e antivirus:
├── Scansionano i file WSL quando acceduti da Windows (\\wsl$\)
├── Possono causare rallentamenti significativi su I/O pesante
├── Esclusioni raccomandate per performance:
│   ├── %LOCALAPPDATA%\Packages\CanonicalGroupLimited.*
│   ├── Cartelle di build/compile (node_modules, .cargo, ecc.)
│   └── File VHDX delle distribuzioni WSL
│
│   PowerShell (come Admin):
│   Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\Packages"
│   Add-MpPreference -ExclusionProcess "vmmem"
│
└── NOTA SICUREZZA: escludere il path WSL riduce la protezione
    Valutare il rischio nel contesto dell'ambiente
```

### Microsoft Defender for Endpoint — Plugin WSL

A partire da WSL 2.0.9, Microsoft offre un **plugin MDE dedicato per WSL** che estende la protezione endpoint direttamente dentro le distribuzioni Linux, senza richiedere l'installazione di un agente Linux separato. Il plugin opera attraverso l'architettura di estensibilità WSL, iniettando un componente di monitoraggio nella VM leggera Hyper-V.

```
Architettura del Plugin MDE per WSL:

┌──────────────────────────────────────────────────────────────┐
│ Windows Host (con MDE onboarded)                              │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ Microsoft Defender for Endpoint (Sense service)          ││
│  │  └── Riceve telemetria aggregata da host + WSL           ││
│  └──────────────────────────┬───────────────────────────────┘│
│                             │ Named pipe / Hyper-V socket     │
│  ┌──────────────────────────▼───────────────────────────────┐│
│  │ WSL 2 VM                                                 ││
│  │                                                          ││
│  │  ┌────────────────────────────────────────────────────┐  ││
│  │  │ WSL Plugin MDE (wsl-pro-service)                   │  ││
│  │  │  ├── Audit subsystem: monitora syscall critiche    │  ││
│  │  │  │   (execve, connect, open su path sensibili)     │  ││
│  │  │  ├── Network monitor: cattura flussi di rete       │  ││
│  │  │  │   (connessioni in uscita, porte in ascolto)     │  ││
│  │  │  ├── File integrity: rileva modifiche a binari     │  ││
│  │  │  │   critici (/usr/bin, /usr/sbin, /etc/shadow)    │  ││
│  │  │  └── Anti-malware: scansione real-time dei file    │  ││
│  │  └────────────────────────┬───────────────────────────┘  ││
│  │                           │                               ││
│  │  ┌────────────────────────▼───────────────────────────┐  ││
│  │  │ Distribuzioni WSL (Ubuntu, Debian, ecc.)           │  ││
│  │  │  └── Processi utente monitorati trasparentemente   │  ││
│  │  └────────────────────────────────────────────────────┘  ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

Il plugin non richiede configurazione manuale nelle singole distribuzioni. Una volta che il dispositivo Windows è onboarded in MDE e WSL è aggiornato a 2.0.9+, il plugin si attiva automaticamente. Gli eventi di sicurezza rilevati dentro WSL appaiono nel portale Microsoft Defender XDR come alert associati al dispositivo host, con contesto aggiuntivo che identifica la distribuzione WSL di origine.

```powershell
# Verificare che il plugin WSL sia attivo (PowerShell Admin):
wsl --version
# WSL versione: 2.4.x
# Versione kernel: 6.6.x
# → Il plugin è supportato dalla versione 2.0.9+

# Verificare lo stato del plugin dalla distribuzione WSL:
wsl -d Ubuntu -e sh -c "ps aux | grep -i defender"

# Se il plugin non appare, aggiornare WSL:
wsl --update

# Gestire il plugin tramite Intune Settings Catalog:
# Microsoft Defender > WSL > AllowWSLDEAutoInstall = Enabled
```

### Hyper-V Firewall — protezione di rete integrata

A partire da Windows 11 22H2 e WSL 2.0.9+, il **Hyper-V Firewall** è abilitato di default per le distribuzioni WSL 2. Questo significa che le regole di Windows Defender Firewall vengono automaticamente applicate anche al traffico di rete generato dalla VM WSL, eliminando un gap di sicurezza storico dove WSL operava in un ambiente di rete essenzialmente non filtrato.

Il meccanismo funziona a livello dell'host networking stack di Hyper-V, intercettando i pacchetti prima che raggiungano l'interfaccia virtuale della VM WSL. Questo è diverso dal configurare `iptables` dentro la distribuzione Linux — le regole Windows Firewall hanno priorità e vengono applicate indipendentemente dalla configurazione di rete interna alla distribuzione.

```powershell
# ─── Gestione Hyper-V Firewall per WSL ─────────────────────

# Verificare lo stato attuale:
Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore

# Creare una regola specifica per WSL (esempio: bloccare porta 22 in uscita):
New-NetFirewallHyperVRule -Name "BlockWSL-SSH-Out" `
    -DisplayName "Blocca SSH in uscita da WSL" `
    -Direction Outbound `
    -VMCreatorId "{40E0AC32-46A5-438A-A0B2-2B479926381D}" `
    -Protocol TCP `
    -RemotePort 22 `
    -Action Block

# Il VMCreatorId per WSL è sempre {40E0AC32-46A5-438A-A0B2-2B479926381D}

# Elencare regole Hyper-V Firewall attive:
Get-NetFirewallHyperVRule | Where-Object { $_.Enabled -eq "True" } |
    Format-Table Name, Direction, Action, Protocol, RemotePort

# Disabilitare temporaneamente il firewall Hyper-V per WSL (sconsigliato):
# .wslconfig → [wsl2] → firewall=false

# Regola per permettere solo HTTPS e DNS da WSL:
New-NetFirewallHyperVRule -Name "AllowWSL-HTTPS" `
    -Direction Outbound `
    -VMCreatorId "{40E0AC32-46A5-438A-A0B2-2B479926381D}" `
    -Protocol TCP -RemotePort 443 -Action Allow

New-NetFirewallHyperVRule -Name "AllowWSL-DNS" `
    -Direction Outbound `
    -VMCreatorId "{40E0AC32-46A5-438A-A0B2-2B479926381D}" `
    -Protocol UDP -RemotePort 53 -Action Allow
```

---

## 16b. WSL in ambiente enterprise

Nelle organizzazioni che gestiscono centinaia o migliaia di workstation sviluppatore, WSL deve essere governato centralmente per garantire conformità, sicurezza e standardizzazione. Microsoft ha progressivamente aggiunto strumenti di gestione enterprise per WSL tramite **Intune Settings Catalog**, **Group Policy (GPO)** e integrazione con **Microsoft Defender for Endpoint**.

### Gestione WSL tramite Intune Settings Catalog

Dal 2024, Intune include un set dedicato di impostazioni per WSL nel **Settings Catalog**, accessibile da Devices → Configuration → Create → Settings Catalog → cercando "WSL". Queste impostazioni permettono di controllare granularmente cosa gli utenti possono fare con WSL sui dispositivi gestiti.

```
Impostazioni disponibili nel Settings Catalog di Intune per WSL:

┌────────────────────────────────────────────────────────────────┐
│ Impostazione                │ Valori         │ Effetto          │
├─────────────────────────────┼────────────────┼──────────────────┤
│ AllowWSL                    │ 0 / 1          │ Abilita/disabilita│
│                             │                │ WSL interamente  │
├─────────────────────────────┼────────────────┼──────────────────┤
│ AllowInboxWSL               │ 0 / 1          │ Consente la      │
│                             │                │ versione inbox   │
│                             │                │ (integrata in    │
│                             │                │ Windows, non lo  │
│                             │                │ Store)           │
├─────────────────────────────┼────────────────┼──────────────────┤
│ AllowWSL1                   │ 0 / 1          │ Permette WSL 1   │
│                             │                │ (legacy). 0 =    │
│                             │                │ solo WSL 2       │
├─────────────────────────────┼────────────────┼──────────────────┤
│ AllowCustomKernel           │ 0 / 1          │ Se 0, impedisce  │
│                             │                │ kernel custom    │
│                             │                │ in .wslconfig    │
├─────────────────────────────┼────────────────┼──────────────────┤
│ AllowKernelDebugging        │ 0 / 1          │ Debug del kernel │
│                             │                │ WSL (security    │
│                             │                │ risk)            │
├─────────────────────────────┼────────────────┼──────────────────┤
│ AllowNestedVirtualization   │ 0 / 1          │ Virtualizzazione │
│                             │                │ annidata in WSL  │
├─────────────────────────────┼────────────────┼──────────────────┤
│ AllowCustomNetworking       │ 0 / 1          │ Networking       │
│                             │                │ personalizzato   │
│                             │                │ (mirrored, ecc.) │
├─────────────────────────────┼────────────────┼──────────────────┤
│ AllowDeveloperFeatures      │ 0 / 1          │ Funzionalità     │
│                             │                │ sperimentali     │
└────────────────────────────────────────────────────────────────┘

Configurazione raccomandata per ambienti enterprise:
  AllowWSL             = 1   (permettere WSL)
  AllowWSL1            = 0   (forzare WSL 2 — più sicuro, VM isolata)
  AllowCustomKernel    = 0   (impedire kernel non verificati)
  AllowKernelDebugging = 0   (ridurre superficie d'attacco)
  AllowInboxWSL        = 0   (forzare la versione Store, aggiornabile)
```

### Gestione WSL tramite Group Policy (GPO)

Per ambienti Active Directory tradizionali, Microsoft fornisce template ADMX per WSL. Questi offrono le stesse impostazioni del Settings Catalog ma distribuite tramite GPO, utili per organizzazioni non ancora migrate a Intune o in scenari di co-management.

```
Percorso GPO: Computer Configuration → Administrative Templates → 
  Windows Subsystem for Linux

Impostazioni GPO disponibili:
├── Allow Windows Subsystem for Linux
│   └── Equivalente a AllowWSL nel Settings Catalog
├── Allow WSL1
│   └── Disabilitare per forzare solo WSL 2
├── Allow custom kernel configuration
│   └── Blocca kernel=[path] in .wslconfig
├── Allow kernel debugging
│   └── Blocca il debug del kernel WSL
├── Allow nested virtualization
│   └── Controlla se WSL può usare Hyper-V annidato
└── Allow custom system distribution
    └── Controlla distribuzioni di sistema personalizzate

Installazione template ADMX:
1. Scaricare il pacchetto ADMX da Microsoft (GitHub wsl-settings)
2. Copiare i file .admx in %SystemRoot%\PolicyDefinitions\
3. Copiare i file .adml nella cartella lingua appropriata
4. Aggiornare gpmc.msc e verificare che le impostazioni appaiano
```

### Compliance e monitoraggio WSL in ambiente gestito

Oltre alla configurazione, le organizzazioni devono verificare che i dispositivi con WSL rispettino le policy di sicurezza. Intune permette di creare **custom compliance scripts** in PowerShell che verificano lo stato di WSL e riportano la conformità.

```powershell
# Script di compliance Intune per WSL (PowerShell)
# Rileva se WSL è installato, quale versione è in uso,
# e se le impostazioni di sicurezza sono conformi

$compliance = @{}

# Verifica se WSL è installato
$wslInstalled = Get-WindowsOptionalFeature -Online -FeatureName "Microsoft-Windows-Subsystem-Linux"
$compliance["WslInstalled"] = ($wslInstalled.State -eq "Enabled")

# Verifica le distribuzioni installate
$distros = wsl --list --verbose 2>$null
$compliance["HasDistributions"] = ($distros -ne $null -and $distros.Count -gt 1)

# Verifica che tutte le distribuzioni siano WSL 2
$wsl1Distros = $distros | Where-Object { $_ -match "\s+1\s*$" }
$compliance["AllWSL2"] = ($wsl1Distros.Count -eq 0)

# Verifica che il firewall WSL sia abilitato
$wslconfig = "$env:USERPROFILE\.wslconfig"
if (Test-Path $wslconfig) {
    $content = Get-Content $wslconfig -Raw
    $firewallDisabled = $content -match "firewall\s*=\s*false"
    $compliance["FirewallEnabled"] = (-not $firewallDisabled)
    
    # Verifica che il kernel custom non sia configurato
    $customKernel = $content -match "kernel\s*="
    $compliance["NoCustomKernel"] = (-not $customKernel)
} else {
    $compliance["FirewallEnabled"] = $true   # Default è abilitato
    $compliance["NoCustomKernel"] = $true
}

# Output JSON per Intune
$compliance | ConvertTo-Json -Compress

# JSON di detection rules per Intune custom compliance:
# {
#   "Rules": [
#     {
#       "SettingName": "AllWSL2",
#       "Operator": "IsEquals",
#       "DataType": "Boolean",
#       "Operand": true,
#       "MoreInfoUrl": "https://learn.microsoft.com/windows/wsl",
#       "RemediationStrings": [
#         { "Language": "it_IT",
#           "Title": "WSL 1 non conforme",
#           "Description": "Tutte le distribuzioni WSL devono essere WSL 2" }
#       ]
#     }
#   ]
# }
```

### Scenari di rete enterprise — proxy e VPN

In ambienti corporate, la connettività di rete è spesso mediata da proxy e VPN. WSL 2.4+ ha introdotto funzionalità specifiche per questi scenari, ma alcune richiedono configurazione aggiuntiva.

```ini
# .wslconfig — configurazione rete enterprise completa
[wsl2]
networkingMode=mirrored    # WSL condivide le interfacce di rete Windows
dnsTunneling=true          # DNS via canale Hyper-V (bypassare VPN split-tunnel)
firewall=true              # Hyper-V firewall attivo
autoProxy=true             # Eredita proxy PAC/WPAD da Windows

[experimental]
autoMemoryReclaim=gradual  # Recupero memoria dopo inattività
```

```
Matrice compatibilità VPN con WSL 2:

┌──────────────────────┬─────────────┬──────────────────────────┐
│ Scenario             │ Networking  │ Note                     │
├──────────────────────┼─────────────┼──────────────────────────┤
│ VPN GlobalProtect    │ mirrored    │ Funziona con             │
│                      │             │ dnsTunneling=true        │
├──────────────────────┼─────────────┼──────────────────────────┤
│ VPN Cisco AnyConnect │ mirrored    │ Richiede dnsTunneling    │
│                      │             │ e autoProxy              │
├──────────────────────┼─────────────┼──────────────────────────┤
│ VPN Zscaler          │ mirrored    │ Certificato root deve    │
│                      │             │ essere importato in WSL  │
├──────────────────────┼─────────────┼──────────────────────────┤
│ VPN WireGuard        │ mirrored    │ Funziona nativamente     │
├──────────────────────┼─────────────┼──────────────────────────┤
│ Proxy PAC/WPAD       │ mirrored +  │ autoProxy legge la       │
│                      │ autoProxy   │ configurazione Windows   │
├──────────────────────┼─────────────┼──────────────────────────┤
│ Proxy esplicito      │ qualsiasi   │ Settare HTTP_PROXY       │
│ (senza PAC)          │             │ manualmente in .bashrc   │
└──────────────────────┴─────────────┴──────────────────────────┘

Per proxy con certificati custom (es. ispezione TLS corporate):
# Importare il certificato root della CA aziendale in WSL:
sudo cp azienda-root-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Per Node.js (non usa il trust store di sistema):
export NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/azienda-root-ca.crt
```

---

## 17. Integrazione con Windows Terminal

### Configurazione profili WSL

Windows Terminal rileva automaticamente le distribuzioni WSL installate e crea profili per ciascuna. La configurazione avanzata permette personalizzazione completa.

```jsonc
// Settings di Windows Terminal (Ctrl+Shift+, oppure settings.json)
// %LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json

{
    "defaultProfile": "{2c4de342-...}",  // GUID del profilo WSL Ubuntu

    "profiles": {
        "defaults": {
            // Impostazioni applicate a TUTTI i profili
            "font": {
                "face": "JetBrains Mono",
                "size": 12,
                "weight": "normal"
            },
            "opacity": 95,
            "useAcrylic": true,
            "padding": "8, 8, 8, 8",
            "scrollbarState": "hidden",
            "antialiasingMode": "cleartype"
        },
        "list": [
            {
                "name": "Ubuntu",
                "source": "Windows.Terminal.Wsl",
                // "commandline": "wsl.exe -d Ubuntu",   // Implicito
                "startingDirectory": "//wsl.localhost/Ubuntu/home/renan",
                "icon": "🐧",
                "colorScheme": "One Dark",
                "font": {
                    "face": "JetBrains Mono",
                    "size": 12
                },
                "tabTitle": "Ubuntu WSL",
                "bellStyle": "none"
            },
            {
                "name": "Debian (Dev)",
                "source": "Windows.Terminal.Wsl",
                "commandline": "wsl.exe -d Debian",
                "startingDirectory": "//wsl.localhost/Debian/home/renan/projects",
                "colorScheme": "Solarized Dark",
                "suppressApplicationTitle": true,
                "tabTitle": "Debian Dev"
            },
            {
                "name": "Ubuntu (Root)",
                "commandline": "wsl.exe -d Ubuntu -u root",
                "startingDirectory": "//wsl.localhost/Ubuntu/root",
                "colorScheme": "Campbell",
                "tabTitle": "Root Shell",
                "icon": "⚠️"
            }
        ]
    },

    "schemes": [
        {
            "name": "One Dark",
            "background": "#282C34",
            "foreground": "#ABB2BF",
            "cursorColor": "#528BFF",
            "selectionBackground": "#3E4451",
            "black": "#282C34",
            "red": "#E06C75",
            "green": "#98C379",
            "yellow": "#E5C07B",
            "blue": "#61AFEF",
            "purple": "#C678DD",
            "cyan": "#56B6C2",
            "white": "#ABB2BF",
            "brightBlack": "#5C6370",
            "brightRed": "#E06C75",
            "brightGreen": "#98C379",
            "brightYellow": "#E5C07B",
            "brightBlue": "#61AFEF",
            "brightPurple": "#C678DD",
            "brightCyan": "#56B6C2",
            "brightWhite": "#FFFFFF"
        }
    ],

    "actions": [
        { "command": { "action": "splitPane", "split": "horizontal", "profile": "Ubuntu" },
          "keys": "alt+shift+-" },
        { "command": { "action": "splitPane", "split": "vertical", "profile": "Ubuntu" },
          "keys": "alt+shift+=" },
        { "command": "find", "keys": "ctrl+shift+f" },
        { "command": { "action": "newTab", "profile": "Ubuntu" },
          "keys": "ctrl+shift+t" }
    ]
}
```

### Funzionalità avanzate di Windows Terminal

```
Funzionalità utili:
├── Split pane: dividere il terminale in pannelli (Alt+Shift+D)
├── Tab multipli: un tab per ogni distribuzione o sessione
├── Ricerca: Ctrl+Shift+F per cercare nell'output
├── Scroll infinito: scorrere l'output senza limiti
├── Copia/incolla: Ctrl+C/V nativo (o selezione con mouse per copia)
├── Unicode e emoji: supporto completo
├── Ligature nei font: con font come JetBrains Mono, Fira Code
├── Background image: immagine di sfondo personalizzata
├── Quake mode: terminale dropdown con scorciatoia globale
└── Profili automatici: le distribuzioni WSL vengono rilevate automaticamente

# Quake mode (terminale dropdown globale):
# Settings → Actions → Add:
# { "command": { "action": "quakeMode" }, "keys": "win+`" }
# → Premi Win+` per aprire/chiudere il terminale come dropdown

# Avviare Windows Terminal da WSL:
wt.exe -p "Ubuntu"              # Nuova finestra con profilo Ubuntu
wt.exe -w 0 nt -p "Ubuntu"     # Nuovo tab nella finestra corrente
```

### Font raccomandati per il terminale

```
Font con supporto Nerd Fonts (icone per starship, oh-my-zsh, powerline):
├── JetBrains Mono Nerd Font
├── Fira Code Nerd Font
├── Cascadia Code (incluso con Windows Terminal)
├── Hack Nerd Font
└── Source Code Pro Nerd Font

# Installare da:
# https://www.nerdfonts.com/
# Oppure via scoop:
# scoop bucket add nerd-fonts
# scoop install JetBrainsMono-NF
```

---

## 18. Troubleshooting

### Problemi di installazione e avvio

**"WSL non si avvia: Virtual Machine Platform non abilitato"**
```powershell
# Abilitare i componenti necessari:
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
# Riavviare il PC
# Verificare virtualizzazione nel BIOS:
# Task Manager → Performance → CPU → "Virtualization: Enabled"
# Se disabilitato, entrare nel BIOS/UEFI e abilitare Intel VT-x o AMD-V
```

**"WslRegisterDistribution failed with error: 0x80370102"**
```
Causa: Hyper-V o Virtual Machine Platform non abilitato
Soluzione:
1. Aprire "Funzionalità di Windows" (optionalfeatures.exe)
2. Abilitare: Piattaforma macchina virtuale, Sottosistema Windows per Linux
3. Se su Windows 10 Pro/Enterprise: abilitare anche Hyper-V
4. Riavviare
5. Verificare: systeminfo | find "Requisiti Hyper-V"
```

**"WslRegisterDistribution failed with error: 0x80070003"**
```
Causa: path di installazione non valido o disco pieno
Soluzione:
1. Verificare spazio disco: dir %LOCALAPPDATA%\Packages
2. Se disco pieno: spostare la distribuzione su un altro disco
3. Se path corrotto: wsl --unregister <distro> e reinstallare
```

**"WSL 2 requires an update to its kernel component"**
```powershell
# Aggiornare il kernel WSL:
wsl --update
# Se non funziona, scaricare manualmente:
# https://aka.ms/wsl2kernel
# Installare l'MSI e riavviare
```

**"La distribuzione si avvia e si chiude immediatamente"**
```powershell
# Diagnosticare:
wsl -d Ubuntu -- echo "test"
# Se fallisce, controllare i log:
wsl --status
# Provare il reset:
wsl --terminate Ubuntu
wsl --shutdown
# Se persiste: esportare, unregister, reimportare
```

### Problemi di rete

**"Nessuna connessione internet da WSL"**
```bash
# Passo 1: Verificare connettività
ping -c 3 8.8.8.8         # Test connettività IP
ping -c 3 google.com      # Test DNS

# Passo 2: Se IP funziona ma DNS no:
cat /etc/resolv.conf
# Se è vuoto o ha IP non raggiungibile:
sudo rm /etc/resolv.conf
sudo bash -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'
sudo chattr +i /etc/resolv.conf

# Passo 3: Se nulla funziona:
wsl --shutdown    # Da PowerShell
# Riaprire WSL

# Passo 4: Se il problema persiste dopo shutdown:
# In .wslconfig:
# [wsl2]
# networkingMode=mirrored
# dnsTunneling=true
```

**"VPN blocca la connettività WSL"**
```bash
# Problema comune: VPN su Windows interrompe il routing WSL NAT

# Soluzione 1 (raccomandata): Mirrored mode
# In .wslconfig:
# [wsl2]
# networkingMode=mirrored
# dnsTunneling=true
# autoProxy=true

# Soluzione 2: DNS manuale
# Dopo la connessione VPN, l'IP del DNS server può cambiare
# Ottenere il DNS della VPN da PowerShell:
# Get-DnsClientServerAddress | Select InterfaceAlias,ServerAddresses
# Usare quegli IP in /etc/resolv.conf

# Soluzione 3: Route manuale (avanzato)
# Se il routing è il problema, aggiungere route manualmente:
# sudo ip route add <rete-corporate> via $(ip route show default | awk '{print $3}')
```

**"Port forwarding non funziona: servizio WSL non raggiungibile da Windows"**
```bash
# Verifica 1: il servizio è in ascolto?
ss -tlnp | grep <porta>
# Deve mostrare 0.0.0.0:<porta> o ::::<porta>
# Se è su 127.0.0.1:<porta>, il servizio accetta solo connessioni locali
# → Configurare il servizio per ascoltare su 0.0.0.0

# Verifica 2: da Windows, provare localhost
curl http://localhost:<porta>
# Il port forwarding automatico WSL → Windows funziona solo per localhost

# Verifica 3: se serve accesso dalla rete locale:
# Creare port forwarding manuale (vedi sezione Networking)
# E aggiungere regola firewall Windows
```

**"DNS intermittente o lento"**
```ini
# In .wslconfig:
[wsl2]
dnsTunneling=true

[experimental]
bestEffortDnsParsing=true
useWindowsDnsCache=true
```

**"WSL ottiene un IP diverso ad ogni avvio"**
```
In modalità NAT, l'IP di WSL viene assegnato da DHCP virtuale e cambia.
Soluzioni:
1. Usare mirrored mode (stesso IP di Windows)
2. Usare hostname invece di IP
3. Usare localhost per comunicazione Windows ↔ WSL
```

### Problemi di filesystem e I/O

**"I/O lentissimo sui file"**
```bash
# Causa quasi certa: i file sono su /mnt/c/ (filesystem Windows via 9P)
# Verifica:
pwd  # Se inizia con /mnt/c/, /mnt/d/, ecc. → problema 9P

# Soluzione: spostare i file nel filesystem Linux nativo
cp -r /mnt/c/Users/Renan/project/ ~/projects/
cd ~/projects/project
# La differenza di performance è 10-100x

# Se DEVI lavorare su file Windows:
# 1. Usare WSL 1 per quella distribuzione specifica:
#    wsl --set-version <distro> 1
# 2. Oppure copiare avanti e indietro:
#    rsync -av /mnt/c/project/ ~/project-local/
#    # Lavorare su ~/project-local/
#    rsync -av ~/project-local/ /mnt/c/project/
```

**"npm install / yarn install lentissimo"**
```bash
# Sicuramente il progetto è su /mnt/c/
# Spostare su ext4:
mv /mnt/c/Users/Renan/projects/myapp ~/projects/myapp
cd ~/projects/myapp
rm -rf node_modules
npm install    # Ora 5-10x più veloce

# Se DEVI tenere il progetto su Windows (es. condivisione con tool Windows):
# Usare volume mounting con bind mount per node_modules:
# O usare Docker con volume named per node_modules
```

**"Permessi 777 su tutti i file Windows"**
```bash
# Manca l'opzione metadata nel mount
# In /etc/wsl.conf:
# [automount]
# options="metadata,umask=22,fmask=11"

# Riavviare: wsl --terminate <distro>
# Verificare: ls -la /mnt/c/Users/
# Dovrebbe mostrare permessi realistici
```

**"git mostra tutti i file come modificati"**
```bash
# Problema di line endings (CRLF vs LF) o permessi

# Fix line endings:
git config --global core.autocrlf input

# Fix permessi:
git config --global core.fileMode false

# Se il progetto è su /mnt/c/ con metadata:
# Aggiungere al .gitattributes:
# * text=auto eol=lf
```

**"inotify non funziona su file in /mnt/c/"**
```bash
# WSL 2 NON supporta inotify/fswatch sui file del filesystem Windows (9P)
# Questo impatta: hot-reload, file watching, compilazione incrementale

# Soluzioni:
# 1. Spostare il progetto nel filesystem Linux (la soluzione migliore)
# 2. Usare polling invece di inotify:
#    - Webpack: watchOptions: { poll: 1000 }
#    - Nodemon: nodemon --legacy-watch
#    - Chokidar: usePolling: true
# 3. Usare WSL 1 per quel progetto specifico (inotify funziona su /mnt/c/ in WSL 1)
```

**"Disco VHDX cresce senza sosta"**
```powershell
# Il VHDX cresce ma non si riduce automaticamente

# Soluzione 1: Abilitare sparse VHD (automatico)
# In .wslconfig:
# [experimental]
# sparseVhd=true

# Soluzione 2: Compattare manualmente
wsl --shutdown
# PowerShell come Admin:
Optimize-VHD -Path "$env:LOCALAPPDATA\Packages\CanonicalGroupLimited.Ubuntu*\LocalState\ext4.vhdx" -Mode Full

# Soluzione 3: Pulire dentro WSL prima di compattare
sudo apt autoremove -y
sudo apt clean
docker system prune -af  # Se Docker è installato
# Poi wsl --shutdown e Optimize-VHD
```

### Problemi di memoria

**"WSL occupa troppa RAM (vmmem al 90%+)"**
```ini
# In .wslconfig:
[wsl2]
memory=6GB          # Limita la RAM allocata

[experimental]
autoMemoryReclaim=gradual    # Rilascio automatico della RAM inutilizzata
```

```bash
# Rilasciare memoria manualmente (dentro WSL):
echo 1 | sudo tee /proc/sys/vm/drop_caches   # Pulisce page cache
echo 2 | sudo tee /proc/sys/vm/drop_caches   # Pulisce dentries e inodes
echo 3 | sudo tee /proc/sys/vm/drop_caches   # Pulisce tutto

# Rilasciare TUTTA la memoria WSL:
# Da PowerShell:
wsl --shutdown
# La RAM viene rilasciata completamente
```

**"La swap cresce troppo"**
```ini
# In .wslconfig:
[wsl2]
swap=2GB                     # Limita lo swap
swapFile=D:\\WSL\\swap.vhdx  # Sposta su altro disco se necessario
```

### Problemi GPU

**"nvidia-smi non funziona in WSL"**
```bash
# Verifica 1: driver Windows aggiornato?
# Scaricare l'ultimo driver da https://www.nvidia.com/download/index.aspx
# o https://developer.nvidia.com/cuda/wsl

# Verifica 2: /dev/dxg esiste?
ls -la /dev/dxg
# Se non esiste: aggiornare WSL
wsl --update

# Verifica 3: NON hai installato il driver NVIDIA Linux in WSL?
dpkg -l | grep nvidia-driver
# Se sì, RIMUOVERLO:
sudo apt remove --purge nvidia-driver-*
# Il driver deve venire SOLO da Windows

# Verifica 4: Riavviare WSL
wsl --shutdown
```

**"CUDA out of memory in WSL"**
```bash
# La VM WSL ha un limite di memoria (vedi .wslconfig)
# Se il modello ML richiede più VRAM:
# 1. Aumentare memory in .wslconfig
# 2. Usare mixed precision (fp16) per ridurre l'uso VRAM
# 3. Usare gradient checkpointing
# 4. Ridurre batch size

# Verificare VRAM disponibile:
nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv
```

### Problemi di systemd

**"systemctl non funziona: System has not been booted with systemd"**
```bash
# Verificare che systemd sia abilitato:
cat /etc/wsl.conf
# Deve contenere:
# [boot]
# systemd=true

# Dopo la modifica, riavviare:
# wsl --terminate <distro>
# wsl -d <distro>

# Verificare:
ps -p 1 -o comm=
# Deve mostrare "systemd"

# Se ancora non funziona:
# Aggiornare WSL: wsl --update
# systemd richiede WSL versione 0.67.6+
wsl --version
```

**"Servizi systemd non partono al boot WSL"**
```bash
# systemctl enable <servizio> funziona, ma WSL non è un boot tradizionale
# I servizi "enabled" partono quando la distribuzione si avvia

# Se un servizio non parte:
journalctl -u <servizio> -b
# Cercare errori nei log

# Alternativa: usare boot command in wsl.conf:
# [boot]
# command="systemctl start docker ssh"
```

### Problemi di interop

**"Impossibile eseguire comandi Windows da WSL (explorer.exe, code, ecc.)"**
```bash
# Verificare interop:
cat /proc/sys/fs/binfmt_misc/WSLInterop
# Deve esistere ed essere abilitato

# In /etc/wsl.conf:
# [interop]
# enabled=true
# appendWindowsPath=true

# Se il PATH Windows non è nel PATH:
echo $PATH | tr ':' '\n' | grep -i windows
# Se vuoto: appendWindowsPath è false o wsl.conf non è configurato

# Riavviare dopo le modifiche: wsl --terminate <distro>
```

**"Errore: 'command not found' per tool che funziona in PowerShell"**
```bash
# Il tool potrebbe non essere nel PATH Windows o il PATH non è appendato
# Verificare:
which cmd.exe
# Se non trovato: appendWindowsPath=false in wsl.conf

# Verificare il path del tool:
/mnt/c/Windows/System32/cmd.exe /c "where <tool>"
```

### Problemi con Docker

**"Docker daemon non raggiungibile da WSL"**
```bash
# Con Docker Desktop:
# 1. Verificare: Settings → Resources → WSL Integration
#    → La distribuzione deve essere abilitata
# 2. Riavviare Docker Desktop
# 3. Riavviare WSL: wsl --shutdown

# Con Docker Engine nativo in WSL:
sudo systemctl status docker
# Se non attivo:
sudo systemctl start docker
# Se non installato: seguire guida installazione Docker Engine

# Verificare socket:
ls -la /var/run/docker.sock
# Deve esistere e l'utente deve essere nel gruppo docker:
groups | grep docker
# Se no: sudo usermod -aG docker $USER && newgrp docker
```

**"Docker build lento in WSL"**
```bash
# Causa 1: BuildKit non abilitato
export DOCKER_BUILDKIT=1

# Causa 2: Context troppo grande
# Creare .dockerignore:
echo -e "node_modules\n.git\n*.log\nbuild\ndist" > .dockerignore

# Causa 3: File su /mnt/c/
# Spostare il progetto in /home/ per build veloci
```

---

## 19. FAQ

**D1: Posso eseguire WSL 1 e WSL 2 contemporaneamente?**
Si. Ogni distribuzione può essere configurata indipendentemente come WSL 1 o WSL 2. Il comando `wsl --set-version <distro> <1|2>` cambia la versione. Distribuzioni diverse possono coesistere con versioni diverse.

**D2: WSL rallenta Windows?**
In idle, l'impatto è trascurabile. La VM WSL 2 si avvia solo quando si apre una distribuzione e si spegne dopo un timeout di inattività. Il consumo di RAM è la risorsa più impattata; configurare `memory` in `.wslconfig` e `autoMemoryReclaim=gradual` per minimizzare l'impatto.

**D3: Posso usare WSL per produzione?**
WSL non è progettato per carichi di produzione. Per produzione usare Linux nativo, container, o VM dedicate. WSL è ideale per sviluppo, test e prototipazione. Detto questo, nulla impedisce tecnicamente di eseguire servizi in WSL, ma manca di SLA, monitoraggio enterprise e hardening adeguato.

**D4: Come condivido la clipboard tra WSL e Windows?**
La clipboard è condivisa automaticamente per il testo. Da WSL: `echo "test" | clip.exe` per copiare, `powershell.exe -Command Get-Clipboard` per incollare. Con WSLg, la clipboard funziona anche per le app grafiche (Ctrl+C/Ctrl+V bidirezionale).

**D5: WSL supporta i container Windows?**
No. WSL esegue container Linux. I container Windows richiedono Docker Desktop con engine Windows o un host Windows Server. I due tipi di container non possono coesistere nella stessa istanza Docker.

**D6: Come accedo ai file WSL da un'app Windows?**
Digitare `\\wsl$\<distro>\` nella barra degli indirizzi di File Explorer. Oppure usare `\\wsl.localhost\<distro>\` (più affidabile con VPN). Si possono anche mappare come unità di rete: `net use Z: \\wsl$\Ubuntu`.

**D7: Posso usare WSL con Hyper-V VM già esistenti?**
Si. WSL 2 e Hyper-V condividono lo stesso hypervisor. Non ci sono conflitti. Tuttavia, WSL 2 e VMware/VirtualBox possono avere problemi di compatibilità perche' VMware e VirtualBox (versioni meno recenti) non supportano Hyper-V.

**D8: Come faccio a fare un backup completo prima di un aggiornamento Windows?**
```powershell
wsl --shutdown
wsl --list --verbose
# Per ogni distribuzione:
wsl --export Ubuntu C:\Backup\ubuntu-pre-update.tar
wsl --export Debian C:\Backup\debian-pre-update.tar
```

**D9: WSL funziona su Windows Home?**
Si, da Windows 10 versione 2004+. WSL 2 non richiede Hyper-V "completo" (che e' solo su Pro/Enterprise) ma usa la Virtual Machine Platform, disponibile anche su Home.

**D10: Come posso eseguire servizi WSL che partono con Windows?**
Creare un task in Task Scheduler che esegue `wsl -d Ubuntu -- sudo systemctl start <servizio>` al login. Oppure creare uno script PowerShell in `shell:startup` che avvia WSL e i servizi necessari.

**D11: Il mio antivirus interferisce con WSL?**
Si, gli antivirus che scansionano in real-time possono rallentare significativamente le operazioni I/O in WSL. Aggiungere esclusioni per il path dei VHDX e per il processo vmmem. Vedere la sezione Sicurezza per dettagli.

**D12: Come aggiorno il kernel WSL?**
```powershell
wsl --update
# Verifica:
wsl --version
# Il kernel si aggiorna indipendentemente dalla distribuzione
```

**D13: Posso montare dischi fisici (USB, ext4) in WSL?**
```powershell
# Si, da Windows 11 o WSL recente:
wsl --mount \\.\PHYSICALDRIVE2 --partition 1 --type ext4
# Il disco sara' disponibile in /mnt/wsl/PHYSICALDRIVE2p1
# Per smontare:
wsl --unmount \\.\PHYSICALDRIVE2
```

**D14: Come creo un ambiente WSL identico su piu' macchine?**
Esportare la distribuzione configurata (`wsl --export`), distribuire il tarball alle macchine target e importare (`wsl --import`). Oppure usare un Dockerfile per generare un rootfs riproducibile e importarlo.

**D15: WSL supporta IPv6?**
In modalita' NAT, il supporto IPv6 e' limitato. Con mirrored mode (`networkingMode=mirrored`), IPv6 funziona nativamente perche' WSL condivide le interfacce di rete di Windows.

**D16: Come gestisco le line endings (CRLF/LF) tra Windows e WSL?**
Configurare `git config --global core.autocrlf input` in WSL (converte CRLF a LF al commit). Aggiungere un `.gitattributes` al progetto con `* text=auto eol=lf`. Gli editor moderni (VS Code) gestiscono questo automaticamente.

**D17: Posso usare WSL per compilare software per Windows?**
Si, con cross-compilation. Installare il cross-compiler appropriato (es. `mingw-w64` per C/C++) e compilare con il target Windows. Per .NET: installare il .NET SDK Linux e usare `dotnet publish -r win-x64`.

---

## 20. Best Practices per ambiente di sviluppo

### Checklist setup iniziale

```
Workstation WSL — Setup Completo
═══════════════════════════════════════════════════════════════

□ 1. Aggiornare Windows all'ultima versione
□ 2. Abilitare virtualizzazione nel BIOS
□ 3. wsl --install -d Ubuntu-24.04
□ 4. wsl --set-default-version 2
□ 5. Configurare .wslconfig:
     - memory: 50% della RAM (max 16 GB per sviluppo generico)
     - processors: 50-75% dei core
     - networkingMode: mirrored
     - autoMemoryReclaim: gradual
     - sparseVhd: true
□ 6. Configurare /etc/wsl.conf:
     - systemd: true
     - metadata negli automount options
     - hostname personalizzato
□ 7. Installare Windows Terminal + font Nerd Font
□ 8. Installare VS Code + estensione WSL
□ 9. Configurare git (user, email, autocrlf, chiavi SSH)
□ 10. Installare tool di sviluppo (nvm, pyenv, Go, Rust, ecc.)
□ 11. Configurare Docker (Desktop o Engine nativo)
□ 12. Primo backup: wsl --export
□ 13. Verificare: networking, DNS, GPU (se necessario)
```

### Regole fondamentali

```
1. FILE NEL FILESYSTEM CORRETTO
   ├── Progetti Linux/Docker → /home/user/projects/ (ext4)
   ├── Progetti Windows → C:\Users\...\projects\ (NTFS)
   └── Mai lavorare su /mnt/c/ per progetti con molti file

2. WSL 2 SEMPRE (tranne eccezioni rare)
   ├── Docker, systemd, GPU richiedono WSL 2
   ├── WSL 1 solo per interop filesystem Windows specifico
   └── inotify su /mnt/c/ e' l'unico caso forte per WSL 1

3. LIMITARE LE RISORSE
   ├── .wslconfig con limiti RAM e CPU
   ├── autoMemoryReclaim per evitare sprechi
   └── wsl --shutdown quando non si usa WSL

4. BACKUP REGOLARI
   ├── wsl --export settimanale
   ├── Prima di aggiornamenti Windows importanti
   └── Prima di operazioni distruttive sulla distribuzione

5. VS CODE REMOTE - WSL
   ├── Sempre usare l'estensione WSL per sviluppo
   ├── Le extensions eseguono nel contesto Linux
   ├── Performance I/O native su ext4
   └── Debugging e terminal nel contesto Linux

6. NETWORKING MIRRORED (Windows 11)
   ├── Elimina problemi NAT e port forwarding
   ├── VPN funziona automaticamente
   └── IPv6 nativo

7. GIT: CORE.AUTOCRLF=INPUT
   ├── Previene problemi CRLF/LF
   ├── Usare .gitattributes nel progetto
   └── Chiavi SSH separate o condivise (con permessi corretti)

8. DOCKER: FILESYSTEM LINUX
   ├── Progetti Docker in /home/, mai in /mnt/c/
   ├── Volume mount da ext4 per performance
   └── Docker Desktop o Engine nativo — scegliere uno

9. SICUREZZA
   ├── Non esporre servizi WSL alla rete senza firewall
   ├── VHDX e' leggibile da Windows — proteggere i segreti
   ├── Aggiornamenti di sicurezza regolari
   └── Limitare interop se non necessario

10. SHELL E TERMINALE
    ├── Windows Terminal con profili per ogni distribuzione
    ├── Zsh + starship (opzionale ma produttivo)
    ├── Font Nerd Font per icone e ligature
    └── tmux per sessioni persistenti
```

### Template .wslconfig raccomandato

```ini
# %USERPROFILE%\.wslconfig — Template raccomandato per sviluppatori

[wsl2]
# Risorse — adattare alla propria macchina
memory=8GB
processors=4
swap=4GB

# Networking — mirrored elimina la maggior parte dei problemi
networkingMode=mirrored
dnsTunneling=true
autoProxy=true
firewall=true

# Virtualization
nestedVirtualization=false    # true solo se serve KVM/Android emulator

[experimental]
autoMemoryReclaim=gradual
sparseVhd=true
bestEffortDnsParsing=true
useWindowsDnsCache=true
```

### Template wsl.conf raccomandato

```ini
# /etc/wsl.conf — Template raccomandato per sviluppatori

[boot]
systemd=true

[automount]
enabled=true
root=/mnt/
options="metadata,umask=22,fmask=11"

[network]
generateHosts=true
generateResolvConf=true
hostname=dev-wsl

[interop]
enabled=true
appendWindowsPath=true

[user]
default=renan
```

### Struttura directory consigliata

```bash
# Organizzazione del filesystem di sviluppo in WSL

~/
├── projects/                 # Tutti i progetti di sviluppo
│   ├── personal/             # Progetti personali
│   ├── work/                 # Progetti lavorativi
│   └── oss/                  # Open source contributions
├── scripts/                  # Script di automazione personali
├── tools/                    # Tool custom compilati
├── .ssh/                     # Chiavi SSH (permessi 600/700)
├── .config/                  # Configurazione app XDG
└── backups/                  # Backup temporanei prima di operazioni distruttive

# Non usare MAI:
# /mnt/c/Users/.../projects/  ← Troppo lento per sviluppo
# /tmp/ per file importanti   ← Si perde al reboot
```

---

## Riferimenti e risorse

| Risorsa | URL |
|---------|-----|
| Documentazione ufficiale WSL | https://learn.microsoft.com/windows/wsl/ |
| Kernel WSL (sorgente) | https://github.com/microsoft/WSL2-Linux-Kernel |
| WSLg (sorgente) | https://github.com/microsoft/wslg |
| Release notes WSL | https://learn.microsoft.com/windows/wsl/release-notes |
| Best practices Microsoft | https://learn.microsoft.com/windows/wsl/setup/environment |
| CUDA on WSL | https://developer.nvidia.com/cuda/wsl |
| Docker Desktop WSL 2 | https://docs.docker.com/desktop/wsl/ |
| Windows Terminal docs | https://learn.microsoft.com/windows/terminal/ |

---

## Esercizi

### Esercizio 1 — Concettuale: WSL 1 vs WSL 2

Descrivi le differenze architetturali tra WSL 1 (translation layer) e WSL 2 (lightweight VM Hyper-V). Spiega perché WSL 2 offre compatibilità syscall completa ma introduce complessità di rete. Quando è preferibile WSL 1?

### Esercizio 2 — Lab: Custom Distro e networking mirrored

1. Scaricare un rootfs minimale (es. Alpine Linux).
2. Importarlo con `wsl --import MyDistro <path> <rootfs.tar.gz>`.
3. Abilitare `networkingMode=mirrored` in `.wslconfig`.
4. Avviare un web server sulla porta 8080 nella distro e verificare l'accesso da Windows senza port forwarding.
5. Esportare la distro configurata con `wsl --export`.

### Esercizio 3 — Scenario: Performance filesystem cross-OS

Un team di sviluppo lamenta lentezza estrema nel build di un progetto Node.js in WSL 2. Il progetto è su `/mnt/c/Users/dev/projects/`. Identifica la causa root, proponi la soluzione (spostamento in ext4), e scrivi uno script che automatizzi la migrazione preservando i permessi git.

### Esercizio 4 — Design: Ambiente di sviluppo enterprise con WSL 2

Progetta un ambiente di sviluppo standardizzato per 50 sviluppatori basato su WSL 2. Considera: distribuzione custom pre-configurata via `wsl --import`, `.wslconfig` gestito da GPO, Docker Desktop con WSL 2 backend, GPU passthrough per il team ML, e strategia di backup dei dati nel filesystem ext4.

---

## Auto-valutazione

<details>
<summary>1. Qual è la differenza fondamentale tra il kernel WSL 1 e WSL 2?</summary>

WSL 1 traduce le chiamate di sistema Linux in chiamate Windows NT (translation layer) — non esegue un kernel Linux reale. WSL 2 esegue un kernel Linux completo all'interno di una lightweight VM Hyper-V, garantendo compatibilità syscall al 100% ma introducendo un layer di rete virtualizzato.
</details>

<details>
<summary>2. Perché i progetti nel filesystem NTFS (/mnt/c/) sono lenti in WSL 2?</summary>

Ogni accesso a file attraversa il confine VM → host via il protocollo 9P (Plan 9 Filesystem Protocol). Le operazioni I/O intensive (come `npm install` o `git status` su migliaia di file) subiscono la latenza di questa traduzione. La soluzione è mantenere i file di progetto nel filesystem ext4 nativo di WSL 2 (~/).
</details>

<details>
<summary>3. Cosa fa networkingMode=mirrored e quale problema risolve?</summary>

In modalità default (NAT), la distro WSL 2 ha un indirizzo IP diverso dall'host Windows, richiedendo port forwarding esplicito. La modalità `mirrored` condivide lo stack di rete dell'host: la distro usa lo stesso IP di Windows, eliminando la complessità NAT e permettendo l'accesso diretto ai servizi senza forwarding.
</details>

<details>
<summary>4. Come si abilita systemd in una distribuzione WSL 2?</summary>

Aggiungere `[boot] systemd=true` nel file `/etc/wsl.conf` all'interno della distribuzione, poi riavviare con `wsl --shutdown`. Richiede WSL versione 0.67.6+ e Windows 11 22H2+. Con systemd attivo si possono usare `systemctl`, servizi, timer e snap.
</details>

<details>
<summary>5. Qual è la differenza tra .wslconfig e wsl.conf?</summary>

`.wslconfig` si trova su Windows (`%USERPROFILE%\.wslconfig`) e configura opzioni globali per tutte le distribuzioni WSL 2 (memoria, CPU, swap, networking mode, kernel custom). `wsl.conf` si trova dentro ogni distribuzione (`/etc/wsl.conf`) e configura opzioni specifiche per quella distro (automount, network hostname, systemd, interop).
</details>

<details>
<summary>6. Come si configura il GPU passthrough per CUDA in WSL 2?</summary>

Requisiti: driver NVIDIA per Windows con supporto WSL (non installare driver Linux dentro WSL). Installare il CUDA Toolkit dentro la distro WSL. Il driver Windows espone `/dev/dxg` nella VM WSL 2 tramite il modulo kernel `dxgkrnl`. Verificare con `nvidia-smi` dentro WSL.
</details>

<details>
<summary>7. Qual è il vantaggio di Docker Desktop con WSL 2 backend rispetto a Hyper-V backend?</summary>

Con il backend WSL 2, i container Linux girano direttamente nel kernel Linux della VM WSL 2, senza una VM Docker separata. Vantaggi: startup più rapido, consumo di memoria inferiore (condiviso con WSL), accesso diretto ai file della distro, e possibilità di usare `docker` CLI sia da Windows che da dentro la distro.
</details>

---

## Letture primarie consigliate

- Microsoft Learn — WSL Documentation. https://learn.microsoft.com/windows/wsl/ (consultato: 2026-05-23)
- Microsoft Learn — WSL Networking. https://learn.microsoft.com/windows/wsl/networking (consultato: 2026-05-23)
- Microsoft Learn — GPU in WSL. https://learn.microsoft.com/windows/wsl/tutorials/gpu-compute (consultato: 2026-05-23)
- Docker Docs — Docker Desktop WSL 2 Backend. https://docs.docker.com/desktop/wsl/ (consultato: 2026-05-23)
- Microsoft DevBlogs — WSLg Architecture. https://devblogs.microsoft.com/commandline/wslg-architecture/ (consultato: 2026-05-23)

---

## Collegamenti incrociati

| Modulo | Relazione con questo capitolo |
|---|---|
| [06-rete-windows.md](06-rete-windows.md) | Networking Windows — prerequisito per comprendere NAT/mirrored mode in WSL 2 |
| [23-hyper-v-guida-completa.md](23-hyper-v-guida-completa.md) | Hyper-V — la tecnologia di virtualizzazione su cui WSL 2 si basa |
| [14-batch-scripting.md](14-batch-scripting.md) | Scripting — interop tra comandi Windows e Linux via WSL |
| [02-powershell.md](02-powershell.md) | PowerShell — gestione WSL via cmdlet e automazione |
| [19-troubleshooting.md](19-troubleshooting.md) | Troubleshooting — diagnosi problemi di rete, performance e compatibilità WSL |

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **WSL 2** | Windows Subsystem for Linux versione 2. Esegue un kernel Linux completo in una lightweight VM Hyper-V con compatibilità syscall al 100%. |
| **9P (Plan 9 Protocol)** | Protocollo di rete usato internamente da WSL 2 per montare il filesystem Windows (NTFS) dentro la distro Linux come `/mnt/c/`. Fonte della latenza I/O cross-filesystem. |
| **WSLg** | WSL Graphics. Componente che abilita l'esecuzione di applicazioni grafiche Linux (GUI) su Windows tramite Wayland/X11 proxy e RDP interno. |
| **Mirrored mode** | Modalità di networking WSL 2 che condivide lo stack di rete dell'host Windows, eliminando il NAT e assegnando lo stesso IP alla distro. |
| **systemd** | Init system e service manager standard di Linux, supportato in WSL 2 dal 2022. Abilita `systemctl`, timer, snap e servizi standard. |
| **.wslconfig** | File di configurazione globale WSL 2, posizionato in `%USERPROFILE%`, che controlla memoria, CPU, swap, rete e kernel custom per tutte le distro. |
| **wsl.conf** | File di configurazione per-distro, posizionato in `/etc/wsl.conf`, che controlla automount, hostname, interop e boot (systemd). |
| **VHDX** | Virtual Hard Disk Extended. Formato del disco virtuale usato da WSL 2 per il filesystem ext4 di ogni distribuzione. Cresce dinamicamente. |
| **dxgkrnl** | Modulo kernel Linux in WSL 2 che espone l'interfaccia DirectX del GPU Windows, permettendo CUDA e DirectML senza driver Linux nativi. |
| **interop** | Funzionalità WSL che permette di eseguire binari Windows da dentro Linux (es. `explorer.exe .`) e viceversa (`wsl ls`). |
