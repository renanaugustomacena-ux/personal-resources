# Migrazione di Windows Server VM da VMware a Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 09.4 (chiude la sequenza scenari specifici, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 06.1-06.3 (strategie cold/warm/live cutover); modulo 08.1 (`qemu-img convert` per VMDK→qcow2/raw); modulo 07.1 (DNS cutover); modulo 09.2-09.3 (DB e high-I/O — utili per server applicativi Windows che ospitano SQL Server o IIS ad alto carico); fluenza PowerShell + dcdiag/repadmin per i Domain Controller; familiarita con BSOD codes (in particolare INACCESSIBLE_BOOT_DEVICE 0x7B).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. preparare una VM Windows Server (2012 R2, 2016, 2019, 2022, 2025) **prima** della migrazione: installare i driver VirtIO dal `virtio-win.iso` (vioscsi, viostor, NetKVM, balloon, vioserial, qxl), configurare `Start = 0` (Boot) per `vioscsi`/`viostor`, validare che il driver disco sia caricato anche in modalita Safe Boot;
> 2. eseguire la **conversione del disco** VMDK → qcow2 (snapshot, thin) o raw (perf max) con `qemu-img convert -p -W -O qcow2/raw` partendo da snapshot consolidato; importare il disco con `qm importdisk` o `qm set --scsiN /path/to/file`;
> 3. configurare la VM Proxmox per Windows: BIOS UEFI vs SeaBIOS (preservare il match con la sorgente), `--scsihw virtio-scsi-single`, `--cpu host`, `--ostype win10/win11/wXXr2`, machine type `pc-q35-X.Y` (Q35 raccomandato per UEFI), TPM 2.0 emulato per Server 2022+ con Secure Boot;
> 4. transizionare la **rete da VMXNET3 → VirtIO Net**: o pre-installare il driver e0 (e1000) come fallback transitorio, o installare NetKVM lato VMware prima dello shutdown; riapplicare configurazione IP statica via `netsh interface ipv4 set address` e re-importare regole firewall;
> 5. installare e configurare il **QEMU Guest Agent** (`qemu-ga.msi` dalla ISO virtio-win) sostituendo i VMware Tools; abilitare il canale `--agent enabled=1` lato Proxmox; validare con `qm guest cmd <VMID> ping`;
> 6. gestire correttamente la migrazione di **Domain Controller Active Directory**: trasferire ruoli FSMO al DC ridondante prima del cutover, eseguire `dcdiag /v` post-migrazione, verificare `repadmin /replsummary` e la replica con tutti i partner, validare risoluzione DNS e Kerberos; *non* applicare snapshot ad un DC migrato (tombstone reanimation rischio gravissimo);
> 7. risolvere il problema di **licensing e attivazione**: KMS rebind dopo cambio hypervisor (riattivare via `slmgr /ato`), conversione AVMA → KMS quando necessario, gestione dell'attivazione hardware-based (hash CPU+motherboard cambia → necessaria riattivazione);
> 8. applicare le **ottimizzazioni post-migrazione**: disabilitare ballooning per server critici (DC, SQL Server, Exchange), abilitare TRIM/discard, RSS sulla NIC VirtIO, piano energetico High Performance, sync time tramite NTP esterno per il PDC emulator (NON via QEMU host-time).
> **Tempo stimato:** lettura 90-120 min · lab 480-720 min (per migrare un membro server completo + un DC con replica)
> **Livello:** competent → proficient (Dreyfus 3 → 4); requisiti elevati su AD/DNS interno
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Windows Server 2012 R2 (EOS 2023-10), 2016 (Mainstream 2022-01, ESU fino 2027-01), 2019 (Mainstream 2024-01, Extended fino 2029-01), 2022 (Mainstream 2026-10, Extended fino 2031-10), 2025 (GA 2024-11, Mainstream fino 2029-10); virtio-win 0.1.262+ (ottobre 2024) e 0.1.266 (febbraio 2025); QEMU Guest Agent 9.x; Proxmox VE 8.x; QEMU 8.x → 10.x.

## Mappa concettuale

```
+============================================================+
|     Windows Server: pipeline di migrazione a Proxmox       |
+============================================================+
|                                                            |
|   PRE-MIGRAZIONE (sul lato VMware, VM accesa)              |
|                                                            |
|   1. Inventario: OS version, controller (PVSCSI/LSI),      |
|      NIC (VMXNET3/e1000), disk size, ruoli (AD/DNS/...)    |
|   2. Snapshot quiesced (con memoria) come safety net       |
|   3. Installa virtio-win drivers (NON cambia hardware!)    |
|      vioscsi, viostor, NetKVM, balloon, vioserial, qxl     |
|   4. Imposta Start=0 nel registro per vioscsi/viostor      |
|   5. Disinstalla VMware Tools                              |
|   6. (Per DC) trasferisci FSMO a un altro DC               |
|   7. Shutdown ordinato                                     |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   CONVERSIONE & IMPORT                                     |
|                                                            |
|   8. Esporta VMDK (ovftool / scp dal datastore)            |
|   9. qemu-img convert -p -W -O qcow2|raw input.vmdk dest   |
|  10. qm create <VMID> --ostype winXX --scsihw virtio-scsi- |
|      single --cpu host --machine pc-q35-X.Y --bios ovmf    |
|      (per UEFI) o seabios (per BIOS legacy)                |
|  11. qm importdisk (o qm set --scsiN /path)                |
|  12. Configura ordine boot: --boot order=scsi0             |
|  13. (UEFI) qm set --efidisk0 storage:0,efitype=4m,...     |
|  14. (Server 2022+ Secure Boot) qm set --tpmstate0 ...     |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   PRIMO BOOT SU PROXMOX                                    |
|                                                            |
|  15. Avvio: il guest deve riconoscere il disco virtio-scsi |
|      Se BSOD 0x7B INACCESSIBLE_BOOT_DEVICE → driver vioscsi|
|      non era pre-installato. Recovery: boot da virtio-win  |
|      ISO, "Repair → Driver" oppure offline registry edit.  |
|  16. Windows installa il driver NetKVM (NIC nuova)         |
|  17. Reapply IP, DNS, gateway: netsh interface ipv4 ...    |
|  18. Test connettivita, RDP, AD trust                      |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   POST-MIGRAZIONE                                          |
|                                                            |
|  19. Installa QEMU Guest Agent (qemu-ga.msi)               |
|      qm set --agent enabled=1                              |
|  20. (DC) dcdiag /v + repadmin /replsummary all            |
|  21. Riattivazione licenza: slmgr /ato (KMS)               |
|      o slmgr /ipk + /ato per cambio key                    |
|  22. Disabilita ballooning per critici: --balloon 0        |
|  23. Abilita TRIM: --discard=on; Defrag schedulato OFF     |
|  24. NIC: RSS on, RSC off in alcuni casi (vedi callout)    |
|  25. Power plan = High Performance                         |
|  26. NTP esterno per PDC; disabilita time-sync host        |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Windows non sopravvive a un cambio di hardware del controller di boot senza preparazione.** Linux ha un kernel modulare con initrd dinamico; Windows ha un boot driver "incollato" che si carica all'inizio. Senza `vioscsi` pre-installato e con `Start=0`, la VM non vede il disco e si pianta su 0x7B. Niente magie, niente eccezioni: il driver va installato *prima* dello shutdown.
2. **VMware Tools va disinstallato, ma con cautela.** Lasciare i driver VMware residui (vmxnet3, pvscsi, vmci, vsock) puo causare conflitti, BSOD intermittenti o eventi nel log Windows. Disinstallazione pulita: stop dei servizi → uninstall via setup → `pnputil /enum-drivers` per identificare residui → `pnputil /delete-driver oemNN.inf /uninstall`.
3. **I Domain Controller sono speciali, e snapshot su DC e tossico.** Mai applicare uno snapshot pre-migrazione su un DC dopo la migrazione (tombstone reanimation, lingering object): la replica AD ha invarianti di tempo (USN journal, InvocationID) che lo snapshot non rispetta. Il rollback per un DC e: spegnere, demoteare il DC migrato, ri-promote da zero o ri-replicare da un altro DC.
4. **VirtIO Net non equivale a VMXNET3 in tutti i workload.** VMXNET3 ha alcune feature (LRO/TSO ottimizzato per certe versioni di ESXi) che VirtIO Net implementa diversamente. Per server applicativi standard la differenza e nei limiti del rumore; per network function (VPN concentrators, load balancer, IDS) testare *prima* del cutover con i pattern di traffico reale.
5. **`--cpu host` non e un'opzione, e quasi sempre la scelta giusta.** L'unica eccezione: cluster Proxmox con CPU eterogenei dove la VM deve poter live-migrate fra nodi (allora si usa `--cpu kvm64` o un baseline EVC-equivalente). Per la maggior parte dei deployment: `--cpu host` da SIMD complete + ~10-20% di prestazioni in piu.
6. **Il time sync per i DC va via NTP esterno, non via QEMU host-time.** L'host time-sync di QEMU e affidabile per VM general-purpose, ma il PDC emulator deve essere la fonte autorevole del dominio: deve sincronizzarsi con un sorgente esterno (es. `time.nist.gov`, `pool.ntp.org`) e propagare il tempo alle altre macchine del dominio. Disabilitare il time-sync host-side: `qm set --ostype win10 --localtime 0` *e* dentro il DC: `w32tm /config /manualpeerlist:"time.windows.com,0x9" /syncfromflags:manual /update`.

## Indice
- [Panoramica](#panoramica)
- [Pre-requisiti e Preparazione dell'Ambiente](#pre-requisiti-e-preparazione-dellambiente)
- [Installazione dei Driver VirtIO Prima della Migrazione](#installazione-dei-driver-virtio-prima-della-migrazione)
- [Conversione del Disco e del Controller](#conversione-del-disco-e-del-controller)
- [Migrazione della Rete: VMXNET3 verso VirtIO Net](#migrazione-della-rete-vmxnet3-verso-virtio-net)
- [QEMU Guest Agent: Installazione e Configurazione](#qemu-guest-agent-installazione-e-configurazione)
- [Gestione Speciale dei Domain Controller Active Directory](#gestione-speciale-dei-domain-controller-active-directory)
- [Licensing e Attivazione Post-Migrazione](#licensing-e-attivazione-post-migrazione)
- [Specificità per Versione di Windows Server](#specificità-per-versione-di-windows-server)
- [Procedura Step-by-Step Completa](#procedura-step-by-step-completa)
- [Ottimizzazione Post-Migrazione](#ottimizzazione-post-migrazione)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La migrazione di macchine virtuali Windows Server da VMware vSphere a Proxmox VE rappresenta una delle operazioni più critiche nell'intero processo di transizione dell'infrastruttura. A differenza delle VM Linux, dove il kernel gestisce i driver in modo modulare e il passaggio tra hypervisor è relativamente trasparente, Windows Server richiede una preparazione meticolosa dei driver paravirtualizzati prima dello spostamento. Se la VM viene avviata su Proxmox senza i driver VirtIO correttamente installati, il sistema operativo non sarà in grado di accedere al disco di boot, risultando in un Blue Screen of Death (BSOD) con codice INACCESSIBLE_BOOT_DEVICE.

Il passaggio da un ambiente VMware a Proxmox implica la sostituzione di componenti hardware virtualizzati fondamentali: il controller disco PVSCSI o LSI Logic viene rimpiazzato dal VirtIO SCSI controller, l'adattatore di rete VMXNET3 dal VirtIO Net (o temporaneamente dall'emulato e1000), e gli strumenti di integrazione VMware Tools vengono sostituiti dal QEMU Guest Agent. Ciascuna di queste transizioni richiede un approccio specifico e una sequenza precisa di operazioni per evitare perdita di dati, downtime prolungato o instabilità del sistema.

Questo documento copre l'intero ciclo di migrazione per Windows Server nelle versioni 2012 R2, 2016, 2019 e 2022, con attenzione particolare ai Domain Controller Active Directory, alla gestione del licensing post-migrazione, e alle ottimizzazioni specifiche per l'ambiente KVM/QEMU. La procedura è stata validata in ambienti di produzione e include i passaggi di rollback per ogni fase critica.

---

## Pre-requisiti e Preparazione dell'Ambiente

### Requisiti Lato VMware

Prima di procedere con qualsiasi operazione, è necessario raccogliere informazioni dettagliate sulla VM sorgente. I dati essenziali includono:

| Parametro | Comando/Posizione | Esempio |
|---|---|---|
| Versione OS | `systeminfo \| findstr /B /C:"OS Name"` | Windows Server 2019 Standard |
| Architettura | `wmic os get osarchitecture` | 64-bit |
| Controller disco | vSphere Client → VM Settings → SCSI Controller | PVSCSI |
| Adattatore rete | vSphere Client → VM Settings → Network Adapter | VMXNET3 |
| Dimensione disco | `Get-Disk \| Format-Table` (PowerShell) | 100 GB |
| Formato disco VMware | Datastore Browser | Thin provisioned VMDK |
| VMware Tools versione | `"C:\Program Files\VMware\VMware Tools\VMwareToolboxCmd.exe" -v` | 12.3.0 |
| Ruoli installati | `Get-WindowsFeature \| Where Installed` | AD DS, DNS, DHCP |

### Requisiti Lato Proxmox

Sul nodo Proxmox di destinazione verificare:

```bash
# Verificare la versione di Proxmox
pveversion -v

