# Backup e Ripristino Windows — Guida Completa

> **Modulo 15** · **Aggiornamento:** 2026-05-24

| Campo | Valore |
|---|---|
| **Modulo del corso** | Amministrazione Windows enterprise |
| **Prerequisiti** | Conoscenza dello storage Windows e VSS (→ `07-storage-windows.md`), familiarità con Active Directory per System State (→ `01-active-directory.md`), padronanza di PowerShell base (→ `02-powershell.md`) |
| **Obiettivi di apprendimento** | 1) Progettare una strategia di backup conforme alla regola 3-2-1 con RPO/RTO definiti · 2) Configurare Windows Server Backup e VSS per snapshot consistenti · 3) Eseguire e verificare System State backup e bare metal recovery · 4) Implementare soluzioni enterprise con Veeam, DPM e Azure Backup · 5) Pianificare e testare procedure di disaster recovery per AD, SQL, Exchange e Hyper-V |
| **Tempo stimato** | lettura 100 min · lab 120 min |
| **Livello** | Proficient |
| **Ultimo aggiornamento** | 2026-05-24 |

## Idee guida
1. **Windows Server Backup (built-in) basico.**
2. **Veeam Backup & Replication enterprise standard.**
3. **VSS (Volume Shadow Copy) per consistent snapshot.**
4. **System State backup per AD + registry.**
5. **Azure Backup per protezione cloud-native e ibrida.**
6. **DPM (Data Protection Manager) per scenari enterprise on-premises.**
7. **SQL Server / Exchange / Hyper-V backup specializzati.**
8. **PowerShell e Robocopy per automazione backup file-level.**
9. **Disaster recovery planning strutturato con test periodici.**


## Indice

