# Scenario 03 — FSMO Seizure da DC Inaccessibile

> **Modulo di riferimento:** [01-active-directory.md](../01-active-directory.md), [25-active-directory-design-avanzato.md](../25-active-directory-design-avanzato.md), [34-disaster-recovery-ad-pki.md](../34-disaster-recovery-ad-pki.md)
> **Tempo stimato:** 1.5–2 ore
> **Livello:** advanced
> **Prerequisiti:** Lab AD multi-DC (almeno 2 DC), completamento moduli 01, 03, 25, 34
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

Venerdì sera, il data center primario subisce un guasto hardware irreversibile. Il Domain Controller principale (DC01.contoso.local, Windows Server 2022) è distrutto: scheda madre e storage array non recuperabili. DC01 deteneva tutti e 5 i ruoli FSMO. Non è disponibile un backup recente del System State di DC01 (l'ultimo risale a 45 giorni fa, oltre la tombstone lifetime).

L'ambiente è composto da:
- **DC01** (offline/distrutto) — tutti i ruoli FSMO, Global Catalog, DNS integrato AD
- **DC02** (online) — Global Catalog, DNS integrato AD, sito "Branch-Office"
- **DC03** (online) — DNS integrato AD, sito "DR-Site"

Il tuo compito è ripristinare la piena funzionalità del dominio.

---

## Fase 1 — Assessment (30 min)

### 1.1 Identificare i ruoli FSMO e il DC che li deteneva

```powershell
# Verificare chi detiene attualmente i ruoli FSMO
# Questi comandi mostreranno ancora DC01 come holder (anche se è offline)
netdom query fsmo

# Output atteso (DC01 offline):
# Schema master               DC01.contoso.local    <-- INACCESSIBILE
# Domain naming master         DC01.contoso.local    <-- INACCESSIBILE
# PDC                          DC01.contoso.local    <-- INACCESSIBILE
# RID pool manager             DC01.contoso.local    <-- INACCESSIBILE
# Infrastructure master        DC01.contoso.local    <-- INACCESSIBILE

# Alternativa PowerShell — ruoli forest-wide
Get-ADForest | Select-Object SchemaMaster, DomainNamingMaster

# Ruoli domain-wide
Get-ADDomain | Select-Object PDCEmulator, RIDMaster, InfrastructureMaster
```

### 1.2 Comprendere l'impatto per ruolo

```
Impatto della perdita di ogni ruolo FSMO:
┌─────────────────────────┬──────────────┬───────────────────────────────────────────────┐
│ Ruolo                   │ Scope        │ Impatto immediato                             │
├─────────────────────────┼──────────────┼───────────────────────────────────────────────┤
│ Schema Master           │ Forest       │ Nessuno (usato solo per modifiche schema,     │
│                         │              │ operazione rara)                              │
├─────────────────────────┼──────────────┼───────────────────────────────────────────────┤
│ Domain Naming Master    │ Forest       │ Nessuno (usato solo per aggiungere/rimuovere  │
│                         │              │ domini nella foresta)                         │
├─────────────────────────┼──────────────┼───────────────────────────────────────────────┤
│ PDC Emulator            │ Domain       │ ALTO: password changes non propagati          │
│                         │              │ immediatamente, time sync interrotto,         │
│                         │              │ GPO editor senza target preferito,            │
│                         │              │ account lockout inconsistente                 │
├─────────────────────────┼──────────────┼───────────────────────────────────────────────┤
│ RID Master              │ Domain       │ MEDIO: i DC esauriscono il pool RID           │
│                         │              │ assegnato → impossibile creare nuovi          │
│                         │              │ oggetti (utenti, gruppi, computer)            │
├─────────────────────────┼──────────────┼───────────────────────────────────────────────┤
│ Infrastructure Master   │ Domain       │ BASSO in ambiente single-domain con tutti     │
│                         │              │ DC come GC. ALTO in multi-domain: riferimenti │
│                         │              │ cross-domain non aggiornati                   │
└─────────────────────────┴──────────────┴───────────────────────────────────────────────┘
```

### 1.3 Verificare lo stato della replicazione

```powershell
# Controllare lo stato di replicazione tra i DC rimanenti
repadmin /showrepl DC02
repadmin /showrepl DC03

# Riepilogo della replicazione dell'intero dominio
repadmin /replsummary

# Cercare errori di replicazione (DC01 mostrerà fallimenti)
repadmin /showrepl * /csv | ConvertFrom-Csv |
    Where-Object { $_.'Number of Failures' -gt 0 } |
    Select-Object 'Destination DSA', 'Source DSA', 'Number of Failures', 'Last Failure Time' |
    Format-Table -AutoSize

# Verificare che DC02 e DC03 siano sincronizzati tra loro
repadmin /showrepl DC02 DC03 "DC=contoso,DC=local"

# Controllare il pool RID rimanente su DC02
# (critico: se sta per esaurirsi, il seize del RID Master è urgente)
$ridInfo = Get-ADObject "CN=RID Set,CN=DC02,OU=Domain Controllers,DC=contoso,DC=local" `
    -Properties rIDAllocationPool, rIDPreviousAllocationPool, rIDUsedPool, rIDNextRID
$poolStart = [int64]($ridInfo.rIDPreviousAllocationPool) -band 0xFFFFFFFF
$poolEnd = [int64]($ridInfo.rIDPreviousAllocationPool) -shr 32
$nextRID = $ridInfo.rIDNextRID
Write-Output "Pool corrente: $poolStart - $poolEnd"
Write-Output "Prossimo RID: $nextRID"
Write-Output "RID rimanenti: $($poolEnd - $nextRID)"
```

### 1.4 Scegliere il DC target per il seizure

```powershell
# Criteri di scelta:
# 1. DC più aggiornato (replicazione più recente con DC01)
# 2. Global Catalog server
# 3. Stessa rete/sito di DC01 (se possibile)

# Verificare quale DC ha gli USN più alti (replicazione più recente)
repadmin /showutdvec DC02 "DC=contoso,DC=local"
repadmin /showutdvec DC03 "DC=contoso,DC=local"

# Verificare chi è Global Catalog
Get-ADDomainController -Filter * | Select-Object Name, Site, IsGlobalCatalog,
    OperatingSystem, IPv4Address | Format-Table -AutoSize

# Per questo scenario, scegliamo DC02 (GC, più aggiornato)
```

---

## Fase 2 — Seize dei ruoli FSMO (30 min)

### 2.1 Metodo 1: ntdsutil (procedura interattiva classica)

```
# ATTENZIONE: il seize è un'operazione IRREVERSIBILE
# Il DC originale (DC01) NON deve MAI essere riportato online dopo il seize
# Se riportato online, causerà conflitti catastrofici

# Eseguire su DC02 come Domain Admin / Enterprise Admin

ntdsutil
  roles
  connections
  connect to server DC02.contoso.local
  quit

  # Seize dei ruoli (ordine raccomandato):

  # 1. PDC Emulator (impatto più alto — ripristinare per primo)
  seize PDC

  # Conferma: "Are you sure you want to perform the seizure?" → YES
  # Output atteso: "Role seized successfully"

  # 2. Infrastructure Master
  seize infrastructure master

  # 3. Domain Naming Master
  seize domain naming master

  # 4. Schema Master
  seize schema master

  # 5. RID Master (ultimo: richiede attenzione speciale)
  seize RID master
  # NOTA: dopo il seize del RID Master, il nuovo holder invaliderà
  # il pool RID corrente e ne allocherà uno nuovo per evitare
  # duplicazione SID

  quit
  quit
```

### 2.2 Metodo 2: PowerShell (alternativa moderna)

```powershell
# Move-ADDirectoryServerOperationMasterRole con -Force esegue il seize
# Senza -Force esegue un transfer (richiede che il DC originale sia online)

# Seize di tutti i ruoli su DC02
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" `
    -OperationMasterRole PDCEmulator, RIDMaster, InfrastructureMaster, `
    SchemaMaster, DomainNamingMaster `
    -Force -Confirm:$false

# Verificare i nuovi holder
Get-ADForest | Select-Object SchemaMaster, DomainNamingMaster
Get-ADDomain | Select-Object PDCEmulator, RIDMaster, InfrastructureMaster

# Output atteso: tutti i ruoli su DC02.contoso.local
```

### 2.3 Verificare il seizure

```powershell
# Verifica completa
netdom query fsmo

# Output atteso:
# Schema master               DC02.contoso.local
# Domain naming master         DC02.contoso.local
# PDC                          DC02.contoso.local
# RID pool manager             DC02.contoso.local
# Infrastructure master        DC02.contoso.local

# Verificare che i servizi funzionino
# Test PDC Emulator: cambio password
Set-ADAccountPassword -Identity "test.user" -Reset -NewPassword (
    ConvertTo-SecureString "Test@12345!" -AsPlainText -Force
)
# Se riesce senza errori: PDC Emulator funzionante

# Test RID Master: creazione nuovo oggetto
New-ADUser -Name "Test-RID-$(Get-Date -Format 'yyMMddHHmm')" `
    -SamAccountName "test-rid-check" -Enabled $false
# Se riesce: RID pool allocato correttamente
# Pulizia: Remove-ADUser -Identity "test-rid-check" -Confirm:$false

# Test time sync (PDC Emulator è la root del time sync nel dominio)
w32tm /query /source
# Deve mostrare una fonte esterna o NTP, non DC01
```

---

## Fase 3 — Metadata Cleanup (20 min)

### 3.1 Rimuovere DC01 da Active Directory

```powershell
# CRITICO: rimuovere tutti i riferimenti a DC01 per evitare errori di replicazione

# Metodo 1: ntdsutil metadata cleanup
ntdsutil
  metadata cleanup
  connections
  connect to server DC02.contoso.local
  quit
  select operation target
  list domains
  select domain 0
  list sites
  select site 0
  list servers in site
  # Identificare il numero di DC01 nella lista
  select server <numero-DC01>
  quit
  remove selected server
  quit
  quit

# Metodo 2: PowerShell (più pulito)
# Rimuovere l'oggetto server da AD Sites and Services
$dc01 = Get-ADDomainController -Identity "DC01" -ErrorAction SilentlyContinue
if ($dc01) {
    # Rimuovere l'oggetto NTDS Settings
    $ntdsDN = "CN=NTDS Settings,CN=DC01,CN=Servers,CN=Primary-Site,CN=Sites,CN=Configuration,DC=contoso,DC=local"
    Remove-ADObject -Identity $ntdsDN -Recursive -Confirm:$false

    # Rimuovere l'oggetto server
    $serverDN = "CN=DC01,CN=Servers,CN=Primary-Site,CN=Sites,CN=Configuration,DC=contoso,DC=local"
    Remove-ADObject -Identity $serverDN -Recursive -Confirm:$false

    Write-Output "[+] Oggetto DC01 rimosso da Sites and Services"
}
```

### 3.2 Pulizia record DNS

```powershell
# Rimuovere i record DNS di DC01

# Record A
$dnsZone = "contoso.local"
Remove-DnsServerResourceRecord -ZoneName $dnsZone -Name "DC01" -RRType A -Force -ErrorAction SilentlyContinue

# Record SRV per servizi DC (LDAP, Kerberos, GC)
$srvRecords = @(
    "_ldap._tcp.dc._msdcs.$dnsZone"
    "_kerberos._tcp.dc._msdcs.$dnsZone"
    "_ldap._tcp.$dnsZone"
    "_kerberos._tcp.$dnsZone"
    "_gc._tcp.$dnsZone"
    "_ldap._tcp.gc._msdcs.$dnsZone"
    "_kpasswd._tcp.$dnsZone"
    "_kpasswd._udp.$dnsZone"
)

foreach ($zone in $srvRecords) {
    Get-DnsServerResourceRecord -ZoneName $zone.Split('.',2)[1] -Name $zone.Split('.')[0] `
        -RRType SRV -ErrorAction SilentlyContinue |
        Where-Object { $_.RecordData.DomainName -match 'DC01' } |
        Remove-DnsServerResourceRecord -ZoneName $zone.Split('.',2)[1] -Force -ErrorAction SilentlyContinue
}

