# Tutorial: Fondamenti VMware — L'Ambiente che Stai per Lasciare — Lab Pratico

> **Documenti di riferimento:** `01-FONDAMENTI-VMWARE/architettura-vsphere-esxi.md` · `01-FONDAMENTI-VMWARE/vmware-networking-storage.md`
> **Dominio:** Migrazione VMware vSphere → Proxmox VE — Fase 1, Fondamenti
> **Ambito:** architettura vSphere e VMkernel · licensing post-Broadcom · `esxcli` operativo · gestione memoria e CPU scheduler · vSwitch, port group, VLAN e NIC teaming · VMFS, NFS, iSCSI e tipi di VMDK · inventario PowerCLI che alimenta il piano di migrazione · ciò che blocca una migrazione e va scoperto adesso
> **Durata lab:** 5-6 ore
> **Livello:** Intermedio — richiede Linux (systemd, rete, LVM) e TCP/IP con VLAN
> **Prerequisiti:** un host con virtualizzazione annidata attiva; Proxmox VE 8.x già installato su `pve1`; PowerShell 7 sul client
> **Ambiente:** ESXi 8.0 U3 annidato dentro Proxmox VE 8.x, licenza di valutazione 60 giorni

---

## Perché questo tutorial esiste

Questo è un corso di migrazione, non un corso di VMware. La differenza cambia cosa studi e in che ordine.

Non impari vSphere per amministrarlo: lo impari per **inventariarlo, capirne i vincoli e portartelo via**. Ogni concetto di questa lezione arriva accompagnato dal suo equivalente Proxmox, e il laboratorio non finisce con "ho configurato un vSwitch" ma con **sei file CSV** che i tutorial successivi consumeranno davvero — quelli dell'assessment (`migr05`), del networking (`migr07`) e dello storage (`migr08`).

```
COSA PRODUCI ALLA FINE DI QUESTO LAB

  ~/migrazione-lab/assessment/
  ├── host-inventory.csv      hardware, versioni, build degli host ESXi
  ├── vm-inventory.csv        risorse, OS, firmware, UUID di ogni VM
  ├── vm-disks.csv            dischi, formato, datastore di provenienza
  ├── vm-snapshots.csv        gli snapshot che DEVONO sparire prima
  ├── portgroups.csv          port group, VLAN ID, vSwitch
  ├── datastores.csv          tipo, capacità, versione VMFS
  ├── vsphere-roles.csv       i ruoli, personalizzati compresi
  └── vsphere-permissions.csv chi può fare cosa, e su cosa

  Questi otto file sono l'input della Fase 2. Senza, il piano di
  migrazione è un'ipotesi.
```

---

## Lab Environment Setup

### Architettura del lab

Il laboratorio è quello definito dalla guida allo studio del corso, e **resta lo stesso per tutti i diciannove tutorial**. Vale la pena costruirlo una volta bene.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ARCHITETTURA DEL LABORATORIO                       │
│                                                                       │
│  Management  10.10.10.0/24  (VLAN 10)   ← console, SSH, API          │
│  VM traffic  10.10.20.0/24  (VLAN 20)   ← le VM migrate              │
│  Storage     10.10.30.0/24  (VLAN 30)   ← NFS, iSCSI                 │
│  Migrazione  10.10.40.0/24  (VLAN 40)   ← traffico di conversione    │
│                                                                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                        │
│  │  pve1     │  │  pve2     │  │  pve3     │  ← destinazione        │
│  │ 10.10.10.11│ │ 10.10.10.12│ │ 10.10.10.13│                        │
│  └─────┬─────┘  └───────────┘  └───────────┘                        │
│        │                                                              │
│        │  dentro pve1, annidato:                                     │
│        └──► ┌──────────────┐    ┌──────────────┐                    │
│             │  esxi1       │    │  NFS server  │                    │
│             │ 10.10.10.20  │    │ 10.10.30.50  │                    │
│             │  ← SORGENTE  │    │  ← condiviso │                    │
│             └──────────────┘    └──────────────┘                    │
│                                                                       │
│  Workstation 10.10.10.100 — PowerShell 7 + PowerCLI, browser        │
└──────────────────────────────────────────────────────────────────────┘

⚠ IN QUESTO TUTORIAL COSTRUISCI SOLO `esxi1`. I tre nodi Proxmox
  arrivano nel tutorial migr02; qui pve1 serve solo come contenitore
  per l'ESXi annidato.
```

### Verifica dei prerequisiti

```bash
# === CHECK PREREQUISITI — da eseguire su pve1 ===
echo "=== VIRTUALIZZAZIONE ANNIDATA ==="

# La virtualizzazione annidata è la condizione che rende possibile
# tutto il resto: senza, ESXi si installa ma nessuna VM al suo
# interno si accende.
if [ "$(cat /sys/module/kvm_intel/parameters/nested 2>/dev/null)" = "Y" ] ||
   [ "$(cat /sys/module/kvm_amd/parameters/nested 2>/dev/null)" = "1" ]; then
  echo "[OK] nested virtualization attiva"
else
  echo "[FAIL] nested NON attiva — vedi il blocco successivo"
fi

# Estensioni di virtualizzazione hardware
grep -qE '(vmx|svm)' /proc/cpuinfo && echo "[OK] VT-x/AMD-V presente" \
  || echo "[FAIL] virtualizzazione disabilitata nel BIOS"

echo ""
echo "=== RISORSE ==="
echo "RAM totale:  $(free -g | awk '/^Mem:/{print $2}') GB   (minimo 32, consigliato 64)"
echo "Core CPU:    $(nproc)                                  (minimo 8)"
echo "Spazio /var: $(df -BG /var/lib/vz | awk 'NR==2{print $4}')  (minimo 200G)"

echo ""
echo "=== VERSIONE PROXMOX ==="
pveversion
```

```bash
# === ATTIVARE LA VIRTUALIZZAZIONE ANNIDATA, se il check è fallito ===
# Intel
echo "options kvm_intel nested=1" > /etc/modprobe.d/kvm-nested.conf
# AMD — usare questa riga al posto della precedente su CPU AMD
# echo "options kvm_amd nested=1" > /etc/modprobe.d/kvm-nested.conf

# Il modulo va ricaricato: se ci sono VM accese, il rmmod fallisce.
# In quel caso serve un riavvio, ed è la strada più pulita.
modprobe -r kvm_intel 2>/dev/null && modprobe kvm_intel

# Verifica
cat /sys/module/kvm_intel/parameters/nested   # atteso: Y
```

⚠ La virtualizzazione annidata costa fra il 10% e il 15% di prestazioni, e in un lab non conta. Conta invece sapere che **le misure di prestazioni fatte qui non sono trasferibili in produzione**: quando nel tutorial `migr08` misurerai l'I/O, il numero sarà quello del lab, non quello del cliente. Lo diremo di nuovo lì.

### Creare la VM per ESXi annidato

```bash
# === CREAZIONE VM esxi1 SU pve1 ===
# `-cpu host` è obbligatorio: ESXi controlla le feature della CPU
# all'avvio e rifiuta di installarsi su una CPU emulata generica.
qm create 200 \
  --name esxi1 \
  --memory 16384 \
  --cores 4 \
  --cpu host \
  --machine q35 \
  --bios ovmf \
  --efidisk0 local-lvm:1,efitype=4m \
  --scsihw pvscsi \
  --net0 vmxnet3,bridge=vmbr0 \
  --ostype other

# Disco di sistema per ESXi
qm set 200 --scsi0 local-lvm:32

# Secondo disco: diventerà il datastore VMFS del lab
qm set 200 --scsi1 local-lvm:200

# ISO di installazione (scaricata dal portale Broadcom con account
# gratuito: la licenza di valutazione dura 60 giorni)
qm set 200 --ide2 local:iso/VMware-VMvisor-Installer-8.0U3.iso,media=cdrom
qm set 200 --boot order='ide2;scsi0'

qm start 200
```

```
⚠ TRE PUNTI DOVE QUESTA CONFIGURAZIONE SI ROMPE, e perché

  1. SENZA `-cpu host` l'installer si ferma con un errore sulla CPU.
     È la causa numero uno dei fallimenti di ESXi annidato.
  2. LA SCHEDA DI RETE deve essere `vmxnet3` o `e1000e`: ESXi 8 ha
     rimosso i driver di molte schede legacy, `virtio` compreso.
  3. IL CONTROLLER `pvscsi` è quello che ESXi riconosce nativamente.
     Con `virtio-scsi` l'installer non vede alcun disco, e l'errore
     dice "no compatible storage device" senza spiegare perché.

⚠ E UNA VERIFICA CHE DEVI FARE TU: questi parametri valgono per
  ESXi 8.0 U3 su Proxmox VE 8.x con CPU Intel di decima
  generazione o successiva. Su hardware diverso — soprattutto AMD
  con generazioni Zen precedenti — la matrice di compatibilità va
  controllata sulla documentazione della tua versione. Non la do
  per verificata sul tuo hardware, perché non lo è.
