# Glossario del Corso — Migrazione VMware → Proxmox VE

Glossario consolidato dei termini utilizzati nel corso. Aggregato dai glossari locali di tutti i moduli (`01` → `19`) e dei case study + capstone.

> **Aggiornamento:** 2026-04-27
> **Convenzioni:** termini in **grassetto** quando referenziati in piu moduli; sigle espanse alla prima occorrenza.

---

## A

| Termine | Definizione | Modulo principale |
|---|---|---|
| **ACME** | Automatic Certificate Management Environment (RFC 8555). | 12.1 |
| **Active Directory (AD)** | Directory service Microsoft per identita aziendali. | 09.4, 12.2 |
| **APD (vSphere)** | All-Paths-Down; perdita totale connettivita storage. | 10.3 |
| **APST (NVMe)** | Autonomous Power State Transitions. | 09.3 |
| **ARC (ZFS)** | Adaptive Replacement Cache di ZFS. | 09.3 |
| **AVMA** | Automatic VM Activation; attivazione gratuita per Windows su Hyper-V Datacenter. | 09.4 |

## B

| Termine | Definizione | Modulo principale |
|---|---|---|
| **Backup snapshot** | Backup live tramite snapshot del disco. | 11.1 |
| **balloon driver** | Driver VirtIO per memory ballooning. | 09.4 |
| **BCP** | Business Continuity Plan. | 19 |
| **BGP Anycast** | Stesso IP annunciato da multipli siti. | 19 |
| **BMC** | Baseboard Management Controller (IPMI). | 10.3 |
| **bond LACP (802.3ad)** | Aggregazione link Ethernet con LACP. | 09.3 |
| **break-glass account** | Account locale di emergenza per recovery. | 12.2 |
| **BSOD 0x7B** | Bug check Windows: kernel non puo accedere al disco di boot. | 09.4, 17.2 |

## C

| Termine | Definizione | Modulo principale |
|---|---|---|
| **CA interna** | Certificate Authority ospitata internamente. | 12.1 |
| **`cache=none`** | Modalita disco QEMU/KVM senza host page cache. | 09.2, 09.3 |
| **`cache=writeback`** | Cache async; pericolosa con database. | 09.2, 09.3 |
| **Capacity reserve** | % di capacita lasciata libera per failover. | 10.4 |
| **Capstone** | Progetto pratico finale del corso. | 00-CAPSTONE |
| **Ceph** | Sistema storage distribuito open-source. | 09.3, 19 |
| **Ceph deep-scrub** | Verifica integrita periodica blocchi OSD. | 09.3 |
| **Ceph RBD** | RADOS Block Device. | 09.3 |
| **Ceph RBD mirror** | Replica RBD cross-cluster. | 19 |
| **CIS Benchmark** | Linee guida hardening del Center for Internet Security. | 12.3 |
| **Cloud-init** | Standard de facto per init automatica VM cloud. | 14.1 |
| **Cloud image** | Immagine OS pre-configurata per cloud. | 14.1 |
| **CMDB** | Configuration Management Database. | 13 |
| **`cosign`** | Tool sigstore per firma digitale di artefatti. | 14.1 |
| **`corosync`** | Cluster communication engine; gestisce membership e quorum. | 10.1 |
| **CPU pinning** | Vincolare un processo a uno specifico set di core. | 09.3 |
| **Crash-consistent** | Backup come power loss; FS ok ma app potrebbe inconsistente. | 11.1 |
| **CRM (Cluster Resource Manager)** | Decisore HA centrale. | 10.1 |
| **Cutover** | Operazione di passaggio finale da sistema vecchio a nuovo. | 18 |
| **Cutover Lead** | Owner operativo del cutover. | 18 |

## D

