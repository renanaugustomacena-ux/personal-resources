# Production Cutover Runbook — Migrazione VMware → Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 8 — Cutover di produzione · Modulo 18 (nuovo, vedi `00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 01-17 (intera materia tecnica del corso); modulo 16 (runbook batch / cluster); fluenza con `qm`, `pct`, `pvecm`, networking, storage, backup; capacita di leadership operativa durante incident; comunicazione tecnico-business con stakeholder C-level.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. progettare un **Production Cutover Plan** end-to-end con timeline, ruoli (cutover lead, network lead, storage lead, app lead, comms lead), checklist preflight, executive go/no-go criteria;
> 2. orchestrare un **cutover finale** (la finestra dove il traffico produttivo passa da VMware a Proxmox) con minimal downtime e zero data loss;
> 3. preparare e validare la **rollback procedure**: criteri di trigger oggettivi, soglia di tempo per decidere ("se non e UP entro T+90min, rollback"), procedura step-by-step;
> 4. comunicare con stakeholder durante l'esecuzione: status update ogni 30min, escalation path, war room protocol;
> 5. eseguire **post-cutover validation**: smoke test applicativi, monitoring threshold validation, business metric checks, soak test 24-48h;
> 6. documentare lessons learned e aggiornare il runbook per il prossimo cutover.
> **Tempo stimato:** lettura 90-120 min · pianificazione cutover reale 4-8 settimane · esecuzione 6-24h
> **Livello:** proficient → expert (Dreyfus 4 → 5); leadership operativa
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; framework di reference: ITIL 4 Change Enablement, Google SRE Book.

---

## Mappa concettuale

```
+============================================================+
|     Production Cutover: pipeline e milestone               |
+============================================================+
|                                                            |
|   T-30g: ANNUNCIO + COMMS PLAN                             |
|     - Stakeholder briefing                                  |
|     - Schedule cutover window (typically weekend low-load) |
|     - Communication plan to end users                      |
|                                                            |
|   T-14g: PREP DEEP                                         |
|     - VM inventory final + dependency map                  |
|     - Pre-flight: backup verified, target capacity ok      |
|     - DNS TTL ridotto a 5min (24-48h prima)                |
|     - Tabletop exercise (dry run)                          |
|                                                            |
|   T-7g: FREEZE WINDOW                                      |
|     - Code freeze, no app changes                          |
|     - Final delta migration sync                           |
|     - Rollback plan reviewed and approved by sponsor       |
|                                                            |
|   T-1g: GO/NO-GO                                            |
|     - Health check finale: cluster Proxmox green           |
|     - Network diagnostic completi                          |
|     - Approval formale dello sponsor                       |
|                                                            |
|   T0:    CUTOVER (windowed, 4-12h tipico)                  |
|     - War room aperto                                      |
|     - Step-by-step esecuzione documentata                  |
|     - Status update ogni 30min                             |
|     - Decision points con criteri oggettivi                |
|                                                            |
|   T0+24h: POST-CUTOVER VALIDATION                          |
|     - Soak test 24-48h                                     |
|     - Metriche monitoring vs baseline                      |
|     - Business metric validation                           |
|                                                            |
|   T0+7d: STABILIZATION + DECOMMISSION PREP                 |
|     - VMware mantenuto offline ma pronto al rollback       |
|     - Skill transfer + runbook update                      |
|                                                            |
|   T0+30d: VMWARE DECOMMISSIONING                           |
|     - Spegnimento finale VMware                            |
|     - Reclaim hardware o restituzione (lease)              |
|     - License decommission Broadcom                        |
|                                                            |
+============================================================+
```

## Idee guida del modulo

1. **Cutover non e operazione tecnica, e operazione di leadership.** La parte tecnica deve essere noiosa (gia testata in batch precedenti). La sfida e gestire stakeholder, decision points sotto pressione, comunicazione pulita.
2. **Rollback va testato, non solo documentato.** "Se va male torniamo a VMware" non e un piano. "VMware spinto entro 30 min in caso di trigger X, validato in lab a Q1" e un piano.
3. **Decision points devono essere oggettivi, mai soggettivi.** Non "se sembra che non vada bene". Si: "se IOPS DB < 80% baseline per > 15 min consecutivi, rollback".
4. **War room is a thing.** Stanza fisica o Zoom dedicato; tutti i lead presenti; comms lead aggiorna stakeholder ogni 30min senza interrompere il lavoro tecnico.
5. **Post-cutover non e "fatto". E iniziato.** I primi 24-72h sono critici: monitoring serrato, validazione business metric, on-call elevato.
6. **Zero surprise.** Ogni step del cutover deve essere stato eseguito almeno una volta in lab. L'unica differenza e il traffico di produzione reale.
7. **Comunicazione asincrona.** Il team tecnico non risponde ai manager: il Comms Lead filtra e riassume. Questo protegge il focus del team.

---

## Indice