```

Segui l'installer da console: accetta l'EULA, scegli `scsi0` come disco di sistema, imposta la password di root, e configura la rete di management su `10.10.10.20/24` con gateway `10.10.10.1`. Al termine, l'host risponde su `https://10.10.10.20/ui`.

### PowerShell e PowerCLI sul client

```bash
# === POWERCLI SU LINUX — dalla workstation, non da ESXi ===
# PowerCLI è il modo serio di inventariare vSphere. Gira su
# PowerShell 7, che è multipiattaforma.
pwsh -Command 'Install-Module VMware.PowerCLI -Scope CurrentUser -Force'

# Il lab usa certificati autofirmati: senza questa riga ogni
# Connect-VIServer fallisce con un errore di certificato.
pwsh -Command 'Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false'

# Verifica
pwsh -Command 'Get-Module -ListAvailable VMware.PowerCLI | Select-Object Name,Version'
```

```bash
# Directory di lavoro: gli artefatti dell'assessment vivono qui e
# vengono riusati da tutti i tutorial successivi
mkdir -p ~/migrazione-lab/{assessment,script,output}
cd ~/migrazione-lab
echo "[OK] lab pronto in ~/migrazione-lab"
```

---

## PART A: FONDAMENTI — L'architettura che stai per lasciare

> vSphere non è un prodotto: è un ecosistema di componenti che cooperano. Capire quali di questi hanno un equivalente in Proxmox, quali si sostituiscono con qualcos'altro e quali semplicemente spariscono è la premessa di ogni decisione che prenderai nelle prossime diciotto lezioni. Chi salta questo passaggio scopre a metà migrazione che una funzionalità su cui contava non esiste dall'altra parte — e a quel punto la scoperta costa una finestra di manutenzione.

---

### Concetto A1: I tre pezzi, e quale sopravvive

> **Analogia.** Un'orchestra. **ESXi** sono i musicisti: ognuno suona il proprio strumento e potrebbe farlo anche da solo. **vCenter** è il direttore: non produce un suono, ma è l'unico che sa cosa devono fare tutti insieme — senza di lui i musicisti suonano, ma non c'è più il concerto. **vSphere Client** è lo spartito sul leggio: la vista che ti fa capire cosa sta succedendo. Quando migri, i musicisti hanno un equivalente diretto, il direttore no: in Proxmox la direzione non è un componente separato, è distribuita fra i musicisti stessi.

```
+=====================================================================+
|                    vSphere — i componenti                            |
+=====================================================================+
|                                                                      |
|   vSphere Client (HTML5)  ──┐                                       |
|   PowerCLI                ──┼──► vCenter Server Appliance (vCSA)    |
|   REST API                ──┘      ├── SSO / PSC                    |
|                                     ├── vpxd (il servizio centrale) |
|                                     ├── PostgreSQL (inventario)     |
|                                     └── Inventory Service           |
|                                             │                        |
|            ┌────────────────────────────────┼───────────────┐       |
|            ▼                                ▼               ▼       |
|      ┌───────────┐                    ┌───────────┐   ┌──────────┐ |
|      │ ESXi 1    │                    │ ESXi 2    │   │ ESXi N   │ |
|      │ VM VM VM  │                    │ VM VM     │   │ VM       │ |
|      └───────────┘                    └───────────┘   └──────────┘ |
+=====================================================================+

E COSA DIVENTA IN PROXMOX

  ESXi              ──► un nodo Proxmox VE (Debian + KVM/QEMU)
  vCenter           ──► NIENTE. Non esiste un nodo di gestione
                        centrale: ogni nodo è anche console, e il
                        cluster si tiene con Corosync + pmxcfs
  vSphere Client    ──► l'interfaccia web di QUALUNQUE nodo
  PowerCLI          ──► l'API REST di Proxmox + `qm`/`pct`/`pvesm`
  vCenter DB        ──► pmxcfs, un filesystem replicato su tutti i
                        nodi (`/etc/pve`)

⚠ L'ASSENZA DI vCENTER È IL CAMBIO ARCHITETTURALE PIÙ GRANDE, e va
  nella colonna dei vantaggi e in quella dei costi insieme.
   · non c'è un single point of failure di gestione, e non c'è una
     appliance da patchare, dimensionare e salvare
   · ma non c'è nemmeno un punto unico dove leggere lo stato di
     cento host, e le funzioni che vivevano in vCenter — DRS su
     tutte — o si ricostruiscono o si perdono (§migr10)
```

---

### Concetto A2: ESXi non è Linux, e il giorno del cutover si vede

Molti arrivano alla migrazione convinti che ESXi sia "un Linux con sopra un hypervisor". Non lo è, e la differenza spiega perché certe cose in Proxmox si fanno in un modo che sembra troppo semplice.

```
+=====================================================================+
|                      ESXi — lo stack reale                           |
+=====================================================================+
|  +-----+ +-----+ +-----+                                            |
|  | VM1 | | VM2 | | VMn |          ← guest                          |
|  +--+--+ +--+--+ +--+--+                                            |
|     |       |       |                                                |
|  +--v-------v-------v-----------------------------+                 |
|  |  vmx / vmx-vcpu-N        (un processo per VM)  |  ← user world  |
|  +------------------------------------------------+                 |
|  |  hostd · vpxa · sfcbd · dcui · rhttpproxy      |  ← gestione    |
|  +================================================+                 |
|  |                 VMkernel                        |                 |
|  |  scheduler CPU · memory manager · driver        |                 |
|  |  driver VMFS · stack di rete · stack SCSI       |                 |
|  +================================================+                 |
|  |                 hardware x86-64                 |                 |
|  +-------------------------------------------------+                |
+=====================================================================+

IL VMkernel È UN MICROKERNEL PROPRIETARIO, non un kernel Linux. Da
questo discendono tre conseguenze pratiche:

  1. NON PUOI INSTALLARCI SOFTWARE. Niente `apt`, niente agenti di
     monitoraggio arbitrari: si estende con i VIB, che sono pacchetti
     firmati da VMware o dal vendor dell'hardware.
  2. LA SHELL È VOLUTAMENTE POVERA. `esxcli` è un'interfaccia
     verso il VMkernel, non una shell di sistema.
  3. IL FILESYSTEM È VMFS, che è un filesystem a cluster fatto per
     un caso d'uso solo: file grandi, pochi, aperti da più host
     contemporaneamente con locking distribuito.

E IN PROXMOX
  il nodo È una Debian. `apt`, systemd, journalctl, i tuoi agenti,
  i tuoi script. È il vantaggio più immediato della migrazione, ed
  è anche il rischio più immediato: su un nodo Proxmox si può
  rompere il sistema in modi che su ESXi erano impossibili.
```

| Processo ESXi | Cosa fa | Equivalente su Proxmox |
|---|---|---|
| `vmx` / `vmx-vcpu-N` | il processo di una VM, un thread per vCPU | il processo `qemu-system-x86_64` |
| `hostd` | il demone di gestione dell'host, serve l'API | `pvedaemon` + `pveproxy` |
| `vpxa` | l'agente che parla con vCenter | non esiste: non c'è vCenter |
| `dcui` | la console diretta su Alt+F2 | una console Linux normale |
| `sfcbd` | broker CIM per l'hardware | `lm-sensors`, IPMI, i tool del vendor |

---

### Concetto A3: Il licensing, che è la ragione per cui sei qui

Questa sezione non è un'opinione sul valore dei prodotti: è il contesto che spiega perché un corso di migrazione esiste. La decisione strategica, in questo corso, si assume già presa.

```
COSA È CAMBIATO CON L'ACQUISIZIONE BROADCOM (novembre 2023)

  PRIMA — licenze perpetue, per CPU o per VM
    Essentials              ~500 USD, fino a 3 host
    Essentials Plus       ~4.500 USD, + HA e vMotion
    Standard              ~1.100 USD/CPU
    Enterprise Plus       ~3.500 USD/CPU, + DRS e dvSwitch
    ROBO                  per-VM, per le sedi remote

  DOPO — solo abbonamento, prezzo per CORE
    VCF   vSphere + vSAN + NSX + Aria      lo stack completo
    VVF   vSphere + vSAN
    VSS   solo vSphere
    VVEP  fino a 96 core, per le PMI

  GLI EFFETTI OPERATIVI, che sono quelli che ti riguardano:
   · le licenze perpetue non si comprano più, e quelle possedute
     restano ma senza supporto rinnovabile allo stesso modo
   · il prezzo si calcola sui core, con un minimo per CPU: un host
     con due socket da 8 core può pagare come uno da molti di più
   · prodotti standalone discontinuati, canale partner ridotto
   · aumenti riportati da molti clienti fra 2x e 10x
```

⚠ Le cifre della tabella "prima" sono prezzi di listino indicativi dell'epoca, non quotazioni: servono a mostrare la **struttura** del modello, non a preventivare. Per un business case reale — che costruirai nel tutorial `migr15` — i numeri devono venire dai contratti veri del cliente e da un preventivo attuale, mai da una tabella in un corso.

---

## PART B: ESXi DALLA RIGA DI COMANDO

