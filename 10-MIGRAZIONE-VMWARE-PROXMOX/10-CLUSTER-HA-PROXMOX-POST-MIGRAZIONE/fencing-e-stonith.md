# Fencing e STONITH: Protezione del Cluster

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 4 — Cluster HA post-migrazione · Modulo 10.3 (segue 10.2 live-migration, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 10.1 (HA Manager); concetti di consensus distribuito, split-brain; familiarita con IPMI/iLO/iDRAC e watchdog timer kernel.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. spiegare perche il fencing e prerequisito non opzionale per HA: senza fencing un nodo "isolato" puo continuare a scrivere su storage condiviso → corruzione e split-brain di dati;
> 2. distinguere **self-fencing** (watchdog hardware o softdog: il nodo si auto-elimina al timeout) da **STONITH attivo** (un altro nodo "spara" il nodo malfunzionante via IPMI/iLO/PDU);
> 3. configurare **watchdog hardware** (`iTCO_wdt`, `wdat_wdt`, `iAMT`) o software (`softdog`) in `/etc/default/pve-ha-manager` con `WATCHDOG_MODULE=...`;
> 4. configurare **fencing IPMI**: device IPMI accessibile out-of-band (rete management dedicata), credenziali isolate, test con `ipmitool -I lanplus -H ... power status`;
> 5. configurare il **modulo `fence-agents`** opzionale per Proxmox (community), con agenti per IPMI, iLO, iDRAC, AWS instance, vCenter, switch managed PDU;
> 6. testare il fencing in scenari controllati: kill `corosync`, disconnect rete cluster, hard freeze del kernel (`echo c > /proc/sysrq-trigger`); validare che il nodo sia effettivamente isolato in ≤ 60s;
> 7. confrontare il modello di fencing Proxmox (watchdog primario + IPMI come failsafe) con vSphere HA (datastore heartbeating + isolation response policy + APD/PDL handling).
> **Tempo stimato:** lettura 50-70 min · lab 240-360 min (configurare e testare fencing su cluster di test)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; corosync 3.1.x; pve-ha-manager 4.x; ipmitool 1.8.x; fence-agents 4.x.

## Mappa concettuale

```
+============================================================+
|     Fencing in Proxmox: livelli e meccanismi               |
+============================================================+
|                                                            |
|   LIVELLO 1: WATCHDOG (self-fencing)                       |
|   - Hardware (iTCO, iAMT, BMC) o software (softdog)        |
|   - Il nodo deve "kickare" il watchdog ogni N secondi      |
|   - Se non riceve kick → reset hardware automatico         |
|   - Trigger: nodo perde quorum → pmxcfs read-only          |
|     → pve-ha-lrm non puo dichiarare ack → watchdog scade   |
|     → reset → fencing implicito                            |
|                                                            |
|   LIVELLO 2: STONITH IPMI (active fencing, opzionale)      |
|   - Comunita: pacchetto `fence-agents` non default         |
|   - Un nodo survivor "spara" il nodo malfunzionante via    |
|     IPMI: `ipmitool -H <bmc-ip> ... power off`             |
|   - Richiede rete management isolata e credenziali fence   |
|                                                            |
|   LIVELLO 3: STONITH FISICO (manualmente, last resort)     |
|   - Operatore stacca cavo alimentazione, switch off PDU    |
|   - Solo per scenari catastrofici dove tutto il resto      |
|     fallisce                                               |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   FLUSSO TIPICO (con watchdog)                             |
|                                                            |
|   T0:   pve3 perde rete corosync                           |
|   T0+10s: pve3 perde quorum (token timeout)                |
|   T0+15s: pmxcfs su pve3 read-only                         |
|   T0+15s: pve-ha-lrm su pve3 stop-acking le risorse        |
|   T0+15s: watchdog su pve3 non riceve kick                 |
|   T0+60s: watchdog scade → reset hw del nodo               |
|   T0+60s: pve1+pve2 (con quorum) marcano pve3 fenced       |
|   T0+65s: CRM riassegna risorse pve3 a pve1/pve2           |
|   T0+90s: VM ex-pve3 up sui nuovi nodi                     |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Senza fencing, HA non e HA.** La promessa di HA e: "una VM gira sempre, anche se un nodo cade". Ma se il nodo "caduto" sta ancora scrivendo sul disco condiviso e la stessa VM viene avviata altrove, hai *due* VM con lo stesso file system → corruzione totale. Il fencing previene questo scenario garantendo che il nodo "sospetto" sia rimosso prima del failover.
2. **Watchdog e fencing implicito sufficiente per la maggior parte dei deployment.** Hardware watchdog (Intel TCO o equivalente) e affidabile e indipendente dal SO. Per deployment standard, configurare correttamente il watchdog (verifica con `dmesg | grep -i watchdog` e `cat /proc/sys/kernel/printk_devkmsg`) e tutto cio che serve.
3. **STONITH IPMI aggiunge un secondo livello di protezione.** Utile in scenari dove il watchdog potrebbe fallire (es. hang del kernel cosi grave che neanche il watchdog reagisce). Costo: complessita di configurazione, manutenzione credenziali fence, rischio di "fence loop" se mal configurato. Vale la pena per cluster a missione critica (banche, salute, infrastrutture critiche).
4. **Mai testare il fencing su un cluster di produzione senza prepararsi.** "Ho configurato il fencing IPMI" senza averlo mai testato = falsa sicurezza. Preparare uno scenario controllato (cluster lab gemello), eseguire fence test 5+ volte, validare i tempi e l'effetto sulle VM.
5. **Il fencing deve essere indipendente dalla rete di produzione.** Se il fencing IPMI usa la stessa rete che e caduta nel guasto, il fencing non potra eseguire. Servire IPMI/iLO su rete management dedicata (separate VLAN, separate switch, ideal: separate L2 broadcast domain).

---

## Introduzione

Il fencing (letteralmente "recintare", isolare) e il meccanismo che garantisce che un nodo non funzionante venga rimosso in modo sicuro dal cluster prima che le sue risorse vengano avviate su un altro nodo. Senza fencing, un cluster HA non puo operare in modo sicuro: il rischio e che la stessa VM venga eseguita contemporaneamente su due nodi diversi, causando corruzione dei dati.

STONITH ("Shoot The Other Node In The Head") e il termine usato nel mondo dei cluster per indicare il fencing basato sull'hardware: un meccanismo che forza lo spegnimento o il riavvio di un nodo problematico tramite un canale fuori-banda (out-of-band), indipendente dalla rete di produzione.

---

## Perche il Fencing e Critico

### Il Problema Fondamentale

Consideriamo questo scenario senza fencing:

```
SCENARIO SENZA FENCING (PERICOLOSO):

Tempo T0: Cluster con 3 nodi, VM 100 in esecuzione su Nodo 1
           VM 100 ha un disco su storage condiviso (Ceph/NFS)

Tempo T1: Nodo 1 diventa irraggiungibile (crash rete, non crash hardware)
           Corosync perde il contatto con Nodo 1
           Il cluster dichiara Nodo 1 come "offline"

Tempo T2: L'HA Manager decide di avviare VM 100 su Nodo 2
           MA... Nodo 1 e ancora in esecuzione!
           VM 100 gira ANCORA su Nodo 1 (il nodo non sa di essere "offline")

Tempo T3: VM 100 e in esecuzione SU ENTRAMBI i nodi
           Entrambe le istanze scrivono sullo stesso disco
           +-----------+          +-----------+
           |  Nodo 1   |          |  Nodo 2   |
           |  VM 100   |          |  VM 100   |
           |  (scrive) |          |  (scrive) |
           +-----+-----+          +-----+-----+
                 |                       |
                 v                       v
           +-----------------------------------+
           |     STORAGE CONDIVISO             |
           |     CORRUZIONE GARANTITA!         |
           +-----------------------------------+

RISULTATO: Filesystem corrotto, database danneggiato, dati persi
```

### La Soluzione: Fencing

```
SCENARIO CON FENCING (SICURO):

Tempo T0: VM 100 in esecuzione su Nodo 1

Tempo T1: Nodo 1 diventa irraggiungibile
           Corosync rileva la perdita

Tempo T2: Il cluster PRIMA esegue il fencing di Nodo 1
           +-------------------------------------------+
           | FENCING: Nodo 1 viene forzatamente spento |
           | tramite watchdog o IPMI/iLO/iDRAC         |
           +-------------------------------------------+
           Nodo 1 e GARANTITO essere spento

Tempo T3: SOLO DOPO il fencing confermato,
           l'HA Manager avvia VM 100 su Nodo 2

Tempo T4: VM 100 gira SOLO su Nodo 2
           Nessuna corruzione possibile
```

---

## Meccanismi di Fencing in Proxmox VE

### Panoramica dei Metodi

```
+------------------------------------------------------------------+
|              METODI DI FENCING PROXMOX VE                        |
+------------------------------------------------------------------+
|                                                                  |
|  +--------------------+    +--------------------+                |
|  | SOFTWARE WATCHDOG  |    | HARDWARE WATCHDOG  |                |
|  | (softdog)          |    | (iTCO_wdt, etc.)   |                |
|  | Affidabilita: 3/5  |    | Affidabilita: 4/5  |                |
|  | Costo: ZERO        |    | Costo: Incluso HW  |                |
|  +--------------------+    +--------------------+                |
|                                                                  |
|  +--------------------+    +--------------------+                |
|  | IPMI/iLO/iDRAC     |    | PDU Intelligente   |                |
|  | (rete out-of-band) |    | (power fencing)    |                |
|  | Affidabilita: 5/5  |    | Affidabilita: 5/5  |                |
|  | Costo: Incluso HW  |    | Costo: PDU smart   |                |
|  +--------------------+    +--------------------+                |
|                                                                  |
+------------------------------------------------------------------+
```

### Tabella Comparativa

| Metodo | Affidabilita | Velocita | Requisiti | Produzione |
|--------|-------------|----------|-----------|------------|
| softdog (software) | Media | 60 sec | Nessuno | Solo test |
| Hardware watchdog | Alta | 30-60 sec | Chip watchdog | Si |
| IPMI/iLO/iDRAC | Molto alta | 10-30 sec | BMC configurato | Raccomandato |
| PDU smart | Molto alta | 5-15 sec | PDU SNMP/IP | Datacentre |
| Combinato (watchdog+IPMI) | Massima | 10-30 sec | Entrambi | Best practice |

---

## Watchdog: Software e Hardware

### Software Watchdog (softdog)

Il software watchdog e un modulo del kernel Linux che riavvia il sistema se il servizio di watchdog smette di "nutrirlo" (watchdog feeding). E il meccanismo di fencing di default in Proxmox VE.

```bash
# Verificare se il software watchdog e caricato
lsmod | grep softdog

# Il modulo softdog viene caricato automaticamente da Proxmox
# quando l'HA e attivo e nessun hardware watchdog e disponibile

# Il file device del watchdog
ls -la /dev/watchdog
# crw------- 1 root root 10, 130 Mar 24 10:00 /dev/watchdog

# Verificare quale watchdog e attivo
cat /sys/class/watchdog/watchdog0/identity
# softdog oppure il nome del watchdog hardware

# Timeout del watchdog (in secondi)
cat /sys/class/watchdog/watchdog0/timeout
# Default: 10 secondi (ma Proxmox HA lo configura diversamente)
```

**Come funziona il software watchdog:**

```
+------------------------------------------------------------------+
|              CICLO DEL SOFTWARE WATCHDOG                         |
+------------------------------------------------------------------+
|                                                                  |
|  Funzionamento NORMALE:                                          |
|                                                                  |
|  pve-ha-lrm (LRM) --> apre /dev/watchdog                       |
|      |                                                           |
|      +--> ogni N secondi scrive su /dev/watchdog ("feeding")    |
|      |                                                           |
|      +--> il kernel azzera il timer del watchdog                |
|      |                                                           |
|      +--> il sistema rimane in esecuzione                       |
|                                                                  |
|  Funzionamento in ERRORE:                                        |
|                                                                  |
|  pve-ha-lrm smette di "nutrire" il watchdog                    |
|  (perche ha perso il quorum o il nodo e in stato critico)       |
|      |                                                           |
|      +--> il timer del watchdog scade                           |
|      |                                                           |
|      +--> il kernel triggera un REBOOT forzato                  |
|      |                                                           |
|      +--> il nodo viene riavviato                               |
|      |                                                           |
|      +--> dopo il reboot, il nodo rientra nel cluster            |
|                                                                  |
+------------------------------------------------------------------+
```

**Limiti del software watchdog:**
- Dipende dal kernel Linux: se il kernel va in panic in modo anomalo, il watchdog potrebbe non funzionare
- Non puo spegnere il sistema in caso di freeze hardware totale
- Non funziona se il sistema e bloccato a livello di firmware/hardware
- Adeguato solo per ambienti di test o non critici

### Hardware Watchdog

Il hardware watchdog e un chip presente sulla scheda madre del server che opera indipendentemente dal sistema operativo. Se il sistema operativo non "nutre" il watchdog entro il timeout, il chip forza un hard reset.

**Watchdog hardware comuni:**

| Chip | Server | Modulo Kernel |
|------|--------|---------------|
| iTCO_wdt | Intel (la maggior parte) | iTCO_wdt |
| SP5100 TCO | AMD EPYC | sp5100_tco |
| HPE iLO watchdog | HPE ProLiant | hpwdt |
| Dell WDAT | Dell PowerEdge | wdat_wdt |
| Supermicro | Supermicro X11/X12 | iTCO_wdt |

### Configurazione del Hardware Watchdog

```bash
# ============================================================
# PASSO 1: Identificare il watchdog hardware disponibile
# ============================================================

# Cercare i moduli watchdog disponibili
ls /lib/modules/$(uname -r)/kernel/drivers/watchdog/

# Provare a caricare il modulo iTCO (comune su sistemi Intel)
modprobe iTCO_wdt

# Verificare se il watchdog hardware e stato rilevato
dmesg | grep -i watchdog

# Output esempio (successo):
# iTCO_wdt: Intel TCO WatchDog Timer Driver v1.11
# iTCO_wdt: Found a Intel PCH TCO device (Version=6, TCOBASE=0x0400)
# iTCO_wdt: initialized. heartbeat=30 sec (nowayout=0)

# Verificare il device
cat /sys/class/watchdog/watchdog0/identity
# Dovrebbe mostrare "iTCO_wdt" o simile (non "softdog")

# ============================================================
# PASSO 2: Configurare il caricamento automatico del modulo
# ============================================================

# Aggiungere il modulo al caricamento automatico
echo "iTCO_wdt" > /etc/modules-load.d/watchdog.conf

# Per server AMD EPYC:
# echo "sp5100_tco" > /etc/modules-load.d/watchdog.conf

# Per server HPE:
# echo "hpwdt" > /etc/modules-load.d/watchdog.conf

# ============================================================
# PASSO 3: Impedire il caricamento del software watchdog
# ============================================================

# Blacklistare il softdog per assicurarsi che venga usato l'hardware
echo "blacklist softdog" > /etc/modprobe.d/blacklist-softdog.conf

# Aggiornare initramfs
update-initramfs -u -k all

# ============================================================
# PASSO 4: Riavviare e verificare
# ============================================================

reboot

# Dopo il riavvio, verificare
cat /sys/class/watchdog/watchdog0/identity
# Deve mostrare il watchdog HARDWARE, non softdog

wdctl
# Output esempio:
# Device:        /dev/watchdog0
# Identity:      iTCO_wdt [version 6]
# Timeout:       30s
# Pre-timeout:    0s
# Timeleft:      30s
# FLAG           DESCRIPTION               STATUS BOOT-STATUS
# KEEPALIVEPING  Keep alive ping reply          1           0
# MAGICCLOSE     Supports magic close char      0           0
# SETTIMEOUT     Set timeout (in seconds)       0           0
```

### Configurazione Avanzata del Watchdog in Proxmox

```bash
# Il file di configurazione del watchdog per HA e in:
# /etc/default/pve-ha-manager

# Configurazione del watchdog nel datacenter
# In /etc/pve/datacenter.cfg:
# (Proxmox gestisce automaticamente il watchdog, ma si puo verificare)

# Verificare che il servizio HA stia usando il watchdog corretto
systemctl status watchdog-mux.service

# Proxmox usa un multiplexer watchdog (watchdog-mux) che:
# 1. Apre /dev/watchdog
# 2. Fornisce un socket unix ai servizi HA
# 3. Se il servizio HA smette di comunicare, il watchdog non viene piu nutrito
# 4. Il watchdog (hardware o software) riavvia il sistema

# Controllare il log del watchdog
journalctl -u watchdog-mux.service

# Verificare che il watchdog sia attivo nell'HA
ha-manager status | grep -i fence
```

---

## IPMI/iLO/iDRAC: Fencing Out-of-Band

### Concetto

Il fencing IPMI utilizza l'interfaccia di gestione fuori-banda (BMC - Baseboard Management Controller) per forzare lo spegnimento o il riavvio di un nodo. Questo e completamente indipendente dal sistema operativo e dalla rete di produzione.

```
+------------------------------------------------------------------+
|              FENCING IPMI                                        |
+------------------------------------------------------------------+
|                                                                  |
|  Nodo 1 (irraggiungibile)        Nodo 2 (funzionante)          |
|  +--------------------+          +--------------------+          |
|  | Proxmox VE         |          | Proxmox VE         |          |
|  | (crash/freeze)     |          | (CRM master)       |          |
|  +--------------------+          +--------------------+          |
|  | BMC (IPMI/iLO)     |          |        |           |          |
|  | IP: 10.10.50.11    |          |        |           |          |
|  +--------+-----------+          +--------+-----------+          |
|           |                               |                      |
|           |    Rete IPMI dedicata         |                      |
|           +-------------------------------+                      |
|                                                                  |
|  Nodo 2 invia: ipmitool power off --> BMC di Nodo 1            |
|  BMC di Nodo 1 spegne fisicamente il server                    |
|  Nodo 2 conferma: fencing riuscito                              |
|  Nodo 2 avvia le VM di Nodo 1                                  |
+------------------------------------------------------------------+
```

### Configurazione IPMI per Fencing

```bash
# ============================================================
# PASSO 1: Configurare IPMI su ogni server (via BIOS o tool)
# ============================================================

# Verificare che IPMI sia raggiungibile da ogni nodo
ipmitool -I lanplus -H 10.10.50.11 -U admin -P password chassis status
ipmitool -I lanplus -H 10.10.50.12 -U admin -P password chassis status
ipmitool -I lanplus -H 10.10.50.13 -U admin -P password chassis status

# Output atteso:
# System Power         : on
# Power Overload       : false
# Power Interlock      : inactive
# Main Power Fault     : false
# Power Control Fault  : false

# ============================================================
# PASSO 2: Testare il power control via IPMI
# ============================================================

# Testare lo spegnimento (su un nodo di TEST, non in produzione!)
ipmitool -I lanplus -H 10.10.50.11 -U admin -P password chassis power off

# Verificare lo stato
ipmitool -I lanplus -H 10.10.50.11 -U admin -P password chassis power status
# Output: Chassis Power is off

# Riaccendere
ipmitool -I lanplus -H 10.10.50.11 -U admin -P password chassis power on

# Reset forzato
ipmitool -I lanplus -H 10.10.50.11 -U admin -P password chassis power reset

# ============================================================
# PASSO 3: Configurare il fence agent in Proxmox
# ============================================================

# Proxmox supporta fence agents tramite il pacchetto fence-agents-pve
apt install fence-agents-pve

# Verificare i fence agents disponibili
ls /usr/sbin/fence_*

# Il fence agent principale per IPMI:
fence_ipmilan --help

# Test del fence agent:
fence_ipmilan --ip=10.10.50.11 --username=admin --password=password \
    --action=status --lanplus

# Output: Status: ON
```

### Configurazione di fence_pve

Proxmox VE utilizza il proprio agente di fencing (`fence_pve`) che si integra con il sistema HA:

```bash
# Il file di configurazione del fencing e in:
# /etc/pve/ha/fence.cfg (non esiste per default)

# Per configurare il fencing IPMI, creare/modificare:
# /etc/pve/datacenter.cfg

# Aggiungere la configurazione del fencing
cat >> /etc/pve/datacenter.cfg << 'EOF'
fencing: watchdog
# Il fencing di default usa il watchdog
# Per aggiungere IPMI come fencing aggiuntivo, si usa ha/fence.cfg
EOF

# Configurazione avanzata in /etc/pve/ha/fence.cfg
# Formato: <tipo> <nodo> <parametri>

# Esempio per 3 nodi con IPMI:
cat > /etc/pve/ha/fence.cfg << 'FENCECFG'
# Fencing configuration
# device <nome> <agente> <parametri>
# node <nodo> <device-list>

device ipmi1 fence_ipmilan ipaddr=10.10.50.11,login=admin,passwd=password,lanplus=1,power_timeout=30
device ipmi2 fence_ipmilan ipaddr=10.10.50.12,login=admin,passwd=password,lanplus=1,power_timeout=30
device ipmi3 fence_ipmilan ipaddr=10.10.50.13,login=admin,passwd=password,lanplus=1,power_timeout=30

node pve1 ipmi1
node pve2 ipmi2
node pve3 ipmi3
FENCECFG
```

### Configurazione per Vendor Specifici

**Dell iDRAC:**

```bash
# Test connettivita iDRAC
fence_ipmilan --ip=10.10.50.11 --username=root --password=calvin \
    --action=status --lanplus --ipport=623

# Alternativa con fence_idrac (se disponibile)
# apt install fence-agents-all
fence_idrac --ip=10.10.50.11 --username=root --password=calvin \
    --action=status --ssl --ssl-insecure
```

**HPE iLO:**

```bash
# Test connettivita iLO
fence_ipmilan --ip=10.10.50.11 --username=Administrator --password=password \
    --action=status --lanplus

# Alternativa con fence_ilo via REST API
fence_ilo5_ssh --ip=10.10.50.11 --username=Administrator --password=password \
    --action=status

# HPE iLO offre anche la possibilita di usare hponcfg per configurazione
```

**Supermicro IPMI:**

```bash
# Supermicro usa IPMI standard
fence_ipmilan --ip=10.10.50.11 --username=ADMIN --password=ADMIN \
    --action=status --lanplus

# Su alcuni modelli Supermicro, potrebbe essere necessario:
fence_ipmilan --ip=10.10.50.11 --username=ADMIN --password=ADMIN \
    --action=status --lanplus --ipmitool-path=/usr/bin/ipmitool \
    --power-timeout=30 --login-timeout=15
```

---

## Test del Fencing

### Procedura di Test Completa

```bash
# ============================================================
# FASE 1: Verifica prerequisiti
# ============================================================

# Verificare watchdog attivo
wdctl
cat /sys/class/watchdog/watchdog0/identity

# Verificare IPMI raggiungibile (se configurato)
for node_ip in 10.10.50.11 10.10.50.12 10.10.50.13; do
    echo "Testing IPMI $node_ip:"
    ipmitool -I lanplus -H $node_ip -U admin -P password chassis power status
done

# Verificare HA manager status
ha-manager status

# ============================================================
# FASE 2: Test watchdog (su nodo di TEST)
# ============================================================

# ATTENZIONE: Questo test riavviera il nodo!
# Eseguire SOLO su un nodo di test o in una finestra di manutenzione

# Metodo 1: Simulare perdita quorum
# Bloccare il traffico corosync per forzare la perdita di quorum
iptables -A INPUT -p udp --dport 5405:5412 -j DROP
iptables -A OUTPUT -p udp --dport 5405:5412 -j DROP

# Il watchdog dovrebbe riavviare il nodo entro ~120 secondi
# (il timeout dipende dalla configurazione HA)

# Metodo 2: Trigger SysRq (crash immediato)
echo c > /proc/sysrq-trigger

# Metodo 3: Verificare il comportamento del watchdog senza riavvio
# (test non distruttivo - solo verifica che il watchdog sia attivo)
cat /sys/class/watchdog/watchdog0/state
# active = il watchdog e in uso
# Il timeleft dovrebbe aggiornarsi ogni volta che viene letto

# ============================================================
# FASE 3: Test IPMI (non distruttivo)
# ============================================================

# Test azione "status" (non spegne nulla)
fence_ipmilan --ip=10.10.50.11 --username=admin --password=password \
    --action=status --lanplus
# Output atteso: Status: ON

# Test azione "list" (elenca i nodi gestibili)
fence_ipmilan --ip=10.10.50.11 --username=admin --password=password \
    --action=list --lanplus

# ============================================================
# FASE 4: Test fencing completo (DISTRUTTIVO - solo in manutenzione)
# ============================================================

# Da Nodo 2, forzare il fencing di Nodo 1:
fence_ipmilan --ip=10.10.50.11 --username=admin --password=password \
    --action=off --lanplus

# Verificare che Nodo 1 sia spento
fence_ipmilan --ip=10.10.50.11 --username=admin --password=password \
    --action=status --lanplus
# Output atteso: Status: OFF

# Riaccendere Nodo 1
fence_ipmilan --ip=10.10.50.11 --username=admin --password=password \
    --action=on --lanplus

# ============================================================
# FASE 5: Test failover end-to-end
# ============================================================

# 1. Creare una VM di test con HA
qm create 9999 --name test-ha-fencing --memory 512 --net0 virtio,bridge=vmbr0
qm start 9999
ha-manager add vm:9999 --state started --max_restart 3 --max_relocate 2

# 2. Verificare su quale nodo gira
ha-manager status | grep 9999
# service vm:9999 (pve1, started)

# 3. Spegnere il nodo via IPMI (simulando un crash hardware)
fence_ipmilan --ip=10.10.50.11 --username=admin --password=password \
    --action=off --lanplus

# 4. Da un altro nodo, monitorare il failover
watch -n 2 'ha-manager status'

# 5. Verificare che la VM venga riavviata su un altro nodo
# service vm:9999 (pve2, started)

# 6. Riaccendere il nodo fenced
fence_ipmilan --ip=10.10.50.11 --username=admin --password=password \
    --action=on --lanplus

# 7. Pulire il test
ha-manager remove vm:9999
qm stop 9999
qm destroy 9999
```

---

## Cosa Succede Senza Fencing Corretto

### Scenari di Fallimento

```
Scenario 1: NESSUN fencing configurato
  - L'HA Manager NON sposta le VM quando un nodo cade
  - Le VM rimangono in stato "unknown" indefinitamente
  - L'operatore deve intervenire manualmente
  - RISULTATO: Nessuna alta disponibilita effettiva

Scenario 2: Solo software watchdog con kernel hang
  - Il kernel si blocca (non panic, ma hang)
  - Il software watchdog e implementato nel kernel
  - Se il kernel e bloccato, il watchdog potrebbe non scattare
  - RISULTATO: Nodo zombie, possibile split-brain

Scenario 3: Fencing IPMI ma rete IPMI non funzionante
  - L'HA Manager tenta il fencing via IPMI
  - La rete IPMI e irraggiungibile (cavo staccato, switch guasto)
  - Il fencing FALLISCE
  - L'HA Manager NON avvia le VM su un altro nodo
  - RISULTATO: VM ferme, nessun failover

Scenario 4: Watchdog + IPMI configurati correttamente
  - Il nodo perde connettivita cluster
  - Il watchdog locale riavvia il nodo (self-fencing)
  - Contemporaneamente, il cluster tenta il fencing IPMI
  - Il nodo viene riavviato con certezza
  - L'HA Manager avvia le VM su un altro nodo
  - RISULTATO: Failover corretto e sicuro
```

### Log di un Fencing Riuscito

```bash
# Esempio di log durante un fencing watchdog riuscito:

# Sui nodi rimanenti (CRM master):
journalctl -u pve-ha-crm --since "5 minutes ago"

# Mar 24 14:30:15 pve2 pve-ha-crm[1234]: node 'pve1': state changed from 'online' to 'unknown'
# Mar 24 14:30:20 pve2 pve-ha-crm[1234]: node 'pve1': state changed from 'unknown' to 'fence'
# Mar 24 14:30:21 pve2 pve-ha-crm[1234]: fencing node 'pve1'
# Mar 24 14:30:22 pve2 pve-ha-crm[1234]: roles/kill watchdog for node 'pve1' successful
# Mar 24 14:31:30 pve2 pve-ha-crm[1234]: fencing: acknowledged - Loss of node 'pve1' confirmed
# Mar 24 14:31:31 pve2 pve-ha-crm[1234]: recover service 'vm:100' from fenced node 'pve1' to node 'pve2'
# Mar 24 14:31:32 pve2 pve-ha-crm[1234]: service 'vm:100': state changed from 'started' to 'recovery'
# Mar 24 14:31:45 pve2 pve-ha-lrm[5678]: starting service vm:100
# Mar 24 14:32:00 pve2 pve-ha-lrm[5678]: service vm:100 started successfully
# Mar 24 14:32:01 pve2 pve-ha-crm[1234]: service 'vm:100': state changed from 'recovery' to 'started'

# Sul nodo fenced (dopo il reboot, nei log del boot):
# Mar 24 14:30:25 pve1 kernel: watchdog: watchdog0: watchdog did not stop!
# Mar 24 14:30:25 pve1 kernel: Restarting system
```

---

## Confronto con VMware HA Isolation Response

### VMware HA e l'Isolamento Host

In VMware vSphere, quando un host viene dichiarato "isolated" (non raggiungibile dagli altri host ma potenzialmente ancora funzionante), l'amministratore puo configurare diverse risposte:

```
+------------------------------------------+-------------------------------------------+
| VMware Host Isolation Response           | Proxmox VE Fencing Equivalente            |
+------------------------------------------+-------------------------------------------+
| "Leave powered on"                       | Nessun equivalente diretto                |
| - L'host mantiene le VM accese           | (Proxmox richiede fencing per HA)         |
| - Nessun failover                        |                                           |
+------------------------------------------+-------------------------------------------+
| "Shut down and restart VMs"              | Watchdog fencing                          |
| - L'host spegne le VM                    | - Il watchdog riavvia il nodo             |
| - vSphere HA le riavvia altrove          | - HA avvia le VM altrove                  |
+------------------------------------------+-------------------------------------------+
| "Power off and restart VMs"              | IPMI fencing                              |
| - Force power off VM                     | - IPMI spegne il nodo                     |
| - vSphere HA le riavvia altrove          | - HA avvia le VM altrove                  |
+------------------------------------------+-------------------------------------------+

VMware aggiuntivo:
+------------------------------------------+-------------------------------------------+
| Datastore Heartbeating                   | Nessun equivalente                        |
| - Heartbeat su datastore condiviso       | (Proxmox usa solo rete per heartbeat)     |
| - Distingue isolamento da crash          |                                           |
+------------------------------------------+-------------------------------------------+
| VM Component Protection (VMCP)           | Nessun equivalente diretto                |
| - APD (All Paths Down)                   | (comportamento default: errore VM)        |
| - PDL (Permanent Device Loss)            |                                           |
+------------------------------------------+-------------------------------------------+
```

### Differenze Chiave

```
VMware:
  1. Rileva l'isolamento dell'host
  2. L'host ISOLATO decide cosa fare delle proprie VM
  3. vSphere HA sul lato cluster riavvia le VM altrove
  4. Doppio livello: risposta host + risposta cluster
  5. Datastore heartbeat come secondo canale di rilevamento

Proxmox:
  1. Rileva la perdita del nodo (corosync)
  2. Il cluster FENCES il nodo (il nodo non decide, viene forzato)
  3. Solo DOPO il fencing, le VM vengono avviate altrove
  4. Singolo livello: fencing = garanzia che il nodo sia spento
  5. Solo rete per il rilevamento (nessun datastore heartbeat)
```

---

## Best Practice per il Fencing in Produzione

### Checklist di Configurazione

```
[ ] Hardware watchdog configurato e verificato su tutti i nodi
[ ] softdog blacklistato (se hardware watchdog disponibile)
[ ] IPMI/iLO/iDRAC configurato su tutti i nodi
[ ] Rete IPMI dedicata e separata dalla rete di produzione
[ ] Credenziali IPMI documentate in modo sicuro
[ ] Test di fencing eseguito su ogni nodo (almeno una volta)
[ ] Test di failover end-to-end completato con successo
[ ] Monitoraggio dello stato del watchdog attivo
[ ] Monitoraggio della raggiungibilita IPMI attivo
[ ] Procedure di recovery documentate
[ ] Tempi di fencing misurati e documentati
```

### Rete IPMI: Sicurezza e Configurazione

```bash
# La rete IPMI DEVE essere isolata e protetta

# Best practice per la rete IPMI:
# 1. VLAN dedicata, non raggiungibile da Internet
# 2. Credenziali forti (non usare i default!)
# 3. Accesso limitato solo ai nodi del cluster
# 4. Firmware BMC aggiornato
# 5. HTTPS abilitato (se supportato)
# 6. IPMI su porta di rete dedicata (non condivisa)

# Cambiare la password IPMI di default
ipmitool -I lanplus -H 10.10.50.11 -U admin -P default_password \
    user set password 2 NewSecurePassword123!

# Verificare gli utenti IPMI
ipmitool -I lanplus -H 10.10.50.11 -U admin -P NewSecurePassword123! \
    user list

# Disabilitare utenti non necessari
ipmitool -I lanplus -H 10.10.50.11 -U admin -P NewSecurePassword123! \
    user disable <user-id>
```

### Script di Verifica Periodica del Fencing

```bash
#!/bin/bash
# /usr/local/bin/check-fencing.sh
# Eseguire periodicamente via cron per verificare che il fencing sia funzionante

LOG="/var/log/fencing-check.log"
ERRORS=0

echo "$(date): Fencing check started" >> $LOG

# 1. Verificare watchdog
WD_IDENTITY=$(cat /sys/class/watchdog/watchdog0/identity 2>/dev/null)
if [ -z "$WD_IDENTITY" ]; then
    echo "$(date): CRITICAL - No watchdog device found!" >> $LOG
    ERRORS=$((ERRORS + 1))
elif [ "$WD_IDENTITY" = "softdog" ]; then
    echo "$(date): WARNING - Using software watchdog (softdog)" >> $LOG
else
    echo "$(date): OK - Hardware watchdog: $WD_IDENTITY" >> $LOG
fi

# 2. Verificare watchdog-mux
if ! systemctl is-active --quiet watchdog-mux.service; then
    echo "$(date): CRITICAL - watchdog-mux service not running!" >> $LOG
    ERRORS=$((ERRORS + 1))
fi

# 3. Verificare raggiungibilita IPMI (se configurato)
IPMI_HOSTS="10.10.50.11 10.10.50.12 10.10.50.13"
for host in $IPMI_HOSTS; do
    if ping -c 1 -W 2 $host > /dev/null 2>&1; then
        echo "$(date): OK - IPMI $host raggiungibile" >> $LOG
    else
        echo "$(date): CRITICAL - IPMI $host NON raggiungibile!" >> $LOG
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. Verificare HA manager
if ! ha-manager status 2>/dev/null | grep -q "quorum OK"; then
    echo "$(date): CRITICAL - HA Manager quorum not OK!" >> $LOG
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -gt 0 ]; then
    echo "$(date): FENCING CHECK FAILED - $ERRORS errors found" >> $LOG
    # Inviare alert (mail, Telegram, etc.)
    # mail -s "Fencing Check FAILED on $(hostname)" admin@esempio.it < $LOG
    exit 2
