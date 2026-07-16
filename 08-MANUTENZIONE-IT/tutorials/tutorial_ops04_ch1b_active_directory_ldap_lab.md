# Tutorial: Active Directory Avanzato e LDAP — Hands-On Lab

> **Documento di riferimento:** `04-servizi-infrastruttura.md` (sezioni Active Directory e LDAP)
> **Dominio:** Infrastruttura di Rete — Identity e Directory Services
> **Ambito:** Manutenzione AD (replica, FSMO, NTDS.dit, SYSVOL), pulizia oggetti obsoleti, LDAP Security (Signing, LDAPS), Group Policy audit, AD Security Hardening
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio-Avanzato — richiede ops03a (Windows Server), ops04a (DNS/DHCP/NTP)
> **Prerequisiti:** DC-LAB-01 promosso a Domain Controller con AD DS installato, WKS-LAB-01 aggiunto al dominio
> **Ambiente:** Principalmente DC-LAB-01; SRV-LINUX-01 per test LDAP da Linux

---

## Lab Environment Setup

```powershell
# Da DC-LAB-01 — verifica pre-lab
Write-Host "=== VERIFICA PRE-LAB AD ===" -ForegroundColor Cyan

# AD DS installato e funzionante?
$adws = Get-Service ADWS -ErrorAction SilentlyContinue
if ($adws.Status -eq "Running") { Write-Host "[OK] Active Directory Web Services: Running" -ForegroundColor Green }
else { Write-Host "[ERR] ADWS non in esecuzione" -ForegroundColor Red }

# DC risponde ai comandi AD?
try {
    $domain = Get-ADDomain -ErrorAction Stop
    Write-Host "[OK] Dominio: $($domain.DNSRoot)" -ForegroundColor Green
    Write-Host "[OK] PDC Emulator: $($domain.PDCEmulator)" -ForegroundColor Green
} catch {
    Write-Host "[ERR] Impossibile contattare AD: $_" -ForegroundColor Red
}

# Ruoli FSMO
netdom query fsmo
```

Output atteso:
```
[OK] Active Directory Web Services: Running
[OK] Dominio: lab.local
[OK] PDC Emulator: DC-LAB-01.lab.local
Schema master          DC-LAB-01.lab.local
Naming master          DC-LAB-01.lab.local
PDC                    DC-LAB-01.lab.local
RID pool manager       DC-LAB-01.lab.local
Infrastructure master  DC-LAB-01.lab.local
```

In un singolo DC (il nostro lab) tutti i ruoli FSMO risiedono sullo stesso server — in produzione sono distribuiti tra DC diversi.

---

## PART A: FONDAMENTI — Active Directory come Cuore dell'Identità Aziendale

> Immagina una grande università. C'è un ufficio centrale che gestisce l'identità di ogni studente, professore e dipendente: sa chi sei (autenticazione), cosa puoi fare (autorizzazione), a quali gruppi appartieni (gruppi di sicurezza). Ogni risorsa dell'università — aule, laboratori, biblioteca, Wi-Fi — verifica con quell'ufficio se hai il diritto di accedere. Active Directory è quell'ufficio centrale per l'infrastruttura IT aziendale. Se l'ufficio chiude, nessuno entra da nessuna parte.

---

### Concetto A1: Active Directory — Struttura e Componenti Critici

**La gerarchia AD in tre livelli:**

```
FORESTA (Forest)
├── Schema: definisce tutti i tipi di oggetti possibili in AD
│   └── Schema Master gestisce le modifiche allo schema
└── DOMINIO (Domain): lab.local
    ├── Objects: Users, Computers, Groups, GPO, OUs
    ├── Database: NTDS.dit (il cuore di tutto)
    ├── SYSVOL: GPO files, script di logon (replicati tra DC)
    └── UNITÀ ORGANIZZATIVE (OU)
        ├── OU=Users
        │   ├── CN=Amministratore
        │   └── CN=lab-user
        ├── OU=Computers
        │   └── CN=WKS-LAB-01
        └── OU=Servers
            └── CN=SRV-LINUX-01 (se aggiunto)
```

**Il database NTDS.dit — cosa contiene:**

```
NTDS.dit (file database Extensible Storage Engine)
├── Schema partition: definizioni di tutti gli oggetti AD
├── Configuration partition: topologia AD, siti, servizi
├── Domain partition: tutti gli oggetti del dominio (utenti, computer, GPO)
└── Global Catalog: sottoinsieme di tutti gli oggetti della foresta
    (solo in un DC designato come Global Catalog)

Dimensione tipica:
  - Piccola azienda (< 1.000 oggetti): 50-200 MB
  - Media azienda (10.000 oggetti): 500 MB - 2 GB
  - Grande azienda (100.000+ oggetti): 5-20 GB
```

**I 5 ruoli FSMO — perché esistono:**

> **Analogia.** In un'azienda, alcune decisioni devono essere prese da una singola persona con autorità — non si può fare votazione: il CEO firma i contratti, il CFO approva i budget. I ruoli FSMO (Flexible Single Master Operations) sono quei "firmatari" di Active Directory: operazioni che non possono essere eseguite in parallelo da più DC senza rischio di conflitti.

| Ruolo | Chi lo tiene | Quando è critico |
|---|---|---|
| **Schema Master** | Foresta | Solo durante estensioni schema (Es: install Exchange) |
| **Domain Naming Master** | Foresta | Solo durante aggiunta/rimozione domini |
| **PDC Emulator** | Dominio | **SEMPRE** — gestisce orario, blocchi account, cambio password |
| **RID Master** | Dominio | Creazione nuovi oggetti (assegna RID ai DC) |
| **Infrastructure Master** | Dominio | Cross-domain object references |

Il PDC Emulator è il più critico in produzione — si occupa di:
- Sincronizzazione dell'orario per tutto il dominio (vedi NTP in ops04a)
- Cambio password prioritario (se un utente cambia password, il cambio è immediato su PDC)
- Blocco degli account (gestisce la propagazione del lockout)

---

### Concetto A2: Replica AD — Come i Dati si Propagano tra DC

> **Analogia.** Immagina due banche con gli stessi conti correnti. Se aggiorno il saldo su una filiale, l'altra filiale deve saperlo — ma non subito (sarebbe troppo costoso aggiornare in tempo reale ogni operazione). Invece, ogni pochi minuti le due filiali si "sincronizzano" e si scambiano le modifiche. Active Directory funziona così: le modifiche si propagano tra i Domain Controller via replica, non in tempo reale ma entro pochi minuti (di default).

**Come funziona la replica AD:**

```
Modifica su DC-LAB-01 (es. nuova password utente)
         ↓
La modifica viene assegnata un Update Sequence Number (USN)
USN = numero progressivo che identifica ogni modifica
         ↓
DC-LAB-01 notifica i DC "partner" che ha nuovi aggiornamenti
         ↓
I DC partner richiedono la modifica (pull-based replication)
         ↓
La modifica si propaga attraverso tutti i DC
         ↓
Tempo tipico: < 15 secondi in una LAN (replication interval = 15 sec)
              < 3 ore tra siti geografici (inter-site replication)
```

**Problemi di replica — i più comuni:**

```
1. Lingering Objects (oggetti fantasma)
   Causa: Un DC è stato offline > 60 giorni (oltre il tombstone lifetime)
   Effetto: Il DC ha oggetti che gli altri hanno eliminato
   Soluzione: repadmin /removelingeringobjects

2. Errore di replica (Event ID 1864, 2042)
   Causa: DC offline troppo a lungo, problemi di rete
   Diagnosi: repadmin /replsummary | findstr /i "error\|fail"
   Soluzione: dipende dall'errore (rete, DNS, certificati)

3. SYSVOL non replicato
   Causa: problemi DFSR (Distributed File System Replication)
   Effetto: GPO applicate in modo inconsistente tra DC
   Diagnosi: dfsrdiag pollad
   Soluzione: dfsrdiag syncnow /RGName:"Domain System Volume"
```