> L'interfaccia web di ESXi va bene per guardare. Per inventariare, per capire cosa c'è davvero su un host e per scriptare, si usa `esxcli`. È anche l'unico strumento disponibile quando l'host è in sofferenza e la web non risponde più — situazione in cui ti troverai, prima o poi, la notte di un cutover.

---

### Esercizio B1: Primo contatto — l'host si presenta

Abilita SSH dalla console DCUI (F2 → Troubleshooting Options → Enable SSH), poi collegati.

```bash
# === DALLA WORKSTATION ===
ssh root@10.10.10.20

# === SISTEMA ===
esxcli system version get
# Product: VMware ESXi
# Version: 8.0.3
# Build: Releasebuild-24022510
# Update: 3
# Patch: 24

esxcli system hostname get
esxcli hardware cpu global get       # socket, core, thread
esxcli hardware memory get           # memoria fisica e usata

# === COSA GIRA ===
esxcli vm process list
# Il world-id serve per il kill forzato: annotalo mentalmente,
# perché è il primo strumento quando una VM non si spegne (§F3)
```

```bash
# === LE QUATTRO FAMIGLIE DI COMANDI CHE USERAI DAVVERO ===

# Rete
esxcli network nic list                    # le NIC fisiche
esxcli network vswitch standard list       # i vSwitch
esxcli network ip interface list           # le VMkernel port
esxcli network ip route ipv4 list          # il routing
esxcli network firewall ruleset list       # il firewall dell'host

# Storage
esxcli storage core device list            # i dispositivi
esxcli storage filesystem list             # i datastore montati
esxcli storage core adapter list           # gli HBA
esxcli storage nmp device list             # il multipathing

# Manutenzione
esxcli system maintenanceMode set --enable true
esxcli software vib list                   # i pacchetti installati
esxcli software profile get                # il profilo immagine

# Log
esxcli system syslog config set --loghost='udp://10.10.10.100:514'
esxcli system syslog reload
```

```
COSA REGISTRARE DA QUESTO ESERCIZIO, per l'assessment

  versione e build esatti  ► determinano quali VM hardware version
                             sono supportate, e quindi cosa
                             `virt-v2v` troverà (§migr06)
  socket / core / thread   ► la base del dimensionamento del target
                             (§migr05)
  VIB di terze parti       ► driver di vendor che NON esistono su
                             Proxmox: se ce ne sono, è un vincolo,
                             non un dettaglio
```

---

### Esercizio B2: La memoria sotto pressione

> **Analogia.** Una biblioteca con più libri che scaffali. Prima il bibliotecario nota che ci sono dieci copie identiche dello stesso libro e ne tiene una sola (**TPS**). Poi comprime i volumi che nessuno consulta, rimpicciolendoli (**compression**). Poi passa fra i lettori e chiede a ciascuno di restituire i libri che non stanno leggendo davvero (**ballooning**). Solo alla fine porta i libri in cantina, da dove recuperarli richiede una spedizione (**swap**). Il punto è l'ordine: quando arrivi allo swap, hai già perso.

```
Pressione BASSA ──────────────────────────────► Pressione ALTA

┌────────┐   ┌──────────────┐   ┌────────────┐   ┌────────┐
│  TPS   │──►│ Compression  │──►│ Ballooning │──►│  Swap  │
└────────┘   └──────────────┘   └────────────┘   └────────┘
 dedup di     pagine inattive    il guest         .vswp sul
 pagine       compresse in       pagina da sé,    datastore.
 identiche    RAM                via vmmemctl     Prestazioni
                                                  rovinate.

⚠ TPS FRA VM DIVERSE È DISATTIVATO PER DEFAULT dalla 6.0, per il
  rischio di side-channel: la deduplica riguarda solo le pagine
  della stessa VM. Chi dimensiona contando sulla deduplica
  inter-VM sta usando un numero che non esiste più da dieci anni.
```

```bash
# === OSSERVARE LA MEMORIA SU ESXi ===
esxcli hardware memory get

# `esxtop` in modalità memoria: premi `m` dopo l'avvio
esxtop
# Colonne che contano:
#   MCTLSZ   memoria reclamata dal balloon (MB). Se è > 0, l'host
#            sta già chiedendo indietro memoria ai guest
#   SWCUR    swap corrente. Se è > 0, sei oltre il punto di rottura
#   ZIP/UNZIP compressione attiva

# La stessa informazione, scriptabile
esxcli system slp stats get 2>/dev/null || true
vsish -e get /memory/comprehensive 2>/dev/null | head -20
```

```
E IN PROXMOX, dove la stessa cosa ha nomi diversi

  TPS            ──► KSM (Kernel Samepage Merging). Attivo, e con
                     lo stesso caveat di sicurezza. Si governa con
                     `ksmtuned`.
  Compression    ──► zswap / zram, non attivi per difetto
  Ballooning     ──► il device `balloon` di QEMU, `qm set <id>
                     --balloon <MB>`
  Swap           ──► lo swap del nodo, con lo stesso effetto
                     rovinoso sulle prestazioni

⚠ LA DIFFERENZA CHE CONTA NEL DIMENSIONAMENTO: su ESXi
  l'overcommit di memoria è una pratica normale e ben rodata. Su
  Proxmox funziona, ma il comportamento sotto pressione è quello
  del kernel Linux, e l'OOM killer di Linux non è gentile come il
  memory manager del VMkernel — può terminare una VM invece di
  degradarla. Il dimensionamento del tutorial migr05 tiene conto
  di questo, e riduce l'overcommit ammesso.
```

---

### Esercizio B3: Il CPU scheduler, e la metrica che tutti ignorano

```bash
# === esxtop IN MODALITÀ CPU (è la vista predefinita) ===
esxtop
# Premi `V` per filtrare solo le VM.

# La colonna che conta più di tutte:
#   %RDY    percentuale di tempo in cui una vCPU era PRONTA a
#           girare ma aspettava una CPU fisica libera
#
#   < 5%    normale
#   5-10%   contesa: da tenere d'occhio
#   > 10%   la VM è rallentata da un problema di scheduling, non
#           da un problema suo
```

```
IL CONTROSENSO CHE VALE LA PENA CAPIRE ADESSO

Una VM con 8 vCPU su un host affollato può essere PIÙ LENTA della
stessa VM con 4 vCPU. Lo scheduler deve trovare 8 core liberi
contemporaneamente per farla girare: più vCPU chiedi, più aspetti.

  ➜ È il co-scheduling, e sopravvive alla migrazione: KVM ha lo
    stesso problema, con nomi diversi. Nel tutorial migr09
    ridimensioneremo le vCPU delle VM migrate proprio per questo,
    e in molti casi la VM migrata andrà più veloce con MENO vCPU
    di quante ne avesse su VMware.

⚠ E QUESTO È UN ESEMPIO DEL PRINCIPIO GENERALE DEL CORSO: migrare
  non è copiare la configurazione. Una configurazione tarata per
  un hypervisor va ri-tarata per l'altro, e chi copia i valori
  uno a uno porta con sé anche gli errori di dimensionamento
  accumulati negli anni.
```

| Concetto | Su vSphere | Su Proxmox |
|---|---|---|
| CPU fisica / virtuale | pCPU / vCPU | core host / vCPU |
| Attesa di scheduling | `%RDY` in `esxtop` | `steal time` nel guest, `%st` in `top` |
| Risorse garantite | CPU reservation | `cpuunits`, cgroup v2 |
| Limite e peso | limit / shares | `cpulimit`, `cpuunits` |
| Compatibilità fra host | EVC mode | tipo di CPU esplicito (`--cpu`) |

---

## PART C: NETWORKING vSPHERE, E IL SUO EQUIVALENTE

> Il networking è la parte della migrazione dove gli errori si vedono subito e in modo spettacolare: una VLAN sbagliata e la VM migrata è viva ma irraggiungibile. La buona notizia è che la mappatura fra i due mondi è quasi uno a uno. La cattiva è che i default sono diversi, e i default sono ciò che nessuno controlla.

---

### Concetto C1: vSwitch, port group, VMkernel — e cosa diventano

> **Analogia.** Un vSwitch è uno switch di rete che invece di stare nel rack sta nella RAM. Le sue porte sono raggruppate per etichetta — i **port group** — come se avessi etichettato i gruppi di porte dello switch fisico "produzione", "backup", "gestione", assegnando a ciascun gruppo la sua VLAN. Le **VMkernel port** sono le prese a cui si collega l'host stesso, non le VM: è da lì che ESXi parla di management, vMotion, storage.

