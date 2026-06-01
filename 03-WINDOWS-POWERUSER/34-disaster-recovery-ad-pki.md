# Disaster Recovery — Active Directory + PKI

> **Modulo 34** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Corso** | Windows per ingegneri di sistema |
| **Fase** | Continuità operativa e disaster recovery |
| **Modulo del corso** | 34 — Disaster Recovery Active Directory + PKI |
| **Versioni di riferimento** | Windows Server 2025, AD DS 2025, AD CS 2025, Entra Connect 2.x, Azure Site Recovery |
| **Livello** | Proficient |
| **Prerequisiti** | Active Directory administration (→ `01-active-directory.md`, → `25-active-directory-design-avanzato.md`), PKI e certificati (→ `28-pki-certificati-guida-completa.md`), backup e ripristino (→ `15-backup-ripristino.md`) |
| **Obiettivi di apprendimento** | 1) Pianificare RTO e RPO differenziati per ruolo (DC, CA, DNS) e definire una strategia di backup System State · 2) Eseguire la procedura completa di AD forest recovery secondo la guida Microsoft ufficiale · 3) Configurare backup e restore di CA root offline ed Enterprise CA con protezione delle chiavi private · 4) Implementare authoritative e non-authoritative restore di oggetti AD e SYSVOL · 5) Testare e documentare runbook di DR con drill periodici in ambiente isolato |
| **Tempo stimato** | lettura 100 min · lab 180 min |
| **Ultimo aggiornamento** | 2026-05-23 |

## Idee guida

1. **AD Forest Recovery Guide e canonical: leggere intero pre-disaster.**
2. **Backup System State da DC: settimanale minimum.**
3. **PKI offline root CA backup: extract HSM key + cert.**
4. **DSRM (Directory Services Restore Mode) password documented.**
5. **CRL signing key rotation + republish.**
6. **Il disaster recovery di AD non è un evento — è un processo documentato, testato e ripetuto.**
7. **Senza AD funzionante, l'intera infrastruttura Windows è paralizzata: DNS, GPO, autenticazione, PKI.**
8. **RTO e RPO devono essere definiti PER RUOLO (DC, CA, DNS) — non come valori unici.**
9. **Il backup più recente è inutile se non è mai stato testato con un restore.**
10. **La forest recovery richiede isolamento di rete totale — un singolo DC compromesso può re-infettare l'intera forest.**


## Indice

