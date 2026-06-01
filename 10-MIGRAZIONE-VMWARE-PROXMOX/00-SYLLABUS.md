# Syllabus — Migrazione VMware vSphere → Proxmox VE

> **Tipo:** struttura formale del corso (scaffolding didattico)
> **Lingua del corso:** italiano
> **Livello target a fine corso:** Dreyfus 4 — Proficient (capace di pianificare, eseguire e troubleshootare migrazioni in ambiente di produzione enterprise senza supervisione, con giudizio sui trade-off operativi).
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:**
> - VMware vSphere/ESXi 8.0 GA (ott 2022) → 8.0 Update 3 (giu 2024) → 8.0 Update 3i / 8.0.3 P08 (feb 2026)
> - Proxmox VE 8.x (riferimento principale del corso) con note di transizione a Proxmox VE 9.x (rilasciato il 2025-11-19, base Debian 13 Trixie, kernel 6.17.x, QEMU 10.1, ZFS 2.3, Ceph Squid 19.2)
> - virt-v2v ≥ 2.x (libguestfs)
> - QEMU/KVM 7.x → 10.x

Questo syllabus formalizza la struttura didattica del corso. Il corso ha gia una guida di studio storica completa in `00-GUIDA-ALLO-STUDIO/guida-allo-studio-migrazione.md` (preservata integralmente, contiene roadmap settimanale dettagliata, lab setup, prerequisiti, glossario VMware↔Proxmox e bibliografia ragionata). Questo file aggiunge la struttura accademica formale: identita del corso, esiti di apprendimento espliciti, dipendenze tra moduli, schema di valutazione, capstone.

---

## 1. Identita del corso

**Titolo formale:** *Migrazione VMware vSphere → Proxmox VE — corso operativo di livello enterprise*

**Filosofia.** Il corso non insegna solo *come* migrare una VM. Insegna a *progettare* un programma di migrazione: assessment della baseline, scelta della strategia (cold/warm/live/app-level) sulla base di vincoli reali (downtime ammesso, dimensione disco, criticita applicativa, skill di team), pianificazione dei rischi con piani di rollback, esecuzione operativa con runbook tracciabili, validazione post-migrazione, stabilizzazione e operativita day-2.

**Approccio.** Studio dei fondamenti di entrambe le piattaforme (fasi 1-2), poi pratica operativa in laboratorio (fasi 3-5). Ogni capitolo combina teoria, comando con output atteso, configurazione di esempio realistica, modi di rottura noti e procedure di recupero.

**Cosa NON e questo corso.**
- Non e un'introduzione a VMware o a Linux: prevede gia conoscenze di base di entrambi (vedi "Prerequisiti").
- Non e un corso di certificazione (VCP, VCAP, Proxmox Certified) — copre il sapere operativo che si sovrappone, ma il taglio e quello di chi *fa il lavoro*, non di chi prepara un esame.
- Non e una vendita di Proxmox contro VMware. Le ragioni che spingono al cambio (licensing post-Broadcom, costi, indipendenza tecnologica) sono trattate nel modulo 15, ma il corso assume che la decisione strategica sia gia stata presa.

---

## 2. Destinatari e ruoli

| Ruolo | Profilo | Sezioni prioritarie |
|---|---|---|
| System Administrator | Opera sistemi Linux/Windows, gestisce VM, ha visibilita ESXi diretta | 01-04, 06-09, 11, 16-17 |
| Infrastructure Engineer | Progetta sistemi virtualizzati, dimensiona, sceglie tecnologie | tutti |
| Network Engineer | Si interessa al lato L2/L3 della migrazione | 04, 07, 12 |
| Storage Engineer | Si interessa a datastore, formati, performance, replica | 03, 08 |
| DevOps / SRE | Cerca l'automazione e il day-2 ops | 13, 14, 16 |
| Security Engineer | Vuole garantire identita, audit, compliance dopo il passaggio | 12 |
| IT Manager / CTO | Cerca il quadro strategico e di costo | 00, 05, 15 |

Il modulo `00-GUIDA-ALLO-STUDIO/guida-allo-studio-migrazione.md` contiene gia una tabella simile e una proposta di roadmap settimanale — qui la rilanciamo con esplicita identita di livello (Dreyfus) per ruolo:

| Ruolo | Livello iniziale richiesto | Livello atteso a fine corso |
|---|---|---|
| System Admin | Dreyfus 2-3 (Advanced Beginner / Competent) | Dreyfus 4 (Proficient) |
| Infrastructure Eng. | Dreyfus 3 (Competent) | Dreyfus 4-5 (Proficient / Expert) |
| DevOps / SRE | Dreyfus 3 | Dreyfus 4 |
| IT Manager | Dreyfus 1-2 | Dreyfus 3 (sa giudicare proposte tecniche) |

---

## 3. Esiti di apprendimento (verbi attivi)

Al completamento del corso lo studente deve essere in grado di:

**Livello cognitivo: Comprensione**
- spiegare l'architettura di vSphere/ESXi e di Proxmox VE in modo speculare, identificando i concetti omologhi e quelli senza equivalente diretto;
- ricostruire la storia dei modelli di licenza VMware pre/post-Broadcom e i loro effetti operativi e finanziari su un parco macchine reale.

**Livello cognitivo: Applicazione**
- eseguire l'inventario completo di un ambiente vSphere (host, VM, storage, networking, permessi, snapshot, RDM, passthrough) tramite PowerCLI e ovftool, producendo gli artefatti CSV/JSON che alimenteranno il piano di migrazione;
- scegliere e dimensionare il cluster Proxmox target, motivando la scelta del backend di storage (LVM-Thin, ZFS, Ceph, NFS) e del modello di networking (Linux Bridge, OVS, SDN);
- convertire dischi VMDK → qcow2 / raw con `qemu-img`, gestendo split VMDK, descriptor file e modalita di preallocazione;
- automatizzare la conversione di VM con `virt-v2v` (input `vpx://`, `ova`, `disk`), iniettando driver VirtIO e validando il boot;
- pianificare un cutover di rete (DNS TTL ridotto, mappatura VLAN, parallelo DHCP/firewall) con piano di rollback < 5 minuti.

**Livello cognitivo: Analisi**
- diagnosticare un cluster Proxmox in stato di "no quorum" o di split-brain, ricostruendo la topologia Corosync/`pmxcfs` e applicando interventi minimi e reversibili;
- analizzare le performance I/O di una VM migrata (`iostat -xdz`, `qm config`, `pveperf`) e attribuire un eventuale degrado a NUMA, iothread, cache mode, o backend di storage;
- distinguere falsi-positivi e veri-positivi negli alert post-migrazione (Zabbix, Grafana) discriminando l'effetto della migrazione dai cambi configurativi paralleli.

**Livello cognitivo: Valutazione e progettazione**
- progettare un programma di migrazione a wave per > 50 VM con classificazione per criticita, dipendenze applicative, finestre di downtime e criteri di go/no-go misurabili;
- valutare l'opportunita di migrare a Proxmox VE 9.x rispetto a 8.x, considerando deltas Debian Trixie, kernel 6.17, QEMU 10, Ceph Squid, e le finestre EOL;
- redigere un runbook produttivo pronto per essere eseguito da un peer, includendo pre-flight, esecuzione, validazione, criteri di rollback e comunicazione.

---

## 4. Prerequisiti

I prerequisiti tecnici minimi sono gia descritti in dettaglio in `00-GUIDA-ALLO-STUDIO/guida-allo-studio-migrazione.md` §5. In sintesi:

| Area | Soglia minima |
|---|---|
| Linux system administration | CRITICO — Dreyfus 3+ (filesystem, systemd, package mgmt, journalctl, bash scripting base) |
| Networking TCP/IP | IMPORTANTE — IPv4/IPv6 + subnetting, VLAN 802.1Q, bonding/LACP, iptables/nftables, DNS, DHCP |
| Storage | IMPORTANTE — block vs file, RAID 0/1/5/6/10, LVM PV/VG/LV, NFS, iSCSI |
| Virtualizzazione di base | UTILE — concetti hypervisor tipo 1 vs 2, VirtIO, snapshot, clone |
| VMware vSphere (esistente) | UTILE — navigazione vSphere Client, gestione VM, datastore base |

Per chi viene da altri corsi della libreria, le dipendenze esterne sono:

| Dipendenza | Corso/Modulo della libreria |
|---|---|
| Linux fondamentali | `02-LINUX-POWERUSER` (intero) — in particolare moduli su filesystem, systemd, networking, LVM, ZFS, virtualizzazione (KVM/QEMU) |
| Operations e ITIL | `08-MANUTENZIONE-IT` (cap. su backup/DR, change management, runbook, SLO/SLI) |
| Automazione e IaC | `09-AUTOMAZIONI-FLUSSI-DI-LAVORO` (Ansible, Python, OAuth/API) — alimenta il modulo 14 |
| Sicurezza e identita | `03-WINDOWS-POWERUSER` (Active Directory, LDAP, PKI) per il modulo 12 |

---

## 5. Struttura per fasi e mappa delle dipendenze tra moduli

Il corso e organizzato in 5 fasi sequenziali. La mappa qui sotto rappresenta le dipendenze fra moduli (una freccia A → B significa "il modulo B presuppone i contenuti di A").

```
FASE 1 — FONDAMENTI
  01 vSphere/ESXi ──┐
                    ├──► 05 Assessment ──► 06 Strategie ──► 07 Net ──► 08 Storage ──► 09 Scenari
  02 Proxmox VE ────┤                              │            │           │
                    │                              ▼            ▼           │
                    ├──► 03 Storage adv ───────────┘                        │
                    └──► 04 Net adv ───────────────┘                        │
                                                                            ▼
                                                                  ┌─── FASE 4 ───┐
                                                                  │ 10 Cluster HA │
                                                                  │ 11 Backup     │
                                                                  │ 12 Sicurezza  │
                                                                  └──────┬────────┘
                                                                         ▼
                                                                  ┌─── FASE 5 ───┐
                                                                  │ 13 Monit.    │
                                                                  │ 14 IaC       │
                                                                  │ 15 Business  │
                                                                  │ 16 Runbook   │
                                                                  │ 17 Troublesh.│
                                                                  └──────────────┘
                                                                         ▼
                                                                  ┌── nuovi ──┐
                                                                  │ 18 Cutover│
                                                                  │ 19 DR     │
                                                                  └───────────┘
```

L'ordine raccomandato di studio e quello sopra. Saltare moduli e ammesso solo per il **Percorso Accelerato per Ruolo** descritto in `00-GUIDA-ALLO-STUDIO/guida-allo-studio-migrazione.md` §3.

### Mappatura: fase → moduli → ore-stimate-aggregate

| Fase | Moduli | Ore stimate (lettura + lab) |
|---|---|---|
| 1. Fondamenti | 00, 01, 02, 03, 04 | 50-66 |
| 2. Assessment | 05 | 8-12 |
| 3. Migrazione | 06, 07, 08, 09 | 40-56 |
| 4. Post-migrazione | 10, 11, 12 | 26-38 |
| 5. Operations | 13, 14, 15, 16, 17 | 42-56 |
| Nuovi | 18, 19 | 14-20 |
| Capstone | 00-CAPSTONE | 20-30 |
| **Totale** | | **200-278** |

(Le stime sono coerenti con la roadmap settimanale del file storico, con +10–20 ore aggiunte per il capstone formale e per i moduli 18 e 19.)

---

## 6. Schema di valutazione

Il corso non e a frequenza obbligatoria ne ha esami. La valutazione e per **milestone pratiche autovalutate**, ognuna con criteri di passaggio espliciti (PASS/FAIL non-ambigui).