# Record CNAME nella zona _msdcs
Get-DnsServerResourceRecord -ZoneName "_msdcs.$dnsZone" -RRType CNAME -ErrorAction SilentlyContinue |
    Where-Object { $_.RecordData.HostNameAlias -match 'DC01' } |
    Remove-DnsServerResourceRecord -ZoneName "_msdcs.$dnsZone" -Force

# Rimuovere la zona di reverse lookup per IP di DC01 (se esiste record PTR)
# Remove-DnsServerResourceRecord -ZoneName "1.0.10.in-addr.arpa" -Name "10" -RRType PTR -Force

# Pulizia dei record stale
# Forzare scavenging
Start-DnsServerScavenging -Force

Write-Output "[+] Pulizia DNS completata"
```

### 3.3 Pulizia DFSR membership (se presente)

```powershell
# Se SYSVOL usa DFSR (default da Windows Server 2008 R2+):
# Rimuovere DC01 dalla membership DFSR

# Verificare il tipo di replica SYSVOL
$sysvolRepl = Get-ADObject "CN=DFSR-GlobalSettings,CN=System,DC=contoso,DC=local" `
    -Properties * -ErrorAction SilentlyContinue
if ($sysvolRepl) {
    Write-Output "SYSVOL replication: DFSR"

    # Rimuovere la membership di DC01 dal gruppo di replica Domain System Volume
    $dfsrMember = Get-ADObject -SearchBase "CN=Domain System Volume,CN=DFSR-GlobalSettings,CN=System,DC=contoso,DC=local" `
        -Filter {Name -eq 'DC01'} -ErrorAction SilentlyContinue
    if ($dfsrMember) {
        Remove-ADObject -Identity $dfsrMember.DistinguishedName -Recursive -Confirm:$false
        Write-Output "[+] DC01 rimosso dalla membership DFSR"
    }
}

