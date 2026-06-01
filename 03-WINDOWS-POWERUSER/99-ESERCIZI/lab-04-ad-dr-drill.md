# Lab 04 — AD Forest Recovery e DR Drill

> **Modulo di riferimento:** [34-disaster-recovery-ad-pki.md](../34-disaster-recovery-ad-pki.md), [01-active-directory.md](../01-active-directory.md), [11-servizi-certificati.md](../11-servizi-certificati.md)
> **Tempo stimato:** 3-4 ore
> **Livello:** advanced
> **Prerequisiti:** Forest AD multi-DC funzionante (lab-01), PKI enterprise configurata, Windows Server 2022, accesso Domain Admin + DSRM password
> **Ultimo aggiornamento:** 2026-05-23

---

## Obiettivo

Eseguire un ciclo completo di disaster recovery per una foresta Active Directory: dal backup pianificato, attraverso la simulazione di un disastro catastrofico con perdita di tutti i DC, fino al ripristino completo della foresta, della CA enterprise e alla verifica post-recovery. Al termine si compilerà un report DR drill conforme agli standard enterprise.

> **Riferimento ufficiale:** [Microsoft Learn — AD Forest Recovery](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/forest-recovery-guide/ad-forest-recovery-guide)
> **Riferimento CA:** [Microsoft Learn — Back up and restore AD CS](https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/back-up-restore-ad-cs)

---

## Ambiente

| Ruolo | Hostname | IP | Sistema operativo |
|-------|----------|----|-------------------|
| DC primario (PDC Emulator, tutti i FSMO) | DC01 | 10.0.0.10 | Windows Server 2022 |
| DC secondario | DC02 | 10.0.0.11 | Windows Server 2022 |
| Enterprise CA (su DC01 o server dedicato) | CA01 | 10.0.0.12 | Windows Server 2022 |
| Client di test | WIN-CLIENT | 10.0.0.50 | Windows 11 |

- Dominio: `lab.local`
- Foresta: single-domain, functional level 2016+
- Snapshot di tutte le VM **prima di iniziare**

> **ATTENZIONE:** Questo lab è distruttivo. Eseguirlo esclusivamente in ambiente di laboratorio isolato. Mai in produzione.

---

## Parte 1 — Preparazione Backup (45 min)

### 1.1 Installare Windows Server Backup su tutti i DC

```powershell
# Eseguire su DC01 e DC02
Install-WindowsFeature Windows-Server-Backup -IncludeManagementTools

# Verificare installazione
Get-WindowsFeature Windows-Server-Backup
```

**Output atteso:**

```
Display Name                       Name                    Install State
------------                       ----                    -------------
[X] Windows Server Backup          Windows-Server-Backup   Installed
```

### 1.2 System State backup di DC01 (FSMO holder)

```powershell
# Creare cartella destinazione backup
New-Item -Path "D:\Backup\SystemState" -ItemType Directory -Force

# Avviare backup System State
# Include: AD DS database (ntds.dit), SYSVOL, Registry, boot files, COM+ class registration
wbadmin start systemstatebackup -backupTarget:D: -quiet

# Tempo stimato: 15-30 minuti a seconda della dimensione del database AD
```

**Output atteso (fine backup):**

```
The backup operation successfully completed.
The backup of volume (C:) completed successfully.
Summary of the backup operation:
------------------
The backup operation successfully completed.
```

> **Nota:** Il parametro `-quiet` elimina le richieste di conferma interattive. In produzione, valutare `-backupTarget:\\server\share` per backup remoti.

### 1.3 System State backup di DC02

```powershell
# Stesso comando su DC02
wbadmin start systemstatebackup -backupTarget:D: -quiet
```

### 1.4 Verificare i backup disponibili

```powershell
# Su ciascun DC: elencare le versioni di backup
wbadmin get versions

# Output piu' dettagliato
wbadmin get versions -backupTarget:D:
```

**Output atteso:**

```
Backup time: 23/05/2026 10:30
Backup location: Fixed Disk labeled D:
Version identifier: 05/23/2026-08:30
Can recover: Application(s), System State
```

### 1.5 Backup del database CA