---

### Concetto A3: LDAP — Il Linguaggio di Active Directory

> **Analogia.** Active Directory è un grande scaffale di archivio. LDAP (Lightweight Directory Access Protocol) è il linguaggio che usi per comunicare con il bibliotecario: "Dammi tutti gli utenti la cui cognome inizia con 'M'", "Aggiungi questa persona al gruppo 'Finanza'", "Cambia l'email di questo utente". LDAP è al DNS e AD quello che SQL è ai database — il protocollo di query.

**La struttura DN (Distinguished Name) — come AD identifica gli oggetti:**

```
Ogni oggetto AD ha un DN univoco che descrive la sua posizione:

CN=Administrator,CN=Users,DC=lab,DC=local
│                │           │
│                │           └── DC = Domain Component (parte del dominio)
│                └── CN = Container (Users)
└── CN = Common Name (l'oggetto stesso)

Esempio utente in una OU:
CN=lab-user,OU=Users,DC=lab,DC=local

Esempio computer:
CN=WKS-LAB-01,OU=Computers,DC=lab,DC=local

Esempio GPO:
CN={GUID},CN=Policies,CN=System,DC=lab,DC=local
```

**LDAP Security — i tre livelli di protezione:**

```
LIVELLO 1: LDAP semplice (porta 389) — NO crittografia
  Tutto in chiaro sul filo — password visibili in Wireshark
  Accettabile SOLO in reti completamente isolate e fidate

LIVELLO 2: LDAP con Signing (porta 389 + SASL)
  I messaggi LDAP sono firmati digitalmente
  Previene la manomissione (integrità), ma non nasconde il contenuto
  Configurazione raccomandata: LDAPServerIntegrity = 2 (Require)

LIVELLO 3: LDAPS (porta 636, TLS) — MASSIMA sicurezza
  Tutto il traffico LDAP è cifrato con TLS
  Previene intercettazione E manomissione
  Obbligatorio per GDPR, PCI-DSS, ISO 27001
```

**Event ID 2889 — l'allarme silenzioso:**

```
Event ID 2889 nel log "Directory Service":
"A client attempted to perform a simple LDAP bind that 
 did not include LDAP signing"

Questo evento appare ogni volta che un'applicazione si connette
ad AD senza richiedere la firma LDAP. Comune quando:
- Applicazioni legacy ancora usano LDAP non firmato
- Scanner di vulnerabilità eseguono test
- Alcune versioni di Linux/Mac usano ldap:// invece di ldaps://
```

---

### Concetto A4: Group Policy — Il Sistema di Configurazione Centralizzata

> **Analogia.** Un'azienda con 500 computer non può andare su ogni macchina a configurare il firewall, le restrizioni USB, la complessità della password. Le Group Policy (GPO) sono come un regolamento aziendale pubblicato una sola volta che si applica automaticamente a tutti. Modifichi la policy, e la prossima volta che un utente fa login la riceve.

**Come le GPO si applicano — l'ordine LSDOU:**

```
L = Local (GPO locale del computer)
S = Site (GPO del sito AD — basate sulla subnet)
D = Domain (GPO collegate al dominio)
O = OU (GPO collegate alle OU — più specifiche vincono)

Le GPO si applicano dall'ultimo all'ultimo: Local → Site → Domain → OU
Un'impostazione in OU sovrascrive quella in Domain (salvo "Enforced")

Eccezioni importanti:
- Enforced (No Override): la GPO superiore non può essere sovrascritta
- Block Inheritance: l'OU blocca GPO dalle OU genitore (non blocca Enforced)
```

**RSoP — Resultant Set of Policy:**

```
Con N GPO collegate, come sapere quale impostazione "vince"?
RSoP (Resultant Set of Policy) calcola il risultato finale.

Strumenti:
  gpresult /h report.html     → HTML con tutte le policy applicate
  gpresult /r                 → sommario testuale veloce
  Get-GPResultantSetOfPolicy  → PowerShell

Perché è utile:
  "Perché questo utente non riesce a usare USB?"
  → gpresult mostra quale GPO ha bloccato l'USB
  "Perché questa computer ha le impostazioni del firewall sbagliate?"
  → gpresult mostra l'ordine di applicazione delle GPO
```

---

### Concetto A5: AD Security — Perché AD è il Target Principale degli Attaccanti

> **Perché mi interessa?** Active Directory è il "master key" dell'infrastruttura aziendale. Chi controlla AD, controlla tutto: può creare account admin, accedere a qualsiasi file, leggere qualsiasi email, disabilitare qualsiasi servizio. Il 90% degli attacchi ransomware moderni iniziano con una compromissione di AD. Mantenere AD sicuro non è "nice to have" — è la differenza tra un'azienda operativa e una che paga riscatto.

**I vettori di attacco AD più comuni:**

```
1. Pass-the-Hash (PtH)
   Attaccante ruba l'hash NTLM di un account
   → Usa l'hash per autenticarsi senza conoscere la password
   Prevenzione: disabilita NTLM, usa Kerberos + credential guard

2. Kerberoasting
   Attaccante richiede ticket TGS per account di servizio (SPN)
   → Crack offline del ticket (se password debole)
   Prevenzione: account di servizio con password ≥ 25 caratteri + GMSA

3. DCSync
   Attaccante ha privilegi di "Replicating Directory Changes All"
   → Può eseguire una replica AD e scaricare tutti gli hash
   Prevenzione: monitora Event ID 4662 con these_specific_GUIDs

4. Kerberos Unconstrained Delegation
   Server con delega non vincolata può impersonare qualsiasi utente
   → Attaccante che compromette quel server = Domain Admin
   Prevenzione: usa Constrained/Resource-Based Constrained Delegation
```

**I 3 gruppi più pericolosi da monitorare:**

```
Domain Admins    → accesso totale al dominio
Enterprise Admins → accesso totale alla foresta
Schema Admins    → può modificare la struttura di AD

Regola d'oro: questi gruppi devono avere il MINIMO indispensabile.
In un'azienda normale, Domain Admins dovrebbe avere 1-3 persone.
Un account di servizio in Domain Admins è sempre sbagliato.
```

---

---

## PART B: OPERAZIONI — Manutenzione Proattiva di Active Directory

---

### Esercizio B1: Verifica Salute AD — dcdiag e repadmin

**Obiettivo.** Eseguire i due strumenti fondamentali per la salute di Active Directory: `dcdiag` (diagnostica del DC) e `repadmin` (stato della replica). Questi sono i primi comandi da eseguire quando si sospetta un problema AD.

**Background.** In produzione con più DC, questi strumenti rivelano problemi di replica, errori DNS, certificati scaduti, e problemi con i ruoli FSMO. Nel nostro lab con un solo DC, molti test non hanno partner con cui comparare — ma è comunque fondamentale imparare la sintassi e il significato dell'output.

---

**Step 1 — dcdiag: la visita medica del Domain Controller**

```powershell
# Su DC-LAB-01 come Administrator

# Test rapido con i test più comuni
dcdiag /test:dns /v
```

Output atteso (primo blocco):
```
Directory Server Diagnosis

Performing initial setup:
   Trying to find home server...
   Home Server = DC-LAB-01
   * Identified AD Forest.
   Done gathering initial info.

Doing initial required tests

   Testing server: Default-First-Site-Name\DC-LAB-01
      Starting test: Connectivity
         ......................... DC-LAB-01 passed test Connectivity
```

