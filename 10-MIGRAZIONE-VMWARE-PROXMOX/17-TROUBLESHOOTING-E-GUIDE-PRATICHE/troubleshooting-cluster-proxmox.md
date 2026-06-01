# Troubleshooting Cluster Proxmox

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 7 — Day-2 operations · Modulo 17.1 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 02 (architettura cluster, corosync, pmxcfs), 10.1-10.3 (HA, fencing, live migration); fluenza con `journalctl`, `systemctl`, network diagnostics.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. diagnosticare problemi di **quorum loss** (corosync token timeout, network partition, NTP drift) e applicare recovery procedures;
> 2. risolvere problemi `pmxcfs` (read-only, lock stuck, corruzione cluster.db);
> 3. recovery di nodo "ghost" o "stuck" (fenced loop, watchdog non triggera);
> 4. usare strumenti diagnostici: `pvecm status`, `corosync-cfgtool -s`, `journalctl -u corosync -u pve-cluster -u pve-ha-lrm`, `ha-manager status`.
> **Tempo stimato:** lettura 60-90 min · uso reattivo durante incident
> **Livello:** proficient (Dreyfus 4); SRE/operations
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **Prima di toccare nulla, raccogli evidenza.** `journalctl --since "1h ago"` su tutti i nodi, `pvecm status`, `ha-manager status`, screenshot delle GUI. Senza evidenza, root cause analysis impossibile.
2. **Mai forzare quorum (`pvecm e <count>`) senza capire cosa stai facendo.** Forzando quorum su una "isola" minoritaria, rischi split-brain manuale.
3. **Recovery cluster di solito significa: ripristinare rete, restart corosync, attendere rejoin.** Se questo non basta, valutare un "fresh re-init" del nodo problematico (re-add al cluster).

---

## Indice