```powershell
# Su CA01 (o DC01 se la CA e' co-hosted)
# Creare directory di destinazione
New-Item -Path "D:\Backup\CA" -ItemType Directory -Force

# Backup completo della CA: database, log, certificato CA, chiave privata
certutil -backup D:\Backup\CA

# Verra' richiesta una password per proteggere la chiave privata
# Inserire una password complessa e documentarla in modo sicuro
```

**Output atteso:**

```
Certutil: -backup command completed successfully.
```

Verificare il contenuto del backup:

```powershell
Get-ChildItem D:\Backup\CA -Recurse

# Deve contenere:
#   DataBase\  — file .edb del database CA
#   CA01.lab.local.p12  — certificato e chiave privata CA (PKCS#12)
```

### 1.6 Backup del certificato CA e CRL separatamente

```powershell
# Esportare solo il certificato CA (senza chiave privata)
certutil -ca.cert D:\Backup\CA\ca-cert.cer

# Esportare la CRL corrente
certutil -getCRL D:\Backup\CA\current.crl

# Verificare il certificato esportato
certutil -verify D:\Backup\CA\ca-cert.cer
```

### 1.7 Schedulare backup automatico con PowerShell

```powershell
# Creare policy di backup schedulato (giornaliero alle 02:00)
$policy = New-WBPolicy
$systemState = New-WBSystemState
Add-WBSystemState -Policy $policy
$target = New-WBBackupTarget -VolumePath "D:"
Add-WBBackupTarget -Policy $policy -Target $target

# Schedulare alle 02:00
Set-WBSchedule -Policy $policy -Schedule 02:00

# Applicare la policy
Set-WBPolicy -Policy $policy -Force

# Verificare la policy configurata
Get-WBPolicy -Editable
```

**Output atteso:**

```
Schedule       : 02:00
BackupTargets  : {D:}
VolumesToBackup: {}
SystemState    : True
```

### 1.8 Creare script di backup completo riutilizzabile

```powershell
# Salvare come D:\Scripts\Full-DR-Backup.ps1
$ErrorActionPreference = 'Stop'
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$logFile   = "D:\Backup\Logs\backup-$timestamp.log"

New-Item -Path "D:\Backup\Logs" -ItemType Directory -Force | Out-Null

function Write-Log {
    param([string]$Message)
    $entry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
    Add-Content -Path $logFile -Value $entry
    Write-Host $entry
}

Write-Log "=== Inizio backup DR ==="

# 1. System State
Write-Log "Avvio System State backup..."
wbadmin start systemstatebackup -backupTarget:D: -quiet
if ($LASTEXITCODE -eq 0) {
    Write-Log "System State backup completato con successo"
} else {
    Write-Log "ERRORE: System State backup fallito (exit code $LASTEXITCODE)"
}

# 2. CA backup (solo se il ruolo CA e' installato)
if (Get-WindowsFeature ADCS-Cert-Authority | Where-Object Installed) {
    Write-Log "Avvio backup CA..."
    $caBackupDir = "D:\Backup\CA\$timestamp"
    New-Item -Path $caBackupDir -ItemType Directory -Force | Out-Null
    certutil -backup $caBackupDir
    Write-Log "Backup CA completato"
}

# 3. Esportare configurazione DNS
Write-Log "Esportazione zone DNS..."
$dnsZones = Get-DnsServerZone | Where-Object { $_.ZoneType -ne 'Forwarder' }
foreach ($zone in $dnsZones) {
    Export-DnsServerZone -Name $zone.ZoneName -FileName "dns-$($zone.ZoneName).bak"
    Write-Log "Zona DNS esportata: $($zone.ZoneName)"
}

# 4. Esportare GPO
Write-Log "Esportazione Group Policy Objects..."
$gpoBackupDir = "D:\Backup\GPO\$timestamp"
New-Item -Path $gpoBackupDir -ItemType Directory -Force | Out-Null
Get-GPO -All | ForEach-Object {
    Backup-GPO -Guid $_.Id -Path $gpoBackupDir | Out-Null
    Write-Log "GPO esportata: $($_.DisplayName)"
}

Write-Log "=== Backup DR completato ==="
```

