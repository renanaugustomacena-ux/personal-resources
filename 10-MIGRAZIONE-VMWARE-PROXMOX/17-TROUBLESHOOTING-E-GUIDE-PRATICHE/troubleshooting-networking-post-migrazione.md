# Troubleshooting Networking Post-Migrazione

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 7 — Day-2 operations · Modulo 17.3 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 04 (architettura networking Proxmox); modulo 07 (cutover networking); fluenza con `ip`, `tcpdump`, `ethtool`, VLAN concepts.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. diagnosticare problemi di connettivita post-migrazione: VM non raggiungibile, IP duplicati, DNS rotti, MAC table dello switch stale;
> 2. risolvere problemi MTU mismatch (jumbo frames mal configurate), VLAN tagging errato (PVID, trunk vs access);
> 3. troubleshooting bonding (LACP not negotiated), STP loops, broadcast storm;
> 4. usare `tcpdump`, `tshark`, switch port mirror per packet capture diagnostico.
> **Tempo stimato:** lettura 60-90 min · uso reattivo
> **Livello:** competent → proficient (Dreyfus 3 → 4); networking expertise
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **OSI layer-by-layer diagnosis.** L1 (cavo, link), L2 (MAC, VLAN), L3 (IP, routing), L4 (port, firewall), L7 (app). Mai saltare livelli.
2. **MAC address change post-migrazione disorienta MAC table degli switch.** Per 1-2 minuti ARP/MAC table prendono tempo per imparare il nuovo MAC. Forzare via `arping -U` o riavvio interfaccia switch.
3. **DNS cache TTL e nemico durante cutover.** TTL 5min su record critico significa 5min di "vecchio IP" in caching DNS. Pre-abbassare TTL 24h prima del cutover.

---

## Indice