| Termine | Definizione | Modulo principale |
|---|---|---|
| **DAVG/cmd (esxtop)** | Latenza media del dispositivo fisico VMware. | 09.3 |
| **DC (Domain Controller)** | Server AD per autenticazione Windows. | 09.4 |
| **`dcdiag`** | Tool Microsoft per diagnosi salute Domain Controller. | 09.4 |
| **Decommissioning** | Spegnimento sistema vecchio. | 18 |
| **Deduplica chunk-level** | Stesso chunk salvato una sola volta. | 11.2 |
| **Defense in depth** | Architettura security multi-layer. | 12.3 |
| **DNS-01 challenge** | ACME validazione via TXT record DNS. | 12.1 |
| **DORA** | EU regulation 2022/2554 su IT resilience finanziario. | 19 |
| **DPIA** | Data Protection Impact Assessment (GDPR Art. 35). | 12.3 |
| **DR (Disaster Recovery)** | Recovery operations dopo perdita totale di un sito. | 19 |
| **DRS (vSphere)** | Distributed Resource Scheduler (assente in Proxmox nativo). | 10.4 |

## E

| Termine | Definizione | Modulo principale |
|---|---|---|
| **e1000** | NIC emulata Intel; fallback compatibile universalmente. | 09.4 |
| **EOL** | End-of-Life; data fine supporto vendor. | 09.4 |
| **Encryption keyfile (PBS)** | File chiave AES-256-GCM per encryption client-side. | 11.2 |
| **`enforce_gtid_consistency`** | Vincolo MySQL per GTID-safe statement. | 09.2 |
| **`esxtop`** | Tool ESXi per monitoring real-time. | 09.3 |

## F

| Termine | Definizione | Modulo principale |
|---|---|---|
| **Failback** | Ritorno a Site A dopo recovery. | 19 |
| **Fence loop** | Scenario dove nodi si fence reciprocamente. | 10.3 |
| **`fence-agents`** | Pacchetto Linux con agenti per fence diversi tipi. | 10.3 |
| **Fencing** | Isolamento sicuro di un nodo malfunzionante. | 10.1, 10.3 |
| **fio** | Flexible I/O Tester. | 09.3 |
| **FreeRADIUS** | Open-source RADIUS server; usato per 2FA. | 12.2 |
| **Freeze window** | Periodo di no-changes prima del cutover. | 18 |
| **`fsfreeze` / `fsthaw`** | QEMU Guest Agent: congelare/scongelare FS. | 11.1 |
| **FSMO** | Flexible Single-Master Operations; 5 ruoli AD. | 09.4 |

## G

| Termine | Definizione | Modulo principale |
|---|---|---|
| **GAVG/cmd (esxtop)** | Latenza percepita dal guest VMware. | 09.3 |
| **GC (PBS)** | Garbage Collection per chunk orfani. | 11.2 |
| **GCS (VMware)** | Guest Customization Spec; legacy di cloud-init. | 14.1 |
| **GDPR** | EU regulation 2016/679 protezione dati. | 12.3 |
| **GeoDNS** | DNS routing geo-aware per failover. | 19 |
| **GO/NO-GO** | Decision point con criteri oggettivi. | 18 |
| **Group sync (LDAP/AD)** | Importazione gruppi a Proxmox. | 12.2 |
| **GTID** | Global Transaction Identifier MySQL 8.0+. | 09.2 |

## H

| Termine | Definizione | Modulo principale |
|---|---|---|
| **HA (High Availability)** | Resilienza interna a un singolo sito. | 10.1, 19 |
| **HA Manager** | Componente Proxmox per HA risorse. | 10.1 |
| **Heatmap (Grafana)** | Visualizzazione 2D di metriche nel tempo. | 10.4 |
| **HIPAA** | US legislation per dati sanitari. | 12.3 |
| **Hook script (vzdump)** | Script eseguito da vzdump pre/post backup. | 11.1 |
| **HSTS** | HTTP Strict Transport Security. | 12.1 |
| **HTTP-01 challenge** | ACME validazione via file su porta 80. | 12.1 |
| **Huge pages** | Pagine memoria 2MB; riducono pressure TLB. | 09.2, 09.3 |

## I

