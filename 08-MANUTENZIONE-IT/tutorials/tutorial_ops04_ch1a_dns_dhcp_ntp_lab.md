# Tutorial: DNS, DHCP e NTP — Servizi Fondazionali di Rete — Hands-On Lab

> **Documento di riferimento:** `04-servizi-infrastruttura.md` (sezioni DNS, DHCP, NTP)
> **Dominio:** Infrastruttura di Rete — Servizi Fondazionali
> **Ambito:** DNS Windows (AD-Integrated) e Linux (BIND9), DHCP scope management e failover, NTP hierarchy e sincronizzazione temporale
> **Durata lab:** 4-5 ore (suddivisibili in più sessioni)
> **Livello:** Intermedio — richiede ops00 (lab), ops01a (ITIL), ops03a (Windows Server), ops03b (Linux)
> **Prerequisiti:** DC-LAB-01 con AD DS e DNS installati, SRV-LINUX-01 operativo, WKS-LAB-01 per i test
> **Ambiente:** DC-LAB-01 (DNS + DHCP + NTP primario), SRV-LINUX-01 (BIND9 + chrony), WKS-LAB-01 (client)

---

## Lab Environment Setup

```powershell
# Da WKS-LAB-01 — verifica pre-lab: tutti i servizi devono rispondere
$checks = @(
    @{ Name = "DC-LAB-01 DNS";  IP = "192.168.56.10"; Port = 53  },
    @{ Name = "DC-LAB-01 DHCP"; IP = "192.168.56.10"; Port = 67  },
    @{ Name = "SRV-LINUX-01";   IP = "192.168.56.20"; Port = 22  }
)
foreach ($c in $checks) {
    $ok = Test-NetConnection -ComputerName $c.IP -Port $c.Port -WarningAction SilentlyContinue
    $sym = if ($ok.TcpTestSucceeded) { "[OK]" } else { "[ERR]" }
    Write-Host "$sym $($c.Name) ($($c.IP)):$($c.Port)"
}

# Verifica DNS dal client Windows
Resolve-DnsName dc-lab-01.lab.local -Server 192.168.56.10
```

Output atteso:
```
[OK] DC-LAB-01 DNS (192.168.56.10):53
[OK] DC-LAB-01 DHCP (192.168.56.10):67
[OK] SRV-LINUX-01 (192.168.56.20):22
```

---

## PART A: FONDAMENTI — I Tre Pilastri della Rete Aziendale

> Immagina una città. Ogni residente ha una casa (indirizzo IP), ma le persone si chiamano per nome (nome host). C'è un ufficio anagrafe che assegna gli indirizzi (DHCP), una rubrica telefonica che traduce nomi in indirizzi (DNS), e un orologio civico centralizzato a cui tutti devono sincronizzarsi (NTP). Senza questi tre servizi, la "città" IT non funziona: le persone non si trovano, gli indirizzi si duplicano, e gli appuntamenti (le sessioni autenticate) vengono fissati in orari impossibili.

---

### Concetto A1: DNS — La Rubrica Telefonica dell'Infrastruttura

> **Analogia.** Prima dei cellulari, per chiamare qualcuno cercavi il suo nome sull'elenco telefonico e trovavi il numero. Il DNS è esattamente questo: tu scrivi `www.azienda.it`, il DNS trova `93.184.216.34`. Senza DNS, ogni volta che vuoi collegarti a un server dovresti ricordare il suo indirizzo IP — come se dovessi ricordare a memoria il numero di telefono di ogni persona che conosci.

**Come funziona la risoluzione DNS:**

```
Tu digiti: glpi.lab.local
               │
               ▼
     [Cache locale del client]
     "Ho già risolto questo?"
          SÌ → usa cache
          NO  → chiedi al DNS server
               │
               ▼
     [DC-LAB-01: 192.168.56.10]
     Server DNS Autorevole per lab.local
     "Conosco glpi.lab.local?"
          SÌ → risponde con IP
          NO  → chiede a server superiori (forwarder)
               │
               ▼
     [Server DNS Internet (8.8.8.8)]
     Solo per nomi esterni (google.com, microsoft.com)
```

**I tipi di record DNS più importanti:**

| Tipo | Nome | Cosa fa | Esempio nel lab |
|------|------|---------|-----------------|
| **A** | Address | Nome → IPv4 | `dc-lab-01.lab.local → 192.168.56.10` |
| **PTR** | Pointer | IPv4 → Nome | `192.168.56.10 → dc-lab-01.lab.local` |
| **CNAME** | Alias | Nome → Nome | `glpi.lab.local → srv-linux-01.lab.local` |
| **MX** | Mail Exchanger | Mail server del dominio | `lab.local → mail.lab.local` |
| **SRV** | Service | Posizione servizi AD | `_ldap._tcp.lab.local → dc-lab-01:389` |
| **NS** | Name Server | Server autorevole per la zona | `lab.local → dc-lab-01.lab.local` |
| **SOA** | Start of Authority | Info amministrative zona | Numero seriale, refresh, retry |

**DNS AD-Integrated vs Standard:**

Active Directory usa zone DNS integrate nel database di AD. Questo ha tre vantaggi enormi:
1. **Replica automatica** — i record DNS si replicano insieme ad AD, senza configurazione separata
2. **Aggiornamenti sicuri** — solo i computer del dominio possono registrare/aggiornare i propri record
3. **Disponibilità** — ogni DC è anche server DNS autorevole; se un DC cade, gli altri servono le query

**Il problema degli "stale records" (record obsoleti):**

```
Scenario: WKS-LAB-01 viene reinstallato con IP diverso
Prima: wks-lab-01.lab.local → 192.168.56.30
Dopo reinstall: wks-lab-01.lab.local → 192.168.56.31 (nuovo IP)

Problema: il vecchio record 192.168.56.30 rimane nel DNS
Risultato: la rete pensa che WKS-LAB-01 sia ancora sul vecchio IP
           → connessioni fallite, log di sicurezza confusi

Soluzione: DNS Scavenging (pulizia automatica dei record non aggiornati)
```

**DNS Scavenging — come funziona:**

```
Record creato → [No-Refresh Interval: 7 giorni]
                Il client NON può aggiornare il record
                Impedisce flood di aggiornamenti inutili
                    ↓
               [Refresh Interval: 7 giorni]
                Il client DEVE aggiornare il record
                Se non lo aggiorna → record candidato alla pulizia
                    ↓
               [Scavenging]
                Il server elimina i record non aggiornati da >14 giorni
                (7 No-Refresh + 7 Refresh = 14 giorni totali)
```

---

### Concetto A2: DHCP — L'Ufficio Anagrafe della Rete

> **Analogia.** Quando arrivi in un hotel, non scegli tu la tua stanza: la reception ti assegna la stanza disponibile e ti dà la chiave (indirizzo IP). La chiave è temporanea: al check-out la riconsegni (lease scaduto) e la stanza torna disponibile per altri ospiti. Il DHCP funziona esattamente così: assegna indirizzi IP temporanei (lease) ai dispositivi che si collegano alla rete, gestisce la "disponibilità" delle stanze (pool di indirizzi), e garantisce che non ci siano due ospiti nella stessa stanza (duplicate detection).

**Il processo DORA — come il client ottiene un indirizzo IP:**

```
Client (nuovo dispositivo)          DHCP Server (DC-LAB-01)
        │                                    │
        │──── DISCOVER (broadcast) ─────────▶│  "C'è un DHCP server?"
        │                                    │
        │◀─── OFFER ─────────────────────────│  "Sì! Ti offro 192.168.56.31"
        │                                    │
        │──── REQUEST (broadcast) ───────────▶│  "Accetto quell'IP"
        │                                    │
        │◀─── ACK ───────────────────────────│  "Confermato, lease: 8 giorni"
        │                                    │
   [IP configurato: 192.168.56.31]
   [Lease scade: 2026-07-23]
```

**Componenti di uno scope DHCP:**

```
Scope: 192.168.56.0/24 — Rete Lab
├── Range: 192.168.56.100 – 192.168.56.200 (indirizzi assegnabili)
├── Esclusioni: 192.168.56.1-10 (router, DC, server — IP statici)
├── Lease Duration: 8 giorni (default Windows)
├── Opzioni scope:
│   ├── 003 Router: 192.168.56.1 (gateway)
│   ├── 006 DNS: 192.168.56.10 (DC-LAB-01)
│   └── 015 Domain Name: lab.local
└── Riserve (reservations):
    └── SRV-LINUX-01: MAC aa:bb:cc:dd:ee:ff → sempre 192.168.56.20
```

**DHCP Failover — ridondanza per il servizio più critico:**

```
Senza failover:
  Server DHCP unico muore → client non ottengono IP → rete non funziona

Con failover:
  DHCP Primario ←→ DHCP Secondario (replica del database lease)
  Se il primario cade, il secondario continua ad assegnare IP
  I lease già assegnati vengono onorati da entrambi

Modalità:
  Load Sharing: 50% dei lease dal primario, 50% dal secondario
  Hot Standby: il secondario interviene solo se il primario è offline
```