```
+=====================================================================+
|            NETWORKING: vSphere → Proxmox VE                          |
+=====================================================================+
| VMware                       | Proxmox VE                           |
| ============================ | ==================================== |
| Standard vSwitch (vSS)       | Linux Bridge (vmbr0, vmbr1, …)       |
| Distributed vSwitch (dvS)    | Open vSwitch, o SDN di Proxmox       |
| Port Group                   | VLAN sul bridge / porta OVS          |
| VMkernel Port                | IP sul bridge o su interfaccia VLAN  |
| vmnic (uplink)               | NIC fisica (ens18, enp3s0, …)        |
| NIC Teaming                  | Linux bonding (bond0, …)             |
| LACP                         | bond mode 4 (802.3ad)                |
| Active/Standby               | bond mode 1 (active-backup)          |
| VLAN tagging (VST)           | vlan filtering sul bridge            |
| VLAN trunk (VGT, 4095)       | bridge vlan-aware + trunk            |
| Traffic shaping · NIOC       | `tc`, oppure QoS di OVS              |
| Jumbo frames (MTU 9000)      | MTU su interfaccia e bridge          |
| NSX                          | SDN di Proxmox (zone, VNet)          |
+=====================================================================+

⚠ LA RIGA CHE COSTA PIÙ FATICA È QUELLA DEL dvSwitch. Un
  Distributed vSwitch è UN oggetto configurato una volta in
  vCenter e applicato a tutti gli host. In Proxmox non esiste un
  equivalente diretto: la configurazione di rete è per nodo, in
  `/etc/network/interfaces`, e la coerenza fra i nodi te la
  garantisci tu — con Ansible, con un file di riferimento, o con
  la SDN integrata. Lo affronteremo nel tutorial migr07.
```

---

### Esercizio C2: Creare un vSwitch, e leggerlo

```bash
# === SU esxi1 — creare la topologia del lab ===

# Un vSwitch dedicato al traffico delle VM
esxcli network vswitch standard add --vswitch-name=vSwitch1

# Jumbo frames: va impostato QUI e anche sullo switch fisico e
# sulla VMkernel port. Se manca un anello della catena, i pacchetti
# grandi spariscono senza errore — è il guasto più subdolo di
# tutto il networking virtuale.
esxcli network vswitch standard set --vswitch-name=vSwitch1 --mtu=9000

# Un uplink fisico
esxcli network vswitch standard uplink add \
  --vswitch-name=vSwitch1 --uplink-name=vmnic1

# I port group, uno per VLAN
esxcli network vswitch standard portgroup add \
  --portgroup-name=PG-Produzione --vswitch-name=vSwitch1
esxcli network vswitch standard portgroup set \
  --portgroup-name=PG-Produzione --vlan-id=20

esxcli network vswitch standard portgroup add \
  --portgroup-name=PG-Storage --vswitch-name=vSwitch1
esxcli network vswitch standard portgroup set \
  --portgroup-name=PG-Storage --vlan-id=30
```

```bash
# === LEGGERE LA CONFIGURAZIONE — è questo che ti serve migrando ===
esxcli network vswitch standard list
# Name: vSwitch1
#    Class: cswitch
#    Num Ports: 2560
#    Used Ports: 4
#    Configured Ports: 128
#    MTU: 9000
#    CDP Status: listen
#    Uplinks: vmnic1
#    Portgroups: PG-Storage, PG-Produzione

esxcli network vswitch standard portgroup list
# Name            Virtual Switch  Active Clients  VLAN ID
# --------------  --------------  --------------  -------
# PG-Produzione   vSwitch1                     0       20
# PG-Storage      vSwitch1                     0       30

# LE POLICY DI SICUREZZA DEL PORT GROUP — da guardare sempre
esxcli network vswitch standard portgroup policy security get \
  --portgroup-name=PG-Produzione
# AllowPromiscuous: false
# AllowMACAddressChange: false
# AllowForged: false
```

```
⚠ LE TRE POLICY DI SICUREZZA SONO UN VINCOLO DI MIGRAZIONE, e
  quasi nessuno le controlla prima:

   AllowPromiscuous      se è `true` da qualche parte, c'è una VM
                         che sniffa il traffico — tipicamente un
                         IDS, un packet broker o un cluster che
                         usa multicast. Su Proxmox il bridge Linux
                         si comporta diversamente, e quella VM
                         smetterà di funzionare senza dirlo.
   AllowMACAddressChange se è `true`, qualcosa cambia il proprio
                         MAC: un cluster con IP virtuale, un
                         firewall in HA, una VM con NIC bonded.
   AllowForged           se è `true`, una VM emette pacchetti con
                         MAC sorgente diverso dal proprio: quasi
                         sempre è un router, un NAT o un
                         hypervisor annidato.

  ➜ ANNOTA OGNI PORT GROUP CHE HA UN `true`. Sono le VM che
    richiederanno attenzione specifica nel tutorial migr07, e
    sono anche quelle che, se le tratti come le altre, ti fanno
    fallire il collaudo post-migrazione.
```

---

### Esercizio C3: Le policy di teaming, e i due modi bond che le sostituiscono

```
LE QUATTRO POLICY DI TEAMING DI vSPHERE

  Route based on originating virtual port   ← il default
      ogni VM è legata a un uplink in base alla porta virtuale.
      Semplice, nessun requisito sullo switch fisico.
  Route based on source MAC hash
      come sopra, ma l'hash è sul MAC del guest.
  Route based on IP hash                    ← richiede LACP
      hash su IP sorgente+destinazione. È l'unico che distribuisce
      le connessioni di UNA stessa VM su più uplink, ed è l'unico
      che pretende una configurazione anche sullo switch fisico.
  Use explicit failover order
      un uplink attivo, gli altri in attesa.

E IN PROXMOX, con il bonding di Linux:

  originating virtual port ─┐
  source MAC hash          ─┼─► bond mode 1 (active-backup)
  explicit failover        ─┘   oppure mode 2 (balance-xor)
  IP hash                   ──► bond mode 4 (802.3ad) + LACP
                                sullo switch, con xmit_hash_policy
                                layer3+4

⚠ LA TRAPPOLA È IL PASSAGGIO A LACP. Se in VMware avevi "IP hash",
  lo switch fisico ha già un port-channel configurato: il bond
  Proxmox DEVE essere mode 4, altrimenti il port-channel dello
  switch e il bond del server si contraddicono, e il risultato è
  una rete che funziona a intermittenza in modo inspiegabile.
  Il contrario è altrettanto vero: mode 4 senza LACP sullo switch
  non porta su il link.
```

```bash
# === LEGGERE IL TEAMING ESISTENTE — da riportare nell'assessment ===
esxcli network vswitch standard policy failover get --vswitch-name=vSwitch1
# Load Balancing: srcport
# Network Failure Detection: link
# Notify Switches: true
# Failback: true
# Active Adapters: vmnic1
# Standby Adapters:
# Unused Adapters:

# Il valore di `Load Balancing` è quello che determina il bond mode
# di destinazione:
#   srcport / srcmac / explicit  → bond mode 1 o 2
#   iphash                       → bond mode 4, con LACP sullo switch
```

---

### Concetto C4: I tre modi di taggare una VLAN

> **Analogia.** Una busta da spedire in un palazzo con molti uffici. **VST**: la scrivi senza destinatario interno e la portineria (il vSwitch) ci applica l'etichetta dell'ufficio giusto prima di darla al corriere. **EST**: nessuno etichetta niente, ma il corriere ritira solo da una porta che serve un ufficio solo — l'informazione sta nella porta, non nella busta. **VGT**: sei tu, dentro l'ufficio, a scrivere il destinatario interno, e la portineria non tocca nulla.

```
+===================================================================+
|                    I TRE MODI, E COSA IMPLICANO                    |
+===================================================================+
|                                                                    |
|  VST — Virtual Switch Tagging          <- il caso normale          |
|    Port Group con VLAN ID = 1..4094                                |
|    la VM manda frame SENZA tag, il vSwitch lo aggiunge             |
|    lo switch fisico riceve una porta TRUNK                         |
|      => Proxmox: bridge vlan-aware, e tag=<vlan> sulla VM          |
|                                                                    |
|  EST — External Switch Tagging                                     |
|    Port Group con VLAN ID = 0 (nessuno)                            |
|    nessuno tagga: la VLAN la decide lo switch fisico               |
|    lo switch fisico riceve una porta ACCESS                        |
|      => Proxmox: bridge normale, nessun tag. E' il caso piu        |
|         semplice, ed e' anche quello che nasconde l'informazione:  |
|         la VLAN non compare da nessuna parte nella config di       |
|         VMware, e va chiesta a chi gestisce lo switch.             |
|                                                                    |
|  VGT — Virtual Guest Tagging                                       |
|    Port Group con VLAN ID = 4095 (trunk)                           |
|    e' il GUEST a taggare: dentro la VM ci sono sotto-interfacce    |
|      => Proxmox: bridge vlan-aware con trunk, e nessun tag sulla   |
|         VM. Tipico di firewall virtuali, router e appliance.       |
|                                                                    |
+===================================================================+

⚠ IL VALORE 4095 È QUELLO DA CERCARE NELL'ASSESSMENT. Un port group
  con VLAN ID 4095 significa che dentro quella VM esiste una
  configurazione di rete che non vedi da fuori: se la migri come se
  fosse una VM normale, perde tutte le sue VLAN interne e nessun
  comando su Proxmox te lo dirà — semplicemente, metà dei suoi
  servizi non risponderà più.

⚠ E IL VALORE 0 È QUELLO PIÙ INSIDIOSO, perché sembra "nessuna
  VLAN" mentre significa "VLAN decisa altrove". Le VM su port group
  EST vanno mappate parlando con chi gestisce lo switch fisico, non
  leggendo la configurazione di vSphere.
```