| Termine | Definizione | Modulo principale |
|---|---|---|
| **i440FX** | Machine type QEMU legacy con PCI. | 09.4 |
| **Idempotency** | Operazione ripetibile con stesso effetto. | 14.2 |
| **iLO / iDRAC** | Implementazioni IPMI di HP / Dell. | 10.3 |
| **`innodb_buffer_pool_size`** | Cache principale MySQL InnoDB. | 09.2 |
| **`innodb_flush_method`** | Modalita sync/flush MySQL. | 09.2 |
| **Index file (PBS)** | Metadata di un backup snapshot. | 11.2 |
| **InvocationID (AD)** | UUID per istanza NTDS di un DC. | 09.4 |
| **IPMI** | Intelligent Platform Management Interface. | 10.3 |
| **IOPS** | Input/Output Operations Per Second. | 09.3 |
| **iothread** | Thread I/O dedicato per disco virtuale QEMU. | 09.2, 09.3 |
| **iSCSI** | Internet SCSI; storage block protocol. | 09.3 |
| **iTCO_wdt** | Watchdog hardware Intel TCO. | 10.3 |

## J

| Termine | Definizione | Modulo principale |
|---|---|---|
| **Jumbo frames** | Frame Ethernet con MTU 9000. | 09.3 |

## K

| Termine | Definizione | Modulo principale |
|---|---|---|
| **KAVG/cmd (esxtop)** | Latenza aggiunta dal kernel VMware. | 09.3 |
| **Keyless signing** | OIDC-based signing senza chiavi long-lived. | 14.1 |
| **KMS (Microsoft)** | Key Management Service per attivazione volume Windows. | 09.4 |

## L

| Termine | Definizione | Modulo principale |
|---|---|---|
| **LDAP filter** | Query per identificare utenti/gruppi candidati. | 12.2 |
| **LDAPS** | LDAP over TLS (port 636). | 12.2 |
| **Let's Encrypt** | CA gratuita pubblica che usa ACME. | 12.1 |
| **Lingering object (AD)** | Oggetto presente su un DC ma cancellato sugli altri. | 09.4 |
| **Live migration** | Spostamento di una VM running senza interruzione. | 10.2 |
| **LLD (Low-Level Discovery, Zabbix)** | Auto-discovery dinamica. | 13 |
| **Load balancing** | Distribuzione carico tra nodi. | 10.4 |
| **LRM (Local Resource Manager)** | Esecutore HA locale; uno per nodo. | 10.1 |
| **LVM-thin** | Volume manager Linux con thin provisioning. | 09.3 |

## M

| Termine | Definizione | Modulo principale |
|---|---|---|
| **MAK** | Multiple Activation Key Microsoft. | 09.4 |
| **Maintenance window** | Finestra annunciata per operazioni che impattano servizio. | 18 |
| **`migration_max_bandwidth`** | Limite globale bandwidth migrazione. | 10.2 |
| **`migration_type=secure`** | Migrazione cifrata via SSH tunnel. | 10.2 |
| **`migration_type=insecure`** | Migrazione non cifrata; per rete dedicata isolata. | 10.2 |
| **Microsegmentation** | Firewall L4 a livello di singolo guest. | 12.3 |
| **`mysqldump --single-transaction`** | Snapshot consistente per InnoDB. | 09.2 |

## N

| Termine | Definizione | Modulo principale |
|---|---|---|
| **Namespace (PBS)** | Multi-tenancy logica all'interno di un datastore. | 11.2 |
| **NetKVM** | Driver VirtIO Net per Windows. | 09.4 |
| **Network isolation** | Separazione VLAN per ridurre blast radius. | 12.3 |
| **NIS2** | EU directive 2022/2555 su cybersecurity. | 19 |
| **`nofailback`** | Sticky placement; non torna a priorita superiore. | 10.1 |
| **NUMA (Non-Uniform Memory Access)** | Architettura multi-socket. | 09.2, 09.3 |

## O