# Verificare spazio disponibile sullo storage di destinazione
pvesm status

# Verificare che la ISO virtio-win sia disponibile
ls /var/lib/vz/template/iso/virtio-win*.iso

# Se non presente, scaricare l'ultima versione stabile
wget -O /var/lib/vz/template/iso/virtio-win.iso \
  https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso
```

### Snapshot e Backup Pre-Migrazione

È imperativo creare un backup completo e verificato prima di qualsiasi modifica:

```powershell
# Su VMware: creare snapshot con memoria e quiesce
# Via PowerCLI:
$vm = Get-VM -Name "WIN-SRV-2019"
New-Snapshot -VM $vm -Name "Pre-Migration-Backup" -Description "Snapshot before Proxmox migration" -Memory -Quiesce

# Verificare l'integrità dello snapshot
Get-Snapshot -VM $vm | Format-List *
```

Per i Domain Controller, lo snapshot con memoria NON è raccomandato a causa del rischio di USN rollback. Utilizzare invece un backup Windows Server Backup o un backup a livello di applicazione.

---

## Installazione dei Driver VirtIO Prima della Migrazione

Questa è la fase più critica dell'intero processo. I driver VirtIO devono essere installati e registrati nel registry di Windows **prima** che la VM venga spostata su Proxmox. Senza il driver `viostor` (o `vioscsi`) caricato all'avvio, Windows non potrà montare il volume di boot.

### Montaggio della ISO virtio-win sulla VM VMware

Dalla console vSphere, collegare la ISO `virtio-win.iso` al lettore CD/DVD della VM. In alternativa, copiare il contenuto della ISO su un percorso di rete accessibile dalla VM.

### Struttura della ISO virtio-win

La ISO contiene i driver organizzati per versione di Windows e architettura:

```
virtio-win.iso/
├── Balloon/          # Memory ballooning driver
│   ├── 2k19/amd64/  # Windows Server 2019 64-bit
│   ├── 2k22/amd64/  # Windows Server 2022 64-bit
│   └── ...
├── NetKVM/           # VirtIO network driver
│   ├── 2k19/amd64/
│   └── ...
├── vioscsi/          # VirtIO SCSI controller driver
│   ├── 2k19/amd64/
│   └── ...
├── viostor/          # VirtIO block storage driver
│   ├── 2k19/amd64/
│   └── ...
├── qxldod/           # Display driver (QXL)
│   └── ...
├── vioserial/        # Serial port driver (guest agent)
│   └── ...
├── guest-agent/      # QEMU Guest Agent installer
│   ├── qemu-ga-x86_64.msi
│   └── qemu-ga-i386.msi
└── virtio-win-gt-x64.msi  # Installer bundle (tutti i driver)
```

### Metodo 1: Installazione Tramite MSI Installer (Raccomandato)

Il metodo più semplice e affidabile consiste nell'utilizzare l'installer bundle:

```powershell
# Montare la ISO o navigare al percorso di rete
# Eseguire l'installer con privilegi elevati
D:\virtio-win-gt-x64.msi /quiet /norestart

# Verificare che i driver siano stati installati
Get-WindowsDriver -Online | Where-Object { $_.ProviderName -eq "Red Hat, Inc." } | Format-Table Driver, OriginalFileName, ProviderName, Date
```

L'installer MSI installa automaticamente tutti i driver VirtIO necessari e li registra nel driver store di Windows. Questo garantisce che al prossimo avvio, quando il controller disco sarà di tipo VirtIO, Windows caricherà il driver corretto.

### Metodo 2: Installazione Manuale dei Driver Individuali

Se si desidera un controllo granulare, i driver possono essere installati singolarmente tramite `pnputil`:

```powershell
# Driver disco VirtIO SCSI (CRITICO - senza questo la VM non si avvia)
pnputil /add-driver "D:\vioscsi\2k19\amd64\vioscsi.inf" /install

# Driver disco VirtIO block (alternativo a vioscsi)
pnputil /add-driver "D:\viostor\2k19\amd64\viostor.inf" /install

# Driver rete VirtIO
pnputil /add-driver "D:\NetKVM\2k19\amd64\netkvm.inf" /install

# Driver balloon (gestione memoria)
pnputil /add-driver "D:\Balloon\2k19\amd64\balloon.inf" /install