---

## Parte 2 — Documentare lo Stato Pre-Disastro e Simulare il Disastro (30 min)

### 2.1 Raccogliere lo stato pre-disastro

Questa documentazione e' essenziale per la verifica post-recovery.

```powershell
# Creare directory per la documentazione
New-Item -Path "D:\DR-Docs\Pre-Disaster" -ItemType Directory -Force

# === Stato AD ===
# Diagnostic completa di AD
dcdiag /v /c > D:\DR-Docs\Pre-Disaster\dcdiag-full.txt

# Stato replica tra DC
repadmin /showrepl > D:\DR-Docs\Pre-Disaster\repadmin-showrepl.txt
repadmin /replsummary > D:\DR-Docs\Pre-Disaster\repadmin-replsummary.txt

# Titolari FSMO
netdom query fsmo > D:\DR-Docs\Pre-Disaster\fsmo-holders.txt
```

**Output atteso (fsmo-holders.txt):**

```
Schema master               DC01.lab.local
Domain naming master        DC01.lab.local
PDC                         DC01.lab.local
RID pool manager            DC01.lab.local
Infrastructure master       DC01.lab.local
The command completed successfully.
```

```powershell
# === Stato DNS ===
Get-DnsServerZone | Format-Table -AutoSize > D:\DR-Docs\Pre-Disaster\dns-zones.txt
Resolve-DnsName lab.local -Type SOA > D:\DR-Docs\Pre-Disaster\dns-soa.txt
Resolve-DnsName _ldap._tcp.dc._msdcs.lab.local -Type SRV > D:\DR-Docs\Pre-Disaster\dns-srv-ldap.txt

# === Utenti e gruppi ===
Get-ADUser -Filter * -Properties MemberOf |
    Select-Object SamAccountName, Enabled, DistinguishedName |
    Export-Csv D:\DR-Docs\Pre-Disaster\ad-users.csv -NoTypeInformation

Get-ADGroup -Filter * |
    Select-Object Name, GroupScope, GroupCategory |
    Export-Csv D:\DR-Docs\Pre-Disaster\ad-groups.csv -NoTypeInformation

# === Stato GPO ===
Get-GPO -All |
    Select-Object DisplayName, Id, GpoStatus, CreationTime, ModificationTime |
    Export-Csv D:\DR-Docs\Pre-Disaster\gpo-list.csv -NoTypeInformation

# === Stato CA ===
certutil -ping > D:\DR-Docs\Pre-Disaster\ca-status.txt
certutil -CRL > D:\DR-Docs\Pre-Disaster\ca-crl-status.txt
certutil -view -restrict "Disposition=20" -out "RequestID,CommonName" > D:\DR-Docs\Pre-Disaster\ca-issued-certs.txt

# === Computer account ===
Get-ADComputer -Filter * |
    Select-Object Name, DNSHostName, OperatingSystem |
    Export-Csv D:\DR-Docs\Pre-Disaster\ad-computers.csv -NoTypeInformation
```

### 2.2 Verificare salute AD prima del disastro

```powershell
# Tutti i test dcdiag devono essere PASSED
dcdiag /q

# Se ci sono errori, risolverli PRIMA di procedere
# Errori comuni:
#   DNS: verificare che i record _msdcs siano presenti
#   Replica: forzare replica con repadmin /syncall /AdeP
```

### 2.3 Simulare il disastro — Spegnimento controllato

> **PUNTO DI NON RITORNO:** Prima di procedere, verificare che:
> 1. Tutti i backup in Parte 1 siano completati con successo
> 2. La documentazione pre-disastro sia salvata su un supporto esterno o host separato
> 3. Gli snapshot VM siano stati creati

```powershell
# Annotare timestamp di inizio disastro
$disasterStart = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "DISASTER START: $disasterStart"

# Spegnere DC02 per primo (non-FSMO holder)
Stop-Computer -ComputerName DC02 -Force

# Attendere 30 secondi
Start-Sleep -Seconds 30

# Spegnere DC01 (FSMO holder) — simula perdita catastrofica
Stop-Computer -Force
```

