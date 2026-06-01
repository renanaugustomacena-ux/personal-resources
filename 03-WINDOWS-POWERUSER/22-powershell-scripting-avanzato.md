# PowerShell Scripting Avanzato — Guida Approfondita

> **Modulo 22** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Modulo del corso** | Windows per ingegneri di sistema |
| **Prerequisiti** | Padronanza di PowerShell base (→ `02-powershell.md`), familiarità con Active Directory (→ `01-active-directory.md`), conoscenza di base della sicurezza Windows (→ `05-sicurezza-windows.md`) |
| **Obiettivi di apprendimento** | 1) Progettare moduli PowerShell completi con manifest, autoloading e pubblicazione su PSGallery · 2) Padroneggiare PSRemoting (WinRM, SSH backend, JEA) e risolvere il problema del double-hop · 3) Implementare pattern di error handling avanzato con eccezioni tipizzate, ErrorRecord e trap · 4) Ottimizzare le pipeline con ValueFromPipeline, steppable pipelines e runspaces · 5) Sviluppare classi PowerShell e risorse DSC class-based · 6) Scrivere test Pester con code coverage e integrazione CI/CD · 7) Applicare security hardening agli script (signing, AMSI, Constrained Language Mode, WDAC) · 8) Gestire segreti con il modulo SecretManagement e integrare Azure KeyVault |
| **Tempo stimato** | 22–30 ore (studio + esercizi + laboratorio) |
| **Livello** | Proficient (avanzato) |
| **Ultimo aggiornamento** | 2026-05-23 |
| **Versioni di riferimento** | PowerShell 7.5.x, Windows PowerShell 5.1, Pester 5.6.x, PSScriptAnalyzer 1.23.x, SecretManagement 1.1.x, .NET 9.0 |

## Idee guida
1. **PSRemoting over SSH (PS 7+).** Modern, no WinRM.
2. **JEA (Just Enough Administration) + SSH backend.**
3. **WinRM fallback per legacy.**
4. **Try/Catch/Finally + ErrorAction.**
5. **DSC (Desired State Configuration) declarative.**