- [Panoramica](#panoramica)
- [Strategia di Backup](#strategia-di-backup)
- [Windows Server Backup](#windows-server-backup)
- [Volume Shadow Copy (VSS)](#volume-shadow-copy-vss)
- [System State Backup](#system-state-backup)
- [SQL Server Backup](#sql-server-backup)
- [Exchange e Microsoft 365 Backup](#exchange-e-microsoft-365-backup)
- [Hyper-V Backup](#hyper-v-backup)
- [Azure Backup](#azure-backup)
- [Veeam Backup & Replication](#veeam-backup--replication)
- [DPM — Data Protection Manager](#dpm--data-protection-manager)
- [Active Directory Recovery](#active-directory-recovery)
- [Bare Metal Recovery](#bare-metal-recovery)
- [PowerShell Backup Automation](#powershell-backup-automation)
- [Robocopy per Backup File-Level](#robocopy-per-backup-file-level)
- [Disaster Recovery Planning](#disaster-recovery-planning)
- [Backup Testing — Schedule e Checklist](#backup-testing--schedule-e-checklist)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

Il backup in ambiente Windows Server protegge da: guasti hardware, errori umani, ransomware, corruzione dati e disastri. Una strategia completa include backup regolari (dati + System State), shadow copy per recovery rapido, bare metal per DR completo, e procedure testate di ripristino Active Directory.

### Componenti dell'ecosistema di backup Windows

| Componente | Funzione | Scope |
|-----------|----------|-------|
| Windows Server Backup | Backup built-in con wbadmin/PS | Volumi, System State, BMR |
| Volume Shadow Copy (VSS) | Snapshot point-in-time per consistency | File recovery self-service |
| Azure Backup | Backup-as-a-Service cloud Microsoft | File, VM, SQL, ibrido |
| Veeam B&R | Piattaforma enterprise terze parti | VM, fisici, cloud, SaaS |
| DPM | System Center Data Protection Manager | On-premises enterprise |
| SQL Server Backup | Backup nativo motore database | Full, diff, log, PITR |
| Exchange DAG | Alta disponibilità database posta | Replica continua |
| Hyper-V Checkpoint | Snapshot VM per test/rollback | Dev/test, production checkpoints |
| Robocopy | Copia file-level con delta sync | Mirror cartelle, migrazione |

### Terminologia fondamentale

| Termine | Definizione |
|---------|------------|
| RPO (Recovery Point Objective) | Quantità massima di dati che si accetta di perdere. Un RPO di 1 ora significa che il backup più vecchio ammesso ha al massimo 1 ora |
| RTO (Recovery Time Objective) | Tempo massimo entro cui il servizio deve tornare operativo dopo un disastro |
| RPA (Recovery Point Actual) | RPO effettivamente misurato nei test. Deve essere ≤ RPO dichiarato |
| RTA (Recovery Time Actual) | RTO effettivamente misurato nei test. Deve essere ≤ RTO dichiarato |
| MTPD (Maximum Tolerable Period of Disruption) | Durata massima di interruzione prima di impatto irreversibile sul business |
| Backup Window | Finestra temporale disponibile per eseguire il backup senza impatto sulle operazioni |
| Retention | Periodo di conservazione dei backup prima dell'eliminazione automatica |
| GFS (Grandfather-Father-Son) | Schema di rotazione: giornaliero (figlio), settimanale (padre), mensile (nonno) |
| Air-Gap | Separazione fisica o logica del backup dalla rete di produzione |
| Deduplication | Eliminazione blocchi duplicati per ridurre lo spazio occupato |

---

## Strategia di Backup

### RPO e RTO — Definizioni operative

```
RPO = Recovery Point Objective
    Quanti dati posso permettermi di perdere in caso di disastro.
    Determina la FREQUENZA del backup.
    RPO 1 ora → backup almeno ogni ora.
    RPO 15 minuti → transaction log backup ogni 15 minuti (SQL).

RTO = Recovery Time Objective
    In quanto tempo devo ripristinare il servizio.
    Determina il METODO di backup e la velocità del restore.
    RTO 15 minuti → instant VM recovery (Veeam), hot standby.
    RTO 4 ore → restore da disco locale.
    RTO 24 ore → restore da tape o cloud.

RELAZIONE RPO/RTO:
    RPO aggressivo + RTO aggressivo = costo elevato (replica sincrona, hot standby)
    RPO rilassato + RTO rilassato = costo basso (backup giornaliero su tape)
    
    La scelta dipende dall'analisi BIA (Business Impact Analysis):
    quanto costa al business ogni ora di downtime vs costo della soluzione.
```

### Classificazione dei dati per backup

```
TIER 1 — Mission Critical (RPO ≤ 15 min, RTO ≤ 1 ora)
    Active Directory, database transazionali, sistemi ERP/CRM
    → Replica sincrona + backup frequente + instant recovery

TIER 2 — Business Critical (RPO ≤ 4 ore, RTO ≤ 4 ore)
    File server, email, application server
    → Backup incrementale frequente + restore da disco

TIER 3 — Business Important (RPO ≤ 24 ore, RTO ≤ 24 ore)
    Archivi, sistemi sviluppo, documentazione
    → Backup giornaliero + restore da disco o cloud

TIER 4 — Non Critical (RPO ≤ 1 settimana, RTO ≤ 1 settimana)
    Dati temporanei, ambienti di test riproducibili
    → Backup settimanale o su richiesta
```

### Regola 3-2-1

```
3 copie dei dati (produzione + 2 backup)
2 media diversi (disco locale + remoto/cloud/tape)
1 copia offsite (fuori sede per DR)

Estensione moderna: 3-2-1-1-0
+1 copia offline/air-gapped (protezione ransomware)
+0 errori verificati (testare i restore!)
```

### Tipi di Backup

| Tipo | Cosa Salva | Velocità | Restore | Uso |
|------|-----------|----------|---------|-----|
| Full | Tutto | Lento | Veloce (1 set) | Base settimanale |
| Incremental | Solo modifiche dall'ultimo backup (full o incr) | Veloce | Lento (chain) | Giornaliero |
| Differential | Modifiche dall'ultimo full | Medio | Medio (full + diff) | Alternativa |
| Copy | Tutto (senza resettare archive bit) | Lento | Veloce | Ad-hoc |

#### Confronto catene di restore

```
INCREMENTAL:
    Full (Dom) → Inc (Lun) → Inc (Mar) → Inc (Mer) → Inc (Gio) → Inc (Ven)
    Restore venerdì = Full + Inc(Lun) + Inc(Mar) + Inc(Mer) + Inc(Gio) + Inc(Ven)
    6 set necessari. Se uno manca nella chain, restore impossibile.

DIFFERENTIAL:
    Full (Dom) → Diff (Lun) → Diff (Mar) → Diff (Mer) → Diff (Gio) → Diff (Ven)
    Restore venerdì = Full + Diff(Ven)
    2 set necessari. Più robusto ma i diff crescono durante la settimana.

INCREMENTAL FOREVER (Veeam, Azure):
    Full sintetico generato periodicamente dal software.
    Solo incrementali trasmessi in rete → risparmio bandwidth.
    Restore: il software ricostruisce il full dall'ultima catena.

REVERSE INCREMENTAL (Veeam):
    L'ultimo backup è sempre un full virtuale.
    Restore del punto più recente = lettura singolo file.
    I punti precedenti richiedono merge con i delta inversi.
```

### Schedule Tipo

```
Domenica:   Full backup
Lunedì:     Incremental
Martedì:    Incremental
Mercoledì:  Incremental
Giovedì:    Incremental
Venerdì:    Incremental
Sabato:     Incremental

Retention: 4 settimane giornaliero, 12 mesi settimanale, 7 anni annuale
```

### Schema GFS (Grandfather-Father-Son)

```
Son (Figlio)    = Backup giornaliero    → Retention 14-30 giorni
Father (Padre)  = Backup settimanale    → Retention 4-12 settimane
Grandfather     = Backup mensile        → Retention 12-84 mesi (compliance)

Implementazione:
    Giornaliero: incrementale, Mon-Sat
    Settimanale: full sintetico o full, ogni domenica. Il backup di domenica
                 diventa anche il settimanale. Marcato come "GFS Weekly".
    Mensile:     il primo full del mese marcato come "GFS Monthly".
    Annuale:     il primo full di gennaio marcato come "GFS Yearly".

Veeam GFS: configurabile in Backup Job → Schedule → GFS Retention.
Azure Backup: Policy → Long-Term Retention → Weekly/Monthly/Yearly.
```

### Strategie Anti-Ransomware — Backup Immutabili e Air-Gap

```
CONTESTO ATTUALE:
    Secondo il Verizon 2025 Data Breach Investigations Report, il 44% di tutte
    le violazioni di dati nel 2025 ha coinvolto ransomware. Dato ancora più
    allarmante: l'89% delle vittime ransomware intervistate ha dichiarato che
    i propri repository di backup sono stati presi di mira dagli attaccanti.

    La sola regola 3-2-1 non è più sufficiente se tutte le copie sono
    raggiungibili dalla stessa rete con le stesse credenziali.
    L'estensione 3-2-1-1-0 aggiunge:
    +1 copia IMMUTABILE o AIR-GAPPED
    +0 errori di restore verificati

IMMUTABILITÀ — Implementazioni concrete:

    1. Veeam Linux Hardened Repository
       - Repository Linux dedicato con XFS
       - Immutabilità a livello file system tramite chattr +i
       - Nemmeno root può cancellare i backup durante la finestra di retention
       - L'account di connessione Veeam è un utente non-root con accesso SSH
         monouso (single-use credentials per l'installazione)
       - Dopo l'installazione, l'accesso SSH può essere disabilitato
       - Nessuna porta in ascolto tranne quella del transport service Veeam

    2. Azure Immutable Vault
       - Recovery Services Vault con immutabilità abilitata a livello vault
       - Azure Portal → Vault → Properties → Immutability → Enable
       - Due modalità:
         a) Locked: irreversibile, nemmeno l'admin Azure può disabilitare
         b) Unlocked: può essere disabilitata (per ambienti di test)
       - Soft delete abilitato di default (14 giorni di protezione aggiuntiva)
       - Multi-User Authorization: richiede approvazione di un secondo admin
         per operazioni distruttive (cancellazione backup, disabilitazione
         immutabilità, modifica policy di retention)

    3. AWS S3 Object Lock (WORM)
       - Compliance Mode: nemmeno l'account root AWS può cancellare
       - Governance Mode: utenti con permessi specifici possono rimuovere
       - Usato con Veeam Scale-Out Backup Repository → Capacity Tier
       - Retention configurabile per oggetto o per bucket

    4. Tape offline / Air-Gap fisico
       - La forma più antica e ancora più resiliente di air-gap
       - Tape estratta dalla library e conservata in cassaforte ignifuga
         fuori sede (bunker, caveau bancario, sito DR)
       - Nessuna connessione di rete = nessun attacco remoto possibile
       - Limitazione: RTO elevato (recuperare la tape + restore)

AIR-GAP LOGICO (Virtual Air-Gap):
    - Segmento di rete isolato (VLAN dedicata) per il repository di backup
    - Firewall rules: solo il Veeam server può comunicare con il repository
    - Nessuna route verso Internet dal segmento backup
    - Credenziali separate: l'account backup NON è Domain Admin
    - MFA obbligatoria per accesso alla console di backup
    - Jump server dedicato per amministrazione del backup

SEPARAZIONE DELLE CREDENZIALI:
    - L'account di backup (es. svc-backup@corp.contoso.com) appartiene
      SOLO al gruppo Backup Operators, NON a Domain Admins
    - La console Veeam / DPM ha un proprio set di credenziali admin
    - Il repository Linux ha credenziali locali (non AD-joined)
    - L'accesso al vault Azure usa un Service Principal dedicato
    - Se il ransomware compromette un Domain Admin, i backup restano protetti

MONITORAGGIO ANOMALIE:
    - Alert se la dimensione del backup cambia drasticamente
      (compressione anomala → possibile encryption ransomware)
    - Alert se i backup vengono cancellati manualmente
    - Alert se le policy di retention vengono modificate
    - Alert se un numero anomalo di file cambia tra incrementali
    - Veeam ONE: dashboard dedicata per ransomware detection
    - Azure Monitor: alert su operazioni distruttive nel vault
```

---

## Windows Server Backup

### Installazione e Configurazione

```powershell
# Installare
Install-WindowsFeature Windows-Server-Backup -IncludeManagementTools

# Backup completo del server
wbadmin start backup -backupTarget:E: -include:C: -allCritical -vssFull -quiet

# Backup specifici volumi
wbadmin start backup -backupTarget:E: -include:C:,D: -vssFull -quiet

# Backup su share di rete
wbadmin start backup -backupTarget:\\BACKUP-SRV\Backups -include:C: `
    -allCritical -vssFull -user:CORP\svc-backup -password:P@ss -quiet

# System State backup
wbadmin start systemstatebackup -backupTarget:E: -quiet

# Backup con PowerShell (più granulare)
$policy = New-WBPolicy
$volume = Get-WBVolume -AllVolumes | Where-Object MountPath -eq "C:"
Add-WBVolume -Policy $policy -Volume $volume
Add-WBSystemState -Policy $policy
$target = New-WBBackupTarget -VolumePath "E:"
Add-WBBackupTarget -Policy $policy -Target $target
Set-WBVssBackupOption -Policy $policy -VssFullBackup
Start-WBBackup -Policy $policy
```

### Backup di file e cartelle specifiche

```powershell
# Aggiungere file spec alla policy
$policy = New-WBPolicy
$filespec = New-WBFileSpec -FileSpec "D:\Shares\Contabilita"
Add-WBFileSpec -Policy $policy -FileSpec $filespec

# Escludere sottocartelle
$exclude = New-WBFileSpec -FileSpec "D:\Shares\Contabilita\Temp" -Exclude
Add-WBFileSpec -Policy $policy -FileSpec $exclude

$target = New-WBBackupTarget -NetworkPath "\\BACKUP-SRV\Backups" `
    -Credential (Get-Credential)
Add-WBBackupTarget -Policy $policy -Target $target
Start-WBBackup -Policy $policy
```

### Restore da Windows Server Backup

```powershell
# Elencare backup disponibili
wbadmin get versions

# Elencare backup su target specifico
wbadmin get versions -backupTarget:E:
wbadmin get versions -backupTarget:\\BACKUP-SRV\Backups

# Restore singoli file/cartelle
wbadmin start recovery -version:05/20/2026-21:00 `
    -itemType:File `
    -items:"D:\Shares\Contabilita\Report.xlsx" `
    -recoveryTarget:"D:\Restored" `
    -backupTarget:E: -quiet

# Restore intero volume
wbadmin start recovery -version:05/20/2026-21:00 `
    -itemType:Volume `
    -items:D: `
    -recoveryTarget:D: `
    -backupTarget:E: -quiet

# Restore applicazione (Exchange, SQL, Hyper-V)
wbadmin start recovery -version:05/20/2026-21:00 `
    -itemType:App `
    -items:Exchange `
    -backupTarget:E: -quiet
```

### Schedule Backup

```powershell
# Configurare backup schedulato
$policy = New-WBPolicy

# Volumi
$volume = Get-WBVolume -AllVolumes | Where-Object MountPath -eq "C:"
Add-WBVolume -Policy $policy -Volume $volume

# System State
Add-WBSystemState -Policy $policy

# Bare Metal Recovery (include tutto il necessario per BMR)
Add-WBBareMetalRecovery -Policy $policy

# Target
$target = New-WBBackupTarget -VolumePath "E:"
Add-WBBackupTarget -Policy $policy -Target $target

# Schedule (09:00 e 21:00 ogni giorno)
Set-WBSchedule -Policy $policy -Schedule 09:00, 21:00

# VSS
Set-WBVssBackupOption -Policy $policy -VssFullBackup

# Applicare
Set-WBPolicy -Policy $policy -Force

# Verificare policy
Get-WBPolicy
Get-WBSummary
Get-WBJob -Previous 5 | Select-Object StartTime, EndTime, JobState, DetailedMessage
```

### Limiti di Windows Server Backup

```
- Non supporta backup su tape.
- Un solo schedule per server (non job multipli).
- Retention limitata: i backup vecchi vengono sovrascritti automaticamente.
- Non supporta deduplication nativa nel backup.
- Non supporta catalogo centralizzato (ogni server gestisce i propri backup).
- Per ambienti enterprise: considerare Veeam, DPM, o Azure Backup.
```

---

## Volume Shadow Copy (VSS)

### Architettura VSS

```
VSS è un framework di servizi Windows che coordina la creazione di
snapshot consistenti (shadow copy) di volumi.

COMPONENTI:

1. VSS Requestor (chi chiede la shadow copy)
   - Windows Server Backup (wbadmin)
   - Veeam Agent
   - System Center DPM
   - Qualsiasi applicazione che usa l'API VSS

2. VSS Provider (chi crea la shadow copy)
   - System Provider (built-in, copy-on-write su stesso volume)
   - Hardware Provider (SAN/NAS con snapshot hardware)
   - Software Provider (terze parti, es. Veeam)
   
   Il System Provider usa il meccanismo copy-on-write:
   quando un blocco viene modificato, il blocco originale viene copiato
   nell'area di storage delle shadow copy PRIMA della modifica.

3. VSS Writer (chi garantisce la consistenza applicativa)
   - Ogni applicazione può registrare un VSS Writer
   - Il writer mette l'applicazione in stato "quiescent" durante la snapshot
   - Esempi: SQL Server VSS Writer, Exchange Writer, 
     Hyper-V VSS Writer, DHCP Writer, Registry Writer

FLUSSO DI UNA SHADOW COPY:

    Requestor → chiede snapshot
    VSS Service → notifica tutti i Writer: "PrepareForSnapshot"
    Writer → flush cache, freeze I/O
    VSS Service → chiede al Provider: "CreateSnapshot"
    Provider → crea snapshot copy-on-write
    VSS Service → notifica Writer: "PostSnapshot" (thaw)
    Writer → riprende I/O normale
    
    Tutto il processo dura tipicamente < 60 secondi.
    L'applicazione è "freezata" solo per pochi secondi.
```

### VSS Writers — Diagnostica

```powershell
# Elencare tutti i VSS writer e il loro stato
vssadmin list writers

# Output tipico:
# Writer name: 'SqlServerWriter'
#    Writer Id: {a65faa63-5ea8-4ebc-9dbd-a0c4db26912a}
#    Writer Instance Id: {5d159b2e-...}
#    State: [1] Stable          ← OK
#    Last error: No error

# Stati possibili:
# [1] Stable           → OK, pronto
# [2] Waiting          → In attesa (transizione, controllare dopo qualche secondo)
# [5] Failed           → ERRORE: writer crashato, riavviare il servizio
# [6] Unknown          → Non raggiungibile
# [7] Waiting for completion → Bloccato (controllare l'applicazione)

# Se un writer è in stato Failed:
# 1. Identificare il servizio Windows associato
# 2. Riavviare il servizio:
Restart-Service VSS
Restart-Service MSSQLSERVER     # Per SQL Writer
Restart-Service MSExchangeIS    # Per Exchange Writer

# 3. Verificare di nuovo
vssadmin list writers | Select-String -Pattern "State:"
```

### VSS Providers

```powershell
# Elencare provider installati
vssadmin list providers

# Output tipico:
# Provider name: 'Microsoft Software Shadow Copy provider 1.0'
#    Provider type: System
#    Provider Id: {b5946137-7b9f-4925-af80-51abd60b20d5}

# Provider hardware (SAN):
# Se il SAN ha un VSS Hardware Provider installato,
# le snapshot vengono delegate al SAN → zero impatto sul server.
# Verificare con il vendor SAN (NetApp, Dell EMC, HPE, Pure Storage).
```

### Gestione Shadow Copy

```powershell
# VSS crea snapshot point-in-time di volumi
# Permette agli utenti di recuperare file autonomamente ("Previous Versions")

# Abilitare shadow copy
vssadmin add shadowstorage /for=D: /on=D: /maxsize=20%

# Creare snapshot manuale
vssadmin create shadow /for=D:

# Elencare snapshot
vssadmin list shadows /for=D:
Get-WmiObject Win32_ShadowCopy | Select-Object DeviceObject, InstallDate

# Schedulare snapshot automatici (via Task Scheduler)
# Tipicamente: 2 volte al giorno (07:00 e 12:00)
schtasks /create /tn "VSS-D-Morning" /tr "vssadmin create shadow /for=D:" ^
    /sc daily /st 07:00 /ru SYSTEM
schtasks /create /tn "VSS-D-Noon" /tr "vssadmin create shadow /for=D:" ^
    /sc daily /st 12:00 /ru SYSTEM

# Eliminare shadow copy vecchie
vssadmin delete shadows /for=D: /oldest /quiet

# Eliminare tutte
vssadmin delete shadows /for=D: /all /quiet

# Utilizzo da utente:
# Tasto destro sulla cartella → Properties → Previous Versions
# Selezionare la versione e "Restore" o "Open"

# ATTENZIONE: shadow copy NON è un backup!
# - Risiedono sullo stesso volume (se il disco muore, si perde tutto)
# - Non protegge da ransomware (il malware cancella le shadow copy)
# - Usare come complemento, non sostituto del backup
```

### VSS — Gestione avanzata con PowerShell

```powershell
# Shadow copy via WMI/CIM
$shadow = (Get-WmiObject -List Win32_ShadowCopy).Create("D:\", "ClientAccessible")

# Montare una shadow copy come cartella
$sc = Get-WmiObject Win32_ShadowCopy | Sort-Object InstallDate -Descending | Select-Object -First 1
$link = "C:\ShadowMount\"
cmd /c mklink /d $link "$($sc.DeviceObject)\"

# Accedere ai file nella shadow copy montata
Get-ChildItem "C:\ShadowMount\Shares\Contabilita"

# Rimuovere il link simbolico dopo l'uso
cmd /c rmdir "C:\ShadowMount"

# Configurare dimensione massima per volume
vssadmin resize shadowstorage /for=D: /on=D: /maxsize=50GB

# Elencare spazio utilizzato
vssadmin list shadowstorage
```

---

## System State Backup

```powershell
# System State include:
# - Registry
# - COM+ class registration database
# - Boot files
# - Active Directory database (NTDS.DIT) — solo sui DC
# - SYSVOL — solo sui DC
# - Certificate Services database — solo sui CA server
# - Cluster database — solo sui nodi cluster

# Backup
wbadmin start systemstatebackup -backupTarget:E: -quiet

# Elencare backup disponibili
wbadmin get versions -backupTarget:E:

# Ripristino System State (NON-AUTHORITATIVE)
# Il DC riceve le modifiche dagli altri DC via replica dopo il restore
wbadmin start systemstaterecovery -version:MM/DD/YYYY-HH:MM -backupTarget:E: -quiet

# Per restore: il server deve essere in DSRM (Directory Services Restore Mode)
# Boot → F8 → DSRM → login con password DSRM

# AUTHORITATIVE restore (vedi sezione AD Recovery)
# Per ripristinare un oggetto specifico e impedire che la replica lo sovrascriva
```

### Best practices System State

```
- Eseguire backup System State QUOTIDIANO su ogni Domain Controller.
- Retention minima: 60 giorni (coprire il tombstone lifetime di AD, default 180 giorni).
- Conservare i backup su volume diverso dal sistema operativo.
- Verificare che la dimensione del backup non cresca in modo anomalo
  (può indicare corruzione del database AD o file di log fuori controllo).
- Documentare la password DSRM in un luogo sicuro (password manager, cassaforte).
- Testare il restore System State almeno trimestralmente in ambiente isolato.
```

---

## SQL Server Backup

### Tipi di backup SQL Server

```
FULL BACKUP
    Copia l'intero database, incluso il transaction log sufficiente
    per il recovery durante il restore.
    → Base per tutti gli altri tipi di backup.

DIFFERENTIAL BACKUP
    Copia solo le extent (gruppi di 8 pagine da 64KB) modificate
    dall'ultimo full backup.
    → Crescono durante la settimana, reset al prossimo full.

TRANSACTION LOG BACKUP
    Copia il transaction log e lo tronca (libera spazio nel log).
    → Permette Point-in-Time Recovery (PITR).
    → Disponibile solo in FULL o BULK_LOGGED recovery model.

COPY-ONLY BACKUP
    Full backup che non interrompe la catena di log backup.
    → Usare per backup ad-hoc senza impattare la strategia.

TAIL-LOG BACKUP
    Ultimo log backup prima di un restore, per catturare
    le transazioni dopo l'ultimo log backup schedulato.
    → Critico per minimizzare la perdita di dati.
```

### Comandi T-SQL

```sql
-- Full backup
BACKUP DATABASE [Contabilita]
TO DISK = N'E:\SQLBackups\Contabilita_Full.bak'
WITH COMPRESSION, CHECKSUM, INIT,
     NAME = N'Contabilita-Full',
     STATS = 10;

-- Differential backup
BACKUP DATABASE [Contabilita]
TO DISK = N'E:\SQLBackups\Contabilita_Diff.bak'
WITH DIFFERENTIAL, COMPRESSION, CHECKSUM, INIT,
     NAME = N'Contabilita-Diff',
     STATS = 10;

-- Transaction log backup
BACKUP LOG [Contabilita]
TO DISK = N'E:\SQLBackups\Contabilita_Log.trn'
WITH COMPRESSION, CHECKSUM, INIT,
     NAME = N'Contabilita-Log',
     STATS = 10;

-- Copy-only backup (non interrompe la chain)
BACKUP DATABASE [Contabilita]
TO DISK = N'E:\SQLBackups\Contabilita_CopyOnly.bak'
WITH COPY_ONLY, COMPRESSION, CHECKSUM;

-- Backup su URL (Azure Blob Storage)
BACKUP DATABASE [Contabilita]
TO URL = N'https://storageaccount.blob.core.windows.net/sqlbackups/Contabilita.bak'
WITH CREDENTIAL = N'AzureStorageCredential',
     COMPRESSION, CHECKSUM, STATS = 10;

-- Tail-log backup (prima di un restore)
BACKUP LOG [Contabilita]
TO DISK = N'E:\SQLBackups\Contabilita_TailLog.trn'
WITH NORECOVERY, NO_TRUNCATE;
```

### Restore SQL Server

```sql
-- Restore completo: Full + Diff + Log chain
-- 1. Restore full con NORECOVERY (non rende il DB disponibile)
RESTORE DATABASE [Contabilita]
FROM DISK = N'E:\SQLBackups\Contabilita_Full.bak'
WITH NORECOVERY, REPLACE, STATS = 10;

-- 2. Restore differential con NORECOVERY
RESTORE DATABASE [Contabilita]
FROM DISK = N'E:\SQLBackups\Contabilita_Diff.bak'
WITH NORECOVERY, STATS = 10;

-- 3. Restore transaction log con RECOVERY (ultimo della catena)
RESTORE LOG [Contabilita]
FROM DISK = N'E:\SQLBackups\Contabilita_Log.trn'
WITH RECOVERY, STATS = 10;

-- Point-in-Time Recovery (PITR)
-- Restore fino a un momento specifico
RESTORE LOG [Contabilita]
FROM DISK = N'E:\SQLBackups\Contabilita_Log.trn'
WITH RECOVERY, STOPAT = '2026-05-22T14:30:00';

-- Verificare integrità del backup senza restore
RESTORE VERIFYONLY
FROM DISK = N'E:\SQLBackups\Contabilita_Full.bak'
WITH CHECKSUM;

-- Leggere informazioni dal file di backup
RESTORE HEADERONLY FROM DISK = N'E:\SQLBackups\Contabilita_Full.bak';
RESTORE FILELISTONLY FROM DISK = N'E:\SQLBackups\Contabilita_Full.bak';
```

### SQL Server — Maintenance Plan

```sql
-- Maintenance Plan via T-SQL / SQL Agent Job
-- Schedule consigliato per database transazionale:

-- Full backup: domenica ore 02:00
-- Differential: lunedì-sabato ore 02:00
-- Log backup: ogni 15 minuti (RPO ≤ 15 min)
-- Integrity check (DBCC CHECKDB): sabato ore 22:00

-- Configurare compressione backup a livello server
EXEC sp_configure 'backup compression default', 1;
RECONFIGURE;

-- Controllare ultimo backup per ogni database
SELECT
    d.name AS DatabaseName,
    MAX(CASE WHEN b.type = 'D' THEN b.backup_finish_date END) AS LastFullBackup,
    MAX(CASE WHEN b.type = 'I' THEN b.backup_finish_date END) AS LastDiffBackup,
    MAX(CASE WHEN b.type = 'L' THEN b.backup_finish_date END) AS LastLogBackup
FROM sys.databases d
LEFT JOIN msdb.dbo.backupset b ON d.name = b.database_name
WHERE d.database_id > 4  -- escludi system DB
GROUP BY d.name
ORDER BY LastFullBackup;
```

---

## Exchange e Microsoft 365 Backup

### Exchange Server On-Premises

```
ARCHITETTURA EXCHANGE BACKUP:

1. Database Availability Group (DAG)
   - Replica sincrona/asincrona dei database tra più server
   - NON è un backup (protegge da guasto hardware, non da corruzione logica)
   - Configurazione tipica: 4 copie del database su 4 server

2. Backup con Windows Server Backup
   - Exchange ha un VSS Writer dedicato (Microsoft Exchange Writer)
   - Supporta backup online (senza smontare il database)
   - Il backup tronca i transaction log

3. Backup con strumenti enterprise (Veeam, DPM, Commvault)
   - Application-aware: usano il VSS Writer di Exchange
   - Supportano granular recovery (singola mailbox, singolo item)
   - Veeam Explorer for Exchange: restore granulare senza restore completo
```

```powershell
# Backup Exchange con Windows Server Backup
# Prerequisito: Exchange installato, WSB feature abilitata

# Backup del volume che contiene i database Exchange
wbadmin start backup -backupTarget:F: -include:E: -vssFull -quiet

# Dopo il backup, verificare che i log siano stati troncati
Get-MailboxDatabase | Select-Object Name, DatabaseSize, AvailableNewMailboxSpace

# Verificare lo stato del DAG
Get-MailboxDatabaseCopyStatus * | Format-Table Name, Status, CopyQueueLength, ReplayQueueLength

# Restore singola mailbox (richiede Recovery Database)
# 1. Restore del backup su un volume alternativo
# 2. Montare come Recovery Database
New-MailboxRestoreRequest -SourceDatabase "RecoveryDB" `
    -SourceStoreMailbox "Mario Rossi" `
    -TargetMailbox "Mario.Rossi" `
    -TargetRootFolder "Recovered"
```

### Microsoft 365 Backup

```
ATTENZIONE CRITICA: Microsoft 365 NON include backup completo dei dati.

Cosa Microsoft protegge:
    - Disponibilità dell'infrastruttura (SLA 99.9%)
    - Replica geografica per disaster recovery
    - Protezione contro guasti hardware Microsoft

Cosa Microsoft NON protegge:
    - Cancellazione accidentale da parte degli utenti
    - Cancellazione malevola (insider threat, account compromesso)
    - Ransomware che cripta i file OneDrive/SharePoint
    - Requisiti di retention compliance (GDPR, legal hold)
    - Migrazione dati fuori da Microsoft 365

RETENTION NATIVA M365:
    Email (Exchange Online):
        - Deleted Items: 30 giorni
        - Recoverable Items: 14 giorni (estendibile a 30)
        - Litigation Hold: infinito ma richiede licenza E3+
    
    OneDrive:
        - Versioning: 500 versioni per file
        - Recycle Bin: 93 giorni
        - Account utente eliminato: 30 giorni poi cancellato
    
    SharePoint:
        - Versioning: configurabile
        - Recycle Bin primo livello: 93 giorni
        - Recycle Bin secondo livello: fino a 93 giorni (quota)
    
    Teams:
        - Chat: conservata in Exchange Online (mailbox utente)
        - File: conservati in SharePoint/OneDrive

SOLUZIONI DI BACKUP TERZE PARTI PER M365:
    - Veeam Backup for Microsoft 365
    - Commvault for Microsoft 365
    - Barracuda Cloud-to-Cloud Backup
    - AvePoint Cloud Backup
    - Acronis Cyber Protect Cloud
    
    Funzionalità comuni:
    - Backup automatico Exchange Online, OneDrive, SharePoint, Teams
    - Granular recovery (singola email, singolo file, singolo team)
    - Ricerca cross-mailbox per eDiscovery
    - Storage su Azure Blob, AWS S3, o storage locale
    - Encryption at rest e in transit
```

---

## Hyper-V Backup

### Backup a livello VM vs Guest-Level

```
VM-LEVEL BACKUP (Host-Level)
    Backup della VM dall'hypervisor, senza agente nella VM.
    
    Vantaggi:
    - Nessun software da installare nelle VM
    - Backup dell'intera VM (disco, config, checkpoint)
    - Application-aware tramite VSS Integration Services
    - Restore rapido: instant VM recovery
    
    Requisiti:
    - Hyper-V Integration Services installati nella VM
    - VSS richiede Integration Services per consistency
    - Windows VM: full application-aware backup
    - Linux VM: file-system consistent (no application-aware)

GUEST-LEVEL BACKUP (Agent-Based)
    Agente di backup installato dentro la VM.
    
    Vantaggi:
    - Granularità maggiore (singoli file, database)
    - Application-aware completo (SQL, Exchange, AD)
    - Indipendente dall'hypervisor
    
    Svantaggi:
    - Agente da installare e mantenere in ogni VM
    - Consumo risorse nella VM
    - Non cattura la configurazione VM

RACCOMANDAZIONE:
    Usare VM-level backup come base (intera VM).
    Aggiungere guest-level per applicazioni critiche
    che richiedono restore granulare (SQL PITR, Exchange item-level).
```

### Checkpoint Hyper-V

```powershell
# STANDARD CHECKPOINT (ex "Snapshot")
# Cattura stato completo: disco + memoria + configurazione
# Il file .avhdx contiene i delta dal checkpoint
# ATTENZIONE: NON per uso in produzione! Solo dev/test.
# Motivo: include stato della memoria → applicazioni possono
# non essere consistenti al restore (es. connessioni DB scadute)

# Creare checkpoint standard
Checkpoint-VM -Name "WebServer01" -SnapshotName "Pre-Aggiornamento"

# PRODUCTION CHECKPOINT (Windows Server 2016+)
# Usa VSS dentro la VM → backup application-consistent
# NON include stato memoria → le applicazioni ripartono pulite
# Sicuro per la produzione

# Configurare la VM per production checkpoint (default su 2016+)
Set-VM -Name "WebServer01" -CheckpointType Production

# Verificare il tipo di checkpoint configurato
Get-VM -Name "WebServer01" | Select-Object Name, CheckpointType

# Creare production checkpoint
Checkpoint-VM -Name "WebServer01" -SnapshotName "Pre-Patch-2026-05-22"

# Elencare checkpoint
Get-VMCheckpoint -VMName "WebServer01"

# Ripristinare un checkpoint
Restore-VMCheckpoint -VMName "WebServer01" -Name "Pre-Patch-2026-05-22" -Confirm:$false

# Eliminare un checkpoint (il .avhdx viene mergiato nel .vhdx)
Remove-VMCheckpoint -VMName "WebServer01" -Name "Pre-Patch-2026-05-22"

# Eliminare TUTTI i checkpoint di una VM
Get-VMCheckpoint -VMName "WebServer01" | Remove-VMCheckpoint

# ATTENZIONE: la rimozione del checkpoint NON è un rollback!
# Rimuovere un checkpoint merge le modifiche nel disco base.
# Per fare rollback: usare Restore-VMCheckpoint PRIMA di rimuovere.
```

### Checkpoint vs Backup — Differenze Operative

```
I checkpoint Hyper-V e i backup sono strumenti complementari ma con
scopi, garanzie e limiti molto diversi. Confonderli è uno degli errori
più frequenti in ambienti virtualizzati.

CONFRONTO DIRETTO:

| Criterio                  | Checkpoint                        | Backup (WSB/Veeam/DPM)           |
|---------------------------|-----------------------------------|-----------------------------------|
| Dove risiedono i dati     | Stesso storage della VM (.avhdx)  | Storage separato (repo, vault)    |
| Protezione da guasto disco| NO — se il disco muore, checkpoint | SI — copia indipendente          |
|                           | e VM si perdono insieme           |                                   |
| Portabilità               | NO — dipendono dal disco padre    | SI — restore su qualsiasi host   |
| Consistenza applicativa   | Production: VSS-consistent        | Application-aware con VSS writer |
|                           | Standard: crash-consistent + RAM  |                                   |
| Impatto sulle performance | Crescente nel tempo: ogni I/O     | Impatto solo durante il backup   |
|                           | attraversa la catena di .avhdx    | (freeze VSS breve)               |
| Merge alla rimozione      | Può richiedere ore su .avhdx grandi| Non applicabile                  |
|                           | + rischio corruzione se interrotto|                                   |
| Retention a lungo termine | NO — degradano le prestazioni     | SI — retention GFS multi-anno    |
| Protezione da ransomware  | NO — accessibili dall'host        | SI — con immutabilità/air-gap    |

LIMITAZIONI CRITICHE DEI CHECKPOINT:

    1. Active Directory: MAI usare checkpoint su Domain Controller
       in produzione. Il rollback di un checkpoint causa USN rollback:
       il DC crede di essere a un punto precedente nel tempo e
       la replica AD si rompe irrecuperabilmente.

    2. Cluster: MAI su nodi cluster attivi. Il rollback può causare
       split-brain o inconsistenza del quorum.

    3. Catena lunga: ogni checkpoint aggiunge un .avhdx alla catena.
       Più la catena è lunga, più le prestazioni I/O degradano
       (ogni lettura deve risalire la catena fino al .vhdx base).

    4. Spazio disco: i .avhdx crescono ad ogni scrittura nella VM.
       Se lo storage si riempie, la VM si mette in pausa critica.

    5. Merge: alla rimozione di un checkpoint, il contenuto del .avhdx
       viene consolidato nel disco padre. Su dischi grandi questo
       processo genera I/O elevato e, se interrotto (crash dell'host,
       mancanza di corrente), può corrompere il disco della VM.

QUANDO USARE I CHECKPOINT:
    - Prima di applicare patch o aggiornamenti su VM non-DC/non-cluster
    - Prima di modifiche di configurazione rischiose
    - In ambienti dev/test per test rapidi
    - Come rollback immediato (minuti) per problemi appena introdotti

QUANDO USARE I BACKUP:
    - Protezione dei dati a lungo termine
    - Disaster recovery (hardware failure, ransomware)
    - Compliance e retention
    - Recovery di singoli file o oggetti applicativi (mailbox, DB)
    - Qualsiasi scenario che richieda portabilità o isolamento dei dati
```

### Backup Hyper-V con Windows Server Backup

```powershell
# WSB supporta backup Hyper-V application-aware
# Requisiti: Hyper-V Integration Services attivi nella VM

# Backup di tutte le VM sul volume Hyper-V
wbadmin start backup -backupTarget:F: -hyperv:WebServer01,SQLServer01 -vssFull -quiet

# Con PowerShell
$policy = New-WBPolicy
$hyperv = New-WBHyperVComponent
$hyperv | Add-WBHyperVComponent -VM (Get-WBVirtualMachine | Where-Object VMName -eq "WebServer01")
Add-WBHyperVComponent -Policy $policy -Component $hyperv
$target = New-WBBackupTarget -VolumePath "F:"
Add-WBBackupTarget -Policy $policy -Target $target
Set-WBVssBackupOption -Policy $policy -VssFullBackup
Start-WBBackup -Policy $policy
```

---

## Azure Backup

### Architettura Azure Backup

```
COMPONENTI PRINCIPALI:

1. Recovery Services Vault
   - Container Azure che conserva i backup
   - Geo-redundant (GRS) o locally redundant (LRS)
   - Encryption at rest con chiavi Microsoft o customer-managed
   - Soft delete: 14 giorni di protezione da cancellazione accidentale

2. MARS Agent (Microsoft Azure Recovery Services)
   - Agente installato su server Windows on-premises o Azure VM
   - Backup di file e cartelle verso il Recovery Services Vault
   - System State backup verso Azure
   - NON supporta backup bare metal (usare Azure Backup Server per quello)
   - Compressione e encryption prima dell'upload

3. Azure Backup Server (MABS)
   - Versione di DPM per Azure, senza licenza System Center
   - Backup application-aware: SQL, Exchange, SharePoint, Hyper-V
   - Backup su disco locale + tiering automatico verso Azure
   - Supporta bare metal recovery

4. Azure VM Backup (nativo)
   - Backup a livello VM dall'infrastruttura Azure
   - Snapshot + trasferimento al vault
   - Application-consistent tramite VSS (Windows) o script pre/post (Linux)
   - Restore: intera VM, singoli dischi, singoli file
```

### MARS Agent — Configurazione

```powershell
# 1. Scaricare il MARS Agent dal Recovery Services Vault
#    Azure Portal → Recovery Services Vault → Getting Started → Backup
#    → Goal: On-premises, Files and folders → Download Agent

# 2. Installare il MARS Agent sul server
# MARSAgentInstaller.exe /q

# 3. Registrare il server con il vault
# Scaricare le credenziali del vault dal portale Azure
# Start-OBRegistration -VaultCredentials "C:\vault_credentials.publishsettings"

# 4. Configurare backup con PowerShell
# Configurare la policy di backup
$policy = New-OBPolicy

# Schedule: backup giornaliero alle 22:00
$schedule = New-OBSchedule -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday `
    -TimesOfDay 22:00
Set-OBSchedule -Policy $policy -Schedule $schedule

# Retention: 30 giorni giornaliero, 12 settimane settimanale, 12 mesi mensile
$retention = New-OBRetentionPolicy -RetentionDays 30 `
    -RetentionWeeklyPolicy -RetentionWeeks 12 `
    -RetentionMonthlyPolicy -RetentionMonths 12 `
    -RetentionYearlyPolicy -RetentionYears 7
Set-OBRetentionPolicy -Policy $policy -RetentionPolicy $retention

# File/cartelle da proteggere
$filespec = New-OBFileSpec -FileSpec @("D:\Shares", "D:\Data")
Add-OBFileSpec -Policy $policy -FileSpec $filespec

# Esclusioni
$exclude = New-OBFileSpec -FileSpec @("D:\Shares\Temp", "*.tmp", "*.log") -Exclude
Add-OBFileSpec -Policy $policy -FileSpec $exclude

# Encryption passphrase (CONSERVARE IN LUOGO SICURO!)
$passphrase = ConvertTo-SecureString "ComplexP@ssPhrase!2026" -AsPlainText -Force
Set-OBMachineSetting -EncryptionPassphrase $passphrase

# Applicare la policy
Set-OBPolicy -Policy $policy

# Avviare backup manuale
Start-OBBackup

# Monitorare lo stato
Get-OBJob | Format-Table JobType, Status, StartTime, EndTime
```

### MARS Agent — Gestione Operativa

```powershell
# === BANDWIDTH THROTTLING ===
# Limitare la banda usata dal MARS Agent durante l'orario lavorativo
# per non saturare la connessione di produzione.

# Abilitare throttling
Set-OBMachineSetting -ThrottleBandwidthBeginHour 8 `
    -ThrottleBandwidthEndHour 18 `
    -WorkHourBandwidth 512000 `
    -NonWorkHourBandwidth 0       # 0 = nessun limite fuori orario

# Verificare la configurazione attuale
Get-OBMachineSetting | Select-Object ThrottleBandwidthBeginHour, 
    ThrottleBandwidthEndHour, WorkHourBandwidth, NonWorkHourBandwidth

# === CONFIGURAZIONE PROXY ===
# Se il server accede ad Azure tramite proxy HTTP
Set-OBMachineSetting -ProxyServer "http://proxy.corp.contoso.com" `
    -ProxyPort 8080 `
    -ProxyUsername "CORP\svc-backup" `
    -ProxyPassword (ConvertTo-SecureString "P@ss" -AsPlainText -Force)

# Rimuovere configurazione proxy (accesso diretto)
Set-OBMachineSetting -NoProxy

# === ROTAZIONE PASSPHRASE DI ENCRYPTION ===
# CRITICO: cambiare la passphrase NON re-cripta i backup esistenti.
# I backup fatti con la vecchia passphrase richiedono la vecchia per il restore.
# Documentare ENTRAMBE le passphrase (vecchia e nuova) fino alla scadenza
# dell'ultimo backup criptato con la vecchia.

$newPassphrase = ConvertTo-SecureString "NuovaP@ssPhrase!2026" -AsPlainText -Force
Set-OBMachineSetting -EncryptionPassphrase $newPassphrase

# Verificare che la passphrase sia impostata
Get-OBMachineSetting | Select-Object EncryptionPassphraseSet

# === AGGIORNAMENTO AGENT ===
# Verificare versione corrente
Get-OBMachineSetting | Select-Object -ExpandProperty CBBVersion

# Scaricare l'ultima versione dal vault:
# Azure Portal → Recovery Services Vault → Properties → MARS Agent Update
# Installare con: MARSAgentInstaller.exe /q /nu (silent, no auto-update)
# L'aggiornamento preserva la registrazione e le policy esistenti.

# === MONITORAGGIO E DIAGNOSTICA ===
# Stato dell'ultimo job
Get-OBJob -Previous 5 | Format-Table JobType, Status, StartTime, EndTime, JobStatus

# Verificare dimensione dei dati protetti
Get-OBPolicy | Select-Object -ExpandProperty FileSpecs

# Log MARS Agent: %ProgramData%\Microsoft\Microsoft Azure Recovery Services Agent\Temp\
# File chiave: CBEngineCurr.errlog (errori correnti)
#              ScratchSpace (dati temporanei durante backup/restore)

# === ANNULLAMENTO REGISTRAZIONE SERVER ===
# Per rimuovere un server dal vault (decommissioning, migrazione)
# Azure Portal → Recovery Services Vault → Backup Infrastructure
# → Protected Servers → select server → Delete
# Poi sul server locale:
Start-OBRegistration -VaultCredentials "NUOVE_credenziali.publishsettings"
# Oppure disinstallare l'agent se il server viene decommissionato.

# === LIMITI OPERATIVI MARS AGENT ===
# - Max 1700 GB di dati per server (per policy)
# - Max 9 backup al giorno (schedule massimo: ogni 2 ore, max 3 per slot)
# - NON supporta bare metal recovery (solo file, cartelle, System State)
# - NON supporta backup di applicazioni (SQL, Exchange) → usare MABS per quello
# - Richiede .NET Framework 4.7.2+ e TLS 1.2
# - Supporta Windows Server 2016, 2019, 2022, 2025
```

### Azure VM Backup

```powershell
# Prerequisiti: Recovery Services Vault nella stessa region della VM

# Abilitare backup su una VM Azure (via Az PowerShell)
$vault = Get-AzRecoveryServicesVault -Name "MyVault" -ResourceGroupName "RG-Backup"
Set-AzRecoveryServicesVaultContext -Vault $vault

# Configurare policy
$policy = Get-AzRecoveryServicesBackupProtectionPolicy -Name "DefaultPolicy"

# Abilitare protezione sulla VM
$vm = Get-AzVM -ResourceGroupName "RG-Production" -Name "WebServer01"
Enable-AzRecoveryServicesBackupProtection -ResourceGroupName "RG-Production" `
    -Name "WebServer01" -Policy $policy

# Avviare backup on-demand
$container = Get-AzRecoveryServicesBackupContainer -ContainerType AzureVM `
    -FriendlyName "WebServer01"
$item = Get-AzRecoveryServicesBackupItem -Container $container -WorkloadType AzureVM
Backup-AzRecoveryServicesBackupItem -Item $item

# Monitorare
Get-AzRecoveryServicesBackupJob -Status InProgress

# Restore VM: intera VM o singoli dischi
$rp = Get-AzRecoveryServicesBackupRecoveryPoint -Item $item -StartDate (Get-Date).AddDays(-7)
$rp | Format-Table RecoveryPointTime, RecoveryPointType

# Restore come nuova VM
$restoreConfig = New-AzRecoveryServicesBackupRestoreConfig -RecoveryPoint $rp[0] `
    -TargetResourceGroupName "RG-Restored" -StorageAccountName "restoresa" `
    -StorageAccountResourceGroupName "RG-Backup" -RestoreAsNewVM
Restore-AzRecoveryServicesBackupItem -RecoveryPoint $rp[0] -RestoreConfig $restoreConfig

# File recovery: montare i dischi del recovery point come volumi locali
# Azure Portal → Recovery Services Vault → Backup Items → File Recovery
# Scaricare lo script → eseguirlo → i volumi vengono montati → copiare i file
```

### Azure Backup per SQL Server in Azure VM

```powershell
# Azure Backup supporta backup nativo SQL Server nelle Azure VM
# Backup stream-based: non passa per snapshot VM

# Abilitare auto-protection su un'istanza SQL
$vault = Get-AzRecoveryServicesVault -Name "MyVault"
Set-AzRecoveryServicesVaultContext -Vault $vault

# Registrare la VM SQL
Register-AzRecoveryServicesBackupContainer -ResourceId $vm.Id `
    -BackupManagementType AzureWorkload -WorkloadType MSSQL

# Configurare backup per tutti i database (auto-protection)
# Azure Portal → Recovery Services Vault → Backup → Workload: SQL in Azure VM
# → Auto-protect l'istanza SQL → i nuovi database vengono protetti automaticamente

# Restore: Full, Differential, Log (PITR fino al secondo)
# Point-in-Time: selezionare data/ora esatta nel portale
```

---

## Veeam Backup & Replication

### Architettura Veeam

```
COMPONENTI:

1. Veeam Backup Server
   - Console di gestione, scheduling, catalogo
   - Database di configurazione (SQL Server o PostgreSQL)
   - Non processa i dati di backup direttamente

2. Veeam Proxy
   - Elabora i dati: compressione, deduplication, encryption
   - Tipi:
     - VMware: Virtual Appliance (hot-add) o Network (NBD)
     - Hyper-V: On-Host o Off-Host proxy
   - Scalare i proxy per aumentare il throughput

3. Veeam Repository
   - Dove vengono conservati i backup
   - Tipi: Windows Server, Linux Server (hardened!), 
     dedup appliance (HPE StoreOnce, Dell Data Domain),
     object storage (S3, Azure Blob, Google Cloud)
   - Linux Hardened Repository: immutabilità a livello file system
     → protezione ransomware (non cancellabile nemmeno da root)

4. Scale-Out Backup Repository (SOBR)
   - Pool di repository con tiering automatico
   - Performance Tier: storage veloce (disco locale, SAN)
   - Capacity Tier: object storage (S3, Azure Blob) per dati vecchi
   - Archive Tier: storage freddo (Glacier, Azure Archive)

5. WAN Accelerator
   - Ottimizza il traffico per backup/replica offsite
   - Deduplication globale, cache locale

6. Enterprise Manager
   - Console web per gestione multi-server Veeam
   - Self-service restore portal per gli utenti
   - REST API per automazione
```

### Backup Job Veeam

```powershell
# Prerequisito: Veeam B&R installato, infrastructure aggiunta

# Aggiungere server Hyper-V (o VMware vCenter)
Add-VBRServer -Name "HyperV01.corp.contoso.com" -Type HvServer `
    -Credential (Get-Credential)

# Creare un repository
Add-VBRBackupRepository -Name "Repo-Local" -Server "VEEAM-SRV" `
    -Folder "E:\VeeamBackups" -Type WinLocal

# Creare un backup job
$vm = Find-VBRHvEntity -Name "WebServer01"
$repo = Get-VBRBackupRepository -Name "Repo-Local"

Add-VBRHvBackupJob -Name "Job-WebServers" -Entity $vm `
    -BackupRepository $repo -Description "Backup web server di produzione"

# Configurare schedule
$job = Get-VBRJob -Name "Job-WebServers"
Set-VBRJobSchedule -Job $job -Daily -At "22:00" -DailyKind EveryDay
Enable-VBRJobSchedule -Job $job

# Configurare retention (14 punti di restore)
Set-VBRJobOptions -Job $job -Options @{
    RetainDays = 14
}

# Avviare backup manuale
Start-VBRJob -Job $job

# Monitorare lo stato del job
Get-VBRJob | Select-Object Name, @{N="LastRun";E={$_.FindLastSession().EndTime}},
    @{N="Result";E={$_.FindLastSession().Result}}

# Elencare i backup esistenti
Get-VBRBackup | Select-Object Name, CreationTime
```

### Restore Operations Veeam

```powershell
# Restore intera VM
$backup = Get-VBRBackup -Name "Job-WebServers"
$restorePoint = Get-VBRRestorePoint -Backup $backup -Name "WebServer01" |
    Sort-Object CreationTime -Descending | Select-Object -First 1

Start-VBRHvRestoreVM -RestorePoint $restorePoint -Server "HyperV01" `
    -Path "C:\ClusterStorage\Volume1" -VMName "WebServer01-Restored"

# Restore singoli file (FLR - File Level Recovery)
# Veeam monta il backup e permette di navigare i file
$session = Start-VBRWindowsFileRestore -RestorePoint $restorePoint
# Apre la finestra di browse dei file → copiare i file necessari
Stop-VBRWindowsFileRestore -Session $session

# Restore item-level per applicazioni
# Veeam Explorer per: Exchange, SharePoint, SQL, Active Directory, Oracle
# Esempio: Restore singola mailbox Exchange
# Start-VBRExchangeItemRestore → explorer interattivo

# Restore su cloud (Direct Restore to Azure / AWS)
# Restore un backup locale come VM in Azure
```

### Instant VM Recovery

```
Veeam Instant VM Recovery permette di avviare una VM direttamente
dal backup in pochi secondi, senza restore completo.

FUNZIONAMENTO:
1. Veeam monta il backup file (.vbk) via NFS sul server Hyper-V/ESXi
2. La VM parte direttamente dal backup file (read-only)
3. Le scritture vanno su un delta temporaneo (redirect-on-write)
4. La VM è operativa in 1-2 minuti (RTO aggressivo)
5. Storage vMotion / Live Migration sposta la VM su storage di produzione
6. Al termine, il delta viene mergiato → la VM è completamente migrata

CASI D'USO:
- Disaster recovery con RTO < 15 minuti
- Verifica rapida di un backup (il backup funziona? la VM parte?)
- Ambiente temporaneo per troubleshooting
```

```powershell
# Instant VM Recovery
$restorePoint = Get-VBRRestorePoint -Backup $backup -Name "SQLServer01" |
    Sort-Object CreationTime -Descending | Select-Object -First 1

Start-VBRInstantRecovery -RestorePoint $restorePoint `
    -Server "HyperV01" -VMName "SQLServer01-InstantRestore"

# Dopo aver verificato che la VM funziona, migrare su storage di produzione
# e finalizzare:
# Stop-VBRInstantRecovery -VM "SQLServer01-InstantRestore" -Migrate
```

### SureBackup

```
SureBackup verifica AUTOMATICAMENTE che i backup siano ripristinabili.

FUNZIONAMENTO:
1. Crea un ambiente isolato (Virtual Lab) con rete sandbox
2. Avvia le VM dal backup (come Instant VM Recovery)
3. Esegue test automatici su ogni VM:
   - Heartbeat (la VM risponde?)
   - Ping test (rete funziona?)
   - Application test (porta aperta? URL risponde?)
   - Script personalizzato (query SQL? test funzionale?)
4. Report: PASS / FAIL per ogni VM
5. Spegne tutto e pulisce l'ambiente isolato

CONFIGURAZIONE:
1. Virtual Lab: rete isolata con proxy per accesso esterno controllato
2. Application Group: le VM da testare, in ordine di avvio
   (es. prima DC, poi SQL, poi Exchange, poi Web)
3. SureBackup Job: schedule del test (es. ogni notte dopo il backup)
4. Verification script: test personalizzati per ogni applicazione

RISULTATO:
- Certezza che il backup è ripristinabile
- Non più "backup non testato = nessun backup"
- Report auditable per compliance
```

### Veeam Agent for Windows — Edizione Free e Workstation

```
Veeam Agent for Windows è un prodotto separato da Veeam Backup & Replication,
progettato per il backup di macchine fisiche (workstation e server).
Disponibile in più edizioni con funzionalità crescenti.

EDIZIONI A CONFRONTO:

| Funzionalità                     | Free          | Workstation   | Server         |
|----------------------------------|---------------|---------------|----------------|
| Backup su disco locale           | SI            | SI            | SI             |
| Backup su share di rete          | SI            | SI            | SI             |
| Backup su Veeam Repository       | NO            | SI            | SI             |
| Backup su cloud (S3, Azure Blob) | NO            | SI            | SI             |
| Gestione centralizzata (managed) | NO            | SI            | SI             |
| Application-aware processing     | NO            | NO            | SI             |
| Encryption del backup            | NO            | SI            | SI             |
| Transaction log backup (SQL)     | NO            | NO            | SI             |
| File-level restore               | SI            | SI            | SI             |
| Volume-level restore             | SI            | SI            | SI             |
| Bare metal recovery              | SI            | SI            | SI             |
| Instant recovery (boot da backup)| NO            | NO            | SI             |
| Supporto tecnico Veeam           | Community only| 24/7 produzione| 24/7 produzione|
| Uso commerciale                  | SI            | SI            | SI             |
| Costo                            | Gratuito      | Per socket    | Per socket     |

VERSIONE CORRENTE: 13.0 (aggiornamento marzo 2026)

INSTALLAZIONE E CONFIGURAZIONE FREE EDITION:

    1. Scaricare da veeam.com → Free Products → Veeam Agent for Windows
    2. Installare (richiede .NET Framework 4.7.2+)
    3. Al primo avvio, selezionare "Free" come licenza
    4. Creare un Recovery Media (USB bootable) per bare metal recovery:
       Menu → Create Recovery Media → selezionare USB o ISO
       IMPORTANTE: creare il recovery media PRIMA di un disastro,
       non durante! Il media include i driver specifici dell'hardware.

    5. Configurare il backup job:
       a. Tipo: Entire Computer (BMR) | Volume Level | File Level
       b. Destinazione: disco locale, USB esterno, share di rete
       c. Schedule: giornaliero, in orario di basso carico
       d. Retention: numero di punti di restore da conservare

    6. Il job esegue automaticamente alla schedule configurata
    7. Monitorare lo stato dalla system tray icon di Veeam

MODALITÀ STANDALONE vs MANAGED:
    Standalone (Free): il backup job è configurato localmente sulla macchina.
    Nessuna visibilità centralizzata. Adatto per singoli server isolati
    o workstation di utenti esperti.

    Managed (richiede licenza): il backup job viene definito e distribuito
    dal Veeam Backup & Replication server. L'admin gestisce centinaia
    di agent da una console unica. Policy uniformi, monitoraggio
    centralizzato, alert consolidati, report compliance.

QUANDO FARE UPGRADE DA FREE A PAID:
    - Servono backup criptati (compliance, dati sensibili)
    - Servono backup su cloud storage (tiering, offsite)
    - L'ambiente supera 5-10 macchine (gestione centralizzata critica)
    - Servono backup application-aware per SQL/Exchange/AD su fisici
    - Il supporto community non è sufficiente (SLA di recovery stringenti)

LIMITAZIONI FREE EDITION:
    - Un solo backup job per macchina
    - Nessun backup su Veeam Repository o cloud object storage
    - Nessuna encryption → i dati di backup sono in chiaro
    - Nessun application-aware → i backup di database sono crash-consistent
      (non transaction-consistent)
    - Nessuna gestione centralizzata → ogni macchina è autonoma
    - Nessun supporto ufficiale → solo forum community
```

---

## DPM — Data Protection Manager

### Panoramica DPM

```
System Center Data Protection Manager (DPM) è la soluzione enterprise
Microsoft per backup on-premises.

FUNZIONALITÀ:
- Backup application-aware: SQL, Exchange, SharePoint, Hyper-V
- Backup su disco, tape, e cloud (Azure Backup integration)
- Backup continuo per SQL e Exchange (ogni 15 minuti)
- Bare metal recovery
- Protection group: raggruppamento logico di risorse protette
- Self-service recovery per utenti (portale web)

ARCHITETTURA:
    DPM Server → disco locale (Storage Pool)
                → tape library (opzionale)
                → Azure Backup (tiering cloud)

    DPM Agent → installato su ogni server protetto
             → comunica con DPM Server
             → coordina VSS per consistency

REQUISITI:
- Windows Server con SQL Server dedicato (o co-hosted)
- Storage Pool: volumi dedicati per i backup
- Licenza System Center DPM o Azure Backup Server (MABS, gratuito)
```

### Installazione e configurazione DPM

```powershell
# 1. Prerequisiti
# - SQL Server installato (o installazione locale durante setup)
# - .NET Framework 4.8+
# - Windows Server 2019/2022

# 2. Aggiungere dischi allo Storage Pool
# DPM Console → Management → Disks → Add → selezionare dischi dedicati
# I dischi vengono formattati e gestiti da DPM (non usare per altro!)

# 3. Installare agenti DPM sui server da proteggere
# DPM Console → Management → Agents → Install
# Oppure manualmente:
# \\DPM-SERVER\DPMAgentInstall\DPMAgentInstaller_x64.exe /q

# 4. Creare un Protection Group
# DPM Console → Protection → New Protection Group
# Selezionare: tipo di dati (File, SQL, Exchange, Hyper-V, System State, BMR)
# Selezionare i server e le risorse da proteggere
# Configurare schedule e retention

# PowerShell equivalente:
$pg = New-DPMProtectionGroup -DPMServerName "DPM01" -Name "PG-FileServers"

# Aggiungere datasource
$agent = Get-DPMProductionServer -DPMServerName "DPM01" | 
    Where-Object MachineName -eq "FILESVR01"
$ds = Get-DPMDatasource -ProductionServer $agent -Inquire |
    Where-Object Name -eq "D:\"
Add-DPMChildDatasource -ProtectionGroup $pg -ChildDatasource $ds

# Configurare obiettivi di protezione
Set-DPMProtectionType -ProtectionGroup $pg -ShortTerm Disk -LongTerm Online

# Schedule: sincronizzazione ogni 4 ore, express full alle 20:00
Set-DPMPolicySchedule -ProtectionGroup $pg -Schedule (New-Object Microsoft.Internal.EnterpriseStorage.Dls.UI.ObjectModel.OMCommon.Schedule) `
    -SyncFrequency 240

# Retention: 10 giorni su disco, 12 mesi su Azure
Set-DPMPolicyObjective -ProtectionGroup $pg -RetentionRangeInDays 10 `
    -OnlineRetentionRangeInMonths 12

# Committare il Protection Group
Set-DPMProtectionGroup -ProtectionGroup $pg

# 5. Monitorare
Get-DPMJob -DPMServerName "DPM01" -Status InProgress
Get-DPMAlert -DPMServerName "DPM01" | Where-Object Severity -eq "Error"
```

### DPM — Backup su tape

```
DPM supporta tape library per backup a lungo termine.

CONFIGURAZIONE:
1. Collegare la tape library al DPM server (SAS/FC/iSCSI)
2. DPM Console → Management → Libraries → Rescan
3. Nel Protection Group: selezionare "I want long-term protection using tape"
4. Configurare:
   - Schedule: settimanale/mensile/annuale
   - Retention: es. 1 anno settimanale, 7 anni annuale
   - Tape labeling: etichettatura automatica
   
ROTAZIONE TAPE:
   Tape offsite settimanale: spedire una copia fuori sede
   Tape annuale: conservare per il periodo di retention compliance
   
LIMITAZIONI:
   - Restore da tape è lento (seek + read sequenziale)
   - Non supporta granular recovery diretto da tape (serve restore su disco)
   - Tape deteriorano: verificare periodicamente con test di lettura
```

---

## Active Directory Recovery

### Non-Authoritative Restore

```powershell
# Ripristina AD dal backup. Il DC riceve poi le modifiche
# più recenti dagli altri DC via replica normale.
# Usare quando: il DC ha problemi ma gli altri DC sono OK

# 1. Riavviare in DSRM
bcdedit /set safeboot dsrepair
Restart-Computer

# 2. Login con .\Administrator e password DSRM

# 3. Restore System State
wbadmin start systemstaterecovery -version:MM/DD/YYYY-HH:MM -backupTarget:E:

# 4. Riavviare normalmente
bcdedit /deletevalue safeboot
Restart-Computer

# 5. Il DC replica con gli altri e si aggiorna
```

### Authoritative Restore

```powershell
# Ripristina un oggetto specifico e lo FORZA su tutti i DC
# Usare quando: un oggetto è stato cancellato e deve essere recuperato

# 1-3. Come sopra (DSRM + System State restore)

# 4. Prima di riavviare, marcare l'oggetto come authoritative
ntdsutil
> activate instance ntds
> authoritative restore
> restore object "CN=Mario Rossi,OU=Utenti,DC=corp,DC=contoso,DC=com"
> quit
> quit

# Per un'intera OU:
> restore subtree "OU=Utenti,DC=corp,DC=contoso,DC=com"

# 5. Riavviare normalmente
# L'oggetto marcato come authoritative ha version number più alto
# e sovrascrive la cancellazione su tutti gli altri DC

# AD Recycle Bin (alternativa moderna — Windows Server 2008 R2+)
# Se abilitato, gli oggetti cancellati vengono conservati per 180 giorni

# Abilitare (una volta, irreversibile)
Enable-ADOptionalFeature "Recycle Bin Feature" -Scope ForestOrConfigurationSet `
    -Target "corp.contoso.com"

# Recuperare oggetto dal cestino
Get-ADObject -Filter 'Name -like "Mario*"' -IncludeDeletedObjects |
    Where-Object isDeleted -eq $true |
    Restore-ADObject
```

### DSRM — Directory Services Restore Mode

```powershell
# DSRM è una modalità di avvio speciale per i Domain Controller
# Permette di eseguire operazioni sul database AD offline

# Impostare/modificare la password DSRM
ntdsutil
> set dsrm password
> reset password on server null
# (inserire nuova password)
> quit
> quit

# Sincronizzare la password DSRM con un account AD
# (utile per non dimenticare la password DSRM)
ntdsutil
> set dsrm password
> sync from domain account CORP\dsrm-sync-account
> quit
> quit

# Configurare sync automatica (via Registry + Task Scheduler)
# HKLM\System\CurrentControlSet\Control\Lsa\DsrmAdminLogonBehavior
# Valore 1: permette login DSRM anche in modalità normale (utile per test)
# Valore 2: permette login DSRM solo quando il servizio AD DS è fermato
# Valore 0 (default): login DSRM solo in Safe Mode

# ATTENZIONE sulla password DSRM:
# - È l'unica via di accesso se AD è corrotto
# - Documentarla in un luogo sicuro offline
# - Testarla periodicamente (almeno ogni 6 mesi)
# - Cambiarla quando il personale IT cambia
```

### AD Recovery — Scenari avanzati

```powershell
# SCENARIO 1: DC corrotto, altri DC sani
# → Non-Authoritative Restore oppure DCPromo nuovo DC + replica
# Se il DC è l'unico con un ruolo FSMO:
Get-ADDomain | Select-Object InfrastructureMaster, PDCEmulator, RIDMaster
Get-ADForest | Select-Object SchemaMaster, DomainNamingMaster
# Trasferire i ruoli FSMO prima di decommissionare:
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" `
    -OperationMasterRole PDCEmulator, RIDMaster, InfrastructureMaster

# SCENARIO 2: Cancellazione massiva di oggetti AD
# → AD Recycle Bin (se abilitato) o Authoritative Restore
# Con Recycle Bin:
Get-ADObject -Filter 'isDeleted -eq $true -and ObjectClass -eq "user"' `
    -IncludeDeletedObjects -Properties WhenChanged |
    Where-Object { $_.WhenChanged -gt (Get-Date).AddHours(-4) } |
    Restore-ADObject

# SCENARIO 3: Corruzione dell'intero database AD (NTDS.DIT)
# → Se più DC: demote il DC corrotto, pulire metadata, promuovere nuovo DC
# → Se unico DC: restore System State da backup noto buono

# SCENARIO 4: Ransomware su tutti i DC
# → Isolamento rete totale
# → Restore DC primario da backup air-gapped
# → Rebuild DC secondari da replica dopo restore
# → Reset KRBTGT password (due volte, con 12 ore di intervallo)
# → Reset password tutti gli account admin
```

---

## Bare Metal Recovery

```powershell
# BMR ripristina un server da zero su hardware nuovo o esistente
# Include: volumi di sistema, boot manager, system state, e dati necessari

# Prerequisiti per BMR:
# 1. Backup con flag -allCritical o Add-WBBareMetalRecovery
# 2. Supporto di avvio (USB/DVD) con Windows Server Installation Media

# Creare backup BMR
wbadmin start backup -backupTarget:E: -allCritical -vssFull -quiet

# PROCEDURA DI RECOVERY:
# 1. Avviare dal media di installazione Windows Server
# 2. Scegliere lingua → "Repair your computer"
# 3. Troubleshoot → System Image Recovery
# 4. Selezionare il backup (da disco locale, rete, o USB)
# 5. Scegliere: Use latest available → Restore
# 6. Il server riparte come al momento del backup

# Se backup su rete:
# In WinRE → Command Prompt
# net use Z: \\BACKUP-SRV\Backups /user:CORP\admin
# Poi: System Image Recovery → selezionare backup dalla rete

# DOPO IL RESTORE:
# - Verificare servizi e applicazioni
# - Applicare aggiornamenti mancanti (dal momento del backup ad oggi)
# - Se DC: verificare replica AD (repadmin /replsummary)
# - Se cluster: verificare stato nodo
```

### BMR — Procedura Dettagliata Step-by-Step

```
FASE 1: VERIFICA PRE-BACKUP (da eseguire PRIMA del disastro)

    1. Determinare la modalità di boot del server:
       - UEFI o Legacy BIOS? → msinfo32 → System Summary → BIOS Mode
       - IMPORTANTE: il restore DEVE usare la stessa modalità di boot.
         Un backup UEFI non può essere ripristinato in modalità Legacy
         e viceversa. Documentare questa informazione.

    2. Verificare che il backup BMR sia completo:
       wbadmin get versions -backupTarget:E:
       → Cercare "Can Recover: Bare Metal Recovery, ..."
       Se non appare "Bare Metal Recovery", il backup non include
       i volumi critici. Rifare con -allCritical.

    3. Creare e testare il WinPE/WinRE bootable:
       - USB con media di installazione Windows Server (stessa versione)
       - O WinPE personalizzato con driver storage (vedi sezione dedicata)
       - Verificare che il media avvii correttamente PRIMA del disastro

    4. Documentare la configurazione hardware:
       - Modello server, controller RAID, NIC
       - Layout partizioni: Get-Partition | Format-Table DiskNumber, PartitionNumber,
         Size, Type, DriveLetter
       - Modalità boot (UEFI/Legacy)

FASE 2: BOOT IN WINRE (durante il disastro)

    1. Inserire il media di installazione Windows Server (USB/DVD)
    2. Configurare il boot order nel BIOS/UEFI per avviare dal media
    3. Alla schermata di installazione:
       - Selezionare lingua e layout tastiera
       - Cliccare "Repair your computer" (NON "Install now")

    4. Troubleshoot → System Image Recovery
       Se il wizard non trova il backup automaticamente:
       a. Selezionare "Select a system image" → Next
       b. Se backup su disco locale: il wizard lo trova se il driver
          del controller storage è caricato
       c. Se backup su rete: cliccare "Advanced" → "Search for a
          system image on the network"

    5. Configurazione rete in WinRE (se backup su rete):
       Aprire Command Prompt da Troubleshoot → Command Prompt

       # Inizializzare la rete
       wpeutil initializenetwork

       # Verificare che la NIC sia riconosciuta
       ipconfig /all

       # Se DHCP non funziona, configurare IP statico:
       netsh interface ip set address "Ethernet" static 192.168.1.100 255.255.255.0 192.168.1.1
       netsh interface ip set dns "Ethernet" static 192.168.1.10

       # Mappare la share di rete con il backup
       net use Z: \\BACKUP-SRV\Backups /user:CORP\admin P@ssword

       # Se la NIC non è riconosciuta: caricare il driver
       drvload X:\drivers\nic\e1d65x64.inf

    6. Tornare a System Image Recovery e selezionare il backup dalla rete

FASE 3: ESECUZIONE DEL RESTORE

    1. Il wizard mostra i dettagli del backup selezionato:
       - Data e ora del backup
       - Nome del computer
       - Dischi inclusi
    2. Opzioni avanzate:
       - "Format and repartition disks": riformatta i dischi secondo
         il layout originale. Selezionare se il disco di destinazione
         è nuovo o diverso dall'originale.
       - "Only restore system drives": ripristina solo i volumi di sistema
         (utile se i dati sono su volumi separati non compromessi)
    3. Confermare → il restore inizia
    4. Tempo stimato: dipende dalla dimensione e dalla velocità I/O.
       Regola empirica: ~30-60 GB/ora su disco locale, ~10-30 GB/ora su rete.

FASE 4: VALIDAZIONE POST-RESTORE

    Dopo il riavvio, eseguire la seguente checklist:
```

```powershell
# Script: Post-BMR-Validation.ps1
# Eseguire immediatamente dopo un bare metal recovery

Write-Host "=== VALIDAZIONE POST-BMR ===" -ForegroundColor Cyan

# 1. Verificare identità del server
Write-Host "`n[1] Identità server:" -ForegroundColor Yellow
Write-Host "  Hostname:    $env:COMPUTERNAME"
Write-Host "  Domain:      $(Get-WmiObject Win32_ComputerSystem | Select-Object -ExpandProperty Domain)"
Write-Host "  OS Version:  $((Get-WmiObject Win32_OperatingSystem).Caption)"

# 2. Verificare rete
Write-Host "`n[2] Configurazione rete:" -ForegroundColor Yellow
Get-NetIPAddress -AddressFamily IPv4 | Where-Object InterfaceAlias -notlike "Loopback*" |
    Format-Table InterfaceAlias, IPAddress, PrefixLength

# 3. Verificare DNS
Write-Host "[3] Risoluzione DNS:" -ForegroundColor Yellow
$domain = (Get-WmiObject Win32_ComputerSystem).Domain
Resolve-DnsName $domain -ErrorAction SilentlyContinue | Select-Object -First 1

# 4. Verificare servizi critici
Write-Host "`n[4] Servizi critici:" -ForegroundColor Yellow
$criticalServices = @("Netlogon", "DNS", "NTDS", "W32Time", "DFSR")
foreach ($svc in $criticalServices) {
    $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($s) {
        $color = if ($s.Status -eq "Running") { "Green" } else { "Red" }
        Write-Host "  $($svc): $($s.Status)" -ForegroundColor $color
    }
}

# 5. Se DC: verificare replica AD
Write-Host "`n[5] Replica AD (solo DC):" -ForegroundColor Yellow
if (Get-Service NTDS -ErrorAction SilentlyContinue) {
    repadmin /replsummary
    dcdiag /q
}

# 6. Verificare attivazione Windows
Write-Host "`n[6] Attivazione Windows:" -ForegroundColor Yellow
cscript //nologo C:\Windows\System32\slmgr.vbs /dli

Write-Host "`n=== VALIDAZIONE COMPLETATA ===" -ForegroundColor Cyan
```

### BMR — Hardware diverso

```
PROBLEMA: il backup è stato fatto su HW-A (Dell R740) e devo
ripristinare su HW-B (HPE DL380) con controller storage diverso.

SOLUZIONE:
1. Avviare dal media di installazione Windows Server su HW-B
2. In WinRE, caricare i driver del controller storage:
   - Command Prompt → drvload X:\drivers\controller.inf
   - Oppure: inserire USB con driver, il wizard li trova automaticamente
3. Procedere con System Image Recovery
4. Dopo il restore, Windows rileva l'hardware diverso e installa driver

DRIVER CRITICI:
   - Controller storage (RAID, HBA, NVMe)
   - Controller di rete (per backup da rete)
   - Chipset (per stabilità generale)

POST-RESTORE SU HW DIVERSO:
   - Verificare Device Manager: nessun dispositivo con punto esclamativo
   - Reinstallare driver specifici del vendor (management agents, monitoring)
   - Verificare licenza Windows (può richiedere riattivazione su HW diverso)
   - Se DC: verificare che i GUID e i SID siano corretti
   - Se cluster: potrebbe richiedere riconfigurazione del nodo
```

### BMR — WinPE personalizzato

```powershell
# Creare un WinPE bootable con driver e tool precaricati
# Utile per BMR su hardware non standard

# Installare Windows ADK + WinPE add-on
# (scaricare da Microsoft)

# Creare ambiente WinPE
copype amd64 C:\WinPE_custom

# Montare l'immagine
Dism /Mount-Image /ImageFile:C:\WinPE_custom\media\sources\boot.wim `
    /Index:1 /MountDir:C:\WinPE_custom\mount

# Aggiungere driver
Dism /Image:C:\WinPE_custom\mount /Add-Driver /Driver:C:\Drivers\Storage /Recurse

# Aggiungere PowerShell a WinPE
Dism /Image:C:\WinPE_custom\mount /Add-Package `
    /PackagePath:"C:\ADK\WinPE_OCs\WinPE-WMI.cab"
Dism /Image:C:\WinPE_custom\mount /Add-Package `
    /PackagePath:"C:\ADK\WinPE_OCs\WinPE-NetFx.cab"
Dism /Image:C:\WinPE_custom\mount /Add-Package `
    /PackagePath:"C:\ADK\WinPE_OCs\WinPE-PowerShell.cab"

# Smontare e salvare
Dism /Unmount-Image /MountDir:C:\WinPE_custom\mount /Commit

# Creare ISO bootable
MakeWinPEMedia /ISO C:\WinPE_custom C:\WinPE_custom\WinPE_BMR.iso

# Creare USB bootable
MakeWinPEMedia /UFD C:\WinPE_custom F:
```

---

## PowerShell Backup Automation

### Script di backup automatizzato con reporting

```powershell
# Script: Automated-Backup.ps1
# Esegue backup WSB e invia report via email

param(
    [string]$BackupTarget = "E:",
    [string]$SmtpServer = "smtp.corp.contoso.com",
    [string]$EmailTo = "it-team@corp.contoso.com",
    [string]$EmailFrom = "backup-monitor@corp.contoso.com"
)

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
$logFile = "C:\BackupLogs\Backup_$timestamp.log"

function Write-Log {
    param([string]$Message)
    $entry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
    Add-Content -Path $logFile -Value $entry
    Write-Host $entry
}

try {
    Write-Log "=== INIZIO BACKUP ==="
    Write-Log "Target: $BackupTarget"
    Write-Log "Server: $env:COMPUTERNAME"

    # Verificare spazio disponibile
    $disk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='$BackupTarget'"
    $freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
    Write-Log "Spazio libero su $BackupTarget : $freeGB GB"

    if ($freeGB -lt 50) {
        Write-Log "ATTENZIONE: spazio insufficiente (< 50 GB)"
    }

    # Verificare VSS writers
    $vssOutput = vssadmin list writers 2>&1
    $failedWriters = ($vssOutput | Select-String "State:") | 
        Where-Object { $_ -notmatch "Stable" }
    if ($failedWriters) {
        Write-Log "ATTENZIONE: VSS Writer non stabili:"
        $failedWriters | ForEach-Object { Write-Log "  $_" }
    }

    # Eseguire backup
    Write-Log "Avvio backup..."
    $backupResult = wbadmin start backup -backupTarget:$BackupTarget `
        -include:C: -allCritical -vssFull -quiet 2>&1
    
    $backupResult | ForEach-Object { Write-Log $_ }

    # Verificare risultato
    $lastJob = Get-WBJob -Previous 1
    $status = $lastJob.JobState
    $duration = ($lastJob.EndTime - $lastJob.StartTime).ToString("hh\:mm\:ss")

    Write-Log "Stato: $status"
    Write-Log "Durata: $duration"
    Write-Log "=== FINE BACKUP ==="

    # Inviare report email
    $subject = if ($status -eq "Completed") {
        "[OK] Backup $env:COMPUTERNAME completato"
    } else {
        "[ERRORE] Backup $env:COMPUTERNAME FALLITO"
    }

    $body = Get-Content $logFile -Raw
    Send-MailMessage -From $EmailFrom -To $EmailTo -Subject $subject `
        -Body $body -SmtpServer $SmtpServer

} catch {
    Write-Log "ERRORE CRITICO: $_"
    Send-MailMessage -From $EmailFrom -To $EmailTo `
        -Subject "[CRITICO] Errore backup $env:COMPUTERNAME" `
        -Body "Errore: $_`n`nLog: $(Get-Content $logFile -Raw)" `
        -SmtpServer $SmtpServer
}
```

### wbadmin — Riferimento comandi

```powershell
# === WBADMIN REFERENCE ===

# Avviare backup
wbadmin start backup -backupTarget:<target> -include:<volumi> [opzioni]
    # -allCritical        include tutti i volumi critici per BMR
    # -vssFull            full VSS backup (aggiorna log backup delle app)
    # -vssCopy            copy VSS backup (non aggiorna log)
    # -quiet              non chiede conferma
    # -allowDeleteOldBackups  sovrascrive backup vecchi se spazio insufficiente

# Backup System State
wbadmin start systemstatebackup -backupTarget:<target> -quiet

# Elencare versioni di backup
wbadmin get versions [-backupTarget:<target>]

# Elencare elementi in un backup
wbadmin get items -version:<version> [-backupTarget:<target>]

# Recovery
wbadmin start recovery -version:<version> -itemType:<type> -items:<path> [opzioni]
    # -itemType:Volume    restore intero volume
    # -itemType:File      restore file/cartelle
    # -itemType:App       restore applicazione
    # -recoveryTarget:    dove ripristinare
    # -overwrite:Overwrite|Skip|CreateCopy

# System State recovery
wbadmin start systemstaterecovery -version:<version> [-backupTarget:<target>]

# Recovery su macchina alternativa (in WinRE)
wbadmin start sysrecovery -version:<version> -backupTarget:<target> -machine:<name>

# Eliminare backup
wbadmin delete backup -version:<version> [-backupTarget:<target>] -quiet
wbadmin delete systemstatebackup -keepVersions:3 -quiet

# Stato del backup in corso
wbadmin get status

# Fermare backup in corso
wbadmin stop job -quiet
```

### WBADMIN — Automazione Avanzata e Schedulazione

```powershell
# === SCHEDULE PERSISTENTE CON wbadmin enable backup ===
# Crea una policy di backup schedulata che sopravvive ai riavvii.
# Limitazione WSB: un solo schedule per server.

# Abilitare backup schedulato su disco dedicato
wbadmin enable backup -addtarget:E: -include:C:,D: -allCritical `
    -schedule:09:00,21:00 -vssFull -quiet

# Abilitare backup schedulato su share di rete
wbadmin enable backup -addtarget:\\BACKUP-SRV\Backups `
    -include:C: -allCritical -schedule:22:00 `
    -user:CORP\svc-backup -password:P@ss -vssFull -quiet

# Disabilitare backup schedulato
wbadmin disable backup -quiet

# === SUPERARE IL LIMITE DI UN SOLO SCHEDULE ===
# WSB permette un solo backup job schedulato per server.
# Per eseguire backup diversi (es. System State ogni 4 ore,
# full volume ogni notte), usare Task Scheduler + script wrapper.

# Script wrapper per System State backup ogni 4 ore
$scriptBlock = @'
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
$logFile = "C:\BackupLogs\SystemState_$timestamp.log"

try {
    wbadmin start systemstatebackup -backupTarget:E: -quiet 2>&1 | 
        Out-File -FilePath $logFile
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        Add-Content -Path $logFile -Value "ERRORE: wbadmin exit code $exitCode"
        # Scrivere evento nel Windows Event Log per monitoraggio
        Write-EventLog -LogName Application -Source "WSB-Custom" `
            -EventId 9001 -EntryType Error `
            -Message "System State backup fallito. Exit code: $exitCode"
    } else {
        Write-EventLog -LogName Application -Source "WSB-Custom" `
            -EventId 9000 -EntryType Information `
            -Message "System State backup completato con successo."
    }
} catch {
    Add-Content -Path $logFile -Value "ECCEZIONE: $_"
    Write-EventLog -LogName Application -Source "WSB-Custom" `
        -EventId 9002 -EntryType Error `
        -Message "System State backup eccezione: $_"
}
'@
# Salvare come C:\Scripts\SystemStateBackup.ps1

# Creare l'Event Log source personalizzata (una volta sola)
New-EventLog -LogName Application -Source "WSB-Custom" -ErrorAction SilentlyContinue

# Schedulare ogni 4 ore
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\Scripts\SystemStateBackup.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At "00:00" `
    -RepetitionInterval (New-TimeSpan -Hours 4) `
    -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

Register-ScheduledTask -TaskName "SystemStateBackup-4h" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Description "System State backup ogni 4 ore"

# === EVENT LOG — ID CHIAVE DI WINDOWS SERVER BACKUP ===
# Monitorare questi Event ID nel log Microsoft-Windows-Backup:
#
# Event ID 4  = Backup completato con successo
# Event ID 5  = Backup completato con avvisi
# Event ID 8  = Backup fallito
# Event ID 14 = Backup annullato dall'utente
# Event ID 17 = Backup System State completato con successo
# Event ID 18 = Backup System State fallito
# Event ID 49 = Spazio insufficiente sulla destinazione
# Event ID 50 = Impossibile accedere alla destinazione di rete
# Event ID 521 = Errore VSS durante il backup
#
# Esempio: alert via email su Event ID 8 (backup fallito)
# Configurare in Event Viewer → Attach Task To This Event
# oppure usare il modulo PowerShell ScheduledTaskNotification.

# === PULIZIA AUTOMATICA CON RETENTION PERSONALIZZATA ===
# WSB non offre retention granulare. Questo script implementa
# una retention personalizzata per backup System State.

# Mantenere solo gli ultimi 10 backup System State
$versions = wbadmin get versions 2>&1 | Select-String "Version identifier"
$versionCount = ($versions | Measure-Object).Count

if ($versionCount -gt 10) {
    # wbadmin delete systemstatebackup mantiene gli ultimi N
    wbadmin delete systemstatebackup -keepVersions:10 -quiet
    Write-EventLog -LogName Application -Source "WSB-Custom" `
        -EventId 9003 -EntryType Information `
        -Message "Pulizia backup: mantenuti ultimi 10 su $versionCount totali."
}
```

### Monitoraggio backup con PowerShell

```powershell
# Script: Monitor-BackupStatus.ps1
# Controlla lo stato dei backup su più server e genera report

$servers = @("DC01", "DC02", "FILESVR01", "SQLSVR01", "EXCH01")
$report = @()

foreach ($server in $servers) {
    try {
        $session = New-PSSession -ComputerName $server -ErrorAction Stop
        $summary = Invoke-Command -Session $session -ScriptBlock {
            $s = Get-WBSummary
            $lastJob = Get-WBJob -Previous 1
            [PSCustomObject]@{
                Server          = $env:COMPUTERNAME
                LastBackupTime  = $s.LastBackupTime
                LastResult      = $s.LastBackupResultHR
                NextBackupTime  = $s.NextBackupTime
                DetailedMessage = $lastJob.DetailedMessage
                JobState        = $lastJob.JobState
                Duration        = if ($lastJob.EndTime -and $lastJob.StartTime) {
                    ($lastJob.EndTime - $lastJob.StartTime).ToString("hh\:mm\:ss")
                } else { "N/A" }
            }
        }
        $report += $summary
        Remove-PSSession $session
    } catch {
        $report += [PSCustomObject]@{
            Server          = $server
            LastBackupTime  = "ERRORE CONNESSIONE"
            LastResult      = $_.Exception.Message
            NextBackupTime  = "N/A"
            DetailedMessage = "Impossibile connettersi al server"
            JobState        = "Unknown"
            Duration        = "N/A"
        }
    }
}

# Output console
$report | Format-Table Server, LastBackupTime, JobState, Duration, LastResult -AutoSize

# Export CSV
$report | Export-Csv "C:\BackupLogs\BackupReport_$(Get-Date -Format 'yyyy-MM-dd').csv" -NoTypeInformation

# Elencare server con backup falliti
$failed = $report | Where-Object { $_.JobState -ne "Completed" }
if ($failed) {
    Write-Host "`n=== BACKUP FALLITI ===" -ForegroundColor Red
    $failed | Format-Table Server, LastBackupTime, JobState, DetailedMessage
}
```

### Rotazione backup con PowerShell

```powershell
# Pulizia automatica backup vecchi — da schedulare via Task Scheduler

# Eliminare backup WSB più vecchi di N giorni (mantenere gli ultimi 5)
wbadmin delete systemstatebackup -keepVersions:5 -quiet

# Pulizia file di backup manuali
$backupPath = "E:\ManualBackups"
$retentionDays = 30

Get-ChildItem -Path $backupPath -Recurse -File |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$retentionDays) } |
    Remove-Item -Force -Verbose

# Pulizia log di backup vecchi
$logPath = "C:\BackupLogs"
Get-ChildItem -Path $logPath -Filter "*.log" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) } |
    Remove-Item -Force
```

---

## Robocopy per Backup File-Level

### Robocopy — Fondamenti per backup

```powershell
# Robocopy (Robust File Copy) è lo strumento built-in Windows
# per copia file-level affidabile. Non è un "backup" nel senso
# tradizionale (no VSS, no catalogo, no application-aware) ma è
# eccellente per mirror di cartelle e migrazione dati.

# === MIRROR (copia esatta della sorgente sulla destinazione) ===
# ATTENZIONE: /MIR elimina dalla destinazione i file non presenti nella sorgente!
robocopy "D:\Shares" "F:\Backup\Shares" /MIR /R:3 /W:5 /LOG:"C:\Logs\robocopy.log"

# === COPIA INCREMENTALE (solo file nuovi/modificati) ===
robocopy "D:\Shares" "F:\Backup\Shares" /E /XO /R:3 /W:5 /LOG+:"C:\Logs\robocopy.log"

# === FLAG PRINCIPALI ===
# /MIR          Mirror (equivale a /E /PURGE): copia tutto + elimina extra
# /E            Copia sottocartelle, incluse quelle vuote
# /S            Copia sottocartelle, escluse quelle vuote
# /XO           Escludi file più vecchi (copia solo più nuovi)
# /COPY:DATSOU  Cosa copiare: Data, Attributes, Timestamps, Security, Owner, aUditing
# /DCOPY:DAT    Cosa copiare per le directory
# /COPYALL      Equivale a /COPY:DATSOU (tutto)
# /SEC          Copia con security (equivale a /COPY:DATS)
# /R:n          Numero di retry per file falliti (default 1000000!)
# /W:n          Attesa tra retry in secondi (default 30!)
# /MT:n         Multi-thread: n thread paralleli (default 8, max 128)
# /LOG:file     Scrive log su file (sovrascrive)
# /LOG+:file    Appende al log
# /TEE          Output a console E a log simultaneamente
# /NP           No progress: non mostra percentuale (log più pulito)
# /NDL          No directory list: non logga nomi directory
# /NFL          No file list: non logga nomi file (solo summary)
# /ETA          Mostra tempo stimato di arrivo
# /XD dirs      Escludi directory
# /XF files     Escludi file
# /MAXAGE:n     Escludi file più vecchi di n giorni (o data YYYYMMDD)
# /MINAGE:n     Escludi file più nuovi di n giorni
# /MON:n        Monitor: riesegui quando cambiano almeno n file
# /MOT:n        Monitor: riesegui ogni n minuti

# IMPORTANTE: impostare SEMPRE /R e /W!
# I default (1M retry, 30s wait) possono bloccare robocopy per settimane
# su un singolo file inaccessibile.
```

### Robocopy — Scenari di backup

```powershell
# === BACKUP GIORNALIERO FILE SERVER ===
robocopy "D:\Shares\Contabilita" "\\BACKUP-SRV\Backup\Contabilita" `
    /MIR /COPY:DATSOU /DCOPY:DAT `
    /R:3 /W:5 /MT:16 `
    /XD "Temp" "Cache" `
    /XF "*.tmp" "*.bak" "thumbs.db" `
    /LOG:"C:\Logs\robocopy_contabilita_$(Get-Date -Format 'yyyyMMdd').log" `
    /TEE /NP

# === BACKUP CON VERSIONAMENTO (timestamp nella destinazione) ===
$dest = "F:\Backup\Daily\$(Get-Date -Format 'yyyy-MM-dd')"
robocopy "D:\Shares" $dest /E /COPY:DATSOU /R:3 /W:5 /MT:16 `
    /LOG:"C:\Logs\robocopy_daily.log"

# === MIGRAZIONE DATI (con ACL e attributi completi) ===
robocopy "\\OldServer\Shares" "\\NewServer\Shares" `
    /E /COPYALL /DCOPY:DAT `
    /R:5 /W:10 /MT:32 `
    /LOG:"C:\Logs\migration.log" /TEE /ETA

# === MONITOR CONTINUO (copia ogni volta che cambiano 10+ file) ===
robocopy "D:\HotFolder" "F:\Backup\HotFolder" /MIR /MON:10 /MOT:5 `
    /R:3 /W:5 /LOG+:"C:\Logs\robocopy_monitor.log"
```

### Robocopy — Schedulazione con Task Scheduler

```powershell
# Creare un task schedulato per robocopy backup giornaliero

# 1. Creare lo script wrapper
$scriptContent = @'
@echo off
set LOG=C:\Logs\robocopy_%date:~-4%%date:~3,2%%date:~0,2%.log
robocopy "D:\Shares" "\\BACKUP-SRV\Backup\Shares" /MIR /COPY:DATSOU /R:3 /W:5 /MT:16 /NP /LOG:"%LOG%"
set RC=%ERRORLEVEL%
if %RC% GTR 7 (
    echo ERRORE: Robocopy exit code %RC% >> "%LOG%"
    exit /b 1
)
exit /b 0
'@
# Nota: salvare come .bat e schedulare

# Robocopy exit codes:
# 0 = nessuna modifica
# 1 = file copiati con successo
# 2 = extra file/dir nella destinazione (con /MIR vengono eliminati)
# 4 = file/dir mismatch (file diversi trovati)
# 8 = errore copia su alcuni file
# 16 = errore fatale (nessun file copiato)
# Combinazioni: es. 3 = 1+2 = file copiati + extra rimossi (OK)
# REGOLA: exit code ≤ 7 = successo, > 7 = errore

# 2. Schedulare via PowerShell
$action = New-ScheduledTaskAction -Execute "C:\Scripts\RobocopyBackup.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "23:00"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 4)
$principal = New-ScheduledTaskPrincipal -UserId "CORP\svc-backup" `
    -LogonType Password -RunLevel Highest

Register-ScheduledTask -TaskName "RobocopyDailyBackup" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Description "Backup giornaliero file server via robocopy"
```

---

## Disaster Recovery Planning

### DR Plan Template

```
1. INVENTARIO
   - Lista server critici con: ruolo, IP, dipendenze, RPO/RTO
   - Documentazione configurazione (GPO, DNS, DHCP scope, firewall rules)
   - Credenziali: DSRM password, admin locali, account servizio

2. RPO e RTO per ogni sistema:
   RPO (Recovery Point Objective) = quanti dati posso perdere
   RTO (Recovery Time Objective) = in quanto tempo devo ripristinare

   | Sistema | RPO | RTO | Metodo |
   |---------|-----|-----|--------|
   | Domain Controller | 1 ora | 2 ore | System State + BMR |
   | File Server | 4 ore | 4 ore | WSB + Shadow Copy |
   | Database | 15 min | 1 ora | SQL backup + log shipping |
   | Web Server | 24 ore | 1 ora | VM snapshot + Config backup |
   | Exchange | 1 ora | 4 ore | Database backup + DAG |

3. PROCEDURA DI RECOVERY (per ogni scenario)
   Scenario A: Guasto singolo server
   → Restore da backup su hardware nuovo/VM
   → Tempo stimato: 2-4 ore

   Scenario B: Guasto site (incendio, alluvione)
   → Attivare site DR
   → Restore DC dal backup offsite
   → Restore servizi critici
   → Tempo stimato: 8-24 ore

   Scenario C: Ransomware
   → Isolare la rete
   → Identificare scope dell'infezione
   → Restore da backup air-gapped/offline
   → Rebuild sistemi compromessi
   → Tempo stimato: 24-72 ore

4. TEST
   - Test restore trimestrale (almeno)
   - DR drill annuale (simulazione completa)
   - Documentare risultati e miglioramenti
```

### Runbook di Disaster Recovery

```
Un runbook è una procedura passo-passo che chiunque nel team IT
deve poter seguire per ripristinare un servizio in caso di disastro.

STRUTTURA RUNBOOK PER SERVIZIO:

=== RUNBOOK: Domain Controller ===

PREREQUISITI:
- Backup System State recente (< 24 ore)
- Media di installazione Windows Server 2022
- Password DSRM (location: password manager, cassaforte ufficio X)
- Credenziali account servizio backup
- Accesso al repository backup (\\BACKUP-SRV\Backups o Azure vault)

SCENARIO 1: DC non avvia, altri DC sani
Tempo stimato: 2 ore
1. Verificare hardware (diagnostica vendor)
2. Se hardware OK → tentare Last Known Good Configuration
3. Se hardware guasto:
   a. Procurare server sostitutivo (o VM Hyper-V)
   b. BMR restore da ultimo backup
   c. Verificare: dcdiag /v
   d. Verificare: repadmin /replsummary
   e. Verificare: DNS funzionante (nslookup domain.com)
4. Se replica funziona → DC operativo

SCENARIO 2: DC unico (no ridondanza)
Tempo stimato: 4 ore
1. CRITICO: System State backup DEVE essere disponibile
2. Installare Windows Server da zero
3. Restore System State da backup
4. Boot in DSRM → wbadmin start systemstaterecovery
5. Riavviare normalmente
6. Verificare: dcdiag, repadmin, DNS, DHCP, GPO
7. LEZIONE APPRESA: implementare secondo DC immediatamente

SCENARIO 3: Ransomware su DC
Tempo stimato: 8-24 ore
1. ISOLARE la rete (scollegare switch, disabilitare interfacce)
2. NON riavviare i DC criptati (evidenza forense)
3. Restore DC primario da backup AIR-GAPPED/OFFLINE
4. Verificare integrità AD (database non corrotto)
5. Resettare password KRBTGT (2 volte, intervallo 12 ore)
6. Resettare tutte le password admin (Domain Admins, Enterprise Admins)
7. Resettare password account servizio critici
8. Ricostruire DC secondari (dcpromo da zero, non restore)
9. Solo dopo: ricollegare la rete segmento per segmento
10. Audit completo: cos'è stato compromesso, come è entrato

CONTATTI:
- IT Manager: [nome] [telefono]
- Vendor hardware: [contratto supporto] [numero ticket]
- Fornitore backup: [supporto]
- Fornitore security: [incident response team]
- Legale/DPO: [per notifiche GDPR se dati personali compromessi]
```

### Documentazione configurazione per DR

```powershell
# Script per esportare configurazione critica (eseguire regolarmente)

# === Active Directory ===
# Export GPO
Get-GPO -All | ForEach-Object {
    Backup-GPO -Guid $_.Id -Path "C:\DR-Docs\GPO" -Comment "DR Export $(Get-Date -Format 'yyyy-MM-dd')"
}

# Export DNS zones
$zones = Get-DnsServerZone | Where-Object IsAutoCreated -eq $false
foreach ($zone in $zones) {
    Export-DnsServerZone -Name $zone.ZoneName -FileName "C:\DR-Docs\DNS\$($zone.ZoneName).dns"
}

# Export DHCP
Export-DhcpServer -ComputerName $env:COMPUTERNAME -File "C:\DR-Docs\DHCP\dhcp-export.xml"

# Export OU structure
Get-ADOrganizationalUnit -Filter * | 
    Select-Object DistinguishedName, Name, Description |
    Export-Csv "C:\DR-Docs\AD\OU-Structure.csv" -NoTypeInformation

# Export ruoli FSMO
$domain = Get-ADDomain
$forest = Get-ADForest
[PSCustomObject]@{
    PDCEmulator          = $domain.PDCEmulator
    RIDMaster            = $domain.RIDMaster
    InfrastructureMaster = $domain.InfrastructureMaster
    SchemaMaster         = $forest.SchemaMaster
    DomainNamingMaster   = $forest.DomainNamingMaster
} | Export-Csv "C:\DR-Docs\AD\FSMO-Roles.csv" -NoTypeInformation

# === Rete ===
# Export configurazione IP di tutti i server
Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object InterfaceAlias -notlike "Loopback*" |
    Select-Object InterfaceAlias, IPAddress, PrefixLength, DefaultGateway |
    Export-Csv "C:\DR-Docs\Network\IP-Config.csv" -NoTypeInformation

# === Certificati ===
Get-ChildItem Cert:\LocalMachine\My |
    Select-Object Thumbprint, Subject, NotAfter, Issuer |
    Export-Csv "C:\DR-Docs\Certs\Certificates.csv" -NoTypeInformation
```

---

## Backup Testing — Schedule e Checklist

### Schedule di test consigliato

```
FREQUENZA MINIMA DI TEST:

| Test | Frequenza | Responsabile | Durata |
|------|-----------|-------------|--------|
| Verifica completamento job | Giornaliero (automatico) | Monitoring | 5 min |
| Restore singolo file | Settimanale | Backup admin | 30 min |
| Restore database SQL | Mensile | DBA | 1-2 ore |
| Restore System State DC | Trimestrale | AD admin | 2-4 ore |
| BMR su VM di test | Trimestrale | Infra team | 4-8 ore |
| Restore Exchange mailbox | Trimestrale | Mail admin | 1-2 ore |
| DR drill completo | Annuale | Tutto il team IT | 1-2 giorni |
| Test integrità tape | Semestrale | Backup admin | 2-4 ore |
| Verifica backup M365 | Trimestrale | Cloud admin | 1 ora |
| SureBackup (se Veeam) | Ogni backup (automatico) | Veeam | Automatico |

REGOLA: se un test fallisce, il backup NON è considerato valido.
Fissare il problema e ritestare prima di procedere.
```

### Checklist di test restore

```
=== CHECKLIST RESTORE FILE ===
[ ] Il file è stato ripristinato nella posizione corretta
[ ] La dimensione del file corrisponde all'originale
[ ] Il contenuto del file è integro (aprire e verificare)
[ ] I permessi NTFS sono corretti
[ ] Il timestamp del file è corretto
[ ] Il file è utilizzabile dall'applicazione che lo consuma

=== CHECKLIST RESTORE DATABASE SQL ===
[ ] Il database è online e accessibile
[ ] DBCC CHECKDB non riporta errori
[ ] Le tabelle contengono i dati attesi (row count)
[ ] Le query di produzione funzionano correttamente
[ ] Gli indici sono integri
[ ] I job SQL Agent sono configurati
[ ] Le connessioni applicative funzionano
[ ] Il PITR è stato testato (restore a un punto specifico)

=== CHECKLIST BMR ===
[ ] Il server si avvia correttamente
[ ] Windows è attivato
[ ] Tutti i servizi critici partono
[ ] La rete funziona (IP, DNS, gateway)
[ ] Il server è raggiungibile dagli altri server
[ ] Le applicazioni installate funzionano
[ ] Se DC: dcdiag passa tutti i test
[ ] Se DC: replica AD funziona (repadmin /replsummary)
[ ] Se cluster: il nodo si riunisce al cluster
[ ] Il monitoraggio riceve dati dal server ripristinato

=== CHECKLIST RESTORE ACTIVE DIRECTORY ===
[ ] dcdiag /v non riporta errori critici
[ ] repadmin /replsummary mostra replica sana
[ ] DNS risolve i record interni
[ ] DHCP rilascia indirizzi (se DC è anche DHCP)
[ ] GPO si applicano ai client (gpresult /r su un client)
[ ] Login utenti funzionano
[ ] Kerberos ticket vengono rilasciati (klist)
[ ] SYSVOL è replicato e accessibile (\\domain\SYSVOL)
[ ] FSMO roles sono corretti e raggiungibili

=== CHECKLIST RESTORE EXCHANGE ===
[ ] Il database è montato e sano
[ ] Gli utenti possono inviare e ricevere email
[ ] OWA (Outlook Web) funziona
[ ] ActiveSync funziona (test da mobile)
[ ] I flussi di posta interni ed esterni sono operativi
[ ] I transaction log vengono troncati dopo il backup
```

### Documentare i risultati dei test

```powershell
# Template per report test di restore

$testReport = [PSCustomObject]@{
    Data              = Get-Date -Format "yyyy-MM-dd"
    TipoTest          = "BMR"                    # File/DB/BMR/SystemState/DR
    ServerOrigine     = "FILESVR01"
    BackupUsato       = "2026-05-20 21:00"       # timestamp del backup
    AmbienteRestore   = "VM di test - HyperV02"  # dove è stato ripristinato
    TempoRestore      = "2 ore 15 minuti"        # durata effettiva
    Esito             = "SUCCESSO"               # SUCCESSO/PARZIALE/FALLIMENTO
    RTAmisurato       = "2:15:00"                # RTA effettivo
    RTOobiettivo      = "4:00:00"                # RTO dichiarato
    RTArispettato     = "SI"                     # RTA ≤ RTO?
    ProblemiRiscontrati = "Driver NIC non trovato in WinPE, aggiunto manualmente"
    AzioniCorrettive  = "Aggiornare WinPE personalizzato con driver NIC Intel I225"
    Tester            = "Nome Cognome"
    Approvato         = "IT Manager"
}

# Salvare in formato strutturato
$testReport | Export-Csv "C:\DR-Docs\TestRestore\TestReport_$(Get-Date -Format 'yyyyMMdd').csv" `
    -NoTypeInformation -Append
```

---

## Best Practices

1. **Testare i restore**: un backup non testato è come non avere backup. Testare trimestralmente
2. **Backup air-gapped**: almeno una copia offline/disconnessa per protezione ransomware
3. **System State per ogni DC**: backup quotidiano, retention 60 giorni
4. **AD Recycle Bin**: abilitare sempre — recovery molto più semplice
5. **Shadow Copy come complemento**: 2 snapshot al giorno per self-service utenti, MA non come unico backup
6. **Monitorare i job**: alert per backup falliti. Un backup fallito non rilevato è peggio di nessun backup
7. **Documentare le procedure**: chiunque nel team deve poter eseguire un restore seguendo la documentazione
8. **Password DSRM**: documentata e conservata in luogo sicuro. Testarla periodicamente
9. **Encryption dei backup**: crittografare i backup at rest e in transit. Per MARS Agent e Veeam: la passphrase di encryption è l'unica via per ripristinare — perderla significa perdere i backup
10. **Separazione dei privilegi**: l'account di backup non deve essere Domain Admin. Usare un account dedicato con i minimi privilegi necessari (Backup Operators group)
11. **Immutabilità**: dove possibile, usare storage immutabile (Veeam Linux Hardened Repository, Azure Immutable Vault, AWS S3 Object Lock) per impedire la cancellazione anche con credenziali compromesse
12. **Bandwidth management**: schedulare i backup completi in orari di basso carico. Usare throttling di rete per non impattare il traffico di produzione
13. **Patch management dei server di backup**: il server di backup è un target primario per il ransomware. Tenerlo aggiornato, hardened, e con accesso limitato
14. **Retention compliance**: verificare che le policy di retention soddisfino i requisiti legali e normativi (GDPR, SOX, HIPAA, normativa settoriale)
15. **Multi-site**: per DR offsite, verificare che i backup siano effettivamente accessibili dal sito secondario. Testare il restore dal sito DR, non solo dal sito primario
16. **Capacity planning**: monitorare la crescita dello storage di backup. Un backup che non ha più spazio è un backup che non viene eseguito

---

## Troubleshooting

### Errori VSS

**"VSS Writer in stato Failed"** → Identificare il writer con `vssadmin list writers`. I writer più comuni con problemi: SQL Server Writer, Exchange Writer, Hyper-V Writer. Riavviare il servizio Windows associato al writer (es. `Restart-Service MSSQLSERVER` per SQL). Se persiste, riavviare il servizio VSS stesso: `Restart-Service VSS`. Verificare Event Viewer → Application → eventi con source "VSS".

**"Backup fallisce con errore VSS"** → `vssadmin list writers` per verificare lo stato dei VSS writer. Writer in stato "Failed" o "Waiting for completion" causano il fallimento. Riavviare il servizio del writer problematico. Per SQL: verificare che il SQL VSS Writer sia attivo.

**"VSS errore 0x8004231f — Insufficient storage"** → Lo shadow storage è pieno. Aumentare con `vssadmin resize shadowstorage /for=D: /on=D: /maxsize=50GB`. Se il volume è pieno, liberare spazio o spostare lo shadow storage su un altro volume.

**"VSS errore 0x800423f4 — Writer experienced a non-transient error"** → Il writer ha un errore persistente. Verificare i log dell'applicazione associata. Per SQL: controllare ERRORLOG. Per Exchange: controllare Application Event Log per eventi MSExchange. Spesso richiede riavvio dell'applicazione, non solo del writer.

**"VSS Provider failure: errore 0x80042302"** → Il provider VSS non riesce a creare la shadow copy. Verificare che il volume target abbia spazio sufficiente. Se si usa un hardware provider (SAN): verificare la comunicazione tra server e SAN, aggiornare il VSS provider del vendor.

### Errori backup job

**"Spazio insufficiente per backup"** → Verificare spazio sulla destinazione, ridurre retention, escludere volumi non necessari. Per shadow copy: aumentare `maxsize` o ridurre frequenza snapshot.

**"Backup lento: throughput sotto i 50 MB/s"** → Verificare: (1) antivirus che scansiona i file di backup → escludere le cartelle backup dall'AV, (2) rete satura → schedulare in orari di basso carico o usare QoS, (3) disco destinazione frammentato o RAID degradato → verificare stato RAID e salute disco, (4) troppi snapshot VSS pendenti → eliminare snapshot vecchi, (5) Veeam: verificare bottleneck nel Proxy o Repository con le statistiche del job.

**"Backup job rimane in stato Running per ore"** → Controllare se un file è bloccato (lock esclusivo). Verificare con `Get-SmbOpenFile` o Process Explorer. File di database aperti, file di log in uso, file VSS in attesa possono bloccare il job. Se WSB: `wbadmin get status` per dettagli.

**"Backup su rete fallisce con errore di autenticazione"** → Verificare credenziali dell'account di backup. L'account deve avere permessi di scrittura sulla share di destinazione. Se l'account è cambiato o la password è scaduta, aggiornare le credenziali nella policy di backup. Verificare che il firewall non blocchi SMB (porta 445).

**"Backup Veeam fallisce con errore CBT (Changed Block Tracking)"** → CBT corrotto sulla VM Hyper-V/VMware. Resettare CBT: per Hyper-V, disabilitare e riabilitare CBT sulla VM. Per VMware: `Set-HardDisk -HardDisk $hd -DisableChangedBlockTracking` poi riabilitare. Il prossimo backup sarà un full (nessun delta disponibile).

**"Errore 2155348010: The version does not support this version of the file format"** → Backup creato con versione più recente di WSB rispetto a quella che tenta il restore. Aggiornare il server target allo stesso livello di patch del server sorgente.

### Errori di restore

**"BMR fallisce: backup non trovato"** → In WinRE, verificare che il driver del disco sia caricato. Per backup su rete: configurare la rete in WinRE (Command Prompt → `net use`). Il backup deve essere accessibile da WinPE/WinRE.

**"Restore file: accesso negato"** → L'account che esegue il restore non ha privilegi sufficienti. Per WSB: serve appartenenza al gruppo Backup Operators o Administrators. Per restore su share di rete: verificare permessi NTFS e share sulla destinazione.

**"Restore SQL fallisce con errore di page checksum"** → Il backup è corrotto. Verificare con `RESTORE VERIFYONLY FROM DISK = 'percorso.bak' WITH CHECKSUM`. Se corrotto: usare un backup precedente. Prevenzione: abilitare CHECKSUM in tutti i backup SQL (`WITH CHECKSUM`).

**"Restore VM Veeam: errore connessione all'hypervisor"** → Verificare che l'hypervisor sia raggiungibile dal Veeam server. Controllare credenziali di connessione in Veeam → Managed Servers. Se le credenziali sono cambiate, aggiornarle. Verificare che i servizi Hyper-V / vCenter siano attivi.

**"Restore Exchange: database non si monta dopo restore"** → Verificare lo stato del database con `Get-MailboxDatabase -Status`. Se il database è in stato "Dirty Shutdown": eseguire `eseutil /r` per replay dei log. Se mancano log: eseguire `eseutil /p` (repair, ultima risorsa — può causare perdita dati) seguito da `New-MailboxRepairRequest`.

### Errori Active Directory

**"AD restore: oggetti non appaiono dopo non-authoritative restore"** → La replica potrebbe richiedere tempo. Verificare con `repadmin /showrepl`. Se l'oggetto è stato cancellato su altri DC e il restore è non-authoritative, la cancellazione vince. Usare authoritative restore o AD Recycle Bin.

**"DSRM: password non funziona"** → La password DSRM è specifica del DC e non viene sincronizzata con AD. Se dimenticata: (1) da un altro DC, usare ntdsutil per resetarla da remoto, (2) in ultima istanza: reinstallare il DC e promuoverlo di nuovo. Prevenzione: documentare la password e testarla regolarmente.

**"Dopo restore DC: errore replica 8606 (insufficient attributes)"** → Indicativo di oggetti con attributi inconsistenti. Forzare replica completa: `repadmin /syncall /APed`. Se persiste: verificare il database AD con `ntdsutil → semantic database analysis → go fixup`.

**"Authoritative restore fallisce: ntdsutil errore di accesso"** → Verificare di essere in DSRM e loggati come .\Administrator (non come account di dominio). Il servizio AD DS deve essere fermato. Se il database è corrotto: tentare `ntdsutil → files → integrity` prima dell'authoritative restore.

### Errori Azure Backup

**"MARS Agent: backup fallisce con errore 0x80070005 (Access Denied)"** → L'account SYSTEM deve avere accesso alle cartelle protette. Verificare permessi NTFS. Se il server è un DC: verificare che la policy "Perform volume maintenance tasks" includa SYSTEM.

**"Azure VM Backup: snapshot fallisce con errore timeout"** → La VM impiega troppo per il freeze VSS. Cause: (1) il guest agent non è aggiornato → aggiornare VM Agent, (2) un'applicazione nella VM blocca VSS → verificare VSS writers nella VM, (3) disco con I/O elevato → schedulare backup in orario di basso carico.

**"Azure Backup: errore di rete durante upload"** → Verificare connettività verso `*.blob.core.windows.net`. Se si usa un proxy: configurarlo nel MARS Agent. Se la rete è instabile: il MARS Agent riprende automaticamente, ma upload molto grandi possono fallire su connessioni lente. Considerare Azure ExpressRoute per backup di grandi dimensioni.

### Errori Hyper-V

**"Hyper-V backup fallisce: Integration Services non installati"** → Installare Hyper-V Integration Services nella VM guest. Per Windows moderni è incluso automaticamente via Windows Update. Per Linux: installare `hyperv-daemons`. Senza Integration Services il backup sarà crash-consistent (non application-consistent).

**"Checkpoint merge molto lento dopo eliminazione"** → Il merge di .avhdx grandi può richiedere ore e causare I/O elevato. Non spegnere la VM durante il merge. Pianificare la rimozione dei checkpoint in orari di basso carico. Monitorare con `Get-VMCheckpoint` e `Measure-VM` per l'I/O.

---

## FAQ

**D1: Ogni quanto dovrei testare i restore dei backup?**
R: File individuali: settimanale. Database: mensile. System State/BMR: trimestrale. DR completo (con tutto il team): annuale. Se usi Veeam SureBackup, configura test automatici dopo ogni backup.

**D2: Shadow copy è un backup?**
R: No. Le shadow copy risiedono sullo stesso volume dei dati originali. Se il disco si guasta, si perdono dati E shadow copy insieme. Inoltre il ransomware cancella sistematicamente le shadow copy. Usarle come complemento per recovery rapido self-service, mai come unico metodo di protezione.

**D3: Ho bisogno di Veeam se ho Windows Server Backup?**
R: Dipende dalla complessità dell'ambiente. WSB è sufficiente per piccoli ambienti (< 10 server, requisiti di restore semplici). Per ambienti enterprise: Veeam offre instant VM recovery (RTO < 15 min), SureBackup (verifica automatica), granular recovery applicativo, replica, e orchestrazione DR. Il costo si giustifica quando il downtime costa più della licenza Veeam.

**D4: Come proteggo i backup dal ransomware?**
R: Strategia multilivello: (1) almeno una copia air-gapped (tape offsite, disco scollegato), (2) immutabilità dello storage (Veeam Linux Hardened Repository, Azure Immutable Vault, S3 Object Lock), (3) separazione credenziali (l'account di backup NON deve essere Domain Admin), (4) MFA sull'infrastruttura di backup, (5) monitoraggio anomalie (backup size che cambia drasticamente può indicare encryption ransomware).

**D5: Qual è la differenza tra non-authoritative e authoritative restore di AD?**
R: Non-authoritative: ripristina il DC dal backup, poi il DC riceve le modifiche più recenti dagli altri DC via replica. Usare quando il DC ha problemi ma gli altri DC sono sani. Authoritative: ripristina un oggetto specifico e lo forza su tutti i DC (incrementa il version number), impedendo che la replica sovrascriva il restore. Usare quando un oggetto è stato cancellato e deve essere recuperato.

**D6: Devo fare backup di Microsoft 365?**
R: Si. Microsoft garantisce la disponibilità dell'infrastruttura (SLA 99.9%), non la protezione dei dati degli utenti. Cancellazione accidentale, insider threat, ransomware su OneDrive/SharePoint, e requisiti di retention compliance non sono coperti. Usare una soluzione terze parti (Veeam Backup for M365, Commvault, AvePoint).

**D7: Quanto spazio devo prevedere per i backup?**
R: Regola empirica con deduplication: 1.5-2x la dimensione dei dati sorgente per 30 giorni di retention. Senza deduplication: 3-5x. Per SQL con transaction log frequenti: aggiungere 20-30% per i log. Monitorare la crescita mensile e fare capacity planning semestrale.

**D8: Il backup di Azure VM protegge anche i dati all'interno della VM?**
R: Si, il backup Azure VM è un backup a livello disco — cattura tutto il contenuto dei dischi della VM. Per database SQL in Azure VM: usare Azure Backup for SQL che offre backup application-aware con PITR fino al secondo, più granulare del backup VM.

**D9: Posso fare BMR su hardware completamente diverso?**
R: Si, con alcune accortezze. WinRE/WinPE deve avere i driver del controller storage del nuovo hardware. Dopo il restore: verificare Device Manager, reinstallare driver specifici del vendor, verificare attivazione Windows (potrebbe richiedere riattivazione). Se è un DC: i SID e i GUID restano invariati, quindi funziona.

**D10: Come gestisco la password DSRM?**
R: Documentarla in un password manager aziendale o in una cassaforte fisica. Testarla almeno ogni 6 mesi (boot in DSRM su un DC di test). Cambiarla quando il personale IT cambia. Può essere sincronizzata con un account AD via ntdsutil (`sync from domain account`), ma l'account sorgente deve essere protetto.

**D11: Quanto tempo serve per un Instant VM Recovery con Veeam?**
R: La VM è avviabile in 1-2 minuti dal backup. Le prestazioni iniziali sono limitate (la VM legge dal backup file via NFS). Dopo l'avvio, Storage vMotion / Live Migration migra i dati su storage di produzione. La migrazione completa dipende dalla dimensione della VM e dal throughput dello storage.

**D12: DPM o Veeam — quale scegliere?**
R: DPM: se l'infrastruttura è interamente Microsoft (Hyper-V, SQL, Exchange, SCOM) e si ha già la licenza System Center. Veeam: se l'ambiente è misto (VMware + Hyper-V), se servono funzionalità avanzate (Instant VM Recovery, SureBackup, Linux Hardened Repository), o se si vuole un prodotto specializzato nel backup. MABS (Azure Backup Server) è un'alternativa gratuita a DPM con funzionalità simili + integrazione Azure nativa.

**D13: Come faccio backup incrementale forever senza un full periodico?**
R: Veeam e Azure Backup supportano "incremental forever" con synthetic full. Il primo backup è un full. I successivi sono incrementali. Periodicamente il software crea un full sintetico combinando il full originale con gli incrementali, senza ricaricare tutti i dati dal server sorgente. Riduce il traffico di rete e la durata del backup window.

**D14: Il backup di Hyper-V cattura anche la configurazione della VM?**
R: Si. Il backup a livello VM (host-level) include la configurazione della VM (numero vCPU, RAM, rete, disco), i file .vhdx, e i production checkpoint. Al restore si ottiene una VM identica all'originale. I checkpoint standard (con stato memoria) vengono invece esclusi dal backup per ragioni di consistenza.

**D15: Come verifico che un backup SQL sia integro senza fare un restore completo?**
R: Usare `RESTORE VERIFYONLY FROM DISK = 'path.bak' WITH CHECKSUM`. Questo verifica la struttura del backup, i checksum delle pagine e la leggibilità dei dati senza scrivere nulla su disco. Non è un test completo (non verifica la consistenza logica del database), ma intercetta corruzioni del file di backup e problemi di I/O.

**D16: Quanto spesso devo fare il backup dei transaction log SQL per un RPO di 15 minuti?**
R: Il backup dei transaction log deve avvenire ogni 15 minuti o meno. Configurare un SQL Agent Job con schedule ogni 15 minuti. In ambienti critici (RPO < 5 minuti): considerare log shipping o Always On Availability Groups con replica sincrona, che offrono RPO vicino a zero.

**D17: Cosa succede se perdo la passphrase di encryption di Azure Backup / Veeam?**
R: I dati sono irrecuperabili. La passphrase è l'unica chiave per decrittare i backup. Microsoft e Veeam non possono recuperarla. Documentare la passphrase in almeno due luoghi sicuri separati (password manager + cassaforte fisica). Testare periodicamente che la passphrase documentata funzioni.

---

## Esercizi

### Esercizio 1: Windows Server Backup Completo

Configurare e testare un backup completo con Windows Server Backup:

1. Installare la feature con `Install-WindowsFeature Windows-Server-Backup`.
2. Configurare un backup schedulato giornaliero del volume C: su un disco dedicato con `wbadmin`.
3. Eseguire un System State backup separato con `wbadmin start systemstatebackup`.
4. Verificare il backup con `wbadmin get versions` e controllare l'Event Log (Event ID 4, source Microsoft-Windows-Backup).
5. Testare il restore di un singolo file e di un'intera cartella.

**Criteri di validazione**: `wbadmin get status` deve mostrare "completed successfully". Il file ripristinato deve essere identico all'originale (verificare con `Get-FileHash`).

### Esercizio 2: Bare Metal Recovery

Eseguire un test di bare metal recovery:

1. Su un server di lab, eseguire un bare metal backup con `wbadmin start backup -allCritical -systemState`.
2. Annotare la configurazione hardware (NIC, dischi, BIOS/UEFI).
3. Avviare il server da WinRE (media di installazione → Repair your computer → Troubleshoot → System Image Recovery).
4. Selezionare il backup e completare il restore.
5. Dopo il riavvio, verificare: servizi attivi, configurazione IP, domain join, applicazioni.

**Criteri di validazione**: il server deve essere operativo dopo il restore, con tutti i servizi funzionanti e la stessa identità AD (SID, hostname).

### Esercizio 3: Pianificazione Disaster Recovery

Creare un piano di DR completo per un ambiente con 2 DC, 1 file server, 1 SQL Server:

1. Definire RPO e RTO per ogni servizio (AD: RPO 1h/RTO 2h; SQL: RPO 15min/RTO 1h; File: RPO 4h/RTO 4h).
2. Scegliere la strategia di backup per ogni servizio (System State per AD, full+log per SQL, file-level per file server).
3. Documentare la sequenza di restore in caso di disastro completo (AD prima, poi DNS, poi SQL, poi file server).
4. Definire i test di verifica periodici (frequenza, responsabile, criteri di successo).
5. Creare un runbook operativo con checklist step-by-step per ogni scenario di ripristino.

**Criteri di validazione**: il piano deve coprire ogni scenario (singolo server, disastro completo, corruzione AD). I tempi stimati devono rispettare gli RTO definiti.

### Esercizio 4: Backup SQL Server con Transaction Log

Configurare un backup SQL Server con RPO di 15 minuti:

1. Verificare che il database sia in recovery model FULL con `SELECT DATABASEPROPERTYEX('dbname','Recovery')`.
2. Configurare un full backup giornaliero con `BACKUP DATABASE ... TO DISK`.
3. Configurare un differential backup ogni 4 ore.
4. Configurare un transaction log backup ogni 15 minuti tramite SQL Agent Job.
5. Testare il point-in-time recovery a una data/ora specifica con `RESTORE DATABASE ... WITH STOPAT`.

**Criteri di validazione**: il restore PITR deve recuperare i dati fino al minuto specificato. La catena di log backup deve essere integra (`RESTORE HEADERONLY`).

---

## Auto-valutazione

### Domanda 1

Qual è la regola 3-2-1 nel backup e perché è considerata il minimo?

<details>
<summary>Risposta</summary>

La regola 3-2-1 prevede: 3 copie dei dati (1 originale + 2 backup), su 2 tipi di supporto diversi (es. disco + tape/cloud), con 1 copia offsite (fuori sede o nel cloud). È il minimo perché protegge da: guasto hardware (2 supporti), disastro locale (1 offsite), errore umano (3 copie). Evoluzioni moderne: 3-2-1-1-0 aggiunge 1 copia immutabile (ransomware protection) e 0 errori nei test di restore.

Riferimento: Veeam, 3-2-1-1-0 Backup Rule. Consultato: 2026-05-23.
</details>

### Domanda 2

Qual è la differenza tra RPO e RTO?

<details>
<summary>Risposta</summary>

RPO (Recovery Point Objective) = quantità massima di dati che si può perdere, misurata in tempo. RPO 1 ora significa che si accetta di perdere fino a 1 ora di dati. Determinato dalla frequenza dei backup. RTO (Recovery Time Objective) = tempo massimo per ripristinare il servizio dopo un disastro. RTO 4 ore significa che il servizio deve essere operativo entro 4 ore. Determinato dalla velocità del restore e dalla complessità del recovery. RPO influenza il costo dello storage; RTO influenza l'infrastruttura di recovery.

Riferimento: ISO 22301, Business Continuity Management. Consultato: 2026-05-23.
</details>

### Domanda 3

Cosa include un System State backup e quando è necessario?

<details>
<summary>Risposta</summary>

System State include: registry, COM+ class registration database, boot files, Active Directory database (NTDS.DIT, solo su DC), SYSVOL (solo su DC), Certificate Services database (solo su CA), cluster service information (solo su nodi cluster). È necessario per: ripristino di un DC (authoritative/non-authoritative restore), recovery dopo corruzione del registry, ripristino di una CA. Un backup dei soli file non è sufficiente per ripristinare un DC.

Riferimento: Microsoft Learn, System State Backup. Consultato: 2026-05-23.
</details>

### Domanda 4

Come funziona VSS e perché è fondamentale per backup consistenti?

<details>
<summary>Risposta</summary>

VSS (Volume Shadow Copy Service) coordina tra il backup software (requestor), il sistema operativo (provider) e le applicazioni (writers) per creare uno snapshot consistente del volume in un istante specifico. Le applicazioni VSS-aware (SQL, Exchange, AD) flushano i buffer e bloccano le scritture momentaneamente durante la creazione dello snapshot, garantendo consistenza transazionale. Senza VSS, il backup potrebbe catturare file in stato inconsistente (open file problem), rendendo i dati inutilizzabili.

Riferimento: Microsoft Learn, Volume Shadow Copy Service. Consultato: 2026-05-23.
</details>

### Domanda 5

Qual è la differenza tra Veeam e DPM, e quando scegliere ciascuno?

<details>
<summary>Risposta</summary>

DPM (Data Protection Manager): ideale se l'infrastruttura è interamente Microsoft (Hyper-V, SQL, Exchange, SCOM) e si possiede già la licenza System Center. Integrato con l'ecosistema Microsoft, supporto Azure nativo. Veeam: ideale per ambienti misti (VMware + Hyper-V), offre funzionalità avanzate (Instant VM Recovery in 1-2 minuti, SureBackup per verifica automatica, Linux Hardened Repository per immutabilità). MABS (Azure Backup Server) è un'alternativa gratuita a DPM con funzionalità simili + integrazione Azure nativa.

Riferimento: Microsoft Learn, DPM Overview; Veeam Help Center. Consultato: 2026-05-23.
</details>

### Domanda 6

Come si verifica l'integrità di un backup SQL senza eseguire un restore completo?

<details>
<summary>Risposta</summary>

Usare `RESTORE VERIFYONLY FROM DISK = 'path.bak' WITH CHECKSUM`. Questo verifica: la struttura del backup file, i checksum delle pagine, la leggibilità dei dati, la completezza del backup set. Non è un test completo (non verifica la consistenza logica del database), ma intercetta corruzioni del file di backup e problemi di I/O. Per una verifica più approfondita: restore su un server di test ed eseguire `DBCC CHECKDB`. Automatizzare con Veeam SureBackup o DPM verification job.

Riferimento: Microsoft Learn, RESTORE VERIFYONLY. Consultato: 2026-05-23.
</details>

---

## Letture Primarie Consigliate

1. **Microsoft Learn: Windows Server Backup** — Guida completa a wbadmin, System State, bare metal recovery.
   https://learn.microsoft.com/en-us/windows-server/administration/windows-server-backup/windows-server-backup-overview
   Consultato: 2026-05-23.

2. **Microsoft Learn: Azure Backup** — Architettura, vault, policy, e scenari ibridi.
   https://learn.microsoft.com/en-us/azure/backup/
   Consultato: 2026-05-23.

3. **Veeam Help Center** — Documentazione completa Veeam Backup & Replication.
   https://www.veeam.com/documentation-guides-datasheets.html
   Consultato: 2026-05-23.

4. **Microsoft Learn: SQL Server Backup and Restore** — Full, differential, transaction log, PITR.
   https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/
   Consultato: 2026-05-23.

5. **Microsoft Learn: Active Directory Forest Recovery** — Procedura step-by-step per il ripristino di una foresta AD.
   https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/forest-recovery-guide/ad-forest-recovery-guide
   Consultato: 2026-05-23.

---

## Collegamenti Incrociati

| File | Relazione con questo modulo |
|---|---|
| [01-active-directory.md](01-active-directory.md) | Contesto: System State backup include NTDS.DIT e SYSVOL, authoritative restore |
| [07-storage-windows.md](07-storage-windows.md) | Prerequisito: volumi, VSS provider, storage per backup |
| [09-monitoraggio-performance.md](09-monitoraggio-performance.md) | Contesto: monitoraggio backup job, alerting su fallimenti |
| [11-servizi-certificati.md](11-servizi-certificati.md) | Contesto: backup del database CA e della chiave privata |
| [23-hyper-v-guida-completa.md](23-hyper-v-guida-completa.md) | Contesto: backup a livello VM, production checkpoints, Veeam per Hyper-V |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **BMR** | Bare Metal Recovery. Ripristino completo del sistema operativo e dati su hardware nuovo o esistente. |
| **DPM** | Data Protection Manager. Soluzione di backup enterprise Microsoft inclusa in System Center. |
| **DSRM** | Directory Services Restore Mode. Modalità di avvio speciale per il ripristino di Active Directory su un DC. |
| **MABS** | Microsoft Azure Backup Server. Versione gratuita di DPM con integrazione Azure nativa. |
| **PITR** | Point-In-Time Recovery. Ripristino di un database a un istante specifico tramite catena di transaction log. |
| **RPO** | Recovery Point Objective. Quantità massima di dati accettabilmente perdibili, espressa in tempo. |
| **RTO** | Recovery Time Objective. Tempo massimo per ripristinare un servizio dopo un disastro. |
| **VSS** | Volume Shadow Copy Service. Servizio Windows per snapshot consistenti di volumi, fondamentale per backup application-aware. |
| **wbadmin** | Tool da linea di comando per Windows Server Backup. Sostituisce ntbackup. |
| **Writer** | Componente VSS di un'applicazione (SQL, Exchange, AD) che garantisce consistenza durante lo snapshot. |