> **Scenario simulato:** Un guasto al sistema storage ha corrotto i dischi di tutti i Domain Controller. L'unico materiale disponibile e' il backup System State e il backup della CA.

---

## Parte 3 — Procedura di Forest Recovery (60 min)

> **Riferimento:** [Microsoft Learn — AD Forest Recovery Steps](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/forest-recovery-guide/ad-forest-recovery-procedures)

### 3.1 Isolare la rete

Prima di qualsiasi ripristino, isolare il segmento di rete per evitare conflitti con eventuali DC zombie.

```powershell
# Sul hypervisor: scollegare le VM dalla rete di produzione
# Creare un virtual switch isolato
# In Hyper-V:
New-VMSwitch -Name "DR-Isolated" -SwitchType Private
Get-VM -Name DC01 | Get-VMNetworkAdapter | Connect-VMNetworkAdapter -SwitchName "DR-Isolated"
```

### 3.2 Avviare DC01 in Directory Services Restore Mode (DSRM)

```powershell
# Metodo 1: da console di recovery
# Al boot premere F8 → Directory Services Restore Mode

# Metodo 2: configurare DSRM boot da un ambiente PE o dalla console
bcdedit /set safeboot dsrepair

# Riavviare
Restart-Computer -Force
```

Dopo il riavvio in DSRM:

```powershell
# Login con account DSRM locale: .\Administrator e password DSRM
# Verificare che siamo in DSRM
(Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\SafeBoot").Option
# Output atteso: dovrebbe essere presente l'opzione DSRM
```

### 3.3 Ripristinare System State su DC01

```powershell
# Elencare i backup disponibili
wbadmin get versions -backupTarget:D:

# Annotare il version identifier (es. 05/23/2026-08:30)
# Ripristinare System State con restore autoritativo di SYSVOL
wbadmin start systemstaterecovery -version:05/23/2026-08:30 -backupTarget:D: -authSysvol -quiet

# -authSysvol: rende SYSVOL autoritativo (fondamentale per forest recovery)
# Tempo stimato: 20-40 minuti
```

**Output atteso:**

```
The system state recovery operation completed successfully.
You need to restart the server to complete the recovery operation.
```

```powershell
# NON riavviare ancora. Prima completare la configurazione.
```

### 3.4 Invalidare il pool RID corrente

```powershell
# Prevenire il riutilizzo di RID gia' assegnati ai DC distrutti
# Aprire ntdsutil
ntdsutil
# Al prompt: roles
# Al prompt: connections
# Al prompt: connect to server DC01
# Al prompt: quit
# Al prompt: seize rid master

# Equivalente one-liner (Windows Server 2022):
ntdsutil "roles" "connections" "connect to server DC01.lab.local" "quit" "seize rid master" "quit" "quit"
```

### 3.5 Impostare nuovo pool RID

```powershell
# Incrementare il pool RID per evitare collisioni
# Via ADSI Edit o PowerShell:

# Verificare RID pool corrente
dcdiag /test:ridmanager /v

# Invalidare pool RID e forzare nuovo range
# Questo previene duplicati SID
$ridManager = [ADSI]"LDAP://CN=RID Manager$,CN=System,DC=lab,DC=local"
# Il valore viene aggiornato automaticamente dopo il seize del ruolo RID Master
```

### 3.6 Rimuovere il boot DSRM e riavviare in modalita' normale

```powershell
# Rimuovere il flag DSRM dal boot
bcdedit /deletevalue safeboot

# Riavviare DC01 in modalita' normale
Restart-Computer -Force
```

### 3.7 Verificare avvio di DC01

```powershell
# Dopo il riavvio, login come lab\Administrator

# Verificare che AD DS sia avviato
Get-Service NTDS, DNS, Netlogon, KDC

# Output atteso: tutti Running
```

**Output atteso:**

```
Status   Name               DisplayName
------   ----               -----------
Running  dns                DNS Server
Running  KDC                Kerberos Key Distribution Center
Running  Netlogon           Netlogon
Running  NTDS               Active Directory Domain Services
```

```powershell
# Test rapido AD
Get-ADDomainController -Filter *

# Dovrebbe mostrare solo DC01 (DC02 e' ancora "registrato" ma offline)
```