| Milestone | Dopo modulo | Criterio di PASS |
|---|---|---|
| M1 — Fondamenti | 02.2 | Installato Proxmox cluster a 3 nodi, creato 1 VM Linux + 1 Windows + 1 LXC, dimostrato cluster status `Quorate (3/3)`. |
| M2 — Storage e Net | 04.1 | Configurato ZFS mirror, VLAN trunk attiva, Linux Bridge con bonding 802.3ad o active-backup; produrre `zpool status`, `bridge link show`, `cat /proc/net/bonding/bond0`. |
| M3 — Prima migrazione | 06.1 o 06.2 | Migrata 1 VM (Linux o Windows) da ESXi a Proxmox via cold migration; VM avvia, rete configurata, login SSH/RDP riuscito. |
| M4 — Migrazione completa | 09.4 | Migrate ≥ 5 VM (mix Windows/Linux/DB) con almeno 2 strategie diverse (cold + virt-v2v + warm/rsync). Documentare tempi e anomalie. |
| M5 — Cluster HA produzione | 10.4 | Cluster 3 nodi con HA attivo, fencing configurato, failover testato spegnendo brutalmente un nodo: VM si riavvia su altro nodo entro la finestra obiettivo (≤ 2 min). |
| M6 — Production Ready | 12.3 | Backup PBS schedulato e con verifica restore eseguita; certificato TLS valido (Let's Encrypt o internal CA); auth LDAP/AD funzionante. |
| M7 — Day-2 operativo | 17.4 | Monitoring Zabbix attivo con almeno 5 trigger custom; ≥ 2 runbook scritti dallo studente e validati sul lab; troubleshooting completato di 1 scenario simulato (es. quorum loss). |
| M8 — Capstone | 18-19 + capstone | Vedi `00-CAPSTONE.md`. |

Ogni milestone ha esercizi di rinforzo nei file `99-ESERCIZI/`.

---

## 7. Capstone

Vedi `00-CAPSTONE.md` per il brief completo. In sintesi: progettare ed eseguire un programma di migrazione end-to-end su un ambiente VMware simulato (3 host ESXi nested, ~10 VM eterogenee, storage NFS condiviso, dominio AD), producendo:

1. piano di assessment con artefatti CSV;
2. dimensionamento del cluster Proxmox target con motivazioni;
3. piano di rete (VLAN, IP, DNS, firewall) con piano di rollback;
4. runbook eseguibile (≥ 30 step) per la wave principale;
5. report di esecuzione (output reali, deviazioni, decisioni in-flight);
6. validazione post-migrazione (performance baseline confronto, backup verificato, monitoring attivo);
7. documento di handover per gli operatori day-2.

Tempo stimato: 20-30 ore di lavoro pratico, distribuite su 1-2 settimane.

---

## 8. Bibliografia

L'elenco completo delle fonti primarie usate nel corso e in `00-BIBLIOGRAFIA.md`. Le risorse storiche del corso (libri, comunita, doc ufficiali) sono in `00-GUIDA-ALLO-STUDIO/guida-allo-studio-migrazione.md` §7.

Norma del corso: ogni claim tecnico non banale e ancorato ad almeno una fonte primaria (RFC, doc ufficiale Proxmox/VMware/QEMU/libguestfs, kernel.org, IEEE, NIST, CVE pubblico). Le fonti sono numerate per modulo nei rispettivi capitoli e consolidate in `00-BIBLIOGRAFIA.md`.

---

## 9. Cadenza didattica suggerita

| Modalita | Ore/settimana | Settimane | Note |
|---|---|---|---|
| Full-time | 40 | 5-7 | Include capstone |
| Part-time intensivo | 20 | 10-14 | Realistico per chi lavora a tempo pieno |
| Studio serale | 8-10 | 20-30 | Distribuisce il carico, ma rischia di perdere continuita: tenere quaderno di lab |
| Solo lab pratico (skip teoria) | 20 | 4-5 | Sconsigliato per chi non ha gia 2-3 anni di esperienza VMware |

---

## 10. Cosa cambia in questo corso rispetto alla guida storica

Il file `00-GUIDA-ALLO-STUDIO/guida-allo-studio-migrazione.md` resta il documento di riferimento esecutivo (roadmap settimanale, lab setup, glossario VMware↔Proxmox). Questo `00-SYLLABUS.md` aggiunge sopra di esso, *senza sostituirlo*:

- una identita formale del corso e dei suoi limiti;
- esiti di apprendimento espressi in verbi attivi e classificati per livello cognitivo (Bloom/Anderson);
- mappatura esplicita delle dipendenze fra moduli;
- criteri di PASS misurabili per ogni milestone;
- collegamento ai capstone, ai case study e agli esercizi extra in `99-*/`;
- riferimenti aggiornati a Proxmox VE 9.x (rilasciato il 2025-11-19, vedi `00-BIBLIOGRAFIA.md`) e ai punti rilascio di ESXi 8.0.x successivi a U3.

Tutti i moduli esistenti restano validi: gli aggiornamenti tecnici (es. delta 8.x → 9.x) sono inseriti come callout `> **Approfondimento**` ai punti specifici, mai come riscrittura.