```powershell
# Test di replica (in un ambiente multi-DC mostrerebbe gli errori di sync)
dcdiag /test:replications /v

# Verifica ruoli FSMO
dcdiag /test:fsmocheck /v

# Verifica che il DC si stia pubblicizzando correttamente
dcdiag /test:advertising /v

# Test completo (verbose) — richiede 2-3 minuti
dcdiag /v /c /e
```

Interpretazione dell'output:
```
"passed test XXX"  → il test è superato (verde)
"failed test XXX"  → ATTENZIONE — indagare
"warning: XXX"     → warning — non critico ma da monitorare

Test chiave da non ignorare se falliscono:
- Connectivity: il DC non è raggiungibile
- DNS: problemi DNS che impattano AD
- Replications: errori di replica tra DC
- FsmoCheck: ruoli FSMO non raggiungibili
- Advertising: il DC non si pubblicizza ai client
```

---

**Step 2 — repadmin: stato della replica**

```powershell
# Riepilogo della replica per tutti i DC della foresta
repadmin /replsummary
```

Output atteso (con un solo DC, nessun partner):
```
Replication Summary Start Time: 2026-07-15 10:00:00

Beginning data collection for replication summary, this may take awhile:
..................

Source DSA          largest delta    fails/total %%   error
 DC-LAB-01           00h:00m:00s    0 /   0    0

Destination DSA     largest delta    fails/total %%   error
 DC-LAB-01           00h:00m:00s    0 /   0    0

```

Con più DC, la colonna "fails/total" mostrerebbe eventuali errori di replica e la colonna "largest delta" mostrerebbe quanto tempo è passato dall'ultima replica riuscita.

```powershell
# Stato dettagliato per ogni partizione
repadmin /showrepl

# Verifica la coerenza della topologia KCC (Knowledge Consistency Checker)
repadmin /kcc
# KCC ridisegna automaticamente la topologia di replica — eseguire se si aggiunge/rimuove un DC
```

---

**Step 3 — Verifica FSMO e pool RID**

```powershell
# Titolari dei 5 ruoli FSMO
netdom query fsmo

# Via PowerShell
Get-ADDomain | Select-Object PDCEmulator, RIDMaster, InfrastructureMaster
Get-ADForest | Select-Object SchemaMaster, DomainNamingMaster

# Verifica pool RID rimanente
# Se il pool si esaurisce, non si possono creare nuovi oggetti AD
dcdiag /test:ridmanager /v

# Verifica che il PDC Emulator sia raggiungibile
Test-NetConnection -ComputerName (Get-ADDomain).PDCEmulator -Port 389 -InformationLevel Quiet
```

Output atteso per netdom:
```
Schema master          DC-LAB-01.lab.local
Naming master          DC-LAB-01.lab.local
PDC                    DC-LAB-01.lab.local
RID pool manager       DC-LAB-01.lab.local
Infrastructure master  DC-LAB-01.lab.local
The command completed successfully.
```

---

**Step 4 — Verifica SYSVOL e replica DFSR**

```powershell
# Stato della replica SYSVOL
dfsrdiag pollad

# Verifica il contenuto di SYSVOL (GPO policies)
$sysvol = "\\DC-LAB-01\SYSVOL\lab.local\Policies"
$policies = Get-ChildItem -Path $sysvol -Directory
Write-Host "GPO in SYSVOL: $($policies.Count)"
$policies | Select-Object Name, LastWriteTime

# Controlla che il servizio DFSR sia attivo
Get-Service DFSR | Select-Object Name, Status, StartType
```

Output atteso:
```
GPO in SYSVOL: 2  (o più, dipende da quante GPO hai creato)
Name                                    LastWriteTime
----                                    -------------
{6AC1786C-016F-11D2-945F-00C04FB984F9}  (Default Domain Controllers Policy)
{31B2F340-016D-11D2-945F-00C04FB984F9}  (Default Domain Policy)
```

**Checkpoint di verifica B1:**

```powershell
Write-Host "=== VERIFICA SALUTE AD ===" -ForegroundColor Cyan

# 1. Connectivity test
$conn = dcdiag /test:Connectivity 2>&1 | Where-Object { $_ -match "passed|failed" }
if ($conn -match "passed") { Write-Host "[OK] dcdiag /test:Connectivity: passed" -ForegroundColor Green }
else { Write-Host "[ERR] dcdiag Connectivity failed" -ForegroundColor Red }

# 2. FSMO accessibili
$pdc = (Get-ADDomain).PDCEmulator
$pdcOk = Test-NetConnection -ComputerName $pdc -Port 389 -WarningAction SilentlyContinue
if ($pdcOk.TcpTestSucceeded) { Write-Host "[OK] PDC Emulator ($pdc) raggiungibile su porta 389" -ForegroundColor Green }

# 3. DFSR (SYSVOL) attivo
$dfsr = Get-Service DFSR -ErrorAction SilentlyContinue
if ($dfsr.Status -eq "Running") { Write-Host "[OK] Servizio DFSR attivo (SYSVOL replication)" -ForegroundColor Green }
else { Write-Host "[ERR] DFSR non attivo" -ForegroundColor Red }
```

---

### Esercizio B2: Audit Oggetti Obsoleti — Pulizia AD

**Obiettivo.** Identificare utenti inattivi, computer inattivi, gruppi vuoti e account con configurazioni di sicurezza rischiose. Generare report CSV per il responsabile IT.

**Background.** Active Directory accumula entropia: account di ex-dipendenti abilitati, computer reinstallati ma non rimossi dal dominio, gruppi vuoti creati e dimenticati. Questa "sporcizia" aumenta la superficie d'attacco (un account abilitato di ex-dipendente può essere usato da un attaccante) e complica l'amministrazione.

---

**Step 1 — Crea directory per i report**

```powershell
# Crea la directory dei report
New-Item -Path "C:\Reports\AD" -ItemType Directory -Force | Out-Null
Write-Host "[OK] Directory C:\Reports\AD creata"
```

---

**Step 2 — Utenti inattivi da più di 90 giorni**

```powershell
$soglia90 = (Get-Date).AddDays(-90)

# Utenti abilitati che non fanno login da > 90 giorni
$utentiInattivi = Get-ADUser -Filter { 
    LastLogonDate -lt $soglia90 -and Enabled -eq $true 
} -Properties LastLogonDate, EmailAddress, Department, Manager |
    Select-Object `
        Name, SamAccountName, EmailAddress, Department,
        @{N="GiorniInattivo"; E={ ((Get-Date) - ($_.LastLogonDate ?? (Get-Date "2000-01-01"))).Days }},
        LastLogonDate |
    Sort-Object GiorniInattivo -Descending

Write-Host "Utenti abilitati inattivi da >90 giorni: $($utentiInattivi.Count)"
$utentiInattivi | Format-Table -AutoSize

# Esporta CSV
$utentiInattivi | Export-Csv -Path "C:\Reports\AD\utenti_inattivi_$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
Write-Host "[OK] Report salvato in C:\Reports\AD\"
```

---

**Step 3 — Computer inattivi da più di 90 giorni**

```powershell
$computerInattivi = Get-ADComputer -Filter {
    LastLogonDate -lt $soglia90
} -Properties LastLogonDate, OperatingSystem, OperatingSystemVersion |
    Select-Object `
        Name, LastLogonDate, OperatingSystem,
        @{N="GiorniInattivo"; E={ ((Get-Date) - ($_.LastLogonDate ?? (Get-Date "2000-01-01"))).Days }} |
    Sort-Object GiorniInattivo -Descending

Write-Host "Computer inattivi da >90 giorni: $($computerInattivi.Count)"
$computerInattivi | Format-Table -AutoSize

$computerInattivi | Export-Csv -Path "C:\Reports\AD\computer_inattivi_$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
```

---

**Step 4 — Gruppi vuoti**

