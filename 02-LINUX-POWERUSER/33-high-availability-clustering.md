---
Modulo del corso: "Linux per ingegneri di sistema"
Prerequisiti:
  - Amministrazione Linux intermedia (systemd, networking, storage)
  - Familiarità con la riga di comando, editor di testo e scripting Bash
  - Conoscenza base di TCP/IP, firewalling e storage (LVM, filesystem)
  - Esperienza con package manager (apt, dnf/yum)
  - Modulo 04 — systemd (gestione servizi, unit file)
  - Modulo 05 — Networking (interfacce, routing, bonding)
  - Modulo 06 — Storage (LVM, filesystem, RAID)
  - Modulo 11 — Sicurezza (firewall, hardening base)
Obiettivi:
  1. Progettare architetture High Availability eliminando Single Point of Failure con ridondanza a ogni livello
  2. Configurare cluster Pacemaker/Corosync con resource agents, vincoli, gruppi, cloni e risorse promotable
  3. Implementare fencing STONITH obbligatorio con IPMI, SBD e fence agents per hypervisor/cloud
  4. Gestire failover VIP con Keepalived/VRRP e load balancing avanzato con HAProxy
  5. Configurare storage replicato con DRBD (sincrono/asincrono) e integrarlo con Pacemaker
  6. Applicare pattern HA per database (Patroni, Group Replication), applicazioni stateless/stateful e ambienti cloud
  7. Monitorare la salute del cluster con Prometheus, crm_mon e alerting automatizzato
  8. Pianificare Disaster Recovery con analisi RPO/RTO, georedundanza e test di failover sistematici
Tempo stimato: 20-28 ore
Livello: proficient
Ultimo aggiornamento: 2026-05-23
Versioni di riferimento: Pacemaker 2.1+, Corosync 3.1+, DRBD 9.2+, HAProxy 2.9+, Keepalived 2.3+
---

# High Availability e Clustering Linux — Guida Completa

> **Modulo 33** · **Aggiornamento:** 2026-05-23

## Idee guida
1. **Pacemaker + Corosync standard cluster Linux.**
2. **Fencing/STONITH mandatory; without no HA.**
3. **Keepalived + VRRP per simple VIP failover.**
4. **DRBD + Pacemaker per shared storage HA.**

## Mappa Concettuale

```
                           ┌──────────────────────────────┐
                           │    HIGH AVAILABILITY         │
                           │    E CLUSTERING LINUX        │
                           └──────────────┬───────────────┘
                                          │
            ┌─────────────────────────────┼──────────────────────────────┐
            │                             │                              │
     ┌──────▼──────┐              ┌───────▼──────┐               ┌──────▼──────┐
     │  CLUSTER    │              │  NETWORKING  │               │  STORAGE    │
     │  MANAGEMENT │              │  HA          │               │  HA         │
     └──────┬──────┘              └───────┬──────┘               └──────┬──────┘
            │                             │                             │
    ┌───────┼───────┐            ┌────────┼────────┐           ┌───────┼───────┐
    │       │       │            │        │        │           │       │       │
    ▼       ▼       ▼            ▼        ▼        ▼           ▼       ▼       ▼
 Pace-   Coro-   Fencing     Keepa-   HAProxy   Network    DRBD   GlusterFS  Ceph
 maker   sync    STONITH     lived    LVS       Bonding    (rep.) (distrib.) (distrib.)
 (CRM)   (msg)   (SBD/IPMI) (VRRP)   (L4/L7)   LACP/BFD
    │       │       │            │        │        │           │       │       │
    ▼       ▼       ▼            ▼        ▼        ▼           ▼       ▼       ▼
 Resource Totem   Fence       VIP     Backend    Bonding    Sinc/  Replica   RBD
 Agents   Proto-  Agents      Failov. Health     Modes      Async  Disperse  CephFS
 OCF/LSB  col     IPMI/SBD    Track   Check      802.3ad    Dual-  Erasure   RADOS
 systemd  Quorum  libvirt     Script  SSL Term.  BFD        Prim.  Coding    GW
            │                             │                             │
    ┌───────┼───────┐            ┌────────┼────────┐           ┌───────┼───────┐
    │       │       │            │        │        │           │       │       │
    ▼       ▼       ▼            ▼        ▼        ▼           ▼       ▼       ▼
 Groups  Cloni  Promot-      Unicast  ACL/     Rate        GFS2   OCFS2   Shared
 Vincoli Risorse able        Peers    Routing  Limiting    (DLM)  (DLM)   SAN
 CIB/PE  pcs    Master/Sl.   Notify   WebSock. Drain
            │                             │                             │
            ▼                             ▼                             ▼
 Database HA              Application HA              Disaster Recovery
 Patroni/PG               Stateless/Stateful          RPO/RTO
 MySQL GR                 Session Affinity            Georedundanza
 etcd cluster             Graceful Degradation        Cloud HA
```


## Indice