**Rogue DHCP — la minaccia silenziosa:**

```
Scenario: qualcuno collega un router consumer alla rete aziendale
Quel router ha DHCP abilitato di default
Inizia ad assegnare IP sbagliati ai client
→ IP wrong subnet → impossibile accedere ai server
→ DNS wrong → non si risolvono i nomi
→ Gateway wrong → traffico intercettato (MITM)

Rilevamento: Event ID 1063 in Windows Event Log
             "DHCP server unauthorized in Active Directory"
```

---

### Concetto A3: NTP — L'Orologio Civico dell'Infrastruttura

> **Analogia.** Immagina una banca con 10 filiali. Ogni filiale ha un suo orologio, e gli orologi non sono sincronizzati: la filiale A segna le 14:00, la filiale B le 14:07. Quando un cliente fa un bonifico a 14:00 dalla filiale A e il sistema di controllo frodi della filiale B vede la transazione a "14:07", pensa che ci sia un anomalia di sequenza temporale e blocca tutto. Kerberos (il sistema di autenticazione Active Directory) è quel sistema di controllo frodi: accetta solo operazioni che avvengono entro 5 minuti dall'ora di sistema del Domain Controller. Se il tuo PC è sfasato di più, non riesci ad accedere alla rete.

**La gerarchia NTP — gli Stratum:**

```
STRATUM 0 — Sorgente di riferimento
  Orologio atomico, ricevitore GPS
  Non comunicano direttamente sulla rete

STRATUM 1 — Server primari
  Direttamente connessi alla sorgente Stratum 0
  Precisione: < 1 millisecondo

STRATUM 2 — Server secondari (DC-LAB-01 nel lab)
  Sincronizzano da Stratum 1
  Precisione: ~ 10-50 millisecondi
  Servono come sorgente per i client aziendali

STRATUM 3-15 — Client (WKS-LAB-01, SRV-LINUX-01)
  Sincronizzano da Stratum 2

STRATUM 16 — NON SINCRONIZZATO (errore!)
  Il server non ha trovato sorgente valida
```

**In Active Directory — la gerarchia W32Time:**

```
Internet NTP Pool (Stratum 1/2)
    ↓
DC-LAB-01 (PDC Emulator) — Stratum 2
  Unica sorgente autorevole del dominio
  Si sincronizza da server internet

DC secondari (se presenti) — Stratum 3
  Si sincronizzano dal PDC Emulator
  
WKS-LAB-01, altri client — Stratum 4
  Si sincronizzano dal DC che li autentica
  
SRV-LINUX-01 — Stratum 3 o 4
  Configurabile per sincronizzare dal DC
  o direttamente dal pool NTP
```

**Perché 5 minuti è il limite di Kerberos:**

Il protocollo Kerberos v5 include un timestamp in ogni ticket di autenticazione. Se il client e il server hanno orologi sfasati di più di 5 minuti (`MaxClockSkew` configurabile, default 5 min), il server rifiuta il ticket come "potenzialmente riutilizzato" — una difesa contro gli attacchi di tipo replay. Questo significa che:

```
Accesso fallisce → "KRB_AP_ERR_SKEW" o "Clock skew too great"
                      ↓
              Causa probabile: orologio client > 5 min sfasato
                      ↓
              Diagnosi: w32tm /query /status
              Fix: w32tm /resync /force (Windows)
                   chronyc makestep (Linux)
```

**NTP vs PTP — quando usare quale:**

| Caratteristica | NTP | PTP (IEEE 1588) |
|---|---|---|
| Precisione | 1-50 millisecondi | 10 ns - 1 microsecondo |
| Hardware dedicato | No | Sì (NIC con hardware timestamping) |
| Complessità | Bassa | Media-Alta |
| Caso d'uso | Infrastruttura IT aziendale | Trading HFT, 5G, automazione |
| Il nostro lab | **Usiamo NTP** | Fuori scope |

---

### Concetto A4: DDI — DNS, DHCP e IPAM come Sistema Integrato

> **Analogia.** In una città ben gestita, l'ufficio anagrafe (DHCP), la rubrica telefonica (DNS) e il catasto (IPAM) devono essere coordinati. Se l'anagrafe assegna un nuovo indirizzo a un residente, la rubrica deve essere aggiornata. Se il catasto mostra che un appartamento è libero, l'anagrafe può assegnarlo. Quando questi tre sistemi non comunicano, il risultato è il caos: indirizzi duplicati, rubriche obsolete, conflitti di proprietà.

**DDI = DNS + DHCP + IPAM (IP Address Management)**

In Windows Server, queste tre funzioni sono integrate:
- Il DHCP aggiorna automaticamente il DNS quando assegna un IP (Dynamic DNS — DDNS)
- L'IPAM (ruolo opzionale di Windows Server) tiene traccia di tutti gli IP assegnati
- I record DNS "stale" vengono puliti automaticamente dallo scavenging

```
Dispositivo si collega alla rete
         ↓
DHCP assegna IP: 192.168.56.105
         ↓
DHCP aggiorna DNS automaticamente (DDNS):
   nuovopc.lab.local → 192.168.56.105 (record A)
   192.168.56.105 → nuovopc.lab.local (record PTR)
         ↓
14 giorni senza rinnovo lease?
   DNS Scavenging elimina il record stale
         ↓
Quadro IP sempre coerente e aggiornato
```

---

### Concetto A5: Perché questi servizi sono "fondazionali"

> **Perché mi interessa?** Questi tre servizi non sono "funzionalità nice-to-have" — sono la condizione necessaria per qualsiasi altra cosa funzioni nella rete aziendale. Se il DNS non funziona, gli utenti non aprono le applicazioni (anche se i server sono perfetti). Se il DHCP non funziona, i nuovi dispositivi non ottengono IP. Se NTP è sfasato, le autenticazioni AD falliscono. L'80% degli "incidenti di rete misteriosi" in realtà è un problema DNS, DHCP o NTP mal configurato.

**Impatto di un'interruzione:**

| Servizio | Se cade per 1 ora | Impatto ITIL |
|---|---|---|
| **DNS** | Nessun nome si risolve, accesso a tutte le applicazioni compromesso | P1 — Major Incident |
| **DHCP** | I lease esistenti durano ancora, ma nuovi dispositivi non ottengono IP | P2 (crescente) |
| **NTP** | I client con orologio sfasato non si autenticano su AD | P1 se PDC cade |

**Sequenza di troubleshooting "utente non accede alla rete":**

```
1. L'utente ha un indirizzo IP?     → ipconfig /all
   NO  → problema DHCP
   SÌ  → vai al passo 2

2. Il DNS risolve i nomi?           → ping dc-lab-01.lab.local
   NO  → problema DNS (nameserver, zone, record)
   SÌ  → vai al passo 3

3. L'autenticazione funziona?       → klist (visualizza ticket Kerberos)
   NO  → problema NTP o AD (clock skew)
   SÌ  → problema applicativo o permessi
```

---

---

## PART B: OPERAZIONI — Configurare e Mantenere DNS, DHCP e NTP

---

### Esercizio B1: DNS Windows — Configurare lo Scavenging e Verificare la Zona

**Obiettivo.** Abilitare la pulizia automatica dei record DNS obsoleti su DC-LAB-01 e verificare che la zona `lab.local` sia integrata in Active Directory con aggiornamenti dinamici sicuri.

**Background.** In ambienti dove i dispositivi cambiano spesso IP (laptop, macchine virtuali, dispositivi IoT), il database DNS si accumula di record "stale" — record che puntano a IP non più validi. Lo scavenging risolve questo automaticamente.

---

**Step 1 — Connettiti a DC-LAB-01 e verifica la zona DNS**

```powershell
# Su DC-LAB-01 (192.168.56.10) — apri PowerShell come Administrator

# Elenca tutte le zone DNS configurate
Get-DnsServerZone | Select-Object ZoneName, ZoneType, IsDsIntegrated, DynamicUpdate
```

Output atteso:
```
ZoneName                          ZoneType IsDsIntegrated DynamicUpdate
--------                          -------- -------------- -------------
0.in-addr.arpa                   Primary  False          None
56.168.192.in-addr.arpa           Primary  True           Secure
lab.local                         Primary  True           Secure
TrustAnchors                      Primary  False          None
```

La colonna `IsDsIntegrated = True` conferma che `lab.local` è integrata in AD. `DynamicUpdate = Secure` significa che solo i computer del dominio possono aggiornare i propri record.

---

**Step 2 — Abilita lo scavenging sulla zona lab.local**

```powershell
# Configura i parametri di scavenging per la zona lab.local
Set-DnsServerZoneAging `
    -Name "lab.local" `
    -Aging $true `
    -NoRefreshInterval 7.00:00:00 `
    -RefreshInterval 7.00:00:00

# Abilita lo scavenging sul server DNS (necessario oltre che sulla zona)
Set-DnsServerScavenging `
    -ScavengingState $true `
    -ScavengingInterval 7.00:00:00 `
    -ApplyOnAllZones