# Forzare replica DFSR tra DC02 e DC03
repadmin /syncall DC02 /APed

# Verificare stato DFSR
Get-WmiObject -Namespace "root\microsoftdfs" -Class DfsrReplicationGroupConfig `
    -ComputerName DC02 | Select-Object ReplicationGroupName, ReplicationGroupGuid
```

### 3.4 Rimuovere l'oggetto computer di DC01

```powershell
# Rimuovere l'account computer di DC01 dalla OU Domain Controllers
$dc01Computer = Get-ADComputer -Identity "DC01" -ErrorAction SilentlyContinue
if ($dc01Computer) {
    Remove-ADComputer -Identity "DC01" -Confirm:$false
    Write-Output "[+] Account computer DC01 rimosso"
}

# Verificare che non ci siano riferimenti residui
Get-ADObject -Filter {Name -like "*DC01*"} -SearchBase "DC=contoso,DC=local" |
    Select-Object DistinguishedName, ObjectClass |
    Format-Table -AutoSize
# Deve restituire zero risultati
```

---

## Fase 4 — Rebuild e Redistribuzione (20 min)

### 4.1 Deployare un nuovo DC sostitutivo

```powershell
# Su un nuovo server (DC04) — installare il ruolo AD DS
Install-WindowsFeature AD-Domain-Services -IncludeManagementTools

# Promuovere a DC (replica dal DC02)
Install-ADDSDomainController `
    -DomainName "contoso.local" `
    -SiteName "Primary-Site" `
    -ReplicationSourceDC "DC02.contoso.local" `
    -InstallDns:$true `
    -DatabasePath "D:\NTDS" `
    -LogPath "D:\NTDS" `
    -SysvolPath "D:\SYSVOL" `
    -SafeModeAdministratorPassword (Read-Host -AsSecureString "DSRM Password") `
    -Force