```powershell
$gruppiVuoti = Get-ADGroup -Filter * -Properties Members, Description |
    Where-Object { $_.Members.Count -eq 0 } |
    Select-Object Name, GroupScope, GroupCategory, Description, @{N="Membri"; E={0}} |
    Sort-Object Name

Write-Host "Gruppi senza membri: $($gruppiVuoti.Count)"
$gruppiVuoti | Format-Table -AutoSize

$gruppiVuoti | Export-Csv -Path "C:\Reports\AD\gruppi_vuoti_$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
```

---

**Step 5 — Account con configurazioni rischiose**

```powershell
Write-Host "`n=== ACCOUNT CON CONFIGURAZIONI RISCHIOSE ===" -ForegroundColor Yellow

# Password che non scade mai (rischio: se compromessa, valida per sempre)
$pwdNoExpire = Get-ADUser -Filter { 
    PasswordNeverExpires -eq $true -and Enabled -eq $true 
} -Properties PasswordNeverExpires, PasswordLastSet |
    Select-Object Name, SamAccountName, PasswordLastSet
    
Write-Host "`n[WARN] Account con 'Password Never Expires' ($($pwdNoExpire.Count)):"
$pwdNoExpire | Format-Table -AutoSize

# Account con Kerberos Unconstrained Delegation
# Questi server possono impersonare qualsiasi utente del dominio
$unconstrained = Get-ADComputer -Filter { 
    TrustedForDelegation -eq $true 
} -Properties TrustedForDelegation, DNSHostName

Write-Host "`n[WARN] Computer con Unconstrained Delegation ($($unconstrained.Count)):"
$unconstrained | Select-Object Name, DNSHostName | Format-Table -AutoSize
# Nota: i DC hanno sempre TrustedForDelegation=True — normale e atteso

# Account AdminCount=1 ma non più in gruppi privilegiati (ACL orfane)
$adminCountOrphans = Get-ADUser -Filter { AdminCount -eq 1 } -Properties AdminCount, MemberOf |
    Where-Object { 
        $groups = $_.MemberOf | ForEach-Object { (Get-ADGroup $_).Name }
        -not ($groups -match "Domain Admins|Enterprise Admins|Schema Admins|Administrators")
    } |
    Select-Object Name, SamAccountName

if ($adminCountOrphans.Count -gt 0) {
    Write-Host "`n[WARN] Account con AdminCount=1 orfani (ACL non corrette): $($adminCountOrphans.Count)"
    $adminCountOrphans | Format-Table
}

# Membri dei gruppi privilegiati
Write-Host "`n[INFO] Membri Domain Admins:"
Get-ADGroupMember "Domain Admins" | Select-Object Name, SamAccountName, ObjectClass | Format-Table
```

---

### Esercizio B3: LDAP Security — Verifica Signing e LDAPS

**Obiettivo.** Verificare la configurazione LDAP Signing e Channel Binding su DC-LAB-01, cercare connessioni LDAP non firmate nel log eventi, e testare LDAPS da SRV-LINUX-01.

**Background.** Senza LDAP Signing, un attaccante in posizione MITM (Man in the Middle) può intercettare o modificare le query LDAP — incluse le operazioni di cambio password. Con Windows Server 2019 e successivi, Microsoft ha iniziato a richiedere LDAP Signing per default.

---

**Step 1 — Verifica configurazione LDAP Signing**

```powershell
# Su DC-LAB-01

# Verifica il livello di LDAP Signing richiesto
$ldapSigning = Get-ItemProperty `
    "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LDAPServerIntegrity" `
    -ErrorAction SilentlyContinue

$level = switch ($ldapSigning.LDAPServerIntegrity) {
    0 { "0 = None (nessuna firma richiesta) — INSICURO" }
    1 { "1 = Negotiated — firma richiesta se supportata" }
    2 { "2 = Required — firma SEMPRE richiesta (raccomandato)" }
    default { "Non configurato (usa default del server)" }
}

Write-Host "LDAP Signing Level: $level"

# Verifica Channel Binding
$channelBinding = Get-ItemProperty `
    "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LdapEnforceChannelBinding" `
    -ErrorAction SilentlyContinue

$cbLevel = switch ($channelBinding.LdapEnforceChannelBinding) {
    0 { "0 = Never enforced" }
    1 { "1 = When supported" }
    2 { "2 = Always enforced (raccomandato)" }
    default { "Non configurato" }
}
Write-Host "LDAP Channel Binding: $cbLevel"
```

---

**Step 2 — Cerca connessioni LDAP non firmate (Event ID 2889)**

```powershell
# Cerca nei log eventi le connessioni LDAP non firmate
$ev2889 = Get-WinEvent -FilterHashtable @{
    LogName = "Directory Service"
    Id = 2889
    StartTime = (Get-Date).AddDays(-30)
} -MaxEvents 20 -ErrorAction SilentlyContinue

if ($ev2889) {
    Write-Host "[WARN] Trovate $($ev2889.Count) connessioni LDAP non firmate (ultimi 30 gg):" -ForegroundColor Yellow
    $ev2889 | Select-Object TimeCreated, 
        @{N="IP_Client"; E={$_.Properties[0].Value}},
        @{N="Account"; E={$_.Properties[1].Value}} |
        Format-Table -AutoSize
} else {
    Write-Host "[OK] Nessuna connessione LDAP non firmata negli ultimi 30 giorni" -ForegroundColor Green
}

# Verifica Event ID 2898 (LDAP notification limit — possibile flooding da applicazioni)
$ev2898 = Get-WinEvent -FilterHashtable @{
    LogName = "Directory Service"
    Id = 2898
    StartTime = (Get-Date).AddDays(-7)
} -MaxEvents 10 -ErrorAction SilentlyContinue

if ($ev2898) {
    Write-Host "[WARN] Event ID 2898 trovati — applicazioni con troppe notifiche LDAP" -ForegroundColor Yellow
}
```

---

**Step 3 — Verifica certificato LDAPS**

Per LDAPS (LDAP over TLS, porta 636), il DC deve avere un certificato valido con il nome del server nel Subject/SAN. In un lab senza CA enterprise, useremo il certificato self-signed installato automaticamente da AD DS.

```powershell
# Verifica certificati del DC con Server Authentication EKU
$certs = Get-ChildItem Cert:\LocalMachine\My |
    Where-Object {
        $_.EnhancedKeyUsageList.FriendlyName -contains "Server Authentication" -and
        $_.NotAfter -gt (Get-Date)
    } |
    Select-Object Subject, Thumbprint, NotAfter, Issuer

Write-Host "`nCertificati validi per LDAPS:"
$certs | Format-List

# Verifica che la porta 636 (LDAPS) sia in ascolto
$ldaps = Test-NetConnection -ComputerName "127.0.0.1" -Port 636 -WarningAction SilentlyContinue
if ($ldaps.TcpTestSucceeded) { 
    Write-Host "[OK] Porta 636 (LDAPS) in ascolto su DC-LAB-01" -ForegroundColor Green
} else {
    Write-Host "[WARN] Porta 636 non in ascolto — LDAPS potrebbe non essere configurato" -ForegroundColor Yellow
    Write-Host "Soluzione: installa un certificato di Server Authentication nel LocalMachine\My store"
}
```

---

**Step 4 — Test LDAPS da SRV-LINUX-01**

```bash
# Su SRV-LINUX-01 via SSH

# Installa ldap-utils
sudo apt install -y ldap-utils

# Test LDAP standard (porta 389) — non crittografato
ldapsearch -H ldap://192.168.56.10 \
    -x \
    -b "DC=lab,DC=local" \
    -D "CN=Administrator,CN=Users,DC=lab,DC=local" \
    -W \
    "(objectClass=user)" cn sAMAccountName \
    -z 5 2>&1 | head -30