# Verifica la configurazione
Get-DnsServerZoneAging -Name "lab.local"
```

Output atteso:
```
ZoneName          : lab.local
AgingEnabled      : True
NoRefreshInterval : 7.00:00:00
RefreshInterval   : 7.00:00:00
ScavengeServers   : {}
```

---

**Step 3 — Verifica i record DNS esistenti**

```powershell
# Elenca tutti i record di tipo A nella zona lab.local
Get-DnsServerResourceRecord -ZoneName "lab.local" -RRType "A" |
    Select-Object HostName, TimeToLive, @{N="IP";E={$_.RecordData.IPv4Address.ToString()}} |
    Sort-Object HostName
```

Output atteso:
```
HostName    TimeToLive IP
--------    ---------- --
dc-lab-01   00:20:00   192.168.56.10
srv-linux-01 00:20:00  192.168.56.20
wks-lab-01  00:20:00   192.168.56.30
```

---

**Step 4 — Aggiungi record DNS personalizzati**

```powershell
# Aggiungi un record CNAME per rendere "glpi" un alias di srv-linux-01
Add-DnsServerResourceRecordCName `
    -ZoneName "lab.local" `
    -Name "glpi" `
    -HostNameAlias "srv-linux-01.lab.local."

# Aggiungi un record A per un server ipotetico (test scavenging)
Add-DnsServerResourceRecord `
    -ZoneName "lab.local" `
    -A `
    -Name "test-stale" `
    -IPv4Address "192.168.56.99"

# Verifica i record appena aggiunti
Resolve-DnsName "glpi.lab.local" -Server 192.168.56.10
Resolve-DnsName "test-stale.lab.local" -Server 192.168.56.10
```

Output atteso per glpi:
```
Name                                   Type   TTL   Section    NameHost
----                                   ----   ---   -------    --------
glpi.lab.local                         CNAME  1200  Answer     srv-linux-01.lab.local

Name       : srv-linux-01.lab.local
QueryType  : A
TTL        : 1200
Section    : Answer
IP4Address : 192.168.56.20
```

---

**Step 5 — Configura e verifica i Conditional Forwarders**

I Conditional Forwarders permettono di risolvere nomi di domini specifici tramite server DNS dedicati. Utile per ambienti multi-dominio o per integrazione cloud (Azure AD, AWS Route 53).

```powershell
# Aggiungi un conditional forwarder (esempio: per azure.local usa 8.8.8.8)
Add-DnsServerConditionalForwarderZone `
    -Name "azure.lab.local" `
    -MasterServers "8.8.8.8", "8.8.4.4" `
    -ReplicationScope "Domain"

# Elenca i forwarder configurati
Get-DnsServerZone | Where-Object { $_.ZoneType -eq "Forwarder" } |
    Select-Object ZoneName, ZoneType

# Verifica i forwarder generici (per nomi non locali)
Get-DnsServerForwarder
```

---

**Step 6 — Abilita il debug logging DNS (temporaneo, solo per troubleshooting)**

```powershell
# Abilita il logging dettagliato (da disabilitare dopo il troubleshooting)
Set-DnsServerDiagnostics `
    -Queries $true `
    -Answers $true `
    -SendPackets $true `
    -ReceivePackets $true `
    -LogFilePath "C:\Windows\System32\dns\dns.log" `
    -MaxMBFileSize 100

# Dopo il troubleshooting — disabilita il debug logging
Set-DnsServerDiagnostics -All $false
```

**Checkpoint di verifica B1:**

```powershell
# Esegui questi comandi e verifica che tutti passino
Write-Host "=== VERIFICA DNS ===" -ForegroundColor Cyan

# 1. Zona integrata in AD
$zone = Get-DnsServerZone -Name "lab.local"
if ($zone.IsDsIntegrated) { Write-Host "[OK] Zona lab.local integrata in AD" -ForegroundColor Green }
else { Write-Host "[ERR] Zona non integrata" -ForegroundColor Red }

# 2. Scavenging abilitato
$aging = Get-DnsServerZoneAging -Name "lab.local"
if ($aging.AgingEnabled) { Write-Host "[OK] Scavenging abilitato (7+7 giorni)" -ForegroundColor Green }
else { Write-Host "[ERR] Scavenging non abilitato" -ForegroundColor Red }

# 3. Record CNAME glpi
$cname = Resolve-DnsName "glpi.lab.local" -Server 192.168.56.10 -ErrorAction SilentlyContinue
if ($cname) { Write-Host "[OK] Record CNAME glpi.lab.local presente" -ForegroundColor Green }
else { Write-Host "[ERR] Record CNAME non trovato" -ForegroundColor Red }
```

---

### Esercizio B2: DHCP Windows — Gestione Scope, Lease e Reservations

**Obiettivo.** Verificare lo stato dello scope DHCP su DC-LAB-01, aggiungere una reservation per SRV-LINUX-01, analizzare il log DHCP e rilevare eventuali server DHCP non autorizzati.

**Background.** In una rete aziendale, il DHCP deve garantire che i server critici abbiano sempre lo stesso IP (via reservation) e che i client non autorizzati non possano distribuire IP (server DHCP non autorizzati in AD sono una minaccia reale).

---

**Step 1 — Verifica stato dello scope e utilizzo**

```powershell
# Su DC-LAB-01

# Elenca tutti gli scope configurati
Get-DhcpServerv4Scope | Select-Object ScopeId, StartRange, EndRange, SubnetMask, State, Name

# Statistiche di utilizzo dello scope
Get-DhcpServerv4ScopeStatistics -ScopeId "192.168.56.0" |
    Select-Object ScopeId, Free, InUse, Reserved, Pending, PercentageInUse
```

Output atteso:
```
ScopeId       StartRange       EndRange         SubnetMask    State  Name
-------       ----------       --------         ----------    -----  ----
192.168.56.0  192.168.56.100   192.168.56.200   255.255.255.0 Active Rete Lab

ScopeId       Free  InUse Reserved Pending PercentageInUse
-------       ----  ----- -------- ------- ---------------
192.168.56.0  98    3     0        0       2.94
```

---

**Step 2 — Visualizza tutti i lease attivi**

```powershell
# Elenca tutti i lease assegnati
Get-DhcpServerv4Lease -ScopeId "192.168.56.0" |
    Select-Object IPAddress, HostName, ClientId, LeaseExpiryTime, AddressState |
    Sort-Object IPAddress
```

Output atteso:
```
IPAddress       HostName    ClientId           LeaseExpiryTime     AddressState
---------       --------    --------           ---------------     ------------
192.168.56.100  WKS-LAB-01  00-15-5d-xx-xx-xx  2026-07-23 09:00   Active
192.168.56.101  ...         ...                 ...                Active
```

---

**Step 3 — Aggiungi una reservation per SRV-LINUX-01**

Una reservation garantisce che un dispositivo specifico (identificato dal MAC address) riceva sempre lo stesso IP dal DHCP.

```bash
# Prima recupera il MAC address di SRV-LINUX-01
# Su SRV-LINUX-01 via SSH:
ip link show enp0s8 | grep "link/ether" | awk '{print $2}'
```

Output atteso (il MAC varia per ogni VM):
```
08:00:27:xx:xx:xx
```

```powershell
# Su DC-LAB-01 — aggiungi la reservation
# Sostituisci "08-00-27-XX-XX-XX" con il MAC reale di SRV-LINUX-01
Add-DhcpServerv4Reservation `
    -ScopeId "192.168.56.0" `
    -IPAddress "192.168.56.20" `
    -ClientId "08-00-27-XX-XX-XX" `
    -Description "SRV-LINUX-01 — Ubuntu Server Lab" `
    -Name "srv-linux-01"

# Verifica la reservation
Get-DhcpServerv4Reservation -ScopeId "192.168.56.0" |
    Select-Object IPAddress, Name, ClientId, Description
```

Output atteso:
```
IPAddress        Name          ClientId           Description
---------        ----          --------           -----------
192.168.56.20    srv-linux-01  08-00-27-XX-XX-XX  SRV-LINUX-01 — Ubuntu Server Lab
```

---

**Step 4 — Analizza il log DHCP per Event ID critici**

Il DHCP server di Windows registra eventi importanti nel Windows Event Log. Gli Event ID chiave sono:

| Event ID | Significato | Attenzione |
|---|---|---|
| 10 | Nuovo lease assegnato | Normale |
| 11 | Lease rinnovato | Normale |
| 12 | Lease rilasciato (DHCPRELEASE) | Normale |
| 13 | Indirizzo già in uso (conflict) | Investigare! |
| 15 | Lease scaduto | Normale se dispositivo offline |
| 1063 | Server DHCP non autorizzato rilevato | CRITICO — Rogue DHCP! |

