# Lab 01 — Progettazione e deploy forest AD multi-tier

> **Modulo di riferimento:** [25-active-directory-design-avanzato.md](../25-active-directory-design-avanzato.md), [01-active-directory.md](../01-active-directory.md)
> **Tempo stimato:** 3-4 ore
> **Livello:** proficient
> **Prerequisiti:** 3 VM Windows Server 2022/2025 (DC-MI, DC-RM, DC-NA), rete lab con 3 subnet, completamento moduli 01, 02, 25
> **Ultimo aggiornamento:** 2026-05-23

---

## Obiettivo

Progettare e implementare una foresta Active Directory per un'azienda con sede centrale a Milano e filiali a Roma e Napoli. La foresta include 2 RWDC e 1 RODC, siti AD configurati con subnet e site link, struttura OU tier 0/1/2, DNS integrato in AD e verifica completa dell'infrastruttura.

---

## Ambiente

| VM | Ruolo | IP | Subnet |
|----|-------|----|--------|
| DC-MI | RWDC, primo DC della foresta | 10.10.10.10/24 | Milano HQ |
| DC-RM | RWDC, secondo DC | 10.10.20.10/24 | Roma Branch |
| DC-NA | RODC, branch DC | 10.10.30.10/24 | Napoli Branch |

- Windows Server 2022 o 2025 Datacenter (installazione Desktop Experience)
- Functional Level: Windows Server 2016 (minimo)
- Nome dominio: `corp.labexample.it`
- Nome NetBIOS: `CORP`
- Snapshot di ogni VM prima di iniziare

> **Fonte:** <https://learn.microsoft.com/windows-server/identity/ad-ds/deploy/install-active-directory-domain-services--level-100->

---

## Parte 1 — Documento di progettazione (30 min)

### 1.1 Giustificazione del design single forest / single domain

Prima di toccare la console, redigere un breve documento di progettazione che risponda a queste domande:

| Decisione | Scelta | Motivazione |
|-----------|--------|-------------|
| Numero foreste | 1 | Trust implicito tra tutti i DC, gestione semplificata, nessun requisito di isolamento regolamentare |
| Numero domini | 1 | Sotto 5000 utenti, nessun requisito di policy di password separate per divisione, replica completa accettabile |
| Functional Level | Windows Server 2016+ | Supporto per Privileged Access Management, Kerberos FAST |
| RODC | Sì, a Napoli | Sede con sicurezza fisica ridotta, nessun admin locale qualificato |

### 1.2 Schema di naming

```
Foresta:           corp.labexample.it
Dominio radice:    corp.labexample.it
NetBIOS:           CORP
Siti AD:           Milano-HQ, Roma-Branch, Napoli-Branch
Subnet:            10.10.10.0/24, 10.10.20.0/24, 10.10.30.0/24
```

---

## Parte 2 — Deployment primo Domain Controller (45 min)

### 2.1 Preparare DC-MI (Milano HQ)

Configurare IP statico, hostname e DNS puntato a localhost:

```powershell
# Rinominare il server
Rename-Computer -NewName "DC-MI" -Restart

# Dopo il riavvio, configurare IP statico
New-NetIPAddress -InterfaceAlias "Ethernet" `
    -IPAddress 10.10.10.10 `
    -PrefixLength 24 `
    -DefaultGateway 10.10.10.1

Set-DnsClientServerAddress -InterfaceAlias "Ethernet" `
    -ServerAddresses 127.0.0.1,10.10.20.10
```

### 2.2 Installare il ruolo AD DS

```powershell
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools

# Verificare installazione
Get-WindowsFeature AD-Domain-Services
```

Output atteso:

```
Display Name                                            Name                       Install State
------------                                            ----                       -------------
[X] Active Directory Domain Services                    AD-Domain-Services         Installed
```

### 2.3 Promuovere a primo DC della foresta