```

Se LDAP Signing è impostato a "Required" (livello 2), questo comando fallisce:
```
ldap_bind: Confidentiality required (13)
  additional info: 00002028: LdapErr: DSID-0C09044E, 
  comment: The server requires binds to turn on integrity checking if SSL\TLS are not already active on the connection
```

Questo è il comportamento **corretto** — il server rifiuta connessioni non firmate.

```bash
# Test LDAPS (porta 636) — crittografato
# Nota: in lab con cert self-signed, usa -Z o ignora errori certificato con -k
ldapsearch -H ldaps://192.168.56.10 \
    -x \
    -b "DC=lab,DC=local" \
    -D "CN=Administrator,CN=Users,DC=lab,DC=local" \
    -W \
    "(objectClass=user)" cn sAMAccountName \
    -z 5 \
    -o tls_reqcert=never 2>&1 | head -30
```

---

### Esercizio B4: Group Policy — Audit e Verifica RSoP

**Obiettivo.** Eseguire un audit delle GPO del dominio, identificare GPO non collegate, generare un report HTML, e verificare le policy risultanti su WKS-LAB-01 con gpresult.

**Background.** Le GPO si accumulano nel tempo: si crea una GPO per un progetto, il progetto finisce, la GPO rimane collegata e applica impostazioni che nessuno ricorda più. L'audit periodico delle GPO previene conflitti, riduce la superficie di attacco e semplifica il troubleshooting.

---

**Step 1 — Elenca tutte le GPO con stato e data modifica**

```powershell
# Su DC-LAB-01

# Elenco completo GPO con info chiave
Get-GPO -All |
    Select-Object `
        DisplayName,
        GpoStatus,
        CreationTime,
        ModificationTime,
        @{N="ID"; E={$_.Id.ToString().Substring(0,8) + "..."}} |
    Sort-Object ModificationTime -Descending |
    Format-Table -AutoSize
```

Output atteso (lab con GPO base):
```
DisplayName                        GpoStatus ModificationTime
-----------                        --------- ----------------
Default Domain Controllers Policy  AllSettingsEnabled  2026-07-10 09:00
Default Domain Policy              AllSettingsEnabled  2026-07-10 09:00
```

---

**Step 2 — Identifica GPO non collegate**

```powershell
# GPO senza link (orfane — consumano spazio in SYSVOL e AD)
$orphanGPO = Get-GPO -All | ForEach-Object {
    $gpo = $_
    # Genera report XML e cerca link
    $xml = [xml](Get-GPOReport -Guid $gpo.Id -ReportType XML)
    $ns = @{ gpo = "http://www.microsoft.com/GroupPolicy/Settings" }
    $links = ($xml | Select-Xml -XPath "//gpo:LinksTo" -Namespace $ns).Count
    
    if ($links -eq 0) {
        [PSCustomObject]@{
            Nome = $gpo.DisplayName
            UltimaModifica = $gpo.ModificationTime
            Stato = $gpo.GpoStatus
            Link = $links
        }
    }
} | Where-Object { $_ }

if ($orphanGPO) {
    Write-Host "GPO non collegate ($($orphanGPO.Count)):" -ForegroundColor Yellow
    $orphanGPO | Format-Table
} else {
    Write-Host "[OK] Tutte le GPO hanno almeno un link" -ForegroundColor Green
}
```

---

**Step 3 — Backup di tutte le GPO**

```powershell
# Backup GPO — eseguire prima di qualsiasi modifica
$backupPath = "C:\Backup\GPO\$(Get-Date -Format 'yyyyMMdd')"
New-Item -Path $backupPath -ItemType Directory -Force | Out-Null

Backup-GPO -All -Path $backupPath

# Verifica backup creato
$files = Get-ChildItem -Path $backupPath -Recurse
Write-Host "[OK] Backup GPO eseguito in $backupPath ($($files.Count) file)"

# Per ripristinare una GPO dal backup:
# Restore-GPO -Name "Default Domain Policy" -Path $backupPath
```

---

**Step 4 — Crea una GPO di test e verifica RSoP**

```powershell
# Crea una GPO di test che configura uno sfondo del desktop
$testGPO = New-GPO -Name "LAB-Desktop-Settings" -Comment "GPO di test per il lab ops04b"

# Configura un'impostazione: imposta il banner di accesso
Set-GPRegistryValue `
    -Name "LAB-Desktop-Settings" `
    -Key "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" `
    -ValueName "LegalNoticeCaption" `
    -Type String `
    -Value "LAB ENVIRONMENT"

Set-GPRegistryValue `
    -Name "LAB-Desktop-Settings" `
    -Key "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" `
    -ValueName "LegalNoticeText" `
    -Type String `
    -Value "Questo sistema è un ambiente di laboratorio IT. Accesso autorizzato solo."

# Collega la GPO al dominio (applica a tutti i computer)
New-GPLink `
    -Name "LAB-Desktop-Settings" `
    -Target "DC=lab,DC=local" `
    -LinkEnabled Yes

Write-Host "[OK] GPO 'LAB-Desktop-Settings' creata e collegata al dominio"

# Forza aggiornamento GPO su DC-LAB-01
gpupdate /force
```

---

**Step 5 — Verifica RSoP su WKS-LAB-01**

```powershell
# Su WKS-LAB-01 (dopo gpupdate /force o login)

# Forza aggiornamento
gpupdate /force

# Report testuale veloce
gpresult /r

# Report HTML completo
gpresult /h "C:\temp\gpresult_wks.html" /f
# Apri il report HTML in Edge/Chrome per vedere le GPO applicate

# Verifica che la GPO LAB-Desktop-Settings sia applicata
gpresult /r | findstr "LAB-Desktop"
```

Output atteso (dopo aggiornamento GPO):
```
COMPUTER SETTINGS
-----------------
    Applied Group Policy Objects
    -----------------------------
        LAB-Desktop-Settings
        Default Domain Policy
        Default Domain Controllers Policy
```

---

### Esercizio B5: AD Security — Audit Account Privilegiati e Monitoraggio Accessi

**Obiettivo.** Verificare la composizione dei gruppi privilegiati, rilevare tentativi di accesso falliti e creazione di nuovi account, e configurare un alert per account lockout.

**Background.** Monitorare chi è nei gruppi Domain Admins e cosa succede con gli account privilegiati è la prima linea di difesa. Un accesso fallito ripetuto può indicare un attacco brute force; un nuovo membro in Domain Admins non previsto è un indicatore critico di compromissione.

---

**Step 1 — Audit gruppi privilegiati**

```powershell
# Su DC-LAB-01

Write-Host "=== AUDIT GRUPPI PRIVILEGIATI ===" -ForegroundColor Red

$gruppiPrivilegiati = @("Domain Admins", "Enterprise Admins", "Schema Admins", "Administrators", "Backup Operators", "Account Operators")

foreach ($gruppo in $gruppiPrivilegiati) {
    try {
        $members = Get-ADGroupMember -Identity $gruppo -Recursive -ErrorAction Stop |
            Select-Object Name, SamAccountName, ObjectClass
        Write-Host "`n[$gruppo] — $($members.Count) membro/i:" -ForegroundColor Yellow
        $members | Format-Table -AutoSize
    } catch {
        Write-Host "`n[$gruppo] — Gruppo non trovato o errore: $_" -ForegroundColor Gray
    }
}
```

---

**Step 2 — Account lockout nelle ultime 24 ore**

```powershell
# Account bloccati nelle ultime 24 ore (Event ID 4740)
$lockouts = Get-WinEvent -FilterHashtable @{
    LogName = "Security"
    Id = 4740
    StartTime = (Get-Date).AddHours(-24)
} -ErrorAction SilentlyContinue

