# Scenario 01 — Rilevamento Estrazione Credenziali (Mimikatz)

> **Modulo di riferimento:** [05-sicurezza-windows.md](../05-sicurezza-windows.md), [24-windows-defender-endpoint-security.md](../24-windows-defender-endpoint-security.md), [29-windows-server-hardening.md](../29-windows-server-hardening.md)
> **Tempo stimato:** 1.5–2 ore
> **Livello:** advanced
> **Prerequisiti:** Lab AD con DC e workstation domain-joined, Sysmon installato, completamento moduli 01, 05, 21, 24
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

Il SOC riceve un alert ad alta priorità dal SIEM: un processo sospetto su una workstation domain-joined (WKS-FIN-042) ha tentato di accedere alla memoria del processo LSASS. L'utente associato è `CONTOSO\m.rossi`, analista del dipartimento finanziario. L'alert è scattato alle 14:32 UTC.

Il tuo compito come incident responder è:

1. Verificare se c'è stata estrazione di credenziali
2. Determinare l'estensione della compromissione
3. Contenere l'incidente e prevenire movimento laterale
4. Implementare contromisure permanenti

---

## Fase 1 — Triage (30 min)

### 1.1 Verificare gli alert LSASS (Sysmon Event ID 10)

```powershell
# Cercare accessi sospetti alla memoria di LSASS (Sysmon Event ID 10 - ProcessAccess)
# GrantedAccess 0x1010, 0x1410, 0x1438 sono tipici di Mimikatz
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Sysmon/Operational'
    Id = 10
} -MaxEvents 500 | Where-Object {
    $_.Properties[5].Value -match 'lsass\.exe'
} | Select-Object TimeCreated,
    @{N='SourceProcess'; E={$_.Properties[3].Value}},
    @{N='TargetProcess'; E={$_.Properties[5].Value}},
    @{N='GrantedAccess'; E={$_.Properties[7].Value}} |
    Format-Table -AutoSize

# Filtrare per accessi con permessi di lettura memoria tipici di credential dumping
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Sysmon/Operational'
    Id = 10
} -MaxEvents 1000 | Where-Object {
    $_.Properties[5].Value -match 'lsass\.exe' -and
    $_.Properties[7].Value -in @('0x1010','0x1410','0x1438','0x143a')
} | Format-List TimeCreated, Message
```

### 1.2 Verificare process creation sospetti (Event ID 4688)

```powershell
# Controllare creazione processi con command line auditing abilitato
# Event ID 4688 = nuovo processo creato
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4688
} -MaxEvents 2000 | Where-Object {
    $_.Message -match 'mimikatz|sekurlsa|lsadump|kerberos::list|crypto::capi|privilege::debug'
} | Select-Object TimeCreated, @{
    N='CommandLine'; E={($_.Message -split "`n" | Where-Object {$_ -match 'Process Command Line'})}
} | Format-List

# Cercare processi che hanno ottenuto SeDebugPrivilege (necessario per accesso LSASS)
# Event ID 4672 = privilegi speciali assegnati a nuovo logon
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4672
} -MaxEvents 500 | Where-Object {
    $_.Message -match 'SeDebugPrivilege'
} | Select-Object TimeCreated, @{
    N='Account'; E={$_.Properties[1].Value}
} | Format-Table -AutoSize
```

### 1.3 Analizzare PowerShell logging (Event ID 4103, 4104)

```powershell
# Event ID 4104 = Script Block Logging (cattura il codice PowerShell eseguito)
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-PowerShell/Operational'
    Id = 4104
} -MaxEvents 500 | Where-Object {
    $_.Message -match 'Invoke-Mimikatz|DumpCreds|sekurlsa|Get-GPPPassword|Invoke-ReflectivePEInjection|MiniDump'
} | Select-Object TimeCreated, @{
    N='ScriptBlock'; E={$_.Properties[2].Value.Substring(0, [Math]::Min(200, $_.Properties[2].Value.Length))}
} | Format-List

# Event ID 4103 = Module Logging (cattura comandi e output)
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-PowerShell/Operational'
    Id = 4103
} -MaxEvents 500 | Where-Object {
    $_.Message -match 'lsass|credential|ntlm|kerberos|ticket|dcsync'
} | Select-Object TimeCreated | Format-Table -AutoSize