```powershell
$SafeModePwd = ConvertTo-SecureString "P@ssw0rd!DSRM#2026" -AsPlainText -Force

Install-ADDSForest `
    -DomainName "corp.labexample.it" `
    -DomainNetbiosName "CORP" `
    -ForestMode "WinThreshold" `
    -DomainMode "WinThreshold" `
    -InstallDns:$true `
    -DatabasePath "C:\Windows\NTDS" `
    -LogPath "C:\Windows\NTDS" `
    -SysvolPath "C:\Windows\SYSVOL" `
    -SafeModeAdministratorPassword $SafeModePwd `
    -NoRebootOnCompletion:$false `
    -Force:$true
```

> **Nota:** `WinThreshold` corrisponde al functional level Windows Server 2016.
> **Fonte:** <https://learn.microsoft.com/powershell/module/addsdeployment/install-addsforest>

Il server si riavvia automaticamente. Dopo il riavvio, verificare:

```powershell
Get-ADForest | Select-Object Name, ForestMode, RootDomain
Get-ADDomain | Select-Object DNSRoot, DomainMode, PDCEmulator
```

---

## Parte 3 — Deploy secondo RWDC e RODC (45 min)

### 3.1 Preparare e promuovere DC-RM (Roma, RWDC)

Su DC-RM, configurare rete e DNS verso DC-MI:

```powershell
Rename-Computer -NewName "DC-RM" -Restart

New-NetIPAddress -InterfaceAlias "Ethernet" `
    -IPAddress 10.10.20.10 `
    -PrefixLength 24 `
    -DefaultGateway 10.10.20.1

Set-DnsClientServerAddress -InterfaceAlias "Ethernet" `
    -ServerAddresses 10.10.10.10

# Verificare risoluzione DNS del dominio
Resolve-DnsName corp.labexample.it
```

Installare AD DS e promuovere come DC aggiuntivo:

```powershell
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools

$DomainCred = Get-Credential  # CORP\Administrator
$SafeModePwd = ConvertTo-SecureString "P@ssw0rd!DSRM#2026" -AsPlainText -Force

Install-ADDSDomainController `
    -DomainName "corp.labexample.it" `
    -Credential $DomainCred `
    -InstallDns:$true `
    -DatabasePath "C:\Windows\NTDS" `
    -LogPath "C:\Windows\NTDS" `
    -SysvolPath "C:\Windows\SYSVOL" `
    -SafeModeAdministratorPassword $SafeModePwd `
    -NoRebootOnCompletion:$false `
    -Force:$true
```

> **Fonte:** <https://learn.microsoft.com/powershell/module/addsdeployment/install-addsdomaincontroller>

### 3.2 Preparare e promuovere DC-NA (Napoli, RODC)

Su DC-NA, configurare rete e DNS verso DC-MI:

```powershell
Rename-Computer -NewName "DC-NA" -Restart

New-NetIPAddress -InterfaceAlias "Ethernet" `
    -IPAddress 10.10.30.10 `
    -PrefixLength 24 `
    -DefaultGateway 10.10.30.1

Set-DnsClientServerAddress -InterfaceAlias "Ethernet" `
    -ServerAddresses 10.10.10.10
```

Installare AD DS e promuovere come RODC:

```powershell
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools

$DomainCred = Get-Credential  # CORP\Administrator
$SafeModePwd = ConvertTo-SecureString "P@ssw0rd!DSRM#2026" -AsPlainText -Force

Install-ADDSDomainController `
    -DomainName "corp.labexample.it" `
    -Credential $DomainCred `
    -ReadOnlyReplica:$true `
    -InstallDns:$true `
    -DatabasePath "C:\Windows\NTDS" `
    -LogPath "C:\Windows\NTDS" `
    -SysvolPath "C:\Windows\SYSVOL" `
    -SafeModeAdministratorPassword $SafeModePwd `
    -NoRebootOnCompletion:$false `
    -Force:$true
```

> Il flag `-ReadOnlyReplica:$true` installa il DC come Read-Only Domain Controller.

### 3.3 Verificare tutti i DC

Da DC-MI, verificare la presenza di tutti i DC:

```powershell
Get-ADDomainController -Filter * | Format-Table Name, Site, IsReadOnly, IPv4Address, OperatingSystem

# Output atteso:
# Name   Site              IsReadOnly IPv4Address  OperatingSystem
# ----   ----              ---------- -----------  ---------------
# DC-MI  Default-First-... False      10.10.10.10  Windows Server 2022 ...
# DC-RM  Default-First-... False      10.10.20.10  Windows Server 2022 ...
# DC-NA  Default-First-... True       10.10.30.10  Windows Server 2022 ...
```

---

## Parte 4 — Siti, subnet e site link (30 min)

### 4.1 Creare i siti AD

```powershell
# Rinominare il sito predefinito
Get-ADReplicationSite -Filter "Name -eq 'Default-First-Site-Name'" |
    Rename-ADObject -NewName "Milano-HQ"

# Creare i siti per le filiali
New-ADReplicationSite -Name "Roma-Branch"
New-ADReplicationSite -Name "Napoli-Branch"

# Verificare
Get-ADReplicationSite -Filter * | Select-Object Name
```

Output atteso:

```
Name
----
Milano-HQ
Roma-Branch
Napoli-Branch
```

### 4.2 Creare le subnet e associarle ai siti

```powershell
New-ADReplicationSubnet -Name "10.10.10.0/24" -Site "Milano-HQ"
New-ADReplicationSubnet -Name "10.10.20.0/24" -Site "Roma-Branch"
New-ADReplicationSubnet -Name "10.10.30.0/24" -Site "Napoli-Branch"

# Verificare
Get-ADReplicationSubnet -Filter * | Format-Table Name, Site
```

### 4.3 Configurare i site link

```powershell
# Rimuovere il site link predefinito (non più necessario)
Get-ADReplicationSiteLink -Filter "Name -eq 'DEFAULTIPSITELINK'" | Remove-ADReplicationSiteLink -Confirm:$false

# Creare site link separati per controllo granulare dei costi e frequenze
# Milano-Roma (bassa latenza, connessione veloce)
New-ADReplicationSiteLink -Name "MI-RM-Link" `
    -SitesIncluded "Milano-HQ","Roma-Branch" `
    -Cost 100 `
    -ReplicationFrequencyInMinutes 15 `
    -InterSiteTransportProtocol IP

# Milano-Napoli (latenza maggiore, RODC)
New-ADReplicationSiteLink -Name "MI-NA-Link" `
    -SitesIncluded "Milano-HQ","Napoli-Branch" `
    -Cost 200 `
    -ReplicationFrequencyInMinutes 30 `
    -InterSiteTransportProtocol IP

# Verificare
Get-ADReplicationSiteLink -Filter * | Format-Table Name, Cost, ReplicationFrequencyInMinutes
```

> **Fonte:** <https://learn.microsoft.com/windows-server/identity/ad-ds/plan/creating-a-site-link-design>

### 4.4 Spostare i DC nei siti corretti

```powershell
Move-ADDirectoryServer -Identity "DC-MI" -Site "Milano-HQ"
Move-ADDirectoryServer -Identity "DC-RM" -Site "Roma-Branch"
Move-ADDirectoryServer -Identity "DC-NA" -Site "Napoli-Branch"

# Verificare
Get-ADDomainController -Filter * | Format-Table Name, Site
```

---

## Parte 5 — Struttura OU con modello tier 0/1/2 (30 min)

### 5.1 Creare la struttura OU

Il modello tier isola gli asset in base al livello di privilegio:

| Tier | Contiene | Rischio |
|------|----------|---------|
| Tier 0 | Domain Controller, account Domain Admin, foresta | Massimo |
| Tier 1 | Server applicativi, account Server Admin | Alto |
| Tier 2 | Workstation, account utente standard | Medio |

