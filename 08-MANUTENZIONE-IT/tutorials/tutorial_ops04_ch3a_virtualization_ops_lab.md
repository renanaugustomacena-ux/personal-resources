# Tutorial: Virtualizzazione — Gestione Operativa delle VM — Hands-On Lab

> **Documento di riferimento:** `04-servizi-infrastruttura.md` (sezione Manutenzione Virtualizzazione)
> **Dominio:** Infrastruttura — Compute Layer
> **Ambito:** Concetti hypervisor, ciclo di vita VM, snapshot management, monitoraggio risorse VirtualBox, right-sizing, confronto piattaforme enterprise (VMware/Hyper-V/Proxmox)
> **Durata lab:** 3-4 ore
> **Livello:** Intermedio — richiede ops03a (Windows Server), ops03b (Linux)
> **Prerequisiti:** VirtualBox installato sul tuo host con le 3 VM del lab in esecuzione
> **Ambiente lab:** Lavoriamo dalla macchina host VirtualBox — gestiamo le VM del lab dall'esterno
> **Nota:** In produzione utilizzeresti VMware vSphere, Hyper-V o Proxmox. Il nostro lab usa VirtualBox (hypervisor tipo 2 — ideale per apprendimento, stessi concetti).

---

## Lab Environment Setup

```bash
# Sul tuo host (Windows/Linux/Mac) — dove gira VirtualBox

# Verifica che VBoxManage sia accessibile (CLI di VirtualBox)
VBoxManage --version
# Output atteso: 7.x.x (o versione installata)

# Lista tutte le VM registrate in VirtualBox
VBoxManage list vms
# Dovresti vedere DC-LAB-01, SRV-LINUX-01, WKS-LAB-01

# Lista VM in esecuzione
VBoxManage list runningvms
```

---

## PART A: FONDAMENTI — Perché la Virtualizzazione Ha Cambiato l'IT