```powershell
# Cerca eventi DHCP degli ultimi 7 giorni
Get-WinEvent -FilterHashtable @{
    LogName = "System"
    ProviderName = "Microsoft-Windows-DHCP-Server"
    StartTime = (Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, Id, Message |
    Sort-Object TimeCreated -Descending |
    Select-Object -First 20

# Cerca specificamente conflitti e rogue DHCP
Get-WinEvent -FilterHashtable @{
    LogName = "System"
    ProviderName = "Microsoft-Windows-DHCP-Server"
    Id = @(13, 1063)
    StartTime = (Get-Date).AddDays(-30)
} -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, Id, Message
```

---

**Step 5 — Verifica autorizzazione DHCP in Active Directory**

Solo i DHCP server autorizzati in Active Directory possono distribuire IP. Un server non autorizzato viene bloccato automaticamente.

```powershell
# Verifica quali DHCP server sono autorizzati in AD
Get-DhcpServerInDC

# Verifica che DC-LAB-01 sia autorizzato
$fqdn = (Get-Item env:COMPUTERNAME).Value + ".lab.local"
$authorized = Get-DhcpServerInDC | Where-Object { $_.DnsName -like "*$($env:COMPUTERNAME)*" }
if ($authorized) {
    Write-Host "[OK] DC-LAB-01 è autorizzato come DHCP server in AD" -ForegroundColor Green
} else {
    Write-Host "[WARN] DC-LAB-01 non trovato tra i DHCP autorizzati" -ForegroundColor Yellow
}
```

Output atteso:
```
IPAddress       DnsName
---------       -------
192.168.56.10   DC-LAB-01.lab.local

[OK] DC-LAB-01 è autorizzato come DHCP server in AD
```

---

**Step 6 — Genera un report CSV di utilizzo IP**

```powershell
# Genera un report completo dell'utilizzo IP dello scope
$leases = Get-DhcpServerv4Lease -ScopeId "192.168.56.0"
$reservations = Get-DhcpServerv4Reservation -ScopeId "192.168.56.0"
$stats = Get-DhcpServerv4ScopeStatistics -ScopeId "192.168.56.0"

$report = [PSCustomObject]@{
    DataReport    = (Get-Date -Format "yyyy-MM-dd HH:mm")
    ScopeID       = "192.168.56.0"
    TotaleInUso   = $stats.InUse
    TotaleLiberi  = $stats.Free
    TotaleRiservati = $stats.Reserved
    PercentualeUso  = [math]::Round($stats.PercentageInUse, 2)
    LeaseAttivi   = $leases.Count
    Riserve       = $reservations.Count
}

$report | Format-List

# Salva su file
$leases | Select-Object IPAddress, HostName, ClientId, LeaseExpiryTime, AddressState |
    Export-Csv -Path "C:\Reports\dhcp_lease_report_$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation

Write-Host "[OK] Report salvato in C:\Reports\" -ForegroundColor Green
```

**Checkpoint di verifica B2:**

```powershell
Write-Host "=== VERIFICA DHCP ===" -ForegroundColor Cyan

# 1. Scope attivo
$scope = Get-DhcpServerv4Scope -ScopeId "192.168.56.0" -ErrorAction SilentlyContinue
if ($scope.State -eq "Active") { Write-Host "[OK] Scope 192.168.56.0 attivo" -ForegroundColor Green }

# 2. Reservation SRV-LINUX-01
$res = Get-DhcpServerv4Reservation -ScopeId "192.168.56.0" |
    Where-Object { $_.IPAddress -eq "192.168.56.20" }
if ($res) { Write-Host "[OK] Reservation per SRV-LINUX-01 (192.168.56.20) presente" -ForegroundColor Green }
else { Write-Host "[ERR] Reservation mancante" -ForegroundColor Red }

# 3. Nessun rogue DHCP nelle ultime 24 ore
$rogue = Get-WinEvent -FilterHashtable @{
    LogName = "System"; Id = 1063
    StartTime = (Get-Date).AddDays(-1)
} -ErrorAction SilentlyContinue
if (-not $rogue) { Write-Host "[OK] Nessun Rogue DHCP rilevato (24h)" -ForegroundColor Green }
else { Write-Host "[WARN] Rogue DHCP rilevato! Investigare immediatamente" -ForegroundColor Red }
```

---

### Esercizio B3: NTP Windows — Configurare il PDC Emulator come Sorgente Autorevole

**Obiettivo.** Configurare DC-LAB-01 (che è il PDC Emulator) per sincronizzarsi con il pool NTP italiano, verificare la gerarchia di sincronizzazione temporale del dominio e rilevare eventuali problemi di clock skew.

**Background.** In Active Directory, il PDC Emulator è la sorgente temporale autorevole per tutto il dominio. Se non è configurato correttamente per sincronizzarsi con un server NTP esterno, tutti i client del dominio derivano la loro ora da un orologio che non è calibrato — e alla lunga il drift accumulato causa fallimenti di autenticazione Kerberos.

---

**Step 1 — Verifica il ruolo PDC Emulator e lo stato NTP attuale**

```powershell
# Su DC-LAB-01

# Verifica che questo DC sia il PDC Emulator
netdom query fsmo | findstr "PDC"

# Stato corrente della sincronizzazione NTP
w32tm /query /status
```

Output atteso per w32tm /query /status:
```
Leap Indicator: 0(no warning)
Stratum: 5 (secondary reference - syncd by (S)NTP)
Precision: -6 (15.625ms per tick)
Root Delay: 0.0000000s
Root Dispersion: 0.0000000s
ReferenceId: 0x0A0038xx (source IP: 10.0.56.xx)
Last Successful Sync Time: 7/15/2026 8:30:00 AM
Source: time.windows.com
Poll Interval: 10 (1024s)
```

---

**Step 2 — Configura il PDC Emulator per sincronizzarsi con pool NTP italiano**

```powershell
# Configura il servizio W32Time con 4 server NTP del pool italiano
# (4 sorgenti evitano il "two-clock problem" — con 2 sorgenti in disaccordo
# il client non può determinare quale sia corretta)
w32tm /config `
    /manualpeerlist:"0.it.pool.ntp.org,0x8 1.it.pool.ntp.org,0x8 2.it.pool.ntp.org,0x8 3.it.pool.ntp.org,0x8" `
    /syncfromflags:manual `
    /reliable:yes `
    /update

# Riavvia il servizio W32Time per applicare la configurazione
Restart-Service w32time

# Forza una risincronizzazione immediata
w32tm /resync /force

# Verifica la nuova configurazione
w32tm /query /configuration
```

Nota: nel lab senza accesso internet, il comando `/resync /force` può fallire con "The computer did not resync because no time data was available." — questo è normale in un ambiente isolato. In produzione con accesso internet funzionerebbe.

---

**Step 3 — Verifica la gerarchia di sincronizzazione**

```powershell
# Verifica le sorgenti NTP configurate
w32tm /query /peers

# Misura lo scostamento tra DC-LAB-01 e se stesso (baseline)
w32tm /stripchart /computer:127.0.0.1 /samples:5 /dataonly

# In un ambiente con più DC, verifica lo scostamento tra DC
# Esempio: DC secondario vs PDC Emulator
# w32tm /stripchart /computer:dc02.lab.local /samples:5 /dataonly
```

Output atteso (w32tm /stripchart):
```
Tracking 127.0.0.1 [127.0.0.1:123].
Collecting 5 samples.
The current time is 7/15/2026 10:00:00 AM.
10:00:00, -00.0000000s
10:00:02, +00.0000001s
10:00:04, -00.0000001s
10:00:06, +00.0000000s
10:00:08, -00.0000001s
```

L'offset deve essere < 100ms in un ambiente sano. Un offset > 500ms è critico; > 5 minuti causa fallimenti Kerberos.

---

**Step 4 — Verifica NTP su WKS-LAB-01 (client del dominio)**

```powershell
# Su WKS-LAB-01
# I client del dominio sincronizzano automaticamente con il DC che li autentica

# Verifica la sorgente NTP del client
w32tm /query /source

# Stato completo
w32tm /query /status

# Forza risincronizzazione (utile dopo un periodo di hibernate o snapshot)
w32tm /resync
```

Output atteso per /source:
```
\\DC-LAB-01.lab.local
```

Il client mostra il nome del DC come sorgente — questo conferma che la gerarchia NTP AD funziona correttamente.

---

**Step 5 — Simula e risolvi un problema di clock skew**

```powershell
# Su WKS-LAB-01 — simula un problema di orologio sfasato
# (NON fare in produzione — solo per didattica)

# Avanza l'orologio di 6 minuti (supera il limite Kerberos di 5 min)
# $fuoroSync = (Get-Date).AddMinutes(6)
# Set-Date -Date $fuoroSync

# Tenta un'operazione che usa Kerberos
# klist  → mostrerebbe errore di ticket
# Get-ADUser Administrator  → fallirebbe

# Ripristina sincronizzando dal DC
w32tm /resync /force

# Verifica che l'orologio sia ora corretto
Get-Date

# Verifica i ticket Kerberos (devono essere presenti)
klist
```