```bash
# === TROVARE I TRE CASI NEL PROPRIO AMBIENTE ===
esxcli network vswitch standard portgroup list

# Name            Virtual Switch  Active Clients  VLAN ID
# --------------  --------------  --------------  -------
# PG-Produzione   vSwitch1                     3       20   <- VST
# PG-Legacy       vSwitch1                     1        0   <- EST
# PG-Firewall     vSwitch1                     1     4095   <- VGT

# La classificazione, per l'assessment
esxcli network vswitch standard portgroup list | awk 'NR>2 {
  vlan = $NF
  if (vlan == 4095)   modo = "VGT - il guest tagga, VERIFICARE"
  else if (vlan == 0) modo = "EST - VLAN sullo switch fisico"
  else                modo = "VST - normale"
  printf "%-18s VLAN %-5s %s\n", $1, vlan, modo
}'
```

---

## PART D: STORAGE vSPHERE, E IL SUO EQUIVALENTE

> Lo storage è il punto dove la migrazione consuma tempo: convertire i dischi è l'operazione più lunga di tutto il progetto, e la finestra di downtime dipende quasi solo da questo. Capire cosa c'è sotto un datastore — e quale forma prenderà dall'altra parte — è ciò che rende preventivabile una migrazione.

---

### Concetto D1: VMFS, NFS, iSCSI — cosa si porta dietro e cosa no

> **Analogia.** VMFS è un armadio condiviso da più persone, con una serratura intelligente: chiunque può aprirlo, ma quando qualcuno sta usando uno scomparto gli altri lo vedono occupato e non ci scrivono sopra. È fatto per pochi oggetti molto grandi — i dischi delle VM — e sarebbe pessimo per contenere milioni di foglietti. È esattamente il motivo per cui non esiste nulla di identico dall'altra parte: Proxmox risolve lo stesso problema in modi diversi a seconda del caso.

```
+=====================================================================+
|              STORAGE: vSphere → Proxmox VE                           |
+=====================================================================+
| VMware                       | Proxmox VE                           |
| ============================ | ==================================== |
| Datastore VMFS               | LVM / LVM-Thin / directory           |
| Datastore NFS                | storage NFS (praticamente identico)  |
| LUN iSCSI → VMFS             | LVM su iSCSI, o iSCSI diretto        |
| LUN Fibre Channel → VMFS     | LVM su LUN FC                        |
| vSAN                         | Ceph (RBD)                           |
| VMDK thick                   | raw su LVM, oppure qcow2             |
| VMDK thin                    | qcow2, oppure LVM-Thin               |
| RDM                          | passthrough del disco, o LVM         |
| Storage vMotion              | `qm move-disk` (a caldo)             |
| Snapshot (catena di delta)   | snapshot qcow2 o LVM-Thin            |
| Linked clone                 | qcow2 con backing file               |
| Storage DRS                  | NIENTE: manuale, o script            |
| VAAI                         | non serve: LVM e Ceph fanno altro    |
| SIOC                         | limiti I/O via cgroup                |
+=====================================================================+

LE TRE RIGHE CHE MERITANO ATTENZIONE

  vSAN → Ceph        è la migrazione più impegnativa del catalogo.
                     Non è una conversione: è una ricostruzione
                     dello strato di storage, con il proprio
                     dimensionamento e le proprie regole.
  Storage DRS → ∅    il bilanciamento automatico dei datastore non
                     ha equivalente. Se ci contavi, dopo la
                     migrazione lo fai a mano o con uno script.
  RDM → passthrough  funziona, ma è la voce che fa fallire più
                     migrazioni automatiche: `virt-v2v` non
                     converte un RDM (§D3).
```

---

### Esercizio D2: Esplorare un datastore, e i file di una VM

```bash
# === CREARE IL DATASTORE DEL LAB SU esxi1 ===
# Il secondo disco della VM annidata diventa VMFS.
esxcli storage core device list | grep -A2 "Display Name"

# Sostituisci <naa.xxx> con l'identificativo del secondo disco
# vmkfstools crea il filesystem; -b è la dimensione di blocco
vmkfstools -C vmfs6 -S DS-Lab /vmfs/devices/disks/<naa.xxx>:1

# Verificare
esxcli storage filesystem list
# Mount Point                                  Volume Name  Type    Size
# /vmfs/volumes/6612ab34-...                   DS-Lab       VMFS-6  200.0GB
```

```bash
# === I FILE DI UNA VM — cosa migra e cosa no ===
cd /vmfs/volumes/DS-Lab/vm-test
ls -lh

# vm-test.vmx           configurazione. NON migra: si rilegge per
#                       ricostruire la config su Proxmox
# vm-test.vmdk          descriptor (poche righe di testo)
# vm-test-flat.vmdk     i DATI veri. È questo che si converte.
# vm-test.nvram         BIOS/UEFI virtuale. Non migra.
# vm-test.vmsd          indice degli snapshot
# vm-test-000001.vmdk   un delta di snapshot ← DEVE SPARIRE PRIMA
# vmware.log            il log della VM

# Il descriptor è leggibile, e dice il formato:
cat vm-test.vmdk | grep -E 'createType|extent|ddb.adapterType'
# createType="vmfs"
# RW 41943040 VMFS "vm-test-flat.vmdk"
# ddb.adapterType = "lsilogic"
```

```
⚠ `ddb.adapterType` È UN'INFORMAZIONE CHE TI SERVIRÀ DAVVERO. Dice
  quale controller disco il guest si aspetta di trovare:

    lsilogic / lsisas1068  ► il guest ha driver LSI. Su Proxmox
                             diventerà VirtIO SCSI, e i driver
                             VirtIO vanno iniettati PRIMA del
                             primo avvio, o Windows va in
                             INACCESSIBLE_BOOT_DEVICE (§migr09)
    pvscsi                 ► driver VMware paravirtuale: stesso
                             problema, aggravato
    ide                    ► lento, ma migra senza sorprese

  ➜ È la ragione per cui il tutorial migr06 dedica un'intera
    sezione all'iniezione dei driver: non è un dettaglio di
    rifinitura, è la differenza fra una VM che si accende e una
    che non si accende.
```

---

### Esercizio D3: I tipi di VMDK, e le tre cose che bloccano una migrazione

```bash
# === IL FORMATO DEI DISCHI, VM PER VM ===
# Da eseguire dalla workstation, con PowerCLI
pwsh
```

```powershell
Connect-VIServer -Server 10.10.10.20 -User root

# Thin, thick lazy-zeroed, thick eager-zeroed: il formato decide
# quanto tempo costerà la conversione
Get-VM | Get-HardDisk |
  Select-Object Parent, Name, CapacityGB, StorageFormat, Filename |
  Format-Table -AutoSize

# Parent    Name         CapacityGB StorageFormat Filename
# ------    ----         ---------- ------------- --------
# vm-test   Hard disk 1          40 Thin          [DS-Lab] vm-test/vm-test.vmdk
```

```
LE TRE COSE CHE BLOCCANO UNA MIGRAZIONE, e vanno trovate ORA

  ① GLI SNAPSHOT
     Una VM con snapshot attivi non si migra: la catena di delta va
     consolidata prima. Su una VM con snapshot vecchi di mesi, il
     consolidamento può richiedere ore e spazio che non hai.
     ➜ Vanno trovati adesso, non la notte del cutover.

  ② GLI RDM (Raw Device Mapping)
     Un disco che punta direttamente a una LUN, senza VMFS in
     mezzo. `virt-v2v` non lo converte. Va gestito a parte:
     presentando la stessa LUN a Proxmox, o copiando i dati a
     livello applicativo.
     ➜ Tipico di: cluster Microsoft, database con requisiti
       particolari, appliance di terze parti.

  ③ IL PASSTHROUGH (GPU, USB, seriali)
     Un dispositivo fisico assegnato alla VM. Proxmox lo supporta,
     ma la configurazione è diversa e l'hardware deve esistere sul
     nodo di destinazione.
     ➜ Se una VM ha una chiave di licenza USB, quella chiave deve
       essere fisicamente sul nodo Proxmox giusto, e la VM non
       potrà più migrare liberamente nel cluster.
```

```powershell
# === TROVARLE TUTTE E TRE, IN UN COLPO SOLO ===

# ① Snapshot
Get-VM | Get-Snapshot |
  Select-Object @{N='VM';E={$_.VM.Name}}, Name, Created,
                @{N='SizeGB';E={[math]::Round($_.SizeGB,2)}}

# ② RDM — il DiskType lo dichiara
Get-VM | Get-HardDisk |
  Where-Object { $_.DiskType -like '*Raw*' } |
  Select-Object Parent, Name, DiskType, ScsiCanonicalName

# ③ Passthrough — i device PCI e USB assegnati
Get-VM | ForEach-Object {
  $vm = $_.Name
  $_.ExtensionData.Config.Hardware.Device |
    Where-Object { $_ -is [VMware.Vim.VirtualPCIPassthrough] -or
                   $_ -is [VMware.Vim.VirtualUSB] } |
    Select-Object @{N='VM';E={$vm}},
                  @{N='Tipo';E={$_.GetType().Name}}
}
```