> Prima della virtualizzazione (anni '90), ogni applicazione girava su un server fisico dedicato. Un'azienda con 20 applicazioni aveva 20 server fisici, ognuno dei quali usava in media il 10-15% delle risorse. Stavano lì a consumare energia, spazio e denaro per il 90% del tempo. La virtualizzazione ha permesso di mettere 20 "server virtuali" su 2 server fisici, moltiplicando l'utilizzo delle risorse. Oggi oltre l'80% dei workload aziendali gira su infrastruttura virtuale.

---

### Concetto A1: L'Hypervisor — Il Direttore d'Orchestra

> **Analogia.** Un hypervisor è come un condominio di lusso. Il palazzo fisico (il server) ha muri, fondamenta, impianti elettrici e idraulici (CPU, RAM, disco, rete). L'hypervisor è l'amministratore del condominio: divide il palazzo in appartamenti (VM), assegna risorse a ciascuno (quante stanze, quanta corrente), e si assicura che i condòmini non si disturbino a vicenda. Ogni condòmino (VM) vede "il suo appartamento" come se fosse una casa intera — non sa degli altri.

**Tipo 1 vs Tipo 2 Hypervisor:**

```
TYPE 1 — Bare Metal (Enterprise)
  ┌──────────────────────────────┐
  │    VM1    │    VM2    │ VM3  │  ← Virtual Machines
  ├───────────────────────────────┤
  │         HYPERVISOR           │  ← Gira DIRETTAMENTE sull'hardware
  │    (ESXi / Hyper-V / KVM)   │     Nessun OS host
  ├───────────────────────────────┤
  │    CPU / RAM / DISCO / RETE  │  ← Hardware fisico
  └──────────────────────────────┘
  
  Pro: performance massime, nessun overhead OS host
  Uso: datacenter, produzione, cloud
  Esempi: VMware ESXi, Microsoft Hyper-V, Proxmox VE (KVM)

TYPE 2 — Hosted (Desktop/Lab)
  ┌──────────────────────────────┐
  │    VM1    │    VM2    │ VM3  │  ← Virtual Machines
  ├───────────────────────────────┤
  │         HYPERVISOR           │  ← Gira come APP sull'OS host
  │  (VirtualBox / VMware WS)   │
  ├───────────────────────────────┤
  │     WINDOWS / macOS / Linux  │  ← OS HOST
  ├───────────────────────────────┤
  │    CPU / RAM / DISCO / RETE  │  ← Hardware fisico
  └──────────────────────────────┘
  
  Pro: facile da installare, ideale per sviluppo e lab
  Contro: overhead dell'OS host, performance inferiori
  Uso: lab, sviluppo, test, formazione
  Esempi: VirtualBox, VMware Workstation
```

---

### Concetto A2: Risorse Virtuali — vCPU, vRAM, vDisk

> **Analogia.** Quando un hypervisor assegna 4 vCPU a una VM, è come dare a un cameriere 4 "voucher" da presentare alla cucina (CPU fisica). Il cameriere può avere 4 voucher, ma se la cucina ha solo 2 cuochi (core fisici) e ci sono 10 camerieri, ognuno dovrà aspettare. Il CPU "steal time" (tempo rubato) è l'attesa del cameriere per avere un cuoco disponibile.

**CPU (vCPU):**

```
Host fisico: 8 core fisici
  VM1: 4 vCPU
  VM2: 4 vCPU
  VM3: 2 vCPU
  VM4: 2 vCPU
  Totale allocato: 12 vCPU > 8 core fisici

Overcommit CPU: rapporto 12:8 = 1.5:1
  Funziona perché raramente tutte le VM usano il 100% CPU simultaneamente
  Ma con carico elevato simultaneo → CPU Ready alto (VM "aspetta" il core)
  
CPU Ready < 5%: normale
CPU Ready 5-10%: monitorare
CPU Ready > 10%: performance degradate — riduci overcommit o aggiungi host

Anti-pattern: assegnare 8 vCPU a una VM che ne usa 2%
  → Spreca risorse, aumenta il NUMA overhead
  → Regola: assegna vCPU in base all'utilizzo reale (right-sizing)
```

**RAM (vRAM):**

```
Host fisico: 32 GB RAM
  VM1: 8 GB
  VM2: 8 GB
  VM3: 4 GB
  VM4: 4 GB
  VM5: 4 GB
  Totale allocato: 28 GB < 32 GB (sottoscrittura → OK)

Overcommit RAM: diverso dall'overcommit CPU
  Se totale allocato > RAM fisica → l'hypervisor usa balloon driver,
  memory swapping, transparent page sharing
  → Questi meccanismi degradano SEVERAMENTE le performance!
  
Differenza pratica:
  vRAM allocata: 8 GB (quanto la VM pensa di avere)
  vRAM attiva:   3 GB (quanto la VM usa effettivamente)
  Il balloon driver può "sgonfiare" la RAM non usata

Soglie sicure:
  Overcommit < 1.2:1 → sicuro per carichi standard
  Overcommit > 1.5:1 → rischio swap → performance IO degrades
  Overcommit > 2:1   → NO per produzione
```

**Storage (vDisk):**

```
VHD/VMDK/QCOW2 — i formati del disco virtuale:
  Fixed (preallocato): disco da 50 GB occupa subito 50 GB sul disco host
    PRO: performance migliori, nessun overhead crescita
    CONTRO: usa spazio anche se la VM ha solo 10 GB di dati
    
  Dynamic/Thin (crescita dinamica): disco da 50 GB parte da ~1 GB
    PRO: risparmio spazio iniziale
    CONTRO: prestazioni leggermente inferiori durante la crescita
    RISCHIO: se si esaurisce lo spazio host → CORRUZIONE del disco virtuale!
    
Nel nostro lab (VirtualBox):
  Formato: VMDK (compatibile VMware) o VDI (nativo VirtualBox)
  Tipo: Dynamic — i dischi crescono all'occorrenza
  
Dove stanno i file disco:
  Default Windows: C:\Users\{user}\VirtualBox VMs\{vmname}\
  Default Linux:   ~/VirtualBox VMs/{vmname}/
```

---

### Concetto A3: Snapshots — Salvagente o Trappola?

> **Analogia.** Uno snapshot è come una fotografia di tutte le carte sulla tua scrivania in un momento preciso. Se rompi qualcosa lavorando, puoi rimettere le carte esattamente dove erano guardando la foto. Però se hai 50 foto che si accumulano, la scrivania è sempre più ingombra (overhead), e se distruggi la scrivania fisica (disco), tutte le foto si perdono con essa.

**Come funziona uno snapshot:**

```
Stato iniziale:
  disco_vm.vmdk (o .vdi) — 20 GB
  
Dopo CREATE SNAPSHOT "pre-update":
  disco_vm.vmdk    → congelato, solo lettura
  disco_vm-delta1.vmdk → nuovo, solo scritture recenti
  
Dopo 7 giorni di uso:
  disco_vm.vmdk         — 20 GB (base)
  disco_vm-delta1.vmdk  — 8 GB (7 giorni di modifiche)
  
Se faccio rollback: elimino delta1, ritorno allo stato base
Se elimino snapshot: merge di delta1 nel base (operazione lenta!)
```

**Anti-pattern degli snapshot — l'errore più comune:**

```
❌ "Uso gli snapshot come backup"
   Problema: snapshot e dati sono sullo STESSO disco fisico
   Se il disco si guasta → snapshot E dati ENTRAMBI persi
   
❌ "Lascio gli snapshot attivi a lungo"
   Problema 1: accumulo spazio (ogni snapshot = delta che cresce)
   Problema 2: performance degradate (ogni I/O deve attraversare più layer)
   Problema 3: eliminazione/merge lenta e rischiosa
   Regola: snapshot > 7 giorni → problema. Mai > 30 giorni in produzione

❌ "Faccio snapshot di database senza quiesce"
   Problema: il database potrebbe essere nel mezzo di una scrittura
   Lo snapshot cattura un disco inconsistente → ripristino fallirà
   Soluzione: snapshot con quiesce (VM Tools) o flush del filesystem
   
✅ Uso corretto degli snapshot:
   - Prima di un aggiornamento OS/applicazione (rimuovi dopo 48h)
   - Per test di patch (rollback entro 24h se test fallisce)
   - Mai come sostituto del backup
```

---

### Concetto A4: Alta Disponibilità — VM Failure Senza Down Time

> **Analogia.** Imagine di avere un negozio con due cassieri. Se uno si ammala, l'altro continua a servire i clienti. HA per le VM funziona allo stesso modo: le VM girano su più host fisici in un cluster, e se un host si guasta, le VM ripartono automaticamente su un altro host del cluster.

**Meccanismi HA:**

```
VMWARE HA (High Availability):
  - Cluster di 2+ host ESXi
  - vCenter monitora lo stato degli host (heartbeat)
  - Se un host va offline → VM ripartono su altri host in 2-5 min
  - Configura: HA Admission Control (riserva risorse per failover)
  
HYPER-V FAILOVER CLUSTER:
  - Windows Server Failover Clustering + Hyper-V
  - Live Migration: sposta VM senza downtime (durante manutenzione)
  - Quick Migration: pausa VM, migra, riparte (down di secondi)
  
PROXMOX HA:
  - Basato su Corosync (quorum) + Pacemaker (resource manager)
  - ha-manager gestisce il failover automatico
  - Richiede storage condiviso (Ceph) o replicazione
  
KPI importanti:
  RTO (Recovery Time Objective): quanto tempo per tornare online
    Senza HA: 30-60 min (riavvio manuale su nuovo hardware)
    Con HA: 2-5 min (failover automatico)
  RPO (Recovery Point Objective): quanti dati si perdono
    Senza replica: tutto dall'ultimo backup
    Con replica: dipende dalla frequenza di replica (es. 15 min)
```

---

### Concetto A5: Right-Sizing — Ottimizzare le Risorse VM

> **Perché mi interessa?** In un'infrastruttura non ottimizzata, il 40-60% delle VM è sovradimensionata: hanno 8 vCPU ma ne usano 1, 16 GB di RAM ma ne usano 4. Queste risorse "sprecate" impediscono di avviare altre VM, aumentano i costi cloud, e aumentano il NUMA overhead. Il right-sizing periodico è fondamentale per la salute dell'infrastruttura.

```
PROCESSO DI RIGHT-SIZING:

1. Raccolta dati (2-4 settimane di baseline):
   - CPU: utilizzo medio, picco, percentile 95°
   - RAM: utilizzo attivo (non allocato)
   - Disco: IOPS, throughput, utilizzo spazio
   
2. Analisi:
   - CPU avg < 20% e peak < 40% → sovradimensionata (candida riduzione)
   - RAM active < 40% dell'allocato → sovradimensionata
   
3. Azione (sempre in finestra di manutenzione):
   - Riduci vCPU: spegni VM → cambia config → riavvia
   - Riduci RAM: Hot-add memoria (solo alcune piattaforme)
   
4. Verifica post-modifica:
   - Monitor per 48h: performance invariata? → right-sizing riuscito
   - Degrado? → ripristina configurazione precedente (rollback)

REGOLA EMPIRICA:
   vCPU: assegna al 95° percentile dell'uso + 20% buffer
   RAM:  assegna al picco di consumo attivo + 25% buffer
```

---

### Concetto A6: VirtualBox nel Contesto Enterprise

> Il nostro lab usa VirtualBox perché è gratuito, multipiattaforma, e perfetto per la formazione. In produzione, le aziende usano hypervisor Tipo 1 per performance e funzionalità enterprise. Comprendere i concetti su VirtualBox li rende trasferibili a VMware, Hyper-V e Proxmox.

| Caratteristica | VirtualBox (Lab) | VMware vSphere | Hyper-V | Proxmox VE |
|---|---|---|---|---|
| Tipo hypervisor | Tipo 2 (hosted) | Tipo 1 (bare metal) | Tipo 1 | Tipo 1 (KVM+LXC) |
| Costo | Gratuito | ~€45.000/anno/10 host | Incluso in WS2022 | ~€1.000/anno supporto |
| Live Migration | No | vMotion | Live Migration | Yes |
| HA automatica | No | vSphere HA | Failover Cluster | Proxmox HA |
| Snapshot | Sì | Sì (+ quiesce) | Checkpoint | Sì |
| CLI | VBoxManage | esxcli / PowerCLI | PowerShell | pvecm / qm / pct |
| Uso | Lab/dev | Enterprise premium | Ambienti MS | Enterprise OS |

**Trasferibilità dei concetti:**

```
VBoxManage list vms         ≈ qm list (Proxmox) ≈ Get-VM (Hyper-V) ≈ esxcli vm list (VMware)
VBoxManage snapshot take    ≈ qm snapshot (Proxmox) ≈ Checkpoint-VM (Hyper-V)
VBoxManage metrics query    ≈ pvesh get /nodes/pve/status ≈ Get-VMResourceMetering
VBoxManage showvminfo       ≈ qm config (Proxmox) ≈ Get-VMFirmware (Hyper-V)
```

---
---

## PART B: OPERAZIONI — Gestire VM con VirtualBox e Principi Enterprise

> **Obiettivo generale.** Alla fine di questa sezione sarai in grado di: gestire il ciclo di vita delle VM tramite VirtualBox CLI (VBoxManage), creare e gestire snapshot, monitorare l'utilizzo delle risorse, eseguire operazioni di manutenzione (cloning, export), riconoscere le configurazioni errate più comuni (snapshot accumulati, overcommit eccessivo). Tutto applicabile ai principi di VMware, Hyper-V e Proxmox.

> **Nota esecuzione:** Tutti i comandi `VBoxManage` vanno eseguiti sull'**host** (il tuo PC dove gira VirtualBox), non dentro le VM. Su Windows usa PowerShell o cmd; su Linux/Mac usa il terminale. Il percorso di VBoxManage potrebbe essere `"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"` su Windows — aggiungi al PATH se non funziona direttamente.

---

### Esercizio B1: Inventario e Stato delle VM

**Obiettivo.** Ottenere una visione completa delle VM registrate nel tuo VirtualBox: stato, configurazione risorse, network.

**Background.** In un ambiente enterprise con 500+ VM, l'inventario automatico è fondamentale per il capacity planning. Con VirtualBox in locale, questa è la versione ridotta dello stesso processo che si farebbe con VMware PowerCLI o Proxmox `qm list`.

**Step 1 — Lista tutte le VM con stato.**

```bash
# Sul tuo HOST (dove gira VirtualBox)

# Lista tutte le VM (nome e UUID)
VBoxManage list vms

# Lista solo le VM in esecuzione
VBoxManage list runningvms

# Output atteso:
# "DC-LAB-01"   {a1b2c3d4-...}
# "SRV-LINUX-01" {e5f6g7h8-...}
# "WKS-LAB-01"  {i9j0k1l2-...}
```

**Step 2 — Dettaglio configurazione di ogni VM.**

```bash
# Informazioni complete su DC-LAB-01
VBoxManage showvminfo "DC-LAB-01"

# Filtra le informazioni più rilevanti
VBoxManage showvminfo "DC-LAB-01" | grep -E "Memory|CPUs|State|VRAM|Display|Storage|NIC|UUID"
```

**Output atteso e interpretazione:**

```
Name:                        DC-LAB-01
UUID:                        a1b2c3d4-...
Memory size:                 4096MB        ← vRAM allocata
CPUs:                        2             ← vCPU allocate
State:                       running       ← oppure: poweroff, saved, paused
VRAM size:                   16MB          ← memoria video
Storage Controller Name:     SATA
  Port 0: /path/to/DC-LAB-01.vmdk (UUID: ...)
NIC 1:   Host-only Adapter, 'VirtualBox Host-Only Ethernet Adapter'
NIC 2:   NAT
```

**Step 3 — Script inventario completo (tutte le VM).**

```bash
# Inventario di tutte le VM in formato tabulare
for vm in $(VBoxManage list vms | awk -F'"' '{print $2}'); do
    state=$(VBoxManage showvminfo "$vm" --machinereadable 2>/dev/null | grep "^VMState=" | cut -d'"' -f2)
    mem=$(VBoxManage showvminfo "$vm" --machinereadable 2>/dev/null | grep "^memory=" | cut -d'=' -f2)
    cpu=$(VBoxManage showvminfo "$vm" --machinereadable 2>/dev/null | grep "^cpus=" | cut -d'=' -f2)
    printf "%-20s | State: %-10s | vCPU: %-3s | vRAM: %s MB\n" "$vm" "$state" "$cpu" "$mem"
done
```

**Output atteso:**

```
DC-LAB-01            | State: running     | vCPU: 2   | vRAM: 4096 MB
SRV-LINUX-01         | State: running     | vCPU: 2   | vRAM: 2048 MB
WKS-LAB-01           | State: running     | vCPU: 2   | vRAM: 2048 MB
```

**Step 4 — Informazioni disco virtuale.**

```bash
# Tutti i dischi VirtualBox registrati
VBoxManage list hdds

# Dettaglio di un disco specifico (cerca il file vmdk/vdi di DC-LAB-01)
DISK_PATH=$(VBoxManage showvminfo "DC-LAB-01" --machinereadable 2>/dev/null | \
    grep "IDE\|SATA\|SCSI" | grep "vmdk\|vdi" | head -1 | cut -d'"' -f2)
echo "Disco trovato: $DISK_PATH"

if [ -n "$DISK_PATH" ]; then
    VBoxManage showhdinfo "$DISK_PATH"
fi
```

**Output atteso e cosa cercare:**

```
UUID:           ...
Accessible:     yes         ← deve essere "yes"
Logical size:   51200 MB    ← 50 GB (capacità logica della VM)
Current size on disk: 12384 MB  ← 12 GB (spazio fisico realmente occupato)
Type:           Normal (base)   ← se fosse "differencing" → snapshot attivo!
Format:         VDI
```

**Checkpoint B1:**
- [ ] `VBoxManage list vms` mostra le 3 VM del lab
- [ ] `VBoxManage showvminfo` mostra configurazione RAM, CPU, disco
- [ ] Script inventario eseguito con output tabulare
- [ ] Differenza tra "Logical size" e "Current size on disk" compresa

---

### Esercizio B2: Monitoraggio Risorse VM in Tempo Reale

**Obiettivo.** Monitorare l'utilizzo di CPU, RAM e I/O delle VM tramite VBoxManage metrics, e confrontare con i dati visti dall'interno delle VM.

**Background.** In VMware vSphere, useresti `esxtop` o le metriche di vCenter. In Hyper-V, `Get-VMResourceMetering`. In VirtualBox, `VBoxManage metrics`. La prospettiva dall'hypervisor è diversa da quella della VM: l'hypervisor vede il consumo reale, la VM vede le risorse allocate.

**Step 1 — Abilita la raccolta metriche VirtualBox.**

```bash
# Le metriche devono essere abilitate esplicitamente (richiede VM in esecuzione)
VBoxManage metrics setup --period 1 --samples 10 "DC-LAB-01"
VBoxManage metrics setup --period 1 --samples 10 "SRV-LINUX-01"

# Lista le metriche disponibili per una VM
VBoxManage metrics list "DC-LAB-01"
```

**Step 2 — Campiona CPU e RAM.**

```bash
# Campiona le metriche di CPU e RAM (aspetta qualche secondo per raccogliere dati)
echo "=== METRICHE DC-LAB-01 ==="
VBoxManage metrics query "DC-LAB-01" CPU/Load/User CPU/Load/Kernel RAM/Usage/Total RAM/Usage/Used 2>/dev/null

echo ""
echo "=== METRICHE SRV-LINUX-01 ==="
VBoxManage metrics query "SRV-LINUX-01" CPU/Load/User CPU/Load/Kernel RAM/Usage/Total RAM/Usage/Used 2>/dev/null

# Se le metriche non sono ancora disponibili (VM appena avviata):
echo ""
echo "[INFO] Se i valori sono vuoti, aspetta 10 secondi e riesegui"
echo "       Le metriche richiedono qualche secondo per accumularsi"
```

**Step 3 — Monitora in loop per 30 secondi.**

```bash
# Monitor continuo per 30 secondi (6 campioni da 5s)
echo "=== MONITORING CPU/RAM (30 secondi) ==="
for i in $(seq 1 6); do
    echo "--- Campione $i/6 ($(date +%H:%M:%S)) ---"
    VBoxManage metrics query "DC-LAB-01" CPU/Load/User RAM/Usage/Used 2>/dev/null | \
        grep -E "CPU|RAM"
    VBoxManage metrics query "SRV-LINUX-01" CPU/Load/User RAM/Usage/Used 2>/dev/null | \
        grep -E "CPU|RAM"
    sleep 5
done
```

**Step 4 — Confronto prospettiva hypervisor vs VM.**

```bash
# Sul tuo host (hypervisor view):
echo "=== VISTA HYPERVISOR: risorse fisiche dell'host ==="
# Linux host:
if uname -s | grep -q Linux; then
    echo "CPU host:"; grep "cpu MHz" /proc/cpuinfo | head -4
    echo "RAM host:"; free -h
elif uname -s | grep -q Darwin; then
    echo "CPU host:"; sysctl -n hw.logicalcpu
    echo "RAM host:"; vm_stat
fi

echo ""
echo "=== DENTRO DC-LAB-01: come la VM vede le risorse ==="
echo "(Apri una sessione RDP o console su DC-LAB-01 e verifica in Task Manager)"
echo "Comando PowerShell da eseguire dentro DC-LAB-01:"
echo "  Get-CimInstance -ClassName Win32_OperatingSystem | Select TotalVisibleMemorySize, FreePhysicalMemory"
echo "  Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 5"
```

**Nota didattica — la differenza tra viste:**

```
HYPERVISOR vede:
  CPU utilizzata dalla VM: 15% dei core fisici allocati
  RAM used: 1.8 GB (RAM "balloon" — effettivamente in uso)
  
DENTRO LA VM vede:
  CPU: 15% di "2 core"
  RAM: 3.8 GB disponibili (allocati), 1.8 GB in uso
  
La VM non sa che "i suoi core" potrebbero essere condivisi con altre VM.
Se il CPU Ready è alto (hypervisor), la VM percepirà slowdown.
```

**Checkpoint B2:**
- [ ] `VBoxManage metrics setup` eseguito su DC-LAB-01
- [ ] Metriche CPU e RAM campionate con `VBoxManage metrics query`
- [ ] Comprendi la differenza tra vRAM allocata (VM vede) e RAM attiva (hypervisor vede)

---

### Esercizio B3: Snapshot — Creazione, Verifica, Rollback, Eliminazione

**Obiettivo.** Creare uno snapshot di SRV-LINUX-01, verificarne lo stato, simulare una modifica "disastrosa", eseguire il rollback, poi eliminare correttamente lo snapshot.

**Background.** Questo esercizio simula il workflow reale: prima di una manutenzione (aggiornamento kernel, modifica config critica), si crea uno snapshot. Se qualcosa va storto, si ripristina. Poi, se tutto è andato bene, si elimina lo snapshot entro 48h.

**Step 1 — Verifica stato snapshot attuale.**

```bash
# Prima di creare nuovi snapshot, verifica cosa c'è già
echo "=== SNAPSHOT ESISTENTI ==="
VBoxManage snapshot "SRV-LINUX-01" list 2>/dev/null || echo "Nessuno snapshot presente"
VBoxManage snapshot "DC-LAB-01"    list 2>/dev/null || echo "Nessuno snapshot presente"
VBoxManage snapshot "WKS-LAB-01"   list 2>/dev/null || echo "Nessuno snapshot presente"
```

**Step 2 — Crea uno snapshot "live" di SRV-LINUX-01.**

```bash
# Crea snapshot con la VM in esecuzione (live snapshot)
# Su VirtualBox senza Guest Additions: il filesystem potrebbe non essere quiesced
# Su VirtualBox con Guest Additions: il filesystem viene "congelato" correttamente
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAP_NAME="pre-maint_${TIMESTAMP}"

echo "=== CREAZIONE SNAPSHOT: $SNAP_NAME ==="
VBoxManage snapshot "SRV-LINUX-01" take "$SNAP_NAME" \
    --description "Snapshot pre-manutenzione per esercizio tutorial ops04e" \
    --live

echo ""
echo "Verifica snapshot creato:"
VBoxManage snapshot "SRV-LINUX-01" list
```

**Output atteso:**

```
=== CREAZIONE SNAPSHOT: pre-maint_20260715_143022 ===
0%...10%...20%...30%...40%...50%...60%...70%...80%...90%...100%
Snapshot taken. UUID: f1e2d3c4-...

Verifica snapshot creato:
   Name: pre-maint_20260715_143022 (UUID: f1e2d3c4-...)
   Description: Snapshot pre-manutenzione per esercizio tutorial ops04e
   Snapshot was taken at 14:30:22 on 2026-07-15T14:30:22.123000Z
```

**Step 3 — Verifica impatto sul disco (il delta file).**

```bash
# Dopo la creazione dello snapshot, il disco base è "congelato"
# Tutte le nuove scritture vanno in un file delta separato

VBoxManage list hdds | grep -A5 "SRV-LINUX-01"

# Controlla la cartella dove stanno i file della VM
VM_PATH=$(VBoxManage showvminfo "SRV-LINUX-01" --machinereadable | \
    grep "CfgFile" | cut -d'"' -f2 | xargs dirname)
echo "Cartella VM: $VM_PATH"

# Lista i file presenti (dovrebbe ora mostrare file .vdi o -delta.vmdk aggiuntivi)
ls -lah "$VM_PATH" 2>/dev/null || \
echo "[INFO] Su Windows: esplora %USERPROFILE%\VirtualBox VMs\SRV-LINUX-01\"
```

**Step 4 — Simula "danno" e rollback.**

```bash
# Simula modifica: connettiti a SRV-LINUX-01 via SSH e crea un file di test
ssh lab-admin@192.168.56.20 "echo 'MODIFICA_TEST_$(date)' | sudo tee /tmp/test_snapshot.txt"
echo "File di test creato: $(ssh lab-admin@192.168.56.20 'cat /tmp/test_snapshot.txt' 2>/dev/null)"

echo ""
echo "=== ROLLBACK allo snapshot pre-manutenzione ==="
echo "ATTENZIONE: la VM verrà spenta automaticamente per il ripristino"
echo "Premi CTRL+C per annullare, ENTER per procedere..."
read -r

# La VM deve essere spenta per il rollback in VirtualBox
VBoxManage controlvm "SRV-LINUX-01" poweroff 2>/dev/null
sleep 5

# Ripristina lo snapshot
SNAP_NAME=$(VBoxManage snapshot "SRV-LINUX-01" list 2>/dev/null | grep "pre-maint" | head -1 | awk '{print $2}')
VBoxManage snapshot "SRV-LINUX-01" restore "$SNAP_NAME"

# Riavvia la VM
VBoxManage startvm "SRV-LINUX-01" --type headless
sleep 30  # aspetta che SRV-LINUX-01 si avvii

# Verifica: il file di test non dovrebbe più esistere
ssh lab-admin@192.168.56.20 "ls /tmp/test_snapshot.txt 2>/dev/null && echo 'ROLLBACK FALLITO' || echo 'ROLLBACK OK: file non presente'"
```

**Step 5 — Elimina lo snapshot (dopo verifica esito positivo).**

```bash
echo "=== ELIMINAZIONE SNAPSHOT ==="
SNAP_NAME=$(VBoxManage snapshot "SRV-LINUX-01" list 2>/dev/null | grep "pre-maint" | head -1 | awk '{print $2}')

# L'eliminazione può richiedere alcuni minuti (merge del delta nel disco base)
VBoxManage snapshot "SRV-LINUX-01" delete "$SNAP_NAME"

echo ""
echo "Verifica: nessuno snapshot rimasto"
VBoxManage snapshot "SRV-LINUX-01" list 2>/dev/null || echo "Nessuno snapshot — OK"

echo ""
echo "=== DISK SIZE DOPO ELIMINAZIONE ==="
echo "[INFO] Il disco base potrebbe essere leggermente più grande ora"
echo "       (il delta è stato mergiato nel file base)"
```

**Checkpoint B3:**
- [ ] Snapshot creato con `VBoxManage snapshot take`
- [ ] Modifica di test creata dentro la VM
- [ ] Rollback eseguito e verifica che la modifica è scomparsa
- [ ] Snapshot eliminato con `VBoxManage snapshot delete`
- [ ] Comprendi che snapshot > 7 giorni è un problema

---

### Esercizio B4: Modifica Risorse VM — vCPU e RAM (Right-Sizing)

**Obiettivo.** Modificare la configurazione di vCPU e RAM di una VM in VirtualBox, simulando il processo di right-sizing che si farebbe in produzione.

**Background.** In produzione, il right-sizing richiede analisi dati di 2-4 settimane, approvazione del change management, finestra di manutenzione, backup/snapshot pre-modifica, e verifica post-modifica. Qui lo simuliamo su WKS-LAB-01 (workstation — meno critica).

**Nota importante:** In VirtualBox, la modifica di CPU e RAM richiede che la VM sia **spenta** (poweroff). VMware vSphere con Hot-Add CPU/RAM permette la modifica a caldo su VM supportate — concetto da conoscere per l'enterprise.

**Step 1 — Verifica configurazione corrente.**

```bash
echo "=== CONFIGURAZIONE CORRENTE WKS-LAB-01 ==="
VBoxManage showvminfo "WKS-LAB-01" | grep -E "Memory size|CPUs|State"
```

**Step 2 — Spegni WKS-LAB-01 per la modifica.**

```bash
echo "=== SPEGNIMENTO WKS-LAB-01 ==="
STATE=$(VBoxManage showvminfo "WKS-LAB-01" --machinereadable | grep "^VMState=" | cut -d'"' -f2)
echo "Stato corrente: $STATE"

if [ "$STATE" = "running" ]; then
    # Spegnimento pulito (ACPI power button)
    VBoxManage controlvm "WKS-LAB-01" acpipowerbutton
    echo "Inviato segnale ACPI spegnimento..."
    echo "Attendo 60 secondi per lo spegnimento pulito..."
    sleep 60
    
    # Verifica se si è spenta
    STATE=$(VBoxManage showvminfo "WKS-LAB-01" --machinereadable | grep "^VMState=" | cut -d'"' -f2)
    if [ "$STATE" != "poweroff" ]; then
        echo "Spegnimento lento — forzo poweroff"
        VBoxManage controlvm "WKS-LAB-01" poweroff
        sleep 5
    fi
fi
echo "VM spenta: $(VBoxManage showvminfo 'WKS-LAB-01' | grep State)"
```

**Step 3 — Modifica CPU e RAM.**

```bash
# Modifica: aggiungi 1 vCPU (da 2 a 3 — simulazione upgrade)
echo "=== MODIFICA VCPU ==="
VBoxManage modifyvm "WKS-LAB-01" --cpus 3
echo "vCPU impostata a: $(VBoxManage showvminfo 'WKS-LAB-01' | grep 'CPUs:')"

# Modifica: aumenta RAM (da 2048 a 3072 MB — simulazione upgrade)
echo "=== MODIFICA vRAM ==="
VBoxManage modifyvm "WKS-LAB-01" --memory 3072
echo "vRAM impostata a: $(VBoxManage showvminfo 'WKS-LAB-01' | grep 'Memory size:')"
```

**Step 4 — Riavvia e verifica.**

```bash
echo "=== RIAVVIO WKS-LAB-01 ==="
VBoxManage startvm "WKS-LAB-01" --type headless 2>/dev/null || \
VBoxManage startvm "WKS-LAB-01" --type gui

echo "Attendo 60 secondi per l'avvio..."
sleep 60

# Verifica
VBoxManage showvminfo "WKS-LAB-01" | grep -E "Memory size|CPUs|State"

echo ""
echo "=== VERIFICA DALL'INTERNO (via RDP a WKS-LAB-01) ==="
echo "Apri Task Manager → Performance → CPU: deve mostrare 3 core"
echo "RAM: 3.0 GB disponibili"
echo ""
echo "PowerShell (dentro WKS-LAB-01):"
echo '  (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors'
echo '  [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)'
```

**Step 5 — Ripristina la configurazione originale (rollback).**

```bash
# Se il right-sizing ha causato problemi, ripristina la configurazione originale
# (In questo caso è solo un esercizio, ma simula il processo di rollback)
VBoxManage controlvm "WKS-LAB-01" acpipowerbutton
sleep 60
VBoxManage controlvm "WKS-LAB-01" poweroff 2>/dev/null
sleep 5
VBoxManage modifyvm "WKS-LAB-01" --cpus 2 --memory 2048
VBoxManage startvm "WKS-LAB-01" --type headless 2>/dev/null || \
VBoxManage startvm "WKS-LAB-01" --type gui
echo "Configurazione ripristinata a 2 vCPU / 2048 MB"
```

**Checkpoint B4:**
- [ ] WKS-LAB-01 spenta con `acpipowerbutton` (spegnimento pulito)
- [ ] CPU e RAM modificate con `VBoxManage modifyvm`
- [ ] VM riavviata e verifica configurazione eseguita
- [ ] Configurazione ripristinata (rollback simulato)
- [ ] Comprendi perché la modifica richiede la VM spenta (vs Hot-Add enterprise)

---

### Esercizio B5: Export/Clone VM — Backup e Migrazione

**Obiettivo.** Esportare una VM in formato OVF (Open Virtualization Format) e clonare una VM esistente — operazioni fondamentali per backup, migrazione tra hypervisor, e deploy rapido di nuove VM.

**Background.** L'export OVF è lo standard aperto per il trasporto di VM tra diversi hypervisor. Puoi esportare da VirtualBox e importare in VMware (con piccole modifiche), o viceversa. Il clone è usato per "templatizzare" una VM configurata e distribuirla rapidamente.

**Step 1 — Export VM in formato OVF.**

```bash
# Crea la cartella di export
EXPORT_DIR="${HOME}/vm-exports"
mkdir -p "$EXPORT_DIR"

echo "=== EXPORT WKS-LAB-01 in OVF ==="
echo "Nota: la VM deve essere spenta per l'export"

# Spegni WKS-LAB-01 se in esecuzione
VBoxManage controlvm "WKS-LAB-01" acpipowerbutton 2>/dev/null
sleep 30
VBoxManage controlvm "WKS-LAB-01" poweroff 2>/dev/null
sleep 5

# Export OVF (formato aperto, importabile in VMware, Proxmox, etc.)
VBoxManage export "WKS-LAB-01" \
    --output "${EXPORT_DIR}/WKS-LAB-01-export.ovf" \
    --ovf20 \
    --vsys 0 \
    --product "WKS-LAB-01" \
    --vendor "Lab IT Operations" \
    --description "Workstation lab per tutorial IT Ops"

echo ""
echo "=== FILE ESPORTATI ==="
ls -lah "${EXPORT_DIR}/"
```

**Output atteso:**

```
=== FILE ESPORTATI ===
WKS-LAB-01-export.ovf     # Descrittore XML (configurazione VM)
WKS-LAB-01-export.mf      # File manifest (checksum)  
WKS-LAB-01-disk001.vmdk   # Disco virtuale compresso
```

**Step 2 — Verifica OVF e checksum.**

```bash
echo "=== CONTENUTO OVF (primi 50 righe) ==="
head -50 "${EXPORT_DIR}/WKS-LAB-01-export.ovf"

echo ""
echo "=== CHECKSUM FILE ==="
cat "${EXPORT_DIR}/WKS-LAB-01-export.mf" 2>/dev/null || \
ls -la "${EXPORT_DIR}/"
```

**Step 3 — Clone rapido di una VM (linked vs full).**

```bash
# CLONE FULL: copia indipendente completa
# Usa più spazio ma la VM clonata è completamente indipendente
echo "=== CLONE FULL DI SRV-LINUX-01 (esempio — richiede spazio) ==="
echo "[DEMO] Comando che si userebbe in produzione:"
echo "VBoxManage clonevm 'SRV-LINUX-01' --name 'SRV-LINUX-02-clone' --register --snapshot '' --mode machine"

# CLONE LINKED: usa snapshot differencing, poco spazio ma dipende dal parent
echo ""
echo "[DEMO] Clone linked (per laboratori, template deploy):"
echo "VBoxManage clonevm 'SRV-LINUX-01' --name 'SRV-LINUX-DEV' --register --snapshot 'base-clean' --mode machine --options link"

echo ""
echo "[INFO] Nel lab non eseguiamo il clone per risparmiare spazio disco."
echo "       Il concetto è identico a: VMware 'clone to VM', Hyper-V 'Export + Import', Proxmox 'qm clone'"
```

**Step 4 — Riavvia WKS-LAB-01.**

```bash
VBoxManage startvm "WKS-LAB-01" --type headless 2>/dev/null || \
VBoxManage startvm "WKS-LAB-01" --type gui
echo "WKS-LAB-01 riavviata"
```

**Checkpoint B5:**
- [ ] Export OVF creato con file `.ovf`, `.mf`, `.vmdk`
- [ ] Contenuto OVF letto — riconosci la struttura XML
- [ ] Differenza clone full vs clone linked compresa

---

### Esercizio B6: Simulazione Operazioni Enterprise (Comandi di Riferimento)

**Obiettivo.** Familiarizzarsi con i comandi equivalenti sulle piattaforme enterprise, che non abbiamo fisicamente nel lab ma sono fondamentali per il lavoro reale.

**Background.** Questo esercizio è teorico-pratico: leggi, comprendi e "esegui mentalmente" i comandi che useresti in un ambiente reale. In un colloquio o on-boarding aziendale, conoscere questi comandi dimostra comprensione dei concetti — anche se non li hai eseguiti su hardware fisico.

**VMware vSphere — comandi PowerCLI:**

```powershell
# Connessione a vCenter
Connect-VIServer -Server vcenter.lab.local -Credential (Get-Credential)

# Lista VM con risorse e stato
Get-VM | Select-Object Name, PowerState, NumCpu, MemoryGB,
    @{N='CPU_Avg%';E={[math]::Round((Get-Stat $_ -Stat cpu.usage.average -Realtime -MaxSamples 5 |
        Measure-Object -Property Value -Average).Average, 1)}} |
    Format-Table -AutoSize

# VM con snapshot più vecchi di 7 giorni — DA RIMUOVERE
Get-VM | Get-Snapshot | Where-Object { $_.Created -lt (Get-Date).AddDays(-7) } |
    Select-Object VM, Name, Created, SizeGB | Format-Table -AutoSize

# Right-sizing: VM con CPU avg < 20% (sovradimensionate)
# (In produzione: raccogli dati per 4 settimane prima di agire)
Get-VM | Where-Object { $_.PowerState -eq "PoweredOn" } | ForEach-Object {
    $avgCpu = (Get-Stat -Entity $_ -Stat cpu.usage.average -Start (Get-Date).AddDays(-30) |
        Measure-Object -Property Value -Average).Average
    if ($avgCpu -lt 20) {
        [PSCustomObject]@{ VM=$_.Name; vCPU=$_.NumCpu; RAM_GB=$_.MemoryGB; AvgCPU=$([math]::Round($avgCpu,1)) }
    }
}

# Vmotion: migra VM senza downtime tra host
Move-VM -VM "DC-LAB-01" -Destination (Get-VMHost "host02.lab.local")
```

**Microsoft Hyper-V — comandi PowerShell:**

```powershell
# Lista VM con stato e risorse
Get-VM | Select-Object Name, State, CPUUsage, MemoryAssigned, Uptime | Format-Table -AutoSize

# Checkpoint (equivalente VMware Snapshot)
Checkpoint-VM -Name "SRV-LINUX-01" -SnapshotName "pre-maint-$(Get-Date -Format 'yyyyMMdd')"
Get-VMSnapshot -VMName "SRV-LINUX-01"

# Checkpoint più vecchi di 7 giorni
Get-VM | Get-VMSnapshot | Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-7) } |
    Select-Object VMName, Name, CreationTime

# Rimuovi checkpoint vecchio
Remove-VMSnapshot -VMName "SRV-LINUX-01" -Name "pre-maint-20260601"

# Modifica risorse (VM deve essere spenta)
Set-VM -Name "WKS-LAB-01" -ProcessorCount 4 -MemoryStartupBytes 4GB

# Live Migration senza downtime
Move-VM -Name "DC-LAB-01" -DestinationHost "hyper-v-02.lab.local" -IncludeStorage `
    -DestinationStoragePath "D:\VMs"

# Replica Hyper-V (per DR)
Enable-VMReplication -VMName "SRV-LINUX-01" -ReplicaServerName "dr-hyper-v.lab.local" `
    -ReplicaServerPort 8080 -AuthenticationType Kerberos
```

**Proxmox VE — comandi CLI:**

```bash
# Lista VM e container
qm list              # VM KVM
pct list             # Container LXC

# Stato dettagliato VM
qm status 100        # VM con VMID 100
qm config 100        # Configurazione completa

# Snapshot Proxmox
qm snapshot 100 pre-maint --description "Pre-manutenzione $(date)"
qm listsnapshot 100

# Snapshot più vecchi di 7 giorni (analisi manuale o script)
for vmid in $(qm list | awk 'NR>1{print $1}'); do
    qm listsnapshot "$vmid" 2>/dev/null | grep -v "^UPID" | awk -v now="$(date +%s)" \
        '{print $1, $2}' | while read name ts; do
        # Calcola età snapshot
        [ "$name" != "current" ] && echo "VM $vmid: snapshot $name"
    done
done

# Modifica risorse (a caldo per alcune, spento per altre)
qm set 100 --cores 4 --memory 4096

# Clone da template
qm clone 9000 101 --name "new-vm" --full 1

# Migrazione tra nodi
qm migrate 100 pve-node2 --online    # live migration
qm migrate 100 pve-node2             # offline migration

# Stato HA
ha-manager status
ha-manager add 100 --group produzione --max_restart 3
```

**Checkpoint B6:**
- [ ] Letti e compresi i comandi VMware PowerCLI per inventario VM e snapshot
- [ ] Letti e compresi i comandi Hyper-V PowerShell per checkpoint e live migration
- [ ] Letti e compresi i comandi Proxmox per qm/pct e ha-manager
- [ ] Sai identificare il comando equivalente per ogni operazione tra le 3 piattaforme

---
---

## PART C: SISTEMATIZZARE — Governance della Virtualizzazione

---

### SOP-VIRT-001: Manutenzione Infrastruttura Virtuale

```
DOCUMENTO: SOP-VIRT-001 v1.0
TITOLO:    Procedura Operativa Standard — Gestione VM e Hypervisor
AMBITO:    Tutte le piattaforme di virtualizzazione (VirtualBox lab / Enterprise)
TRIGGER:   Settimanale (pulizia snapshot) / Mensile (right-sizing review)
OWNER:     Team IT Operations
```

**1. Check Settimanale Snapshot (15 min)**

```
STEP 1: Lista tutti gli snapshot di tutte le VM
  VirtualBox: for vm in $(VBoxManage list vms | awk -F'"' '{print $2}'); do
                  VBoxManage snapshot "$vm" list 2>/dev/null
              done
  VMware: Get-VM | Get-Snapshot | Select-Object VM, Name, Created, SizeGB
  Hyper-V: Get-VM | Get-VMSnapshot | Select-Object VMName, Name, CreationTime
  Proxmox: for vmid in $(qm list | awk 'NR>1{print $1}'); do
               qm listsnapshot "$vmid" 2>/dev/null; done
  
STEP 2: Identifica snapshot da eliminare
  Regola: snapshot > 7 giorni → richiede giustificazione scritta in GLPI
  Regola: snapshot > 30 giorni → eliminazione obbligatoria (change manager approva)
  Eccezioni: snapshot pre-release approvati (max 14 giorni) con ticket GLPI aperto

STEP 3: Per ogni snapshot da eliminare
  a) Verifica che il sistema associato funzioni correttamente
  b) Verifica che non ci sia un rollback pendente
  c) Elimina snapshot
  d) Documenta in GLPI: snapshot eliminato, motivo, data

STEP 4: Controlla spazio disco recuperato
  Nota: l'eliminazione fa un merge — può liberare o non liberare spazio
  immediatamente (dipende dall'hypervisor e dal tipo di snapshot)
```

**2. Review Right-Sizing Mensile (30 min)**

```
STEP 1: Estrai dati utilizzo ultime 4 settimane
  (vCenter: vSphere Performance → Last Month)
  (Hyper-V: Get-VMResourceMetering dopo Enable-VMResourceMetering)
  (Proxmox: pvesh get /nodes/pve/rrddata → Grafana o script)

STEP 2: Identifica candidati al right-sizing
  Criteri:
  - CPU: utilizzo medio < 15% E picco < 30% (sovradimensionata)
  - RAM: utilizzo attivo < 40% dell'allocato (sovradimensionata)
  
STEP 3: Per ogni candidata
  a) Apri ticket GLPI: Change Request tipo Normal
  b) Documenta: config attuale, config proposta, metrica di uso
  c) Notifica proprietario applicazione (2 settimane di preavviso)
  d) Pianifica finestra di manutenzione
  
STEP 4: Esegui in finestra manutenzione
  a) Snapshot pre-modifica
  b) Modifica vCPU/RAM
  c) Riavvio VM
  d) Monitor 48h post-modifica
  e) Rimuovi snapshot se tutto ok

STEP 5: Documenta risparmio in GLPI
  Risorse liberate = ora disponibili per nuove VM
```

**3. Escalation**

```
VM non risponde (stuck):   VBoxManage controlvm nome poweroff (FORZA)
                           Poi startvm — se ancora stuck: reinspeziona log
Snapshot > 50% dello spazio disco: P1 ticket → elimina snapshot
                                   più vecchi immediatamente
Hypervisor offline:        Segui DR-HV-001 (non coperto in questo tutorial)
Corruzione disco VM:       STOP operazioni → backup snapshot → contatta DBA/admin
```

---

### Script C1: vm_health_check.sh — Check Automatico VM VirtualBox

```bash
#!/usr/bin/env bash
# vm_health_check.sh — Check settimanale VM VirtualBox
# Eseguire sull'host VirtualBox
# Schedulare: crontab -e → 0 9 * * 1 /opt/scripts/vm_health_check.sh >> /var/log/vm_health.log 2>&1
# Prerequisiti: VBoxManage nel PATH

set -euo pipefail

VBOXMANAGE=$(command -v VBoxManage 2>/dev/null || \
    echo "/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe")
SNAP_WARN_DAYS=7
SNAP_CRIT_DAYS=30
LOG="/tmp/vm_health_$(date +%Y%m%d_%H%M%S).log"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ISSUES=()
STATUS="OK"

ok()   { echo -e "${GREEN}[OK]${NC}      $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}    $*"; STATUS="WARNING"; ISSUES+=("WARN: $*"); }
crit() { echo -e "${RED}[CRITICO]${NC} $*"; STATUS="CRITICAL"; ISSUES+=("CRIT: $*"); }

{
echo "============================================="
echo "  VM HEALTH CHECK — VirtualBox"
echo "  Host: $(hostname) | $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================="
echo ""

# Verifica VBoxManage accessibile
if ! "$VBOXMANAGE" --version &>/dev/null; then
    crit "VBoxManage non accessibile: $VBOXMANAGE"
    exit 1
fi

VBOX_VERSION=$("$VBOXMANAGE" --version 2>/dev/null)
echo "VirtualBox versione: $VBOX_VERSION"
echo ""

# ─── SEZIONE 1: STATO VM ──────────────────────────────────────────────────────
echo "━━━ [1] STATO VM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
VM_LIST=$("$VBOXMANAGE" list vms 2>/dev/null | awk -F'"' '{print $2}')
VM_COUNT=$(echo "$VM_LIST" | wc -l)
RUNNING_COUNT=$("$VBOXMANAGE" list runningvms 2>/dev/null | wc -l)
echo "VM totali registrate: $VM_COUNT"
echo "VM in esecuzione:     $RUNNING_COUNT"
echo ""

while IFS= read -r vm; do
    [ -z "$vm" ] && continue
    info=$("$VBOXMANAGE" showvminfo "$vm" --machinereadable 2>/dev/null)
    state=$(echo "$info"  | grep "^VMState="    | cut -d'"' -f2)
    mem=$(echo "$info"    | grep "^memory="     | cut -d'=' -f2)
    cpus=$(echo "$info"   | grep "^cpus="       | cut -d'=' -f2)
    
    if [ "$state" = "running" ]; then
        ok "VM: $vm | State: $state | vCPU: $cpus | vRAM: ${mem}MB"
    elif [ "$state" = "poweroff" ]; then
        warn "VM: $vm | State: $state (spenta — prevista o problem?)"
    elif [ "$state" = "saved" ]; then
        warn "VM: $vm | State: SAVED (VM in stato sospeso — snapshot implicito)"
    else
        crit "VM: $vm | State: $state (stato anomalo)"
    fi
done <<< "$VM_LIST"
echo ""

# ─── SEZIONE 2: SNAPSHOT AUDIT ────────────────────────────────────────────────
echo "━━━ [2] SNAPSHOT AUDIT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TODAY_EPOCH=$(date +%s)
TOTAL_SNAPS=0
OLD_SNAPS=0

while IFS= read -r vm; do
    [ -z "$vm" ] && continue
    snap_output=$("$VBOXMANAGE" snapshot "$vm" list 2>/dev/null || true)
    
    if [ -z "$snap_output" ]; then
        ok "VM: $vm | Nessuno snapshot"
        continue
    fi
    
    # Conta snapshot (ogni riga che inizia con "Name:")
    snap_count=$(echo "$snap_output" | grep -c "Name:" || true)
    TOTAL_SNAPS=$((TOTAL_SNAPS + snap_count))
    
    # Cerca snapshot con data nel nome (pattern: YYYYMMDD)
    while IFS= read -r line; do
        if echo "$line" | grep -qE "[0-9]{8}"; then
            # Estrai data dallo snapshot name
            snap_date=$(echo "$line" | grep -oE "[0-9]{8}" | head -1)
            if [ -n "$snap_date" ]; then
                snap_epoch=$(date -d "${snap_date:0:4}-${snap_date:4:2}-${snap_date:6:2}" +%s 2>/dev/null || echo "$TODAY_EPOCH")
                age_days=$(( (TODAY_EPOCH - snap_epoch) / 86400 ))
                snap_name=$(echo "$line" | grep -oE '"[^"]*"' | head -1 | tr -d '"')
                
                if [ "$age_days" -ge "$SNAP_CRIT_DAYS" ]; then
                    crit "VM: $vm | Snapshot '$snap_name' ha ${age_days} giorni — ELIMINA ORA"
                    OLD_SNAPS=$((OLD_SNAPS + 1))
                elif [ "$age_days" -ge "$SNAP_WARN_DAYS" ]; then
                    warn "VM: $vm | Snapshot '$snap_name' ha ${age_days} giorni"
                    OLD_SNAPS=$((OLD_SNAPS + 1))
                else
                    ok "VM: $vm | Snapshot '$snap_name' (${age_days} giorni)"
                fi
            fi
        fi
    done <<< "$snap_output"
    
    [ "$snap_count" -gt 0 ] && [ "$OLD_SNAPS" -eq 0 ] && \
        ok "VM: $vm | $snap_count snapshot (tutti recenti)"
done <<< "$VM_LIST"

echo ""
echo "Totale snapshot trovati: $TOTAL_SNAPS | Snapshot da rivedere: $OLD_SNAPS"
echo ""

# ─── SEZIONE 3: SPAZIO DISCO HOST ─────────────────────────────────────────────
echo "━━━ [3] SPAZIO DISCO HOST ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
df -h | grep -E "^/dev|^Filesystem" | while IFS= read -r line; do
    [ "$(echo "$line" | awk '{print $1}')" = "Filesystem" ] && echo "$line" && continue
    pct=$(echo "$line" | awk '{print $5}' | tr -d '%')
    if [ "${pct:-0}" -ge 90 ]; then
        crit "Disco: $line"
    elif [ "${pct:-0}" -ge 75 ]; then
        warn "Disco: $line"
    else
        ok "Disco: $line"
    fi
done
echo ""

# ─── SOMMARIO ─────────────────────────────────────────────────────────────────
echo "============================================="
echo "STATO COMPLESSIVO: $STATUS"
if [ ${#ISSUES[@]} -gt 0 ]; then
    echo ""
    echo "AZIONI RICHIESTE:"
    for issue in "${ISSUES[@]}"; do
        echo "  → $issue"
    done
fi
echo "Report: $LOG"
echo "Fine: $(date '+%H:%M:%S')"
echo "============================================="
} | tee "$LOG"

exit 0
```

**Deploy script:**

```bash
# Sul tuo host (dove gira VirtualBox)

# Linux/Mac host:
sudo mkdir -p /opt/scripts
sudo cp vm_health_check.sh /opt/scripts/
sudo chmod +x /opt/scripts/vm_health_check.sh
sudo /opt/scripts/vm_health_check.sh

# Schedulazione settimanale (Linux/Mac):
crontab -e
# Aggiungi: 0 9 * * 1 /opt/scripts/vm_health_check.sh >> /var/log/vm_health_weekly.log 2>&1

# Windows (Task Scheduler con Git Bash o WSL):
# schtasks /create /tn "VM Health Check" /tr "bash /opt/scripts/vm_health_check.sh" /sc WEEKLY /d MON /st 09:00
```

---

### Integrazione con ITIL: Virtualizzazione e Gestione dei Servizi

**Quale pratica ITIL?**

| Pratica ITIL | Come si manifesta nella virtualizzazione |
|---|---|
| **Configuration Management** | CMDB con tutte le VM come CI (Configuration Item) |
| **Change Management** | Ogni modifica VM (CPU/RAM/snapshot) è un change record |
| **Availability Management** | HA cluster garantisce SLA di disponibilità (99.9%) |
| **Capacity Management** | Right-sizing, overcommit monitoring, capacity planning |
| **Release Management** | Deploy nuove VM da template — processo standardizzato |

**Il ciclo di vita di una VM come processo ITIL:**

```
1. SERVICE REQUEST: "Richiesta nuova VM per progetto CRM"
   → Ticket in GLPI: requisiti (CPU/RAM/OS/scopo)
   → Approvazione manager IT

2. CHANGE REQUEST: "Deploy VM CRM-APP-01"
   → RFC in GLPI: change normal
   → Standard template: scelto da catalogo
   → CAB approval se impatta produzione

3. PROVISIONING (implementazione):
   → Clone da template gold image
   → Configurazione OS (hostname, IP, join AD)
   → Test di accettazione (ping, RDP/SSH, servizi)
   
4. OPERAZIONI (vita della VM):
   → Monitoraggio continuo (CPU/RAM/Disk)
   → Snapshot prima di ogni manutenzione
   → Patch mensili coordinate con Change Management
   → Right-sizing semestrale
   
5. DECOMMISSIONING (fine vita):
   → Approvazione smantellamento
   → Backup finale + export OVF (retention 90 giorni)
   → Snapshot eliminati
   → VM spenta → poi deregistrata
   → Risorse liberate documentate in CMDB
```

**Come scala a 500 VM?**

```
Con 500 VM non puoi gestire snapshot manualmente.

AUTOMATION TOOLS:
  VMware: vRealize Orchestrator + vSphere HA + DRS automatico
  Proxmox: pveam + Ceph + vzdump schedulato via web UI
  Hyper-V: SCVMM (System Center VMM) per orchestrazione
  
MONITORING PLATFORM:
  Prometheus + vSphere Exporter: metriche tutte le VM in Grafana
  Alert automatici: CPU Ready > 5%, snapshot > 7 giorni, RAM balloon
  
SELF-SERVICE PORTAL:
  Gli utenti richiedono VM da un catalogo → deploy automatico in ore, non giorni
  Approvazione workflow automatica per richieste standard
  
RIGHT-SIZING AUTOMATICO:
  Tool: Turbonomic, CloudPhysics, VMware Operations Manager
  Analizzano 30-90 giorni di dati, suggeriscono right-sizing con ROI calcolato
```

---

### Checklist di Validazione Lab

**Part A — Fondamenti:**
- [ ] Sai spiegare Tipo 1 vs Tipo 2 hypervisor con esempi
- [ ] Comprendi il rischio dell'overcommit CPU e RAM
- [ ] Sai descrivere il comportamento di uno snapshot (file delta)
- [ ] Conosci il rischio "snapshot > 7 giorni" e perché
- [ ] Sai cosa significa "right-sizing" e quando farlo

**Part B — Operazioni:**
- [ ] `VBoxManage list vms` mostra le 3 VM del lab
- [ ] `VBoxManage showvminfo` usato per vedere CPU/RAM/disco di una VM
- [ ] Metriche CPU/RAM campionate con `VBoxManage metrics query`
- [ ] Snapshot creato, rollback eseguito, snapshot eliminato
- [ ] VM spenta e riconfigurata (CPU/RAM) con `VBoxManage modifyvm`
- [ ] Export OVF creato con file .ovf, .mf, .vmdk
- [ ] Comandi VMware/Hyper-V/Proxmox equivalenti riconosciuti

**Part C — Sistematizzare:**
- [ ] SOP-VIRT-001 letta con comprensione del processo snapshot review
- [ ] `vm_health_check.sh` deployato e testato
- [ ] Ciclo di vita VM mappato a pratiche ITIL
- [ ] Sai spiegare come questo processo scala a 500 VM

---

### Appendice A: Comandi VBoxManage Essenziali

```bash
# INVENTORY
VBoxManage list vms                          # Tutte le VM
VBoxManage list runningvms                   # VM in esecuzione
VBoxManage showvminfo "VM-NAME"              # Info completa
VBoxManage showvminfo "VM-NAME" --machinereadable  # Formato parsing

# LIFECYCLE
VBoxManage startvm "VM-NAME" --type headless  # Avvia (senza GUI)
VBoxManage startvm "VM-NAME" --type gui       # Avvia (con GUI)
VBoxManage controlvm "VM-NAME" acpipowerbutton  # Spegnimento pulito
VBoxManage controlvm "VM-NAME" poweroff         # Forza spegnimento
VBoxManage controlvm "VM-NAME" pause            # Metti in pausa
VBoxManage controlvm "VM-NAME" resume           # Riprendi
VBoxManage controlvm "VM-NAME" savestate        # Sospendi (save state)

# SNAPSHOT
VBoxManage snapshot "VM-NAME" list
VBoxManage snapshot "VM-NAME" take "snap-name" --description "..." --live
VBoxManage snapshot "VM-NAME" restore "snap-name"
VBoxManage snapshot "VM-NAME" delete "snap-name"

# CONFIGURAZIONE (VM deve essere spenta)
VBoxManage modifyvm "VM-NAME" --memory 4096      # Cambia RAM (MB)
VBoxManage modifyvm "VM-NAME" --cpus 4           # Cambia vCPU
VBoxManage modifyvm "VM-NAME" --vram 32          # Cambia VRAM
VBoxManage modifyvm "VM-NAME" --description "..."

# DISCO
VBoxManage list hdds                         # Tutti i dischi registrati
VBoxManage showhdinfo "/path/to/disk.vdi"    # Info disco
VBoxManage modifyhd "/path/to/disk.vdi" --resize 51200  # Espandi a 50GB

# RETE
VBoxManage modifyvm "VM-NAME" --nic1 hostonly --hostonlyadapter1 "vboxnet0"
VBoxManage modifyvm "VM-NAME" --nic2 nat

# EXPORT/IMPORT
VBoxManage export "VM-NAME" --output "/path/to/vm.ovf" --ovf20
VBoxManage import "/path/to/vm.ovf" --dry-run  # Simula import
VBoxManage import "/path/to/vm.ovf"            # Importa

# METRICHE
VBoxManage metrics setup --period 1 --samples 60 "VM-NAME"
VBoxManage metrics query "VM-NAME"
VBoxManage metrics collect "VM-NAME" CPU/Load/User RAM/Usage/Used

# GUEST ADDITIONS (dentro la VM)
VBoxManage guestcontrol "VM-NAME" run --exe "/bin/bash" -- -c "whoami"
```

---

### Appendice B: Confronto Comandi Tra Piattaforme

| Operazione | VirtualBox | VMware ESXi/vCenter | Hyper-V | Proxmox |
|---|---|---|---|---|
| Lista VM | `list vms` | `Get-VM` | `Get-VM` | `qm list` |
| Avvia VM | `startvm` | `Start-VM` | `Start-VM` | `qm start 100` |
| Spegni VM | `controlvm poweroff` | `Stop-VM` | `Stop-VM` | `qm stop 100` |
| Info VM | `showvminfo` | `Get-VMResource` | `Get-VM -Name` | `qm config 100` |
| Crea snapshot | `snapshot take` | `New-Snapshot` | `Checkpoint-VM` | `qm snapshot 100` |
| Ripristina snapshot | `snapshot restore` | `Set-VM -Snapshot` | `Restore-VMSnapshot` | `qm rollback 100` |
| Elimina snapshot | `snapshot delete` | `Remove-Snapshot` | `Remove-VMSnapshot` | `qm delsnapshot 100` |
| Modifica CPU | `modifyvm --cpus` | `Set-VM -NumCPU` | `Set-VM -Proc` | `qm set 100 --cores` |
| Modifica RAM | `modifyvm --memory` | `Set-VM -MemoryGB` | `Set-VM -MemoryGB` | `qm set 100 --memory` |
| Migrazione | Export+Import | `Move-VM` (vMotion) | `Move-VM` (Live Mig.) | `qm migrate 100 pve2` |
| Clone | `clonevm` | `New-VM -DiskGB` | Export+Import | `qm clone 100 101` |
| Export | `export --output` | `Export-VM` | `Export-VM` | `vzdump 100` |

---

### Riferimenti

- VirtualBox Manual: VBoxManage reference — https://www.virtualbox.org/manual/ch08.html
- VMware KB: Snapshot best practices — regole 7/30 giorni
- `04-servizi-infrastruttura.md` §Manutenzione Virtualizzazione
- ITIL 4: Configuration Management Practice
- Tutorial prerequisiti: `tutorial_ops03a` (Windows Server), `tutorial_ops03b` (Linux)
- Tutorial correlati: `tutorial_ops04_ch2b` (Storage — thin provisioning), `tutorial_ops06_ch1a` (Backup — snapshot vs backup)