# Dopo il reboot, verificare la promozione
Get-ADDomainController -Identity "DC04" |
    Select-Object Name, Site, IsGlobalCatalog, OperatingSystem
```

### 4.2 Abilitare Global Catalog su DC04

```powershell
# Promuovere DC04 a Global Catalog (se non fatto durante l'installazione)
$dc04ntds = Get-ADObject "CN=NTDS Settings,CN=DC04,CN=Servers,CN=Primary-Site,CN=Sites,CN=Configuration,DC=contoso,DC=local"
Set-ADObject -Identity $dc04ntds -Replace @{'options' = 1}

# Verificare
Get-ADDomainController -Identity "DC04" | Select-Object Name, IsGlobalCatalog
# Attendere la replica del GC (può richiedere tempo per domini grandi)
```

### 4.3 Ridistribuire i ruoli FSMO secondo best practice

```powershell
# Best practice Microsoft: NON tenere tutti i ruoli su un singolo DC
#
# Distribuzione raccomandata (single domain):
# DC02: PDC Emulator + RID Master (devono essere sullo stesso DC)
# DC04: Schema Master + Domain Naming Master + Infrastructure Master
#
# Nota: Schema Master e Domain Naming Master devono essere su un GC

# Trasferire (NON seize — DC02 è online) i ruoli forest-wide a DC04
Move-ADDirectoryServerOperationMasterRole -Identity "DC04" `
    -OperationMasterRole SchemaMaster, DomainNamingMaster, InfrastructureMaster

# Mantenere PDC Emulator e RID Master su DC02
# (già lì dopo il seize — nessuna azione necessaria)

# Verificare distribuzione finale
Write-Output "=== Ruoli Forest ==="
Get-ADForest | Format-List SchemaMaster, DomainNamingMaster

Write-Output "=== Ruoli Domain ==="
Get-ADDomain | Format-List PDCEmulator, RIDMaster, InfrastructureMaster

# Output atteso:
# SchemaMaster       : DC04.contoso.local
# DomainNamingMaster : DC04.contoso.local
# PDCEmulator        : DC02.contoso.local
# RIDMaster          : DC02.contoso.local
# InfrastructureMaster : DC04.contoso.local
```

### 4.4 Verificare la salute dell'ambiente