### Mappa Concettuale

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                   POWERSHELL SCRIPTING AVANZATO                             │
├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
│  STRUTTURE DATI  │  REMOTING & IPC  │  ROBUSTEZZA      │  TOOLCHAIN         │
│                  │                  │                  │                    │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌──────────────┐ │ ┌────────────────┐ │
│ │PSCustomObject│ │ │ WinRM / SSH  │ │ │ Try/Catch/   │ │ │ Pester 5       │ │
│ │Hashtable ord.│ │ │ PSRemoting   │ │ │ Finally      │ │ │ Test & Cover.  │ │
│ └──────────────┘ │ ├──────────────┤ │ ├──────────────┤ │ ├────────────────┤ │
│ ┌──────────────┐ │ │ JEA          │ │ │ ErrorRecord  │ │ │PSScriptAnalyzer│ │
│ │ Classi PS    │ │ │ Constrained  │ │ │ $ErrorAction │ │ │ Linting        │ │
│ │ Enum, Tipi   │ │ │ Endpoints    │ │ │ Preference   │ │ ├────────────────┤ │
│ └──────────────┘ │ ├──────────────┤ │ ├──────────────┤ │ │ platyPS        │ │
│ ┌──────────────┐ │ │ Double-Hop   │ │ │ Exec Policy  │ │ │ Documentazione │ │
│ │ Pipeline     │ │ │ CredSSP vs   │ │ │ Script Sign  │ │ ├────────────────┤ │
│ │ Optimization │ │ │ Kerberos Del.│ │ │ AMSI / CLM   │ │ │SecretManagemt. │ │
│ └──────────────┘ │ └──────────────┘ │ └──────────────┘ │ └────────────────┘ │
├──────────────────┴──────────────────┴──────────────────┴────────────────────┤
│  MODULI: Manifest (.psd1) │ PSGallery │ Nested │ Autoloading               │
├─────────────────────────────────────────────────────────────────────────────┤
│  DSC: Configuration │ Resources │ LCM │ Push/Pull │ Class-based Resources   │
├─────────────────────────────────────────────────────────────────────────────┤
│  PERFORMANCE: Measure-Command │ Runspaces │ ForEach -Parallel │ .NET call  │
├─────────────────────────────────────────────────────────────────────────────┤
│  PS 7.x: Cross-Platform │ .NET Core │ Compat Module │ Ternary │ Pipeline ∥ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Indice
- [Panoramica](#panoramica)
- [PSCustomObject e Hashtable Avanzate](#pscustomobject-e-hashtable-avanzate)
- [Splatting dei Parametri](#splatting-dei-parametri)
- [Regular Expressions in PowerShell](#regular-expressions-in-powershell)
- [Lavorare con JSON, XML e CSV](#lavorare-con-json-xml-e-csv)
- [Chiamate REST API con Invoke-RestMethod](#chiamate-rest-api-con-invoke-restmethod)
- [Esecuzione Parallela e Concorrenza](#esecuzione-parallela-e-concorrenza)
- [PSJobs e Runspaces](#psjobs-e-runspaces)
- [Creazione di Moduli PowerShell](#creazione-di-moduli-powershell)
- [Testing con Pester](#testing-con-pester)
- [PSScriptAnalyzer e Qualità del Codice](#psscriptanalyzer-e-qualità-del-codice)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Pattern Avanzati di Error Handling](#pattern-avanzati-di-error-handling)
- [PSRemoting — Deep Dive](#psremoting--deep-dive)
- [Pipeline Optimization](#pipeline-optimization)
- [Sviluppo Class-Based](#sviluppo-class-based)
- [DSC — Desired State Configuration](#dsc--desired-state-configuration)
- [Sicurezza negli Script](#sicurezza-negli-script)
- [Secret Management](#secret-management)
- [PowerShell 7.x vs Windows PowerShell](#powershell-7x-vs-windows-powershell)
- [Logging e Debugging Avanzato](#logging-e-debugging-avanzato)
- [Script Packaging e Distribuzione](#script-packaging-e-distribuzione)
- [Riferimenti](#riferimenti)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie Consigliate](#letture-primarie-consigliate)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)

---

## Panoramica

PowerShell è molto più di un semplice sostituto del Command Prompt: è un linguaggio di scripting completo, costruito sul framework .NET, che permette di automatizzare praticamente qualsiasi aspetto dell'amministrazione di sistemi Windows, Azure, Microsoft 365 e infrastrutture ibride. Mentre le basi di PowerShell — cmdlet, pipeline, variabili — sono accessibili anche ai principianti, le funzionalità avanzate trasformano PowerShell in uno strumento di ingegneria del software a tutti gli effetti.

Questa guida esplora le tecniche avanzate che distinguono uno script PowerShell scritto in modo professionale da uno script amatoriale: dall'uso corretto di PSCustomObject per la strutturazione dei dati, passando per le regular expressions per l'elaborazione del testo, fino all'esecuzione parallela per prestazioni ottimali, alla creazione di moduli riutilizzabili e al testing automatizzato con Pester.

L'obiettivo non è solo insegnare la sintassi, ma trasmettere i principi di ingegneria del software applicati a PowerShell: codice testabile, manutenibile, performante e conforme alle best practices della community. Ogni sezione include esempi pratici tratti da scenari reali di amministrazione di sistema e DevOps.

---

## PSCustomObject e Hashtable Avanzate

### Hashtable: Fondamenta

Le hashtable in PowerShell sono collezioni di coppie chiave-valore, fondamentali per la strutturazione dei dati. La sintassi base è semplice, ma le hashtable hanno capacità avanzate spesso sottoutilizzate.

```powershell
# Hashtable base
$server = @{
    Name     = "SRV-DC01"
    IP       = "10.0.1.10"
    Role     = "Domain Controller"
    OS       = "Windows Server 2022"
    RAM_GB   = 16
}

# Accesso ai valori
$server.Name                    # Dot notation
$server["Name"]                 # Bracket notation (utile con chiavi dinamiche)
$key = "IP"; $server[$key]      # Chiave da variabile

# Hashtable ordinate (mantengono l'ordine di inserimento)
$orderedServer = [ordered]@{
    Name = "SRV-DC01"
    IP   = "10.0.1.10"
    Role = "Domain Controller"
}

# Iterare su una hashtable
$server.GetEnumerator() | ForEach-Object {
    Write-Output "$($_.Key): $($_.Value)"
}

# Hashtable annidate
$infrastructure = @{
    DC = @{
        Primary   = @{ Name = "DC01"; IP = "10.0.1.10" }
        Secondary = @{ Name = "DC02"; IP = "10.0.1.11" }
    }
    FileServer = @{
        Name = "FS01"
        Shares = @("Finance$", "HR$", "IT$")
    }
}

# Accesso annidato
$infrastructure.DC.Primary.IP    # "10.0.1.10"
$infrastructure.FileServer.Shares[0]  # "Finance$"
```

### PSCustomObject: Oggetti Strutturati

PSCustomObject è il modo raccomandato per creare oggetti personalizzati in PowerShell. A differenza delle hashtable, i PSCustomObject mantengono l'ordine delle proprietà, sono più performanti nella pipeline e si integrano nativamente con `Format-Table`, `Export-Csv` e `ConvertTo-Json`.

```powershell
# Creare un PSCustomObject (sintassi raccomandata)
$server = [PSCustomObject]@{
    Name       = "SRV-DC01"
    IP         = "10.0.1.10"
    Role       = "Domain Controller"
    OS         = "Windows Server 2022"
    RAM_GB     = 16
    LastReboot = (Get-Date).AddDays(-15)
}

# Aggiungere proprietà dinamicamente
$server | Add-Member -MemberType NoteProperty -Name "Location" -Value "Datacenter Roma"

# Aggiungere metodi
$server | Add-Member -MemberType ScriptMethod -Name "GetUptime" -Value {
    (New-TimeSpan -Start $this.LastReboot -End (Get-Date)).Days
}
$server.GetUptime()  # Restituisce il numero di giorni dall'ultimo reboot

# Creare una collezione di oggetti (pattern comune per report)
$report = Get-ADComputer -Filter * -Properties OperatingSystem, LastLogonDate |
    ForEach-Object {
        [PSCustomObject]@{
            ComputerName   = $_.Name
            OS             = $_.OperatingSystem
            LastLogon      = $_.LastLogonDate
            DaysSinceLogon = if ($_.LastLogonDate) {
                (New-TimeSpan -Start $_.LastLogonDate -End (Get-Date)).Days
            } else { "Mai" }
            Stale          = if ($_.LastLogonDate) {
                (New-TimeSpan -Start $_.LastLogonDate -End (Get-Date)).Days -gt 90
            } else { $true }
        }
    }

$report | Where-Object Stale -eq $true | Export-Csv "C:\Reports\StaleComputers.csv" -NoTypeInformation
```

### Typed Properties con Classi PowerShell

Da PowerShell 5.0, è possibile definire classi con proprietà tipizzate:

```powershell
class ServerInfo {
    [string]$Name
    [string]$IPAddress
    [string]$Role
    [int]$RAM_GB
    [datetime]$LastReboot
    [bool]$IsOnline

    ServerInfo([string]$name, [string]$ip) {
        $this.Name = $name
        $this.IPAddress = $ip
        $this.IsOnline = Test-Connection -ComputerName $ip -Count 1 -Quiet
        $this.LastReboot = [datetime]::MinValue
    }

    [int] GetUptimeDays() {
        if ($this.LastReboot -eq [datetime]::MinValue) { return -1 }
        return (New-TimeSpan -Start $this.LastReboot -End (Get-Date)).Days
    }

    [string] ToString() {
        return "$($this.Name) [$($this.IPAddress)] - Online: $($this.IsOnline)"
    }
}

$srv = [ServerInfo]::new("DC01", "10.0.1.10")
$srv.Role = "Domain Controller"
$srv.RAM_GB = 16
$srv.GetUptimeDays()
```

---

## Splatting dei Parametri

Lo **splatting** è una tecnica che migliora drasticamente la leggibilità degli script quando si invocano cmdlet con molti parametri. Invece di una singola riga lunghissima, i parametri vengono definiti in una hashtable e passati al cmdlet usando l'operatore `@` al posto di `$`.

```powershell
# SENZA splatting (difficile da leggere e mantenere)
Send-MailMessage -From "admin@contoso.com" -To "team@contoso.com" -Subject "Report Giornaliero" -Body "In allegato il report." -SmtpServer "smtp.contoso.com" -Port 587 -UseSsl -Credential $cred -Attachments "C:\Reports\daily.csv"

# CON splatting (chiaro e manutenibile)
$mailParams = @{
    From        = "admin@contoso.com"
    To          = "team@contoso.com"
    Subject     = "Report Giornaliero"
    Body        = "In allegato il report."
    SmtpServer  = "smtp.contoso.com"
    Port        = 587
    UseSsl      = $true
    Credential  = $cred
    Attachments = "C:\Reports\daily.csv"
}
Send-MailMessage @mailParams

# Splatting condizionale — aggiungere parametri dinamicamente
$copyParams = @{
    Path        = "C:\Source\*"
    Destination = "D:\Backup\"
    Recurse     = $true
}

if ($includeHidden) {
    $copyParams.Add("Force", $true)
}

if ($logFile) {
    $copyParams.Add("Verbose", $true)
}

Copy-Item @copyParams

# Splatting con parametri posizionali (usando array invece di hashtable)
$testArgs = @("10.0.1.10", 4, 64, 2)
Test-Connection @testArgs
# Equivale a: Test-Connection -ComputerName "10.0.1.10" -Count 4 -BufferSize 64 -MaxHops 2
```

Un uso avanzato dello splatting è il **parameter forwarding**, dove una funzione wrapper passa tutti i parametri ricevuti a un'altra funzione:

```powershell
function Invoke-SafeRestart {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$ComputerName,
        [switch]$Force,
        [int]$Delay = 30
    )

    # Costruire splatting dinamico basato su $PSBoundParameters
    $restartParams = @{}
    if ($PSBoundParameters.ContainsKey('Force')) { $restartParams.Force = $true }
    if ($PSBoundParameters.ContainsKey('Delay')) { $restartParams.Delay = $Delay }

    foreach ($computer in $ComputerName) {
        if (Test-Connection -ComputerName $computer -Count 1 -Quiet) {
            Restart-Computer -ComputerName $computer @restartParams
            Write-Output "Restart avviato per $computer"
        } else {
            Write-Warning "$computer non raggiungibile — skip"
        }
    }
}
```

---

## Regular Expressions in PowerShell

PowerShell integra il motore regex di .NET, uno dei più potenti disponibili. Le regex sono utilizzabili con gli operatori `-match`, `-replace`, `-split` e con la classe `[regex]`.

### Operatori Base

```powershell
# -match: restituisce $true/$false e popola $Matches
"Server-DC01-Roma" -match "Server-(\w+)-(\w+)"
$Matches[0]  # "Server-DC01-Roma" (match completo)
$Matches[1]  # "DC01" (primo gruppo di cattura)
$Matches[2]  # "Roma" (secondo gruppo di cattura)

# Named captures (gruppi con nome)
"2026-04-12 15:30:00" -match "(?<anno>\d{4})-(?<mese>\d{2})-(?<giorno>\d{2})"
$Matches.anno    # "2026"
$Matches.mese    # "04"
$Matches.giorno  # "12"

# -replace: sostituzione con regex
"mario.rossi@contoso.com" -replace "^(.+)@(.+)$", 'Utente: $1, Dominio: $2'
# Output: "Utente: mario.rossi, Dominio: contoso.com"

# -replace con scriptblock (PowerShell 7+)
"file_2026_04_12.log" -replace '\d{4}_(\d{2})_(\d{2})', {
    $month = [int]$_.Groups[1].Value
    $day = [int]$_.Groups[2].Value
    "$day/$month"
}

# -split con regex
"one;;two;;;three" -split ";+"
# Output: "one", "two", "three" (split su uno o più punti e virgola)
```

### Pattern Comuni per Amministrazione

```powershell
# Validazione indirizzo IP
$ipPattern = "^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
"192.168.1.256" -match $ipPattern  # $false (256 non è valido)
"10.0.1.10" -match $ipPattern      # $true

# Parsing di log file
$logLine = '2026-04-12 15:30:45 ERROR [AuthService] Failed login for user "admin" from 10.0.5.33'
$logPattern = "^(?<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?<level>\w+) \[(?<source>\w+)\] (?<message>.+)$"

if ($logLine -match $logPattern) {
    [PSCustomObject]@{
        Timestamp = [datetime]$Matches.timestamp
        Level     = $Matches.level
        Source    = $Matches.source
        Message   = $Matches.message
    }
}

# Estrarre tutti gli indirizzi email da un testo
$text = "Contattare mario.rossi@contoso.com oppure support@help.contoso.com per info"
$emailPattern = "[\w.+-]+@[\w.-]+\.\w{2,}"
[regex]::Matches($text, $emailPattern) | ForEach-Object { $_.Value }

# Parsing di output di comandi nativi
$netstatOutput = netstat -an | Where-Object { $_ -match "ESTABLISHED" }
$connectionPattern = "\s+(?<proto>\w+)\s+(?<local>[\d.]+):(?<lport>\d+)\s+(?<remote>[\d.]+):(?<rport>\d+)\s+(?<state>\w+)"

$connections = $netstatOutput | ForEach-Object {
    if ($_ -match $connectionPattern) {
        [PSCustomObject]@{
            Protocol   = $Matches.proto
            LocalAddr  = $Matches.local
            LocalPort  = [int]$Matches.lport
            RemoteAddr = $Matches.remote
            RemotePort = [int]$Matches.rport
            State      = $Matches.state
        }
    }
}

$connections | Group-Object RemoteAddr | Sort-Object Count -Descending | Select-Object -First 10
```

### Regex Avanzate con [regex]

```powershell
# Lookahead e Lookbehind
# Trovare numeri seguiti da "GB" ma senza catturare "GB"
"RAM: 16GB, Disco: 512GB, Cache: 4MB" -match "\d+(?=GB)"
# $Matches[0] = "16" (solo il primo match con -match)

# Per tutti i match usare [regex]::Matches
[regex]::Matches("RAM: 16GB, Disco: 512GB", "\d+(?=GB)") | ForEach-Object { $_.Value }
# "16", "512"

# Lookbehind negativo: trovare numeri NON preceduti da "Cache: "
[regex]::Matches("RAM: 16GB, Cache: 4MB, Disco: 512GB", "(?<!Cache:\s)\d+(?=GB)") |
    ForEach-Object { $_.Value }
# "16", "512" (esclude 4 perché è preceduto da "Cache: " ma non termina con GB comunque)

# Replace con evaluator
$template = "Il server {SERVER} nel datacenter {DC} ha IP {IP}"
$values = @{
    SERVER = "DC01"
    DC     = "Roma"
    IP     = "10.0.1.10"
}

$result = [regex]::Replace($template, "\{(\w+)\}", {
    param($match)
    $key = $match.Groups[1].Value
    if ($values.ContainsKey($key)) { $values[$key] } else { $match.Value }
})
# "Il server DC01 nel datacenter Roma ha IP 10.0.1.10"
```

---

## Lavorare con JSON, XML e CSV

### JSON

```powershell
# Convertire oggetti PowerShell in JSON
$servers = @(
    [PSCustomObject]@{ Name = "DC01"; IP = "10.0.1.10"; Role = "DC" }
    [PSCustomObject]@{ Name = "FS01"; IP = "10.0.1.20"; Role = "FileServer" }
)
$json = $servers | ConvertTo-Json -Depth 3
$json | Out-File "C:\Config\servers.json" -Encoding UTF8

# Leggere JSON da file
$serversFromJson = Get-Content "C:\Config\servers.json" -Raw | ConvertFrom-Json

# Lavorare con JSON annidato
$complexJson = @"
{
    "environment": "production",
    "servers": [
        {
            "name": "DC01",
            "network": {
                "ip": "10.0.1.10",
                "subnet": "255.255.255.0",
                "gateway": "10.0.1.1"
            },
            "roles": ["AD DS", "DNS", "DHCP"]
        }
    ]
}
"@

$config = $complexJson | ConvertFrom-Json
$config.servers[0].network.ip        # "10.0.1.10"
$config.servers[0].roles             # Array: "AD DS", "DNS", "DHCP"

# Modificare e risalvare
$config.servers[0].network.ip = "10.0.1.11"
$config | ConvertTo-Json -Depth 5 | Set-Content "C:\Config\updated.json" -Encoding UTF8

# ATTENZIONE al Depth! Il default è 2, insufficiente per strutture profonde
# Sempre specificare -Depth esplicitamente
```

### XML

```powershell
# Caricare un file XML
[xml]$xmlDoc = Get-Content "C:\Config\web.config"

# Navigare la struttura XML con dot notation
$xmlDoc.configuration.appSettings.add | ForEach-Object {
    Write-Output "$($_.key) = $($_.value)"
}

# Modificare un valore
$node = $xmlDoc.configuration.appSettings.add | Where-Object { $_.key -eq "ConnectionString" }
$node.value = "Server=NEWSRV;Database=AppDB;Integrated Security=true"
$xmlDoc.Save("C:\Config\web.config")

# Creare XML da zero
$xml = New-Object System.Xml.XmlDocument
$declaration = $xml.CreateXmlDeclaration("1.0", "UTF-8", $null)
$xml.AppendChild($declaration) | Out-Null

$root = $xml.CreateElement("Servers")
$xml.AppendChild($root) | Out-Null

$server = $xml.CreateElement("Server")
$server.SetAttribute("Name", "DC01")
$server.SetAttribute("IP", "10.0.1.10")
$root.AppendChild($server) | Out-Null

$xml.Save("C:\Config\servers.xml")

# XPath per query complesse
$xmlDoc.SelectNodes("//add[@key='ConnectionString']")
$xmlDoc.SelectSingleNode("//system.web/compilation/@debug")
```

### CSV

```powershell
# Esportare in CSV
$data = Get-Process | Select-Object Name, Id, CPU, WorkingSet64
$data | Export-Csv "C:\Reports\processes.csv" -NoTypeInformation -Encoding UTF8

# Importare da CSV
$imported = Import-Csv "C:\Reports\processes.csv"
# ATTENZIONE: tutti i valori importati da CSV sono stringhe!
$imported[0].Id.GetType()  # String, non Int

# Convertire i tipi dopo l'importazione
$typedData = Import-Csv "C:\Reports\processes.csv" | ForEach-Object {
    [PSCustomObject]@{
        Name        = $_.Name
        Id          = [int]$_.Id
        CPU         = [double]$_.CPU
        WorkingSet  = [long]$_.WorkingSet64
    }
}

# CSV con delimitatore personalizzato
Import-Csv "C:\Data\export.csv" -Delimiter ";" -Encoding UTF8

# Generare CSV senza file intermedio
$result = Get-ADUser -Filter * -Properties Department, Title |
    Select-Object Name, SamAccountName, Department, Title |
    ConvertTo-Csv -NoTypeInformation
```

---

## Chiamate REST API con Invoke-RestMethod

```powershell
# GET semplice
$response = Invoke-RestMethod -Uri "https://api.github.com/repos/PowerShell/PowerShell/releases/latest"
$response.tag_name   # Versione più recente
$response.assets | Select-Object name, download_count, size

# GET con autenticazione Bearer token
$headers = @{
    Authorization = "Bearer $env:API_TOKEN"
    Accept        = "application/json"
}
$data = Invoke-RestMethod -Uri "https://api.example.com/v1/servers" -Headers $headers

# POST con body JSON
$body = @{
    title = "Nuovo Ticket"
    description = "Server DC01 non raggiungibile"
    priority = "high"
    assignee = "admin@contoso.com"
} | ConvertTo-Json

$newTicket = Invoke-RestMethod -Uri "https://api.example.com/v1/tickets" `
    -Method POST `
    -Headers $headers `
    -Body $body `
    -ContentType "application/json"

# Paginazione automatica
function Get-AllPages {
    [CmdletBinding()]
    param(
        [string]$BaseUri,
        [hashtable]$Headers,
        [int]$PageSize = 100
    )

    $allResults = @()
    $page = 1

    do {
        $uri = "$BaseUri`?page=$page&per_page=$PageSize"
        $response = Invoke-RestMethod -Uri $uri -Headers $Headers
        $allResults += $response
        $page++
    } while ($response.Count -eq $PageSize)

    return $allResults
}

# Gestione errori con Invoke-RestMethod
try {
    $result = Invoke-RestMethod -Uri "https://api.example.com/v1/resource/999" `
        -Headers $headers `
        -ErrorAction Stop
} catch {
    $statusCode = $_.Exception.Response.StatusCode.Value__
    $errorBody = $_.ErrorDetails.Message | ConvertFrom-Json

    switch ($statusCode) {
        404 { Write-Warning "Risorsa non trovata" }
        401 { Write-Error "Token non valido o scaduto" }
        429 {
            $retryAfter = $_.Exception.Response.Headers["Retry-After"]
            Write-Warning "Rate limit raggiunto. Riprovare dopo $retryAfter secondi"
            Start-Sleep -Seconds ([int]$retryAfter + 1)
        }
        default { Write-Error "Errore API: $statusCode - $($errorBody.message)" }
    }
}

# Upload file multipart
$form = @{
    file = Get-Item "C:\Reports\daily.csv"
    description = "Report giornaliero"
}
Invoke-RestMethod -Uri "https://api.example.com/v1/upload" `
    -Method POST `
    -Headers $headers `
    -Form $form
```

---

## Esecuzione Parallela e Concorrenza

### ForEach-Object -Parallel (PowerShell 7+)

```powershell
# Esecuzione parallela base
$servers = @("SRV01", "SRV02", "SRV03", "SRV04", "SRV05", "SRV06", "SRV07", "SRV08")

$results = $servers | ForEach-Object -Parallel {
    $computerName = $_
    $pingResult = Test-Connection -ComputerName $computerName -Count 2 -Quiet
    $uptime = if ($pingResult) {
        try {
            $os = Get-CimInstance Win32_OperatingSystem -ComputerName $computerName -ErrorAction Stop
            (New-TimeSpan -Start $os.LastBootUpTime -End (Get-Date)).Days
        } catch { "Errore" }
    } else { "Offline" }

    [PSCustomObject]@{
        Server = $computerName
        Online = $pingResult
        UptimeDays = $uptime
    }
} -ThrottleLimit 4  # Massimo 4 thread paralleli

# ATTENZIONE: le variabili esterne richiedono $using:
$credential = Get-Credential
$logPath = "C:\Logs"

$servers | ForEach-Object -Parallel {
    $cred = $using:credential
    $log = $using:logPath

    $session = New-PSSession -ComputerName $_ -Credential $cred
    $result = Invoke-Command -Session $session -ScriptBlock {
        Get-Service | Where-Object Status -eq 'Stopped'
    }
    $result | Export-Csv "$log\$_.csv" -NoTypeInformation
    Remove-PSSession $session
} -ThrottleLimit 5

# Thread-safe collection per aggregare risultati
$threadSafeList = [System.Collections.Concurrent.ConcurrentBag[PSCustomObject]]::new()

1..100 | ForEach-Object -Parallel {
    $bag = $using:threadSafeList
    $result = [PSCustomObject]@{
        Number = $_
        Square = $_ * $_
        Thread = [System.Threading.Thread]::CurrentThread.ManagedThreadId
    }
    $bag.Add($result)
} -ThrottleLimit 10

$threadSafeList | Sort-Object Number
```

### Confronto Prestazioni

```powershell
# Sequenziale vs Parallelo — benchmark
$servers = 1..20 | ForEach-Object { "10.0.1.$_" }

# Sequenziale
$sequential = Measure-Command {
    $servers | ForEach-Object {
        Test-Connection -ComputerName $_ -Count 1 -Quiet -ErrorAction SilentlyContinue
    }
}

# Parallelo
$parallel = Measure-Command {
    $servers | ForEach-Object -Parallel {
        Test-Connection -ComputerName $_ -Count 1 -Quiet -ErrorAction SilentlyContinue
    } -ThrottleLimit 10
}

Write-Output "Sequenziale: $($sequential.TotalSeconds)s | Parallelo: $($parallel.TotalSeconds)s"
```

---

## PSJobs e Runspaces

### Background Jobs (PSJobs)

```powershell
# Avviare un job in background
$job = Start-Job -Name "BackupLogs" -ScriptBlock {
    param($source, $dest)
    Copy-Item -Path $source -Destination $dest -Recurse -Force
    Get-ChildItem $dest -Recurse | Measure-Object -Property Length -Sum
} -ArgumentList "C:\Logs\*", "D:\Backup\Logs"

# Monitorare lo stato del job
Get-Job -Name "BackupLogs" | Select-Object Name, State, HasMoreData

# Attendere il completamento e recuperare i risultati
$result = $job | Wait-Job | Receive-Job
$result.Sum / 1MB  # Dimensione totale in MB

# Rimuovere i job completati
Get-Job | Where-Object State -eq "Completed" | Remove-Job

# Job multipli con monitoraggio
$jobs = @()
$servers = @("SRV01", "SRV02", "SRV03")

foreach ($server in $servers) {
    $jobs += Start-Job -Name "Audit-$server" -ScriptBlock {
        param($comp)
        Invoke-Command -ComputerName $comp -ScriptBlock {
            @{
                Hostname  = $env:COMPUTERNAME
                Services  = (Get-Service | Where-Object Status -eq "Running").Count
                Processes = (Get-Process).Count
                FreeGB    = [math]::Round((Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / 1GB, 2)
            }
        }
    } -ArgumentList $server
}

# Attendere tutti i job e raccogliere risultati
$jobs | Wait-Job | ForEach-Object {
    $data = Receive-Job $_
    [PSCustomObject]$data
} | Format-Table -AutoSize
```

### Runspaces (Prestazioni Superiori)

I Runspaces sono più performanti dei PSJobs perché evitano l'overhead della serializzazione/deserializzazione tra processi. Sono eseguiti come thread nello stesso processo PowerShell.

```powershell
# Runspace Pool per esecuzione massivamente parallela
$runspacePool = [runspacefactory]::CreateRunspacePool(1, 10)  # Min 1, Max 10 thread
$runspacePool.Open()

$tasks = @()
$servers = 1..50 | ForEach-Object { "10.0.1.$_" }

foreach ($server in $servers) {
    $powershell = [powershell]::Create()
    $powershell.RunspacePool = $runspacePool

    [void]$powershell.AddScript({
        param($target)
        $result = Test-Connection -ComputerName $target -Count 1 -Quiet -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            Server = $target
            Online = $result
            CheckTime = Get-Date
        }
    }).AddArgument($server)

    $tasks += [PSCustomObject]@{
        PowerShell = $powershell
        Handle     = $powershell.BeginInvoke()
    }
}

# Raccogliere risultati
$results = $tasks | ForEach-Object {
    $_.PowerShell.EndInvoke($_.Handle)
    $_.PowerShell.Dispose()
}

$runspacePool.Close()
$runspacePool.Dispose()

$results | Where-Object Online -eq $true | Format-Table
```

### Confronto Metodi di Parallelismo

```powershell
# Riepilogo dei metodi disponibili in PowerShell per esecuzione parallela,
# con indicazione di quando usare ciascuno.

# Metodo            │ PS5.1 │ PS7+ │ Overhead │ Caso d'uso ideale
# ──────────────────┼───────┼──────┼──────────┼──────────────────────────
# Start-Job         │ Si    │ Si   │ Alto     │ Task lunghi, isolamento
# ForEach -Parallel │ No    │ Si   │ Medio    │ Iterazione parallela, semplice
# Runspace Pool     │ Si    │ Si   │ Basso    │ Alta performance, controllo fine
# Start-ThreadJob   │ No    │ Si   │ Basso    │ Come Job ma in-process (leggero)
# Invoke-Command    │ Si    │ Si   │ Rete     │ Remoto multi-server

# Start-ThreadJob (PS7+): leggero come un runspace, API come un job
$tjob = Start-ThreadJob -ScriptBlock {
    1..1000000 | Where-Object { $_ % 7 -eq 0 } | Measure-Object
}
$tjob | Wait-Job | Receive-Job

# Regola pratica:
# - < 10 task I/O-bound → ForEach-Object -Parallel
# - > 10 task CPU-bound → Runspace Pool
# - Task remoti multi-server → Invoke-Command -ComputerName $list
# - Isolamento necessario → Start-Job (processo separato)
# - PS5.1 senza moduli extra → Runspace Pool (unica opzione performante)

# Errore comune: usare Start-Job per centinaia di task piccoli
# Ogni job crea un PROCESSO separato → overhead enorme
# Soluzione: Runspace Pool o ForEach-Object -Parallel con ThrottleLimit
```

---

## Creazione di Moduli PowerShell

### Struttura di un Modulo

```
MyModule\
├── MyModule.psd1          # Module manifest
├── MyModule.psm1          # Module script (root module)
├── Public\                # Funzioni esportate
│   ├── Get-ServerStatus.ps1
│   ├── Set-ServerConfig.ps1
│   └── Invoke-ServerAudit.ps1
├── Private\               # Funzioni interne (non esportate)
│   ├── Connect-Database.ps1
│   └── Write-AuditLog.ps1
├── Tests\                 # Test Pester
│   ├── Get-ServerStatus.Tests.ps1
│   └── Module.Tests.ps1
├── en-US\                 # Help files
│   └── MyModule-help.xml
└── README.md
```

### Module Manifest (.psd1)

```powershell
# Generare il manifest
New-ModuleManifest -Path "C:\Modules\ServerTools\ServerTools.psd1" `
    -RootModule "ServerTools.psm1" `
    -ModuleVersion "1.0.0" `
    -Author "Team IT" `
    -Description "Strumenti di gestione server per l'infrastruttura Contoso" `
    -PowerShellVersion "5.1" `
    -FunctionsToExport @("Get-ServerStatus", "Set-ServerConfig", "Invoke-ServerAudit") `
    -CmdletsToExport @() `
    -VariablesToExport @() `
    -AliasesToExport @() `
    -Tags @("Server", "Administration", "Monitoring") `
    -RequiredModules @("ActiveDirectory")
```

### Root Module (.psm1) con Dot-Sourcing

```powershell
# ServerTools.psm1

# Importare tutte le funzioni private
$privateFunctions = Get-ChildItem -Path "$PSScriptRoot\Private\*.ps1" -ErrorAction SilentlyContinue
foreach ($file in $privateFunctions) {
    try {
        . $file.FullName
    } catch {
        Write-Error "Errore nell'importazione di $($file.Name): $_"
    }
}

# Importare tutte le funzioni pubbliche
$publicFunctions = Get-ChildItem -Path "$PSScriptRoot\Public\*.ps1" -ErrorAction SilentlyContinue
foreach ($file in $publicFunctions) {
    try {
        . $file.FullName
    } catch {
        Write-Error "Errore nell'importazione di $($file.Name): $_"
    }
}

# Esportare solo le funzioni pubbliche
Export-ModuleMember -Function $publicFunctions.BaseName
```

### Esempio di Funzione Pubblica

```powershell
# Public\Get-ServerStatus.ps1
function Get-ServerStatus {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [Alias("ComputerName", "CN")]
        [string[]]$Name,

        [Parameter()]
        [PSCredential]$Credential,

        [Parameter()]
        [switch]$Detailed
    )

    begin {
        Write-Verbose "Inizio verifica stato server..."
        $sessionParams = @{}
        if ($Credential) { $sessionParams.Credential = $Credential }
    }

    process {
        foreach ($server in $Name) {
            Write-Verbose "Verifica di $server..."

            $online = Test-Connection -ComputerName $server -Count 1 -Quiet -ErrorAction SilentlyContinue

            $result = [PSCustomObject]@{
                PSTypeName = 'ServerTools.ServerStatus'
                Name       = $server
                Online     = $online
                CheckTime  = Get-Date
            }

            if ($online -and $Detailed) {
                try {
                    $os = Get-CimInstance Win32_OperatingSystem -ComputerName $server @sessionParams -ErrorAction Stop
                    $result | Add-Member -NotePropertyName "OS" -NotePropertyValue $os.Caption
                    $result | Add-Member -NotePropertyName "UptimeDays" -NotePropertyValue (New-TimeSpan -Start $os.LastBootUpTime).Days
                    $result | Add-Member -NotePropertyName "FreeMemoryMB" -NotePropertyValue ([math]::Round($os.FreePhysicalMemory / 1024))
                } catch {
                    Write-Warning "Impossibile raccogliere dettagli da $server : $_"
                }
            }

            Write-AuditLog -Server $server -Action "StatusCheck" -Result $online
            $result
        }
    }

    end {
        Write-Verbose "Verifica completata."
    }
}
```

### Module Manifest — Approfondimento

Il manifest `.psd1` è il cuore dell'identità di un modulo. Contiene metadati, dipendenze, controllo delle esportazioni e informazioni per la PSGallery. Un manifest ben scritto è la differenza tra un modulo professionale e uno amatoriale.

```powershell
# Campi chiave del manifest .psd1
@{
    RootModule        = 'ServerTools.psm1'
    ModuleVersion     = '2.1.0'
    CompatiblePSEditions = @('Desktop', 'Core')   # PS 5.1 e PS 7+
    GUID              = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    Author            = 'Team IT Contoso'
    CompanyName       = 'Contoso S.p.A.'
    Copyright         = '(c) 2026 Contoso. Tutti i diritti riservati.'
    Description       = 'Strumenti di gestione e monitoraggio server per infrastruttura Contoso.'
    PowerShellVersion = '5.1'
    DotNetFrameworkVersion = '4.7.2'    # Solo per Desktop edition

    # Controllo esportazioni — SEMPRE esplicito
    FunctionsToExport = @(
        'Get-ServerStatus'
        'Set-ServerConfig'
        'Invoke-ServerAudit'
        'New-ServerReport'
    )
    CmdletsToExport   = @()
    VariablesToExport  = @()
    AliasesToExport    = @()

    # Dipendenze
    RequiredModules    = @(
        @{ ModuleName = 'ActiveDirectory'; ModuleVersion = '1.0.0.0' }
        @{ ModuleName = 'Microsoft.PowerShell.SecretManagement'; ModuleVersion = '1.1.0' }
    )
    RequiredAssemblies = @()

    # Nested modules (moduli caricati nel contesto del modulo principale)
    NestedModules      = @('Helpers\FormatHelper.psm1')

    # Metadati per PSGallery
    PrivateData = @{
        PSData = @{
            Tags         = @('Server', 'Administration', 'Monitoring', 'Windows')
            LicenseUri   = 'https://github.com/contoso/ServerTools/blob/main/LICENSE'
            ProjectUri   = 'https://github.com/contoso/ServerTools'
            IconUri      = 'https://raw.githubusercontent.com/contoso/ServerTools/main/icon.png'
            ReleaseNotes = 'v2.1.0: Aggiunto supporto SSH remoting, migliorato error handling.'
            Prerelease   = ''   # Impostare a 'beta1' per versioni pre-release
        }
    }
}
```

### PSModulePath e Module Autoloading

PowerShell cerca i moduli nelle directory elencate in `$env:PSModulePath`. Dalla versione 3.0, il module autoloading importa automaticamente un modulo quando si invoca uno dei suoi comandi esportati.

```powershell
# Visualizzare i percorsi di ricerca moduli
$env:PSModulePath -split [System.IO.Path]::PathSeparator

# Percorsi tipici:
# - C:\Users\<utente>\Documents\PowerShell\Modules     (utente, PS 7)
# - C:\Program Files\PowerShell\Modules                (sistema, PS 7)
# - C:\Program Files\PowerShell\7\Modules              (built-in, PS 7)
# - C:\Users\<utente>\Documents\WindowsPowerShell\Modules (utente, PS 5.1)
# - C:\Program Files\WindowsPowerShell\Modules          (sistema, PS 5.1)

# Aggiungere un percorso personalizzato (sessione corrente)
$env:PSModulePath += [System.IO.Path]::PathSeparator + 'C:\CustomModules'

# Aggiungere persistentemente via profilo
Add-Content $PROFILE "`n`$env:PSModulePath += '$([System.IO.Path]::PathSeparator)C:\CustomModules'"

# Forzare la ri-discovery dei moduli dopo aver aggiunto un percorso
Get-Module -ListAvailable -Refresh

# Verificare quale modulo viene trovato per primo (priorità)
Get-Module -ListAvailable -Name ServerTools | Select-Object Name, Version, ModuleBase
```

### Nested Modules

I nested modules vengono caricati nel contesto del modulo padre e possono accedere alle sue funzioni private.

```powershell
# Struttura con nested modules
# ServerTools\
# ├── ServerTools.psd1
# ├── ServerTools.psm1
# ├── Helpers\
# │   ├── FormatHelper.psm1     # Nested module
# │   └── DatabaseHelper.psm1   # Nested module
# └── Public\
#     └── *.ps1

# Nel manifest (.psd1):
# NestedModules = @('Helpers\FormatHelper.psm1', 'Helpers\DatabaseHelper.psm1')

# Le funzioni esportate dai nested modules sono visibili nel modulo padre
# ma controllate da FunctionsToExport nel manifest del padre
```

### Pubblicazione su PSGallery

```powershell
# Registrare la API key (ottenuta da https://www.powershellgallery.com/account)
$apiKey = Read-Host -AsSecureString "PSGallery API Key"
$apiKeyPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
)

# Verificare il modulo prima della pubblicazione
Test-ModuleManifest -Path "C:\Modules\ServerTools\ServerTools.psd1"
Invoke-ScriptAnalyzer -Path "C:\Modules\ServerTools\" -Recurse -Severity Error, Warning

# Pubblicare su PSGallery
Publish-Module -Path "C:\Modules\ServerTools" -NuGetApiKey $apiKeyPlain -Verbose

# Pubblicare su un repository privato (NuGet feed interno)
Register-PSRepository -Name "ContosoGallery" `
    -SourceLocation "https://nuget.contoso.com/v2" `
    -PublishLocation "https://nuget.contoso.com/v2/package" `
    -InstallationPolicy Trusted

Publish-Module -Path "C:\Modules\ServerTools" `
    -Repository "ContosoGallery" `
    -NuGetApiKey $internalApiKey

# Installare da repository privato
Install-Module ServerTools -Repository ContosoGallery -Scope CurrentUser
```

---

## Testing con Pester

Pester è il framework di testing standard per PowerShell. Dalla versione 5, utilizza una sintassi basata su container e discovery.

```powershell
# Installare Pester 5
Install-Module Pester -MinimumVersion 5.0.0 -Force -SkipPublisherCheck

# Tests\Get-ServerStatus.Tests.ps1
BeforeAll {
    # Importare il modulo da testare
    $modulePath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    Import-Module "$modulePath\ServerTools.psd1" -Force
}

Describe "Get-ServerStatus" {
    Context "Quando il server è raggiungibile" {
        BeforeAll {
            # Mock di Test-Connection per simulare server online
            Mock Test-Connection { $true } -ModuleName ServerTools
            Mock Get-CimInstance {
                [PSCustomObject]@{
                    Caption             = "Microsoft Windows Server 2022"
                    LastBootUpTime      = (Get-Date).AddDays(-10)
                    FreePhysicalMemory  = 4194304  # 4 GB in KB
                }
            } -ModuleName ServerTools
            Mock Write-AuditLog {} -ModuleName ServerTools
        }

        It "Deve restituire Online = true" {
            $result = Get-ServerStatus -Name "TestServer"
            $result.Online | Should -BeTrue
        }

        It "Deve includere il nome del server" {
            $result = Get-ServerStatus -Name "TestServer"
            $result.Name | Should -BeExactly "TestServer"
        }

        It "Con -Detailed deve includere informazioni OS" {
            $result = Get-ServerStatus -Name "TestServer" -Detailed
            $result.OS | Should -Not -BeNullOrEmpty
            $result.UptimeDays | Should -BeGreaterOrEqual 0
        }

        It "Deve accettare input dalla pipeline" {
            $results = @("SRV01", "SRV02") | Get-ServerStatus
            $results.Count | Should -Be 2
        }
    }

    Context "Quando il server non è raggiungibile" {
        BeforeAll {
            Mock Test-Connection { $false } -ModuleName ServerTools
            Mock Write-AuditLog {} -ModuleName ServerTools
        }

        It "Deve restituire Online = false" {
            $result = Get-ServerStatus -Name "OfflineServer"
            $result.Online | Should -BeFalse
        }

        It "Non deve tentare di raccogliere dettagli" {
            Get-ServerStatus -Name "OfflineServer" -Detailed
            Should -Not -Invoke Get-CimInstance -ModuleName ServerTools
        }
    }

    Context "Validazione parametri" {
        It "Deve richiedere il parametro Name" {
            { Get-ServerStatus } | Should -Throw
        }

        It "Deve accettare un array di nomi" {
            Mock Test-Connection { $true } -ModuleName ServerTools
            Mock Write-AuditLog {} -ModuleName ServerTools
            $results = Get-ServerStatus -Name @("SRV01", "SRV02", "SRV03")
            $results.Count | Should -Be 3
        }
    }
}

# Eseguire i test
Invoke-Pester -Path "C:\Modules\ServerTools\Tests\" -Output Detailed

# Eseguire con code coverage
$pesterConfig = New-PesterConfiguration
$pesterConfig.Run.Path = "C:\Modules\ServerTools\Tests\"
$pesterConfig.CodeCoverage.Enabled = $true
$pesterConfig.CodeCoverage.Path = @("C:\Modules\ServerTools\Public\*.ps1")
$pesterConfig.Output.Verbosity = "Detailed"
Invoke-Pester -Configuration $pesterConfig
```

### Pester e CI/CD Integration

Pester si integra con le principali pipeline CI/CD tramite output JUnit/NUnit e exit code non-zero in caso di fallimento.

```powershell
# Configurazione Pester per CI/CD (GitHub Actions, Azure DevOps, Jenkins)
$ciConfig = New-PesterConfiguration
$ciConfig.Run.Path = "./Tests/"
$ciConfig.Run.Exit = $true                    # Exit con codice non-zero se test falliscono
$ciConfig.Run.Throw = $true                   # Lanciare eccezione su fallimento

# Output in formato NUnit per CI
$ciConfig.TestResult.Enabled = $true
$ciConfig.TestResult.OutputFormat = "NUnitXml"
$ciConfig.TestResult.OutputPath = "./TestResults/pester-results.xml"

# Code coverage con soglia minima
$ciConfig.CodeCoverage.Enabled = $true
$ciConfig.CodeCoverage.Path = @("./Public/*.ps1", "./Private/*.ps1")
$ciConfig.CodeCoverage.OutputFormat = "JaCoCo"
$ciConfig.CodeCoverage.OutputPath = "./TestResults/coverage.xml"
$ciConfig.CodeCoverage.CoveragePercentTarget = 80   # Soglia minima 80%

$ciConfig.Output.Verbosity = "Detailed"

Invoke-Pester -Configuration $ciConfig
```

```yaml
# Esempio: GitHub Actions workflow per test Pester
# .github/workflows/test.yml
name: PowerShell Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Pester
        shell: pwsh
        run: Install-Module Pester -MinimumVersion 5.5.0 -Force
      - name: Run Tests
        shell: pwsh
        run: |
          $config = New-PesterConfiguration
          $config.Run.Path = "./Tests/"
          $config.Run.Exit = $true
          $config.CodeCoverage.Enabled = $true
          $config.CodeCoverage.Path = @("./Public/*.ps1")
          $config.TestResult.Enabled = $true
          $config.TestResult.OutputPath = "./TestResults/results.xml"
          Invoke-Pester -Configuration $config
      - name: Publish Test Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: ./TestResults/
```

### Pattern di Test Avanzati

```powershell
# Test con dati parametrizzati (TestCases)
Describe "ConvertTo-Bytes" {
    It "Converte '<Input>' in <Expected> bytes" -TestCases @(
        @{ Input = "1KB"; Expected = 1024 }
        @{ Input = "1MB"; Expected = 1048576 }
        @{ Input = "1.5GB"; Expected = 1610612736 }
        @{ Input = "0B"; Expected = 0 }
    ) {
        ConvertTo-Bytes -Value $Input | Should -Be $Expected
    }
}

# Test con mock di comandi esterni
Describe "Invoke-ServerAudit" {
    BeforeAll {
        Mock Invoke-Command {
            [PSCustomObject]@{
                ComputerName = $ComputerName
                Services = 42
                FreeGB = 120.5
            }
        } -ModuleName ServerTools
    }

    It "Non deve fallire se il server è raggiungibile" {
        { Invoke-ServerAudit -ComputerName "TestSRV" } | Should -Not -Throw
    }

    It "Deve chiamare Invoke-Command esattamente una volta" {
        Invoke-ServerAudit -ComputerName "TestSRV"
        Should -Invoke Invoke-Command -Times 1 -Exactly -ModuleName ServerTools
    }
}

# BeforeEach e AfterEach per isolamento
Describe "Set-ServerConfig" {
    BeforeEach {
        $script:tempFile = New-TemporaryFile
        '{}' | Set-Content $script:tempFile
    }

    AfterEach {
        Remove-Item $script:tempFile -ErrorAction SilentlyContinue
    }

    It "Deve scrivere la configurazione nel file" {
        Set-ServerConfig -Path $script:tempFile -Key "MaxThreads" -Value 8
        $content = Get-Content $script:tempFile -Raw | ConvertFrom-Json
        $content.MaxThreads | Should -Be 8
    }
}
```

---

## PSScriptAnalyzer e Qualità del Codice

PSScriptAnalyzer è il linter ufficiale per PowerShell, basato su regole che verificano conformità con le best practices.

```powershell
# Installare PSScriptAnalyzer
Install-Module PSScriptAnalyzer -Force

# Analizzare un singolo file
Invoke-ScriptAnalyzer -Path "C:\Scripts\MyScript.ps1"

# Analizzare un'intera cartella ricorsivamente
Invoke-ScriptAnalyzer -Path "C:\Modules\ServerTools\" -Recurse |
    Format-Table -Property RuleName, Severity, ScriptName, Line, Message -AutoSize

# Filtrare per severità
Invoke-ScriptAnalyzer -Path "C:\Scripts\" -Recurse -Severity Error, Warning

# Usare un set di regole personalizzato
$rules = @{
    Rules = @{
        PSAvoidUsingCmdletAliases = @{
            Enabled = $true
        }
        PSUseApprovedVerbs = @{
            Enabled = $true
        }
        PSAvoidUsingPlainTextForPassword = @{
            Enabled = $true
        }
        PSUseShouldProcessForStateChangingFunctions = @{
            Enabled = $true
        }
    }
}

$rules | ConvertTo-Json -Depth 3 | Set-Content "C:\Config\PSScriptAnalyzerSettings.json"
Invoke-ScriptAnalyzer -Path "C:\Scripts\" -Settings "C:\Config\PSScriptAnalyzerSettings.json"

# Correzione automatica dove possibile
Invoke-ScriptAnalyzer -Path "C:\Scripts\MyScript.ps1" -Fix

# Regole più importanti da conoscere:
# PSAvoidUsingCmdletAliases      - Non usare alias (ls, cd, %) negli script
# PSAvoidUsingPositionalParameters - Usare sempre parametri nominati
# PSAvoidUsingInvokeExpression   - Evitare Invoke-Expression (sicurezza)
# PSUseDeclaredVarsMoreThanAssignments - Variabili dichiarate ma mai usate
# PSAvoidGlobalVars              - Evitare variabili $global:
# PSUseSingularNouns             - Nomi di funzione con sostantivi singolari
# PSAvoidUsingPlainTextForPassword - Non usare [string] per password
# PSUseShouldProcessForStateChangingFunctions - Supportare -WhatIf/-Confirm
```

---

## Best Practices

**Usare sempre CmdletBinding:** Ogni funzione avanzata dovrebbe dichiarare `[CmdletBinding()]` per supportare `-Verbose`, `-Debug`, `-ErrorAction` e altri parametri comuni. Questo costa zero sforzo e migliora drasticamente l'usabilità della funzione.

**Preferire PSCustomObject a hashtable per l'output:** Quando una funzione restituisce dati strutturati, PSCustomObject è sempre preferibile perché si integra con la pipeline, `Format-Table`, `Export-Csv` e `ConvertTo-Json` senza conversioni aggiuntive.

**Non catturare eccezioni generiche:** Evitare `catch { }` vuoti o `catch [Exception]` troppo ampi. Catturare le eccezioni specifiche attese e lasciare che le altre propaghino. Un errore silente è peggiore di un errore visibile.

**Usare -ErrorAction Stop con try/catch:** Il blocco `catch` intercetta solo errori terminanti. Poiché molti cmdlet generano errori non-terminanti per default, è necessario specificare `-ErrorAction Stop` per renderli catturabili.

**Validare i parametri:** Utilizzare gli attributi di validazione (`[ValidateNotNullOrEmpty()]`, `[ValidateRange()]`, `[ValidateSet()]`, `[ValidatePattern()]`, `[ValidateScript()]`) per fallire rapidamente con messaggi chiari piuttosto che procedere con dati invalidi.

**Non scrivere su console con Write-Host:** `Write-Host` bypassa la pipeline e non può essere catturato o rediretto. Usare `Write-Output` per i dati, `Write-Verbose` per i dettagli di esecuzione, `Write-Warning` per gli avvisi e `Write-Error` per gli errori.

**Implementare -WhatIf e -Confirm:** Le funzioni che modificano lo stato del sistema (creazione, modifica, eliminazione di risorse) dovrebbero supportare `SupportsShouldProcess` per permettere un dry-run sicuro.

**Usare percorsi completi:** Non fare affidamento sulla directory corrente. Usare `$PSScriptRoot` per percorsi relativi allo script e percorsi completi per tutto il resto. La directory corrente cambia in contesti diversi (task scheduler, remoting, jobs).

---

## Troubleshooting

### Problema: Script Funziona in Console ma Fallisce come Scheduled Task

**Sintomi**: Uno script PowerShell che funziona perfettamente quando eseguito manualmente in console fallisce silenziosamente o con errori quando eseguito tramite Task Scheduler.

**Causa**: Le cause più comuni sono: execution policy diversa per l'utente del task, profilo PowerShell non caricato, mancanza di moduli nel path, percorsi relativi che si risolvono diversamente, variabili d'ambiente mancanti, oppure il task viene eseguito come x86 invece che x64.

**Soluzione**:

```powershell
# Configurazione corretta del Task Scheduler:
# Programma: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
# Argomenti: -NoProfile -ExecutionPolicy Bypass -File "C:\Scripts\MyScript.ps1"
# Directory: C:\Scripts

# Per PowerShell 7:
# Programma: C:\Program Files\PowerShell\7\pwsh.exe
# Argomenti: -NoProfile -File "C:\Scripts\MyScript.ps1"

# Aggiungere logging esplicito allo script
Start-Transcript -Path "C:\Logs\task-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
try {
    # ... corpo dello script ...
} catch {
    Write-Error "Errore fatale: $_"
    $_ | Out-File "C:\Logs\error.log" -Append
} finally {
    Stop-Transcript
}
```

### Problema: Invoke-RestMethod Restituisce Errore SSL/TLS

**Sintomi**: Le chiamate API via HTTPS falliscono con "The underlying connection was closed" o "Could not create SSL/TLS secure channel".

**Causa**: La versione di TLS negoziata non è supportata dall'endpoint. PowerShell 5.1 utilizza TLS 1.0 per default su sistemi non aggiornati.

**Soluzione**:

```powershell
# Forzare TLS 1.2 (aggiungere all'inizio dello script)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Per PowerShell 7, TLS 1.2+ è il default — non necessita di questa riga

# Se il certificato del server è self-signed (SOLO in sviluppo)
if ($env:ENVIRONMENT -eq "Development") {
    $PSDefaultParameterValues['Invoke-RestMethod:SkipCertificateCheck'] = $true
}
```

### Problema: Modulo Non Trovato Dopo l'Installazione

**Sintomi**: `Import-Module MyModule` restituisce "Module not found" nonostante il modulo sia stato copiato.

**Causa**: Il modulo non si trova in nessuna delle directory elencate in `$env:PSModulePath`, oppure la struttura delle cartelle non è corretta (il nome della cartella deve corrispondere al nome del modulo).

**Soluzione**:

```powershell
# Verificare i percorsi di ricerca moduli
$env:PSModulePath -split ";"

# Verificare la struttura corretta
# CORRETTO: C:\Modules\ServerTools\ServerTools.psd1
# ERRATO:   C:\Modules\ServerTools.psd1 (manca la cartella)
# ERRATO:   C:\Modules\MyTools\ServerTools.psd1 (nome cartella diverso)

# Aggiungere un percorso personalizzato (persistente via profilo)
Add-Content $PROFILE "`n`$env:PSModulePath += ';C:\CustomModules'"

# Importare da percorso esplicito (workaround)
Import-Module "C:\Modules\ServerTools\ServerTools.psd1" -Force
```

### Tabella Troubleshooting Estesa

| # | Sintomo | Causa Probabile | Soluzione |
|---|---------|-----------------|-----------|
| 1 | Script OK in console, fallisce come Scheduled Task | Execution policy, profilo non caricato, percorsi relativi, architettura x86/x64 | Usare `-NoProfile -ExecutionPolicy Bypass -File`, percorsi assoluti, pwsh.exe x64 |
| 2 | `Invoke-RestMethod` errore SSL/TLS | TLS 1.0 default in PS 5.1 su sistemi non aggiornati | `[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12` |
| 3 | Modulo non trovato dopo installazione | Cartella non in `$env:PSModulePath` o struttura errata | Nome cartella = nome modulo, verificare `$env:PSModulePath` |
| 4 | `catch` non cattura l'errore | Errore non-terminante (la maggior parte dei cmdlet) | Aggiungere `-ErrorAction Stop` al cmdlet |
| 5 | Variabile in `ForEach-Object -Parallel` è `$null` | Scope isolato nei thread paralleli | Usare `$using:variabile` per passare variabili |
| 6 | `ConvertTo-Json` tronca le strutture annidate | Profondità default = 2 | Specificare `-Depth 10` (o il valore necessario) |
| 7 | PSRemoting fallisce su macchine in workgroup | WinRM non configurato, TrustedHosts vuoto | `Enable-PSRemoting -Force`, configurare `TrustedHosts` |
| 8 | Double-hop: accesso negato al secondo server | Credenziali Kerberos non delegate | RBCD, KCD, o CredSSP (vedere sezione dedicata) |
| 9 | `Import-Csv` restituisce solo stringhe | CSV importa tutto come `[string]` | Cast esplicito dopo importazione: `[int]$_.Column` |
| 10 | Pester test passano localmente, falliscono in CI | Dipendenze mancanti, percorsi diversi, moduli non installati | Installare moduli nel workflow CI, usare `$PSScriptRoot` |
| 11 | `Set-Content` produce file con encoding errato | Default encoding varia tra PS 5.1 (UTF-16) e PS 7 (UTF-8 no BOM) | Specificare sempre `-Encoding UTF8` |
| 12 | Script lento con `+=` su array grande | `+=` ricrea l'array ad ogni iterazione — O(n²) | Usare `[System.Collections.Generic.List[object]]` o assegnare output del loop |
| 13 | `Get-Credential` fallisce in script non interattivo | Nessun prompt UI disponibile (CI, servizio, SSH) | Costruire PSCredential da SecretManagement o variabili d'ambiente |
| 14 | Modulo PS 5.1 non funziona in PS 7 | Dipendenze .NET Framework non disponibili in .NET Core | Usare `Import-Module -UseWindowsPowerShell` (WinCompat) |
| 15 | `Invoke-Command` timeout su molti server | Timeout default 240s, connessioni sequenziali | Usare `-ThrottleLimit`, `-SessionOption (New-PSSessionOption -OpenTimeout 30000)` |
| 16 | `$ErrorActionPreference = 'Stop'` causa crash inattesi | Rende terminanti TUTTI gli errori, anche quelli innocui | Preferire `-ErrorAction Stop` per cmdlet specifici |
| 17 | Script firmato diventa invalido dopo modifica | La firma include l'hash dello script | Rifirmare dopo ogni modifica con `Set-AuthenticodeSignature` |
| 18 | `Get-WmiObject` non disponibile in PS 7 | Rimosso in PowerShell Core | Usare `Get-CimInstance` (equivalente moderno) |

---

## Pattern Avanzati di Error Handling

### Try/Catch/Finally con Eccezioni Tipizzate

Un aspetto spesso sottovalutato dell'error handling in PowerShell è la gestione granulare delle eccezioni. Invece di catturare genericamente tutti gli errori, è possibile intercettare tipi specifici di eccezione e reagire in modo appropriato.

```powershell
# Error handling con eccezioni specifiche
function Get-RemoteServiceInfo {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ComputerName,
        [string]$ServiceName = "W32Time"
    )

    try {
        $service = Get-Service -ComputerName $ComputerName -Name $ServiceName -ErrorAction Stop
        [PSCustomObject]@{
            Computer = $ComputerName
            Service  = $service.DisplayName
            Status   = $service.Status
            Success  = $true
        }
    }
    catch [System.Management.Automation.ActionPreferenceStopException] {
        # Errore di connessione remota
        Write-Warning "Impossibile connettersi a $ComputerName"
        [PSCustomObject]@{
            Computer = $ComputerName
            Service  = $ServiceName
            Status   = "Unreachable"
            Success  = $false
        }
    }
    catch [Microsoft.PowerShell.Commands.ServiceCommandException] {
        # Servizio non trovato
        Write-Warning "Servizio '$ServiceName' non trovato su $ComputerName"
        [PSCustomObject]@{
            Computer = $ComputerName
            Service  = $ServiceName
            Status   = "NotFound"
            Success  = $false
        }
    }
    catch {
        # Errore generico non previsto
        Write-Error "Errore imprevisto per $ComputerName : $($_.Exception.GetType().FullName) - $($_.Exception.Message)"
        throw  # Ri-lanciare l'eccezione al chiamante
    }
    finally {
        # Cleanup: eseguito sempre, sia su successo che su errore
        Write-Verbose "Operazione completata per $ComputerName"
    }
}

# Utilizzo con gestione errori aggregata
$servers = @("SRV01", "SRV02", "OFFLINE03", "SRV04")
$results = $servers | ForEach-Object { Get-RemoteServiceInfo -ComputerName $_ -Verbose }
$failures = $results | Where-Object { -not $_.Success }
if ($failures) {
    Write-Warning "Server con problemi: $($failures.Computer -join ', ')"
}
```

### ErrorVariable e WarningVariable

```powershell
# Catturare errori in una variabile senza interrompere l'esecuzione
$allErrors = @()
Get-Service -ComputerName "SERVER01","OFFLINE02","SERVER03" -Name "Spooler" `
    -ErrorAction SilentlyContinue -ErrorVariable +allErrors

# $allErrors ora contiene tutti gli errori generati
$allErrors | ForEach-Object {
    Write-Output "Errore: $($_.TargetObject) - $($_.Exception.Message)"
}

# Pattern avanzato: retry con backoff esponenziale
function Invoke-WithRetry {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [scriptblock]$ScriptBlock,
        [int]$MaxRetries = 3,
        [int]$InitialDelaySeconds = 2
    )

    $attempt = 0
    $lastError = $null

    do {
        $attempt++
        try {
            $result = & $ScriptBlock
            return $result
        }
        catch {
            $lastError = $_
            if ($attempt -lt $MaxRetries) {
                $delay = $InitialDelaySeconds * [math]::Pow(2, $attempt - 1)
                Write-Warning "Tentativo $attempt fallito. Riprovo tra $delay secondi..."
                Start-Sleep -Seconds $delay
            }
        }
    } while ($attempt -lt $MaxRetries)

    Write-Error "Operazione fallita dopo $MaxRetries tentativi: $($lastError.Exception.Message)"
    throw $lastError
}

# Utilizzo
$data = Invoke-WithRetry -MaxRetries 3 -ScriptBlock {
    Invoke-RestMethod -Uri "https://api.example.com/data" -TimeoutSec 10
}
```

### Logging Strutturato

```powershell
# Funzione di logging strutturato per script di produzione
function Write-StructuredLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [ValidateSet("INFO","WARN","ERROR","DEBUG")]
        [string]$Level = "INFO",
        [string]$Source = $MyInvocation.ScriptName,
        [string]$LogPath = "C:\Logs\script.log",
        [hashtable]$Properties = @{}
    )

    $logEntry = [PSCustomObject]@{
        Timestamp  = (Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff")
        Level      = $Level
        Source     = $Source
        Message    = $Message
        Computer   = $env:COMPUTERNAME
        User       = $env:USERNAME
        Properties = ($Properties | ConvertTo-Json -Compress)
    }

    # Scrivere nel file di log (thread-safe con mutex)
    $mutex = New-Object System.Threading.Mutex($false, "LogMutex")
    try {
        $mutex.WaitOne() | Out-Null
        $logEntry | Export-Csv -Path $LogPath -Append -NoTypeInformation -Encoding UTF8
    }
    finally {
        $mutex.ReleaseMutex()
    }

    # Output su console con colori
    switch ($Level) {
        "ERROR" { Write-Host "[$($logEntry.Timestamp)] ERROR: $Message" -ForegroundColor Red }
        "WARN"  { Write-Host "[$($logEntry.Timestamp)] WARN:  $Message" -ForegroundColor Yellow }
        "DEBUG" { Write-Verbose "[$($logEntry.Timestamp)] DEBUG: $Message" }
        default { Write-Host "[$($logEntry.Timestamp)] INFO:  $Message" -ForegroundColor Gray }
    }
}

# Utilizzo
Write-StructuredLog -Message "Script avviato" -Level INFO
Write-StructuredLog -Message "Connessione al server" -Level DEBUG -Properties @{Server="SRV01"; Port=443}
Write-StructuredLog -Message "Timeout connessione" -Level ERROR -Properties @{Server="SRV01"; Timeout=30}
```

### ErrorRecord — Anatomia

Ogni errore in PowerShell è un oggetto `ErrorRecord` con proprietà ricche per il debugging:

```powershell
try {
    Get-Item "C:\FileInesistente.txt" -ErrorAction Stop
} catch {
    $err = $_

    # Proprietà dell'ErrorRecord
    $err.Exception               # L'eccezione .NET sottostante
    $err.Exception.GetType().FullName  # Tipo esatto dell'eccezione
    $err.Exception.Message       # Messaggio di errore
    $err.CategoryInfo            # Categoria (ObjectNotFound, PermissionDenied, etc.)
    $err.FullyQualifiedErrorId   # ID univoco dell'errore
    $err.InvocationInfo          # Informazioni su riga, script, comando che ha generato l'errore
    $err.InvocationInfo.ScriptLineNumber  # Riga dello script
    $err.InvocationInfo.ScriptName        # File dello script
    $err.TargetObject            # Oggetto che ha causato l'errore
    $err.ScriptStackTrace        # Stack trace completo

    # Pattern per report errori dettagliati
    Write-Error -Message "Operazione fallita" -Exception $err.Exception `
        -Category $err.CategoryInfo.Category `
        -ErrorId "CustomErrorId" `
        -TargetObject $err.TargetObject
}
```

### Errori Terminanti vs Non-Terminanti

```powershell
# ERRORE NON-TERMINANTE: il cmdlet segnala l'errore ma continua
# La maggior parte dei cmdlet genera errori non-terminanti per default
Get-Service -ComputerName "OFFLINE01","SRV02"
# SRV02 viene comunque processato anche se OFFLINE01 fallisce

# ERRORE TERMINANTE: interrompe l'esecuzione
# Generato da: throw, cmdlet con -ErrorAction Stop, eccezioni .NET
throw [System.InvalidOperationException]::new("Configurazione non valida")

# $ErrorActionPreference — controlla il comportamento globale
$ErrorActionPreference = 'Stop'         # Rende TUTTI gli errori terminanti
$ErrorActionPreference = 'Continue'     # Default: mostra l'errore e continua
$ErrorActionPreference = 'SilentlyContinue'  # Ignora l'errore silenziosamente
$ErrorActionPreference = 'Inquire'      # Chiede all'utente cosa fare

# -ErrorAction parametro per cmdlet — sovrascrive la preference
Get-Service -Name "Inesistente" -ErrorAction SilentlyContinue
Get-Service -Name "Inesistente" -ErrorAction Stop   # Diventa catturabile con catch
```

### Istruzione trap

L'istruzione `trap` è un meccanismo alternativo a try/catch, ereditato da PowerShell 1.0. Cattura errori terminanti nello scope corrente e in tutti gli scope figli.

```powershell
# trap nello scope di una funzione
function Invoke-RiskyOperation {
    # trap intercetta errori terminanti in questo scope
    trap {
        Write-Warning "Errore catturato: $($_.Exception.Message)"
        Write-Warning "Riga: $($_.InvocationInfo.ScriptLineNumber)"
        continue   # continue → riprende l'esecuzione dopo il comando fallito
                   # break    → propaga l'errore allo scope padre
    }

    Write-Output "Inizio operazione"
    throw "Errore simulato"
    Write-Output "Questa riga viene eseguita con 'continue', saltata con 'break'"
}

# trap con tipo specifico di eccezione
trap [System.IO.FileNotFoundException] {
    Write-Warning "File non trovato: $($_.TargetObject)"
    continue
}

trap [System.UnauthorizedAccessException] {
    Write-Error "Accesso negato: $($_.Exception.Message)"
    break
}
```

---

## PSRemoting — Deep Dive

PSRemoting è il meccanismo di amministrazione remota di PowerShell che permette di eseguire comandi su uno o più computer remoti in modo sicuro e scalabile.

### WinRM Backend

WinRM (Windows Remote Management) è il backend tradizionale, basato su WS-Management. È il default in Windows PowerShell 5.1 e supportato anche in PowerShell 7.

```powershell
# Abilitare PSRemoting (richiede privilegi di amministratore)
Enable-PSRemoting -Force

# Verifica della configurazione WinRM
winrm quickconfig
Test-WSMan -ComputerName "SRV01"
Get-WSManInstance winrm/config -ComputerName "SRV01"

# Listener WinRM — HTTP (5985) e HTTPS (5986)
Get-WSManInstance winrm/config/listener -Enumerate

# Configurare HTTPS listener con certificato
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.Subject -match "SRV01.contoso.com" -and $_.EnhancedKeyUsageList.FriendlyName -contains "Server Authentication"
}
New-WSManInstance winrm/config/listener -SelectorSet @{ Address="*"; Transport="HTTPS" } `
    -ValueSet @{ CertificateThumbprint=$cert.Thumbprint }

# TrustedHosts — per ambienti non-dominio
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "10.0.1.*" -Force
# ATTENZIONE: TrustedHosts disabilita l'autenticazione Kerberos reciproca

# Sessione remota interattiva
Enter-PSSession -ComputerName "SRV01" -Credential $cred

# Comando remoto su più server
Invoke-Command -ComputerName "SRV01","SRV02","SRV03" -ScriptBlock {
    Get-Service W32Time | Select-Object MachineName, Status
}

# Sessione persistente (riutilizzabile, riduce overhead di connessione)
$sessions = New-PSSession -ComputerName "SRV01","SRV02" -Credential $cred
Invoke-Command -Session $sessions -ScriptBlock { Get-Process | Measure-Object }
$sessions | Remove-PSSession
```

### SSH Backend (PowerShell 7+)

PowerShell 7 supporta SSH come backend di trasporto alternativo a WinRM. SSH è preferibile per ambienti misti Windows/Linux e per evitare le complessità di WinRM.

```powershell
# Prerequisiti:
# 1. OpenSSH Server installato e configurato sul target
# 2. Subsystem PowerShell configurato in sshd_config:
#    Subsystem powershell c:/progra~1/powershell/7/pwsh.exe -sshs -NoLogo -NoProfile

# Sessione remota via SSH
Enter-PSSession -HostName "linux01.contoso.com" -UserName "admin" -SSHTransport

# Sessione con chiave SSH
Enter-PSSession -HostName "SRV01" -UserName "admin" -KeyFilePath "~/.ssh/id_ed25519"

# Invoke-Command via SSH su più host (misti Windows/Linux)
$sshSessions = @(
    @{ HostName = "win-srv01"; UserName = "admin" }
    @{ HostName = "linux-srv01"; UserName = "root" }
)
Invoke-Command -SSHConnection $sshSessions -ScriptBlock {
    [PSCustomObject]@{
        Hostname = hostname
        OS = if ($IsLinux) { "Linux" } elseif ($IsWindows) { "Windows" } else { "macOS" }
        PSVersion = $PSVersionTable.PSVersion
    }
}
```

### JEA — Just Enough Administration

JEA crea endpoint PowerShell vincolati che limitano i comandi disponibili agli utenti, implementando il principio del minimo privilegio.

```powershell
# 1. Creare il file Role Capability (.psrc)
New-PSRoleCapabilityFile -Path "C:\JEA\DnsAdmin.psrc" `
    -VisibleCmdlets @(
        'Get-DnsServerZone'
        'Get-DnsServerResourceRecord'
        @{ Name = 'Add-DnsServerResourceRecordA'; Parameters = @{
            Name = 'ZoneName'; ValidateSet = 'contoso.com','test.contoso.com'
        }}
        @{ Name = 'Remove-DnsServerResourceRecord'; Parameters = @{
            Name = 'ZoneName'; ValidateSet = 'test.contoso.com'  # Solo zona test
        }}
    ) `
    -VisibleFunctions @('Get-ServerStatus') `
    -VisibleExternalCommands @('nslookup.exe', 'ipconfig.exe')

# 2. Creare il file Session Configuration (.pssc)
New-PSSessionConfigurationFile -Path "C:\JEA\DnsAdmin.pssc" `
    -SessionType RestrictedRemoteServer `
    -RunAsVirtualAccount `  # Esegue come account virtuale locale (no password)
    -TranscriptDirectory "C:\JEA\Transcripts" `
    -RoleDefinitions @{
        'CONTOSO\DNS-Operators' = @{ RoleCapabilities = 'DnsAdmin' }
        'CONTOSO\DNS-ReadOnly'  = @{ RoleCapabilities = 'DnsViewer' }
    }

# 3. Registrare l'endpoint JEA
Register-PSSessionConfiguration -Name "JEA_DNS" `
    -Path "C:\JEA\DnsAdmin.pssc" `
    -Force

# 4. Utilizzare l'endpoint JEA
$jeaSession = New-PSSession -ComputerName "DNS01" -ConfigurationName "JEA_DNS"
Invoke-Command -Session $jeaSession -ScriptBlock {
    # L'utente vede solo i comandi definiti nella role capability
    Get-Command | Measure-Object  # Pochi comandi disponibili
    Get-DnsServerZone             # Permesso
    # Restart-Service DNS         # ERRORE: comando non disponibile
}

# 5. Verificare i transcript JEA per audit
Get-ChildItem "C:\JEA\Transcripts" -Recurse -Filter "*.txt" |
    Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

### Il Problema del Double-Hop

Il double-hop si verifica quando una sessione remota tenta di accedere risorse su un terzo server. Le credenziali Kerberos non vengono delegate automaticamente al secondo hop.

```
Client → SRV01 (1° hop, OK) → SRV02 (2° hop, FALLISCE — no credenziali)
```

```powershell
# Soluzioni al double-hop (in ordine di sicurezza, dal migliore al peggiore):

# 1. SOLUZIONE MIGLIORE: Kerberos Constrained Delegation (KCD)
# Configurare in AD: SRV01 può delegare a SRV02 per specifici servizi
# Set-ADComputer -Identity SRV01 -Add @{
#     'msDS-AllowedToDelegateTo' = @(
#         'cifs/SRV02.contoso.com'
#         'http/SRV02.contoso.com'
#     )
# }

# 2. Resource-Based Constrained Delegation (RBCD) — preferita da Windows Server 2012+
$srv01 = Get-ADComputer -Identity SRV01
Set-ADComputer -Identity SRV02 -PrincipalsAllowedToDelegateToAccount $srv01

# 3. CredSSP — funzionale ma meno sicuro (le credenziali vengono inviate al server)
# Sul CLIENT:
Enable-WSManCredSSP -Role Client -DelegateComputer "SRV01.contoso.com"
# Sul SERVER (SRV01):
Enable-WSManCredSSP -Role Server

# Usare CredSSP nella sessione:
$session = New-PSSession -ComputerName "SRV01" `
    -Authentication Credssp `
    -Credential $cred

# 4. Passaggio esplicito di credenziali (workaround pragmatico)
Invoke-Command -ComputerName "SRV01" -ScriptBlock {
    param($cred)
    Invoke-Command -ComputerName "SRV02" -Credential $cred -ScriptBlock {
        Get-ChildItem "\\FileServer\Share$"
    }
} -ArgumentList $cred
```

---

## Pipeline Optimization

La pipeline è il cuore di PowerShell. Comprenderne il funzionamento interno è essenziale per scrivere codice performante e idiomatico.

### Anatomia del Pipeline Processing

Ogni funzione avanzata con `[CmdletBinding()]` può implementare tre blocchi che corrispondono alle fasi della pipeline:

```powershell
function Process-ServerData {
    [CmdletBinding()]
    param(
        # ValueFromPipeline: il valore viene passato dalla pipeline
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$ServerName,

        # ValueFromPipelineByPropertyName: il valore viene dal nome della proprietà
        [Parameter(ValueFromPipelineByPropertyName)]
        [Alias("IPAddress")]
        [string]$IP,

        [Parameter()]
        [switch]$Resolve
    )

    begin {
        # Eseguito UNA SOLA VOLTA all'inizio della pipeline
        # Ideale per: inizializzazione risorse, connessioni DB, contatori
        Write-Verbose "Inizializzazione..."
        $results = [System.Collections.Generic.List[PSCustomObject]]::new()
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    }

    process {
        # Eseguito PER OGNI oggetto nella pipeline
        # $_ oppure il parametro con ValueFromPipeline contiene l'oggetto corrente
        $status = Test-Connection -ComputerName $ServerName -Count 1 -Quiet -ErrorAction SilentlyContinue
        $obj = [PSCustomObject]@{
            Server = $ServerName
            IP     = $IP
            Online = $status
        }

        if ($Resolve -and $status) {
            $dns = Resolve-DnsName $ServerName -ErrorAction SilentlyContinue
            $obj | Add-Member -NotePropertyName "DnsResult" -NotePropertyValue $dns.IPAddress
        }

        # Emettere nella pipeline per il prossimo cmdlet (streaming)
        $obj

        # Oppure accumulare per output in blocco
        $results.Add($obj)
    }

    end {
        # Eseguito UNA SOLA VOLTA alla fine della pipeline
        # Ideale per: cleanup, report finali, chiusura connessioni
        $stopwatch.Stop()
        Write-Verbose "Processati $($results.Count) server in $($stopwatch.Elapsed.TotalSeconds)s"
    }
}

# Uso con pipeline
@("SRV01","SRV02","SRV03") | Process-ServerData -Resolve -Verbose

# Uso con ValueFromPipelineByPropertyName
Import-Csv "servers.csv" | Process-ServerData
# Il CSV deve avere colonne "ServerName" (o match per parametro) e "IP" (o "IPAddress" per alias)
```

### Steppable Pipelines

Le steppable pipelines permettono di controllare manualmente le fasi begin/process/end di un cmdlet, utile per il wrapping e l'intercettazione.

```powershell
function Export-FilteredCsv {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(ValueFromPipeline)]
        [PSObject]$InputObject,

        [int]$MaxRows = 10000
    )

    begin {
        # Creare una steppable pipeline per Export-Csv
        $csvParams = @{
            Path = $Path
            NoTypeInformation = $true
            Encoding = 'UTF8'
            Append = $false
        }
        $steppable = { Export-Csv @csvParams }.GetSteppablePipeline()
        $steppable.Begin($true)   # $true = invocato da pipeline
        $rowCount = 0
    }

    process {
        $rowCount++
        if ($rowCount -le $MaxRows) {
            $steppable.Process($InputObject)
        } else {
            Write-Warning "Limite di $MaxRows righe raggiunto, troncamento output."
        }
    }

    end {
        $steppable.End()
        Write-Verbose "Esportate $([math]::Min($rowCount, $MaxRows)) righe su $Path"
    }
}

# Uso: esporta al massimo 5000 righe
Get-Process | Export-FilteredCsv -Path "C:\Reports\processes.csv" -MaxRows 5000
```

### Anti-Pattern Pipeline e Ottimizzazioni

```powershell
# ANTI-PATTERN 1: accumulare in array con +=
# += crea un NUOVO array ad ogni iterazione — O(n²)
$results = @()
foreach ($item in $largeCollection) {
    $results += [PSCustomObject]@{ Name = $item }  # LENTO
}

# CORRETTO: usare List<T> o assegnare direttamente l'output
$results = [System.Collections.Generic.List[PSCustomObject]]::new()
foreach ($item in $largeCollection) {
    $results.Add([PSCustomObject]@{ Name = $item })  # O(1) ammortizzato
}

# ANCORA MEGLIO: assegnazione diretta dall'output della pipeline
$results = foreach ($item in $largeCollection) {
    [PSCustomObject]@{ Name = $item }
}

# ANTI-PATTERN 2: Where-Object in loop annidati — usare hashtable come indice
# LENTO:
$users | ForEach-Object {
    $dept = $departments | Where-Object { $_.Id -eq $user.DeptId }
}
# VELOCE: indicizzare con hashtable
$deptIndex = @{}
$departments | ForEach-Object { $deptIndex[$_.Id] = $_ }
$users | ForEach-Object {
    $dept = $deptIndex[$_.DeptId]  # O(1) lookup
}

# ANTI-PATTERN 3: chiamate .NET in pipeline vs foreach
# Pipeline ForEach-Object: overhead per ogni oggetto (scriptblock invocation)
Measure-Command { 1..100000 | ForEach-Object { $_ * 2 } }    # ~2s
# foreach statement: molto più veloce
Measure-Command { foreach ($i in 1..100000) { $i * 2 } }     # ~0.1s
# Usare ForEach-Object solo quando serve lo streaming nella pipeline
```

---

## Sviluppo Class-Based

PowerShell 5.0 ha introdotto le classi, portando paradigmi OOP nel linguaggio. Le classi sono utili per strutture dati complesse, risorse DSC e validazione di tipi.

### Classi, Proprietà e Metodi

```powershell
class NetworkDevice {
    # Proprietà con tipi
    [string]$Hostname
    [string]$IPAddress
    [ValidateSet("Switch","Router","Firewall","AccessPoint")]
    [string]$Type
    [int]$Port = 22
    hidden [PSCredential]$Credential   # hidden: non mostrata da Get-Member di default

    # Costruttore default
    NetworkDevice() {
        $this.Type = "Switch"
    }

    # Costruttore con parametri
    NetworkDevice([string]$hostname, [string]$ip, [string]$type) {
        $this.Hostname = $hostname
        $this.IPAddress = $ip
        $this.Type = $type
    }

    # Metodo
    [bool] TestConnection() {
        return Test-Connection -ComputerName $this.IPAddress -Count 1 -Quiet -ErrorAction SilentlyContinue
    }

    # Metodo con parametri
    [PSCustomObject] GetInfo([bool]$detailed) {
        $info = [PSCustomObject]@{
            Hostname = $this.Hostname
            IP       = $this.IPAddress
            Type     = $this.Type
            Online   = $this.TestConnection()
        }
        if ($detailed) {
            $dns = Resolve-DnsName $this.IPAddress -ErrorAction SilentlyContinue
            $info | Add-Member -NotePropertyName "DnsName" -NotePropertyValue $dns.NameHost
        }
        return $info
    }

    # Override di ToString
    [string] ToString() {
        return "$($this.Hostname) ($($this.IPAddress)) [$($this.Type)]"
    }
}

# Utilizzo
$switch = [NetworkDevice]::new("SW-CORE01", "10.0.1.1", "Switch")
$switch.TestConnection()
$switch.GetInfo($true)

# Array di oggetti tipizzati
[NetworkDevice[]]$inventory = @(
    [NetworkDevice]::new("SW-01", "10.0.1.1", "Switch")
    [NetworkDevice]::new("FW-01", "10.0.1.254", "Firewall")
    [NetworkDevice]::new("RT-01", "10.0.1.253", "Router")
)
$inventory | ForEach-Object { $_.GetInfo($false) } | Format-Table
```

### Enum in PowerShell

```powershell
# Enum semplice
enum ServerRole {
    DomainController
    FileServer
    WebServer
    DatabaseServer
    ApplicationServer
}

# Enum con valori espliciti (flags)
[Flags()] enum ServiceState {
    None     = 0
    Running  = 1
    Degraded = 2
    Critical = 4
    Maintenance = 8
}

# Utilizzo di enum
[ServerRole]$role = "WebServer"
[ServerRole]$role2 = [ServerRole]::DatabaseServer

# Flags: combinare valori
[ServiceState]$state = [ServiceState]::Running -bor [ServiceState]::Degraded
$state.HasFlag([ServiceState]::Running)   # $true
$state.HasFlag([ServiceState]::Critical)  # $false

# Enum come validatore nei parametri
function Set-ServerRole {
    param(
        [Parameter(Mandatory)]
        [ServerRole]$Role   # Accetta solo valori dell'enum, con tab completion
    )
    Write-Output "Ruolo impostato a: $Role"
}
```

### Ereditarietà

```powershell
# Classe base
class Asset {
    [string]$AssetTag
    [string]$Location
    [datetime]$PurchaseDate

    [int] GetAgeDays() {
        return (New-TimeSpan -Start $this.PurchaseDate -End (Get-Date)).Days
    }

    [bool] IsWarrantyExpired([int]$warrantyYears) {
        return $this.GetAgeDays() -gt ($warrantyYears * 365)
    }
}

# Classe derivata
class ServerAsset : Asset {
    [string]$Hostname
    [string]$OperatingSystem
    [int]$RAM_GB
    [int]$CPU_Cores

    ServerAsset([string]$tag, [string]$hostname) {
        $this.AssetTag = $tag
        $this.Hostname = $hostname
        $this.PurchaseDate = Get-Date
    }

    [PSCustomObject] GetSummary() {
        return [PSCustomObject]@{
            AssetTag  = $this.AssetTag
            Hostname  = $this.Hostname
            OS        = $this.OperatingSystem
            AgeMonths = [math]::Round($this.GetAgeDays() / 30, 1)
            Warranty  = if ($this.IsWarrantyExpired(3)) { "SCADUTA" } else { "Valida" }
        }
    }
}

$srv = [ServerAsset]::new("SRV-2026-001", "PROD-WEB01")
$srv.OperatingSystem = "Windows Server 2022"
$srv.RAM_GB = 32
$srv.GetSummary()
```

### Emulazione di Interfacce

PowerShell non supporta interfacce native, ma è possibile emularle con classi base astratte e validazione runtime.

```powershell
# Classe base che funge da interfaccia
class IMonitorable {
    [string] GetHealthStatus() {
        throw [System.NotImplementedException]::new(
            "La classe derivata deve implementare GetHealthStatus()"
        )
    }

    [hashtable] GetMetrics() {
        throw [System.NotImplementedException]::new(
            "La classe derivata deve implementare GetMetrics()"
        )
    }
}

# Implementazione
class WindowsServer : IMonitorable {
    [string]$Hostname

    WindowsServer([string]$hostname) { $this.Hostname = $hostname }

    [string] GetHealthStatus() {
        $ping = Test-Connection -ComputerName $this.Hostname -Count 1 -Quiet -ErrorAction SilentlyContinue
        return if ($ping) { "Healthy" } else { "Unreachable" }
    }

    [hashtable] GetMetrics() {
        return @{
            CPU    = (Get-Counter "\Processor(_Total)\% Processor Time" -ErrorAction SilentlyContinue).CounterSamples.CookedValue
            Memory = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB
        }
    }
}

# Funzione che lavora con qualsiasi IMonitorable
function Test-MonitorableHealth {
    param([IMonitorable]$Target)
    $status = $Target.GetHealthStatus()
    Write-Output "$($Target.GetType().Name): $status"
}
```

---

## DSC — Desired State Configuration

DSC è il framework dichiarativo di PowerShell per la configurazione e il mantenimento dello stato dei sistemi. Definisce il "come dovrebbe essere" un sistema, lasciando al motore DSC la responsabilità di applicare e mantenere quella configurazione.

### Concetti Fondamentali

```
┌─────────────────────────────────────────────────────────┐
│                   DSC ARCHITECTURE                      │
│                                                         │
│  Configuration Script (.ps1)                            │
│       ↓ compilazione                                    │
│  MOF Document (.mof)                                    │
│       ↓ distribuzione                                   │
│  Local Configuration Manager (LCM)                      │
│       ↓ applicazione                                    │
│  DSC Resources (built-in + community)                   │
│       ↓ convergenza                                     │
│  Stato Desiderato = Stato Corrente                      │
└─────────────────────────────────────────────────────────┘
```

### Configuration Block

```powershell
# Definire una configurazione DSC
Configuration WebServerSetup {
    param(
        [Parameter(Mandatory)]
        [string[]]$ComputerName,

        [PSCredential]$Credential
    )

    # Importare risorse DSC
    Import-DscResource -ModuleName PSDesiredStateConfiguration
    Import-DscResource -ModuleName xWebAdministration -ModuleVersion "3.3.0"

    # Nodo: configurazione per ogni computer target
    Node $ComputerName {

        # Garantire che IIS sia installato
        WindowsFeature IIS {
            Name   = "Web-Server"
            Ensure = "Present"
        }

        # Garantire che ASP.NET sia installato (dipende da IIS)
        WindowsFeature AspNet {
            Name      = "Web-Asp-Net45"
            Ensure    = "Present"
            DependsOn = "[WindowsFeature]IIS"
        }

        # Creare un sito web
        xWebsite DefaultSite {
            Name            = "ContosoWeb"
            PhysicalPath    = "C:\inetpub\contosoweb"
            State           = "Started"
            BindingInfo     = @(
                MSFT_xWebBindingInformation {
                    Protocol = "HTTP"
                    Port     = 80
                }
                MSFT_xWebBindingInformation {
                    Protocol = "HTTPS"
                    Port     = 443
                    CertificateThumbprint = "ABC123..."
                }
            )
            DependsOn       = "[WindowsFeature]IIS"
        }

        # Garantire che un servizio sia in esecuzione
        Service W3SVC {
            Name        = "W3SVC"
            StartupType = "Automatic"
            State       = "Running"
            DependsOn   = "[WindowsFeature]IIS"
        }

        # Garantire che una directory esista
        File WebContent {
            DestinationPath = "C:\inetpub\contosoweb"
            Type            = "Directory"
            Ensure          = "Present"
        }

        # Firewall rule
        Script FirewallRule {
            GetScript = {
                $rule = Get-NetFirewallRule -Name "AllowHTTPS" -ErrorAction SilentlyContinue
                @{ Result = if ($rule) { $rule.Enabled } else { "NotFound" } }
            }
            TestScript = {
                $rule = Get-NetFirewallRule -Name "AllowHTTPS" -ErrorAction SilentlyContinue
                return ($null -ne $rule -and $rule.Enabled -eq 'True')
            }
            SetScript = {
                New-NetFirewallRule -Name "AllowHTTPS" -DisplayName "Allow HTTPS" `
                    -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
            }
        }
    }
}

# Compilare la configurazione (genera file .mof)
WebServerSetup -ComputerName "WEB01","WEB02" -OutputPath "C:\DSC\WebServer"
```

### LCM e Modalità Push/Pull

```powershell
# Visualizzare la configurazione del LCM
Get-DscLocalConfigurationManager

# Configurare il LCM
[DSCLocalConfigurationManager()]
Configuration LCMConfig {
    Node "WEB01" {
        Settings {
            RefreshMode                = "Pull"          # Pull da un server, o "Push"
            RefreshFrequencyMins       = 30              # Ogni 30 minuti
            ConfigurationModeFrequencyMins = 60          # Verifica conformità ogni 60 min
            ConfigurationMode          = "ApplyAndAutoCorrect"  # Auto-corregge derive
            RebootNodeIfNeeded         = $true
            AllowModuleOverwrite       = $true
        }

        # Pull Server (se RefreshMode = Pull)
        ConfigurationRepositoryWeb PullServer {
            ServerURL          = "https://dsc-pull.contoso.com:8080/PSDSCPullServer.svc"
            RegistrationKey    = "xxx-xxx-xxx"
            ConfigurationNames = @("WebServerSetup")
        }
    }
}

# PUSH MODE: applicare direttamente
Start-DscConfiguration -Path "C:\DSC\WebServer" -ComputerName "WEB01" -Wait -Verbose -Force

# Verificare lo stato corrente
Test-DscConfiguration -ComputerName "WEB01" -Detailed

# Ottenere la configurazione corrente
Get-DscConfiguration -CimSession (New-CimSession -ComputerName "WEB01")
```

### Risorsa DSC Class-Based

```powershell
# Una risorsa DSC scritta come classe PowerShell
[DscResource()]
class cServiceMonitor {
    [DscProperty(Key)]
    [string]$ServiceName

    [DscProperty(Mandatory)]
    [string]$ExpectedStatus   # "Running" o "Stopped"

    [DscProperty()]
    [string]$LogPath = "C:\DSC\Logs\ServiceMonitor.log"

    # GET: restituisce lo stato corrente
    [cServiceMonitor] Get() {
        $svc = Get-Service -Name $this.ServiceName -ErrorAction SilentlyContinue
        $this.ExpectedStatus = if ($svc) { $svc.Status.ToString() } else { "NotFound" }
        return $this
    }

    # TEST: verifica se lo stato corrente corrisponde a quello desiderato
    [bool] Test() {
        $svc = Get-Service -Name $this.ServiceName -ErrorAction SilentlyContinue
        if (-not $svc) { return $false }
        return $svc.Status.ToString() -eq $this.ExpectedStatus
    }

    # SET: applica lo stato desiderato
    [void] Set() {
        $svc = Get-Service -Name $this.ServiceName -ErrorAction SilentlyContinue
        if (-not $svc) {
            throw "Servizio '$($this.ServiceName)' non trovato."
        }

        if ($this.ExpectedStatus -eq "Running" -and $svc.Status -ne "Running") {
            Start-Service -Name $this.ServiceName
            "$(Get-Date -Format 'o') | Avviato servizio $($this.ServiceName)" |
                Out-File $this.LogPath -Append
        }
        elseif ($this.ExpectedStatus -eq "Stopped" -and $svc.Status -ne "Stopped") {
            Stop-Service -Name $this.ServiceName -Force
            "$(Get-Date -Format 'o') | Arrestato servizio $($this.ServiceName)" |
                Out-File $this.LogPath -Append
        }
    }
}
```

---

## DSC v3 e Azure Machine Configuration

### Evoluzione di DSC

```powershell
# DSC v3 (precedentemente "DSCv3" o "DSC next") e` la riscrittura completa
# di Desired State Configuration, ora cross-platform e basata su JSON.
# Non e` piu` accoppiata a WMI/CIM ma usa un'architettura a plugin.

# Differenze chiave tra DSC v2 (classico) e DSC v3:
#
# Caratteristica    │ DSC v2 (PS5.1)      │ DSC v3
# ──────────────────┼─────────────────────┼──────────────────────
# Runtime           │ WMI/CIM + LCM       │ CLI standalone (dsc.exe)
# Formato config    │ PowerShell (.ps1)    │ YAML/JSON
# Piattaforma       │ Solo Windows         │ Windows + Linux + macOS
# Risorse           │ MOF o class-based    │ Plugin (qualsiasi lang)
# Orchestratore     │ LCM (pull/push)      │ Azure MC / CLI
# Dipendenze        │ PowerShell 5.1       │ Nessuna (binario standalone)
# Stato             │ Maintenance mode     │ Sviluppo attivo

# Installazione DSC v3 (da winget o GitHub Releases)
winget install Microsoft.DSC

# Verificare versione
dsc --version

# Esempio: configurazione DSC v3 in YAML
# Questo file dichiara che un file specifico deve esistere con un contenuto dato

# config.dsc.yaml:
# $schema: https://raw.githubusercontent.com/PowerShell/DSC/main/schemas/...
# resources:
#   - name: Ensure motd file
#     type: Microsoft.DSC/File
#     properties:
#       path: /etc/motd
#       content: "Managed by DSC v3"
#       ensure: present
#   - name: Ensure NTP service
#     type: Microsoft.DSC/Service
#     properties:
#       name: chronyd
#       state: running
#       enabled: true

# Eseguire in modalita` test (verifica senza modificare)
dsc config test --file config.dsc.yaml

# Eseguire in modalita` set (applica le modifiche)
dsc config set --file config.dsc.yaml

# Esportare la configurazione corrente
dsc config export --file config.dsc.yaml
```

### Azure Machine Configuration (ex Guest Configuration)

```powershell
# Azure Machine Configuration e` il servizio Azure che sostituisce
# Azure Policy Guest Configuration. Usa DSC v3 come motore e permette
# di applicare e verificare configurazioni su VM Azure e server Arc.

# Workflow:
# 1. Scrivere la configurazione DSC v3 (YAML/JSON)
# 2. Pacchettizzare come contenuto Machine Configuration (.zip)
# 3. Pubblicare su Azure Blob Storage
# 4. Assegnare tramite Azure Policy
# 5. La VM/Arc agent scarica, applica, e riporta compliance

# Installare il modulo PowerShell per Machine Configuration
Install-Module GuestConfiguration -Force

# Creare un pacchetto da una configurazione DSC
New-GuestConfigurationPackage `
    -Name "SecurityBaseline" `
    -Configuration ".\compiled\SecurityBaseline.mof" `
    -Type AuditAndSet `
    -Force

# Testare il pacchetto localmente prima del deploy
$report = Test-GuestConfigurationPackage `
    -Path ".\SecurityBaseline\SecurityBaseline.zip"
$report.resources | Format-Table ResourceName, ComplianceStatus

# Pubblicare il pacchetto su Azure Blob Storage
$uri = Publish-GuestConfigurationPackage `
    -Path ".\SecurityBaseline\SecurityBaseline.zip" `
    -ResourceGroupName "rg-governance" `
    -StorageAccountName "stgovernance"

# Creare una Azure Policy definition che referenzia il pacchetto
New-GuestConfigurationPolicy `
    -ContentUri $uri `
    -DisplayName "Security Baseline per Windows Server" `
    -Description "Verifica e applica la baseline di sicurezza aziendale" `
    -Path ".\policies" `
    -Platform Windows `
    -Mode ApplyAndAutoCorrect `
    -Version "1.0.0"

# Pubblicare la policy su Azure
Publish-GuestConfigurationPolicy -Path ".\policies"

# Verificare compliance dal portale:
# Azure Portal → Policy → Compliance → filtrare per "Security Baseline"
# Ogni server mostra: Compliant / Non-compliant / Not started
```

---

## Sicurezza negli Script

### Execution Policy

L'Execution Policy è il primo livello di difesa contro l'esecuzione involontaria di script. Non è un meccanismo di sicurezza infallibile (è facilmente bypassabile), ma previene errori accidentali.

```powershell
# Visualizzare le policy per tutti gli scope
Get-ExecutionPolicy -List

# Scope (in ordine di precedenza):
# MachinePolicy  → GPO Computer Configuration (massima priorità)
# UserPolicy     → GPO User Configuration
# Process        → Solo la sessione corrente
# CurrentUser    → HKCU registry
# LocalMachine   → HKLM registry

# Impostare la policy (richiede Admin per LocalMachine)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine

# Valori:
# Restricted     → Nessuno script eseguibile (default su client Windows)
# AllSigned       → Solo script firmati digitalmente
# RemoteSigned   → Script locali OK, script scaricati devono essere firmati
# Unrestricted   → Tutti gli script (warning per download)
# Bypass         → Nessuna restrizione, nessun warning

# Via GPO: Computer Configuration → Administrative Templates →
# Windows Components → Windows PowerShell → Turn on Script Execution
```

### Firma Digitale degli Script

```powershell
# Creare un certificato di firma codice (per test — usare CA aziendale in produzione)
$cert = New-SelfSignedCertificate -Type CodeSigningCert `
    -Subject "CN=PowerShell Code Signing" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -NotAfter (Get-Date).AddYears(3)

# Firmare uno script
$signingCert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1
Set-AuthenticodeSignature -FilePath "C:\Scripts\Deploy.ps1" `
    -Certificate $signingCert `
    -TimestampServer "http://timestamp.digicert.com"

# Verificare la firma
Get-AuthenticodeSignature -FilePath "C:\Scripts\Deploy.ps1"

# Firmare tutti gli script in una cartella
Get-ChildItem "C:\Scripts\*.ps1" -Recurse | ForEach-Object {
    Set-AuthenticodeSignature -FilePath $_.FullName `
        -Certificate $signingCert `
        -TimestampServer "http://timestamp.digicert.com"
}

# Verificare l'integrità: la firma diventa invalida se lo script viene modificato
$sig = Get-AuthenticodeSignature "C:\Scripts\Deploy.ps1"
if ($sig.Status -ne "Valid") {
    Write-Error "Script $($sig.Path) ha firma invalida: $($sig.StatusMessage)"
}
```

### AMSI — Antimalware Scan Interface

AMSI è l'interfaccia attraverso cui PowerShell invia il contenuto degli script al motore antimalware (Defender o altro) per la scansione in tempo reale. Funziona anche su codice offuscato perché la scansione avviene dopo il de-offuscamento.

```powershell
# AMSI è attivo per default in PowerShell 5.1+ e PowerShell 7+
# Verificare se AMSI è funzionante (questo trigger AMSI come test)
# NOTA: non eseguire in produzione — solo per verificare che AMSI blocca correttamente

# Come funziona:
# 1. L'utente digita/esegue un comando
# 2. PowerShell invia il contenuto a AMSI prima dell'esecuzione
# 3. AMSI lo passa al motore antimalware registrato
# 4. Se malware → blocco con errore "This script contains malicious content"
# 5. Se pulito → esecuzione normale

# Verificare il provider AMSI registrato
Get-CimInstance -Namespace "root/Microsoft/Windows/AMSI" -ClassName "AMSI_Provider" `
    -ErrorAction SilentlyContinue

# AMSI copre anche: .NET, VBScript, JScript, WMI
```

### Constrained Language Mode (CLM)

CLM limita le funzionalità di PowerShell disponibili, bloccando l'accesso diretto a .NET, COM e altre API potenzialmente pericolose.

```powershell
# Verificare la modalità corrente
$ExecutionContext.SessionState.LanguageMode

# Valori possibili:
# FullLanguage         → Tutte le funzionalità (default)
# ConstrainedLanguage  → Limitato: no .NET diretto, no COM, no Add-Type
# RestrictedLanguage   → Solo variabili e operatori base
# NoLanguage           → Solo cmdlet, nessun codice inline

# In CLM queste operazioni sono BLOCCATE:
# [System.IO.File]::ReadAllText("file.txt")     # Accesso .NET diretto
# New-Object -ComObject WScript.Shell            # COM
# Add-Type -TypeDefinition '...'                  # Compilazione C#
# $host.UI.RawUI                                  # Accesso a proprietà host

# CLM si attiva automaticamente in sistemi con:
# - AppLocker in modalità Allow (non Audit)
# - WDAC (Windows Defender Application Control) con policy attiva
# - Device Guard

# Test script per verificare se CLM è attivo
if ($ExecutionContext.SessionState.LanguageMode -eq 'ConstrainedLanguage') {
    Write-Warning "Constrained Language Mode attivo — funzionalità limitate"
    # Usare solo cmdlet nativi, evitare accesso .NET diretto
}
```

### Integrazione con AppLocker e WDAC

```powershell
# AppLocker: verificare le policy attive per script PowerShell
Get-AppLockerPolicy -Effective | Select-Object -ExpandProperty RuleCollections |
    Where-Object { $_.RuleCollectionType -eq "Script" }

# WDAC: verificare le policy attive
Get-CimInstance -ClassName Win32_DeviceGuardPolicy -Namespace "root\Microsoft\Windows\DeviceGuard"

# Creare una policy WDAC che permetta solo script firmati
# (da eseguire su un sistema di riferimento "gold image")
# New-CIPolicy -Level Publisher -FilePath "C:\Policies\BasePolicy.xml" `
#     -UserPEs -MultiplePolicyFormat
# Set-CIPolicySetting -FilePath "C:\Policies\BasePolicy.xml" `
#     -Provider "PowerShell" -Key "ScriptExecution" -Value "Allowed"

# Best practice: usare WDAC al posto di AppLocker per nuovi deployment
# WDAC è enforced a livello kernel, AppLocker è enforced a livello utente
```

---

## Secret Management

Il modulo `Microsoft.PowerShell.SecretManagement` fornisce un'interfaccia unificata per la gestione dei segreti (password, chiavi API, certificati) in PowerShell 7+.

### SecretManagement e SecretStore

```powershell
# Installare i moduli
Install-Module Microsoft.PowerShell.SecretManagement -Force
Install-Module Microsoft.PowerShell.SecretStore -Force

# Registrare il vault locale (SecretStore)
Register-SecretVault -Name "LocalVault" `
    -ModuleName Microsoft.PowerShell.SecretStore `
    -DefaultVault

# Configurare SecretStore (protezione con password)
Set-SecretStoreConfiguration -Authentication Password `
    -PasswordTimeout 900 `    # Timeout 15 minuti
    -Interaction Prompt        # Chiedi password quando necessario

# Salvare segreti
Set-Secret -Name "APIKey-Prod" -Secret "sk-abc123xyz789" -Vault "LocalVault"
Set-Secret -Name "DBPassword" -Secret (ConvertTo-SecureString "P@ssw0rd!" -AsPlainText)
Set-Secret -Name "ServiceAccount" -Secret (Get-Credential)   # PSCredential completo

# Recuperare segreti
$apiKey = Get-Secret -Name "APIKey-Prod" -AsPlainText        # Come stringa
$dbPass = Get-Secret -Name "DBPassword"                       # Come SecureString
$cred   = Get-Secret -Name "ServiceAccount"                   # Come PSCredential

# Elencare tutti i segreti
Get-SecretInfo -Vault "LocalVault" | Format-Table Name, Type, VaultName

# Rimuovere un segreto
Remove-Secret -Name "APIKey-Prod" -Vault "LocalVault"

# Uso negli script: niente più password in chiaro
$headers = @{
    Authorization = "Bearer $(Get-Secret -Name 'APIKey-Prod' -AsPlainText)"
}
Invoke-RestMethod -Uri "https://api.example.com/data" -Headers $headers
```

### Integrazione Azure KeyVault

```powershell
# Installare l'estensione vault per Azure KeyVault
Install-Module Az.KeyVault -Force
Install-Module Az.Accounts -Force

# Autenticarsi con Azure
Connect-AzAccount

# Registrare Azure KeyVault come vault in SecretManagement
# Richiede il modulo: Microsoft.PowerShell.SecretManagement.Az
Install-Module Microsoft.PowerShell.SecretManagement.Az -Force -AllowPrerelease

Register-SecretVault -Name "AzureVault" `
    -ModuleName "Microsoft.PowerShell.SecretManagement.Az" `
    -VaultParameters @{
        AZKVaultName = "contoso-keyvault"
        SubscriptionId = "xxx-xxx-xxx"
    }

# Ora i segreti da Azure KeyVault sono accessibili con la stessa API
$azSecret = Get-Secret -Name "ProdConnectionString" -Vault "AzureVault" -AsPlainText

# Pattern per script che devono funzionare in ambienti diversi
function Get-AppSecret {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    # Priorità: variabile d'ambiente → Azure KeyVault → SecretStore locale
    $envVar = [Environment]::GetEnvironmentVariable($Name)
    if ($envVar) { return $envVar }

    $vaults = Get-SecretVault
    foreach ($vault in $vaults) {
        $secret = Get-Secret -Name $Name -Vault $vault.Name -ErrorAction SilentlyContinue -AsPlainText
        if ($secret) { return $secret }
    }

    throw "Segreto '$Name' non trovato in nessun vault o variabile d'ambiente."
}
```

---

## PowerShell 7.x vs Windows PowerShell

PowerShell 7 (basato su .NET Core / .NET 6+) è il successore cross-platform di Windows PowerShell 5.1. Le due versioni coesistono e hanno differenze significative.

### Differenze Architetturali

| Aspetto | Windows PowerShell 5.1 | PowerShell 7.x |
|---------|------------------------|-----------------|
| Runtime | .NET Framework 4.x | .NET 9.0 (LTS) |
| Eseguibile | `powershell.exe` | `pwsh.exe` |
| Piattaforme | Solo Windows | Windows, Linux, macOS |
| Profilo | `$HOME\Documents\WindowsPowerShell` | `$HOME\Documents\PowerShell` |
| Moduli | `C:\Windows\System32\WindowsPowerShell` | `C:\Program Files\PowerShell\7` |
| Side-by-side | Parte del sistema operativo | Installazione separata |
| Supporto | Solo security fix | Sviluppo attivo |
| WinRM | Nativo | Supportato (richiede config) |
| SSH Remoting | Non supportato | Nativo |

### Funzionalità Esclusive di PowerShell 7.x

```powershell
# 1. Operatore ternario
$status = $isOnline ? "Online" : "Offline"
# Equivale a: $status = if ($isOnline) { "Online" } else { "Offline" }

# 2. Null-coalescing operator
$name = $user.DisplayName ?? $user.SamAccountName ?? "Sconosciuto"
# Equivale a: $name = if ($null -ne $user.DisplayName) { $user.DisplayName } ...

# 3. Null-conditional assignment
$config ??= @{}   # Assegna @{} solo se $config è $null

# 4. Pipeline chain operators (&& e ||)
Build-Project && Deploy-Project     # Deploy solo se Build ha successo
Test-Connection SRV01 || Send-Alert  # Alert solo se ping fallisce

# 5. ForEach-Object -Parallel (già trattato nella sezione parallela)
1..10 | ForEach-Object -Parallel { $_ * 2 } -ThrottleLimit 5

# 6. Clean block nelle funzioni
function Get-Data {
    [CmdletBinding()]
    param([string]$Path)

    begin   { $conn = Open-Connection }
    process { Get-Item $Path }
    end     { }
    clean   {
        # Eseguito SEMPRE, anche su Ctrl+C o pipeline interrotta
        # Più affidabile di 'end' per il cleanup
        if ($conn) { $conn.Close() }
    }
}

# 7. ErrorView conciso
$ErrorView = 'ConciseView'    # Default in PS 7 — errori più leggibili
$ErrorView = 'NormalView'     # Stile tradizionale

# 8. Get-Error per diagnostica dettagliata
Get-Error   # Mostra l'ultimo errore con dettagli completi
Get-Error -Newest 3  # Ultimi 3 errori
```

### Windows Compatibility Module

Il modulo `WindowsCompatibility` permette di usare moduli Windows PowerShell 5.1 in PowerShell 7 tramite remoting implicito.

```powershell
# PowerShell 7 importa automaticamente i moduli Windows tramite WinCompat
# quando il modulo non ha una versione nativa per PS 7
Import-Module ActiveDirectory   # Usa WinCompat automaticamente se necessario

# Verificare se un modulo funziona nativamente o via WinCompat
Get-Module ActiveDirectory | Select-Object Name, ModuleType, CompatiblePSEditions

# Forzare l'importazione esplicita via WinCompat
Import-Module -Name GroupPolicy -UseWindowsPowerShell

# Moduli che RICHIEDONO WinCompat (non hanno versione PS 7 nativa):
# - ActiveDirectory
# - GroupPolicy
# - DHCP Server
# - DNS Server
# - Alcuni moduli RSAT

# Moduli che funzionano NATIVAMENTE in PS 7:
# - Microsoft.PowerShell.* (core)
# - Az.* (Azure)
# - Pester
# - PSScriptAnalyzer
# - Microsoft.Graph.*
```

### Compatibilità negli Script

```powershell
# Pattern per script che devono funzionare su entrambe le versioni
if ($PSVersionTable.PSEdition -eq 'Core') {
    # Codice specifico per PS 7+
    $result = $data ?? "default"
} else {
    # Codice per Windows PowerShell 5.1
    $result = if ($null -ne $data) { $data } else { "default" }
}

# Verificare la versione minima
#Requires -Version 7.0
# oppure check runtime:
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Error "Questo script richiede PowerShell 7 o superiore."
    exit 1
}

# Verificare la piattaforma (solo PS 7+)
if ($IsWindows) { <# codice Windows #> }
if ($IsLinux)   { <# codice Linux #> }
if ($IsMacOS)   { <# codice macOS #> }
```

---

## Logging e Debugging Avanzato

### Stream di Output

PowerShell ha 6 stream di output separati, ciascuno con un proprio scopo:

```powershell
# Stream 1: Output (Success) — dati
Write-Output "Dati per la pipeline"    # Va nella pipeline
# Stream 2: Error
Write-Error "Errore non terminante"
# Stream 3: Warning
Write-Warning "Attenzione: disco quasi pieno"
# Stream 4: Verbose (visibile con -Verbose)
Write-Verbose "Dettaglio: connessione a SRV01..."
# Stream 5: Debug (visibile con -Debug)
Write-Debug "Debug: variabile x = $x"
# Stream 6: Information (PS 5.0+)
Write-Information "Info: operazione completata" -Tags "Status"

# Redirezionare gli stream
# &1 = Success, &2 = Error, &3 = Warning, &4 = Verbose, &5 = Debug, &6 = Information
.\script.ps1 4>&1 5>&1 6>&1 | Tee-Object -FilePath "C:\Logs\all-output.log"
# Redirezionare tutti gli stream a un file
.\script.ps1 *> "C:\Logs\everything.log"
# Solo errori a file, resto a console
.\script.ps1 2> "C:\Logs\errors.log"
```

### Transcript

```powershell
# Transcript: registra TUTTA l'attività della sessione
Start-Transcript -Path "C:\Logs\session-$(Get-Date -Format 'yyyyMMdd-HHmmss').log" `
    -IncludeInvocationHeader   # Include timestamp per ogni comando

# ... operazioni ...

Stop-Transcript

# Transcript automatico via GPO:
# Computer Configuration → Administrative Templates →
# Windows Components → Windows PowerShell → Turn on PowerShell Transcription
# Percorso: \\server\share\Transcripts\%COMPUTERNAME%

# Transcript automatico via profilo
Add-Content $PROFILE @'
Start-Transcript -Path "$HOME\Logs\PS_$(Get-Date -Format 'yyyyMMdd').log" -Append
'@
```

### PSBreakpoint e Debugging

```powershell
# Breakpoint su riga
Set-PSBreakpoint -Script "C:\Scripts\Deploy.ps1" -Line 42

# Breakpoint su variabile (si attiva quando la variabile viene letta o scritta)
Set-PSBreakpoint -Variable "connectionString" -Mode Write
Set-PSBreakpoint -Variable "errorCount" -Mode ReadWrite

# Breakpoint su comando
Set-PSBreakpoint -Command "Invoke-RestMethod"

# Breakpoint condizionale
Set-PSBreakpoint -Script "C:\Scripts\Deploy.ps1" -Line 42 -Action {
    if ($server -eq "PROD-DB01") { break }   # Si ferma solo per il server di produzione
}

# Elencare breakpoint attivi
Get-PSBreakpoint

# Rimuovere breakpoint
Remove-PSBreakpoint -Id 1
Get-PSBreakpoint | Remove-PSBreakpoint   # Rimuovi tutti

# Debugging nel terminale
# Quando il debugger è attivo, comandi disponibili:
# s  (Step Into)    — entra nelle funzioni
# v  (Step Over)    — esegue la riga senza entrare nelle funzioni
# o  (Step Out)     — esce dalla funzione corrente
# c  (Continue)     — continua fino al prossimo breakpoint
# q  (Quit)         — interrompe il debugging
# k  (Stack Trace)  — mostra lo stack delle chiamate
# l  (List)         — mostra il codice circostante
# $variabile        — ispeziona qualsiasi variabile
```

### Debugging in VS Code

```jsonc
// .vscode/launch.json per debug PowerShell
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "PowerShell: Launch Script",
            "type": "PowerShell",
            "request": "launch",
            "script": "${workspaceFolder}/Scripts/Deploy.ps1",
            "args": ["-ComputerName", "SRV01", "-Verbose"],
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "PowerShell: Launch Pester Tests",
            "type": "PowerShell",
            "request": "launch",
            "script": "Invoke-Pester",
            "args": ["-Path", "${workspaceFolder}/Tests/", "-Output", "Detailed"],
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "PowerShell: Attach to Process",
            "type": "PowerShell",
            "request": "attach",
            "processId": "${command:pickProcess}"
        }
    ]
}
```

### Misurare le Performance

```powershell
# Measure-Command per timing di blocchi di codice
$elapsed = Measure-Command {
    $data = Get-ADUser -Filter * -Properties Department, LastLogonDate
}
Write-Output "Query AD completata in $($elapsed.TotalSeconds)s ($($data.Count) utenti)"

# Trace-Command per diagnostica dei binding dei parametri
Trace-Command -Name ParameterBinding -Expression {
    Get-Process -Name "powershell"
} -PSHost

# Profile dello script con Measure-Script (dalla PSGallery)
# Install-Module Profiler
# Measure-Script -ScriptBlock { .\MyScript.ps1 }

# Confrontare due approcci
$results = @(
    @{ Label = "Where-Object"; Time = (Measure-Command {
        1..100000 | Where-Object { $_ % 2 -eq 0 }
    }).TotalMilliseconds }
    @{ Label = "foreach filter"; Time = (Measure-Command {
        foreach ($i in 1..100000) { if ($i % 2 -eq 0) { $i } }
    }).TotalMilliseconds }
    @{ Label = ".Where()"; Time = (Measure-Command {
        (1..100000).Where({ $_ % 2 -eq 0 })
    }).TotalMilliseconds }
)
$results | ForEach-Object { [PSCustomObject]$_ } | Sort-Object Time | Format-Table -AutoSize
```

---

## Profiling e Ottimizzazione Memoria

### Memory Profiling

```powershell
# PowerShell puo` consumare molta memoria con collection grandi,
# pipeline complesse o moduli pesanti. Profilare l'uso memoria e`
# essenziale per script che girano a lungo o processano dati massivi.

# Misurare memoria del processo PowerShell corrente
$proc = Get-Process -Id $PID
[PSCustomObject]@{
    WorkingSetMB   = [math]::Round($proc.WorkingSet64 / 1MB, 1)
    PrivateMemMB   = [math]::Round($proc.PrivateMemorySize64 / 1MB, 1)
    VirtualMemMB   = [math]::Round($proc.VirtualMemorySize64 / 1MB, 1)
    GCTotalMemMB   = [math]::Round([GC]::GetTotalMemory($false) / 1MB, 1)
    GCCollections  = @{
        Gen0 = [GC]::CollectionCount(0)
        Gen1 = [GC]::CollectionCount(1)
        Gen2 = [GC]::CollectionCount(2)
    }
}

# Pattern: monitorare memoria durante l'esecuzione
function Measure-MemoryUsage {
    param([scriptblock]$ScriptBlock)

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    $before = [GC]::GetTotalMemory($true)

    & $ScriptBlock

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    $after = [GC]::GetTotalMemory($true)

    [PSCustomObject]@{
        BeforeMB    = [math]::Round($before / 1MB, 2)
        AfterMB     = [math]::Round($after / 1MB, 2)
        DeltaMB     = [math]::Round(($after - $before) / 1MB, 2)
    }
}

# Utilizzo
Measure-MemoryUsage -ScriptBlock {
    $data = Get-ChildItem C:\Windows\System32 -Recurse -ErrorAction SilentlyContinue
}
```

### Anti-Pattern di Memoria e Soluzioni

```powershell
# ANTI-PATTERN 1: accumulare tutto in un array
# BAD — carica TUTTO in memoria
$allLogs = Get-WinEvent -LogName Security -MaxEvents 100000

# GOOD — processare in streaming con pipeline
Get-WinEvent -LogName Security -MaxEvents 100000 |
    Where-Object Id -eq 4625 |
    Select-Object TimeCreated, @{N='User';E={$_.Properties[5].Value}} |
    Export-Csv -Path ".\failed-logons.csv" -NoTypeInformation

# ANTI-PATTERN 2: += con array (O(n²) — riallocazione ad ogni append)
$results = @()
foreach ($item in $collection) {
    $results += [PSCustomObject]@{ Name = $item }   # LENTO
}

# GOOD — usare [System.Collections.Generic.List[object]]
$results = [System.Collections.Generic.List[object]]::new()
foreach ($item in $collection) {
    $results.Add([PSCustomObject]@{ Name = $item })  # O(1) amortizzato
}

# GOOD alternativo — output diretto dal foreach (streaming)
$results = foreach ($item in $collection) {
    [PSCustomObject]@{ Name = $item }   # Stream output
}

# ANTI-PATTERN 3: non liberare risorse
# BAD — StreamReader resta aperto
$reader = [System.IO.StreamReader]::new("C:\big-file.log")
$content = $reader.ReadToEnd()
# Dimentica $reader.Dispose()

# GOOD — usare try/finally o using statement (PS7+)
# PS7+:
$content = & { using ($reader = [System.IO.StreamReader]::new("C:\big-file.log")) {
    $reader.ReadToEnd()
}}

# PS5.1:
try {
    $reader = [System.IO.StreamReader]::new("C:\big-file.log")
    $content = $reader.ReadToEnd()
}
finally {
    if ($reader) { $reader.Dispose() }
}

# ANTI-PATTERN 4: Import-Csv su file enormi
# BAD — carica tutto in memoria
$csv = Import-Csv "C:\data\10million-rows.csv"

# GOOD — streaming con .NET StreamReader + parsing manuale
$reader = [System.IO.StreamReader]::new("C:\data\10million-rows.csv")
$header = $reader.ReadLine() -split ','
$count = 0
while ($null -ne ($line = $reader.ReadLine())) {
    $fields = $line -split ','
    # Processare riga per riga
    $count++
}
$reader.Dispose()
Write-Host "Processate $count righe"
```

### Garbage Collection Tuning

```powershell
# Forzare garbage collection (utile in loop lunghi)
# Non chiamare troppo frequentemente — il GC di .NET e` gia` ottimizzato
[GC]::Collect()
[GC]::WaitForPendingFinalizers()

# In PS7+, verificare se Server GC e` abilitato
# (migliore per workload con alta allocazione)
[System.Runtime.GCSettings]::IsServerGC
# true → Server GC (ottimizzato per throughput, usa piu` memoria)
# false → Workstation GC (ottimizzato per latenza)

# Per abilitare Server GC in PS7, creare/modificare
# $PSHOME/powershell.runtimeconfig.json:
# {
#   "runtimeOptions": {
#     "configProperties": {
#       "System.GC.Server": true
#     }
#   }
# }

# Monitorare GC in tempo reale con dotnet-counters (richiede .NET SDK)
# dotnet-counters monitor --process-id $PID --counters System.Runtime
# Mostra: gc-heap-size, gen-0/1/2-gc-count, alloc-rate, ecc.
```

---

## Script Packaging e Distribuzione

### platyPS — Documentazione Automatica

platyPS genera help basato su Markdown per i moduli PowerShell, mantenendo lo standard MAML.

```powershell
# Installare platyPS
Install-Module platyPS -Force

# Generare la documentazione Markdown da un modulo
Import-Module ServerTools
New-MarkdownHelp -Module ServerTools -OutputFolder ".\docs\help" -WithModulePage

# La struttura generata:
# docs\help\
# ├── ServerTools.md           # Pagina del modulo
# ├── Get-ServerStatus.md      # Help per ogni funzione esportata
# ├── Set-ServerConfig.md
# └── Invoke-ServerAudit.md

# Aggiornare la documentazione dopo modifiche al codice
Update-MarkdownHelp -Path ".\docs\help"

# Generare il file MAML XML per Get-Help
New-ExternalHelp -Path ".\docs\help" -OutputPath ".\ServerTools\en-US"

# Dopo la generazione, Get-Help funziona:
# Get-Help Get-ServerStatus -Full
```

### PSScriptAnalyzer Custom Rules

```powershell
# Regola personalizzata PSScriptAnalyzer
# File: CustomRules.psm1
function Measure-NoWriteHostInModules {
    [CmdletBinding()]
    [OutputType([Microsoft.Windows.PowerShell.ScriptAnalyzer.Generic.DiagnosticRecord[]])]
    param(
        [Parameter(Mandatory)]
        [System.Management.Automation.Language.ScriptBlockAst]$ScriptBlockAst
    )

    $results = @()
    $commands = $ScriptBlockAst.FindAll({
        param($ast)
        $ast -is [System.Management.Automation.Language.CommandAst] -and
        $ast.CommandElements[0].Value -eq 'Write-Host'
    }, $true)

    foreach ($cmd in $commands) {
        $results += [Microsoft.Windows.PowerShell.ScriptAnalyzer.Generic.DiagnosticRecord]@{
            Message  = "Evitare Write-Host nei moduli. Usare Write-Output, Write-Verbose o Write-Information."
            Extent   = $cmd.Extent
            RuleName = "NoWriteHostInModules"
            Severity = "Warning"
        }
    }
    return $results
}
Export-ModuleMember -Function Measure-*

# Usare la regola personalizzata
Invoke-ScriptAnalyzer -Path ".\ServerTools\" -CustomRulePath ".\CustomRules.psm1" -Recurse
```

### Script come Tool Standalone

```powershell
# Pattern per script distribuibili come file singolo con help integrato

<#
.SYNOPSIS
    Verifica lo stato di salute di un'infrastruttura Windows.

.DESCRIPTION
    Esegue controlli su: connettività, servizi, spazio disco, certificati in scadenza,
    Windows Update pending, e ultimo reboot. Genera un report in formato CSV o HTML.

.PARAMETER ComputerName
    Uno o più nomi di computer da verificare. Accetta pipeline.

.PARAMETER OutputFormat
    Formato del report: CSV, HTML, o Console. Default: Console.

.PARAMETER OutputPath
    Percorso del file di output. Richiesto per CSV e HTML.

.EXAMPLE
    .\Invoke-HealthCheck.ps1 -ComputerName "SRV01","SRV02" -OutputFormat HTML -OutputPath "C:\Reports\health.html"

.EXAMPLE
    Get-ADComputer -Filter * | .\Invoke-HealthCheck.ps1 -OutputFormat CSV -OutputPath "C:\Reports\health.csv"

.NOTES
    Versione: 2.0.0
    Richiede: PowerShell 5.1+, credenziali di amministratore sui target

.LINK
    https://github.com/contoso/infra-tools
#>

#Requires -Version 5.1
#Requires -Modules @{ ModuleName='Microsoft.PowerShell.SecretManagement'; ModuleVersion='1.1.0' }
#Requires -RunAsAdministrator

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
    [Alias("CN", "Name")]
    [string[]]$ComputerName,

    [ValidateSet("CSV", "HTML", "Console")]
    [string]$OutputFormat = "Console",

    [string]$OutputPath
)

begin {
    if ($OutputFormat -ne "Console" -and -not $OutputPath) {
        throw "Il parametro -OutputPath è richiesto per il formato $OutputFormat"
    }
}

process {
    # ... implementazione ...
}
```

---

## Riferimenti

- Microsoft Docs: PowerShell Documentation — https://learn.microsoft.com/en-us/powershell/
- PowerShell Style Guide — https://poshcode.gitbook.io/powershell-practice-and-style/
- Pester Documentation — https://pester.dev/docs/quick-start
- PSScriptAnalyzer Rules — https://learn.microsoft.com/en-us/powershell/utility-modules/psscriptanalyzer/rules/readme
- PowerShell Gallery — https://www.powershellgallery.com/
- .NET Regular Expressions — https://learn.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-language-quick-reference
- PowerShell RFC Repository — https://github.com/PowerShell/PowerShell-RFC

---

## Esercizi

### Esercizio 1: Modulo di Inventario Server

Creare un modulo PowerShell `ServerInventory` che:

1. Abbia la struttura corretta (`.psd1`, `.psm1`, cartelle `Public/`, `Private/`, `Tests/`).
2. Esponga le funzioni: `Get-ServerInventory`, `Test-ServerHealth`, `Export-InventoryReport`.
3. `Get-ServerInventory` accetti `-ComputerName` con `ValueFromPipeline` e `ValueFromPipelineByPropertyName`, esegua query WMI/CIM per raccogliere: hostname, OS, CPU, RAM, spazio disco, ultimo reboot, servizi critici.
4. `Test-ServerHealth` verifichi: ping, spazio disco > 10%, certificati in scadenza entro 30 giorni, Windows Update pending.
5. `Export-InventoryReport` generi output in CSV, HTML o JSON in base al parametro `-Format`.
6. Tutte le funzioni supportino `-Verbose` e `-ErrorAction`.
7. Il manifest dichiari `CompatiblePSEditions = @('Desktop','Core')`.

**Criteri di validazione**: `Test-ModuleManifest` senza errori. `Invoke-ScriptAnalyzer` senza severity Error. Almeno 5 test Pester con coverage >= 80% sulle funzioni pubbliche.

### Esercizio 2: JEA Endpoint per Operatori DNS

Configurare un endpoint JEA che:

1. Permetta agli operatori DNS (gruppo `DNS-Operators`) di: visualizzare zone DNS, aggiungere record A e CNAME, ma solo nella zona `test.contoso.com`.
2. Permetta al gruppo `DNS-ReadOnly` di: visualizzare zone e record, ma non modificare nulla.
3. Esegua come virtual account (nessuna password da gestire).
4. Registri tutti i comandi eseguiti in transcript.
5. Blocchi l'accesso a tutti i comandi non esplicitamente autorizzati.

**Criteri di validazione**: connettersi all'endpoint JEA e verificare che `Get-Command` restituisca solo i comandi autorizzati. Tentare un comando non autorizzato e verificare che venga bloccato. Verificare che i transcript vengano scritti.

### Esercizio 3: Pipeline di Audit con Pester

Creare una suite di test Pester (`Infrastructure.Tests.ps1`) che funzioni come audit automatizzato dell'infrastruttura:

1. Verificare che i servizi critici (DNS, AD DS, DFSR) siano in esecuzione su una lista di server.
2. Verificare che lo spazio disco libero sia > 15% su tutti i volumi di tutti i server.
3. Verificare che le policy di sicurezza (password policy, lockout policy) corrispondano ai valori attesi.
4. Verificare che i certificati SSL dei server web non scadano entro 60 giorni.
5. Verificare che PSRemoting sia funzionante su tutti i server della lista.
6. Generare il report in formato NUnit XML per integrazione con CI/CD.

**Criteri di validazione**: i test devono usare `BeforeAll` per stabilire le connessioni remote una sola volta. Devono usare `TestCases` per iterare sulla lista server. Devono gestire server non raggiungibili senza bloccare i test successivi.

### Esercizio 4: Script Cross-Platform con Secret Management

Creare uno script `Sync-CloudConfig.ps1` che:

1. Funzioni sia su PowerShell 7 (Windows/Linux) che su Windows PowerShell 5.1.
2. Utilizzi `SecretManagement` per recuperare le credenziali API (non hardcoded).
3. Si connetta a un'API REST, scarichi la configurazione corrente, la confronti con una configurazione locale, e applichi le differenze.
4. Implementi retry con backoff esponenziale (3 tentativi, 2s/4s/8s).
5. Supporti `-WhatIf` per mostrare le modifiche senza applicarle.
6. Registri ogni operazione con logging strutturato (JSON) su file.
7. Gestisca il rate-limiting dell'API (header `Retry-After`).

**Criteri di validazione**: lo script deve passare `Invoke-ScriptAnalyzer` senza warning di severity Error o Warning. Deve funzionare con `$ErrorActionPreference = 'Stop'`. Deve includere comment-based help completo.

---

## Auto-valutazione

### Domanda 1

Qual è la differenza tra un errore terminante e un errore non-terminante in PowerShell? Come si rende catturabile con `try/catch` un errore non-terminante?

<details>
<summary>Risposta</summary>

Un errore **terminante** interrompe l'esecuzione del comando e dello scope corrente. È generato da: `throw`, eccezioni .NET non gestite, e cmdlet invocati con `-ErrorAction Stop`. Un errore **non-terminante** viene scritto nello stream di errore ma l'esecuzione del cmdlet continua con gli oggetti successivi — questo è il comportamento predefinito della maggior parte dei cmdlet.

Il blocco `try/catch` cattura **solo** errori terminanti. Per rendere catturabile un errore non-terminante, si deve aggiungere `-ErrorAction Stop` al cmdlet che lo genera:

```powershell
try {
    Get-Service -ComputerName "OFFLINE" -ErrorAction Stop
} catch {
    # Ora l'errore è catturabile
}
```

In alternativa, `$ErrorActionPreference = 'Stop'` rende terminanti tutti gli errori non-terminanti nella sessione, ma è una pratica rischiosa perché può causare terminazioni inattese su errori innocui.

Riferimento: Microsoft Learn, about_Try_Catch_Finally. Consultato: 2026-05-23.
</details>

### Domanda 2

Spiegare il problema del "double-hop" in PSRemoting. Quali sono le tre soluzioni principali e qual è la più sicura?

<details>
<summary>Risposta</summary>

Il double-hop si verifica quando un client si connette a un server remoto (primo hop) e da lì tenta di accedere a un terzo sistema (secondo hop). Le credenziali Kerberos non vengono delegate automaticamente al secondo hop per ragioni di sicurezza (protezione contro il furto di credenziali).

Le tre soluzioni principali sono:

1. **Resource-Based Constrained Delegation (RBCD)** — La più sicura. Configurata sul server destinazione (SRV02) per specificare quali computer possono delegare credenziali ad esso. Richiede Windows Server 2012+. Non richiede privilegi di Domain Admin per la configurazione.

2. **Kerberos Constrained Delegation (KCD)** — Sicura ma richiede configurazione in AD con privilegi elevati. Il server intermedio (SRV01) viene autorizzato a delegare credenziali solo per servizi specifici su server specifici.

3. **CredSSP** — La meno sicura. Le credenziali complete vengono inviate al server intermedio, dove potrebbero essere rubate se il server è compromesso. Utile come soluzione rapida in ambienti fidati, ma da evitare in produzione.

RBCD è la soluzione raccomandata perché: non richiede privilegi Domain Admin, è configurata sul server destinazione (principio del minimo privilegio), e non espone le credenziali sul server intermedio.

Riferimento: Microsoft Learn, Making the second hop in PowerShell Remoting. Consultato: 2026-05-23.
</details>

### Domanda 3

Perché `$results += $item` in un loop è un anti-pattern? Quale alternativa offre prestazioni migliori?

<details>
<summary>Risposta</summary>

In PowerShell, gli array sono immutabili. L'operatore `+=` non aggiunge un elemento all'array esistente: crea un **nuovo array** con dimensione N+1, copia tutti gli N elementi esistenti, e aggiunge il nuovo elemento. Questo produce una complessità temporale O(n²) per l'intero loop.

Con 100.000 elementi, `+=` è circa 100-1000 volte più lento di un `List<T>`.

Alternative performanti:

```powershell
# 1. List<T> — la più versatile, O(1) ammortizzato per Add()
$results = [System.Collections.Generic.List[PSCustomObject]]::new()
foreach ($item in $data) {
    $results.Add([PSCustomObject]@{ Name = $item })
}

# 2. Assegnazione diretta dall'output del loop — idiomatica PowerShell
$results = foreach ($item in $data) {
    [PSCustomObject]@{ Name = $item }
}

# 3. ConcurrentBag<T> per scenari multi-thread
$bag = [System.Collections.Concurrent.ConcurrentBag[PSCustomObject]]::new()
```

Riferimento: PowerShell Performance Best Practices, Microsoft Learn. Consultato: 2026-05-23.
</details>

### Domanda 4

Che cos'è il Constrained Language Mode (CLM) in PowerShell? Quando si attiva automaticamente e cosa blocca?

<details>
<summary>Risposta</summary>

Constrained Language Mode (CLM) è una modalità di sicurezza di PowerShell che limita le funzionalità del linguaggio per prevenire l'esecuzione di codice potenzialmente dannoso. In CLM sono bloccati:

- Accesso diretto ai tipi .NET (`[System.IO.File]::ReadAllText()`)
- Creazione di oggetti COM (`New-Object -ComObject`)
- `Add-Type` (compilazione C# inline)
- Accesso a proprietà del runtime host (`$host.UI.RawUI`)
- Conversioni di tipo arbitrarie
- Utilizzo di `Invoke-Expression` con contenuto non attendibile

CLM si attiva automaticamente quando:
- **AppLocker** è configurato in modalità Enforce (non Audit) con regole per script
- **WDAC (Windows Defender Application Control)** ha una policy attiva
- **Device Guard** è abilitato
- Uno script non è firmato o non è nell'elenco dei file attendibili

La verifica della modalità corrente si fa con: `$ExecutionContext.SessionState.LanguageMode`.

Gli script firmati da un certificato attendibile secondo la policy WDAC/AppLocker vengono eseguiti in FullLanguage mode; gli script non firmati sono relegati a CLM.

Riferimento: Microsoft Learn, about_Language_Modes. Consultato: 2026-05-23.
</details>

### Domanda 5

Qual è la differenza tra `begin`, `process` e `end` in una funzione avanzata PowerShell? In quale scenario è critico implementare tutti e tre?

<details>
<summary>Risposta</summary>

- **`begin`**: eseguito una sola volta prima che il primo oggetto della pipeline venga processato. Ideale per inizializzazione: apertura connessioni, creazione contatori, preparazione risorse.
- **`process`**: eseguito una volta per ogni oggetto nella pipeline. Qui si accede all'oggetto corrente tramite `$_` o tramite il parametro con `[Parameter(ValueFromPipeline)]`.
- **`end`**: eseguito una sola volta dopo che tutti gli oggetti sono stati processati. Ideale per cleanup, report finali, chiusura connessioni.

È critico implementare tutti e tre quando:

1. La funzione accetta input dalla pipeline (senza `process`, verrebbe processato solo l'ultimo oggetto).
2. Si devono inizializzare risorse costose (connessioni DB, sessioni remote) — metterle in `begin` evita di ricrearle per ogni oggetto.
3. Si deve produrre un report aggregato — i dati si accumulano in `process`, il report si genera in `end`.

```powershell
function Get-AuditReport {
    [CmdletBinding()]
    param([Parameter(ValueFromPipeline)][string]$Server)
    begin   { $conn = Connect-Database; $all = @() }
    process { $all += Invoke-Audit -Server $Server -Connection $conn }
    end     { $conn.Close(); $all | Export-Csv "report.csv" }
}
```

In PowerShell 7+ esiste anche il blocco `clean`, che viene eseguito anche se la pipeline viene interrotta (Ctrl+C), rendendolo più affidabile di `end` per il cleanup.

Riferimento: Microsoft Learn, about_Functions_Advanced_Methods. Consultato: 2026-05-23.
</details>

### Domanda 6

Come funziona AMSI (Antimalware Scan Interface) in PowerShell e perché è efficace anche contro codice offuscato?

<details>
<summary>Risposta</summary>

AMSI è un'interfaccia Windows che permette alle applicazioni di sottoporre contenuto al motore antimalware registrato (tipicamente Microsoft Defender) per la scansione. In PowerShell, AMSI intercetta il contenuto degli script **dopo** che PowerShell li ha de-offuscati e prima di eseguirli.

Il flusso è:
1. L'utente esegue uno script (anche offuscato con encoding, concatenazione, variabili).
2. Il motore PowerShell effettua il parsing e la de-offuscazione del codice.
3. Il codice in chiaro viene inviato ad AMSI.
4. AMSI lo passa al motore antimalware.
5. Se il contenuto è malevolo → blocco con errore.
6. Se pulito → esecuzione.

AMSI è efficace contro l'offuscamento perché opera sullo **stadio finale** del codice, dopo che tutte le tecniche di offuscamento (base64, `Invoke-Expression`, concatenazione di stringhe, variabili di ambiente) sono state risolte dal motore PowerShell. L'antimalware vede il codice nella sua forma effettiva.

AMSI è supportato da: PowerShell 5.1+, .NET Framework 4.8+, VBScript, JScript, WMI.

Riferimento: Microsoft Learn, Antimalware Scan Interface (AMSI). Consultato: 2026-05-23.
</details>

### Domanda 7

Qual è la differenza tra `ValueFromPipeline` e `ValueFromPipelineByPropertyName`? Fornire un esempio concreto in cui il secondo è indispensabile.

<details>
<summary>Risposta</summary>

- **`ValueFromPipeline`**: l'intero oggetto dalla pipeline viene assegnato al parametro. Funziona quando il tipo dell'oggetto corrisponde al tipo del parametro (o è convertibile).
- **`ValueFromPipelineByPropertyName`**: il valore viene estratto da una proprietà dell'oggetto pipeline il cui nome corrisponde al nome del parametro (o a un alias).

Esempio concreto dove `ByPropertyName` è indispensabile:

```powershell
function Restart-ServiceOnServer {
    param(
        [Parameter(ValueFromPipelineByPropertyName)]
        [Alias("ComputerName","CN")]
        [string]$Server,

        [Parameter(ValueFromPipelineByPropertyName)]
        [Alias("Name")]
        [string]$ServiceName
    )
    process {
        Write-Output "Restart $ServiceName on $Server"
    }
}

# Input da CSV con colonne "Server" e "ServiceName"
Import-Csv "services.csv" | Restart-ServiceOnServer
# Ogni riga del CSV fornisce entrambi i valori ai parametri corrispondenti per nome
```

Con `ValueFromPipeline` si potrebbe passare solo un valore (l'intero oggetto). Con `ByPropertyName` si possono mappare automaticamente più proprietà dell'oggetto a più parametri, rendendo la funzione interoperabile con qualsiasi fonte dati che abbia le colonne/proprietà giuste.

Riferimento: Microsoft Learn, about_Functions_Advanced_Parameters. Consultato: 2026-05-23.
</details>

### Domanda 8

Spiegare la differenza tra DSC Push mode e Pull mode. In quale scenario è preferibile ciascuno?

<details>
<summary>Risposta</summary>

**Push mode**: l'amministratore avvia manualmente `Start-DscConfiguration` per inviare la configurazione MOF al target. Il LCM applica la configurazione una volta. Non c'è monitoraggio continuo della conformità a meno che non si configuri esplicitamente.

**Pull mode**: il target (LCM) contatta periodicamente un Pull Server (SMB share o servizio HTTP) per scaricare la configurazione aggiornata. Il LCM verifica la conformità ad intervalli regolari e auto-corregge le derive.

| Scenario | Modalità preferita | Motivazione |
|----------|-------------------|-------------|
| Lab, test, pochi server | Push | Semplice, nessuna infrastruttura aggiuntiva |
| Produzione, 50+ server | Pull | Scalabile, auto-correzione, conformità continua |
| Ambienti air-gapped | Push (da jump host) | Nessun server pull raggiungibile |
| Compliance-driven | Pull + ApplyAndAutoCorrect | Auto-rimediazione delle derive |
| Provisioning iniziale | Push | Il server non ha ancora la configurazione per contattare il pull server |

In pratica, molte organizzazioni usano un approccio ibrido: Push per il provisioning iniziale, Pull per il mantenimento continuo.

Nota: Microsoft sta spostando il focus verso Azure Automanage e Azure Machine Configuration (evoluzione di DSC) per scenari cloud e ibridi.

Riferimento: Microsoft Learn, Desired State Configuration overview. Consultato: 2026-05-23.
</details>

---

## Letture Primarie Consigliate

1. **Microsoft Learn: PowerShell Documentation** — Reference ufficiale completa per PowerShell 7.x e Windows PowerShell 5.1.
   https://learn.microsoft.com/en-us/powershell/
   Consultato: 2026-05-23.

2. **PowerShell Practice and Style Guide** — Guida di stile comunitaria per script PowerShell production-ready.
   https://poshcode.gitbook.io/powershell-practice-and-style/
   Consultato: 2026-05-23.

3. **Pester Documentation** — Documentazione ufficiale di Pester 5, il framework di testing per PowerShell.
   https://pester.dev/docs/quick-start
   Consultato: 2026-05-23.

4. **PSScriptAnalyzer Rules Reference** — Elenco completo delle regole di analisi statica e relative spiegazioni.
   https://learn.microsoft.com/en-us/powershell/utility-modules/psscriptanalyzer/rules/readme
   Consultato: 2026-05-23.

5. **PowerShell Gallery** — Repository ufficiale per la pubblicazione e il download di moduli e script PowerShell.
   https://www.powershellgallery.com/
   Consultato: 2026-05-23.

6. **Microsoft Learn: Desired State Configuration (DSC)** — Guida completa a DSC: configurazioni, risorse, LCM, pull server.
   https://learn.microsoft.com/en-us/powershell/dsc/overview
   Consultato: 2026-05-23.

7. **Microsoft Learn: Just Enough Administration (JEA)** — Documentazione ufficiale per JEA, role capabilities, session configurations.
   https://learn.microsoft.com/en-us/powershell/scripting/security/remoting/jea/overview
   Consultato: 2026-05-23.

8. **Microsoft Learn: SecretManagement Module** — Guida al modulo SecretManagement per la gestione sicura di segreti.
   https://learn.microsoft.com/en-us/powershell/utility-modules/secretmanagement/overview
   Consultato: 2026-05-23.

9. **PowerShell RFC Repository** — Repository delle RFC per le nuove funzionalità di PowerShell, utile per anticipare i cambiamenti futuri.
   https://github.com/PowerShell/PowerShell-RFC
   Consultato: 2026-05-23.

10. **platyPS Documentation** — Strumento per generare help MAML da Markdown per moduli PowerShell.
    https://github.com/PowerShell/platyPS
    Consultato: 2026-05-23.

11. **.NET Regular Expressions Reference** — Documentazione completa del motore regex .NET utilizzato da PowerShell.
    https://learn.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-language-quick-reference
    Consultato: 2026-05-23.

12. **Microsoft Learn: PowerShell Remoting** — Guida approfondita a PSRemoting, WinRM, SSH backend, e troubleshooting.
    https://learn.microsoft.com/en-us/powershell/scripting/security/remoting/remoting-faq
    Consultato: 2026-05-23.

---

## Collegamenti Incrociati

| File | Relazione con questo modulo |
|---|---|
| [02-powershell.md](02-powershell.md) | Prerequisito: fondamenti PowerShell, cmdlet, pipeline, variabili |
| [01-active-directory.md](01-active-directory.md) | Contesto: gestione AD con PowerShell, query LDAP, cmdlet AD |
| [05-sicurezza-windows.md](05-sicurezza-windows.md) | Approfondimento: security baseline, audit, hardening |
| [06-rete-windows.md](06-rete-windows.md) | Contesto: configurazione rete necessaria per PSRemoting |
| [19-troubleshooting.md](19-troubleshooting.md) | Metodologie generali di troubleshooting, complementare alla sezione troubleshooting di questo modulo |
| [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) | Configurazione GPO per Execution Policy, WinRM, Transcript, AMSI |
| [24-windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md) | Integrazione AMSI, WDAC, AppLocker con la sicurezza degli script |
| [14-batch-scripting.md](14-batch-scripting.md) | Confronto: migrazione da Batch a PowerShell, interoperabilità |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **AMSI** | Antimalware Scan Interface. Interfaccia Windows che permette a PowerShell di inviare il contenuto degli script al motore antimalware per la scansione prima dell'esecuzione. |
| **CLM** | Constrained Language Mode. Modalità di sicurezza PowerShell che limita l'accesso a .NET, COM e altre API potenzialmente pericolose. Attivato da AppLocker/WDAC. |
| **CmdletBinding** | Attributo che trasforma una funzione PowerShell in una "funzione avanzata", aggiungendo supporto per parametri comuni come `-Verbose`, `-Debug`, `-ErrorAction`. |
| **CredSSP** | Credential Security Support Provider. Protocollo di autenticazione che delega le credenziali al server remoto, risolvendo il double-hop ma con rischi di sicurezza. |
| **DSC** | Desired State Configuration. Framework dichiarativo PowerShell per definire e mantenere la configurazione dei sistemi. |
| **ErrorRecord** | Oggetto .NET che incapsula un errore PowerShell, contenente l'eccezione, la categoria, l'ID, le informazioni di invocazione e lo stack trace. |
| **JEA** | Just Enough Administration. Tecnologia PowerShell che crea endpoint remoti vincolati con comandi limitati, implementando il principio del minimo privilegio. |
| **LCM** | Local Configuration Manager. Il motore DSC presente su ogni nodo che applica, monitora e mantiene la configurazione desiderata. |
| **MOF** | Managed Object Format. Formato di file generato dalla compilazione di una configurazione DSC, utilizzato dal LCM per applicare la configurazione. |
| **PSCustomObject** | Tipo PowerShell leggero per creare oggetti strutturati con proprietà personalizzate. Preferito alle hashtable per l'output di funzioni. |
| **PSGallery** | PowerShell Gallery. Repository online ufficiale per la pubblicazione e il download di moduli e script PowerShell. |
| **PSRemoting** | PowerShell Remoting. Tecnologia per l'esecuzione di comandi su computer remoti, basata su WinRM (WS-Management) o SSH. |
| **RBCD** | Resource-Based Constrained Delegation. Metodo di delega Kerberos configurato sul server di destinazione, più sicuro di KCD e CredSSP. |
| **Runspace** | Ambiente di esecuzione PowerShell isolato. I runspace pool permettono l'esecuzione parallela di script come thread nel processo corrente, con minore overhead rispetto ai PSJobs. |
| **SecretManagement** | Modulo PowerShell che fornisce un'interfaccia unificata per la gestione di segreti (password, chiavi API), con vault pluggable (SecretStore, Azure KeyVault). |
| **Splatting** | Tecnica PowerShell per passare una hashtable di parametri a un cmdlet usando l'operatore `@` al posto di `$`, migliorando la leggibilità. |
| **Steppable Pipeline** | Meccanismo avanzato che permette di controllare manualmente le fasi begin/process/end di un cmdlet, utile per il wrapping e l'intercettazione della pipeline. |
| **WinRM** | Windows Remote Management. Implementazione Microsoft del protocollo WS-Management per la gestione remota di sistemi Windows. Porta default: 5985 (HTTP), 5986 (HTTPS). |
