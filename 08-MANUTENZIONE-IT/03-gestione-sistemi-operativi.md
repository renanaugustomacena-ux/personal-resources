# Gestione Sistemi Operativi — Guida Completa

> **Modulo:** Operations IT · Modulo 03 · **Prerequisiti:** Linux/Windows admin (corsi 02, 03)
> **Obiettivi:** patch management, baseline hardening, kernel update strategy
> **Tempo:** 60 min · lab 180 min · **Livello:** competent · **Aggiornamento:** 2026-04-27

## Idee guida

1. **Patch tuesday + emergency channel.** Stress-tested cadence + emergency for zero-day.
2. **Baseline hardening = day 1, NON day 30.** CIS Benchmark applicato post-install.
3. **Kernel update = reboot pianificato.** Live patching (Ubuntu Pro, kpatch) e per HA critici.
4. **Documentare ogni patch + rollback path.**


## Indice

1. [Panoramica](#panoramica)
2. [Manutenzione Windows Server](#manutenzione-windows-server)
   - [Patch Management Windows](#patch-management-windows)
   - [Active Directory Manutenzione](#active-directory-manutenzione)
   - [Group Policy Revisione](#group-policy-revisione)
   - [Servizi Windows](#servizi-windows)
   - [Event Log Analisi](#event-log-analisi)
   - [Performance Tuning](#performance-tuning)
3. [Manutenzione Linux Server](#manutenzione-linux-server)
   - [Patch Management Linux](#patch-management-linux)
   - [Gestione Pacchetti](#gestione-pacchetti)
   - [Kernel Management](#kernel-management)
   - [Servizi systemd](#servizi-systemd)
   - [Log Management](#log-management)
   - [Filesystem Manutenzione](#filesystem-manutenzione)
   - [Gestione Utenti e Permessi](#gestione-utenti-e-permessi)
4. [Patch Management Enterprise (Cross-Platform)](#patch-management-enterprise-cross-platform)
   - [Politica Patch Management](#politica-patch-management)
   - [Ambiente di Test](#ambiente-di-test)
   - [Automazione Distribuzione](#automazione-distribuzione)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Panoramica

La gestione dei sistemi operativi rappresenta il pilastro fondamentale di qualsiasi strategia di manutenzione IT. In un ambiente di produzione moderno, la coesistenza di infrastrutture eterogenee basate su Windows Server e distribuzioni Linux Server richiede competenze trasversali, procedure consolidate e automazione pervasiva.

Questa guida copre l'intero ciclo di vita della manutenzione dei sistemi operativi: dall'applicazione delle patch di sicurezza alla gestione dei servizi di directory, dal tuning delle prestazioni alla manutenzione proattiva dei filesystem. L'obiettivo non e' semplicemente mantenere i server funzionanti, ma garantire che operino al massimo livello di sicurezza, stabilita' e prestazioni.

Un ambiente enterprise tipico comprende server Windows per i servizi di directory (Active Directory), file server, applicazioni aziendali e infrastruttura di rete (DNS, DHCP), affiancati da server Linux per web hosting, database, container orchestration e servizi DevOps. La manutenzione di entrambi i mondi richiede approcci differenti ma una filosofia comune: prevenzione, automazione, monitoraggio continuo e documentazione rigorosa.

Le attivita' descritte in questa guida devono essere integrate in un calendario di manutenzione strutturato, con finestre di intervento pianificate, procedure di rollback testate e metriche di conformita' misurabili. Ogni intervento deve essere tracciabile, ripetibile e verificabile.

---

## Manutenzione Windows Server

### Patch Management Windows

La gestione delle patch in ambiente Windows Server e' un processo critico che, se trascurato, espone l'infrastruttura a vulnerabilita' note, instabilita' e non conformita' normativa. Microsoft rilascia aggiornamenti con cadenza mensile (Patch Tuesday, il secondo martedi' di ogni mese) oltre a rilasci fuori banda per vulnerabilita' critiche attivamente sfruttate.

#### Configurazione e Manutenzione WSUS

Windows Server Update Services (WSUS) rimane lo strumento principale per la gestione centralizzata degli aggiornamenti in ambienti on-premises. La configurazione ottimale prevede:

**Architettura WSUS consigliata:**
- Un server WSUS upstream connesso a Microsoft Update per la sincronizzazione
- Server WSUS downstream nelle sedi remote per la distribuzione locale
- Database WSUS su SQL Server (non WID) per ambienti con oltre 500 client
- Disco dedicato per il content store con almeno 100 GB di spazio libero

**Sincronizzazione e classificazioni:**
Configurare la sincronizzazione automatica nelle ore notturne. Selezionare esclusivamente le classificazioni necessarie: Critical Updates, Security Updates, Definition Updates e Service Packs. Evitare di sincronizzare Driver Updates a meno che non sia esplicitamente necessario, poiche' appesantiscono enormemente il database e lo storage.

```powershell
# Verificare lo stato della sincronizzazione WSUS
Get-WsusServer | Get-WsusSubscription | Select-Object LastSynchronizationTime, SynchronizationStatus

# Forzare una sincronizzazione manuale
$wsus = Get-WsusServer
$subscription = $wsus.GetSubscription()
$subscription.StartSynchronization()
```

**Manutenzione del database WSUS:**
Il database WSUS tende a crescere in modo significativo e richiede manutenzione regolare. Eseguire mensilmente:

```powershell
# Pulizia WSUS completa tramite PowerShell
Invoke-WsusServerCleanup -CleanupObsoleteUpdates -CleanupUnneededContentFiles -CompressUpdates -DeclineExpiredUpdates -DeclineSupersededUpdates

# Verifica dimensione database WID
Get-Item "C:\Windows\WID\Data\SUSDB.mdf" | Select-Object Name, @{N='SizeGB';E={[math]::Round($_.Length/1GB,2)}}
```

Eseguire periodicamente lo script di manutenzione indici SQL `WsusDBMaintenance.sql` fornito da Microsoft per la re-indicizzazione e la ricostruzione delle statistiche.

#### Windows Update for Business

Per ambienti ibridi o cloud-first, Windows Update for Business (WUfB) gestito tramite Microsoft Intune offre un'alternativa moderna a WSUS. La configurazione avviene tramite policy di conformita' che definiscono i tempi di differimento per feature update e quality update.

I vantaggi principali includono: nessuna infrastruttura on-premises da mantenere, integrazione nativa con il cloud Microsoft, reporting centralizzato tramite Update Compliance in Azure Monitor.

#### Ciclo Patch Tuesday e Ring-Based Deployment

Il modello di distribuzione basato su ring (anelli) e' fondamentale per mitigare il rischio di aggiornamenti problematici:

| Ring | Scopo | Tempistica | Popolazione |
|------|-------|------------|-------------|
| **Ring 0 — Test** | Validazione iniziale su ambienti non produttivi | Patch Tuesday + 1 giorno | Lab/Dev server |
| **Ring 1 — Pilot** | Test su un campione rappresentativo di produzione | Patch Tuesday + 3 giorni | 5-10% dei server prod |
| **Ring 2 — Production** | Distribuzione su tutti i server di produzione | Patch Tuesday + 7 giorni | 80-85% dei server prod |
| **Ring 3 — Critical** | Server mission-critical con finestre di manutenzione dedicate | Patch Tuesday + 14 giorni | Server critici rimanenti |

Ogni passaggio al ring successivo e' subordinato alla validazione positiva del ring precedente. Documentare e comunicare sempre i risultati di ogni fase.

#### Comandi PowerShell per Gestione Aggiornamenti

```powershell
# Installare il modulo PSWindowsUpdate (se non presente)
Install-Module -Name PSWindowsUpdate -Force

# Verificare aggiornamenti disponibili
Get-WindowsUpdate -MicrosoftUpdate

# Installare tutti gli aggiornamenti disponibili con reboot automatico
Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -AutoReboot

# Installare solo aggiornamenti di sicurezza
Get-WindowsUpdate -Category "Security Updates" | Install-WindowsUpdate -AcceptAll

# Verificare cronologia aggiornamenti installati
Get-WUHistory | Select-Object Date, Title, Result | Sort-Object Date -Descending | Select-Object -First 20

# Verificare aggiornamenti in sospeso che richiedono reboot
Get-WURebootStatus

# Report di conformita' per tutti i server del dominio
$servers = Get-ADComputer -Filter {OperatingSystem -like "*Server*"} | Select-Object -ExpandProperty Name
$servers | ForEach-Object {
    Invoke-Command -ComputerName $_ -ScriptBlock {
        Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5
    } -ErrorAction SilentlyContinue
}
```

#### Compliance Reporting

Generare report di conformita' settimanali che includano: percentuale di server aggiornati per ring, elenco dei server non conformi con motivazione, tempo medio di applicazione delle patch dalla data di rilascio, eccezioni attive e relative scadenze. Questi report devono essere condivisi con il responsabile della sicurezza IT e archiviati per audit di conformita'.

---

### Active Directory Manutenzione

Active Directory (AD) e' il servizio di directory fondamentale per l'autenticazione, l'autorizzazione e la gestione centralizzata in ambienti Windows. La sua manutenzione richiede attenzione costante per garantire la replica tra domain controller, l'integrita' del database e l'igiene degli oggetti.

#### Verifica della Replica AD

La replica e' il meccanismo vitale che mantiene sincronizzati i domain controller. Un problema di replica non rilevato puo' causare inconsistenze nell'autenticazione, lockout multipli e perdita di modifiche alle policy.

```powershell
# Riepilogo completo della replica tra tutti i DC
repadmin /replsummary

# Visualizzare lo stato dettagliato della replica per ogni DC
repadmin /showrepl

# Mostrare eventuali errori di replica
repadmin /failcache

# Forzare la replica tra due DC specifici
repadmin /replicate DC02 DC01 "DC=contoso,DC=local"

# Diagnostica completa del domain controller
dcdiag /v /c /d /e /s:DC01

# Test specifici di dcdiag
dcdiag /test:replications
dcdiag /test:dns /DnsDelegation
dcdiag /test:fsmocheck
dcdiag /test:ridmanager
```

Pianificare l'esecuzione automatizzata di `dcdiag` e `repadmin /replsummary` con cadenza giornaliera, inviando i risultati via email o integrandoli nel sistema di monitoraggio centralizzato.

#### Verifica Ruoli FSMO

I cinque ruoli FSMO (Flexible Single Master Operations) devono essere assegnati a domain controller raggiungibili e performanti. Verificare mensilmente la loro distribuzione:

```powershell
# Visualizzare tutti i ruoli FSMO
netdom query fsmo

# Alternativa con PowerShell
Get-ADForest | Select-Object DomainNamingMaster, SchemaMaster
Get-ADDomain | Select-Object InfrastructureMaster, PDCEmulator, RIDMaster
```

Documentare su quale DC risiede ogni ruolo e avere una procedura testata per il trasferimento (transfer) e il sequestro (seize) dei ruoli in caso di emergenza.

#### Tombstone Lifetime e AD Recycle Bin

Il tombstone lifetime (per default 180 giorni nelle foreste moderne) determina per quanto tempo un oggetto eliminato rimane nel database prima della rimozione definitiva. Verificare che sia configurato correttamente:

```powershell
# Verificare il tombstone lifetime
Get-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=contoso,DC=local" -Properties tombstoneLifetime

# Verificare che il Recycle Bin di AD sia abilitato
Get-ADOptionalFeature -Filter 'Name -like "Recycle*"'

# Abilitare il Recycle Bin (operazione irreversibile)
Enable-ADOptionalFeature 'Recycle Bin Feature' -Scope ForestOrConfigurationSet -Target 'contoso.local'

# Recuperare un oggetto eliminato dal Recycle Bin
Get-ADObject -Filter 'isDeleted -eq $true -and Name -like "*Mario Rossi*"' -IncludeDeletedObjects | Restore-ADObject
```

#### Manutenzione del Database AD (NTDS)

Il database di Active Directory (ntds.dit) richiede manutenzione periodica per mantenere prestazioni ottimali:

```powershell
# Verificare dimensione e integrita' del database (eseguire in DSRM o con DC arrestato)
ntdsutil
  activate instance ntds
  files
  info
  integrity
  quit
  quit

# Deframmentazione offline (richiede DC offline o in DSRM)
ntdsutil
  activate instance ntds
  files
  compact to C:\Temp\NTDS
  quit
  quit
```

La deframmentazione online avviene automaticamente ogni 12 ore tramite il processo di garbage collection. Monitorare l'Event ID 1646 (garbage collection completata) nel log Directory Services.

#### Pulizia Oggetti Obsoleti

Gli oggetti stale (computer e utenti inattivi) rappresentano un rischio di sicurezza e appesantiscono la directory:

```powershell
# Trovare computer inattivi da oltre 90 giorni
$threshold = (Get-Date).AddDays(-90)
Get-ADComputer -Filter {LastLogonDate -lt $threshold} -Properties LastLogonDate |
    Select-Object Name, LastLogonDate, DistinguishedName |
    Sort-Object LastLogonDate

# Trovare utenti inattivi da oltre 90 giorni
Search-ADAccount -AccountInactive -TimeSpan 90.00:00:00 -UsersOnly |
    Select-Object Name, LastLogonDate, Enabled |
    Sort-Object LastLogonDate

# Trovare utenti con password scaduta
Search-ADAccount -PasswordExpired -UsersOnly |
    Select-Object Name, PasswordLastSet

# Disabilitare account inattivi (prima di eliminarli)
Get-ADComputer -Filter {LastLogonDate -lt $threshold} |
    Set-ADComputer -Enabled $false -Description "Disabilitato per inattivita' $(Get-Date -Format 'yyyy-MM-dd')"
```

Implementare una procedura mensile: identificare gli oggetti inattivi, notificare i responsabili, disabilitare dopo conferma, spostare in una OU dedicata ("Da Eliminare"), eliminare dopo 30 giorni ulteriori.

#### Verifica Trust Relationship e DNS Health

```powershell
# Verificare le relazioni di trust
Get-ADTrust -Filter * | Select-Object Name, Direction, TrustType, IntraForest

# Testare il trust
nltest /domain_trusts /all_trusts /v

# Verifica DNS integrato con AD
dcdiag /test:dns /v /e

# Verificare le zone DNS integrate con AD
Get-DnsServerZone | Where-Object {$_.ZoneType -eq 'Primary' -and $_.IsDsIntegrated}

# Verificare i record SRV critici per AD
nslookup -type=srv _ldap._tcp.dc._msdcs.contoso.local
nslookup -type=srv _kerberos._tcp.dc._msdcs.contoso.local
```

---

### Group Policy Revisione

Le Group Policy Object (GPO) sono il meccanismo principale per applicare configurazioni di sicurezza e gestione a utenti e computer del dominio. Un ambiente con GPO non documentate, obsolete o in conflitto genera problemi di prestazioni e sicurezza.

#### Inventario e Documentazione GPO

```powershell
# Elenco completo di tutte le GPO nel dominio
Get-GPO -All | Select-Object DisplayName, Id, GpoStatus, CreationTime, ModificationTime |
    Sort-Object DisplayName | Format-Table -AutoSize

# Esportare report HTML dettagliato di ogni GPO
$reportPath = "C:\GPO-Reports"
New-Item -Path $reportPath -ItemType Directory -Force
Get-GPO -All | ForEach-Object {
    Get-GPOReport -Guid $_.Id -ReportType HTML -Path "$reportPath\$($_.DisplayName).html"
}

# Backup completo di tutte le GPO
$backupPath = "C:\GPO-Backup\$(Get-Date -Format 'yyyy-MM-dd')"
New-Item -Path $backupPath -ItemType Directory -Force
Backup-GPO -All -Path $backupPath
```

#### Pulizia GPO Orfane

Le GPO orfane sono quelle non collegate a nessuna OU o sito, oppure quelle con impostazioni vuote:

```powershell
# Trovare GPO non collegate a nessuna OU
$allGPOs = Get-GPO -All
$linkedGPOs = @()
Get-ADOrganizationalUnit -Filter * | ForEach-Object {
    (Get-GPInheritance -Target $_.DistinguishedName).GpoLinks | ForEach-Object {
        $linkedGPOs += $_.GpoId
    }
}
$orphanedGPOs = $allGPOs | Where-Object { $_.Id -notin $linkedGPOs }
$orphanedGPOs | Select-Object DisplayName, CreationTime, ModificationTime

# Trovare GPO con tutte le sezioni disabilitate o vuote
Get-GPO -All | Where-Object { $_.GpoStatus -eq 'AllSettingsDisabled' } |
    Select-Object DisplayName, GpoStatus
```

#### Validazione RSOP (Resultant Set of Policy)

Per verificare l'effettiva applicazione delle policy su un computer o utente specifico:

```powershell
# Generare report RSOP per un computer specifico
Get-GPResultantSetOfPolicy -Computer "PC-CONTABILITA01" -ReportType HTML -Path "C:\RSOP-Report.html"

# Modellazione "what-if" per simulare spostamento di un computer
# (disponibile tramite GPMC GUI: Group Policy Modeling)

# Verificare la versione delle GPO applicate su un client remoto
Invoke-Command -ComputerName "PC-CONTABILITA01" -ScriptBlock {
    gpresult /r /scope:computer
}
```

#### Pianificazione Backup GPO

Implementare un backup automatizzato settimanale tramite Scheduled Task che esegua il backup completo di tutte le GPO, mantenendo le ultime 4 versioni. Archiviare i backup su un file share dedicato con accesso limitato ai soli amministratori di dominio.

---

### Servizi Windows

I servizi Windows sono componenti critici che garantiscono il funzionamento dell'infrastruttura. La loro manutenzione proattiva previene interruzioni non pianificate.

#### Lista Servizi Critici da Monitorare

| Servizio | Nome Servizio | Impatto se non disponibile |
|----------|--------------|---------------------------|
| Active Directory Domain Services | NTDS | Autenticazione dominio impossibile |
| DNS Server | DNS | Risoluzione nomi non funzionante |
| DHCP Server | DHCPServer | Nessun indirizzo IP ai client |
| Kerberos Key Distribution Center | Kdc | Autenticazione Kerberos fallita |
| Windows Time | W32Time | Desincronizzazione orario, impatto su Kerberos |
| DFS Replication | DFSR | Replica file shares interrotta |
| Group Policy Client | gpsvc | Policy non applicate ai client |
| Print Spooler | Spooler | Stampa non disponibile |
| IIS (W3SVC) | W3SVC | Applicazioni web non raggiungibili |
| SQL Server | MSSQLSERVER | Database non disponibile |

```powershell
# Verificare lo stato di tutti i servizi critici
$criticalServices = @('NTDS','DNS','DHCPServer','Kdc','W32Time','DFSR','W3SVC','Spooler')
$criticalServices | ForEach-Object {
    Get-Service -Name $_ -ErrorAction SilentlyContinue |
    Select-Object Name, DisplayName, Status, StartType
}

# Configurare il recovery automatico per un servizio
sc.exe failure DNS reset= 86400 actions= restart/60000/restart/120000/restart/300000
```

#### Gestione Service Account

Gli account di servizio devono essere gestiti con attenzione per la sicurezza:

```powershell
# Trovare tutti i servizi in esecuzione con account specifici (non LocalSystem)
Get-WmiObject Win32_Service | Where-Object {
    $_.StartName -ne 'LocalSystem' -and $_.StartName -ne 'NT AUTHORITY\LocalService' -and
    $_.StartName -ne 'NT AUTHORITY\NetworkService'
} | Select-Object Name, DisplayName, StartName, State

# Verificare i Group Managed Service Accounts (gMSA)
Get-ADServiceAccount -Filter * | Select-Object Name, Enabled, HostComputers
```

Migrare progressivamente tutti i service account tradizionali a Group Managed Service Accounts (gMSA) per eliminare la gestione manuale delle password.

#### Audit delle Scheduled Task

```powershell
# Elencare tutte le scheduled task non Microsoft su tutti i server
$servers = Get-ADComputer -Filter {OperatingSystem -like "*Server*"} -Properties Name
$servers | ForEach-Object {
    Invoke-Command -ComputerName $_.Name -ScriptBlock {
        Get-ScheduledTask | Where-Object {$_.TaskPath -notlike '\Microsoft\*'} |
        Select-Object TaskName, TaskPath, State, @{N='Computer';E={$env:COMPUTERNAME}}
    } -ErrorAction SilentlyContinue
}
```

---

### Event Log Analisi

I log eventi di Windows sono una fonte preziosa di informazioni diagnostiche. Sapere quali Event ID monitorare e' essenziale per la rilevazione proattiva dei problemi.

#### Event ID Critici da Monitorare

| Event ID | Log | Sorgente | Significato |
|----------|-----|----------|-------------|
| 1074 | System | User32 | Riavvio o arresto pianificato del sistema |
| 6008 | System | EventLog | Arresto imprevisto del sistema (crash) |
| 7031 | System | Service Control Manager | Servizio terminato inaspettatamente |
| 7034 | System | Service Control Manager | Servizio terminato inaspettatamente (ripetuto) |
| 1001 | Application | Windows Error Reporting | Errore applicazione (crash dump) |
| 4625 | Security | Microsoft-Windows-Security-Auditing | Tentativo di logon fallito |
| 4740 | Security | Microsoft-Windows-Security-Auditing | Account utente bloccato (lockout) |
| 4771 | Security | Microsoft-Windows-Security-Auditing | Pre-autenticazione Kerberos fallita |
| 4776 | Security | Microsoft-Windows-Security-Auditing | Validazione credenziali NTLM |
| 1644 | Directory Service | NTDS | Query LDAP lente (richiede attivazione) |
| 2887 | Directory Service | NTDS | Bind LDAP in chiaro (rischio sicurezza) |
| 1128/1129 | Directory Service | NTDS | Replica AD riuscita/fallita |
| 36874 | System | Schannel | Errori TLS/SSL |
| 1014 | System | DNS Client | Timeout risoluzione DNS |
| 51 | System | Disk | Errore di scrittura disco (possibile guasto) |

```powershell
# Cercare arresti imprevisti nelle ultime 48 ore
Get-WinEvent -FilterHashtable @{LogName='System'; Id=6008; StartTime=(Get-Date).AddHours(-48)}

# Cercare tentativi di logon falliti nelle ultime 24 ore
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625; StartTime=(Get-Date).AddHours(-24)} |
    Select-Object TimeCreated, @{N='Account';E={$_.Properties[5].Value}}, @{N='Source';E={$_.Properties[18].Value}}

# Cercare account bloccati
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4740; StartTime=(Get-Date).AddHours(-24)} |
    Select-Object TimeCreated, @{N='Account';E={$_.Properties[0].Value}}, @{N='CallerComputer';E={$_.Properties[1].Value}}

# Cercare servizi crashati
Get-WinEvent -FilterHashtable @{LogName='System'; Id=7031,7034; StartTime=(Get-Date).AddDays(-7)} |
    Select-Object TimeCreated, Message
```

#### Gestione Dimensione Log

Configurare la dimensione massima dei log e la politica di retention:

```powershell
# Impostare dimensione massima Security Log a 1 GB
wevtutil sl Security /ms:1073741824

# Impostare retention mode: sovrascrivere quando pieno
wevtutil sl Security /rt:false

# Esportare e archiviare i log prima della rotazione
wevtutil epl Security "C:\LogArchive\Security-$(Get-Date -Format 'yyyyMMdd').evtx"
```

---

### Performance Tuning

L'ottimizzazione delle prestazioni dei server Windows richiede un approccio metodico basato su dati oggettivi.

#### Metodologia di Monitoraggio Risorse

Utilizzare Performance Monitor (perfmon) per raccogliere baseline e identificare colli di bottiglia:

```powershell
# Contatori chiave da monitorare
# CPU
(Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
# Memoria
(Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue
(Get-Counter '\Memory\Pages/sec').CounterSamples.CookedValue
# Disco
(Get-Counter '\PhysicalDisk(_Total)\Avg. Disk Queue Length').CounterSamples.CookedValue
(Get-Counter '\PhysicalDisk(_Total)\% Disk Time').CounterSamples.CookedValue
# Rete
(Get-Counter '\Network Interface(*)\Bytes Total/sec').CounterSamples

# Creare un Data Collector Set per monitoraggio continuo (24 ore)
logman create counter PerfBaseline -cf "C:\PerfCounters.txt" -si 15 -f csv -o "C:\PerfLogs\Baseline" -v mmddhhmm --duration 24:00:00
```

#### Ottimizzazione Memoria

- Verificare che il file di paging sia dimensionato correttamente (1.5x la RAM fisica per server fino a 32 GB, dimensione fissa per server con piu' RAM)
- Monitorare il pool non-paged per individuare driver o applicazioni con memory leak
- Disabilitare servizi e funzionalita' non necessari per liberare memoria

#### Ottimizzazione Disco I/O

- Verificare l'allineamento delle partizioni su SSD/NVMe
- Separare i dati delle applicazioni (SQL data, Exchange database) dai log delle transazioni su dischi fisici differenti
- Configurare il power plan su "High Performance" per server fisici
- Monitorare la latenza disco: valori superiori a 20ms per operazioni di lettura o 25ms per scrittura indicano un collo di bottiglia

#### Ottimizzazione Rete

```powershell
# Verificare le impostazioni NIC (offloading, RSS, jumbo frames)
Get-NetAdapterAdvancedProperty | Where-Object {$_.DisplayName -match 'Offload|RSS|Jumbo'}

# Verificare errori e scarti sulle interfacce di rete
Get-NetAdapterStatistics | Select-Object Name, ReceivedUnicastPackets, OutboundDiscardedPackets, InboundErrors

# Verificare la configurazione del team NIC
Get-NetLbfoTeam
Get-NetLbfoTeamMember
```

---

## Manutenzione Linux Server

### Patch Management Linux

La gestione degli aggiornamenti su server Linux varia significativamente in base alla distribuzione utilizzata, ma i principi fondamentali restano invariati: applicare tempestivamente le patch di sicurezza, testare gli aggiornamenti prima della produzione e mantenere la possibilita' di rollback.

#### Workflow Debian/Ubuntu (apt)

```bash
# Aggiornare l'indice dei pacchetti
sudo apt update

# Visualizzare gli aggiornamenti disponibili
apt list --upgradable

# Visualizzare solo gli aggiornamenti di sicurezza
sudo apt list --upgradable 2>/dev/null | grep -i security

# Installare solo gli aggiornamenti di sicurezza
sudo apt-get -s dist-upgrade | grep "^Inst" | grep -i securi
sudo unattended-upgrade --dry-run -d

# Applicare tutti gli aggiornamenti (senza rimuovere pacchetti)
sudo apt upgrade -y

# Applicare tutti gli aggiornamenti (incluse le dipendenze che richiedono rimozioni)
sudo apt full-upgrade -y

# Verificare se e' necessario un riavvio
[ -f /var/run/reboot-required ] && echo "RIAVVIO NECESSARIO" || echo "Nessun riavvio richiesto"
cat /var/run/reboot-required.pkgs 2>/dev/null
```

#### Workflow RHEL/CentOS/Rocky (yum/dnf)

```bash
# Verificare aggiornamenti disponibili
sudo dnf check-update

# Verificare aggiornamenti di sicurezza
sudo dnf updateinfo list security

# Installare solo aggiornamenti di sicurezza
sudo dnf update --security -y

# Installare tutti gli aggiornamenti
sudo dnf update -y

# Visualizzare cronologia degli aggiornamenti
sudo dnf history list
sudo dnf history info <ID>

# Rollback di un aggiornamento specifico
sudo dnf history undo <ID>

# Verificare se e' necessario un riavvio (needs-restarting)
sudo needs-restarting -r
```

#### Configurazione Unattended Upgrades (Debian/Ubuntu)

Per garantire che le patch di sicurezza critiche vengano applicate automaticamente:

```bash
# Installare il pacchetto
sudo apt install unattended-upgrades apt-listchanges

# Configurare /etc/apt/apt.conf.d/50unattended-upgrades
# Abilitare solo gli aggiornamenti di sicurezza:
# Unattended-Upgrade::Allowed-Origins {
#     "${distro_id}:${distro_codename}-security";
# };
# Unattended-Upgrade::Automatic-Reboot "false";
# Unattended-Upgrade::Mail "admin@azienda.it";

# Abilitare l'esecuzione automatica
sudo dpkg-reconfigure -plow unattended-upgrades

# Testare la configurazione
sudo unattended-upgrade --dry-run --debug
```

#### Gestione Aggiornamenti Kernel

Gli aggiornamenti del kernel richiedono attenzione particolare poiche' necessitano di un riavvio per entrare in vigore:

```bash
# Verificare il kernel attualmente in uso
uname -r

# Verificare i kernel installati (Debian/Ubuntu)
dpkg --list | grep linux-image

# Verificare i kernel installati (RHEL/CentOS)
rpm -qa | grep kernel

# Pianificare il riavvio dopo un aggiornamento kernel
# Utilizzare sempre una finestra di manutenzione pianificata
sudo shutdown -r 02:00 "Riavvio pianificato per aggiornamento kernel"
```

---

### Gestione Pacchetti

La corretta gestione dei repository e dei pacchetti software garantisce la stabilita' e la sicurezza del sistema.

#### Gestione Repository

```bash
# Debian/Ubuntu - Elencare tutti i repository configurati
apt-cache policy
grep -r "^deb " /etc/apt/sources.list /etc/apt/sources.list.d/

# RHEL/CentOS - Elencare tutti i repository
dnf repolist all

# Verificare la validita' delle chiavi GPG dei repository
apt-key list          # Debian/Ubuntu (deprecato, usare /etc/apt/trusted.gpg.d/)
rpm -qa gpg-pubkey*   # RHEL/CentOS
```

Rimuovere o disabilitare i repository di terze parti non piu' necessari. Ogni repository aggiuntivo aumenta la superficie di attacco e il rischio di conflitti tra pacchetti.

#### Package Hold/Pin

Per impedire l'aggiornamento automatico di pacchetti specifici (ad esempio quando una versione specifica e' richiesta da un'applicazione):

```bash
# Debian/Ubuntu - Bloccare un pacchetto
sudo apt-mark hold nginx
apt-mark showhold

# RHEL/CentOS - Escludere un pacchetto dagli aggiornamenti
# In /etc/dnf/dnf.conf aggiungere:
# exclude=nginx*

# Oppure tramite il plugin versionlock
sudo dnf install dnf-plugin-versionlock
sudo dnf versionlock add nginx
sudo dnf versionlock list
```

#### Pulizia

```bash
# Debian/Ubuntu
sudo apt autoremove -y          # Rimuovere pacchetti orfani
sudo apt autoclean              # Pulire la cache dei pacchetti vecchi
sudo apt clean                  # Pulire tutta la cache

# RHEL/CentOS
sudo dnf autoremove -y
sudo dnf clean all

# Verificare lo spazio occupato dalla cache
du -sh /var/cache/apt/archives/   # Debian/Ubuntu
du -sh /var/cache/dnf/            # RHEL/CentOS
```

---

### Kernel Management

Il kernel Linux e' il cuore del sistema operativo e la sua gestione richiede competenze specifiche.

#### Kernel Attuale e Disponibili

```bash
# Kernel in esecuzione
uname -r
uname -a

# Tutti i kernel installati
dpkg --list | grep linux-image    # Debian/Ubuntu
rpm -qa | grep kernel-core        # RHEL/CentOS

# Kernel di avvio predefinito
grubby --default-kernel           # RHEL/CentOS
```

#### Tuning Parametri Kernel (sysctl)

I parametri kernel controllano il comportamento del sistema a livello fondamentale:

```bash
# Visualizzare tutti i parametri correnti
sysctl -a

# Parametri comuni da ottimizzare per server di produzione

# Rete - Aumentare il buffer TCP per reti ad alta velocita'
sudo sysctl -w net.core.rmem_max=16777216
sudo sysctl -w net.core.wmem_max=16777216
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sudo sysctl -w net.ipv4.tcp_wmem="4096 87380 16777216"

# Sicurezza - Disabilitare il forwarding IP (se non e' un router)
sudo sysctl -w net.ipv4.ip_forward=0

# Sicurezza - Protezione SYN flood
sudo sysctl -w net.ipv4.tcp_syncookies=1

# Memoria - Configurare lo swappiness (valori bassi per server database)
sudo sysctl -w vm.swappiness=10

# Filesystem - Aumentare il limite di inotify watches
sudo sysctl -w fs.inotify.max_user_watches=524288

# Rendere permanenti le modifiche
# Aggiungere i parametri in /etc/sysctl.d/99-tuning.conf
sudo sysctl -p /etc/sysctl.d/99-tuning.conf
```

#### Pulizia Vecchi Kernel

I vecchi kernel occupano spazio su disco e possono confondere il bootloader:

```bash
# Debian/Ubuntu - Rimuovere i vecchi kernel mantenendo l'attuale e il precedente
sudo apt autoremove --purge

# RHEL/CentOS - Configurare il numero di kernel da mantenere
# In /etc/dnf/dnf.conf: installonly_limit=3
sudo dnf remove $(dnf repoquery --installonly --latest-limit=-2 -q)
```

#### DKMS e Moduli Kernel

I moduli DKMS (Dynamic Kernel Module Support) vengono ricompilati automaticamente per ogni nuovo kernel:

```bash
# Verificare lo stato dei moduli DKMS
dkms status

# Ricompilare manualmente un modulo per un kernel specifico
sudo dkms install -m <modulo> -v <versione> -k <versione-kernel>
```

#### Livepatch/kpatch

Per applicare patch di sicurezza al kernel senza riavvio:

```bash
# Ubuntu - Canonical Livepatch
sudo snap install canonical-livepatch
sudo canonical-livepatch enable <token>
canonical-livepatch status --verbose

# RHEL - kpatch
sudo dnf install kpatch
sudo kpatch list
```

---

### Servizi systemd

systemd e' il sistema di init e gestione dei servizi standard nelle distribuzioni Linux moderne.

#### Audit Servizi

```bash
# Elencare tutti i servizi con il loro stato
systemctl list-units --type=service --all

# Trovare tutti i servizi in stato "failed"
systemctl --failed

# Informazioni dettagliate su un servizio specifico
systemctl status nginx.service
journalctl -u nginx.service --since "1 hour ago"

# Elencare i servizi abilitati all'avvio
systemctl list-unit-files --type=service --state=enabled

# Verificare le dipendenze di un servizio
systemctl list-dependencies sshd.service
```

#### Rilevamento e Risoluzione Servizi Falliti

```bash
# Script di rilevamento servizi falliti
#!/bin/bash
FAILED=$(systemctl --failed --no-legend --no-pager | awk '{print $1}')
if [ -n "$FAILED" ]; then
    echo "ATTENZIONE: Servizi in stato failed:"
    echo "$FAILED"
    for svc in $FAILED; do
        echo "--- Ultimi log per $svc ---"
        journalctl -u "$svc" --no-pager -n 20
    done
fi

# Resettare lo stato di un servizio fallito dopo la correzione
sudo systemctl reset-failed nginx.service
sudo systemctl restart nginx.service
```

#### Audit Timer systemd

I timer systemd sono l'equivalente moderno dei cron job:

```bash
# Elencare tutti i timer attivi
systemctl list-timers --all

# Verificare lo stato di un timer specifico
systemctl status logrotate.timer
systemctl cat logrotate.timer
```

#### Limiti Risorse (cgroups)

systemd integra nativamente i cgroups per limitare le risorse dei servizi:

```bash
# Verificare i limiti di risorse di un servizio
systemctl show nginx.service | grep -E 'Memory|CPU|Tasks'

# Impostare limiti di memoria per un servizio
sudo systemctl set-property nginx.service MemoryMax=512M
sudo systemctl set-property nginx.service CPUQuota=50%

# Verificare l'utilizzo corrente delle risorse
systemd-cgtop
```

#### Hardening dei Servizi

Verificare le direttive di sicurezza nei file unit:

```bash
# Analizzare il livello di sicurezza di un servizio
systemd-analyze security nginx.service

# Direttive di hardening raccomandate per i servizi:
# ProtectSystem=strict
# ProtectHome=true
# PrivateTmp=true
# NoNewPrivileges=true
# ReadOnlyPaths=/
# ReadWritePaths=/var/lib/nginx
```

---

### Log Management

La gestione centralizzata e strutturata dei log e' fondamentale per la diagnostica, la sicurezza e la conformita' normativa.

#### Configurazione journald

```bash
# Configurazione in /etc/systemd/journald.conf
# [Journal]
# Storage=persistent          # Persistenza su disco (default: auto)
# SystemMaxUse=2G             # Spazio massimo su disco
# SystemKeepFree=1G           # Spazio minimo da mantenere libero
# SystemMaxFileSize=128M      # Dimensione massima per singolo file
# MaxRetentionSec=3month      # Retention massima
# Compress=yes                # Compressione

# Applicare le modifiche
sudo systemctl restart systemd-journald

# Verificare lo spazio utilizzato dal journal
journalctl --disk-usage

# Pulire i log piu' vecchi di 30 giorni
sudo journalctl --vacuum-time=30d

# Pulire mantenendo solo 1 GB
sudo journalctl --vacuum-size=1G
```

#### Log Rotation (logrotate)

```bash
# Configurazione principale: /etc/logrotate.conf
# Configurazioni per applicazione: /etc/logrotate.d/

# Esempio configurazione per un'applicazione personalizzata
# /etc/logrotate.d/myapp
# /var/log/myapp/*.log {
#     daily
#     missingok
#     rotate 14
#     compress
#     delaycompress
#     notifempty
#     create 0640 www-data adm
#     sharedscripts
#     postrotate
#         systemctl reload myapp 2>/dev/null || true
#     endscript
# }

# Testare la configurazione di logrotate
sudo logrotate -d /etc/logrotate.conf

# Forzare l'esecuzione di logrotate
sudo logrotate -f /etc/logrotate.conf
```

#### File di Log Critici da Monitorare

| File di Log | Contenuto | Cosa Cercare |
|-------------|-----------|--------------|
| `/var/log/syslog` (Debian) o `/var/log/messages` (RHEL) | Log di sistema generale | Errori hardware, servizi, kernel panic |
| `/var/log/auth.log` (Debian) o `/var/log/secure` (RHEL) | Autenticazione | Tentativi di login falliti, escalation privilegi |
| `/var/log/kern.log` | Messaggi kernel | Errori hardware, OOM killer, filesystem errors |
| `/var/log/dmesg` | Boot e hardware | Errori dispositivi, driver failure |
| `/var/log/apt/history.log` o `/var/log/dnf.log` | Gestione pacchetti | Installazioni, aggiornamenti, rimozioni |
| `/var/log/cron` | Cron jobs | Job falliti, esecuzioni non previste |
| `/var/log/mail.log` | Server email | Errori invio/ricezione, spam |
| `/var/log/nginx/error.log` | Web server | Errori 5xx, timeout, upstream failure |

#### Logging Centralizzato

Per ambienti con piu' server, implementare una soluzione di logging centralizzato:

```bash
# Configurare rsyslog per l'invio a un server centrale
# In /etc/rsyslog.d/50-remote.conf:
# *.* @@logserver.azienda.local:514    # TCP
# *.* @logserver.azienda.local:514     # UDP

# Oppure utilizzare journald per l'invio a un sistema esterno
# Configurare systemd-journal-remote per la raccolta centralizzata
```

Soluzioni enterprise raccomandate: ELK Stack (Elasticsearch, Logstash, Kibana), Graylog, Grafana Loki, Splunk.

---

### Filesystem Manutenzione

La manutenzione proattiva dei filesystem previene perdite di dati e interruzioni di servizio.

#### Monitoraggio Spazio Disco e Alerting

```bash
# Verificare lo spazio disco su tutti i filesystem
df -h

# Verificare l'utilizzo degli inode
df -i

# Trovare i file e le directory piu' grandi
du -h --max-depth=1 / 2>/dev/null | sort -rh | head -20

# Trovare file piu' grandi di 1 GB
find / -xdev -type f -size +1G -exec ls -lh {} \; 2>/dev/null

# Script di alerting per spazio disco
#!/bin/bash
THRESHOLD=85
df -H | awk 'NR>1 {gsub(/%/,"",$5); if($5 > '$THRESHOLD') print "ATTENZIONE: "$6" e'"'"' al "$5"% - "$4" disponibili"}'
```

#### Gestione LVM

```bash
# Verificare lo stato dei Volume Group
sudo vgdisplay

# Verificare lo stato dei Logical Volume
sudo lvdisplay

# Estendere un Logical Volume di 10 GB
sudo lvextend -L +10G /dev/vg_data/lv_app

# Ridimensionare il filesystem dopo l'estensione
sudo resize2fs /dev/vg_data/lv_app    # ext4
sudo xfs_growfs /dev/vg_data/lv_app   # xfs

# Creare uno snapshot LVM prima di un intervento rischioso
sudo lvcreate -s -n lv_app_snap -L 5G /dev/vg_data/lv_app

# Rollback da uno snapshot
sudo lvconvert --merge /dev/vg_data/lv_app_snap
```

#### Filesystem Check e Monitoraggio SMART

```bash
# Controllo filesystem (solo su filesystem smontato o in sola lettura)
sudo fsck -n /dev/sda1              # Modalita' solo verifica
sudo e2fsck -f /dev/sda1            # ext4 - verifica forzata
sudo xfs_repair -n /dev/sdb1        # xfs - modalita' verifica

# Installare e configurare smartmontools
sudo apt install smartmontools       # Debian/Ubuntu
sudo dnf install smartmontools       # RHEL/CentOS

# Verificare lo stato SMART di un disco
sudo smartctl -a /dev/sda
sudo smartctl -H /dev/sda           # Solo health status

# Avviare un test SMART
sudo smartctl -t short /dev/sda     # Test breve (2 min)
sudo smartctl -t long /dev/sda      # Test completo (ore)

# Abilitare il monitoraggio continuo
sudo systemctl enable --now smartd
```

#### Pulizia File Temporanei

```bash
# Pulire i file temporanei piu' vecchi di 7 giorni
sudo find /tmp -type f -atime +7 -delete
sudo find /var/tmp -type f -atime +30 -delete

# systemd-tmpfiles gestisce automaticamente la pulizia
sudo systemd-tmpfiles --clean

# Verificare la configurazione di pulizia automatica
ls /etc/tmpfiles.d/
ls /usr/lib/tmpfiles.d/
```

---

### Gestione Utenti e Permessi

La gestione corretta degli account utente e dei permessi e' un requisito fondamentale di sicurezza.

#### Audit Account

```bash
# Trovare account utente con UID >= 1000 (utenti non di sistema)
awk -F: '$3 >= 1000 && $3 < 65534 {print $1, $3, $7}' /etc/passwd

# Trovare account che non hanno mai effettuato il login
lastlog | grep "Never logged in"

# Trovare account con password scaduta o in scadenza
sudo chage -l <username>

# Elencare tutti gli account con shell valida
grep -v '/nologin\|/false' /etc/passwd | awk -F: '{print $1, $7}'

# Trovare account senza password (rischio sicurezza critico)
sudo awk -F: '($2 == "" || $2 == "!") {print $1}' /etc/shadow

# Trovare account con UID 0 diversi da root
awk -F: '$3 == 0 {print $1}' /etc/passwd
```

#### Revisione Accesso Sudo

```bash
# Verificare la configurazione sudoers
sudo visudo -c     # Controllo sintassi

# Elencare i file in /etc/sudoers.d/
ls -la /etc/sudoers.d/

# Trovare tutti gli utenti con accesso sudo
grep -r "ALL" /etc/sudoers /etc/sudoers.d/ 2>/dev/null

# Verificare i gruppi con accesso sudo
getent group sudo     # Debian/Ubuntu
getent group wheel    # RHEL/CentOS

# Verificare i log di utilizzo sudo
grep "sudo:" /var/log/auth.log | tail -50    # Debian/Ubuntu
grep "sudo:" /var/log/secure | tail -50      # RHEL/CentOS
```

#### Rotazione Chiavi SSH

```bash
# Elencare tutte le chiavi SSH autorizzate per ogni utente
for user in $(awk -F: '$3 >= 1000 && $7 !~ /nologin/ {print $1}' /etc/passwd); do
    if [ -f "/home/$user/.ssh/authorized_keys" ]; then
        echo "=== $user ==="
        cat "/home/$user/.ssh/authorized_keys"
    fi
done

# Verificare l'eta' delle chiavi SSH del server
ls -la /etc/ssh/ssh_host_*_key
stat --format="%n creata il %w" /etc/ssh/ssh_host_*_key

# Rigenerare le chiavi host SSH (dopo cambio hardware o compromissione)
sudo rm /etc/ssh/ssh_host_*
sudo dpkg-reconfigure openssh-server    # Debian/Ubuntu
sudo ssh-keygen -A                      # Generico
```

#### Conformita' Policy Password

```bash
# Verificare la configurazione PAM per la complessita' password
cat /etc/pam.d/common-password          # Debian/Ubuntu
cat /etc/pam.d/system-auth              # RHEL/CentOS

# Verificare le impostazioni di password aging predefinite
grep -E "^PASS_MAX_DAYS|^PASS_MIN_DAYS|^PASS_WARN_AGE" /etc/login.defs

# Impostare la politica di scadenza per un utente specifico
sudo chage -M 90 -W 14 -m 1 <username>

# Report completo policy password per un utente
sudo chage -l <username>
```

---

## Patch Management Enterprise (Cross-Platform)

### Politica Patch Management

Una politica di patch management efficace e' il fondamento della sicurezza operativa. Deve essere formalizzata, approvata dal management e comunicata a tutti gli stakeholder.

#### Classificazione delle Patch

| Classificazione | Descrizione | SLA Applicazione | Esempio |
|----------------|-------------|------------------|---------|
| **Critica** | Vulnerabilita' attivamente sfruttata (0-day), rischio compromissione immediata | Entro 72 ore (3 giorni) | CVE con CVSS >= 9.0, RCE senza autenticazione |
| **Importante** | Vulnerabilita' grave con exploit pubblico ma non ancora sfruttata attivamente | Entro 14 giorni | CVE con CVSS 7.0-8.9, escalation privilegi |
| **Moderata** | Vulnerabilita' che richiede condizioni specifiche per l'exploitazione | Entro 30 giorni | CVE con CVSS 4.0-6.9, DoS locale |
| **Bassa** | Vulnerabilita' con impatto minimo o condizioni di exploitazione molto specifiche | Entro 90 giorni | CVE con CVSS < 4.0, information disclosure minore |

#### Processo di Eccezione

Quando non e' possibile applicare una patch entro lo SLA previsto (ad esempio per incompatibilita' applicativa o indisponibilita' della finestra di manutenzione):

1. Il responsabile del sistema compila il modulo di eccezione specificando: sistema interessato, patch non applicabile, motivazione dettagliata, misure di mitigazione alternative e data prevista di applicazione
2. Il responsabile della sicurezza IT valuta il rischio residuo e approva o rifiuta l'eccezione
3. L'eccezione viene registrata nel registro delle eccezioni con una data di scadenza massima
4. Le eccezioni vengono revisionate settimanalmente e rinnovate solo se strettamente necessario

#### Procedura Patch di Emergenza

Per vulnerabilita' critiche attivamente sfruttate (0-day):

1. **Notifica immediata**: il team di sicurezza notifica il team di operations entro 1 ora dalla pubblicazione dell'advisory
2. **Valutazione impatto**: entro 4 ore, determinare quali sistemi sono vulnerabili
3. **Test accelerato**: entro 8 ore, testare la patch su un ambiente rappresentativo
4. **Distribuzione emergenziale**: entro 24-72 ore, applicare la patch a tutti i sistemi vulnerabili, utilizzando finestre di manutenzione di emergenza se necessario
5. **Comunicazione**: aggiornare il management ad ogni fase del processo
6. **Post-mortem**: dopo la distribuzione, documentare lezioni apprese e aggiornare le procedure

---

### Ambiente di Test

Un ambiente di test adeguato e' essenziale per validare gli aggiornamenti prima della distribuzione in produzione.

#### Setup del Laboratorio di Test

L'ambiente di test deve essere il piu' possibile rappresentativo dell'ambiente di produzione:

- Almeno un domain controller di test con la stessa versione di Windows Server della produzione
- Almeno un server Linux di test per ogni distribuzione utilizzata in produzione
- Repliche delle applicazioni business-critical (anche in versione ridotta)
- Stessa configurazione di rete (VLAN, firewall rules, proxy) in scala ridotta
- Database di test con dati anonimizzati per i test applicativi

L'ambiente di test puo' essere implementato su un cluster di virtualizzazione dedicato (Hyper-V, VMware, Proxmox) con snapshot automatici prima di ogni ciclo di test.

#### Test Automatizzati Post-Patching

Dopo l'applicazione delle patch in ambiente di test, eseguire una batteria di test automatizzati:

```bash
# Esempio script di test post-patching Linux
#!/bin/bash
ERRORS=0

# Test 1: Verifica che il sistema si sia avviato correttamente
if ! systemctl is-system-running --quiet; then
    echo "FALLITO: Il sistema non e' in stato 'running'"
    ERRORS=$((ERRORS + 1))
fi

# Test 2: Verifica che tutti i servizi critici siano attivi
for svc in sshd nginx postgresql; do
    if ! systemctl is-active --quiet "$svc"; then
        echo "FALLITO: Il servizio $svc non e' attivo"
        ERRORS=$((ERRORS + 1))
    fi
done

# Test 3: Verifica connettivita' di rete
for host in gateway.local dns.local dbserver.local; do
    if ! ping -c 1 -W 3 "$host" > /dev/null 2>&1; then
        echo "FALLITO: Impossibile raggiungere $host"
        ERRORS=$((ERRORS + 1))
    fi
done

# Test 4: Verifica che le applicazioni web rispondano
for url in http://localhost:80 http://localhost:8080; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    if [ "$HTTP_CODE" != "200" ]; then
        echo "FALLITO: $url restituisce HTTP $HTTP_CODE"
        ERRORS=$((ERRORS + 1))
    fi
done

# Test 5: Verifica spazio disco
DISK_USAGE=$(df / | awk 'NR==2 {gsub(/%/,""); print $5}')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "ATTENZIONE: Disco root al ${DISK_USAGE}%"
    ERRORS=$((ERRORS + 1))
fi

echo "========================"
if [ "$ERRORS" -eq 0 ]; then
    echo "TUTTI I TEST SUPERATI"
    exit 0
else
    echo "$ERRORS TEST FALLITI"
    exit 1
fi
```

```powershell
# Esempio script di test post-patching Windows
$errors = 0

# Test servizi critici
$criticalServices = @('DNS','NTDS','DHCPServer','W3SVC')
foreach ($svc in $criticalServices) {
    $service = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($service.Status -ne 'Running') {
        Write-Warning "FALLITO: Il servizio $svc non e' in esecuzione"
        $errors++
    }
}

# Test connettivita' AD
$dc = Get-ADDomainController -Discover
if (-not $dc) {
    Write-Warning "FALLITO: Impossibile contattare un domain controller"
    $errors++
}

# Test DNS
$dnsTest = Resolve-DnsName "contoso.local" -ErrorAction SilentlyContinue
if (-not $dnsTest) {
    Write-Warning "FALLITO: Risoluzione DNS non funzionante"
    $errors++
}

# Risultato
if ($errors -eq 0) {
    Write-Host "TUTTI I TEST SUPERATI" -ForegroundColor Green
} else {
    Write-Warning "$errors TEST FALLITI"
}
```

#### Checklist Regression Testing

Prima di approvare la distribuzione in produzione, verificare:

- [ ] Il sistema si avvia correttamente dopo il reboot
- [ ] Tutti i servizi critici sono in stato "running"
- [ ] Le applicazioni business-critical sono raggiungibili e funzionanti
- [ ] L'autenticazione utente funziona correttamente (AD, LDAP, SSO)
- [ ] La connettivita' di rete e' integra (DNS, routing, firewall)
- [ ] I database sono accessibili e le query funzionano correttamente
- [ ] I backup automatizzati continuano a funzionare
- [ ] Le performance sono in linea con la baseline (nessun degrado significativo)
- [ ] I log non mostrano errori critici nuovi
- [ ] Le condivisioni di rete sono accessibili

#### Procedure di Rollback

Documentare e testare le procedure di rollback prima di ogni ciclo di patching:

**Windows Server:**
```powershell
# Disinstallare un aggiornamento specifico
wusa /uninstall /kb:5012345 /quiet /norestart

# Ripristinare da un System Restore point (se configurato)
# O ripristinare da snapshot della macchina virtuale
```

**Linux Server:**
```bash
# Debian/Ubuntu - Downgrade di un pacchetto specifico
sudo apt install nginx=1.22.0-1ubuntu1

# RHEL/CentOS - Rollback tramite dnf history
sudo dnf history undo <transaction-id>

# Rollback tramite snapshot LVM
sudo lvconvert --merge /dev/vg_data/lv_root_snap
sudo reboot
```

---

### Automazione Distribuzione

L'automazione e' la chiave per scalare il processo di patching a centinaia o migliaia di server.

#### Ansible per Patching Linux

```yaml
# playbook: patch-linux-servers.yml
---
- name: Patching server Linux
  hosts: linux_servers
  become: true
  serial: "25%"    # Aggiornare il 25% dei server alla volta
  max_fail_percentage: 10

  pre_tasks:
    - name: Creare snapshot LVM (se disponibile)
      command: lvcreate -s -n root_snap -L 5G /dev/vg_root/lv_root
      ignore_errors: true
      when: ansible_lvm is defined

    - name: Verificare spazio disco sufficiente
      assert:
        that: ansible_mounts | selectattr('mount','equalto','/') | map(attribute='size_available') | first > 2147483648
        fail_msg: "Spazio disco insufficiente su / (meno di 2 GB)"

  tasks:
    - name: Aggiornare cache pacchetti (Debian/Ubuntu)
      apt:
        update_cache: yes
        cache_valid_time: 3600
      when: ansible_os_family == "Debian"

    - name: Applicare aggiornamenti di sicurezza (Debian/Ubuntu)
      apt:
        upgrade: safe
        update_cache: yes
      when: ansible_os_family == "Debian"
      register: apt_result

    - name: Applicare aggiornamenti di sicurezza (RHEL/CentOS)
      dnf:
        name: "*"
        state: latest
        security: true
      when: ansible_os_family == "RedHat"
      register: dnf_result

    - name: Verificare se e' necessario un riavvio
      stat:
        path: /var/run/reboot-required
      register: reboot_required
      when: ansible_os_family == "Debian"

    - name: Riavviare se necessario
      reboot:
        reboot_timeout: 600
        msg: "Riavvio per applicazione patch"
      when: >
        (reboot_required.stat.exists is defined and reboot_required.stat.exists) or
        (dnf_result.changed is defined and dnf_result.changed)

  post_tasks:
    - name: Verificare che i servizi critici siano attivi
      systemd:
        name: "{{ item }}"
        state: started
      loop:
        - sshd
        - nginx
        - postgresql
      ignore_errors: true

    - name: Raccogliere report aggiornamenti applicati
      command: "{{ 'apt list --installed 2>/dev/null | head -20' if ansible_os_family == 'Debian' else 'rpm -qa --last | head -20' }}"
      register: installed_updates
      changed_when: false

    - name: Salvare report
      local_action:
        module: copy
        content: "{{ installed_updates.stdout }}"
        dest: "/tmp/patch-report-{{ inventory_hostname }}-{{ ansible_date_time.date }}.txt"
```

#### SCCM/Intune per Patching Windows

Per ambienti Windows enterprise, System Center Configuration Manager (SCCM, ora Microsoft Endpoint Configuration Manager) o Microsoft Intune gestiscono la distribuzione degli aggiornamenti:

- **SCCM**: Ideale per ambienti on-premises e ibridi. Offre Software Update Point (SUP) integrato con WSUS, deployment in fasi, compliance reporting dettagliato e integrazione con le maintenance window
- **Intune**: Ideale per ambienti cloud-first e dispositivi gestiti in remoto. Utilizza Windows Update for Business, Update Rings configurabili e reporting tramite Microsoft Graph

#### Finestre di Manutenzione Pianificate

Definire finestre di manutenzione (maintenance window) ricorrenti:

| Tipo Server | Finestra di Manutenzione | Durata | Frequenza |
|-------------|-------------------------|--------|-----------|
| Server non critici | Mercoledi' 22:00 - 04:00 | 6 ore | Mensile (settimana dopo Patch Tuesday) |
| Server applicativi | Sabato 01:00 - 07:00 | 6 ore | Mensile |
| Server database | Domenica 02:00 - 06:00 | 4 ore | Mensile |
| Domain Controller | Domenica 03:00 - 05:00 (uno alla volta) | 2 ore | Mensile |
| Server critici | Finestra dedicata con approvazione | Variabile | Su richiesta |

#### Gestione Riavvii

I riavvii devono essere coordinati per evitare interruzioni di servizio:

- Riavviare un solo nodo alla volta nei cluster (high availability)
- Verificare che i servizi siano tornati operativi prima di procedere con il nodo successivo
- Per i domain controller, assicurarsi che la replica sia completata dopo ogni riavvio
- Per i server database, verificare l'integrita' del database dopo il riavvio
- Notificare gli utenti con almeno 48 ore di anticipo per interventi che comportano interruzioni

#### Dashboard di Conformita'

Implementare una dashboard centralizzata che mostri in tempo reale:

- Percentuale di server conformi per sistema operativo e per ring
- Tempo medio di applicazione delle patch dalla data di rilascio
- Elenco dei server non conformi con la motivazione (eccezione, errore, in attesa)
- Trend di conformita' nel tempo (grafico mensile)
- Prossime scadenze SLA per le patch in sospeso

Strumenti consigliati: Grafana con dati da Ansible/WSUS, Microsoft Update Compliance (per Windows), Red Hat Satellite/Foreman (per RHEL), Landscape (per Ubuntu).

---

## Deprecazione WSUS e Strumenti Moderni di Patch Management

### Stato della Deprecazione WSUS

A settembre 2024, Microsoft ha annunciato ufficialmente la deprecazione di Windows Server Update Services (WSUS). Sebbene il ruolo WSUS rimanga disponibile in Windows Server 2025 e sia supportato per l'intero ciclo di vita di questa versione (previsto almeno fino al 2035), non verranno sviluppate nuove funzionalita'. Questa decisione segna un cambio di paradigma nella strategia di patching Microsoft, che si sposta decisamente verso soluzioni cloud-native.

Le implicazioni operative per le organizzazioni sono significative. I team IT devono pianificare una transizione graduale verso gli strumenti sostitutivi, mantenendo nel frattempo l'infrastruttura WSUS esistente per i server e i dispositivi che non possono essere immediatamente migrati. Non si tratta di un cambiamento da effettuare dall'oggi al domani, ma di una migrazione strategica che richiede pianificazione e validazione.

#### Alternative Ufficiali Microsoft

**Windows Autopatch (ex Windows Update for Business)**

Ad aprile 2025, Microsoft ha rinominato "Windows Update for Business" in "Windows Update Client Policies", integrando il servizio di deployment in Windows Autopatch, ora incluso con Microsoft 365 Business Premium. Autopatch automatizza la distribuzione degli aggiornamenti utilizzando deployment ring preconfigurati.

Configurazione dei deployment ring tramite Microsoft Intune:

```
Ring 1 — Test:
  Differimento Feature Update: 0 giorni
  Differimento Quality Update: 0 giorni
  Popolazione: Dispositivi IT e tester interni
  
Ring 2 — First:
  Differimento Feature Update: 5 giorni
  Differimento Quality Update: 1 giorno
  Popolazione: Early adopter selezionati (1% dei dispositivi)

Ring 3 — Fast:
  Differimento Feature Update: 14 giorni
  Differimento Quality Update: 3 giorni
  Popolazione: Utenti broad (9% dei dispositivi)

Ring 4 — Broad:
  Differimento Feature Update: 30 giorni
  Differimento Quality Update: 6 giorni
  Popolazione: Maggioranza dell'organizzazione (90% dei dispositivi)
```

La configurazione dei ring in Intune avviene tramite il portale amministrativo in Dispositivi > Aggiornamento Windows > Update rings, dove si creano profili personalizzati che vengono assegnati a gruppi di dispositivi Azure AD. Gli amministratori possono differire i feature update fino a 365 giorni e i quality update fino a 30 giorni.

**Azure Update Manager**

Per la gestione degli aggiornamenti dei server (sia Windows che Linux), Microsoft indirizza verso Azure Update Manager, che sostituisce la funzionalita' precedentemente offerta da Azure Automation Update Management. Azure Update Manager supporta sia macchine virtuali Azure che server on-premises connessi tramite Azure Arc, offrendo:

- Valutazione della conformita' degli aggiornamenti su scala
- Pianificazione degli aggiornamenti con maintenance window
- Distribuzione on-demand per scenari di emergenza
- Supporto cross-platform (Windows Server e distribuzioni Linux principali)
- Reporting integrato con Azure Monitor e Azure Workbooks

```powershell
# Connettere un server on-premises ad Azure Arc per la gestione tramite Azure Update Manager
# Prerequisito: installare l'agente Azure Connected Machine

# Verificare lo stato di conformita' di un server connesso ad Azure Arc
az connectedmachine extension list --machine-name "SRV-PROD-01" --resource-group "rg-servers"

# Avviare una valutazione degli aggiornamenti
az maintenance update list --resource-group "rg-servers" --provider-name "Microsoft.HybridCompute" --resource-type "machines" --resource-name "SRV-PROD-01"
```

#### Soluzioni di Terze Parti Enterprise

Per le organizzazioni che cercano una soluzione cross-platform indipendente dal cloud Microsoft, esistono diverse alternative mature:

| Soluzione | Piattaforme | Modello | Vantaggi Principali |
|-----------|-------------|---------|---------------------|
| **NinjaOne** | Windows, macOS, Linux | Cloud SaaS | RMM integrato, patching third-party, automazione |
| **ManageEngine Patch Manager Plus** | Windows, macOS, Linux | Cloud o On-Prem | Supporto 900+ app third-party, compliance reporting |
| **Automox** | Windows, macOS, Linux | Cloud SaaS | Policy-based patching, zero-trust endpoint management |
| **Ivanti Patch Management** | Windows, macOS, Linux | Cloud o On-Prem | Vulnerability-based patching, integrazione ITSM |
| **BatchPatch** | Windows | On-Prem | Interfaccia semplice, ideale per ambienti puri Windows |

La scelta dello strumento dipende da diversi fattori: dimensione dell'infrastruttura, mix di sistemi operativi, requisiti di compliance, budget e strategia cloud dell'organizzazione. Per ambienti prevalentemente Microsoft, la strada naturale e' Intune/Autopatch per client e Azure Update Manager per server. Per ambienti misti con significativa presenza Linux, una soluzione cross-platform di terze parti o Ansible puo' essere piu' appropriata.

---

### SCCM/MECM — Patch Management Enterprise Windows

Microsoft Endpoint Configuration Manager (MECM, precedentemente System Center Configuration Manager o SCCM) rimane la piattaforma enterprise piu' completa per la gestione degli aggiornamenti Windows in ambienti on-premises e ibridi. SCCM utilizza WSUS come componente sottostante (Software Update Point — SUP) ma aggiunge capacita' avanzate di orchestrazione, targeting, compliance e reporting.

#### Architettura Software Update Point

L'architettura tipica prevede un SUP primario nel sito centrale e SUP secondari nelle sedi remote. Il SUP si integra con il database WSUS per la sincronizzazione dei metadati e il download dei contenuti:

```
┌─────────────────────────────────────┐
│  Microsoft Update (Internet)         │
└──────────────┬──────────────────────┘
               │ Sincronizzazione
┌──────────────▼──────────────────────┐
│  SCCM Primary Site + SUP primario   │
│  (WSUS upstream integrato)          │
│  Database: SQL Server               │
└──────┬───────────────┬──────────────┘
       │               │
┌──────▼────────┐ ┌────▼──────────────┐
│  Distribution │ │  Secondary Site    │
│  Point sede A │ │  + SUP downstream  │
│               │ │  sede B            │
└───────────────┘ └───────────────────┘
```

#### Configurazione Automatic Deployment Rules (ADR)

Le ADR automatizzano l'intero processo di download, creazione del pacchetto di deployment e distribuzione degli aggiornamenti. E' la pratica raccomandata per il patching mensile:

```powershell
# Esempio di creazione ADR tramite PowerShell (ConfigMgr module)
New-CMAutoDeploymentRule -Name "ADR-SecurityUpdates-Monthly" `
    -Description "Deployment automatico patch di sicurezza mensili" `
    -CollectionName "All Windows Servers - Ring 1 Test" `
    -AddToExistingSoftwareUpdateGroup $false `
    -EnabledAfterCreate $true `
    -ArticleId "" `
    -UpdateClassification "Security Updates","Critical Updates" `
    -Product "Windows Server 2022","Windows Server 2025" `
    -DateReleasedOrRevised "Last 1 month" `
    -Superseded $false `
    -DeploymentPackageName "Monthly-Security-Updates" `
    -DownloadFromMicrosoftUpdate $true `
    -DeadlineDateTime (Get-Date).AddDays(14) `
    -UserNotification DisplayAll `
    -SuppressRestartServer $false `
    -AllowRestart $true
```

#### Best Practice SCCM per Software Updates

1. **Limitare a 1000 aggiornamenti per deployment.** Quando si creano ADR, verificare che i criteri non producano piu' di 1000 aggiornamenti per evitare problemi di prestazioni nella valutazione di conformita' lato client.

2. **Configurare TLS/SSL tra WSUS e SCCM.** Abilitare la comunicazione HTTPS sul SUP per prevenire attacchi man-in-the-middle che potrebbero compromettere un client ed eseguire escalation di privilegi.

3. **Database WSUS condiviso tra SUP.** Quando si installano piu' SUP in un sito primario, utilizzare lo stesso database WSUS per ciascun SUP nella stessa foresta Active Directory, riducendo significativamente l'impatto sulle prestazioni di rete.

4. **Maintenance window dedicate.** Configurare maintenance window separate per gli aggiornamenti software e per altri deployment (applicazioni, task sequence) per evitare conflitti e garantire che le patch vengano applicate nelle finestre programmate.

5. **Compliance monitoring continuo.** Utilizzare i report integrati di SCCM (Software Updates Compliance, Software Updates Dashboard) per monitorare la conformita' in tempo reale e identificare rapidamente i sistemi non conformi.

---

## Gestione Patch Management Enterprise Linux

### Red Hat Satellite e Foreman/Katello

Red Hat Satellite e' la piattaforma enterprise di riferimento per la gestione dei sistemi RHEL. Basata su Foreman (il progetto upstream open-source), con il plugin Katello per la gestione dei contenuti, offre un ecosistema completo per il lifecycle management dei server Linux.

#### Architettura Satellite

```
┌─────────────────────────────────────┐
│  Red Hat CDN (Internet)             │
└──────────────┬──────────────────────┘
               │ Sincronizzazione contenuti
┌──────────────▼──────────────────────┐
│  Satellite Server (sede centrale)    │
│  - Content Management (Katello)      │
│  - Provisioning (Foreman)            │
│  - Configuration (Puppet/Ansible)    │
│  - Compliance (OpenSCAP)             │
└──────┬───────────────┬──────────────┘
       │               │
┌──────▼────────┐ ┌────▼──────────────┐
│  Capsule      │ │  Capsule           │
│  Server       │ │  Server            │
│  sede A       │ │  sede B            │
│  (mirror)     │ │  (mirror)          │
└───────────────┘ └───────────────────┘
```

#### Content Lifecycle Environments

Il concetto fondamentale di Satellite e' la separazione dei contenuti in ambienti di lifecycle. I pacchetti vengono promossi attraverso una catena di ambienti prima di raggiungere la produzione:

```
Library → Development → QA → Pre-Production → Production
```

Ogni promozione e' un'azione esplicita che avviene dopo validazione. Un content view in Satellite e' un insieme filtrato di repository (pacchetti RPM, errata, moduli) che viene "pubblicato" come versione immutabile e poi promosso tra gli ambienti.

```bash
# Creare un Content View per i server RHEL 9
hammer content-view create \
    --name "CV-RHEL9-Base" \
    --description "Content View base per RHEL 9" \
    --organization "Azienda-IT"

# Aggiungere i repository necessari
hammer content-view add-repository \
    --name "CV-RHEL9-Base" \
    --repository "Red Hat Enterprise Linux 9 for x86_64 - BaseOS RPMs 9" \
    --organization "Azienda-IT"

hammer content-view add-repository \
    --name "CV-RHEL9-Base" \
    --repository "Red Hat Enterprise Linux 9 for x86_64 - AppStream RPMs 9" \
    --organization "Azienda-IT"

# Pubblicare una nuova versione del Content View
hammer content-view publish \
    --name "CV-RHEL9-Base" \
    --description "Pubblicazione mensile $(date +%Y-%m-%d)" \
    --organization "Azienda-IT"

# Promuovere la versione appena pubblicata all'ambiente Development
hammer content-view version promote \
    --content-view "CV-RHEL9-Base" \
    --version "3.0" \
    --to-lifecycle-environment "Development" \
    --organization "Azienda-IT"

# Dopo validazione, promuovere a Production
hammer content-view version promote \
    --content-view "CV-RHEL9-Base" \
    --version "3.0" \
    --to-lifecycle-environment "Production" \
    --organization "Azienda-IT"
```

#### Errata Management con Satellite

Satellite classifica le errata in tre categorie: Security (RHSA), Bugfix (RHBA) e Enhancement (RHEA). L'applicazione selettiva delle errata consente un controllo granulare:

```bash
# Elencare le errata di sicurezza disponibili per un host
hammer host errata list \
    --host "web-server-01.azienda.local" \
    --errata-type "security"

# Applicare un'errata specifica a un host
hammer host errata apply \
    --host "web-server-01.azienda.local" \
    --errata-ids "RHSA-2025:1234"

# Applicare tutte le errata di sicurezza a un host group tramite remote execution
hammer job-invocation create \
    --job-template "Install Errata - Katello SSH Default" \
    --inputs "errata=type=security" \
    --search-query "hostgroup = webservers" \
    --description "Patching sicurezza mensile webservers"
```

### Canonical Landscape per Ubuntu

Landscape e' la piattaforma di gestione centralizzata di Canonical per i sistemi Ubuntu. Offre funzionalita' analoghe a Red Hat Satellite ma ottimizzate per l'ecosistema Ubuntu e Debian:

- Patch deployment centralizzato con approvazione selettiva
- Compliance reporting con dashboard web
- Integrazione con Livepatch per aggiornamenti kernel senza reboot
- Gestione repository e profili di aggiornamento
- Scripting remoto e audit di conformita'

```bash
# Registrare un client Ubuntu con Landscape
sudo apt install landscape-client
sudo landscape-config --computer-title "web-prod-01" \
    --account-name "azienda" \
    --url "https://landscape.azienda.local/message-system" \
    --ping-url "http://landscape.azienda.local/ping" \
    --ssl-public-key /etc/landscape/landscape-server.pem

# Configurare gli aggiornamenti automatici con approvazione manuale
# In /etc/landscape/client.conf:
# [client]
# manager_plugins = PackageManager
# package_manager_run_unattended = false
```

### Foreman/Katello Open-Source

Per le organizzazioni che non hanno sottoscrizioni Red Hat o che gestiscono un parco eterogeneo di distribuzioni Linux, Foreman con il plugin Katello offre una soluzione open-source equivalente a Satellite. Supporta RHEL, CentOS Stream, Rocky Linux, AlmaLinux, Debian e Ubuntu:

```bash
# Installazione Foreman con Katello su un server dedicato
# Prerequisiti: CentOS Stream 9 o Rocky Linux 9, 8+ GB RAM, 300+ GB disco

# Abilitare i repository necessari
sudo dnf install https://yum.theforeman.org/releases/latest/el9/x86_64/foreman-release.rpm
sudo dnf install https://yum.theforeman.org/katello/latest/katello/el9/x86_64/katello-repos-latest.rpm

# Installare il pacchetto di installazione
sudo dnf install foreman-installer-katello

# Eseguire l'installer
sudo foreman-installer --scenario katello \
    --foreman-initial-admin-username admin \
    --foreman-initial-admin-password "$(openssl rand -base64 24)" \
    --foreman-proxy-dns true \
    --foreman-proxy-dhcp true \
    --foreman-proxy-tftp true
```

### Automazione Cross-Platform con dnf-automatic e apt-daily

Per flotte di piccole-medie dimensioni dove una piattaforma enterprise non e' giustificata, l'automazione nativa del gestore pacchetti offre una soluzione leggera:

**RHEL/CentOS/Rocky — dnf-automatic:**

```bash
# Installare dnf-automatic
sudo dnf install dnf-automatic

# Configurazione in /etc/dnf/automatic.conf
# [commands]
# upgrade_type = security          # Solo aggiornamenti di sicurezza
# apply_updates = yes              # Applicare automaticamente
# download_updates = yes           # Scaricare automaticamente
#
# [emitters]
# emit_via = email                 # Notifica via email
#
# [email]
# email_from = dnf-automatic@server.azienda.local
# email_to = sysadmin@azienda.local
# email_host = smtp.azienda.local

# Abilitare il timer
sudo systemctl enable --now dnf-automatic.timer

# Verificare lo stato del timer
systemctl list-timers dnf-automatic.timer
```

**Debian/Ubuntu — Unattended Upgrades avanzato:**

```bash
# Configurazione avanzata in /etc/apt/apt.conf.d/50unattended-upgrades

Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    // Opzionale: includere anche bugfix updates
    // "${distro_id}:${distro_codename}-updates";
};

// Rimuovere automaticamente le dipendenze inutilizzate
Unattended-Upgrade::Remove-Unused-Dependencies "true";

// Rimuovere i kernel non piu' necessari
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";

// Non riavviare automaticamente (gestire separatamente)
Unattended-Upgrade::Automatic-Reboot "false";

// Notifica via email
Unattended-Upgrade::Mail "sysadmin@azienda.local";
Unattended-Upgrade::MailReport "on-change";

// Blacklist pacchetti da non aggiornare automaticamente
Unattended-Upgrade::Package-Blacklist {
    "nginx";
    "postgresql-*";
    "docker-ce";
};

// Limiti di banda per il download
Acquire::http::Dl-Limit "500";
```

```bash
# Configurazione frequenza in /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";

# Test della configurazione
sudo unattended-upgrade --dry-run --debug 2>&1 | tee /tmp/unattended-upgrade-test.log

# Verificare i log delle esecuzioni precedenti
cat /var/log/unattended-upgrades/unattended-upgrades.log
```

---

## Hardening del Sistema Operativo — CIS Benchmark

### Introduzione ai CIS Benchmark

I CIS (Center for Internet Security) Benchmark sono raccomandazioni di configurazione prescrittive sviluppate attraverso un processo collaborativo guidato dalla comunita' di esperti di cybersecurity. Rappresentano lo standard de facto per l'hardening dei sistemi operativi e sono riconosciuti da framework di conformita' come PCI DSS, HIPAA, NIST 800-53 e ISO 27001.

I benchmark sono disponibili per oltre 25 famiglie di prodotti e vengono aggiornati regolarmente. A partire da gennaio 2025, i benchmark CIS coprono Windows Server 2025, Windows Server 2022, RHEL 9, Ubuntu 24.04 LTS, Rocky Linux 10, e molte altre piattaforme.

#### Profili CIS: Level 1 vs Level 2

Ogni benchmark CIS definisce due profili di hardening:

| Profilo | Obiettivo | Impatto Operativo | Quando Applicare |
|---------|-----------|-------------------|-----------------|
| **Level 1** | Sicurezza di base senza impatto significativo sulle funzionalita' | Basso | Tutti i server, baseline minima obbligatoria |
| **Level 2** | Sicurezza avanzata, puo' limitare alcune funzionalita' | Medio-Alto | Server ad alta criticita', ambienti regolamentati (PCI, HIPAA) |

### Hardening Linux con OpenSCAP

OpenSCAP e' l'implementazione open-source del protocollo SCAP (Security Content Automation Protocol), che consente di automatizzare la valutazione della conformita' e l'applicazione delle remediation basate sui profili CIS e STIG.

#### Installazione e Configurazione OpenSCAP

```bash
# Installazione su RHEL/CentOS/Rocky
sudo dnf install openscap-scanner scap-security-guide

# Installazione su Debian/Ubuntu
sudo apt install libopenscap8 ssg-debian ssg-ubuntu

# Verificare i profili disponibili per la distribuzione corrente
oscap info /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml | grep "Profile:"
# Output tipico:
#   Profile: xccdf_org.ssgproject.content_profile_cis
#   Profile: xccdf_org.ssgproject.content_profile_cis_server_l1
#   Profile: xccdf_org.ssgproject.content_profile_cis_workstation_l1
#   Profile: xccdf_org.ssgproject.content_profile_stig
#   Profile: xccdf_org.ssgproject.content_profile_pci-dss
```

#### Scansione di Conformita' CIS

```bash
# Eseguire una scansione CIS Level 1 Server su RHEL 9 con report HTML
sudo oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
    --results /tmp/cis-scan-results.xml \
    --report /tmp/cis-scan-report.html \
    /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Generare un report in formato ARF (Asset Reporting Format) per archiviazione
sudo oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
    --results-arf /tmp/cis-scan-arf.xml \
    /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

#### Generazione Automatica degli Script di Remediation

OpenSCAP puo' generare automaticamente script Bash o playbook Ansible per correggere le non-conformita' rilevate:

```bash
# Generare uno script Bash di remediation basato sui risultati della scansione
sudo oscap xccdf generate fix \
    --fix-type bash \
    --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
    --output /tmp/cis-remediation.sh \
    /tmp/cis-scan-results.xml

# Generare un playbook Ansible di remediation
sudo oscap xccdf generate fix \
    --fix-type ansible \
    --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
    --output /tmp/cis-remediation-playbook.yml \
    /tmp/cis-scan-results.xml

# ATTENZIONE: NON eseguire mai gli script di remediation in produzione
# senza prima averli revisionati e testati in ambiente di sviluppo.
# Alcune remediation possono interrompere servizi o funzionalita'.

# Revisionare lo script prima dell'esecuzione
less /tmp/cis-remediation.sh

# Eseguire lo script di remediation (SOLO dopo revisione e test)
sudo bash /tmp/cis-remediation.sh
```

#### Integrazione OpenSCAP con Satellite/Foreman

Red Hat Satellite integra nativamente OpenSCAP per la scansione di conformita' su larga scala:

```bash
# Configurare un compliance policy in Satellite tramite hammer
hammer policy create \
    --name "CIS-RHEL9-L1-Monthly" \
    --scap-content "Red Hat RHEL9 default content" \
    --scap-content-profile "CIS Red Hat Enterprise Linux 9 Benchmark Level 1 - Server" \
    --period "monthly" \
    --weekday "sunday" \
    --hostgroups "RHEL9-Production" \
    --organization "Azienda-IT"

# Verificare i risultati di conformita'
hammer host sc-report list --host "web-server-01.azienda.local"
```

### Hardening Windows Server con CIS Benchmark

Per Windows Server, l'applicazione dei CIS Benchmark avviene principalmente tramite Group Policy Object (GPO). Il Center for Internet Security fornisce template GPO scaricabili che possono essere importati direttamente nell'ambiente Active Directory.

#### Importazione Template GPO CIS

```powershell
# Scaricare i CIS Benchmark GPO templates dal sito CIS (richiede account)
# Estrarre l'archivio in una directory locale

# Importare le GPO CIS nell'ambiente AD
$backupPath = "C:\CIS-Benchmark\GPOs"
$gpos = Get-ChildItem $backupPath -Directory

foreach ($gpo in $gpos) {
    $gpoName = "CIS - $($gpo.Name)"
    $newGPO = New-GPO -Name $gpoName -Comment "CIS Benchmark importato $(Get-Date -Format 'yyyy-MM-dd')"
    Import-GPO -BackupGpoName $gpo.Name -Path $backupPath -TargetName $gpoName
    Write-Host "Importata GPO: $gpoName"
}

# NOTA: collegare le GPO alle OU appropriate SOLO dopo test
# NON collegare mai direttamente al dominio root senza validazione
```

#### Audit di Conformita' con Microsoft Policy Analyzer

```powershell
# Utilizzo di Security Compliance Toolkit (SCT) di Microsoft
# Scaricare da Microsoft: Security Compliance Toolkit

# Esportare le impostazioni correnti del server per confronto
secedit /export /cfg C:\SecurityBaseline\current-settings.inf

# Confronto manuale tra impostazioni correnti e baseline CIS
# Verificare le impostazioni critiche:

# Password policy
net accounts

# Audit policy
auditpol /get /category:*

# Diritti utente (User Rights Assignment)
secedit /export /areas USER_RIGHTS /cfg C:\SecurityBaseline\user-rights.inf

# Servizi disabilitati secondo CIS
$cisDisabledServices = @(
    'Browser',          # Computer Browser
    'IISADMIN',         # IIS Admin Service (se non necessario)
    'irmon',            # Infrared Monitor Service
    'SharedAccess',     # Internet Connection Sharing
    'LxssManager',      # Windows Subsystem for Linux (se non necessario)
    'FTPSVC',           # Microsoft FTP Service (se non necessario)
    'sshd',             # OpenSSH Server (se non necessario)
    'RpcLocator',       # Remote Procedure Call Locator
    'RemoteRegistry',   # Remote Registry
    'simptcp',          # Simple TCP/IP Services
    'SSDPSRV',          # SSDP Discovery
    'WMSvc',            # Web Management Service (se non necessario)
    'WerSvc',           # Windows Error Reporting Service
    'Wecsvc',           # Windows Event Collector (se non necessario)
    'WMPNetworkSvc',    # Windows Media Player Network Sharing
    'icssvc',           # Windows Mobile Hotspot Service
    'WpnService',       # Windows Push Notifications
    'PushToInstall',    # Windows PushToInstall Service
    'WinRM'             # Windows Remote Management (se non necessario)
)

foreach ($svc in $cisDisabledServices) {
    $service = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -eq 'Running') {
            Write-Warning "NON CONFORME: $svc ($($service.DisplayName)) e' in esecuzione"
        } else {
            Write-Host "CONFORME: $svc e' arrestato" -ForegroundColor Green
        }
    }
}
```

#### Checklist Hardening Manuale — Controlli Critici

Oltre ai template GPO, verificare manualmente i seguenti controlli CIS di livello critico:

```powershell
# 1. Verificare che il firewall Windows sia abilitato su tutti i profili
Get-NetFirewallProfile | Select-Object Name, Enabled
# Atteso: Enabled = True per Domain, Private, Public

# 2. Verificare che SMBv1 sia disabilitato
Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol
# Atteso: State = Disabled

# 3. Verificare che il Credential Guard sia abilitato (su hardware compatibile)
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
# Verificare SecurityServicesRunning includa CredentialGuard

# 4. Verificare la configurazione NTP
w32tm /query /configuration
# Il PDC Emulator deve sincronizzarsi con una fonte esterna affidabile

# 5. Verificare che il PowerShell Script Block Logging sia abilitato
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
# Atteso: EnableScriptBlockLogging = 1

# 6. Verificare che il Local Administrator Password Solution (LAPS) sia configurato
Get-ADComputer -Filter * -Properties ms-Mcs-AdmPwdExpirationTime |
    Where-Object {$_.'ms-Mcs-AdmPwdExpirationTime' -eq $null} |
    Select-Object Name
# Lista dei computer senza LAPS configurato
```

---

## Gestione Golden Image e Image Pipeline

### Concetti Fondamentali

Una golden image (immagine dorata, o master image) e' un'immagine di sistema operativo pre-configurata che serve come base standardizzata per il provisioning di nuovi server e macchine virtuali. L'approccio golden image garantisce che ogni nuovo sistema nasca con una configurazione sicura, conforme e documentata.

Una golden image tipica include:
- Sistema operativo aggiornato con le ultime patch di sicurezza
- Hardening di base (CIS Level 1 o equivalente)
- Agente di monitoraggio pre-installato (Zabbix, Prometheus node_exporter, Datadog)
- Configurazione di logging centralizzato
- Chiavi SSH o certificati per l'autenticazione iniziale
- Configurazione NTP e DNS di base
- Tool di gestione (agent Satellite/Puppet/Ansible)

### Pipeline di Build con HashiCorp Packer

Packer e' lo strumento di riferimento per la creazione automatizzata di golden image. Utilizza template dichiarativi (in formato HCL o JSON) per definire il processo di build, che include la selezione della sorgente, l'esecuzione di provisioner (script, Ansible, Chef) e la generazione dell'immagine finale.

#### Template Packer per Golden Image Linux (RHEL 9)

```hcl
# golden-image-rhel9.pkr.hcl

packer {
  required_plugins {
    vsphere = {
      source  = "github.com/hashicorp/vsphere"
      version = ">= 1.4.0"
    }
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = ">= 1.1.0"
    }
  }
}

# Variabili configurabili
variable "vsphere_server" {
  type    = string
  default = "vcenter.azienda.local"
}

variable "vsphere_user" {
  type      = string
  sensitive = true
}

variable "vsphere_password" {
  type      = string
  sensitive = true
}

variable "image_version" {
  type    = string
  default = "1.0.0"
}

# Sorgente: VM in vSphere
source "vsphere-iso" "rhel9-base" {
  vcenter_server      = var.vsphere_server
  username            = var.vsphere_user
  password            = var.vsphere_password
  insecure_connection = false

  datacenter = "DC-Principale"
  cluster    = "Cluster-Prod"
  datastore  = "DS-Templates"
  folder     = "Templates/Golden-Images"

  vm_name              = "golden-rhel9-${var.image_version}"
  guest_os_type        = "rhel9_64Guest"
  CPUs                 = 2
  RAM                  = 4096
  disk_controller_type = ["pvscsi"]

  storage {
    disk_size             = 40960
    disk_thin_provisioned = true
  }

  network_adapters {
    network      = "VLAN-Management"
    network_card = "vmxnet3"
  }

  iso_paths = ["[DS-ISO] rhel-9.4-x86_64-dvd.iso"]

  http_directory = "http"
  boot_command   = [
    "<up><wait><tab> inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/ks-rhel9.cfg<enter>"
  ]

  ssh_username = "packer"
  ssh_password = "packer-temp-password"
  ssh_timeout  = "30m"

  convert_to_template = true
}

# Fase di build e provisioning
build {
  sources = ["source.vsphere-iso.rhel9-base"]

  # Step 1: Aggiornamento completo del sistema
  provisioner "shell" {
    inline = [
      "sudo dnf update -y",
      "sudo dnf install -y open-vm-tools cloud-init"
    ]
  }

  # Step 2: Hardening CIS tramite Ansible
  provisioner "ansible" {
    playbook_file = "ansible/cis-hardening-rhel9.yml"
    extra_arguments = [
      "--extra-vars", "cis_level=1"
    ]
  }

  # Step 3: Installazione agenti di monitoraggio
  provisioner "shell" {
    script = "scripts/install-monitoring-agents.sh"
  }

  # Step 4: Pulizia pre-template
  provisioner "shell" {
    inline = [
      "sudo dnf clean all",
      "sudo rm -rf /var/cache/dnf/*",
      "sudo rm -f /etc/ssh/ssh_host_*",
      "sudo rm -rf /tmp/*",
      "sudo rm -rf /var/tmp/*",
      "sudo truncate -s 0 /var/log/messages",
      "sudo truncate -s 0 /var/log/secure",
      "sudo cloud-init clean --logs",
      "sudo rm -f /etc/machine-id",
      "sudo touch /etc/machine-id",
      "sudo rm -f /home/packer/.bash_history",
      "history -c"
    ]
  }

  # Post-processor: registrazione metadati
  post-processor "manifest" {
    output = "builds/rhel9-golden-${var.image_version}.json"
  }
}
```

#### Template Packer per Golden Image Windows Server 2025

```hcl
# golden-image-ws2025.pkr.hcl

source "vsphere-iso" "ws2025-base" {
  vcenter_server = var.vsphere_server
  username       = var.vsphere_user
  password       = var.vsphere_password

  datacenter = "DC-Principale"
  cluster    = "Cluster-Prod"
  datastore  = "DS-Templates"

  vm_name              = "golden-ws2025-${var.image_version}"
  guest_os_type        = "windows2019srvNext_64Guest"
  CPUs                 = 4
  RAM                  = 8192
  disk_controller_type = ["pvscsi"]

  storage {
    disk_size             = 61440
    disk_thin_provisioned = true
  }

  iso_paths = [
    "[DS-ISO] windows-server-2025.iso",
    "[DS-ISO] VMware-tools-windows.iso"
  ]

  floppy_files = [
    "answer-files/autounattend.xml",
    "scripts/win-setup.ps1"
  ]

  communicator   = "winrm"
  winrm_username = "Administrator"
  winrm_password = "packer-temp-password"
  winrm_timeout  = "60m"

  convert_to_template = true
}

build {
  sources = ["source.vsphere-iso.ws2025-base"]

  # Installare Windows Updates
  provisioner "powershell" {
    inline = [
      "Install-Module -Name PSWindowsUpdate -Force -Confirm:$false",
      "Import-Module PSWindowsUpdate",
      "Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -IgnoreReboot"
    ]
  }

  # Riavvio dopo Windows Update
  provisioner "windows-restart" {
    restart_timeout = "30m"
  }

  # Secondo round di aggiornamenti (per dipendenze sequenziali)
  provisioner "powershell" {
    inline = [
      "Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -IgnoreReboot"
    ]
  }

  provisioner "windows-restart" {
    restart_timeout = "30m"
  }

  # Hardening CIS tramite script PowerShell
  provisioner "powershell" {
    script = "scripts/cis-hardening-ws2025.ps1"
  }

  # Installare agenti di monitoraggio
  provisioner "powershell" {
    script = "scripts/install-monitoring-agents.ps1"
  }

  # Pulizia pre-template (Sysprep)
  provisioner "powershell" {
    inline = [
      "# Pulizia Windows Update cache",
      "Stop-Service wuauserv",
      "Remove-Item -Path C:\\Windows\\SoftwareDistribution\\* -Recurse -Force",
      "Start-Service wuauserv",
      "# Pulizia temp files",
      "Remove-Item -Path C:\\Windows\\Temp\\* -Recurse -Force -ErrorAction SilentlyContinue",
      "Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue",
      "# Pulizia log eventi",
      "wevtutil cl Application",
      "wevtutil cl Security",
      "wevtutil cl System",
      "# Sysprep generalizzazione",
      "C:\\Windows\\System32\\Sysprep\\sysprep.exe /generalize /oobe /shutdown /quiet"
    ]
  }
}
```

### Pipeline CI/CD per Golden Image

Integrare la build delle golden image in una pipeline CI/CD garantisce riproducibilita', tracciabilita' e aggiornamento regolare:

```yaml
# .gitlab-ci.yml — Pipeline golden image mensile
stages:
  - validate
  - build
  - scan
  - promote

variables:
  PACKER_VERSION: "1.11.2"
  IMAGE_VERSION: "${CI_PIPELINE_IID}"

validate-template:
  stage: validate
  script:
    - packer init golden-image-rhel9.pkr.hcl
    - packer validate golden-image-rhel9.pkr.hcl
    - packer init golden-image-ws2025.pkr.hcl
    - packer validate golden-image-ws2025.pkr.hcl

build-rhel9:
  stage: build
  script:
    - packer build -var "image_version=${IMAGE_VERSION}" golden-image-rhel9.pkr.hcl
  artifacts:
    paths:
      - builds/rhel9-golden-*.json

build-ws2025:
  stage: build
  script:
    - packer build -var "image_version=${IMAGE_VERSION}" golden-image-ws2025.pkr.hcl
  artifacts:
    paths:
      - builds/ws2025-golden-*.json

security-scan:
  stage: scan
  script:
    # Avviare una VM temporanea dalla golden image e scansionarla
    - ansible-playbook scan-golden-image.yml -e "image_version=${IMAGE_VERSION}"
    # Verificare che il CIS compliance score sia >= 90%
    - python3 scripts/check-compliance-score.py --min-score 90

promote-to-production:
  stage: promote
  when: manual
  script:
    - ansible-playbook promote-golden-image.yml -e "image_version=${IMAGE_VERSION}"
  only:
    - main
```

### Frequenza di Ricostruzione

Le golden image devono essere ricostruite con cadenza regolare per incorporare le ultime patch di sicurezza. La frequenza raccomandata e':

| Tipo di Immagine | Frequenza Rebuild | Motivazione |
|-----------------|-------------------|-------------|
| Immagini di produzione | Mensile (dopo Patch Tuesday + 7 giorni) | Incorpora le patch mensili validate |
| Immagini di sviluppo | Bisettimanale | Cicli di test piu' rapidi |
| Immagini per ambienti critici | Su richiesta + mensile | Patch emergenziali immediate |

Dopo ogni ricostruzione, eseguire sempre una scansione di conformita' CIS e una scansione di vulnerabilita' (Nessus, OpenVAS, Qualys) prima di promuovere l'immagine per l'uso in produzione.

---

## Strategie di Migrazione dei Sistemi Operativi

### Ciclo di Vita e Date End-of-Life

La pianificazione delle migrazioni OS si basa sulle date di fine supporto. Operare sistemi fuori supporto espone l'organizzazione a vulnerabilita' non corrette, non conformita' normativa e potenziali sanzioni.

#### Registro Lifecycle Windows Server

| Versione | Fine Mainstream Support | Fine Extended Support | Stato |
|----------|------------------------|-----------------------|-------|
| Windows Server 2016 | 11 gennaio 2022 | **12 gennaio 2027** | Extended Support, migrazione urgente |
| Windows Server 2019 | 09 gennaio 2024 | 09 gennaio 2029 | Extended Support |
| Windows Server 2022 | **13 ottobre 2026** | 13 ottobre 2031 | Mainstream Support |
| Windows Server 2025 (LTSC) | ~2029 | ~2034 | Mainstream Support, versione attuale |

#### Registro Lifecycle RHEL

| Versione | Fine Full Support | Fine Maintenance Support | Stato |
|----------|-------------------|--------------------------|-------|
| RHEL 7 | 06 agosto 2019 | **30 giugno 2024** (ELS fino 2028) | Extended Life Support (a pagamento) |
| RHEL 8 | 31 maggio 2024 | 31 maggio 2029 (ELS fino 2032) | Maintenance Support |
| RHEL 9 | 31 maggio 2027 | 31 maggio 2032 (ELS fino 2035) | Full Support, versione raccomandata |
| RHEL 10 | ~2030 | ~2035 | Pre-release |

#### Registro Lifecycle Ubuntu LTS

| Versione | Fine Standard Support | Fine ESM (Extended Security Maintenance) | Stato |
|----------|----------------------|------------------------------------------|-------|
| Ubuntu 20.04 LTS | Aprile 2025 | Aprile 2030 | ESM (con Ubuntu Pro) |
| Ubuntu 22.04 LTS | Aprile 2027 | Aprile 2032 | Standard Support |
| Ubuntu 24.04 LTS | Aprile 2029 | Aprile 2034 | Standard Support, versione raccomandata |

### Migrazione Windows Server: In-Place Upgrade vs Clean Install

La scelta tra aggiornamento sul posto e installazione pulita dipende dal contesto specifico:

#### In-Place Upgrade

L'aggiornamento in-place sostituisce i file del sistema operativo su un server in esecuzione con una versione piu' recente, preservando software installato, ruoli server, configurazioni e dati.

**Vantaggi:**
- Tempi di migrazione ridotti (tipicamente 1-3 ore per server)
- Preserva tutte le configurazioni, applicazioni e dati
- Minimo sforzo di riconfigurazione post-migrazione
- A partire da Windows Server 2025, possibilita' di upgrade fino a 4 versioni alla volta (es. 2012 R2 → 2025)

**Svantaggi e rischi:**
- Microsoft riporta un tasso di fallimento fino al 4% per gli upgrade in-place
- Possibilita' di ereditare configurazioni obsolete o problematiche
- L'operazione e' irreversibile una volta completata
- Richiede almeno 30-40 GB di spazio libero su C:

**Procedura:**

```powershell
# PRE-UPGRADE CHECKLIST
# 1. Verificare spazio disco (minimo 30-40 GB liberi su C:)
Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'" |
    Select-Object @{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,2)}}

# 2. Backup completo del sistema (o snapshot VM)
wbadmin start backup -backupTarget:E: -include:C: -quiet

# 3. Verificare la compatibilita' dei ruoli installati
Get-WindowsFeature | Where-Object {$_.Installed -eq $true} |
    Select-Object Name, DisplayName

# 4. Documentare la configurazione di rete
Get-NetIPConfiguration | Format-Table InterfaceAlias, IPv4Address, IPv4DefaultGateway, DNSServer

# 5. Eseguire l'upgrade (da media ISO montata o Windows Update)
# Per Windows Server 2025 via Windows Update:
# Impostazioni > Aggiornamento e Sicurezza > Windows Update > Verifica aggiornamenti

# POST-UPGRADE VERIFICATION
# 6. Verificare la versione del sistema operativo
[System.Environment]::OSVersion
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsBuildNumber

# 7. Verificare lo stato di tutti i ruoli e servizi
Get-WindowsFeature | Where-Object {$_.Installed -eq $true}
Get-Service | Where-Object {$_.StartType -eq 'Automatic' -and $_.Status -ne 'Running'}
```

#### Clean Install con Migrazione dei Ruoli

Per i domain controller, Microsoft raccomanda esplicitamente la clean install: promuovere nuovi DC Windows Server 2025, trasferire i ruoli FSMO, verificare la replica, e poi rimuovere i vecchi DC. Questo approccio garantisce le ottimizzazioni di Active Directory specifiche della nuova versione che non vengono applicate durante un upgrade in-place.

```powershell
# PROCEDURA MIGRAZIONE DOMAIN CONTROLLER

# 1. Installare Windows Server 2025 su nuovo hardware/VM
# 2. Aggiungere il nuovo server al dominio come member server
Add-Computer -DomainName "contoso.local" -Restart

# 3. Promuovere a domain controller
Install-WindowsFeature AD-Domain-Services -IncludeManagementTools
Install-ADDSDomainController -DomainName "contoso.local" `
    -SiteName "Default-First-Site-Name" `
    -DatabasePath "D:\NTDS" `
    -LogPath "D:\NTDS" `
    -SYSVOLPath "D:\SYSVOL" `
    -InstallDns:$true `
    -Credential (Get-Credential) `
    -SafeModeAdministratorPassword (Read-Host -AsSecureString "DSRM Password")

# 4. Verificare la replica
repadmin /replsummary
dcdiag /v /c

# 5. Trasferire i ruoli FSMO al nuovo DC
Move-ADDirectoryServerOperationMasterRole -Identity "DC-NEW" `
    -OperationMasterRole SchemaMaster, DomainNamingMaster, PDCEmulator, RIDMaster, InfrastructureMaster

# 6. Verificare il trasferimento
netdom query fsmo

# 7. Declassare il vecchio DC (solo dopo validazione completa)
Uninstall-ADDSDomainController -DemoteOperationMasterRole -LastDomainControllerInDomain:$false
```

### Migrazione RHEL con Leapp

Leapp e' lo strumento ufficiale supportato da Red Hat per gli upgrade in-place tra versioni major di RHEL. Esegue un'analisi pre-upgrade, identifica problemi di compatibilita' e gestisce la transizione con downtime minimale.

#### Percorsi di Upgrade Supportati (2025)

| Da | A | Stato |
|----|---|-------|
| RHEL 7.9 | RHEL 8.10 | Supportato |
| RHEL 8.10 | RHEL 9.4 (EUS) | Supportato |
| RHEL 8.10 | RHEL 9.6 | Supportato |
| RHEL 9.x | RHEL 10 | Supportato (con Satellite 6.17+) |

#### Procedura Leapp Completa

```bash
# FASE 1: PREPARAZIONE

# Verificare la versione attuale e registrazione
cat /etc/redhat-release
subscription-manager status
subscription-manager list --installed

# Aggiornare alla minor release piu' recente prima dell'upgrade
sudo dnf update -y
sudo reboot

# Installare gli strumenti Leapp
sudo dnf install leapp-upgrade
# Per RHEL con Satellite, installare anche:
# sudo dnf install leapp-upgrade-el8toel9

# FASE 2: ANALISI PRE-UPGRADE

# Eseguire il pre-upgrade assessment
sudo leapp preupgrade --target 9.4

# Analizzare il report generato
cat /var/log/leapp/leapp-report.txt

# Il report classifica i finding in:
# - Inhibitor: blocca l'upgrade, DEVE essere risolto
# - High risk: forte rischio, DOVREBBE essere risolto
# - Medium risk: potenziale problema
# - Low risk / Info: informativo

# Esempio di risoluzione comune: rispondere ai dialoghi Leapp
# (moduli kernel deprecati, pacchetti rimossi, ecc.)
sudo leapp answer --section remove_pam_pkcs11_module_check.confirm=True

# FASE 3: ESECUZIONE UPGRADE

# Creare un backup/snapshot prima dell'upgrade
# (LVM snapshot, snapshot VM, o backup completo)

# Eseguire l'upgrade
sudo leapp upgrade --target 9.4

# Il sistema si riavviera' automaticamente nel initramfs di upgrade
# L'intero processo richiede tipicamente 30-60 minuti

# FASE 4: VERIFICA POST-UPGRADE

# Verificare la nuova versione
cat /etc/redhat-release
uname -r

# Verificare lo stato dei servizi
systemctl --failed

# Verificare i pacchetti rimasti dalla versione precedente
rpm -qa | grep el8

# Rimuovere i pacchetti residui dalla versione precedente
sudo dnf remove $(rpm -qa | grep el8 | grep -v "el8\." | head -20)

# Verificare le sottoscrizioni
subscription-manager status
```

#### Limitazioni Note di Leapp

- Non supporta upgrade di sistemi con storage di rete multipath basato su Ethernet o Infiniband
- Non supporta upgrade di sistemi con boot da SAN via FCoE
- GRUB legacy (non GRUB2) non e' supportato
- Ambienti con Fips mode abilitato richiedono passaggi aggiuntivi
- Cluster Pacemaker/Corosync devono essere gestiti separatamente (membro per membro)

### Pianificazione della Migrazione a Scala

Per migrazioni di centinaia o migliaia di server, adottare un approccio strutturato a fasi:

```
Fase 1 — Inventario e Assessment (Settimane 1-4)
├── Censimento completo dei sistemi operativi (versione, ruolo, owner)
├── Identificazione delle dipendenze applicative
├── Classificazione dei server per criticita' (Tier 1-4)
├── Analisi di compatibilita' hardware per le nuove versioni OS
└── Stima dei costi (licenze, hardware, personale, downtime)

Fase 2 — Progettazione e Test (Settimane 5-12)
├── Definizione della strategia per ogni gruppo di server
│   (in-place upgrade, clean install, migrazione, ricostruzione)
├── Creazione dell'ambiente di test rappresentativo
├── Esecuzione dei test di migrazione su campioni
├── Validazione delle applicazioni sulla nuova versione OS
└── Documentazione delle procedure di rollback

Fase 3 — Migrazione Pilota (Settimane 13-16)
├── Migrazione del 5-10% dei server (Tier 3-4, non critici)
├── Monitoraggio intensivo per 2 settimane
├── Raccolta feedback e correzione delle procedure
└── Approvazione formale per la fase successiva

Fase 4 — Migrazione Broad (Settimane 17-36)
├── Migrazione a ondate del 10-20% dei server alla volta
├── Priorita': prima Tier 4, poi Tier 3, poi Tier 2
├── Verifica di conformita' dopo ogni ondata
└── Documentazione continua di problemi e soluzioni

Fase 5 — Migrazione Critica (Settimane 37-44)
├── Migrazione dei server Tier 1 (mission-critical)
├── Finestre di manutenzione dedicate con team di supporto esteso
├── Procedure di rollback testate e pronte all'esecuzione
└── Comunicazione proattiva a tutti gli stakeholder

Fase 6 — Decommissioning (Settimane 45-52)
├── Dismissione dei server migrati su vecchio OS
├── Revoca delle licenze e delle sottoscrizioni
├── Aggiornamento dell'inventario e della CMDB
└── Report finale con metriche e lezioni apprese
```

---

## Automazione Avanzata Cross-Platform con Ansible

### Playbook Unificato per Inventory e Compliance

Ansible Automation Platform consente di creare un pipeline di patching unificato che gestisce sia server Windows che Linux con un singolo workflow:

```yaml
# playbook: cross-platform-patch-compliance.yml
---
- name: Raccolta inventario e verifica conformita' patch
  hosts: all
  gather_facts: true

  tasks:
    # === LINUX ===
    - name: "[Linux] Verificare aggiornamenti disponibili (Debian/Ubuntu)"
      ansible.builtin.apt:
        update_cache: yes
      register: apt_cache
      when: ansible_os_family == "Debian"
      changed_when: false

    - name: "[Linux] Contare aggiornamenti di sicurezza disponibili (Debian/Ubuntu)"
      ansible.builtin.shell: |
        apt list --upgradable 2>/dev/null | grep -ci security || echo "0"
      register: debian_security_count
      when: ansible_os_family == "Debian"
      changed_when: false

    - name: "[Linux] Verificare aggiornamenti disponibili (RHEL)"
      ansible.builtin.shell: |
        dnf updateinfo list security 2>/dev/null | grep -c "RHSA" || echo "0"
      register: rhel_security_count
      when: ansible_os_family == "RedHat"
      changed_when: false

    - name: "[Linux] Verificare necessita' di reboot"
      ansible.builtin.stat:
        path: /var/run/reboot-required
      register: reboot_required_file
      when: ansible_os_family == "Debian"

    - name: "[Linux] Verificare necessita' di reboot (RHEL)"
      ansible.builtin.command: needs-restarting -r
      register: rhel_reboot
      when: ansible_os_family == "RedHat"
      failed_when: false
      changed_when: false

    # === WINDOWS ===
    - name: "[Windows] Verificare aggiornamenti disponibili"
      ansible.windows.win_updates:
        state: searched
        category_names:
          - SecurityUpdates
          - CriticalUpdates
      register: win_updates
      when: ansible_os_family == "Windows"

    # === REPORT UNIFICATO ===
    - name: Generare report di conformita'
      ansible.builtin.set_fact:
        compliance_report:
          hostname: "{{ inventory_hostname }}"
          os_family: "{{ ansible_os_family }}"
          os_version: "{{ ansible_distribution }} {{ ansible_distribution_version }}"
          kernel: "{{ ansible_kernel | default('N/A') }}"
          security_updates_pending: >-
            {% if ansible_os_family == 'Debian' %}{{ debian_security_count.stdout | default('0') }}
            {% elif ansible_os_family == 'RedHat' %}{{ rhel_security_count.stdout | default('0') }}
            {% elif ansible_os_family == 'Windows' %}{{ win_updates.found_update_count | default('0') }}
            {% else %}unknown{% endif %}
          reboot_required: >-
            {% if ansible_os_family == 'Debian' %}{{ reboot_required_file.stat.exists | default(false) }}
            {% elif ansible_os_family == 'RedHat' %}{{ rhel_reboot.rc | default(0) != 0 }}
            {% elif ansible_os_family == 'Windows' %}{{ win_updates.reboot_required | default(false) }}
            {% else %}unknown{% endif %}
          last_check: "{{ ansible_date_time.iso8601 }}"

    - name: Salvare report in formato JSON
      ansible.builtin.copy:
        content: "{{ compliance_report | to_nice_json }}"
        dest: "/tmp/compliance-{{ inventory_hostname }}.json"
      delegate_to: localhost
```

### Playbook di Patching Windows con Ansible

```yaml
# playbook: patch-windows-servers.yml
---
- name: Patching Windows Server con orchestrazione
  hosts: windows_servers
  serial: "20%"
  max_fail_percentage: 5

  vars:
    maintenance_window_start: "22:00"
    maintenance_window_end: "04:00"
    patch_categories:
      - SecurityUpdates
      - CriticalUpdates

  pre_tasks:
    - name: Verificare che siamo nella finestra di manutenzione
      ansible.builtin.assert:
        that:
          - ansible_date_time.hour | int >= (maintenance_window_start | regex_replace(':.*','') | int) or
            ansible_date_time.hour | int < (maintenance_window_end | regex_replace(':.*','') | int)
        fail_msg: "FUORI dalla finestra di manutenzione. Operazione annullata."

    - name: Creare checkpoint di restore (se VM in vSphere)
      community.vmware.vmware_guest_snapshot:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        datacenter: "{{ vcenter_datacenter }}"
        name: "{{ inventory_hostname }}"
        snapshot_name: "pre-patch-{{ ansible_date_time.date }}"
        description: "Snapshot pre-patching automatico"
        state: present
      delegate_to: localhost
      when: create_vm_snapshot | default(true)

  tasks:
    - name: Installare aggiornamenti di sicurezza e critici
      ansible.windows.win_updates:
        category_names: "{{ patch_categories }}"
        state: installed
        reboot: false
      register: update_result

    - name: Registrare gli aggiornamenti installati
      ansible.builtin.debug:
        msg: "Installati {{ update_result.installed_update_count }} aggiornamenti su {{ inventory_hostname }}"

    - name: Riavviare se necessario
      ansible.windows.win_reboot:
        reboot_timeout: 600
        post_reboot_delay: 120
        msg: "Riavvio per applicazione patch - {{ ansible_date_time.date }}"
      when: update_result.reboot_required

  post_tasks:
    - name: Verificare che i servizi critici siano attivi
      ansible.windows.win_service:
        name: "{{ item }}"
      register: service_check
      loop:
        - DNS
        - W3SVC
        - MSSQLSERVER
      failed_when: service_check.state != 'running' and service_check.exists
      ignore_errors: true

    - name: Inviare notifica di completamento
      ansible.builtin.uri:
        url: "{{ webhook_url }}"
        method: POST
        body_format: json
        body:
          text: "Patching completato su {{ inventory_hostname }}: {{ update_result.installed_update_count }} aggiornamenti installati"
      delegate_to: localhost
      when: webhook_url is defined
```

---

## Compliance Reporting e Audit

### KPI (Key Performance Indicator) per la Gestione OS

Definire e monitorare KPI specifici per la gestione dei sistemi operativi:

| KPI | Target | Frequenza Misurazione | Azione se Fuori Target |
|-----|--------|-----------------------|------------------------|
| **Patch Compliance Rate** (% server conformi) | >= 95% | Settimanale | Escalation al team di sicurezza |
| **Mean Time to Patch** (tempo medio dall'uscita della patch all'applicazione) | <= 14 giorni (critical), <= 30 giorni (important) | Mensile | Revisione processo di approvazione |
| **OS EoL Exposure** (% server su OS fuori supporto) | 0% | Mensile | Piano di migrazione accelerato |
| **CIS Compliance Score** (% di conformita' ai benchmark CIS) | >= 85% (L1) | Trimestrale | Remediation pianificata |
| **Golden Image Freshness** (eta' dell'ultima golden image) | <= 30 giorni | Mensile | Rebuild immagine |
| **Reboot Pending** (% server con riavvio in sospeso) | <= 5% | Settimanale | Pianificazione riavvii |
| **Exception Count** (numero eccezioni patch attive) | <= 10% del parco | Settimanale | Revisione e rientro eccezioni |

### Report Settimanale di Conformita' Patch

Script per la generazione automatica di un report di conformita':

```bash
#!/bin/bash
# report-patch-compliance.sh
# Genera un report settimanale di conformita' patch per l'intero parco Linux

REPORT_FILE="/var/reports/patch-compliance-$(date +%Y-%m-%d).csv"
REPORT_DIR=$(dirname "$REPORT_FILE")
mkdir -p "$REPORT_DIR"

echo "Hostname,OS,Kernel,SecurityUpdates,RebootRequired,LastPatched,ComplianceStatus" > "$REPORT_FILE"

# Leggere la lista dei server dall'inventory Ansible
SERVERS=$(ansible-inventory --list --yaml 2>/dev/null | grep -E "^\s+\w" | awk '{print $1}' | tr -d ':')

for SERVER in $SERVERS; do
    # Raccogliere dati via SSH
    DATA=$(ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SERVER" '
        OS=$(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d "\"")
        KERNEL=$(uname -r)
        
        # Contare aggiornamenti di sicurezza
        if command -v apt &>/dev/null; then
            SEC_UPDATES=$(apt list --upgradable 2>/dev/null | grep -ci security || echo "0")
        elif command -v dnf &>/dev/null; then
            SEC_UPDATES=$(dnf updateinfo list security 2>/dev/null | grep -c "RHSA\|CESA" || echo "0")
        else
            SEC_UPDATES="N/A"
        fi
        
        # Verificare necessita' reboot
        if [ -f /var/run/reboot-required ]; then
            REBOOT="YES"
        elif command -v needs-restarting &>/dev/null; then
            needs-restarting -r &>/dev/null && REBOOT="NO" || REBOOT="YES"
        else
            REBOOT="UNKNOWN"
        fi
        
        # Ultima data di patching
        if command -v apt &>/dev/null; then
            LAST_PATCH=$(stat -c %y /var/log/apt/history.log 2>/dev/null | cut -d" " -f1)
        elif command -v dnf &>/dev/null; then
            LAST_PATCH=$(dnf history list 2>/dev/null | awk "NR==3{print \$4}")
        else
            LAST_PATCH="N/A"
        fi
        
        echo "${OS}|${KERNEL}|${SEC_UPDATES}|${REBOOT}|${LAST_PATCH}"
    ' 2>/dev/null)
    
    if [ -n "$DATA" ]; then
        IFS='|' read -r OS KERNEL SEC_UPDATES REBOOT LAST_PATCH <<< "$DATA"
        
        # Determinare lo stato di conformita'
        if [ "$SEC_UPDATES" = "0" ] && [ "$REBOOT" = "NO" ]; then
            STATUS="COMPLIANT"
        elif [ "$SEC_UPDATES" -gt 10 ] 2>/dev/null; then
            STATUS="CRITICAL"
        else
            STATUS="NON-COMPLIANT"
        fi
        
        echo "${SERVER},${OS},${KERNEL},${SEC_UPDATES},${REBOOT},${LAST_PATCH},${STATUS}" >> "$REPORT_FILE"
    else
        echo "${SERVER},UNREACHABLE,N/A,N/A,N/A,N/A,UNREACHABLE" >> "$REPORT_FILE"
    fi
done

# Generare sommario
TOTAL=$(wc -l < "$REPORT_FILE")
TOTAL=$((TOTAL - 1))  # Escludere header
COMPLIANT=$(grep -c "COMPLIANT" "$REPORT_FILE" || echo "0")
NON_COMPLIANT=$(grep -c "NON-COMPLIANT" "$REPORT_FILE" || echo "0")
CRITICAL=$(grep -c "CRITICAL" "$REPORT_FILE" || echo "0")
UNREACHABLE=$(grep -c "UNREACHABLE" "$REPORT_FILE" || echo "0")

echo ""
echo "=== SOMMARIO CONFORMITA' PATCH $(date +%Y-%m-%d) ==="
echo "Totale server: $TOTAL"
echo "Conformi: $COMPLIANT ($(( COMPLIANT * 100 / TOTAL ))%)"
echo "Non conformi: $NON_COMPLIANT"
echo "Critici: $CRITICAL"
echo "Non raggiungibili: $UNREACHABLE"
echo "================================================="
```

### Documentazione per Audit di Conformita'

Per gli audit di conformita' (ISO 27001, SOC 2, PCI DSS), mantenere la seguente documentazione aggiornata:

1. **Politica di Patch Management** — documento formale approvato dal management che definisce SLA, responsabilita', processo di eccezione e escalation
2. **Registro delle Patch Applicate** — log completo di ogni patch applicata, con data, sistema, risultato e responsabile
3. **Registro delle Eccezioni** — elenco delle eccezioni attive con motivazione, misure di mitigazione e data di scadenza
4. **Report di Conformita' CIS** — scan periodici con punteggio di conformita' e piano di remediation per le non-conformita'
5. **Inventario Sistemi Operativi** — elenco completo con versione OS, date EoL, e piano di migrazione per i sistemi prossimi alla fine del supporto
6. **Procedure di Rollback Testate** — documentazione delle procedure di rollback con evidenza dei test eseguiti
7. **Piano di Migrazione OS** — timeline per la migrazione dei sistemi fuori supporto o prossimi all'EoL

---

## Best Practices

1. **Applicare il principio "Infrastructure as Code" alla configurazione OS.** Ogni impostazione di sistema, parametro kernel, configurazione di servizio e policy di sicurezza deve essere definita in codice versionato (Ansible playbook, GPO documentate, script PowerShell). Questo garantisce riproducibilita', tracciabilita' e possibilita' di audit. Mai configurare un server manualmente senza documentare le modifiche in un repository.

2. **Mantenere un inventario aggiornato e automatizzato di tutti i sistemi operativi.** Utilizzare strumenti di discovery automatici (Active Directory, Ansible inventory, CMDB) per avere sempre una visione completa e aggiornata di: versione OS, livello di patch, ruolo del server, owner responsabile e data ultimo aggiornamento. Un server non inventariato e' un server non gestito e potenzialmente vulnerabile.

3. **Testare sempre gli aggiornamenti prima della distribuzione in produzione.** Nessuna patch deve essere applicata direttamente in produzione, indipendentemente dalla sua classificazione. Il modello ring-based (Test, Pilot, Production, Critical) e' un requisito minimo. Documentare i risultati di ogni fase di test e ottenere l'approvazione formale prima di procedere al ring successivo.

4. **Automatizzare tutto cio' che e' automatizzabile, ma mantenere la capacita' di intervento manuale.** L'automazione riduce gli errori umani, accelera i tempi di esecuzione e garantisce consistenza. Tuttavia, ogni procedura automatizzata deve avere una controparte manuale documentata per le situazioni di emergenza in cui l'automazione non funziona o non e' applicabile.

5. **Implementare il monitoraggio proattivo con soglie di alerting definite.** Non attendere che un problema si manifesti con un'interruzione di servizio. Monitorare continuamente: spazio disco (alert al 80%, critico al 90%), utilizzo CPU e memoria, stato dei servizi critici, errori nei log, conformita' patch, stato della replica AD, salute dei filesystem.

6. **Documentare ogni intervento e mantenere un registro delle modifiche (change log).** Ogni modifica al sistema operativo, alla configurazione dei servizi o alle policy di sicurezza deve essere registrata con: data e ora, descrizione della modifica, motivazione, responsabile dell'intervento, risultato e eventuale procedura di rollback. Questo registro e' indispensabile per il troubleshooting e per gli audit di conformita'.

7. **Pianificare e testare regolarmente le procedure di rollback.** Prima di ogni intervento significativo (aggiornamento kernel, major update, modifica GPO critica), creare un punto di ripristino testato: snapshot VM, backup del sistema, snapshot LVM. La procedura di rollback deve essere documentata, testata e eseguibile in tempi certi. Un intervento senza rollback e' un intervento ad alto rischio non accettabile.

8. **Segregare gli ambienti e applicare il principio del minimo privilegio.** I server di produzione devono essere accessibili solo al personale autorizzato, con credenziali dedicate e multi-factor authentication. Gli account di servizio devono avere i permessi minimi necessari (preferibilmente gMSA per Windows). L'accesso sudo/amministrativo deve essere limitato, loggato e periodicamente revisionato.

9. **Standardizzare le configurazioni OS con immagini golden e template.** Creare e mantenere immagini di base (golden images) per ogni versione di sistema operativo supportata. Le immagini devono includere: configurazione di sicurezza di base (hardening), agente di monitoraggio, configurazione di logging, chiavi SSH o certificati di base. Ricostruire le immagini mensilmente con le patch piu' recenti.

10. **Definire e rispettare il ciclo di vita dei sistemi operativi.** Ogni versione di sistema operativo ha una data di fine supporto (End of Life). Pianificare la migrazione con almeno 12 mesi di anticipo. Mantenere un registro delle versioni OS in uso e delle relative date di EoL. Un sistema operativo fuori supporto e' un rischio di sicurezza inaccettabile e deve essere migrato, isolato o dismesso con priorita'.

---

## Troubleshooting

### Problema: WSUS non sincronizza gli aggiornamenti

**Sintomi:** La console WSUS mostra errori di sincronizzazione. I client non ricevono aggiornamenti nuovi.

**Cause comuni:**
- Certificato SSL scaduto sulla connessione a Microsoft Update
- Proxy non configurato correttamente
- Database WSUS corrotto o frammentato
- Spazio disco insufficiente per il content store

**Risoluzione:**
```powershell
# Verificare la connettivita' verso Microsoft Update
Test-NetConnection -ComputerName "windowsupdate.microsoft.com" -Port 443

# Verificare lo spazio disco
Get-WmiObject Win32_LogicalDisk | Select-Object DeviceID, @{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,2)}}

# Reset della sincronizzazione WSUS
Stop-Service WsusService
sqlcmd -S "np:\\.\pipe\Microsoft##WID\tsql\query" -i "C:\WsusDBMaintenance.sql"
Start-Service WsusService
Invoke-WsusServerCleanup -CleanupObsoleteUpdates -CleanupUnneededContentFiles

# Se il database e' gravemente corrotto, considerare la re-inizializzazione
wsusutil reset
```

---

### Problema: Replica Active Directory fallita

**Sintomi:** Gli utenti riscontrano problemi di autenticazione intermittenti. Le modifiche alle password non si propagano. `repadmin /replsummary` mostra errori.

**Cause comuni:**
- Problemi di rete tra i domain controller (firewall, DNS)
- Orologio di sistema fuori sincronizzazione (differenza maggiore di 5 minuti)
- Oggetto lingering nel database AD
- USN rollback (ripristino di un DC da un backup non supportato)

**Risoluzione:**
```powershell
# Diagnostica completa
dcdiag /v /c /e > C:\dcdiag-output.txt
repadmin /showrepl > C:\repl-status.txt

# Verificare la sincronizzazione dell'orario
w32tm /query /status
w32tm /monitor

# Forzare la sincronizzazione dell'orario
w32tm /resync /force

# Forzare la replica
repadmin /syncall /AdeP

# Se ci sono oggetti lingering
repadmin /removelingeringobjects DC02 DC01_GUID "DC=contoso,DC=local" /advisory_mode
```

---

### Problema: Server Linux non si avvia dopo aggiornamento kernel

**Sintomi:** Dopo un aggiornamento kernel e riavvio, il server resta bloccato al boot o va in kernel panic.

**Cause comuni:**
- Modulo DKMS non ricompilato per il nuovo kernel (driver RAID, scheda di rete)
- Initramfs non aggiornato correttamente
- Parametri boot incompatibili con il nuovo kernel
- Incompatibilita' driver con il nuovo kernel

**Risoluzione:**
```bash
# Dal bootloader GRUB, selezionare il kernel precedente
# (tenere premuto Shift o Esc durante il boot per accedere a GRUB)

# Una volta avviato con il kernel precedente:
# Verificare i moduli DKMS
dkms status

# Ricompilare i moduli per il nuovo kernel
sudo dkms autoinstall -k <versione-nuovo-kernel>

# Rigenerare initramfs
sudo update-initramfs -u -k <versione-nuovo-kernel>   # Debian/Ubuntu
sudo dracut --force --kver <versione-nuovo-kernel>     # RHEL/CentOS

# Se il nuovo kernel e' irrecuperabile, rimuoverlo
sudo apt remove linux-image-<versione-problematica>     # Debian/Ubuntu
sudo dnf remove kernel-<versione-problematica>          # RHEL/CentOS
```

---

### Problema: Spazio disco esaurito su /var/log

**Sintomi:** Il server diventa instabile. I servizi non riescono a scrivere nei log. Possibile impossibilita' di effettuare il login.

**Cause comuni:**
- Logrotate non configurato o non funzionante
- Un'applicazione genera log in modo incontrollato
- Il journal di systemd ha raggiunto dimensioni eccessive
- File di log compressi non eliminati

**Risoluzione:**
```bash
# Identificare i file piu' grandi in /var/log
du -h /var/log/ | sort -rh | head -20

# Pulire rapidamente il journal di systemd
sudo journalctl --vacuum-size=500M

# Troncare un file di log enorme senza eliminarlo (mantiene il file descriptor)
sudo truncate -s 0 /var/log/syslog

# NON usare rm su file aperti da un processo - il disco non viene liberato
# Verificare se ci sono file eliminati ma ancora aperti
sudo lsof +D /var/log/ | grep deleted

# Se trovati file "deleted" ancora aperti, riavviare il servizio che li tiene aperti
sudo systemctl restart rsyslog

# Verificare e riparare logrotate
sudo logrotate -d /etc/logrotate.conf    # Dry-run per diagnostica
sudo logrotate -f /etc/logrotate.conf    # Forzare l'esecuzione
```

---

### Problema: Servizio systemd in stato "failed" che non si ripristina

**Sintomi:** Un servizio critico e' in stato "failed" e il riavvio manuale fallisce ripetutamente.

**Cause comuni:**
- File di configurazione del servizio con errori di sintassi
- Permessi errati su file o directory
- Porta gia' in uso da un altro processo
- Dipendenza non disponibile (database, file share)
- Limiti di risorse raggiunti (cgroups, file descriptor)

**Risoluzione:**
```bash
# Analizzare il motivo del fallimento
systemctl status <servizio>.service
journalctl -u <servizio>.service -n 50 --no-pager

# Verificare eventuali errori di sintassi nella configurazione
<servizio> -t    # Per nginx: nginx -t
<servizio> configtest    # Per Apache: apachectl configtest

# Verificare le porte in uso
sudo ss -tlnp | grep <porta>

# Verificare i permessi
sudo namei -l /path/to/config/file
sudo namei -l /path/to/data/directory

# Verificare i limiti di risorse
systemctl show <servizio>.service | grep -E "Limit|Max"
cat /proc/<PID>/limits

# Resettare lo stato e riavviare
sudo systemctl reset-failed <servizio>.service
sudo systemctl start <servizio>.service
```

---

### Problema: GPO non applicate ai client

**Sintomi:** Le impostazioni definite nelle GPO non hanno effetto sui computer o utenti di destinazione.

**Cause comuni:**
- GPO non collegata alla OU corretta
- Filtro di sicurezza che esclude l'utente o il computer
- WMI filter che esclude il target
- Cache locale delle GPO corrotta
- Servizio Group Policy Client non funzionante

**Risoluzione:**
```powershell
# Forzare l'aggiornamento delle GPO sul client
gpupdate /force

# Generare un report dettagliato delle GPO applicate
gpresult /h C:\gpresult.html /f

# Verificare la connettivita' verso il domain controller
nltest /dsgetdc:contoso.local

# Verificare che il client sia nella OU corretta
Get-ADComputer "PC-CONTABILITA01" | Select-Object DistinguishedName

# Verificare i filtri di sicurezza della GPO problematica
Get-GPPermission -Name "GPO-Sicurezza-Base" -All

# Pulire la cache locale delle GPO (ultima risorsa)
# Eliminare il contenuto di C:\Windows\System32\GroupPolicy\
# e C:\Windows\System32\GroupPolicyUsers\
# quindi eseguire gpupdate /force
```

---

### Problema: Account lockout frequenti di un utente

**Sintomi:** Un utente viene bloccato ripetutamente nonostante utilizzi la password corretta.

**Cause comuni:**
- Credenziali memorizzate obsolete su un dispositivo (sessione RDP, mapped drive, scheduled task)
- Dispositivo mobile con account Exchange/Office 365 con vecchia password
- Servizio Windows configurato con le vecchie credenziali dell'utente
- Attacco brute-force in corso

**Risoluzione:**
```powershell
# Identificare la fonte del lockout - cercare gli eventi 4740 sul PDC Emulator
$pdce = (Get-ADDomain).PDCEmulator
Get-WinEvent -ComputerName $pdce -FilterHashtable @{
    LogName='Security'; Id=4740
} | Where-Object {$_.Properties[0].Value -eq "nome.utente"} |
Select-Object TimeCreated, @{N='CallerComputer';E={$_.Properties[1].Value}}

# Controllare lo stato dell'account
Get-ADUser "nome.utente" -Properties LockedOut, lockoutTime, badPwdCount, badPasswordTime, LastBadPasswordAttempt |
    Select-Object Name, LockedOut, lockoutTime, badPwdCount, LastBadPasswordAttempt

# Sbloccare l'account
Unlock-ADAccount -Identity "nome.utente"

# Cercare scheduled task con le credenziali dell'utente sui server
$servers = Get-ADComputer -Filter {OperatingSystem -like "*Server*"}
$servers | ForEach-Object {
    Invoke-Command -ComputerName $_.Name -ScriptBlock {
        Get-ScheduledTask | Where-Object {$_.Principal.UserId -like "*nome.utente*"}
    } -ErrorAction SilentlyContinue
}
```

---

### Problema: Prestazioni degradate dopo aggiornamento

**Sintomi:** Dopo l'applicazione degli aggiornamenti, il server mostra un utilizzo di CPU, memoria o disco significativamente superiore alla baseline.

**Cause comuni:**
- L'aggiornamento ha riattivato servizi di telemetria o indicizzazione
- Ricostruzione indici in corso (WSUS, SQL Server, Exchange)
- Operazione di ottimizzazione post-aggiornamento in background
- Bug nell'aggiornamento stesso (regressione)

**Risoluzione:**
```bash
# Linux - Identificare il processo responsabile
top -b -n 1 | head -20
iostat -x 1 5
vmstat 1 10

# Verificare se ci sono operazioni di ricostruzione in corso
dmesg | tail -50
journalctl -p err --since "1 hour ago"
```

```powershell
# Windows - Identificare il processo responsabile
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet
Get-Counter '\Process(*)\% Processor Time' | Select-Object -ExpandProperty CounterSamples |
    Sort-Object CookedValue -Descending | Select-Object -First 10

# Verificare se Windows Update sta ancora lavorando in background
Get-Service wuauserv | Select-Object Status
Get-Process TiWorker -ErrorAction SilentlyContinue

# Se il problema persiste dopo 24 ore, considerare il rollback dell'aggiornamento
wusa /uninstall /kb:<numero_KB> /quiet /norestart
```

Se le prestazioni non tornano alla normalita' entro 24-48 ore e non sono identificabili operazioni post-aggiornamento legittime, attivare la procedura di rollback e segnalare il problema al vendor.

---

### Evoluzione del Patch Management: Deprecazione WSUS e Hotpatching in Windows Server 2025

A partire dalla seconda meta' del 2024 e nel corso del 2025-2026, il panorama della gestione delle patch in ambiente Windows Server ha subito trasformazioni significative che ogni amministratore di sistema deve conoscere e pianificare.

**Deprecazione di WSUS.** Microsoft ha annunciato ufficialmente la deprecazione di Windows Server Update Services (WSUS) a settembre 2024. Sebbene il ruolo WSUS sia ancora incluso in Windows Server 2025 e continui a funzionare, Microsoft ha cessato lo sviluppo attivo di nuove funzionalita'. Lo stato di "deprecated" significa che WSUS ricevera' esclusivamente aggiornamenti di manutenzione e compatibilita', ma non verranno introdotti miglioramenti funzionali. Questa decisione segna una transizione strategica verso soluzioni di patch management basate su cloud, in particolare Microsoft Intune e Windows Autopatch. Le organizzazioni che dipendono esclusivamente da WSUS devono iniziare a pianificare una migrazione graduale verso queste piattaforme moderne, soprattutto per la gestione di ambienti ibridi, remoti e con dispositivi mobili. La raccomandazione operativa e' adottare un approccio transitorio: mantenere WSUS per l'infrastruttura on-premises esistente mentre si implementa Intune per i nuovi deployment e i dispositivi gestiti in cloud.

**Hotpatching su Windows Server 2025.** Una delle innovazioni piu' rilevanti di Windows Server 2025 e' il supporto nativo per l'hotpatching, ovvero l'applicazione di patch di sicurezza senza necessita' di riavvio del server. Tuttavia, questa funzionalita' ha attraversato criticita' significative: una vulnerabilita' critica (CVE-2025-59287) nel modo in cui WSUS gestiva determinate richieste ha temporaneamente compromesso il funzionamento dell'hotpatching, richiedendo l'installazione dell'aggiornamento baseline di gennaio 2026 per ripristinare la funzionalita' completa. Per gli ambienti che adottano l'hotpatching, e' fondamentale verificare che l'infrastruttura WSUS sia aggiornata con le patch cumulative piu' recenti e che la baseline di hotpatching sia stata correttamente applicata.

**Blocco degli aggiornamenti ESU tramite WSUS.** A partire dall'aggiornamento di sicurezza di settembre 2025, WSUS in esecuzione su Windows Server 2025 ha rimosso le dipendenze da codice legacy non piu' supportato. Di conseguenza, i sistemi operativi Windows che hanno raggiunto la fine del ciclo di vita (end-of-life) non ricevono piu' automaticamente gli Extended Security Updates (ESU) tramite WSUS, a meno che non vengano configurate azioni aggiuntive specifiche. Gli amministratori che gestiscono ancora server Windows Server 2012 R2 o 2016 in regime ESU devono verificare la corretta configurazione dei prodotti e delle classificazioni WSUS e, se necessario, distribuire manualmente le chiavi di attivazione ESU.

**Aggiornamenti in-place tramite Windows Update.** Microsoft ha iniziato a offrire Windows Server 2025 come aggiornamento feature opzionale tramite Windows Update per i sistemi Windows Server 2019 e Windows Server 2022. Prima di utilizzare questa modalita' di aggiornamento, gli amministratori devono installare l'aggiornamento cumulativo di marzo 2026 (o successivo) e abilitare esplicitamente la policy di feature update. Questa opzione rappresenta una semplificazione significativa del processo di migrazione, ma richiede una pianificazione accurata: test approfonditi in ambiente di staging, verifica della compatibilita' delle applicazioni, backup completo del sistema e una strategia di rollback collaudata. L'aggiornamento in-place non e' raccomandato per server con ruoli critici come Domain Controller o server SQL di produzione senza un'adeguata validazione preventiva.

**Hardening delle comunicazioni WSUS.** Windows Server 2025 ha introdotto modifiche di hardening alle comunicazioni WSUS, richiedendo connessioni TLS 1.2 o superiori per la sincronizzazione tra server upstream e downstream. I certificati auto-firmati non sono piu' accettati nella configurazione predefinita, e gli amministratori devono assicurarsi che l'infrastruttura PKI aziendale fornisca certificati validi per tutti i server WSUS della catena. Queste modifiche migliorano significativamente la sicurezza del canale di distribuzione delle patch, prevenendo attacchi man-in-the-middle che potrebbero consentire l'iniezione di aggiornamenti malevoli.

La combinazione di questi cambiamenti rende il 2025-2026 un periodo di transizione critico per le strategie di patch management enterprise. Le organizzazioni devono investire nella formazione del personale sulle nuove piattaforme cloud-based, pianificare la coesistenza di WSUS e Intune durante il periodo transitorio e aggiornare le procedure operative per incorporare le nuove funzionalita' di hotpatching e le restrizioni ESU.

---

## Esercizi

1. **Lab — patch ring deployment.** 3 ring (canary, early, broad); definisci membership + cadenza promotion.
2. **Stretch — Ubuntu Pro live patching.** Confronta cost vs reboot frequency; quando vale.

## Auto-valutazione

1. Patch tuesday vs emergency: criteri.
2. Live patching: limiti.
3. Baseline hardening: quando applicare?

## Collegamenti incrociati

- Modulo 02 — `../02-LINUX-POWERUSER/`.
- Modulo 03 — `../03-WINDOWS-POWERUSER/`.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Patch tuesday** | Microsoft monthly patch cadence. |
| **Live patching** | Aggiornamento kernel senza reboot. |
| **Baseline hardening** | Configurazione iniziale sicura. |
| **Patch ring** | Deployment progressivo a gruppi. |
| **CIS Benchmark** | Standard hardening Center for Internet Security. |