| Termine | Definizione | Modulo principale |
|---|---|---|
| **OCSP** | Online Certificate Status Protocol. | 12.1 |
| **OCSP stapling** | Server presenta proof di non-revoca con cert. | 12.1 |
| **OIDC** | OpenID Connect; auth standard moderno. | 12.2 |
| **Out-of-band (OOB)** | Canale management indipendente da rete OS. | 10.3 |
| **OVMF / TianoCore** | Firmware UEFI per QEMU. | 09.4 |

## P

| Termine | Definizione | Modulo principale |
|---|---|---|
| **`pam_oath`** | Modulo PAM per OTP TOTP. | 12.2 |
| **Partial-state** | Stato in cui un'operazione e a meta. | 14.2 |
| **Payback period** | Tempo per recuperare l'investimento. | 15 |
| **PBS (Proxmox Backup Server)** | Sistema dedicato per backup Proxmox. | 11.2 |
| **PCI-DSS** | Payment Card Industry Data Security Standard. | 12.3 |
| **PDC Emulator** | Ruolo FSMO; fonte autorevole tempo dominio. | 09.4 |
| **PDL (vSphere)** | Permanent Device Lost. | 10.3 |
| **`pg_basebackup`** | Tool PostgreSQL per copia fisica completa. | 09.2 |
| **`pg_dump -Fc`** | Dump custom binario, restorable in parallelo. | 09.2 |
| **`pg_dumpall`** | Dump logico di tutto un cluster PostgreSQL. | 09.2 |
| **`pg_promote()`** | Funzione PostgreSQL per promote standby. | 09.2 |
| **`pg_rewind`** | Tool risincronizzare primary divergente come standby. | 09.2 |
| **pgBouncer** | Connection pooler PostgreSQL. | 09.2 |
| **`pmxcfs`** | Cluster filesystem Proxmox in `/etc/pve`. | 10.1 |
| **`pnputil`** | Tool Windows per gestire driver store. | 09.4, 17.2 |
| **POC** | Proof of Concept. | 15 |
| **Pre-copy (live migration)** | Algoritmo: copia RAM iterativamente finche dirty rate < bandwidth. | 10.2 |
| **`privsep`** | Privilege separation per token API. | 14.2 |
| **Prometheus** | Monitoring stack pull-based. | 13 |
| **Pruning (PBS)** | Rimozione di backup snapshot per retention policy. | 11.2 |
| **`proxmoxer`** | Libreria Python client per Proxmox API. | 14.2 |
| **`proxmox-backup-client`** | CLI client backup verso PBS. | 11.2 |
| **PVSCSI** | Paravirtual SCSI controller VMware. | 09.4 |

## Q

| Termine | Definizione | Modulo principale |
|---|---|---|
| **Q35** | Machine type QEMU moderno con PCI Express, vIOMMU, UEFI. | 09.4 |
| **`qcow2`** | Formato QEMU con snapshot, thin provisioning. | 09.3 |
| **`qemu-guest-agent` / `qga`** | Agent in-guest per Proxmox. | 09.4 |
| **`qemu-img convert`** | Tool per conversione tra formati VM. | 09.2 |
| **`qm migrate`** | Comando Proxmox per migrazione VM. | 10.2 |
| **`qm template`** | Marca una VM come template read-only. | 14.1 |
| **`qxl`** | Driver display QXL per accelerazione grafica. | 09.4 |
| **Quorum** | Maggioranza richiesta per decisioni cluster. | 10.1 |
| **`qdevice`** | Voto esterno per cluster a 2 nodi. | 10.1 |

## R