if ($lockouts) {
    Write-Host "`n[WARN] Account bloccati nelle ultime 24h: $($lockouts.Count)" -ForegroundColor Yellow
    $lockouts | Select-Object `
        TimeCreated,
        @{N="Account"; E={$_.Properties[0].Value}},
        @{N="CallerComputer"; E={$_.Properties[1].Value}} |
        Format-Table -AutoSize
} else {
    Write-Host "`n[OK] Nessun account bloccato nelle ultime 24 ore" -ForegroundColor Green
}
```

---

**Step 3 — Tentativi di accesso falliti (Event ID 4625)**

```powershell
# Tentativi di accesso falliti nelle ultime 2 ore
$failedLogins = Get-WinEvent -FilterHashtable @{
    LogName = "Security"
    Id = 4625
    StartTime = (Get-Date).AddHours(-2)
} -MaxEvents 50 -ErrorAction SilentlyContinue

if ($failedLogins) {
    Write-Host "`n[WARN] Accessi falliti (ultime 2 ore): $($failedLogins.Count)" -ForegroundColor Yellow
    
    # Raggruppa per account per trovare brute force
    $failedLogins |
        Select-Object @{N="Account"; E={$_.Properties[5].Value}} |
        Group-Object Account |
        Sort-Object Count -Descending |
        Select-Object -First 10 Name, Count |
        Format-Table -AutoSize
        
    Write-Host "Nota: > 5 tentativi per lo stesso account può indicare brute force"
} else {
    Write-Host "`n[OK] Nessun accesso fallito nelle ultime 2 ore" -ForegroundColor Green
}
```

---

**Step 4 — Simula un fallimento di login e verifica il log**

```powershell
# Su WKS-LAB-01 — simula 3 tentativi con password sbagliata
# (non blocca l'account se la policy prevede lockout dopo 5 tentativi)

# Metodo sicuro: usa runas con password sbagliata
for ($i = 1; $i -le 3; $i++) {
    Start-Process "cmd.exe" -ArgumentList "/c echo password_sbagliata | runas /user:lab.local\lab-user notepad" -PassThru 2>$null | Out-Null
    Start-Sleep -Seconds 1
}

Write-Host "Simulati 3 tentativi di login fallito per lab-user"
Start-Sleep -Seconds 5

# Torna su DC-LAB-01 e verifica i log
$recent = Get-WinEvent -FilterHashtable @{
    LogName = "Security"
    Id = 4625
    StartTime = (Get-Date).AddMinutes(-5)
} -ErrorAction SilentlyContinue

Write-Host "`nAccessi falliti negli ultimi 5 minuti:"
$recent | Select-Object TimeCreated,
    @{N="Account"; E={$_.Properties[5].Value}},
    @{N="SourceIP"; E={$_.Properties[19].Value}},
    @{N="Reason"; E={$_.Properties[8].Value}} |
    Format-Table -AutoSize
```

---

---

## PART C: SISTEMATIZZARE — Governance di Active Directory

---

### Progetto C1: SOP — Manutenzione Mensile Active Directory

```markdown
# SOP-AD-001: Manutenzione Mensile Active Directory

**Versione:** 1.0 | **Data:** 2026-07-15 | **Owner:** Infrastructure Team
**Frequenza:** Prima settimana del mese | **Durata stimata:** 60 minuti
**Sistema:** DC-LAB-01 (e tutti i DC della foresta in produzione)

---

## 1. Pre-Controlli (5 minuti)

- [ ] Nessun incidente aperto su Active Directory in GLPI
- [ ] Finestra manutenzione comunicata se in orario lavorativo
- [ ] Backup dello stato di sistema eseguito: `wbadmin start systemstatebackup -backuptarget:E:`

---

## 2. Salute dei Domain Controller (15 minuti)

### 2.1 Diagnostica dcdiag
```powershell
dcdiag /test:dns /v
dcdiag /test:replications /v
dcdiag /test:fsmocheck /v
dcdiag /test:advertising /v
```
Atteso: nessun "failed test" — ogni failure richiede investigazione immediata

### 2.2 Stato replica repadmin
```powershell
repadmin /replsummary
```
Atteso: 0 failures in "fails/total", nessun delta > 1h

### 2.3 Verifica SYSVOL
```powershell
dfsrdiag pollad
Get-Service DFSR | Select-Object Status
```
Atteso: DFSR Running, pollad senza errori

### 2.4 Ruoli FSMO
```powershell
netdom query fsmo
Test-NetConnection -ComputerName (Get-ADDomain).PDCEmulator -Port 389
```

---

## 3. Audit Oggetti (20 minuti)

### 3.1 Utenti inattivi da > 90 giorni
```powershell
$soglia = (Get-Date).AddDays(-90)
Get-ADUser -Filter { LastLogonDate -lt $soglia -and Enabled -eq $true } -Properties LastLogonDate |
    Select-Object Name, SamAccountName, LastLogonDate | Export-Csv "C:\Reports\AD\inattivi.csv" -NoTypeInformation
```
Azione: per ogni utente inattivo, verificare con l'HR se è ancora dipendente. Se no → disabilita.

### 3.2 Account con Password Never Expires
```powershell
Get-ADUser -Filter { PasswordNeverExpires -eq $true -and Enabled -eq $true } |
    Select-Object Name, SamAccountName
```
Azione: account di servizio → OK se documentati. Account utente → rimuovere l'esenzione.

### 3.3 Gruppi privilegiati (Domain Admins, Enterprise Admins)
```powershell
Get-ADGroupMember "Domain Admins" | Select-Object Name, SamAccountName
```
Azione: confronta con lista autorizzata. Ogni membro non in lista → escalation immediata.

---

## 4. Sicurezza LDAP (10 minuti)

### 4.1 Connessioni LDAP non firmate (ultimi 30 giorni)
```powershell
Get-WinEvent -FilterHashtable @{LogName="Directory Service"; Id=2889; StartTime=(Get-Date).AddDays(-30)} -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, @{N="Client";E={$_.Properties[0].Value}} | Format-Table
```
Atteso: nessun evento. Se presenti → identifica le applicazioni e forza LDAP Signing.

### 4.2 Account lockout (ultime 24h)
```powershell
Get-WinEvent -FilterHashtable @{LogName="Security"; Id=4740; StartTime=(Get-Date).AddHours(-24)} -ErrorAction SilentlyContinue
```
Atteso: 0 lockout. Se > 5 lockout sullo stesso account → possibile attacco.

---

## 5. Group Policy (10 minuti)

### 5.1 Backup GPO mensile
```powershell
Backup-GPO -All -Path "C:\Backup\GPO\$(Get-Date -Format 'yyyyMMdd')"
```

### 5.2 Verifica GPO orfane
```powershell
Get-GPO -All | ForEach-Object {
    $xml = [xml](Get-GPOReport -Guid $_.Id -ReportType XML)
    $ns = @{gpo="http://www.microsoft.com/GroupPolicy/Settings"}
    $links = ($xml | Select-Xml -XPath "//gpo:LinksTo" -Namespace $ns).Count
    if ($links -eq 0) { Write-Host "GPO orfana: $($_.DisplayName)" -ForegroundColor Yellow }
}
```

---

## 6. Escalation

| Problema | Soglia | Azione |
|---|---|---|
| dcdiag failed test | Qualsiasi | Apri INC P2 immediatamente |
| Replica failure | Qualsiasi | Apri INC P1 se PDC coinvolto |
| Nuovo membro in Domain Admins non autorizzato | Qualsiasi | INC P1 + notify sicurezza |
| > 10 lockout stesso account < 1h | Qualsiasi | INC P2 + sospendi account |
| Event ID 2889 (LDAP non firmato) | > 0 | Identifica applicazione, apri CHG per mitigarla |
```

---

### Progetto C2: Script — AD Health Check Automatizzato

```powershell
#!/usr/bin/env pwsh
# ad_health_monthly.ps1 — Health check mensile Active Directory
# Esegui su DC-LAB-01 come Domain Admin