# Driver seriale (necessario per QEMU Guest Agent)
pnputil /add-driver "D:\vioserial\2k19\amd64\vioser.inf" /install

# Driver display QXL
pnputil /add-driver "D:\qxldod\2k19\amd64\qxldod.inf" /install
```

Sostituire `2k19` con la directory appropriata per la versione di Windows Server in uso: `2k12R2` per 2012 R2, `2k16` per 2016, `2k22` per 2022.

### Metodo 3: Injection dei Driver nel Registry (Offline, Avanzato)

Se la VM è già stata migrata senza driver e risulta in BSOD, è possibile iniettare i driver offline:

```bash
# Sul nodo Proxmox, montare il disco della VM
qm set <VMID> -ide2 /var/lib/vz/template/iso/virtio-win.iso,media=cdrom

# Avviare la VM in modalità recovery (boot da ISO Windows)
# Dalla console di ripristino:
dism /image:C:\ /add-driver /driver:D:\vioscsi\2k19\amd64 /recurse /forceunsigned
dism /image:C:\ /add-driver /driver:D:\viostor\2k19\amd64 /recurse /forceunsigned
```

### Verifica dell'Installazione dei Driver

Dopo l'installazione, verificare che i driver siano presenti nel driver store:

```powershell
# Elencare i driver VirtIO installati
dism /online /get-drivers | findstr -i "virtio vio Red.Hat"

# Verificare nel registro di sistema
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\vioscsi" -ErrorAction SilentlyContinue
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\viostor" -ErrorAction SilentlyContinue
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\netkvm" -ErrorAction SilentlyContinue

# Il valore Start deve essere 0 (Boot) per vioscsi/viostor
# Se è 3 (Manual), correggerlo:
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\vioscsi" -Name "Start" -Value 0
```

Il valore `Start = 0` nel registry indica che il driver viene caricato durante il boot. Questo è essenziale per `vioscsi` e `viostor`, altrimenti Windows non potrà accedere al disco di sistema durante l'avvio.

---

## Conversione del Disco e del Controller

### Esportazione del Disco VMDK

```bash
# Opzione 1: Esportazione OVF tramite ovftool
ovftool --noSSLVerify vi://user@vcenter/DC/vm/WIN-SRV-2019 /tmp/export/

# Opzione 2: Copia diretta del VMDK dal datastore
scp root@esxi:/vmfs/volumes/datastore1/WIN-SRV-2019/WIN-SRV-2019-flat.vmdk /tmp/

# Opzione 3: Tramite PowerCLI
Export-VApp -VM "WIN-SRV-2019" -Destination /tmp/export/ -Format OVF
```

### Conversione VMDK → QCOW2 o Raw

```bash
# Conversione in formato qcow2 (supporta snapshot, thin provisioning)
qemu-img convert -f vmdk -O qcow2 WIN-SRV-2019-flat.vmdk WIN-SRV-2019.qcow2

# Conversione in formato raw (prestazioni migliori, nessun overhead)
qemu-img convert -f vmdk -O raw WIN-SRV-2019-flat.vmdk WIN-SRV-2019.raw

# Verificare l'integrità del file convertito
qemu-img check WIN-SRV-2019.qcow2
qemu-img info WIN-SRV-2019.qcow2
```

### Importazione su Proxmox

```bash
# Creare la VM su Proxmox (senza disco)
qm create 200 \
  --name WIN-SRV-2019 \
  --memory 8192 \
  --cores 4 \
  --sockets 1 \
  --cpu host \
  --net0 virtio,bridge=vmbr0 \
  --ostype win10 \
  --bios ovmf \
  --machine q35 \
  --efidisk0 local-lvm:1,format=qcow2,efitype=4m,pre-enrolled-keys=1 \
  --scsihw virtio-scsi-single \
  --agent enabled=1

# Importare il disco convertito
qm importdisk 200 WIN-SRV-2019.qcow2 local-lvm

# Collegare il disco importato alla VM
qm set 200 --scsi0 local-lvm:vm-200-disk-1,iothread=1,discard=on

# Impostare l'ordine di boot
qm set 200 --boot order=scsi0
```

La scelta di `virtio-scsi-single` con `iothread=1` è fondamentale per le prestazioni. Ogni disco ottiene un thread I/O dedicato, riducendo la contesa e migliorando la latenza. Il modello di macchina `q35` è raccomandato per Windows moderno in quanto supporta PCIe nativo.

### Nota su BIOS UEFI vs Legacy

Se la VM VMware utilizzava BIOS legacy (non EFI), configurare Proxmox di conseguenza:

```bash
# Per VM con BIOS legacy (SeaBIOS)
qm set 200 --bios seabios
# Rimuovere efidisk se presente
qm set 200 --delete efidisk0
```

Verificare sulla VM VMware prima della migrazione:

```powershell
# Verificare se il sistema usa UEFI o BIOS
bcdedit /enum firmware
# Se restituisce un errore, il sistema è BIOS legacy
# Se mostra entries, il sistema è UEFI
```

---

## Migrazione della Rete: VMXNET3 verso VirtIO Net

### Strategia di Migrazione dell'Adattatore di Rete

La transizione dell'adattatore di rete è meno critica rispetto al controller disco perché non impedisce il boot del sistema. Tuttavia, senza connettività di rete, la VM è inutilizzabile in produzione.

Il percorso raccomandato è:

```
VMXNET3 (VMware) → VirtIO Net (Proxmox, prestazioni ottimali)
                  → e1000 (fallback se VirtIO Net causa problemi)
```

Se i driver VirtIO sono stati installati correttamente prima della migrazione (tramite il pacchetto MSI o il driver NetKVM individuale), il driver `netkvm` verrà caricato automaticamente quando Windows rileva l'hardware VirtIO Net.

### Configurazione dell'Adattatore su Proxmox

```bash
# VirtIO Net (raccomandato)
qm set 200 --net0 virtio,bridge=vmbr0,firewall=0

# e1000 (fallback - prestazioni inferiori ma compatibilità universale)
qm set 200 --net0 e1000,bridge=vmbr0,firewall=0
```

### Preservare la Configurazione IP

Prima della migrazione, documentare la configurazione di rete completa:

```powershell
# Esportare configurazione IP
Get-NetIPConfiguration | Format-List *
Get-NetIPAddress | Export-Csv C:\network-config.csv
Get-DnsClientServerAddress | Export-Csv C:\dns-config.csv
Get-NetRoute | Export-Csv C:\route-config.csv

# Esportare configurazione NIC teaming se presente
Get-NetLbfoTeam | Format-List *
```

Dopo la migrazione, l'adattatore VirtIO apparirà come un nuovo dispositivo di rete. La configurazione IP statica dovrà essere riapplicata manualmente o tramite script:

```powershell
# Identificare il nuovo adattatore VirtIO
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, MacAddress

# Riapplicare configurazione IP
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.1.100 -PrefixLength 24 -DefaultGateway 192.168.1.1
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 192.168.1.10,192.168.1.11
```

---

## QEMU Guest Agent: Installazione e Configurazione

Il QEMU Guest Agent sostituisce VMware Tools per le funzioni di integrazione host-guest. Fornisce: shutdown/reboot graceful dal pannello Proxmox, freeze del filesystem per snapshot consistenti, reporting dell'IP address e di altre informazioni guest.

### Installazione

```powershell
# Dall'installer nella ISO virtio-win
msiexec /i D:\guest-agent\qemu-ga-x86_64.msi /quiet /norestart

# Verificare che il servizio sia in esecuzione
Get-Service QEMU-GA | Format-List *

# Se non è avviato
Start-Service QEMU-GA
Set-Service QEMU-GA -StartupType Automatic
```

### Configurazione su Proxmox

```bash
# Abilitare il canale guest agent sulla VM
qm set 200 --agent enabled=1,fstrim_cloned_disks=1

# Verificare la comunicazione
qm guest cmd 200 ping
qm guest cmd 200 get-osinfo
qm guest exec 200 ipconfig
```

### Rimozione di VMware Tools

Dopo aver confermato il funzionamento del QEMU Guest Agent, rimuovere VMware Tools:

```powershell
# Disinstallazione standard
$app = Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -match "VMware Tools" }
$app.Uninstall()

# Alternativa: da Programmi e Funzionalità o tramite il setup originale
# "C:\Program Files\VMware\VMware Tools\VMwareToolsSetup.exe" /c

# Pulizia dei driver residui
pnputil /enum-drivers | findstr -i vmware
# Per ogni driver VMware trovato:
# pnputil /delete-driver oem<N>.inf /uninstall
```

---

## Gestione Speciale dei Domain Controller Active Directory

La migrazione di un Domain Controller (DC) Active Directory richiede precauzioni aggiuntive significative rispetto a un member server. Un errore nella procedura può causare corruzione del database AD, USN rollback, o perdita dei ruoli FSMO.

### Regole Fondamentali per i DC

1. **Mai** fare snapshot con memoria di un Domain Controller
2. **Mai** clonare un DC senza seguire la procedura di DC cloning di Microsoft
3. **Mai** migrare tutti i DC contemporaneamente — almeno uno deve restare operativo
4. Verificare la replica AD prima, durante e dopo la migrazione
5. Trasferire i ruoli FSMO prima di migrare il DC che li detiene

### Verifica Pre-Migrazione dello Stato AD

```powershell
# Verificare la salute della replica
repadmin /replsummary
repadmin /showrepl
dcdiag /v /c /d /e /s:DC-NAME

