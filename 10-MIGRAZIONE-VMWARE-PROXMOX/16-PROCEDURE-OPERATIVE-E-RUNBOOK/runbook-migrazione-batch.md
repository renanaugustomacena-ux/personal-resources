# Runbook: Migrazione Batch di VM da VMware a Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 6 — Operativa · Modulo 16.1 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 06 (strategie migrazione), 07 (networking), 08 (storage), 09 (scenari), 14 (automazione API). Familiarita con SOP / runbook operativi.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. seguire un runbook strutturato per migrazione batch (10-50 VM), con preflight check, esecuzione, validazione, criteri go/no-go;
> 2. distinguere passi che richiedono validazione manuale da passi che si automatizzano via API;
> 3. documentare deviazioni e lessons learned per migliorare la successiva iterazione.
> **Tempo stimato:** lettura 30-45 min + uso effettivo durante migrazione
> **Livello:** competent (Dreyfus 3); operativa
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** vedi tabella metadata sotto.

## Idee guida

1. **Un runbook NON e una guida didattica.** E una checklist operativa: passi numerati, comandi precisi, criteri di successo binari, trigger di rollback chiari.
2. **Lessons learned dopo ogni esecuzione.** Aggiornare il runbook subito dopo la migrazione; commit timestamped.
3. **Versione runbook deve match la versione tooling.** Comandi `qm` cambiano sottilmente fra Proxmox 7→8→9; documentare versione attesa.

---

| Campo | Valore |
|-------|--------|
| **Documento** | RB-MIG-002 |
| **Versione** | 1.0 |
| **Data creazione** | 2026-03-24 |
| **Ultima modifica** | 2026-03-24 |
| **Autore** | Team Infrastruttura |
| **Classificazione** | Uso interno |
| **Tempo stimato** | Variabile — dipende dal numero e dimensione delle VM nel batch |

---

## Indice