---

**Step 6 — Verifica NTP su SRV-LINUX-01 (Ubuntu)**

```bash
# Su SRV-LINUX-01 via SSH

# Verifica il servizio di sincronizzazione temporale (Ubuntu usa systemd-timesyncd di default)
timedatectl status
```

Output atteso:
```
               Local time: Wed 2026-07-15 10:30:00 UTC
           Universal time: Wed 2026-07-15 10:30:00 UTC
                 RTC time: Wed 2026-07-15 10:30:00
                Time zone: UTC (UTC, +0000)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```

```bash
# Visualizza il server NTP in uso
cat /etc/systemd/timesyncd.conf

# Configura systemd-timesyncd per usare DC-LAB-01 come sorgente NTP
sudo tee /etc/systemd/timesyncd.conf << 'NTPCONF'
[Time]
NTP=192.168.56.10
FallbackNTP=0.ubuntu.pool.ntp.org 1.ubuntu.pool.ntp.org
NTPCONF

# Riavvia il servizio
sudo systemctl restart systemd-timesyncd

# Verifica la sincronizzazione
timedatectl show-timesync --all
```

Output atteso (dopo la configurazione):
```
LinkNTPServers=
SystemNTPServers=192.168.56.10
FallbackNTPServers=0.ubuntu.pool.ntp.org 1.ubuntu.pool.ntp.org
ServerName=192.168.56.10
ServerAddress=192.168.56.20
RootDistanceMaxUSec=5s
PollIntervalMinUSec=32s
PollIntervalMaxUSec=34min 8s
```

**Checkpoint di verifica B3:**

```powershell
# Su DC-LAB-01
Write-Host "=== VERIFICA NTP ===" -ForegroundColor Cyan

# 1. Stratum ragionevole (< 10)
$status = w32tm /query /status
$stratumLine = $status | Where-Object { $_ -match "Stratum" }
Write-Host "[INFO] $stratumLine"

# 2. Ultima sincronizzazione recente
$lastSync = $status | Where-Object { $_ -match "Last Successful" }
Write-Host "[INFO] $lastSync"

# 3. Sincronizzazione client
w32tm /stripchart /computer:192.168.56.30 /samples:3 /dataonly
```

---

### Esercizio B4: DNS Linux — Verifica e Diagnostica di BIND9

**Obiettivo.** Verificare la configurazione BIND9 su SRV-LINUX-01, testare la risoluzione DNS da Linux con `dig`, e confrontare il comportamento tra il DNS Windows (DC-LAB-01) e il resolver Linux.

**Background.** In ambienti misti Windows/Linux, è comune avere BIND9 su Linux per gestire zone specifiche o per configurazioni avanzate (DNSSEC, split-horizon). Saper usare `dig` è fondamentale per il troubleshooting DNS avanzato.

---

**Step 1 — Installa gli strumenti DNS su SRV-LINUX-01**

```bash
# Su SRV-LINUX-01 via SSH

# Installa dnsutils (include dig, nslookup, nsupdate)
sudo apt update
sudo apt install -y dnsutils bind9-utils

# Verifica installazione
dig -v
```

---

**Step 2 — Test DNS con dig — la versione avanzata di nslookup**

```bash
# Query base: risolvi dc-lab-01.lab.local usando il DNS di DC-LAB-01
dig @192.168.56.10 dc-lab-01.lab.local

# Output completo di dig — interpretazione:
# ;; QUESTION SECTION: — la query che hai fatto
# ;; ANSWER SECTION: — la risposta del server
# ;; Query time: — latenza in ms
# ;; SERVER: — server DNS che ha risposto
# ;; WHEN: — timestamp
# ;; MSG SIZE: — dimensione risposta in bytes
```

Output atteso:
```
; <<>> DiG 9.18.x <<>> @192.168.56.10 dc-lab-01.lab.local
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: xxxxx
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;dc-lab-01.lab.local.           IN      A

;; ANSWER SECTION:
dc-lab-01.lab.local.    1200    IN      A       192.168.56.10

;; Query time: 2 msec
;; SERVER: 192.168.56.10#53(192.168.56.10) (UDP)
;; WHEN: Wed Jul 15 10:30:00 UTC 2026
;; MSG SIZE  rcvd: 65
```

Il flag `aa` (Authoritative Answer) conferma che DC-LAB-01 è autorevole per `lab.local`.

---

**Step 3 — Verifica i record SRV di Active Directory**

I record SRV sono fondamentali per AD: permettono ai client di trovare i servizi (LDAP, Kerberos, GC) sul dominio.

```bash
# Record SRV per LDAP (usato da tutti i join di dominio e autenticazioni)
dig @192.168.56.10 _ldap._tcp.lab.local SRV

# Record SRV per Kerberos
dig @192.168.56.10 _kerberos._tcp.lab.local SRV

# Record SRV per il PDC
dig @192.168.56.10 _ldap._tcp.pdc._msdcs.lab.local SRV

# Cerca tutti i record SRV con un solo comando
dig @192.168.56.10 lab.local SRV
```

Output atteso per _ldap._tcp.lab.local SRV:
```
;; ANSWER SECTION:
_ldap._tcp.lab.local.   600   IN  SRV  0 100 389 dc-lab-01.lab.local.
```

Il record SRV indica: priorità 0, peso 100, porta 389, server dc-lab-01.lab.local — un client che cerca LDAP per il dominio lab.local trova dc-lab-01:389.

---

**Step 4 — Misura la latenza DNS e confronta sorgenti**

```bash
# Misura la latenza della risoluzione DNS (5 query per avere media)
for i in 1 2 3 4 5; do
    dig @192.168.56.10 lab.local +stats 2>/dev/null | grep "Query time"
done

# Confronto: risoluzione locale (resolver OS) vs DC-LAB-01
dig dc-lab-01.lab.local +stats 2>/dev/null | grep "Query time"
dig @192.168.56.10 dc-lab-01.lab.local +stats 2>/dev/null | grep "Query time"

# Test di lookup inverso (PTR record)
dig @192.168.56.10 -x 192.168.56.10
```

Output atteso per lookup inverso:
```
;; ANSWER SECTION:
10.56.168.192.in-addr.arpa. 3600 IN PTR dc-lab-01.lab.local.
```

---

**Step 5 — Verifica il resolver DNS di SRV-LINUX-01**

```bash
# Visualizza il resolver DNS configurato
cat /etc/resolv.conf

# Su sistemi con systemd-resolved (Ubuntu moderno)
resolvectl status

# Verifica che SRV-LINUX-01 usi DC-LAB-01 come DNS primario
resolvectl dns | grep "192.168.56.10"

# Test completo — risoluzione di un nome del dominio AD
nslookup glpi.lab.local 192.168.56.10
```

Risultato se la configurazione è corretta:
```
Server:         192.168.56.10
Address:        192.168.56.10#53

Non-authoritative answer:
glpi.lab.local  canonical name = srv-linux-01.lab.local.
Name:   srv-linux-01.lab.local
Address: 192.168.56.20
```

---

### Esercizio B5: Scenario Integrato — Diagnostica DNS/DHCP/NTP

**Obiettivo.** Applicare un approccio sistematico a un incidente che coinvolge tutti e tre i servizi fondazionali.

**Scenario.** Lunedì mattina. Un tecnico segnala: "Arrivato in ufficio, WKS-LAB-01 non riesce ad accedere a GLPI (`http://glpi.lab.local:8080`). Ieri sera tutto funzionava."

Usa il Framework 6-Step per diagnosticare e risolvere.

---

**Step 1 — Identifica il problema (raccoglie informazioni)**

```powershell
# Su WKS-LAB-01

# Ha un IP?
ipconfig /all | findstr /i "IPv4 Subnet Default DNS"
# Atteso: IP 192.168.56.xxx, Subnet 255.255.255.0, Gateway 192.168.56.1, DNS 192.168.56.10

# Ping al gateway
ping 192.168.56.1 -n 3
# Se fallisce: problema L1/L2/L3 — cavo, NIC, routing

# Ping a DC-LAB-01 per IP
ping 192.168.56.10 -n 3
# Se fallisce: problema rete verso il DC

# Ping a SRV-LINUX-01 per IP
ping 192.168.56.20 -n 3
# Se fallisce: problema rete verso SRV-LINUX-01
```

```powershell
# Testa la risoluzione DNS
Resolve-DnsName "glpi.lab.local" -Server 192.168.56.10 -ErrorAction SilentlyContinue

# Testa la connessione HTTP direttamente per IP (esclude DNS)
Test-NetConnection -ComputerName "192.168.56.20" -Port 8080
```

---

**Step 2 — Formula le teorie (dalla più probabile)**