- [Panoramica](#panoramica)
- [Concetti Fondamentali di High Availability](#concetti-fondamentali-di-high-availability)
- [Pacemaker e Corosync](#pacemaker-e-corosync)
- [Fencing e STONITH](#fencing-e-stonith)
- [Keepalived e VRRP](#keepalived-e-vrrp)
- [HAProxy — Load Balancing Avanzato](#haproxy--load-balancing-avanzato)
- [DRBD — Replicated Storage](#drbd--replicated-storage)
- [Storage Distribuito: GlusterFS e Ceph](#storage-distribuito-glusterfs-e-ceph)
- [Scenari Pratici HA](#scenari-pratici-ha)
- [Split-Brain: Prevenzione e Gestione](#split-brain-prevenzione-e-gestione)
- [Disaster Recovery vs High Availability](#disaster-recovery-vs-high-availability)
- [Monitoraggio della Salute del Cluster](#monitoraggio-della-salute-del-cluster)
- [Testing HA — Chaos Engineering e Failover Drills](#testing-ha--chaos-engineering-e-failover-drills)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Esercizi Pratici](#esercizi-pratici)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie](#letture-primarie)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)
- [Riferimenti](#riferimenti)

---

## Panoramica

L'High Availability (HA) è la capacità di un sistema di rimanere operativo e accessibile anche in presenza di guasti hardware o software. In ambienti di produzione, il downtime ha costi diretti (perdita di ricavi, SLA violati) e indiretti (reputazione, fiducia dei clienti). Un'architettura HA ben progettata elimina i single point of failure (SPOF) attraverso ridondanza, failover automatico e monitoraggio continuo.

Questo documento copre l'intero stack HA su Linux: dal cluster management con Pacemaker/Corosync, al load balancing con HAProxy, allo storage replicato con DRBD, fino allo storage distribuito con GlusterFS e Ceph. Ogni sezione include configurazioni reali, esempi di comandi e scenari pratici.

### Terminologia Fondamentale

| Termine | Significato |
|---------|-------------|
| **SPOF** | Single Point of Failure — componente il cui guasto causa il downtime dell'intero servizio |
| **Failover** | Trasferimento automatico del servizio da un nodo guasto a uno funzionante |
| **Failback** | Ritorno del servizio al nodo originale dopo il ripristino |
| **Quorum** | Numero minimo di nodi necessari per prendere decisioni nel cluster |
| **Fencing** | Isolamento forzato di un nodo malfunzionante per proteggere i dati |
| **STONITH** | Shoot The Other Node In The Head — meccanismo di fencing hardware |
| **Split-brain** | Condizione in cui due partizioni del cluster credono entrambe di essere attive |
| **VIP** | Virtual IP — indirizzo IP che si sposta tra nodi in caso di failover |
| **RTO** | Recovery Time Objective — tempo massimo accettabile per il ripristino |
| **RPO** | Recovery Point Objective — quantità massima di dati che si può perdere |

### Livelli di Disponibilità

```
Disponibilità    Downtime/anno    Uso tipico
─────────────    ──────────────   ──────────────────────────
99%              3.65 giorni      Sistemi interni non critici
99.9%            8.76 ore         Applicazioni business standard
99.99%           52.6 minuti      E-commerce, banche, SaaS
99.999%          5.26 minuti      Telecomunicazioni, emergenze
99.9999%         31.5 secondi     Trading ad alta frequenza
```

### Metriche di Affidabilità: MTBF e MTTR

La disponibilità non è un numero magico: si calcola dalle metriche operative effettive.

```
                    MTBF
Availability = ───────────────
                MTBF + MTTR

Dove:
  MTBF = Mean Time Between Failures  (tempo medio tra guasti)
  MTTR = Mean Time To Repair/Recover (tempo medio di ripristino)
```

**Esempio pratico:**
- Server con MTBF = 8760 ore (1 anno), MTTR = 1 ora:
  A = 8760 / (8760 + 1) = 99.989% → circa 52 minuti di downtime/anno
- Stesso server con MTTR = 8 ore (nessuna automazione):
  A = 8760 / (8760 + 8) = 99.909% → circa 8 ore di downtime/anno

La lezione fondamentale: **ridurre l'MTTR ha un impatto maggiore della riduzione dell'MTBF**.
L'HA automatizzata abbatte l'MTTR da ore a secondi.

| Strategia | MTTR tipico | Note |
|-----------|-------------|------|
| Failover manuale | 30-120 min | Dipende dal personale on-call |
| Pacemaker/Corosync | 5-30 sec | Dipende da `token` timeout e monitor interval |
| Keepalived VRRP | 1-3 sec | Failover quasi istantaneo della VIP |
| DNS failover | 30 sec - 10 min | Dipende dal TTL del record DNS |

### Analisi dei Single Point of Failure (SPOF)

L'analisi SPOF è il primo passo nella progettazione HA. Si procede per componenti:

```
Componente            SPOF?     Mitigazione
──────────────────    ──────    ──────────────────────────────────────
Server fisico         SÌ        Cluster multi-nodo
Alimentazione         SÌ        Doppio alimentatore + UPS + PDU ridondante
Rete                  SÌ        NIC bonding + switch ridondanti
Storage locale        SÌ        RAID + DRBD replica su nodo remoto
Switch di rete        SÌ        Switch impilati / ridondanti
Load balancer         SÌ        HAProxy + Keepalived (coppia A/P)
DNS                   SÌ        DNS multipli + Anycast
Data center           SÌ        Geo-replicazione / stretch cluster
Applicazione          SÌ        Più istanze + health check + autoscaling
Database              SÌ        Replica sincrona + failover automatico
Operatore umano       SÌ        Runbook automatizzati + alerting
```

**Albero dei guasti (Fault Tree) — esempio web tier:**

```
                     Servizio non disponibile
                              │
                     ┌────────┴────────┐
                     │    OR           │
              ┌──────┴──────┐   ┌─────┴──────┐
              │ Load Balancer│   │ Tutti i    │
              │ non funziona│   │ backend    │
              │             │   │ non funz.  │
              └──────┬──────┘   └─────┬──────┘
              ┌──────┴──────┐         │
              │    AND      │    ┌────┴────┐
         ┌────┴────┐  ┌────┴──┐│   AND    │
         │ LB-A    │  │ LB-B  │├────┬─────┤
         │ guasto  │  │ guasto││web1│web2 │web3
         └─────────┘  └───────┘│gua.│gua. │gua.
                               └────┴─────┘
```

Il servizio cade solo se entrambi i LB sono guasti **oppure** tutti e tre i backend
sono guasti contemporaneamente. La probabilità combinata è il prodotto delle
probabilità individuali: P(down) = P(LB-A) × P(LB-B) + P(web1) × P(web2) × P(web3).

---

## Concetti Fondamentali di High Availability

### Architetture HA

#### Active/Passive (Failover)

Un nodo attivo gestisce il servizio, uno o più nodi passivi attendono. In caso di guasto, un nodo passivo prende il controllo.

```
                 ┌─────────────┐
  Clients ──────>│  VIP         │
                 │ 10.0.0.100   │
                 └──────┬───────┘
                        │
              ┌─────────┴─────────┐
              │                   │
        ┌─────┴─────┐      ┌─────┴─────┐
        │  Node A    │      │  Node B    │
        │  ACTIVE    │      │  STANDBY   │
        │ 10.0.0.1   │      │ 10.0.0.2   │
        └────────────┘      └────────────┘
```

**Vantaggi**: Semplice, prevedibile, nessun conflitto di risorse.
**Svantaggi**: Il nodo standby non lavora (spreco di risorse), failover non istantaneo.

#### Active/Active (Load Sharing)

Tutti i nodi gestiscono traffico simultaneamente. Se uno cade, il traffico viene redistribuito.

```
                 ┌─────────────┐
  Clients ──────>│ Load Balancer│
                 │ 10.0.0.100  │
                 └──────┬───────┘
                        │
           ┌────────────┼────────────┐
           │            │            │
     ┌─────┴─────┐ ┌───┴───┐ ┌─────┴─────┐
     │  Node A    │ │ Node B│ │  Node C    │
     │  ACTIVE    │ │ ACTIVE│ │  ACTIVE    │
     └────────────┘ └───────┘ └────────────┘
```

**Vantaggi**: Utilizzo completo delle risorse, scalabilità orizzontale.
**Svantaggi**: Complessità nella gestione dello stato condiviso, necessità di session affinity o storage condiviso.

#### N+1 Redundancy

N nodi gestiscono il carico, 1 nodo aggiuntivo è pronto per il failover. È un compromesso tra active/active puro e active/passive.

### Requisiti Infrastrutturali per HA

Per un cluster HA robusto servono almeno:

1. **Rete dedicata per il cluster** (heartbeat): rete separata dal traffico applicativo per la comunicazione inter-nodo
2. **Storage condiviso o replicato**: SAN, NFS, DRBD o storage distribuito
3. **Fencing hardware o software**: IPMI, iLO, DRAC, o fencing via hypervisor
4. **DNS con TTL basso**: per aggiornamenti rapidi in caso di failover
5. **Numero dispari di nodi** (o quorum device): per evitare split-brain

### Teorema CAP e Cluster HA

Il teorema CAP (Brewer, 2000) afferma che un sistema distribuito può garantire al massimo due delle tre proprietà:

| Proprietà | Significato | Impatto su HA |
|-----------|-------------|---------------|
| **Consistency** | Tutti i nodi vedono gli stessi dati nello stesso momento | Replica sincrona (DRBD protocol C), write quorum |
| **Availability** | Ogni richiesta riceve una risposta (successo o errore) | Nessun downtime per il client |
| **Partition tolerance** | Il sistema continua a funzionare nonostante partizionamenti di rete | Requisito implicito nei cluster |

In un cluster Pacemaker/Corosync, la partizione di rete è inevitabile, quindi la scelta è tra **CP** e **AP**:

- **CP (Consistency + Partition tolerance)**: scelta tipica per database e storage condiviso. Il cluster con quorum ferma i servizi sulla partizione minoritaria (no-quorum-policy=stop). I dati restano coerenti, ma la partizione minoritaria è indisponibile.
- **AP (Availability + Partition tolerance)**: possibile per servizi stateless. Entrambe le partizioni continuano a servire richieste, ma con rischio di conflitti se c'è stato condiviso.

Un cluster Pacemaker ben configurato è **CP** per default: il quorum garantisce che solo una partizione operi, il fencing previene la corruzione.

### Algoritmi di Consenso — Panoramica

Il consenso distribuito è il problema fondamentale: come fanno N nodi a concordare su una decisione (chi è il leader, quale valore è corretto)?

```
Algoritmo        Usato da                    Caratteristiche
──────────────   ─────────────────────────   ───────────────────────────────
Totem (UDPU)     Corosync                    Token ring virtuale, ordinamento
                                             totale dei messaggi, membership
Raft             etcd, Consul, CockroachDB   Leader-based, log replication,
                                             term elections, facile da capire
Paxos            Chubby (Google), ZooKeeper   Proposer-acceptor-learner, più
                (variante ZAB)               complesso, provato formalmente
VRRP             Keepalived                  Election basata su priorità,
                                             advertisement periodici
```

**Totem** (usato da Corosync) opera con un token ring virtuale: un token circola tra i nodi, e solo chi ha il token può trasmettere. Garantisce ordinamento totale dei messaggi e rilevamento rapido dei guasti (se un nodo non passa il token entro il timeout, è considerato morto).

### Tassonomia dei Guasti

```
Tipo di guasto          Esempio                          Rilevamento
──────────────────────  ─────────────────────────────    ───────────────────────
Crash failure           Kernel panic, OOM kill           Heartbeat timeout
Omission failure        Pacchetti persi, NIC guasta      Missed token/advertise
Timing failure          Nodo troppo lento (carico CPU)   Monitor timeout
Byzantine failure       Dati corrotti, firmware buggato  Difficile, serve quorum
Partition failure       Switch guasto, cavo scollegato   Split membership
```

Un cluster Pacemaker gestisce crash, omission e partition failures tramite heartbeat + fencing. I Byzantine failures (nodo che mente) sono fuori scope per la maggior parte dei cluster HA tradizionali.

---

## Pacemaker e Corosync

Pacemaker è il cluster resource manager più utilizzato su Linux. Corosync fornisce il layer di comunicazione e membership del cluster. Insieme formano lo stack HA standard per distribuzioni Enterprise (RHEL, SUSE, Ubuntu).

### Architettura dello Stack

```
┌──────────────────────────────────────┐
│           Applicazioni               │
├──────────────────────────────────────┤
│  Resource Agents (OCF, LSB, systemd) │
├──────────────────────────────────────┤
│           Pacemaker (CRM)            │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ CIB (XML)│  │ PE (Policy Engine│  │
│  │ Database │  │   + Scheduler)   │  │
│  └──────────┘  └──────────────────┘  │
├──────────────────────────────────────┤
│           Corosync (Messaging)       │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ Totem    │  │ Quorum           │  │
│  │ Protocol │  │ Subsystem        │  │
│  └──────────┘  └──────────────────┘  │
├──────────────────────────────────────┤
│           Network (UDP/UDPU)         │
└──────────────────────────────────────┘
```

- **CIB** (Cluster Information Base): database XML che descrive la configurazione e lo stato del cluster
- **PE** (Policy Engine): decide dove eseguire le risorse basandosi su vincoli e regole
- **Totem**: protocollo di comunicazione reliable multicast/unicast
- **Quorum**: sottosistema che determina se il cluster può operare

### Installazione

#### RHEL/CentOS/AlmaLinux/Rocky

```bash
# Installazione pacchetti
sudo dnf install -y pacemaker corosync pcs fence-agents-all

# Abilitare e avviare il servizio pcsd (daemon di gestione)
sudo systemctl enable --now pcsd

# Impostare la password per l'utente hacluster (su TUTTI i nodi)
sudo passwd hacluster

# Aprire le porte nel firewall
sudo firewall-cmd --permanent --add-service=high-availability
sudo firewall-cmd --reload
```

#### Debian/Ubuntu

```bash
# Installazione pacchetti
sudo apt install -y pacemaker corosync pcs fence-agents

# Abilitare pcsd
sudo systemctl enable --now pcsd

# Impostare password hacluster (su TUTTI i nodi)
sudo passwd hacluster
```

### Configurazione del Cluster

#### Setup Iniziale con pcs

```bash
# Autenticare i nodi (eseguire da UN solo nodo)
sudo pcs host auth node1.example.com node2.example.com node3.example.com \
  -u hacluster -p 'SecurePassword123!'

# Creare il cluster
sudo pcs cluster setup ha-cluster \
  node1.example.com node2.example.com node3.example.com

# Avviare il cluster
sudo pcs cluster start --all

# Abilitare l'avvio automatico
sudo pcs cluster enable --all

# Verificare lo stato
sudo pcs cluster status
```

Output tipico:

```
Cluster name: ha-cluster
Cluster Summary:
  * Stack: corosync
  * Current DC: node1.example.com (version 2.1.5) - partition with quorum
  * Last updated: Sat Apr 12 10:30:00 2026
  * 3 nodes configured
  * 0 resource instances configured

Node List:
  * Online: [ node1.example.com node2.example.com node3.example.com ]

Full List of Resources:
  * No resources
```

#### Configurazione di Corosync

Il file di configurazione principale è `/etc/corosync/corosync.conf`. Normalmente viene generato da `pcs cluster setup`, ma è utile comprenderne la struttura:

```conf
totem {
    version: 2
    cluster_name: ha-cluster
    transport: knet

    # Crittografia della comunicazione cluster
    crypto_cipher: aes256
    crypto_hash: sha256

    # Timeout e intervalli (in millisecondi)
    token: 5000          # Tempo prima di dichiarare un nodo morto
    token_retransmits_before_loss_const: 10
    join: 60              # Tempo per attendere join messaggi
    consensus: 7500       # Timeout per raggiungere consenso
    max_messages: 20      # Messaggi max per token rotation
}

nodelist {
    node {
        ring0_addr: 10.0.0.1
        name: node1.example.com
        nodeid: 1
    }
    node {
        ring0_addr: 10.0.0.2
        name: node2.example.com
        nodeid: 2
    }
    node {
        ring0_addr: 10.0.0.3
        name: node3.example.com
        nodeid: 3
    }
}

quorum {
    provider: corosync_votequorum
    # Per cluster a 2 nodi, abilitare:
    # two_node: 1
    # wait_for_all: 1
}

logging {
    to_logfile: yes
    logfile: /var/log/corosync/corosync.log
    to_syslog: yes
    timestamp: on
}
```

### Corosync — Approfondimento Internals

#### Protocollo Totem

Corosync utilizza il protocollo Totem Single Ring Ordering and Membership per la comunicazione inter-nodo. Il protocollo garantisce:

1. **Ordinamento totale**: tutti i nodi ricevono i messaggi nello stesso ordine
2. **Reliable delivery**: ogni messaggio viene consegnato a tutti i nodi o a nessuno
3. **Membership virtuale**: il ring si riconfigura automaticamente quando un nodo entra/esce

```
Flusso del token nel ring virtuale:

  Node1 ──token──► Node2 ──token──► Node3
    ▲                                  │
    └──────────────token───────────────┘

- Solo chi possiede il token può trasmettere
- Il token circola con un timer (token timeout)
- Se il token non arriva entro il timeout → il nodo è considerato morto
- Il ring si riconfigura escludendo il nodo guasto
```

Parametri critici del Totem:

| Parametro | Default | Significato |
|-----------|---------|-------------|
| `token` | 1000 ms | Tempo prima di dichiarare un nodo morto (se non riceve token) |
| `consensus` | 1200 ms | Timeout per raggiungere consenso sulla membership |
| `join` | 50 ms | Tempo per attendere join messaggi all'avvio |
| `token_retransmits_before_loss_const` | 4 | Numero di ritrasmissioni prima di dichiarare perdita |
| `max_messages` | 17 | Messaggi massimi trasmessi per possesso del token |

**Regola pratica**: `consensus` > `token` + `2 * token_retransmits_before_loss_const * token / (numero_nodi)`. Per ambienti con alta latenza (WAN), aumentare `token` a 5000-10000 ms.

#### Trasporti: knet vs UDPU vs Multicast

```
Trasporto    Porte           Crittografia    Link ridondanti    Note
───────────  ──────────────  ──────────────  ─────────────────  ─────────────────────
knet         porta base      Sì (nativo)     Sì (multipli)      Default da Corosync 3
             (5405+)                                            Sostituisce UDPU/mcast
UDPU         5405/UDP        Solo authkey    No (un link)       Unicast legacy
Multicast    5405/UDP        Solo authkey    Sì (rrp_mode)      Richiede IGMP snooping
```

**knet** (Kronosnet) è il trasporto moderno, introdotto con Corosync 3. Supporta:
- **Link ridondanti**: fino a 8 link paralleli per nodo
- **Crittografia nativa**: AES-256 + SHA-256 senza richiedere IPsec
- **Compressione**: opzionale per ridurre il traffico
- **Path failover**: se un link cade, il traffico passa automaticamente su un altro

Configurazione knet con link ridondanti:

```conf
totem {
    version: 2
    cluster_name: ha-cluster
    transport: knet

    crypto_cipher: aes256
    crypto_hash: sha256

    # Timeout adattati alla rete
    token: 3000
    consensus: 4500
}

nodelist {
    node {
        ring0_addr: 10.0.0.1    # Link primario (rete dedicata HA)
        ring1_addr: 10.0.1.1    # Link secondario (rete di backup)
        name: node1.example.com
        nodeid: 1
    }
    node {
        ring0_addr: 10.0.0.2
        ring1_addr: 10.0.1.2
        name: node2.example.com
        nodeid: 2
    }
    node {
        ring0_addr: 10.0.0.3
        ring1_addr: 10.0.1.3
        name: node3.example.com
        nodeid: 3
    }
}
```

#### Crittografia e Autenticazione

```bash
# Generare la chiave di autenticazione Corosync
sudo corosync-keygen

# Il file /etc/corosync/authkey viene generato (256 byte casuali)
# Copiare su tutti i nodi con permessi stretti
sudo scp /etc/corosync/authkey node2:/etc/corosync/
sudo scp /etc/corosync/authkey node3:/etc/corosync/
sudo chmod 400 /etc/corosync/authkey
sudo chown root:root /etc/corosync/authkey

# Verificare lo stato dei link
sudo corosync-cfgtool -s
# Output:
# Local node ID 1, transport knet
# LINK ID 0 udp
#   addr  = 10.0.0.1
#   status:
#     nodeid: 2    connected
#     nodeid: 3    connected
# LINK ID 1 udp
#   addr  = 10.0.1.1
#   status:
#     nodeid: 2    connected
#     nodeid: 3    connected
```

### Resource Agents

I Resource Agent (RA) sono script che Pacemaker usa per gestire le risorse. Esistono diversi standard:

| Standard | Posizione | Descrizione |
|----------|-----------|-------------|
| **OCF** | `/usr/lib/ocf/resource.d/` | Standard più ricco, supporta monitor, promote, demote |
| **LSB** | `/etc/init.d/` | Script init legacy |
| **systemd** | unità systemd | Integrazione nativa con systemd |
| **service** | wrapper | Cerca prima systemd, poi LSB |
| **stonith** | fence agents | Agenti per il fencing |

#### Elencare Resource Agents disponibili

```bash
# Tutti i tipi
pcs resource agents

# Solo OCF
pcs resource agents ocf

# Dettaglio di un agente specifico
pcs resource describe ocf:heartbeat:IPaddr2
```

#### Creare una Risorsa Virtual IP

```bash
# Creare una VIP
sudo pcs resource create cluster-vip ocf:heartbeat:IPaddr2 \
  ip=10.0.0.100 \
  cidr_netmask=24 \
  nic=eth0 \
  op monitor interval=10s timeout=20s \
  op start timeout=20s \
  op stop timeout=20s

# Verificare
sudo pcs resource status
```

#### Creare una Risorsa Apache/Nginx

```bash
# Risorsa Apache
sudo pcs resource create webserver ocf:heartbeat:apache \
  configfile=/etc/httpd/conf/httpd.conf \
  statusurl="http://127.0.0.1/server-status" \
  op monitor interval=30s timeout=30s \
  op start timeout=60s \
  op stop timeout=60s

# Vincolo di colocation: webserver sempre sullo stesso nodo della VIP
sudo pcs constraint colocation add webserver with cluster-vip INFINITY

# Vincolo di ordine: prima la VIP, poi il webserver
sudo pcs constraint order cluster-vip then webserver
```

#### Resource Group

Raggruppare risorse che devono stare insieme e avviarsi in ordine:

```bash
# Creare un gruppo
sudo pcs resource group add web-group cluster-vip webserver

# Le risorse nel gruppo:
# 1. Stanno sempre sullo stesso nodo
# 2. Si avviano nell'ordine elencato
# 3. Si fermano nell'ordine inverso
```

#### Cloni e Risorse Promotable

Le risorse **clone** girano su più nodi contemporaneamente (es. un servizio di monitoraggio attivo ovunque). Le risorse **promotable** (ex master/slave) girano su più nodi ma con ruoli differenziati.

```bash
# Creare un clone (risorsa attiva su tutti i nodi)
sudo pcs resource create ping-check ocf:pacemaker:ping \
  host_list="gateway.example.com" \
  multiplier=1000 \
  op monitor interval=30s

sudo pcs resource clone ping-check \
  clone-max=3 \
  clone-node-max=1 \
  globally-unique=false

# Creare una risorsa promotable (master/slave)
sudo pcs resource create drbd-data ocf:linbit:drbd \
  drbd_resource=data \
  op monitor interval=30s role=Master \
  op monitor interval=60s role=Slave

sudo pcs resource promotable drbd-data \
  promoted-max=1 \
  promoted-node-max=1 \
  clone-max=2 \
  clone-node-max=1 \
  notify=true

# Differenze chiave:
# clone          → tutte le istanze identiche (simmetriche)
# promotable     → un'istanza Master, le altre Slave
# promoted-max   → quanti nodi possono essere Master (tipicamente 1)
# notify=true    → i RA ricevono notifiche pre/post promote/demote
```

#### Dettaglio OCF Resource Agent

Gli OCF Resource Agent supportano le seguenti azioni:

| Azione | Descrizione | Return code successo |
|--------|-------------|---------------------|
| `start` | Avvia la risorsa | 0 |
| `stop` | Ferma la risorsa | 0 |
| `monitor` | Controlla lo stato | 0 (attivo), 7 (non attivo) |
| `promote` | Promuovi a Master | 0 |
| `demote` | Retrocedi a Slave | 0 |
| `migrate_to` | Migra la risorsa (live migration) | 0 |
| `meta-data` | Ritorna metadati XML | 0 |
| `validate-all` | Valida la configurazione | 0 |

```bash
# Ispezionare i metadati di un resource agent
pcs resource describe ocf:heartbeat:IPaddr2

# Testare un resource agent manualmente
sudo OCF_ROOT=/usr/lib/ocf \
  OCF_RESKEY_ip=10.0.0.100 \
  OCF_RESKEY_cidr_netmask=24 \
  /usr/lib/ocf/resource.d/heartbeat/IPaddr2 monitor
echo $?   # 0 = attivo, 7 = non attivo

# Resource agents più utilizzati:
# ocf:heartbeat:IPaddr2       → Virtual IP
# ocf:heartbeat:Filesystem    → Mount di filesystem
# ocf:heartbeat:apache        → Apache HTTPD
# ocf:heartbeat:nginx         → Nginx
# ocf:heartbeat:pgsql         → PostgreSQL
# ocf:heartbeat:mysql         → MySQL/MariaDB
# ocf:linbit:drbd             → DRBD
# ocf:pacemaker:ping          → Test raggiungibilità rete
# ocf:pacemaker:remote        → Nodo remoto Pacemaker
```

### Proprietà del Cluster

```bash
# Disabilitare STONITH (solo per test, MAI in produzione)
sudo pcs property set stonith-enabled=false

# Politica di quorum (ignorare quorum per cluster a 2 nodi in test)
sudo pcs property set no-quorum-policy=ignore

# Stickiness: preferire il nodo corrente (evita failback non necessari)
sudo pcs resource defaults update resource-stickiness=100

# Numero di migrazioni prima di considerare la risorsa fallita
sudo pcs resource defaults update migration-threshold=3

# Timeout per il fallimento (reset contatore dopo 300s)
sudo pcs resource defaults update failure-timeout=300s
```

### Vincoli (Constraints)

#### Location Constraints

Controllano su quali nodi una risorsa può girare:

```bash
# Preferire node1 per la risorsa webserver (score 100)
sudo pcs constraint location webserver prefers node1.example.com=100

# Evitare node3 per la risorsa webserver
sudo pcs constraint location webserver avoids node3.example.com=INFINITY

# Regola basata su attributo (solo nodi con ruolo "web")
sudo pcs constraint location webserver rule score=INFINITY \
  '#uname' eq node1.example.com or '#uname' eq node2.example.com
```

#### Colocation Constraints

```bash
# La risorsa db-vip deve stare sullo stesso nodo di db-server
sudo pcs constraint colocation add db-vip with db-server INFINITY

# Il webserver NON deve stare sullo stesso nodo del db-server
sudo pcs constraint colocation add webserver with db-server -INFINITY
```

#### Order Constraints

```bash
# Avviare filesystem prima del database
sudo pcs constraint order filesystem then database

# Ordine opzionale (soft)
sudo pcs constraint order filesystem then database kind=Optional
```

### Operazioni su Risorse

```bash
# Stato completo del cluster
sudo pcs status

# Muovere una risorsa su un nodo specifico
sudo pcs resource move webserver node2.example.com

# Rimuovere il vincolo temporaneo creato da move
sudo pcs resource clear webserver

# Mettere un nodo in standby (le risorse migrano)
sudo pcs node standby node1.example.com

# Riportare il nodo online
sudo pcs node unstandby node1.example.com

# Pulire errori su una risorsa
sudo pcs resource cleanup webserver

# Disabilitare una risorsa (senza rimuoverla)
sudo pcs resource disable webserver

# Riabilitare
sudo pcs resource enable webserver
```

---

## Fencing e STONITH

Il fencing è **obbligatorio** in un cluster di produzione. Senza fencing, un nodo che sembra morto ma in realtà è solo lento potrebbe continuare a scrivere su storage condiviso, causando corruzione dei dati.

### Perché il Fencing è Essenziale

```
Scenario SENZA fencing:
1. Node A gestisce il database, scrive su disco condiviso
2. Node A ha un problema di rete (sembra morto al cluster)
3. Il cluster avvia il database su Node B
4. Node A si riprende, continua a scrivere
5. DUE nodi scrivono sullo stesso disco → CORRUZIONE DATI

Scenario CON fencing:
1. Node A gestisce il database
2. Node A ha un problema di rete
3. Il cluster PRIMA spegne fisicamente Node A (STONITH)
4. POI avvia il database su Node B
5. Solo un nodo scrive → dati sicuri
```

### Tipi di Fencing

| Tipo | Meccanismo | Affidabilità |
|------|------------|--------------|
| **Power fencing** | IPMI, iLO, DRAC, PDU | Molto alta |
| **Storage fencing** | SAN zoning, SCSI reservation | Alta |
| **Hypervisor fencing** | vCenter, libvirt, AWS | Alta |
| **SBD** | Storage-Based Death | Alta (per cluster senza accesso IPMI) |

### Configurazione IPMI Fencing

```bash
# Verificare agenti disponibili
pcs stonith list

# Creare un fence agent IPMI per ogni nodo
sudo pcs stonith create fence-node1 fence_ipmilan \
  ipaddr=10.0.1.1 \
  login=admin \
  passwd='FencePass123!' \
  lanplus=1 \
  power_wait=4 \
  pcmk_host_list=node1.example.com \
  pcmk_host_check=static-list \
  op monitor interval=60s

sudo pcs stonith create fence-node2 fence_ipmilan \
  ipaddr=10.0.1.2 \
  login=admin \
  passwd='FencePass123!' \
  lanplus=1 \
  power_wait=4 \
  pcmk_host_list=node2.example.com \
  pcmk_host_check=static-list \
  op monitor interval=60s

# Vincolo: non eseguire il fence agent sullo stesso nodo che deve fenceare
sudo pcs constraint location fence-node1 avoids node1.example.com=INFINITY
sudo pcs constraint location fence-node2 avoids node2.example.com=INFINITY

# Abilitare STONITH
sudo pcs property set stonith-enabled=true

# Testare (ATTENZIONE: spegne davvero il nodo!)
sudo pcs stonith fence node2.example.com
```

### SBD (Storage-Based Death)

Per ambienti senza IPMI (es. VM senza accesso hypervisor):

```bash
# Installare SBD
sudo dnf install -y sbd

# Creare il dispositivo SBD su un disco condiviso
sudo sbd -d /dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_VBxxxxxxxx -1 60 -4 120 create

# Configurare SBD in /etc/sysconfig/sbd
SBD_DEVICE="/dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_VBxxxxxxxx"
SBD_DELAY_START=no
SBD_PACEMAKER=yes
SBD_STARTMODE=always
SBD_WATCHDOG_DEV=/dev/watchdog
SBD_WATCHDOG_TIMEOUT=5

# Caricare il modulo watchdog
sudo modprobe softdog
echo "softdog" | sudo tee /etc/modules-load.d/softdog.conf

# Abilitare SBD
sudo systemctl enable sbd

# Configurare Pacemaker per usare SBD
sudo pcs stonith create sbd-fencing fence_sbd \
  devices=/dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_VBxxxxxxxx
```

### Catalogo degli Agenti di Fencing

| Agente | Target | Protocollo | Note |
|--------|--------|-----------|------|
| `fence_ipmilan` | Server fisici con BMC | IPMI over LAN | Il più comune per bare metal |
| `fence_ilo` | HP ProLiant | iLO REST API | Usa `--ssl-secure` in produzione |
| `fence_idrac` | Dell PowerEdge | iDRAC RACADM/Redfish | Supporta Redfish da iDRAC 8+ |
| `fence_redfish` | Qualsiasi server con Redfish | DMTF Redfish API | Standard moderno, vendor-neutral |
| `fence_virsh` | VM su KVM/libvirt | SSH + virsh | Per lab o ambienti KVM |
| `fence_vmware_soap` | VM su VMware vSphere | SOAP API vCenter | Richiede credenziali vCenter |
| `fence_vmware_rest` | VM su VMware vSphere | REST API vCenter 6.5+ | Preferito per vSphere moderno |
| `fence_aws` | Istanze EC2 | AWS API | Richiede IAM role con ec2:StopInstances |
| `fence_azure_arm` | VM Azure | Azure Resource Manager API | Richiede service principal |
| `fence_gce` | VM Google Cloud | GCE API | Richiede service account |
| `fence_apc` | PDU APC | SNMP/SSH | Spegne la presa elettrica del server |
| `fence_apc_snmp` | PDU APC via SNMP | SNMP v1/v2c/v3 | Alternativa SNMP a fence_apc |
| `fence_sbd` | Cluster senza IPMI | Watchdog + disco condiviso | Richiede hardware watchdog |
| `fence_scsi` | Storage condiviso | SCSI-3 persistent reservations | Fencing a livello storage |
| `fence_kdump` | Nodi in kernel panic | kdump detection | Ritarda il fencing durante kdump |

### Fencing Topology

Quando un singolo metodo di fencing non è sufficiente, si configurano
**topologie di fencing** con più dispositivi per nodo:

```bash
# Topologia sequenziale: prova IPMI, se fallisce prova PDU
sudo pcs stonith level add 1 node1.example.com fence-node1-ipmi
sudo pcs stonith level add 2 node1.example.com fence-node1-pdu

# Topologia simultanea: entrambi i dispositivi devono avere successo
# (utile per dual-power supply: spegni ENTRAMBI gli alimentatori)
sudo pcs stonith level add 1 node1.example.com fence-node1-pdu-a,fence-node1-pdu-b

# Visualizzare le topologie configurate
sudo pcs stonith level
```

### Fencing Delay — Cluster a 2 Nodi

In un cluster a 2 nodi, se entrambi tentano di fencearsi simultaneamente,
il risultato è un **double-fencing** (entrambi si spengono). La soluzione:

```bash
# Aggiungere un ritardo di fencing sul nodo 2
# Il nodo 1 fencerà il nodo 2 per primo (senza ritardo)
sudo pcs stonith update fence-node1 pcmk_delay_base=0s
sudo pcs stonith update fence-node2 pcmk_delay_base=5s

# Ritardo randomizzato (utile in cluster più grandi)
sudo pcs stonith update fence-node2 pcmk_delay_max=10s
```

### Self-Fencing

Un nodo può auto-fencearsi quando rileva di non poter comunicare con il cluster:

1. **SBD watchdog**: se il nodo non riesce a scrivere il "slot alive" sul
   dispositivo SBD, il watchdog hardware resetta il nodo
2. **`suicide` no-quorum-policy**: il nodo senza quorum si auto-spegne
3. Il self-fencing è un "ultimo resort": il fencing remoto (IPMI/PDU) è sempre
   preferibile perché il nodo guasto potrebbe essere in kernel panic

### Fencing/STONITH — Strategie Avanzate

#### Fencing Concorrente vs Sequenziale

Quando si configurano topologie di fencing con più dispositivi, Pacemaker supporta due modalità operative distinte:

**Sequenziale** (default): i dispositivi vengono provati uno dopo l'altro. Se il primo livello fallisce, si passa al successivo. Utile quando si hanno metodi di fencing di backup (es. IPMI come primario, PDU come fallback).

**Concorrente**: più dispositivi allo stesso livello devono tutti avere successo per completare il fencing. Indispensabile per server con alimentazione ridondante (dual-PSU), dove spegnere un solo alimentatore non basta.

```bash
# Configurare il numero massimo di operazioni di fencing parallele
sudo pcs property set concurrent-fencing=true

# Limitare il numero di azioni di fencing simultanee per dispositivo
# pcmk_action_limit controlla quante operazioni un singolo fence agent
# può eseguire in parallelo (default: 1)
sudo pcs stonith update fence-node1-ipmi pcmk_action_limit=2

# Timeout per il completamento del fencing
# Se il fencing non si completa entro stonith-timeout,
# il cluster non può avviare risorse sul nodo sopravvissuto
sudo pcs property set stonith-timeout=60s
```

#### pcmk_host_map — Mappatura Nomi a Target

In ambienti dove il nome del nodo nel cluster non corrisponde al nome che il fence agent utilizza per identificare il target (es. nome VM diverso dall'hostname):

```bash
# Mappatura hostname → nome VM nell'hypervisor
sudo pcs stonith create fence-kvm fence_virsh \
  ip=hypervisor.local \
  login=root \
  identity_file=/root/.ssh/fence_key \
  pcmk_host_map="node1.cluster.local:vm-node1;node2.cluster.local:vm-node2" \
  pcmk_host_check=static-list \
  pcmk_host_list="node1.cluster.local,node2.cluster.local"
```

#### Fencing e kdump — Coordinamento

Quando un nodo va in kernel panic e kdump è attivo, il fencing immediato può interrompere il dump della memoria, perdendo informazioni diagnostiche preziose. Il fence agent `fence_kdump` ritarda il fencing per dare tempo al dump:

```bash
# Configurare fence_kdump come primo livello (ritarda il fencing)
sudo pcs stonith create fence-kdump-node1 fence_kdump \
  pcmk_host_list=node1.example.com \
  pcmk_reboot_timeout=120

# IPMI come secondo livello (se kdump non completa in tempo)
sudo pcs stonith level add 1 node1.example.com fence-kdump-node1
sudo pcs stonith level add 2 node1.example.com fence-node1-ipmi

# Sul nodo monitorato, configurare kdump per notificare il cluster:
# In /etc/kdump.conf aggiungere:
#   fence_kdump_args "-p 7410 -f auto"
#   fence_kdump_nodes node2.example.com node3.example.com
```

### Quorum

Il quorum impedisce lo split-brain garantendo che solo la partizione con la maggioranza dei voti possa operare.

```bash
# Verificare lo stato del quorum
sudo corosync-quorumtool

# Output tipico:
# Quorum information
# ------------------
# Date:             Sat Apr 12 10:45:00 2026
# Quorum provider:  corosync_votequorum
# Nodes:            3
# Node ID:          1
# Ring ID:          1.25
# Quorate:          Yes
#
# Votequorum information
# ----------------------
# Expected votes:   3
# Highest expected:  3
# Total votes:      3
# Quorum:           2
# Flags:            Quorate

# Politiche di no-quorum:
# stop     → ferma tutte le risorse (default, consigliato)
# freeze   → non ferma le risorse ma non ne avvia di nuove
# ignore   → ignora la perdita di quorum (PERICOLOSO)
# suicide  → il nodo si spegne da solo

sudo pcs property set no-quorum-policy=stop
```

#### Quorum Device (per cluster a 2 nodi)

Un cluster a 2 nodi non può avere quorum se un nodo cade (1 su 2 non è maggioranza). La soluzione è un quorum device esterno:

```bash
# Sul server qdevice (terza macchina leggera)
sudo dnf install -y corosync-qnetd
sudo pcs qdevice setup model net --enable --start

# Sui nodi del cluster
sudo dnf install -y corosync-qdevice
sudo pcs quorum device add model net \
  host=qdevice.example.com \
  algorithm=ffsplit

# Verificare
sudo pcs quorum device status
```

---

## Keepalived e VRRP

Keepalived è un'alternativa più leggera a Pacemaker per scenari di failover semplici (VIP + health check). Implementa il protocollo VRRP (Virtual Router Redundancy Protocol, RFC 5798).

### Installazione

```bash
# RHEL/CentOS
sudo dnf install -y keepalived

# Debian/Ubuntu
sudo apt install -y keepalived

# Abilitare il forwarding IP (necessario per VRRP)
echo "net.ipv4.ip_nonlocal_bind = 1" | sudo tee /etc/sysctl.d/99-keepalived.conf
sudo sysctl -p /etc/sysctl.d/99-keepalived.conf
```

### Configurazione VRRP — Nodo Master

`/etc/keepalived/keepalived.conf` sul nodo MASTER:

```conf
global_defs {
    router_id LVS_MASTER
    vrrp_skip_check_adv_addr
    vrrp_garp_interval 0
    vrrp_gna_interval 0
    enable_script_security
    script_user root
}

# Script di health check
vrrp_script chk_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 2          # Controlla ogni 2 secondi
    weight -20          # Riduce la priorità di 20 se il check fallisce
    fall 3              # 3 check falliti prima di dichiarare down
    rise 2              # 2 check ok prima di dichiarare up
}

vrrp_script chk_http {
    script "/usr/bin/curl -sf http://127.0.0.1/ -o /dev/null"
    interval 5
    weight -30
    fall 3
    rise 2
}

vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51        # Deve essere uguale su tutti i nodi
    priority 100                # Il master ha la priorità più alta
    advert_int 1                # Intervallo advertisement in secondi

    # Autenticazione (semplice ma utile)
    authentication {
        auth_type PASS
        auth_pass SecretVRRP!
    }

    # IP virtuali
    virtual_ipaddress {
        10.0.0.100/24 dev eth0 label eth0:vip
    }

    # Associare gli health check
    track_script {
        chk_haproxy
        chk_http
    }

    # Script da eseguire su transizione di stato
    notify_master "/etc/keepalived/scripts/notify.sh MASTER"
    notify_backup "/etc/keepalived/scripts/notify.sh BACKUP"
    notify_fault  "/etc/keepalived/scripts/notify.sh FAULT"
}
```

### Configurazione VRRP — Nodo Backup

`/etc/keepalived/keepalived.conf` sul nodo BACKUP:

```conf
global_defs {
    router_id LVS_BACKUP
    vrrp_skip_check_adv_addr
    vrrp_garp_interval 0
    vrrp_gna_interval 0
    enable_script_security
    script_user root
}

vrrp_script chk_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 2
    weight -20
    fall 3
    rise 2
}

vrrp_instance VI_1 {
    state BACKUP
    interface eth0
    virtual_router_id 51        # UGUALE al master
    priority 90                 # Priorità inferiore al master
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass SecretVRRP!
    }

    virtual_ipaddress {
        10.0.0.100/24 dev eth0 label eth0:vip
    }

    track_script {
        chk_haproxy
    }

    notify_master "/etc/keepalived/scripts/notify.sh MASTER"
    notify_backup "/etc/keepalived/scripts/notify.sh BACKUP"
    notify_fault  "/etc/keepalived/scripts/notify.sh FAULT"
}
```

### Script di Notifica

```bash
#!/bin/bash
# /etc/keepalived/scripts/notify.sh
STATE=$1
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

case $STATE in
    MASTER)
        logger "keepalived: Transizione a MASTER — $TIMESTAMP"
        systemctl start haproxy 2>/dev/null
        ;;
    BACKUP)
        logger "keepalived: Transizione a BACKUP — $TIMESTAMP"
        ;;
    FAULT)
        logger "keepalived: Transizione a FAULT — $TIMESTAMP"
        echo "Keepalived FAULT on $(hostname)" | mail -s "HA Alert" admin@example.com
        ;;
esac
```

```bash
chmod +x /etc/keepalived/scripts/notify.sh
sudo systemctl enable --now keepalived
```

### Verifica del Funzionamento

```bash
# Controllare lo stato VRRP
sudo journalctl -u keepalived -f

# Verificare che la VIP sia assegnata (solo sul master)
ip addr show eth0

# Output atteso sul master:
# 2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
#     inet 10.0.0.1/24 scope global eth0
#     inet 10.0.0.100/24 scope global secondary eth0:vip

# Simulare un failover (sul master)
sudo systemctl stop keepalived
# Verificare che la VIP si sposti sul backup
```

### Keepalived — Approfondimento VRRP

#### VRRP Internals

Il protocollo VRRP (RFC 5798) funziona con advertisement periodici:

```
Master invia VRRP advertisement ogni advert_int secondi (default: 1s)
via multicast 224.0.0.18, protocollo IP 112

  Master (priority=100)              Backup (priority=90)
     │                                    │
     ├──── VRRP advert ─────────────────► │  "Master è vivo"
     │     (ogni 1 secondo)               │
     ├──── VRRP advert ─────────────────► │
     │                                    │
     ✕  (Master muore)                    │
     │                                    │  Timer scade:
     │                                    │  3 * advert_int + skew_time
     │                                    │  = 3*1 + (256-90)/256 ≈ 3.65s
     │                             ┌──────┴──────┐
     │                             │ Backup →     │
     │                             │ Master       │
     │                             │ Invia GARP   │
     │                             └─────────────┘
```

#### Preemption e nopreempt

```conf
vrrp_instance VI_1 {
    state BACKUP              # Entrambi i nodi partono come BACKUP
    interface eth0
    virtual_router_id 51
    priority 100              # Il nodo con priorità più alta diventa Master
    advert_int 1
    nopreempt                 # NON riprendere il ruolo Master dopo recovery

    # nopreempt impedisce il "ping-pong":
    # 1. NodeA è Master (priority 100)
    # 2. NodeA cade, NodeB diventa Master
    # 3. NodeA torna → senza nopreempt, riprende il ruolo Master
    #    → con nopreempt, resta BACKUP finché NodeB non cade
    #
    # NOTA: per usare nopreempt, state deve essere BACKUP su entrambi i nodi
}
```

#### track_interface e track_script avanzati

```conf
# Monitorare lo stato delle interfacce
vrrp_instance VI_1 {
    track_interface {
        eth0 weight -50       # Se eth0 cade, priorità -50
        eth1 weight -30       # Se eth1 cade, priorità -30
    }

    # Se la priorità effettiva scende sotto quella del peer,
    # il peer diventa Master
}

# Script di health check avanzato con weight
vrrp_script chk_app {
    script "/usr/local/bin/check_app.sh"
    interval 3
    weight -40                # Riduce priorità se fallisce
    fall 3                    # 3 fallimenti consecutivi prima di reagire
    rise 2                    # 2 successi per tornare healthy
    timeout 5                 # Timeout per l'esecuzione dello script
}

# Script senza weight (binary: tutto o niente)
vrrp_script chk_gateway {
    script "/usr/bin/ping -c1 -W1 10.0.0.254"
    interval 5
    weight 0                  # weight 0 = se fallisce, transizione a FAULT
    fall 3
    rise 2
}
```

#### Unicast Peers (ambienti senza multicast)

In ambienti cloud o datacenter che non supportano multicast, usare unicast:

```conf
vrrp_instance VI_1 {
    state BACKUP
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    nopreempt

    # Disabilitare multicast, usare unicast
    unicast_src_ip 10.0.0.1   # IP locale

    unicast_peer {
        10.0.0.2              # IP del peer
        10.0.0.3              # Terzo nodo (opzionale)
    }

    virtual_ipaddress {
        10.0.0.100/24 dev eth0
    }

    # Notify scripts per integrazione con altri servizi
    notify_master "/etc/keepalived/scripts/master.sh"
    notify_backup "/etc/keepalived/scripts/backup.sh"
    notify_fault  "/etc/keepalived/scripts/fault.sh"
    notify_stop   "/etc/keepalived/scripts/stop.sh"
}
```

#### Istanze VRRP Multiple

```conf
# VIP per il servizio web
vrrp_instance VI_WEB {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    virtual_ipaddress {
        10.0.0.100/24
    }
}

# VIP per il servizio database (su un altro nodo per bilanciare)
vrrp_instance VI_DB {
    state BACKUP
    interface eth0
    virtual_router_id 52        # ID diverso!
    priority 90
    virtual_ipaddress {
        10.0.0.101/24
    }
}

# Risultato: NodeA gestisce la VIP web, NodeB gestisce la VIP database
# Se un nodo cade, l'altro prende entrambe le VIP
```

---

## HAProxy — Load Balancing Avanzato

HAProxy è il load balancer open-source più diffuso e performante. Supporta TCP (layer 4) e HTTP (layer 7), con capacità di gestire milioni di connessioni concorrenti.

### Installazione

```bash
# RHEL/CentOS (versione recente dal repo ufficiale)
sudo dnf install -y haproxy

# Debian/Ubuntu
sudo apt install -y haproxy

# Abilitare
sudo systemctl enable haproxy
```

### Configurazione Completa

`/etc/haproxy/haproxy.cfg`:

```conf
#---------------------------------------------------------------------
# Configurazione globale
#---------------------------------------------------------------------
global
    log         /dev/log local0
    log         /dev/log local1 notice
    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     50000
    user        haproxy
    group       haproxy
    daemon

    # Tuning performance
    nbthread    4
    cpu-map     auto:1/1-4 0-3

    # SSL/TLS globale
    ssl-default-bind-ciphersuites   TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
    ssl-default-bind-options        ssl-min-ver TLSv1.2 no-tls-tickets
    tune.ssl.default-dh-param       2048

#---------------------------------------------------------------------
# Defaults
#---------------------------------------------------------------------
defaults
    mode        http
    log         global
    option      httplog
    option      dontlognull
    option      http-server-close
    option      forwardfor except 127.0.0.0/8
    option      redispatch
    retries     3
    timeout connect     5s
    timeout client      30s
    timeout server      30s
    timeout http-request 10s
    timeout http-keep-alive 10s
    timeout queue       30s
    timeout check       5s

    # Compressione
    compression algo gzip deflate
    compression type text/html text/plain text/css application/javascript application/json

    # Error files
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

#---------------------------------------------------------------------
# Pagina di statistiche
#---------------------------------------------------------------------
listen stats
    bind *:8404
    mode http
    stats enable
    stats uri /stats
    stats refresh 10s
    stats show-legends
    stats show-node
    stats auth admin:StatsPassword123!
    stats admin if TRUE

#---------------------------------------------------------------------
# Frontend HTTP → redirect a HTTPS
#---------------------------------------------------------------------
frontend http-in
    bind *:80

    acl is_health_check path /health
    http-request return status 200 content-type text/plain string "OK" if is_health_check

    redirect scheme https code 301 if !{ ssl_fc }

#---------------------------------------------------------------------
# Frontend HTTPS
#---------------------------------------------------------------------
frontend https-in
    bind *:443 ssl crt /etc/haproxy/certs/example.com.pem alpn h2,http/1.1

    # Headers di sicurezza
    http-response set-header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
    http-response set-header X-Content-Type-Options "nosniff"
    http-response set-header X-Frame-Options "DENY"
    http-response set-header Referrer-Policy "strict-origin-when-cross-origin"

    # ACL per routing basato su dominio
    acl host_app1   hdr(host) -i app1.example.com
    acl host_app2   hdr(host) -i app2.example.com
    acl host_api    hdr(host) -i api.example.com

    # ACL per routing basato su path
    acl path_api    path_beg /api/
    acl path_static path_beg /static/ /images/ /css/ /js/
    acl path_ws     path_beg /ws/

    # ACL per rate limiting
    acl too_many_requests sc_http_req_rate(0) gt 100
    http-request track-sc0 src table rate_limit_table
    http-request deny deny_status 429 if too_many_requests

    # ACL per blocco IP
    acl blocked_ips src -f /etc/haproxy/blocked_ips.lst
    http-request deny if blocked_ips

    # Routing
    use_backend backend_app1    if host_app1
    use_backend backend_app2    if host_app2
    use_backend backend_api     if host_api or path_api
    use_backend backend_static  if path_static
    use_backend backend_ws      if path_ws

    default_backend backend_app1

#---------------------------------------------------------------------
# Backend tabella rate limiting
#---------------------------------------------------------------------
backend rate_limit_table
    stick-table type ip size 200k expire 30s store http_req_rate(10s)

#---------------------------------------------------------------------
# Backend applicazione 1 (round-robin con health check)
#---------------------------------------------------------------------
backend backend_app1
    balance roundrobin
    option httpchk GET /health HTTP/1.1\r\nHost:\ app1.example.com
    http-check expect status 200

    cookie SERVERID insert indirect nocache

    server app1-web1 10.0.0.11:8080 check inter 5s fall 3 rise 2 cookie web1 weight 100
    server app1-web2 10.0.0.12:8080 check inter 5s fall 3 rise 2 cookie web2 weight 100
    server app1-web3 10.0.0.13:8080 check inter 5s fall 3 rise 2 cookie web3 weight 50
    server app1-backup 10.0.0.14:8080 check inter 10s fall 3 rise 2 backup

#---------------------------------------------------------------------
# Backend API (least connections)
#---------------------------------------------------------------------
backend backend_api
    balance leastconn
    option httpchk GET /api/health
    http-check expect status 200

    timeout server 60s
    timeout connect 10s

    option redispatch
    retries 3
    retry-on conn-failure empty-response response-timeout 502 503 504

    server api1 10.0.0.21:3000 check inter 5s fall 3 rise 2 maxconn 500
    server api2 10.0.0.22:3000 check inter 5s fall 3 rise 2 maxconn 500

#---------------------------------------------------------------------
# Backend WebSocket
#---------------------------------------------------------------------
backend backend_ws
    balance source
    option httpchk GET /ws/health

    timeout tunnel 3600s
    timeout server 3600s

    server ws1 10.0.0.31:8080 check inter 10s
    server ws2 10.0.0.32:8080 check inter 10s

#---------------------------------------------------------------------
# Backend contenuti statici (con cache)
#---------------------------------------------------------------------
backend backend_static
    balance roundrobin
    http-response set-header Cache-Control "public, max-age=86400"

    server static1 10.0.0.41:80 check
    server static2 10.0.0.42:80 check
```

### Algoritmi di Bilanciamento

| Algoritmo | Descrizione | Uso Tipico |
|-----------|-------------|------------|
| `roundrobin` | Rotazione ciclica con pesi | Default, applicazioni stateless |
| `leastconn` | Server con meno connessioni | API con richieste di durata variabile |
| `source` | Hash dell'IP sorgente | Persistenza senza cookie |
| `uri` | Hash dell'URI | CDN, caching |
| `hdr(name)` | Hash di un header HTTP | Routing per tenant |
| `first` | Primo server disponibile | Minimizzare i server attivi |
| `random` | Scelta casuale con pesi | Buona distribuzione statistica |

### SSL Termination

```bash
# Generare certificato con Let's Encrypt
sudo certbot certonly --standalone -d example.com -d www.example.com

# Combinare cert e key in un file PEM per HAProxy
sudo bash -c 'cat /etc/letsencrypt/live/example.com/fullchain.pem \
  /etc/letsencrypt/live/example.com/privkey.pem > /etc/haproxy/certs/example.com.pem'

# Permessi
sudo chmod 600 /etc/haproxy/certs/example.com.pem

# Rinnovo automatico con deploy hook
sudo bash -c 'cat > /etc/letsencrypt/renewal-hooks/deploy/haproxy.sh << "SCRIPT"
#!/bin/bash
DOMAIN=example.com
cat /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
    /etc/letsencrypt/live/$DOMAIN/privkey.pem > /etc/haproxy/certs/$DOMAIN.pem
systemctl reload haproxy
SCRIPT'
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/haproxy.sh
```

### Verifica e Gestione Runtime

```bash
# Verificare la configurazione
haproxy -c -f /etc/haproxy/haproxy.cfg

# Reload senza downtime (hitless reload)
sudo systemctl reload haproxy

# Comandi via socket
echo "show stat" | sudo socat stdio /var/lib/haproxy/stats
echo "show servers state" | sudo socat stdio /var/lib/haproxy/stats

# Disabilitare un server (drain per manutenzione)
echo "set server backend_app1/app1-web1 state drain" | sudo socat stdio /var/lib/haproxy/stats

# Mettere un server in manutenzione
echo "set server backend_app1/app1-web1 state maint" | sudo socat stdio /var/lib/haproxy/stats

# Riabilitare
echo "set server backend_app1/app1-web1 state ready" | sudo socat stdio /var/lib/haproxy/stats

# Modificare il peso a runtime
echo "set weight backend_app1/app1-web1 50" | sudo socat stdio /var/lib/haproxy/stats
```

---

## DRBD — Replicated Storage

DRBD (Distributed Replicated Block Device) crea un disco replicato via rete tra due o più nodi. È come un RAID 1 via rete: ogni scrittura sul nodo primario viene replicata in tempo reale sul secondario.

### Installazione

```bash
# RHEL/CentOS
sudo dnf install -y drbd-utils kmod-drbd

# Debian/Ubuntu
sudo apt install -y drbd-utils drbd-dkms

# Caricare il modulo kernel
sudo modprobe drbd
echo "drbd" | sudo tee /etc/modules-load.d/drbd.conf
```

### Configurazione

#### File di configurazione globale `/etc/drbd.d/global_common.conf`

```conf
global {
    usage-count no;
}

common {
    handlers {
        fence-peer "/usr/lib/drbd/crm-fence-peer.9.sh";
        after-resync-target "/usr/lib/drbd/crm-unfence-peer.9.sh";
        split-brain "/usr/lib/drbd/notify-split-brain.sh admin@example.com";
    }

    startup {
        wfc-timeout 30;
        degr-wfc-timeout 20;
    }

    disk {
        on-io-error detach;
        resync-rate 100M;
        c-plan-ahead 20;
        c-fill-target 50k;
        c-max-rate 200M;
    }

    net {
        protocol C;
        cram-hmac-alg sha256;
        shared-secret "DRBDSecret123!";
        max-buffers 8000;
        max-epoch-size 8000;
        sndbuf-size 0;
        rcvbuf-size 0;
    }
}
```

I protocolli di replica DRBD hanno significati precisi:

| Protocollo | Descrizione | RPO | Performance |
|------------|-------------|-----|-------------|
| **A** | Asincrono — conferma appena scritto nel buffer TCP locale | Possibile perdita | Più veloce |
| **B** | Semi-sincrono — conferma quando il dato raggiunge il buffer del nodo remoto | Quasi zero perdita | Medio |
| **C** | Sincrono — conferma solo quando il dato è scritto su disco remoto | Zero perdita | Più lento |

#### Risorsa DRBD `/etc/drbd.d/data.res`

```conf
resource data {
    device /dev/drbd0;
    disk /dev/vdb;
    meta-disk internal;

    on node1.example.com {
        address 10.0.1.1:7789;
        node-id 0;
    }

    on node2.example.com {
        address 10.0.1.2:7789;
        node-id 1;
    }

    connection-mesh {
        hosts node1.example.com node2.example.com;
    }
}
```

### Inizializzazione

```bash
# Creare i metadata (su ENTRAMBI i nodi)
sudo drbdadm create-md data

# Avviare la risorsa (su ENTRAMBI)
sudo drbdadm up data

# Forzare la sincronizzazione iniziale (solo sul nodo che diventerà primario)
sudo drbdadm primary --force data

# Verificare lo stato
sudo drbdadm status data
# Output:
# data role:Primary
#   disk:UpToDate
#   peer role:Secondary
#     replication:SyncSource peer-disk:Inconsistent done:45.23%

# Attendere il completamento e poi creare il filesystem
sudo mkfs.ext4 /dev/drbd0
sudo mount /dev/drbd0 /mnt/data
```

### Operazioni Comuni

```bash
# Promuovere a primario
sudo drbdadm primary data

# Retrocedere a secondario
sudo umount /mnt/data
sudo drbdadm secondary data

# Stato dettagliato
cat /proc/drbd
sudo drbdsetup status data --verbose --statistics

# Verificare la connessione
sudo drbdadm cstate data

# Verificare i ruoli
sudo drbdadm role data

# Invalidare un peer (forzare full resync)
sudo drbdadm invalidate-remote data
```

### Integrazione con Pacemaker

```bash
# Creare la risorsa DRBD in Pacemaker
sudo pcs resource create drbd-data ocf:linbit:drbd \
  drbd_resource=data \
  op monitor interval=30s role=Master \
  op monitor interval=60s role=Slave

# Creare la risorsa clone con promozione
sudo pcs resource promotable drbd-data \
  promoted-max=1 \
  promoted-node-max=1 \
  clone-max=2 \
  clone-node-max=1 \
  notify=true

# Filesystem sopra DRBD (solo sul nodo promoted)
sudo pcs resource create fs-data ocf:heartbeat:Filesystem \
  device=/dev/drbd0 \
  directory=/mnt/data \
  fstype=ext4

# Vincoli: filesystem solo dove DRBD è Primary
sudo pcs constraint colocation add fs-data with drbd-data-clone INFINITY with-rsc-role=Master
sudo pcs constraint order promote drbd-data-clone then start fs-data
```

### DRBD — Approfondimento

#### Dual-Primary Mode

DRBD supporta la modalità dual-primary: entrambi i nodi sono Primary contemporaneamente. Richiede un filesystem cluster-aware (GFS2 o OCFS2) sopra il device DRBD.

```conf
# In /etc/drbd.d/data.res — abilitare dual-primary
resource data {
    net {
        protocol C;
        allow-two-primaries yes;
    }

    device /dev/drbd0;
    disk /dev/vdb;
    meta-disk internal;

    on node1.example.com {
        address 10.0.1.1:7789;
        node-id 0;
    }
    on node2.example.com {
        address 10.0.1.2:7789;
        node-id 1;
    }
}
```

```bash
# Promuovere entrambi i nodi a Primary
sudo drbdadm primary data    # su node1
sudo drbdadm primary data    # su node2

# ATTENZIONE: usare SOLO con GFS2 o OCFS2
# ext4/xfs/btrfs NON supportano accesso concorrente → CORRUZIONE
```

#### Auto-promote

DRBD 9 supporta auto-promote: il nodo diventa Primary automaticamente quando un processo tenta di montare il device.

```conf
resource data {
    options {
        auto-promote yes;
    }
}
```

```bash
# Con auto-promote basta montare:
sudo mount /dev/drbd0 /mnt/data     # → promozione automatica a Primary
sudo umount /mnt/data                # → retrocessione a Secondary
```

#### Performance Tuning DRBD

```conf
# Ottimizzazione per reti 10GbE+
resource data {
    disk {
        resync-rate 500M;
        c-plan-ahead 20;
        c-fill-target 100k;
        c-max-rate 800M;
        al-extents 3389;          # Activity log: più grande = meno seeks
        # Solo se il controller ha BBU (Battery Backup Unit):
        # disk-barrier no;
        # disk-flushes no;
    }

    net {
        max-buffers 36000;
        max-epoch-size 36000;
        sndbuf-size 0;            # 0 = autotuning
        rcvbuf-size 0;
    }
}
```

```bash
# Verificare performance
sudo drbdsetup status data --verbose --statistics
# Campi importanti:
#   upper_pending  → I/O in attesa dall'applicazione
#   lower_pending  → I/O in attesa dal disco locale
#   ap_in_flight   → scritture in volo verso il peer
```

### Storage HA — Filesystem Cluster

Per accesso concorrente da più nodi (active/active), servono filesystem cluster-aware con Distributed Lock Manager (DLM).

#### GFS2 su DRBD Dual-Primary

```bash
# Installare DLM e GFS2
sudo dnf install -y dlm gfs2-utils

# Configurare DLM in Pacemaker
sudo pcs resource create dlm ocf:pacemaker:controld \
  op monitor interval=30s on-fail=fence
sudo pcs resource clone dlm clone-max=2 clone-node-max=1

# Creare il filesystem GFS2 su DRBD dual-primary
sudo mkfs.gfs2 -p lock_dlm -t ha-cluster:data \
  -j 2 /dev/drbd0    # -j 2 = 2 journal (uno per nodo)

# Risorsa filesystem GFS2 clonata
sudo pcs resource create gfs2-data ocf:heartbeat:Filesystem \
  device=/dev/drbd0 \
  directory=/mnt/shared \
  fstype=gfs2 \
  options="noatime,nodiratime"

sudo pcs resource clone gfs2-data clone-max=2

# Vincoli: DLM prima di GFS2
sudo pcs constraint order dlm-clone then gfs2-data-clone
sudo pcs constraint colocation add gfs2-data-clone with dlm-clone
```

### Network HA — Bonding e Ridondanza

#### Bonding Modes

| Mode | Nome | Descrizione | Switch config |
|------|------|-------------|---------------|
| 0 | balance-rr | Round-robin | No |
| 1 | active-backup | Una sola interfaccia attiva | No |
| 2 | balance-xor | XOR hash su MAC src/dst | No |
| 4 | 802.3ad | LACP (Link Aggregation) | Sì |
| 5 | balance-tlb | Adaptive transmit LB | No |
| 6 | balance-alb | Adaptive LB (TX+RX) | No |

```bash
# Configurazione bonding mode 4 (LACP) con NetworkManager
sudo nmcli con add type bond con-name bond0 ifname bond0 \
  bond.options "mode=802.3ad,miimon=100,lacp_rate=fast,xmit_hash_policy=layer3+4"

sudo nmcli con add type ethernet con-name bond0-port1 \
  ifname eth0 master bond0

sudo nmcli con add type ethernet con-name bond0-port2 \
  ifname eth1 master bond0

sudo nmcli con mod bond0 ipv4.addresses 10.0.0.1/24 ipv4.method manual
sudo nmcli con up bond0

# Verificare lo stato
cat /proc/net/bonding/bond0
```

#### BFD (Bidirectional Forwarding Detection)

BFD (RFC 5880) rileva guasti di rete tra nodi adiacenti in millisecondi (vs secondi del heartbeat cluster).

```bash
# BFD supportato nativamente da FRRouting
sudo vtysh
configure terminal
  bfd
    peer 10.0.0.2
      receive-interval 300      # ms
      transmit-interval 300
      detect-multiplier 3       # 3 miss = down (900ms totali)
    exit
  exit
exit
```

---

## Storage Distribuito: GlusterFS e Ceph

### GlusterFS — Concetti e Setup Base

GlusterFS è un filesystem distribuito che aggrega storage da più server in un singolo namespace.

```bash
# Installazione (su tutti i nodi)
sudo dnf install -y glusterfs-server
sudo systemctl enable --now glusterd

# Firewall
sudo firewall-cmd --permanent --add-service=glusterfs
sudo firewall-cmd --reload

# Aggiungere peer (da un nodo)
sudo gluster peer probe node2.example.com
sudo gluster peer probe node3.example.com

# Verificare
sudo gluster peer status

# Creare un volume replicato (replica 3)
sudo gluster volume create gv0 replica 3 \
  node1.example.com:/data/brick1/gv0 \
  node2.example.com:/data/brick1/gv0 \
  node3.example.com:/data/brick1/gv0

# Avviare il volume
sudo gluster volume start gv0

# Montare il volume
sudo mount -t glusterfs node1.example.com:/gv0 /mnt/gluster

# Montaggio persistente in /etc/fstab
# node1.example.com:/gv0 /mnt/gluster glusterfs defaults,_netdev,backup-volfile-servers=node2.example.com:node3.example.com 0 0
```

Tipi di volume GlusterFS:

| Tipo | Descrizione | Spazio Utile |
|------|-------------|-------------|
| **Distribute** | Distribuisce i file tra i brick | Somma totale |
| **Replicate** | Replica ogni file su N brick | Totale / N |
| **Disperse** | Erasure coding (simile a RAID 5/6) | Configurabile |
| **Distributed-Replicate** | Distribuisce e replica | Somma / replica |

### Ceph — Architettura e Setup Base

Ceph è un sistema di storage distribuito che offre block storage (RBD), object storage (S3-compatible) e filesystem (CephFS) da un singolo cluster.

```
┌─────────────────────────────────────────────┐
│              Client Layer                    │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐    │
│  │  RBD    │  │ CephFS  │  │ RADOS GW │    │
│  │ (block) │  │ (POSIX) │  │  (S3/obj)│    │
│  └────┬────┘  └────┬────┘  └────┬─────┘    │
├───────┴────────────┴────────────┴───────────┤
│              RADOS (Reliable Autonomic       │
│              Distributed Object Store)       │
├─────────────────────────────────────────────┤
│  ┌───────┐  ┌───────┐  ┌───────┐           │
│  │ OSD 1 │  │ OSD 2 │  │ OSD N │  ...      │
│  └───────┘  └───────┘  └───────┘           │
│  ┌───────┐  ┌───────┐  ┌───────┐           │
│  │ MON 1 │  │ MON 2 │  │ MON 3 │           │
│  └───────┘  └───────┘  └───────┘           │
│  ┌───────┐  ┌───────┐  ┌───────┐           │
│  │ MGR 1 │  │ MGR 2 │  │ MDS 1 │           │
│  └───────┘  └───────┘  └───────┘           │
└─────────────────────────────────────────────┘
```

Componenti chiave:
- **MON** (Monitor): mantiene la mappa del cluster, quorum
- **OSD** (Object Storage Daemon): uno per disco, gestisce storage e replicazione
- **MGR** (Manager): metriche, dashboard, moduli
- **MDS** (Metadata Server): necessario solo per CephFS

```bash
# Installazione con cephadm (metodo moderno)
sudo dnf install -y cephadm ceph-common

# Bootstrap del cluster (primo nodo)
sudo cephadm bootstrap \
  --mon-ip 10.0.0.1 \
  --initial-dashboard-user admin \
  --initial-dashboard-password CephAdmin123! \
  --allow-fqdn-hostname

# Aggiungere host
sudo ceph orch host add node2.example.com 10.0.0.2
sudo ceph orch host add node3.example.com 10.0.0.3

# Aggiungere tutti i dischi come OSD
sudo ceph orch apply osd --all-available-devices

# Verificare
sudo ceph status
sudo ceph osd tree

# Creare un pool per RBD
sudo ceph osd pool create rbd-pool 128
sudo ceph osd pool application enable rbd-pool rbd

# Creare un'immagine block
sudo rbd create --size 100G --pool rbd-pool my-disk
sudo rbd map rbd-pool/my-disk
sudo mkfs.ext4 /dev/rbd0
sudo mount /dev/rbd0 /mnt/ceph-block
```

---

## Scenari Pratici HA

### Scenario 1: Web Server HA con Pacemaker + HAProxy + DRBD

Architettura completa per un sito web ad alta disponibilità:

```
              Internet
                 │
          ┌──────┴──────┐
          │   Firewall   │
          └──────┬──────┘
                 │
    ┌────────────┴────────────┐
    │     VIP: 10.0.0.100     │
    │  (Pacemaker managed)    │
    ├─────────────────────────┤
    │                         │
┌───┴───┐               ┌────┴──┐
│Node A │   Heartbeat    │Node B │
│HAProxy│◄──────────────►│HAProxy│
│DRBD P │   (Corosync)  │DRBD S │
└───┬───┘               └───┬───┘
    │                        │
    └────────┬───────────────┘
             │
    ┌────────┴────────┐
    │  Backend Pool    │
    │  web1  web2  web3│
    └─────────────────┘
```

Configurazione completa:

```bash
# 1. Setup del cluster Pacemaker (da node A)
sudo pcs host auth nodeA.example.com nodeB.example.com -u hacluster -p 'Pass123!'
sudo pcs cluster setup web-ha nodeA.example.com nodeB.example.com
sudo pcs cluster start --all
sudo pcs cluster enable --all

# 2. Configurare STONITH (esempio con fence_virsh per VM)
sudo pcs stonith create fence-nodeA fence_virsh \
  ip=hypervisor.example.com \
  login=root \
  identity_file=/root/.ssh/id_rsa \
  plug=nodeA \
  pcmk_host_list=nodeA.example.com

sudo pcs stonith create fence-nodeB fence_virsh \
  ip=hypervisor.example.com \
  login=root \
  identity_file=/root/.ssh/id_rsa \
  plug=nodeB \
  pcmk_host_list=nodeB.example.com

# 3. Risorse DRBD
sudo pcs resource create drbd-www ocf:linbit:drbd \
  drbd_resource=www \
  op monitor interval=30s role=Master \
  op monitor interval=60s role=Slave

sudo pcs resource promotable drbd-www \
  promoted-max=1 promoted-node-max=1 \
  clone-max=2 clone-node-max=1 notify=true

# 4. Filesystem su DRBD
sudo pcs resource create fs-www ocf:heartbeat:Filesystem \
  device=/dev/drbd0 directory=/var/www fstype=ext4

# 5. VIP
sudo pcs resource create vip-www ocf:heartbeat:IPaddr2 \
  ip=10.0.0.100 cidr_netmask=24 nic=eth0

# 6. HAProxy come risorsa del cluster
sudo pcs resource create haproxy-www systemd:haproxy \
  op monitor interval=10s timeout=20s

# 7. Gruppo di risorse (ordine di avvio)
sudo pcs resource group add web-ha-group \
  fs-www vip-www haproxy-www

# 8. Vincoli
sudo pcs constraint colocation add web-ha-group with drbd-www-clone INFINITY with-rsc-role=Master
sudo pcs constraint order promote drbd-www-clone then start web-ha-group
```

### Scenario 2: Database HA con Failover Automatico (PostgreSQL)

```bash
# Risorse Pacemaker per PostgreSQL HA
# Prerequisito: PostgreSQL configurato per streaming replication

# 1. Risorsa PostgreSQL con promozione
sudo pcs resource create pgsql ocf:heartbeat:pgsql \
  pgctl="/usr/pgsql-15/bin/pg_ctl" \
  psql="/usr/pgsql-15/bin/psql" \
  pgdata="/var/lib/pgsql/15/data" \
  rep_mode="sync" \
  node_list="nodeA nodeB" \
  primary_conninfo_opt="keepalives_idle=60 keepalives_interval=5 keepalives_count=5" \
  master_ip="10.0.0.100" \
  repuser="replicator" \
  restore_command="cp /var/lib/pgsql/15/archive/%f %p" \
  op start timeout=60s \
  op stop timeout=60s \
  op promote timeout=30s \
  op demote timeout=120s \
  op monitor interval=15s timeout=10s \
  op monitor interval=10s timeout=10s role=Master \
  op notify timeout=60s

# 2. Clone con promozione
sudo pcs resource promotable pgsql \
  promoted-max=1 promoted-node-max=1 \
  clone-max=2 clone-node-max=1 notify=true

# 3. VIP per il database
sudo pcs resource create vip-pgsql ocf:heartbeat:IPaddr2 \
  ip=10.0.0.100 cidr_netmask=24

# 4. Vincoli
sudo pcs constraint colocation add vip-pgsql with pgsql-clone INFINITY with-rsc-role=Master
sudo pcs constraint order promote pgsql-clone then start vip-pgsql
```

### Test del Failover

```bash
# Verificare lo stato iniziale
sudo pcs status

# Simulare il guasto del nodo primario
sudo pcs node standby nodeA.example.com

# Osservare il failover
watch -n 1 'pcs status'

# Output atteso:
# * nodeA.example.com: standby
# * nodeB.example.com: online
# * vip-www (ocf:heartbeat:IPaddr2): Started nodeB.example.com
# * drbd-www-clone: Masters: [ nodeB.example.com ]
#                   Stopped: [ nodeA.example.com ]

# Riportare il nodo online
sudo pcs node unstandby nodeA.example.com

# La risorsa NON torna su nodeA automaticamente (resource-stickiness)
# Per forzare il ritorno:
sudo pcs resource move vip-www nodeA.example.com
# Ricordarsi di pulire il vincolo temporaneo:
sudo pcs resource clear vip-www
```

### Scenario 3: Database HA con Patroni (PostgreSQL)

Patroni è il framework standard per PostgreSQL HA. Gestisce automaticamente streaming replication, failover e leader election tramite etcd/Consul/ZooKeeper.

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  etcd node1  │   │  etcd node2  │   │  etcd node3  │
│  (consenso)  │   │  (consenso)  │   │  (consenso)  │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       └──────────────────┼──────────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
┌──────▼───────┐   ┌──────▼───────┐   ┌──────▼───────┐
│  Patroni     │   │  Patroni     │   │  Patroni     │
│  PostgreSQL  │   │  PostgreSQL  │   │  PostgreSQL  │
│  PRIMARY     │   │  REPLICA     │   │  REPLICA     │
│  10.0.0.11   │   │  10.0.0.12   │   │  10.0.0.13   │
└──────────────┘   └──────────────┘   └──────────────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                   ┌──────▼───────┐
                   │  HAProxy     │
                   │  VIP: .100   │
                   │  R/W → Primary│
                   │  R/O → Replica│
                   └──────────────┘
```

```yaml
# /etc/patroni/patroni.yml — configurazione essenziale
scope: pg-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.0.11:8008

etcd3:
  hosts: 10.0.0.1:2379,10.0.0.2:2379,10.0.0.3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576    # 1MB max lag per failover
    synchronous_mode: true               # Replica sincrona

    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 200
        shared_buffers: 4GB
        wal_level: replica
        hot_standby: "on"
        max_wal_senders: 10
        max_replication_slots: 10

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.0.11:5432
  data_dir: /var/lib/pgsql/16/data
  authentication:
    superuser:
      username: postgres
      password: "${PATRONI_SUPERUSER_PASSWORD}"
    replication:
      username: replicator
      password: "${PATRONI_REPLICATION_PASSWORD}"
```

```bash
# HAProxy per routing R/W e R/O automatico
# In /etc/haproxy/haproxy.cfg — aggiungere:
listen pgsql-primary
    bind *:5432
    mode tcp
    option httpchk GET /primary
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server pg1 10.0.0.11:5432 check port 8008
    server pg2 10.0.0.12:5432 check port 8008
    server pg3 10.0.0.13:5432 check port 8008

listen pgsql-replica
    bind *:5433
    mode tcp
    balance roundrobin
    option httpchk GET /replica
    http-check expect status 200
    default-server inter 3s fall 3 rise 2
    server pg1 10.0.0.11:5432 check port 8008
    server pg2 10.0.0.12:5432 check port 8008
    server pg3 10.0.0.13:5432 check port 8008
```

#### MySQL Group Replication

```bash
# Configurazione essenziale in /etc/my.cnf per Group Replication
[mysqld]
server-id=1
gtid_mode=ON
enforce_gtid_consistency=ON
binlog_checksum=NONE

plugin_load_add='group_replication.so'
group_replication_group_name="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
group_replication_start_on_boot=OFF
group_replication_local_address="10.0.0.11:33061"
group_replication_group_seeds="10.0.0.11:33061,10.0.0.12:33061,10.0.0.13:33061"
group_replication_single_primary_mode=ON    # Single-primary mode

# Avviare Group Replication (sul primo nodo)
mysql> SET GLOBAL group_replication_bootstrap_group=ON;
mysql> START GROUP_REPLICATION;
mysql> SET GLOBAL group_replication_bootstrap_group=OFF;

# Sugli altri nodi:
mysql> START GROUP_REPLICATION;

# Verificare
mysql> SELECT * FROM performance_schema.replication_group_members;
```

### Application-Level HA

#### Stateless vs Stateful

```
Stateless (preferibile per HA):
─────────────────────────────────
- Ogni richiesta è autocontenuta
- Nessuno stato in memoria tra richieste
- Session data in Redis/DB esterno
- Scalabilità orizzontale banale
- Failover: il load balancer manda la richiesta a un altro nodo

Stateful (richiede attenzione):
──────────────────────────────
- Stato in memoria (sessioni, cache, WebSocket)
- Richiede session affinity (sticky sessions)
- Failover: lo stato si perde (necessario session replication)
- Opzioni: Redis per sessioni, DB per stato, broadcast cluster
```

#### Session Affinity in HAProxy

```conf
backend app-backend
    balance roundrobin
    # Cookie-based affinity (preferito)
    cookie SERVERID insert indirect nocache maxidle 30m maxlife 12h

    server app1 10.0.0.11:8080 check cookie s1
    server app2 10.0.0.12:8080 check cookie s2
    server app3 10.0.0.13:8080 check cookie s3

    # Se il server originale cade, il client viene redistribuito
    # → l'applicazione deve ricreare la sessione (da Redis/DB)
    option redispatch
```

#### Graceful Degradation

```
Pattern: Circuit Breaker con fallback

  Client ──► Service A ──► Service B (down)
                 │
                 └──► Circuit Breaker aperto
                      │
                      └──► Fallback: dati cache / risposta degradata / coda

Implementazione pratica:
1. Monitor del servizio dipendente
2. Dopo N fallimenti → circuit breaker OPEN
3. Risposte degradate (cache stale, feature ridotte)
4. Periodicamente → HALF-OPEN: tentativo di ripristino
5. Successo → CLOSED: ripristino completo
```

### Cloud HA Patterns

#### Floating IP con API Cloud

```bash
# Esempio: Hetzner Cloud Floating IP failover
# Script da usare come notify_master in Keepalived

#!/bin/bash
# /etc/keepalived/scripts/hetzner-floating-ip.sh
FLOATING_IP_ID="12345"
SERVER_ID="67890"
API_TOKEN="${HCLOUD_TOKEN}"

curl -s -X POST \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"server\": ${SERVER_ID}}" \
  "https://api.hetzner.cloud/v1/floating_ips/${FLOATING_IP_ID}/actions/assign"

logger "Floating IP ${FLOATING_IP_ID} assegnato al server ${SERVER_ID}"
```

#### Cloud Fence Agents

```bash
# AWS fence agent (spegne l'istanza EC2)
sudo pcs stonith create fence-aws fence_aws \
  region=eu-west-1 \
  access_key="${AWS_ACCESS_KEY}" \
  secret_key="${AWS_SECRET_KEY}" \
  plug=i-0abc123def456 \
  pcmk_host_list=node1.internal

# GCP fence agent
sudo pcs stonith create fence-gcp fence_gce \
  project=my-project \
  zone=europe-west1-b \
  plug=instance-1 \
  pcmk_host_list=node1.internal

# Azure fence agent
sudo pcs stonith create fence-azure fence_azure_arm \
  subscriptionId="${AZURE_SUB_ID}" \
  resourceGroup=my-rg \
  tenantId="${AZURE_TENANT_ID}" \
  login="${AZURE_APP_ID}" \
  passwd="${AZURE_PASSWORD}" \
  pcmk_host_list=node1 \
  plug=node1
```

#### Cross-AZ HA

```
Architettura HA cross Availability Zone:

  AZ-A (eu-west-1a)         AZ-B (eu-west-1b)        AZ-C (eu-west-1c)
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │  Node1           │       │  Node2           │       │  Node3           │
  │  Pacemaker       │       │  Pacemaker       │       │  Pacemaker       │
  │  App + DB Primary│       │  App + DB Replica│       │  Quorum Device   │
  └────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
           │                          │                          │
           └──────── VPC Peering / Transit Gateway ─────────────┘

Considerazioni:
- Latenza inter-AZ: 1-5 ms (accettabile per DRBD protocol C)
- DRBD protocol A per cross-region (>50 ms latenza)
- Cloud fence agents al posto di IPMI
- Elastic IP / Floating IP per la VIP
- Usare un Network Load Balancer cloud come alternativa alla VIP
```

---

## Split-Brain: Prevenzione e Gestione

Lo split-brain è la condizione più pericolosa in un cluster: due o più partizioni credono entrambe di essere il cluster attivo, portando a corruzione dei dati.

### Strategie di Prevenzione

```
1. QUORUM — La partizione con la maggioranza dei voti vince
   Cluster a 3 nodi: serve 2/3 per il quorum
   Se la rete si divide 2-1, la partizione con 2 nodi sopravvive

2. FENCING — Spegni forzatamente i nodi della partizione minoritaria
   Anche se un nodo "pensa" di essere attivo,
   il fencing lo spegne prima che faccia danni

3. QUORUM DEVICE — Per cluster a 2 nodi
   Un terzo votante leggero che rompe il pareggio

4. WATCHDOG — Timeout hardware
   Se il nodo non riesce a contattare il cluster,
   il watchdog hardware lo resetta
```

### Gestione Split-Brain su DRBD

```bash
# DRBD ha politiche specifiche per lo split-brain

# In /etc/drbd.d/global_common.conf, sezione net:
net {
    after-sb-0pri disconnect;
    after-sb-1pri discard-secondary;
    after-sb-2pri disconnect;
}

# Recupero manuale dopo split-brain DRBD
# 1. Identificare il nodo con i dati corretti (il "vincitore")
# 2. Sul nodo "perdente" (dati da scartare):
sudo drbdadm disconnect data
sudo drbdadm secondary data
sudo drbdadm -- --discard-my-data connect data

# 3. Sul nodo "vincitore":
sudo drbdadm disconnect data
sudo drbdadm connect data

# 4. Verificare che la sincronizzazione riprenda
sudo drbdadm status data
```

### Strategie Avanzate di Prevenzione Split-Brain

Lo split-brain è il guasto più pericoloso in un cluster HA. Prevenirlo richiede una strategia multilivello.

#### Quorum Device — Algoritmi di Voto

Il **quorum device** (`corosync-qdevice`) aggiunge un voto esterno al cluster, risolvendo il problema del quorum nei cluster a 2 nodi senza aggiungere un terzo nodo completo:

```bash
# Installazione del quorum device (sul nodo arbitro esterno)
sudo dnf install corosync-qnetd
sudo pcs qdevice setup model net --enable --start

# Configurazione sul cluster (da un nodo del cluster)
sudo pcs quorum device add model net \
  host=qnetd-host.example.com \
  algorithm=ffsplit

# Verifica dello stato del quorum device
sudo pcs quorum device status
sudo corosync-quorumtool -s
```

Gli algoritmi disponibili per il quorum device:

| Algoritmo | Comportamento | Caso d'uso |
|-----------|--------------|------------|
| **ffsplit** (fifty-fifty split) | In caso di split esatto, il voto va alla partizione con più nodi attivi; se pari, alla partizione che aveva il quorum precedente | Cluster a 2 nodi — scenario più comune |
| **lms** (last man standing) | Il voto va all'ultima partizione attiva, permettendo al cluster di funzionare anche con un solo nodo | Cluster con nodi che si spengono frequentemente per manutenzione |

```bash
# Cambiare algoritmo da ffsplit a lms
sudo pcs quorum device update model net algorithm=lms

# Verificare la configurazione attiva
sudo pcs quorum device status --full
```

#### Watchdog e SBD — Self-Fencing Hardware

Il **SBD (Storage-Based Death)** combina un watchdog hardware con un dispositivo di storage condiviso (poison-pill) per garantire il fencing anche quando la rete è completamente isolata:

```bash
# Verificare il supporto watchdog nel kernel
ls -la /dev/watchdog*
sudo modprobe softdog  # watchdog software per test

# Configurare SBD con un disco condiviso (LUN iSCSI o FC)
sudo sbd -d /dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_VBxxxxxxxx create
sudo sbd -d /dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_VBxxxxxxxx dump

# Installare e configurare SBD su tutti i nodi
sudo dnf install sbd
```

Configurazione `/etc/sysconfig/sbd`:

```ini
SBD_DEVICE="/dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_VBxxxxxxxx"
SBD_PACEMAKER=yes
SBD_STARTMODE=always
SBD_DELAY_START=no
SBD_WATCHDOG_DEV=/dev/watchdog
SBD_WATCHDOG_TIMEOUT=5
```

Il meccanismo **poison-pill** funziona così:

1. Ogni nodo scrive periodicamente un messaggio "alive" sul dispositivo SBD condiviso
2. Se un nodo deve essere fenced, il nodo che richiede il fencing scrive un messaggio **"poison-pill"** (veleno) nello slot del nodo target
3. Il nodo target legge il proprio slot, trova il poison-pill, e si **auto-termina** (self-fence)
4. Se il nodo target non riesce a leggere lo slot (perché è già down), il watchdog hardware scade e **resetta il nodo** via hardware

```bash
# Verificare lo stato degli slot SBD
sudo sbd -d /dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_VBxxxxxxxx list

# Testare il messaging SBD (NON in produzione!)
# sudo sbd -d /dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_VBxxxxxxxx message node2 test

# Abilitare SBD come metodo di fencing in Pacemaker
sudo pcs stonith create sbd-fencing fence_sbd \
  devices=/dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_VBxxxxxxxx

# Configurare il timeout del watchdog nel cluster
sudo pcs property set stonith-watchdog-timeout=10s
```

#### Combinazione di Meccanismi Anti-Split-Brain

La strategia più robusta combina più livelli:

```
┌─────────────────────────────────────────┐
│  Livello 1: Quorum + Quorum Device     │  ← decisione logica
│  (ffsplit/lms — chi ha diritto di       │
│   operare)                               │
├─────────────────────────────────────────┤
│  Livello 2: STONITH / Fencing          │  ← eliminazione fisica
│  (IPMI, fence_vmware, fence_aws —      │
│   spegnimento forzato del nodo)         │
├─────────────────────────────────────────┤
│  Livello 3: SBD + Watchdog             │  ← self-fencing garantito
│  (poison-pill + watchdog hardware —    │
│   auto-terminazione)                    │
├─────────────────────────────────────────┤
│  Livello 4: DRBD split-brain handler   │  ← protezione dati
│  (after-sb-0pri, after-sb-1pri —       │
│   cosa fare con i dati divergenti)      │
└─────────────────────────────────────────┘
```

---

## Disaster Recovery vs High Availability

HA e DR sono concetti complementari ma distinti:

| Aspetto | High Availability | Disaster Recovery |
|---------|-------------------|-------------------|
| **Obiettivo** | Continuità operativa durante guasti | Ripristino dopo un disastro |
| **Ambito** | Stesso datacenter / stessa regione | Cross-datacenter / cross-regione |
| **RTO tipico** | Secondi-minuti | Minuti-ore |
| **RPO tipico** | Zero (sincrono) — secondi (asincrono) | Minuti-ore (dipende dai backup) |
| **Automazione** | Failover automatico | Spesso richiede intervento manuale |
| **Costo** | Ridondanza attiva (nodi in standby) | Storage backup + infra DR site |

### RPO e RTO in Dettaglio

```
Timeline di un disastro:

Ultimo backup       Disastro       Inizio ripristino     Servizio ripristinato
     │                  │                 │                       │
     ▼                  ▼                 ▼                       ▼
─────┼──────────────────┼─────────────────┼───────────────────────┼────
     │                  │                 │                       │
     │◄── RPO ─────────►│                 │◄─────── RTO ────────►│
     │  (dati persi)     │                 │  (tempo di downtime)  │

RPO = 0 → replica sincrona (DRBD protocol C, Patroni synchronous_mode)
RPO > 0 → replica asincrona, backup periodici, WAL archiving
RTO = 0 → impossibile; anche il failover automatico ha un tempo non nullo
RTO < 1 min → HA con Pacemaker + STONITH, Patroni con etcd
RTO < 15 min → DR site warm standby, replica asincrona continua
RTO < 4 ore → DR con backup + infrastructure as code
```

### Georedundanza

```
Architettura active-passive cross-datacenter:

  DC Primario (Roma)                     DC Secondario (Milano)
  ┌──────────────────────┐               ┌──────────────────────┐
  │  Cluster HA           │               │  Cluster DR           │
  │  (Pacemaker/Corosync) │               │  (standby)            │
  │                       │               │                       │
  │  ┌─────┐  ┌─────┐    │    Replica     │  ┌─────┐  ┌─────┐    │
  │  │ DB  │  │ App │    │   asincrona   │  │ DB  │  │ App │    │
  │  │ Pri │  │ Act │    │──────────────►│  │ Rep │  │ Std │    │
  │  └─────┘  └─────┘    │   (DRBD-A /   │  └─────┘  └─────┘    │
  │                       │    WAL ship)  │                       │
  └──────────────────────┘               └──────────────────────┘
         │                                        │
         │              DNS failover              │
         │         (TTL basso, GeoDNS)            │
         └─────────────────┬──────────────────────┘
                           │
                      ┌────▼────┐
                      │ Clients │
                      └─────────┘
```

**Active-passive cross-site**: un sito opera, l'altro riceve repliche. Failover manuale o semi-automatico. RPO dipende dal lag di replica.

**Active-active cross-site**: entrambi i siti servono traffico. Richiede routing intelligente (GeoDNS, Anycast), gestione dei conflitti sui dati e latenza inter-site accettabile.

### Procedure di DR

```bash
# Verifica RPO: controllare il lag di replica
# PostgreSQL
sudo -u postgres psql -c \
  "SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes,
          NOW() - replay_lag AS lag_time
   FROM pg_stat_replication;"

# DRBD
sudo drbdsetup status data --statistics | grep "out_of_sync"
# out_of_sync:0 → RPO = 0 (tutto sincronizzato)

# Piano di DR test — da eseguire almeno ogni trimestre:
# 1. Verificare che le repliche siano aggiornate (RPO check)
# 2. Simulare la perdita del DC primario
# 3. Promuovere il DC secondario (failover manuale)
# 4. Verificare che i servizi funzionino (RTO check)
# 5. Ripristinare il DC primario e riconfigurare la replica (failback)
# 6. Documentare tempi effettivi e confrontare con gli obiettivi
```

### Geo-Clustering con Booth

Il **geo-clustering** estende l'HA oltre un singolo datacenter, fornendo failover automatico o semi-automatico tra siti geograficamente distanti. **Booth** è il componente di Pacemaker progettato per questo scopo.

#### Architettura Booth

Booth utilizza un meccanismo a **ticket**: un token logico che determina quale sito ha il diritto di eseguire un determinato servizio. Solo il sito che detiene il ticket può attivare le risorse associate.

```
┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│   Sito A     │     │   Sito B     │     │  Arbitro    │
│ (Primario)   │────│ (Secondario) │────│  (Booth)    │
│              │     │              │     │             │
│ Pacemaker    │     │ Pacemaker    │     │ booth-      │
│ + booth-site │     │ + booth-site │     │ arbitrator  │
│              │     │              │     │             │
│ [TICKET] ✓   │     │ [TICKET] ✗   │     │ [VOTO]     │
└──────────────┘     └──────────────┘     └─────────────┘
```

L'**arbitro** è un nodo leggero (non fa parte di nessun cluster Pacemaker) che partecipa solo al voto per i ticket, evitando situazioni di parità.

#### Configurazione Booth

```bash
# Installare booth su tutti i siti e sull'arbitro
sudo dnf install booth-site     # sui nodi del cluster
sudo dnf install booth-arbitrator  # sul nodo arbitro

# File di configurazione: /etc/booth/booth.conf
```

Contenuto di `/etc/booth/booth.conf` (identico su tutti i nodi):

```ini
# Configurazione Booth per geo-clustering
transport="UDP"
port="9929"

# Siti del cluster
site="192.168.1.10"    # IP del sito A
site="192.168.2.10"    # IP del sito B
arbitrator="10.0.0.50"  # IP dell'arbitro

# Definizione del ticket
ticket="ticket-webservice"
  expire="600"          # scadenza ticket in secondi
  timeout="5"           # timeout comunicazione
  retries="5"           # tentativi di rinnovo
  weights="50,50,0"     # peso voto: sitoA, sitoB, arbitro
  acquire-after="60"    # attesa dopo perdita ticket
  before-acquire-handler="/usr/share/booth/service-check.sh"
```

```bash
# Avviare booth su ogni nodo
sudo systemctl enable --now booth@booth

# Verificare lo stato dei ticket
sudo booth list
sudo booth status

# Concedere manualmente un ticket a un sito
sudo booth client grant -t ticket-webservice -s 192.168.1.10

# Revocare un ticket
sudo booth client revoke -t ticket-webservice -s 192.168.1.10
```

#### Integrazione Booth con Pacemaker

```bash
# Configurare il constraint sul ticket nel cluster Pacemaker
# Solo il sito che detiene il ticket può eseguire la risorsa
sudo pcs constraint ticket add ticket-webservice webserver-group \
  loss-policy=stop

# loss-policy definisce cosa fare quando il ticket viene perso:
# stop    → ferma le risorse (sicuro, default)
# demote  → retrocede a slave (per risorse promotable)
# fence   → fence il nodo (aggressivo)
# freeze  → mantiene le risorse ma non le gestisce (rischioso)
```

#### Failover Geo-Cluster

```bash
# Scenario: failover pianificato dal sito A al sito B
# 1. Verificare lo stato su entrambi i siti
sudo booth list
sudo pcs status

# 2. Revocare il ticket dal sito A
sudo booth client revoke -t ticket-webservice -s 192.168.1.10

# 3. Concedere il ticket al sito B
sudo booth client grant -t ticket-webservice -s 192.168.2.10

# 4. Verificare che le risorse si siano spostate
sudo pcs status  # eseguire sul sito B
```

### DRBD Proxy per Replica WAN

**DRBD Proxy** è un componente aggiuntivo (commerciale, fornito da LINBIT) che rende la replica DRBD praticabile su reti WAN ad alta latenza. Agisce come buffer e compressore tra due nodi DRBD distanti.

#### Problema della Replica Sincrona su WAN

La replica sincrona DRBD (protocollo C) richiede che ogni scrittura sia confermata dal nodo remoto prima di completare l'I/O. Su una WAN con 20 ms di latenza, questo significa che ogni scrittura richiede almeno 40 ms di round-trip, limitando drasticamente il throughput:

```
Throughput massimo ≈ Buffer_Size / RTT

Esempio: buffer 128 KB, RTT 40 ms
  = 128 KB / 0.040 s = 3.2 MB/s  ← inaccettabile per molti workload
```

#### Architettura DRBD Proxy

```
Sito A                          WAN                    Sito B
┌──────┐   ┌───────────┐   ┌─────────┐   ┌───────────┐   ┌──────┐
│ DRBD │──│ DRBD      │──│         │──│ DRBD      │──│ DRBD │
│ Node │   │ Proxy (A) │   │  WAN    │   │ Proxy (B) │   │ Node │
│      │   │           │   │ 20ms+   │   │           │   │      │
│      │   │ Buffer:   │   │ latenza │   │ Buffer:   │   │      │
│      │   │ 2 GB RAM  │   │         │   │ 2 GB RAM  │   │      │
│      │   │ +compress │   │         │   │ +compress │   │      │
└──────┘   └───────────┘   └─────────┘   └───────────┘   └──────┘
```

DRBD Proxy:
- **Bufferizza** le scritture localmente (fino a diversi GB di RAM o disco)
- **Comprime** i dati con zlib o lz4 prima di inviarli sulla WAN
- Permette l'uso del **protocollo A** (asincrono) per massimizzare il throughput
- Segnala al nodo DRBD locale che la scrittura è completata appena il dato è nel buffer

#### Configurazione DRBD Proxy

```bash
# Installazione di DRBD Proxy (richiede licenza LINBIT)
sudo dnf install drbd-proxy

# Configurazione in /etc/drbd.d/data.res
resource data {
    protocol A;           # asincrono per WAN

    proxy {
        memlimit 2G;      # buffer in memoria
        plugin {
            zlib level 6;  # compressione (1-9)
        }
    }

    on site-a {
        address   192.168.1.10:7789;
        proxy on site-a {
            inside  192.168.1.10:7790;
            outside 10.0.0.10:7790;   # IP WAN
        }
        disk /dev/vg0/lv_data;
        meta-disk internal;
    }

    on site-b {
        address   192.168.2.10:7789;
        proxy on site-b {
            inside  192.168.2.10:7790;
            outside 10.0.0.20:7790;   # IP WAN
        }
        disk /dev/vg0/lv_data;
        meta-disk internal;
    }
}
```

```bash
# Avviare DRBD Proxy
sudo systemctl enable --now drbd-proxy

# Monitorare lo stato del proxy
sudo drbd-proxy-ctl -c "show"
sudo drbd-proxy-ctl -c "show memusage"
sudo drbd-proxy-ctl -c "show compression"

# Statistiche di compressione tipiche:
# Compressione ratio: 2.5:1 — 4:1 per dati di database
# Compressione ratio: 1.1:1 — 1.3:1 per dati già compressi (immagini, video)
```

---

## Monitoraggio della Salute del Cluster

### Monitoraggio con Pacemaker

```bash
# Status completo
sudo pcs status --full

# Status in formato XML (per parsing)
sudo crm_mon -1 --output-as xml

# Monitoraggio continuo
sudo crm_mon -rf

# Storia dei failover
sudo pcs resource failcount show

# Verificare la configurazione
sudo pcs config

# Simulare una risorsa per il debugging
sudo crm_simulate -sL
```

### Script di Monitoraggio Automatico

```bash
#!/bin/bash
# /usr/local/bin/cluster-health-check.sh

LOG="/var/log/cluster-health.log"
ALERT_EMAIL="admin@example.com"
HOSTNAME=$(hostname -f)

check_cluster() {
    if ! corosync-quorumtool -s 2>/dev/null | grep -q "Quorate: *Yes"; then
        echo "$(date): CRITICAL — No quorum on $HOSTNAME" >> "$LOG"
        echo "Cluster $HOSTNAME has lost quorum" | mail -s "CLUSTER CRITICAL: No Quorum" "$ALERT_EMAIL"
        return 1
    fi

    FAILED=$(pcs status 2>/dev/null | grep -c "FAILED")
    if [ "$FAILED" -gt 0 ]; then
        echo "$(date): WARNING — $FAILED failed resources on $HOSTNAME" >> "$LOG"
        pcs status | mail -s "CLUSTER WARNING: Failed Resources on $HOSTNAME" "$ALERT_EMAIL"
        return 1
    fi

    OFFLINE=$(pcs status nodes 2>/dev/null | grep -c "Offline")
    if [ "$OFFLINE" -gt 0 ]; then
        echo "$(date): WARNING — $OFFLINE nodes offline in cluster" >> "$LOG"
        pcs status nodes | mail -s "CLUSTER WARNING: Nodes Offline" "$ALERT_EMAIL"
        return 1
    fi

    if command -v drbdadm &>/dev/null; then
        DRBD_STATUS=$(drbdadm status all 2>/dev/null)
        if echo "$DRBD_STATUS" | grep -q "Inconsistent\|StandAlone\|SyncSource\|SyncTarget"; then
            echo "$(date): WARNING — DRBD not fully synchronized" >> "$LOG"
            echo "$DRBD_STATUS" | mail -s "CLUSTER WARNING: DRBD Issue on $HOSTNAME" "$ALERT_EMAIL"
        fi
    fi

    echo "$(date): OK — Cluster healthy on $HOSTNAME" >> "$LOG"
    return 0
}

check_cluster
```

### Integrazione con Prometheus

```yaml
# prometheus.yml - scrape config per HAProxy
scrape_configs:
  - job_name: 'haproxy'
    static_configs:
      - targets: ['10.0.0.1:8404', '10.0.0.2:8404']
    metrics_path: /stats
    params:
      stats: ['csv']

  - job_name: 'pacemaker'
    static_configs:
      - targets: ['10.0.0.1:9664', '10.0.0.2:9664', '10.0.0.3:9664']

  - job_name: 'drbd'
    static_configs:
      - targets: ['10.0.0.1:9340', '10.0.0.2:9340']
```

Regole di alerting per Alertmanager:

```yaml
# cluster_alerts.yml
groups:
  - name: cluster_health
    rules:
      - alert: ClusterQuorumLost
        expr: ha_cluster_quorate == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Cluster has lost quorum"
          description: "The HA cluster on {{ $labels.instance }} has lost quorum."

      - alert: ClusterResourceFailed
        expr: ha_cluster_resource_status{status="failed"} > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Cluster resource failed"
          description: "Resource {{ $labels.resource }} is in failed state."

      - alert: DRBDOutOfSync
        expr: drbd_connections_state{state!="Connected"} > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "DRBD not connected"
          description: "DRBD resource on {{ $labels.instance }} is not connected."

      - alert: HAProxyBackendDown
        expr: haproxy_backend_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "HAProxy backend {{ $labels.backend }} is down"
```

### Pacemaker Alerts e Notifiche

A partire da Pacemaker 2.0, il sistema di **alert agents** sostituisce i vecchi notification scripts, fornendo un meccanismo strutturato per inviare notifiche quando lo stato del cluster cambia.

#### Variabili di Ambiente CRM_alert_

Quando Pacemaker invoca un alert agent, passa informazioni tramite variabili di ambiente con prefisso `CRM_alert_`:

| Variabile | Descrizione |
|-----------|-------------|
| `CRM_alert_kind` | Tipo di evento: `node`, `fencing`, `resource` |
| `CRM_alert_version` | Versione del formato alert |
| `CRM_alert_recipient` | Destinatario configurato |
| `CRM_alert_node` | Nome del nodo coinvolto |
| `CRM_alert_desc` | Descrizione dell'evento |
| `CRM_alert_status` | Codice di stato numerico |
| `CRM_alert_target_rc` | Return code atteso (per risorse) |
| `CRM_alert_rc` | Return code effettivo (per risorse) |
| `CRM_alert_rsc` | Nome della risorsa (se `kind=resource`) |
| `CRM_alert_task` | Operazione eseguita (start, stop, monitor) |
| `CRM_alert_timestamp` | Timestamp dell'evento (epoch) |

#### Configurazione Alert con PCS

```bash
# Creare un alert agent che invia email
sudo pcs alert create id=alert-email \
  path=/usr/share/pacemaker/alerts/alert_smtp.sh \
  description="Email alert per eventi cluster"

# Aggiungere un destinatario
sudo pcs alert recipient add alert-email \
  value="admin@example.com" \
  id=recipient-admin

# Configurare opzioni dell'alert (variabili meta)
sudo pcs alert update alert-email \
  meta timestamp-format="%Y-%m-%d %H:%M:%S"

# Filtrare solo eventi specifici (es. solo fencing e risorse)
sudo pcs alert create id=alert-slack \
  path=/var/lib/pacemaker/alerts/alert_slack.sh \
  options kind="fencing,resource"

# Listare gli alert configurati
sudo pcs alert config
```

#### Script Alert Personalizzato

```bash
#!/bin/bash
# /var/lib/pacemaker/alerts/alert_webhook.sh
# Alert agent per inviare notifiche a un webhook

WEBHOOK_URL="${CRM_alert_recipient}"

case "${CRM_alert_kind}" in
    node)
        MSG="Nodo ${CRM_alert_node}: ${CRM_alert_desc}"
        SEVERITY="warning"
        ;;
    fencing)
        MSG="FENCING: nodo ${CRM_alert_node} — ${CRM_alert_desc}"
        SEVERITY="critical"
        ;;
    resource)
        MSG="Risorsa ${CRM_alert_rsc} su ${CRM_alert_node}: "
        MSG+="${CRM_alert_task} rc=${CRM_alert_rc} "
        MSG+="(atteso: ${CRM_alert_target_rc})"
        if [ "${CRM_alert_rc}" != "${CRM_alert_target_rc}" ]; then
            SEVERITY="critical"
        else
            SEVERITY="info"
        fi
        ;;
esac

PAYLOAD=$(cat <<EOJSON
{
  "timestamp": "${CRM_alert_timestamp}",
  "severity": "${SEVERITY}",
  "kind": "${CRM_alert_kind}",
  "message": "${MSG}",
  "node": "${CRM_alert_node}"
}
EOJSON
)

curl -s -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" > /dev/null 2>&1
```

```bash
# Installare lo script e configurare l'alert
sudo install -m 0755 alert_webhook.sh /var/lib/pacemaker/alerts/
sudo pcs alert create id=alert-webhook \
  path=/var/lib/pacemaker/alerts/alert_webhook.sh
sudo pcs alert recipient add alert-webhook \
  value="https://hooks.example.com/cluster-alerts"
```

---

## Testing HA — Chaos Engineering e Failover Drills

Il failover non testato è un failover che non funziona. Ogni cluster HA deve avere una procedura di test periodica documentata e automatizzata.

### Failover Drill Manuale

```bash
# 1. Documentare lo stato iniziale
sudo pcs status > /tmp/pre-drill-$(date +%F).txt
sudo drbdadm status all >> /tmp/pre-drill-$(date +%F).txt

# 2. Simulare guasto del nodo primario
# Opzione A: standby (graceful)
sudo pcs node standby $(hostname -f)

# Opzione B: fence reale (aggressivo, test di STONITH)
sudo pcs stonith fence $(hostname -f)

# Opzione C: kill del processo (simula crash applicativo)
sudo pkill -9 pacemaker-controld

# 3. Verificare il failover
watch -n 1 'pcs status'
# Controllare: VIP migrata? Risorse avviate? DRBD promoted?

# 4. Verificare il servizio dal punto di vista del client
curl -sf http://10.0.0.100/health && echo "OK" || echo "FAIL"
psql -h 10.0.0.100 -U postgres -c "SELECT 1;" 2>/dev/null && echo "DB OK"

# 5. Ripristinare il nodo
sudo pcs node unstandby $(hostname -f)

# 6. Documentare i tempi
# - Tempo di rilevamento del guasto
# - Tempo di fencing
# - Tempo di avvio delle risorse sul nodo secondario
# - Tempo totale di indisponibilità del servizio
```

### Split-Brain Simulation

```bash
# Simulare partizione di rete con iptables (ambiente di test)
# Sul nodo A, bloccare il traffico dal nodo B:
sudo iptables -A INPUT -s 10.0.0.2 -j DROP
sudo iptables -A OUTPUT -d 10.0.0.2 -j DROP

# Osservare il comportamento:
# - Il cluster rileva la perdita del nodo B
# - Se il nodo A ha il quorum → continua a operare
# - Se il nodo A NON ha il quorum → ferma le risorse
# - STONITH tenta di fenceare il nodo B

# Verificare:
sudo pcs status
sudo corosync-quorumtool

# Ripristinare:
sudo iptables -D INPUT -s 10.0.0.2 -j DROP
sudo iptables -D OUTPUT -d 10.0.0.2 -j DROP

# Verificare la riunificazione del cluster
sudo pcs status
```

### Chaos Engineering Automatizzato

```bash
#!/bin/bash
# /usr/local/bin/ha-chaos-test.sh — test automatizzato di resilienza
# ESEGUIRE SOLO IN AMBIENTE DI STAGING

set -euo pipefail
LOG="/var/log/ha-chaos-test-$(date +%F_%H%M).log"
VIP="10.0.0.100"
SERVICE_URL="http://${VIP}/health"

log() { echo "$(date '+%Y-%m-%dT%H:%M:%S') $*" | tee -a "$LOG"; }

check_service() {
    if curl -sf --connect-timeout 5 "$SERVICE_URL" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

wait_for_service() {
    local timeout=$1
    local start
    start=$(date +%s)
    while ! check_service; do
        if (( $(date +%s) - start > timeout )); then
            log "FAIL: servizio non disponibile dopo ${timeout}s"
            return 1
        fi
        sleep 1
    done
    local elapsed=$(( $(date +%s) - start ))
    log "OK: servizio ripristinato in ${elapsed}s"
}

# Test 1: Standby del nodo attivo
log "=== TEST 1: Standby nodo attivo ==="
ACTIVE_NODE=$(pcs status | grep "Masters:" | awk '{print $NF}' | tr -d '[]')
log "Nodo attivo: ${ACTIVE_NODE}"
pcs node standby "${ACTIVE_NODE}"
wait_for_service 60
pcs node unstandby "${ACTIVE_NODE}"
sleep 30

# Test 2: Kill del processo applicativo
log "=== TEST 2: Kill processo applicativo ==="
pkill -9 haproxy 2>/dev/null || true
wait_for_service 30
sleep 30

# Test 3: Interfaccia di rete down (5 secondi)
log "=== TEST 3: Network blip 5s ==="
ip link set eth0 down
sleep 5
ip link set eth0 up
wait_for_service 60

log "=== CHAOS TEST COMPLETATO ==="
cat "$LOG"
```

### Checklist Drill Periodico

```
Frequenza consigliata:
- Failover drill manuale: mensile
- Split-brain test:       trimestrale
- DR test cross-site:     trimestrale
- Chaos test automatico:  settimanale (su staging)
- STONITH test:           dopo ogni modifica alla configurazione

Documentazione per ogni drill:
□ Data e ora del test
□ Tipo di test eseguito
□ Stato del cluster prima del test
□ Tempo di rilevamento del guasto
□ Tempo di failover completo
□ Servizio verificato dal punto di vista client
□ Anomalie riscontrate
□ Azioni correttive necessarie
□ Firma del responsabile
```

### Sviluppo Resource Agent OCF

Un **Resource Agent (RA)** OCF è uno script che Pacemaker utilizza per gestire una risorsa. Segue lo standard **Open Cluster Framework** e deve implementare un set obbligatorio di azioni.

#### Azioni Obbligatorie

| Azione | Descrizione | Return code successo |
|--------|-------------|---------------------|
| `start` | Avvia la risorsa | 0 (OCF_SUCCESS) |
| `stop` | Ferma la risorsa | 0 (OCF_SUCCESS) |
| `monitor` | Controlla lo stato | 0 (running), 7 (not running) |
| `meta-data` | Restituisce XML con metadati | 0 |

#### Return Code OCF Standard

| Codice | Nome | Significato |
|--------|------|-------------|
| 0 | OCF_SUCCESS | Operazione riuscita |
| 1 | OCF_ERR_GENERIC | Errore generico |
| 2 | OCF_ERR_ARGS | Argomenti non validi |
| 3 | OCF_ERR_UNIMPLEMENTED | Azione non implementata |
| 4 | OCF_ERR_PERM | Permessi insufficienti |
| 5 | OCF_ERR_INSTALLED | Software non installato |
| 6 | OCF_ERR_CONFIGURED | Configurazione errata |
| 7 | OCF_NOT_RUNNING | Risorsa non in esecuzione |
| 8 | OCF_RUNNING_MASTER | Risorsa in esecuzione come master |
| 9 | OCF_FAILED_MASTER | Risorsa fallita come master |

#### Scheletro di un Resource Agent OCF

```bash
#!/bin/bash
#
# OCF Resource Agent per il servizio "myapp"
# Percorso: /usr/lib/ocf/resource.d/custom/myapp
#

# Caricare le funzioni helper OCF
: ${OCF_FUNCTIONS_DIR=${OCF_ROOT}/lib/heartbeat}
. ${OCF_FUNCTIONS_DIR}/ocf-shellfuncs

# Metadati XML — obbligatori
myapp_meta_data() {
    cat <<EOF
<?xml version="1.0"?>
<!DOCTYPE resource-agent SYSTEM "ra-api-1.dtd">
<resource-agent name="myapp" version="1.0">
  <version>1.0</version>
  <longdesc lang="it">
    Resource Agent per gestire il servizio myapp.
    Controlla il processo, il PID file e la risposta HTTP.
  </longdesc>
  <shortdesc lang="it">Gestisce myapp</shortdesc>

  <parameters>
    <parameter name="config_file" unique="0" required="1">
      <longdesc lang="it">
        Percorso del file di configurazione di myapp
      </longdesc>
      <shortdesc lang="it">File di configurazione</shortdesc>
      <content type="string" default="/etc/myapp/myapp.conf"/>
    </parameter>
    <parameter name="port" unique="0" required="0">
      <longdesc lang="it">Porta HTTP per il health check</longdesc>
      <shortdesc lang="it">Porta HTTP</shortdesc>
      <content type="integer" default="8080"/>
    </parameter>
  </parameters>

  <actions>
    <action name="start"    timeout="30s"/>
    <action name="stop"     timeout="30s"/>
    <action name="monitor"  timeout="20s" interval="10s" depth="0"/>
    <action name="meta-data" timeout="5s"/>
    <action name="validate-all" timeout="10s"/>
  </actions>
</resource-agent>
EOF
}

# Variabili dall'ambiente OCF
MYAPP_CONFIG="${OCF_RESKEY_config_file:-/etc/myapp/myapp.conf}"
MYAPP_PORT="${OCF_RESKEY_port:-8080}"
MYAPP_PIDFILE="/var/run/myapp.pid"

myapp_start() {
    myapp_monitor
    if [ $? -eq $OCF_SUCCESS ]; then
        ocf_log info "myapp già in esecuzione"
        return $OCF_SUCCESS
    fi

    ocf_log info "Avvio di myapp con config ${MYAPP_CONFIG}"
    /usr/bin/myapp --config "${MYAPP_CONFIG}" \
                   --port "${MYAPP_PORT}" \
                   --pidfile "${MYAPP_PIDFILE}" \
                   --daemon

    # Attendere l'avvio (max 10 secondi)
    local count=0
    while [ $count -lt 10 ]; do
        myapp_monitor && return $OCF_SUCCESS
        sleep 1
        count=$((count + 1))
    done

    ocf_exit_reason "myapp non si è avviato entro 10 secondi"
    return $OCF_ERR_GENERIC
}

myapp_stop() {
    myapp_monitor
    if [ $? -eq $OCF_NOT_RUNNING ]; then
        ocf_log info "myapp già fermo"
        return $OCF_SUCCESS
    fi

    if [ -f "${MYAPP_PIDFILE}" ]; then
        local pid=$(cat "${MYAPP_PIDFILE}")
        ocf_log info "Invio SIGTERM a myapp (PID ${pid})"
        kill -TERM "${pid}"

        # Attendere la terminazione (max 15 secondi)
        local count=0
        while [ $count -lt 15 ]; do
            if ! kill -0 "${pid}" 2>/dev/null; then
                rm -f "${MYAPP_PIDFILE}"
                return $OCF_SUCCESS
            fi
            sleep 1
            count=$((count + 1))
        done

        # Forza terminazione
        ocf_log warn "SIGTERM non sufficiente, invio SIGKILL"
        kill -KILL "${pid}"
        rm -f "${MYAPP_PIDFILE}"
    fi

    return $OCF_SUCCESS
}

myapp_monitor() {
    # Controllo 1: PID file esiste e processo attivo
    if [ ! -f "${MYAPP_PIDFILE}" ]; then
        return $OCF_NOT_RUNNING
    fi

    local pid=$(cat "${MYAPP_PIDFILE}")
    if ! kill -0 "${pid}" 2>/dev/null; then
        ocf_log warn "PID file presente ma processo ${pid} non esiste"
        rm -f "${MYAPP_PIDFILE}"
        return $OCF_NOT_RUNNING
    fi

    # Controllo 2: health check HTTP (monitor depth > 0)
    if ocf_is_probe; then
        return $OCF_SUCCESS
    fi

    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://127.0.0.1:${MYAPP_PORT}/health" 2>/dev/null)

    if [ "${http_code}" = "200" ]; then
        return $OCF_SUCCESS
    else
        ocf_exit_reason "Health check fallito: HTTP ${http_code}"
        return $OCF_ERR_GENERIC
    fi
}

myapp_validate() {
    # Verificare che il binario esista
    if [ ! -x /usr/bin/myapp ]; then
        ocf_exit_reason "/usr/bin/myapp non trovato o non eseguibile"
        return $OCF_ERR_INSTALLED
    fi

    # Verificare che il file di configurazione esista
    if [ ! -f "${MYAPP_CONFIG}" ]; then
        ocf_exit_reason "File di configurazione ${MYAPP_CONFIG} non trovato"
        return $OCF_ERR_CONFIGURED
    fi

    return $OCF_SUCCESS
}

# Dispatch delle azioni
case "$1" in
    meta-data)      myapp_meta_data; exit $OCF_SUCCESS ;;
    start)          myapp_start ;;
    stop)           myapp_stop ;;
    monitor)        myapp_monitor ;;
    validate-all)   myapp_validate ;;
    *)              exit $OCF_ERR_UNIMPLEMENTED ;;
esac
exit $?
```

```bash
# Installare e testare il resource agent
sudo install -m 0755 myapp /usr/lib/ocf/resource.d/custom/myapp

# Verificare i metadati
sudo ocf-tester -n test /usr/lib/ocf/resource.d/custom/myapp

# Creare la risorsa nel cluster
sudo pcs resource create myapp ocf:custom:myapp \
  config_file=/etc/myapp/prod.conf \
  port=8080 \
  op monitor interval=10s timeout=20s \
  op start timeout=30s \
  op stop timeout=30s
```

### Procedure di Manutenzione del Cluster

La manutenzione di un cluster HA richiede procedure specifiche per evitare failover non pianificati e interruzioni di servizio.

#### Standby di un Nodo

Lo standby sposta tutte le risorse dal nodo senza rimuoverlo dal cluster:

```bash
# Mettere un nodo in standby (le risorse migrano)
sudo pcs node standby node2

# Verificare che le risorse si siano spostate
sudo pcs status

# Eseguire la manutenzione (aggiornamenti, riavvio, ecc.)
sudo dnf update -y
sudo reboot

# Riportare il nodo online dopo la manutenzione
sudo pcs node unstandby node2

# Verificare che il nodo sia tornato attivo
sudo pcs status
```

#### Migrazione delle Risorse

```bash
# Spostare una risorsa specifica su un altro nodo
# pcs resource move crea un constraint di location temporaneo
sudo pcs resource move webserver node1

# ATTENZIONE: il constraint rimane attivo dopo il move!
# Rimuoverlo manualmente dopo la manutenzione:
sudo pcs resource clear webserver

# Alternativa: pcs resource relocate (Pacemaker 2.1+)
# Sposta e rimuove automaticamente il constraint
sudo pcs resource relocate run webserver

# Verificare che non ci siano constraint residui
sudo pcs constraint location show
```

**Differenza critica**: `pcs resource move` vs `pcs resource relocate`:

| Comando | Constraint | Rischio |
|---------|-----------|---------|
| `pcs resource move` | Crea constraint permanente | La risorsa non torna al nodo originale dopo unstandby |
| `pcs resource relocate run` | Constraint temporaneo, rimosso automaticamente | Sicuro per manutenzione |
| `pcs resource clear` | Rimuove constraint creati da `move` | Necessario dopo ogni `move` |

#### Rolling Upgrade del Cluster

Procedura per aggiornare il software del cluster senza interruzione del servizio:

```bash
# 1. Verificare lo stato iniziale
sudo pcs status
sudo pcs property show dc-version

# 2. Mettere il primo nodo in standby
sudo pcs node standby node1

# 3. Aggiornare Pacemaker/Corosync sul nodo in standby
sudo dnf update pacemaker corosync pcs -y

# 4. Riavviare i servizi del cluster
sudo systemctl restart corosync pacemaker

# 5. Riportare il nodo online
sudo pcs node unstandby node1

# 6. Verificare la convergenza
sudo pcs status
sudo crm_verify -L -V  # verifica CIB

# 7. Ripetere per ogni nodo successivo
sudo pcs node standby node2
# ... stessi passaggi ...
sudo pcs node unstandby node2

# 8. Verificare che tutti i nodi abbiano la stessa versione
sudo pcs property show dc-version
```

#### Maintenance Mode del Cluster

```bash
# Maintenance mode su tutto il cluster
# Pacemaker smette di monitorare e gestire TUTTE le risorse
sudo pcs property set maintenance-mode=true

# Maintenance mode su una singola risorsa
sudo pcs resource update webserver meta maintenance=true

# Verificare lo stato di maintenance
sudo pcs status  # mostra "(maintenance)" accanto alle risorse

# Uscire dal maintenance mode
sudo pcs property set maintenance-mode=false
sudo pcs resource update webserver meta maintenance=false

# ATTENZIONE: in maintenance mode, Pacemaker NON esegue failover.
# Usare solo per interventi pianificati e brevi.
```

---

## Best Practices

### Progettazione del Cluster

1. **Numero dispari di nodi** (3, 5, 7) per il quorum — o usare un quorum device per cluster a 2 nodi
2. **Rete dedicata per il heartbeat**: VLAN separata, niente routing complesso, latenza minima
3. **STONITH sempre attivo in produzione**: senza fencing, il cluster non è HA, è un rischio
4. **Testare regolarmente il failover**: il failover non testato è un failover che non funziona
5. **Resource stickiness**: impostare un valore positivo per evitare failback non necessari
6. **Documentare la topologia**: chi fa cosa, dove sono le VIP, quali risorse sono in quale gruppo

### HAProxy

1. **Health check attivi**: non affidarsi solo alla connessione TCP, verificare l'endpoint applicativo
2. **Graceful drain**: mettere i server in `drain` prima della manutenzione per completare le richieste in corso
3. **Rate limiting**: proteggere i backend da sovraccarico e DDoS
4. **Log dettagliati**: abilitare httplog con request ID per il troubleshooting
5. **Reload senza downtime**: usare `systemctl reload` che esegue un hitless reload

### DRBD

1. **Usare protocollo C** per zero data loss (sincrono)
2. **Rete dedicata per la replica**: non mischiare traffico DRBD con il traffico applicativo
3. **Monitorare il resync**: un resync lento può indicare problemi di rete o disco
4. **Testare il recovery da split-brain** in ambiente di staging

### Generale

1. **Automatizzare tutto**: deployment, configurazione, test di failover
2. **Monitorare tutto**: quorum, stato risorse, performance DRBD, backend HAProxy
3. **Documentare le procedure**: runbook per failover manuale, recovery da split-brain, sostituzione nodo
4. **Piano di disaster recovery**: il cluster HA protegge da guasti locali, non da disastri (serve anche il backup)

---

## Troubleshooting

### Pacemaker — Problemi Comuni

```bash
# Problema: risorsa non si avvia
# 1. Controllare i log
sudo journalctl -u pacemaker -n 100
sudo pcs resource debug-start <resource_name>

# 2. Controllare i failcount
sudo pcs resource failcount show <resource_name>

# 3. Pulire gli errori
sudo pcs resource cleanup <resource_name>

# 4. Verificare i vincoli
sudo pcs constraint show --full

# 5. Simulare la configurazione
sudo crm_simulate -sL

# Problema: nodo non si unisce al cluster
# 1. Verificare corosync
sudo corosync-cfgtool -s

# 2. Verificare autenticazione
sudo pcs host auth <node> -u hacluster -p <password>

# 3. Verificare l'orologio (NTP)
timedatectl status
chronyc tracking

# Problema: risorse che fanno "ping-pong" tra nodi
sudo pcs resource defaults update resource-stickiness=200
sudo pcs resource defaults update migration-threshold=5
```

### HAProxy — Problemi Comuni

```bash
# Problema: 503 Service Unavailable
# 1. Verificare lo stato dei backend
echo "show servers state" | sudo socat stdio /var/lib/haproxy/stats

# 2. Verificare la raggiungibilità dei backend
curl -v http://10.0.0.11:8080/health

# 3. Controllare i log
sudo journalctl -u haproxy -f

# Problema: connessioni lente
# 1. Verificare le statistiche
curl -s http://admin:StatsPassword123!@localhost:8404/stats\;csv | column -ts,
```

### DRBD — Problemi Comuni

```bash
# Problema: DRBD in stato StandAlone
sudo drbdadm status data
sudo drbdadm connect data

# Problema: split-brain
# 1. Decidere quale nodo ha i dati corretti
# 2. Sul nodo da scartare:
sudo drbdadm disconnect data
sudo drbdadm secondary data
sudo drbdadm -- --discard-my-data connect data
# 3. Sul nodo da mantenere:
sudo drbdadm disconnect data
sudo drbdadm connect data

# Problema: resync lento
sudo drbdadm disk-options --resync-rate=200M data

# Problema: WFConnection (Waiting For Connection)
sudo ss -tlnp | grep 7789
nc -zv 10.0.1.2 7789
```

### Tabella Troubleshooting Rapida

| # | Sintomo | Causa probabile | Soluzione |
|---|---------|-----------------|-----------|
| 1 | `pcs status` mostra "OFFLINE" per un nodo | Corosync non raggiungibile, firewall, NIC down | Verificare `corosync-cfgtool -s`, firewall (`firewall-cmd --list-all`), cavi di rete |
| 2 | Risorsa in stato "Stopped" senza errori | Vincolo location che impedisce l'avvio, nessun nodo valido | `pcs constraint show --full`, verificare score e location |
| 3 | Risorsa in "FAILED" con failcount > 0 | Il resource agent ha ritornato un errore | `pcs resource cleanup <res>`, poi `journalctl -u pacemaker -n 200` |
| 4 | Risorse che fanno "ping-pong" tra nodi | resource-stickiness troppo bassa o =0 | `pcs resource defaults update resource-stickiness=200` |
| 5 | STONITH fallisce: "Unable to fence" | Credenziali IPMI errate, rete di management non raggiungibile | `pcs stonith config <name>`, testare manualmente con `ipmitool` |
| 6 | "No quorum" su cluster a 2 nodi | Un nodo down, no quorum device configurato | Aggiungere quorum device (`pcs quorum device add`) o usare `two_node: 1` |
| 7 | DRBD in stato "StandAlone" | Peer non raggiungibile, configurazione non corrispondente | `drbdadm connect <res>`, verificare `/etc/drbd.d/*.res` su entrambi i nodi |
| 8 | DRBD split-brain: "Split-Brain detected" | Entrambi i nodi erano Primary, dati divergenti | Decidere il "vincitore", `--discard-my-data` sul "perdente" |
| 9 | DRBD resync estremamente lento | Rate limitato, I/O contention, rete satura | Aumentare `resync-rate`, verificare `iotop`/`iftop` |
| 10 | Keepalived non assegna la VIP | ip_nonlocal_bind non attivo, VRRP bloccato dal firewall | `sysctl net.ipv4.ip_nonlocal_bind`, permettere protocollo IP 112 |
| 11 | HAProxy ritorna 503 su tutti i backend | Tutti i server falliscono l'health check | Verificare raggiungibilità backend: `curl http://backend:port/health` |
| 12 | HAProxy "Connection refused" su porta 443 | Certificato SSL mancante o malformato | `haproxy -c -f /etc/haproxy/haproxy.cfg`, verificare path del .pem |
| 13 | Cluster non si forma dopo il reboot | pcsd/corosync non abilitati all'avvio | `systemctl enable pcsd corosync pacemaker` |
| 14 | Errore "CIB syntax error" dopo modifica manuale | XML del CIB corrotto | `pcs cluster cib-push --config backup.xml` dal backup, evitare edit manuali del CIB |
| 15 | Nodo re-aggiunto non riceve le risorse | Nodo in standby o fenced, risorse preferiscono l'altro nodo | `pcs node unstandby <node>`, `pcs resource cleanup`, verificare stickiness |
| 16 | SBD watchdog non scatta: "watchdog timeout missed" | Modulo watchdog non caricato, `/dev/watchdog` assente | `modprobe softdog`, verificare `ls /dev/watchdog*` |
| 17 | GlusterFS mount fallisce con "Transport endpoint not connected" | Brick offline, volume non avviato | `gluster volume status`, `gluster volume start <vol>` |
| 18 | Patroni non elegge un nuovo primary | etcd non raggiungibile, lock non acquisibile | Verificare `etcdctl endpoint health`, logs Patroni |

---

## Esercizi Pratici

### Esercizio 1 — Cluster Pacemaker/Corosync a 2 Nodi

Obiettivo: configurare un cluster HA a 2 nodi con VIP, STONITH e una risorsa applicativa.

```
Requisiti:
- 2 VM Linux (RHEL/Rocky/AlmaLinux 9 o Debian 12)
- 1 VM leggera per quorum device
- Rete dedicata per heartbeat (interfaccia separata)
- Accesso root su tutti i nodi

Procedura:
1. Installare pacemaker, corosync, pcs su entrambi i nodi
2. Configurare pcsd e autenticare i nodi
3. Creare il cluster con pcs cluster setup
4. Configurare STONITH con fence_virsh o SBD
5. Creare le risorse:
   a. VIP (ocf:heartbeat:IPaddr2) su 10.0.0.100
   b. Servizio nginx (systemd:nginx)
   c. Resource group contenente VIP + nginx
6. Configurare il quorum device sulla terza VM
7. Testare il failover con pcs node standby
8. Verificare il servizio dal punto di vista client (curl http://10.0.0.100)
9. Testare il failback: unstandby del nodo originale
10. Verificare che resource-stickiness impedisca il ping-pong

Criterio di successo: failover completo in meno di 30 secondi
con servizio raggiungibile sulla VIP
```

### Esercizio 2 — DRBD + Pacemaker per Storage Replicato

Obiettivo: implementare storage replicato sincrono con failover automatico.

```
Requisiti:
- Cluster a 2 nodi dall'Esercizio 1
- Un disco aggiuntivo per nodo (/dev/vdb, almeno 5GB)
- DRBD installato su entrambi

Procedura:
1. Configurare la risorsa DRBD in /etc/drbd.d/data.res
2. Creare i metadata e avviare la sincronizzazione iniziale
3. Verificare stato: drbdadm status data → UpToDate/UpToDate
4. Creare il filesystem ext4 su /dev/drbd0
5. Integrare con Pacemaker:
   a. Risorsa DRBD promotable
   b. Risorsa Filesystem
   c. Vincolo colocation: filesystem solo dove DRBD è Master
   d. Vincolo order: promote DRBD → start filesystem
6. Testare: scrivere file su /mnt/data, standby del nodo primario
7. Verificare: il file esiste sul nodo promosso?
8. Testare split-brain recovery:
   a. Bloccare la rete tra i nodi (iptables)
   b. Scrivere dati diversi su entrambi
   c. Ripristinare la rete
   d. Risolvere il split-brain manualmente

Criterio di successo: dati persistenti dopo failover,
split-brain risolto senza perdita dei dati corretti
```

### Esercizio 3 — HAProxy + Keepalived per Web Application HA

Obiettivo: implementare load balancing con failover del load balancer stesso.

```
Requisiti:
- 2 nodi per HAProxy + Keepalived
- 3 backend web server con /health endpoint
- Servizio web di test (nginx con pagina statica)

Procedura:
1. Configurare Keepalived su entrambi i nodi HAProxy:
   a. VIP: 10.0.0.100
   b. Health check per HAProxy (vrrp_script chk_haproxy)
   c. nopreempt abilitato
   d. Unicast peers (no multicast)
2. Configurare HAProxy:
   a. Frontend HTTPS con redirect da HTTP
   b. Backend con 3 server e health check GET /health
   c. Sticky sessions con cookie
   d. Rate limiting (max 100 req/10s per IP)
   e. Pagina statistiche su :8404
3. Testare:
   a. Verificare distribuzione del carico (curl in loop)
   b. Fermare un backend → verificare che HAProxy lo rimuova
   c. Fermare HAProxy su un nodo → VIP migra?
   d. Verificare rate limiting (ab -n 200 -c 10 http://10.0.0.100/)
4. Monitorare con la pagina statistiche

Criterio di successo: zero downtime durante failover HAProxy,
backend unhealthy rimosso in <15 secondi
```

### Esercizio 4 — Disaster Recovery Drill Completo

Obiettivo: pianificare e eseguire un DR drill con documentazione dei tempi.

```
Requisiti:
- Cluster HA funzionante (dagli esercizi precedenti)
- Accesso a un "sito DR" (può essere un'altra rete/VLAN)
- Replica asincrona configurata (DRBD protocol A o pg_basebackup)

Procedura:
1. Documentare lo stato iniziale:
   a. pcs status completo
   b. drbdadm status
   c. Ultimo backup verificato
2. Misurare l'RPO effettivo:
   a. Scrivere un record di test con timestamp
   b. Verificare quando appare sul sito DR
   c. Calcolare il lag
3. Simulare la perdita del sito primario:
   a. Spegnere tutti i nodi del sito primario
   b. Cronometrare l'inizio del downtime
4. Eseguire il failover sul sito DR:
   a. Promuovere DRBD/database
   b. Avviare i servizi
   c. Aggiornare il DNS/VIP
   d. Cronometrare il ripristino del servizio
5. Calcolare:
   a. RPO effettivo (dati persi)
   b. RTO effettivo (tempo di downtime)
6. Eseguire il failback:
   a. Ripristinare il sito primario
   b. Riconfigurare la replica
   c. Resincronizzare
   d. Ritornare al sito primario

Criterio di successo: RPO < 5 minuti, RTO < 15 minuti,
procedura documentata e ripetibile
```

---

## Auto-valutazione

### Domanda 1
Perché il fencing (STONITH) è obbligatorio in un cluster di produzione e cosa succede senza?

<details>
<summary>Risposta</summary>

Senza fencing, un nodo che sembra morto (ma è solo lento o con problemi di rete) potrebbe continuare a scrivere su storage condiviso mentre il cluster avvia lo stesso servizio su un altro nodo. Questo causa corruzione dei dati (due writer sullo stesso filesystem/database).

Il fencing garantisce che il nodo guasto sia fisicamente spento (power fence) o isolato (storage fence) PRIMA di avviare il servizio su un altro nodo. Senza STONITH abilitato, Pacemaker rifiuta di eseguire il recovery di risorse che richiedono fencing (come i filesystem su storage condiviso).

Riferimento: ClusterLabs, "Fencing and STONITH" — clusterlabs.org/pacemaker/doc. Consultato: 2026-05-23.
</details>

### Domanda 2
Qual è la differenza tra i protocolli DRBD A, B e C, e quando usare ciascuno?

<details>
<summary>Risposta</summary>

- **Protocollo A** (asincrono): la scrittura è confermata appena il dato entra nel buffer TCP locale. Il dato potrebbe non essere ancora arrivato al peer. RPO > 0 (possibile perdita dati). Usare per replica cross-datacenter con alta latenza.

- **Protocollo B** (semi-sincrono): la scrittura è confermata quando il dato raggiunge il buffer di rete del peer remoto, ma non è ancora su disco. Quasi zero perdita. Usare quando serve un compromesso tra performance e sicurezza.

- **Protocollo C** (sincrono): la scrittura è confermata SOLO quando il dato è scritto su disco sul peer remoto. RPO = 0 (zero data loss). Usare per database e qualsiasi carico di lavoro dove la perdita di dati è inaccettabile. Richiede bassa latenza tra i nodi (<5ms).

Riferimento: LINBIT DRBD User's Guide, "Replication Modes" — docs.linbit.com. Consultato: 2026-05-23.
</details>

### Domanda 3
In un cluster a 2 nodi, come si risolve il problema del quorum e perché serve un quorum device?

<details>
<summary>Risposta</summary>

Un cluster a 2 nodi ha un problema intrinseco: se un nodo cade, l'altro ha 1 voto su 2, che non è una maggioranza. Senza quorum, il nodo superstite non può operare in sicurezza perché non sa se l'altro è realmente morto o se c'è una partizione di rete.

Soluzioni:

1. **Quorum device (qdevice)**: una terza macchina leggera che funge da votante aggiuntivo. Con qdevice, il cluster ha 3 voti: se un nodo cade, l'altro + qdevice = 2/3 = quorum. Si configura con `pcs quorum device add model net host=qdevice.example.com algorithm=ffsplit`.

2. **two_node: 1 + wait_for_all: 1**: opzione in corosync.conf che abilita il quorum con un solo nodo, ma richiede che entrambi i nodi siano presenti all'avvio iniziale. Meno sicuro del qdevice.

3. **no-quorum-policy=ignore**: pericoloso, entrambe le partizioni continuano a operare. Usare SOLO in combinazione con fencing affidabile.

Riferimento: Corosync votequorum documentation — corosync.github.io. Consultato: 2026-05-23.
</details>

### Domanda 4
Come funziona VRRP e qual è la sequenza di elezione del master in Keepalived?

<details>
<summary>Risposta</summary>

VRRP (RFC 5798) funziona con advertisement periodici:

1. Il nodo MASTER invia pacchetti VRRP multicast (224.0.0.18, protocollo IP 112) ogni `advert_int` secondi (default: 1s).
2. I nodi BACKUP ascoltano. Se non ricevono un advertisement per `3 * advert_int + skew_time` secondi, dichiarano il master morto.
3. Il skew_time = (256 - priority) / 256 secondi. Priorità più alta = skew più basso = transizione più rapida.
4. Il nodo BACKUP con priorità più alta diventa il nuovo MASTER e invia un Gratuitous ARP per aggiornare le tabelle ARP degli switch/router.

Con `nopreempt`, un nodo con priorità più alta non riprende il ruolo MASTER quando torna online. Senza `nopreempt` (default), il nodo con priorità superiore fa preemption e diventa MASTER.

Riferimento: RFC 5798 — "Virtual Router Redundancy Protocol (VRRP) Version 3 for IPv4 and IPv6". Consultato: 2026-05-23.
</details>

### Domanda 5
Cosa sono i vincoli location, colocation e order in Pacemaker, e quando usare ciascuno?

<details>
<summary>Risposta</summary>

- **Location constraints**: controllano su QUALI NODI una risorsa può girare. Usano score per esprimere preferenze (INFINITY = obbligatorio, valori positivi = preferenza, negativi = avversione). Esempio: `pcs constraint location webserver prefers node1=100` — preferisce node1 ma non è obbligatorio.

- **Colocation constraints**: definiscono che due risorse devono (o non devono) stare sullo STESSO NODO. Score INFINITY = sempre insieme, -INFINITY = mai insieme. Esempio: `pcs constraint colocation add vip with webserver INFINITY` — la VIP sta sempre sullo stesso nodo del webserver.

- **Order constraints**: definiscono la SEQUENZA di avvio/stop tra risorse. Esempio: `pcs constraint order start vip then start webserver` — la VIP deve essere attiva prima del webserver. `kind=Optional` rende l'ordine preferenziale ma non obbligatorio.

Nella pratica, i resource group sono spesso sufficienti: le risorse in un gruppo hanno implicitamente colocation INFINITY e ordine sequenziale.

Riferimento: ClusterLabs, "Pacemaker Explained" — clusterlabs.org/pacemaker/doc. Consultato: 2026-05-23.
</details>

### Domanda 6
Qual è la differenza tra active/passive e active/active HA, e quali sono i trade-off?

<details>
<summary>Risposta</summary>

**Active/Passive**:
- Un nodo attivo serve il traffico, gli altri sono in standby
- Il failover trasferisce tutte le risorse al nodo standby
- Vantaggi: semplice, nessun conflitto di risorse, prevedibile
- Svantaggi: il nodo standby non lavora (spreco), failover non istantaneo
- Uso tipico: database, servizi stateful, cluster Pacemaker standard

**Active/Active**:
- Tutti i nodi servono traffico simultaneamente
- Se un nodo cade, il carico viene redistribuito tra i superstiti
- Vantaggi: utilizzo completo delle risorse, scalabilità orizzontale, failover più rapido
- Svantaggi: complessità nella gestione dello stato condiviso, necessità di session affinity o shared storage, rischio di conflitti di scrittura
- Uso tipico: web server stateless dietro load balancer, CDN, read replicas

Per i database, il pattern più comune è active/passive per le scritture e active/active per le letture (read replicas).

Riferimento: "Designing Data-Intensive Applications" (Kleppmann, O'Reilly). Consultato: 2026-05-23.
</details>

### Domanda 7
Come si configura un resource group in Pacemaker e quali sono le implicazioni?

<details>
<summary>Risposta</summary>

Un resource group in Pacemaker è un contenitore ordinato di risorse:

```bash
pcs resource group add web-group vip webserver filesystem
```

Implicazioni:
1. **Colocation implicita**: tutte le risorse del gruppo stanno sullo stesso nodo (INFINITY)
2. **Ordine implicito**: le risorse si avviano nell'ordine elencato (vip → webserver → filesystem)
3. **Stop in ordine inverso**: filesystem → webserver → vip
4. **Failover atomico**: se una risorsa critica del gruppo fallisce, l'intero gruppo migra
5. **Un solo nodo**: il gruppo intero gira su un solo nodo alla volta

I gruppi sono un'astrazione comoda che sostituisce la creazione esplicita di vincoli colocation + order. L'ordine di inserimento nella definizione determina la sequenza di avvio.

Per risorse che devono girare su tutti i nodi (es. monitoring agent), usare cloni, non gruppi.

Riferimento: ClusterLabs, "Pacemaker Explained", sezione "Groups" — clusterlabs.org/pacemaker/doc. Consultato: 2026-05-23.
</details>

### Domanda 8
Qual è il ruolo del CAP theorem nella progettazione di un cluster HA e come influenza le scelte?

<details>
<summary>Risposta</summary>

Il teorema CAP (Brewer, 2000) afferma che un sistema distribuito può garantire al massimo due delle tre proprietà: Consistency, Availability, Partition tolerance.

Poiché le partizioni di rete sono inevitabili nei sistemi distribuiti (P è un requisito implicito), la scelta reale è tra:

- **CP**: il cluster sacrifica la disponibilità per mantenere la coerenza. Esempio: Pacemaker con quorum — la partizione minoritaria ferma le risorse (no-quorum-policy=stop). I dati restano coerenti, ma metà del cluster è indisponibile.

- **AP**: il cluster sacrifica la coerenza per mantenere la disponibilità. Esempio: cluster web stateless senza stato condiviso — entrambe le partizioni continuano a servire, ma se c'è stato condiviso (database), rischio di conflitti.

Un cluster Pacemaker ben configurato è **CP**: il quorum e il fencing garantiscono che solo una partizione operi, proteggendo i dati. Per servizi stateless (web server senza sessioni), si può accettare AP con Keepalived su entrambi i lati + split-brain merge post-recovery.

Riferimento: Brewer, "CAP Twelve Years Later: How the Rules Have Changed", IEEE Computer, 2012. Consultato: 2026-05-23.
</details>

### Domanda 9
Come si integra Patroni con HAProxy per il routing automatico delle connessioni R/W e R/O a PostgreSQL?

<details>
<summary>Risposta</summary>

Patroni espone una REST API su ogni nodo (default porta 8008) che ritorna lo stato del nodo:

- `GET /primary` → 200 se il nodo è il primary, 503 altrimenti
- `GET /replica` → 200 se il nodo è una replica healthy, 503 altrimenti
- `GET /health` → 200 se il nodo è healthy (primary o replica)

HAProxy utilizza queste API come health check:

```
listen pgsql-primary
    bind *:5432
    mode tcp
    option httpchk GET /primary
    http-check expect status 200
    server pg1 10.0.0.11:5432 check port 8008
    server pg2 10.0.0.12:5432 check port 8008

listen pgsql-replica
    bind *:5433
    mode tcp
    option httpchk GET /replica
    http-check expect status 200
    server pg1 10.0.0.11:5432 check port 8008
    server pg2 10.0.0.12:5432 check port 8008
```

Le applicazioni si connettono a `haproxy:5432` per le scritture e a `haproxy:5433` per le letture. Quando Patroni esegue un failover, la REST API si aggiorna automaticamente e HAProxy instrada il traffico verso il nuovo primary.

Riferimento: Patroni documentation — patroni.readthedocs.io, sezione "REST API". Consultato: 2026-05-23.
</details>

### Domanda 10
Cos'è il SBD (Storage-Based Death) e quando si usa al posto del fencing IPMI?

<details>
<summary>Risposta</summary>

SBD è un meccanismo di fencing per ambienti dove il fencing hardware (IPMI, iLO, DRAC) non è disponibile (es. VM senza accesso all'hypervisor, bare metal senza BMC).

Funzionamento:
1. Un piccolo disco condiviso (SAN, iSCSI, FC) contiene un "slot" per ogni nodo
2. Ogni nodo scrive periodicamente un messaggio "alive" nel suo slot (heartbeat via disco)
3. Per fenceare un nodo, il cluster scrive un messaggio "poison pill" nello slot del nodo target
4. Il nodo target legge la poison pill e si auto-spegne tramite watchdog hardware

Requisiti:
- Disco condiviso accessibile da tutti i nodi (almeno 1MB)
- Watchdog hardware configurato (`/dev/watchdog`)
- Modulo `softdog` o watchdog hardware supportato

SBD si usa quando:
- VM su hypervisor senza fence agent (es. KVM senza libvirt access)
- Bare metal senza IPMI/iLO/DRAC
- Ambienti cloud senza fence agent specifico
- Come fencing secondario (backup) in aggiunta a IPMI

Riferimento: ClusterLabs, "SBD — Storage-Based Death" — github.com/ClusterLabs/sbd. Consultato: 2026-05-23.
</details>

---

## Letture Primarie

| Risorsa | Tipo | Rilevanza |
|---------|------|-----------|
| ClusterLabs — Pacemaker Explained | Documentazione | Guida ufficiale completa per Pacemaker: risorse, vincoli, fencing |
| Corosync Cluster Engine documentation | Documentazione | Protocollo Totem, knet, configurazione, quorum |
| LINBIT DRBD User's Guide 9.x | Documentazione | Architettura DRBD, protocolli di replica, performance tuning |
| HAProxy Configuration Manual 2.9 | Documentazione | Configurazione completa HAProxy: frontend, backend, ACL, SSL |
| Keepalived User Guide | Documentazione | VRRP internals, health check, configurazione avanzata |
| RFC 5798 — VRRP Version 3 | RFC | Specifica del protocollo VRRP per IPv4 e IPv6 |
| RFC 5880 — Bidirectional Forwarding Detection | RFC | Specifica BFD per rilevamento rapido guasti di rete |
| "Designing Data-Intensive Applications" (Kleppmann, O'Reilly) | Libro | CAP theorem, consenso distribuito, replica, partition tolerance |
| Patroni documentation | Documentazione | PostgreSQL HA con leader election, REST API, switchover/failover |
| Red Hat HA Add-On Administration Guide (RHEL 9) | Guida | Configurazione cluster HA enterprise con pcs, fencing, GFS2 |
| SUSE HA Administration Guide | Guida | Cluster HA con Pacemaker/Corosync in ambiente SUSE, SBD, DRBD |
| Ceph Documentation — Architecture | Documentazione | RADOS, CRUSH algorithm, OSD, MON, CephFS, RBD |

> Tutte le risorse consultate il 2026-05-23.

---

## Collegamenti Incrociati

- **Modulo 04 — systemd**: prerequisito per la gestione dei servizi e unit file usati dai resource agents
- **Modulo 05 — Networking**: fondamentale per bonding, VLAN dedicate al heartbeat, routing VIP
- **Modulo 06 — Storage**: base per LVM, filesystem, RAID necessari per DRBD e storage condiviso
- **Modulo 11 — Sicurezza**: firewall per le porte del cluster, hardening dei nodi HA
- **Modulo 14 — Containerizzazione**: integrazione container con cluster HA, Docker su DRBD
- **Modulo 20 — Monitoring**: complemento per Prometheus, Grafana e alerting del cluster
- **Modulo 29 — PostgreSQL Amministrazione**: approfondimento streaming replication, pg_basebackup per Patroni
- **Modulo 30 — Prometheus/Grafana Monitoring**: integrazione ha_cluster_exporter, drbd_exporter
- **Modulo 34 — Hardening Sicurezza Avanzata**: hardening dei nodi del cluster, crittografia Corosync

---

## Glossario Locale

| Termine | Definizione |
|---------|-------------|
| **CAP theorem** | Teorema di Brewer: un sistema distribuito garantisce al massimo 2 tra Consistency, Availability, Partition tolerance |
| **CIB** | Cluster Information Base — database XML interno di Pacemaker che descrive configurazione e stato del cluster |
| **Corosync** | Layer di comunicazione e membership del cluster; implementa il protocollo Totem per il consenso |
| **DLM** | Distributed Lock Manager — servizio di locking distribuito per filesystem cluster (GFS2, OCFS2) |
| **DRBD** | Distributed Replicated Block Device — replica a livello di blocco via rete, equivalente a RAID 1 via LAN |
| **GFS2** | Global File System 2 — filesystem cluster-aware che supporta accesso concorrente da più nodi con DLM |
| **knet** | Kronosnet — trasporto moderno di Corosync 3 con supporto per link ridondanti, crittografia e compressione |
| **LACP** | Link Aggregation Control Protocol (IEEE 802.3ad) — aggregazione di link fisici in un unico link logico |
| **BFD** | Bidirectional Forwarding Detection (RFC 5880) — rilevamento rapido guasti di rete (millisecondi) |
| **OCF** | Open Cluster Framework — standard per resource agents Pacemaker; supporta start/stop/monitor/promote |
| **Patroni** | Framework Python per PostgreSQL HA con leader election automatica via etcd/Consul/ZooKeeper |
| **PE** | Policy Engine — componente di Pacemaker che decide dove eseguire le risorse basandosi su vincoli e regole |
| **SBD** | Storage-Based Death — meccanismo di fencing via disco condiviso + watchdog hardware |
| **Totem** | Protocollo di comunicazione di Corosync basato su token ring virtuale con ordinamento totale dei messaggi |
| **Watchdog** | Timer hardware che resetta il sistema se non riceve un heartbeat entro il timeout configurato |
| **Promotable** | Risorsa Pacemaker che può assumere ruoli diversi (Master/Slave) su nodi differenti |
| **Resource stickiness** | Preferenza di Pacemaker a mantenere una risorsa sul nodo corrente per evitare migrazioni inutili |

---

## Riferimenti

- **Pacemaker**: [https://clusterlabs.org/pacemaker/](https://clusterlabs.org/pacemaker/)
- **Corosync**: [https://corosync.github.io/corosync/](https://corosync.github.io/corosync/)
- **pcs**: `man pcs`, `pcs --help`
- **HAProxy**: [https://www.haproxy.org/](https://www.haproxy.org/), [https://docs.haproxy.org/](https://docs.haproxy.org/)
- **DRBD**: [https://linbit.com/drbd/](https://linbit.com/drbd/), [https://docs.linbit.com/](https://docs.linbit.com/)
- **GlusterFS**: [https://docs.gluster.org/](https://docs.gluster.org/)
- **Ceph**: [https://docs.ceph.com/](https://docs.ceph.com/)
- **Keepalived**: [https://www.keepalived.org/](https://www.keepalived.org/)
- **RFC 5798**: VRRP v3 specification
- **Red Hat HA Cluster**: [https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/configuring_and_managing_high_availability_clusters/](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/configuring_and_managing_high_availability_clusters/)