fi

echo "$(date): Fencing check completed - ALL OK" >> $LOG
exit 0
```

### Cron Job per la Verifica

```bash
# Aggiungere al crontab
crontab -e

# Verifica ogni 5 minuti
*/5 * * * * /usr/local/bin/check-fencing.sh
```

---

## Troubleshooting del Fencing

### Fencing Non Funziona

```bash
# 1. Verificare che il watchdog sia attivo
wdctl
systemctl status watchdog-mux.service
journalctl -u watchdog-mux.service --since "1 hour ago"

# 2. Verificare che l'HA Manager veda il watchdog
ha-manager status
# Se mostra "no fencing configured", il watchdog non e rilevato

# 3. Controllare i log HA
journalctl -u pve-ha-crm --since "1 hour ago" | grep -i fence

# 4. Se il fencing fallisce, cercare errori specifici
journalctl -u pve-ha-crm --since "1 hour ago" | grep -i "error\|fail\|timeout"

# 5. Verificare i permessi del device watchdog
ls -la /dev/watchdog*
# Deve essere accessibile a root
```

### Fencing Troppo Lento

```bash
# Il tempo di fencing dipende da:
# 1. Token timeout di corosync (default 1000ms, configurabile)
# 2. Timeout del watchdog (default 60-120 secondi)
# 3. Timeout IPMI (configurabile nel fence agent)
# 4. Tempo di boot del nodo (per il recovery)