```powershell
# Test completo della salute AD
dcdiag /v /c /d /e /s:DC02

# Test specifici critici
dcdiag /test:Replications /s:DC02
dcdiag /test:Advertising /s:DC02
dcdiag /test:FsmoCheck /s:DC02
dcdiag /test:RidManager /s:DC02
dcdiag /test:KnowsOfRoleHolders /s:DC02

# Stessi test su DC04
dcdiag /test:Replications /s:DC04
dcdiag /test:Advertising /s:DC04

# Verificare replicazione finale
repadmin /replsummary
# Tutti i DC devono mostrare 0 errori

# Verificare DNS
dcdiag /test:DNS /s:DC02
dcdiag /test:DNS /s:DC04

# Configurare NTP su DC02 (PDC Emulator = root time sync)
w32tm /config /manualpeerlist:"time.windows.com,0x9" /syncfromflags:manual /reliable:yes /update
Restart-Service w32time
w32tm /resync /force
```

---

## Domande di Valutazione

<details>
<summary>1. Perché il DC originale non deve MAI essere riportato online dopo un seize?</summary>

Dopo il seize, il nuovo DC si è auto-assegnato i ruoli FSMO senza il consenso del DC originale. Se il vecchio DC venisse riportato online, crederebbe ancora di detenere i ruoli (non ha ricevuto il messaggio di transfer). Si avrebbero due DC che credono di essere il PDC Emulator, il RID Master, ecc. Le conseguenze includono: duplicazione di RID (SID duplicati che causano problemi di autorizzazione irreparabili), conflitti di replicazione, corruzione della directory. Il vecchio DC deve essere cancellato dalla directory (metadata cleanup) prima che qualsiasi hardware con lo stesso nome venga riutilizzato.
</details>

<details>
<summary>2. Perché il RID Master è il ruolo più delicato da seizzare?</summary>

Il RID Master alloca pool di RID (Relative Identifier) ai DC. Ogni RID viene usato una sola volta per creare il SID di un nuovo oggetto (utente, gruppo, computer). Se due DC avessero lo stesso pool, creerebbero oggetti con SID identici — una condizione irrecuperabile. Durante il seize, il nuovo RID Master invalida il pool corrente e ne alloca uno nuovo con un gap di sicurezza per evitare sovrapposizioni con eventuali RID già allocati ma non ancora replicati dal DC fallito. Per questo motivo, dopo il seize si perdono alcuni RID (il gap), ma si evita la duplicazione.
</details>

<details>
<summary>3. In un ambiente multi-dominio con un solo dominio, perché l'Infrastructure Master è meno critico?</summary>

L'Infrastructure Master è responsabile dell'aggiornamento dei "phantom records": riferimenti cross-domain a oggetti che risiedono in altri domini. In un ambiente single-domain, non esistono riferimenti cross-domain da aggiornare. Inoltre, se tutti i DC sono Global Catalog (come nella best practice per il single-domain), l'Infrastructure Master non ha lavoro da fare perché ogni DC ha già una copia di tutti gli oggetti della foresta nel suo catalogo globale parziale. In un ambiente multi-dominio con DC non-GC, l'Infrastructure Master è essenziale per mantenere la coerenza dei riferimenti.
</details>

<details>
<summary>4. Qual è l'ordine ottimale di seizure e perché?</summary>

L'ordine raccomandato è: (1) PDC Emulator — ha l'impatto operativo più alto e immediato (password sync, time sync, GPO editing, account lockout). (2) Infrastructure Master — poco impatto in single-domain ma necessario per la pulizia. (3) Domain Naming Master — impatto solo su aggiunta/rimozione domini, operazione rara. (4) Schema Master — impatto solo su estensioni schema, ancora più raro. (5) RID Master — ultimo perché il seize invalida il pool corrente; ritardarlo massimizza i RID utilizzabili dai DC rimanenti prima del gap. In un'emergenza dove i DC stanno esaurendo i RID, il RID Master va seizzato prima.
</details>

---

## Riferimenti

- [01-active-directory.md](../01-active-directory.md)
- [25-active-directory-design-avanzato.md](../25-active-directory-design-avanzato.md)
- [34-disaster-recovery-ad-pki.md](../34-disaster-recovery-ad-pki.md)
- Microsoft Learn — [Transfer or seize FSMO roles](https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/transfer-or-seize-fsmo-roles)
- Microsoft Learn — [Clean up server metadata](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/deploy/ad-ds-metadata-cleanup)
- Microsoft Learn — [FSMO placement and optimization](https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/fsmo-placement-and-optimization)