- [1. Teoria: anatomia di un cutover](#1-teoria-anatomia-di-un-cutover)
- [2. Pre-cutover (T-30g a T-1g)](#2-pre-cutover)
- [3. Roles e responsibilities](#3-roles-e-responsibilities)
- [4. Cutover execution (T0)](#4-cutover-execution)
- [5. Decision points e criteri rollback](#5-decision-points-e-criteri-rollback)
- [6. Rollback procedure](#6-rollback-procedure)
- [7. Post-cutover validation (T0+24h a T0+7d)](#7-post-cutover-validation)
- [8. Decommissioning VMware (T0+30d)](#8-decommissioning-vmware)
- [9. Communication templates](#9-communication-templates)
- [10. Tooling e automazione cutover](#10-tooling-e-automazione-cutover)
- [11. Scenari reali e case study](#11-scenari-reali-e-case-study)
- [12. Lessons learned framework](#12-lessons-learned-framework)
- [13. Troubleshooting](#13-troubleshooting)
- [14. Esercizi](#14-esercizi)
- [15. Auto-valutazione](#15-auto-valutazione)
- [16. Approfondimenti](#16-approfondimenti)
- [17. Letture consigliate](#17-letture-consigliate)
- [18. Collegamenti incrociati](#18-collegamenti-incrociati)
- [19. Glossario locale](#19-glossario-locale)

---

## 1. Teoria: anatomia di un cutover

### 1.1 Cos'e un production cutover

Un **production cutover** (o "go-live") e l'operazione pianificata che trasferisce il carico di lavoro produttivo dalla piattaforma sorgente (VMware) alla piattaforma destinazione (Proxmox VE). A differenza delle migrazioni batch (modulo 16), il cutover di produzione e un evento singolo, ad alto impatto, con finestra temporale definita e visibilita executive.

Caratteristiche distintive:
- **Irreversibilita controllata:** dopo il cutover il sistema vecchio viene mantenuto offline ma non smantellato per 30 giorni;
- **Impatto business diretto:** downtime durante la maintenance window;
- **Decision chain formale:** GO/NO-GO con authority definita;
- **Multi-team coordination:** rete, storage, applicativi, comunicazione operano in parallelo;
- **Visibilita esterna:** utenti finali, clienti, management ricevono comunicazioni formali.

### 1.2 Differenza tra cutover e migrazione

| Aspetto | Migrazione batch (modulo 16) | Production cutover (modulo 18) |
|---------|-----|-----|
| Scope | Subset di VM (1-20 per batch) | Intero workload produttivo |
| Downtime tollerabile | Per-VM, spesso cold migrate | Finestra coordinata per tutto |
| Decision authority | Team lead tecnico | CIO/IT Director (sponsor) |
| Rollback | Per-VM, poco impatto | Intero ambiente, alto impatto |
| Comunicazione | Team-internal | Tutta l'organizzazione |
| War room | Non necessario | Obbligatorio |
| Frequenza | Ripetuta (10-50 batch) | Singola (il "big bang" finale) |
| Post-validation | Smoke test per batch | Soak test 24-72h + business metrics |

### 1.3 Modelli di cutover

#### Big Bang cutover

Tutto il workload migra in una sola finestra. Massimo downtime, minima complessita logica.

```
VMware  ████████████████████████████     STOP
                                    ↓ cutover
Proxmox                             ████████████████████████
```

**Quando usare:**
- Ambiente piccolo (<50 VM);
- Dipendenze strette che impediscono migrazione parziale;
- Weekend lungo disponibile (festivi, ponti);
- Team con esperienza limitata (meno decision points = meno errori).

**Rischi:**
- Downtime esteso (8-16h possibile);
- Se rollback, si torna a zero;
- Pressione psicologica elevata.

#### Phased cutover (wave-based)

Il workload migra in wave successive, ciascuna con la propria mini-finestra. Il cutover finale e solo l'ultima wave (tipicamente i sistemi piu critici).

```
Wave 1 (dev/test):     ████ STOP → Proxmox ████████████████
Wave 2 (app servers):       ████ STOP → Proxmox ████████████
Wave 3 (database tier):          ████ STOP → Proxmox ████████
Wave 4 (PRODUCTION):                 ████ STOP → Proxmox ████
```

**Quando usare:**
- Ambiente grande (100+ VM);
- Sistemi con dipendenze a tier (web → app → DB);
- Possibilita di split DNS / multi-homing temporaneo;
- Team esperto che gestisce complessita coordinamento.

**Rischi:**
- Periodo transitorio con split-brain (parte su VMware, parte su Proxmox);
- Network routing complesso durante la transizione;
- Piu decision points = piu possibilita di errore umano.

#### Blue-Green cutover

Entrambi gli ambienti sono attivi contemporaneamente. Il cutover e un semplice redirect del traffico (DNS, load balancer, VIP).

```
VMware  ████████████████████████████ → STANDBY (30d)
Proxmox ████████████████████████████ ← active dopo flip
         ^                          ^
         replication continua       flip traffic
```

**Quando usare:**
- Zero-downtime requirement;
- Budget per doppia capacita temporanea;
- Application stateless o con replication nativa (DB clustering);
- Team con capacita di dual-stack networking.

**Rischi:**
- Costo doppio durante il periodo di overlap;
- Data consistency tra i due ambienti;
- Complessita di networking (split DNS, health checks, session affinity).

### 1.4 Calcolo della maintenance window

La durata della finestra dipende da fattori misurabili. Formula empirica:

```
T_window = T_drain + T_final_sync + T_boot + T_smoke + T_dns + T_buffer

Dove:
  T_drain      = tempo di drain del traffico (tipico: 5-15 min)
  T_final_sync = sync ultimo delta dati (dipende da change rate)
  T_boot       = boot tutte le VM su Proxmox (dipende da numero e ordine)
  T_smoke      = smoke test applicativi (tipico: 30-60 min)
  T_dns        = propagazione DNS (5 min con TTL basso, 15 min buffer)
  T_buffer     = buffer per imprevisti (minimo 30% di T_totale)
```

**Esempio numerico:**
- 80 VM, divise in 4 batch di boot;
- Change rate basso (sync finale: 15 min);
- Boot time medio per VM: 3 min, parallelizzato su 4 batch → 12 min per batch → 48 min totali.

```
T_drain      =  10 min
T_final_sync =  15 min
T_boot       =  48 min
T_smoke      =  45 min
T_dns        =  15 min
T_subtotal   = 133 min (2h 13min)
T_buffer     =  40 min (30%)
T_window     = 173 min → arrotondare a 3h
```

Con il buffer, pianificare una finestra di 4h. Comunicare 6h per sicurezza (il margine protegge da pressioni per chiudere prematuramente).

### 1.5 Risk appetite e downtime contrattuale

Prima di pianificare il cutover, verificare:

| Vincolo | Dove trovare l'informazione | Impatto |
|---------|-----|-----|
| SLA verso clienti | Contratti commerciali, MSA | Penali per downtime non schedulato |
| SLA interni | OLA tra IT e business unit | Impatto su credibilita interna |
| Regolamentazione | NIS2, DORA, settore-specifico | Obbligo di notifica downtime pianificato |
| Finestre consentite | Policy aziendale Change Management | Orari permessi per maintenance (weekend, notte) |
| Business calendar | Finance, Marketing, Sales | Evitare chiusure contabili, lanci, campagne |

**Best practice:** il cutover non avviene MAI:
- L'ultimo giorno del mese/trimestre (chiusure contabili);
- Durante campagne marketing con traffic spike atteso;
- In periodi di audit;
- In concomitanza con altre maintenance window (network, datacenter).

### 1.6 ITIL 4 Change Enablement nel contesto cutover

Il cutover e classificato come **Normal Change — High Risk** nel modello ITIL 4:

```
Change Classification:
  Type:     Normal Change
  Risk:     High
  Impact:   Major (all production services)
  Category: Infrastructure
  
Change Advisory Board (CAB):
  - Required: YES (High risk)
  - Review:   Full plan, rollback procedure, test results
  - Approval: Documented with signatures
  
Change Record:
  - Planned start:    <date time>
  - Planned end:      <date time>
  - Actual start:     <filled at execution>
  - Actual end:       <filled at execution>
  - Result:           SUCCESS | FAILED | ROLLED BACK
  - PIR date:         T+7d (Post-Implementation Review)
```

### 1.7 SRE principles applicati al cutover

Dalla Google SRE philosophy, applicare:

1. **Error budget thinking:** il cutover consuma error budget. Se il servizio e gia al limite del SLO, il cutover va posticipato.
2. **Toil reduction:** automatizzare il piu possibile (scripting boot order, health checks, DNS flip). La parte manuale deve essere solo decision points.
3. **Blameless postmortem:** qualunque esito (successo o rollback), il lessons learned e blameless.
4. **Progressive rollout:** dove possibile, phased cutover con canary prima del full rollout.

---

## 2. Pre-cutover

### 2.1 T-30 giorni: annuncio e governance

#### Documenti da produrre e firmare

1. **Cutover Plan** (documento master):
   - Scope: lista VM in-scope con VMID sorgente e destinazione;
   - Timeline: Gantt con ogni fase e milestone;
   - Roles: RACI matrix;
   - Success criteria: metriche oggettive;
   - Rollback criteria: trigger oggettivi;
   - Communication plan: matrice stakeholder-canale-frequenza.

2. **Risk Register** (aggiornamento dal modulo 05):

```
| ID  | Rischio                        | P | I | Score | Mitigation              | Owner        | Status  |
|-----|--------------------------------|---|---|-------|-------------------------|--------------|---------|
| R01 | Sync finale fallisce           | 3 | 5 | 15    | Pre-test sync 3x        | Storage Lead | OPEN    |
| R02 | DNS non propaga in tempo       | 2 | 4 | 8     | TTL ridotto 48h prima   | Network Lead | OPEN    |
| R03 | App dipende da hw VMware       | 1 | 5 | 5     | Audit pre-cutover        | App Lead     | OPEN    |
| R04 | Team fatigue durante notte     | 3 | 3 | 9     | Turni, caffeina, breaks | Cutover Lead | OPEN    |
| R05 | Sponsor non reperibile         | 2 | 5 | 10    | Delegate authority doc   | Comms Lead   | OPEN    |
| R06 | Network latency post-cutover   | 3 | 4 | 12    | Baseline benchmark pre  | Network Lead | OPEN    |
| R07 | License Proxmox non attivate   | 1 | 3 | 3     | Verify 2w before        | Cutover Lead | CLOSED  |
| R08 | Backup pre-cutover incompleto  | 2 | 5 | 10    | Verify restore test     | Storage Lead | OPEN    |
| R09 | DB data inconsistency          | 2 | 5 | 10    | Checksum + row count    | App Lead     | OPEN    |
| R10 | Cambio last-minute da business | 3 | 4 | 12    | Freeze window strict    | Cutover Lead | OPEN    |
```

3. **Communication Matrix:**

```
| Stakeholder        | Canale          | Frequenza       | Responsabile |
|--------------------|-----------------|-----------------|--------------|
| CIO / IT Director  | Email + call    | T-30, T-7, T-1  | Comms Lead   |
| Business Unit Lead | Email           | T-7, T-1, T0    | Comms Lead   |
| End Users          | Email + portal  | T-7, T0, T0+1h  | Comms Lead   |
| Help Desk          | Slack + email   | T-7, T0 ongoing | Comms Lead   |
| Vendor (Broadcom)  | Ticket          | T-30 (notify)   | Cutover Lead |
| Vendor (Proxmox)   | Support portal  | T-7 (standby)   | Storage Lead |
| Security team      | Email + Slack   | T-7, T0         | Cutover Lead |
| External clients   | Email + status  | T-7, T0+1h      | Comms Lead   |
```

#### Calendario governance

```
T-30g  Kickoff meeting con lead (1h)
       - Presentazione cutover plan
       - Assegnazione ruoli RACI
       - Review risk register
       
T-28g  Communication plan distribuito

T-21g  Status meeting #1 (30 min, ogni martedi)
       - Update preparazione per area

T-14g  Tabletop exercise (4h)
       - Simulazione su carta, scenario-based
       - Dettaglio sotto "Tabletop exercise"

T-14g  Status meeting #2

T-10g  DNS TTL reduction (anticipare 48h prima del target)
       Verificare propagazione TTL con:
       dig +trace @8.8.8.8 app.example.com
       dig +trace @1.1.1.1 app.example.com

T-7g   Freeze window starts
       Status meeting #3

T-3g   Final rehearsal in lab
       Rollback drill test

T-1g   GO/NO-GO meeting (2h)

T0     CUTOVER
```

### 2.2 T-14 giorni: deep preparation

#### Pre-flight checklist completa

```bash
#!/bin/bash
# cutover-preflight-check.sh — run at T-14 and T-1
# Eseguire su ogni nodo Proxmox del cluster di destinazione

set -euo pipefail

LOG="/var/log/cutover-preflight-$(date +%Y%m%d-%H%M%S).log"
PASS=0
FAIL=0

log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"; }
check_pass() { log "  [PASS] $1"; ((PASS++)); }
check_fail() { log "  [FAIL] $1"; ((FAIL++)); }

log "=== CUTOVER PREFLIGHT CHECK ==="
log "Host: $(hostname)"
log "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# 1. Cluster status
log "--- Cluster Health ---"
CLUSTER_STATUS=$(pvecm status 2>&1)
if echo "$CLUSTER_STATUS" | grep -q "Quorate:.*Yes"; then
    check_pass "Cluster quorate"
else
    check_fail "Cluster NOT quorate"
fi

NODES_ONLINE=$(pvecm nodes | grep -c "Online")
NODES_TOTAL=$(pvecm nodes | tail -n +2 | wc -l)
if [ "$NODES_ONLINE" -eq "$NODES_TOTAL" ]; then
    check_pass "All $NODES_TOTAL nodes online"
else
    check_fail "Only $NODES_ONLINE of $NODES_TOTAL nodes online"
fi

# 2. HA status
log "--- HA Manager ---"
HA_STATUS=$(ha-manager status 2>&1)
if echo "$HA_STATUS" | grep -q "error"; then
    check_fail "HA manager has errors"
else
    check_pass "HA manager healthy"
fi

# 3. Ceph (se presente)
log "--- Ceph Status ---"
if command -v ceph &>/dev/null; then
    CEPH_HEALTH=$(ceph health 2>&1)
    if echo "$CEPH_HEALTH" | grep -q "HEALTH_OK"; then
        check_pass "Ceph HEALTH_OK"
    elif echo "$CEPH_HEALTH" | grep -q "HEALTH_WARN"; then
        check_fail "Ceph HEALTH_WARN — investigate before cutover"
    else
        check_fail "Ceph HEALTH_ERR — DO NOT proceed"
    fi
    
    # OSD usage
    MAX_OSD_USAGE=$(ceph osd df | awk '/^[0-9]/{print $NF}' | sort -rn | head -1)
    if (( $(echo "$MAX_OSD_USAGE < 75" | bc -l) )); then
        check_pass "Max OSD usage: ${MAX_OSD_USAGE}% (< 75%)"
    else
        check_fail "Max OSD usage: ${MAX_OSD_USAGE}% — too high for cutover"
    fi
else
    log "  [INFO] Ceph not installed, skipping"
fi

# 4. Storage space
log "--- Storage Capacity ---"
for STORAGE in $(pvesm status | awk 'NR>1 {print $1}'); do
    USAGE=$(pvesm status | awk -v s="$STORAGE" '$1==s {printf "%.0f", ($3/$4)*100}')
    if [ "$USAGE" -lt 70 ]; then
        check_pass "Storage $STORAGE: ${USAGE}% used"
    else
        check_fail "Storage $STORAGE: ${USAGE}% used — need < 70%"
    fi
done

# 5. Network connectivity
log "--- Network Checks ---"
for IFACE in $(ip -o link show up | awk -F: '{print $2}' | tr -d ' ' | grep -v lo); do
    SPEED=$(ethtool "$IFACE" 2>/dev/null | awk '/Speed:/{print $2}')
    check_pass "Interface $IFACE: UP, speed $SPEED"
done

# 6. DNS resolution
log "--- DNS ---"
if host proxmox-node1.example.com &>/dev/null; then
    check_pass "DNS resolution working"
else
    check_fail "DNS resolution failed"
fi

# 7. Time sync
log "--- NTP ---"
OFFSET=$(chronyc tracking 2>/dev/null | awk '/System time/{print $4}')
if [ -n "$OFFSET" ]; then
    check_pass "NTP offset: ${OFFSET}s"
else
    check_fail "NTP not synced — critical for cluster"
fi

# 8. Backup verification
log "--- Backup Status ---"
LAST_BACKUP=$(ls -t /var/log/vzdump/ 2>/dev/null | head -1)
if [ -n "$LAST_BACKUP" ]; then
    check_pass "Last backup log: $LAST_BACKUP"
else
    check_fail "No backup logs found"
fi

# 9. CPU e RAM capacity
log "--- Capacity ---"
CPU_FREE=$(mpstat 1 1 | awk '/Average/{print $NF}')
check_pass "CPU idle: ${CPU_FREE}%"

MEM_FREE_PCT=$(free | awk '/Mem/{printf "%.0f", ($4/$2)*100}')
if [ "$MEM_FREE_PCT" -gt 30 ]; then
    check_pass "Free RAM: ${MEM_FREE_PCT}%"
else
    check_fail "Free RAM: ${MEM_FREE_PCT}% — need > 30%"
fi

# Summary
log ""
log "=== SUMMARY ==="
log "PASSED: $PASS"
log "FAILED: $FAIL"
if [ "$FAIL" -gt 0 ]; then
    log "STATUS: NOT READY — fix $FAIL issues before cutover"
    exit 1
else
    log "STATUS: READY for cutover"
    exit 0
fi
```

#### Verifica backup VMware (sorgente)

```bash
# Su vCenter/ESXi — verificare ultimo backup
# Con Veeam Backup & Replication (esempio):
Get-VBRBackup | Where-Object {$_.JobType -eq "Backup"} | 
    Select-Object Name, LastBackupTime, LastResult |
    Sort-Object LastBackupTime -Descending

# Con VMware native (VADP):
vim-cmd vmsvc/snapshot.get <vmid>

# Verifica integrity dei backup
# Per ogni VM critica, eseguire restore test in lab
```

#### Verifica inventory e dipendenze

```bash
# Inventory freeze — esportare lista VM definitiva
# Su Proxmox (destinazione), verificare che tutte le VM migrated siano presenti:

echo "=== VM Inventory Check ==="
echo "VMID | Name | Status | Node | Memory | Disk"
echo "-----+------+--------+------+--------+-----"
for VMID in $(qm list | awk 'NR>1{print $1}'); do
    NAME=$(qm config "$VMID" | awk -F: '/^name:/{print $2}' | xargs)
    STATUS=$(qm status "$VMID" | awk '{print $2}')
    NODE=$(pvesh get /cluster/resources --type vm 2>/dev/null | \
           python3 -c "import sys,json; [print(r['node']) for r in json.load(sys.stdin) if r.get('vmid')==$VMID]" 2>/dev/null || echo "?")
    MEM=$(qm config "$VMID" | awk -F: '/^memory:/{print $2}' | xargs)
    echo "$VMID | $NAME | $STATUS | $NODE | ${MEM}MB"
done
```

#### DNS TTL reduction

```bash
# Ridurre TTL a 300s (5 min) almeno 48h prima del cutover
# Questo e CRITICO: se il TTL e ancora 3600s durante il cutover,
# il DNS flip richiede fino a 1h per propagare.

# Esempio zona DNS (BIND):
; PRIMA (TTL alto, produzione normale)
app.example.com.    3600    IN  A    10.0.1.100  ; VMware
db.example.com.     3600    IN  A    10.0.1.101  ; VMware
api.example.com.    3600    IN  A    10.0.1.102  ; VMware

; DOPO (TTL ridotto, T-48h prima del cutover)
app.example.com.     300    IN  A    10.0.1.100  ; VMware (TTL 5min)
db.example.com.      300    IN  A    10.0.1.101  ; VMware (TTL 5min)
api.example.com.     300    IN  A    10.0.1.102  ; VMware (TTL 5min)

# Verifica che il TTL sia effettivamente propagato:
dig +short +ttlid app.example.com @8.8.8.8
dig +short +ttlid app.example.com @1.1.1.1
dig +short +ttlid app.example.com @208.67.222.222

# PowerDNS (se usato come authoritative):
pdnsutil set-meta example.com SOA-EDIT INCREMENT-WEEKS
pdnsutil rectify-zone example.com
```

#### Tabletop exercise (T-14g)

Il tabletop exercise e una simulazione del cutover senza toccare sistemi reali. Dura 3-4 ore e coinvolge tutti i lead.

**Struttura del tabletop:**

```
Durata: 3-4 ore
Partecipanti: tutti i lead + sponsor (opzionale osservatore)
Facilitatore: Cutover Lead

Fase 1 — Walkthrough (1h):
  Cutover Lead legge ogni step del runbook. Per ogni step:
  - "Chi lo esegue?"
  - "Quanto tempo?"
  - "Cosa puo andare storto?"
  - "Come verifichi che e andato bene?"

Fase 2 — Scenario injection (1.5h):
  Cutover Lead inietta scenari di failure ogni 15 min:
  
  Scenario A: "La sync finale sta al 97% da 20 min. Che fate?"
  Scenario B: "La VM del DB non bootra su Proxmox. Errore: 
               kvm: failed to initialize KVM. Che fate?"
  Scenario C: "Il smoke test passa, ma le latenze sono 3x baseline."
  Scenario D: "Lo sponsor chiama e chiede 'e tutto ok?' mentre 
               siete nel mezzo di un troubleshooting."
  Scenario E: "DNS propagation: solo 60% dopo 30 min. Che fate?"
  Scenario F: "Un membro del team e troppo stanco alle 3am e 
               commette un errore di configurazione."
  Scenario G: "Il load balancer risponde 502 per il 5% delle request."
  Scenario H: "Un cliente VIP segnala problemi alle 4am."

Fase 3 — Debrief (30 min):
  - Cosa ha funzionato nel piano?
  - Dove ci siamo bloccati?
  - Quali step mancano nel runbook?
  - Quali decision points non sono chiari?
  
Output:
  - Lista di azioni correttive (owner + due date)
  - Runbook aggiornato con fix
  - Eventuali scenari aggiunti al rollback plan
```

### 2.3 T-7 giorni: freeze window

#### Code freeze enforcement

```bash
# Template email code freeze
Subject: [MANDATORY] Code Freeze — Effective <DATE> until <DATE>

All teams,

Effective immediately, a CODE FREEZE is in place for all production 
systems in scope of the VMware → Proxmox cutover.

PROHIBITED until T0+48h:
- Application deployments
- Configuration changes
- Database schema changes
- Network changes
- Security patching (unless critical CVE)
- New VM provisioning

EXCEPTIONS (require Cutover Lead approval):
- P1/Critical production incidents
- Security vulnerabilities with active exploitation

Violation of code freeze will result in cutover postponement.

Process for exceptions:
1. Email cutover-lead@example.com with justification
2. Wait for written approval
3. Document the change in the Change Record
```

#### Final delta sync

```bash
# Script per sync finale VMware → Proxmox
# Da eseguire su ogni VM in scope

#!/bin/bash
# final-delta-sync.sh — eseguire a T-7g e T-1g
set -euo pipefail

SYNC_LOG="/var/log/cutover-sync-$(date +%Y%m%d).log"

# Per VM con disk su storage condiviso (NFS/iSCSI):
# rsync incrementale del disk file

sync_vm() {
    local VMID=$1
    local SOURCE_PATH=$2
    local DEST_PATH=$3
    
    echo "[$(date)] Syncing VMID $VMID..." | tee -a "$SYNC_LOG"
    
    # Calcola dimensione delta
    DELTA_SIZE=$(rsync -avnc --stats "$SOURCE_PATH" "$DEST_PATH" 2>/dev/null | \
                 grep "Total transferred file size" | awk '{print $5}')
    echo "  Delta size: $DELTA_SIZE bytes" | tee -a "$SYNC_LOG"
    
    # Sync
    rsync -avP --checksum "$SOURCE_PATH" "$DEST_PATH" 2>&1 | tee -a "$SYNC_LOG"
    
    # Verify
    SOURCE_MD5=$(md5sum "$SOURCE_PATH" | awk '{print $1}')
    DEST_MD5=$(md5sum "$DEST_PATH" | awk '{print $1}')
    
    if [ "$SOURCE_MD5" = "$DEST_MD5" ]; then
        echo "  [OK] Checksums match" | tee -a "$SYNC_LOG"
    else
        echo "  [FAIL] Checksum mismatch!" | tee -a "$SYNC_LOG"
        return 1
    fi
}

# Per VM migrate con qemu-img convert (raw/qcow2):
sync_vm_qemu() {
    local VMID=$1
    local SOURCE_VMDK=$2
    local DEST_STORAGE="local-zfs"
    
    echo "[$(date)] Converting VMID $VMID from VMDK..." | tee -a "$SYNC_LOG"
    
    # Importa il disco nel formato Proxmox
    qm importdisk "$VMID" "$SOURCE_VMDK" "$DEST_STORAGE" --format qcow2 \
        2>&1 | tee -a "$SYNC_LOG"
    
    echo "  [OK] Import complete" | tee -a "$SYNC_LOG"
}
```

#### Rollback drill (T-7g o T-3g)

Il rollback deve essere **testato**, non solo documentato. Procedura:

```bash
# In ambiente LAB (clone dell'ambiente di produzione)

# 1. Simulare il cutover completo
#    - Spegnere VM su "VMware lab"
#    - Avviare VM su "Proxmox lab"
#    - Verificare funzionamento

# 2. Simulare un failure
#    - Iniettare un problema (es: kill del processo applicativo)
#    - Attendere che il monitoring rilevi il problema
#    - Chiamare "ROLLBACK" come da procedura

# 3. Eseguire il rollback
#    - Spegnere VM su Proxmox lab
#    - Riavviare VM su VMware lab
#    - Verificare funzionamento post-rollback

# 4. Misurare i tempi
ROLLBACK_START=$(date +%s)

# ... esecuzione rollback ...

ROLLBACK_END=$(date +%s)
ROLLBACK_DURATION=$(( ROLLBACK_END - ROLLBACK_START ))
echo "Rollback completed in ${ROLLBACK_DURATION} seconds"
# Se > 90 min, il rollback plan va ottimizzato

# 5. Documentare
echo "Rollback drill results:" > /tmp/rollback-drill-results.txt
echo "  Date:     $(date)" >> /tmp/rollback-drill-results.txt
echo "  Duration: ${ROLLBACK_DURATION}s" >> /tmp/rollback-drill-results.txt
echo "  Status:   PASS/FAIL" >> /tmp/rollback-drill-results.txt
echo "  Issues:   ..." >> /tmp/rollback-drill-results.txt
```

### 2.4 T-1 giorno: GO/NO-GO meeting

#### Agenda strutturata (2 ore)

```
GO/NO-GO Meeting — Production Cutover
Date: <T-1 date>
Duration: 2 hours
Chair: Cutover Lead
Attendees: All leads + Sponsor

AGENDA:

1. [10 min] Cutover Lead: overall readiness assessment
   - Preflight results (automated checks)
   - Open issues from risk register
   - Team readiness (rest, availability, backup personnel)

2. [10 min] Storage Lead: data readiness
   - Last sync status (delta size, time)
   - Backup verification (VMware side)
   - Proxmox storage health + capacity
   - Restore test results

3. [10 min] Network Lead: network readiness
   - DNS TTL confirmed reduced
   - VLAN/firewall rules verified
   - Load balancer configuration ready
   - VPN tunnels (if applicable)
   - Bandwidth capacity check

4. [10 min] App Lead: application readiness
   - Dependency map verified
   - Smoke test scripts ready and tested
   - Business metric baseline documented
   - Application team contacts confirmed

5. [10 min] Comms Lead: communication readiness
   - Stakeholder notifications sent (T-7)
   - Help desk briefed
   - Status update template ready
   - Escalation path confirmed
   - External client notifications (if applicable)

6. [15 min] Open issue review
   - Each open issue: status, mitigation, owner
   - RED FLAG: any new issue discovered after T-7?

7. [10 min] Rollback readiness
   - Rollback drill results (date, duration, issues)
   - Rollback trigger criteria confirmed
   - Decision authority chain confirmed

8. [15 min] Weather check
   - Team energy level (honest assessment)
   - External factors (weather for on-site, network outages, vendor issues)
   - Sponsor availability during window
   - Backup personnel identified for each role

9. [10 min] GO/NO-GO decision
   Sponsor polls each lead:
   "Are you GO or NO-GO? State your confidence level 1-5."

   GO = ALL leads GO with confidence >= 3
   NO-GO = ANY lead NO-GO, or ANY lead confidence < 2
   CONDITIONAL = Some leads at 2; discuss conditions

10. [10 min] If GO: final logistics
    - War room location/URL
    - Check-in time (1h before T0)
    - Equipment check (laptops charged, VPN tested, snacks)
```

#### GO/NO-GO decision matrix

```
| Area | Criterio | Status | Lead |
|------|----------|--------|------|
| Cluster | pvecm status = Quorate, all nodes online | [ ] | Storage |
| Ceph | ceph health = HEALTH_OK | [ ] | Storage |
| Backup | Full backup VMware verified, restore tested | [ ] | Storage |
| Capacity | CPU < 70%, RAM < 70%, storage < 70% | [ ] | Storage |
| DNS | TTL = 300s, verified on 3 external resolvers | [ ] | Network |
| Network | All VLANs, firewalls, LB configs deployed | [ ] | Network |
| Apps | Smoke test scripts tested in lab | [ ] | App |
| Apps | Business metric baseline documented | [ ] | App |
| Comms | Stakeholders notified, help desk briefed | [ ] | Comms |
| Rollback | Rollback drill completed, < 90 min | [ ] | Cutover |
| Rollback | Rollback trigger criteria agreed | [ ] | Cutover |
| Team | All leads confirmed available | [ ] | Cutover |
| Team | Backup personnel identified | [ ] | Cutover |
| Sponsor | Written GO authorization | [ ] | Sponsor |
```

**Output del meeting:**
- Verbale firmato digitalmente da Sponsor e tutti i lead;
- Se NO-GO: timeline rinviata (minimo 1 settimana), root cause analysis, comms a stakeholder entro 24h;
- Se GO: conferma orario war room opening, last check-in call 1h prima di T0.

---

## 3. Roles e responsibilities

### 3.1 RACI matrix

```
R = Responsible, A = Accountable, C = Consulted, I = Informed

| Attivita                    | Cutover Lead | Network | Storage | App  | Comms | Sponsor |
|-----------------------------|-------------|---------|---------|------|-------|---------|
| Cutover plan                | A,R         | C       | C       | C    | C     | I       |
| Risk register               | A,R         | R       | R       | R    | I     | I       |
| Communication plan          | A           | I       | I       | I    | R     | I       |
| DNS TTL reduction           | A           | R       | I       | I    | I     | I       |
| Tabletop exercise           | A,R         | R       | R       | R    | R     | I       |
| GO/NO-GO decision           | R           | C       | C       | C    | C     | A       |
| Traffic drain               | A           | R       | I       | C    | I     | I       |
| Final sync                  | A           | I       | R       | I    | I     | I       |
| VM shutdown VMware          | A           | I       | R       | C    | I     | I       |
| VM boot Proxmox             | A           | I       | R       | C    | I     | I       |
| DNS/VIP flip                | A           | R       | I       | I    | I     | I       |
| Smoke test                  | A           | I       | I       | R    | I     | I       |
| Status updates              | I           | I       | I       | I    | A,R   | I       |
| Decision point evaluation   | A,R         | C       | C       | C    | I     | C       |
| Rollback decision           | R           | C       | C       | C    | I     | A       |
| Rollback execution          | A,R         | R       | R       | R    | R     | I       |
| Post-cutover validation     | A           | R       | R       | R    | I     | I       |
| Decommissioning             | A           | R       | R       | C    | R     | A       |
```

### 3.2 Profilo dettagliato per ruolo

#### Cutover Lead

**Seniority minima:** 10+ anni IT, 5+ migrazioni enterprise.

**Responsabilita nel dettaglio:**
- Owner del runbook: conosce ogni step, l'ha eseguito in lab;
- Decision maker primario durante la finestra;
- Gestisce timing: "stiamo dentro? siamo in ritardo?";
- Unico a poter dichiarare ROLLBACK (con escalation a Sponsor per casi ambigui);
- Non esegue step tecnici (delega) — osserva e decide;
- Tiene il runbook tracker aggiornato in tempo reale.

**Anti-pattern da evitare:**
- Cutover Lead che "aiuta" eseguendo step → perde visione d'insieme;
- Cutover Lead che comunica direttamente con stakeholder → perde focus;
- Cutover Lead che ignora i decision point timer → decisioni tardive.

#### Network Lead

**Responsabilita specifiche:**
- DNS TTL management (pre e post-cutover);
- Load balancer reconfiguration (VIP flip);
- Firewall rule deployment (Proxmox-side);
- VLAN tagging verification;
- VPN tunnel verification (se multi-site);
- Bandwidth monitoring durante cutover.

**Checklist pre-cutover:**

```bash
# Verifiche Network Lead

# 1. DNS TTL
dig +ttlonly app.example.com @8.8.8.8

# 2. Load balancer health
curl -s https://lb.example.com/api/v1/stats | jq '.backend_servers'

# 3. Firewall rules (Proxmox)
for NODE in pve1 pve2 pve3; do
    echo "=== $NODE ==="
    ssh root@$NODE "pve-firewall status"
    ssh root@$NODE "iptables -L -n --line-numbers | head -30"
done

# 4. VLAN connectivity
for VLAN in 10 20 30 100; do
    ping -c 3 -W 2 10.${VLAN}.0.1 && echo "VLAN $VLAN: OK" || echo "VLAN $VLAN: FAIL"
done

# 5. Bandwidth test (tra nodi)
iperf3 -c pve2 -t 10 -P 4
```

#### Storage Lead

**Responsabilita specifiche:**
- Final delta sync VMware → Proxmox;
- Data integrity verification (checksums, row counts);
- Proxmox storage health monitoring;
- VM boot su Proxmox (ordine e timing);
- Storage performance post-boot (IOPS, latency);
- Backup verification su entrambi i lati.

**Checklist pre-cutover:**

```bash
# Verifiche Storage Lead

# 1. Ceph status
ceph -s
ceph osd tree
ceph df

# 2. ZFS pool status (se usato)
zpool status
zpool list

# 3. Storage Proxmox
pvesm status

# 4. IOPS baseline (raccogliere pre-cutover come reference)
for POOL in $(ceph osd pool ls); do
    echo "=== Pool: $POOL ==="
    ceph osd pool stats "$POOL"
done

# 5. Verify VM disk images
for VMID in $(qm list | awk 'NR>1{print $1}'); do
    echo "=== VM $VMID ==="
    qm config "$VMID" | grep -E "^(scsi|ide|virtio|sata)[0-9]"
done
```

#### App Lead

**Responsabilita specifiche:**
- Smoke test design e esecuzione;
- Business metric baseline e validazione;
- Application log monitoring;
- Database integrity checks;
- Comunicazione con team applicativi;
- User acceptance validation.

**Smoke test script template:**

```bash
#!/bin/bash
# smoke-test.sh — da eseguire dopo boot VM su Proxmox
set -euo pipefail

RESULTS_FILE="/tmp/smoke-test-$(date +%Y%m%d-%H%M%S).json"
PASS=0
FAIL=0
TESTS=()

test_result() {
    local name=$1 status=$2 detail=$3
    TESTS+=("{\"name\":\"$name\",\"status\":\"$status\",\"detail\":\"$detail\"}")
    if [ "$status" = "PASS" ]; then ((PASS++)); else ((FAIL++)); fi
    echo "  [$status] $name: $detail"
}

echo "=== SMOKE TEST START ==="

# 1. Web application reachable
HTTP_CODE=$(curl -sk -o /dev/null -w "%{http_code}" https://app.example.com/health)
if [ "$HTTP_CODE" = "200" ]; then
    test_result "web_health" "PASS" "HTTP $HTTP_CODE"
else
    test_result "web_health" "FAIL" "HTTP $HTTP_CODE"
fi

# 2. API endpoint
API_RESPONSE=$(curl -sk -w "\n%{time_total}" https://api.example.com/v1/status)
API_TIME=$(echo "$API_RESPONSE" | tail -1)
API_BODY=$(echo "$API_RESPONSE" | head -1)
if echo "$API_BODY" | jq -e '.status == "ok"' &>/dev/null; then
    test_result "api_status" "PASS" "OK, ${API_TIME}s"
else
    test_result "api_status" "FAIL" "Response: $API_BODY"
fi

# 3. Database connectivity
DB_CHECK=$(mysql -h db.example.com -u monitor -p"${DB_PASS}" \
    -e "SELECT COUNT(*) as cnt FROM information_schema.tables" -s -N 2>&1)
if [ $? -eq 0 ]; then
    test_result "db_connect" "PASS" "Tables: $DB_CHECK"
else
    test_result "db_connect" "FAIL" "$DB_CHECK"
fi

# 4. Database row count verification
EXPECTED_ROWS=1234567  # dal baseline
ACTUAL_ROWS=$(mysql -h db.example.com -u monitor -p"${DB_PASS}" \
    -e "SELECT COUNT(*) FROM main_table" -s -N 2>&1)
DIFF=$(( ACTUAL_ROWS - EXPECTED_ROWS ))
if [ ${DIFF#-} -lt 100 ]; then  # tolleranza 100 righe
    test_result "db_rowcount" "PASS" "Expected: $EXPECTED_ROWS, Actual: $ACTUAL_ROWS"
else
    test_result "db_rowcount" "FAIL" "Expected: $EXPECTED_ROWS, Actual: $ACTUAL_ROWS, Diff: $DIFF"
fi

# 5. Redis/cache
REDIS_PING=$(redis-cli -h cache.example.com ping 2>&1)
if [ "$REDIS_PING" = "PONG" ]; then
    test_result "redis" "PASS" "PONG"
else
    test_result "redis" "FAIL" "$REDIS_PING"
fi

# 6. Mail relay
SMTP_CHECK=$(echo "EHLO test" | nc -w 5 mail.example.com 25 | head -1)
if echo "$SMTP_CHECK" | grep -q "220"; then
    test_result "smtp" "PASS" "SMTP responsive"
else
    test_result "smtp" "FAIL" "$SMTP_CHECK"
fi

# 7. SSL certificate validity
CERT_DAYS=$(echo | openssl s_client -connect app.example.com:443 -servername app.example.com 2>/dev/null | \
    openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
if [ -n "$CERT_DAYS" ]; then
    test_result "ssl_cert" "PASS" "Expires: $CERT_DAYS"
else
    test_result "ssl_cert" "FAIL" "Cannot read certificate"
fi

# 8. DNS resolution from Proxmox
RESOLVED_IP=$(dig +short app.example.com @8.8.8.8)
EXPECTED_IP="10.1.1.100"  # Proxmox IP
if [ "$RESOLVED_IP" = "$EXPECTED_IP" ]; then
    test_result "dns_resolution" "PASS" "Resolved to $RESOLVED_IP (Proxmox)"
else
    test_result "dns_resolution" "FAIL" "Resolved to $RESOLVED_IP, expected $EXPECTED_IP"
fi

# Summary
echo ""
echo "=== SMOKE TEST SUMMARY ==="
echo "PASSED: $PASS"
echo "FAILED: $FAIL"
echo "TOTAL:  $((PASS + FAIL))"

# JSON output
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"passed\":$PASS,\"failed\":$FAIL,\"tests\":[$(IFS=,; echo "${TESTS[*]}")]}" > "$RESULTS_FILE"
echo "Results saved to $RESULTS_FILE"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
```

#### Comms Lead

**Responsabilita specifiche:**
- Status update ogni 30 min durante il cutover;
- Filtro tra team tecnico e stakeholder;
- Help desk coordination;
- Escalation management;
- Documentazione real-time del timeline effettivo;
- Post-cutover notification a utenti.

**Regole fondamentali:**
1. Il Comms Lead NON interrompe il team tecnico per raccogliere info;
2. Il Comms Lead osserva la dashboard, legge il runbook tracker, e compone il messaggio;
3. Se un manager chiama durante il cutover, il Comms Lead gestisce;
4. Se il Comms Lead ha bisogno di info specifica, aspetta un momento di pausa del team.

#### On-call Engineer(s)

**Responsabilita:**
- Esecuzione materiale degli step tecnici sotto direzione dei lead;
- Monitoring dashboard durante tutta la finestra;
- Troubleshooting first-responder;
- Documentazione comandi eseguiti (timestamp + output).

**Requisiti:**
- Ha eseguito lo stesso cutover in lab almeno 2 volte;
- Ha accesso root/admin a tutti i sistemi in scope;
- Ha i contatti di emergenza dei vendor (Proxmox, network, storage).

---

## 4. Cutover execution

### 4.1 War room setup

#### War room fisico

```
Layout:
+---------------------------------------------------+
|  [MAIN SCREEN]  Dashboard monitoring               |
|  [SCREEN 2]     Runbook tracker (Google Sheet live) |
|  [SCREEN 3]     VM status / Proxmox GUI            |
+---------------------------------------------------+
|                                                     |
|  [Cutover Lead]      [Network Lead]                |
|       desk                desk                      |
|                                                     |
|  [Storage Lead]      [App Lead]                    |
|       desk                desk                      |
|                                                     |
|  [Comms Lead]        [On-call Eng]                 |
|       desk                desk                      |
|                                                     |
+---------------------------------------------------+
|  SUPPLIES: coffee, water, snacks, power strips,    |
|  whiteboard, printed runbook, printed contacts     |
+---------------------------------------------------+
```

**Checklist war room:**
- [ ] Schermi: dashboard monitoring visibile a tutti;
- [ ] Rete: WiFi separato + cablato backup;
- [ ] Alimentazione: UPS per tutti i laptop;
- [ ] Comunicazione: Slack channel aperto, Zoom backup;
- [ ] Documentazione: runbook stampato (in caso di failure del laptop);
- [ ] Contatti: lista stampata di numeri di emergenza;
- [ ] Comfort: caffe, acqua, snack, riscaldamento/condizionamento;
- [ ] Orario: wall clock sincronizzato con NTP.

#### War room virtuale (remote)

```
Strumenti:
- Zoom/Teams: sempre aperto, video ON per tutti i lead
- Slack #cutover-execution: comandi, output, decision log
- Slack #cutover-status: solo Comms Lead scrive (stakeholder leggono)
- Google Sheet: runbook tracker live (tutti editano la propria riga)
- Grafana dashboard: URL condiviso, tutti vedono le stesse metriche
- PagerDuty/Opsgenie: on-call routing durante la finestra

Regole:
- Mute di default, unmute per comunicare
- Usare il nome: "Storage Lead: sync completata, passo a Network Lead"
- Nessun side-channel: tutta la comunicazione in war room
- Screenshot ogni 30 min della dashboard (evidence chain)
```

### 4.2 T0 — Cutover timeline dettagliato

Esempio per cutover sabato notte 22:00 → domenica mattina 06:00.

```
PRE-T0:
  21:00  Team check-in. Verifica accesso a tutti i sistemi.
         Verifica che tutti abbiano cenato e siano riposati.
         Ultimo health check automatizzato (script preflight).

  21:30  War room officially opens.
         Cutover Lead: "War room open. Runbook version X.Y."
         Comms Lead: screenshot di tutti i monitoring dashboard (baseline).
         
  21:45  Comms Lead: notifica a stakeholder "Maintenance window starting in 15 min."
         Help desk: attiva la pagina di maintenance.

CUTOVER EXECUTION:

T+00:00 [22:00] === CUTOVER START ===
         Cutover Lead: "T0. Cutover started. War room active."
         Comms Lead: "Cutover started" su #cutover-status.
         
T+00:05  Network Lead: mette load balancer in DRAIN mode.
         # HAProxy:
         echo "set server backend_vmware/srv1 state drain" | \
             socat stdio /var/lib/haproxy/admin.sock
         # oppure F5:
         # tmsh modify ltm pool pool_app members { 10.0.1.100:443 { state user-down } }
         
T+00:10  Network Lead: conferma drain. In-flight request counter:
         echo "show stat" | socat stdio /var/lib/haproxy/admin.sock | \
             awk -F, '/backend_vmware/{print $5" current connections"}'
         Attende fino a 0 connections (max 10 min).

T+00:15  Network Lead: conferma "Zero in-flight. Traffic drained."
         Cutover Lead: "Proceed to VM shutdown."

T+00:20  App Lead: graceful shutdown delle applicazioni su VMware.
         Per ogni VM, in ordine:
         
         # 1. Web/frontend servers (interrompono prima le connessioni utente)
         for VM in web01 web02 web03; do
             ssh $VM "sudo systemctl stop nginx && sudo systemctl stop app-service"
             echo "[$(date)] $VM: app stopped" >> /tmp/cutover-log.txt
         done
         
         # 2. App servers
         for VM in app01 app02; do
             ssh $VM "sudo systemctl stop backend-service"
             echo "[$(date)] $VM: app stopped" >> /tmp/cutover-log.txt
         done
         
         # 3. Database (LAST to stop)
         ssh db01 "sudo systemctl stop mysql"
         ssh db01 "sudo sync"  # flush buffers
         echo "[$(date)] db01: MySQL stopped, buffers flushed" >> /tmp/cutover-log.txt

T+00:30  Storage Lead: ferma la replicazione, esegue final delta sync.
         # Se CBT (Changed Block Tracking) attivo:
         # La sync cattura solo i blocchi modificati dall'ultimo sync
         
         echo "[$(date)] Starting final delta sync..."
         
         # Esempio con Proxmox replication via ZFS:
         # (se i dischi sono gia stati pre-migrati come ZFS volumes)
         zfs send -i @presync pool/vm-disk-100 | \
             ssh proxmox-node "zfs receive tank/vm-disk-100"
         
         echo "[$(date)] Delta sync completed"
         
T+00:40  Storage Lead: verifica integrita dati.
         # Checksum dei disk images:
         md5sum /dev/zvol/tank/vm-disk-100 > /tmp/checksum-proxmox.txt
         # Confronto con checksum VMware (preso pre-shutdown):
         diff /tmp/checksum-vmware.txt /tmp/checksum-proxmox.txt
         
         # Row count per database:
         echo "SELECT table_name, table_rows FROM information_schema.tables 
               WHERE table_schema='production'" | mysql -h db01-vmware > /tmp/rowcount-vmware.txt
         # (confronto post-boot su Proxmox)

T+00:45  Storage Lead: confirma "Data parity verified. Ready for boot."
         Comms Lead: status update #1.
         
T+00:50  === VM BOOT SU PROXMOX ===
         Storage Lead + On-call: boot VM in ordine di dipendenza.

         # Ordine di boot (tier 0 → tier 3):
         
         # Tier 0: Infrastructure (DNS, AD, NTP)
         TIER0="101 102 103"
         for VMID in $TIER0; do
             echo "[$(date)] Booting VMID $VMID (Tier 0: infra)..."
             qm start "$VMID"
             # Wait for QEMU Guest Agent
             timeout 120 bash -c "until qm agent $VMID ping 2>/dev/null; do sleep 5; done"
             echo "[$(date)] VMID $VMID: running, agent responsive"
         done
         
         # Tier 1: Database
         TIER1="110 111"
         for VMID in $TIER1; do
             echo "[$(date)] Booting VMID $VMID (Tier 1: database)..."
             qm start "$VMID"
             timeout 180 bash -c "until qm agent $VMID ping 2>/dev/null; do sleep 5; done"
             # Verify database is accepting connections
             timeout 120 bash -c "until mysql -h \$(qm agent $VMID network-get-interfaces | \
                 jq -r '.[1].\"ip-addresses\"[0].\"ip-address\"') -u monitor -p'${DB_PASS}' \
                 -e 'SELECT 1' 2>/dev/null; do sleep 10; done"
             echo "[$(date)] VMID $VMID: database accepting connections"
         done
         
         # Tier 2: Application servers
         TIER2="120 121 122"
         for VMID in $TIER2; do
             echo "[$(date)] Booting VMID $VMID (Tier 2: app)..."
             qm start "$VMID"
             timeout 120 bash -c "until qm agent $VMID ping 2>/dev/null; do sleep 5; done"
         done
         
         # Tier 3: Web/frontend + utility
         TIER3="130 131 132 140 141"
         for VMID in $TIER3; do
             echo "[$(date)] Booting VMID $VMID (Tier 3: web/util)..."
             qm start "$VMID"
             timeout 120 bash -c "until qm agent $VMID ping 2>/dev/null; do sleep 5; done"
         done
         
T+01:30  Cutover Lead: "All VM running on Proxmox. Status?"
         Storage Lead: "All VM up, guest agents responsive."
         
T+01:35  App Lead: smoke test critical paths.
         ./smoke-test.sh | tee /tmp/smoke-test-cutover.log
         
         # Se smoke test FAIL:
         #   - Identify failing test
         #   - Can we fix in < 30 min?
         #     YES → fix, re-run smoke
         #     NO  → escalate to Cutover Lead for rollback decision
         
T+02:00  Comms Lead: status update #2.
         "Cutover 60% — VM running on Proxmox, smoke testing in progress."

T+02:00  Network Lead: DNS flip.
         
         # Aggiornare i record DNS per puntare ai nuovi IP Proxmox:
         
         # Con nsupdate (BIND dynamic):
         nsupdate -k /etc/bind/keys/update.key <<EOF
         server ns1.example.com
         zone example.com
         update delete app.example.com. A
         update add app.example.com. 300 A 10.1.1.100
         update delete api.example.com. A
         update add api.example.com. 300 A 10.1.1.101
         update delete db.example.com. A
         update add db.example.com. 300 A 10.1.1.110
         send
         EOF
         
         # Con PowerDNS API:
         curl -X PATCH http://ns1.example.com:8081/api/v1/servers/localhost/zones/example.com \
             -H "X-API-Key: ${PDNS_API_KEY}" \
             -H "Content-Type: application/json" \
             -d '{
               "rrsets": [
                 {"name": "app.example.com.", "type": "A", "ttl": 300,
                  "changetype": "REPLACE",
                  "records": [{"content": "10.1.1.100", "disabled": false}]},
                 {"name": "api.example.com.", "type": "A", "ttl": 300,
                  "changetype": "REPLACE",
                  "records": [{"content": "10.1.1.101", "disabled": false}]}
               ]
             }'
         
         # Verifica propagazione:
         for RESOLVER in 8.8.8.8 1.1.1.1 208.67.222.222 9.9.9.9; do
             echo "Resolver $RESOLVER:"
             dig +short app.example.com @$RESOLVER
         done

T+02:15  Network Lead: load balancer redirect al backend Proxmox.
         
         # HAProxy: attivare il backend Proxmox
         echo "set server backend_proxmox/srv1 state ready" | \
             socat stdio /var/lib/haproxy/admin.sock
         
         # Verify backend health
         echo "show stat" | socat stdio /var/lib/haproxy/admin.sock | \
             awk -F, '/backend_proxmox/{print $2, $18}'
         
T+02:30  Comms Lead: status update #3.
         "Cutover 75% — DNS flipped, monitoring traffic flow."

T+02:30  === SOAK TEST START (1h) ===
         Monitoring passivo: tutti osservano le dashboard.
         
         # Script di monitoring continuo durante soak:
         #!/bin/bash
         # soak-monitor.sh — eseguire in background durante soak test
         while true; do
             TIMESTAMP=$(date '+%H:%M:%S')
             
             # CPU cluster
             CPU=$(pvesh get /cluster/resources --type node 2>/dev/null | \
                   python3 -c "import sys,json; nodes=json.load(sys.stdin); \
                   print(f'{sum(n[\"cpu\"]*100 for n in nodes)/len(nodes):.1f}%')" 2>/dev/null)
             
             # HTTP response time
             HTTP_TIME=$(curl -sk -o /dev/null -w "%{time_total}" https://app.example.com/ 2>/dev/null)
             
             # Error rate (from app log)
             ERROR_COUNT=$(ssh app01 "grep -c ERROR /var/log/app/current.log" 2>/dev/null || echo "?")
             
             echo "$TIMESTAMP | CPU: $CPU | HTTP: ${HTTP_TIME}s | Errors: $ERROR_COUNT"
             sleep 60
         done

T+03:00  Comms Lead: status update #4.
T+03:30  Comms Lead: status update #5.
         
T+04:00  === DECISION POINT #1 ===
         (Dettaglio nella sezione Decision Points)
         
         Cutover Lead poll: "Network Lead, GO?" / "Storage Lead, GO?" / 
                           "App Lead, GO?"
         
         If ALL GO → proceed.
         If ANY NO-GO → evaluate rollback.
         
T+04:00  If GO: Cutover Lead "Decision Point 1: GO. Opening production traffic."
         
         # Se il LB era in canary mode, aprire 100%:
         echo "set weight backend_proxmox/srv1 100" | \
             socat stdio /var/lib/haproxy/admin.sock
             
T+04:05  Comms Lead: notifica stakeholder + utenti.
         "Services restored. Monitoring continues."
         Help desk: disattiva pagina maintenance.

T+05:00  === SOAK TEST CONTINUED (1h post-traffic) ===
         Monitoring con traffico reale.
         App Lead: verifica business metrics in tempo reale.
         
         # Business metric check:
         # - Orders per hour vs baseline
         # - Login success rate
         # - API response time p99
         # - Error rate
         
T+05:30  Comms Lead: status update #6.

T+06:00  === DECISION POINT #2 ===
         (Dettaglio nella sezione Decision Points)
         
         If GO → war room released, shift to on-call monitoring.
         If NO-GO → war room remains, evaluate rollback.

T+06:00  If GO: Cutover Lead "Decision Point 2: GO. War room released."
         Comms Lead: "Cutover complete. Monitoring continues. War room closed."
         
         On-call: monitoring 24/7 per 48h.
         Cutover Lead: "Team, get some sleep. On-call takes over."
```

### 4.3 Status update format (ogni 30 min by Comms Lead)

```
Subject: [CUTOVER STATUS] T+X:XX — <RAG color>

TIMESTAMP: YYYY-MM-DD HH:MM UTC
PROGRESS: XX% complete
STATUS: RED | AMBER | GREEN

COMPLETED SINCE LAST UPDATE:
- <items completed with timestamp>

IN PROGRESS:
- <items currently executing + owner>

NEXT 30 MINUTES:
- <planned items>

METRICS:
- CPU cluster avg: XX%
- HTTP response time p99: XXms
- Error rate: X.XX%
- Active connections: XXXX

ISSUES:
- <any open issue + owner + ETA>

DECISION POINTS:
- Next decision point: T+X:XX (<type>)

MOOD: <team energy assessment: energized | steady | fatigued>
```

**Codifica RAG:**

| Colore | Significato | Azione |
|--------|-------------|--------|
| GREEN | On schedule, no issues | Continue |
| AMBER | Minor issue or behind schedule ≤15min | Monitor closely, may need action |
| RED | Major issue or behind ≥30min or smoke test failing | Evaluate rollback, escalate |

### 4.4 Runbook tracker (live document)

```
| # | Step | Owner | Planned | Actual Start | Actual End | Status | Notes |
|---|------|-------|---------|-------------|------------|--------|-------|
| 1 | War room open | CL | 21:30 | | | | |
| 2 | Stakeholder notification | CC | 21:45 | | | | |
| 3 | LB drain mode | NL | 22:00 | | | | |
| 4 | Traffic drain complete | NL | 22:10 | | | | |
| 5 | App shutdown (web) | AL | 22:15 | | | | |
| 6 | App shutdown (app) | AL | 22:20 | | | | |
| 7 | App shutdown (DB) | AL | 22:25 | | | | |
| 8 | Final delta sync | SL | 22:30 | | | | |
| 9 | Data integrity check | SL | 22:40 | | | | |
| 10 | Boot Tier 0 (infra) | SL | 22:50 | | | | |
| 11 | Boot Tier 1 (DB) | SL | 23:00 | | | | |
| 12 | Boot Tier 2 (app) | SL | 23:15 | | | | |
| 13 | Boot Tier 3 (web) | SL | 23:25 | | | | |
| 14 | Smoke test | AL | 23:35 | | | | |
| 15 | DNS flip | NL | 00:00 | | | | |
| 16 | LB redirect | NL | 00:15 | | | | |
| 17 | Soak test start | ALL | 00:30 | | | | |
| 18 | Decision Point #1 | CL | 02:00 | | | | |
| 19 | Open production traffic | NL | 02:05 | | | | |
| 20 | Soak test continued | ALL | 02:05 | | | | |
| 21 | Decision Point #2 | CL | 04:00 | | | | |
| 22 | War room released | CL | 04:00 | | | | |

Legend: CL=Cutover Lead, NL=Network Lead, SL=Storage Lead, AL=App Lead, CC=Comms Lead
Status: PENDING | IN PROGRESS | DONE | SKIPPED | BLOCKED | FAILED
```

---

## 5. Decision points e criteri rollback

### 5.1 Decision Point #1 (after smoke test, ~T+4:00)

**Domanda:** Procedere con traffico di produzione, o rollback?

**GO criteria** (TUTTI devono essere veri):

| # | Criterio | Metodo di verifica | Soglia |
|---|----------|-----|-----|
| 1 | Smoke test | Script automatizzato | 100% pass |
| 2 | CPU cluster | Grafana/Prometheus | < 110% baseline |
| 3 | RAM cluster | Grafana/Prometheus | < 110% baseline |
| 4 | IOPS storage | Ceph/ZFS metrics | < 120% baseline |
| 5 | Network latency | ping/curl p99 | < 120% baseline |
| 6 | Application logs | grep ERROR | < 0.5% error rate |
| 7 | DB row count | SQL count(*) | Match ± 0.01% |
| 8 | DNS propagation | dig da 4 resolver | ≥ 95% pointing to Proxmox |
| 9 | HA status | ha-manager status | No errors |
| 10 | Ceph health | ceph -s | HEALTH_OK |

**NO-GO trigger** (QUALUNQUE singolo trigger attiva la valutazione rollback):

| # | Trigger | Soglia | Azione |
|---|---------|--------|--------|
| 1 | Smoke test failure | 1+ test irrecoverabile | Evaluate fix time vs rollback |
| 2 | CPU/RAM spike | > 150% baseline per 15+ min | Investigate, likely rollback |
| 3 | IOPS degradation | > 200% baseline | Rollback |
| 4 | App error rate | > 1% per 10+ min | Evaluate, likely rollback |
| 5 | DB integrity failure | Row count mismatch > 1% | IMMEDIATE rollback |
| 6 | DNS failure | < 80% propagation dopo 30 min | Investigate DNS, may not need rollback |
| 7 | HA errors | Any HA fence event | Evaluate cluster stability |
| 8 | Ceph degraded | HEALTH_ERR | IMMEDIATE rollback |

**Procedura di decisione:**

```
Cutover Lead:
  1. "Decision Point 1. Polling leads."
  2. "Network Lead: GO or NO-GO?"
  3. "Storage Lead: GO or NO-GO?"
  4. "App Lead: GO or NO-GO?"
  5. Valuta risposte:
     - All GO → "Decision Point 1: GO. Proceeding."
     - Any NO-GO → "What's the issue? Can we fix in 30 min?"
       - YES → set 30-min timer, fix, re-evaluate
       - NO → "Decision Point 1: NO-GO. Initiating rollback."
     - Ambiguous → "Escalating to Sponsor."
       - Call Sponsor: present facts, not opinions
       - Sponsor decides GO or ROLLBACK
```

### 5.2 Decision Point #2 (T+1h post-traffic, ~T+6:00)

**Domanda:** Cutover stabile abbastanza da rilasciare il war room?

**GO criteria** (TUTTI):

| # | Criterio | Soglia |
|---|----------|--------|
| 1 | Production traffic flowing | LB stats show normal request rate |
| 2 | Monitoring stable | No anomalies for 60+ min |
| 3 | Business metrics | ≥ 90% of expected baseline |
| 4 | No critical alerts | Last 60 min clean |
| 5 | User reports | Help desk: no cutover-related tickets |

**NO-GO trigger:**

| # | Trigger | Azione |
|---|---------|--------|
| 1 | Persistent monitoring anomaly | War room stays, investigate |
| 2 | Business metric < 70% expected | Evaluate rollback |
| 3 | Critical alert unresolved > 30 min | Evaluate rollback |
| 4 | User reports of data loss/corruption | IMMEDIATE rollback |

### 5.3 Decision Point #3 (T+24h — nuova, per cutover complessi)

**Domanda:** Confermare permanenza su Proxmox, o rollback tardivo?

Questo decision point e per ambienti con SLA stringenti dove il rollback deve rimanere possibile per 24h.

**GO criteria:**
- 24h di monitoring senza anomalie;
- Business metric stabile (media 24h ≥ 95% baseline);
- Nessun ticket P1 legato al cutover;
- On-call: nessun intervento non previsto.

**Se NO-GO a T+24h:**
- Il rollback tardivo e molto piu costoso (dati accumulati su Proxmox per 24h);
- Richiede sync inversa dei dati (Proxmox → VMware);
- Valutare se il problema e risolvibile senza rollback;
- Sponsor deve approvare il rollback tardivo.

### 5.4 Criteri di rollback automatico

Per evitare decisioni sotto pressione, pre-definire trigger di rollback automatico:

```yaml
# rollback-triggers.yaml — configurazione pre-approvata
# Se uno di questi trigger si attiva, il rollback e AUTOMATICO
# (non richiede decision point)

automatic_rollback:
  - name: "Data corruption detected"
    condition: "DB integrity check fails with data loss"
    action: "IMMEDIATE rollback, no delay"
    
  - name: "Cluster quorum lost"
    condition: "pvecm status shows not quorate"
    action: "IMMEDIATE rollback"
    
  - name: "Total service outage"
    condition: "All smoke tests fail + zero traffic for 10+ min"
    action: "IMMEDIATE rollback"
    
  - name: "Ceph HEALTH_ERR with data at risk"
    condition: "ceph -s shows HEALTH_ERR + degraded PGs > 10%"
    action: "IMMEDIATE rollback"

manual_rollback_evaluation:
  - name: "Performance degradation"
    condition: "IOPS > 200% baseline for 15+ min"
    action: "Cutover Lead evaluates fix vs rollback"
    max_evaluation_time: "30 min"
    
  - name: "Partial service failure"
    condition: "1-2 non-critical services down"
    action: "Cutover Lead evaluates fix vs rollback"
    max_evaluation_time: "60 min"
```

---

## 6. Rollback procedure

### 6.1 Rollback execution timeline

```
ROLLBACK DECLARED: Cutover Lead announces "ROLLBACK. War room stays open."

RB+00:00  Cutover Lead: "Rollback declared at <TIME>. Reason: <REASON>."
          Comms Lead: notify stakeholders immediately.
          "[CUTOVER STATUS] ROLLBACK IN PROGRESS"

RB+00:02  Network Lead: revert DNS to VMware IPs.
          
          # nsupdate (BIND):
          nsupdate -k /etc/bind/keys/update.key <<EOF
          server ns1.example.com
          zone example.com
          update delete app.example.com. A
          update add app.example.com. 300 A 10.0.1.100
          update delete api.example.com. A
          update add api.example.com. 300 A 10.0.1.101
          send
          EOF
          
          # Load balancer: redirect back to VMware
          echo "set server backend_vmware/srv1 state ready" | \
              socat stdio /var/lib/haproxy/admin.sock
          echo "set server backend_proxmox/srv1 state drain" | \
              socat stdio /var/lib/haproxy/admin.sock

RB+00:05  Storage Lead: stop tutte le VM su Proxmox.
          
          for VMID in $(qm list | awk 'NR>1 && $3=="running"{print $1}'); do
              echo "[$(date)] Stopping VMID $VMID..."
              qm shutdown "$VMID" --timeout 60
              # Se non si spegne in 60s, force stop:
              qm status "$VMID" | grep -q running && qm stop "$VMID"
          done

RB+00:10  Storage Lead: sync delta back from Proxmox to VMware.
          # CRITICO: i dati scritti durante il cutover devono essere
          # sincronizzati indietro a VMware
          
          # Se il cutover e durato < 1h e le VM erano in sola lettura,
          # questo step non serve (i dati su VMware sono ancora validi).
          
          # Se ci sono stati write (utenti hanno usato il sistema):
          # Bisogna trasferire i dati delta
          
          # Caso 1: DB — export delta
          ssh proxmox-db01 "mysqldump --where='updated_at >= \"$(date -d '4 hours ago' +%Y-%m-%d\ %H:%M:%S)\"' \
              production > /tmp/delta-dump.sql"
          scp proxmox-db01:/tmp/delta-dump.sql vmware-db01:/tmp/
          ssh vmware-db01 "mysql production < /tmp/delta-dump.sql"
          
          # Caso 2: File storage — rsync delta
          rsync -avP proxmox-fs01:/data/uploads/ vmware-fs01:/data/uploads/

RB+00:20  App Lead: start applicazioni su VMware.
          # Ordine INVERSO al shutdown: DB → app → web
          
          ssh vmware-db01 "sudo systemctl start mysql"
          sleep 30  # wait for DB to accept connections
          
          for VM in vmware-app01 vmware-app02; do
              ssh $VM "sudo systemctl start backend-service"
          done
          sleep 15
          
          for VM in vmware-web01 vmware-web02 vmware-web03; do
              ssh $VM "sudo systemctl start nginx && sudo systemctl start app-service"
          done

RB+00:30  App Lead: smoke test su VMware.
          ./smoke-test-vmware.sh | tee /tmp/rollback-smoke.log

RB+00:45  Network Lead: conferma DNS propagation verso VMware.
          for RESOLVER in 8.8.8.8 1.1.1.1; do
              dig +short app.example.com @$RESOLVER
          done

RB+01:00  Network Lead: load balancer fully on VMware backend.
          echo "show stat" | socat stdio /var/lib/haproxy/admin.sock | \
              awk -F, '/backend/{print $2,$18}'

RB+01:00  App Lead: conferma "VMware environment operational."
          Cutover Lead: "Rollback complete. VMware is serving traffic."

RB+01:30  Comms Lead: notify stakeholders.
          "[CUTOVER STATUS] Rollback complete. Services restored on original platform.
           Investigation underway. New cutover timeline TBD."

RB+02:00  === ROLLBACK MONITORING ===
          On-call: monitoring VMware per 24h.
          Verify all metrics back to pre-cutover baseline.

RB+24h   Root cause analysis meeting.
          - What triggered the rollback?
          - What can we fix before the next attempt?
          - New cutover timeline (minimum 1 week, typically 2-4 weeks)

RB+1w    New cutover plan with mitigations applied.
          Submit to CAB for re-approval.
```

### 6.2 Rollback time limits

```
Regola fondamentale:
  "Se il rollback non e completato entro 90 minuti dalla dichiarazione,
   escalare a Sponsor per valutare opzioni alternative."

Phase timeline:
  0-30 min:  DNS/LB revert + VM shutdown Proxmox
  30-60 min: Data sync back + VM start VMware
  60-90 min: Smoke test + verification

Se > 90 min:
  - Il rollback stesso ha problemi
  - Valutare: fix forward (risolvere su Proxmox) vs continuare rollback
  - Sponsor decide

Caso estremo: se sia Proxmox che VMware non funzionano:
  - DR plan (modulo 19)
  - Restore da backup
  - Questo scenario deve essere prevenuto dal rollback drill pre-cutover
```

### 6.3 Rollback data integrity

Il problema piu complesso del rollback: **i dati scritti durante il cutover**.

```
Scenario timeline:

  22:00  Cutover start
  23:00  VM running su Proxmox
  00:00  DNS flip, traffico su Proxmox
  01:00  Utenti creano dati su Proxmox (ordini, registrazioni, file...)
  02:00  Problema rilevato → ROLLBACK
  
Domanda: i dati creati tra 00:00 e 02:00 su Proxmox, come li portiamo 
         su VMware?

Risposte per tipo di dato:

1. DATABASE (transactional):
   - Export delle transazioni post-cutover da Proxmox
   - Import su VMware (idempotent, con conflict resolution)
   - Verify: count + checksum delle tabelle
   
2. FILE STORAGE:
   - rsync differenziale da Proxmox a VMware
   - Attenzione ai file modificati su entrambi i lati (conflict)
   
3. CACHE (Redis, Memcached):
   - Non serve sync (cache si ricostruisce)
   
4. MESSAGE QUEUE (RabbitMQ, Kafka):
   - Se persistent: export e replay
   - Se transient: lost (accettabile per design)
   
5. SESSIONI UTENTE:
   - Lost (utenti devono rifare login — accettabile)
```

---

## 7. Post-cutover validation

### 7.1 T0+1h: Immediate post-cutover

```bash
#!/bin/bash
# post-cutover-check-1h.sh — eseguire a T0+1h
set -euo pipefail

echo "=== POST-CUTOVER CHECK T0+1h ==="
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# 1. All VM running
echo "--- VM Status ---"
qm list | awk 'NR>1{print $1, $2, $3}' | while read VMID NAME STATUS; do
    if [ "$STATUS" != "running" ]; then
        echo "[ALERT] VMID $VMID ($NAME): $STATUS"
    fi
done

# 2. Cluster health
echo "--- Cluster ---"
pvecm status | grep -E "Quorate|Nodes"

# 3. Ceph (se presente)
if command -v ceph &>/dev/null; then
    echo "--- Ceph ---"
    ceph -s | head -15
fi

# 4. Storage usage
echo "--- Storage ---"
pvesm status

# 5. Network connectivity
echo "--- Network ---"
for HOST in app.example.com api.example.com db.example.com; do
    LATENCY=$(ping -c 3 -W 2 "$HOST" 2>/dev/null | awk -F/ '/avg/{print $5}')
    echo "$HOST: ${LATENCY:-UNREACHABLE}ms"
done

# 6. HTTP checks
echo "--- HTTP ---"
for URL in https://app.example.com/ https://api.example.com/health; do
    CODE=$(curl -sk -o /dev/null -w "%{http_code}" "$URL")
    TIME=$(curl -sk -o /dev/null -w "%{time_total}" "$URL")
    echo "$URL: HTTP $CODE (${TIME}s)"
done

# 7. Load balancer stats
echo "--- Load Balancer ---"
echo "show stat" | socat stdio /var/lib/haproxy/admin.sock 2>/dev/null | \
    awk -F, 'NR>1{print $1,$2,$5,$18}' | head -20
```

### 7.2 T0+24h: First-day validation

Checklist dettagliata per la prima giornata lavorativa post-cutover:

```
MONITORING:
  [ ] Dashboard review: tutte le metriche entro 110% baseline
  [ ] Alert review: nessun alert critico nelle ultime 24h
  [ ] CPU cluster: utilizzo medio e stabile
  [ ] RAM: no memory pressure, no OOM kills
  [ ] Storage IOPS: in linea con baseline
  [ ] Network: no packet loss, latency stabile

BUSINESS METRICS:
  [ ] Orders/hour vs baseline weekday
  [ ] Login success rate >= 99%
  [ ] Transaction volume vs expected
  [ ] API response time p50, p95, p99
  [ ] Error rate < 0.1%

APPLICATION:
  [ ] Error log review (cercare pattern nuovi)
  [ ] Stack trace review (cercare errori sconosciuti)
  [ ] Application performance (APM tool)
  [ ] Cron job execution (tutti eseguiti?)
  [ ] Batch job results (tutti completati?)

USER FEEDBACK:
  [ ] Help desk: ticket count vs normal day
  [ ] Help desk: ticket categories (cutover-related?)
  [ ] Key user survey (informal: "tutto ok?")

INFRASTRUCTURE:
  [ ] Backup: prima notte di backup completata con successo
  [ ] Backup: restore test del backup Proxmox
  [ ] HA: ha-manager status clean
  [ ] Monitoring: tutti gli agent attivi
  [ ] NTP: time sync stabile
  [ ] DNS: TTL puo tornare al valore normale (3600s)

ON-CALL:
  [ ] Coverage 24/7 confermata per 48h
  [ ] Escalation path funzionante
  [ ] Tutti i contatti raggiungibili
```

### 7.3 T0+48h: Soak test extended

```bash
#!/bin/bash
# soak-test-report-48h.sh — generare report dopo 48h
set -euo pipefail

echo "=== SOAK TEST REPORT — 48h POST-CUTOVER ==="
echo "Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Metrics from Prometheus (esempio con promtool/curl)
PROM_URL="http://prometheus.example.com:9090"

echo "=== CPU USAGE (avg last 48h per node) ==="
for NODE in pve1 pve2 pve3; do
    AVG=$(curl -s "${PROM_URL}/api/v1/query?query=avg_over_time(node_cpu_seconds_total{instance=\"${NODE}:9100\",mode=\"idle\"}[48h])" | \
        python3 -c "import sys,json; r=json.load(sys.stdin); print(f'{100-float(r[\"data\"][\"result\"][0][\"value\"][1]):.1f}%')" 2>/dev/null || echo "N/A")
    echo "  $NODE: $AVG"
done

echo ""
echo "=== MEMORY USAGE (max last 48h) ==="
for NODE in pve1 pve2 pve3; do
    MAX=$(curl -s "${PROM_URL}/api/v1/query?query=max_over_time((1-node_memory_MemAvailable_bytes{instance=\"${NODE}:9100\"}/node_memory_MemTotal_bytes{instance=\"${NODE}:9100\"})[48h:])" | \
        python3 -c "import sys,json; r=json.load(sys.stdin); print(f'{float(r[\"data\"][\"result\"][0][\"value\"][1])*100:.1f}%')" 2>/dev/null || echo "N/A")
    echo "  $NODE: $MAX"
done

echo ""
echo "=== ERROR RATE (last 48h) ==="
# Da application metrics (esempio con counter Prometheus)
ERROR_RATE=$(curl -s "${PROM_URL}/api/v1/query?query=sum(rate(http_requests_total{status=~\"5..\"}[48h]))/sum(rate(http_requests_total[48h]))*100" | \
    python3 -c "import sys,json; r=json.load(sys.stdin); print(f'{float(r[\"data\"][\"result\"][0][\"value\"][1]):.3f}%')" 2>/dev/null || echo "N/A")
echo "  5xx error rate: $ERROR_RATE"

echo ""
echo "=== BACKUP STATUS ==="
# Ultimi backup Proxmox
pvesh get /nodes/pve1/tasks --typefilter vzdump --limit 5 --start 0 2>/dev/null | \
    python3 -c "import sys,json; tasks=json.load(sys.stdin); [print(f'  {t[\"starttime\"]} - {t[\"status\"]}') for t in tasks]" 2>/dev/null

echo ""
echo "=== HA EVENTS (last 48h) ==="
journalctl -u pve-ha-lrm --since "48 hours ago" --no-pager | tail -20

echo ""
echo "=== RECOMMENDATION ==="
echo "If all metrics are within baseline and no critical issues:"
echo "  → Confirm cutover success"
echo "  → Begin decommissioning countdown (T0+30d)"
echo "  → Restore DNS TTL to production values (3600s)"
echo "  → Reduce on-call coverage to normal"
```

### 7.4 T0+7d: soak completed

```
Validazione settimanale:

PERFORMANCE TREND:
  [ ] CPU/RAM/IOPS trend stabile (no degradation over 7 days)
  [ ] Response time trend stabile
  [ ] Error rate trend stabile o in calo

RELIABILITY:
  [ ] Backup: 7 backup notturni completati con successo
  [ ] Backup: almeno 1 restore test eseguito
  [ ] HA: test controllato (fence 1 nodo, verifica failover)
  [ ] Monitoring: no false positives, alert threshold tuned

OPERATIONS:
  [ ] Skill transfer session completata (lead → team)
  [ ] Runbook aggiornato con note reali dal cutover
  [ ] Monitoring dashboard personalizzato per Proxmox
  [ ] On-call playbook aggiornato

DECISION:
  [ ] Sponsor approva conferma cutover success
  [ ] Timeline decommissioning confermata (T0+30d)
  [ ] VMware mantenuto offline ma ready per 23 giorni
```

---

## 8. Decommissioning VMware

### 8.1 Prerequisiti (T0+30d)

```
GATE CRITERIA per decommissioning:

  [ ] Cutover stabile per 30 giorni
  [ ] Nessun rollback necessario in 30 giorni
  [ ] Business metrics stabili
  [ ] Sponsor approva per iscritto il decommissioning
  [ ] Legal review: retention dei dati VMware? (compliance)
  [ ] Finance review: impatto su licensing/leasing
```

### 8.2 Procedura di decommissioning

```bash
#!/bin/bash
# vmware-decommission.sh — eseguire SOLO dopo approvazione sponsor

# ATTENZIONE: questo script e IRREVERSIBILE dopo il passo 4.
# Eseguire ogni passo manualmente, verificare, poi procedere.

echo "=== VMWARE DECOMMISSIONING CHECKLIST ==="
echo "Date: $(date)"
echo ""

# Step 1: Final backup archivio (OBBLIGATORIO)
echo "Step 1: Final archive backup"
echo "  Backup TUTTE le VM VMware su storage di archivio"
echo "  Retention: secondo policy aziendale (tipico 1-7 anni)"
echo "  Formato: OVA (portabile) + VMDK raw"
echo "  Verificare restore di almeno 1 VM dall'archivio"
echo ""
read -p "Step 1 completed? (yes/no): " STEP1
[ "$STEP1" != "yes" ] && echo "Abort." && exit 1

# Step 2: Export configurazione VMware (per documentazione)
echo "Step 2: Export VMware configuration"
echo "  - vCenter configuration export"
echo "  - ESXi host profiles"
echo "  - Network/VLAN configuration"
echo "  - Distributed switch configuration"
echo "  - Resource pool configuration"
echo "  - Permission/role configuration"
echo ""
read -p "Step 2 completed? (yes/no): " STEP2
[ "$STEP2" != "yes" ] && echo "Abort." && exit 1

# Step 3: Notification
echo "Step 3: Final notifications"
echo "  - Email a tutti gli stakeholder: 'VMware decommissioning today'"
echo "  - Help desk: aggiornare KB articles"
echo "  - Documentation: archiviare runbook VMware"
echo ""
read -p "Step 3 completed? (yes/no): " STEP3
[ "$STEP3" != "yes" ] && echo "Abort." && exit 1

# Step 4: Shutdown VMware cluster
echo "Step 4: Shutdown VMware"
echo "  WARNING: This is IRREVERSIBLE after hardware reclaim"
echo ""
echo "  4a. Shutdown all VM (should already be off)"
echo "  4b. Put ESXi hosts in maintenance mode"
echo "  4c. Shutdown vCenter Server Appliance (vCSA)"
echo "  4d. Shutdown ESXi hosts"
echo ""
read -p "Step 4 completed? (yes/no): " STEP4
[ "$STEP4" != "yes" ] && echo "Abort." && exit 1

# Step 5: Hardware disposition
echo "Step 5: Hardware"
echo "  Option A: Re-deploy as additional Proxmox capacity"
echo "  Option B: Return lease equipment"
echo "  Option C: Sell surplus hardware"
echo "  Option D: Hold in cold storage (paranoia mode)"
echo ""
echo "  Se Option A: wipe, install Debian+Proxmox, join cluster"
echo "  ATTENZIONE: WIPE COMPLETO del disco prima di riuso"
echo "  Se dati sensibili: NIST 800-88 compliant data destruction"

# Step 6: License termination
echo "Step 6: Broadcom license management"
echo "  - Contattare Broadcom account manager"
echo "  - Richiedere termination delle licenze"
echo "  - Documentare conferma scritta"
echo "  - Aggiornare asset register"
echo "  - Verificare termine contratti di supporto"

# Step 7: Documentation
echo "Step 7: Close-out documentation"
echo "  - Lessons learned document (final)"
echo "  - Before/after comparison report"
echo "  - Cost saving analysis"
echo "  - Archivio runbook completo"
echo "  - Update CMDB: rimuovere asset VMware"
echo "  - Update monitoring: rimuovere check VMware"
echo "  - Update documentation: aggiornare topology diagram"
```

### 8.3 Re-deploy hardware come capacity Proxmox

Se l'hardware VMware viene riutilizzato:

```bash
# Procedura per trasformare un ex-ESXi host in nodo Proxmox

# 1. WIPE completo
# Bootare da USB/PXE un live Linux
dd if=/dev/zero of=/dev/sda bs=1M count=1000  # distrugge MBR/GPT
# Per compliance NIST 800-88: usare nwipe o shred
nwipe --method=dodshort /dev/sda /dev/sdb /dev/sdc

# 2. Installare Proxmox VE
# Bootare dal ISO Proxmox VE 8.x
# Installare con ZFS mirror (se 2+ dischi)
# Configurare rete, hostname, DNS

# 3. Join al cluster esistente
pvecm add <existing-node-ip> --use_ssh

# 4. Configurare Ceph OSD (se il cluster usa Ceph)
# Per ogni disco dati:
pveceph osd create /dev/sdb
pveceph osd create /dev/sdc

# 5. Verificare
pvecm status
ceph osd tree
```

### 8.4 Cost saving analysis template

```
=== VMWARE TO PROXMOX COST ANALYSIS ===

BEFORE (VMware annual cost):
  VMware vSphere licenses:          EUR ___
  VMware vCenter license:           EUR ___
  VMware vSAN license (if any):     EUR ___
  VMware NSX license (if any):      EUR ___
  Broadcom support contract:        EUR ___
  Third-party backup (Veeam etc):   EUR ___
  Total annual VMware cost:         EUR ___

AFTER (Proxmox annual cost):
  Proxmox VE subscriptions:        EUR ___  (Community=0, Standard/Premium=per socket)
  Proxmox Backup Server license:   EUR ___
  Ceph community support:          EUR ___  (typically 0)
  Third-party support (if any):    EUR ___
  Total annual Proxmox cost:       EUR ___

MIGRATION COST (one-time):
  Consulting/professional services: EUR ___
  Hardware additions (if any):      EUR ___
  Training:                         EUR ___
  Downtime cost estimate:           EUR ___
  Total migration cost:             EUR ___

SAVINGS:
  Annual savings:                   EUR ___ (VMware - Proxmox annual)
  Break-even point:                 ___ months (migration cost / monthly savings)
  5-year TCO savings:               EUR ___
```

---

## 9. Communication templates

### 9.1 Stakeholder pre-cutover (T-30d)

```
Subject: Production Cutover Scheduled — <DATE> — Advance Notice

Dear Stakeholders,

This is to inform you that the production cutover from VMware to Proxmox VE 
is scheduled for:

DATE:   Saturday <date> 22:00 → Sunday <date> 06:00 (CET)
IMPACT: All production services unavailable during maintenance window

This notice is 30 days in advance. Detailed communications will follow at 
T-7 days and T-1 day.

Key dates:
- T-7:  Final notice with detailed impact assessment
- T-1:  GO/NO-GO decision meeting
- T0:   Cutover execution
- T+1h: Service restoration notification

Cutover team:
- Sponsor: <Name>, <Title>
- Cutover Lead: <Name>
- For questions: cutover-info@example.com

Please acknowledge receipt of this notice.
```

### 9.2 Stakeholder pre-cutover (T-7d)

```
Subject: [ACTION REQUIRED] Production Cutover — <DATE> — Final Notice

Dear Stakeholders,

This is the FINAL NOTICE for the production cutover from VMware to Proxmox VE.

SCHEDULE:
  Date:    Saturday <date>
  Start:   22:00 CET
  End:     06:00 CET (target)
  Impact:  All production services unavailable

DURING THE WINDOW:
- Status updates every 30 minutes on #cutover-status (Slack)
- Emergency contact: <phone number> (on-call engineer)
- DO NOT contact the cutover team directly for status — use #cutover-status

ACTION REQUIRED:
- Avoid scheduling critical operations on Saturday or Sunday
- Ensure your team is aware of the maintenance window
- Prepare contingency plans for extended downtime (up to 12h worst case)
- Direct end-user questions to Help Desk: <email> / <phone>

POST-CUTOVER:
- Services expected back by 06:00 CET Sunday
- If issues persist, we will communicate via #cutover-status
- Business-as-usual on Monday with elevated monitoring

GO/NO-GO decision will be made at T-1 (Friday <date>). If the cutover is 
postponed, you will be notified by 18:00 Friday.

Sponsor: <Name>, <Title>
Cutover Lead: <Name>
```

### 9.3 End-user notification (T-1d)

```
Subject: Scheduled Maintenance — <DATE> 22:00-06:00

Dear Users,

We will perform scheduled maintenance on our systems:

WHEN:   Saturday <date> from 22:00 to Sunday <date> 06:00 (CET)
WHAT:   Infrastructure upgrade
IMPACT: All online services will be temporarily unavailable

WHAT TO EXPECT:
- Services will be unavailable starting 22:00
- Services expected to resume by 06:00 Sunday
- No action required from you

IF YOU NEED HELP:
- Emergency support: <phone> (available during maintenance)
- Non-urgent: <email>
- Status page: https://status.example.com

We apologize for any inconvenience. This upgrade will improve 
performance and reliability of our services.

Thank you for your patience.
IT Operations Team
```

### 9.4 Status during cutover (ogni 30 min)

```
Subject: [CUTOVER STATUS] T+XX:XX — GREEN/AMBER/RED

TIMESTAMP: YYYY-MM-DD HH:MM CET
PROGRESS:  XX% complete
STATUS:    GREEN

COMPLETED SINCE LAST UPDATE:
- [22:00] Maintenance window opened
- [22:10] Traffic drained from VMware
- [22:15] Applications stopped

IN PROGRESS:
- [22:30] Data synchronization (ETA: 22:45)

NEXT 30 MINUTES:
- VM boot on new platform
- Smoke testing

METRICS:
- Downtime so far: XX min
- Issues: 0 critical, 0 high

NEXT DECISION POINT: T+04:00 (GO/NO-GO for traffic)

---
Status updates every 30 min. Next update: HH:MM CET.
Questions → #cutover-status (Slack), NOT this email thread.
```

### 9.5 Post-cutover success (T0+1h)

```
Subject: [COMPLETED] Maintenance Completed Successfully

Dear Users,

The scheduled maintenance has been completed successfully.

SUMMARY:
- Duration: X hours (22:00 — XX:00 CET)
- Result:   All services restored
- Impact:   [Minimal / As expected]

All services are now operational on the upgraded platform.

IF YOU NOTICE ANY ISSUES:
- Please report to <support email> or Help Desk <phone>
- Include "post-maintenance" in the subject line
- Our team is monitoring closely for the next 48 hours

Thank you for your patience during this upgrade.

IT Operations Team
```

### 9.6 Post-cutover failure / rollback

```
Subject: [NOTICE] Maintenance Update — Services Restored (Rollback)

Dear Users,

The scheduled maintenance has been completed. Due to technical issues 
encountered during the upgrade, we have restored services on the 
original platform.

SUMMARY:
- Duration: X hours (22:00 — XX:00 CET)
- Result:   Rollback to original platform
- Impact:   Services restored, no data loss

YOUR EXPERIENCE:
- All services are operational
- No action required from you
- If you notice any unusual behavior, please contact Help Desk

NEXT STEPS:
- Our team is investigating the root cause
- A new maintenance window will be scheduled (minimum 2 weeks)
- You will receive advance notice

We apologize for any inconvenience.

IT Operations Team
```

### 9.7 Lessons learned email (T0+1w)

```
Subject: Production Cutover — Lessons Learned Report

Team,

Cutover completed on <date>. Full report below.

OUTCOME: SUCCESS / ROLLBACK

KEY METRICS:
- Total maintenance window: X hours
- Actual downtime:          X hours
- Target downtime:          X hours
- Rollback triggered:       NO / YES (at T+XX:XX)
- Issues encountered:       N total (X critical, Y high, Z medium)
- Business metric impact:   <% deviation from baseline>

TIMELINE VS PLAN:
| Phase          | Planned  | Actual   | Delta    |
|----------------|----------|----------|----------|
| Drain          | 10 min   | XX min   | +XX min  |
| Sync           | 15 min   | XX min   | +XX min  |
| Boot           | 45 min   | XX min   | +XX min  |
| Smoke test     | 30 min   | XX min   | +XX min  |
| DNS flip       | 15 min   | XX min   | +XX min  |
| Total          | 115 min  | XXX min  | +XX min  |

WHAT WENT WELL:
1. <specific thing that worked>
2. <specific thing that worked>
3. <specific thing that worked>

WHAT DIDN'T GO WELL:
1. <specific issue + impact + resolution>
2. <specific issue + impact + resolution>

WHAT TO IMPROVE NEXT TIME:
1. <actionable improvement + owner>
2. <actionable improvement + owner>

OPEN ITEMS:
| Item | Owner | Due Date | Status |
|------|-------|----------|--------|
| ...  | ...   | ...      | ...    |

Full report and RCA: <link>
Runbook updated version: <link>
```

---

## 10. Tooling e automazione cutover

### 10.1 Cutover orchestration script

```bash
#!/bin/bash
# cutover-orchestrator.sh — orchestrazione semi-automatica del cutover
# NOTA: i decision points restano MANUALI. Lo script automatizza
# l'esecuzione e il tracking, non le decisioni.

set -euo pipefail

CUTOVER_LOG="/var/log/cutover-$(date +%Y%m%d-%H%M%S).log"
RUNBOOK_STATE="/tmp/cutover-state.json"
SLACK_WEBHOOK="${SLACK_CUTOVER_WEBHOOK}"  # da env var
START_TIME=$(date +%s)

# Funzioni helper
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" | tee -a "$CUTOVER_LOG"
}

elapsed() {
    local now=$(date +%s)
    local diff=$((now - START_TIME))
    printf "T+%02d:%02d" $((diff/3600)) $(((diff%3600)/60))
}

slack_notify() {
    local color=$1 msg=$2
    curl -s -X POST "$SLACK_WEBHOOK" \
        -H 'Content-type: application/json' \
        -d "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$(elapsed) $msg\"}]}" \
        >/dev/null
}

update_state() {
    local step=$1 status=$2
    python3 -c "
import json, os
state = json.load(open('$RUNBOOK_STATE')) if os.path.exists('$RUNBOOK_STATE') else {'steps':{}}
state['steps']['$step'] = {'status': '$status', 'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'}
json.dump(state, open('$RUNBOOK_STATE', 'w'), indent=2)
"
}

wait_for_confirmation() {
    local msg=$1
    log ">>> MANUAL STEP: $msg"
    log ">>> Press ENTER when complete, or type 'abort' to stop."
    read -r response
    if [ "${response,,}" = "abort" ]; then
        log "ABORTED by operator"
        slack_notify "danger" "CUTOVER ABORTED by operator at step: $msg"
        exit 1
    fi
}

check_result() {
    local step=$1 result=$2
    if [ "$result" -ne 0 ]; then
        log "[FAIL] Step '$step' failed with exit code $result"
        slack_notify "danger" "FAIL: $step"
        wait_for_confirmation "Step '$step' failed. Fix and press ENTER to continue, or 'abort'."
    else
        log "[OK] Step '$step' completed"
        update_state "$step" "done"
    fi
}

# === MAIN EXECUTION ===

log "=========================================="
log "PRODUCTION CUTOVER START"
log "=========================================="
update_state "cutover_start" "started"
slack_notify "good" "CUTOVER STARTED. War room active."

# Step 1: Preflight
log "Step 1: Running preflight checks..."
./cutover-preflight-check.sh
check_result "preflight" $?

# Step 2: Drain traffic
log "Step 2: Draining traffic..."
slack_notify "warning" "Draining traffic from VMware load balancer"
echo "set server backend_vmware/srv1 state drain" | \
    socat stdio /var/lib/haproxy/admin.sock 2>&1 | tee -a "$CUTOVER_LOG"
# Wait for drain
log "Waiting for in-flight requests to complete..."
for i in $(seq 1 60); do
    CONN=$(echo "show stat" | socat stdio /var/lib/haproxy/admin.sock 2>/dev/null | \
        awk -F, '/backend_vmware/{print $5}')
    [ "${CONN:-0}" -eq 0 ] && break
    sleep 5
done
check_result "drain_traffic" 0

# Step 3: App shutdown
log "Step 3: Application shutdown..."
wait_for_confirmation "App Lead: Shutdown applications on VMware (web → app → DB)"
update_state "app_shutdown" "done"
slack_notify "warning" "Applications stopped on VMware"

# Step 4: Final sync
log "Step 4: Final delta sync..."
wait_for_confirmation "Storage Lead: Execute final delta sync and verify checksums"
update_state "final_sync" "done"
slack_notify "warning" "Final sync completed, data verified"

# Step 5: Boot VM on Proxmox
log "Step 5: Booting VM on Proxmox..."
# Automated boot with tier ordering
for TIER_NAME in "Tier0-infra" "Tier1-database" "Tier2-app" "Tier3-web"; do
    log "  Booting $TIER_NAME..."
    # Read VMID list from config
    VMIDS=$(python3 -c "
import json
config = json.load(open('/etc/cutover/boot-order.json'))
print(' '.join(str(v) for v in config['$TIER_NAME']))
" 2>/dev/null || echo "")
    
    for VMID in $VMIDS; do
        log "  Starting VMID $VMID..."
        qm start "$VMID" 2>&1 | tee -a "$CUTOVER_LOG"
        # Wait for guest agent
        timeout 180 bash -c "until qm agent $VMID ping 2>/dev/null; do sleep 5; done" || \
            log "  [WARN] VMID $VMID: guest agent timeout"
    done
    log "  $TIER_NAME: all VM started"
done
check_result "boot_vms" 0
slack_notify "good" "All VM running on Proxmox"

# Step 6: Smoke test
log "Step 6: Running smoke tests..."
./smoke-test.sh 2>&1 | tee -a "$CUTOVER_LOG"
SMOKE_RESULT=$?
check_result "smoke_test" $SMOKE_RESULT

# Step 7: DNS flip
log "Step 7: DNS flip..."
wait_for_confirmation "Network Lead: Execute DNS flip to Proxmox IPs"
update_state "dns_flip" "done"
slack_notify "warning" "DNS flipped to Proxmox"

# Step 8: Soak test
log "Step 8: Soak test (60 min)..."
slack_notify "good" "Soak test started. Duration: 60 min."
./soak-monitor.sh &
SOAK_PID=$!
sleep 3600  # 1 hour
kill $SOAK_PID 2>/dev/null

# Step 9: Decision Point #1
log "=========================================="
log "DECISION POINT #1"
log "=========================================="
slack_notify "warning" "DECISION POINT #1 — Cutover Lead: GO or NO-GO?"
wait_for_confirmation "Cutover Lead: Decision Point #1. Type ENTER for GO, or 'abort' for ROLLBACK."
update_state "decision_point_1" "GO"
slack_notify "good" "Decision Point #1: GO. Opening production traffic."

# Step 10: Open traffic
log "Step 10: Opening production traffic..."
echo "set server backend_proxmox/srv1 state ready" | \
    socat stdio /var/lib/haproxy/admin.sock 2>&1 | tee -a "$CUTOVER_LOG"
check_result "open_traffic" 0
slack_notify "good" "Production traffic flowing through Proxmox"

# Step 11: Post-traffic soak
log "Step 11: Post-traffic soak (60 min)..."
sleep 3600

# Step 12: Decision Point #2
log "=========================================="
log "DECISION POINT #2"
log "=========================================="
slack_notify "warning" "DECISION POINT #2 — Confirm stability?"
wait_for_confirmation "Cutover Lead: Decision Point #2. ENTER for GO (release war room), or 'abort'."
update_state "decision_point_2" "GO"

# Done
END_TIME=$(date +%s)
DURATION=$(( END_TIME - START_TIME ))
log "=========================================="
log "CUTOVER COMPLETE"
log "Duration: $(( DURATION / 3600 ))h $(( (DURATION % 3600) / 60 ))m"
log "=========================================="
slack_notify "good" "CUTOVER COMPLETE. Duration: $(( DURATION / 3600 ))h $(( (DURATION % 3600) / 60 ))m. War room released."
```

### 10.2 Boot order configuration

```json
{
  "Tier0-infra": [101, 102, 103],
  "Tier1-database": [110, 111],
  "Tier2-app": [120, 121, 122],
  "Tier3-web": [130, 131, 132, 140, 141],
  
  "boot_config": {
    "tier_delay_seconds": 30,
    "vm_boot_timeout_seconds": 180,
    "guest_agent_timeout_seconds": 120,
    "retry_count": 2,
    "parallel_within_tier": true
  },
  
  "dependency_checks": {
    "101": {"type": "dns", "check": "dig +short localhost @10.1.1.101"},
    "102": {"type": "ldap", "check": "ldapsearch -x -H ldap://10.1.1.102 -b '' -s base"},
    "110": {"type": "mysql", "check": "mysql -h 10.1.1.110 -u monitor -e 'SELECT 1'"},
    "120": {"type": "http", "check": "curl -sk https://10.1.1.120:8080/health"},
    "130": {"type": "http", "check": "curl -sk https://10.1.1.130/"}
  }
}
```

### 10.3 Monitoring dashboard setup (Grafana)

```json
{
  "dashboard": {
    "title": "Production Cutover Dashboard",
    "refresh": "10s",
    "panels": [
      {
        "title": "Cluster CPU Usage",
        "type": "gauge",
        "targets": [{"expr": "avg(100 - (rate(node_cpu_seconds_total{mode='idle'}[5m]) * 100))"}],
        "thresholds": [{"value": 0, "color": "green"}, {"value": 70, "color": "orange"}, {"value": 85, "color": "red"}]
      },
      {
        "title": "Cluster RAM Usage",
        "type": "gauge",
        "targets": [{"expr": "avg(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100"}],
        "thresholds": [{"value": 0, "color": "green"}, {"value": 75, "color": "orange"}, {"value": 90, "color": "red"}]
      },
      {
        "title": "HTTP Response Time (p99)",
        "type": "graph",
        "targets": [{"expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))"}]
      },
      {
        "title": "Error Rate (5xx)",
        "type": "graph",
        "targets": [{"expr": "sum(rate(http_requests_total{status=~'5..'}[5m])) / sum(rate(http_requests_total[5m])) * 100"}]
      },
      {
        "title": "VM Status",
        "type": "table",
        "targets": [{"expr": "pve_guest_info"}]
      },
      {
        "title": "Ceph Health",
        "type": "stat",
        "targets": [{"expr": "ceph_health_status"}]
      },
      {
        "title": "Active Connections (LB)",
        "type": "graph",
        "targets": [{"expr": "haproxy_frontend_current_sessions"}]
      },
      {
        "title": "DNS Propagation Status",
        "type": "stat",
        "description": "Manual update — Network Lead enters value"
      }
    ]
  }
}
```

### 10.4 Alertmanager configuration per cutover

```yaml
# alertmanager-cutover.yml
# Configurazione speciale attiva SOLO durante la finestra di cutover
# Sostituisce le regole normali per evitare alert noise

global:
  resolve_timeout: 5m

route:
  receiver: 'cutover-warroom'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 15m
  
  routes:
    # Critical: immediate notification
    - match:
        severity: critical
      receiver: 'cutover-warroom'
      group_wait: 0s
      repeat_interval: 5m
      
    # Warning: notify but don't spam
    - match:
        severity: warning
      receiver: 'cutover-warroom'
      group_wait: 1m
      repeat_interval: 15m
      
    # Info: log only, don't notify
    - match:
        severity: info
      receiver: 'cutover-log-only'

receivers:
  - name: 'cutover-warroom'
    slack_configs:
      - api_url: '${SLACK_CUTOVER_WEBHOOK}'
        channel: '#cutover-alerts'
        title: '[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
    pagerduty_configs:
      - service_key: '${PAGERDUTY_CUTOVER_KEY}'
        severity: '{{ .CommonLabels.severity }}'
        
  - name: 'cutover-log-only'
    webhook_configs:
      - url: 'http://localhost:9099/log'

# Silence rules for expected alerts during cutover
# (VMware alerts will fire as we shut it down — silence them)
inhibit_rules:
  - source_match:
      alertname: 'CutoverInProgress'
    target_match_re:
      alertname: 'VMware.*'
    equal: ['']
```

---

## 11. Scenari reali e case study

### 11.1 Scenario: cutover di un ERP (SAP/Oracle)

**Contesto:** azienda manifatturiera, 40 VM su VMware vSphere 7, ERP SAP ECC 6.0 su HANA, 200 utenti. Cutover in un weekend.

**Complessita aggiuntive:**
- SAP richiede boot order specifico: HANA → SAP Application Server → SAP Web Dispatcher;
- Lock delle transazioni SAP prima del cutover (`SM13`);
- Export del SAP transport directory;
- Verifica licenze SAP post-migrazione (hardware key change);
- Test RFC connections tra sistemi SAP.

```
Timeline reale:
  Sabato 20:00  War room open
  20:15         SAP lock transactions (SM13)
  20:30         User notification: "SAP unavailable"
  20:45         SAP application servers shutdown
  21:00         HANA graceful shutdown (1 backup final)
  21:30         Final delta sync (HANA data = 2TB, ~45 min)
  22:15         Boot HANA on Proxmox
  22:45         HANA recovery (log replay)
  23:15         Boot SAP App Servers
  23:45         Boot SAP Web Dispatcher
  00:00         SAP smoke test (SE80, SE16, VA01, ME21N)
  00:30         SAP RFC connection test
  01:00         Decision Point #1 → GO
  01:15         Open SAP for users
  
  Problema: HANA boot time su Proxmox: 25 min vs 15 min su VMware
  Causa:    Hugepages non configurate su Proxmox
  Fix:      Configurare hugepages: 
            echo 'vm.nr_hugepages = 16384' >> /etc/sysctl.conf
            sysctl -p
  Impatto:  +10 min sul timeline, nessun impatto su decision point
```

### 11.2 Scenario: cutover con zero-downtime requirement

**Contesto:** e-commerce, 120 VM, fatturato 2M EUR/mese, zero-downtime SLA. Blue-green approach.

```
Architettura blue-green:

  VMware (Blue):  web01-03 → app01-03 → db01 (primary)
                            ↕ replication
  Proxmox (Green): web11-13 → app11-13 → db11 (replica)

Strategia:
  1. Setup replication MySQL da VMware-db01 a Proxmox-db11
  2. Deploy applicazione su Proxmox (identica, testata)
  3. Cutover = cambio DNS + LB flip
  4. Nessun downtime: il traffico passa gradualmente

Timeline:
  T-7d:  MySQL replication attiva, lag < 1s
  T-1d:  Canary: 5% traffico su Proxmox via LB weight
  T-0h:  Full cutover: LB weight 100% Proxmox
         db11 promosso a primary, db01 fermato
         
  Complicazione: replication lag spike durante picco ordini
  Soluzione: cutover schedulato alle 3am (minimo traffico)
```

### 11.3 Scenario: rollback reale

**Contesto:** banca regionale, 80 VM, cutover notturno. Rollback a T+3h.

```
Timeline:
  22:00  Cutover start
  22:30  VM shutdown VMware
  22:45  Final sync completata
  23:00  Boot VM su Proxmox — OK
  23:30  Smoke test:
         - Web app: OK
         - API: OK
         - Core banking: FAIL — timeout su stored procedure
         
  23:45  App Lead: "Core banking timeout. Investigating."
         Causa: stored procedure usa temporary tablespace
         Proxmox VM con 32GB RAM vs VMware 64GB (errore di sizing)
         
  00:00  App Lead: "Can fix by adding RAM to VM: qm set 110 --memory 65536"
         Cutover Lead: "Do we have capacity?"
         Storage Lead: "Si, ma nodo pve2 sarebbe al 92% RAM"
         
  00:15  Cutover Lead: "Rischio troppo alto con nodo al 92%. 
         Se pve2 va in OOM, perdiamo tutto il tier DB.
         Decision: ROLLBACK."
         
  00:15  === ROLLBACK DECLARED ===
  00:20  DNS revert + LB flip
  00:35  VM stop Proxmox, start VMware
  01:00  Smoke test VMware: OK
  01:15  Production traffic restored su VMware
  
  Post-mortem:
  - Root cause: sizing errato della VM DB (modulo 05 non seguito)
  - Fix: aggiungere 2x16GB RAM a pve2 (hardware upgrade)
  - Re-cutover: 3 settimane dopo, successo
  
  Lezione: il rollback drill non aveva testato il workload
           del core banking (solo smoke test base). Il drill
           va fatto con workload realistico.
```

### 11.4 Scenario: cutover multi-site

**Contesto:** azienda con 2 datacenter (Milano + Roma), active-passive. Cutover del sito attivo (Milano).

```
Complessita aggiuntive:
- DR site (Roma) deve essere aggiornato contemporaneamente
- WAN replication VMware → Proxmox cross-site
- DNS GeoDNS: aggiornare entrambi i siti
- VPN site-to-site: routing update

Timeline:
  T-14d: Setup Proxmox cluster a Roma (DR)
  T-7d:  Configurare Ceph RBD mirroring Milano → Roma
  T0:    Cutover Milano (primary)
  T0+24h: Verificare DR replication su Roma
  T0+7d:  DR drill su Roma (simulate failover)
  
  Punto critico: WAN bandwidth per Ceph replication
  Calcolo: 500GB changed data/day × 8 bit / 86400s = 46 Mbit/s
  WAN disponibile: 100 Mbit/s → OK ma con 54% utilizzo
```

---

## 12. Lessons learned framework

### 12.1 Template strutturato

```
| Categoria | Cosa e andato bene | Cosa migliorare | Owner | Due date | Status |
|-----------|-------------------|-----------------|-------|----------|--------|
| Pianificazione | Tabletop exercise ha identificato 3 gap | Risk register incompleto: mancava rischio sizing | CL | T+14d | OPEN |
| Comunicazione | Status update puntuali e apprezzati | Template email era troppo lungo per mobile | CC | T+7d | OPEN |
| Esecuzione tecnica | Boot automatizzato ha risparmiato 20 min | Smoke test non copriva core banking | AL | T+14d | OPEN |
| Decision points | Criteri oggettivi hanno eliminato discussioni | Mancava threshold per memory pressure | CL | T+7d | OPEN |
| Rollback readiness | Rollback drill ha provato il processo | Drill non usava workload realistico | SL | T+14d | OPEN |
| Post-cutover | Monitoring dashboard efficace | Mancava alert per NTP drift | NL | T+7d | OPEN |
| Team management | Turni hanno evitato fatigue | Mancava backup per Storage Lead | CL | T+7d | OPEN |
```

### 12.2 Post-Implementation Review (PIR)

```
POST-IMPLEMENTATION REVIEW
Date: T+7d
Attendees: All cutover leads + sponsor

1. OUTCOME REVIEW
   - Cutover result: SUCCESS / ROLLBACK
   - Planned duration: X hours
   - Actual duration:  X hours
   - Variance:         +/- X hours (X%)
   - Downtime:         X hours
   - User impact:      <description>

2. TIMELINE ANALYSIS
   Per ogni step: planned vs actual, con root cause per variances > 15%.

3. ISSUE REVIEW
   Per ogni issue durante il cutover:
   - Description
   - Time detected
   - Time resolved
   - Root cause
   - Impact
   - Prevention strategy

4. METRIC REVIEW
   - Business metrics post-cutover vs baseline
   - Infrastructure metrics post-cutover vs baseline
   - SLA compliance during and after cutover

5. STAKEHOLDER FEEDBACK
   - Sponsor feedback
   - Business unit feedback
   - End user feedback (ticket analysis)
   - Help desk feedback

6. ACTION ITEMS
   Per ogni improvement:
   - Description
   - Owner
   - Due date
   - Priority

7. RUNBOOK UPDATES
   - Steps to add
   - Steps to modify
   - Steps to remove
   - Timing adjustments
```

### 12.3 Metriche di successo

```
CUTOVER SUCCESS METRICS:

Tier 1 (must-have):
  [ ] Zero data loss
  [ ] Downtime within planned window
  [ ] No rollback (or clean rollback if needed)
  [ ] All services operational post-cutover

Tier 2 (should-have):
  [ ] Downtime < 80% of planned window
  [ ] Business metrics >= 95% of baseline within 24h
  [ ] Zero P1 incidents in first 72h
  [ ] Zero data discrepancies

Tier 3 (nice-to-have):
  [ ] Downtime < 50% of planned window
  [ ] Business metrics >= 99% of baseline within 24h
  [ ] Positive stakeholder feedback
  [ ] Cutover team satisfaction > 4/5
```

---

## 13. Troubleshooting

### 13.1 VM non bootra su Proxmox dopo cutover

**Sintomo:** `qm start <VMID>` fallisce con errore KVM o QEMU.

**Cause piu comuni:**
- CPU type mismatch (VMware CPU non supportato da QEMU);
- Disco non trovato (path storage errato);
- Memoria insufficiente sul nodo;
- Hugepages non configurate per VM che le richiedono.

**Diagnosi:**
```bash
# Check error log
journalctl -u pve-qemu-server@<VMID> --no-pager -n 50

# Verifica configurazione VM
qm config <VMID>

# Verifica capacita nodo
pvesh get /nodes/$(hostname)/status

# Verifica storage
pvesm status
```

**Soluzione:**
```bash
# CPU type: usare 'host' o 'x86-64-v2-AES'
qm set <VMID> --cpu host

# Disco: verificare che il volume esista
lvs | grep vm-<VMID>
# oppure
zfs list | grep vm-<VMID>

# Memoria: verificare capacity
free -h
# Se insufficiente, migrare VM meno critiche ad altro nodo:
qm migrate <VMID-noncritico> <altro-nodo>
```

### 13.2 DNS non propaga dopo il flip

**Sintomo:** `dig` da resolver esterni mostra ancora il vecchio IP.

**Cause:**
- TTL non ridotto in tempo (TTL alto ancora in cache);
- Zona DNS non aggiornata correttamente;
- SOA serial non incrementato (slave DNS non sincronizza);
- CDN cache (se presente).

**Diagnosi:**
```bash
# Verifica TTL attuale dal resolver
dig +all app.example.com @8.8.8.8 | grep -E "TTL|ANSWER"

# Verifica zona su master
dig +all app.example.com @ns1.example.com

# Verifica SOA serial
dig SOA example.com @ns1.example.com

# Verifica slave sync
dig SOA example.com @ns2.example.com
# Il serial deve essere uguale al master
```

**Soluzione:**
```bash
# Forzare propagazione: incrementare SOA serial
# BIND: editare zona, incrementare serial, reload
rndc reload example.com

# Se CDN: flush cache
# Cloudflare:
curl -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/purge_cache" \
    -H "Authorization: Bearer ${CF_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"purge_everything":true}'
```

### 13.3 Performance degradation post-cutover

**Sintomo:** latenze applicative 2-3x superiori al baseline.

**Diagnosi sistematica:**
```bash
# 1. CPU: check se in throttling o overcommit
mpstat -P ALL 1 5
# Se %steal > 5%: overcommit eccessivo

# 2. RAM: check memory pressure
vmstat 1 10
# Se si > 0 o so > 0: swapping, serve piu RAM

# 3. I/O: check disk latency
iostat -xz 1 5
# Se await > 10ms su storage VM: problema storage

# 4. Network: check latency
ping -c 100 -i 0.1 db.example.com | tail -1
# Se avg > 2ms su rete locale: problema rete

# 5. Per Ceph: check OSD latency
ceph osd perf
# Se latenza commit_latency > 10ms: OSD sovraccarico

# 6. Proxmox specifico: NUMA check
numactl --hardware
# Se la VM non e NUMA-aware e il workload e memory-intensive:
qm set <VMID> --numa 1
```

**Fix comuni:**
```bash
# I/O: abilitare writeback cache (se batteria BBU/supercap presente)
qm set <VMID> --scsi0 local-zfs:vm-<VMID>-disk-0,cache=writeback

# CPU: passare a host CPU model
qm set <VMID> --cpu host

# Rete: attivare VirtIO (se era e1000 legacy)
qm set <VMID> --net0 virtio,bridge=vmbr0
```

### 13.4 Ceph degraded durante cutover

**Sintomo:** `ceph -s` mostra HEALTH_WARN o HEALTH_ERR con PG degraded/undersized.

**Diagnosi:**
```bash
ceph health detail
ceph osd tree  # cercare OSD down
ceph pg stat   # cercare PG non active+clean
```

**Azione durante cutover:**
- HEALTH_WARN con pochi PG degraded (< 1%): monitorare, non e bloccante;
- HEALTH_WARN con recovery in corso: attendere recovery, non procedere con boot massivo;
- HEALTH_ERR: **STOP CUTOVER**, risolvere prima di procedere.

```bash
# Se un OSD e down:
ceph osd tree | grep down
# Riavviare il servizio:
systemctl restart ceph-osd@<osd-id>
# Attendere recovery:
ceph -w  # watch fino a HEALTH_OK
```

### 13.5 Load balancer non inoltra al backend Proxmox

**Sintomo:** LB risponde 502/503 dopo il flip.

**Diagnosi HAProxy:**
```bash
# Check backend status
echo "show stat" | socat stdio /var/lib/haproxy/admin.sock | \
    awk -F, '/backend_proxmox/{print $2,$18}'
# Se status != "UP": il health check fallisce

# Check health check
echo "show servers state" | socat stdio /var/lib/haproxy/admin.sock

# Check error log
tail -100 /var/log/haproxy.log | grep -E "5[0-9]{2}|error|warning"
```

**Fix:**
```bash
# Forzare server UP (se health check fallisce ma il servizio funziona)
echo "set server backend_proxmox/srv1 state ready" | \
    socat stdio /var/lib/haproxy/admin.sock

# Verificare che il backend risponda sulla porta giusta
curl -vk https://10.1.1.100:443/  # l'IP del backend Proxmox

# Se porta diversa: fix haproxy config
# Se SSL: verificare certificato (Subject Alternative Name match?)
```

### 13.6 Guest agent non risponde

**Sintomo:** `qm agent <VMID> ping` timeout.

**Diagnosi:**
```bash
# Verificare se il guest agent e installato nella VM
qm agent <VMID> ping 2>&1

# Verificare il canale virtio-serial
virsh qemu-agent-command <VMID> '{"execute":"guest-ping"}' 2>&1
```

**Fix:**
```bash
# Dentro la VM (Linux):
systemctl status qemu-guest-agent
systemctl restart qemu-guest-agent

# Dentro la VM (Windows):
# Verificare servizio "QEMU Guest Agent" in services.msc
# Se non installato: installare da virtio-win drivers ISO

# Sul nodo Proxmox: verificare device seriale
qm config <VMID> | grep serial
# Se mancante:
qm set <VMID> --serial0 socket
```

### 13.7 Replication lag durante final sync

**Sintomo:** la sync finale non completa nel tempo previsto.

**Diagnosi:**
```bash
# Misurare il change rate
# Se ZFS:
zfs get written tank/vm-disk-100

# Se rsync: dry-run per stimare il delta
rsync -avnc --stats source dest

# Misurare bandwidth
iperf3 -c dest-host -t 10
```

**Soluzione:**
```bash
# 1. Ridurre il change rate: assicurarsi che le app siano FERME prima della sync
# 2. Aumentare parallelismo della sync:
#    - Usare piu thread rsync (con parallel)
#    - ZFS: compressione durante send
zfs send -c @snap pool/dataset | ssh dest "zfs receive pool/dataset"

# 3. Se la sync non completa nel buffer time:
#    Cutover Lead decide: estendere la finestra o rollback?
```

### 13.8 Problema di licensing post-cutover

**Sintomo:** applicazione rifiuta la licenza dopo boot su Proxmox (hardware fingerprint cambiato).

**Cause:** molti software vincolano la licenza a UUID del sistema, MAC address, o CPU ID. Il passaggio da VMware a Proxmox cambia questi valori.

**Fix:**
```bash
# Preservare UUID della VM
qm set <VMID> --smbios1 uuid=<original-vmware-uuid>

# Preservare MAC address
qm set <VMID> --net0 virtio=<original-mac>,bridge=vmbr0

# Per SMBIOS:
qm set <VMID> --smbios1 manufacturer=VMware,product=VMware\ Virtual\ Platform
# NOTA: questo e un workaround, non una soluzione permanente.
# Contattare il vendor del software per re-licensing.
```

### 13.9 Cluster quorum instabile durante cutover

**Sintomo:** `pvecm status` mostra Warning o nodo che flappa.

**Diagnosi:**
```bash
# Corosync status
pvecm status
corosync-cfgtool -s

# Check Corosync ring
corosync-cfgtool -s | grep -A5 "RING ID"

# Check network tra nodi
for NODE in pve1 pve2 pve3; do
    ping -c 3 -W 1 $NODE
done
```

**Azione:**
```bash
# Se un nodo non risponde:
# NON rimuoverlo dal cluster durante il cutover!
# Verificare connettivita di rete, riavviare Corosync:
ssh problematic-node "systemctl restart corosync"

# Se il cluster perde il quorum (majority dei nodi down):
# CRITICO: HA non funziona senza quorum
# Opzione A: ripristinare quorum (aggiungere nodi)
# Opzione B: forzare quorum (SOLO in emergenza):
pvecm expected 1  # PERICOLOSO: solo se si e certi che gli altri nodi non tornano
```

### 13.10 Problema di avvio OS Windows su Proxmox

**Sintomo:** Windows BSOD o boot loop dopo migrazione da VMware.

**Cause:** driver VirtIO non installati, o Windows cerca driver VMware PVSCSI/VMXNET3 che non esistono su Proxmox.

**Fix:**
```bash
# 1. Prima del cutover: installare VirtIO drivers nella VM su VMware
#    - Montare virtio-win ISO
#    - Installare tutti i driver (storage, network, balloon, serial)
#    - Riavviare e verificare che Windows bootra

# 2. Se gia migrata senza driver:
#    - Cambiare disk controller a IDE (boot possibile senza driver):
qm set <VMID> --scsihw lsi  # o --scsihw megasas
#    - Bootare, installare VirtIO, poi tornare a VirtIO:
qm set <VMID> --scsihw virtio-scsi-single
```

---

## 14. Esercizi

### Esercizio 1: Tabletop exercise (Gruppi da 4)

In gruppi da 4 persone (Cutover Lead, Network Lead, Storage Lead, Comms Lead), simulate un cutover su carta.

**Istruzioni:**
1. Cutover Lead legge il runbook step-by-step;
2. Ogni 15 minuti, Cutover Lead inietta un "twist":
   - Twist A: la VM del database non si avvia (errore KVM);
   - Twist B: il DNS non propaga (TTL era ancora a 3600s);
   - Twist C: lo sponsor chiama chiedendo "quanto manca?";
   - Twist D: un membro del team si addormenta alle 3am;
   - Twist E: il backup pre-cutover risulta corrotto;
   - Twist F: un cliente VIP segnala problemi a mezzanotte.
3. Documentare le decisioni prese, i tempi, e le lacune del piano.

**Deliverable:** report 2 pagine con azioni correttive.

### Esercizio 2: Design rollback drill

Pianifica e (se possibile) esegui in lab un rollback completo:
1. Deploy ambiente fittizio: 3 VM su "VMware" (puo essere un altro Proxmox cluster), 3 VM su Proxmox;
2. Simula cutover: spegni su VMware, accendi su Proxmox, verifica funzionamento;
3. Simula failure: inietta un problema (es: kill del servizio DB);
4. Esegui rollback documentando ogni step e tempistica;
5. Analizza: quanto tempo? dove si e perso tempo? come velocizzare?

**Deliverable:** rollback drill report con timeline e miglioramenti.

### Esercizio 3: Monitoring threshold automation

Scrivi un sistema di monitoring per la finestra di cutover:
1. Script che raccoglie 10 metriche chiave (CPU, RAM, IOPS, latency, error rate, ecc.);
2. Confronta con baseline (valori pre-cutover);
3. Genera alert se una metrica supera la soglia;
4. Invia status update automatico su Slack ogni 30 min;
5. Bonus: anomaly detection con standard deviation.

**Deliverable:** script funzionante + README con istruzioni.

### Esercizio 4: GO/NO-GO simulation

Simula un GO/NO-GO meeting:
1. Prepara 5 scenari con dati diversi (2 chiari GO, 2 chiari NO-GO, 1 ambiguo);
2. Per ogni scenario, presenta i dati ai "lead" (colleghi);
3. Ogni lead esprime GO o NO-GO con confidence 1-5;
4. Documenta il processo decisionale e le discussioni;
5. Per lo scenario ambiguo: come si risolve? Sponsor? Voto? Dati aggiuntivi?

**Deliverable:** report con analisi dei pattern decisionali del gruppo.

### Esercizio 5: Communication plan completo

Crea un communication plan completo per un cutover:
1. Identifica tutti gli stakeholder (interni + esterni);
2. Per ogni stakeholder: canale, frequenza, template;
3. Scrivi tutti i template (pre, durante, post, rollback);
4. Simula la comunicazione: scrivi 6 status update (ogni 30 min) per un cutover simulato;
5. Includi uno scenario di rollback con la comunicazione appropriata.

**Deliverable:** communication plan completo + 6 sample status update.

### Esercizio 6: Cutover cost analysis

Per un ambiente reale o simulato:
1. Calcola il costo annuale VMware (licenze, supporto, hardware dedicato);
2. Calcola il costo annuale Proxmox equivalente;
3. Stima il costo della migrazione (consulting, downtime, training);
4. Calcola il break-even point;
5. Proietta il risparmio a 3 e 5 anni;
6. Presenta i risultati in formato executive (1 pagina).

**Deliverable:** one-pager con TCO comparison e break-even chart.

### Esercizio 7: Post-mortem di un cutover fallito

Sulla base dello scenario 11.3 (rollback della banca):
1. Scrivi un Post-Implementation Review completo;
2. Identifica i 3 root cause principali;
3. Proponi azioni correttive per ognuno;
4. Progetta il cutover "round 2" con le mitigazioni applicate;
5. Come avresti potuto prevenire il problema nel rollback drill?

**Deliverable:** PIR completo + piano cutover v2.

### Esercizio 8: Cutover orchestration automation

Estendi lo script `cutover-orchestrator.sh`:
1. Aggiungi health check automatici tra ogni step;
2. Aggiungi timeout per ogni step (se > X min, alert);
3. Aggiungi logging strutturato (JSON) per post-analysis;
4. Aggiungi integrazione con PagerDuty per alert critici;
5. Aggiungi generazione automatica del timeline report a fine cutover.

**Deliverable:** script migliorato + test con scenario simulato.

---

## 15. Auto-valutazione

1. Quali sono i 6-7 ruoli del cutover team e cosa fa ciascuno?
2. Differenza fra "decision point" e "rollback trigger automatico".
3. Quando ridurre il TTL DNS prima del cutover e perche?
4. Cosa va validato a T0+24h che non viene validato a T0+1h?
5. War room: chi e dentro, chi e fuori, e perche?
6. Communication cadence durante il cutover: ogni quanto e chi scrive?
7. Rollback drill: perche va testato in anticipo e cosa deve includere?
8. Differenza tra big bang cutover, phased cutover e blue-green cutover.
9. Come si calcola la durata della maintenance window?
10. Quali sono i criteri di GO/NO-GO al Decision Point #1?
11. In quali condizioni scatta un rollback automatico (senza decision point)?
12. Qual e l'ordine corretto di boot delle VM su Proxmox (per tier)?
13. Come gestire i dati scritti durante il cutover se si fa rollback?
14. Cosa comporta il decommissioning di VMware a T0+30d?
15. Come si struttura un Post-Implementation Review (PIR)?
16. ITIL 4: come si classifica il cutover nel modello Change Enablement?
17. Cosa fa il Comms Lead quando un manager chiama chiedendo status durante il cutover?
18. Come si prepara e si conduce un tabletop exercise?

---

## 16. Approfondimenti

### 16.1 Psicologia del war room

Il war room e un ambiente ad alta pressione. Fattori psicologici:

- **Decision fatigue:** dopo 4-6h di decisioni continue, la qualita delle decisioni cala. Soluzione: i decision points sono pre-definiti con criteri oggettivi;
- **Anchoring bias:** il primo dato presentato influenza le decisioni successive. Soluzione: checklist strutturate, non discussioni aperte;
- **Sunk cost fallacy:** "abbiamo gia lavorato 5h, non possiamo fare rollback." Soluzione: i trigger di rollback sono automatici, non negoziabili;
- **Team fatigue:** la stanchezza aumenta il tasso di errore. Soluzione: turni, pause programmate, snack, caffeina.

**Best practice:**
- Pausa obbligatoria di 10 min ogni 2h;
- Snack ad alta energia disponibili;
- Illuminazione adeguata (non troppo buio);
- Temperatura confortevole (non troppo calda);
- Se il cutover dura > 8h: turni di 4h con handoff strutturato.

### 16.2 Cutover e compliance regolamentare

**NIS2 (EU):**
- Il cutover e un "significant change" → notifica all'autorita competente se impatta servizi essenziali;
- Documentazione del piano di cutover e del rollback come parte del risk management;
- Obbligo di business continuity plan che copra il cutover.

**DORA (settore finanziario):**
- Il cutover rientra nel "Digital Operational Resilience Testing";
- Obbligo di test del piano di cutover e del rollback (non solo documentazione);
- Reporting post-cutover all'autorita di vigilanza (se richiesto).

**ISO 27001:**
- Il cutover e un "change" nel contesto di A.12.1.2 (Change management);
- Richiede risk assessment pre-cutover;
- Richiede documentazione della procedura e del risultato.

### 16.3 Cutover e ITIL 4 nella pratica

Il cutover interseca diverse practice ITIL 4:

```
Change Enablement:
  - Change Record con approval CAB
  - Risk assessment documentato
  - Post-Implementation Review

Incident Management:
  - Se il cutover causa incident → incident record collegato al change
  - Escalation path pre-definito

Problem Management:
  - Root cause analysis post-rollback
  - Trend analysis di problemi ricorrenti

Service Level Management:
  - SLA impatto durante maintenance window
  - Comunicazione a clienti su SLA deviation

Knowledge Management:
  - Lessons learned documentate e condivise
  - Runbook aggiornato per futuri cutover
```

### 16.4 Metriche avanzate: MTTR del cutover

Oltre alla durata totale, misurare:

- **MTTR (Mean Time To Recover):** tempo medio dal rilevamento di un problema alla risoluzione durante il cutover. Target: < 15 min per issue non-bloccante;
- **MTTD (Mean Time To Detect):** tempo medio dal manifestarsi di un problema al suo rilevamento. Target: < 5 min (con monitoring automatico);
- **MTTA (Mean Time To Acknowledge):** tempo medio dal detection all'inizio del troubleshooting. Target: < 2 min.

```
Formula efficacia cutover:

  Efficienza = T_planned / T_actual
  
  Se > 1.0: cutover piu veloce del previsto (eccellente)
  Se 0.8-1.0: nei parametri (buono)
  Se 0.5-0.8: significativamente oltre (da migliorare)
  Se < 0.5: il piano era irrealistico (rivedere stima)
```

### 16.5 Canary deployment come alternativa al big bang

Per ambienti che supportano traffic splitting:

```
Canary cutover graduale:

  T0:    5% traffico su Proxmox (canary)
  T0+1h: monitoring stabile → 25% traffico
  T0+2h: monitoring stabile → 50% traffico
  T0+4h: monitoring stabile → 75% traffico
  T0+6h: monitoring stabile → 100% traffico
  
  In qualunque momento: se anomalia → revert a 0% su Proxmox
  
  Vantaggi:
  - Rollback istantaneo (basta tornare a 0%)
  - Nessun downtime
  - Detection precoce di problemi
  
  Requisiti:
  - Application stateless o con session affinity
  - Load balancer con weighted routing
  - Database replication bidirezionale
  - DNS non e il meccanismo di routing (troppo lento)
```

### 16.6 Cutover automation frameworks

Strumenti di orchestrazione cutover usati in ambiente enterprise:

| Strumento | Uso | Open Source |
|-----------|-----|-------------|
| Ansible | Automazione step del runbook | Si |
| Terraform | Infrastructure provisioning pre-cutover | Si |
| Rundeck | Runbook automation con approval gates | Si (Community) |
| ServiceNow | Change management + approval workflow | No |
| PagerDuty | On-call + escalation durante cutover | No |
| Statuspage | Comunicazione utenti durante maintenance | No |
| Grafana | Dashboard monitoring real-time | Si |

**Esempio Ansible playbook per cutover:**

```yaml
# cutover-playbook.yml
---
- name: Pre-cutover validation
  hosts: proxmox_cluster
  tasks:
    - name: Check cluster status
      command: pvecm status
      register: cluster_status
      
    - name: Verify quorum
      assert:
        that:
          - "'Quorate: Yes' in cluster_status.stdout"
        fail_msg: "Cluster not quorate — ABORT"
        
    - name: Check Ceph health
      command: ceph health
      register: ceph_health
      when: "'ceph' in ansible_facts.packages"
      
    - name: Verify Ceph OK
      assert:
        that:
          - "'HEALTH_OK' in ceph_health.stdout"
        fail_msg: "Ceph not healthy — ABORT"
      when: ceph_health is defined

- name: Boot VM on Proxmox
  hosts: proxmox_primary
  vars:
    boot_order:
      - { tier: "infra", vmids: [101, 102, 103] }
      - { tier: "database", vmids: [110, 111] }
      - { tier: "app", vmids: [120, 121, 122] }
      - { tier: "web", vmids: [130, 131, 132] }
  tasks:
    - name: Boot VMs by tier
      command: "qm start {{ item.1 }}"
      loop: "{{ boot_order | subelements('vmids') }}"
      loop_control:
        pause: 10
        
    - name: Wait for guest agent
      command: "qm agent {{ item.1 }} ping"
      loop: "{{ boot_order | subelements('vmids') }}"
      retries: 30
      delay: 10
      register: agent_result
      until: agent_result.rc == 0
```

---

## 17. Letture consigliate

### Letture primarie

- ITIL 4 — Change Enablement practice. https://www.axelos.com/certifications/itil-service-management/itil-4-foundation/itil-4-glossary (retrieved 2026-04-27).
- Google SRE Book — Chapter 13 (Emergency Response). https://sre.google/sre-book/emergency-response/ (retrieved 2026-04-27).
- Google SRE Book — Chapter 14 (Managing Incidents). https://sre.google/sre-book/managing-incidents/ (retrieved 2026-04-27).
- AWS Well-Architected — Operational Excellence. https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/ (retrieved 2026-04-27).
- Atlassian Incident Management Handbook. https://www.atlassian.com/incident-management/handbook (retrieved 2026-04-27).

### Letture secondarie

- Gene Kim et al., *The Phoenix Project* — capitoli su Change Management e IT Operations.
- Nicole Forsgren et al., *Accelerate* — metriche DORA e impatto del change management sulla delivery.
- Proxmox VE Administration Guide — Chapter: Cluster Manager. https://pve.proxmox.com/pve-docs/pve-admin-guide.html (retrieved 2026-04-27).
- NIST SP 800-88 — Guidelines for Media Sanitization (per decommissioning).

---

## 18. Collegamenti incrociati

- Modulo 16.1 — `16-PROCEDURE-OPERATIVE-E-RUNBOOK/runbook-migrazione-batch.md`: building block batch, il cutover production riusa i pattern validati nei batch.
- Modulo 16.2 — `16-PROCEDURE-OPERATIVE-E-RUNBOOK/runbook-migrazione-cluster-completo.md`: contesto cluster-wide, complemento a questo modulo.
- Modulo 19 — `19-MULTI-SITE-DR-PROXMOX.md`: DR multi-site come parte della stabilizzazione post-cutover.
- Modulo 99 — `99-CASE-STUDY/broadcom-vmware-2024.md`: business driver del cutover (Broadcom licensing changes).
- Modulo 11.x — `11-BACKUP-E-RIPRISTINO-PROXMOX/`: backup pre-cutover come safety net e validazione restore.
- Modulo 13.x — `13-MONITORAGGIO-E-OTTIMIZZAZIONE/zabbix-monitoraggio-proxmox.md`: monitoring threshold per decision points durante il cutover.
- Modulo 05 — `05-ASSESSMENT-E-PIANIFICAZIONE/dimensionamento-proxmox-capacity-planning.md`: capacity planning che determina se il cluster Proxmox ha risorse sufficienti per il cutover.
- Modulo 05 — `05-ASSESSMENT-E-PIANIFICAZIONE/analisi-dipendenze-e-criticita.md`: dependency map usata per definire l'ordine di boot e le wave di cutover.
- Modulo 05 — `05-ASSESSMENT-E-PIANIFICAZIONE/timeline-e-risk-assessment.md`: risk register e timeline planning applicati al cutover.
- Modulo 01 — `01-FONDAMENTI-VMWARE/architettura-vsphere-esxi.md`: architettura VMware da cui si migra, comprensione necessaria per il decommissioning.

---

## 19. Glossario locale

| Termine | Definizione |
|---|---|
| **Cutover** | Operazione di passaggio finale da sistema vecchio a nuovo. |
| **Maintenance window** | Finestra di tempo annunciata per operazioni che impattano servizio. |
| **Freeze window** | Periodo di no-changes prima del cutover per stabilizzare l'ambiente. |
| **War room** | Sala (fisica o virtuale) dove il cutover team coordina l'esecuzione in tempo reale. |
| **GO/NO-GO** | Decision point con criteri oggettivi prima di procedere o tornare indietro. |
| **Sponsor** | Stakeholder C-level con authority finale (CIO/IT Director). |
| **Cutover Lead** | Owner operativo del cutover; coordinatore delle attivita e decisore in real-time. |
| **Comms Lead** | Responsabile della comunicazione verso stakeholder durante il cutover. |
| **Smoke test** | Test rapido che valida le funzionalita base di un sistema dopo un cambio. |
| **Soak test** | Test prolungato (24-72h) per validare stabilita sotto carico reale continuo. |
| **Rollback trigger** | Condizione oggettiva e pre-approvata che attiva il rollback (automatico o manuale). |
| **Decommissioning** | Spegnimento e rimozione controllata del sistema vecchio dopo conferma del successo. |
| **TTL DNS** | Time-To-Live dei record DNS; influenza il tempo di propagazione delle modifiche DNS. |
| **Tabletop exercise** | Simulazione su carta del cutover, senza toccare sistemi reali, per validare il piano. |
| **Drain** | Periodo in cui un sistema non riceve nuove richieste ma completa quelle esistenti. |
| **RAG status** | Red-Amber-Green; indicatore visivo di status usato nei report di avanzamento. |
| **Big bang cutover** | Modello di cutover dove tutto il workload migra in una sola finestra. |
| **Blue-green** | Modello con due ambienti identici attivi, il cutover e un semplice redirect del traffico. |
| **Canary** | Modello che instrada gradualmente il traffico verso il nuovo ambiente (5% → 100%). |
| **PIR** | Post-Implementation Review: revisione formale a T+7d dal cutover. |
| **RACI** | Responsible, Accountable, Consulted, Informed: matrice di responsabilita. |
| **CAB** | Change Advisory Board: comitato che approva i cambiamenti ad alto rischio. |
| **Code freeze** | Periodo in cui nessuna modifica al codice o alla configurazione e permessa. |
| **Decision fatigue** | Degrado della qualita decisionale dopo periodi prolungati di decisioni sotto pressione. |
| **Error budget** | Quantita di downtime/errori accettabili prima di violare un SLO. |
| **SLO** | Service Level Objective: target interno di qualita del servizio. |