# Per ridurre il tempo di fencing:

# A. Ridurre il token timeout (attenzione: troppo basso = falsi positivi)
# In corosync.conf, sezione totem:
#   token: 3000   (3 secondi anziche il default)

# B. Configurare IPMI come fencing primario (piu veloce del watchdog)
# Il watchdog richiede che il timeout scada
# IPMI spegne immediatamente il nodo

# C. Ottimizzare il tempo di boot del nodo
# - SSD per il boot
# - Disabilitare test di memoria nel BIOS
# - Ridurre il timeout GRUB
```

---

## Conclusioni

Il fencing e la colonna portante della sicurezza dei dati in un cluster HA. Un cluster Proxmox VE senza fencing correttamente configurato e testato non puo essere considerato un ambiente di produzione affidabile.

La combinazione di hardware watchdog e fencing IPMI offre il massimo livello di protezione: il watchdog garantisce il self-fencing locale, mentre IPMI fornisce un canale fuori-banda per il fencing remoto. Entrambi i meccanismi devono essere testati regolarmente e monitorati continuamente.

Il passaggio da VMware a Proxmox richiede un cambio di mentalita riguardo al fencing: mentre VMware offre un sistema "chiavi in mano" con datastore heartbeating e isolation response configurabili, Proxmox richiede una configurazione esplicita ma offre un controllo piu diretto sul meccanismo di protezione.

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — Watchdog hardware vs softdog: validazione pratica.** Per verificare quale watchdog e attivo: `dmesg | grep -i watchdog` mostra il driver caricato (es. `iTCO_wdt: Intel TCO WatchDog Timer Driver v1.11`). `lsmod | grep -E "iTCO|softdog"` conferma se il modulo e attivo. Se vedi `softdog`: il sistema usa watchdog software, sufficiente per lab e produzione non critica, ma rischiosa per kernel hang. Per upgrade a hardware: identificare il chip (es. Intel C621 PCH supporta iTCO), abilitare in `/etc/modules` e `/etc/default/pve-ha-manager` con `WATCHDOG_MODULE=iTCO_wdt`, riavviare. Verifica funzionamento con test controllato: `echo 1 > /dev/watchdog && sleep 5 && echo V > /dev/watchdog` (chiusura magica = no reset). Fonte: [Linux kernel — Watchdog API](https://www.kernel.org/doc/html/latest/watchdog/watchdog-api.html), retrieved 2026-04-27.

> **Errore comune — Fencing IPMI con credenziali sulla rete di produzione.** Sintomo: durante un guasto di rete, il fencing IPMI fallisce perche i nodi survivor non possono raggiungere il BMC del nodo guasto (la rete e caduta proprio mentre serve). Causa: IPMI configurato sulla stessa rete di produzione/cluster invece che su rete management dedicata. Soluzione: separare IPMI/iLO/iDRAC su VLAN management dedicata, su switch fisicamente separati se possibile, con power independente. Validare con: spegnere uno switch di produzione (lab!) e verificare che IPMI sia ancora raggiungibile dai nodi survivor. Fonte: [Red Hat — IPMI fencing best practices](https://access.redhat.com/articles/27246), retrieved 2026-04-27.

> **Caso reale — Fencing loop in cluster mal configurato.** Cluster a 4 nodi, fencing IPMI configurato in modo simmetrico (ogni nodo puo fence ogni altro). Durante un guasto rete intermittente, due nodi si fencavano a vicenda in continuo: pve1 vede pve2 down → fence pve2 → pve2 reboot → durante reboot, pve2 vede pve1 down → fence pve1 → pve1 reboot → ... loop infinito, cluster down. Causa: nessun "delay" o "majority check" prima di eseguire fence. Soluzione: introdurre delay random tra rilevamento failure ed esecuzione fence; richiedere quorum esplicito (>= n/2 + 1 nodi che concordano sulla diagnosi) prima di fence; logging dettagliato di ogni decisione fence per analisi post-incidente. Lezione: il fencing automatico va testato anche per gli scenari "no-progress" (rete instabile, non solo "rete down"). Fonte: pattern community Pacemaker/Corosync, [Cluster Labs — Fencing pitfalls](https://wiki.clusterlabs.org/wiki/Fencing), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — perche fencing.** Argomenta in 10-12 righe perche un cluster HA *senza* fencing puo causare corruzione dati anche se la rete di produzione e ridondata e i nodi sono affidabili. Includi un esempio concreto con storage condiviso (Ceph o iSCSI) dove la mancanza di fencing porta a "duelling writes".

2. **Lab — verifica watchdog attivo.** Sul tuo cluster Proxmox: (a) `dmesg | grep -i watchdog` per identificare il driver; (b) `lsmod | grep -E "iTCO|softdog|wdat"` per moduli caricati; (c) verificare che `/dev/watchdog` esista; (d) controllare `/etc/default/pve-ha-manager` per la configurazione `WATCHDOG_MODULE`. Documentare il risultato. Se softdog: argomentare se passare a hardware in produzione (pro/contro).

3. **Scenario — fence design per cluster banking.** Un cluster a 5 nodi ospita transazioni finanziarie real-time. RTO target = 60 secondi. Disegna in 15-20 righe il design fencing: (a) watchdog hardware + IPMI come secondo livello; (b) rete management isolata con switch ridondati; (c) policy "strict majority" per fence; (d) audit logging di ogni decisione fence in SIEM; (e) test quarterly con fence di un nodo random e validazione end-to-end. Argomenta come ognuno di questi mitiga rischi specifici.

4. **Stretch — script fence-test automatizzato.** Scrivere uno script Bash che, dato un nodo target nel cluster: (1) verifica preconditions (cluster Quorate, watchdog attivo, IPMI raggiungibile); (2) "isola" il nodo simulando perdita rete (`iptables -A INPUT -p udp --dport 5404:5405 -j DROP`); (3) attende 90s; (4) verifica che il nodo sia stato fenced (reboot avvenuto, rejoined); (5) verifica che le risorse HA siano state migrate; (6) ripristina la rete (rimuove la regola iptables). Output strutturato JSON con timestamp di ogni step.

## Auto-valutazione

1. Differenza fra self-fencing (watchdog) e STONITH attivo (IPMI).
2. Cosa succede se HA e abilitato ma watchdog non e attivo?
3. Quando il watchdog softdog puo fallire e perche hardware e preferibile in produzione?
4. Perche la rete IPMI deve essere indipendente dalla rete cluster/produzione?
5. Cos'e un "fence loop" e come prevenirlo?
6. Come si verifica che il watchdog sia effettivamente attivo sul nodo Proxmox?
7. Quale e il tempo tipico tra perdita quorum e self-fencing per softdog default 60s?
8. Quale comando ipmitool si usa per testare la raggiungibilita di un BMC?

## Letture primarie consigliate

- Proxmox VE Admin Guide — High Availability (fencing). https://pve.proxmox.com/pve-docs/chapter-ha-manager.html#ha_manager_fencing (retrieved 2026-04-27).
- Linux kernel — Watchdog API. https://www.kernel.org/doc/html/latest/watchdog/watchdog-api.html (retrieved 2026-04-27).
- ipmitool(1) man page. https://linux.die.net/man/1/ipmitool (retrieved 2026-04-27).
- Red Hat — Fencing Best Practices. https://access.redhat.com/articles/27246 (retrieved 2026-04-27).
- Cluster Labs — Fencing wiki. https://wiki.clusterlabs.org/wiki/Fencing (retrieved 2026-04-27).
- VMware — vSphere HA isolation response (per confronto). https://docs.vmware.com/en/VMware-vSphere/8.0/com.vmware.vsphere.avail.doc/GUID-2BBA8FE5-3CDD-4F2F-B85B-FF7BFC52BD0F.html (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 10.1 — `ha-manager-regole-e-gruppi.md`: HA Manager dipende dal fencing.
- Modulo 10.2 — `live-migration-proxmox-interna.md`: live migration coordinata da CRM/LRM.
- Modulo 10.4 — `bilanciamento-carico-vm.md`: distribuzione carico post-fencing.
- Modulo 17.x — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-cluster-proxmox.md`: scenari di troubleshooting fencing.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Fencing** | Isolamento sicuro di un nodo malfunzionante prima del failover. |
| **STONITH** | Shoot The Other Node In The Head; fencing attivo via canale out-of-band. |
| **Self-fencing** | Nodo che si auto-elimina (tramite watchdog) quando perde quorum. |
| **Watchdog hardware** | Chip independent che reset il sistema se non riceve kick (es. Intel TCO). |
| **`softdog`** | Implementazione software del watchdog (kernel module). |
| **IPMI** | Intelligent Platform Management Interface; standard out-of-band management. |
| **iLO / iDRAC** | Implementazioni IPMI di HP / Dell. |
| **BMC** | Baseboard Management Controller; processore dedicato per IPMI. |
| **Out-of-band (OOB)** | Canale di comunicazione indipendente dalla rete OS/produzione. |
| **Fence loop** | Scenario dove nodi si fence reciprocamente in continuo. |
| **`fence-agents`** | Pacchetto Linux con agenti per fence diversi tipi di hardware. |
| **APD (vSphere)** | All-Paths-Down; perdita totale connettivita storage. |
| **PDL (vSphere)** | Permanent Device Lost; storage device dichiarato perso permanentemente. |
| **Datastore heartbeating** | Meccanismo vSphere HA per validare nodi via storage. |