# Cercare download di script remoti (Invoke-Expression + download cradle)
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-PowerShell/Operational'
    Id = 4104
} -MaxEvents 1000 | Where-Object {
    $_.Message -match 'Net\.WebClient|Invoke-WebRequest|DownloadString|IEX\s*\(|iex\s*\('
} | Format-List TimeCreated, Message
```

### 1.4 Verificare logon anomali (Event ID 4624, 4625, 4648)

```powershell
# Event ID 4624 = Logon riuscito — cercare logon type 3 (network) e 10 (RemoteInteractive)
# da host non previsti
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4624
    StartTime = (Get-Date).AddHours(-24)
} -MaxEvents 5000 | Where-Object {
    $logonType = $_.Properties[8].Value
    $logonType -in @(3, 10) -and
    $_.Properties[5].Value -eq 'CONTOSO\m.rossi'
} | Select-Object TimeCreated,
    @{N='LogonType'; E={$_.Properties[8].Value}},
    @{N='SourceIP'; E={$_.Properties[18].Value}},
    @{N='Account'; E={$_.Properties[5].Value}} |
    Format-Table -AutoSize

# Event ID 4648 = Logon con credenziali esplicite (runas, pass-the-hash)
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4648
    StartTime = (Get-Date).AddHours(-24)
} | Select-Object TimeCreated,
    @{N='SubjectUser'; E={$_.Properties[1].Value}},
    @{N='TargetUser'; E={$_.Properties[5].Value}},
    @{N='TargetServer'; E={$_.Properties[8].Value}} |
    Format-Table -AutoSize

# Event ID 4625 = Logon falliti (brute force o spray)
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4625
    StartTime = (Get-Date).AddHours(-24)
} | Group-Object @{E={$_.Properties[5].Value}} |
    Sort-Object Count -Descending | Select-Object Count, Name -First 10
```

### 1.5 Cercare indicatori di DCSync (sul Domain Controller)

```powershell
# Sul DC: cercare Event ID 4662 con DS-Replication-Get-Changes (DCSync attack)
# ObjectType GUID per DS-Replication-Get-Changes-All: 1131f6ad-9c07-11d1-f79f-00c04fc2dcd2
Get-WinEvent -ComputerName DC01 -FilterHashtable @{
    LogName = 'Security'
    Id = 4662
    StartTime = (Get-Date).AddHours(-24)
} | Where-Object {
    $_.Message -match '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2|1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'
} | Select-Object TimeCreated, @{
    N='Account'; E={$_.Properties[1].Value}
} | Format-List
# CRITICO: se l'account non è un DC, è DCSync — compromissione grave
```

### 1.6 Documentare lo stato iniziale

```powershell
# Snapshot forense dell'incidente
$incidentDir = "C:\Incident-$(Get-Date -Format 'yyyyMMdd-HHmm')"
New-Item -ItemType Directory -Path $incidentDir -Force

# Processi attivi
Get-Process | Select-Object Id, ProcessName, Path, StartTime |
    Export-Csv "$incidentDir\processes.csv" -NoTypeInformation

# Connessioni di rete
Get-NetTCPConnection | Where-Object State -eq 'Established' |
    Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess |
    Export-Csv "$incidentDir\connections.csv" -NoTypeInformation

# Utenti loggati
query user 2>$null | Out-File "$incidentDir\logged-users.txt"

# Hash dei binari sospetti trovati (per IoC sharing)
Get-ChildItem C:\Windows\Temp, C:\Users\*\AppData\Local\Temp -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) } |
    Get-FileHash -Algorithm SHA256 -ErrorAction SilentlyContinue |
    Export-Csv "$incidentDir\temp-file-hashes.csv" -NoTypeInformation
```

---

## Fase 2 — Contenimento (30 min)

### 2.1 Isolamento della workstation

```powershell
# Isolare la workstation dalla rete (mantenere accesso locale per forensics)
# Opzione 1: Firewall locale — bloccare tutto tranne RDP da jump host forense
$forensicJumpHost = "10.0.1.50"

# Bloccare tutto il traffico in uscita
New-NetFirewallRule -DisplayName "INCIDENT-BlockAllOut" -Direction Outbound `
    -Action Block -Profile Any -Enabled True

# Permettere solo RDP dal jump host forense
New-NetFirewallRule -DisplayName "INCIDENT-AllowForensicRDP" -Direction Inbound `
    -Action Allow -Protocol TCP -LocalPort 3389 `
    -RemoteAddress $forensicJumpHost -Enabled True

# Opzione 2: Disabilitare interfaccia di rete (più aggressivo)
# Get-NetAdapter | Disable-NetAdapter -Confirm:$false

# Verificare isolamento
Get-NetFirewallRule -DisplayName "INCIDENT-*" | Format-Table DisplayName, Direction, Action, Enabled
```