```
Teoria 1 (più probabile): Il container Docker GLPI è fermo dopo un riavvio
  Test: ssh srv-linux-01 "docker ps | grep glpi"

Teoria 2: Il record DNS CNAME glpi.lab.local è stato rimosso o corrotto
  Test: Resolve-DnsName glpi.lab.local

Teoria 3: WKS-LAB-01 ha perso il lease DHCP e ha IP sbagliato
  Test: ipconfig /all — verifica IP nel range 192.168.56.100-200

Teoria 4: Problema NTP — orologio sfasato causa fallimento autenticazione
  Test: w32tm /query /status, controlla "Last Successful Sync Time"
```

---

**Step 3 — Testa le teorie in sequenza**

```bash
# Test Teoria 1 — Stato container Docker su SRV-LINUX-01
ssh lab-admin@192.168.56.20 "docker compose -f ~/glpi-docker/docker-compose.yml ps"
# Atteso: se i container non sono "Up", questa è la causa
# Fix: ssh lab-admin@192.168.56.20 "cd ~/glpi-docker && docker compose up -d"
```

```powershell
# Test Teoria 2 — Record DNS
$dns = Resolve-DnsName "glpi.lab.local" -Server 192.168.56.10 -ErrorAction SilentlyContinue
if (-not $dns) {
    Write-Host "[CAUSA] Record DNS glpi.lab.local mancante" -ForegroundColor Red
    # Fix: Add-DnsServerResourceRecordCName -ZoneName "lab.local" -Name "glpi" -HostNameAlias "srv-linux-01.lab.local."
}

# Test Teoria 3 — IP corretto
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.56.*" }).IPAddress
if ($ip -notlike "192.168.56.1[0-9][0-9]") {
    Write-Host "[CAUSA] IP non nel range DHCP previsto: $ip" -ForegroundColor Red
    # Fix: ipconfig /release && ipconfig /renew
}

# Test Teoria 4 — NTP
$ntpStatus = w32tm /query /status
Write-Host "NTP Status:"
$ntpStatus | Select-String "Stratum|Source|Last Successful"
```

---

**Step 4 — Implementa e documenta la soluzione**

Apri GLPI e crea un ticket per documentare l'incidente:

```
Ticket: INC-2026-XXXX
Tipo: Incident
Categoria: Applicazioni / GLPI
Priorità: P3 (impatta 1 utente, bassa urgenza)
Titolo: GLPI non accessibile lunedì mattina

Descrizione:
WKS-LAB-01 non riesce ad accedere a http://glpi.lab.local:8080.
Ping a 192.168.56.20 funziona. Porta 8080 non risponde.

Investigazione:
- DNS glpi.lab.local: risolve correttamente (192.168.56.20)
- NTP: sincronizzato, nessun clock skew
- Test porta 8080: "Connection refused"
- SSH su SRV-LINUX-01: container GLPI non attivo

Causa: Container Docker GLPI non ripartito dopo riavvio del sistema
Soluzione: Eseguito "docker compose up -d" su SRV-LINUX-01
Prevenzione: Aggiungere restart: unless-stopped nel docker-compose.yml
```

---

---

## PART C: SISTEMATIZZARE — Governance dei Servizi Fondazionali

---

### Progetto C1: SOP — Manutenzione Mensile DNS/DHCP/NTP

```markdown
# SOP-INF-001: Manutenzione Mensile Servizi Fondazionali (DNS, DHCP, NTP)

**Versione:** 1.0 | **Data:** 2026-07-15 | **Owner:** Infrastructure Team
**Frequenza:** Prima settimana di ogni mese | **Durata stimata:** 45 minuti
**Sistema:** DC-LAB-01 (DNS + DHCP + NTP) + SRV-LINUX-01

---

## 1. Pre-Controlli (5 minuti)

- [ ] Nessun incidente aperto su DNS/DHCP/NTP in GLPI
- [ ] Finestra manutenzione comunicata agli utenti se in orario lavorativo
- [ ] Backup configurazione DNS eseguito: `dnscmd /zoneexport lab.local lab.local.bak`

---

## 2. DNS — Checklist Mensile (15 minuti)

### 2.1 Verifica zona AD-Integrated
```powershell
Get-DnsServerZone -Name "lab.local" | Select-Object ZoneName, IsDsIntegrated, DynamicUpdate
```
Atteso: IsDsIntegrated=True, DynamicUpdate=Secure

### 2.2 Verifica scavenging abilitato
```powershell
Get-DnsServerZoneAging -Name "lab.local"
```
Atteso: AgingEnabled=True, NoRefreshInterval=7d, RefreshInterval=7d

### 2.3 Conta record stale (non aggiornati da >30 giorni)
```powershell
$cutoff = (Get-Date).AddDays(-30)
Get-DnsServerResourceRecord -ZoneName "lab.local" -RRType "A" |
    Where-Object { $_.TimeStamp -lt $cutoff -and $_.TimeStamp -ne $null } |
    Select-Object HostName, TimeStamp, @{N="IP";E={$_.RecordData.IPv4Address}} |
    Sort-Object TimeStamp
```
Azione: verifica che i record stale siano davvero obsoleti prima di eliminarli

### 2.4 Avvia scavenging manuale (se necessario)
```powershell
Start-DnsServerScavenging
```

### 2.5 Verifica forwarder DNS
```powershell
Get-DnsServerForwarder
```
Verifica che i forwarder configurati siano raggiungibili

---

## 3. DHCP — Checklist Mensile (15 minuti)

### 3.1 Utilizzo scope
```powershell
Get-DhcpServerv4ScopeStatistics -ScopeId "192.168.56.0" |
    Select-Object ScopeId, Free, InUse, PercentageInUse
```
Soglia warning: PercentageInUse > 80%
Azione se critico: espandi il range o individua lease non rinnovati

### 3.2 Reservation verificate
```powershell
Get-DhcpServerv4Reservation -ScopeId "192.168.56.0" |
    Select-Object IPAddress, Name, ClientId
```
Verifica che tutte le reservation siano ancora valide

### 3.3 Ricerca lease orfani (lease senza host name)
```powershell
Get-DhcpServerv4Lease -ScopeId "192.168.56.0" |
    Where-Object { -not $_.HostName } |
    Select-Object IPAddress, ClientId, LeaseExpiryTime
```
Azione: verifica se sono dispositivi non autorizzati

### 3.4 Verifica log DHCP per anomalie
```powershell
Get-WinEvent -FilterHashtable @{
    LogName = "System"
    ProviderName = "Microsoft-Windows-DHCP-Server"
    Id = @(13, 1063)  # Conflict + Rogue
    StartTime = (Get-Date).AddDays(-30)
} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, Message
```

---

## 4. NTP — Checklist Mensile (10 minuti)

### 4.1 Stato sincronizzazione PDC Emulator
```powershell
w32tm /query /status | Select-String "Stratum|Source|Last Successful"
```
Atteso: Stratum < 5, Last Successful entro 24 ore

### 4.2 Verifica scostamento client
```powershell
w32tm /stripchart /computer:192.168.56.30 /samples:3 /dataonly
```
Atteso: offset < 100ms; > 500ms = warning; > 300000ms (5min) = CRITICO

### 4.3 NTP su SRV-LINUX-01
```bash
ssh lab-admin@192.168.56.20 "timedatectl status | grep synchronized"
```
Atteso: "System clock synchronized: yes"

---

## 5. Report e Documentazione

Aggiorna il ticket GLPI mensile con:
- Utilizzo scope DHCP (percentuale)
- Record stale rimossi dallo scavenging
- Scostamento NTP massimo osservato
- Eventuali anomalie trovate e risolte

---

## 6. Escalation

| Problema | Soglia | Azione |
|---|---|---|
| Utilizzo DHCP > 80% | Immediato | Espandi range o analizza lease anomali |
| Rogue DHCP rilevato | Immediato | Isola il dispositivo, apri INC P1 |
| NTP offset > 5 minuti | Immediato | Risincronizza PDC, apri INC P2 |
| Record DNS stale > 10% | 30 giorni | Forza scavenging, rivedi configurazione |
```

---

### Progetto C2: Script — Health Check Mensile DNS/DHCP/NTP

```powershell
#!/usr/bin/env pwsh
# dns_dhcp_ntp_health.ps1 — Health check mensile servizi fondazionali
# Esegui su DC-LAB-01 come Administrator
# Output: report console + CSV opzionale

param(
    [string]$ScopeId = "192.168.56.0",
    [string]$ZoneName = "lab.local",
    [string]$LinuxServer = "192.168.56.20",
    [string]$LinuxUser = "lab-admin",
    [string]$ReportPath = "C:\Reports"
)

function Write-OK   { param($msg) Write-Host "[ OK] $msg" -ForegroundColor Green }
function Write-WARN { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-ERR  { param($msg) Write-Host "[ERR] $msg" -ForegroundColor Red }

$errors   = 0
$warnings = 0

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " DNS/DHCP/NTP HEALTH CHECK — $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# ===== DNS =====
Write-Host "`n[ DNS ]" -ForegroundColor Cyan