```powershell
$DomainDN = (Get-ADDomain).DistinguishedName

# OU radice aziendale
New-ADOrganizationalUnit -Name "CORP" -Path $DomainDN -ProtectedFromAccidentalDeletion $true

$CorpDN = "OU=CORP,$DomainDN"

# --- Tier 0 ---
New-ADOrganizationalUnit -Name "Tier0-Admin" -Path $CorpDN
$Tier0DN = "OU=Tier0-Admin,$CorpDN"

New-ADOrganizationalUnit -Name "Accounts" -Path $Tier0DN
New-ADOrganizationalUnit -Name "Groups" -Path $Tier0DN
New-ADOrganizationalUnit -Name "ServiceAccounts" -Path $Tier0DN

# --- Tier 1 ---
New-ADOrganizationalUnit -Name "Tier1-Servers" -Path $CorpDN
$Tier1DN = "OU=Tier1-Servers,$CorpDN"

New-ADOrganizationalUnit -Name "Accounts" -Path $Tier1DN
New-ADOrganizationalUnit -Name "Groups" -Path $Tier1DN
New-ADOrganizationalUnit -Name "Servers" -Path $Tier1DN
New-ADOrganizationalUnit -Name "ServiceAccounts" -Path $Tier1DN

# --- Tier 2 ---
New-ADOrganizationalUnit -Name "Tier2-Workstations" -Path $CorpDN
$Tier2DN = "OU=Tier2-Workstations,$CorpDN"

New-ADOrganizationalUnit -Name "Accounts" -Path $Tier2DN
New-ADOrganizationalUnit -Name "Groups" -Path $Tier2DN
New-ADOrganizationalUnit -Name "Workstations" -Path $Tier2DN

# --- OU per sede (sotto Tier 2) ---
foreach ($sede in @("Milano","Roma","Napoli")) {
    New-ADOrganizationalUnit -Name $sede -Path "OU=Accounts,$Tier2DN"
    New-ADOrganizationalUnit -Name $sede -Path "OU=Workstations,$Tier2DN"
}
```

### 5.2 Verificare la struttura OU

```powershell
Get-ADOrganizationalUnit -Filter * -SearchBase $CorpDN |
    Select-Object Name, DistinguishedName |
    Sort-Object DistinguishedName |
    Format-Table -AutoSize
```

### 5.3 Delegare il controllo Tier 1 e Tier 2

Esempio: delegare la gestione utenti Tier 2 a un gruppo specifico:

```powershell
# Creare il gruppo di delega
New-ADGroup -Name "T2-UserAdmins" `
    -GroupScope DomainLocal `
    -GroupCategory Security `
    -Path "OU=Groups,$Tier2DN" `
    -Description "Gestione utenti Tier 2"

# Delegare "Reset Password" e "Unlock Account" sulla OU Tier 2 Accounts
$Tier2AccountsDN = "OU=Accounts,$Tier2DN"
$GroupSID = (Get-ADGroup "T2-UserAdmins").SID

# ACL per Reset Password
$acl = Get-Acl "AD:\$Tier2AccountsDN"
$resetPwdGuid = [GUID]"00299570-246d-11d0-a768-00aa006e0529"  # Reset Password
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $GroupSID,
    "ExtendedRight",
    "Allow",
    $resetPwdGuid,
    "Descendents",
    [GUID]"bf967aba-0de6-11d0-a285-00aa003049e2"  # User object
)
$acl.AddAccessRule($ace)
Set-Acl "AD:\$Tier2AccountsDN" $acl
```

> **Fonte:** <https://learn.microsoft.com/windows-server/identity/ad-ds/plan/delegating-administration-by-using-ou-objects>

---

## Parte 6 — Posizionamento e verifica FSMO (20 min)

### 6.1 Verificare il posizionamento attuale dei ruoli FSMO

```powershell
# Metodo 1: netdom
netdom query fsmo

# Metodo 2: PowerShell
Get-ADForest | Select-Object SchemaMaster, DomainNamingMaster
Get-ADDomain | Select-Object PDCEmulator, RIDMaster, InfrastructureMaster
```