| Termine | Definizione | Modulo principale |
|---|---|---|
| **RAG status** | Red-Amber-Green; indicatore visivo di status. | 18 |
| **`raw` (formato disco)** | Formato senza overhead, IOPS diretti al backend. | 09.2, 09.3 |
| **Realm** | Sorgente di autenticazione in Proxmox. | 12.2 |
| **Replication slot (PG)** | Meccanismo per garantire ritenzione WAL. | 09.2 |
| **`restricted` (HA group)** | 1=solo gruppo, 0=preferenza gruppo. | 10.1 |
| **Retention policy** | Regole conservazione backup. | 11.1 |
| **Rolling migration (cluster)** | Replace one node at a time. | 09.1 |
| **Rollback trigger** | Condizione oggettiva che attiva il rollback. | 18 |
| **Rolling release / window** | Rilascio progressivo. | 18 |
| **ROI** | Return on Investment. | 15 |
| **RPO** | Recovery Point Objective. | 11.1, 19 |
| **RSC** | Receive Segment Coalescing (NIC feature). | 09.4 |
| **RSS** | Receive Side Scaling (NIC feature). | 09.4 |
| **RTO** | Recovery Time Objective. | 11.1, 19 |

## S

| Termine | Definizione | Modulo principale |
|---|---|---|
| **SBOM** | Software Bill of Materials. | 14.1 |
| **SeaBIOS** | Firmware BIOS legacy per QEMU. | 09.4 |
| **Self-fencing** | Nodo si auto-elimina (via watchdog). | 10.3 |
| **`shared_buffers`** | Cache pagine PostgreSQL. | 09.2 |
| **SIEM** | Security Information and Event Management. | 12.3 |
| **`slmgr.vbs`** | Script Windows per gestione licensing. | 09.4 |
| **Smoke test** | Test rapido che valida funzionalita base. | 18 |
| **Snapshot mode (vzdump)** | Backup live tramite snapshot del disco. | 11.1 |
| **Soak test** | Test prolungato per validare stabilita. | 18 |
| **`softdog`** | Implementazione software del watchdog. | 10.3 |
| **`SOURCE_AUTO_POSITION=1`** | MySQL replica usa GTID. | 09.2 |
| **Split-brain** | Due "isole" cluster con autorita conflittuale. | 10.1 |
| **Sponsor** | Stakeholder C-level con authority finale. | 18 |
| **StartTLS** | Upgrade da LDAP cleartext a TLS. | 12.2 |
| **State (HA)** | started/stopped/disabled/ignored/error. | 10.1 |
| **STONITH** | Shoot The Other Node In The Head; fencing attivo. | 10.3 |
| **Stretched cluster** | Singolo cluster su 2+ siti (vincoli stretti). | 19 |
| **Sticky sessions (LB)** | Mantieni client sullo stesso backend. | 09.1 |
| **Sync job (PBS)** | Replica datastore verso secondo PBS. | 11.2 |
| **Sync replication** | Replica simultanea; RPO 0 ma latency cost. | 19 |

## T

| Termine | Definizione | Modulo principale |
|---|---|---|
| **Tabletop exercise** | Simulazione su carta del cutover. | 18 |
| **Tape Backup (PBS)** | Backup offline su LTO. | 11.2 |
| **TCO** | Total Cost of Ownership. | 15 |
| **Template (Zabbix)** | Insieme riusabile items + triggers + graphs. | 13 |
| **`testssl.sh`** | Tool per audit configurazione TLS server. | 12.1 |
| **THP** | Transparent Hugepage. | 09.3 |
| **Throughput** | MB/s effettivi; metrica primaria sequenziale. | 09.3 |
| **Ticket (Proxmox auth)** | Session-based auth, scade in 2h. | 14.2 |
| **Token API** | Long-lived secret per auth scripting. | 14.2 |
| **TPM 2.0 emulato** | Trusted Platform Module software (`swtpm`). | 09.4 |
| **TPS** | Transactions Per Second. | 09.2 |
| **Trigger (Zabbix)** | Condizione che attiva un alert. | 13 |
| **TTL DNS** | Time-To-Live record DNS. | 18 |

## U

| Termine | Definizione | Modulo principale |
|---|---|---|
| **UEFI Secure Boot** | Boot firmware con cert-based verification. | 09.4 |
| **UPID** | Unique Process ID; identificatore di task async. | 14.2 |
| **USN (Update Sequence Number, AD)** | Numero seq replica AD. | 09.4 |