### 3.8 Metadata cleanup — Rimuovere DC distrutti

```powershell
# Rimuovere i metadati di DC02 (distrutto)
# Metodo PowerShell (Windows Server 2022):
$dc02 = Get-ADDomainController -Identity "DC02"
Remove-ADDomainController -Identity $dc02 -ForceRemoval -Confirm:$false

# Metodo alternativo con ntdsutil:
ntdsutil
# metadata cleanup
# connections
# connect to server DC01.lab.local
# quit
# select operation target
# list domains
# select domain 0
# list sites
# select site 0
# list servers in site
# select server <numero di DC02>
# quit
# remove selected server
```

Verificare la pulizia:

```powershell
# DC02 non deve piu' apparire
Get-ADDomainController -Filter * | Select-Object Name, IPv4Address, IsGlobalCatalog

# Verificare anche nei record DNS
Get-DnsServerResourceRecord -ZoneName "lab.local" -Name "DC02" -ErrorAction SilentlyContinue
# Non dovrebbe restituire nulla o un errore "not found"
```

### 3.9 Seize di tutti i ruoli FSMO su DC01

```powershell
# Se DC01 era gia' il FSMO holder, questo passaggio e' una conferma.
# Se i ruoli erano distribuiti tra DC01 e DC02, eseguire il seize:

# Seize tutti e 5 i ruoli FSMO
Move-ADDirectoryServerOperationMasterRole -Identity "DC01" `
    -OperationMasterRole SchemaMaster, DomainNamingMaster, PDCEmulator, RIDMaster, InfrastructureMaster `
    -Force

# Verificare
netdom query fsmo
```

**Output atteso:**

```
Schema master               DC01.lab.local
Domain naming master        DC01.lab.local
PDC                         DC01.lab.local
RID pool manager            DC01.lab.local
Infrastructure master       DC01.lab.local
The command completed successfully.
```

### 3.10 Pulizia record DNS orfani

```powershell
# Rimuovere record DNS di DC02
$dcToClean = "DC02"
$zoneName  = "lab.local"

# Record A
Remove-DnsServerResourceRecord -ZoneName $zoneName -Name $dcToClean -RRType A -Force -ErrorAction SilentlyContinue

# Record _msdcs (piu' importanti)
$msdcsZone = "_msdcs.$zoneName"
Get-DnsServerResourceRecord -ZoneName $msdcsZone |
    Where-Object { $_.RecordData.DomainName -like "*$dcToClean*" } |
    ForEach-Object {
        Remove-DnsServerResourceRecord -ZoneName $msdcsZone -Name $_.HostName -RRType $_.RecordType -Force
        Write-Host "Rimosso: $($_.HostName) ($($_.RecordType))"
    }

# SRV records nel dominio principale
Get-DnsServerResourceRecord -ZoneName $zoneName -RRType SRV |
    Where-Object { $_.RecordData.DomainName -like "*$dcToClean*" } |
    ForEach-Object {
        Remove-DnsServerResourceRecord -ZoneName $zoneName -Name $_.HostName -RRType SRV -Force
        Write-Host "Rimosso SRV: $($_.HostName)"
    }
```

### 3.11 Ricostruire DC02 come nuovo Domain Controller

```powershell
# Su una nuova VM con Windows Server 2022 installato pulito
# Hostname: DC02, IP: 10.0.0.11, DNS: 10.0.0.10 (DC01)

# Rinominare il server
Rename-Computer -NewName "DC02" -Restart

# Dopo il riavvio, installare il ruolo AD DS
Install-WindowsFeature AD-Domain-Services -IncludeManagementTools

# Promuovere a DC nella foresta esistente
Install-ADDSDomainController `
    -DomainName "lab.local" `
    -InstallDns:$true `
    -Credential (Get-Credential) `
    -SafeModeAdministratorPassword (ConvertTo-SecureString "P@ssw0rdDSRM!" -AsPlainText -Force) `
    -SiteName "Default-First-Site-Name" `
    -ReplicationSourceDC "DC01.lab.local" `
    -Force:$true