1. [Panoramica Problemi di Cluster](#panoramica)
2. [Nodo Non Si Unisce al Cluster](#nodo-non-join)
3. [Perdita di Quorum](#perdita-quorum)
4. [Split-Brain Recovery](#split-brain)
5. [Corosync Communication Failure](#corosync-failure)
6. [pmxcfs Non Monta](#pmxcfs)
7. [Errori Certificati](#errori-certificati)
8. [HA Non Effettua il Failover](#ha-failover)
9. [Fencing Non Funziona](#fencing)
10. [Ceph Health Warnings](#ceph-health)
11. [OSD Down e Recovery](#osd-down)
12. [MON Election Issues](#mon-election)
13. [Recovery da Total Cluster Failure](#total-failure)
14. [Comandi pvecm per Diagnostica](#pvecm-comandi)

---

## Panoramica Problemi di Cluster {#panoramica}

Un cluster Proxmox VE si basa su tre componenti fondamentali:

- **Corosync**: comunicazione e membership del cluster, gestione del quorum
- **pmxcfs**: filesystem distribuito per la configurazione del cluster (`/etc/pve`)
- **HA Manager**: gestisce il failover automatico delle VM/container

Quando uno di questi componenti fallisce, l'impatto puo variare da un singolo nodo non raggiungibile alla perdita completa dell'accesso al cluster.

### Architettura del Quorum

```
Nodi nel cluster    Quorum minimo    Nodi che possono fallire
1                   1                0
2                   2 (problematico) 0
3                   2                1
4                   3                1
5                   3                2
6                   4                2
7                   4                3
```

Il quorum richiede la maggioranza assoluta: `(N/2) + 1` nodi devono essere attivi.

---

## Nodo Non Si Unisce al Cluster {#nodo-non-join}

### Sintomi

```bash
pvecm add <cluster-ip>
# Errori possibili:
# "unable to join cluster: SSH connection failed"
# "unable to join cluster: authentication failure"
# "unable to join cluster: host already in cluster"
# "unable to join cluster: node is already a cluster member"
```

### Diagnostica e Soluzione

**Errore: SSH connection failed**

```bash
# Verificare la connettivita SSH
ssh root@<cluster-ip>

# Verificare che SSH sia in ascolto
ss -tlnp | grep 22

# Verificare il firewall
iptables -L -n | grep 22
pve-firewall status

# Verificare la risoluzione nomi
getent hosts <cluster-node-hostname>
cat /etc/hosts
# IMPORTANTE: /etc/hosts deve contenere gli IP corretti di TUTTI i nodi
# e NON deve avere 127.0.1.1 associato al hostname del nodo
```

**Errore: authentication failure**

```bash
# Rigenerare le chiavi SSH
ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
ssh-copy-id root@<cluster-ip>

# Verificare la fingerprint
ssh-keyscan <cluster-ip>
```

**Errore: host already in cluster**

```bash
# Se il nodo era gia in un cluster diverso, rimuovere prima la configurazione
# ATTENZIONE: questo cancella la configurazione del cluster precedente

systemctl stop pve-cluster
systemctl stop corosync
pmxcfs -l  # Avvia pmxcfs in modalita locale

rm /etc/pve/corosync.conf
rm -rf /etc/corosync/*
rm /etc/pve/authkey.conf 2>/dev/null
rm -rf /var/lib/corosync/*

systemctl stop pmxcfs
systemctl start pve-cluster

# Ora tentare il join
pvecm add <cluster-ip>
```

**Errore: porte Corosync bloccate**

```bash
# Corosync usa le porte UDP 5405-5412
# Verificare che siano raggiungibili

# Sul nodo esistente
ss -ulnp | grep corosync

# Dal nodo che deve unirsi
nc -uzv <cluster-ip> 5405

# Aprire le porte nel firewall se necessario
iptables -A INPUT -p udp --dport 5405:5412 -j ACCEPT
```

---

## Perdita di Quorum {#perdita-quorum}

### Sintomi

```bash
# La GUI Proxmox mostra: "cluster not ready - no quorum?"
# I comandi pvecm/qm/pct falliscono con errori di quorum

pvecm status
# Quorum: 0  <- PROBLEMA: nessun quorum
# Expected votes: 3
# Total votes: 1
```

### Diagnostica

```bash
# Verificare lo stato Corosync
systemctl status corosync
corosync-cfgtool -s
# Mostra le interfacce Corosync e il loro stato

# Verificare la membership
corosync-cmapctl | grep members
# Deve mostrare tutti i nodi attivi

# Verificare i ring Corosync
corosync-cfgtool -s
# Se mostra status "FAULTY" per un ring, c'e un problema di comunicazione
```

### Soluzione Temporanea: Forzare il Quorum

```bash
# ATTENZIONE: usare solo in emergenza quando si e certi
# che gli altri nodi NON sono operativi

# Impostare i voti attesi al numero di nodi raggiungibili
pvecm expected 1
# Questo forza il quorum con un singolo nodo

# Dopo aver ripristinato gli altri nodi, reimpostare:
pvecm expected <numero-totale-nodi>
```

### Soluzione: Ripristinare la Comunicazione tra Nodi

```bash
# 1. Verificare la rete tra i nodi
ping <nodo2-ip>
ping <nodo3-ip>

# 2. Verificare che Corosync sia in esecuzione su tutti i nodi
ssh root@<nodo2> systemctl status corosync
ssh root@<nodo3> systemctl status corosync

# 3. Riavviare Corosync sui nodi problematici
ssh root@<nodo2> systemctl restart corosync

# 4. Verificare il quorum
pvecm status
# Expected votes: 3
# Total votes: 3
# Quorum: 2  <- OK
```

---

## Split-Brain Recovery {#split-brain}

### Cos'e lo Split-Brain

Lo split-brain si verifica quando i nodi del cluster perdono la comunicazione tra loro ma continuano a funzionare indipendentemente. Questo puo causare:
- Dati divergenti tra i nodi
- VM avviate su piu nodi contemporaneamente (pericolosissimo per i dati)
- Configurazioni inconsistenti

### Identificare lo Split-Brain

```bash
# Su ogni nodo, verificare la vista del cluster
pvecm status
pvecm nodes

# Se nodi diversi mostrano membership diverse, c'e split-brain

# Verificare i log
journalctl -u corosync --since "1 hour ago"
# Cercare messaggi come:
# "retransmit failed"
# "processor failed"
# "membership changed"
```

### Procedura di Recovery

```bash
# 1. FERMARE TUTTE LE VM su ENTRAMBI i lati dello split
# Questo e CRITICO per evitare corruzione dati
qm list
# Per ogni VM in esecuzione:
qm stop <vmid>

# 2. Scegliere il lato "vincente" (quello con i dati piu aggiornati)

# 3. Sul lato "perdente", fermare i servizi cluster
systemctl stop pve-ha-lrm
systemctl stop pve-ha-crm
systemctl stop pvestatd
systemctl stop pveproxy
systemctl stop corosync

# 4. Risolvere il problema di rete che ha causato lo split

# 5. Riavviare Corosync sul lato perdente
systemctl start corosync

# 6. Verificare che il cluster si sia riunito
pvecm status
pvecm nodes

# 7. Riavviare i servizi
systemctl start pve-ha-lrm
systemctl start pve-ha-crm
systemctl start pvestatd
systemctl start pveproxy

# 8. Verificare la configurazione
# Confrontare /etc/pve/qemu-server/ su tutti i nodi
# Dovrebbero essere identici (pmxcfs li sincronizza)
```

---

## Corosync Communication Failure {#corosync-failure}

### Diagnostica Corosync

```bash
# Stato delle interfacce Corosync
corosync-cfgtool -s
# Output:
# Printing ring status.
# Local node ID 1
# RING ID 0
#         id      = 10.0.0.1
#         status  = ring 0 active with no faults  <- OK
# oppure:
#         status  = Marking ringid 0 interface 10.0.0.1 FAULTY  <- PROBLEMA

# Log Corosync
journalctl -u corosync --no-pager -n 100

# Statistiche Corosync
corosync-cmapctl | grep stats.srp
# Mostra pacchetti inviati/ricevuti, errori, retransmit

# Verificare la configurazione
cat /etc/pve/corosync.conf
```

### Problemi Comuni Corosync

**Ring interface FAULTY:**

```bash
# L'interfaccia di rete usata da Corosync non funziona

# Verificare l'interfaccia
ip addr show <interface>
ip link show <interface>

# Verificare la raggiungibilita degli altri nodi
ping -I <corosync-ip> <altro-nodo-corosync-ip>

# Se l'interfaccia e stata cambiata o non esiste:
# Modificare corosync.conf per puntare all'interfaccia corretta
# ATTENZIONE: modificare corosync.conf solo via pvecm o dalla GUI
```

**Multicast non funziona (default in Proxmox < 7):**

```bash
# Verificare se il multicast funziona sulla rete
# Su un nodo:
tcpdump -i <interface> -n udp port 5405

# Sull'altro nodo:
echo "test" | socat - UDP4-DATAGRAM:239.192.1.1:5405

# Se multicast non funziona, passare a unicast:
# Modificare corosync.conf per usare unicast (knet in Proxmox 7+)
pvecm updatecerts
```

**Knet transport issues (Proxmox 7+):**

```bash
# Proxmox 7+ usa knet come transport Corosync
# Verificare lo stato knet
corosync-cfgtool -s

# Log specifici knet
journalctl -u corosync | grep knet

# Se ci sono problemi con knet, verificare:
# 1. Porte UDP 5405 aperte
# 2. Nessun firewall tra i nodi
# 3. MTU sufficiente (knet aggiunge overhead)
```

---

## pmxcfs Non Monta {#pmxcfs}

### Sintomi

```bash
# /etc/pve non e accessibile
ls /etc/pve
# ls: cannot access '/etc/pve': Transport endpoint is not connected

# Oppure
# "pmxcfs: filesystem was not cleanly unmounted"
```

### Diagnostica

```bash
# Stato di pmxcfs
systemctl status pve-cluster

# Log
journalctl -u pve-cluster --no-pager -n 50

# Verificare se il processo esiste
ps aux | grep pmxcfs

# Verificare il mount point
mount | grep pve
```

### Soluzione

```bash
# 1. Tentare il restart
systemctl restart pve-cluster

# 2. Se non funziona, verificare Corosync
systemctl status corosync

# 3. Se Corosync e OK ma pmxcfs non monta:
# Fermare tutti i servizi che dipendono da /etc/pve
systemctl stop pveproxy
systemctl stop pvedaemon
systemctl stop pve-ha-lrm
systemctl stop pve-ha-crm

# Riavviare pve-cluster
systemctl restart pve-cluster

# Riavviare i servizi
systemctl start pvedaemon
systemctl start pveproxy
systemctl start pve-ha-lrm
systemctl start pve-ha-crm

# 4. Se tutto fallisce, avviare in modalita locale
systemctl stop pve-cluster
pmxcfs -l
# /etc/pve sara accessibile ma in sola lettura locale
# Questo permette di accedere alla configurazione per diagnostica
```

### Recovery del Database pmxcfs

```bash
# Se il database SQLite di pmxcfs e corrotto
# Il database si trova in /var/lib/pve-cluster/config.db

# Backup del database corrente
cp /var/lib/pve-cluster/config.db /var/lib/pve-cluster/config.db.bak

# Verificare l'integrita
sqlite3 /var/lib/pve-cluster/config.db "PRAGMA integrity_check;"

# Se corrotto, recuperare da un altro nodo:
# Sul nodo funzionante:
scp /var/lib/pve-cluster/config.db root@<nodo-problematico>:/var/lib/pve-cluster/

# Riavviare
systemctl restart pve-cluster
```

---

## Errori Certificati {#errori-certificati}

### Sintomi

```bash
# "SSL: certificate verify failed"
# "TASK ERROR: SSL connection error"
# GUI Proxmox non accessibile via HTTPS
```

### Diagnostica

```bash
# Verificare i certificati
openssl x509 -in /etc/pve/nodes/<nodename>/pve-ssl.pem -text -noout
openssl x509 -in /etc/pve/pve-root-ca.pem -text -noout

# Verificare la scadenza
openssl x509 -in /etc/pve/nodes/<nodename>/pve-ssl.pem -enddate -noout

# Verificare la catena
openssl verify -CAfile /etc/pve/pve-root-ca.pem /etc/pve/nodes/<nodename>/pve-ssl.pem
```

### Rigenerare i Certificati

```bash
# Rigenerare i certificati del nodo
pvecm updatecerts --force

# Se non funziona, rigenerare manualmente
cd /etc/pve/nodes/<nodename>
rm pve-ssl.pem pve-ssl.key
pvecm updatecerts

# Riavviare i servizi
systemctl restart pveproxy
systemctl restart pvedaemon

# Rigenerare la CA root (ATTENZIONE: invalida tutti i certificati del cluster)
# Eseguire solo se strettamente necessario
rm /etc/pve/pve-root-ca.pem
rm /etc/pve/priv/pve-root-ca.key
pvecm updatecerts --force
# Poi su ogni nodo:
pvecm updatecerts --force
systemctl restart pveproxy
```

---

## HA Non Effettua il Failover {#ha-failover}

### Diagnostica HA

```bash
# Stato del HA manager
ha-manager status

# Output tipico:
# quorum OK, node1 (CRM master)
# service vm:100: started (node1)
# service vm:101: started (node2)
# service ct:200: started (node1)

# Log HA
journalctl -u pve-ha-crm --no-pager -n 50
journalctl -u pve-ha-lrm --no-pager -n 50

# Verificare la configurazione HA
cat /etc/pve/ha/resources.cfg
cat /etc/pve/ha/groups.cfg
cat /etc/pve/ha/manager_status
```

### Problemi Comuni HA

**VM non in HA failover:**

```bash
# Verificare che la VM sia configurata per HA
ha-manager status | grep <vmid>

# Se non presente, aggiungerla:
ha-manager add vm:<vmid> --group <ha-group> --state started

# Verificare il gruppo HA
cat /etc/pve/ha/groups.cfg
```

**HA non rileva il fallimento del nodo:**

```bash
# HA dipende dal quorum Corosync per rilevare il fallimento
pvecm status

# Se il nodo fallito e ancora visto come online:
# Il fencing potrebbe non funzionare
# Verificare i timeout HA
cat /etc/pve/datacenter.cfg | grep -E "ha:|fencing"
```

**VM resta in stato "fence" o "recovery":**

```bash
# Se una VM e bloccata in stato di recovery
ha-manager status
# service vm:100: fence (node2)  <- bloccata in fencing

# Se il nodo originale non e piu raggiungibile e il fencing non funziona:
# Rimuovere manualmente il lock
rm /etc/pve/nodes/<nodo-fallito>/qemu-server/<vmid>.conf.lock 2>/dev/null

# Forzare il recovery
ha-manager set vm:<vmid> --state started
```

---

## Fencing Non Funziona {#fencing}

### Cos'e il Fencing

Il fencing e il meccanismo che garantisce che un nodo fallito venga effettivamente "spento" prima di riavviare le sue VM su un altro nodo. Senza fencing, c'e il rischio di split-brain a livello VM.

### Configurazione Fencing

```bash
# Proxmox supporta diversi metodi di fencing:
# 1. IPMI/BMC (consigliato)
# 2. PDU (Power Distribution Unit)
# 3. Watchdog (software-based)

# Configurazione watchdog (piu semplice)
# In /etc/pve/datacenter.cfg:
ha: shutdown_policy=conditional

# Verificare che il watchdog sia attivo
cat /dev/watchdog
# Se restituisce "Device or resource busy": watchdog attivo

# Configurare il watchdog hardware (se disponibile)
modprobe ipmi_watchdog
# Aggiungere a /etc/modules:
echo "ipmi_watchdog" >> /etc/modules
```

### Diagnostica Fencing

```bash
# Verificare lo stato del watchdog
systemctl status watchdog-mux

# Log del fencing
journalctl -u pve-ha-crm | grep -i fence

# Testare il fencing (ATTENZIONE: questo RIAVVIA il nodo!)
# Solo in ambiente di test:
# echo 1 > /proc/sys/kernel/sysrq
# echo b > /proc/sysrq-trigger
```

---

## Ceph Health Warnings {#ceph-health}

### HEALTH_WARN

```bash
# Verificare i warning
ceph health detail

# Warning comuni e soluzioni:

# 1. "clock skew detected"
# I clock dei nodi non sono sincronizzati
chronyc tracking
chronyc sources -v
# Soluzione:
systemctl restart chrony
# O configurare un NTP server comune

# 2. "X nearfull osd(s)"
ceph osd df | sort -k5 -n
# Soluzione: aggiungere storage o rimuovere dati
ceph osd reweight-by-utilization

# 3. "pool X has too few placement groups"
ceph osd pool get <pool> pg_num
# Soluzione:
ceph osd pool set <pool> pg_num <nuovo-valore>

# 4. "X slow ops"
ceph daemon osd.<id> dump_ops_in_flight
# Soluzione: verificare dischi lenti (vedi sezione Ceph Slow Ops)

# 5. "noout flag(s) set"
# Flag impostato manualmente o automaticamente
ceph osd unset noout

# 6. "X osds down"
# Vedere sezione OSD Down
```

### HEALTH_ERR

```bash
# Errori critici

# 1. "X pgs are stuck inactive"
ceph pg dump_stuck inactive
# Soluzione: verificare che gli OSD siano tutti attivi
ceph osd tree

# 2. "X pgs degraded"
ceph pg dump_stuck degraded
ceph health detail
# Soluzione: attendere il recovery automatico se gli OSD sono in recovery
# Forzare il recovery se necessario:
ceph osd force-recovery osd.<id>

# 3. "X pgs undersized"
ceph pg dump_stuck undersized
# Causa: non abbastanza repliche disponibili
# Verificare il numero di OSD attivi vs repliche richieste

# 4. "X objects unfound"
ceph pg <pgid> list_unfound
# Soluzione: potrebbe richiedere il mark lost
# ATTENZIONE: questo comporta perdita di dati
# ceph pg <pgid> mark_unfound_lost delete

# 5. "mon election timed out"
# Vedere sezione MON Election Issues
```

---

## OSD Down e Recovery {#osd-down}

### Diagnostica OSD

```bash
# Stato degli OSD
ceph osd tree
# Mostra tutti gli OSD e il loro stato (up/down, in/out)

# Dettagli OSD specifico
ceph osd find <osd-id>
# Mostra il nodo e il dispositivo dell'OSD

# Log dell'OSD
journalctl -u ceph-osd@<osd-id> --no-pager -n 50

# Verificare il disco fisico
smartctl -a /dev/sdX
```

### Recuperare un OSD Down

```bash
# 1. Tentare il restart
systemctl start ceph-osd@<osd-id>

# 2. Se non si avvia, verificare i log
journalctl -u ceph-osd@<osd-id> --no-pager -n 100

# 3. Errori comuni:
# "leveldb error" o "rocksdb error" -> database OSD corrotto
# Soluzione: ricostruire il database
ceph-objectstore-tool --data-path /var/lib/ceph/osd/ceph-<id> --op repair

# "cannot open OSD superblock" -> disco non montato
mount | grep ceph-<osd-id>
mount /dev/sdX /var/lib/ceph/osd/ceph-<osd-id>

# 4. Se il disco e fallito, rimuovere l'OSD e aggiungerne uno nuovo
ceph osd out <osd-id>
# Attendere il rebalancing (ceph -w)
systemctl stop ceph-osd@<osd-id>
ceph osd purge <osd-id> --yes-i-really-mean-it

# Sostituire il disco fisico e creare nuovo OSD
ceph-volume lvm create --data /dev/sdX
```

### Gestire il Recovery

```bash
# Monitorare il progresso del recovery
ceph -w
# Oppure:
ceph status
# recovery_ratio: X/Y objects recovered

# Se il recovery e troppo lento, aumentare i limiti
ceph tell osd.* injectargs --osd-recovery-max-active 3
ceph tell osd.* injectargs --osd-recovery-sleep 0

# Se il recovery impatta troppo le prestazioni, rallentarlo
ceph tell osd.* injectargs --osd-recovery-max-active 1
ceph tell osd.* injectargs --osd-recovery-sleep 0.5
ceph tell osd.* injectargs --osd-max-backfills 1

# Flag utili durante le manutenzioni
ceph osd set noout      # Previene il rebalancing se un nodo va giu
ceph osd set norecover  # Ferma il recovery
ceph osd set nobackfill # Ferma il backfill

# Rimuovere i flag dopo la manutenzione
ceph osd unset noout
ceph osd unset norecover
ceph osd unset nobackfill
```

---

## MON Election Issues {#mon-election}

### Diagnostica MON

```bash
# Stato dei monitor
ceph mon stat
ceph mon dump
ceph quorum_status | jq .

# Log del monitor
journalctl -u ceph-mon@<hostname> --no-pager -n 100

# Verificare la comunicazione tra i MON
ceph mon_status | jq .
```

### Problemi Comuni MON

```bash
# 1. MON non raggiunge il quorum
# I MON richiedono la maggioranza (2 su 3, 3 su 5)
ceph mon stat
# "e3: 3 mons at {node1=10.0.0.1:6789, node2=10.0.0.2:6789, node3=10.0.0.3:6789},
#  election epoch 156, quorum 0,1,2 node1,node2,node3"

# Se il quorum non e raggiunto:
# Verificare la connettivita sulla porta 6789
nc -zv <mon-ip> 6789

# 2. MON con store corrotto
ceph-mon --cluster ceph -i <mon-id> --extract-monmap /tmp/monmap
# Se fallisce, il database del MON potrebbe essere corrotto

# Recovery: ricostruire il MON
systemctl stop ceph-mon@<hostname>
ceph-mon --cluster ceph -i <hostname> --extract-monmap /tmp/monmap
rm -rf /var/lib/ceph/mon/ceph-<hostname>/store.db
ceph-mon --cluster ceph -i <hostname> --mkfs --monmap /tmp/monmap
chown -R ceph:ceph /var/lib/ceph/mon/ceph-<hostname>
systemctl start ceph-mon@<hostname>

# 3. Clock skew tra MON
# I MON richiedono clock sincronizzati (< 0.05s di differenza)
chronyc tracking
# Se la differenza e > 50ms:
chronyc -a makestep
```

---

## Recovery da Total Cluster Failure {#total-failure}

### Scenario: Tutti i Nodi Down

Questa e la situazione peggiore: tutti i nodi del cluster sono spenti o non funzionanti contemporaneamente (es. blackout totale del data center).

### Procedura di Recovery

```bash
# FASE 1: Avviare UN nodo alla volta, iniziando dal primo nodo del cluster

# 1.1. Avviare il primo nodo (quello che era il CRM master se possibile)
# Attendere il boot completo

# 1.2. Verificare lo stato
systemctl status corosync
systemctl status pve-cluster

# Il nodo non avra quorum con un solo nodo attivo
pvecm status
# Quorum: 0

# 1.3. Forzare il quorum (TEMPORANEO)
pvecm expected 1

# 1.4. Verificare che /etc/pve sia accessibile
ls /etc/pve/nodes/

# FASE 2: Avviare gli altri nodi uno alla volta

# 2.1. Avviare il secondo nodo
# 2.2. Verificare che si unisca al cluster
pvecm status
pvecm nodes

# 2.3. Avviare il terzo nodo (e successivi)

# FASE 3: Ripristinare il quorum normale
# Una volta che tutti i nodi sono online:
pvecm expected <numero-totale-nodi>

# FASE 4: Verificare Ceph (se presente)
ceph status
ceph osd tree
# Se OSD sono down, avviarli:
systemctl start ceph-osd@<id>

# FASE 5: Verificare le VM e i container
qm list
pct list
# Avviare le VM che dovrebbero essere attive
# L'HA manager dovrebbe gestire automaticamente le VM HA
```

### Recovery con Cluster Corrotto

```bash
# Se la configurazione del cluster e corrotta e non si riesce ad avviare:

# 1. Avviare pmxcfs in modalita locale su OGNI nodo
systemctl stop pve-cluster
pmxcfs -l

# 2. Verificare e confrontare le configurazioni su ogni nodo
ls /etc/pve/nodes/
cat /etc/pve/corosync.conf

# 3. Se corosync.conf e corrotto, ricostruirlo
# Sul nodo master:
pvecm create <cluster-name> --link0 <ip>

# Sugli altri nodi:
pvecm add <master-ip>
```

---

## Comandi pvecm per Diagnostica {#pvecm-comandi}

### Riferimento Comandi

```bash
# === Stato del Cluster ===
pvecm status              # Stato completo del cluster
pvecm nodes               # Lista nodi con stato
pvecm expected <N>        # Impostare voti attesi (forzare quorum)

# === Gestione Nodi ===
pvecm create <name>       # Creare un nuovo cluster
pvecm add <ip>            # Unirsi a un cluster
pvecm delnode <nodename>  # Rimuovere un nodo dal cluster

# === Certificati ===
pvecm updatecerts         # Aggiornare i certificati
pvecm updatecerts --force # Forzare la rigenerazione

# === Corosync ===
corosync-cfgtool -s       # Stato interfacce Corosync
corosync-cmapctl          # Mappa configurazione Corosync
corosync-quorumtool -s    # Stato quorum dettagliato

# === Diagnostica Avanzata ===
# Verificare la comunicazione tra nodi
pvecm ping <nodename>

# Dump della configurazione Corosync attuale
cat /etc/pve/corosync.conf

# Verificare i processi del cluster
systemctl status corosync pve-cluster pvedaemon pveproxy \
    pve-ha-crm pve-ha-lrm pvestatd

# Log consolidato del cluster
journalctl -u corosync -u pve-cluster -u pve-ha-crm \
    --since "1 hour ago" --no-pager
```

### Script di Diagnostica Cluster

```bash
#!/bin/bash
# cluster-health-check.sh
# Eseguire su un nodo del cluster

echo "=== Proxmox Cluster Health Check ==="
echo "Data: $(date)"
echo "Nodo: $(hostname)"
echo ""

echo "--- Stato Cluster ---"
pvecm status 2>&1
echo ""

echo "--- Nodi ---"
pvecm nodes 2>&1
echo ""

echo "--- Corosync ---"
corosync-cfgtool -s 2>&1
echo ""

echo "--- Servizi ---"
for svc in corosync pve-cluster pvedaemon pveproxy pve-ha-crm pve-ha-lrm pvestatd; do
    STATUS=$(systemctl is-active $svc 2>/dev/null)
    printf "%-20s %s\n" "$svc" "$STATUS"
done
echo ""

echo "--- HA Status ---"
ha-manager status 2>&1
echo ""

if command -v ceph &>/dev/null; then
    echo "--- Ceph Status ---"
    ceph status 2>&1
    echo ""
    echo "--- Ceph OSD Tree ---"
    ceph osd tree 2>&1
    echo ""
fi

echo "--- Filesystem /etc/pve ---"
ls /etc/pve/ 2>&1 | head -20
echo ""

echo "--- Spazio Disco Nodo ---"
df -h / /var/lib/vz 2>/dev/null
echo ""

echo "=== Health Check Completato ==="
```

Questo script fornisce una panoramica rapida dello stato di salute del cluster e puo essere integrato in un sistema di monitoraggio o eseguito periodicamente come parte della manutenzione ordinaria.

---

## Letture primarie consigliate

- Proxmox VE Wiki — Cluster Manager. https://pve.proxmox.com/wiki/Cluster_Manager (retrieved 2026-04-27).
- Proxmox VE Admin Guide — High Availability. https://pve.proxmox.com/pve-docs/chapter-ha-manager.html (retrieved 2026-04-27).
- Corosync — Documentation. https://corosync.github.io/corosync/ (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 10.1 — `../10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/ha-manager-regole-e-gruppi.md`: HA fundamentals.
- Modulo 10.3 — `../10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/fencing-e-stonith.md`: fencing recovery.
- Modulo 17.3 — `troubleshooting-networking-post-migrazione.md`: spesso problemi cluster sono problemi rete.