# Identificare il detentore dei ruoli FSMO
netdom query fsmo

# Output tipico:
# Schema master               DC01.contoso.local
# Domain naming master        DC01.contoso.local
# PDC                         DC01.contoso.local
# RID pool manager            DC01.contoso.local
# Infrastructure master       DC01.contoso.local

# Verificare il database AD
esentutl /g "C:\Windows\NTDS\ntds.dit"
```

### Procedura per DC con Ruoli FSMO

Se il DC da migrare detiene ruoli FSMO, trasferirli prima della migrazione:

```powershell
# Trasferire tutti i ruoli FSMO a un altro DC
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" -OperationMasterRole SchemaMaster,DomainNamingMaster,PDCEmulator,RIDMaster,InfrastructureMaster -Force

# Verificare il trasferimento
netdom query fsmo
```

### Sequenza di Migrazione per DC

```
1. Verificare salute AD (dcdiag, repadmin)
2. Trasferire ruoli FSMO (se applicabile)
3. Installare driver VirtIO sulla VM in VMware
4. Forzare una replica completa: repadmin /syncall /AdeP
5. Spegnere la VM (shutdown pulito, NO snapshot)
6. Esportare e convertire il disco VMDK
7. Importare su Proxmox con configurazione corretta
8. Avviare la VM su Proxmox
9. Riconfigurare la rete (stessi IP!)
10. Verificare replica AD: repadmin /replsummary
11. Eseguire dcdiag /v /c completo
12. Monitorare per 24-48 ore
```

### Verifica Post-Migrazione AD

```powershell
# Test completo della salute del DC
dcdiag /v /c /d /e /s:DC-NAME > C:\dcdiag-post-migration.txt

# Verificare la replica con tutti i partner
repadmin /replsummary
repadmin /showrepl DC-NAME

# Verificare la risoluzione DNS
Resolve-DnsName contoso.local -Type SOA
Resolve-DnsName _ldap._tcp.dc._msdcs.contoso.local -Type SRV

# Verificare Kerberos
klist purge
klist get krbtgt

# Verificare i servizi critici
Get-Service NTDS, DNS, KDC, Netlogon, W32Time | Format-Table Name, Status
```

---

## Licensing e Attivazione Post-Migrazione

La migrazione dell'hypervisor modifica l'hardware virtuale percepito da Windows, il che può innescare una richiesta di riattivazione della licenza. Il comportamento dipende dal tipo di licenza.

### Tipi di Licenza e Impatto

| Tipo Licenza | Impatto Migrazione | Azione Richiesta |
|---|---|---|
| KMS (Key Management Service) | Riattivazione automatica se KMS raggiungibile | Verificare connettività al KMS |
| MAK (Multiple Activation Key) | Può richiedere riattivazione telefonica | Contattare Microsoft se online fallisce |
| AVMA (Automatic VM Activation) | Non funziona su Proxmox (solo Hyper-V) | Convertire a KMS o MAK |
| OEM | Non trasferibile | Acquistare nuova licenza |
| Retail/FPP | Riattivazione possibile | `slmgr /ato` |
| Datacenter con diritti VM illimitati | Licenza host, non guest | Verificare compliance |

### Procedura di Riattivazione

```powershell
# Verificare lo stato corrente della licenza
slmgr /dli
slmgr /xpr

# Per licenze KMS: forzare la riattivazione
slmgr /ato

# Se KMS non raggiungibile, verificare:
nslookup -type=srv _vlmcs._tcp.contoso.local
# Deve risolvere al server KMS

# Impostare manualmente il server KMS se necessario
slmgr /skms kms-server.contoso.local:1688
slmgr /ato

# Per AVMA (non funziona su Proxmox): convertire a KMS
slmgr /ipk <KMS-CLIENT-SETUP-KEY>
slmgr /ato
```

### Chiavi KMS Client Setup per Windows Server

| Versione | Edition | KMS Client Key |
|---|---|---|
| 2022 | Standard | VDYBN-27WPP-V4HQT-9VMD4-VMK7H |
| 2022 | Datacenter | WX4NM-KYWYW-QJJR4-XV3QB-6VM33 |
| 2019 | Standard | N69G4-B89J2-4G8F4-WWYCC-J464C |
| 2019 | Datacenter | WMDGN-G9PQG-XVVXX-R3X43-63DFG |
| 2016 | Standard | WC2BQ-8NRM3-FDDYY-2BFGV-KHKQY |
| 2016 | Datacenter | CB7KF-BWN84-R7R2Y-793K2-8XDDG |
| 2012 R2 | Standard | D2N9P-3P6X9-2R39C-7RTCD-MDVJX |
| 2012 R2 | Datacenter | W3GGN-FT8W3-Y4M27-J84CP-Q3VJ9 |

---

## Specificità per Versione di Windows Server

### Windows Server 2012 R2

- Richiede driver VirtIO versione compatibile (verificare la cartella `2k12R2` nella ISO)
- Non supporta Secure Boot con OVMF su Proxmox — usare SeaBIOS
- Fine del supporto esteso: ottobre 2023 — pianificare l'upgrade
- Il driver `qxldod` potrebbe non essere disponibile; usare `vga std`
- Impostare `ostype` a `win8` nella configurazione Proxmox

```bash
qm set 200 --ostype win8 --bios seabios --machine i440fx --vga std
```

### Windows Server 2016

- Supporto completo per tutti i driver VirtIO
- Supporta UEFI con OVMF e Secure Boot
- Il modello macchina `q35` è raccomandato
- Impostare `ostype` a `win10`

```bash
qm set 200 --ostype win10 --bios ovmf --machine q35 --vga qxl
```

### Windows Server 2019

- Supporto ottimale per VirtIO, incluso multiqueue per NetKVM
- Supporta tutte le funzionalità avanzate di Proxmox
- Raccomandato il tipo di CPU `host` per funzionalità complete

```bash
qm set 200 --ostype win10 --bios ovmf --machine q35 --cpu host --vga qxl
```

### Windows Server 2022

- Richiede i driver VirtIO più recenti (versione >= 0.1.229)
- Supporto nativo per VBS (Virtualization Based Security) — verificare compatibilità
- TPM 2.0 virtuale disponibile su Proxmox 7.x+

```bash
qm set 200 --ostype win11 --bios ovmf --machine q35 --cpu host --vga qxl \
  --tpmstate0 local-lvm:1,version=v2.0
```

---

## Procedura Step-by-Step Completa

### Fase 1: Preparazione (T-7 giorni)

```
1. Documentare la configurazione completa della VM VMware
2. Verificare backup funzionanti
3. Scaricare virtio-win.iso sul nodo Proxmox
4. Preparare la VM Proxmox di destinazione (senza disco)
5. Pianificare la finestra di manutenzione
6. Notificare gli stakeholder
```

### Fase 2: Pre-installazione Driver (T-3 giorni)

```
1. Montare virtio-win.iso sulla VM in VMware
2. Installare tutti i driver VirtIO (MSI o manuale)
3. Installare QEMU Guest Agent
4. Verificare l'installazione dei driver nel registry
5. Riavviare la VM e confermare funzionamento normale
6. Per i DC: eseguire dcdiag e repadmin per baseline
```

### Fase 3: Migrazione (Giorno M)

```
 1. [M-1h]  Snapshot/backup finale su VMware
 2. [M-30m] Per i DC: repadmin /syncall /AdeP
 3. [M-15m] Shutdown pulito della VM
 4. [M]     Esportare disco VMDK
 5. [M+15m] Convertire VMDK → qcow2/raw
 6. [M+30m] Importare disco su Proxmox
 7. [M+45m] Configurare la VM Proxmox
 8. [M+1h]  Avviare la VM su Proxmox
 9. [M+1h15] Verificare boot (console VNC/SPICE)
10. [M+1h30] Riconfigurare rete
11. [M+1h45] Verificare servizi e applicazioni
12. [M+2h]  Per i DC: dcdiag, repadmin, DNS
13. [M+2h]  Verificare attivazione Windows
```

### Fase 4: Validazione Post-Migrazione (T+1 a T+7)

```
1. Monitorare performance per 24-48 ore
2. Verificare tutti i servizi applicativi
3. Eseguire test di carico se applicabile
4. Rimuovere VMware Tools
5. Ottimizzare configurazione (sezione successiva)
6. Rimuovere snapshot VMware dopo periodo di grazia (7 giorni)
7. Documentare la migrazione completata
```

---

## Ottimizzazione Post-Migrazione

### Configurazione CPU e Memoria

```bash
# CPU: tipo host per massime prestazioni
qm set 200 --cpu host