## V

| Termine | Definizione | Modulo principale |
|---|---|---|
| **VAMT** | Volume Activation Management Tool. | 09.4 |
| **Verification job (PBS)** | Validazione SHA-256 chunk. | 11.2 |
| **`verify=0` (LDAP realm)** | Disabilita verifica cert; *mai* in produzione. | 12.2 |
| **VirtIO** | Standard di paravirtualizzazione. | 09.4 |
| **virtio-scsi-single** | Controller Proxmox con iothread per disco. | 09.3 |
| **`virtio-win.iso`** | ISO con driver VirtIO Windows + qemu-ga. | 09.4 |
| **VLAN** | Virtual LAN; isolamento Layer 2. | 12.3 |
| **VM-Generation ID** | Identifier per detect snapshot rollback. | 09.4 |
| **VMA format** | Formato proprietario Proxmox per backup di VM. | 11.1 |
| **vMotion (VMware)** | Equivalente VMware di live migration. | 10.2 |
| **VMXNET3** | NIC paravirtualizzata VMware. | 09.4 |
| **vioscsi / viostor** | Driver VirtIO SCSI / Block per Windows. | 09.4 |
| **vmxnet3** | NIC VMware (sostituita da NetKVM su Proxmox). | 09.4 |
| **`vm.dirty_ratio`** | % RAM sporche prima blocco scrittura. | 09.3 |
| **`vm.swappiness`** | Tendenza kernel a usare swap. | 09.3 |
| **vRealize Operations** | VMware monitoring; equivalente assente in Proxmox. | 13 |
| **vscsiStats** | Tool ESXi per istogrammi block size. | 09.3 |
| **vzdump** | Tool Proxmox per backup VM e container. | 11.1 |

## W

| Termine | Definizione | Modulo principale |
|---|---|---|
| **WAL (Write-Ahead Log)** | Log modifiche PostgreSQL. | 09.2 |
| **`wal_keep_size`** | WAL ritenuto sul primary per standby (PG ≥ 13). | 09.2 |
| **War room** | Sala dove cutover team coordina esecuzione. | 18 |
| **Watchdog** | Timer hardware/software che reset il sistema se non kicked. | 10.1, 10.3 |
| **`weight 0` (HAProxy)** | Backend riceve 0 nuove sessioni. | 09.1 |
| **Wildcard cert** | Cert valido per `*.example.com`. | 12.1 |
| **WORM** | Write-Once-Read-Many; storage immutabile. | 11.1 |

## X

| Termine | Definizione | Modulo principale |
|---|---|---|
| **xtrabackup (Percona)** | Hot backup fisico MySQL. | 09.2 |
| **xtrabackup `--copy-back`** | Step restore in datadir destinazione. | 09.2 |
| **xtrabackup `--prepare`** | Step post-backup; applica log uncommitted. | 09.2 |

## Z

| Termine | Definizione | Modulo principale |
|---|---|---|
| **Zabbix Agent** | Daemon su host monitorato. | 13 |
| **Zabbix Server** | Componente principale Zabbix. | 13 |
| **ZFS ARC** | Adaptive Replacement Cache di ZFS. | 09.3 |
| **`zfs send / receive`** | Replication snapshot-based ZFS. | 19 |
| **ZFS recordsize** | Dimensione blocchi logici ZFS. | 09.3 |

---

## Note metodologiche

Questo glossario e *folder-wide* per il corso `10-MIGRAZIONE-VMWARE-PROXMOX`. Termini introdotti in moduli specifici hanno il riferimento al modulo principale; per definizioni piu approfondite, consultare la sezione "Glossario locale" del modulo indicato.

Per termini di altre cartelle del library (es. concetti generali Linux dal corso 02, concetti Windows dal corso 03), vedere i glossari delle cartelle corrispondenti una volta scaffolded.