Output atteso (tutti su DC-MI dopo l'installazione iniziale):

```
SchemaMaster       : DC-MI.corp.labexample.it
DomainNamingMaster : DC-MI.corp.labexample.it
PDCEmulator        : DC-MI.corp.labexample.it
RIDMaster          : DC-MI.corp.labexample.it
InfrastructureMaster : DC-MI.corp.labexample.it
```

### 6.2 Spostare il ruolo Infrastructure Master su DC-RM

In un dominio single-domain non è critico, ma serve come esercizio:

```powershell
Move-ADDirectoryServerOperationMasterRole `
    -Identity "DC-RM" `
    -OperationMasterRole InfrastructureMaster `
    -Confirm:$false

# Verificare lo spostamento
Get-ADDomain | Select-Object InfrastructureMaster
```

Output atteso:

```
InfrastructureMaster
--------------------
DC-RM.corp.labexample.it
```

### 6.3 Documentare il posizionamento finale

| Ruolo FSMO | DC | Sito |
|------------|----|------|
| Schema Master | DC-MI | Milano-HQ |
| Domain Naming Master | DC-MI | Milano-HQ |
| PDC Emulator | DC-MI | Milano-HQ |
| RID Master | DC-MI | Milano-HQ |
| Infrastructure Master | DC-RM | Roma-Branch |

> **Nota:** i ruoli FSMO non possono risiedere su un RODC (DC-NA).

---

## Parte 7 — Configurazione DNS (30 min)

### 7.1 Verificare le zone DNS integrate in AD

```powershell
# Su DC-MI
Get-DnsServerZone | Format-Table ZoneName, ZoneType, IsDsIntegrated, ReplicationScope

# Output atteso:
# ZoneName                ZoneType IsDsIntegrated ReplicationScope
# --------                -------- -------------- ----------------
# corp.labexample.it      Primary  True           Domain
# _msdcs.corp.labexample.it Primary True          Forest
# 10.10.10.in-addr.arpa   Primary  True           Domain
```

### 7.2 Creare le zone di reverse lookup

```powershell
# Zona reverse per ogni subnet
Add-DnsServerPrimaryZone -NetworkID "10.10.10.0/24" `
    -ReplicationScope "Domain" `
    -DynamicUpdate "Secure"

Add-DnsServerPrimaryZone -NetworkID "10.10.20.0/24" `
    -ReplicationScope "Domain" `
    -DynamicUpdate "Secure"

Add-DnsServerPrimaryZone -NetworkID "10.10.30.0/24" `
    -ReplicationScope "Domain" `
    -DynamicUpdate "Secure"

# Verificare
Get-DnsServerZone | Where-Object { $_.IsReverseLookupZone } | Format-Table ZoneName
```

### 7.3 Configurare i conditional forwarder

Esempio: risolvere un dominio partner esterno:

```powershell
Add-DnsServerConditionalForwarderZone `
    -Name "partner.example.com" `
    -MasterServers 203.0.113.10,203.0.113.11 `
    -ReplicationScope "Forest"

# Configurare il forwarder generale (es. Cloudflare, quad9)
Set-DnsServerForwarder -IPAddress 9.9.9.9,149.112.112.112 -PassThru
```

### 7.4 Configurare aging e scavenging

```powershell
# Abilitare aging sulla zona
Set-DnsServerZoneAging -Name "corp.labexample.it" `
    -Aging $true `
    -NoRefreshInterval 7.00:00:00 `
    -RefreshInterval 7.00:00:00

# Abilitare scavenging sul server DNS (solo su DC-MI)
Set-DnsServerScavenging -ScavengingState $true `
    -ScavengingInterval 7.00:00:00
```

> **Fonte:** <https://learn.microsoft.com/windows-server/networking/dns/dns-top>

---

## Parte 8 — Verifica completa dell'infrastruttura (30 min)

### 8.1 dcdiag

```powershell
# Diagnostica completa su tutti i DC
dcdiag /v /e /c

# Test specifici critici
dcdiag /test:DNS /DnsAll /e
dcdiag /test:Replications /v
dcdiag /test:FSMOCheck
dcdiag /test:KnowsOfRoleHolders
```

Tutti i test devono restituire `passed`. Investigare ogni `failed`.

### 8.2 repadmin

```powershell
# Sommario replica tra tutti i DC
repadmin /replsummary

# Output atteso (nessun errore):
# Source DSA   largest delta  fails/total %% error
# DC-MI              05m:12s    0 /   5    0
# DC-RM              06m:34s    0 /   5    0
# DC-NA              15m:01s    0 /   5    0

# Stato dettagliato della replica
repadmin /showrepl DC-MI
repadmin /showrepl DC-RM

# Forzare una replica immediata
repadmin /syncall /A /d /e /P
```

### 8.3 Test di risoluzione DNS

```powershell
# Risolvere il dominio AD
Resolve-DnsName corp.labexample.it -Type A
Resolve-DnsName _ldap._tcp.corp.labexample.it -Type SRV
Resolve-DnsName _kerberos._tcp.corp.labexample.it -Type SRV

# Verificare i record SRV per ogni sito
Resolve-DnsName _ldap._tcp.Milano-HQ._sites.corp.labexample.it -Type SRV
Resolve-DnsName _ldap._tcp.Roma-Branch._sites.corp.labexample.it -Type SRV
Resolve-DnsName _ldap._tcp.Napoli-Branch._sites.corp.labexample.it -Type SRV

# Reverse lookup
Resolve-DnsName 10.10.10.10 -Type PTR
Resolve-DnsName 10.10.20.10 -Type PTR
```

### 8.4 Verifica Global Catalog

```powershell
# DC-MI e DC-RM devono essere GC, DC-NA (RODC) è GC di default
Get-ADDomainController -Filter * |
    Format-Table Name, IsGlobalCatalog, IsReadOnly, Site

# Verificare la porta GC (3268)
Test-NetConnection DC-MI.corp.labexample.it -Port 3268
Test-NetConnection DC-RM.corp.labexample.it -Port 3268
```

### 8.5 Verifica RODC

```powershell
# Verificare la Password Replication Policy del RODC
Get-ADDomainControllerPasswordReplicationPolicy -Identity "DC-NA" -Allowed
Get-ADDomainControllerPasswordReplicationPolicy -Identity "DC-NA" -Denied

# Verificare che nessuna password sensibile sia in cache
Get-ADDomainControllerPasswordReplicationPolicyUsage -Identity "DC-NA" -RevealedAccounts
```

---

## Checklist finale

- [ ] Foresta `corp.labexample.it` creata con functional level WinThreshold
- [ ] 3 DC operativi: DC-MI (RWDC), DC-RM (RWDC), DC-NA (RODC)
- [ ] 3 siti AD configurati con subnet associate
- [ ] Site link con costi e frequenze differenziati
- [ ] Struttura OU tier 0/1/2 creata con delega
- [ ] Ruoli FSMO documentati e verificati
- [ ] Zone DNS forward e reverse integrate in AD
- [ ] Conditional forwarder configurato
- [ ] Aging/scavenging DNS abilitato
- [ ] `dcdiag /v /e` senza errori
- [ ] `repadmin /replsummary` senza errori
- [ ] Record SRV DNS per ogni sito risolvibili
- [ ] RODC Password Replication Policy verificata

---

## Riferimenti

- <https://learn.microsoft.com/windows-server/identity/ad-ds/plan/ad-ds-design-and-planning>
- <https://learn.microsoft.com/windows-server/identity/ad-ds/deploy/install-active-directory-domain-services--level-100->
- <https://learn.microsoft.com/windows-server/identity/ad-ds/plan/creating-a-site-link-design>
- <https://learn.microsoft.com/windows-server/identity/ad-ds/deploy/rodc/read-only-domain-controller-updates>
- <https://learn.microsoft.com/windows-server/identity/ad-ds/plan/delegating-administration-by-using-ou-objects>
- <https://learn.microsoft.com/windows-server/networking/dns/dns-top>