try {
    $zone = Get-DnsServerZone -Name $ZoneName -ErrorAction Stop
    if ($zone.IsDsIntegrated) { Write-OK "Zona $ZoneName integrata in AD" }
    else { Write-WARN "Zona $ZoneName NON integrata in AD"; $warnings++ }
} catch {
    Write-ERR "Zona DNS $ZoneName non trovata: $_"; $errors++
}

try {
    $aging = Get-DnsServerZoneAging -Name $ZoneName -ErrorAction Stop
    if ($aging.AgingEnabled) { Write-OK "Scavenging abilitato (No-Refresh: $($aging.NoRefreshInterval), Refresh: $($aging.RefreshInterval))" }
    else { Write-WARN "Scavenging NON abilitato — record stale si accumuleranno"; $warnings++ }
} catch {
    Write-ERR "Impossibile verificare aging DNS: $_"; $errors++
}

# Record stale (non aggiornati da >30 giorni)
$cutoff = (Get-Date).AddDays(-30)
$stale = Get-DnsServerResourceRecord -ZoneName $ZoneName -RRType "A" -ErrorAction SilentlyContinue |
    Where-Object { $_.TimeStamp -and $_.TimeStamp -lt $cutoff }
if ($stale.Count -eq 0) {
    Write-OK "Nessun record A stale (>30 giorni) trovato"
} elseif ($stale.Count -lt 5) {
    Write-WARN "$($stale.Count) record A stale trovati — verificare prima di eliminare"; $warnings++
} else {
    Write-ERR "$($stale.Count) record A stale trovati — eseguire scavenging"; $errors++
}

# ===== DHCP =====
Write-Host "`n[ DHCP ]" -ForegroundColor Cyan

try {
    $scope = Get-DhcpServerv4Scope -ScopeId $ScopeId -ErrorAction Stop
    if ($scope.State -eq "Active") { Write-OK "Scope $ScopeId attivo" }
    else { Write-ERR "Scope $ScopeId in stato: $($scope.State)"; $errors++ }
} catch {
    Write-ERR "Scope DHCP $ScopeId non trovato: $_"; $errors++
}

try {
    $stats = Get-DhcpServerv4ScopeStatistics -ScopeId $ScopeId -ErrorAction Stop
    $pct = [math]::Round($stats.PercentageInUse, 1)
    if ($pct -lt 80) { Write-OK "Utilizzo scope: $pct% ($($stats.InUse) in uso, $($stats.Free) liberi)" }
    elseif ($pct -lt 90) { Write-WARN "Utilizzo scope ALTO: $pct% — espandere presto il range"; $warnings++ }
    else { Write-ERR "Utilizzo scope CRITICO: $pct% — espandere immediatamente"; $errors++ }
} catch {
    Write-ERR "Impossibile leggere statistiche DHCP: $_"; $errors++
}

# Rogue DHCP nelle ultime 24h
$rogue = Get-WinEvent -FilterHashtable @{
    LogName = "System"; Id = 1063
    StartTime = (Get-Date).AddHours(-24)
} -ErrorAction SilentlyContinue
if ($rogue) {
    Write-ERR "ROGUE DHCP rilevato! $($rogue.Count) eventi nelle ultime 24h — AZIONE IMMEDIATA"; $errors++
} else {
    Write-OK "Nessun Rogue DHCP rilevato (ultime 24 ore)"
}

# Reservation verificate
$res = Get-DhcpServerv4Reservation -ScopeId $ScopeId -ErrorAction SilentlyContinue
Write-OK "$($res.Count) reservation configurate"

# ===== NTP =====
Write-Host "`n[ NTP ]" -ForegroundColor Cyan

$ntpRaw = w32tm /query /status 2>&1
$stratumLine = $ntpRaw | Where-Object { $_ -match "Stratum:" }
$sourceLine  = $ntpRaw | Where-Object { $_ -match "Source:" }
$lastSync    = $ntpRaw | Where-Object { $_ -match "Last Successful" }

if ($stratumLine) {
    $stratumNum = ($stratumLine -replace ".*Stratum:\s*(\d+).*", '$1').Trim()
    [int]$s = $stratumNum
    if ($s -le 5) { Write-OK "Stratum: $s (sorgente primaria ben configurata)" }
    elseif ($s -le 10) { Write-WARN "Stratum: $s (catena NTP lunga — verificare sorgenti)"; $warnings++ }
    else { Write-ERR "Stratum: $s — NON SINCRONIZZATO o catena troppo lunga"; $errors++ }
}

if ($sourceLine) {
    Write-OK "Sorgente NTP: $($sourceLine.Trim())"
}

if ($lastSync) {
    Write-OK "Ultima sincronizzazione: $($lastSync.Trim())"
}

# Verifica NTP su SRV-LINUX-01 (via SSH)
try {
    $linuxNtp = ssh "$LinuxUser@$LinuxServer" "timedatectl status 2>/dev/null | grep synchronized" 2>$null
    if ($linuxNtp -match "yes") {
        Write-OK "SRV-LINUX-01: orologio sincronizzato"
    } else {
        Write-WARN "SRV-LINUX-01: orologio NON sincronizzato — verificare systemd-timesyncd"; $warnings++
    }
} catch {
    Write-WARN "Impossibile verificare NTP su SRV-LINUX-01 via SSH"; $warnings++
}

# ===== RIEPILOGO =====
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host " RIEPILOGO" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host " ESITO: TUTTO OK — nessuna anomalia rilevata" -ForegroundColor Green
} elseif ($errors -eq 0) {
    Write-Host " ESITO: WARNING ($warnings) — revisione consigliata" -ForegroundColor Yellow
} else {
    Write-Host " ESITO: ERRORI ($errors) + WARNING ($warnings) — ATTENZIONE RICHIESTA" -ForegroundColor Red
}

# Salva report
if (-not (Test-Path $ReportPath)) { New-Item -ItemType Directory -Path $ReportPath | Out-Null }
$reportFile = "$ReportPath\dns_dhcp_ntp_$(Get-Date -Format 'yyyyMMdd').txt"
$ntpRaw | Out-File -Append $reportFile
Write-Host " Report: $reportFile" -ForegroundColor Gray
```

**Installazione e utilizzo:**

```powershell
# Salva lo script
New-Item -Path "C:\Scripts" -ItemType Directory -Force | Out-Null
# (copia il contenuto sopra in C:\Scripts\dns_dhcp_ntp_health.ps1)

# Esegui manualmente
& "C:\Scripts\dns_dhcp_ntp_health.ps1"

# Pianifica come Scheduled Task — primo lunedì del mese alle 07:00
$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday `
    -WeeksInterval 4 `
    -At "07:00AM"

$action = New-ScheduledTaskAction `
    -Execute "pwsh.exe" `
    -Argument "-NonInteractive -File C:\Scripts\dns_dhcp_ntp_health.ps1"

Register-ScheduledTask `
    -TaskName "DNS-DHCP-NTP-Monthly-Check" `
    -Trigger $trigger `
    -Action $action `
    -RunLevel Highest `
    -User "SYSTEM"

Write-Host "[OK] Task pianificato: DNS-DHCP-NTP-Monthly-Check"
```

---

### Progetto C3: Integrazione ITIL — DNS/DHCP/NTP nelle Pratiche ITSM

**I servizi fondazionali nel CMDB:**

Ogni servizio fondazionale deve essere un Configuration Item (CI) nel CMDB (GLPI):

| CI Name | Tipo | Relazioni | Owner |
|---|---|---|---|
| DNS-LAB-01 | Software Service | Dipende da DC-LAB-01 | Infrastructure Team |
| DHCP-LAB-01 | Software Service | Dipende da DC-LAB-01 | Infrastructure Team |
| W32Time-LAB | Software Service | Dipende da PDC Emulator | Infrastructure Team |
| lab.local DNS Zone | Configuration | Ospitata da DNS-LAB-01 | Infrastructure Team |

**Query SQL per GLPI — verifica CI servizi fondazionali:**

```sql
-- Elenca tutti i CI di tipo "Software Service" in GLPI
SELECT
    name,
    comment,
    date_mod,
    is_active
FROM glpi_softwarelicenses
WHERE name LIKE '%DNS%'
   OR name LIKE '%DHCP%'
   OR name LIKE '%NTP%'
ORDER BY name;

-- In alternativa usa la GUI GLPI:
-- Assets → Software → filtra per "DNS" o "DHCP"
```

**Connessione Incident → DNS/DHCP/NTP:**

```
Incidente "utente non accede alla rete"
         ↓
L'operatore L1 segue la checklist:
  1. Ha IP? → se no → check DHCP
  2. DNS risolve? → se no → check DNS
  3. Autenticazione fallisce? → se no → check NTP/Kerberos
         ↓
Risolto in L1 → chiude ticket con KB articolo
Non risolto → escalation L2 con diagnosi già in mano
```

**KPI per i servizi fondazionali:**