⚠ Se questi tre comandi non restituiscono nulla, non significa che l'ambiente sia pulito: significa che *il lab* è pulito. In un ambiente reale restituiscono quasi sempre qualcosa, e ciò che restituiscono determina quali VM finiranno nell'ultima wave della migrazione, quella delle eccezioni.

---

## PART E: L'INVENTARIO CHE ALIMENTA LA MIGRAZIONE

> Questa è la parte del tutorial che produce il risultato vero. Tutto il resto serve a capire cosa stai guardando; questo produce i file su cui lavorerai per le prossime diciotto lezioni. Un assessment fatto male non si nota subito: si nota alla terza wave, quando scopri che il dimensionamento era sbagliato e mezzo cluster è da rifare.

---

### Esercizio E1: Connessione e inventario degli host

```powershell
# === ~/migrazione-lab/script/01-inventario-host.ps1 ===
# Lo script è scritto per essere rieseguibile: sovrascrive i CSV
# ogni volta, così un secondo passaggio a distanza di settimane
# produce un confronto invece di un duplicato.

param(
  [string]$Server   = '10.10.10.20',
  [string]$Utente   = 'root',
  [string]$Destinazione = "$HOME/migrazione-lab/assessment"
)

Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false | Out-Null
Connect-VIServer -Server $Server -User $Utente

New-Item -ItemType Directory -Force -Path $Destinazione | Out-Null

# === HOST ===
Get-VMHost | Select-Object Name,
    @{N='Version';E={$_.Version}},
    @{N='Build';E={$_.Build}},
    @{N='Model';E={$_.Model}},
    @{N='CPUCores';E={$_.ExtensionData.Hardware.CpuInfo.NumCpuCores}},
    @{N='CPUThreads';E={$_.ExtensionData.Hardware.CpuInfo.NumCpuThreads}},
    @{N='MemoryGB';E={[math]::Round($_.MemoryTotalGB,2)}},
    @{N='MemoryUsedGB';E={[math]::Round($_.MemoryUsageGB,2)}} |
  Export-Csv -Path "$Destinazione/host-inventory.csv" -NoTypeInformation

Write-Host "[OK] host-inventory.csv"
```

```
PERCHÉ OGNI COLONNA È LÌ

  Version, Build   la matrice di compatibilità di virt-v2v dipende
                   da questi due, non dalla versione "commerciale"
  Model            il modello dell'hardware: serve a decidere se i
                   nodi si riusano per Proxmox o si sostituiscono
  CPUCores         la base del dimensionamento. ⚠ CORE, non
                   THREAD: dimensionare sui thread è l'errore che
                   porta a un cluster sottodimensionato del 40%
  MemoryTotalGB    il totale fisico
  MemoryUsedGB     l'uso REALE, che è quasi sempre molto sotto il
                   totale allocato alle VM — ed è la differenza fra
                   i due a dirti quanto overcommit c'era davvero
```

---

### Esercizio E2: VM, dischi, snapshot, rete, storage

```powershell
# === ~/migrazione-lab/script/02-inventario-vm.ps1 ===

$Destinazione = "$HOME/migrazione-lab/assessment"

# === VM ===
Get-VM | Select-Object Name,
    @{N='PowerState';E={$_.PowerState}},
    @{N='GuestOS';E={$_.ExtensionData.Config.GuestFullName}},
    @{N='NumCPU';E={$_.NumCpu}},
    @{N='MemoryGB';E={$_.MemoryGB}},
    @{N='HWVersion';E={$_.HardwareVersion}},
    @{N='VMHost';E={$_.VMHost.Name}},
    @{N='ToolsStatus';E={$_.ExtensionData.Guest.ToolsStatus}},
    @{N='IPAddress';E={$_.Guest.IPAddress -join ','}},
    @{N='UsedSpaceGB';E={[math]::Round($_.UsedSpaceGB,2)}},
    @{N='ProvisionedSpaceGB';E={[math]::Round($_.ProvisionedSpaceGB,2)}},
    @{N='Firmware';E={$_.ExtensionData.Config.Firmware}},
    @{N='UUID';E={$_.ExtensionData.Config.Uuid}} |
  Export-Csv -Path "$Destinazione/vm-inventory.csv" -NoTypeInformation

# === DISCHI ===
Get-VM | ForEach-Object {
    $nomeVm = $_.Name
    $_ | Get-HardDisk | Select-Object `
        @{N='VM';E={$nomeVm}},
        @{N='CapacityGB';E={[math]::Round($_.CapacityGB,2)}},
        @{N='StorageFormat';E={$_.StorageFormat}},
        @{N='Filename';E={$_.Filename}},
        @{N='Datastore';E={$_.Filename -replace '\[([^\]]+)\].*','$1'}}
} | Export-Csv -Path "$Destinazione/vm-disks.csv" -NoTypeInformation

# === SNAPSHOT ===
Get-VM | Get-Snapshot | Select-Object `
    @{N='VM';E={$_.VM.Name}}, Name, Created,
    @{N='SizeGB';E={[math]::Round($_.SizeGB,2)}} |
  Export-Csv -Path "$Destinazione/vm-snapshots.csv" -NoTypeInformation

# === PORT GROUP ===
Get-VMHost | ForEach-Object {
    $host_ = $_.Name
    $_ | Get-VirtualPortGroup | Select-Object `
        @{N='Host';E={$host_}}, Name, VLanId, VirtualSwitchName
} | Export-Csv -Path "$Destinazione/portgroups.csv" -NoTypeInformation

# === DATASTORE ===
Get-Datastore | Select-Object Name, Type,
    @{N='CapacityGB';E={[math]::Round($_.CapacityGB,2)}},
    @{N='FreeSpaceGB';E={[math]::Round($_.FreeSpaceGB,2)}},
    @{N='PercentUsed';E={
        [math]::Round(($_.CapacityGB - $_.FreeSpaceGB) / $_.CapacityGB * 100, 1)
    }},
    @{N='VMFSVersion';E={$_.FileSystemVersion}} |
  Export-Csv -Path "$Destinazione/datastores.csv" -NoTypeInformation

Write-Host "[OK] sei file prodotti in $Destinazione"
```

```
LE TRE COLONNE CHE DECIDONO LA STRATEGIA DI MIGRAZIONE

  ProvisionedSpaceGB vs UsedSpaceGB
      La differenza è il thin provisioning. Un parco con 40 TB
      provisionati e 12 TB usati non richiede 40 TB di destinazione
      — ma richiede una decisione consapevole su quanto
      overprovisioning replicare (§migr05).

  HWVersion
      La VM hardware version. Le versioni molto vecchie (< 9)
      indicano VM che nessuno ha toccato da anni: spesso sono
      quelle senza owner, e sono le candidate migliori per essere
      spente invece che migrate.

  ToolsStatus
      `toolsNotInstalled` su una VM in produzione significa che non
      hai il quiescing per i backup, non hai l'IP dal guest, e
      probabilmente non hai nemmeno il contatto di chi la gestisce.
```

---

### Esercizio E3: Esportare permessi e ruoli

I permessi sono la voce dell'assessment che viene dimenticata più spesso, e ce se ne accorge il primo lunedì dopo il cutover: le VM funzionano, e nessuno riesce ad accedervi.

```powershell
# === ~/migrazione-lab/script/03-permessi.ps1 ===
$Destinazione = "$HOME/migrazione-lab/assessment"

# I ruoli definiti, quelli personalizzati compresi
Get-VIRole |
  Select-Object Name,
    @{N='IsSystem';E={$_.IsSystem}},
    @{N='NumPrivilegi';E={$_.PrivilegeList.Count}},
    @{N='Privilegi';E={$_.PrivilegeList -join ';'}} |
  Export-Csv -Path "$Destinazione/vsphere-roles.csv" -NoTypeInformation

# Chi può fare cosa, e su quale oggetto
Get-VIPermission |
  Select-Object @{N='Entity';E={$_.Entity.Name}},
    @{N='EntityType';E={$_.Entity.GetType().Name}},
    @{N='Principal';E={$_.Principal}},
    @{N='Role';E={$_.Role}},
    @{N='Propagate';E={$_.Propagate}},
    @{N='IsGroup';E={$_.IsGroup}} |
  Export-Csv -Path "$Destinazione/vsphere-permissions.csv" -NoTypeInformation

Write-Host "[OK] ruoli e permessi esportati"
```

```
COSA NON SI TRASFERISCE, E VA RICOSTRUITO A MANO

  IL MODELLO È DIVERSO, non solo la sintassi:

    vSphere                       Proxmox VE
    --------------------------    -------------------------------
    Permission = utente + ruolo   ACL = percorso + utente + ruolo
      + oggetto + propagate
    gerarchia dell'inventario     gerarchia di percorsi (/vms/100,
      (datacenter -> cluster        /storage/nfs, /nodes/pve1)
       -> host -> VM)
    ~300 privilegi granulari      ~40 privilegi
    ruoli di sistema fissi        predefiniti + personalizzati
    SSO / PSC                     realm: pam, pve, LDAP, AD, OIDC

  ➜ LA CONSEGUENZA PRATICA: un ruolo vSphere con dodici privilegi
    scelti finemente spesso non ha un equivalente esatto, e va
    approssimato. L'approssimazione va fatta VERSO IL BASSO — meno
    privilegi, non di più — e verificata con chi usa quel ruolo.