# Il server si riavviera' automaticamente
# Tempo stimato: 10-20 minuti
```

### 3.12 Verificare replica dopo promozione DC02

```powershell
# Attendere 5 minuti dopo il riavvio di DC02, poi su DC01:
repadmin /showrepl

# Forzare replica bidirezionale
repadmin /syncall DC01 /AdeP
repadmin /syncall DC02 /AdeP

# Verificare che non ci siano errori
repadmin /replsummary
```

**Output atteso (replsummary):**

```
Replication Summary Start Time: 2026-05-23 12:30:00

Beginning data collection for replication summary, this may take awhile:
  ......

Source DSA          largest delta    fails/total %%   error
DC01               00m:05s          0 /   5    0
DC02               00m:08s          0 /   5    0
```

---

## Parte 4 — Recovery della Certification Authority (30 min)

### 4.1 Reinstallare il ruolo CA (se necessario)

```powershell
# Su CA01 (o DC01 se co-hosted):
# Se il server e' stato ripristinato dal backup, il ruolo CA potrebbe essere gia' presente.
# Se si tratta di un'installazione pulita:

Install-WindowsFeature ADCS-Cert-Authority -IncludeManagementTools

# NON configurare ancora — prima ripristinare il database dal backup
```

### 4.2 Ripristinare il database CA dal backup

```powershell
# Fermare il servizio CA
Stop-Service CertSvc

# Ripristinare database e log
certutil -restore D:\Backup\CA

# Se richiesta la password, inserire quella usata durante il backup (Parte 1.5)
```

**Output atteso:**

```
Certutil: -restore command completed successfully.
```

```powershell
# Riavviare il servizio CA
Start-Service CertSvc

# Verificare stato del servizio
Get-Service CertSvc
```

### 4.3 Verificare pubblicazione CRL

```powershell
# Pubblicare una nuova CRL
certutil -CRL

# Verificare la CRL
certutil -URL http://CA01.lab.local/CertEnroll/lab-CA01-CA.crl

# Verificare via LDAP
certutil -verify -urlfetch D:\Backup\CA\ca-cert.cer
```

**Output atteso:**

```
Leaf certificate revocation check passed
CertUtil: -verify command completed successfully.
```

### 4.4 Verificare enrollment dei certificati

```powershell
# Verificare che i template siano accessibili
certutil -CATemplates

# Richiedere un certificato di test (tipo Computer)
# Da un client o server unito al dominio:
$enrollment = Get-Certificate -Template "Machine" -CertStoreLocation Cert:\LocalMachine\My
$enrollment.Status

# Output atteso: Issued
```

```powershell
# Verificare il certificato emesso
Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.NotBefore -gt (Get-Date).AddHours(-1) } |
    Select-Object Subject, Issuer, NotBefore, NotAfter, Thumbprint |
    Format-List
```

### 4.5 Verificare la catena di certificati completa

```powershell
# Testare la catena completa
$cert = Get-ChildItem Cert:\LocalMachine\My | Select-Object -First 1
$chain = New-Object Security.Cryptography.X509Certificates.X509Chain
$chain.Build($cert)

$chain.ChainStatus | ForEach-Object {
    Write-Host "Status: $($_.Status) - $($_.StatusInformation)"
}

# Output atteso: nessun errore, oppure:
# Status: NoError - No errors detected.
```

---

## Parte 5 — Verifica Post-Recovery (30 min)

### 5.1 Diagnostic completa AD

```powershell
# dcdiag completo e verboso su tutti i DC
dcdiag /v /c /e > D:\DR-Docs\Post-Recovery\dcdiag-full.txt

# Versione rapida: solo errori
dcdiag /q
```

**Output atteso (dcdiag /q):** Nessun output = tutti i test passati.

Se ci sono errori:

```
# Errori comuni post-recovery:

# "Failed test SystemLog" → eventi di errore nel log di sistema, spesso transitori
#   Verificare: Get-EventLog -LogName System -EntryType Error -Newest 20

# "Failed test Services" → un servizio AD non e' partito
#   Verificare: Get-Service NTDS, DNS, KDC, Netlogon