| KPI | Formula | Target | Alert |
|---|---|---|---|
| DNS Availability | Uptime DNS service / Ore totali | 99.9% | < 99.5% |
| DHCP Scope Utilization | IP in uso / IP totali | < 80% | > 85% |
| NTP Offset massimo | Max |offset| tra tutti i client | < 100ms | > 500ms |
| DNS Query Latency | Avg query time (ms) | < 10ms | > 50ms |
| Rogue DHCP events | Conteggio Event ID 1063 | 0 | ≥ 1 |

---

## Checklist di Validazione — Tutorial ops04a Completato

### Fondamenti (Part A)
- [ ] Sai spiegare la differenza tra DNS recursivo e autorevole con un esempio
- [ ] Sai descrivere il processo DORA del DHCP e cosa succede se il server non risponde
- [ ] Sai spiegare la gerarchia NTP Stratum 0/1/2 e perché il PDC Emulator è Stratum 2
- [ ] Sai spiegare perché il clock skew > 5 minuti blocca Kerberos
- [ ] Sai elencare i 3 tipi di record DNS creati da DHCP Dynamic Updates (A, PTR, CNAME)
- [ ] Sai spiegare cosa sono i "record stale" e come lo scavenging li gestisce

### Operazioni (Part B)
- [ ] B1: Scavenging DNS configurato con No-Refresh=7gg e Refresh=7gg su zona lab.local
- [ ] B1: Record CNAME `glpi.lab.local → srv-linux-01.lab.local` creato e verificato
- [ ] B2: Reservation DHCP per SRV-LINUX-01 (192.168.56.20) configurata con MAC reale
- [ ] B2: Log DHCP analizzato — nessun Event ID 1063 (Rogue DHCP)
- [ ] B3: `w32tm /query /status` mostra Stratum ragionevole e sorgente configurata
- [ ] B3: WKS-LAB-01 usa DC-LAB-01 come sorgente NTP (`w32tm /query /source`)
- [ ] B3: SRV-LINUX-01 configurato con `systemd-timesyncd` puntato a DC-LAB-01
- [ ] B4: `dig @192.168.56.10 _ldap._tcp.lab.local SRV` mostra il record SRV corretto
- [ ] B5: Scenario integrato diagnosticato con Framework 6-Step — ticket GLPI aperto

### Governance (Part C)
- [ ] SOP-INF-001 letta e compresa — sai eseguire la checklist mensile
- [ ] Script `dns_dhcp_ntp_health.ps1` eseguito con output "TUTTO OK" (o anomalie investigate)
- [ ] Sai spiegare come DNS, DHCP e NTP sono collegati come CI nel CMDB

---

## Appendice A: Cheat Sheet Comandi DNS/DHCP/NTP

### DNS — Windows (DC-LAB-01)
```powershell
# Zona
Get-DnsServerZone -Name "lab.local"
Get-DnsServerZoneAging -Name "lab.local"
Set-DnsServerZoneAging -Name "lab.local" -Aging $true -NoRefreshInterval 7.00:00:00 -RefreshInterval 7.00:00:00

# Record
Get-DnsServerResourceRecord -ZoneName "lab.local" -RRType "A"
Add-DnsServerResourceRecordCName -ZoneName "lab.local" -Name "alias" -HostNameAlias "server.lab.local."
Remove-DnsServerResourceRecord -ZoneName "lab.local" -RRType "CNAME" -Name "alias" -Force

# Risoluzione
Resolve-DnsName "nome.lab.local" -Server 192.168.56.10
Resolve-DnsName "nome.lab.local" -Type SRV -Server 192.168.56.10

# Scavenging
Start-DnsServerScavenging
```

### DNS — Linux (SRV-LINUX-01)
```bash
# Query base
dig @192.168.56.10 dc-lab-01.lab.local
dig @192.168.56.10 _ldap._tcp.lab.local SRV
dig @192.168.56.10 -x 192.168.56.10           # reverse lookup
dig @192.168.56.10 lab.local +stats            # con latenza

# nslookup alternativo
nslookup dc-lab-01.lab.local 192.168.56.10
nslookup -type=SRV _ldap._tcp.lab.local 192.168.56.10

# Resolver locale
resolvectl status
cat /etc/resolv.conf
```

### DHCP — Windows (DC-LAB-01)
```powershell
# Scope
Get-DhcpServerv4Scope
Get-DhcpServerv4ScopeStatistics -ScopeId "192.168.56.0"

# Lease
Get-DhcpServerv4Lease -ScopeId "192.168.56.0"
Remove-DhcpServerv4Lease -ScopeId "192.168.56.0" -ClientId "XX-XX-XX-XX-XX-XX"

# Reservation
Add-DhcpServerv4Reservation -ScopeId "192.168.56.0" -IPAddress "192.168.56.20" -ClientId "08-00-27-XX-XX-XX"
Get-DhcpServerv4Reservation -ScopeId "192.168.56.0"

# Failover
Get-DhcpServerv4Failover
Get-DhcpServerInDC
```

### NTP — Windows
```powershell
# Query
w32tm /query /status
w32tm /query /source
w32tm /query /peers
w32tm /query /configuration

# Configurazione PDC
w32tm /config /manualpeerlist:"0.it.pool.ntp.org,0x8 1.it.pool.ntp.org,0x8" /syncfromflags:manual /reliable:yes /update
Restart-Service w32time
w32tm /resync /force

# Misurazione offset
w32tm /stripchart /computer:192.168.56.30 /samples:5 /dataonly
```

### NTP — Linux
```bash
# systemd-timesyncd (Ubuntu)
timedatectl status
timedatectl show-timesync --all
systemctl restart systemd-timesyncd

# chrony (RHEL/CentOS/Fedora)
chronyc tracking
chronyc sources -v
chronyc makestep          # forza sincronizzazione immediata

# ntpq (ntpd legacy)
ntpq -p
ntpstat
```

---

## Appendice B: Decision Tree — "L'utente non accede alla rete"

```
PROBLEMA: utente non accede alla rete
              │
              ▼
Ha un indirizzo IP?    [ipconfig /all]
   NO → problema DHCP
        ├── Il DHCP server è attivo?  [Get-DhcpServerv4Scope]
        ├── Il client è sulla VLAN giusta?
        └── Firewall blocca UDP 67/68?
   SÌ → continua ▼

L'IP è nel range corretto?  (192.168.56.100-200)
   NO → IP conflitto o lease da rogue DHCP
        └── ipconfig /release && ipconfig /renew
   SÌ → continua ▼

Ping al gateway (192.168.56.1)?
   NO → problema L1/L2/L3  (cavo, NIC, VLAN, routing)
   SÌ → continua ▼

DNS risolve dc-lab-01.lab.local?  [Resolve-DnsName]
   NO → problema DNS
        ├── Server DNS raggiungibile?  [ping 192.168.56.10]
        ├── Zona lab.local presente?  [Get-DnsServerZone]
        └── Record A presente?  [Get-DnsServerResourceRecord]
   SÌ → continua ▼

Autenticazione AD funziona?  [klist / net use]
   NO → problema Kerberos → NTP
        ├── w32tm /query /status (offset < 5 minuti?)
        └── w32tm /resync /force
   SÌ → problema applicativo (permessi, configurazione app)
```

---

## Appendice C: Soglie di Allarme — Riferimento Rapido

| Metrica | OK | Warning | Critico | Impatto se Critico |
|---|---|---|---|---|
| DHCP Scope Use% | < 80% | 80-90% | > 90% | Nuovi dispositivi non ottengono IP |
| Record DNS stale | 0 | 1-5% | > 10% | Risoluzione errata, connessioni fallite |
| NTP Stratum | ≤ 5 | 6-10 | > 10 / 16 | Deriva orologio progressiva |
| NTP Offset | < 100ms | 100-500ms | > 5 minuti | Fallimento Kerberos, no login AD |
| Rogue DHCP | 0 | N/A | ≥ 1 | IP sbagliati, MITM possibile |
| DNS Query Time | < 10ms | 10-50ms | > 50ms | Apertura applicazioni lenta |

---

## Riferimenti

| Risorsa | Posizione | Contenuto |
|---|---|---|
| Documento sorgente | `../04-servizi-infrastruttura.md` (sez. DNS, DHCP, NTP) | Configurazioni complete di produzione |
| Tutorial ops03a | `tutorial_ops03_ch1a_windows_server_ops_lab.md` | Windows Server base (prerequisito) |
| Tutorial ops04b | `tutorial_ops04_ch1b_active_directory_ldap_lab.md` | Active Directory avanzato |
| RFC 8633 | tools.ietf.org/html/rfc8633 | NTP Best Current Practices |
| RFC 2131 | tools.ietf.org/html/rfc2131 | DHCP Protocol Specification |
| RFC 1035 | tools.ietf.org/html/rfc1035 | DNS standard originale |

---

*Fine tutorial ops04a — Prossimo: `tutorial_ops04_ch1b_active_directory_ldap_lab.md`*