### 2.2 Disabilitare account compromessi

```powershell
# Disabilitare immediatamente l'account compromesso
Disable-ADAccount -Identity "m.rossi"

# Forzare logoff delle sessioni attive dell'utente su tutti i server
# (richiede PsExec o sessioni remote)
$computers = Get-ADComputer -Filter * -SearchBase "OU=Servers,DC=contoso,DC=local" |
    Select-Object -ExpandProperty Name

foreach ($pc in $computers) {
    Invoke-Command -ComputerName $pc -ScriptBlock {
        $sessions = query user 2>$null | Where-Object { $_ -match 'm\.rossi' }
        if ($sessions) {
            $sessionId = ($sessions -split '\s+')[2]
            logoff $sessionId /server:localhost
        }
    } -ErrorAction SilentlyContinue
}

# Reset password immediato (anche se l'account è disabilitato, per sicurezza)
Set-ADAccountPassword -Identity "m.rossi" -Reset -NewPassword (
    ConvertTo-SecureString "TempP@ss$(Get-Random -Minimum 10000 -Maximum 99999)!" -AsPlainText -Force
)

# Revocare tutti i ticket Kerberos per l'utente (invalidare TGT)
# Reset dell'attributo krbtgt richiede cautela, ma per l'utente:
Set-ADUser -Identity "m.rossi" -Replace @{
    'msDS-UserDontExpirePassword' = $false
}
```

### 2.3 Verificare movimento laterale

```powershell
# Cercare Event ID 4648 (logon con credenziali esplicite) su altri host
# per rilevare pass-the-hash o pass-the-ticket
$allDomainComputers = Get-ADComputer -Filter {OperatingSystem -like "*Windows*"} |
    Select-Object -ExpandProperty Name

$lateralMovement = @()
foreach ($pc in $allDomainComputers) {
    try {
        $events = Get-WinEvent -ComputerName $pc -FilterHashtable @{
            LogName = 'Security'
            Id = 4648
            StartTime = (Get-Date).AddHours(-24)
        } -MaxEvents 100 -ErrorAction Stop | Where-Object {
            $_.Properties[1].Value -match 'm\.rossi|WKS-FIN-042'
        }
        if ($events) {
            $lateralMovement += [PSCustomObject]@{
                Computer = $pc
                EventCount = $events.Count
                FirstSeen = ($events | Sort-Object TimeCreated | Select-Object -First 1).TimeCreated
            }
        }
    } catch { }
}

$lateralMovement | Format-Table -AutoSize
# Se risultati: estendere il contenimento a quei sistemi
```

### 2.4 Invalidare ticket Kerberos (se DCSync confermato)

```powershell
# CRITICO: se DCSync è confermato, l'attaccante potrebbe avere l'hash di krbtgt
# In quel caso: Golden Ticket attack è possibile
# Reset krbtgt password (due volte, con intervallo di 12h per max ticket lifetime)

# ATTENZIONE: questa operazione ha impatto sull'intero dominio
# Eseguire solo dopo approvazione del CISO

# Primo reset
Reset-KrbtgtPassword -DomainController DC01 -Credential (Get-Credential)
# Nota: usare lo script ufficiale Microsoft "Reset-KrbtgtPassword"
# https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/reset-krbtgt-account-password

# Verificare stato replicazione dopo il reset
repadmin /showrepl
```

---

## Fase 3 — Remediation (30 min)

### 3.1 Abilitare Credential Guard

```powershell
# Verificare compatibilità hardware (VBS/HVCI)
# Richiede: UEFI Secure Boot, TPM 2.0, virtualizzazione hardware
Get-ComputerInfo | Select-Object OsName,
    DeviceGuardSmartStatus,
    DeviceGuardSecurityServicesConfigured,
    DeviceGuardSecurityServicesRunning

# Abilitare Credential Guard via GPO (percorso raccomandato)
# Computer Configuration > Administrative Templates > System > Device Guard
# "Turn On Virtualization Based Security" = Enabled
# Credential Guard Configuration = Enabled with UEFI lock

# Abilitare via registry (per test immediato su singola macchina)
# Abilitare VBS
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard" `
    -Name "EnableVirtualizationBasedSecurity" -Value 1 -Type DWord
# Abilitare Credential Guard
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LsaCfgFlags" -Value 1 -Type DWord

# Verificare stato dopo reboot
# (Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard).SecurityServicesRunning
# Valore 1 = Credential Guard attivo
```

### 3.2 Abilitare LSA Protection (RunAsPPL)

```powershell
# LSA Protection impedisce a processi non protetti di accedere a LSASS
# Imposta LSASS come Protected Process Light (PPL)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RunAsPPL" -Value 1 -Type DWord