1. [Panoramica Problemi di Rete Post-Migrazione](#panoramica)
2. [NIC Non Rilevata](#nic-non-rilevata)
3. [MAC Address Errato](#mac-address-errato)
4. [IP Statico su Interfaccia Sbagliata](#ip-statico-interfaccia-sbagliata)
5. [Regole udev Persistent Net (Linux)](#regole-udev)
6. [Windows Ghost NIC Adapters](#windows-ghost-nic)
7. [VLAN Non Funzionante](#vlan-non-funzionante)
8. [MTU Mismatch](#mtu-mismatch)
9. [DNS Resolution Failure](#dns-resolution-failure)
10. [Firewall Blocking](#firewall-blocking)
11. [Bonding e Team NIC Non Funzionante](#bonding-non-funzionante)
12. [OVS Bridge Issues](#ovs-bridge-issues)
13. [Comandi Diagnostici di Riferimento](#comandi-diagnostici)
14. [Flowchart di Troubleshooting Sistematico](#flowchart)

---

## Panoramica Problemi di Rete Post-Migrazione {#panoramica}

I problemi di rete dopo una migrazione da VMware a Proxmox sono tra i piu comuni e possono manifestarsi in modi diversi. Le cause principali includono:

- **Cambio hardware virtuale**: VMware utilizza vmxnet3 o e1000, Proxmox utilizza VirtIO-net o e1000 emulato
- **MAC address diverso**: il nuovo NIC virtuale ha un MAC address diverso da quello originale
- **Regole udev residue**: Linux potrebbe assegnare un nome diverso all'interfaccia di rete
- **Configurazione statica**: gli IP statici sono legati al nome dell'interfaccia che potrebbe essere cambiato
- **Driver mancanti**: senza il driver VirtIO-net, la NIC paravirtualizzata non viene rilevata

### Impatto sulla Produzione

I problemi di rete sono particolarmente critici perche:
- La VM potrebbe risultare completamente irraggiungibile
- I servizi dipendenti dalla rete (database, web server, DNS) si fermano
- Il monitoraggio non riceve piu metriche dalla VM
- I backup via rete falliscono

---

## NIC Non Rilevata {#nic-non-rilevata}

### Sintomi

- `ip link show` mostra solo l'interfaccia `lo` (loopback)
- `lspci` non mostra dispositivi di rete
- Windows Device Manager non mostra alcun network adapter
- La VM non ha connettivita di rete

### Causa 1: Driver VirtIO-net Mancante

La NIC di tipo `virtio` richiede il driver VirtIO-net nel sistema operativo guest.

**Diagnostica Linux:**

```bash
# Verificare se il dispositivo PCI e presente
lspci | grep -i net
# Se appare "Red Hat, Inc. Virtio network device" ma nessuna interfaccia:
# Il dispositivo e presente ma il driver non e caricato

# Verificare il modulo
lsmod | grep virtio_net
# Se vuoto, il modulo non e caricato

# Tentare il caricamento
modprobe virtio_net
# Se fallisce: il modulo non e disponibile nel kernel
```

**Soluzione Linux:**

```bash
# Se il modulo esiste ma non e caricato
modprobe virtio_net

# Verificare
ip link show
# Dovrebbe apparire una nuova interfaccia (es. ens18, eth0)

# Rendere permanente
echo "virtio_net" >> /etc/modules-load.d/virtio.conf

# Se il modulo non esiste, ricostruire initramfs (da live CD se necessario)
echo "virtio_net" >> /etc/initramfs-tools/modules  # Debian/Ubuntu
update-initramfs -u -k all

# Per RHEL/CentOS
echo 'add_drivers+=" virtio_net "' > /etc/dracut.conf.d/virtio-net.conf
dracut --force
```

**Soluzione Windows:**

```bash
# Su Proxmox: cambiare temporaneamente a e1000 (non richiede driver)
qm set <vmid> -net0 e1000,bridge=vmbr0

# Avviare Windows, installare driver VirtIO
# Poi tornare a virtio:
qm set <vmid> -net0 virtio,bridge=vmbr0
```

### Causa 2: Bridge Proxmox Non Configurato

```bash
# Verificare che il bridge esista sul nodo Proxmox
ip link show vmbr0
brctl show vmbr0

# Verificare la configurazione della VM
qm config <vmid> | grep net

# Output atteso:
# net0: virtio=XX:XX:XX:XX:XX:XX,bridge=vmbr0

# Verificare che il bridge sia collegato all'interfaccia fisica
cat /etc/network/interfaces
# Dovrebbe contenere:
# auto vmbr0
# iface vmbr0 inet static
#     address 10.0.0.1/24
#     bridge-ports eno1
#     bridge-stp off
#     bridge-fd 0
```

### Causa 3: Firewall Proxmox che Blocca il Traffico

```bash
# Verificare lo stato del firewall Proxmox
pve-firewall status

# Verificare le regole per la VM
cat /etc/pve/firewall/<vmid>.fw

# Disabilitare temporaneamente per test
pve-firewall stop
# ATTENZIONE: questo disabilita il firewall per TUTTE le VM

# Oppure disabilitare solo per la VM specifica
qm set <vmid> -firewall 0
# Questo va impostato sull'interfaccia di rete:
# net0: virtio=XX:XX:XX:XX:XX:XX,bridge=vmbr0,firewall=0
```

---

## MAC Address Errato {#mac-address-errato}

### Problema

Dopo la migrazione, la VM riceve un nuovo MAC address che non corrisponde a quello originale. Questo causa problemi con:
- DHCP lease (il server DHCP assegna un IP diverso)
- Licenze software legate al MAC
- Regole firewall basate su MAC
- ARP table degli switch e dei router

### Diagnostica

```bash
# Linux: verificare il MAC address attuale
ip link show
# Confrontare con il MAC originale dalla configurazione VMware

# Windows:
ipconfig /all
# Oppure:
getmac /v
```

### Soluzione: Impostare il MAC Address Originale

```bash
# Su Proxmox: impostare il MAC address della VM VMware originale
# Trovare il MAC originale dal file VMX:
# grep -i "ethernet0.generatedAddress" /vmfs/volumes/datastore1/<vm>/<vm>.vmx

# Impostare su Proxmox
qm set <vmid> -net0 virtio=00:50:56:XX:XX:XX,bridge=vmbr0

# Il formato MAC VMware e tipicamente:
# 00:50:56:XX:XX:XX (VMware OUI assegnato)
# 00:0C:29:XX:XX:XX (VMware OUI generato)

# ATTENZIONE: Proxmox usa di default il range MAC:
# BC:24:11:XX:XX:XX (OUI Proxmox)
```

### Considerazioni sul MAC Address

```bash
# Verificare che non ci siano conflitti MAC sulla rete
# Dal router/switch:
show mac address-table | include <mac>

# Dal nodo Proxmox, verificare i MAC di tutte le VM:
qm list | awk '{print $1}' | while read vmid; do
    echo "VM $vmid:"
    qm config $vmid 2>/dev/null | grep "net[0-9]"
done
```

---

## IP Statico su Interfaccia Sbagliata {#ip-statico-interfaccia-sbagliata}

### Problema

La configurazione di rete fa riferimento a un'interfaccia che non esiste piu. Su VMware l'interfaccia poteva chiamarsi `ens192` o `ens160`, mentre su Proxmox potrebbe chiamarsi `ens18` o `eth0`.

### Diagnostica Linux

```bash
# Vedere le interfacce disponibili
ip link show

# Vedere la configurazione corrente
ip addr show

# Confrontare con la configurazione salvata
# Debian/Ubuntu:
cat /etc/network/interfaces
cat /etc/netplan/*.yaml 2>/dev/null

# RHEL/CentOS 7:
cat /etc/sysconfig/network-scripts/ifcfg-*

# RHEL/Rocky/Alma 8+:
nmcli connection show
nmcli device status
```

### Soluzione Debian/Ubuntu (interfaces file)

```bash
# Identificare il nuovo nome dell'interfaccia
ip link show
# Esempio: ens18 (tipico su Proxmox)

# Modificare /etc/network/interfaces
# Vecchia configurazione:
# auto ens192
# iface ens192 inet static
#     address 10.0.0.100/24
#     gateway 10.0.0.1

# Nuova configurazione:
cat > /etc/network/interfaces << 'EOF'
auto lo
iface lo inet loopback

auto ens18
iface ens18 inet static
    address 10.0.0.100/24
    gateway 10.0.0.1
    dns-nameservers 10.0.0.1 8.8.8.8
EOF

# Riavviare il networking
systemctl restart networking
# Oppure:
ifdown ens18 && ifup ens18
```

### Soluzione Ubuntu (Netplan)

```bash
# Identificare il nome dell'interfaccia
ip link show

# Modificare il file Netplan
cat > /etc/netplan/01-netcfg.yaml << 'EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    ens18:
      addresses:
        - 10.0.0.100/24
      routes:
        - to: default
          via: 10.0.0.1
      nameservers:
        addresses:
          - 10.0.0.1
          - 8.8.8.8
EOF

# Applicare
netplan apply
```

### Soluzione RHEL/CentOS 7

```bash
# Rinominare il file di configurazione
cd /etc/sysconfig/network-scripts/
mv ifcfg-ens192 ifcfg-ens18

# Modificare il contenuto
sed -i 's/ens192/ens18/g' ifcfg-ens18

# Rimuovere l'UUID e HWADDR vecchi (verranno rigenerati)
sed -i '/^UUID=/d' ifcfg-ens18
sed -i '/^HWADDR=/d' ifcfg-ens18

# Riavviare il networking
systemctl restart network
```

### Soluzione RHEL/Rocky 8+/9 (NetworkManager)

```bash
# Listare le connessioni
nmcli connection show

# Se la vecchia connessione e ancora presente
nmcli connection delete "ens192"

# Creare una nuova connessione
nmcli connection add type ethernet \
    con-name "ens18" \
    ifname ens18 \
    ipv4.addresses "10.0.0.100/24" \
    ipv4.gateway "10.0.0.1" \
    ipv4.dns "10.0.0.1 8.8.8.8" \
    ipv4.method manual \
    connection.autoconnect yes

# Attivare
nmcli connection up "ens18"
```

### Soluzione Windows

```powershell
# Identificare gli adattatori di rete
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, MacAddress

# Se l'adattatore e rilevato ma ha configurazione errata:
# Riconfigurare IP statico
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress "10.0.0.100" -PrefixLength 24 -DefaultGateway "10.0.0.1"
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses ("10.0.0.1","8.8.8.8")
```

---

## Regole udev Persistent Net (Linux) {#regole-udev}

### Problema

Le distribuzioni Linux meno recenti (CentOS 6, Ubuntu 14.04, Debian 8 e precedenti) utilizzavano regole udev per assegnare nomi persistenti alle interfacce di rete basandosi sul MAC address. Dopo la migrazione, il nuovo MAC address causa la creazione di una nuova interfaccia (es. `eth1` invece di `eth0`).

### Diagnostica

```bash
# Verificare le regole udev
cat /etc/udev/rules.d/70-persistent-net.rules

# Output problematico tipico:
# SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{address}=="00:50:56:xx:xx:xx",
#   ATTR{type}=="1", KERNEL=="eth*", NAME="eth0"
# SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{address}=="bc:24:11:yy:yy:yy",
#   ATTR{type}=="1", KERNEL=="eth*", NAME="eth1"
# La prima riga e la vecchia NIC VMware, la seconda e la nuova NIC Proxmox
```

### Soluzione

```bash
# Rimuovere le regole udev persistenti
rm -f /etc/udev/rules.d/70-persistent-net.rules
rm -f /etc/udev/rules.d/75-persistent-net-generator.rules

# Rigenerare le regole (facoltativo, avverra al prossimo boot)
udevadm trigger --subsystem-match=net

# Riavviare per applicare
reboot

# Dopo il riavvio, l'interfaccia dovrebbe essere assegnata correttamente
ip link show
```

### Nomi Interfacce Predictable (systemd)

Le distribuzioni moderne usano nomi di interfaccia "predictable" basati sulla posizione PCI:

```bash
# Schema di naming tipico su Proxmox:
# ens18  - PCIe slot 18 (primo NIC VirtIO)
# ens19  - PCIe slot 19 (secondo NIC VirtIO)
# enp0s18 - PCI bus 0, slot 18

# Schema di naming tipico su VMware:
# ens160 - PCIe slot 160
# ens192 - PCIe slot 192
# ens224 - PCIe slot 224

# Il cambio di nome e dovuto alla diversa posizione PCI del dispositivo
# virtualizzato da VMware vs KVM/QEMU

# Per forzare il naming classico (eth0, eth1):
# Aggiungere al kernel command line:
# net.ifnames=0 biosdevname=0
# In /etc/default/grub:
GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0"
# Poi: update-grub && reboot
```

---

## Windows Ghost NIC Adapters {#windows-ghost-nic}

### Problema

Dopo la migrazione, Windows potrebbe mostrare "adapter fantasma" residui dalla configurazione VMware, che possono causare conflitti IP, impossibilita di configurare la rete, e DHCP non funzionante.

### Diagnostica

```powershell
# Mostrare TUTTI i dispositivi (inclusi quelli nascosti/non presenti)
# Da prompt dei comandi elevato:
set devmgr_show_nonpresent_devices=1
devmgmt.msc
# In Device Manager: View > Show hidden devices
# Sotto "Network adapters" appariranno le NIC fantasma (grigie)
```

### Soluzione

```powershell
# Rimuovere i ghost adapters da PowerShell
# Listare tutti gli adapter di rete (inclusi non presenti)
Get-PnpDevice -Class Net | Where-Object {$_.Status -eq "Unknown"} |
    Select-Object InstanceId, FriendlyName, Status

# Rimuovere i ghost adapters
Get-PnpDevice -Class Net | Where-Object {$_.Status -eq "Unknown"} |
    ForEach-Object {
        Write-Host "Rimozione: $($_.FriendlyName)"
        & pnputil /remove-device $_.InstanceId
    }

# Metodo alternativo con devcon (Windows SDK)
devcon remove =net @*vmxnet*
devcon remove =net @*vmware*

# Dopo la rimozione, resettare la configurazione di rete
netsh interface ip reset
netsh winsock reset

# Riavviare
Restart-Computer
```

### Pulizia Registro di Rete Windows

```powershell
# Se rimangono configurazioni IP residue, pulire il registro
# ATTENZIONE: fare backup del registro prima

# Rimuovere le interfacce di rete obsolete dal registro
$adapters = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
foreach ($adapter in $adapters) {
    $props = Get-ItemProperty $adapter.PSPath
    if ($props.IPAddress -and $props.IPAddress -ne "0.0.0.0") {
        Write-Host "Interfaccia: $($adapter.PSChildName) - IP: $($props.IPAddress)"
    }
}
```

---

## VLAN Non Funzionante {#vlan-non-funzionante}

### Configurazione VLAN su Proxmox

Le VLAN possono essere configurate a diversi livelli:

```bash
# Metodo 1: VLAN-aware bridge (consigliato)
# In /etc/network/interfaces:
auto vmbr0
iface vmbr0 inet manual
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094

# Configurazione VM con VLAN tag:
qm set <vmid> -net0 virtio,bridge=vmbr0,tag=100

# Metodo 2: Bridge dedicato per VLAN
auto eno1.100
iface eno1.100 inet manual

auto vmbr100
iface vmbr100 inet manual
    bridge-ports eno1.100
    bridge-stp off
    bridge-fd 0

# VM senza tag (il bridge gestisce la VLAN):
qm set <vmid> -net0 virtio,bridge=vmbr100
```

### Diagnostica VLAN

```bash
# Verificare che il bridge sia VLAN-aware
bridge vlan show dev vmbr0

# Verificare il tag VLAN della VM
qm config <vmid> | grep net

# Verificare il traffico VLAN
tcpdump -i vmbr0 -e -n vlan 100

# Verificare le VLAN sull'interfaccia fisica
cat /proc/net/vlan/config
ip -d link show eno1.100

# Verificare che lo switch fisico sia configurato per trunk/tagged
# (dipende dal vendor dello switch)
```

### Problemi Comuni VLAN

```bash
# Problema: VM su VLAN 100 non raggiunge il gateway
# Verificare 1: il bridge e VLAN-aware
bridge vlan show

# Verificare 2: la porta trunk sullo switch e configurata
# Verificare 3: il tag VLAN e corretto nella config VM

# Problema: trunk VLAN non funziona dentro la VM
# Per passare VLAN tagged traffic dentro la VM:
qm set <vmid> -net0 virtio,bridge=vmbr0,trunks="100;200;300"
# Questo permette alla VM di gestire internamente le VLAN
```

---

## MTU Mismatch {#mtu-mismatch}

### Problema

Se la rete utilizza Jumbo Frames (MTU > 1500) o se c'e un mismatch di MTU tra i diversi segmenti di rete, possono verificarsi perdita di pacchetti, prestazioni degradate, o connessioni che funzionano solo parzialmente.

### Diagnostica

```bash
# Verificare MTU su tutte le interfacce del nodo Proxmox
ip link show | grep mtu

# Verificare MTU dentro la VM (Linux)
ip link show | grep mtu

# Verificare MTU dentro la VM (Windows)
netsh interface ipv4 show subinterfaces

# Test con ping di pacchetti grandi (Linux)
ping -M do -s 1472 <gateway>    # MTU 1500 (1472 + 28 header)
ping -M do -s 8972 <gateway>    # MTU 9000 (8972 + 28 header)
# Se il ping fallisce con "message too long", l'MTU e troppo basso

# Test con ping di pacchetti grandi (Windows)
ping -f -l 1472 <gateway>
```

### Soluzione

```bash
# Impostare MTU sul bridge Proxmox
# In /etc/network/interfaces:
auto vmbr0
iface vmbr0 inet static
    address 10.0.0.1/24
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    mtu 9000

auto eno1
iface eno1 inet manual
    mtu 9000

# Applicare
ifreload -a

# Dentro la VM Linux:
ip link set ens18 mtu 9000
# Per renderlo permanente, modificare la configurazione di rete

# Dentro la VM Windows:
netsh interface ipv4 set subinterface "Ethernet" mtu=9000 store=persistent
# Oppure da PowerShell:
Set-NetAdapterAdvancedProperty -Name "Ethernet" -RegistryKeyword "*JumboPacket" -RegistryValue "9014"
```

---

## DNS Resolution Failure {#dns-resolution-failure}

### Diagnostica

```bash
# Linux
cat /etc/resolv.conf
systemd-resolve --status 2>/dev/null || resolvectl status 2>/dev/null

# Test di risoluzione
nslookup google.com
dig google.com
host google.com

# Verificare raggiungibilita del DNS server
ping <dns-server-ip>
nc -zv <dns-server-ip> 53
dig @<dns-server-ip> google.com

# Windows
ipconfig /all | findstr DNS
nslookup google.com
```

### Soluzioni Comuni

```bash
# Linux: resolv.conf sovrascritto
# Se il file e un symlink a systemd-resolved:
ls -la /etc/resolv.conf

# Configurare DNS con systemd-resolved
cat > /etc/systemd/resolved.conf << 'EOF'
[Resolve]
DNS=10.0.0.1 8.8.8.8
FallbackDNS=8.8.4.4
EOF
systemctl restart systemd-resolved

# Oppure configurazione diretta (senza systemd-resolved)
cat > /etc/resolv.conf << 'EOF'
nameserver 10.0.0.1
nameserver 8.8.8.8
search example.com
EOF

# Windows: flush DNS cache
ipconfig /flushdns
# Reimpostare DNS
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses ("10.0.0.1","8.8.8.8")
```

---

## Firewall Blocking {#firewall-blocking}

### Linux: iptables/nftables

```bash
# Verificare regole firewall attive
iptables -L -n -v
iptables -L -n -v -t nat

# Per nftables (distribuzioni piu recenti):
nft list ruleset

# firewalld (RHEL/CentOS/Rocky):
firewall-cmd --list-all
firewall-cmd --list-all-zones

# ufw (Ubuntu):
ufw status verbose

# Disabilitare temporaneamente per test
systemctl stop firewalld  # RHEL/CentOS
ufw disable               # Ubuntu
iptables -F               # Flush tutte le regole (ATTENZIONE)
```

### Windows Firewall

```powershell
# Verificare stato firewall
Get-NetFirewallProfile | Select-Object Name, Enabled

# Disabilitare temporaneamente per test
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

# Riabilitare
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# Verificare regole che bloccano
Get-NetFirewallRule | Where-Object {$_.Action -eq "Block" -and $_.Enabled -eq "True"} |
    Select-Object DisplayName, Direction, Action
```

---

## Bonding e Team NIC Non Funzionante {#bonding-non-funzionante}

### Problema

Se la VM su VMware aveva NIC teaming configurato, questa configurazione potrebbe non funzionare correttamente su Proxmox perche le interfacce fisiche sono cambiate.

### Linux Bonding

```bash
# Verificare lo stato del bonding
cat /proc/net/bonding/bond0

# Se il bonding fa riferimento a interfacce vecchie (ens192, ens224):
# Aggiornare la configurazione

# Debian/Ubuntu con /etc/network/interfaces:
auto bond0
iface bond0 inet static
    address 10.0.0.100/24
    gateway 10.0.0.1
    bond-slaves ens18 ens19
    bond-mode active-backup
    bond-miimon 100
    bond-primary ens18

# RHEL/CentOS con NetworkManager:
nmcli connection add type bond \
    con-name bond0 \
    ifname bond0 \
    bond.options "mode=active-backup,miimon=100"
nmcli connection add type ethernet \
    slave-type bond \
    con-name bond0-slave1 \
    ifname ens18 \
    master bond0
nmcli connection add type ethernet \
    slave-type bond \
    con-name bond0-slave2 \
    ifname ens19 \
    master bond0
nmcli connection up bond0
```

### Configurazione Corretta su Proxmox

```bash
# Per il bonding e preferibile configurarlo a livello Proxmox
# piuttosto che dentro la VM

# Bonding sul nodo Proxmox (/etc/network/interfaces):
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-miimon 100
    bond-mode 802.3ad
    bond-xmit-hash-policy layer3+4

auto vmbr0
iface vmbr0 inet static
    address 10.0.0.1/24
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0

# La VM ha una singola NIC virtuale connessa al bridge
# Il bonding e trasparente per la VM
qm set <vmid> -net0 virtio,bridge=vmbr0
```

---

## OVS Bridge Issues {#ovs-bridge-issues}

### Diagnostica Open vSwitch

```bash
# Verificare che OVS sia installato e in esecuzione
systemctl status openvswitch-switch
ovs-vsctl show

# Verificare i bridge OVS
ovs-vsctl list-br

# Verificare le porte di un bridge
ovs-vsctl list-ports vmbr0

# Verificare i flussi
ovs-ofctl dump-flows vmbr0

# Problemi comuni:
# 1. OVS non avviato
systemctl start openvswitch-switch

# 2. Bridge non creato
ovs-vsctl add-br vmbr0
ovs-vsctl add-port vmbr0 eno1

# 3. VLAN non configurata
ovs-vsctl set port <vm-port> tag=100
```

### Migrazione da Linux Bridge a OVS

```bash
# Se si desidera migrare a OVS per funzionalita avanzate

# 1. Installare OVS
apt install openvswitch-switch  # Debian/Ubuntu

# 2. Configurare in /etc/network/interfaces
auto vmbr0
iface vmbr0 inet static
    address 10.0.0.1/24
    ovs_type OVSBridge
    ovs_ports eno1

auto eno1
iface eno1 inet manual
    ovs_bridge vmbr0
    ovs_type OVSPort

# 3. Aggiornare la configurazione delle VM
# (il nome del bridge resta lo stesso, qm non richiede modifiche)
```

---

## Comandi Diagnostici di Riferimento {#comandi-diagnostici}

### Comandi ip

```bash
# Interfacce e indirizzi
ip link show                    # Lista interfacce
ip addr show                    # Lista indirizzi IP
ip addr show ens18              # Dettagli singola interfaccia
ip route show                   # Tabella di routing
ip route get 10.0.0.1           # Come viene raggiunto un IP
ip neigh show                   # ARP table (neighbour cache)

# Statistiche
ip -s link show ens18           # Statistiche interfaccia
# TX/RX bytes, packets, errors, dropped
```

### Comandi ss (Socket Statistics)

```bash
# Connessioni attive
ss -tulnp                       # TCP/UDP listening con PID
ss -s                           # Statistiche riassuntive
ss -t state established         # Solo connessioni stabilite
ss -t dst 10.0.0.1              # Connessioni verso un IP specifico
```

### tcpdump

```bash
# Cattura traffico su un'interfaccia
tcpdump -i ens18 -n             # Tutto il traffico
tcpdump -i ens18 -n host 10.0.0.1   # Solo traffico verso/da un IP
tcpdump -i ens18 -n port 80     # Solo traffico sulla porta 80
tcpdump -i ens18 -n icmp        # Solo ICMP (ping)
tcpdump -i ens18 -n -e vlan     # Traffico VLAN (mostra tag)
tcpdump -i ens18 -n -w /tmp/capture.pcap   # Salva su file

# Sul nodo Proxmox, catturare traffico del bridge
tcpdump -i vmbr0 -n host <vm-ip>
```

### ethtool

```bash
# Informazioni sull'interfaccia
ethtool ens18                   # Settings (speed, duplex, link status)
ethtool -i ens18                # Driver information
ethtool -S ens18                # Statistiche dettagliate
ethtool -k ens18                # Offload features

# Impostazioni utili
ethtool -K ens18 tso off        # Disabilitare TCP Segmentation Offload
ethtool -K ens18 gso off        # Disabilitare Generic Segmentation Offload
# Utile per debugging problemi di performance di rete
```

### nmap

```bash
# Scansione rapida di una subnet
nmap -sn 10.0.0.0/24           # Ping scan (host discovery)
nmap -p 22,80,443 10.0.0.100   # Scansione porte specifiche
nmap -sV -p 1-1000 10.0.0.100  # Service version detection
```

---

## Flowchart di Troubleshooting Sistematico {#flowchart}

### Procedura Step-by-Step

```
INIZIO: La VM non ha connettivita di rete dopo la migrazione

STEP 1: L'interfaccia di rete e visibile nel guest?
├── NO -> Il driver NIC non e caricato
│   ├── Linux: modprobe virtio_net
│   ├── Windows: installare driver NetKVM
│   └── Workaround: cambiare NIC a e1000
│
└── SI -> STEP 2: L'interfaccia ha un indirizzo IP?
    ├── NO (DHCP) -> Il DHCP funziona?
    │   ├── Verificare MAC address (DHCP lease legato al vecchio MAC)
    │   ├── Verificare bridge Proxmox
    │   └── Verificare VLAN tag
    │
    ├── NO (Statico) -> La configurazione punta all'interfaccia corretta?
    │   ├── Linux: verificare nome interfaccia (ens192 -> ens18)
    │   ├── Linux: rimuovere regole udev persistenti
    │   ├── Windows: rimuovere ghost NIC adapters
    │   └── Riconfigurare IP statico sulla nuova interfaccia
    │
    └── SI -> STEP 3: Il gateway e raggiungibile?
        ├── NO -> Problema di L2
        │   ├── Verificare bridge Proxmox (vmbr0 collegato?)
        │   ├── Verificare VLAN (tag corretto?)
        │   ├── Verificare MTU (mismatch?)
        │   ├── Verificare ARP (ip neigh show)
        │   └── tcpdump sul bridge per verificare traffico
        │
        └── SI -> STEP 4: Internet e raggiungibile?
            ├── NO con IP -> Problema di routing
            │   ├── Verificare route (ip route show)
            │   ├── Verificare NAT/PAT sul firewall
            │   └── Verificare ACL sullo switch/router
            │
            ├── NO con DNS -> Problema DNS
            │   ├── Verificare /etc/resolv.conf
            │   ├── Verificare raggiungibilita DNS server
            │   └── Verificare firewall (porta 53)
            │
            └── SI -> STEP 5: I servizi specifici funzionano?
                ├── NO -> Firewall guest che blocca
                │   ├── Linux: iptables -L / firewall-cmd --list-all
                │   ├── Windows: Get-NetFirewallProfile
                │   └── Verificare SELinux/AppArmor
                │
                └── SI -> La rete funziona correttamente!
```

### Script di Diagnostica Automatica

```bash
#!/bin/bash
# network-diag.sh - Diagnostica di rete post-migrazione
# Eseguire all'interno della VM migrata

echo "=== Diagnostica Rete Post-Migrazione ==="
echo "Data: $(date)"
echo "Hostname: $(hostname)"
echo ""

echo "--- Interfacce di Rete ---"
ip link show
echo ""

echo "--- Indirizzi IP ---"
ip addr show
echo ""

echo "--- Routing ---"
ip route show
echo ""

echo "--- DNS ---"
cat /etc/resolv.conf 2>/dev/null
echo ""

echo "--- Test Connettivita ---"
GATEWAY=$(ip route show default | awk '{print $3}')
if [ -n "$GATEWAY" ]; then
    echo "Gateway: $GATEWAY"
    ping -c 3 -W 2 $GATEWAY && echo "Gateway: OK" || echo "Gateway: UNREACHABLE"
else
    echo "ATTENZIONE: nessun gateway default configurato"
fi
echo ""

echo "--- Test DNS ---"
if command -v nslookup &>/dev/null; then
    nslookup google.com 2>&1 | head -5
elif command -v dig &>/dev/null; then
    dig +short google.com
elif command -v host &>/dev/null; then
    host google.com
fi
echo ""

echo "--- Test Internet ---"
ping -c 3 -W 2 8.8.8.8 && echo "Internet (IP): OK" || echo "Internet (IP): UNREACHABLE"
echo ""

echo "--- Moduli VirtIO Rete ---"
lsmod | grep virtio_net
echo ""

echo "--- Dispositivi PCI di Rete ---"
lspci | grep -i net
echo ""

echo "--- Firewall ---"
iptables -L -n 2>/dev/null | head -20
echo ""

echo "=== Diagnostica Completata ==="
```

Questo script fornisce una panoramica rapida dello stato della rete e aiuta a identificare il livello in cui si trova il problema, consentendo di procedere con la soluzione appropriata seguendo il flowchart descritto sopra.

---

## Letture primarie consigliate

- Linux kernel — Networking documentation. https://www.kernel.org/doc/html/latest/networking/index.html (retrieved 2026-04-27).
- iproute2 documentation. https://wiki.linuxfoundation.org/networking/iproute2 (retrieved 2026-04-27).
- tcpdump — Public Repository. https://www.tcpdump.org/manpages/tcpdump.1.html (retrieved 2026-04-27).
- Proxmox VE Wiki — Network Configuration. https://pve.proxmox.com/wiki/Network_Configuration (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 04.1 — `../04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md`: configurazione di base.
- Modulo 07.1 — `../07-MIGRAZIONE-NETWORKING/ip-planning-dns-dhcp-firewall.md`: pianificazione cutover IP.
- Modulo 17.1 — `troubleshooting-cluster-proxmox.md`: spesso problemi cluster sono problemi rete.