⚠ E UN CONTROLLO CHE VALE LA PENA FARE ADESSO: quante identità
  hanno il ruolo Administrator? Se la risposta è "più di tre", la
  migrazione è l'occasione per ridurle, ed è una delle poche cose
  che si guadagnano davvero rifacendo un impianto da capo.
```

```bash
# La domanda, su una riga
awk -F',' 'NR>1 && $4 ~ /Admin/ {print $3}' \
  ~/migrazione-lab/assessment/vsphere-permissions.csv | sort -u | wc -l
```

---

### Esercizio E4: Leggere l'inventario come un piano

```bash
# === DALLA WORKSTATION — le domande a cui i CSV devono rispondere ===
cd ~/migrazione-lab/assessment

# Quante VM, e quanto spazio serve davvero?
awk -F',' 'NR>1 {usato+=$10; prov+=$11} END {
  printf "VM: %d\nUsato: %.1f GB\nProvisionato: %.1f GB\nRapporto: %.2fx\n",
         NR-1, usato, prov, prov/usato
}' vm-inventory.csv

# Quali VM hanno snapshot? (queste bloccano la migrazione)
wc -l < vm-snapshots.csv | xargs -I{} echo "Righe snapshot (header incluso): {}"

# Quante VLAN distinte? (questo è l'input del tutorial migr07)
awk -F',' 'NR>1 {print $3}' portgroups.csv | sort -u
```

```
LA DOMANDA CHE CHIUDE LA FASE 1

  "Se domani dovessi migrare, cosa NON so ancora?"

  Le risposte tipiche, e dove si affrontano:
   · non so quali VM dipendono da quali          → migr05
   · non so quanto downtime è ammesso per ognuna → migr05
   · non so se il target regge il carico         → migr05
   · non so come convertire i dischi             → migr06, migr08
   · non so come rimappare le VLAN               → migr07
   · non so cosa fare degli RDM                  → migr08
   · non so chi chiamare se va storto            → migr16, migr18

⚠ SE A QUESTA DOMANDA RISPONDI "niente", non hai finito
  l'assessment: hai finito di guardare l'inventario. Sono due cose
  diverse, e la seconda è la parte facile.
```

---

## PART F: MODI DI ROTTURA E RECUPERO

> Ogni tutorial di questo corso finisce mostrando come si rompe ciò che hai appena costruito. Non per completezza: perché il giorno in cui si rompe davvero, sei sotto pressione e non hai tempo di imparare. Questi tre guasti sono quelli che incontrerai su ESXi durante una migrazione reale.

---

### Esercizio F1: L'host che non risponde più alla web

```bash
# SINTOMO: https://10.10.10.20/ui non carica, ma l'host risponde
# al ping e le VM continuano a girare.
#
# CAUSA quasi sempre: `hostd` è morto o bloccato. È il demone che
# serve l'API e l'interfaccia: le VM non dipendono da lui, per
# questo continuano a funzionare.

ssh root@10.10.10.20

# Verificare lo stato
/etc/init.d/hostd status

# Riavviare SOLO hostd — non tocca le VM in esecuzione
/etc/init.d/hostd restart

# Se non basta, riavviare tutti gli agenti di gestione
services.sh restart

# ⚠ `services.sh restart` NON riavvia le VM, ma interrompe
#   temporaneamente vMotion e le operazioni in corso. Non farlo
#   durante una migrazione attiva.

# Dove guardare per capire cosa è successo
tail -100 /var/log/hostd.log
tail -50 /var/log/vmkernel.log
```

---

### Esercizio F2: Il datastore che non si monta

```bash
# SINTOMO: dopo un riavvio, un datastore VMFS non compare.

# 1. Il dispositivo è visto?
esxcli storage core device list | grep -i "naa\."

# 2. Il filesystem è riconosciuto?
esxcli storage filesystem list
esxcli storage vmfs extent list

# 3. Ci sono snapshot di LUN non risolti? (causa frequente su SAN)
esxcli storage vmfs snapshot list
# Se elenca qualcosa, il VMFS è visto come una COPIA e per
# sicurezza non viene montato: ESXi non sa se è l'originale o un
# clone, e montarlo entrambi corromperebbe i dati.

# 4. Montare deliberatamente, dopo aver capito cosa si sta montando
esxcli storage vmfs snapshot mount --volume-label=DS-Lab

# ⚠ `--persist` rende il mount permanente e riscrive la signature.
#   Se il volume È davvero un clone e l'originale è ancora in uso,
#   questa operazione è distruttiva. Non usarla senza sapere quale
#   dei due volumi hai davanti.
```

---

### Esercizio F3: La VM che non si spegne

```bash
# SINTOMO: `Power Off` dall'interfaccia non fa niente, la VM resta
# accesa e non risponde. Succede quando il processo vmx è bloccato
# su una I/O che non ritorna — tipicamente storage.

# 1. Trovare il world-id
esxcli vm process list
# vm-test
#    World ID: 2098456
#    Process ID: 0
#    VMX Cartel ID: 2098455
#    UUID: 42 1a ...
#    Display Name: vm-test
#    Config File: /vmfs/volumes/DS-Lab/vm-test/vm-test.vmx

# 2. Terminare, con la gradualità giusta
esxcli vm process kill --type=soft  --world-id=2098456   # SIGTERM
esxcli vm process kill --type=hard  --world-id=2098456   # SIGKILL
esxcli vm process kill --type=force --world-id=2098456   # ultima risorsa

# ⚠ L'ORDINE NON È DECORATIVO. `soft` lascia al guest la
#   possibilità di chiudere pulitamente: su un database, la
#   differenza fra `soft` e `force` è la differenza fra un riavvio
#   e un recovery. Si sale di livello solo dopo aver aspettato.

# 3. Se nemmeno `force` funziona, il problema non è la VM: è lo
#    storage sottostante che non risponde. Guardare lì.
tail -f /var/log/vmkernel.log | grep -i "scsi\|nmp\|path"
```

---

## Pulizia del laboratorio

```bash
# === SU pve1 — solo se NON prosegui subito con migr02 ===
# `esxi1` serve ancora nei tutorial migr05, migr06, migr07 e migr08
# come ambiente sorgente: conviene fermarla, non distruggerla.

qm stop 200
qm set 200 --onboot 0

# Distruzione definitiva — solo a corso finito
# qm destroy 200 --purge

# ⚠ NON CANCELLARE ~/migrazione-lab/assessment/: quegli otto CSV sono
#   l'input di tutti i tutorial successivi. Se li perdi, il
#   tutorial migr05 non ha su cosa lavorare.
echo "[OK] lab sospeso; assessment conservato in ~/migrazione-lab"
```

---

## Riepilogo concettuale

```
FONDAMENTI VMWARE — Mappa dei concetti

L'ARCHITETTURA
├── tre componenti: ESXi (i musicisti), vCenter (il direttore),
│     il client (lo spartito)
├── ESXi → un nodo Proxmox; il client → l'interfaccia di qualunque
│     nodo; vCenter → NIENTE, e questo è il cambio più grande
├── il VMkernel non è Linux: niente apt, niente agenti arbitrari,
│     estensioni solo via VIB firmati
└── un nodo Proxmox È una Debian: è il vantaggio più immediato e
      insieme il nuovo modo di rompere le cose

LA MEMORIA E LA CPU
├── TPS → compressione → ballooning → swap: quando arrivi allo
│     swap hai già perso, e TPS inter-VM è spento dal 2015
├── in Proxmox: KSM, balloon di QEMU, swap del nodo — con l'OOM
│     killer di Linux che è meno gentile del VMkernel
├── %RDY sopra il 10% significa che la VM aspetta la CPU, non che
│     ha bisogno di più vCPU
└── più vCPU può voler dire più lenta: vale su ESXi e su KVM

IL NETWORKING
├── vSwitch → Linux Bridge · port group → VLAN sul bridge ·
│     VMkernel port → IP sul bridge
├── dvSwitch → nessun equivalente diretto: la coerenza fra nodi la
│     garantisci tu, con Ansible o con la SDN
├── le tre policy di sicurezza (promiscuous, MAC change, forged)
│     identificano le VM che richiederanno attenzione
├── teaming "IP hash" ⇒ bond mode 4 + LACP sullo switch: sbagliare
│     questo abbinamento dà una rete intermittente
└── VLAN: VST è il caso normale, EST nasconde la VLAN sullo switch
      fisico, VGT (4095) significa che tagga il guest

LO STORAGE
├── VMFS → LVM/LVM-Thin/directory · NFS → NFS · vSAN → Ceph
├── il file che si converte è il `-flat.vmdk`, non il descriptor
├── `ddb.adapterType` dice quali driver il guest si aspetta, ed è
│     la ragione per cui i driver VirtIO vanno iniettati prima
└── Storage DRS non ha equivalente: dopo, si bilancia a mano