# Verificare (dopo reboot)
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "RunAsPPL"
# Deve restituire 1

# Verificare con Sysmon che LSASS sia in esecuzione come PPL
Get-Process lsass | Select-Object Id, ProcessName, @{
    N='Protection'; E={(Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine}
}
```

### 3.3 Configurare LAPS (Local Administrator Password Solution)

```powershell
# Installare modulo LAPS (Windows LAPS nativo in Windows 11/Server 2025)
# Per legacy LAPS:
# Install-Module -Name LAPS -Force

# Verificare schema AD per LAPS
Get-ADObject "CN=ms-Mcs-AdmPwd,$(Get-ADRootDSE | Select-Object -ExpandProperty schemaNamingContext)" `
    -ErrorAction SilentlyContinue
# Se non esiste, estendere lo schema:
# Update-LapsADSchema

# Configurare GPO LAPS
# Computer Configuration > Administrative Templates > LAPS
# "Configure password backup directory" = Active Directory
# "Password Settings" = Complexity: Large+Small+Numbers+Specials, Length: 20, Age: 30
```

### 3.4 Aggiungere account sensibili al gruppo Protected Users

```powershell
# Protected Users disabilita: NTLM auth, DES/RC4 Kerberos, delegation,
# cache delle credenziali, TGT renewal oltre 4h
$sensitiveAccounts = @("admin.rete", "svc.backup", "admin.dominio")

foreach ($account in $sensitiveAccounts) {
    Add-ADGroupMember -Identity "Protected Users" -Members $account
    Write-Output "[+] $account aggiunto a Protected Users"
}

# Verificare membership
Get-ADGroupMember -Identity "Protected Users" | Select-Object Name, SamAccountName |
    Format-Table -AutoSize
```

### 3.5 Abilitare ASR rules per protezione LSASS

```powershell
# Attack Surface Reduction rule per LSASS
# GUID: 9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2
# "Block credential stealing from the Windows local security authority subsystem"

# Abilitare in modalità Block
Set-MpPreference -AttackSurfaceReductionRules_Ids "9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2" `
    -AttackSurfaceReductionRules_Actions Enabled

# Verificare stato
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Ids
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Actions

# Abilitare altre ASR rules rilevanti
# Block process creations originating from PSExec and WMI commands
Set-MpPreference -AttackSurfaceReductionRules_Ids "d1e49aac-8f56-4280-b9ba-993a6d77406c" `
    -AttackSurfaceReductionRules_Actions Enabled

# Block executable content from email client and webmail
Set-MpPreference -AttackSurfaceReductionRules_Ids "be9ba2d9-53ea-4cdc-84e5-9b1eeee46550" `
    -AttackSurfaceReductionRules_Actions Enabled
```

### 3.6 Hardening della policy di audit

```powershell
# Abilitare audit avanzato per Credential Access
# (se non già configurato via GPO)
auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable
auditpol /set /subcategory:"Other Logon/Logoff Events" /success:enable /failure:enable
auditpol /set /subcategory:"Special Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable

# Abilitare command line auditing nei processi
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit" `
    -Name "ProcessCreationIncludeCmdLine_Enabled" -Value 1 -Type DWord

# Verificare policy
auditpol /get /category:"Logon/Logoff"
auditpol /get /category:"Account Logon"
```

---

## Fase 4 — Report (20 min)

Redigere un incident report con:

1. **Timeline**: dall'alert iniziale (14:32 UTC) a contenimento completato, con ogni azione timestamped in ISO 8601
2. **Impatto**: account compromessi, sistemi con evidenza di movimento laterale, credenziali potenzialmente esfiltrate
3. **Azioni**: isolamento rete, disabilitazione account, reset password, verifica DCSync
4. **Remediation**: Credential Guard, RunAsPPL, LAPS, Protected Users, ASR rules
5. **IoC**: hash dei binari sospetti, IP di origine, pattern di accesso LSASS

### Mapping MITRE ATT&CK

| Tecnica | ID | Fase |
|---------|-----|------|
| OS Credential Dumping: LSASS Memory | T1003.001 | Credential Access |
| OS Credential Dumping: DCSync | T1003.006 | Credential Access |
| Use Alternate Authentication Material: Pass the Hash | T1550.002 | Lateral Movement |
| Remote Services: Remote Desktop Protocol | T1021.001 | Lateral Movement |
| Abuse Elevation Control Mechanism | T1548 | Privilege Escalation |

### CVSS e contesto

L'estrazione di credenziali da LSASS non è di per sé una CVE singola, ma un'intera classe di attacco. La gravità dipende dal contesto:

- **Con DCSync confermato**: CRITICO (compromissione dell'intero dominio, accesso a krbtgt → Golden Ticket)
- **Senza DCSync, con credenziali admin**: ALTO (movimento laterale, accesso a risorse privilegiate)
- **Solo credenziali utente standard**: MEDIO (accesso limitato, ma potenziale pivot)

---

## Domande di Valutazione

<details>
<summary>1. Perché Credential Guard è efficace contro Mimikatz?</summary>

Credential Guard utilizza Virtualization-Based Security (VBS) per isolare il processo LSA in un ambiente protetto (LSAIso — Isolated LSA). Le credenziali (NTLM hash, Kerberos TGT/session keys) sono gestite dal trustlet LSAIso, che risiede in una VM separata dal kernel del sistema operativo. Anche un attaccante con privilegi SYSTEM non può accedere alla memoria di LSAIso, perché l'hypervisor applica l'isolamento. Mimikatz legge la memoria di LSASS nel kernel, ma con Credential Guard i segreti non sono più in quella memoria.
</details>

<details>
<summary>2. Qual è la differenza tra RunAsPPL e Credential Guard?</summary>

RunAsPPL (Protected Process Light) è un meccanismo del kernel che impedisce a processi non firmati Microsoft di aprire handle a LSASS con permessi di lettura memoria. Blocca l'injection e il memory dump da parte di tool come Mimikatz che usano OpenProcess(). Tuttavia, un driver in kernel mode o un exploit kernel potrebbe bypassare questa protezione. Credential Guard è più robusto: usa l'hypervisor per isolare le credenziali in una VM separata, rendendo l'attacco impossibile anche con accesso kernel. In pratica, si abilitano entrambi: RunAsPPL come prima linea di difesa, Credential Guard come protezione definitiva.
</details>

<details>
<summary>3. Perché il reset di krbtgt deve essere fatto due volte?</summary>

Il ticket Kerberos TGT ha un lifetime massimo (default: 10 ore) e un renewal lifetime (default: 7 giorni). Quando si resetta la password di krbtgt, AD mantiene la password precedente (N-1) come valida per garantire la continuità operativa durante la replicazione. Un Golden Ticket forgiato con la password N-1 resterebbe valido. Il secondo reset (dopo almeno il tempo di replica + max ticket lifetime) invalida anche la password N-1, rendendo inutilizzabile qualsiasi Golden Ticket forgiato con entrambe le versioni. L'intervallo consigliato tra i due reset è almeno 12 ore (max TGT lifetime + margine di replicazione).
</details>

<details>
<summary>4. Come rilevi un attacco DCSync nel log di audit?</summary>

DCSync sfrutta il protocollo MS-DRSR (Directory Replication Service Remote Protocol) per richiedere la replica di oggetti AD, inclusi gli hash delle password. Si rileva con Event ID 4662 nel Security log del DC, filtrando per le proprietà di accesso ai GUID di replica: `1131f6ad-9c07-11d1-f79f-00c04fc2dcd2` (DS-Replication-Get-Changes-All) e `1131f6aa-9c07-11d1-f79f-00c04fc2dcd2` (DS-Replication-Get-Changes). Se l'account che esegue la richiesta non è un Domain Controller, è un attacco DCSync. In un ambiente sano, solo gli account macchina dei DC dovrebbero generare questi eventi.
</details>

---

## Riferimenti

- [05-sicurezza-windows.md](../05-sicurezza-windows.md)
- [24-windows-defender-endpoint-security.md](../24-windows-defender-endpoint-security.md)
- [29-windows-server-hardening.md](../29-windows-server-hardening.md)
- [01-active-directory.md](../01-active-directory.md)
- Microsoft Learn — [Credential Guard Overview](https://learn.microsoft.com/en-us/windows/security/identity-protection/credential-guard/)
- Microsoft Learn — [Configuring LSA Protection](https://learn.microsoft.com/en-us/windows-server/security/credentials-protection-and-management/configuring-additional-lsa-protection)
- Microsoft Learn — [Attack Surface Reduction rules reference](https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference)
- MITRE ATT&CK — [T1003.001 OS Credential Dumping: LSASS Memory](https://attack.mitre.org/techniques/T1003/001/)
- MITRE ATT&CK — [T1003.006 OS Credential Dumping: DCSync](https://attack.mitre.org/techniques/T1003/006/)