# NUMA awareness (se il nodo ha più socket)
qm set 200 --numa 1

# Ballooning (non raccomandato per server critici)
# Per DC e DB server, disabilitare:
qm set 200 --balloon 0

# Hugepages (riduce overhead TLB)
# Solo se il nodo ha hugepages configurate
qm set 200 --hugepages 1024
```

### Ottimizzazione Disco

```bash
# Abilitare discard/TRIM per thin provisioning
qm set 200 --scsi0 local-lvm:vm-200-disk-1,iothread=1,discard=on,ssd=1

# All'interno di Windows, abilitare TRIM schedulato
# (di solito attivo per default su SSD)
fsutil behavior query DisableDeleteNotify
# Se il valore è 1, abilitare:
fsutil behavior set DisableDeleteNotify 0
```

### Ottimizzazione di Rete

```powershell
# All'interno di Windows, abilitare le offload features
Get-NetAdapterAdvancedProperty -Name "Ethernet" | Format-Table

# Impostare RSS (Receive Side Scaling)
Set-NetAdapterAdvancedProperty -Name "Ethernet" -RegistryKeyword "*RSS" -RegistryValue 1

# Impostare il numero di code
Set-NetAdapterRss -Name "Ethernet" -NumberOfReceiveQueues 4
```

### Configurazione dei Servizi di Tempo

Per i Domain Controller, la sincronizzazione temporale è critica:

```powershell
# Disabilitare la sincronizzazione tempo dell'hypervisor (QEMU)
# e usare NTP tramite il PDC emulator
w32tm /config /manualpeerlist:"time.windows.com" /syncfromflags:manual /reliable:yes /update
Restart-Service W32Time
w32tm /resync
```

### Disabilitare Power Management Aggressivo

```powershell
# Impostare il piano energetico su High Performance
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

