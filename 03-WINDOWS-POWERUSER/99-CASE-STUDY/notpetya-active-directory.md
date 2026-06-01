# Case Study — NotPetya 2017: Devastazione di Active Directory via Supply Chain

> **Modulo del corso:** Amministrazione Windows enterprise — Case Study
> **Prerequisiti:** [01-active-directory.md](../01-active-directory.md), [29-windows-server-hardening.md](../29-windows-server-hardening.md), [34-disaster-recovery-ad-pki.md](../34-disaster-recovery-ad-pki.md)
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-23
> **CVSS 3.1:** N/A (malware multi-vettore, non singola CVE)
> **CVE correlate:** CVE-2017-0144 (EternalBlue), CVE-2017-0145 (EternalRomance)
> **CWE:** CWE-494 (Download of Code Without Integrity Check), CWE-306 (Missing Authentication for Critical Function)

---

## Sintesi dell'Incidente

NotPetya è il cyberattacco più distruttivo nella storia, con danni stimati superiori a $10 miliardi globalmente. Il 27 giugno 2017, un malware mascherato da ransomware (in realtà un wiper) è stato distribuito tramite un aggiornamento compromesso del software di contabilità ucraino MEDoc. In poche ore ha devastato infrastrutture IT globali, con Active Directory come bersaglio primario e vettore di propagazione.

Il caso Maersk è emblematico: l'intero patrimonio IT globale — 4.000 server, 45.000 PC, 2.500 applicazioni — è stato distrutto in meno di 7 ore. Il recovery è stato possibile solo grazie a un singolo domain controller offline in Ghana, risparmiato per un'interruzione di corrente fortuita.

---

## Cronologia Dettagliata

| Data | Evento |
|------|--------|
| 2017-04-14 | Shadow Brokers pubblica exploit NSA: EternalBlue (CVE-2017-0144) e EternalRomance (CVE-2017-0145) |
| 2017-03-14 | Microsoft rilascia MS17-010 che patcha le vulnerabilità SMBv1 |
| 2017-05-12 | WannaCry usa EternalBlue per propagarsi globalmente — avvertimento ignorato da molte organizzazioni |
| 2017-06 (~) | Attaccanti (attribuiti a Sandworm/GRU Russia) compromettono i server di aggiornamento di M.E.Doc |
| 2017-06-27 10:00 UTC | Aggiornamento MEDoc compromesso distribuito a ~400.000 client in Ucraina |
| 2017-06-27 10:30 | NotPetya inizia la propagazione laterale via EternalBlue + credential harvesting |
| 2017-06-27 ~11:00 | Maersk: primi sistemi infetti in ufficio Odessa (Ucraina). Entro 7 minuti, propagazione globale |
| 2017-06-27 ~14:00 | Maersk: sistemi IT globali completamente offline. AP Møller-Maersk opera 76 terminal portuali in 41 paesi |
| 2017-06-27 | Altre vittime: Merck ($870M), FedEx/TNT ($400M), Saint-Gobain ($384M), Mondelez ($188M), Reckitt Benckiser ($129M) |
| 2017-06-28 | Maersk scopre un DC sopravvissuto in Ghana (offline per blackout elettrico) |
| 2017-07-07 | Maersk: AD forest ricostruito. 10 giorni di operazioni manuali con carta e telefono |
| 2017-07-17 | Maersk: operazioni IT sostanzialmente ripristinate (20 giorni totali) |
| 2018-02-15 | White House attribuisce formalmente NotPetya alla Russia (GRU, unità Sandworm) |

---

## Analisi Tecnica

### Vettore Iniziale: Supply Chain via MEDoc

```
Catena di compromissione:

1. Attaccanti compromettono server aggiornamenti M.E.Doc
   └── M.E.Doc: software di contabilità/fiscale obbligatorio in Ucraina
   └── ~400.000 installazioni in aziende ucraine

2. Aggiornamento legittimo (EzVit.exe) sostituito con payload malevolo
   └── Firmato con certificato M.E.Doc valido
   └── Distribuito via meccanismo di aggiornamento automatico

3. Il payload si esegue con i privilegi dell'utente MEDoc
   └── Tipicamente SYSTEM o admin locale (installazione servizio)
```

### Meccanismo di Propagazione: Multi-Vettore

NotPetya usava tre metodi di propagazione simultanei, rendendolo estremamente efficace:

```
Propagazione NotPetya:

┌─────────────────────────────────────────────────────────┐
│ 1. EternalBlue (CVE-2017-0144)                         │
│    └── Exploit SMBv1 → RCE su sistemi non patchati     │
│    └── Funziona senza autenticazione                   │
│    └── Stesso exploit di WannaCry (2017-05-12)         │
├─────────────────────────────────────────────────────────┤
│ 2. Credential Harvesting (variante Mimikatz)            │
│    └── Estrae credenziali da LSASS memory              │
│    └── Password hash NTLM + ticket Kerberos            │
│    └── Passa-the-Hash per autenticarsi su altri sistemi │
│    └── Include modulo Mimikatz compilato in-memory      │
├─────────────────────────────────────────────────────────┤
│ 3. WMI / PsExec remoto                                 │
│    └── Usa credenziali raccolte per esecuzione remota   │
│    └── WMI: wmic /node:<target> process call create     │
│    └── PsExec: copia ed esegue payload via SMB admin$   │
│    └── Funziona anche su sistemi patchati per SMBv1     │
└─────────────────────────────────────────────────────────┘

Combinazione letale:
- EternalBlue per sistemi non patchati (nessuna credenziale richiesta)
- Mimikatz + WMI/PsExec per sistemi patchati (usa credenziali rubate)
- Risultato: propagazione quasi al 100% in reti flat
```

### Perché Active Directory Era il Bersaglio Primario

```
Ruolo di AD nella catena di attacco:

1. CREDENTIAL STORE
   └── LSASS contiene hash NTLM e ticket Kerberos
   └── Domain Admin credentials = accesso a TUTTO
   └── Un singolo DA compromesso = intera forest compromessa

2. PROPAGATION VECTOR
   └── Admin$ e C$ share accessibili con credenziali di dominio
   └── WMI e PsExec usano autenticazione AD
   └── GPO possono distribuire malware a tutti i client

3. DESTRUCTION TARGET
   └── NTDS.dit (database AD) cifrato/distrutto
   └── SYSVOL (Group Policy) cifrato/distrutto
   └── Boot sector (MBR/VBR) sovrascritto
   └── Senza AD: nessun login, nessun DNS interno,
       nessuna autenticazione, nessun servizio
```

### Il Payload Distruttivo

```
Sequenza distruttiva per host:

1. Attende 10-60 minuti (raccolta credenziali, propagazione)

2. Modifica MBR con bootloader custom
   └── Mostra falsa schermata CHKDSK durante cifratura

3. Cifra MFT (Master File Table) con Salsa20
   └── Key derivata da combinazione unica per host
   └── Key NON inviata a nessun C2 → nessun decript possibile
   └── Questo conferma: wiper, NON ransomware

4. Richiede $300 in Bitcoin per "decriptare"
   └── Indirizzo Bitcoin e email (wowsmith123456@posteo.net)
   └── Email bloccata da Posteo il giorno stesso
   └── Anche pagando: decifratura impossibile by design

5. Reboot forzato → schermata "CHKDSK" (in realtà cifratura)
   └── Al termine: sistema irrecuperabile
```

---

## Il Caso Maersk: Anatomia della Distruzione

### Timeline della Catastrofe

Maersk, il più grande operatore di container shipping al mondo (76 terminal portuali, 800 navi, 41 paesi), è stato devastato in ore:

- **10:00 UTC**: Ufficio Odessa infetto via MEDoc
- **10:07 UTC**: Prima propagazione laterale (7 minuti dall'infezione iniziale)
- **10:15 UTC**: Sistemi in Danimarca (HQ Copenhagen) infetti via VPN
- **10:30 UTC**: Propagazione globale in corso — uffici in 130 paesi
- **11:00 UTC**: IT staff inizia a scollegare server, ma è troppo tardi
- **14:00 UTC**: Praticamente tutti i sistemi IT offline

### Impatto Operativo

| Area | Impatto |
|------|---------|
| **Server** | 4.000 server distrutti |
| **PC** | 45.000 PC distrutti |
| **Applicazioni** | 2.500 applicazioni down |
| **Active Directory** | Tutti i DC distrutti tranne uno |
| **Operazioni portuali** | 76 terminal bloccati — navi non possono caricare/scaricare |
| **Prenotazioni** | Sistema booking offline — 10M container non tracciabili |
| **Comunicazioni** | Nessuna email, telefoni VoIP down |
| **Durata** | 10 giorni di operazioni manuali (carta, telefono, WhatsApp) |
| **Costo** | $250-300 milioni (dichiarato da Maersk) |

### Il DC di Ghana: Fortuna nella Catastrofe

Il singolo domain controller sopravvissuto a Accra, Ghana, era offline a causa di un'interruzione di corrente locale. Quando il team IT ha scoperto il DC sopravvissuto:

1. **Trasporto fisico**: un dipendente Maersk ha volato da Accra a Londra con il server (il DC non poteva essere connesso alla rete per paura di infezione)
2. **Forest rebuild**: dal singolo DC, il team Microsoft (inviato d'emergenza) ha ricostruito l'intera forest AD
3. **Reinstallazione**: 4.000 server e 45.000 PC reinstallati in 10 giorni con team da tutto il mondo

**Cosa sarebbe successo senza il DC di Ghana?** Ricostruzione AD da zero: settimane o mesi. Ogni account, ogni GPO, ogni trust, ogni configurazione — persi. L'identità stessa dell'organizzazione era nel database AD.

---

## Impatto Globale

| Organizzazione | Settore | Danno Stimato |
|----------------|---------|---------------|
| Maersk | Shipping/Logistica | $300M |
| Merck | Farmaceutico | $870M |
| FedEx/TNT Express | Logistica | $400M |
| Saint-Gobain | Costruzioni | $384M |
| Mondelez | Alimentare | $188M |
| Reckitt Benckiser | Beni di consumo | $129M |
| DLA Piper | Studio legale | non dichiarato |
| Rosneft | Energia | non dichiarato |
| Heritage Valley Health | Sanità | operazioni interrotte |
| **Totale globale** | | **$10+ miliardi** |

---

## Mitigazione e Lezioni Apprese

### 1. AD Backup OFFLINE Mandatory

```powershell
# Backup System State su media offline (non connesso alla rete)
wbadmin start systemstatebackup -backupTarget:E:

# Verificare backup
wbadmin get versions -backupTarget:E:

# Script per backup settimanale con rotazione
$BackupDrive = "E:"
$LogPath = "C:\Logs\AD-Backup"
$MaxBackups = 4

# Backup System State
wbadmin start systemstatebackup -backupTarget:$BackupDrive -quiet

# Retention: mantenere ultimi 4 backup
$Versions = wbadmin get versions -backupTarget:$BackupDrive
# ... logica di rotazione ...
```

**Regola**: almeno un backup AD offline, disconnesso dalla rete, testato con restore drill trimestrale. Il backup online viene distrutto insieme al sistema.

### 2. Tier Model per Credenziali Privilegiate

```
Modello a 3 Tier per contenere propagazione:

┌─────────────────────────────────────────┐
│ TIER 0 — Forest/Domain (DC, AD, PKI)   │
│ • Admin accounts dedicati              │
│ • PAW (Privileged Access Workstation)   │
│ • NO email, NO internet, NO VPN        │
│ • Separate credential silo             │
└────────────────┬────────────────────────┘
                 │ ← credential barrier
┌────────────────┴────────────────────────┐
│ TIER 1 — Server (app, DB, file)        │
│ • Server admin accounts                │
│ • NO domain admin login                │
│ • Logon restriction via GPO            │
└────────────────┬────────────────────────┘
                 │ ← credential barrier
┌────────────────┴────────────────────────┐
│ TIER 2 — Workstation/Device            │
│ • Help desk accounts                   │
│ • User accounts                        │
│ • NO server/domain admin login         │
└─────────────────────────────────────────┘

NotPetya ha funzionato perché: reti flat, Domain Admin
usato per login ovunque → credenziali cached su ogni PC.
```

### 3. Patch SMBv1 e Disabilitazione Protocolli Legacy

```powershell
# Disabilitare SMBv1 — SERVER
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart

# Disabilitare SMBv1 — CLIENT
Set-SmbClientConfiguration -EnableBandwidthThrottling $false

# Verificare
Get-SmbServerConfiguration | Select EnableSMB1Protocol
Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol

# Abilitare SMB signing (previene relay attacks)
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force

# Abilitare SMB encryption (SMB 3.x)
Set-SmbServerConfiguration -EncryptData $true -Force
```

### 4. Protezione contro Credential Theft

```powershell
# Abilitare Credential Guard (Windows 10/Server 2016+)
# Via GPO: Computer Configuration > Administrative Templates >
#   System > Device Guard > Turn On Virtualization Based Security
# Con Credential Guard: Secure Credential Guard

# Protected Users group — impedisce caching credenziali
Add-ADGroupMember -Identity "Protected Users" -Members "AdminTier0"

# Restrict NTLM
# GPO: Network security: Restrict NTLM: NTLM authentication in this domain
# Valore: Deny for domain servers / Deny for domain accounts

# LAPS (Local Administrator Password Solution)
# Ogni PC ha password admin locale unica, rotata automaticamente
# Previene Pass-the-Hash con credenziali admin locali condivise
Install-Module -Name LAPS -Force
Update-LapsADSchema
Set-LapsADComputerSelfPermission -Identity "OU=Workstations,DC=corp,DC=local"
```

### 5. DR Drill: Scenario "Zero DC Survive"

```
Procedura di forest recovery da zero:

1. Isolare la rete (switch off / VLAN isolation)
2. Installare OS pulito su hardware dedicato
3. Restore System State da backup offline
4. Verificare integrità NTDS.dit
5. Seize all FSMO roles sul DC ripristinato
6. Reset password krbtgt (2 volte, con intervallo)
7. Reset password di tutti gli account privilegiati
8. Aggiungere DC aggiuntivi via promozione
9. Verificare replicazione
10. Graduale riconnessione dei servizi

Questo drill DEVE essere eseguito almeno annualmente.
Tempo target: < 4 ore per primo DC operativo.
```

### 6. Segmentazione di Rete

```
Prima di NotPetya (rete flat):

[PC Ucraina] ←VPN→ [HQ Denmark] ←→ [Terminal 1..76]
     ↕                    ↕                  ↕
  [Tutti parlano con tutti — nessuna segmentazione]

Dopo NotPetya (segmentata):

[PC Ucraina] ←VPN→ [FW] ←→ [HQ Denmark]
                              ├── [Tier 0 VLAN] (DC, PKI)
                              ├── [Tier 1 VLAN] (Servers)
                              ├── [Tier 2 VLAN] (Workstations)
                              └── [DMZ] (Internet-facing)

Ogni tier ha firewall rules che impediscono:
- Admin login cross-tier
- SMB laterale non necessario
- WMI/PsExec non autorizzato
```

---

## Indicatori di Compromissione (IoC)

### Hash del Payload

```
SHA-256:
027cc450ef5f8c5f653329641ec1fed91f694e0d229928963b30f6b0d7d3a745 (main payload)
02ef73bd2458627ed7b397ec26ee2de2e92c71a0e7588f78734761d8edbdcd9f (perfc.dat)
```

### Event ID Rilevanti per Detection

| Event ID | Log | Significato |
|----------|-----|-------------|
| 4688 | Security | Creazione processo (cercare cmd.exe, wmic.exe, rundll32.exe anomali) |
| 4624 tipo 3 | Security | Network logon (propagazione laterale) |
| 4648 | Security | Logon con credenziali esplicite (PtH) |
| 7045 | System | Installazione nuovo servizio (payload come servizio) |
| 4697 | Security | Installazione servizio (audit policy) |
| 1102 | Security | Log cancellato (tentativo di coprire tracce) |

---

## Domande di Riflessione

1. Se Maersk non avesse avuto il DC di Ghana offline, quanto tempo avrebbe richiesto ricostruire l'intera forest AD da zero? Quali informazioni sarebbero state perse permanentemente?

2. La tua organizzazione ha un backup AD offline, disconnesso dalla rete, testato con restore drill? Se non lo ha, quali sono le barriere all'implementazione?

3. Come implementeresti il tier model in un'organizzazione che usa lo stesso account Domain Admin per tutto, dai DC ai PC utente?

4. NotPetya si è propagato via VPN da un ufficio ucraino. Come segmenteresti la rete per prevenire propagazione cross-site?

5. Il costo di NotPetya per Maersk ($300M) include 10 giorni di operazioni manuali. Qual è il costo stimato per la tua organizzazione di operare senza IT per 10 giorni?

---

## Riferimenti

- Andy Greenberg, "The Untold Story of NotPetya, the Most Devastating Cyberattack in History" — Wired, 2018-08-22. https://www.wired.com/story/notpetya-cyberattack-ukraine-russia-code-crashed-the-world/ (consultato: 2026-05-23)
- Gavin Ashton (Maersk IT), "Petya – An Eye-Opener" — 2017. Post rimosso, archiviato.
- US-CERT Alert TA17-181A — "Petya Ransomware". https://www.cisa.gov/news-events/alerts/2017/06/29/petya-ransomware (consultato: 2026-05-23)
- Microsoft Security Response Center, MS17-010 — "Security Update for Microsoft Windows SMB Server". https://msrc.microsoft.com/update-guide/vulnerability/CVE-2017-0144 (consultato: 2026-05-23)
- ESET Research, "TeleBots are back: Supply-chain attacks against Ukraine" — 2017-06-30. https://www.welivesecurity.com/2017/06/30/telebots-back-supply-chain-attacks-against-ukraine/ (consultato: 2026-05-23)
- White House Press Statement, "Statement from the Press Secretary on NotPetya attribution" — 2018-02-15.
- NVD CVE-2017-0144 — https://nvd.nist.gov/vuln/detail/CVE-2017-0144 (consultato: 2026-05-23)

---

## Cross-links

- [01-active-directory.md](../01-active-directory.md) — Active Directory fundamentals
- [25-active-directory-design-avanzato.md](../25-active-directory-design-avanzato.md) — AD design, tier model
- [29-windows-server-hardening.md](../29-windows-server-hardening.md) — hardening, CIS benchmark
- [34-disaster-recovery-ad-pki.md](../34-disaster-recovery-ad-pki.md) — AD forest recovery, DR procedures
- [05-sicurezza-windows.md](../05-sicurezza-windows.md) — Windows security, Credential Guard
- [08-permessi-e-accesso.md](../08-permessi-e-accesso.md) — permessi, delegazione
- [06-rete-windows.md](../06-rete-windows.md) — networking, segmentazione