# "Failed test FrsEvent" o "DFSREvent" → SYSVOL non ancora replicato
#   Attendere 15 minuti e ripetere. Se persiste:
#   dfsrdiag pollad
```

### 5.2 Verifica replicazione

```powershell
repadmin /replsummary > D:\DR-Docs\Post-Recovery\repadmin-replsummary.txt

# Dettaglio per ogni naming context
repadmin /showrepl DC01 > D:\DR-Docs\Post-Recovery\repadmin-showrepl-dc01.txt
repadmin /showrepl DC02 > D:\DR-Docs\Post-Recovery\repadmin-showrepl-dc02.txt

# Verificare uptime della replica (deve essere < tempo dal ripristino)
repadmin /showrepl DC01 | Select-String "Last attempt"
```

### 5.3 Test autenticazione utenti

```powershell
# Creare un utente di test
New-ADUser -Name "DR-TestUser" `
    -SamAccountName "drtestuser" `
    -UserPrincipalName "drtestuser@lab.local" `
    -AccountPassword (ConvertTo-SecureString "T3stP@ss!" -AsPlainText -Force) `
    -Enabled $true

# Verificare autenticazione (da un client di dominio o via PowerShell remoto)
$cred = Get-Credential -UserName "lab\drtestuser" -Message "Test autenticazione post-DR"
Test-ComputerSecureChannel -Credential $cred

# Alternativa: test LDAP bind
$ldap = New-Object DirectoryServices.DirectoryEntry("LDAP://DC01.lab.local", "drtestuser@lab.local", "T3stP@ss!")
if ($ldap.Name -ne $null) {
    Write-Host "LDAP bind riuscito: autenticazione funzionante" -ForegroundColor Green
} else {
    Write-Host "ERRORE: LDAP bind fallito" -ForegroundColor Red
}
```

### 5.4 Verificare applicazione Group Policy

```powershell
# Su un client di dominio
gpupdate /force

# Verificare risultato applicazione
gpresult /r > D:\DR-Docs\Post-Recovery\gpresult.txt

# Verificare via PowerShell
Get-GPResultantSetOfPolicy -ReportType Html -Path D:\DR-Docs\Post-Recovery\rsop.html
```

### 5.5 Validazione catena certificati

```powershell
# Verificare che la CA enterprise sia raggiungibile
certutil -ping
# Output atteso: "Server 'CA01.lab.local ICertRequest2' ICertRequest interface is alive"

# Verificare AIA e CDP
certutil -verify -urlfetch Cert:\LocalMachine\My\<thumbprint>

# Verificare che Auto-Enrollment funzioni (dopo gpupdate)
certutil -pulse
```

### 5.6 Confronto stato pre e post-recovery

```powershell
# Confrontare il numero di oggetti AD
$preUsers  = (Import-Csv D:\DR-Docs\Pre-Disaster\ad-users.csv).Count
$postUsers = (Get-ADUser -Filter *).Count
Write-Host "Utenti pre-disaster: $preUsers | post-recovery: $postUsers"

$preGroups  = (Import-Csv D:\DR-Docs\Pre-Disaster\ad-groups.csv).Count
$postGroups = (Get-ADGroup -Filter *).Count
Write-Host "Gruppi pre-disaster: $preGroups | post-recovery: $postGroups"

$preGPO  = (Import-Csv D:\DR-Docs\Pre-Disaster\gpo-list.csv).Count
$postGPO = (Get-GPO -All).Count
Write-Host "GPO pre-disaster: $preGPO | post-recovery: $postGPO"

# Eventuali differenze vanno investigate e documentate nel report DR
```

### 5.7 Pulizia post-drill

```powershell
# Rimuovere utente di test
Remove-ADUser -Identity "drtestuser" -Confirm:$false

# Ricollegare le VM alla rete di produzione (se applicabile)
# Get-VM -Name DC01 | Get-VMNetworkAdapter | Connect-VMNetworkAdapter -SwitchName "Production"
```

---

## Parte 6 — DR Drill Report Template (15 min)

Compilare il seguente report dopo ogni DR drill. Salvare in formato strutturato.

### 6.1 Template report

```
================================================================
              DR DRILL REPORT — FORESTA lab.local
