# PowerShell — Guida Completa

> **Modulo 02** · **Versione:** PowerShell 7.5+ · **Aggiornamento:** 2026-05-22

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [00-guida-allo-studio.md](00-guida-allo-studio.md), [14-batch-scripting.md](14-batch-scripting.md)
> **Obiettivi di apprendimento:**
> 1. Distinguere PowerShell 7+ da Windows PowerShell 5.1 e scegliere la versione corretta
> 2. Padroneggiare la triade discovery: Get-Command, Get-Help, Get-Member
> 3. Costruire pipeline object-based per trasformare e filtrare dati
> 4. Creare moduli riutilizzabili e firmati per ambienti enterprise
> 5. Automatizzare operazioni di amministrazione su Active Directory e server remoti
> **Tempo stimato:** lettura 60 min · lab 90 min
> **Livello:** competent
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida
1. **PowerShell 7+ cross-platform; Windows PowerShell 5.1 legacy.**
2. **Get-Command, Get-Help, Get-Member: triade discovery.**
3. **Pipeline object-based; differente da bash text.**
4. **Modules > script: reusable, signed.**


## Indice

- [Panoramica](#panoramica)
- [Fondamenti PowerShell](#fondamenti-powershell)
  - [Versioni e Installazione](#versioni-e-installazione)
  - [Pipeline e Oggetti](#pipeline-e-oggetti)
  - [Providers e PSDrives](#providers-e-psdrives)
  - [Navigazione e Help](#navigazione-e-help)
  - [Alias e Profilo](#alias-e-profilo)
- [Cmdlet Deep Dive](#cmdlet-deep-dive)
  - [Get-Help](#get-help)
  - [Get-Command](#get-command)
  - [Get-Member](#get-member)
  - [Where-Object](#where-object)
  - [Select-Object](#select-object)
  - [ForEach-Object](#foreach-object)
  - [Sort-Object](#sort-object)
  - [Group-Object](#group-object)
  - [Measure-Object](#measure-object)
  - [Formattazione Output](#formattazione-output)
- [Variabili e Tipi di Dati](#variabili-e-tipi-di-dati)
  - [Variabili](#variabili)
  - [Stringhe](#stringhe)
  - [Array](#array)
  - [Hashtable](#hashtable)
  - [Oggetti Personalizzati](#oggetti-personalizzati)
  - [Type Accelerators](#type-accelerators)
- [Flusso di Controllo](#flusso-di-controllo)
  - [If / Elseif / Else](#if--elseif--else)
  - [Switch](#switch)
  - [For](#for)
  - [Foreach](#foreach)
  - [While e Do-While](#while-e-do-while)
  - [Break e Continue](#break-e-continue)
  - [Operatori Ternari e Null-Coalescing](#operatori-ternari-e-null-coalescing)
- [Funzioni](#funzioni)
  - [Funzioni Base](#funzioni-base)
  - [Parametri Avanzati](#parametri-avanzati)
  - [Begin / Process / End](#begin--process--end)
  - [Advanced Functions e CmdletBinding](#advanced-functions-e-cmdletbinding)
  - [Splatting](#splatting)
- [Moduli](#moduli)
  - [Creare un Modulo](#creare-un-modulo)
  - [Module Manifest](#module-manifest)
  - [PSGallery e Repository Privati](#psgallery-e-repository-privati)
- [Gestione Errori](#gestione-errori)
  - [Try / Catch / Finally](#try--catch--finally)
  - [Errori Terminanti vs Non-Terminanti](#errori-terminanti-vs-non-terminanti)
  - [ErrorActionPreference e ErrorAction](#erroractionpreference-e-erroraction)
  - [Variabile $Error e ErrorVariable](#variabile-error-e-errorvariable)
  - [Trap](#trap)
  - [Validazione Parametri](#validazione-parametri)
- [File e Elaborazione Testo](#file-e-elaborazione-testo)
  - [Get-Content e Set-Content](#get-content-e-set-content)
  - [Import / Export CSV](#import--export-csv)
  - [JSON](#json)
  - [XML](#xml)
  - [Regex e Pattern Matching](#regex-e-pattern-matching)
  - [Select-String](#select-string)
- [Gestione Registry](#gestione-registry)
- [WMI e CIM](#wmi-e-cim)
- [PowerShell Remoting](#powershell-remoting)
  - [Configurazione WinRM](#configurazione-winrm)
  - [Sessioni Remote](#sessioni-remote)
  - [Just Enough Administration (JEA)](#just-enough-administration-jea)
- [DSC — Desired State Configuration](#dsc--desired-state-configuration)
  - [Risorse DSC](#risorse-dsc)
  - [Push vs Pull Mode](#push-vs-pull-mode)
  - [Local Configuration Manager (LCM)](#local-configuration-manager-lcm)
- [PowerShell per Active Directory](#powershell-per-active-directory)
  - [Gestione Utenti](#gestione-utenti)
  - [Gestione Gruppi](#gestione-gruppi)
  - [Gestione Computer](#gestione-computer)
  - [Gestione OU](#gestione-ou)
  - [GPO e Replica](#gpo-e-replica)
  - [Audit e Account Lockout](#audit-e-account-lockout)
- [PowerShell per Exchange](#powershell-per-exchange)
- [PowerShell per Azure](#powershell-per-azure)
- [PowerShell per Microsoft 365](#powershell-per-microsoft-365)
- [Sicurezza PowerShell](#sicurezza-powershell)
  - [Execution Policy in Dettaglio](#execution-policy-in-dettaglio)
  - [Firma degli Script](#firma-degli-script)
  - [AMSI — Antimalware Scan Interface](#amsi--antimalware-scan-interface)
  - [Constrained Language Mode](#constrained-language-mode)
  - [Logging e Auditing](#logging-e-auditing)
- [Performance e Ottimizzazione](#performance-e-ottimizzazione)
  - [Measure-Command](#measure-command)
  - [Esecuzione Parallela](#esecuzione-parallela)
  - [Jobs](#jobs)
  - [Runspaces](#runspaces)
  - [Tecniche di Ottimizzazione](#tecniche-di-ottimizzazione)
- [Moduli Utili e Gallery](#moduli-utili-e-gallery)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Script Pratici](#script-pratici)

---

## Panoramica

PowerShell è la shell e il linguaggio di scripting Microsoft, basato su oggetti .NET. A differenza delle shell tradizionali basate su testo, PowerShell passa oggetti attraverso la pipeline, consentendo manipolazioni dati precise e potenti. PowerShell 7+ (cross-platform, basato su .NET 6+) è il futuro, ma Windows PowerShell 5.1 (basato su .NET Framework) rimane installato di default su Windows e necessario per alcuni moduli.

### Differenze chiave tra PowerShell 7+ e Windows PowerShell 5.1

| Aspetto | Windows PowerShell 5.1 | PowerShell 7+ |
|---------|------------------------|---------------|
| Runtime | .NET Framework 4.x | .NET 6/7/8/9 |
| Eseguibile | `powershell.exe` | `pwsh.exe` |
| Cross-platform | No (solo Windows) | Sì (Windows, Linux, macOS) |
| Pipeline parallelismo | No nativo | `ForEach-Object -Parallel` |
| Ternary operator | No | `$x ? "sì" : "no"` |
| Null-coalescing | No | `$x ?? "default"` |
| Pipeline chain | No | `cmd1 && cmd2`, `cmd1 || cmd2` |
| SSH remoting | No | Sì |
| Percorso configurazione | `$PSHOME` sotto System32 | `$PSHOME` sotto Program Files |
| Side-by-side | No (sostituisce 5.0) | Sì (coesiste con 5.1) |

PowerShell 7+ può coesistere con 5.1 sulla stessa macchina. Alcuni moduli Windows (RSAT, DISM) richiedono ancora 5.1 o il parametro `-UseWindowsPowerShell` per il caricamento in 7+.

---

## Fondamenti PowerShell

### Versioni e Installazione

```powershell
# Versione corrente
$PSVersionTable.PSVersion

# Windows PowerShell 5.1: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
# PowerShell 7+: C:\Program Files\PowerShell\7\pwsh.exe

# Installare PowerShell 7
winget install --id Microsoft.PowerShell --source winget

# Installare da MSI (alternativa)
# https://github.com/PowerShell/PowerShell/releases

# Verificare edizione
$PSVersionTable.PSEdition    # 'Desktop' = 5.1, 'Core' = 7+

# Execution Policy
Get-ExecutionPolicy -List
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Restricted     → Nessuno script
# AllSigned      → Solo script firmati
# RemoteSigned   → Script locali ok, remoti devono essere firmati
# Unrestricted   → Tutto (con warning)
# Bypass         → Tutto (senza warning)
```

### Pipeline e Oggetti

La pipeline è il concetto fondamentale di PowerShell. A differenza di bash dove la pipeline trasmette testo, PowerShell trasmette **oggetti .NET** completi con proprietà e metodi.

```powershell
# Ogni cmdlet restituisce oggetti, non testo
# Get-Process restituisce oggetti System.Diagnostics.Process

# L'operatore | passa oggetti al cmdlet successivo
Get-Process | Where-Object CPU -gt 10 | Sort-Object CPU -Descending

# Ogni oggetto nella pipeline ha proprietà e metodi
# $_ o $PSItem rappresenta l'oggetto corrente
Get-Service | ForEach-Object { "$($_.Name): $($_.Status)" }

# La pipeline preserva il tipo: l'output mantiene le proprietà
Get-Process notepad | Stop-Process    # Stop-Process sa fermare il processo
                                       # perché riceve un oggetto Process

# Pipeline vs variabili: stessa cosa
$procs = Get-Process
$procs | Where-Object CPU -gt 10

# equivalente a:
Get-Process | Where-Object CPU -gt 10

# Pipeline input binding: ByValue vs ByPropertyName
# ByValue:        l'oggetto intero viene passato
# ByPropertyName: PowerShell matcha proprietà → parametri per nome

# Esempio ByPropertyName: un CSV con colonna "Name" alimenta -Name
Import-Csv "servers.csv" | Get-Service    # se il CSV ha colonna "Name"

# Flusso della pipeline: un oggetto alla volta
# (non è un array che arriva tutto insieme)
1..5 | ForEach-Object {
    Write-Host "Elaboro $_"    # esce uno alla volta
    Start-Sleep -Milliseconds 200
}
```

### Providers e PSDrives

I PowerShell Providers espongono data store diversi come se fossero filesystem. Ogni provider crea uno o più PSDrive.

```powershell
# Elencare tutti i provider
Get-PSProvider

# Provider predefiniti:
# FileSystem    → C:, D:, ...
# Registry      → HKLM:, HKCU:
# Certificate   → Cert:
# Environment   → Env:
# Variable      → Variable:
# Function      → Function:
# Alias         → Alias:
# WSMan         → WSMan:

# Elencare tutti i PSDrive
Get-PSDrive

# Navigare il registry come fosse un filesystem
Set-Location HKLM:\SOFTWARE\Microsoft
Get-ChildItem                              # "ls" nelle chiavi di registro
Get-ItemProperty .                         # Leggere valori

# Navigare i certificati
Set-Location Cert:\LocalMachine\My
Get-ChildItem | Select-Object Subject, Thumbprint, NotAfter

# Variabili di ambiente come PSDrive
Get-ChildItem Env:
$env:PATH                                  # accesso diretto
$env:COMPUTERNAME

# Creare PSDrive personalizzato
New-PSDrive -Name Logs -PSProvider FileSystem -Root "C:\Logs"
Get-ChildItem Logs:\    # ora funziona come un drive

# PSDrive temporaneo (solo sessione corrente)
New-PSDrive -Name Scripts -PSProvider FileSystem -Root "\\server\scripts$"
Get-ChildItem Scripts:\

# Rimuovere PSDrive
Remove-PSDrive -Name Logs

# Navigare le funzioni disponibili
Get-ChildItem Function:
# Navigare gli alias
Get-ChildItem Alias:
```

### Navigazione e Help

```powershell
# Aggiornare help (una tantum, richiede admin)
Update-Help -Force -ErrorAction SilentlyContinue

# Salvare help offline
Save-Help -DestinationPath "\\server\PSHelp" -Module ActiveDirectory
Update-Help -SourcePath "\\server\PSHelp"

# Cercare comandi
Get-Command *service*              # Cercare per nome
Get-Command -Verb Get -Noun *DNS*  # Per verbo e nome
Get-Command -Module ActiveDirectory # Per modulo
Get-Command -Type Cmdlet           # Solo cmdlet (no funzioni/alias)
Get-Command -ParameterType [string] # Comandi che accettano stringhe

# Help
Get-Help Get-Process               # Sommario
Get-Help Get-Process -Detailed     # Con parametri e esempi
Get-Help Get-Process -Examples     # Solo esempi
Get-Help Get-Process -Full         # Completo con note tecniche
Get-Help Get-Process -Online       # Apre documentazione web
Get-Help Get-Process -ShowWindow   # Finestra GUI con ricerca
Get-Help about_*                   # Articoli concettuali
Get-Help about_Operators           # Tutti gli operatori
Get-Help about_Comparison_Operators
Get-Help about_Regular_Expressions

# Scoprire proprietà e metodi di un oggetto
Get-Process | Get-Member                    # Tutti i membri
Get-Process | Get-Member -MemberType Property  # Solo proprietà
Get-Process | Get-Member -MemberType Method    # Solo metodi
"stringa" | Get-Member                      # Metodi disponibili per stringhe
@(1,2,3) | Get-Member                       # Membri di un array (attenzione: mostra Int32)
,@(1,2,3) | Get-Member                      # Forzare: mostra Object[]

# Navigazione filesystem
Get-ChildItem -Path C:\Users -Recurse -Depth 2   # ls ricorsivo con profondità
Get-ChildItem -Path C:\ -Filter "*.log" -Recurse # Cercare file per estensione
Get-ChildItem -Path . -Hidden                      # File nascosti
Get-ChildItem -Path . -Force                       # Tutti (inclusi nascosti e sistema)
Get-Item -Path "C:\Windows\System32\drivers\etc\hosts"  # Singolo file
Test-Path "C:\temp"                                 # Esiste?
Test-Path "C:\temp" -PathType Container             # È una directory?
Test-Path "C:\temp\file.txt" -PathType Leaf         # È un file?
```

### Alias e Profilo

```powershell
# Alias comuni
Get-Alias                          # Lista tutti
Get-Alias -Name ls                 # Cosa fa 'ls'?
Get-Alias -Definition Get-ChildItem # Quali alias puntano a Get-ChildItem?
Set-Alias -Name np -Value notepad  # Creare alias
New-Alias -Name gh -Value Get-Help # Alternativa
Remove-Item Alias:\np              # Rimuovere alias

# Alias predefiniti notevoli:
# ls, dir, gci   → Get-ChildItem
# cd, sl, chdir  → Set-Location
# cat, type, gc  → Get-Content
# cp, copy       → Copy-Item
# mv, move       → Move-Item
# rm, del, rmdir → Remove-Item
# cls, clear     → Clear-Host
# ps, gps        → Get-Process
# kill           → Stop-Process
# %              → ForEach-Object
# ?              → Where-Object
# select         → Select-Object
# sort           → Sort-Object
# group          → Group-Object
# measure        → Measure-Object

# IMPORTANTE: negli script usare sempre il nome completo, mai alias
# Gli alias sono per la console interattiva

# Profilo PowerShell (eseguito all'avvio)
$PROFILE                           # Path del profilo
$PROFILE.AllUsersAllHosts           # Profilo per tutti gli utenti, tutte le shell
$PROFILE.AllUsersCurrentHost        # Tutti gli utenti, shell corrente
$PROFILE.CurrentUserAllHosts        # Utente corrente, tutte le shell
$PROFILE.CurrentUserCurrentHost     # Utente corrente, shell corrente (default)

Test-Path $PROFILE                 # Esiste?
New-Item -Path $PROFILE -ItemType File -Force  # Creare
notepad $PROFILE                   # Editare
code $PROFILE                      # Editare con VS Code

# Esempio contenuto profilo:
# Set-Alias -Name g -Value git
# function prompt { "PS $($PWD.Path.Split('\')[-1])> " }
# Import-Module posh-git
# Import-Module Terminal-Icons
# $PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# Ricaricare profilo senza riavviare
. $PROFILE
```

---

## Cmdlet Deep Dive

### Get-Help

```powershell
# Get-Help è il sistema di documentazione integrato

# Sintassi base
Get-Help Get-Process

# Livelli di dettaglio
Get-Help Get-Process -Detailed       # Include parametri e esempi
Get-Help Get-Process -Full           # Tutto: parametri, input/output, note, link
Get-Help Get-Process -Examples       # Solo esempi pratici
Get-Help Get-Process -Parameter Name # Info su un singolo parametro
Get-Help Get-Process -Online         # Apre la pagina docs.microsoft.com

# Articoli concettuali (about_*)
Get-Help about_Operators             # Operatori
Get-Help about_Automatic_Variables   # Variabili automatiche
Get-Help about_Splatting             # Tecnica splatting
Get-Help about_Scopes                # Scope delle variabili
Get-Help about_Preference_Variables  # Variabili di preferenza
Get-Help about_Pipelines            # Pipeline in dettaglio
Get-Help about_Functions_Advanced    # Funzioni avanzate
Get-Help about_Try_Catch_Finally    # Gestione errori

# Cercare nella help
Get-Help *firewall*                  # Qualsiasi help che contiene "firewall"
Get-Help -Category Cmdlet -Name *DNS* # Solo cmdlet con DNS nel nome

# Aggiornamento help
Update-Help -Force -ErrorAction SilentlyContinue
# Specificare lingua
Update-Help -UICulture en-US -Force

# Finestra help interattiva (WPF, solo Windows)
Get-Help Get-Process -ShowWindow
```

### Get-Command

```powershell
# Get-Command scopre tutto ciò che è eseguibile

# Cercare per pattern
Get-Command *process*               # Qualsiasi comando con "process"
Get-Command -Name Get-*             # Tutti i Get-*
Get-Command -Name *-Service         # Tutti i *-Service

# Filtrare per tipo
Get-Command -Type Cmdlet            # Solo cmdlet compilati
Get-Command -Type Function          # Solo funzioni
Get-Command -Type Alias             # Solo alias
Get-Command -Type Application       # Eseguibili nativi (.exe, .bat)

# Filtrare per verbo e nome
Get-Command -Verb Get -Noun *DNS*
Get-Command -Verb Set, New, Remove -Noun *User*

# Filtrare per modulo
Get-Command -Module ActiveDirectory
Get-Command -Module Microsoft.PowerShell.Management
Get-Command -Module Az.Compute

# Filtrare per parametro
Get-Command -ParameterName ComputerName  # Comandi con -ComputerName
Get-Command -ParameterType [PSCredential] # Comandi che accettano credenziali

# Informazioni dettagliate su un comando
Get-Command Get-Process | Select-Object *
(Get-Command Get-Process).Parameters     # Parametri disponibili
(Get-Command Get-Process).ParameterSets  # Set di parametri

# Trovare la posizione di un eseguibile
Get-Command notepad | Select-Object Source    # Percorso dell'exe
Get-Command python -ErrorAction SilentlyContinue  # Verificare se installato

# Contare comandi per modulo
Get-Command | Group-Object ModuleName | Sort-Object Count -Descending | Select-Object -First 10
```

### Get-Member

```powershell
# Get-Member rivela la struttura interna degli oggetti

# Tutti i membri di un oggetto
Get-Process | Get-Member

# Filtrare per tipo di membro
Get-Process | Get-Member -MemberType Property      # Proprietà
Get-Process | Get-Member -MemberType Method         # Metodi
Get-Process | Get-Member -MemberType NoteProperty   # Proprietà aggiunte (es. da Select-Object)
Get-Process | Get-Member -MemberType AliasProperty  # Alias di proprietà
Get-Process | Get-Member -MemberType ScriptProperty # Proprietà calcolate

# Scoprire il tipo dell'oggetto
Get-Process | Get-Member | Select-Object -First 1 TypeName
(Get-Process)[0].GetType().FullName     # System.Diagnostics.Process

# Esplorare proprietà di oggetti diversi
Get-Service | Get-Member -MemberType Property
Get-Date | Get-Member -MemberType Method
[System.IO.FileInfo]::new("C:\test.txt") | Get-Member

# Metodi statici di un tipo
[math] | Get-Member -Static
[string] | Get-Member -Static
[datetime] | Get-Member -Static

# Uso pratico: scoprire cosa posso fare con un oggetto
$file = Get-Item "C:\Windows\System32\notepad.exe"
$file | Get-Member
# Ora so che ha: FullName, Length, LastWriteTime, Extension...
$file.FullName
$file.Length
$file.LastWriteTime

# Esplorare metodi
$str = "Hello World"
$str | Get-Member -MemberType Method
# Ora so che posso fare: .ToUpper(), .Split(), .Contains(), .Replace()...
```

### Where-Object

```powershell
# Where-Object (alias: ?, where) filtra oggetti nella pipeline

# Sintassi script block (classica)
Get-Service | Where-Object { $_.Status -eq "Running" }
Get-Process | Where-Object { $_.WorkingSet64 -gt 100MB }
Get-ChildItem C:\ -Recurse | Where-Object { $_.Extension -eq ".log" -and $_.Length -gt 1MB }

# Sintassi semplificata (PowerShell 3+)
Get-Service | Where-Object Status -eq "Running"
Get-Process | Where-Object CPU -gt 10
Get-ChildItem | Where-Object Length -gt 1MB

# Limitazione della sintassi semplificata: un solo confronto
# Per condizioni complesse, usare il script block

# Operatori di confronto utilizzabili
Get-Service | Where-Object { $_.DisplayName -like "*Windows*" }     # Wildcard
Get-Service | Where-Object { $_.DisplayName -match "^Windows\s" }   # Regex
Get-Process | Where-Object { $_.Name -in @("chrome", "firefox") }   # Contenuto in array
Get-ADUser -Filter * | Where-Object { $_.Enabled -eq $true }

# Confronti multipli
Get-Process | Where-Object {
    $_.CPU -gt 5 -and
    $_.WorkingSet64 -gt 50MB -and
    $_.Name -notlike "svc*"
}

# Negazione
Get-Service | Where-Object { $_.Status -ne "Running" }
Get-Process | Where-Object { $_.Name -notmatch "^(System|Idle)$" }

# Filtro su proprietà nested
Get-ChildItem -Recurse | Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) }
Get-ChildItem -Recurse | Where-Object { $_.LastWriteTime.Year -eq 2026 }

# PRESTAZIONI: preferire -Filter del cmdlet quando disponibile
# LENTO (filtra dopo aver recuperato tutto):
Get-ADUser -Filter * | Where-Object Department -eq "IT"
# VELOCE (filtra al server):
Get-ADUser -Filter 'Department -eq "IT"'
```

### Select-Object

```powershell
# Select-Object (alias: select) seleziona proprietà e sottoinsiemi

# Selezionare proprietà specifiche
Get-Process | Select-Object Name, CPU, WorkingSet64

# Primi N / ultimi N oggetti
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5
Get-EventLog -LogName System -Newest 100 | Select-Object -Last 10

# Saltare e prendere (paginazione)
Get-Process | Select-Object -Skip 5 -First 10

# Unici
Get-Process | Select-Object -ExpandProperty Name -Unique

# Proprietà calcolate (custom)
Get-Process | Select-Object Name,
    @{Name='MemoriaMB'; Expression={[math]::Round($_.WorkingSet64 / 1MB, 2)}},
    @{Name='CPUSecondi'; Expression={[math]::Round($_.CPU, 2)}}

Get-ChildItem -Recurse | Select-Object Name,
    @{N='DimensioneKB'; E={[math]::Round($_.Length / 1KB, 1)}},
    @{N='Età'; E={(Get-Date) - $_.LastWriteTime}}

# ExpandProperty: estrarre il valore di una singola proprietà come array
Get-Service | Select-Object -ExpandProperty Name           # Array di stringhe
(Get-Service | Select-Object Name).Name                    # Equivalente

# ExcludeProperty: tutto tranne
Get-Process | Select-Object * -ExcludeProperty Modules, Threads

# Differenza tra Select-Object e Format-Table:
# Select-Object: restituisce OGGETTI (utilizzabili nella pipeline)
# Format-Table:  restituisce TESTO FORMATTATO (fine pipeline, per display)
Get-Process | Select-Object Name, CPU | Export-Csv out.csv   # Funziona
# Get-Process | Format-Table Name, CPU | Export-Csv out.csv  # NON funziona bene
```

### ForEach-Object

```powershell
# ForEach-Object (alias: %, foreach) esegue un blocco per ogni oggetto

# Sintassi script block
Get-Service | ForEach-Object { $_.DisplayName.ToUpper() }

Get-ChildItem *.txt | ForEach-Object {
    $content = Get-Content $_.FullName
    "$($_.Name): $($content.Count) righe"
}

# Sintassi con nome del metodo (PowerShell 4+)
"hello", "world" | ForEach-Object ToUpper
(Get-ChildItem).FullName    # Alternativa: accesso diretto alla proprietà

# Accesso a proprietà e metodi per nome (senza script block)
Get-Process | ForEach-Object -MemberName Name          # Proprietà
"hello", "world" | ForEach-Object -MemberName ToUpper  # Metodo
1, 2, 3 | ForEach-Object -MemberName ToString -ArgumentList "X2"  # Metodo con argomenti

# Begin / Process / End blocks
Get-Service | ForEach-Object -Begin {
    $count = 0
    Write-Host "Inizio elaborazione servizi..."
} -Process {
    if ($_.Status -eq "Running") { $count++ }
} -End {
    Write-Host "Servizi in esecuzione: $count"
}

# ForEach-Object -Parallel (PowerShell 7+)
1..10 | ForEach-Object -Parallel {
    Start-Sleep -Seconds 1
    "Completato $_"
} -ThrottleLimit 5    # max 5 thread paralleli

# Usare variabili esterne in -Parallel (con $using:)
$logPath = "C:\Logs"
Get-Service | ForEach-Object -Parallel {
    $svc = $_
    "$($svc.Name): $($svc.Status)" | Out-File "$($using:logPath)\$($svc.Name).txt"
} -ThrottleLimit 10
```

### Sort-Object

```powershell
# Sort-Object (alias: sort) ordina oggetti

# Ordinamento semplice
Get-Process | Sort-Object Name                    # Ascendente (default)
Get-Process | Sort-Object CPU -Descending         # Discendente
Get-Process | Sort-Object CPU -Descending -Top 5  # Top 5 (PowerShell 7+)
Get-Process | Sort-Object CPU -Descending -Bottom 5 # Bottom 5 (PowerShell 7+)

# Ordinamento multiplo
Get-Service | Sort-Object Status, DisplayName
Get-Process | Sort-Object @{Expression='CPU'; Descending=$true},
                          @{Expression='Name'; Ascending=$true}

# Ordinamento stabile (-Stable)
# Mantiene l'ordine relativo degli elementi uguali
Get-Process | Sort-Object -Property CPU -Stable

# Ordinamento unico
Get-Process | Sort-Object Name -Unique            # Rimuove duplicati

# Ordinamento case-sensitive
"a", "B", "c", "A", "b", "C" | Sort-Object -CaseSensitive

# Ordinamento con espressione calcolata
Get-ChildItem -Recurse | Sort-Object @{
    Expression = { $_.LastWriteTime }
    Descending = $true
} | Select-Object FullName, LastWriteTime -First 20

# Ordinamento numerico di stringhe
"file10", "file2", "file1", "file20" | Sort-Object { [int]($_ -replace '\D') }
```

### Group-Object

```powershell
# Group-Object (alias: group) raggruppa oggetti per proprietà

# Raggruppamento base
Get-Service | Group-Object Status
# Output: Count, Name (valore della proprietà), Group (oggetti)

# Accedere ai gruppi
$groups = Get-Service | Group-Object Status
$groups | Where-Object Name -eq "Running" | Select-Object -ExpandProperty Group

# Convertire in hashtable (-AsHashTable)
$svcByStatus = Get-Service | Group-Object Status -AsHashTable
$svcByStatus["Running"]         # Array di servizi in esecuzione
$svcByStatus["Stopped"].Count   # Conteggio servizi fermi

# Raggruppamento con -AsString (chiavi come stringhe)
$svcByStatus = Get-Service | Group-Object Status -AsHashTable -AsString

# Raggruppamento multiplo
Get-ChildItem -Recurse -File | Group-Object Extension |
    Sort-Object Count -Descending |
    Select-Object Count, Name

# Raggruppamento con proprietà calcolata
Get-ChildItem -Recurse -File | Group-Object {
    if ($_.Length -lt 1KB) { "Tiny (<1KB)" }
    elseif ($_.Length -lt 1MB) { "Small (<1MB)" }
    elseif ($_.Length -lt 100MB) { "Medium (<100MB)" }
    else { "Large (100MB+)" }
} | Select-Object Count, Name

# Raggruppamento per data
Get-EventLog -LogName System -Newest 1000 |
    Group-Object { $_.TimeGenerated.ToString("yyyy-MM-dd") } |
    Sort-Object Name -Descending |
    Select-Object Count, Name
```

### Measure-Object

```powershell
# Measure-Object (alias: measure) calcola statistiche

# Conteggio
Get-Service | Measure-Object                      # Count
Get-ChildItem -Recurse -File | Measure-Object     # Conteggio file

# Statistiche numeriche
Get-ChildItem -Recurse -File | Measure-Object -Property Length -Sum -Average -Maximum -Minimum

# Statistiche testo (righe, parole, caratteri)
Get-Content "C:\Logs\app.log" | Measure-Object -Line -Word -Character

# Uso combinato
$stats = Get-ChildItem -Recurse -File | Measure-Object -Property Length -Sum -Average
"File: $($stats.Count), Totale: $([math]::Round($stats.Sum / 1GB, 2)) GB, Media: $([math]::Round($stats.Average / 1MB, 2)) MB"
```

### Formattazione Output

```powershell
# REGOLA D'ORO: la formattazione è sempre l'ULTIMO passo della pipeline
# Dopo Format-*, gli oggetti sono di tipo FormatEntryData e non più utilizzabili

# Format-Table (default per >4 proprietà o per la maggior parte dei cmdlet)
Get-Process | Format-Table Name, CPU, WorkingSet -AutoSize
Get-Process | Format-Table -Property Name, CPU, WorkingSet -AutoSize -Wrap

# Colonne calcolate in Format-Table
Get-Process | Format-Table Name,
    @{Label='CPU(s)'; Expression={'{0:N2}' -f $_.CPU}; Align='Right'},
    @{Label='Mem(MB)'; Expression={'{0:N0}' -f ($_.WorkingSet64/1MB)}; Align='Right'} -AutoSize

# Format-List (dettaglio, una proprietà per riga)
Get-Service -Name wuauserv | Format-List *
Get-Process | Where-Object Name -eq "explorer" | Format-List Name, Id, CPU, StartTime, Path

# Format-Wide (una sola proprietà su più colonne)
Get-Service | Format-Wide -Column 4
Get-Service | Format-Wide DisplayName -Column 3

# Format-Custom (personalizzato, basato su .format.ps1xml)
Get-Process | Format-Custom -Depth 1

# Out-GridView (GUI interattiva, solo Windows)
Get-Process | Out-GridView
Get-Service | Out-GridView -PassThru | Stop-Service   # Selezione interattiva

# Export a file
Get-Service | Export-Csv -Path "services.csv" -NoTypeInformation -Encoding UTF8
Get-Service | ConvertTo-Json | Out-File "services.json" -Encoding UTF8
Get-Service | Export-Clixml "services.xml"    # Serializzazione PowerShell completa
Get-Service | ConvertTo-Html | Out-File "services.html"

# Out-String: convertire output in stringa
$text = Get-Process | Out-String
$text = Get-Process | Format-Table | Out-String

# Tee-Object: output a schermo E a file contemporaneamente
Get-Process | Tee-Object -FilePath "processes.txt" | Where-Object CPU -gt 10

# Filtrare output con testo (ultima risorsa)
Get-Service | Out-String | Select-String "running"

# Formattazione numeri
"{0:N2}" -f 1234.5678            # 1,234.57
"{0:C2}" -f 99.5                 # €99.50 (cultura locale)
"{0:P1}" -f 0.856                # 85.6%
"{0:X}" -f 255                   # FF (esadecimale)
[math]::Round(3.14159, 2)        # 3.14
```

---

## Variabili e Tipi di Dati

### Variabili

```powershell
# Assegnazione
$name = "Mario"
$number = 42
$array = @(1, 2, 3, 4, 5)
$hash = @{ Name = "Mario"; Age = 30; City = "Milano" }

# Tipi espliciti (casting)
[string]$name = "Mario"
[int]$count = 0
[datetime]$date = Get-Date
[bool]$isAdmin = $true
[double]$pi = 3.14159
[decimal]$price = 19.99
[char]$letter = 'A'
[byte]$b = 255

# Variabili automatiche
$PSVersionTable       # Versione PowerShell
$HOME                 # Home directory
$PWD                  # Working directory corrente
$null                 # Null
$true / $false        # Booleani
$_                    # Oggetto corrente nella pipeline (alias: $PSItem)
$?                    # Success ultimo comando (bool)
$LASTEXITCODE         # Exit code ultimo programma nativo
$Error                # Array degli ultimi errori (più recente = indice 0)
$args                 # Argomenti funzione/script (non named)
$PSCmdlet             # Oggetto cmdlet corrente (in advanced functions)
$PSScriptRoot         # Directory dello script corrente
$PSCommandPath        # Percorso completo dello script corrente
$input                # Input della pipeline (in funzioni senza process block)
$Matches              # Risultati dell'ultimo -match
$Host                 # Oggetto host (console)
$PID                  # Process ID della sessione PowerShell corrente

# Scope delle variabili
$global:var = "visibile ovunque"
$script:var = "visibile nello script"
$local:var  = "visibile nel blocco corrente"
$private:var = "visibile solo nel blocco corrente, non nei figli"
$env:VAR    = "variabile di ambiente"

# Differenza tra local e private:
function Test-Scope {
    $local:x = "local"     # visibile anche nelle funzioni figlie
    $private:y = "private" # NON visibile nelle funzioni figlie
    Inner
}
function Inner { "x=$x, y=$y" }   # x=local, y=

# Variabili di preferenza importanti
$ErrorActionPreference        # Stop, Continue (default), SilentlyContinue
$VerbosePreference            # Continue (mostra), SilentlyContinue (default)
$DebugPreference              # Come sopra
$WarningPreference            # Continue (default)
$ConfirmPreference            # High, Medium, Low, None
$InformationPreference        # SilentlyContinue (default), Continue
$ProgressPreference           # Continue (default), SilentlyContinue (nasconde barre)
$PSDefaultParameterValues     # Parametri default per cmdlet

# PSDefaultParameterValues: parametri default per qualsiasi cmdlet
$PSDefaultParameterValues = @{
    'Export-Csv:NoTypeInformation' = $true
    'Export-Csv:Encoding'          = 'UTF8'
    'Out-File:Encoding'            = 'UTF8'
    'Invoke-WebRequest:UseBasicParsing' = $true
}
```

### Stringhe

```powershell
# Double quotes: espansione variabili e caratteri escape
"Ciao $name, oggi è $(Get-Date -Format 'dd/MM/yyyy')"
"Tabulazione:`tFine`nNuova riga"
"Percorso: $($env:USERPROFILE)\Documents"

# Single quotes: letterale, nessuna espansione
'Nessuna espansione: $name rimane $name'
'Nessun escape: `n rimane `n'

# Escape character: backtick (`)
"Dollaro letterale: `$name"
"Apice: `""
"Backtick: ``"
# Sequenze escape: `n (newline), `r (carriage return), `t (tab), `0 (null)

# Here-strings (multilinea) con espansione
$text = @"
Riga 1 con $name
Riga 2 con $(Get-Date)
"@

# Here-strings letterali (senza espansione)
$literal = @'
Riga 1: $name non viene espanso
Riga 2: $(Get-Date) nemmeno
'@

# Operazioni stringa
"HELLO".ToLower()                # hello
"hello".ToUpper()                # HELLO
"hello world".Split(" ")         # array: hello, world
"hello" -replace "l", "L"       # heLLo (case-insensitive)
"hello" -creplace "l", "L"      # heLLo (case-sensitive)
"hello" -match "^he"            # True, popola $Matches
"hello".Substring(0, 3)         # hel
"hello".PadLeft(10, "*")        # *****hello
"hello".PadRight(10, ".")       # hello.....
"  hello  ".Trim()              # hello
"  hello  ".TrimStart()         # "hello  "
"  hello  ".TrimEnd()           # "  hello"
"hello".Contains("ell")         # True (case-sensitive in .NET)
"hello".StartsWith("hel")       # True
"hello".EndsWith("llo")         # True
"hello".IndexOf("l")            # 2
"hello".Replace("l", "r")       # herro (.NET, case-sensitive)
"hello".Insert(5, " world")     # hello world
"hello".Remove(2, 2)            # heo (rimuove 2 char da posizione 2)

# Join e Split
[string]::Join(", ", @("a", "b", "c"))   # a, b, c
"a,b,c" -split ","                         # array: a, b, c
"a,,b" -split ",", 0, "RemoveEmptyEntries" # array: a, b
@("a", "b", "c") -join " | "              # a | b | c

# String formatting
"Il valore è {0} e il nome è {1}" -f 42, "test"
"Data: {0:yyyy-MM-dd HH:mm}" -f (Get-Date)
"Prezzo: {0:C2}" -f 19.99
"Percentuale: {0:P1}" -f 0.856
"Hex: 0x{0:X4}" -f 255

# Conversione
[int]"42"                        # 42
[datetime]"2026-01-15"           # oggetto DateTime
[version]"1.2.3"                 # oggetto Version
[guid]::NewGuid()                # GUID casuale
[uri]"https://example.com"       # oggetto Uri
```

### Array

```powershell
# Creazione array
$arr = @(1, 2, 3, 4, 5)
$arr = 1, 2, 3, 4, 5                 # Equivalente (la virgola è l'operatore)
$empty = @()                          # Array vuoto
$single = , 42                        # Array con un solo elemento
$range = 1..10                        # Range: 1 a 10
$range = 10..1                        # Range inverso

# Tipizzare un array
[int[]]$numbers = 1, 2, 3
[string[]]$names = "Mario", "Luigi"

# Accesso agli elementi
$arr[0]                              # Primo elemento
$arr[-1]                             # Ultimo elemento
$arr[1..3]                           # Slice: elementi da indice 1 a 3
$arr[-3..-1]                         # Ultimi 3 elementi
$arr[0, 2, 4]                        # Elementi specifici

# Array sono IMMUTABILI in dimensione (in realtà vengono ricreati)
$arr += 6                            # Crea un NUOVO array con l'elemento aggiunto
$arr += @(7, 8, 9)                   # Aggiungere più elementi

# Per append frequenti, usare ArrayList o List (molto più efficiente)
$list = [System.Collections.ArrayList]::new()
$list.Add("primo")      | Out-Null    # .Add() restituisce l'indice, Out-Null lo scarta
$list.Add("secondo")    | Out-Null
$list.Remove("primo")                 # Rimuovere per valore
$list.RemoveAt(0)                     # Rimuovere per indice
$list.Insert(0, "inserito")           # Inserire a posizione

# Generic List (preferita, tipizzata)
$list = [System.Collections.Generic.List[string]]::new()
$list.Add("primo")
$list.Add("secondo")
$list.Contains("primo")              # True
$list.IndexOf("secondo")             # 1

# Operazioni su array
$arr.Count                            # Lunghezza
$arr.Length                            # Equivalente
$arr -contains 3                      # True
$arr -notcontains 99                  # True
3 -in $arr                            # True
$arr | Where-Object { $_ -gt 3 }     # Filtrare
$arr | Sort-Object                    # Ordinare
$arr | Sort-Object -Descending        # Ordinare discendente
$arr | Select-Object -Unique          # Unici
$arr | ForEach-Object { $_ * 2 }     # Map

# Confronto array
$diff = Compare-Object @(1,2,3,4) @(3,4,5,6)
# => indica quale array contiene l'elemento
# <= indica nell'altro

# Array multidimensionale
$matrix = @(
    @(1, 2, 3),
    @(4, 5, 6),
    @(7, 8, 9)
)
$matrix[0][1]    # 2 (riga 0, colonna 1)

# Svuotare un array
$arr = @()
$arr.Clear()     # Per ArrayList/List
```

### Hashtable

```powershell
# Creazione hashtable
$hash = @{
    Name = "Mario"
    Age  = 30
    City = "Milano"
}

# Accesso ai valori
$hash["Name"]                        # Mario
$hash.Name                           # Mario (dot notation)
$hash["Age"]                         # 30

# Aggiungere / modificare
$hash["Email"] = "mario@test.com"    # Aggiungere
$hash.Phone = "+39 02 1234567"       # Aggiungere con dot notation
$hash["Age"] = 31                    # Modificare

# Rimuovere
$hash.Remove("Phone")

# Verifica esistenza
$hash.ContainsKey("Name")           # True
$hash.ContainsValue("Mario")        # True

# Iterare
$hash.GetEnumerator() | ForEach-Object {
    "$($_.Key) = $($_.Value)"
}
# Oppure:
foreach ($key in $hash.Keys) {
    "$key = $($hash[$key])"
}

# Conteggio
$hash.Count

# Ordered hashtable (mantiene ordine di inserimento)
$ordered = [ordered]@{
    First  = 1
    Second = 2
    Third  = 3
}
# Le hashtable normali NON garantiscono l'ordine

# Hashtable nested
$config = @{
    Database = @{
        Server   = "sql01.contoso.com"
        Name     = "AppDB"
        Port     = 1433
    }
    Logging = @{
        Level = "Info"
        Path  = "C:\Logs"
    }
}
$config.Database.Server              # sql01.contoso.com
$config["Database"]["Port"]          # 1433

# Merge di hashtable
$defaults = @{ Color = "Blue"; Size = 10; Verbose = $false }
$custom = @{ Size = 20; Font = "Arial" }
$merged = $defaults.Clone()
$custom.GetEnumerator() | ForEach-Object { $merged[$_.Key] = $_.Value }
# $merged: Color=Blue, Size=20, Verbose=False, Font=Arial

# Splatting con hashtable (vedi sezione Funzioni)
$params = @{
    Path        = "C:\Logs"
    Filter      = "*.log"
    Recurse     = $true
    ErrorAction = "SilentlyContinue"
}
Get-ChildItem @params
```

### Oggetti Personalizzati

```powershell
# PSCustomObject: il modo più comune per creare oggetti strutturati

# Metodo 1: [PSCustomObject] con hashtable (preferito)
$server = [PSCustomObject]@{
    Name     = "SRV01"
    IP       = "192.168.1.10"
    OS       = "Windows Server 2022"
    RAM_GB   = 32
    Status   = "Online"
}
$server.Name    # SRV01

# Metodo 2: New-Object con Add-Member
$server = New-Object PSObject
$server | Add-Member -MemberType NoteProperty -Name "Name" -Value "SRV01"
$server | Add-Member -MemberType NoteProperty -Name "IP" -Value "192.168.1.10"

# Metodo 3: Select-Object con proprietà calcolate (dalla pipeline)
Get-Process | Select-Object Name,
    @{N='MemMB'; E={[math]::Round($_.WorkingSet64/1MB)}},
    @{N='CPUSec'; E={[math]::Round($_.CPU, 2)}}

# Array di oggetti personalizzati
$servers = @(
    [PSCustomObject]@{ Name="SRV01"; Role="Web"; Status="Online" }
    [PSCustomObject]@{ Name="SRV02"; Role="DB"; Status="Online" }
    [PSCustomObject]@{ Name="SRV03"; Role="Web"; Status="Offline" }
)
$servers | Where-Object Role -eq "Web"
$servers | Sort-Object Status
$servers | Format-Table -AutoSize

# Aggiungere proprietà a un oggetto esistente
$server | Add-Member -MemberType NoteProperty -Name "LastCheck" -Value (Get-Date)
$server | Add-Member -MemberType ScriptMethod -Name "Ping" -Value {
    Test-Connection $this.IP -Count 1 -Quiet
}
$server.Ping()    # Esegue il metodo

# Definire una classe PowerShell (PowerShell 5+)
class ServerInfo {
    [string]$Name
    [string]$IP
    [string]$OS
    [int]$RAM_GB
    [ValidateSet("Online","Offline","Maintenance")]
    [string]$Status

    ServerInfo([string]$name, [string]$ip) {
        $this.Name = $name
        $this.IP = $ip
        $this.Status = "Online"
    }

    [bool]Ping() {
        return Test-Connection $this.IP -Count 1 -Quiet
    }

    [string]ToString() {
        return "$($this.Name) ($($this.IP)) - $($this.Status)"
    }
}

$srv = [ServerInfo]::new("SRV01", "10.0.0.1")
$srv.OS = "Windows Server 2022"
$srv.RAM_GB = 64
$srv.Ping()
```

### Type Accelerators

```powershell
# I type accelerators sono scorciatoie per i tipi .NET completi

# Acceleratori comuni
[string]        # System.String
[int]           # System.Int32
[long]          # System.Int64
[double]        # System.Double
[decimal]       # System.Decimal
[float]         # System.Single
[bool]          # System.Boolean
[byte]          # System.Byte
[char]          # System.Char
[array]         # System.Array
[hashtable]     # System.Collections.Hashtable
[psobject]      # System.Management.Automation.PSObject
[pscustomobject] # System.Management.Automation.PSObject
[datetime]      # System.DateTime
[timespan]      # System.TimeSpan
[guid]          # System.Guid
[uri]           # System.Uri
[version]       # System.Version
[regex]         # System.Text.RegularExpressions.Regex
[xml]           # System.Xml.XmlDocument
[ipaddress]     # System.Net.IPAddress
[mailaddress]   # System.Net.Mail.MailAddress
[type]          # System.Type
[void]          # System.Void
[scriptblock]   # System.Management.Automation.ScriptBlock
[switch]        # System.Management.Automation.SwitchParameter
[nullable[int]] # System.Nullable`1[System.Int32]
[math]          # System.Math
[enum]          # System.Enum

# Uso pratico
[math]::PI                                       # 3.14159265358979
[math]::Round(3.14159, 2)                        # 3.14
[math]::Max(10, 20)                              # 20
[math]::Pow(2, 10)                               # 1024
[math]::Sqrt(144)                                # 12

[datetime]::Now                                  # Data/ora corrente
[datetime]::UtcNow                               # UTC
[datetime]::ParseExact("15/01/2026", "dd/MM/yyyy", $null)

[guid]::NewGuid()                                # GUID casuale
[guid]::Empty                                    # 00000000-0000-0000-0000-000000000000

[regex]::Match("Hello World", "\w+")             # Hello
[regex]::Matches("aaa bbb ccc", "\w+")           # 3 match
[regex]::Replace("2026-01-15", "(\d{4})-(\d{2})-(\d{2})", '$3/$2/$1')

[ipaddress]::Parse("192.168.1.1")
[uri]::EscapeDataString("hello world")           # hello%20world

[System.IO.Path]::GetExtension("file.txt")       # .txt
[System.IO.Path]::GetFileNameWithoutExtension("file.txt")  # file
[System.IO.Path]::Combine("C:\Users", "mario", "Documents")
[System.Environment]::OSVersion
[System.Environment]::MachineName
[System.Environment]::UserName

# Elencare tutti i type accelerators disponibili
[psobject].Assembly.GetType("System.Management.Automation.TypeAccelerators")::Get
```

---

## Flusso di Controllo

### If / Elseif / Else

```powershell
# Struttura base
if ($value -gt 100) {
    "Grande"
} elseif ($value -gt 50) {
    "Medio"
} else {
    "Piccolo"
}

# Operatori di confronto
# -eq, -ne, -gt, -ge, -lt, -le    (case-insensitive per default)
# -ceq, -cne, -cgt, -cge, -clt, -cle  (case-sensitive)
# -ieq, -ine, -igt, -ige, -ilt, -ile  (case-insensitive esplicito)
# -like, -notlike                   (wildcard: *, ?, [])
# -match, -notmatch                (regex)
# -contains, -notcontains          (array contiene valore)
# -in, -notin                      (valore in array)
# -is, -isnot                      (type check)
# -and, -or, -not, -xor, !         (logici)
# -band, -bor, -bxor, -bnot, -shl, -shr  (bitwise)

# Esempio reale: verifica prerequisiti
$osInfo = Get-CimInstance Win32_OperatingSystem
if ($osInfo.Version -like "10.*" -and [Environment]::Is64BitOperatingSystem) {
    Write-Output "Sistema compatibile"
} elseif ($osInfo.Version -like "6.3.*") {
    Write-Warning "Windows 8.1/2012 R2: supporto limitato"
} else {
    Write-Error "Sistema non supportato: $($osInfo.Caption)"
}

# If come espressione (assegnazione condizionale)
$status = if ($service.Status -eq "Running") { "Attivo" } else { "Fermo" }

# Null check
if ($null -eq $result) { "Nessun risultato" }
# NOTA: mettere $null a sinistra per evitare confronti su array
# $result -eq $null può dare risultati inaspettati se $result è un array

# Type check
if ($obj -is [System.IO.FileInfo]) { "È un file" }
if ($obj -is [string]) { "È una stringa" }
if ($obj -isnot [array]) { "Non è un array" }
```

### Switch

```powershell
# Switch base
switch ($status) {
    "Running"  { "Il servizio è attivo" }
    "Stopped"  { "Il servizio è fermo" }
    "Paused"   { "Il servizio è in pausa" }
    default    { "Stato sconosciuto: $status" }
}

# Switch con -Wildcard
switch -Wildcard ($filename) {
    "*.txt"  { "File di testo" }
    "*.ps1"  { "Script PowerShell" }
    "*.log"  { "File di log" }
    default  { "Tipo sconosciuto" }
}

# Switch con -Regex
switch -Regex ($input) {
    "^\d+$"           { "Solo numeri" }
    "^[a-zA-Z]+$"     { "Solo lettere" }
    "^\S+@\S+\.\S+$"  { "Sembra un email" }
    default            { "Formato non riconosciuto" }
}

# Switch su array (itera su ogni elemento)
switch (1, 2, 3, 4, 5) {
    { $_ -le 2 }  { "$_ è piccolo" }
    { $_ -gt 2 }  { "$_ è grande" }
}

# Switch con script block per condizioni complesse
switch ($errorCount) {
    { $_ -eq 0 }              { "Nessun errore" }
    { $_ -ge 1 -and $_ -le 5} { "Pochi errori: $_" }
    { $_ -gt 5 }              { "Troppi errori: $_" }
}

# Switch con break (ferma la valutazione)
switch ($priority) {
    "Critical" { Handle-Critical; break }
    "High"     { Handle-High; break }
    "Medium"   { Handle-Medium; break }
    default    { Handle-Low }
}

# Switch su file (legge riga per riga)
switch -File "C:\Logs\app.log" {
    { $_ -match "ERROR" }   { "ERRORE: $_" }
    { $_ -match "WARNING" } { "AVVISO: $_" }
}

# Switch con -CaseSensitive
switch -CaseSensitive ($method) {
    "GET"  { "Lettura" }
    "POST" { "Creazione" }
    "get"  { "Questo NON matcha GET" }
}
```

### For

```powershell
# For classico
for ($i = 0; $i -lt 10; $i++) {
    Write-Output "Iterazione $i"
}

# For con step personalizzato
for ($i = 0; $i -le 100; $i += 10) {
    Write-Output "$i%"
}

# For decrescente
for ($i = 10; $i -ge 0; $i--) {
    Write-Output "Countdown: $i"
}

# For con variabili multiple
for ($i = 0, $j = 10; $i -lt $j; $i++, $j--) {
    "$i - $j"
}

# For infinito (con break)
for (;;) {
    $input = Read-Host "Inserisci comando (q per uscire)"
    if ($input -eq 'q') { break }
    Invoke-Expression $input
}
```

### Foreach

```powershell
# foreach statement (NON è ForEach-Object nella pipeline)
foreach ($file in Get-ChildItem *.txt) {
    $lineCount = (Get-Content $file.FullName | Measure-Object -Line).Lines
    "$($file.Name): $lineCount righe"
}

# Differenza tra foreach STATEMENT e ForEach-Object CMDLET:
# foreach statement: carica TUTTO in memoria, poi itera (più veloce per piccole raccolte)
# ForEach-Object:    elabora UN oggetto alla volta nella pipeline (meno memoria)

# foreach con hashtable
$config = @{ Server = "SRV01"; Port = 8080; SSL = $true }
foreach ($key in $config.Keys) {
    "$key = $($config[$key])"
}

# foreach con indice
$items = "a", "b", "c", "d"
for ($i = 0; $i -lt $items.Count; $i++) {
    "Indice $i = $($items[$i])"
}
# Alternativa con .ForEach() (metodo, PowerShell 4+)
@(1,2,3).ForEach({ $_ * 10 })    # 10, 20, 30
```

### While e Do-While

```powershell
# While: controlla PRIMA di eseguire
$count = 0
while ($count -lt 5) {
    "Count: $count"
    $count++
}

# Do-While: esegue ALMENO UNA VOLTA, poi controlla
do {
    $input = Read-Host "Inserisci un numero (0 per uscire)"
    [int]$num = $input
    if ($num -ne 0) { "Hai inserito $num" }
} while ($num -ne 0)

# Do-Until: esegue finché la condizione NON diventa vera
do {
    $response = Invoke-WebRequest -Uri "https://api.example.com/status" -UseBasicParsing
    Start-Sleep -Seconds 5
} until ($response.StatusCode -eq 200)

# While con timeout
$timeout = (Get-Date).AddMinutes(5)
while ((Get-Date) -lt $timeout) {
    $svc = Get-Service -Name "TargetService" -ErrorAction SilentlyContinue
    if ($svc.Status -eq "Running") {
        Write-Output "Servizio avviato."
        break
    }
    Write-Output "In attesa... $(Get-Date -Format 'HH:mm:ss')"
    Start-Sleep -Seconds 10
}
```

### Break e Continue

```powershell
# Break: esce dal ciclo corrente
foreach ($server in $servers) {
    $result = Test-Connection $server -Count 1 -Quiet
    if (-not $result) {
        Write-Warning "Server $server non raggiungibile. Interrompo."
        break    # esce dal foreach
    }
    Process-Server $server
}

# Continue: salta all'iterazione successiva
foreach ($file in Get-ChildItem *.log) {
    if ($file.Length -eq 0) {
        continue    # salta file vuoti
    }
    $errors = Select-String -Path $file.FullName -Pattern "ERROR"
    "$($file.Name): $($errors.Count) errori"
}

# Break con label (esce da un ciclo specifico)
:outer foreach ($server in $servers) {
    foreach ($port in 80, 443, 8080) {
        $result = Test-NetConnection $server -Port $port -WarningAction SilentlyContinue
        if (-not $result.TcpTestSucceeded) {
            Write-Warning "$server : porta $port chiusa"
            break outer    # esce dal ciclo esterno
        }
    }
}
```

### Operatori Ternari e Null-Coalescing

```powershell
# Operatore ternario (PowerShell 7+)
$result = $value -gt 10 ? "Grande" : "Piccolo"

$status = (Test-Connection $server -Count 1 -Quiet) ? "Online" : "Offline"

$label = $count -eq 1 ? "elemento" : "elementi"
"Trovati $count $label"

# Null-coalescing ?? (PowerShell 7+)
$val = $null ?? "default"           # "default" (perché $val è $null)
$val = "presente" ?? "default"      # "presente"

# Null-coalescing assignment ??= (PowerShell 7+)
$config ??= @{}                     # Assegna solo se $config è $null

# Null-conditional ?. (accesso condizionale a proprietà/metodi)
${obj}?.Method()                    # Esegue Method solo se $obj non è $null
${obj}?.Property                    # Accede a Property solo se $obj non è $null

# Pipeline chain operators (PowerShell 7+)
Get-Process notepad && Write-Output "Notepad trovato"    # && = se successo
Get-Process fakename || Write-Output "Non trovato"       # || = se fallisce
```

---

## Funzioni

### Funzioni Base

```powershell
# Funzione semplice
function Get-Greeting {
    param([string]$Name = "Mondo")
    "Ciao, $Name!"
}
Get-Greeting -Name "Mario"    # Ciao, Mario!
Get-Greeting                  # Ciao, Mondo!

# Funzione con tipo di ritorno
function Add-Numbers {
    param(
        [int]$A,
        [int]$B
    )
    return $A + $B
}
$sum = Add-Numbers -A 5 -B 3    # 8

# NOTA: in PowerShell TUTTO l'output non catturato viene restituito
function Get-Data {
    "primo output"           # questo viene restituito
    42                       # anche questo
    Write-Host "messaggio"   # questo va SOLO a schermo, non nella pipeline
    "ultimo output"          # anche questo viene restituito
}
$result = Get-Data    # $result = @("primo output", 42, "ultimo output")

# Per evitare output indesiderato
$null = Do-Something           # scarta con $null
Do-Something | Out-Null        # scarta con Out-Null (più lento)
[void](Do-Something)          # cast a void
```

### Parametri Avanzati

```powershell
function Deploy-Application {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        # Parametro obbligatorio
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$ApplicationName,

        # Validazione con set di valori permessi
        [Parameter(Mandatory = $true)]
        [ValidateSet("Development", "Staging", "Production")]
        [string]$Environment,

        # Validazione range numerico
        [ValidateRange(1, 65535)]
        [int]$Port = 8080,

        # Validazione con pattern regex
        [ValidatePattern("^v\d+\.\d+\.\d+$")]
        [string]$Version = "v1.0.0",

        # Validazione con script personalizzato
        [ValidateScript({
            if (-not (Test-Path $_)) { throw "Percorso '$_' non esiste" }
            $true
        })]
        [string]$PackagePath,

        # Validazione non nullo e non vuoto
        [ValidateNotNullOrEmpty()]
        [string]$Description,

        # Validazione lunghezza stringa
        [ValidateLength(3, 50)]
        [string]$Tag,

        # Validazione conteggio array
        [ValidateCount(1, 10)]
        [string[]]$Servers,

        # Switch (booleano senza valore)
        [switch]$Force,

        # Parametro da pipeline
        [Parameter(ValueFromPipeline = $true)]
        [string[]]$InputData,

        # Parametro da pipeline per nome proprietà
        [Parameter(ValueFromPipelineByPropertyName = $true)]
        [Alias("CN", "MachineName")]
        [string]$ComputerName,

        # Credenziali
        [System.Management.Automation.PSCredential]
        [System.Management.Automation.Credential()]
        $Credential = [System.Management.Automation.PSCredential]::Empty
    )

    # ShouldProcess: supporta -WhatIf e -Confirm
    if ($PSCmdlet.ShouldProcess($ApplicationName, "Deploy to $Environment")) {
        Write-Verbose "Deploy di $ApplicationName versione $Version su $Environment"
        # ... logica di deploy
    }
}

# Uso:
Deploy-Application -ApplicationName "MyApp" -Environment Production -Port 443 -Version "v2.1.0" -WhatIf
Deploy-Application "MyApp" "Staging" -Verbose
```

### Begin / Process / End

```powershell
# I blocchi begin/process/end controllano il comportamento pipeline

function ConvertTo-UpperCase {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$InputString
    )

    begin {
        # Eseguito UNA VOLTA, prima del primo oggetto pipeline
        Write-Verbose "Inizio elaborazione"
        $count = 0
    }

    process {
        # Eseguito PER OGNI oggetto nella pipeline
        $count++
        $InputString.ToUpper()
    }

    end {
        # Eseguito UNA VOLTA, dopo l'ultimo oggetto
        Write-Verbose "Elaborati $count elementi"
    }
}

# Uso con pipeline
"hello", "world", "test" | ConvertTo-UpperCase -Verbose
# Output: HELLO, WORLD, TEST

# Esempio reale: aggregazione nella pipeline
function Get-AverageLength {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline)]
        [string]$Line
    )
    begin   { $total = 0; $count = 0 }
    process { $total += $Line.Length; $count++ }
    end     { if ($count -gt 0) { $total / $count } else { 0 } }
}

Get-Content "C:\Logs\app.log" | Get-AverageLength

# Se non si specifica begin/process/end, tutto il codice è implicitamente nel blocco end
# Questo significa che con la pipeline, $_ non funziona senza process block
```

### Advanced Functions e CmdletBinding

```powershell
# CmdletBinding trasforma una funzione in un "cmdlet in script"
# Abilita: -Verbose, -Debug, -ErrorAction, -ErrorVariable, -OutVariable, -OutBuffer
#          -WhatIf, -Confirm (se SupportsShouldProcess)

function Get-DiskSpace {
    <#
    .SYNOPSIS
        Verifica lo spazio disco sui server specificati.
    .DESCRIPTION
        Restituisce informazioni sullo spazio disco con soglie di warning.
        Supporta pipeline input e esecuzione remota.
    .PARAMETER ComputerName
        Nome del computer. Default: localhost.
    .PARAMETER ThresholdPercent
        Percentuale minima di spazio libero per warning. Default: 20.
    .PARAMETER Credential
        Credenziali per l'accesso remoto.
    .EXAMPLE
        Get-DiskSpace -ComputerName "SRV01","SRV02" -ThresholdPercent 15
    .EXAMPLE
        "SRV01","SRV02" | Get-DiskSpace
    .EXAMPLE
        Get-DiskSpace -Verbose
    .OUTPUTS
        PSCustomObject con proprietà: Computer, Drive, SizeGB, FreeGB, FreePercent, Status
    .NOTES
        Richiede accesso WMI/CIM sui server target.
    #>
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param(
        [Parameter(Mandatory = $false, ValueFromPipeline = $true,
                   ValueFromPipelineByPropertyName = $true)]
        [Alias("CN", "Server")]
        [string[]]$ComputerName = $env:COMPUTERNAME,

        [Parameter(Mandatory = $false)]
        [ValidateRange(1, 99)]
        [int]$ThresholdPercent = 20
    )

    begin {
        Write-Verbose "Soglia warning: $ThresholdPercent%"
    }

    process {
        foreach ($computer in $ComputerName) {
            Write-Verbose "Controllo disco su $computer"
            try {
                $disks = Get-CimInstance -ClassName Win32_LogicalDisk -ComputerName $computer `
                    -Filter "DriveType=3" -ErrorAction Stop

                foreach ($disk in $disks) {
                    $freePercent = [math]::Round(($disk.FreeSpace / $disk.Size) * 100, 2)
                    [PSCustomObject]@{
                        Computer    = $computer
                        Drive       = $disk.DeviceID
                        SizeGB      = [math]::Round($disk.Size / 1GB, 2)
                        FreeGB      = [math]::Round($disk.FreeSpace / 1GB, 2)
                        FreePercent = $freePercent
                        Status      = if ($freePercent -lt $ThresholdPercent) { "WARNING" } else { "OK" }
                    }
                }
            }
            catch {
                Write-Warning "Errore connessione a $computer : $_"
            }
        }
    }

    end {
        Write-Verbose "Controllo completato"
    }
}
```

### Splatting

```powershell
# Splatting passa parametri da una hashtable usando @ invece di $
# Rende i comandi lunghi leggibili

# Senza splatting (lungo e illeggibile)
Send-MailMessage -From "admin@contoso.com" -To "user@contoso.com" -Subject "Report" -Body "Vedi allegato" -SmtpServer "smtp.contoso.com" -Port 587 -UseSsl -Credential $cred -Attachments "report.xlsx"

# Con splatting (pulito)
$mailParams = @{
    From        = "admin@contoso.com"
    To          = "user@contoso.com"
    Subject     = "Report"
    Body        = "Vedi allegato"
    SmtpServer  = "smtp.contoso.com"
    Port        = 587
    UseSsl      = $true
    Credential  = $cred
    Attachments = "report.xlsx"
}
Send-MailMessage @mailParams

# Splatting con array (parametri posizionali)
$testParams = @("192.168.1.1", 4, 64)  # Host, Count, BufferSize
Test-Connection @testParams

# Combinare splatting con parametri espliciti
$baseParams = @{
    ComputerName = "SRV01"
    ErrorAction  = "Stop"
}
Get-Service @baseParams -Name "wuauserv"

# Passare splatting a funzioni wrapper
function Invoke-SafeCommand {
    param(
        [string]$CommandName,
        [hashtable]$Parameters
    )
    try {
        & $CommandName @Parameters
    }
    catch {
        Write-Warning "Comando fallito: $_"
    }
}
Invoke-SafeCommand -CommandName "Get-Service" -Parameters @{ Name = "wuauserv" }
```

---

## Moduli

### Creare un Modulo

```powershell
# Struttura consigliata di un modulo
# MyModule/
# ├── MyModule.psd1          → Module manifest (metadati)
# ├── MyModule.psm1          → Module script (caricamento funzioni)
# ├── Public/                → Funzioni esportate (API pubblica)
# │   ├── Get-Something.ps1
# │   └── Set-Something.ps1
# ├── Private/               → Funzioni interne (helper)
# │   └── Helper.ps1
# ├── Tests/                 → Test Pester
# │   ├── Get-Something.Tests.ps1
# │   └── Set-Something.Tests.ps1
# ├── en-US/                 → Help localizzata
# │   └── MyModule-help.xml
# └── README.md

# MyModule.psm1 — dot-source tutti i file
$publicPath = Join-Path $PSScriptRoot "Public"
$privatePath = Join-Path $PSScriptRoot "Private"

$publicFunctions = @()
if (Test-Path $publicPath) {
    $publicFunctions = Get-ChildItem -Path $publicPath -Filter "*.ps1" -Recurse
    $publicFunctions | ForEach-Object { . $_.FullName }
}

if (Test-Path $privatePath) {
    Get-ChildItem -Path $privatePath -Filter "*.ps1" -Recurse |
        ForEach-Object { . $_.FullName }
}

Export-ModuleMember -Function $publicFunctions.BaseName

# Esempio Public/Get-Something.ps1
function Get-Something {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )
    # Può usare funzioni private definite in Private/
    $data = Get-InternalData -Name $Name    # funzione privata
    [PSCustomObject]@{
        Name   = $Name
        Result = $data
    }
}
```

### Module Manifest

```powershell
# Creare il manifest (.psd1)
$manifestParams = @{
    Path              = ".\MyModule\MyModule.psd1"
    RootModule        = "MyModule.psm1"
    ModuleVersion     = "1.0.0"
    GUID              = [guid]::NewGuid()
    Author            = "Renan Augusto Macena"
    CompanyName       = "Contoso"
    Copyright         = "(c) 2026. All rights reserved."
    Description       = "Modulo per la gestione dell'infrastruttura"
    PowerShellVersion = "7.0"
    FunctionsToExport = @("Get-Something", "Set-Something")
    CmdletsToExport   = @()
    VariablesToExport  = @()
    AliasesToExport    = @()
    RequiredModules    = @("ActiveDirectory")
    Tags              = @("Infrastructure", "Automation")
    ProjectUri        = "https://github.com/user/MyModule"
    LicenseUri        = "https://github.com/user/MyModule/blob/main/LICENSE"
}
New-ModuleManifest @manifestParams

# Testare il manifest
Test-ModuleManifest -Path ".\MyModule\MyModule.psd1"

# Percorsi standard per moduli
$env:PSModulePath -split [System.IO.Path]::PathSeparator
# Tipicamente:
# - $HOME\Documents\PowerShell\Modules       (utente, PS 7)
# - $HOME\Documents\WindowsPowerShell\Modules (utente, PS 5.1)
# - C:\Program Files\PowerShell\Modules       (tutti gli utenti, PS 7)
# - C:\Windows\System32\WindowsPowerShell\v1.0\Modules (sistema)

# Installare il modulo localmente
$destPath = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "PowerShell\Modules\MyModule\1.0.0"
Copy-Item -Path ".\MyModule\*" -Destination $destPath -Recurse
```

### PSGallery e Repository Privati

```powershell
# PSGallery: repository pubblico ufficiale

# Cercare moduli
Find-Module -Name *Excel*
Find-Module -Tag "ActiveDirectory" -Repository PSGallery
Find-Module -Command Get-DiskSpace

# Installare moduli
Install-Module -Name PSWindowsUpdate -Scope CurrentUser
Install-Module -Name ImportExcel -Scope CurrentUser -Force
Install-Module -Name Pester -Scope CurrentUser -SkipPublisherCheck  # per moduli pre-installati

# Gestione moduli
Get-Module -ListAvailable                         # Moduli installati (tutti)
Get-Module                                        # Moduli caricati nella sessione
Get-InstalledModule                               # Installati da PSGallery
Import-Module -Name MyModule                      # Caricare
Import-Module -Name MyModule -Force               # Ricaricare (utile durante sviluppo)
Remove-Module -Name MyModule                      # Scaricare dalla sessione
Update-Module -Name PSWindowsUpdate               # Aggiornare
Uninstall-Module -Name ModuleName                 # Rimuovere

# Pubblicare su PSGallery
# Richiede API key da https://www.powershellgallery.com/
Publish-Module -Path ".\MyModule" -NuGetApiKey $apiKey

# Repository privato (NuGet feed)
# Registrare un repository privato
Register-PSRepository -Name "InternalRepo" `
    -SourceLocation "https://nuget.contoso.com/v2" `
    -PublishLocation "https://nuget.contoso.com/v2/package" `
    -InstallationPolicy Trusted

# Registrare un repository basato su file share
Register-PSRepository -Name "FileRepo" `
    -SourceLocation "\\server\PSRepository" `
    -PublishLocation "\\server\PSRepository" `
    -InstallationPolicy Trusted

# Pubblicare su repository privato
Publish-Module -Path ".\MyModule" -Repository "InternalRepo" -NuGetApiKey $key

# Installare da repository privato
Install-Module -Name MyModule -Repository "InternalRepo"

# Gestione repository
Get-PSRepository
Set-PSRepository -Name "InternalRepo" -InstallationPolicy Trusted
Unregister-PSRepository -Name "InternalRepo"

# Usare moduli 5.1 in PowerShell 7 (compatibilità)
Import-Module ActiveDirectory -UseWindowsPowerShell
# Crea un proxy: PS 7 comunica con un processo PS 5.1 in background
```

---

## Gestione Errori

### Try / Catch / Finally

```powershell
# Struttura base
try {
    $service = Get-Service -Name "ServizioInesistente" -ErrorAction Stop
    Restart-Service $service -ErrorAction Stop
}
catch [System.ServiceProcess.ServiceCommandException] {
    Write-Error "Errore specifico del servizio: $($_.Exception.Message)"
}
catch [System.UnauthorizedAccessException] {
    Write-Error "Accesso negato: $($_.Exception.Message)"
}
catch [System.IO.IOException] {
    Write-Error "Errore I/O: $($_.Exception.Message)"
}
catch {
    # Catch generico: cattura tutto il resto
    Write-Error "Errore generico: $($_.Exception.Message)"
    Write-Error "Tipo eccezione: $($_.Exception.GetType().FullName)"
    Write-Error "Stack trace: $($_.ScriptStackTrace)"
}
finally {
    # Eseguito SEMPRE, errore o no
    # Ideale per cleanup: chiudere connessioni, rilasciare risorse
    Write-Output "Blocco finally eseguito"
    if ($connection) { $connection.Close() }
}

# Accedere ai dettagli dell'errore nel catch
try {
    Get-Item "C:\FileCheNonEsiste.txt" -ErrorAction Stop
}
catch {
    $errorRecord = $_
    $errorRecord.Exception.Message          # Messaggio
    $errorRecord.Exception.GetType().Name   # Tipo eccezione
    $errorRecord.CategoryInfo               # Categoria
    $errorRecord.FullyQualifiedErrorId      # ID errore
    $errorRecord.InvocationInfo             # Info sul comando che ha fallito
    $errorRecord.ScriptStackTrace           # Stack trace dello script
    $errorRecord.TargetObject               # Oggetto che ha causato l'errore
}

# Try/catch annidati
try {
    try {
        # Operazione rischiosa
        Remove-Item "C:\Critico\file.dat" -ErrorAction Stop
    }
    catch {
        Write-Warning "Tentativo 1 fallito, riprovo..."
        Start-Sleep -Seconds 2
        Remove-Item "C:\Critico\file.dat" -ErrorAction Stop   # Secondo tentativo
    }
}
catch {
    Write-Error "Operazione fallita definitivamente: $_"
}
```

### Errori Terminanti vs Non-Terminanti

```powershell
# ERRORI NON-TERMINANTI (default per la maggior parte dei cmdlet)
# - Vengono scritti nello stream di errore
# - Il cmdlet CONTINUA l'esecuzione
# - try/catch NON li intercetta (a meno di -ErrorAction Stop)

Get-Service -Name "fake1", "wuauserv", "fake2"
# Mostra errore per fake1, restituisce wuauserv, mostra errore per fake2

# ERRORI TERMINANTI
# Due tipi:
# 1. Eccezioni .NET (throw, metodi che lanciano eccezioni)
# 2. Errori promossi con -ErrorAction Stop

# Tipo 1: throw
function Test-Value {
    param([string]$Value)
    if ([string]::IsNullOrEmpty($Value)) {
        throw "Il valore non può essere vuoto"    # errore terminante
    }
}

# Tipo 2: promuovere errore non-terminante
Get-Service -Name "fake" -ErrorAction Stop    # ora try/catch lo intercetta

# ThrowTerminatingError (in advanced functions)
function Get-SafeItem {
    [CmdletBinding()]
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        $ex = [System.IO.FileNotFoundException]::new("File non trovato: $Path")
        $er = [System.Management.Automation.ErrorRecord]::new(
            $ex, "FileNotFound", [System.Management.Automation.ErrorCategory]::ObjectNotFound, $Path
        )
        $PSCmdlet.ThrowTerminatingError($er)
    }
    Get-Item $Path
}

# WriteError (non-terminante, in advanced functions)
function Process-Items {
    [CmdletBinding()]
    param([string[]]$Items)
    foreach ($item in $Items) {
        if ($item -eq "bad") {
            $PSCmdlet.WriteError(
                [System.Management.Automation.ErrorRecord]::new(
                    [System.Exception]::new("Elemento non valido: $item"),
                    "InvalidItem",
                    [System.Management.Automation.ErrorCategory]::InvalidArgument,
                    $item
                )
            )
            continue    # continua con il prossimo
        }
        "Elaborato: $item"
    }
}
```

### ErrorActionPreference e ErrorAction

```powershell
# -ErrorAction (per singolo cmdlet)
# Stop              → Genera errore terminante (try/catch lo intercetta)
# Continue           → Mostra errore e continua (DEFAULT)
# SilentlyContinue   → Ignora errore, non mostra nulla
# Inquire            → Chiede all'utente cosa fare
# Ignore             → Ignora completamente (nemmeno $Error lo registra)
# Suspend            → Sospende (solo in workflow)
# Break              → Entra nel debugger (PowerShell 7+)

Get-Service -Name "fake" -ErrorAction SilentlyContinue   # Nessun output errore
Get-Service -Name "fake" -ErrorAction Stop                # Terminante
Get-Service -Name "fake" -ErrorAction Ignore              # Ignorato completamente

# $ErrorActionPreference (globale, per la sessione)
$ErrorActionPreference = "Stop"            # TUTTI gli errori diventano terminanti
$ErrorActionPreference = "Continue"        # Default: mostra e continua
$ErrorActionPreference = "SilentlyContinue" # Silenzia tutti

# ATTENZIONE: impostare Stop globalmente cambia il comportamento di tutti i cmdlet
# Preferire -ErrorAction Stop sul singolo cmdlet quando possibile

# Pattern sicuro: impostare temporaneamente e ripristinare
$oldPref = $ErrorActionPreference
try {
    $ErrorActionPreference = "Stop"
    # ... operazioni dove tutti gli errori devono fermare ...
}
finally {
    $ErrorActionPreference = $oldPref
}
```

### Variabile $Error e ErrorVariable

```powershell
# $Error: array automatico degli ultimi errori (max 256 per default)
$Error[0]                     # Errore più recente
$Error[0].Exception.Message   # Messaggio
$Error.Count                  # Quanti errori registrati
$Error.Clear()                # Svuotare la lista errori

# $MaximumErrorCount: cambiare dimensione buffer
$MaximumErrorCount = 512

# -ErrorVariable: catturare errori di un singolo cmdlet
Get-Service -Name "fake1", "fake2" -ErrorAction SilentlyContinue -ErrorVariable svcErrors
if ($svcErrors) {
    Write-Warning "$($svcErrors.Count) servizi non trovati"
    $svcErrors | ForEach-Object { Write-Warning $_.Exception.Message }
}

# NOTA: il nome ErrorVariable NON ha il $
# Per appendere (non sovrascrivere), prefissare con +
Get-Service -Name "fake1" -ErrorAction SilentlyContinue -ErrorVariable +allErrors
Get-Service -Name "fake2" -ErrorAction SilentlyContinue -ErrorVariable +allErrors
$allErrors.Count    # 2

# Controllare se l'ultimo comando ha avuto successo
Get-Service -Name "wuauserv" -ErrorAction SilentlyContinue
if ($?) {
    "Comando riuscito"
} else {
    "Comando fallito"
}

# $LASTEXITCODE: exit code di programmi nativi (.exe)
ping -n 1 192.168.1.1
if ($LASTEXITCODE -eq 0) { "Host raggiungibile" } else { "Host non raggiungibile" }
```

### Trap

```powershell
# Trap: gestore errori a livello di scope (alternativa a try/catch)
# Meno usato di try/catch, ma utile in script semplici

trap {
    Write-Warning "Errore intercettato: $_"
    continue    # continua l'esecuzione dopo l'errore
    # 'break' fermerebbe lo script e propagherebbe l'errore
}

Get-Service -Name "fake" -ErrorAction Stop    # trap lo intercetta
Write-Output "Questa riga viene eseguita (grazie a continue)"

# Trap specifico per tipo
trap [System.IO.FileNotFoundException] {
    Write-Warning "File non trovato: $_"
    continue
}
trap [System.UnauthorizedAccessException] {
    Write-Error "Accesso negato: $_"
    break    # ferma lo script
}
```

### Validazione Parametri

```powershell
# Tutti gli attributi di validazione disponibili

# Valore obbligatorio
[Parameter(Mandatory)]
[string]$Name

# Non null e non vuoto
[ValidateNotNull()]
[object]$Object

[ValidateNotNullOrEmpty()]
[string]$Name

# Set di valori permessi
[ValidateSet("TCP", "UDP", "ICMP")]
[string]$Protocol

# Range numerico
[ValidateRange(1, 65535)]
[int]$Port

# Lunghezza stringa
[ValidateLength(3, 50)]
[string]$Username

# Conteggio elementi array
[ValidateCount(1, 10)]
[string[]]$Servers

# Pattern regex
[ValidatePattern("^\d{3}-\d{4}$")]
[string]$PhoneNumber

# Script di validazione personalizzato
[ValidateScript({
    if (-not (Test-Path $_)) { throw "Il percorso '$_' non esiste" }
    if (-not (Test-Path $_ -PathType Leaf)) { throw "'$_' non è un file" }
    $true
})]
[string]$FilePath

# ValidateDrive (PowerShell 6.1+)
[ValidateDrive("C", "D")]
[string]$Path    # Accetta solo percorsi su C: o D:

# ValidateUserDrive (per JEA)
[ValidateUserDrive()]
[string]$Path    # Solo percorsi nel drive User:

# ArgumentCompleter (completamento tab personalizzato)
[ArgumentCompleter({
    param($cmd, $param, $wordToComplete)
    Get-Service | Where-Object Name -like "$wordToComplete*" |
        ForEach-Object { $_.Name }
})]
[string]$ServiceName

# Combinare validazioni
[Parameter(Mandatory)]
[ValidateNotNullOrEmpty()]
[ValidateLength(3, 256)]
[ValidatePattern("^[a-zA-Z]")]
[string]$Username
```

---

## File e Elaborazione Testo

### Get-Content e Set-Content

```powershell
# Leggere un file
Get-Content -Path "C:\Logs\app.log"                    # Tutte le righe (array di stringhe)
Get-Content -Path "C:\Logs\app.log" -TotalCount 10     # Prime 10 righe
Get-Content -Path "C:\Logs\app.log" -Tail 20           # Ultime 20 righe
Get-Content -Path "C:\Logs\app.log" -Tail 10 -Wait     # Ultime 10 + follow (come tail -f)

# Leggere come singola stringa
Get-Content -Path "C:\file.txt" -Raw                   # Tutto come singola stringa

# Encoding
Get-Content -Path "C:\file.txt" -Encoding UTF8
Get-Content -Path "C:\file.txt" -Encoding ASCII
Get-Content -Path "C:\file.bin" -AsByteStream           # Lettura binaria (PS 7+)
Get-Content -Path "C:\file.bin" -Encoding Byte           # Lettura binaria (PS 5.1)

# Scrivere un file
Set-Content -Path "C:\output.txt" -Value "Contenuto del file"
Set-Content -Path "C:\output.txt" -Value $data -Encoding UTF8

# Appendere a un file
Add-Content -Path "C:\Logs\app.log" -Value "[$(Get-Date)] Messaggio"

# Out-File (alternativa con più controllo sulla formattazione)
Get-Process | Out-File -FilePath "C:\output.txt" -Encoding UTF8 -Width 200

# Confronto Set-Content vs Out-File:
# Set-Content: scrive stringhe, converte oggetti con .ToString()
# Out-File:    usa il sistema di formattazione PowerShell (come l'output a schermo)

# Sostituire contenuto in un file
(Get-Content "C:\config.ini") -replace "OldValue", "NewValue" |
    Set-Content "C:\config.ini"

# Operazioni su file
Copy-Item -Path "C:\source\file.txt" -Destination "C:\dest\"
Move-Item -Path "C:\old\file.txt" -Destination "C:\new\file.txt"
Remove-Item -Path "C:\temp\*.tmp" -Force
Rename-Item -Path "C:\old.txt" -NewName "new.txt"
New-Item -Path "C:\Logs" -ItemType Directory -Force
New-Item -Path "C:\Logs\app.log" -ItemType File -Force

# Verifica e info file
Test-Path "C:\file.txt"
$file = Get-Item "C:\Windows\notepad.exe"
$file.Length                    # Dimensione in byte
$file.CreationTime              # Data creazione
$file.LastWriteTime             # Ultima modifica
$file.LastAccessTime            # Ultimo accesso
$file.Attributes                # Attributi (ReadOnly, Hidden, etc.)

# Hash di un file
Get-FileHash -Path "C:\file.exe" -Algorithm SHA256
Get-FileHash -Path "C:\file.exe" -Algorithm MD5
```

### Import / Export CSV

```powershell
# Esportare in CSV
Get-Service | Select-Object Name, Status, StartType |
    Export-Csv -Path "C:\Data\services.csv" -NoTypeInformation -Encoding UTF8

# Importare da CSV
$services = Import-Csv -Path "C:\Data\services.csv"
$services | Where-Object Status -eq "Running"
$services[0].Name    # Accesso per proprietà

# CSV con delimitatore personalizzato
Export-Csv -Path "out.csv" -Delimiter ";" -NoTypeInformation
Import-Csv -Path "in.csv" -Delimiter ";"

# CSV con header personalizzato
Import-Csv -Path "data.csv" -Header "ID", "Nome", "Email"

# Convertire (non salvare su file)
$csv = Get-Process | Select-Object Name, CPU | ConvertTo-Csv -NoTypeInformation
$objects = $csv | ConvertFrom-Csv

# Esempio pratico: report utenti AD inattivi
Get-ADUser -Filter 'Enabled -eq $true' -Properties LastLogonDate, Department |
    Where-Object { $_.LastLogonDate -lt (Get-Date).AddDays(-90) } |
    Select-Object Name, SamAccountName, Department, LastLogonDate |
    Sort-Object LastLogonDate |
    Export-Csv "C:\Reports\InactiveUsers_$(Get-Date -Format 'yyyyMMdd').csv" `
        -NoTypeInformation -Encoding UTF8
```

### JSON

```powershell
# Convertire oggetto in JSON
$data = @{
    Name     = "Server01"
    IP       = "192.168.1.10"
    Services = @("IIS", "SQL", "DNS")
    Config   = @{
        Port    = 8080
        SSL     = $true
        Timeout = 30
    }
}
$json = $data | ConvertTo-Json -Depth 5    # -Depth per oggetti annidati (default: 2)
$json | Out-File "C:\Config\server.json" -Encoding UTF8

# Convertire JSON in oggetto
$obj = Get-Content "C:\Config\server.json" -Raw | ConvertFrom-Json
$obj.Name
$obj.Services[0]
$obj.Config.Port

# JSON compresso (una riga)
$data | ConvertTo-Json -Compress

# JSON da API REST
$response = Invoke-RestMethod -Uri "https://api.example.com/data"
# Invoke-RestMethod converte automaticamente JSON in oggetti
$response.results | Select-Object name, value

# Invoke-WebRequest (più basso livello, ritorna anche headers)
$raw = Invoke-WebRequest -Uri "https://api.example.com/data" -UseBasicParsing
$data = $raw.Content | ConvertFrom-Json
$raw.StatusCode
$raw.Headers["Content-Type"]

# Modificare JSON e riscrivere
$config = Get-Content "C:\Config\app.json" -Raw | ConvertFrom-Json
$config.Database.ConnectionTimeout = 60
$config | ConvertTo-Json -Depth 10 | Set-Content "C:\Config\app.json" -Encoding UTF8
```

### XML

```powershell
# Leggere XML
[xml]$xmlDoc = Get-Content "C:\Config\web.config"
$xmlDoc.configuration.appSettings.add | Select-Object key, value

# Accesso a nodi
$xmlDoc.SelectNodes("//add[@key='ConnectionString']")
$xmlDoc.SelectSingleNode("//connectionStrings/add").connectionString

# Creare XML
$xml = [xml]@"
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <servers>
    <server name="SRV01" role="Web" />
    <server name="SRV02" role="DB" />
  </servers>
</configuration>
"@
$xml.Save("C:\Config\servers.xml")

# Export/Import-Clixml: serializzazione PowerShell nativa
# Preserva tipi e struttura completa degli oggetti
Get-Service | Export-Clixml "C:\Backup\services.xml"
$services = Import-Clixml "C:\Backup\services.xml"

# Utile per salvare credenziali (criptate con DPAPI, legate al profilo utente)
Get-Credential | Export-Clixml "C:\Secure\cred.xml"
$cred = Import-Clixml "C:\Secure\cred.xml"    # funziona solo con lo stesso utente/macchina
```

### Regex e Pattern Matching

```powershell
# Operatore -match (case-insensitive, primo match)
"Server01-Web-Prod" -match "(\w+)-(\w+)-(\w+)"
$Matches                       # Hashtable con i gruppi
$Matches[0]                    # "Server01-Web-Prod" (match completo)
$Matches[1]                    # "Server01"
$Matches[2]                    # "Web"
$Matches[3]                    # "Prod"

# -cmatch (case-sensitive)
"Hello" -cmatch "hello"        # False

# -match con named groups
"2026-05-22" -match "(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})"
$Matches.year                  # 2026
$Matches.month                 # 05
$Matches.day                   # 22

# -replace con regex
"Phone: 02-1234-5678" -replace "\d", "X"        # Phone: XX-XXXX-XXXX
"Mario Rossi" -replace "(\w+)\s+(\w+)", '$2, $1' # Rossi, Mario

# -replace con script block (PowerShell 6+)
"hello world" -replace "\w+", { $_.Value.ToUpper() }    # HELLO WORLD

# -split con regex
"one, two,  three" -split "\s*,\s*"    # array: one, two, three
"2026-05-22T14:30:00" -split "[T:-]"   # array: 2026, 05, 22, 14, 30, 00

# Classe [regex] per operazioni avanzate
$pattern = [regex]::new("\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
$ips = $pattern.Matches("Server 192.168.1.1 e 10.0.0.1 e 172.16.0.1")
$ips | ForEach-Object { $_.Value }

# Regex comuni per sysadmin
$patterns = @{
    IPv4     = "\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    Email    = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    MAC      = "([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
    URL      = "https?://[^\s]+"
    Date_ISO = "\d{4}-\d{2}-\d{2}"
    GUID     = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
}
```

### Select-String

```powershell
# Select-String: grep di PowerShell

# Cercare in un file
Select-String -Path "C:\Logs\app.log" -Pattern "ERROR"
Select-String -Path "C:\Logs\*.log" -Pattern "ERROR" -SimpleMatch   # Stringa letterale

# Cercare ricorsivamente
Get-ChildItem -Recurse -Filter "*.log" | Select-String -Pattern "CRITICAL"

# Case-sensitive
Select-String -Path "C:\Logs\app.log" -Pattern "error" -CaseSensitive

# Contesto (righe prima e dopo)
Select-String -Path "C:\Logs\app.log" -Pattern "ERROR" -Context 3, 3
# Mostra 3 righe prima e 3 dopo ogni match

# Negazione (righe che NON contengono)
Select-String -Path "C:\Logs\app.log" -Pattern "DEBUG" -NotMatch

# Multipli pattern
Select-String -Path "C:\Logs\app.log" -Pattern "ERROR", "CRITICAL", "FATAL"

# Restituire solo il match (non la riga intera)
Select-String -Path "C:\Logs\app.log" -Pattern "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" -AllMatches |
    ForEach-Object { $_.Matches.Value } | Sort-Object -Unique

# Proprietà dell'oggetto MatchInfo
$result = Select-String -Path "C:\Logs\app.log" -Pattern "ERROR"
$result[0].Path          # Percorso file
$result[0].LineNumber    # Numero riga
$result[0].Line          # Riga completa
$result[0].Pattern       # Pattern usato
$result[0].Matches       # Oggetti Match

# Equivalente di grep -c (conteggio)
(Select-String -Path "C:\Logs\app.log" -Pattern "ERROR").Count

# Cercare in stringhe (non file)
"Hello World", "Goodbye World", "Hello PowerShell" | Select-String "Hello"
```

---

## Gestione Registry

```powershell
# Il registro Windows è accessibile come PSDrive

# Navigare il registro
Set-Location HKLM:\SOFTWARE\Microsoft
Get-ChildItem                              # Sotto-chiavi
Get-ChildItem -Recurse -Depth 1           # Ricorsivo con limite

# PSDrive di registro
# HKLM: → HKEY_LOCAL_MACHINE
# HKCU: → HKEY_CURRENT_USER

# Per accedere ad altre hive:
New-PSDrive -Name HKU -PSProvider Registry -Root HKEY_USERS
New-PSDrive -Name HKCR -PSProvider Registry -Root HKEY_CLASSES_ROOT

# Leggere valori
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion"
# Proprietà specifiche
(Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").ProductName
(Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").CurrentBuild

# Get-ItemPropertyValue (più diretto, PS 5+)
Get-ItemPropertyValue -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -Name "ProductName"

# Creare una chiave
New-Item -Path "HKCU:\SOFTWARE\MyApp" -Force

# Creare / impostare un valore
New-ItemProperty -Path "HKCU:\SOFTWARE\MyApp" -Name "Setting1" -Value "Hello" -PropertyType String
Set-ItemProperty -Path "HKCU:\SOFTWARE\MyApp" -Name "Setting1" -Value "NewValue"

# Tipi di valori di registro
# String       → REG_SZ
# ExpandString → REG_EXPAND_SZ (variabili d'ambiente espanse)
# Binary       → REG_BINARY
# DWord        → REG_DWORD (32-bit integer)
# QWord        → REG_QWORD (64-bit integer)
# MultiString  → REG_MULTI_SZ (array di stringhe)

New-ItemProperty -Path "HKCU:\SOFTWARE\MyApp" -Name "Port" -Value 8080 -PropertyType DWord
New-ItemProperty -Path "HKCU:\SOFTWARE\MyApp" -Name "Servers" -Value @("SRV01","SRV02") -PropertyType MultiString

# Rimuovere valore
Remove-ItemProperty -Path "HKCU:\SOFTWARE\MyApp" -Name "Setting1"

# Rimuovere chiave (e tutto il contenuto)
Remove-Item -Path "HKCU:\SOFTWARE\MyApp" -Recurse -Force

# Verificare esistenza
Test-Path "HKCU:\SOFTWARE\MyApp"
$null -ne (Get-ItemProperty "HKCU:\SOFTWARE\MyApp" -Name "Setting1" -ErrorAction SilentlyContinue)

# Cercare nel registro
Get-ChildItem -Path "HKLM:\SOFTWARE" -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.GetValue("DisplayName") -like "*Python*" }

# Esempio: elencare software installato
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
    Where-Object DisplayName |
    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
    Sort-Object DisplayName

# Anche per 32-bit su 64-bit
Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" |
    Where-Object DisplayName |
    Select-Object DisplayName, DisplayVersion

# Registro remoto
Invoke-Command -ComputerName SRV01 -ScriptBlock {
    Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" |
        Select-Object ProductName, CurrentBuild
}
```

---

## WMI e CIM

```powershell
# CIM (Common Information Model) è il successore moderno di WMI
# Usare Get-CimInstance al posto di Get-WmiObject (deprecato in PS 7)

# Informazioni sistema operativo
Get-CimInstance -ClassName Win32_OperatingSystem |
    Select-Object Caption, Version, BuildNumber, OSArchitecture, LastBootUpTime

# Informazioni computer
Get-CimInstance -ClassName Win32_ComputerSystem |
    Select-Object Name, Domain, Manufacturer, Model, TotalPhysicalMemory,
    @{N='MemoriaGB'; E={[math]::Round($_.TotalPhysicalMemory/1GB, 2)}}

# CPU
Get-CimInstance -ClassName Win32_Processor |
    Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed

# Dischi
Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DriveType=3" |
    Select-Object DeviceID,
    @{N='SizeGB'; E={[math]::Round($_.Size/1GB,2)}},
    @{N='FreeGB'; E={[math]::Round($_.FreeSpace/1GB,2)}},
    @{N='Free%'; E={[math]::Round($_.FreeSpace/$_.Size*100,1)}}

# Dischi fisici
Get-CimInstance -ClassName Win32_DiskDrive |
    Select-Object Model, MediaType, @{N='SizeGB'; E={[math]::Round($_.Size/1GB)}}

# Memoria RAM (moduli)
Get-CimInstance -ClassName Win32_PhysicalMemory |
    Select-Object BankLabel, @{N='CapacityGB'; E={$_.Capacity/1GB}}, Speed, Manufacturer

# Schede di rete
Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -Filter "IPEnabled=$true" |
    Select-Object Description, IPAddress, DefaultIPGateway, MACAddress, DHCPEnabled

# BIOS
Get-CimInstance -ClassName Win32_BIOS | Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate

# Servizi
Get-CimInstance -ClassName Win32_Service |
    Where-Object State -eq "Running" |
    Select-Object Name, DisplayName, StartMode, ProcessId

# Processi
Get-CimInstance -ClassName Win32_Process |
    Select-Object Name, ProcessId, WorkingSetSize, CommandLine |
    Sort-Object WorkingSetSize -Descending | Select-Object -First 10

# Uptime
$os = Get-CimInstance Win32_OperatingSystem
$uptime = (Get-Date) - $os.LastBootUpTime
"Uptime: $($uptime.Days) giorni, $($uptime.Hours) ore"

# CIM su computer remoti
$cimSession = New-CimSession -ComputerName "SRV01", "SRV02"
Get-CimInstance -ClassName Win32_OperatingSystem -CimSession $cimSession |
    Select-Object PSComputerName, Caption, LastBootUpTime
Remove-CimSession $cimSession

# CIM con protocollo DCOM (per compatibilità con vecchi sistemi)
$sessionOption = New-CimSessionOption -Protocol Dcom
$cimSession = New-CimSession -ComputerName "OldServer" -SessionOption $sessionOption

# Enumerare classi WMI/CIM disponibili
Get-CimClass -Namespace "root/cimv2" | Where-Object CimClassName -like "Win32_*" | Select-Object CimClassName
Get-CimClass -ClassName Win32_Service | Select-Object -ExpandProperty CimClassProperties | Select-Object Name, CimType

# Metodi CIM (azioni)
# Riavviare un servizio
Invoke-CimMethod -ClassName Win32_Service -Filter "Name='Spooler'" -MethodName StopService
Invoke-CimMethod -ClassName Win32_Service -Filter "Name='Spooler'" -MethodName StartService

# Creare processo remoto
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = "notepad.exe"
} -ComputerName SRV01

# Event log via CIM
Get-CimInstance -ClassName Win32_NTLogEvent -Filter "LogFile='System' AND EventType=1" -MaxCount 10 |
    Select-Object TimeGenerated, SourceName, Message
```

---

## PowerShell Remoting

### Configurazione WinRM

```powershell
# Abilitare remoting (sul server target, richiede admin)
Enable-PSRemoting -Force
# Esegue: configura WinRM, crea listener HTTP, imposta regole firewall, avvia servizio

# Verificare configurazione WinRM
winrm quickconfig
winrm get winrm/config
winrm get winrm/config/client
winrm get winrm/config/service

# Configurazione listener
Get-ChildItem WSMan:\localhost\Listener

# WinRM over HTTPS (produzione)
# 1. Installare certificato SSL sul server
# 2. Creare listener HTTPS
New-Item -Path WSMan:\localhost\Listener -Transport HTTPS `
    -Address * -CertificateThumbPrint $thumbprint -Force

# Configurare porte
Set-Item WSMan:\localhost\Service\MaxConcurrentOperationsPerUser 10
Set-Item WSMan:\localhost\Shell\MaxMemoryPerShellMB 1024

# Trusted Hosts (per ambienti non-domain)
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "192.168.10.*"
# O per server specifici:
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "server1,server2,192.168.1.10"
# Leggere
Get-Item WSMan:\localhost\Client\TrustedHosts

# SSH remoting (PowerShell 7+, cross-platform)
# 1. Installare OpenSSH Server sul target
# 2. Configurare sshd_config per il sottosistema PowerShell:
#    Subsystem powershell /usr/bin/pwsh -sshs -NoLogo -NoProfile
# 3. Connettersi
Enter-PSSession -HostName server01 -UserName admin -SSHTransport

# Firewall rules
New-NetFirewallRule -Name "WinRM-HTTPS" -DisplayName "WinRM over HTTPS" `
    -Protocol TCP -LocalPort 5986 -Direction Inbound -Action Allow
```

### Sessioni Remote

```powershell
# Sessione interattiva (1:1)
Enter-PSSession -ComputerName SRV01
# Ora si è "dentro" SRV01
Get-Service | Where-Object Status -eq Running
hostname
Exit-PSSession

# Sessione con credenziali
$cred = Get-Credential
Enter-PSSession -ComputerName SRV01 -Credential $cred

# Invoke-Command: esecuzione remota (1:N, parallelo)
Invoke-Command -ComputerName SRV01, SRV02, SRV03 -ScriptBlock {
    Get-Service -Name "wuauserv" | Select-Object PSComputerName, Status
}

# Invoke-Command con parametri
Invoke-Command -ComputerName SRV01 -ScriptBlock {
    param($serviceName)
    Get-Service -Name $serviceName
} -ArgumentList "wuauserv"

# Invoke-Command con $using: (PowerShell 3+, più pulito)
$svcName = "wuauserv"
Invoke-Command -ComputerName SRV01 -ScriptBlock {
    Get-Service -Name $using:svcName
}

# Invoke-Command con file script locale
Invoke-Command -ComputerName SRV01, SRV02 -FilePath "C:\Scripts\Maintenance.ps1"

# Sessione persistente (riutilizzabile, mantiene stato)
$session = New-PSSession -ComputerName SRV01, SRV02
Invoke-Command -Session $session -ScriptBlock { $global:data = Get-Process }
# Seconda invocazione: la variabile $data è ancora lì
Invoke-Command -Session $session -ScriptBlock { $global:data.Count }
Remove-PSSession $session    # Chiudere quando finito

# Copiare file via sessione remota
$s = New-PSSession -ComputerName SRV01
Copy-Item -Path "C:\Local\file.txt" -Destination "C:\Remote\" -ToSession $s
Copy-Item -Path "C:\Remote\log.txt" -Destination "C:\Local\" -FromSession $s
Remove-PSSession $s

# Esecuzione parallela (PowerShell 7+)
$servers = "SRV01", "SRV02", "SRV03", "SRV04"
$servers | ForEach-Object -Parallel {
    Invoke-Command -ComputerName $_ -ScriptBlock {
        Get-ComputerInfo | Select-Object CsName, OsName
    }
} -ThrottleLimit 4

# Sessione con configurazione personalizzata
$sessionOption = New-PSSessionOption -OpenTimeout 30000 -OperationTimeout 60000 -MaxConnectionRetryCount 3
$session = New-PSSession -ComputerName SRV01 -SessionOption $sessionOption

# Disconnettere e riconnettersi a sessioni
$s = New-PSSession -ComputerName SRV01 -Name "Maintenance"
Invoke-Command -Session $s -ScriptBlock { Start-LongRunningTask }
Disconnect-PSSession $s    # Disconnette ma la sessione continua
# ... più tardi, anche da un altro client ...
$s = Get-PSSession -ComputerName SRV01 -Name "Maintenance"
Connect-PSSession $s
Receive-PSSession $s       # Ricevere l'output
```

### Just Enough Administration (JEA)

```powershell
# JEA limita cosa un utente può fare in una sessione remota
# Principio del minimo privilegio applicato a PowerShell remoting

# 1. Creare Role Capability file (.psrc)
New-PSRoleCapabilityFile -Path "C:\JEA\Roles\DnsAdmin.psrc" `
    -VisibleCmdlets @(
        "Get-DnsServerZone",
        "Add-DnsServerResourceRecordA",
        "Remove-DnsServerResourceRecord",
        @{ Name = "Restart-Service"; Parameters = @{ Name = "Name"; ValidateSet = "DNS" } }
    ) `
    -VisibleFunctions @("Get-DnsReport") `
    -VisibleExternalCommands @("C:\Windows\System32\ipconfig.exe")

# 2. Creare Session Configuration file (.pssc)
New-PSSessionConfigurationFile -Path "C:\JEA\JEAConfig.pssc" `
    -SessionType RestrictedRemoteServer `
    -TranscriptDirectory "C:\JEA\Transcripts" `
    -RunAsVirtualAccount `
    -RoleDefinitions @{
        "CONTOSO\DNS-Operators" = @{ RoleCapabilities = "DnsAdmin" }
        "CONTOSO\DNS-Viewers"   = @{ RoleCapabilities = "DnsViewer" }
    }

# 3. Registrare la configurazione
Register-PSSessionConfiguration -Name "JEA-DNS" `
    -Path "C:\JEA\JEAConfig.pssc" -Force

# 4. Connettersi con JEA
Enter-PSSession -ComputerName DnsServer -ConfigurationName "JEA-DNS"
# L'utente vede SOLO i cmdlet permessi nella Role Capability

# Verificare sessioni JEA disponibili
Get-PSSessionConfiguration | Select-Object Name, Permission

# Testare la configurazione
Test-PSSessionConfigurationFile -Path "C:\JEA\JEAConfig.pssc"
```

---

## DSC — Desired State Configuration

### Risorse DSC

```powershell
# DSC definisce lo STATO DESIDERATO di un sistema in modo dichiarativo
# "Questo server DEVE avere IIS installato" → DSC verifica e corregge

# Esempio: configurazione web server
Configuration WebServerConfig {
    param (
        [string[]]$NodeName = 'localhost'
    )

    Import-DscResource -ModuleName PSDesiredStateConfiguration

    Node $NodeName {
        WindowsFeature IIS {
            Ensure = 'Present'
            Name   = 'Web-Server'
        }

        WindowsFeature IISMgmt {
            Ensure    = 'Present'
            Name      = 'Web-Mgmt-Console'
            DependsOn = '[WindowsFeature]IIS'
        }

        File WebContent {
            Ensure          = 'Present'
            Type            = 'Directory'
            DestinationPath = 'C:\inetpub\wwwroot\mysite'
            DependsOn       = '[WindowsFeature]IIS'
        }

        Service W3SVC {
            Name        = 'W3SVC'
            State       = 'Running'
            StartupType = 'Automatic'
            DependsOn   = '[WindowsFeature]IIS'
        }

        Registry DisableTelemetry {
            Ensure    = 'Present'
            Key       = 'HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\DataCollection'
            ValueName = 'AllowTelemetry'
            ValueData = '0'
            ValueType = 'Dword'
        }

        Script CustomCheck {
            GetScript  = { @{ Result = (Test-Path "C:\App\config.json") } }
            TestScript = { Test-Path "C:\App\config.json" }
            SetScript  = {
                New-Item -Path "C:\App" -ItemType Directory -Force
                '{}' | Set-Content "C:\App\config.json"
            }
        }
    }
}

# Compilare la configurazione (genera file .mof)
WebServerConfig -NodeName "SRV01" -OutputPath "C:\DSC\WebServer"

# Applicare
Start-DscConfiguration -Path "C:\DSC\WebServer" -Wait -Verbose -Force

# Verificare stato
Test-DscConfiguration -Detailed
Get-DscConfigurationStatus
Get-DscConfiguration           # Configurazione corrente applicata

# Risorse DSC disponibili
Get-DscResource
Get-DscResource -Module PSDesiredStateConfiguration

# Installare risorse dalla Gallery
Install-Module -Name xWebAdministration
Install-Module -Name cChoco
Install-Module -Name NetworkingDsc
```

### Push vs Pull Mode

```powershell
# PUSH MODE: l'amministratore "spinge" la configurazione ai nodi
# - Semplice, diretto, nessuna infrastruttura aggiuntiva
# - Ideale per piccoli ambienti

Start-DscConfiguration -Path "C:\DSC\Config" -ComputerName SRV01, SRV02 -Wait -Verbose

# PULL MODE: i nodi "tirano" la configurazione da un Pull Server
# - Scalabile per centinaia/migliaia di nodi
# - I nodi verificano periodicamente e si auto-correggono
# - Richiede un Pull Server (IIS o SMB)

# Configurare il Pull Server (richiede modulo xPSDesiredStateConfiguration)
# I nodi si registrano con un ConfigurationID o RegistrationKey
# e scaricano le configurazioni (.mof) dal server a intervalli regolari
```

### Local Configuration Manager (LCM)

```powershell
# Il LCM è il "motore" DSC su ogni nodo
# Controlla come e quando le configurazioni vengono applicate

# Visualizzare configurazione LCM
Get-DscLocalConfigurationManager

# Configurare LCM
[DSCLocalConfigurationManager()]
Configuration LCMConfig {
    Node "SRV01" {
        Settings {
            # Modalità: ApplyOnly, ApplyAndMonitor, ApplyAndAutoCorrect
            ConfigurationMode              = "ApplyAndAutoCorrect"
            # Intervallo (in minuti) tra i controlli di conformità
            ConfigurationModeFrequencyMins = 30
            # Intervallo refresh (Pull mode)
            RefreshFrequencyMins           = 30
            # Push o Pull
            RefreshMode                    = "Push"
            # Riavvio se necessario
            RebootNodeIfNeeded             = $true
            # Azione su errore di configurazione
            ActionAfterReboot              = "ContinueConfiguration"
        }
    }
}

LCMConfig -OutputPath "C:\DSC\LCM"
Set-DscLocalConfigurationManager -Path "C:\DSC\LCM" -ComputerName SRV01 -Verbose
```

---

## PowerShell per Active Directory

### Gestione Utenti

```powershell
# Modulo richiesto
Import-Module ActiveDirectory

# LEGGERE utenti
Get-ADUser -Identity mrossi -Properties *
Get-ADUser -Identity mrossi -Properties EmailAddress, Department, Title, Manager

Get-ADUser -Filter 'Enabled -eq $true' -Properties LastLogonDate, Department |
    Select-Object Name, SamAccountName, Department, LastLogonDate

Get-ADUser -Filter 'Department -eq "IT"' -Properties Title |
    Select-Object Name, SamAccountName, Title

# Utenti inattivi (ultimo logon > 90 giorni)
Get-ADUser -Filter 'Enabled -eq $true' -Properties LastLogonDate |
    Where-Object { $_.LastLogonDate -lt (Get-Date).AddDays(-90) } |
    Select-Object Name, SamAccountName, LastLogonDate |
    Export-Csv "InactiveUsers.csv" -NoTypeInformation

# CREARE utente
$password = ConvertTo-SecureString "P@ssw0rd123!" -AsPlainText -Force
New-ADUser -Name "Mario Rossi" `
    -SamAccountName "mrossi" `
    -UserPrincipalName "mrossi@contoso.com" `
    -GivenName "Mario" `
    -Surname "Rossi" `
    -DisplayName "Mario Rossi" `
    -Department "IT" `
    -Title "System Administrator" `
    -Office "Milano" `
    -Path "OU=Users,OU=IT,DC=contoso,DC=com" `
    -AccountPassword $password `
    -Enabled $true `
    -ChangePasswordAtLogon $true

# MODIFICARE utente
Set-ADUser -Identity mrossi -Department "DevOps" -Title "DevOps Engineer"
Set-ADUser -Identity mrossi -Replace @{telephoneNumber = "+39 02 1234567"}
Set-ADUser -Identity mrossi -Manager "lverdi"

# Spostare utente tra OU
Move-ADObject -Identity (Get-ADUser mrossi).DistinguishedName `
    -TargetPath "OU=Users,OU=DevOps,DC=contoso,DC=com"

# Disabilitare utente
Disable-ADAccount -Identity mrossi
# Abilitare
Enable-ADAccount -Identity mrossi

# Reset password
Set-ADAccountPassword -Identity mrossi `
    -Reset -NewPassword (ConvertTo-SecureString "NewP@ss123!" -AsPlainText -Force)
Unlock-ADAccount -Identity mrossi

# RIMUOVERE utente
Remove-ADUser -Identity mrossi -Confirm:$false

# Creazione massiva da CSV
Import-Csv "C:\Data\new_users.csv" | ForEach-Object {
    $params = @{
        Name              = "$($_.GivenName) $($_.Surname)"
        SamAccountName    = $_.SamAccountName
        UserPrincipalName = "$($_.SamAccountName)@contoso.com"
        GivenName         = $_.GivenName
        Surname           = $_.Surname
        Department        = $_.Department
        Path              = $_.OU
        AccountPassword   = ConvertTo-SecureString $_.Password -AsPlainText -Force
        Enabled           = $true
    }
    New-ADUser @params
    Write-Output "Creato: $($_.SamAccountName)"
}
```

### Gestione Gruppi

```powershell
# LEGGERE gruppi
Get-ADGroup -Filter * | Select-Object Name, GroupCategory, GroupScope
Get-ADGroup -Identity "Domain Admins" -Properties Members, Description

# Membri di un gruppo
Get-ADGroupMember "Domain Admins"                     # Membri diretti
Get-ADGroupMember "Domain Admins" -Recursive |        # Ricorsivo (nested groups)
    Select-Object Name, ObjectClass, SamAccountName

# Gruppi di un utente
Get-ADPrincipalGroupMembership mrossi | Select-Object Name

# CREARE gruppo
New-ADGroup -Name "GRP-IT-Admins" `
    -SamAccountName "GRP-IT-Admins" `
    -GroupCategory Security `
    -GroupScope Global `
    -DisplayName "IT Administrators" `
    -Path "OU=Groups,DC=contoso,DC=com" `
    -Description "Gruppo amministratori IT"

# MODIFICARE gruppo
Set-ADGroup -Identity "GRP-IT-Admins" -Description "Amministratori IT - Aggiornato"

# Aggiungere membri
Add-ADGroupMember -Identity "GRP-IT-Admins" -Members "mrossi", "lverdi", "gbianchi"

# Rimuovere membri
Remove-ADGroupMember -Identity "GRP-IT-Admins" -Members "mrossi" -Confirm:$false

# RIMUOVERE gruppo
Remove-ADGroup -Identity "GRP-IT-Admins" -Confirm:$false

# Confrontare membri di due gruppi
$group1 = Get-ADGroupMember "GRP-Team1" | Select-Object -ExpandProperty SamAccountName
$group2 = Get-ADGroupMember "GRP-Team2" | Select-Object -ExpandProperty SamAccountName
Compare-Object $group1 $group2
```

### Gestione Computer

```powershell
# LEGGERE computer
Get-ADComputer -Filter * | Select-Object Name, DNSHostName, Enabled
Get-ADComputer -Filter 'OperatingSystem -like "*Server*"' -Properties OperatingSystem, LastLogonDate |
    Select-Object Name, OperatingSystem, LastLogonDate

# Computer inattivi
Get-ADComputer -Filter * -Properties LastLogonDate |
    Where-Object { $_.LastLogonDate -lt (Get-Date).AddDays(-90) } |
    Select-Object Name, LastLogonDate

# CREARE oggetto computer (pre-stage)
New-ADComputer -Name "WS-MROSSI" `
    -SamAccountName "WS-MROSSI" `
    -Path "OU=Workstations,DC=contoso,DC=com" `
    -Enabled $true

# MODIFICARE computer
Set-ADComputer -Identity "WS-MROSSI" -Description "Workstation Mario Rossi - IT"
Set-ADComputer -Identity "WS-MROSSI" -ManagedBy "mrossi"

# Spostare computer tra OU
Move-ADObject -Identity (Get-ADComputer "WS-MROSSI").DistinguishedName `
    -TargetPath "OU=DevOps-Workstations,DC=contoso,DC=com"

# RIMUOVERE computer
Remove-ADComputer -Identity "WS-OLD01" -Confirm:$false
```

### Gestione OU

```powershell
# LEGGERE OU
Get-ADOrganizationalUnit -Filter * | Select-Object Name, DistinguishedName
Get-ADOrganizationalUnit -Filter 'Name -like "IT*"' -Properties Description

# CREARE OU
New-ADOrganizationalUnit -Name "DevOps" `
    -Path "OU=IT,DC=contoso,DC=com" `
    -Description "Unità Organizzativa DevOps" `
    -ProtectedFromAccidentalDeletion $true

# MODIFICARE OU
Set-ADOrganizationalUnit -Identity "OU=DevOps,OU=IT,DC=contoso,DC=com" `
    -Description "DevOps Team - Aggiornato 2026"

# RIMUOVERE OU (prima rimuovere protezione)
Set-ADOrganizationalUnit -Identity "OU=Old,DC=contoso,DC=com" `
    -ProtectedFromAccidentalDeletion $false
Remove-ADOrganizationalUnit -Identity "OU=Old,DC=contoso,DC=com" -Confirm:$false
```

### GPO e Replica

```powershell
# GPO
Get-GPO -All | Select-Object DisplayName, GpoStatus, ModificationTime | Sort-Object ModificationTime
Get-GPO -Name "Default Domain Policy" | Select-Object *

# Report GPO
Get-GPResultantSetOfPolicy -Computer SRV01 -User mrossi -ReportType Html -Path "C:\Reports\rsop.html"
Get-GPOReport -All -ReportType Html -Path "C:\Reports\AllGPOs.html"

# Backup GPO
Backup-GPO -All -Path "C:\GPOBackup"
# Restore
Restore-GPO -Name "My GPO" -Path "C:\GPOBackup"

# REPLICA
Get-ADReplicationPartnerMetadata -Target * -Scope Domain |
    Select-Object Server, Partner, LastReplicationSuccess, LastReplicationResult

Get-ADReplicationFailure -Target * -Scope Domain

# Forzare replica
Invoke-Command -ComputerName DC01 -ScriptBlock { repadmin /syncall /AdeP }
```

### Audit e Account Lockout

```powershell
# Account bloccati
Search-ADAccount -LockedOut | Select-Object Name, SamAccountName, LastLogonDate
# Sbloccare
Unlock-ADAccount -Identity mrossi

# Account scaduti
Search-ADAccount -AccountExpired |
    Select-Object Name, SamAccountName, AccountExpirationDate

# Password scadute
Search-ADAccount -PasswordExpired |
    Select-Object Name, SamAccountName, PasswordLastSet

# Account lockout source (dove è avvenuto il blocco)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4740} -MaxEvents 20 |
    Select-Object TimeCreated,
        @{N='User'; E={$_.Properties[0].Value}},
        @{N='Source'; E={$_.Properties[1].Value}}

# Tentativi di logon falliti
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 50 |
    Select-Object TimeCreated,
        @{N='Account'; E={$_.Properties[5].Value}},
        @{N='SourceIP'; E={$_.Properties[19].Value}},
        @{N='Status'; E={$_.Properties[7].Value}}
```

---

## PowerShell per Exchange

```powershell
# Connettersi a Exchange Online
Install-Module ExchangeOnlineManagement
Connect-ExchangeOnline -UserPrincipalName admin@contoso.com

# MAILBOX
Get-Mailbox -ResultSize Unlimited | Select-Object DisplayName, PrimarySmtpAddress, RecipientTypeDetails
Get-MailboxStatistics -Identity user@contoso.com | Select-Object DisplayName, TotalItemSize, ItemCount

# Creare mailbox condivisa
New-Mailbox -Shared -Name "Info" -DisplayName "Info Contoso" -Alias info
Add-MailboxPermission -Identity info@contoso.com -User mrossi -AccessRights FullAccess

# DISTRIBUTION GROUP
New-DistributionGroup -Name "DG-Marketing" -ManagedBy admin@contoso.com
Add-DistributionGroupMember -Identity "DG-Marketing" -Member user@contoso.com

# MESSAGE TRACE
Get-MessageTrace -SenderAddress user@contoso.com -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date)

# Disconnettersi
Disconnect-ExchangeOnline -Confirm:$false
```

---

## PowerShell per Azure

```powershell
# Installare modulo
Install-Module Az -Scope CurrentUser

# Connettersi
Connect-AzAccount
# Con Service Principal:
# Connect-AzAccount -ServicePrincipal -ApplicationId $appId -CertificateThumbprint $thumb -TenantId $tenant

# Contesto
Get-AzContext
Set-AzContext -Subscription "Production"

# RISORSE
Get-AzVM | Select-Object Name, ResourceGroupName, Location
Get-AzStorageAccount | Select-Object StorageAccountName, ResourceGroupName
Get-AzWebApp | Select-Object Name, State, DefaultHostName

# CREARE RISORSE
New-AzResourceGroup -Name "RG-Production" -Location "westeurope"

New-AzVM -ResourceGroupName "RG-Production" -Name "VM01" `
    -Location "westeurope" -Image "Win2022Datacenter" -Size "Standard_B2s" `
    -Credential (Get-Credential)

# GESTIONE VM
Start-AzVM -ResourceGroupName "RG-Production" -Name "VM01"
Stop-AzVM -ResourceGroupName "RG-Production" -Name "VM01" -Force
Restart-AzVM -ResourceGroupName "RG-Production" -Name "VM01"

# NETWORKING
Get-AzNetworkSecurityGroup | Select-Object Name, ResourceGroupName
Get-AzVirtualNetwork | Select-Object Name, AddressSpace
```

---

## PowerShell per Microsoft 365

```powershell
# Moduli necessari
Install-Module Microsoft.Graph -Scope CurrentUser
Install-Module MSOnline  # Legacy, ancora usato per alcune operazioni

# Connettersi con Microsoft Graph
Connect-MgGraph -Scopes "User.Read.All", "Group.Read.All", "Directory.Read.All"

# UTENTI
Get-MgUser -All | Select-Object DisplayName, UserPrincipalName, AccountEnabled
Get-MgUser -UserId "mrossi@contoso.com" -Property DisplayName, JobTitle, Department

# LICENZE
Get-MgSubscribedSku | Select-Object SkuPartNumber, ConsumedUnits,
    @{N='Total';E={$_.PrepaidUnits.Enabled}}

Get-MgUserLicenseDetail -UserId "mrossi@contoso.com" |
    Select-Object SkuPartNumber

# GRUPPI
Get-MgGroup -All | Where-Object GroupTypes -contains "Unified" |
    Select-Object DisplayName, Mail

# Disconnettersi
Disconnect-MgGraph
```

---

## Sicurezza PowerShell

### Execution Policy in Dettaglio

```powershell
# Le Execution Policy NON sono un meccanismo di sicurezza
# Sono una protezione contro l'esecuzione ACCIDENTALE di script

# Visualizzare policy per ogni scope (priorità dall'alto in basso)
Get-ExecutionPolicy -List
# MachinePolicy   → Group Policy computer
# UserPolicy       → Group Policy utente
# Process          → Solo sessione corrente
# CurrentUser      → HKCU del registro
# LocalMachine     → HKLM del registro

# Impostare per scope
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Set-ExecutionPolicy -ExecutionPolicy AllSigned -Scope LocalMachine

# Per una singola sessione
pwsh -ExecutionPolicy Bypass -File "script.ps1"

# ATTENZIONE: Execution Policy è aggirabile in molti modi
# NON affidarsi ad essa come meccanismo di sicurezza
# Usare AppLocker/WDAC per bloccare veramente l'esecuzione di script
```

### Firma degli Script

```powershell
# Firmare uno script con un certificato code signing

# Trovare certificati code signing
Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert

# Creare certificato self-signed (solo per test)
$cert = New-SelfSignedCertificate -Type CodeSigningCert `
    -Subject "CN=PowerShell Code Signing" `
    -CertStoreLocation Cert:\CurrentUser\My

# Firmare uno script
$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1
Set-AuthenticodeSignature -FilePath "C:\Scripts\MyScript.ps1" -Certificate $cert `
    -TimestampServer "http://timestamp.digicert.com"

# Verificare firma
Get-AuthenticodeSignature -FilePath "C:\Scripts\MyScript.ps1"

# Con AllSigned policy, solo script firmati possono essere eseguiti
# BEST PRACTICE: firmare tutti gli script in produzione
```

### AMSI — Antimalware Scan Interface

```powershell
# AMSI è integrato in PowerShell da Windows 10 / Server 2016
# Ogni script e comando viene inviato all'antimalware PRIMA dell'esecuzione

# Verificare se AMSI è attivo
# In una sessione PowerShell standard, AMSI è sempre attivo

# AMSI intercetta:
# - Script eseguiti con powershell.exe/pwsh.exe
# - Comandi interattivi
# - Contenuti dinamici (Invoke-Expression, .NET reflection)
# - Script offuscati (de-offusca prima di scansionare)

# Gli attaccanti cercano di bypassare AMSI
# Difesa: tenere aggiornato l'antimalware e usare Constrained Language Mode

# Testare AMSI (stringa di test standard EICAR)
# L'antimalware dovrebbe bloccare qualsiasi tentativo di esecuzione
# del test string EICAR in PowerShell
```

### Constrained Language Mode

```powershell
# Constrained Language Mode (CLM) limita le funzionalità PowerShell
# Blocca: .NET arbitrario, COM, P/Invoke, Add-Type
# Permette: cmdlet base, script firmati

# Verificare la modalità corrente
$ExecutionContext.SessionState.LanguageMode
# FullLanguage        → Tutte le funzionalità (default admin)
# ConstrainedLanguage → Limitato (default con AppLocker/WDAC)
# RestrictedLanguage  → Molto limitato (no script blocks)
# NoLanguage          → Solo comandi, nessun scripting

# Impostare CLM manualmente (non persistente, per test)
$ExecutionContext.SessionState.LanguageMode = "ConstrainedLanguage"

# Implementazione corretta tramite:
# 1. WDAC (Windows Defender Application Control) — preferito
# 2. AppLocker con regole script PowerShell
# Quando WDAC/AppLocker è attivo, PS entra automaticamente in CLM
# per sessioni non elevate o script non firmati

# In CLM, questi sono bloccati:
# [System.IO.File]::ReadAllText("C:\file.txt")     # BLOCCATO
# Add-Type -TypeDefinition $code                    # BLOCCATO
# $obj.GetType().GetMethods()                       # BLOCCATO (reflection)
# New-Object -ComObject WScript.Shell               # BLOCCATO
```

### Logging e Auditing

```powershell
# PowerShell offre 3 livelli di logging per security auditing

# 1. SCRIPT BLOCK LOGGING
# Registra ogni blocco di script eseguito (inclusi quelli deoffuscati)
# Abilitare via GPO o registro:
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
New-Item -Path $regPath -Force
Set-ItemProperty -Path $regPath -Name "EnableScriptBlockLogging" -Value 1
# Log in: Event Viewer → Applications and Services → Microsoft → Windows → PowerShell → Operational
# Event ID: 4104

# 2. MODULE LOGGING
# Registra esecuzione pipeline per moduli specifici
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging"
New-Item -Path $regPath -Force
Set-ItemProperty -Path $regPath -Name "EnableModuleLogging" -Value 1
# Specificare moduli:
$regPath2 = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging\ModuleNames"
New-Item -Path $regPath2 -Force
Set-ItemProperty -Path $regPath2 -Name "*" -Value "*"    # Tutti i moduli
# Event ID: 4103

# 3. TRANSCRIPTION
# Registra TUTTO l'input e output della console in file di testo
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription"
New-Item -Path $regPath -Force
Set-ItemProperty -Path $regPath -Name "EnableTranscripting" -Value 1
Set-ItemProperty -Path $regPath -Name "OutputDirectory" -Value "C:\PSTranscripts"
Set-ItemProperty -Path $regPath -Name "EnableInvocationHeader" -Value 1

# Transcription manuale (per sessione)
Start-Transcript -Path "C:\Transcripts\session_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
# ... lavoro ...
Stop-Transcript

# Consultare i log
Get-WinEvent -FilterHashtable @{
    LogName      = "Microsoft-Windows-PowerShell/Operational"
    Id           = 4104    # Script Block Logging
} -MaxEvents 20 | Select-Object TimeCreated, Message

# BEST PRACTICE di sicurezza per PowerShell:
# - Abilitare tutti e 3 i tipi di logging
# - Impostare CLM tramite WDAC per utenti non-admin
# - Usare AllSigned execution policy + certificato aziendale
# - Centralizzare i log con SIEM (Splunk, Sentinel, Elastic)
# - Monitorare Event ID 4104, 4103, 4688 (process creation)
# - Disabilitare PowerShell 2.0 (non supporta AMSI e CLM):
Disable-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root
```

---

## Performance e Ottimizzazione

### Measure-Command

```powershell
# Misurare il tempo di esecuzione di un blocco
Measure-Command {
    Get-ChildItem -Recurse C:\Windows -ErrorAction SilentlyContinue | Out-Null
}
# Restituisce un TimeSpan

# Confrontare due approcci
$t1 = Measure-Command {
    Get-ADUser -Filter * | Where-Object Department -eq "IT"
}
$t2 = Measure-Command {
    Get-ADUser -Filter 'Department -eq "IT"'
}
"Where-Object: $($t1.TotalMilliseconds)ms vs -Filter: $($t2.TotalMilliseconds)ms"

# Misurare con Stopwatch (per misurazioni più precise)
$sw = [System.Diagnostics.Stopwatch]::StartNew()
# ... operazione ...
$sw.Stop()
"Elapsed: $($sw.Elapsed.TotalSeconds) secondi"
```

### Esecuzione Parallela

```powershell
# ForEach-Object -Parallel (PowerShell 7+)
# Esegue script blocks in thread separati

$servers = @("SRV01", "SRV02", "SRV03", "SRV04", "SRV05")

# Sequenziale (lento)
$servers | ForEach-Object {
    Test-Connection $_ -Count 1 -Quiet
}

# Parallelo (veloce)
$servers | ForEach-Object -Parallel {
    [PSCustomObject]@{
        Server = $_
        Online = Test-Connection $_ -Count 1 -Quiet
    }
} -ThrottleLimit 5

# Usare variabili esterne con $using:
$logDir = "C:\Logs"
$cred = Get-Credential
$servers | ForEach-Object -Parallel {
    $result = Invoke-Command -ComputerName $_ -Credential $using:cred -ScriptBlock {
        Get-Service | Where-Object Status -eq "Running"
    }
    $result | Export-Csv "$($using:logDir)\$($_)_services.csv" -NoTypeInformation
} -ThrottleLimit 10

# ATTENZIONE: -Parallel ha overhead per la creazione dei thread
# NON usare per operazioni veloci su pochi elementi
# Il beneficio si vede con operazioni I/O-bound o molti elementi
```

### Jobs

```powershell
# Start-Job: esegue un script block in background (processo separato)

# Avviare un job
$job = Start-Job -ScriptBlock {
    Get-ChildItem C:\Windows -Recurse -ErrorAction SilentlyContinue
}

# Controllare stato
Get-Job              # Lista tutti i job
Get-Job -Id 1        # Job specifico
$job.State           # Running, Completed, Failed

# Ricevere risultati
$results = Receive-Job -Job $job -Wait    # -Wait attende il completamento
Receive-Job -Id 1

# Rimuovere job
Remove-Job -Job $job
Get-Job | Remove-Job    # Rimuovere tutti

# Job con parametri
Start-Job -ScriptBlock {
    param($path, $filter)
    Get-ChildItem -Path $path -Filter $filter -Recurse
} -ArgumentList "C:\Logs", "*.log"

# Attendere tutti i job
$jobs = @()
$jobs += Start-Job { Get-Service }
$jobs += Start-Job { Get-Process }
$jobs += Start-Job { Get-EventLog System -Newest 100 }
$results = $jobs | Wait-Job | Receive-Job

# Start-ThreadJob (più leggero, stesso processo)
# Richiede: Install-Module ThreadJob
Start-ThreadJob -ScriptBlock { Get-Process }
```

### Runspaces

```powershell
# Runspaces: il modo più performante per il parallelismo
# Meno overhead di Jobs (nessun processo separato)
# Più complesso da usare, ma molto più veloce

# Esempio con RunspacePool
$maxThreads = 10
$pool = [runspacefactory]::CreateRunspacePool(1, $maxThreads)
$pool.Open()

$jobs = @()
$servers = @("SRV01", "SRV02", "SRV03", "SRV04", "SRV05")

foreach ($server in $servers) {
    $ps = [powershell]::Create()
    $ps.RunspacePool = $pool
    $ps.AddScript({
        param($computerName)
        [PSCustomObject]@{
            Computer = $computerName
            Online   = Test-Connection $computerName -Count 1 -Quiet
            Time     = Get-Date
        }
    }).AddArgument($server) | Out-Null

    $jobs += [PSCustomObject]@{
        PowerShell = $ps
        Handle     = $ps.BeginInvoke()
    }
}

# Raccogliere risultati
$results = foreach ($job in $jobs) {
    $job.PowerShell.EndInvoke($job.Handle)
    $job.PowerShell.Dispose()
}

$pool.Close()
$pool.Dispose()

$results | Format-Table -AutoSize
```

### Tecniche di Ottimizzazione

```powershell
# 1. FILTRARE A SINISTRA (Filter-Left)
# Il filtro più vicino possibile alla sorgente dati

# LENTO: recupera tutto, poi filtra
Get-ADUser -Filter * | Where-Object Department -eq "IT"
# VELOCE: filtra al server
Get-ADUser -Filter 'Department -eq "IT"'

# LENTO: recupera tutto da CIM, poi filtra
Get-CimInstance Win32_Service | Where-Object State -eq "Running"
# VELOCE: filtro WQL al provider
Get-CimInstance Win32_Service -Filter "State='Running'"

# 2. SELEZIONARE SOLO LE PROPRIETÀ NECESSARIE
# LENTO
Get-ADUser -Filter * -Properties *
# VELOCE
Get-ADUser -Filter * -Properties Department, LastLogonDate

# 3. USARE ArrayList/List INVECE DI += su array
# LENTO (O(n^2) - ricrea l'array ogni volta)
$arr = @()
1..10000 | ForEach-Object { $arr += $_ }
# VELOCE (O(1) ammortizzato)
$list = [System.Collections.Generic.List[int]]::new()
1..10000 | ForEach-Object { $list.Add($_) }

# 4. USARE StringBuilder PER CONCATENAZIONE STRINGHE
# LENTO
$text = ""
1..10000 | ForEach-Object { $text += "Riga $_`n" }
# VELOCE
$sb = [System.Text.StringBuilder]::new()
1..10000 | ForEach-Object { $sb.AppendLine("Riga $_") | Out-Null }
$text = $sb.ToString()

# 5. EVITARE Write-Host NELLA PIPELINE
# Write-Host scrive direttamente alla console (lento)
# Write-Output scrive nella pipeline (veloce, reindirizzabile)

# 6. SOPPRIMERE OUTPUT NON NECESSARIO
# Usare [void] o Out-Null
[void]$list.Add("item")          # Più veloce
$list.Add("item") | Out-Null     # Più lento (crea pipeline)
$null = $list.Add("item")        # Veloce

# 7. USARE -ReadCount CON Get-Content PER FILE GRANDI
Get-Content "C:\huge.log" -ReadCount 1000 | ForEach-Object {
    # $_ è un array di 1000 righe
    $_ | Where-Object { $_ -match "ERROR" }
}

# 8. $ProgressPreference PER VELOCIZZARE CMDLET CON BARRA PROGRESSIONE
$ProgressPreference = "SilentlyContinue"    # Disabilita barra progressione
Invoke-WebRequest -Uri "https://example.com/big.zip" -OutFile "big.zip"
$ProgressPreference = "Continue"             # Ripristinare
```

---

## Moduli Utili e Gallery

| Modulo | Funzione |
|--------|----------|
| `ActiveDirectory` | Gestione AD DS (built-in con RSAT) |
| `PSWindowsUpdate` | Gestione Windows Update da PowerShell |
| `ImportExcel` | Import/export Excel senza Office installato |
| `Pester` | Framework testing per PowerShell |
| `PSScriptAnalyzer` | Linter per best practices PowerShell |
| `posh-git` | Integrazione Git nel prompt |
| `Terminal-Icons` | Icone nel terminale |
| `Microsoft.Graph` | API Microsoft Graph (M365, Azure AD) |
| `Az` | Azure Resource Management |
| `ExchangeOnlineManagement` | Exchange Online |
| `VMware.PowerCLI` | Gestione VMware vSphere |
| `dbatools` | Amministrazione SQL Server |
| `Pode` | Web server/API in PowerShell |
| `PSReadLine` | Editing riga di comando avanzato (built-in) |
| `ThreadJob` | Jobs leggeri (thread, non processi) |
| `Microsoft.PowerShell.SecretManagement` | Gestione centralizzata dei segreti |
| `Microsoft.PowerShell.SecretStore` | Vault locale per SecretManagement |
| `PlatyPS` | Generazione documentazione help da Markdown |
| `PSFramework` | Logging, configurazione, templating per moduli |
| `Selenium` | Automazione browser web |

---

## Best Practices

1. **Usare Advanced Functions con CmdletBinding**: `[CmdletBinding()]` abilita `-Verbose`, `-Debug`, `-ErrorAction` e altre funzionalità standard.
2. **Verb-Noun naming**: seguire la convenzione. `Get-Verb` elenca i verbi approvati.
3. **Error handling esplicito**: usare `try/catch` con `-ErrorAction Stop`.
4. **Comment-based help**: documentare ogni funzione con `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`, `.EXAMPLE`.
5. **Evitare Write-Host**: usare `Write-Output` per dati, `Write-Verbose` per dettagli, `Write-Warning` per avvisi. `Write-Host` solo per UI interattiva.
6. **Non usare alias negli script**: `gci` → `Get-ChildItem` (leggibilità e portabilità).
7. **Splatting per comandi lunghi**: `$params = @{...}; Cmd @params`.
8. **PSScriptAnalyzer**: eseguire prima di ogni deploy per verificare best practices.
9. **Filtrare a sinistra**: usare `-Filter` del cmdlet prima di `Where-Object`.
10. **Output tipizzato**: restituire `[PSCustomObject]` con proprietà consistenti.
11. **Usare `#Requires`**: dichiarare prerequisiti in testa allo script.
    ```powershell
    #Requires -Version 7.0
    #Requires -Modules ActiveDirectory
    #Requires -RunAsAdministrator
    ```
12. **Non hardcodare credenziali**: usare `Get-Credential`, `SecretManagement`, o variabili d'ambiente.
13. **Usare `-WhatIf` e `-Confirm`**: implementare `SupportsShouldProcess` in funzioni che modificano dati.
14. **Logging strutturato**: usare `Write-Verbose`, `Write-Debug`, `Write-Information` per diagnostica.
15. **Encoding UTF8**: impostare `$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'`.

---

## Troubleshooting

**"Il termine non è riconosciuto come cmdlet"**
Il modulo non è installato o importato. Verificare: `Get-Module -ListAvailable | Where-Object Name -like "*keyword*"`. Installare con `Install-Module` o importare con `Import-Module`. Se il modulo è per PS 5.1, usare `Import-Module -UseWindowsPowerShell`.

**"Accesso negato durante remoting"**
Verificare: WinRM abilitato sul target (`Enable-PSRemoting`), firewall aperto (porta 5985 HTTP / 5986 HTTPS), l'utente è admin locale sul target, TrustedHosts configurato se non in dominio. Testare con `Test-WSMan -ComputerName SRV01`.

**"Execution Policy impedisce l'esecuzione"**
`Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`. Per esecuzioni singole: `pwsh -ExecutionPolicy Bypass -File script.ps1`. Verificare con `Get-ExecutionPolicy -List` quale scope blocca.

**"Pipeline lenta con molti oggetti"**
Usare `-Filter` direttamente nel cmdlet anziché `Where-Object` dopo. Esempio: `Get-ADUser -Filter 'Department -eq "IT"'` è molto più veloce di `Get-ADUser -Filter * | Where-Object Department -eq "IT"`.

**"Modulo non compatibile con PowerShell 7"**
Usare `Import-Module NomeModulo -UseWindowsPowerShell`. Questo crea un proxy che comunica con un processo PS 5.1 in background. Verificare compatibilità con `Get-Module -ListAvailable -PSEdition Desktop`.

**"ConvertFrom-Json restituisce oggetto piatto"**
Usare `-Depth` con `ConvertTo-Json`: il valore default è 2, insufficiente per oggetti profondamente annidati. Esempio: `$obj | ConvertTo-Json -Depth 10`.

**"Errori di encoding nei file CSV/testo"**
Specificare sempre l'encoding: `Export-Csv -Encoding UTF8`, `Out-File -Encoding UTF8`, `Set-Content -Encoding UTF8`. In PS 7, UTF8 senza BOM è il default; in PS 5.1 no.

**"Get-WinEvent non trova eventi"**
Verificare il nome del log con `Get-WinEvent -ListLog *`. Usare `-FilterHashtable` per prestazioni: `Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625}` è più veloce di `Where-Object`.

**"Invoke-WebRequest fallisce con errore SSL"**
In PS 5.1: `[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12`. In PS 7: usare `-SkipCertificateCheck` per test (mai in produzione). Verificare che i certificati root siano aggiornati.

**"Variable scope: la variabile non è visibile nella funzione"**
Per default, le funzioni vedono le variabili del parent scope in sola lettura. Per modificarle: usare `$script:var` o `$global:var`. Preferire passare valori tramite parametri.

**"Array += è lento con molti elementi"**
`+=` ricrea l'array ogni volta (O(n)). Usare `[System.Collections.Generic.List[tipo]]` con `.Add()` che è O(1) ammortizzato. Differenza significativa sopra i 1000 elementi.

**"ForEach-Object -Parallel non vede le mie variabili"**
Usare `$using:nomeVariabile` per accedere a variabili dello scope esterno. Le variabili locali non sono accessibili nei thread paralleli. Funzioni e moduli devono essere ri-importati in ogni thread.

**"Script funziona in console ma non come scheduled task"**
Verificare: percorso completo dell'eseguibile (`pwsh.exe` o `powershell.exe`), execution policy (`-ExecutionPolicy Bypass`), account di esecuzione (Local System non ha profilo utente), percorsi di rete (mappature drive non disponibili senza logon interattivo).

**"Get-ADUser è lento con -Properties *"**
Non usare `-Properties *` in produzione. Specificare solo le proprietà necessarie. Usare `-ResultSetSize` per limitare i risultati durante il debug. Usare `-SearchBase` per limitare l'ambito di ricerca.

**"CIM/WMI: RPC server non disponibile"**
Verificare: servizio WinRM attivo sul target, firewall (porte 135, 5985-5986), DNS risolve il nome correttamente, l'utente ha permessi WMI sul target. Provare con DCOM: `$opt = New-CimSessionOption -Protocol Dcom`.

**"Errore 'Cannot bind argument to parameter' con pipeline"**
Verificare il tipo di binding: `ByValue` (tipo oggetto intero) vs `ByPropertyName` (nomi proprietà matchano nomi parametri). Usare `Get-Help NomeCmdlet -Parameter NomeParametro` per vedere se accetta pipeline input e come.

**"Select-Object restituisce NoteProperty invece del tipo originale"**
Normale: `Select-Object` crea nuovi oggetti `PSCustomObject` con le proprietà selezionate. Se serve il tipo originale, usare `Where-Object` per filtrare o accedere alla proprietà direttamente.

**"Lo script consuma troppa memoria"**
Usare pipeline streaming (`ForEach-Object`) invece di `foreach` statement che carica tutto in memoria. Processare file grandi con `-ReadCount`. Forzare garbage collection con `[GC]::Collect()` se necessario (raro).

**"Errore double-hop nel remoting"**
Il secondo hop (es. da SRV01 accedere a SRV02) fallisce perché le credenziali non vengono delegate. Soluzioni: CredSSP (meno sicuro), Kerberos constrained delegation (preferito), o passare esplicitamente le credenziali con `$using:cred` in `Invoke-Command`.

**"Differenze di output tra PS 5.1 e 7"**
Alcuni cmdlet hanno output diverso tra le versioni. Confrontare con `Get-Command NomeCmdlet | Select-Object Source, Version`. Alcuni moduli Windows esistono solo in 5.1. Usare `$PSVersionTable.PSEdition` per branching condizionale.

---

## FAQ

**D1: Qual è la differenza tra `ForEach-Object` e `foreach` statement?**
`ForEach-Object` opera nella pipeline, elaborando un oggetto alla volta (bassa memoria, streaming). `foreach` carica l'intera collezione in memoria prima di iterare (più veloce per piccole collezioni, ma non usa la pipeline). Negli script, `foreach` è tipicamente più veloce; nella pipeline, `ForEach-Object` è obbligatorio.

**D2: Quando usare Write-Output vs Write-Host vs Write-Verbose?**
`Write-Output` (o nessun cmdlet, output implicito) per dati che devono attraversare la pipeline. `Write-Host` solo per UI interattiva (non catturabile in variabili). `Write-Verbose` per messaggi diagnostici visibili con `-Verbose`. `Write-Warning` per avvisi, `Write-Error` per errori non-terminanti.

**D3: Come gestire le credenziali in modo sicuro negli script automatizzati?**
Opzioni in ordine di preferenza: (1) Managed Service Account / gMSA per scheduled tasks; (2) `SecretManagement` module con vault Azure Key Vault o locale; (3) `Export-Clixml` per salvare credenziali criptate con DPAPI (legate a utente+macchina); (4) Variabili d'ambiente. Mai hardcodare password nel codice.

**D4: Come faccio a eseguire comandi su centinaia di server?**
`Invoke-Command` è già parallelo per natura: invia i comandi simultaneamente a tutti i server specificati in `-ComputerName`. Usare `-ThrottleLimit` per limitare le connessioni simultanee (default: 32). Per grandi numeri, usare sessioni persistenti con `New-PSSession`.

**D5: Posso usare PowerShell per REST API?**
Sì. `Invoke-RestMethod` converte automaticamente JSON in oggetti. `Invoke-WebRequest` dà controllo completo su headers e response. Supportano autenticazione Bearer, Basic, OAuth. Esempio: `Invoke-RestMethod -Uri $url -Headers @{Authorization="Bearer $token"} -Method Get`.

**D6: Come creare un log file strutturato?**
Usare un pattern con timestamp e livello. Esempio: funzione `Write-Log` che scrive a file e usa `Write-Verbose` contemporaneamente. Per logging professionale, usare il modulo `PSFramework` che offre logging async, rotazione, e provider multipli.

**D7: Cosa sono i PowerShell Providers e perché mi servono?**
I Providers espongono data store diversi (filesystem, registro, certificati, variabili d'ambiente) come se fossero filesystem. Permettono di usare `Get-ChildItem`, `Set-Location`, `New-Item` su dati che non sono file. Esempio: navigare il registro con `cd HKLM:\SOFTWARE`, o i certificati con `cd Cert:\LocalMachine\My`.

**D8: Come debuggare uno script PowerShell?**
(1) `Set-PSBreakpoint -Script script.ps1 -Line 42` per breakpoint. (2) `Set-PSBreakpoint -Variable myVar -Mode ReadWrite` per breakpoint su variabile. (3) VS Code con estensione PowerShell (F5 per debug). (4) `Set-StrictMode -Version Latest` per catturare variabili non definite. (5) `$DebugPreference = "Continue"` per vedere messaggi `Write-Debug`.

**D9: Qual è la differenza tra `-eq` e `.Equals()`?**
`-eq` è l'operatore PowerShell: case-insensitive per stringhe, gestisce `$null`, funziona con array (filtra). `.Equals()` è il metodo .NET: case-sensitive, lancia eccezione su `$null`. Usare `-eq` nella maggior parte dei casi. Usare `-ceq` per confronti case-sensitive.

**D10: Come rendere uno script compatibile sia con PS 5.1 che 7?**
Usare `$PSVersionTable.PSEdition` per branching. Evitare feature PS 7-only (ternary, null-coalescing, -Parallel) o wrappare con `if ($PSVersionTable.PSVersion.Major -ge 7)`. Testare su entrambe le versioni. Usare `#Requires -Version 5.1` per dichiarare il minimo.

**D11: Come gestire file Excel senza Office installato?**
Modulo `ImportExcel`: `Install-Module ImportExcel`. Supporta lettura, scrittura, formattazione, grafici, pivot table. Esempio: `Import-Excel "file.xlsx" -WorksheetName "Sheet1"` e `$data | Export-Excel "output.xlsx" -AutoSize -FreezeTopRow -BoldTopRow`.

**D12: Come misurare le prestazioni di uno script?**
`Measure-Command { ... }` per blocchi semplici. `[System.Diagnostics.Stopwatch]` per misurazioni granulari. `Trace-Command` per debug di pipeline e parameter binding. Per profiling completo, VS Code con l'estensione PowerShell offre profiling integrato.

**D13: Come funziona lo scope in PowerShell?**
Scope gerarchico: Global → Script → Function → Local. Le variabili sono visibili nei child scope (lettura), ma le modifiche nel child scope creano una copia locale. Per modificare nel parent scope: `$script:var`, `$global:var`. I moduli hanno il proprio scope isolato.

**D14: Come gestire output multipli da una funzione?**
Tutto l'output non catturato diventa parte del return value. Per restituire un solo tipo di dato: catturare output indesiderato con `$null =`, `[void]`, o `| Out-Null`. Usare `Write-Verbose` e `Write-Warning` per messaggi (non vanno nella pipeline). Per output strutturato complesso, restituire un singolo `[PSCustomObject]`.

**D15: Qual è la differenza tra Pester 4 e Pester 5?**
Pester 5 ha rotto la retrocompatibilità. Differenze principali: `Should` ora usa `-Be`, `-BeExactly`, `-HaveCount` (non più `Should Be`). Discovery e Run sono fasi separate. I mock sono scoped al blocco `It` o `Context`. `TestDrive:` è ancora supportato. Windows include Pester 3.4; installare v5 con `Install-Module Pester -Force -SkipPublisherCheck`.

**D16: Come monitorare le risorse di sistema con PowerShell?**
Combinare `Get-CimInstance` per snapshot, `Get-Counter` per performance counter real-time, e `Register-CimIndicationEvent` per eventi WMI asincroni. Esempio: `Get-Counter '\Processor(*)\% Processor Time' -Continuous -SampleInterval 2` per CPU real-time.

---

## Script Pratici

### Script 1 — Report stato servizi critici

```powershell
<#
.SYNOPSIS
    Genera un report HTML dei servizi critici su server multipli.
.DESCRIPTION
    Controlla lo stato di servizi predefiniti su una lista di server
    e genera un report HTML con evidenziazione dei servizi fermi.
#>

#Requires -Version 5.1

param(
    [string[]]$ComputerName = @("SRV01", "SRV02", "SRV03"),
    [string[]]$ServiceName  = @("wuauserv", "W3SVC", "MSSQLSERVER", "DNS", "Spooler"),
    [string]$ReportPath     = "C:\Reports\ServiceReport_$(Get-Date -Format 'yyyyMMdd_HHmmss').html"
)

$results = foreach ($computer in $ComputerName) {
    foreach ($svc in $ServiceName) {
        try {
            $service = Get-Service -ComputerName $computer -Name $svc -ErrorAction Stop
            [PSCustomObject]@{
                Computer    = $computer
                ServiceName = $svc
                DisplayName = $service.DisplayName
                Status      = $service.Status.ToString()
                StartType   = $service.StartType.ToString()
                Checked     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            }
        }
        catch {
            [PSCustomObject]@{
                Computer    = $computer
                ServiceName = $svc
                DisplayName = "N/A"
                Status      = "NOT FOUND"
                StartType   = "N/A"
                Checked     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            }
        }
    }
}

# Generare HTML con stile
$head = @"
<style>
    body { font-family: Segoe UI, sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; }
    th { background-color: #2c3e50; color: white; padding: 10px; text-align: left; }
    td { padding: 8px; border: 1px solid #ddd; }
    tr:nth-child(even) { background-color: #f2f2f2; }
    .stopped { background-color: #e74c3c; color: white; }
    .running { background-color: #2ecc71; color: white; }
    h1 { color: #2c3e50; }
</style>
"@

$body = $results | ForEach-Object {
    $statusClass = switch ($_.Status) {
        "Running" { "running" }
        default   { "stopped" }
    }
    $_ | Add-Member -MemberType NoteProperty -Name "StatusClass" -Value $statusClass -PassThru
}

$html = $body | ConvertTo-Html -Head $head -Title "Service Report" `
    -PreContent "<h1>Report Servizi - $(Get-Date -Format 'dd/MM/yyyy HH:mm')</h1>"

# Evidenziare celle con colore
$html = $html -replace '<td>Running</td>', '<td class="running">Running</td>'
$html = $html -replace '<td>Stopped</td>', '<td class="stopped">Stopped</td>'
$html = $html -replace '<td>NOT FOUND</td>', '<td class="stopped">NOT FOUND</td>'

$html | Out-File $ReportPath -Encoding UTF8
Write-Output "Report salvato: $ReportPath"
```

### Script 2 — Pulizia file vecchi con log

```powershell
<#
.SYNOPSIS
    Elimina file più vecchi di N giorni da cartelle specificate.
.DESCRIPTION
    Scansiona le cartelle indicate, trova file più vecchi della soglia,
    li elimina e genera un log dettagliato delle operazioni.
#>

#Requires -Version 5.1

param(
    [Parameter(Mandatory)]
    [string[]]$Path,

    [int]$DaysOld = 30,

    [string[]]$Include = @("*.log", "*.tmp", "*.bak"),

    [string]$LogFile = "C:\Logs\Cleanup_$(Get-Date -Format 'yyyyMMdd').log",

    [switch]$WhatIf
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logEntry
    switch ($Level) {
        "ERROR"   { Write-Warning $Message }
        "WARNING" { Write-Warning $Message }
        default   { Write-Verbose $Message }
    }
}

$cutoffDate = (Get-Date).AddDays(-$DaysOld)
$totalSize = 0
$totalCount = 0

Write-Log "Avvio pulizia. Soglia: $DaysOld giorni (prima di $($cutoffDate.ToString('yyyy-MM-dd')))"
Write-Log "Cartelle: $($Path -join ', ')"
Write-Log "Pattern: $($Include -join ', ')"
if ($WhatIf) { Write-Log "MODALITA' SIMULAZIONE (WhatIf)" "WARNING" }

foreach ($folder in $Path) {
    if (-not (Test-Path $folder)) {
        Write-Log "Cartella non trovata: $folder" "WARNING"
        continue
    }

    $files = Get-ChildItem -Path $folder -Include $Include -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoffDate }

    foreach ($file in $files) {
        try {
            $sizeKB = [math]::Round($file.Length / 1KB, 2)
            if ($WhatIf) {
                Write-Log "[WhatIf] Eliminerei: $($file.FullName) ($sizeKB KB, $($file.LastWriteTime.ToString('yyyy-MM-dd')))"
            } else {
                Remove-Item $file.FullName -Force -ErrorAction Stop
                Write-Log "Eliminato: $($file.FullName) ($sizeKB KB)"
            }
            $totalSize += $file.Length
            $totalCount++
        }
        catch {
            Write-Log "Errore eliminazione $($file.FullName): $_" "ERROR"
        }
    }
}

$totalMB = [math]::Round($totalSize / 1MB, 2)
$action = if ($WhatIf) { "da eliminare" } else { "eliminati" }
Write-Log "Completato. File $action`: $totalCount, Spazio liberato: $totalMB MB"
Write-Output "Pulizia completata. $totalCount file $action ($totalMB MB). Log: $LogFile"
```

### Script 3 — Monitoraggio spazio disco con allarme

```powershell
<#
.SYNOPSIS
    Monitora lo spazio disco e invia allarme se sotto soglia.
#>

#Requires -Version 5.1

param(
    [string[]]$ComputerName = @($env:COMPUTERNAME),
    [int]$ThresholdPercent  = 15,
    [string]$SmtpServer     = "smtp.contoso.com",
    [string]$From           = "monitoring@contoso.com",
    [string[]]$To           = @("admin@contoso.com")
)

$alerts = @()

foreach ($computer in $ComputerName) {
    try {
        $disks = Get-CimInstance -ClassName Win32_LogicalDisk `
            -ComputerName $computer -Filter "DriveType=3" -ErrorAction Stop

        foreach ($disk in $disks) {
            $freePercent = [math]::Round(($disk.FreeSpace / $disk.Size) * 100, 1)
            $freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
            $totalGB = [math]::Round($disk.Size / 1GB, 2)

            if ($freePercent -lt $ThresholdPercent) {
                $alerts += [PSCustomObject]@{
                    Computer    = $computer
                    Drive       = $disk.DeviceID
                    TotalGB     = $totalGB
                    FreeGB      = $freeGB
                    FreePercent = $freePercent
                    Severity    = if ($freePercent -lt 5) { "CRITICAL" }
                                 elseif ($freePercent -lt 10) { "HIGH" }
                                 else { "WARNING" }
                }
            }
        }
    }
    catch {
        Write-Warning "Impossibile contattare $computer`: $_"
    }
}

if ($alerts.Count -gt 0) {
    $body = $alerts | ConvertTo-Html -Fragment -PreContent "<h2>Disk Space Alerts</h2>" | Out-String
    $subject = "DISK ALERT: $($alerts.Count) dischi sotto soglia ($ThresholdPercent%)"

    $mailParams = @{
        From       = $From
        To         = $To
        Subject    = $subject
        Body       = $body
        BodyAsHtml = $true
        SmtpServer = $SmtpServer
    }
    Send-MailMessage @mailParams
    Write-Output "Inviato allarme per $($alerts.Count) dischi"
    $alerts | Format-Table -AutoSize
} else {
    Write-Output "Tutti i dischi sopra soglia ($ThresholdPercent%). Nessun allarme."
}
```

### Script 4 — Inventario software installato

```powershell
<#
.SYNOPSIS
    Genera un inventario del software installato su computer remoti.
#>

#Requires -Version 5.1

param(
    [string[]]$ComputerName = @($env:COMPUTERNAME),
    [string]$OutputPath = "C:\Reports\SoftwareInventory_$(Get-Date -Format 'yyyyMMdd').csv"
)

$regPaths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
)

$inventory = foreach ($computer in $ComputerName) {
    Write-Verbose "Scansione $computer..."
    try {
        Invoke-Command -ComputerName $computer -ScriptBlock {
            param($paths)
            foreach ($path in $paths) {
                Get-ItemProperty $path -ErrorAction SilentlyContinue |
                    Where-Object { $_.DisplayName -and $_.DisplayName.Trim() -ne "" } |
                    Select-Object @{N='Computer'; E={$env:COMPUTERNAME}},
                        DisplayName, DisplayVersion, Publisher, InstallDate,
                        @{N='SizeKB'; E={$_.EstimatedSize}},
                        @{N='Architecture'; E={
                            if ($path -like "*WOW6432Node*") { "x86" } else { "x64" }
                        }}
            }
        } -ArgumentList (,$regPaths) -ErrorAction Stop
    }
    catch {
        Write-Warning "Errore su $computer`: $_"
        [PSCustomObject]@{
            Computer       = $computer
            DisplayName    = "ERRORE CONNESSIONE"
            DisplayVersion = $_.Exception.Message
            Publisher      = ""; InstallDate = ""; SizeKB = 0; Architecture = ""
        }
    }
}

$inventory | Sort-Object Computer, DisplayName |
    Export-Csv $OutputPath -NoTypeInformation -Encoding UTF8

$stats = $inventory | Group-Object Computer | Select-Object Name, Count
Write-Output "Inventario completato: $($inventory.Count) software su $($stats.Count) computer"
Write-Output "Salvato: $OutputPath"
$stats | Format-Table -AutoSize
```

### Script 5 — Backup automatico con rotazione

```powershell
<#
.SYNOPSIS
    Esegue backup di cartelle con compressione e rotazione dei vecchi backup.
#>

#Requires -Version 5.1

param(
    [Parameter(Mandatory)]
    [string[]]$SourcePath,

    [Parameter(Mandatory)]
    [string]$DestinationPath,

    [int]$RetainDays = 30,

    [string]$LogFile = "C:\Logs\Backup_$(Get-Date -Format 'yyyyMMdd').log"
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

function Write-Log {
    param([string]$Message)
    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Add-Content -Path $LogFile -Value $entry
    Write-Output $entry
}

# Creare directory destinazione
if (-not (Test-Path $DestinationPath)) {
    New-Item -Path $DestinationPath -ItemType Directory -Force | Out-Null
}

Write-Log "=== INIZIO BACKUP ==="

# Backup ogni cartella
foreach ($source in $SourcePath) {
    if (-not (Test-Path $source)) {
        Write-Log "ERRORE: Sorgente non trovata: $source"
        continue
    }

    $folderName = Split-Path $source -Leaf
    $archiveName = "${folderName}_${timestamp}.zip"
    $archivePath = Join-Path $DestinationPath $archiveName

    Write-Log "Backup: $source -> $archivePath"
    try {
        Compress-Archive -Path $source -DestinationPath $archivePath -CompressionLevel Optimal -ErrorAction Stop
        $size = [math]::Round((Get-Item $archivePath).Length / 1MB, 2)
        Write-Log "Completato: $archiveName ($size MB)"
    }
    catch {
        Write-Log "ERRORE backup $source`: $_"
    }
}

# Rotazione: eliminare backup vecchi
Write-Log "Rotazione backup (> $RetainDays giorni)..."
$cutoff = (Get-Date).AddDays(-$RetainDays)
$oldBackups = Get-ChildItem -Path $DestinationPath -Filter "*.zip" |
    Where-Object { $_.LastWriteTime -lt $cutoff }

foreach ($old in $oldBackups) {
    try {
        Remove-Item $old.FullName -Force -ErrorAction Stop
        Write-Log "Eliminato vecchio backup: $($old.Name)"
    }
    catch {
        Write-Log "ERRORE eliminazione $($old.Name): $_"
    }
}

Write-Log "=== BACKUP COMPLETATO ==="
```

### Script 6 — Test connettività di rete

```powershell
<#
.SYNOPSIS
    Verifica la connettività di rete verso server e porte specifiche.
#>

#Requires -Version 5.1

param(
    [Parameter(Mandatory)]
    [string[]]$Target,

    [int[]]$Port = @(80, 443, 3389, 5985),

    [int]$TimeoutMs = 3000
)

$results = foreach ($host_ in $Target) {
    # Ping ICMP
    $ping = Test-Connection $host_ -Count 2 -Quiet -ErrorAction SilentlyContinue

    # Test porte TCP
    $portResults = foreach ($p in $Port) {
        try {
            $tcp = [System.Net.Sockets.TcpClient]::new()
            $connect = $tcp.BeginConnect($host_, $p, $null, $null)
            $success = $connect.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
            if ($success) { $tcp.EndConnect($connect) }
            $tcp.Close()

            [PSCustomObject]@{
                Port   = $p
                Status = if ($success) { "Open" } else { "Filtered" }
            }
        }
        catch {
            [PSCustomObject]@{
                Port   = $p
                Status = "Closed"
            }
        }
    }

    # DNS
    $dns = try {
        [System.Net.Dns]::GetHostEntry($host_).AddressList[0].IPAddressToString
    } catch { "Unresolved" }

    [PSCustomObject]@{
        Target    = $host_
        IP        = $dns
        Ping      = if ($ping) { "OK" } else { "FAIL" }
        Ports     = ($portResults | ForEach-Object { "$($_.Port):$($_.Status)" }) -join ", "
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

$results | Format-Table -AutoSize -Wrap
```

### Script 7 — Gestione massiva utenti AD da CSV

```powershell
<#
.SYNOPSIS
    Crea, modifica o disabilita utenti AD in blocco da un file CSV.
.DESCRIPTION
    Il CSV deve avere le colonne: Action, SamAccountName, GivenName, Surname,
    Department, Title, OU, Password (solo per Create).
    Action: Create, Modify, Disable, Enable
#>

#Requires -Version 5.1
#Requires -Modules ActiveDirectory

param(
    [Parameter(Mandatory)]
    [ValidateScript({ Test-Path $_ })]
    [string]$CsvPath,

    [switch]$WhatIf
)

$users = Import-Csv $CsvPath
$results = @()

foreach ($user in $users) {
    $result = [PSCustomObject]@{
        Action         = $user.Action
        SamAccountName = $user.SamAccountName
        Status         = "Unknown"
        Details        = ""
    }

    try {
        switch ($user.Action) {
            "Create" {
                $upn = "$($user.SamAccountName)@$((Get-ADDomain).DNSRoot)"
                $params = @{
                    Name              = "$($user.GivenName) $($user.Surname)"
                    SamAccountName    = $user.SamAccountName
                    UserPrincipalName = $upn
                    GivenName         = $user.GivenName
                    Surname           = $user.Surname
                    Department        = $user.Department
                    Title             = $user.Title
                    Path              = $user.OU
                    AccountPassword   = ConvertTo-SecureString $user.Password -AsPlainText -Force
                    Enabled           = $true
                    ChangePasswordAtLogon = $true
                }
                if ($WhatIf) {
                    $result.Status = "WhatIf"
                    $result.Details = "Creerebbe utente $upn in $($user.OU)"
                } else {
                    New-ADUser @params -ErrorAction Stop
                    $result.Status = "OK"
                    $result.Details = "Utente creato"
                }
            }
            "Modify" {
                $setParams = @{ Identity = $user.SamAccountName }
                if ($user.Department) { $setParams.Department = $user.Department }
                if ($user.Title)      { $setParams.Title = $user.Title }
                if ($WhatIf) {
                    $result.Status = "WhatIf"
                    $result.Details = "Modificherebbe: $($setParams.Keys -join ', ')"
                } else {
                    Set-ADUser @setParams -ErrorAction Stop
                    $result.Status = "OK"
                    $result.Details = "Utente modificato"
                }
            }
            "Disable" {
                if ($WhatIf) {
                    $result.Status = "WhatIf"
                    $result.Details = "Disabiliterebbe l'account"
                } else {
                    Disable-ADAccount -Identity $user.SamAccountName -ErrorAction Stop
                    $result.Status = "OK"
                    $result.Details = "Account disabilitato"
                }
            }
            "Enable" {
                if ($WhatIf) {
                    $result.Status = "WhatIf"
                    $result.Details = "Abiliterebbe l'account"
                } else {
                    Enable-ADAccount -Identity $user.SamAccountName -ErrorAction Stop
                    $result.Status = "OK"
                    $result.Details = "Account abilitato"
                }
            }
            default {
                $result.Status = "SKIP"
                $result.Details = "Azione non riconosciuta: $($user.Action)"
            }
        }
    }
    catch {
        $result.Status = "ERROR"
        $result.Details = $_.Exception.Message
    }

    $results += $result
}

$results | Format-Table -AutoSize
$summary = $results | Group-Object Status | Select-Object Name, Count
Write-Output "`nRiepilogo:"
$summary | Format-Table -AutoSize
```

### Script 8 — Monitor eventi di sicurezza in tempo reale

```powershell
<#
.SYNOPSIS
    Monitora eventi di sicurezza critici in tempo reale dal Security Event Log.
#>

#Requires -Version 5.1
#Requires -RunAsAdministrator

param(
    [int]$PollIntervalSeconds = 10,
    [string]$LogFile = "C:\Logs\SecurityMonitor_$(Get-Date -Format 'yyyyMMdd').log"
)

# Event ID da monitorare
$criticalEvents = @{
    4625 = "Logon fallito"
    4740 = "Account bloccato"
    4720 = "Account utente creato"
    4726 = "Account utente eliminato"
    4732 = "Membro aggiunto a gruppo locale"
    4756 = "Membro aggiunto a gruppo universale"
    4728 = "Membro aggiunto a gruppo globale"
    4735 = "Gruppo locale modificato"
    4648 = "Logon con credenziali esplicite"
    1102 = "Audit log cancellato"
}

$eventIds = $criticalEvents.Keys
$lastCheck = (Get-Date).AddSeconds(-$PollIntervalSeconds)

Write-Output "Monitoraggio eventi di sicurezza avviato..."
Write-Output "Event ID monitorati: $($eventIds -join ', ')"
Write-Output "Intervallo: ogni $PollIntervalSeconds secondi"
Write-Output "Log: $LogFile"
Write-Output "Premi Ctrl+C per interrompere.`n"

while ($true) {
    $now = Get-Date
    try {
        $events = Get-WinEvent -FilterHashtable @{
            LogName   = 'Security'
            Id        = $eventIds
            StartTime = $lastCheck
            EndTime   = $now
        } -ErrorAction SilentlyContinue

        foreach ($evt in $events) {
            $description = $criticalEvents[[int]$evt.Id]
            $detail = switch ($evt.Id) {
                4625 { "Account: $($evt.Properties[5].Value), IP: $($evt.Properties[19].Value)" }
                4740 { "Account: $($evt.Properties[0].Value), Sorgente: $($evt.Properties[1].Value)" }
                4720 { "Nuovo account: $($evt.Properties[0].Value), Creato da: $($evt.Properties[4].Value)" }
                4726 { "Account eliminato: $($evt.Properties[0].Value)" }
                default { "Vedi Event Viewer per dettagli" }
            }

            $logEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [ID:$($evt.Id)] $description - $detail"
            Add-Content -Path $LogFile -Value $logEntry
            Write-Warning $logEntry
        }
    }
    catch {
        # Nessun evento nel periodo, o errore di accesso
    }

    $lastCheck = $now
    Start-Sleep -Seconds $PollIntervalSeconds
}
```

### Script 9 — Report performance sistema

```powershell
<#
.SYNOPSIS
    Raccoglie metriche di performance del sistema e genera un report.
#>

#Requires -Version 5.1

param(
    [string]$ComputerName = $env:COMPUTERNAME,
    [string]$OutputPath   = "C:\Reports\PerfReport_$(Get-Date -Format 'yyyyMMdd_HHmmss').html"
)

Write-Verbose "Raccolta metriche da $ComputerName..."

# OS Info
$os = Get-CimInstance Win32_OperatingSystem -ComputerName $ComputerName
$cs = Get-CimInstance Win32_ComputerSystem -ComputerName $ComputerName
$cpu = Get-CimInstance Win32_Processor -ComputerName $ComputerName

# Uptime
$uptime = (Get-Date) - $os.LastBootUpTime

# Memoria
$totalMemGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
$freeMemGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
$usedMemGB = [math]::Round($totalMemGB - $freeMemGB, 2)
$memPercent = [math]::Round(($usedMemGB / $totalMemGB) * 100, 1)

# Dischi
$disks = Get-CimInstance Win32_LogicalDisk -ComputerName $ComputerName -Filter "DriveType=3" |
    Select-Object DeviceID,
    @{N='TotalGB'; E={[math]::Round($_.Size/1GB,2)}},
    @{N='FreeGB'; E={[math]::Round($_.FreeSpace/1GB,2)}},
    @{N='UsedPercent'; E={[math]::Round((1-($_.FreeSpace/$_.Size))*100,1)}}

# Top processi per CPU
$topCPU = Get-Process -ComputerName $ComputerName -ErrorAction SilentlyContinue |
    Sort-Object CPU -Descending |
    Select-Object -First 10 Name, Id, CPU,
    @{N='MemMB'; E={[math]::Round($_.WorkingSet64/1MB,1)}}

# Top processi per memoria
$topMem = Get-Process -ComputerName $ComputerName -ErrorAction SilentlyContinue |
    Sort-Object WorkingSet64 -Descending |
    Select-Object -First 10 Name, Id,
    @{N='MemMB'; E={[math]::Round($_.WorkingSet64/1MB,1)}},
    @{N='CPU'; E={[math]::Round($_.CPU,2)}}

# Generare HTML
$head = @"
<style>
    body { font-family: Segoe UI, sans-serif; margin: 20px; background: #f5f5f5; }
    .card { background: white; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    table { border-collapse: collapse; width: 100%; }
    th { background: #34495e; color: white; padding: 10px; text-align: left; }
    td { padding: 8px; border-bottom: 1px solid #eee; }
    h1 { color: #2c3e50; } h2 { color: #34495e; }
    .metric { font-size: 2em; font-weight: bold; color: #2c3e50; }
    .label { color: #7f8c8d; font-size: 0.9em; }
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }
    .warn { color: #e67e22; } .crit { color: #e74c3c; }
</style>
"@

$memClass = if ($memPercent -gt 90) { "crit" } elseif ($memPercent -gt 75) { "warn" } else { "" }

$htmlBody = @"
<h1>Performance Report - $ComputerName</h1>
<p>Generato: $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')</p>

<div class="card">
<h2>Sistema</h2>
<div class="grid">
<div><div class="label">OS</div><div>$($os.Caption)</div></div>
<div><div class="label">Uptime</div><div>$($uptime.Days)g $($uptime.Hours)h $($uptime.Minutes)m</div></div>
<div><div class="label">CPU</div><div>$($cpu.Name)</div></div>
<div><div class="label">Core / Thread</div><div>$($cpu.NumberOfCores) / $($cpu.NumberOfLogicalProcessors)</div></div>
</div>
</div>

<div class="card">
<h2>Memoria</h2>
<div class="metric $memClass">$memPercent% utilizzata</div>
<p>$usedMemGB GB usati su $totalMemGB GB totali ($freeMemGB GB liberi)</p>
</div>

<div class="card">
<h2>Dischi</h2>
$($disks | ConvertTo-Html -Fragment | Out-String)
</div>

<div class="card">
<h2>Top 10 Processi per CPU</h2>
$($topCPU | ConvertTo-Html -Fragment | Out-String)
</div>

<div class="card">
<h2>Top 10 Processi per Memoria</h2>
$($topMem | ConvertTo-Html -Fragment | Out-String)
</div>
"@

ConvertTo-Html -Head $head -Body $htmlBody -Title "Performance Report" |
    Out-File $OutputPath -Encoding UTF8

Write-Output "Report salvato: $OutputPath"
```

### Script 10 — Sincronizzazione cartelle con verifica integrità

```powershell
<#
.SYNOPSIS
    Sincronizza il contenuto di una cartella sorgente in una destinazione
    verificando l'integrità tramite hash SHA256.
.DESCRIPTION
    Confronta i file tra sorgente e destinazione usando hash.
    Copia solo file nuovi o modificati. Opzionalmente rimuove file
    dalla destinazione che non esistono più nella sorgente.
#>

#Requires -Version 5.1

param(
    [Parameter(Mandatory)]
    [ValidateScript({ Test-Path $_ -PathType Container })]
    [string]$Source,

    [Parameter(Mandatory)]
    [string]$Destination,

    [switch]$Mirror,       # Rimuove file extra dalla destinazione
    [switch]$WhatIf,
    [string]$LogFile = "C:\Logs\Sync_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $entry -ErrorAction SilentlyContinue
    switch ($Level) {
        "ERROR"   { Write-Error $Message }
        "WARNING" { Write-Warning $Message }
        default   { Write-Verbose $Message }
    }
}

# Creare destinazione
if (-not (Test-Path $Destination)) {
    if ($WhatIf) {
        Write-Log "[WhatIf] Creerebbe directory: $Destination"
    } else {
        New-Item -Path $Destination -ItemType Directory -Force | Out-Null
        Write-Log "Creata directory: $Destination"
    }
}

$stats = @{ Copied = 0; Updated = 0; Skipped = 0; Deleted = 0; Errors = 0; BytesCopied = 0 }

Write-Log "=== INIZIO SINCRONIZZAZIONE ==="
Write-Log "Sorgente: $Source"
Write-Log "Destinazione: $Destination"
Write-Log "Mirror: $Mirror | WhatIf: $WhatIf"

# Scansione sorgente
$sourceFiles = Get-ChildItem -Path $Source -Recurse -File
Write-Log "File in sorgente: $($sourceFiles.Count)"

foreach ($file in $sourceFiles) {
    $relativePath = $file.FullName.Substring($Source.TrimEnd('\').Length)
    $destFile = Join-Path $Destination $relativePath

    $destDir = Split-Path $destFile -Parent
    if (-not (Test-Path $destDir)) {
        if (-not $WhatIf) {
            New-Item -Path $destDir -ItemType Directory -Force | Out-Null
        }
    }

    $shouldCopy = $false
    $action = ""

    if (-not (Test-Path $destFile)) {
        $shouldCopy = $true
        $action = "NEW"
    } else {
        $srcHash = (Get-FileHash $file.FullName -Algorithm SHA256).Hash
        $dstHash = (Get-FileHash $destFile -Algorithm SHA256).Hash
        if ($srcHash -ne $dstHash) {
            $shouldCopy = $true
            $action = "UPDATED"
        }
    }

    if ($shouldCopy) {
        try {
            $sizeKB = [math]::Round($file.Length / 1KB, 2)
            if ($WhatIf) {
                Write-Log "[WhatIf] $action`: $relativePath ($sizeKB KB)"
            } else {
                Copy-Item $file.FullName -Destination $destFile -Force -ErrorAction Stop
                Write-Log "$action`: $relativePath ($sizeKB KB)"
            }
            $stats.BytesCopied += $file.Length
            if ($action -eq "NEW") { $stats.Copied++ } else { $stats.Updated++ }
        }
        catch {
            Write-Log "ERRORE copia $relativePath`: $_" "ERROR"
            $stats.Errors++
        }
    } else {
        $stats.Skipped++
    }
}

# Mirror: rimuovere file extra dalla destinazione
if ($Mirror) {
    $destFiles = Get-ChildItem -Path $Destination -Recurse -File
    foreach ($dFile in $destFiles) {
        $relativePath = $dFile.FullName.Substring($Destination.TrimEnd('\').Length)
        $srcEquiv = Join-Path $Source $relativePath
        if (-not (Test-Path $srcEquiv)) {
            try {
                if ($WhatIf) {
                    Write-Log "[WhatIf] DELETED: $relativePath"
                } else {
                    Remove-Item $dFile.FullName -Force -ErrorAction Stop
                    Write-Log "DELETED: $relativePath"
                }
                $stats.Deleted++
            }
            catch {
                Write-Log "ERRORE eliminazione $relativePath`: $_" "ERROR"
                $stats.Errors++
            }
        }
    }
}

$totalMB = [math]::Round($stats.BytesCopied / 1MB, 2)
Write-Log "=== SINCRONIZZAZIONE COMPLETATA ==="
Write-Log "Nuovi: $($stats.Copied) | Aggiornati: $($stats.Updated) | Invariati: $($stats.Skipped) | Eliminati: $($stats.Deleted) | Errori: $($stats.Errors) | Trasferiti: $totalMB MB"

Write-Output "`nRiepilogo sincronizzazione:"
Write-Output "  Nuovi:      $($stats.Copied)"
Write-Output "  Aggiornati: $($stats.Updated)"
Write-Output "  Invariati:  $($stats.Skipped)"
Write-Output "  Eliminati:  $($stats.Deleted)"
Write-Output "  Errori:     $($stats.Errors)"
Write-Output "  Trasferiti: $totalMB MB"
Write-Output "  Log: $LogFile"
```

## Esercizi

1. Spiegare la differenza concettuale tra pipeline text-based (bash) e pipeline object-based (PowerShell), con un esempio pratico per ciascuna.
2. Scrivere uno script PowerShell che enumeri tutti i servizi in stato "Running" su una macchina remota, filtri quelli il cui nome inizia con "Win", e esporti il risultato in CSV.
3. Un collega ha scritto uno script che funziona in Windows PowerShell 5.1 ma fallisce in PowerShell 7. Lo script usa `Get-WmiObject`. Diagnosticare il problema e proporre la correzione.
4. Progettare un modulo PowerShell riutilizzabile per la gestione degli utenti AD: definire le funzioni pubbliche, i parametri obbligatori, e la strategia di firma del modulo.

## Auto-valutazione

<details><summary>1. Qual è la triade di cmdlet per la discovery in PowerShell?</summary>
`Get-Command` (trova cmdlet disponibili), `Get-Help` (mostra documentazione), `Get-Member` (ispeziona proprietà e metodi degli oggetti nella pipeline). Riferimento: sezione «Fondamenti PowerShell».
</details>

<details><summary>2. Cosa sono i PSDrive e a cosa servono i Provider?</summary>
I Provider espongono data store diversi (Registry, filesystem, certificati, variabili) come se fossero filesystem. I PSDrive sono le "unità" montate da ciascun provider (es. HKLM:, Cert:, Env:). Riferimento: sezione «Providers e PSDrives».
</details>

<details><summary>3. Come si gestiscono gli errori in PowerShell?</summary>
Con `try/catch/finally` per errori terminating e con `-ErrorAction Stop` per convertire errori non-terminating in terminating. `$ErrorActionPreference` controlla il comportamento globale. Riferimento: sezione «Error Handling».
</details>

<details><summary>4. Qual è la differenza tra ForEach-Object e foreach statement?</summary>
`ForEach-Object` è un cmdlet che opera nella pipeline, elabora un oggetto alla volta (basso consumo memoria). Il `foreach` statement carica tutta la collezione in memoria prima di iterare (più veloce su collezioni piccole). Riferimento: sezione «ForEach-Object».
</details>

<details><summary>5. Come si crea e importa un modulo PowerShell?</summary>
Creare una directory con il nome del modulo, un file .psm1 con le funzioni, e un manifest .psd1 con `New-ModuleManifest`. Importare con `Import-Module`. Per distribuzione enterprise, pubblicare su una PSGallery privata. Riferimento: sezione «Modules».
</details>

<details><summary>6. Che differenza c'è tra PowerShell 7+ e Windows PowerShell 5.1?</summary>
PowerShell 7+ è cross-platform, basato su .NET (Core/8+), usa `pwsh.exe`. Windows PowerShell 5.1 è solo Windows, basato su .NET Framework 4.x, usa `powershell.exe`. Alcuni moduli legacy (es. quelli che usano `Get-WmiObject`) funzionano solo in 5.1. Riferimento: sezione «Versioni e Installazione».
</details>

<details><summary>7. Cosa fa il cmdlet Measure-Object e in quali scenari è utile?</summary>
Calcola statistiche su proprietà numeriche (Count, Sum, Average, Min, Max) o conta righe/parole/caratteri di testo. Utile per report, audit e analisi di log. Riferimento: sezione «Measure-Object».
</details>

## Letture primarie consigliate

- Microsoft Learn — PowerShell Documentation: <https://learn.microsoft.com/en-us/powershell/> (consultato: 2026-05-23)
- Microsoft Learn — About Modules: <https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_modules> (consultato: 2026-05-23)
- PowerShell Gallery: <https://www.powershellgallery.com/> (consultato: 2026-05-23)
- Don Jones, Jeffrey Hicks — Learn PowerShell in a Month of Lunches (Manning): <https://www.manning.com/books/learn-powershell-in-a-month-of-lunches> (consultato: 2026-05-23)

## Collegamenti incrociati

- [01-active-directory.md](01-active-directory.md) — Oggetti AD gestiti via PowerShell
- [22-powershell-scripting-avanzato.md](22-powershell-scripting-avanzato.md) — Scripting avanzato e DSC
- [14-batch-scripting.md](14-batch-scripting.md) — Batch scripting legacy (confronto)
- [03-ruoli-server.md](03-ruoli-server.md) — Install-WindowsFeature e gestione ruoli
- [09-monitoraggio-performance.md](09-monitoraggio-performance.md) — Performance counters via PowerShell

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| Cmdlet | Comando PowerShell nativo, segue la convenzione Verbo-Nome |
| Pipeline | Catena di comandi dove l'output di uno è l'input del successivo (oggetti, non testo) |
| PSDrive | Unità virtuale esposta da un Provider PowerShell (es. HKLM:, Cert:) |
| Provider | Componente che espone un data store come filesystem navigabile |
| Module | Package di cmdlet, funzioni e variabili distribuibile e importabile |
| Manifest (.psd1) | File di metadati di un modulo: versione, autore, dipendenze, funzioni esportate |
| Splatting | Tecnica per passare parametri a un cmdlet tramite hashtable (@params) |
| ScriptBlock | Blocco di codice delimitato da `{ }`, eseguibile come lambda o passabile a cmdlet |
| Remoting (PSSession) | Esecuzione di comandi su macchine remote tramite WinRM/SSH |
| ErrorAction | Parametro comune che controlla il comportamento in caso di errore (Stop, Continue, SilentlyContinue) |
