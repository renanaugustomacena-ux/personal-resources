# IP Planning, DNS, DHCP e Firewall nella Migrazione VMware-Proxmox

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 07.1 (apre il cluster networking, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 04.1 (Linux Bridge/VLAN/Bonding); modulo 06.1, 06.3 (strategie e cutover); networking di base (subnetting, ARP, RFC 1918, RFC 2131 DHCP, RFC 2136 dynamic DNS); concetti firewall stateful.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. decidere fra **IP preservation** (stesso IP della VM dopo cutover) e **re-IP** (nuovo IP), motivando la scelta sulla base di accoppiamento applicativo (VM hardcoded IP), DNS resolver coverage, costo di riconfigurazione client;
> 2. eseguire una **migrazione same-subnet** (la VM resta sulla stessa subnet, solo cambia hypervisor) vs **different-subnet** (la VM cambia rete L3 — richiede update DNS, eventualmente NAT, eventualmente reload firewall stateful);
> 3. progettare la strategia DNS pre-cutover: TTL drop a 60 s 24-48 h prima, sostituzione record A/AAAA, monitoraggio propagation lag, ripristino TTL 24 h dopo;
> 4. pianificare la migrazione DHCP (reservations, leases, scope) e gli IP statici (preservation guaranteed nei file di config);
> 5. tradurre regole firewall NSX (Distributed Firewall) in regole Proxmox Firewall (cluster-level + VM-level con `firewall=1` su `--net0`);
> 6. costruire un **cutover runbook di rete** con pre-flight, esecuzione, validazione e rollback < 5 min.
> **Tempo stimato:** lettura 90-120 min · lab 240-360 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** BIND 9.18+, Microsoft DNS 2019/2022, ISC DHCP 4.4, Kea DHCP 2.x, NSX-T 3.x/4.x, Proxmox Firewall (incluso in PVE 8.x).

## Mappa concettuale

```
+======================================================+
|  Cutover di rete — pipeline                          |
+======================================================+
|                                                      |
|   PRE-CUTOVER (T-48h)                                |
|     +-- DNS TTL drop a 60 s su record migranti       |
|     +-- monitoring resolver propagation              |
|     +-- backup config DHCP/firewall                  |
|         |                                            |
|         v                                            |
|   CLONE/SYNC                                         |
|     +-- VM cloned su Proxmox (stesso IP riservato)   |
|     +-- delta sync rsync/CBT                         |
|         |                                            |
|         v                                            |
|   CUTOVER WINDOW (T-0)                               |
|     +-- Stop VM su VMware                            |
|     +-- Final delta sync                             |
|     +-- Start VM su Proxmox (stesso IP)              |
|     +-- Update DNS A/AAAA record (se re-IP)          |
|     +-- Update firewall rules per nuovo MAC          |
|     +-- Update DHCP reservation (MAC → IP)           |
|     +-- Update VRRP / HSRP se gateway VM            |
|         |                                            |
|         v                                            |
|   VALIDAZIONE (5-30 min)                             |
|     +-- ping, traceroute, dig, curl                  |
|     +-- ARP cache flush sui peer                     |
|     +-- TCP session drain (FIN_WAIT2 max 60 s)       |
|     +-- application healthcheck                      |
|         |                                            |
|         v                                            |
|   POST-CUTOVER (T+24h)                               |
|     +-- DNS TTL ripristinato a normale (3600 s)      |
|     +-- monitoring continuato 48 h                   |
|     +-- documentazione chiusura wave                 |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **IP preservation > re-IP, quando possibile.** Re-IP richiede reconfig di tutti i client che si collegano alla VM, e in molte app legacy l'IP e hardcoded in config files, registry, DB, comandi cron. IP preservation richiede solo che il MAC nuovo sul Proxmox finisca su un'interface della stessa subnet, e che eventuali DHCP reservation siano aggiornate.
2. **Same-subnet e la situazione meno costosa.** Se l'host Proxmox e nella stessa VLAN del cluster VMware sorgente, allora la VM puo conservare il suo IP senza problemi: e solo il MAC che cambia. ARP cache si rinfresca naturalmente in 60 s o forziamo con `arping -U`.
3. **TTL DNS basso pre-cutover, sempre.** Il vincolo non e solo "abbasso TTL il giorno prima": il TTL deve essere stato basso *abbastanza tempo* perche la riduzione si propaghi. Se TTL era 86400 s e lo abbasso adesso a 60 s, i resolver impareranno il nuovo TTL solo *dopo che expira il vecchio* — fino a 24 h dopo. Quindi: drop TTL a 60 s almeno 48 h prima del cutover; nei resolver moderati e abbastanza.
4. **Firewall NSX → Proxmox: traduzione concettuale.** NSX Distributed Firewall vive nel kernel ESXi e applica regole per VM (group-based, tag-based). Proxmox Firewall vive nel netfilter Linux dell'host con regole per VMID. La traduzione: NSX security group → Proxmox security group; NSX rule per tag → Proxmox rule con alias di IPSet; NSX object-based rule → Proxmox FW rule scritta in `/etc/pve/firewall/cluster.fw` o `/etc/pve/firewall/<vmid>.fw`.
5. **VRRP/HSRP come gateway: occhio al MAC virtuale.** Se il default gateway della VLAN e una coppia VRRP master/standby di router fisici, niente da fare. Se invece il gateway vive *come VM su VMware*, va migrato con cura: VRRP master deve passare la "VIP" alla nuova VM Proxmox prima del cutover dei client, altrimenti tutti i client perdono il default gateway per la durata del cutover. Soluzione: tenere la coppia VRRP in cross-hypervisor durante la wave (un router su VMware, l'altro su Proxmox), poi smettere il vecchio.

## Indice
- [Panoramica](#panoramica)
- [IP Preservation vs Re-IP: Matrice Decisionale](#ip-preservation-vs-re-ip-matrice-decisionale)
- [Migrazione Same-Subnet vs Different-Subnet](#migrazione-same-subnet-vs-different-subnet)
- [Strategia DNS: Riduzione TTL e Aggiornamento Record](#strategia-dns-riduzione-ttl-e-aggiornamento-record)
- [Migrazione DHCP Reservation e IP Statici](#migrazione-dhcp-reservation-e-ip-statici)
- [Migrazione Firewall: NSX verso Proxmox Firewall](#migrazione-firewall-nsx-verso-proxmox-firewall)
- [Strategie di Network Cutover](#strategie-di-network-cutover)
- [Migrazione Load Balancer e VIP](#migrazione-load-balancer-e-vip)
- [Procedure di Rollback](#procedure-di-rollback)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La pianificazione IP, la gestione DNS, DHCP e firewall rappresentano gli aspetti Layer 3-7 della migrazione di rete da VMware a Proxmox VE. Mentre i documenti precedenti trattano la migrazione Layer 2 (bridge, VLAN, bonding), questo documento affronta le decisioni architetturali e operative che determinano come le VM mantengono (o cambiano) la propria identità di rete durante il passaggio tra piattaforme.

La decisione fondamentale è se preservare gli indirizzi IP delle VM o effettuare un re-IP. Questa scelta ha ramificazioni su ogni aspetto dell'infrastruttura: DNS, certificati TLS (che possono includere indirizzi IP nei SAN), regole firewall, configurazioni applicative con IP hardcoded, monitoring, backup, e qualsiasi sistema che faccia riferimento alle VM tramite indirizzo IP. La preservazione IP è quasi sempre preferibile, ma non sempre possibile — ad esempio quando la migrazione avviene tra datacenter con subnet diverse.

Questo documento fornisce matrici decisionali, procedure operative dettagliate, configurazioni di esempio e strategie di cutover per gestire ogni scenario, dalla migrazione più semplice (same-subnet con IP preservation) alla più complessa (different-subnet con re-IP, DNS cutover, e aggiornamento firewall). Particolare attenzione viene dedicata alle procedure di rollback, spesso trascurate ma essenziali per garantire un piano B in caso di problemi durante la migrazione.

---

## IP Preservation vs Re-IP: Matrice Decisionale

### Fattori Decisionali

La scelta tra preservare gli IP esistenti o riassegnarne di nuovi dipende da molteplici fattori tecnici e organizzativi:

| Fattore | Favorisce IP Preservation | Favorisce Re-IP |
|---|---|---|
| **Ubicazione fisica** | Stesso datacenter/rack | Datacenter diverso |
| **Subnet** | Stessa subnet L2 estesa | Subnet diverse |
| **Numero VM** | Molte VM (>50) | Poche VM (<10) |
| **Dipendenze IP hardcoded** | Molte applicazioni con IP fissi | Tutto referenziato via DNS |
| **Regole firewall** | Basate su IP, molte regole | Basate su hostname/FQDN |
| **Certificati TLS con IP** | Presenti SAN con IP | Solo FQDN nei certificati |
| **Complessità applicativa** | Cluster con IP hardcoded | Applicazioni stateless |
| **Finestra di manutenzione** | Limitata (<2h) | Ampia (>8h) |
| **DNS dinamico** | Non disponibile | Disponibile e funzionante |

### Matrice Decisionale

```
                            Stessa Subnet          Subnet Diversa
                         ┌───────────────────┬───────────────────┐
                         │                   │                   │
  Poche dipendenze IP    │  IP Preservation  │     Re-IP con     │
  (<10 regole FW,        │  (scenario ideale) │   DNS cutover     │
   no IP in cert)        │                   │                   │
                         ├───────────────────┼───────────────────┤
                         │                   │                   │
  Molte dipendenze IP    │  IP Preservation  │  L2 stretch +     │
  (>10 regole FW,        │  (obbligatoria)   │  IP Preservation  │
   IP in cert/app)       │                   │  oppure Re-IP     │
                         │                   │  graduale         │
                         └───────────────────┴───────────────────┘
```

### Inventario IP Pre-Migrazione

Prima di prendere qualsiasi decisione, compilare un inventario completo degli indirizzi IP:

```bash
#!/bin/bash
# ip_inventory.sh
# Esportare inventario IP da VMware tramite PowerCLI (eseguire su Windows)
# Oppure: raccogliere direttamente dalle VM con questo script

OUTPUT="ip_inventory_$(date +%Y%m%d).csv"
echo "hostname,ip_address,subnet_mask,gateway,dns_servers,vlan,mac_address,type" > "$OUTPUT"

# Per ogni VM (eseguire via SSH o agent)
# Esempio per Linux:
hostname=$(hostname -f)
for iface in $(ip -o link show | awk -F': ' '{print $2}' | grep -v lo); do
    ip_addr=$(ip -4 addr show "$iface" 2>/dev/null | grep inet | awk '{print $2}')
    mac=$(ip link show "$iface" | grep ether | awk '{print $2}')
    [[ -z "$ip_addr" ]] && continue
    echo "$hostname,$ip_addr,,,,,$mac,static_or_dhcp"
done >> "$OUTPUT"
```

PowerCLI per inventario VMware:

```powershell
# Esportare IP di tutte le VM da vCenter
Get-VM | Where-Object {$_.PowerState -eq "PoweredOn"} |
    Select-Object Name,
        @{N="IP";E={$_.Guest.IPAddress -join ";"}},
        @{N="Network";E={($_ | Get-NetworkAdapter).NetworkName -join ";"}},
        @{N="MAC";E={($_ | Get-NetworkAdapter).MacAddress -join ";"}},
        @{N="OS";E={$_.Guest.OSFullName}} |
    Export-Csv -Path "vm_ip_inventory.csv" -NoTypeInformation
```

---

## Migrazione Same-Subnet vs Different-Subnet

### Same-Subnet Migration

Nella migrazione same-subnet, gli host Proxmox sono collegati allo stesso segmento Layer 2 degli host VMware. Le VM mantengono lo stesso IP, subnet, gateway e DNS senza alcuna modifica.

```
┌─────────────────────────────────────────────────────────────┐
│                    Switch Fisico                             │
│                    VLAN 100: 10.0.100.0/24                  │
│                                                             │
│   Trunk Port 1        Trunk Port 2        Trunk Port 3     │
│       │                    │                    │           │
│  ┌────┴────┐          ┌────┴────┐          ┌────┴────┐     │
│  │ ESXi    │          │ Proxmox │          │ Proxmox │     │
│  │ Host 1  │          │ Host 1  │          │ Host 2  │     │
│  │         │          │         │          │         │     │
│  │ VM-A    │ migrate  │ VM-A    │          │ VM-C    │     │
│  │ .100.10 │ ──────→  │ .100.10 │          │ .100.12 │     │
│  │         │          │         │          │         │     │
│  │ VM-B    │          │ VM-B    │ migrate  │ VM-B    │     │
│  │ .100.11 │          │ .100.11 │ ──────→  │ .100.11 │     │
│  └─────────┘          └─────────┘          └─────────┘     │
└─────────────────────────────────────────────────────────────┘

L'IP della VM non cambia. Il gateway (10.0.100.1) resta lo stesso.
Solo il MAC dell'uplink cambia → aggiornamento ARP table sullo switch.
```

Procedura operativa:

1. Verificare che la VLAN 100 sia configurata sia sulle porte ESXi che sulle porte Proxmox
2. Spegnere la VM su VMware
3. Avviare la VM su Proxmox (stesso IP, stessa VLAN tag)
4. La VM invierà un Gratuitous ARP (GARP) al boot, aggiornando la ARP table dello switch e del gateway
5. Se il GARP non avviene (alcuni OS non lo inviano), forzare l'aggiornamento:

```bash
# Dal host Proxmox, forzare GARP per conto della VM
arping -U -I vmbr0.100 10.0.100.10 -c 3

# Oppure dalla VM stessa (Linux)
arping -U -I eth0 10.0.100.10 -c 3

# Su Windows nella VM, svuotare la cache ARP
arp -d *
# E fare ping al gateway per rigenerare l'entry ARP
ping 10.0.100.1
```

### Different-Subnet Migration

Quando i host Proxmox sono su una subnet diversa, ogni VM migrata deve ricevere un nuovo indirizzo IP. Questo scenario è significativamente più complesso e richiede aggiornamenti coordinati di DNS, firewall, monitoring, e configurazioni applicative.

```
┌──────────────────────┐          ┌──────────────────────┐
│ Datacenter A (VMware)│          │ Datacenter B (Proxmox)│
│ Subnet: 10.0.100.0/24│          │ Subnet: 10.1.100.0/24│
│                      │          │                      │
│  VM-A: 10.0.100.10   │ migrate  │  VM-A: 10.1.100.10   │
│  VM-B: 10.0.100.11   │ ──────→  │  VM-B: 10.1.100.11   │
│  GW:   10.0.100.1    │          │  GW:   10.1.100.1    │
│  DNS:  10.0.10.5     │          │  DNS:  10.1.10.5     │
└──────────────────────┘          └──────────────────────┘

Tutto cambia: IP, gateway, DNS server.
Richiede aggiornamento di: DNS record, firewall rules, app config,
monitoring, backup targets, certificati (se IP nei SAN).
```

Checklist per different-subnet migration:

```
□ Inventario completo IP e dipendenze
□ Riduzione TTL DNS (almeno 7 giorni prima)
□ Preparazione nuovi IP nella nuova subnet
□ Aggiornamento regole firewall (bidirezionale)
□ Aggiornamento record DNS (A, PTR, SRV, MX)
□ Aggiornamento configurazioni applicative
□ Aggiornamento monitoring (Nagios, Zabbix, Prometheus)
□ Aggiornamento backup configuration
□ Verifica certificati TLS (SAN con IP?)
□ Piano di rollback documentato
□ Test post-migrazione per ogni servizio
```

---

## Strategia DNS: Riduzione TTL e Aggiornamento Record

### Timeline DNS Pre-Migrazione

La gestione DNS è critica per minimizzare il downtime percepito. La preparazione deve iniziare almeno 7 giorni prima della migrazione:

```
Giorno -7: Ridurre TTL da 3600s (1h) a 60s (1min)
    │       per tutti i record delle VM da migrare
    │
Giorno -3: Verificare che il TTL ridotto sia propagato
    │       (dig +trace per ogni record critico)
    │
Giorno -1: Freeze delle modifiche DNS
    │       Backup completo zone DNS
    │       Verifica pre-migrazione
    │
Giorno 0:  MIGRAZIONE
    │       1. Spegnere VM su VMware
    │       2. Avviare VM su Proxmox
    │       3. Aggiornare record DNS (se re-IP)
    │       4. Verificare risoluzione DNS
    │       5. Verificare servizi
    │
Giorno +1: Monitoring attivo
    │       Verifica che tutti i client usino i nuovi IP
    │
Giorno +7: Ripristinare TTL originale (3600s)
    │       Rimuovere vecchi record se presenti
    │
Giorno +30: Cleanup: rimuovere IP temporanei,
            aggiornare documentazione
```

### Riduzione TTL: Procedura

Per BIND/named:

```bash
# Prima (TTL alto)
; /etc/bind/zones/db.example.com
$TTL 3600
@       IN      SOA     ns1.example.com. admin.example.com. (
                        2026041200  ; Serial
                        3600        ; Refresh
                        900         ; Retry
                        604800      ; Expire
                        86400 )     ; Negative Cache TTL

webapp  IN      A       10.0.100.10
dbserver IN     A       10.0.100.20

# Dopo riduzione TTL (Giorno -7)
$TTL 60
@       IN      SOA     ns1.example.com. admin.example.com. (
                        2026041201  ; Serial (incrementato!)
                        3600        ; Refresh
                        900         ; Retry
                        604800      ; Expire
                        60 )        ; Negative Cache TTL

webapp  60      IN      A       10.0.100.10
dbserver 60     IN      A       10.0.100.20
```

```bash
# Ricaricare la zona
rndc reload example.com

# Verificare la propagazione
dig webapp.example.com +short
dig webapp.example.com +trace | grep -i ttl

# Verificare da DNS resolver esterno
dig @8.8.8.8 webapp.example.com | grep -i ttl
```

Per Microsoft DNS (PowerShell):

```powershell
# Ridurre TTL per record specifici
Get-DnsServerResourceRecord -ZoneName "example.com" -Name "webapp" |
    ForEach-Object {
        $old = $_
        $new = $_.Clone()
        $new.TimeToLive = [System.TimeSpan]::FromSeconds(60)
        Set-DnsServerResourceRecord -ZoneName "example.com" -OldInputObject $old -NewInputObject $new
    }
```

### Aggiornamento Record DNS Post-Migrazione

Script per aggiornamento batch dei record DNS (nsupdate per BIND):

```bash
#!/bin/bash
# update_dns_records.sh
# Input: CSV con formato "hostname,old_ip,new_ip"

DNS_SERVER="10.0.10.5"
ZONE="example.com"
KEY_FILE="/etc/bind/keys/update.key"
CSV_FILE="dns_migration_map.csv"
LOG_FILE="/var/log/dns_migration_$(date +%Y%m%d_%H%M%S).log"

while IFS=',' read -r hostname old_ip new_ip; do
    [[ "$hostname" == "hostname" ]] && continue
    [[ -z "$hostname" ]] && continue

    fqdn="${hostname}.${ZONE}"

    echo "Aggiornamento: $fqdn $old_ip → $new_ip" | tee -a "$LOG_FILE"

    # Aggiornare record A
    nsupdate -k "$KEY_FILE" <<EOF
server $DNS_SERVER
zone $ZONE
update delete $fqdn A
update add $fqdn 60 A $new_ip
send
EOF

    if [[ $? -eq 0 ]]; then
        echo "  OK: record A aggiornato" | tee -a "$LOG_FILE"
    else
        echo "  ERRORE: aggiornamento record A fallito" | tee -a "$LOG_FILE"
    fi

    # Aggiornare record PTR (reverse DNS)
    # Calcolare la zona reverse
    reverse_ip=$(echo "$new_ip" | awk -F. '{print $4"."$3"."$2"."$1}')
    reverse_zone=$(echo "$new_ip" | awk -F. '{print $3"."$2"."$1".in-addr.arpa"}')

    nsupdate -k "$KEY_FILE" <<EOF
server $DNS_SERVER
zone $reverse_zone
update delete ${reverse_ip}.in-addr.arpa PTR
update add ${reverse_ip}.in-addr.arpa 60 PTR $fqdn.
send
EOF

    # Verificare
    resolved_ip=$(dig +short "$fqdn" @"$DNS_SERVER")
    if [[ "$resolved_ip" == "$new_ip" ]]; then
        echo "  VERIFICATO: $fqdn → $resolved_ip" | tee -a "$LOG_FILE"
    else
        echo "  ATTENZIONE: $fqdn risolve a $resolved_ip (atteso: $new_ip)" | tee -a "$LOG_FILE"
    fi

done < "$CSV_FILE"
```

---

## Migrazione DHCP Reservation e IP Statici

### Inventario Completo degli Assegnamenti IP

Classificare ogni VM in una delle seguenti categorie:

| Categoria | Descrizione | Azione Migrazione |
|---|---|---|
| **IP Statico nel Guest** | IP configurato nel sistema operativo | Modificare config nel guest (se re-IP) |
| **DHCP Reservation** | IP assegnato dal DHCP basato su MAC | Aggiornare reservation con nuovo MAC |
| **DHCP Dinamico** | IP assegnato dal pool DHCP | Nessuna azione specifica |
| **IP secondario/alias** | IP aggiuntivi sulla stessa NIC | Verificare migrazione di tutti gli alias |

### Migrazione DHCP Reservation

Quando una VM viene migrata, il suo MAC address può cambiare (Proxmox assegna MAC dal range `BC:24:11:xx:xx:xx` per le interfacce virtio). Le reservation DHCP basate su MAC devono essere aggiornate.

Script per ISC DHCP Server:

```bash
#!/bin/bash
# migrate_dhcp_reservations.sh
# Aggiornare le reservation DHCP dopo la migrazione

DHCP_CONF="/etc/dhcp/dhcpd.conf"
BACKUP="${DHCP_CONF}.backup.$(date +%Y%m%d)"
CSV_FILE="mac_migration_map.csv"  # formato: hostname,old_mac,new_mac,ip

cp "$DHCP_CONF" "$BACKUP"

while IFS=',' read -r hostname old_mac new_mac ip; do
    [[ "$hostname" == "hostname" ]] && continue
    [[ -z "$hostname" ]] && continue

    # Normalizzare i MAC (minuscolo, separatore :)
    old_mac_norm=$(echo "$old_mac" | tr '[:upper:]' '[:lower:]' | tr '-' ':')
    new_mac_norm=$(echo "$new_mac" | tr '[:upper:]' '[:lower:]' | tr '-' ':')

    echo "Aggiornamento reservation: $hostname ($old_mac_norm → $new_mac_norm)"

    # Sostituire il MAC nella reservation
    sed -i "s/hardware ethernet ${old_mac_norm}/hardware ethernet ${new_mac_norm}/g" "$DHCP_CONF"
done < "$CSV_FILE"

# Verificare sintassi
dhcpd -t -cf "$DHCP_CONF"
if [[ $? -eq 0 ]]; then
    echo "Sintassi OK. Riavvio dhcpd..."
    systemctl restart isc-dhcp-server
else
    echo "ERRORE di sintassi! Ripristino backup..."
    cp "$BACKUP" "$DHCP_CONF"
fi
```

Ottenere il mapping dei nuovi MAC da Proxmox:

```bash
# Per ogni VM migrata, estrarre il nuovo MAC
for vmid in $(qm list | awk 'NR>1 {print $1}'); do
    hostname=$(qm config "$vmid" | grep "^name:" | awk '{print $2}')
    mac=$(qm config "$vmid" | grep "^net0:" | grep -oP '[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}')
    echo "${hostname},${mac}"
done > proxmox_mac_inventory.csv
```

### Gestione IP Statici nelle VM

Per le VM con IP statico configurato nel guest OS, nel caso di re-IP è necessario aggiornare la configurazione di rete all'interno di ogni VM. Script di automazione via SSH:

```bash
#!/bin/bash
# reip_linux_vms.sh
# Riconfigurazione IP per VM Linux via SSH

CSV_FILE="reip_map.csv"  # formato: hostname,old_ip,new_ip,new_gw,new_dns

while IFS=',' read -r hostname old_ip new_ip new_gw new_dns; do
    [[ "$hostname" == "hostname" ]] && continue

    echo "=== Riconfigurando $hostname: $old_ip → $new_ip ==="

    ssh -o ConnectTimeout=5 "root@${old_ip}" bash <<REMOTE_EOF
        # Backup configurazione corrente
        cp /etc/network/interfaces /etc/network/interfaces.pre_migration

        # Identificare l'interfaccia con l'IP corrente
        IFACE=\$(ip -o addr show | grep "${old_ip}" | awk '{print \$2}')

        if [[ -z "\$IFACE" ]]; then
            echo "ERRORE: interfaccia con IP ${old_ip} non trovata"
            exit 1
        fi

        echo "Interfaccia: \$IFACE"

        # Per sistemi con /etc/network/interfaces (Debian/Ubuntu)
        if [[ -f /etc/network/interfaces ]]; then
            sed -i "s|address ${old_ip}|address ${new_ip}|g" /etc/network/interfaces
            sed -i "s|gateway .*|gateway ${new_gw}|g" /etc/network/interfaces
        fi

        # Per sistemi con NetworkManager (RHEL/CentOS)
        if command -v nmcli &>/dev/null; then
            CONN=\$(nmcli -t -f NAME,DEVICE con show --active | grep "\$IFACE" | cut -d: -f1)
            nmcli con mod "\$CONN" ipv4.addresses "${new_ip}/24"
            nmcli con mod "\$CONN" ipv4.gateway "${new_gw}"
            nmcli con mod "\$CONN" ipv4.dns "${new_dns}"
        fi

        # Aggiornare /etc/resolv.conf
        echo "nameserver ${new_dns}" > /etc/resolv.conf

        echo "Configurazione aggiornata. Riavvio networking..."
        # Non eseguire qui: la connessione SSH si interromperà
        # Usare at o nohup
        echo "systemctl restart networking" | at now + 1 minute
REMOTE_EOF

    echo "  Attendere 90 secondi per il riavvio networking..."
    sleep 90

    # Verificare raggiungibilità al nuovo IP
    if ping -c 3 -W 2 "$new_ip" &>/dev/null; then
        echo "  OK: $hostname raggiungibile al nuovo IP $new_ip"
    else
        echo "  ERRORE: $hostname NON raggiungibile al nuovo IP $new_ip"
    fi

done < "$CSV_FILE"
```

---

## Migrazione Firewall: NSX verso Proxmox Firewall

### Architettura VMware NSX Distributed Firewall

NSX Distributed Firewall (DFW) opera a livello di vNIC, intercettando il traffico prima che raggiunga il vSwitch. Le regole possono essere basate su:

- Indirizzo IP (sorgente/destinazione)
- Security group (raggruppamento logico di VM)
- Security tag (classificazione automatica)
- Applicazione/protocollo (Layer 7 con DPI)

### Proxmox Firewall: Architettura

Il firewall Proxmox opera su tre livelli gerarchici:

```
┌─────────────────────────────────────────┐
│           Datacenter Level               │
│  /etc/pve/firewall/cluster.fw           │
│  Policy globali, regole per tutto il DC  │
├─────────────────────────────────────────┤
│           Host Level                     │
│  /etc/pve/nodes/<node>/host.fw          │
│  Regole specifiche per l'host            │
├─────────────────────────────────────────┤
│           VM Level                       │
│  /etc/pve/firewall/<vmid>.fw            │
│  Regole specifiche per la singola VM     │
└─────────────────────────────────────────┘
```

Il firewall è implementato tramite iptables (o nftables nelle versioni più recenti) e inserisce le regole nella catena FORWARD del kernel Linux. Ogni regola viene applicata sulla vNIC della VM, simulando il comportamento del NSX DFW.

### Mapping Regole NSX → Proxmox

#### Esportazione Regole NSX

```bash
# Via NSX API (NSX-T)
curl -k -u admin:password \
    https://nsx-manager.example.com/policy/api/v1/infra/domains/default/security-policies \
    | jq '.results[] | {name: .display_name, rules: .rules}' > nsx_rules_export.json

# Via PowerCLI (NSX-V)
Get-NsxFirewallSection | Get-NsxFirewallRule |
    Select-Object Name, Source, Destination, Service, Action, Direction |
    Export-Csv -Path "nsx_firewall_rules.csv" -NoTypeInformation
```

#### Conversione in Regole Proxmox

Esempio di conversione:

NSX Rule originale:
```
Name: Allow-Web-to-DB
Source: Security Group "Web-Servers" (10.0.100.10, 10.0.100.11)
Destination: Security Group "DB-Servers" (10.0.200.20, 10.0.200.21)
Service: TCP/3306 (MySQL)
Action: Allow
```

Proxmox equivalente — a livello VM (per la VM database 10.0.200.20, vmid=200):

```
# /etc/pve/firewall/200.fw
[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT

[RULES]
# Allow Web Servers to access MySQL
IN ACCEPT -source 10.0.100.10 -p tcp -dport 3306 -log nolog
IN ACCEPT -source 10.0.100.11 -p tcp -dport 3306 -log nolog

# Allow monitoring
IN ACCEPT -source 10.0.10.5 -p tcp -dport 9100 -log nolog

# Allow SSH from management
IN ACCEPT -source 10.0.10.0/24 -p tcp -dport 22 -log nolog
```

Proxmox equivalente — a livello cluster (per policy globali):

```
# /etc/pve/firewall/cluster.fw
[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT

[IPSET management]
10.0.10.0/24

[IPSET web_servers]
10.0.100.10
10.0.100.11

[IPSET db_servers]
10.0.200.20
10.0.200.21

[GROUP web-to-db]
# Regole per traffico web → database
IN ACCEPT -source +web_servers -dest +db_servers -p tcp -dport 3306 -log nolog

[RULES]
# Permettere ICMP per monitoring
IN ACCEPT -p icmp -log nolog

# Permettere SSH da management
IN ACCEPT -source +management -p tcp -dport 22 -log nolog

# Bloccare tutto il resto (policy implicita)
```

### Security Group → IP Set

Gli NSX Security Group si mappano agli IP Set di Proxmox. La differenza fondamentale è che gli NSX Security Group possono essere dinamici (basati su tag, nome VM, OS, ecc.), mentre gli IP Set di Proxmox sono statici (liste di IP/subnet):

```
# /etc/pve/firewall/cluster.fw

[IPSET web_servers]
# Equivalente di NSX Security Group "Web-Servers"
10.0.100.10  # web01
10.0.100.11  # web02
10.0.100.12  # web03

[IPSET db_servers]
# Equivalente di NSX Security Group "DB-Servers"
10.0.200.20  # db-primary
10.0.200.21  # db-replica

[IPSET monitoring]
# Equivalente di NSX Security Group "Monitoring"
10.0.10.5    # prometheus
10.0.10.6    # grafana
```

### Integrazione con nftables

Per regole firewall più complesse che superano le capacità del firewall Proxmox integrato, è possibile usare nftables direttamente:

```bash
# /etc/nftables.conf (aggiuntivo al firewall Proxmox)
table inet custom_rules {
    chain forward {
        type filter hook forward priority 10; policy accept;

        # Rate limiting per protezione DDoS
        iifname "vmbr0" tcp dport 80 meter http_limit { ip saddr limit rate 100/second } accept
        iifname "vmbr0" tcp dport 80 meter http_limit { ip saddr limit rate over 100/second } drop

        # Blocco traffico inter-VLAN non autorizzato
        # VLAN 100 → VLAN 200 bloccato (tranne porta 3306)
        ip saddr 10.0.100.0/24 ip daddr 10.0.200.0/24 tcp dport != 3306 drop
    }
}
```

```bash
# Applicare le regole
nft -f /etc/nftables.conf

# Verificare le regole attive
nft list ruleset

# Rendere persistente
systemctl enable nftables
```

---

## Strategie di Network Cutover

### Strategia 1: Scheduled Maintenance Window

La strategia più semplice e sicura. Tutte le VM vengono migrate durante una finestra di manutenzione pianificata.

```
Timeline:
──────────────────────────────────────────────────────────
T-7 giorni:  Ridurre TTL DNS a 60s
T-1 giorno:  Pre-flight check completo
T-0:         INIZIO FINESTRA DI MANUTENZIONE
  │
  ├── T+0:00  Notifica utenti, stop traffico esterno
  ├── T+0:15  Spegnere VM su VMware (ordine: app → web → db)
  ├── T+0:30  Avviare VM su Proxmox (ordine: db → web → app)
  ├── T+0:45  Aggiornare DNS (se re-IP)
  ├── T+1:00  Test di connettività e servizi
  ├── T+1:30  Aggiornare firewall rules
  ├── T+2:00  Test end-to-end completi
  ├── T+2:30  Ripristinare traffico esterno
  │
  └── T+3:00  FINE FINESTRA DI MANUTENZIONE
──────────────────────────────────────────────────────────
T+1 giorno:  Monitoring intensivo
T+7 giorni:  Ripristinare TTL DNS originali
```

### Strategia 2: Parallel Run (Zero-Downtime)

Le VM vengono duplicate (non migrate) su Proxmox. Entrambi gli ambienti sono attivi contemporaneamente. Il traffico viene spostato gradualmente tramite DNS o load balancer.

```
┌─────────────────────┐     ┌─────────────────────┐
│   VMware (attivo)   │     │   Proxmox (standby)  │
│                     │     │                      │
│   web01: .100.10    │     │   web01: .100.50     │
│   web02: .100.11    │     │   web02: .100.51     │
│   db01:  .200.20    │     │   db01:  .200.50     │
└────────┬────────────┘     └────────┬─────────────┘
         │                           │
         └─────────┬─────────────────┘
                   │
            ┌──────┴──────┐
            │ DNS / Load  │
            │ Balancer    │
            │             │
            │ webapp.ex → │
            │  VMware (w) │  Fase 1: 100% VMware
            │  Proxmox(0) │
            │             │
            │ webapp.ex → │
            │  VMware(50) │  Fase 2: 50/50
            │  Proxmox(50)│
            │             │
            │ webapp.ex → │
            │  VMware (0) │  Fase 3: 100% Proxmox
            │  Proxmox(w) │
            └─────────────┘
```

**Attenzione**: questa strategia richiede che i dati siano sincronizzati tra le due istanze (replica database, shared storage, ecc.). Non è applicabile per VM stateful senza un meccanismo di replica.

### Strategia 3: DNS-Based Cutover

Il cutover avviene cambiando i record DNS. Funziona bene quando tutti i client accedono ai servizi tramite hostname (non IP diretto):

```bash
# Fase 1: Preparazione
# webapp.example.com → 10.0.100.10 (VMware) TTL 60

# Fase 2: Migrare la VM a Proxmox con nuovo IP
# VM attiva su Proxmox con IP 10.1.100.10

# Fase 3: Aggiornare DNS
nsupdate -k /etc/bind/keys/update.key <<EOF
server dns.example.com
zone example.com
update delete webapp.example.com A
update add webapp.example.com 60 A 10.1.100.10
send
EOF

# Fase 4: Verificare propagazione
watch -n 5 "dig +short webapp.example.com @8.8.8.8"

# Fase 5: Monitorare per 24h
# I client con DNS cache più alta del TTL continueranno a usare il vecchio IP
# Mantenere il vecchio IP attivo come redirect/proxy temporaneo
```

---

## Migrazione Load Balancer e VIP

### Scenari di Migrazione VIP

I Virtual IP (VIP) esposti dai load balancer richiedono attenzione specifica:

| Scenario | Complessità | Approccio |
|---|---|---|
| LB esterno (F5, HAProxy su bare metal) | Bassa | Aggiornare pool member IP |
| LB come VM (HAProxy/Nginx VM) | Media | Migrare il LB stesso |
| NSX Load Balancer | Alta | Sostituire con HAProxy/keepalived |
| VIP con keepalived/VRRP | Media | Riconfigurare keepalived su Proxmox |

### Migrazione con Load Balancer Esterno

Se il load balancer è un appliance esterno (F5, NetScaler, HAProxy bare metal), la migrazione è semplice: aggiornare gli IP dei backend server nel pool.

```
# HAProxy: aggiornare backend pool
# /etc/haproxy/haproxy.cfg

backend web_servers
    balance roundrobin
    # Prima (VMware)
    # server web01 10.0.100.10:80 check
    # server web02 10.0.100.11:80 check

    # Dopo (Proxmox - same subnet, IP preservato)
    server web01 10.0.100.10:80 check
    server web02 10.0.100.11:80 check
    # IP identici: nessuna modifica necessaria!

    # Dopo (Proxmox - different subnet)
    server web01 10.1.100.10:80 check
    server web02 10.1.100.11:80 check
```

### Sostituzione NSX LB con keepalived + HAProxy

NSX Load Balancer non esiste in Proxmox. La combinazione keepalived (per VIP floating) + HAProxy (per load balancing) è l'alternativa standard:

```bash
# Installazione su VM Proxmox dedicata
apt install -y keepalived haproxy

# /etc/keepalived/keepalived.conf
vrrp_instance VI_WEB {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass secretpass
    }
    virtual_ipaddress {
        10.0.100.100/24    # VIP per il servizio web
    }
}

# /etc/haproxy/haproxy.cfg
frontend web_frontend
    bind 10.0.100.100:80
    bind 10.0.100.100:443 ssl crt /etc/ssl/certs/webapp.pem
    default_backend web_backend

backend web_backend
    balance roundrobin
    option httpchk GET /health
    server web01 10.0.100.10:80 check inter 3000
    server web02 10.0.100.11:80 check inter 3000
```

---

## Procedure di Rollback

### Principi di Rollback

Ogni migrazione deve avere un piano di rollback documentato e testato. Il rollback deve essere possibile entro un tempo definito (tipicamente 30-60 minuti) senza perdita di dati.

### Rollback Procedure per Same-Subnet Migration

```
TRIGGER: Servizio non funzionante dopo 30 minuti dalla migrazione

1. STOP: Arrestare la VM su Proxmox
   qm stop <vmid>

2. VERIFY: Verificare che la VM sia spenta
   qm status <vmid>

3. START: Avviare la VM originale su VMware
   Power-On via vCenter (la VM non è stata cancellata)

4. ARP: Forzare aggiornamento ARP
   # Dalla VM VMware o dal host ESXi
   vmkping -I vmk0 <gateway_ip>

5. VERIFY: Test di connettività
   ping <vm_ip>
   curl http://<vm_ip>:<port>/health

6. DNS: Ripristinare eventuali record DNS modificati
   # Se nessun record DNS è stato cambiato, skip

7. NOTIFY: Comunicare il rollback al team
```

### Rollback Procedure per Different-Subnet (Re-IP)

```
TRIGGER: Servizio non funzionante dopo 30 minuti dalla migrazione

1. DNS ROLLBACK: Ripristinare i record DNS ai vecchi IP
   nsupdate -k /etc/bind/keys/update.key <<EOF
   server dns.example.com
   zone example.com
   update delete webapp.example.com A
   update add webapp.example.com 60 A 10.0.100.10
   send
   EOF

2. FIREWALL ROLLBACK: Ripristinare le regole firewall
   cp /etc/pve/firewall/cluster.fw.backup /etc/pve/firewall/cluster.fw

3. VM ROLLBACK:
   a. Spegnere VM su Proxmox: qm stop <vmid>
   b. Avviare VM su VMware (vCenter Power-On)

4. DHCP ROLLBACK: Ripristinare reservation
   cp /etc/dhcp/dhcpd.conf.backup /etc/dhcp/dhcpd.conf
   systemctl restart isc-dhcp-server

5. VERIFY: Test completo di tutti i servizi

6. POST-MORTEM: Analizzare la causa del fallimento prima di ritentare
```

### Script di Rollback Automatizzato

```bash
#!/bin/bash
# rollback_migration.sh
# Eseguire SOLO in caso di fallimento della migrazione

set -euo pipefail

ROLLBACK_LOG="/var/log/rollback_$(date +%Y%m%d_%H%M%S).log"
DNS_BACKUP="/root/migration/dns_backup.zone"
FW_BACKUP="/root/migration/cluster.fw.backup"
VM_LIST="/root/migration/migrated_vms.csv"  # formato: vmid,hostname

exec > >(tee -a "$ROLLBACK_LOG") 2>&1

echo "=== INIZIO ROLLBACK - $(date) ==="

# Fase 1: Spegnere VM su Proxmox
echo "--- Fase 1: Spegnimento VM Proxmox ---"
while IFS=',' read -r vmid hostname; do
    [[ "$vmid" == "vmid" ]] && continue
    echo "Spegnimento VM $vmid ($hostname)..."
    qm stop "$vmid" --timeout 60 2>/dev/null || echo "  WARN: VM $vmid non raggiungibile"
done < "$VM_LIST"

# Fase 2: Ripristinare DNS
echo "--- Fase 2: Ripristino DNS ---"
if [[ -f "$DNS_BACKUP" ]]; then
    cp "$DNS_BACKUP" /etc/bind/zones/db.example.com
    rndc reload example.com
    echo "DNS ripristinato"
else
    echo "ATTENZIONE: backup DNS non trovato, ripristino manuale necessario"
fi

# Fase 3: Ripristinare firewall
echo "--- Fase 3: Ripristino Firewall ---"
if [[ -f "$FW_BACKUP" ]]; then
    cp "$FW_BACKUP" /etc/pve/firewall/cluster.fw
    echo "Firewall ripristinato"
else
    echo "ATTENZIONE: backup firewall non trovato"
fi

echo ""
echo "=== ROLLBACK COMPLETATO - $(date) ==="
echo "AZIONE RICHIESTA: Avviare le VM su VMware tramite vCenter"
echo "AZIONE RICHIESTA: Verificare tutti i servizi"
```

---

## Best Practices

- **Preservare gli IP** quando possibile. Ogni re-IP introduce rischio e complessità. Se la migrazione avviene nella stessa rete Layer 2, non c'è motivo per cambiare IP.

- **Ridurre il TTL DNS almeno 7 giorni prima** della migrazione. Molti resolver DNS rispettano il TTL, ma alcuni (soprattutto quelli aziendali) ignorano TTL molto bassi. 7 giorni garantiscono che anche le cache più aggressive abbiano scaduto i vecchi record.

- **Mantenere i vecchi IP attivi** per almeno 7 giorni dopo la migrazione (se possibile). Configurare un redirect o proxy temporaneo sui vecchi IP che inoltra il traffico ai nuovi. Questo cattura i client con DNS cache stale.

- **Documentare OGNI dipendenza IP** prima della migrazione: firewall rules, certificati, configurazioni applicative, script di backup, monitoring, cron job. Le dipendenze non documentate sono la prima causa di problemi post-migrazione.

- **Testare il rollback** prima di eseguire la migrazione. Simulare il fallimento e verificare che la procedura di rollback funzioni nei tempi previsti.

- **Migrare i servizi DNS/DHCP per ultimi**, dopo che tutti gli altri servizi sono stati migrati e validati. Questi sono servizi infrastrutturali critici il cui malfunzionamento ha impatto su tutta l'infrastruttura.

- **Utilizzare IP Set nel firewall Proxmox** per emulare i Security Group NSX. Mantenere gli IP Set aggiornati con l'inventario delle VM.

- **Non disattivare il firewall** durante la migrazione "per semplicità". Le regole firewall devono essere migrate insieme alla VM. Un ambiente senza firewall, anche temporaneamente, è un rischio inaccettabile.

- **Creare snapshot/backup** di ogni VM prima della migrazione. In caso di problemi, il ripristino dallo snapshot è più rapido del rollback completo.

- **Automatizzare il più possibile**: script per aggiornamento DNS, DHCP, firewall. L'esecuzione manuale di molte operazioni durante una finestra di manutenzione è soggetta a errori.

- **Pianificare la migrazione fuori dagli orari di punta** e assicurarsi che il team di supporto sia disponibile per le prime 24 ore post-migrazione.

- **Verificare i certificati TLS**: se contengono IP nei Subject Alternative Names (SAN), devono essere rigenerati con i nuovi IP prima della migrazione.

---

## Troubleshooting

### Problema: DNS Non Si Propaga Dopo l'Aggiornamento
**Sintomi**: dopo aver aggiornato il record DNS, il `dig` verso il DNS server locale mostra il nuovo IP, ma i client continuano a raggiungere il vecchio IP.
**Causa**: il TTL non era stato ridotto con sufficiente anticipo. I resolver DNS dei client hanno la vecchia entry in cache con un TTL alto (es. 3600 secondi). Inoltre, alcuni resolver intermedi (ISP, aziendali) possono ignorare TTL molto bassi e imporre un minimum TTL proprio.
**Soluzione**: attendere la scadenza del TTL originale. Per i client interni, forzare il flush della cache DNS: su Windows `ipconfig /flushdns`, su Linux `systemd-resolve --flush-caches` o `resolvectl flush-caches`. Per i resolver aziendali, contattare il team IT per forzare il clear della cache.
**Prevenzione**: ridurre il TTL almeno 7 giorni prima. Verificare la propagazione con `dig +trace` da punti diversi della rete. Per servizi critici, considerare di mantenere un proxy/redirect sul vecchio IP.

### Problema: Regole Firewall Bloccano Traffico Legittimo dopo Migrazione
**Sintomi**: servizi che funzionavano correttamente prima della migrazione sono bloccati. I log del firewall Proxmox mostrano "REJECT" o "DROP" per traffico che dovrebbe essere consentito.
**Causa**: le regole firewall non sono state completamente migrate da NSX. Possibili cause specifiche: IP Set incompleto (non tutti gli IP sono stati inseriti), regole basate su security group dinamici NSX che non hanno equivalente diretto in Proxmox, o policy di default diversa (NSX allow vs Proxmox drop).
**Soluzione**: verificare i log firewall in tempo reale: `tail -f /var/log/pve-firewall.log | grep DROP`. Identificare il traffico bloccato e aggiungere le regole mancanti. Come workaround temporaneo (solo per diagnosi), impostare `policy_in: ACCEPT` nel file .fw della VM interessata, verificare che il traffico passi, poi aggiungere le regole specifiche e reimpostare `policy_in: DROP`.
**Prevenzione**: migrare le regole firewall PRIMA di migrare le VM. Testare le regole con traffico simulato. Non cambiare la policy di default durante la migrazione.

### Problema: DHCP Lease Non Rinnovato con Nuovo MAC
**Sintomi**: la VM migrata ha un MAC address diverso e non riceve l'IP corretto dal DHCP. Riceve un IP dal pool dinamico invece della reservation prevista.
**Causa**: la reservation DHCP è ancora basata sul vecchio MAC address (VMware), ma la VM su Proxmox ha un nuovo MAC (range `BC:24:11:xx:xx:xx` per virtio).
**Soluzione**: aggiornare la reservation nel DHCP server con il nuovo MAC. In alternativa, preservare il MAC originale VMware nella configurazione della VM Proxmox: `qm set <vmid> -net0 virtio=<vecchio_mac>,bridge=vmbr0,tag=<vlan>`. Questo evita di dover modificare le reservation DHCP.
**Prevenzione**: durante la migrazione, preservare i MAC address originali quando possibile. Proxmox consente di specificare qualsiasi MAC address nella configurazione della NIC virtuale.

### Problema: VIP Non Raggiungibile Dopo Migrazione Load Balancer
**Sintomi**: il Virtual IP (VIP) gestito da keepalived o dal load balancer non è raggiungibile dopo la migrazione della VM del LB su Proxmox.
**Causa**: Proxmox di default non consente il MAC spoofing (necessario per VIP/VRRP). L'interfaccia di rete della VM deve avere Promiscuous Mode abilitato, oppure il bridge deve consentire ARP con IP diversi dall'IP configurato.
**Soluzione**: nella configurazione della NIC della VM LB, il firewall Proxmox potrebbe bloccare i pacchetti ARP per il VIP. Verificare che `IP Filter` non sia attivo sulla NIC se la VM deve annunciare un IP diverso dal proprio. Nel file `/etc/pve/firewall/<vmid>.fw`, assicurarsi che non ci siano regole che blocchino il traffico VRRP (protocollo 112) o i pacchetti gratuitous ARP. In alternativa, aggiungere il VIP come IP noto: `net0: virtio=...,bridge=vmbr0,tag=100` e nel firewall `[IPSET ipfilter-net0]` aggiungere sia l'IP primario che il VIP.
**Prevenzione**: testare keepalived/VRRP in ambiente di test prima della migrazione. Documentare tutti i VIP e le configurazioni di load balancing.

### Problema: Perdita di Connettività Inter-Datacenter dopo Re-IP
**Sintomi**: VM nel nuovo datacenter (Proxmox) non possono comunicare con sistemi nel vecchio datacenter (VMware) o con sistemi in altri datacenter.
**Causa**: le route statiche o le policy di routing tra datacenter non includono le nuove subnet assegnate all'ambiente Proxmox. I router/firewall perimetrali non hanno route verso le nuove subnet.
**Soluzione**: verificare la routing table dei router tra datacenter: `show ip route` (Cisco). Aggiungere route statiche o annunciare le nuove subnet via protocollo di routing (OSPF, BGP). Verificare anche le ACL sui firewall perimetrali, che potrebbero bloccare le nuove subnet.
**Prevenzione**: coordinare la pianificazione IP con il team di networking. Assicurarsi che le nuove subnet siano annunciate/routate PRIMA di migrare le VM. Testare il routing end-to-end prima della migrazione.

### Problema: Certificati TLS Rifiutati dopo Re-IP
**Sintomi**: i client ricevono errori di certificato TLS (SSL_ERROR_BAD_CERT_DOMAIN o simili) quando si collegano al servizio migrato tramite IP diretto.
**Causa**: il certificato TLS contiene il vecchio IP nel campo Subject Alternative Name (SAN). Dopo il re-IP, il nuovo IP non corrisponde al certificato.
**Soluzione**: rigenerare il certificato con il nuovo IP nel SAN. Per Let's Encrypt, i certificati non possono contenere IP, solo FQDN — il che significa che il problema si presenta solo con certificati interni (CA privata). Per CA interna: `openssl req -new -key server.key -out server.csr -addext "subjectAltName=IP:10.1.100.10,DNS:webapp.example.com"` e far firmare dalla CA. Come workaround temporaneo, i client possono accedere al servizio via FQDN (che corrisponde al certificato) invece che via IP diretto.
**Prevenzione**: inventariare tutti i certificati prima della migrazione. Identificare quelli con IP nei SAN. Rigenerarli prima del cutover. Preferire certificati con solo FQDN nei SAN per evitare questo problema in future migrazioni.

### Problema: Script di Monitoring Non Funzionano dopo Re-IP
**Sintomi**: Nagios/Zabbix/Prometheus non rilevano le VM migrate. Alert di "host down" per tutte le VM migrate nonostante siano funzionanti.
**Causa**: le configurazioni del sistema di monitoring contengono i vecchi IP delle VM. I check puntano agli indirizzi precedenti.
**Soluzione**: aggiornare le configurazioni del monitoring con i nuovi IP. Per Prometheus: aggiornare i `targets` in `prometheus.yml`. Per Zabbix: aggiornare gli host via API o interfaccia web. Per Nagios: aggiornare i file `.cfg` degli host. Riavviare il servizio di monitoring dopo le modifiche.
**Prevenzione**: includere l'aggiornamento del monitoring nella checklist di migrazione. Automatizzare l'aggiornamento con script che leggono il CSV di mapping IP e aggiornano le configurazioni del monitoring.

---

## Riferimenti

- [Proxmox VE Firewall Documentation](https://pve.proxmox.com/wiki/Firewall)
- [ISC DHCP Server Documentation](https://kb.isc.org/docs/isc-dhcp-44-manual-pages-dhcpdconf)
- [BIND 9 Administrator Reference Manual](https://bind9.readthedocs.io/en/latest/)
- [keepalived Documentation](https://www.keepalived.org/manpage.html)
- [HAProxy Documentation](https://www.haproxy.org/download/2.8/doc/configuration.txt)
- [nftables Wiki](https://wiki.nftables.org/wiki-nftables/index.php/Main_Page)
- [VMware NSX-T API Guide](https://developer.vmware.com/apis/1163/nsx-t)
- [RFC 2136 - Dynamic Updates in DNS](https://www.rfc-editor.org/rfc/rfc2136)
- [RFC 5798 - VRRP v3](https://www.rfc-editor.org/rfc/rfc5798)
- [OWASP Network Segmentation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Network_Segmentation_Cheat_Sheet.html)
- [Proxmox VE HA Manager](https://pve.proxmox.com/wiki/High_Availability)

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — Proxmox Firewall a tre livelli.** Il firewall di Proxmox lavora a tre livelli annidati: (a) **datacenter** (`/etc/pve/firewall/cluster.fw`) — regole valide su tutti i nodi e tutte le VM; (b) **node** (`/etc/pve/nodes/<node>/host.fw`) — regole per il management dell'host stesso (porta 8006, SSH); (c) **VM** (`/etc/pve/firewall/<vmid>.fw`) — regole per VM specifica, applicate via `firewall=1` sul `--net` device. La precedenza e: cluster → node → VM. Per debug: `pve-firewall compile` mostra le regole iptables generate. Riferimento: [`PVE-FIREWALL`] `https://pve.proxmox.com/wiki/Firewall`.

> **Errore comune — ARP table del switch fisico stale dopo cutover.** Sintomo: dopo aver migrato una VM mantenendo IP, alcuni client riescono a raggiungerla e altri no per 5-10 min. Causa: lo switch fisico ha cached il vecchio MAC della VM-VMware in CAM/MAC table, e i frame in arrivo per quell'IP vengono inoltrati alla porta vecchia. Soluzione: dalla nuova VM-Proxmox, eseguire `arping -U -I eth0 <vm-ip>` (gratuitous ARP unsolicited) appena dopo il boot — invia un broadcast ARP che forza tutti gli switch e router della VLAN a ri-imparare il MAC. Su VM Linux: aggiungere allo script di startup. Su Windows: equivalente non e nativo, usare `gratarp.exe` o un piccolo tool custom.

> **Caso reale — DNS view splittato non aggiornato.** Un'azienda con DNS interno (Active Directory DNS) e DNS pubblico esposto via Cloudflare ha aggiornato solo il DNS pubblico durante un cutover. I client interni hanno continuato a risolvere il vecchio IP per altre 4 ore (TTL interno 14400). Soluzione preventiva: avere una checklist che includa **tutti i resolver** (interno AD, esterno pubblico, AWS Route53, Azure DNS, Cloudflare, eventuali DNS forwarder), e fare il drop TTL su tutti.

---

## Esercizi

1. **Concettuale — IP preservation o re-IP?** Per ognuno: (a) database PostgreSQL stand-alone con 30 client che si collegano via IP hardcoded; (b) web server dietro reverse proxy (Nginx) — un solo client; (c) AD Domain Controller; (d) container LXC di sviluppo. *Risposte:* (a) IP preservation strongly preferred (re-IP = 30 client da reconfigurare); (b) re-IP ok (basta aggiornare il `proxy_pass` su Nginx); (c) IP preservation (DC sono critici e tutto AD lo riferisce per IP/FQDN); (d) re-IP banale (e dev).

2. **Lab — gratuitous ARP post-cutover.** Su un lab a 2 nodi (uno simulato VMware, uno Proxmox), eseguire un cutover di una VM Linux Debian preservando IP. Catturare con `tcpdump -ni vmbr0 arp` il traffico ARP nei primi 60 sec. Verificare che `arping -U -I eth0 <ip>` venga emesso dalla nuova VM e accolto dagli switch. Se manca, troubleshootare lo switch.

3. **Scenario — firewall NSX rule traduzione.** Hai una regola NSX-T: "permettere TCP 443 da security group `web-tier` verso security group `app-tier`". Sul cluster Proxmox con 5 VM web e 3 VM app, scrivi le regole equivalenti in `/etc/pve/firewall/cluster.fw`. *Risposta:* creare due IPSet (`+web` e `+app`) con i rispettivi IP delle VM; regola `IN ACCEPT --proto tcp --dport 443 --source +web --dest +app`. Verificare con `pve-firewall compile`.

4. **Stretch — DNS migration script.** Scrivere uno script Python che, dato un file `dns-records.csv` (record da migrare), esegua: (a) verifica TTL attuale; (b) abbassa TTL a 60 s; (c) waiter di propagation lag con dig query da multipli resolver pubblici (1.1.1.1, 8.8.8.8, 9.9.9.9, 208.67.222.222) e log delle risposte; (d) al cutover, sostituisce il record A; (e) waiter di nuova propagazione; (f) ripristina TTL originale dopo 24 h. Bonus: integrare nsupdate (RFC 2136) per Microsoft DNS / BIND con Kerberos.

## Auto-valutazione

1. Differenza fra IP preservation e re-IP, e in quale scenario preferire l'uno o l'altro?
2. Quanto tempo prima del cutover abbassare il TTL DNS, e perche non subito al cutover?
3. Cosa fa `arping -U -I eth0 <ip>` e perche serve dopo cutover con MAC change?
4. Tre livelli di Proxmox Firewall: dove vivono i file di config?
5. Cosa fa `pve-firewall compile` e quando si usa?
6. Come si traduce un security group NSX-T in Proxmox Firewall?
7. Differenza fra gratuitous ARP request e gratuitous ARP reply?
8. RFC 2136: cosa formalizza e in quali implementazioni DNS e usato?

## Letture primarie consigliate

- [`PVE-FIREWALL`] Proxmox VE Wiki — Firewall. https://pve.proxmox.com/wiki/Firewall
- [`RFC-2131`] RFC 2131 — Dynamic Host Configuration Protocol. https://datatracker.ietf.org/doc/html/rfc2131
- [`RFC-2132`] RFC 2132 — DHCP Options. https://datatracker.ietf.org/doc/html/rfc2132
- RFC 2136 — Dynamic Updates in DNS. https://datatracker.ietf.org/doc/html/rfc2136
- RFC 5798 — VRRP v3. https://datatracker.ietf.org/doc/html/rfc5798
- RFC 5227 — IPv4 Address Conflict Detection (gratuitous ARP). https://datatracker.ietf.org/doc/html/rfc5227
- VMware NSX-T Distributed Firewall. https://docs.vmware.com/en/VMware-NSX/index.html
- BIND 9 Administrator Reference Manual. https://bind9.readthedocs.io/
- Microsoft DNS Server. https://learn.microsoft.com/en-us/windows-server/networking/dns/

## Collegamenti incrociati

- Modulo 04.1 — `../04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md`: networking di base Proxmox.
- Modulo 06.3 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/live-migration-minimo-downtime.md`: strategie cutover dipendenti dal DNS.
- Modulo 07.2 — `mapping-vswitch-linux-bridge.md`: mapping vSwitch ↔ Linux Bridge in pratica.
- Modulo 07.3 — `migrazione-vlan-e-segmentazione.md`: migrazione VLAN e segmentazione.
- Modulo 12.1, 12.2, 12.3 — `../12-SICUREZZA-E-COMPLIANCE/`: sicurezza post-migrazione.
- Modulo 17.3 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-networking-post-migrazione.md`: troubleshooting networking.

## Glossario locale

| Termine | Definizione |
|---|---|
| **IP preservation** | Mantenimento dello stesso IP della VM dopo la migrazione (richiede stessa subnet o NAT). |
| **Re-IP** | La VM ottiene un IP nuovo dopo migrazione, richiede update DNS e reconfig client. |
| **Same-subnet migration** | VM resta nella stessa subnet/VLAN, cambia solo l'hypervisor. |
| **Different-subnet migration** | VM cambia rete L3 — richiede DNS update e gestione NAT/firewall. |
| **TTL DNS** | Time To Live di un record DNS, in secondi. Default tipico 3600. |
| **Gratuitous ARP** | ARP request/reply emesso da un host per annunciare proattivamente il suo MAC sul network (RFC 5227). |
| **`arping -U`** | Linux: invia gratuitous ARP unsolicited. |
| **DHCP reservation** | Mappatura statica MAC → IP nel server DHCP. |
| **VRRP / HSRP** | Protocolli di failover di gateway IP virtuali (RFC 5798 / Cisco proprietary). |
| **NSX Distributed Firewall** | Firewall virtuale di NSX-T che applica regole nel kernel ESXi (vNIC level). |
| **Proxmox Firewall** | Firewall a 3 livelli (cluster, node, VM) basato su iptables/nftables. |
| **IPSet (Proxmox)** | Insieme nominato di IP/CIDR usato nelle regole del firewall (es. `+web-servers`). |
| **`/etc/pve/firewall/cluster.fw`** | File di config del firewall a livello cluster Proxmox. |
| **`/etc/pve/firewall/<vmid>.fw`** | File di config firewall per singola VM. |
| **`pve-firewall compile`** | Comando che mostra le regole iptables generate dal config Proxmox Firewall. |
| **RFC 2136** | Dynamic Updates in DNS — usato per nsupdate (BIND, Microsoft DNS via Kerberos). |