# Verificare
powercfg /getactivescheme
```

---

## Best Practices

- **Installare sempre i driver VirtIO PRIMA della migrazione** — è l'errore più comune e il più costoso da risolvere post-factum
- **Utilizzare l'installer MSI** per i driver VirtIO anziché l'installazione manuale dei singoli INF, per garantire la registrazione corretta nel driver store e nel registry
- **Non migrare mai tutti i Domain Controller contemporaneamente** — mantenere almeno un DC operativo nell'ambiente VMware fino a completa validazione
- **Trasferire i ruoli FSMO** prima di migrare il DC che li detiene, non dopo
- **Preservare gli stessi indirizzi IP e hostname** per minimizzare l'impatto sulle applicazioni e sui servizi dipendenti
- **Utilizzare il formato raw per i dischi** di server mission-critical per prestazioni ottimali, qcow2 per server dove gli snapshot sono necessari
- **Disabilitare il memory ballooning** per Domain Controller e database server
- **Mantenere il backup VMware** per almeno 7-14 giorni dopo la migrazione come opzione di rollback
- **Pianificare la migrazione in ore di basso carico** e con una finestra di manutenzione concordata
- **Testare la procedura su una VM non critica** prima di procedere con server di produzione
- **Documentare ogni passaggio** eseguito e ogni deviazione dalla procedura standard
- **Verificare la licenza Windows** e pianificare la riattivazione prima della migrazione, specialmente per le licenze AVMA che non funzionano su Proxmox

---

## Troubleshooting

### Problema: BSOD INACCESSIBLE_BOOT_DEVICE all'Avvio

**Sintomi**: La VM non si avvia su Proxmox, mostrando una schermata blu con codice di errore 0x0000007B o INACCESSIBLE_BOOT_DEVICE.

**Causa**: I driver VirtIO per il controller disco (vioscsi/viostor) non sono stati installati prima della migrazione, oppure il valore di avvio nel registry non è impostato correttamente (Start != 0).

**Soluzione**: Avviare la VM da un'ISO di installazione Windows in modalità recovery. Dalla command prompt di ripristino, montare la ISO virtio-win e iniettare i driver offline con DISM:
```
dism /image:C:\ /add-driver /driver:D:\vioscsi\2k19\amd64 /recurse /forceunsigned
```
In alternativa, cambiare temporaneamente il controller disco a IDE (`--scsihw lsi`) per poter avviare Windows, installare i driver VirtIO, e poi tornare a VirtIO SCSI.

**Prevenzione**: Verificare sempre l'installazione dei driver e il valore `Start = 0` nel registry per vioscsi/viostor prima di procedere con la migrazione.

---

### Problema: Nessuna Connettività di Rete Dopo la Migrazione

**Sintomi**: La VM si avvia correttamente ma non ha connettività di rete. Il Device Manager mostra l'adattatore di rete con un punto esclamativo giallo o non mostra alcun adattatore.

**Causa**: Il driver NetKVM (VirtIO Net) non è stato installato prima della migrazione, oppure la configurazione IP statica è rimasta associata all'adattatore VMware precedente.

**Soluzione**: Se il driver manca, montare la ISO virtio-win sulla VM tramite il pannello Proxmox e installare il driver NetKVM dal Device Manager. Se il driver è presente ma la rete non funziona, verificare che l'IP sia configurato sul nuovo adattatore. Come workaround immediato, cambiare il modello di rete a `e1000` che non richiede driver aggiuntivi:
```bash
qm set 200 --net0 e1000,bridge=vmbr0
```

**Prevenzione**: Installare il driver NetKVM prima della migrazione e documentare la configurazione IP per riapplicarla manualmente.

---

### Problema: Errori di Replica Active Directory Post-Migrazione

**Sintomi**: `repadmin /replsummary` mostra errori di replica. `dcdiag` riporta fallimenti nei test di connettività o replica. Event log mostra eventi NTDS Replication con errori.

**Causa**: Cambio dell'indirizzo IP o del MAC address, problemi di risoluzione DNS, o tempo di spegnimento prolungato che ha causato scadenza del tombstone o gap nella replica.

**Soluzione**: Verificare la risoluzione DNS in entrambe le direzioni (forward e reverse). Assicurarsi che il DC migrato possa raggiungere tutti i partner di replica. Forzare la replica:
```powershell
repadmin /syncall /AdeP
```
Se il tempo offline ha superato il tombstone lifetime (60 o 180 giorni), il DC deve essere demoted e ripromosse.

**Prevenzione**: Minimizzare il tempo di spegnimento durante la migrazione. Assicurarsi che DNS sia configurato correttamente e che gli IP siano preservati.

---

### Problema: Attivazione Windows Fallita (Errore 0xC004F074)

**Sintomi**: Windows mostra il watermark di attivazione. `slmgr /dli` riporta stato "Notification" o "Grace period". Errore 0xC004F074 indica che il KMS non è raggiungibile.

**Causa**: Il server KMS non è raggiungibile dalla VM migrata (problema di rete), oppure la licenza era di tipo AVMA (funziona solo su Hyper-V) che non è supportata su KVM/Proxmox.

**Soluzione**: Verificare la connettività al server KMS (`telnet kms-server 1688`). Se il problema è AVMA, convertire a KMS inserendo la chiave KMS client setup appropriata:
```powershell
slmgr /ipk <KMS-CLIENT-KEY>
slmgr /skms kms-server.contoso.local:1688
slmgr /ato
```

**Prevenzione**: Identificare il tipo di licenza prima della migrazione e pianificare la conversione AVMA→KMS in anticipo.

---

### Problema: Prestazioni Disco Degradate Post-Migrazione

**Sintomi**: Le operazioni di I/O sono significativamente più lente rispetto all'ambiente VMware. Applicazioni che dipendono dal disco (SQL Server, file server) mostrano latenza elevata.

**Causa**: Il controller disco è configurato come IDE anziché VirtIO SCSI, oppure manca iothread, oppure il formato disco è qcow2 senza preallocation, oppure la cache mode non è ottimale.

**Soluzione**: Verificare e ottimizzare la configurazione:
```bash
# Assicurarsi di usare VirtIO SCSI con iothread
qm set 200 --scsihw virtio-scsi-single --scsi0 local-lvm:vm-200-disk-1,iothread=1,discard=on,cache=none
```
Per workload intensivi, considerare la conversione a formato raw e l'uso di LVM-thin o ZFS come backend di storage.

**Prevenzione**: Configurare sempre VirtIO SCSI con iothread e testare le prestazioni I/O con un benchmark (CrystalDiskMark, diskspd) immediatamente dopo la migrazione.

---

### Problema: Clock Drift e Problemi di Sincronizzazione Temporale

**Sintomi**: Il tempo del sistema diverge progressivamente. Kerberos authentication fallisce con errori di skew temporale. I log mostrano timestamp inconsistenti.

**Causa**: Conflitto tra la sincronizzazione temporale dell'hypervisor QEMU e il servizio W32Time di Windows. Su VMware, VMware Tools gestiva questa integrazione; su Proxmox, il meccanismo è diverso.

**Soluzione**: Disabilitare la sincronizzazione temporale dell'hypervisor e configurare NTP direttamente:
```powershell
# Per i DC (PDC Emulator deve usare una sorgente esterna)
w32tm /config /manualpeerlist:"0.pool.ntp.org 1.pool.ntp.org" /syncfromflags:manual /reliable:yes /update
Restart-Service W32Time
w32tm /resync
w32tm /query /status
```

**Prevenzione**: Configurare la sincronizzazione temporale come parte della procedura post-migrazione standard. Per i Domain Controller, il PDC Emulator deve avere una sorgente NTP esterna configurata.

---

### Problema: QEMU Guest Agent Non Comunica

**Sintomi**: Il pannello Proxmox non mostra l'IP della VM. I comandi `qm guest cmd` falliscono con timeout. Shutdown graceful dal pannello Proxmox non funziona.

**Causa**: Il servizio QEMU Guest Agent non è installato o non è in esecuzione nella VM. Il canale seriale virtio (vsock o virtio-serial) non è configurato sulla VM Proxmox. Il firewall Windows blocca la comunicazione.

**Soluzione**: Verificare il servizio dentro la VM:
```powershell
Get-Service QEMU-GA
Start-Service QEMU-GA
```
Verificare la configurazione Proxmox:
```bash
qm set 200 --agent enabled=1
# Verificare che il device seriale sia presente
qm config 200 | grep serial
```
Se il device serial manca, la comunicazione non può avvenire. Riavviare la VM dopo aver abilitato l'agent nella configurazione.

**Prevenzione**: Installare il QEMU Guest Agent durante la fase di pre-installazione driver, prima della migrazione. Abilitare l'agent nella configurazione VM Proxmox al momento della creazione.

---

### Problema: Secure Boot Fallisce su Proxmox

**Sintomi**: La VM non si avvia su Proxmox con OVMF/UEFI. L'output della console mostra errori relativi al Secure Boot o al certificato di firma.

**Causa**: I driver VirtIO non sono firmati con un certificato riconosciuto dal firmware UEFI, oppure la configurazione OVMF non include le chiavi Microsoft pre-enrolled.

**Soluzione**: Utilizzare l'opzione `pre-enrolled-keys=1` quando si crea l'EFI disk per includere le chiavi Microsoft. Se il problema persiste, disabilitare temporaneamente Secure Boot nella configurazione UEFI della VM (accedere alla shell UEFI premendo ESC durante il boot).

```bash
# Ricreare l'EFI disk con chiavi pre-enrolled
qm set 200 --delete efidisk0
qm set 200 --efidisk0 local-lvm:1,format=qcow2,efitype=4m,pre-enrolled-keys=1
```

**Prevenzione**: Usare sempre `pre-enrolled-keys=1` per VM Windows con UEFI Secure Boot. Assicurarsi di utilizzare la versione più recente della ISO virtio-win con driver firmati.

---

## Riferimenti

- [Proxmox VE Wiki — Windows VirtIO Drivers](https://pve.proxmox.com/wiki/Windows_VirtIO_Drivers)
- [Proxmox VE Wiki — QEMU Guest Agent](https://pve.proxmox.com/wiki/Qemu-guest-agent)
- [Fedora Project — VirtIO-Win Drivers](https://docs.fedoraproject.org/en-US/quick-docs/creating-windows-virtual-machines-using-virtio-drivers/)
- [Microsoft — Active Directory Backup and Recovery](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/ad-forest-recovery-guide)
- [Microsoft — FSMO Roles](https://learn.microsoft.com/en-us/troubleshoot/windows-server/identity/fsmo-roles)
- [Microsoft — KMS Client Setup Keys](https://learn.microsoft.com/en-us/windows-server/get-started/kms-client-activation-keys)
- [Microsoft — Volume Activation](https://learn.microsoft.com/en-us/windows-server/get-started/volume-activation-overview)
- [Proxmox VE Wiki — Migration of Servers to Proxmox VE](https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE)
- [QEMU Documentation — VirtIO](https://www.qemu.org/docs/master/system/devices/virtio-net.html)
- [Red Hat — VirtIO Drivers for Windows](https://access.redhat.com/articles/2488201)

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — virtio-win release cadence e stable channel.** Il progetto upstream Fedora/Red Hat per i driver Windows (`virtio-win`) rilascia ISO firmate stabili approssimativamente trimestralmente. Versione stabile corrente (riferimento del modulo): **virtio-win-0.1.262** (ottobre 2024) e **0.1.266** (febbraio 2025), entrambe con supporto Server 2022/2025 + Secure Boot. Le versioni "latest" su `https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/latest-virtio/` sono build di sviluppo, non firmate "stable": evitarle in produzione. Fonte canonica: [virtio-win-pkg-scripts releases](https://github.com/virtio-win/virtio-win-pkg-scripts/releases) + [Fedora repo](https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/), retrieved 2026-04-27.

> **Approfondimento — Q35 vs i440FX machine type per Windows Server.** Per Windows Server moderno (2019+), il machine type **Q35** e raccomandato perche: (1) supporta UEFI/OVMF nativamente; (2) usa PCI Express invece del legacy PCI di i440FX, abilitando piu di 32 device; (3) supporta vIOMMU (necessario per nested virt e per alcune feature di security come Credential Guard); (4) ha topologia PCIe coerente con hardware recente, importante per drivers che fanno ACPI introspection. Per Server 2012 R2/2016 con BIOS legacy e drivers KVM piu vecchi: i440FX puo essere piu safe. Conversione machine type richiede attenzione: `qm set --machine pc-q35-8.0` modifica il device tree visibile al guest, Windows registra "Hardware change detected" e puo richiedere riattivazione. Pin di una versione specifica (`pc-q35-8.1` invece di `q35` aliased) per evitare drift al prossimo upgrade Proxmox/QEMU. Fonte: [QEMU machine types — Q35 vs i440FX](https://www.qemu.org/docs/master/system/i386/pc.html), retrieved 2026-04-27.

> **Approfondimento — `qemu-img convert -W` parallelizza, `-p` mostra progresso.** Il flag `-W` abilita writes asincroni in parallelo (default 8 thread), accelerando la conversione di 2-4x su SSD/NVMe. Il flag `-p` mostra una barra di progresso ANSI con throughput corrente. Per VMDK di grandi dimensioni (> 500 GB) con conversione live (mentre la VM sorgente e ferma), considerare anche `-S 64k` (sparse output con cluster 64K) per qcow2 o `-o preallocation=metadata` per il caso preferito (allocato spazio metadati ma dati thin). Esempio completo: `qemu-img convert -p -W -m 16 -O qcow2 -o cluster_size=64k,preallocation=metadata source.vmdk dest.qcow2`. Fonte: [qemu-img(1) manpage](https://www.qemu.org/docs/master/tools/qemu-img.html), retrieved 2026-04-27.

> **Errore comune — BSOD 0x7B INACCESSIBLE_BOOT_DEVICE al primo boot.** Sintomo: la VM Windows si avvia su Proxmox e dopo il logo Windows va in BSOD `INACCESSIBLE_BOOT_DEVICE` (codice 0x0000007B). Causa: il driver `vioscsi` o `viostor` non era installato + abilitato come boot driver prima dello shutdown. Soluzione (offline registry edit): (1) Boot della VM da una ISO di Windows Server (rescue mode); (2) `regedit` → File → Load Hive → mount `C:\Windows\System32\config\SYSTEM`; (3) navigare a `HKLM\<mountname>\ControlSet001\Services\vioscsi` e impostare `Start = 0` (DWORD); (4) ripetere per `viostor`; (5) Unload Hive, riavvio. Soluzione preventiva: installare i driver dal `virtio-win-guest-tools.exe` *prima* dello shutdown su VMware. Soluzione alternativa: avviare temporaneamente la VM con controller `--scsihw lsi` (driver Windows nativo), installare vioscsi dentro Windows acceso, switchare a `virtio-scsi-single` con shutdown + edit config. Fonte: [Microsoft — Troubleshoot stop error 0x7B](https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/stop-error-0x7b-after-you-move-windows-to-a-new-hard-drive), retrieved 2026-04-27.

> **Errore comune — Snapshot di un Domain Controller dopo la migrazione.** Sintomo: dopo aver migrato un DC su Proxmox e aver applicato uno snapshot pre-migrazione "per sicurezza", la replica AD inizia a fallire con errori 8606, 8451 (lingering object) o 8438 (invalid USN). In casi gravi: tombstone reanimation, oggetti cancellati che riappaiono, autenticazioni Kerberos che falliscono in modo intermittente. Causa: AD usa USN (Update Sequence Number) e InvocationID (UUID per istanza di NTDS) per tracciare la replica. Uno snapshot riporta indietro USN e DSA (Directory Service Agent) ma il resto del dominio e avanzato; il DC ripristinato emette USN gia "consumati" dagli altri DC, che li ignorano (lingering objects). Soluzione: NON applicare snapshot a DC. Per rollback di un DC: demoteare con `dcpromo` (o `Uninstall-WindowsFeature AD-Domain-Services -IncludeManagementTools` su Server Core), reinstallare il ruolo DC da zero, ri-replicare. Soluzione preventiva: per Server 2012 R2+, AD ha "VM-Generation ID" che teoricamente protegge da rollback snapshot — ma solo se l'hypervisor lo espone correttamente al guest e il DC e in stato "USN rollback aware". QEMU/KVM espone VM-Generation ID via `--vmgenid auto`, ma e meglio non fidarsene e trattare i DC come immutabili post-cutover. Fonte: [Microsoft — Virtual DC and USN rollback](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/virtualized-domain-controller-architecture), retrieved 2026-04-27.

> **Errore comune — VMXNET3 driver residuo dopo conversione.** Sintomo: la NIC VirtIO funziona ma negli eventi si vedono errori "vmxnet3 service failed to start" ad ogni boot, oppure compaiono interfacce "ghost" in `Get-NetAdapter -IncludeHidden`. Causa: il driver vmxnet3 e ancora installato anche se l'hardware non c'e piu; Windows tenta di caricarlo. Soluzione: `pnputil /enum-drivers` per trovare gli `.inf` VMware (cercare `vmxnet`, `pvscsi`, `vmci`, `vmusbarbiter`, `vsock`); per ognuno: `pnputil /delete-driver oemNN.inf /uninstall /force`. Verificare con `Get-PnpDevice -Status Unknown` e disinstallare i device fantasma. Soluzione preventiva: prima dello shutdown su VMware, eseguire `VMwareToolsSetup.exe /c` (uninstall) o `MsiExec.exe /x {GUID}` se l'installer non e disponibile, poi pulire i driver con `pnputil`. Fonte: [Microsoft — pnputil command reference](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil-command-syntax), retrieved 2026-04-27.

> **Caso reale — Riattivazione Windows dopo cambio CPU e BIOS UUID.** Una farm di 30 VM Server 2019 e stata migrata da VMware (CPU Intel Xeon Gold 6248) a Proxmox (CPU AMD EPYC 7543). Tutte le VM hanno richiesto riattivazione (perdita "Digital License" basata su hash hardware). Soluzione adottata: (1) verificare disponibilita di KMS server interno o Microsoft Activation Service esposto al network di management; (2) per ogni VM, eseguire `slmgr /ato` (forzata riattivazione automatica); (3) per ~5 VM su 30, l'attivazione e fallita con error `0xC004F074` (KMS pool exhausted) — soluzione: aggiungere KMS host key extension via `slmgr /ipk <KMS-CLIENT-KEY>` poi `slmgr /ato`; (4) documentare nel runbook che ogni cambio CPU host richiede riattivazione e tenere disponibile il KMS host key per uso emergenza. Lezione: per workload Windows-heavy, preparare il path di riattivazione *prima* del cutover, non scoprirlo dopo. Fonte: [Microsoft — Volume Activation Management Tool (VAMT)](https://learn.microsoft.com/en-us/windows/deployment/volume-activation/volume-activation-management-tool), retrieved 2026-04-27.

> **Caso reale — RSC su VirtIO Net e prestazioni TCP degradate post-migrazione.** Un IIS server con ~5 Gbit/s di traffico HTTP ha mostrato latenza ad anelli (jitter di ~20-100ms) dopo la migrazione, anche se IOPS e CPU erano nei range. Causa: Receive Segment Coalescing (RSC) abilitato sulla NIC VirtIO Net interagiva male con un workload con molte connessioni keep-alive corte (HTTP/1.1). Su VMXNET3 il problema non si presentava. Soluzione: `Disable-NetAdapterRsc -Name "VirtIO Network Adapter"`; e impostare `Set-NetAdapterAdvancedProperty -Name "VirtIO Network Adapter" -DisplayName "Recv Segment Coalescing (IPv4)" -DisplayValue "Disabled"`. Per workload single-flow alto throughput (es. SMB transfer da PB), RSC e invece utile e va lasciato attivo. Lezione: il default VirtIO non e ottimale per ogni workload Windows; le advanced properties della NIC vanno configurate in base al pattern di traffico. Fonte: [Microsoft — Receive Segment Coalescing](https://learn.microsoft.com/en-us/windows-hardware/drivers/network/receive-segment-coalescing-rsc-), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — risolvi il BSOD 0x7B.** Un collega ti chiama: "ho migrato una VM Windows 2019 ma il primo boot va in BSOD INACCESSIBLE_BOOT_DEVICE. Che cosa devo fare?" Argomenta in 8-10 righe le 3 strade per recuperare la VM senza ripartire da capo: (a) modifica registry offline con regedit caricando l'hive SYSTEM; (b) boot temporaneo con controller `lsi` (driver nativo Windows), installazione vioscsi dentro Windows, switch a virtio-scsi-single; (c) recovery via Windows ISO + cmd + dism /online /add-driver. Indica per ognuna i comandi/passi chiave.

2. **Lab — preparare e migrare un Windows Server 2022 standalone.** Su una VM Server 2022 (puo essere Eval ISO Microsoft, 180 giorni) ospitata su VMware Workstation o ESXi: (a) installare i driver virtio-win 0.1.266 da `virtio-win-guest-tools.exe`; (b) verificare con `pnputil /enum-drivers | findstr vio`; (c) impostare `Start=0` per `vioscsi` via PowerShell `Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\vioscsi" -Name Start -Value 0`; (d) shutdown ordinato; (e) export OVA; (f) `qemu-img convert -p -W -O qcow2 disk.vmdk disk.qcow2`; (g) `qm create` + `qm importdisk` + boot; (h) verifica primo boot pulito; (i) installa qemu-ga.msi; (j) misura TPS su un benchmark di test (es. CrystalDiskMark via guest agent o RDP).