param(
    [string]$ReportPath = "C:\Reports\AD",
    [int]$InactiveThresholdDays = 90,
    [string]$AlertEmail = ""   # opzionale — per notifiche
)

function Write-OK   { param($msg) Write-Host "[ OK] $msg" -ForegroundColor Green }
function Write-WARN { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-ERR  { param($msg) Write-Host "[ERR] $msg" -ForegroundColor Red }

$errCount  = 0
$warnCount = 0
$ts = Get-Date -Format "yyyyMMdd_HHmm"

if (-not (Test-Path $ReportPath)) { New-Item -Path $ReportPath -ItemType Directory -Force | Out-Null }

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " AD HEALTH CHECK — $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# ===== SERVIZI AD =====
Write-Host "`n[ SERVIZI AD ]" -ForegroundColor Cyan

$adServices = @("ADWS", "DNS", "Netlogon", "kdc", "DFSR")
foreach ($svc in $adServices) {
    $s = Get-Service $svc -ErrorAction SilentlyContinue
    if ($s.Status -eq "Running") { Write-OK "Servizio $svc: Running" }
    elseif ($s) { Write-ERR "Servizio $svc: $($s.Status)"; $errCount++ }
    else { Write-WARN "Servizio $svc non trovato"; $warnCount++ }
}

# ===== DCDIAG =====
Write-Host "`n[ DCDIAG ]" -ForegroundColor Cyan

$dcdiagOutput = dcdiag /test:Connectivity /test:Advertising /test:FsmoCheck 2>&1
$failed = $dcdiagOutput | Where-Object { $_ -match "failed test" }
$passed = $dcdiagOutput | Where-Object { $_ -match "passed test" }

Write-OK "dcdiag passed: $($passed.Count) test"
if ($failed.Count -gt 0) {
    $failed | ForEach-Object { Write-ERR "dcdiag: $_"; $errCount++ }
}

# ===== REPLICA =====
Write-Host "`n[ REPLICA AD ]" -ForegroundColor Cyan

$replOutput = repadmin /replsummary 2>&1
$replErrors = $replOutput | Where-Object { $_ -match "[1-9]+\s+/\s+[0-9]+" -and $_ -notmatch "0\s+/\s+0" }
if ($replErrors) {
    $replErrors | ForEach-Object { Write-ERR "Replica error: $_"; $errCount++ }
} else {
    Write-OK "Nessun errore di replica AD"
}

# ===== FSMO =====
Write-Host "`n[ FSMO ]" -ForegroundColor Cyan

$pdcEmulator = (Get-ADDomain).PDCEmulator
$pdcOk = Test-NetConnection -ComputerName $pdcEmulator -Port 389 -WarningAction SilentlyContinue
if ($pdcOk.TcpTestSucceeded) { Write-OK "PDC Emulator ($pdcEmulator) raggiungibile" }
else { Write-ERR "PDC Emulator non raggiungibile!"; $errCount++ }

# ===== OGGETTI OBSOLETI =====
Write-Host "`n[ OGGETTI OBSOLETI ]" -ForegroundColor Cyan

$soglia = (Get-Date).AddDays(-$InactiveThresholdDays)

$inactiveUsers = Get-ADUser -Filter { LastLogonDate -lt $soglia -and Enabled -eq $true } `
    -Properties LastLogonDate -ErrorAction SilentlyContinue
if ($inactiveUsers.Count -gt 0) {
    Write-WARN "Utenti abilitati inattivi da >$InactiveThresholdDays gg: $($inactiveUsers.Count)"
    $inactiveUsers | Select-Object Name, SamAccountName, LastLogonDate |
        Export-Csv "$ReportPath\utenti_inattivi_$ts.csv" -NoTypeInformation
    $warnCount++
} else {
    Write-OK "Nessun utente abilitato inattivo da >$InactiveThresholdDays giorni"
}

$emptyGroups = Get-ADGroup -Filter * -Properties Members -ErrorAction SilentlyContinue |
    Where-Object { $_.Members.Count -eq 0 }
if ($emptyGroups.Count -gt 5) {
    Write-WARN "Gruppi vuoti: $($emptyGroups.Count) (> 5 è anomalo)"
    $warnCount++
} else {
    Write-OK "Gruppi vuoti: $($emptyGroups.Count) (nella norma)"
}

# ===== SICUREZZA =====
Write-Host "`n[ SICUREZZA ]" -ForegroundColor Cyan

# Account lockout ultime 24h
$lockouts = Get-WinEvent -FilterHashtable @{
    LogName="Security"; Id=4740
    StartTime=(Get-Date).AddHours(-24)
} -ErrorAction SilentlyContinue

if ($lockouts.Count -gt 10) {
    Write-ERR "Account lockout ultime 24h: $($lockouts.Count) — possibile attacco brute force"; $errCount++
} elseif ($lockouts.Count -gt 0) {
    Write-WARN "Account lockout ultime 24h: $($lockouts.Count)"; $warnCount++
} else {
    Write-OK "Nessun account lockout nelle ultime 24 ore"
}

# LDAP non firmati (ultime settimane)
$ldapUnsigned = Get-WinEvent -FilterHashtable @{
    LogName="Directory Service"; Id=2889
    StartTime=(Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue

if ($ldapUnsigned.Count -gt 0) {
    Write-WARN "Connessioni LDAP non firmate (7gg): $($ldapUnsigned.Count) — verificare applicazioni"
    $warnCount++
} else {
    Write-OK "Nessuna connessione LDAP non firmata (ultimi 7 giorni)"
}

# Domain Admins — conta i membri
$daCount = (Get-ADGroupMember "Domain Admins" -ErrorAction SilentlyContinue).Count
if ($daCount -le 5) { Write-OK "Domain Admins: $daCount membro/i" }
else { Write-WARN "Domain Admins: $daCount membri — verificare se tutti sono necessari"; $warnCount++ }

# ===== RIEPILOGO =====
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host " RIEPILOGO" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

if ($errCount -eq 0 -and $warnCount -eq 0) {
    Write-Host " ESITO: TUTTO OK" -ForegroundColor Green
} elseif ($errCount -eq 0) {
    Write-Host " ESITO: $warnCount WARNING — revisione consigliata" -ForegroundColor Yellow
} else {
    Write-Host " ESITO: $errCount ERRORI + $warnCount WARNING — ATTENZIONE RICHIESTA" -ForegroundColor Red
}

Write-Host " Report: $ReportPath\*_$ts.csv" -ForegroundColor Gray
```

**Utilizzo:**

```powershell
# Esecuzione manuale
& "C:\Scripts\ad_health_monthly.ps1"

# Con path report custom
& "C:\Scripts\ad_health_monthly.ps1" -ReportPath "D:\Reports\AD" -InactiveThresholdDays 60

# Pianifica come Scheduled Task — ogni primo lunedì del mese alle 07:30
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -WeeksInterval 4 -At "07:30AM"
$action  = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NonInteractive -File C:\Scripts\ad_health_monthly.ps1"
Register-ScheduledTask -TaskName "AD-Monthly-Health" -Trigger $trigger -Action $action -RunLevel Highest -User "SYSTEM"
Write-Host "[OK] Task pianificato: AD-Monthly-Health"
```

---

### Progetto C3: Integrazione ITIL — Active Directory nelle Pratiche ITSM

**AD nel CMDB di GLPI — i Configuration Item essenziali:**

| CI | Tipo | Attributi | Relazioni |
|---|---|---|---|
| DC-LAB-01 (AD) | Server | IP, OS, Ruoli FSMO | Dipende da: DC-LAB-01 (hardware) |
| lab.local Domain | Domain | DFL, FFL, N° DC, Schema version | Ospitato su: DC-LAB-01 (AD) |
| Default Domain Policy | GPO | GUID, Ultima modifica, N° impostazioni | Collegata a: lab.local Domain |
| NTDS.dit | Database File | Percorso, Dimensione, Ultima backup | Parte di: DC-LAB-01 (AD) |

**Integrazione con Change Management:**

```
MODIFICHE AD che richiedono RFC Normal Change:
  - Estensione dello schema AD (es. installazione Exchange)
  - Aggiunta/rimozione di Domain Controller
  - Modifica GPO di sicurezza baseline
  - Trasferimento ruoli FSMO
  - Aggiornamento functional level (Domain/Forest)

MODIFICHE AD che richiedono RFC Standard Change (pre-approvato):
  - Aggiunta utenti a gruppi standard
  - Creazione OU per nuovo progetto
  - Backup GPO e modifica configurazioni non-security

MODIFICHE AD che NON richiedono RFC:
  - Reset password utente standard
  - Sblocco account utente
  - Aggiunta computer al dominio
```

---

## Checklist di Validazione — Tutorial ops04b Completato

### Fondamenti (Part A)
- [ ] Sai descrivere la struttura Foresta/Dominio/OU di Active Directory
- [ ] Sai elencare i 5 ruoli FSMO e spiegare perché il PDC Emulator è il più critico
- [ ] Sai spiegare come funziona la replica AD tra DC con il concetto di USN
- [ ] Sai spiegare la struttura DN di un oggetto AD (`CN=User,OU=Users,DC=lab,DC=local`)
- [ ] Sai distinguere LDAP, LDAP Signing e LDAPS e quando usare ciascuno
- [ ] Sai descrivere l'ordine LSDOU di applicazione delle GPO
- [ ] Sai spiegare i 3 principali vettori di attacco AD (PtH, Kerberoasting, DCSync)

### Operazioni (Part B)
- [ ] B1: `dcdiag /test:connectivity` → passed
- [ ] B1: `repadmin /replsummary` → 0 failures
- [ ] B1: `netdom query fsmo` → tutti i ruoli su DC-LAB-01
- [ ] B1: DFSR service in stato Running
- [ ] B2: Report CSV utenti inattivi generato in `C:\Reports\AD\`
- [ ] B2: Gruppi privilegiati (Domain Admins, Enterprise Admins) auditati
- [ ] B3: LDAP Signing level verificato con Get-ItemProperty
- [ ] B3: Log "Directory Service" verificato per Event ID 2889
- [ ] B4: Backup GPO eseguito in `C:\Backup\GPO\YYYYMMDD\`
- [ ] B4: GPO `LAB-Desktop-Settings` creata, collegata e verificata con `gpresult /r`
- [ ] B5: `Get-ADGroupMember "Domain Admins"` — lista auditata
- [ ] B5: Event ID 4740 (lockout) e 4625 (failed login) analizzati

### Governance (Part C)
- [ ] SOP-AD-001 letta e compresa
- [ ] Script `ad_health_monthly.ps1` eseguito senza errori
- [ ] Sai spiegare quali modifiche AD richiedono RFC Normal Change vs Standard Change

---

## Appendice A: Cheat Sheet Comandi Active Directory

```powershell
# ==== DIAGNOSTICA ====
dcdiag /v /c /e                             # diagnostica completa
dcdiag /test:dns /v                         # solo test DNS
dcdiag /test:replications /v                # solo replica
repadmin /replsummary                       # riepilogo replica
repadmin /showrepl                          # dettaglio replica
repadmin /syncall /AdeP                     # forza replica immediata
netdom query fsmo                           # ruoli FSMO

# ==== DOMINIO E FORESTA ====
Get-ADDomain                                # info dominio
Get-ADForest                                # info foresta
Get-ADDomainController -Filter *            # tutti i DC

# ==== UTENTI ====
Get-ADUser -Identity "lab-user" -Properties *           # info utente completa
Get-ADUser -Filter {Enabled -eq $true} -Properties *    # tutti gli utenti attivi
New-ADUser -Name "Test User" -SamAccountName "tuser" -UserPrincipalName "tuser@lab.local"
Set-ADUser -Identity "tuser" -EmailAddress "tuser@lab.local"
Disable-ADAccount -Identity "tuser"
Enable-ADAccount -Identity "tuser"
Unlock-ADAccount -Identity "tuser"
Set-ADAccountPassword -Identity "tuser" -Reset -NewPassword (ConvertTo-SecureString "NewPass@2024!" -AsPlainText -Force)

# ==== GRUPPI ====
Get-ADGroupMember "Domain Admins" -Recursive
Add-ADGroupMember -Identity "IT-Team" -Members "tuser"
Remove-ADGroupMember -Identity "IT-Team" -Members "tuser" -Confirm:$false

# ==== GPO ====
Get-GPO -All
Get-GPOReport -Name "Default Domain Policy" -ReportType HTML -Path "C:\report.html"
Backup-GPO -All -Path "C:\Backup\GPO"
gpresult /r                                 # RSoP testuale
gpupdate /force                             # forza aggiornamento GPO

# ==== SYSVOL ====
dfsrdiag pollad                             # stato DFSR
Get-Service DFSR | Select-Object Status

# ==== SICUREZZA ====
Get-ADUser -Filter {PasswordNeverExpires -eq $true -and Enabled -eq $true}
Get-ADComputer -Filter {TrustedForDelegation -eq $true}
Get-WinEvent -FilterHashtable @{LogName="Security"; Id=4740}   # lockout
Get-WinEvent -FilterHashtable @{LogName="Security"; Id=4625}   # failed login
Get-WinEvent -FilterHashtable @{LogName="Security"; Id=4728}   # add to group
```

---

## Appendice B: Event ID Critici Active Directory

| Event ID | Log | Significato | Priorità |
|---|---|---|---|
| **4624** | Security | Login riuscito | Normale (baseline) |
| **4625** | Security | Login fallito | Warning se ripetuto |
| **4740** | Security | Account bloccato | Warning |
| **4720** | Security | Nuovo account creato | Monitorare |
| **4726** | Security | Account eliminato | Monitorare |
| **4728** | Security | Aggiunto a gruppo globale | CRITICO se Domain Admins |
| **4732** | Security | Aggiunto a gruppo locale | Monitorare |
| **4756** | Security | Aggiunto a gruppo universale | Monitorare |
| **4771** | Security | Kerberos pre-auth fallita | Warning — possibile PtH/brute force |
| **5136** | Security | Oggetto AD modificato | Monitorare per GPO/Schema changes |
| **1864** | Directory Service | DC non replicato da > 24h | WARNING |
| **2889** | Directory Service | LDAP non firmato | Warning — applicazioni legacy |
| **4602** | DFS Replication | SYSVOL replica iniziale completata | Info |

---

## Riferimenti

| Risorsa | Posizione | Contenuto |
|---|---|---|
| Documento sorgente | `../04-servizi-infrastruttura.md` (sez. AD e LDAP) | Dettaglio configurazioni di produzione |
| Tutorial ops03a | `tutorial_ops03_ch1a_windows_server_ops_lab.md` | Windows Server base (prerequisito) |
| Tutorial ops04a | `tutorial_ops04_ch1a_dns_dhcp_ntp_lab.md` | DNS/DHCP/NTP (prerequisito — NTP/Kerberos) |
| Tutorial ops05b | `tutorial_ops05_ch1b_access_audit_compliance_lab.md` | Audit avanzato, compliance |
| Microsoft Docs AD | learn.microsoft.com/windows-server/identity | Documentazione ufficiale |

---

*Fine tutorial ops04b — Prossimo: `tutorial_ops04_ch2a_email_web_services_lab.md`*
