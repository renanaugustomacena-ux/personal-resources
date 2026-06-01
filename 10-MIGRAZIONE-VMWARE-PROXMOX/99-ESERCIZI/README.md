# 99-ESERCIZI — Laboratori e Scenari Avanzati

Questa cartella contiene esercizi extra che non rientrano direttamente nei singoli moduli. Tre tipi di contenuto:

1. **Lab guidati** — esecuzione step-by-step di scenari complessi cross-module.
2. **Scenari di troubleshooting** — guasti realistici da riprodurre e risolvere.
3. **Capstone-prep** — esercizi di consolidamento prima del progetto finale (`../00-CAPSTONE.md`).

---

## Indice

- `lab-01-cluster-3-nodi-from-scratch.md` — costruisci cluster a 3 nodi con storage condiviso, VLAN, HA, drill failover.
- `lab-02-migrazione-multi-os.md` — migra Linux + Windows + DB nello stesso batch, gestendo dipendenze.
- `lab-03-dr-drill-end-to-end.md` — failover completo a Site B + failback.
- `scenario-01-corosync-flapping.md` — diagnose split-brain intermittente.
- `scenario-02-vm-non-converge.md` — live migration che non converge mai.
- `scenario-03-bsod-windows-post-migration.md` — recovery 0x7B offline.
- `scenario-04-ceph-osd-down-cascading.md` — cluster Ceph che perde OSD a cascata.

---

## Lab 01 — Cluster 3 nodi from scratch

**Obiettivo**: costruire da zero un cluster Proxmox a 3 nodi production-ready in 4-6 ore.

**Materiale**: 3 server fisici o 3 VM nested (32 GB RAM, 8 core, 200 GB disk ognuno).

**Step**:
1. Installa Proxmox VE 8.x (ISO ufficiale) su tutti i nodi.
2. Configura networking: 1 NIC management (vmbr0), 1 NIC cluster/storage (vmbr1 con MTU 9000, VLAN dedicata).
3. Crea cluster: `pvecm create <name>` su pve1, `pvecm add pve1` su pve2 e pve3.
4. Verifica quorum: `pvecm status` deve mostrare 3 voti.
5. Configura Ceph: `pveceph init` + `pveceph mon create` + 3 OSD per nodo.
6. Configura HA: aggiungi 1 VM al pool HA con gruppo "all-nodes".
7. Test failover: spegnimento brusco di un nodo. Misura RTO.
8. Documenta.

**Criteri successo**: cluster Quorate, Ceph HEALTH_OK, VM HA migra entro 2 min al failover.

---

## Lab 02 — Migrazione multi-OS

**Obiettivo**: migrare 5 VM eterogenee (Linux Apache, Linux PostgreSQL, Windows AD DC, Windows IIS, FreeBSD) in batch.

**Step**:
1. Pre-migration: install virtio-win + qemu-ga su Windows; ensure Linux ha qemu-guest-agent.
2. Per ognuna: snapshot, export OVA o VMDK, conversione qcow2/raw.
3. Import su Proxmox, configurazione VM optimal per ogni OS.
4. Sequenza boot: AD DC prima (DNS), poi DB, poi app server.
5. Validazione: ping, RDP/SSH, applicative smoke test.

**Criteri successo**: tutti 5 i workload funzionali entro 4 ore.

---

## Lab 03 — DR drill end-to-end

**Obiettivo**: simulazione failover + failback su 2 cluster (Site A + Site B).

**Materiale**: 2 cluster Proxmox a 3 nodi ognuno, link site-to-site.

**Step**:
1. Configura ZFS replication ogni 15 min Site A → Site B.
2. Declare drill (NOT real). Spegni Site A.
3. Site B: promote replica, boot VM, redirect DNS.
4. Validate produzione su Site B per 4h.
5. Failback: replicate Site B → Site A delta, switch back.
6. Post-mortem report.

**Criteri successo**: RTO < 2h, RPO < 30 min, 0 data loss.

---

## Scenario 01 — Corosync flapping

**Sintomi**: HA Manager riporta intermittentemente "Node X timeout"; VM si migrano e poi tornano a casa loop.

**Da diagnosticare**: rete cluster instabile, MTU mismatch, switch port flapping, NIC firmware bug, CPU overload sul nodo causa late corosync token.

**Tools**: `journalctl -u corosync`, `ethtool -S <nic>`, `ip -s link show`, `mpstat 1`.

---

## Scenario 02 — VM non converge

**Sintomi**: `qm migrate <VMID> <target> --online` dopo 30 minuti non e ancora completato; dirty page rate 800 MB/s, bandwidth 600 MB/s.

**Da risolvere**: aumentare bandwidth (rete dedicata, MTU 9000, insecure), abilitare auto-converge throttling, abilitare compress, in extremis stop-and-copy diretto.

---

## Scenario 03 — BSOD Windows post-migration

**Sintomi**: Windows Server 2019 dopo migrazione boot in BSOD 0x7B INACCESSIBLE_BOOT_DEVICE.

**Da risolvere**: offline registry edit del file `Windows/System32/config/SYSTEM` per impostare Start=0 su `vioscsi`. Tools: `chntpw` o `hivex` da live Linux ISO. Verifica col risultato di `regedit` post-edit.

---

## Scenario 04 — Ceph OSD down cascading

**Sintomi**: `ceph -s` mostra OSD down; rebalance start; durante rebalance, un secondo OSD va offline; cluster va in HEALTH_ERR; alcune pool diventano inattive.

**Da risolvere**: stop il rebalance (`ceph osd set noout`), diagnose root cause primo OSD (disco SMART, log dmesg), valutare se ricreare entrambi gli OSD o se restore da snapshot. Strategia: ridurre carico cluster, aumentare priorita recovery vs client I/O.