3. **Scenario — DC migration plan.** Hai 4 Domain Controller AD: DC01 (PDC, FSMO holder, Server 2019), DC02 (DC + DNS, Server 2019), DC03 (DC + DNS, Server 2022), DC04 (DC read-only, Server 2022). Argomenta in 15-20 righe il piano di migrazione: (a) ordine di migrazione (quale DC per primo? perche?); (b) trasferimento FSMO (quando? a chi?); (c) gestione del PDC time sync; (d) cosa fare se durante la migrazione di DC03 la replica fallisce; (e) verifica di salute post-migrazione (`dcdiag`, `repadmin /replsummary`, `nltest /dsgetdc`); (f) rollback plan se il dominio mostra inconsistenze.

4. **Stretch — automazione qm import + driver inject.** Scrivere uno script PowerShell + bash che, dato un VMDK + un OVF: (1) parsa OVF per estrarre OS type, RAM, CPU; (2) genera config qm appropriata (machine type, scsihw, ostype); (3) esegue `qemu-img convert` con flag ottimali; (4) crea VM, importa disco, configura boot order, EFI disk se serve; (5) **prima del primo boot**, monta il disco offline tramite `nbd` o `qemu-nbd`, edita il registry hive con `chntpw` o `hivex` per impostare `Start=0` su vioscsi; (6) avvia VM e attende segnalazione del guest agent. Bonus: rollback automatico se il guest non risponde entro 5 min.

5. **Stretch — confronto prestazioni VMXNET3 vs VirtIO Net.** Su due VM Server 2022 identiche (una su VMware con VMXNET3, una su Proxmox con VirtIO Net), eseguire benchmark di rete con: (a) `iperf3` TCP single stream; (b) `iperf3` TCP 8 stream paralleli; (c) test reale: scaricare un file 100 GB via SMB; (d) test latenza: `ping -t -l 1500` su rete dedicata. Confrontare throughput, CPU usage del guest (`Get-Counter "\Processor(_Total)\% Processor Time"`), e jitter. Documentare i 2-3 advanced settings VirtIO che fanno la differenza maggiore.

6. **Stretch — automazione riattivazione post-migrazione.** Scrivere un GPO o uno script PowerShell che, eseguito al primo boot post-migrazione (Task Scheduler `At startup`): (1) verifica `slmgr /xpr` lo stato attivazione; (2) se non attivo, esegue `slmgr /ato` (KMS); (3) se KMS fallisce, prova VAMT; (4) loggia il risultato in un eventlog custom; (5) invia notifica via webhook (es. Teams, Slack) al team operations. Bonus: schedulato anche come task ricorrente settimanale.

## Auto-valutazione