- [Fondamenti di AD Disaster Recovery](#fondamenti-di-ad-disaster-recovery)
  - [Perché AD è un Single Point of Failure](#perché-ad-è-un-single-point-of-failure)
  - [Tipologie di Disastro AD](#tipologie-di-disastro-ad)
  - [Componenti Critici da Proteggere](#componenti-critici-da-proteggere)
  - [RTO e RPO per Servizi AD](#rto-e-rpo-per-servizi-ad)
- [Backup di Active Directory](#backup-di-active-directory)
  - [System State Backup — wbadmin](#system-state-backup--wbadmin)
  - [Cosa Include il System State](#cosa-include-il-system-state)
  - [Scheduling e Retention](#scheduling-e-retention)
  - [NTDS.DIT — Backup del Database AD](#ntdsdit--backup-del-database-ad)
  - [Snapshot AD con ntdsutil](#snapshot-ad-con-ntdsutil)
  - [Verifica Integrità dei Backup](#verifica-integrità-dei-backup)
  - [Backup di Terze Parti](#backup-di-terze-parti)
- [DSRM — Directory Services Restore Mode](#dsrm--directory-services-restore-mode)
  - [Che Cos'è DSRM](#che-cosè-dsrm)
  - [Password DSRM — Gestione e Reset](#password-dsrm--gestione-e-reset)
  - [Avvio in DSRM](#avvio-in-dsrm)
  - [DSRM Network Access](#dsrm-network-access)
  - [Operazioni Disponibili in DSRM](#operazioni-disponibili-in-dsrm)
- [Authoritative vs Non-Authoritative Restore](#authoritative-vs-non-authoritative-restore)
  - [Non-Authoritative Restore](#non-authoritative-restore)
  - [Authoritative Restore](#authoritative-restore)
  - [Authoritative Restore di Oggetti Specifici](#authoritative-restore-di-oggetti-specifici)
  - [Authoritative Restore di una Intera Subtree](#authoritative-restore-di-una-intera-subtree)
  - [Quando Usare Quale Metodo](#quando-usare-quale-metodo)
- [AD Recycle Bin](#ad-recycle-bin)
  - [Architettura e Funzionamento](#architettura-e-funzionamento)
  - [Abilitazione di AD Recycle Bin](#abilitazione-di-ad-recycle-bin)
  - [Recupero Oggetti Eliminati](#recupero-oggetti-eliminati)
  - [Tombstone e Deleted Object Lifetime](#tombstone-e-deleted-object-lifetime)
  - [Limitazioni di AD Recycle Bin](#limitazioni-di-ad-recycle-bin)
- [Forest Recovery — Procedura Completa](#forest-recovery--procedura-completa)
  - [Prerequisiti per la Forest Recovery](#prerequisiti-per-la-forest-recovery)
  - [Fase 1 — Isolamento e Valutazione](#fase-1--isolamento-e-valutazione)
  - [Fase 2 — Ripristino del Primo DC](#fase-2--ripristino-del-primo-dc)
  - [Fase 3 — Pulizia dei Metadata](#fase-3--pulizia-dei-metadata)
  - [Fase 4 — Seize dei Ruoli FSMO](#fase-4--seize-dei-ruoli-fsmo)
  - [Fase 5 — Ripristino dei DC Aggiuntivi](#fase-5--ripristino-dei-dc-aggiuntivi)
  - [Fase 6 — Ripristino di SYSVOL](#fase-6--ripristino-di-sysvol)
  - [Fase 7 — Validazione e Rientro in Produzione](#fase-7--validazione-e-rientro-in-produzione)
- [SYSVOL Restore — D2 e D4](#sysvol-restore--d2-e-d4)
  - [DFSR vs FRS — Determinare il Motore di Replica](#dfsr-vs-frs--determinare-il-motore-di-replica)
  - [DFSR D2 Restore (Non-Authoritative)](#dfsr-d2-restore-non-authoritative)
  - [DFSR D4 Restore (Authoritative)](#dfsr-d4-restore-authoritative)
  - [FRS Restore (Legacy)](#frs-restore-legacy)
  - [Verifica Post-Restore SYSVOL](#verifica-post-restore-sysvol)
- [DFSR Recovery Avanzata](#dfsr-recovery-avanzata)
  - [DFSR Database Corruption](#dfsr-database-corruption)
  - [DFSR Conflitti e Pre-Staging](#dfsr-conflitti-e-pre-staging)
  - [Ripristino DFSR dopo Journal Wrap](#ripristino-dfsr-dopo-journal-wrap)
- [DNS Integrated Zones Recovery](#dns-integrated-zones-recovery)
  - [AD-Integrated DNS — Come Funziona](#ad-integrated-dns--come-funziona)
  - [Backup delle Zone DNS](#backup-delle-zone-dns)
  - [Ripristino Zone DNS](#ripristino-zone-dns)
  - [Pulizia Record Stale dopo DR](#pulizia-record-stale-dopo-dr)
  - [Conditional Forwarders e Stub Zones](#conditional-forwarders-e-stub-zones)
- [PKI Disaster Recovery](#pki-disaster-recovery)
  - [Architettura PKI e Componenti Critici](#architettura-pki-e-componenti-critici)
  - [Backup della CA — Chiave Privata e Database](#backup-della-ca--chiave-privata-e-database)
  - [Restore della CA su Nuovo Server](#restore-della-ca-su-nuovo-server)
  - [CRL Availability durante Outage](#crl-availability-durante-outage)
  - [OCSP Responder Recovery](#ocsp-responder-recovery)
  - [Root CA Offline — Procedure di Recovery](#root-ca-offline--procedure-di-recovery)
  - [Subordinate CA Recovery](#subordinate-ca-recovery)
  - [Re-issue dopo Compromissione della CA](#re-issue-dopo-compromissione-della-ca)
  - [Certificate Template Recovery](#certificate-template-recovery)
- [Cross-Forest Trust Recovery](#cross-forest-trust-recovery)
  - [Trust Relationship Fundamentals](#trust-relationship-fundamentals)
  - [Ripristino Trust dopo Forest Recovery](#ripristino-trust-dopo-forest-recovery)
  - [Selective Authentication dopo Recovery](#selective-authentication-dopo-recovery)
  - [Verifica Trust Post-Recovery](#verifica-trust-post-recovery)
- [Azure AD Connect Disaster Recovery](#azure-ad-connect-disaster-recovery)
  - [Architettura AADConnect e Componenti](#architettura-aadconnect-e-componenti)
  - [Backup di AADConnect](#backup-di-aadconnect)
  - [Staging Server come DR Strategy](#staging-server-come-dr-strategy)
  - [Rebuild AADConnect da Zero](#rebuild-aadconnect-da-zero)
  - [Impatto su Entra ID durante Outage](#impatto-su-entra-id-durante-outage)
- [Bare Metal Recovery di Domain Controller](#bare-metal-recovery-di-domain-controller)
  - [BMR vs System State Restore](#bmr-vs-system-state-restore)
  - [Procedura BMR con Windows Server Backup](#procedura-bmr-con-windows-server-backup)
  - [BMR su Hardware Differente](#bmr-su-hardware-differente)
  - [Recovery di DC Virtualizzati](#recovery-di-dc-virtualizzati)
  - [VM Generation ID e SafeRestore](#vm-generation-id-e-saferestore)
- [DR Planning e Testing](#dr-planning-e-testing)
  - [DR Plan — Struttura e Contenuti](#dr-plan--struttura-e-contenuti)
  - [Testing del DR Plan](#testing-del-dr-plan)
  - [DR Drill — Tabletop vs Full Exercise](#dr-drill--tabletop-vs-full-exercise)
  - [Documentazione e Runbook](#documentazione-e-runbook)
  - [Comunicazione durante un Incidente](#comunicazione-durante-un-incidente)
- [Runbook Templates](#runbook-templates)
  - [Runbook — Single DC Failure](#runbook--single-dc-failure)
  - [Runbook — Forest-Wide Recovery](#runbook--forest-wide-recovery)
  - [Runbook — PKI CA Recovery](#runbook--pki-ca-recovery)
  - [Runbook — Ransomware AD Recovery](#runbook--ransomware-ad-recovery)
- [Scenari](#scenari)
- [Esercizi](#esercizi)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Letture](#letture)
- [Glossario](#glossario)


---

## Fondamenti di AD Disaster Recovery

### Perché AD è un Single Point of Failure

Active Directory è il cuore dell'infrastruttura Windows enterprise. Quando AD è down, l'impatto è totale:

| Servizio dipendente | Impatto senza AD |
|---|---|
| Autenticazione utenti | Login impossibile su tutti i PC domain-joined |
| Group Policy | Nessuna policy applicata, configurazioni drift |
| DNS (AD-integrated) | Risoluzione nomi interna fallisce |
| PKI / Certificati | Nessun enrollment, CRL check fallisce |
| File Server / DFS | Accesso negato a tutte le share |
| Exchange / Teams | Mail flow e autenticazione bloccati |
| SQL Server | Windows Authentication fallisce |
| SCCM / Intune | Nessun management delle macchine |
| VPN / RADIUS | Autenticazione remota impossibile |
| Applicazioni LDAP-integrated | Tutte le app line-of-business down |

**Concetto chiave:** AD non è "un servizio tra tanti" — è IL servizio da cui tutti gli altri dipendono. Il DR plan di AD ha priorità assoluta rispetto a qualsiasi altro sistema.

### Tipologie di Disastro AD

```
┌─────────────────────────────────────────────────────────────┐
│                  CLASSIFICAZIONE DISASTRI AD                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LIVELLO 1 — Singolo Oggetto                                │
│  ├── Cancellazione accidentale OU/utente/gruppo             │
│  ├── Modifica errata di attributi critici                   │
│  └── Recovery: AD Recycle Bin, Authoritative Restore        │
│                                                             │
│  LIVELLO 2 — Singolo DC                                     │
│  ├── Hardware failure                                       │
│  ├── OS corruption                                          │
│  ├── NTDS.DIT corruption                                    │
│  └── Recovery: Rebuild DC, BMR, System State restore        │
│                                                             │
│  LIVELLO 3 — Multi-DC / Sito                                │
│  ├── Disastro naturale (sito fisico distrutto)              │
│  ├── Network partition prolungata                           │
│  ├── Storage failure condiviso (SAN)                        │
│  └── Recovery: Promozione DC secondari, site recovery       │
│                                                             │
│  LIVELLO 4 — Forest-Wide                                    │
│  ├── Ransomware / wiper che colpisce tutti i DC             │
│  ├── Schema corruption (irreversibile via replica)          │
│  ├── Compromissione totale (Golden Ticket, DC-Shadow)       │
│  ├── Errore amministrativo catastrofico                     │
│  └── Recovery: FULL FOREST RECOVERY                         │
│                                                             │
│  LIVELLO 5 — PKI Compromise                                 │
│  ├── Chiave privata CA compromessa                          │
│  ├── Root CA failure                                        │
│  ├── CRL/OCSP non raggiungibili                             │
│  └── Recovery: CA rebuild, re-issue, trust rebuild          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Componenti Critici da Proteggere

| Componente | Dove risiede | Frequenza backup | Note |
|---|---|---|---|
| NTDS.DIT | `%SystemRoot%\NTDS\` | System State, giornaliero | Database AD principale |
| SYSVOL | `%SystemRoot%\SYSVOL\` | System State + file-level | GPO, scripts di logon |
| Registry HKLM | System State | Automatico con SS | Configurazione servizi |
| Boot files (BCD) | System partition | System State | Necessario per avvio |
| DNS zones (AD-integrated) | Dentro NTDS.DIT | Con System State | Partizione DomainDnsZones |
| Certificate DB | `%SystemRoot%\CertLog\` | Backup CA separato | CA database + log |
| CA private key | Dipende (software/HSM) | Export manuale | Critico — mai in chiaro su disco |
| DFSR database | `%SystemRoot%\System Volume Information\DFSR\` | Automatico con SS | Journal e conflict files |
| Schema partition | NTDS.DIT | Con System State | Schema Master unico |
| Configuration partition | NTDS.DIT | Con System State | Sites, Services, PKI config |
| AADConnect config | Server AADConnect | Export configurazione | Regole di sync, filtri |

### RTO e RPO per Servizi AD

**RTO (Recovery Time Objective):** tempo massimo accettabile prima del ripristino del servizio.
**RPO (Recovery Point Objective):** quantità massima di dati che si accetta di perdere.

| Servizio | RTO raccomandato | RPO raccomandato | Giustificazione |
|---|---|---|---|
| Autenticazione (singolo DC) | 1 ora | 0 (replica) | DC ridondanti coprono |
| Autenticazione (forest-wide) | 4-8 ore | 24 ore max | Forest recovery complessa |
| DNS | 1 ora | 0 (AD-integrated) | Ridondanza multi-DC |
| SYSVOL / GPO | 4 ore | 24 ore | Restore D2/D4 |
| PKI — Issuing CA | 4-8 ore | Ultimo backup CA | Enrollment bloccato |
| PKI — CRL availability | 30 min | N/A | CRL cached, ma scadenza critica |
| FSMO roles | 2 ore | N/A | Seize se necessario |
| Cross-forest trust | 8-24 ore | N/A | Richiede forest funzionante |
| AADConnect sync | 24 ore | 30 min (staging) | Staging server come hot standby |

```powershell
# Documentare RTO/RPO nel registro AD — custom attributo su oggetto dominio
# Esempio: annotazione in description dell'oggetto Sites
Get-ADObject -Identity "CN=Sites,CN=Configuration,DC=contoso,DC=com" |
    Set-ADObject -Description "DR RTO: 4h Auth, 8h Forest | RPO: 24h | Ultimo test: 2026-05-15"
```


---

## Backup di Active Directory

### System State Backup — wbadmin

Il System State è il metodo ufficiale Microsoft per il backup di Active Directory. Contiene tutto ciò che serve per ripristinare un DC a uno stato consistente.

```powershell
# Installare la feature Windows Server Backup
Install-WindowsFeature Windows-Server-Backup -IncludeManagementTools

# Backup System State su volume dedicato
wbadmin start systemstatebackup -backupTarget:E: -quiet

# Backup System State su share di rete
wbadmin start systemstatebackup -backupTarget:\\backup-server\ad-backups -quiet

# Verificare l'ultimo backup
wbadmin get versions -backupTarget:E:

# Verificare che il backup sia di tipo System State
wbadmin get items -version:05/22/2026-06:00 -backupTarget:E:
```

**Requisiti di spazio:** il System State backup richiede circa 10-15 GB per DC, a seconda della dimensione del database AD e delle zone DNS.

**ATTENZIONE:** non usare mai un backup System State più vecchio della tombstone lifetime (default 180 giorni). Oggetti oltre questa soglia sono stati permanentemente eliminati e un restore causerebbe inconsistenze.

### Cosa Include il System State

```
System State Backup
├── Active Directory (NTDS.DIT + log)
├── SYSVOL
├── Registry (HKLM completo)
├── Boot Files (BCD, bootmgr)
├── COM+ Class Registration Database
├── Certificate Services Database (se il DC è anche CA)
├── Cluster Service Information (se presente)
├── IIS Metabase (se presente)
├── System Files protetti (WFP)
└── Performance Counter Configuration
```

### Scheduling e Retention

```powershell
# Creare un backup schedule giornaliero via PowerShell
# Backup giornaliero alle 02:00 sul volume E:
$policy = New-WBPolicy
$sysState = New-WBSystemState
Add-WBSystemState -Policy $policy
$target = New-WBBackupTarget -VolumePath E:
Add-WBBackupTarget -Policy $policy -Target $target
Set-WBSchedule -Policy $policy -Schedule 02:00
Set-WBPolicy -Policy $policy -Force

# Verificare la policy corrente
Get-WBPolicy -Editable

# Verificare lo stato dell'ultimo backup
Get-WBJob -Previous 1

# Verificare tutti i backup disponibili
Get-WBBackupSet
```

**Retention policy raccomandata:**

| Ambiente | Frequenza | Retention | Storage |
|---|---|---|---|
| Produzione critica | Giornaliero + settimanale full | 30 giorni giornalieri, 90 giorni settimanali | Volume dedicato + offsite |
| Produzione standard | Giornaliero | 14 giorni | Volume dedicato |
| Lab/Dev | Settimanale | 7 giorni | Volume locale |

```powershell
# Script di pulizia backup vecchi (eseguire come Scheduled Task)
# Mantiene solo gli ultimi 14 giorni
$cutoff = (Get-Date).AddDays(-14)
$versions = wbadmin get versions -backupTarget:E: | 
    Select-String "Version identifier" |
    ForEach-Object { $_.Line.Split(":")[1].Trim() }

foreach ($ver in $versions) {
    $verDate = [datetime]::ParseExact($ver.Substring(0,10), "MM/dd/yyyy", $null)
    if ($verDate -lt $cutoff) {
        wbadmin delete systemstatebackup -version:$ver -backupTarget:E: -quiet
        Write-Host "Eliminato backup: $ver"
    }
}
```

### NTDS.DIT — Backup del Database AD

Il file `NTDS.DIT` è il cuore di Active Directory. Contiene tutti gli oggetti, attributi, password hash e metadati di replica.

```powershell
# Localizzare NTDS.DIT e file di log
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" |
    Select-Object "DSA Database File", "Database log files path", "DSA Working Directory"

# Output tipico:
# DSA Database File       : C:\Windows\NTDS\ntds.dit
# Database log files path : C:\Windows\NTDS
# DSA Working Directory   : C:\Windows\NTDS

# Dimensione corrente del database
Get-Item C:\Windows\NTDS\ntds.dit | Select-Object Name, @{N='SizeMB';E={[math]::Round($_.Length/1MB,2)}}

# Verifica integrità del database (offline, richiede DSRM)
# Da eseguire in DSRM:
ntdsutil "activate instance ntds" "files" "integrity" quit quit

# Compattazione offline del database (in DSRM)
ntdsutil "activate instance ntds" "files" "compact to C:\temp\ntds_compact" quit quit
# Se successo: copiare il file compattato su quello originale
# e cancellare i log: del C:\Windows\NTDS\*.log
```

**Struttura del database NTDS.DIT:**

```
NTDS.DIT (Extensible Storage Engine — ESE / JET Blue)
├── Schema Partition (cn=schema,cn=configuration,dc=...)
│   └── Classi, attributi, OID, schema version
├── Configuration Partition (cn=configuration,dc=...)
│   └── Sites, Services, PKI, DFS-R topology
├── Domain Partition (dc=contoso,dc=com)
│   └── Utenti, gruppi, computer, OU, GPO links
├── Application Partitions
│   ├── DomainDnsZones
│   └── ForestDnsZones
└── Security descriptors (NTDS Security table)
```

### Snapshot AD con ntdsutil

Gli snapshot AD permettono di montare una copia read-only del database per consultazione senza impattare il DC in produzione.

```powershell
# Creare uno snapshot (DC online, nessun downtime)
ntdsutil "activate instance ntds" snapshot create quit quit
# Output: Snapshot set {GUID} generated successfully.

# Elencare gli snapshot disponibili
ntdsutil "activate instance ntds" snapshot "list all" quit quit

# Montare uno snapshot
ntdsutil "activate instance ntds" snapshot "mount {GUID}" quit quit

# Lo snapshot è montato come volume — esporre con dsamain per query LDAP
dsamain -dbpath "C:\$SNAP_202605220200_VOLUMEC$\Windows\NTDS\ntds.dit" -ldapport 33389

# Ora si può fare query con ldp.exe o PowerShell su localhost:33389
Get-ADUser -Filter * -Server localhost:33389 -Properties WhenChanged

# Smontare e pulire
ntdsutil "activate instance ntds" snapshot "unmount {GUID}" quit quit
ntdsutil "activate instance ntds" snapshot "delete {GUID}" quit quit
```

### Verifica Integrità dei Backup

**Non esiste backup valido se non è stato testato.**

```powershell
# Verificare che il backup sia consistente
wbadmin get versions -backupTarget:E:

# Test restore in ambiente isolato (VM senza rete)
# 1. Creare una VM isolata (no network adapter o VLAN isolata)
# 2. Boot da Windows Server ISO
# 3. Selezionare "Repair your computer" > Troubleshoot > System State Recovery
# 4. Verificare che AD si avvia correttamente
# 5. Eseguire dcdiag /v per validare

# Script di monitoring backup — inviare alert se backup fallito
$lastBackup = Get-WBJob -Previous 1
if ($lastBackup.JobState -ne 'Completed') {
    $body = "ALERT: System State backup fallito su $env:COMPUTERNAME`n"
    $body += "Stato: $($lastBackup.JobState)`n"
    $body += "Errore: $($lastBackup.ErrorDescription)`n"
    $body += "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC' -AsUTC)"
    
    Send-MailMessage -From "ad-backup@contoso.com" -To "ad-admins@contoso.com" `
        -Subject "CRITICAL: AD Backup Failed - $env:COMPUTERNAME" `
        -Body $body -SmtpServer "smtp.contoso.com"
}

# Verificare l'età del backup più recente
$latestBackup = Get-WBBackupSet | Sort-Object BackupTime -Descending | Select-Object -First 1
$backupAge = (Get-Date) - $latestBackup.BackupTime
if ($backupAge.TotalHours -gt 48) {
    Write-Warning "ATTENZIONE: ultimo backup più vecchio di 48 ore ($([math]::Round($backupAge.TotalHours,1))h)"
}
```

### Backup di Terze Parti

Strumenti come Veeam, Commvault, Veritas NetBackup e Cohesity supportano backup AD-aware.

**Vantaggi rispetto a wbadmin:**
- Granular object-level restore senza DSRM
- Confronto tra backup e stato corrente
- Dashboard centralizzata multi-DC
- Integrazione con storage enterprise

**Rischi:**
- Agent sul DC = superficie di attacco aggiuntiva
- Dipendenza da vendor per il restore
- Licenze costose
- Testare SEMPRE la procedura di restore del vendor specifico

```powershell
# Verifica che il backup agent sia in esecuzione (esempio Veeam)
Get-Service VeeamAgent -ErrorAction SilentlyContinue |
    Select-Object Name, Status, StartType

# Verifica eventi di backup nel log Application
Get-WinEvent -FilterHashtable @{
    LogName = 'Application'
    ProviderName = 'Microsoft-Windows-Backup'
    Level = 1,2  # Error, Critical
    StartTime = (Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, Id, Message
```


---

## DSRM — Directory Services Restore Mode

### Che Cos'è DSRM

DSRM (Directory Services Restore Mode) è una modalità di avvio speciale dei Domain Controller Windows che permette di accedere al server quando Active Directory non è disponibile. In DSRM, il servizio NTDS è fermo e il database `NTDS.DIT` è accessibile per operazioni di manutenzione e restore.

```
Avvio normale DC:                    Avvio DSRM:
┌─────────────────┐                  ┌─────────────────┐
│  Windows Boot   │                  │  Windows Boot   │
│       ↓         │                  │       ↓         │
│  NTDS Service   │ ← ATTIVO        │  NTDS Service   │ ← FERMO
│       ↓         │                  │       ↓         │
│  AD disponibile │                  │  AD OFFLINE     │
│       ↓         │                  │       ↓         │
│  Login con      │                  │  Login con      │
│  credenziali AD │                  │  account DSRM   │
│       ↓         │                  │       ↓         │
│  Servizi partono│                  │  Solo servizi   │
│  (DNS, DFS...)  │                  │  base (no DNS)  │
└─────────────────┘                  └─────────────────┘
```

### Password DSRM — Gestione e Reset

La password DSRM viene impostata durante la promozione del DC (`dcpromo` / `Install-ADDSDomainController`). È l'unica credenziale che funziona in DSRM e **deve essere documentata e conservata in modo sicuro**.

```powershell
# Reset della password DSRM (da eseguire sul DC con AD attivo)
ntdsutil "set dsrm password" "reset password on server null" quit quit
# Verrà richiesta la nuova password interattivamente

# Sincronizzare la password DSRM con un account AD specifico
# (permette di usare la stessa password di un account admin)
ntdsutil "set dsrm password" "sync from domain account AdminDSRM" quit quit

# Verificare che la sincronizzazione sia configurata via registry
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "DsrmAdminLogonBehavior"
# Valore 0 = solo DSRM locale (default)
# Valore 1 = DSRM locale + network se NTDS fermo
# Valore 2 = sempre (NON raccomandato — rischio pass-the-hash)
```

**Best practice per la password DSRM:**
- Password lunga (20+ caratteri), complessa, unica per DC
- Conservata in password manager aziendale o cassaforte fisica
- Rotata ogni 90 giorni
- Documentata nel runbook DR con posizione esatta
- **MAI** la stessa password su tutti i DC
- Testare il login DSRM almeno una volta l'anno

### Avvio in DSRM

```powershell
# Metodo 1: bcdedit (da Windows attivo, reboot in DSRM al prossimo avvio)
bcdedit /set safeboot dsrepair
Restart-Computer -Force

# Metodo 2: msconfig
# Eseguire msconfig > Boot > Safe boot > Active Directory repair

# Metodo 3: Shift+F8 durante il boot (poco affidabile su hardware moderno)

# Metodo 4: Per VM Hyper-V/VMware
# Hyper-V: Start VM, premi subito F8 o configura da bcdedit
# VMware: Modifica VMX con bios.bootDelay = "10000"

# IMPORTANTE: dopo il restore, rimuovere il flag safeboot!
bcdedit /deletevalue safeboot
Restart-Computer -Force
```

### DSRM Network Access

Per impostazione predefinita, la password DSRM funziona solo per login locale. Per abilitare l'accesso di rete (necessario per alcuni tool di restore remoto):

```powershell
# Configurare DsrmAdminLogonBehavior
# Valore 1 = accesso rete quando NTDS è fermo (raccomandato per DR)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "DsrmAdminLogonBehavior" -Value 1 -Type DWord

# Verificare la configurazione
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "DsrmAdminLogonBehavior"

# ATTENZIONE: Valore 2 permette login rete anche con NTDS attivo
# Questo è un rischio di sicurezza (pass-the-hash su account locale DSRM)
# Usare SOLO valore 1
```

### Operazioni Disponibili in DSRM

| Operazione | Disponibile in DSRM | Note |
|---|---|---|
| System State restore | Sì | Operazione primaria |
| NTDS.DIT integrity check | Sì | `ntdsutil files integrity` |
| NTDS.DIT compact | Sì | `ntdsutil files compact to` |
| NTDS.DIT move | Sì | `ntdsutil files move db to` |
| Authoritative restore | Sì | `ntdsutil auth restore` |
| Registry editing | Sì | regedit disponibile |
| File copy/backup | Sì | Explorer / xcopy |
| Active Directory queries | No | NTDS è fermo |
| DNS management | No | DNS dipende da AD |
| Replication | No | NTDS è fermo |
| GPO processing | No | Nessuna policy applicata |


---

## Authoritative vs Non-Authoritative Restore

### Non-Authoritative Restore

Un restore non-authoritative ripristina il DC a uno stato precedente. Dopo il riavvio, il DC contatta gli altri DC e **riceve tramite replica** tutte le modifiche avvenute dopo il backup, riportandosi allo stato corrente.

**Quando usarlo:** hardware failure di un singolo DC, OS corruption, NTDS.DIT corruption su un singolo DC.

```powershell
# Procedura Non-Authoritative Restore
# 1. Avviare il DC in DSRM
bcdedit /set safeboot dsrepair
Restart-Computer -Force

# 2. Login con credenziali DSRM: .\Administrator + password DSRM

# 3. Restore System State
wbadmin start systemstaterecovery -version:05/20/2026-02:00 -backupTarget:E: -quiet

# 4. Attendere il completamento (può richiedere 30-90 minuti)

# 5. Rimuovere il flag DSRM e riavviare
bcdedit /deletevalue safeboot
Restart-Computer -Force

# 6. Dopo il riavvio, il DC replicherà automaticamente le modifiche recenti
# Verificare con:
repadmin /replsummary
dcdiag /v
```

### Authoritative Restore

Un restore authoritative ripristina oggetti specifici e li **marca come più recenti** di qualsiasi altra copia nella forest. Dopo il riavvio, il DC replicherà VERSO gli altri DC, sovrascrivendo le loro copie.

**Quando usarlo:** cancellazione accidentale di OU, gruppi, utenti che si vuole ripristinare su tutti i DC.

```powershell
# Procedura Authoritative Restore
# 1. Avviare in DSRM e fare prima un non-authoritative restore (vedi sopra)

# 2. PRIMA di riavviare normalmente, eseguire il mark authoritative
# Aprire prompt dei comandi in DSRM

# 3. Marcare autoritativamente un oggetto specifico
ntdsutil "authoritative restore" "restore object \"CN=Mario Rossi,OU=Utenti,DC=contoso,DC=com\"" quit quit

# 4. Il comando incrementa il version number (USN) dell'oggetto
# di 100.000 per giorno dalla data del backup
# Questo garantisce che sia "più nuovo" di qualsiasi modifica successiva

# 5. Rimuovere flag DSRM e riavviare
bcdedit /deletevalue safeboot
Restart-Computer -Force

# 6. Il DC replicherà l'oggetto restored verso tutti gli altri DC
# perché il version number è il più alto
```

### Authoritative Restore di Oggetti Specifici

```powershell
# Restore di un singolo utente
ntdsutil "authoritative restore" "restore object \"CN=Mario Rossi,OU=Utenti,DC=contoso,DC=com\"" quit quit

# Restore di un singolo gruppo
ntdsutil "authoritative restore" "restore object \"CN=GruppoVendite,OU=Gruppi,DC=contoso,DC=com\"" quit quit

# Restore di un computer account
ntdsutil "authoritative restore" "restore object \"CN=PC-MARIO01,OU=Computer,DC=contoso,DC=com\"" quit quit

# NOTA: il restore di un utente NON ripristina automaticamente le membership
# di gruppo. Bisogna fare auth restore anche dei gruppi coinvolti.
# Il file .txt generato da ntdsutil contiene i link da ripristinare.

# Esempio output ntdsutil:
# Opening DIT database... Done.
# The current time is 05-22-2026 14:30:00.
# Most recent database update occurred at 05-20-2026 02:00:00.
# Increasing attribute version numbers by 200000.
# Counting records that need updating...
# Records found: 1
# Done.
# Successfully completed authoritative restore.
# The LDIF file "ar_20260522-143000_objects.ldf" was created.
# Use this file to re-create back-links for restored objects.
```

### Authoritative Restore di una Intera Subtree

```powershell
# Restore di un'intera OU e tutti gli oggetti contenuti
ntdsutil "authoritative restore" "restore subtree \"OU=Vendite,DC=contoso,DC=com\"" quit quit

# Restore dell'intero dominio (ESTREMO — usare solo per forest recovery)
ntdsutil "authoritative restore" "restore database" quit quit

# ATTENZIONE: il restore di una subtree grande può generare un'enorme
# quantità di traffico di replica. Pianificare durante una finestra
# di manutenzione e monitorare con:
repadmin /showrepl
repadmin /replsummary
```

### Quando Usare Quale Metodo

| Scenario | Metodo | Motivazione |
|---|---|---|
| DC hardware failure | Non-authoritative | Il DC si aggiorna dagli altri |
| DC OS corruption | Non-authoritative o rebuild | Gli altri DC hanno dati correnti |
| Cancellazione OU accidentale | Authoritative (subtree) | Serve sovrascrivere la cancellazione sugli altri DC |
| Utente cancellato ieri | AD Recycle Bin | Più semplice, no DSRM necessario |
| Schema corruption | Forest Recovery | Nessun metodo parziale funziona |
| Ransomware su tutti i DC | Forest Recovery | Tutti i DC compromessi |
| Modifica GPO errata | Backup GPO + re-import | Non serve restore AD |


---

## AD Recycle Bin

### Architettura e Funzionamento

AD Recycle Bin è una feature introdotta in Windows Server 2008 R2 (migliorata in 2012+) che permette di recuperare oggetti AD eliminati senza downtime e senza DSRM.

```
Ciclo di vita di un oggetto AD con Recycle Bin:
                                                              
  LIVE              DELETED           RECYCLED         REMOVED
  ┌──────┐         ┌──────┐         ┌──────┐         ┌──────┐
  │Object│──DEL──→ │Deleted│──TTL──→│Recycled│──TTL──→│Purged│
  │ con  │         │ tutti │  180d  │ perde  │  180d  │      │
  │attrs │         │ attrs │        │ attrs  │        │ gone │
  │      │         │intatti│        │non-link│        │      │
  └──────┘         └──────┘         └──────┘         └──────┘
                   ↑                                         
            Recover qui                                      
          (PowerShell)                                       
            FACILE                                           

Senza Recycle Bin (pre-2008 R2 o non abilitato):

  LIVE              TOMBSTONE         REMOVED
  ┌──────┐         ┌──────────┐      ┌──────┐
  │Object│──DEL──→ │Tombstone │──TTL→│Purged│
  │ con  │         │solo pochi│ 180d │      │
  │attrs │         │ attrs    │      │ gone │
  └──────┘         └──────────┘      └──────┘
                   ↑
            Recover qui = DIFFICILE
            (molti attributi persi)
```

### Abilitazione di AD Recycle Bin

**Prerequisiti:**
- Forest functional level: Windows Server 2008 R2 o superiore
- Tutti i DC nella forest devono avere almeno Windows Server 2008 R2
- **L'operazione è IRREVERSIBILE** — una volta abilitato, non si può disabilitare

```powershell
# Verificare il functional level corrente
Get-ADForest | Select-Object ForestMode
Get-ADDomain | Select-Object DomainMode

# Verificare se AD Recycle Bin è già abilitato
Get-ADOptionalFeature -Filter 'Name -like "Recycle Bin*"' |
    Select-Object Name, EnabledScopes

# Abilitare AD Recycle Bin (richiede Enterprise Admin)
Enable-ADOptionalFeature 'Recycle Bin Feature' `
    -Scope ForestOrConfigurationSet `
    -Target (Get-ADForest).Name `
    -Confirm:$false

# Verificare l'abilitazione
Get-ADOptionalFeature -Filter 'Name -like "Recycle Bin*"' |
    Select-Object Name, EnabledScopes
# EnabledScopes deve mostrare il DN della forest
```

### Recupero Oggetti Eliminati

```powershell
# Elencare tutti gli oggetti eliminati
Get-ADObject -Filter 'isDeleted -eq $true' -IncludeDeletedObjects -Properties * |
    Select-Object Name, ObjectClass, WhenChanged, DistinguishedName |
    Sort-Object WhenChanged -Descending

# Cercare un utente specifico eliminato
Get-ADObject -Filter 'isDeleted -eq $true -and Name -like "*Mario*"' `
    -IncludeDeletedObjects -Properties *

# Ripristinare un singolo utente
Get-ADObject -Filter 'isDeleted -eq $true -and Name -like "*Mario Rossi*"' `
    -IncludeDeletedObjects |
    Restore-ADObject

# Ripristinare un utente in una OU specifica (se la OU originale non esiste più)
Get-ADObject -Filter 'isDeleted -eq $true -and Name -like "*Mario Rossi*"' `
    -IncludeDeletedObjects |
    Restore-ADObject -TargetPath "OU=Utenti,DC=contoso,DC=com"

# Ripristinare un'intera OU e il suo contenuto
# ATTENZIONE: ripristinare prima la OU, poi gli oggetti contenuti
$ouDN = "OU=Vendite\0ADEL:a1b2c3d4-...,CN=Deleted Objects,DC=contoso,DC=com"
Restore-ADObject -Identity $ouDN

# Poi ripristinare gli oggetti dentro la OU
Get-ADObject -Filter 'isDeleted -eq $true -and LastKnownParent -eq "OU=Vendite,DC=contoso,DC=com"' `
    -IncludeDeletedObjects |
    Restore-ADObject

# Ripristinare un gruppo
Get-ADObject -Filter 'isDeleted -eq $true -and ObjectClass -eq "group" -and Name -like "*GruppoFinanza*"' `
    -IncludeDeletedObjects |
    Restore-ADObject

# Verificare il ripristino
Get-ADUser "Mario Rossi" -Properties MemberOf, WhenChanged
```

### Tombstone e Deleted Object Lifetime

```powershell
# Verificare la Tombstone Lifetime corrente
Get-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=contoso,DC=com" `
    -Properties tombstoneLifetime |
    Select-Object tombstoneLifetime
# Default: 180 giorni (Windows Server 2003 SP2+)
# Vecchi domini: 60 giorni

# Verificare la Deleted Object Lifetime (per Recycle Bin)
Get-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=contoso,DC=com" `
    -Properties "msDS-DeletedObjectLifetime" |
    Select-Object "msDS-DeletedObjectLifetime"
# Se null: usa lo stesso valore di tombstoneLifetime

# Modificare la Deleted Object Lifetime (esempio: 365 giorni)
Set-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=contoso,DC=com" `
    -Replace @{"msDS-DeletedObjectLifetime" = 365}

# Modificare la Tombstone Lifetime
Set-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=contoso,DC=com" `
    -Replace @{tombstoneLifetime = 365}
```

### Limitazioni di AD Recycle Bin

| Limitazione | Dettaglio |
|---|---|
| Oggetti oltre la DOL | Non recuperabili — sono stati purgati |
| Attributi linked dopo Recycled state | Persi (membership gruppi, manager, etc.) |
| Schema objects | Non eliminabili, quindi non nel Recycle Bin |
| Oggetti di configurazione | Recuperabili, ma verificare consistenza |
| Cross-domain links | Possono richiedere intervento manuale |
| Password dell'utente | Conservata in Deleted state, ma l'utente dovrà fare reset alla prima login |
| SID e SID History | Conservati — permessi NTFS intatti |
| Abilitazione | Irreversibile |


---

## Forest Recovery — Procedura Completa

La Forest Recovery è la procedura Microsoft ufficiale per ripristinare un'intera forest AD dopo un disastro catastrofico. È il processo più complesso e rischioso del DR di Active Directory.

### Prerequisiti per la Forest Recovery

**Prima del disastro (preparazione):**

```powershell
# 1. Documentare la topologia della forest
Get-ADForest | Format-List *
Get-ADDomain | Format-List *
Get-ADDomainController -Filter * |
    Select-Object Name, Domain, Site, IPv4Address, OperatingSystem, IsGlobalCatalog,
        @{N='FSMORoles';E={$_.OperationMasterRoles -join ', '}} |
    Format-Table -AutoSize

# 2. Documentare i ruoli FSMO
netdom query fsmo

# 3. Documentare la topologia dei siti
Get-ADReplicationSite -Filter * | Select-Object Name, Description
Get-ADReplicationSiteLink -Filter * | Select-Object Name, Cost, ReplicationFrequencyInMinutes, SitesIncluded
Get-ADReplicationSubnet -Filter * | Select-Object Name, Site

# 4. Esportare la configurazione DNS
# Per ogni zona:
Get-DnsServerZone | Where-Object { $_.ZoneType -ne 'Forwarder' } |
    ForEach-Object {
        Export-DnsServerZone -Name $_.ZoneName -FileName "$($_.ZoneName).dns.bak"
    }

# 5. Verificare che i backup System State siano recenti su OGNI DC
$dcs = Get-ADDomainController -Filter *
foreach ($dc in $dcs) {
    $lastBackup = Invoke-Command -ComputerName $dc.HostName -ScriptBlock {
        Get-WBBackupSet | Sort-Object BackupTime -Descending | Select-Object -First 1
    }
    [PSCustomObject]@{
        DC = $dc.Name
        LastBackup = $lastBackup.BackupTime
        AgeDays = [math]::Round(((Get-Date) - $lastBackup.BackupTime).TotalDays, 1)
    }
} | Format-Table -AutoSize

# 6. Salvare il forest recovery document stampato e offline
# Include: topology, FSMO, DC list, DSRM passwords, backup locations
```

### Fase 1 — Isolamento e Valutazione

```
┌─────────────────────────────────────────────────────────────┐
│              FASE 1: ISOLAMENTO E VALUTAZIONE               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DISCONNETTERE tutti i DC dalla rete di produzione       │
│     └── Nessun DC deve comunicare con altri DC              │
│     └── Previene re-infezione / replica di dati corrotti    │
│                                                             │
│  2. VALUTARE l'entità del danno                             │
│     ├── Quanti DC sono compromessi?                         │
│     ├── I backup sono integri e non compromessi?            │
│     ├── La compromissione è limitata ad AD o è più ampia?   │
│     └── Timestamp dell'ultimo stato "buono" noto            │
│                                                             │
│  3. SCEGLIERE il DC da ripristinare per primo               │
│     ├── Preferire un DC con backup recente e integro        │
│     ├── Preferire un DC che era Global Catalog              │
│     ├── Preferire il DC del root domain della forest        │
│     └── EVITARE DC RODC per il primo restore                │
│                                                             │
│  4. VERIFICARE l'integrità del backup scelto                │
│     └── wbadmin get versions + test restore su VM isolata   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Fase 2 — Ripristino del Primo DC

```powershell
# Il primo DC è il punto di partenza per ricostruire tutta la forest.
# Deve essere ripristinato in totale isolamento di rete.

# 1. Avviare il DC in DSRM
bcdedit /set safeboot dsrepair
Restart-Computer -Force

# 2. Restore System State
wbadmin start systemstaterecovery -version:05/20/2026-02:00 -backupTarget:E: -quiet

# 3. Al termine del restore, NON riavviare ancora.
# Decidere se serve authoritative restore di SYSVOL.

# 4. Se necessario authoritative restore del database AD:
ntdsutil "authoritative restore" "restore database" quit quit

# 5. Configurare SYSVOL come authoritative (DFSR D4) per il primo DC
# Vedi sezione "SYSVOL Restore — D2 e D4"

# 6. Impostare il DC come Global Catalog (se non lo era)
# Dopo il riavvio, da ADSI Edit o PowerShell:
Set-ADObject "CN=NTDS Settings,CN=DC01,CN=Servers,CN=SitoMain,CN=Sites,CN=Configuration,DC=contoso,DC=com" `
    -Replace @{"options" = 1}

# 7. Invalidare il pool RID corrente per prevenire duplicati
# Dopo il riavvio:
# Aumentare il valore di rIDAvailablePool nell'oggetto RID Manager
$ridManager = Get-ADObject "CN=RID Manager$,CN=System,DC=contoso,DC=com" -Properties rIDAvailablePool
# Il pool va invalidato per forzare nuova allocazione

# 8. Reset della password dell'account krbtgt (DUE VOLTE, con intervallo)
# Prima reset:
Set-ADAccountPassword -Identity krbtgt -Reset -NewPassword (
    ConvertTo-SecureString -AsPlainText (
        -join ((65..90)+(97..122)+(48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    ) -Force
)
# Attendere almeno 10 ore (tempo di vita massimo ticket TGT)
# Seconda reset:
# Ripetere il comando sopra

# 9. Rimuovere safeboot e riavviare
bcdedit /deletevalue safeboot
Restart-Computer -Force

# 10. Verificare che AD sia funzionante
dcdiag /v
repadmin /replsummary
nltest /dsgetdc:contoso.com
```

### Fase 3 — Pulizia dei Metadata

Dopo aver ripristinato il primo DC, tutti gli altri DC della forest sono "fantasmi" — i loro account macchina e oggetti NTDS Settings esistono in AD ma i server fisici potrebbero non esistere più.

```powershell
# Elencare tutti i DC noti alla forest
Get-ADDomainController -Filter * |
    Select-Object Name, HostName, IPv4Address, Site, IsGlobalCatalog

# Per ogni DC che NON verrà ripristinato dal backup,
# rimuovere i metadata con ntdsutil:
ntdsutil
  metadata cleanup
  connections
  connect to server DC01.contoso.com
  quit
  select operation target
  list domains
  select domain 0
  list sites
  select site 0
  list servers in site
  select server 1    # il DC da rimuovere
  quit
  remove selected server
  quit
  quit

# Alternativa PowerShell (più pulita):
# Rimuovere il server object
$dcToRemove = "DC02"
$serverObj = Get-ADObject -Filter "Name -eq '$dcToRemove'" `
    -SearchBase "CN=Sites,CN=Configuration,DC=contoso,DC=com" `
    -SearchScope Subtree
Remove-ADObject $serverObj -Recursive -Confirm:$false

# Rimuovere anche dal DNS
# Cancellare i record A, CNAME e SRV relativi al DC rimosso
$zone = "contoso.com"
Get-DnsServerResourceRecord -ZoneName $zone -Name $dcToRemove |
    Remove-DnsServerResourceRecord -ZoneName $zone -Force

# Cancellare i record _msdcs
Get-DnsServerResourceRecord -ZoneName "_msdcs.$zone" |
    Where-Object { $_.RecordData.DomainName -like "*$dcToRemove*" } |
    Remove-DnsServerResourceRecord -ZoneName "_msdcs.$zone" -Force

# Pulire i record SRV
foreach ($srv in @("_ldap._tcp", "_kerberos._tcp", "_gc._tcp", "_kpasswd._tcp")) {
    Get-DnsServerResourceRecord -ZoneName $zone -Name $srv -RRType SRV |
        Where-Object { $_.RecordData.DomainName -like "*$dcToRemove*" } |
        Remove-DnsServerResourceRecord -ZoneName $zone -Force
}
```

### Fase 4 — Seize dei Ruoli FSMO

Se i DC che detenevano i ruoli FSMO non sono recuperabili, i ruoli devono essere "seized" (forzatamente assunti) dal primo DC ripristinato.

```powershell
# Verificare chi detiene i ruoli FSMO attualmente
netdom query fsmo

# Seize di tutti i ruoli FSMO sul DC corrente
# Usare Move-ADDirectoryServerOperationMasterRole con -Force per il seize

# Seize Schema Master
Move-ADDirectoryServerOperationMasterRole -Identity "DC01" `
    -OperationMasterRole SchemaMaster -Force -Confirm:$false

# Seize Domain Naming Master
Move-ADDirectoryServerOperationMasterRole -Identity "DC01" `
    -OperationMasterRole DomainNamingMaster -Force -Confirm:$false

# Seize RID Master
Move-ADDirectoryServerOperationMasterRole -Identity "DC01" `
    -OperationMasterRole RIDMaster -Force -Confirm:$false

# Seize PDC Emulator
Move-ADDirectoryServerOperationMasterRole -Identity "DC01" `
    -OperationMasterRole PDCEmulator -Force -Confirm:$false

# Seize Infrastructure Master
Move-ADDirectoryServerOperationMasterRole -Identity "DC01" `
    -OperationMasterRole InfrastructureMaster -Force -Confirm:$false

# Seize di tutti i ruoli in un singolo comando
Move-ADDirectoryServerOperationMasterRole -Identity "DC01" `
    -OperationMasterRole SchemaMaster,DomainNamingMaster,RIDMaster,PDCEmulator,InfrastructureMaster `
    -Force -Confirm:$false

# Verificare
netdom query fsmo
Get-ADDomainController -Identity "DC01" | Select-Object OperationMasterRoles
```

### Fase 5 — Ripristino dei DC Aggiuntivi

Dopo aver validato il primo DC, i DC aggiuntivi vengono ricostruiti da zero e promossi contro il primo DC.

```powershell
# OPZIONE A: Promozione di un nuovo server come DC aggiuntivo
# (preferita — server pulito, nessun residuo di compromissione)

# 1. Installare il ruolo AD DS
Install-WindowsFeature AD-Domain-Services -IncludeManagementTools

# 2. Promuovere come DC aggiuntivo
Install-ADDSDomainController `
    -DomainName "contoso.com" `
    -SiteName "SitoMain" `
    -InstallDns:$true `
    -DatabasePath "C:\Windows\NTDS" `
    -LogPath "C:\Windows\NTDS" `
    -SysvolPath "C:\Windows\SYSVOL" `
    -ReplicationSourceDC "DC01.contoso.com" `
    -SafeModeAdministratorPassword (Read-Host -AsSecureString "Password DSRM") `
    -Force:$true

# OPZIONE B: Restore da backup di un secondo DC (se il backup è sicuro)
# Stessa procedura della Fase 2, ma con non-authoritative restore
# Il DC riceverà aggiornamenti dal primo DC via replica

# 3. Dopo la promozione, verificare la replica
repadmin /replsummary
repadmin /showrepl DC02

# 4. Verificare la salute del nuovo DC
dcdiag /s:DC02 /v

# 5. Se necessario, rendere il DC un Global Catalog
Set-ADObject "CN=NTDS Settings,CN=DC02,CN=Servers,CN=SitoMain,CN=Sites,CN=Configuration,DC=contoso,DC=com" `
    -Replace @{"options" = 1}
```

### Fase 6 — Ripristino di SYSVOL

SYSVOL contiene le Group Policy e gli script di logon. Il ripristino corretto è cruciale.

```powershell
# Per il PRIMO DC: DFSR D4 (authoritative)
# Per i DC AGGIUNTIVI: DFSR D2 (non-authoritative)
# Vedi sezione dedicata "SYSVOL Restore — D2 e D4" per i dettagli completi

# Verificare che SYSVOL sia condiviso
Get-SmbShare -Name SYSVOL -ErrorAction SilentlyContinue
Get-SmbShare -Name NETLOGON -ErrorAction SilentlyContinue

# Se SYSVOL non è condiviso, verificare DFSR
Get-WmiObject -Namespace "root\microsoftdfs" -Class DfsrReplicatedFolderInfo |
    Select-Object ReplicatedFolderName, State, CurrentStagePath
# State 4 = Normal, State 2 = Initial Sync

# Verificare che le GPO siano presenti
Get-ChildItem "C:\Windows\SYSVOL\sysvol\contoso.com\Policies" | Measure-Object
Get-GPO -All | Select-Object DisplayName, Id, ModificationTime | Format-Table -AutoSize
```

### Fase 7 — Validazione e Rientro in Produzione

```powershell
# Checklist di validazione COMPLETA prima del rientro in produzione

# 1. dcdiag su TUTTI i DC
$allDCs = Get-ADDomainController -Filter *
foreach ($dc in $allDCs) {
    Write-Host "=== dcdiag per $($dc.Name) ===" -ForegroundColor Cyan
    dcdiag /s:$($dc.HostName) /v
}

# 2. Verifica replica
repadmin /replsummary
repadmin /showrepl * /csv | ConvertFrom-Csv |
    Where-Object { $_."Number of Failures" -gt 0 } |
    Format-Table "Source DSA", "Naming Context", "Number of Failures", "Last Failure Status"

# 3. Verifica FSMO
netdom query fsmo

# 4. Verifica DNS
# Tutti i record SRV necessari devono esistere
$domain = "contoso.com"
foreach ($srv in @("_ldap._tcp.dc._msdcs.$domain", "_kerberos._tcp.dc._msdcs.$domain",
                   "_gc._tcp.$domain")) {
    $result = Resolve-DnsName -Name $srv -Type SRV -ErrorAction SilentlyContinue
    if ($result) {
        Write-Host "OK: $srv -> $($result.Count) record(s)" -ForegroundColor Green
    } else {
        Write-Host "FAIL: $srv -> nessun record" -ForegroundColor Red
    }
}

# 5. Verifica autenticazione
nltest /dsgetdc:contoso.com
nltest /sc_verify:contoso.com

# 6. Verifica SYSVOL
dcdiag /test:sysvolcheck /test:netlogons

# 7. Verifica GPO
Get-GPO -All | Measure-Object
gpresult /r /scope computer

# 8. Test login utente su un client
# Fare login manuale con un utente di test su un client domain-joined

# 9. Graduale rientro in produzione
# - Connettere prima i DC alla rete isolata di validazione
# - Poi connettere un subset di client per test
# - Infine aprire a tutti i client
```


---

## SYSVOL Restore — D2 e D4

### DFSR vs FRS — Determinare il Motore di Replica

```powershell
# Verificare se SYSVOL usa DFSR o FRS
# Metodo 1: controllare il servizio
Get-Service DFSR -ErrorAction SilentlyContinue | Select-Object Name, Status
Get-Service NtFrs -ErrorAction SilentlyContinue | Select-Object Name, Status
# Se DFSR è Running e NtFrs è Stopped → DFSR (buono, moderno)
# Se NtFrs è Running e DFSR è Stopped → FRS (legacy, migrare!)

# Metodo 2: controllare il livello di migrazione DFSR
dfsrmig /getglobalstate
# Global state: Eliminated → migrazione completata a DFSR
# Global state: Prepared/Redirected → migrazione in corso
# Se non esiste dfsrmig → ancora su FRS

# Metodo 3: controllare via LDAP
Get-ADObject "CN=DFSR-GlobalSettings,CN=System,DC=contoso,DC=com" -ErrorAction SilentlyContinue
# Se l'oggetto esiste → DFSR configurato

# Se ancora su FRS: pianificare URGENTEMENTE la migrazione a DFSR
# FRS è deprecato dal 2008 R2 e rimosso in Windows Server 2025
```

### DFSR D2 Restore (Non-Authoritative)

D2 (stato non-autoritativo) indica a DFSR di reinizializzare il database locale e scaricare il contenuto da un partner autoritativo.

```powershell
# D2 è usato per i DC AGGIUNTIVI durante forest recovery
# Il DC scaricherà SYSVOL dal DC che ha fatto D4

# 1. Fermare il servizio DFSR
Stop-Service DFSR

# 2. Impostare il flag D2 via ADSIEDIT o PowerShell
# Navigare a: CN=SYSVOL Subscription,CN=Domain System Volume,
#             CN=DFSR-LocalSettings,CN=DC02,CN=Servers,CN=SitoMain,
#             CN=Sites,CN=Configuration,DC=contoso,DC=com

$dn = "CN=SYSVOL Subscription,CN=Domain System Volume," +
      "CN=DFSR-LocalSettings,CN=DC02,CN=Servers,CN=SitoMain," +
      "CN=Sites,CN=Configuration,DC=contoso,DC=com"

# Impostare msDFSR-Enabled = FALSE
Set-ADObject $dn -Replace @{"msDFSR-Enabled" = $false}

# 3. Forzare replica AD per propagare il cambio
repadmin /syncall DC02 /APed

# 4. Riavviare il servizio DFSR
Start-Service DFSR

# 5. Attendere che DFSR registri l'evento 4114 nel log
#    "DFSR è stato disabilitato per il set di repliche"
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Id=4114} -MaxEvents 1

# 6. Reimpostare msDFSR-Enabled = TRUE
Set-ADObject $dn -Replace @{"msDFSR-Enabled" = $true}

# 7. Forzare replica
repadmin /syncall DC02 /APed

# 8. Riavviare DFSR
Restart-Service DFSR

# 9. Attendere evento 4602 "DFSR ha inizializzato il set di repliche"
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Id=4602} -MaxEvents 1

# 10. Verificare che SYSVOL sia condiviso
net share | Select-String "SYSVOL|NETLOGON"
```

### DFSR D4 Restore (Authoritative)

D4 (stato autoritativo) indica a DFSR che questo DC ha la copia "master" di SYSVOL. Tutti gli altri DC scaricheranno da qui.

```powershell
# D4 è usato per il PRIMO DC durante forest recovery
# Questo DC diventa la fonte autoritativa per SYSVOL

# 1. Fermare il servizio DFSR
Stop-Service DFSR

# 2. Impostare il flag D4 via PowerShell
$dn = "CN=SYSVOL Subscription,CN=Domain System Volume," +
      "CN=DFSR-LocalSettings,CN=DC01,CN=Servers,CN=SitoMain," +
      "CN=Sites,CN=Configuration,DC=contoso,DC=com"

# Impostare msDFSR-Enabled = FALSE
Set-ADObject $dn -Replace @{"msDFSR-Enabled" = $false}

# Impostare msDFSR-Options = 1 (flag autoritativo)
Set-ADObject $dn -Replace @{"msDFSR-Options" = 1}

# 3. Forzare replica AD
repadmin /syncall DC01 /APed

# 4. Riavviare DFSR
Start-Service DFSR

# 5. Attendere evento 4114
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Id=4114} -MaxEvents 1

# 6. Reimpostare msDFSR-Enabled = TRUE (msDFSR-Options rimane 1)
Set-ADObject $dn -Replace @{"msDFSR-Enabled" = $true}

# 7. Forzare replica AD
repadmin /syncall DC01 /APed

# 8. Riavviare DFSR
Restart-Service DFSR

# 9. Attendere evento 4602 (autoritativo completato)
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Id=4602} -MaxEvents 1

# 10. SYSVOL è ora autoritativo su questo DC
# Gli altri DC con D2 scaricheranno da qui
```

### FRS Restore (Legacy)

Per ambienti ancora su FRS (pre-migrazione DFSR):

```powershell
# Authoritative FRS restore (equivalente D4)
# 1. Fermare il servizio NtFrs
Stop-Service NtFrs

# 2. Impostare il flag nel registry
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NtFrs\Parameters\Backup/Restore\Process at Startup" `
    -Name "BurFlags" -Value 0xD4 -Type DWord
# D4 = autoritativo (il DC è la fonte)
# D2 = non-autoritativo (il DC scarica dagli altri)

# 3. Riavviare NtFrs
Start-Service NtFrs

# 4. Verificare che il flag sia stato consumato (torna a 0)
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NtFrs\Parameters\Backup/Restore\Process at Startup" `
    -Name "BurFlags"
# Deve essere 0 dopo il restart

# 5. Controllare il log eventi di File Replication Service
Get-WinEvent -FilterHashtable @{LogName='File Replication Service'; Level=4} -MaxEvents 10
```

### Verifica Post-Restore SYSVOL

```powershell
# 1. Verificare che SYSVOL e NETLOGON siano condivisi su tutti i DC
$allDCs = Get-ADDomainController -Filter *
foreach ($dc in $allDCs) {
    $shares = Invoke-Command -ComputerName $dc.HostName -ScriptBlock {
        Get-SmbShare | Where-Object { $_.Name -in @('SYSVOL','NETLOGON') }
    }
    [PSCustomObject]@{
        DC = $dc.Name
        SYSVOL = ($shares | Where-Object Name -eq 'SYSVOL').Path
        NETLOGON = ($shares | Where-Object Name -eq 'NETLOGON').Path
    }
} | Format-Table -AutoSize

# 2. Confrontare il contenuto delle GPO tra DC
$refernceDC = "DC01"
$refPolicies = Get-ChildItem "\\$refernceDC\SYSVOL\contoso.com\Policies" -Directory
foreach ($dc in $allDCs | Where-Object Name -ne $refernceDC) {
    $dcPolicies = Get-ChildItem "\\$($dc.HostName)\SYSVOL\contoso.com\Policies" -Directory
    $diff = Compare-Object $refPolicies.Name $dcPolicies.Name
    if ($diff) {
        Write-Warning "$($dc.Name): differenze trovate in SYSVOL"
        $diff | Format-Table
    } else {
        Write-Host "$($dc.Name): SYSVOL sincronizzato" -ForegroundColor Green
    }
}

# 3. dcdiag specifico per SYSVOL
dcdiag /test:sysvolcheck
dcdiag /test:netlogons
```


---

## DFSR Recovery Avanzata

### DFSR Database Corruption

```powershell
# Sintomi: eventi 2104, 2004, 1202 nel log DFS Replication
# Il database DFSR è corrotto e la replica è bloccata

# 1. Identificare il problema
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Level=1,2} -MaxEvents 20 |
    Select-Object TimeCreated, Id, Message | Format-List

# 2. Fermare DFSR
Stop-Service DFSR

# 3. Cancellare il database DFSR (verrà ricostruito)
$dfsrDB = "$env:SystemRoot\System Volume Information\DFSR"
# ATTENZIONE: verificare il percorso prima di cancellare
Get-ChildItem $dfsrDB -Recurse | Select-Object FullName
Remove-Item "$dfsrDB\*" -Recurse -Force

# 4. Riavviare DFSR — ricostruirà il database
Start-Service DFSR

# 5. Monitorare la ricostruzione
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Id=4602,4604} -MaxEvents 5

# NOTA: durante la ricostruzione, SYSVOL potrebbe non essere condiviso.
# I client che dipendono da questo DC per GPO non riceveranno policy.
```

### DFSR Conflitti e Pre-Staging

```powershell
# DFSR gestisce i conflitti con "last writer wins"
# I file in conflitto vanno nella cartella ConflictAndDeleted

# Verificare i conflitti
Get-DfsrBacklog -GroupName "Domain System Volume" -SourceComputerName DC01 -DestinationComputerName DC02

# Controllare la dimensione della cartella ConflictAndDeleted
$conflictPath = "$env:SystemRoot\System Volume Information\DFSR\Private\ConflictAndDeleted"
if (Test-Path $conflictPath) {
    Get-ChildItem $conflictPath -Recurse | Measure-Object -Property Length -Sum |
        Select-Object Count, @{N='SizeMB';E={[math]::Round($_.Sum/1MB,2)}}
}

# Verificare la dimensione della staging area
Get-DfsrMembership -GroupName "Domain System Volume" -ComputerName $env:COMPUTERNAME |
    Select-Object GroupName, FolderName, StagingPathUNC, StagingPath,
        @{N='StagingQuotaMB';E={$_.StagingSizeInMb}}
```

### Ripristino DFSR dopo Journal Wrap

Un journal wrap si verifica quando il journal USN di NTFS si riempie e le voci più vecchie vengono sovrascritte prima che DFSR le abbia lette.

```powershell
# Evento 2213: Journal wrap detected
# Il DC non può replicare finché il problema non è risolto

# 1. Verificare l'evento
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Id=2213} -MaxEvents 1

# 2. Se il DC ha una copia completa e consistente di SYSVOL,
#    abilitare il recovery automatico via registry:
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\DFSR\Parameters" `
    -Name "StopReplicationOnAutoRecovery" -Value 0 -Type DWord

# 3. Riavviare DFSR
Restart-Service DFSR

# 4. Se il recovery automatico non funziona, eseguire un D2 restore
# (procedura completa nella sezione D2 sopra)

# 5. Dopo il recovery, verificare
Get-DfsrBacklog -GroupName "Domain System Volume" -SourceComputerName DC01 -DestinationComputerName $env:COMPUTERNAME
```


---

## DNS Integrated Zones Recovery

### AD-Integrated DNS — Come Funziona

Le zone DNS AD-integrated sono memorizzate dentro il database AD (NTDS.DIT) in partizioni dedicate:

```
Database AD (NTDS.DIT)
├── DomainDnsZones (DC=DomainDnsZones,DC=contoso,DC=com)
│   └── contoso.com zone data
│   └── _msdcs.contoso.com zone data
└── ForestDnsZones (DC=ForestDnsZones,DC=contoso,DC=com)
    └── _msdcs.<forest root> zone data
```

**Vantaggi delle zone AD-integrated:**
- Replica multi-master (ogni DC con DNS può scrivere)
- Sicurezza integrata (DACL su ogni record)
- Nessun zone transfer (usa replica AD)
- Recovery automatico con System State restore

### Backup delle Zone DNS

```powershell
# Le zone AD-integrated sono incluse nel System State backup.
# Per backup aggiuntivo, esportare le zone in file:

# Esportare tutte le zone in file .dns
$zones = Get-DnsServerZone | Where-Object { $_.ZoneType -ne 'Forwarder' }
$backupPath = "E:\DNS-Backup\$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Path $backupPath -Force

foreach ($zone in $zones) {
    # Export della zona
    Export-DnsServerZone -Name $zone.ZoneName -FileName "$($zone.ZoneName).dns.bak"
    # Il file viene creato in %SystemRoot%\System32\dns\
    $sourceFile = "$env:SystemRoot\System32\dns\$($zone.ZoneName).dns.bak"
    Copy-Item $sourceFile $backupPath -Force
    Write-Host "Esportata zona: $($zone.ZoneName)"
}

# Esportare anche la configurazione del server DNS
$dnsConfig = Get-DnsServer
$dnsConfig | Export-Clixml "$backupPath\DnsServerConfig.xml"

# Esportare i forwarder
Get-DnsServerForwarder | Export-Clixml "$backupPath\DnsForwarders.xml"

# Esportare i conditional forwarder
Get-DnsServerZone | Where-Object { $_.ZoneType -eq 'Forwarder' } |
    Export-Clixml "$backupPath\ConditionalForwarders.xml"
```

### Ripristino Zone DNS

```powershell
# Scenario 1: Zone DNS corrotte, AD funzionante
# Le zone AD-integrated si ripristinano con il System State
# Se solo DNS è corrotto, forzare una replica completa:
repadmin /syncall /APed

# Verificare che le partizioni DNS siano replicate
repadmin /showrepl | Select-String "DomainDnsZones|ForestDnsZones"

# Scenario 2: Ricostruzione DNS da file di export
# Ricreare la zona (cancellare la corrotta prima se esiste)
Add-DnsServerPrimaryZone -Name "contoso.com" `
    -ReplicationScope "Domain" `
    -LoadExisting `
    -ZoneFile "contoso.com.dns.bak"

# Scenario 3: Ripristino record specifici
# Importare record da file di zona
# Copiare il file .dns.bak in %SystemRoot%\System32\dns\
# Poi usare dnscmd:
dnscmd /zoneload contoso.com

# Ripristinare forwarders
$forwarders = Import-Clixml "E:\DNS-Backup\20260522\DnsForwarders.xml"
Set-DnsServerForwarder -IPAddress $forwarders.IPAddress

# Verificare la risoluzione dopo il ripristino
Resolve-DnsName -Name "contoso.com" -Type SOA -DnsOnly
Resolve-DnsName -Name "_ldap._tcp.dc._msdcs.contoso.com" -Type SRV -DnsOnly
nslookup -type=SRV _ldap._tcp.dc._msdcs.contoso.com
```

### Pulizia Record Stale dopo DR

Dopo un disaster recovery, molti record DNS potrebbero puntare a DC o server che non esistono più.

```powershell
# Abilitare lo scavenging (pulizia automatica record stale)
# Sul server DNS:
Set-DnsServerScavenging -ScavengingState $true `
    -RefreshInterval (New-TimeSpan -Days 7) `
    -NoRefreshInterval (New-TimeSpan -Days 7) `
    -ScavengingInterval (New-TimeSpan -Days 7)

# Abilitare aging per la zona specifica
Set-DnsServerZoneAging -Name "contoso.com" -Aging $true `
    -RefreshInterval (New-TimeSpan -Days 7) `
    -NoRefreshInterval (New-TimeSpan -Days 7)

# Forzare uno scavenging immediato
Start-DnsServerScavenging -Force

# Trovare record stale manualmente
Get-DnsServerResourceRecord -ZoneName "contoso.com" -RRType A |
    Where-Object { $_.Timestamp -and $_.Timestamp -lt (Get-Date).AddDays(-30) } |
    Select-Object HostName, RecordType, Timestamp, @{N='IP';E={$_.RecordData.IPv4Address}}

# Eliminare record di DC rimossi
$removedDCs = @("DC02", "DC03")
foreach ($dc in $removedDCs) {
    Get-DnsServerResourceRecord -ZoneName "contoso.com" -Name $dc -ErrorAction SilentlyContinue |
        Remove-DnsServerResourceRecord -ZoneName "contoso.com" -Force
}

# Registrare nuovamente i record DNS corretti su ogni DC attivo
# Eseguire su ciascun DC:
ipconfig /registerdns
nltest /dsregdns
# O forzare la registrazione completa:
net stop netlogon && net start netlogon
```

### Conditional Forwarders e Stub Zones

```powershell
# Dopo forest recovery, verificare che conditional forwarders siano intatti
Get-DnsServerZone | Where-Object ZoneType -eq 'Forwarder' |
    Select-Object ZoneName, MasterServers, ReplicationScope

# Se mancanti, ricreare
Add-DnsServerConditionalForwarderZone -Name "partner.com" `
    -MasterServers "10.20.30.40","10.20.30.41" `
    -ReplicationScope "Forest"

# Verificare stub zones
Get-DnsServerZone | Where-Object ZoneType -eq 'Stub' |
    Select-Object ZoneName, MasterServers

# Ricreare stub zones se necessario
Add-DnsServerStubZone -Name "subsidiary.contoso.com" `
    -MasterServers "10.50.0.10" `
    -ReplicationScope "Forest"
```


---

## PKI Disaster Recovery

### Architettura PKI e Componenti Critici

```
Architettura PKI Tipica Enterprise
                                                    
  ┌──────────────────┐                              
  │  ROOT CA          │  OFFLINE, air-gapped        
  │  (Stand-alone)    │  Accesa solo per:            
  │                   │  - Rinnovare SubCA cert      
  │  Chiave privata:  │  - Pubblicare CRL root       
  │  HSM o export     │  - Audit annuale              
  └────────┬─────────┘                               
           │ Firma                                    
           ↓                                          
  ┌──────────────────┐     ┌──────────────────┐       
  │  ISSUING CA 1     │     │  ISSUING CA 2     │      
  │  (Enterprise)     │     │  (Enterprise)     │      
  │                   │     │                   │      
  │  AD-integrated    │     │  AD-integrated    │      
  │  Templates        │     │  Templates        │      
  │  Auto-enrollment  │     │  Auto-enrollment  │      
  └────────┬─────────┘     └────────┬─────────┘      
           │                        │                  
           ↓                        ↓                  
  ┌──────────────────────────────────────────────┐    
  │  CDP / AIA / OCSP                             │    
  │  - CRL Distribution Points (HTTP, LDAP)       │    
  │  - Authority Information Access               │    
  │  - OCSP Responders                            │    
  └──────────────────────────────────────────────┘    
```

**Componenti critici da proteggere:**

| Componente | Percorso | Criticità | Backup method |
|---|---|---|---|
| CA Private Key | Software store o HSM | MASSIMA | certutil -backupkey o HSM export |
| CA Certificate | AD NTAuthCertificates | Alta | certutil -ca.cert |
| CA Database | `%SystemRoot%\CertLog\` | Alta | certutil -backupdb |
| CA Registry config | HKLM\SYSTEM\CCS\Services\CertSvc | Media | reg export |
| Certificate Templates | AD Configuration partition | Media | Con System State |
| CRL files | CDP locations (HTTP/LDAP) | Alta | Copy-Item |
| OCSP config | OCSP server | Media | Export configurazione |

### Backup della CA — Chiave Privata e Database

```powershell
# ========================================================
# BACKUP COMPLETO DELLA CA — Eseguire su ogni CA server
# ========================================================

$backupPath = "E:\CA-Backup\$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Path $backupPath -Force

# 1. Backup della chiave privata e certificato CA
# Richiede una password per proteggere il file PFX
certutil -backupkey $backupPath
# Verrà richiesta una password — usare password complessa (20+ char)
# Output: .p12 file contenente chiave privata + cert chain

# 2. Backup del database CA
certutil -backupdb $backupPath
# Crea i file:
# - DataBase\ (cartella con .edb + log)
# - edb*.log (transaction log)

# 3. Backup del certificato CA (senza chiave privata)
certutil -ca.cert "$backupPath\CA-Certificate.cer"

# 4. Backup della configurazione registry
reg export "HKLM\SYSTEM\CurrentControlSet\Services\CertSvc" "$backupPath\CertSvc-Registry.reg" /y

# 5. Backup della configurazione CA
certutil -getreg CA > "$backupPath\CA-Configuration.txt"

# 6. Backup dei template pubblicati
certutil -catemplates > "$backupPath\CA-Templates.txt"

# 7. Esportare l'elenco dei certificati emessi (per audit)
certutil -view -out "RequestId,CommonName,NotBefore,NotAfter,SerialNumber,CertificateTemplate" `
    csv > "$backupPath\IssuedCertificates.csv"

# 8. Backup della CRL corrente
$crlPath = "$env:SystemRoot\System32\CertSrv\CertEnroll"
Copy-Item "$crlPath\*.crl" $backupPath -Force
Copy-Item "$crlPath\*.crt" $backupPath -Force

# 9. Verificare il backup
certutil -verifystore MY
Write-Host "Backup completato in: $backupPath"
Get-ChildItem $backupPath -Recurse | Select-Object Name, Length, LastWriteTime

# IMPORTANTE: conservare il backup in luogo sicuro
# - La chiave privata della CA è il segreto più critico dell'infrastruttura PKI
# - Cifrare il backup con BitLocker o strumento enterprise
# - Conservare offline (USB in cassaforte o vault)
# - Rotare la password del PFX ogni 90 giorni
```

### Restore della CA su Nuovo Server

```powershell
# ========================================================
# RESTORE DELLA CA SU NUOVO SERVER
# ========================================================

# Prerequisiti:
# - Windows Server con stesso OS version (o superiore)
# - Nome server IDENTICO alla CA originale (o rinomina post-install)
# - Membro del dominio corretto
# - Ruolo AD CS installato ma NON configurato

# 1. Installare il ruolo AD CS
Install-WindowsFeature ADCS-Cert-Authority -IncludeManagementTools

# 2. Ripristinare la chiave privata della CA
# Importare il file .p12 nello store della macchina
certutil -restorekey "E:\CA-Backup\20260522\CA-Key.p12"
# Verrà richiesta la password usata durante il backup

# 3. Configurare la CA con la chiave esistente
# Per Enterprise Subordinate CA:
Install-AdcsCertificationAuthority `
    -CAType EnterpriseSubordinateCA `
    -CertFile "E:\CA-Backup\20260522\CA-Certificate.cer" `
    -CACommonName "Contoso Issuing CA 01" `
    -KeyContainerName "Contoso Issuing CA 01" `
    -DatabaseDirectory "C:\Windows\System32\CertLog" `
    -LogDirectory "C:\Windows\System32\CertLog" `
    -Force

# 4. Fermare il servizio CA prima del restore del database
Stop-Service CertSvc

# 5. Ripristinare il database CA
certutil -restoredb "E:\CA-Backup\20260522"

# 6. Ripristinare la configurazione registry
reg import "E:\CA-Backup\20260522\CertSvc-Registry.reg"

# 7. Avviare il servizio CA
Start-Service CertSvc

# 8. Verificare la CA
certutil -ping
certutil -CRL  # Pubblica una nuova CRL
certutil -getreg CA\CAServerName
certutil -verifystore MY

# 9. Pubblicare il certificato CA e CRL in AD
certutil -dspublish -f "E:\CA-Backup\20260522\CA-Certificate.cer" SubCA
certutil -dspublish -f "E:\CA-Backup\20260522\CA-Certificate.cer" NTAuthCA

# 10. Verificare che i client possano raggiungere la CRL
certutil -verify -urlfetch "E:\CA-Backup\20260522\CA-Certificate.cer"
```

### CRL Availability durante Outage

Se la CA è down, i client non possono ottenere nuove CRL. Se le CRL scadono, TUTTI i certificati emessi dalla CA verranno considerati non validi.

```powershell
# Verificare la scadenza della CRL corrente
certutil -URL "http://pki.contoso.com/CertEnroll/Contoso-CA.crl"

# Controllare la CRL via PowerShell
$crlUrl = "http://pki.contoso.com/CertEnroll/Contoso-CA.crl"
$webClient = New-Object System.Net.WebClient
$crlBytes = $webClient.DownloadData($crlUrl)
$crl = New-Object System.Security.Cryptography.X509Certificates.X509Crl
# Analizzare con certutil
$tempFile = "$env:TEMP\current.crl"
[System.IO.File]::WriteAllBytes($tempFile, $crlBytes)
certutil -dump $tempFile | Select-String "Next Update|This Update"

# STRATEGIA DI MITIGAZIONE: CRL con validità estesa
# Configurare la CA per pubblicare CRL con overlap più lungo
certutil -setreg CA\CRLPeriodUnits 2
certutil -setreg CA\CRLPeriod "Weeks"
certutil -setreg CA\CRLOverlapUnits 3
certutil -setreg CA\CRLOverlapPeriod "Days"
certutil -setreg CA\CRLDeltaPeriodUnits 1
certutil -setreg CA\CRLDeltaPeriod "Days"
Restart-Service CertSvc

# STRATEGIA DI MITIGAZIONE: CDP multipli
# Configurare almeno 2 CDP (HTTP) su server diversi
# Se la CA è down, i CDP restano raggiungibili se ospitati altrove
# Pubblicare manualmente la CRL su CDP secondari:
Copy-Item "C:\Windows\System32\CertSrv\CertEnroll\*.crl" "\\web-pki\wwwroot\CertEnroll\" -Force

# STRATEGIA DI MITIGAZIONE: OCSP
# OCSP è meno impattato di CRL perché ha cache propria
# Se la CA torna online, OCSP riprende automaticamente

# Calcolo tempo critico:
# Se CRL Period = 1 settimana e Overlap = 3 giorni,
# hai 7 + 3 = 10 giorni max prima che le CRL scadano.
# La CA DEVE tornare online entro questo periodo.
```

### OCSP Responder Recovery

```powershell
# Installare OCSP Responder (se il server OCSP è distrutto)
Install-WindowsFeature ADCS-Online-Cert -IncludeManagementTools

# Configurare OCSP per la CA ripristinata
# 1. Aprire Online Responder Management (certsrv.msc)
# 2. Aggiungere una Revocation Configuration
# 3. Puntare al certificato della CA ripristinata

# Verificare OCSP
certutil -URL "http://ocsp.contoso.com/ocsp"

# Forzare aggiornamento della signing key OCSP
# Se la CA è stata ripristinata con nuova chiave, OCSP deve ottenere nuovo cert
certutil -pulse

# Monitorare lo stato OCSP
Get-OCSPRevocationConfiguration | Select-Object Identity, Status, CAServerName
```

### Root CA Offline — Procedure di Recovery

```powershell
# La Root CA offline è il componente PIÙ critico della PKI.
# Se la chiave privata è compromessa o persa, l'INTERA PKI è compromessa.

# ========================================================
# PROCEDURA DI RECOVERY ROOT CA OFFLINE
# ========================================================

# Prerequisiti:
# - Backup della chiave privata (PFX/P12) conservato in cassaforte
# - CD/USB con backup verificato
# - Server standalone (NON domain-joined)
# - Nessuna connessione di rete (air-gapped)

# 1. Installare Windows Server su hardware pulito
# 2. NON unire al dominio (Root CA è standalone)

# 3. Installare il ruolo CA
Install-WindowsFeature ADCS-Cert-Authority -IncludeManagementTools

# 4. Ripristinare la chiave privata
certutil -restorekey "D:\RootCA-Backup\RootCA.p12"

# 5. Configurare come Standalone Root CA con chiave esistente
Install-AdcsCertificationAuthority `
    -CAType StandaloneRootCA `
    -CACommonName "Contoso Root CA" `
    -KeyContainerName "Contoso Root CA" `
    -HashAlgorithmName SHA256 `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -ValidityPeriod Years `
    -ValidityPeriodUnits 20 `
    -Force

# 6. Ripristinare il database
Stop-Service CertSvc
certutil -restoredb "D:\RootCA-Backup"
Start-Service CertSvc

# 7. Pubblicare una nuova CRL
certutil -CRL

# 8. Esportare la CRL su USB per trasferirla ai CDP
# Copiare *.crl da C:\Windows\System32\CertSrv\CertEnroll\ su USB

# 9. Spegnere la Root CA e metterla in sicurezza
# La Root CA deve restare offline fino alla prossima operazione necessaria
```

### Subordinate CA Recovery

```powershell
# Se una Subordinate (Issuing) CA è distrutta e serve un nuovo certificato
# dalla Root CA:

# 1. Sul nuovo server Issuing CA, generare una CSR
certreq -new "C:\CAConfig\SubCA.inf" "C:\CAConfig\SubCA.req"

# Contenuto di SubCA.inf:
# [NewRequest]
# Subject = "CN=Contoso Issuing CA 01,DC=contoso,DC=com"
# KeySpec = 1
# KeyLength = 4096
# HashAlgorithm = SHA256
# Exportable = TRUE
# MachineKeySet = TRUE
# SMIME = FALSE
# PrivateKeyArchive = FALSE
# UserProtected = FALSE
# UseExistingKeySet = FALSE
# ProviderName = "RSA#Microsoft Software Key Storage Provider"
# ProviderType = 12
# RequestType = PKCS10

# 2. Portare la CSR alla Root CA offline (via USB)

# 3. Sulla Root CA, firmare la richiesta
certreq -submit -config "RootCA\Contoso Root CA" "C:\Requests\SubCA.req"
# Approvare nella console certsrv.msc

# 4. Esportare il certificato firmato
certreq -retrieve -config "RootCA\Contoso Root CA" <RequestID> "C:\Requests\SubCA.cer"

# 5. Trasferire il certificato firmato al nuovo Issuing CA server (via USB)

# 6. Sul nuovo Issuing CA, installare il certificato
certutil -installcert "C:\CAConfig\SubCA.cer"
Start-Service CertSvc

# 7. Pubblicare in AD
certutil -dspublish -f "C:\CAConfig\SubCA.cer" SubCA
certutil -dspublish -f "C:\CAConfig\SubCA.cer" NTAuthCA
```

### Re-issue dopo Compromissione della CA

Se la chiave privata della CA è compromessa, **tutti i certificati emessi dalla CA sono potenzialmente compromessi.**

```powershell
# ========================================================
# PROCEDURA DI RE-ISSUE DOPO COMPROMISSIONE CA
# ========================================================

# 1. REVOCARE il certificato della CA compromessa
# Sulla Root CA (se compromissione è della Subordinate CA):
certutil -revoke <SerialNumberSubCA> 1  # 1 = Key Compromise
certutil -CRL  # Pubblicare CRL aggiornata con la revoca

# 2. Pubblicare la CRL della Root CA su tutti i CDP
# (procedura manuale per Root CA offline)

# 3. Costruire una NUOVA Subordinate CA
# - Nuovo server
# - Nuova chiave privata
# - Nuovo certificato dalla Root CA

# 4. Revocare TUTTI i certificati emessi dalla CA compromessa
# Esportare la lista:
certutil -view -restrict "Disposition=20" -out "SerialNumber,CommonName" csv > revoke-list.csv
# Revocare in blocco:
$certs = Import-Csv revoke-list.csv
foreach ($cert in $certs) {
    certutil -revoke $cert.SerialNumber 1
}
certutil -CRL

# 5. Re-emettere i certificati dalla nuova CA
# Per auto-enrollment: le GPO forzeranno il re-enrollment automatico
# Per certificati manuali: notificare gli owner e re-emettere

# 6. Rimuovere il certificato della vecchia CA da NTAuthCertificates
certutil -viewdelstore "ldap:///CN=NTAuthCertificates,CN=Public Key Services,CN=Services,CN=Configuration,DC=contoso,DC=com?cACertificate"

# 7. Verificare che nessun client usi ancora la vecchia CA
Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.Issuer -like "*VecchiaCA*" }
```

### Certificate Template Recovery

```powershell
# I template sono oggetti AD nella partizione Configuration.
# Se distrutti, si ripristinano con il System State restore.

# Verificare i template correnti
Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=contoso,DC=com" `
    -Filter * -Properties displayName |
    Select-Object Name, displayName

# Esportare template per backup (LDIFDE)
ldifde -f "E:\PKI-Backup\templates.ldf" `
    -d "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=contoso,DC=com" `
    -p subtree

# Importare template da backup
ldifde -i -f "E:\PKI-Backup\templates.ldf"

# Verificare i template pubblicati sulla CA
certutil -catemplates

# Ripubblicare template sulla CA se mancanti
certutil -setcatemplates +WebServer,User,Computer,DomainController
```


---

## Cross-Forest Trust Recovery

### Trust Relationship Fundamentals

```powershell
# Verificare le trust relationship correnti
Get-ADTrust -Filter * |
    Select-Object Name, Direction, TrustType, ForestTransitive, SelectiveAuthentication

# Dettagli trust
nltest /domain_trusts /all_trusts /v

# Tipi di trust:
# - Forest trust: bidirezionale tra due forest (richiede forest functional level 2003+)
# - External trust: tra due domini specifici
# - Shortcut trust: accelera l'autenticazione tra domini nella stessa forest
# - Realm trust: con Kerberos realm non-Windows
```

### Ripristino Trust dopo Forest Recovery

Dopo una forest recovery, le trust con altre forest/domini devono essere ricreate perché le password delle trust vengono invalidate.

```powershell
# 1. Verificare lo stato delle trust esistenti
nltest /sc_verify:partner.com
# Se fallisce: la trust è rotta

# 2. Reset della password della trust
netdom trust contoso.com /domain:partner.com /resetOnTgt /passwordT:NuovaPassword123!
# Eseguire anche dall'altro lato:
netdom trust partner.com /domain:contoso.com /resetOnSrc /passwordT:NuovaPassword123!

# 3. Se il reset non funziona, ricreare la trust da zero
# Prima, rimuovere la trust esistente
Remove-ADObject -Identity "CN=partner.com,CN=System,DC=contoso,DC=com" -Confirm:$false

# Poi ricreare:
# Lato contoso.com (outgoing):
netdom trust contoso.com /domain:partner.com `
    /add /twoway `
    /passwordT:TrustPassword! `
    /UserO:contoso\Administrator /PasswordO:* `
    /UserD:partner\Administrator /PasswordD:*

# 4. Se forest trust con selective authentication:
Set-ADObject "CN=partner.com,CN=System,DC=contoso,DC=com" `
    -Replace @{trustAttributes = 0x408}  # Forest + Selective Authentication

# 5. Verificare la trust
nltest /sc_verify:partner.com
Get-ADTrust -Identity "partner.com" | Select-Object *
Test-ComputerSecureChannel -Server "DC01.partner.com"
```

### Selective Authentication dopo Recovery

```powershell
# Se la trust usa Selective Authentication, verificare che i permessi
# "Allowed to Authenticate" siano corretti dopo il recovery

# Controllare chi ha il permesso "Allowed to Authenticate"
# su risorse nel dominio locale per utenti del dominio trusted:
Get-ADComputer -Filter * -Properties "msDS-AllowedToActOnBehalfOfOtherIdentity" |
    Where-Object { $_."msDS-AllowedToActOnBehalfOfOtherIdentity" } |
    Select-Object Name, "msDS-AllowedToActOnBehalfOfOtherIdentity"

# Assegnare permesso "Allowed to Authenticate" su un server specifico
# per un gruppo del dominio trusted
$serverIdentity = Get-ADComputer "FileServer01"
$trustedGroup = New-Object System.Security.Principal.SecurityIdentifier "S-1-5-21-...-1234"
# Usare dsacls o ADSI per assegnare il permesso
dsacls "CN=FileServer01,OU=Servers,DC=contoso,DC=com" /G "${trustedGroup}:CA;Allowed to Authenticate"
```

### Verifica Trust Post-Recovery

```powershell
# Script completo di verifica trust
$trusts = Get-ADTrust -Filter *
foreach ($trust in $trusts) {
    Write-Host "`n=== Trust: $($trust.Name) ===" -ForegroundColor Cyan
    
    # Stato canale sicuro
    $scStatus = nltest /sc_verify:$($trust.Name) 2>&1
    Write-Host "Secure Channel: $scStatus"
    
    # Direzione
    Write-Host "Direction: $($trust.Direction)"
    Write-Host "Type: $($trust.TrustType)"
    Write-Host "Forest Transitive: $($trust.ForestTransitive)"
    Write-Host "Selective Auth: $($trust.SelectiveAuthentication)"
    
    # Test DNS
    $dnsResult = Resolve-DnsName -Name $trust.Name -Type NS -ErrorAction SilentlyContinue
    if ($dnsResult) {
        Write-Host "DNS: OK" -ForegroundColor Green
    } else {
        Write-Host "DNS: FAIL" -ForegroundColor Red
    }
    
    # Test Kerberos
    $kerb = klist get krbtgt/$($trust.Name) 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Kerberos: OK" -ForegroundColor Green
    } else {
        Write-Host "Kerberos: FAIL" -ForegroundColor Red
    }
}
```


---

## Azure AD Connect Disaster Recovery

### Architettura AADConnect e Componenti

```
┌─────────────────┐         ┌─────────────────┐
│  Active          │  Sync   │  Microsoft       │
│  Directory       │ ──────→ │  Entra ID        │
│  On-Premises     │         │  (Azure AD)      │
│                  │         │                  │
│  DC01, DC02...   │         │  tenant.         │
│                  │         │  onmicrosoft.com │
└────────┬────────┘         └─────────────────┘
         │                          ↑
         │                          │
         ↓                          │
┌────────────────┐   Sync every    │
│  AADConnect     │   30 min ──────┘
│  Server         │
│                 │   Componenti:
│  - Sync Engine  │   - SQL LocalDB o full SQL
│  - Connector    │   - Password Hash Sync (PHS)
│  - Rules Engine │   - Pass-through Auth (PTA)
│  - Scheduler    │   - Federation (ADFS)
│                 │
│  STAGING Server │ ← Hot standby (read-only sync)
│  (opzionale)    │
└────────────────┘
```

### Backup di AADConnect

```powershell
# AADConnect non ha un meccanismo di backup nativo robusto.
# La strategia è: configurazione esportabile + staging server.

# 1. Esportare la configurazione AADConnect
# (disponibile da AADConnect 1.5.42.0+)
# Aprire PowerShell come admin sul server AADConnect:
Import-Module ADSync
Get-ADSyncServerConfiguration -Path "E:\AADConnect-Backup\$(Get-Date -Format 'yyyyMMdd')"

# 2. Documentare le sync rules custom
Get-ADSyncRule | Where-Object { $_.ImmutableTag -eq $null } |
    Select-Object Name, Direction, Connector, LinkType, Precedence |
    Export-Csv "E:\AADConnect-Backup\CustomSyncRules.csv" -NoTypeInformation

# 3. Esportare le sync rules in dettaglio
Get-ADSyncRule | Where-Object { $_.ImmutableTag -eq $null } |
    ForEach-Object {
        $_ | ConvertTo-Json -Depth 5 | Out-File "E:\AADConnect-Backup\Rule_$($_.Name -replace '[^\w]','_').json"
    }

# 4. Documentare i connector spaces
Get-ADSyncConnector | Select-Object Name, Type, ConnectorTypeName |
    Export-Csv "E:\AADConnect-Backup\Connectors.csv" -NoTypeInformation

# 5. Esportare la configurazione del scheduler
Get-ADSyncScheduler | Export-Clixml "E:\AADConnect-Backup\SchedulerConfig.xml"

# 6. Backup del database AADConnect (SQL LocalDB)
# Il database è in: C:\Program Files\Microsoft Azure AD Sync\Data\
# Fare backup file-level (fermare il servizio prima):
Stop-Service ADSync
Copy-Item "C:\Program Files\Microsoft Azure AD Sync\Data\*" "E:\AADConnect-Backup\Database\" -Recurse -Force
Start-Service ADSync
```

### Staging Server come DR Strategy

Lo staging server è la strategia DR raccomandata da Microsoft per AADConnect.

```powershell
# Lo staging server esegue le stesse sync rules ma NON scrive in Entra ID.
# In caso di disastro, si promuove a server attivo.

# Installare AADConnect su un secondo server con le stesse impostazioni
# ma selezionare "Enable staging mode" durante il wizard

# Verificare che lo staging server sia sincronizzato
Get-ADSyncScheduler
# StagingModeEnabled dovrebbe essere True

# PROMOZIONE dello staging server (quando il primario è down):

# 1. Sul server di staging, disabilitare staging mode:
Set-ADSyncScheduler -StagingModeEnabled $false

# 2. Forzare un ciclo di sync completo
Start-ADSyncSyncCycle -PolicyType Initial

# 3. Verificare che il sync funzioni
Get-ADSyncScheduler
Get-ADSyncConnectorRunStatus

# 4. Se il vecchio server torna online, metterlo in staging mode:
# Sul VECCHIO server:
Set-ADSyncScheduler -StagingModeEnabled $true

# ATTENZIONE: non possono MAI esserci DUE server attivi contemporaneamente.
# Due server attivi = conflitti di scrittura in Entra ID.
```

### Rebuild AADConnect da Zero

Se non c'è staging server e il server AADConnect è perso:

```powershell
# 1. Installare AADConnect su un nuovo server
# Scaricare l'installer da https://www.microsoft.com/en-us/download/details.aspx?id=47594

# 2. Durante il wizard, selezionare "Customize"
# 3. Configurare con le stesse opzioni della installazione originale
#    (per questo serve la documentazione della configurazione!)

# 4. Se la configurazione precedente era esportata:
# Importare la configurazione
# L'import è possibile solo durante una nuova installazione via wizard

# 5. Dopo l'installazione, importare le sync rules custom
# Se esportate in JSON, ricrearle manualmente
# O usare il modulo ADSync per ricrearle via script

# 6. Forzare sync completo
Start-ADSyncSyncCycle -PolicyType Initial

# 7. Verificare
Get-ADSyncScheduler
$status = Get-ADSyncConnectorRunStatus
if ($status) {
    Write-Host "Sync in corso..."
    $status | Select-Object ConnectorName, RunProfileName, Status
} else {
    Write-Host "Nessun sync in corso — verificare se completato"
}

# 8. Controllare lo stato in Entra ID
# Portale Azure > Entra ID > Azure AD Connect > Stato sincronizzazione
```

### Impatto su Entra ID durante Outage

```powershell
# Quando AADConnect è down, cosa succede?

# IMPATTO IMMEDIATO (0-30 min):
# - Nessun impatto visibile
# - Le credenziali sincronizzate continuano a funzionare
# - L'ultimo stato sincronizzato è valido

# IMPATTO A BREVE TERMINE (30 min - 24 ore):
# - Nuovi utenti creati on-prem non appaiono in Entra ID
# - Password cambiate on-prem non si sincronizzano
# - Modifiche ai gruppi non si propagano
# - MFA/Conditional Access continuano a funzionare

# IMPATTO A LUNGO TERMINE (24+ ore):
# - Il portale Entra ID mostra warning "sync non recente"
# - L'export dei delta si accumula
# - Dopo 30 giorni senza sync: possibile disabilitazione account sincronizzati

# MITIGAZIONE durante outage:
# Se necessario cambiare password:
# Usare il portale Entra ID direttamente (self-service password reset)
# Le modifiche in cloud NON verranno sovrascritte al riavvio di AADConnect
# (a meno che la source of authority sia AD)

# Monitorare lo stato sync da Entra ID
# PowerShell con modulo AzureAD:
# Connect-AzureAD
# Get-AzureADSync*

# Verificare l'ultima sync
# Portale Azure > Entra ID > Azure AD Connect
# "Last Sync" mostra il timestamp dell'ultima sincronizzazione
```


---

## Bare Metal Recovery di Domain Controller

### BMR vs System State Restore

| Aspetto | Bare Metal Recovery | System State Restore |
|---|---|---|
| Cosa ripristina | Intero server (OS + dati + System State) | Solo componenti System State |
| Richiede OS pre-installato | No | Sì |
| Velocità | Più lento (intero disco) | Più veloce (solo SS) |
| Hardware identico richiesto | Preferibile (non obbligatorio) | N/A (OS già installato) |
| Dimensione backup | 20-50+ GB | 10-15 GB |
| Uso tipico | Hardware distrutto | OS corruption, AD corruption |

### Procedura BMR con Windows Server Backup

```powershell
# PRE-REQUISITO: Aver configurato un backup BMR

# Creare un backup BMR
wbadmin start backup -backupTarget:E: -include:C: -systemState -allCritical -quiet

# Oppure backup su rete:
wbadmin start backup -backupTarget:\\backup-server\bmr-dc01 -include:C: -systemState -allCritical -quiet

# Scheduling BMR backup
$policy = New-WBPolicy
Add-WBBareMetalRecovery -Policy $policy
$target = New-WBBackupTarget -VolumePath E:
Add-WBBackupTarget -Policy $policy -Target $target
Set-WBSchedule -Policy $policy -Schedule 03:00
Set-WBPolicy -Policy $policy -Force

# === PROCEDURA DI RESTORE ===

# 1. Boot da Windows Server Installation Media (ISO/USB)
# 2. Selezionare lingua e "Repair your computer"
# 3. Troubleshoot > System Image Recovery
# 4. Selezionare il backup (locale o rete)
# 5. Se rete: configurare IP temporaneo per raggiungere il backup server
# 6. Selezionare "Restore only system drives" (non formattare dischi dati)
# 7. Attendere il completamento (30-120 minuti a seconda delle dimensioni)
# 8. Riavviare

# Post-restore:
# Il DC si avvia normalmente e cerca di replicare con gli altri DC
# Se forest recovery: avviare in DSRM per authoritative restore
```

### BMR su Hardware Differente

```powershell
# Windows Server BMR è abbastanza tollerante con hardware diverso.
# I problemi principali:

# 1. Driver del disk controller diverso
# - Iniettare il driver durante il restore wizard
# - O preparare un WinPE custom con i driver necessari

# 2. Differenze NIC
# - Windows rileva la nuova NIC e assegna un nuovo profilo
# - L'IP statico del DC deve essere riconfigurato
# - I record DNS A devono essere aggiornati

# 3. Problemi di attivazione
# - Se il product key è legato all'hardware (OEM), serve una nuova licenza
# - Le licenze Volume License non hanno questo problema

# Post-restore su hardware diverso:
# Verificare driver
Get-PnpDevice -Status ERROR

# Verificare e riconfigurare la rete
Get-NetAdapter | Select-Object Name, Status, MacAddress, LinkSpeed
Get-NetIPAddress -InterfaceAlias "Ethernet*" | Select-Object IPAddress, PrefixLength

# Riconfigurare IP statico se necessario
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 10.0.0.10 `
    -PrefixLength 24 -DefaultGateway 10.0.0.1
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 127.0.0.1,10.0.0.11
```

### Recovery di DC Virtualizzati

```powershell
# I DC virtualizzati hanno considerazioni aggiuntive per il DR.

# HYPER-V:
# - NON usare snapshot/checkpoint Hyper-V per il backup di DC
# - Gli snapshot possono causare USN rollback e database corruption
# - Usare SEMPRE Windows Server Backup o tool AD-aware

# VMWARE:
# - Stessa regola: NON usare snapshot VMware come backup
# - Usare VMware vSphere Backup con application-consistent snapshots
# - Verificare che VMware Tools sia aggiornato per VM Generation ID

# Restore di un DC VM:
# Opzione A: Restore della VM intera da backup hypervisor (AD-aware)
# Opzione B: Deploy nuova VM + System State restore
# Opzione C: Deploy nuova VM + promozione DC

# Per restore VM:
# 1. Restore della VM (spenta)
# 2. NON avviare in rete fino a che l'isolamento è verificato
# 3. Verificare VM Generation ID (vedi sotto)
# 4. Avviare e verificare
```

### VM Generation ID e SafeRestore

Windows Server 2012+ supporta VM-GenerationID per proteggere contro USN rollback.

```powershell
# VM Generation ID è un identificatore unico della VM che cambia
# quando viene applicato uno snapshot o restore.
# AD rileva il cambio e protegge la consistenza del database.

# Verificare il VM Generation ID corrente
Get-ADDomainController -Identity $env:COMPUTERNAME |
    Select-Object Name, @{N='VMGenID';E={
        (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Virtual Machine\Auto").VmGenerationId
    }}

# Cosa succede quando AD rileva un cambio di VM-GenerationID:
# 1. Il pool RID viene invalidato (previene SID duplicati)
# 2. Il database invocationID viene resettato
# 3. Le password degli account computer/trust vengono rigenerate
# 4. DFSR effettua un non-authoritative sync
# 5. Evento 2170 nel log Directory Service

# Verificare eventi SafeRestore
Get-WinEvent -FilterHashtable @{LogName='Directory Service'; Id=2170} -MaxEvents 5 -ErrorAction SilentlyContinue

# Verificare che l'hypervisor supporti VM-GenerationID
# Hyper-V: supportato da Windows Server 2012+
# VMware: supportato da vSphere 5.0+ con VM hardware version 9+
# KVM/QEMU: supportato con libvirt recente

# ATTENZIONE: hypervisor che non supportano VM-GenerationID
# (vecchie versioni) possono causare USN rollback silente.
# In questi ambienti: non fare MAI snapshot di DC.
```


---

## DR Planning e Testing

### DR Plan — Struttura e Contenuti

Un DR plan per Active Directory deve contenere:

```
DR PLAN — Active Directory
============================

1. INFORMAZIONI GENERALI
   ├── Versione del documento e data ultimo aggiornamento
   ├── Approvazione (CIO, CISO, IT Director)
   ├── Distribuzione (chi ha copia del documento)
   └── Frequenza di revisione (semestrale minimo)

2. INVENTARIO
   ├── Elenco di tutti i DC con: nome, IP, sito, ruoli FSMO, GC, OS version
   ├── Elenco CA con: tipo (Root/Sub), algoritmo, scadenza cert
   ├── Elenco trust relationship
   ├── AADConnect server e staging server
   └── DNS server e zone configuration

3. BACKUP STRATEGY
   ├── Cosa viene backuppato e frequenza
   ├── Dove sono conservati i backup (primario + offsite)
   ├── Retention policy
   ├── Procedura di verifica backup
   └── Password dei backup (dove conservate)

4. CONTATTI E ESCALATION
   ├── Team AD / Identity
   ├── Team Storage / Backup
   ├── Team Network
   ├── Team Security
   ├── Management / CISO
   ├── Vendor support (Microsoft Premier, Veeam, etc.)
   └── Orari reperibilità e SLA

5. PROCEDURE DI RECOVERY
   ├── Singolo DC failure
   ├── Multi-DC failure
   ├── Forest recovery
   ├── PKI recovery
   ├── DNS recovery
   ├── Trust recovery
   └── AADConnect recovery

6. COMUNICAZIONE
   ├── Template di comunicazione per diversi scenari
   ├── Canali alternativi (se email/Teams sono down)
   ├── Notifiche a management e stakeholder
   └── Comunicazione a utenti finali

7. POST-INCIDENT
   ├── Checklist di validazione post-recovery
   ├── Procedure di ritorno alla normalità
   ├── Lessons learned template
   └── Piano di miglioramento
```

### Testing del DR Plan

```powershell
# Il DR plan DEVE essere testato almeno 2 volte l'anno.
# Test insufficienti sono la causa #1 di fallimento dei DR plan.

# Livelli di test:

# LIVELLO 1: Documentation Review (mensile)
# - Verificare che il documento sia aggiornato
# - Controllare che i contatti siano correnti
# - Verificare che le password documentate funzionino

# LIVELLO 2: Tabletop Exercise (trimestrale)
# - Riunione del team con scenario simulato
# - Discussione delle procedure passo-passo
# - Identificazione di gap nel piano

# LIVELLO 3: Component Test (trimestrale)
# - Test di singole procedure (es: restore System State in lab)
# - Test di seize FSMO
# - Test di DSRM login
# - Test di CRL publish da Root CA

# LIVELLO 4: Full DR Drill (semestrale)
# - Forest recovery completa in ambiente isolato
# - Simulazione completa dal disastro al ripristino
# - Misurare il tempo effettivo di recovery (vs RTO dichiarato)
# - Documentare tutti i problemi incontrati

# Script per verificare la preparazione al DR
Write-Host "=== DR Readiness Check ===" -ForegroundColor Cyan

# 1. Backup recenti?
$backupCheck = Get-WBBackupSet | Sort-Object BackupTime -Descending | Select-Object -First 1
$backupAge = ((Get-Date) - $backupCheck.BackupTime).TotalHours
$status = if ($backupAge -lt 48) { "OK" } else { "FAIL" }
Write-Host "Backup più recente: $([math]::Round($backupAge,1))h fa [$status]"

# 2. DSRM password funzionante?
Write-Host "DSRM password: verificare manualmente con test login"

# 3. FSMO roles assegnati?
$fsmo = netdom query fsmo 2>&1
Write-Host "FSMO roles: $($fsmo | Select-Object -First 5)"

# 4. Replica funzionante?
$replStatus = repadmin /replsummary 2>&1
$failures = ($replStatus | Select-String "fail" -SimpleMatch).Count
$status = if ($failures -eq 0) { "OK" } else { "FAIL ($failures)" }
Write-Host "Replica: $status"

# 5. SYSVOL condiviso?
$sysvolShare = Get-SmbShare -Name SYSVOL -ErrorAction SilentlyContinue
$status = if ($sysvolShare) { "OK" } else { "FAIL" }
Write-Host "SYSVOL share: $status"
```

### DR Drill — Tabletop vs Full Exercise

**Tabletop Exercise:**
- Durata: 2-4 ore
- Partecipanti: team AD, security, management
- Scenario: presentato su carta, discussione delle azioni
- Output: gap identificati, azioni correttive

**Full DR Drill:**
- Durata: 4-16 ore (a seconda della complessità)
- Ambiente: lab isolato con VM che replicano la produzione
- Scenario: esecuzione reale delle procedure di recovery
- Output: tempo effettivo di recovery, problemi reali, metriche

```powershell
# Template per documentare i risultati del DR drill

$drillReport = @"
DR DRILL REPORT
===============
Data: $(Get-Date -Format 'yyyy-MM-dd')
Tipo: [Tabletop / Component / Full]
Scenario: [Descrizione dello scenario simulato]
Durata: [Inizio - Fine]
Partecipanti: [Elenco]

METRICHE
--------
RTO dichiarato: [valore]
RTO effettivo:  [valore misurato]
RPO dichiarato: [valore]
RPO effettivo:  [valore misurato]

RISULTATI
---------
[ ] Backup recuperato con successo
[ ] System State restore completato
[ ] DSRM login funzionante
[ ] Forest recovery completata
[ ] FSMO roles seized con successo
[ ] SYSVOL restored e condiviso
[ ] DNS funzionante
[ ] Autenticazione utenti funzionante
[ ] GPO applicate
[ ] PKI funzionante

PROBLEMI RISCONTRATI
--------------------
1. [Problema]: [Soluzione trovata] [Tempo perso]
2. [...]

AZIONI CORRETTIVE
------------------
1. [Azione]: [Responsabile] [Scadenza]
2. [...]
"@
$drillReport | Out-File "E:\DR-Reports\DrillReport_$(Get-Date -Format 'yyyyMMdd').txt"
```

### Documentazione e Runbook

```powershell
# Il runbook deve essere:
# - Stampato e conservato in luogo fisico accessibile
# - Disponibile offline (USB, non solo su SharePoint che dipende da AD)
# - Aggiornato dopo ogni cambio di infrastruttura
# - Testato con personale diverso (non solo chi l'ha scritto)

# Generare automaticamente un inventario aggiornato per il runbook
$inventario = @{
    Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC' -AsUTC
    Forest = (Get-ADForest).Name
    ForestMode = (Get-ADForest).ForestMode
    Domains = (Get-ADForest).Domains
    DomainControllers = Get-ADDomainController -Filter * |
        Select-Object Name, HostName, IPv4Address, Site, IsGlobalCatalog,
            OperatingSystem, OperationMasterRoles
    Sites = Get-ADReplicationSite -Filter * | Select-Object Name
    SiteLinks = Get-ADReplicationSiteLink -Filter * |
        Select-Object Name, Cost, ReplicationFrequencyInMinutes
    Trusts = Get-ADTrust -Filter * |
        Select-Object Name, Direction, TrustType, ForestTransitive
    DNSZones = Get-DnsServerZone | Select-Object ZoneName, ZoneType, ReplicationScope
}

$inventario | ConvertTo-Json -Depth 5 |
    Out-File "E:\DR-Runbook\AD-Inventory_$(Get-Date -Format 'yyyyMMdd').json"
```

### Comunicazione durante un Incidente

```
MATRICE DI COMUNICAZIONE — AD DISASTER
=========================================

Tempo 0 (Disastro rilevato):
  → Team AD: via telefono/SMS (email potrebbe non funzionare)
  → CISO: notifica immediata
  → IT Director: notifica immediata
  → Service Desk: "AD non disponibile, tutti i servizi Windows impattati"

Tempo +30 min (Assessment completato):
  → Management: stima impatto e timeline
  → Utenti: "servizi non disponibili, stiamo lavorando al ripristino"
  → Vendor support: apertura ticket se necessario

Ogni 2 ore durante recovery:
  → Update a tutti gli stakeholder
  → Canale alternativo se email non funziona:
    - Telefono/SMS
    - WhatsApp/Signal gruppo emergenza
    - Slack/Teams se non dipendente da AD on-prem
    - Radio (in scenari estremi)

Post-recovery:
  → Conferma ripristino a tutti
  → Timeline per post-mortem
  → Lessons learned meeting entro 48h
```


---

## Runbook Templates

### Runbook — Single DC Failure

```
RUNBOOK: SINGOLO DC FAILURE
============================
Trigger: un DC non risponde o ha hardware failure
RTO: 1-2 ore
Impatto: ridotto se ci sono altri DC nel sito

STEP 1: VERIFICA (10 min)
  □ Ping il DC: Test-Connection DC02
  □ Verificare console hypervisor (se VM)
  □ Verificare hardware (se fisico): iLO/iDRAC/IMM
  □ Controllare se FSMO roles erano su questo DC: netdom query fsmo

STEP 2: DECISIONE (5 min)
  □ DC recuperabile in < 1 ora? → riparare
  □ DC non recuperabile? → procedere con ricostruzione

STEP 3A: RIPARAZIONE (se recuperabile)
  □ Fix hardware / restart VM
  □ Verificare avvio: dcdiag /s:DC02 /v
  □ Verificare replica: repadmin /showrepl DC02
  □ Fine

STEP 3B: RICOSTRUZIONE (se non recuperabile)
  □ Se FSMO holder: seize roles su altro DC
  □ Metadata cleanup: ntdsutil / Remove-ADObject
  □ DNS cleanup: rimuovere record A/SRV del DC
  □ Promuovere un nuovo server come DC
  □ Verificare: dcdiag, repadmin, nltest

STEP 4: VALIDAZIONE
  □ dcdiag /v su tutti i DC
  □ repadmin /replsummary
  □ nltest /sc_verify:contoso.com
  □ Test login utente
  □ Verificare SYSVOL share
```

### Runbook — Forest-Wide Recovery

```
RUNBOOK: FOREST-WIDE RECOVERY
===============================
Trigger: tutti i DC compromessi (ransomware, schema corruption)
RTO: 4-24 ore
Impatto: TOTALE — nessun servizio Windows funzionante

PRE-REQUISITI:
  □ Backup System State verificato e accessibile
  □ Password DSRM documentata
  □ Documentazione topologia forest
  □ Ambiente isolato preparato (VM senza rete)

FASE 1: ISOLAMENTO (30 min)
  □ Spegnere TUTTI i DC
  □ Disconnettere la rete da tutti i DC
  □ Verificare integrità backup

FASE 2: PRIMO DC (1-3 ore)
  □ Scegliere il DC per il primo restore
  □ Boot in DSRM
  □ System State restore: wbadmin start systemstaterecovery
  □ Authoritative restore se necessario: ntdsutil auth restore
  □ SYSVOL D4 (autoritativo)
  □ Rimuovere safeboot e riavviare
  □ Verificare: dcdiag /v

FASE 3: PULIZIA (1-2 ore)
  □ Metadata cleanup per DC non recuperabili
  □ Seize FSMO roles se necessario
  □ Pulizia DNS
  □ Reset password krbtgt (2 volte con 10h intervallo)
  □ Invalidare pool RID

FASE 4: DC AGGIUNTIVI (1-4 ore per DC)
  □ Per ogni DC aggiuntivo necessario:
    □ Installare Windows Server su hardware/VM pulito
    □ Promuovere come DC replica
    □ SYSVOL D2 (non-autoritativo)
    □ Verificare replica

FASE 5: VALIDAZIONE (1-2 ore)
  □ dcdiag su tutti i DC
  □ repadmin /replsummary
  □ DNS: verify SRV records
  □ SYSVOL condiviso su tutti i DC
  □ FSMO roles verificati
  □ Test login su client

FASE 6: RIENTRO (graduale)
  □ Connettere un subset di client per test
  □ Verificare GPO
  □ Verificare autenticazione applicazioni
  □ Aprire a tutti i client
  □ Monitorare per 48h
```

### Runbook — PKI CA Recovery

```
RUNBOOK: PKI CA RECOVERY
==========================
Trigger: Issuing CA server down/distrutto
RTO: 4-8 ore
Impatto: no new certificates, CRL scaduta se oltre overlap period

PRE-REQUISITI:
  □ Backup chiave privata CA (PFX/P12) con password
  □ Backup database CA
  □ Backup registry configuration
  □ AD funzionante (Enterprise CA dipende da AD)

STEP 1: VERIFICA CRL (15 min)
  □ Controllare scadenza CRL: certutil -URL <CRL URL>
  □ Se CRL scade entro 48h → priorità CRITICA
  □ Se CRL è valida per > 7 giorni → priorità alta

STEP 2: MITIGAZIONE TEMPORANEA (30 min)
  □ Se CRL disponibile su CDP secondari → nessuna azione
  □ Se CRL sta scadendo → pubblicare CRL manualmente da backup
  □ Copy-Item backup.crl to \\web-pki\wwwroot\CertEnroll\

STEP 3: REBUILD CA (2-4 ore)
  □ Preparare nuovo server (Windows Server, domain joined)
  □ Install-WindowsFeature ADCS-Cert-Authority
  □ Restoring CA key: certutil -restorekey
  □ Configure CA con chiave esistente
  □ Restore database: certutil -restoredb
  □ Import registry: reg import CertSvc-Registry.reg
  □ Start-Service CertSvc
  □ Pubblicare nuova CRL: certutil -CRL

STEP 4: VALIDAZIONE (30 min)
  □ certutil -ping
  □ certutil -CRL (publish)
  □ Verificare CDP raggiungibile: certutil -verify -urlfetch
  □ Test enrollment su un client
  □ Verificare OCSP se presente

STEP 5: POST-RECOVERY
  □ Aggiornare certificato CA in AD se necessario
  □ Forzare auto-enrollment: gpupdate /force sui client
  □ Monitorare enrollment per 48h
```

### Runbook — Ransomware AD Recovery

```
RUNBOOK: RANSOMWARE AD RECOVERY
=================================
Trigger: ransomware ha cifrato/compromesso i DC
RTO: 8-48 ore
Impatto: TOTALE + rischio di re-infezione

⚠️  QUESTO È UNO SCENARIO DI INCIDENT RESPONSE.
    Coordinare con il team Security/CISO.

STEP 1: CONTENIMENTO (immediato)
  □ Disconnettere TUTTI i DC dalla rete (non spegnere se possibile)
  □ Preservare evidence (memory dump, disk image)
  □ Identificare il vettore di attacco
  □ Determinare il Patient Zero e la timeline
  □ Valutare se i backup sono stati compromessi
  □ Coinvolgere forze dell'ordine se richiesto

STEP 2: ASSESSMENT (1-4 ore)
  □ I backup sono integri e non cifrati?
  □ I backup sono anteriori alla compromissione?
  □ Quali DC sono salvabili?
  □ La Root CA è stata compromessa?
  □ Krbtgt è stato compromesso (Golden Ticket)?
  □ Trust relationships compromesse?

STEP 3: AMBIENTE CLEAN (2-4 ore)
  □ Preparare hardware/VM PULITO (non contaminato)
  □ Rete ISOLATA per il recovery
  □ Nessuna connessione verso il segmento compromesso

STEP 4: FOREST RECOVERY (vedere runbook Forest-Wide)
  □ Seguire la procedura Forest Recovery completa
  □ AGGIUNTIVO: reset krbtgt 2 volte
  □ AGGIUNTIVO: reset password TUTTI gli admin
  □ AGGIUNTIVO: reset password trust
  □ AGGIUNTIVO: revocare e re-emettere certificati CA se compromessi
  □ AGGIUNTIVO: rimuovere persistence (scheduled task, GPO malevole,
    modifiche allo schema, AdminSDHolder, DCSync permissions)

STEP 5: HARDENING POST-RECOVERY
  □ Implementare tiered admin model
  □ Abilitare Protected Users
  □ Rimuovere permessi DCSync non necessari
  □ Configurare LAPS
  □ Abilitare Advanced Audit Policy
  □ Deploy EDR su tutti i DC
  □ Segmentare la rete dei DC

STEP 6: MONITORAGGIO INTENSIVO (30 giorni)
  □ Monitoring 24/7 dei DC
  □ Alert su eventi sospetti (4625, 4768, 4769, 4720, 4732)
  □ Verificare assenza di persistence
  □ Scanning periodico con tool di detection
```


---

## Scenari

| Disaster | RTO target | Recovery procedure |
|---|---|---|
| Single DC fail | 1h | Promote replica DC; rebuild |
| Forest corruption | 24-48h | Forest Recovery from backup |
| PKI root compromise | 1 settimana | Re-issue root + rebuild trust |
| OU cancellata accidentalmente | 15 min | AD Recycle Bin |
| SYSVOL corruption su un DC | 2h | DFSR D2 restore |
| Tutti i DC cifrati da ransomware | 24-72h | Forest recovery in ambiente isolato |
| AADConnect server failure | 30 min (staging) / 4h (rebuild) | Promuovere staging o rebuild |
| CRL scaduta per CA down | 1h | Pubblicare CRL da backup su CDP |
| DNS zone corrotta | 1h | Replica AD o restore da file |
| Cross-forest trust rotta | 2h | Reset password trust o ricreazione |
| Schema Master perso | 2h | Seize su altro DC |
| NTDS.DIT corrotto su DC | 2-4h | System State restore o rebuild |


---

## Esercizi

1. **Lab — DSRM boot + restore.** AD authoritative restore in lab.
2. **Stretch — Forest Recovery drill.**
3. **Lab — AD Recycle Bin.** Abilitare AD Recycle Bin, cancellare un utente e un gruppo, recuperare entrambi con PowerShell. Verificare che le membership siano corrette.
4. **Lab — System State Backup e Restore.** Configurare un backup schedulato con `wbadmin`, eseguire un backup manuale, verificare l'integrità, e fare un restore in VM isolata.
5. **Lab — SYSVOL D4/D2.** In un lab con 2 DC, corrompere SYSVOL sul primo DC, eseguire D4 restore, poi forzare D2 sull'altro DC. Verificare che le GPO siano sincronizzate.
6. **Lab — PKI CA Backup e Restore.** Eseguire il backup completo di una Enterprise CA (chiave, database, registry). Ricostruire la CA su un nuovo server. Verificare che l'enrollment funzioni.
7. **Lab — FSMO Seize.** Spegnere il DC che detiene i ruoli FSMO. Eseguire il seize su un altro DC. Verificare che tutti i servizi funzionino.
8. **Lab — DNS Recovery.** Esportare le zone DNS, cancellare una zona, ripristinarla dal backup. Verificare la risoluzione.
9. **Stretch — DR Drill completo.** Eseguire una forest recovery completa in ambiente lab: backup → spegnimento tutti i DC → restore primo DC → metadata cleanup → seize FSMO → promozione DC aggiuntivi → validazione. Misurare il tempo totale e confrontare con l'RTO dichiarato.
10. **Lab — AADConnect Staging Failover.** Configurare un server AADConnect attivo e uno in staging. Fermare il server attivo, promuovere lo staging, verificare che il sync funzioni.


---

## Troubleshooting

### 1. System State restore fallisce con errore "Version not compatible"

**Causa:** il backup è stato creato su una versione diversa di Windows Server.
**Soluzione:**
```powershell
# Verificare la versione del backup
wbadmin get versions -backupTarget:E:
# Confrontare con la versione corrente
[System.Environment]::OSVersion.Version
# Il restore richiede stessa major version (2019→2019, 2022→2022)
# Per cross-version: promuovere un nuovo DC invece di restore
```

### 2. DSRM login fallisce — "The user name or password is incorrect"

**Causa:** password DSRM dimenticata o non sincronizzata.
**Soluzione:**
```powershell
# Se il DC può ancora avviarsi normalmente:
ntdsutil "set dsrm password" "reset password on server null" quit quit
# Se il DC non si avvia normalmente:
# Boot da Windows PE, montare il SAM hive, reset password con tool offline
# Oppure: abbandonare il DC e ricostruirlo
```

### 3. Dopo il restore, la replica mostra "lingering objects"

**Causa:** oggetti tombstoned presenti su altri DC ma non nel backup.
**Soluzione:**
```powershell
# Identificare lingering objects
repadmin /removelingeringobjects DC02.contoso.com <GUID-DC01> "DC=contoso,DC=com" /advisory_mode
# Se confermato, rimuovere senza advisory_mode:
repadmin /removelingeringobjects DC02.contoso.com <GUID-DC01> "DC=contoso,DC=com"
# Strict replication consistency:
repadmin /regkey DC02 +strict
```

### 4. SYSVOL non condiviso dopo il restore — NETLOGON share mancante

**Causa:** DFSR non ha completato l'inizializzazione.
**Soluzione:**
```powershell
# Verificare lo stato DFSR
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Level=1,2,3} -MaxEvents 20
# Se evento 4012 (DFSR fermato): rifare procedura D4/D2
# Se evento 2213 (journal wrap): reset DFSR database
# Verificare manualmente che il SYSVOL path esista:
Test-Path "C:\Windows\SYSVOL\sysvol"
Test-Path "C:\Windows\SYSVOL\domain"
```

### 5. Errore "The Active Directory Domain Services database has been restored" dopo snapshot VM

**Causa:** USN rollback detection dopo restore di snapshot VM.
**Soluzione:**
```powershell
# Se l'hypervisor supporta VM-GenerationID (Hyper-V 2012+, vSphere 5.0+):
# Il problema si risolve automaticamente con SafeRestore.
# Se hypervisor vecchio:
# 1. Il DC è in quarantena — non replicherà
# 2. Demote forzato: dcpromo /forceremoval
# 3. Metadata cleanup
# 4. Re-promozione da zero
# NON tentare di "fixare" un USN rollback — ricostruire il DC.
```

### 6. Authoritative restore non funziona — gli oggetti vengono cancellati di nuovo

**Causa:** il version number non è stato incrementato correttamente, o i linked attributes (group membership) non sono stati ripristinati.
**Soluzione:**
```powershell
# Verificare che ntdsutil abbia generato il file .ldf
# Il file contiene le operazioni LDIF per ripristinare i back-links
# Importare il file LDIF:
ldifde -i -f "ar_20260522-143000_objects.ldf"
# Se non funziona: fare auth restore della subtree intera, non del singolo oggetto
```

### 7. Certificate enrollment fallisce dopo CA restore — "The RPC server is unavailable"

**Causa:** il server CA non è registrato correttamente in AD o il certificato non è in NTAuthCertificates.
**Soluzione:**
```powershell
# Verificare che la CA sia registrata in AD
certutil -dspublish -f <CA-cert-file> SubCA
certutil -dspublish -f <CA-cert-file> NTAuthCA
# Verificare connettività RPC
Test-NetConnection -ComputerName CA01 -Port 135
# Verificare il servizio
Get-Service CertSvc -ComputerName CA01
# Forzare auto-enrollment
certutil -pulse
gpupdate /force
```

### 8. DNS non risolve dopo forest recovery — nslookup timeout

**Causa:** i record SRV non sono stati registrati dal DC.
**Soluzione:**
```powershell
# Forzare registrazione DNS
ipconfig /registerdns
nltest /dsregdns
net stop netlogon && net start netlogon
# Verificare che il DNS forwardi ai root hints se serve internet
Get-DnsServerForwarder
# Verificare le zone
Get-DnsServerZone | Select-Object ZoneName, ZoneType
```

### 9. Replica bloccata — "The target principal name is incorrect" (errore 1398/1722)

**Causa:** mismatch tra nome DNS, SPN e account computer del DC dopo restore.
**Soluzione:**
```powershell
# Verificare SPN del DC
setspn -L DC01
# Reset dell'account computer del DC
netdom resetpwd /server:DC02 /userd:contoso\Administrator /passwordd:*
# Verificare il canale sicuro
Test-ComputerSecureChannel -Server DC02 -Repair
# Se non funziona: demote e re-promote il DC problematico
```

### 10. AADConnect sync fallisce dopo restore — "stopped-server"

**Causa:** il database AADConnect è inconsistente o la connessione a Entra ID è interrotta.
**Soluzione:**
```powershell
# Verificare lo stato del sync
Get-ADSyncScheduler
Get-ADSyncConnectorRunStatus
# Se il database è corrotto: rimuovere e reinstallare AADConnect
# Se la connessione è interrotta: verificare credenziali
# Forzare un full sync:
Start-ADSyncSyncCycle -PolicyType Initial
```

### 11. Errore "There is not enough space on the disk" durante System State restore

**Causa:** il volume di destinazione non ha spazio sufficiente.
**Soluzione:**
```powershell
# System State restore richiede circa 2x la dimensione del backup
# Verificare lo spazio disponibile:
Get-Volume | Select-Object DriveLetter, SizeRemaining, Size |
    ForEach-Object { [PSCustomObject]@{
        Drive = $_.DriveLetter
        FreeGB = [math]::Round($_.SizeRemaining/1GB,2)
        TotalGB = [math]::Round($_.Size/1GB,2)
    }}
# Liberare spazio o usare un volume diverso
# Opzione: restore su un volume aggiuntivo e poi spostare
```

### 12. Dopo metadata cleanup, eventi "can't replicate with removed DC"

**Causa:** riferimenti residui al DC rimosso in oggetti di connessione o site links.
**Soluzione:**
```powershell
# Verificare oggetti di connessione rimasti
Get-ADObject -SearchBase "CN=Sites,CN=Configuration,DC=contoso,DC=com" `
    -Filter "objectClass -eq 'nTDSConnection'" -Properties fromServer |
    Where-Object { $_.fromServer -like "*DCRimosso*" } |
    Remove-ADObject -Confirm:$false

# Forzare KCC a ricalcolare la topology
repadmin /kcc
```

### 13. DFSR mostra "sharing violation" su file SYSVOL

**Causa:** un processo (antivirus, backup agent) ha un lock su un file nel SYSVOL.
**Soluzione:**
```powershell
# Identificare il processo che blocca il file
# Usare handle.exe (Sysinternals) o Resource Monitor
# Verificare esclusioni antivirus per SYSVOL:
# Escludere: %SystemRoot%\SYSVOL\*, %SystemRoot%\System Volume Information\DFSR\*
# Configurare il backup agent per non fare lock su SYSVOL
```

### 14. Forest recovery completata ma le Group Policy non si applicano

**Causa:** SYSVOL non è considerato "ready" dal servizio Netlogon.
**Soluzione:**
```powershell
# Verificare la readiness di SYSVOL
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters" -Name SysvolReady
# Valore 1 = ready, 0 = not ready
# Se 0: DFSR non ha completato l'inizializzazione
# Verificare lo stato DFSR: eventi 4602, 4604
# Se necessario, forzare SysvolReady (SOLO come ultima risorsa, TEMPORANEO):
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters" -Name SysvolReady -Value 1
Restart-Service Netlogon
```

### 15. CRL publishing fallisce — "Access denied" sui CDP HTTP

**Causa:** il servizio CA non ha permessi per scrivere sulla share del CDP.
**Soluzione:**
```powershell
# Verificare i permessi sulla share CDP
Get-SmbShareAccess -Name "CertEnroll"
# L'account computer della CA deve avere Change permission
Grant-SmbShareAccess -Name "CertEnroll" -AccountName "CONTOSO\CA01$" -AccessRight Change -Force
# Verificare permessi NTFS
$acl = Get-Acl "C:\inetpub\wwwroot\CertEnroll"
$acl.Access | Where-Object { $_.IdentityReference -like "*CA01*" }
# Se mancante:
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("CONTOSO\CA01$","Modify","ContainerInherit,ObjectInherit","None","Allow")
$acl.AddAccessRule($rule)
Set-Acl "C:\inetpub\wwwroot\CertEnroll" $acl
```

### 16. Dopo restore, i client ottengono "Clock skew too great" (Kerberos)

**Causa:** l'orologio del DC ripristinato è disallineato rispetto ai client.
**Soluzione:**
```powershell
# Verificare l'ora sul DC
w32tm /query /status
# Riconfigurare NTP source (il PDC Emulator deve puntare a NTP esterno)
w32tm /config /manualpeerlist:"time.windows.com" /syncfromflags:manual /reliable:YES /update
w32tm /resync /force
# Gli altri DC sincronizzeranno la gerarchia dal PDC Emulator
# La tolleranza Kerberos di default è ±5 minuti
```

### 17. Trust recovery fallisce — "The security database on the server does not have a computer account"

**Causa:** l'account trust è stato perso durante il forest recovery.
**Soluzione:**
```powershell
# La trust deve essere ricreata da zero su entrambi i lati
# Lato locale:
Remove-ADObject "CN=partner.com,CN=System,DC=contoso,DC=com" -Confirm:$false
# Ricreare la trust:
netdom trust contoso.com /domain:partner.com /add /twoway /passwordT:TrustPwd!
# Verificare:
nltest /sc_verify:partner.com
```


---

## FAQ

### 1. Ogni quanto devo fare il backup di Active Directory?

**Risposta:** Almeno una volta al giorno (System State) per ambienti di produzione. Per ambienti critici (finanza, sanità), due volte al giorno. Il backup deve essere più frequente della tombstone lifetime (default 180 giorni) per essere utilizzabile. Idealmente, testare il restore almeno una volta al trimestre.

### 2. Posso usare gli snapshot della VM (Hyper-V / VMware) come backup dei DC?

**Risposta:** **NO.** Gli snapshot VM non sono backup AD-consistent. Possono causare USN rollback, che mette il DC in quarantena e richiede una ricostruzione. Usare sempre Windows Server Backup (System State) o tool di terze parti AD-aware. Le VM Generation ID (2012+) mitigano il rischio ma non lo eliminano — gli snapshot restano una cattiva pratica per i DC.

### 3. Che succede se la password DSRM è persa?

**Risposta:** Se il DC si avvia normalmente in modalità standard, si può resettare la password DSRM con `ntdsutil`. Se il DC NON si avvia normalmente e la password DSRM è persa, il DC deve essere ricostruito da zero (promozione di un nuovo DC). Per questo motivo, la password DSRM deve essere documentata, conservata in un password manager, e testata periodicamente.

### 4. Qual è la differenza tra AD Recycle Bin e Authoritative Restore?

**Risposta:** AD Recycle Bin è una funzionalità che mantiene gli oggetti eliminati in stato "Deleted" con tutti gli attributi, permettendo un recupero rapido via PowerShell senza downtime. Authoritative Restore richiede DSRM, è più complesso, ma funziona anche senza Recycle Bin abilitato e può ripristinare oggetti da backup più vecchi. Usare Recycle Bin per cancellazioni recenti, Authoritative Restore per corruzione database o recupero da backup.

### 5. Posso ripristinare un backup di AD su hardware completamente diverso?

**Risposta:** Sì, con Bare Metal Recovery. Windows Server è abbastanza tollerante con hardware diverso, ma potrebbe essere necessario iniettare driver per il controller disco. Le NIC avranno nuovi profili e l'IP dovrà essere riconfigurato. Le licenze OEM potrebbero richiedere riattivazione. Per DC virtualizzati, è generalmente più semplice.

### 6. Come faccio a sapere se il mio backup è ancora utilizzabile?

**Risposta:** Un backup System State è utilizzabile se: (a) è più recente della tombstone lifetime (180 giorni per default), (b) è stato creato sulla stessa major version di Windows Server, (c) non è corrotto (verificare con `wbadmin get versions`). L'unico modo per essere certi è **testare il restore** in un ambiente isolato.

### 7. Quanto tempo serve per una forest recovery completa?

**Risposta:** In media 8-24 ore per un ambiente medio (10-20 DC, 1 forest, 1-2 domini). Il tempo dipende da: dimensione del database AD, velocità del restore, numero di DC da ricostruire, complessità della topologia, e esperienza del team. Con un team preparato e procedure testate, si può ridurre a 4-8 ore per il primo DC funzionante.

### 8. Devo resettare la password krbtgt dopo una forest recovery? Quante volte?

**Risposta:** **Sì, obbligatorio.** Due volte, con almeno 10 ore di intervallo tra i reset. Il motivo: krbtgt è usato per firmare tutti i Kerberos Ticket Granting Tickets (TGT). Se un attaccante ha ottenuto l'hash di krbtgt (Golden Ticket), può generare TGT validi indefinitamente. Il doppio reset invalida tutti i TGT esistenti (il primo reset invalida i nuovi, il secondo invalida quelli firmati con la versione N-1).

### 9. L'AD Recycle Bin ripristina anche le membership dei gruppi?

**Risposta:** Sì, **se l'oggetto è ancora in stato "Deleted"** (non ancora in stato "Recycled"). Gli attributi linked (come memberOf) vengono conservati nella fase Deleted. Se l'oggetto è passato allo stato Recycled (dopo la Deleted Object Lifetime), gli attributi linked sono persi. Per questo è importante intervenire rapidamente e impostare una DOL adeguata.

### 10. Posso usare un RODC (Read-Only Domain Controller) per la forest recovery?

**Risposta:** **No.** Un RODC non contiene una copia completa del database AD (in particolare, non ha le password degli utenti non cached). Il primo DC nella forest recovery deve essere un RWDC (Read-Write DC). Un RODC può essere utile dopo la recovery come DC aggiuntivo in siti remoti.

### 11. Come gestisco la PKI se la CA è anche il DC che devo ripristinare?

**Risposta:** Situazione complicata ma comune negli ambienti piccoli. Il System State backup include sia AD che il database CA. Ripristinare il System State ripristina entrambi. Tuttavia, è una bad practice avere la CA sullo stesso server del DC. Dopo il recovery, pianificare la separazione dei ruoli: spostare la CA su un server dedicato.

### 12. Quanto dura la CRL della mia CA e cosa succede quando scade?

**Risposta:** La durata è configurabile (default spesso 1 settimana per Base CRL, 1 giorno per Delta CRL). Quando la CRL scade e non è disponibile una nuova: le applicazioni che verificano la revoca falliranno. L'impatto dipende dalla configurazione dei client: se il check CRL è "hard fail" (default per smart card logon, EAP-TLS), l'autenticazione fallisce. Se è "soft fail" (default per web), il certificato viene accettato comunque (con warning). Pianificare CRL period e overlap in base al proprio RTO per la CA.

### 13. Posso fare il restore di AD su Windows Server 2025 da un backup di Windows Server 2019?

**Risposta:** **No.** Il System State restore richiede la stessa major version di Windows Server. Per migrare: promuovere un DC 2025 nella forest esistente, replicare, poi demote i DC 2019. Non è un'operazione di DR, è una migration.

### 14. Il mio AADConnect non ha uno staging server. Quanto è grave?

**Risposta:** **Grave.** Senza staging server, un failure del server AADConnect richiede una reinstallazione completa (4-8 ore se la configurazione è documentata, giorni se non lo è). Con uno staging server, il failover è 5-10 minuti. Il costo di una VM con AADConnect in staging è trascurabile rispetto al rischio. Configurarlo è priorità alta.

### 15. Come verifico che il mio DR plan funzioni realmente?

**Risposta:** L'unico modo è **testarlo.** Un DR plan non testato è un documento fiction. Fare almeno: (1) tabletop exercise trimestrale con il team, (2) test di singole componenti (DSRM login, System State restore, FSMO seize) trimestrale, (3) full forest recovery drill in lab isolato semestrale. Misurare il tempo effettivo e confrontare con l'RTO dichiarato. Documentare ogni problema riscontrato e aggiornare il piano.

### 16. Dopo una forest recovery, gli utenti devono cambiare password?

**Risposta:** Dipende dal motivo del recovery. Se è un semplice hardware failure: no, le password sono nel backup. Se è un ransomware/compromissione: **sì, tutti gli utenti devono cambiare password**, perché l'attaccante potrebbe avere gli hash. Forzare il cambio password al prossimo logon per tutti:
```powershell
Get-ADUser -Filter * -SearchBase "OU=Utenti,DC=contoso,DC=com" |
    Set-ADUser -ChangePasswordAtLogon $true
```

### 17. Posso automatizzare completamente la forest recovery?

**Risposta:** No, non completamente. Alcuni passi richiedono decisioni umane (quale backup usare, quali DC ricostruire, quando connettere alla rete). Tuttavia, si possono automatizzare i singoli passi (script per metadata cleanup, FSMO seize, validazione). Microsoft non fornisce un tool automatizzato per la forest recovery. Strumenti di terze parti (Semperis, Quest) offrono automazione parziale ma richiedono comunque supervisione.

### 18. Qual è il rischio di non avere AD Recycle Bin abilitato?

**Risposta:** Senza AD Recycle Bin, un oggetto eliminato diventa immediatamente un tombstone con la maggior parte degli attributi persi (incluse membership di gruppo, manager, attributi custom). Il recupero richiede DSRM + authoritative restore, con downtime significativo. Con Recycle Bin, il recupero è un comando PowerShell senza downtime. Non c'è nessun motivo valido per non abilitarlo (è irreversibile ma non ha svantaggi operativi).


---

## Letture

- Microsoft Learn — AD Forest Recovery. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/ad-forest-recovery-guide
- Microsoft Learn — AD DS Backup and Recovery. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/ad-ds-simplified-administration
- Microsoft Learn — AD Recycle Bin. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/adac/introduction-to-active-directory-administrative-center-enhancements--level-100-#ad-recycle-bin
- Microsoft Learn — SYSVOL Replication Migration (FRS to DFSR). https://learn.microsoft.com/en-us/windows-server/storage/dfs-replication/migrate-sysvol-to-dfsr
- Microsoft Learn — Certificate Services Backup and Restore. https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/backup-restore
- Microsoft Learn — Azure AD Connect (Entra Connect) DR. https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-sync-staging-server
- Microsoft Learn — DSRM Password Management. https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-r2-and-2012/cc753343(v=ws.11)
- Microsoft — AD DS Design Guide. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/ad-ds-design-guide
- Semperis — Active Directory Disaster Recovery Best Practices. https://www.semperis.com/resources/
- SANS — Recovering Active Directory from a Compromise. https://www.sans.org/white-papers/


---

## Glossario

| Termine | Definizione |
|---|---|
| **Forest Recovery** | Procedura Microsoft ufficiale per il ripristino completo di una forest AD dopo un disastro catastrofico. Include isolamento, restore del primo DC, metadata cleanup, seize FSMO, e ricostruzione dei DC aggiuntivi. |
| **DSRM** | Directory Services Restore Mode. Modalità di avvio speciale dei DC che ferma il servizio NTDS e permette accesso al database AD per operazioni di manutenzione e restore. |
| **System State** | Insieme di componenti critici del sistema operativo che include AD database, SYSVOL, registry, boot files e COM+ registration. Backuppato con `wbadmin`. |
| **HSM** | Hardware Security Module. Dispositivo fisico per la protezione delle chiavi crittografiche, usato tipicamente per la chiave privata della Root CA. |
| **Authoritative Restore** | Tipo di restore AD che marca gli oggetti ripristinati con un version number più alto, forzando la replica verso gli altri DC. Usato per recuperare oggetti cancellati. |
| **Non-Authoritative Restore** | Tipo di restore AD che ripristina il DC a uno stato precedente e poi lascia che la replica aggiorni il DC con le modifiche recenti dagli altri DC. |
| **Tombstone** | Stato di un oggetto AD cancellato (senza Recycle Bin). L'oggetto perde la maggior parte degli attributi ma mantiene il GUID e pochi dati per 180 giorni prima della purge definitiva. |
| **Deleted Object Lifetime (DOL)** | Periodo durante il quale un oggetto eliminato rimane in stato "Deleted" (con tutti gli attributi) prima di passare a "Recycled". Applicabile solo con AD Recycle Bin abilitato. Default 180 giorni. |
| **AD Recycle Bin** | Feature AD (Windows Server 2008 R2+) che mantiene gli oggetti eliminati con tutti i loro attributi per un periodo configurabile, permettendo un recupero rapido senza DSRM. Irreversibile una volta abilitata. |
| **NTDS.DIT** | File database di Active Directory basato sul motore ESE (Extensible Storage Engine). Contiene tutti gli oggetti AD, attributi, password hash e metadati di replica. Ubicazione default: `%SystemRoot%\NTDS\ntds.dit`. |
| **SYSVOL** | Shared folder sui DC che contiene le Group Policy Objects (GPO) e gli script di logon/logoff. Replicato tra tutti i DC via DFSR (o FRS legacy). |
| **DFSR** | Distributed File System Replication. Servizio di replica file usato per SYSVOL (sostituto di FRS dal 2008 R2). Supporta compressione, scheduling e stato D2/D4 per il recovery. |
| **D2 / D4** | Flag di stato DFSR per il recovery. D2 = non-autoritativo (il DC scarica SYSVOL da un partner). D4 = autoritativo (il DC è la fonte master di SYSVOL). |
| **FRS** | File Replication Service. Servizio legacy di replica file per SYSVOL, deprecato dal 2008 R2 e rimosso in Windows Server 2025. Deve essere migrato a DFSR. |
| **FSMO** | Flexible Single Master Operations. 5 ruoli speciali in una forest AD: Schema Master, Domain Naming Master, RID Master, PDC Emulator, Infrastructure Master. Ciascuno esiste su un singolo DC. |
| **Seize** | Operazione forzata per assumere un ruolo FSMO quando il DC che lo detiene non è più disponibile. Differente dal "transfer" che è cooperativo. |
| **USN Rollback** | Condizione in cui il database AD di un DC torna a un numero di sequenza precedente, causando inconsistenze di replica. Tipicamente causato da restore di snapshot VM su hypervisor vecchi. |
| **VM Generation ID** | Identificatore unico delle VM (Hyper-V 2012+, vSphere 5.0+) che cambia dopo snapshot/restore, permettendo ad AD di rilevare il rollback e proteggere la consistenza. |
| **BMR** | Bare Metal Recovery. Tipo di restore che ripristina l'intero server (OS + dati + System State) su hardware vuoto, senza richiedere un OS pre-installato. |
| **RTO** | Recovery Time Objective. Tempo massimo accettabile per ripristinare un servizio dopo un disastro. Definito per servizio e concordato con il business. |
| **RPO** | Recovery Point Objective. Quantità massima di dati che si accetta di perdere, misurata in tempo (es: RPO 24h = si accetta di perdere fino a 24 ore di modifiche). |
| **CRL** | Certificate Revocation List. Elenco firmato dalla CA dei certificati revocati. Pubblicato su CDP (CRL Distribution Point) e verificato dai client prima di accettare un certificato. |
| **CDP** | CRL Distribution Point. Percorso (HTTP, LDAP, file) dove la CA pubblica le CRL. I client accedono ai CDP per verificare se un certificato è revocato. |
| **OCSP** | Online Certificate Status Protocol. Alternativa alle CRL per la verifica dello stato di revoca dei certificati. Il client interroga un OCSP Responder che risponde in tempo reale. |
| **NTAuthCertificates** | Oggetto AD nella partizione Configuration che contiene i certificati delle CA autorizzate a emettere certificati per autenticazione (smart card, EAP-TLS). |
| **AADConnect** | Azure AD Connect (ora Entra Connect). Tool Microsoft per sincronizzare utenti, gruppi e password tra AD on-premises e Microsoft Entra ID (Azure AD). |
| **Staging Server** | Server AADConnect configurato in modalità read-only che esegue la sincronizzazione senza scrivere in Entra ID. Usato come hot standby per il DR. |
| **krbtgt** | Account di servizio AD usato dal Key Distribution Center (KDC) per firmare i Kerberos Ticket Granting Tickets (TGT). La compromissione di krbtgt permette la creazione di Golden Ticket. |
| **Golden Ticket** | Attacco Kerberos in cui un attaccante usa l'hash di krbtgt per creare TGT arbitrari con qualsiasi privilegio. Richiede reset di krbtgt 2 volte per mitigare. |
| **Metadata Cleanup** | Processo di rimozione dei riferimenti a un DC non più esistente dalla configurazione AD (oggetti server, connection objects, record DNS). Necessario dopo un DC failure permanente. |
| **Runbook** | Documento operativo con procedure passo-passo per gestire un incidente o un'operazione. Deve essere testato, stampato e accessibile offline. |

---

## Esercizi

### Esercizio 1 — Concettuale: RTO/RPO per servizi AD e PKI

Definisci RTO e RPO differenziati per ciascun componente: Domain Controller (PDC Emulator, GC), Enterprise CA, Root CA offline, DNS integrato in AD, SYSVOL. Giustifica le differenze tra i valori scelti in base all'impatto operativo di ciascun servizio.

### Esercizio 2 — Lab: Backup e restore System State di un DC

1. In una VM di lab, configurare un DC con AD DS e almeno 50 oggetti (utenti, gruppi, OU).
2. Eseguire un backup System State con `wbadmin start systemstatebackup`.
3. Eliminare una OU con gli oggetti contenuti.
4. Eseguire un authoritative restore della OU con `ntdsutil` (incrementando la version number).
5. Verificare che la replica propaghi gli oggetti ripristinati agli altri DC.

### Esercizio 3 — Scenario: Forest recovery dopo ransomware

Un ransomware ha compromesso tutti i DC di una forest a 2 domini. L'ultimo backup System State valido è di 18 ore fa. La Root CA offline è intatta. Descrivi la procedura completa: isolamento di rete, restore del primo DC, seize dei ruoli FSMO, reset di krbtgt (2 volte), rebuild degli altri DC, verifica SYSVOL DFSR, e ripristino della catena PKI.

### Esercizio 4 — Design: Piano DR per infrastruttura AD multi-sito

Progetta un piano di disaster recovery per una forest AD con 3 siti (Milano, Roma, Londra), 8 DC, 2 Enterprise CA e 1 Root CA offline. Includi: strategia di backup (frequenza, retention, storage offsite), runbook con ruoli e responsabilità, procedura di test DR trimestrale, e integrazione con Azure Site Recovery per i DC virtualizzati.

---

## Auto-valutazione

<details>
<summary>1. Qual è la differenza tra authoritative e non-authoritative restore in AD?</summary>

**Non-authoritative restore:** ripristina il DC a uno stato precedente dal backup, poi la replica normale aggiorna il DC con le modifiche recenti dagli altri DC. Usato per ripristinare un DC che ha perso il database. **Authoritative restore:** dopo il non-authoritative, si usa `ntdsutil` per incrementare il version number degli oggetti specifici, forzando la replica a propagare quegli oggetti verso gli altri DC. Usato per recuperare oggetti eliminati accidentalmente.
</details>

<details>
<summary>2. Perché la forest recovery richiede l'isolamento di rete totale?</summary>

Se un DC compromesso o con dati corrotti è ancora raggiungibile in rete, può replicare i dati corrotti verso i DC appena ripristinati, re-infettando l'intera forest. L'isolamento garantisce che il primo DC ripristinato sia la sola fonte di verità, e gli altri DC vengano ricostruiti da zero tramite promozione nel forest isolato.
</details>

<details>
<summary>3. Cosa include il System State backup di un Domain Controller?</summary>

Active Directory database (NTDS.DIT), SYSVOL (GPO e script di logon), Registry, boot files, COM+ class registration database, certificate services database (se il DC ospita una CA), e i file protetti da Windows File Protection. Per un DC il System State è l'unico metodo supportato per il backup AD.
</details>

<details>
<summary>4. Come si esegue il backup della chiave privata di una Root CA offline?</summary>

`certutil -backupKey <percorso>` esporta la chiave privata in formato PFX protetto da password. Per CA con HSM, si usa la procedura specifica dell'HSM per estrarre/eseguire il backup della chiave. Il backup deve essere archiviato in almeno 2 ubicazioni fisiche separate, con accesso limitato e documentato.
</details>

<details>
<summary>5. Perché è necessario resettare la password di krbtgt due volte durante una forest recovery?</summary>

L'account krbtgt ha una "password history" di 2 valori. I TGT Kerberos esistenti sono firmati con una delle due password più recenti. Resettando 2 volte, si invalidano tutti i TGT esistenti (inclusi eventuali Golden Ticket creati da un attaccante). Tra i due reset è necessario attendere almeno un ciclo di replica completo.
</details>

<details>
<summary>6. Qual è la differenza tra Tombstone e AD Recycle Bin per il recovery di oggetti?</summary>

Senza Recycle Bin, un oggetto eliminato diventa un **tombstone**: perde quasi tutti gli attributi e mantiene solo il GUID per 180 giorni. Il recovery richiede un authoritative restore da backup. Con **AD Recycle Bin** (abilitato), l'oggetto eliminato mantiene tutti gli attributi nello stato "Deleted" per il Deleted Object Lifetime (180 giorni), permettendo il recupero rapido con `Restore-ADObject` senza DSRM.
</details>

<details>
<summary>7. Come si verifica che SYSVOL sia replicato correttamente dopo un restore?</summary>

`Get-DfsrState` per verificare lo stato DFSR su ogni DC. `dfsrdiag pollad` per forzare un polling immediato. Verificare il contenuto di `\\DC\SYSVOL\<dominio>\Policies\` confrontando le GPO con `Get-GPO -All`. Controllare Event Log DFS Replication (Event ID 4602 = replica completata, 4012 = SYSVOL non pronto). Se necessario, usare i flag D2/D4 per forzare un re-sync.
</details>

---

## Letture primarie consigliate

- Microsoft Learn — AD Forest Recovery Guide. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/ad-forest-recovery-guide (consultato: 2026-05-23)
- Microsoft Learn — Backing Up and Restoring AD DS. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/ad-forest-recovery-backing-up-a-full-server (consultato: 2026-05-23)
- Microsoft Learn — AD CS Backup and Recovery. https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/backup-and-restore-certificate-authority (consultato: 2026-05-23)
- Microsoft Learn — AD Recycle Bin. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/adac/introduction-to-active-directory-administrative-center-enhancements--level-100-#ad_recycle_bin_mgmt (consultato: 2026-05-23)
- Microsoft Learn — DFSR SYSVOL Recovery. https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/dfsr-sysvol-migration (consultato: 2026-05-23)

---

## Collegamenti incrociati

| Modulo | Relazione con questo capitolo |
|---|---|
| [01-active-directory.md](01-active-directory.md) | Fondamenti AD: FSMO, replica, tombstone — prerequisito |
| [25-active-directory-design-avanzato.md](25-active-directory-design-avanzato.md) | Design AD avanzato: tiering, ESAE, multi-domain — complementare |
| [28-pki-certificati-guida-completa.md](28-pki-certificati-guida-completa.md) | PKI e CA: architettura, template, CRL — prerequisito per la sezione PKI DR |
| [15-backup-ripristino.md](15-backup-ripristino.md) | Backup Windows: wbadmin, Windows Server Backup, Azure Backup — complementare |
| [19-troubleshooting.md](19-troubleshooting.md) | Troubleshooting: diagnosi post-restore, verifica servizi, Event Viewer |