CIÒ CHE BLOCCA UNA MIGRAZIONE, e va trovato subito
├── snapshot attivi: da consolidare prima, e può volerci ore
├── RDM: virt-v2v non li converte, vanno gestiti a parte
└── passthrough (GPU, USB, seriali): l'hardware deve esistere sul
      nodo giusto, e quella VM non migrerà più liberamente

L'ASSESSMENT
├── otto CSV: host, VM, dischi, snapshot, port group, datastore,
│     ruoli e permessi
├── dimensionare sui CORE, non sui thread
├── provisionato contro usato: la differenza è la decisione
│     sull'overprovisioning da replicare
└── la domanda che chiude la fase: "cosa NON so ancora?"
```

---

## Checklist di competenze

**Ambiente e fondamenti**

- [ ] Hai un ESXi annidato funzionante, e sai perché servono `-cpu host`, `vmxnet3` e `pvscsi`
- [ ] Sai quali componenti vSphere hanno un equivalente Proxmox e quale non ce l'ha
- [ ] Sai spiegare perché ESXi non è Linux, e cosa cambia dopo la migrazione
- [ ] Sai ricostruire il cambio di licensing post-Broadcom senza confondere listino e preventivo

**Operatività su ESXi**

- [ ] Ricavi versione, build, socket, core e thread di un host con `esxcli`
- [ ] Sai leggere `%RDY` e sai perché più vCPU può voler dire più lenta
- [ ] Conosci l'ordine TPS → compressione → ballooning → swap, e cosa significa arrivare in fondo
- [ ] Sai riavviare `hostd` senza toccare le VM in esecuzione

**Rete e storage**

- [ ] Crei un vSwitch con port group e VLAN, e ne rileggi la configurazione
- [ ] Sai quale bond mode corrisponde a ciascuna policy di teaming
- [ ] Sai perché le tre policy di sicurezza del port group sono un vincolo di migrazione
- [ ] Distingui descriptor e `-flat.vmdk`, e sai quale dei due si converte
- [ ] Sai leggere `ddb.adapterType` e dedurne il lavoro sui driver

**Assessment**

- [ ] Produci gli otto CSV con PowerCLI, e sai perché ogni colonna è lì
- [ ] Sai perché un ruolo vSphere spesso non ha un equivalente esatto
- [ ] Trovi snapshot, RDM e passthrough con tre comandi
- [ ] Dimensioni sui core e non sui thread
- [ ] Sai dire, dopo l'assessment, che cosa non sai ancora

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| ESXi annidato senza `-cpu host` | L'installer si ferma su un errore di CPU incomprensibile | `--cpu host`, sempre, per l'annidato |
| Scheda `virtio` sulla VM ESXi | ESXi 8 non ha il driver: nessuna rete, nessuna spiegazione | `vmxnet3` o `e1000e` |
| Dimensionare sui thread invece che sui core | Cluster di destinazione sottodimensionato di circa il 40% | `NumCpuCores`, mai `NumCpuThreads` |
| Copiare le vCPU uno a uno dalla VM sorgente | Si eredita un errore di dimensionamento vecchio di anni | Ridimensionare sulla base di `%RDY` e dell'uso reale |
| Migrare una VM con snapshot attivi | La conversione fallisce, o converte uno stato incoerente | Consolidare prima, e mettere in conto le ore che serve |
| Scoprire gli RDM durante il cutover | `virt-v2v` non li converte: la VM resta indietro | Cercarli nell'assessment, e pianificarli a parte |
| Ignorare le policy di sicurezza del port group | Le VM che sniffano o cambiano MAC smettono di funzionare in silenzio | Annotare ogni `true` e trattarlo come un caso speciale |
| Bond mode 1 dove c'era "IP hash" | Lo switch ha un port-channel: la rete funziona a intermittenza | Mode 4 con LACP, allineato allo switch |
| Convertire il descriptor invece del `-flat` | Si converte un file di poche righe e si perdono i dati | Il `-flat.vmdk` è il disco |
| Assumere che i tempi del lab valgano in produzione | La virtualizzazione annidata costa il 10-15% | Misurare sul target reale, e dirlo quando si riporta |
| `force` come primo tentativo di spegnimento | Su un database è la differenza fra riavvio e recovery | `soft`, poi `hard`, poi `force` |
| Montare un VMFS snapshot con `--persist` senza verificare | Se è un clone e l'originale è in uso, è distruttivo | Capire quale volume si ha davanti, prima |

---

## Troubleshooting rapido

**L'installer ESXi si ferma con un errore sulla CPU**
- Causa: CPU emulata generica invece di quella dell'host
- Fix: `qm set 200 --cpu host`, e verificare che nested sia attiva

**ESXi installato, ma nessuna interfaccia di rete rilevata**
- Causa: scheda `virtio`, il cui driver non esiste in ESXi 8
- Fix: `qm set 200 --net0 vmxnet3,bridge=vmbr0`

**L'installer non trova alcun disco**
- Causa: controller `virtio-scsi`, non riconosciuto
- Fix: `--scsihw pvscsi`

**Le VM dentro ESXi annidato non si accendono**
- Causa: virtualizzazione annidata non attiva sull'host Proxmox
- Fix: `kvm_intel nested=1` (o `kvm_amd`), ricaricare il modulo, riavviare

**L'interfaccia web di ESXi non risponde, ma le VM girano**
- Causa: `hostd` bloccato
- Fix: `/etc/init.d/hostd restart`; se non basta, `services.sh restart` — mai durante una migrazione

**`Connect-VIServer` fallisce per il certificato**
- Causa: certificato autofirmato del lab
- Fix: `Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false`

**Un datastore VMFS non compare dopo un riavvio**
- Causa: riconosciuto come snapshot di LUN, quindi non montato per sicurezza
- Fix: `esxcli storage vmfs snapshot list`, capire quale volume è, poi montare deliberatamente

**Una VM non si spegne in alcun modo**
- Causa: `vmx` bloccato su una I/O che non ritorna
- Fix: `esxcli vm process kill` in ordine soft → hard → force; se resiste, il problema è lo storage

**I jumbo frame non funzionano ma l'MTU è 9000**
- Causa: un anello della catena non è configurato (switch fisico, vSwitch, VMkernel port)
- Fix: `vmkping -d -s 8972 <destinazione>`; se fallisce, risalire la catena elemento per elemento

---

## Prossimi passi

| Tutorial | Collegamento con questo |
|---|---|
| `tutorial_migr02_fondamenti_proxmox_lab.md` | L'altra metà del confronto: i tre nodi Proxmox, e ogni concetto di qui che trova il suo posto |
| `tutorial_migr05_assessment_pianificazione_lab.md` | Consuma gli otto CSV prodotti qui e li trasforma in un piano a wave |
| `tutorial_migr06_strategie_migrazione_lab.md` | `virt-v2v`, l'iniezione dei driver VirtIO, e il perché di `ddb.adapterType` |
| `tutorial_migr07_migrazione_networking_lab.md` | La mappatura vSwitch → bridge, con le policy di sicurezza trovate qui |
| `tutorial_migr08_migrazione_storage_lab.md` | La conversione dei `-flat.vmdk`, e cosa fare degli RDM |

---

## Risorse di riferimento

**Documentazione primaria:** [VMware vSphere 8.0 Documentation](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere.html) — il riferimento su `esxcli`, VMFS e le policy di rete · [PowerCLI Reference](https://developer.broadcom.com/powercli) per i cmdlet usati nell'assessment · [Proxmox VE Administration Guide](https://pve.proxmox.com/pve-docs/pve-admin-guide.html) per l'altra metà di ogni mappatura

**Nel dominio:** `01-FONDAMENTI-VMWARE/architettura-vsphere-esxi.md` per il dettaglio su vCenter, permessi e hardware version · `01-FONDAMENTI-VMWARE/vmware-networking-storage.md` per dvSwitch, vSAN, multipathing e le tabelle di mappatura complete · `00-GLOSSARIO.md` per il vocabolario VMware↔Proxmox

**Da leggere prima della Fase 2:** `00-SYLLABUS.md` §5, la mappa delle dipendenze fra moduli — dice quali tutorial presuppongono questo, e in che ordine conviene affrontarli

---

> **Nota sulle versioni.** Questo lab è scritto per ESXi 8.0 U3 annidato su Proxmox VE 8.x, PowerCLI 13.x su PowerShell 7. I parametri di `qm create` sono verificati su CPU Intel di decima generazione e successive: su hardware diverso, e in particolare su AMD, la compatibilità dell'ESXi annidato va controllata sulla documentazione della propria versione prima di dare per scontato che l'installer parta. I comandi `esxcli` e i cmdlet PowerCLI sono quelli documentati per la 8.0; su ESXi 7.x alcuni namespace hanno percorsi diversi.

> **Fine del Tutorial migr01 — Fondamenti VMware**
>
> Prossimo tutorial: `tutorial_migr02_fondamenti_proxmox_lab.md`