1. Quale chiave di registro va impostata a `Start = 0` per il driver `vioscsi` e perche?
2. Differenza tra UEFI/OVMF e SeaBIOS in QEMU; quando preferire uno o l'altro per Windows Server?
3. Q35 machine type vs i440FX: quali 4 vantaggi pratici di Q35 per Server 2019+?
4. `qemu-img convert -W`: cosa fa il flag e perche accelera la conversione?
5. Cosa succede se applichi uno snapshot a un DC migrato e perche e tossico?
6. Quale comando PowerShell trasferisce tutti i ruoli FSMO a un altro DC?
7. `slmgr /ato` vs `slmgr /ipk`: quando usare ognuno e che ordine seguire?
8. VirtIO Net Receive Segment Coalescing (RSC): in quale scenario va disabilitato?
9. Quale ISO contiene il driver `qemu-ga.msi` e dove si scarica la versione stabile?
10. `pnputil /delete-driver oemNN.inf /uninstall` rimuove un driver: come trovare l'NN corretto?
11. Per il PDC emulator, quale e la fonte autorevole di tempo e perche non il QEMU host-time?
12. Qual e il modo corretto di rollbackare un DC migrato se serve tornare a VMware?

## Letture primarie consigliate

- Proxmox VE Wiki — Windows VirtIO Drivers. https://pve.proxmox.com/wiki/Windows_VirtIO_Drivers (retrieved 2026-04-27).
- Proxmox VE Wiki — QEMU Guest Agent. https://pve.proxmox.com/wiki/Qemu-guest-agent (retrieved 2026-04-27).
- Proxmox VE Wiki — Migration of servers to Proxmox VE. https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE (retrieved 2026-04-27).
- Fedora — virtio-win stable releases. https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/ (retrieved 2026-04-27).
- virtio-win-pkg-scripts — releases (GitHub). https://github.com/virtio-win/virtio-win-pkg-scripts/releases (retrieved 2026-04-27).
- QEMU — Machine types Q35 vs i440FX. https://www.qemu.org/docs/master/system/i386/pc.html (retrieved 2026-04-27).
- QEMU — qemu-img(1) manpage. https://www.qemu.org/docs/master/tools/qemu-img.html (retrieved 2026-04-27).
- Microsoft Learn — Active Directory Forest Recovery Guide. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/ad-forest-recovery-guide (retrieved 2026-04-27).
- Microsoft Learn — FSMO Roles. https://learn.microsoft.com/en-us/troubleshoot/windows-server/identity/fsmo-roles (retrieved 2026-04-27).
- Microsoft Learn — Virtualized Domain Controller architecture. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/virtualized-domain-controller-architecture (retrieved 2026-04-27).
- Microsoft Learn — KMS Client Setup Keys. https://learn.microsoft.com/en-us/windows-server/get-started/kms-client-activation-keys (retrieved 2026-04-27).
- Microsoft Learn — Volume Activation Overview. https://learn.microsoft.com/en-us/windows-server/get-started/volume-activation-overview (retrieved 2026-04-27).
- Microsoft Learn — Troubleshoot stop error 0x7B. https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/stop-error-0x7b-after-you-move-windows-to-a-new-hard-drive (retrieved 2026-04-27).
- Microsoft Learn — pnputil command syntax. https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil-command-syntax (retrieved 2026-04-27).
- Microsoft Learn — Windows Time Service tools (`w32tm`). https://learn.microsoft.com/en-us/windows-server/networking/windows-time-service/windows-time-service-tools-and-settings (retrieved 2026-04-27).
- Red Hat — VirtIO Drivers for Microsoft Windows. https://access.redhat.com/articles/2488201 (retrieved 2026-04-27).
- chntpw / hivex — offline Windows registry editing. https://github.com/libguestfs/hivex (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 09.1 — `migrazione-applicazioni-stateful.md`: Windows Server applicativi (Exchange, SharePoint) come applicazioni stateful.
- Modulo 09.2 — `migrazione-database-postgresql-mysql.md`: per SQL Server, applicare gli stessi principi VM-config (`--balloon 0`, `cache=none`).
- Modulo 09.3 — `migrazione-high-io-workloads.md`: tuning VM per Windows DB/file server.
- Modulo 06.1 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/strategie-metodi-migrazione.md`: scelta cold/warm/live per Windows Server.
- Modulo 06.2 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/migrazione-con-virt-v2v.md`: alternativa virt-v2v per Windows (se virtio non disponibile pre-shutdown).
- Modulo 07.1 — `../07-MIGRAZIONE-NETWORKING/ip-planning-dns-dhcp-firewall.md`: pianificazione cutover IP/DNS per AD.
- Modulo 08.1 — `../08-MIGRAZIONE-STORAGE/conversione-vmdk-qcow2-raw.md`: conversione del disco di sistema Windows.
- Modulo 12.x — `../12-SICUREZZA-E-COMPLIANCE/autenticazione-ldap-ad-proxmox.md`: integrazione AD con Proxmox post-migrazione.
- Modulo 17.x — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-driver-e-dispositivi.md`: troubleshooting driver Windows post-migrazione.

## Glossario locale

| Termine | Definizione |
|---|---|
| **VirtIO** | Standard di paravirtualizzazione per guest Linux/Windows; offre performance native. |
| **vioscsi** | Driver VirtIO SCSI per Windows; obbligatorio per disco di boot su virtio-scsi(-single). |
| **viostor** | Driver VirtIO Block (alternativa a vioscsi); in disuso a favore di vioscsi. |
| **NetKVM** | Driver VirtIO Net per Windows. |
| **balloon** | Driver per memory ballooning (memoria dinamica). |
| **vioserial** | Driver VirtIO Serial; richiesto per QEMU Guest Agent. |
| **qxl** | Driver display QXL per accelerazione grafica QEMU. |
| **PVSCSI** | Paravirtual SCSI controller VMware (sostituito da vioscsi su Proxmox). |
| **VMXNET3** | NIC paravirtualizzata VMware (sostituita da VirtIO Net su Proxmox). |
| **e1000** | NIC emulata standard Intel; usata come fallback compatibile universalmente. |
| **VMware Tools** | Suite di driver e agent VMware (sostituita da QEMU Guest Agent + virtio-win). |
| **QEMU Guest Agent** | Agent in-guest per Proxmox (qemu-ga.msi); espone comandi (shutdown, fstrim, freeze). |
| **`virtio-win.iso`** | ISO con tutti i driver VirtIO Windows + qemu-ga + tools; rilasciata da progetto Fedora. |
| **OVMF / TianoCore** | Firmware UEFI per QEMU; alternativa a SeaBIOS (BIOS legacy). |
| **SeaBIOS** | Firmware BIOS legacy per QEMU; default per VM senza UEFI. |
| **Q35** | Machine type QEMU moderno con PCI Express, vIOMMU, supporto UEFI. |
| **i440FX** | Machine type QEMU legacy con PCI; default storico. |
| **TPM 2.0 emulato** | Trusted Platform Module software (`swtpm`); richiesto per Server 2022 Secure Boot. |
| **`--ostype winXX`** | Hint a Proxmox sulla famiglia OS guest; influenza alcune scelte default. |
| **BSOD 0x7B (INACCESSIBLE_BOOT_DEVICE)** | Bug check Windows: il kernel non puo accedere al disco di boot. |
| **`pnputil`** | Tool Windows per gestire driver store; usato per uninstall mirato. |
| **FSMO** | Flexible Single-Master Operations; 5 ruoli AD (Schema, DomainNaming, RID, PDC, Infrastructure). |
| **PDC Emulator** | Ruolo FSMO; fonte autorevole di tempo per il dominio. |
| **`dcdiag`** | Tool Microsoft per diagnosi salute Domain Controller. |
| **`repadmin`** | Tool Microsoft per diagnostica replica AD. |
| **InvocationID** | UUID per istanza NTDS di un DC; cambia se il DC e ripristinato da snapshot. |
| **USN (Update Sequence Number)** | Numero seq replica AD; il rollback via snapshot causa USN rollback. |
| **Lingering object** | Oggetto AD presente su un DC ma cancellato sugli altri; tipicamente da USN rollback. |
| **VM-Generation ID** | Identifier QEMU/KVM/Hyper-V per detect snapshot rollback (Server 2012 R2+). |
| **`slmgr.vbs`** | Script Windows per gestione licensing (`/ato`, `/ipk`, `/xpr`, `/dlv`). |
| **KMS (Key Management Service)** | Server interno per attivazione volume Windows. |
| **AVMA (Automatic VM Activation)** | Attivazione gratuita per VM Windows su host Hyper-V Datacenter; non funziona su KVM. |
| **MAK (Multiple Activation Key)** | Chiave volume Microsoft attivabile direttamente con MS (no KMS). |
| **RSS (Receive Side Scaling)** | Feature NIC che distribuisce interrupt su piu CPU; abilitare per high-throughput. |
| **RSC (Receive Segment Coalescing)** | Feature NIC che combina segmenti TCP in receive; talvolta dannoso per workload latenza-bound. |
| **`w32tm`** | Tool Windows per Windows Time Service. |