1. [Obiettivo e Ambito](#1-obiettivo-e-ambito)
2. [Principi della Migrazione Batch](#2-principi-della-migrazione-batch)
3. [Raggruppamento delle VM](#3-raggruppamento-delle-vm)
4. [Tracking Spreadsheet](#4-tracking-spreadsheet)
5. [Workflow di Migrazione Parallela](#5-workflow-di-migrazione-parallela)
6. [Pre-Batch Checklist](#6-pre-batch-checklist)
7. [Esecuzione del Batch](#7-esecuzione-del-batch)
8. [Monitoraggio del Progresso](#8-monitoraggio-del-progresso)
9. [Gestione Errori Mid-Batch](#9-gestione-errori-mid-batch)
10. [Validazione Post-Batch](#10-validazione-post-batch)
11. [Template di Comunicazione](#11-template-di-comunicazione)
12. [Procedura di Escalation](#12-procedura-di-escalation)
13. [Metriche e Reportistica](#13-metriche-e-reportistica)
14. [Lessons Learned](#14-lessons-learned)

---

## 1. Obiettivo e Ambito

### 1.1 Obiettivo

Definire la procedura operativa per la migrazione simultanea di più Virtual Machine (batch) dall'infrastruttura VMware vSphere a Proxmox VE. Una migrazione batch consente di migrare un gruppo logico di VM in una singola finestra di manutenzione, ottimizzando i tempi e riducendo il numero di interventi pianificati.

### 1.2 Definizioni

| Termine | Definizione |
|---------|------------|
| **Batch** | Gruppo di VM migrate nella stessa finestra di manutenzione |
| **Wave** | Macro-fase del progetto che comprende più batch |
| **Dependency Group** | Gruppo di VM che devono essere migrate insieme per vincoli applicativi |
| **Migration Lane** | Canale di migrazione parallelo gestito da un operatore |
| **Cutover Window** | Finestra temporale in cui il servizio è interrotto per il cutover |

### 1.3 Limiti Operativi

| Parametro | Limite Raccomandato | Limite Massimo |
|-----------|-------------------|----------------|
| VM per batch | 5-10 | 15 |
| Operatori per batch | 2-3 | 4 |
| Migration lane parallele | 2-3 | 4 |
| Durata massima batch | 6 ore | 10 ore |
| Dati totali per batch | 500 GB | 1 TB |

---

## 2. Principi della Migrazione Batch

### 2.1 Criteri di Raggruppamento

Le VM vengono raggruppate in batch secondo i seguenti criteri (in ordine di priorità):

1. **Dipendenza applicativa**: VM che appartengono allo stesso stack applicativo devono essere nello stesso batch
2. **Stessa VLAN/subnet**: VM nella stessa rete per semplificare la validazione
3. **Dimensione disco simile**: Per bilanciare i tempi di migrazione nelle lane parallele
4. **Stesso owner applicativo**: Per coordinare la validazione post-migrazione
5. **Priorità business**: VM meno critiche prima, per validare la procedura

### 2.2 Ordine di Priorità dei Batch

| Fase | Tipo di VM | Obiettivo |
|------|-----------|-----------|
| Pilot Batch | 2-3 VM non critiche (test/dev) | Validare la procedura end-to-end |
| Batch 1 | VM di sviluppo e test | Ridurre rischio, acquisire esperienza |
| Batch 2-N | VM di staging/pre-produzione | Validazione con carichi simili alla produzione |
| Batch N+1 | VM di produzione non critiche | Prime migrazioni di produzione |
| Batch Finale | VM di produzione critiche | Migrazione con massima attenzione |

### 2.3 Anti-Pattern da Evitare

- **NON** migrare nello stesso batch VM di produzione critiche e VM di test
- **NON** migrare domain controller e VM che dipendono da essi nello stesso batch
- **NON** superare la capacità di validazione del team (max 15 VM per batch)
- **NON** pianificare batch durante periodi di alto carico business
- **NON** procedere con un nuovo batch se il precedente ha problemi non risolti

---

## 3. Raggruppamento delle VM

### 3.1 Matrice di Raggruppamento

Per ogni VM dell'inventario, compilare la seguente matrice:

| VM Name | OS | Disco Totale (GB) | VLAN | Dependency Group | Owner | Priorità | Batch Proposto |
|---------|----|--------------------|------|-----------------|-------|----------|----------------|
| web-app-01 | Ubuntu 22.04 | 50 | 100 | WebApp Stack | Team Web | Media | Batch-03 |
| web-app-02 | Ubuntu 22.04 | 50 | 100 | WebApp Stack | Team Web | Media | Batch-03 |
| db-mysql-01 | Rocky 9 | 200 | 200 | WebApp Stack | Team DBA | Alta | Batch-03 |
| dev-tools-01 | Ubuntu 24.04 | 30 | 50 | Nessuno | Team Dev | Bassa | Batch-01 |
| monitoring-01 | Debian 12 | 100 | 300 | Monitoring | Team Ops | Alta | Batch-05 |

### 3.2 Identificazione delle Dipendenze

Per ogni dependency group, mappare le dipendenze:

```
WebApp Stack:
├── web-app-01 (frontend) → dipende da: db-mysql-01, redis-01
├── web-app-02 (frontend) → dipende da: db-mysql-01, redis-01
├── api-server-01 (backend) → dipende da: db-mysql-01, redis-01, rabbitmq-01
├── db-mysql-01 (database) → dipende da: nfs-storage-01 (backup)
├── redis-01 (cache) → nessuna dipendenza interna
└── rabbitmq-01 (queue) → nessuna dipendenza interna
```

**Regola**: Se le VM di un dependency group non possono essere migrate tutte nello stesso batch, migrare prima le VM indipendenti (es. redis, rabbitmq) e poi quelle con dipendenze (es. web, api, db).

### 3.3 Algoritmo di Ordinamento Migrazione Intra-Batch

All'interno di un singolo batch, l'ordine di migrazione delle VM segue questa logica:

1. **Prima**: VM senza dipendenze (cache, queue, utility)
2. **Poi**: VM database / backend
3. **Infine**: VM frontend / web server
4. **Load balancer**: Per ultimo, in modo che il cutover avvenga solo quando tutto il backend è pronto

### 3.4 Dimensionamento del Batch

Calcolare il tempo totale stimato per il batch:

```
Tempo_Batch = MAX(Lane_1_Time, Lane_2_Time, ..., Lane_N_Time) + Tempo_Validazione + Buffer

Dove:
  Lane_X_Time = SUM(Tempo_Migrazione_VM_i) per ogni VM assegnata alla lane X
  Tempo_Validazione = 30 min * Numero_VM (se in parallelo) o 15 min * Numero_VM (se sequenziale)
  Buffer = 30% del tempo totale stimato
```

Esempio:

```
Batch-03 (6 VM, 2 lane parallele):
  Lane 1: web-app-01 (2h) + web-app-02 (2h) + redis-01 (1h) = 5h
  Lane 2: db-mysql-01 (3h) + api-server-01 (2h) + rabbitmq-01 (1h) = 6h

  Tempo effettivo: MAX(5h, 6h) = 6h
  Validazione: 30 min * 6 = 3h (ma in parallelo ~1.5h)
  Buffer: (6h + 1.5h) * 30% = 2.25h

  Tempo totale stimato: 6h + 1.5h + 2.25h = ~10h
  → Troppo lungo per una singola finestra. Dividere in 2 batch.
```

---

## 4. Tracking Spreadsheet

### 4.1 Struttura dello Spreadsheet di Tracking

Creare un foglio di calcolo condiviso con le seguenti colonne:

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| Batch ID | Testo | Identificativo del batch (es. BATCH-003) |
| VM Name | Testo | Nome della VM |
| Migration Lane | Numero | Lane assegnata (1, 2, 3) |
| Operatore | Testo | Nome dell'operatore assegnato |
| Fase Corrente | Dropdown | Pre-Check / Export / Convert / Import / Config / Boot / Validate / Complete / Failed |
| Inizio Previsto | DateTime | Ora prevista di inizio |
| Inizio Effettivo | DateTime | Ora effettiva di inizio |
| Fine Prevista | DateTime | Ora prevista di completamento |
| Fine Effettiva | DateTime | Ora effettiva di completamento |
| Stato | Dropdown | In Attesa / In Corso / Completata / Errore / Rollback |
| % Completamento | Numero | Percentuale di avanzamento |
| Note | Testo | Annotazioni e problemi riscontrati |
| Validazione | Dropdown | Pending / Pass / Fail |
| Sign-off Owner | Testo | Nome e data del sign-off |

### 4.2 Dashboard di Sintesi

```
╔══════════════════════════════════════════════════╗
║           BATCH-003 — STATO MIGRAZIONE           ║
╠══════════════════════════════════════════════════╣
║ Data: 2026-04-15        Ora: 14:30               ║
║ Finestra: 08:00 - 18:00  Rimanente: 3h 30m       ║
╠══════════════════════════════════════════════════╣
║                                                   ║
║ Totale VM:      6                                 ║
║ Completate:     3  [██████████░░░░░░░░░░] 50%     ║
║ In Corso:       2  [████░░░░░░░░░░░░░░░░]         ║
║ In Attesa:      1  [██░░░░░░░░░░░░░░░░░░]         ║
║ Errore:         0                                  ║
║                                                   ║
║ Lane 1: web-app-02 [████████░░░░] 75% - Import    ║
║ Lane 2: api-server-01 [██████░░░░] 60% - Convert  ║
║                                                   ║
║ Prossima decisione GO/NO-GO: 16:00                ║
║ Rollback deadline: 17:00                          ║
╚══════════════════════════════════════════════════╝
```

### 4.3 Template Aggiornamento Stato (ogni 30 minuti)

```
[HH:MM] BATCH-003 Status Update
═══════════════════════════════
Lane 1 (Operatore: Mario):
  ✅ web-app-01: Completata — validazione OK
  🔄 web-app-02: Import in corso (ETA: 30 min)
  ⏳ redis-01: In attesa

Lane 2 (Operatore: Lucia):
  ✅ rabbitmq-01: Completata — validazione OK
  ✅ db-mysql-01: Completata — validazione OK
  🔄 api-server-01: Export in corso (ETA: 45 min)

Problemi: Nessuno
Prossimo aggiornamento: [HH:MM+30]
```

---

## 5. Workflow di Migrazione Parallela

### 5.1 Schema del Workflow

```
                    ┌─────────────────────┐
                    │   INIZIO BATCH       │
                    │   Go/No-Go Check     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Spegnere VM         │
                    │  (tutte le VM del    │
                    │   batch insieme)     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼────────┐ ┌────▼────────┐ ┌────▼────────┐
     │   LANE 1        │ │   LANE 2    │ │   LANE 3    │
     │                 │ │             │ │             │
     │ VM-A: Export    │ │ VM-D: Export│ │ VM-F: Export│
     │ VM-A: Convert   │ │ VM-D: Conv. │ │ VM-F: Conv. │
     │ VM-A: Import    │ │ VM-D: Import│ │ VM-F: Import│
     │ VM-A: Config    │ │ VM-D: Config│ │ VM-F: Config│
     │ VM-A: Boot      │ │ VM-D: Boot  │ │ VM-F: Boot  │
     │ VM-A: Validate  │ │ VM-D: Valid.│ │ VM-F: Valid. │
     │ ─── Avanti ──── │ │ ── Avanti──│ │ ── Avanti──│
     │ VM-B: Export    │ │ VM-E: Export│ │             │
     │ VM-B: Convert   │ │ VM-E: Conv. │ │  (Lane      │
     │ ...             │ │ ...         │ │   libera)   │
     └────────┬────────┘ └────┬────────┘ └────┬────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  VALIDAZIONE        │
                    │  POST-BATCH         │
                    │  (tutte le VM)      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  FINE BATCH         │
                    │  Sign-off & Report  │
                    └─────────────────────┘
```

### 5.2 Regole per le Lane Parallele

1. Ogni lane è gestita da un singolo operatore
2. L'operatore segue il runbook singola VM (RB-MIG-001) per ogni VM nella sua lane
3. Le lane operano indipendentemente — un problema su una lane non ferma le altre
4. L'export delle VM può essere parallelizzato se la rete lo consente
5. Se una lane finisce prima, l'operatore può prendere VM dalla lane più carica

### 5.3 Gestione Risorse Condivise

```bash
# Verificare la banda disponibile per trasferimento parallelo
# Regola: max 3 trasferimenti simultanei su link 10 Gbps
# max 2 trasferimenti simultanei su link 1 Gbps

# Monitorare la banda in tempo reale
iftop -i bond0 -n

# Monitorare il carico I/O sullo storage di staging
iostat -x 5

# Monitorare il carico I/O sullo storage Proxmox
pvesh get /nodes/$(hostname)/status | jq '.data.rootfs'
zpool iostat -v 1  # Se ZFS
ceph -s             # Se Ceph
```

---

## 6. Pre-Batch Checklist

### 6.1 Checklist T-7 Giorni (Una Settimana Prima)

| # | Attività | Responsabile | Stato | Note |
|---|----------|-------------|-------|------|
| 1 | Lista VM del batch confermata | Migration Lead | ☐ | |
| 2 | Dipendenze VM mappate e validate | Migration Lead | ☐ | |
| 3 | Owner applicativi informati e concordi | Migration Lead | ☐ | |
| 4 | Finestra di manutenzione approvata (Change Request) | Change Manager | ☐ | |
| 5 | Backup di tutte le VM verificato | Team Backup | ☐ | |
| 6 | Operatori assegnati e disponibili | Migration Lead | ☐ | |
| 7 | Lane assegnate e bilanciate | Migration Lead | ☐ | |
| 8 | Comunicazione pianificata inviata | Communication Lead | ☐ | |

### 6.2 Checklist T-1 Giorno (Il Giorno Prima)

| # | Attività | Responsabile | Stato | Note |
|---|----------|-------------|-------|------|
| 1 | Pre-check completato per tutte le VM del batch | Operatori | ☐ | |
| 2 | Schede tecniche VM compilate | Operatori | ☐ | |
| 3 | Storage di staging — spazio sufficiente verificato | Operatori | ☐ | |
| 4 | Storage Proxmox — spazio sufficiente verificato | Operatori | ☐ | |
| 5 | VMID assegnati per tutte le VM | Migration Lead | ☐ | |
| 6 | VLAN/Bridge verificati su Proxmox | Network Team | ☐ | |
| 7 | Driver VirtIO ISO presente su tutti i nodi Proxmox | Operatori | ☐ | |
| 8 | Canale di comunicazione batch pronto (chat/call) | Migration Lead | ☐ | |
| 9 | Tracking spreadsheet pronto e condiviso | Migration Lead | ☐ | |
| 10 | Backup on-demand eseguito per VM critiche | Team Backup | ☐ | |
| 11 | Conferma finale da owner applicativi | Migration Lead | ☐ | |
| 12 | Contatti di emergenza aggiornati | Migration Lead | ☐ | |

### 6.3 Checklist T-0 (Inizio Batch — Go/No-Go)

| # | Criterio Go/No-Go | Stato | Decisione |
|---|-------------------|-------|-----------|
| 1 | Tutti gli operatori presenti e pronti | ☐ | |
| 2 | Nessun incidente P1/P2 in corso | ☐ | |
| 3 | Storage di staging accessibile | ☐ | |
| 4 | Proxmox cluster healthy | ☐ | |
| 5 | VMware vCenter raggiungibile | ☐ | |
| 6 | Rete stabile (nessun allarme) | ☐ | |
| 7 | Backup di oggi completato con successo | ☐ | |
| 8 | Owner applicativi confermano go-ahead | ☐ | |
| 9 | Change Request approvato e in stato "implementazione" | ☐ | |
| 10 | Nessun blocco dell'ultimo minuto | ☐ | |

**Decisione**: ☐ **GO** — Procedere con il batch | ☐ **NO-GO** — Posticipare (motivazione: _________________)

**Approvazione Go/No-Go**:

| Ruolo | Nome | Firma/Conferma | Ora |
|-------|------|----------------|-----|
| Migration Lead | | | |
| IT Manager | | | |
| Owner Applicativo 1 | | | |
| Owner Applicativo 2 | | | |

---

## 7. Esecuzione del Batch

### 7.1 Fase 1: Shutdown Coordinato delle VM (T+0)

```bash
# Script per shutdown ordinato di tutte le VM del batch
# IMPORTANTE: Seguire l'ordine inverso delle dipendenze
# Prima i frontend, poi i backend, infine i database

# Ordine di shutdown (esempio):
# 1. Load balancer / frontend
# 2. Application server / API
# 3. Cache / Queue
# 4. Database

# PowerCLI — Shutdown ordinato
$batchVMs = @(
    @{Name="web-app-01"; Order=1; WaitSeconds=30},
    @{Name="web-app-02"; Order=1; WaitSeconds=30},
    @{Name="api-server-01"; Order=2; WaitSeconds=60},
    @{Name="redis-01"; Order=3; WaitSeconds=30},
    @{Name="rabbitmq-01"; Order=3; WaitSeconds=60},
    @{Name="db-mysql-01"; Order=4; WaitSeconds=120}
)

foreach ($group in ($batchVMs | Group-Object Order | Sort-Object Name)) {
    Write-Host "=== Shutdown gruppo $($group.Name) ==="
    foreach ($vm in $group.Group) {
        Write-Host "Shutting down $($vm.Name)..."
        Shutdown-VMGuest -VM $vm.Name -Confirm:$false
    }
    $waitTime = ($group.Group | Measure-Object WaitSeconds -Maximum).Maximum
    Write-Host "Attendere $waitTime secondi per lo shutdown completo..."
    Start-Sleep -Seconds $waitTime

    # Verificare lo shutdown
    foreach ($vm in $group.Group) {
        $state = (Get-VM -Name $vm.Name).PowerState
        if ($state -ne "PoweredOff") {
            Write-Warning "ATTENZIONE: $($vm.Name) ancora in stato $state — forzare lo stop?"
        }
    }
}
```

### 7.2 Fase 2: Export Parallelo (T+5 min)

Ogni operatore nella propria lane inizia l'export seguendo il runbook singola VM (RB-MIG-001, Fase 1):

```bash
# Lane 1 — Operatore 1
# Eseguire in sequenza per ogni VM assegnata
# Annotare inizio e fine di ogni operazione nel tracking spreadsheet

echo "[$(date '+%H:%M:%S')] Lane 1 — Inizio export web-app-01"
ovftool --noSSLVerify \
  "vi://admin@vcenter.local/DC/vm/web-app-01" \
  /mnt/staging/batch-003/web-app-01/

echo "[$(date '+%H:%M:%S')] Lane 1 — Export web-app-01 completato"
echo "[$(date '+%H:%M:%S')] Lane 1 — Inizio export web-app-02"
# ...continua
```

### 7.3 Fase 3: Conversione e Import (durante/dopo l'export)

La conversione e l'import possono iniziare non appena l'export di una VM è completato, senza attendere il completamento dell'export di tutte le VM:

```bash
# Esempio: Pipeline per una lane
# Mentre VM-A è in fase di import, VM-B può essere in fase di export

# VM-A: Conversione
qemu-img convert -f vmdk -O qcow2 -p \
  /mnt/staging/batch-003/web-app-01/web-app-01-disk1.vmdk \
  /mnt/staging/batch-003/web-app-01/web-app-01.qcow2

# VM-A: Creazione VM e Import (mentre VM-B è in export)
qm create 201 --name web-app-01 --memory 4096 --cores 2 --sockets 1 \
  --cpu cputype=x86-64-v2-AES --ostype l26 --net0 virtio,bridge=vmbr0,tag=100 \
  --scsihw virtio-scsi-single --bios seabios --agent enabled=1

qm importdisk 201 /mnt/staging/batch-003/web-app-01/web-app-01.qcow2 local-lvm
qm set 201 --scsi0 local-lvm:vm-201-disk-0,ssd=1,discard=on,iothread=1
qm set 201 --boot order=scsi0
```

### 7.4 Fase 4: Configurazione e Boot

Per ogni VM completata la fase di import:

```bash
# Completare la configurazione (vedi RB-MIG-001, Fase 4)
# Avviare la VM
qm start 201

# Quick validation
# Attendere 60 secondi per il boot
sleep 60
qm guest cmd 201 ping  # Verifica guest agent
ssh admin@192.168.100.x "hostname && uptime && systemctl --failed"
```

### 7.5 Fase 5: Validazione Rapida (per ogni VM)

Eseguire la validazione rapida (non completa) per procedere con la migrazione delle VM successive:

```bash
# Quick validation checklist per batch
VM_IP="192.168.100.x"
VM_NAME="web-app-01"

echo "=== Quick Validation: $VM_NAME ==="
echo -n "Ping: "; ping -c 1 -W 2 $VM_IP > /dev/null 2>&1 && echo "OK" || echo "FAIL"
echo -n "SSH: "; ssh -o ConnectTimeout=5 admin@$VM_IP "echo OK" 2>/dev/null || echo "FAIL"
echo -n "Hostname: "; ssh admin@$VM_IP "hostname" 2>/dev/null
echo -n "Services: "; ssh admin@$VM_IP "systemctl --failed | head -5" 2>/dev/null
echo -n "Disk: "; ssh admin@$VM_IP "df -h / | tail -1" 2>/dev/null
echo "=================================="
```

---

## 8. Monitoraggio del Progresso

### 8.1 Dashboard in Tempo Reale

Mantenere aggiornato il tracking spreadsheet con aggiornamenti ogni 15-30 minuti. Il Migration Lead monitora il progresso complessivo.

### 8.2 Script di Monitoraggio Automatico

```bash
#!/bin/bash
# monitor-batch.sh — Monitoraggio automatico stato batch
# Eseguire sul nodo Proxmox

BATCH_VMIDS=(201 202 203 204 205 206)

while true; do
    clear
    echo "╔══════════════════════════════════════════════╗"
    echo "║   BATCH MIGRATION MONITOR — $(date '+%H:%M:%S')        ║"
    echo "╠══════════════════════════════════════════════╣"

    for VMID in "${BATCH_VMIDS[@]}"; do
        STATUS=$(qm status $VMID 2>/dev/null | awk '{print $2}')
        NAME=$(qm config $VMID 2>/dev/null | grep "^name:" | awk '{print $2}')

        if [ -z "$STATUS" ]; then
            echo "║ VMID $VMID: non ancora creata                 ║"
        elif [ "$STATUS" == "running" ]; then
            AGENT=$(qm agent $VMID ping 2>/dev/null && echo "OK" || echo "N/A")
            echo "║ $VMID ($NAME): RUNNING | Agent: $AGENT    ║"
        else
            echo "║ $VMID ($NAME): $STATUS                    ║"
        fi
    done

    echo "╚══════════════════════════════════════════════╝"
    sleep 30
done
```

### 8.3 Checkpoint Temporali

Stabilire checkpoint fissi durante il batch per valutare il progresso:

| Checkpoint | Ora | Criterio | Azione se non raggiunto |
|-----------|-----|----------|------------------------|
| CP1 — Export completato | T+2h | Tutti gli export completati | Valutare riduzione scope batch |
| CP2 — 50% VM migrate | T+4h | Metà delle VM avviate e validate | Valutare prioritizzazione |
| CP3 — Go/No-Go finale | T+6h | Tutte le VM migrate | Decidere su VM rimanenti |
| CP4 — Validazione completa | T+8h | Tutte le validazioni OK | Decidere rollback parziale |
| CP5 — Rollback deadline | T+9h | Punto di non ritorno | Rollback di tutte le VM non validate |

---

## 9. Gestione Errori Mid-Batch

### 9.1 Classificazione degli Errori

| Severità | Descrizione | Impatto sul Batch | Azione |
|----------|------------|-------------------|--------|
| **S1 — Critico** | Errore che blocca l'intera infrastruttura (es. storage down, rete down) | Blocco totale | Stop batch, valutare rollback totale |
| **S2 — Alto** | Errore che blocca una lane (es. conversione fallita) | Blocco parziale | Bypassare VM, continuare lane |
| **S3 — Medio** | Errore su singola VM (es. boot failure) | Nessun impatto su altre VM | Troubleshoot o rollback singola VM |
| **S4 — Basso** | Warning non bloccante (es. guest agent non installato) | Nessuno | Annotare e risolvere post-batch |

### 9.2 Procedura Errore S1 — Blocco Critico

```
1. STOP — Fermare tutte le operazioni su tutte le lane
2. COMUNICARE — Informare il Migration Lead e l'IT Manager
3. VALUTARE — Analizzare l'impatto (quante VM sono già migrate? Quali servizi sono down?)
4. DECIDERE:
   a) Se il problema è risolvibile in < 30 min → risolvere e continuare
   b) Se il problema non è risolvibile rapidamente → ROLLBACK TOTALE
5. ESEGUIRE la decisione
6. DOCUMENTARE tutto
```

### 9.3 Procedura Errore S2/S3 — Errore su Lane/VM

```
1. ISOLARE — L'errore riguarda solo questa VM/lane
2. ANNOTARE — Documentare l'errore nel tracking spreadsheet
3. DECIDERE:
   a) Se il troubleshooting richiede < 15 min → tentare la risoluzione
   b) Se il troubleshooting richiede > 15 min → SKIP (saltare la VM)
4. Se SKIP:
   a) Annotare la VM come "Failed — da ripianificare"
   b) Se la VM era critica per il dependency group, valutare rollback del gruppo
   c) Continuare con le altre VM della lane
5. POST-BATCH: Analizzare l'errore e ripianificare la migrazione della VM
```

### 9.4 Decision Tree per Errori Mid-Batch

```
Errore rilevato
├── Impatta l'intera infrastruttura?
│   ├── SÌ → Errore S1 → STOP BATCH
│   │   ├── Risolvibile in < 30 min?
│   │   │   ├── SÌ → Risolvere e continuare
│   │   │   └── NO → ROLLBACK TOTALE
│   │   └── (Escalation a IT Manager)
│   │
│   └── NO → Impatta la singola VM?
│       ├── SÌ → Errore S2/S3
│       │   ├── Risolvibile in < 15 min?
│       │   │   ├── SÌ → Troubleshoot
│       │   │   └── NO → SKIP VM
│       │   │       ├── VM ha dipendenze critiche nel batch?
│       │   │       │   ├── SÌ → Rollback dependency group
│       │   │       │   └── NO → Continuare batch
│       │   │       └── Ripianificare migrazione VM
│       │   └── (Annotare nel tracking)
│       │
│       └── Warning non bloccante → Errore S4
│           └── Annotare e continuare
```

### 9.5 Rollback Parziale (Solo VM Specifiche)

```bash
# Rollback di una singola VM dal batch
VMID_ROLLBACK=203
VM_NAME="api-server-01"

# 1. Spegnere la VM su Proxmox
qm stop $VMID_ROLLBACK

# 2. Riaccendere la VM originale su VMware
# (Da vCenter o PowerCLI)
# Start-VM -VM $VM_NAME

# 3. Verificare la VM VMware
ping -c 3 IP_ORIGINALE_VM

# 4. Annotare nel tracking spreadsheet
echo "[$(date)] ROLLBACK: $VM_NAME ($VMID_ROLLBACK) — VM riaccesa su VMware"

# 5. Le altre VM del batch continuano normalmente
```

---

## 10. Validazione Post-Batch

### 10.1 Validazione Completa di Tutte le VM

Dopo che tutte le VM del batch sono state migrate e hanno superato la quick validation, eseguire la validazione completa:

```bash
#!/bin/bash
# validate-batch.sh — Validazione completa batch

BATCH_VMS=(
    "201:web-app-01:192.168.100.10:linux"
    "202:web-app-02:192.168.100.11:linux"
    "203:api-server-01:192.168.100.20:linux"
    "204:redis-01:192.168.100.30:linux"
    "205:rabbitmq-01:192.168.100.31:linux"
    "206:db-mysql-01:192.168.100.40:linux"
)

echo "╔══════════════════════════════════════╗"
echo "║  VALIDAZIONE POST-BATCH BATCH-003   ║"
echo "║  $(date '+%Y-%m-%d %H:%M:%S')                  ║"
echo "╚══════════════════════════════════════╝"

PASS=0
FAIL=0

for VM_ENTRY in "${BATCH_VMS[@]}"; do
    IFS=':' read -r VMID NAME IP OS <<< "$VM_ENTRY"
    echo ""
    echo "=== Validazione $NAME (VMID: $VMID, IP: $IP) ==="

    CHECKS_OK=0
    CHECKS_TOTAL=0

    # Check 1: VM running su Proxmox
    ((CHECKS_TOTAL++))
    STATUS=$(qm status $VMID | awk '{print $2}')
    if [ "$STATUS" == "running" ]; then
        echo "  [PASS] VM status: running"
        ((CHECKS_OK++))
    else
        echo "  [FAIL] VM status: $STATUS"
    fi

    # Check 2: Ping
    ((CHECKS_TOTAL++))
    if ping -c 1 -W 3 $IP > /dev/null 2>&1; then
        echo "  [PASS] Ping: reachable"
        ((CHECKS_OK++))
    else
        echo "  [FAIL] Ping: unreachable"
    fi

    # Check 3: SSH
    ((CHECKS_TOTAL++))
    if ssh -o ConnectTimeout=5 -o BatchMode=yes admin@$IP "echo OK" > /dev/null 2>&1; then
        echo "  [PASS] SSH: connected"
        ((CHECKS_OK++))
    else
        echo "  [FAIL] SSH: connection failed"
    fi

    # Check 4: Guest Agent
    ((CHECKS_TOTAL++))
    if qm agent $VMID ping > /dev/null 2>&1; then
        echo "  [PASS] QEMU Guest Agent: active"
        ((CHECKS_OK++))
    else
        echo "  [WARN] QEMU Guest Agent: not responding"
    fi

    # Check 5: DNS resolution
    ((CHECKS_TOTAL++))
    RESOLVED_IP=$(dig +short $NAME.dominio.local)
    if [ "$RESOLVED_IP" == "$IP" ]; then
        echo "  [PASS] DNS: $NAME.dominio.local → $IP"
        ((CHECKS_OK++))
    else
        echo "  [FAIL] DNS: $NAME.dominio.local → $RESOLVED_IP (atteso: $IP)"
    fi

    echo "  Risultato: $CHECKS_OK/$CHECKS_TOTAL checks superati"

    if [ $CHECKS_OK -eq $CHECKS_TOTAL ]; then
        ((PASS++))
    else
        ((FAIL++))
    fi
done

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  RIEPILOGO VALIDAZIONE              ║"
echo "║  VM Pass: $PASS | VM Fail: $FAIL           ║"
echo "╚══════════════════════════════════════╝"
```

### 10.2 Test delle Dipendenze Inter-VM

```bash
# Verificare che le dipendenze applicative funzionino

# Test 1: Frontend → Backend
curl -s -o /dev/null -w "%{http_code}" http://web-app-01.dominio.local/api/health
# Atteso: 200

# Test 2: Backend → Database
ssh admin@api-server-01 "mysql -h db-mysql-01 -u app -p'password' -e 'SELECT 1'"
# Atteso: risultato senza errori

# Test 3: Backend → Redis
ssh admin@api-server-01 "redis-cli -h redis-01 ping"
# Atteso: PONG

# Test 4: Backend → RabbitMQ
ssh admin@api-server-01 "curl -s -u guest:guest http://rabbitmq-01:15672/api/overview | jq '.node'"
# Atteso: nome nodo RabbitMQ
```

### 10.3 Validazione Performance

```bash
# Confrontare le performance con la baseline pre-migrazione

# CPU
ssh admin@$IP "vmstat 1 5 | tail -1"

# Disco I/O
ssh admin@$IP "iostat -x 1 5 | tail -5"

# Latenza rete
ping -c 20 $IP | tail -1
# Confrontare con la baseline
```

### 10.4 Sign-Off Post-Batch

| VM | Owner Applicativo | Validazione Funzionale | Sign-Off | Data/Ora |
|----|-------------------|----------------------|----------|----------|
| web-app-01 | | ☐ Pass ☐ Fail | | |
| web-app-02 | | ☐ Pass ☐ Fail | | |
| api-server-01 | | ☐ Pass ☐ Fail | | |
| redis-01 | | ☐ Pass ☐ Fail | | |
| rabbitmq-01 | | ☐ Pass ☐ Fail | | |
| db-mysql-01 | | ☐ Pass ☐ Fail | | |

---

## 11. Template di Comunicazione

### 11.1 Comunicazione Pre-Batch (T-7 giorni)

```
Oggetto: [MANUTENZIONE PROGRAMMATA] Migrazione Batch VM — GG/MM/AAAA

Gentili colleghi,

nell'ambito del progetto di migrazione da VMware a Proxmox VE, è programmata
la migrazione di un gruppo di Virtual Machine (Batch BATCH-003).

Dettagli:
━━━━━━━━
Data: GG/MM/AAAA
Orario: dalle HH:MM alle HH:MM
Durata prevista downtime: X ore

VM coinvolte:
- web-app-01 (Servizio Web Portale)
- web-app-02 (Servizio Web Portale)
- api-server-01 (API Backend)
- redis-01 (Cache)
- rabbitmq-01 (Message Queue)
- db-mysql-01 (Database)

Servizi impattati:
- Portale Web Aziendale (non disponibile durante la migrazione)
- API di integrazione (non disponibile durante la migrazione)

Azioni richieste:
- Nessuna azione richiesta da parte vostra
- Eventuali processi batch che utilizzano le API dovranno essere
  ripianificati dopo l'orario di fine manutenzione

Per informazioni: infrastruttura@dominio.local | Tel. XXXX

Cordiali saluti,
Team Infrastruttura
```

### 11.2 Comunicazione Inizio Batch (T+0)

```
Oggetto: [IN CORSO] Migrazione Batch BATCH-003 — Inizio Manutenzione

La manutenzione programmata per la migrazione Batch BATCH-003 è iniziata.

Inizio: HH:MM
Fine prevista: HH:MM

I servizi indicati nella comunicazione precedente non sono al momento disponibili.
Invieremo aggiornamenti ogni 2 ore.

Prossimo aggiornamento: HH:MM
```

### 11.3 Aggiornamento Stato (ogni 2 ore)

```
Oggetto: [AGGIORNAMENTO] Migrazione Batch BATCH-003 — Stato ore HH:MM

Stato attuale della migrazione:

Completate: X/Y VM (XX%)
In corso: X VM
In attesa: X VM
Problemi: [Nessuno / Descrizione]

Fine prevista: HH:MM [Confermata / Posticipata a HH:MM]

Prossimo aggiornamento: HH:MM
```

### 11.4 Comunicazione Fine Batch

```
Oggetto: [COMPLETATA] Migrazione Batch BATCH-003 — Servizi Ripristinati

La migrazione Batch BATCH-003 è stata completata con successo.

Riepilogo:
━━━━━━━━━
VM migrate: 6/6 (100%)
Downtime effettivo: X ore Y minuti
Problemi riscontrati: [Nessuno / Descrizione]

Tutti i servizi sono stati ripristinati e verificati.

In caso di anomalie, contattare immediatamente:
📧 infrastruttura@dominio.local
📞 Tel. XXXX (reperibilità 24/7)

Cordiali saluti,
Team Infrastruttura
```

---

## 12. Procedura di Escalation

### 12.1 Matrice di Escalation

| Livello | Condizione | Chi viene contattato | Tempo di Risposta |
|---------|-----------|---------------------|-------------------|
| L0 | Problema su singola VM | Operatore della lane | Immediato |
| L1 | Problema non risolvibile in 15 min | Migration Lead | 5 min |
| L2 | Problema che richiede rollback parziale | IT Manager | 10 min |
| L3 | Problema che richiede rollback totale | CTO / Direzione IT | 15 min |
| L4 | Problema con impatto su servizi critici aziendali | Comitato di Crisi | 30 min |

### 12.2 Contatti di Emergenza

| Ruolo | Nome | Telefono | Email | Disponibilità |
|-------|------|----------|-------|---------------|
| Migration Lead | __________ | __________ | __________ | Durante batch |
| IT Manager | __________ | __________ | __________ | Reperibile |
| Network Admin | __________ | __________ | __________ | Reperibile |
| Storage Admin | __________ | __________ | __________ | Reperibile |
| DBA | __________ | __________ | __________ | Reperibile |
| Vendor Support (Proxmox) | __________ | __________ | __________ | Ticket |
| Vendor Support (VMware) | __________ | __________ | __________ | Ticket |

### 12.3 Template Escalation

```
ESCALATION — BATCH-003 — LIVELLO [X]

Data/Ora: GG/MM/AAAA HH:MM
Riportato da: [NOME]
Livello di escalation: [L1/L2/L3/L4]

Descrizione del problema:
[Descrizione chiara e concisa]

Impatto:
- VM coinvolte: [elenco]
- Servizi impattati: [elenco]
- Utenti impattati: [numero/dipartimenti]

Tentativi di risoluzione:
1. [Tentativo 1 — risultato]
2. [Tentativo 2 — risultato]

Azione richiesta:
[Cosa si chiede alla persona a cui si scala]

Decisione urgente richiesta:
☐ Continuare troubleshooting (tempo stimato: X min)
☐ Rollback singola VM
☐ Rollback dependency group
☐ Rollback totale batch
☐ Altro: _______________
```

---

## 13. Metriche e Reportistica

### 13.1 Metriche per Batch

| Metrica | Valore | Target |
|---------|--------|--------|
| Numero VM migrate | __/__ | 100% |
| Tempo totale batch | __ ore | < finestra pianificata |
| Downtime medio per VM | __ min | < 2 ore |
| Numero errori S1 | __ | 0 |
| Numero errori S2/S3 | __ | < 2 |
| Numero rollback | __ | 0 |
| Velocità media migrazione | __ GB/ora | > 50 GB/ora |
| Tempo medio validazione per VM | __ min | < 30 min |
| Soddisfazione owner (1-5) | __ | >= 4 |

### 13.2 Report Post-Batch

Compilare entro 24 ore dal completamento del batch:

```
REPORT POST-BATCH — BATCH-003
══════════════════════════════

1. SOMMARIO ESECUTIVO
   - Batch: BATCH-003
   - Data: GG/MM/AAAA
   - Durata: X ore Y minuti
   - Esito: Successo / Successo parziale / Fallimento
   - VM migrate: X/Y

2. DETTAGLIO PER VM
   [Tabella con stato di ogni VM]

3. PROBLEMI RISCONTRATI
   [Elenco problemi con root cause e risoluzione]

4. TEMPISTICHE
   - Inizio pianificato: HH:MM | Inizio effettivo: HH:MM
   - Fine pianificata: HH:MM | Fine effettiva: HH:MM
   - Scostamento: +/- X minuti

5. LESSONS LEARNED
   [Cosa è andato bene, cosa migliorare]

6. AZIONI CORRETTIVE
   [Azioni da implementare prima del prossimo batch]
```

---

## 14. Lessons Learned

### 14.1 Template Lessons Learned

Dopo ogni batch, compilare:

| # | Categoria | Descrizione | Impatto | Azione Correttiva | Responsabile | Scadenza |
|---|-----------|------------|---------|-------------------|-------------|----------|
| 1 | Processo | | | | | |
| 2 | Tecnico | | | | | |
| 3 | Comunicazione | | | | | |
| 4 | Tooling | | | | | |

### 14.2 Revisione Continua del Runbook

Dopo ogni batch:

1. Aggiornare il runbook con le lesson learned
2. Aggiornare le tempistiche stimate basandosi sui dati reali
3. Aggiornare i limiti operativi se necessario
4. Condividere le lessons learned con tutto il team prima del batch successivo
5. Aggiornare gli script di automazione con eventuali fix

### 14.3 Trend Analysis

Monitorare i seguenti trend attraverso i batch:

- Tempo medio di migrazione per GB — dovrebbe diminuire
- Numero di errori per batch — dovrebbe diminuire
- Tempo di validazione per VM — dovrebbe diminuire
- Numero di rollback — dovrebbe essere zero
- Soddisfazione degli owner applicativi — dovrebbe aumentare

---

**Fine del documento — RB-MIG-002 v1.0**

---

## Esercizi

1. **Lab — eseguire una migrazione batch simulata.** Su lab di test, applicare il runbook a 5 VM throwaway: pre-flight check, batch convert, validation, rollback simulato. Documentare ogni deviazione.
2. **Stretch — runbook automation script.** Trasformare il runbook in script Python che esegue ogni passo con dry-run mode + apply mode + report finale strutturato.

## Letture primarie consigliate

- Modulo 06.1-06.3 — Strategie di migrazione (cold/warm/live).
- Modulo 14.2 — `../14-AUTOMAZIONE-E-INFRASTRUCTURE-AS-CODE/proxmox-api-automazione-script.md`: API per automazione runbook.
- ITIL 4 — Service Operations (best practice runbook).

## Collegamenti incrociati

- Modulo 16.2 — `runbook-migrazione-cluster-completo.md`: runbook a scala completa.
- Modulo 18 (nuovo) — `../18-PRODUCTION-CUTOVER-RUNBOOK.md`: runbook dettagliato per cutover finale.