================================================================

Data drill:            2026-05-23
Responsabile:          [Nome]
Partecipanti:          [Nomi]

================================================================
1. SCENARIO
================================================================
Descrizione:           Perdita catastrofica di tutti i DC
Causa simulata:        Guasto storage array
Componenti colpiti:    DC01, DC02, CA01

================================================================
2. METRICHE
================================================================

                       TARGET          RAGGIUNTO
RTO (Recovery Time):   4 ore           [__:__]
RPO (Recovery Point):  24 ore          [__:__]

Timeline:
  Inizio disastro:     [HH:MM]
  Inizio recovery:     [HH:MM]
  DC01 operativo:      [HH:MM]  (delta: __ min)
  DC02 operativo:      [HH:MM]  (delta: __ min)
  CA operativa:        [HH:MM]  (delta: __ min)
  Verifica completata: [HH:MM]  (delta: __ min)

================================================================
3. CHECKLIST VERIFICA POST-RECOVERY
================================================================
[  ] dcdiag /q senza errori su tutti i DC
[  ] repadmin /replsummary senza failure
[  ] Autenticazione utenti funzionante
[  ] Group Policy applicate correttamente
[  ] DNS resolution funzionante (interno ed esterno)
[  ] CA operativa — enrollment funzionante
[  ] CRL pubblicata e valida
[  ] Catena certificati verificata
[  ] SYSVOL replicato e accessibile

================================================================
4. PROBLEMI RISCONTRATI
================================================================

Nr | Gravita'   | Descrizione              | Risoluzione           | Tempo
---|-----------|--------------------------|----------------------|------
1  | [C/H/M/L] | [descrizione problema]   | [come risolto]       | [min]
2  | [C/H/M/L] | [descrizione problema]   | [come risolto]       | [min]

================================================================
5. LESSONS LEARNED
================================================================

5.1  Cosa ha funzionato bene:
     -

5.2  Cosa non ha funzionato:
     -

5.3  Sorprese / imprevisti:
     -

================================================================
6. AZIONI DI MIGLIORAMENTO
================================================================

Nr | Azione                         | Responsabile | Scadenza   | Priorita'
---|--------------------------------|-------------|------------|----------
1  | [azione correttiva]            | [nome]      | [data]     | [C/H/M]
2  | [azione correttiva]            | [nome]      | [data]     | [C/H/M]

================================================================
7. APPROVAZIONE
================================================================

Firma responsabile IT:  _________________________  Data: __/__/____
Firma management:       _________________________  Data: __/__/____

================================================================
```

### 6.2 Script per generare report automatico

```powershell
# Script che raccoglie automaticamente le metriche per il report
$report = @{
    Date        = Get-Date -Format "yyyy-MM-dd"
    DCCount     = (Get-ADDomainController -Filter *).Count
    UserCount   = (Get-ADUser -Filter *).Count
    GroupCount  = (Get-ADGroup -Filter *).Count
    GPOCount    = (Get-GPO -All).Count
    DcdiagPass  = ((dcdiag /q 2>&1) | Measure-Object).Count -eq 0
    ReplHealthy = ((repadmin /replsummary 2>&1) -match "0 / .* 0").Count -gt 0
    CAOnline    = (certutil -ping 2>&1) -match "alive"
}

$report | Format-Table -AutoSize
Write-Host "`nDR Drill completato: $(if ($report.DcdiagPass -and $report.CAOnline) { 'SUCCESSO' } else { 'CON PROBLEMI — verificare' })"
```

---

## Risorse

| Risorsa | URL |
|---------|-----|
| AD Forest Recovery Guide | https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/forest-recovery-guide/ad-forest-recovery-guide |
| Forest Recovery Steps | https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/forest-recovery-guide/ad-forest-recovery-procedures |
| FSMO Role Seizure | https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/transfer-or-seize-fsmo-roles-in-ad-ds |
| Back up and restore AD CS | https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/back-up-restore-ad-cs |
| Metadata Cleanup | https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/deploy/ad-ds-metadata-cleanup |
| wbadmin Reference | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/wbadmin |
